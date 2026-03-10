"""
MODULE 8 – Government Intelligence Engine
Consolidates MSP guarantee, subsidy amounts, insurance support, and compensation.
"""
from django.utils.translation import gettext as _
from data.loader import get_msp, get_subsidies, get_insurance


def calculate(crop: str, state: str, land_size_acres: float) -> dict:
    """Returns detailed government support breakdown."""
    land_ha = max(land_size_acres * 0.4047, 0.001)

    msp = get_msp(crop)
    subsidy_data = get_subsidies(crop)
    insurance = get_insurance(crop)

    # Per-hectare subsidies scaled to land
    fertilizer_subsidy = subsidy_data.get("fertilizer", 0) * land_ha
    seed_subsidy = subsidy_data.get("seed", 0) * land_ha
    irrigation_subsidy = subsidy_data.get("irrigation", 0) * land_ha
    pm_kisan = subsidy_data.get("pm_kisan", 6000)

    total_subsidy = fertilizer_subsidy + seed_subsidy + irrigation_subsidy + pm_kisan
    insurance_premium = insurance["premium_ha"] * land_ha
    max_insurance_payout = insurance_premium * 10 * (insurance["coverage_pct"] / 100)

    return {
        "msp_per_quintal": round(msp, 0),
        "has_msp": msp > 0,
        "fertilizer_subsidy": round(fertilizer_subsidy, 0),
        "seed_subsidy": round(seed_subsidy, 0),
        "irrigation_subsidy": round(irrigation_subsidy, 0),
        "pm_kisan": round(pm_kisan, 0),
        "total_subsidy": round(total_subsidy, 0),
        "insurance_coverage_pct": insurance["coverage_pct"],
        "insurance_premium": round(insurance_premium, 0),
        "max_insurance_payout": round(max_insurance_payout, 0),
        "schemes": _get_relevant_schemes(crop),
    }


def _get_relevant_schemes(crop: str) -> list:
    """Return list of applicable government schemes for a crop."""
    schemes = [
        {"name": "PM-KISAN", "description": _("₹6,000/year direct income support to all landholding farmers"), "benefit": _("₹6,000/year")},
        {"name": "PM Fasal Bima Yojana (PMFBY)", "description": _("Crop insurance with low premium and high coverage against natural calamities"), "benefit": _("Up to 90% crop loss covered")},
        {"name": "Soil Health Card Scheme", "description": _("Free soil testing and nutrient recommendations to improve yield"), "benefit": _("Free soil analysis + nutrient advice")},
        {"name": "Kisan Credit Card (KCC)", "description": _("Short-term credit at 4-7% interest rate for farm expenses"), "benefit": _("Low-interest farm credit")},
    ]
    crop_specific = {
        "Rice":      {"name": "National Food Security Mission (NFSM)", "description": _("Special support for rice cultivation - improved seeds, demos, and training"), "benefit": _("Seed subsidy + training")},
        "Wheat":     {"name": "National Food Security Mission (NFSM)", "description": _("Support for wheat cultivation with better seed varieties and technologies"), "benefit": _("Seed & technology support")},
        "Sugarcane": {"name": "Sugar Development Fund", "description": _("Interest-free loans for sugarcane cultivation and cane development"), "benefit": _("Zero-interest development loan")},
        "Cotton":    {"name": "Technology Mission on Cotton (TMC)", "description": _("Improved cotton varieties, pest management, and ginning support"), "benefit": _("Better seed + pest support")},
        "Soybean":   {"name": "National Food Security Mission – Oilseeds", "description": _("Support for oilseed crops including soybean cultivation technology"), "benefit": _("Seed & tech subsidy")},
        "Groundnut": {"name": "National Food Security Mission – Oilseeds", "description": _("Oilseed cultivation support with seed subsidy and demonstrations"), "benefit": _("Seed subsidy + demo")},
        "Mustard":   {"name": "National Food Security Mission – Oilseeds", "description": _("Support for mustard cultivation under oilseed mission"), "benefit": _("Seed & fertiliser support")},
    }
    if crop in crop_specific:
        schemes.append(crop_specific[crop])
    return schemes
