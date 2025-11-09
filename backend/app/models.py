from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String(1000), default="")
