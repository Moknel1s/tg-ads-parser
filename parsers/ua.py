"""
Площадки Украины 🇺🇦.

Фриланс-биржи (заказы клиентов): FreelanceHunt, Freelance.ua, Kabanchik.
Классифайд услуг: Prom.ua (require_want). Доски вакансий: Work.ua, DOU —
добавлены выключенными, фильтр найма оставит только проектную/контрактную работу.

Weblancer.net (укр./рос.) зарегистрирован в ru_extra.py.
Селекторы — в атрибутах классов, правьте при смене вёрстки.
"""
from __future__ import annotations

from urllib.parse import urljoin

from .base import Ad, BaseParser, ConfigurableHTMLParser


class FreelanceHuntParser(BaseParser):
    """FreelanceHunt — главная украинская фриланс-биржа. Проекты /project/<slug>."""

    name = "freelancehunt"
    title = "FreelanceHunt"
    country = "ua"
    enabled_default = True

    BASE = "https://freelancehunt.com"
    LIST_URL = "https://freelancehunt.com/projects"

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        html = await self._get_html(self.LIST_URL)
        soup = self.soup(html)
        ads: list[Ad] = []
        seen: set[str] = set()
        for a in soup.select("a[href*='/project/']"):
            title = a.get_text(" ", strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5 or not href:
                continue
            url = urljoin(self.BASE, href)
            if url in seen:
                continue
            seen.add(url)
            ads.append(Ad(title=title, url=url, source=self.name, country=self.country))
        return ads


class FreelanceUaParser(ConfigurableHTMLParser):
    name = "freelanceua"
    title = "Freelance.ua"
    country = "ua"
    enabled_default = True

    BASE = "https://freelance.ua"
    LIST_URL = "https://freelance.ua/"
    USE_DYNAMIC = True  # лендинг/SPA — рендерим, селекторы правьте при необходимости
    CARD_SELECTOR = ".project, .b-project, li.project, article, .card"
    TITLE_SELECTOR = "a[href*='/project'], h2 a, a.title, a"
    PRICE_SELECTOR = ".cost, .price, .budget"
    DESC_SELECTOR = ".text, .description, .desc"


class KabanchikParser(ConfigurableHTMLParser):
    name = "kabanchik"
    title = "Kabanchik.ua"
    country = "ua"
    enabled_default = True

    BASE = "https://kabanchik.ua"
    LIST_URL = "https://kabanchik.ua/orders"
    USE_DYNAMIC = True  # часто SPA/антибот
    CARD_SELECTOR = ".order, .task, .card, article, [class*='order']"
    TITLE_SELECTOR = "a[href*='/order'], a[href*='/task'], h3 a, a"
    PRICE_SELECTOR = ".price, .budget"
    DESC_SELECTOR = ".description, .text"


class PromUaParser(ConfigurableHTMLParser):
    name = "prom"
    title = "Prom.ua (услуги)"
    country = "ua"
    enabled_default = True
    require_want = True  # маркетплейс/классифайд

    BASE = "https://prom.ua"
    LIST_URL = "https://prom.ua/ua/search?search_term=розробка+сайту"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-qaid='product_block'], .x-gallery-tile, article, .card"
    TITLE_SELECTOR = "a[data-qaid='product_link'], a, h3"
    PRICE_SELECTOR = "[data-qaid='product_price'], .price"
    DESC_SELECTOR = ".description"


class WorkUaParser(ConfigurableHTMLParser):
    # Доска ВАКАНСИЙ. Раздел IT; фильтр найма оставит контракт/проект.
    name = "workua"
    title = "Work.ua (IT)"
    country = "ua"
    enabled_default = False

    BASE = "https://www.work.ua"
    LIST_URL = "https://www.work.ua/jobs-it/"
    CARD_SELECTOR = ".card, .job-link, [class*='job-link'], div[id^='job']"
    TITLE_SELECTOR = "h2 a, a.job-link, a[href*='/jobs/']"
    PRICE_SELECTOR = ".strong-600, .salary"
    DESC_SELECTOR = ".add-top-xs, .description"


class DouParser(ConfigurableHTMLParser):
    # DOU — сильный IT-раздел, но это ВАКАНСИИ. Фильтр найма оставит контракт.
    name = "dou"
    title = "DOU.ua (вакансии)"
    country = "ua"
    enabled_default = False

    BASE = "https://jobs.dou.ua"
    LIST_URL = "https://jobs.dou.ua/vacancies/"
    CARD_SELECTOR = ".l-vacancy, .vacancy, li.l-vacancy"
    TITLE_SELECTOR = "a.vt, a[href*='/vacancies/'], h2 a"
    PRICE_SELECTOR = ".salary"
    DESC_SELECTOR = ".sh-info, .description"
