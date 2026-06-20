"""
treatment_agent.py, economics_agent.py, locator_agent.py, quarantine_agent.py,
translator_agent.py -- bundled together since each is a thin, single-purpose
wrapper around an MCP tool. Splitting them into separate files would add
boilerplate without adding clarity; each class below is independently
testable and independently swappable.
"""

from backend.mcp_server.tools.agrovet_directory import get_nearest_agrovets
from backend.mcp_server.tools.price_lookup import calculate_recovery_feed_formula
from backend.mcp_server.tools.translator import translate_disease_name, translate_quarantine_decision
from backend.mcp_server.tools.treatment_db import get_treatment_protocol


class TreatmentAgent:
    """Looks up treatment steps and symptoms for a diagnosed disease."""

    name = "treatment_agent"

    def run(self, disease_id: str) -> dict:
        return get_treatment_protocol(disease_id)


class EconomicsAgent:
    """Builds a priced recovery feed formula using local ingredient prices."""

    name = "economics_agent"

    def run(self, total_kg: float = 10.0) -> dict:
        return calculate_recovery_feed_formula(total_kg)


class LocatorAgent:
    """Finds the nearest agrovets to the farmer's location."""

    name = "locator_agent"

    def run(self, lat: float, lon: float, top_n: int = 3) -> list[dict]:
        return get_nearest_agrovets(lat, lon, top_n)


class QuarantineAgent:
    """
    Makes an explicit quarantine recommendation with a stated reason. This is
    kept as its own agent (rather than folded into TreatmentAgent) because
    the decision -- isolate the flock or not -- is high-stakes and benefits
    from being a clearly auditable, separate step in the pipeline.
    """

    name = "quarantine_agent"

    def run(self, treatment_record: dict) -> dict:
        quarantine = treatment_record.get("quarantine", {"required": False, "reason": "Unknown."})
        return {
            "quarantine_required": quarantine["required"],
            "reason": quarantine["reason"],
        }


class TranslatorAgent:
    """Translates the final farmer-facing output into Twi when requested."""

    name = "translator_agent"

    def run(self, disease_name: str, quarantine_required: bool) -> dict:
        return {
            "disease_name_twi": translate_disease_name(disease_name),
            "quarantine_twi": translate_quarantine_decision(quarantine_required),
        }
