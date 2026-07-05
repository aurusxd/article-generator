from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from api.client import ApiClient
from services.logger import log
from telegram.command_handler import BotCommandHandler
from config import BOT_TOKEN
from telegram.keyboards.main import keyboard

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
api_client = ApiClient()
command_handler = BotCommandHandler(api_client=api_client)
dp.startup.register(command_handler.on_startup)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать!",
        reply_markup=keyboard,
    )


# @dp.message()
# async def message_handler(message: types.Message):
#     """Перенаправляет входящие сообщения Telegram в обработчик команд."""
#     user_id = str(message.from_user.id)
#     username = message.from_user.username or message.from_user.first_name or "Unknown"
#     text = message.text or ""
#     log.info(f"Сообщение от {user_id}:{username}: {text}")

#     await command_handler.handle_message(message)


