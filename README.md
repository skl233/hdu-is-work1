# Work 1 — Secure REST API Development with CI/CD and Real CVE Vulnerability Analysis

[![Secure API CI](https://github.com/skl233/hdu-is-work1/actions/workflows/ci.yml/badge.svg)](https://github.com/skl233/hdu-is-work1/actions/workflows/ci.yml)
[![CVE](https://img.shields.io/badge/CVE-2017--1000028-red)](https://nvd.nist.gov/vuln/detail/CVE-2017-1000028)
[![CWE-22](https://img.shields.io/badge/CWE--22-path%20traversal-orange)](https://cwe.mitre.org/data/definitions/22.html)
[![OWASP](https://img.shields.io/badge/OWASP-Top%2010%202021-blue)](https://owasp.org/www-project-top-ten/)

**Student:** SONG Kongliang (宋孔亮) · **HDU number:** 23320316
**Course:** Information Security · **Laboratory Work No. 1**
**Variant:** CVE-2017-1000028 — GlassFish 4.1 Admin Console Path Traversal (Arbitrary File Read)
**Stack:** Python 3.11 + Flask 3 · Flask-SQLAlchemy (ORM) · PyJWT · bcrypt · SQLite
**CI/CD:** GitHub Actions — pytest + **Bandit (SAST)** + **pip-audit (SCA)**

> Repository: <https://github.com/skl233/hdu-is-work1>
> Latest successful pipeline run: <https://github.com/skl233/hdu-is-work1/actions/runs/40266586056>

---

## Where to look first

| If you want to see… | Open |
|---|---|
| The API code and its defences | [`app/`](app/) — `routes.py`, `security.py`, `models.py` |
| The automated security tests (11) | [`tests/test_api.py`](tests/test_api.py) |
| The CI pipeline definition | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| The pipeline **actually passing** | [Actions → Secure API CI](https://github.com/skl233/hdu-is-work1/actions/workflows/ci.yml) |
| The **real CVE reproduction** (live evidence) | [`cve/CVE-2017-1000028/README.md`](cve/CVE-2017-1000028/README.md) |
| Raw exploit output (`/etc/passwd`, admin password) | [`cve/CVE-2017-1000028/evidence/`](cve/CVE-2017-1000028/evidence/) |
| The fix and its verification (3 checks passed) | [`cve/CVE-2017-1000028/evidence/verify-fix.txt`](cve/CVE-2017-1000028/evidence/verify-fix.txt) |
| The written report (Word) | [`docs/Work1_Report_SONG_Kongliang_23320316.docx`](docs/Work1_Report_SONG_Kongliang_23320316.docx) |

---

## 1. Project overview

A small but complete REST API that demonstrates the defensive side of the
OWASP Top 10, wired into a CI/CD pipeline that runs security scanners on every
push, plus a full analysis of a real-world CVE reproduced with Vulhub.

```
POST /auth/login   -> authenticate, receive a signed JWT
GET  /api/data     -> protected: list users
POST /api/posts    -> protected: create a post   (own-choice endpoint)
GET  /api/posts    -> protected: parameterised search
GET  /api/me       -> protected: who am I (from the JWT claims)
GET  /health       -> liveness probe
```

---

## 2. API documentation

| Method | Endpoint | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/auth/login` | – | `{"username":"alice","password":"Str0ng!Passw0rd#2024"}` | `200` `{"access_token": "...", "token_type": "Bearer", "expires_in": 1800}` · `401` on failure |
| GET | `/api/data` | Bearer JWT | – | `200` `{"count":3,"data":[{...}]}` · `401` without/with invalid token |
| POST | `/api/posts` | Bearer JWT | `{"title":"...","content":"..."}` | `201` `{"message":"created","post":{...}}` · `400` on empty/invalid input |
| GET | `/api/posts?q=text` | Bearer JWT | query string | `200` `{"count":n,"data":[...]}` (all fields escaped) |
| GET | `/api/me` | Bearer JWT | – | `200` `{"id":1,"username":"alice","role":"user"}` |
| GET | `/health` | – | – | `200` `{"status":"ok"}` |

Demo accounts (created on first start, passwords stored only as bcrypt hashes):

| Username | Password | Role |
|---|---|---|
| `alice` | `Str0ng!Passw0rd#2024` | user |
| `bob` | `Str0ng!Passw0rd#2024` | user |
| `admin` | `Adm1n!Passw0rd#2024` | admin |

### How to run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python run.py                                          # http://127.0.0.1:5000
```

### curl walkthrough (real output: `docs/api-demo-output.txt`)

```bash
# 1. login
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Str0ng!Passw0rd#2024"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. protected endpoint without a token  -> 401
curl -i http://127.0.0.1:5000/api/data

# 3. protected endpoint with the token   -> 200
curl -i http://127.0.0.1:5000/api/data -H "Authorization: Bearer $TOKEN"

# 4. XSS payload is escaped in the response
curl -X POST http://127.0.0.1:5000/api/posts -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"<img src=x onerror=alert(1)>","content":"<script>alert(\"xss\")</script>"}'
```

Observed (excerpt from `docs/api-demo-output.txt`):

```
### 3. GET /api/data WITHOUT a token
HTTP/1.1 401
{ "error": "Missing or malformed Authorization header" }

### 4. GET /api/data WITH the token
HTTP/1.1 200
{ "count": 3, "data": [ {"id":1,"username":"alice","role":"user"}, ... ] }

### 6. SQL injection attempt in the login form
POST /auth/login  {"username": "' OR '1'='1' --", "password": "' OR '1'='1' --"}
HTTP/1.1 401
{ "error": "invalid username or password" }

### 7. POST /api/posts with an XSS payload
HTTP/1.1 201
"content": "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
"title":   "&lt;img src=x onerror=alert(1)&gt;"
```

A ready-to-import Postman collection is in `postman/work1-api.postman_collection.json`.

---

## 3. Implemented security measures

### 3.1 SQL injection (OWASP A03)

* Every database access goes through the **SQLAlchemy ORM / Core `select()`**
  construct. Values are always passed as bound parameters, never concatenated
  into a SQL string:
  ```python
  stmt = select(User).where(User.username == username)          # app/routes.py
  stmt = stmt.where(Post.content.ilike(f"%{query}%"))           # bind parameter
  ```
* No raw `db.engine.execute("SELECT ... ")` anywhere in the project.
* Automated proof: `tests/test_api.py::test_sql_injection_payload_is_not_executed`
  and `::test_posts_search_is_parameterised` — the classic `' OR '1'='1' --`
  payload returns `401` / `0` results instead of dumping rows.

### 3.2 XSS (OWASP A03)

* All user-controlled values are escaped **on output** with
  `markupsafe.escape()` (`app/security.py::sanitize`) before being serialised,
  so `<script>` becomes `&lt;script&gt;` (see the transcript above).
* Input is length-limited (`title` ≤ 120, `content` ≤ 4000 chars) and the
  response `Content-Type` is strictly `application/json`.
* Defence-in-depth headers on every response
  (`app/__init__.py::apply_security_headers`):
  `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `HSTS`.
* Automated proof: `tests/test_api.py::test_xss_payload_is_escaped_on_output`.

### 3.3 Broken authentication (OWASP A07)

* **Password hashing — bcrypt** with cost factor 12 and a per-password random
  salt (`app/security.py::hash_password`). Plaintext passwords never touch the
  database; `tests/test_api.py::test_password_is_stored_hashed` asserts the
  stored value starts with `$2b$` and differs from the plaintext.
* **JWT** issued on successful login (HS256, `iss` = `work1-secure-api`,
  `iat`/`nbf`/`exp`, 30-minute lifetime). The signing key comes from the
  `JWT_SECRET` environment variable; if it is missing the app generates an
  ephemeral random secret instead of falling back to a hard-coded one.
* **Middleware** `@token_required` (`app/security.py`) validates the
  `Authorization: Bearer <token>` header on `/api/data`, `/api/posts`,
  `/api/me`: it checks the signature, the issuer, the expiry and the presence
  of the required claims, then re-loads the subject from the database.
  Tampered, expired, malformed and missing tokens all yield `401`
  (`test_tampered_token_is_rejected`, `test_expired_token_is_rejected`).
* **No user enumeration:** a wrong password and an unknown username return the
  identical message, and the unknown-user path still performs a bcrypt
  comparison against a dummy hash so the response time does not reveal whether
  the account exists.
* Passwords longer than 72 bytes are rejected explicitly (bcrypt limit).
* The Flask debugger is disabled in every environment.

---

## 4. CI/CD pipeline with security scanners

File: `.github/workflows/ci.yml` — triggered on **every push and pull request**.

| Job | Tool | Command | Gate |
|---|---|---|---|
| `tests` | pytest | `pytest -v` | 11 tests must pass |
| `sast` | **Bandit** (SAST) | `bandit -r app -ll -ii -f json -o bandit-report.json` | no medium/high finding |
| `sca` | **pip-audit** (SCA) | `pip-audit -r requirements.txt --strict --format json` | no known-vulnerable dependency |

Both scanners upload their JSON report as a workflow artifact, and Bandit also
publishes SARIF to the GitHub **Security** tab (`codeql-action/upload-sarif`).

### Scanner results (verified locally, identical commands)

```bash
$ pytest -q
11 passed, 12 warnings in 8.54s

$ bandit -r app -ll -ii
Run started:2026-10-20
Test results:
        No issues identified.
Code scanned:
        Total lines of code: 331
        Total issues (by severity):
                Undefined: 0    Low: 1    Medium: 0    High: 0

$ pip-audit -r requirements.txt --strict
No known vulnerabilities found
```

### Screenshots of the SAST/SCA reports from the "Actions" section

> Replace the two files below with your own screenshots after the first green
> run (Actions → workflow run → job `sast` / `sca` → "Upload Bandit report").

| Pipeline overview (all jobs green) | SAST job — Bandit |
|---|---|
| ![CI overview](docs/screenshots/01-actions-green.png) | ![Bandit](docs/screenshots/02-bandit-sast.png) |

| SCA job — pip-audit | Downloaded artifacts |
|---|---|
| ![pip-audit](docs/screenshots/03-pip-audit-sca.png) | ![artifacts](docs/screenshots/04-artifacts.png) |

*(The Bandit "Low: 1" entry is `B105` on the demo seed passwords in
`app/seed.py`; it is annotated with `# nosec` and filtered out by `-ll`. It is
a deliberate teaching fixture, not production code.)*

---

## 5. CVE part — CVE-2017-1000028 (GlassFish 4.1)

Full write-up: **[`cve/CVE-2017-1000028/README.md`](cve/CVE-2017-1000028/README.md)**.
**Reproduced for real on this machine** — raw captures in
`cve/CVE-2017-1000028/evidence/`. Summary:

### 5.1 Name and brief description

**CVE-2017-1000028 — GlassFish 4.1 admin console arbitrary file read.**
The administration console of GlassFish Server Open Source Edition 4.1 serves
its static theme resources from `/theme/META-INF/` and decodes the request URI
with a lenient UTF-8 decoder that still accepts **overlong** (non shortest
form) sequences. The bytes `%c0%ae` are therefore decoded to `.`, so
`%c0%ae%c0%ae/` becomes `../`. Because the decoded path is never canonicalised
and re-checked against the theme directory, an **unauthenticated** attacker can
walk out of that directory and read **any file readable by the GlassFish
process** — `/etc/passwd`, `domains/domain1/config/admin-keyfile`, even
`/proc/self/environ`, which returns the administrator password in cleartext.
CWE-22 (with CWE-178 overlong UTF-8 as the enabler) · CVSS v3 **7.5 High**
(`AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`) · fixed in GlassFish 4.1.2 / 5.0.

### 5.2 Reproduction (commands)

```bash
# vulnerable environment: GlassFish 4.1, admin console on 4848 (TLS)
docker compose -f cve/CVE-2017-1000028/vulnerable/docker-compose.yml up -d

# the console needs 3-5 minutes to initialise: wait until
#   curl -k https://127.0.0.1:4848/login.jsf
# no longer returns "The Admin Console Adapter is not yet initialized."

python cve/CVE-2017-1000028/poc/exploit.py --port 4848 --file /etc/passwd --https

# -> HTTP status : 200
# -> root:x:0:0:root:/root:/bin/bash
# -> ...
# -> [+] VULNERABLE - file content disclosed without authentication.

# the same trick leaks the administrator password in clear text:
python cve/CVE-2017-1000028/poc/exploit.py --port 4848 --file /proc/self/environ --https
# -> ADMIN_PASSWORD=vulhub_default_password

# ...and the console credential file:
python cve/CVE-2017-1000028/poc/exploit.py --port 4848 --https \
  --file /usr/local/glassfish4/glassfish/domains/domain1/config/admin-keyfile
# -> admin;{SSHA256}z5q5cZWChstXsvY4mTLnitBUSyfpOgONr9kKQha5TM7bV6S5lvn5gQ==;asadmin

# log in at https://127.0.0.1:4848 with admin / vulhub_default_password
```

One-shot scripts: `poc/reproduce.sh` (Linux/WSL) and `poc/reproduce.ps1`
(Windows) — they start the lab, wait for the console, fire the three requests
and save every output to `cve/CVE-2017-1000028/evidence/`.

Screenshots to attach (see `evidence/SCREENSHOTS.md`):
`01-container-running.png`, `02-console-login.png`, `03-poc-etc-passwd.png`,
`04-poc-environ.png`, `05-fixed-403.png`, `06-verify-fix.png`.

### 5.3 Root cause analysis

The console maps a request URI onto a file inside the theme directory. That
mapping performs three steps in the wrong order:

1. **Percent-decode with a lenient UTF-8 decoder.** Legal UTF-8 forbids
   non-shortest-form sequences, but the decoder accepts `%c0%ae` and returns
   `.` (CWE-178). The traversal therefore only *appears* after decoding — any
   defence that inspects the raw URI for `..` sees nothing suspicious.
2. **No canonicalisation.** The decoded path is never passed through
   `normalize()` / `getCanonicalPath()`, so `../../../../etc/passwd` keeps its
   `..` segments all the way to the file lookup (CWE-22).
3. **No base-directory check.** Even with canonicalisation, the safe pattern is
   *canonicalise → verify the result still starts with the theme root → open*.
   That verification is missing entirely.

Two enabling conditions turn the bug into a critical one:

* the theme resource handler is reachable **before authentication** — this is
  an unauthenticated file read, not a privilege escalation; and
* the GlassFish process in the container runs as **root**, so "any file the
  process can read" means *every* file, including `/proc/self/environ`.

It is a **canonicalisation / decoding defect**, not an injection or memory
corruption bug. The upstream fix makes URI decoding strict and canonicalises
and validates the path before opening the file.

### 5.4 Fix applied

| # | Change | File |
|---|---|---|
| 1 | **Upgrade to GlassFish ≥ 4.1.2 / 5.0** — strict URI decoding, canonicalise + base-directory check before opening the file — **primary fix** | documented in `README.md` §6.1 |
| 2 | Admin console **no longer published to the host** — reachable only on the internal docker network | `fixed/docker-compose.yml` |
| 3 | **JDWP debug port 5005 removed** (a Java debugger port is remote code execution by design) | `fixed/docker-compose.yml` |
| 4 | Reverse proxy rejects **overlong UTF-8** (`%c0`, `%e0`, `%f0`, `%f8`, `%fc`) and traversal sequences (`../`, `%2e%2e`, `%252e`) | `fixed/nginx.conf` |
| 5 | Proxy bound to **127.0.0.1** only | `fixed/docker-compose.yml` |
| 6 | Backend version banners hidden (`Server`, `X-Powered-By`) | `fixed/nginx.conf` |
| 7 | Administrator password externalised to `.env` instead of hard-coded | `fixed/.env.example` |

Upgrading removes the *cause* (lenient decoding + missing canonicalisation);
the other measures reduce exposure and blast radius (defence in depth) and add
detection. Note that a reverse proxy alone is **not** a fix — it is a
compensating control that must be paired with the version upgrade.

### 5.5 Proof that the vulnerability is gone

```bash
cd cve/CVE-2017-1000028/fixed && cp .env.example .env && docker compose up -d
cd .. && python poc/verify_fix.py          # vulnerable stack must still be up
```

Real output (`evidence/verify-fix.txt`):

```
==============================================================================
CVE-2017-1000028 - fix verification (vulnerable vs hardened)
==============================================================================
[PASS] A. vulnerable env: exploit works           HTTP 200, /etc/passwd marker=yes
[PASS] B. hardened env: exploit blocked           HTTP 403, /etc/passwd marker=no
[PASS] C. hardened env: console still usable      HTTP 302 -> http://127.0.0.1/login.jsf
------------------------------------------------------------------------------
RESULT: ALL CHECKS PASSED
```

* A is the **control group**: the exploit still works against the untouched
  container, so a "pass" in B is meaningful.
* B proves the mitigation: the same payload now returns `403 Forbidden` from
  nginx (`evidence/fix-poc-blocked.txt`).
* C proves the console was **not** broken — the fix is not simply "switch the
  service off".

Screenshots to attach: `evidence/05-fixed-403.png` (403),
`evidence/06-verify-fix.png` (all checks passed).

---

## 6. Repository layout

```
.
├── app/                      application package
│   ├── __init__.py           app factory, security headers
│   ├── models.py             ORM models (User, Post)
│   ├── routes.py             endpoints
│   ├── security.py           bcrypt, JWT, token middleware, escaping
│   └── seed.py               demo data (hashed passwords)
├── tests/test_api.py         11 automated security tests
├── .github/workflows/ci.yml  CI/CD: pytest + Bandit + pip-audit
├── cve/CVE-2017-1000028/     vulnerable env, PoC, fixed env, evidence
├── docs/                     API demo transcript, report
├── postman/                  Postman collection
├── scripts/api_smoke_test.py real HTTP smoke test
├── requirements.txt / requirements-dev.txt
└── run.py
```

---

## 7. Ethics

The CVE was reproduced only in a disposable localhost Docker lab created from
Vulhub for this coursework. No third-party system was targeted, and the fixed
environment binds its ports to `127.0.0.1`.
