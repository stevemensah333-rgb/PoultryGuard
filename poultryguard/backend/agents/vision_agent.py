"""
vision_agent.py

Agent responsible for one job: look at the photo, return a disease
hypothesis with a confidence score. Keeping this agent narrow (single
responsibility) makes it easy to test and swap out independently of the
rest of the pipeline -- e.g. replacing CLIP with a fine-tuned model later
requires no changes anywhere else in the system.
"""

from PIL import Image

from backend.models.vision_model import ClassificationResult, get_classifier


class VisionAgent:
    name = "vision_agent"

    def run(self, image: Image.Image) -> ClassificationResult:
        classifier = get_classifier()
        return classifier.classify(image)
