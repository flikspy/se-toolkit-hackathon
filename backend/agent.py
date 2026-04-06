from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import re

from database import get_db
from models import GroceryItem
import schemas, crud

router = APIRouter()

# Simple category mapping
CATEGORIES = {
    'milk': 'dairy', 'cheese': 'dairy', 'yogurt': 'dairy', 'butter': 'dairy', 'cream': 'dairy',
    'bread': 'bakery', 'bun': 'bakery', 'bagel': 'bakery',
    'chicken': 'meat', 'beef': 'meat', 'pork': 'meat', 'sausage': 'meat',
    'apple': 'produce', 'banana': 'produce', 'tomato': 'produce', 'onion': 'produce',
    'carrot': 'produce', 'lettuce': 'produce', 'potato': 'produce',
    'rice': 'grains', 'pasta': 'grains', 'cereal': 'grains', 'oats': 'grains',
    'egg': 'dairy', 'eggs': 'dairy',
}


def parse_natural_language(text: str) -> List[schemas.GroceryItemCreate]:
    """Parse natural language text into grocery items."""
    text = text.lower().strip()
    
    # Remove common filler words
    text = re.sub(r'\b(add|buy|get|need|please|some|and|also|to|list|my|our|the|for|from)\b', ' ', text)
    text = re.sub(r'[^\w\s,;]', '', text)
    
    # Split by common delimiters
    items_text = re.split(r'[,;\n]+', text)
    
    items = []
    for item_text in items_text:
        item_text = item_text.strip()
        if not item_text:
            continue
        
        # Try to extract quantity (e.g. "2 milk", "3x eggs")
        qty_match = re.match(r'^(\d+)\s*(?:x\s*)?(.+)$', item_text)
        if qty_match:
            qty = qty_match.group(1)
            name = qty_match.group(2).strip()
        else:
            qty = '1'
            name = item_text
        
        # Handle plural -> singular
        if name.endswith('s') and len(name) > 3:
            singular = name[:-1]
            if singular in CATEGORIES:
                name = singular
        
        # Determine category
        category = 'other'
        for keyword, cat in CATEGORIES.items():
            if keyword in name:
                category = cat
                break
        
        items.append(schemas.GroceryItemCreate(
            name=name,
            quantity=qty,
            category=category
        ))
    
    return items


class AgentRequest(BaseModel):
    text: str


@router.post("/agent/add", response_model=List[schemas.GroceryItem])
def agent_add(request: AgentRequest, db: Session = Depends(get_db)):
    """Add items via natural language input."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty input")
    
    parsed_items = parse_natural_language(request.text)
    if not parsed_items:
        raise HTTPException(status_code=400, detail="Could not parse any items")
    
    created = []
    for item in parsed_items:
        created.append(crud.create_item(db, item))
    
    return created
