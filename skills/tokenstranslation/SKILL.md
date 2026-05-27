---
name: tokenstranslation
description: >
  Multilingual token-tax fix. Translates non-English prompts to English (the cheapest
  BPE language) before they reach Claude, then translates the response back. Stacks
  with tokenstransfer and caveman. Saves 25-55% extra on Spanish/French/German/Portuguese/
  Italian/Japanese/Chinese inputs. Free hosted at translation.tokenstree.com.
  Trigger: /tokenstranslation or "translate prompt to cheap tokens".
---

# tokenstranslation

> Same string in Spanish costs 27% more tokens than in English. Arabic: 230% more. Japanese: 193% more. This is the BPE language tax. We fix it.

Tokenization is biased toward English because the training corpora are. Non-English UX pays a permanent tax on every API call. tokenstranslation detects the source language, translates to English on the way in, translates Claude's response back on the way out. The user sees their native language. The bill sees English.

## When this is worth it

| Your UX language | Tax vs English | What tokenstranslation saves |
|---|---:|---:|
| Spanish, Portuguese, Italian, French | 25-35% extra | 20-30% on input |
| German, Dutch | 30-50% extra | 25-40% on input |
| Japanese | ~190% extra | 50-65% on input |
| Chinese | ~30-90% extra (varies by tokenizer) | 15-50% on input |
| Arabic, Hindi, Thai | 200-400% extra | 50-75% on input |

If your product is multilingual, this is the single biggest free win on your bill.

## Modes

| Mode | What | Setup |
|---|---|---|
| **api** (only mode for v2.0) | HTTP to translation.tokenstree.com (free tier + paid) | `export TOKENTRANSLATION_API_KEY=tk_...` |
| **local** (roadmap v2.1) | Local NLLB or Helsinki-NLP models | not yet shipped |

Local mode is planned for v2.1 to mirror caveman's fully-offline philosophy. The translation models (NLLB-200) are ~1GB so the install footprint matters; we want to make it opt-in.

## Trigger

`/tokenstranslation` — also auto-suggested when:
- User's input is detected as non-English
- Caller passes `target_lang=` to override

## Preserved exactly

Code, URLs, file paths, technical English terms (function names, library names) stay in their original form even when surrounding prose is translated.

## Optional: Tokinensis encoding

`tokenstranslation` can apply Tokinensis v2 — a proprietary ultra-token-efficient encoding (synthetic morpheme language). Roughly 30-50% smaller than English on technical text. Trade-off: Claude has not seen Tokinensis in training, so for highest accuracy paths leave it off. For pure structural prompts (categorization, format conversion) it works fine.

## Config

```bash
export TOKENTRANSLATION_API_KEY="tk_..."          # free at translation.tokenstree.com
export TOKENTRANSLATION_USE_TOKINENSIS="false"    # opt-in experimental
```

## See also

- `/tokenstransfer` — input compression (compresses, not translates)
- `/caveman` — output compression
- `/caveman-fullstack` — all three at once
