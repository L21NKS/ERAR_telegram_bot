from dotenv import load_dotenv
import os
from bot_variables.const import var_labels, var_names, score_ranges, user_states
from bot_func.db_func import save_rating_to_db,update_rating_in_db
from bot_variables.bot_instance import bot


load_dotenv()
api_key = os.getenv("KEY")


def handle_rating_steps(message):
    chat_id = message.chat.id
    state = user_states[chat_id]

    if state['step'] == -1:
        state['film_name'] = message.text.strip()
        state['step'] = 0
        bot.send_message(chat_id, f"Введите оценку за {var_labels[0]}:")
        return

    step = state['step']
    min_val, max_val = score_ranges[step]

    try:
        score = float(message.text.strip())
        if not (min_val <= score <= max_val):
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, f"⚠️ Введите число от {min_val} до {max_val}.")
        return

    state['scores'].append(score)
    state['step'] += 1

    if state['step'] < len(var_names):
        bot.send_message(chat_id, f"Введите оценку за {var_labels[state['step']]}:")
    else:
        scores = state['scores']
        main_scores = scores[:7]
        coefficient = scores[7]
        average = sum(main_scores) / 7
        final_score = round(average * coefficient, 2)

        film_name = state['film_name']
        user_id = message.from_user.id

        if state.get('action') == 'edit_film':

            update_rating_in_db(film_name, final_score, user_id)
            bot.send_message(chat_id, f"✅ Оценка фильма \"{film_name}\" успешно обновлена на {final_score}")
        else:
            save_rating_to_db(film_name, final_score, user_id)
            bot.send_message(chat_id, f"Спасибо! Итоговая оценка фильма \"{film_name}\": {final_score}")

        del user_states[chat_id]