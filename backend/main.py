from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db
from models import Base
import crud, schemas
from agent import router as agent_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shared Grocery List", version="0.1.0")

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


# --- Grocery Items ---


@app.get("/items", response_model=List[schemas.GroceryItem])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_items(db, skip=skip, limit=limit)


@app.post("/items", response_model=schemas.GroceryItem)
def create_item(item: schemas.GroceryItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.put("/items/{item_id}", response_model=schemas.GroceryItem)
def update_item(item_id: int, item_update: schemas.GroceryItemUpdate, db: Session = Depends(get_db)):
    updated = crud.update_item(db, item_id, item_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


@app.post("/items/{item_id}/toggle", response_model=schemas.GroceryItem)
def toggle_item(item_id: int, db: Session = Depends(get_db)):
    updated = crud.toggle_bought(db, item_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated
