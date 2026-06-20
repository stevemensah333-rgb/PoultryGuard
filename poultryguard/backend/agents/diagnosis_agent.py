"""
diagnosis_agent.py

Agent responsible for turning a raw vision classification into a
farmer-facing diagnosis decision, including a confidence policy: if the
model isn't confident enough, this agent decides to recommend a vet visit
rather than asserting a specific disease. This is a basic safety guardrail
-- low-confidence model output should never be presented to a farmer as
a confident medical diagnosis.
"""

from dataclasses import dataclass

from backend.models.vision_model import ClassificationResult

LOW_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class Diagnosis:
    disease_id: str
    disease_name: str
    confidence: float
    is_confident: bool
    advisory: str


class DiagnosisAgent:
    name = "diagnosis_agent"

    def run(self, classification: ClassificationResult) -> Diagnosis:
        is_confident = classification.confidence >= LOW_CONFIDENCE_THRESHOLD

        if is_confident:
            advisory = (
                f"The image most closely matches {classification.disease_name} "
                f"with {classification.confidence * 100:.1f}% confidence."
            )
        else:
            advisory = (
                "The image doesn't clearly match a known pattern with high confidence "
                f"(best guess: {classification.disease_name} at {classification.confidence * 100:.1f}%). "
                "We recommend showing this photo to a local veterinary officer or "
                "agricultural extension agent for a confirmed diagnosis."
            )

        return Diagnosis(
            disease_id=classification.disease_id,
            disease_name=classification.disease_name,
            confidence=classification.confidence,
            is_confident=is_confident,
            advisory=advisory,
        )
