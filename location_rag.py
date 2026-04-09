"""Location-aware recommendation context builders."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from kakao_api import (
    GeoPoint,
    KakaoApiError,
    PlaceCandidate,
    geocode_address,
    has_kakao_credentials,
    haversine_meters,
    reverse_geocode,
    search_nearby_restaurants,
)
from menu_db import MenuRow, load_menu_context, load_menu_rows


WALKING_METERS_PER_MINUTE = 80
DEFAULT_NEARBY_RADIUS_M = 500

KW_WALK = "\uB3C4\uBCF4"
KW_RADIUS = "\uBC18\uACBD"
KW_NEAR = "\uADFC\uCC98"
KW_AROUND = "\uC8FC\uBCC0"
KW_CLOSE = "\uAC00\uAE4C\uC6B4"
KW_MY_LOCATION = "\uB0B4 \uC704\uCE58"
KW_CURRENT_LOCATION = "\uD604\uC7AC \uC704\uCE58"
KW_FROM = "\uC5D0\uC11C"
KW_MINUTE = "\uBD84"
KW_DISTANCE = "\uAC70\uB9AC"
KW_INSIDE = "\uC548"
KW_WITHIN = "\uC774\uB0B4"


@dataclass(frozen=True)
class LocationIntent:
    wants_nearby: bool
    origin_query: str = ""
    radius_m: int | None = None
    used_current_location: bool = False


@dataclass(frozen=True)
class RecommendationContext:
    context_text: str
    source_label: str
    note: str = ""


def parse_location_intent(user_text: str) -> LocationIntent:
    text = " ".join(user_text.split())
    wants_nearby = any(
        keyword in text
        for keyword in (
            KW_WALK,
            KW_RADIUS,
            KW_NEAR,
            KW_AROUND,
            KW_CLOSE,
            KW_MY_LOCATION,
            KW_CURRENT_LOCATION,
        )
    )

    radius_m: int | None = None
    walk_match = re.search(rf"{KW_WALK}\s*(\d+)\s*{KW_MINUTE}", text)
    if walk_match:
        radius_m = int(walk_match.group(1)) * WALKING_METERS_PER_MINUTE

    meter_match = re.search(rf"{KW_RADIUS}\s*(\d+)\s*m", text, flags=re.IGNORECASE)
    if meter_match:
        radius_m = int(meter_match.group(1))

    meter_inside_match = re.search(
        rf"(\d+)\s*m\s*(?:{KW_INSIDE}|{KW_WITHIN})",
        text,
        flags=re.IGNORECASE,
    )
    if meter_inside_match:
        radius_m = int(meter_inside_match.group(1))

    origin_query = ""
    origin_match = re.search(
        rf"(.+?){KW_FROM}\s*(?:{KW_WALK}\s*\d+\s*{KW_MINUTE}(?:{KW_DISTANCE})?|"
        rf"{KW_RADIUS}\s*\d+\s*m|(?:\d+)\s*m\s*(?:{KW_INSIDE}|{KW_WITHIN})|{KW_NEAR}|{KW_AROUND})",
        text,
    )
    if origin_match:
        origin_query = _cleanup_origin_query(origin_match.group(1))

    used_current_location = KW_MY_LOCATION in text or KW_CURRENT_LOCATION in text
    return LocationIntent(
        wants_nearby=wants_nearby,
        origin_query=origin_query,
        radius_m=radius_m,
        used_current_location=used_current_location,
    )


def _cleanup_origin_query(origin_query: str) -> str:
    cleaned = origin_query.strip(" ,.")
    for marker in (
        "\uCD94\uCC9C\uD574\uC8FC\uB294\uB370",
        "\uCD94\uCC9C\uD574\uC918",
        "\uCD94\uCC9C",
        "\uAE30\uC900\uC73C\uB85C",
        "\uADFC\uCC98",
        "\uC8FC\uBCC0",
    ):
        if marker in cleaned:
            cleaned = cleaned.split(marker)[-1].strip(" ,.")
    return cleaned


def _resolve_origin(
    intent: LocationIntent,
    origin_query: str | None,
    latitude: float | None,
    longitude: float | None,
) -> GeoPoint | None:
    if origin_query:
        return geocode_address(origin_query)

    if intent.origin_query:
        return geocode_address(intent.origin_query)

    if latitude is not None and longitude is not None:
        return reverse_geocode(longitude, latitude)

    return None


def _csv_candidates_nearby(
    origin: GeoPoint,
    csv_path: Path | None,
    radius_m: int,
) -> list[PlaceCandidate]:
    rows = load_menu_rows(csv_path)
    candidates: list[PlaceCandidate] = []
    for row in rows:
        if not row.address:
            continue
        point = geocode_address(row.address)
        if point is None:
            continue

        distance_m = haversine_meters(
            origin.latitude,
            origin.longitude,
            point.latitude,
            point.longitude,
        )
        if distance_m > radius_m:
            continue

        candidates.append(
            PlaceCandidate(
                name=row.name,
                category="csv_restaurant",
                address=row.address,
                latitude=point.latitude,
                longitude=point.longitude,
                distance_m=distance_m,
            )
        )

    candidates.sort(key=lambda candidate: candidate.distance_m or 10**9)
    return candidates


def _origin_keywords(origin_query: str) -> list[str]:
    raw_tokens = re.findall(r"[0-9A-Za-z\uAC00-\uD7A3]+", origin_query)
    stopwords = {
        "\uC624\uB298",
        "\uC810\uC2EC",
        "\uCD94\uCC9C",
        "\uC6B8\uC0B0",
        "\uBD81\uAD6C",
        "\uB0A8\uAD6C",
        "\uB3D9\uAD6C",
        "\uC911\uAD6C",
        "\uC11C\uAD6C",
    }
    keywords: list[str] = []
    for token in raw_tokens:
        if len(token) < 2 or token in stopwords:
            continue
        keywords.append(token)
        for suffix in ("\uB3D9", "\uB85C", "\uAE38", "\uD14C\uB77C\uC2A4"):
            if token.endswith(suffix) and len(token) > len(suffix) + 1:
                keywords.append(token[: -len(suffix)])
    deduped: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        if keyword in seen:
            continue
        seen.add(keyword)
        deduped.append(keyword)
    return deduped


def _csv_candidates_by_text(csv_path: Path | None, origin_query: str) -> list[MenuRow]:
    rows = load_menu_rows(csv_path)
    keywords = _origin_keywords(origin_query)
    scored_rows: list[tuple[int, MenuRow]] = []
    for row in rows:
        haystack = f"{row.name} {row.address}".lower()
        score = sum(1 for keyword in keywords if keyword.lower() in haystack)
        if score > 0:
            scored_rows.append((score, row))
    scored_rows.sort(key=lambda item: (-item[0], item[1].name))
    return [row for _, row in scored_rows]


def _format_csv_text_fallback(origin_query: str, rows: list[MenuRow]) -> str:
    lines = [
        f"Nearby text fallback origin={origin_query}",
        "Use the following CSV restaurants as approximate nearby candidates based on address text match.",
    ]
    if not rows:
        lines.append("No CSV text-match candidates were found.")
        return "\n".join(lines)

    for index, row in enumerate(rows[:12], start=1):
        lines.append(
            f"{index}. name={row.name}, address={row.address}, closed_day={row.closed_day}"
        )
    return "\n".join(lines)


def _format_mixed_context(
    origin: GeoPoint,
    csv_candidates: list[PlaceCandidate],
    kakao_candidates: list[PlaceCandidate],
    radius_m: int,
) -> tuple[str, str]:
    notes: list[str] = []
    lines = [
        f"Nearby search origin={origin.query}, area={origin.area_text}, radius_m={radius_m}",
    ]

    if csv_candidates:
        lines.append("CSV nearby candidates:")
        for index, candidate in enumerate(csv_candidates[:10], start=1):
            lines.append(
                f"{index}. name={candidate.name}, category={candidate.category}, "
                f"address={candidate.address}, distance={candidate.distance_m:.0f}m"
            )
    else:
        notes.append("No nearby CSV restaurants matched the current radius.")

    if kakao_candidates:
        lines.append("Kakao nearby candidates:")
        for index, candidate in enumerate(kakao_candidates[:8], start=1):
            distance = (
                f"{candidate.distance_m:.0f}m"
                if candidate.distance_m is not None
                else "unknown"
            )
            lines.append(
                f"{index}. name={candidate.name}, category={candidate.category}, "
                f"address={candidate.address}, distance={distance}"
            )
    else:
        notes.append("No nearby Kakao restaurants matched the current radius.")

    if not csv_candidates and not kakao_candidates:
        lines.append("No nearby recommendation candidates were found.")

    return "\n".join(lines), " ".join(notes)


def build_recommendation_context(
    user_text: str,
    csv_path: Path | None,
    origin_query: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: int | None = None,
) -> RecommendationContext:
    intent = parse_location_intent(user_text)
    effective_radius_m = radius_m or intent.radius_m or DEFAULT_NEARBY_RADIUS_M

    if intent.wants_nearby or origin_query or latitude is not None or longitude is not None:
        if not has_kakao_credentials():
            fallback_origin = origin_query or intent.origin_query
            if fallback_origin:
                fallback_rows = _csv_candidates_by_text(csv_path, fallback_origin)
                return RecommendationContext(
                    context_text=_format_csv_text_fallback(fallback_origin, fallback_rows),
                    source_label="csv_text_fallback",
                    note="KAKAO_REST_API_KEY is missing, so approximate CSV text-match fallback was used.",
                )
            return RecommendationContext(
                context_text="",
                source_label="csv+kakao_nearby",
                note="KAKAO_REST_API_KEY is missing.",
            )

        try:
            origin = _resolve_origin(intent, origin_query, latitude, longitude)
        except KakaoApiError as exc:
            message = str(exc)
            if "HTTP 403" in message:
                message = (
                    "Kakao Local API access was denied. Check whether Kakao Maps is enabled "
                    "for this app in Kakao Developers."
                )
            fallback_origin = origin_query or intent.origin_query
            if fallback_origin:
                fallback_rows = _csv_candidates_by_text(csv_path, fallback_origin)
                return RecommendationContext(
                    context_text=_format_csv_text_fallback(fallback_origin, fallback_rows),
                    source_label="csv_text_fallback",
                    note=f"{message} Approximate CSV text-match fallback was used.",
                )
            return RecommendationContext(
                context_text="",
                source_label="csv+kakao_nearby",
                note=message,
            )
        if origin is None:
            fallback_origin = origin_query or intent.origin_query
            if fallback_origin:
                fallback_rows = _csv_candidates_by_text(csv_path, fallback_origin)
                return RecommendationContext(
                    context_text=_format_csv_text_fallback(fallback_origin, fallback_rows),
                    source_label="csv_text_fallback",
                    note="Could not resolve the requested origin from Kakao. Approximate CSV text-match fallback was used.",
                )
            return RecommendationContext(
                context_text="",
                source_label="csv+kakao_nearby",
                note="Could not resolve the requested origin from Kakao.",
            )

        try:
            csv_candidates = _csv_candidates_nearby(origin, csv_path, effective_radius_m)
            kakao_candidates = search_nearby_restaurants(
                origin.latitude,
                origin.longitude,
                effective_radius_m,
            )
        except KakaoApiError as exc:
            message = str(exc)
            if "HTTP 403" in message:
                message = (
                    "Kakao Local API access was denied. Check whether Kakao Maps is enabled "
                    "for this app in Kakao Developers."
                )
            fallback_origin = origin_query or intent.origin_query or origin.area_text
            if fallback_origin:
                fallback_rows = _csv_candidates_by_text(csv_path, fallback_origin)
                return RecommendationContext(
                    context_text=_format_csv_text_fallback(fallback_origin, fallback_rows),
                    source_label="csv_text_fallback",
                    note=f"{message} Approximate CSV text-match fallback was used.",
                )
            return RecommendationContext(
                context_text="",
                source_label="csv+kakao_nearby",
                note=message,
            )
        context_text, note = _format_mixed_context(
            origin,
            csv_candidates,
            kakao_candidates,
            effective_radius_m,
        )
        return RecommendationContext(
            context_text=context_text,
            source_label="csv+kakao_nearby",
            note=note,
        )

    menu_context = load_menu_context(csv_path)
    return RecommendationContext(
        context_text=menu_context,
        source_label="csv",
        note="" if menu_context else "CSV database unavailable.",
    )
