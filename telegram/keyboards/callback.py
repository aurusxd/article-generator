from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router
from aiogram.filters.callback_data import CallbackData
router = Router()


class TopicCallback(CallbackData, prefix="topic"):
    action: str
    topic_id: int

@router.callback_query(F.data == "topics")
async def topics(callback: CallbackQuery):
    await callback.message.edit_text("Список тематик")
    await callback.answer()


@router.callback_query(F.data == "create_topic")
async def create(callback: CallbackQuery):
    await callback.message.edit_text("Введите название новой тематики")
    await callback.answer()


@router.callback_query(F.data == "start")
async def start_scheduler(callback: CallbackQuery):
    await callback.answer("Автопубликация включена")


@router.callback_query(F.data == "stop")
async def stop_scheduler(callback: CallbackQuery):
    await callback.answer("Автопубликация остановлена")