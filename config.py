"""
Конфигурация проекта.

Читает переменные окружения из файла .env и хранит все настройки бота
в одном месте, чтобы их было удобно менять.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта (папка, где лежит этот файл)
BASE_DIR = Path(__file__).resolve().parent

# Загружаем переменные окружения из .env (если файл есть)
load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
#  Вспомогательные функции для чтения переменных окружения
# ---------------------------------------------------------------------------
def _get_bool(name: str, default: bool = True) -> bool:
    """Читает булеву переменную окружения (1/true/yes/on -> True)."""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on", "y"}


def _get_int(name: str, default: int) -> int:
    """Читает целочисленную переменную окружения с запасным значением."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    """Читает вещественную переменную окружения с запасным значением."""
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
#  Telegram
# ---------------------------------------------------------------------------
# Токен бота (обязательно, берётся у @BotFather)
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Ваш личный Telegram ID: сюда бот шлёт объявления и только вы можете им управлять
ADMIN_ID: int = _get_int("ADMIN_ID", 0)


# ---------------------------------------------------------------------------
#  Парсинг
# ---------------------------------------------------------------------------
# Интервал запуска парсинга (минуты). Реальный интервал — случайный в этом диапазоне.
PARSE_INTERVAL_MIN: int = _get_int("PARSE_INTERVAL_MIN", 7)
PARSE_INTERVAL_MAX: int = _get_int("PARSE_INTERVAL_MAX", 10)

# Сколько объявлений максимум брать с одного сайта за проход
MAX_ADS_PER_SITE: int = _get_int("MAX_ADS_PER_SITE", 30)

# Задержки между HTTP-запросами (секунды), чтобы не банили
REQUEST_DELAY_MIN: float = _get_float("REQUEST_DELAY_MIN", 1.0)
REQUEST_DELAY_MAX: float = _get_float("REQUEST_DELAY_MAX", 3.0)


# ---------------------------------------------------------------------------
#  База данных
# ---------------------------------------------------------------------------
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "ads.db"))


# ---------------------------------------------------------------------------
#  Включение/выключение отдельных сайтов
#  Любой сайт можно выключить через .env: SITE_AVITO=0
# ---------------------------------------------------------------------------
SITES_ENABLED: dict[str, bool] = {
    "avito": _get_bool("SITE_AVITO", True),
    "youdo": _get_bool("SITE_YOUDO", True),
    "flru": _get_bool("SITE_FLRU", True),
    "kwork": _get_bool("SITE_KWORK", True),
    "hh": _get_bool("SITE_HH", True),
}


# ---------------------------------------------------------------------------
#  Ключевые слова по умолчанию.
#  Засеваются в БД при самом первом запуске. Потом управляются командами
#  /add_keyword и /del_keyword и хранятся уже в базе.
# ---------------------------------------------------------------------------
DEFAULT_KEYWORDS: list[str] = [
    # Точные фразы «ищут исполнителя»
    "нужен сайт",
    "нужен лендинг",
    "ищу веб-разработчика",
    "разработать интернет-магазин",
    "разработка сайта",
    "создать сайт",
    "сделать сайт",
    "нужен программист",
    # Широкие корни-стеммы — ловят больше формулировок.
    # Для более строгого отбора любое из них можно удалить через /del_keyword.
    "сайт",
    "лендинг",
    "верстк",              # верстка / вёрстка / верстальщик
    "интернет-магазин",
    "интернет магазин",
    "веб-разраб",          # веб-разработчик / веб-разработка
    "верстальщик",
    "фронтенд",
    "телеграм-бот",
    "чат-бот",
]


# ---------------------------------------------------------------------------
#  Пул User-Agent'ов для ротации (чтобы запросы выглядели «человечнее»)
# ---------------------------------------------------------------------------
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]


def validate() -> list[str]:
    """
    Проверяет обязательные настройки. Возвращает список ошибок
    (пустой список = всё в порядке).
    """
    errors: list[str] = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN не задан в .env")
    if not ADMIN_ID:
        errors.append("ADMIN_ID не задан в .env")
    return errors
