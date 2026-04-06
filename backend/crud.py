from sqlalchemy.orm import Session
from models import GroceryItem, Room
import schemas
from typing import List


# --- Room ---

def create_room(db: Session) -> Room:
    room = Room()
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def get_room_by_code(db: Session, code: str) -> Room | None:
    return db.query(Room).filter(Room.code == code.upper()).first()


# --- Grocery Items ---

def get_items(db: Session, room_id: int, skip: int = 0, limit: int = 100) -> List[GroceryItem]:
    return (
        db.query(GroceryItem)
        .filter(GroceryItem.room_id == room_id)
        .order_by(GroceryItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_item(db: Session, item: schemas.GroceryItemCreate, room_id: int) -> GroceryItem:
    data = item.model_dump()
    data['room_id'] = room_id
    db_item = GroceryItem(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, room_id: int, item_update: schemas.GroceryItemUpdate) -> GroceryItem | None:
    db_item = db.query(GroceryItem).filter(
        GroceryItem.id == item_id,
        GroceryItem.room_id == room_id
    ).first()
    if db_item is None:
        return None
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int, room_id: int) -> bool:
    db_item = db.query(GroceryItem).filter(
        GroceryItem.id == item_id,
        GroceryItem.room_id == room_id
    ).first()
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True


def toggle_bought(db: Session, item_id: int, room_id: int) -> GroceryItem | None:
    db_item = db.query(GroceryItem).filter(
        GroceryItem.id == item_id,
        GroceryItem.room_id == room_id
    ).first()
    if db_item is None:
        return None
    db_item.is_bought = not db_item.is_bought
    db.commit()
    db.refresh(db_item)
    return db_item
