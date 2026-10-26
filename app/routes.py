"""API endpoints.

1. POST /auth/login  - authentication, returns a signed JWT.
2. GET  /api/data    - protected, returns a list of users.
3. POST /api/posts   - protected, creates a post (own choice endpoint).
   (extra) GET /api/posts - protected search over posts.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app import db
from app.models import Post, User
from app.security import (
    check_credentials,
    issue_token,
    password_is_acceptable,
    sanitize,
    token_required,
)

api = Blueprint("api", __name__)


def _json_body() -> dict:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _post_to_dict(post: Post) -> dict:
    """Serialise a post; every user-controlled field is escaped on output."""
    return {
        "id": post.id,
        "title": sanitize(post.title, 120),
        "content": sanitize(post.content, 4000),
        "author": sanitize(post.author.username, 80),
        "created_at": post.created_at.isoformat(),
    }


@api.get("/health")
def health():
    return jsonify(status="ok")


@api.post("/auth/login")
def login():
    """Authenticate a user and issue a JWT.

    The lookup uses a parameterised query (SQLAlchemy ``select``), so a
    payload such as ``' OR '1'='1`` is treated as data, not as SQL.
    """
    body = _json_body()
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))

    if not username or not password:
        return jsonify(error="username and password are required"), 400
    # bcrypt silently truncates at 72 bytes - reject longer input explicitly.
    if not password_is_acceptable(password):
        return jsonify(error="password must be 1-72 bytes"), 400

    stmt = select(User).where(User.username == username)
    user = db.session.execute(stmt).scalar_one_or_none()

    if user is None or not check_credentials(password, user.password_hash):
        # Same generic message and comparable timing for both failure reasons.
        return jsonify(error="invalid username or password"), 401

    token, expires_in = issue_token(user)
    return (
        jsonify(
            access_token=token,
            token_type="Bearer",
            expires_in=expires_in,
            user={"id": user.id, "username": sanitize(user.username), "role": user.role},
        ),
        200,
    )


@api.get("/api/data")
@token_required
def get_data(current_user):
    """Protected endpoint: list registered users (no password hashes exposed)."""
    users = db.session.execute(select(User).order_by(User.id)).scalars().all()
    return (
        jsonify(
            count=len(users),
            data=[
                {
                    "id": user.id,
                    "username": sanitize(user.username, 80),
                    "role": sanitize(user.role, 20),
                    "created_at": user.created_at.isoformat(),
                }
                for user in users
            ],
        ),
        200,
    )


@api.post("/api/posts")
@token_required
def create_post(current_user):
    """Protected endpoint: create a post for the authenticated user.

    Input is length-limited and stored as data (ORM parameter binding).
    Output is escaped, so ``<script>`` payloads are rendered inert.
    """
    body = _json_body()
    title = str(body.get("title", "")).strip()
    content = str(body.get("content", "")).strip()

    if not title or not content:
        return jsonify(error="title and content are required"), 400
    if len(title) > 120 or len(content) > 4000:
        return jsonify(error="title/content too long"), 400

    post = Post(title=title, content=content, author_id=current_user.id)
    db.session.add(post)
    db.session.commit()

    return jsonify(message="created", post=_post_to_dict(post)), 201


@api.get("/api/posts")
@token_required
def list_posts(current_user):
    """Protected endpoint: search posts with a bound (parameterised) LIKE."""
    query = str(request.args.get("q", "")).strip()
    stmt = select(Post).order_by(Post.id.desc())
    if query:
        # The value is bound as a parameter - SQL injection is not possible.
        stmt = stmt.where(Post.content.ilike(f"%{query}%"))

    posts = db.session.execute(stmt).scalars().all()
    return jsonify(count=len(posts), data=[_post_to_dict(post) for post in posts]), 200


@api.get("/api/me")
@token_required
def me(current_user):
    """Protected endpoint: information about the caller (from the JWT)."""
    return (
        jsonify(
            id=current_user.id,
            username=sanitize(current_user.username, 80),
            role=sanitize(current_user.role, 20),
        ),
        200,
    )
