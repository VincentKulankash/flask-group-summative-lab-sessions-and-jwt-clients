# OWNER: Allen (Quality & Docs)
# Shared pytest fixtures for test_auth.py and test_diary.py.
# - Every test gets a fresh app backed by an in-memory SQLite database (TestingConfig).
# - The app context is NOT kept pushed while requests run, so Flask-Login's
#   per-request user cache (flask.g) can't leak between two test clients.

import pytest

from app import create_app
from config import TestingConfig
from extensions import db


PASSWORD = "password123"


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """An anonymous (logged out) test client."""
    return app.test_client()


def signup(client, username, email=None, password=PASSWORD):
    return client.post("/auth/signup", json={
        "username": username,
        "email": email or f"{username}@example.com",
        "password": password,
    })


def login(client, username, password=PASSWORD):
    return client.post("/auth/login", json={
        "username": username,
        "password": password,
    })


def make_logged_in_client(app, username):
    """Sign up + log in on a fresh client. The session cookie stays on that client."""
    client = app.test_client()
    signup(client, username)
    login(client, username)
    return client


@pytest.fixture
def alice(app):
    """Logged-in client for user 'alice'."""
    return make_logged_in_client(app, "alice")


@pytest.fixture
def bob(app):
    """Logged-in client for user 'bob' (separate cookie jar from alice)."""
    return make_logged_in_client(app, "bob")
