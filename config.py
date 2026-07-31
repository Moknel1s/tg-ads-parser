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
def env_bool(name: str, default: bool = True) -> bool:
    """Читает булеву переменную окружения (1/true/yes/on -> True)."""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on", "y"}


# Короткий псевдоним для обратной совместимости
_get_bool = env_bool


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


def _get_int_list(name: str, default: list[int]) -> list[int]:
    """
    Читает список целых чисел из переменной окружения.
    Разделители — запятая или точка с запятой. Пустое значение → default.
    Пример: ADMIN_IDS=1107340556, 222333444
    """
    raw = os.getenv(name)
    if not raw:
        return default
    result: list[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result or default


# ---------------------------------------------------------------------------
#  Telegram
# ---------------------------------------------------------------------------
# Токен бота (обязательно, берётся у @BotFather)
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Старая переменная ADMIN_ID оставлена для обратной совместимости:
# если новые переменные ниже не заданы — используются её значения.
_LEGACY_ADMIN_ID: int = _get_int("ADMIN_ID", 0)

# Куда бот присылает найденные объявления.
# Может быть вашим личным ID ИЛИ ID группы/канала (у групп он отрицательный).
TARGET_CHAT_ID: int = _get_int("TARGET_CHAT_ID", _LEGACY_ADMIN_ID)

# Кто может управлять ботом (командами). Список личных ID через запятую.
ADMIN_IDS: list[int] = _get_int_list(
    "ADMIN_IDS", [_LEGACY_ADMIN_ID] if _LEGACY_ADMIN_ID else []
)


# ---------------------------------------------------------------------------
#  Парсинг
# ---------------------------------------------------------------------------
PARSE_INTERVAL_MIN: int = _get_int("PARSE_INTERVAL_MIN", 7)
PARSE_INTERVAL_MAX: int = _get_int("PARSE_INTERVAL_MAX", 10)
MAX_ADS_PER_SITE: int = _get_int("MAX_ADS_PER_SITE", 30)
REQUEST_DELAY_MIN: float = _get_float("REQUEST_DELAY_MIN", 1.0)
REQUEST_DELAY_MAX: float = _get_float("REQUEST_DELAY_MAX", 3.0)


# ---------------------------------------------------------------------------
#  База данных
# ---------------------------------------------------------------------------
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "ads.db"))


# ---------------------------------------------------------------------------
#  Страны и их флаги
#  Включение/выключение целой страны: COUNTRY_RU=0 в .env
# ---------------------------------------------------------------------------
COUNTRIES: dict[str, dict[str, str]] = {
    "ru": {"flag": "🇷🇺", "name": "Россия"},
    "uz": {"flag": "🇺🇿", "name": "Узбекистан"},
    "us": {"flag": "🇺🇸", "name": "США"},
    "gb": {"flag": "🇬🇧", "name": "Великобритания"},
    "au": {"flag": "🇦🇺", "name": "Австралия"},
}

COUNTRIES_ENABLED: dict[str, bool] = {
    code: env_bool(f"COUNTRY_{code.upper()}", True) for code in COUNTRIES
}


def country_flag(code: str) -> str:
    """Возвращает флаг страны по её коду (или глобус, если код неизвестен)."""
    return COUNTRIES.get(code, {}).get("flag", "🌐")


def country_name(code: str) -> str:
    """Возвращает название страны по её коду."""
    return COUNTRIES.get(code, {}).get("name", code)


# ---------------------------------------------------------------------------
#  Ключевые слова услуг Loomis (список по умолчанию).
#  Засеваются в БД при первом запуске и при повышении KEYWORDS_VERSION.
#  Дальше управляются командами /add_keyword и /del_keyword.
#
#  Ищем ТОЛЬКО услуги Loomis.uz: разработка сайтов/веб-приложений,
#  CRM/ERP/SaaS, ИИ-решения, Telegram-боты для бизнеса, интеграции,
#  автоматизация, digital-продукты под ключ.
# ---------------------------------------------------------------------------
KEYWORDS_VERSION = "loomis-2"

