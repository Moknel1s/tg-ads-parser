# 🤖 Loomis Ads Parser — бот-охотник за заказами на разработку

Telegram-бот, который следит за досками объявлений и фриланс-биржами в
**5 странах** (🇷🇺 🇺🇿 🇺🇸 🇬🇧 🇦🇺) и присылает **только заказы под услуги
Loomis.uz**: разработка сайтов, веб-приложений, CRM/ERP, SaaS, ИИ-решения,
Telegram-боты для бизнеса, интеграции и автоматизация. Как только находит
новое подходящее объявление — сразу шлёт его в личку или в общий чат с флагом
страны источника.

---

## ✨ Возможности

- ⏱ Автоматический парсинг каждые **7–10 минут**, все сайты — **параллельно**.
- 🎯 Фильтр **строго по услугам Loomis** (ключевые слова RU/EN/UZ) + стоп-лист,
  который отсекает дизайн логотипов, SMM, SEO без разработки, курьеров и т.п.
- 🌍 Объявления с **5 стран**, у каждого сообщения — **флаг страны**.
- 🗄 **Дедупликация** по ссылке (SQLite) — одно объявление не приходит дважды.
- 🧩 **Расширяемая архитектура** — новый сайт добавляется одним классом.
- 🔌 Можно включать/выключать **целые страны** и **отдельные сайты** из `.env`.
- 🛡 Устойчивость к ошибкам: упавший сайт не роняет бота.
- 🔐 Управляют ботом только разрешённые пользователи (`ADMIN_IDS`).
- 🛠 Сообщение «Бот на техобслуживании» при штатной остановке.

---

## 📁 Структура проекта

```
tg_ads_parser/
├── bot/
│   ├── handlers.py       # команды (/start, /sites, /countries, ...)
│   ├── keyboards.py       # кнопка «Открыть объявление»
│   └── middlewares.py     # доступ только для ADMIN_IDS
├── parsers/
│   ├── __init__.py        # РЕЕСТР сайтов (добавление новых — здесь)
│   ├── base.py            # Ad, BaseParser, ConfigurableHTMLParser, RSS-хелпер
│   ├── hh.py kwork.py flru.py youdo.py avito.py   # 🇷🇺 отдельные парсеры
│   ├── ru_extra.py        # 🇷🇺 Freelance.ru, Weblancer, Habr, Workzilla, Профи, Workspace
│   ├── uz.py              # 🇺🇿 OLX.uz, Dowork, UZITHUB, Giglancer, Worklance, EDC, InfoShop
│   ├── us.py              # 🇺🇸 Reddit, Craigslist + глобальные (Upwork, Fiverr, ...)
│   ├── gb.py              # 🇬🇧 PeoplePerHour, Bark, Gumtree, YunoJuno
│   └── au.py              # 🇦🇺 Airtasker, SEEK, Indeed
├── database/db.py         # SQLite: увиденные объявления, ключевые слова, meta
├── scheduler/jobs.py      # ядро парсинга + фильтр + расписание
├── config.py              # настройки, страны, ключевые слова, стоп-слова
├── main.py                # точка входа
├── .env.example  requirements.txt  start.bat  README.md
```

---

## 🚀 Установка

Нужен **Python 3.11+**.

```bash
cd tg_ads_parser
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium   # нужно для динамических сайтов (Avito, Upwork и т.п.)
```

---

## ⚙️ Настройка

```bash
copy .env.example .env    # Windows   (cp — на Linux/macOS)
```

Заполните в `.env` как минимум:

```env
BOT_TOKEN=123456789:AAE...ваш_токен
TARGET_CHAT_ID=123456789   # куда слать (личный ID или ID группы, отрицательный)
ADMIN_IDS=123456789        # кто управляет ботом (личные ID через запятую)
```

