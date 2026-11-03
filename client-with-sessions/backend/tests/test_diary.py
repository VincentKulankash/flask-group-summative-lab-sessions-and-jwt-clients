# OWNER: Allen (Quality & Docs)
# TASKS:
# 1. Test CRUD routes (Create, Read, Update, Delete).
# 2. Test pagination (page, per_page, total).
# 3. Test security: User A CANNOT read/edit/delete User B's entry (should get 404).

import pytest


def create_entry(client, title="My day", content="It was a good day.", mood="happy"):
    return client.post("/diary-entries", json={
        "title": title,
        "content": content,
        "mood": mood,
    })


# ---------- AUTH REQUIRED ----------

@pytest.mark.parametrize("method, url", [
    ("get", "/diary-entries"),
    ("post", "/diary-entries"),
    ("get", "/diary-entries/1"),
    ("patch", "/diary-entries/1"),
    ("delete", "/diary-entries/1"),
])
def test_diary_routes_require_login(client, method, url):
    res = getattr(client, method)(url, json={})

    assert res.status_code == 401
    assert res.get_json() == {"error": "Unauthorized. Please log in."}


# ---------- CREATE ----------

def test_create_entry(alice):
    res = create_entry(alice)

    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "My day"
    assert data["content"] == "It was a good day."
    assert data["mood"] == "happy"
    assert data["entry_date"] is not None


def test_create_entry_belongs_to_current_user(alice):
    me = alice.get("/auth/me").get_json()
    data = create_entry(alice).get_json()

    assert data["user_id"] == me["id"]


def test_create_entry_ignores_user_id_from_request(alice, bob):
    bob_id = bob.get("/auth/me").get_json()["id"]
    alice_id = alice.get("/auth/me").get_json()["id"]

    res = alice.post("/diary-entries", json={
        "title": "Sneaky",
        "content": "Trying to post as bob",
        "user_id": bob_id,
    })

    assert res.status_code == 201
    assert res.get_json()["user_id"] == alice_id


def test_create_entry_mood_is_optional(alice):
    res = alice.post("/diary-entries", json={"title": "No mood", "content": "Just text"})

    assert res.status_code == 201
    assert res.get_json()["mood"] is None


def test_create_entry_missing_title_returns_400(alice):
    res = alice.post("/diary-entries", json={"content": "No title"})

    assert res.status_code == 400
    assert "title" in res.get_json()["error"]


def test_create_entry_missing_content_returns_400(alice):
    res = alice.post("/diary-entries", json={"title": "No content"})

    assert res.status_code == 400
    assert "content" in res.get_json()["error"]


# ---------- READ ----------

def test_get_own_entry(alice):
    entry_id = create_entry(alice).get_json()["id"]

    res = alice.get(f"/diary-entries/{entry_id}")

    assert res.status_code == 200
    assert res.get_json()["id"] == entry_id


def test_get_missing_entry_returns_404(alice):
    res = alice.get("/diary-entries/9999")

    assert res.status_code == 404
    assert res.get_json() == {"error": "Resource not found"}


# ---------- UPDATE ----------

def test_patch_updates_only_given_fields(alice):
    entry_id = create_entry(alice).get_json()["id"]

    res = alice.patch(f"/diary-entries/{entry_id}", json={"title": "New title"})

    assert res.status_code == 200
    data = res.get_json()
    assert data["title"] == "New title"
    assert data["content"] == "It was a good day."
    assert data["mood"] == "happy"


def test_patch_invalid_data_returns_400(alice):
    entry_id = create_entry(alice).get_json()["id"]

    res = alice.patch(f"/diary-entries/{entry_id}", json={"title": ""})

    assert res.status_code == 400
    assert "title" in res.get_json()["error"]


# ---------- DELETE ----------

def test_delete_entry(alice):
    entry_id = create_entry(alice).get_json()["id"]

    res = alice.delete(f"/diary-entries/{entry_id}")

    assert res.status_code == 200
    assert res.get_json() == {"message": "Entry deleted"}
    assert alice.get(f"/diary-entries/{entry_id}").status_code == 404


# ---------- PAGINATION ----------

def test_list_defaults_to_page_1_with_10_per_page(alice):
    for i in range(15):
        create_entry(alice, title=f"Entry {i}")

    res = alice.get("/diary-entries")

    assert res.status_code == 200
    data = res.get_json()
    assert len(data["entries"]) == 10
    assert data["pagination"] == {"page": 1, "per_page": 10, "total": 15, "pages": 2}


def test_list_second_page(alice):
    for i in range(15):
        create_entry(alice, title=f"Entry {i}")

    data = alice.get("/diary-entries?page=2&per_page=10").get_json()

    assert len(data["entries"]) == 5
    assert data["pagination"]["page"] == 2


def test_list_custom_per_page(alice):
    for i in range(7):
        create_entry(alice, title=f"Entry {i}")

    data = alice.get("/diary-entries?page=1&per_page=3").get_json()

    assert len(data["entries"]) == 3
    assert data["pagination"] == {"page": 1, "per_page": 3, "total": 7, "pages": 3}


def test_list_page_past_the_end_is_empty(alice):
    create_entry(alice)

    data = alice.get("/diary-entries?page=5").get_json()

    assert data["entries"] == []
    assert data["pagination"]["total"] == 1


def test_list_is_newest_first(alice):
    for i in range(3):
        create_entry(alice, title=f"Entry {i}")

    titles = [e["title"] for e in alice.get("/diary-entries").get_json()["entries"]]

    assert titles == ["Entry 2", "Entry 1", "Entry 0"]


def test_list_only_shows_own_entries(alice, bob):
    create_entry(alice, title="Alice's entry")
    create_entry(bob, title="Bob's entry")

    data = alice.get("/diary-entries").get_json()

    assert [e["title"] for e in data["entries"]] == ["Alice's entry"]
    assert data["pagination"]["total"] == 1


@pytest.mark.parametrize("query", [
    "page=0",
    "page=abc",
    "per_page=0",
    "per_page=101",
])
def test_list_invalid_pagination_returns_400(alice, query):
    res = alice.get(f"/diary-entries?{query}")

    assert res.status_code == 400


def test_list_invalid_pagination_returns_json_error(alice):
    res = alice.get("/diary-entries?page=0")

    assert res.get_json() == {"error": "page must be a positive integer."}


# ---------- SECURITY: OWNERSHIP ----------

@pytest.fixture
def alice_entry_id(alice):
    return create_entry(alice, title="Alice's secret").get_json()["id"]


def test_other_user_cannot_read_entry(bob, alice_entry_id):
    res = bob.get(f"/diary-entries/{alice_entry_id}")

    assert res.status_code == 404


def test_other_user_cannot_update_entry(alice, bob, alice_entry_id):
    res = bob.patch(f"/diary-entries/{alice_entry_id}", json={"title": "Hacked"})

    assert res.status_code == 404
    assert alice.get(f"/diary-entries/{alice_entry_id}").get_json()["title"] == "Alice's secret"


def test_other_user_cannot_delete_entry(alice, bob, alice_entry_id):
    res = bob.delete(f"/diary-entries/{alice_entry_id}")

    assert res.status_code == 404
    assert alice.get(f"/diary-entries/{alice_entry_id}").status_code == 200
