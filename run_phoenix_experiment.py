import csv
from pathlib import Path

from agent import run_agent
from tracing import enable_arize_tracing, flush_arize_tracing


VALIDATION_CASES_PATH = Path("validation_cases.csv")


def load_mock_trace_cases(path=VALIDATION_CASES_PATH):
    with Path(path).open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def main():
    status = enable_arize_tracing()
    print(status)

    cases = load_mock_trace_cases()
    print(f"Generating {len(cases)} Ask Ari mock traces")
    results = []
    for case in cases:
        result = run_agent(
            persona=case["persona"],
            request=case["request"],
        )
        results.append(result)
        print(
            case["id"],
            case["persona"],
            result["trace_id"],
            result["intent"],
            result["approval"],
            result["customer_scope"],
        )

    flush_arize_tracing()
    return results


if __name__ == "__main__":
    main()
