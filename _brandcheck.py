import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agriverse.settings')
import django; django.setup()

from django.test import Client
from django.utils import translation

c = Client()
OK = '[OK]'; FAIL = '[FAIL]'

print('=== 1. Page Response Tests ===')
for url, name in [('/', 'Homepage'), ('/analysis/', 'Analysis'), ('/hi/', 'Hindi Home'), ('/hi/analysis/', 'Hindi Analysis')]:
    r = c.get(url)
    status = OK if r.status_code == 200 else FAIL
    print(f'  {status} {name} ({url}) -> {r.status_code}')

print()
print('=== 2. Brand Name Check in HTML ===')
r = c.get('/')
html = r.content.decode('utf-8')
kv = 'AGRIVERSE' in html
ac = 'AgriCompare' in html
agri = 'AGRICOMPARE' in html
if kv and not ac and not agri:
    print(f'  {OK} Homepage has AGRIVERSE AI, no old brand')
else:
    print(f'  {FAIL} AGRIVERSE={kv}  AgriCompare={ac}  AGRICOMPARE={agri}')

print()
print('=== 3. Hindi Translation Test ===')
with translation.override('hi'):
    from django.utils.translation import gettext as _
    tests = [
        ('Suitable', 'उपयुक्त'),
        ('Happy', 'खुश'),
        ('AGRIVERSE AI', 'कृषि-वर्स एआई'),
        ('Smart Farming Intelligence Platform', 'स्मार्ट कृषि बुद्धिमत्ता मंच'),
        ('Crop Suitability', 'फसल उपयुक्तता'),
        ('Market Intelligence', 'बाज़ार बुद्धिमत्ता'),
        ('How It Works', 'यह कैसे काम करता है'),
        ('Crop Comparison Results', 'फसल तुलना परिणाम'),
    ]
    for msgid, expected in tests:
        result = _(msgid)
        status = OK if result == expected else FAIL
        print(f'  {status} "{msgid}" -> "{result}"')

print()
print('=== 4. Locale .mo Files ===')
import pathlib
for lang in ['hi','bn','kn','ml','mr','pa','ta','te']:
    mo = pathlib.Path(f'locale/{lang}/LC_MESSAGES/django.mo')
    exists = mo.exists()
    size = mo.stat().st_size if exists else 0
    status = OK if exists and size > 100 else FAIL
    print(f'  {status} {lang}: {size} bytes')

print()
print('=== 5. Old Brand Reference Check ===')
import glob
old_brand_found = []
for pattern in ['templates/**/*.html', 'core/**/*.py', 'engines/**/*.py', 'agriverse/**/*.py']:
    for f in glob.glob(pattern, recursive=True):
        try:
            with open(f, encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
            for bad in ['AgriCompare', 'AGRICOMPARE']:
                if bad in content:
                    old_brand_found.append(f'{f} (contains {bad})')
        except:
            pass
if old_brand_found:
    print(f'  {FAIL} Old brand found:')
    for x in old_brand_found:
        print(f'    - {x}')
else:
    print(f'  {OK} Zero old AgriCompare/AGRICOMPARE references in templates & code')

print()
print('=== 6. AJAX Endpoint Test ===')
r = c.post('/ajax/farm/', {
    'state': 'Maharashtra', 'crop': 'Jowar', 'soil_type': 'black',
    'land_size_acres': '5', 'investment_capacity': '50000', 'irrigation': 'yes'
})
if r.status_code == 200:
    import json
    d = json.loads(r.content)
    status = OK if d.get('success') else FAIL
    print(f'  {status} Farm AJAX -> success={d.get("success")}')
else:
    print(f'  {FAIL} Farm AJAX -> HTTP {r.status_code}')

print()
print('All checks done!')
