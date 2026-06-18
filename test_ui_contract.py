from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_response_first_internal_layout_contract():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    helper_source = (ROOT / "ui_helpers.py").read_text(encoding="utf-8")

    for label in (
        "Adobe Enterprise · Ask Ari · Internal Productivity Agent",
        "Adobe’s internal productivity platform for resolving customer issues across multiple teams",
        "Teams can plug in specialized agents for executive prep, campaigns, audience activation, support, and governed data access as they onboard.",
        "governed by Adobe IT",
        "Outcome Summary",
        "Audit-ready decision record",
        "Raw trace log",
        "Audit",
        "Generated SQL for aggregate, Disney-scoped analysis.",
    ):
        assert label in source
    assert "What the user asked / input" in helper_source
    assert "What the agent inferred / output" in helper_source
    assert "st.set_page_config" in source
    assert 'layout="wide"' in source
    assert ".block-container { max-width: 1180px; padding-top: 3.25rem;" in source
    assert ".cloud-top-spacer { height: .35rem; }" in source
    assert '<div class="cloud-top-spacer"></div>' in source
    assert "st.sidebar" not in source
    assert "Load scenario" not in source
    assert "Enterprise workflow sandbox · V0" not in source
    assert "internal-title" not in source
    assert "::selection" in source
    assert "Arize" not in source
    assert "Phoenix" not in source
    assert "workbench_left, workbench_gutter, workbench_right = st.columns([0.5, 0.04, 0.46], gap=\"small\")" in source
    assert "employee_picker, employee_gutter, employee_card = st.columns(" in source
    assert '[0.5, 0.04, 0.46], gap="small", vertical_alignment="center"' in source
    assert "response-panel-shell" in source
    assert "response-panel-empty" not in source
    assert "output-panel-surface" in source
    assert ".section-kicker.response-panel-kicker" in source
    assert ".section-kicker.response-panel-kicker { color: var(--adobe-red);" in source
    assert "agent-output-kicker" in source
    assert "agent-answer-body" in source
    assert "st.container(border=True)" not in source
    assert '[data-testid="stTabs"] [data-testid="stMarkdownContainer"] p' in source
    assert "font-size: .86rem !important;" in source
    assert "border: 1px solid #ececea;" in source
    assert "box-shadow: none;" in source
    assert '[data-testid="stTextArea"] textarea:focus' in source
    assert "What do you need resolved?" not in source
    assert "Agent output" not in source
    assert "Ari unblocks the work" in source
    assert "Ari returns the work product first" not in source
    assert "Ask Ari to help with the employee request" not in source
    assert "Audit tracks the decision record after a run" in source
    assert "Ari · Internal Operations Assistant" not in source
    assert "request-panel-shell" in source
    assert "prompt-composer-shell" in source
    assert "prompt-composer-footer" in source
    assert "Scope-aware prompt" in source
    assert "background: #fbfbf9;" in source
    assert "Describe the customer work to unblock" not in source
    assert "What should Ari help unblock?" in source
    assert "Ask about executive prep, campaign delays, audience activation, support signals, or governed data access." in source
    assert "Ari checks what it can act on, gathers evidence, routes approvals, and pings the right teams across the matrix org." in source
    assert "output_tab, audit_tab = st.tabs([\"Output\", \"Audit\"])" in source
    assert "dev-tool" not in source
    assert "dev-summary" not in source
    assert "audit-tool-heading" in source
    assert "audit-summary-grid" in source
    assert "eval-result-grid" in source
    assert "st.table(build_decision_rows(result, persona))" in source
    assert "load_adobe_mark(Path(__file__).parent / \"assets\" / \"adobe-mark.svg\")" in source
    assert "adobe-mark.svg\").read_text" not in source
    assert "matrix org" in source
    assert "pings the right teams" in source
    assert "Ari can act for" in source
    assert "Access Check" in source
    assert "Customer Scope" not in source
    assert "Customer scope:" not in source
    assert "campaign delays, audience activation" in source
    assert source.index("What should Ari help unblock?") < source.index("Ari unblocks the work")
    assert source.index("Ari unblocks the work") < source.index("Decision Trace")
    assert (ROOT / "assets" / "adobe-mark.svg").exists()


