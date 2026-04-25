import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, CHAT_ID, PROXY
from services.ai_gen import get_ai_advice, daily_weather_prompt
from services.weather import (
    get_weather_data_for_day,
    extract_current_data,
    extract_hourly_data,
    extract_daily_data,
    summarize_all_data,
)

session = AiohttpSession()
if PROXY:
    session = AiohttpSession(proxy=PROXY)

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


async def send_daily_weather():
    print("Запуск утренней рассылки...")

    weather_data = await get_weather_data_for_day()

    current = extract_current_data(weather_data)
    daily = extract_daily_data(weather_data)
    hourly = extract_hourly_data(weather_data)
    summarized = summarize_all_data(current, hourly, daily)

    current_crompt = daily_weather_prompt(summarized)
    try:
        advice = await get_ai_advice(current_crompt)
        await bot.send_message(chat_id=CHAT_ID, text=advice)
    except RuntimeError as e:
        await bot.send_message(chat_id=CHAT_ID, text=e)
        await bot.send_message(chat_id=CHAT_ID, text="Держи просто сухой прогноз:")
        await bot.send_message(chat_id=CHAT_ID, text=summarized)


async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")

    scheduler.add_job(send_daily_weather, trigger="cron", hour=7, minute=0)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
