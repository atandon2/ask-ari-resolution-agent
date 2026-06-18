"""Run deterministic validation checks without optional integration dependencies."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from agent import run_agent


RESULT_FIELDS = [
    "id",
    "persona",
    "request",
    "trace_id",
    "expected_intent",
    "actual_intent",
    "intent_match",
    "expected_tables",
    "actual_tables",
    "tables_match",
    "expected_approval",
    "actual_approval",
    "approval_match",
    "expected_customer_scope",
    "actual_customer_scope",
    "customer_scope_match",
    "overall_pass",
    "notes",
]


def _parse_tables(value: str) -> list[str]:
    return value.split("|") if value else []


def _serialize_tables(tables: list[str]) -> str:
    return "|".join(tables)


def evaluate_case(case: dict[str, str]) -> dict[str, Any]:
    """Run one labeled request and return exact-match comparison fields."""

    result = run_agent(case["persona"], case["request"])
    expected_tables = _parse_tables(case["expected_tables"])
    comparisons = {
        "intent_match": result["intent"] == case["expected_intent"],
        "tables_match": result["selected_tables"] == expected_tables,
        "approval_match": result["approval"] == case["expected_approval"],
        "customer_scope_match": (
            result["customer_scope"] == case["expected_customer_scope"]
        ),
    }
    return {
        "id": case["id"],
        "persona": case["persona"],
        "request": case["request"],
        "trace_id": result["trace_id"],
        "expected_intent": case["expected_intent"],
        "actual_intent": result["intent"],
        "expected_tables": case["expected_tables"],
        "actual_tables": _serialize_tables(result["selected_tables"]),
        "expected_approval": case["expected_approval"],
        "actual_approval": result["approval"],
        "expected_customer_scope": case["expected_customer_scope"],
        "actual_customer_scope": result["customer_scope"],
        **comparisons,
        "overall_pass": all(comparisons.values()),
        "notes": case["notes"],
    }


def run_validation_checks(
    input_path: Path = Path("validation_cases.csv"),
    output_path: Path = Path("validation_results.csv"),
) -> dict[str, int]:
    """Validate every CSV row, print a summary, and save detailed results."""

    with input_path.open(newline="", encoding="utf-8") as input_file:
        cases = list(csv.DictReader(input_file))

    results = [evaluate_case(case) for case in cases]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    for result in results:
        if not result["overall_pass"]:
            failed_checks = [
                field.replace("_match", "")
                for field in (
                    "intent_match",
                    "tables_match",
                    "approval_match",
                    "customer_scope_match",
                )
                if not result[field]
            ]
            print(f"FAIL {result['id']}: {', '.join(failed_checks)}")

    passed = sum(bool(result["overall_pass"]) for result in results)
    summary = {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
    }
    print(f"Validation checks: {summary['passed']}/{summary['total']} passed")
    print(f"Results written to {output_path}")
    return summary


if __name__ == "__main__":
    run_validation_checks()
