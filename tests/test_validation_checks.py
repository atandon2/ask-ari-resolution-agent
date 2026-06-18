import ast
import csv
import importlib
from pathlib import Path

import pytest

from run_validation_checks import run_validation_checks


ROOT = Path(__file__).parents[1]


def test_validation_runner_writes_twenty_passing_rows(tmp_path, capsys):
    output_path = tmp_path / "validation_results.csv"

    summary = run_validation_checks(ROOT / "validation_cases.csv", output_path)
    with output_path.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))

    assert summary == {"total": 20, "passed": 20, "failed": 0}
    assert len(rows) == 20
    assert all(row["overall_pass"] == "True" for row in rows)
    assert all(row["intent_match"] == "True" for row in rows)
    assert all(row["tables_match"] == "True" for row in rows)
    assert all(row["approval_match"] == "True" for row in rows)
    assert all(row["customer_scope_match"] == "True" for row in rows)
    assert all(row["trace_id"].startswith("wf_") for row in rows)
    output = capsys.readouterr().out
    assert "Validation checks: 20/20 passed" in output
    assert str(output_path) in output


def test_phoenix_stub_is_import_safe_and_explicitly_inactive():
    module = importlib.import_module("integration_stub")

    assert module.PHOENIX_INTEGRATION_ACTIVE is False
    assert "not active" in module.integration_status().lower()
    assert "step 2" in module.integration_status().lower()


@pytest.mark.parametrize(
    "function_name",
    [
        "create_or_load_dataset",
        "run_agent_experiment",
        "attach_evaluators",
        "log_validation_results",
    ],
)
def test_phoenix_stub_boundaries_do_not_pretend_to_be_implemented(function_name):
    module = importlib.import_module("integration_stub")

    with pytest.raises(NotImplementedError, match="Step 2"):
        getattr(module, function_name)(None)


def test_phoenix_stub_has_no_optional_package_imports():
    source = (ROOT / "integration_stub.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert imported_modules.isdisjoint(
        {"phoenix", "arize", "opentelemetry", "openinference"}
    )
