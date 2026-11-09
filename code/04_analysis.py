"""Step 4: every number in the study, into data/results.json.

Chance: a direction drawn at random lies within 20 degrees of the north to south line 40/180 = 22.2% of the time, and
within 30 degrees 33.3%. Shares are tested against chance with an exact binomial test. The axial mean of a set of
bearings (0..180) doubles the angles, averages the unit vectors and halves the result; its length R (0 to 1) measures
how tightly they agree.
"""
import sys
import numpy as np, pandas as pd, shapely
from scipy.stats import binomtest
from common import *
from sunmodel import glare, season_days, ALT_MAX, HALF, PLAY

C = pd.read_pickle(os.path.join(WORK, "cricket.pkl"))
U = pd.read_pickle(os.path.join(WORK, "sports.pkl"))
W0 = pd.read_pickle(os.path.join(WORK, "world.pkl"))
U0 = pd.read_pickle(os.path.join(WORK, "uk.pkl"))
ST = pd.read_pickle(os.path.join(WORK, "streets.pkl"))
OV = pd.read_csv(os.path.join(DATA, "overrides_applied.csv")) if os.path.getsize(os.path.join(DATA, "overrides_applied.csv")) > 2 else pd.DataFrame()
C.loc[C.country.isin(CARIB), "country"] = "Caribbean"
R = {}
R["chance20"] = round(40 / 180 * 100, 1)
R["chance30"] = round(60 / 180 * 100, 1)


def amean(b):
    a = np.radians(np.asarray(b, float) * 2)
    c, s = np.cos(a).mean(), np.sin(a).mean()
    m = (math.degrees(math.atan2(s, c)) / 2) % 180
    return round(m if m <= 90 else m - 180, 1), round(float(math.hypot(c, s)), 3)


def summ(d, axis=True):
    n = len(d)
    if n == 0:
        return {"n": 0}
    k20 = int((d.nsd <= 20).sum())
    out = {"n": n, "ns20": round(100 * k20 / n, 1), "ns30": round(100 * (d.nsd <= 30).mean(), 1),
           "ew20": round(100 * (d.nsd >= 70).mean(), 1), "card10": round(100 * (d.cd <= 10).mean(), 1),
           "median_nsd": round(float(d.nsd.median()), 1),
           "p_ns20": float(f"{binomtest(k20, n, 40 / 180, alternative='greater').pvalue:.3g}")}
    m, r = amean(d.bearing)
    out.update(mean_bearing=m, R=r)
    return out


# ---------------- counts
R["n"] = {"uk_polygons": len(U0), "world_cricket": len(W0), "uk_cricket": int((W0.country == "United Kingdom").sum()),
          "countries_cricket": int(W0.country.nunique()), "dup_cricket": int(len(W0) - len(C)),
          "overrides": len(OV)}
for c in ["strip", "square", "ground", "nets", "other", "dropped"]:
    R["n"]["cricket_" + c] = int((C.cls == c).sum())
for k in ("name", "width", "edge"):
    R["n"]["nets_" + k] = int((C.nets_rule == k).sum())
R["n"]["strip_candidates"] = int(R["n"]["nets_width"] + R["n"]["nets_edge"] + (C.cls == "strip").sum())
R["n"]["nets_moved_pc"] = round(100 * (R["n"]["nets_width"] + R["n"]["nets_edge"]) / R["n"]["strip_candidates"], 1)
R["n"]["ground_axis"] = int(((C.cls == "ground") & (C.ratio >= 1.2)).sum())
R["n"]["ground_round"] = int(((C.cls == "ground") & (C.ratio < 1.2)).sum())
R["n"]["strip_countries"] = int(C[C.cls == "strip"].country.nunique())
R["n"]["strip_uk"] = int(((C.cls == "strip") & (C.country == "United Kingdom")).sum())
R["n"]["other_sports_axis"] = int(U.has_axis.sum())
R["n"]["uk_by_sport_raw"] = U0.group.value_counts().to_dict()
R["n"]["strip_median_length"] = round(float(C[C.cls == "strip"].length.median()), 1)
R["n"]["strip_median_width"] = round(float(C[C.cls == "strip"].width.median()), 1)

