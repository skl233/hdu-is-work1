"""Start the API on 127.0.0.1:5055 and run real HTTP requests against it.

The transcript (curl-style) is printed and written to docs/api-demo-output.txt,
so the README and the report contain genuine responses, not invented ones.

Usage:  python scripts/api_smoke_test.py
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

BASE = "http://127.0.0.1:5055"
SECRET = os.environ.get("SEED_USER_SECRET", "Str0ng!Passw0rd#2024")  # nosec B105
LINES = []


def log(text: str = "") -> None:
    print(text)
    LINES.append(text)


def request(method: str, path: str, body: dict | None = None, token: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    log(f"$ curl -i -X {method} {BASE}{path}" + (" -d '" + json.dumps(body) + "'" if body else ""))
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status, payload = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        status, payload = error.code, error.read().decode()

    try:
        pretty = json.dumps(json.loads(payload), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pretty = payload
    if len(pretty) > 700:
        pretty = pretty[:700] + "\n... (truncated)"
    log(f"HTTP/1.1 {status}")
    log(pretty)
    log("-" * 78)
    return status, payload


def main() -> int:
    db_path = os.path.join(tempfile.gettempdir(), "work1-smoke.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    app = create_app(
        test_config={
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "JWT_SECRET": "smoke-test-secret",
            "JWT_TTL_MINUTES": 30,
        }
    )
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False),
        daemon=True,
    ).start()
    time.sleep(2.5)

    log("=== Work 1 - secure REST API smoke test ===")
    log()

    log("### 1. POST /auth/login with a wrong password (must be 401)")
    request("POST", "/auth/login", {"username": "alice", "password": "wrong"})

    log("### 2. POST /auth/login with valid credentials (must return a JWT)")
    status, payload = request("POST", "/auth/login", {"username": "alice", "password": SECRET})
    token = json.loads(payload).get("access_token", "") if status == 200 else ""

    log("### 3. GET /api/data WITHOUT a token (must be 401)")
    request("GET", "/api/data")

    log("### 4. GET /api/data WITH the token (must be 200)")
    request("GET", "/api/data", token=token)

    log("### 5. GET /api/data with a tampered token (must be 401)")
    request("GET", "/api/data", token=token[:-2] + "xy" if token else "forged")

    log("### 6. SQL injection attempt in the login form (must be 401, no token)")
    request(
        "POST",
        "/auth/login",
        {"username": "' OR '1'='1' --", "password": "' OR '1'='1' --"},
    )

    log("### 7. POST /api/posts with an XSS payload (output must be escaped)")
    request(
        "POST",
        "/api/posts",
        {"title": "<img src=x onerror=alert(1)>", "content": "<script>alert('xss')</script>"},
        token=token,
    )

    log("### 8. GET /api/posts?q=script (parameterised search)")
    request("GET", "/api/posts?q=script", token=token)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "api-demo-output.txt"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(LINES))
    log("Transcript written to docs/api-demo-output.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
