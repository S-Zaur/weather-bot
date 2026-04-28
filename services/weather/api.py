import openmeteo_requests
import openmeteo_sdk
import requests_cache
from retry_requests import retry

from config import LAT, LON


async def get_weather_data_for_day() -> openmeteo_sdk.WeatherApiResponse:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "forecast_days": 1,
        "current": [
            "weather_code",
            "temperature_2m",
            "apparent_temperature",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "rain",
        ],
        "daily": ["rain_sum", "precipitation_probability_max"],
        "hourly": [
            "temperature_2m",
            "wind_speed_10m",
            "wind_gusts_10m",
            "wind_direction_10m",
            "rain",
            "precipitation_probability",
            "uv_index",
        ],
    }

    responses = openmeteo.weather_api(url, params=params)
    return responses[0]


async def get_predict_rain_data() -> openmeteo_sdk.WeatherApiResponse:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "current": [
            "weather_code",
            "temperature_2m",
            "apparent_temperature",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "rain",
        ],
        "minutely_15": [
            "rain",
            "precipitation_probability",
        ],
        "forecast_minutely_15": 12,
    }

    responses = openmeteo.weather_api(url, params=params)
    return responses[0]
