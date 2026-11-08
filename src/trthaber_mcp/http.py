"""HTTP layer for trthaber_mcp.

trthaber.com (TRT Haber) serves its homepage, category pages
(/haber/<category>/), article pages
(/haber/<category>/<slug>-<id>.html) and the breaking-news page
(/son-dakika-haberleri) fully server-rendered — no login, no API
key, no session cookies needed. Plain HTTP 200 with a browser UA
(verified live 2026-11-08). The transport still uses curl-cffi
chrome120 impersonation, the same proven pattern as the other
Turkey-factory servers. Requests are kept gentle (one at a time,
~0.8s apart) and read-only. GET only — the site's own search is a
CSRF-token POST flow (POST /ajax/getCsrfToken/search/ then GET
/ajax/getSearchResults/) and POSTs are not usable from this build
environment, so search is implemented as a scan of the listings
(see server.py).
"""
from __future__ import annotations

import time
from urllib.parse import quote

from curl_cffi import requests as _r

BASE = "https://www.trthaber.com"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

_last_fetch = 0.0


class TrthaberError(RuntimeError):
    pass


def _get(url: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _r.get(url, impersonate="chrome120", headers=_HEADERS, timeout=TIMEOUT)
    except Exception as e:
        raise TrthaberError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise TrthaberError(
            "trthaber.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise TrthaberError(
            "trthaber.com rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code in (404, 410):
        raise TrthaberError(
            f"page not found (HTTP {resp.status_code}): {url} — check the "
            "category / article URL"
        )
    if resp.status_code != 200:
        raise TrthaberError(f"unexpected HTTP {resp.status_code} fetching {url}")
    return resp.text


def fetch_home_html() -> str:
    return _get(f"{BASE}/")


def fetch_category_html(category: str) -> str:
    """Category listing: /haber/<category>/ (gundem, ekonomi, ...)."""
    return _get(f"{BASE}/haber/{quote(category)}/")


def fetch_article_html(article_url: str) -> str:
    """Article page (full URL or path)."""
    if article_url.startswith("http"):
        url = article_url
    else:
        url = f"{BASE}/{article_url.lstrip('/')}"
    if "trthaber.com" not in url:
        raise TrthaberError(f"not a trthaber.com URL: {article_url}")
    return _get(url)


def fetch_latest_html() -> str:
    """Breaking-news page: /son-dakika-haberleri (newest first)."""
    return _get(f"{BASE}/son-dakika-haberleri")
