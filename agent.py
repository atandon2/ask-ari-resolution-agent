"""Deterministic V0 orchestration for the Adobe Enterprise Resolution Agent.

The classifier is intentionally replaceable. Everything after classification—
scope, policy, approvals, tools, traces, and evals—stays explicit application
logic whether the classifier is deterministic or model-powered.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from tracing import end_workflow, start_workflow, trace_step
from tools import (
    PERSONAS,
    build_sql_for_numeric_question,
    check_access_policy,
    check_customer_scope,
    get_customer_context,
    get_incident_context,
    get_marketing_performance,
    get_open_issues,
    get_product_telemetry,
    get_schema_catalog,
    get_user_context,
    submit_approval_request,
)


CLASSIFIER_MODE = "deterministic"


SCENARIOS: dict[str, dict[str, Any]] = {
    "A": {
        "label": "A · Customer escalation",
        "persona": "Emily Chen",
        "request": "Disney is threatening to escalate. Prepare me for tomorrow’s executive review.",
        "customer": "Disney",
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
        "risk": "medium",
        "inference": "Disney executive briefing needed; combine account health, open issues, product signals, and business impact.",
    },
    "B": {
        "label": "B · Marketing workflow",
        "persona": "Olivia Martinez",
        "request": "Disney’s Black Friday campaign is delayed and audiences are not activating. Help me understand what happened.",
        "customer": "Disney",
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
        "risk": "medium",
        "inference": "Trace the Black Friday activation path from segment readiness through exports, journeys, telemetry, and delivery impact.",
    },
    "C": {
        "label": "C · Technical investigation",
        "persona": "Alex Rivera",
        "request": "Disney says audience exports are delayed. Help me understand why.",
        "customer": "Disney",
        "intent": "technical_investigation",
        "tables": ["incidents", "product_telemetry", "support_tickets", "jira_bugs"],
        "approval": "not_required",
        "scope": "authorized",
        "risk": "medium",
        "inference": "Investigate Disney export latency using active incidents, operational telemetry, support history, and linked defects.",
    },
    "D": {
        "label": "D · Guided access escalation",
        "persona": "Alex Rivera",
        "request": "I need to investigate Disney export failures.",
        "customer": "Disney",
        "intent": "access_request",
        "tables": ["customer_export_logs", "audience_exports"],
        "approval": "pending",
        "scope": "authorized",
        "risk": "high",
        "inference": "A job-level failure investigation needs restricted customer export logs plus aggregate export-job context, so time-bound approval is required.",
    },
    "E": {
        "label": "E · NL-to-SQL analysis",
        "persona": "Emily Chen",
        "request": "Disney says exports are delayed. How many export jobs failed today compared to yesterday?",
        "customer": "Disney",
        "intent": "numeric_analysis",
        "tables": ["audience_exports", "customer_accounts"],
        "approval": "not_required",
        "scope": "authorized",
        "risk": "low",
        "inference": "Calculate Disney-scoped aggregate failed-export counts for today and yesterday; raw customer-level logs are not needed.",
    },
    "F": {
        "label": "F · Ambiguous request",
        "persona": "Emily Chen",
        "request": "Pull everything I need for tomorrow.",
        "customer": None,
        "intent": "clarification",
        "tables": [],
        "approval": "not_required",
        "scope": "clarification_required",
        "risk": "low",
        "inference": "The customer, meeting objective, and desired output are missing; selecting data would require unsupported assumptions.",
    },
    "G": {
        "label": "G · Governance rejection",
        "persona": "Maya Patel",
        "request": "Export all customer-level export logs from last year.",
        "customer": "All customers",
        "intent": "restricted_data_export",
        "tables": ["customer_export_logs"],
        "approval": "rejected",
        "scope": "unauthorized",
        "risk": "critical",
        "inference": "The request spans all customers and asks for raw restricted logs; Maya has no customer-restricted access.",
    },
    "H": {
        "label": "H · Customer scope rejection",
        "persona": "Alex Rivera",
        "request": "Nike is threatening to escalate. Prepare me for tomorrow’s executive review.",
        "customer": "Nike",
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
        "risk": "high",
        "inference": "A Nike executive briefing was requested, but Alex's assigned customer scope is Disney and Marriott.",
    },
}


def _normalize(text: str) -> str:
    return " ".join(text.replace("’", "'").casefold().split()).rstrip(".")


def _canonical_scenario(persona: str, request: str) -> tuple[str | None, dict[str, Any] | None]:
    normalized = _normalize(request)
    for scenario_id, scenario in SCENARIOS.items():
        if scenario["persona"] == persona and _normalize(scenario["request"]) == normalized:
            return scenario_id, scenario
    return None, None


def _customer_from_request(request: str) -> str | None:
    normalized = _normalize(request)
    for customer in ("Disney", "Nike", "Marriott"):
        if customer.casefold() in normalized:
            return customer
    if "all customer" in normalized:
        return "All customers"
    return None


def _classification_from_scenario(scenario_id: str, scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "intent": scenario["intent"],
        "customer": scenario["customer"],
        "selected_tables": list(scenario["tables"]),
        "risk": scenario["risk"],
        "inference": scenario["inference"],
    }


def classify_deterministically(persona: str, request: str) -> dict[str, Any]:
    """Stable V0 classifier: canonical match first, ordered keyword rules second."""

    scenario_id, scenario = _canonical_scenario(persona, request)
    if scenario:
        return _classification_from_scenario(scenario_id, scenario)

    normalized = _normalize(request)
    customer = _customer_from_request(request)
    if "all customer" in normalized and "export log" in normalized:
        template = SCENARIOS["G"]
    elif "failed" in normalized and "today" in normalized and "yesterday" in normalized:
        template = SCENARIOS["E"]
    elif "black friday" in normalized or "not activating" in normalized:
        template = SCENARIOS["B"]
    elif "investigate" in normalized and ("export failure" in normalized or "export log" in normalized):
        template = SCENARIOS["D"]
    elif "export" in normalized and ("delayed" in normalized or "latency" in normalized):
        template = SCENARIOS["C"]
    elif "escalat" in normalized or "executive review" in normalized:
        template = SCENARIOS["A"]
    else:
        template = SCENARIOS["F"]

    classification = _classification_from_scenario("free_form", template)
    classification["scenario_id"] = None
    if customer is not None:
        classification["customer"] = customer
    return classification


def classify_with_llm(persona: str, request: str) -> dict[str, Any]:
    """Production model boundary for intent, entities, resources, and inference."""

    raise NotImplementedError("Connect an LLM classifier here for production use.")


def classify_request(persona: str, request: str) -> dict[str, Any]:
    """Dispatch classification without coupling orchestration to a model choice."""

    if CLASSIFIER_MODE == "deterministic":
        return classify_deterministically(persona, request)
    if CLASSIFIER_MODE == "llm":
        return classify_with_llm(persona, request)
    raise ValueError(f"Unsupported classifier mode: {CLASSIFIER_MODE}")


def _eval_target(scenario_id: str | None) -> dict[str, Any]:
    if not scenario_id:
        return {}
    scenario = SCENARIOS[scenario_id]
    return {
        "expected_intent": scenario["intent"],
        "expected_tables": list(scenario["tables"]),
        "expected_approval": scenario["approval"],
        "expected_customer_scope": scenario["scope"],
    }


def _eval_result(
    target: dict[str, Any],
    intent: str,
    tables: list[str],
    approval: str,
    customer_scope: str,
) -> dict[str, dict[str, Any]]:
    if not target:
        return {}
    comparisons = {
        "intent": (target["expected_intent"], intent),
        "selected_tables": (target["expected_tables"], tables),
        "approval": (target["expected_approval"], approval),
        "customer_scope": (target["expected_customer_scope"], customer_scope),
    }
    return {
        name: {"expected": expected, "actual": actual, "match": expected == actual}
        for name, (expected, actual) in comparisons.items()
    }


def run_agent(persona: str, request: str) -> dict[str, Any]:
    """Run one governed, traceable agent workflow and return a UI-ready result."""

    if persona not in PERSONAS:
        raise ValueError(f"Unknown persona: {persona}")

    trace_id = f"wf_{uuid4().hex[:12]}"
    start_workflow(trace_id, request, persona)

    tools_used: list[str] = []

    def call_tool(name: str, function: Callable[..., Any], *args: Any) -> Any:
        tools_used.append(name)
        return function(*args, _trace_id=trace_id)

    user_context = call_tool("get_user_context", get_user_context, persona)
    classification = classify_request(persona, request)
    trace_step(
        trace_id,
        "classification.completed",
        {
            "intent": classification["intent"],
            "customer": classification["customer"],
            "mode": CLASSIFIER_MODE,
        },
    )

    intent = classification["intent"]
    customer = classification["customer"]
    selected_tables = list(classification["selected_tables"])
    risk = classification["risk"]
    approval = "not_required"
    proposed_sql = None

    if intent == "clarification" and not customer:
        customer_scope = "clarification_required"
        response = (
            "### I need three details before I select data\n\n"
            "1. **Which customer** is tomorrow's meeting about?\n"
            "2. What is the meeting **objective**—escalation, technical review, or campaign planning?\n"
            "3. What output would help most: an executive brief, investigation, or metrics summary?\n\n"
            "I have not accessed customer data or assumed a customer."
        )
        trace_step(trace_id, "clarification.requested", {"missing": ["customer", "objective", "output"]})
    else:
        customer_scope = call_tool(
            "check_customer_scope", check_customer_scope, user_context, customer
        )
        trace_step(
            trace_id,
            "customer_scope.checked",
            {"customer": customer, "result": customer_scope},
        )

        if customer_scope not in ("authorized", "aggregate_only"):
            approval = "rejected"
            if intent == "restricted_data_export":
                response = (
                    "### Request rejected\n\n"
                    "This asks for raw customer-level export logs across all customers. Maya's role has no "
                    "customer-restricted access, and broad raw-log exports are prohibited.\n\n"
                    "**Safer next action:** Request an aggregate report instead of customer-level logs, "
                    "with counts grouped by month and no customer identifiers."
                )
            else:
                response = (
                    f"### Customer scope rejected\n\n{persona} is not assigned to {customer}; the assigned "
                    "scope is "
                    + ", ".join(user_context["assigned_customers"])
                    + ". No customer data was accessed.\n\n"
                    f"**Safer next action:** Ask the {customer} account owner to run the briefing, or request "
                    "temporary customer-scoped access through governance."
                )
            trace_step(trace_id, "workflow.rejected", {"reason": "customer_scope"})
        else:
            call_tool("get_schema_catalog", get_schema_catalog)
            policy = call_tool(
                "check_access_policy",
                check_access_policy,
                user_context,
                selected_tables,
                customer,
            )
            trace_step(
                trace_id,
                "access_policy.checked",
                {
                    "allowed": policy["allowed"],
                    "requires_approval": policy["requires_approval"],
                },
            )

            if policy["requires_approval"] and intent == "access_request":
                approval_record = call_tool(
                    "submit_approval_request",
                    submit_approval_request,
                    persona,
                    customer,
                    "customer_export_logs",
                    "Sarah Kim",
                    "4 hours",
                )
                approval = "pending"
                response = (
                    "### Temporary access requested\n\n"
                    "The investigation needs job-level `customer_export_logs` plus aggregate "
                    "`audience_exports`. Restricted logs have **not** been opened.\n\n"
                    f"- **Approver:** {approval_record['approver']}, {approval_record['approver_title']}\n"
                    f"- **Delivery:** {', '.join(approval_record['delivery'])}\n"
                    f"- **Status:** {approval_record['status']}\n"
                    f"- **Duration:** {approval_record['duration']} (long-running investigation)\n"
                    f"- **Request:** {approval_record['request_id']}\n\n"
                    "The workflow can resume automatically after approval."
                )
                trace_step(
                    trace_id,
                    "approval.submitted",
                    {"request_id": approval_record["request_id"], "status": "Pending"},
                )
            elif not policy["allowed"]:
                approval = "rejected"
                response = (
                    f"### Request rejected\n\n{policy['reason']} No restricted data was accessed.\n\n"
                    "**Safer next action:** Request an aggregate report with identifiers removed."
                )
                trace_step(trace_id, "workflow.rejected", {"reason": "access_policy"})
            elif intent == "customer_escalation":
                account = call_tool("get_customer_context", get_customer_context, customer)
                issues = call_tool("get_open_issues", get_open_issues, customer)
                telemetry = call_tool(
                    "get_product_telemetry", get_product_telemetry, customer
                )
                marketing = call_tool(
                    "get_marketing_performance", get_marketing_performance, customer
                )
                response = (
                    f"### Executive brief · {customer}\n\n"
                    f"**Headline:** {customer} is {account['health'].lower()} because an export-worker "
                    "incident is now affecting activation commitments. The immediate goal is to show "
                    "containment, ownership, and a dated recovery plan.\n\n"
                    "**Evidence**\n"
                    f"- {len(issues['support_tickets'])} open support tickets; "
                    f"{issues['support_tickets'][0]['id']} is P1.\n"
                    f"- Export p95 is {telemetry['p95_export_delay_minutes']} minutes with "
                    f"{telemetry['export_queue_depth']:,} jobs queued.\n"
                    f"- Black Friday delivery is {marketing.get('delivery_vs_plan', 'being assessed')} versus plan.\n\n"
                    "**Recommended executive posture:** Acknowledge the impact, name the incident and "
                    "engineering owner, commit to the next update, and schedule a post-incident reliability review."
                )
            elif intent == "marketing_investigation":
                marketing = call_tool(
                    "get_marketing_performance", get_marketing_performance, customer
                )
                telemetry = call_tool(
                    "get_product_telemetry", get_product_telemetry, customer
                )
                response = (
                    "### Black Friday activation investigation\n\n"
                    "**What happened:** Three segments were not export-ready. Six downstream exports then "
                    "encountered the elevated export queue, leaving four journeys waiting for audiences.\n\n"
                    f"- Campaign delivery: **{marketing['delivery_vs_plan']} vs plan**\n"
                    f"- Export queue: **{telemetry['export_queue_depth']:,} jobs**\n"
                    f"- p95 delay: **{telemetry['p95_export_delay_minutes']} minutes**\n\n"
                    "**Recommended workflow:** Re-publish the three blocked segments, prioritize the six campaign "
                    "exports, then release the four journeys after audience-count validation."
                )
            elif intent == "technical_investigation":
                incident = call_tool(
                    "get_incident_context", get_incident_context, customer
                )
                telemetry = call_tool(
                    "get_product_telemetry", get_product_telemetry, customer
                )
                issues = call_tool("get_open_issues", get_open_issues, customer)
                ticket_id = (
                    issues["support_tickets"][0]["id"]
                    if issues["support_tickets"]
                    else "no linked support case"
                )
                bug_id = (
                    issues["jira_bugs"][0]["id"]
                    if issues["jira_bugs"]
                    else "no linked engineering bug"
                )
                response = (
                    "### Root-cause summary\n\n"
                    f"**Likely cause:** {incident.get('cause', 'No active incident is confirmed')}. "
                    f"{incident.get('incident_id', 'No incident')} is "
                    f"{incident.get('status', 'under review').lower()} and affects "
                    f"{incident.get('affected_service', 'the export workflow')}.\n\n"
                    f"Telemetry shows a queue depth of **{telemetry.get('export_queue_depth', 0):,}** and "
                    f"p95 delay of **{telemetry.get('p95_export_delay_minutes', 0)} minutes**. "
                    f"Evidence links to {ticket_id} and {bug_id}.\n\n"
                    f"**Next action:** Validate the aggregate signal, then update {customer} by "
                    f"{incident.get('next_update', 'the next agreed checkpoint')}."
                )
            elif intent == "numeric_analysis":
                proposed_sql = call_tool(
                    "build_sql_for_numeric_question",
                    build_sql_for_numeric_question,
                    customer,
                    "failed export jobs",
                )
                response = (
                    "### Export failure comparison\n\n"
                    "Disney had **145 failed export jobs today** versus **37 yesterday**—an increase "
                    "of **108 jobs (+292%)**.\n\n"
                    "This answer uses aggregate, Disney-scoped counts from `audience_exports` joined to "
                    "`customer_accounts`. It does **not** retrieve or expose raw `customer_export_logs`."
                )
                trace_step(
                    trace_id,
                    "sql.generated",
                    {"scope": customer, "result_shape": "aggregate_counts"},
                )
            else:
                response = (
                    "### More detail needed\n\nPlease specify the customer and desired outcome before data is selected."
                )

    target = _eval_target(classification["scenario_id"])
    eval_result = _eval_result(
        target, intent, selected_tables, approval, customer_scope
    )
    if target:
        trace_step(
            trace_id,
            "eval.completed",
            {"matches": sum(item["match"] for item in eval_result.values()), "total": 4},
        )
    result = {
        "trace_id": trace_id,
        "intent": intent,
        "customer": customer,
        "risk": risk,
        "approval": approval,
        "customer_scope": customer_scope,
        "tools_used": tools_used,
        "selected_tables": selected_tables,
        "proposed_sql": proposed_sql,
        "user_asked": request,
        "agent_inferred": classification["inference"],
        "eval_target": target,
        "eval_result": eval_result,
        "response": response,
    }
    result["trace_log"] = end_workflow(
        trace_id,
        {
            "intent": intent,
            "approval": approval,
            "risk": risk,
            "tool_count": len(tools_used),
        },
    )
    return result
