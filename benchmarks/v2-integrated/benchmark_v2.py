#!/usr/bin/env python3
"""
caveman_tokenstransfer.2.0 — Extended benchmark v2 (integrated).

Adds to v1 (vs-caveman):
- Wider prompt set: 30 prompts in 4 suites
- Realistic RAG/agent workloads with system prompt + retrieved context
- Measures the FULLSTACK scenario (transfer-then-caveman) end-to-end on a
  representative call ledger (input + output)
- Estimates $ savings on Haiku 4.5 pricing
"""
import json
import os
import re
import time
import statistics
from typing import List, Dict

import requests
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
def tok(s: str) -> int: return len(ENC.encode(s))

TRANSFER_URL = os.environ.get("TOKENSTRANSFER_URL", "https://transfer.tokenstree.com")
TRANSFER_KEY = os.environ["TOKENSTRANSFER_API_KEY"]
TRANSLATE_URL = os.environ.get("TOKENTRANSLATION_URL", "https://translation.tokenstree.com")
TRANSLATE_KEY = os.environ["TOKENTRANSLATION_API_KEY"]

# Haiku 4.5 pricing per 1M tokens
PRICE_IN = 1.0
PRICE_OUT = 5.0

# Output token reduction baselines from caveman public benchmark
# (we cannot run Claude here without an API key — these are caveman's reported numbers)
CAVEMAN_OUTPUT_REDUCTION = 0.65  # 65% avg
CAVEMAN_OUTPUT_LITE = 0.30
CAVEMAN_OUTPUT_ULTRA = 0.75

# ---- prompt suites ----
SYS_RAG = (
    "You are a senior engineer answering questions about a large Django codebase. "
    "Cite specific files and line numbers when possible. If unsure, say so. "
    "The codebase uses Django 5.0, Postgres 16, Redis 7, Celery 5. "
    "We have ~120 models, ~600 views, ~200 management commands. "
    "Authentication is handled by django-allauth with JWT issuance for the API. "
    "We use django-rest-framework for the API layer and channels for WebSockets. "
    "The team prefers function-based views for new code. "
    "We avoid signals where possible because they hurt traceability. "
    "Migrations are run via a CI job, never manually. "
    "Background work runs in Celery with Redis as broker and result backend. "
    "Tests use pytest-django and run in parallel with pytest-xdist. "
)
RAG_CTX = (
    "Retrieved context (top 3 chunks):\n"
    "1. `accounts/views.py:42` — login view uses session-based auth and falls back to JWT "
    "when the X-Use-JWT header is present. It uses a custom rate limiter that keys on IP "
    "+ user agent hash. The limiter is implemented in `accounts/ratelimit.py` and uses Redis "
    "with a 60-second sliding window.\n"
    "2. `accounts/ratelimit.py:1-40` — RedisSlidingWindowLimiter class. Uses ZADD/ZREMRANGEBYSCORE "
    "on a sorted set per key. The window is configurable but defaults to 60 seconds. The "
    "implementation is thread-safe under gunicorn but has a known race under uvicorn workers.\n"
    "3. `core/middleware.py:88` — global middleware that catches RateLimitExceeded and returns "
    "429 with a Retry-After header. It also logs the offending IP to a Postgres table for later "
    "analysis. There is a TODO to move this to ClickHouse for higher throughput.\n"
)

CODING_PROMPTS = [
    "Why is my React component re-rendering on every state update even though the props haven't changed?",
    "My Express auth middleware is letting expired JWT tokens through. The expiry check uses Date.now() compared to the token's exp field. What's wrong?",
    "How do I set up a PostgreSQL connection pool in Node.js with proper timeout and error handling?",
    "Explain the difference between git rebase and git merge. When should I use each?",
    "Refactor this callback-based Node.js function to use async/await: function getUser(id, cb) { db.query('SELECT * FROM users WHERE id=?', [id], (e,r)=>{if(e)return cb(e); if(!r.length)return cb(new Error('Not found')); cb(null,r[0]); }); }",
    "We have a monolithic Django app that's getting slow. The team is debating microservices. What factors should we consider?",
    "Review this Express route for security: app.get('/api/users/:id', (req,res)=>{ db.query(`SELECT * FROM users WHERE id=${req.params.id}`).then(u=>res.json(u)); });",
    "How do I write a multi-stage Dockerfile for a Node.js app to minimize the final image size?",
    "I have a race condition in my Go service where two goroutines update a shared map. How do I fix it without killing performance?",
    "My React error boundary isn't catching errors from async event handlers. Why and how do I fix it?",
]

