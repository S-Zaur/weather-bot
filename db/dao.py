from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Type

from db.models import BotState, Location, User

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> ModelType:
        result = await self.session.get(self.model, id)
        return result


class StateDAO(BaseDAO[BotState]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BotState)

    async def get_state(self, key: str) -> str | None:
        result = await self.session.execute(select(BotState).where(BotState.key == key))
        obj = result.scalar_one_or_none()
        return obj.value if obj else None

    async def set_state(self, key: str, value: str):
        result = await self.session.execute(select(BotState).where(BotState.key == key))
        obj = result.scalar_one_or_none()

        if obj:
            obj.value = value
        else:
            self.session.add(BotState(key=key, value=value))

        await self.session.commit()


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

    async def get_all_with_locations(self):
        query = select(User).options(joinedload(User.location))
        result = await self.session.execute(query)
        return result.scalars().all()


class LocationDAO(BaseDAO[Location]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Location)

    async def add_location(self, lat, lon, name, user_id):
        self.session.add(Location(user_id=user_id, name=name, lat=lat, lon=lon))
        await self.session.commit()
