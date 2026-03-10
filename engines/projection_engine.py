"""
MODULE 4 – Future Projection Engine
Projects 3-year and 5-year income using growth factors and climate stability trends.
"""
import math
from data.loader import get_climate_history, get_growth_factors


def _rainfall_stability(rainfall_series: list) -> float:
    """Coefficient of variation (lower = more stable). Returns stability index 0-1."""
    if len(rainfall_series) < 2:
        return 0.8
    mean = sum(rainfall_series) / len(rainfall_series)
    if mean == 0:
        return 0.5
    variance = sum((x - mean) ** 2 for x in rainfall_series) / len(rainfall_series)
    cv = math.sqrt(variance) / mean
    stability = max(0.0, 1.0 - min(cv, 1.0))
    return round(stability, 4)


def _compound_growth(base: float, rate: float, years: int) -> float:
    """Apply compound growth rate over n years."""
    return base * ((1 + rate) ** years)


def calculate(crop: str, state: str, financial: dict, suitability: dict) -> dict:
    """
    Returns 3-year and 5-year earning projections along with stability metrics.
    """
    annual_profit = financial.get("net_profit", 0)
    suitability_score = suitability.get("suitability_score", 0.5)

    history = get_climate_history(state)
    rainfall_series = history.get("rainfall", [800] * 5)
    stability_index = _rainfall_stability(rainfall_series)

    gf = get_growth_factors(crop)
    price_growth = gf["price_growth"]
    yield_growth = gf["yield_growth"]
    volatility = gf["volatility"]

    # Combined growth rate = average of price and yield growth
    combined_growth = (price_growth + yield_growth) / 2.0

    # Adjust growth by suitability (unsuitable crop degrades over time)
    adjusted_growth = combined_growth * suitability_score

    # Year-by-year projection
    yearly_profits: list = []
    for yr in range(1, 6):
        projected = _compound_growth(annual_profit, adjusted_growth, yr)
        # Apply volatility noise (deterministic: odd years slightly lower)
        noise = 1 - volatility * 0.3 if yr % 2 == 0 else 1 + volatility * 0.1
        yearly_profits.append(round(projected * noise, 0))

    cumulative_3yr = sum(yearly_profits[:3])
    cumulative_5yr = sum(yearly_profits[:5])

    # Volatility index and stability score
    volatility_index = round(volatility * 100, 1)
    income_stability_score = round(stability_index * suitability_score * 100, 1)

    # Long-term loss scenario if unsuitable crop continues unchanged
    if suitability_score < 0.5:
        degradation_rate = (0.5 - suitability_score) * 0.10
        loss_3yr = sum(
            abs(annual_profit) * ((1 + degradation_rate) ** yr) for yr in range(1, 4)
        )
        loss_5yr = sum(
            abs(annual_profit) * ((1 + degradation_rate) ** yr) for yr in range(1, 6)
        )
    else:
        loss_3yr = 0.0
        loss_5yr = 0.0

    return {
        "yearly_profits": yearly_profits,
        "cumulative_3yr": round(cumulative_3yr, 0),
        "cumulative_5yr": round(cumulative_5yr, 0),
        "avg_annual_3yr": round(cumulative_3yr / 3, 0) if cumulative_3yr else 0,
        "avg_annual_5yr": round(cumulative_5yr / 5, 0) if cumulative_5yr else 0,
        "volatility_index": volatility_index,
        "income_stability_score": income_stability_score,
        "rainfall_stability": round(stability_index * 100, 1),
        "growth_rate_pct": round(adjusted_growth * 100, 2),
        "loss_3yr_if_unsuitable": round(loss_3yr, 0),
        "loss_5yr_if_unsuitable": round(loss_5yr, 0),
        "years": [2025, 2026, 2027, 2028, 2029],
    }
