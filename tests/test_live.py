"""Live tests for trthaber_mcp — real requests to trthaber.com.

Requires network + Chrome TLS impersonation (curl-cffi). The server
is polite by design (~0.8s between requests), so this file takes
~30s. Run: python -m unittest discover -s tests -v

Headlines change during the day; tests assert structure and sane
ranges, not exact titles.
"""
import json
import unittest

from trthaber_mcp import http as H
from trthaber_mcp import news as N

ARTICLE_URL = (
    "https://www.trthaber.com/haber/bilim-teknoloji/"
    "guney-torid-goktasi-yagmuru-bu-gece-nadir-gorulen-ates-toplari-"
    "olusturacak-962288.html"
)


class TestLiveHeadlines(unittest.TestCase):
    def test_gundem(self):
        html_text = H.fetch_category_html("gundem")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 10)
        self.assertIn("trthaber.com/haber/gundem/", rows[0]["url"])

    def test_ekonomi(self):
        html_text = H.fetch_category_html("ekonomi")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 10)

    def test_spor(self):
        html_text = H.fetch_category_html("spor")
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 10)

    def test_unknown_category_404(self):
        with self.assertRaises(H.TrthaberError):
            H.fetch_category_html("xyzabcqwerty")


class TestLiveLatest(unittest.TestCase):
    def test_son_dakika(self):
        html_text = H.fetch_latest_html()
        rows = N.parse_listing(html_text)
        self.assertGreater(len(rows), 50)


class TestLiveArticle(unittest.TestCase):
    def test_meteor_shower(self):
        html_text = H.fetch_article_html(ARTICLE_URL)
        a = N.parse_article(html_text)
        self.assertEqual(
            a["title"],
            "Güney Torid göktaşı yağmuru bu gece nadir görülen ateş topları oluşturacak",
        )
        self.assertEqual(a["date_published"], "2026-11-05 07:06:00+03:00")
        self.assertGreater(a["paragraph_count"], 5)


class TestLiveServerTools(unittest.TestCase):
    """End-to-end: call the MCP tool functions and check JSON output."""

    def test_headlines_tool(self):
        from trthaber_mcp.server import trthaber_headlines

        out = json.loads(trthaber_headlines("gundem", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["category_name"], "Gündem")

    def test_latest_tool(self):
        from trthaber_mcp.server import trthaber_latest

        out = json.loads(trthaber_latest(limit=5))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 5)

    def test_article_tool(self):
        from trthaber_mcp.server import trthaber_get_article

        out = json.loads(trthaber_get_article(ARTICLE_URL))
        self.assertNotIn("error", out)
        self.assertIn("Torid", out["body"])

    def test_search_tool(self):
        from trthaber_mcp.server import trthaber_search_news

        out = json.loads(trthaber_search_news("COP31", limit=5))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)

    def test_categories_tool(self):
        from trthaber_mcp.server import trthaber_list_categories

        out = json.loads(trthaber_list_categories())
        self.assertEqual(len(out["categories"]), 18)

    def test_bad_category_error(self):
        from trthaber_mcp.server import trthaber_headlines

        out = json.loads(trthaber_headlines("nope"))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
