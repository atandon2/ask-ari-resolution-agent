import csv
import json

from build_arize_dataset import ARIZE_DATASET_FIELDS, build_arize_dataset_rows


def test_build_arize_dataset_rows_maps_validation_cases_for_upload():
    rows = build_arize_dataset_rows()

    assert len(rows) == 20
    assert set(rows[0]) == set(ARIZE_DATASET_FIELDS)
    assert rows[0]["id"] == "A"
    assert rows[0]["persona"] == "Emily Chen"
    assert rows[0]["attributes.input.value"] == rows[0]["request"]
    assert rows[0]["attributes.metadata.case_id"] == "A"
    assert rows[0]["attributes.metadata.persona"] == "Emily Chen"

    expected = json.loads(rows[0]["expected_output_json"])
    assert expected == {
        "expected_intent": "customer_escalation",
        "expected_tables": [
            "customer_accounts",
            "support_tickets",
            "jira_bugs",
            "product_telemetry",
            "campaign_performance",
        ],
        "expected_approval": "not_required",
        "expected_customer_scope": "authorized",
    }


def test_arize_dataset_csv_exists_and_has_twenty_rows():
    with open("arize_ask_ari_dataset.csv", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == ARIZE_DATASET_FIELDS
    assert len(rows) == 20
    assert rows[5]["expected_intent"] == "clarification"
    assert rows[5]["expected_customer_scope"] == "clarification_required"
