# Jankburg's Blender models

Map props for Jankburg (`shared/jankburg.js`), the Battle Royale city. They're built over the map's own boxes and fitted
onto them in the game (`public/js/propfield.js`, `meta.box`). They're look-only: the boxes stay the collision, the bots'
nav and the hits, and the gameplay hash of the map doesn't change. The ranked to-do list is
`docs/maps/jankburg/MODEL_LIST.md`.

| script | makes | notes |
|---|---|---|
| `make_jb_fountain.py` | `p_jb_fountain.glb` | the Smiling Fountain in the plaza: a marble basin (pink panels, brass finials, a mosaic floor of coins), a pedestal with a SMILE: IT'S MANDATORY plaque, a brass cup, and a 12 m glossy smiley with a face on both sides (domed eyes, one pupil wandering, a toothy grin, a chrome nozzle spitting into the pool). One copy; `propOf('jb_fountain')` wraps `fountain()`'s boxes (the benches stay theirs). 16k tris, far LOD 1k. `-- --qa` runs the asset QA gate (`--qa-parts` names the parts) |

Run with `blender52 -b --python tools/blender/jankburg/<script> -- [--qa] [--no-sheet] [--no-export]`; the sheet goes to
`tools/blender/sheets/`.
