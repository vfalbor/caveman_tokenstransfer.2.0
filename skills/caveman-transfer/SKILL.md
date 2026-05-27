---
name: caveman-transfer
description: >
  Input-side token compression via TokensTransfer (LLMLingua-2). Compress long system prompts,
  RAG context, memory files, and tool definitions before they reach Claude. Cuts ~53% of input
  tokens on average. Complements core caveman (which cuts output tokens). Use when prompt is
  long, contains retrieved context, or includes verbose system instructions.
  Trigger: /caveman-transfer <text|file> or "compress input" or "compress prompt".
---

# Caveman Transfer

## Purpose

Caveman makes the *model talk less*. caveman-transfer makes the *prompt smaller* before sending. Different sides of the bill. They compose.

The skill calls **[transfer.tokenstree.com](https://transfer.tokenstree.com)** — a hosted LLMLingua-2 (`xlm-roberta-large` fine-tuned for prompt compression) — and returns the semantically compressed text. LLMLingua-2 drops low-information tokens while preserving meaning. Independent benchmark: -52.9% average input tokens across the caveman benchmark suite, with code/URLs/proper nouns preserved.

## Trigger

`/caveman-transfer <filepath>` or `/caveman-transfer "<text>"` — or invoke when:
- User pastes a long prompt and asks "make this smaller"
- Memory/CLAUDE.md/RAG context exceeds ~2k tokens
- User says "compress prompt", "compress context", "shrink input"

## Process

1. Read or accept the text to compress.
2. POST to `https://transfer.tokenstree.com/compress` with body:
   ```json
   { "text": "<input>", "rate": 0.5 }
   ```
   Header: `X-API-Key: $TOKENSTRANSFER_API_KEY` (free signup at transfer.tokenstree.com).
3. Receive compressed text + metrics (`tokens_original`, `tokens_compressed`, `savings_percent`).
4. If the file is a memory file (CLAUDE.md, AGENTS.md, etc), write the compressed version in place and back up the original to `<file>.original.md`.
5. Report savings to user: "Compressed X → Y tokens (-Z%)".

## When to use which mode

| Workload | Use caveman | Use caveman-transfer | Use both (`caveman-fullstack`) |
|---|---|---|---|
| Chat (short input, medium output) | ✅ | — | optional |
| Code generation (long output) | ✅✅ | — | ✅ |
| RAG (long context, short answer) | optional | ✅✅ | ✅✅ |
| Agent loop (system + tools + history) | optional | ✅✅ | ✅✅ |
| Memory file compression | — | ✅✅ | — |

Rule of thumb: if input > 3× output, prioritize caveman-transfer. If output > input, prioritize caveman.

## Preserved Exactly

The transfer service preserves code blocks, URLs, proper nouns, numbers, file paths, and command names. Same guarantees as caveman-compress, but the model does it semantically rather than via regex — handles edge cases the rule-based version misses.

## Configuration

Set once per agent:

```bash
export TOKENSTRANSFER_API_KEY="tt_..."   # free at transfer.tokenstree.com
```

Optional:
```bash
export TOKENSTRANSFER_RATE="0.5"        # keep 50% of tokens (default)
export TOKENSTRANSFER_URL="https://transfer.tokenstree.com"
```

## Comparison vs caveman-compress

| | caveman-compress | caveman-transfer |
|---|---|---|
| Algorithm | Regex rules | LLMLingua-2 (ML) |
| Avg savings on caveman bench | 8.6% | **52.9%** |
| Latency | <50ms local | ~500-2000ms HTTP |
| Network required | no | yes |
| Quality on edge cases | rule-based | semantic |
| Cost | free | free tier, paid above |

caveman-compress is great when offline / latency-critical / simple text. caveman-transfer wins on serious savings for production workloads.

## See also

- `/caveman` — output-side compression (talk telegraphic)
- `/caveman-compress` — local rule-based input compression (lighter weight)
- `/caveman-fullstack` — orchestrates caveman + caveman-transfer for end-to-end savings
