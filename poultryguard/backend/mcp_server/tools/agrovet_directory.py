"""
agrovet_directory.py

MCP tool for finding the nearest agrovets (agricultural input shops) to a
farmer's location. Uses a placeholder JSON directory for Kumasi; in production
this would query a live data source (e.g. Google Places API or a government
agro-dealer registry).
"""

import json
import math
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agrovets_kumasi.json")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def get_nearest_agrovets(lat: float, lon: float, top_n: int = 3) -> list[dict]:
    """
    Return the `top_n` nearest agrovets to the given coordinates, each annotated
    with distance in km and a Google Maps directions link.
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        agrovets = json.load(f)["agrovets"]

    for shop in agrovets:
        shop["distance_km"] = round(_haversine_km(lat, lon, shop["lat"], shop["lon"]), 2)
        shop["directions_url"] = (
            f"https://www.google.com/maps/dir/?api=1&destination={shop['lat']},{shop['lon']}"
        )

    agrovets.sort(key=lambda s: s["distance_km"])
    return agrovets[:top_n]
