# trthaber-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/trthaber-mcp

Unofficial **read-only** MCP server for trthaber.com (TRT Haber), the Turkish public broadcaster's news site — headlines by category, breaking news (son dakika), full article text, keyword search over the current listings, and the category list.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with trthaber.com or TRT.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "trthaber": {
      "command": "uvx",
      "args": ["trthaber-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m trthaber_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `trthaber_headlines` | Top headlines in one category — `category`: "gundem" (default), "turkiye", "dunya", "turk-dunyasi", "ekonomi", "spor", "savunma", "cocuk", "dunya-disi", "kultur-sanat", "yasam", "saglik", "bilim-teknoloji", "egitim", "cevre", "guncel", "trt-arsiv", "interaktif"; `limit` 1..30 (category pages list 15) |
| `trthaber_latest` | Breaking news (son dakika), newest first — `limit` 1..30 (the page lists ~120 articles) |
| `trthaber_get_article` | Full text of one article — `article_url` (as returned by the headlines/latest/search tools); returns title, spot, publish/modify dates, description, image, full body |
| `trthaber_search_news` | Keyword search over current news — scans the homepage, the breaking-news page and all 18 category listings, matching titles and summaries; `limit` 1..30 |
| `trthaber_list_categories` | The 18 TRT Haber news categories (slug + Turkish display name), for use with `trthaber_headlines` |

Example output (`trthaber_get_article` / Güney Torid meteor-shower story, 5 Nov 2026):

```json
{"title": "Güney Torid göktaşı yağmuru bu gece nadir görülen ateş topları oluşturacak",
 "spot": "Güney Torid göktaşı yağmurunun en yoğun döneme ulaşmasıyla birlikte …",
 "date_published": "2026-11-05 07:06:00+03:00", "paragraph_count": 9,
 "image": "https://trthaberstatic.cdn.wp.trt.com.tr/resimler/2480000/necef-colu-meteor-yagmuru-aa-2481428.jpg"}
```

## How it works

trthaber.com serves its homepage, category pages (`/haber/<category>/`), article pages (`/haber/<category>/<slug>-<id>.html`) and the breaking-news page (`/son-dakika-haberleri`, ~120 articles, newest first) fully server-rendered — no login, no API key, no session cookies. Category pages carry 15 headline links each in the fixtures. Article pages carry the title in `<h1>`, the spot in `<h2 class="news-spot">`, publish/modify dates in an inline JSON blob, description and image in meta tags, and the full body as consecutive `<p>` elements inside `news-detail-container` (the run ends at the `news-tags` block). There is no author byline anywhere on the site, and no NewsArticle JSON-LD (only an Organization block). One site feature does NOT work server-side and is documented, not faked: the site's own search (`/arama.html`) is JS + CSRF-token POST gated (POST `/ajax/getCsrfToken/search/`), and a tokenless GET returns a 200 page with an empty results container — so `trthaber_search_news` scans the current listings instead. Transport uses Chrome TLS impersonation (`curl-cffi`, `chrome120`); requests are spaced ~0.8s apart; everything is read-only.

## Install

```bash
uvx trthaber-mcp==0.1.0        # run directly (needs uv)
# or
pip install trthaber-mcp==0.1.0
trthaber-mcp    # starts the MCP server on stdio
```

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Offline tests run on recorded fixtures (real pages fetched 2026-11-08); live tests hit trthaber.com. 26/26 green at build time (14 offline + 12 live) plus an MCP stdio smoke test.

## Roadmap

- "Çok okunanlar" (most read) if the site ever exposes it server-side
- Video/social-video listings (`/sosyal-videolar/`)
- Live TV schedule (`/canli-yayin-izle.html` is a stream page, not data)

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
