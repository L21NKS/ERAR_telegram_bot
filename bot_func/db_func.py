from dotenv import load_dotenv
import os
import psycopg2
from bot_variables.bd import db_config
import telebot
from bot_variables.const import user_states,var_labels
import urllib


load_dotenv()
api_key = os.getenv("KEY")
bot = telebot.TeleBot(api_key)

def save_rating_to_db(film_name, final_score, user_log):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ratings (film_name, final_score, user_log) VALUES (%s, %s, %s)',
            (film_name, final_score, user_log)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")


def show_user_ratings(message):
    user_id = message.from_user.id
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT film_name, final_score FROM ratings WHERE user_log = %s',
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if rows:
            response = "Ваши оцененные фильмы\n"
            for film, score in rows:
                response += f"🎬  {film}  —  {score} / 10\n"
        else:
            response = "Вы пока не оценили ни одного фильма."

        bot.send_message(message.chat.id, response)

    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при получении данных")
        print(f"[DB ERROR] {e}")

def delete_film_by_number(user_id, film_number):
    films = get_user_rated_films(user_id)
    if 0 < film_number <= len(films):
        film_id = films[film_number - 1][0]
        film_name = films[film_number - 1][1]

        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM ratings WHERE id = %s AND user_log = %s',
                (film_id, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return film_name
        except Exception as e:
            print(f"[DB ERROR] {e}")
            return None
    return None


def check_film_exists(user_id, film_name):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM ratings WHERE film_name = %s AND user_log = %s',
            (film_name, user_id)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return False


def update_rating_in_db(film_name, new_score, user_id):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE ratings SET final_score = %s WHERE film_name = %s AND user_log = %s',
            (new_score, film_name, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")

def add_note(user_id, note_text):
    try:
        encoded_name = urllib.parse.quote(note_text)
        full_note = f"[{note_text}](https://www.kinopoisk.ru/index.php?kp_query={encoded_name})"
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notes (user_log, note_text) VALUES (%s, %s)',
            (user_id, full_note)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")


def get_notes(user_id):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, note_text FROM notes WHERE user_log = %s ORDER BY id',
            (user_id,)
        )
        notes = cursor.fetchall()
        cursor.close()
        conn.close()
        return notes
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return []


def delete_note_by_number(user_id, note_number):
    try:
        notes = get_notes(user_id)
        if 0 < note_number <= len(notes):
            note_id = notes[note_number - 1][0]
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM notes WHERE id = %s AND user_log = %s',
                (note_id, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        return False
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return False

def update_note_by_number(user_id, note_number, new_text):
    try:
        notes = get_notes(user_id)
        if 0 < note_number <= len(notes):
            note_id = notes[note_number - 1][0]

            encoded_name = urllib.parse.quote(new_text)
            full_note = f"[{new_text}](https://www.kinopoisk.ru/index.php?kp_query={encoded_name})"

            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE notes SET note_text = %s WHERE id = %s AND user_log = %s',
                (full_note, note_id, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        return False
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return False


def process_film_name_for_edit(message):
    chat_id = message.chat.id
    film_name = message.text.strip()

    if film_name in {
        "Начать оценивать", "Оцененные фильмы", "Заметки", "Назад",
        "Удалить оценку", "Изменить оценку", "Написать заметку",
        "Изменить заметку", "Удалить заметку"
    }:
        user_states.pop(chat_id, None)
        return

    if check_film_exists(chat_id, film_name):
        user_states[chat_id] = {
            'step': 0,
            'scores': [],
            'film_name': film_name,
            'action': 'edit_film'
        }
        bot.send_message(chat_id, f"Введите новую оценку за {var_labels[0]}:")
    else:
        bot.send_message(chat_id, f"⚠️ Фильм «{film_name}» не найден в ваших оценках")
        user_states.pop(chat_id, None)

def get_user_rated_films(user_id):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, film_name, final_score FROM ratings WHERE user_log = %s ORDER BY id',
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return []

def get_film_name_by_number(user_id, number):
    films = get_user_rated_films(user_id)
    if 0 < number <= len(films):
        return films[number - 1][1] 
    return None

def get_top_rated_films(limit=10):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT film_name, ROUND(AVG(final_score)::numeric, 2) AS avg_score, COUNT(*) AS total
            FROM ratings
            GROUP BY film_name
            ORDER BY avg_score DESC
            LIMIT %s
        """, (limit,))
        top_films = cursor.fetchall()
        cursor.close()
        conn.close()
        return top_films
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return []

