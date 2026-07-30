"""
Парсер Kwork (https://kwork.ru/projects) — «Биржа» проектов от заказчиков.

Kwork — это Vue-приложение: карточки НЕ лежат в HTML, а рендерятся из большого
JSON-объекта `window.stateData`, встроенного в страницу. Поэтому мы вытаскиваем
этот JSON и читаем список проектов из ключа `wants` — это гораздо надёжнее, чем
парсить CSS-селекторы (которые к тому же в статике отсутствуют).
"""
from __future__ import annotations

import json

from .base import Ad, BaseParser

LIST_URL = "https://kwork.ru/projects"

# Куда ведёт ссылка на проект (по его id)
PROJECT_URL = "https://kwork.ru/projects/{id}/view"


class KworkParser(BaseParser):
    name = "kwork"
    title = "Kwork (биржа проектов)"
    country = "ru"
    enabled_default = True

    async def fetch(self, keywords: list[str]) -> list[Ad]:
        html = await self._get_html(LIST_URL)

        data = _extract_state_data(html)
        if not data:
            return []

        # Список проектов может лежать в разных местах в зависимости от версии
        wants = (
            data.get("wants")
            or data.get("wantsListData", {}).get("wants")
            or []
        )

        ads: list[Ad] = []
        for w in wants:
            wid = w.get("id")
            name = (w.get("name") or "").strip()
            if not wid or not name:
                continue

            ads.append(
                Ad(
                    title=name,
                    url=PROJECT_URL.format(id=wid),
                    source=self.name,
                    country=self.country,
                    description=(w.get("description") or "").strip(),
                    price=_format_price(w),
                )
            )
        return ads


def _extract_state_data(html: str) -> dict | None:
    """
    Достаёт объект `window.stateData = {...};` из HTML.
    Используем json.raw_decode — он корректно находит конец JSON-объекта
    (учитывает вложенные скобки и кавычки), в отличие от «жадной» регулярки.
    """
    marker = "window.stateData"
    idx = html.find(marker)
    if idx == -1:
        return None
    start = html.find("{", idx)
    if start == -1:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(html, start)
        return obj
    except (json.JSONDecodeError, ValueError):
        return None


def _format_price(w: dict) -> str:
    """Формирует строку бюджета из priceLimit / possiblePriceLimit."""
    def clean(x) -> str | None:
        try:
            return str(int(float(x)))
        except (TypeError, ValueError):
            return None

    low = clean(w.get("priceLimit"))
    high = clean(w.get("possiblePriceLimit"))

    if low and high and high != low:
        return f"{low}–{high} ₽"
    if low:
        return f"от {low} ₽"
    return ""
