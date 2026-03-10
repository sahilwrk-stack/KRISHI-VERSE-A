"""
MODULE 3 – Risk & Loss Engine
Estimates failure probability, insurance cover, and potential financial loss.
"""
from django.utils.translation import gettext as _
from data.loader import get_insurance, get_crop_requirements


def calculate(crop: str, state: str, suitability: dict, financial: dict) -> dict:
    """
    Returns risk profile: failure probability, estimated loss, insurance coverage.
    """
    suitability_score = suitability.get("suitability_score", 0.5)
    investment = financial.get("investment_needed", 0)
    revenue = financial.get("expected_revenue", 0)

    req = get_crop_requirements(crop)
    base_yield_loss_pct = req.get("failure_yield_loss_pct", 30) / 100.0

    # Failure probability rises as suitability falls
    # At score=1.0 → ~5% base risk; at score=0 → ~90% risk
    base_failure_prob = max(0.05, 1.0 - suitability_score)
    failure_prob = min(0.90, base_failure_prob * 0.95)

    # Expected financial loss if failure occurs
    gross_exposure = investment + revenue
    yield_loss_value = revenue * base_yield_loss_pct * failure_prob

    # Insurance
    ins = get_insurance(crop)
    coverage_pct = ins["coverage_pct"] / 100.0
    premium_total = ins["premium_ha"] * financial.get("land_ha", 1.0)

    insurance_payout = yield_loss_value * coverage_pct
    final_loss_after_insurance = max(0.0, yield_loss_value - insurance_payout)
    net_loss_worst_case = max(0.0, investment * failure_prob - insurance_payout)

    # Risk level classification
    if failure_prob < 0.20:
        risk_level = _("Low")
        risk_color = "success"
    elif failure_prob < 0.45:
        risk_level = _("Moderate")
        risk_color = "warning"
    else:
        risk_level = _("High")
        risk_color = "danger"

    return {
        "failure_probability": round(failure_prob, 4),
        "failure_probability_pct": round(failure_prob * 100, 1),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "insurance_coverage_pct": ins["coverage_pct"],
        "insurance_premium_total": round(premium_total, 0),
        "insurance_payout": round(insurance_payout, 0),
        "yield_loss_value": round(yield_loss_value, 0),
        "final_loss_after_insurance": round(final_loss_after_insurance, 0),
        "net_loss_worst_case": round(net_loss_worst_case, 0),
        "gross_exposure": round(gross_exposure, 0),
    }
