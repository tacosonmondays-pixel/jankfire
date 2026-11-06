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
node tools/blender/shots.cjs 3100 <outDir> ar,shotgun,revolver 3,0   # viewmodel hip + ADS, code vs Blender, Too HD + Potato,
                                                                     # then the ADS check (exit code 1 if it fails)
node tools/blender/shots.cjs 3100 <outDir> ar,smg,shotgun 3 --check-only  # just the ADS check
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
| `make_smg.py` | `w_smg.glb` | MP5A3 pattern, x1.0, glowing flashlight forend |
| `make_redline.py` | `w_redline.glb` | PPS-43 pattern, x1.18, `needle` node (the tachometer, driven by HP) + `redline_vents` material (the barrel glows through the jacket) |
| `make_minigun.py` | `w_minigun.glb` | M134 pattern, x1.0, `barrels` node (spun by the game) |
| `make_sniper.py` | `w_sniper.glb` | AWM pattern, x1.67, `bolt` node (cycles with the bolt animation) |
| `make_chicken.py` | `w_chicken.glb` | Carl Gustaf M3 pattern, x1.05, rubber chicken in the muzzle |
| `make_bowling.py` | `w_bowling.glb` | backyard pneumatic cannon (PVC barrel, air tank, sprinkler valve, gauge) |
| `make_banana.py` | `w_banana.glb` | AKS-74U pattern, x1.1, a real banana as the banana mag, peel muzzle |
| `make_marbles.py` | `w_marbles.glb` | flintlock blunderbuss pistol, x1.1, mason-jar marble hopper |
| `make_water.py` | `w_water.glb` | 90s pump squirt pistol, x1.3, a soda bottle tank (neck forward, base toward you); nodes `water_wzN` (origin on the tank floor: scale y = how full) and `pump_wzB` |
| `make_taser.py` | `w_taser.glb` | conducted-energy pistol, x1.25, cartridge with dart ports, laser chin, 3-dot sights; node `led_wzN` (ARMED light, on the rear panel) |
| `make_remote.py` | `w_remote.glb` | CRT-era TV remote, life size, printed number pad, raised PAUSE / REWIND symbols, no sights; node `ir_wzN` (the game flashes it) |
| `make_radar.py` | `w_radar.glb` | hand-held traffic radar, life size, coiled cord; node `lamp_wzN` (blinks), `screen` metadata = the recess the game draws the LED readout in |
| `make_burst.py` | `w_burst.glb` | Hat Trick: FAMAS F1 pattern bullpup, nodes `mag` + `charge` |
| `make_lmg.py` | `w_lmg.glb` | Belt Sander: M249 pattern, nodes `mag` (ammo box), `cover` (feed cover hinge), `belt_00`..`belt_11` (links, hidden as the belt empties), `lmg_heat` material (the barrel glows with heat) |
| `make_dmr.py` | `w_dmr.glb` | Second Opinion: SVD pattern with a PSO-style scope, nodes `mag` + `charge` |
| `make_lever.py` | `w_lever.glb` | Yeehaw: Winchester 1892 pattern, nodes `lever` (front pin) + `lhammer` (spin-cock + lever throw are in `public/js/rifles.js`) |
| `make_autoshot.py` | `w_autoshot.glb` | Lawn Mower: Saiga-12 pattern auto shotgun, nodes `mag` + `charge` |
| `make_nailgun.py` | `w_nailgun.glb` | 21-degree framing nailer x1.6, turned so the drive points forward: handle = pistol grip, stick magazine of nails raked under the nose, spirit level taped on as the sight |
| `make_tennis.py` | `w_tennis.glb` | garage ball launcher x1.1: clear ball can barrel, side-fed hopper can, CO2 bottle foregrip, a tennis racket's handle + throat as the grip, a bit of strung head as the trigger guard |
| `make_cart.py` | `w_cart.glb`, `p_cart.glb` | the Shopping Cart Cannon (6in PVC, a cart basket wrapped round the barrel, cart handle foregrip, coin lock, castor monopod) + the real-size cart it fires (nodes `wheel_*`, spun by the game) |
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
  forward to set the eye distance), `hatAt` `[[x, y, z], height]`, moving parts (`pump`, `cylinder`, `hammer`, `bolt`), the code models' hooks
  (`needle`, `vents`, `barrels`) and `paint` (materials the flat look recolours).
- **Aiming**: put real sights high enough that the gun stays under the crosshair (the AR's flip-up peep, the shotgun's
  ghost ring, the Redline's tall aperture, the Peel Shooter's side-mount red dot). Guns without sights can carry `ads`
  `[x, y, z]`, the viewmodel pose while aiming (the bowling cannon tucks itself down and right). The ADS check in
  `shots.cjs` aims every gun at 1280x720, 1280x800 and 900x900 and FOV 70 + 120, renders only the viewmodel and fails if
  it covers more than 25% of the middle 40% x 40% of the screen.
- **Props**: vehicles face +x like the map builder's `car()`. Make the model match the boxes it stands in for
  (`shared/props.js` `PROPS`), feet on y = 0. Variants are separate nodes; give each its own origin with `part(..., pivot)`.
- **Look**: glossy and bevelled (the owner's pick, 2026-11-05). `?models=flat` in the address (or localStorage
  `jf_models = 'flat'`) shows a faceted no-gloss version for comparison, with each weapon's `paint` materials in its
  shared/weapons.js colour; it's never on by default.
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
