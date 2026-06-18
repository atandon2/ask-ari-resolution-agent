from agent import SCENARIOS, run_agent
from tools import PERSONAS
from ui_helpers import (
    build_decision_rows,
    eval_checklist,
    split_safer_next_action,
)


def test_agent_result_exposes_inferred_customer():
    scenario = SCENARIOS["A"]
    result = run_agent(scenario["persona"], scenario["request"])

    assert result["customer"] == "Disney"


def test_decision_rows_map_request_to_agent_inference():
    scenario = SCENARIOS["A"]
    result = run_agent(scenario["persona"], scenario["request"])
    rows = build_decision_rows(result, PERSONAS[scenario["persona"]])

    assert [row["Step"] for row in rows] == [
        "Classification",
        "Employee access",
        "Access policy",
        "Tools and data",
        "Approval",
        "Evaluation",
    ]
    assert result["user_asked"] in rows[0]["What the user asked / input"]
    assert "What the agent inferred:" in rows[0]["What the agent inferred / output"]
    assert "Intent: customer_escalation" in rows[0]["What the agent inferred / output"]
    assert "Customer: Disney" in rows[0]["What the agent inferred / output"]
    assert "customer_accounts" in rows[3]["What the agent inferred / output"]


def test_canonical_eval_checklist_uses_visual_checks():
    scenario = SCENARIOS["A"]
    result = run_agent(scenario["persona"], scenario["request"])

    assert eval_checklist(result) == [
        "Intent ✅",
        "Tables ✅",
        "Approval ✅",
        "Scope ✅",
    ]


def test_free_form_eval_checklist_has_no_labeled_target():
    result = run_agent(
        "Emily Chen",
        "Please help me think through a customer issue next week.",
    )

    assert result["eval_target"] == {}
    assert eval_checklist(result) == ["No labeled eval target."]


def test_rejection_safer_action_is_separated_from_response():
    scenario = SCENARIOS["G"]
    result = run_agent(scenario["persona"], scenario["request"])

    body, action = split_safer_next_action(result["response"])

    assert "Safer next action" not in body
    assert action is not None
    assert "aggregate report" in action


def test_non_rejection_response_is_unchanged():
    scenario = SCENARIOS["A"]
    result = run_agent(scenario["persona"], scenario["request"])

    body, action = split_safer_next_action(result["response"])

    assert body == result["response"]
    assert action is None
