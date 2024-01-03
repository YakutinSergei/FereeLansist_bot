from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from bot_menu.menu import create_inline_kb, menu_performer, menu_customer
from database.orm import bd_get_user_status, bd_add_performer, get_user_profile, bd_add_customer, \
    get_user_profile_customer
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
                                                                 LEXICON_RU['it-professional'],
                                                                 LEXICON_RU['cleaner'],
                                                                 LEXICON_RU['cancel']
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



