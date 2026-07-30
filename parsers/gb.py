"""
Площадки Великобритании 🇬🇧.

PeoplePerHour, Bark, YunoJuno обычно требуют вход/аккаунт, Gumtree имеет
антибот-защиту — поэтому по умолчанию ВЫКЛЮЧЕНЫ. Включаются в .env после
добавления прокси/ключей и проверки селекторов.

(Глобальные Upwork/Fiverr/Freelancer.com зарегистрированы один раз в us.py и
покрывают в том числе Великобританию.)
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class PeoplePerHourParser(ConfigurableHTMLParser):
    name = "peopleperhour"
    title = "PeoplePerHour"
    country = "gb"
    enabled_default = False

    BASE = "https://www.peopleperhour.com"
    LIST_URL = "https://www.peopleperhour.com/freelance-jobs/technology-programming"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job, li[data-testid='job-card'], .card"
    TITLE_SELECTOR = "a.title, h4 a, a[href*='/freelance-jobs/']"
    PRICE_SELECTOR = ".price, .budget"
    DESC_SELECTOR = ".description, .job-description"


class BarkParser(ConfigurableHTMLParser):
    name = "bark"
    title = "Bark"
    country = "gb"
    enabled_default = False  # лиды требуют аккаунт-профи

    BASE = "https://www.bark.com"
    LIST_URL = "https://www.bark.com/en/gb/website-development/"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".request, .lead, .card"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".price"
    DESC_SELECTOR = ".description"


class GumtreeUkParser(ConfigurableHTMLParser):
    name = "gumtreeuk"
    title = "Gumtree UK"
    country = "gb"
    enabled_default = False  # антибот

    BASE = "https://www.gumtree.com"
    LIST_URL = "https://www.gumtree.com/search?search_category=web-design-services&q=website"
    USE_DYNAMIC = True
    CARD_SELECTOR = "article[data-q='search-result'], .listing-link"
    TITLE_SELECTOR = "a, h2"
    PRICE_SELECTOR = ".listing-price, .price"
    DESC_SELECTOR = ".listing-description, .description"


class YunoJunoParser(ConfigurableHTMLParser):
    name = "yunojuno"
    title = "YunoJuno"
    country = "gb"
    enabled_default = False  # требует вход

    BASE = "https://www.yunojuno.com"
    LIST_URL = "https://www.yunojuno.com/freelancers/jobs"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job, .card, [data-job]"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".rate, .price"
    DESC_SELECTOR = ".description"
