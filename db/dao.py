from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Type

from db.models import Location, User, UserSetting

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> ModelType:
        result = await self.session.get(self.model, id)
        return result


class UserDAO(BaseDAO[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def add_user(self, telegram_id: int, username: str):
        self.session.add(User(telegram_id=telegram_id, username=username))
        await self.session.commit()

    async def get_with_location(self, telegram_id: int):
        query = (
            select(User)
            .filter_by(telegram_id=telegram_id)
            .options(joinedload(User.location))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_setting(self, telegram_id: int):
        query = (
            select(User)
            .filter_by(telegram_id=telegram_id)
            .options(joinedload(User.setting))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all_for_daily_report(self, target_time: time):
        query = (
            select(User)
            .join(UserSetting)
            .filter(
                UserSetting.daily_report_enabled == True,
                UserSetting.report_time == target_time,
            )
            .options(joinedload(User.location))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_for_rain_alert(self):
        query = (
            select(User)
            .join(UserSetting)
            .filter(
                UserSetting.rain_alert_enabled == True,
            )
            .options(joinedload(User.location))
            .options(joinedload(User.setting))
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class LocationDAO(BaseDAO[Location]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Location)

    async def add_location(self, user_id, lat, lon, name):
        self.session.add(Location(user_id=user_id, name=name, lat=lat, lon=lon))
        await self.session.commit()

    async def update_or_create(self, user_id: int, lat: float, lon: float, name: str):
        location = await self.session.get(Location, user_id)
        if location:
            location.lat = lat
            location.lon = lon
            location.name = name
        else:
            location = Location(user_id=user_id, lat=lat, lon=lon, name=name)
            self.session.add(location)
        await self.session.commit()
        return location


class UserSettingDAO(BaseDAO[UserSetting]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSetting)

    async def default(self, user_id: int):
        self.session.add(UserSetting(user_id=user_id))
        await self.session.commit()

    async def toggle_daily_report(self, user_id: int):
        setting = await self.session.get(UserSetting, user_id)
        setting.daily_report_enabled = not setting.daily_report_enabled
        await self.session.commit()
        return setting

    async def toggle_rain_alert(self, user_id: int):
        setting = await self.session.get(UserSetting, user_id)
        setting.rain_alert_enabled = not setting.rain_alert_enabled
        await self.session.commit()
        return setting

    async def change_report_time(self, user_id: int, report_time: time):
        setting = await self.session.get(UserSetting, user_id)
        setting.report_time = report_time
        await self.session.commit()
        return setting

    async def change_rain_th(self, user_id: int, threshold: float):
        setting = await self.session.get(UserSetting, user_id)
        setting.rain_threshold = threshold
        await self.session.commit()
        return setting

    async def set_is_raining_now(self, user_id: int, is_raining_now: bool):
        setting = await self.session.get(UserSetting, user_id)
        setting.is_raining_now = is_raining_now
        await self.session.commit()
        return setting
