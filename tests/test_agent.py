import csv
from pathlib import Path

import pytest

from agent import CLASSIFIER_MODE, SCENARIOS, classify_with_llm, run_agent
from run_validation_checks import run_validation_checks


EXPECTED_SCENARIOS = {
    "A": {
        "intent": "customer_escalation",
        "tables": [
            "customer_accounts",
            "support_tickets",
            "jira_bugs",
            "product_telemetry",
            "campaign_performance",
        ],
        "approval": "not_required",
        "scope": "authorized",
    },
    "B": {
        "intent": "marketing_investigation",
        "tables": [
            "audience_segments",
            "audience_exports",
            "journey_executions",
            "campaign_performance",
            "product_telemetry",
        ],
        "approval": "not_required",
        "scope": "authorized",
    },
    "C": {
        "intent": "technical_investigation",
        "tables": [
            "incidents",
            "product_telemetry",
            "support_tickets",
            "jira_bugs",
        ],
        "approval": "not_required",
        "scope": "authorized",
    },
    "D": {
        "intent": "access_request",
        "tables": ["customer_export_logs", "audience_exports"],
        "approval": "pending",
        "scope": "authorized",
    },
    "E": {
        "intent": "numeric_analysis",
        "tables": ["audience_exports", "customer_accounts"],
        "approval": "not_required",
        "scope": "authorized",
    },
    "F": {
        "intent": "clarification",
        "tables": [],
        "approval": "not_required",
        "scope": "clarification_required",
    },
    "G": {
        "intent": "restricted_data_export",
        "tables": ["customer_export_logs"],
        "approval": "rejected",
        "scope": "unauthorized",
    },
    "H": {
        "intent": "customer_escalation",
        "tables": [
            "customer_accounts",
            "support_tickets",
            "jira_bugs",
            "product_telemetry",
            "campaign_performance",
        ],
        "approval": "rejected",
        "scope": "unauthorized",
    },
}


@pytest.mark.parametrize("scenario_id", list("ABCDEFGH"))
def test_canonical_scenario_outcome(scenario_id):
    scenario = SCENARIOS[scenario_id]
    expected = EXPECTED_SCENARIOS[scenario_id]

    result = run_agent(scenario["persona"], scenario["request"])

    assert result["intent"] == expected["intent"]
    assert result["selected_tables"] == expected["tables"]
    assert result["approval"] == expected["approval"]
    assert result["customer_scope"] == expected["scope"]
    assert result["eval_target"] == {
        "expected_intent": expected["intent"],
        "expected_tables": expected["tables"],
        "expected_approval": expected["approval"],
        "expected_customer_scope": expected["scope"],
    }
    assert all(comparison["match"] for comparison in result["eval_result"].values())


def test_classifier_boundary_is_explicit():
    assert CLASSIFIER_MODE == "deterministic"
    with pytest.raises(NotImplementedError, match="LLM classifier"):
        classify_with_llm("Emily Chen", "Prepare a briefing")


def test_ambiguous_request_asks_for_clarification_without_data_access():
    result = run_agent("Emily Chen", "Pull everything I need for tomorrow.")

    assert result["intent"] == "clarification"
    assert result["selected_tables"] == []
    assert result["proposed_sql"] is None
    assert "which customer" in result["response"].lower()
    assert "objective" in result["response"].lower()


def test_unauthorized_customer_scope_is_rejected():
    result = run_agent(
        "Alex Rivera",
        "Nike is threatening to escalate. Prepare me for tomorrow’s executive review.",
    )

    assert result["customer_scope"] == "unauthorized"
    assert result["approval"] == "rejected"
    assert "not assigned to nike" in result["response"].lower()
    assert "safer next action" in result["response"].lower()


def test_broad_customer_export_is_rejected():
    result = run_agent(
        "Maya Patel", "Export all customer-level export logs from last year."
    )

    assert result["intent"] == "restricted_data_export"
    assert result["approval"] == "rejected"
    assert "aggregate report" in result["response"].lower()
    assert "safer next action" in result["response"].lower()


def test_guided_access_escalation_describes_approval_delivery():
    scenario = SCENARIOS["D"]
    result = run_agent(scenario["persona"], scenario["request"])
    response = result["response"].lower()

    assert "sarah kim" in response
    assert "customer data governance manager" in response
    assert "approval queue" in response
    assert "slack dm" in response
    assert "email" in response
    assert "4 hours" in response
    assert "pending" in response


def test_numeric_analysis_uses_aggregate_tables_only():
    scenario = SCENARIOS["E"]
    result = run_agent(scenario["persona"], scenario["request"])

    assert result["selected_tables"] == ["audience_exports", "customer_accounts"]
    assert "customer_export_logs" not in result["proposed_sql"]
    assert "145" in result["response"]
    assert "37" in result["response"]
    assert "292%" in result["response"]
    assert "aggregate" in result["response"].lower()
    assert "raw" in result["response"].lower()


def test_sql_is_generated_only_for_scenario_e():
    for scenario_id, scenario in SCENARIOS.items():
        result = run_agent(scenario["persona"], scenario["request"])
        assert (result["proposed_sql"] is not None) == (scenario_id == "E")


def test_every_run_has_an_observable_workflow_trace():
    scenario = SCENARIOS["A"]
    first = run_agent(scenario["persona"], scenario["request"])
    second = run_agent(scenario["persona"], scenario["request"])

    assert first["trace_id"] != second["trace_id"]
    assert first["user_asked"] == scenario["request"]
    assert first["agent_inferred"]
    assert [event["sequence"] for event in first["trace_log"]] == list(
        range(1, len(first["trace_log"]) + 1)
    )
    steps = [event["step"] for event in first["trace_log"]]
    assert steps[0] == "workflow.started"
    assert "classification.completed" in steps
    assert any(step.startswith("tool.") for step in steps)
    assert steps[-1] == "workflow.completed"


def test_eval_dataset_has_twenty_labeled_cases():
    csv_path = Path(__file__).parents[1] / "validation_cases.csv"
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == [
        "id",
        "persona",
        "request",
        "expected_intent",
        "expected_tables",
        "expected_approval",
        "expected_customer_scope",
        "notes",
    ]
    assert len(rows) == 20


def test_all_validation_cases_match_their_labels():
    csv_path = Path(__file__).parents[1] / "validation_cases.csv"
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    for case in rows:
        result = run_agent(case["persona"], case["request"])
        expected_tables = (
            case["expected_tables"].split("|") if case["expected_tables"] else []
        )
        assert result["intent"] == case["expected_intent"], case["id"]
        assert result["selected_tables"] == expected_tables, case["id"]
        assert result["approval"] == case["expected_approval"], case["id"]
        assert result["customer_scope"] == case["expected_customer_scope"], case["id"]


def test_validation_runner_can_execute(tmp_path):
    output_path = tmp_path / "validation_results.csv"

    summary = run_validation_checks(
        Path(__file__).parents[1] / "validation_cases.csv",
        output_path,
    )

    assert summary == {"total": 20, "passed": 20, "failed": 0}
    assert output_path.exists()
