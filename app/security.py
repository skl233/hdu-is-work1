"""Security helpers: password hashing, JWT issuing/validation, output escaping."""

from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, jsonify, request
from markupsafe import escape

# bcrypt only uses the first 72 bytes of a password.
BCRYPT_MAX_BYTES = 72

# Pre-computed hash used to keep the response time constant when the user
# does not exist (prevents username enumeration / timing side channels).
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt(rounds=12))


def hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt (cost factor 12, salt generated per password)."""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time verification of a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def check_credentials(plain_password: str, password_hash: str | None) -> bool:
    """Verify credentials without leaking whether the account exists."""
    if password_hash:
        return verify_password(plain_password, password_hash)
    verify_password(plain_password, _DUMMY_HASH.decode("utf-8"))
    return False


def password_is_acceptable(plain_password: str) -> bool:
    """Reject empty passwords and passwords longer than the bcrypt limit."""
    return bool(plain_password) and len(plain_password.encode("utf-8")) <= BCRYPT_MAX_BYTES


def issue_token(user) -> tuple[str, int]:
    """Issue a signed JWT for an authenticated user."""
    ttl_minutes = int(current_app.config.get("JWT_TTL_MINUTES", 30))
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "iss": "work1-secure-api",
    }
    token = jwt.encode(
        claims,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token, ttl_minutes * 60


def decode_token(token: str) -> dict:
    """Validate a JWT: signature, issuer, expiration and required claims."""
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
        issuer="work1-secure-api",
        options={"require": ["exp", "iat", "nbf", "sub"]},
    )


def token_required(view):
    """Middleware: require and validate a Bearer JWT on protected endpoints."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return (
                jsonify(error="Missing or malformed Authorization header"),
                401,
            )
        try:
            claims = decode_token(parts[1])
        except jwt.ExpiredSignatureError:
            return jsonify(error="Token has expired"), 401
        except jwt.InvalidTokenError:
            return jsonify(error="Invalid token"), 401

        from app.models import User

        user = db_session_user(User, claims["sub"])
        if user is None:
            return jsonify(error="Unknown subject"), 401

        kwargs["current_user"] = user
        return view(*args, **kwargs)

    return wrapper


def db_session_user(model, subject: str):
    """Load the token subject from the database using a parameterised query."""
    from sqlalchemy import select

    from app import db

    stmt = select(model).where(model.id == int(subject))
    return db.session.execute(stmt).scalar_one_or_none()


def sanitize(value, max_length: int | None = None) -> str:
    """Escape untrusted data before it is rendered/returned (XSS prevention)."""
    text = escape("" if value is None else str(value))
    if max_length is not None:
        text = text[:max_length]
    return str(text)
