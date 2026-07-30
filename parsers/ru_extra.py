"""
Дополнительные площадки России (кроме уже вынесенных в отдельные файлы
hh.py, kwork.py, flru.py, youdo.py, avito.py).

Все парсеры — на базе ConfigurableHTMLParser: сайт описывается набором
CSS-селекторов в атрибутах класса. Если сайт сменит вёрстку — поправьте
селекторы здесь.

enabled_default=False у сайтов, которым обычно нужны авторизация / прокси /
проверка селекторов. Их можно включить в .env (например SITE_WORKZILLA=1).
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class FreelanceRuParser(ConfigurableHTMLParser):
    name = "freelanceru"
    title = "Freelance.ru"
    country = "ru"
    enabled_default = True

    BASE = "https://freelance.ru"
    LIST_URL = "https://freelance.ru/project/search"
    CARD_SELECTOR = ".promo, .project, li.project, .fl-project"
    TITLE_SELECTOR = "a.title, h2 a, a[href*='/project/']"
    PRICE_SELECTOR = ".cost, .price, .amount"
    DESC_SELECTOR = ".text, .description, .desc"


class WeblancerParser(ConfigurableHTMLParser):
    name = "weblancer"
    title = "Weblancer"
    country = "ru"
    enabled_default = True

    BASE = "https://www.weblancer.net"
    LIST_URL = "https://www.weblancer.net/jobs/"
    CARD_SELECTOR = ".cols_table .row, .project_row, .row.cols_table_row"
    TITLE_SELECTOR = "a.text-melon, h2 a, a[href*='/jobs/']"
    PRICE_SELECTOR = ".amount, .price, .float-right .title"
    DESC_SELECTOR = ".text_field, .description, .text"


class HabrFreelanceParser(ConfigurableHTMLParser):
    name = "habr"
    title = "Habr Freelance"
    country = "ru"
    enabled_default = True

    BASE = "https://freelance.habr.com"
    LIST_URL = "https://freelance.habr.com/tasks"
    CARD_SELECTOR = "article.task, .task, li.task"
    TITLE_SELECTOR = "a.task__title, .task__title a, h2 a"
    PRICE_SELECTOR = ".task__finance, .count, .task__price"
    DESC_SELECTOR = ".task__description, .task__text"


class WorkzillaParser(ConfigurableHTMLParser):
    # Обычно требует авторизацию — по умолчанию выключен.
    name = "workzilla"
    title = "Workzilla"
    country = "ru"
    enabled_default = False

    BASE = "https://workzilla.com"
    LIST_URL = "https://workzilla.com/freelancer/tasks"
    USE_DYNAMIC = True
    CARD_SELECTOR = ".task-card, .task, [data-task]"
    TITLE_SELECTOR = "a.task-card__title, .task-title a, a[href*='/task/']"
    PRICE_SELECTOR = ".task-card__price, .price"
    DESC_SELECTOR = ".task-card__description, .task-description"


class ProfiRuParser(ConfigurableHTMLParser):
    # Сильный антибот/JS — по умолчанию выключен.
    name = "profiru"
    title = "Профи.ру"
    country = "ru"
    enabled_default = False

    BASE = "https://profi.ru"
    LIST_URL = "https://profi.ru/backoffice/n.php"  # раздел заказов (нужна проверка)
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-shmid], .order, .snippet"
    TITLE_SELECTOR = "a, .title"
    PRICE_SELECTOR = ".price, .cost"
    DESC_SELECTOR = ".description, .text"


class WorkspaceParser(ConfigurableHTMLParser):
    # Тендеры на digital — часто нужна авторизация. По умолчанию выключен.
    name = "workspace"
    title = "Workspace.ru (тендеры)"
    country = "ru"
    enabled_default = False

    BASE = "https://workspace.ru"
    LIST_URL = "https://workspace.ru/tenders/"
    CARD_SELECTOR = ".tender, .b-tender, .tenders-item"
    TITLE_SELECTOR = "a.tender__title, h3 a, a[href*='/tenders/']"
    PRICE_SELECTOR = ".tender__budget, .budget, .price"
    DESC_SELECTOR = ".tender__desc, .description"
