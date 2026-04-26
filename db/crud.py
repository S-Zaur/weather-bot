from sqlalchemy import select
from db.database import async_session
from db.models import BotState


async def get_state(key: str) -> str | None:
    async with async_session() as session:
        result = await session.execute(select(BotState).where(BotState.key == key))
        obj = result.scalar_one_or_none()
        return obj.value if obj else None


async def set_state(key: str, value: str):
    async with async_session() as session:
        result = await session.execute(select(BotState).where(BotState.key == key))
        obj = result.scalar_one_or_none()

        if obj:
            obj.value = value
        else:
            session.add(BotState(key=key, value=value))

        await session.commit()