# ---------------- cricket classes overall and UK sports
S = C[C.cls == "strip"]
R["strips_world"] = summ(S)
UKC = C[C.country == "United Kingdom"]
R["uk"] = {"strip": summ(UKC[UKC.cls == "strip"]), "square": summ(UKC[UKC.cls == "square"]),
           "ground_axis": summ(UKC[(UKC.cls == "ground") & (UKC.ratio >= 1.2)]), "nets": summ(UKC[UKC.cls == "nets"])}
for g in ["football", "tennis", "rugby", "hockey", "netball", "basketball", "gaelic"]:
    R["uk"][g] = summ(U[(U.cls == g) & U.has_axis])
bw = U[U.cls == "bowls"]
R["uk"]["bowls"] = {"n": len(bw), "card10": round(100 * (bw.cd <= 10).mean(), 1), "median_ratio": round(float(bw.ratio.median()), 3)}
R["uk"]["all_other_sports"] = summ(U[U.has_axis & ~U.cls.isin(["tennis"])])
# the long side of a UK square runs across its strips: share whose long side is within 20 degrees of east to west
R["uk"]["square"]["long_side_ew20"] = R["uk"]["square"]["ew20"]

# ---------------- by country (strips; squares as compass alignment; grounds as a proxy)
countries = ["United Kingdom", "Australia", "New Zealand", "India", "South Africa", "Pakistan", "Sri Lanka", "Bangladesh",
             "Caribbean", "United States of America", "Canada", "Samoa", "Ireland", "Netherlands"]
R["by_country"] = {}
for c in countries:
    d = C[C.country == c]
    R["by_country"][c] = {"strip": summ(d[d.cls == "strip"]), "square": summ(d[d.cls == "square"]),
                          "ground_axis": summ(d[(d.cls == "ground") & (d.ratio >= 1.2)]),
                          "all_cricket": int(len(d)), "median_lat": round(float(d.lat.median()), 1)}
R["strip_countries_20"] = [c for c in countries if R["by_country"][c]["strip"]["n"] >= 20]

# ---------------- latitude bands (strips)
bands = [(-50, -40), (-40, -35), (-35, -30), (-30, -20), (-20, 0), (0, 25), (25, 45), (45, 52), (52, 61)]
R["lat_bands"] = []
for a, b in bands:
    d = S[(S.lat >= a) & (S.lat < b)]
    R["lat_bands"].append({"lat0": a, "lat1": b, **summ(d)})
# hemisphere
R["north"] = summ(S[S.lat >= 0]); R["south"] = summ(S[S.lat < 0])

# ---------------- the glare model
lats = list(range(-46, 61, 1))
G = []
for la in lats:
    g = glare(la)
    z = np.where(g == 0)[0]
    zz = [int(b if b < 90 else b - 180) for b in z]
    G.append({"lat": la, "zero_lo": min(zz), "zero_hi": max(zz), "peak": int(g.argmax()), "glare_ew": int(g[90]),
              "glare_ns": int(g[0]), "glare_max": int(g.max()), "curve": [int(v) for v in g[::5]]})
R["glare"] = {"alt_max": ALT_MAX, "half": HALF, "play_from": PLAY[0], "by_lat": G}
gz = {x["lat"]: x for x in G}
S = S.assign(glat=np.clip(np.round(S.lat), -46, 60).astype(int))
S["in_safe"] = [(lo <= (b if b < 90 else b - 180) <= hi) for b, lo, hi in zip(S.bearing, S.glat.map(lambda v: gz[v]["zero_lo"]), S.glat.map(lambda v: gz[v]["zero_hi"]))]
R["glare"]["strips_safe"] = round(100 * S.in_safe.mean(), 1)
R["glare"]["uk_lat52"] = dict(gz[52], glare_ew_h=round(gz[52]["glare_ew"] / 60))
R["glare"]["lat_minus34"] = gz[-34]
R["glare"]["lat_minus41"] = gz[-41]
R["glare"]["lat_18"] = gz[18]
for c in R["strip_countries_20"]:
    d = S[S.country == c]
    R["by_country"][c]["strip"]["glare_safe"] = round(100 * d.in_safe.mean(), 1)
# a random bearing's chance of the glare-free arc at the UK latitude
R["glare"]["uk_safe_chance"] = round(100 * (gz[52]["zero_hi"] - gz[52]["zero_lo"] + 1) / 180, 1)

