"""Step 2: sort the measured polygons into things that have an axis, drop duplicates, apply the hand overrides.

Cricket (world file, which includes every UK cricket way):
  nets     named "net(s)" or "practice": practice nets, kept apart
  nets     also: rectangles of strip length 6 to 12 m wide (banks of nets), and strips lying outside a mapped
           ground but within 40 m of its edge (nets beside the field); both found by checking contact sheets by eye
  strip    a single pitch: rectangle 17 to 45 m long and 1.5 to 6 m wide, at least 3.5 times as long as wide
           (most are 20 to 32 m by 2.5 to 4 m: the 22 yards between the stumps plus creases and run-ups)
  square   the block of several strips side by side: 180 to 3,500 m2, at most 60 m long, filling at least 85% of
           its rectangle. Its strips can run along either side, so only its turn from the compass (mod 90) is used
  ground   the whole field, 6,000 m2 or more: round or oval. Only grounds at least 1.2 times as long as wide are given
           an axis (the long axis of the oval), which is checked against the strips mapped inside grounds
  other    everything else (odd shapes and sizes)
Other sports (UK file): one playing area of the expected size and shape (see WIN), at least 1.3 times as long as wide.
Duplicates: two polygons of the same class whose areas overlap by 80% or more (intersection over union) are one pitch;
the larger is kept. Hand overrides: code/overrides.csv (osm id, action, reason), each checked against the outline.
Outputs: WORK/cricket.pkl (world cricket), WORK/sports.pkl (UK, all sports with an axis), data/overrides_applied.csv
"""
import sys
import numpy as np, pandas as pd, shapely
from common import *

W_ = pd.read_pickle(os.path.join(WORK, "world.pkl"))
GW = pd.read_pickle(os.path.join(WORK, "geoms_world.pkl")).set_index("osm").geom
U = pd.read_pickle(os.path.join(WORK, "uk.pkl"))
GU = pd.read_pickle(os.path.join(WORK, "geoms_uk.pkl")).set_index("osm").geom
OV = pd.read_csv(os.path.join(ROOT, "code", "overrides.csv"), comment="#", dtype=str).fillna("")

# ---- cricket classes
w = W_.copy()
nets = w.name.str.contains(r"\bnets?\b|practi[cs]e|training", case=False, regex=True)
strip = (~nets) & w.length.between(17, 45) & (w.width <= 6) & (w.width >= 1.5) & (w.ratio >= 3.5)
# wider rectangles of strip length (6 to 12 m wide) are banks of practice nets, as the contact sheets showed
widenets = (~nets) & (~strip) & w.length.between(17, 45) & w.width.between(6, 12) & (w.ratio >= 2.5)
nets = nets | widenets
square = (~nets) & (~strip) & w.area.between(*SQUARE_A) & (w.fill >= 0.85) & (w.length <= 60)
ground = (~nets) & (w.area >= GROUND_A)
w["cls"] = np.select([nets, strip, square, ground], ["nets", "strip", "square", "ground"], "other")
# a strip lying outside a mapped ground but within 40 m of its edge is a practice net beside the field, not the
# match pitch in its middle (the contact sheets showed these)
gidx = w.index[w.cls == "ground"]
gg = [shapely.from_wkb(GW[o]) for o in w.loc[gidx, "osm"]]
gt = shapely.STRtree(gg)
sidx = w.index[w.cls == "strip"]
pts = shapely.points(w.loc[sidx, "lon"].values, w.loc[sidx, "lat"].values)
inside = np.zeros(len(sidx), bool)
inside[gt.query(pts, predicate="within")[0]] = True
near = np.zeros(len(sidx), bool)
# candidates within a generous distance in degrees, then the true distance in metres in a local frame
ci, cg = gt.query(pts, predicate="dwithin", distance=40 / 111195 / 0.3)
for i, j in zip(ci, cg):
    if near[i] or inside[i]:
        continue
    lo0, la0 = w.loc[sidx[i], "lon"], w.loc[sidx[i], "lat"]
    k = math.cos(math.radians(la0))
    xy = np.array(gg[j].exterior.coords)
    ring = shapely.LineString(np.c_[(xy[:, 0] - lo0) * 111195 * k, (xy[:, 1] - la0) * 111195])
    near[i] = ring.distance(shapely.Point(0, 0)) <= 40
