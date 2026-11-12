# Dead Mall: what still needs modelling

The walk-through (2026-11-11) was played in Zombies at Too HD. It covered every area, the objectives (crate, power, shutters, wall guns, windows, colas, the Voider, the Cheat Machine) and the props up close, plus `tools/blender/inventory_maps.mjs`. The pictures are in `walkthrough.jpg`:
- row 1: the six areas
- row 2: the objectives
- row 3: the props

**The short version:** apart from the machines, the mall doesn't read as a mall. It's six plaster boxes with a maroon lid, a tiled floor and coloured blocks. There are no shopfronts, signage, railings, escalators or skylight. The arcade is two containers with a light strip. The toy store is three giant painted slabs. The mystery crate, the power switch and the shutters (what you look at every round) are code boxes with a canvas on them.

Already Blender models, so not on this list: the window barricades (`x_zmboard`), the Cheat Machine (`x_zmmachine`), the Warranty Voider (`x_zmvoider`), every cola machine (`x_zmcola`), the zombies themselves, and the dock's stacked crates (`p_crate`, matched by size).

Ranked by what players see most: objectives first, then the mall's shell, then props. Columns:
- **now:** what's there today.
- **plan:** what the model will be.
- **collision:** what happens to the boxes you bump into.
- **size:** the triangle budget.

Every model covers its own boxes. Map props go into one kit file, `p_mallkit.glb` (a node per piece, placed with `W.P('mallkit', ...)` like the school and hospital kits). Objectives are lazy `x_zm*` files with a code fallback in `public/js/zombies.js`. Collision stays boxes everywhere. `tools/arch/gamehash.mjs` stays identical apart from the look-only `pv` tags.

