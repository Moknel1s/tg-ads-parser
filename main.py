"""
Точка входа приложения.

Здесь всё собирается вместе:
  * настраивается логирование;
  * проверяется конфигурация (.env);
  * создаётся бот и диспетчер aiogram;
  * подключается middleware (доступ только владельцу) и обработчики команд;
  * инициализируется БД;
  * запускается планировщик автопарсинга;
  * стартует long-polling бота.

Запуск:  python main.py
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from bot.handlers import router
from bot.middlewares import AdminMiddleware
from database import db
from scheduler.jobs import run_parsing, setup_scheduler


def setup_logging() -> None:
    """Настраивает логирование в консоль."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    # Убираем слишком «болтливые» логи сторонних библиотек
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


log = logging.getLogger("main")


async def main() -> None:
    setup_logging()

    # 1. Проверяем обязательные настройки
    errors = config.validate()
    if errors:
        for err in errors:
            log.error("Ошибка конфигурации: %s", err)
        log.error("Заполните .env (см. .env.example) и перезапустите бота.")
        return

    # 2. Создаём бота (все сообщения — в формате HTML)
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # 3. Диспетчер + middleware + обработчики
    dp = Dispatcher()
    dp.message.middleware(AdminMiddleware())      # к командам — только владелец
    dp.callback_query.middleware(AdminMiddleware())
    dp.include_router(router)

    # 4. Инициализируем базу данных
    await db.init_db()

    # 5. Запускаем планировщик автопарсинга (объявления идут в TARGET_CHAT_ID)
    scheduler = setup_scheduler(bot, config.TARGET_CHAT_ID)
    scheduler.start()

    # 6. Делаем первый прогон парсинга при старте (не блокируем запуск бота)
    asyncio.create_task(run_parsing(bot, config.TARGET_CHAT_ID))

    log.info("Бот запущен. Ожидаю команды…")
    try:
        # Удаляем возможные «зависшие» апдейты и стартуем long-polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        # Аккуратно гасим всё при остановке
        scheduler.shutdown(wait=False)
        await db.close_db()
        await bot.session.close()
        log.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Ctrl+C — штатная остановка
        pass
