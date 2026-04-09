"""Kakao Local Search API helper."""

from __future__ import annotations

import os

import requests


BASE_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
DEFAULT_LOCATION = "울산 북구 송정"


def search_places(keyword: str, size: int = 3) -> list[dict]:
    """카카오 로컬 API로 키워드 검색 후 최대 size개 장소를 반환합니다."""
    api_key = os.getenv("KAKAO_REST_API_KEY", "")
    if not api_key:
        return []

    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": keyword, "size": size}

    try:
        resp = requests.get(BASE_URL, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    documents = resp.json().get("documents", [])
    return [
        {
            "name": d.get("place_name", ""),
            "address": d.get("road_address_name") or d.get("address_name", ""),
            "phone": d.get("phone", ""),
            "lat": float(d.get("y", 0)),
            "lng": float(d.get("x", 0)),
            "url": d.get("place_url", ""),
            "category": d.get("category_name", ""),
        }
        for d in documents
    ]


def build_map_html(places: list[dict]) -> str:
    """Leaflet.js로 마커가 찍힌 지도 HTML을 반환합니다."""
    if not places:
        return ""

    center_lat = places[0]["lat"]
    center_lng = places[0]["lng"]

    markers_js = ""
    for i, p in enumerate(places, 1):
        popup = f"{i}. {p['name']}<br/>{p['address']}"
        if p["phone"]:
            popup += f"<br/>📞 {p['phone']}"
        markers_js += (
            f"L.marker([{p['lat']}, {p['lng']}])"
            f".addTo(map)"
            f".bindPopup('{popup}', {{maxWidth: 220}})"
        )
        if i == 1:
            markers_js += ".openPopup()"
        markers_js += ";\n"

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body {{ margin: 0; padding: 0; }}
    #map {{ width: 100%; height: 380px; border-radius: 18px; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map').setView([{center_lat}, {center_lng}], 15);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '© OpenStreetMap contributors'
    }}).addTo(map);
    {markers_js}
  </script>
</body>
</html>
"""
