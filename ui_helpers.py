"""Small presentation helpers for the response-first Streamlit UI."""

from __future__ import annotations

from typing import Any


TRACE_COLUMNS = [
    "Step",
    "What the user asked / input",
    "What the agent inferred / output",
]


def _pretty(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "None"


def eval_checklist(result: dict[str, Any]) -> list[str]:
    """Return a screenshot-friendly canonical eval summary."""

    if not result["eval_target"]:
        return ["No labeled eval target."]
    labels = {
        "intent": "Intent",
        "selected_tables": "Tables",
        "approval": "Approval",
        "customer_scope": "Scope",
    }
    return [
        f"{label} {'✅' if result['eval_result'][key]['match'] else '❌'}"
        for key, label in labels.items()
    ]


def split_safer_next_action(response: str) -> tuple[str, str | None]:
    """Separate rejection guidance so the UI can emphasize it."""

    marker = "**Safer next action:**"
    if marker not in response:
        return response, None
    body, action = response.split(marker, 1)
    return body.rstrip(), action.strip()


def build_decision_rows(
    result: dict[str, Any], persona_context: dict[str, Any]
) -> list[dict[str, str]]:
    """Create a curated input/output decision record from structured results."""

    customer = result.get("customer") or "Not inferred"
    assigned_scope = _join(persona_context["assigned_customers"])
    tables = _join(result["selected_tables"])
    tools = _join(result["tools_used"])

    if result["customer_scope"] == "clarification_required":
        policy_output = "Not evaluated until the request is clarified."
    elif result["approval"] == "pending":
        policy_output = "Restricted data requires temporary approval."
    elif result["approval"] == "rejected":
        policy_output = "Access blocked by employee access or data policy."
    else:
        policy_output = "Access policy passed."

    if result["approval"] == "pending":
        approval_output = (
            "Status: Pending · Sarah Kim, Customer Data Governance Manager · "
            "Approval Queue + Slack DM + Email · Duration: 4 hours"
        )
    else:
        approval_output = f"Approval: {_pretty(result['approval'])}"

    target = result["eval_target"]
    if target:
        eval_input = (
            f"Intent: {target['expected_intent']} · "
            f"Tables: {_join(target['expected_tables'])} · "
            f"Approval: {target['expected_approval']} · "
            f"Scope: {target['expected_customer_scope']}"
        )
    else:
        eval_input = "No canonical target"

    return [
        {
            "Step": "Classification",
            "What the user asked / input": result["user_asked"],
            "What the agent inferred / output": (
                f"What the agent inferred: {result['agent_inferred']}\n"
                f"Intent: {result['intent']}\nCustomer: {customer}"
            ),
        },
        {
            "Step": "Employee access",
            "What the user asked / input": (
                f"Persona: {persona_context['name']} · Employee access: {assigned_scope}"
            ),
            "What the agent inferred / output": (
                f"Customer: {customer} · Decision: {_pretty(result['customer_scope'])}"
            ),
        },
        {
            "Step": "Access policy",
            "What the user asked / input": f"Data sources considered: {tables}",
            "What the agent inferred / output": policy_output,
        },
        {
            "Step": "Tools and data",
            "What the user asked / input": f"Selected tools: {tools}",
            "What the agent inferred / output": f"Selected data sources: {tables}",
        },
        {
            "Step": "Approval",
            "What the user asked / input": f"Risk level: {_pretty(result['risk'])}",
            "What the agent inferred / output": approval_output,
        },
        {
            "Step": "Evaluation",
            "What the user asked / input": eval_input,
            "What the agent inferred / output": " · ".join(eval_checklist(result)),
        },
    ]
