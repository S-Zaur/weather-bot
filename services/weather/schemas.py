from collections import Counter
from dataclasses import dataclass
from datetime import date, time

from services.enums import DayPeriod, WindDirection


@dataclass
class CurrentWeather:
    description: str
    emoji: str
    temp: float
    apparent_temp: float
    wind_speed: float
    wind_direction: float
    wind_gusts: float
    rain: float


@dataclass
class MinutelyWeather:
    t: time
    rain: float
    prob: float


@dataclass
class MinutelyForecast:
    minutes: list[MinutelyWeather]

    @property
    def max_rain(self) -> float:
        return max(x.rain for x in self.minutes)

    @property
    def max_prob(self) -> float:
        return max(x.prob for x in self.minutes)

    @property
    def rain_start_time(self):
        for minute in self.minutes:
            if minute.rain != 0:
                return minute.t
        return None


@dataclass
class HourlyWeather:
    hour: time
    temperature: float
    wind_speed: float
    wind_gusts: float
    wind_direction: WindDirection
    rain: float
    prob: float
    uv_index: float


@dataclass
class HourlyForecast:
    hours: list[HourlyWeather]
    day: date

    @property
    def is_empty(self) -> bool:
        return len(self.hours) == 0

    @property
    def max_temp(self) -> float:
        return max(x.temperature for x in self.hours)

    @property
    def min_temp(self) -> float:
        return min(x.temperature for x in self.hours)

    @property
    def avg_wind_speed(self) -> float:
        s = sum(x.wind_speed for x in self.hours)
        l = len(self.hours)
        return round(s / l, 1)

    @property
    def prevailing_wind_direction(self) -> str:
        return Counter(x.wind_direction for x in self.hours).most_common(1)[0][0]

    @property
    def max_gusts(self) -> float:
        return max(x.wind_gusts for x in self.hours)

    @property
    def max_uv(self) -> float:
        return max(x.uv_index for x in self.hours)

    @property
    def max_rain(self) -> float:
        return max(x.rain for x in self.hours)

    @property
    def max_prob(self) -> float:
        return max(x.prob for x in self.hours)

    @property
    def start(self) -> time:
        return self.hours[0].hour

    @property
    def end(self) -> time:
        return self.hours[-1].hour

    @property
    def rain_ranges(self) -> list["HourlyForecast"]:
        rain_events = []
        current_event = []
        for hour in self.hours:
            if hour.rain > 0:
                current_event.append(hour)
            else:
                if current_event:
                    rain_events.append(HourlyForecast(current_event, self.day))
                    current_event = []
        if current_event:
            rain_events.append(HourlyForecast(current_event))
        return rain_events

    def get_by_period(self, period: DayPeriod) -> "HourlyForecast":
        return HourlyForecast(
            hours=[
                h for h in self.hours if DayPeriod.get_period(h.hour.hour) == period
            ],
            day=self.day,
        )


@dataclass
class DailyWeather:
    rain_sum: float
    prob_max: float
