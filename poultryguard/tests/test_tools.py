"""
Basic unit tests for PoultryGuard's tool layer. These deliberately avoid the
vision model (CLIP/torch) so they run fast and without GPU/ML dependencies --
useful for CI. Run with: pytest tests/
"""

import pytest

from backend.mcp_server.tools.agrovet_directory import get_nearest_agrovets
from backend.mcp_server.tools.price_lookup import calculate_recovery_feed_formula
from backend.mcp_server.tools.translator import translate_disease_name, translate_quarantine_decision
from backend.mcp_server.tools.treatment_db import get_treatment_protocol, list_known_diseases
from backend.security import InvalidImageError, validate_and_load_image


def test_nearest_agrovets_returns_sorted_by_distance():
    results = get_nearest_agrovets(6.6885, -1.6244, top_n=3)
    assert len(results) == 3
    distances = [r["distance_km"] for r in results]
    assert distances == sorted(distances)


def test_nearest_agrovets_include_directions_url():
    results = get_nearest_agrovets(6.6885, -1.6244, top_n=1)
    assert results[0]["directions_url"].startswith("https://www.google.com/maps")


def test_feed_formula_totals_match_line_items():
    formula = calculate_recovery_feed_formula(total_kg=10.0)
    summed = round(sum(item["line_cost_ghs"] for item in formula["line_items"]), 2)
    assert summed == formula["total_cost_ghs"]


def test_treatment_protocol_known_disease():
    record = get_treatment_protocol("newcastle_disease")
    assert record["name"] == "Newcastle Disease"
    assert record["quarantine"]["required"] is True
    assert len(record["treatment_steps"]) > 0


def test_treatment_protocol_unknown_disease_is_safe_default():
    record = get_treatment_protocol("not_a_real_disease")
    # Unknown diseases should default to quarantine=True as a safety precaution
    assert record["quarantine"]["required"] is True


def test_list_known_diseases_includes_healthy():
    diseases = list_known_diseases()
    ids = [d["id"] for d in diseases]
    assert "healthy" in ids
    assert "newcastle_disease" in ids


def test_twi_translation_known_disease():
    assert translate_disease_name("Newcastle Disease") == "Newcastle Yare"


def test_twi_translation_unknown_disease_falls_back_to_english():
    # Translator must never invent a translation for unknown text --
    # mistranslating medical guidance is worse than not translating it.
    unknown = "Some Disease Not In The Dictionary"
    assert translate_disease_name(unknown) == unknown


def test_quarantine_translation():
    assert "Aane" in translate_quarantine_decision(True)
    assert "Daabi" in translate_quarantine_decision(False)


def test_validate_image_rejects_garbage_bytes():
    with pytest.raises(InvalidImageError):
        validate_and_load_image(b"this is not an image")


def test_validate_image_rejects_empty_bytes():
    with pytest.raises(InvalidImageError):
        validate_and_load_image(b"")


def test_validate_image_rejects_oversized_upload():
    huge_bytes = b"\x00" * (9 * 1024 * 1024)  # 9 MB > 8 MB limit
    with pytest.raises(InvalidImageError):
        validate_and_load_image(huge_bytes)
