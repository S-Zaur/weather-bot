from enum import Enum, StrEnum


class WindDirection(StrEnum):
    NORTH = "северный"
    NORTH_EAST = "северо-восточный"
    EAST = "восточный"
    SOUTH_EAST = "юго-восточный"
    SOUTH = "южный"
    SOUTH_WEST = "юго-западный"
    WEST = "западный"
    NORTH_WEST = "северо-западный"

    @classmethod
    def from_degrees(cls, degrees: float) -> "WindDirection":
        directions = list(cls)
        index = int((degrees + 22.5) // 45) % 8
        return directions[index]


class DayPeriod(Enum):
    MORNING = "утро"
    DAY = "день"
    EVENING = "вечер"
    NIGHT = "ночь"

    @classmethod
    def get_period(cls, hour: int) -> "DayPeriod":
        if 6 <= hour < 12:
            return cls.MORNING
        if 12 <= hour < 18:
            return cls.DAY
        if 18 <= hour < 24:
            return cls.EVENING
        return cls.NIGHT

    @property
    def instrumental(self) -> str:
        """Творительный падеж"""
        cases = {
            "утро": "утром",
            "день": "днем",
            "вечер": "вечером",
            "ночь": "ночью",
        }
        return cases[self.value]

    @property
    def genitive(self) -> str:
        """Родительный падеж"""
        cases = {
            "утро": "утра",
            "день": "дня",
            "вечер": "вечера",
            "ночь": "ночи",
        }
        return cases[self.value]
