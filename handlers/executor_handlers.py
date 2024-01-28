import calendar

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from datetime import datetime



from bot_menu.menu import kb_date_order, kb_day_order, kb_month_order, \
    kb_year_order, kb_check_time, kb_check_hours, kb_check_minut, create_inline_kb
from create_bot import bot
from database.orm import bd_get_user_status, get_specializations_db, bd_post_order_user, bd_add_user_order
from lexicon.lex_ru import lx_common_phrases, LEXICON_RU


router: Router = Router()

#Реакция на новый заказ исполнителем
@router.callback_query(F.data.startswith('senOrder_'))
async def process_choice_order_executor(callback: CallbackQuery):
    if callback.data.split('_')[-1] == lx_common_phrases['reject_order']: # Если нажал отклонить
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
    else:
        # Добавляем
        id_order = int(callback.data.split('_')[1]) # ID заказа
        tg_id = callback.from_user.id
        await bd_add_user_order(tg_id=tg_id, id_order=id_order)
        await bot.edit_message_text(text=lx_common_phrases['choice_order'],
                                    chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id)