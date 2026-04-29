from aiogram.fsm.state import State, StatesGroup


class LocationRegistration(StatesGroup):
    waiting_for_location = State()
    waiting_for_name = State()
