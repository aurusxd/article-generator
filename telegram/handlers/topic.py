from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from services.topic_service import topic_service
from telegram.keyboards.callback import TopicCallback
from telegram.states.topic import EditTopicState
from telegram.keyboards.main import keyboard

router = Router()




@router.callback_query(F.data == "topics")
async def show_topics(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    topics = await topic_service.get_all_topics()

    for topic in topics:
        builder.button(
            text=topic.name,
            callback_data=TopicCallback(
                action="open",
                topic_id=topic.id,
            ).pack(),
        )
    
    builder.button(
        text="⬅️ Назад",
        callback_data="back"
    )
    builder.adjust(1)

    await callback.message.edit_text(
        text = "📄 Выберите тематику:" if topics else "Тематики пока не созданы.",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@router.callback_query(TopicCallback.filter(F.action == "open"))
async def open_topic(
    callback: CallbackQuery,
    callback_data: TopicCallback,
):
    topic = await topic_service.get_topic_by_id(callback_data.topic_id)

    if topic is None:
        await callback.answer("Тематика не найдена", show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✏️ Изменить название",
        callback_data=TopicCallback(
            action="edit_name",
            topic_id=topic.id,
        ).pack(),
    )

    builder.button(
        text="📝 Изменить описание",
        callback_data=TopicCallback(
            action="edit_description",
            topic_id=topic.id,
        ).pack(),
    )

    builder.button(
        text="🔢 Публикаций в день",
        callback_data=TopicCallback(
            action="edit_posts",
            topic_id=topic.id,
        ).pack(),
    )

    builder.button(
        text="📷 С фото" if topic.with_photo else "📷 Без фото",
        callback_data=TopicCallback(
            action="photo",
            topic_id=topic.id,
        ).pack(),
    )


    builder.button(
        text="⏸ Выключить" if topic.is_enabled else "▶️ Включить",
        callback_data=TopicCallback(
            action="toggle",
            topic_id=topic.id,
        ).pack(),
    )

    builder.button(
        text="🗑 Удалить",
        callback_data=TopicCallback(
            action="delete",
            topic_id=topic.id,
        ).pack(),
    )

    builder.button(
        text="⬅️ Назад",
        callback_data="back",
    )

    builder.adjust(2,2,2,1)

    await callback.message.edit_text(
        text=(
            f"📄 Тематика: {topic.name}\n\n"
            f"Описание:\n{topic.description}\n\n"
            f"Публикаций в день: {topic.posts_per_day}\n"
            f"Статус: {'🟢 Включена' if topic.is_enabled else '🔴 Выключена'}\n"
            f"Фото: {'✅ Да' if topic.with_photo else '❌ Нет'}\n"
        ),
        reply_markup=builder.as_markup(),
    )

    await callback.answer()

@router.callback_query(TopicCallback.filter(F.action == "edit_name"))
async def edit_topic_name_start(
    callback: CallbackQuery,
    callback_data: TopicCallback,
    state: FSMContext,
):
    await state.update_data(topic_id=callback_data.topic_id)
    await state.set_state(EditTopicState.name)

    await callback.message.answer("Введите новое название тематики:")
    await callback.answer()

@router.message(EditTopicState.name)
async def edit_topic_name_finish(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    topic_id = data["topic_id"]

    await topic_service.update_topic(
        topic_id=topic_id,
        name=message.text,
    )

    await state.clear()

    await message.answer("✅ Название тематики обновлено",reply_markup=keyboard)


@router.callback_query(TopicCallback.filter(F.action == "edit_description"))
async def edit_topic_desc_start(
    callback: CallbackQuery,
    callback_data: TopicCallback,
    state: FSMContext,
):
    await state.update_data(topic_id=callback_data.topic_id)
    await state.set_state(EditTopicState.description)

    await callback.message.answer("Введите новое описание:")
    await callback.answer()

@router.message(EditTopicState.description)
async def edit_topic_desc_finish(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    topic_id = data["topic_id"]

    await topic_service.update_topic(
        topic_id=topic_id,
        description=message.text,
    )

    await state.clear()

    await message.answer("✅ Описание тематики обновлено",reply_markup=keyboard)


@router.callback_query(TopicCallback.filter(F.action == "edit_posts"))
async def edit_topic_posts_start(
    callback: CallbackQuery,
    callback_data: TopicCallback,
    state: FSMContext,
):
    await state.update_data(topic_id=callback_data.topic_id)
    await state.set_state(EditTopicState.posts_per_day)

    await callback.message.answer("Введите новое количество публикаций в день:")
    await callback.answer()

@router.message(EditTopicState.posts_per_day)
async def edit_topic_posts_finish(
    message: Message,
    state: FSMContext,
):
    if not message.text.isdigit():
        await message.answer("Введите число. Например: 3")
        return

    data = await state.get_data()
    topic_id = data["topic_id"]

    await topic_service.update_topic(
        topic_id=topic_id,
        posts_per_day=int(message.text),
    )

    await state.clear()

    await message.answer("✅ Количество публикаций тематики обновлено",reply_markup=keyboard)

@router.callback_query(TopicCallback.filter(F.action == "toggle"))
async def toggle_topic(
    callback: CallbackQuery,
    callback_data: TopicCallback,
):
    topic = await topic_service.get_topic_by_id(callback_data.topic_id)

    if topic is None:
        await callback.answer("Тематика не найдена", show_alert=True)
        return

    await topic_service.update_topic(
        topic_id=topic.id,
        is_enabled=not topic.is_enabled,
    )

    await callback.message.edit_text("Статус изменен",reply_markup=keyboard)

@router.callback_query(TopicCallback.filter(F.action == "delete"))
async def delete_topic(
    callback: CallbackQuery,
    callback_data: TopicCallback,
):
    topic = await topic_service.get_topic_by_id(callback_data.topic_id)

    if topic is None:
        await callback.answer("Тематика не найдена", show_alert=True)
        return

    await topic_service.delete_topic(
        topic_id=topic.id,
    )

    await callback.message.edit_text("Топик удален",reply_markup=keyboard)

@router.callback_query(TopicCallback.filter(F.action == "photo"))
async def photo(
    callback: CallbackQuery,
    callback_data: TopicCallback,
):
    topic = await topic_service.get_topic_by_id(callback_data.topic_id)

    if topic is None:
        await callback.answer("Тематика не найдена", show_alert=True)
        return

    await topic_service.update_topic(
        topic_id=topic.id,
        with_photo=not topic.with_photo
    )

    await callback.message.edit_text("Статус изменен",reply_markup=keyboard)