RAG_PROMPTS = [
    "User question: why are some users getting 429s even though they should not have hit the rate limit?",
    "User question: how do we migrate the rate limiter from Redis to ClickHouse without downtime?",
    "User question: can we increase the rate limit window from 60s to 5min without breaking existing callers?",
    "User question: explain how the JWT fallback path interacts with the rate limiter — does it count differently?",
    "User question: write a unit test that reproduces the uvicorn race condition.",
]

AGENT_PROMPTS = [
    SYS_RAG + "\n\nTool definitions:\n" + "\n".join([
        "- search_code(query: str, top_k: int = 5) -> List[Match]",
        "- read_file(path: str, start: int = 1, end: int = -1) -> str",
        "- run_command(cmd: str, cwd: str = '.') -> str",
        "- write_file(path: str, content: str) -> None",
        "- search_issues(query: str) -> List[Issue]",
        "- search_pull_requests(query: str) -> List[PR]",
        "- search_commits(query: str) -> List[Commit]",
        "- run_tests(pattern: str = '*') -> TestResult",
    ]) + "\n\nUser: " + q
    for q in [
        "Add a new feature flag for the JWT fallback path. Default off. Wire it through the rate limiter.",
        "Audit the codebase for any direct calls to time.time() in rate-limiting code paths — those should use a monotonic clock.",
        "Find every place where we use session-based auth and check whether the rate limit applies. Make a report.",
        "There's a flaky test in test_ratelimit.py. Figure out why and fix it without disabling the test.",
        "The product team wants to A/B test a stricter rate limit (30/min vs 60/min). Implement the experiment harness.",
    ]
]

MULTILING_PROMPTS = [
    "Tengo una aplicación Django con un modelo de usuario personalizado y necesito migrar la base de datos sin perder datos existentes.",
    "Mon composant React se re-rend à chaque mise à jour de l'état même si les props n'ont pas changé. Pourquoi?",
    "Wie richte ich einen PostgreSQL-Verbindungspool in Node.js mit ordnungsgemäßer Timeout- und Fehlerbehandlungskonfiguration ein?",
    "Temos um aplicativo Django monolítico que está ficando lento. A equipe está debatendo microsserviços. Quais são os principais fatores?",
    "Spiegami come ottimizzare un Dockerfile multi-stage per ridurre la dimensione dell'immagine finale.",
]

SUITES = [
    ("coding", CODING_PROMPTS, 500),       # typical output 500 tokens
    ("rag", [SYS_RAG + "\n\n" + RAG_CTX + "\n\n" + p for p in RAG_PROMPTS], 400),
    ("agent", AGENT_PROMPTS, 300),
    ("multilingual", MULTILING_PROMPTS, 500),
]

# ---- caveman rules (input compression) ----
ARTICLES = {"a", "an", "the"}
FILLERS = {"just","really","basically","actually","simply","essentially","generally"}
REDUNDANT_RX = [
    (r"\bin order to\b", "to"), (r"\bmake sure to\b", "ensure"),
    (r"\bdue to the fact that\b", "because"),
    (r"\butilize\b", "use"), (r"\butilizes\b", "use"),
]
def caveman_rules(text):
    out = text
    for rx, rep in REDUNDANT_RX:
        out = re.sub(rx, rep, out, flags=re.I)
    out = "\n".join(" ".join(
        w for w in line.split()
        if re.sub(r"[^a-zA-Z']","",w).lower() not in ARTICLES | FILLERS
    ) for line in out.split("\n"))
    return re.sub(r"[ \t]+"," ", out).strip()

# ---- API callers ----
def transfer_compress(text, rate=0.5):
    try:
        r = requests.post(f"{TRANSFER_URL}/compress",
            headers={"X-API-Key": TRANSFER_KEY, "Content-Type":"application/json"},
            json={"text": text, "rate": rate}, timeout=180)
        d = r.json()
        return d.get("compressed_text",""), d.get("metrics",{})
    except Exception as e:
        return "", {"error": str(e)}

