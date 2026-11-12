# Jankburg's Blender models

Map props for Jankburg (`shared/jankburg.js`), the Battle Royale city. They're built over the map's own boxes and fitted
onto them in the game (`public/js/propfield.js`, `meta.box`). They're look-only: the boxes stay the collision, the bots'
nav and the hits, and the gameplay hash of the map doesn't change. The ranked to-do list is
`docs/maps/jankburg/MODEL_LIST.md`.

| script | makes | notes |
|---|---|---|
| `make_jb_fountain.py` | `p_jb_fountain.glb` | the Smiling Fountain in the plaza: a marble basin (pink panels, brass finials, a mosaic floor of coins), a pedestal with a SMILE: IT'S MANDATORY plaque, a brass cup, and a 12 m glossy smiley with a face on both sides (domed eyes, one pupil wandering, a toothy grin, a chrome nozzle spitting into the pool). One copy; `propOf('jb_fountain')` wraps `fountain()`'s boxes (the benches stay theirs). 16k tris, far LOD 1k. `-- --qa` runs the asset QA gate (`--qa-parts` names the parts) |
| `make_jb_wall.py` + `jbkit.py` | `p_jb_wall.glb`, `p_jb_merlon.glb` | the firewall: a 6 m precast module (board-formed concrete with tie holes, a hazard plinth, half pilasters on each joint, the pink neon in a steel channel on both faces, a coping you run along with a yellow edge line on the city side, CCTV and conduit outside, a lamp and a cable tray inside), four art variants as nodes `v0`..`v3` (FIRE / WALL stencils that read FIREWALL on neighbouring modules, a YOU ARE NOW LEAVING THE PRODUCT plate, a ☺ STAY INSIDE poster and a tag); and the merlon. `wallKit()` in `cityWall()` fits a module onto every full-height piece of the wall boxes (stretched to whole modules); each merlon box is a `propOf('jb_merlon')`. ~250 tris a module, 22 far. `jbkit.py` = atlas cells, boxes with per-face atlas UVs, the concrete painter, the QA call |
| `make_jb_gate.py` | `p_jb_gate.glb` | the four gates, one node each (`N` Data Gate, `S` Freight Gate, `E` East Toll, `W` West Toll: only the name plate changes): gatehouses with a pedestrian tunnel, name plates outside, HAVE A NICE DAY inside, the sign bridge's steel frame and lights (the two pictures stay the map's), toll booths, boom barriers. `propOf('jb_gate', ..., { v: gate.id })` round the gate's boxes (not the pictures, not the jersey barriers). ~1k tris a gate |

Run with `blender52 -b --python tools/blender/jankburg/<script> -- [--qa] [--no-sheet] [--no-export]`; the sheet goes to
`tools/blender/sheets/`.
