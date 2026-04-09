"""Kakao Local API helpers for geocoding and nearby place search."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODE_CACHE_PATH = Path(".kakao_geocode_cache.json")


class KakaoApiError(RuntimeError):
    """Raised when a Kakao Local API request fails."""


@dataclass(frozen=True)
class GeoPoint:
    query: str
    longitude: float
    latitude: float
    display_name: str = ""
    area_text: str = ""


@dataclass(frozen=True)
class PlaceCandidate:
    name: str
    category: str
    address: str
    latitude: float
    longitude: float
    distance_m: float | None = None


def has_kakao_credentials() -> bool:
    return bool(os.getenv("KAKAO_REST_API_KEY"))


def haversine_meters(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    radius_m = 6371000.0
    d_lat = radians(latitude2 - latitude1)
    d_lon = radians(longitude2 - longitude1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(latitude1))
        * cos(radians(latitude2))
        * sin(d_lon / 2) ** 2
    )
    return 2 * radius_m * asin(sqrt(a))


def _headers() -> dict[str, str]:
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key:
        raise KakaoApiError("KAKAO_REST_API_KEY is missing.")
    return {"Authorization": f"KakaoAK {api_key}"}


def _request_json(url: str) -> Any:
    request = Request(url, headers=_headers())
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        detail = f"HTTP {exc.code}"
        if body:
            detail += f": {body}"
        raise KakaoApiError(detail) from exc
    except Exception as exc:
        raise KakaoApiError(str(exc)) from exc


def _load_cache() -> dict[str, dict[str, Any]]:
    if not GEOCODE_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(GEOCODE_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, dict[str, Any]]) -> None:
    GEOCODE_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _geo_from_cache(query: str) -> GeoPoint | None:
    cache = _load_cache()
    cached = cache.get(query)
    if not cached:
        return None
    return GeoPoint(
        query=query,
        longitude=float(cached["longitude"]),
        latitude=float(cached["latitude"]),
        display_name=str(cached.get("display_name", "")),
        area_text=str(cached.get("area_text", "")),
    )


def _cache_geo_point(query: str, point: GeoPoint) -> None:
    cache = _load_cache()
    cache[query] = {
        "longitude": point.longitude,
        "latitude": point.latitude,
        "display_name": point.display_name,
        "area_text": point.area_text,
    }
    _save_cache(cache)


def geocode_address(query: str) -> GeoPoint | None:
    cached = _geo_from_cache(query)
    if cached is not None:
        return cached

    address_url = "https://dapi.kakao.com/v2/local/search/address.json?" + urlencode(
        {"query": query}
    )
    payload = _request_json(address_url)
    documents = payload.get("documents") or []
    if documents:
        first = documents[0]
        address = first.get("address") or {}
        road_address = first.get("road_address") or {}
        area_text = " ".join(
            part
            for part in [
                address.get("region_1depth_name", "") or road_address.get("region_1depth_name", ""),
                address.get("region_2depth_name", "") or road_address.get("region_2depth_name", ""),
                address.get("region_3depth_name", "") or road_address.get("region_3depth_name", ""),
            ]
            if part
        ).strip()
        display_name = road_address.get("address_name", "") or address.get("address_name", "")
        point = GeoPoint(
            query=query,
            longitude=float(first["x"]),
            latitude=float(first["y"]),
            display_name=display_name,
            area_text=area_text,
        )
        _cache_geo_point(query, point)
        return point

    keyword_url = "https://dapi.kakao.com/v2/local/search/keyword.json?" + urlencode(
        {"query": query, "size": 1}
    )
    keyword_payload = _request_json(keyword_url)
    keyword_documents = keyword_payload.get("documents") or []
    if not keyword_documents:
        return None

    first = keyword_documents[0]
    area_text = " ".join(
        part
        for part in [
            first.get("region_1depth_name", ""),
            first.get("region_2depth_name", ""),
            first.get("region_3depth_name", ""),
        ]
        if part
    ).strip()
    display_name = first.get("road_address_name", "") or first.get("address_name", "")
    point = GeoPoint(
        query=query,
        longitude=float(first["x"]),
        latitude=float(first["y"]),
        display_name=display_name,
        area_text=area_text,
    )
    _cache_geo_point(query, point)
    return point


def reverse_geocode(longitude: float, latitude: float) -> GeoPoint | None:
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?" + urlencode(
        {"x": longitude, "y": latitude}
    )
    payload = _request_json(url)
    documents = payload.get("documents") or []
    area_text = ""
    if documents:
        first = documents[0]
        area_text = " ".join(
            part
            for part in [
                first.get("region_1depth_name", ""),
                first.get("region_2depth_name", ""),
                first.get("region_3depth_name", ""),
            ]
            if part
        ).strip()

    return GeoPoint(
        query="current_location",
        longitude=longitude,
        latitude=latitude,
        display_name=area_text,
        area_text=area_text,
    )


def search_nearby_restaurants(
    latitude: float,
    longitude: float,
    radius_m: int,
) -> list[PlaceCandidate]:
    url = "https://dapi.kakao.com/v2/local/search/category.json?" + urlencode(
        {
            "category_group_code": "FD6",
            "x": longitude,
            "y": latitude,
            "radius": radius_m,
            "sort": "distance",
            "size": 15,
            "page": 1,
        }
    )
    payload = _request_json(url)
    documents = payload.get("documents") or []
    candidates: list[PlaceCandidate] = []
    for document in documents:
        distance_raw = document.get("distance", "")
        distance_m = float(distance_raw) if distance_raw else None
        candidates.append(
            PlaceCandidate(
                name=document.get("place_name", "").strip(),
                category=document.get("category_name", "").strip(),
                address=document.get("road_address_name", "").strip()
                or document.get("address_name", "").strip(),
                latitude=float(document["y"]),
                longitude=float(document["x"]),
                distance_m=distance_m,
            )
        )
    return candidates
