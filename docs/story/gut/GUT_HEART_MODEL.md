# The heart of the Gut: the model

The Gut's landmark. A giant heart that is about 1,700 human hearts grown into one, on a spiral tower of fused bone.
It is what Regrowth made of the war dead: nobody built it. This page is about the model only: what is in the files,
what placement and shader code can rely on, and how to rebuild it. Where it stands in the world, its collision, the
shared beat and the ground fog are in `BIG_HEART_PLACEMENT.md`.

| file | what |
|---|---|
| `public/models/story/s_gut_heart.glb` | the near model and the far model in one file (2.1 MB) |
| `public/models/story/s_gut_heart.json` | collision boxes, the stair, markers, which vertex channel holds what (32 KB) |
| `tools/blender/make_gut_heart.py`, `tools/blender/heartkit.py` | the build scripts (Blender 5.2) |
| `tools/blender/gut_heart_demo.html`, `tools/blender/gut_heart_shots.cjs` | the three.js page with the ripple running, and the script that serves it and renders the sheets |

It is **not** in `public/models/story/index.json` on purpose. That list is the props the city streams through
`public/js/city/props.js`, and that loader throws away every vertex channel except position, normal, uv and colour, so
the ripple would be lost. Load the landmark on its own, the way the train boss is loaded (nearest-filtered textures,
the small studio reflection), and keep `uv1`.

## Sheets
In the game's renderer (`docs/story/gut/`):
- `gut_heart_turn.jpg`: front, three-quarter, side, back, with a 1.8 m figure.
- `gut_heart_reads.jpg`: what you see in Gut fog with the game's 95° camera: 150 m (the far model, and the same
  zoomed), 60 m, 15 m at its foot, 5 m at the top of the stair under the apex.
- `gut_heart_close.jpg`: the small hearts at 15 m and 4 m, the vessels at the top, the back, the stair, the foot and
  the roots, where the bone holds it, and the near model beside the far model at 125 m.
- `gut_heart_ripple.jpg`: one beat in six moments, and the wave map (which heart goes when).
- `gut_heart_ripple.mp4`: the ripple running, from 60 m, 24 m and the top of the stair.

From Blender (`tools/blender/sheets/story/`): `s_gut_heart.jpg` (turnaround), `s_gut_heart_closeups.jpg`,
`s_gut_heart_lod1.jpg` (the far model).

## Space and size
Metres. x right, y up, **the heart's front faces +z**, its apex points to **+x**. The origin is the middle of the
tower's foot, on the ground. Roots and the knees of the buttresses go to y = -1.

| | |
|---|---|
| whole thing | 49.4 m to the tips of the feelers, 19.7 m across at the foot |
| the heart's body (apex to the top of the atria) | 14.3 m, 11 m wide |
| apex to the top of the aortic arch | 18.4 m |
| the feelers off the arch and the vena cava | another 3 to 4 m, thin |
| the spine | 29.4 m (19 vertebrae); the apex hangs at y = 27.6 |
| the stair | 101 treads, 0.25 m rise, 5.25 m a turn, 4.76 turns, top at y = 25.6 |
| a small heart | fused ones sit 0.36 to 0.53 m apart; whole ones are 0.37 to 0.7 m long (most about 0.5) without their stumps |

## Parts
All six meshes sit on the root with no transform. glTF has no hidden flag: **hide the three `_lod1` nodes on load**
and swap at about 120 m.

| node | what | materials |
|---|---|---|
| `gh_heart` | 1,577 fused hearts (each a low dome with its own painted heart, 354 of them with stumps of their vessels), 140 whole hearts standing out of the mass (most round the apex), 5 hanging off the apex on their own veins, the aorta, pulmonary trunk and vena cava as ropes of smaller vessels, feelers, coronary arteries and veins as tubes in the real grooves, strings of drip | `gh_flesh`, `gh_glow` |
| `gh_creep` | the flesh that comes down the tower: a sleeve under the heart with 13 hearts in it, the aorta and the vena cava down the spine (as in a body), small veins, a twig along every fourth rib, the web under the stair and between ribs near the top, six roots into the ground | `gh_flesh` |
| `gh_tower` | the spine (waisted drums of packed bone with pads between), 101 rib treads (every other one goes on round and down into the spine: the cage), a spur under the stair from each vertebra, 9 ribs that hold the heart (2 snapped short, 2 curled away), 5 thigh bones about 10 m long as buttresses, 3 hip blades, the mound, 9 human-size skulls | `gh_bone`, `gh_ossuary` |
| `gh_heart_lod1`, `gh_creep_lod1`, `gh_tower_lod1` | the same, far: 324 cells with nine painted hearts each, single-rope vessels, fewer ribs | the same four |

three.js turns a mesh with two materials into a group: `gh_heart` has children `gh_heart_1` (flesh) and `gh_heart_2`
(glow). Find materials by name, not meshes by index.

