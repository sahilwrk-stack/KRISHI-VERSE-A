"""
Crop & Vegetable Comparison Engine
Ranks all items available in a state by profit, stability, balance, or low risk.
"""
from django.utils.translation import gettext as _
from data.vegetable_data import MARKET_ITEMS, STATE_AVAILABLE_ITEMS
from data.loader import get_state_data
from engines.suitability_engine import (
    _score_in_range, _soil_type_score, _ph_score, _nitrogen_score,
)

ACRES_TO_HA = 0.4047


# ─────────────────────────────────────────────────────────────────────────────
# SUITABILITY (reuses suitability_engine helpers)
# ─────────────────────────────────────────────────────────────────────────────
def _calc_suitability(state_data: dict, item: dict, soil_type: str) -> dict:
    rf_score = _score_in_range(
        state_data["avg_rainfall"],
        item["min_rainfall"], item["max_rainfall"], item["optimal_rainfall"],
    )
    t_score = _score_in_range(
        state_data["avg_temp"],
        item["min_temp"], item["max_temp"], item["optimal_temp"],
    )
    h_score = _score_in_range(
        state_data["avg_humidity"],
        item["min_humidity"], item["max_humidity"], item["optimal_humidity"],
    )
    climate_score = rf_score * 0.40 + t_score * 0.35 + h_score * 0.25

    ph_sc   = _ph_score(state_data["soil_ph"], item["min_ph"], item["max_ph"])
    type_sc = _soil_type_score(soil_type or state_data["soil_type"], item["ideal_soils"])
    nitro   = _nitrogen_score(state_data.get("nitrogen", "medium"))
    soil_score = ph_sc * 0.40 + type_sc * 0.40 + nitro * 0.20

    final = max(0.0, min(1.0, climate_score * 0.60 + soil_score * 0.40))

    if final > 0.75:
        level, color = _("Suitable"), "success"
    elif final >= 0.50:
        level, color = _("Moderate"), "warning"
    else:
        level, color = _("Not Recommended"), "danger"

    temp_dev = round(abs(state_data["avg_temp"] - item["optimal_temp"]), 1)
    rain_dev = round(state_data["avg_rainfall"] - item["optimal_rainfall"])

    return {
        "score": round(final, 4),
        "pct": round(final * 100, 1),
        "level": level,
        "color": color,
        "climate_pct": round(climate_score * 100, 1),
        "soil_pct": round(soil_score * 100, 1),
        "temp_deviation_c": temp_dev,
        "rainfall_deviation_mm": rain_dev,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL
# ─────────────────────────────────────────────────────────────────────────────
def _calc_financial(item: dict, land_ha: float, investment_capacity: float,
                    suitability_score: float) -> dict:
    cost_ha  = item["national_avg_cost_ha"]
    yield_ha = item["national_avg_yield_q_ha"]
    price_q  = item["national_avg_price_q"]
    msp_q    = item.get("msp_q", 0)

    needed = cost_ha * land_ha
    inv_ratio = min(investment_capacity / needed, 1.0) if needed > 0 else 1.0
    actual_inv = min(investment_capacity, needed)

    # Yield reduced by investment gap and suitability
    eff_yield = yield_ha * (0.5 + 0.5 * inv_ratio) * (0.6 + 0.4 * suitability_score)
    total_yield = eff_yield * land_ha

    eff_price   = max(price_q, msp_q)
    revenue     = total_yield * eff_price
    net_profit  = revenue - needed
    roi         = (net_profit / needed * 100) if needed > 0 else 0.0

    return {
        "investment_needed": round(needed, 0),
        "actual_investment": round(actual_inv, 0),
        "inv_ratio_pct": round(inv_ratio * 100, 1),
        "total_yield_q": round(total_yield, 2),
        "yield_per_ha": round(eff_yield, 1),
        "effective_price_q": round(eff_price, 0),
        "expected_revenue": round(revenue, 0),
        "net_profit": round(net_profit, 0),
        "roi": round(roi, 2),
        "profit_per_acre": round(net_profit / max(land_ha / ACRES_TO_HA, 0.001), 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STABILITY SCORE  &  MARKET INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────
def _calc_stability(item: dict, suitability_score: float) -> float:
    v   = item["price_volatility"]
    d   = item["demand_index"]
    sl  = item["storage_loss_pct"] / 100.0
    raw = (1 - v) * d * (1 - sl)
    # Blend with suitability so unsuitable crops get lower stability
    blended = raw * (0.7 + 0.3 * suitability_score)
    return round(max(0.0, min(1.0, blended)), 4)


# ─────────────────────────────────────────────────────────────────────────────
# FUTURE PROJECTIONS
# ─────────────────────────────────────────────────────────────────────────────
def _calc_projections(revenue: float, growth_rate: float,
                      stability_score: float) -> dict:
    yearly = []
    for yr in range(1, 6):
        inc = revenue * ((1 + growth_rate) ** yr) * stability_score
        yearly.append(round(inc, 0))

    return {
        "yearly": yearly,
        "total_3yr": round(sum(yearly[:3]), 0),
        "total_5yr": round(sum(yearly), 0),
        "avg_annual_3yr": round(sum(yearly[:3]) / 3, 0),
        "avg_annual_5yr": round(sum(yearly) / 5, 0),
        "years": [2025, 2026, 2027, 2028, 2029],
    }


# ─────────────────────────────────────────────────────────────────────────────
# LOSS DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def _is_avoid(financial: dict, item: dict, suitability: dict) -> tuple:
    reasons = []
    if financial["net_profit"] < 0:
        reasons.append("Negative profit")
    if item["price_volatility"] > 0.70:
        reasons.append(f"High price volatility ({item['price_volatility']*100:.0f}%)")
    if suitability["level"] == "Not Recommended":
        reasons.append("Climate/soil not suitable")
    if item["storage_loss_pct"] > 40:
        reasons.append(f"High storage loss ({item['storage_loss_pct']}%)")
    return bool(reasons), reasons


# ─────────────────────────────────────────────────────────────────────────────
# EMOTION
# ─────────────────────────────────────────────────────────────────────────────
def _emotion(best: dict) -> dict:
    if best is None:
        return {"label": _("Sad"), "emoji": "sad", "color": "danger",
                "message": _("No suitable crops found for this region with given investment.")}

    profit = best["financial"]["net_profit"]
    stability = best["stability_score"]
    volatility = best["item_data"]["price_volatility"]
    proj_5yr = best["projections"]["total_5yr"]

    score = (
        min(100, max(0, profit / max(abs(profit), 1) * 50 + 50)) * 0.35
        + stability * 100 * 0.30
        + (1 - volatility) * 100 * 0.20
        + min(100, proj_5yr / max(abs(proj_5yr), 1) * 50 + 50) * 0.15
    )

    if score >= 70:
        return {"label": _("Happy"), "emoji": "happy", "color": "success",
                "message": _("Excellent! %(crop)s is a highly profitable and stable choice for your region.") % {"crop": best["name"]}}
    elif score >= 55:
        return {"label": _("Satisfied"), "emoji": "satisfied", "color": "primary",
                "message": _("Good choice! %(crop)s offers solid returns with manageable risk.") % {"crop": best["name"]}}
    elif score >= 40:
        return {"label": _("Neutral"), "emoji": "neutral", "color": "info",
                "message": _("%(crop)s offers moderate returns. Consider the suggested solutions to improve profitability.") % {"crop": best["name"]}}
    elif score >= 25:
        return {"label": _("Concerned"), "emoji": "concerned", "color": "warning",
                "message": _("Caution advised. %(crop)s has moderate risk. Review the loss-risk crops carefully.") % {"crop": best["name"]}}
    else:
        return {"label": _("Sad"), "emoji": "sad", "color": "danger",
                "message": _("High risk detected. Most crops face challenges in this region. Explore modern solutions.")}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def run(state: str, land_size_acres: float, investment_capacity: float,
        mode: str, soil_type: str, filter_type: str = "All") -> dict:
    """
    Analyse all available crops/vegetables for a state and rank them.
    Returns a full result dict ready for template rendering.
    """
    state_title = state.strip().title()
    state_data  = get_state_data(state_title)
    land_ha     = max(land_size_acres * ACRES_TO_HA, 0.001)

    available = STATE_AVAILABLE_ITEMS.get(state_title, list(MARKET_ITEMS.keys()))

    results = []
    for name in available:
        item = MARKET_ITEMS.get(name)
        if item is None:
            continue
        if filter_type != "All" and item["type"] != filter_type:
            continue

        suit   = _calc_suitability(state_data, item, soil_type)
        fin    = _calc_financial(item, land_ha, investment_capacity, suit["score"])
        stab   = _calc_stability(item, suit["score"])
        proj   = _calc_projections(fin["expected_revenue"], item["price_growth_rate"], stab)
        avoid, avoid_reasons = _is_avoid(fin, item, suit)

        results.append({
            "name": name,
            "type": item["type"],
            "season": item["season"],
            "suitability": suit,
            "financial": fin,
            "stability_score": stab,
            "stability_pct": round(stab * 100, 1),
            "projections": proj,
            "is_avoid": avoid,
            "avoid_reasons": avoid_reasons,
            "item_data": {
                "price_volatility":     item["price_volatility"],
                "price_volatility_pct": round(item["price_volatility"] * 100, 1),
                "demand_index":         item["demand_index"],
                "demand_pct":           round(item["demand_index"] * 100, 1),
                "storage_loss_pct":     item["storage_loss_pct"],
                "price_growth_rate":    item["price_growth_rate"],
                "price_growth_pct":     round(item["price_growth_rate"] * 100, 1),
                "msp_q":                item.get("msp_q", 0),
            },
        })

    if not results:
        return {"results": [], "best": None, "second": None, "top_avoid": None,
                "avoid_items": [], "emotion": _emotion(None),
                "state": state_title, "state_info": state_data,
                "mode": mode, "filter_type": filter_type,
                "total_items": 0, "good_count": 0, "avoid_count": 0,
                "land_size_acres": land_size_acres, "land_ha": round(land_ha, 3),
                "investment_capacity": investment_capacity, "soil_type": soil_type,
                "chart_labels": [], "chart_profit": [], "chart_stability": [],
                "chart_roi": [], "chart_5yr": []}

    # ── Ranking ───────────────────────────────────────────────────────────────
    safe = [r for r in results if not r["is_avoid"]]

    if mode == "profit":
        ranked = sorted(results, key=lambda x: x["financial"]["net_profit"], reverse=True)
    elif mode == "stable":
        ranked = sorted(results, key=lambda x: x["stability_score"], reverse=True)
    elif mode == "balanced":
        max_p = max((abs(r["financial"]["net_profit"]) for r in results), default=1) or 1
        for r in results:
            r["balanced_score"] = round(
                0.5 * (r["financial"]["net_profit"] / max_p) + 0.5 * r["stability_score"], 4
            )
        ranked = sorted(results, key=lambda x: x.get("balanced_score", 0), reverse=True)
    elif mode == "low_risk":
        positive = [r for r in results if r["financial"]["net_profit"] > 0]
        ranked = sorted(positive,
                        key=lambda x: (x["item_data"]["price_volatility"],
                                       x["item_data"]["storage_loss_pct"]))
        ranked += [r for r in results if r["financial"]["net_profit"] <= 0]
    else:
        ranked = results

    avoid_items = [r for r in ranked if r["is_avoid"]]
    good_items  = [r for r in ranked if not r["is_avoid"]]

    best   = good_items[0] if good_items else (ranked[0] if ranked else None)
    second = good_items[1] if len(good_items) > 1 else (ranked[1] if len(ranked) > 1 else None)
    top_avoid = avoid_items[0] if avoid_items else None

    # ── Chart data ────────────────────────────────────────────────────────────
    top12 = ranked[:12]
    chart_labels    = [r["name"] for r in top12]
    chart_profit    = [float(r["financial"]["net_profit"]) for r in top12]
    chart_stability = [float(r["stability_pct"]) for r in top12]
    chart_roi       = [float(r["financial"]["roi"]) for r in top12]
    chart_5yr       = [float(r["projections"]["total_5yr"]) for r in top12]

    return {
        "results": ranked,
        "best": best,
        "second": second,
        "top_avoid": top_avoid,
        "avoid_items": avoid_items,
        "emotion": _emotion(best),
        "state": state_title,
        "state_info": state_data,
        "mode": mode,
        "filter_type": filter_type,
        "total_items": len(results),
        "good_count": len(good_items),
        "avoid_count": len(avoid_items),
        "land_size_acres": land_size_acres,
        "land_ha": round(land_ha, 3),
        "investment_capacity": investment_capacity,
        "soil_type": soil_type,
        "chart_labels": chart_labels,
        "chart_profit": chart_profit,
        "chart_stability": chart_stability,
        "chart_roi": chart_roi,
        "chart_5yr": chart_5yr,
    }
