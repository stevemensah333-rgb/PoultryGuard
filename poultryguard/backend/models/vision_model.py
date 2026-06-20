"""
vision_model.py

Zero-shot poultry disease classifier using CLIP (openai/clip-vit-base-patch32).

Why zero-shot CLIP instead of a fine-tuned classifier?
  - No labeled training dataset is required to get a working demo today.
  - It is easy to swap in a fine-tuned model later (e.g. a ResNet/ViT trained on
    real labeled poultry disease photos) without changing the agent interface --
    just replace the `classify` method's internals and keep the same return shape.

AMD GPU (ROCm) note:
  When PyTorch is installed with a ROCm build (see README.md), AMD GPUs are
  exposed through the standard `torch.cuda` API. That means no special code is
  needed here -- `torch.cuda.is_available()` and `.to("cuda")` work the same way
  they would on an NVIDIA box. This module simply picks the best available
  device (ROCm/CUDA GPU > CPU).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DISEASES_PATH = os.path.join(DATA_DIR, "diseases.json")
MODEL_NAME = "openai/clip-vit-base-patch32"


@dataclass
class ClassificationResult:
    disease_id: str
    disease_name: str
    confidence: float
    all_scores: dict


class PoultryVisionClassifier:
    """Zero-shot CLIP classifier over poultry disease label prompts."""

    def __init__(self, model_name: str = MODEL_NAME, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[vision_model] Loading {model_name} on device: {self.device}")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)

        with open(DISEASES_PATH, "r", encoding="utf-8") as f:
            self._diseases = json.load(f)["diseases"]

        # Flatten (disease_id -> list of prompt strings) for CLIP text encoding
        self._prompts: List[str] = []
        self._prompt_to_disease: List[str] = []
        for disease in self._diseases:
            for label in disease["clip_labels"]:
                self._prompts.append(label)
                self._prompt_to_disease.append(disease["id"])

    def classify(self, image: Image.Image) -> ClassificationResult:
        inputs = self.processor(
            text=self._prompts, images=image, return_tensors="pt", padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image  # shape: [1, num_prompts]
            probs = logits_per_image.softmax(dim=1).squeeze(0).cpu().tolist()

        # Aggregate prompt-level scores back up to disease-level scores (max over prompts)
        disease_scores: dict[str, float] = {}
        for prompt_idx, score in enumerate(probs):
            disease_id = self._prompt_to_disease[prompt_idx]
            disease_scores[disease_id] = max(disease_scores.get(disease_id, 0.0), score)

        best_disease_id = max(disease_scores, key=disease_scores.get)
        best_score = disease_scores[best_disease_id]
        disease_name = next(
            d["name"] for d in self._diseases if d["id"] == best_disease_id
        )

        return ClassificationResult(
            disease_id=best_disease_id,
            disease_name=disease_name,
            confidence=round(best_score, 4),
            all_scores={k: round(v, 4) for k, v in disease_scores.items()},
        )


# Simple singleton accessor so the model loads once per process
_classifier_instance: PoultryVisionClassifier | None = None


def get_classifier() -> PoultryVisionClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = PoultryVisionClassifier()
    return _classifier_instance
