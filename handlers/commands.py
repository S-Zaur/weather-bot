from datetime import datetime
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db.repository import Repository
from handlers.state import LocationRegistration
from services.ai_gen import daily_weather_prompt, get_ai_advice, predict_rain_prompt
from services.weather import advisor, api, parser

router = Router()


@router.message(Command("now"))
async def cmd_weather(message: Message, repo: Repository):
    msg = await message.answer("Узнаем погоду")

    location = (await repo.user.get_with_location(message.from_user.id)).location
    weather_data = await api.get_weather_data_for_day(location)

    daily = parser.extract_daily_data(weather_data)
    hourly = parser.extract_hourly_data(weather_data)
    current = parser.extract_current_data(weather_data)
    summarized = advisor.get_full_day_forecast(daily, hourly, current)

    current_crompt = daily_weather_prompt(summarized)
    try:
        advice = await get_ai_advice(current_crompt)
        await msg.edit_text(advice)
    except RuntimeError as e:
        await msg.edit_text("Ой, что-то пошло не так. Держи просто сухой прогноз:")
        await message.answer(summarized)


@router.message(Command("rain"))
async def cmd_rain(message: Message, repo: Repository):
    alert_key = "last_rain_alert_time"

    msg = await message.answer("Узнаем погоду")

    location = (await repo.user.get_with_location(message.from_user.id)).location
    weather_data = await api.get_predict_rain_data(location)
    current = parser.extract_current_data(weather_data)
    minutely = parser.extract_minutely_data(weather_data)
    predict = advisor.get_minutely_forecast(current, minutely)

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
        await repo.state.set_state(
            alert_key + str(message.from_user.id), datetime.now().isoformat()
        )


@router.message(Command("start"))
async def cmd_start(message: Message, repo: Repository, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username
    user = await repo.user.get_by_id(telegram_id)

    if user:
        await message.answer(f"С возвращением, {user.username}! Рад тебя видеть снова.")
        return
    await repo.user.add_user(telegram_id, username)
    await state.set_state(LocationRegistration.waiting_for_location)
    await message.answer(
        "Привет! Чтобы я мог присылать тебе прогноз погоды, пожалуйста отправь мне геолокацию места которое хочешь отслеживать"
    )
    await message.answer(
        "Это можно сделать через меню вложений (скрепка -> геолокация)"
    )


@router.message(LocationRegistration.waiting_for_location, F.location)
async def get_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude

    await state.update_data(lat=lat, lon=lon)
    await state.set_state(LocationRegistration.waiting_for_name)
    await message.answer(
        "Локация получена. Как назовем это место? (пример 'Дом' или 'Работа')"
    )


@router.message(LocationRegistration.waiting_for_name, F.text)
async def get_name(message: Message, repo: Repository, state: FSMContext):
    data = await state.get_data()
    lat = data["lat"]
    lon = data["lon"]
    name = message.text

    await repo.location.add_location(lat, lon, name, message.from_user.id)
    await state.clear()
    await message.answer(
        f"Место {name} успешно сохранено! Теперь я буду присылать тебе прогноз погоды для этой точки"
    )
