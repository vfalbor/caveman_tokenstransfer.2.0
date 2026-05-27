"""
caveman_tokenstransfer.2.0 — unified compression client.

Auto-routes:
  1. LOCAL mode (no network) if `llmlingua` + `torch` installed → uses local.py
  2. API mode (fallback) → POST to transfer.tokenstree.com

Both modes preserve code blocks, inline code, URLs, markdown headings,
list markers, and blank lines.

Quick start (local):
    pip install llmlingua torch tiktoken
    python -c "from caveman_transfer.client import compress; print(compress('long text...')[0])"

Quick start (API):
    export TOKENSTRANSFER_API_KEY=tt_...
    python -c "from caveman_transfer.client import compress; print(compress('long text...')[0])"

Force a mode:
    compress(text, mode='local')   # raises if unavailable
    compress(text, mode='api')     # forces API even if local is available
"""
from __future__ import annotations
import os
import re
import json
import time
import warnings
from typing import Optional, Tuple, Dict, List

import requests

try:
    from . import local as _local  # package import
except ImportError:
    try:
        import local as _local      # direct script import
    except ImportError:
        _local = None  # type: ignore

DEFAULT_URL = os.environ.get("TOKENSTRANSFER_URL", "https://transfer.tokenstree.com")
DEFAULT_KEY = os.environ.get("TOKENSTRANSFER_API_KEY", "")
DEFAULT_RATE = float(os.environ.get("TOKENSTRANSFER_RATE", "0.5"))
FAIL_SOFT = os.environ.get("TOKENSTRANSFER_FAIL_SOFT", "true").lower() == "true"
PREFER_MODE = os.environ.get("TOKENSTRANSFER_MODE", "auto").lower()  # auto|local|api

# Preserve regions (markdown-aware).
PRESERVE_PATTERNS = [
    re.compile(r"^---\n.*?\n---\n", re.S | re.M),
    re.compile(r"```.*?```", re.S),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"https?://\S+"),
    re.compile(r"^\s*#{1,6}\s+.+$", re.M),
    re.compile(r"^\s*(?:[-*+]|\d+\.)\s", re.M),
    re.compile(r"\n\s*\n"),
]
MIN_PROSE_LEN = 30


class TransferError(RuntimeError):
    pass


def _segment(text: str) -> List[Tuple[str, str]]:
    marks: List[Tuple[int, int]] = []
    for rx in PRESERVE_PATTERNS:
        for m in rx.finditer(text):
            if any(not (m.end() <= s or m.start() >= e) for s, e in marks):
                continue
            marks.append((m.start(), m.end()))
    marks.sort()
    segments: List[Tuple[str, str]] = []
    cursor = 0
    for s, e in marks:
        if cursor < s:
            segments.append(("prose", text[cursor:s]))
        segments.append(("preserve", text[s:e]))
        cursor = e
    if cursor < len(text):
        segments.append(("prose", text[cursor:]))
    return segments


def _glue(parts: List[str]) -> str:
    out: List[str] = []
    for i, p in enumerate(parts):
        if i > 0 and out and p and not out[-1][-1:].isspace() and not p[0].isspace():
            out.append(" ")
        out.append(p)
    return "".join(out)


