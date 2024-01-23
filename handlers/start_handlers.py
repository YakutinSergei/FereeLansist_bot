from datetime import timedelta, datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from bot_menu.menu import create_inline_kb, menu_performer, menu_customer, my_order
from create_bot import bot
from database.orm import bd_get_user_status, bd_add_performer, get_user_profile, bd_add_customer, \
    get_user_profile_customer, bd_get_order, get_order_info
from lexicon.lex_ru import lx_common_phrases, LEXICON_RU

router: Router = Router()

#FSM на выбор исполнителя
class FSMperformer_add(StatesGroup):
    name = State()
    specialization = State()

#FSM для заказчика
class FSMcustomer_add(StatesGroup):
    name = State()

#Команда старт
@router.message(CommandStart())
@router.message(F.text == LEXICON_RU['profile'])
async def process_start_command(message: Message):
    # Проверяем есть ли такой пользователь
    # 0 - нет 1 - исполнитель 2 - заказчик
    user_status = await bd_get_user_status(tg_id=message.from_user.id)
    if user_status == 0:
        await message.answer(text=lx_common_phrases['start_text'],
                             reply_markup=await create_inline_kb(1,
                                                                 'chRole_',
                                                                  LEXICON_RU['performer'],
                                                                   LEXICON_RU['customer']
                                                                   ))
    elif user_status == 1:
        user = await get_user_profile(tg_id=message.from_user.id)
        txt_profile = (f"<b><i>🌟ПРОФИЛЬ🌟</i></b>\n\n"
                       f"<b>Имя и фамилия</b>: {user[0]['name']}\n"
                       f"<b>Специализация</b>: {user[0]['specialization']}\n"
                       f"<b>Всего выполнено заказов</b>: {user[1]['count']}\n"
                       f"<b>Рейтинг</b>: {user[0]['rating']}\n"
                       f"<b>Статус</b>: {user[0]['status']}\n")

        await message.answer(text=txt_profile, reply_markup=await create_inline_kb(1,
                                                                                    'changeStatus',
                                                                                    LEXICON_RU[
                                                                                        'change_status']))
    else:
        user = await get_user_profile_customer(tg_id=message.from_user.id)
        txt_profile = (f"<b><i>🌟ПРОФИЛЬ🌟</i></b>\n\n"
                       f"<b>Имя и фамилия</b>: {user['customer_name']}\n"
                       f"<b>Активных заказов</b>: {user['active_orders_count']}\n"
                       f"<b>Всего создано заказов</b>: {user['completed_orders_count']}\n")

        await message.answer(text=txt_profile, reply_markup=menu_customer.as_markup(resize_keyboard=True))


#Отмена создания
@router.callback_query(F.data.startswith('cancel_'))
async def process_specializations_name(callback: CallbackQuery, state: FSMContext):
    user_status = await bd_get_user_status(tg_id=callback.from_user.id)
    if user_status == 0:
        await callback.message.answer(text=lx_common_phrases['cancel_choice'])
        await state.clear()
        await callback.answer()
    else:
        await callback.answer(text='‼️Вы уже зарегистрированы в приложении‼️', show_alert=True)


#Выбор кем является пользователь
@router.callback_query(F.data.startswith('chRole_'))
async def process_choice_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split('_')[1]
    user_status = await bd_get_user_status(tg_id=callback.from_user.id)
    if user_status == 0:
        if role == LEXICON_RU['performer']: # Если выбрал роль исполнителя
            await callback.message.answer(text=lx_common_phrases['enter_name'],
                                          reply_markup=await create_inline_kb(1,
                                                                            'cancel_',
                                                                            LEXICON_RU['cancel']))
            await state.set_state(FSMperformer_add.name)

        elif role == LEXICON_RU['customer']: # Если выбрал роль заказчика
            await callback.message.answer(text=lx_common_phrases['enter_name'],
                                          reply_markup=await create_inline_kb(1,
                                                                              'cancel_',
                                                                              LEXICON_RU['cancel']))
            await state.set_state(FSMcustomer_add.name)

    else:
        await callback.answer(text='‼️Вы уже зарегистрированы в приложении‼️', show_alert=True)

    await callback.answer()


# Ввод имени и фамилии ИСПОЛНИТЕЛЯ
@router.message(StateFilter(FSMperformer_add.name))
async def process_executor_name(message: Message, state: FSMContext):
    user_status = await bd_get_user_status(tg_id=message.from_user.id)

    if user_status == 0:
        await state.update_data(name=message.text)
        await message.answer(text=lx_common_phrases['choice_specializations'],
                             reply_markup=await create_inline_kb(1,
                                                                 'chSpec_',
                                                                 LEXICON_RU['porter'],
                                                                 LEXICON_RU['electrician'],
                                                                 LEXICON_RU['plumber'],
                                                                 LEXICON_RU['it-professional']
                                                                 ))
        await state.set_state(FSMperformer_add.specialization)
    else:
        await message.answer(text='‼️Вы уже зарегистрированы в приложении ‼️', show_alert=True)

