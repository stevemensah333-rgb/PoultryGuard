"""
price_lookup.py

MCP tool for calculating the cost of a recovery feed formula using current
local ingredient prices. Uses placeholder Kumasi prices; swap in a live
market-price feed for production use.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "feed_prices_kumasi.json")

# A simple, illustrative recovery mash recipe by weight ratio.
# Real formulations should come from a poultry nutritionist and vary by
# flock size, age, and the specific disease's nutritional needs.
BASE_RECIPE_RATIOS = {
    "maize_bran": 0.45,
    "soybean_meal": 0.25,
    "wheat_bran": 0.15,
    "fish_meal": 0.08,
    "limestone": 0.03,
    "salt": 0.01,
    "premix_vitamin": 0.02,
    "electrolyte_vitamin_powder": 0.01,
}


def get_feed_prices() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_recovery_feed_formula(total_kg: float = 10.0) -> dict:
    """
    Build a recovery feed formula for `total_kg` of feed and price it out
    using current local ingredient prices.
    """
    prices = get_feed_prices()["ingredients_per_kg"]

    line_items = []
    total_cost = 0.0
    for ingredient, ratio in BASE_RECIPE_RATIOS.items():
        kg = round(total_kg * ratio, 2)
        unit_price = prices.get(ingredient, 0.0)
        cost = round(kg * unit_price, 2)
        total_cost += cost
        line_items.append(
            {
                "ingredient": ingredient,
                "kg": kg,
                "unit_price_ghs": unit_price,
                "line_cost_ghs": cost,
            }
        )

    return {
        "total_kg": total_kg,
        "currency": "GHS",
        "line_items": line_items,
        "total_cost_ghs": round(total_cost, 2),
    }
