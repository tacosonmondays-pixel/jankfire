# Mount Kaboom, old vs new (quick-play Islands)

Same five cameras (top-down footprint, air, side, crater, beach), Too HD, old = main at 21e0224, new = this branch. Shape only: the Art lane dresses it (rock look,
lava channels, rim rocks, smoke), which is why the new one has no lava streams yet.

- `old_vs_new_sheet.jpg`: all four pairs
- `old_vs_new_top.jpg` (the footprint from straight above), `_air.jpg`, `_side.jpg`, `_crater.jpg`, `_beach.jpg`: one pair each

v2 (owner: "quite a bit larger and blend it", "too round at the base"): rim about 15 m with a notch north and a low gap
south, crater floor 11.5, an uneven foot (lava delta north, a long ridge west-north-west, an east buttress, a
south-west shoulder, a collapsed flank south-east), a 5 m apron of lumpy ground that keeps the island's grass and sand.

The shape lives in `shared/map.js` (`KABOOM`, `kaboom()`); the lava throat and `map.pits` are unchanged. Islands S&D
keeps the terraces and stairs.

Rough pass (owner: "too smooth still"; Art lane's list): `rough_sheet.jpg` (air, side, crater, beach). Three broken
cliff bands, V-cut gullies with knife ridges between, a jagged rim (the north notch and south gap kept), crags, a spatter
cone on the west spur, a wider crater floor (rim radius 6.4, floor 4.6) with walk-out ramps at the two gaps. Rock is
flat-faceted and coloured by shape (mid purple-grey, dark steep faces, ash up top and on benches, rust patches, dark
gully beds). The older `old_vs_new_*` pictures show the smooth v2 shape.

Walking: Islands' rock is walkable up to about 1.3 m per metre (`soft: 1.15`); steeper (cliff bands, crag sides) is a
wall, and the walk graph knows it. `node tests/terrain/kaboom.mjs` checks the routes up and back.
