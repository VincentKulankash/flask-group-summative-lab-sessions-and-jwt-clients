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

from flask import Blueprint

# Acey & Stanley will fill this in
diary_bp = Blueprint("diary_bp", __name__, url_prefix="/diary-entries")