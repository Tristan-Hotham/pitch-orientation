"""Shared paths and helpers for the pitch-orientation study ("Which way do cricket pitches face?").

Raw inputs (read in place, never modified):
  UK     /home/claude/newdata/raw_new9/pitches_uk.tsv.gz
         OpenStreetMap via QLever (osm2rdf): every leisure=pitch way or relation in the United Kingdom with a sport tag,
         columns ?x (OSM URL) ?sport ?name ?wkt (POLYGON or MULTIPOLYGON).
  WORLD  /home/claude/newdata/raw_new9/cricket_world.tsv.gz
         every OpenStreetMap leisure=pitch + sport=cricket way in the world, columns ?x ?name ?wkt.
  GEO    /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson (country of each pitch), Natural Earth, public domain.
  OFM    OpenFreeMap vector tiles (https://tiles.openfreemap.org), transportation layer, for the street-grid test.
Intermediates go to WORK (/home/claude/scratch/pitch-orientation), outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PO_RAW", "/home/claude/newdata/raw_new9")
UK = os.path.join(RAW, "pitches_uk.tsv.gz")
WORLD = os.path.join(RAW, "cricket_world.tsv.gz")
GEO = "/home/claude/newdata/raw/geo"
FONTS = "/home/claude/ref/fonts"
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("PO_WORK", "/home/claude/scratch/pitch-orientation")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "pitch-orientation"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

# sport groups (OSM sport tag -> group)
SPORT = {"cricket": "cricket", "soccer": "football", "tennis": "tennis", "rugby_union": "rugby", "rugby": "rugby",
         "rugby_league": "rugby", "field_hockey": "hockey", "hockey": "hockey", "netball": "netball",
         "basketball": "basketball", "bowls": "bowls", "athletics": "athletics", "running": "athletics",
         "gaelic_games": "gaelic", "baseball": "baseball", "american_football": "american_football"}
SNAME = {"cricket_strip": "Cricket strips", "cricket_square": "Cricket squares", "cricket_ground": "Cricket grounds",
         "football": "Football", "tennis": "Tennis", "rugby": "Rugby", "hockey": "Hockey", "netball": "Netball",
         "basketball": "Basketball", "bowls": "Bowls", "athletics": "Athletics tracks", "gaelic": "Gaelic games",
         "baseball": "Baseball", "american_football": "American football"}

# cricket size classes (minimum-area rectangle, metres). A strip is the 22-yard (20.12 m) rectangle of a single pitch
# with its creases (in practice 20 to 30 m long and 2.5 to 6 m wide); a square holds several strips side by side;
# a ground is the whole outfield, round or oval, usually with no axis.
STRIP_L = (17.0, 45.0)
STRIP_W = (1.5, 6.0)
SQUARE_A = (180.0, 3500.0)
GROUND_A = 6000.0
MIN_RATIO = 1.3             # elongated enough to have an axis (for whole pitches of other sports)

# Country groups for the world comparison (Natural Earth ADMIN names)
CARIB = ["Jamaica", "Trinidad and Tobago", "Barbados", "Guyana", "Antigua and Barbuda", "Saint Lucia", "Grenada",
         "Saint Vincent and the Grenadines", "Saint Kitts and Nevis", "Dominica", "Anguilla", "British Virgin Islands",
         "Montserrat", "Cayman Islands", "Bermuda", "United States Virgin Islands", "Sint Maarten", "Saint Martin"]


def jsave(obj, path, indent=None):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "deg": return f"{float(v):.1f}°"
    if f == "deg0": return f"{round(float(v))}°"
    raise ValueError(f)


def ns_dev(b):
    """angle (0..90) between an axis bearing (0..180) and the north to south line"""
    import numpy as np
    b = np.asarray(b, float) % 180
    return np.minimum(b, 180 - b)


def card_dev(b):
    """angle (0..45) between a direction and the nearest cardinal line, for squares that have no single axis"""
    import numpy as np
    b = np.asarray(b, float) % 90
    return np.minimum(b, 90 - b)
