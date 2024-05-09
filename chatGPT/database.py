import logging
import sqlite3
from config import *
import math
from gpt import *


logging.basicConfig(filename=LOGS_PATH, level=logging.DEBUG,
                    format="%(asctime)s %(message)s", filemode="w")


def create_db(database_name=DB_NAME):
    db_path = f'{database_name}'
    connection = sqlite3.connect(db_path)
    connection.close()

def create_table_answer():
    sql_query=f'''
               CREATE TABLE IF NOT EXISTS gpt_answer(
               id INTEGER PRIMARY KEY,
               user_id INTEGER,
               gpt_answer TEXT)
            '''
    execute_query(DB_NAME, sql_query)
def create_table(table_name=DB_TABLE_USERS_NAME):
    sql_query = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                tts_symbols INTEGER,
                blocks INTEGER,
                tokens INTEGER)
            '''
    execute_query(DB_NAME, sql_query)


def execute_query(db_file, query, data=None):
    """
    Функция для выполнения запроса к базе данных.
    Принимает имя файла базы данных, SQL-запрос и опциональные данные для вставки.
    """

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    if data:
        cursor.execute(query, data)
    else:
        cursor.execute(query)

    connection.commit()
    connection.close()


def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    try:
        logging.info(f"DATABASE: Execute query: {sql_query}")

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)

        rows = cursor.fetchall()
        connection.close()
        return rows

    except sqlite3.Error as e:
        logging.error(f"DATABASE: Ошибка при запросе: {e}")
        print("Ошибка при выполнении запроса:", e)


def reg(user_id):
    connection = sqlite3.connect('speech_kit.db')
    cursor = connection.cursor()
    query = f'SELECT user_id FROM gpt_answer WHERE user_id = {user_id}'
    results = cursor.execute(query)
    if results != user_id:
        cursor.execute('''INSERT INTO gpt_answer (user_id, gpt_answer)VALUES (?, ?)''',
                       (user_id,' '))
    connection.commit()

def gpt_answer(answer, user_id):
    connection = sqlite3.connect('speech_kit.db')
    cur = connection.cursor()
    cur.execute(
        'UPDATE gpt_answer SET gpt_answer = ? WHERE user_id = ?;',
        (answer, user_id)
    )
    connection.commit()

def is_token_limit(message, dialogue):
    user_id = message.from_user.id
    text_symbols = count_tokens_in_dialogue(dialogue)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_tokens(user_id) + text_symbols
    if user_id==ADMIN_ID:
        MAX_TOKENS=9999999999999999999999
    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_TOKENS:
        msg = f"Превышен общий лимит Tokens {MAX_TOKENS}. Использовано: " \
              f"{all_symbols} символов. Доступно: {MAX_TOKENS - all_symbols}"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит GPT на запрос {MAX_GPT_TOKENS}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return text_symbols
def is_tts_symbol_limit(message, text):
    user_id = message.from_user.id
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_symbol(user_id) + text_symbols

    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_USER_TTS_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}. Использовано: " \
              f"{all_symbols} символов. Доступно: {MAX_USER_TTS_SYMBOLS - all_symbols}"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return len(text)
def insert_row(user_id, message, tts_symbols, blocks,tokens,db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Вставляем в таблицу новое сообщение
            cursor.execute('''INSERT INTO messages (user_id, message, tts_symbols, blocks, tokens)VALUES (?, ?, ?, ?, ?)''',
                           (user_id, message, tts_symbols, blocks,tokens))
            # Сохраняем изменения
            conn.commit()
    except Exception as e:  # обрабатываем ошибку и записываем её в переменную <e>
        print(f"Error: {e}")  # выводим ошибку в консоль


def count_all_tokens(user_id, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(tokens) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")



def count_all_symbol(user_id, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")

def count_all_blocks(user_id, db_name="speech_kit.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(blocks) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            if data and data[0]:
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")


def is_stt_block_limit(message, duration):
    user_id = message.from_user.id

    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / 15) # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = count_all_blocks(user_id) + audio_blocks

    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= MAX_USER_STT_BLOCKS:
        msg = f"Превышен общий лимит SpeechKit STT {MAX_USER_STT_BLOCKS}. Использовано {all_blocks} блоков. Доступно: {MAX_USER_STT_BLOCKS - all_blocks}"
        bot.send_message(user_id, msg)
        return None

    return audio_blocks


def clear_base(user_id):
    connection = sqlite3.connect('speech_kit.db')
    cur = connection.cursor()
    cur.execute(f'DELETE FROM gpt_answer WHERE user_id={user_id}')
    cur.execute('''INSERT INTO gpt_answer (user_id, gpt_answer)VALUES (?, ?)''',
                   (user_id, ' '))
    connection.commit()