from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError

from extensions import db
from models import DiaryEntry
from schemas.diary_schema import diary_schema, format_errors
from services.diary_service import owns_entry, get_paginated_entries


diary_bp = Blueprint("diary_entries", __name__)


# CREATE: POST /diary-entries
@diary_bp.route("/diary-entries", methods=["POST"])
@login_required
def create_entry():
    try:
        data = diary_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": format_errors(err.messages)}), 400

    # Always associate the entry with the authenticated user.
    entry = DiaryEntry(**data, user_id=current_user.id)

    db.session.add(entry)
    db.session.commit()

    return jsonify(entry.to_dict()), 201


# READ ONE: GET /diary-entries/<entry_id>
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["GET"])
@login_required
@owns_entry
def get_entry(entry):
    return jsonify(entry.to_dict()), 200


# UPDATE: PATCH /diary-entries/<entry_id>
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["PATCH"])
@login_required
@owns_entry
def update_entry(entry):
    try:
        data = diary_schema.load(
            request.get_json() or {},
            partial=True
        )
    except ValidationError as err:
        return jsonify({"error": format_errors(err.messages)}), 400

    for key, value in data.items():
        setattr(entry, key, value)

    db.session.commit()

    return jsonify(entry.to_dict()), 200


# DELETE: DELETE /diary-entries/<entry_id>
@diary_bp.route("/diary-entries/<int:entry_id>", methods=["DELETE"])
@login_required
@owns_entry
def delete_entry(entry):
    db.session.delete(entry)
    db.session.commit()

    return jsonify({"message": "Entry deleted"}), 200


# LIST: GET /diary-entries
# Stanley's pagination implementation comes next.


# LIST: GET /diary-entries
# STANLEY: Paginated diary entries, newest first.
@diary_bp.route("/diary-entries", methods=["GET"])
@login_required
def list_entries():
    result = get_paginated_entries(current_user.id)
    return jsonify(result), 200
