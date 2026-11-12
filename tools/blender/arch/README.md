# Map architecture in Blender (PS1 / grimy-corporate look)

Buildings, stairs, walls and fences drawn as Blender models over the maps' own collision boxes. Visual only: physics,
bots and hits keep the boxes exactly as they were (`node tools/arch/gamehash.mjs` before/after must match).

## How it fits together
1. **Tag the boxes** in `shared/map.js`: `const A = B.arch('home', x, z, rot, y, { paint })` gives a local frame like
   `B.local()`; every box drawn through `A` gets `{ av: 'home', ai: <placement> }`. `A.plain` is the same frame without
   the tag (furniture, props). For helpers that add boxes themselves (`roofTop()`): `n0 = B.boxes.length; ...;
   B.archSince(n0, id, x, z, rot, y)`. The placement list ends up in `map.boxes.arch`.
2. **Dump** them in the building's own frame: `node tools/arch/dump.mjs <map> <id> tools/blender/arch/boxes/<id>.json`
   (it checks every placement has the same boxes).
3. **Texture kit**: `python3 tools/blender/arch/texkit.py [--sheet out.png]` writes `public/models/arch/kit/*.png` +
   `kit.json`: 32-128 px seamless textures cut to a 16-colour clut, 15-bit colour, 4x4 ordered dither, 1-bit alpha. Light
   grey ones (siding, shingle, stucco, trim, louvre, picket, corrugated, metal) are tinted. `decals.png` is an atlas of fake
   ads, signs, stickers, graffiti, grime (cells by name in `kit.json`). Shared with the props lane.
4. **Build**: `blender52 -b --python tools/blender/arch/make_<id>.py` -> `public/models/arch/<id>.glb`. `archkit.py`
   reads the boxes and builds quads in game space, one mesh per material: walls grouped into planes with their openings
   found and dressed (casings, sills, broken panes, doors swung open), real stairs over solid step boxes (treads with a
   nosing, risers, stringers, newels, balusters, a handrail), caps, bands, corner boards, decals, then vertex AO by
   ray-casting (written as COLOR_0). `dress_shell()` does a whole `shell()` building. It prints z-fight pairs; keep it 0.
5. **In game**: `public/js/archfield.js` loads the models listed in `ARCH_IDS` for the map, merges every placement into
   one mesh per material (each house's paint baked into its vertex colours: material names ending `@siding` / `@roof` /
   `@trim` take `placement.paint`), and `world.js` skips the tagged boxes while the model is in. `?arch=0` turns it off.
6. **Check**: `blender52 -b --python tools/blender/arch/sheet.py -- public/models/arch/<id>.glb out.png` renders a
   turnaround; run the `blender-asset-qa` gate on the glb.

## Rules
- Anything solid in the game looks solid, anything open looks open: railings that are boxes are panels, windows stay holes
  (only shards in the corners), doors are swung back against the wall, nothing big hangs out where you'd try to stand.
- Visual steps sit exactly on the collision steps (the treads are the step tops). Relief stays shallow (a few cm).
- Paint comes from the map (`paint: { siding, roof }` = map material keys, colours in `archfield.js` `PAINT`).

## Next to tools/blender/ps1.py (PR #83)
`ps1.py` repaints one finished model into a single baked PS1 texture (guns, props, vehicles). Architecture uses this kit
instead: buildings are huge and tile, so they get small seamless textures in world-scale UVs plus vertex AO. Both
use the same treatment: a small palette per texture, 15-bit colour, ordered dither, matte, no mipmaps up close. Shared
conventions for glbs that use the kit: no embedded images; each material carries extras `tex` (kit image name), `tile`,
`col` (hex factor), and optionally `paint` (a slot the map repaints), `alpha` (1-bit cutout), `glow` / `glowmap`
(emissive) and `nocast` (no sun shadow); `shine` / `spec` (a glossy coat: Phong, the same diffuse light plus a
highlight, for paint, zinc and chrome) and `nomip` (no mipmaps: see-through wire mesh, which mipped melts into a sheet or
vanishes). The client loads each kit image once by name (archfield.js `tex()`).

## Models
- `make_mastyard.py` -> `mastyard.glb`: Scary Forest's radio mast and its fenced yard (site B), with the guy anchors.
