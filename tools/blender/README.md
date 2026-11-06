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
node tools/blender/shots.cjs 3100 <outDir> ar:ar_toy,cig,bow 3      # skins are weapon:model; weapons that can't aim get an
                                                                     # "in use" shot instead (lit, drawn, swung)
node tools/blender/shots.cjs 3100 <outDir> ar,smg,shotgun 3 --check-only  # just the ADS check
node tools/blender/shots_props.cjs 3100 <outDir> 3,0                 # props on Warehouse/Suburb vs their boxes + a showcase
```
Optional size squeeze (not needed, files are 70-600 KB): `npx @gltf-transform/cli optimize in.glb out.glb --compress quantize
--texture-compress false`. Don't use Draco or meshopt: the client has no decoders (and the apt Blender has no Draco).

## What's here
| file | makes | notes |
|---|---|---|
| `lib.py` | the kit | game-coordinate primitives (`box`, `cyl`, `lathe`, `side` side-profile extrusions, `side_x`, `tube`, `sweep`, `loft` (any cross-section along a path, per-face materials), `wheel`, booleans with `cut`, `jitter` for fur / ash / snow), materials (`mat`, `emit_tex` for glowing textures) with generated crusty textures (`tex_noise`, `tex_wood`, `tex_stripes`, `tex_camo`, `tex_canvas` + a 5x7 bitmap font), UVs (`uv_box`, `uv_planar` decals, `uv_cyl` wrap-around labels), `part` for moving nodes, `zone_join` (wrap zones), `clone_scaled` (a thrown copy), `finish` + `export` + `sheet` (`exposure` for pale things) |
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
| `make_akimbo.py` | `w_akimbo.glb` | MAC-10 pattern (stock pushed in), x1.1, one gun the game puts in both hands: `cocker` knob node (snaps back per shot), `mag` node (origin at its base, slides out along `dir`), `tags` L / R sticker nodes (one shows per hand). `-- --qa` runs the asset-QA gate on every part |
| `make_sawnoff.py` | `w_sawnoff.glb` | 12 ga side-by-side hammer coach gun, sawn off (300 mm barrels, stock cut to a pistol grip), x1.0: `hinge_wzB` node (the barrels break open round the pin in the knuckle at (0, -0.002, -0.05), like a real side-by-side, so the shells come out over the action; `forend_wzA`, `shell1_wzN` / `shell2_wzN` ride on it), `hammerR_wzN` / `hammerL_wzN` (modelled cocked, the game drops them 0.75 rad onto the strikers) |
| `make_pistol.py` | `w_pistol.glb` | Plan B: 1911A1 / Government pattern .45 (5in), x1.5 like the revolver: `slide_wzB` (kicks back / locks open, the gold barrel stays and pokes out), `mag_wzB` (origin at the base pad's middle, slides out along `dir` = the 18 degree grip rake), `hammer_wzN` (ring hammer modelled cocked, origin on its pin). Gold-filled roll marks (PLAN B / TOLD YOU SO), pearl grips with B medallions |
| `make_car.py` | `p_car.glb` | sedan, paint material `car_paint` (recoloured per car) |
| `make_bus.py` | `p_bus.glb` | conventional school bus |
| `make_forklift.py` | `p_forklift.glb` | counterbalance forklift |
| `make_pallet.py` | `p_pallet.glb`, `p_pallet_load.glb` | EUR block pallet, empty + shrink-wrapped load |
| `make_rack.py` | `p_rack.glb` | pallet rack: nodes `bay` (6 m) and `frame` |
| `make_streetlight.py` | `p_streetlight.glb` | 6 m cobra-head street light |
| `make_numballs.py` | `p_numball.glb` | glossy toy number balls, nodes `n0`..`n9` |
| `make_cig.py` | `w_cig.glb`, `w_cig_cigar.glb` | king-size filter cigarette x2.2 (MAY CAUSE JANK), fat gordo cigar x1.45; the ember is the `tip` node |
| `make_cards.py` | `w_cards.glb`, `pj_card.glb`, `w_reverse.glb`, `w_reverse_skip.glb` | rounded glossy cards: the deck's `fan` (`card0`..`card4` face meshes, weapons.js deals your hand onto them), the thrown card, the Reverse / Skip cards (`card` node) |
| `make_bread.py` | `w_bread.glb`, `w_bread_croissant.glb` | baguette x2.7 with real scores, in a bakery sleeve that says BREAD; croissant x8.7 |
| `make_spoon.py` | `w_knife_spoon.glb`, `w_knife_ladle.glb` | the Knife's Spoon skin (the tablespoon held like a knife, x0.915, on its side) and Ladle skin (the soup ladle, bowl down, handle on the grip axis, chicken noodle soup still in it). The Spoon weapon itself is gone: it's the knife now |
| `make_knife_pizza.py` | `w_knife_pizza.glb` | restaurant pizza wheel, life size (100 mm wheel, fork, thumb guard), a pepperoni stuck on, cheese string, NOT A KNIFE |
| `make_knife_keycard.py` | `w_knife_keycard.glb` | ☺ CORP ID badge x1.2 on a lobster claw, the lanyard wound into the grip (loop + clasp off the butt), bottom edge ground sharp |
| `make_knife_fish.py` | `w_knife_fish.glb` | frozen Atlantic mackerel x1.3 held by the tail stock, frost + ice lumps, curled mid-flop, FRESH sticker |
| `make_katana_skins.py` | `w_katana_baguette.glb`, `w_katana_neon.glb` | katana skins on the code katana's layout; the blade is its own node (`katBlade`, origin at the guard face, `katLen`) so it grows with kills. Baguette (scored, bitten, cheese-box tsuba, twine ito); Neon Tube (glowing tube in glass, heatsink tsuba, glowing circuit ito, cord hanging out the back) |
| `make_bread_sliced.py` | `w_bread_sliced.glb` | FAMILY SIZE sliced loaf (42 slices) in a polka-dot bag clear on top, twisted neck = handle, twist tie |
| `make_slipper_flipflop.py` | `w_slipper_flipflop.glb`, `pj_slipper_flipflop.glb` | beach flip-flop, real size, worn foot imprint, SALE tag, gum underneath; thrown x1.6 |
| `make_slipper.py` | `w_slipper.glb`, `pj_slipper.glb`, `w_slipper_croc.glb`, `pj_slipper_croc.glb` | fluffy house slipper (a MOM tag), foam clog with charms; thrown ones x1.6 |
| `make_projectiles.py` | `pj_chicken`, `pj_bowling`, `pj_banana`, `pj_peel`, `pj_frag`, `pj_smokegren` | the rubber chicken (with a firework on its back), the giant bowling ball, the banana, the peel on the floor, a pineapple frag (PULL ME tag), a canister smoke (DO NOT INHALE) |
| `make_slapper.py` | `w_slapper.glb`, `w_slapper_foam.glb`, `w_slapper_paw.glb` | jelly-rubber toy hand on a candy stick (real hand x1.35, metaballs, SLAP knuckle tattoos), stadium foam finger (#1 / U R #2), grizzly paw (BEAR ARMS); the slapping end is the `hand` node; `--only=` builds one |
| `make_scythe.py` | `w_scythe.glb`, `w_scythe_rifle.glb`, `w_scythe_reaper.glb` | the killstreak's two forms from one rifle (Remington-700-size action, 34 mm scope) + an Austrian scythe blade on a hinge (`blade` node); the rifle's `bolt` cycles; the Reaper (bone blade, skull pommel, IF FOUND, YOU'RE NEXT) |
| `make_revolver_flint.py` | `w_revolver_flint.glb` | late-1700s holster flintlock x1.05 (TOTALLY A REVOLVER); the cock is the `hammer` node (under a flipped empty so +x swings it the right way) |
| `make_gumball.py` | `w_marbles_gumball.glb` | counter-top gumball machine x1.0 stretched into a pistol: see-through globe, 28 gumballs, the chrome chute is the barrel (NO REFUNDS) |
| `make_redline_hotrod.py` | `w_redline_hotrod.glb` | the Redline x1.18 in candy cherry with a flame job, chrome, fuzzy dice; zoomie exhaust throats share `redline_vents`, so they glow with your HP; same `needle` |
| `make_ar_toy.py` | `w_ar_toy.glb` | foam-dart blaster about x1.3 a real toy: clamshell screws, priming slide, see-through dart clip, tall plastic sights (NOT A TOY) |
| `make_ar_bullpup.py` | `w_ar_bullpup.glb` | original 24in DMR bullpup x1.38, carry-handle optic, smoke mag behind the grip (FRONT TOWARD ENEMY); `port` = shells fly out by your cheek |
| `make_smg_uzi.py` | `w_smg_uzi.glb` | Uzi-pattern open bolt x1.45, raised sights (FITS MOST POCKETS, your keys on the sling loop) |
| `make_shotgun_double.py` | `w_shotgun_double.glb` | side-by-side 12-bore hammer gun x1.0; both hammers are the `hammer` node; a gold rubber duck on the lock plate |
| `make_minigun_gatling.py` | `w_minigun_gatling.glb` | 1874 Camel-pattern Gatling x1.0: the crank is on the barrel axis, inside the `barrels` node (TURN CRANK FASTER) |
| `make_sniper_musket.py` | `w_sniper_musket.glb` | Brown Bess x1.38 with a 15in bayonet; a brass pirate spyglass lashed on is the scope |
| `make_sniper_golden.py` | `w_sniper_golden.glb` | the round-1 AWM re-dressed: gold scrollwork, rubies, a crown turret, a PRICELESS tag; `noWrap`, `glint` spots, `bolt` |
| `make_chicken_turkey.py` | `w_chicken_turkey.glb`, `pj_chicken_turkey.glb` | RPG-style tube with a roast turkey on the muzzle (HEAT 350F); the thrown turkey x3.3 |
| `make_bowling_cannon.py` | `w_bowling_cannon.glb` | bronze hand mortar with verdigris, slow-match fuse, bowling-pin lifting handles; `ads` pose |
| `make_banana_bunch.py` | `w_banana_bunch.glb` | the Peel Shooter's AKS-74U in AK-74 plum, the mag is a whole hand of bananas (PRODUCE OF JANK) |

## Rules that make a model drop straight in
- **Build in game space**: three.js axes and metres (x right, y up, -z forward); `lib.gv()` converts to Blender. A
  weapon keeps the code model's muzzle point and grip/hand area (`public/js/models.js` `WB`), so the viewmodel pose, ADS,
  muzzle flash, tracers, twirl pivot and recoil all still fit. Real guns: take real millimetres and pick one scale factor
  that lands the muzzle on the code model's (each script says which).
- **Metadata** goes on the root empty as `jf` (exported as glTF extras, read by `public/js/glbkit.js`):
  `muzzle`, `sight` `{ y, z }` (the line of sight; the game puts your eye 0.17 m / scale behind `z`, so push `z` back or
  forward to set the eye distance), `hatAt` `[[x, y, z], height]`, moving parts (`pump`, `cylinder`, `hammer`, `bolt`), the code models' hooks
  (`needle`, `vents`, `barrels`, `tip` = the cigarette ember weapons.js swells, `fan` = the card nodes it deals your hand
  onto, `hand`, `blade`, `card`), `bow` (the string rig: the halves stay on the limb tips and bend to the arrow's nock as
  you draw, the limbs flex), `glint` (spots for the Golden Sniper's star glint), `noWrap` (a trophy no wrap paints), `port`
  (where the shells fly out, if not the default spot) and `paint` (materials the flat look recolours). `id` is the base weapon, `skin` the skin it is.
- **File names**: a weapon is `w_<id>.glb`, a skin `w_<skin id>.glb` (e.g. `w_ar_toy.glb`), a thrown thing `pj_<kind>.glb`
  (centred, nose to -z) and a skin's thrown one `pj_<skin id>.glb` (a thrown croc is a croc). Anything missing = the code
  model, as before.
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

## Kit gotchas (found the hard way)
- Raw bmesh UVs: name the layer (`bm.loops.layers.uv.new('UVMap')`). Unnamed it's "Float2", and after a join the
  exported UVs are all zeros (white textures).
- `uv_planar` right after making an object reads a stale `matrix_world`: call `bpy.context.view_layer.update()` first.
- `lathe()` caps both ends by default, so a thin ring becomes a solid disc (a lens cover): pass `cap=False` for bands.
- Boolean cuts can leave the new faces on an empty material slot (grey in the sheet): the round-2 gun scripts have a
  small `fixmats()` that hands them the object's own material.
- Metaballs: positions go through `gv()`, radii are metres too (millimetres made a 70 m blob that hung Blender).
- One Blender session = unique object names: in a multi-file script give each model's hook nodes their own names and
  put the exact name in its meta.

## How the game uses them
- `public/js/glbkit.js`: `prepAuthored` takes any glb with `jf` metadata: nearest-filtered textures, the Potato vertex
  snap (`jankify`), a small studio env map for gloss, glows kept through skins. `authored(id)` gives a shared copy.
- Weapons: `buildWeapon` (models.js) swaps in `w_<id>` (or `w_<skin>` for a skin model) as built (no fitting) and reads
  muzzle/sight/hat/hooks from it. A missing or broken file = the code model, as before. Finishes, wraps, hats and
  effects work on top. Thrown things: `buildProjectile` takes `pj_<skin>` / `pj_<kind>`, `buildPeel` takes `pj_peel`.
- Knives and katanas (`public/js/blades/`) stay code-built: they are real-reference models already. `glossBlade` gives
  them the Blender set's studio gloss (steel and brass turn metal, wood varnished, grips satin) whenever the Blender
  models are loaded.
- Props: a map's boxes carry `{ pv: id }`; while `p_<id>` is loaded `world.js` skips drawing those boxes and `props.js`
  draws the model at the spot `L.P()` recorded. Collisions never change. In a map builder:
  ```js
  prop(L, 'forklift', x, z, r)                  // catalog boxes (shared/props.js) + the model
  const pv = L.P('bus', x, z, r); L(..., 'caryellow', pv)   // your own boxes, drawn only when the model is missing
  ```
  `r` = quarter turns (like `B.local`), opts `{ v: variant, color: 'carblue', s: scale, y }`.
