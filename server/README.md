# BootScoot API

Zero-dependency Node REST server wrapping the JavaScript search.
A demo page lives at `/`; JSON endpoints below.

```bash
node server/server.js          # PORT env, default 3000
```

## Endpoints

- `GET /api/health` → `{"status":"ok"}`
- `GET /api/search?q=Bailando&max_results=5` →
  `{"query","count","cached","results":[{id,title,url,choreographer,date,count,walls,level,music}]}`

Params: `q` (required), `level`, `wall`, `lang`, `order`,
`max_results` (default 20, cap 100), `base_url`. Results are cached
5 minutes so repeat queries don't re-hit the source site. CORS is
open (`Access-Control-Allow-Origin: *`).

## Deploy

Dockerfile is included (`server/Dockerfile`), plus a Render
blueprint (`render.yaml` at the repo root, free plan). It also runs
fine on any Node host, or as a Cloudflare Worker with a thin adapter.
