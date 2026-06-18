"""Response-first Streamlit UI for the Adobe Enterprise Resolution Agent."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from agent import SCENARIOS, run_agent
from tools import PERSONAS
from ui_helpers import build_decision_rows, load_adobe_mark, split_safer_next_action


PERSONA_SCENARIOS = {
    "Emily Chen": "A",
    "Olivia Martinez": "B",
    "Alex Rivera": "C",
    "Jason Lee": "E",
    "Sarah Kim": "D",
    "Maya Patel": "G",
}

PERSONA_ORDER = [
    "Jason Lee",
    "Maya Patel",
    "Emily Chen",
    "Olivia Martinez",
    "Alex Rivera",
    "Sarah Kim",
]


st.set_page_config(
    page_title="Adobe Enterprise Resolution Agent",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    :root {
        --canvas: #f7f7f5;
        --surface: #ffffff;
        --surface-soft: #f0f0ed;
        --ink: #1d1d1f;
        --muted: #66666b;
        --border: #d9d9d5;
        --adobe-red: #d92920;
        --green: #237a57;
        --amber: #8a5a11;
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    .stApp ::selection { background: rgba(217, 41, 32, .16); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(247, 247, 245, .9); }
    .block-container { max-width: 1180px; padding-top: 3.25rem; padding-bottom: 4rem; }
    h1, h2, h3, p, label { font-family: "Helvetica Neue", Arial, sans-serif; }
    h1 { color: var(--ink); letter-spacing: -.035em; font-size: 2.55rem !important; font-weight: 680 !important; }
    h2 { letter-spacing: -.02em; }
    h3 { color: var(--ink); font-size: 1.08rem !important; letter-spacing: -.01em; }
    .internal-header { display: flex; align-items: flex-start; gap: .75rem; margin-bottom: .68rem; }
    .cloud-top-spacer { height: .35rem; }
    .adobe-mark { width: 32px; height: 28px; flex: 0 0 auto; margin-top: .12rem; }
    .internal-lockup {
        color: var(--ink); font-family: "Helvetica Neue", Arial, sans-serif;
        font-size: 1.32rem; line-height: 1.16; letter-spacing: -.02em; font-weight: 720;
    }
    .internal-description {
        color: #4f4f54; font-size: .92rem; line-height: 1.5;
        max-width: 850px; margin-top: .35rem;
    }
    .employee-row-label {
        align-items: center; display: flex; gap: .65rem;
        color: var(--muted); font-size: .62rem; font-weight: 780;
        letter-spacing: .09em; margin: .08rem 0 .42rem; text-transform: uppercase;
    }
    .employee-row-label::after {
        background: #e3e3df; content: ""; flex: 1; height: 1px;
    }
    .st-key-session_context_band {
        background: rgba(255,255,255,.36);
        border-bottom: 1px solid #e3e3df;
        border-top: 0;
        margin: .32rem 0 .72rem;
        padding: .28rem 0 .88rem;
    }
    .employee-session-card {
        background: #f2f2ef; border: 1px solid #ececea;
        border-radius: 12px; box-sizing: border-box; height: auto;
        display: flex; align-items: center; min-height: 4.75rem;
        padding: .82rem .95rem;
    }
    .st-key-session_context_band [data-testid="stMarkdownContainer"]:has(.employee-session-card) {
        margin-bottom: 0 !important;
    }
    .employee-picker-card {
        background: rgba(255,255,255,.58); border: 1px solid var(--border);
        border-radius: 8px; height: 100%; margin-bottom: .42rem; padding: .78rem .85rem;
    }
    .employee-profile { display: flex; gap: .8rem; align-items: center; min-width: 0; }
    .employee-avatar {
        align-items: center; background: var(--ink); border-radius: 999px; color: #fff;
        display: flex; flex: 0 0 auto; font-size: .78rem; font-weight: 780;
        height: 42px; justify-content: center; letter-spacing: .04em; width: 42px;
    }
    .employee-badge {
        background: #f4e7e6; border: 1px solid #ead0ce; border-radius: 999px;
        color: #8f1f1a; display: inline-block; font-size: .58rem; font-weight: 780;
        letter-spacing: .08em; margin-bottom: .28rem; padding: .12rem .42rem;
        text-transform: uppercase;
    }
    .employee-name { color: var(--ink); font-size: .9rem; font-weight: 760; line-height: 1.2; }
    .employee-meta { color: #55555a; font-size: .76rem; line-height: 1.4; margin-top: .14rem; }
    .employee-scope { color: #6a6a70; font-size: .72rem; line-height: 1.38; margin-top: .12rem; }
    .selection-label {
        color: var(--muted); font-size: .62rem; font-weight: 760;
        letter-spacing: .08em; text-transform: uppercase;
    }
    .selection-value { color: var(--ink); font-size: .86rem; font-weight: 700; margin-top: .15rem; }
    .selection-copy { color: #5d5d62; font-size: .75rem; line-height: 1.42; margin-top: .18rem; }
    .request-panel-shell {
        background: linear-gradient(180deg, #ffffff 0%, #fbfbf9 100%);
        border: 1px solid #ececea; border-radius: 12px;
        box-shadow: none;
        margin: .62rem 0 .75rem;
        padding: 1.05rem 1.08rem;
    }
    .agent-orb {
        align-items: center; background: var(--adobe-red); border-radius: 999px;
        color: #fff; display: flex; flex: 0 0 auto; font-size: .76rem;
        font-weight: 820; height: 42px; justify-content: center; letter-spacing: .02em; width: 42px;
    }
    .request-kicker {
        color: var(--adobe-red); font-size: .64rem; font-weight: 820;
        letter-spacing: .08em; text-transform: uppercase;
    }
    .request-title {
        color: var(--ink); font-size: 1.34rem; font-weight: 760;
        letter-spacing: -.025em; line-height: 1.15; margin-top: .16rem;
    }
    .request-copy {
        color: #58585e; font-size: .82rem; line-height: 1.45;
        margin-top: .36rem; max-width: 720px;
    }
    .prompt-composer-shell {
        background: #fbfbf9; border: 1px solid #d6d6d1; border-radius: 14px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.75);
        padding: .62rem .7rem .58rem; margin-top: .8rem;
    }
    .prompt-composer-footer {
        align-items: center; color: #77777c; display: flex; gap: .45rem;
        font-size: .68rem; letter-spacing: .01em; margin: .48rem .08rem 0;
    }
    .prompt-composer-dot {
        background: var(--adobe-red); border-radius: 999px; display: inline-block;
        height: .42rem; opacity: .78; width: .42rem;
    }
    .response-panel-shell {
        background: #f2f2ef;
        border: 1px solid #ececea; border-radius: 12px;
        box-shadow: none;
        margin: .62rem 0 .75rem; padding: 1.05rem 1.08rem;
    }
    .section-kicker.response-panel-kicker { color: var(--adobe-red); margin: 0 0 .28rem; }
    .response-panel-title {
        color: var(--ink); font-size: 1.18rem; font-weight: 760;
        letter-spacing: -.02em; line-height: 1.18;
    }
    .response-panel-copy {
        color: #58585e; font-size: .8rem; line-height: 1.43;
        margin-top: .34rem;
    }
    .cta-spacer { margin: .2rem 0 1.35rem; }
    .st-key-ari_cta button {
        min-height: 2.7rem;
        box-shadow: 0 1px 0 rgba(0,0,0,.05);
    }
    .section-kicker {
        color: var(--muted); font-size: .68rem; font-weight: 760;
        letter-spacing: .09em; text-transform: uppercase; margin: 1.45rem 0 .4rem;
    }
    .agent-output-kicker {
        color: var(--adobe-red);
        margin: .95rem 0 0;
    }
    .output-panel-surface {
        background: #f2f2ef;
        border-radius: 12px;
    }
    .agent-answer-body {
        color: #232326;
        font-size: .88rem;
        line-height: 1.46;
    }
    .agent-answer-body h1,
    .agent-answer-body h2,
    .agent-answer-body h3 {
        font-size: 1.02rem !important;
        line-height: 1.22;
        margin: .15rem 0 .7rem;
    }
    .agent-answer-body p,
    .agent-answer-body li {
        font-size: .88rem;
        line-height: 1.46;
    }
    .agent-answer-body ul {
        margin-top: .35rem;
        padding-left: 1.15rem;
    }
    .audit-tool-heading {
        align-items: center; color: var(--ink); display: flex; gap: .35rem;
        font-size: .82rem; font-weight: 780; letter-spacing: -.01em;
        margin: .85rem 0 .45rem;
    }
    .audit-tool-note {
        color: var(--muted); font-size: .74rem; line-height: 1.42;
        margin: -.1rem 0 .65rem;
    }
    .audit-summary-grid,
    .eval-result-grid {
        display: grid; gap: .5rem; grid-template-columns: repeat(2, minmax(0, 1fr));
        margin: .15rem 0 .9rem;
    }
    .audit-summary-card,
    .eval-result-card {
        background: #f4f4f1; border: 1px solid var(--border); border-radius: 7px;
        padding: .64rem .7rem; min-width: 0;
    }
    .audit-summary-label,
    .eval-result-label {
        color: var(--muted); font-size: .58rem; font-weight: 780;
        letter-spacing: .08em; text-transform: uppercase;
    }
    .audit-summary-value,
    .eval-result-value {
        color: var(--ink); font-size: .82rem; font-weight: 690;
        line-height: 1.25; margin-top: .16rem; overflow-wrap: anywhere;
    }
    .eval-result-value.pass { color: var(--green); }
    .eval-result-value.fail { color: var(--adobe-red); }
    .outcome-strip {
        display: grid; grid-template-columns: repeat(4, 1fr);
        background: var(--surface-soft); border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border); margin: .25rem 0 1rem;
    }
    .outcome-item { padding: .72rem .85rem; min-width: 0; }
    .outcome-item + .outcome-item { border-left: 1px solid var(--border); }
    .outcome-label {
        color: var(--muted); font-size: .62rem; font-weight: 760;
        letter-spacing: .08em; text-transform: uppercase;
    }
    .outcome-value {
        color: var(--ink); font-size: .82rem; font-weight: 690;
        margin-top: .16rem; overflow-wrap: anywhere;
    }
    .approval-callout {
        background: #fff7e8; border: 1px solid #ead4aa; border-left: 4px solid #c8841b;
        border-radius: 7px; color: #4b3a1e; margin: .8rem 0; padding: .8rem .9rem;
    }
    .approval-title { color: #714a11; font-size: .72rem; font-weight: 780; letter-spacing: .06em; text-transform: uppercase; }
    .approval-grid { display: grid; grid-template-columns: 1.25fr 1.5fr .7fr .7fr; gap: .75rem; margin-top: .55rem; }
    .approval-key { color: #80653d; font-size: .62rem; text-transform: uppercase; letter-spacing: .05em; }
    .approval-value { color: #332818; font-size: .76rem; font-weight: 670; margin-top: .1rem; }
    .safer-action {
        background: #edf6f1; border: 1px solid #c8e1d3; border-left: 4px solid var(--green);
        border-radius: 7px; color: #244b39; margin: .8rem 0; padding: .78rem .9rem;
    }
    .safer-title { color: var(--green); font-size: .7rem; font-weight: 780; letter-spacing: .055em; text-transform: uppercase; }
    .safer-copy { font-size: .8rem; line-height: 1.45; margin-top: .25rem; }
    .trace-id {
        display: inline-block; background: var(--surface-soft); border: 1px solid var(--border);
        border-radius: 4px; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: .7rem; padding: .2rem .4rem; margin-bottom: .65rem;
    }
    .audit-note {
        color: var(--muted); font-size: .76rem; line-height: 1.45;
        border-left: 3px solid #8a8a8e; margin: .8rem 0 1rem; padding-left: .65rem;
    }
    div.stButton > button[kind="primary"] {
        background: var(--adobe-red); border-color: var(--adobe-red);
        border-radius: 6px; font-weight: 700;
    }
    div.stButton > button { border-radius: 6px; }
    [data-testid="stTextArea"] {
        margin-top: .72rem;
    }
    [data-testid="stTextArea"] div[data-baseweb="textarea"] {
        background: #fcfcfa !important;
        border: 1px solid #d8d8d2 !important;
        border-radius: 14px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
        transition: border-color .15s ease, box-shadow .15s ease, background .15s ease;
    }
    [data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
        background: #ffffff !important;
        border-color: #c5c5be !important;
        box-shadow: 0 0 0 3px rgba(29,29,31,.035), inset 0 1px 0 rgba(255,255,255,.9) !important;
    }
    [data-testid="stTextArea"] div[data-baseweb="base-input"] {
        background: transparent !important;
        border-radius: 14px !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stTextArea"] textarea {
        background: transparent !important; border-radius: 14px;
        border: 0 !important; box-shadow: none !important; outline: none !important;
        color: var(--ink) !important; caret-color: var(--ink);
        font-size: .86rem !important;
        line-height: 1.45 !important;
        padding: .92rem 1rem !important;
        -webkit-text-fill-color: var(--ink);
        resize: none;
    }
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextArea"] textarea:focus-visible {
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stTextArea"] textarea::placeholder {
        color: #737378 !important; -webkit-text-fill-color: #737378; opacity: 1;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-weight: 650;
    }
    [data-baseweb="select"] > div {
        background: var(--surface) !important;
        border-color: #b9b9b3 !important;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,.03);
    }
    [data-baseweb="select"], [data-baseweb="select"] * {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-baseweb="select"] input {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        caret-color: var(--ink) !important;
    }
    [data-baseweb="select"] svg { fill: var(--ink) !important; }
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] ul,
    [role="listbox"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 12px 30px rgba(0,0,0,.12) !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [role="option"], [role="option"] * {
        background: var(--surface) !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [role="option"]:hover,
    [role="option"]:hover * {
        background: #f8eeee !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [role="option"][aria-selected="true"],
    [role="option"][aria-selected="true"] * {
        background: #f4e7e6 !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stCodeBlock"] { border: 1px solid var(--border); border-radius: 7px; }
    [data-testid="stTabs"] [role="tab"],
    [data-testid="stTabs"] [role="tab"] p {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
        color: var(--adobe-red) !important;
        -webkit-text-fill-color: var(--adobe-red) !important;
    }
    [data-testid="stTabs"] {
        background: #f2f2ef;
        border-radius: 12px;
        padding: .55rem .65rem .78rem;
    }
    [data-testid="stTabs"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stTabs"] [data-testid="stMarkdownContainer"] li {
        font-size: .86rem !important;
        line-height: 1.45 !important;
    }
    [data-testid="stTabs"] [data-testid="stMarkdownContainer"] h3 {
        font-size: .98rem !important;
        line-height: 1.24 !important;
        margin-bottom: .55rem !important;
    }
    [data-testid="stTable"] { border: 1px solid var(--border); border-radius: 7px; overflow: hidden; }
    [data-testid="stTable"] table { table-layout: fixed; width: 100%; }
    [data-testid="stTable"] th {
        background: #e9e9e5 !important; color: var(--ink) !important;
        font-size: .7rem; line-height: 1.3; white-space: normal !important;
    }
    [data-testid="stTable"] td {
        background: var(--surface) !important; color: #343438 !important;
        font-size: .73rem; line-height: 1.42; white-space: pre-wrap !important;
        vertical-align: top;
    }
    [data-testid="stExpander"] details { border-color: var(--border); background: rgba(255,255,255,.42); }
    @media (max-width: 760px) {
        .block-container { padding-top: 2.3rem; }
        .internal-lockup { font-size: 1.12rem; }
        .request-panel-shell { display: block; }
        .agent-orb { margin-bottom: .65rem; }
        .outcome-strip { grid-template-columns: repeat(2, 1fr); }
        .outcome-item:nth-child(3) { border-left: 0; border-top: 1px solid var(--border); }
        .outcome-item:nth-child(4) { border-top: 1px solid var(--border); }
        .approval-grid { grid-template-columns: 1fr 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _persona_label(persona_name: str) -> str:
    persona = PERSONAS[persona_name]
    return f'{persona["name"]} · {persona["title"]}'


def _initials(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


def _load_persona_scenario() -> None:
    scenario_id = PERSONA_SCENARIOS[st.session_state.persona_selection]
    st.session_state.scenario_selection = scenario_id
    scenario = SCENARIOS[scenario_id]
    st.session_state.request_text = scenario["request"]
    st.session_state.last_result = None


def _pretty(value: str) -> str:
    return value.replace("_", " ").title()


def _render_outcome_summary(result: dict[str, object], compact: bool = False) -> None:
    items = [
        ("Intent", result["intent"]),
        ("Access Check", result["customer_scope"]),
        ("Approval", result["approval"]),
        ("Risk", result["risk"]),
    ]
    if compact:
        cells = "".join(
            '<div class="audit-summary-card">'
            f'<div class="audit-summary-label">{html.escape(label)}</div>'
            f'<div class="audit-summary-value">{html.escape(_pretty(str(value)))}</div>'
            "</div>"
            for label, value in items
        )
        st.markdown(f'<div class="audit-summary-grid">{cells}</div>', unsafe_allow_html=True)
    else:
        cells = "".join(
            '<div class="outcome-item">'
            f'<div class="outcome-label">{html.escape(label)}</div>'
            f'<div class="outcome-value">{html.escape(_pretty(str(value)))}</div>'
            "</div>"
            for label, value in items
        )
        st.markdown(
            '<div class="section-kicker">Outcome Summary</div>'
            f'<div class="outcome-strip">{cells}</div>',
            unsafe_allow_html=True,
        )


def _render_pending_approval() -> None:
    st.markdown(
        """
        <div class="approval-callout">
          <div class="approval-title">Approval required before restricted data is opened</div>
          <div class="approval-grid">
            <div><div class="approval-key">Approver</div><div class="approval-value">Sarah Kim<br>Customer Data Governance Manager</div></div>
            <div><div class="approval-key">Notifications</div><div class="approval-value">Approval Queue + Slack DM + Email</div></div>
            <div><div class="approval-key">Duration</div><div class="approval-value">4 hours</div></div>
            <div><div class="approval-key">Status</div><div class="approval-value">Pending</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_safer_action(action: str) -> None:
    st.markdown(
        '<div class="safer-action"><div class="safer-title">Safer next action</div>'
        f'<div class="safer-copy">{html.escape(action)}</div></div>',
        unsafe_allow_html=True,
    )


