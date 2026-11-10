# trthaber-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/trthaber-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای trthaber.com (تی‌آرتی خبر — خبرگزاری رادیو و تلویزیون دولتی ترکیه) — تیترها بر اساس دسته‌بندی، اخبار فوری (سون داکیکا)، متن کامل خبر، جستجوی کلیدواژه در فهرست‌های جاری و فهرست دسته‌بندی‌ها.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP ترکیه» (خط لوله به سبک سپهر). وابسته به trthaber.com یا TRT نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP خود اضافه کنید (stdio):

```json
{
  "mcpServers": {
    "trthaber": {
      "command": "uvx",
      "args": ["trthaber-mcp==0.1.1"]
    }
  }
}
```

یا به‌صورت محلی اجرا کنید: `python -m trthaber_mcp.server` (نیازمند `mcp<2` و `curl-cffi`).

## ابزارها

| ابزار | توضیح |
|------|--------|
| `trthaber_headlines` | تیترهای برتر یک دسته — `category`: ‏«gundem» (پیش‌فرض)، ‏«turkiye»، ‏«dunya»، ‏«turk-dunyasi»، ‏«ekonomi»، ‏«spor»، ‏«savunma»، ‏«cocuk»، ‏«dunya-disi»، ‏«kultur-sanat»، ‏«yasam»، ‏«saglik»، ‏«bilim-teknoloji»، ‏«egitim»، ‏«cevre»، ‏«guncel»، ‏«trt-arsiv»، ‏«interaktif»؛ ‏`limit` ‏۱ تا ۳۰ (هر صفحهٔ دسته ۱۵ خبر دارد) |
| `trthaber_latest` | اخبار فوری (سون داکیکا)، از جدید به قدیم — `limit` ‏۱ تا ۳۰ (صفحه ~۱۲۰ خبر دارد) |
| `trthaber_get_article` | متن کامل یک خبر — `article_url` (نشانی‌ای که ابزارهای headlines/latest/search برمی‌گردانند)؛ تیتر، خلاصهٔ خبر (spot)، تاریخ انتشار/ویرایش، توضیح، تصویر و متن کامل |
| `trthaber_search_news` | جستجوی کلیدواژه در اخبار جاری — صفحهٔ اصلی، صفحهٔ اخبار فوری و فهرست هر ۱۸ دسته را می‌خواند و در تیتر و خلاصه جستجو می‌کند؛ `limit` ‏۱ تا ۳۰ |
| `trthaber_list_categories` | ۱۸ دستهٔ خبری تی‌آرتی خبر (slug + نام ترکی)، برای استفاده با `trthaber_headlines` |

## چگونه کار می‌کند

trthaber.com صفحهٔ اصلی، صفحات دسته‌بندی (`/haber/<category>/`)، صفحات خبر (`/haber/<category>/<slug>-<id>.html`) و صفحهٔ اخبار فوری (`/son-dakika-haberleri`، ~۱۲۰ خبر، از جدید به قدیم) را کاملاً سمت سرور رندر می‌کند — بدون ورود، کلید API و کوکی. هر صفحهٔ دسته در فیکسچرها ۱۵ پیوند خبر دارد. در صفحهٔ خبر، تیتر در `<h1>`، خلاصه در `<h2 class="news-spot">`، تاریخ انتشار/ویرایش در یک بلوک JSON درون‌خطی، توضیح و تصویر در متا تگ‌ها و متن کامل در `<p>`های متوالی داخل `news-detail-container` است (متن در بلوک `news-tags` تمام می‌شود). سایت هیچ نام نویسنده‌ای ندارد و JSON-LD از نوع NewsArticle هم ندارد (فقط بلوک Organization). یک قابلیت سایت سمت سرور کار نمی‌کند و جعل نمی‌شود، بلکه مستند شده است: جستجوی خود سایت (`/arama.html`) به جاوااسکریپت + توکن CSRF با POST نیاز دارد (POST به `/ajax/getCsrfToken/search/`) و GET بدون توکن صفحهٔ ۲۰۰ با ظرف نتایج خالی برمی‌گرداند — بنابراین `trthaber_search_news` فهرست‌های جاری را می‌خواند. انتقال با جعل TLS کروم است (`curl-cffi`، ‏`chrome120`)؛ درخواست‌ها با فاصلهٔ ~۰٫۸ ثانیه؛ همه‌چیز فقط‌خواندنی است.

## نصب

```bash
uvx trthaber-mcp==0.1.1        # اجرای مستقیم (نیازمند uv)
# یا
pip install trthaber-mcp==0.1.1
trthaber-mcp    # سرور MCP را روی stdio راه می‌اندازد
```

## تست‌ها

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

تست‌های آفلاین روی صفحات واقعیِ ضبط‌شده اجرا می‌شوند (دریافت‌شده در ۲۰۲۶-۱۱-۰۸)؛ تست‌های زنده به trthaber.com وصل می‌شوند. ۲۶/۲۶ سبز (۱۴ آفلاین + ۱۲ زنده) + تست دود MCP روی stdio.

## نقشهٔ راه

- «پربازدیدترین‌ها»، اگر سایت آن را سمت سرور ارائه دهد
- فهرست ویدیوها (`/sosyal-videolar/`)
- صفحهٔ پخش زنده (`/canli-yayin-izle.html` صفحهٔ استریم است، نه داده)

## مجوز

MIT — ببینید [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
