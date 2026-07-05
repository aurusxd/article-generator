from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from telegram.states.topic import CreateTopicState
from services.topic_service import topic_service

router = Router()


@router.callback_query(F.data == "create_topic")
async def create_topic_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.set_state(CreateTopicState.name)

    await callback.message.answer("Введите название тематики:")
    await callback.answer()

@router.message(CreateTopicState.name)
async def create_topic_name(
    message: Message,
    state: FSMContext,
):
    await state.update_data(name=message.text)

    await state.set_state(CreateTopicState.description)

    await message.answer("Теперь введите описание тематики:")

@router.message(CreateTopicState.description)
async def create_topic_description(
    message: Message,
    state: FSMContext,
):
    await state.update_data(description=message.text)

    await state.set_state(CreateTopicState.posts_per_day)

    await message.answer("Сколько публикаций в день делать?")


@router.message(CreateTopicState.posts_per_day)
async def create_topic_posts_per_day(
    message: Message,
    state: FSMContext,
):
    if not message.text.isdigit():
        await message.answer("Введите число. Например: 3")
        return

    posts_per_day = int(message.text)

    data = await state.get_data()

    topic = await topic_service.create_topic(
        name=data["name"],
        description=data["description"],
    )

    if topic is None:
        await message.answer("Не удалось создать тематику.")
        await state.clear()
        return

    await topic_service.update_topic(
        topic_id=topic.id,
        posts_per_day=posts_per_day,
    )

    await state.clear()

    await message.answer(
        f"Тематика создана!\n\n"
        f"Название: {data['name']}\n"
        f"Описание: {data['description']}\n"
        f"Публикаций в день: {posts_per_day}"
    )