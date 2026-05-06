from datetime import datetime

from services.enums import DayPeriod
from services.weather.schemas import (
    CurrentWeather,
    DailyWeather,
    HourlyForecast,
    MinutelyForecast,
)


def get_current_forecast(current: CurrentWeather) -> str:
    summ = f"{current.description}{current.emoji}"
    temp = f"{current.temp}°С ощущается как {current.apparent_temp}°С"
    wind = f"{current.wind_direction} ветер {current.wind_speed} м/с с порывами до {current.wind_gusts} м/с"
    rain = (
        "без осадков"
        if current.rain == 0
        else f"дождь интенсивностью {current.rain} мм/ч"
    )
    return f"{summ}, {temp}, {wind}, {rain}"


def get_minutely_forecast(current: CurrentWeather, minutely: MinutelyForecast) -> str:
    start = minutely.rain_start_time
    if start is None:
        return None
    current_forecast = get_current_forecast(current)
    return f"{current_forecast}. Примерно в {start} начнется дождь с интенсивностью до {minutely.max_rain} мм/15мин и вероятностью {minutely.max_prob}%"


def _get_hourly_forecast(hourly: HourlyForecast) -> str:
    temp_sum = f"температура от {hourly.min_temp}°С до {hourly.max_temp}°С"
    wind_sum = f"{hourly.prevailing_wind_direction} ветер {hourly.avg_wind_speed} м/с с порывами до {hourly.max_gusts} м/с"
    uv_index_sum = f"УФ индекс до {hourly.max_uv}"
    return f"{temp_sum}, {wind_sum}, {uv_index_sum}"


def get_full_day_forecast(
    daily: DailyWeather, hourly: HourlyForecast, current: CurrentWeather
) -> str:
    current_forecast = get_current_forecast(current)
    morning = get_day_period_forecast(hourly, DayPeriod.MORNING)
    day = get_day_period_forecast(hourly, DayPeriod.DAY)
    evening = get_day_period_forecast(hourly, DayPeriod.EVENING)
    rain = get_rain_forecast(hourly, daily)
    return f"""- Сейчас {datetime.now().strftime('%H:%M')} {current_forecast}
- {morning}
- {day}
- {evening}
- {rain}"""


def get_day_period_forecast(hourly: HourlyForecast, period: DayPeriod) -> str:
    weather = hourly.get_by_period(period)
    forecast = _get_hourly_forecast(weather)
    return f"{period.instrumental} ожидается {forecast}"


def get_rain_forecast(hourly: HourlyForecast, daily: DailyWeather = None):
    if daily and daily.rain_sum == 0:
        return "Сегодня осадков не ожидается"
    rains = hourly.rain_ranges
    if not rains:
        return "Сегодня осадков не ожидается"
    letters = ("ь", "") if len(rains) == 1 else ("и", "ы")
    rains_text = [
        f"с {x.start} до {x.end} часов с максимальной интенсивностью {x.max_rain} мм/ч и вероятностью {x.max_prob}%"
        for x in rains
    ]
    return f"Сегодня ожидаются дожд{letters[0]} в период{letters[1]}: {', '.join(rains_text)}"


def get_tomorrow_forecast(hourly: HourlyForecast) -> str:
    morning = get_day_period_forecast(hourly, DayPeriod.MORNING)
    day = get_day_period_forecast(hourly, DayPeriod.DAY)
    evening = get_day_period_forecast(hourly, DayPeriod.EVENING)
    rain = get_rain_forecast(hourly)
    return f"""- Завтра {morning}
- {day}
- {evening}
Завтра {rain}"""
