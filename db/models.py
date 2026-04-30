from datetime import time

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, ForeignKey, String, Time

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
    setting: Mapped["UserSetting"] = relationship(back_populates="user", uselist=False)


class Location(Base):
    __tablename__ = "locations"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), primary_key=True, autoincrement=False
    )

    name: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="location")


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id"), primary_key=True
    )

    daily_report_enabled: Mapped[bool] = mapped_column(default=True)
    report_time: Mapped[time] = mapped_column(Time, default=time(8, 0))

    rain_alert_enabled: Mapped[bool] = mapped_column(default=True)
    rain_threshold: Mapped[float] = mapped_column(default=0.1)

    user: Mapped["User"] = relationship(back_populates="setting")
