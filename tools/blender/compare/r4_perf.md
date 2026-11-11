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

## Re-measured after merging main (2026-11-10)

Same script, Suburb only, against main at a9897c3 (shaped ground, Blender buildings and rocks in both):

| preset | draw calls avg (worst) main -> branch | triangles avg (worst) main -> branch |
|---|---|---|
| Too HD | 648 (1,076) -> 463 (787), -29% | 785k (1,026k) -> 713k (800k), -9% |
| Potato | 386 (784) -> 253 (421), -34% | 430k (553k) -> 338k (366k), -22% |

Branch only, Too HD, bots matches with no page errors: Jankburg 1,143 (2,758) calls, 410k (663k) triangles; Skyline 328 (515)
calls, 531k (565k) triangles. Frame time is not in these numbers (software GL in the sandbox makes it meaningless).