def _render_eval_summary(result: dict[str, object]) -> None:
    labels = {
        "intent": "Intent",
        "selected_tables": "Tables",
        "approval": "Approval",
        "customer_scope": "Scope",
    }
    if not result["eval_target"]:
        st.markdown(
            '<div class="eval-result-grid">'
            '<div class="eval-result-card"><div class="eval-result-label">Eval target</div>'
            '<div class="eval-result-value">No labeled eval target</div></div></div>',
            unsafe_allow_html=True,
        )
        return
    cells = "".join(
        '<div class="eval-result-card">'
        f'<div class="eval-result-label">{html.escape(label)}</div>'
        f'<div class="eval-result-value {"pass" if result["eval_result"][key]["match"] else "fail"}">'
        f'{"Match ✅" if result["eval_result"][key]["match"] else "Mismatch ❌"}</div>'
        "</div>"
        for key, label in labels.items()
    )
    st.markdown(f'<div class="eval-result-grid">{cells}</div>', unsafe_allow_html=True)
    st.caption(
        "Demo/debug view: compares intent, selected data sources, approval, and access result against the labeled scenario."
    )


if "persona_selection" not in st.session_state:
    st.session_state.persona_selection = SCENARIOS["A"]["persona"]
if "scenario_selection" not in st.session_state:
    st.session_state.scenario_selection = PERSONA_SCENARIOS[
        st.session_state.persona_selection
    ]
