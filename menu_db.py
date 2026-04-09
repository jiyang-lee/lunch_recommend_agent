"""CSV-backed lunch menu database helpers."""

from __future__ import annotations

import csv
from pathlib import Path


DEFAULT_MENU_CSV = "restaurants.csv"


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {str(key).strip(): str(value).strip() for key, value in row.items()}
            for row in reader
        ]


def format_menu_context(rows: list[dict[str, str]], limit: int = 20) -> str:
    if not rows:
        return "Menu DB is empty."

    headers = [header for header in rows[0].keys() if header]
    lines = []
    for index, row in enumerate(rows[:limit], start=1):
        parts = [f"{header}={row.get(header, '')}" for header in headers]
        lines.append(f"{index}. " + ", ".join(parts))

    if len(rows) > limit:
        lines.append(f"... and {len(rows) - limit} more rows")

    return "\n".join(lines)


def load_menu_context(csv_path: Path | None) -> str:
    if csv_path is None or not csv_path.exists():
        return ""

    rows = read_csv_rows(csv_path)
    return format_menu_context(rows)
