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
node tools/blender/shots_r3.cjs 3100 <outDir> camera,frame,calc,nvg,wand,wreck,rig,arms,missile 3,0
                                     # the gear, wrecking ball and Overdrive Rig: OLD | BLENDER | IN USE strips in the game's lights
node tools/blender/rig_game.cjs 3100 <outDir> both 3 --video         # the Overdrive Rig in Training: first person (the real
                                     # killstreak) + third person (the pose code on the range), screenshots or a clip each
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
| `make_rack.py` | `p_rack.glb` | pallet rack: nodes `bay` (6 m) and `frame` |
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
| `make_pistol_calc.py` | `w_pistol_calc.glb` | Calculator: 80s desk calculator on Plan B's grip, LCD reads 58008; `slide_wzB` = the top shell (child `slide_keys_wzN` keeps keys + LCD unwrapped), `mag_wzB` = a 2xAA sled, `hammer_wzN` = the AC key lever |
| `make_akimbo_walkie.py` | `w_akimbo_walkie.glb` | Walkie Talkies: upright radio as the grip, rubber duck antenna off the front jack = barrel; `cocker_wzN` (channel knob), `mag_wzB` (battery pack), `tagL_wzN` / `tagR_wzN` |
| `make_sawnoff_pepper.py` | `w_sawnoff_pepper.glb` | Pepper Mills: two walnut restaurant mills banded together as barrels; `hinge_wzB` (+ `hinge_trim_wzN`), `forend_wzA`, `shell1/2_wzN` = giant peppercorns, `hammerR/L_wzN` = finial knobs |
| `make_cards_business.py` | `w_cards_business.glb` | Business Cards: portrait ☺ CORP cards fanned out of a chrome case; `fan` card0..4 = inset faces the game deals onto |
| `make_water_skins.py` | `w_water_flower.glb`, `w_water_hose.glb` | Squirt Flower (daisy muzzle, stem barrel, clear bulb tank) and Hose Nozzle (8-pattern dial, NOT SOAP jar tank, lever = pump); `water_*_wzN` + `pump_*_wzB`; `--only=flower/hose` |
| `make_taser_zapper.py` | `w_taser_zapper.glb` | Bug Zapper: fly-swatter racket bent into a pistol grip, head flat at muzzle height; `led_wzN` |
| `make_remote_pad.py` | `w_remote_pad.glb` | Game Pad: original wired pad held by its right handle, II / << face keys; `ir_wzN` = the cut cable's frayed end (the muzzle) |
| `make_revolver_drill.py` | `w_revolver_drill.glb` | Cordless Drill: pink drill/driver, bubble-level sight; `cylinder_wzB` = chuck + gold bit, `hammer_wzN` = gear selector |
| `make_laser_cattoy.py` | `w_laser_cattoy.glb` | Cat Laser: giant felt toy mouse, laser in its nose, swiss cheese grip; `meta.laser` hooks (lz_led0..4, lz_emit, lz_button, lz_tail = the swinging charm), bound by `public/js/laserglb.js` (any Blender laser, the base one too) |
| `sidekit.py` | (helpers) | keys, top-down plates, decal quads, curved label patches, ring UVs, 7-segment LCD painter, the ☺ CORP smiley |
| `make_ar_keytar.py` | `w_ar_keytar.glb` | 80s keytar x1.0 as a carbine: two octaves of keys on the top deck (you aim over them), glowing ribbon neck, headstock front sight, jack-plug muzzle, ROM cartridge `mag`, octave-slider `charge`, coiled patch cable (☺ CORP SYNTH-47, LEGALLY A GUN) |
| `make_smg_label.py` | `w_smg_label.glb` | office label printer x2.5 as the SMG: keypad, flush LCD (DEAD x3 COPIES), tape-cassette `mag`, tape-feed `charge`, APPROVED stamp butt, labels on everything, a PROPERTY OF ☺ CORP strip out of the muzzle |
| `make_shotgun_umbrella.py` | `w_shotgun_umbrella.glb` | gent's stick umbrella x1.15: brass ferrule muzzle, furled canopy (☺ print), the runner is `pump_wzB`, crook bent into the grip (its hook = trigger guard), IT NEVER RAINS INDOORS tag |
| `make_sniper_cue.py` | `w_sniper_cue.glb` | 58in pool cue x1.4: chalked tip muzzle, ebony points (☺ CORP BILLIARDS), brass action, 8-ball knob on `bolt_wzB`, three-ball mag, felt scope between chalk cubes (NO JUMP SHOTS) |
| `make_burst_ticket.py` | `w_burst_ticket.glb` | deli TAKE A NUMBER dispenser as the Hat Trick bullpup: queue-stanchion barrel, NOW SERVING 03 carry handle (sight tunnel through it), ticket-roll `mag`, yellow PULL `charge` (PLEASE WAIT) |
| `make_lmg_leaf.py` | `w_lmg_leaf.glb` | blower-vac-mulcher as the Belt Sander: vacuum tube barrel with slots showing `lmg_heat`, yellow blade lid = `cover`, leaf-bag `mag` (100% ORGANIC AMMO), `belt_00`..`belt_11` are autumn leaves (LEAF IT TO US) |
| `make_dmr_pen.py` | `w_dmr_pen.glb` | boardroom fountain pen: nib muzzle, resin barrel with ink window, marble desk-set grip, ink-cartridge `mag`, pen-clip `charge`, magnifier + loupe scope, SIGN HERE flags |
| `make_lever_capgun.py` | `w_lever_capgun.glb` | 60s toy cap rifle on the Yeehaw's layout: orange-plug barrel, scrollwork receiver with the cap door open on a red roll, fake-wood stock with a horse-head medallion, yellow loop `lever`, big-spur `lhammer` (BANG!) |
| `make_autoshot_trimmer.py` | `w_autoshot_trimmer.glb` | petrol string trimmer as the Lawn Mower: bump head muzzle, debris guard, 2-stroke engine, see-through fuel-tank `mag` (MIX 50:1), pull-start `charge` (TRIM RESPONSIBLY) |
| `corp.py` | (helpers) | the gun skins' kit: scale helper, `moving()`, `fixmats`, ☺ smiley + sticker painting, decal UVs, `uv_tube` |
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
| `make_laser.py` | `w_laser.glb` | Big Laser Pointer: an office laser pointer pen x4.7 (leg-sized) with a lime toy-pistol grip duct-taped under it, D-cells, a PEW-O-METER LED bar and a cat charm; `meta.laser` hooks, bound by `public/js/laserglb.js` like the Cat Laser's: `lz_button_wzN` (pressed), `lz_led0_wzN`..`lz_led4_wzN` (lit with the charge), `lz_emit_wzN`, `lz_charm_wzN` (swings); the charge orb is the game's |
| `make_gear.py` | `x_camera.glb`, `x_photoframe.glb`, `x_calc.glb`, `x_nvg.glb` | the gear (`x_` = not a weapon, loaded only when someone carries it): instant camera at real size (`flash`, `shutter`, `print` > `pic`, the photo the game paints), the photo portal (a 2.1 m print on an easel back, the live picture fills its opening), the Pop Quiz calculator (`screen` shows the sum), flip-up night vision goggles (`pivot` at the forehead knuckle, `lensL` / `lensR` / `ir` glow, `strap` only on other people's heads); `-- --only=camera,frame,calc,nvg` |
| `make_icons.py` | `x_moonboots.glb`, `x_spinbot.glb`, `x_satellite.glb`, `x_medkit.glb`, `x_bubble.glb`, `x_target.glb`, `x_blackhole.glb` | icon props for the killstreaks and items that had no model (moon boots, spinbot shades in gyro rings, spy satellite, medkit, shield bubble, Chicken Strike's target, Giant Duck's black hole). Only `public/js/itemicons.js` uses them: rendered once each in the icon studio (`icons.js studioIcon`) for the loadout, the HUD and the buy menu. Lazy `x_` files, 30-80 KB (12-24 KB gzipped) |
| `make_rig.py` | `x_rig.glb`, `x_rigarms.glb`, `pj_rigmissile.glb` | the Overdrive Rig, jointed exactly like the code rig (`public/js/rigmodel.js`): one empty per joint (names, parents and rest spots in the `joints` meta, so the leg IK and every pose still fit), each joint's plates as one mesh per material in its space; `rg_*` materials are the game's (`rg_accent` = your colour, visor, core, glows, the hack deck's `rg_screen`), `*_sm` parts stay out of the outline / shield / afterimage; pistons, hoses, glows and flames stay code and have mounts. Excavator-breaker forearms, forklift-mast spine, ammo-crate missile pods, chrome stacks, BONK / HUGS knuckles, a bobblehead on the dash. The first-person forearms (`armR` > `fistR`, `armL` > `fistL`) and the missile (RETURN TO SENDER). `-- --only=rig,arms,missile`, `--qa` (per joint), `--stats` |
| `make_trees.py` | `p_lollipop`, `p_conifer`, `p_pine`, `p_birch`, `p_deadtree`, `p_palm`, `p_saguaro`, `p_fern`, `p_bush` | round 4, the maps' trees and plants: built on each kit function's layout (trunk on the origin), `meta.box` = the box version's extent, a hand-made far silhouette under `lod1`, crowns in `tint` where the map colours them |
| `make_street.py` | `p_streetlight` (replaces round 1's `make_streetlight.py`), `p_acunit`, `p_watertower`, `p_billboard` (+ `p_billboard_post`), `p_barrier`, `p_cone`, `p_vending`, `p_generator` | round 4, the street: cobra-head lights (the lamp is `glow`), rooftop condensers, a water tower, billboard faces (the ad stays the map's picture) and posts (so every board size fits), jersey blocks, cones, vending machines (cabinet `tint` = its panel colour), a light tower |
| `make_yard.py` | `p_container`, `p_crate`, `p_barrel`, `p_pallet`, `p_cardboard`, `p_pallet_load` (these two replace round 1's `make_pallet.py`), `p_trailer`, `p_excavator` | round 4, the yard: found on every map by box material + size (each box one copy, any size), paint in `tint` (container / barrel colours) |
| `make_market.py` | `p_stall`, `p_tent`, `p_pot`, `p_camel`, `p_hay`, `p_wagon`, `p_wagon_open`, `p_grave`, `p_grave_cross`, `p_dyevat`, `p_handcart` | round 4, the market and the desert: awnings, tent cloth, camel blankets, cart loads and dye in `tint`; the stall's rug stays a map box |
| `make_traffic.py` | `p_car_hatch`, `p_car_sedan`, `p_car_taxi`, `p_car_pickup`, `p_car_van`, `p_car_icecream`, `p_car_bus`, `p_car_truck` | round 4, the traffic (`cars.js`, facing +z, real size): `body` (paint = `tint`, fixed liveries on taxi / ice cream / bus), `lamps` / `tails` / `inds`, `wheel_fl/fr/rl/rr` on their hubs, a 300-triangle `lod1`; the sedan, hatch and taxi also stand in for the parked cars |
| `make_vehicles.py` | `p_transitbus`, `p_boxtruck`, `p_semi`, `p_semitrailer` | round 4, the last box-built vehicles: Suburb's walk-in shuttle bus (seats, poles and a dash inside, windows long gone), the parked box truck (roller door up, a plank load floor you can walk on), the Warehouse semi and its trailer on its own (Warehouse S&D). Every copy has the same boxes, so each file is drawn as built (scale 1, the kit function's anchor) |
| `farlod.py`, `lod_splice.py` | far LODs for `p_forklift`, `p_bus`, `p_numball` | round 1's props get a `lod1` (a few hundred tris, the same paints): `make_forklift.py` / `make_bus.py` / `make_numballs.py` build it, `lod_splice.py` adds it to the shipped file and keeps every byte of the close-up (`python3 tools/blender/lod_splice.py <old.glb> <new.glb> <out.glb>`, no Blender needed) |
| `zmkit.py` | (helpers) | the zombies props' kit: outline slabs, a ray cast onto a surface (nails and screws sat on the real face), straight-on UVs + a fix for collapsed ones, `glow_mat` (base and glow are separate textures, so with the glow turned down it's dead glass), polygon / star / comic-text painters, board `grain`, a boolean that hands the cut faces the cutter's material, planar tubes with mitred bends (neon, rims), rounded rects, a dentable `grid_plate`, the `qa` gate |
| `make_zmboard.py` | `x_zmboard.glb` | Dead Mall window barricade (zombies), in the window's own space: x -1..1 across the 2 m opening, y up from the floor (sill 0.9, top 2.9), z 0 = the wall's inner face, +z = the room. `frame` (origin 0,0,0): two 2x4 battens at x +-1.05 (y 0.85..2.95), wall nails, the snapped-off stub of an old board, duct tape, a torn STAY OUT strip. `plank_0`..`plank_5` bottom to top, each its own node with its origin at its own centre and its rest tilt baked into the mesh (the node is unrotated): a weathered grey board with a bite out of it, a shopping cart's side grille (red handle, coin lock), a cedar board sprayed NO BRAINS HERE, the snapped-off end of an EVERYTHING MUST GO sign (die-cut 70% OFF burst, its dead tube poking out), a kiddie racer's panel (07, KEEP HANDS INSIDE), a crate slat nailed up upside down (THIS SIDE UP). 0/2/4 lie on the battens, 1/3/5 over them on spacer blocks (part of the plank), nails at both ends. meta `planks`, `opening`, `plankAt` [[x, y, z, tilt]]. `-- --qa` |
| `make_zmmachine.py` | `x_zmmachine.glb` | the Cheat Machine (zombies): a slot / vending cabinet, 1.1 x 0.82 x 2.22 m, feet at y 0, front +z. CHEAT in real pink neon tube on stand-offs, MACHINE backlit, neon dice, fat dice and the beacon on top; a 0.78 x 0.52 screen recess with black glass (meta `screen` {c = the glass's centre, w, h} = where the game puts its canvas, facing +z), 14 chase bulbs; DON'T button (a PRESS sticker points at it), coin door + INSERT CASH, tickets, a tongue out of the prize bay, dented kick plate, side art (a giant 7, dice, numbers), glowing edge strips, a crooked dented service panel with wires out of it and a loop of meat out of the cabinet on the left, DO NOT TIP (IT TIPS BACK) on the back. Nodes: `lever` (origin = its pivot, modelled up, turns about local x, + = forward pull; meta `lever` {pivot, axis, pull}), `lamp_wzN` (the beacon dome, origin at its centre, `zm_lamp`). `zm_neon` = everything the machine's power lights (neon, bulbs, coin entry, edge strips); its glow is its own texture, so turned down it's unlit glass. `-- --qa` |

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
- A plane the game paints with its own canvas texture (the camera's `pic`, the calculator's `screen`, the rig's
  `rg_screen`): the glTF exporter writes v as 1 - v and the game's canvas textures are flipY, so author that plane's V
  flipped (v = 1 on the bottom edge) or the game's picture shows upside down.

## How the game uses them
- `public/js/glbkit.js`: `prepAuthored` takes any glb with `jf` metadata: nearest-filtered textures, the Potato vertex
  snap (`jankify`), a small studio env map for gloss, glows kept through skins. `authored(id)` gives a shared copy.
- Weapons: `buildWeapon` (models.js) swaps in `w_<id>` (or `w_<skin>` for a skin model) as built (no fitting) and reads
  muzzle/sight/hat/hooks from it. A missing or broken file = the code model, as before. Finishes, wraps, hats and
  effects work on top. Thrown things: `buildProjectile` takes `pj_<skin>` / `pj_<kind>`, `buildPeel` takes `pj_peel`.
- Loaded late: weapon skins, the gear, the wrecking ball and the Overdrive Rig (`x_*`, `pj_rigmissile`) download only
  when they're in your loadout (`prefetchLoadout`) or someone near you uses one: `authored(id)` starts the download, the
  code model stands in until it lands, and `whenLate(id, fn)` lets a module rebuild then. Side renderers (icons, the
  locker preview, tests) draw through `withEnv(renderer, root, draw)` so chrome keeps its reflections there.
- Gear hooks (`gearmodels.js`): the game swaps "own" node materials for its live ones (`ownMat`: the camera's `pic`,
  the calculator's `screen`, the goggles' lenses) and moves the hook nodes (shutter, print, pivot). The laser's are in
  its `meta.laser` (`laserglb.js`).
- The Overdrive Rig: `rigmodel.js` finds each joint of `x_rig` by name, merges its meshes per material, swaps `rg_*`
  for the game's materials (your colour, glows, the hack screen) and keeps its own pistons, hoses, glows and flames;
  `rigarms.js` does the same with `x_rigarms` for first person, and the missiles use `pj_rigmissile`.
- Knives and katanas (`public/js/blades/`) stay code-built: they are real-reference models already. `glossBlade` gives
  them the Blender set's studio gloss (steel and brass turn metal, wood varnished, grips satin) whenever the Blender
  models are loaded.
- World props (round 4, `p_<id>.glb`): the map kit functions in `shared/map.js` / `shared/jankburg.js` wrap their boxes
  in `propOf()` (`shared/propcap.js`): the boxes get `{ pv: id }` and one placement goes in the builder's `props` list
  (anchor, turn, the boxes' extent, a tint = a map material). Crates, barrels, pallets, cardboard, containers and jersey
  blocks are spotted by material and size wherever a map adds them. Collisions, nav, spawns never change (every map's
  boxes hash the same as without it). `public/js/propfield.js` draws them: one InstancedMesh per prop, material and LOD
  for the whole map (plain materials that shine alike are merged first), each copy fitted onto its boxes (`meta.box`, or
  the one size every copy has, or the model's bounding box), `tint` = the copy's map colour, near copies = lod0 + shadows,
  far = the `lod1` node, out of view / past the fog = not drawn. A map's prop files download when it loads (they're lazy
  like skins), the map is built without the boxes of props on their way, and a file that never comes gets its boxes
  back. Traffic: `cars.js` builds a car from `p_car_<type>` (`wheel_*` hubs, `lamps` / `tails` / `inds`, `tint` paint)
  when it's loaded; parked cars use the same models.
  ```js
  propOf('stall', L.pt(x, 0, z), L.yaw, () => { /* the kit's own boxes */ }, { t: awning, keep: (b) => b.rug })
  ```
  Check them in the game: `node tools/blender/shots_r4.cjs <port> <dir> <ids|map> [maps] [presets] [n]` (box version vs
  Blender, same camera), `node tools/blender/shots_traffic.cjs <port> <dir>` (every traffic car, code vs Blender),
  `node tools/blender/props_r4.mjs [--md]` (copies per map, tris and materials per model),
  `node tools/blender/perf_props.cjs <port> <out.json> [maps]` (draw calls + triangles).
- Round 1's props (forklift, bus, number balls, racks, pallet loads) still use `prop(L, id, x, z, r)` / `L.P()`
  (shared/props.js: catalog boxes + a placement at a spot with quarter turns); they draw through the same instancing.
