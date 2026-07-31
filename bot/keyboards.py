"""
Клавиатуры (inline-кнопки) для сообщений бота.
"""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def ad_keyboard(url: str) -> InlineKeyboardMarkup:
    """
    Кнопка «Открыть объявление» под сообщением с найденным объявлением.
    Ведёт прямо на страницу объявления.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Открыть объявление", url=url)
    return builder.as_markup()


def actions_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки управления парсингом:
      • «Парсинг сейчас» — только новые объявления;
      • «Показать все» — все подходящие, даже уже отправленные.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Парсинг сейчас", callback_data="parse_now")
    builder.button(text="📋 Показать все (вкл. отправленные)", callback_data="parse_all")
    builder.adjust(1)  # по одной кнопке в ряд
    return builder.as_markup()
