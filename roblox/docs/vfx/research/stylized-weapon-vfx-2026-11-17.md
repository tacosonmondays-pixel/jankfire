# Stylized, glowy weapon and aura VFX on Roblox: research notes (17 Nov 2026)

After the owner's reference clip (weapons wrapped in coiling ribbons of golden light, star glints, golden smoke, big
crescent slashes) and their ask to look through YouTube, forums, GitHub and X. A research pass; Reddit could not be
reached (blocked to automated reads) and X gave only search snippets. Numbers marked * are starting values, not from a
source.

## Techniques
- **Mesh VFX**: spin and scale a crescent or ring mesh, the MeshPart itself transparent, the art on Texture children
  (Textures project per face, so a crescent uses Top and Bottom). EasyVFX's defaults: scale 0.6 -> 1.4, spin 90 deg,
  0.5 s. Scroll by stepping `Texture.OffsetStudsU/V`; true UV scrolling only through EditableMesh (Play only). Mesh
  flipbooks: a mesh sequence swapped each frame. Cheap energy shell: ForceField material + TextureID. Overbright:
  `Texture.Color3` or `SpecialMesh.VertexColor` 2-5 blooms (VertexColor reported clamped inside a character).
- **Emissive masks** (since Feb 2026): `SurfaceAppearance.EmissiveMaskContent` / `EmissiveStrength` / `EmissiveTint`,
  scriptable, bloom like Neon; paint vines into a skin's mask and pulse the strength. Unconfirmed: test before relying.
- **Beam arcs**: CurveSize = (4/3) tan(theta/4) r. Semicircle: diameter x 2/3; quarter: 0.5523 r (four beams make a
  ring). Negative CurveSize mirrors. About 50 Segments. TextureSpeed gives motion with no code; three beams with
  different speeds on one pair shimmer.
- **Coils**: beams under one holder, spin the holder each frame
  (`holder.CFrame = handle.CFrame * CFrame.Angles(0, 0, rot)`); or trails on orbiting attachments.
- **Glints**: Speed 0, Acceleration 0, frozen flipbook (FlipbookFramerate 0 + FlipbookStartRandom); a twinkle is two
  bumps in the Size curve.
- **Stylized smoke**: hard edge of about 1 px, 2-3 grey levels, darker rim; Transparency about 0.3, low LightInfluence,
  kept under about 0.45 grey. Custom flipbook grids (FlipbookSizeX/Y, client beta) allow 32+ frames.
- **Bloom stacking**: with Bloom threshold 1 only pure white blooms, so push cores above it (Brightness on Beams and
  Trails, particles with LightInfluence 0, Color3 above 1): a white-hot core, colour at the edges, the core fading
  first; shrink cores (additive whites stack into a disc). On a pale scene LightEmission 0.35-0.55 clips far less. A
  dark LightEmission 0 copy behind for contrast (our dark twins).
- **ZOffset**: gaps of 0.001 are enough to layer; glows over a body 2-4; -1/-2 behind; ground layers 0.
- **Steady glow, no flicker**: Lifetime 1, Rate 2, Transparency 1 -> 0 -> 1 (two overlapping add to a constant).
- **Colour**: 20 keypoints at most; beams need at least n-1 segments for n keys. White -> main -> second colour over
  about 0.35 s.
- **Timing** (stated, not measured): a flash lasts 1-4 frames; a slash is full size on frame 1; the peak falls in the
  first 25 %; layers die at different times.
- **First person**: since release 638 the default camera hides emitters, beams and trails parented to the Character in
  first person (ours sit on the viewmodel, not the character; check new ones).

## Tools
Free: Krita, GIMP (Polar Coordinates turns streaks into crescents), Blender (a swirl mesh: cylinder + Clouds mask,
Smooth, Simple Deform 360 deg), EasyVFX and Spark (MIT runtimes). Paid: Photoshop, After Effects, EmberGen. Plugins
(prices not checked): VFX Forge, VFX Suite, Moon Animator 2, ZonitoVisuals, Ro's Particle Editor, VFX Studio, VortexFX.

## Recipes
1. Beam crescent slash: CurveSize 12.67 on 19-stud attachments, 50 segments, 3-6 beams on one holder, a gold texture
   with a pink rim, LightEmission 1, LightInfluence 0, Brightness 3, a dark copy at ZOffset -0.05; tween Width to 0
   while the holder turns -90 -> +175 deg over 0.15-0.2 s*; particle slashes under it (Lifetime 0.3,
   VelocityPerpendicular).
