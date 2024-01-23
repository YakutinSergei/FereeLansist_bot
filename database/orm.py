from datetime import datetime

import asyncpg

from environs import Env

env = Env()
env.read_env()

#Получение статуса юзера
async def bd_get_user_status(tg_id: int) -> int:
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        user_status = await conn.fetchrow(f'''SELECT id_user 
                                            FROM performers 
                                            WHERE tg_id = {tg_id}''')
        if user_status:
            return 1
        else:
            user_status = await conn.fetchrow(f'''SELECT id_user 
                                                        FROM customers 
                                                        WHERE tg_id = {tg_id}''')
            if user_status:
                return 2
            else:
                return 0


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Добавление исполнителя'''
async def bd_add_performer(tg_id, performer):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                 host=env('host'))

        await conn.execute(f'''INSERT INTO performers(tg_id, name, id_status, id_specialization)
                                      VALUES($1, $2, 1, (SELECT id_specialization
                                                      FROM specializations
                                                      WHERE name = '{performer['specialization']}'))''',
                           tg_id, performer['name'])


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Добавляем заказчика'''
async def bd_add_customer(tg_id:int, name:str):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                 host=env('host'))

        await conn.execute(f'''INSERT INTO customers(tg_id, name)
                                              VALUES($1, $2)''',
                           tg_id, name)
    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')

'''Данные о исполнителе'''
async def get_user_profile(tg_id:int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        user = await conn.fetchrow(f'''SELECT performers.name, 
                                                performers.rating,
                                                specializations.name AS specialization,
                                                statuses.name AS status
                                        FROM performers
                                        JOIN specializations ON performers.id_specialization = specializations.id_specialization
                                        JOIN statuses ON performers.id_status = statuses.id_status
                                        WHERE tg_id = {tg_id}''')


        count_order = await conn.fetchrow(f'''SELECT COUNT(id_user) 
                                        FROM executors_orders
                                        WHERE id_user = (SELECT id_user
                                                        FROM performers
                                                        WHERE tg_id = {tg_id})
                                        AND selected = 1 AND checked = 1''')

        return user, count_order

    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Данные о заказчике'''
async def get_user_profile_customer(tg_id:int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        user = await conn.fetchrow(f'''
                                    SELECT c.name AS customer_name, 
                                           COUNT(DISTINCT o.id_order) AS active_orders_count, 
                                           COUNT(DISTINCT CASE WHEN o.checked = 1 THEN o.id_order END) AS completed_orders_count
                                    FROM customers c
                                        LEFT JOIN orders o ON c.id_user = o.id_user
                                    WHERE c.tg_id = {tg_id}
                                    GROUP BY c.name;
    ''')

        return  user
    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Получение всех специальностей'''
async def get_specializations_db():
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        specializations = await conn.fetch(f'''
                                                SELECT name
                                                FROM specializations
''')

        return specializations

    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Записываем данные заказа в базу данных'''
async def bd_post_order_user(order, tg_id:int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        num_order = await conn.fetchrow(f'''INSERT INTO orders(id_user, 
                                                  place, 
                                                  price, 
                                                  date_of_creation, 
                                                  date_completion, 
                                                  time_completion, 
                                                  num_of_performers, 
                                                  id_specialization, 
                                                  description)
                                          VALUES((SELECT id_user
                                                  FROM customers
                                                  WHERE tg_id = $1), 
                                                  $2, 
                                                  $3, 
                                                  $4,
                                                  $5,
                                                  $6,
                                                  $7,
                                                  (SELECT id_specialization
                                                  FROM specializations
                                                  WHERE name = $8),
                                                  $9) 
                                          RETURNING id_order''',
                           tg_id,
                           order['location'],
                           int(order['price_order']),
                           datetime.now(),
                           datetime.strptime(order['date_order'], '%Y-%m-%d').date(),
                           datetime.strptime(order['time_order'], '%H:%M').time(),
                           int(order['count_workers_order']),
                           order['specializations_order'],
                           order['desc_order']
                           )

        user_orders = await conn.fetch(f'''
                                        SELECT tg_id
                                        FROM performers
                                        WHERE id_specialization = (SELECT id_specialization
                                                                  FROM specializations
                                                                  WHERE name = '{order['specializations_order']}'
                                                                  )
''')

        return user_orders, num_order

    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Добавление заказа к исполнителю'''
async def bd_add_user_order(tg_id: int,
                            id_order: int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        await conn.execute(f'''INSERT INTO executors_orders(id_user, id_order)
                                                      VALUES((SELECT id_user
                                                              FROM performers 
                                                              WHERE tg_id = $1), $2)''',
                           tg_id, id_order)

    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')



'''Получение всех заказов заказчика'''
async def bd_get_order(tg_id:int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        user_orders = await conn.fetch(f'''
                                           SELECT id_order
                                           FROM orders
                                           WHERE id_user = (SELECT id_user
                                                             FROM customers
                                                             WHERE tg_id = '{tg_id}'
                                                             )
                                           ORDER BY id_order
       ''')

        return user_orders


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''получаем данные о заказе'''
async def get_order_info(id_order:int):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        orders = await conn.fetchrow(f'''
                                       SELECT o.place, 
                                              o.price, 
                                              o.date_of_creation, 
                                              o.date_completion,
                                              o.time_completion,
                                              o.num_of_performers,
                                              s.name,
                                              o.description,
                                              o.checked
                                       FROM orders o
                                       JOIN specializations s ON s.id_specialization = o.id_specialization
                                       WHERE id_order = {id_order} AND checked = 0
       ''')

        return orders


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')