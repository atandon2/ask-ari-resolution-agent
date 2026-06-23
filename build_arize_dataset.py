"""Build an Arize AX dataset CSV from Ask Ari validation cases.

Upload the generated CSV in Arize via:
Develop / Datasets & Experiments -> + New Dataset -> Upload CSV.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


VALIDATION_CASES_PATH = Path("validation_cases.csv")
ARIZE_DATASET_PATH = Path("arize_ask_ari_dataset.csv")

ARIZE_DATASET_FIELDS = [
    "id",
    "persona",
    "request",
    "attributes.input.value",
    "attributes.metadata.case_id",
    "attributes.metadata.persona",
    "attributes.metadata.notes",
    "expected_intent",
    "expected_tables",
    "expected_approval",
    "expected_customer_scope",
    "expected_output_json",
]


def _parse_tables(value: str) -> list[str]:
    return value.split("|") if value else []


def build_arize_dataset_rows(
    input_path: Path = VALIDATION_CASES_PATH,
) -> list[dict[str, str]]:
    """Return validation rows shaped for Arize dataset upload."""

    with input_path.open(newline="", encoding="utf-8") as input_file:
        validation_rows = list(csv.DictReader(input_file))

    arize_rows = []
    for row in validation_rows:
        expected_output = {
            "expected_intent": row["expected_intent"],
            "expected_tables": _parse_tables(row["expected_tables"]),
            "expected_approval": row["expected_approval"],
            "expected_customer_scope": row["expected_customer_scope"],
        }
        arize_rows.append(
            {
                "id": row["id"],
                "persona": row["persona"],
                "request": row["request"],
                "attributes.input.value": row["request"],
                "attributes.metadata.case_id": row["id"],
                "attributes.metadata.persona": row["persona"],
                "attributes.metadata.notes": row["notes"],
                "expected_intent": row["expected_intent"],
                "expected_tables": row["expected_tables"],
                "expected_approval": row["expected_approval"],
                "expected_customer_scope": row["expected_customer_scope"],
                "expected_output_json": json.dumps(
                    expected_output,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
    return arize_rows


def write_arize_dataset(
    output_path: Path = ARIZE_DATASET_PATH,
    input_path: Path = VALIDATION_CASES_PATH,
) -> Path:
    """Write the Arize upload CSV and return its path."""

    rows = build_arize_dataset_rows(input_path)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=ARIZE_DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


if __name__ == "__main__":
    path = write_arize_dataset()
    print(f"Wrote {path}")
