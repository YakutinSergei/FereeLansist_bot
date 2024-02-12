import calendar
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta

from bot_menu.menu import kb_date_order, kb_day_order, kb_month_order, \
    kb_year_order, kb_check_time, kb_check_hours, kb_check_minut, create_inline_kb, my_order
from config_data import apsh
from create_bot import bot
from database.orm import bd_get_user_status, get_specializations_db, bd_post_order_user, get_orders_user, get_order_info
from lexicon.lex_ru import lx_common_phrases, LEXICON_RU


router: Router = Router()


class FSMorder_add(StatesGroup):
    location = State()
    date_order = State()
    time_order = State()
    specializations_order = State()
    count_workers_order = State()
    price_order = State()
    desc_order = State()


#Отмена создания
@router.callback_query(F.data.startswith('ordCancel_'))
async def process_specializations_name(callback: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id= callback.message.message_id)
    await callback.message.answer(text=lx_common_phrases['cancel_choice'])
    await state.clear()
    await callback.answer()


'''Создать заказ'''


@router.message(F.text == LEXICON_RU['add_order'])
async def process_add_order_location(message: Message, state: FSMContext):
    user_status = await bd_get_user_status(tg_id=message.from_user.id)
    if user_status == 2:
        current_datetime = str(datetime.now().date())
        await message.answer(text=lx_common_phrases['date_order'], reply_markup=await kb_date_order(current_datetime))
        await state.set_state(FSMorder_add.date_order)
        await state.update_data(date_order=current_datetime)  # Обновляем FSM


'''выбор даты'''


