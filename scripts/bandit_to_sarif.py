"""Convert a Bandit JSON report into a SARIF 2.1.0 document.

Bandit releases before 1.7.5 (and some packaging of 1.7.x) do not ship a
native ``-f sarif`` formatter, which makes ``bandit -f sarif`` fail with
"invalid choice". This script builds the SARIF document from the JSON report
instead, so the CI pipeline can always publish results to the GitHub
"Security" tab.

Usage
-----
    python scripts/bandit_to_sarif.py bandit-report.json bandit.sarif
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
TOOL_NAME = "bandit"
TOOL_URI = "https://bandit.readthedocs.io/"
RULE_HELP_URI = "https://bandit.readthedocs.io/en/latest/plugins/{test_id}.html"

# Bandit severity/confidence -> SARIF level
LEVEL_MAP = {
    "HIGH": "error",
    "MEDIUM": "warning",
    "LOW": "note",
    "UNDEFINED": "none",
}


def _relative_uri(filename: str) -> str:
    """SARIF wants repo-relative POSIX paths."""
    path = filename.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if os.path.isabs(path):
        path = os.path.basename(path)
    return path


def build_sarif(report: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    rules: dict[str, dict[str, Any]] = {}

    for item in report.get("results", []):
        test_id = item.get("test_id", "B000")
        severity = str(item.get("issue_severity", "UNDEFINED")).upper()

        rules.setdefault(
            test_id,
            {
                "id": test_id,
                "name": item.get("test_name", test_id),
                "shortDescription": {"text": item.get("test_name", test_id)},
                "fullDescription": {"text": item.get("issue_text", "")},
                "helpUri": RULE_HELP_URI.format(test_id=test_id),
                "defaultConfiguration": {"level": LEVEL_MAP.get(severity, "warning")},
                "properties": {
                    "confidence": item.get("issue_confidence", "UNDEFINED"),
                    "tags": ["security", "static-analysis"],
                },
            },
        )

        results.append(
            {
                "ruleId": test_id,
                "level": LEVEL_MAP.get(severity, "warning"),
                "message": {
                    "text": "{}: {}".format(
                        item.get("issue_text", ""), item.get("issue_cwe", {}).get("id", "")
                    ).strip()
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": _relative_uri(item.get("filename", "")),
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": max(1, int(item.get("line_number") or 1)),
                                "startColumn": max(1, int(item.get("col_offset") or 1) + 1),
                                "snippet": {"text": (item.get("code") or "").strip()},
                            },
                        }
                    }
                ],
                "properties": {
                    "issue_confidence": item.get("issue_confidence", "UNDEFINED"),
                    "issue_severity": severity,
                },
            }
        )

    metrics = report.get("metrics", {}).get("_totals", {})

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "informationUri": TOOL_URI,
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "properties": {
                            "linesOfCode": metrics.get("loc", 0),
                            "issuesBySeverity": {
                                "high": metrics.get("SEVERITY.HIGH", 0),
                                "medium": metrics.get("SEVERITY.MEDIUM", 0),
                                "low": metrics.get("SEVERITY.LOW", 0),
                            },
                        },
                    }
                ],
                "originalUriBaseIds": {"%SRCROOT%": {"uri": "file:///"}},
            }
        ],
    }


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else "bandit-report.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "bandit.sarif"

    with open(src, encoding="utf-8") as handle:
        report = json.load(handle)

    sarif = build_sarif(report)
    with open(dst, "w", encoding="utf-8") as handle:
        json.dump(sarif, handle, indent=2)

    total = len(sarif["runs"][0]["results"])
    print(f"SARIF written to {dst} ({total} result(s), "
          f"{len(sarif['runs'][0]['tool']['driver']['rules'])} rule(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
