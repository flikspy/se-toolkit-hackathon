from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import secrets

Base = declarative_base()


def generate_room_code() -> str:
    """Generate a 6-character uppercase room code."""
    return secrets.token_urlsafe(4)[:6].upper()


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True, default=generate_room_code)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("GroceryItem", back_populates="room")


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    quantity = Column(String, default="1")
    category = Column(String, default="other")
    is_bought = Column(Boolean, default=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    added_by = Column(String, default="anonymous")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    room = relationship("Room", back_populates="items")
