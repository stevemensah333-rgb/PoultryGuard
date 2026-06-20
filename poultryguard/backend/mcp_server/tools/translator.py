"""
translator.py

MCP tool for translating known UI strings and disease names into Twi using a
placeholder phrase dictionary. For free-form text that isn't in the
dictionary, this falls back to returning the original English text rather
than guessing -- mistranslating medical guidance is worse than not
translating it. A production version should integrate a reviewed
English<->Twi machine translation model or professional translator workflow.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "twi_translations.json")


def _load_translations() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def translate_disease_name(disease_name: str) -> str:
    translations = _load_translations()
    return translations["disease_names"].get(disease_name, disease_name)


def translate_ui_string(key: str) -> str:
    translations = _load_translations()
    return translations["ui"].get(key, key)


def translate_quarantine_decision(required: bool) -> str:
    translations = _load_translations()
    return translations["quarantine_yes"] if required else translations["quarantine_no"]
