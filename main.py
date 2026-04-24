from services.ai_gen import prepare_weather_prompt, current_weather_prompt
from services.weather import get_weather_data_for_day, extract_current_data, extract_hourly_data, extract_daily_data, summarize_all_data
import asyncio

async def main():
    data = await get_weather_data_for_day()
    cur = extract_current_data(data)
    hourly = extract_hourly_data(data)
    daily = extract_daily_data(data)
    sum = summarize_all_data(cur, hourly, daily)
    print(prepare_weather_prompt(sum))
    print(current_weather_prompt(sum))


asyncio.run(main())