from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db
from models import Base
import crud, schemas
from agent import router as agent_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shared Grocery List", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Room ---

@app.post("/rooms", response_model=schemas.Room)
def create_room(db: Session = Depends(get_db)):
    """Create a new shared room and get its code."""
    return crud.create_room(db)


@app.get("/rooms/{code}", response_model=schemas.Room)
def join_room(code: str, db: Session = Depends(get_db)):
    """Join an existing room by its code."""
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


# --- Grocery Items ---

@app.get("/rooms/{code}/items", response_model=List[schemas.GroceryItem])
def read_items(code: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return crud.get_items(db, room_id=room.id, skip=skip, limit=limit)


@app.post("/rooms/{code}/items", response_model=schemas.GroceryItem)
def create_item(code: str, item: schemas.GroceryItemBase, db: Session = Depends(get_db)):
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    item_data = schemas.GroceryItemCreate(
        name=item.name,
        quantity=item.quantity,
        category=item.category,
        room_id=room.id
    )
    return crud.create_item(db, item_data, room.id)


@app.put("/rooms/{code}/items/{item_id}", response_model=schemas.GroceryItem)
def update_item(code: str, item_id: int, item_update: schemas.GroceryItemUpdate, db: Session = Depends(get_db)):
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    updated = crud.update_item(db, item_id, room.id, item_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/rooms/{code}/items/{item_id}")
def delete_item(code: str, item_id: int, db: Session = Depends(get_db)):
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    success = crud.delete_item(db, item_id, room.id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


@app.post("/rooms/{code}/items/{item_id}/toggle", response_model=schemas.GroceryItem)
def toggle_item(code: str, item_id: int, db: Session = Depends(get_db)):
    room = crud.get_room_by_code(db, code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    updated = crud.toggle_bought(db, item_id, room.id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated
