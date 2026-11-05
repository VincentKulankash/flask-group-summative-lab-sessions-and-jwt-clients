# OWNER: Allen (Quality & Docs)
# TASKS:
# 1. Script to populate the database with test data.
# 2. Create at least 3 users with hashed passwords.
# 3. Create multiple diary entries with varied moods/dates.
#
# USAGE (from the backend folder, after `flask db upgrade`):
#   python seed.py
# WARNING: this deletes all existing users and diary entries first.

import random
from datetime import datetime, timedelta

from faker import Faker

from app import create_app
from extensions import db
from models import User, DiaryEntry


fake = Faker()

SEED_PASSWORD = "password123"

USERS = [
    {"username": "allen", "email": "allen@example.com"},
    {"username": "johnb", "email": "johnb@example.com"},
    {"username": "acey", "email": "acey@example.com"},
    {"username": "stanley", "email": "stanley@example.com"},
]

MOODS = ["happy", "sad", "excited", "calm", "anxious", "grateful", "tired", None]

ENTRIES_PER_USER = 12


def clear_data():
    print("Clearing old data...")
    DiaryEntry.query.delete()
    User.query.delete()
    db.session.commit()


def seed_users():
    print("Creating users...")
    users = []

    for info in USERS:
        user = User(username=info["username"], email=info["email"])
        # set_password() stores a bcrypt hash, never the plain password
        user.set_password(SEED_PASSWORD)
        users.append(user)

    db.session.add_all(users)
    db.session.commit()
    return users


def seed_entries(users):
    print("Creating diary entries...")
    entries = []

    for user in users:
        for _ in range(ENTRIES_PER_USER):
            # Spread entries over the last 60 days. created_at is set too,
            # because GET /diary-entries sorts newest first by created_at.
            date = datetime.utcnow() - timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 23),
            )

            entries.append(DiaryEntry(
                title=fake.sentence(nb_words=5).rstrip("."),
                content="\n\n".join(fake.paragraphs(nb=random.randint(1, 3))),
                mood=random.choice(MOODS),
                entry_date=date,
                created_at=date,
                updated_at=date,
                user_id=user.id,
            ))

    db.session.add_all(entries)
    db.session.commit()
    return entries


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        clear_data()
        users = seed_users()
        entries = seed_entries(users)

        print(f"Seeded {len(users)} users and {len(entries)} diary entries.")
        print(f"Log in with any of these usernames and password '{SEED_PASSWORD}':")
        for user in users:
            print(f"  - {user.username}")
