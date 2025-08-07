# bot_variables/bot_instance.py
import os
import telebot
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("KEY")
bot = telebot.TeleBot(api_key)
