"""
Площадки США 🇺🇸 (сюда же вынесены глобальные маркетплейсы, чтобы не дублировать
их в каждой стране: Upwork, Fiverr, Freelancer.com, Guru, Thumbtack).

Реально работающие без авторизации:
  * Reddit (r/forhire и др.) — через публичный JSON;
  * Craigslist — через RSS-ленты.

Глобальные маркетплейсы требуют авторизацию/API-ключи или имеют сильный антибот,
поэтому по умолчанию ВЫКЛЮЧЕНЫ (enabled_default=False). Включаются в .env после
добавления ключей/прокси и проверки селекторов.
"""
from __future__ import annotations

from .base import Ad, BaseParser, ConfigurableHTMLParser


class RedditParser(BaseParser):
    """Посты «[Hiring]» из сабреддитов фриланса — через публичный JSON Reddit."""

    name = "reddit"
    title = "Reddit (r/forhire и др.)"
    country = "us"
    enabled_default = True

    SUBREDDITS = ["forhire", "jobbit", "freelance_forhire"]

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        ads: list[Ad] = []
        for sub in self.SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub}/new.json"
            try:
                data = await self._get_json(
                    url,
                    params={"limit": 50},
                    headers={"User-Agent": "loomis-ads-parser/1.0 (by u/loomis)"},
                )
            except Exception:  # noqa: BLE001 — один сабреддит не должен ронять остальные
                continue

            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                title = d.get("title", "") or ""
                # Берём только объявления, где ИЩУТ исполнителя ([Hiring]).
                if "[hiring]" not in title.lower():
                    continue
                permalink = d.get("permalink", "")
                link = f"https://www.reddit.com{permalink}" if permalink else d.get("url", "")
                description = (d.get("selftext", "") or "")[:500]
                ads.append(
                    Ad(title=title, url=link, source=self.name, country=self.country,
                       description=description)
                )
        return ads


class CraigslistParser(BaseParser):
    """Computer-gigs с Craigslist — через RSS-ленты нескольких городов."""

    name = "craigslist"
    title = "Craigslist (gigs)"
    country = "us"
    enabled_default = True

    # Категория cpg = computer gigs, запрос website. Города можно добавлять.
    FEEDS = [
        "https://newyork.craigslist.org/search/cpg?format=rss&query=website",
        "https://sfbay.craigslist.org/search/cpg?format=rss&query=website",
        "https://losangeles.craigslist.org/search/cpg?format=rss&query=website",
    ]

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        ads: list[Ad] = []
        for feed in self.FEEDS:
            try:
                items = await self._get_rss(feed)
            except Exception:  # noqa: BLE001
                continue
            for it in items:
                if not it.get("link"):
                    continue
                ads.append(
                    Ad(title=it.get("title", ""), url=it["link"], source=self.name,
                       country=self.country, description=it.get("description", ""))
                )
        return ads


# ---------------------------------------------------------------------------
#  Глобальные маркетплейсы (по умолчанию выключены — нужны ключи/прокси)
# ---------------------------------------------------------------------------
class UpworkParser(ConfigurableHTMLParser):
    name = "upwork"
    title = "Upwork (глобально)"
    country = "us"
    enabled_default = False  # нужен вход/официальный API

    BASE = "https://www.upwork.com"
    LIST_URL = "https://www.upwork.com/nx/search/jobs/?q=web%20development"
    USE_DYNAMIC = True
    CARD_SELECTOR = "article[data-test='JobTile'], section.job-tile"
    TITLE_SELECTOR = "a.job-tile-title-link, h2 a, a[href*='/jobs/']"
    PRICE_SELECTOR = "[data-test='budget'], .js-budget"
    DESC_SELECTOR = "[data-test='job-description-text'], .description"


class FiverrParser(ConfigurableHTMLParser):
    name = "fiverr"
    title = "Fiverr (глобально)"
    country = "us"
    enabled_default = False  # buyer requests требуют вход

    BASE = "https://www.fiverr.com"
    LIST_URL = "https://www.fiverr.com/search/gigs?query=web%20development"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".gig-card-layout, [data-gig-id]"
    TITLE_SELECTOR = "a[href*='/gigs/'], h3 a"
    PRICE_SELECTOR = ".price, [data-testid='price']"
    DESC_SELECTOR = ".description"


class FreelancerComParser(ConfigurableHTMLParser):
    name = "freelancercom"
    title = "Freelancer.com (глобально)"
    country = "us"
    enabled_default = False

    BASE = "https://www.freelancer.com"
    LIST_URL = "https://www.freelancer.com/jobs/website/"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".JobSearchCard-item, [data-project-id]"
    TITLE_SELECTOR = "a.JobSearchCard-primary-heading-link, h3 a"
    PRICE_SELECTOR = ".JobSearchCard-primary-price, .price"
    DESC_SELECTOR = ".JobSearchCard-primary-description, .description"


class GuruParser(ConfigurableHTMLParser):
    name = "guru"
    title = "Guru (глобально)"
    country = "us"
    enabled_default = False

    BASE = "https://www.guru.com"
    LIST_URL = "https://www.guru.com/d/jobs/skill/website-design/"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".record, li.serviceListing"
    TITLE_SELECTOR = "a.h5, h2 a, a[href*='/jobs/']"
    PRICE_SELECTOR = ".budget, .price"
    DESC_SELECTOR = ".desc, .description"


class ThumbtackParser(ConfigurableHTMLParser):
    name = "thumbtack"
    title = "Thumbtack (глобально)"
    country = "us"
    enabled_default = False  # лиды требуют аккаунт-профи

    BASE = "https://www.thumbtack.com"
    LIST_URL = "https://www.thumbtack.com/k/website-design/near-me/"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".service-card, [data-test='ServiceCard']"
    TITLE_SELECTOR = "a, h3"
    PRICE_SELECTOR = ".price"
    DESC_SELECTOR = ".description"
