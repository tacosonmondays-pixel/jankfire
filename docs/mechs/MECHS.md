# Mechs: the rig the game loads (names for the Gameplay session)

**Status:** the game files carry the owner's Tripo bodies as they are (their own heads, V horns and faces: the owner's
call, `docs/mechs/RESEARCH.md`), cut onto the rig and painted by `tools/blender/mechs/tripo_swap.py`.
- From the concept: PAPER PLANE's pods, highlighter cannons, wings and crane; NIGHT SHIFT's hands, sword and shield.
- PAPER PLANE's body is try A until the owner picks A or B.
- Every name below is the same as on the concept meshes.
- Pictures: `docs/mechs/tripo/compare/` and `docs/mechs/tripo/ingame/`. Concept notes: `docs/mechs/CONCEPT.md`; research:
  `docs/mechs/RESEARCH.md`.

## Files
| file | what |
|---|---|
| `public/models/x_mech_paperplane.glb` | PAPER PLANE: joints, meshes, markers, 20 clips (~1.5 MB, 21k tris) |
| `public/models/x_mech_nightshift.glb` | NIGHT SHIFT: joints, meshes, markers, 19 clips (~1.1 MB, 18k tris) |

- The `x_` prefix means they're lazy: load them only when a mech is in play.
- Each file is ONE model per mech (after the Tripo swap too: wings, drone, sword and shield are inside it).
- Rebuild (Tripo bodies, what ships): `blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=<name> qa`
  (`body=paperplane_body_b` for PAPER PLANE's other body).
- Back to the concept meshes: `blender52 -b -P tools/blender/mechs/make_mechs_rig.py -- [mech=<name>] [qa]` (same
  names, clips and markers).
- No far-LOD copies are in the files (MECH DROP draws every mesh); `tripo_swap.py ... lod_tris=7000` adds
  `<joint>_lod1` siblings if the game ever wants them.
- Check: `node tools/blender/mechs/clip_sheets.cjs [outDir] [mech] [rowsPerSheet]` plays every clip in three.js and
  writes contact sheets (`docs/mechs/clips/*.jpg`). It exits 1 if a clip is missing or the page errors.

## Space and rig
- **Space:** game axes. The mech faces **-z**, its right is **+x**, feet sit on y = 0, and the root is on the ground
  between the feet. To face it along the player's yaw, turn its holder by the yaw (a yaw of 0 already faces -z).
- **The rig:** no SkinnedMesh. Every joint is a named node with its rigid mesh child `<joint>_mesh`. Clips animate the
  nodes' quaternions, the hips' position, and a few parts' positions (destroy, drone).
- **No root motion:** `root` never moves in any clip. The game moves and turns the root. The hips bob and drop (kneels,
  landings), and every grounded key is solved so the feet sit on y = 0.
- **The root node's `userData.jf` meta** lists:
  - `joints` (name, rest position, parent)
  - `clips` (name, dur, loop, hold, partial, note)
  - `marks` (name, joint, rest position, direction)
  - `palettes` (colour options A / B)
  - `fps` (30)
  - PAPER PLANE also has `drone_axis`.

## Joints
- Both: `root` > `hips` > `waist` > `chest` > `neck` > `head`.
- Both: `chest` > `hatch` (cockpit: PAPER PLANE's nose lifts, NIGHT SHIFT's breastplate drops), `backpack`.
- Both: `chest` > `shoulder_L|R` > `upperarm_L|R` > `forearm_L|R` > `hand_L|R`.
- Both: `hips` > `thigh_L|R` > `shin_L|R` > `foot_L|R` > `toe_L|R`.
- Both: `hips` > `skirt_L|R`.
- PAPER PLANE also has:
  - `shoulder_L|R` > `pod_L|R` (2 x 3 pencils each).
  - `forearm_L|R` > `cannon_L|R`: the twin highlighter cannons under each forearm (never animated).
  - `backpack` > `wing_L|R` (rest = the stowed V; jet mode swings them flat).
  - `wing_L` > `drone` > `drone_wing_L|R` (the origami crane). To send it out, play `drone_launch`, then reparent `drone`
    to the scene and fly it with `drone_flap` playing. To bring it back, reparent it to `wing_L` and play
    `drone_return`.
- NIGHT SHIFT also has:
  - `head` > `beacon`: spin it about y in code, forever. On the Tripo body it carries no mesh (its forehead lamp glows instead); `mk_beacon` stays.
  - `hand_R` > `sword`.
  - `forearm_L` > `shield`.

## Markers (empty nodes; positions and directions are also in the meta)
- PAPER PLANE:
  - `mk_missile_L0..5` and `mk_missile_R0..5`: pencil tips (0..2 top row, 3..5 bottom row), pointing -z on the pods.
  - `mk_thrust_back_L|R` and `mk_thrust_heel_L|R`: nozzle exits.
  - `mk_drone`: the crane's beak.
  - `mk_muzzle_L|R` (on `forearm_L|R`): just past the highlighter tips, pointing -z.
  - `mk_seat`, `mk_eject`.
- NIGHT SHIFT:
  - `mk_sword_base`, `mk_sword_tip`: the blade, for the trail and hit line.
  - `mk_shield_face`.
  - `mk_beacon`.
  - `mk_thrust_back_L|R` and `mk_thrust_calf_L0|L1|R0|R1`.
  - `mk_seat`, `mk_eject`.
- Both: `mk_mark` (on `head`): half a metre over the top of the head (the OVERTIME badge).

## Materials
- `pp_paint` / `ns_paint`: the team / player colour. Tint it; colour A is the default.
- `*_white`, `*_dark`, `*_accent`, `*_frame` (metal), `*_chrome`, `*_glass`.
- `*_glow`: the visor slats or bar and the sword edges. Emissive.
- `*_thrust`: the thruster throats. Emissive; scale it with boost.
- Decals have their own materials, e.g. `ns_ledmat` is the PLEASE HOLD screen.
- **Painted metal** (`tools/blender/mechs/metalkit.py`, the owner: "they look like plastic toys"):
  - paint is metallic car paint with a clear coat; white is pearl; `frame` is brushed gunmetal (anisotropic);
    `accent` is polished gold.
  - All of them share one small tiling detail set (panel lines, rivets, scratches, chips, grime in the seams;
    `mech_detail_*`) on box UVs, 2 m per tile.
  - `COLOR_0` holds baked shading: ambient occlusion and lighter worn edges.
  - No extra materials or draw calls. Paint materials carry `extras.jf_look = 'painted metal'`.
- **Tinting:** a model whose paint has `jf_look` keeps its own paint material (maps, clear coat). MECH DROP clones it
  per mech and sets the colour (`public/js/mechmodel.js`), instead of swapping in the glossy stand-in paint.
- PAPER PLANE's wings and crane stay paper: `*_paper` copies of the role materials, without the metal look.
- **Draw calls** (the coordinator, 2026-11-13: a hero draws in 15-30 calls; each material on a joint's mesh is one):
  the Battle Island heroes merge every flat painted role but the team paint into one `<prefix>_trim` material
  (`metalkit.merge_trim`, on by default in `make_hero.py`; `no-merge` turns it off). Its colour per part is in
  `COLOR_0` (times the AO bake); its metal / roughness / clear coat come from a 64 px role atlas
  (`tools/blender/mechs/tex/<prefix>_trim.png`: R clear coat, G roughness, B metal) read through `TEXCOORD_1`.
  `extras.jf_trim` lists the roles in it. The team paint, the glows and the decals stay their own materials.
  Measure a hero in a real game: `node tools/blender/mechs/draws_game.cjs <port> <outDir> <frame> [preset] [map]`.

## Clips (all 30 fps; three.js AnimationMixer by name)
- "hold last frame": play it LoopOnce with `clampWhenFinished = true`.
- "partial": the clip keys only the joints it names, so play it on top of a body clip.
- Durations are in seconds.

| mech | clip | dur | play | note |
|---|---|---|---|---|
| paperplane | `idle` | 2.40 | loop | breathing (spin NIGHT SHIFT's beacon in code: it turns about y forever) |
| paperplane | `walk` | 1.00 | loop | in place, 2 steps |
| paperplane | `run` | 0.66 | loop | in place, leaning in |
| paperplane | `boost_dash` | 0.75 | once | a burst forward: crouch, launch lean with arms back, recover (the game moves it) |
| paperplane | `jump` | 0.60 | hold last frame | crouch, spring, tuck (last frame held while airborne) |
| paperplane | `land` | 0.60 | once | impact squash, overshoot, settle |
| paperplane | `hover` | 1.60 | loop | thrusters holding it up: legs hang, slow bob |
| paperplane | `hit_react` | 0.50 | once | snaps back and twists, recovers with overshoot |
| paperplane | `drop_in` | 1.30 | hold last frame | impact at 0.36 s (x time stretch); ends in a held low hero pose: spawn the dust ring at the impact |
| paperplane | `pilot_in` | 2.60 | once | kneels, hatch opens (pilot climbs in 1.0 to 1.6 s), hatch shuts, stands |
| paperplane | `eject` | 0.70 | hold last frame | the hatch blows open (the pilot launches at 0.08 s); held open |
| paperplane | `destroy` | 1.60 | hold last frame | hit, the hatch pops (eject), armour flies off, slumps to one knee; held. hide/replace parts as the game likes |
| paperplane | `jet_in` | 0.80 | hold last frame | folds into the paper plane: wings swing down flat, legs together |
| paperplane | `jet_fly` | 1.20 | loop | a gentle bank |
| paperplane | `jet_out` | 0.80 | hold last frame | unfolds into a hover |
| paperplane | `missile_salvo` | 1.20 | once | pods flip up 45 deg, three kicks (fire 2 pencils a side on each: 0.30, 0.52, 0.74 s), back down |
| paperplane | `lunge` | 0.60 | once | dash-and-strike at a target (heals on hit) |
| paperplane | `drone_launch` | 0.60 | hold last frame, partial | the crane lifts off its dock on the left wing (1.7 m up and out by 0.6 s); then detach it and fly it (play drone_flap on it) |
| paperplane | `drone_return` | 0.60 | once, partial | back onto its dock (reattach it first) |
| paperplane | `drone_flap` | 0.36 | loop, partial | the crane's wings (only its wing joints: plays on top of anything) |
| nightshift | `idle` | 3.00 | loop | breathing (spin NIGHT SHIFT's beacon in code: it turns about y forever) |
| nightshift | `walk` | 1.25 | loop | in place, 2 steps |
| nightshift | `run` | 0.83 | loop | in place, leaning in |
| nightshift | `boost_dash` | 0.94 | once | a burst forward: crouch, launch lean with arms back, recover (the game moves it) |
| nightshift | `jump` | 0.75 | hold last frame | crouch, spring, tuck (last frame held while airborne) |
| nightshift | `land` | 0.75 | once | impact squash, overshoot, settle |
| nightshift | `hover` | 2.00 | loop | thrusters holding it up: legs hang, slow bob |
| nightshift | `hit_react` | 0.62 | once | snaps back and twists, recovers with overshoot |
| nightshift | `drop_in` | 1.62 | hold last frame | impact at 0.36 s (x time stretch); ends in a held low hero pose: spawn the dust ring at the impact |
| nightshift | `pilot_in` | 3.25 | once | kneels, hatch opens (pilot climbs in 1.0 to 1.6 s), hatch shuts, stands |
| nightshift | `eject` | 0.88 | hold last frame | the hatch blows open (the pilot launches at 0.08 s); held open |
| nightshift | `destroy` | 2.00 | hold last frame | hit, the hatch pops (eject), armour flies off, slumps to one knee; held. hide/replace parts as the game likes |
| nightshift | `sword_combo_1` | 0.65 | once | flat cut right to left (hit at 0.24 s): stamps an OVERTIME mark |
| nightshift | `sword_combo_2` | 0.60 | once | backhand left to right (hit at 0.22 s) |
| nightshift | `sword_combo_3` | 0.95 | once | overhead chop (hit at 0.42 s): the 4th mark clocks them out |
| nightshift | `triple_shift` | 1.30 | once | three dashing slashes (hits at 0.20, 0.44, 0.68 s); the game dashes the root |
| nightshift | `shield_block` | 0.40 | hold last frame | shield up in front, braced (held) |
| nightshift | `shield_bash` | 0.55 | once | shoves the shield forward (hit at 0.22 s) |
| nightshift | `ground_slam` | 1.50 | once | big overhead slam (impact at 0.56 s: shockwave + dust ring), a held beat, recover |
| both | `drop_fall` | 0.50 / 0.62 | loop | the MECH DROP fall until it lands (knees up, arms up, a flutter) |
| both | `hero_intro` | 1.75 / 2.12 | hold last frame | the MECH DROP landing, starting AT the impact: superhero landing (knee and fist down), a beat looking up, a gather, then the signature pose, held. PAPER PLANE: wings out, pods up, hand on hip, cannon low. NIGHT SHIFT: sword overhead, then driven into the floor |

- **Weight:** the hits snap in (a cubic ease-in into the impact key: the wind-up hangs, the hit lands, then it eases
  out into the follow-through). Every other key keeps Blender's smooth in / out.
- **Events:** `meta.clips[].events` = `[{ t, fx, at, shake?, ground? }]`: at `t` s into the clip, play `fx` at the node
  `at` (a joint or a marker; `ground` = on the floor under it) and shake the camera by `shake` (0..1) if it is near.
  `fx`: `dust`, `step`, `slam`, `spark`, `glint`, `burst`, `vent`, `flare`, `pop`. The hero kit plays them.

## Hero kit (`public/js/mechlook.js`; the owner: "higher quality than the base game, same with the mechs")
For any mech glb that comes through `buildMech` (no frame names in it, so new heroes get it free):
- **Rim light:** a hard fresnel edge (white, a hint of the mech's colour) added to the emissive of every lit material,
  on top of the game's vertex snap. Weaker on Potato.
- **Ink:** one smooth outline hull per joint (inverted hull, thicker far away), built once per model and shared.
  Off on Potato. About 20 extra draw calls per mech.
- **Glows:** the emissive materials (eyes, visors, nozzles, the PLEASE HOLD screen) burn hotter with the thrust and
  flare on a `flare` event; NIGHT SHIFT's blade (`*_blade`) heats up mid-swing. They bloom where bloom is on.
- **Thrusters:** a contrail (a camera-facing ribbon) behind each `mk_thrust_*` while it burns and moves, and a heat
  shimmer behind each flame.
- **Events:** the clip events above; `mechLook.onEvent = (inst, ev, pos) => {}` is the hook for sounds.
- **Stickers and spray slots** (`tools/blender/mechs/herokit.py`, baked in the file): a unit number (`07`, `24/7`),
  NO STEP, CAUTION HOT, JANK COLA, POWERED BY BREAD, WASH ME, HOW IS MY PILOTING?, a serial, on the biggest flat plates
  facing the right way (one shared atlas, `*_decalmat`). Two spray / skin slots, picked first so stickers keep off
  them: `meta.decal_slots` `[{ name: 'spray_0', joint, at, dir, up, size }]` (rest pose, game space) plus an
  `mk_spray_<n>` marker each. `sprayOnMech(inst, slot, texture)` projects a texture there; it rides the joint.
- **Far LOD and detail** (2026-11-12, "can the mechs be larger and more detailed?"): a hero file holds its near model
  (`<joint>_mesh`, about 60-80k tris: bolts, rams, vents, hinges, hoses, layered skins over the chassis, a 2K normal
  map with panel lines and rivets) and a far one (`<joint>_lod1`, 15k or less: half the segments, chamfers for bevels,
  no `dt()` detail parts), both made in one run (`make_mechs_rig.build_lod`, `tools/blender/mechs/detailkit.py`).
  glbkit hides the far one; `lookTick` swaps the two when the camera passes `meta.lod.dist`
  metres: 26 m on Mid, x0.6 Potato, x0.8 Crusty, x1.4 Too HD. `inst.look.lodForce = true / false` holds one. The ink
  hulls come from the far LOD for both (bolts and hoses need no outline; it keeps the ink cheap up close).
  What a squad costs: `node tools/blender/mechs/bench_mech.cjs <port> <hero> [n] [preset]`.
- **Game hooks:** `buildMech` / `poseMech` / `setMechColor` / `freeMech` call it; a falling drop (`s.falling`) plays
  `drop_fall`, a fresh landing (`s.intro`) plays `hero_intro`, the landing shot keeps the camera shake.
- **Film it:** `node tools/blender/mechs/mech_drop.cjs <port> <outDir> [frame] [preset] [video]` plays a MECH DROP in
  Training (the client side only) and saves the stills and an mp4.

## Hitboxes (server boxes, not in the files)
- PAPER PLANE: about 1.6 x 4.9 x 1.4 m (wings excluded).
- NIGHT SHIFT: about 2.4 x 5.7 x 1.6 m (shield excluded).
