"""
Базовый модуль для всех парсеров.

Здесь:
  * dataclass Ad — единое представление объявления с любого сайта;
  * BaseParser — базовый класс. Чтобы добавить новый сайт, достаточно
    унаследоваться от BaseParser и реализовать метод fetch().

В базовом классе уже есть готовые помощники:
  * _get_html()          — GET-запрос статической страницы (aiohttp);
  * _get_json()          — GET-запрос JSON-API (aiohttp);
  * _get_html_dynamic()  — рендер динамической страницы (playwright);
  * soup()               — разбор HTML через BeautifulSoup;
  * safe_fetch()         — обёртка, которая ловит любые ошибки и не даёт боту упасть.
"""
from __future__ import annotations

import abc
import asyncio
import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

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
    """
    Приводит ссылку к каноническому виду (убирает query и fragment),
    чтобы одна и та же карточка не считалась разными объявлениями
    из-за utm-меток и прочего «мусора» в адресе.
    """
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
    source: str                      # источник (avito, youdo, hh, ...)
    description: str = ""             # короткое описание
    price: str = ""                  # цена/бюджет (если есть)
    found_at: datetime = field(default_factory=datetime.now)  # когда нашли

    @property
    def uid(self) -> str:
        """
        Уникальный идентификатор объявления = sha256 от нормализованной ссылки.
        Если ссылки нет — берём хэш от «источник + заголовок».
        Именно по uid проверяется, не отправляли ли мы объявление раньше.
        """
        base = normalize_url(self.url) or f"{self.source}:{self.title}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def text_blob(self) -> str:
        """Заголовок + описание одной строкой (для поиска по ключевым словам)."""
        return f"{self.title} {self.description}".strip()


class BaseParser(abc.ABC):
    """
    Базовый класс парсера. Наследники обязаны реализовать метод fetch().

    Атрибуты класса:
        name    — короткий машинный идентификатор сайта (avito, youdo, ...);
        title   — человекочитаемое название (для команды /sites);
        enabled — включён ли сайт (проставляется из конфига при создании).
    """

    name: str = "base"
    title: str = "Базовый парсер"
    enabled: bool = True

    @abc.abstractmethod
    async def fetch(self, keywords: list[str]) -> list[Ad]:
        """
        Получить список объявлений с сайта.

        keywords — текущие ключевые слова. Часть сайтов (например HH с его API)
        может использовать их прямо в поисковом запросе. Остальные могут
        игнорировать этот аргумент — окончательная фильтрация по ключевым
        словам всё равно происходит централизованно в планировщике.
        """
        raise NotImplementedError

    async def safe_fetch(self, keywords: list[str]) -> list[Ad]:
        """
        Безопасная обёртка над fetch(): ловит ЛЮБЫЕ ошибки, чтобы падение
        одного сайта не роняло весь бот. Возвращает не более MAX_ADS_PER_SITE.
        """
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
    #  Готовые помощники для наследников
    # ------------------------------------------------------------------
    @staticmethod
    def _headers() -> dict[str, str]:
        """Заголовки запроса со случайным User-Agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    @staticmethod
    async def _polite_delay() -> None:
        """Небольшая случайная задержка перед запросом (чтобы не банили)."""
        await asyncio.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    async def _get_html(self, url: str, params: dict | None = None) -> str:
        """GET статической страницы. Возвращает HTML как строку."""
        await self._polite_delay()
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(headers=self._headers(), timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def _get_json(self, url: str, params: dict | None = None,
                        headers: dict | None = None) -> dict:
        """
        GET JSON-API. Возвращает распарсенный JSON (dict).
        headers — дополнительные заголовки (перекрывают стандартные),
        например для API, требующих особый User-Agent.
        """
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

    async def _get_html_dynamic(self, url: str, wait_selector: str | None = None,
                                timeout_ms: int = 30000) -> str:
        """
        Рендер динамической страницы через Playwright (headless Chromium).
        Нужен для сайтов, которые подгружают контент через JavaScript (Avito и др.).

        Требует установленного браузера: `playwright install chromium`.
        """
        # Импортируем внутри метода, чтобы playwright не был обязателен,
        # если динамические сайты не используются.
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
                    # Ждём появления нужного блока (не критично, если не дождались)
                    try:
                        await page.wait_for_selector(wait_selector, timeout=10000)
                    except Exception:  # noqa: BLE001
                        pass
                return await page.content()
            finally:
                await browser.close()

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        """Разбирает HTML в объект BeautifulSoup (парсер html.parser — без доп. зависимостей)."""
        return BeautifulSoup(html, "html.parser")
