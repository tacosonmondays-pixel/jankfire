# REVENUE PROTECTION: the model

The boss of `m06_tickets_please` (TICKETS, PLEASE). This page is about the model only: what is in the files, what the
fight and animation code can rely on, and how to rebuild it. No fight code and no animation is in here yet.

| file | what |
|---|---|
| `public/models/story/revenue_protection.glb` | the mask, the 17:32 behind it, the inspector (3.8 MB) |
| `public/models/story/rp_arm.glb` | the arm kit: one segment, the wrist knot, the hand, a stump (0.3 MB) |
| `public/models/story/revenue_protection.parts.json` | every part's box, its break stage, the markers (15 KB) |
| `tools/blender/make_revenue_protection.py`, `tools/blender/rpkit.py` | the build scripts (Blender 5.2) |
| `tools/blender/rp_shots.cjs`, `rp_shots.html` | the sheets in the game's renderer, and the load check |

Neither `.glb` is in `public/models/story/index.json` on purpose: that list is the story props the city loads. Load the
boss when the mission starts (`glbkit` treatment: nearest textures, the studio reflection).

## Sheets
From Blender (`tools/blender/sheets/`): `rp_turnaround.jpg` (front, three-quarter, side, back in a ring the size of the
bore with a 1.8 m figure), `rp_stages.jpg` (the three break stages), `rp_closeups.jpg` (enamel and bolts, a crazed plate,
the blown eye, the mass at 6 m, the inspector, the far LOD, the hand open and gripping, eight segments on a curve).

In the game's renderer (`docs/story/train/`): `rp_game_turn.jpg` (the same turnaround, plus the view from the wagon at
22 m and 8.5 m in tunnel light), `rp_game_stages.jpg` (the stages, studio and tunnel light, driven by the parts file),
`rp_game_close.jpg` (the close-ups, the near plug beside `mass_lod` at 30 m, and the arm kit as a chain).

## Space
Metres. x right, y up, **the mask faces +z** (toward the train). The origin is the middle of the 9.2 m bore, on the
plane of the plates' backs; the enamel face is at z = 0.14. The track bed of the concept's tunnel is at y = -3.13, so
the bottom of the disc is under the floor (as in the approved concept). "L" is the mask's own left = **+x** = on your
right when you face it.

## Parts (`revenue_protection.glb`)
Three groups under the root: `mask`, `mass`, `inspector`. Move `mask` and the whole sign goes.

| node | what | notes |
|---|---|---|
| `plate_00` .. `plate_11` | the enamel plates with their bolts | 00-03 inner quadrants (from +x, counter-clockwise), 04-11 outer, 45° each. 02 03 08 09 10 11 are the lower ones. 11 carries ☺ CORP's asset tag |
| `plate_NN_crazed` | the same plate in five shards, a hair out of place, on the cracked texture | hidden. Swap it in when a plate has taken enough, then drop it |
| `plate_NN_up`, `plate_NN_low` | 02 03 08 11 split along the smile crack | hidden. Stage 3: `_low` drops, `_up` stays on |
| `frame`, `frame_low` | the back lattice, hoop and hub | `frame_low` is everything under the smile crack: it drops in stage 3 |
| `eye_R`, `eye_L` | the lamp housings (bezel, can, what is left of the lens) | origin on the hinge pin (outer side): turn about y to swing one open. Inside is `rp_void`, so they stay black |
| `eye_L_blown` | the left housing burst from behind | hidden until stage 2 |
| `eye_cluster` > `eyeball_00` .. `eyeball_12` | the real eyes behind it | hidden until stage 2. Each ball's origin is its centre and it looks along +z: aim them at the player |
| `anchors`, `anchor_hang` | ☺ CORP's clamps and cyan ratchet straps | five let go in stage 3, `anchor_hang` (top, a little left) is what the face hangs off |
| `mass_ne`, `mass_nw`, `mass_sw`, `mass_se` | the plug of commuters in four wedges | each is closed (the cut faces are meat), so it can come apart along a cross at the end |
| `mass_lod` | the plug as one 624-triangle mesh, the near one photographed onto its face | hidden. Use it far away, or while every plate is still on |
| `inspector` | empty at his waist (scale 1.12) | `insp_body`, `insp_head` (origin on the neck), `insp_armR` > `insp_foreR` > `insp_punch_lever`, `insp_armL` > `insp_foreL`, `insp_base` (the mound he is fused into) |

Hidden parts are visible in the file (glTF has no hidden flag). Each carries `jf_hidden: 1` in its extras, the root's
`jf` has the list (`hidden`), and the parts file marks them `"hidden": true`. Hide them on load.

Materials: `rp_enamel`, `rp_enamel_crazed` (512 px, the whole face seen straight on, with a roughness map), `rp_steel`
(128 px swatches with a metal / roughness map), `rp_void`, `rp_char` (64 px, tiles), `rp_pack` (128 px, the plug's
wall), `rp_bits` (128 px: faces, lanyards, ID cards, clothes), `rp_mass_lod`, and the three that glow, each its own
material so the game can drive it: `rp_inspector_glow` (his chest, eyes and mouth), `rp_eye_glow` (the cluster),
`rp_knot_glow` (the wrist knot, in `rp_arm.glb`). Vertex colours (COLOR_0) are baked AO times a tint.

## The arm kit (`rp_arm.glb`)
Every piece sits on the file's origin: clone what you need.