if "request_text" not in st.session_state:
    st.session_state.request_text = SCENARIOS[
        st.session_state.scenario_selection
    ]["request"]
if "last_result" not in st.session_state:
    st.session_state.last_result = None


logo_svg = load_adobe_mark(Path(__file__).parent / "assets" / "adobe-mark.svg")
st.markdown('<div class="cloud-top-spacer"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="internal-header">'
    f'<div class="adobe-mark">{logo_svg}</div>'
    '<div><div class="internal-lockup">Adobe Enterprise · Ask Ari · Internal Productivity Agent</div>'
    '<div class="internal-description">Adobe’s internal productivity platform for resolving customer issues across multiple teams. '
    "Teams can plug in specialized agents for executive prep, campaigns, audience activation, support, and governed data access as they onboard. "
    "Customer data access, approvals, and audit trails are governed by Adobe IT.</div></div></div>",
    unsafe_allow_html=True,
)


with st.container(key="session_context_band", border=False):
    st.markdown(
        '<div class="employee-row-label">Session context</div>',
        unsafe_allow_html=True,
    )
    employee_picker, employee_gutter, employee_card = st.columns(
        [0.5, 0.04, 0.46], gap="small", vertical_alignment="center"
    )
    with employee_picker:
        st.selectbox(
            "Logged-in employee",
            PERSONA_ORDER,
            format_func=_persona_label,
            key="persona_selection",
            on_change=_load_persona_scenario,
        )

    persona = PERSONAS[st.session_state.persona_selection]
    scope = ", ".join(persona["assigned_customers"]) or "No customer-restricted access"
    with employee_card:
        st.markdown(
            '<div class="employee-session-card">'
            '<div class="employee-profile">'
            f'<div class="employee-avatar">{html.escape(_initials(persona["name"]))}</div>'
            '<div><div class="employee-badge">Adobe SSO</div>'
            f'<div class="employee-name">Signed in as {html.escape(persona["name"])}</div>'
            f'<div class="employee-meta">{html.escape(persona["title"])} · {html.escape(persona["team"])}</div>'
            f'<div class="employee-scope">Ari can act for {html.escape(persona["name"].split()[0])} on: {html.escape(scope)}</div></div>'
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )


