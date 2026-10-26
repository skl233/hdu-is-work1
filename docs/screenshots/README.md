# Screenshots of the CI/CD security scans

Put the following PNG files in this folder; they are referenced by `README.md`
and by the report. They prove that the SAST/SCA checks ran inside the pipeline.

| File | Where to take it |
|---|---|
| `01-actions-green.png` | Repository → **Actions** → latest run: all three jobs (Tests, SAST, SCA) green |
| `02-bandit-sast.png` | Actions → run → job **SAST (Bandit)** → expanded step "Static analysis of application code" (`No issues identified`) |
| `03-pip-audit-sca.png` | Actions → run → job **SCA (pip-audit)** → expanded step (`No known vulnerabilities found`) |
| `04-artifacts.png` | Bottom of the run page: artifacts `bandit-report` and `pip-audit-report` |

Until the screenshots exist, the README shows the placeholders; the verified
command-line equivalents are already recorded in `README.md` section 4 and in
`docs/scan-evidence.md`.
