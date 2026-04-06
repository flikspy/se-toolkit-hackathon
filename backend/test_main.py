"""
Comprehensive tests for the Shared Grocery List backend.

Includes:
- Room creation and isolation
- CRUD operations within rooms
- Agent parsing (happy paths + counter-tests)
- Edge cases, malformed input, security tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Base

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
# ROOM
# ============================================================

class TestRoom:
    def test_create_room(self):
        r = client.post("/rooms")
        assert r.status_code == 200
        data = r.json()
        assert "code" in data
        assert len(data["code"]) == 6
        assert data["code"].isupper()

    def test_join_room(self):
        r = client.post("/rooms")
        code = r.json()["code"]
        r = client.get(f"/rooms/{code}")
        assert r.status_code == 200
        assert r.json()["code"] == code

    def test_join_invalid_code(self):
        r = client.get("/rooms/NOPEXX")
        assert r.status_code == 404

    def test_room_isolation(self):
        r1 = client.post("/rooms")
        r2 = client.post("/rooms")
        code1 = r1.json()["code"]
        code2 = r2.json()["code"]

        client.post(f"/rooms/{code1}/items", json={"name": "milk"})
        client.post(f"/rooms/{code2}/items", json={"name": "bread"})

        items1 = client.get(f"/rooms/{code1}/items").json()
        items2 = client.get(f"/rooms/{code2}/items").json()
        assert len(items1) == 1 and items1[0]["name"] == "milk"
        assert len(items2) == 1 and items2[0]["name"] == "bread"

    def test_unique_codes(self):
        codes = set()
        for _ in range(50):
            r = client.post("/rooms")
            codes.add(r.json()["code"])
        assert len(codes) == 50  # all unique


# ============================================================
# CRUD — CREATE
# ============================================================

class TestCreateItem:
    def test_create_simple(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "milk"})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "milk"
        assert data["quantity"] == "1"
        assert data["is_bought"] is False
        assert data["room_id"] == room["id"]

    def test_create_with_quantity(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "eggs", "quantity": "12"})
        assert r.status_code == 200
        assert r.json()["quantity"] == "12"

    def test_create_with_category(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "bread", "category": "bakery"})
        assert r.status_code == 200
        assert r.json()["category"] == "bakery"

    def test_create_empty_name(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": ""})
        assert r.status_code == 422

    def test_create_missing_name(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"quantity": "2"})
        assert r.status_code == 422

    def test_create_in_nonexistent_room(self):
        r = client.post("/rooms/FAKE/items", json={"name": "milk"})
        assert r.status_code == 404


# ============================================================
# CRUD — READ
# ============================================================

class TestReadItems:
    def test_empty_room(self):
        room = client.post("/rooms").json()
        r = client.get(f"/rooms/{room['code']}/items")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_items(self):
        room = client.post("/rooms").json()
        client.post(f"/rooms/{room['code']}/items", json={"name": "a"})
        client.post(f"/rooms/{room['code']}/items", json={"name": "b"})
        r = client.get(f"/rooms/{room['code']}/items")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_order_by_created_desc(self):
        import time
        room = client.post("/rooms").json()
        client.post(f"/rooms/{room['code']}/items", json={"name": "first"})
        time.sleep(0.01)
        client.post(f"/rooms/{room['code']}/items", json={"name": "second"})
        r = client.get(f"/rooms/{room['code']}/items")
        assert r.json()[0]["name"] == "second"

    def test_nonexistent_room_items(self):
        r = client.get("/rooms/FAKE/items")
        assert r.status_code == 404


# ============================================================
# CRUD — UPDATE
# ============================================================

class TestUpdateItem:
    def test_update_name(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "old"})
        item_id = r.json()["id"]
        r = client.put(f"/rooms/{room['code']}/items/{item_id}", json={"name": "new"})
        assert r.status_code == 200
        assert r.json()["name"] == "new"

    def test_update_nonexistent(self):
        room = client.post("/rooms").json()
        r = client.put(f"/rooms/{room['code']}/items/9999", json={"name": "x"})
        assert r.status_code == 404

    def test_partial_update(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "milk", "quantity": "2"})
        item_id = r.json()["id"]
        r = client.put(f"/rooms/{room['code']}/items/{item_id}", json={"quantity": "5"})
        assert r.json()["name"] == "milk"
        assert r.json()["quantity"] == "5"


# ============================================================
# CRUD — DELETE
# ============================================================

class TestDeleteItem:
    def test_delete_ok(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "x"})
        item_id = r.json()["id"]
        r = client.delete(f"/rooms/{room['code']}/items/{item_id}")
        assert r.status_code == 200
        assert client.get(f"/rooms/{room['code']}/items").json() == []

    def test_delete_nonexistent(self):
        room = client.post("/rooms").json()
        r = client.delete(f"/rooms/{room['code']}/items/9999")
        assert r.status_code == 404


# ============================================================
# TOGGLE
# ============================================================

class TestToggleItem:
    def test_toggle_false_to_true(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "x"})
        item_id = r.json()["id"]
        r = client.post(f"/rooms/{room['code']}/items/{item_id}/toggle")
        assert r.json()["is_bought"] is True

    def test_toggle_back(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items", json={"name": "x"})
        item_id = r.json()["id"]
        client.post(f"/rooms/{room['code']}/items/{item_id}/toggle")
        r = client.post(f"/rooms/{room['code']}/items/{item_id}/toggle")
        assert r.json()["is_bought"] is False

    def test_toggle_nonexistent(self):
        room = client.post("/rooms").json()
        r = client.post(f"/rooms/{room['code']}/items/9999/toggle")
        assert r.status_code == 404


# ============================================================
# AGENT — HAPPY PATHS
# ============================================================

class TestAgentHappy:
    def _room_code(self):
        return client.post("/rooms").json()["code"]

    def test_single_item(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "add milk", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "milk"

    def test_multiple_items_with_and(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "add milk and eggs", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 2
        names = [i["name"] for i in r.json()]
        assert "milk" in names
        assert "egg" in names

    def test_multiple_items_with_comma(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "milk, eggs, bread", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_digit_quantity(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "5 eggs", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "5"
        assert r.json()[0]["name"] == "egg"

    def test_number_word_quantity(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "eight eggs", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "8"

    def test_multi_word_number(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "twenty one chupa chups", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "21"
        assert r.json()[0]["name"] == "chupa chups"

    def test_category_detection(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "milk", "room_code": code})
        assert r.json()[0]["category"] == "dairy"

        r = client.post("/agent/add", json={"text": "bread", "room_code": code})
        assert r.json()[0]["category"] == "bakery"

    def test_x_quantity_format(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "3x milk", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "3"

    def test_agent_respects_room(self):
        r1 = client.post("/rooms").json()
        r2 = client.post("/rooms").json()
        client.post("/agent/add", json={"text": "milk", "room_code": r1["code"]})
        items_r2 = client.get(f"/rooms/{r2['code']}/items").json()
        assert len(items_r2) == 0


# ============================================================
# AGENT — COUNTER-TESTS
# ============================================================

class TestAgentCounter:
    def _room_code(self):
        return client.post("/rooms").json()["code"]

    def test_empty_text(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "", "room_code": code})
        assert r.status_code == 400

    def test_whitespace_only(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "   ", "room_code": code})
        assert r.status_code == 400

    def test_only_filler_words(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "please add some", "room_code": code})
        assert r.status_code == 400

    def test_special_characters(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "@#$%^&*!", "room_code": code})
        assert r.status_code in (200, 400)

    def test_very_long_string(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "item " * 1000, "room_code": code})
        assert r.status_code in (200, 400)

    def test_sql_injection_in_name(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "'; DROP TABLE grocery_items; --", "room_code": code})
        assert r.status_code in (200, 400)
        r2 = client.get(f"/rooms/{code}/items")
        assert r2.status_code == 200

    def test_xss_in_name(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "<script>alert('xss')</script>", "room_code": code})
        assert r.status_code == 200
        assert "<script>" not in r.json()[0]["name"].lower()

    def test_unicode_cyrillic(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "молоко", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "молоко"

    def test_unicode_emoji(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "🥛 milk", "room_code": code})
        assert r.status_code == 200

    def test_newlines_and_tabs(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "milk\neggs\tbread", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_mixed_case(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "MILK AND EGGS", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "milk"

    def test_extra_spaces(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "  milk  ,  eggs  ", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_quantity_zero(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "0 milk", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "0"

    def test_floating_quantity(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "2.5 kg apples", "room_code": code})
        assert r.status_code in (200, 400)

    def test_huge_quantity(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "999999 items", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "999999"

    def test_semicolons_as_separator(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "milk; eggs; bread", "room_code": code})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_no_unknown_number_word(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "bazillion eggs", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["quantity"] == "1"

    def test_duplicate_items_created_separately(self):
        code = self._room_code()
        client.post("/agent/add", json={"text": "milk", "room_code": code})
        r = client.post("/agent/add", json={"text": "milk", "room_code": code})
        assert r.status_code == 200
        assert len(client.get(f"/rooms/{code}/items").json()) == 2

    def test_missing_text_field(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"room_code": code})
        assert r.status_code == 422

    def test_missing_room_code(self):
        r = client.post("/agent/add", json={"text": "milk"})
        assert r.status_code == 422

    def test_invalid_room_code(self):
        r = client.post("/agent/add", json={"text": "milk", "room_code": "INVALID"})
        assert r.status_code == 404

    def test_text_as_number(self):
        code = self._room_code()
        r = client.post("/agent/add", json={"text": "42", "room_code": code})
        assert r.status_code == 200
        assert r.json()[0]["name"] == "42"


# ============================================================
# API — GENERIC EDGE CASES
# ============================================================

class TestApiEdgeCases:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_404_unknown_route(self):
        r = client.get("/nonexistent")
        assert r.status_code == 404

    def test_wrong_method(self):
        r = client.post("/health")
        assert r.status_code == 405

    def test_malformed_json(self):
        r = client.post(
            "/rooms/ABCD/items",
            content=b"{not json}",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_concurrent_creates(self):
        import concurrent.futures
        room = client.post("/rooms").json()

        def create(i):
            return client.post(f"/rooms/{room['code']}/items", json={"name": f"item-{i}"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(create, range(10)))
        assert all(r.status_code == 200 for r in results)
        assert len(client.get(f"/rooms/{room['code']}/items").json()) == 10
