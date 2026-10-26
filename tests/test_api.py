"""Automated tests: authentication, access control, SQLi and XSS behaviour."""

import pytest
from sqlalchemy import select

from app import create_app, db
from app.models import User
from app.security import hash_password, issue_token

PLAIN_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        test_config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "JWT_SECRET": "test-only-secret",
            "JWT_TTL_MINUTES": 15,
            "SEED_DEMO_DATA": False,
        }
    )
    with application.app_context():
        db.session.add(
            User(username="alice", password_hash=hash_password(PLAIN_PASSWORD), role="user")
        )
        db.session.commit()
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username="alice", password=PLAIN_PASSWORD):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_login_returns_jwt(client):
    response = login(client)
    assert response.status_code == 200
    body = response.get_json()
    assert body["token_type"] == "Bearer"
    assert len(body["access_token"].split(".")) == 3


def test_login_rejects_wrong_password(client):
    assert login(client, password="wrong-password").status_code == 401


def test_login_rejects_unknown_user_without_user_enumeration(client):
    unknown = login(client, username="ghost")
    wrong_pw = login(client, password="wrong-password")
    assert unknown.status_code == 401 and wrong_pw.status_code == 401
    assert unknown.get_json() == wrong_pw.get_json()


def test_protected_endpoint_without_token_is_denied(client):
    assert client.get("/api/data").status_code == 401
    assert login(client).status_code == 200


def test_protected_endpoint_with_token_returns_data(client):
    token = login(client).get_json()["access_token"]
    response = client.get("/api/data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert any(item["username"] == "alice" for item in data)
    assert all("password" not in item for item in data)


def test_tampered_token_is_rejected(client):
    token = login(client).get_json()["access_token"]
    forged = token[:-3] + "abc"
    response = client.get("/api/data", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_expired_token_is_rejected(app):
    with app.app_context():
        user = db.session.execute(select(User)).scalars().first()
        app.config["JWT_TTL_MINUTES"] = -5
        token, _ = issue_token(user)
    response = app.test_client().get(
        "/api/data", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_sql_injection_payload_is_not_executed(client):
    payload = "' OR '1'='1' --"
    response = client.post(
        "/auth/login", json={"username": payload, "password": payload}
    )
    assert response.status_code == 401
    assert "access_token" not in response.get_json()


def test_password_is_stored_hashed(app):
    with app.app_context():
        user = db.session.execute(select(User)).scalars().first()
    assert user.password_hash != PLAIN_PASSWORD
    assert user.password_hash.startswith("$2b$")


def test_xss_payload_is_escaped_on_output(client):
    token = login(client).get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = "<script>alert('xss')</script>"
    created = client.post(
        "/api/posts",
        json={"title": "<img src=x onerror=alert(1)>", "content": payload},
        headers=headers,
    )
    assert created.status_code == 201

    body = created.get_json()["post"]
    assert "<script>" not in body["content"]
    assert "&lt;script&gt;" in body["content"]
    assert "&lt;img" in body["title"]

    listing = client.get("/api/posts", headers=headers).get_json()
    assert "<script>" not in listing["data"][0]["content"]


def test_posts_search_is_parameterised(client):
    token = login(client).get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/posts", json={"title": "note", "content": "secret-document"}, headers=headers
    )
    found = client.get("/api/posts?q=secret", headers=headers).get_json()
    not_found = client.get(
        "/api/posts?q=' OR 1=1 --", headers=headers
    ).get_json()
    assert found["count"] == 1
    assert not_found["count"] == 0
