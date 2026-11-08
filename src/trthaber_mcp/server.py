"""MCP server: unofficial read-only access to trthaber.com (TRT Haber)."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import news as _N

mcp = FastMCP("trthaber-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for trthaber.com (TRT Haber), the
Turkish public broadcaster's news site — headlines by category,
breaking news (son dakika), full article text, keyword search over
the current listings, and the category list. Data comes from the
site's server-rendered pages — no login, no API key. Category pages
(/haber/<category>/: gundem, turkiye, dunya, turk-dunyasi, ekonomi,
spor, savunma, cocuk, dunya-disi, kultur-sanat, yasam, saglik,
bilim-teknoloji, egitim, cevre, guncel, trt-arsiv, interaktif) list
15 headlines each. The breaking-news page (/son-dakika-haberleri)
lists ~120 articles, newest first. Article pages carry the title,
spot (h2.news-spot), publish date, description, image and the full
body text; there is no author byline on the site. The site's own
search is JS + CSRF-token POST gated (POST /ajax/getCsrfToken/
search/), so keyword search here scans the homepage, the
breaking-news page and the category listings instead, matching the
keyword in titles and summaries. Read-only; transport uses Chrome
TLS impersonation; requests are spaced ~0.8s apart. Built by
Mohammad Abbasi (mohammad-abbasi-sh) — Turkey MCP factory.\
"""


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)}, ensure_ascii=False)


def _validate_limit(limit: int, lo: int = 1, hi: int = 30) -> int:
    if not lo <= limit <= hi:
        raise ValueError(f"limit must be between {lo} and {hi}")
    return limit


@mcp.tool()
def trthaber_headlines(category: str = "gundem", limit: int = 10) -> str:
    """Top headlines in one TRT Haber category. category: "gundem"
    (default), "turkiye", "dunya", "turk-dunyasi", "ekonomi", "spor",
    "savunma", "cocuk", "dunya-disi", "kultur-sanat", "yasam",
    "saglik", "bilim-teknoloji", "egitim", "cevre", "guncel",
    "trt-arsiv", "interaktif". limit 1..30 (category pages list 15).
    Returns headlines (title, article URL, summary when the listing
    carries one, publish time when shown)."""
    try:
        category = (category or "gundem").strip().lower()
        if category not in _N.CATEGORIES:
            raise ValueError(
                f"category must be one of {', '.join(_N.CATEGORIES)}"
            )
        _validate_limit(limit)
        html_text = _http.fetch_category_html(category)
        rows = _N.parse_listing(html_text)
    except (ValueError, _http.TrthaberError) as e:
        return _err(e)
    return json.dumps(
        {
            "category": category,
            "category_name": _N.CATEGORIES[category],
            "count": min(limit, len(rows)),
            "headlines": rows[:limit],
        },
        ensure_ascii=False,
    )


@mcp.tool()
def trthaber_latest(limit: int = 10) -> str:
    """Breaking news (son dakika) from TRT Haber, newest first.
    limit 1..30 (the page lists ~120 articles). Returns articles
    (title, article URL, summary when present, publish time when
    shown)."""
    try:
        _validate_limit(limit)
        html_text = _http.fetch_latest_html()
        rows = _N.parse_listing(html_text)
    except (ValueError, _http.TrthaberError) as e:
        return _err(e)
    return json.dumps(
        {"count": min(limit, len(rows)), "articles": rows[:limit]},
        ensure_ascii=False,
    )


@mcp.tool()
def trthaber_get_article(article_url: str) -> str:
    """Full text of one TRT Haber article. article_url: the article's
    trthaber.com URL (as returned by the headlines/latest/search
    tools, e.g. "https://www.trthaber.com/haber/bilim-teknoloji/
    guney-torid-goktasi-yagmuru-bu-gece-nadir-gorulen-ates-toplari-
    olusturacak-962288.html"). Returns title, spot, publish date,
    description, image and the full body text."""
    try:
        if not article_url or not article_url.strip():
            raise ValueError("article_url must not be empty")
        html_text = _http.fetch_article_html(article_url.strip())
        data = _N.parse_article(html_text)
    except (ValueError, _http.TrthaberError) as e:
        return _err(e)
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def trthaber_search_news(query: str, limit: int = 10) -> str:
    """Keyword search over current TRT Haber news: scans the
    homepage, the breaking-news page and all 18 category listings,
    matching the keyword in titles and summaries. query: e.g.
    "ekonomi", "deprem", "COP31". limit 1..30. Note: the site's own
    /arama search is CSRF-token POST gated, so this searches the
    current listings instead of a search backend."""
    try:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        _validate_limit(limit)
        q = _N.tr_lower(query.strip())
        rows: list[dict] = []
        seen: set[str] = set()

        def _scan(html_text: str) -> None:
            for r in _N.parse_listing(html_text):
                if r["url"] in seen:
                    continue
                seen.add(r["url"])
                hay = _N.tr_lower(f"{r.get('title', '')} {r.get('summary', '')}")
                if q in hay:
                    rows.append(r)

        _scan(_http.fetch_home_html())
        if len(rows) < limit:
            _scan(_http.fetch_latest_html())
        for category in _N.CATEGORIES:
            if len(rows) >= limit:
                break
            _scan(_http.fetch_category_html(category))
    except (ValueError, _http.TrthaberError) as e:
        return _err(e)
    return json.dumps(
        {"query": query.strip(),
         "count": min(limit, len(rows)), "articles": rows[:limit]},
        ensure_ascii=False,
    )


@mcp.tool()
def trthaber_list_categories() -> str:
    """The 18 TRT Haber news categories (slug + Turkish display
    name), for use with trthaber_headlines. No arguments."""
    return json.dumps(
        {
            "categories": [
                {"slug": slug, "name": name}
                for slug, name in _N.CATEGORIES.items()
            ]
        },
        ensure_ascii=False,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