| node | what | how to use it |
|---|---|---|
| `arm_seg` | 1.5 m of rope: eight arms round the outside, four inside, a quarter turn of braid | runs from its origin along **+z**. Chain them: put each at a joint and `lookAt` the next. Arms overhang the far end by about 0.3 m, which covers the joint when the chain bends. 0.6 m thick |
| `arm_knot` | the wrist: lanyards wound into a ball, ID cards, lit from inside | origin at its centre, radius 0.42. The weak point |
| `arm_hand` | the hand made of hands | wrist at the origin, fingers along +z, **the palm faces -y**, thumb on +x. 1.9 m long |
| `f0` .. `f4` > `f?_a` > `f?_b` > `f?_c` | thumb and four fingers, three joints each | `f?` holds the finger's spread. Curl a joint with `rotation.x` (+ closes): 0 is open, about 0.95 on every joint is a grip (0.7 on the thumb) |
| `arm_stump` | what is left when the wrist is shot through | the cut faces +z; put it on the last segment's far end |

To get past the rim the first two segments have to be flat: scale them to about 0.35 along the tunnel's radius. A whole
0.6 m rope does not fit in the 0.19 m between the hoop and the bore.

## The parts file
`revenue_protection.parts.json`, root space, metres.

- `parts[]`: `name`, `centre`, `half` (axis-aligned half extents of the part as built), `stage` (the break stage that
  takes it away, 0 = never), `group`, `tris`, and where they apply `hidden`, `shown_from` (the stage it appears at),
  `instead_of` (what it replaces), `pivot` (its origin, when that is not the root's).
- `stages`: what each of the three does, by node name. Stage 1 lists the plates the sheets drop (09, 06, 11); the
  fight can drop any plate. Stage 2 hides `eye_L`, shows `eye_L_blown` + `eye_cluster`, and swaps 02 03 08 for their
  halves (the smile is back, as a crack). Stage 3 drops the `_low` halves, `plate_10`, `frame_low` and `anchors`, and
  gives the pivot the rest hangs from.
- `markers`: `eye_L` / `eye_R` (centre, half size, hinge, depth), `inspector` (`at`, `crit` and `crit_r`, `head`,
  `punch`, his joints), `hang_bolt`, `anchors`, `hub`, `smile_crack` (25 points, rim to rim), `plate_face_z`,
  `glass_z` (the backs of the plates, where the hands are pressed), `sockets` (12 round the rim: `pos`, `dir`, `out`),
  `mouth_sockets` (4, for the arms that come out of the mouth in stage 3).
- `tunnel`: the bore, the floor, the radii. `tris`, `materials`, `lod`, `arm` (the kit's numbers).

## Triangles
| | triangles |
|---|---|
| mask (12 plates, lattice, hoop, eyes, clamps) | 14,916 |
| the 17:32 | 33,471 |
| the inspector | 2,008 |
| **on screen, whole** | **50,395** |
| hidden damage pieces (crazed plates, halves, blown eye, cluster) | 15,174 |
| `mass_lod` | 624 |
| `arm_seg` / `arm_knot` / `arm_hand` / `arm_stump` | 1,164 / 1,100 / 2,748 / 173 |

With `mass_lod` in place of the plug and the inspector (the mask whole, nothing behind it showing) it is about 15,500.

## What the fight can rely on
- Every plate is its own mesh with its bolts. Hide one and the hole is real: lattice, then bodies, hands flat against
  where the enamel was.
- The canonical order above is only what the sheets show. Any plate can be crazed and dropped at any time. If 11 is
  still on at stage 3, use `plate_11_up` / `plate_11_low` like the other three.
- The smile crack runs through plates 08, 02, 03 and 11, and `frame_low` is cut on the same line, so nothing is left
  in front of the inspector once the lower third has gone. Plates 09 and 10 are wholly under the crack.
- The inspector is in the mouth: his cap is 15 cm under the lowest point of the crack. He is hidden until stage 3.
- Boxes in the parts file are of the part as built. Swing an eye, hang the mask or curl a finger and the box no longer
  holds: transform it with the node.
- Nothing is rigged or skinned. Everything that moves is a node with its origin on its pivot.

## Rebuild
```
blender52 -b -P tools/blender/make_revenue_protection.py              # both .glb, the parts file, the Blender sheets (3.5 min)
blender52 -b -P tools/blender/make_revenue_protection.py -- --qa      # the same, plus the asset-QA gate on 28 groups
blender52 -b -P tools/blender/make_revenue_protection.py -- --only=mask --no-ao --preview=/tmp/p --views=front,q,eye --stage=2   # a quick look
node tools/blender/rp_shots.cjs                                        # the sheets in the game's renderer; fails if a part is missing
```
Flags: `--no-export`, `--no-sheet`, `--no-ao`, `--no-lod`, `--stats`. The export ends with `compact_glb` (normals,
colours and UVs quantized, positions left as floats so no node gets a scale): 5.2 MB becomes 3.8 MB. three.js reads it
as it is.

## QA
The asset-QA gate (`.claude/skills/blender-asset-qa`) passes on all 28 groups with no errors: the mask whole, the plug
with the inspector, each crazed plate and each half on its own, the blown eye, the cluster, and the four arm pieces.
Crazed plates are checked with a 3 cm contact tolerance, because their shards are a crack apart on purpose.

## Known weak spots
- 3.8 MB is big for this repo (the next largest model is 1.6 MB). It is mostly vertices: 65,000 triangles with the
  hidden pieces. The crazed plates are a fifth of it.
- The plug's wall and back are a texture of packed commuters on a lumpy barrel, not modelled people. You never get
  behind it in the fight.
- The commuters are built from one head, one torso and four hands. Up close they are alike.
- The hand's palm is a slab with arms laid on it. The fingers carry the idea, the palm less so.
- The inspector's face is a 16 px decal on a low-poly head, and his punch is small in his fist.
- A whole arm cannot pass the rim (see the arm kit). The game has to flatten the first segments.
