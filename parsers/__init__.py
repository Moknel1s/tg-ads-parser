"""
Реестр парсеров (по странам).

Как ДОБАВИТЬ НОВЫЙ САЙТ:
  1. Создайте класс-наследник ConfigurableHTMLParser (или BaseParser) в файле
     нужной страны (ru_extra.py, uz.py, us.py, gb.py, au.py). Задайте:
     name, title, country, enabled_default и селекторы.
  2. Импортируйте класс здесь и добавьте в _ALL.
  3. (Опционально) укажите в SITE_NEEDS, что сайту нужно для работы:
     "proxy" — резидентный прокси нужной страны; "api" — вход/официальный API.

Как ДОБАВИТЬ СТРАНУ: добавьте её в config.COUNTRIES и ставьте country="код".

Включение/выключение:
  * страна целиком:  COUNTRY_RU=0  в .env
  * отдельный сайт:  SITE_KWORK=0  (или SITE_UPWORK=1)

Правило: сайты, которые нельзя спарсить в принципе (мёртвые домены, капча,
пейвол, vetted-сети без публичной доски, доски вакансий) здесь НЕ регистрируются.
"""
import config

from .au import AirtaskerParser, IndeedAuParser, SeekParser
from .avito import AvitoParser, AvitoVacanciesParser
from .base import Ad, BaseParser, ConfigurableHTMLParser
from .flru import FLruParser
from .gb import BarkParser, GumtreeUkParser, PeoplePerHourParser, YunoJunoParser
from .kwork import KworkParser
from .ru_extra import (
    FreelanceRuParser,
    FreelanceSpaceParser,
    ProfiRuParser,
    WeblancerParser,
    WorkspaceParser,
    WorkzillaParser,
)
from .us import (
    CraigslistParser,
    FiverrParser,
    FreelancerComParser,
    GuruParser,
    RedditParser,
    ThumbtackParser,
    UpworkParser,
)
from .uz import (
    BirBirParser,
    BisyorParser,
    DoworkUzParser,
    GiglancerParser,
    HHUzParser,
    OlxUzParser,
    OneGoodParser,
    OpenDealParser,
    SalexyParser,
    TwoWorkParser,
    UzitHubParser,
)
from .youdo import YouDoParser

# Полный список классов парсеров, сгруппированный по странам.
_ALL: list[type[BaseParser]] = [
    # 🇷🇺 Россия
    KworkParser, FLruParser, FreelanceRuParser, FreelanceSpaceParser,
    YouDoParser, AvitoParser, AvitoVacanciesParser, WeblancerParser,
    WorkzillaParser, ProfiRuParser, WorkspaceParser,
    # 🇺🇿 Узбекистан
    OlxUzParser, BisyorParser, SalexyParser, DoworkUzParser, UzitHubParser,
    GiglancerParser, TwoWorkParser, BirBirParser, OpenDealParser,
    OneGoodParser, HHUzParser,
    # 🇺🇸 США
    RedditParser, CraigslistParser, UpworkParser, FiverrParser,
    FreelancerComParser, GuruParser, ThumbtackParser,
    # 🇬🇧 Великобритания
    PeoplePerHourParser, BarkParser, GumtreeUkParser, YunoJunoParser,
    # 🇦🇺 Австралия
    AirtaskerParser, SeekParser, IndeedAuParser,
]

# Что нужно сайту для реальной работы (для пометки в /sites):
#   "proxy" — публичный, но нужен резидентный прокси нужной страны (антибот/гео)
#   "api"   — нужен вход/аккаунт или официальный API
#   (нет в словаре) — работает как есть, без прокси и входа
SITE_NEEDS: dict[str, str] = {
    # RU
    "youdo": "proxy", "avito": "proxy", "avitovac": "proxy", "weblancer": "proxy",
    "workspace": "proxy", "workzilla": "api", "profiru": "api",
    # UZ (все — антибот/гео)
    "olxuz": "proxy", "bisyor": "proxy", "salexy": "proxy", "dowork": "proxy",
    "uzithub": "proxy", "giglancer": "proxy", "2work": "proxy", "birbir": "proxy",
    "opendeal": "proxy", "1good": "proxy", "hhuz": "proxy",
    # US
    "reddit": "proxy", "craigslist": "proxy",
    "upwork": "api", "fiverr": "api", "freelancercom": "api", "guru": "api",
    "thumbtack": "api",
    # GB
    "peopleperhour": "api", "bark": "api", "gumtreeuk": "proxy", "yunojuno": "api",
    # AU
    "airtasker": "proxy", "seek": "api", "indeedau": "api",
}


def _is_enabled(parser: BaseParser) -> bool:
    """Сайт активен, если ВКЛючена его страна И включён сам сайт."""
    country_on = config.COUNTRIES_ENABLED.get(parser.country, True)
    site_on = config.env_bool(f"SITE_{parser.name.upper()}", parser.enabled_default)
    return country_on and site_on


def get_parsers() -> list[BaseParser]:
    """Создаёт по одному экземпляру каждого парсера с вычисленным enabled."""
    parsers: list[BaseParser] = []
    for cls in _ALL:
        parser = cls()
        parser.enabled = _is_enabled(parser)
        parsers.append(parser)
    return parsers


def all_sites() -> list[dict]:
    """Метаданные всех сайтов (без сетевых запросов): для /sites и /countries."""
    result = []
    for cls in _ALL:
        result.append({
            "name": cls.name,
            "title": cls.title,
            "country": cls.country,
            "needs": SITE_NEEDS.get(cls.name),   # None / "proxy" / "api"
            "enabled": config.COUNTRIES_ENABLED.get(cls.country, True)
                       and config.env_bool(f"SITE_{cls.name.upper()}", cls.enabled_default),
        })
    return result


def site_titles() -> dict[str, str]:
    """Словарь {машинный ключ сайта: человекочитаемое название}."""
    return {cls.name: cls.title for cls in _ALL}


def site_require_want() -> dict[str, bool]:
    """{ключ сайта: требовать ли явный признак запроса} — для досок-классифайдов."""
    return {cls.name: getattr(cls, "require_want", False) for cls in _ALL}


__all__ = [
    "Ad", "BaseParser", "ConfigurableHTMLParser",
    "get_parsers", "all_sites", "site_titles", "site_require_want",
]
