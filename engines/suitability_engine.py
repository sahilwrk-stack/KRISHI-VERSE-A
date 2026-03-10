"""
MODULE 1 – Crop Suitability Engine
Calculates how well a chosen crop matches the state's climate and soil profile.
"""
from django.utils.translation import gettext as _
from data.loader import get_crop_requirements, get_state_data


def _score_in_range(value: float, lo: float, hi: float, opt: float) -> float:
    """
    Returns a 0-1 score reflecting how close 'value' is to the [lo, hi] range,
    with peak score at 'opt'. Prevents division-by-zero throughout.
    """
    if lo >= hi:
        return 1.0 if value == opt else max(0.0, 1.0 - abs(value - opt) / max(abs(opt), 1))

    if value < lo:
        deficit = lo - value
        penalty = deficit / max(lo, 1)
        return max(0.0, 1.0 - min(penalty, 1.0))
    elif value > hi:
        excess = value - hi
        penalty = excess / max(hi, 1)
        return max(0.0, 1.0 - min(penalty, 1.0))
    else:
        mid_range = (hi - lo) / 2.0
        if mid_range == 0:
            return 1.0
        dist_from_opt = abs(value - opt)
        return max(0.0, 1.0 - (dist_from_opt / mid_range) * 0.4)


def _soil_type_score(actual_soil: str, ideal_soils: list) -> float:
    """Fuzzy match soil type: exact match = 1.0, partial overlap = 0.65, no match = 0.3."""
    actual = actual_soil.lower().strip()
    for s in ideal_soils:
        if s.lower() == actual:
            return 1.0
    for s in ideal_soils:
        if s.lower() in actual or actual in s.lower():
            return 0.65
    return 0.3


def _ph_score(actual_ph: float, min_ph: float, max_ph: float) -> float:
    """Score soil pH match. ±0.5 unit outside range is acceptable."""
    if min_ph <= actual_ph <= max_ph:
        return 1.0
    if actual_ph < min_ph:
        gap = min_ph - actual_ph
    else:
        gap = actual_ph - max_ph
    return max(0.0, 1.0 - gap / 2.0)


def _nitrogen_score(level: str) -> float:
    mapping = {"low": 0.45, "medium": 0.78, "high": 1.0}
    return mapping.get(level.lower(), 0.5)


def calculate(state: str, crop: str, soil_type: str, irrigation: str) -> dict:
    """
    Returns a suitability assessment dict with individual scores and
    a suitability_level classification.
    """
    req = get_crop_requirements(crop)
    st = get_state_data(state)

    # ── Climate scores ────────────────────────────────────────────────────────
    rainfall_score = _score_in_range(
        st["avg_rainfall"],
        req["min_rainfall"], req["max_rainfall"], req["optimal_rainfall"],
    )
    temp_score = _score_in_range(
        st["avg_temp"],
        req["min_temp"], req["max_temp"], req["optimal_temp"],
    )
    humidity_score = _score_in_range(
        st["avg_humidity"],
        req["min_humidity"], req["max_humidity"], req["optimal_humidity"],
    )

    # Irrigation adjustment: if irrigation unavailable and crop needs high water, penalise
    irrigation_ok = irrigation.lower() in ("yes", "available", "true", "1")
    water_req = req.get("water_req", "medium")
    if not irrigation_ok and water_req == "high":
        rainfall_score *= 0.75
    elif not irrigation_ok and water_req == "medium":
        rainfall_score *= 0.90

    climate_score = (rainfall_score * 0.40 + temp_score * 0.35 + humidity_score * 0.25)

    # ── Soil scores ───────────────────────────────────────────────────────────
    ph_sc = _ph_score(st["soil_ph"], req["min_ph"], req["max_ph"])
    type_sc = _soil_type_score(soil_type or st["soil_type"], req["ideal_soils"])
    nitro_sc = _nitrogen_score(st.get("nitrogen", "medium"))
    soil_score = ph_sc * 0.40 + type_sc * 0.40 + nitro_sc * 0.20

    # ── Final weighted score ──────────────────────────────────────────────────
    final_score = climate_score * 0.60 + soil_score * 0.40
    final_score = max(0.0, min(1.0, final_score))

    if final_score > 0.75:
        level = _("Suitable")
        color = "success"
    elif final_score >= 0.50:
        level = _("Moderate Risk")
        color = "warning"
    else:
        level = _("Not Recommended")
        color = "danger"

    return {
        "suitability_score": round(final_score, 4),
        "suitability_pct": round(final_score * 100, 1),
        "suitability_level": level,
        "suitability_color": color,
        "climate_score": round(climate_score, 4),
        "climate_pct": round(climate_score * 100, 1),
        "soil_score": round(soil_score, 4),
        "soil_pct": round(soil_score * 100, 1),
        "rainfall_score": round(rainfall_score, 4),
        "rainfall_pct": round(rainfall_score * 100, 1),
        "temp_score": round(temp_score, 4),
        "temp_pct": round(temp_score * 100, 1),
        "humidity_score": round(humidity_score, 4),
        "humidity_pct": round(humidity_score * 100, 1),
        "ph_score": round(ph_sc, 4),
        "ph_pct": round(ph_sc * 100, 1),
        "soil_type_score": round(type_sc, 4),
        "state_rainfall": st["avg_rainfall"],
        "crop_min_rainfall": req["min_rainfall"],
        "crop_max_rainfall": req["max_rainfall"],
        "state_temp": st["avg_temp"],
        "crop_min_temp": req["min_temp"],
        "crop_max_temp": req["max_temp"],
        "state_humidity": st["avg_humidity"],
        "crop_min_humidity": req["min_humidity"],
        "crop_max_humidity": req["max_humidity"],
        "state_ph": st["soil_ph"],
        "crop_min_ph": req["min_ph"],
        "crop_max_ph": req["max_ph"],
        "irrigation_ok": irrigation_ok,
        "water_req": water_req,
    }
