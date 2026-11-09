"""Step 10: README.md, LICENSE and the Reddit post text (reddit/post.md), filled from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
n, sw, u, bc, st, g = R["n"], R["strips_world"], R["uk"], R["by_country"], R["streets"], R["glare"]
readme = f"""# Which way do cricket pitches face?

The long axis of every cricket pitch mapped in OpenStreetMap worldwide ({n['world_cricket']:,} polygons) and every sports pitch in the United Kingdom ({n['uk_polygons']:,}), measured against the north to south line, to test the old advice that cricket pitches and tennis courts should run north to south, out of the low evening sun. With a simple model of sun glare and a comparison with the local street grid.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24075295}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/pitch-orientation/}}
Code and data: {REPO}

## Headline results

- {sw['ns20']:.1f}% of the world's {n['cricket_strip']:,} mapped cricket strips (single pitches) lie within 20° of north to south, against {R['chance20']:.1f}% by chance; {sw['ew20']:.1f}% lie within 20° of east to west. Australia {bc['Australia']['strip']['ns20']:.1f}% ({bc['Australia']['strip']['n']:,} strips), United Kingdom {u['strip']['ns20']:.1f}% ({u['strip']['n']:,}), New Zealand {bc['New Zealand']['strip']['ns20']:.1f}% ({bc['New Zealand']['strip']['n']:,}).
- UK cricket squares agree: {u['square']['ew20']:.1f}% of {u['square']['n']:,} have their long side (usually the side across the strips) within 20° of east to west.
- In the UK, tennis courts follow the rule ({u['tennis']['ns20']:.1f}% of {u['tennis']['n']:,}); football ({u['football']['ns20']:.1f}% north to south, {u['football']['ew20']:.1f}% east to west), rugby ({u['rugby']['ns20']:.1f}%) and Gaelic games ({u['gaelic']['ns20']:.1f}%) do not.
- Glare model: at 52°N in an English season, an east to west pitch has about {g['uk_lat52']['glare_ew_h']} hours of low sun along it; every bearing from {g['uk_lat52']['zero_lo']}° to {g['uk_lat52']['zero_hi']}° has none. {g['strips_safe']:.1f}% of strips lie in the glare-free arc for their latitude.
- In built-up places with an off-compass street grid, pitches follow the streets: football {st['football']['urban_closer_to_grid']:.0f}%, tennis {st['tennis']['urban_closer_to_grid']:.0f}%, cricket strips only {st['strip']['urban_closer_to_grid']:.0f}%.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`): the Inked World map style on MapLibre GL JS; rose diagrams of pitch directions when zoomed out, single pitches as oriented glyphs coloured by their turn from north to south when zoomed in; filter by sport; search; popups with the glare-free arc. |
| `header.png` | Social card, 1200 x 630. |
| `data/pitches.csv` | Every measured polygon ({len(open(os.path.join(DATA, 'pitches.csv')).readlines()) - 1:,} rows): OSM id and link, sport, class (cricket strip, square, ground, nets, other; other sports), whether it has an axis, name, country, centroid, axis bearing, length, width, ratio, area, fill, turn from north to south. ODbL. |
| `data/countries.csv` | Cricket by country: strips, squares and elongated grounds. |
| `data/glare_by_latitude.csv` | The glare model: glare-free arc and minutes of low sun by pitch bearing (every 5°), per degree of latitude. |
| `data/street_grid_sample.csv` | The street sample: road length within 200 m, grid direction (mod 90) and strength, angles to grid and compass. |
| `data/strip_checks.csv` | Every strip with its context checks (cricket polygons nearby, cluster). |
| `data/overrides_applied.csv` | Hand overrides (none were needed after the rules; kept for the record). |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/pitches.json`, `data/places.json` | Page data; towns for search (Natural Earth). |
| `data/cricket_venues.csv` | Map only, not part of the analysis: further cricket places in OpenStreetMap (stadiums, clubs, sports centres, shared pitches) with no cricket pitch outline, from `data/raw/cricket_venues_*.tsv.gz` by `code/05b_venues.py`. ODbL. |
| other `data/*` files, `js/`, `fonts/` | The Inked World map style, copied from the ink-map study via church-orientation. |
| `code/` | Numbered scripts, the glare model (`sunmodel.py`), templates, `qa.js`. |
| `release/` | Paper, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Outlines: OpenStreetMap `leisure=pitch` ways and relations with a sport in the UK, and `sport=cricket` pitch ways worldwide, from QLever (osm2rdf). Country from Natural Earth.
- Axis: local true-north equirectangular frame; long side of the minimum-area rectangle, folded to 0° to 180°.
- Cricket classes: strip (17 to 45 m by 1.5 to 6 m, ratio at least 3.5); square (180 to 3,500 m², at most 60 m, fills 85% of its rectangle; compass alignment only); ground (6,000 m² or more; axis only if 1.2 times as long as wide); nets (named nets, rectangles of strip length 6 to 12 m wide, strips within 40 m outside a mapped ground). The last two rules came from contact sheets of a random sample of {R['audit']['sheet_sample_1']} strips checked by eye; they moved {n['nets_moved_pc']:.1f}% of the first strip list. Duplicates (same class, overlap of 80% or more): {n['dup_cricket']}.
- Other sports: kept when the rectangle has the size and shape of one playing area (see `code/02_classify.py`).
- Glare model: minutes per season with the sun above 0° and at most {g['alt_max']:.0f}° high and within {g['half']:.0f}° of the pitch line, 10:00 to sunset; Spencer (1971) declination, Bennett (1982) refraction.
- Street grid: OpenFreeMap vector tiles (zoom 14), roads within 200 m; length-weighted dominant direction mod 90°; built-up means at least 1,500 m of road; compared where the grid turns 15° or more from the compass.
- Caveats: strips are mapped mostly in Australia, New Zealand and Britain and rarely in South Asia and the Caribbean; Test grounds are mostly mapped as stadiums; size rules let the odd net through; the glare model is a sketch.

