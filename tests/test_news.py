"""Offline tests for trthaber_mcp.news — recorded real trthaber.com pages.

Fixtures are real pages fetched 2026-11-08 (plain curl, browser UA):
- homepage.html: / (63 deduped article links; first: Emine Erdoğan
  "8 Kasım Azerbaycan Günü" paylaşımı, time 14:40).
- category-gundem.html: /haber/gundem/ (15 articles; first: COP31
  Antalya story with a summary starting "Türkiye'nin ev
  sahipliğinde...").
- category-ekonomi.html: /haber/ekonomi/ (15 articles).
- article.html: Güney Torid meteor-shower story -962288 (9 body
  paragraphs, published 2026-11-05 07:06:00+03:00).
- latest.html: /son-dakika-haberleri (120 deduped articles).
- search-no-token.html: /arama.html?q=ekonomi (200 but the results
  container is EMPTY — the site's search needs a CSRF-token POST,
  so parse_listing must return [] here).
"""
import os
import unittest

from trthaber_mcp import news as N

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class TestListingParse(unittest.TestCase):
    def test_gundem(self):
        rows = N.parse_listing(_read("category-gundem.html"))
        self.assertEqual(len(rows), 15)
        first = rows[0]
        self.assertEqual(
            first["title"],
            "Dünya iklim gündemi için Antalya'da buluşuyor: COP31 yarın başlıyor",
        )
        self.assertTrue(first["url"].endswith("-962576.html"))

    def test_gundem_summary(self):
        rows = N.parse_listing(_read("category-gundem.html"))
        second = rows[1]
        self.assertEqual(
            second["title"],
            "Bakan Murat Kurum: COP31'de Antalya’dan tüm dünyaya ortak bir çağrı yapacağız",
        )
        self.assertIn("Sıfır Atık", second["summary"])

    def test_ekonomi(self):
        rows = N.parse_listing(_read("category-ekonomi.html"))
        self.assertEqual(len(rows), 15)
        self.assertEqual(
            rows[0]["title"],
            "Çevresel Etki Değerlendirmesi Yönetmeliği'nde değişikliğe gidildi",
        )
        self.assertIn("Resmi Gazete", rows[0]["summary"])

    def test_homepage(self):
        rows = N.parse_listing(_read("homepage.html"))
        self.assertEqual(len(rows), 63)
        self.assertEqual(
            rows[0]["title"],
            "Emine Erdoğan'dan \"8 Kasım Azerbaycan Günü\" paylaşımı",
        )
        self.assertEqual(rows[0]["time"], "14:40")

    def test_latest(self):
        rows = N.parse_listing(_read("latest.html"))
        self.assertEqual(len(rows), 120)
        self.assertEqual(
            rows[0]["title"],
            "Emine Erdoğan'dan \"8 Kasım Azerbaycan Günü\" paylaşımı",
        )

    def test_search_no_token_empty(self):
        # Tokenless search page carries no results (CSRF-token POST
        # gated) — the search tool scans listings instead.
        rows = N.parse_listing(_read("search-no-token.html"))
        self.assertEqual(rows, [])

    def test_all_have_url_title(self):
        for name in ("category-gundem.html", "category-ekonomi.html",
                     "homepage.html", "latest.html"):
            for r in N.parse_listing(_read(name)):
                self.assertTrue(r["url"].startswith("https://www.trthaber.com/haber/"))
                self.assertTrue(r["url"].endswith(".html"))
                self.assertTrue(r["title"])

    def test_categories(self):
        self.assertEqual(len(N.CATEGORIES), 18)
        self.assertEqual(N.CATEGORIES["gundem"], "Gündem")
        self.assertEqual(N.CATEGORIES["bilim-teknoloji"], "Bilim Teknoloji")
        self.assertEqual(N.CATEGORIES["spor"], "Spor")


class TestArticleParse(unittest.TestCase):
    def setUp(self):
        self.a = N.parse_article(_read("article.html"))

    def test_core(self):
        self.assertEqual(
            self.a["title"],
            "Güney Torid göktaşı yağmuru bu gece nadir görülen ateş topları oluşturacak",
        )
        self.assertEqual(self.a["date_published"], "2026-11-05 07:06:00+03:00")
        self.assertEqual(self.a["date_modified"], "2026-11-05 07:08:38+03:00")

    def test_spot(self):
        self.assertIn("en yoğun döneme", self.a["spot"])
        self.assertIn("ateş toplarını izleme", self.a["spot"])

    def test_body(self):
        self.assertEqual(self.a["paragraph_count"], 9)
        self.assertIn("104 bin 607 kilometre", self.a["body"])
        self.assertIn("Bill Cooke", self.a["body"])
        self.assertIn("2032 yılında", self.a["body"])

    def test_image_url(self):
        self.assertTrue(self.a["image"].startswith("https://trthaberstatic.cdn.wp.trt.com.tr/"))
        self.assertTrue(self.a["url"].endswith("-962288.html"))

    def test_no_body(self):
        with self.assertRaises(ValueError):
            N.parse_article("<html><body>no article here</body></html>")


class TestTrLower(unittest.TestCase):
    def test_turkish(self):
        self.assertEqual(N.tr_lower("İstanbul"), "istanbul")
        self.assertEqual(N.tr_lower("IĞDIR"), "ığdır")
        self.assertEqual(N.tr_lower("Şoför"), "şoför")


if __name__ == "__main__":
    unittest.main()