def test_persona_control_is_above_request_and_drives_fixed_scenario():
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert source.index('"Logged-in employee"') < source.index("What should Ari help unblock?")
    assert '"Persona",' not in source
    assert '"Demo scenario"' not in source
    assert "Run the selected scenario" not in source
    assert "scenario_col" not in source
    assert "format_func=_persona_label" in source
    assert "Signed in as" in source
    assert "Adobe SSO" in source
    assert "Ari can act for" in source
    assert "employee-avatar" in source
    assert 'st.container(key="session_context_band", border=False)' in source
    assert "employee-row-label" in source
    assert ".employee-row-label::after" in source
    assert "Session context" in source
    internal_header_rule = source.split(".internal-header {", 1)[1].split("}", 1)[0]
    session_band_rule = source.split(".st-key-session_context_band {", 1)[1].split("}", 1)[0]
    employee_label_rule = source.split(".employee-row-label {", 1)[1].split("}", 1)[0]
    assert "margin-bottom: .68rem;" in internal_header_rule
    assert "border-top: 0;" in session_band_rule
    assert "border-bottom: 1px solid #e3e3df;" in session_band_rule
    assert "background: rgba(255,255,255,.36);" in session_band_rule
    assert "margin: .32rem 0 .72rem;" in session_band_rule
    assert "padding: .28rem 0 .88rem;" in session_band_rule
    assert "margin: .08rem 0 .42rem;" in employee_label_rule
    request_panel_rule = source.split(".request-panel-shell {", 1)[1].split("}", 1)[0]
    response_panel_rule = source.split(".response-panel-shell {", 1)[1].split("}", 1)[0]
    assert "margin: .62rem 0 .75rem;" in request_panel_rule
    assert "margin: .62rem 0 .75rem;" in response_panel_rule
    assert "employee-picker-card" in source
    assert "employee-session-card" in source
    session_rule = source.split(".employee-session-card {", 1)[1].split("}", 1)[0]
    assert "background: #f2f2ef;" in session_rule
    assert "border: 1px solid #ececea;" in session_rule
    assert "border-radius: 12px;" in session_rule
    assert "height: auto;" in session_rule
    assert "align-items: center;" in session_rule
    assert (
        '.st-key-session_context_band [data-testid="stMarkdownContainer"]:has(.employee-session-card)'
        in source
    )
    assert "margin-bottom: 0 !important;" in source
    assert '<div class="selection-label">Scenario</div>' not in source
    assert "scenario-panel" not in source
    assert "pre-filled for this employee" not in source
    assert "employee-prefill" not in source
    assert "PERSONA_SCENARIOS" in source
    assert "PERSONA_ORDER" in source
    assert '"Jason Lee",' in source
    assert source.index('"Jason Lee",') < source.index('"Maya Patel",')
    assert source.index('"Maya Patel",') < source.index('"Emily Chen",')
    assert "PERSONA_ORDER," in source
    assert "list(PERSONAS)" not in source
    assert "st.session_state.persona_selection = PERSONA_ORDER[0]" in source
    assert (
        "st.session_state.scenario_selection = PERSONA_SCENARIOS[\n"
        "        st.session_state.persona_selection\n"
        "    ]"
    ) in source
    assert '"Jason Lee": "E"' in source
    assert '"Emily Chen": "A"' in source
    assert '"Olivia Martinez": "B"' in source
    assert "on_change=_load_persona_scenario" in source
    assert "st.table" in source


def test_primary_cta_is_centered_and_employee_facing():
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "What should Ari help unblock?" in source
    assert "What work should Ari help move forward?" not in source
    assert "Ask Ari" in source
    assert "Ask Ari to resolve the employee request" not in source
    assert "Ask Resolution Agent to do the work" not in source
    assert "Run resolution workflow" not in source
    assert "request-panel-shell" in source
    assert "request-copy" in source
    assert "button_left, button_center, button_right = st.columns([1, 1.2, 1])" in source


def test_request_textarea_overrides_host_theme_text_colors():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    textarea_rule = source.split(
        '[data-testid="stTextArea"] textarea {', 1
    )[1].split("}", 1)[0]
    base_input_rule = source.split(
        '[data-testid="stTextArea"] div[data-baseweb="base-input"] {', 1
    )[1].split("}", 1)[0]

    assert "color: var(--ink) !important;" in textarea_rule
    assert "caret-color: var(--ink);" in textarea_rule
    assert "background: transparent !important;" in base_input_rule
    assert "color: var(--ink) !important;" in base_input_rule
    assert '[data-testid="stTextArea"] textarea::placeholder' in source


def test_selectbox_text_overrides_host_theme_text_colors():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    selectbox_rule = source.split(
        '[data-baseweb="select"], [data-baseweb="select"] * {', 1
    )[1].split("}", 1)[0]

    assert "color: var(--ink) !important;" in selectbox_rule
    assert "-webkit-text-fill-color: var(--ink) !important;" in selectbox_rule
    assert '[data-testid="stSelectbox"] label' in source
    assert '[data-baseweb="popover"]' in source
    assert '[data-baseweb="select"] input' in source
    assert '[role="option"][aria-selected="true"]' in source


def test_readme_explains_model_relevance_and_arize_handoff():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Model Relevance" in readme
    for capability in (
        "intent detection",
        "customer extraction",
        "inferred data source selection",
        "policy interpretation",
        "clarification behavior",
        "response synthesis",
    ):
        assert capability in readme
    assert "your step 2" in readme


def test_readme_separates_local_capabilities_from_future_phoenix_work():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## What works today locally" in readme
    assert "## Local Run" in readme
    assert "## Run validation checks" in readme
    assert "## Deploying to Streamlit Community Cloud" in readme
    assert "## How to plug this into Arize/Phoenix" in readme
    assert "Phoenix/Arize integration is not active yet" in readme
    assert "python run_validation_checks.py" in readme
    assert "LLM-as-judge" in readme


def test_requirements_stay_small():
    dependencies = {
        line.split(">=")[0]
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    assert dependencies == {"streamlit", "pytest"}