# ---------------- validation: strips mapped inside grounds
GW = pd.read_pickle(os.path.join(WORK, "geoms_world.pkl")).set_index("osm").geom
Gd = C[C.cls == "ground"]
tree = shapely.STRtree([shapely.from_wkb(GW[o]) for o in Gd.osm])
pi, gi = tree.query(shapely.points(C[C.cls == "strip"].lon, C[C.cls == "strip"].lat), predicate="within")
Sx = C[C.cls == "strip"].iloc[pi]; Gx = Gd.iloc[gi]
dd = np.abs((Sx.bearing.values - Gx.bearing.values + 90) % 180 - 90)
el = Gx.ratio.values >= 1.2
R["validation"] = {"strips_in_grounds": int(len(pi)), "elongated": int(el.sum()),
                   "elongated_within20": round(100 * (dd[el] <= 20).mean(), 1) if el.any() else None,
                   "elongated_median_diff": round(float(np.median(dd[el])), 1) if el.any() else None,
                   "round": int((~el).sum()), "round_within20": round(100 * (dd[~el] <= 20).mean(), 1) if (~el).any() else None}
C["in_ground"] = False
C.loc[Sx.index, "in_ground"] = True

# ---------------- streets
M = ST.drop(columns="cls").merge(pd.concat([C[["osm", "cls", "bearing", "nsd", "cd", "country", "lat", "lon"]], U[["osm", "cls", "bearing", "nsd", "cd", "lat", "lon"]].assign(country="United Kingdom")]).drop_duplicates("osm"), on="osm")
M = M[M.cls.isin(["strip", "square", "football", "tennis", "rugby", "netball", "basketball"])]
M["d_grid"] = np.abs((M.bearing - M.grid + 45) % 90 - 45)          # 0..45: off the street grid (either way)
M["grid_off"] = card_dev(M.grid)                                     # how far the grid itself turns from the compass
URB = 1500.0                                                         # m of road within 200 m: a built-up setting
R["streets_sample"] = {"n": len(M), "urban_threshold_m": URB, "radius_m": 200, "grid_off_min": 15}
R["streets"] = {}
for key, sel in [("strip", M.cls == "strip"), ("square", M.cls == "square"), ("strip_uk", (M.cls == "strip") & (M.country == "United Kingdom")),
                 ("strip_aus", (M.cls == "strip") & (M.country == "Australia")),
                 ("football", M.cls == "football"), ("tennis", M.cls == "tennis"), ("rugby", M.cls == "rugby"),
                 ("netball", M.cls == "netball"), ("basketball", M.cls == "basketball")]:
    d = M[sel & (M.road_len >= URB) & (M.grid_off >= 15)]
    a = M[sel & (M.grid_off >= 15) & M.grid.notna()]
    R["streets"][key] = {"n_urban": len(d), "urban_closer_to_grid": round(100 * (d.d_grid < d.cd).mean(), 1) if len(d) else None,
                         "urban_within5_grid": round(100 * (d.d_grid <= 5).mean(), 1) if len(d) else None,
                         "urban_within5_compass": round(100 * (d.cd <= 5).mean(), 1) if len(d) else None,
                         "n_all": len(a), "all_closer_to_grid": round(100 * (a.d_grid < a.cd).mean(), 1) if len(a) else None,
                         "n_sample": int(sel.sum()), "median_road_len": round(float(M[sel].road_len.median()), 0)}
M.to_pickle(os.path.join(WORK, "streets_merged.pkl"))

# ---------------- examples for the text (named UK strips), and per-country lists for the page
S2 = C[(C.cls == "strip")].copy()
R["examples"] = {}
ex = S2[(S2.country == "United Kingdom")].copy()
ex["abs"] = ex.nsd
R["examples"]["uk_ns"] = ex.sort_values("nsd").head(5)[["osm", "name", "lon", "lat", "bearing", "length", "width"]].to_dict("records")
R["examples"]["uk_ew"] = ex.sort_values("nsd", ascending=False).head(5)[["osm", "name", "lon", "lat", "bearing", "length", "width"]].to_dict("records")
C.to_pickle(os.path.join(WORK, "cricket_final.pkl"))
jsave(R, os.path.join(DATA, "results.json"), indent=1)
print(json.dumps({k: R[k] for k in ["n", "strips_world", "validation", "streets", "north", "south"]}, indent=0)[:6000])
for c in R["strip_countries_20"]:
    print(c, R["by_country"][c]["strip"])
for k, v in R["uk"].items():
    print(k, v)
print(R["glare"]["uk_lat52"], R["glare"]["strips_safe"])
