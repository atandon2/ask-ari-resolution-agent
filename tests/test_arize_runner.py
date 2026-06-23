import run_phoenix_experiment as runner


def test_runner_loads_twenty_validation_cases_for_mock_trace_generation():
    cases = runner.load_mock_trace_cases()

    assert len(cases) == 20
    assert {case["persona"] for case in cases} == {
        "Alex Rivera",
        "Emily Chen",
        "Jason Lee",
        "Maya Patel",
        "Olivia Martinez",
        "Sarah Kim",
    }


def test_runner_main_enables_tracing_and_runs_validation_cases(monkeypatch, capsys):
    calls = []
    cases = [
        {"id": "A", "persona": "Emily Chen", "request": "Brief Disney"},
        {"id": "B", "persona": "Olivia Martinez", "request": "Investigate Disney"},
    ]

    def fake_enable_arize_tracing():
        calls.append(("enable_arize_tracing",))
        return {"enabled": True, "project_name": "ask-ari-resolution-agent"}

    def fake_run_agent(persona, request):
        calls.append(("run_agent", persona, request))
        return {
            "trace_id": "wf_test123",
            "intent": "numeric_analysis",
            "approval": "not_required",
            "customer_scope": "authorized",
        }

    monkeypatch.setattr(runner, "enable_arize_tracing", fake_enable_arize_tracing)
    monkeypatch.setattr(runner, "load_mock_trace_cases", lambda: cases)
    monkeypatch.setattr(runner, "run_agent", fake_run_agent)

    runner.main()

    assert calls == [("enable_arize_tracing",)] + [
        ("run_agent", case["persona"], case["request"])
        for case in cases
    ]
    output = capsys.readouterr().out
    assert "Generating 2 Ask Ari mock traces" in output
    assert "ask-ari-resolution-agent" in output
    assert "wf_test123" in output
