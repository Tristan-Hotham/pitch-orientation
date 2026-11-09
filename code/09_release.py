"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24075295, https://doi.org/10.5281/zenodo.24075295 and https://blog.tristanhotham.com/2026/10/31/pitch-orientation/ stay as placeholders for the publisher."""
import json as _json, re, shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "07_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Pitch_Orientation"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
# facts written in words in the blog only
a = R["audit"]
assert 11 <= a["sheet_sample_1"] / a["sheet_nets_1"] <= 13                       # "about one in twelve"
assert R["glare"]["uk_lat52"]["peak"] > 90                                         # worst direction east-south-east, safe arc leans north-east

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Which way do cricket pitches face?",
        "slug": "pitch-orientation",
        "excerpt": f"The old advice says a cricket pitch should run north to south, out of the evening sun. I measured every cricket pitch in OpenStreetMap and every sports pitch in the UK: {R['strips_world']['ns20']:.0f}% of cricket strips follow the rule, tennis courts mostly do, and football pitches point anywhere.",
        "seo_description": f"{R['strips_world']['ns20']:.0f}% of the world's mapped cricket strips run north to south. Tennis follows the rule; football ignores it.",
        "tags": ["maps", "data visualisation", "cricket", "tennis", "football", "OpenStreetMap", "sun", "sport", "geography"],
        "header_alt": f"Title card reading 'Which way do cricket pitches face?' on parchment beside a large rose diagram of cricket strips standing upright on the north to south line, with the line '{R['strips_world']['ns20']:.0f}% lie within 20° of N to S'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
OWN = ["pitches.csv", "countries.csv", "glare_by_latitude.csv", "street_grid_sample.csv", "strip_checks.csv", "overrides_applied.csv", "results.json"]
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in OWN:
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("\\texttt{", "").replace("}", "").replace("\\emph{", "")
zmeta = {"title": "Which Way Do Cricket Pitches Face? The Orientation of Sports Pitches in OpenStreetMap, the Low Sun and the Street Grid",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/pitch-orientation/}}.</p><p>Sources: OpenStreetMap contributors (ODbL), queried with QLever; OpenFreeMap vector tiles; Natural Earth. The pitch table (pitches.csv) is derived from OpenStreetMap and released under the Open Database Licence; other derived data and text CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["sports pitches", "cricket", "orientation", "sun glare", "OpenStreetMap", "street networks", "tennis", "sports facility design"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.openstreetmap.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.5281/zenodo.24052501", "relation": "references", "resource_type": "publication-workingpaper"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
