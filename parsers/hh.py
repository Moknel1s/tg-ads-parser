"""
Парсер HH.ru — через официальный публичный API (https://api.hh.ru/vacancies).

Это самый надёжный источник: официальный JSON-API не требует обхода защит
и не банит за парсинг (в разумных пределах). Берём свежие вакансии за сутки
по разработке/вёрстке, а окончательный отбор по ключевым словам делает планировщик.
"""
from __future__ import annotations

from .base import Ad, BaseParser

# Короткий поисковый запрос по названию вакансии.
# Держим его компактным: слишком длинный URL HH отклоняет с 403.
# Окончательная фильтрация по вашим ключевым словам всё равно идёт в планировщике.
BASE_QUERY = "разработка сайта OR лендинг OR верстка OR веб-разработчик"

API_URL = "https://api.hh.ru/vacancies"

# HH требует осмысленный User-Agent с названием приложения, иначе отвечает 403.
HH_HEADERS = {"User-Agent": "tg-ads-parser/1.0 (freelance monitor)"}


class HHParser(BaseParser):
    name = "hh"
    title = "HH.ru (вакансии)"
    country = "ru"
    enabled_default = True

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        params = {
            "text": BASE_QUERY,
            "search_field": "name",          # искать в названии вакансии
            "per_page": 50,
            "order_by": "publication_time",  # сначала самые свежие
            "period": 1,                     # за последний день
        }
        data = await self._get_json(API_URL, params=params, headers=HH_HEADERS)

        ads: list[Ad] = []
        for item in data.get("items", []):
            title = item.get("name") or "Без названия"
            url = item.get("alternate_url") or ""

            # Короткое описание собираем из snippet (требования + обязанности)
            snippet = item.get("snippet") or {}
            desc_parts = [snippet.get("requirement"), snippet.get("responsibility")]
            description = " ".join(p for p in desc_parts if p)
            # Убираем HTML-теги подсветки <highlighttext>
            description = description.replace("<highlighttext>", "").replace("</highlighttext>", "")

            # Зарплата → строка с ценой
            price = _format_salary(item.get("salary"))

            ads.append(
                Ad(
                    title=title,
                    url=url,
                    source=self.name,
                    country=self.country,
                    description=description,
                    price=price,
                )
            )
        return ads


def _format_salary(salary: dict | None) -> str:
    """Превращает объект зарплаты HH в читаемую строку."""
    if not salary:
        return ""
    frm, to = salary.get("from"), salary.get("to")
    cur = salary.get("currency", "")
    if frm and to:
        return f"{frm}–{to} {cur}"
    if frm:
        return f"от {frm} {cur}"
    if to:
        return f"до {to} {cur}"
    return ""