Materials:
- `gh_flesh`: one 256 px atlas (eight painted hearts, three unrolled hearts, the far model's tile, vessel swatches).
  Roughness 0.36, a thin clear coat. Everything that ripples.
- `gh_glow`: the pits between hearts where the inside shows. Dark base, an emissive ramp (black at the rim, deep red
  at the bottom), strength 1.5. Its own material so the game can pulse it. 96 pits, mostly along the grooves.
- `gh_bone`: 256 x 128 atlas (pitted bone, rib skin, cooked rib, burned bone, the pad between vertebrae, a skull face).
- `gh_ossuary`: 128 px, tiles, uvs in metres: the packed bone ends and faces the mass is made of.

All four are single sided. Vertex colours (COLOR_0) are a tint times baked occlusion: multiply them into the texture
(GLTFLoader does). The bone's tint also carries the war: charred on the flank that faced the flash (from -x, +z,
`markers.blast_from`), stained pink where the flesh reaches, dirty at the ground.

## The ripple
Every vertex of `gh_heart` and `gh_creep` (near and far, both materials) carries **TEXCOORD_1 = (phase, weight)**,
as floats. In three.js that is `geometry.attributes.uv1`.

- **u = phase.** When the beat reaches this vertex. 0 at the pacemaker (top of the right atrium, the heart's own upper
  right, `markers.pacemaker`), 0.30 by the far side of the atria, a pause, 0.38 where the ventricles start, **1.0 at
  the apex**. Every small heart has one phase. It goes on past 1 down the tower: 1.0 at the sleeve, 1.55 at the foot
  of the spine, 1.6 at the root tips. The great vessels on top run 0.5 to 0.98 (the aorta fills as the ventricles
  go), the vena cava 0 to 0.04.
- **v = weight.** How far this vertex moves. 0 = held still: every seam between hearts, the back of a whole heart
  where it is sunk in the mass, burned hearts (0.12, they barely twitch), roots. 1 = the crown of a small heart.
  Vessels 0.2 to 0.5.

One line in the vertex shader does it. Displace along the **normal**: flesh has no split normals anywhere it moves,
so nothing tears (the fused cells carry authored normals so each is lit as a ball; their rims have weight 0).

```glsl
// vertex shader, once
attribute vec2 aPulse;      // = TEXCOORD_1. in three: geo.setAttribute('aPulse', geo.getAttribute('uv1'))
uniform float uTime;
float ghBeat(float t) {     // lub-dub, then rest. t = 0..1 through one beat
  return exp(-pow((t - 0.12) / 0.045, 2.0)) + 0.6 * exp(-pow((t - 0.33) / 0.06, 2.0));
}
// after #include <begin_vertex>
float gh = ghBeat(fract(uTime * 0.72 - aPulse.x * 0.55));     // 0.72 beats a second; the wave takes 0.55 of a beat to cross
transformed += objectNormal * (aPulse.y * 0.09 * gh);         // 9 cm at a crown
```

The plainest version, if a sine is enough:
`transformed += objectNormal * aPulse.y * 0.06 * pow(max(0.0, sin(uTime * 4.5 - aPulse.x * 3.5)), 6.0);`

Two things the demo adds, both optional and both one line in the fragment shader (pass `gh * aPulse.y` down as a
varying):
- **the flush**: `diffuseColor.rgb *= 1.0 + 0.6 * vFlush;` after `<color_fragment>`. A 9 cm swell cannot be seen
  from 150 m; a wave of brightening can. This is what carries the ripple across the district.
- **the light inside**: `totalEmissiveRadiance *= 0.55 + 1.1 * vBeat;` on `gh_glow`, so each pit brightens as the
  wave passes it.

`geometry.attributes.uv1` is not declared by three's shaders unless a map uses it, which is why the snippet copies
it to its own attribute name. The far model has the same channel, coarser (one phase per 0.9 m cell): the same shader
runs on it, or drop the swell there and keep the flush.

If the model is ever loaded through the generic prop path instead, `uv1` is stripped; `gh_flesh` matches that
loader's `flesh` rule, so the whole heart breathes at once. It works, but it is not the ripple.

## The json
`s_gut_heart.json`, root space, metres.

- `boxes` (axis aligned, `[x0, y0, z0, x1, y1, z1]`): `tower` (10, the spine in 3 m lifts), `heart` (6 slabs, each
  inside the heart's outline at that height), `buttresses` (25, five per thigh bone), `mound` (2), `steps` (98 square
  pads, one per tread that exists: a walkable spiral made of boxes).
