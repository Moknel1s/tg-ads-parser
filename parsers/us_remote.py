"""
Глобальные / удалённые job-борды и биржи (страна us).

Реальное состояние (проверено вживую 2026-07):
  ✅ We Work Remotely — публичные RSS-ленты (работает сразу)
  ⚙️ Arc.dev, Contra, LinkedIn — JS/SPA + антибот (best-effort, через playwright)
  ❌ Wellfound (403), Toptal (403) — блокируют скрейпинг
  ❌ FlexJobs — платная подписка (контент за пейволом)
  ❌ Gun.io, Codeable — vetted-сети: публичной доски заказов нет
     (клиенты подают заявки приватно)

Реально отдаёт данные только WeWorkRemotely — он включён. Остальные добавлены
как классы, но ВЫКЛЮЧЕНЫ по умолчанию: включаются в .env (SITE_LINKEDIN=1 и т.п.)
после добавления авторизации/API-ключей/прокси и проверки селекторов.
Внимание: скрейпинг LinkedIn и ряда площадок может нарушать их правила —
используйте официальные API, где это возможно.
"""
from __future__ import annotations

from .base import Ad, BaseParser, ConfigurableHTMLParser


class WeWorkRemotelyParser(BaseParser):
    """Удалённые вакансии разработки через публичные RSS-ленты WeWorkRemotely."""

    name = "weworkremotely"
    title = "We Work Remotely"
    country = "us"
    # Выключен: это доска ВАКАНСИЙ (наём удалённых сотрудников), а не заказов.
    enabled_default = False

    FEEDS = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    ]

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        ads: list[Ad] = []
        seen: set[str] = set()
        for feed in self.FEEDS:
            try:
                items = await self._get_rss(feed)
            except Exception:  # noqa: BLE001 — одна лента не должна ронять остальные
                continue
            for it in items:
                link = it.get("link", "")
                if not link or link in seen:
                    continue
                seen.add(link)
                # Описание в RSS содержит HTML — вычищаем теги
                raw_desc = it.get("description", "")
                description = self.soup(raw_desc).get_text(" ", strip=True) if raw_desc else ""
                ads.append(
                    Ad(title=it.get("title", ""), url=link, source=self.name,
                       country=self.country, description=description[:500])
                )
        return ads


# ---------------------------------------------------------------------------
#  Ниже — выключены по умолчанию (нужны авторизация / API / прокси)
# ---------------------------------------------------------------------------
class ArcParser(ConfigurableHTMLParser):
    name = "arc"
    title = "Arc.dev"
    country = "us"
    enabled_default = False

    BASE = "https://arc.dev"
    LIST_URL = "https://arc.dev/remote-jobs"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-testid='job-card'], .job-card, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".salary, .rate"
    DESC_SELECTOR = ".description"


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


class ContraParser(ConfigurableHTMLParser):
    name = "contra"
    title = "Contra.com"
    country = "us"
    enabled_default = False

    BASE = "https://contra.com"
    LIST_URL = "https://contra.com/opportunities"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-testid='opportunity'], .opportunity, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".budget, .rate"
    DESC_SELECTOR = ".description"


class LinkedInParser(ConfigurableHTMLParser):
    # ВНИМАНИЕ: скрейпинг LinkedIn против его правил. Лучше официальный API.
    name = "linkedin"
    title = "LinkedIn (вакансии)"
    country = "us"
    enabled_default = False

    BASE = "https://www.linkedin.com"
    LIST_URL = ("https://www.linkedin.com/jobs/search"
                "?keywords=web%20developer&f_WT=2")  # f_WT=2 — удалёнка
    USE_DYNAMIC = True
    CARD_SELECTOR = ".base-card, .job-search-card, li"
    TITLE_SELECTOR = "a.base-card__full-link, h3.base-search-card__title, a"
    PRICE_SELECTOR = ".job-search-card__salary-info, .salary"
    DESC_SELECTOR = ".base-search-card__metadata"


class GunIoParser(ConfigurableHTMLParser):
    # ❌ vetted-сеть: публичной доски заказов нет. Оставлен как заглушка-класс.
    name = "gunio"
    title = "Gun.io"
    country = "us"
    enabled_default = False

    BASE = "https://gun.io"
    LIST_URL = "https://gun.io/find-work/"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job, .card, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".rate, .price"
    DESC_SELECTOR = ".description"


class CodeableParser(ConfigurableHTMLParser):
    # ❌ Клиенты подают заявки приватно — публичной доски нет.
    name = "codeable"
    title = "Codeable.io"
    country = "us"
    enabled_default = False

    BASE = "https://codeable.io"
    LIST_URL = "https://codeable.io/"
    CARD_SELECTOR = ".project, .card, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".price"
    DESC_SELECTOR = ".description"


class FlexJobsParser(ConfigurableHTMLParser):
    # ❌ Контент за платной подпиской (пейвол).
    name = "flexjobs"
    title = "FlexJobs"
    country = "us"
    enabled_default = False

    BASE = "https://www.flexjobs.com"
    LIST_URL = "https://www.flexjobs.com/search?search=web+developer"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job, .sc-job, article"
    TITLE_SELECTOR = "a, h4, h3"
    PRICE_SELECTOR = ".salary"
    DESC_SELECTOR = ".description"


class ToptalParser(ConfigurableHTMLParser):
    # ❌ vetted-сеть, публичной доски заказов нет + блокирует скрейпинг (403).
    name = "toptal"
    title = "Toptal"
    country = "us"
    enabled_default = False

    BASE = "https://www.toptal.com"
    LIST_URL = "https://www.toptal.com/careers"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".job, .card, article"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".rate"
    DESC_SELECTOR = ".description"
