**Title:** [OC] Cricket pitches are supposed to run north to south, out of the evening sun. I measured every one in OpenStreetMap: 55% do (chance: 22%). Football pitches don't care.

**Body:**

The old advice: lay a cricket pitch (and a tennis court) north to south, so the low evening sun isn't in the batter's or bowler's eyes. I took every cricket pitch mapped in OpenStreetMap and every sports pitch in the UK, and measured the long axis of each outline.

- Cricket strips (the 22 yards themselves): 55% within 20° of north to south. Australia 69%, UK 47%, New Zealand 34%.
- UK tennis courts: 40%. UK football pitches: 26% north to south and 25% east to west, so no preference at all.
- In towns, most pitches just follow the street grid (85% of football pitches), cricket the least (66%).

Interactive map with a rose for every area, and every pitch when you zoom in: https://maps.tristanhotham.com/pitch-orientation/

**Source comment:**

Data: OpenStreetMap contributors (ODbL), queried with QLever; OpenFreeMap tiles for the street grid; Natural Earth. Tools: Python (shapely, pandas, matplotlib), MapLibre. Axis = long side of the minimum-area rectangle round each outline. Cricket "pitches" sorted into strips, squares, grounds and nets by size and shape, checked by eye on samples. Sun model: Spencer (1971), Bennett (1982). Paper and code: https://github.com/Tristan-Hotham/pitch-orientation
