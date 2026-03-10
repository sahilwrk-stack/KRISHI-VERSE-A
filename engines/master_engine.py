"""
Master Engine – Orchestrates all 10 modules and returns the full analysis dict.
"""
from engines import (
    suitability_engine,
    financial_engine,
    risk_engine,
    projection_engine,
    diagnosis_engine,
    solution_engine,
    government_engine,
    emotion_engine,
)
from data.loader import get_climate_history, get_state_data, get_crop_requirements
from data.extended_data import STATE_DATA, CROP_REQUIREMENTS, ALL_STATES


def _all_states_suitability(crop: str, soil_type: str, irrigation: str) -> dict:
    """Calculate quick suitability score for all states for choropleth map."""
    scores: dict = {}
    for st in ALL_STATES:
        try:
            result = suitability_engine.calculate(st, crop, soil_type, irrigation)
            scores[st] = round(result["suitability_score"] * 100, 1)
        except Exception:
            scores[st] = 0.0
    return scores


def run(
    state: str,
    crop: str,
    land_size_acres: float,
    soil_type: str,
    irrigation: str,
    investment_capacity: float,
) -> dict:
    """
    Execute all analysis modules and return a consolidated result dictionary.
    Defensively handles any module failure to prevent total analysis failure.
    """
    errors: list = []

    # ── Module 1: Suitability ─────────────────────────────────────────────────
    try:
        suitability = suitability_engine.calculate(state, crop, soil_type, irrigation)
    except Exception as e:
        errors.append(f"Suitability: {e}")
        suitability = {"suitability_score": 0.5, "suitability_level": "Unknown",
                       "suitability_pct": 50, "suitability_color": "secondary",
                       "climate_score": 0.5, "climate_pct": 50,
                       "soil_score": 0.5, "soil_pct": 50,
                       "rainfall_score": 0.5, "rainfall_pct": 50,
                       "temp_score": 0.5, "temp_pct": 50,
                       "humidity_score": 0.5, "humidity_pct": 50,
                       "ph_score": 0.5, "ph_pct": 50,
                       "soil_type_score": 0.5,
                       "state_rainfall": 800, "crop_min_rainfall": 500, "crop_max_rainfall": 1200,
                       "state_temp": 25, "crop_min_temp": 15, "crop_max_temp": 35,
                       "state_humidity": 60, "crop_min_humidity": 50, "crop_max_humidity": 80,
                       "state_ph": 7.0, "crop_min_ph": 6.0, "crop_max_ph": 7.5,
                       "irrigation_ok": True, "water_req": "medium"}

    # ── Module 2: Financial ───────────────────────────────────────────────────
    try:
        financial = financial_engine.calculate(crop, state, land_size_acres, investment_capacity)
    except Exception as e:
        errors.append(f"Financial: {e}")
        financial = {"investment_needed": 0, "investment_capacity": investment_capacity,
                     "investment_ratio_pct": 100, "total_yield_q": 0,
                     "expected_revenue": 0, "govt_support": 0, "net_profit": 0,
                     "roi": 0, "land_ha": land_size_acres * 0.4047, "land_acres": land_size_acres,
                     "effective_price": 0, "msp": 0, "market_price": 0,
                     "cost_per_ha": 0, "profit_per_acre": 0, "break_even_price": 0,
                     "subsidy_detail": {}}

    # ── Module 3: Risk ────────────────────────────────────────────────────────
    try:
        risk = risk_engine.calculate(crop, state, suitability, financial)
    except Exception as e:
        errors.append(f"Risk: {e}")
        risk = {"failure_probability": 0.3, "failure_probability_pct": 30,
                "risk_level": "Moderate", "risk_color": "warning",
                "insurance_coverage_pct": 75, "insurance_premium_total": 0,
                "insurance_payout": 0, "final_loss_after_insurance": 0,
                "net_loss_worst_case": 0, "yield_loss_value": 0, "gross_exposure": 0}

    # ── Module 4: Projection ──────────────────────────────────────────────────
    try:
        projection = projection_engine.calculate(crop, state, financial, suitability)
    except Exception as e:
        errors.append(f"Projection: {e}")
        projection = {"yearly_profits": [0] * 5, "cumulative_3yr": 0, "cumulative_5yr": 0,
                      "avg_annual_3yr": 0, "avg_annual_5yr": 0, "volatility_index": 10,
                      "income_stability_score": 50, "rainfall_stability": 70,
                      "growth_rate_pct": 3, "loss_3yr_if_unsuitable": 0,
                      "loss_5yr_if_unsuitable": 0, "years": [2025, 2026, 2027, 2028, 2029]}

    # ── Module 5: Diagnosis ───────────────────────────────────────────────────
    try:
        diagnosis = diagnosis_engine.diagnose(state, crop, suitability)
    except Exception as e:
        errors.append(f"Diagnosis: {e}")
        diagnosis = {"failure_reasons": [], "problem_keys": ["general"],
                     "has_issues": False, "critical_count": 0, "moderate_count": 0}

    # ── Modules 6 & 7: Solutions ──────────────────────────────────────────────
    try:
        solutions = solution_engine.recommend(
            diagnosis.get("problem_keys", ["general"]), financial, land_size_acres
        )
    except Exception as e:
        errors.append(f"Solutions: {e}")
        solutions = {"modern_solutions": [], "traditional_solutions": [],
                     "best_modern": None, "best_traditional": None, "new_stability_score": None}

    # ── Module 8: Government ──────────────────────────────────────────────────
    try:
        government = government_engine.calculate(crop, state, land_size_acres)
    except Exception as e:
        errors.append(f"Government: {e}")
        government = {"msp_per_quintal": 0, "has_msp": False, "total_subsidy": 0,
                      "insurance_coverage_pct": 75, "insurance_premium": 0,
                      "max_insurance_payout": 0, "schemes": [],
                      "fertilizer_subsidy": 0, "seed_subsidy": 0,
                      "irrigation_subsidy": 0, "pm_kisan": 6000}

    # ── Module 9: Emotion ─────────────────────────────────────────────────────
    try:
        emotion = emotion_engine.classify(financial, suitability, risk, projection)
    except Exception as e:
        errors.append(f"Emotion: {e}")
        emotion = {"farmer_emotion": "Satisfied", "emoji": "😐", "color": "warning",
                   "badge": "bg-warning", "message": "Analysis incomplete.",
                   "recommendation": "Review individual modules.", "composite_score": 50}

    # ── Climate history for charts ────────────────────────────────────────────
    try:
        climate_history = get_climate_history(state)
    except Exception:
        climate_history = {"years": [2019, 2020, 2021, 2022, 2023],
                           "rainfall": [800] * 5, "temps": [25] * 5}

    # ── All-states suitability for choropleth map ─────────────────────────────
    try:
        map_scores = _all_states_suitability(crop, soil_type, irrigation)
    except Exception:
        map_scores = {}

    # ── Radar chart data (actual vs crop requirement) ─────────────────────────
    req = get_crop_requirements(crop)
    st_data = get_state_data(state)
    radar = {
        "labels": ["Rainfall", "Temperature", "Humidity", "Soil pH", "Soil Type"],
        "actual": [
            round(suitability["rainfall_pct"], 1),
            round(suitability["temp_pct"], 1),
            round(suitability["humidity_pct"], 1),
            round(suitability["ph_pct"], 1),
            round(suitability.get("soil_type_score", 0.5) * 100, 1),
        ],
    }

    return {
        "input": {
            "state": state, "crop": crop,
            "land_size_acres": land_size_acres,
            "soil_type": soil_type, "irrigation": irrigation,
            "investment_capacity": investment_capacity,
        },
        "suitability": suitability,
        "financial": financial,
        "risk": risk,
        "projection": projection,
        "diagnosis": diagnosis,
        "solutions": solutions,
        "government": government,
        "emotion": emotion,
        "climate_history": climate_history,
        "map_scores": map_scores,
        "radar": radar,
        "errors": errors,
        "crop_req": req,
        "state_info": st_data,
    }
