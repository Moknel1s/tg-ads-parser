"""
Площадки Узбекистана 🇺🇿. Все включены по умолчанию.

Реальное состояние доменов (проверено вживую 2026-07):
  ✅ bisyor.uz          — обычный HTML, карточки .product_item (парсится сразу)
  ✅ olx.uz             — работает (52 объявления в тесте)
  ⚙️ dowork.uz          — HTML, но на корне каталог услуг (предложения); best-effort
  ⚙️ uzithub.uz         — Next.js (SPA) → рендер через playwright
  ⚙️ giglancer.uz       — SPA-заглушка → playwright
  ⚙️ 2work.uz           — SPA с прелоадером → playwright
  ⚙️ salexy.uz          — HTML, но структура листинга нетривиальна; best-effort
  ⚙️ birbir.uz          — 403 (антибот) → playwright, лучше с прокси/UZ IP
  ❌ worklance.uz        — домен НЕ резолвится (сайт недоступен)
  ❌ uzfreelance.com     — домен-парковка (редирект на рекламу)
  ❌ edc.sale            — капча на входе
  ❌ infoshop.uz         — таймаут (недоступен из тестовой среды)
  ❌ freelance.admin.uz  — таймаут (недоступен из тестовой среды)

Сайты, помеченные ❌, оставлены подключёнными по вашему запросу, но реально
данные не отдадут, пока не станут доступны (бот при этом не падает — safe_fetch
ловит ошибку). Их можно выключить в .env: SITE_WORKLANCE=0 и т.п.
Все селекторы — в атрибутах классов, правьте при смене вёрстки.
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class OlxUzParser(ConfigurableHTMLParser):
    name = "olxuz"
    title = "OLX.uz"
    country = "uz"
    enabled_default = True
    require_want = True  # классифайд: берём только явные запросы

    BASE = "https://www.olx.uz"
    LIST_URL = "https://www.olx.uz/list/q-sayt/"
    CARD_SELECTOR = "div[data-cy='l-card'], div[data-testid='l-card']"
    TITLE_SELECTOR = "h6, [data-cy='ad-card-title'] a, a.css-rc5s2u"
    LINK_SELECTOR = "a"
    PRICE_SELECTOR = "p[data-testid='ad-price'], .price"


class BisyorParser(ConfigurableHTMLParser):
    # ✅ Проверено: карточка .product_item — это сам <a href> (заголовок + цена).
    name = "bisyor"
    title = "Bisyor.uz"
    country = "uz"
    enabled_default = True
    require_want = True  # классифайд

    BASE = "https://bisyor.uz"
    LIST_URL = "https://bisyor.uz/search?q=sayt"
    CARD_SELECTOR = "a.product_item"
    TITLE_SELECTOR = ".product_text_h4"
    PRICE_SELECTOR = ".price_product"
    DESC_SELECTOR = ""


class SalexyParser(ConfigurableHTMLParser):
    name = "salexy"
    title = "Salexy.uz"
    country = "uz"
    enabled_default = True
    require_want = True  # классифайд

    BASE = "https://salexy.uz"
    LIST_URL = "https://salexy.uz/?q=sayt"
    USE_DYNAMIC = True  # листинг подгружается скриптами
    CARD_SELECTOR = ".product-item, .product-list__item, article, .card"
    TITLE_SELECTOR = "a, h3, .title"
    PRICE_SELECTOR = ".price"


class DoworkUzParser(ConfigurableHTMLParser):
    name = "dowork"
    title = "Dowork.uz"
    country = "uz"
    enabled_default = True
    require_want = True  # каталог услуг = предложения

    BASE = "https://dowork.uz"
    LIST_URL = "https://dowork.uz/"
    CARD_SELECTOR = ".service-card, .vacancy, .card, article"
    TITLE_SELECTOR = "a, .title, h3"
    PRICE_SELECTOR = ".price, .svc-card-price, .salary"
    DESC_SELECTOR = ".description, .svc-card-desc"


class UzitHubParser(ConfigurableHTMLParser):
    name = "uzithub"
    title = "UZITHUB.uz"
    country = "uz"
    enabled_default = True

    BASE = "https://uzithub.uz"
    LIST_URL = "https://uzithub.uz/"
    USE_DYNAMIC = True  # Next.js (SPA)
    CARD_SELECTOR = ".vacancy, .card, article, [class*='vacancy']"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".salary, .price"
    DESC_SELECTOR = ".description, .text"


class GiglancerParser(ConfigurableHTMLParser):
    name = "giglancer"
    title = "Giglancer.uz"
    country = "uz"
    enabled_default = True

    BASE = "https://giglancer.uz"
    LIST_URL = "https://giglancer.uz/projects"
    USE_DYNAMIC = True  # SPA
    CARD_SELECTOR = ".project, .card, .gig, article"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".price, .budget"
    DESC_SELECTOR = ".description, .text"


class TwoWorkParser(ConfigurableHTMLParser):
    name = "2work"
    title = "2work.uz"
    country = "uz"
    enabled_default = True

    BASE = "https://2work.uz"
    LIST_URL = "https://2work.uz/"
    USE_DYNAMIC = True  # SPA с прелоадером
    CARD_SELECTOR = ".vacancy, .job, .card, article, [class*='vacancy']"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".salary, .price"
    DESC_SELECTOR = ".description, .text"


class BirBirParser(ConfigurableHTMLParser):
    name = "birbir"
    title = "BirBir.uz"
    country = "uz"
    enabled_default = True
    require_want = True  # классифайд

    BASE = "https://birbir.uz"
    LIST_URL = "https://birbir.uz/uz/search?query=sayt"
    USE_DYNAMIC = True  # антибот (403 на статике) — пробуем через браузер
    CARD_SELECTOR = "a[href*='/e/'], .product-item, .card, article"
    TITLE_SELECTOR = ".title, h3, .name"
    PRICE_SELECTOR = ".price"
