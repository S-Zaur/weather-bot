from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, ForeignKey, String

from db.database import Base


class BotState(Base):
    __tablename__ = "bot_state"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column()


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(100))
    location: Mapped["Location"] = relationship(back_populates="user", uselist=False)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))

    name: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="location")
