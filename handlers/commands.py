import asyncio
from contextlib import suppress
from datetime import datetime
import re
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from db.repository import Repository
from handlers.state import LocationRegistration, Setting
from handlers.waiting_phrases import get_phrase
from keyboards.callback import SettingsCallback
from keyboards.inline import SettingsKeyboards
from services.ai_gen import daily_weather_prompt, get_ai_advice, predict_rain_prompt
from services.weather import advisor, api, parser

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, repo: Repository, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username
    user = await repo.user.get_by_id(telegram_id)

    if user:
        await message.answer(f"С возвращением, {user.username}! Рад тебя видеть снова.")
        return
    await repo.user.add_user(telegram_id, username)
    await repo.setting.default(telegram_id)
    await state.set_state(LocationRegistration.waiting_for_location)
    await message.answer(
        "Привет! Чтобы я мог присылать тебе прогноз погоды, пожалуйста отправь мне геолокацию места которое хочешь отслеживать"
    )
    await message.answer(
        "Это можно сделать через меню вложений (скрепка -> геолокация)"
    )


@router.message(Command("now"))
async def cmd_weather(message: Message, repo: Repository):
    msg = await message.answer("Начинаю сбор данных...")
    stop_animation = asyncio.Event()
    animation_task = asyncio.create_task(animate_loading(msg, stop_animation))

    location = (await repo.user.get_with_location(message.from_user.id)).location
    weather_data = await api.get_weather_data_for_day(location)

    daily = parser.extract_daily_data(weather_data)
    hourly = parser.extract_hourly_data(weather_data)
    current = parser.extract_current_data(weather_data)
    summarized = advisor.get_full_day_forecast(daily, hourly, current)

    current_crompt = daily_weather_prompt(summarized)
    advice = ""
    try:
        advice = await get_ai_advice(current_crompt)
    except RuntimeError as e:
        advice = summarized
    finally:
        stop_animation.set()
        await animation_task
        await msg.edit_text(advice)


@router.message(Command("rain"))
async def cmd_rain(message: Message, repo: Repository):
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
    except RuntimeError:
        await msg.edit_text("Скоро дождь, вот чуть подробнее:")
        await message.answer(predict)


@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message, repo: Repository):
    msg = await message.answer("Начинаю сбор данных...")
    stop_animation = asyncio.Event()
    animation_task = asyncio.create_task(animate_loading(msg, stop_animation))

    location = (await repo.user.get_with_location(message.from_user.id)).location
    weather_data = await api.get_tomorrow_weather(location)

    hourly = parser.extract_hourly_data(weather_data)
    summarized = advisor.get_tomorrow_forecast(hourly)

    current_crompt = daily_weather_prompt(summarized)
    advice = ""
    try:
        advice = await get_ai_advice(current_crompt)
    except RuntimeError as e:
        advice = summarized
    finally:
        stop_animation.set()
        await animation_task
        await msg.edit_text(advice)


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

    await repo.location.update_or_create(message.from_user.id, lat, lon, name)
    await state.clear()
    await message.answer(
        f"Место {name} успешно сохранено! Теперь я буду присылать тебе прогноз погоды для этой точки"
    )


@router.message(Command("my_location"))
async def cmd_my_location(message: Message, repo: Repository):
    user = await repo.user.get_with_location(message.from_user.id)
    if not user:
        await message.answer("Мы с тобой еще не знакомы. Введи /start чтобы начать")
        return
    if not user.location:
        await message.answer(
            "Ты еще не сохранил местоположение. Чтобы сделать это введи /edit_location"
        )
        return
    await message.answer(f"Твоя локация: {user.location.name}")
    await message.bot.send_location(
        chat_id=message.chat.id, latitude=user.location.lat, longitude=user.location.lon
    )


@router.message(Command("edit_location"))
async def edit_location(message: Message, state: FSMContext):
    await state.set_state(LocationRegistration.waiting_for_location)
    await message.answer("Можешь присылать новую геопозицию (скрепка -> геопозиция)")


