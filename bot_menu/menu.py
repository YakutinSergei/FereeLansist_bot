import calendar
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import datetime

from lexicon.lex_ru import LEXICON_RU, PAGE, lx_common_phrases

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


'''Клавиатура на выбор даты заказа'''


async def kb_date_order(order_datetime):
    # Получаем текущую дату и время
    current_datetime = datetime.strptime(order_datetime, "%Y-%m-%d")

    # Получаем текущий год, месяц и число
    current_year = current_datetime.year
    current_month = get_month_name(current_datetime.month)
    current_day = current_datetime.day
    # Инициализируем билдер
    inline_markup: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=str(current_day),
        callback_data=f'current_day'
    ), InlineKeyboardButton(
        text=str(current_month),
        callback_data=f'current_month'
    ), InlineKeyboardButton(
        text=str(current_year),
        callback_data=f'current_year'
    )
    ]
    inline_markup.row(*buttons, width=3)

    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['resume'],
        callback_data=f'goTimeOrder'
    ), InlineKeyboardButton(
        text=LEXICON_RU['cancel'],
        callback_data=f'ordCancel_'
    )
    ]
    inline_markup.row(*buttons, width=1)
    return inline_markup.as_markup()


'''Клавиатура на выбор дня заказа'''


async def kb_day_order(index_day: int, count_day_month: int):
    end_month = 7 - ((index_day + count_day_month + 1) % 7)
    # Инициализируем билдер
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []
    for i in range(1, index_day + count_day_month + 1 + end_month + 1):
        if i <= index_day or i > index_day + count_day_month:
            buttons.append(InlineKeyboardButton(
                text='.',
                callback_data='NoneDay'))
        else:
            buttons.append(InlineKeyboardButton(
                text=f'{i - index_day}',
                callback_data=f'checkDayOrder_{i - index_day}'))

    kb_builder.row(*buttons, width=7)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['back_date_order'],
        callback_data='backDateOrder')
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Клавиатура для выбора месяца заказа'''


async def kb_month_order():
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []
    months = {
        1: 'Янв',
        2: 'Фев',
        3: 'Мар',
        4: 'Апр',
        5: 'Май',
        6: 'Июн',
        7: 'Июл',
        8: 'Авг',
        9: 'Сен',
        10: 'Окт',
        11: 'Ноя',
        12: 'Дек'
    }

    for i in range(1, len(months) + 1):
        buttons.append(InlineKeyboardButton(
            text=f'{months[i]}',
            callback_data=f'checkMonthOrder_{i}'))

    kb_builder.row(*buttons, width=3)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['back_date_order'],
        callback_data='backDateOrder')
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Клавиатура на выбор года заказа'''


async def kb_year_order():
    year_order = datetime.now().year
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    for i in range(year_order, year_order + 3):
        buttons.append(InlineKeyboardButton(
            text=f'{i}',
            callback_data=f'checkYearOrder_{i}'))

    kb_builder.row(*buttons, width=3)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['back_date_order'],
        callback_data='backDateOrder')
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Клавиатура время заказа'''


async def kb_check_time(time_order: str):
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Добавляем ноль если часы или минуты меньше 10
    if int(time_order.split(':')[0]) < 10:
        hours = '0' + time_order.split(':')[0]
    else:
        hours = time_order.split(':')[0]

    if int(time_order.split(':')[1]) < 10:
        minutes = '0' + time_order.split(':')[1]
    else:
        minutes = time_order.split(':')[1]
    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=hours,
        callback_data=f"checkTimeOrder_hour"
    ), InlineKeyboardButton(
        text=":",
        callback_data=f"checkTimeOrder"
    ), InlineKeyboardButton(
        text=minutes,
        callback_data=f"checkTimeOrder_minutes"
    )
    ]

    kb_builder.row(*buttons, width=3)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['resume'],
        callback_data=f'goSpecializationOrder'
    ), InlineKeyboardButton(
        text=LEXICON_RU['cancel'],
        callback_data=f'ordCancel_'
    )
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Выбор час выполнения заказы'''


