# Making the mechs in Tripo: which pictures to use

These pictures come from the concept models (`docs/mechs/CONCEPT.md`). Tripo turns them into the final meshes, then
`tools/blender/mechs/` cuts them onto the mech's joints so the animations and team colours still work. The text
prompts are with the owner already; this page is only about the pictures.

## The bodies (multiview: front, left, back, right)
Use Tripo's **multiview image to 3D** and give it the four pictures of one mech, in this order:

| slot | PAPER PLANE | NIGHT SHIFT |
|---|---|---|
| front | `paperplane_body_front.png` | `nightshift_body_front.png` |
| left | `paperplane_body_left.png` | `nightshift_body_left.png` |
| back | `paperplane_body_back.png` | `nightshift_body_back.png` |
| right | `paperplane_body_right.png` | `nightshift_body_right.png` |

- "left" = seen from the mech's own left side, "right" = from its right side.
- All four are orthographic at the same scale, in an A-pose with the arms out (so they don't fuse to the body).
- The light is even, with no shine, glow, stickers or text. The background is a light grey, not white, so the white
  plates don't vanish into it.
- The bodies have **no moving parts**: PAPER PLANE without its wings and crane drone, NIGHT SHIFT with empty hands
  (no sword, no shield). Those are made on their own (below) and attached afterwards.

## The moving parts (single image to 3D, one at a time)
Use **image to 3D** with the `_3q` picture (3/4 view). If Tripo gets the shape wrong, try the `_flat` one instead.

| part | 3/4 view | flat view |
|---|---|---|
| PAPER PLANE wing pair (the stowed V, seen from behind) | `paperplane_wings_3q.png` | `paperplane_wings_flat.png` |
| PAPER PLANE crane drone | `paperplane_drone_3q.png` | `paperplane_drone_flat.png` |
| NIGHT SHIFT sword (blade up) | `nightshift_sword_3q.png` | `nightshift_sword_flat.png` |
| NIGHT SHIFT shield (front face) | `nightshift_shield_3q.png` | `nightshift_shield_flat.png` |

## Settings and download
1. Keep the textures (PBR on is fine) and a mid poly count. Every model is decimated and given LODs later.
2. Download each result as a **GLB** and name it after its picture: `paperplane_body.glb`, `paperplane_wings.glb`,
   `paperplane_drone.glb`, `nightshift_body.glb`, `nightshift_sword.glb`, `nightshift_shield.glb`.
3. Put them in `docs/mechs/tripo/in/` (or send them to the session) and the swap-in script takes it from there.
   Models made on the owner's paid Tripo plan are the owner's to use (see `docs/story/cast_refs/TRIPO_LICENCE.md`).

## Remaking the pictures
`blender52 -b -P tools/blender/mechs/make_tripo_refs.py -- [mech=paperplane|nightshift] [spp=48] [res=1024]`

## After Tripo: putting the meshes on the rig
```
blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=paperplane qa   # (and mech=nightshift)
node tools/blender/mechs/clip_sheets.cjs                                  # every clip on the new meshes, in three.js
node tools/blender/mechs/compare.cjs <out.jpg> "front,q,side,back" a=<one.glb> b=<other.glb>   # side by side
```
- `tripo_swap.py` reads the GLBs from `docs/mechs/tripo/in/` (`in=<dir>` for another folder) and writes over
  `public/models/x_mech_<name>.glb`, keeping every joint, marker and clip. `qa` runs the asset gate on the result.
- No body file means nothing changes: the concept model stays as the fallback.
- **Rigged downloads cut best.** When Tripo's auto-rig is on, the GLB carries a skeleton and skin weights:
  - each face goes to the joint its bones point at;
  - the rig's elbows, knees and spine move onto Tripo's own pivots, so limbs bend where the mesh does.
  - Without a rig, the concept arms are posed to fit inside the mesh, and each face goes to the nearest concept part.
- Tripo builds bodies out of separate plates, so whole plates stay on one joint.
- **The Tripo look stays as it is** (the owner's call, 2026-11-12): its heads, V horns, faces and plates.
- **Kept from the concept** (`keep=` changes the list):
  - PAPER PLANE's pencil pods and highlighter cannons (gameplay add-ons, no Tripo face is cut onto them);
  - NIGHT SHIFT's hands (Tripo's came out melted, and these grip the sword).
- **Hand-placed paint** (`PAINT_SPEC` in the script, boxes in game metres):
  - helmets, V horns, forehead and chin;
  - glowing eyes, NIGHT SHIFT's forehead lamp, PAPER PLANE's back nozzles.
  - New Tripo bodies need their own entries: `dump_mesh=<path.glb>` writes the fitted mesh to pick spots from.
- **Untextured meshes** take their paint from the concept, one colour per plate. Each part ends up with about the
  concept's mix of team colour, white, dark and metal. Team colours keep working.
- **Clean-up, all automatic:**
  - lumpy plates (`hull=`: NIGHT SHIFT's shins) are rebuilt as clean faceted armour;
  - chips that float at rest, doubled triangles and folded faces go, so the asset gate passes;
  - `rods=drop` also drops thin rods (off by default: the look stays).
- **Painted metal** (`metalkit.py`):
  - metallic car paint with a clear coat, brushed gunmetal frames, gold accents;
  - one shared tiling detail set (panel lines, rivets, scratches, chips, grime);
  - baked vertex shading (occlusion, worn edges);
  - small chamfers on the Tripo plate edges so the light catches them (`bevel=`, 1.4 cm NIGHT SHIFT, 8 mm PAPER PLANE).
  - `flat` builds without it.
- Moving parts (wings, crane, sword, shield) are fitted onto the concept ones (`JF_TRIPO ... fit error`). A part
  named in `concept=` keeps the concept one.
- Turn the body with `yaw=0` if Tripo's front came out facing the other way.
- Test without real files: `-- mech=nightshift make-standin=<dir>` writes a fake Tripo input from the concept model.
  Then run the swap with `in=<dir> out=<test.glb>`.

## The first batch (2026-11-12): what went in, what to remake
Pictures: `compare/paperplane.jpg` and `compare/nightshift.jpg` (three.js, as in the game), and `ingame/` (Training, Too
HD; `mechdrop_A.jpg` and `mechdrop_B.jpg` through MECH DROP's own loader).

| file | used? | notes |
|---|---|---|
| `paperplane_body_a.glb` | **yes (until the owner picks)** | Broad shoulder fins, spiky gauntlets. No rig, so the arms are fitted (see below). |
| `paperplane_body_b.glb` | **the other pick** | Slimmer and darker, sabre hilts on the back. Rigged, so it cuts cleanly. `body=paperplane_body_b` builds it. |
| `nightshift_body.glb` | **yes** | Heavy knight. Its melted hands were swapped for the concept's, and its lumpy shins rebuilt. Its forehead lens is the headlamp. |
| `paperplane_drone.glb` | no | A winged helmet, not a crane. The concept crane stays. |

To remake in Tripo, if the owner wants:
1. **PAPER PLANE A with the auto-rig on** (same picture, rig enabled before download): the cut gets Tripo's own elbows.
2. **The crane drone** from `paperplane_drone_flat.png`, or with "origami paper crane" in the prompt.
3. Wings, sword and shield whenever wanted (the concept ones are in for now).