@router.callback_query(F.data.startswith('current_'))
async def process_date_order(callback: CallbackQuery, state: FSMContext):
    date_chance = callback.data.split('_')[1]
    performer = await state.get_data()  # Записывыем данные из FSM
    year_order = int(performer['date_order'].split('-')[0]) #Год который выбрал пользователь
    month_order = int(performer['date_order'].split('-')[1]) #Месяц который выбрал польтзователь
    # Выбор изменения числа
    if date_chance == 'day':
        first_day_of_month_weekday_index = calendar.monthrange(year_order, month_order)[0]# какой сейчас день недели
        count_day_month = calendar.monthrange(year_order, month_order)[1]#Количество дней в месяце
        await bot.edit_message_text(text=lx_common_phrases['check_day'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    reply_markup=await kb_day_order(first_day_of_month_weekday_index,
                                                                    count_day_month))
    elif date_chance == 'month':
        await bot.edit_message_text(text=lx_common_phrases['check_month'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    reply_markup=await kb_month_order())
    else:
        await bot.edit_message_text(text=lx_common_phrases['check_month'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    reply_markup=await kb_year_order())
    await callback.answer()


'''Запись нового числа'''


@router.callback_query(F.data.startswith('checkDayOrder_'))
async def process_day_choice(callback: CallbackQuery, state: FSMContext):
    day_order_new = callback.data.split('_')[-1] # День который выбрал пользователь
    performer = await state.get_data()  # Записывыем данные из FSM
    year_order = str(performer['date_order'].split('-')[0]) # Год
    month_order = str(performer['date_order'].split('-')[1]) # Месяц
    new_date_order = "-".join([year_order,
                               month_order,
                               day_order_new]) # Новая дата заказа

    await bot.edit_message_text(text=lx_common_phrases['date_order'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_date_order(new_date_order))
    await state.set_state(FSMorder_add.date_order)
    await state.update_data(date_order=new_date_order)  # Обновляем FSM

    await callback.answer()


'''Запись нового месяца'''


@router.callback_query(F.data.startswith('checkMonthOrder_'))
async def process_month_choice(callback: CallbackQuery, state: FSMContext):
    month_order_new = callback.data.split('_')[-1] #Месяц который выбрал пользователь
    performer = await state.get_data()  # Записывыем данные из FSM
    year_order = str(performer['date_order'].split('-')[0]) # Год
    day_order = str(performer['date_order'].split('-')[2]) # День

    '''Проверяем количество дней в месяце если текущий день больше чем количество дней в месяце ставим последний день месяца'''

    count_day_month = calendar.monthrange(int(year_order), int(month_order_new))[1]
    if count_day_month < int(day_order):
        day_order = str(count_day_month)
    new_date_order = "-".join([year_order,
                               month_order_new,
                               day_order]) # Новая дата заказа

    await bot.edit_message_text(text=lx_common_phrases['date_order'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_date_order(new_date_order))
    await state.update_data(date_order=new_date_order)  # Обновляем FSM

    await callback.answer()


'''Выбор года'''
@router.callback_query(F.data.startswith('checkYearOrder_'))
async def process_year_choice(callback: CallbackQuery, state: FSMContext):
    year_order_new = callback.data.split('_')[-1] # Год который выбрал пользователь
    performer = await state.get_data()  # Записывыем данные из FSM
    month_order = str(performer['date_order'].split('-')[1])  # Месяц
    day_order = str(performer['date_order'].split('-')[2])  # День

    count_day_month = calendar.monthrange(int(year_order_new), int(month_order))[1]
    if count_day_month < int(day_order):
        day_order = str(count_day_month)

    new_date_order = "-".join([year_order_new,
                               month_order,
                               day_order])  # Новая дата заказа

    await bot.edit_message_text(text=lx_common_phrases['check_year'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_date_order(new_date_order))
    await state.set_state(FSMorder_add.date_order)
    await state.update_data(date_order=new_date_order)  # Обновляем FSM

    await callback.answer()


'''Кнопка назад в выборе даты'''
@router.callback_query(F.data =='backDateOrder')
async def process_day_choice(callback: CallbackQuery, state: FSMContext):
    performer = await state.get_data()  # Записывыем данные из FSM
    current_datetime = performer['date_order']
    await bot.edit_message_text(text=lx_common_phrases['date_order'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_date_order(current_datetime))

    await callback.answer()




'''Выбор времени'''
@router.callback_query(F.data =='goTimeOrder')
async def process_time_choice(callback: CallbackQuery, state: FSMContext):
    current_time = datetime.now().time() # текущее время в формате 11:55:13.164810
    hour = str(current_time.hour)
    minutes = str(current_time.minute)
    time_order = ":".join([hour,
                           minutes])  # Время заказа
    await state.set_state(FSMorder_add.time_order)
    await state.update_data(time_order=time_order)  # Обновляем FSM
    await bot.edit_message_text(text=lx_common_phrases['check_time'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_check_time(time_order))

    await callback.answer()


@router.callback_query(F.data.startswith('checkTimeOrder_'))
async def process_date_order(callback: CallbackQuery, state: FSMContext):
    time_order = callback.data.split('_')[-1]
    if time_order == 'hour':
        await bot.edit_message_text(text=lx_common_phrases['check_hour'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    reply_markup=await kb_check_hours())
    else:
        await bot.edit_message_text(text=lx_common_phrases['check_minutes'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    reply_markup=await kb_check_minut())

    await callback.answer()


'''Кнопка назад в выборе времени'''


@router.callback_query(F.data =='backTimeOrder')
async def process_day_choice(callback: CallbackQuery, state: FSMContext):
    performer = await state.get_data()  # Записывыем данные из FSM
    time_order = performer['time_order']
    await bot.edit_message_text(text=lx_common_phrases['check_time'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_check_time(time_order))
    await callback.answer()



'''Выбор час '''
@router.callback_query(F.data.startswith('checkHouseOrder_'))
async def process_check_house_order(callback: CallbackQuery, state: FSMContext):
    performer = await state.get_data()  # Записывыем данные из FSM
    time_order = performer['time_order'] # Получаем время заказа
    minutes_order = time_order.split(':')[-1] # Получаем минуты заказа
    new_hour_order = callback.data.split('_')[-1] # Получаем новые часы заказа
    new_time_order = ":".join([new_hour_order,
                           minutes_order])  # Ноовое время заказа

    await bot.edit_message_text(text=lx_common_phrases['check_hour'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_check_time(new_time_order))

    await state.update_data(time_order=new_time_order)  # Обновляем FSM, записываем новое время заказа


'''Выбор минут '''


@router.callback_query(F.data.startswith('checkMinutesOrder_'))
async def process_check_house_order(callback: CallbackQuery, state: FSMContext):
    performer = await state.get_data()  # Записывыем данные из FSM
    time_order = performer['time_order']  # Получаем время заказа
    hours_order = time_order.split(':')[0]  # Получаем часы заказа
    new_minutes_order = callback.data.split('_')[-1]  # Получаем новые минуты заказа
    new_time_order = ":".join([hours_order,
                               new_minutes_order])  # Ноовое время заказа

    await bot.edit_message_text(text=lx_common_phrases['check_minutes'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await kb_check_time(new_time_order))

    await state.update_data(time_order=new_time_order)  # Обновляем FSM, записываем новое время заказа


'''Выбор специализации'''
@router.callback_query(F.data =='goSpecializationOrder')
async def process_specialization_choice(callback: CallbackQuery):
    specializations = await get_specializations_db() # Получаем все специализации с базы данных

    specializations_btns = [] # Создаем лист для кнопок

    for specialization in specializations: # Записываем все специализации в лист
        specializations_btns.append(specialization['name'])

    specializations_btns.append(LEXICON_RU['cancel'])
    await bot.edit_message_text(text=lx_common_phrases['check_specializations'],
                                chat_id=callback.from_user.id,
                                message_id=callback.message.message_id,
                                reply_markup=await create_inline_kb(1,
                                                                    'choiceSpec_',
                                                                    *specializations_btns))




'''Продолжить после выбора специализации'''
@router.callback_query(F.data.startswith('choiceSpec_'))
async def process_check_house_order(callback: CallbackQuery, state: FSMContext):
    specialization = callback.data.split('_')[-1]

    if specialization == LEXICON_RU['cancel']:
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
        await callback.message.answer(text=lx_common_phrases['cancel_choice'])
        await state.clear()
        await callback.answer()
    else:
        await state.set_state(FSMorder_add.specializations_order)
        await state.update_data(specializations_order=specialization)  # Обновляем FSM, записываем специализацию
        await callback.message.answer(text=lx_common_phrases['location'],
                                reply_markup=await create_inline_kb(1,
                                                                  'ordCancel_',
                                                                  LEXICON_RU['cancel']))
        await state.set_state(FSMorder_add.location)
    await callback.answer()




'''После ввода место проведения работ'''
@router.message(StateFilter(FSMorder_add.location))
async def process_add_order_location(message: Message, state: FSMContext):
    location_order = message.text.replace("'", "").replace(";", "")
    await state.update_data(location=location_order)  # Обновляем FSM, записываем специализацию

    await message.answer(text=lx_common_phrases['count_workers'],
                         reply_markup=await create_inline_kb(1,
                                                             'ordCancel_',
                                                             LEXICON_RU['cancel']))
    await state.set_state(FSMorder_add.count_workers_order)


'''Ввод количества рабочих'''
@router.message(StateFilter(FSMorder_add.count_workers_order))
async def process_add_order_location(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(count_workers_order=message.text)  # Обновляем FSM, записываем количество рабочих

        await message.answer(text=lx_common_phrases['price_order'],
                             reply_markup=await create_inline_kb(1,
                                                                 'ordCancel_',
                                                                 LEXICON_RU['cancel']))
        await state.set_state(FSMorder_add.price_order)
    else:
        await message.answer(text='Вы ввели не число, попробуйте еще раз')


'''Ввод суммы заказа'''
@router.message(StateFilter(FSMorder_add.price_order))
async def process_add_order_location(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(price_order=message.text)  # Обновляем FSM, записываем количество рабочих
        await message.answer(text=lx_common_phrases['desc_order'],
                             reply_markup=await create_inline_kb(1,
                                                                 'ordCancel_',
                                                                 LEXICON_RU['cancel']))
        await state.set_state(FSMorder_add.desc_order)
    else:
        await message.answer(text='Вы ввели не число, попробуйте еще раз')


'''Ввод описания заказа'''
@router.message(StateFilter(FSMorder_add.desc_order))
async def process_add_order_location(message: Message, state: FSMContext):
    if len(message.text) < 256:
        desc = message.text.replace("'", "").replace(";", "")
        await state.update_data(desc_order=desc)  # Обновляем FSM, записываем количество рабочих
        order = await state.get_data()  # Записывыем данные из FSM
        #Записываем данные в базу данных
        tg_id = message.from_user.id
        user_order = await bd_post_order_user(tg_id=tg_id, order=order)

        # Отправляем сообщение заказчику о том что заказ создан
        await message.answer(text=lx_common_phrases['order_create'])

        #Запускаем событие через 3 часа, передаем id_order
        scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
        scheduler.add_job(apsh.choice_of_performers, 'date', run_date=datetime.now() + timedelta(seconds=30),
                          args=(user_order[1]["id_order"],tg_id,))
        scheduler.start()

        if user_order[0]: # проверяем есть ли исполнители под эту спецификацию
            # Отправляем заказчика
            for user in user_order[0]:
                try:
                    await bot.send_message(chat_id=user['tg_id'],
                                           text=f"<b>Номер заказа:</b> {user_order[1]['id_order']}"
                                                f"<b>📍Место:</b> {order['location']}\n"
                                                f"<b>📆Дата и время</b>: {order['date_order']} г. {order['time_order']}\n"
                                                f"<b>💰Цена</b>: {order['price_order']}\n"
                                                f"<b>📝Описание работ</b>: {order['desc_order']}\n"
                                                f"<b>🔢Количество рабочих</b>: {order['count_workers_order']}\n",
                                           reply_markup=await create_inline_kb(2,
                                                                               f'senOrder_{user_order[1]["id_order"]}_',
                                                                               lx_common_phrases['accept_order'],
                                                                               lx_common_phrases['reject_order'])
                                           )
                except:
                    print(f"{user['tg_id']}: Заблокировал пользователя")
        await state.clear()
    else:
        await message.answer(text='Вы ввели слишком длинный текст, попробуйте еще раз')



'''Поиск заказов исполнителем'''
@router.message(F.text == LEXICON_RU['search_orders'])
async def search_orders_performer(message: Message):
    tg_id =int(message.from_user.id)
    orders_user = await get_orders_user(tg_id=tg_id) # получаем заказы по специализации исполнителя

    if orders_user:
        await message.answer(text=lx_common_phrases['my_order'],
                             reply_markup=await my_order(N=0,
                                                         role='OrderSearch',
                                                         orders=orders_user
                                                         ))

'''Листание и заказы в поиске'''
@router.callback_query(F.data.startswith('OrderSearch_'))
async def process_search_order(callback: CallbackQuery):
    action = callback.data.split('_')[-1]
    tg_id = callback.from_user.id

    if action == 'backward':# листание назад
        N = int(callback.data.split('_')[1])
        if N - 8 > 0:
            if N < 16:
                N = N - 15
            else:
                N = (((N) // 8) * 8) - 16
        orders_user = await get_orders_user(tg_id=tg_id)  # получаем заказы по специализации исполнителя

        await callback.message.edit_reply_markup(reply_markup=await my_order(N=N,
                                                                             role='OrderSearch',
                                                                             orders=orders_user
                                                                             ))
    elif action == 'forward': # листание вперед
        N = int(callback.data.split('_')[1])
        orders_user = await get_orders_user(tg_id=tg_id)  # получаем заказы по специализации исполнителя

        await callback.message.edit_reply_markup(reply_markup=await my_order(N=N,
                                                         role='OrderSearch',
                                                         orders=orders_user
                                                         ))
    elif action.isdigit(): # информация о заказе
        id_order = int(callback.data.split('_')[-1])
        order = await get_order_info(id_order)
        await callback.message.answer(text=f"<b>Номер заказа:</b> {id_order}"
                                                f"<b>📍Место:</b> {order['place']}\n"
                                                f"<b>📆Дата и время</b>: {order['date_completion']} г. {order['time_completion']}\n"
                                                f"<b>💰Цена</b>: {order['price']}\n"
                                                f"<b>📝Описание работ</b>: {order['description']}\n"
                                                f"<b>🔢Количество рабочих</b>: {order['num_of_performers']}\n",
                                           reply_markup=await create_inline_kb(2,
                                                                               f'senOrder_{id_order}_',
                                                                               lx_common_phrases['accept_order'],
                                                                               lx_common_phrases['reject_order']))
    await callback.answer()


