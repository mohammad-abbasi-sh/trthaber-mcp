"""Stdlib parsing for trthaber.com (TRT Haber) server-rendered news pages.

Verified live 2026-11-08 against real pages (fixtures in tests/):
- Homepage (268KB): 62 deduped article links. Article anchors look
  like <a href="https://www.trthaber.com/haber/<cat>/<slug>-<id>.html"
  title="HEADLINE" class="site-url">; the title attribute IS the
  headline. Inner text sometimes starts with a "HH:MM " time prefix,
  sometimes is empty (image anchors), sometimes is a summary line.
- Category pages (/haber/<cat>/, ~107KB): 15 deduped articles each.
  Each article appears up to 3 times: an image anchor (empty inner
  text), a title anchor (inner text = headline), and a summary anchor
  (inner text = first sentence of the spot). The title attribute is
  present on all three, so the parser prefers it and takes the
  summary from a differing inner text.
- Article page (~90KB): <h1> title, <h2 class="news-spot"> spot,
  meta description / og:image / og:url, "datePublished" in an inline
  JSON blob ("2026-11-05 07:06:00+03:00"), no author meta anywhere.
  Body = consecutive <p> elements inside <div class="news-detail-
  container">, ending at <div class="news-tags"> (9 paragraphs in
  the fixture). No NewsArticle JSON-LD (only an Organization block).
- Son-dakika page (/son-dakika-haberleri, 235KB): 120 deduped
  articles, newest first — same anchor shape as the homepage.
- Search: the site's own search is JS + CSRF-token POST gated
  (POST /ajax/getCsrfToken/search/ then GET /ajax/getSearchResults/);
  a tokenless GET of /arama.html?q=... returns a 200 page with an
  EMPTY results container (see fixture search-no-token.html). POSTs
  are not usable from this build environment, so keyword search here
  scans the homepage + son-dakika + category listings instead
  (same approach as sozcu-mcp, whose own search was dead too).
"""
from __future__ import annotations

import html
import re

CATEGORIES = {
    "gundem": "Gündem",
    "turkiye": "Türkiye",
    "dunya": "Dünya",
    "turk-dunyasi": "Türk Dünyası",
    "ekonomi": "Ekonomi",
    "spor": "Spor",
    "savunma": "Savunma",
    "cocuk": "Çocuk",
    "dunya-disi": "Dünya Dışı",
    "kultur-sanat": "Kültür-Sanat",
    "yasam": "Yaşam",
    "saglik": "Sağlık",
    "bilim-teknoloji": "Bilim Teknoloji",
    "egitim": "Eğitim",
    "cevre": "Çevre",
    "guncel": "Güncel",
    "trt-arsiv": "TRT Arşiv",
    "interaktif": "İnteraktif",
}

_TR_UPPER_TO_LOWER = str.maketrans({
    "İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ",
    "Ü": "ü", "Ö": "ö", "Ç": "ç",
})


def tr_lower(s: str) -> str:
    """Turkish-aware lowercase (str.lower() mangles İ -> i + dot)."""
    return s.translate(_TR_UPPER_TO_LOWER).lower()


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    # The site backslash-escapes apostrophes inside attribute values
    # (title="Emine Erdoğan\'dan ...") — undo that.
    text = text.replace("\\'", "'").replace('\\"', '"')
    return re.sub(r"\s+", " ", text).strip()


_TIME_PREFIX_RE = re.compile(r"^\d{2}:\d{2}\s+")


def _strip_time(text: str) -> tuple[str, str]:
    """Split a leading "HH:MM " publish-time prefix off a headline."""
    m = _TIME_PREFIX_RE.match(text)
    if m:
        return text[m.end():].strip(), text[:5]
    return text, ""


# ---------------------------------------------------------------- listings

_TITLE_ATTR_RE = re.compile(r'title="([^"]+)"')


def parse_listing(html_text: str) -> list[dict]:
    """Article links on a listing page -> [{url, title, summary?, time?}].

    The title attribute on the anchor is the headline (present on
    image, title and summary anchors alike). Inner text is used only
    as a fallback, and a differing inner text becomes the summary.
    """
    by_url: dict[str, dict] = {}
    for m in re.finditer(r"<a\b[^>]*>", html_text):
        tag = m.group(0)
        href_m = re.search(
            r'href="(https://www\.trthaber\.com/haber/[a-z-]+/'
            r'[a-z0-9-]+-\d+\.html)"',
            tag,
        )
        if not href_m:
            continue
        url = href_m.group(1)
        # inner text: up to the closing </a> after this tag
        end = html_text.find("</a>", m.end())
        inner = html_text[m.end():end] if end > 0 else ""
        inner_text = _clean(inner)
        inner_text, time_prefix = _strip_time(inner_text)
        title_m = _TITLE_ATTR_RE.search(tag)
        title = _clean(title_m.group(1)) if title_m else inner_text
        if not title:
            continue
        row = by_url.get(url)
        if row is None:
            row = {"url": url, "title": title}
            if time_prefix:
                row["time"] = time_prefix
            by_url[url] = row
        # A differing, sentence-like inner text is the summary.
        if (
            inner_text
            and inner_text != title
            and len(inner_text) > 20
            and "summary" not in row
        ):
            row["summary"] = inner_text[:400]
    return list(by_url.values())


# ---------------------------------------------------------------- article

def parse_article(html_text: str) -> dict:
    """Article page -> title, spot, dates, description, image, body."""
    out: dict = {}
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.S)
    if m:
        out["title"] = _clean(m.group(1))
    if not out.get("title"):
        m = re.search(r"<title>(.*?)</title>", html_text, re.S)
        if m:
            out["title"] = _clean(m.group(1)).split(" - Son Dakika")[0]

    m = re.search(
        r'<h2[^>]*class="news-spot"[^>]*>(.*?)</h2>', html_text, re.S
    )
    if m:
        out["spot"] = _clean(m.group(1))

    def _meta(name: str) -> str | None:
        mm = re.search(
            rf'<meta[^>]+(?:property|name)="{re.escape(name)}"[^>]+content="([^"]*)"',
            html_text,
        )
        return html.unescape(mm.group(1)) if mm else None

    out["description"] = _meta("description") or _meta("og:description") or ""
    out["image"] = _meta("og:image") or ""
    m = re.search(r'<meta property="og:url" content="([^"]+)"', html_text) or re.search(
        r'<link rel="canonical" href="([^"]+)"', html_text
    )
    if m:
        out["url"] = m.group(1)
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html_text)
    if m:
        out["date_published"] = m.group(1).strip()
    m = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html_text)
    if m:
        out["date_modified"] = m.group(1).strip()

    # Body: <p> run inside news-detail-container, up to news-tags.
    i = html_text.find("news-detail-container")
    if i < 0:
        raise ValueError("no article body found on this page")
    end = html_text.find('class="news-tags"', i)
    region = html_text[i:end if end > 0 else len(html_text)]
    paras = []
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", region, re.S):
        text = _clean(pm.group(1))
        if text:
            paras.append(text)
    if not paras:
        raise ValueError("no article body paragraphs found on this page")
    out["body"] = "\n\n".join(paras)
    out["paragraph_count"] = len(paras)
    return {k: v for k, v in out.items() if v not in (None, "")}