DEFAULT_KEYWORDS: list[str] = [
    # ---- Русский ----
    "сайт", "веб-сайт", "web-сайт",  # широкие корни (ловят «корпоративного сайта» и т.п.)
    "нужен сайт", "сделать сайт", "разработать сайт", "разработка сайта",
    "создать сайт", "создание сайта", "заказать сайт", "сайт под ключ",
    "корпоративный сайт", "сайт для бизнеса",
    "ищу веб-разработчика", "веб-разработчик", "веб разработчик",
    "нужен разработчик", "нужен программист",
    "нужен лендинг", "лендинг", "landing page",
    "интернет-магазин", "интернет магазин", "онлайн-магазин", "онлайн магазин",
    "веб-приложение", "веб приложение", "веб-сервис",
    "нужна crm", "crm-систем", "срм",
    "нужна erp", "erp-систем",
    "saas",
    "телеграм-бот", "телеграм бот", "telegram бот", "telegram-бот",
    "тг-бот", "тг бот", "чат-бот", "чатбот", "бот-ассистент",
    "бот для бизнеса", "бот для автоматизации", "бот для",
    "автоматизация бизнес", "автоматизация процесс", "автоматизировать",
    "интеграц",  # интеграция / интеграции / интегрировать
    "искусственный интеллект", "нейросет", "ии-решени", "gpt-бот", "чат-gpt",
    "цифровой продукт", "digital-продукт", "портал",
    # ---- English ----
    "web development", "website development", "need a website",
    "build a website", "looking for web developer", "web developer needed",
    "hire a developer", "need a developer",
    "web app", "web application",
    "need crm", "need erp", "saas product",
    "telegram bot", "chatbot", "ai solution", "ai-powered",
    "artificial intelligence", "machine learning",
    "business automation", "api integration", "system integration",
    "ecommerce", "e-commerce", "online store",
    # ---- Oʻzbekcha (узбекский) ----
    "sayt kerak", "web sayt", "web sayt yaratish", "sayt yaratish",
    "dasturchi kerak", "dastur kerak", "bot kerak",
    "onlayn dokon", "onlayn do'kon", "ilova kerak", "avtomatlashtirish",
    "crm kerak",
]


# ---------------------------------------------------------------------------
#  Стоп-слова: если объявление про это — НЕ берём.
#  Но если в тексте есть явный признак разработки (см. DEV_INDICATORS),
#  стоп-слово игнорируется (т.е. «логотип + сайт» — берём).
# ---------------------------------------------------------------------------
STOP_KEYWORDS: list[str] = [
    "логотип", "лого ", "фирменный стиль", "брендбук",
    "копирайт", "рерайт", "написание текст", "контент-менеджер",
    "smm", "таргет", "ведение инстаграм", "ведение соцсет", "ведение групп",
    "seo-продвижение", "поисковое продвижение", "сео продвижение",
    "ремонт", "сантехник", "электрик", "курьер", "доставка еды",
    "грузчик", "уборка", "клининг", "репетитор", "массаж", "маникюр",
    "баннер", "полиграфи", "визитк",
    "logo design", "copywriting", "content writing", "social media",
    "data entry", "virtual assistant", "translation",
]

# ЖЁСТКИЕ стоп-слова: исключают ВСЕГДА (даже если рядом «сайт»/разработка).
# Это чисто маркетинговые услуги (SEO/SMM/реклама/раскрутка) — не разработка.
HARD_STOP_KEYWORDS: list[str] = [
    "seo", "сео", "smm", "смм",
    "продвижение сайт", "продвижения сайт", "продвижению сайт",
    "раскрутк", "таргетолог", "таргетинг",
    "контекстная реклама", "настройка рекламы", "настройку рекламы",
    "яндекс директ", "google ads", "маркетолог",
]

