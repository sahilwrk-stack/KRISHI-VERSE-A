"""
Health-check script for KRISHI-VERSE AI
Run: python _healthcheck.py
"""
import os, sys, json
# Force UTF-8 output so Hindi/script characters display in any terminal
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

os.environ["DJANGO_SETTINGS_MODULE"] = "krishiverse.settings"

import django
django.setup()

from django.test import Client

client = Client()
client.get("/")  # seed CSRF cookie
csrf = client.cookies.get("csrftoken")
token = csrf.value if csrf else "test"

OK = "\033[92m  OK  \033[0m"
FAIL = "\033[91m  FAIL\033[0m"
WARN = "\033[93m  WARN\033[0m"

errors = []

# ── 1. Page responses ──────────────────────────────────────────────────────
print("\n=== 1. Page Responses ===")
pages = [
    ("/",              200),
    ("/analysis/",     200),
    ("/hi/",           200),
    ("/hi/analysis/",  200),
    ("/pa/",           200),
    ("/ta/",           200),
]
for url, expected in pages:
    r = client.get(url)
    icon = OK if r.status_code == expected else FAIL
    if r.status_code != expected:
        errors.append(f"Page {url} returned {r.status_code}")
    print(f"{icon} GET {url} -> {r.status_code}")

# ── 2. AJAX farm endpoint ─────────────────────────────────────────────────
print("\n=== 2. AJAX Farm Endpoint ===")
farm_data = {
    "csrfmiddlewaretoken": token,
    "state": "Maharashtra",
    "crop": "Jowar",
    "soil_type": "black",
    "land_size_acres": "2.5",
    "investment_capacity": "50000",
    "irrigation": "yes",
}
r = client.post("/ajax/farm/", farm_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
if r.status_code == 200:
    data = json.loads(r.content)
    if data.get("success"):
        has_html = bool(data.get("html", "").strip())
        has_chart = "chart_data" in data
        print(f"{OK} status=200  success=True  html={has_html}  chart_data={has_chart}")
        if not has_html:
            errors.append("ajax_farm returned success but html is empty")
    else:
        print(f"{FAIL} success=False  errors={data.get('errors')}")
        errors.append(f"ajax_farm failed: {data.get('errors')}")
else:
    print(f"{FAIL} status={r.status_code}")
    errors.append(f"ajax_farm HTTP {r.status_code}")

# ── 3. AJAX market endpoint ───────────────────────────────────────────────
print("\n=== 3. AJAX Market Endpoint ===")
mkt_data = {
    "csrfmiddlewaretoken": token,
    "state": "Maharashtra",
    "soil_type": "black",
    "land_size_acres": "2.5",
    "investment_capacity": "50000",
    "mode": "balanced",
    "filter_type": "All",
}
r = client.post("/ajax/market/", mkt_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
if r.status_code == 200:
    data = json.loads(r.content)
    if data.get("success"):
        has_html = bool(data.get("html", "").strip())
        has_chart = "chart_data" in data
        result_count = len(data.get("chart_data", {}).get("labels", []))
        print(f"{OK} status=200  success=True  html={has_html}  chart_data={has_chart}  crops={result_count}")
    else:
        print(f"{FAIL} success=False  errors={data.get('errors')}")
        errors.append(f"ajax_market failed: {data.get('errors')}")
else:
    print(f"{FAIL} status={r.status_code}")
    errors.append(f"ajax_market HTTP {r.status_code}")

# ── 4. API endpoints ──────────────────────────────────────────────────────
print("\n=== 4. API Endpoints ===")
r = client.get("/api/state-crops/?state=Maharashtra")
if r.status_code == 200:
    d = json.loads(r.content)
    n = len(d.get("crops", []))
    print(f"{OK} api/state-crops  Maharashtra -> {n} crops")
    if n == 0:
        errors.append("api/state-crops returned 0 crops for Maharashtra")
else:
    print(f"{FAIL} api/state-crops status={r.status_code}")
    errors.append("api/state-crops failed")

r = client.get("/api/soil-types/?state=Maharashtra")
if r.status_code == 200:
    d = json.loads(r.content)
    n = len(d.get("soil_types", []))
    print(f"{OK} api/soil-types   Maharashtra -> {n} soil types")
else:
    print(f"{FAIL} api/soil-types status={r.status_code}")
    errors.append("api/soil-types failed")

# ── 5. i18n machinery ────────────────────────────────────────────────────
print("\n=== 5. i18n Translation Check ===")
from django.utils import translation
test_strings = {
    "en": {"Suitable": "Suitable",   "Happy": "Happy",   "High": "High"},
    "hi": {"Suitable": "उपयुक्त",     "Happy": "खुश",     "High": "उच्च"},
}
for lang, expected in test_strings.items():
    with translation.override(lang):
        from django.utils.translation import gettext as _
        for msgid, msgstr in expected.items():
            result = _(msgid)
            icon = OK if result == msgstr else WARN
            if result != msgstr and lang != "en":
                print(f"{icon} [{lang}] _('{msgid}') = '{result}'  (expected '{msgstr}')")
            else:
                print(f"{icon} [{lang}] _('{msgid}') = '{result}'")

# ── 6. Locale files present ───────────────────────────────────────────────
print("\n=== 6. Compiled Locale Files (.mo) ===")
import pathlib
locale_root = pathlib.Path("locale")
for lang_dir in sorted(locale_root.iterdir()):
    mo = lang_dir / "LC_MESSAGES" / "django.mo"
    po = lang_dir / "LC_MESSAGES" / "django.po"
    mo_ok = mo.exists()
    po_ok = po.exists()
    icon = OK if (mo_ok and po_ok) else FAIL
    if not (mo_ok and po_ok):
        errors.append(f"locale/{lang_dir.name} missing .mo or .po")
    print(f"{icon} {lang_dir.name}  po={po_ok}  mo={mo_ok}")

# ── 7. No stale agricompare references ────────────────────────────────────
print("\n=== 7. Stale 'agricompare' Reference Check ===")
import subprocess
result = subprocess.run(
    ["python", "-c",
     "import subprocess; r = subprocess.run(['rg','agricompare','--include=*.py','--include=*.html','-l'], capture_output=True, text=True); print(r.stdout.strip() or 'NONE')"],
    capture_output=True, text=True
)
hits = result.stdout.strip()
if hits == "NONE" or hits == "":
    print(f"{OK} No stale 'agricompare' references found in .py/.html files")
else:
    print(f"{WARN} Files still contain 'agricompare':\n{hits}")

# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "="*52)
if errors:
    print(f"\033[91m  {len(errors)} ISSUE(S) FOUND:\033[0m")
    for e in errors:
        print(f"    • {e}")
else:
    print(f"\033[92m  ALL CHECKS PASSED — Project is healthy!\033[0m")
print("="*52 + "\n")
