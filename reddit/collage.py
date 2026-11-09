"""Reddit collage (reddit/pitch_orientation_collage.png, 3000 x 1900) and the social card (header.png, 1200 x 630).
Run from anywhere: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import pandas as pd
from figstyle import *

R = jload(os.path.join(DATA, "results.json"))
C = pd.read_pickle(os.path.join(WORK, "cricket_final.pkl"))
U = pd.read_pickle(os.path.join(WORK, "sports.pkl"))
S = C[C.cls == "strip"]
sw, u, bc = R["strips_world"], R["uk"], R["by_country"]
SRC = "Data: OpenStreetMap contributors (ODbL)  ·  Analysis and map: Dr Tristan Hotham  ·  maps.tristanhotham.com/pitch-orientation"


def bigrose(ax, b, colour_by_dev=True, nbin=36, fs=16):
    h, e = np.histogram(np.asarray(b) % 180, bins=nbin, range=(0, 180))
    h = h / h.max()
    mid = (e[:-1] + e[1:]) / 2
    th = np.radians(mid)
    cols = NS_CMAP(NS_NORM(ns_dev(mid)))
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    w = np.radians(180 / nbin) * 0.9
    ax.bar(th, h, width=w, color=cols, edgecolor="none")
    ax.bar(th + math.pi, h, width=w, color=cols, edgecolor="none")
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270])); ax.set_xticklabels(["N", "E", "S", "W"], fontsize=fs)
    ax.set_facecolor("#FBF5E4"); ax.spines["polar"].set_color(MUT); ax.grid(color=RULE, lw=0.8)


# ---------------- collage
fig = plt.figure(figsize=(20, 12.667)); paper(fig)
fig.text(0.03, 0.955, "Which way do cricket pitches face?", fontproperties=DISP, fontsize=46, va="top")
fig.text(0.03, 0.885, f"The rule: north to south, out of the low evening sun. {sw['ns20']:.0f}% of {R['n']['cricket_strip']:,} mapped cricket strips obey it.",
         fontproperties=SERP, fontsize=21, color=MUT, va="top")
# maps
panels = [("Britain", (-6.0, 2.0, 50.0, 55.2), [0.02, 0.1, 0.2, 0.6], "United Kingdom"),
          ("South-east Australia", (138.0, 153.8, -38.9, -26.5), [0.235, 0.1, 0.25, 0.6], "Australia"),
          ("New Zealand", (166.2, 178.8, -47.0, -34.3), [0.5, 0.1, 0.16, 0.6], "New Zealand")]
for t, ext, rect, c in panels:
    ax = fig.add_axes(rect)
    k = basemap(ax, ext, lw=0.6)
    d = S[(S.lon.between(ext[0], ext[1])) & (S.lat.between(ext[2], ext[3]))]
    ticks(ax, d.lon.values, d.lat.values, d.bearing.values, k, L=(ext[3] - ext[2]) * 0.013, lw=2.0)
    v = bc[c]["strip"]
    ax.set_title(f"{t}\n{v['ns20']:.0f}% of {v['n']:,} strips", fontsize=15, pad=8, loc="left")
# big rose
ax = fig.add_axes([0.685, 0.42, 0.28, 0.36], projection="polar")
bigrose(ax, S.bearing.values)
fig.text(0.825, 0.815, f"All {R['n']['cricket_strip']:,} strips", ha="center", fontsize=20)
# sports bars
ax = fig.add_axes([0.765, 0.1, 0.2, 0.26]); ax.set_facecolor(PAPER)
keys = [("strip", "Cricket strips", "cricket"), ("tennis", "Tennis courts", "tennis"), ("netball", "Netball", "netball"), ("football", "Football", "football"), ("rugby", "Rugby", "rugby")]
y = np.arange(len(keys))[::-1]
for yy, (k, lab, cc) in zip(y, keys):
    ax.barh(yy, u[k]["ns20"], color=SPORTC[cc], height=0.66)
    ax.text(u[k]["ns20"] + 1, yy, f"{u[k]['ns20']:.0f}%", va="center", fontsize=14)
ax.axvline(R["chance20"], color=INK, ls="--", lw=1.2)
ax.text(R["chance20"] + 0.8, -0.85, "chance", fontsize=12)
ax.set_yticks(y); ax.set_yticklabels([k[1] for k in keys], fontsize=14); ax.set_xlim(0, 60); ax.set_ylim(-1.1, len(keys) - 0.4)
ax.set_xticks([]); [ax.spines[s].set_visible(False) for s in ("top", "right", "bottom")]
ax.set_title("United Kingdom, within 20° of N to S", fontsize=14.5, loc="left")
nsbar(fig, [0.03, 0.775, 0.3, 0.018], label="Each line is one strip, tinted by its turn from north to south")
fig.text(0.03, 0.725, "Map titles: share of strips within 20° of north to south", fontsize=14, color=INK)
fig.text(0.03, 0.025, SRC, fontsize=13, color=MUT)
fig.text(0.97, 0.025, f"Chance alone: {R['chance20']:.0f}% within 20°", fontsize=13, color=MUT, ha="right")
out = os.path.join(ROOT, "reddit", "pitch_orientation_collage.png")
fig.savefig(out, dpi=150, facecolor=PAPER); plt.close(fig)

# ---------------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3)); paper(fig)
fig.text(0.05, 0.86, "Which way do", fontproperties=DISP, fontsize=46, va="top")
fig.text(0.05, 0.70, "cricket pitches face?", fontproperties=DISP, fontsize=46, va="top", color=RED)
fig.text(0.05, 0.47, f"{sw['ns20']:.0f}% lie within 20° of N to S", fontproperties=DISPB, fontsize=26, va="top")
fig.text(0.05, 0.36, f"{R['n']['cricket_strip']:,} cricket strips measured from OpenStreetMap.\nTennis follows the rule; football ignores it.", fontproperties=SERP, fontsize=17, color=MUT, va="top")
fig.text(0.05, 0.08, "maps.tristanhotham.com/pitch-orientation", fontsize=13, color=MUT)
ax = fig.add_axes([0.6, 0.06, 0.37, 0.88], projection="polar")
bigrose(ax, S.bearing.values, fs=13)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER); plt.close(fig)
from PIL import Image
print(Image.open(out).size, Image.open(os.path.join(ROOT, "header.png")).size)
