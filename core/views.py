import json
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
from core.forms import FarmAnalysisForm, CropCompareForm
from engines.master_engine import run as run_analysis
from engines.comparison_engine import run as run_comparison
from data.loader import get_soil_types_for_state, get_crops_for_state


FEATURE_CARDS = [
    {"emoji": "🌱", "name": "Crop Suitability Analysis",     "desc": "Matches climate, soil type, rainfall & pH of your state against each crop's ideal requirements."},
    {"emoji": "💰", "name": "Financial ROI & Profit",        "desc": "Calculates investment needed, expected yield, revenue, net profit and return on investment per acre."},
    {"emoji": "📊", "name": "Market Intelligence Engine",    "desc": "Ranks every crop by demand index, price volatility, storage risk and annual growth rate."},
    {"emoji": "📈", "name": "5-Year Income Projection",      "desc": "Projects your earnings year-by-year for the next 5 years using compound growth and stability models."},
    {"emoji": "⚠",  "name": "Risk & Loss Detection",         "desc": "Estimates failure probability, crop loss value, insurance payout and worst-case net loss scenario."},
    {"emoji": "🏛",  "name": "Government Support Insights",  "desc": "Surfaces PM-KISAN, PMFBY, KCC, e-NAM and crop-specific scheme benefits that boost your income."},
    {"emoji": "🌍", "name": "State-Based Crop Filtering",    "desc": "Shows only crops actually grown in your selected state — no irrelevant suggestions."},
    {"emoji": "😊", "name": "Farmer Emotion Prediction",     "desc": "Combines profit, stability, risk and future earnings into a single emotional confidence score."},
]

CROPS_SHOWCASE = [
    {"emoji": "🌾", "name": "Wheat",       "type": "Rabi Crop"},
    {"emoji": "🌾", "name": "Rice",        "type": "Kharif Crop"},
    {"emoji": "🌽", "name": "Maize",       "type": "Kharif Crop"},
    {"emoji": "🟡", "name": "Mustard",     "type": "Rabi Crop"},
    {"emoji": "🟤", "name": "Cotton",      "type": "Kharif Crop"},
    {"emoji": "🍬", "name": "Sugarcane",   "type": "Annual Crop"},
    {"emoji": "🥜", "name": "Groundnut",   "type": "Kharif Crop"},
    {"emoji": "🫘", "name": "Soybean",     "type": "Kharif Crop"},
    {"emoji": "🍅", "name": "Tomato",      "type": "Vegetable"},
    {"emoji": "🧅", "name": "Onion",       "type": "Vegetable"},
    {"emoji": "🥔", "name": "Potato",      "type": "Vegetable"},
    {"emoji": "🥬", "name": "Cabbage",     "type": "Vegetable"},
    {"emoji": "🥦", "name": "Cauliflower", "type": "Vegetable"},
    {"emoji": "🥕", "name": "Carrot",      "type": "Vegetable"},
    {"emoji": "🫑", "name": "Lady Finger", "type": "Vegetable"},
    {"emoji": "🟡", "name": "Turmeric",    "type": "Spice"},
    {"emoji": "🟫", "name": "Ginger",      "type": "Spice"},
    {"emoji": "🌿", "name": "Garlic",      "type": "Vegetable"},
]


@require_http_methods(["GET"])
def index(request):
    return render(request, "core/index.html", {
        "feature_cards":  FEATURE_CARDS,
        "crops_showcase": CROPS_SHOWCASE,
    })


@require_http_methods(["GET", "POST"])
def analyze(request):
    if request.method == "POST":
        form = FarmAnalysisForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            result = run_analysis(
                state=cd["state"],
                crop=cd["crop"],
                land_size_acres=float(cd["land_size_acres"]),
                soil_type=cd["soil_type"],
                irrigation=cd["irrigation"],
                investment_capacity=float(cd["investment_capacity"]),
            )

            # Prepare JSON-serialisable chart payloads
            ch = result["climate_history"]
            projection = result["projection"]

            chart_data = {
                "rainfall": {
                    "labels": [str(y) for y in ch["years"]],
                    "data": [float(v) for v in ch["rainfall"]],
                },
                "temperature": {
                    "labels": [str(y) for y in ch["years"]],
                    "data": [float(v) for v in ch["temps"]],
                },
                "income_projection": {
                    "labels": [str(y) for y in projection["years"]],
                    "data": [float(v) for v in projection["yearly_profits"]],
                },
                "radar": {
                    "labels": result["radar"]["labels"],
                    "data": [float(v) for v in result["radar"]["actual"]],
                },
                "map_scores": {
                    k: float(v) for k, v in result["map_scores"].items()
                },
            }

            # Optionally save to DB (non-blocking)
            try:
                from core.models import AnalysisHistory
                AnalysisHistory.objects.create(
                    state=cd["state"], crop=cd["crop"],
                    land_size_acres=cd["land_size_acres"],
                    soil_type=cd["soil_type"], irrigation=cd["irrigation"],
                    investment_capacity=cd["investment_capacity"],
                    suitability_score=result["suitability"].get("suitability_score"),
                    net_profit=result["financial"].get("net_profit"),
                    roi=result["financial"].get("roi"),
                    farmer_emotion=result["emotion"].get("farmer_emotion", ""),
                )
            except Exception:
                pass

            return render(request, "core/results.html", {
                "result": result,
                "chart_data_json": json.dumps(chart_data),
                "form": FarmAnalysisForm(request.POST),
            })
        else:
            return render(request, "core/index.html", {
                "feature_cards":  FEATURE_CARDS,
                "crops_showcase": CROPS_SHOWCASE,
            })

    return render(request, "core/index.html", {
        "feature_cards":  FEATURE_CARDS,
        "crops_showcase": CROPS_SHOWCASE,
    })


