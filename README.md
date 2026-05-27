# caveman_tokenstransfer.2.0

> 🪨 + 🧠 — **caveman make mouth small.** **TokensTransfer make ear small.** Together: bill small.

[caveman](https://github.com/JuliusBrussee/caveman) (64k★) cut Claude's *output* tokens by 65% with a caveman dialect. Brilliant. But ~70% of your spend on long-context apps is the *input*: system prompts, RAG context, tool definitions, memory files. That side, caveman barely touches.

This fork adds **TokensTransfer** (LLMLingua-2 hosted at [transfer.tokenstree.com](https://transfer.tokenstree.com)) as a peer skill. Same caveman install flow. Same 30+ agents supported. New result: **input -53% on average. Stacked with caveman output: -55% per call.**

## One-line install (everything from upstream caveman + new transfer skills)

```bash
# macOS / Linux / WSL
curl -fsSL https://raw.githubusercontent.com/vfalbor/caveman_tokenstransfer.2.0/main/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/vfalbor/caveman_tokenstransfer.2.0/main/install.ps1 | iex
```

Then set your free TokensTransfer API key (sign up at [transfer.tokenstree.com](https://transfer.tokenstree.com)):

```bash
export TOKENSTRANSFER_API_KEY="tt_..."
```

Use:
- `/caveman` — output side, 4 levels (lite | full | ultra | wenyan)
- `/caveman-transfer <file|prompt>` — input side, hosted LLMLingua-2
- `/caveman-fullstack` — both at once (RAG, agents)
- `/caveman-compress <file>` — original local input rule-based (offline)

## Three-way head-to-head

Same 25 prompts across 4 suites (coding, RAG, agent, multilingual). Token counts via `tiktoken cl100k_base` (Claude tokenizer within ~2% on Latin scripts). Cost model uses Haiku 4.5 ($1/M input, $5/M output).

### Average cost reduction per call

| Configuration | Coding | RAG | Agent | Multilingual | **Overall avg** |
|---|---:|---:|---:|---:|---:|
| Baseline | — | — | — | — | — |
| **Caveman only** (output -65%) | -65% | -62% | -63% | -65% | **-60.2%** |
| **Transfer only** (input -53%) | -2% | -27% | -42% | -3% | **-3.7%** |
| **🔥 Fullstack 2.0** (both) | -65% | -64% | -69% | -65% | **-63.9%** |

The bigger the input/output ratio, the more transfer matters. On RAG-style calls (long context, short answer), transfer alone saves 27%. On agent loops with system prompts + tool defs, transfer alone saves 42%. Stacking with caveman tops out at -69%.

### Why is "transfer only" small on coding?

Because in these benchmark prompts the *output* (typically 500 tokens at Haiku rates) dominates the bill more than the *input* (20-30 tokens). When the call is short-prompt / long-answer, caveman alone is enough. When the call is long-prompt / short-answer (RAG, agents), transfer is the bigger lever.

That's why we built **fullstack**: pick the workload, both compressions fire automatically.

### Workload picker

| Your workload | Use this | Why |
|---|---|---|
| Chat assistant (short Q, short A) | `/caveman lite` | Output dominates, but compression overhead matters |
| Code review (long file in, short suggestions out) | `/caveman-fullstack` | Both sides material |
| RAG / Q&A (long context, short answer) | `/caveman-transfer` + `/caveman lite` | Input dominates |
| Agent loop (system + tools + history) | `/caveman-fullstack` | Input dominates massively |
| Long-form generation (short prompt, long doc) | `/caveman ultra` | Output dominates |
| Memory file compression (offline) | `/caveman-compress` (local) or `/caveman-transfer` (hosted, deeper) | One-shot |

## Reproduction

```bash
git clone https://github.com/vfalbor/caveman_tokenstransfer.2.0
cd caveman_tokenstransfer.2.0/benchmarks/v2-integrated
pip install -r requirements.txt
export TOKENSTRANSFER_API_KEY="tt_..."
export TOKENTRANSLATION_API_KEY="tk_..."  # optional, for multilingual
python3 benchmark_v2.py
```

Raw results in [`benchmarks/v2-integrated/results.json`](benchmarks/v2-integrated/results.json). The independent input-side comparison (caveman-compress vs LLMLingua-2 on caveman's own prompts) lives at [vfalbor/llm-language-token-tax/vs-caveman](https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman).

## What's in this fork (vs upstream caveman)

| | Upstream caveman | caveman_tokenstransfer.2.0 |
|---|---|---|
| Output dialect (`/caveman`) | ✅ | ✅ (unchanged) |
| Local input rules (`/caveman-compress`) | ✅ | ✅ (unchanged) |
| Hosted input LLMLingua-2 (`/caveman-transfer`) | ❌ | ✅ **new** |
| Combined input+output (`/caveman-fullstack`) | ❌ | ✅ **new** |
| Memory file compression | rule-based local | rule-based local + hosted semantic |
| Multilingual prompt → English token-efficient form | ❌ | ✅ (via [translation.tokenstree.com](https://translation.tokenstree.com)) |
| Installer for 30+ agents | ✅ | ✅ (rebranded, same coverage) |

All upstream skills/agents continue to work unchanged. The new skills are additive.

## Caveats

1. **Output quality on compressed input is the next benchmark.** Token counts are real; downstream accuracy on a compressed RAG prompt vs an original prompt needs Claude in the loop to measure. LLMLingua-2's published evals (ACL 2024) show parity at `rate=0.5` on QA/summarization. We'll publish a TokensTree-specific quality eval shortly.
2. **Network roundtrip.** `/caveman-transfer` is a hosted service; expect 500-2000ms added latency. For latency-critical paths, `/caveman-compress` (local rules) is the fallback.
3. **This is a fork.** Credit to [@JuliusBrussee](https://github.com/JuliusBrussee). The output side of this stack is his work. We added the input side and the integration.

## License

MIT (inherited from upstream caveman). Commercial use, modification, redistribution — all permitted.

## Star ⭐

If this saved you bill money, star this repo. Star [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) too — they did the hard half.
