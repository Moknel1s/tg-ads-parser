"""
Парсер YouDo (https://youdo.com) — раздел заданий по разработке сайтов.

Внимание: вёрстка YouDo периодически меняется. Все CSS-селекторы вынесены
в константы вверху файла — если сайт поменяет разметку, поправьте их здесь.
"""
from __future__ import annotations

from urllib.parse import urljoin

from .base import Ad, BaseParser

# Страница со списком открытых заданий по разработке сайтов
LIST_URL = "https://youdo.com/tasks-all-opened-all/development-sites/"
BASE = "https://youdo.com"

# --- CSS-селекторы (правьте здесь, если сайт изменит вёрстку) ---
CARD_SELECTOR = "div[data-task-id], .TasksList-item, .b-task"   # карточка задания
TITLE_SELECTOR = "a.TasksList-itemLink, a.b-task-title, a[href*='/t']"  # заголовок-ссылка
PRICE_SELECTOR = ".TasksList-itemPrice, .b-task-price, [class*='price']"  # бюджет
DESC_SELECTOR = ".TasksList-itemDescription, .b-task-description"        # описание


class YouDoParser(BaseParser):
    name = "youdo"
    title = "YouDo (задания)"
    country = "ru"
    enabled_default = True

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        html = await self._get_html(LIST_URL)
        soup = self.soup(html)

        ads: list[Ad] = []
        for card in soup.select(CARD_SELECTOR):
            link_el = card.select_one(TITLE_SELECTOR)
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            href = link_el.get("href", "")
            if not title or not href:
                continue

            url = urljoin(BASE, href)

            price_el = card.select_one(PRICE_SELECTOR)
            price = price_el.get_text(strip=True) if price_el else ""

            desc_el = card.select_one(DESC_SELECTOR)
            description = desc_el.get_text(" ", strip=True) if desc_el else ""

            ads.append(
                Ad(title=title, url=url, source=self.name, country=self.country,
                   description=description, price=price)
            )
        return ads
