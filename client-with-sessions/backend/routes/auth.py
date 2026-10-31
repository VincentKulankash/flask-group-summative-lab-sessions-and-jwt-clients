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

from flask import Blueprint

# JohnB will fill this in
auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")