"""
Data loader: merges CSV files with the extended Python data dictionaries.
CSV data takes precedence where available; extended_data fills all other gaps.
Uses __file__-based path resolution — no Django settings dependency.
"""
import os
from pathlib import Path
import pandas as pd
from data.extended_data import (
    CROP_REQUIREMENTS, STATE_DATA, STATE_CROP_COST_YIELD,
    MARKET_PRICES, SUBSIDIES, MODERN_SOLUTIONS, TRADITIONAL_SOLUTIONS,
    CROP_GROWTH_FACTORS, ALL_CROPS, ALL_STATES, SOIL_TYPES,
)

# Project root = two levels up from this file (FAM/data/loader.py → FAM/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# CSV loaders (lazy-loaded & cached)
# ─────────────────────────────────────────────────────────────────────────────
_cache: dict = {}


def _load_csv(filename: str) -> pd.DataFrame:
    if filename not in _cache:
        path = _PROJECT_ROOT / filename
        try:
            _cache[filename] = pd.read_csv(path)
        except Exception:
            _cache[filename] = pd.DataFrame()
    return _cache[filename]


# ─────────────────────────────────────────────────────────────────────────────
# CROP REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────
def get_crop_requirements(crop: str) -> dict:
    """Return agronomic requirements for a crop."""
    crop_title = crop.strip().title()
    return CROP_REQUIREMENTS.get(crop_title, CROP_REQUIREMENTS.get("Wheat"))


# ─────────────────────────────────────────────────────────────────────────────
# STATE CLIMATE DATA
# ─────────────────────────────────────────────────────────────────────────────
def get_state_data(state: str) -> dict:
    """Return climate and soil data for a state."""
    state_title = state.strip().title()
    return STATE_DATA.get(state_title, list(STATE_DATA.values())[0])


