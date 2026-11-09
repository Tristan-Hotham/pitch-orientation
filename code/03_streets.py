"""Step 3: the street grid around a sample of pitches, as a rival explanation for their direction.

Sample (seed 7): every cricket strip, square and net in the world file, and random samples of UK football pitches, tennis
courts, rugby pitches, netball and basketball courts (sizes in N_SPORT). For each, the OpenFreeMap vector tiles at
zoom 14 that its 200 m circle touches are read, and the road centrelines (motorway to service roads; paths and tracks
left out) within 200 m are collected:
  road_len   metres of road within 200 m (an urban density measure)
  grid       the length-weighted dominant road direction, folded to 0..90 degrees (roads at right angles agree)
  grid_str   its strength (0 = roads in all directions, 1 = one direction only)
For cricket strips the roads and building outlines within 250 m are also kept (local metres) for the contact sheets
used to check the strips by eye. Tiles are read into memory only and never written to disk.
Outputs: WORK/streets.pkl, WORK/context.pkl
"""
import sys, time, urllib.request
import numpy as np, pandas as pd
import mapbox_vector_tile as mvt
from concurrent.futures import ThreadPoolExecutor
from common import *

Z = 14
RAD = 200.0
ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary", "minor", "service", "busway"}
UA = {"User-Agent": "pitch-orientation-study/1.0 (research; maps.tristanhotham.com)"}
N_SPORT = {"football": 2500, "tennis": 2500, "rugby": 800, "netball": 600, "basketball": 600}
tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
URL = tj["tiles"][0]
n = 2 ** Z

C = pd.read_pickle(os.path.join(WORK, "cricket.pkl"))
U = pd.read_pickle(os.path.join(WORK, "sports.pkl"))
S = [C[C.cls.isin(["strip", "square", "nets"])].assign(src="cricket")]   # nets too, so a later class change needs no refetch
for g, k in N_SPORT.items():
    d = U[(U.cls == g) & U.has_axis]
    S.append(d.sample(n=min(k, len(d)), random_state=7).assign(src="uk"))
S = pd.concat(S, ignore_index=True)


def tile_xy(lon, lat):
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


need = []
for r in S.itertuples():
    dlat = 260 / 111195
    dlon = dlat / math.cos(math.radians(r.lat))
    ts = set()
    for lo in (r.lon - dlon, r.lon, r.lon + dlon):
        for la in (r.lat - dlat, r.lat, r.lat + dlat):
            x, y = tile_xy(lo, la)
            ts.add((int(x), int(y)))
    need.append(ts)
tiles = sorted(set().union(*need))
print("sample", len(S), "tiles", len(tiles), file=sys.stderr)


def lines_of(lay, x, y, keep):
    out = []
    if not lay:
        return out
    ext = lay["extent"]
    for f in lay["features"]:
        if not keep(f):
            continue
        g = f["geometry"]
        t = g["type"]
        if t == "LineString":
            parts = [g["coordinates"]]
        elif t == "MultiLineString":
            parts = g["coordinates"]
        elif t == "Polygon":
            parts = [g["coordinates"][0]]
        elif t == "MultiPolygon":
            parts = [p[0] for p in g["coordinates"]]
        else:
            continue
        for ln in parts:
            a = np.array(ln, float)
            if len(a) < 2:
                continue
            lon = (x + a[:, 0] / ext) / n * 360 - 180
            lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * (y + a[:, 1] / ext) / n))))
            out.append(np.c_[lon, lat])
    return out


def fetch(t):
    x, y = t
    for k in range(5):
        try:
            req = urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA)
            b = urllib.request.urlopen(req, timeout=60).read()
            d = mvt.decode(b, default_options={"y_coord_down": True})
            roads = lines_of(d.get("transportation"), x, y, lambda f: f["properties"].get("class") in ROADS and f["geometry"]["type"] in ("LineString", "MultiLineString"))
            blds = lines_of(d.get("building"), x, y, lambda f: f["geometry"]["type"] in ("Polygon", "MultiPolygon"))
            return t, (roads, blds)
        except Exception:
            time.sleep(2 + 3 * k)
    print("failed", t, file=sys.stderr)
    return t, None


T = {}
t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    for j, (t, v) in enumerate(ex.map(fetch, tiles)):
        T[t] = v
        if j % 1000 == 0:
            print(j, round(time.time() - t0), file=sys.stderr)

R = 6371008.8
out, ctx = [], {}
for (i, r), ts in zip(S.iterrows(), need):
    if any(T.get(t) is None for t in ts):
        continue
    k = math.cos(math.radians(r.lat))
    to_xy = lambda s: np.c_[(s[:, 0] - r.lon) * math.radians(1) * R * k, (s[:, 1] - r.lat) * math.radians(1) * R]
    L, ang = 0.0, []
    keep_roads, keep_blds = [], []
    seen = set()
    for t in ts:
        roads, blds = T[t]
        for s in roads:
            XY = to_xy(s)
            if np.hypot(XY[:, 0], XY[:, 1]).min() > 400:
                continue
            if r.cls in ("strip", "nets"):
                keep_roads.append(np.round(XY).astype(np.int16) if np.abs(XY).max() < 30000 else None)
            for (a0, b0), (a1, b1) in zip(XY[:-1], XY[1:]):
                key = (round(a0), round(b0), round(a1), round(b1))
                if key in seen:          # the same segment from the buffer of a neighbouring tile
                    continue
                seen.add(key)
                dx, dy = a1 - a0, b1 - b0
                ln = math.hypot(dx, dy)
                if ln < 0.5:
                    continue
                tpar = max(0, min(1, -(a0 * dx + b0 * dy) / (ln * ln)))
                if math.hypot(a0 + tpar * dx, b0 + tpar * dy) > RAD:
                    continue
                L += ln
                ang.append((math.degrees(math.atan2(dx, dy)) % 180, ln))
        if r.cls in ("strip", "nets"):
            for s in blds:
                XY = to_xy(s)
                if np.hypot(XY[:, 0], XY[:, 1]).min() < 260:
                    keep_blds.append(np.round(XY).astype(np.int16))
    if ang:
        b = np.array(ang)
        a4 = np.radians((b[:, 0] % 90) * 4)
        Cc, Sn = (b[:, 1] * np.cos(a4)).sum(), (b[:, 1] * np.sin(a4)).sum()
        grid = math.degrees(math.atan2(Sn, Cc)) / 4 % 90
        strength = math.hypot(Cc, Sn) / b[:, 1].sum()
    else:
        grid, strength = np.nan, np.nan
    out.append(dict(osm=r.osm, cls=r.cls, src=r.src, road_len=round(L, 1), grid=round(grid, 2) if ang else np.nan,
                    grid_str=round(strength, 3) if ang else np.nan))
    if r.cls in ("strip", "nets"):
        ctx[r.osm] = ([x for x in keep_roads if x is not None], keep_blds)
pd.DataFrame(out).to_pickle(os.path.join(WORK, "streets.pkl"))
pd.to_pickle(ctx, os.path.join(WORK, "context.pkl"))
print("done", len(out), round(time.time() - t0), file=sys.stderr)
