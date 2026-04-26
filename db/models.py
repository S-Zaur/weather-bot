from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class BotState(Base):
    __tablename__ = "bot_state"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column()
