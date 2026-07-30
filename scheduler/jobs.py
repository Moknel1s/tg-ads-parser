"""
Ядро парсинга и планировщик.

Здесь:
  * run_parsing()    — один полный проход: опросить все сайты параллельно,
                       отфильтровать по ключевым словам, отсеять дубли и
                       отправить новые объявления в личку;
  * setup_scheduler()— настраивает APScheduler на автозапуск каждые 7–10 минут;
  * LAST_RUN_STATS   — статистика последнего прогона (для команд /status и /sites).
"""
from __future__ import annotations

import asyncio
import html
import logging
import random
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.keyboards import ad_keyboard
from config import PARSE_INTERVAL_MAX, PARSE_INTERVAL_MIN
from database import db
from parsers import Ad, get_parsers

log = logging.getLogger(__name__)

# Блокировка, чтобы два парсинга не запускались одновременно
# (например, автозапуск по расписанию + ручной /parse_now).
_lock = asyncio.Lock()

# Статистика последнего прогона: имя сайта -> сколько объявлений получено.
# Используется командами /status и /sites. "error" — если сайт упал.
LAST_RUN_STATS: dict[str, str | int] = {}

# Человекочитаемые названия источников для сообщений
SOURCE_TITLES = {
    "avito": "Avito",
    "youdo": "YouDo",
    "flru": "FL.ru",
    "kwork": "Kwork",
    "hh": "HH.ru",
}


# ---------------------------------------------------------------------------
#  Фильтрация по ключевым словам
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Приводит текст к нижнему регистру и заменяет ё→е для устойчивого поиска."""
    return text.lower().replace("ё", "е")


def keyword_match(ad: Ad, keywords: list[str]) -> bool:
    """
    True, если в заголовке или описании объявления встречается
    хотя бы одно ключевое слово. Если ключевых слов нет — пропускаем всё.
    """
    if not keywords:
        return True
    blob = _normalize(ad.text_blob())
    return any(_normalize(kw) in blob for kw in keywords)


# ---------------------------------------------------------------------------
#  Форматирование и отправка сообщения
# ---------------------------------------------------------------------------
def format_message(ad: Ad) -> str:
    """Собирает красивое HTML-сообщение по объявлению."""
    source = SOURCE_TITLES.get(ad.source, ad.source)
    title = html.escape(ad.title)

    lines = [f"🆕 <b>{title}</b>", ""]

    if ad.description:
        # Обрезаем описание, чтобы сообщение не было слишком длинным
        desc = ad.description.strip()
        if len(desc) > 400:
            desc = desc[:400].rstrip() + "…"
        lines.append(html.escape(desc))
        lines.append("")

    if ad.price:
        lines.append(f"💰 <b>Бюджет:</b> {html.escape(ad.price)}")

    lines.append(f"🌐 <b>Источник:</b> {html.escape(source)}")
    lines.append(f"🕒 <b>Найдено:</b> {ad.found_at.strftime('%d.%m.%Y %H:%M')}")

    return "\n".join(lines)


async def _send_ad(bot: Bot, chat_id: int, ad: Ad) -> bool:
    """
    Отправляет одно объявление в личку с кнопкой «Открыть объявление».
    Возвращает True при успешной доставке и False, если отправить не удалось
    (например, вы ещё не нажали боту /start или заблокировали его).
    Любые ошибки перехватываются — падения бота не происходит.
    """
    text = format_message(ad)
    keyboard = ad_keyboard(ad.url) if ad.url else None
    try:
        await bot.send_message(chat_id, text, reply_markup=keyboard)
        return True
    except TelegramRetryAfter as exc:
        # Telegram просит подождать (флуд-контроль) — ждём и пробуем ещё раз
        log.warning("Флуд-контроль Telegram, ждём %s c.", exc.retry_after)
        await asyncio.sleep(exc.retry_after + 1)
        try:
            await bot.send_message(chat_id, text, reply_markup=keyboard)
            return True
        except TelegramAPIError as exc2:
            log.warning("Не удалось отправить объявление: %s", exc2)
            return False
    except TelegramAPIError as exc:
        # Например: пользователь не начал диалог с ботом или заблокировал его
        log.warning("Не удалось отправить объявление: %s", exc)
        return False


# ---------------------------------------------------------------------------
#  Основной проход парсинга
# ---------------------------------------------------------------------------
async def run_parsing(bot: Bot, target_chat_id: int) -> int:
    """
    Один полный проход парсинга. Объявления отправляются в target_chat_id
    (личка или группа). Возвращает количество новых отправленных объявлений.
    Защищён блокировкой от одновременного запуска.
    """
    if _lock.locked():
        log.info("Парсинг уже выполняется — пропускаю повторный запуск.")
        return 0

    async with _lock:
        started = datetime.now()
        log.info("=== Старт парсинга ===")

        keywords = await db.get_keywords()
        parsers = [p for p in get_parsers() if p.enabled]

        # Опрашиваем все сайты ПАРАЛЛЕЛЬНО. safe_fetch не бросает исключений.
        results = await asyncio.gather(
            *(p.safe_fetch(keywords) for p in parsers)
        )

        # Обновляем статистику по каждому сайту
        LAST_RUN_STATS.clear()
        new_count = 0

        for parser, ads in zip(parsers, results):
            LAST_RUN_STATS[parser.name] = len(ads)

            for ad in ads:
                # 1) фильтр по ключевым словам
                if not keyword_match(ad, keywords):
                    continue
                # 2) защита от дублей
                if await db.is_seen(ad.uid):
                    continue
                # 3) отправляем; помечаем «увиденным» только при успешной доставке,
                #    чтобы при неудаче объявление пришло в следующий цикл
                sent = await _send_ad(bot, target_chat_id, ad)
                if sent:
                    await db.mark_seen(ad.uid, ad.source, ad.title, ad.url, ad.price)
                    new_count += 1
                    # небольшая пауза между отправками, чтобы не ловить флуд-контроль
                    await asyncio.sleep(random.uniform(0.4, 0.9))

        await db.set_last_parse(started)
        elapsed = (datetime.now() - started).total_seconds()
        log.info("=== Парсинг завершён: %d новых за %.1f c ===", new_count, elapsed)
        return new_count


# ---------------------------------------------------------------------------
#  Настройка планировщика
# ---------------------------------------------------------------------------
def setup_scheduler(bot: Bot, target_chat_id: int) -> AsyncIOScheduler:
    """
    Настраивает APScheduler на автозапуск парсинга.

    target_chat_id — куда слать найденные объявления (личка или группа).
    Базовый интервал — PARSE_INTERVAL_MIN минут, плюс случайный «джиттер»
    до (MAX-MIN) минут, чтобы запуски были не строго по таймеру.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    jitter_seconds = max(0, (PARSE_INTERVAL_MAX - PARSE_INTERVAL_MIN) * 60)

    scheduler.add_job(
        run_parsing,
        trigger=IntervalTrigger(minutes=PARSE_INTERVAL_MIN, jitter=jitter_seconds),
        args=[bot, target_chat_id],
        id="parse_job",
        max_instances=1,      # не запускать параллельно самих себя
        coalesce=True,        # если пропустили запуск — не копить очередь
        replace_existing=True,
    )
    log.info(
        "Планировщик: интервал ~%d–%d мин.",
        PARSE_INTERVAL_MIN, PARSE_INTERVAL_MAX,
    )
    return scheduler
