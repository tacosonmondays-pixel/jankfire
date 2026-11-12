# Crate + Range: what still needs a model

Walk-through on main at 1f85a6d, Too HD, from each spawn and from above (`walk_crate.jpg`, `walk_range.jpg` next to this
file; Crate: far / over / spawn 1 / spawn 2 / top, Range: back / left / over / right / spawn / spray). Box counts from
`tools/blender/inventory_maps.mjs`: Crate 57 boxes + 40 deco, Range 170.

Already models on these maps: the 2 m wooden crates on Crate (`p_crate`), Range's trees (`p_conifer`, `p_lollipop`) and
ad boards (`p_billboard`, `p_billboard_post`). The dummies are the player mannequins (not on this list).

How they get built: the props lane (`propOf()` in `shared/map.js`, a `p_<id>.glb` from a `tools/blender/make_*.py` in the
glossy bevelled look, fitted onto its boxes, falling back to them). Collisions stay the same boxes unless a line says so.

Ranked by what players see most (Training is where everyone lands first, so its firing line is at the top).

| # | map | what | now | plan | collision change | size |
|---|---|---|---|---|---|---|
| 1 | range | **the firing line**: the long bench you spawn behind, the sandbags in front of it, the 4 lane dividers on the left | a plank slab, 12 dirt-textured slabs, 4 thin planks | new models: a real range shooting bench (plank top on trestles, rubber mat, brass cases, ear-defenders, a JANKFIRE RANGE RULES card), a sandbag wall (stacked, tied, sagging hessian bags), lane divider baffles | no | 40 m bench, 12 bags rows, 4 baffles |
| 2 | crate | **the toy tower under the arena**: 3 giant face blocks the toy box floats on (the first thing you see on the menu and on the way down) | 3 boxes with a face sticker on every side | full redo as giant wooden toy blocks: bevelled painted wood, raised carved faces (the same googly faces), grain, chipped corners, the middle one still turned | no (render-only) | 26 m / 24 m / 36 m cubes |
| 3 | crate | **the playroom** around it: the crayons, the "ball", the bed, the train set, the block stack, the ceiling lamp, the window | boxes (square crayons, a cube ball, a slab bed) | new models: round crayons with paper wrappers and worn tips, a real bouncy ball (striped), a kid's bed (headboard, duvet, pillow), a wooden train (engine, carriage, track with sleepers), a stacked-block pile, a pendant lamp, a window frame with sill | no (render-only) | room 840 m |
| 4 | crate | **the arena middle**: the 5 x 3 m face block with the teal lid you fight round | a face-textured box + a slab | remodel: a toy shape-sorter cube (teal lid with star / circle / square holes, raised faces on the sides) | no | 5 x 3 x 5 m + 7 m lid |
| 5 | range | **the backstop berm** the bullets end up in at the end of the lanes | 2 dirt boxes | new model: an earth berm with a timber target frame, a row of paper targets, a RED FLAG pole | no (render-only) | 120 x 16 m |
| 6 | range | **the two watchtowers** at the back corners | 4 sticks, a deck, a roof slab | new model: a timber range tower (cross-braced legs, a ladder, railing, a corrugated roof, a red light) | no (render-only) | 4.4 x 10.8 m |
| 7 | crate + range | **the floating pink parkour blocks** (Crate's 4 corner hops and the gold top; Range's 6 stepping blocks and the stone pillar) | flat boxes | new models: Crate: giant toy building bricks (studs on top) and a gold star block; Range: pink stepping blocks with hazard edges, the pillar as a concrete column | no | 2.5-3 m blocks |
| 8 | crate | **the crate walls and toy cubes on the arena** (2 long crates, 4 small red / blue cubes) | box crates, plain cubes | the long crates on `p_crate`'s look (stretched planks, stencils), the cubes as toy bricks | no | 5 x 2 x 1 m, 1.2 m |
| 9 | range | **the boundary fence** round the field | 60 posts and a wire box each | new model: a post-and-wire fence section (galvanised posts, three wires, a KEEP OUT sign every few) | no (render-only) | 10 m sections |
| 10 | range | **the left ledge and the spray range wall** | a stone slab with the `missing` texture strip (on purpose: keep the joke), a 16 x 6 m brick box | remodel: the spray wall as a steel-plated concrete backstop (the spray-pattern marks still draw on it, `sprayrange.js`); the ledge keeps its boxes | no | 16 x 6 m |

Not on the list: the jump pads (shared by every map), the floor and ground (fine as they are), the dummies (characters).

## Order of work
1. `claude/map-crate-rangeline`: the firing line (#1).
2. `claude/map-crate-toytower`: the toy tower and the arena middle (#2, #4).
3. `claude/map-crate-playroom`: the playroom (#3).
4. `claude/map-crate-rangeback`: the berm and the watchtowers (#5, #6).
5. `claude/map-crate-blocks`: the parkour blocks, the long crates and toy cubes (#7, #8).
6. `claude/map-crate-fence`: the fence and the spray wall (#9, #10).