| # | What | Now | Plan | Collision | Size |
|---|---|---|---|---|---|
| 1 | **The mystery crate** (`buildCrate`, everyone's favourite gamble) | A brown box with a box lid, a flat "? ? ?" sticker and a cyan cone of light. | `x_zmcrate`: a beat-up shipping crate turned mall prize box. Planked sides with steel corner caps and stencilled ??? and FRAGILE-ISH, a hinged lid on real hinges (the `lid` node, origin on the hinge), a padlock hanging open, straw packing inside, a glowing gap. The game keeps the beam and the weapon flicking out of it. | Unchanged (the 1.8 x 0.9 x 0.9 box). | 2–3k |
| 2 | **Roller shutters ×7** (the doors you buy) | A flat grey box with the canvas sign, and a yellow-black striped box as the housing. | `x_zmshutter`: a real roller shutter. Ribbed steel slats (the `curtain` node the game slides up), a bottom rail with a handle and a padlock hasp, side guide channels, and a round barrel housing with end plates and a hazard band. The area's name and price stay the game's spray-paint canvas, laid on the slats. | Unchanged (the 4 x 3 door box; the housing box stays look-only). | 1.5–2.5k |
| 3 | **The power switch** (the dock's objective) | A black box, a box lever and a yellow POWER plane. | `x_zmpower`: a big wall breaker. A grey cabinet with an open door, a knife-switch handle (the `lever` node), fuses, a DANGER plate, conduit up into the ceiling, and a lamp the game lights. | Unchanged (it hangs on the wall box). | 1.5–2k |
| 4 | **The atrium's elevator core** (the big loop in the middle) | One 7 x 8 x 4 blue glass-block cube. | A glass scenic lift shaft. Chrome mullions, a stuck car half-way with its doors jammed open a crack, call buttons and a floor dial at the bottom, an OUT OF ORDER sign, a planter skirt round the base. | Unchanged (the cube stays the loop). | 3–5k |
| 5 | **The mall shell: shopfronts and signage** (`wall()` ×9 + the areas) | Bare plaster walls, a maroon ceiling slab, nothing that says "mall". | One look-only dressing model per wing, laid on the inside wall faces and the ceiling. Dead shopfronts (glass with roller grilles, dead neon store names like PRETZEL PALACE, SOCKS ETC, BRAINS & NOBLE), pilasters, a wall base and cornice, a dropped-ceiling grid with troffer lights, and a skylight in the atrium. Planned as `arch/mall_*.glb` covering the wall boxes' faces (walls stay boxes). The wall guns, shutters and machines keep their spots clear. | Unchanged, look-only. | 6–10k a wing |
| 6 | **The arcade cabinets** (6 rows of back-to-back cabinets) | Red and blue shipping containers with a glowing strip down each side. | Rows of real upright cabinets back to back. Each has a marquee, a CRT bezel, a control panel with stick and buttons, a coin door and side art. A few are different (a driving game, a dance mat, a claw machine). Screens glow with the power. Mallkit `cabrow` (one node per 9 m row). | Unchanged. | 2–4k a row (instanced) |
| 7 | **The toy store shelves** (3 full-height loops) | Three 14 m slabs painted pink, blue and yellow, and five coloured cubes. | Mallkit `toyshelf`: double-sided gondola shelving to the ceiling, with end caps, price strips and toys (plushies, boxed robots, balls, a dinosaur, block sets), some fallen on the floor. The loose cubes become toy blocks, a ball pit tub and a rocking horse. | Unchanged. | 3–5k per shelf |
| 8 | **The entrance hall's info kiosk** (the first thing you see) | A wooden box, a tile slab and a plaster post. | Mallkit `kiosk`: an oval info desk with a laminate top, a YOU ARE HERE directory on the post (map of the mall), a dead monitor, a brochure rack, and a bell. The two pillars get mall cladding with mirror strips. | Unchanged. | 2–3k |
| 9 | **The food court** (9 tables and the burger counter) | Wooden cubes and a tile slab with a red top. | Mallkit `foodtable`: a round table on a pedestal with four swivel seats, trays and cups left on it. `burgerbar`: a fast-food counter with a menu board (BRAIN FREEZE, JANK MEAL), registers, a soda fountain and a heat lamp. | Unchanged. | 1k a table, 3k the counter |
| 10 | **Planters, benches, the entrance hedges** | Green cubes and wooden slabs. | Mallkit `planter` (a tiled planter box with a fake ficus and gum under the rim), `bench` (a slatted mall bench with chrome arms), `hedge` (a dead box hedge in a long planter). | Unchanged. | 600–1.2k each |
| 11 | **The loading dock's forklift and pallet** | A yellow box with a glass box on top, and a wooden slab. | Use the existing Blender forklift (`p_forklift`) and pallet (`p_pallet`) through the catalog. Free. | Unchanged. | already built |
| 12 | **Wall-gun boards ×12** | A flat chalkboard picture with the gun hung on it. | Mallkit-style `x_zmchalk` frame: a real wooden-framed chalkboard with a chalk ledge, chalk stubs and two screws. The chalk outline and price stay the game's canvas. | None (wall-mounted). | 300 |
| 13 | **The back alleys ×16** (behind every window) | A road slab, brick boxes, a lid and black "tire" bin bags. | Mallkit `alley`: a brick alley end with a dumpster, real bin bags, a drainpipe and a puddle, so the windows look out onto something. | Unchanged. | 1.5k (instanced ×16) |
| 14 | **Ceiling lamps** (`buildLamps`, instanced) | Flat boxes. | A 2x4 troffer with a diffuser grid. Dead ones look dead, lit ones glow with the power. | None. | 100 (instanced) |

Order of work: 1–3 (the objectives, one PR each or the crate and power together), 4, then 6–10 as mallkit batches, then 5 (the shell, the biggest one), then the rest. Each gets:
- the asset gate (0 errors)
- the tests
- `tools/arch/gamehash.mjs` showing it is look-only
- a Zombies run showing the objective still works (buy the door, spin the crate, throw the power)
- before/after pictures in Too HD plus one Potato
- a patch-notes line in the PR

Shared code note: `public/js/zombies.js` builds the crate, shutters, power and boards for every Zombies map (Jankfield High and Second Opinion General too), so items 1–3 and 12 upgrade all three maps at once.
