# Blender pipeline

Models are built **from code** in headless Blender, exported as `.glb` into `public/models/`, and swapped into the
game by the client. Every model also gets a turnaround sheet in `tools/blender/sheets/` to review it without opening
Blender. Visual only: collisions, hitboxes and bot nav stay boxes.

## Run it
```
blender --version                          # 4.0.2 in the cloud env. missing: apt-get install -y blender python3-numpy libegl1 libgl1-mesa-dri libegl-mesa0
blender -b --python tools/blender/make_ar.py              # glb + sheet (~20 s)
blender -b --python tools/blender/make_ar.py -- --no-sheet  # glb only (~5 s)
blender -b --python tools/blender/make_ar.py -- --no-export # sheet only
tools/blender/make_all.sh                                 # everything, 3 at a time
```
Then check it in the real game (start a server first: `PORT=3100 node server.js`):
```
node tools/blender/shots.cjs 3100 <outDir> ar,shotgun,revolver 3,0   # viewmodel hip + ADS, code vs Blender, Too HD + Potato
node tools/blender/shots_props.cjs 3100 <outDir> 3,0                 # props on Warehouse/Suburb vs their boxes + a showcase
```
Optional size squeeze (not needed, files are 70-600 KB): `npx @gltf-transform/cli optimize in.glb out.glb --compress quantize
--texture-compress false`. Don't use Draco or meshopt: the client has no decoders (and the apt Blender has no Draco).

## What's here
| file | makes | notes |
|---|---|---|
| `lib.py` | the kit | game-coordinate primitives (`box`, `cyl`, `lathe`, `side` side-profile extrusions, `side_x`, `tube`, `wheel`, booleans with `cut`), materials (`mat`) with generated crusty textures (`tex_noise`, `tex_wood`, `tex_stripes`, `tex_camo`, `tex_canvas` + a 5x7 bitmap font), `part` for moving nodes, `finish` + `export` + `sheet` |
| `make_ar.py` | `w_ar.glb` | M4-pattern carbine, x1.54 |
| `make_shotgun.py` | `w_shotgun.glb` | 870-pattern pump, x1.05, `pump` node |
| `make_revolver.py` | `w_revolver.glb` | 6in .357, x1.5, `cylinder` + `hammer` nodes |
| `make_car.py` | `p_car.glb` | sedan, paint material `car_paint` (recoloured per car) |
| `make_bus.py` | `p_bus.glb` | conventional school bus |
| `make_forklift.py` | `p_forklift.glb` | counterbalance forklift |
| `make_pallet.py` | `p_pallet.glb`, `p_pallet_load.glb` | EUR block pallet, empty + shrink-wrapped load |
| `make_rack.py` | `p_rack.glb` | pallet rack: nodes `bay` (6 m) and `frame` |
| `make_streetlight.py` | `p_streetlight.glb` | 6 m cobra-head street light |
| `make_numballs.py` | `p_numball.glb` | glossy toy number balls, nodes `n0`..`n9` |

## Rules that make a model drop straight in
- **Build in game space**: three.js axes and metres (x right, y up, -z forward); `lib.gv()` converts to Blender. A
  weapon keeps the code model's muzzle point and grip/hand area (`public/js/models.js` `WB`), so the viewmodel pose, ADS,
  muzzle flash, tracers, twirl pivot and recoil all still fit. Real guns: take real millimetres and pick one scale factor
  that lands the muzzle on the code model's (each script says which).
- **Metadata** goes on the root empty as `jf` (exported as glTF extras, read by `public/js/glbkit.js`):
  `muzzle`, `sight` `{ y, z }` (the line of sight; the game puts your eye 0.17 m / scale behind `z`, so push `z` back or
  forward to set the eye distance), `hatAt` `[[x, y, z], height]`, and moving parts (`pump`, `cylinder`, `hammer`).
- **Props**: vehicles face +x like the map builder's `car()`. Make the model match the boxes it stands in for
  (`shared/props.js` `PROPS`), feet on y = 0. Variants are separate nodes; give each its own origin with `part(..., pivot)`.
- **Materials**: glTF keeps base colour/texture, roughness, metallic, emission, alpha and clearcoat. Bake colour into the
  texture (`tex_*` take the colour). Emissive materials stay glowing under weapon skins. Textures are tiny and nearest
  filtered on purpose (ugly-on-purpose, matches Potato through Too HD).
- **Budget**: weapons up to ~10k tris (viewmodel), props 2-16k. Keep bevels small and segment counts modest.

## How the game uses them
- `public/js/glbkit.js`: `prepAuthored` takes any glb with `jf` metadata: nearest-filtered textures, the Potato vertex
  snap (`jankify`), a small studio env map for gloss, glows kept through skins. `authored(id)` gives a shared copy.
- Weapons: `buildWeapon` (models.js) swaps in `w_<id>` as built (no fitting) and reads muzzle/sight/hat from it.
  A missing or broken file = the code model, as before. Weapon skins (finishes, hats, effects) work on top.
- Props: a map's boxes carry `{ pv: id }`; while `p_<id>` is loaded `world.js` skips drawing those boxes and `props.js`
  draws the model at the spot `L.P()` recorded. Collisions never change. In a map builder:
  ```js
  prop(L, 'forklift', x, z, r)                  // catalog boxes (shared/props.js) + the model
  const pv = L.P('bus', x, z, r); L(..., 'caryellow', pv)   // your own boxes, drawn only when the model is missing
  ```
  `r` = quarter turns (like `B.local`), opts `{ v: variant, color: 'carblue', s: scale, y }`.
