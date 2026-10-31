# OWNER: ACEY (CRUD) & STANLEY (Pagination)
# TASKS:
# 1. POST   /diary-entries      (Create entry for current_user)
# 2. GET    /diary-entries/<id> (Read ONE entry, check ownership)
# 3. PATCH  /diary-entries/<id> (Update, check ownership)
# 4. DELETE /diary-entries/<id> (Delete, check ownership)
# 5. GET    /diary-entries      (STANLEY: Paginated list, newest first)
# RULES:
# - All routes MUST have @login_required.
# - Attach new entries to current_user.id, NEVER from request JSON.
# - If user A requests user B's entry, return 404 NOT 403.

# ---------- IMPORTS ----------
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from extensions import db
from models import DiaryEntry
from schemas.diary_schema import diary_schema, format_errors

# A Blueprint is a mini-app. app.py plugs it into the main app.
diary_bp = Blueprint("diary_entries", __name__)


# ---------- HELPER: find an entry, but only if it's MINE ----------
def get_own_entry(entry_id):
    # Someone else's entry counts as "not found", so we return 404, never 403
    return DiaryEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()


# ---------- 1. CREATE: POST /diary-entries ----------
@diary_bp.route("/diary-entries", methods=["POST"])
@login_required
def create_entry():
    try:
        data = diary_schema.load(request.get_json() or {})  # validate input
    except ValidationError as err:
        return jsonify({"error": format_errors(err.messages)}), 400
    # user_id comes from the logged-in user, NEVER from the request
    entry = DiaryEntry(**data, user_id=current_user.id)
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


# ---------- 2. READ ONE: GET /diary-entries/<id> ----------
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["GET"])
@login_required
def get_entry(entry_id):
    entry = get_own_entry(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify(entry.to_dict()), 200


# ---------- 3. UPDATE: PATCH /diary-entries/<id> ----------
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["PATCH"])
@login_required
def update_entry(entry_id):
    entry = get_own_entry(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    try:
        # partial=True: the user can send only the fields they want to change
        data = diary_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": format_errors(err.messages)}), 400
    for key, value in data.items():
        setattr(entry, key, value)
    db.session.commit()
    return jsonify(entry.to_dict()), 200


# ---------- 4. DELETE: DELETE /diary-entries/<id> ----------
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_entry(entry_id):
    entry = get_own_entry(entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Entry deleted"}), 200


# ---------- 5. LIST: GET /diary-entries ----------
# STANLEY's job (paginated list). Leave it for him.
