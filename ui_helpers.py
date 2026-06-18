from pathlib import Path




def load_adobe_mark(logo_path=None) -> str:
    """Load local logo SVG if available; otherwise return a safe inline fallback."""
    if logo_path is None:
        logo_path = Path(__file__).parent / "assets" / "adobe-mark.svg"
    else:
        logo_path = Path(logo_path)

    if logo_path.exists():
        return logo_path.read_text(encoding="utf-8")

    return """
    <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="7" fill="#D71920"/>
      <path d="M16 7L25 25H19.5L16 17.5L12.5 25H7L16 7Z" fill="white"/>
    </svg>
    """


def split_safer_next_action(response: str):
    """Split safer next action from a response if present."""
    markers = [
        "Safer next action:",
        "**Safer next action:**",
        "Safer next step:",
        "**Safer next step:**",
    ]

    for marker in markers:
        if marker in response:
            before, after = response.split(marker, 1)
            return before.strip(), after.strip()

    return response, None


def _join_list(value):
    if value is None:
        return "None"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "None"
    return str(value)


def build_decision_rows(result: dict):
    """Build PM-friendly audit-ready decision record rows for Streamlit display."""
    tools_used = result.get("tools_used", [])
    if isinstance(tools_used, list):
        tool_names = []
        for tool in tools_used:
            if isinstance(tool, dict):
                tool_names.append(tool.get("tool") or tool.get("name") or str(tool))
            else:
                tool_names.append(str(tool))
        tools_text = ", ".join(tool_names) if tool_names else "None"
    else:
        tools_text = str(tools_used)

    selected_tables = result.get("selected_tables", [])
    tables_text = _join_list(selected_tables)

    eval_target = result.get("validation_target") or result.get("eval_target") or {}
    validation_result = result.get("validation_result") or result.get("eval_result") or {}

    if validation_result:
        validation_text = ", ".join(
            f"{key}: {'✅' if value else '❌'}"
            for key, value in validation_result.items()
            if isinstance(value, bool)
        )
        if not validation_text:
            validation_text = str(validation_result)
    elif eval_target:
        validation_text = "Validation target defined"
    else:
        validation_text = "No labeled validation target"

    return [
        {
            "Step": "Classification",
            "Input": result.get("user_asked", "Employee request"),
            "Output": result.get("agent_inferred", result.get("intent", "Unknown")),
        },
        {
            "Step": "Customer scope",
            "Input": result.get("customer_scope", "Not determined"),
            "Output": result.get("customer_scope", "Not determined"),
        },
        {
            "Step": "Access policy",
            "Input": tables_text,
            "Output": result.get("approval", "Unknown"),
        },
        {
            "Step": "Tools and data",
            "Input": tools_text,
            "Output": tables_text,
        },
        {
            "Step": "Approval",
            "Input": result.get("intent", "Unknown"),
            "Output": f"{result.get('approval', 'Unknown')} · Risk: {result.get('risk', 'Unknown')}",
        },
        {
            "Step": "Validation",
            "Input": str(eval_target) if eval_target else "No labeled target",
            "Output": validation_text,
        },
    ]
