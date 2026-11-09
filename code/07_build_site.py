"""Step 7: index.html from code/page_template.html + page.css + essay.html, filled from data/results.json, with the
full-screen snippet; page images in img/ (the blog figures at 1200 px); the Inked World map files copied from the
church-orientation study. 10.5281/zenodo.24075295, https://doi.org/10.5281/zenodo.24075295 and https://blog.tristanhotham.com/2026/10/31/pitch-orientation/ stay as placeholders for the publisher."""
import re, shutil
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI_URL", "BLOG_URL", "DOI"}
# facts stated in words on the page and in alt text
u = R["uk"]
assert u["strip"]["ns20"] > u["tennis"]["ns20"] > u["netball"]["ns20"] > max(u["football"]["ns20"], u["rugby"]["ns20"], u["gaelic"]["ns20"])
assert abs(u["football"]["ns20"] - u["football"]["ew20"]) < 2 and u["tennis"]["ew20"] < 15
assert u["square"]["ew20"] > u["square"]["ns20"]
bc = R["by_country"]
order = sorted(R["strip_countries_20"], key=lambda c: -bc[c]["strip"]["ns20"])
assert order == ["Australia", "United States of America", "United Kingdom", "Canada", "New Zealand", "Samoa"], order
assert [round(bc[c]["strip"]["ns20"]) for c in order] == [69, 49, 47, 46, 34, 29]
assert u["gaelic"]["ew20"] < R["chance20"] < min(u["football"]["ew20"], u["rugby"]["ew20"])
assert [round(u[k]["ns20"]) for k in ["strip", "tennis", "netball", "hockey", "basketball", "football", "rugby", "gaelic"]] == [47, 40, 30, 28, 27, 26, 25, 24]
st = R["streets"]
assert st["strip"]["urban_closer_to_grid"] < min(st[k]["urban_closer_to_grid"] for k in ("football", "tennis", "rugby", "netball", "basketball"))
g = R["glare"]["uk_lat52"]
assert g["zero_hi"] > -g["zero_lo"] and g["glare_ns"] == 0
assert R["audit"]["sheet_doubtful_2"] == 1

css = open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read()
essay = open(os.path.join(ROOT, "code", "essay.html"), encoding="utf-8").read()
rows = []
for c in ["United Kingdom", "Australia", "New Zealand", "India", "South Africa", "Pakistan", "Sri Lanka", "Bangladesh", "Caribbean",
          "United States of America", "Canada", "Samoa", "Ireland"]:
    v = bc[c]
    s, q, gr = v["strip"], v["square"], v["ground_axis"]
    f = lambda x, k: f"{x[k]:.0f}%" if x.get("n", 0) >= 10 else ("" if not x.get("n") else "few")
    rows.append(f"<tr><td>{c.replace('United States of America', 'United States')}</td><td class=\"r\">{s.get('n', 0)}</td><td class=\"r\">{f(s, 'ns20')}</td>"
                f"<td class=\"r\">{f(q, 'card10')}</td><td class=\"r\">{gr.get('n', 0)}</td><td class=\"r\">{f(gr, 'ns20')}</td></tr>")
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", css).replace("{{ESSAY}}", essay).replace("{{COUNTRY_ROWS}}", "".join(rows))
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
import figstyle_stops
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{NS_STOPS}}", json.dumps(figstyle_stops.NS_STOPS))
t = t.replace("{{GLARE}}", json.dumps({x["lat"]: [x["zero_lo"], x["zero_hi"]] for x in R["glare"]["by_lat"]}))
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
left = set(re.findall(r"\{\{([^}]+)\}\}", t))
assert left <= KEEP, left
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
for nm in ("shapes", "map", "sports", "roses", "countries", "glare", "streets"):
    im = Image.open(os.path.join(ROOT, "release", "paper", f"f_{nm}.png")).convert("RGB")
    im.thumbnail((1200, 1200), Image.LANCZOS)
    im.save(os.path.join(ROOT, "img", f"{nm}.png"), optimize=True)
    t = re.sub(r'(src="img/%s\.png"[^>]*?)width="\d+" height="\d+"' % nm, r'\g<1>width="%d" height="%d"' % im.size, t)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
# the Inked World map files
SRC = "/home/claude/studies/church-orientation"
for fn in os.listdir(f"{SRC}/data"):
    if fn.endswith((".geojson", ".webp", ".png")) or fn in ("house_regions.json", "walls_boxes.json"):
        shutil.copy(f"{SRC}/data/{fn}", f"{DATA}/{fn}")
os.makedirs(f"{DATA}/grid", exist_ok=True)
shutil.copy(f"{SRC}/data/grid/index.json", f"{DATA}/grid/index.json")
print("index.html", len(t) // 1024, "KB")
