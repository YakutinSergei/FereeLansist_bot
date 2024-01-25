from datetime import datetime

import asyncpg

from environs import Env

from bot_menu.menu import create_inline_kb
from create_bot import bot
from lexicon.lex_ru import lx_common_phrases

env = Env()
env.read_env()


# Функция выбора исполнителей

async def choice_of_performers(id_order, tg_id):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))


        #Получаем всех исполнителей по заказу
        users_order = await conn.fetch(f'''SELECT p.id_user, p.number_workers, p.tg_id
                                                FROM performers p
                                                JOIN executors_orders eo ON p.id_user = eo.id_user
                                                WHERE eo.id_order = {id_order}
                                                ORDER BY p.rating DESC;''')


        # Получаем данные о заказе
        order = await conn.fetchrow(f'''SELECT o.num_of_performers, c.tg_id
                                        FROM orders o
                                        JOIN customers c ON o.id_user = c.id_user
                                        WHERE o.id_order = {id_order};''')

        print(order)

        # Проверяем есть ли исполнители заказа
        if users_order: # Если есть
            sum_users = 0
            selected_users = {} # Записываем всех
            selected_items = [] # Выбранный
            target_sum = order['num_of_performers'] # Сколько надо нам рабочих

            if len(users_order) <=1:
                selected_users.update({users_order[0]['tg_id']: users_order[0]['number_workers']})
                for key, value in selected_users.items():
                    selected_items.append((key, value))
            else:
                for user in users_order:
                    selected_users.update({user['tg_id']: user['number_workers']})
                    sum_users += user['number_workers']
                    print(selected_users)
                    if sum_users == target_sum: # Если равно, то записываем всех в рассылку
                        for key, value in selected_users.items():
                            selected_items.append((key, value))
                    elif sum_users > target_sum:# Если сумма людей больше чем надо
                        #Сортируем список
                        sorted_dict_desc = dict(sorted(selected_users.items(),
                                                       key=lambda item: item[1],
                                                       reverse=True))

                        if len(selected_users) > 1:  # Если в словаре более одной записи
                            for key, value in sorted_dict_desc.items():  # Перебераем все элементы словаря
                                if sum_users + value <= target_sum:
                                    selected_items.append((key, value))
                                    sum_users += value
                                else:
                                    selected_items.append((key, value))
                                    break
                        else: # Если в словаре одна запись
                            for key, value in sorted_dict_desc.items():
                                selected_items.append((key, value))
                        break

            # Записываем в базу данных исполнителей
            for item in selected_items:
                # Записываем в базу данных исполнителей
                await conn.execute(f"UPDATE users "
                                   f"SET selected = 1 "
                                   f"WHERE id_user = (SELECT id_user"
                                   f"FROM performers"
                                   f"WHERE tg_id = {int(item[0])})")
                
            #Отправляем сообщения всем исполнителям
            for item in selected_items:
                try:


                    #Отправляем сообщения
                    await bot.send_message(chat_id=int(item[0]),
                                           text=f'Вас выбрали исполнителем заказа <b><i>№{id_order}</i></b>',
                                           reply_markup=await create_inline_kb(1,
                                                                               'toOrderPer_',
                                                                                lx_common_phrases['info_order']))
                except:
                    print('Ошибка, пользователь заблокировал Вас')

            # Отправка сообщения заказчику
            try:
                await bot.send_message(chat_id=tg_id,
                                       text=f'Выбраны исполнители по заказу <b><i>№{id_order}</i></b>',
                                       reply_markup=await create_inline_kb(1,
                                                                           'toOrderCus_',
                                                                           lx_common_phrases['info_order']))
            except:
                print('Ошибка, пользователь заблокировал Вас')

        else: #Если нет людей кто откликнулся
            try:
                await bot.send_message(chat_id=tg_id,
                                       text=f'К сожалению по заказу №{id_order} исполнители не найдены',
                                       reply_markup=await create_inline_kb(1,
                                                                           'toOrderCus_',
                                                                           lx_common_phrases['info_order']))
            except:
                print('Ошибка, пользователь заблокировал Вас')


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Делаем всем исполнителям что заказ выполнен'''
async def completed_user_order(id_order):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))
        # Ставим отметку, что заказ выполнен
        await conn.execute(f'''UPDATE executors_orders
                                    SET checked = 1 
                                    WHERE id_order = {id_order}''')
    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')