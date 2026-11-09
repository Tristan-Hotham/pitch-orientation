# Which way do cricket pitches face?

The long axis of every cricket pitch mapped in OpenStreetMap worldwide (15,168 polygons) and every sports pitch in the United Kingdom (84,853), measured against the north to south line, to test the old advice that cricket pitches and tennis courts should run north to south, out of the low evening sun. With a simple model of sun glare and a comparison with the local street grid.

Interactive page: https://maps.tristanhotham.com/pitch-orientation/
Paper: https://doi.org/10.5281/zenodo.24075295
Blog post: https://blog.tristanhotham.com/2026/10/31/pitch-orientation/
Code and data: https://github.com/Tristan-Hotham/pitch-orientation

## Headline results

- 54.7% of the world's 1,394 mapped cricket strips (single pitches) lie within 20° of north to south, against 22.2% by chance; 9.9% lie within 20° of east to west. Australia 68.6% (692 strips), United Kingdom 46.9% (209), New Zealand 34.3% (338).
- UK cricket squares agree: 31.8% of 578 have their long side (usually the side across the strips) within 20° of east to west.
- In the UK, tennis courts follow the rule (40.5% of 29,426); football (26.1% north to south, 25.3% east to west), rugby (25.3%) and Gaelic games (24.1%) do not.
- Glare model: at 52°N in an English season, an east to west pitch has about 88 hours of low sun along it; every bearing from -33° to 61° has none. 82.5% of strips lie in the glare-free arc for their latitude.
- In built-up places with an off-compass street grid, pitches follow the streets: football 85%, tennis 80%, cricket strips only 66%.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`): the Inked World map style on MapLibre GL JS; rose diagrams of pitch directions when zoomed out, single pitches as oriented glyphs coloured by their turn from north to south when zoomed in; filter by sport; search; popups with the glare-free arc. |
| `header.png` | Social card, 1200 x 630. |
| `data/pitches.csv.gz` | Every measured polygon (gzipped; also unzipped in the Zenodo archive) (95,867 rows): OSM id and link, sport, class (cricket strip, square, ground, nets, other; other sports), whether it has an axis, name, country, centroid, axis bearing, length, width, ratio, area, fill, turn from north to south. ODbL. |
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
- Cricket classes: strip (17 to 45 m by 1.5 to 6 m, ratio at least 3.5); square (180 to 3,500 m², at most 60 m, fills 85% of its rectangle; compass alignment only); ground (6,000 m² or more; axis only if 1.2 times as long as wide); nets (named nets, rectangles of strip length 6 to 12 m wide, strips within 40 m outside a mapped ground). The last two rules came from contact sheets of a random sample of 120 strips checked by eye; they moved 19.4% of the first strip list. Duplicates (same class, overlap of 80% or more): 2.
- Other sports: kept when the rectangle has the size and shape of one playing area (see `code/02_classify.py`).
- Glare model: minutes per season with the sun above 0° and at most 15° high and within 15° of the pitch line, 10:00 to sunset; Spencer (1971) declination, Bennett (1982) refraction.
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

- OpenStreetMap (https://www.openstreetmap.org/), © OpenStreetMap contributors, Open Database Licence. Queried with QLever (University of Freiburg). `data/pitches.csv.gz`, `data/pitches.json`, `data/strip_checks.csv`, `data/street_grid_sample.csv` and `data/cricket_venues.csv` are derived databases under the ODbL.
- OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap data) for the street grid and the map.
- Natural Earth (public domain): countries and populated places.
- Map style: the Inked World (ink-map study, MIT code), with Natural Earth, RESOLVE Ecoregions 2017 (CC BY 4.0), Wikidata (CC0) and AWS Terrain Tiles.
- Fonts: MedievalSharp and IM Fell (SIL Open Font License); Fraunces, Source Serif 4, IBM Plex Mono (SIL Open Font License).

## Citation

Hotham, T. (2026) Which way do cricket pitches face? The orientation of sports pitches in OpenStreetMap, the low sun and the street grid. Zenodo. https://doi.org/10.5281/zenodo.24075295

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
