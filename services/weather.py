import openmeteo_requests
import openmeteo_sdk
import requests_cache
from retry_requests import retry
from collections import Counter
from config import LAT, LON
from services.utils import get_non_zero_ranges, get_weather_desc, get_wind_direction

async def get_weather_data_for_day() -> openmeteo_sdk.WeatherApiResponse:
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "forecast_days":1,
        "current":["weather_code","temperature_2m","apparent_temperature","wind_speed_10m","wind_direction_10m","wind_gusts_10m", "rain"],
        "daily":["rain_sum","precipitation_probability_max", "uv_index_max"],
        "hourly":["temperature_2m","wind_speed_10m","wind_direction_10m", "wind_gusts_10m","rain","precipitation_probability"],
    }

    responses = openmeteo.weather_api(url, params = params)
    return responses[0]

async def get_rain_data() -> openmeteo_sdk.WeatherApiResponse:
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "current":["weather_code","temperature_2m","apparent_temperature","wind_speed_10m","wind_direction_10m","wind_gusts_10m", "rain"],
        "minutely_15": ["rain", "precipitation_probability"],
        "forecast_minutely_15": 24,
    }

    responses = openmeteo.weather_api(url, params = params)
    return responses[0]

def extract_daily_data(response:openmeteo_sdk.WeatherApiResponse)->dict:
    rain_sum = round(response.Daily().Variables(0).Values(0),1)
    prob_max = round(response.Daily().Variables(1).Values(0),1)
    uv_index =round(response.Daily().Variables(2).Values(0),1)
    return {
        "rain_sum": rain_sum,
        "prob_max": prob_max,
        "uv_index": uv_index
    }

def extract_hourly_data(response:openmeteo_sdk.WeatherApiResponse)->dict:
    hourly_temperature = [round(response.Hourly().Variables(0).Values(i),1) for i in range(response.Hourly().Variables(0).ValuesLength())]
    hourly_wind_speed = [round(response.Hourly().Variables(1).Values(i),1) for i in range(response.Hourly().Variables(1).ValuesLength())]
    hourly_wind_direction = [get_wind_direction(response.Hourly().Variables(2).Values(i)) for i in range(response.Hourly().Variables(2).ValuesLength())]
    hourly_wind_gusts = [round(response.Hourly().Variables(3).Values(i)) for i in range(response.Hourly().Variables(3).ValuesLength())]
    rain = [round(response.Hourly().Variables(4).Values(i),1) for i in range(response.Hourly().Variables(4).ValuesLength())]
    prob = [round(response.Hourly().Variables(5).Values(i),1) for i in range(response.Hourly().Variables(5).ValuesLength())]
    return {
        "temperature": hourly_temperature,
        "wind_speed": hourly_wind_speed,
        "wind_direction":hourly_wind_direction,
        "wind_gusts":hourly_wind_gusts,
        "rain": rain,
        "prob": prob
    }

def extract_minutely_data(response:openmeteo_sdk.WeatherApiResponse)-> dict:
    rain_minutely = [round(response.Minutely15().Variables(0).Values(i),1) for i in range(response.Minutely15().Variables(0).ValuesLength())]
    precipitation_minutely = [round(response.Minutely15().Variables(1).Values(i),1) for i in range(response.Minutely15().Variables(1).ValuesLength())]
    return [(rain_minutely[i], precipitation_minutely[i]) for i in range(response.Minutely15().Variables(0).ValuesLength())]

def extract_current_data(response:openmeteo_sdk.WeatherApiResponse)->dict:
    weather_desc, weather_emoji = get_weather_desc(response.Current().Variables(0).Value())
    temp = round(response.Current().Variables(1).Value(),1)
    apparent_temp = round(response.Current().Variables(2).Value(),1)
    wind_speed = round(response.Current().Variables(3).Value(),1)
    wind_direction = get_wind_direction(response.Current().Variables(4).Value())
    wind_gusts = round(response.Current().Variables(5).Value(),1)
    rain = round(response.Current().Variables(6).Value(),1)
    return {
        "desc": weather_desc,
        "emoji": weather_emoji,
        "temp": temp, 
        "apparent_temp": apparent_temp,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "wind_gusts": wind_gusts,
        "rain": rain
    }

def summarize_all_data(current_data:dict, hourly_data:dict, daily_data:dict)-> str:
    current = interpret_current_weather(current_data)
    morning = interpret_hourly_weather(hourly_data["temperature"][6:12], 
                             hourly_data["wind_speed"][6:12],
                             hourly_data["wind_direction"][6:12],
                             hourly_data["wind_gusts"][6:12])
    day = interpret_hourly_weather(hourly_data["temperature"][12:18], 
                             hourly_data["wind_speed"][12:18],
                             hourly_data["wind_direction"][12:18],
                             hourly_data["wind_gusts"][12:18])
    evening = interpret_hourly_weather(hourly_data["temperature"][18:24], 
                             hourly_data["wind_speed"][18:24],
                             hourly_data["wind_direction"][18:24],
                             hourly_data["wind_gusts"][18:24])
    rain = interpret_rain_data(daily_data, hourly_data)


    return f"""- Сейчас {current}
- Утром {morning}
- Днем {day}
- Вечером {evening}
- {rain}
- Максимальный УФ индекс за день: {daily_data["uv_index"]}"""

def interpret_current_weather(weather:dict)-> str:
    summ = f"{weather["desc"]}{weather["emoji"]}"
    temp = f"{weather["temp"]}°С ощущается как {weather["apparent_temp"]}°С"
    wind = f"{weather["wind_direction"]} ветер {weather["wind_speed"]} м/с с порывами до {weather["wind_gusts"]} м/с"
    rain = "без осадков" if weather["rain"]==0 else f"дождь интенсивностью {weather['rain']} мм/ч"
    return f"{summ}, {temp}, {wind}, {rain}"

def interpret_hourly_weather(temp, wind_speed, wind_direction, wind_gusts):
    temp_sum = f"температура от {min(temp)}°С до {max(temp)}°С"
    direction = Counter(wind_direction).most_common(1)[0][0]
    average = round(sum(wind_speed)/len(wind_speed),1)
    wind_sum = f"{direction} ветер {average} м/с с порывами до {max(wind_gusts)} м/с"
    return f"{temp_sum}, {wind_sum}"

def interpret_rain_data(daily_data:dict, hourly_data:dict)->str:
    if daily_data["rain_sum"] == 0:
        return "Сегодня осадков не ожидается"
    rain = hourly_data["rain"]
    prob = hourly_data["prob"]
    ranges = get_non_zero_ranges(rain)
    if len(ranges) == 0:
        return "Сегодня осадков не ожидается"
    letters = ('ь','') if len(ranges) == 1 else ('и', 'ы')
    rains = []
    for i in ranges:
        s = slice(*i)
        rains.append(f"с {i[0]} до {i[1]} часов с максимальной интенсивностью {max(rain[s])} мм/ч и вероятностью {max(prob[s])}%")
    return f"Сегодня ожидаются дожд{letters[0]} в период{letters[1]}: {', '.join(rains)}"