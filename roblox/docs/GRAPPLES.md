# Grapple skins (draft, 17 Nov 2026)

The owner, via the main session: "Let's get custom grapples again, kill effects and grapples should be gacha too!!"

The eight grapple skins are the web game's (`shared/cosmetics.js` `COSMETICS.grapple`): same ids, names and rarities. The
web hooks (`tools/blender/make_grapples.py`) were the base shapes. Here they are restyled for Roblox in the chunky clean
way: a few big round masses, flat colours, SmoothPlastic, Neon only where the glow is the point, one accent per head, and
nothing printed on them. A helper of the flair session made the look: the head models, the rope pictures and the client
code. The flair session owns the catalogue (`Flair.luau`), the equip screen, the loot hookup, the import and the save.

Preview sheet (Cycles, on a grey wall: the view from the end of your rope, then the side): `docs/grapples/heads-sheet.jpg`.

## The eight

| id | name | rarity | head (model asset) | rope |
|---|---|---|---|---|
| rope | Rope | free | iron grappling hook: dark crown on the wall, three fat prongs curling back, shank, four coils of brown rope lashing, the eye (113932793511930) | brown three-strand rope: `twist` tinted brown, 0.22 wide |
| chain | Chain | common | steel claw: dark palm disc, barrel with two dark bands, the eye, four jointed fingers biting in (109288193353572) | steel chain: `chain` (face-on rings, edge-on links), 0.36 wide |
| candy | Candy Cane | common | the crook of a candy cane, helical red stripes on cream (the stripes are geometry: two pieces) (110813247615068) | `candy` stripes, its own colours, 0.24 wide |
| plunger | Plunger | rare | muted red rubber cup on the wall, darker rim and collar, wooden handle back at you, a knob (82089190964520) | pale cotton cord: `twist` tinted cream, 0.18 wide |
| vine | Jungle Vine | rare | forked wooden hook, its knot on the wall, vine coils lashing the stick, two leaves (85954939445069) | `vine` (stem, a leaf each side), 0.32 at your hand to 0.75 at the hook |
| laser | Laser | epic | emitter: Neon cyan lens and ring on the wall, charcoal body, steel bands, three claws, three fins, a Neon tail (79595434254565) | `glow` tinted cyan, LightEmission 1, bands scroll along it, a soft pulse |
| sticky | Sticky Hand | epic | the vending-machine toy: one fused gummy hand, see-through green (Transparency 0.2), palm flat on the wall, fingers up, the cord at the wrist (90493771144036) | plain see-through green cord, thins as it stretches, wobbles |
| rainbow | Rainbow | legendary | a puffy five-point star, Neon; the game spins it and runs its colour through the rainbow (73499289204214) | `ribbon`, its colours flowing along it toward the star |

## The head frame (the contract)

The units are studs, on Roblox's own axes. **x** is right, **y** is up, **z** is back toward the player along the rope.
The **origin is the bite**: the point on the wall the rope hit. The head points down **-Z** into the wall and lies at
z >= 0. **Tail** is how far back from the bite the rope ties on, at (0, 0, Tail). The rope ends there, so it never pokes
through the head.

In the game the head's CFrame is `CFrame.lookAt(bite, bite + ropeDirection, up)`. The up vector is world up made square
to the rope. A rope pointing straight up or down uses its own heading instead. After that, each frame reuses the last
frame's up, so the head never suddenly rolls.

| id | length (z) | across (x by y) | tail |
|---|---|---|---|
| rope | 1.63 | 1.15 x 1.01 | 1.5 |
| chain | 1.34 | 0.92 x 0.92 | 1.28 |
| candy | 1.75 | 0.25 x 0.83 | 1.6 |
| plunger | 1.72 | 0.96 x 0.96 | 1.7 |
| vine | 1.44 | 1.02 x 1.26 | 1.44 |
| laser | 1.27 | 0.64 x 0.70 | 1.22 |
| sticky | 0.47 | 0.91 x 1.17 (the hand stands up from the bite) | 0.42 |
| rainbow | 0.38 | 1.20 x 1.15 | 0.33 |

## Files

- `tools/roblox/grapple_heads.py` (headless Blender 5.3): builds the eight heads into `grap_<id>.glb` and writes
  `grapples.json`, which has each head's box, tail, triangle count and each piece's centre. With `--preview` it also
  renders the preview shots. The glbs are turned for Roblox (`rbxglb.turn_for_roblox`) and land in the head frame at
  1 stud per file unit. Pieces are named `<id>_<node>__<look>`, where the look is `p<hex>` (SmoothPlastic), `n<hex>`
  (Neon) or `g<hex><alpha>` (see-through).
  Run: `blender -b --factory-startup -P tools/roblox/grapple_heads.py -- <out_dir> [--preview <dir>] [--only id,id]`.
  The build is deterministic: a rerun gives byte-identical glbs.
