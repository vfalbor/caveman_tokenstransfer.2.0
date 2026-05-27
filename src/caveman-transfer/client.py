"""
caveman_tokenstransfer.2.0 — Python client for the transfer side.

v3 improvements over v2:
- Preserve markdown headings (#, ##, ###...)
- Preserve bullet/numbered list markers (-, *, 1.)
- Preserve YAML frontmatter blocks (--- ... ---)
- Preserve blank lines (paragraph breaks)
- Inject single-space buffer around preserved inline regions so prose words
  don't glue to backticks after compression
- Skip API call if prose chunk is below MIN_PROSE_LEN
- Fail-soft: on network error, return original text + emit a warning marker
  in metrics — never break the user's downstream LLM call
"""
import os
import re
import json
import time
import warnings
from typing import Optional, Tuple, Dict, List

import requests

DEFAULT_URL = os.environ.get("TOKENSTRANSFER_URL", "https://transfer.tokenstree.com")
DEFAULT_KEY = os.environ.get("TOKENSTRANSFER_API_KEY", "")
DEFAULT_RATE = float(os.environ.get("TOKENSTRANSFER_RATE", "0.5"))
FAIL_SOFT = os.environ.get("TOKENSTRANSFER_FAIL_SOFT", "true").lower() == "true"

# Patterns kept verbatim (highest priority first).
PRESERVE_PATTERNS = [
    re.compile(r"^---\n.*?\n---\n", re.S | re.M),         # YAML frontmatter
    re.compile(r"```.*?```", re.S),                        # fenced code
    re.compile(r"`[^`\n]+`"),                              # inline code
    re.compile(r"https?://\S+"),                           # URLs
    re.compile(r"^\s*#{1,6}\s+.+$", re.M),                 # markdown headings
    re.compile(r"^\s*(?:[-*+]|\d+\.)\s", re.M),            # list bullets/numbers (marker only)
    re.compile(r"\n\s*\n"),                                # blank-line paragraph breaks
]

MIN_PROSE_LEN = 30


class TransferError(RuntimeError):
    pass


def _segment(text: str) -> List[Tuple[str, str]]:
    """Split into ordered [(kind, text), ...] segments. kind ∈ {prose, preserve}."""
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
    """
    Join parts ensuring whitespace doesn't collapse. The compressor strips
    leading/trailing whitespace from prose chunks, so we re-introduce a single
    space at boundaries when both sides are non-whitespace.
    """
    out = []
    for i, p in enumerate(parts):
        if i > 0:
            prev = out[-1]
            if prev and p and not prev[-1].isspace() and not p[0].isspace():
                out.append(" ")
        out.append(p)
    return "".join(out)


def compress(
    text: str,
    rate: Optional[float] = None,
    target_token: Optional[int] = None,
    api_key: Optional[str] = None,
    url: Optional[str] = None,
    timeout: float = 120.0,
    fail_soft: Optional[bool] = None,
) -> Tuple[str, Dict]:
    """
    Compress text via LLMLingua-2.

    Preserves: code blocks, inline code, URLs, markdown headings,
    list markers, blank lines, YAML frontmatter.

    Returns (compressed_text, metrics).
    On network/API error: if fail_soft=True (default), returns original text
    with metrics.error set. Otherwise raises TransferError.
    """
    api_key = api_key or DEFAULT_KEY
    if not api_key:
        if (fail_soft if fail_soft is not None else FAIL_SOFT):
            return text, {"error": "no_api_key", "fallback": "passthrough"}
        raise TransferError(
            "No TOKENSTRANSFER_API_KEY set. Get a free key at https://transfer.tokenstree.com"
        )
    if rate is None and target_token is None:
        rate = DEFAULT_RATE
    fail_soft = fail_soft if fail_soft is not None else FAIL_SOFT

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

        payload: Dict = {"text": chunk}
        if target_token is not None:
            payload["target_token"] = target_token
        if rate is not None:
            payload["rate"] = rate

        t0 = time.time()
        try:
            r = requests.post(
                f"{url or DEFAULT_URL}/compress",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as e:
            if fail_soft:
                warnings.warn(f"caveman-transfer network error, falling back: {e}")
                return text, {"error": str(e), "fallback": "passthrough"}
            raise TransferError(f"Network error contacting transfer service: {e}")

        if r.status_code != 200:
            if fail_soft:
                warnings.warn(f"caveman-transfer HTTP {r.status_code}, falling back")
                return text, {"error": f"http_{r.status_code}", "fallback": "passthrough"}
            raise TransferError(f"HTTP {r.status_code}: {r.text[:200]}")
        try:
            data = r.json()
        except ValueError:
            if fail_soft:
                return text, {"error": "invalid_json", "fallback": "passthrough"}
            raise TransferError(f"Invalid JSON response: {r.text[:200]}")

        compressed = data.get("compressed_text", "")
        m = data.get("metrics", {})
        total_orig += int(m.get("tokens_original", 0))
        total_comp += int(m.get("tokens_compressed", 0))
        elapsed_ms += int((time.time() - t0) * 1000)
        n_compressed += 1
        out_parts.append(compressed)

    result = _glue(out_parts)
    metrics = {
        "tokens_original_prose": total_orig,
        "tokens_compressed_prose": total_comp,
        "savings_percent_on_prose": (
            round((1 - total_comp / total_orig) * 100, 1) if total_orig else 0.0
        ),
        "client_elapsed_ms": elapsed_ms,
        "n_segments": len(segments),
        "n_prose_chunks_compressed": n_compressed,
    }
    return result, metrics


def compress_file(path: str, backup: bool = True, **kwargs) -> Dict:
    """Compress a memory file in place. Backs up original to <path>.original.md."""
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


# Optional cost estimation helper
HAIKU_45_IN  = 1.0
HAIKU_45_OUT = 5.0
def estimate_savings_usd(tokens_saved: int, model: str = "haiku-4.5", side: str = "input") -> float:
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
