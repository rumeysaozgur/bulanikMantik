from __future__ import annotations

from fuzzy_credit_risk import evaluate_scenarios


def main() -> None:
    rows = evaluate_scenarios()
    headers = list(rows[0].keys())
    widths = {
        header: max(len(str(header)), *(len(str(row[header])) for row in rows))
        for header in headers
    }
    print(" | ".join(header.ljust(widths[header]) for header in headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(" | ".join(str(row[header]).ljust(widths[header]) for header in headers))


if __name__ == "__main__":
    main()
