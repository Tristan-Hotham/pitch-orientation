"""Checks of the whole set of cricket strips (not a sample), and contact sheets for checking strips by eye.

1. context: is each strip inside or within 150 m of another cricket polygon (ground, square, other)? Strips with no
   cricket around them are listed, since they may be nets, a long-jump runway or a mistagged path.
2. clusters: strips within 120 m of each other are one ground; the per-ground share (one vote per ground, its axial
   mean) checks that big grounds with many strips do not drive the result.
3. contact sheets (WORK/sheets/*.png): every strip drawn at the same scale with the OpenFreeMap roads and buildings
   around it and the other cricket polygons, 60 to a page, for checking by eye. Not part of the release.
Output: WORK/audit.json, data/strip_checks.csv
"""
import sys
import numpy as np, pandas as pd, shapely
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

C = pd.read_pickle(os.path.join(WORK, "cricket_final.pkl"))
GW = pd.read_pickle(os.path.join(WORK, "geoms_world.pkl")).set_index("osm").geom
ctx = pd.read_pickle(os.path.join(WORK, "context.pkl"))
S = C[C.cls == "strip"].copy()
O = C[C.cls.isin(["ground", "square", "other", "nets"])]
og = [shapely.from_wkb(GW[o]) for o in O.osm]
tree = shapely.STRtree(og)
k = np.cos(np.radians(S.lat.values))
pts = shapely.points(S.lon.values, S.lat.values)
near = np.zeros(len(S), bool)
inside = np.zeros(len(S), bool)
i, j = tree.query(pts, predicate="dwithin", distance=150 / 111195 / 0.3)
for a, b in zip(i, j):      # candidates in degrees, then the true distance in metres in a local frame
    if near[a]:
        continue
    xy0 = np.array(og[b].exterior.coords)
    P = shapely.Polygon(np.c_[(xy0[:, 0] - S.lon.values[a]) * 111195 * k[a], (xy0[:, 1] - S.lat.values[a]) * 111195])
    near[a] = P.buffer(0).distance(shapely.Point(0, 0)) <= 150
i2, _ = tree.query(pts, predicate="within")
inside[i2] = True
S["near_cricket"] = near
S["in_cricket"] = inside
# clusters of strips: single linkage within 120 m
xy = np.c_[S.lon.values * 111195 * k, S.lat.values * 111195]
lab = -np.ones(len(S), int)
cur = 0
from scipy.spatial import cKDTree
kd = cKDTree(xy)
for s in range(len(S)):
    if lab[s] >= 0:
        continue
    st = [s]; lab[s] = cur
    while st:
        q = st.pop()
        for t in kd.query_ball_point(xy[q], 120):
            if lab[t] < 0:
                lab[t] = cur; st.append(t)
    cur += 1
S["cluster"] = lab


def amean(b):
    a = np.radians(np.asarray(b, float) * 2)
    return (math.degrees(math.atan2(np.sin(a).mean(), np.cos(a).mean())) / 2) % 180


cl = S.groupby("cluster").agg(n=("osm", "size"), bearing=("bearing", amean), country=("country", "first"))
cl["nsd"] = ns_dev(cl.bearing)
A = {"strips": len(S), "with_cricket_nearby": int(near.sum()), "inside_cricket": int(inside.sum()),
     "isolated": int((~near).sum()), "clusters": int(len(cl)), "clusters_multi": int((cl.n > 1).sum()),
     "cluster_ns20": round(100 * (cl.nsd <= 20).mean(), 1),
     "isolated_ns20": round(100 * (ns_dev(S[~S.near_cricket].bearing) <= 20).mean(), 1),
     "near_ns20": round(100 * (ns_dev(S[S.near_cricket].bearing) <= 20).mean(), 1)}
for c in ["United Kingdom", "Australia", "New Zealand"]:
    d = cl[cl.country == c]
    A[f"cluster_ns20_{c}"] = round(100 * (d.nsd <= 20).mean(), 1)
    A[f"clusters_{c}"] = len(d)
jsave(A, os.path.join(WORK, "audit.json"), indent=1)
RR = jload(os.path.join(DATA, "results.json"))
RR["audit"] = A
RR["audit"]["sheet_sample_1"] = 120; RR["audit"]["sheet_nets_1"] = 10       # first look by eye, before the nets rules
RR["audit"]["sheet_sample_2"] = 60; RR["audit"]["sheet_doubtful_2"] = 1     # second look, after them (see NOTES.md)
jsave(RR, os.path.join(DATA, "results.json"), indent=1)
S[["osm", "name", "country", "lon", "lat", "bearing", "length", "width", "near_cricket", "in_cricket", "cluster"]].to_csv(
    os.path.join(DATA, "strip_checks.csv"), index=False)
print(A)

if os.environ.get("SHEETS"):
    out = os.path.join(WORK, "sheets"); os.makedirs(out, exist_ok=True)
    order = S.sort_values(["country", "lat"]).osm.tolist()
    sel = os.environ.get("SHEETS")
    if sel != "all":
        rng = np.random.default_rng(3)
        order = list(rng.choice(order, size=min(int(sel), len(order)), replace=False))
    R = 6371008.8
    for p0 in range(0, len(order), 60):
        fig, axs = plt.subplots(6, 10, figsize=(20, 12.5))
        for ax, o in zip(axs.ravel(), order[p0:p0 + 60]):
            r = S[S.osm == o].iloc[0]
            kk = math.cos(math.radians(r.lat))
            roads, blds = ctx.get(o, ([], []))
            for b in blds:
                ax.fill(b[:, 0], b[:, 1], color="#bbbbbb", lw=0)
            for rd in roads:
                ax.plot(rd[:, 0], rd[:, 1], color="#888", lw=0.8)
            near_o = O[(np.abs(O.lon - r.lon) < 0.004) & (np.abs(O.lat - r.lat) < 0.003)]
            for oo in near_o.osm:
                g = shapely.from_wkb(GW[oo])
                a = np.array(g.exterior.coords)
                ax.plot((a[:, 0] - r.lon) * math.radians(1) * R * kk, (a[:, 1] - r.lat) * math.radians(1) * R, color="#2a7", lw=0.8)
            g = shapely.from_wkb(GW[o])
            a = np.array(g.exterior.coords)
            ax.fill((a[:, 0] - r.lon) * math.radians(1) * R * kk, (a[:, 1] - r.lat) * math.radians(1) * R, color="#d22", lw=0)
            ax.set_xlim(-120, 120); ax.set_ylim(-120, 120); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"{o} {r.country[:10]} {r.bearing:.0f}", fontsize=6.5)
        fig.tight_layout()
        fig.savefig(os.path.join(out, f"sheet_{p0 // 60:03d}.png"), dpi=70)
        plt.close(fig)
    print("sheets", (len(order) + 59) // 60)
