# Desert (Dry Gulch): what still needs modelling (DRAFT, parked)

Status: parked 2026-11-12 (the session moved to Battle Island). Walk-through done (Too HD contact sheets below:
`walk_dm_a/b/c.jpg` = Desert, `walk_sd_a.jpg` = Desert S&D), `tools/blender/inventory_maps.mjs` run (desert 624 prop +
1637 architecture + 770 terrain boxes; desert_sd 569 + 1191 + 269). The ranking below is a first pass from the code,
the inventory and the walk-through; each line still needs its size and plan checked before work starts.

Already Blender: wagons, camels, hay, stalls, tents, graves, saguaros, palms, adobe huts (arch), the rim rocks
(rocks_desert / _sd), crates, barrels, containers.

| # | What | Now | Plan | Collision change | Notes |
|---|---|---|---|---|---|
| 1 | Mine headframe (`headframe()`, A site on S&D, mesa top on Desert) | 25 boxes | new prop `p_headframe` | no | **started**: `tools/blender/make_frontier.py` (timber gallows frame, red sheave, ore skip, counterweight, JANK MINING CO. board), ~11.5k tris, not wired into map.js / not tested in game yet |
| 2 | The payroll train (`train()`: 4-4-0 engine, tender, boxcar, flatcar, caboose; B site on S&D, the depot on Desert) | 32 boxes + 50 wheels + 166 track | new prop(s), one per car | no | walkable boxcar / caboose stay boxes |
| 3 | Frontier false-front buildings (`frontier()` + `shell()` walls, stairs, slabs: saloon, bank, hotel, livery, store, sheriff, undertaker, assay, mine co., depot) | ~1100 boxes, 7-8 sizes | arch models per size / a parametric kit | no | biggest box count on the map |
| 4 | Town wall, gate towers, corner towers, battlements | 252 / 151 boxes | arch model (adobe wall kit + gatehouse) | no | seen from everywhere |
| 5 | Church + bell tower | shell + boxes | arch model | no | west bank landmark |
| 6 | Stone bridge + gateposts + lanterns | 13 + 20 boxes | prop / arch | no | the mid lane |
| 7 | Rail trestle over the canyon | 77 boxes | prop | no | north lane |
| 8 | Rope bridge | 55 boxes | prop | no | south lane |
| 9 | Water tanks on stilts (`waterTank()`, 2-3 copies) + windpumps (`windpump()`, 1-2) | 26-39 + 21-42 boxes | props `p_stilttank`, `p_windpump` (same file as #1) | no | |
| 10 | The mesa + mine mouth, tunnel lintel, rock bands | ~70 boxes | rock model like rocks_desert | no | A site's backdrop on S&D |
| 11 | Mission ruin, old fort ruin, watchtower | ~90 boxes | arch | no | |
| 12 | Small props: ore carts, founder's cart, well, powder store, outhouses, forge + anvil, crypt, dead tree, troughs, hitching rails, buffer stop, crossing sign | ~120 boxes | prop batch | no | |
| 13 | Ground scatter: sagebrush, tumbleweeds, dirt patches; outside dunes | 151 + 132 look-only | props / dune mesh | no | |
