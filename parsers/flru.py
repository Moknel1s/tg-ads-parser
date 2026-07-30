"""
Парсер FL.ru (https://www.fl.ru) — лента проектов по разработке сайтов.

Внимание: у FL.ru есть защита от ботов, а вёрстка периодически меняется.
CSS-селекторы вынесены в константы вверху файла — правьте их при необходимости.
Если статический запрос перестанет отдавать данные, включите USE_DYNAMIC = True
(потребуется установленный playwright: `playwright install chromium`).
"""
from __future__ import annotations

from urllib.parse import urljoin

from .base import Ad, BaseParser

# Лента проектов (категория «Сайты «под ключ»»)
LIST_URL = "https://www.fl.ru/projects/"
BASE = "https://www.fl.ru"

# Использовать ли рендер через playwright вместо обычного запроса
USE_DYNAMIC = False

# --- CSS-селекторы (правьте здесь при смене вёрстки) ---
CARD_SELECTOR = ".b-post, div[id^='project-item'], .project-item"  # карточка проекта
TITLE_SELECTOR = "a.b-post__link, h2 a, a[href*='/projects/']"     # заголовок-ссылка
PRICE_SELECTOR = ".b-post__price, .b-layout__txt_price, [class*='price']"  # бюджет
DESC_SELECTOR = ".b-post__txt, .b-layout__txt, .project-description"       # описание


class FLruParser(BaseParser):
    name = "flru"
    title = "FL.ru (проекты)"

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        if USE_DYNAMIC:
            html = await self._get_html_dynamic(LIST_URL, wait_selector=CARD_SELECTOR)
        else:
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
                Ad(title=title, url=url, source=self.name,
                   description=description, price=price)
            )
        return ads
