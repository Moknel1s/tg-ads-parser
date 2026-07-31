"""
Ядро парсинга и планировщик.

  * run_parsing()     — один полный проход: опросить сайты параллельно,
                        отфильтровать по услугам Loomis, отсеять дубли и
                        отправить новые объявления в целевой чат;
  * setup_scheduler() — автозапуск каждые PARSE_INTERVAL_MIN..MAX минут;
  * is_relevant()     — фильтр «только услуги Loomis»;
  * format_message()  — красивое сообщение с флагом страны;
  * LAST_RUN_STATS    — статистика последнего прогона (для /status, /sites).
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

import config
from bot.keyboards import ad_keyboard
from database import db
from parsers import Ad, get_parsers, site_require_want, site_titles

log = logging.getLogger(__name__)

# Блокировка, чтобы два парсинга не запускались одновременно.
_lock = asyncio.Lock()

# Статистика последнего прогона: имя сайта -> сколько объявлений получено.
LAST_RUN_STATS: dict[str, int] = {}

# Человекочитаемые названия источников (строится из реестра парсеров).
SOURCE_TITLES: dict[str, str] = site_titles()

# Для каких источников требуется явный признак запроса (доски-классифайды).
SOURCE_REQUIRE_WANT: dict[str, bool] = site_require_want()


# ---------------------------------------------------------------------------
#  Фильтрация «только услуги Loomis»
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Нижний регистр + ё→е для устойчивого поиска."""
    return text.lower().replace("ё", "е")


def is_relevant(ad: Ad, keywords: list[str]) -> bool:
    """
    True, если объявление — это ЗАПРОС на услугу Loomis (ищут исполнителя):
      1) содержит хотя бы одно сервисное ключевое слово;
      2) НЕ содержит стоп-слов (дизайн логотипов, SMM, SEO без разработки,
         курьеры…) — но если есть явный признак разработки, стоп-слово
         игнорируется;
      3) это НЕ реклама услуги: если есть признак «предложения» (создам, делаю,
         веб-студия, портфолио, недорого…) и при этом НЕТ признака «запроса»
         (нужен, ищу, требуется, need, looking for, kerak…) — отсекаем.
    """
    blob = _normalize(ad.text_blob())
    if not blob:
        return False

    # 1) должно быть хотя бы одно ключевое слово услуги
    if not any(_normalize(kw) in blob for kw in keywords):
        return False

    # 2a) жёсткие стоп-слова (SEO/SMM/реклама) — исключаем всегда
    if any(_normalize(h) in blob for h in config.HARD_STOP_KEYWORDS):
        return False

    # 2b) обычные стоп-слова исключают, если рядом нет признака разработки
    if any(_normalize(s) in blob for s in config.STOP_KEYWORDS):
        if not any(_normalize(d) in blob for d in config.DEV_INDICATORS):
            return False

    # 3) распознаём намерение
    has_want = any(_normalize(w) in blob for w in config.WANT_INDICATORS)
    has_offer = any(_normalize(o) in blob for o in config.OFFER_INDICATORS)  # сильные
    has_offer_weak = has_offer or any(
        _normalize(o) in blob for o in config.OFFER_WEAK_INDICATORS
    )

    if SOURCE_REQUIRE_WANT.get(ad.source, False):
        # Классифайды (OLX, Avito, Bisyor…): нужен ЯВНЫЙ запрос И никаких
        # сильных признаков предложения — даже если есть крючок «Нужен сайт?».
        if not has_want or has_offer:
            return False
    else:
        # Биржи задач (FL.ru, Kwork…): отсекаем явные предложения без запроса.
        if has_offer_weak and not has_want:
            return False

    return True


# ---------------------------------------------------------------------------
#  Форматирование и отправка сообщения
# ---------------------------------------------------------------------------
def format_message(ad: Ad) -> str:
    """
    Прежний (компактный) формат сообщения + флаг страны источника
    в начале заголовка.
    """
    flag = config.country_flag(ad.country)
    source = SOURCE_TITLES.get(ad.source, ad.source)
    title = html.escape(ad.title)

    lines = [f"{flag} 🆕 <b>{title}</b>", ""]

    if ad.description:
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
    Отправляет объявление с кнопкой «Открыть объявление».
    Возвращает True при успехе, False при ошибке (ошибки перехватываются,
    чтобы остановка/цикл не падали).
    """
    text = format_message(ad)
    keyboard = ad_keyboard(ad.url) if ad.url else None
    try:
        await bot.send_message(chat_id, text, reply_markup=keyboard)
        return True
    except TelegramRetryAfter as exc:
        log.warning("Флуд-контроль Telegram, ждём %s c.", exc.retry_after)
        await asyncio.sleep(exc.retry_after + 1)
        try:
            await bot.send_message(chat_id, text, reply_markup=keyboard)
            return True
        except TelegramAPIError as exc2:
            log.warning("Не удалось отправить объявление: %s", exc2)
            return False
    except TelegramAPIError as exc:
        log.warning("Не удалось отправить объявление: %s", exc)
        return False


# ---------------------------------------------------------------------------
#  Основной проход парсинга
# ---------------------------------------------------------------------------
async def run_parsing(bot: Bot, target_chat_id: int) -> int:
    """
    Один полный проход парсинга. Объявления идут в target_chat_id.
    Возвращает количество новых отправленных объявлений.
    """
    if _lock.locked():
        log.info("Парсинг уже выполняется — пропускаю повторный запуск.")
        return 0

    async with _lock:
        started = datetime.now()
        log.info("=== Старт парсинга ===")

        keywords = await db.get_keywords()
        parsers = [p for p in get_parsers() if p.enabled]

        # Опрашиваем все включённые сайты ПАРАЛЛЕЛЬНО.
        results = await asyncio.gather(*(p.safe_fetch(keywords) for p in parsers))

        LAST_RUN_STATS.clear()
        new_count = 0

        for parser, ads in zip(parsers, results):
            LAST_RUN_STATS[parser.name] = len(ads)

            for ad in ads:
                # 1) фильтр «только услуги Loomis»
                if not is_relevant(ad, keywords):
                    continue
                # 2) защита от дублей (по ссылке)
                if await db.is_seen(ad.uid):
                    continue
                # 3) отправляем; помечаем «увиденным» только при успешной доставке
                sent = await _send_ad(bot, target_chat_id, ad)
                if sent:
                    await db.mark_seen(ad.uid, ad.source, ad.title, ad.url, ad.price)
                    new_count += 1
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
    target_chat_id — куда слать найденные объявления.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    jitter_seconds = max(0, (config.PARSE_INTERVAL_MAX - config.PARSE_INTERVAL_MIN) * 60)

    scheduler.add_job(
        run_parsing,
        trigger=IntervalTrigger(minutes=config.PARSE_INTERVAL_MIN, jitter=jitter_seconds),
        args=[bot, target_chat_id],
        id="parse_job",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    log.info(
        "Планировщик: интервал ~%d–%d мин.",
        config.PARSE_INTERVAL_MIN, config.PARSE_INTERVAL_MAX,
    )
    return scheduler
