from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db.crud import set_state
from services.ai_gen import daily_weather_prompt, get_ai_advice, predict_rain_prompt
from services.weather.advisor import get_full_day_forecast, get_minutely_forecast
from services.weather.api import get_predict_rain_data, get_weather_data_for_day
from services.weather.parser import (
    extract_current_data,
    extract_daily_data,
    extract_hourly_data,
    extract_minutely_data,
)

router = Router()


@router.message(Command("now"))
async def cmd_weather(message: Message):
    msg = await message.answer("Узнаем погоду")

    weather_data = await get_weather_data_for_day()

    daily = extract_daily_data(weather_data)
    hourly = extract_hourly_data(weather_data)
    current = extract_current_data(weather_data)
    summarized = get_full_day_forecast(daily, hourly, current)

    current_crompt = daily_weather_prompt(summarized)
    try:
        advice = await get_ai_advice(current_crompt)
        await msg.edit_text(advice)
    except RuntimeError as e:
        await msg.edit_text("Ой, что-то пошло не так. Держи просто сухой прогноз:")
        await message.answer(summarized)


@router.message(Command("rain"))
async def cmd_rain(message: Message):
    alert_key = "last_rain_alert_time"

    msg = await message.answer("Узнаем погоду")

    weather_data = await get_predict_rain_data()
    current = extract_current_data(weather_data)
    minutely = extract_minutely_data(weather_data)
    predict = get_minutely_forecast(current, minutely)

    if predict is None:
        await msg.edit_text("В ближайшие 3 часа дождя не ожидается")
        return

    prompt = predict_rain_prompt(predict)
    try:
        advice = await get_ai_advice(prompt)
        await msg.edit_text(advice)
    except RuntimeError as e:
        await msg.edit_text("Скоро дождь, вот чуть подробнее:")
        await message.answer(predict)
    finally:
        await set_state(alert_key, datetime.now().isoformat())
