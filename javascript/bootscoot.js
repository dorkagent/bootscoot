// BootScoot - line-dance stepsheet search. Zero dependencies, Node 18+.
// const { search } = require("./bootscoot");
// const results = await search("Bailando", { maxResults: 10 });

const DEFAULT_BASE_URL = "https://www.copperknob.co.uk";
const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36";

const stripTags = (s) =>
  (s || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();

function parseResults(html, baseUrl) {
  const results = [];
  const blockRe = /<div class="listitem"[^>]*>([\s\S]*?)<\/div>\s*<\/div>/g;
  let m;
  while ((m = blockRe.exec(html)) !== null) {
    const block = m[1];
    const hrefM = block.match(/<a href="([^"]+)"/);
    if (!hrefM) continue;
    const idM = hrefM[1].match(/\/stepsheets\/([A-Za-z0-9]+)\//);
    if (!idM) continue;

    const titleM = block.match(/<span class="listTitleColor1">([\s\S]*?)<\/span>/);
    const cdM = block.match(/<span class="listTitleColor2">([\s\S]*?)<\/span>/);
    let choreographer = null,
      date = null;
    if (cdM) {
      const parts = stripTags(cdM[1]).split(/\s+-\s+/);
      choreographer = parts[0] || null;
      date = parts[1] || null;
    }

    let count = null,
      walls = null,
      level = null,
      music = null;
    const infoM = block.match(/<p class="listIcons">([\s\S]*?)<\/p>/);
    if (infoM) {
      const info = stripTags(infoM[1]);
      const cM = info.match(/(\d+)\s*Count/i);
      if (cM) count = parseInt(cM[1], 10);
      const wM = info.match(/(\d+)\s*Wall/i);
      if (wM) walls = parseInt(wM[1], 10);
      const muM = info.match(/Music:\s*(.+)$/i);
      if (muM) {
        music = muM[1].trim() || null;
        level =
          info
            .slice(0, muM.index)
            .replace(/(\d+)\s*Count/gi, "")
            .replace(/(\d+)\s*Wall/gi, "")
            .replace(/^[\s-]+|[\s-]+$/g, "") || null;
      }
    }

    results.push({
      id: idM[1],
      title: stripTags(titleM ? titleM[1] : "") || null,
      url: new URL(hrefM[1], baseUrl).href,
      choreographer,
      date,
      count,
      walls,
      level,
      music,
    });
  }
  return results;
}

async function search(query, opts = {}) {
  const baseUrl = (opts.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const maxResults = opts.maxResults ?? 20;
  const delayMs = opts.delayMs ?? 1000;
  const q = {
    Order: opts.order || "Date",
    Lang: opts.lang || "",
    Level: opts.level || "",
    Wall: opts.wall || "",
    Search: query,
  };

  const results = [];
  let recnum = 0;
  for (;;) {
    const params = new URLSearchParams(q);
    if (recnum > 0) params.set("recnum", String(recnum));
    const url = `${baseUrl}/search?${params}`;
    const res = await fetch(url, {
      headers: { "User-Agent": USER_AGENT, Accept: "text/html" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
    const html = await res.text();
    const batch = parseResults(html, baseUrl);
    if (batch.length === 0) break;
    results.push(...batch);
    if (results.length >= maxResults) break;
    recnum += 20;
    await new Promise((r) => setTimeout(r, delayMs));
  }
  return results.slice(0, maxResults);
}

module.exports = { search, parseResults, DEFAULT_BASE_URL };
