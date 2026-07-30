"""
Middleware (промежуточные обработчики).

AdminMiddleware пропускает к обработчикам только сообщения от разрешённых
пользователей (список ADMIN_IDS из .env). Все чужие сообщения молча
игнорируются — так посторонние не смогут управлять вашим ботом.

Важно: ADMIN_IDS — это ЛИЧНЫЕ ID людей (положительные). Не путать с
TARGET_CHAT_ID (куда шлём объявления — там может быть ID группы, отрицательный).
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import ADMIN_IDS

log = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Пропускает только пользователей из списка ADMIN_IDS."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # aiogram кладёт пользователя события в data["event_from_user"]
        user = data.get("event_from_user")

        # Если список ADMIN_IDS пуст — пропускаем всех (удобно для первичной
        # настройки), об этом предупреждается в логах при старте (см. main.py).
        if ADMIN_IDS and user is not None and user.id not in ADMIN_IDS:
            log.info("Игнорирую сообщение от постороннего пользователя id=%s", user.id)
            return None

        return await handler(event, data)