## How to rerun

Needs Python 3 with pandas, numpy, scipy, shapely, matplotlib, Pillow, fontTools and mapbox-vector-tile; xelatex and pdfinfo; node with Playwright for `code/qa.js`. Raw inputs are listed in `code/common.py`; intermediates go to `PO_WORK`. Step 03 reads OpenFreeMap tiles over the network.

```
python3 code/01_axes.py        # axes of every polygon
python3 code/02_classify.py    # classes, duplicates, overrides
python3 code/03_streets.py     # street grid sample (network)
python3 code/04_analysis.py    # results.json
python3 code/04b_audit.py      # whole-set checks (SHEETS=120 draws contact sheets)
python3 code/05_export.py      # data files and page data
python3 code/06_figures.py     # figures
python3 code/07_build_site.py  # index.html
python3 code/08_paper.py       # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage and header
python3 code/10_readme.py      # README, LICENSE, Reddit post
python3 code/09_release.py     # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap (https://www.openstreetmap.org/), © OpenStreetMap contributors, Open Database Licence. Queried with QLever (University of Freiburg). `data/pitches.csv`, `data/pitches.json`, `data/strip_checks.csv`, `data/street_grid_sample.csv` and `data/cricket_venues.csv` are derived databases under the ODbL.
- OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap data) for the street grid and the map.
- Natural Earth (public domain): countries and populated places.
- Map style: the Inked World (ink-map study, MIT code), with Natural Earth, RESOLVE Ecoregions 2017 (CC BY 4.0), Wikidata (CC0) and AWS Terrain Tiles.
- Fonts: MedievalSharp and IM Fell (SIL Open Font License); Fraunces, Source Serif 4, IBM Plex Mono (SIL Open Font License).

## Citation

Hotham, T. (2026) Which way do cricket pitches face? The orientation of sports pitches in OpenStreetMap, the low sun and the street grid. Zenodo. {{https://doi.org/10.5281/zenodo.24075295}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in "\n".join(l for l in readme.replace("```", "").splitlines() if not l.startswith("|---")), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/church-orientation/LICENSE", encoding="utf-8").read().split("Church data")[0]
lic += """Pitch data (data/pitches.csv, data/pitches.json, data/strip_checks.csv, data/street_grid_sample.csv): derived from OpenStreetMap, © OpenStreetMap contributors, Open Database Licence 1.0 (https://opendatacommons.org/licenses/odbl/1-0/).
Natural Earth data: public domain.
Map style files in js/, fonts/ and the basemap data in data/ come from the ink-map study (code MIT; data credits in its README: OpenStreetMap ODbL, RESOLVE Ecoregions CC BY 4.0, Wikidata CC0, Natural Earth). Fonts under the SIL Open Font License (see fonts/ttf).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] Cricket pitches are supposed to run north to south, out of the evening sun. I measured every one in OpenStreetMap: {sw['ns20']:.0f}% do (chance: {R['chance20']:.0f}%). Football pitches don't care.

**Body:**

The old advice: lay a cricket pitch (and a tennis court) north to south, so the low evening sun isn't in the batter's or bowler's eyes. I took every cricket pitch mapped in OpenStreetMap and every sports pitch in the UK, and measured the long axis of each outline.

- Cricket strips (the 22 yards themselves): {sw['ns20']:.0f}% within 20° of north to south. Australia {bc['Australia']['strip']['ns20']:.0f}%, UK {u['strip']['ns20']:.0f}%, New Zealand {bc['New Zealand']['strip']['ns20']:.0f}%.
- UK tennis courts: {u['tennis']['ns20']:.0f}%. UK football pitches: {u['football']['ns20']:.0f}% north to south and {u['football']['ew20']:.0f}% east to west, so no preference at all.
- In towns, most pitches just follow the street grid ({st['football']['urban_closer_to_grid']:.0f}% of football pitches), cricket the least ({st['strip']['urban_closer_to_grid']:.0f}%).

Interactive map with a rose for every area, and every pitch when you zoom in: {PAGE}

**Source comment:**

Data: OpenStreetMap contributors (ODbL), queried with QLever; OpenFreeMap tiles for the street grid; Natural Earth. Tools: Python (shapely, pandas, matplotlib), MapLibre. Axis = long side of the minimum-area rectangle round each outline. Cricket "pitches" sorted into strips, squares, grounds and nets by size and shape, checked by eye on samples. Sun model: Spencer (1971), Bennett (1982). Paper and code: {REPO}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README, LICENSE, post written")
