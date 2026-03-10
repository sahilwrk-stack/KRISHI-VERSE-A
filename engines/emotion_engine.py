"""
MODULE 9 – Emotional Outcome Engine
Classifies the farmer's likely emotional outcome based on financial and risk data.
"""
from django.utils.translation import gettext as _


def classify(financial: dict, suitability: dict, risk: dict, projection: dict) -> dict:
    """
    Returns farmer_emotion (Happy / Satisfied / Concerned / Sad) with
    a personalised message and recommendation.
    """
    net_profit = financial.get("net_profit", 0)
    investment = max(financial.get("investment_needed", 1), 1)
    roi = financial.get("roi", 0)
    stability = projection.get("income_stability_score", 50)
    failure_prob = risk.get("failure_probability", 0.5)
    suitability_score = suitability.get("suitability_score", 0.5)

    # Composite score (0-100)
    profit_score = min(100, max(0, (net_profit / investment) * 100))
    risk_penalty = failure_prob * 40
    composite = (
        profit_score * 0.35
        + stability * 0.25
        + suitability_score * 100 * 0.25
        + max(0, roi) * 0.15
        - risk_penalty
    )
    composite = max(0.0, min(100.0, composite))

    if composite >= 68:
        emotion = _("Happy")
        emoji = "😊"
        color = "success"
        message = _(
            "Excellent choice! Your crop selection aligns well with the local "
            "climate and soil. High returns and stable income are expected. "
            "Your farming journey looks prosperous!"
        )
        recommendation = _(
            "Continue with the current crop plan. Invest in quality seeds and "
            "modern irrigation to maximise yield further."
        )
        badge = "bg-success"
    elif composite >= 45:
        emotion = _("Satisfied")
        emoji = "😐"
        color = "warning"
        message = _(
            "Your crop selection is acceptable but there are moderate risks. "
            "Implementing the suggested solutions will significantly improve "
            "your profitability and stability."
        )
        recommendation = _(
            "Review the modern and traditional solutions provided. A small "
            "extra investment in soil health or irrigation can push you into "
            "the 'Happy' zone."
        )
        badge = "bg-warning"
    elif composite >= 25:
        emotion = _("Concerned")
        emoji = "😟"
        color = "secondary"
        message = _(
            "This crop carries notable risks in your selected state. Income "
            "may be below expectations. Consider adopting suggested solutions "
            "or exploring alternative crops with better suitability."
        )
        recommendation = _(
            "Strongly consider the recommended modern solutions. Alternatively, "
            "check other crops that are highly suitable for your state."
        )
        badge = "bg-secondary"
    else:
        emotion = _("Sad")
        emoji = "😢"
        color = "danger"
        message = _(
            "This crop is not well-suited for your region and financial profile. "
            "High probability of financial loss. Immediate reconsideration of "
            "crop selection is strongly advised."
        )
        recommendation = _(
            "Switch to a crop that is naturally suited to your state's climate. "
            "Use the suitability engine to compare alternative crops before investing."
        )
        badge = "bg-danger"

    return {
        "farmer_emotion": emotion,
        "emoji": emoji,
        "color": color,
        "badge": badge,
        "message": message,
        "recommendation": recommendation,
        "composite_score": round(composite, 1),
    }
