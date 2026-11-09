"""Step 5b: cricket venues for the map only (not part of the analysis).

OpenStreetMap has many cricket places that are not a measurable pitch outline: stadiums, clubs, sports centres,
pitches shared with other sports, and clubs mapped as a single point. They help readers find their own ground, so the
page shows them as a separate class, "Cricket venue (not measured)". Nothing here changes any number in the study.

Input:  data/raw/cricket_venues_a.tsv.gz (sport=cricket) and data/raw/cricket_venues_b.tsv.gz (sport lists
        containing cricket), from the QLever osm-planet endpoint: OSM id, leisure, name, first coordinate of the
        geometry (exact for points, a corner for areas).
Output: adds rows to data/pitches.json (class 12), writes data/cricket_venues.csv, and names unnamed measured grounds
        from a named venue within 150 m.
"""
import csv, gzip, json, math, os, re
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
KEEP = {"pitch", "stadium", "sports_centre", "practice_pitch", "park", "recreation_ground", "sports_hall", "batting_cage", ""}
CLUB = re.compile(r"cricket|\bcc\b|club|ground|oval|park|field|stadium|recreation|\bgreen\b|academy|pavilion", re.I)
SHOP = re.compile(r"\bshop\b|\bstore\b|direct|supplies|\bltd\b|sports line|outlet", re.I)

def rows(fn):
    with gzip.open(os.path.join(DATA, "raw", fn), "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4: continue
            m = re.search(r"/(node|way|relation)/(\d+)>", p[0]); c = re.search(r"\(+\s*(-?[\d.]+) (-?[\d.]+)", p[3])
            if not m or not c: continue
            uq = lambda s: s.strip().strip('"').replace('\\"', '"')
            yield m.group(1)[0] + m.group(2), uq(p[1]), uq(p[2]), float(c.group(1)), float(c.group(2))

D = json.load(open(os.path.join(DATA, "pitches.json")))
LAB = "Cricket venue (not measured)"
if LAB in D["classes"]:  # rerun-safe: drop earlier venue rows
    vi = D["classes"].index(LAB); D["rows"] = [r for r in D["rows"] if r[5] != vi]
else:
    D["classes"].append(LAB); vi = len(D["classes"]) - 1
K = {k: i for i, k in enumerate(D["keys"])}
have = {r[K["osm"]] for r in D["rows"]}
cr = [r for r in D["rows"] if r[K["cls"]] <= 3]
cx = np.array([r[K["lon"]] for r in cr]); cy = np.array([r[K["lat"]] for r in cr])
allx = np.array([r[K["lon"]] for r in D["rows"]]); ally = np.array([r[K["lat"]] for r in D["rows"]]); allk = [r[K["country"]] for r in D["rows"]]

def near(x, y, X, Y):
    d = np.hypot((X - x) * math.cos(math.radians(y)), Y - y) * 111.2
    i = int(np.argmin(d)) if len(d) else -1
    return i, (d[i] if i >= 0 else 1e9)

seen, out, named, dropped = set(), [], 0, {"leisure": 0, "dup": 0, "shop": 0, "near": 0}
for fn in ("cricket_venues_a.tsv.gz", "cricket_venues_b.tsv.gz"):
    for osm, lei, name, x, y in rows(fn):
        if osm in have or osm in seen: dropped["dup"] += 1; continue
        seen.add(osm)
        if lei not in KEEP: dropped["leisure"] += 1; continue
        if lei == "" and (not name or not CLUB.search(name)): dropped["leisure"] += 1; continue
        if name and SHOP.search(name): dropped["shop"] += 1; continue
        i, dkm = near(x, y, cx, cy)
        if dkm < 0.15:  # a measured cricket polygon is already there
            if name and not cr[i][K["name"]]: cr[i][K["name"]] = name; named += 1
            dropped["near"] += 1; continue
        j, dk = near(x, y, allx, ally)
        k = allk[j] if dk < 60 else -1
        out.append([round(x, 5), round(y, 5), 0, 0, 0, vi, k, name, osm, 0, lei])

# merge venues closer than 100 m to each other (a club point inside its stadium, say): keep the named / larger one
out.sort(key=lambda r: (r[7] == "", {"stadium": 0, "sports_centre": 1}.get(r[10], 2)))
kept = []
grid = {}
for r in out:
    g = (round(r[0] * 200), round(r[1] * 200)); clash = False
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for q in grid.get((g[0] + dx, g[1] + dy), []):
                if math.hypot((q[0] - r[0]) * math.cos(math.radians(r[1])), q[1] - r[1]) * 111.2 < 0.1: clash = True
    if clash: dropped["near"] += 1; continue
    grid.setdefault(g, []).append(r); kept.append(r)

D["rows"] += [r[:10] for r in kept]
json.dump(D, open(os.path.join(DATA, "pitches.json"), "w"), ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(DATA, "cricket_venues.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["osm", "osm_url", "leisure", "name", "lon", "lat", "country"])
    T = {"n": "node", "w": "way", "r": "relation"}
    for r in kept: w.writerow([r[8], f"https://www.openstreetmap.org/{T[r[8][0]]}/{r[8][1:]}", r[10], r[7], r[0], r[1], D["countries"][r[6]] if r[6] >= 0 else ""])
R = json.load(open(os.path.join(DATA, "results.json")))
R["map_venues"] = {"added": len(kept), "named_grounds": named, "dropped": dropped}
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), ensure_ascii=False, indent=1)
print("venues added", len(kept), "grounds named", named, dropped)