def _call_api(chunk: str, rate, target_token, api_key, url, timeout):
    payload: Dict = {"text": chunk}
    if target_token is not None:
        payload["target_token"] = target_token
    if rate is not None:
        payload["rate"] = rate
    r = requests.post(
        f"{url or DEFAULT_URL}/compress",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    if r.status_code != 200:
        raise TransferError(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


def _call_local(chunk: str, rate, target_token):
    return _local.compress(chunk, rate=rate, target_token=target_token)


def _pick_mode(requested: Optional[str], api_key: str) -> str:
    """Decide local vs api. Order: explicit arg > env > auto-detect."""
    mode = (requested or PREFER_MODE).lower()
    if mode == "local":
        return "local"
    if mode == "api":
        return "api"
    # auto
    if _local is not None and _local.is_available():
        return "local"
    return "api"


def compress(
    text: str,
    rate: Optional[float] = None,
    target_token: Optional[int] = None,
    api_key: Optional[str] = None,
    url: Optional[str] = None,
    timeout: float = 120.0,
    fail_soft: Optional[bool] = None,
    mode: Optional[str] = None,
) -> Tuple[str, Dict]:
    """
    Compress text. Local-first if available, API fallback.

    Returns (compressed_text, metrics).
    """
    fail_soft = fail_soft if fail_soft is not None else FAIL_SOFT
    api_key = api_key or DEFAULT_KEY
    if rate is None and target_token is None:
        rate = DEFAULT_RATE

    picked = _pick_mode(mode, api_key)
    if picked == "api" and not api_key:
        if fail_soft:
            return text, {"error": "no_api_key_no_local", "fallback": "passthrough",
                          "hint": "pip install llmlingua torch tiktoken — or set TOKENSTRANSFER_API_KEY"}
        raise TransferError(
            "No TOKENSTRANSFER_API_KEY set and local mode unavailable. "
            "Either pip install llmlingua torch tiktoken or get a free key at "
            "https://transfer.tokenstree.com"
        )

    segments = _segment(text)
    out_parts: List[str] = []
    total_orig = 0
    total_comp = 0
    elapsed_ms = 0
    n_compressed = 0

    for kind, chunk in segments:
        if kind == "preserve" or len(chunk.strip()) < MIN_PROSE_LEN:
            out_parts.append(chunk)
            continue
        try:
            if picked == "local":
                comp, m = _call_local(chunk, rate, target_token)
                total_orig += int(m["tokens_original"])
                total_comp += int(m["tokens_compressed"])
                elapsed_ms += int(m["elapsed_ms"])
            else:
                data = _call_api(chunk, rate, target_token, api_key, url, timeout)
                comp = data.get("compressed_text", chunk)
                mm = data.get("metrics", {})
                total_orig += int(mm.get("tokens_original", 0))
                total_comp += int(mm.get("tokens_compressed", 0))
                elapsed_ms += int(mm.get("processing_time_ms", 0))
            n_compressed += 1
            out_parts.append(comp)
        except (TransferError, requests.RequestException) as e:
            if fail_soft:
                warnings.warn(f"caveman-transfer error on chunk, falling back to passthrough: {e}")
                out_parts.append(chunk)
            else:
                raise

    result = _glue(out_parts)
    metrics = {
        "mode": picked,
        "tokens_original_prose": total_orig,
        "tokens_compressed_prose": total_comp,
        "savings_percent_on_prose": (
            round((1 - total_comp / total_orig) * 100, 1) if total_orig else 0.0
        ),
        "elapsed_ms": elapsed_ms,
        "n_segments": len(segments),
        "n_prose_chunks_compressed": n_compressed,
    }
    return result, metrics


def compress_file(path: str, backup: bool = True, **kwargs) -> Dict:
    with open(path, "r") as f:
        original = f.read()
    compressed, metrics = compress(original, **kwargs)
    if metrics.get("error"):
        return metrics
    if backup:
        with open(f"{path}.original.md", "w") as f:
            f.write(original)
    with open(path, "w") as f:
        f.write(compressed)
    metrics["backup_path"] = f"{path}.original.md" if backup else None
    return metrics


HAIKU_45_IN  = 1.0
HAIKU_45_OUT = 5.0
def estimate_savings_usd(tokens_saved: int, side: str = "input", model: str = "haiku-4.5") -> float:
    price = HAIKU_45_IN if side == "input" else HAIKU_45_OUT
    return round(tokens_saved * price / 1_000_000, 6)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m caveman_transfer.client <file_or_text> [rate]", file=sys.stderr)
        sys.exit(1)
    arg = sys.argv[1]
    rate = float(sys.argv[2]) if len(sys.argv) > 2 else None
    if os.path.isfile(arg):
        m = compress_file(arg, rate=rate)
        print(json.dumps(m, indent=2))
    else:
        out, m = compress(arg, rate=rate)
        print(out)
        print("---", file=sys.stderr)
        print(json.dumps(m, indent=2), file=sys.stderr)
