"""
Middleware (промежуточные обработчики).

AdminMiddleware пропускает к обработчикам только сообщения от владельца бота
(ADMIN_ID из .env). Все чужие сообщения молча игнорируются — так посторонние
не смогут управлять вашим ботом.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import ADMIN_ID

log = logging.getLogger(__name__)


class AdminMiddleware(BaseMiddleware):
    """Пропускает только владельца бота (ADMIN_ID)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # aiogram кладёт пользователя события в data["event_from_user"]
        user = data.get("event_from_user")

        # Если ADMIN_ID не задан — пропускаем всех (удобно для первичной настройки),
        # но об этом предупреждаем в логах при старте (см. main.py).
        if ADMIN_ID and user is not None and user.id != ADMIN_ID:
            log.info("Игнорирую сообщение от постороннего пользователя id=%s", user.id)
            return None

        return await handler(event, data)
