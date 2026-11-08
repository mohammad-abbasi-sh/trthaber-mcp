# trthaber-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/trthaber-mcp

trthaber.com (TRT Haber — Türkiye'nin kamu yayıncısı) için resmi olmayan **salt okunur** MCP sunucusu — kategoriye göre manşetler, son dakika haberleri, haberin tam metni, güncel listelerde anahtar kelime araması ve kategori listesi.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. trthaber.com veya TRT ile bağlantısı yoktur.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza ekleyin (stdio):

```json
{
  "mcpServers": {
    "trthaber": {
      "command": "uvx",
      "args": ["trthaber-mcp"]
    }
  }
}
```

Veya yerelde çalıştırın: `python -m trthaber_mcp.server` (`mcp<2`, `curl-cffi` gerekir).

## Araçlar

| Araç | Açıklama |
|------|-------------|
| `trthaber_headlines` | Bir kategorideki manşetler — `category`: "gundem" (varsayılan), "turkiye", "dunya", "turk-dunyasi", "ekonomi", "spor", "savunma", "cocuk", "dunya-disi", "kultur-sanat", "yasam", "saglik", "bilim-teknoloji", "egitim", "cevre", "guncel", "trt-arsiv", "interaktif"; `limit` 1..30 (kategori sayfaları 15 haber listeler) |
| `trthaber_latest` | Son dakika haberleri, yeniden eskiye — `limit` 1..30 (sayfa ~120 haber listeler) |
| `trthaber_get_article` | Bir haberin tam metni — `article_url` (headlines/latest/search araçlarının döndürdüğü URL); başlık, spot, yayın/değişiklik tarihleri, açıklama, görsel, tam metin |
| `trthaber_search_news` | Güncel haberlerde anahtar kelime araması — ana sayfayı, son dakika sayfasını ve 18 kategori listesini tarar; `limit` 1..30 |
| `trthaber_list_categories` | 18 TRT Haber kategorisi (slug + Türkçe ad), `trthaber_headlines` için |

## Nasıl çalışır

trthaber.com ana sayfasını, kategori sayfalarını (`/haber/<kategori>/`), haber sayfalarını (`/haber/<kategori>/<slug>-<id>.html`) ve son dakika sayfasını (`/son-dakika-haberleri`, ~120 haber, yeniden eskiye) tamamen sunucu taraflı gösterir — giriş, API anahtarı ve çerez gerekmez. Kategori sayfalarında 15 manşet bağlantısı vardır. Haber sayfalarında başlık `<h1>` içinde, spot `<h2 class="news-spot">` içinde, yayın/değişiklik tarihleri satır içi bir JSON bloğunda, açıklama ve görsel meta etiketlerdedir; tam metin `news-detail-container` içindeki ardışık `<p>` öğeleridir (metin `news-tags` bloğunda biter). Sitede hiç yazar imzası yoktur ve NewsArticle JSON-LD de yoktur (yalnızca Organization bloğu). Sitenin bir özelliği sunucu tarafında çalışmaz ve uydurulmaz, belgelenir: sitenin kendi araması (`/arama.html`) JS + CSRF-token POST gerektirir (POST `/ajax/getCsrfToken/search/`), jetonsuz GET boş sonuç içeren bir 200 sayfası döndürür — bu yüzden `trthaber_search_news` güncel listeleri tarar. Aktarım Chrome TLS taklidi kullanır (`curl-cffi`, `chrome120`); istekler ~0,8 sn arayla; her şey salt okunurdur.

## Kurulum

```bash
uvx trthaber-mcp        # doğrudan çalıştır (uv gerekir)
# veya
pip install trthaber-mcp
trthaber-mcp    # MCP sunucusunu stdio üzerinde başlatır
```

## Testler

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Çevrimdışı testler kaydedilmiş gerçek sayfalarla çalışır (2026-11-08'de çekildi); canlı testler trthaber.com'a bağlanır. 26/26 yeşil (14 çevrimdışı + 12 canlı) + MCP stdio duman testi.

## Yol haritası

- "Çok okunanlar" (site sunucu tarafında sunarsa)
- Video listeleri (`/sosyal-videolar/`)
- Canlı TV akış sayfası (`/canli-yayin-izle.html` veri değil, akış sayfasıdır)

## Lisans

MIT — bkz. [LICENSE](LICENSE).
