# OWNER: JohnB (Authentication)
# TASKS:
# 1. Helper functions for auth logic.
# 2. Hash passwords using bcrypt.
# 3. Verify passwords.
# 4. Check for duplicate usernames/emails before creating user.


from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db, bcrypt
from models import User


class DuplicateUserError(Exception):
    """Raised when username or email already exists."""
    pass


# 1. HASH PASSWORD
def hash_password(password):
    """Generate a secure bcrypt password hash."""

    return bcrypt.generate_password_hash(
        password
    ).decode("utf-8")


# 2. VERIFY PASSWORD
def verify_password(password, password_hash):
    """Compare entered password against stored hash."""

    return bcrypt.check_password_hash(
        password_hash,
        password
    )


# 3. CHECK DUPLICATES
def check_duplicate_user(username, email):
    """Check for existing username or email."""

    return User.query.filter(
        db.or_(
            func.lower(User.username) == username.lower(),
            func.lower(User.email) == email.lower()
        )
    ).first()


# 4. CREATE USER
def create_user(username, email, password):
    """Create a new user with a hashed password."""

    username = username.strip()
    email = email.strip().lower()

    # Check for existing username or email
    existing_user = check_duplicate_user(
        username,
        email
    )

    if existing_user:

        if existing_user.username.lower() == username.lower():
            raise DuplicateUserError(
                "Username already exists."
            )

        raise DuplicateUserError(
            "Email already exists."
        )

    # Hash password before storing
    password_hash = hash_password(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    try:
        db.session.add(user)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        raise DuplicateUserError(
            "Username or email already exists."
        )

    return user


# 5. AUTHENTICATE USER
def authenticate_user(username, password):
    """Find user and verify login credentials."""

    user = User.query.filter(
        func.lower(User.username) == username.strip().lower()
    ).first()

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash
    ):
        return None

    return user
