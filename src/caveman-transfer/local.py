"""
caveman_tokenstransfer.2.0 — 100% local LLMLingua-2 inference.

Runs the LLMLingua-2 prompt compression model in-process on the user's machine.
No network, no API key, no transfer.tokenstree.com round-trip. Caveman-style:
fully local.

First-use cost: downloads ~1.5GB model from HuggingFace (one time, cached
in ~/.cache/huggingface).

CPU inference: ~5s on a 500-token prompt. GPU: ~0.5s. Set device via env.

Usage:
    from caveman_transfer import local as ctl
    out, m = ctl.compress("long prompt...", rate=0.5)

Or via the unified client (auto-detects local vs API):
    from caveman_transfer.client import compress
    out, m = compress("...")     # uses local if llmlingua installed, else API
"""
from __future__ import annotations
import logging
import os
import time
from typing import Optional, Tuple, Dict

logger = logging.getLogger("caveman_transfer.local")

DEFAULT_MODEL = os.environ.get(
    "LLMLINGUA_MODEL", "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
)
DEFAULT_DEVICE = os.environ.get("LLMLINGUA_DEVICE", "cpu")

_compressor = None
_load_error: Optional[str] = None


def is_available() -> bool:
    """True if local mode can run (llmlingua + torch importable)."""
    try:
        import llmlingua  # noqa: F401
        import torch       # noqa: F401
        return True
    except ImportError:
        return False


def _enc():
    import tiktoken
    if not hasattr(_enc, "_e"):
        _enc._e = tiktoken.get_encoding("cl100k_base")
    return _enc._e


def _load():
    """Lazy-load the LLMLingua-2 PromptCompressor."""
    global _compressor, _load_error
    if _compressor is not None:
        return _compressor
    if _load_error:
        return None
    try:
        from llmlingua import PromptCompressor
        logger.info(f"Loading {DEFAULT_MODEL} on {DEFAULT_DEVICE} (first run downloads ~1.5GB)")
        _compressor = PromptCompressor(
            model_name=DEFAULT_MODEL,
            use_llmlingua2=True,
            device_map=DEFAULT_DEVICE,
        )
        return _compressor
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load local LLMLingua-2: {e}")
        return None


def compress(
    text: str,
    rate: Optional[float] = None,
    target_token: Optional[int] = None,
    force_tokens: Optional[list] = None,
) -> Tuple[str, Dict]:
    """
    Compress text locally with LLMLingua-2. Same return shape as client.compress().

    Returns (compressed_text, metrics). Raises RuntimeError if local mode
    unavailable.
    """
    if not is_available():
        raise RuntimeError(
            "Local mode requires 'llmlingua' and 'torch'. "
            "Install: pip install llmlingua torch tiktoken"
        )
    c = _load()
    if c is None:
        raise RuntimeError(f"Failed to load LLMLingua-2: {_load_error}")

    t0 = time.time()
    tokens_original = len(_enc().encode(text))

    kwargs = {}
    if target_token is not None:
        kwargs["target_token"] = target_token
    if rate is not None:
        kwargs["rate"] = rate
    if force_tokens:
        kwargs["force_tokens"] = force_tokens

    result = c.compress_prompt(text, **kwargs)
    compressed = result.get("compressed_prompt", "") if isinstance(result, dict) else str(result)
    tokens_compressed = len(_enc().encode(compressed))

    metrics = {
        "tokens_original": tokens_original,
        "tokens_compressed": tokens_compressed,
        "tokens_saved": tokens_original - tokens_compressed,
        "savings_percent": (
            round((1 - tokens_compressed / tokens_original) * 100, 1)
            if tokens_original else 0.0
        ),
        "elapsed_ms": int((time.time() - t0) * 1000),
        "mode": "local",
        "model": DEFAULT_MODEL,
        "device": DEFAULT_DEVICE,
    }
    return compressed, metrics


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print(f"Available: {is_available()}")
        sys.exit(0)
    arg = sys.argv[1]
    rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    text = open(arg).read() if os.path.isfile(arg) else arg
    out, m = compress(text, rate=rate)
    print(out)
    print("---", file=sys.stderr)
    print(json.dumps(m, indent=2), file=sys.stderr)