- `tools/roblox/grapple_ropes.py` (`py -E -P`): draws the six rope pictures, already alpha-bled.
- `roblox/assets/grapples/`: the uploaded glbs, `grapples.json` and `ropes/*.png`.
- `roblox/studio-tools/GrappleImport.luau`: builds `ReplicatedStorage.JankfireGrapples.<id>` from the uploads (see below).
  It is not in `studio.project.json` yet.
- `roblox/src/shared/GrappleLook.luau` (ReplicatedStorage.Jankfire): the looks, `dress`, `attach`, `preview`, `ready`.
- `roblox/src/client/GrappleSkins.client.luau` (StarterPlayerScripts.Jankfire): dresses every rope it sees.

## Rope pictures

The pictures run along the rope in x and across it in y. Each one tiles along the rope, using `TextureMode Wrap` with
`TextureLength` set to the studs one picture covers. A rope's Color multiplies its picture, so the grey pictures take
their colour from the look.

| picture | size | used by | Decal id | image id |
|---|---|---|---|---|
| twist | 128x32 | rope (brown), plunger (cream) | 73043694393156 | 128729089001963 |
| chain | 128x64 | chain | 81833412743656 | 107278956523683 |
| candy | 64x32 | candy | 118442793065578 | 127006434700551 |
| vine | 256x128 | vine | 85015828496852 | 110014939268762 |
| glow | 128x32 | laser | 94671855236150 | 81238473856499 |
| ribbon | 128x32 | rainbow | 117030152790720 | 117284904786521 |

All six were looked at full size before upload and all were Approved. None has text, digits, symbols or anything like a
code.

## How the code draws it

- **GrappleSkins** watches `workspace.Terrain.ChildAdded` for Beams and works out which skin each rope wears:
  - A Beam with an `Owner` attribute is the server's rope for that player, and wears that player's `Grapple` attribute,
    which FlairServer publishes.
  - If `Owner` is our own player, the rope is skipped, because HideOwnRope hides it and Move.client draws ours.
  - A Beam without `Owner` is our own rope and wears our own `Grapple` attribute.
  - A `Skin` attribute on the Beam overrides both. This is the test hook, for example `beam:SetAttribute("Skin", "laser")`;
    changing it re-dresses the rope.
  - Unknown ids wear `rope`.
  - A Beam already marked `GrappleLook` is left alone; the equip screen's preview Beam is one.
- **`GrappleLook.dress(beam, id)`** sets the rope's look and marks the Beam with `GrappleLook = id`.
- **`GrappleLook.attach(beam, id)`** clones the head from `JankfireGrapples` and falls back to the rope head if that
  skin's head is missing. The clone is anchored with no collision, query or touch, and is parented to a client-side
  folder `workspace.GrappleHeads`. It sits on the bite, which is `Attachment1`'s position when attach runs.
  - **While the head is on, the Beam's `Attachment1` is swapped for a `GrappleTie` attachment** in Terrain, which sits on
    the bite moved back by the tail. Cleanup puts the original attachment back if it still exists. The rope's own
    attachment is never moved, and nothing in Move, HookCheck, GrappleImpacts or Main reads `Attachment1`. The swap only
    changes what this client draws.
  - The cleanup is returned, and also runs by itself when the Beam or its anchor goes.
- **`GrappleLook.preview(a0, point, id)`** makes its own Attachment1 in Terrain and a dressed Beam, parents the Beam
  next to a0, adds the head, and returns a cleanup that removes all of it. FlairUI already calls it this way.
- **`GrappleLook.ready(id)`** is true for `rope`, and for any other skin once its head is in `JankfireGrapples`. It is
  the same rule as `Flair.grappleReady`.
- **One `RenderStepped`** is shared by every live rope and connected only while one exists. Each frame:
  - Heads follow the swing (`BulkMoveTo`, and only when the head moved or spins).
  - The tie follows the rope.
  - **rainbow**: the hue spectrum runs along the rope, one round every 40 studs, flowing toward the star. The star wears
    the colour at the head's end and spins at 1.7 rad/s about the rope.
  - **laser**: a soft 6 rad/s pulse in the beam's transparency and width, and the Neon `glow` pieces lighten toward
    white.
  - **sticky**: the cord thins as it stretches, `clamp(sqrt(15/len), 0.45, 1.4)`, with a 6 % wobble.