Токен — у [@BotFather](https://t.me/BotFather), личный ID — у [@userinfobot](https://t.me/userinfobot).
Если шлёте в группу — добавьте бота в неё; если в личку — нажмите боту `/start`.

**Включить/выключить страну или сайт:**
```env
COUNTRY_AU=0     # выключить всю Австралию
SITE_UPWORK=1    # включить Upwork (нужен вход/API)
SITE_KWORK=0     # выключить Kwork
```

---

## ▶️ Запуск

```bash
python main.py
```
Или дважды кликните **`start.bat`** (Windows). Остановка — **Ctrl + C**
(при этом бот отправит уведомление о техобслуживании).

---

## 💬 Команды

| Команда | Что делает |
|---|---|
| `/start` | Запуск и краткая инструкция |
| `/status` | Активные страны/сайты, последний парсинг, новых за сегодня |
| `/countries` | Список стран, их вкл/выкл и число активных сайтов |
| `/sites` | Все сайты по странам и их статус |
| `/keywords` | Ключевые слова услуг |
| `/add_keyword <слово>` | Добавить ключевое слово |
| `/del_keyword <слово>` | Удалить ключевое слово |
| `/parse_now` | Принудительный парсинг прямо сейчас |

---

## 📨 Пример сообщения

```
🇷🇺 Новое объявление

Источник: Kwork (биржа проектов)
Заголовок: Разработать корпоративный сайт + CRM
Краткое описание: Нужен сайт-каталог и интеграция с CRM.
Бюджет/цена: 50000 ₽
Ссылка: https://kwork.ru/projects/1/view
```
Плюс кнопка «🔗 Открыть объявление». Флаг слева = страна источника
(🇷🇺 🇺🇿 🇺🇸 🇬🇧 🇦🇺).

---

## 🔑 Ключевые слова услуг (по умолчанию)

Ищем **только** услуги Loomis. Список (RU + EN + UZ) засевается в БД при первом
запуске, дальше управляется командами `/add_keyword` и `/del_keyword`.

Примеры: `нужен сайт`, `разработка сайта`, `лендинг`, `интернет-магазин`,
`веб-приложение`, `нужна CRM`, `нужна ERP`, `saas`, `телеграм-бот`,
`автоматизация бизнес`, `интеграц`, `искусственный интеллект`, `нейросет`,
`web development`, `need a website`, `web app`, `ai solution`, `ecommerce`,
`sayt kerak`, `web sayt yaratish`, `dasturchi kerak`, `avtomatlashtirish` — и т.д.
(полный список — в `config.py`, переменная `DEFAULT_KEYWORDS`).

**Стоп-слова** (в `config.py`, `STOP_KEYWORDS`) отсекают не-разработку: логотипы,
копирайт, SMM, SEO без разработки, курьеров, ремонт и т.п. Если рядом есть явный
признак разработки (сайт/CRM/бот/интеграция…), стоп-слово игнорируется.

---

## 🌍 Какие сайты подключены (по факту)

Реальность парсинга: часть площадок отдают данные свободно, часть требует
авторизацию / API-ключи / прокси или имеет сильный антибот. Поэтому вторые
**по умолчанию выключены** — код готов, но нужно добавить ключи/прокси и
проверить селекторы, после чего включить их флагом `SITE_<КЛЮЧ>=1`.

| Страна | ✅ Включены по умолчанию | ⚪️ Выключены (нужны ключи/прокси/проверка) |
|---|---|---|
| 🇷🇺 | **Все 10 сайтов + HH**: FL.ru, Kwork, Freelance.ru, Workzilla, YouDo, Weblancer, Avito, Профи.ру, Workspace.ru, Habr/Фрилансим, HH.ru | — |
| 🇺🇿 | OLX.uz | Dowork, UZITHUB, Giglancer, Worklance, EDC.Sale, InfoShop |
| 🇺🇸 | Reddit (r/forhire…), Craigslist | Upwork, Fiverr, Freelancer.com, Guru, Thumbtack |
| 🇬🇧 | — | PeoplePerHour, Bark, Gumtree, YunoJuno |
| 🇦🇺 | — | Airtasker, SEEK, Indeed |

Заметки по России:
- **Стабильно работают**: Kwork, FL.ru, Freelance.ru (JSON/HTML), HH (API).
- **Через playwright** (нужен `playwright install chromium`): YouDo, Avito,
  Workzilla, Профи.ру, Workspace.ru. Без прокси/авторизации они часто отдают 0
  из-за антибота — это блокировка, а не ошибка; бот при этом не падает.
- **Habr Freelance закрыт** и переехал в **Фрилансим (freelansim.ru)** — парсим его.
- Selector-парсеры могут требовать правки селекторов при смене вёрстки — они
  вынесены в атрибуты классов (см. `parsers/ru_extra.py`).

Прочее:
- **Глобальные маркетплейсы** (Upwork, Fiverr, Freelancer.com) зарегистрированы
  один раз (в `us.py`) и покрывают в т.ч. GB/AU — чтобы не плодить дубли.
- **Telegram-каналы** как источник в этой версии не реализованы: для чтения
  каналов нужен userbot (Telethon/Pyrogram) с номером телефона — это отдельный
  модуль, могу добавить по запросу.
- Если сайт заблокирован по IP или сменил вёрстку — бот **не падает**, а
  пропускает его и пишет предупреждение в лог. Смотрите `/sites` — там видно,
  кто сколько отдал в последний раз.

---

## 🧩 Как добавить новый сайт

**1. Опишите сайт классом** в файле нужной страны (например `parsers/uz.py`).
Для типового сайта хватает нескольких CSS-селекторов:

```python
from .base import ConfigurableHTMLParser

class MySiteParser(ConfigurableHTMLParser):
    name = "mysite"            # уникальный ключ (для SITE_MYSITE и /sites)
    title = "Мой сайт"          # название для /sites
    country = "uz"              # код страны (должен быть в config.COUNTRIES)
    enabled_default = True      # включён ли по умолчанию

    BASE = "https://mysite.uz"
    LIST_URL = "https://mysite.uz/projects"
    USE_DYNAMIC = False         # True — если сайт рендерится через JS (playwright)
    CARD_SELECTOR = ".project-card"
    TITLE_SELECTOR = "a.title"
    PRICE_SELECTOR = ".budget"
    DESC_SELECTOR = ".desc"
```

Для нестандартных сайтов (JSON-API, RSS) наследуйтесь от `BaseParser` и
реализуйте `fetch()` — примеры: `parsers/hh.py` (API), `parsers/kwork.py`
(встроенный JSON), `parsers/us.py` (`RedditParser` — JSON, `CraigslistParser` — RSS).
В `BaseParser` уже есть готовые `_get_html`, `_get_json`, `_get_rss`,
`_get_html_dynamic`, `soup`.

**2. Зарегистрируйте класс** в `parsers/__init__.py` — импорт + добавить в `_ALL`.

Готово: расписание, фильтрация по услугам, флаг страны, дедуп и вкл/выкл
заработают автоматически.

## 🗺 Как добавить новую страну

1. Добавьте её в `config.COUNTRIES`:
   ```python
   COUNTRIES = {
       ...
       "de": {"flag": "🇩🇪", "name": "Германия"},
   }
   ```
2. У парсеров этой страны ставьте `country = "de"`.
3. (Опционально) `COUNTRY_DE=0` в `.env`, чтобы её выключать.

---

## 🛠 Частые проблемы

| Проблема | Решение |
|---|---|
| `BOT_TOKEN не задан` | Заполните `.env` |
| Бот молчит в личке | Нажмите боту `/start` |
| Бот молчит в группе | Добавьте бота в группу (`TARGET_CHAT_ID`) |
| Сайт отдаёт 0 / ошибку 403 | Блокировка по IP — нужен прокси/домашний IP; либо сменилась вёрстка (правьте селекторы в классе) |
| Слишком мало объявлений | Добавьте ключевые слова через `/add_keyword` или включите больше сайтов/стран |

---

## 📦 Зависимости

aiogram 3.x · aiohttp + beautifulsoup4 · playwright · aiosqlite · APScheduler ·
python-dotenv. Соблюдайте правила и условия использования парсимых сайтов.
