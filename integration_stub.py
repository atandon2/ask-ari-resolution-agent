"""Future Step 2 boundaries for optional Arize/Phoenix integration.

Phoenix/Arize integration is not active yet. This module intentionally imports
no Phoenix, Arize, OpenTelemetry, or OpenInference package. The local app,
agent, tests, and validation runner work without those optional dependencies.
"""


PHOENIX_INTEGRATION_ACTIVE = False


def integration_status() -> str:
    """Describe the honest current integration state."""

    return (
        "Phoenix/Arize integration is not active yet. This repo prepares the "
        "tracing and eval contracts so Step 2 can plug into Phoenix."
    )


def create_or_load_dataset(csv_path: object) -> None:
    """Future: create or load a Phoenix dataset from validation_cases.csv."""

    # Future Step 2: import the Phoenix client here and upload labeled examples.
    raise NotImplementedError(
        "Step 2: install and configure Phoenix, then create or load the dataset."
    )


def run_agent_experiment(dataset: object) -> None:
    """Future: run the local agent against Phoenix dataset examples."""

    # Future Step 2: start a Phoenix experiment that calls agent.run_agent.
    raise NotImplementedError(
        "Step 2: run the agent over the configured Phoenix dataset."
    )


def attach_evaluators(experiment: object) -> None:
    """Future: attach deterministic code and subjective response evaluators."""

    # Future Step 2: register intent, tables, approval, and scope code evaluators.
    # LLM-as-judge evaluators can later assess groundedness and actionability.
    raise NotImplementedError(
        "Step 2: attach Phoenix evaluators to the configured experiment."
    )


def log_validation_results(results: object) -> None:
    """Future: write experiment and validation results back to Phoenix."""

    # Future Step 2: send result labels, scores, explanations, and trace IDs.
    raise NotImplementedError(
        "Step 2: log experiment and eval results to the configured Phoenix project."
    )
