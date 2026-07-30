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
