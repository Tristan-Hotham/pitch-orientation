# NOTES: pitch-orientation (batch 9, study 3)

Brief: /home/claude/work/new9/BRIEFS.md (study 3) + shared rules in new8/BRIEFS.md and newdata/BRIEF.md.
Format refs: studies/church-orientation (axis code, OFM street code), sunless-valleys (sun maths, DOI placeholder).
Intermediates: /home/claude/scratch/pitch-orientation (not repo; delete at end).

## Plan
1. 01_axes.py: MRR long axis of every polygon (UK all sports; world cricket), country by NE 10m.
2. 02_classify.py: cricket classes strip / square / ground / nets / other; other sports by size window; dedupe IoU>=0.8; overrides.csv.
3. 03_streets.py: OFM z14 roads within 200 m for every strip + square, samples of UK football/tennis/rugby/netball/basketball.
4. 04_analysis.py: N-S shares by class/sport/country, latitude, glare model (sunmodel.py), street test, checks -> results.json.
5. export, figures, site, paper, blog, release, readme, collage, QA.

## Log
- 01: UK 84,853 polygons, world cricket 15,168 (UK cricket ways identical in both files: 4,150 of 4,152 UK pitches_uk cricket in world file).
- Validation: strips mapped inside grounds: grounds with ratio >= 1.2 have long axis within ~3 deg of the strip (median) -> but UK grounds
  overall don't follow strips; ground axis treated as weak proxy only.
- Sizes: strips 17-45 x <=12 m, ratio>=2.5; squares 180-3500 m2 fill>=0.85 (mod-90 only); grounds >= 6000 m2.
- Famous Test grounds are mostly leisure=stadium, not in the data (only Wankhede, Basin Reserve as round grounds).
- 03 streets: 9,847 samples, 10,891 OFM tiles (~33 min, peak RAM 2.6 GB).
- Eye audit (04b_audit.py, contact sheets in scratch): sample 1 of 120 strips: ~10 were banks of nets at ground edges, all
  6-12 m wide or just outside a ground -> rules: strip width <=6 m (ratio>=3.5); 6-12 m wide -> nets; strip within 40 m
  outside a ground -> nets. Moved 355 of 1,729 (20.5%). Sample 2 of 60 after rules: 1 doubtful (w622306776, NZ, beside
  building). overrides.csv: no hand overrides needed (kept, empty). Duplicates (IoU>=0.8): 2 cricket, 11 other sports.
- Whole-set checks: 1,039 of 1,374 strips have no other cricket polygon within 150 m (isolated ns20 55.0% vs near 54.3%,
  so not driving result); per-ground clusters (120 m) give 53.7% vs 54.8% per strip.
- Results: strips 54.8% within 20 of N-S (chance 22.2); Aus 69.1, UK 46.6, NZ 34.6; UK tennis 40.5, football 26.1 (EW 25.3);
  UK squares long side EW 31.8 vs NS 16.6. Glare model 52N: safe arc -33..+61; 82.5% of strips safe. Streets: urban off-grid
  closer to streets football 84.9, tennis 80.0, strips 67.3 (Aus 53.9).
- South Asia/Caribbean: strips barely mapped (India 17, Pakistan 3) -> country comparison only for 6 countries with >=20 strips.
- References to verify (cited in paper): Bast & Buchhold 2017 CIKM (QLever); Bast, Brosi, Kalmbach, Lehmann 2021 SIGSPATIAL
  (osm2rdf, pages 536-539 from memory); Bennett 1982 J. Navigation 35(2) 255-259; Boeing 2019 Applied Network Science 4, 67;
  Freeman & Shapira 1975 CACM 18(7) 409-413; Spencer 1971 Search 2(5) 172; Hotham 2026 church-orientation Zenodo 10.5281/zenodo.24052501.
  No citation given for the north-south advice itself (could not verify a guidance document offline; e.g. Sport England guidance could be added after checking).
- Scratch deleted at end (rerun 01-03 to regenerate, ~40 min).
- DONE: figures, index.html, paper (9 pp, https://doi.org/10.5281/zenodo.24075295 placeholder; DOI env fills), blog (6 figs), zenodo, README, LICENSE, collage, header, QA (0 errors except blocked Google Fonts).

## Independent review (2026)
- Reran 01 to 10 from raw. Fixes: (1) the nets "edge" rule used a distance in degrees (40/111195/0.55), i.e. 45 to 73 m, not 40 m;
  now true metric distance in a local frame: edge nets 45 -> 25, strips 1,374 -> 1,394, rules moved 19.4% (was 20.5%).
  (2) 04b_audit "within 150 m" also used degrees; now metric (strips with cricket nearby 313 of 1,394).
  (3) 03_streets now samples nets too (so a class change needs no refetch) and keeps their context.
- Texts: uncited "groundsmen everywhere" claims replaced with cited guidance (Government of Western Australia, Sports dimensions
  guide; FIFA Stadium Guidelines 2022, s2.2); "football gets no advice" removed (FIFA recommends N-S for stadiums); Gaelic games
  no longer said to exceed chance east to west; country order fixed (USA now 2nd); square claim softened; street baseline (50%) stated.
- References verified on the web; osm2rdf page range (536 to 539) unverifiable -> replaced by DOI; DOIs added for QLever, Boeing.
- Spot check: 60 random strips + every Samoa and Canada strip drawn with OFM context: no clear misclassification; Samoan strips are
  concrete village pitches, two lie inside building outlines.
