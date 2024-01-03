from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from lexicon.lex_ru import LEXICON_RU

'''генератор клавиатур'''
async def create_inline_kb(width: int,
                     pref: str,
                     *args: str,
                     **kwargs: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    # Заполняем список кнопками из аргументов args и kwargs
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=LEXICON_RU[button] if button in LEXICON_RU else button,
                callback_data=pref + button))

    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=pref + button))

    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=width)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()

'''Обычная клавиатура на исполнителя'''
menu_performer: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

btn_row_1: list[KeyboardButton] = [KeyboardButton(text=LEXICON_RU['profile']),
                                   KeyboardButton(text=LEXICON_RU['my_orders'])
                                   ]
btn_row_2: list[KeyboardButton] = [KeyboardButton(text=LEXICON_RU['search_orders'])]

menu_performer.row(*btn_row_1, width=2).row(*btn_row_2, width=1)

'''Обычная клавиатура на заказчика'''
menu_customer: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

btn_row_1: list[KeyboardButton] = [KeyboardButton(text=LEXICON_RU['profile']),
                                   KeyboardButton(text=LEXICON_RU['my_orders'])
                                   ]
btn_row_2: list[KeyboardButton] = [KeyboardButton(text=LEXICON_RU['add_order'])]

menu_customer.row(*btn_row_1, width=2).row(*btn_row_2, width=1)