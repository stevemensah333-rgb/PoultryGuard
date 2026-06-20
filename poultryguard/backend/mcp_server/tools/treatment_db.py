"""
treatment_db.py

MCP tool for retrieving treatment steps, symptoms, and quarantine guidance for
a given disease ID. Backed by a placeholder JSON file; in production this
should be sourced from a veterinary-reviewed knowledge base.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "diseases.json")


def _load_diseases() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["diseases"]


def get_treatment_protocol(disease_id: str) -> dict:
    """Return the full treatment record for a disease_id, or a 'not found' stub."""
    diseases = _load_diseases()
    for disease in diseases:
        if disease["id"] == disease_id:
            return disease
    return {
        "id": disease_id,
        "name": "Unknown",
        "symptoms": [],
        "treatment_steps": ["No treatment protocol found for this disease ID. Consult a veterinary officer."],
        "quarantine": {"required": True, "reason": "Unknown disease -- isolate as a precaution until assessed by a professional."},
        "recovery_feed_additions": [],
    }


def list_known_diseases() -> list[dict]:
    """Return a lightweight list of all diseases the system can recognize."""
    return [{"id": d["id"], "name": d["name"]} for d in _load_diseases()]
