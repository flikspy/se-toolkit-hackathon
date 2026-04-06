"""
Comprehensive tests for the Shared Grocery List backend.

Includes:
- Normal CRUD operations
- Agent parsing (happy paths)
- Counter-tests (edge cases, malformed input, attacks)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Base

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ============================================================
# HEALTH
# ============================================================

class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ============================================================
# CRUD — CREATE
# ============================================================

class TestCreateItem:
    def test_create_simple(self):
        r = client.post("/items", json={"name": "milk"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "milk"
        assert data["quantity"] == "1"
        assert data["is_bought"] is False

    def test_create_with_quantity(self):
        r = client.post("/items", json={"name": "eggs", "quantity": "12"})
        assert r.status_code == 200
        assert r.json()["quantity"] == "12"

    def test_create_with_category(self):
        r = client.post("/items", json={"name": "bread", "category": "bakery"})
        assert r.status_code == 200
        assert r.json()["category"] == "bakery"

    def test_create_empty_name(self):
        r = client.post("/items", json={"name": ""})
        assert r.status_code == 422

    def test_create_missing_name(self):
        r = client.post("/items", json={"quantity": "2"})
        assert r.status_code == 422


# ============================================================
# CRUD — READ
# ============================================================

class TestReadItems:
    def test_empty_list(self):
        r = client.get("/items")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_items(self):
        client.post("/items", json={"name": "a"})
        client.post("/items", json={"name": "b"})
        r = client.get("/items")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_order_by_created_desc(self):
        import time
        client.post("/items", json={"name": "first"})
        time.sleep(0.01)
        client.post("/items", json={"name": "second"})
        r = client.get("/items")
        assert r.json()[0]["name"] == "second"


# ============================================================
# CRUD — UPDATE
# ============================================================

class TestUpdateItem:
    def test_update_name(self):
        r = client.post("/items", json={"name": "old"})
        item_id = r.json()["id"]
        r = client.put(f"/items/{item_id}", json={"name": "new"})
        assert r.status_code == 200
        assert r.json()["name"] == "new"

    def test_update_nonexistent(self):
        r = client.put("/items/9999", json={"name": "x"})
        assert r.status_code == 404

    def test_partial_update(self):
        r = client.post("/items", json={"name": "milk", "quantity": "2"})
        item_id = r.json()["id"]
        r = client.put(f"/items/{item_id}", json={"quantity": "5"})
        assert r.json()["name"] == "milk"  # unchanged
        assert r.json()["quantity"] == "5"


# ============================================================
# CRUD — DELETE
# ============================================================

class TestDeleteItem:
    def test_delete_ok(self):
        r = client.post("/items", json={"name": "x"})
        item_id = r.json()["id"]
        r = client.delete(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["message"] == "Item deleted"
        assert client.get("/items").json() == []

    def test_delete_nonexistent(self):
        r = client.delete("/items/9999")
        assert r.status_code == 404


# ============================================================
# TOGGLE
# ============================================================

class TestToggleItem:
    def test_toggle_false_to_true(self):
        r = client.post("/items", json={"name": "x"})
        item_id = r.json()["id"]
        r = client.post(f"/items/{item_id}/toggle")
        assert r.json()["is_bought"] is True

    def test_toggle_back(self):
        r = client.post("/items", json={"name": "x"})
        item_id = r.json()["id"]
        client.post(f"/items/{item_id}/toggle")
        r = client.post(f"/items/{item_id}/toggle")
        assert r.json()["is_bought"] is False

    def test_toggle_nonexistent(self):
        r = client.post("/items/9999/toggle")
        assert r.status_code == 404


# ============================================================
# AGENT — HAPPY PATHS
# ============================================================

class TestAgentHappy:
    def test_single_item(self):
        r = client.post("/agent/add", json={"text": "add milk"})
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "milk"

    def test_multiple_items_with_and(self):
        r = client.post("/agent/add", json={"text": "add milk and eggs"})
        assert r.status_code == 200
        assert len(r.json()) == 2
        names = [i["name"] for i in r.json()]
        assert "milk" in names
        assert "egg" in names

    def test_multiple_items_with_comma(self):
        r = client.post("/agent/add", json={"text": "milk, eggs, bread"})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_digit_quantity(self):
        r = client.post("/agent/add", json={"text": "5 eggs"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "5"
        assert r.json()[0]["name"] == "egg"

    def test_number_word_quantity(self):
        r = client.post("/agent/add", json={"text": "eight eggs"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "8"

    def test_multi_word_number(self):
        r = client.post("/agent/add", json={"text": "twenty one chupa chups"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "21"
        assert r.json()[0]["name"] == "chupa chups"

    def test_category_detection(self):
        r = client.post("/agent/add", json={"text": "milk"})
        assert r.json()[0]["category"] == "dairy"

        r = client.post("/agent/add", json={"text": "bread"})
        assert r.json()[0]["category"] == "bakery"

        r = client.post("/agent/add", json={"text": "chicken"})
        assert r.json()[0]["category"] == "meat"

    def test_x_quantity_format(self):
        r = client.post("/agent/add", json={"text": "3x milk"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "3"


# ============================================================
# AGENT — COUNTER-TESTS (edge cases, malformed, attacks)
# ============================================================

class TestAgentCounter:
    def test_empty_text(self):
        r = client.post("/agent/add", json={"text": ""})
        assert r.status_code == 400

    def test_whitespace_only(self):
        r = client.post("/agent/add", json={"text": "   "})
        assert r.status_code == 400

    def test_only_filler_words(self):
        r = client.post("/agent/add", json={"text": "please add some"})
        assert r.status_code == 400

    def test_special_characters(self):
        r = client.post("/agent/add", json={"text": "@#$%^&*!"})
        # Should not crash — gets cleaned, may produce items or 400
        assert r.status_code in (200, 400)

    def test_very_long_string(self):
        long_text = "item " * 1000
        r = client.post("/agent/add", json={"text": long_text})
        # Should not crash
        assert r.status_code in (200, 400)

    def test_sql_injection_in_name(self):
        r = client.post("/agent/add", json={"text": "'; DROP TABLE grocery_items; --"})
        # Must NOT crash; DB should survive
        assert r.status_code in (200, 400)
        # Verify DB still works
        r2 = client.get("/items")
        assert r2.status_code == 200

    def test_xss_in_name(self):
        r = client.post("/agent/add", json={"text": "<script>alert('xss')</script>"})
        assert r.status_code == 200
        assert "<script>" not in r.json()[0]["name"].lower()

    def test_unicode_cyrillic(self):
        r = client.post("/agent/add", json={"text": "молоко"})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "молоко"

    def test_unicode_emoji(self):
        r = client.post("/agent/add", json={"text": "🥛 milk"})
        assert r.status_code == 200

    def test_emoji_only(self):
        r = client.post("/agent/add", json={"text": "🥛🍞🧀"})
        assert r.status_code in (200, 400)

    def test_numbers_everywhere(self):
        r = client.post("/agent/add", json={"text": "123 456 789"})
        assert r.status_code in (200, 400)

    def test_newlines_and_tabs(self):
        r = client.post("/agent/add", json={"text": "milk\neggs\tbread"})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_mixed_case(self):
        r = client.post("/agent/add", json={"text": "MILK AND EGGS"})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "milk"

    def test_extra_spaces(self):
        r = client.post("/agent/add", json={"text": "  milk  ,  eggs  "})
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_quantity_zero(self):
        r = client.post("/agent/add", json={"text": "0 milk"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "0"

    def test_negative_quantity(self):
        r = client.post("/agent/add", json={"text": "-5 eggs"})
        # Regex only matches positive digits, so name will be "-5 eggs"
        assert r.status_code in (200, 400)

    def test_floating_quantity(self):
        r = client.post("/agent/add", json={"text": "2.5 kg apples"})
        assert r.status_code in (200, 400)

    def test_huge_quantity(self):
        r = client.post("/agent/add", json={"text": "999999 items"})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "999999"

    def test_semicolons_as_separator(self):
        r = client.post("/agent/add", json={"text": "milk; eggs; bread"})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_no_unknown_number_word(self):
        r = client.post("/agent/add", json={"text": "bazillion eggs"})
        # "bazillion" is not in NUMBER_WORDS, so name="bazillion eggs" qty=1
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "1"

    def test_duplicate_items_created_separately(self):
        client.post("/agent/add", json={"text": "milk"})
        r = client.post("/agent/add", json={"text": "milk"})
        assert r.status_code == 200
        # Agent doesn't deduplicate — that's OK for V1
        all_items = client.get("/items").json()
        assert len(all_items) == 2

    def test_missing_text_field(self):
        r = client.post("/agent/add", json={})
        assert r.status_code == 422

    def test_text_as_number(self):
        r = client.post("/agent/add", json={"text": "42"})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "42"


# ============================================================
# API — GENERIC EDGE CASES
# ============================================================

class TestApiEdgeCases:
    def test_404_unknown_route(self):
        r = client.get("/nonexistent")
        assert r.status_code == 404

    def test_wrong_method(self):
        r = client.post("/health")  # health is GET only
        assert r.status_code == 405

    def test_malformed_json(self):
        r = client.post(
            "/items",
            content=b"{not json}",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_concurrent_creates(self):
        import concurrent.futures

        def create(i):
            return client.post("/items", json={"name": f"item-{i}"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(create, range(10)))
        assert all(r.status_code == 200 for r in results)
        assert len(client.get("/items").json()) == 10
