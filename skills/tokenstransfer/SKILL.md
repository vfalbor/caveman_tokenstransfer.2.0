---
name: tokenstransfer
description: >
  Input-side token compression. Drop 50-55% of input tokens BEFORE they reach Claude.
  Runs 100% local by default (LLMLingua-2 in-process, ~1.5GB one-time model download)
  or via the hosted convenience tier at transfer.tokenstree.com. Preserves code blocks,
  URLs, file paths, markdown structure exactly. Peer to caveman: caveman cuts what the
  model SAYS, tokenstransfer cuts what the model HEARS. Stack both for max savings.
  Trigger: /tokenstransfer <text|file> or "compress prompt" or "compress input".
---

# tokenstransfer

> 🪨 caveman make mouth small. 🌳 **tokenstransfer make ear small.** Together: bill small.

Caveman compresses the model's *output*. tokenstransfer compresses the *input*. On long-context apps (RAG, agents, memory-heavy chats) input is 60-80% of the bill. caveman barely touches that side. tokenstransfer takes 50-55% off the top.

## Modes

| Mode | What | Setup | Latency | Cost |
|---|---|---|---|---|
| **local** (default) | LLMLingua-2 in your Python process | `pip install llmlingua torch tiktoken` | ~5s CPU / ~0.5s GPU | free |
| **api** (fallback) | HTTP to transfer.tokenstree.com | `export TOKENSTRANSFER_API_KEY=tt_...` | ~500-2000ms | free tier + paid |

Auto-detect: if `llmlingua` is importable, local mode is used; otherwise falls back to API. Force a mode with `TOKENSTRANSFER_MODE=local|api`.

## Trigger

`/tokenstransfer <filepath>` or `/tokenstransfer "<text>"` — or invoke when:
- User pastes a long prompt and asks "make this smaller"
- Memory/CLAUDE.md/RAG context > 2k tokens
- User says "compress prompt", "shrink input", "save tokens"
- A system prompt has >500 tokens and is reused across calls (compress once, cache)

## Preserved exactly

`code blocks` ``` …code… ``` `inline` https://urls `file/paths.ext` `# markdown headings` `- list markers`. Only prose is sent through the compressor.

## Example

Before (174 tokens):
> "You are a helpful senior engineer answering questions about a large Django codebase. Please cite specific files and line numbers when possible. If you are not sure, just say so. The codebase uses Django 5.0, Postgres 16, Redis 7, and Celery 5. We have approximately 120 models, 600 views, and 200 management commands. Authentication is handled by django-allauth with JWT issuance for the API."

After local mode, rate=0.5 (83 tokens, -52%):
> "senior engineer answering questions Django codebase cite specific files line numbers If not sure say codebase uses Django 5.0 Postgres 16 Redis 7 Celery 5 120 models 600 views 200 management commands Authentication django-allauth JWT issuance API"

Same meaning. Half the tokens. Code, URLs, version numbers preserved exactly.

## Config

```bash
# choose one
pip install llmlingua torch tiktoken              # local mode (recommended, no network)
export TOKENSTRANSFER_API_KEY="tt_..."            # OR api mode

# optional
export TOKENSTRANSFER_MODE="local"                # force mode (auto|local|api)
export TOKENSTRANSFER_RATE="0.5"                  # 0.5 = keep 50%
export LLMLINGUA_DEVICE="cuda"                    # if you have a GPU
```

## See also

- `/caveman` — output-side compression dialect
- `/tokenstranslation` — multilingual prompt → English token-efficient form
- `/caveman-fullstack` — caveman + tokenstransfer in one command
- `server/` — self-hostable backend if you don't want hosted or in-process
