# BootScoot (JavaScript)

Zero dependencies, Node 18+. One async function returning an array of
result objects for your script to take over.

```javascript
const { search } = require("./bootscoot");

const results = await search("Bailando", { maxResults: 10 });
// [{ id, title, url, choreographer, date, count, walls, level, music }, ...]
```

Options: `baseUrl` (target site), `maxResults` (default 20, follows
pagination), `maxPages` (default 10, safety cap), `level`, `wall`,
`lang`, `order`, `delayMs`.

Note: `level` comes back in the site's own language (e.g. `Débutant` on
French sheets).

CLI:

```bash
node bin/bootscoot.js "Bailando" --max-results 10 --format json
node bin/bootscoot.js "Bailando" --format text --level Beginner --base-url https://...
```
