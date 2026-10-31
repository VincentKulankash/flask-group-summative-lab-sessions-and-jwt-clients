# OWNER: Acey (Diary CRUD)
# TASKS:
# 1. Define DiaryEntrySchema.
# 2. Make 'title' and 'content' required.
# 3. Make 'mood' optional.
# RULES: Ensure validation errors match {"error": "message"} format.

from marshmallow import Schema, fields, validate, EXCLUDE


class DiaryEntrySchema(Schema):
    # Ignore any extra fields (like user_id) sent in the request.
    # This is how we make sure user_id NEVER comes from the request.
    class Meta:
        unknown = EXCLUDE

    # title and content are REQUIRED
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=1))
    # mood is OPTIONAL (can be left out or null)
    mood = fields.Str(required=False, allow_none=True, validate=validate.Length(max=80))


# The one schema object our routes use
diary_schema = DiaryEntrySchema()


def format_errors(messages):
    """Turn Marshmallow's errors into the agreed format: one readable message.
    Example: {"title": ["Missing data for required field."]}
    becomes:  "title: Missing data for required field."
    """
    return "; ".join(f"{field}: {' '.join(errs)}" for field, errs in messages.items())
