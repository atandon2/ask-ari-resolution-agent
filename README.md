# Ask Ari: Cross-Functional Resolution Agent

Ask Ari is a lightweight Streamlit demo of an internal workplace productivity agent for resolving customer issues across multiple teams. It is designed for a PM walkthrough about governed agent workflows, observability, validation, access policy, and cross-functional handoffs.

The core product idea: the agent feels agentic because it infers likely resources, checks customer and table access, invokes traceable tools, creates approvals, and explains decisions.

This is a demo sandbox, not a production Adobe integration.

## What works today locally

- Streamlit UI for employee request intake and Ari’s response.
- Six employee personas with distinct customer/account permissions.
- Eight deterministic demo scenarios covering briefings, investigations, approvals, numerical analysis, clarification, and rejection.
- Fake enterprise tools and data sources; no production systems are connected.
- A local `trace_log` with a unique trace ID, ordered agent steps, fake tool calls, and workflow completion.
- Audit view with request intent, inferred customer scope, selected data sources, approval decision, workflow timeline, validation target, and validation result.
- Twenty labeled examples in `validation_cases.csv`.
- A local validation runner that checks intent, tables, approval, and customer scope, then writes `validation_results.csv`.
- Aggregate-only SQL for the numerical analysis scenario; all other scenarios return `proposed_sql = None`.

Phoenix/Arize is still optional and not required by the Streamlit app. The repo also includes optional Step 2 runners for exporting traces and running dataset experiments in Arize when you install `requirements-arize.txt` and provide Arize credentials.

## Local Run

Python 3.10 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If you already have an environment active, the minimal commands are:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app imports Streamlit and local Python modules only. It does not import or require Phoenix, Arize, OpenTelemetry, or OpenInference.

## Run tests

```bash
source .venv/bin/activate
python -m pytest -q
```

The suite verifies all eight canonical demos, all twenty validation rows, trace lifecycle ordering, governance rejections, clarification behavior, SQL isolation, local validation output, and the optional integration stub.

## Run validation checks

```bash
source .venv/bin/activate
python run_validation_checks.py
```

Expected summary:

```text
Validation checks: 20/20 passed
Results written to validation_results.csv
```

`validation_results.csv` is regenerated on every run and ignored by Git. Each row includes its trace ID, expected and actual values, four match flags, and an overall pass result.

## Build the Arize dataset CSV

```bash
source .venv/bin/activate
python build_arize_dataset.py
```

This writes `arize_ask_ari_dataset.csv`, a 20-row upload file derived from `validation_cases.csv`.

Upload it in Arize:

1. Go to **Develop → Datasets & Experiments**.
2. Click **+ New Dataset**.
3. Choose **Upload CSV**.
4. Upload `arize_ask_ari_dataset.csv`.
5. Name the dataset `ask-ari-validation-cases`.

The CSV includes the employee request as `attributes.input.value`, persona and case metadata, and expected labels for intent, selected tables, approval path, and customer scope.

## Run the Arize experiment

Use this after uploading `arize_ask_ari_dataset.csv` as a dataset named `ask-ari-validation-cases`.

This is the right path for Ask Ari because the workflow is a custom Python agent: it performs classification, access checks, tool selection, approval routing, and response generation. Arize Playground is better for prompt-only experiments. For this use case, run the agent as code and attach deterministic evaluators.

```bash
source .venv/bin/activate
pip install -r requirements-arize.txt

export ARIZE_SPACE_ID="your-space-id"
export ARIZE_API_KEY="your-api-key"
export ARIZE_DATASET_NAME="ask-ari-validation-cases"
export ARIZE_EXPERIMENT_NAME="ask-ari-v0-deterministic-router"

python run_arize_experiment.py
```

The runner calls `run_agent()` for every dataset row and logs four code-eval columns:

- `intent_match`
- `tables_match`
- `approval_match`
- `customer_scope_match`

To test the loop before logging a real experiment, add:

```bash
export ARIZE_DRY_RUN=true
python run_arize_experiment.py
```

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to Streamlit Community Cloud.
3. Choose “New app.”
4. Select this GitHub repo.
5. Set main file path to `app.py`.
6. Deploy.
7. Confirm the app loads and demo scenarios run.

No secrets are required for the local demo. Phoenix, Arize, OpenTelemetry, and OpenInference packages are optional future additions and are not needed for deployment.

## Repository structure

