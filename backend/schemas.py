from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


# --- Room ---

class RoomCreate(BaseModel):
    pass


class Room(BaseModel):
    id: int
    code: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Grocery Items ---

class GroceryItemBase(BaseModel):
    name: str
    quantity: Optional[str] = "1"
    category: Optional[str] = "other"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class GroceryItemCreate(GroceryItemBase):
    pass


class GroceryItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[str] = None
    category: Optional[str] = None
    is_bought: Optional[bool] = None


class GroceryItem(GroceryItemBase):
    id: int
    is_bought: bool
    room_id: int
    added_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