@router.message(Command("settings"))
async def cmd_settings(message: Message, repo: Repository):
    user = await repo.user.get_with_setting(message.from_user.id)

    await message.answer(
        "Здесь ты можешь настроить, как и когда бот будет тебя беспокоить",
        reply_markup=SettingsKeyboards.main_settings(user.setting),
    )


@router.callback_query(SettingsCallback.filter(F.action == "edit"))
async def handle_edit(
    callback: CallbackQuery,
    repo: Repository,
    callback_data: SettingsCallback,
    state: FSMContext,
):
    if callback_data.value == "daily_report":
        settings = await repo.setting.toggle_daily_report(callback.from_user.id)
        updated_kb = SettingsKeyboards.main_settings(settings)
        await callback.message.edit_reply_markup(reply_markup=updated_kb)
        await callback.answer("Настройки изменены")
    if callback_data.value == "rain_alert":
        settings = await repo.setting.toggle_rain_alert(callback.from_user.id)
        updated_kb = SettingsKeyboards.main_settings(settings)
        await callback.message.edit_reply_markup(reply_markup=updated_kb)
        await callback.answer("Настройки изменены")
    if callback_data.value == "report_time":
        await callback.message.edit_text(
            "Введи время для утреннего отчета в формате **ЧЧ:ММ** (например, 08:30)",
            reply_markup=None,
        )
        await state.update_data(menu_message_id=callback.message.message_id)
        await state.set_state(Setting.waiting_for_time)
        await callback.answer()
    if callback_data.value == "rain_th":
        await callback.message.edit_text(
            "Введи порог для уведомлений о дожде (если интенсивность дождя ниже этого числа уведомление тебе не придет). Например 0.5 или 1",
            reply_markup=None,
        )
        await state.update_data(menu_message_id=callback.message.message_id)
        await state.set_state(Setting.waiting_for_rain_th)
        await callback.answer()


@router.message(Setting.waiting_for_time, F.text)
async def process_report_time(message: Message, state: FSMContext, repo: Repository):
    time_input = message.text
    data = await state.get_data()
    menu_msg_id = data.get("menu_message_id")
    await message.delete()

    if not re.match(r"^([01]?[0-9]):[0-5][0-9]$", time_input):
        if not data.get("after_error"):
            err_msg = await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="Неверный формат. Попробуй еще раз (например, 06:30)",
            )
            await state.update_data(menu_msg_id=err_msg.message_id, after_error=True)
        return

    time_input = datetime.strptime(time_input, "%H:%M").time()
    settings = await repo.setting.change_report_time(message.from_user.id, time_input)
    updated_kb = SettingsKeyboards.main_settings(settings)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_msg_id,
        text="Время уведомлений изменено",
        reply_markup=updated_kb,
    )
    await state.clear()


@router.message(Setting.waiting_for_rain_th, F.text)
async def process_rain_th(message: Message, state: FSMContext, repo: Repository):
    th_input = message.text
    data = await state.get_data()
    menu_msg_id = data.get("menu_message_id")
    await message.delete()

    if not re.match(r"^(?:10(?:\.0)?|[0-9](?:\.[0-9])?)$", th_input):
        if not data.get("after_error"):
            err_msg = await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=menu_msg_id,
                text="Неверный формат. Попробуй еще раз (например, 2.5)",
            )
            await state.update_data(menu_msg_id=err_msg.message_id, after_error=True)
        return

    th_input = float(th_input)
    settings = await repo.setting.change_rain_th(message.from_user.id, th_input)
    updated_kb = SettingsKeyboards.main_settings(settings)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_msg_id,
        text="Порог уведомлений изменен",
        reply_markup=updated_kb,
    )
    await state.clear()


async def animate_loading(message: Message, stop_event: asyncio.Event):
    with suppress(TelegramBadRequest, asyncio.CancelledError):
        while not stop_event.is_set():
            await asyncio.sleep(3)
            if stop_event.is_set():
                break
            phrase = get_phrase()
            await message.edit_text(phrase)