| File or folder | Responsibility |
|---|---|
| `app.py` | Streamlit UI, employee request intake, Ari response, audit view, and validation comparison |
| `agent.py` | Replaceable classifier boundary, deterministic routing, policy workflow, and structured result |
| `tools.py` | Fake enterprise data, access checks, approval submission, and aggregate SQL |
| `tracing.py` | Single local tracing boundary: workflow start, ordered steps, workflow end, and trace retrieval |
| `run_validation_checks.py` | Executable deterministic validation runner and CSV result writer |
| `integration_stub.py` | Import-safe, explicitly inactive future Phoenix/Arize integration boundaries |
| `run_phoenix_experiment.py` | Optional bulk trace generator for Arize/OpenTelemetry tracing |
| `run_arize_experiment.py` | Optional Arize dataset experiment runner with deterministic code evaluators |
| `requirements-arize.txt` | Optional packages for Arize tracing and experiment runs |
| `validation_cases.csv` | Twenty labeled local examples |
| `requirements.txt` | Minimal packages required to run the app and tests |
| `tests/` | Agent, governance, trace, UI contract, validation, and optional-integration tests |
| `screenshots/` | Optional folder for README or presentation screenshots |
| `assets/` | Static UI assets, including the Adobe-style mark used by the Streamlit app |

The main interface remains intentionally small:

```python
result = run_agent(persona, request)
```

The structured result includes `trace_id`, `trace_log`, `intent`, `risk`, `approval`, `customer_scope`, `tools_used`, `selected_tables`, `proposed_sql`, `eval_target`, and `response`. It also retains the original request, inferred interpretation, and canonical validation comparison for the UI.

## Model Relevance

This is a deterministic V0 for live-demo reliability. `CLASSIFIER_MODE = "deterministic"` guarantees repeatable scenario outcomes. `classify_with_llm(persona, request)` marks a future model boundary without pretending a model is connected.

In production, an LLM would handle:

- intent detection
- customer extraction
- inferred data source selection
- policy interpretation
- clarification behavior
- response synthesis

The model should not silently own every control. Customer authorization, enforceable table policy, approval state, tracing, and validation comparison remain explicit application responsibilities.

The walkthrough narrative is:

> deterministic demo → model boundary → trace log → validation target → validation result → product recommendations

## How this plugs into Arize/Phoenix

Phoenix/Arize integration is not active by default. The app, tests, and local validation flow run without Arize, Phoenix, OpenTelemetry, or OpenInference installed. `integration_stub.py` remains an import-safe map of the integration boundary and performs no network call.

The repo supports Step 2 in these ways:

1. `tracing.py` centralizes workflow start, step, and end events. Its TODO markers show where OpenInference/OpenTelemetry spans and Phoenix export can be added.
2. `run_phoenix_experiment.py` can generate multiple Ask Ari workflow traces into Arize when optional tracing credentials are configured.
3. `validation_cases.csv` provides a labeled dataset that can be created or loaded in Arize/Phoenix.
4. `run_arize_experiment.py` runs `run_agent()` against that dataset and attaches deterministic code evaluators for intent, tables, approval, and customer scope.
5. `run_agent()` returns stable fields and a trace ID for each experiment row.

The Step 2 development workflow is:

1. Upload `arize_ask_ari_dataset.csv` as `ask-ari-validation-cases`.
2. Run `run_arize_experiment.py` to create the baseline deterministic experiment.
3. Review evaluator failures by intent, table selection, approval path, and customer scope.
4. Change the classifier, prompt, policy rules, or model boundary.
5. Re-run with a new `ARIZE_EXPERIMENT_NAME`.
6. Compare baseline vs. candidate experiments in Arize.
7. Add LLM-as-judge evaluators later for subjective response quality such as groundedness, actionability, executive readiness, and policy explanation.

The local app, tests, and validation runner remain fully usable when Phoenix and Arize are not installed or configured.

## Five-minute PM walkthrough

1. **Emily customer escalation:** Show Ari’s cross-team executive briefing and the evidence sources selected by the agent.
2. **Alex guided access escalation:** Show that Ari can infer restricted data is needed without opening it; point to Sarah Kim, notification channels, and the four-hour approval.
3. **Emily numerical analysis:** Show the only SQL path and explain that it returns Disney-scoped aggregate counts, not raw logs.
4. **Maya governance rejection:** Show how broad restricted export requests are blocked with a safer next action.
5. **Audit view:** Walk from user request to agent inference, workflow timeline, validation target, and validation result.
6. **Step 2:** Explain how the same trace and result contracts can later be exported to Phoenix without changing the local agent flow.

## Scenario map

| ID | Outcome | Product point |
|---|---|---|
| A | Executive briefing | Cross-team evidence synthesis |
| B | Marketing investigation | End-to-end activation workflow |
| C | Technical investigation | Incident-to-ticket-to-bug reasoning |
| D | Pending access request | Guided, time-bound governance |
| E | Aggregate NL-to-SQL | Numerical answer without raw logs |
| F | Clarifying questions | No unsupported customer assumption |
| G | Governance rejection | Broad restricted export blocked |
| H | Customer-scope rejection | Assigned-account boundary enforced |
