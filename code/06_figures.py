"""Step 6: figures for the blog (release/blog/b_*.png, 1800 px wide), the paper (release/paper/f_*.png) and the page (img/)."""
import shapely
import pandas as pd
from figstyle import *

R = jload(os.path.join(DATA, "results.json"))
C = pd.read_pickle(os.path.join(WORK, "cricket_final.pkl"))
U = pd.read_pickle(os.path.join(WORK, "sports.pkl"))
M = pd.read_pickle(os.path.join(WORK, "streets_merged.pkl"))
GW = pd.read_pickle(os.path.join(WORK, "geoms_world.pkl")).set_index("osm").geom
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper"); IMG = os.path.join(ROOT, "img")
for d in (BLOG, PAP, IMG):
    os.makedirs(d, exist_ok=True)
SRC = "Data: OpenStreetMap contributors (ODbL). Analysis: Tristan Hotham, maps.tristanhotham.com/pitch-orientation"
S = C[C.cls == "strip"]


def out(fig, name, paper=True):
    dpi = 1800 / fig.get_figwidth()
    fig.savefig(os.path.join(BLOG, f"b_{name}.png"), dpi=dpi, facecolor=fig.get_facecolor())
    if paper:
        fig.savefig(os.path.join(PAP, f"f_{name}.png"), dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def head(fig, t, sub, y=0.965):
    fig.text(0.03, y, t, fontproperties=DISP, fontsize=27, va="top")
    fig.text(0.03, y - 0.075 * 6.5 / fig.get_figheight(), sub, fontproperties=SERP, fontsize=13.5, color=MUT, va="top")


# ---------- 1. map: Britain, south-east Australia, New Zealand
def fig_map():
    fig = plt.figure(figsize=(14, 7.0)); paper(fig)
    head(fig, "Every cricket strip, drawn along its length",
         f"{R['n']['cricket_strip']:,} single pitches from OpenStreetMap, tinted by their turn from north to south")
    panels = [("Britain", (-6.5, 2.2, 49.9, 55.6), [0.02, 0.06, 0.31, 0.76], "United Kingdom"),
              ("South-east Australia", (138.0, 153.8, -38.9, -26.5), [0.35, 0.06, 0.36, 0.76], "Australia"),
              ("New Zealand", (166.2, 178.8, -47.0, -34.3), [0.73, 0.06, 0.25, 0.76], "New Zealand")]
    for t, ext, rect, c in panels:
        ax = fig.add_axes(rect)
        k = basemap(ax, ext)
        d = S[(S.lon.between(ext[0], ext[1])) & (S.lat.between(ext[2], ext[3]))]
        L = (ext[3] - ext[2]) * 0.012
        ticks(ax, d.lon.values, d.lat.values, d.bearing.values, k, L=L, lw=1.5)
        v = R["by_country"][c]["strip"]
        ax.text(0.03, 0.97, t, transform=ax.transAxes, fontproperties=DISPB, fontsize=15, va="top", zorder=9,
                bbox=dict(fc=PAPER, ec="none", alpha=0.85, pad=2))
        ax.text(0.03, 0.905, f"{v['n']:,} strips, {v['ns20']:.0f}% within 20° of N to S", transform=ax.transAxes, fontsize=10, va="top", zorder=9,
                bbox=dict(fc=PAPER, ec="none", alpha=0.85, pad=2))
    nsbar(fig, [0.66, 0.875, 0.31, 0.02])
    foot(fig, SRC + ". Chance alone would put 22% within 20° of north to south.")
    out(fig, "map")


# ---------- 2. sports compared (UK)
def fig_sports():
    keys = [("strip", "Cricket strips"), ("tennis", "Tennis courts"), ("netball", "Netball courts"), ("hockey", "Hockey pitches"),
            ("basketball", "Basketball courts"), ("football", "Football pitches"), ("rugby", "Rugby pitches"), ("gaelic", "Gaelic pitches")]
    fig = plt.figure(figsize=(13, 7.4)); paper(fig)
    head(fig, "Cricket and tennis face north. Football faces anywhere.",
         "United Kingdom: share of pitches whose long axis lies within 20° and 30° of the north to south line")
    ax = fig.add_axes([0.22, 0.15, 0.62, 0.64]); ax.set_facecolor(PAPER)
    y = np.arange(len(keys))[::-1]
    for yy, (k, lab) in zip(y, keys):
        v = R["uk"][k]
        c = SPORTC.get({"strip": "cricket"}.get(k, k), MUT)
        ax.barh(yy, v["ns30"], color=c, alpha=0.35, height=0.7)
        ax.barh(yy, v["ns20"], color=c, height=0.7)
        ax.text(v["ns30"] + 1, yy, f"{v['ns20']:.0f}%  ({v['n']:,})", va="center", fontsize=11)
    ax.axvline(R["chance20"], color=INK, ls="--", lw=1); ax.axvline(R["chance30"], color=INK, ls=":", lw=1)
    ax.text(R["chance20"], len(keys) - 0.35, "chance, 20°", ha="center", fontsize=9.5, color=INK)
    ax.text(R["chance30"], len(keys) - 0.35, "chance, 30°", ha="left", fontsize=9.5, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([k[1] for k in keys], fontsize=12)
    ax.set_xlim(0, 75); ax.set_xlabel("Share within 20° (dark) and 30° (pale) of north to south, %  (number measured)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    foot(fig, SRC)
    out(fig, "sports")


# ---------- 3. roses
def fig_roses():
    fig = plt.figure(figsize=(14, 6.4)); paper(fig)
    head(fig, "Which way they point", "The long axis of each pitch, as a rose: the longer the petal, the more pitches point that way")
    G = [(S[S.country == "United Kingdom"].bearing, SPORTC["cricket"], "UK cricket strips"),
         (S[S.country == "Australia"].bearing, SPORTC["cricket"], "Australian cricket strips"),
         (U[(U.cls == "tennis") & U.has_axis].bearing, SPORTC["tennis"], "UK tennis courts"),
         (U[(U.cls == "football") & U.has_axis].bearing, SPORTC["football"], "UK football pitches"),
         (C[(C.cls == "square") & (C.country == "United Kingdom")].bearing, "#8E6F4F", "UK cricket squares,\nlong side")]
    for i, (b, c, t) in enumerate(G):
        ax = fig.add_axes([0.035 + i * 0.196, 0.08, 0.145, 0.64], projection="polar")
        rose(ax, b, c, t, sub=f"{len(b):,}")
    foot(fig, SRC)
    out(fig, "roses")


# ---------- 4. countries
def fig_countries():
    cs = [c for c in R["strip_countries_20"]]
    cs = sorted(cs, key=lambda c: -R["by_country"][c]["strip"]["ns20"])
    fig = plt.figure(figsize=(13, 7.6)); paper(fig)
    head(fig, "Australia follows the rule best", "Cricket strips within 20° of north to south, by country (with at least 20 strips mapped), and the median latitude")
    ax = fig.add_axes([0.25, 0.15, 0.6, 0.63]); ax.set_facecolor(PAPER)
    y = np.arange(len(cs))[::-1]
    for yy, c in zip(y, cs):
        v = R["by_country"][c]["strip"]
        ax.barh(yy, v["ns20"], color=RED if c != "United Kingdom" else "#C4471F", height=0.68)
        ax.text(v["ns20"] + 1, yy, f"{v['ns20']:.0f}%  ({v['n']:,} strips, {abs(R['by_country'][c]['median_lat']):.0f}°{'N' if R['by_country'][c]['median_lat'] >= 0 else 'S'})", va="center", fontsize=11)
    ax.axvline(R["chance20"], color=INK, ls="--", lw=1)
    ax.text(R["chance20"] + 0.5, -0.9, "chance", fontsize=9.5)
    nm = {"United States of America": "United States"}
    ax.set_yticks(y); ax.set_yticklabels([nm.get(c, c) for c in cs], fontsize=12)
    ax.set_xlim(0, 95); ax.set_ylim(-1.2, len(cs) - 0.4); ax.set_xlabel("Share within 20° of north to south, %")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    foot(fig, SRC)
    out(fig, "countries")


# ---------- 5. the glare model
def fig_glare():
    fig = plt.figure(figsize=(13, 7.2)); paper(fig)
    g = R["glare"]
    head(fig, "Where the low sun lines up with the pitch",
         f"Minutes a season when the sun is under {g['alt_max']:.0f}° high and within {g['half']:.0f}° of the line of the pitch, from 10 in the morning to sunset")
    ax = fig.add_axes([0.08, 0.13, 0.55, 0.62]); ax.set_facecolor(PAPER)
    bs = np.arange(0, 180, 5)
    for lat, c, lab in [(52, "#C4471F", "52°N (England), April to September"), (-34, "#2F5D8C", "34°S (Sydney), October to March"), (18, "#7A8F3A", "18°N (Mumbai), October to March")]:
        x = next(v for v in g["by_lat"] if v["lat"] == lat)
        ax.plot(bs, np.array(x["curve"]) / 60, color=c, lw=2.2, label=lab)
    ax.set_xticks([0, 45, 90, 135, 180]); ax.set_xticklabels(["N to S", "NE to SW", "E to W", "SE to NW", "N to S"])
    ax.set_ylabel("Hours of low sun along the pitch, per season"); ax.legend(frameon=False, fontsize=10.5, loc="upper left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax2 = fig.add_axes([0.68, 0.13, 0.29, 0.62]); ax2.set_facecolor(PAPER)
    L = [v["lat"] for v in g["by_lat"]]
    ax2.fill_betweenx(L, [v["zero_lo"] for v in g["by_lat"]], [v["zero_hi"] for v in g["by_lat"]], color="#E7D3A0", lw=0)
    ax2.axvline(0, color=INK, lw=0.8)
    for lb in R["lat_bands"]:
        if lb["n"] >= 25:
            ax2.plot([lb["mean_bearing"]], [(lb["lat0"] + lb["lat1"]) / 2], "o", color=RED, ms=4 + lb["n"] / 60)
    ax2.set_xlim(-90, 90); ax2.set_ylim(-47, 61); ax2.set_xticks([-60, -30, 0, 30, 60]); ax2.set_xticklabels(["NW", "", "N", "", "NE"])
    ax2.set_ylabel("Latitude"); ax2.set_title("Glare-free bearings (shaded)\nand the average strip (dots)", fontsize=11)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    foot(fig, SRC + ". Solar position: Spencer (1971); refraction: Bennett (1982).")
    out(fig, "glare")


# ---------- 6. streets
def fig_streets():
    fig = plt.figure(figsize=(13, 6.6)); paper(fig)
    head(fig, "In towns, pitches line up with the streets", "Pitches in built-up places where the local street grid turns 15° or more from the compass: angle to the grid and to the compass")
    sets = [("football", "Football pitches", SPORTC["football"]), ("tennis", "Tennis courts", SPORTC["tennis"]), ("strip", "Cricket strips", SPORTC["cricket"])]
    for i, (k, t, c) in enumerate(sets):
        ax = fig.add_axes([0.06 + i * 0.32, 0.16, 0.26, 0.56]); ax.set_facecolor(PAPER)
        sel = (M.cls == k) & (M.road_len >= R["streets_sample"]["urban_threshold_m"]) & (M.grid_off >= 15)
        d = M[sel]
        bins = np.arange(0, 46, 3)
        ax.hist(d.d_grid, bins=bins, color=c, alpha=0.85, label="to the street grid")
        ax.hist(d.cd, bins=bins, histtype="step", color=INK, lw=1.6, label="to the compass")
        ax.set_title(f"{t} (n = {len(d):,})\n{R['streets'][k]['urban_closer_to_grid']:.0f}% closer to the streets", fontsize=11.5)
        ax.set_xlabel("Angle, degrees (0 = lined up)")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if i == 0:
            ax.legend(frameon=False, fontsize=10)
    foot(fig, SRC + ". Roads within 200 m from OpenFreeMap vector tiles.")
    out(fig, "streets")


# ---------- 7. what is measured: strip, square, ground
def fig_shapes():
    fig = plt.figure(figsize=(13, 5.6)); paper(fig)
    head(fig, "Strip, square and ground", "Three things OpenStreetMap calls a cricket pitch, with the smallest rectangle that fits round each (dashed). North is up.")
    rng = np.random.default_rng(4)
    picks = []
    for cls, cond in [("strip", (C.cls == "strip") & (C.country == "United Kingdom") & C.in_ground),
                      ("square", (C.cls == "square") & (C.country == "United Kingdom")),
                      ("ground", (C.cls == "ground") & (C.country == "United Kingdom") & (C.ratio < 1.12))]:
        d = C[cond]
        picks.append((cls, d.iloc[int(rng.integers(len(d)))]))
    txt = {"strip": "A strip: one pitch,\n{L:.0f} m by {W:.0f} m.\nIts long axis is the pitch.",
           "square": "A square: many strips side by side,\n{L:.0f} m by {W:.0f} m.\nOnly its turn from the compass counts.",
           "ground": "A ground: the whole field,\n{L:.0f} m by {W:.0f} m.\nRound: no axis."}
    for i, (cls, r) in enumerate(picks):
        ax = fig.add_axes([0.03 + i * 0.33, 0.08, 0.28, 0.66]); ax.set_facecolor(PAPER)
        g = shapely.from_wkb(GW[r.osm]); k = math.cos(math.radians(r.lat))
        a = np.array(g.exterior.coords); X = (a[:, 0] - r.lon) * 111195 * k; Y = (a[:, 1] - r.lat) * 111195
        ext = 80 if cls == "ground" else 25
        ax.set_ylim(-ext, ext * 1.45)
        if cls == "strip":
            # the ground around it, if mapped
            for o in C[(C.cls == "ground") & (np.abs(C.lon - r.lon) < 0.003) & (np.abs(C.lat - r.lat) < 0.002)].osm:
                b = np.array(shapely.from_wkb(GW[o]).exterior.coords)
                ax.plot((b[:, 0] - r.lon) * 111195 * k, (b[:, 1] - r.lat) * 111195, color="#7A8F3A", lw=1)
        ax.fill(X, Y, color="#C9D7A0" if cls != "strip" else "#D9B77A", ec=INK, lw=1.2)
        P = shapely.Polygon(np.c_[X, Y]).minimum_rotated_rectangle
        q = np.array(P.exterior.coords); ax.plot(q[:, 0], q[:, 1], color=RED, lw=1.2, ls="--")
        if cls == "strip":
            b = math.radians(r.bearing); h = r.length / 2 + 6
            ax.annotate("", xy=(math.sin(b) * h, math.cos(b) * h), xytext=(-math.sin(b) * h, -math.cos(b) * h), arrowprops=dict(arrowstyle="-", color=RED, lw=2))
        ax.set_xlim(-ext * 1.2, ext * 1.2); ax.set_ylim(-ext, ext * 1.45); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.text(0.0, 1.0, txt[cls].format(L=r.length, W=r.width), transform=ax.transAxes, fontsize=10.5, va="top")
        ax.text(1.0, 0.0, f"{2.4 * ext:.0f} m across   OSM " + r.osm, transform=ax.transAxes, fontsize=8, ha="right", color=MUT)
    foot(fig, SRC)
    out(fig, "shapes")


for f in (fig_map, fig_sports, fig_roses, fig_countries, fig_glare, fig_streets, fig_shapes):
    f(); print("fig", f.__name__)
