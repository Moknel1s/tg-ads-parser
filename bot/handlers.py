"""
Обработчики команд бота.

Команды:
  /start        — запуск и краткая инструкция
  /status       — статус (активные сайты, последний парсинг, новых за сегодня)
  /keywords     — показать текущие ключевые слова
  /add_keyword  — добавить ключевое слово
  /del_keyword  — удалить ключевое слово
  /parse_now    — принудительно запустить парсинг прямо сейчас
  /sites        — список подключённых сайтов и их статус
"""
from __future__ import annotations

import html
import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from config import TARGET_CHAT_ID
from database import db
from parsers import get_parsers
from scheduler.jobs import LAST_RUN_STATS, SOURCE_TITLES, run_parsing

log = logging.getLogger(__name__)

# Роутер, в который собраны все обработчики. Подключается в main.py.
router = Router(name="commands")


# ---------------------------------------------------------------------------
#  /start
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "👋 <b>Привет! Я слежу за объявлениями, где ищут исполнителя.</b>\n\n"
        "Я регулярно проверяю сайты (Avito, YouDo, FL.ru, Kwork, HH.ru) и, "
        "как только нахожу новое подходящее объявление, сразу присылаю его сюда.\n\n"
        "<b>Команды:</b>\n"
        "/status — что сейчас происходит\n"
        "/sites — список сайтов и их статус\n"
        "/keywords — мои ключевые слова\n"
        "/add_keyword &lt;слово&gt; — добавить ключевое слово\n"
        "/del_keyword &lt;слово&gt; — удалить ключевое слово\n"
        "/parse_now — проверить прямо сейчас\n\n"
        "🔎 Парсинг запускается автоматически каждые несколько минут."
    )
    await message.answer(text)


# ---------------------------------------------------------------------------
#  /status
# ---------------------------------------------------------------------------
@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    parsers = get_parsers()
    active = [p for p in parsers if p.enabled]

    last_parse = await db.get_last_parse()
    last_parse_str = last_parse.replace("T", " ") if last_parse else "ещё не запускался"

    today = await db.count_today()
    keywords = await db.get_keywords()

    text = (
        "📊 <b>Статус</b>\n\n"
        f"🌐 Активных сайтов: <b>{len(active)}</b> из {len(parsers)}\n"
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
    await message.answer(f"🔑 <b>Ключевые слова ({len(keywords)}):</b>\n{items}")


# ---------------------------------------------------------------------------
#  /add_keyword <слово>
# ---------------------------------------------------------------------------
@router.message(Command("add_keyword"))
async def cmd_add_keyword(message: Message, command: CommandObject) -> None:
    word = (command.args or "").strip()
    if not word:
        await message.answer(
            "Укажите слово или фразу после команды.\n"
            "Пример: <code>/add_keyword нужен сайт</code>"
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
            "Пример: <code>/del_keyword нужен сайт</code>"
        )
        return

    deleted = await db.del_keyword(word)
    if deleted:
        await message.answer(f"🗑 Удалил ключевое слово: <b>{html.escape(word)}</b>")
    else:
        await message.answer(f"❓ Такого слова нет: <b>{html.escape(word)}</b>")


# ---------------------------------------------------------------------------
#  /parse_now
# ---------------------------------------------------------------------------
@router.message(Command("parse_now"))
async def cmd_parse_now(message: Message) -> None:
    await message.answer("🔄 Запускаю проверку сайтов прямо сейчас…")

    # Куда слать результаты: в целевой чат из .env, иначе — туда, откуда команда
    target = TARGET_CHAT_ID or message.chat.id
    new_count = await run_parsing(message.bot, target)

    await message.answer(f"✅ Готово. Новых объявлений: <b>{new_count}</b>")


# ---------------------------------------------------------------------------
#  /sites
# ---------------------------------------------------------------------------
@router.message(Command("sites"))
async def cmd_sites(message: Message) -> None:
    parsers = get_parsers()
    lines = ["🌐 <b>Подключённые сайты:</b>", ""]

    for p in parsers:
        status = "🟢 вкл" if p.enabled else "⚪️ выкл"
        title = SOURCE_TITLES.get(p.name, p.title)

        # Результат последнего прогона (если был)
        last = LAST_RUN_STATS.get(p.name)
        if last == "error":
            extra = " — ⚠️ ошибка в прошлый раз"
        elif isinstance(last, int):
            extra = f" — получено {last} в прошлый раз"
        else:
            extra = ""

        lines.append(f"{status} — <b>{html.escape(title)}</b>{extra}")

    await message.answer("\n".join(lines))
