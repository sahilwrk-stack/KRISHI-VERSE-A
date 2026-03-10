"""
MODULE 2 – Financial Engine
Calculates investment, expected yield, revenue, government support, net profit, ROI.
"""
from data.loader import (
    get_cost_and_yield, get_market_price, get_msp, get_subsidies,
)

ACRES_TO_HA = 0.4047


def calculate(crop: str, state: str, land_size_acres: float,
              investment_capacity: float) -> dict:
    """
    Returns detailed financial projections for the given farmer inputs.
    All monetary values are in Indian Rupees (₹).
    """
    land_ha = max(land_size_acres * ACRES_TO_HA, 0.001)

    cy = get_cost_and_yield(crop, state)
    cost_per_ha: float = cy["cost_ha"]
    yield_per_ha: float = cy["yield_q_ha"]

    investment_needed: float = cost_per_ha * land_ha
    investment_capacity = max(investment_capacity, 0.0)

    # Investment sufficiency ratio (capped at 1.0)
    inv_ratio = min(investment_capacity / investment_needed, 1.0) if investment_needed > 0 else 1.0
    actual_investment = min(investment_capacity, investment_needed)

    # Yield scales with investment ratio (under-investment reduces yield)
    effective_yield_per_ha = yield_per_ha * (0.5 + 0.5 * inv_ratio)
    total_yield_q = effective_yield_per_ha * land_ha

    # Revenue – use higher of market price or MSP
    market_price = get_market_price(crop, state)
    msp = get_msp(crop)
    effective_price = max(market_price, msp)
    expected_revenue = total_yield_q * effective_price

    # Government support
    subsidy_data = get_subsidies(crop)
    govt_support = _calc_govt_support(subsidy_data, land_ha)

    # Financial outcomes
    net_profit = expected_revenue + govt_support - investment_needed
    roi = (net_profit / investment_needed * 100) if investment_needed > 0 else 0.0
    profit_per_acre = net_profit / max(land_size_acres, 0.001)
    break_even_price = investment_needed / max(total_yield_q, 0.001)

    return {
        "land_ha": round(land_ha, 3),
        "land_acres": round(land_size_acres, 2),
        "cost_per_ha": round(cost_per_ha, 0),
        "investment_needed": round(investment_needed, 0),
        "investment_capacity": round(investment_capacity, 0),
        "investment_ratio_pct": round(inv_ratio * 100, 1),
        "actual_investment": round(actual_investment, 0),
        "yield_per_ha": round(effective_yield_per_ha, 1),
        "total_yield_q": round(total_yield_q, 2),
        "market_price": round(market_price, 0),
        "msp": round(msp, 0),
        "effective_price": round(effective_price, 0),
        "expected_revenue": round(expected_revenue, 0),
        "govt_support": round(govt_support, 0),
        "net_profit": round(net_profit, 0),
        "roi": round(roi, 2),
        "profit_per_acre": round(profit_per_acre, 0),
        "break_even_price": round(break_even_price, 2),
        "subsidy_detail": subsidy_data,
    }


def _calc_govt_support(subsidy_data: dict, land_ha: float) -> float:
    """Sum all per-hectare subsidies plus flat PM-Kisan amount."""
    fertilizer = subsidy_data.get("fertilizer", 0) * land_ha
    seed = subsidy_data.get("seed", 0) * land_ha
    irrigation = subsidy_data.get("irrigation", 0) * land_ha
    pm_kisan = subsidy_data.get("pm_kisan", 6000)
    return fertilizer + seed + irrigation + pm_kisan
