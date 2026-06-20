"""
server.py

PoultryGuard MCP Server.

Exposes the farmer-support tools (agrovet lookup, feed pricing, treatment
protocols, Twi translation) over the Model Context Protocol so that any
MCP-compatible agent or client (including the agents in backend/agents/)
can call them as standard tools rather than importing Python functions
directly. This is what lets the same tool surface be reused by a different
agent framework, a CLI, or a separate orchestrator without rewriting logic.

Run standalone with:
    python -m backend.mcp_server.server
"""

from mcp.server.fastmcp import FastMCP

from backend.mcp_server.tools.agrovet_directory import get_nearest_agrovets
from backend.mcp_server.tools.price_lookup import calculate_recovery_feed_formula
from backend.mcp_server.tools.treatment_db import get_treatment_protocol, list_known_diseases
from backend.mcp_server.tools.translator import (
    translate_disease_name,
    translate_quarantine_decision,
    translate_ui_string,
)

mcp = FastMCP("poultryguard")


@mcp.tool()
def find_nearest_agrovets(lat: float, lon: float, top_n: int = 3) -> list[dict]:
    """Find the nearest agrovets to a farmer's GPS location, with distance and directions."""
    return get_nearest_agrovets(lat, lon, top_n)


@mcp.tool()
def recovery_feed_formula(total_kg: float = 10.0) -> dict:
    """Calculate a priced recovery feed formula for a given total weight in kg, using local prices."""
    return calculate_recovery_feed_formula(total_kg)


@mcp.tool()
def treatment_protocol(disease_id: str) -> dict:
    """Get symptoms, treatment steps, and quarantine guidance for a disease ID."""
    return get_treatment_protocol(disease_id)


@mcp.tool()
def known_diseases() -> list[dict]:
    """List all diseases this system can currently recognize."""
    return list_known_diseases()


@mcp.tool()
def translate_to_twi(disease_name: str | None = None, ui_key: str | None = None, quarantine_required: bool | None = None) -> dict:
    """Translate a disease name, a UI string key, or a quarantine decision into Twi."""
    result = {}
    if disease_name is not None:
        result["disease_name_twi"] = translate_disease_name(disease_name)
    if ui_key is not None:
        result["ui_string_twi"] = translate_ui_string(ui_key)
    if quarantine_required is not None:
        result["quarantine_twi"] = translate_quarantine_decision(quarantine_required)
    return result


if __name__ == "__main__":
    mcp.run()
