from functools import wraps

from flask import abort, request
from flask_login import current_user

from models import DiaryEntry


def owns_entry(view_function):
    """Ensure a diary entry belongs to the authenticated user."""

    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        entry_id = kwargs.get("entry_id")

        if entry_id is None and args:
            entry_id = args[0]
            args = args[1:]

        if entry_id is None:
            abort(404)

        entry = DiaryEntry.query.filter_by(
            id=entry_id,
            user_id=current_user.id
        ).first()

        if entry is None:
            abort(404)

        kwargs.pop("entry_id", None)

        return view_function(entry, *args, **kwargs)

    return decorated_function


def get_paginated_entries(user_id):
    """Return the authenticated user's diary entries, newest first."""

    page_value = request.args.get("page", "1")
    per_page_value = request.args.get("per_page", "10")

    try:
        page = int(page_value)
        per_page = int(per_page_value)
    except (ValueError, TypeError):
        abort(400, description="page and per_page must be integers.")

    if page < 1:
        abort(400, description="page must be a positive integer.")

    if per_page < 1 or per_page > 100:
        abort(400, description="per_page must be between 1 and 100.")

    pagination = (
        DiaryEntry.query
        .filter_by(user_id=user_id)
        .order_by(
            DiaryEntry.created_at.desc(),
            DiaryEntry.id.desc()
        )
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    )

    return {
        "entries": [entry.to_dict() for entry in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }
