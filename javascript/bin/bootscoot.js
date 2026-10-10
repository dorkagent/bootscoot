#!/usr/bin/env node
// Usage: bootscoot "Bailando" [--max-results 10] [--format json|text] [--level Beginner] [--base-url URL]
const { search } = require("../bootscoot");

function arg(flag, def = null) {
  const i = process.argv.indexOf(flag);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  return v !== undefined && !v.startsWith("--") ? v : def; // never swallow the next flag
}

(async () => {
  const query = process.argv[2];
  if (!query || query.startsWith("--")) {
    console.error(
      'Usage: bootscoot "query" [--max-results N] [--format json|text] [--level X] [--wall N] [--lang X] [--order X] [--base-url URL]'
    );
    process.exit(1);
  }
  const format = arg("--format", "json");
  if (format !== "json" && format !== "text") {
    console.error(`error: unknown --format "${format}" (expected json|text)`);
    process.exit(1);
  }
  let maxResults = parseInt(arg("--max-results", "20"), 10);
  if (!Number.isFinite(maxResults) || maxResults < 1) maxResults = 20;
  const results = await search(query, {
    maxResults,
    level: arg("--level", ""),
    wall: arg("--wall", ""),
    lang: arg("--lang", ""),
    order: arg("--order", ""),
    baseUrl: arg("--base-url", null),
  });
  if (format === "json") {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const r of results) {
      console.log(
        `${r.title} — ${r.choreographer || "?"} (${r.date || "?"}) [${r.count || "?"}ct ${r.walls || "?"}w ${r.level || ""}]`
      );
      console.log(`  ${r.url}`);
    }
  }
})().catch((e) => {
  console.error("error:", e.message);
  process.exit(2);
});