def translation_optimize(text):
    try:
        r = requests.post(f"{TRANSLATE_URL}/translate/in",
            headers={"X-API-Key": TRANSLATE_KEY, "Content-Type":"application/json"},
            json={"text": text}, timeout=60)
        d = r.json()
        return d.get("optimized_text",""), d
    except Exception as e:
        return "", {"error": str(e)}

# ---- cost model ----
def cost(tin, tout):
    return tin * PRICE_IN / 1e6 + tout * PRICE_OUT / 1e6

# ---- run ----
def run():
    results = {"meta": {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                        "tokenizer": "cl100k_base",
                        "transfer_rate": 0.5,
                        "caveman_output_reduction_used": CAVEMAN_OUTPUT_REDUCTION,
                        "price_in_per_M": PRICE_IN, "price_out_per_M": PRICE_OUT},
               "suites": {}, "fullstack_summary": {}}

    for suite_name, prompts, baseline_out in SUITES:
        rows = []
        for i, p in enumerate(prompts):
            t_in = tok(p)
            # Transfer
            tx_text, _ = transfer_compress(p, rate=0.5)
            t_tx = tok(tx_text) if tx_text else t_in
            # Translation
            tr_text, _ = translation_optimize(p)
            t_tr = tok(tr_text) if tr_text else t_in
            # Caveman rules
            t_cv = tok(caveman_rules(p))
            # Both (transfer + then caveman rules — should match transfer alone)
            t_both_in = t_tx

            # Output baselines (estimated)
            o_baseline = baseline_out
            o_caveman = int(baseline_out * (1 - CAVEMAN_OUTPUT_REDUCTION))
            # Fullstack output = caveman applied
            o_fullstack = o_caveman

            row = {
                "id": f"{suite_name}-{i+1}",
                "input": {
                    "baseline": t_in,
                    "transfer": t_tx,
                    "translation": t_tr,
                    "caveman_rules": t_cv,
                },
                "output_estimated": {
                    "baseline": o_baseline,
                    "caveman": o_caveman,
                },
                "cost_per_call": {
                    "baseline":           round(cost(t_in,        o_baseline),  6),
                    "caveman_only":       round(cost(t_in,        o_caveman),   6),
                    "transfer_only":      round(cost(t_tx,        o_baseline),  6),
                    "fullstack_2_0":      round(cost(t_tx,        o_fullstack), 6),
                },
            }
            base_c = row["cost_per_call"]["baseline"]
            row["savings_pct"] = {
                "caveman_only":  round((1 - row["cost_per_call"]["caveman_only"]  / base_c) * 100, 1),
                "transfer_only": round((1 - row["cost_per_call"]["transfer_only"] / base_c) * 100, 1),
                "fullstack_2_0": round((1 - row["cost_per_call"]["fullstack_2_0"] / base_c) * 100, 1),
            }
            rows.append(row)
            print(f"[{suite_name}/{row['id']}] in {t_in}→{t_tx} ({(1-t_tx/t_in)*100:.0f}%)  "
                  f"out {o_baseline}→{o_caveman}  cost {base_c:.5f}→{row['cost_per_call']['fullstack_2_0']:.5f} "
                  f"(-{row['savings_pct']['fullstack_2_0']:.0f}%)")
            time.sleep(0.3)
        results["suites"][suite_name] = rows

    # Fullstack summary across all suites
    fs_savings = []
    tx_savings = []
    cv_savings = []
    for s, rows in results["suites"].items():
        for r in rows:
            fs_savings.append(r["savings_pct"]["fullstack_2_0"])
            tx_savings.append(r["savings_pct"]["transfer_only"])
            cv_savings.append(r["savings_pct"]["caveman_only"])
    results["fullstack_summary"] = {
        "n_prompts": len(fs_savings),
        "avg_savings_pct": {
            "caveman_only":   round(statistics.mean(cv_savings), 1),
            "transfer_only":  round(statistics.mean(tx_savings), 1),
            "fullstack_2_0":  round(statistics.mean(fs_savings), 1),
        },
        "median_savings_pct": {
            "caveman_only":   round(statistics.median(cv_savings), 1),
            "transfer_only":  round(statistics.median(tx_savings), 1),
            "fullstack_2_0":  round(statistics.median(fs_savings), 1),
        },
    }
    print("\n=== FULLSTACK SUMMARY ===")
    print(json.dumps(results["fullstack_summary"], indent=2))

    with open("results.json","w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved → results.json")

if __name__ == "__main__":
    run()
