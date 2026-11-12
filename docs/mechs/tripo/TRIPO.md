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
blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=paperplane      # (and mech=nightshift)
node tools/blender/mechs/clip_sheets.cjs                                   # every clip on the new meshes, in three.js
```
- `tripo_swap.py` reads the GLBs from `docs/mechs/tripo/in/` (`in=<dir>` for another folder) and writes over
  `public/models/x_mech_<name>.glb`, keeping every joint, marker and clip.
- No body file means nothing changes: the concept model stays as the fallback.
- The cut is done in the same A-pose as the pictures:
  - Each Tripo face goes to the joint of the nearest concept surface, then pieces are tidied along the seams.
  - Paint areas get a grey copy of Tripo's texture under the team colour, so team tinting still works.
  - Glowing areas glow.
- Moving parts are fitted onto the concept parts automatically. The fit error is printed (`JF_TRIPO ... fit error`).
- If a part comes out turned wrong, re-run Tripo with its `_flat` picture.
- `body_tris=45000` and `lod_tris=7000` set the near and far budgets. Each joint gets a far copy named `<joint>_lod1`.
- Turn the body with `yaw=0` if Tripo's front came out facing the other way (the default `yaw=180` suits glTF's +z front).
- Test without real files: `-- mech=nightshift make-standin=<dir>` writes a fake Tripo input from the concept model.
  Then run the swap with `in=<dir> out=<test.glb>`.
