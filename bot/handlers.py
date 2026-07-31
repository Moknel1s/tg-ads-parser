"""
Обработчики команд бота.

  /start        — запуск и краткая инструкция
  /status       — статус (страны, сайты, последний парсинг, новых за сегодня)
  /keywords     — показать текущие ключевые слова услуг
  /add_keyword  — добавить ключевое слово
  /del_keyword  — удалить ключевое слово
  /parse_now    — принудительно запустить парсинг прямо сейчас
  /sites        — список сайтов по странам и их статус
  /countries    — список стран, их вкл/выкл и число активных сайтов
"""
from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

import config
from bot.keyboards import actions_keyboard
from config import TARGET_CHAT_ID
from database import db
from parsers import all_sites
from scheduler.jobs import FORCE_SEND_LIMIT, LAST_RUN_STATS, run_parsing

log = logging.getLogger(__name__)

router = Router(name="commands")


# ---------------------------------------------------------------------------
#  /start
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "👋 <b>Я ищу заказы под услуги Loomis.uz</b>\n\n"
        "Слежу за досками объявлений и фриланс-биржами в 🇷🇺 🇺🇿 🇺🇸 🇬🇧 🇦🇺 "
        "и присылаю только то, что связано с разработкой digital-продуктов: "
        "сайты, веб-приложения, CRM/ERP, SaaS, ИИ-решения, Telegram-боты, "
        "интеграции и автоматизация.\n\n"
        "<b>Команды:</b>\n"
        "/status — что сейчас происходит\n"
        "/countries — страны и их статус\n"
        "/sites — сайты по странам\n"
        "/keywords — ключевые слова услуг\n"
        "/add_keyword &lt;слово&gt; — добавить\n"
        "/del_keyword &lt;слово&gt; — удалить\n"
        "/parse_now — проверить прямо сейчас\n"
        "/parse_all — показать все подходящие (даже отправленные)\n\n"
        "🔎 Парсинг запускается автоматически каждые несколько минут."
    )
    await message.answer(text, reply_markup=actions_keyboard())


