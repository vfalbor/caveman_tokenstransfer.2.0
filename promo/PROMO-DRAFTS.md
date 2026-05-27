# Promotion drafts — copy-paste, you publish

These are drafts for channels I cannot post on myself (HN, Reddit, awesome-list issues). Adjust tone if you want; the numbers are all real.

---

## Hacker News — Show HN

**Title** (HN cap: 80 chars):
```
Show HN: I forked caveman and added input-side compression (LLMLingua-2, local)
```

**URL field**:
```
https://github.com/vfalbor/caveman_tokenstransfer.2.0
```

**Text** (optional, only if you want a story):
```
Caveman (https://github.com/JuliusBrussee/caveman, 64k stars in two weeks) cuts Claude's output tokens by 65% by making the model talk telegraphic. Great for codegen. Smaller win for RAG/agent workloads where the input is 80%+ of the bill.

I forked it and added two peer skills on the input side:

- /tokenstransfer — LLMLingua-2 (microsoft/llmlingua-2-xlm-roberta-large), runs 100% local with `pip install llmlingua torch tiktoken`. No API key, no network. Matches caveman's fully-local philosophy.
- /tokenstranslation — multilingual prompt → English (BPE-cheap tokens) for non-English UX. Cuts another 25-55% off non-English calls.
- /caveman-fullstack — both at once.

Benchmark, 25 prompts, 4 suites, tiktoken cl100k_base, Haiku 4.5 cost model:

  coding  caveman -65% / transfer -2%  / fullstack -65%
  RAG     caveman -62% / transfer -27% / fullstack -64%
  agent   caveman -63% / transfer -42% / fullstack -69%
  
Same install pattern as caveman (curl | bash, 30+ agents). MIT. Polite courtesy ping is up at JuliusBrussee/caveman/discussions/454.

Raw results, methodology, reproduction script:
https://github.com/vfalbor/caveman_tokenstransfer.2.0/tree/main/benchmarks/v2-integrated

Independent input-side head-to-head vs caveman-compress on caveman's own benchmark prompts:
https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman

What I'd love feedback on:
1. The fail-soft API fallback in client.py — currently swallows errors and passes through original text. Is that the right default vs raising?
2. The naming. /tokenstransfer was on purpose to give it equal billing with /caveman (not /caveman-transfer). Reads ok or jarring?
3. Whether the quality eval should block the 2.0 cut. LLMLingua-2 has the ACL 2024 evals; should I rerun them on Haiku before pushing harder on the numbers?
```

---

## Reddit — r/ClaudeAI

**Title**:
```
I forked caveman to cut the OTHER side of the bill (input, not output). 100% local. -55% per call on RAG/agents.
```

**Body**:
```
You all saw the caveman repo blow up — Claude talking like a caveman, -65% output tokens, 64k stars in two weeks. Real numbers, real fun.

What it doesn't touch is the input. On any RAG app or agent loop with a long system prompt + retrieved context + tool definitions, the input is 80-90% of your bill. -65% on the 10% half doesn't move the invoice much.

So I forked it: **caveman_tokenstransfer.2.0**.

What it adds (without touching anything upstream caveman ships):
- `/tokenstransfer` — drops ~53% of your input tokens via LLMLingua-2 (microsoft/llmlingua-2-xlm-roberta-large). Runs **100% local** by default — `pip install llmlingua torch tiktoken`, no network, no API key. Same fully-local philosophy caveman has.
- `/tokenstranslation` — same string in Spanish costs 27% more tokens than in English, Arabic 230%. Translates to English on the way in, back on the way out. Free win for non-English UX.
- `/caveman-fullstack` — all three (caveman dialect + tokenstransfer + tokenstranslation) in one command.

Benchmark (25 prompts, Haiku 4.5 cost model):

| Workload | caveman | tokenstransfer | both |
|---|---|---|---|
| Codegen | -65% | -2% | -65% |
| RAG | -62% | -27% | -64% |
| Agent loop | -63% | -42% | **-69%** |

Install is the same `curl | bash` pattern as caveman. Same 30+ agents supported (Claude Code, Codex, Cursor, Windsurf, Cline, Aider, Continue, +24 more).

Repo: https://github.com/vfalbor/caveman_tokenstransfer.2.0

Courtesy show-and-tell ping is up at JuliusBrussee/caveman/discussions/454 — credit where credit's due, they did the hard half.

Star it if it cuts your bill. Star [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) too.

Why use many token when few token do trick. 🪨🌳
```

