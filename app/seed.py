"""Seed data for the demo database.

The demo secrets are read from the environment; the literal fallbacks are
marked with ``# nosec B105`` because they are dummy accounts of a teaching
project, never production credentials.
"""

import os

from app import db
from app.models import Post, User
from app.security import hash_password

DEMO_USER_SECRET = os.environ.get("SEED_USER_SECRET", "Str0ng!Passw0rd#2024")  # nosec B105
DEMO_ADMIN_SECRET = os.environ.get("SEED_ADMIN_SECRET", "Adm1n!Passw0rd#2024")  # nosec B105

DEMO_ACCOUNTS = (
    ("alice", "alice@example.com", DEMO_USER_SECRET, "user"),
    ("bob", "bob@example.com", DEMO_USER_SECRET, "user"),
    ("admin", "admin@example.com", DEMO_ADMIN_SECRET, "admin"),
)


def seed_demo_data() -> None:
    """Create demo users and posts once, using hashed passwords only."""
    if User.query.first() is not None:
        return

    users = []
    for username, _email, secret, role in DEMO_ACCOUNTS:
        user = User(
            username=username,
            password_hash=hash_password(secret),
            role=role,
        )
        db.session.add(user)
        users.append(user)
    db.session.flush()

    demo_posts = (
        ("Welcome", "This record is stored and returned escaped."),
        ("Security notes", "Passwords are stored as bcrypt hashes."),
        ("CI/CD", "Bandit and pip-audit run on every push."),
    )
    for title, content in demo_posts:
        db.session.add(Post(title=title, content=content, author_id=users[0].id))

    db.session.commit()
