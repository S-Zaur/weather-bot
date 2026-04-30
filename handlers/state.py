from aiogram.fsm.state import State, StatesGroup


class LocationRegistration(StatesGroup):
    waiting_for_location = State()
    waiting_for_name = State()


class Setting(StatesGroup):
    waiting_for_time = State()
    waiting_for_rain_th = State()
