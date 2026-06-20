#!/usr/bin/env python3
"""
poultryguard_cli.py

A simple Agents CLI skill for PoultryGuard: run a full diagnosis from the
command line, no server or browser required. Useful for batch-testing
photos, for field agents without reliable internet for a web UI, or for
scripting PoultryGuard into other tools (e.g. a WhatsApp bot backend).

Usage:
    python poultryguard_cli.py path/to/bird_photo.jpg --lat 6.6885 --lon -1.6244 --twi

Run `python poultryguard_cli.py --help` for all options.
"""

import argparse
import json
import sys

from PIL import Image

from backend.agents.orchestrator import PoultryGuardOrchestrator
from backend.security import InvalidImageError, validate_and_load_image


def main() -> int:
    parser = argparse.ArgumentParser(description="PoultryGuard: diagnose a sick bird from a photo.")
    parser.add_argument("image_path", help="Path to a JPEG/PNG/WEBP photo of the bird.")
    parser.add_argument("--lat", type=float, default=6.6885, help="Farmer latitude (default: central Kumasi).")
    parser.add_argument("--lon", type=float, default=-1.6244, help="Farmer longitude (default: central Kumasi).")
    parser.add_argument("--feed-kg", type=float, default=10.0, help="Recovery feed batch size in kg.")
    parser.add_argument("--twi", action="store_true", help="Include Twi translations in the output.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a readable summary.")
    args = parser.parse_args()

    try:
        with open(args.image_path, "rb") as f:
            raw_bytes = f.read()
        image = validate_and_load_image(raw_bytes)
    except (FileNotFoundError, InvalidImageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    orchestrator = PoultryGuardOrchestrator()
    report = orchestrator.run(
        image=image,
        farmer_lat=args.lat,
        farmer_lon=args.lon,
        flock_feed_kg=args.feed_kg,
        include_twi=args.twi,
    ).to_dict()

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"\n=== PoultryGuard Diagnosis ===")
    print(f"Disease: {report['disease_name']} (confidence: {report['confidence'] * 100:.1f}%)")
    print(f"{report['advisory']}\n")

    print("Treatment steps:")
    for i, step in enumerate(report["treatment_steps"], 1):
        print(f"  {i}. {step}")

    print(f"\nQuarantine required: {'YES' if report['quarantine_required'] else 'NO'}")
    print(f"  Reason: {report['quarantine_reason']}")

    print(f"\nRecovery feed formula total cost: GHS {report['feed_formula']['total_cost_ghs']}")

    print("\nNearest agrovets:")
    for shop in report["nearest_agrovets"]:
        print(f"  - {shop['name']} ({shop['area']}) — {shop['distance_km']} km — {shop['phone']}")

    if report.get("twi"):
        print(f"\nTwi: {report['twi']['disease_name_twi']} | {report['twi']['quarantine_twi']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