- `stair`: `rise`, `pitch`, `turns`, `dphi`, `axis` (the spine's centre and radius every 1.5 m: it is not straight),
  and `list`: every tread's `y` (its top), `phi` (it points along (cos phi, 0, sin phi) from the axis), `r0`, `r1`,
  `mid`, `state`. Three treads are `gone` (a gap to jump) and six are `stub` (half a tread). It climbs
  counter-clockwise seen from above.
- `markers`: `base_centre`, `listening_spot` (9 m out in front, clear of roots and buttresses), `stair_foot`,
  `first_tread`, `stair_top`, `apex` (2 m above and just past the end of the last tread: you can reach the hanging
  hearts), `heart_centre`, `pacemaker`, `top`, `glow_light` (where a point light inside the heart would go),
  `hanging_hearts`, `root_ends`, `femur_feet`, `rib_cup_tips`, `blast_from`.
- `ripple`: the channel, in words and as GLSL. `size`, `tris`, `nodes`, `materials`, `hearts`.

## Triangles
| | triangles |
|---|---|
| `gh_heart` | 29,969 |
| `gh_tower` | 8,659 |
| `gh_creep` | 4,093 |
| **near model** | **42,721** |
| `gh_heart_lod1` / `gh_tower_lod1` / `gh_creep_lod1` | 3,306 / 4,289 / 380 |
| **far model** | **7,975** |

Near: 5 primitives in 4 materials (4 draw calls once merged by material), about 49,000 vertices in the file. Far: the same count of primitives.

## What placement code can rely on
- Feet on y = 0 at the origin. Roots and knees go under to y = -1: put it on flat ground, or sink it a little.
- It has a front (+z) and a burned side (-x, +z). The stair starts at the front and ends under the apex on the +x
  side.
- How far it reaches from the axis (`size.reach_from_axis_m`): 11.6 m at the ground (the roots), 6.6 m up the tower, 8.9 m at the heart.
- The boxes are the model as built. The stair's pads are 0.22 m thick and overlap, so they climb as stairs.
- Hearts never move more than the shader's amplitude times their weight (9 cm with the numbers above). The `heart`
  boxes are inside the heart's outline, so the swell never matters to collisions.
- Nothing is rigged, skinned or animated in the file. The only motion is the shader's.
- Canon: this is the failed Regrowth trial's own work (Gristle & Sons, page 4). It should stand somewhere on the
  campus side of the Gut, alone. Dot and Mina are in the Gut; nothing on the model says whether they are in this.

## Rebuild
```
blender52 -b -P tools/blender/make_gut_heart.py                 # the glb, the json, the Blender sheets (about 2 min)
blender52 -b -P tools/blender/make_gut_heart.py -- --qa         # the same, plus the asset-QA gate on the near and the far model
blender52 -b -P tools/blender/make_gut_heart.py -- --no-export --preview=/tmp/p --views=front,q,hearts,stair    # a quick look
node tools/blender/gut_heart_shots.cjs                          # the sheets and the clip in the game's renderer; fails if uv1 is missing
node tools/blender/gut_heart_shots.cjs --serve                  # then open http://localhost:8787/gut_heart_demo.html
```
Flags: `--no-export`, `--no-sheet`, `--no-ao`, `--no-lod`, `--qa-warn`, `--lod` (preview the far model). The export
ends with `compact_glb`: normals and colours as bytes, TEXCOORD_0 as 16 bit (KHR_mesh_quantization, three.js reads it
as it is); positions and TEXCOORD_1 stay floats. 3.0 MB becomes 2.1 MB.

`heartkit.py` is this model's own kit. It repeats some of `rpkit.py` from the train boss's branch (the buffer idea,
the compactor, the picture helpers), because that file is not on `main` yet. When both are, they could share.

## QA
The asset-QA gate (`.claude/skills/blender-asset-qa`) passes on both models with no errors.

Warnings it gives, all accepted:
- UV overlap (99% on the flesh): every small heart is painted from one of eight tiles on purpose; nothing is baked.
- "Not resting on the ground": roots and knees go under on purpose.
- 2 back-to-back face pairs in `gh_heart`, 2 duplicate vertices in `gh_creep`: left in.

Found by the gate and fixed in the geometry: cells whose rim was ordered wrong (the surface was not one-sided there),
skulls floating in the spine's waists or buried in it (they are placed by a ray now), vessel stumps hovering over
their heart, spurs lying in the treads above them (z-fighting), zero-area uvs on three-sided tubes and the pits.

## Known weak spots
- A fused heart is 6 to 12 triangles and a 64 px painting. Past 4 m it reads as a heart; nose to it, it is a lump
  with a painted groove and a stump. The whole hearts carry the close read, and there are 158 of them, most round
  the apex where the stair ends. Higher up (out of reach without a grapple) the fused ones are plain cones.
- The hip blades and the mound at the foot are the least convincing bone: big, few faces.
- Skulls are human size and there are 9. From the ground you do not find them; on the first turns of the stair you do.
  The faces in the spine's texture do more.
- The heat-warped ribs are 12 of the stair's ribs that hang out and down instead of coming back in (most on the
  burned side), plus two of the ribs that hold the heart. It reads as "broken" more than "melted".
- Skin between the ribs was meant to thicken toward the heart; there are only 7 patches of it.
- Blistered and burned hearts are texture and tint only (no blister geometry).
- The far model's cells are bigger than the near one's, so the swap at 120 m is a small pop in the silhouette's bumps.
- The descending aorta behind the heart is a single tube, not a rope like the arch.
- The stair's boxes are square pads, not the ribs' real outlines, and the four missing treads are real gaps.
- 42.7k triangles is at the top of the budget. The cheapest cuts: the far side's whole hearts, or turning more of
  the fused domes (12 triangles) into cones (6).
