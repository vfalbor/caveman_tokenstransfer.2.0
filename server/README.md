# caveman-tokenstransfer — self-hostable compression server

The LLMLingua-2 backend behind [transfer.tokenstree.com](https://transfer.tokenstree.com), stripped of auth/billing/DB. Run it locally or on your own infra. No vendor lock-in.

> caveman is 100% local. Now the transfer side can be 100% local too.

## Run with Docker (recommended)

```bash
cd server
docker compose up -d
# first start downloads the model (~1.5GB) and may take 2-5 min
```

Test:

```bash
curl -s http://localhost:8080/health | jq .
curl -s -X POST http://localhost:8080/compress \
  -H 'Content-Type: application/json' \
  -d '{"text": "This is a long input prompt with filler words.", "rate": 0.5}' | jq .
```

Then point the client at it:

```bash
export TOKENSTRANSFER_URL=http://localhost:8080
export TOKENSTRANSFER_API_KEY=anything   # accepted; no auth in self-host mode
```

## Run without Docker

```bash
cd server
pip install -r requirements.txt
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.1
uvicorn app:app --host 0.0.0.0 --port 8080
```

Python 3.10+, ~3 GB RAM, CPU-only by default. Set `LLMLINGUA_DEVICE=cuda` if you have an NVIDIA GPU (10-50× faster).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | model status, device |
| `POST` | `/compress` | compress prompt (params: `text`, `rate` or `target_token`) |
| `GET` | `/docs` | OpenAPI Swagger UI |

## Notes vs hosted

The hosted [transfer.tokenstree.com](https://transfer.tokenstree.com) adds:
- API key auth + usage limits (free tier)
- Persisted stats / logs per user
- Lower-latency warm model (preloaded across users)
- A "translate first" pipeline using [translation.tokenstree.com](https://translation.tokenstree.com)

For self-host, you get the LLMLingua-2 core. Wrap auth/limits/usage tracking around it however you like.

## License

MIT. Same as the rest of caveman_tokenstransfer.2.0.
