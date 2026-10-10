#!/usr/bin/env node
// Usage: bootscoot "Bailando" [--max-results 10] [--format json|text] [--level Beginner] [--base-url URL]
const { search } = require("../bootscoot");

function arg(flag, def = null) {
  const i = process.argv.indexOf(flag);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

(async () => {
  const query = process.argv[2];
  if (!query || query.startsWith("--")) {
    console.error('Usage: bootscoot "query" [--max-results N] [--format json|text] [--level X] [--wall N] [--base-url URL]');
    process.exit(1);
  }
  const format = arg("--format", "json");
  const results = await search(query, {
    maxResults: parseInt(arg("--max-results", "20"), 10),
    level: arg("--level", ""),
    wall: arg("--wall", ""),
    baseUrl: arg("--base-url", null),
  });
  if (format === "json") {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const r of results) {
      console.log(`${r.title} — ${r.choreographer || "?"} (${r.date || "?"}) [${r.count || "?"}ct ${r.walls || "?"}w ${r.level || ""}]`);
      console.log(`  ${r.url}`);
    }
  }
})().catch((e) => {
  console.error("error:", e.message);
  process.exit(2);
});