# ---------------------------------------------------------------------------
#  /status
# ---------------------------------------------------------------------------
@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    sites = all_sites()
    active_sites = [s for s in sites if s["enabled"]]
    active_countries = [c for c, on in config.COUNTRIES_ENABLED.items() if on]

    last_parse = await db.get_last_parse()
    last_parse_str = last_parse.replace("T", " ") if last_parse else "ещё не запускался"

    today = await db.count_today()
    keywords = await db.get_keywords()

    text = (
        "📊 <b>Статус</b>\n\n"
        f"🗺 Стран активно: <b>{len(active_countries)}</b> из {len(config.COUNTRIES)}\n"
        f"🌐 Сайтов активно: <b>{len(active_sites)}</b> из {len(sites)}\n"
        f"🕒 Последний парсинг: <b>{last_parse_str}</b>\n"
        f"🆕 Новых объявлений за сегодня: <b>{today}</b>\n"
        f"🔑 Ключевых слов: <b>{len(keywords)}</b>"
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
#  /keywords
# ---------------------------------------------------------------------------
@router.message(Command("keywords"))
async def cmd_keywords(message: Message) -> None:
    keywords = await db.get_keywords()
    if not keywords:
        await message.answer("Список ключевых слов пуст. Добавьте через /add_keyword")
        return
    items = "\n".join(f"• {html.escape(k)}" for k in keywords)
    # Ограничиваем длину, чтобы не превысить лимит Telegram (4096 символов)
    if len(items) > 3500:
        items = items[:3500] + "\n…"
    await message.answer(f"🔑 <b>Ключевые слова услуг ({len(keywords)}):</b>\n{items}")


# ---------------------------------------------------------------------------
#  /add_keyword <слово>
# ---------------------------------------------------------------------------
@router.message(Command("add_keyword"))
async def cmd_add_keyword(message: Message, command: CommandObject) -> None:
    word = (command.args or "").strip()
    if not word:
        await message.answer(
            "Укажите слово или фразу после команды.\n"
            "Пример: <code>/add_keyword нужна CRM</code>"
        )
        return
    added = await db.add_keyword(word)
    if added:
        await message.answer(f"✅ Добавил ключевое слово: <b>{html.escape(word)}</b>")
    else:
        await message.answer(f"ℹ️ Такое слово уже есть: <b>{html.escape(word)}</b>")


# ---------------------------------------------------------------------------
#  /del_keyword <слово>
# ---------------------------------------------------------------------------
@router.message(Command("del_keyword"))
async def cmd_del_keyword(message: Message, command: CommandObject) -> None:
    word = (command.args or "").strip()
    if not word:
        await message.answer(
            "Укажите слово, которое нужно удалить.\n"
            "Пример: <code>/del_keyword saas</code>"
        )
        return
    deleted = await db.del_keyword(word)
    if deleted:
        await message.answer(f"🗑 Удалил ключевое слово: <b>{html.escape(word)}</b>")
    else:
        await message.answer(f"❓ Такого слова нет: <b>{html.escape(word)}</b>")


# ---------------------------------------------------------------------------
#  /parse_now и /parse_all (+ кнопки)
# ---------------------------------------------------------------------------
async def _run_and_report(message: Message, force: bool) -> None:
    """
    Общий помощник: запускает парсинг и отчитывается о результате.
    force=True — «показать всё» (в т.ч. уже отправленные объявления).
    Служебные сообщения идут в тот чат, откуда вызвали; сами объявления —
    в TARGET_CHAT_ID.
    """
    if force:
        await message.answer(
            "📋 Собираю <b>все</b> подходящие объявления "
            "(в т.ч. уже отправленные)… Это может занять до минуты."
        )
    else:
        await message.answer("🔄 Запускаю проверку сайтов прямо сейчас…")

    target = TARGET_CHAT_ID or message.chat.id
    count = await run_parsing(message.bot, target, force=force)

    if force:
        note = f"\n<i>(показаны первые {FORCE_SEND_LIMIT} — лимит за один раз)</i>" \
            if count >= FORCE_SEND_LIMIT else ""
        await message.answer(
            f"✅ Готово. Отправлено объявлений: <b>{count}</b>{note}",
            reply_markup=actions_keyboard(),
        )
    else:
        await message.answer(
            f"✅ Готово. Новых объявлений: <b>{count}</b>",
            reply_markup=actions_keyboard(),
        )


@router.message(Command("parse_now"))
async def cmd_parse_now(message: Message) -> None:
    await _run_and_report(message, force=False)


@router.message(Command("parse_all"))
async def cmd_parse_all(message: Message) -> None:
    await _run_and_report(message, force=True)


@router.callback_query(F.data == "parse_now")
async def cb_parse_now(call: CallbackQuery) -> None:
    await call.answer("Запускаю…")
    if call.message:
        await _run_and_report(call.message, force=False)


@router.callback_query(F.data == "parse_all")
async def cb_parse_all(call: CallbackQuery) -> None:
    await call.answer("Собираю все объявления…")
    if call.message:
        await _run_and_report(call.message, force=True)


# ---------------------------------------------------------------------------
#  /sites — список сайтов, сгруппированный по странам
# ---------------------------------------------------------------------------
@router.message(Command("sites"))
async def cmd_sites(message: Message) -> None:
    sites = all_sites()
    by_country: dict[str, list[dict]] = {}
    for s in sites:
        by_country.setdefault(s["country"], []).append(s)

    lines = ["🌐 <b>Сайты по странам</b>", ""]
    for code, meta in config.COUNTRIES.items():
        group = by_country.get(code, [])
        if not group:
            continue
        country_on = config.COUNTRIES_ENABLED.get(code, True)
        suffix = "" if country_on else " — <i>страна выключена</i>"
        lines.append(f"{meta['flag']} <b>{meta['name']}</b>{suffix}")
        for s in group:
            status = "🟢" if s["enabled"] else "⚪️"
            last = LAST_RUN_STATS.get(s["name"])
            extra = f" · {last} шт." if isinstance(last, int) else ""
            lines.append(f"  {status} {html.escape(s['title'])}{extra}")
        lines.append("")

    lines.append("🟢 включён · ⚪️ выключен. Управление: <code>SITE_KWORK=0</code> в .env")
    await message.answer("\n".join(lines))


# ---------------------------------------------------------------------------
#  /countries — страны и их статус
# ---------------------------------------------------------------------------
@router.message(Command("countries"))
async def cmd_countries(message: Message) -> None:
    sites = all_sites()
    lines = ["🗺 <b>Страны</b>", ""]
    for code, meta in config.COUNTRIES.items():
        group = [s for s in sites if s["country"] == code]
        if not group:
            continue
        on = config.COUNTRIES_ENABLED.get(code, True)
        enabled_cnt = sum(1 for s in group if s["enabled"])
        mark = "🟢 вкл" if on else "⚪️ выкл"
        lines.append(
            f"{meta['flag']} <b>{meta['name']}</b> — {mark} · "
            f"активных сайтов {enabled_cnt}/{len(group)}"
        )

    lines.append("")
    lines.append(
        "Выключить страну: <code>COUNTRY_UZ=0</code> в .env. "
        "Отдельный сайт: <code>SITE_UPWORK=1</code>."
    )
    await message.answer("\n".join(lines))
