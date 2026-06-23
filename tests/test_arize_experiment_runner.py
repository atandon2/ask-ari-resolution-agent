import importlib
import os


def test_ask_ari_task_runs_agent_from_dataset_row(monkeypatch):
    runner = importlib.import_module("run_arize_experiment")
    calls = []

    def fake_run_agent(persona, request):
        calls.append((persona, request))
        return {
            "intent": "customer_escalation",
            "selected_tables": ["customer_accounts"],
            "approval": "not_required",
            "customer_scope": "authorized",
        }

    monkeypatch.setattr(runner, "run_agent", fake_run_agent)

    output = runner.ask_ari_task(
        {
            "persona": "Emily Chen",
            "request": "Prepare Disney executive review",
        }
    )

    assert calls == [("Emily Chen", "Prepare Disney executive review")]
    assert output["intent"] == "customer_escalation"


def test_score_helpers_compare_expected_fields():
    runner = importlib.import_module("run_arize_experiment")
    output = {
        "intent": "numeric_analysis",
        "selected_tables": ["audience_exports", "customer_accounts"],
        "approval": "not_required",
        "customer_scope": "authorized",
    }
    row = {
        "expected_intent": "numeric_analysis",
        "expected_tables": "customer_accounts|audience_exports",
        "expected_approval": "not_required",
        "expected_customer_scope": "authorized",
    }

    assert runner.score_intent(output, row).score == 1
    assert runner.score_tables(output, row).score == 1
    assert runner.score_approval(output, row).score == 1
    assert runner.score_customer_scope(output, row).score == 1


def test_score_helpers_explain_mismatches():
    runner = importlib.import_module("run_arize_experiment")
    output = {
        "intent": "customer_escalation",
        "selected_tables": ["support_tickets"],
        "approval": "not_required",
        "customer_scope": "authorized",
    }
    row = {
        "expected_intent": "clarification",
        "expected_tables": "customer_accounts|support_tickets",
        "expected_approval": "rejected",
        "expected_customer_scope": "clarification_required",
    }

    assert runner.score_intent(output, row).score == 0
    assert "expected clarification" in runner.score_intent(output, row).explanation
    assert runner.score_tables(output, row).score == 0
    assert "customer_accounts" in runner.score_tables(output, row).explanation
    assert runner.score_approval(output, row).score == 0
    assert runner.score_customer_scope(output, row).score == 0


def test_main_exits_with_helpful_message_when_arize_sdk_missing(monkeypatch):
    runner = importlib.import_module("run_arize_experiment")

    monkeypatch.setattr(runner, "load_arize_sdk", lambda: (_ for _ in ()).throw(ImportError("No module named arize.experiments")))

    try:
        runner.main()
    except SystemExit as exc:
        assert "pip install -r requirements-arize.txt" in str(exc)
    else:
        raise AssertionError("main() should exit clearly when the full Arize SDK is missing")


def test_configure_ssl_cert_bundle_uses_certifi_when_env_missing(monkeypatch):
    runner = importlib.import_module("run_arize_experiment")

    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)

    runner.configure_ssl_cert_bundle()

    assert os.environ["SSL_CERT_FILE"].endswith("cacert.pem")
    assert os.environ["REQUESTS_CA_BUNDLE"].endswith("cacert.pem")


def test_configure_ssl_cert_bundle_does_not_override_existing_env(monkeypatch):
    runner = importlib.import_module("run_arize_experiment")

    monkeypatch.setenv("SSL_CERT_FILE", "/custom/ssl.pem")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/custom/requests.pem")

    runner.configure_ssl_cert_bundle()

    assert os.environ["SSL_CERT_FILE"] == "/custom/ssl.pem"
    assert os.environ["REQUESTS_CA_BUNDLE"] == "/custom/requests.pem"
