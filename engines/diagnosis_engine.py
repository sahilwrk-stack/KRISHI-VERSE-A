"""
MODULE 5 – Failure Diagnosis Engine
Rule-based comparison of actual vs required conditions to identify root causes.
"""
from django.utils.translation import gettext as _
from data.loader import get_crop_requirements, get_state_data


# Maps each diagnosis key to a problem_type used by the solution engine
DIAGNOSIS_PROBLEM_MAP = {
    "Low Rainfall":            "low rainfall",
    "Excess Rainfall":         "excess rainfall",
    "High Temperature":        "high temperature",
    "Low Temperature":         "low temperature",
    "High Humidity":           "high humidity",
    "Low Humidity":            "low rainfall",
    "Soil pH Too High":        "soil ph mismatch",
    "Soil pH Too Low":         "soil ph mismatch",
    "Poor Soil Nutrients":     "poor soil nutrients",
    "Soil Type Mismatch":      "soil type mismatch",
    "Insufficient Irrigation": "low rainfall",
}


def _pct_diff(actual: float, target: float) -> float:
    if target == 0:
        return 0.0
    return abs(actual - target) / target * 100


def _severity(key: str):
    """Return (translated_label, english_key) for a severity level."""
    return _("Critical") if key == "Critical" else _("Moderate") if key == "Moderate" else _("None"), key


