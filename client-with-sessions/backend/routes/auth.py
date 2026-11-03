# OWNER: JohnB (Authentication)
# TASKS:
# 1. POST /auth/signup (Create user, return 201)
# 2. POST /auth/login  (login_user(), return 200)
# 3. GET  /auth/me     (@login_required, return current_user)
# 4. POST /auth/logout (logout_user(), clear session)
# RULES:
# - Do not return password_hash in any response.
# - Return 401 for bad credentials, 409/422 for duplicates.
# - Format all errors as {"error": "message"}.

from flask import Blueprint, request, jsonify


# JohnB will fill this in
auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from marshmallow import ValidationError

from schemas.user_schema import user_schema
from services.auth_service import (
    create_user,
    authenticate_user,
    DuplicateUserError
)


# Authentication blueprint
auth_bp = Blueprint(
    "auth_bp",
    __name__,
    url_prefix="/auth"
)


# 1. SIGNUP
@auth_bp.route("/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 422

    try:
        # Validate incoming registration data
        validated_data = user_schema.load(data)

        # Create user
        user = create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

        return jsonify(user_schema.dump(user)), 201

    except ValidationError as error:
        messages = [
            message
            for field_errors in error.messages.values()
            for message in field_errors
        ]

        return jsonify({
            "error": messages[0] if messages else "Invalid registration data."
        }), 422

    except DuplicateUserError as error:
        return jsonify({
            "error": str(error)
        }), 409


# 2. LOGIN
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain valid JSON."
        }), 422

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required."
        }), 422

    user = authenticate_user(username, password)

    if user is None:
        return jsonify({
            "error": "Invalid username or password."
        }), 401

    # Start authenticated session
    login_user(user)

    return jsonify(user_schema.dump(user)), 200


# 3. CHECK CURRENT SESSION
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():

    return jsonify(user_schema.dump(current_user)), 200


# 4. LOGOUT
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    return jsonify({
        "message": "Successfully logged out."
    }), 200
