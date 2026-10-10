// node --test test.js
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { parseResults, looksChallenged } = require("./bootscoot");

const FIXTURE = `
<html><body>
<div class="listitem">
  <div class="listTitle">
    <a href="https://example.com/stepsheets/AAA111/cowboys-mix">
    <span class="listTitleColor1"><mark>Cowboy</mark>s Mix</span></a>
    <span class="listTitleColor2">Unknown</span>
  </div>
  <div class="listInfo">
    <p class="listIcons">40&nbsp;Count&nbsp;&nbsp;&nbsp; -&nbsp;Wall&nbsp;&nbsp;&nbsp; Partenaire&nbsp;&nbsp;&nbsp;Music: Caf&#233; Ol&#233; - &Eacute;toile</p>
  </div>
</div>
<div class="listitem">
  <div class="listTitle">
    <a href="https://example.com/stepsheets/BBB222/dance-two">
    <span class="listTitleColor1">Dance Two</span></a>
    <span class="listTitleColor2">John Doe (UK) - September 2026</span>
  </div>
  <div class="listInfo">
    <p class="listIcons">64&nbsp;Count&nbsp;&nbsp;&nbsp; 2&nbsp;Wall&nbsp;&nbsp;&nbsp; Improver&nbsp;&nbsp;&nbsp;Music: Song Two - Artist</p>
  </div>
</div>
</body></html>`;

test("parses fields, keeps mid-word mark joined", () => {
  const [r1, r2] = parseResults(FIXTURE, "https://example.com");
  assert.equal(r1.id, "AAA111");
  assert.equal(r1.title, "Cowboys Mix");
  assert.equal(r1.url, "https://example.com/stepsheets/AAA111/cowboys-mix");
  assert.equal(r2.title, "Dance Two");
  assert.equal(r2.choreographer, "John Doe (UK)");
  assert.equal(r2.date, "September 2026");
});

test("dateless choreographer kept; -Wall leaves walls null without leaking into level", () => {
  const [r1] = parseResults(FIXTURE, "https://example.com");
  assert.equal(r1.choreographer, "Unknown");
  assert.equal(r1.date, null);
  assert.equal(r1.count, 40);
  assert.equal(r1.walls, null);
  assert.equal(r1.level, "Partenaire");
});

test("decodes numeric and named entities", () => {
  const [r1] = parseResults(FIXTURE, "https://example.com");
  assert.equal(r1.music, "Café Olé - Étoile");
});

test("detects challenge pages", () => {
  assert.equal(
    looksChallenged("<html><title>Just a moment...</title>challenges.cloudflare.com</html>"),
    true
  );
  assert.equal(looksChallenged(FIXTURE), false);
});
