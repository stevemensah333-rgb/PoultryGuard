"""
adk_integration.py

This module wires PoultryGuard's tools into Google's Agent Development Kit
(ADK) so the same multi-agent system can run as a proper ADK `LlmAgent` tree
(useful for deployment, tracing, and using Gemini's reasoning to decide
*when* to call each tool, rather than the fixed pipeline order used in
orchestrator.py).

orchestrator.py is the pipeline actually used by the demo app, because it
runs fully offline with zero API keys -- important for a reliable judged
demo. This file shows how the exact same tool functions plug into ADK for
a production deployment where a Gemini-backed root agent can reason about
edge cases (e.g. "the photo shows two different symptoms, should I ask the
farmer a follow-up question before recommending quarantine?") that a fixed
pipeline can't handle.

Requires: pip install google-adk
Requires: GOOGLE_API_KEY (or Vertex AI credentials) set as an environment
variable -- never hardcode this. See README.md "Configuration" section.
"""

import os

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from backend.mcp_server.tools.agrovet_directory import get_nearest_agrovets
from backend.mcp_server.tools.price_lookup import calculate_recovery_feed_formula
from backend.mcp_server.tools.translator import translate_disease_name, translate_quarantine_decision
from backend.mcp_server.tools.treatment_db import get_treatment_protocol, list_known_diseases


def build_poultryguard_adk_agent() -> Agent:
    """
    Build a root ADK agent with PoultryGuard's tools attached. Image
    classification itself stays outside ADK's tool-calling loop (CLIP runs
    locally, synchronously, before the agent is invoked) -- the ADK agent's
    job here is reasoning over the *results* of that classification:
    deciding what to tell the farmer, whether to ask a clarifying question,
    and which tools to call in what order.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Export it as an environment variable "
            "before building the ADK agent (do not hardcode it in source)."
        )

    tools = [
        FunctionTool(get_treatment_protocol),
        FunctionTool(list_known_diseases),
        FunctionTool(calculate_recovery_feed_formula),
        FunctionTool(get_nearest_agrovets),
        FunctionTool(translate_disease_name),
        FunctionTool(translate_quarantine_decision),
    ]

    return Agent(
        name="poultryguard_root_agent",
        model="gemini-2.0-flash",
        instruction=(
            "You are PoultryGuard, an assistant for small-scale poultry farmers in "
            "Ghana. You are given a disease name and confidence score that has "
            "already been determined from a photo by a vision model. Your job is to: "
            "1) explain the disease and its symptoms in plain, non-technical language; "
            "2) give clear treatment steps; 3) calculate a priced recovery feed "
            "formula; 4) recommend nearby agrovets; 5) give a clear quarantine "
            "yes/no decision with a reason. If the confidence score is low, "
            "recommend the farmer get a vet to confirm before treating. Always use "
            "the provided tools to get treatment, pricing, and location data rather "
            "than inventing it yourself."
        ),
        tools=tools,
    )