@require_http_methods(["GET", "POST"])
def compare(request):
    """Crop & Vegetable comparison tab."""
    if request.method == "POST":
        form = CropCompareForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            result = run_comparison(
                state=cd["state"],
                land_size_acres=float(cd["land_size_acres"]),
                investment_capacity=float(cd["investment_capacity"]),
                mode=cd["mode"],
                soil_type=cd["soil_type"],
                filter_type=cd.get("filter_type", "All"),
            )
            chart_data = {
                "labels":    result["chart_labels"],
                "profit":    result["chart_profit"],
                "stability": result["chart_stability"],
                "roi":       result["chart_roi"],
                "proj_5yr":  result["chart_5yr"],
            }
            return render(request, "core/compare_results.html", {
                "result": result,
                "chart_data_json": json.dumps(chart_data),
                "form": CropCompareForm(request.POST),
            })
        return render(request, "core/compare.html", {"form": form})
    return render(request, "core/compare.html", {"form": CropCompareForm()})


@require_http_methods(["GET"])
def analysis_dashboard(request):
    """Unified dashboard — both forms on one page, results loaded via AJAX."""
    return render(request, "analysis_dashboard.html", {
        "farm_form":    FarmAnalysisForm(),
        "compare_form": CropCompareForm(),
    })


def _build_farm_chart_data(result: dict) -> dict:
    ch         = result["climate_history"]
    projection = result["projection"]
    return {
        "rainfall": {
            "labels": [str(y) for y in ch["years"]],
            "data":   [float(v) for v in ch["rainfall"]],
        },
        "temperature": {
            "labels": [str(y) for y in ch["years"]],
            "data":   [float(v) for v in ch["temps"]],
        },
        "income_projection": {
            "labels": [str(y) for y in projection["years"]],
            "data":   [float(v) for v in projection["yearly_profits"]],
        },
        "radar": {
            "labels": result["radar"]["labels"],
            "data":   [float(v) for v in result["radar"]["actual"]],
        },
        "map_scores": {k: float(v) for k, v in result["map_scores"].items()},
    }


@require_http_methods(["POST"])
def ajax_farm(request):
    """AJAX endpoint — process farm form, return rendered partial HTML."""
    form = FarmAnalysisForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    cd = form.cleaned_data
    try:
        result = run_analysis(
            state=cd["state"],
            crop=cd["crop"],
            land_size_acres=float(cd["land_size_acres"]),
            soil_type=cd["soil_type"],
            irrigation=cd["irrigation"],
            investment_capacity=float(cd["investment_capacity"]),
        )
        chart_data = _build_farm_chart_data(result)
    except Exception as exc:
        return JsonResponse({"success": False,
                             "errors": {"__all__": [str(exc)]}})

    # Optional history save
    try:
        from core.models import AnalysisHistory
        AnalysisHistory.objects.create(
            state=cd["state"], crop=cd["crop"],
            land_size_acres=cd["land_size_acres"],
            soil_type=cd["soil_type"], irrigation=cd["irrigation"],
            investment_capacity=cd["investment_capacity"],
            suitability_score=result["suitability"].get("suitability_score"),
            net_profit=result["financial"].get("net_profit"),
            roi=result["financial"].get("roi"),
            farmer_emotion=result["emotion"].get("farmer_emotion", ""),
        )
    except Exception:
        pass

    s = result["suitability"]
    suitability_bars = [
        (_("Climate"),     s["climate_pct"],     "text-primary"),
        (_("Soil"),        s["soil_pct"],         "text-success"),
        (_("Rainfall"),    s["rainfall_pct"],     "text-info"),
        (_("Temperature"), s["temp_pct"],         "text-warning"),
        (_("Humidity"),    s["humidity_pct"],     "text-secondary"),
        (_("Soil pH"),     s["ph_pct"],           "text-danger"),
    ]
    html = render_to_string("partials/_farm_result.html", {
        "result":           result,
        "suitability_bars": suitability_bars,
    }, request=request)
    return JsonResponse({"success": True, "html": html, "chart_data": chart_data})


@require_http_methods(["POST"])
def ajax_market(request):
    """AJAX endpoint — process market comparison form, return rendered partial HTML."""
    form = CropCompareForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors})

    cd = form.cleaned_data
    try:
        result = run_comparison(
            state=cd["state"],
            land_size_acres=float(cd["land_size_acres"]),
            investment_capacity=float(cd["investment_capacity"]),
            mode=cd["mode"],
            soil_type=cd["soil_type"],
            filter_type=cd.get("filter_type", "All"),
        )
        chart_data = {
            "labels":    result["chart_labels"],
            "profit":    result["chart_profit"],
            "stability": result["chart_stability"],
            "roi":       result["chart_roi"],
            "proj_5yr":  result["chart_5yr"],
        }
    except Exception as exc:
        return JsonResponse({"success": False,
                             "errors": {"__all__": [str(exc)]}})

    html = render_to_string("partials/_market_result.html", {
        "result": result,
    }, request=request)
    return JsonResponse({"success": True, "html": html, "chart_data": chart_data})


@require_http_methods(["GET"])
def api_soil_types(request):
    """Return soil types available for the given state as JSON."""
    state = request.GET.get("state", "").strip()
    if not state:
        return JsonResponse({"soil_types": []})
    soils = get_soil_types_for_state(state)
    return JsonResponse({"soil_types": soils})


@require_http_methods(["GET"])
def api_state_crops(request):
    """Return farm-analysis crops available for the given state as JSON."""
    state = request.GET.get("state", "").strip()
    if not state:
        return JsonResponse({"crops": []})
    crops = get_crops_for_state(state)
    return JsonResponse({"crops": crops})
