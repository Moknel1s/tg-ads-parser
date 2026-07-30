"""
Парсер Avito (https://www.avito.ru) — раздел «Услуги», IT / интернет / телеком.

ВАЖНО: у Avito сильная защита от ботов и контент рендерится через JavaScript,
поэтому здесь используется Playwright (headless-браузер), а не обычный запрос.
Нужен установленный браузер: `playwright install chromium`.

Мы ищем объявления, где ЗАКАЗЧИК ищет исполнителя, поэтому по умолчанию
используем поиск по фразе. Селекторы вынесены в константы вверху файла.
"""
from __future__ import annotations

from urllib.parse import urljoin

from .base import Ad, BaseParser

BASE = "https://www.avito.ru"

# Поиск по услугам с запросом «нужен сайт / разработка сайта», сортировка — по дате.
# s=104 — сортировка «по дате»; category берётся из раздела «Услуги».
SEARCH_URL = (
    "https://www.avito.ru/all/predlozheniya_uslug"
    "?q=нужен+сайт+разработка+сайта&s=104"
)

# --- CSS-селекторы (Avito часто их меняет — правьте здесь) ---
CARD_SELECTOR = "[data-marker='item']"
TITLE_SELECTOR = "[itemprop='name'], [data-marker='item-title']"
LINK_SELECTOR = "a[data-marker='item-title'], a[itemprop='url']"
PRICE_SELECTOR = "[itemprop='price'], [data-marker='item-price']"
DESC_SELECTOR = "[class*='description'], meta[itemprop='description']"


class AvitoParser(BaseParser):
    name = "avito"
    title = "Avito (услуги)"
    country = "ru"
    # По умолчанию выключен: сильный антибот, часто отдаёт 0 без прокси.
    enabled_default = False

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        # Avito без рендера JS не отдаёт объявления — используем playwright
        html = await self._get_html_dynamic(SEARCH_URL, wait_selector=CARD_SELECTOR)
        soup = self.soup(html)

        ads: list[Ad] = []
        for card in soup.select(CARD_SELECTOR):
            link_el = card.select_one(LINK_SELECTOR)
            title_el = card.select_one(TITLE_SELECTOR)
            if not link_el:
                continue

            title = (title_el.get_text(strip=True) if title_el
                     else link_el.get_text(strip=True))
            href = link_el.get("href", "")
            if not title or not href:
                continue

            url = urljoin(BASE, href)

            price_el = card.select_one(PRICE_SELECTOR)
            price = ""
            if price_el:
                price = price_el.get("content") or price_el.get_text(strip=True)

            desc_el = card.select_one(DESC_SELECTOR)
            description = ""
            if desc_el:
                description = desc_el.get("content") or desc_el.get_text(" ", strip=True)

            ads.append(
                Ad(title=title, url=url, source=self.name, country=self.country,
                   description=description, price=price)
            )
        return ads
