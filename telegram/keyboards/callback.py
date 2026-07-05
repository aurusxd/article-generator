from aiogram import F, types
from aiogram.types import CallbackQuery
from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from telegram.keyboards.main import keyboard

router = Router()

class TopicCallback(CallbackData, prefix="topic"):
    action: str
    topic_id: int



@router.callback_query(F.data == "start")
async def start_scheduler(callback: CallbackQuery):
    await callback.answer("Автопубликация включена")


@router.callback_query(F.data == "stop")
async def stop_scheduler(callback: CallbackQuery):
    await callback.answer("Автопубликация остановлена")

@router.callback_query(F.data == "back")
async def back_command(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Добро пожаловать!",
        reply_markup=keyboard,
    )