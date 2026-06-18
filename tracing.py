"""Optional-dependency-free tracing for the local agent demo.

This module is the single tracing boundary. Today it stores ordered events in
memory; Step 2 can export the same lifecycle to Phoenix/OpenTelemetry without
changing the agent or fake-tool interfaces.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_TRACE_LOGS: dict[str, list[dict[str, Any]]] = {}


def start_workflow(trace_id: str, request: str, persona: str) -> dict[str, Any]:
    """Start a fresh local workflow trace."""

    _TRACE_LOGS[trace_id] = []
    # TODO: Start an OpenInference/OpenTelemetry span and attach it to Phoenix.
    return trace_step(
        trace_id,
        "workflow.started",
        {"request": request, "persona": persona},
    )


def trace_step(
    trace_id: str, step_name: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Append one ordered event to a workflow trace."""

    events = _TRACE_LOGS.setdefault(trace_id, [])
    event = {
        "sequence": len(events) + 1,
        "step": step_name,
        "payload": deepcopy(payload),
    }
    events.append(event)
    # TODO: Emit a Phoenix/OpenTelemetry event on the active workflow span.
    print(f"[trace:{trace_id}] {step_name}: {payload}")
    return deepcopy(event)


def end_workflow(trace_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    """Finish a workflow and return its complete local trace."""

    trace_step(trace_id, "workflow.completed", result)
    # TODO: End and export the OpenInference/OpenTelemetry span to Phoenix.
    return get_trace_log(trace_id)


def get_trace_log(trace_id: str) -> list[dict[str, Any]]:
    """Return a defensive copy so callers cannot mutate stored trace events."""

    return deepcopy(_TRACE_LOGS.get(trace_id, []))
