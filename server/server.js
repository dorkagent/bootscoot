// BootScoot API - tiny zero-dependency REST wrapper around the search.
// node server/server.js   (PORT env, default 3000)
//
//   GET /                        demo page
//   GET /api/health              {"status":"ok"}
//   GET /api/search?q=Bailando&level=Beginner&wall=4&lang=&order=Date&max_results=20
//                                {"query","count","cached","results":[...]}
const http = require("http");
const { search } = require("../javascript/bootscoot");

const PORT = parseInt(process.env.PORT || "3000", 10);
const CACHE_TTL_MS = 5 * 60 * 1000; // don't re-hit the source site for repeat queries
const MAX_RESULTS_CAP = 100;
const cache = new Map();

const DEMO_PAGE = `<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BootScoot API</title>
<style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#222}
input,button{font-size:1rem;padding:.5rem}input{width:60%}button{cursor:pointer}
pre{background:#f4f4f4;padding:1rem;overflow:auto;font-size:.8rem}
.result{border-bottom:1px solid #ddd;padding:.6rem 0}
.result a{color:#1a56db}
.meta{color:#666;font-size:.85rem}
code{background:#f4f4f4;padding:.1rem .3rem}
</style></head><body>
<h1>🤠 BootScoot API</h1>
<p>Line-dance stepsheet search as JSON. Try it:</p>
<p><code>GET /api/search?q=Bailando&amp;max_results=5</code></p>
<form id="f"><input id="q" placeholder="dance name…" value="Bailando"><button>Search</button></form>
<div id="out"></div>
<script>
document.getElementById("f").onsubmit = async (e) => {
  e.preventDefault();
  const out = document.getElementById("out");
  out.innerHTML = "<p>searching…</p>";
  const r = await fetch("/api/search?q=" + encodeURIComponent(document.getElementById("q").value) + "&max_results=10");
  const d = await r.json();
  if (d.error) { out.innerHTML = "<p>error: " + d.error + "</p>"; return; }
  out.innerHTML = d.results.map(x =>
    '<div class="result"><a href="' + x.url + '" target="_blank">' + (x.title || "?") + "</a>" +
    '<div class="meta">' + [x.choreographer, x.date, x.count + "ct", x.walls + "w", x.level].filter(Boolean).join(" · ") + "</div>" +
    (x.music ? '<div class="meta">🎵 ' + x.music + "</div>" : "") + "</div>"
  ).join("") || "<p>no results</p>";
};
</script>
<p class="meta">Params: <code>q</code> (required), <code>level</code>, <code>wall</code>, <code>lang</code>, <code>order</code>, <code>max_results</code> (default 20, cap 100), <code>base_url</code>. Results cached 5 min.</p>
</body></html>`;

function json(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Content-Length": Buffer.byteLength(data),
  });
  res.end(data);
}

async function handleSearch(url) {
  const q = (url.searchParams.get("q") || "").trim();
  if (!q) return { status: 400, body: { error: "missing required parameter: q" } };

  let maxResults = parseInt(url.searchParams.get("max_results") || "20", 10);
  if (!Number.isFinite(maxResults) || maxResults < 1) maxResults = 20;
  maxResults = Math.min(maxResults, MAX_RESULTS_CAP);

  const opts = {
    maxResults,
    level: url.searchParams.get("level") || "",
    wall: url.searchParams.get("wall") || "",
    lang: url.searchParams.get("lang") || "",
    order: url.searchParams.get("order") || "",
    baseUrl: url.searchParams.get("base_url") || null,
  };
  const key = JSON.stringify({ q, ...opts });
  const hit = cache.get(key);
  if (hit && Date.now() - hit.t < CACHE_TTL_MS) {
    return { status: 200, body: { query: q, count: hit.results.length, cached: true, results: hit.results } };
  }
  const results = await search(q, opts);
  cache.set(key, { t: Date.now(), results });
  if (cache.size > 200) cache.delete(cache.keys().next().value); // keep memory bounded
  return { status: 200, body: { query: q, count: results.length, cached: false, results } };
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    if (req.method === "GET" && url.pathname === "/") {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(DEMO_PAGE);
    }
    if (req.method === "GET" && url.pathname === "/api/health") {
      return json(res, 200, { status: "ok" });
    }
    if (req.method === "GET" && url.pathname === "/api/search") {
      const { status, body } = await handleSearch(url);
      return json(res, status, body);
    }
    return json(res, 404, { error: "not found" });
  } catch (e) {
    return json(res, 502, { error: e.message });
  }
});

server.listen(PORT, () => console.log(`bootscoot-api on :${PORT}`));
