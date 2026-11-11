# Effects from Blender: what works, what it costs, what to redo first

Owner, 2026-11-11: "research how to do proper ripples splashes smoke fire auras fog other weather effects in blender".
This is research plus two small proofs. Nothing here changes what players see.

## Short version
- Blender's job for a game like ours is to **bake pictures**: flipbook sprite sheets (smoke, fire, splashes, explosions),
  normal maps (water) and a few meshes (aura shells, lightning bolts, snow cover). The game then plays them cheaply.
- Rain, snow, dust, fog and auras should **stay in code** (particles, shaders, the fog we already have). Blender adds
  little there except a sprite or a mask.
- In our environment the real smoke/fluid solver (Mantaflow) does not run in either Blender. Everything else does.
  Fire and smoke can still be baked from noise volumes, and that is what the proof does.
- Recommended order: 1. explosions + muzzle smoke as flipbooks, 2. fire flipbook option, 3. the ocean normal map on the
  big seas, 4. splash crown re-render, then weather (rain, snow) in code.

## What runs here (tested 2026-11-11)
| | `blender52` (bpy 5.2.3) | `blender` (apt 4.0.2) |
|---|---|---|
| Cycles (CPU) | works; 96 px volume frame about 4 s at 16 samples | fails: "Build without OpenImageDenoiser" on render (denoising would need switching off; not retried) |
| EEVEE headless | works on software GL, about 27 s for the first 64 px frame | works, about 5 s |
| Workbench | works | works |
| Ocean modifier | works | works |
| Classic particle systems | works | works |
| Geometry Nodes volume grids (advect, curl, gradient) | present | older SDF/volume nodes only |
| Mantaflow smoke / fire / liquid | **fails**: `'LevelsetGrid' object has no attribute 'setConst'`, then `Manta::Error ... can't clean grid cache` | **fails** (coordinator's run): `PyImport_AppendInittab() may not be called after Py_Initialize()` |

The `setConst` error is a known symptom of a `bpy`-as-a-module build where Mantaflow's Python side does not match
(same error reported on Blender's developer forum, no fix given). I found no workaround for the pip module. A normal
desktop Blender (not the pip module, not apt 4.0.2) is what would bake `tools/sprites/smoke_sim.py`. Not tried: building
Blender from source, or the Geometry Nodes grid-advect nodes as a home-made smoke solver (possible in 5.2, a project of
its own).

## How each effect should be made
Costs are for our renderer: one instanced draw per sprite sheet, see-through quads cost fill (overdraw), a 576 px RGBA
sheet is about 1.3 MB of GPU memory (about 1.8 MB with mipmaps). "Potato" = what that preset should do.

| effect | make it in Blender as | keep in code | cost in game | Potato |
|---|---|---|---|---|
| **water ripples** (surface) | a tiling normal map: Ocean modifier read off the mesh (proof below) for seas; rings for ponds are better drawn (ours) | two layers of the map sliding across each other in the water shader (already there as "painted water ripples") | 2 texture reads a pixel, 256 px map, no extra draws | off: the two-sine shader |
| **splashes** | a side-on crown flipbook: particles + a lathe sheet or metaballs, white with alpha, 16 frames 4x4; top-down ring flipbook | droplets as particles; where and when | 1 draw per sheet, a few quads | code squares |
| **smoke** | flipbook, 36 frames 6x6, 96 px cells, shading in colour and thickness in alpha. From a sim where one runs, else a noise volume in Cycles | spawn, drift, sort, fade; one tint per use | the heavy one: up to 240 see-through quads; +15 to 25% frame time with 3 clouds on software GL | code squares |
| **fire** | looping flipbook from a noise volume with glow (proof below): 36 frames, last 6 cross-faded into the first | the flicker light, embers and smoke on top; cartoon fire can stay the shader we have | 1 draw, 1 to 3 quads a fire, premultiplied so it glows without a second pass | the shader flames |
| **explosions** | one-shot flipbook 8x8 (64 frames): fireball noise volume with a colour ramp that cools to smoke | flash, shockwave ring, debris, light | 1 draw, 2 to 4 big quads for half a second | code particles |
| **auras** (players, items) | a shell mesh (the model pushed out along its normals) with scrolling UVs, or a ring/column card with a tiling noise texture; Blender only makes the mesh + texture | the look is a shader: fresnel rim + scrolling noise, additive | 1 extra draw per aura'd thing, small | a flat ring |
| **fog** | nothing | the scene fog + height haze we have; for patches, a few big soft cards using the smoke sheet | free (fog) or a handful of quads | fog only |
| **rain** | at most a streak sprite and a ground-hit ring flipbook (the weather skill renders a top-down ripple) | camera-attached streak particles, ground rings, the wet look as a material tweak | a few hundred streak quads in one draw | fewer, shorter streaks |
| **snow** | a flake sprite; snow cover as geometry on maps that need it (`surface_weather.py --snow-depth`) | falling flakes as particles with sway | one draw | fewer flakes |
| **wind / dust** | a dust-puff flipbook (the smoke sheet, tinted) and a leaf sprite | particles pushed by a wind vector | small | off |
| **lightning** | a bolt mesh or 3 or 4 bolt sprites (`lightning.py` builds a branching curve) | the flash is a light + sky brightness keyed 3 strokes about 50 ms apart; random bolt picked in code | 1 quad for 100 ms | flash only |

Rules that came out of the proofs and the reading:
- **Render on a see-through film, straight to a grid.** Every frame the same size, nothing touching a cell's edge (fade
  the last few pixels), same frame count per sheet. Sheets that crop or rescale frames make the effect "breathe".
- **36 frames (6x6) is enough for loops at about 15 a second; 64 (8x8) for one-shots.** 96 px cells read fine at our
  resolutions and keep Potato's chunky look when shown with nearest filtering.
- **Loops**: render a few frames past the end and cross-fade them into the start.
- **Colour or shading?** Smoke: store shading (lit from the top left) and tint it in the game, so one sheet does white
  smoke, dust and steam. Fire: store colour, premultiplied, drawn unlit.
- **Flat sprites facing the camera look wrong from above** for tall things (fire columns). Use 2 crossed cards or keep
  those effects short. Six-way lit smoke (one sheet lit from six sides, mixed by the real sun) is the next step up if
  we ever want smoke that takes the map's light direction; it doubles the texture.
- **Never export rain or snow as geometry.** Weather is a runtime system; Blender delivers sprites and masks.

## Proofs (made here, shown in the game)
Both scripts run headless with `blender52`. The outputs are in `public/sprites/` (the ocean map is used on the seas since the ocean PR; the fire proof sheet is not used).

1. **Fire flipbook without the fluid solver**: `tools/sprites/blender/fire_flipbook.py`. A box of volume; density and
   glow from 4D noise sliding up through a flame-shaped mask; Cycles, 96 px, 16 samples, 42 frames in about 3 minutes;
   packed 6x6 with a looped seam. 519 kB. `docs/gfx/blender/fire_sheet.jpg` is the sheet,
   `docs/gfx/blender/proof_fire.jpg` shows it next to today's shader flame on Islands. It reads as soft, realistic
   fire. It is noisier than a production bake (more samples would fix that) and has no ink or banding, so it does not
   match the comic flames; it would suit the soft smoke the owner picked.
2. **Water normal map from the Ocean modifier**: `tools/sprites/blender/ocean_normal.py`. Reads the wave heights off
   the modifier's grid (it tiles exactly), turns them into a 256 px normal map. Under a second. 135 kB.
   `docs/gfx/blender/proof_water.jpg`: the lagoon with the shader only, with our drawn ripple map, and with the ocean
   map. The ocean map gives wind-blown open-water streaks (good for the seas); the drawn one gives raindrop rings (good
   for ponds and pools). They can be per-liquid.

Not proven: a splash flipbook from Blender (particles + metaballs is the plan; not built), EEVEE for sheets (works but
slow on software GL; Cycles was faster for volumes here), anything from Mantaflow.

## What to redo first
1. **Explosions and muzzle smoke as flipbooks** (frag, rockets, the rig, car wrecks). Biggest visible jump per effect,
   short-lived so overdraw is cheap, and the fire proof's method (noise volume, colour ramp) is the same recipe.
2. **Fire as a flipbook option** next to the shader flames, for the flare and burning cars. Proof exists.
3. **Ocean normal map on the open seas**, drawn ripple map on ponds; decide the "painted water ripples" default.
4. **Splash crown re-rendered in Blender** in the soft style, replacing the comic crown now that smoke is soft.
5. **Rain, then snow, in code** (streak particles, ground rings, a wetness tweak), with sprites from Blender only where
   needed. A new feature, not a redo, so it comes after the redos.
6. Auras and lightning when a weapon or map needs them: both are mostly shader work.

## Add-on: real subsurface scattering and surface detail maps (flesh ground, character skin)
The owner asked the Terrain lane: "Are there height map and sub surface scattering on stuff?" Today: no height maps
anywhere; normal maps only on Blender props and weapons (`models.js` keeps a GLB's `normalMap`); the story's flesh
ground is a Standard material with a painted canvas texture and a pulse in the vertex shader (`city/mats.js`); skin has
the soft-skin term from PR #125 (wrap light + back light for the sun, no maps). This section is reading and reasoning
from the code and from three.js as shipped (0.170); nothing in it was built or measured.

**What "real" SSS costs, and what we can afford**
| technique | what it is | cost | fits us? |
|---|---|---|---|
| wrap + back light (soft skin, have it) | light bleeds past the shadow line, glows through from behind | a few lines in the material's shader, no textures | yes, every preset above Crusty; it is the base |
| + **thickness map** ("fast SSS") | a baked texture saying how thin the mesh is there; thin parts (ears, fingers, flesh ridges) let more light through. three.js ships this as an example shader (`SubsurfaceScatteringShader`) | 1 extra texture read; the map is baked once in Blender (bake ambient occlusion with normals flipped, or just paint it) | yes at Mid and up. The biggest step up for the price. Needs UVs, so Blender-made meshes only (not the box mannequin) |
| pre-integrated skin (a lookup ramp by light angle and curvature) | red-tinted soft terminator done by a small ramp texture | 1 tiny texture read | yes, but only shows on smooth curved meshes; our flat-shaded low-poly limbs barely benefit |
| screen-space SSS (blur the lit skin in screen space) | what AAA faces use | extra full-screen passes + a skin mask | no. Too heavy for our presets and it would smear the pixel look |
| three.js `MeshPhysicalMaterial` transmission / thickness | made for glass and thin plastic, renders the scene twice | a whole extra scene pass | no for skin or ground |

**Surface detail maps**
| map | what it does | cost | fits us? |
|---|---|---|---|
| normal map | fakes small bumps in the lighting | 1 texture read, no extra geometry | yes, Mid and up. For the flesh ground: bake it from the same painted veins and pores so it lines up |
| bump map (from a height texture) | same idea from a grey height image | 3 reads of 1 texture | yes; simplest for canvas-painted textures because no baking step is needed, a little softer than a normal map |
| height / displacement map | really moves the surface | needs many more triangles (tessellated ground) | only where the mesh is already dense: the Terrain lane's real terrain meshes. Not on box maps |
| parallax mapping | fakes depth by shifting the texture with view angle | 1 to 16 extra reads a pixel, custom shader | maybe, Too HD only, for the flesh ground; low priority |

**Where Blender comes in**: baking. Thickness, normal and ambient-occlusion maps for any Blender-made mesh
(`blender-texturing`, `blender-pbr-materials` skills); a tiling normal + height pair for the flesh ground rendered from a
sculpted or noise-displaced plane (the ocean script here is the same idea). Both run headless with `blender52` (Cycles
baking works here; not exercised for this section).

**Per preset**
- Potato, Crusty: none of it. Flat colours and the painted textures, as now.
- Mid: soft skin (have it) + a bump or normal map on the flesh ground.
- Too HD: the above + thickness-map SSS on Blender-made skin and on the flesh ground's ridges + optional parallax.

**Suggested first step**: the flesh ground, because it is one material and it is all over the story's Big Stomach
district. Paint a height layer next to the existing colour canvas, feed it as a bump map, and add the soft-skin term
with a thickness value from the same height (ridges thin, valleys thick). One file (`city/mats.js`), no new assets, and
a before/after is easy to shoot. Character skin gets the thickness map when the mannequin is replaced by a Blender mesh
with UVs; on the box mannequin there is nothing to map it onto.

Sources for this section (three.js as vendored in `node_modules/three`, not opened on the web this session):
`examples/jsm/shaders/SubsurfaceScatteringShader.js`, the `bumpMap` / `normalMap` / `displacementMap` properties of
`MeshStandardMaterial`, and the transmission pass in `WebGLRenderer`.

## Tested / not tested
Tested here: the capability table above; both proof scripts end to end; both proofs loaded in the game (headless
SwiftShader, Islands, Too HD) with no page errors. Not tested: a real GPU, frame time of the proofs, dark maps, any of
the "how to make it" rows other than fire, smoke and water (they are the standard methods, not things built here).

## Sources
- Flipbook basics, grid sizes and pitfalls: https://vfxdoc.readthedocs.io/en/latest/textures/flipbooks/
- Six-way lit smoke: https://unity.com/blog/engine-platform/realistic-smoke-with-6-way-lighting-in-vfx-graph
- The `setConst` Mantaflow error in the bpy module: https://devtalk.blender.org/t/python-module-bpy-mantaflow-issues-after-successful-build/15460
- A related Mantaflow bake failure through Python: https://projects.blender.org/blender/blender-addons/issues/75889
- Blender sprite-sheet baking discussion: https://blenderartists.org/t/particle-sprite-sheet-for-3d-game/621114
- In the repo: `.claude/skills/blender-weather-fx` (rain, snow, lightning, wet surfaces, real-time notes),
  `docs/gfx/sprites/README.md` (the smoke test, the Kenney and Unity packs).
