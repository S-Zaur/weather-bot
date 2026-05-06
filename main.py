import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

from config import BOT_TOKEN, PROXY
from db.dao import UserDAO, UserSettingDAO
from db.database import init_models, async_session
from db.middleware import DbSessionMiddleware
from services.ai_gen import (
    get_ai_advice,
    daily_weather_prompt,
    predict_rain_prompt,
)
from handlers.commands import router as coms_router
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
tz = pytz.timezone("Asia/Yekaterinburg")


async def send_daily_weather():
    nw = datetime.now(tz).time().replace(second=0, microsecond=0)
    async with async_session() as session:
        user_dao = UserDAO(session)
        users = await user_dao.get_all_for_daily_report(nw)

        for user in users:

            weather_data = await get_weather_data_for_day(user.location)

            daily = extract_daily_data(weather_data)
            hourly = extract_hourly_data(weather_data)
            current = extract_current_data(weather_data)

            summarized = get_full_day_forecast(daily, hourly, current)

            current_crompt = daily_weather_prompt(summarized)

            try:
                advice = await get_ai_advice(current_crompt)
                await bot.send_message(chat_id=user.telegram_id, text=advice)
            except TelegramForbiddenError:
                pass
            except RuntimeError as e:
                await bot.send_message(chat_id=user.telegram_id, text=e)
                await bot.send_message(
                    chat_id=user.telegram_id, text="Держи просто сухой прогноз:"
                )
                await bot.send_message(chat_id=user.telegram_id, text=summarized)


async def check_rain():
    async with async_session() as session:
        user_dao = UserDAO(session)
        setting_dao = UserSettingDAO(session)
        users = await user_dao.get_all_for_rain_alert()

        for user in users:

            weather_data = await get_predict_rain_data(user.location)
            current = extract_current_data(weather_data)
            minutely = extract_minutely_data(weather_data)
            predict = get_minutely_forecast(
                current, minutely, user.setting.rain_threshold
            )
            if predict is None:
                if user.setting.is_raining_now:
                    await setting_dao.set_is_raining_now(user.telegram_id, False)
                continue

            if user.setting.is_raining_now:
                continue

            prompt = predict_rain_prompt(predict)
            try:
                advice = await get_ai_advice(prompt)
                await bot.send_message(chat_id=user.telegram_id, text=advice)
            except TelegramForbiddenError:
                pass
            except RuntimeError as e:
                await bot.send_message(chat_id=user.telegram_id, text=e)
                await bot.send_message(
                    chat_id=user.telegram_id, text="Скоро дождь, вот чуть подробнее:"
                )
                await bot.send_message(chat_id=user.telegram_id, text=predict)
            finally:
                await setting_dao.set_is_raining_now(user.telegram_id, True)


async def main():
    await init_models()
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")

    scheduler.add_job(
        send_daily_weather,
        trigger="interval",
        minutes=1,
    )
    scheduler.add_job(check_rain, trigger="interval", minutes=30)
    scheduler.start()

    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.include_router(coms_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
