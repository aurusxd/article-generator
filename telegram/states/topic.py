from aiogram.fsm.state import State, StatesGroup


class CreateTopicState(StatesGroup):
    name = State()
    description = State()
    posts_per_day = State()


class EditTopicState(StatesGroup):
    name = State()
    description = State()
    posts_per_day = State()