# Local verification of the CI/CD security scanners

The pipeline in `.github/workflows/ci.yml` runs exactly these commands. They
were executed locally (Python 3.11, Windows 11) before pushing.

## 1. Unit tests — `pytest -q`

```
11 passed, 12 warnings in 8.54s
```

Tests: `tests/test_api.py`

1. `test_login_returns_jwt`
2. `test_login_rejects_wrong_password`
3. `test_login_rejects_unknown_user_without_user_enumeration`
4. `test_protected_endpoint_without_token_is_denied`
5. `test_protected_endpoint_with_token_returns_data`
6. `test_tampered_token_is_rejected`
7. `test_expired_token_is_rejected`
8. `test_sql_injection_payload_is_not_executed`
9. `test_password_is_stored_hashed`
10. `test_xss_payload_is_escaped_on_output`
11. `test_posts_search_is_parameterised`

## 2. SAST — `bandit -r app -ll -ii`

```
[main]  INFO    running on Python 3.11.9
Run started:2026-10-20 02:48:36.989268+00:00

Test results:
        No issues identified.

Code scanned:
        Total lines of code: 331

Run metrics:
        Total issues (by severity):
                Undefined: 0
                Low: 1
                Medium: 0
                High: 0
```

(`-ll` reports medium/high severity only. The single low finding is `B105` on
the demo seed passwords in `app/seed.py`; it is annotated `# nosec` because
those are teaching fixtures, not production secrets.)

## 3. SCA — `pip-audit -r requirements.txt --strict`

```
No known vulnerabilities found
```

## 4. Runtime behaviour — `python scripts/api_smoke_test.py`

Full transcript: `docs/api-demo-output.txt` (8 requests: wrong password 401,
valid login 200 + JWT, protected endpoint 401/200, tampered token 401, SQLi
401, XSS escaped 201, parameterised search 200).
