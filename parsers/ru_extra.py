"""
Дополнительные площадки России (кроме вынесенных в отдельные файлы
hh.py, kwork.py, flru.py, youdo.py, avito.py).

Все парсеры включены по умолчанию (enabled_default=True). Сайты с сильным
антиботом (Workzilla, Профи.ру, Workspace) работают через playwright и без
прокси/авторизации могут отдавать 0 — это блокировка по IP, а не ошибка кода.

Селекторы вынесены в атрибуты классов — правьте их здесь при смене вёрстки.
"""
from __future__ import annotations

from .base import ConfigurableHTMLParser


class FreelanceRuParser(ConfigurableHTMLParser):
    name = "freelanceru"
    title = "Freelance.ru"
    country = "ru"
    enabled_default = True

    BASE = "https://freelance.ru"
    # Лента заданий (селекторы проверены на живой странице)
    LIST_URL = "https://freelance.ru/task"
    CARD_SELECTOR = ".task-card"
    TITLE_SELECTOR = "a.task-card__title-link"
    LINK_SELECTOR = "a.task-card__title-link"
    PRICE_SELECTOR = ".task-card__price"  # без .task-badge (там «Видно всем»)
    DESC_SELECTOR = ".task-card__desc"


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
    # ВНИМАНИЕ: Habr Freelance закрыт и переехал в «Фрилансим» (freelansim.ru).
    # Парсим его. Если сайт недоступен — вернётся пусто (бот не падает).
    name = "habr"
    title = "Habr Freelance / Фрилансим"
    country = "ru"
    enabled_default = True

    BASE = "https://freelansim.ru"
    LIST_URL = "https://freelansim.ru/tasks"
    CARD_SELECTOR = ".task, .tasks__item, article.task, li.task"
    TITLE_SELECTOR = "a.task__title, .task__title a, h2 a, a[href*='/tasks/']"
    PRICE_SELECTOR = ".task__finance, .count, .task__price"
    DESC_SELECTOR = ".task__description, .task__text"


class WorkzillaParser(ConfigurableHTMLParser):
    name = "workzilla"
    title = "Workzilla"
    country = "ru"
    enabled_default = True

    BASE = "https://workzilla.com"
    LIST_URL = "https://workzilla.com/freelancer/tasks"
    USE_DYNAMIC = True  # рендерится через JS, часто требует вход
    CARD_SELECTOR = ".task-card, .task, [data-task]"
    TITLE_SELECTOR = "a.task-card__title, .task-title a, a[href*='/task/']"
    PRICE_SELECTOR = ".task-card__price, .price"
    DESC_SELECTOR = ".task-card__description, .task-description"


class ProfiRuParser(ConfigurableHTMLParser):
    name = "profiru"
    title = "Профи.ру"
    country = "ru"
    enabled_default = True

    BASE = "https://profi.ru"
    # Публичный каталог заказов у Профи.ру ограничен — без авторизации часто пусто.
    LIST_URL = "https://profi.ru/orders/"
    USE_DYNAMIC = True
    CARD_SELECTOR = "[data-shmid], .order, .snippet, article"
    TITLE_SELECTOR = "a, .title, h3"
    PRICE_SELECTOR = ".price, .cost"
    DESC_SELECTOR = ".description, .text"


class WorkspaceParser(ConfigurableHTMLParser):
    name = "workspace"
    title = "Workspace.ru (тендеры)"
    country = "ru"
    enabled_default = True

    BASE = "https://workspace.ru"
    LIST_URL = "https://workspace.ru/tenders/"
    USE_DYNAMIC = True  # антибот на статическом запросе (403) — пробуем через браузер
    CARD_SELECTOR = ".tender, .b-tender, .tenders-item, article"
    TITLE_SELECTOR = "a.tender__title, h3 a, a[href*='/tenders/']"
    PRICE_SELECTOR = ".tender__budget, .budget, .price"
    DESC_SELECTOR = ".tender__desc, .description"
