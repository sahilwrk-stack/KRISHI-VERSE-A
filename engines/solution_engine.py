"""
MODULES 6 & 7 – Modern & Traditional Solution Engine
Recommends technology-based and low-cost traditional solutions based on
diagnosed problems, then calculates revised yield and income projections.
"""
from data.loader import get_modern_solution, get_traditional_solution


def _revised_profit(original_profit: float, yield_improvement_pct: float,
                    extra_cost: float) -> float:
    """Apply yield improvement to revenue portion and subtract extra cost."""
    improvement_factor = yield_improvement_pct / 100.0
    additional_revenue = max(0.0, original_profit) * improvement_factor
    return original_profit + additional_revenue - extra_cost


def recommend(problem_keys: list, financial: dict, land_size_acres: float) -> dict:
    """
    Returns modern_solutions and traditional_solutions lists along with
    revised financial estimates per solution.
    """
    land_ha = max(land_size_acres * 0.4047, 0.001)
    original_profit = financial.get("net_profit", 0)

    modern_list: list = []
    traditional_list: list = []
    seen_modern: set = set()
    seen_trad: set = set()

    for key in (problem_keys or ["general"]):
        # Modern solution
        ms = get_modern_solution(key)
        if ms["solution"] not in seen_modern:
            seen_modern.add(ms["solution"])
            extra_cost = ms["investment_ha"] * land_ha
            subsidy_savings = extra_cost * ms.get("subsidy_pct", 0) / 100.0
            net_extra_cost = extra_cost - subsidy_savings
            rev_profit = _revised_profit(original_profit, ms["yield_improvement_pct"], net_extra_cost)
            rev_yield = financial.get("total_yield_q", 0) * (1 + ms["yield_improvement_pct"] / 100)
            modern_list.append({
                "problem": key.title(),
                "solution": ms["solution"],
                "description": ms["description"],
                "extra_investment": round(extra_cost, 0),
                "subsidy_savings": round(subsidy_savings, 0),
                "net_extra_cost": round(net_extra_cost, 0),
                "roi_years": ms["roi_years"],
                "yield_improvement_pct": ms["yield_improvement_pct"],
                "revised_profit": round(rev_profit, 0),
                "revised_yield_q": round(rev_yield, 2),
                "subsidy_available": ms.get("subsidy_available", False),
                "subsidy_pct": ms.get("subsidy_pct", 0),
            })

        # Traditional solution
        ts = get_traditional_solution(key)
        if ts["solution"] not in seen_trad:
            seen_trad.add(ts["solution"])
            trad_cost = ts["cost_approx_ha"] * land_ha
            rev_profit_t = _revised_profit(original_profit, ts["yield_improvement_pct"], trad_cost)
            rev_yield_t = financial.get("total_yield_q", 0) * (1 + ts["yield_improvement_pct"] / 100)
            traditional_list.append({
                "problem": key.title(),
                "solution": ts["solution"],
                "description": ts["description"],
                "cost_level": ts["cost_level"],
                "total_cost": round(trad_cost, 0),
                "yield_improvement_pct": ts["yield_improvement_pct"],
                "revised_profit": round(rev_profit_t, 0),
                "revised_yield_q": round(rev_yield_t, 2),
            })

    # Best modern and traditional picks (highest yield improvement)
    best_modern = max(modern_list, key=lambda x: x["yield_improvement_pct"], default=None)
    best_traditional = max(traditional_list, key=lambda x: x["yield_improvement_pct"], default=None)

    new_stability_score = None
    if best_modern:
        improvement = best_modern["yield_improvement_pct"] / 100.0
        base_suitability = financial.get("investment_ratio_pct", 70) / 100.0
        new_stability_score = round(min(100.0, base_suitability * 100 + improvement * 30), 1)

    return {
        "modern_solutions": modern_list,
        "traditional_solutions": traditional_list,
        "best_modern": best_modern,
        "best_traditional": best_traditional,
        "new_stability_score": new_stability_score,
    }
