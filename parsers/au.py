"""
Площадки Австралии 🇦🇺.

Airtasker, SEEK, Indeed AU имеют антибот-защиту / требуют официальный API,
поэтому по умолчанию ВЫКЛЮЧЕНЫ. Включаются в .env после добавления
прокси/ключей и проверки селекторов.

(Глобальные Upwork/Fiverr/Freelancer.com зарегистрированы в us.py и покрывают
в том числе Австралию.)
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class AirtaskerParser(ConfigurableHTMLParser):
    name = "airtasker"
    title = "Airtasker"
    country = "au"
    enabled_default = False

    BASE = "https://www.airtasker.com"
    LIST_URL = "https://www.airtasker.com/tasks/?category=web-development"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-ui-name='taskCard'], .task-card, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = "[data-ui-name='taskPrice'], .price"
    DESC_SELECTOR = ".description"


class SeekParser(ConfigurableHTMLParser):
    name = "seek"
    title = "SEEK (контракты)"
    country = "au"
    enabled_default = False  # сильный антибот / нужен API

    BASE = "https://www.seek.com.au"
    LIST_URL = "https://www.seek.com.au/web-developer-jobs?worktype=244"  # 244 = contract
    USE_DYNAMIC = True
    CARD_SELECTOR = "article[data-card-type='JobCard'], [data-automation='normalJob']"
    TITLE_SELECTOR = "a[data-automation='jobTitle'], h3 a"
    PRICE_SELECTOR = "[data-automation='jobSalary'], .salary"
    DESC_SELECTOR = "[data-automation='jobShortDescription'], .description"


class IndeedAuParser(ConfigurableHTMLParser):
    name = "indeedau"
    title = "Indeed Australia"
    country = "au"
    enabled_default = False  # сильный антибот / нужен API

    BASE = "https://au.indeed.com"
    LIST_URL = "https://au.indeed.com/jobs?q=web+developer+contract&l=Australia"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job_seen_beacon, div.cardOutline"
    TITLE_SELECTOR = "h2.jobTitle a, a.jcs-JobTitle"
    PRICE_SELECTOR = ".salary-snippet-container, .estimated-salary"
    DESC_SELECTOR = ".job-snippet"
