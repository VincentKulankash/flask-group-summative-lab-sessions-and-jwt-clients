# Personal Diary API (Flask Sessions)

<!-- OWNER: Allen (Quality & Docs) -->

A Flask REST API where users sign up, log in with a **session cookie** (Flask-Login), and manage their own private diary entries. Each user can only see, edit, or delete their own entries.

**Team:** Vincent Kulankash, JohnB (authentication), Acey (diary CRUD), Stanley (ownership & pagination), Allen (tests, seed data & docs)

## Tech Stack

- Flask 2.2, Flask-SQLAlchemy, Flask-Migrate (SQLite)
- Flask-Login (session-based auth), Flask-Bcrypt (password hashing)
- Marshmallow (validation), Flask-CORS
- pytest, Faker

## Project Structure

```
backend/
├── app.py              # create_app() factory, error handlers, blueprints
├── config.py           # Config + TestingConfig (in-memory SQLite)
├── extensions.py       # db, bcrypt, login_manager, migrate, cors
├── models.py           # User, DiaryEntry
├── routes/
│   ├── auth.py         # /auth/* routes
│   └── diary_entries.py# /diary-entries routes
├── schemas/            # Marshmallow schemas (user, diary entry)
├── services/           # auth helpers, ownership decorator, pagination
├── migrations/         # Alembic migrations
├── seed.py             # sample data
└── tests/              # pytest suite
```

## Setup

From the `client-with-sessions/backend` folder:

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
cp .env.examplt .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste this as SECRET_KEY in .env

# 4. Create the database tables
flask db upgrade

# 5. (Optional) Load sample data
python seed.py

# 6. Run the server (http://localhost:5000)
flask run
```

### Environment Variables

| Variable       | Default                    | Description                     |
| -------------- | -------------------------- | ------------------------------- |
| `SECRET_KEY`   | `dev-secret-key-change-me` | Signs the session cookie        |
| `DATABASE_URL` | `sqlite:///app.db`         | Stored at `instance/app.db`     |

## Seed Data

`python seed.py` **deletes all existing data**, then creates 4 users with 12 diary entries each (random moods, dates spread over the last 60 days).

All seeded users share the password `password123`:

| Username  | Email                 |
| --------- | --------------------- |
| `allen`   | allen@example.com     |
| `johnb`   | johnb@example.com     |
| `acey`    | acey@example.com      |
| `stanley` | stanley@example.com   |

## Running Tests

```bash
pytest           # or: pytest -v
```

Tests use `TestingConfig` (in-memory SQLite), so your real database is never touched. They cover:

- **Auth** (`tests/test_auth.py`): signup validation and duplicates, login, wrong credentials, `/auth/me`, logout, session cookies persisting between requests, and that `password_hash` is never returned.
- **Diary** (`tests/test_diary.py`): create, read, update, and delete; validation errors; pagination (`page`, `per_page`, `total`, newest first); login required on every route.
- **Security**: user B gets `404` when trying to read, edit, or delete user A's entry, and a `user_id` sent in the request body is ignored.

Shared fixtures (`app`, `client`, and the logged-in `alice` / `bob` clients) live in `tests/conftest.py`.

## API Reference

All request and response bodies are JSON. Errors always look like `{"error": "message"}`.
Routes marked 🔒 need a logged-in session cookie, and return `401` without one.

### Authentication

| Method | Endpoint       | Body                              | Success                 | Errors                                         |
| ------ | -------------- | --------------------------------- | ----------------------- | ---------------------------------------------- |
| POST   | `/auth/signup` | `username`, `email`, `password`   | `201` user              | `422` invalid data, `409` username/email taken |
| POST   | `/auth/login`  | `username`, `password`            | `200` user + cookie     | `422` missing fields, `401` wrong credentials  |
| GET    | `/auth/me` 🔒  | —                                 | `200` current user      | `401`                                          |
| POST   | `/auth/logout` 🔒 | —                              | `200` `{"message": ...}`| `401`                                          |

Validation rules: username 3–50 characters, valid email, password at least 8 characters. Usernames and emails are case-insensitive when checking for duplicates and logging in.

User response:

```json
{ "id": 1, "username": "allen", "email": "allen@example.com" }
```

### Diary Entries 🔒

| Method | Endpoint               | Body                                   | Success                  | Errors                              |
| ------ | ---------------------- | -------------------------------------- | ------------------------ | ----------------------------------- |
| GET    | `/diary-entries`       | query: `page` (1), `per_page` (10, max 100) | `200` paginated list | `400` bad page/per_page             |
| POST   | `/diary-entries`       | `title`, `content`, `mood` (optional)  | `201` entry              | `400` validation                    |
| GET    | `/diary-entries/<id>`  | —                                      | `200` entry              | `404` not found / not yours         |
| PATCH  | `/diary-entries/<id>`  | any of `title`, `content`, `mood`      | `200` entry              | `400` validation, `404`             |
| DELETE | `/diary-entries/<id>`  | —                                      | `200` `{"message": "Entry deleted"}` | `404`                   |

Another user's entry returns `404` (not `403`), so the API doesn't reveal that the entry exists.

Entry response:

```json
{
  "id": 1,
  "title": "My day",
  "content": "It was a good day.",
  "mood": "happy",
  "entry_date": "2026-11-03T10:15:00",
  "user_id": 1
}
```

Paginated list response (newest first):

```json
{
  "entries": [ { "id": 3, "title": "..." } ],
  "pagination": { "page": 1, "per_page": 10, "total": 15, "pages": 2 }
}
```

## Example with curl

```bash
# Sign up and log in (the cookie jar keeps the session)
curl -X POST localhost:5000/auth/signup -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"password123"}'
curl -c cookies.txt -X POST localhost:5000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"password123"}'

# Create and list entries
curl -b cookies.txt -X POST localhost:5000/diary-entries -H "Content-Type: application/json" \
  -d '{"title":"First entry","content":"Hello diary","mood":"happy"}'
curl -b cookies.txt "localhost:5000/diary-entries?page=1&per_page=5"
```

## Known Issues

- Invalid pagination values (for example `?page=0`) return `400`, but as Flask's default HTML page instead of `{"error": ...}`, because `app.py` has no `400` error handler. The test `test_list_invalid_pagination_returns_json_error` is marked `xfail` until this is fixed.
- The React client in `client-with-sessions/src` calls `/signup`, `/login`, `/check_session` and `DELETE /logout`, but this API uses `/auth/signup`, `/auth/login`, `/auth/me` and `POST /auth/logout`. The client's signup form also doesn't send `email`, and it reads errors from `err.errors` instead of `error`.
