"""Application factory for the Work 1 secure REST API.

Security-relevant configuration (JWT secret, database URL, token lifetime)
is always taken from environment variables; sensible development defaults
are generated at runtime instead of being hard-coded.
"""

import os
import secrets

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    jwt_secret = os.environ.get("JWT_SECRET")
    if not jwt_secret:
        # Never ship a hard-coded secret: generate an ephemeral one per process.
        jwt_secret = secrets.token_urlsafe(48)
        app.logger.warning("JWT_SECRET is not set - generated an ephemeral secret.")

    app.config.from_mapping(
        SECRET_KEY=jwt_secret,
        JWT_SECRET=jwt_secret,
        JWT_ALGORITHM="HS256",
        JWT_TTL_MINUTES=int(os.environ.get("JWT_TTL_MINUTES", "30")),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///work1.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=64 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app import routes  # noqa: F401  (import registers the blueprint)
    from app.models import Post, User  # noqa: F401  (import registers models)

    app.register_blueprint(routes.api)

    with app.app_context():
        db.create_all()
        # Demo rows are optional: tests start from a clean database.
        if app.config.get("SEED_DEMO_DATA", True):
            from app.seed import seed_demo_data

            seed_demo_data()

    @app.after_request
    def apply_security_headers(response):
        """Defence-in-depth response headers (XSS / clickjacking / sniffing)."""
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    return app