# ─────────────────────────────────────────────────────────────────────────────
# COST & YIELD
# ─────────────────────────────────────────────────────────────────────────────
def get_cost_and_yield(crop: str, state: str) -> dict:
    """Return per-hectare cost and yield for crop-state combination."""
    key = (crop.strip().title(), state.strip().title())
    if key in STATE_CROP_COST_YIELD:
        return STATE_CROP_COST_YIELD[key]

    # Fall back to CSV data
    df = _load_csv("cleaned_cost_of_cultivation.csv")
    if not df.empty:
        row = df[
            (df["crop"].str.lower() == crop.lower()) &
            (df["state"].str.lower() == state.lower())
        ]
        if not row.empty:
            cost = float(row.iloc[0]["total_cost_per_hectare"])
            req = get_crop_requirements(crop)
            return {"cost_ha": cost, "yield_q_ha": req["national_avg_yield_q_ha"]}

    req = get_crop_requirements(crop)
    return {
        "cost_ha": req["national_avg_cost_ha"],
        "yield_q_ha": req["national_avg_yield_q_ha"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# MARKET PRICE
# ─────────────────────────────────────────────────────────────────────────────
def get_market_price(crop: str, state: str) -> float:
    """Return market price per quintal for crop in state."""
    key = (crop.strip().title(), state.strip().title())
    if key in MARKET_PRICES:
        return float(MARKET_PRICES[key])

    df = _load_csv("cleaned_market_price.csv")
    if not df.empty:
        row = df[
            (df["crop"].str.lower() == crop.lower()) &
            (df["state"].str.lower() == state.lower())
        ]
        if not row.empty:
            return float(row.iloc[0]["market_price_per_quintal"])

    req = get_crop_requirements(crop)
    return float(req["national_avg_price_q"])


# ─────────────────────────────────────────────────────────────────────────────
# MSP
# ─────────────────────────────────────────────────────────────────────────────
def get_msp(crop: str) -> float:
    """Return MSP per quintal for a crop."""
    req = get_crop_requirements(crop)
    msp = req.get("msp_q", 0)
    if msp:
        return float(msp)

    df = _load_csv("cleaned_msp_data.csv")
    if not df.empty:
        row = df[df["crop"].str.lower() == crop.lower()]
        if not row.empty:
            return float(row.iloc[0]["msp_per_quintal"])
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# SUBSIDIES
# ─────────────────────────────────────────────────────────────────────────────
def get_subsidies(crop: str) -> dict:
    """Return government subsidy data for a crop."""
    crop_title = crop.strip().title()
    return SUBSIDIES.get(crop_title, SUBSIDIES.get("Wheat"))


# ─────────────────────────────────────────────────────────────────────────────
# INSURANCE
# ─────────────────────────────────────────────────────────────────────────────
def get_insurance(crop: str) -> dict:
    """Return crop insurance coverage % and premium per hectare."""
    req = get_crop_requirements(crop)
    return {
        "coverage_pct": req.get("insurance_pct", 75),
        "premium_ha": req.get("insurance_premium_ha", 1200),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLIMATE HISTORY
# ─────────────────────────────────────────────────────────────────────────────
def get_climate_history(state: str) -> dict:
    """Return 5-year rainfall and temperature history for a state."""
    state_title = state.strip().title()
    data = STATE_DATA.get(state_title, {})
    years = list(range(2019, 2024))

    # Try to enrich from CSV
    df = _load_csv("cleaned_state_climate_history.csv")
    rainfall = data.get("rainfall_history", [data.get("avg_rainfall", 800)] * 5)
    temps = data.get("temp_history", [data.get("avg_temp", 25)] * 5)

    if not df.empty:
        csv_rows = df[df["state"].str.lower() == state.lower()].sort_values("year")
        if not csv_rows.empty:
            years = csv_rows["year"].tolist()
            rainfall = csv_rows["rainfall_mm"].tolist()
            temps = csv_rows["temperature_c"].tolist()

    return {"years": years, "rainfall": rainfall, "temps": temps}


# ─────────────────────────────────────────────────────────────────────────────
# SOLUTIONS
# ─────────────────────────────────────────────────────────────────────────────
def get_modern_solution(problem_key: str) -> dict:
    """Return modern solution for a problem type."""
    key = problem_key.lower().strip()
    return MODERN_SOLUTIONS.get(key, MODERN_SOLUTIONS["general"])


def get_traditional_solution(problem_key: str) -> dict:
    """Return traditional solution for a problem type."""
    key = problem_key.lower().strip()
    return TRADITIONAL_SOLUTIONS.get(key, TRADITIONAL_SOLUTIONS["general"])


# ─────────────────────────────────────────────────────────────────────────────
# GROWTH FACTORS
# ─────────────────────────────────────────────────────────────────────────────
def get_growth_factors(crop: str) -> dict:
    """Return price/yield growth and volatility factors for a crop."""
    crop_title = crop.strip().title()
    return CROP_GROWTH_FACTORS.get(crop_title, {"price_growth": 0.04, "yield_growth": 0.02, "volatility": 0.12})


# ─────────────────────────────────────────────────────────────────────────────
# DROPDOWN DATA FOR FORMS
# ─────────────────────────────────────────────────────────────────────────────
def get_all_crops():
    return ALL_CROPS


def get_all_states():
    return ALL_STATES


def get_all_soil_types():
    return SOIL_TYPES


def get_soil_types_for_state(state: str) -> list:
    """Return only the soil types that exist in the given state."""
    state_title = state.strip().title()
    data = STATE_DATA.get(state_title, {})
    types = data.get("soil_types", [])
    return types if types else SOIL_TYPES


def get_crops_for_state(state: str) -> list:
    """
    Return crops (from CROP_REQUIREMENTS) that are available in the given state.
    Uses STATE_AVAILABLE_ITEMS (vegetable_data) intersected with known farm crops.
    Falls back to STATE_DATA major_crops, then all crops.
    """
    from data.vegetable_data import STATE_AVAILABLE_ITEMS
    from data.extended_data import CROP_REQUIREMENTS

    state_title = state.strip().title()
    all_farm_crops = set(CROP_REQUIREMENTS.keys())

    # Get state-specific available items (crops + vegetables)
    state_items = STATE_AVAILABLE_ITEMS.get(state_title, [])
    if state_items:
        # Keep only items that the farm analysis engine knows about
        filtered = [c for c in state_items if c in all_farm_crops]
        if filtered:
            return sorted(filtered)

    # Fallback: use major_crops from STATE_DATA
    state_data = STATE_DATA.get(state_title, {})
    major = [c for c in state_data.get("major_crops", []) if c in all_farm_crops]
    if major:
        return sorted(major)

    # Last resort: all farm crops
    return sorted(all_farm_crops)
