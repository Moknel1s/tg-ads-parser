"""
Дополнительные US/глобальные площадки (по запросу пользователя).

ВНИМАНИЕ: большинство из них — доски ВАКАНСИЙ (Arc, Dice, WeWorkRemotely,
LinkedIn) или требуют вход (LinkedIn, Wellfound). Все добавлены ВЫКЛЮЧЕННЫМИ
(enabled_default=False). Даже если включить — фильтр найма
(EMPLOYMENT_STOP_KEYWORDS) отсеет штатные вакансии и оставит только проектную/
контрактную работу. Contra — фриланс-площадка.

Не добавлены (спарсить нельзя): Toptal, Gun.io (vetted-сети без публичной доски),
FlexJobs (платная подписка).
"""
from __future__ import annotations

from .base import Ad, BaseParser, ConfigurableHTMLParser


class WeWorkRemotelyParser(BaseParser):
    """Удалённые вакансии разработки через публичные RSS-ленты (доска вакансий)."""

    name = "weworkremotely"
    title = "We Work Remotely"
    country = "us"
    enabled_default = False  # доска вакансий — включайте осознанно

    FEEDS = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    ]

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        ads: list[Ad] = []
        seen: set[str] = set()
        for feed in self.FEEDS:
            try:
                items = await self._get_rss(feed)
            except Exception:  # noqa: BLE001
                continue
            for it in items:
                link = it.get("link", "")
                if not link or link in seen:
                    continue
                seen.add(link)
                desc = it.get("description", "")
                desc = self.soup(desc).get_text(" ", strip=True) if desc else ""
                ads.append(
                    Ad(title=it.get("title", ""), url=link, source=self.name,
                       country=self.country, description=desc[:500])
                )
        return ads


class ContraParser(ConfigurableHTMLParser):
    name = "contra"
    title = "Contra.com"
    country = "us"
    enabled_default = False

    BASE = "https://contra.com"
    LIST_URL = "https://contra.com/opportunities"
    USE_DYNAMIC = True  # React-SPA
    CARD_SELECTOR = "[data-testid='opportunity'], .opportunity, article, a[href*='/opportunity']"
    TITLE_SELECTOR = "a, h3, .title"
    PRICE_SELECTOR = ".budget, .rate"
    DESC_SELECTOR = ".description"


class ArcParser(ConfigurableHTMLParser):
    name = "arc"
    title = "Arc.dev"
    country = "us"
    enabled_default = False

    BASE = "https://arc.dev"
    LIST_URL = "https://arc.dev/remote-jobs"
    USE_DYNAMIC = True  # Next.js
    CARD_SELECTOR = "[data-testid='job-card'], .job-card, article, a[href*='/remote-jobs/']"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".salary, .rate"
    DESC_SELECTOR = ".description"


class DiceParser(ConfigurableHTMLParser):
    name = "dice"
    title = "Dice.com"
    country = "us"
    enabled_default = False

    BASE = "https://www.dice.com"
    LIST_URL = "https://www.dice.com/jobs?q=web%20developer%20contract"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-cy='card'], .search-card, dhi-search-card, a[href*='/job-detail/']"
    TITLE_SELECTOR = "a.card-title-link, a[data-cy='card-title-link'], h5 a, a"
    PRICE_SELECTOR = ".salary"
    DESC_SELECTOR = ".card-description, .description"


class LinkedInParser(ConfigurableHTMLParser):
    # ВНИМАНИЕ: скрейпинг LinkedIn против его правил. Лучше официальный API.
    name = "linkedin"
    title = "LinkedIn (Jobs)"
    country = "us"
    enabled_default = False

    BASE = "https://www.linkedin.com"
    LIST_URL = ("https://www.linkedin.com/jobs/search"
                "?keywords=web%20developer&f_WT=2")
    USE_DYNAMIC = True
    CARD_SELECTOR = ".base-card, .job-search-card, li"
    TITLE_SELECTOR = "a.base-card__full-link, h3.base-search-card__title, a"
    PRICE_SELECTOR = ".job-search-card__salary-info, .salary"
    DESC_SELECTOR = ".base-search-card__metadata"


class WellfoundParser(ConfigurableHTMLParser):
    name = "wellfound"
    title = "Wellfound (AngelList)"
    country = "us"
    enabled_default = False  # 403 без авторизации

    BASE = "https://wellfound.com"
    LIST_URL = "https://wellfound.com/role/r/web-developer"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-test='StartupResult'], .job-listing, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".compensation, .salary"
    DESC_SELECTOR = ".description"
