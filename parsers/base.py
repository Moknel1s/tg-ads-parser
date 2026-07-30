"""
Базовый модуль для всех парсеров.

Здесь:
  * dataclass Ad — единое представление объявления (с указанием страны);
  * BaseParser — базовый класс парсера;
  * ConfigurableHTMLParser — база для «типовых» сайтов: достаточно задать
    несколько CSS-селекторов классом-атрибутом, и парсер готов;
  * helpers: HTTP (aiohttp), рендер JS (playwright), RSS (xml.etree).

Чтобы добавить новый сайт — см. parsers/__init__.py (там инструкция).
"""
from __future__ import annotations

import abc
import asyncio
import hashlib
import logging
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

import aiohttp
from bs4 import BeautifulSoup

from config import (
    MAX_ADS_PER_SITE,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    USER_AGENTS,
)

log = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Приводит ссылку к каноническому виду (убирает query и fragment)."""
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", "")).rstrip("/")
    except ValueError:
        return url


@dataclass
class Ad:
    """Единое представление объявления с любого сайта."""

    title: str                       # заголовок
    url: str                         # ссылка на объявление
    source: str                      # источник (машинный ключ: flru, kwork, ...)
    country: str = "ru"              # код страны источника (ru/uz/us/gb/au)
    description: str = ""             # короткое описание
    price: str = ""                  # цена/бюджет (если есть)
    found_at: datetime = field(default_factory=datetime.now)

    @property
    def uid(self) -> str:
        """Уникальный идентификатор = sha256 от нормализованной ссылки."""
        base = normalize_url(self.url) or f"{self.source}:{self.title}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def text_blob(self) -> str:
        """Заголовок + описание одной строкой (для поиска по ключевым словам)."""
        return f"{self.title} {self.description}".strip()


class BaseParser(abc.ABC):
    """
    Базовый класс парсера. Наследники обязаны реализовать метод fetch().

    Атрибуты класса:
        name            — машинный ключ сайта (flru, kwork, olxuz, reddit, ...);
        title           — человекочитаемое название (для /sites);
        country         — код страны источника (ru/uz/us/gb/au);
        enabled_default — включён ли сайт по умолчанию (False для сайтов,
                          которым нужны ключи API / прокси / проверка селекторов);
        enabled         — итоговое включение (ставится реестром из конфига).
    """

    name: str = "base"
    title: str = "Базовый парсер"
    country: str = "ru"
    enabled_default: bool = True
    enabled: bool = True

    @abc.abstractmethod
    async def fetch(self, keywords: list[str]) -> list[Ad]:
        """Получить список объявлений с сайта."""
        raise NotImplementedError

    async def safe_fetch(self, keywords: list[str]) -> list[Ad]:
        """Безопасная обёртка: ловит любые ошибки, не даёт боту упасть."""
        if not self.enabled:
            return []
        try:
            ads = await self.fetch(keywords)
            log.info("[%s] получено объявлений: %d", self.name, len(ads))
            return ads[:MAX_ADS_PER_SITE]
        except Exception as exc:  # noqa: BLE001 — намеренно ловим всё
            log.warning("[%s] ошибка парсинга: %s", self.name, exc)
            return []

    # ------------------------------------------------------------------
    #  Готовые помощники
    # ------------------------------------------------------------------
    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8,uz;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    @staticmethod
    async def _polite_delay() -> None:
        await asyncio.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    async def _get_html(self, url: str, params: dict | None = None) -> str:
        """GET статической страницы. Возвращает HTML/текст."""
        await self._polite_delay()
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(headers=self._headers(), timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def _get_json(self, url: str, params: dict | None = None,
                        headers: dict | None = None) -> dict:
        """GET JSON-API. headers — дополнительные заголовки (перекрывают базовые)."""
        await self._polite_delay()
        timeout = aiohttp.ClientTimeout(total=25)
        hdrs = self._headers()
        hdrs["Accept"] = "application/json"
        if headers:
            hdrs.update(headers)
        async with aiohttp.ClientSession(headers=hdrs, timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _get_rss(self, url: str, params: dict | None = None) -> list[dict]:
        """
        GET RSS/Atom/RDF-ленты. Возвращает список словарей
        {title, link, description}. Работает без внешних зависимостей.
        """
        text = await self._get_html(url, params=params)
        return parse_rss(text)

    async def _get_html_dynamic(self, url: str, wait_selector: str | None = None,
                                timeout_ms: int = 30000) -> str:
        """Рендер динамической страницы через Playwright (для JS-сайтов)."""
        from playwright.async_api import async_playwright

        await self._polite_delay()
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    locale="ru-RU",
                )
                page = await context.new_page()
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                if wait_selector:
                    try:
                        await page.wait_for_selector(wait_selector, timeout=10000)
                    except Exception:  # noqa: BLE001
                        pass
                return await page.content()
            finally:
                await browser.close()

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")


class ConfigurableHTMLParser(BaseParser):
    """
    База для «типовых» сайтов со списком объявлений в HTML.
    Чтобы описать сайт — достаточно задать атрибуты класса
    (URL и CSS-селекторы). Логика обхода карточек общая.

    Если сайт динамический (JS) — поставьте USE_DYNAMIC = True.
    """

    BASE: str = ""            # базовый домен для достройки относительных ссылок
    LIST_URL: str = ""        # страница со списком объявлений
    USE_DYNAMIC: bool = False # рендерить ли через playwright

    CARD_SELECTOR: str = ""   # селектор карточки объявления
    TITLE_SELECTOR: str = ""  # селектор заголовка (внутри карточки)
    LINK_SELECTOR: str = ""   # селектор ссылки (по умолчанию = TITLE_SELECTOR)
    PRICE_SELECTOR: str = ""  # селектор цены/бюджета (необязательно)
    DESC_SELECTOR: str = ""   # селектор описания (необязательно)

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        if not self.LIST_URL or not self.CARD_SELECTOR:
            return []

        if self.USE_DYNAMIC:
            html = await self._get_html_dynamic(self.LIST_URL, self.CARD_SELECTOR)
        else:
            html = await self._get_html(self.LIST_URL)

        soup = self.soup(html)
        base = self.BASE or self.LIST_URL
        link_sel = self.LINK_SELECTOR or self.TITLE_SELECTOR

        ads: list[Ad] = []
        for card in soup.select(self.CARD_SELECTOR):
            link_el = card.select_one(link_sel)
            if not link_el:
                continue

            title_el = card.select_one(self.TITLE_SELECTOR) if self.TITLE_SELECTOR else link_el
            title = (title_el or link_el).get_text(strip=True)
            href = link_el.get("href", "")
            if not title or not href:
                continue

            url = urljoin(base, href)
            price = _extract(card, self.PRICE_SELECTOR)
            description = _extract(card, self.DESC_SELECTOR)

            ads.append(
                Ad(title=title, url=url, source=self.name, country=self.country,
                   description=description, price=price)
            )
        return ads


# ---------------------------------------------------------------------------
#  Вспомогательные функции модуля
# ---------------------------------------------------------------------------
def _extract(card, selector: str) -> str:
    """Достаёт текст (или content=) из первого совпавшего селектора карточки."""
    if not selector:
        return ""
    el = card.select_one(selector)
    if not el:
        return ""
    return (el.get("content") or el.get_text(" ", strip=True) or "").strip()


def _local(tag: str) -> str:
    """Возвращает имя XML-тега без namespace (например '{...}item' -> 'item')."""
    return tag.split("}")[-1].lower()


def parse_rss(text: str) -> list[dict]:
    """
    Разбирает RSS / Atom / RDF в список {title, link, description}.
    Использует стандартный xml.etree — без внешних зависимостей.
    """
    items: list[dict] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return items

    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        entry: dict[str, str] = {"title": "", "link": "", "description": ""}
        for child in node:
            tag = _local(child.tag)
            if tag == "title":
                entry["title"] = (child.text or "").strip()
            elif tag == "link":
                # RSS: текст внутри <link>; Atom: атрибут href
                entry["link"] = (child.get("href") or child.text or "").strip()
            elif tag in ("description", "summary", "content"):
                entry["description"] = (child.text or "").strip()
        if entry["title"]:
            items.append(entry)
    return items
