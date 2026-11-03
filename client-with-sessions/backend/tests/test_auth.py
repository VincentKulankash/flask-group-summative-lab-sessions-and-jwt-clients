# OWNER: Allen (Quality & Docs)
# TASKS:
# 1. Use in-memory SQLite database via TestingConfig.
# 2. Test: Signup, Login, /auth/me, Logout.
# 3. Ensure session cookies persist between test client requests.

from models import User
from tests.conftest import signup, login, PASSWORD


# ---------- SIGNUP ----------

def test_signup_creates_user(client):
    res = signup(client, "alice")

    assert res.status_code == 201
    data = res.get_json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_signup_never_returns_password(client):
    data = signup(client, "alice").get_json()

    assert "password" not in data
    assert "password_hash" not in data


def test_signup_stores_hashed_password(app, client):
    signup(client, "alice")

    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        assert user.password_hash != PASSWORD
        assert user.check_password(PASSWORD)


def test_signup_duplicate_username_returns_409(client):
    signup(client, "alice")
    res = signup(client, "ALICE", email="other@example.com")

    assert res.status_code == 409
    assert res.get_json() == {"error": "Username already exists."}


def test_signup_duplicate_email_returns_409(client):
    signup(client, "alice")
    res = signup(client, "alice2", email="Alice@Example.com")

    assert res.status_code == 409
    assert res.get_json() == {"error": "Email already exists."}


def test_signup_invalid_email_returns_422(client):
    res = signup(client, "alice", email="not-an-email")

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_signup_short_password_returns_422(client):
    res = signup(client, "alice", password="short")

    assert res.status_code == 422
    assert res.get_json() == {"error": "Password must be at least 8 characters long."}


def test_signup_missing_fields_returns_422(client):
    res = client.post("/auth/signup", json={"username": "alice"})

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_signup_without_json_body_returns_422(client):
    res = client.post("/auth/signup", data="not json", content_type="text/plain")

    assert res.status_code == 422
    assert "error" in res.get_json()


# ---------- LOGIN ----------

def test_login_success_sets_session_cookie(client):
    signup(client, "alice")
    res = login(client, "alice")

    assert res.status_code == 200
    assert res.get_json()["username"] == "alice"
    assert "password_hash" not in res.get_json()
    assert "session=" in res.headers.get("Set-Cookie", "")


def test_login_username_is_case_insensitive(client):
    signup(client, "alice")
    res = login(client, "ALICE")

    assert res.status_code == 200


def test_login_wrong_password_returns_401(client):
    signup(client, "alice")
    res = login(client, "alice", password="wrongpassword")

    assert res.status_code == 401
    assert res.get_json() == {"error": "Invalid username or password."}


def test_login_unknown_user_returns_401(client):
    res = login(client, "nobody")

    assert res.status_code == 401
    assert res.get_json() == {"error": "Invalid username or password."}


def test_login_missing_fields_returns_422(client):
    res = client.post("/auth/login", json={"username": "alice"})

    assert res.status_code == 422
    assert "error" in res.get_json()


# ---------- /auth/me (session persistence) ----------

def test_me_requires_login(client):
    res = client.get("/auth/me")

    assert res.status_code == 401
    assert res.get_json() == {"error": "Unauthorized. Please log in."}


def test_me_returns_current_user_after_login(client):
    signup(client, "alice")
    login(client, "alice")

    # The test client keeps the session cookie, so this request is authenticated.
    res = client.get("/auth/me")

    assert res.status_code == 200
    assert res.get_json()["username"] == "alice"
    assert "password_hash" not in res.get_json()


def test_session_is_per_client(app, alice):
    # A different client has no cookie, so it is not logged in.
    other = app.test_client()

    assert alice.get("/auth/me").status_code == 200
    assert other.get("/auth/me").status_code == 401


# ---------- LOGOUT ----------

def test_logout_clears_session(alice):
    res = alice.post("/auth/logout")

    assert res.status_code == 200
    assert res.get_json() == {"message": "Successfully logged out."}
    assert alice.get("/auth/me").status_code == 401


def test_logout_requires_login(client):
    res = client.post("/auth/logout")

    assert res.status_code == 401
