from sqlalchemy.orm import Session
from models import GroceryItem
import schemas
from typing import List


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[GroceryItem]:
    return db.query(GroceryItem).order_by(GroceryItem.created_at.desc()).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.GroceryItemCreate) -> GroceryItem:
    db_item = GroceryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, item_update: schemas.GroceryItemUpdate) -> GroceryItem | None:
    db_item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if db_item is None:
        return None
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    db_item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True


def toggle_bought(db: Session, item_id: int) -> GroceryItem | None:
    db_item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if db_item is None:
        return None
    db_item.is_bought = not db_item.is_bought
    db.commit()
    db.refresh(db_item)
    return db_item
