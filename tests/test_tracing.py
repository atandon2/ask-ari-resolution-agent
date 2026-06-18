from pathlib import Path

from agent import SCENARIOS, run_agent
from tracing import end_workflow, get_trace_log, start_workflow, trace_step


REQUIRED_RESULT_FIELDS = {
    "trace_id",
    "trace_log",
    "intent",
    "risk",
    "approval",
    "customer_scope",
    "tools_used",
    "selected_tables",
    "proposed_sql",
    "eval_target",
    "response",
}


def test_trace_lifecycle_is_ordered():
    start_workflow("trace-1", "Investigate Disney", "Alex Rivera")
    trace_step(
        "trace-1",
        "classification.completed",
        {"intent": "technical_investigation"},
    )
    trace = end_workflow(
        "trace-1",
        {"intent": "technical_investigation", "approval": "not_required"},
    )

    assert [event["step"] for event in trace] == [
        "workflow.started",
        "classification.completed",
        "workflow.completed",
    ]
    assert [event["sequence"] for event in trace] == [1, 2, 3]
    assert trace[0]["payload"] == {
        "request": "Investigate Disney",
        "persona": "Alex Rivera",
    }
    assert trace[-1]["payload"]["approval"] == "not_required"


def test_get_trace_log_returns_a_copy():
    start_workflow("trace-copy", "Prepare a briefing", "Emily Chen")
    trace = get_trace_log("trace-copy")
    trace[0]["payload"]["persona"] = "Changed"

    assert get_trace_log("trace-copy")[0]["payload"]["persona"] == "Emily Chen"


def test_agent_result_contains_required_fields_and_complete_trace():
    scenario = SCENARIOS["A"]
    result = run_agent(scenario["persona"], scenario["request"])

    assert REQUIRED_RESULT_FIELDS <= result.keys()
    assert result["trace_log"][0]["step"] == "workflow.started"
    assert result["trace_log"][-1]["step"] == "workflow.completed"
    assert any(
        event["step"].startswith("tool.") for event in result["trace_log"]
    )


def test_tracing_module_is_the_single_trace_storage_boundary():
    root = Path(__file__).parents[1]
    tracing_source = (root / "tracing.py").read_text(encoding="utf-8")
    tools_source = (root / "tools.py").read_text(encoding="utf-8")
    agent_source = (root / "agent.py").read_text(encoding="utf-8")

    assert "_TRACE_LOGS" in tracing_source
    assert "_TRACE_LOGS" not in tools_source
    assert "_TRACE_LOGS" not in agent_source
    assert "from tracing import" in tools_source
    assert "from tracing import" in agent_source
