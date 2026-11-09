"""Step 1: measure the long axis of every pitch polygon in OpenStreetMap (UK, every sport; world, cricket).

For each polygon (the largest part of a multipolygon): project to a local true-north metric frame about its centroid
(equirectangular, exact enough over a few hundred metres), take the minimum-area rotated rectangle and record the
bearing of its long side folded into 0..180 degrees, length, width, ratio, area and how well the rectangle fills it
(fill = polygon area / rectangle area; an oval fills about 0.785 of its box, a rectangle 1). The country of each
world cricket pitch comes from Natural Earth 1:10m (point in polygon on the centroid).
Outputs: WORK/uk.pkl, WORK/world.pkl, WORK/geoms_uk.pkl (outline WKB for figures)
"""
import gzip, csv, sys
import numpy as np, pandas as pd
import shapely
from shapely import wkt as W
from shapely.geometry import Polygon, MultiPolygon, shape
from common import *

csv.field_size_limit(10**9)
R = 6371008.8


def unq(v):
    v = v.strip()
    if v.startswith('"'):
        v = v[1:v.rfind('"')] if '"^^' in v or '"@' in v or v.endswith('"') else v[1:]
    return v.replace('\\"', '"')


def read(path, has_sport):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(r)
        for x in r:
            url = x[0].strip("<>")
            typ, oid = url.split("/")[-2:]
            if has_sport:
                sport, name, g = unq(x[1]), unq(x[2]), x[3]
            else:
                sport, name, g = "cricket", unq(x[1]), x[2]
            g = g.split('"^^')[0].strip('"')
            if g.startswith("POINT") or g.startswith("LINESTRING"):
                continue
            rows.append(dict(osm=typ[0] + oid, sport=sport, name=name, wkt=g))
    return rows


def largest(g):
    if isinstance(g, Polygon):
        return g
    polys = []
    for p in getattr(g, "geoms", []):
        if isinstance(p, Polygon):
            polys.append(p)
        elif isinstance(p, MultiPolygon):
            polys += list(p.geoms)
    return max(polys, key=lambda p: p.area) if polys else None


def axis_of(poly):
    lon0, lat0 = poly.centroid.x, poly.centroid.y
    k = math.cos(math.radians(lat0))
    xy = np.array(poly.exterior.coords)
    X = (xy[:, 0] - lon0) * math.radians(1) * R * k
    Y = (xy[:, 1] - lat0) * math.radians(1) * R
    P = Polygon(np.c_[X, Y])
    if not P.is_valid:
        P = largest(P.buffer(0))
    area = P.area
    rect = P.minimum_rotated_rectangle
    c = np.array(rect.exterior.coords)[:4]
    e1, e2 = c[1] - c[0], c[2] - c[1]
    l1, l2 = np.hypot(*e1), np.hypot(*e2)
    e, L, Wd = (e1, l1, l2) if l1 >= l2 else (e2, l2, l1)
    brg = math.degrees(math.atan2(e[0], e[1])) % 180
    return dict(lon=round(lon0, 6), lat=round(lat0, 6), length=round(L, 1), width=round(Wd, 1),
                ratio=round(L / max(Wd, 0.1), 3), area=round(area, 1), fill=round(area / max(rect.area, 1e-6), 3),
                bearing=round(brg, 2), verts=len(xy) - 1)


def measure(rows, keep_geom=False):
    out, bad = [], 0
    for r in rows:
        try:
            p = largest(W.loads(r.pop("wkt")))
            if p is None or p.is_empty or p.area == 0:
                bad += 1; continue
            r.update(axis_of(p))
            if keep_geom:
                r["geom"] = shapely.to_wkb(shapely.set_precision(p, 1e-7))
            out.append(r)
        except Exception:
            bad += 1
    print("measured", len(out), "failed", bad, file=sys.stderr)
    return pd.DataFrame(out)


uk = measure(read(UK, True), keep_geom=True)
uk["group"] = uk.sport.map(SPORT).fillna("other")
uk[["osm", "geom"]].to_pickle(os.path.join(WORK, "geoms_uk.pkl"))
uk.drop(columns="geom").to_pickle(os.path.join(WORK, "uk.pkl"))

wd = measure(read(WORLD, False), keep_geom=True)
wd[["osm", "geom"]].to_pickle(os.path.join(WORK, "geoms_world.pkl"))
wd = wd.drop(columns="geom")
# country by point in polygon
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
cg = [shape(f["geometry"]) for f in NE["features"]]
cn = [f["properties"]["ADMIN"] for f in NE["features"]]
tree = shapely.STRtree(cg)
pts = shapely.points(wd.lon.values, wd.lat.values)
pi, ci = tree.query(pts, predicate="within")
cty = np.array([None] * len(wd), object)
cty[pi] = np.array(cn, object)[ci]
miss = np.where(pd.isna(cty))[0]
if len(miss):      # coastal pitches outside the 1:10m outline: nearest country within about 5 km
    ni = tree.query_nearest(pts[miss], max_distance=0.05)
    cty[miss[ni[0]]] = np.array(cn, object)[ni[1]]
wd["country"] = cty
print(wd.country.value_counts().head(25), file=sys.stderr)
wd.to_pickle(os.path.join(WORK, "world.pkl"))
