"""Step 5: reusable data files and the compact page data.

data/pitches.csv           every measured pitch polygon: OSM id, sport, class, name, country, position, axis, size, flags
data/pitches.json          the pitches with an axis (and squares and round grounds), compact arrays for the map page
data/countries.csv         cricket by country: strips, squares, grounds
data/glare_by_latitude.csv the glare model: glare-free arc and glare minutes by pitch bearing, per degree of latitude
data/street_grid_sample.csv the street-grid sample (OSM id, class, road length, grid direction and strength)
data/places.json           towns for the page search (Natural Earth populated places, public domain)
"""
import csv
import numpy as np, pandas as pd
from common import *

R = jload(os.path.join(DATA, "results.json"))
C = pd.read_pickle(os.path.join(WORK, "cricket_final.pkl"))
U = pd.read_pickle(os.path.join(WORK, "sports.pkl"))
U0 = pd.read_pickle(os.path.join(WORK, "uk.pkl"))
M = pd.read_pickle(os.path.join(WORK, "streets_merged.pkl"))

# --- full table: UK non-cricket sports from the UK file (all measured), cricket from the world file
u_all = U0[U0.group != "cricket"].merge(U[["osm", "has_axis", "cls"]], on="osm", how="left")
u_all["cls"] = u_all.cls.fillna(u_all.group)
u_all["has_axis"] = u_all.has_axis.fillna(False).astype(bool)
u_all["country"] = "United Kingdom"
c_all = C.drop(columns=["nsd", "cd", "dup", "in_ground"], errors="ignore")
c_all["group"] = "cricket"
c_all["cls"] = "cricket_" + c_all.cls
cols = ["osm", "sport", "group", "cls", "has_axis", "name", "country", "lon", "lat", "bearing", "length", "width", "ratio", "area", "fill"]
T = pd.concat([c_all[cols], u_all[cols]], ignore_index=True)
T["ns_dev"] = ns_dev(T.bearing).round(1)
T["lon"] = T.lon.round(5); T["lat"] = T.lat.round(5)
for c_ in ("bearing", "length", "width", "area"):
    T[c_] = T[c_].round(1)
T["ratio"] = T.ratio.round(2); T["fill"] = T.fill.round(2)
T["osm_url"] = "https://www.openstreetmap.org/" + T.osm.str[0].map({"w": "way", "r": "relation"}) + "/" + T.osm.str[1:]
T.to_csv(os.path.join(DATA, "pitches.csv"), index=False, quoting=csv.QUOTE_MINIMAL)

# --- page data: class index, country index
CLS = ["cricket_strip", "cricket_square", "cricket_ground", "cricket_nets", "football", "tennis", "rugby", "hockey",
       "netball", "basketball", "gaelic", "bowls"]
LAB = ["Cricket strip", "Cricket square", "Cricket ground", "Cricket nets", "Football", "Tennis", "Rugby", "Hockey",
       "Netball", "Basketball", "Gaelic games", "Bowls"]
P = T[T.cls.isin(CLS)].copy()
P = P[P.has_axis | P.cls.isin(["cricket_square", "cricket_ground", "cricket_nets", "bowls"])]
CTRY = sorted(P.country.dropna().unique().tolist())
rows = []
for r in P.itertuples():
    ax = 1 if r.has_axis else (2 if r.cls in ("cricket_square", "bowls") else 0)       # 1 axis, 2 compass only (mod 90), 0 none
    if r.cls == "cricket_nets":
        ax = 1
    rows.append([round(r.lon, 5), round(r.lat, 5), round(r.bearing, 1), round(r.length), round(r.width), CLS.index(r.cls),
                 CTRY.index(r.country) if isinstance(r.country, str) else -1, r.name if isinstance(r.name, str) else "", r.osm, ax])
jsave({"keys": ["lon", "lat", "bearing", "length", "width", "cls", "country", "name", "osm", "axis"], "classes": LAB,
       "countries": CTRY, "rows": rows}, os.path.join(DATA, "pitches.json"))

# --- countries
cr = []
for c, v in R["by_country"].items():
    for k in ("strip", "square", "ground_axis"):
        x = v[k]
        if x.get("n"):
            cr.append({"country": c, "class": k, **{kk: x.get(kk) for kk in ("n", "ns20", "ns30", "ew20", "card10", "median_nsd", "mean_bearing", "R", "p_ns20", "glare_safe")}})
pd.DataFrame(cr).to_csv(os.path.join(DATA, "countries.csv"), index=False)

# --- glare model
gr = []
for g in R["glare"]["by_lat"]:
    row = {"lat": g["lat"], "glare_free_from": g["zero_lo"], "glare_free_to": g["zero_hi"], "worst_bearing": g["peak"]}
    for i, v in enumerate(g["curve"]):
        row[f"min_b{i * 5:03d}"] = v
    gr.append(row)
pd.DataFrame(gr).to_csv(os.path.join(DATA, "glare_by_latitude.csv"), index=False)

M[["osm", "cls", "country", "road_len", "grid", "grid_str", "bearing", "d_grid", "cd"]].rename(
    columns={"cd": "d_compass", "grid": "grid_mod90"}).to_csv(os.path.join(DATA, "street_grid_sample.csv"), index=False)

# --- places for search: Natural Earth populated places
NE = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
pl = []
for f in NE["features"]:
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"][:2]
    pl.append((p["name"], p.get("adm0name") or "", round(lon, 4), round(lat, 4), p.get("pop_max") or 0))
pl.sort(key=lambda x: -x[4])
jsave([[a, b, c, d] for a, b, c, d, _ in pl], os.path.join(DATA, "places.json"))
print("pitches.csv", len(T), "page rows", len(rows), "places", len(pl))
