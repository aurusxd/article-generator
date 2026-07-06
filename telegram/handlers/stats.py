from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from services.topic_service import topic_service
from telegram.keyboards.callback import TopicCallback
from telegram.states.topic import EditTopicState
from telegram.keyboards.main import keyboard
from services.publication_log_service import publication_log_service
router = Router()




@router.callback_query(F.data == "stats")
async def show_topics(callback: CallbackQuery):
    list = publication_log_service.get_topic_logs()
    await callback.message.edit_text(
        text = f"Постов отправлено: {len(list)}",
        reply_markup=keyboard,
    )
