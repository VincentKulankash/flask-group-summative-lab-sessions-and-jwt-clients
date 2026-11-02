# OWNER: JohnB (Authentication)
# TASKS:
# 1. Define UserSchema using Marshmallow.
# 2. Add validations: email format, password minimum length.
# 3. Exclude password_hash from serialization output.


from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)


class UserSchema(Schema):

    id = fields.Int(dump_only=True)

    username = fields.Str(
        required=True,
        validate=validate.Length(
            min=3,
            max=50,
            error="Username must be between 3 and 50 characters."
        )
    )

    email = fields.Email(
        required=True,
        validate=validate.Length(
            max=120,
            error="Email cannot exceed 120 characters."
        )
    )

    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=8,
            max=128,
            error="Password must be at least 8 characters long."
        )
    )

    created_at = fields.DateTime(
        dump_only=True
    )


# Schema instance
user_schema = UserSchema()
