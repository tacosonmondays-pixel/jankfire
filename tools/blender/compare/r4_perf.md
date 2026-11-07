# Round 4 props: draw calls and triangles

renderer.info for the world pass (the sun's shadow pass included; one is forced each measured frame) in a bots match at
Too HD, 1280 x 720, from 12 fixed views (3 spawns x 4 directions, 6 frames each), players and particles hidden so
only the map, its props and the traffic count. main = origin/main at cc731b9, branch = claude/blender-pipeline.
Measured with `node tools/blender/perf_props.cjs <port> <out.json> jankburg,suburb,skyline 3` (software GL in the sandbox).

| map | draw calls avg (worst view) main | branch | triangles avg (worst view) main | branch |
|---|---|---|---|---|
| jankburg | 1508 (3189) | 1084 (2179) -28% | 653k (950k) | 614k (808k) -6% |
| suburb | 637 (999) | 388 (525) -39% | 692k (861k) | 562k (597k) -19% |
| skyline | 360 (490) | 316 (455) -12% | 591k (606k) | 526k (567k) -11% |

Scene totals (everything built, view independent): jankburg 51 instanced draws for 2917 prop copies, suburb 65 instanced draws for 1791 prop copies, skyline 51 instanced draws for 2363 prop copies.
