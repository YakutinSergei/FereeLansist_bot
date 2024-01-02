from datetime import datetime, timedelta

import asyncpg

from environs import Env


env = Env()
env.read_env()

#Создаем таблицу
async def db_connect():
    try:
        conn = await asyncpg.connect(user=env('user'),  password=env('password'), database=env('db_name'), host=env('host'))


        '''
        Таблица статусов statuses
        id_status - номер статуса
        name - имя статуса
        '''

        await conn.execute('''CREATE TABLE IF NOT EXISTS statuses(id_status SERIAL PRIMARY KEY,
                                                                    name TEXT);''')

        '''
        Таблица специализаций specializations
        id_specialization - номер специализации
        name - имя специализации
        '''
        await conn.execute('''CREATE TABLE IF NOT EXISTS specializations(id_specialization SERIAL PRIMARY KEY,
                                                                    name TEXT);''')


        '''
        Таблица заказчиков customers
        id_user - номер пользователя по порядку
        tg_id - id телеграмм
        name - Имя и фамилия
        '''
        await conn.execute('''CREATE TABLE IF NOT EXISTS customers(id_user SERIAL NOT NULL PRIMARY KEY,
                                                                    tg_id BIGSERIAL,
                                                                    name TEXT);''')


        '''
        Таблица исполнителей performers
        id_user - номер пользователя по порядку
        tg_id - id телеграмм
        name - Имя и фамилия
        id_status - статут из таблицы статусов
        rating - рейтинг исполнителя по умолчанию 50
        id_specialization - номер специализации
        '''
        await conn.execute('''CREATE TABLE IF NOT EXISTS performers(id_user SERIAL NOT NULL PRIMARY KEY,
                                                                    tg_id BIGSERIAL,
                                                                    name TEXT,
                                                                    id_status INTEGER REFERENCES statuses(id_status) NOT NULL,
                                                                    rating INTEGER DEFAULT '50',
                                                                    id_specialization INTEGER REFERENCES specializations(id_specialization) NOT NULL);''')


        '''
        Таблица заказов
        id_order - номер заказа
        id_user - номер заказчика из таблицы customers
        place - место проведения
        price - плата за работу
        date_of_creation - дата и время создания заказа
        date_completion - дата начала работ
        time_completion - время начала работ
        num_of_performers - количество исполнителей
        id_specialization - номер специализации
        description - описание работ       
        '''

        await conn.execute('''CREATE TABLE IF NOT EXISTS orders(id_order SERIAL NOT NULL PRIMARY KEY,
                                                                    id_user INTEGER REFERENCES customers(id_user) NOT NULL,
                                                                    place TEXT,
                                                                    price INTEGER,
                                                                    date_of_creation TIMESTAMP,
                                                                    date_completion DATE,
                                                                    time_completion TIME,
                                                                    num_of_performers INTEGER,
                                                                    id_specialization INTEGER REFERENCES specializations(id_specialization) NOT NULL, 
                                                                    description TEXT);''')


        '''
        Таблица заказов исполнителей executors_orders
        id_user - номер исполнителя из таблицы performers
        id_order - номер заказа из таблицы orders
        selected - выбран ли в качестве исполнителя        
        '''
        await conn.execute('''CREATE TABLE IF NOT EXISTS executors_orders(id_user INTEGER REFERENCES performers(id_user) NOT NULL,
                                                                            id_order INTEGER REFERENCES orders(id_order) NOT NULL,
                                                                            selected INTEGER DEFAULT '0');''')



    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
          if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')