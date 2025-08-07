from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telebot import types
from bot_variables.const import user_states, menu_texts
from bot_func.db_func import get_notes,add_note,delete_note_by_number,update_note_by_number
from bot_func.bot_utils import safe_send
from bot_variables.bot_instance import bot



load_dotenv()
api_key = os.getenv("KEY")


def show_rating_options(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Посмотреть заметки"),
        types.KeyboardButton("Написать заметку"),
        types.KeyboardButton("Изменить заметку"),
        types.KeyboardButton("Удалить заметку"),
        types.KeyboardButton("Назад")
    )
    view_notes(message, reply_markup=markup)

def ask_to_add_note(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'action': 'add_note'}
    safe_send(chat_id, "Введите название фильма, который вы хотите добавить в заметки:")

    def wrapper(msg):
        if msg.text.strip() in menu_texts:
            user_states.pop(chat_id, None)
            return

        if user_states.get(chat_id, {}).get("action") == "add_note":
            add_note(msg.from_user.id, msg.text.strip())
            user_states.pop(chat_id, None)
            show_rating_options(msg)

    bot.register_next_step_handler(message, wrapper)

def ask_to_delete_note(message):
    chat_id = message.chat.id
    notes = get_notes(chat_id)

    if not notes:
        safe_send(chat_id, "⚠️ У вас пока нет заметок для удаления")
        return

    user_states[chat_id] = {'action': 'delete_note'}
    safe_send(chat_id, "Введите номер заметки, которую вы хотите удалить:")

    def wrapper(msg):
        if msg.text.strip() in menu_texts:
            user_states.pop(chat_id, None)
            return

        if user_states.get(chat_id, {}).get("action") == "delete_note":
            try:
                number = int(msg.text.strip())

                success = delete_note_by_number(msg.from_user.id, number)
                if success:
                    show_rating_options(msg)
                else:
                    safe_send(chat_id, "⚠️ Неверный номер заметки")
            except ValueError:
                safe_send(chat_id, "⚠️ Введите корректный номер")
            user_states.pop(chat_id, None)

    bot.register_next_step_handler(message, wrapper)

def ask_note_number_to_edit(message):
    chat_id = message.chat.id
    notes = get_notes(chat_id)

    if not notes:
        safe_send(chat_id, "⚠️ У вас пока нет заметок для изменения")
        return

    user_states[chat_id] = {'action': 'edit_note'}
    safe_send(chat_id, "Введите номер заметки, которую хотите изменить:")

    def wrapper(msg):
        if msg.text.strip() in menu_texts:
            user_states.pop(chat_id, None)
            return

        if user_states.get(chat_id, {}).get("action") == "edit_note":
            try:
                number = int(msg.text.strip())
                user_states[chat_id] = {'action': 'edit_note_text', 'note_number': number}
                safe_send(chat_id, "Введите новый текст для заметки:")

                def final_step(msg2):
                    if msg2.text.strip() in menu_texts:
                        user_states.pop(chat_id, None)
                        return

                    note_number = user_states[chat_id].get('note_number')
                    success = update_note_by_number(msg2.from_user.id, note_number, msg2.text.strip())
                    if success:
                        show_rating_options(msg2)
                    else:
                        safe_send(chat_id, "⚠️ Номер заметки неверный")
                    user_states.pop(chat_id, None)

                bot.register_next_step_handler(msg, final_step)

            except ValueError:
                safe_send(chat_id, "⚠️ Введите корректный номер")
                user_states.pop(chat_id, None)

    bot.register_next_step_handler(message, wrapper)

def view_notes(message, reply_markup=None):
    notes = get_notes(message.from_user.id)

    if notes:
        response = "📋 Ваши заметки:\n"
        for i, (_, text) in enumerate(notes, 1):
            response += f"{i}. {text}\n"
    else:
        response = "⚠️ У вас пока нет заметок"

    safe_send(message.chat.id, response, reply_markup=reply_markup, parse_mode='Markdown')