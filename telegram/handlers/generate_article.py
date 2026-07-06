from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from services.topic_service import topic_service
from telegram.states.topic import CreateTopicState
from services.deepseek_service import ask_agent
import random

from utils.other import sanitize_html

router = Router()


@router.callback_query(F.data == "generate_article")
async def show_topics(callback: CallbackQuery):

    topics = await topic_service.get_all_topics()
    if topics == []:
        await callback.message.answer("Список топиков пуст, создайте топики")
        return
    await callback.message.answer("Генерирую...")

    topic = random.choice(topics)

    answer = await ask_agent(topic.name, topic.description)
    res = sanitize_html(answer)
    await callback.message.answer(res,parse_mode="HTML")