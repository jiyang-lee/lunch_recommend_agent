"""CSV-backed lunch menu database helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


DEFAULT_MENU_CSV = str(Path("db") / "restaurants.csv")
KOREAN_WEEKDAYS = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일",
]


@dataclass(frozen=True)
class MenuRow:
    id: str
    name: str
    closed_day: str
    address: str


def current_korean_weekday(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return KOREAN_WEEKDAYS[now.weekday()]


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {str(key).strip(): str(value).strip() for key, value in row.items()}
            for row in reader
        ]


def to_menu_rows(rows: Iterable[dict[str, str]]) -> list[MenuRow]:
    menu_rows: list[MenuRow] = []
    for row in rows:
        menu_rows.append(
            MenuRow(
                id=row.get("id", ""),
                name=row.get("가게이름", ""),
                closed_day=row.get("휴무일", ""),
                address=row.get("주소", ""),
            )
        )
    return menu_rows


def is_open_today(row: MenuRow, weekday: str) -> bool:
    if not row.closed_day:
        return True
    return row.closed_day != weekday


def filter_open_rows(rows: list[MenuRow], weekday: str) -> list[MenuRow]:
    return [row for row in rows if is_open_today(row, weekday)]


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


def format_menu_rows(rows: list[MenuRow], limit: int = 20) -> str:
    if not rows:
        return "Menu DB is empty."

    lines = []
    for index, row in enumerate(rows[:limit], start=1):
        parts = [
            f"id={row.id}",
            f"name={row.name}",
            f"closed_day={row.closed_day}",
            f"address={row.address}",
        ]
        lines.append(f"{index}. " + ", ".join(parts))

    if len(rows) > limit:
        lines.append(f"... and {len(rows) - limit} more rows")

    return "\n".join(lines)


def load_menu_context(csv_path: Path | None) -> str:
    if csv_path is None or not csv_path.exists():
        return ""

    rows = read_csv_rows(csv_path)
    return format_menu_context(rows)


def load_menu_rows(csv_path: Path | None) -> list[MenuRow]:
    if csv_path is None or not csv_path.exists():
        return []

    return to_menu_rows(read_csv_rows(csv_path))


def build_menu_context_for_day(csv_path: Path | None, weekday: str) -> str:
    rows = load_menu_rows(csv_path)
    if not rows:
        return ""

    open_rows = filter_open_rows(rows, weekday)
    if not open_rows:
        return ""

    header = (
        "The following restaurants are open on the selected day. "
        "When recommending lunch, only use these open restaurants."
    )
    return header + "\n" + format_menu_rows(open_rows)