def diagnose(state: str, crop: str, suitability: dict) -> dict:
    """
    Returns a list of reason dicts, each containing the reason, severity, and
    a problem_key used to look up solutions.
    """
    req = get_crop_requirements(crop)
    st = get_state_data(state)
    reasons: list = []

    # ── Rainfall ─────────────────────────────────────────────────────────────
    actual_rf = st["avg_rainfall"]
    if actual_rf < req["min_rainfall"]:
        deficit_pct = _pct_diff(actual_rf, req["min_rainfall"])
        sev_key = "Critical" if deficit_pct > 40 else "Moderate"
        reasons.append({
            "reason": _("Low Rainfall"),
            "detail": _(
                "State rainfall (%(actual)s mm) is below crop minimum "
                "(%(minimum)s mm). Deficit: %(deficit)s%%."
            ) % {"actual": actual_rf, "minimum": req['min_rainfall'], "deficit": f"{deficit_pct:.0f}"},
            "severity": _(sev_key),
            "severity_key": sev_key,
            "severity_color": "danger" if sev_key == "Critical" else "warning",
            "problem_key": "low rainfall",
            "icon": "cloud-rain",
        })
    elif actual_rf > req["max_rainfall"]:
        excess_pct = _pct_diff(actual_rf, req["max_rainfall"])
        sev_key = "Critical" if excess_pct > 40 else "Moderate"
        reasons.append({
            "reason": _("Excess Rainfall"),
            "detail": _(
                "State rainfall (%(actual)s mm) exceeds crop maximum "
                "(%(maximum)s mm). Excess: %(excess)s%%."
            ) % {"actual": actual_rf, "maximum": req['max_rainfall'], "excess": f"{excess_pct:.0f}"},
            "severity": _(sev_key),
            "severity_key": sev_key,
            "severity_color": "danger" if sev_key == "Critical" else "warning",
            "problem_key": "excess rainfall",
            "icon": "cloud-drizzle",
        })

    # ── Temperature ───────────────────────────────────────────────────────────
    actual_t = st["avg_temp"]
    if actual_t > req["max_temp"]:
        diff = actual_t - req["max_temp"]
        sev_key = "Critical" if diff > 5 else "Moderate"
        reasons.append({
            "reason": _("High Temperature"),
            "detail": _(
                "Average temperature (%(actual)s°C) exceeds crop maximum "
                "(%(maximum)s°C) by %(diff)s°C."
            ) % {"actual": actual_t, "maximum": req['max_temp'], "diff": f"{diff:.1f}"},
            "severity": _(sev_key),
            "severity_key": sev_key,
            "severity_color": "danger" if sev_key == "Critical" else "warning",
            "problem_key": "high temperature",
            "icon": "thermometer-high",
        })
    elif actual_t < req["min_temp"]:
        diff = req["min_temp"] - actual_t
        sev_key = "Critical" if diff > 5 else "Moderate"
        reasons.append({
            "reason": _("Low Temperature"),
            "detail": _(
                "Average temperature (%(actual)s°C) is below crop minimum "
                "(%(minimum)s°C) by %(diff)s°C."
            ) % {"actual": actual_t, "minimum": req['min_temp'], "diff": f"{diff:.1f}"},
            "severity": _(sev_key),
            "severity_key": sev_key,
            "severity_color": "danger" if sev_key == "Critical" else "warning",
            "problem_key": "low temperature",
            "icon": "thermometer-low",
        })

    # ── Humidity ──────────────────────────────────────────────────────────────
    actual_h = st["avg_humidity"]
    if actual_h > req["max_humidity"]:
        diff = actual_h - req["max_humidity"]
        sev_key = "Moderate" if diff <= 15 else "Critical"
        reasons.append({
            "reason": _("High Humidity"),
            "detail": _(
                "Humidity (%(actual)s%%) exceeds crop maximum (%(maximum)s%%). "
                "Increases fungal disease risk."
            ) % {"actual": actual_h, "maximum": req['max_humidity']},
            "severity": _(sev_key),
            "severity_key": sev_key,
            "severity_color": "warning",
            "problem_key": "high humidity",
            "icon": "moisture",
        })
    elif actual_h < req["min_humidity"]:
        reasons.append({
            "reason": _("Low Humidity"),
            "detail": _(
                "Humidity (%(actual)s%%) is below crop minimum (%(minimum)s%%). "
                "Increases water stress."
            ) % {"actual": actual_h, "minimum": req['min_humidity']},
            "severity": _("Moderate"),
            "severity_key": "Moderate",
            "severity_color": "warning",
            "problem_key": "low rainfall",
            "icon": "moisture",
        })

    # ── Soil pH ───────────────────────────────────────────────────────────────
    actual_ph = st["soil_ph"]
    if actual_ph > req["max_ph"] + 0.3:
        reasons.append({
            "reason": _("Soil pH Too High"),
            "detail": _(
                "Soil pH (%(ph)s) is alkaline. Crop needs pH %(min_ph)s–%(max_ph)s. "
                "Nutrient lock-up likely."
            ) % {"ph": actual_ph, "min_ph": req['min_ph'], "max_ph": req['max_ph']},
            "severity": _("Moderate"),
            "severity_key": "Moderate",
            "severity_color": "warning",
            "problem_key": "soil ph mismatch",
            "icon": "flask",
        })
    elif actual_ph < req["min_ph"] - 0.3:
        reasons.append({
            "reason": _("Soil pH Too Low"),
            "detail": _(
                "Soil pH (%(ph)s) is acidic. Crop needs pH %(min_ph)s–%(max_ph)s. "
                "Aluminum toxicity risk."
            ) % {"ph": actual_ph, "min_ph": req['min_ph'], "max_ph": req['max_ph']},
            "severity": _("Moderate"),
            "severity_key": "Moderate",
            "severity_color": "warning",
            "problem_key": "soil ph mismatch",
            "icon": "flask",
        })

    # ── Soil Nutrients ────────────────────────────────────────────────────────
    nitrogen = st.get("nitrogen", "medium")
    if nitrogen == "low":
        reasons.append({
            "reason": _("Poor Soil Nutrients"),
            "detail": _("Soil nitrogen is low. Crop yield will be significantly limited without fertiliser input."),
            "severity": _("Moderate"),
            "severity_key": "Moderate",
            "severity_color": "warning",
            "problem_key": "poor soil nutrients",
            "icon": "tree",
        })

    # ── Soil Type ─────────────────────────────────────────────────────────────
    if suitability.get("soil_type_score", 1.0) < 0.5:
        reasons.append({
            "reason": _("Soil Type Mismatch"),
            "detail": _(
                "Soil type in %(state)s does not match crop requirements. "
                "Ideal soils: %(soils)s."
            ) % {"state": state, "soils": ", ".join(req['ideal_soils'])},
            "severity": _("Moderate"),
            "severity_key": "Moderate",
            "severity_color": "warning",
            "problem_key": "soil type mismatch",
            "icon": "layers",
        })

    if not reasons:
        reasons.append({
            "reason": _("No Major Issues"),
            "detail": _("All key parameters are within acceptable range for this crop."),
            "severity": _("None"),
            "severity_key": "None",
            "severity_color": "success",
            "problem_key": "general",
            "icon": "check-circle",
        })

    # Collect unique problem keys for solution lookup
    problem_keys = list(dict.fromkeys(r["problem_key"] for r in reasons))

    return {
        "failure_reasons": reasons,
        "problem_keys": problem_keys,
        "has_issues": any(r["severity"] != "None" for r in reasons),
        "critical_count": sum(1 for r in reasons if r["severity"] == "Critical"),
        "moderate_count": sum(1 for r in reasons if r["severity"] == "Moderate"),
    }
