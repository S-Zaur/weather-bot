from zoneinfo import ZoneInfo

import openmeteo_sdk
from datetime import datetime, timedelta
from services.enums import WindDirection
from services.weather import schemas
from services.weather.codes import get_weather_desc


def extract_daily_data(
    response: openmeteo_sdk.WeatherApiResponse,
) -> schemas.DailyWeather:
    assert response.Daily().VariablesLength() == 2
    rain_sum = round(response.Daily().Variables(0).Values(0), 1)
    prob_max = round(response.Daily().Variables(1).Values(0), 1)
    return schemas.DailyWeather(rain_sum, prob_max)


def extract_hourly_data(
    response: openmeteo_sdk.WeatherApiResponse,
) -> schemas.HourlyForecast:
    hourly = response.Hourly()
    assert hourly.VariablesLength() == 7
    for i in range(7):
        assert hourly.Variables(i).ValuesLength() == 24
    lst = []
    delta = timedelta(hours=1)
    tz = ZoneInfo("Asia/Yekaterinburg")
    time = datetime.fromtimestamp(hourly.Time(), tz=tz)
    for i in range(24):
        lst.append(
            schemas.HourlyWeather(
                time,
                round(hourly.Variables(0).Values(i), 1),
                round(hourly.Variables(1).Values(i), 1),
                round(hourly.Variables(2).Values(i), 1),
                WindDirection.from_degrees(hourly.Variables(3).Values(i)),
                round(hourly.Variables(4).Values(i), 1),
                round(hourly.Variables(5).Values(i), 1),
                round(hourly.Variables(6).Values(i), 1),
            )
        )
        time += delta
    return schemas.HourlyForecast(lst, time.date)


def extract_minutely_data(
    response: openmeteo_sdk.WeatherApiResponse,
) -> schemas.MinutelyForecast:
    minutely = response.Minutely15()
    assert minutely.VariablesLength() == 2
    for i in range(2):
        assert minutely.Variables(i).ValuesLength() == 12
    lst = []
    delta = timedelta(minutes=15)
    tz = ZoneInfo("Asia/Yekaterinburg")
    time = datetime.fromtimestamp(minutely.Time(), tz=tz)
    for i in range(12):
        lst.append(
            schemas.MinutelyWeather(
                time,
                round(minutely.Variables(0).Values(i), 1),
                round(minutely.Variables(1).Values(i), 1),
            )
        )
        time += delta
    return schemas.MinutelyForecast(lst)


def extract_current_data(
    response: openmeteo_sdk.WeatherApiResponse,
) -> schemas.CurrentWeather:
    current = response.Current()
    assert current.VariablesLength() == 7
    return schemas.CurrentWeather(
        *get_weather_desc(current.Variables(0).Value()),
        round(response.Current().Variables(1).Value(), 1),
        round(response.Current().Variables(2).Value(), 1),
        round(response.Current().Variables(3).Value(), 1),
        WindDirection.from_degrees(current.Variables(4).Value()),
        round(response.Current().Variables(5).Value(), 1),
        round(response.Current().Variables(6).Value(), 1),
    )