## Checked so far (17 Nov, Studio Edit, read-only)

- All eight uploads load with `InsertService:LoadAsset`. A dry run of GrappleImport's build put every piece within 0.000
  studs of its centre in the file, unrotated, with the names and look codes parsing. Sizes match the table above.
- The six Decals resolve to the image ids above.
- `GrappleLook.luau` and `GrappleSkins.client.luau` compile. Each was wrapped as an uncalled function in an unparented
  ModuleScript.
- Nothing has been tried in Play yet: the rope pictures on a live Beam, the head following a swing, and the animations.

## Putting it in (the flair session)

1. Build the heads: `G = require(<GrappleImport>:Clone())`, then `G.build(nil, true)` for a dry run (it reports each
   head's size and how far each piece sits from where the file says), then `G.build()` and `G.check()`.
2. Push `GrappleLook.luau` (ReplicatedStorage.Jankfire) and `GrappleSkins.client.luau` (StarterPlayerScripts.Jankfire).
   Compile-check both in Studio.
3. Play test: hook a wall, then set `Skin` on your rope Beam (in `workspace.Terrain`) to each id. Check the head sits on
   the wall pointing in, the rope ends at the tail, and the rainbow, laser and sticky animate.
4. Run the flicker check (`PolishBackup.ZFight`) on a head if anything shimmers. No two pieces share a face by design.

## Uncertain / to check in Play

- `TextureSpeed` direction on the laser: the bands may run toward your hand instead of the wall. If they do, flip the
  sign of `textureSpeed` in LOOKS.laser.
- The heads are not scaled up with distance (the web game scaled far hooks up to 3x). At 1.2 to 1.8 studs they should
  read at swing range; if they don't, add a stepped `ScaleTo` in `GrappleLook.attach`.
- Triangle counts: rope 7.1k, chain 9.4k, laser 5.5k, vine 5.0k, plunger 4.1k, candy 3.0k, sticky 2.6k, rainbow 1.8k.
  Roblox's mesh LOD cuts these at distance. If many ropes at once ever cost frames, cut the prong and finger sides in
  `grapple_heads.py` (`sides=14`).
- The sticky hand is see-through (0.2) SmoothPlastic with a little reflectance; see whether the owner wants it more solid.
- Fresh pictures can log "No asset content representation" for a while after upload; they still draw (VFX pipeline note).
- FlairUI's own fallback (used only if GrappleLook fails to load) parents a plain Beam to Terrain without `Owner`.
  GrappleSkins would then dress it as your own rope. That is harmless, but worth knowing.
- Anything that one day reads a rope Beam's `Attachment1` will get the `GrappleTie` while a head is on, not the bite.
  The bite is still the original attachment, and nothing reads it today.

## Installed and tested (17 Nov 2026, place v541)

Built by the flair session from the helper's uploads: `PolishBackup.GrappleImport` (now in `studio.project.json` and
`StudioExport`'s list) made `ReplicatedStorage.JankfireGrapples` with all eight. Photos:
`roblox/docs/grapples/grapples-in-game-sheet.jpg`.

- **Fixed at install:** the import set a PrimaryPart, and a model with a PrimaryPart pivots on that part, not on
  `WorldPivot`. Every head would have sat 0.2-0.9 studs off its bite (`G.check` caught it). The importer now sets the
  PrimaryPart's `PivotOffset` so `GetPivot()` is the bite; `G.check` reads 0.000 for all eight.
- **All eight latched on a wall** at once, as other players see them (server-style ropes with `Owner` and a `Skin`
  override): every head sits on the wall pointing in, ropes end at the tie, rainbow cycles, laser glows.
- **A real hook (E)** after equipping Laser through the equip screen (`Flair` remote "grapple"): your own rope is the
  laser, head and all. The server's copy for everyone else reads your `Grapple` attribute the same way.
- **The GRAPPLE tab** (FlairUI): eight tiles, the worn one marked, the picked one previewed on the copy of you
  through `GrappleLook.preview`.
- **Loot:** once the heads were in, `Flair.forSale("grapple")` lists the seven non-free skins, so the Duffel Bag and the
  shop carry them (the loot session's hook; checked by that session before the heads, gate confirmed).
- Not tested: two real players (Studio solo); the laser's band direction while swinging; heads at long range.
