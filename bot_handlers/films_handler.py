from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telebot import types
from bot_variables.const import user_states, menu_texts,var_labels
from bot_func.bot_utils import safe_send,pluralize_ru
from bot_func.db_func import delete_film_by_number,get_user_rated_films
from bot_variables.bot_instance import bot


load_dotenv()
api_key = os.getenv("KEY")


def show_rating_film_options(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Удалить оценку"),
        types.KeyboardButton("Изменить оценку"),
        types.KeyboardButton("Назад")
    )
    safe_send(chat_id, "Ваши оценённые фильмы:", reply_markup=markup)

    films = get_user_rated_films(chat_id)

    if not films:
        safe_send(chat_id, "⚠️ У вас пока нет оценённых фильмов")
        return

    response = ""
    for i, (_, name, score) in enumerate(films, 1):
        response += f"{i}. {name} — {score}\n"

    safe_send(chat_id, response)

def ask_rating_number_to_delete(message):
    chat_id = message.chat.id
    films = get_user_rated_films(chat_id)

    if not films:
        safe_send(chat_id, "⚠️ У вас пока нет оценённых фильмов")
        return  

    user_states[chat_id] = {'action': 'delete_film'}
    response = "🎬 Ваши оценённые фильмы:\n"
    for i, (_, name, score) in enumerate(films, 1):
        response += f"{i}. {name} — {score}/10\n"

    safe_send(chat_id, response)
    safe_send(chat_id, "Введите номер фильма, который вы хотите удалить:")

    def wrapper(msg):
        if msg.text.strip() in menu_texts:
            user_states.pop(chat_id, None)
            return

        try:
            number = int(msg.text.strip())
            deleted_film = delete_film_by_number(msg.from_user.id, number)
            if deleted_film:
                safe_send(chat_id, f"✅ Фильм «{deleted_film}» был удалён.")
            else:
                safe_send(chat_id, "⚠️ Неверный номер фильма")
        except ValueError:
            safe_send(chat_id, "⚠️ Введите корректный номер")
        user_states.pop(chat_id, None)

    bot.register_next_step_handler(message, wrapper)

def ask_rating_number_to_edit(message):
    chat_id = message.chat.id
    films = get_user_rated_films(chat_id)

    if not films:
        safe_send(chat_id, "⚠️ У вас пока нет оценённых фильмов")
        return

    response = "🎬 Ваши оценённые фильмы:\n"
    for i, (_, name, score) in enumerate(films, 1):
        response += f"{i}. {name} — {score}\n"

    safe_send(chat_id, response)
    safe_send(chat_id, "Введите номер фильма, оценку которого вы хотите изменить:")

    user_states[chat_id] = {'action': 'edit_film_select'}

    def wrapper(msg):
        try:
            number = int(msg.text.strip())
            if not (1 <= number <= len(films)):
                raise ValueError
            film_name = films[number - 1][1]
            user_states[chat_id] = {
                'step': 0,
                'scores': [],
                'film_name': film_name,
                'action': 'edit_film'
            }

            safe_send(chat_id, f"✏️ Изменяем оценку фильма «{film_name}»")
            safe_send(chat_id, f"Введите новую оценку за {var_labels[0]}:")

        except ValueError:
            safe_send(chat_id, "⚠️ Введите корректный номер фильма")
            user_states.pop(chat_id, None)

    bot.register_next_step_handler(message, wrapper)

def process_film_name_for_deletion(message):
    chat_id = message.chat.id
    film_name = message.text.strip()

    menu_texts

    if film_name in menu_texts:
        user_states.pop(chat_id, None)
        return  

    success = delete_film_by_number(chat_id, film_name)
    if success:
        safe_send(chat_id, f"Оценка фильма '{film_name}' успешно удалена.")
    user_states.pop(chat_id, None)

def show_rating(message):
    from bot_func.db_func import get_top_rated_films
    top_films = get_top_rated_films()

    if not top_films:
        safe_send(message.chat.id, "⚠️ В данный момент нет общего рейтинга")
        return

    response = "🏆 Топ-10 фильмов по средней оценке:\n\n"
    for i, (film, avg_score, count) in enumerate(top_films, 1):
        form = pluralize_ru(count)
        response += f"{i}. {film} — {avg_score}  ({count} {form})\n"


    safe_send(message.chat.id, response)