edge = near & ~inside
w.loc[sidx[edge], "cls"] = "nets"
w["nets_rule"] = np.where(w.name.str.contains(r"\bnets?\b|practi[cs]e|training", case=False, regex=True), "name",
                 np.where(widenets, "width", np.where(w.index.isin(sidx[edge]), "edge", "")))
w["has_axis"] = (w.cls == "strip") | ((w.cls == "ground") & (w.ratio >= 1.2))


def dedupe(df, G, by):
    """drop the smaller of any two polygons in the same class overlapping by IoU >= 0.8"""
    drop = set()
    for c, d in df.groupby(by):
        geoms = [shapely.from_wkb(G[o]) for o in d.osm]
        tree = shapely.STRtree(geoms)
        a, b = tree.query(geoms, predicate="intersects")
        ar = np.array([g.area for g in geoms])
        for i, j in zip(a, b):
            if i >= j:
                continue
            inter = geoms[i].intersection(geoms[j]).area
            iou = inter / (ar[i] + ar[j] - inter)
            if iou >= 0.8:
                drop.add(d.osm.iloc[i] if ar[i] < ar[j] else d.osm.iloc[j])
    return drop


dupw = dedupe(w[w.cls != "other"], GW, "cls")
w["dup"] = w.osm.isin(dupw)
print("cricket duplicates", len(dupw), file=sys.stderr)

# ---- other sports (UK)
WIN = {  # group: (length range m, width range m, ratio range)
    "football": ((30, 130), (15, 95), (1.25, 2.2)),
    "rugby": ((60, 160), (35, 100), (1.3, 2.3)),
    "hockey": ((40, 110), (20, 70), (1.3, 2.2)),
    "gaelic": ((80, 170), (45, 100), (1.3, 2.2)),
    "tennis": ((22, 42), (10, 21), (1.6, 2.6)),
    "netball": ((24, 40), (12, 22), (1.6, 2.6)),
    "basketball": ((20, 40), (10, 24), (1.4, 2.4)),
}
u = U[U.group.isin(list(WIN) + ["bowls"])].copy()
ok = np.zeros(len(u), bool)
for g, (L, Wd, r) in WIN.items():
    m = (u.group == g) & u.length.between(*L) & u.width.between(*Wd) & u.ratio.between(*r)
    ok |= m.values
u["has_axis"] = ok
u["cls"] = u.group
dupu = dedupe(u[u.has_axis], GU, "cls")
u["dup"] = u.osm.isin(dupu)
print("UK sport duplicates", len(dupu), file=sys.stderr)
# UK cricket from the world file, so that both tables use the same classes
wuk = w[w.country == "United Kingdom"].copy()

# ---- hand overrides
log = []
for r in OV.itertuples():
    for df in (w, u):
        m = df.osm == r.osm
        if not m.any():
            continue
        if r.action == "drop":
            df.loc[m, "has_axis"] = False
            df.loc[m, "cls"] = "dropped"
        elif r.action.startswith("cls="):
            df.loc[m, "cls"] = r.action[4:]
            df.loc[m, "has_axis"] = r.action[4:] == "strip"
        log.append(dict(osm=r.osm, action=r.action, reason=r.reason, name=df.loc[m, "name"].iloc[0]))
pd.DataFrame(log).to_csv(os.path.join(DATA, "overrides_applied.csv"), index=False)
print("overrides applied", len(log), file=sys.stderr)

w = w[~w.dup]
u = u[~u.dup]
w["nsd"] = ns_dev(w.bearing); w["cd"] = card_dev(w.bearing)
u["nsd"] = ns_dev(u.bearing); u["cd"] = card_dev(u.bearing)
w.to_pickle(os.path.join(WORK, "cricket.pkl"))
u.to_pickle(os.path.join(WORK, "sports.pkl"))
print(w.cls.value_counts().to_dict(), file=sys.stderr)
print(u[u.has_axis].cls.value_counts().to_dict(), file=sys.stderr)
