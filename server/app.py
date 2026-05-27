"""
caveman-tokenstransfer self-hostable LLMLingua-2 compression server.

Minimal FastAPI app exposing the same /compress endpoint as
transfer.tokenstree.com, no auth, no DB. Run it yourself with:

    docker compose up

Or:

    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8080

Then point the client at it:

    export TOKENSTRANSFER_URL=http://localhost:8080
    export TOKENSTRANSFER_API_KEY=anything   # accepted; no auth in self-host mode
"""
from __future__ import annotations
import logging
import os
import time
from typing import Optional, List

import tiktoken
from fastapi import FastAPI
from pydantic import BaseModel, Field

LLMLINGUA_MODEL = os.environ.get(
    "LLMLINGUA_MODEL", "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
)
LLMLINGUA_DEVICE = os.environ.get("LLMLINGUA_DEVICE", "cpu")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ct-server")

app = FastAPI(
    title="caveman-tokenstransfer (self-hostable)",
    version="2.0.0",
    description="LLMLingua-2 prompt compression. Drop-in for transfer.tokenstree.com.",
)

_enc = None
_compressor = None
_load_error: Optional[str] = None


def enc() -> tiktoken.Encoding:
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding("cl100k_base")
    return _enc


def compressor():
    global _compressor, _load_error
    if _compressor is not None:
        return _compressor
    if _load_error:
        return None
    try:
        logger.info(f"Loading LLMLingua-2: {LLMLINGUA_MODEL} on {LLMLINGUA_DEVICE}")
        from llmlingua import PromptCompressor
        _compressor = PromptCompressor(
            model_name=LLMLINGUA_MODEL,
            use_llmlingua2=True,
            device_map=LLMLINGUA_DEVICE,
        )
        logger.info("Loaded.")
        return _compressor
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load model: {e}")
        return None


class CompressRequest(BaseModel):
    text: str = Field(..., min_length=1)
    rate: Optional[float] = Field(None, ge=0.05, le=0.95)
    target_token: Optional[int] = Field(None, ge=10, le=20000)
    force_tokens: Optional[List[str]] = None


@app.get("/health")
def health():
    c = compressor()
    return {
        "status": "ok" if c is not None else "model_unavailable",
        "version": "2.0.0",
        "model": {
            "name": LLMLINGUA_MODEL,
            "device": LLMLINGUA_DEVICE,
            "ready": c is not None,
            "error": _load_error,
        },
    }


@app.post("/compress")
def compress(req: CompressRequest):
    """
    Compress prompt text with LLMLingua-2.

    Either pass `target_token` (compress to this many tokens) or `rate`
    (keep this fraction of tokens, e.g. 0.5).
    """
    c = compressor()
    if c is None:
        return {
            "error": "model_unavailable",
            "detail": _load_error,
            "compressed_text": req.text,  # passthrough so caller doesn't break
            "metrics": {"fallback": "passthrough"},
        }

    t0 = time.time()
    tokens_original = len(enc().encode(req.text))
    kwargs = {}
    if req.target_token is not None:
        kwargs["target_token"] = req.target_token
    if req.rate is not None:
        kwargs["rate"] = req.rate
    if req.force_tokens:
        kwargs["force_tokens"] = req.force_tokens

    result = c.compress_prompt(req.text, **kwargs)
    compressed_text = result.get("compressed_prompt", "") if isinstance(result, dict) else str(result)
    tokens_compressed = len(enc().encode(compressed_text))
    elapsed_ms = int((time.time() - t0) * 1000)

    return {
        "compressed_text": compressed_text,
        "metrics": {
            "tokens_original": tokens_original,
            "tokens_compressed": tokens_compressed,
            "tokens_saved": tokens_original - tokens_compressed,
            "compression_ratio": (
                round(tokens_original / tokens_compressed, 2)
                if tokens_compressed else None
            ),
            "savings_percent": (
                round((1 - tokens_compressed / tokens_original) * 100, 1)
                if tokens_original else 0.0
            ),
            "processing_time_ms": elapsed_ms,
            "method": "llmlingua2-self-hosted",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
