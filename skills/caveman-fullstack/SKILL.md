---
name: caveman-fullstack
description: >
  End-to-end token compression. Combines caveman-transfer (input side, LLMLingua-2,
  ~53% input savings) with caveman (output side, telegraphic dialect, ~65% output savings).
  Use when you want maximum bill reduction on long-context workloads (RAG, agents, code review).
  Trigger: /caveman-fullstack or "compress everything" or "save max tokens".
---

# Caveman Fullstack

## Purpose

The full caveman_tokenstransfer.2.0 stack. Two compressions, one command:

1. **Input side** — call `transfer.tokenstree.com` (LLMLingua-2) on the prompt before sending. -53% input tokens.
2. **Output side** — activate caveman dialect on the response. -65% output tokens.

On a typical RAG call with Haiku 4.5 (10k input / 500 output), this cuts the per-call cost by **55%**. Measured numbers in [benchmarks/v2-integrated/results.json](../../benchmarks/v2-integrated/results.json).

## Trigger

`/caveman-fullstack` — also activates automatically when:
- Input prompt > 5,000 tokens AND user requests cost optimization.
- User says "save max tokens", "minimize spend", "compress everything".

## Process

1. Capture the user's full input (system prompt + context + question).
2. Identify code blocks, URLs, file paths — mark as preserve regions.
3. POST the prose regions to `https://transfer.tokenstree.com/compress` (rate=0.5).
4. Reassemble with preserve regions intact.
5. Activate caveman output dialect for the response (`/caveman full` default).
6. Send. Report savings:
   ```
   Input: 10,247 → 4,816 tokens (-53%)
   Output budget: caveman dialect (~65% reduction expected)
   Estimated savings: 55% on this call
   ```

## When NOT to use

- Very short prompts (<200 input tokens). Fixed compression overhead dominates.
- Prompts requiring verbatim quotation of input (legal, exam questions). LLMLingua-2 paraphrases — set rate=0.8 or skip transfer step.
- Outputs that must be in formal prose (customer-facing emails, marketing copy). Skip caveman output, keep transfer.

For those cases use `/caveman-transfer` alone (input only) or `/caveman lite` (mild output compression).

## Configuration

```bash
export TOKENSTRANSFER_API_KEY="tt_..."
export CAVEMAN_FULLSTACK_DEFAULT_LEVEL="full"   # lite|full|ultra
export CAVEMAN_FULLSTACK_TRANSFER_RATE="0.5"
```

## Telemetry

If `CAVEMAN_FULLSTACK_TELEMETRY=true`, the skill logs per-call savings to `~/.caveman-fullstack/log.jsonl`. Aggregate stats via:

```bash
python3 -m caveman_fullstack.stats --since 30d
```

Reports: total calls, total tokens saved, estimated $ saved (using Haiku 4.5 pricing).

## See also

- `/caveman-transfer` — input side only
- `/caveman` — output side only
- [vs-caveman benchmark](https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman) — independent input-side comparison.
- [benchmarks/v2-integrated](../../benchmarks/v2-integrated) — fullstack integrated benchmark.
