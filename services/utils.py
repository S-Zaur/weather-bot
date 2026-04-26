from itertools import groupby
from services.weather_codes import WMO_WEATHER_CODES


def get_wind_direction(degrees: float) -> str:
    directions = [
        "Северный",
        "Северо-восточный",
        "Восточный",
        "Юго-восточный",
        "Южный",
        "Юго-западный",
        "Западный",
        "Северо-западный",
    ]
    index = int((degrees + 22.5) // 45) % 8
    return directions[index]


def get_weather_desc(code: int) -> list[str, str]:
    return WMO_WEATHER_CODES.get(
        code, {"text": "Неизвестная погода", "emoji": "❓"}
    ).values()


def get_non_zero_ranges(arr: list) -> list:
    ranges = []
    for key, group in groupby(enumerate(arr), key=lambda x: x[1] != 0):
        if key:
            items = list(group)
            ranges.append((items[0][0], items[-1][0] + 1))
    return ranges


def find_first_nonzero_index(arr):
    for index, value in enumerate(arr):
        if value != 0:
            return index
    return None
