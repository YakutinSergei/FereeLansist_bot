from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from datetime import datetime


from bot_menu.menu import create_inline_kb, menu_performer, menu_customer, kb_date_order
from database.orm import bd_get_user_status, bd_add_performer, get_user_profile, bd_add_customer, \
    get_user_profile_customer
from lexicon.lex_ru import lx_common_phrases, LEXICON_RU


router: Router = Router()


class FSMorder_add(StatesGroup):
    location = State()
    date_order = State()


#Отмена создания
@router.callback_query(F.data.startswith('ordCancel_'))
async def process_specializations_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text=lx_common_phrases['cancel_choice'])
    await state.clear()
    await callback.answer()


'''Создать заказ'''
@router.message(F.text == LEXICON_RU['add_order'])
async def process_add_order_location(message: Message, state: FSMContext):
    await message.answer(text=lx_common_phrases['date_order'], reply_markup=await kb_date_order())
    await state.set_state(FSMorder_add.date_order)
    current_datetime = str(datetime.now().date())
    await state.update_data(date_order=current_datetime)  # Обновляем FSM
    await state.set_state(FSMorder_add.location)



'''После ввода место проведения работ'''
@router.message(StateFilter(FSMorder_add.location))
async def process_add_order_location(message: Message, state: FSMContext):




     # await message.answer(text=lx_common_phrases['location'],
     #                         reply_markup=await create_inline_kb(1,
     #                                                           'ordCancel_',
     #                                                           LEXICON_RU['cancel']))
     # await state.set_state(FSMorder_add.location)