---

## Reddit — r/LLMDevs (alternate)

**Title**:
```
Benchmark: LLMLingua-2 vs caveman-compress on caveman's own prompts (input-side head-to-head)
```

**Body**:
```
Quick benchmark for anyone debating between rule-based prompt compression (caveman-compress skill) and ML-based (LLMLingua-2).

Setup: caveman's published 10-prompt benchmark, both compressors at equivalent rate, tiktoken cl100k_base.

Results (input tokens reduced):
- caveman-compress (regex rules, the local skill): 8.6%
- LLMLingua-2 (microsoft/llmlingua-2-xlm-roberta-large, hosted): 52.9%

6× delta. The rule-based version is fine for offline / latency-critical / simple text. LLMLingua-2 wins by a lot when you can afford the ~500ms (hosted) or ~5s (CPU local) it takes.

Code + raw results + methodology, all reproducible:
https://github.com/vfalbor/llm-language-token-tax/tree/main/vs-caveman

I packaged it as part of a fork that adds /tokenstransfer (LLMLingua-2, runs 100% local) to the caveman skill suite:
https://github.com/vfalbor/caveman_tokenstransfer.2.0

Not selling anything. Free, MIT, local mode. Hosted tier exists as convenience.
```

---

## Awesome-list issue — `awesome-claude-code`

(The most active awesome-list for Claude tooling. Likely repo: `dpamio/awesome-claude-code` or similar — find the active one before posting.)

**Title**:
```
Add: caveman_tokenstransfer.2.0 — input-side compression peer to caveman
```

**Body**:
```
Hi! Suggesting an addition to the "Token Optimization" / "Skills" section:

**[caveman_tokenstransfer.2.0](https://github.com/vfalbor/caveman_tokenstransfer.2.0)** — Fork of caveman that adds LLMLingua-2 input compression (`/tokenstransfer`, 100% local) and multilingual token-tax fix (`/tokenstranslation`) as peer skills. Stacks with caveman for combined -55% bill reduction on long-context workloads. Same installer covers 30+ agents.

The original [caveman](https://github.com/JuliusBrussee/caveman) (output side, already in this list) is referenced and credited in the fork's README.

Happy to PR directly if preferred.
```

---

## Twitter / X — short version

```
🪨 caveman make mouth small.
🌳 tokenstransfer make ear small.
Together: bill small.

just shipped caveman_tokenstransfer.2.0 — fork of caveman with LLMLingua-2 input compression (100% local) + multilingual fix as peer skills. -55% per call on RAG/agents, MIT, same 30+ agent installer.

https://github.com/vfalbor/caveman_tokenstransfer.2.0

⭐ if it cut your bill. ⭐ @JuliusBrussee/caveman too — they did the hard half.

why use many token when few token do trick.
```

---

## LinkedIn — for serious-product crowd

```
Shipped today: caveman_tokenstransfer.2.0

Context: the "caveman" repo hit 64k GitHub stars in two weeks by cutting Claude's OUTPUT tokens 65% through a caveman dialect. Brilliant for codegen.

But on RAG/agent workloads, the INPUT is 80%+ of the bill. Caveman doesn't touch that.

So I forked it and added two peer skills on the input side:
• /tokenstransfer — LLMLingua-2 prompt compression, runs 100% local (no API key needed), saves 53% of input tokens on average.
• /tokenstranslation — fixes the BPE language tax on non-English prompts (Spanish prompts cost 27% more tokens than English for the same content).

Combined with caveman's output dialect: -69% per call on agent loops, -55% overall.

Same install command as upstream. Same 30+ agents supported. MIT.

The benchmark and methodology are public:
https://github.com/vfalbor/caveman_tokenstransfer.2.0

Credit to Julius Brussee for the output side and the 30-agent installer plumbing. We took the other side.
```
