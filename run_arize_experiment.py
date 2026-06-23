"""Run Ask Ari as an Arize dataset experiment.

This is the Step 2 bridge from the local Ask Ari workflow into Arize
Datasets + Experiments. It intentionally stays separate from the Streamlit app:

- app.py remains the employee-facing product experience.
- tracing.py exports live workflow traces.
- this file runs the validation dataset as an offline experiment with
  deterministic code evaluators.

The file is import-safe without Arize installed so local tests and the app do
not require optional Arize dependencies.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from agent import run_agent


DEFAULT_DATASET_NAME = "ask-ari-validation-cases"
DEFAULT_EXPERIMENT_NAME = "ask-ari-v0-deterministic-router"


@dataclass(frozen=True)
class ScoreResult:
    """Small local score object used by tests and wrapped for Arize at runtime."""

    score: int
    label: str
    explanation: str


def ask_ari_task(dataset_row: dict[str, Any]) -> dict[str, Any]:
    """Run one validation example through the Ask Ari agent."""

    return run_agent(
        persona=dataset_row["persona"],
        request=dataset_row["request"],
    )


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _split_tables(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return {item.strip() for item in _normalize(value).split("|") if item.strip()}


def _score_match(name: str, actual: Any, expected: Any) -> ScoreResult:
    actual_value = _normalize(actual)
    expected_value = _normalize(expected)
    matched = actual_value == expected_value
    return ScoreResult(
        score=int(matched),
        label="pass" if matched else "fail",
        explanation=(
            f"{name} matched: {actual_value}"
            if matched
            else f"{name} mismatch: expected {expected_value}, got {actual_value}"
        ),
    )


def score_intent(output: dict[str, Any], dataset_row: dict[str, Any]) -> ScoreResult:
    return _score_match(
        "intent",
        output.get("intent"),
        dataset_row.get("expected_intent"),
    )


def score_approval(output: dict[str, Any], dataset_row: dict[str, Any]) -> ScoreResult:
    return _score_match(
        "approval",
        output.get("approval"),
        dataset_row.get("expected_approval"),
    )


def score_customer_scope(output: dict[str, Any], dataset_row: dict[str, Any]) -> ScoreResult:
    return _score_match(
        "customer scope",
        output.get("customer_scope"),
        dataset_row.get("expected_customer_scope"),
    )


def score_tables(output: dict[str, Any], dataset_row: dict[str, Any]) -> ScoreResult:
    actual_tables = _split_tables(output.get("selected_tables", []))
    expected_tables = _split_tables(dataset_row.get("expected_tables", ""))
    matched = actual_tables == expected_tables
    return ScoreResult(
        score=int(matched),
        label="pass" if matched else "fail",
        explanation=(
            f"tables matched: {sorted(actual_tables)}"
            if matched
            else (
                "tables mismatch: "
                f"expected {sorted(expected_tables)}, got {sorted(actual_tables)}"
            )
        ),
    )


def load_arize_sdk():
    """Load optional Arize experiment SDK only when this runner is executed."""

    from arize import ArizeClient
    from arize.experiments import EvaluationResult

    return ArizeClient, EvaluationResult


def configure_ssl_cert_bundle() -> None:
    """Use certifi's CA bundle when local Python has no trusted cert path.

    This avoids common macOS virtualenv failures like:
    SSL: CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate.

    Existing user-provided cert settings are respected.
    """

    try:
        import certifi
    except ImportError:
        return

    cert_path = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cert_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)


def _as_arize_evaluator(
    name: str,
    score_fn: Callable[[dict[str, Any], dict[str, Any]], ScoreResult],
    EvaluationResult,
):
    """Wrap a local score function in Arize's EvaluationResult contract."""

    def evaluator(output: dict[str, Any], dataset_row: dict[str, Any]):
        score = score_fn(output, dataset_row)
        return EvaluationResult(
            score=score.score,
            label=score.label,
            explanation=score.explanation,
        )

    evaluator.__name__ = name
    return evaluator


def build_evaluators(EvaluationResult):
    """Create deterministic code evaluators for the Ask Ari validation dataset."""

    return [
        _as_arize_evaluator("intent_match", score_intent, EvaluationResult),
        _as_arize_evaluator("tables_match", score_tables, EvaluationResult),
        _as_arize_evaluator("approval_match", score_approval, EvaluationResult),
        _as_arize_evaluator("customer_scope_match", score_customer_scope, EvaluationResult),
    ]


def main():
    """Run the Ask Ari dataset experiment in Arize."""

    configure_ssl_cert_bundle()

    try:
        ArizeClient, EvaluationResult = load_arize_sdk()
    except ImportError as exc:
        raise SystemExit(
            "The full Arize Python SDK is required to run experiments.\n"
            "Install optional dependencies with:\n\n"
            "  pip install -r requirements-arize.txt\n\n"
            f"Original import error: {exc}"
        ) from None

    api_key = os.getenv("ARIZE_API_KEY")
    space_id = os.getenv("ARIZE_SPACE_ID")
    dataset_name = os.getenv("ARIZE_DATASET_NAME", DEFAULT_DATASET_NAME)
    experiment_name = os.getenv("ARIZE_EXPERIMENT_NAME", DEFAULT_EXPERIMENT_NAME)
    dry_run = os.getenv("ARIZE_DRY_RUN", "false").lower() == "true"

    if not api_key:
        raise SystemExit("Set ARIZE_API_KEY before running this experiment.")
    if not space_id:
        raise SystemExit("Set ARIZE_SPACE_ID before running this experiment.")

    client = ArizeClient(api_key=api_key)
    experiment, experiment_df = client.experiments.run(
        name=experiment_name,
        dataset=dataset_name,
        space=space_id,
        task=ask_ari_task,
        evaluators=build_evaluators(EvaluationResult),
        concurrency=3,
        dry_run=dry_run,
        metadata={
            "app": "ask-ari",
            "workflow": "cross-functional-resolution-agent",
            "classifier_mode": "deterministic",
        },
    )

    print(
        "Completed Ask Ari experiment:",
        {
            "experiment": getattr(experiment, "name", None) if experiment else None,
            "dataset": dataset_name,
            "rows": len(experiment_df),
            "dry_run": dry_run,
        },
    )
    return experiment, experiment_df


if __name__ == "__main__":
    main()
