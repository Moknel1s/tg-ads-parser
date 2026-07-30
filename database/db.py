"""
Слой работы с базой данных (SQLite через aiosqlite).

Здесь хранятся:
  * seen_ads  — уже увиденные/отправленные объявления (защита от дублей);
  * keywords  — текущие ключевые слова;
  * meta      — служебные данные (например, время последнего парсинга).

Используется одно общее асинхронное соединение на всё приложение.
"""
import logging
from datetime import datetime

import aiosqlite

from config import DB_PATH, DEFAULT_KEYWORDS

log = logging.getLogger(__name__)

# Единое соединение с БД (открывается один раз в init_db)
_db: aiosqlite.Connection | None = None


async def init_db() -> None:
    """
    Открывает соединение, создаёт таблицы (если их ещё нет)
    и засевает ключевые слова по умолчанию при первом запуске.
    """
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row

    # Таблица увиденных объявлений. uid — хэш ссылки (первичный ключ = защита от дублей).
    await _db.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_ads (
            uid        TEXT PRIMARY KEY,
            source     TEXT,
            title      TEXT,
            url        TEXT,
            price      TEXT,
            created_at TEXT
        )
        """
    )
    # Таблица ключевых слов
    await _db.execute(
        "CREATE TABLE IF NOT EXISTS keywords (word TEXT PRIMARY KEY)"
    )
    # Служебная таблица «ключ-значение»
    await _db.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    await _db.commit()

    # Если ключевых слов ещё нет — засеваем значениями по умолчанию
    cur = await _db.execute("SELECT COUNT(*) AS c FROM keywords")
    row = await cur.fetchone()
    if row and row["c"] == 0:
        await _db.executemany(
            "INSERT OR IGNORE INTO keywords (word) VALUES (?)",
            [(w.lower().strip(),) for w in DEFAULT_KEYWORDS],
        )
        await _db.commit()
        log.info("Засеяно %d ключевых слов по умолчанию", len(DEFAULT_KEYWORDS))

    log.info("База данных готова: %s", DB_PATH)


async def close_db() -> None:
    """Закрывает соединение с БД (вызывается при остановке бота)."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def _conn() -> aiosqlite.Connection:
    """Возвращает соединение или бросает ошибку, если БД не инициализирована."""
    if _db is None:
        raise RuntimeError("База данных не инициализирована. Сначала вызовите init_db().")
    return _db


# ---------------------------------------------------------------------------
#  Работа с объявлениями (дедупликация)
# ---------------------------------------------------------------------------
async def is_seen(uid: str) -> bool:
    """Проверяет, отправляли ли мы уже объявление с таким uid."""
    cur = await _conn().execute("SELECT 1 FROM seen_ads WHERE uid = ?", (uid,))
    return await cur.fetchone() is not None


async def mark_seen(uid: str, source: str, title: str, url: str, price: str = "") -> None:
    """Помечает объявление как увиденное (сохраняет в БД)."""
    await _conn().execute(
        """
        INSERT OR IGNORE INTO seen_ads (uid, source, title, url, price, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (uid, source, title, url, price, datetime.now().isoformat(timespec="seconds")),
    )
    await _conn().commit()


async def count_today() -> int:
    """Сколько новых объявлений найдено сегодня (по локальной дате)."""
    cur = await _conn().execute(
        "SELECT COUNT(*) AS c FROM seen_ads "
        "WHERE date(created_at) = date('now', 'localtime')"
    )
    row = await cur.fetchone()
    return row["c"] if row else 0


# ---------------------------------------------------------------------------
#  Работа с ключевыми словами
# ---------------------------------------------------------------------------
async def get_keywords() -> list[str]:
    """Возвращает список всех ключевых слов (в нижнем регистре)."""
    cur = await _conn().execute("SELECT word FROM keywords ORDER BY word")
    rows = await cur.fetchall()
    return [r["word"] for r in rows]


async def add_keyword(word: str) -> bool:
    """
    Добавляет ключевое слово. Возвращает True, если добавлено,
    и False, если такое слово уже было.
    """
    word = word.lower().strip()
    if not word:
        return False
    cur = await _conn().execute("SELECT 1 FROM keywords WHERE word = ?", (word,))
    if await cur.fetchone() is not None:
        return False
    await _conn().execute("INSERT INTO keywords (word) VALUES (?)", (word,))
    await _conn().commit()
    return True


async def del_keyword(word: str) -> bool:
    """
    Удаляет ключевое слово. Возвращает True, если что-то удалили,
    и False, если такого слова не было.
    """
    word = word.lower().strip()
    cur = await _conn().execute("DELETE FROM keywords WHERE word = ?", (word,))
    await _conn().commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
#  Служебные данные (meta)
# ---------------------------------------------------------------------------
async def set_meta(key: str, value: str) -> None:
    """Сохраняет пару ключ-значение в таблицу meta."""
    await _conn().execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await _conn().commit()


async def get_meta(key: str) -> str | None:
    """Читает значение из таблицы meta (или None, если ключа нет)."""
    cur = await _conn().execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = await cur.fetchone()
    return row["value"] if row else None


async def set_last_parse(dt: datetime) -> None:
    """Запоминает время последнего успешного парсинга."""
    await set_meta("last_parse", dt.isoformat(timespec="seconds"))


async def get_last_parse() -> str | None:
    """Возвращает время последнего парсинга (строкой) или None."""
    return await get_meta("last_parse")
