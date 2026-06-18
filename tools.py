"""Fake enterprise tools and data for the resolution-agent demo.

Nothing in this module connects to an Adobe or customer system. The functions
are deliberately small so a PM can explain each policy and data boundary.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from tracing import trace_step


PERSONAS = {
    "Emily Chen": {
        "name": "Emily Chen",
        "title": "Senior Customer Success Manager",
        "team": "Enterprise Accounts",
        "assigned_customers": ["Disney", "Nike"],
        "access_mode": "assigned_customers",
    },
    "Olivia Martinez": {
        "name": "Olivia Martinez",
        "title": "Senior Solutions Consultant",
        "team": "Experience Cloud",
        "assigned_customers": ["Disney"],
        "access_mode": "assigned_customers",
    },
    "Alex Rivera": {
        "name": "Alex Rivera",
        "title": "Support Engineer",
        "team": "Experience Platform Support",
        "assigned_customers": ["Disney", "Marriott"],
        "access_mode": "assigned_customers",
    },
    "Jason Lee": {
        "name": "Jason Lee",
        "title": "Product Manager",
        "team": "Audience Platform",
        "assigned_customers": [],
        "access_mode": "aggregate_only",
    },
    "Sarah Kim": {
        "name": "Sarah Kim",
        "title": "Customer Data Governance Manager",
        "team": "Trust & Governance",
        "assigned_customers": ["*"],
        "access_mode": "governance",
    },
    "Maya Patel": {
        "name": "Maya Patel",
        "title": "Marketing Manager",
        "team": "Digital Marketing",
        "assigned_customers": [],
        "access_mode": "unrestricted_marketing_only",
    },
}


TABLE_CATALOG = {
    "customer_accounts": {"description": "Account health and ownership", "level": "customer"},
    "support_tickets": {"description": "Open support cases", "level": "customer"},
    "jira_bugs": {"description": "Engineering defects", "level": "customer"},
    "incidents": {"description": "Service incidents", "level": "customer"},
    "product_telemetry": {"description": "Operational product signals", "level": "customer"},
    "audience_segments": {"description": "Audience readiness metadata", "level": "customer"},
    "audience_exports": {"description": "Aggregate export job outcomes", "level": "customer"},
    "journey_executions": {"description": "Journey activation status", "level": "customer"},
    "campaign_performance": {"description": "Campaign delivery metrics", "level": "customer"},
    "customer_export_logs": {"description": "Raw customer-level export logs", "level": "restricted"},
    "access_requests": {"description": "Temporary access requests", "level": "governance"},
    "approval_history": {"description": "Approval audit history", "level": "governance"},
    "data_policies": {"description": "Data access rules", "level": "governance"},
}


CUSTOMER_ACCOUNTS = {
    "Disney": {
        "customer": "Disney",
        "tier": "Strategic",
        "health": "At risk",
        "renewal_window": "Q1",
        "executive_owner": "Emily Chen",
    },
    "Nike": {
        "customer": "Nike",
        "tier": "Strategic",
        "health": "Stable",
        "renewal_window": "Q3",
        "executive_owner": "Emily Chen",
    },
    "Marriott": {
        "customer": "Marriott",
        "tier": "Enterprise",
        "health": "Stable",
        "renewal_window": "Q4",
        "executive_owner": "Customer Success West",
    },
}

OPEN_ISSUES = {
    "Disney": {
        "support_tickets": [
            {"id": "SUP-1842", "severity": "P1", "summary": "Audience exports delayed"},
            {"id": "SUP-1819", "severity": "P2", "summary": "Journey activation backlog"},
        ],
        "jira_bugs": [
            {"id": "AUD-7312", "status": "In progress", "summary": "Export worker retry storm"}
        ],
    },
    "Nike": {"support_tickets": [], "jira_bugs": []},
    "Marriott": {"support_tickets": [], "jira_bugs": []},
}

PRODUCT_TELEMETRY = {
    "Disney": {
        "export_queue_depth": 1820,
        "p95_export_delay_minutes": 47,
        "failed_jobs_today": 145,
        "failed_jobs_yesterday": 37,
        "healthy_worker_ratio": "71%",
    },
    "Nike": {"export_queue_depth": 42, "p95_export_delay_minutes": 4},
    "Marriott": {"export_queue_depth": 38, "p95_export_delay_minutes": 3},
}

MARKETING_PERFORMANCE = {
    "Disney": {
        "campaign": "Black Friday 2026",
        "ready_segments": 8,
        "blocked_segments": 3,
        "exports_delayed": 6,
        "journeys_waiting": 4,
        "delivery_vs_plan": "-18%",
    }
}

INCIDENT_CONTEXT = {
    "Disney": {
        "incident_id": "INC-2468",
        "status": "Mitigating",
        "started": "07:42 PT",
        "affected_service": "Audience Export Workers",
        "cause": "Retry amplification after a connector timeout",
        "next_update": "11:30 PT",
    }
}


def traced_tool(function: Callable[..., Any]) -> Callable[..., Any]:
    """Log every fake tool call without changing its public demo signature."""

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        trace_id = kwargs.pop("_trace_id", None)
        if trace_id:
            trace_step(
                trace_id,
                f"tool.{function.__name__}",
                {"status": "called", "argument_count": len(args)},
            )
        return function(*args, **kwargs)

    return wrapper


@traced_tool
def get_user_context(persona: str) -> dict[str, Any]:
    return dict(PERSONAS[persona])


@traced_tool
def get_customer_context(customer: str) -> dict[str, Any]:
    return dict(CUSTOMER_ACCOUNTS.get(customer, {"customer": customer, "health": "Unknown"}))


@traced_tool
def get_open_issues(customer: str) -> dict[str, Any]:
    return dict(OPEN_ISSUES.get(customer, {"support_tickets": [], "jira_bugs": []}))


@traced_tool
def get_product_telemetry(customer: str) -> dict[str, Any]:
    return dict(PRODUCT_TELEMETRY.get(customer, {}))


@traced_tool
def get_marketing_performance(customer: str) -> dict[str, Any]:
    return dict(MARKETING_PERFORMANCE.get(customer, {}))


@traced_tool
def get_incident_context(customer: str) -> dict[str, Any]:
    return dict(INCIDENT_CONTEXT.get(customer, {}))


@traced_tool
def get_schema_catalog() -> dict[str, dict[str, str]]:
    return {table: dict(details) for table, details in TABLE_CATALOG.items()}


@traced_tool
def check_customer_scope(user_context: dict[str, Any], customer: str | None) -> str:
    if not customer:
        return "clarification_required"
    if user_context["access_mode"] == "governance":
        return "authorized"
    if customer == "All customers":
        return "aggregate_only" if user_context["access_mode"] == "aggregate_only" else "unauthorized"
    if customer in user_context["assigned_customers"]:
        return "authorized"
    return "unauthorized"


@traced_tool
def check_access_policy(
    user_context: dict[str, Any], selected_tables: list[str], customer: str | None
) -> dict[str, Any]:
    restricted = "customer_export_logs" in selected_tables
    if user_context["access_mode"] == "unrestricted_marketing_only" and restricted:
        return {
            "allowed": False,
            "requires_approval": False,
            "reason": "Role has no customer-restricted data access.",
        }
    if customer == "All customers" and restricted:
        return {
            "allowed": False,
            "requires_approval": False,
            "reason": "Broad raw-log exports are prohibited.",
        }
    if restricted:
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": "Raw customer export logs require time-bound governance approval.",
        }
    return {"allowed": True, "requires_approval": False, "reason": "Policy checks passed."}


@traced_tool
def submit_approval_request(
    requester: str,
    customer: str,
    resource: str,
    approver: str,
    duration: str,
) -> dict[str, Any]:
    return {
        "request_id": "AR-2048",
        "requester": requester,
        "customer": customer,
        "resource": resource,
        "approver": approver,
        "approver_title": "Customer Data Governance Manager",
        "duration": duration,
        "status": "Pending",
        "delivery": ["Approval queue", "Slack DM", "Email"],
    }


@traced_tool
def build_sql_for_numeric_question(customer: str, metric: str) -> str:
    """Build aggregate-only SQL; raw customer export logs are never selected."""

    return f"""WITH scoped_exports AS (
    SELECT ae.status, CAST(ae.completed_at AS DATE) AS export_date
    FROM audience_exports AS ae
    JOIN customer_accounts AS ca ON ca.customer_id = ae.customer_id
    WHERE ca.customer_name = '{customer}'
      AND CAST(ae.completed_at AS DATE) >= CURRENT_DATE - INTERVAL '1 day'
)
SELECT
    SUM(CASE WHEN export_date = CURRENT_DATE AND status = 'failed' THEN 1 ELSE 0 END) AS failed_today,
    SUM(CASE WHEN export_date = CURRENT_DATE - INTERVAL '1 day' AND status = 'failed' THEN 1 ELSE 0 END) AS failed_yesterday
FROM scoped_exports;
-- Metric: {metric}"""
