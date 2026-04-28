import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, CHAT_ID, PROXY
from db.crud import get_state, set_state
from db.database import init_models
from services.ai_gen import (
    get_ai_advice,
    daily_weather_prompt,
    predict_rain_prompt,
)
from services.weather.advisor import get_full_day_forecast, get_minutely_forecast
from services.weather.api import get_predict_rain_data, get_weather_data_for_day
from services.weather.parser import (
    extract_current_data,
    extract_daily_data,
    extract_hourly_data,
    extract_minutely_data,
)


session = AiohttpSession()
if PROXY:
    session = AiohttpSession(proxy=PROXY)

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


async def send_daily_weather():
    print("Запуск утренней рассылки...")

    weather_data = await get_weather_data_for_day()

    daily = extract_daily_data(weather_data)
    hourly = extract_hourly_data(weather_data)
    current = extract_current_data(weather_data)

    summarized = get_full_day_forecast(daily, hourly, current)

    current_crompt = daily_weather_prompt(summarized)

    try:
        advice = await get_ai_advice(current_crompt)
        await bot.send_message(chat_id=CHAT_ID, text=advice)
    except RuntimeError as e:
        await bot.send_message(chat_id=CHAT_ID, text=e)
        await bot.send_message(chat_id=CHAT_ID, text="Держи просто сухой прогноз:")
        await bot.send_message(chat_id=CHAT_ID, text=summarized)


async def check_rain():
    print("Проверка дождя")
    alert_key = "last_rain_alert_time"

    weather_data = await get_predict_rain_data()
    current = extract_current_data(weather_data)
    minutely = extract_minutely_data(weather_data)
    predict = get_minutely_forecast(current, minutely)
    if predict is None:
        return

    last_alert_str = await get_state(alert_key)

    if last_alert_str:
        last_alert_time = datetime.fromisoformat(last_alert_str)
        if datetime.now() - last_alert_time < timedelta(minutes=40):
            return

    prompt = predict_rain_prompt(predict)
    try:
        advice = await get_ai_advice(prompt)
        await bot.send_message(chat_id=CHAT_ID, text=advice)
    except RuntimeError as e:
        await bot.send_message(chat_id=CHAT_ID, text=e)
        await bot.send_message(chat_id=CHAT_ID, text="Скоро дождь, вот чуть подробнее:")
        await bot.send_message(chat_id=CHAT_ID, text=predict)
    finally:
        await set_state(alert_key, datetime.now().isoformat())


async def main():
    await init_models()
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")

    scheduler.add_job(send_daily_weather, trigger="cron", hour=7, minute=0)
    scheduler.add_job(send_daily_weather, trigger="interval", minutes=1)
    scheduler.add_job(check_rain, trigger="interval", minutes=30)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