async def kb_check_hours():
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for i in range(1, 25):
        buttons.append(InlineKeyboardButton(
            text=f'{i}',
            callback_data=f'checkHouseOrder_{i}'))

    kb_builder.row(*buttons, width=6)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['back_date_order'],
        callback_data='backTimeOrder')
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Выбор минуты выполнения заказы'''


async def kb_check_minut():
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for i in range(0, 60):
        buttons.append(InlineKeyboardButton(
            text=f'{i}',
            callback_data=f'checkMinutesOrder_{i}'))

    kb_builder.row(*buttons, width=6)

    buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
        text=LEXICON_RU['back_date_order'],
        callback_data='backTimeOrder')
    ]
    kb_builder.row(*buttons, width=1)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()

'''Клавиатура на мои заказы'''
async def my_order(N:int, role, orders):
    names = []
    if N % 8 == 0:
        pg = (N + 8) // 8
    else:
        pg = ((N + 8) // 8) + 1

    if len(orders) % 8 == 0:
        pg_max = len(orders) // 8
    else:
        pg_max = len(orders) // 8 + 1

    if N + 8 < len(orders):
        N_max = N + 8
    else:
        N_max = len(orders)

    for i in range(N, N_max):
        names.append(f"{orders[i]['id_order']}")

    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for name in names:
        kb_builder.row(InlineKeyboardButton(
            text=f'Заказ № {name}',
            callback_data=f'{role}_{name}'))

    kb_builder.row(InlineKeyboardButton(
        text=PAGE['backward'],
        callback_data=f'myOrder_{N_max}_backward'),
        InlineKeyboardButton(
            text=f'{pg}/{pg_max}',
            callback_data=f'myOrder_{N_max}_count'),
        InlineKeyboardButton(
            text=PAGE['forward'],
            callback_data=f'myOrder_{N_max}_forward'),
        width=3)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Клавиатура на поиск заказов'''

async def order(N:int, role, orders):
    names = []
    if N % 8 == 0:
        pg = (N + 8) // 8
    else:
        pg = ((N + 8) // 8) + 1

    if len(orders) % 8 == 0:
        pg_max = len(orders) // 8
    else:
        pg_max = len(orders) // 8 + 1

    if N + 8 < len(orders):
        N_max = N + 8
    else:
        N_max = len(orders)

    for i in range(N, N_max):
        names.append(f"{orders[i]['id_order']}")

    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    for name in names:
        kb_builder.row(InlineKeyboardButton(
            text=f'Заказ № {name}',
            callback_data=f'{role}_{name}'))

    kb_builder.row(InlineKeyboardButton(
        text=PAGE['backward'],
        callback_data=f'OrderSearch_{N_max}_backward'),
        InlineKeyboardButton(
            text=f'{pg}/{pg_max}',
            callback_data=f'OrderSearchCount'),
        InlineKeyboardButton(
            text=PAGE['forward'],
            callback_data=f'OrderSearch_{N_max}_forward'),
        width=3)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


'''Клавиатура на оценку исполнителей после выполненного заказа'''
async def kb_user_score(users_order, id_order):
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    for user in users_order:
        print(user)
        buttons: list[InlineKeyboardButton] = [InlineKeyboardButton(
            text=lx_common_phrases['downgrade_the_rating'],
            callback_data=f'estimation_-5_{user["id_user"]}_{id_order}'
        ), InlineKeyboardButton(
            text=user["name"],
            callback_data='None'
        ), InlineKeyboardButton(
            text=lx_common_phrases['increase_the_rating'],
            callback_data=f'estimation_5_{user["id_user"]}_{id_order}'
        )
        ]

    kb_builder.row(*buttons, width=3)

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


# Наименование номера месяца
def get_month_name(month_number):
    months = {
        1: 'Янв',
        2: 'Фев',
        3: 'Мар',
        4: 'Апр',
        5: 'Май',
        6: 'Июн',
        7: 'Июл',
        8: 'Авг',
        9: 'Сен',
        10: 'Окт',
        11: 'Ноя',
        12: 'Дек'
    }
    return months.get(month_number, 'Некорректный номер месяца')
