from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telebot import types
from bot_variables.const import user_states
from bot_func.hand_func import handle_rating_steps
from bot_func.db_func import show_user_ratings,delete_film_by_number
from bot_handlers.notes_handler import show_rating_options,ask_to_add_note,ask_to_delete_note,ask_note_number_to_edit,view_notes
from bot_handlers.films_handler import show_rating_film_options,ask_rating_number_to_delete,ask_rating_number_to_edit,process_film_name_for_deletion,show_rating
from bot_func.bot_utils import safe_send,information
from bot_variables.bot_instance import bot


load_dotenv()
api_key = os.getenv("KEY")


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("Начать оценивать"), types.KeyboardButton("Оцененные фильмы"),types.KeyboardButton("Заметки"),types.KeyboardButton("Рейтинг"),types.KeyboardButton("Важная информация"))
    
    safe_send(
    message.chat.id,
    (
        f"Привет, {message.from_user.first_name}! Если ты сюда попал, значит, тебе нравится оценивать разного рода фильмы."
        " Если тебе надоели обычные заметки, в которых ты записывал фильмы для будущего обзора, то тебя ждёт понятная и точная система оценки кинокартин." \
        "\n"
        "Полную информацию о том, как пользоваться ботом, ты можешь найти в разделе «Важная информация». Приятного пользования!"
    ),
    reply_markup=markup
)
    safe_send(
    message.chat.id,
    (
        "Оценка фильма рассчитывается на основе 8 составляющих:\n"
        "1. \"Режиссёрская работа\"\n"
        "2. \"Операторская работа\"\n"
        "3. \"Сценарий\"\n"
        "4. \"Актёрская игра\"\n"
        "5. \"Монтаж\"\n"
        "6. \"Декорации\"\n"
        "7. \"Звуковое сопровождение и музыка\"\n"
        "8. \"Коэффициент общих эмоций от фильма\"\n"
        "Итоговая оценка фильма будет находиться в диапазоне от 0 до 10"
    )
)

    

@bot.message_handler(func=lambda message: message.text == "Заметки")
def handle_notes_1(message):
    show_rating_options(message)


@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Начать оценивать"),
        types.KeyboardButton("Оцененные фильмы"),
        types.KeyboardButton("Заметки"),
        types.KeyboardButton("Рейтинг"),
        types.KeyboardButton("Важная информация")
    )
    safe_send(message.chat.id, "✅ Вы вернулись в главное меню", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Написать заметку")
def handle_notes_2(message):
    ask_to_add_note(message)

@bot.message_handler(func=lambda message: message.text == "Удалить заметку")
def handle_notes_3(message):
    ask_to_delete_note(message)


@bot.message_handler(func=lambda message: message.text == "Изменить заметку")
def handle_notes_4(message):
    ask_note_number_to_edit(message)


@bot.message_handler(func=lambda message: message.text == "Посмотреть заметки")
def handle_notes_5(message):
    view_notes(message, reply_markup=None)



@bot.message_handler(func=lambda message: message.text == "Оцененные фильмы")
def handle_film_1 (message):
    show_rating_film_options(message)

@bot.message_handler(func=lambda message: message.text == "Удалить оценку")
def handle_film_2 (message):
    ask_rating_number_to_delete(message)

@bot.message_handler(func=lambda message: message.text == "Изменить оценку")
def handle_film_3 (message):
    ask_rating_number_to_edit(message)

    process_film_name_for_deletion(message)

@bot.message_handler(func=lambda message: message.text == "Важная информация")
def inf_film (message):
    information(message)


@bot.message_handler(content_types=['text'])
def main(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text == "Начать оценивать":
        user_states[chat_id] = {'step': -1, 'scores': []}
        safe_send(chat_id, "Введите название фильма:")
        return

    if text == "Оцененные фильмы":
        show_user_ratings(message)
        return
    
    if text == "Удалить оценку":
        delete_film_by_number(message)
        return
    
    if text == "Рейтинг":
        show_rating(message)
        return

    if chat_id in user_states:
        handle_rating_steps(message)
        return

bot.polling(none_stop=True, interval=0)