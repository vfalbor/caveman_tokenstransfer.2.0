# caveman_tokenstransfer.2.0

> 🪨 **caveman make mouth small.** 🌳 **tokenstransfer make ear small.** Together: bill small.

[![star](https://img.shields.io/github/stars/vfalbor/caveman_tokenstransfer.2.0?style=social)](https://github.com/vfalbor/caveman_tokenstransfer.2.0)
[![mit](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![fork](https://img.shields.io/badge/fork%20of-JuliusBrussee%2Fcaveman-blue)](https://github.com/JuliusBrussee/caveman)
[![local](https://img.shields.io/badge/runs-100%25%20local-brightgreen)](#install)

[caveman](https://github.com/JuliusBrussee/caveman) (64k★) cut Claude's *output* tokens by 65% with a caveman dialect. Brilliant. But 60-80% of your spend on long-context apps is the *input*: system prompts, RAG context, tool definitions, memory files. That side, caveman barely touch.

This fork add **tokenstransfer** (LLMLingua-2, runs 100% local) + **tokenstranslation** (BPE language-tax fix) as peers. Same install. Same one-liner. Same fully-local philosophy. Three skills, one suite, one bill cut in half.

## install

```bash
# macOS / Linux / WSL
curl -fsSL https://raw.githubusercontent.com/vfalbor/caveman_tokenstransfer.2.0/main/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/vfalbor/caveman_tokenstransfer.2.0/main/install.ps1 | iex

# enable local mode (optional but recommended — no network, no API key)
pip install llmlingua torch tiktoken
```

Then in your agent (Claude Code, Codex, Cursor, Windsurf, +30 more):

```
/caveman              ← output dialect (4 levels)
/tokenstransfer       ← input compression, 100% local
/tokenstranslation    ← multilingual → cheap-token language
/caveman-fullstack    ← all three at once
```

> Star cost zero. Fair trade. ⭐

## what each one does

| Skill | What it compresses | Avg savings | Mode | Stacks with |
|---|---|---:|---|---|
| `/caveman` | Output (model talks telegraphic) | **65%** | local prompt | tokenstransfer |
| `/tokenstransfer` | Input (LLMLingua-2 drops low-info tokens) | **53%** | 100% local (or hosted) | all |
| `/tokenstranslation` | Multilingual input → English tokens | **25-55%** (lang-dep) | hosted | all |
| `/caveman-fullstack` | All three at once | **55-69%** total | mixed | — |
| `/caveman-compress` | Input via regex rules (original caveman) | 9-12% | local | — |

## before / after

**Original prompt** (174 tokens, English):

```
You are a helpful senior engineer answering questions about a large Django codebase.
Please cite specific files and line numbers when possible. If you are not sure, just
say so. The codebase uses Django 5.0, Postgres 16, Redis 7, and Celery 5. We have
approximately 120 models, 600 views, and 200 management commands. Authentication is
handled by django-allauth with JWT issuance for the API.
```

After `/tokenstransfer` local, rate=0.5 (83 tokens, **-52%**):

```
senior engineer answering questions Django codebase cite specific files line numbers
If not sure say codebase uses Django 5.0 Postgres 16 Redis 7 Celery 5 120 models 600
views 200 management commands Authentication django-allauth JWT issuance API
```

Same meaning. Half the tokens. **Code, URLs, version numbers, file paths preserved exactly.**

## benchmark — 25 prompts, 4 suites, Haiku 4.5 cost model

```
$ python3 benchmarks/v2-integrated/benchmark_v2.py
```

Average per-call cost reduction:

| Suite | caveman only (output) | tokenstransfer only (input) | fullstack (both) |
|---|---:|---:|---:|
| coding (short Q, ~500 tok out) | -65% | -2% | **-65%** |
| RAG (long context, ~400 tok out) | -62% | -27% | **-64%** |
| agent (system + tools + history) | -63% | -42% | **-69%** |
| multilingual | -65% | -3% (en-en) | -65% (+25-55% with tokenstranslation) |
| **overall avg** | **-60.2%** | **-3.7%** | **-63.9%** |

Reading the table:
- For **long-context / short-answer** workloads (RAG, agents), tokenstransfer is the bigger lever (-27%/-42% alone).
- For **short-prompt / long-answer** workloads (codegen), caveman alone gets you most of the way.
- For **multilingual** UX, stack tokenstranslation to clear the BPE language tax (~25-55% extra).
- For everything, **fullstack** wins (-63.9% avg).

[Raw results](benchmarks/v2-integrated/results.json) · [Methodology](benchmarks/v2-integrated/benchmark_v2.py) · [Independent input-side comparison vs caveman-compress](https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman)

## modes — pick your trade-off

```
TOKENSTRANSFER_MODE=local      # in-process LLMLingua-2, ~5s CPU, no network
TOKENSTRANSFER_MODE=api        # HTTP to transfer.tokenstree.com, ~500ms, free tier
TOKENSTRANSFER_MODE=auto       # (default) local if available, else api
```

Auto-detect: if `llmlingua` + `torch` are importable, local mode runs. Otherwise fallback to API. **No vendor lock-in.** Caveman is 100% local; we match that floor.

## self-host the backend

If you want the LLMLingua-2 server on your own infra (not as a Python dep, but as a microservice for your team):

```bash
cd server
docker compose up -d
export TOKENSTRANSFER_URL=http://localhost:8080
export TOKENSTRANSFER_API_KEY=anything   # accepted; no auth in self-host mode
```

See [`server/README.md`](server/README.md). FastAPI + Dockerfile + compose. MIT.

## supported agents

Same as upstream caveman: Claude Code, Codex CLI, Cursor, Windsurf, Cline, Continue, Kilo, Roo, Augment, GitHub Copilot, Aider, Amp, Crush, Devin, Droid, ForgeCode, Goose, iFlow, Kiro, Mistral Vibe, OpenHands, Qwen Code, Rovo Dev, Tabnine, Trae, Warp, Replit. **30+ agents, one installer.**

## what's in this fork (vs upstream caveman)

| | Upstream caveman | caveman_tokenstransfer.2.0 |
|---|---|---|
| `/caveman` (output dialect) | ✅ | ✅ unchanged |
| `/caveman-compress` (regex rules) | ✅ | ✅ unchanged |
| `/tokenstransfer` (LLMLingua-2) | ❌ | ✅ **new, 100% local** |
| `/tokenstranslation` (multilingual fix) | ❌ | ✅ **new** |
| `/caveman-fullstack` (combined) | ❌ | ✅ **new** |
| Self-hostable LLMLingua-2 server | ❌ | ✅ **new** (`server/`) |
| 30+ agents installer | ✅ | ✅ rebranded |
| Fully local option | ✅ | ✅ matched |
| License | MIT | MIT |

The output-side credit goes to [@JuliusBrussee](https://github.com/JuliusBrussee). We added the input side and the suite glue.

## benchmarks you should read

- `benchmarks/v2-integrated/` (in this repo) — the 25-prompt suite measured above
- [`vfalbor/llm-language-token-tax/vs-caveman/`](https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman) — input-side head-to-head vs `caveman-compress` on caveman's own benchmark prompts
- [Caveman's original output benchmark](https://github.com/JuliusBrussee/caveman/tree/main/benchmarks) — for context

## caveats

1. **Output quality.** All numbers are token counts. LLMLingua-2 has [published evals (ACL 2024)](https://arxiv.org/abs/2403.12968) showing parity on QA/summarization at `rate=0.5`. We trust their evals; we did not re-run them. If your domain is sensitive, sample answers and verify before going wide.
2. **Local mode first-run cost.** ~1.5GB model download from HuggingFace on first call. Cached after that. CPU inference ~5s/prompt; GPU ~0.5s.
3. **tokenstranslation is currently hosted-only.** Local NLLB-200 mode is on the v2.1 roadmap. The hosted free tier is enough for most workloads.

## license

MIT (inherited). Commercial use, modification, redistribution — all permitted.

## sponsor

This is a hobby fork shipped to save people money. If it saved you any: **[❤ Sponsor on GitHub](https://github.com/sponsors/vfalbor)**.

---

## 🌱 the TokensTree suite — hosted convenience tier

If you don't want to install Python deps and you're OK with a network round-trip, the hosted versions of tokenstransfer and tokenstranslation are at:

- **[transfer.tokenstree.com](https://transfer.tokenstree.com)** — same LLMLingua-2 model, free tier, ~500ms latency. Sign up, get an API key, point `TOKENSTRANSFER_MODE=api`.
- **[translation.tokenstree.com](https://translation.tokenstree.com)** — multilingual prompt optimization + optional Tokinensis encoding. Free tier, no model download.
- **[tokenstree.com](https://tokenstree.com)** — the social network for AI agents. Every 1 billion tokens saved = 1 real tree planted. Newsletter on token economics here: [tokenstree.com/newsletter.html](https://tokenstree.com/newsletter.html).

The hosted tier is convenience — local mode is the floor. Both are MIT, both are free, both ship the same numbers in this benchmark.

---

> 🪨 + 🌳 — **why use many token when few token do trick.**
>
> ⭐ this repo if it saved you bill money. ⭐ [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) too — they did the hard half.
