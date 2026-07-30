"""
Реестр парсеров.

Чтобы ДОБАВИТЬ НОВЫЙ САЙТ:
  1. Создайте файл parsers/mysite.py с классом-наследником BaseParser.
  2. Импортируйте его здесь и добавьте в словарь _ALL.
  3. (Опционально) добавьте флаг SITE_MYSITE в config.SITES_ENABLED и .env.
Всё остальное (расписание, дедупликация, отправка) заработает автоматически.
"""
from config import SITES_ENABLED

from .avito import AvitoParser
from .base import Ad, BaseParser
from .flru import FLruParser
from .hh import HHParser
from .kwork import KworkParser
from .youdo import YouDoParser

# Соответствие «ключ сайта → класс парсера».
# Ключ должен совпадать с ключом в config.SITES_ENABLED.
_ALL: dict[str, type[BaseParser]] = {
    "avito": AvitoParser,
    "youdo": YouDoParser,
    "flru": FLruParser,
    "kwork": KworkParser,
    "hh": HHParser,
}


def get_parsers() -> list[BaseParser]:
    """
    Создаёт по одному экземпляру каждого парсера и проставляет флаг enabled
    из конфига. Возвращает список всех парсеров (включая выключенные — их
    отфильтрует safe_fetch()).
    """
    parsers: list[BaseParser] = []
    for key, cls in _ALL.items():
        parser = cls()
        parser.enabled = SITES_ENABLED.get(key, True)
        parsers.append(parser)
    return parsers


__all__ = ["Ad", "BaseParser", "get_parsers"]
