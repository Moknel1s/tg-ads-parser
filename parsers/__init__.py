"""
Реестр парсеров (по странам).

Как ДОБАВИТЬ НОВЫЙ САЙТ:
  1. Создайте класс-наследник ConfigurableHTMLParser (или BaseParser для
     нестандартных случаев) в файле нужной страны:
     parsers/ru_extra.py, parsers/uz.py, parsers/us.py, parsers/gb.py,
     parsers/au.py — или в отдельном файле.
     Обязательно задайте: name, title, country, enabled_default и селекторы.
  2. Импортируйте класс здесь и добавьте его в список _ALL.
Всё остальное (расписание, фильтрация, дедуп, флаги, вкл/выкл) заработает само.

Как ДОБАВИТЬ НОВУЮ СТРАНУ:
  1. Добавьте её в config.COUNTRIES (код + флаг + название).
  2. Проставляйте этот код в атрибуте country у парсеров этой страны.

Включение/выключение:
  * страна целиком:  COUNTRY_RU=0  в .env
  * отдельный сайт:  SITE_KWORK=0  (или SITE_UPWORK=1, чтобы включить)
"""
import config

from .avito import AvitoParser
from .au import AirtaskerParser, IndeedAuParser, SeekParser
from .base import Ad, BaseParser, ConfigurableHTMLParser
from .flru import FLruParser
from .gb import BarkParser, GumtreeUkParser, PeoplePerHourParser, YunoJunoParser
from .hh import HHParser
from .kwork import KworkParser
from .ru_extra import (
    FreelanceRuParser,
    HabrFreelanceParser,
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
from .us_remote import (
    ArcParser,
    CodeableParser,
    ContraParser,
    FlexJobsParser,
    GunIoParser,
    LinkedInParser,
    ToptalParser,
    WellfoundParser,
    WeWorkRemotelyParser,
)
from .uz import (
    BirBirParser,
    BisyorParser,
    DoworkUzParser,
    EdcSaleParser,
    FreelanceAdminParser,
    GiglancerParser,
    InfoShopUzParser,
    OlxUzParser,
    SalexyParser,
    TwoWorkParser,
    UzFreelanceParser,
    UzitHubParser,
    WorklanceParser,
)
from .youdo import YouDoParser

# Полный список классов парсеров, сгруппированный по странам.
_ALL: list[type[BaseParser]] = [
    # 🇷🇺 Россия
    HHParser, KworkParser, FLruParser, YouDoParser, AvitoParser,
    FreelanceRuParser, WeblancerParser, HabrFreelanceParser,
    WorkzillaParser, ProfiRuParser, WorkspaceParser,
    # 🇺🇿 Узбекистан
    OlxUzParser, BisyorParser, SalexyParser, DoworkUzParser, UzitHubParser,
    GiglancerParser, TwoWorkParser, BirBirParser, WorklanceParser,
    UzFreelanceParser, FreelanceAdminParser, EdcSaleParser, InfoShopUzParser,
    # 🇺🇸 США / глобальные маркетплейсы и удалённые job-борды
    RedditParser, CraigslistParser, WeWorkRemotelyParser,
    UpworkParser, FiverrParser, FreelancerComParser, GuruParser, ThumbtackParser,
    ArcParser, WellfoundParser, ContraParser, LinkedInParser,
    GunIoParser, CodeableParser, FlexJobsParser, ToptalParser,
    # 🇬🇧 Великобритания
    PeoplePerHourParser, BarkParser, GumtreeUkParser, YunoJunoParser,
    # 🇦🇺 Австралия
    AirtaskerParser, SeekParser, IndeedAuParser,
]


def _is_enabled(parser: BaseParser) -> bool:
    """
    Сайт активен, если ВКЛючена его страна И включён сам сайт.
    Страна: COUNTRY_<CODE> в .env (по умолчанию вкл).
    Сайт:   SITE_<NAME> в .env (по умолчанию — из enabled_default класса).
    """
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
    """
    Метаданные всех сайтов (без сетевых запросов): для команд /sites и /countries
    и для подписи источника в сообщениях.
    """
    result = []
    for cls in _ALL:
        result.append({
            "name": cls.name,
            "title": cls.title,
            "country": cls.country,
            "enabled": config.COUNTRIES_ENABLED.get(cls.country, True)
                       and config.env_bool(f"SITE_{cls.name.upper()}", cls.enabled_default),
        })
    return result


def site_titles() -> dict[str, str]:
    """Словарь {машинный ключ сайта: человекочитаемое название}."""
    return {cls.name: cls.title for cls in _ALL}


def site_require_want() -> dict[str, bool]:
    """
    Словарь {ключ сайта: требовать ли явный признак запроса}.
    True — для досок-классифайдов (OLX, Avito, bisyor…).
    """
    return {cls.name: getattr(cls, "require_want", False) for cls in _ALL}


__all__ = [
    "Ad", "BaseParser", "ConfigurableHTMLParser",
    "get_parsers", "all_sites", "site_titles", "site_require_want",
]
