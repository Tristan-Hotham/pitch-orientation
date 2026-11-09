"""Step 8: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Pitch_Orientation.pdf and .tex beside the f_*.png figures. The DOI stays a placeholder
unless the publisher reruns with DOI=10.5281/zenodo.N in the environment."""
import re, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Pitch_Orientation"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


rows = ""
raw = R["n"]["uk_by_sport_raw"]
for k, lab, rk in [("strip", "Cricket strips", "cricket"), ("tennis", "Tennis", "tennis"), ("netball", "Netball", "netball"), ("hockey", "Hockey", None),
                   ("basketball", "Basketball", "basketball"), ("football", "Football", "football"), ("rugby", "Rugby (union, league)", None), ("gaelic", "Gaelic games", "gaelic"),
                   ("square", "Cricket squares (long side)", None), ("nets", "Cricket nets", None)]:
    v = R["uk"][k]
    rows += f"{lab} & {v['n']:,} & {v['ns20']:.1f} & {v['ns30']:.1f} & {v['ew20']:.1f} & {v['mean_bearing']:.1f} & {v['R']:.2f} & {pv(v['p_ns20'])}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{United Kingdom, pitches with an axis by sport: number measured; share (\\%) within 20° and 30° of north to south "
      f"and within 20° of east to west; axial mean bearing (degrees from north, negative west of north) and its length $R$; binomial p-value for the 20° share against {R['chance20']:.1f}\\%. "
      f"Polygons tagged in the UK file: football {raw['football']:,}, tennis {raw['tennis']:,}, cricket {raw['cricket']:,}, rugby {raw['rugby'] + raw.get('rugby_union', 0):,}.}}\\label{{tab:sports}}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Sport & n & $\\le$20° & $\\le$30° & E to W $\\le$20° & Mean & $R$ & p\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for c in ["United Kingdom", "Australia", "New Zealand", "United States of America", "Canada", "Samoa", "India", "South Africa", "Pakistan", "Sri Lanka", "Bangladesh", "Caribbean"]:
    v = R["by_country"][c]
    s, q, g = v["strip"], v["square"], v["ground_axis"]
    f = lambda x, k: f"{x[k]:.1f}" if x.get("n", 0) >= 10 else "."
    rows += (f"{c.replace('United States of America', 'United States')} & {v['median_lat']:.0f} & {v['all_cricket']:,} & {s.get('n', 0)} & {f(s, 'ns20')} & "
             f"{q.get('n', 0)} & {f(q, 'card10')} & {g.get('n', 0)} & {f(g, 'ns20')}\\\\\n")
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Cricket by country: median latitude, all cricket polygons, strips and their share (\\%) within 20° of north to south, "
      "squares and their share within 10° of the compass, elongated grounds and their share within 20° of north to south (shares shown for 10 or more). "
      "Caribbean: the West Indies cricket territories together.}\\label{tab:countries}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule Country & Lat. & All & Strips & $\\le$20° & Squares & $\\le$10° & Grounds & $\\le$20°\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{TABLE_SPORTS}}", TS).replace("{{TABLE_COUNTRIES}}", TC).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24075295", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
for bad in ("DSIT", "DCMS"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "DOI_URL shown:", "https://doi.org/10.5281/zenodo.24075295" in txt)
