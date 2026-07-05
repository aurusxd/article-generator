from aiogram.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()

builder.button(
    text="📄 Тематики",
    callback_data="topics",
)

builder.button(
    text="➕ Создать",
    callback_data="create_topic",
)

builder.button(
    text="▶️ Запустить",
    callback_data="start",
)

builder.button(
    text="⏹️ Остановить",
    callback_data="stop",
)



builder.adjust(1)

keyboard = builder.as_markup()