# Ввод имени и фамилии Заказчика
@router.message(StateFilter(FSMcustomer_add.name))
async def process_customer_name(message: Message, state: FSMContext):
    user_status = await bd_get_user_status(tg_id=message.from_user.id)
    if user_status == 0:
        name = message.text
        await bd_add_customer(message.from_user.id, name)  # Добавляем в базу данных заказчика
        await state.clear()
        txt_profile = (f"<b><i>🌟ПРОФИЛЬ🌟</i></b>\n\n"
                       f"<b>Имя и фамилия</b>: {name}\n"
                       f"<b>Активных заказов</b>: 0\n"
                       f"<b>Всего создано заказов</b>: 0\n")
        await message.answer(text=lx_common_phrases['creating_profile'],
                             reply_markup=menu_customer.as_markup(resize_keyboard=True))

        await message.answer(text=txt_profile)



# Выбор специализации
@router.callback_query(StateFilter(FSMperformer_add.specialization))
async def process_specializations_name(callback: CallbackQuery, state: FSMContext):
    user_status = await bd_get_user_status(tg_id=callback.from_user.id)
    if user_status == 0:

        specialization = callback.data.split('_')[1] # Специализация

        '''Если нажата кнопка отмена'''
        if specialization == LEXICON_RU['cancel']:
            await callback.message.answer(text=lx_common_phrases['cancel_choice'])
            await state.clear()
        else:
            await state.update_data(specialization=specialization) # Обновляем FSM
            performer = await state.get_data() # Записывыем данные из FSM
            await bd_add_performer(callback.from_user.id, performer) # Добавляем в базу данных исполнителя
            await state.clear()
            txt_profile = (f"<b><i>🌟ПРОФИЛЬ🌟</i></b>\n\n"
                           f"<b>Имя и фамилия</b>: {performer['name']}\n"
                           f"<b>Специализация</b>: {specialization}\n"
                           f"<b>Всего выполнено заказов</b>: 0\n"
                           f"<b>Рейтинг</b>: 50\n"
                           f"<b>Статус</b>: 🔍В поиске работы")

            await callback.message.answer(text=lx_common_phrases['creating_profile'], reply_markup=menu_performer.as_markup(resize_keyboard=True))
            await callback.message.answer(text=txt_profile, reply_markup= await create_inline_kb(1,
                                                                                                 'changeStatus',
                                                                                                 LEXICON_RU['change_status']))
    else:
        await callback.answer(text='‼️Вы уже зарегистрированы в приложении‼️', show_alert=True)

    await callback.answer()



# Кнопка мои заказы
@router.message(F.text == LEXICON_RU['my_orders'])
async def process_my_order(message: Message):
    print('nen')
# Проверяем есть ли такой пользователь
    # 0 - нет 1 - исполнитель 2 - заказчик
    user_status = await bd_get_user_status(tg_id=message.from_user.id)
    if user_status == 1:
        pass
    elif user_status == 2:
        customer_order = await bd_get_order(tg_id=message.from_user.id)
        await message.answer(text=lx_common_phrases['my_order'],
                             reply_markup=await my_order(N=0,
                                                          role='customerOrder',
                                                          orders=customer_order
                                                          ))

'''Листание моих заказов'''
@router.callback_query(F.data.startswith('myOrder_'))
async def paging_order(callback: CallbackQuery):
    user_status = await bd_get_user_status(tg_id=callback.from_user.id)
    if user_status == 1:
        pass
    elif user_status == 2:
        action = callback.data.split('_')[-1]
        #Если нажата кнопка вперед
        if action == 'forward':
            N = int(callback.data.split('_')[1])
            customer_order = await bd_get_order(tg_id=callback.from_user.id)
            if N < len(customer_order):
                await callback.message.edit_reply_markup(reply_markup=await my_order(N=N,
                                                                                     role='customerOrder',
                                                                                     orders=customer_order
                                                                                     ))
        elif action == 'backward':
            N = int(callback.data.split('_')[1])
            customer_order = await bd_get_order(tg_id=callback.from_user.id)
            if N - 8 > 0:
                if N < 16:
                    N = N - 15
                else:
                    N = (((N) // 8) * 8) - 16
                await callback.message.edit_reply_markup(reply_markup=await my_order(N=N,
                                                                                     role='customerOrder',
                                                                                     orders=customer_order
                                                                                     ))
    await callback.answer()

'''Информация о заказе, заказчик'''
@router.callback_query(F.data.startswith('customerOrder'))
async def info_order_customer(callback: CallbackQuery):
    id_order = int(callback.data.split('_')[-1])
    order = await get_order_info(id_order)
    print(order)
    print(order['date_of_creation'])
    if (datetime.now() - (order['date_of_creation'] + timedelta(hours=3))) > timedelta(hours=3):
        status = lx_common_phrases['my_order_activ']
    else:
        status = lx_common_phrases['status_order_search']

    text = (f"<b>Номер заказа:</b> {id_order}\n"
            f"<b>📍Место:</b> {order['place']}\n"
            f"<b>📆Дата и время</b>: {order['date_completion']} г. {order['time_completion']}\n"
            f"<b>💰Цена</b>: {order['price']}\n"
            f"<b>📝Описание работ</b>: {order['description']}\n"
            f"<b>🔢Количество рабочих</b>: {order['num_of_performers']}\n\n"
            f"<b>Статус заказа</b>: {status}")
    await callback.message.answer(text=text, reply_markup=await create_inline_kb(1,
                                                                                f'stOrder_{id_order}_',
                                                                                 LEXICON_RU['сompleted'],
                                                                                 LEXICON_RU['cancel']
                                  ))
    await callback.answer()


'''Отмена выполнения задания'''



'''Кнопка заказ выполнен'''
