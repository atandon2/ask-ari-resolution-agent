"""Optional tracing boundary for the local Ask Ari demo.

This module always stores ordered local trace events in memory. If Arize OTEL
is installed and configured, the same workflow also emits OpenTelemetry spans
to Arize.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from typing import Any


_TRACE_LOGS: dict[str, list[dict[str, Any]]] = {}
_ARIZE_TRACER: Any | None = None
_ARIZE_TRACER_PROVIDER: Any | None = None
_ARIZE_WORKFLOW_SPANS: dict[str, Any] = {}


def enable_arize_tracing(
    space_id: str | None = None,
    api_key: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """Enable optional Arize OTEL tracing for subsequent workflows."""

    global _ARIZE_TRACER, _ARIZE_TRACER_PROVIDER

    try:
        from arize.otel import register
    except ImportError:
        return {
            "enabled": False,
            "message": (
                "Arize tracing is optional. Install it with: "
                "pip install -r requirements-arize.txt"
            ),
        }

    resolved_space_id = space_id or os.getenv("ARIZE_SPACE_ID")
    resolved_api_key = api_key or os.getenv("ARIZE_API_KEY")
    resolved_project = (
        project_name
        or os.getenv("ARIZE_PROJECT_NAME")
        or "ask-ari-resolution-agent"
    )

    if not resolved_space_id or not resolved_api_key:
        return {
            "enabled": False,
            "message": (
                "Set ARIZE_SPACE_ID and ARIZE_API_KEY before enabling tracing."
            ),
        }

    _ARIZE_TRACER_PROVIDER = register(
        space_id=resolved_space_id,
        api_key=resolved_api_key,
        project_name=resolved_project,
    )
    _ARIZE_TRACER = _ARIZE_TRACER_PROVIDER.get_tracer(__name__)

    return {
        "enabled": True,
        "project_name": resolved_project,
    }


def _safe_attributes(payload: dict[str, Any]) -> dict[str, str]:
    """Serialize arbitrary demo payloads into OTEL-safe string attributes."""

    return {
        f"ask_ari.payload.{key}": json.dumps(value, default=str)
        for key, value in payload.items()
    }


def _start_arize_span(trace_id: str, request: str, persona: str) -> None:
    if not _ARIZE_TRACER:
        return

    _ARIZE_WORKFLOW_SPANS[trace_id] = _ARIZE_TRACER.start_span(
        "ask_ari.workflow",
        attributes={
            "ask_ari.trace_id": trace_id,
            "ask_ari.persona": persona,
            "ask_ari.request": request,
        },
    )


def _trace_arize_event(
    trace_id: str,
    step_name: str,
    payload: dict[str, Any],
) -> None:
    span = _ARIZE_WORKFLOW_SPANS.get(trace_id)
    if not span:
        return

    span.add_event(step_name, attributes=_safe_attributes(payload))


def _end_arize_span(trace_id: str, result: dict[str, Any]) -> None:
    span = _ARIZE_WORKFLOW_SPANS.pop(trace_id, None)
    if not span:
        return

    for key, value in result.items():
        span.set_attribute(
            f"ask_ari.result.{key}",
            json.dumps(value, default=str),
        )
    span.end()


def flush_arize_tracing(shutdown: bool = True) -> None:
    """Flush the optional tracer provider, and optionally shut it down."""

    if not _ARIZE_TRACER_PROVIDER:
        return
    if hasattr(_ARIZE_TRACER_PROVIDER, "force_flush"):
        _ARIZE_TRACER_PROVIDER.force_flush()
    if shutdown and hasattr(_ARIZE_TRACER_PROVIDER, "shutdown"):
        _ARIZE_TRACER_PROVIDER.shutdown()


def start_workflow(trace_id: str, request: str, persona: str) -> dict[str, Any]:
    """Start a fresh local workflow trace."""

    _TRACE_LOGS[trace_id] = []
    _start_arize_span(trace_id, request, persona)

    return trace_step(
        trace_id,
        "workflow.started",
        {"request": request, "persona": persona},
    )


def trace_step(
    trace_id: str,
    step_name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Append one ordered event to a workflow trace."""

    events = _TRACE_LOGS.setdefault(trace_id, [])
    event = {
        "sequence": len(events) + 1,
        "step": step_name,
        "payload": deepcopy(payload),
    }
    events.append(event)

    _trace_arize_event(trace_id, step_name, payload)

    print(f"[trace:{trace_id}] {step_name}: {payload}")
    return deepcopy(event)


def end_workflow(trace_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    """Finish a workflow and return its complete local trace."""

    trace_step(trace_id, "workflow.completed", result)
    _end_arize_span(trace_id, result)

    return get_trace_log(trace_id)


def get_trace_log(trace_id: str) -> list[dict[str, Any]]:
    """Return a defensive copy so callers cannot mutate stored trace events."""

    return deepcopy(_TRACE_LOGS.get(trace_id, []))
