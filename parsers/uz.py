"""
Площадки Узбекистана 🇺🇿.

OLX.uz включён по умолчанию (публичный поиск), остальные нишевые площадки —
выключены по умолчанию: у них нестабильная/неизвестная вёрстка, иногда нужна
авторизация. Включаются в .env (например SITE_DOWORK=1) после проверки
селекторов вверху классов.
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class OlxUzParser(ConfigurableHTMLParser):
    name = "olxuz"
    title = "OLX.uz"
    country = "uz"
    enabled_default = True

    BASE = "https://www.olx.uz"
    # Поиск по запросу «sayt» (сайт). Можно поменять запрос под себя.
    LIST_URL = "https://www.olx.uz/list/q-sayt/"
    CARD_SELECTOR = "div[data-cy='l-card'], div[data-testid='l-card']"
    TITLE_SELECTOR = "h6, [data-cy='ad-card-title'] a, a.css-rc5s2u"
    LINK_SELECTOR = "a"
    PRICE_SELECTOR = "p[data-testid='ad-price'], .price"
    DESC_SELECTOR = ""


class DoworkUzParser(ConfigurableHTMLParser):
    name = "dowork"
    title = "Dowork.uz"
    country = "uz"
    enabled_default = False

    BASE = "https://dowork.uz"
    LIST_URL = "https://dowork.uz/vacancies"
    CARD_SELECTOR = ".vacancy, .card, .job"
    TITLE_SELECTOR = "a, .title"
    PRICE_SELECTOR = ".salary, .price"
    DESC_SELECTOR = ".description, .text"


class UzitHubParser(ConfigurableHTMLParser):
    name = "uzithub"
    title = "UZITHUB.uz"
    country = "uz"
    enabled_default = False

    BASE = "https://uzithub.uz"
    LIST_URL = "https://uzithub.uz/vacancies"
    CARD_SELECTOR = ".vacancy, .card, article"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".salary, .price"
    DESC_SELECTOR = ".description, .text"


class GiglancerParser(ConfigurableHTMLParser):
    name = "giglancer"
    title = "Giglancer.uz"
    country = "uz"
    enabled_default = False

    BASE = "https://giglancer.uz"
    LIST_URL = "https://giglancer.uz/projects"
    CARD_SELECTOR = ".project, .card, .gig"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".price, .budget"
    DESC_SELECTOR = ".description, .text"


class WorklanceParser(ConfigurableHTMLParser):
    name = "worklance"
    title = "Worklance.uz"
    country = "uz"
    enabled_default = False

    BASE = "https://worklance.uz"
    LIST_URL = "https://worklance.uz/projects"
    CARD_SELECTOR = ".project, .card, article"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".price, .budget"
    DESC_SELECTOR = ".description, .text"


class EdcSaleParser(ConfigurableHTMLParser):
    name = "edcsale"
    title = "EDC.Sale"
    country = "uz"
    enabled_default = False

    BASE = "https://edc.sale"
    LIST_URL = "https://edc.sale/"
    CARD_SELECTOR = ".product, .card, .item"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".price"
    DESC_SELECTOR = ".description, .text"


class InfoShopUzParser(ConfigurableHTMLParser):
    name = "infoshop"
    title = "InfoShop.uz"
    country = "uz"
    enabled_default = False

    BASE = "https://infoshop.uz"
    LIST_URL = "https://infoshop.uz/"
    CARD_SELECTOR = ".product, .card, .item"
    TITLE_SELECTOR = "a, .title, h3 a"
    PRICE_SELECTOR = ".price"
    DESC_SELECTOR = ".description, .text"