# Признаки того, что речь всё-таки про разработку — перебивают обычные стоп-слова.
DEV_INDICATORS: list[str] = [
    "сайт", "лендинг", "landing", "веб", "web", "приложени", "app",
    "crm", "erp", "saas", "интеграц", "integration",
    "автоматизац", "automation", "разработ", "develop",
    "portal", "портал", "gpt", "нейросет", "интеллект",
    "dastur", "sayt", "ilova", "бот", "bot",
]


# ---------------------------------------------------------------------------
#  Определение НАМЕРЕНИЯ объявления.
#  Нам нужны только те, где ЗАКАЗЧИК ИЩЕТ исполнителя (запрос).
#  Объявления, где автор САМ ПРЕДЛАГАЕТ услугу (конкурент/фрилансер) — отсекаем.
#
#  Логика: если есть признак «предложения» и при этом НЕТ признака «запроса» —
#  считаем это рекламой услуги и пропускаем.
# ---------------------------------------------------------------------------
# Признаки того, что ищут исполнителя (это нам нужно):
WANT_INDICATORS: list[str] = [
    # ---- Русский ----
    "нужен", "нужна", "нужно", "нужны", "нужен исполнитель",
    "ищу", "ищем", "ищет", "ищется", "в поиске", "в поисках",
    "требуется", "требуются", "разыскивается",
    "закажу", "хочу заказать", "нужно заказать",
    "кто сделает", "кто сможет", "кто может сделать", "кто возьмется",
    "ищу подрядчика", "ищу специалиста", "ищу разработчика", "ищу команду",
    "ищу фрилансера", "нужен фрилансер", "нужен подрядчик", "помогите сделать",
    "посоветуйте", "подскажите кто",
    # ---- English ----
    "need", "needed", "looking for", "hiring", "wanted", "seeking",
    "want to hire", "we need", "i need", "in search of", "require a",
    "who can build", "who can make", "anyone who can",
    # ---- Oʻzbekcha ----
    "kerak", "kerakli", "izlayapman", "izlaymiz", "qidiryapman",
]

# Признаки того, что автор САМ предлагает услугу (это отсекаем):
OFFER_INDICATORS: list[str] = [
    # ---- Русский ----
    "предлагаю", "предлагаем", "предложу",
    "делаю", "делаем", "выполню", "выполним", "выполняю", "выполняем",
    "создам", "создадим", "создаю", "создаём", "создаем",
    "разработаю", "разработаем", "напишу", "напишем",
    "сверстаю", "сверстаем", "оказываю", "оказываем", "предоставляю", "предоставляем",
    "наша компания", "наша студия", "веб-студия", "веб студия", "web-студия",
    "портфолио", "мои услуги", "наши услуги", "мои работы", "наши работы",
    "услуги по разработке", "услуги веб", "услуги программиста",
    "обращайтесь", "обращайтесь к нам", "закажите", "закажите у нас",
    "гарантия", "недорого", "по низким ценам", "цена от", "стоимость от",
    "работаю с", "работаем с", "опыт", "стаж", "качественно и в срок",
    "быстро и качественно", "любой сложности", "профессиональн", "прайс",
    "расценк", "заказы принимаю", "лет на рынке",
    # ---- English ----
    "i offer", "we offer", "i will build", "i will create", "i will make",
    "i will develop", "i can build", "i can create", "i can make",
    "i can develop", "my services", "our services", "for hire", "hire me",
    "portfolio", "affordable", "we provide", "we build", "we develop",
    "years of experience", "professional web",
    # ---- Oʻzbekcha ----
    "yarataman", "yaratamiz", "qilaman", "qilamiz", "xizmatlar",
    "xizmatlarini taklif", "tajribali", "arzon",
]


# ---------------------------------------------------------------------------
#  Пул User-Agent'ов для ротации
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
    if not TARGET_CHAT_ID:
        errors.append("TARGET_CHAT_ID не задан в .env (куда слать объявления)")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS не задан в .env (кто управляет ботом)")
    return errors