workbench_left, workbench_gutter, workbench_right = st.columns([0.5, 0.04, 0.46], gap="small")
with workbench_left:
    st.markdown(
        '<div class="request-panel-shell">'
        '<div class="request-kicker">Ask Ari</div>'
        '<div class="request-title">What should Ari help unblock?</div>'
        '<div class="request-copy">Ask about executive prep, campaign delays, audience activation, support signals, or governed data access. Ari checks what it can act on, gathers evidence, routes approvals, and pings the right teams across the matrix org.</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.text_area(
        "Employee request",
        key="request_text",
        height=154,
        label_visibility="collapsed",
        placeholder="Ask Ari about a customer issue, campaign delay, access request, or operational question…",
    )
    st.markdown(
        '<div class="prompt-composer-footer"><span class="prompt-composer-dot"></span>'
        "Scope-aware prompt · Ari checks access before routing work</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="cta-spacer"></div>', unsafe_allow_html=True)
    button_left, button_center, button_right = st.columns([1, 1.2, 1])
    with button_center:
        run_clicked = st.button(
            "Ask Ari",
            type="primary",
            use_container_width=True,
            key="ari_cta",
        )
if run_clicked:
    if st.session_state.request_text.strip():
        with st.spinner("Checking context, scope, policy, and evidence…"):
            st.session_state.last_result = run_agent(
                st.session_state.persona_selection,
                st.session_state.request_text.strip(),
            )
    else:
        st.error("Enter an employee request before running the workflow.")


result = st.session_state.last_result
with workbench_right:
    if result:
        st.markdown(
            '<div class="section-kicker agent-output-kicker">Ari unblocks the work</div>',
            unsafe_allow_html=True,
        )
        output_tab, audit_tab = st.tabs(["Output", "Audit"])
        with output_tab:
            response_body, safer_action = split_safer_next_action(result["response"])
            st.markdown('<div class="agent-answer-body">', unsafe_allow_html=True)
            with st.container(border=False):
                st.markdown(response_body)
            st.markdown("</div>", unsafe_allow_html=True)
            if result["approval"] == "pending":
                _render_pending_approval()
            if safer_action:
                _render_safer_action(safer_action)

            if result["proposed_sql"]:
                with st.expander(
                    "Generated SQL for aggregate, Disney-scoped analysis.", expanded=False
                ):
                    st.caption(
                        "Aggregate counts only. This does not access raw customer-level export logs."
                    )
                    st.code(result["proposed_sql"], language="sql")
        with audit_tab:
            st.markdown('<div class="audit-tool-heading">Outcome Summary</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="audit-tool-note">Debug view for checking how the workflow classified the request, evaluated access, and handled approvals.</div>',
                unsafe_allow_html=True,
            )
            _render_outcome_summary(result, compact=True)
            st.markdown('<div class="audit-tool-heading">Eval Result</div>', unsafe_allow_html=True)
            _render_eval_summary(result)
            st.markdown('<div class="audit-tool-heading">Decision Trace</div>', unsafe_allow_html=True)
            st.markdown(
                f'<span class="trace-id">{html.escape(str(result["trace_id"]))}</span>',
                unsafe_allow_html=True,
            )
            st.table(build_decision_rows(result, persona))
            st.markdown(
                '<div class="audit-note"><strong>Audit-ready decision record:</strong> this workflow captured '
                "request intent, employee access, data sources, approval decision, and final action.</div>",
                unsafe_allow_html=True,
            )
            with st.expander("Raw trace log", expanded=False):
                st.json(result["trace_log"])
    else:
        st.markdown(
            '<div class="response-panel-shell output-panel-surface">'
            '<div class="section-kicker response-panel-kicker">Ari unblocks the work</div>'
            '<div class="response-panel-title">Executive brief, investigation, or approval path appears here</div>'
            '<div class="response-panel-copy">Ari returns the blocker, evidence, team handoff, approval path, or next move. Audit tracks the decision record after a run.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
