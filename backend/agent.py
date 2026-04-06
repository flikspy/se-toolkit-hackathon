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


# Number words mapping
NUMBER_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
    'hundred': 100, 'dozen': 12,
}


def parse_number_words(words: list) -> tuple[int, int] | None:
    """Try to parse leading number words like 'twenty one' → (21, 2)."""
    if not words:
        return None

    # Try multi-word: "twenty one" → 21
    for i in range(min(len(words), 3), 0, -1):
        parts = words[:i]
        # All parts must be valid number words
        if all(p in NUMBER_WORDS for p in parts):
            total = sum(NUMBER_WORDS[p] for p in parts)
            if total > 0:
                return (total, i)
    return None


def parse_natural_language(text: str) -> List[schemas.GroceryItemCreate]:
    """Parse natural language text into grocery items."""
    text = text.lower().strip()

    # Replace "and" with comma before removing it
    text = re.sub(r'\band\b', ',', text)

    # Remove other filler words
    text = re.sub(r'\b(add|buy|get|need|please|some|also|to|list|my|our|the|for|from)\b', ' ', text)
    text = re.sub(r'[^\w\s,;]', '', text)

    # Split by common delimiters (comma, semicolon, newline, tab)
    items_text = re.split(r'[,;\n\t]+', text)

    items = []
    for item_text in items_text:
        item_text = item_text.strip()
        if not item_text:
            continue

        # Try to extract digit quantity (e.g. "2 milk", "3x eggs", "3xeggs")
        qty_match = re.match(r'^(\d+)x?\s+(.+)$', item_text)
        if qty_match:
            qty = qty_match.group(1)
            name = qty_match.group(2).strip()
        else:
            # Check for number words (e.g. "twenty one chupa chups")
            words = item_text.split()
            num_result = parse_number_words(words)
            if num_result:
                qty = str(num_result[0])
                name = ' '.join(words[num_result[1]:])
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