2. Mesh crescent: transparent body, Top/Bottom Textures with Color3 (4, 3, 1.6)*; size 0.6 -> 1.4, spin 90, fade, 0.15 s*.
3. Coiling vine: attachments on a helix, 4 per turn, X along the tangent, CurveSize 0.5523 r, FaceCamera off,
   TextureSpeed 1*, a wider soft beam on the same attachments at +0.001 ZOffset, the holder spinning 1.5 rad/s*.
4. Orbit trail: pivot at the muzzle, `CFrame.Angles(0, 0, t*6) * CFrame.new(r, 0, 0)`, Trail Lifetime 0.25*,
   white -> gold -> pink.
5. Four-point glint: LockedToPart, Speed 0, Lifetime 0.3*, Size 0 -> 2 -> 0.5 -> 0*, Brightness 4*, ZOffset 3, a soft
   halo under it.
6. Orb or flower: the steady-glow trick, a soft radial texture, ZOffset 2.
7. Golden smoke curl: 4x4 OneShot curl flipbook, Lifetime 1*, Size 0.5 -> 2*, Transparency 0.3 -> 1, Drag 3*,
   rising 2*, LightEmission 0.4*.

## Aura tutorials
- MrWonderHow, "Glowing Sword Aura, No Scripts" (youtube.com/watch?v=lvCpPpkCmHk): tip, middle and guard attachments; a
  beam tip to guard with TextureSpeed; an arc flipbook on an invisible strip welded to the blade; rising wisps
  (VelocityParallel, small upward Acceleration); sparks in a box round the blade with frozen flipbooks; the glow as
  three stacked beams.
- Twist VFX, "Learn Roblox Aura VFX in 1 Hour" (youtube.com/watch?v=u2o-wHKDlpw, aura from 8:28): spirits (Speed 1-3,
  RotSpeed +-45, off-centre textures), a steady glow at ZOffset 2-4, dot "spec" textures, ground rings
  (VelocityPerpendicular, Speed 0.1), mirrored spiral beams with negative CurveSize; build in daylight.
- Twist VFX, "Slash VFX" (youtube.com/watch?v=zlKdwujvP2A): recipe 1, plus ground wind at ZOffset 7.
- MattASG, anime aura parts 1 and 2 (youtube.com/watch?v=rJeZrKWhSag, youtube.com/watch?v=pj6e4O_qfw8): per limb a 4x4
  flame flipbook, Loop 30 fps, Lifetime 1, Rotation +-180, Rate 80, ZOffset -1, a black/purple copy at -2; part 2 uses
  beams.
- Jam Pro, "VFX Aura Tutorial" (youtube.com/watch?v=qznzxuvtecA): a ground base (VelocityPerpendicular, Speed 0.01,
  LockedToPart, high RotSpeed), a pulsing ring, squashed VelocityParallel streaks.
- TerKungTH (youtube.com/watch?v=OxFo5lRNR0c, youtube.com/watch?v=nz_m1eTJuSs): chapters only (ground aura, star
  floor, smoke, specs, glitter flare, lightning).
- Zonito, "Astral Sword" (youtube.com/watch?v=OSMb35-vfAc): a timelapse; the sword aura from 0:00, scripting at 12:37.

## Sources
- devforum.roblox.com/t/1793748: spinning beams round a sword.
- devforum.roblox.com/t/4357705: emissive masks.
- devforum.roblox.com/t/2820890: EditableMesh UV scrolling.
- devforum.roblox.com/t/1113871: a crescent slash with Texture children.
- devforum.roblox.com/t/4005128: custom flipbook layouts.
- github.com/VuxSussy/EasyVFX: MIT runtime; ring and slash maths, performance rules.
- github.com/SyphoDev-yt/roblox-ai-skills (skills/roblox-vfx/SKILL.md): glow and smoke numbers (AI-made: treat with
  care).
- create.roblox.com/docs/reference/engine/classes/Beam.md: CurveSize, TextureSpeed, Brightness.
- create.roblox.com/docs/release-notes/release-notes-638: first-person effect hiding.

## What we take next
For the angel rifle: the coils as Beams on a spinning holder (recipe 3: a real ribbon, not particle dots), the star
glint as recipe 5 with a soft halo, the steady-glow trick on the halo, a golden smoke curl, white-hot cores over gold.
For swing weapons: recipes 1-2 (crescent slashes).
