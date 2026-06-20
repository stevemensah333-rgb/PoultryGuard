"""
orchestrator.py

The Orchestrator coordinates the full PoultryGuard pipeline:

    photo --> VisionAgent --> DiagnosisAgent --> TreatmentAgent
                                              --> EconomicsAgent
                                              --> LocatorAgent
                                              --> QuarantineAgent
                                              --> TranslatorAgent (if requested)
                                              --> final structured report

This mirrors the multi-agent coordination pattern used in Google's ADK: a
top-level agent delegates each sub-task to a specialized agent and merges
their outputs into one coherent result, rather than one monolithic prompt
trying to do everything at once. See `adk_integration.py` in this folder for
notes on wiring this same set of agents into the actual google-adk SDK.

No API keys are required to run this pipeline -- the vision model is a
local CLIP model and every other agent calls local tools/data.
"""

from dataclasses import asdict, dataclass

from PIL import Image

from backend.agents.diagnosis_agent import DiagnosisAgent
from backend.agents.support_agents import (
    EconomicsAgent,
    LocatorAgent,
    QuarantineAgent,
    TranslatorAgent,
    TreatmentAgent,
)
from backend.agents.vision_agent import VisionAgent

# Default location: central Kumasi. In the real app this comes from the
# farmer's device GPS or a manually entered location.
DEFAULT_LAT = 6.6885
DEFAULT_LON = -1.6244


@dataclass
class PoultryGuardReport:
    disease_name: str
    confidence: float
    is_confident: bool
    advisory: str
    symptoms: list
    treatment_steps: list
    quarantine_required: bool
    quarantine_reason: str
    feed_formula: dict
    nearest_agrovets: list
    twi: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class PoultryGuardOrchestrator:
    def __init__(self) -> None:
        self.vision_agent = VisionAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.treatment_agent = TreatmentAgent()
        self.economics_agent = EconomicsAgent()
        self.locator_agent = LocatorAgent()
        self.quarantine_agent = QuarantineAgent()
        self.translator_agent = TranslatorAgent()

    def run(
        self,
        image: Image.Image,
        farmer_lat: float = DEFAULT_LAT,
        farmer_lon: float = DEFAULT_LON,
        flock_feed_kg: float = 10.0,
        include_twi: bool = False,
    ) -> PoultryGuardReport:
        classification = self.vision_agent.run(image)
        diagnosis = self.diagnosis_agent.run(classification)
        treatment_record = self.treatment_agent.run(diagnosis.disease_id)
        feed_formula = self.economics_agent.run(flock_feed_kg)
        nearest_agrovets = self.locator_agent.run(farmer_lat, farmer_lon)
        quarantine = self.quarantine_agent.run(treatment_record)

        twi = None
        if include_twi:
            twi = self.translator_agent.run(
                diagnosis.disease_name, quarantine["quarantine_required"]
            )

        return PoultryGuardReport(
            disease_name=diagnosis.disease_name,
            confidence=diagnosis.confidence,
            is_confident=diagnosis.is_confident,
            advisory=diagnosis.advisory,
            symptoms=treatment_record.get("symptoms", []),
            treatment_steps=treatment_record.get("treatment_steps", []),
            quarantine_required=quarantine["quarantine_required"],
            quarantine_reason=quarantine["reason"],
            feed_formula=feed_formula,
            nearest_agrovets=nearest_agrovets,
            twi=twi,
        )
