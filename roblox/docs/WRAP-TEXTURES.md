# Wrap textures (16 November 2026)

The owner asked: "start working on the wrap textures? if you do little details like stars and whatnot, they should be
actual stars and not little squares like before".

Before this, a wrap recoloured **whole pieces** of a gun in a pattern (`alt`, `cycle`, `speck`, `bands`, `fade`), so
Galaxy's "stars" were whole pieces turned lilac and every patterned wrap read as blocks. Now a wrap is a **picture**:
a seamless texture drawn as real shapes (five-pointed stars, notched petals, tapered stripes, smooth camo blobs, a
woven carbon twill, crisp checks), laid on the gun through UVs, with roughness, metalness, relief and glow where the
wrap needs them. Wraps are cosmetics, so they carry colour; each is still meant to look deliberate and calm.

**Where it stands:** 79 of the 102 wraps are textures; the other 23 stay colour wraps (21 plain colours, plus QR Code
and Barcode, which may never be images). Every kit gun the owner picked carries the flat-projection UVs (`gun_uvs.py`,
live since place version 313, 242 `WrapUV` pieces) and `WrapUV` on every piece but the glow and glass ones. Photos:
`wrap-textures/in-hand-24.jpg` and `wrap-textures/round4/` (24 wraps in hand in the hall, place version 341), `wrap-textures/round3/` (the hardest ten after the second judging, place version 327),
`wrap-textures/round2/` (in the hall on the flat-UV guns, plus Blender renders),
`wrap-textures/galaxy-dots-before-after.jpg` (the owner's Galaxy note),
`wrap-textures/batch1-sheet.jpg` and `wrap-textures/judge1/` (the first round).

**Galaxy is all round dots on purpose; do not put star shapes back on it.** The owner asked for it on 16 Nov 2026:
"get rid of the stars and just keep them like dots, I want it to look like an actual galaxy". Every other wrap's
noticeable stars are real star shapes (see Lessons, "Stars").

## Rules for every wrap image (read first)

On 16 November 2026 at 09:39 UTC the owner's Roblox account was moderated and Studio was put out of the place. The
notice named the **QR Code** wrap's first image (asset 86852454924459, "Your image broke the rules", reason "Directing
Users Off-Platform"): random black and white modules with three finder squares and a smiley. It encoded nothing, but it
looked like a QR code. Every image this pipeline draws is uploaded to Roblox, so from now on:

- **No QR-like or barcode-like patterns**, nothing a scanner or a person could take for a code. "QR Code" and
  "Barcode" are plain colour wraps; their designs are unregistered and `wrap_upload.py` refuses them (`NEVER`).
- **No URLs, handles, @names, social or site logos.**
- **No readable text at all, words or numbers.** Writing is drawn as rounded grey bars (`ink_lines`), a jersey number
  as a blank panel, a stamp as an outline (Receipt, Spreadsheet, Corporate Memo, Organ Donor, ☺ CORP, Number Soup,
  Market Crash, Tokyo Night were redrawn this way).
- **No 69 / 420 / 666 jokes, nothing sexual or about drugs, no blood, gore, body parts or raw flesh** (Meat Suit is
  salami, the organ card a heart).
- Look at every map at full size before an upload batch, not just the contact sheet.

The images uploaded before these rules that break them were taken out of `assets.json` and the book, and are to be
archived on Roblox once the account is cleared: the list is in the shared notes (`wrap-uploads-16nov.md`).

## How it fits together

| step | what | where |
| --- | --- | --- |
| 1. draw | every wrap is a Python function that draws a 1024 px seamless tile: colour, plus height (made into a normal map), roughness, metalness and an emissive mask where it needs them. Shapes are signed distance fields with one pixel of anti-aliasing, stamped modulo the tile so nothing has a seam; noise and Voronoi are periodic over the tile. The dice of each wrap are seeded by its id, so a run always draws the same picture. | `tools/roblox/wrap_textures.py` (designs), `tools/roblox/wraplib.py` (the drawing kit) |
| 2. look | a Blender render of a wrap on a kit gun, from roughly the player's eye and from the left, with the export's own UVs | `tools/roblox/wrap_preview.py` |
| 3. UVs | the kit guns are unfolded at export, one scale for the whole gun (one tile = `TILE_M` = 0.25 m of gun; sidearms 1.25 times finer). The LEFT side of every piece (what first person sees) maps to one flat projection (u, v) = (z, y), so a pattern runs straight across body, grip, mag and stock, upright when seen from the left. Long pieces are unfolded round the gun from there, upright pieces (grip, mag) round their front and back; round pieces by angle. Each piece's one seam sits at its bottom-right (long pieces) or front-right (upright pieces) edge. Nothing is mirrored. | `tools/roblox/gun_uvs.py`, called by `export_weapons.py --kit` (which also exports tangents now, for the normal maps) |
| 4. upload | each map is an Open Cloud upload with `assetType: "Image"` (its id goes straight into a SurfaceAppearance; no Decal lookup). No monthly cap on images. Ids are kept by file hash, so a redrawn map uploads again and an unchanged one never does. A flat map (one roughness everywhere) is a tiny shared image. | `tools/roblox/wrap_upload.py` (`list`, `set`, `book`), ids in `roblox/assets/wraps/assets.json`, the specs in `roblox/assets/wraps/wraps.json` |
| 5. Studio | `ReplicatedStorage.JankfireWraps`: one `SurfaceAppearance` per textured wrap, named by wrap id, with attributes `Swatch` (its colour map, for the loadout chip) and `Finish` (`GLOWS` / `SHINY`). SurfaceAppearance maps can only be set in Edit, so the folder is built by running the generated book. | `roblox/studio-tools/WrapBook.luau` (run its whole text through `execute_luau` in Edit) |
| 6. wear | `WeaponModels.wrap(model, wrapId, mode)`: a piece in the mode's zone that carries the attribute `WrapUV` gets a clone of the wrap's SurfaceAppearance (named `WrapSA`); any other piece (a code model's boxes, a gun from before the unfold) still gets the old palette laid over it. Taking a wrap off destroys `WrapSA` and puts back the piece's own look. The client preloads the pictures of the wraps its player wears. | `roblox/src/shared/WeaponModels.luau` (the wraps section) |
| 7. pick | the loadout's wrap chip shows a 9 x 6 cm piece of the texture and its finish word | `roblox/src/client/LoadoutUI.client.luau` (`paintChip`, `finishWord`) |

`WrapUV` is set on every MeshPart of a kit template by `WeaponImport.kit` (and `kitShredder`) when the book row says
`uv = true`, which `export_weapons.py --kit` writes. So the first re-export and re-upload of the kit guns turns the
textures on, gun by gun; before that, kit guns keep the old colour wraps.

The three modes are unchanged: **normal** paints the `_wzA` pieces (the handle side), **reverse** the `_wzB` pieces
(the business end), **full** everything; `_wzN` trims keep their look unless the wrap is on full. Server, client and
preview paint the same pieces (the picture does not depend on any order).

**On a skin the accents are never painted (19 Nov 2026).** The owner: "my friend wanted the Seraph with the gold
accents with full wrap, but full send covers the entire gun even the accents. Can you fix the split?" On a gun wearing a
skin (the model's `Skin` attribute), `WeaponModels.wrap` takes the skin's accents out before anything else, in every
mode. No wrap picture, no other-half dark tone, no wrap Accent colour on its glow pieces, no hero-decal trim hiding.
`WeaponModels.isAccent(part, model)` says what an accent is:
- a trim (`_wzN`: gold rims and bands, emblems, crowns, lit lines, the shade shells over them);
- a glow or glass piece (Neon / Glass);
- a decoration by its node or slot even in a body zone (`ACCENT_NODES`: rwing, lwing, wing(s), halo, crown, bow, heart,
  gem; `ACCENT_SLOTS`: wing, feat(2), halo, lit, glow, cglow, wglow, shade, gem, heart). The Seraph's and the Ducky
  line's wings are `_wzA`;
- or the skin's own say: a part attribute `Accent` (true makes it one, false takes it out).

So on a skin, HANDLE paints its `_wzA` body, BARREL its `_wzB` body, WHOLE GUN both; the trims, wings and glow stay as
the skin was designed. A gold BODY stays wrappable (Golden Sniper, the Flintlock's barrel, the Cloudlock's stock: gold
in `_wzA`/`_wzB`). Plain kit guns keep the old rule. `fitImported` keeps each piece's node and slot as `WrapNode` /
`WrapSlot`, so renamed pieces (blade, needle, vent) still answer.

## Two-tone modes (16 Nov 2026)

The owner asked for "the dual tone wraps like normal reversed full". All three modes work with every textured wrap
on every kit gun. A check in Edit wrapped a clone of each of the 15 gun templates in each mode; per gun, normal /
reverse / full paint:

| gun | normal | reverse | full | gun | normal | reverse | full |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ar | 3 | 6 | 16 | revolver | 2 | 1 | 9 |
| smg | 3 | 6 | 15 | sawnoff | 2 | 3 | 18 |
| burst | 3 | 7 | 17 | pistol | 2 | 3 | 12 |
| lmg | 3 | 8 | 33 | marbles | 2 | 1 | 13 |
| dmr | 3 | 6 | 16 | redline | 2 | 6 | 15 |
| sniper | 1 | 8 | 19 | katana | 1 | 3 | 8 |
| lever | 3 | 4 | 18 | autoshot | 4 | 6 | 21 |
| shotgun | 2 | 4 | 12 | | | | |

Normal and reverse leave the other pieces in the gun's factory paint, so the gun comes out two-tone. In the loadout
the three mode chips (HANDLE, BUSINESS END, FULL SEND) sit at the top right of the wraps bar. Each now shows a small
two-block gun (stock end left, muzzle right) with the painted half lit. Hovering a chip tries that mode on the big
3D preview ("(trying it on)"), the way hovering a wrap chip does, and clicking wears it. Sheet:
`wrap-textures/modes-in-hand.jpg` (6 wraps x the 3 modes in hand, place version 355).

## Animated wraps

The web game animates 18 wraps in its shader: scrolling patterns, pulses running along traces, a glint sweeping over
gold, hue that shifts with the angle, flicker. On Roblox a SurfaceAppearance cannot scroll its texture, and its maps
can only be set in Edit. Stepping through pre-drawn frames would mean swapping whole SurfaceAppearances while playing,
so each swap reloads the textures: a hitch and a blink. What can change while playing, cheaply, is the glow
(`EmissiveStrength`, `EmissiveTint`) and the tint (`Color`). `client/WrapAnim.client.luau` animates those for 15 wraps,
smoothly and off one shared clock (the server's time), so a wrap pulses in step on every screen. Nothing flickers.

| wrap | on Roblox | on the web |
| --- | --- | --- |
| Neon Hex | glow breathes (2.6 s) | light runs along the grooves |
| Circuit Board | glow breathes (2.0 s) | pulses run along the traces |
| Kintsugi | a glint swells and fades on the gold (4.5 s) | a glint sweeps along the gold |
| CRT | glow breathes (2.2 s) | a bright bar rolls up the screen |
| Tokyo Night | a neon hum (1.6 s) | neon flicker |
| Market Crash (stonks) | glow breathes (2.0 s) | the chart scrolls |
| Vaporwave | glow breathes (5 s) | the grid scrolls |
| ☺ CORP | glow breathes (2.1 s) | the smileys pulse |
| Black Hole | glow breathes (4 s) | the disk swirls |
| Lava Lamp | glow breathes (6 s) | the blobs rise and merge |
| Glitch | glow drifts magenta to cyan (5 s) | bands jitter |
| Aurora | glow drifts green to violet (9 s) and breathes (5 s) | the curtains flow |
| Nebula | glow drifts pink to blue (10 s) and breathes (7 s) | the clouds drift |
| Opal | the fire's hue cycles (12 s) | the fire shifts as it turns |
| Holo | an iridescent tint cycles over the foil (8 s) | the hue sweeps with the angle |
| Missing Texture | glow hums (1.8 s) | (not animated on the web; added after the Rivals study, below) |
| Rainbow | a slow shimmer of tint across the stripes (10 s) | (not animated on the web; added after the Rivals study) |

Not animated on Roblox: Sakura and Koi (on the web their petals and fish drift by scrolling, which a
SurfaceAppearance cannot do), and Meat (its heartbeat; it is salami now). Stained Glass has a static glow on the web
too.

How it works: `WeaponModels.wrap` gives each worn picture the attribute `Wrap = <id>` and the tag `WrapSA`, on the
server (other players' guns, the racks) and on the client (the held gun, the loadout previews). The client script
finds them by the tag, works out each wrap's value once per step at 20 Hz, and writes it to that wrap's pieces. It
skips pieces more than 160 studs from the camera, checking twice a second. Cost in Play: the slowest step was
38 microseconds (the attribute `StepUs` on the script shows it live).

## A wrap is a palette (after the Rivals study, 16 Nov 2026)

The owner asked to study how Rivals does wraps ("look up skin wraps in rivals btw!"). Notes and pictures are in the
vault: `Research\Rivals wraps.md` and `Research\rivals-wraps-pictures\`. The strongest finding:

- **A Rivals wrap is a pattern plus a paired flat colour plus an accent.** The pattern goes on one zone of the gun
  (by default the furniture: stock and handguard). The other zone (the metal: receiver, barrel, magazine, grip) takes
  a dark tone of the same wrap, often the pattern itself tinted nearly black. An "Inverted" box swaps the zones. A
  skin's glowing parts take the wrap's accent colour, and lenses keep their own.
- Rarity climbs through material and motion, not more colours: Common is flat, Rare a pattern, Legendary a special
  surface or glow, and every top-tier wrap is animated. In 19 of 22 animated showcases the gun's overall brightness
  hardly moves; what moves is the glow or the pattern.
- Players judge wraps in first person by how well they can see: very bright wraps get "flashbang" complaints.

What changed here, the four that matter most for ours:

1. **The other half takes the wrap's own dark tone, not the factory paint.** Our HANDLE and BUSINESS END modes are
   Rivals' two zones (HANDLE = the pattern on the body panels and stock, BUSINESS END = the inverted look). Before,
   the unpainted half kept the gun's factory colours, so a Sakura SMG came out pink on teal. Now
   `WeaponModels.wrap` gives the other half (zone `b` on HANDLE, `a` on BUSINESS END) a clone of the same picture
   with its `Color` set to the wrap's `Second` tone: a grey multiplier that takes the pattern down to about 0.2
   luminance, never lighter than 0.45 of the picture. Its glow drops to 30%. A plain colour wrap gives that half
   its first colour at 35%. Trims (`_wzN`), glow and glass pieces keep their look. FULL SEND still covers
   everything on a plain gun; on a skin it covers the body only (see "On a skin the accents are never painted").
2. **Glow pieces take the wrap's accent.** A gun's Neon pieces (sight dots, lamps, vents) take the wrap's `Accent`:
   its brightest saturated colour, lifted to full brightness (cyan for Neon Hex, violet for Galaxy, pink for
   Sakura).
3. **The chip shows the palette.** Each picture chip in the loadout has a band of the wrap's `Dark` tone along its
   bottom quarter, so the chip says "this pattern with this dark".
4. **Every Legendary picture moves.** Missing Texture and Rainbow, the two still ones, joined the animator. Meat
   (no glow map) and Liquid Chrome (a plain colour wrap) stay still. Circuit and CRT are Epic and animate; that is
   fine.

`Second`, `Dark` and `Accent` are worked out from each wrap's colour map by `wrap_upload.py book` (`tones()`) and
set as attributes on the wrap's SurfaceAppearance by `WrapBook.luau`, so no new images were needed. Rarities were
not changed: the loot session prices and drops by them. Our Commons include patterned wraps where Rivals keeps
Commons flat, which is a call for the owner.

## Glow that blooms (16 Nov 2026)

The owner: "skins can have native glowing parts but skin wraps can apply the glow, like maybe the magma can glow
between the cracks?" A wrap's glow comes from its emissive map times `EmissiveStrength`. To bloom it has to pass the
zone's Bloom threshold: 1.9 in the hub and the training hall, 2.2 in training v2, 2.3 on the playground, 2.4 on
Rooftop v2 and v3 (`HubLook.luau`). The rule for the glow wraps:

- **Thin lines and cores are 1.0 in the mask** and `EmissiveStrength` is about 3, so they cross even 2.4 and bloom.
- **Halos, rims and broad glows stay at 0.35 or under** (about 1.1 at strength 3), so they glow without blooming and a
  whole gun never turns into a light ("flashbang", the Rivals players' complaint).

| wrap | what blooms | strength (was) |
| --- | --- | --- |
| Lava | the cracks' white-hot cores; the hot rim glows at 0.3; the crust is dark | 3.6 (2.2) |
| Neon Hex | the filament in each groove | 3.5 (2.0) |
| Circuit Board | the traces' centres (mask raised from 0.7 to 1.0) | 3.0 (1.1) |
| Kintsugi | the gold seams (mask raised from 0.35 to 1.0) | 3.0 (0.6) |
| Black Hole | the photon ring of its one hole (an unlit SurfaceGui at Brightness 3; "One black hole" below); the tile is 1.5 and doesn't bloom | 1.5 (1.6) |
| Nebula | the four-point twinkles; the gas (at most 0.6) glows under the threshold | 2.8 (1.3) |
| Tokyo Night | the neon signs' lines | 3.0 (1.6) |
| Market Crash | the falling line and the candles | 3.0 (1.3) |
| Glitch | the bright bands | 2.6 (1.2) |
| Arcade | the neon shapes | 2.8 (1.1) |

Broad glows stay under the threshold on purpose: CRT, Lava Lamp, Missing Texture, Vaporwave, Aurora, Opal, Stained
Glass, Holo. The glow follows the modes: the painted half glows full, and on HANDLE or BUSINESS END the dark half's
picture glows at 30% (about 1, no bloom). `WrapAnim` breathes the glow on top (Hex 0.7 to 1.25 of its strength, so
it blooms all through the breath in the hall).

In hand (place version 428, `wrap-textures/glow-sheet.jpg`, frames in `wrap-textures/glow/`): Lava, Neon Hex in the
training hall (Bloom 2.2) and Kintsugi, Nebula, Black Hole on Rooftop v3 (Bloom 2.4, daylight), with before frames.
A fresh judge: **7.1** on those five (Black Hole 8, Lava, Hex and Kintsugi 7, Nebula 6.5), against about 6 before
the pass. Lava blooms clearly (a soft orange halo past the cracks), Hex and Kintsugi mostly read brighter with a
faint halo near the eye, Nebula's twinkles barely bloom. Nothing blinding; Lava is the nearest to blown out near the
camera, so it is the one to turn down first if anyone finds it loud.

- Trap, seen twice: a freshly uploaded map can leave its SurfaceAppearance rendering as the bare part for a while,
  even once its `moderationResult` is Approved (the SMG showed its plain teal minutes after `circuit_emit` was
  uploaded; the sniper its factory paint 17 minutes after Ducky's maps; both fine when next looked at, Circuit
  half an hour on, Ducky two hours on). `ContentProvider:PreloadAsync` is no help: it reports Failure for working image ids too. Judge a new map
  in a later Play, not the one right after its upload.

## One black hole (16 Nov 2026)

The owner: "the black hole wrap should have one black hole and like an effect of the wrap being pulled towards it?"
A wrap's tile repeats every 25 cm of gun (`TILE_M`), so the old Black Hole tile, with two holes drawn in it, showed
six or more on a rifle. Now:

- **The tile** (`blackhole_color/emit.png`) has no hole: dark violet and ember dust drawn out along the gun, and star
  streaks stretched into arcs that all bend the same way, as if part of one great swirl. Its glow stays low
  (`EmissiveStrength` 1.5, nothing over 0.55 in the mask), so only the hole blooms.
- **The hole** is ONE picture per gun, laid by `WeaponModels.hole` as two SurfaceGuis on one face: of every piece
  that wears the picture (either half, so the hole sits in the same place on NORMAL, HANDLE, BUSINESS END and FULL),
  the face that looks to the gun's left (the side first person sees), the biggest, marked down when its piece is
  behind the `Grip` spot (the stock, out of first person's view) or well below it (the mag, at the screen's bottom
  edge). The hole is as big as that face is tall and slides to the face's back end, nearest the eye. On the rifle
  that is the receiver (0.34 studs tall), just above the hand. (First try, 16 Nov: painted pieces only and centred;
  on NORMAL the rifle's only painted piece with a big left face was the stock, so the hole sat out of view, and on
  FULL it sat at the receiver's far front, small and edge-on.) `blackhole_decal.png` is LIT (`LightInfluence` 1): the space round the hole wound into a spiral, star
  streaks winding in, longer and nearly round near the ring (the lensing look), the accretion disk's three hot arms,
  a faint Einstein ring; opaque in the middle, fading to nothing at its rim so the tile shows round it.
  `blackhole_hole.png` is UNLIT (`LightInfluence` 0, `Brightness` 3): the black core, the photon ring (brighter on the
  left, the side whose disk comes towards you, as real ones are) and a thin second image of it, and the disk's
  orange inner glow. Ring 1.0 x 3 crosses every Bloom threshold; the dim side and the orange glow stay under it.
- **It moves** (`client/WrapAnim`, every frame, off the shared clock): the spiral turns backwards at 10 degrees a
  second, which moves every arm inward (the arms are wound so the radius falls as the angle rises), the ring's
  `Brightness` breathes between 2.6 and 3.4, and a faint orange ripple shrinks from the rim into the ring every
  2.8 s.
- **The chip** in the loadout and shop is its own picture (`blackhole_chip.png`: the tile, the decal and the ring
  together), set as the wrap's `Swatch`.
- The mechanism is generic: any wrap whose SurfaceAppearance carries `Decal` (and `DecalGlow`) gets one. `WrapBook`
  sets them from the `decal`, `hole` and `swatch` images a design returns (`more_maps` in `wrap_textures.py`).
- In hand (place version 443, `wrap-textures/one-hole-sheet.jpg`, frames in `wrap-textures/one-hole/`): on the
  rifle the hole sits on the receiver just above the hand on NORMAL (the receiver is the dark half there) and FULL
  alike, big and readable from the eye, its ring blooming, the tile's streaks round it; Ducky on FULL and NORMAL.
- Traps: a SurfaceGui ignores its part's `LocalTransparencyModifier`, which is how the game hides your own world gun
  in first person and the viewmodel in third person or scoped, so WrapAnim switches each hole off while its piece
  is hidden (without it a lone hole floats where the gun is hidden). SurfaceGuis don't draw in a ViewportFrame, so
  a preview drawn in one shows the tile without the hole (the chip shows it).

## Ducky (VIP, 16 Nov 2026)

For the shop's VIP pack: Roster row `ducky`, legendary, `vip = true` (never in a Spray Can, the shop's rotation or a
bundle; `LootTable.vipOnly` and the shop read it), owned on every gun with VIP. The Ducky skin set's palette
(`tools/roblox/gun_sets_ducky.py`): rubber-duck yellow leaning lemon so the warm lamps don't push it to orange, the
bill orange only on bills, a soft white, a calm bath-water blue only on bubbles. A quiet staggered pattern of little
ducks in profile, moulded in the same yellow a shade lighter and raised a little (with the set's plump wing and
three round feather tips), and soap bubbles in the gaps whose rims and highlights glow softly (0.3 to 0.45 x 1.2,
well under Bloom). Satin. Its accent (the gun's glow pieces) is named in the design (`e0883a`, the bills' orange),
since the bills are too small a share of the tile to be picked automatically. In hand (v443) the halls' lamps make
its yellow read brighter than drawn, a toy-bright lemon; if it should be calmer, take the base a step darker and less
saturated in `ducky()` (and the ducks with it).

## Brighter, moving, raised (16 Nov 2026, evening)

The owner: "Can certain wraps have a brighter glow, some are animated right? I want cool effects and maybe even
height maps on some."

- **Radiant glow** (`RADIANT` comments in `wrap_textures.py`): the glow wraps' strength went up by about half. Lava
  5.5, Neon Hex 5.0, Circuit Board 4.5, Tokyo Night 4.5, Kintsugi 4.2, Market Crash 4.0, Arcade 4.0, Nebula 3.6,
  Glitch 3.4 (were 2.6 to 3.6). Only lines at 1.0 in the mask bloom; halos and rims stay under every threshold
  (Hex's halo 0.35 x 5 = 1.75). Black Hole's ring: `Brightness` 4, breathing 3.4 to 4.6, so it blooms all round at
  the top of the breath.
- **Effects** (`client/WrapAnim`, "WRAP EFFECTS"): a few slow particles off the painted half's four biggest picture
  pieces, from their surfaces, in the kinds and textures of Fx's skin effects (embers, four-point sparkles, round
  glowing dots, soap bubbles): Lava embers rising, Kintsugi gold glints, Nebula twinkles, Galaxy round dots (never
  star shapes there), Neon Hex cyan motes drifting up, Circuit green motes, Tokyo pink and blue motes, Ducky soap
  bubbles, Holo white glints. First person: they ride with the view, go quiet while you aim and stop while the gun is
  hidden; guns further than 160 studs don't emit. Black Hole: ten glowing motes wind down the spiral into the ring.
- **Animated** (already): 17 wraps breathe, glint, drift or shift hue (the table under "Animated wraps"), and Black
  Hole's spiral turns.
- **Relief** (`RELIEF` in `wrap_textures.py`): Roblox takes no real height map on a SurfaceAppearance, only a normal
  map, which fakes the relief with the light. Most designs raised their shapes by a step one pixel wide, a rim the
  mipmaps lose a metre from the eye; nine wraps' heights are now widened into bevels and deepened: Lava (crust
  plates domed up from the cracks), Neon Hex (bevelled panels), Circuit Board (traces and chips proud of the board),
  Kintsugi (the gold seams a raised bead), Bubble Wrap, Carbon Fiber, Wood, and two that had none, Seigaiha (the
  wave lines carved) and Sakura (the blossoms raised), from the picture's light parts (`lum`).
  Check a relief before uploading with `py tools/roblox/wrap_relief_preview.py <wraps dir> <out.png> <ids...>`
  (each normal map lit from the upper left over its colour map). A new normal map can leave the wrap rendering bare
  for a while after its upload (see the trap under "Glow that blooms").
- In hand (place version 465, `wrap-textures/radiant-sheet.jpg`, frames and the lit relief preview in
  `wrap-textures/radiant/`): Lava's cracks bloom wider than at 3.6, its plates read domed, and embers rise off the
  rifle (4 emitters, WrapAnim's step 13 us). Black Hole's ring blooms; the motes are small in a still. Ducky's
  bubbles weren't in the frame when it was taken. Near the eye an ember is a soft orange blob a few centimetres
  across; if that reads too big, halve the sizes for first person in `rebuild` (`fp`).

## Triangulum (VIP daily reward, 17 Nov 2026)

One of the VIP daily reward's exclusive trio (with the Triangulum Sniper skin and the Star Tricorne hat); brief and
concept sheet from the skin concepts session (notes folder: `triangulum-vip-brief.md`, `triangulum-vip-trio.jpg`), its
draft design folded into `wrap_textures.py` (`triangulum`, `tri_*` helpers). Roster row `triangulum`, legendary, and
NOT `vip = true`: the VIP pack hands out everything vip; `VipDailyData.EXCLUSIVE` is its daily-only mark, and the
containers, the shop and the pack skip it.

- **The tile:** a star chart of the night sky. Deep midnight with a slow, faint cloudiness, faint curved gold chart
  lines running along the gun and one dashed gold arc, about 800 round dot stars, and three invented constellation
  figures a tile (four-point stars joined by thin gold lines that stop short of each star, a thin gold ring round
  each figure's brightest star). The draft's upright chart lines are off (`TRI_UPRIGHT`): at first-person scale the
  two ways together read as a grid of cells; the lines along the gun alone read as a chart.
- **The mark:** the Triangulum constellation, a long thin triangle of three stars, ONCE per gun through
  `WeaponModels.hole`, apex toward the muzzle. Its own kind of hero decal (`DecalStyle` "mark"): still (no spin,
  ripple or motes); a 2:1 picture (`DecalAspect`) so it runs about 15 cm along a receiver a third of a stud tall; the
  lit decal is the gold lines over a soft midnight calm; the glow picture's three stars each get their own label
  (`DecalStars`, cut from the one image with `ImageRectOffset`), so WrapAnim breathes them one after another.
- **Not on the Triangulum Sniper:** the skin carries the mark already, so `hole` refuses a hero decal on a gun whose
  `Skin` is in `NO_HERO` (`sniper_triangulum`) or that has the attribute `NoHeroDecal`.
- Its accent (the gun's glow pieces) is starlight `ffe7a6`.
- In hand (place version 564, `wrap-textures/triangulum-sheet.jpg`, frames and the chip in `wrap-textures/triangulum/`):
  on the rifle the mark sits on the receiver above the hand, apex forward, its stars blooming; the midnight reads blue
  in the hall. A gun given the Skin `sniper_triangulum` got no mark (0 SurfaceGuis, 2 without it). The Triangulum
  Sniper skin wasn't in the place yet (only the wrap is under ReplicatedStorage), so it is untested on the real skin.
- **Clean shape (17 Nov, the skin concepts session from the v564 sheet):** the rifle's olive kit-mark slots and a rivet
  stood inside the triangle and broke its one clean read (they did the same over Black Hole's hole). Now `hole` hides
  the gun's small trims (`_wzN` pieces) that stand over the picture on that face while it shows (Transparency 1,
  remembered, so changing or taking off the wrap brings them back). Applies to every hero decal.

## Glow you can see (18 Nov 2026, place versions 906 and 921)

The owner: "can you add a glow to certain textures like a brighter glow? I can't see it when applying it really", and
then "can you make nebula twinkle and the lighter purple parts have a brighter glow".

**Why it was hard to see.** A wrap's glow is the colour map x the emissive mask x `EmissiveStrength` x `EmissiveTint`,
in linear light. Measured on the drawn maps (`scratchpad glow/analyze.py`: the 99th and 99.9th percentile of that, and
the share over 2.0), only nine of the 22 glow wraps had anything over a Bloom threshold: Lava, Arcade, Market Crash,
Kintsugi, Tokyo Night, Neon Hex, Datamosh and Circuit (just) and a few Nebula pixels. Galaxy peaked at 0.13, Aurora at
0.21, Holo 0.08, Stained Glass 0.08: well under a lit surface's own 0.3 to 1, so in hand they looked unlit. And a
picker (the loadout, the match loadout, the shop, crates) is a ViewportFrame: it draws a SurfaceAppearance's emissive
(checked in Edit, a rifle in Neon Hex at x0 / x1 / x2.5) but no Bloom and no particles, so there a glow was a slightly
lighter line at most.

**In the world (`wrap_textures.py`, GLOW 18 Nov notes; WrapBook):**

| wrap | strength (was) | what changed |
| --- | --- | --- |
| Galaxy | 6.5 (1.2) | the brighter stars bloom, the star clouds glow (4.5 at first, place version 906; it read quiet in hand under Rooftop v3's light, so 6.5 in 921) |
| Aurora | 5.0 (1.2) | the curtains glow; the lower edges near the threshold |
| Holo Foil | 4.0 (0.5) | the stars and sparkles bloom |
| Stained Glass | 6.0 (0.6) | the panes glow as if lit from behind |
| ☺ CORP | 5.0 (0.9) | the smileys' rims bloom |
| Nebula | 6.5 (3.6) | new mask: the pale purple gas glows full (about 10% of the tile over 1, 6% blooms in the hub) |
| Amethyst Geode | 4.5 (none) | its first mask: the crystal pockets lit from inside, the facet ridges bright |
| CRT, Missing Texture, Opal, Vaporwave, Lava Lamp | 2.4, 2.5, 2.0, 2.2, 1.6 (1.4, 0.8, 0.7, 1.1, 1.0) | broad glows: brighter, still under the threshold (no flashbang) |
| Black Hole, Triangulum | 3.0, 4.0 (1.5, 2.0) | the tiles' streaks and stars (the hole and the mark were already bright) |
| Circuit, Neon Hex, Kintsugi, Tokyo Night, Lava | 7.0, 6.0, 5.5, 5.5, 6.0 (4.5, 5.0, 4.2, 4.5, 5.5) | the line glows up a fifth to a half (Circuit's traces only just reached 2.0 before) |
| Arcade, Datamosh, Market Crash | 5.0 each (4.0, 3.4, 4.0) | the same |

Ducky stays 1.2 (soap bubbles, not a glow wrap). New masks: `geode_emit` 82262081498012, `nebula_emit`
89061714432334. No other map changed, so nothing else re-uploaded; the book was rebuilt from a full redraw (identical
before the change, byte for byte) and the 22 changed rows set in Studio directly.

**Nebula twinkles** (`client/WrapAnim`, FX `nebula`, kind `twinkle`): small four-point stars appear at random points on
the painted half's pieces and fade in, hold and fade out where they sit (no drift, `LockedToPart`), each living 1.3 to
3.1 s, about ten on a rifle at once, `Brightness` 3 so they bloom. Particles, so no per-frame property writes. The drawn
twinkles in the map keep their bloom, and the drift (pink to blue, 10 s) runs as before.

**In the pickers** (`client/WrapAnim`, "THE PICKERS"; no picker file changed: it finds the pictures by the `WrapSA`
tag, so the loadout, match loadout, shop and crates all get it):
- a picture inside a ViewportFrame glows 1.6x (`PREVIEW_GAIN`, before the animation reads it, so breathing wraps
  breathe round the raised level);
- a wrap whose book strength is at least 1.5 gets a soft halo behind the weapon in its `Accent` colour (the glow
  texture as an ImageLabel just behind the frame, fitted every frame to the weapon's projected box, so it follows the
  loadout's turning gun; opacity 0.38 to 0.6 by strength, breathing over 3 s). A frame whose parent lays out its
  children (a list or grid) gets the gain only;
- a glowing wrap with WRAP EFFECTS gets them drawn over the weapon as images (MOTES, at most 3 to 7 a frame): Nebula's
  twinkles, Lava's embers rising, Galaxy's dots, Kintsugi's and Holo's glints, Hex, Circuit and Tokyo's motes.
- `WrapAnim`'s attribute `PreviewGlowOff = true` turns the gain, halos and motes off (before / after photos).

**Settings:** GRAPHICS > OTHER PLAYERS' SKIN EFFECTS ("animated wraps and flames") now reaches the wraps: off, a gun in
another player's hands keeps its wrap still (no breathing, no particles); yours, the racks and the pickers move as ever.
The particle density setting already scales the wrap particles (SettingsApply scales every emitter's Rate).

**In hand** (solo Play, the Redline in first person in the training hall, each arena's look set on the client;
`wrap-textures/glow-18nov-sheet.jpg`, frames in `wrap-textures/glow-18nov/`):
- Galaxy: at 1.2 the stars were faint specks on black; at 4.5 brighter, still quiet under Rooftop v3's light (Bloom 2.4);
  at 6.5 the clouds read purple and lit and the stars bright. Kept 6.5.
- Nebula: the pale purple clouds glow strongly under the training hall's, Rooftop v3's and Arctic Cabin's lights (Bloom
  2.6, the highest threshold), and the twinkles come and go round the gun (two frames a moment apart). A twinkle can
  sit a few millimetres off the gun where a piece's box stands proud of its mesh (particles start on the part's box,
  not its mesh): it reads as a glint round the gun.
- Lava at 6.0 under the hub's light (Bloom 1.9, the lowest): bright cracks with a soft orange bloom, no white-out.
- The loadout picker, Nebula: before (no gain, no halo) the gun reads as a print; after, it glows with a soft violet
  halo behind it and twinkles over it. The Edit probes (`glow-18nov/vpf_probe1.jpg`, `vpf_probe2.jpg`) show eight more.
- Not checked in hand: Amethyst Geode. It rendered bare (the gun's factory paint) in the Edit check straight after its
  new mask went on (the known trap); judge it in a later Play.
- Trap: `open_cloud_invoke` timed out twice while another session's Play test was running; one call during my own
  lock went straight through.

## The mastery camos (18 Nov 2026)

The owner: "level up weapons to unlock gold, damascus, diamond and galaxy camo for their respective guns". The
weapon-mastery session builds the levels and the unlocks (per gun); these are the four pictures, a prestige ladder.
Ids `mastery_gold`, `mastery_damascus`, `mastery_diamond`, `mastery_galaxy` (Roster rows with `mastery = true`, all
legendary; the Roster rows and names are the weapon-mastery session's). They're never sold and never in a container,
bundle or gift: Roster moves every `mastery` wrap out of `Roster.wraps` into `Roster.masteryWraps` (still in
`wrapById`), so the Spray Cans and the shop's rotation never see them; grants come only through
`Loot.grant("mastery:<camo>@<gun>")` (Gold at gun level 10, Damascus 20, Diamond 30, Galaxy 40). A camo counts as
live once `ReplicatedStorage.JankfireWraps.<id>` exists.

| wrap | look | glow (strength) | moves (WrapAnim) |
| --- | --- | --- | --- |
| Mastery Gold | polished warm gold (full metal, gloss 0.2) in broad rich-to-pale swathes, a faint brushing along the gun | seven small four-point glints bloom (3.0, tint ffe2a0) | glint every 5.5 s; gold sparkles drift off it |
| Mastery Damascus | pattern-welded steel: many fine flowing layers folded into ripples and drops, bright and dark steel with a faint warm temper in the dark ones, etched deeper and duller | none | the temper shifts very faintly (iris, 14 s) |
| Mastery Diamond | faceted crystal: pale ice facets, each a cut face lit from the upper left, a faint prismatic tint, bright fine edges (metal 0.6, gloss 0.1) | edges glow under Bloom, six corner sparkles bloom (4.0) | the spectrum sweeps the facets (iris, 9 s); white twinkles where it sits |
| Mastery Galaxy | the top tier, a space camo: organic camo shapes cut a blue-black field, inside them violet and teal gas, round stars and a few four-point twinkles, a glowing lilac rim round each shape | gas, stars, twinkles and rims (5.5) | the gas drifts violet to teal and breathes; stars twinkle (as Nebula) |

In the pickers the glow ones (gold, diamond, galaxy) get the halo and their effects drawn over the gun
("Glow you can see"). Damascus and Mastery Galaxy skip the in-hand colour pass (HALL_TUNED). Maps: 11 uploads (all
Approved), ids in `assets.json`; checked full size (colour, normal, roughness, glow) for codes, stripes and text.
`bake_guard.py` is for Tripo bake atlases (it softens their packed strips and drops stray metal marks); these
seamless tiles have no strips and flat metal, so it had nothing to do, and running it would break the book's
checksum match.

- In hand (place version 981, `wrap-textures/mastery-sheet.jpg`: all four on the rifle, pistol and sniper in the
  training hall, and the loadout with the four Mastery chips in a row; frames in `wrap-textures/mastery/`). The
  diamond's spectrum sweep passes through ice blue and lavender (iris sat 0.1; lower it if it should stay whiter).
  A camo's maps take a second or two to load the first time it's worn, and the gun shows its factory paint until
  they arrive; in a test, re-equip or wait before a photo.

## Redrawing or adding a wrap

```bash
py tools/roblox/wrap_textures.py <upload dir>/wraps --sheet <id> [...]      # draw (and a contact sheet)
blender -b --factory-startup -P tools/roblox/wrap_preview.py -- <out> roblox/assets/weapons-kit/src/w_ar.glb <upload dir>/wraps full <id>
py tools/roblox/wrap_upload.py <upload dir>/wraps list                       # what needs uploading
#   upload each listed file (Open Cloud, assetType Image), then:
py tools/roblox/wrap_upload.py <upload dir>/wraps set <file> <id> [...]
py tools/roblox/wrap_upload.py <upload dir>/wraps book                       # writes WrapBook.luau
```

Then run `WrapBook.luau` in Studio (Edit) and save. The upload dir is the Studio-approved folder
`C:\Users\soup2\AppData\Local\Temp\claude\76cad3e90d004071\2f7beada-dc88-4870-9c10-a63ae3e562cc\scratchpad\rooftop-models\wraps`.
The PNGs are not kept in git (about 1.5 MB each); the script draws them again, identically.

A new wrap needs its row in `src/shared/Roster.luau` too (name, rarity, and the palette the old colour path still uses
on pieces without UVs).

## Judging (the hardest ten: Galaxy, Camo, Hex, Tiger, Sakura, Racing, Carbon, Hazard, Holo, Damascus)

Each round an independent judge (a subagent that sees only the photos and the brief) scores the ten in the training
hall, first and third person.

| round | average | what it found | what changed |
| --- | --- | --- | --- |
| 1 | 5.2 | checks skewed into diamonds, hazard stripes zig-zagged at chamfers, tiger stripes stretched into drips (all the first UV unfold, which used each point's own height); pale shards (glow and glass pieces took the old palette); hex glowed two lines a groove; carbon weave too big; damascus a barcode | UVs became flat projections per face family (no shear); `WeaponModels.wrap` leaves pieces without UVs alone on an unfolded gun; one hex filament on the cell boundary; carbon tows 4 mm; damascus in mid greys |
| 2 | 5.75 | the mapping problems gone (stretch measured: no face over 1.8 times, and only small corner facets); warm and saturated bases ran hot under the hall's lamps (Tiger, Hazard, Sakura, Camo); carbon read as chrome basketweave; holo a pastel toy; damascus a contour map; small checks blurred to grey at range; hex panels mirrored the tan walls | Tiger amber-brown with dark brown stripes, Hazard ochre, Sakura plum-charcoal with blossoms of four sizes, Camo olive drab, Galaxy near-black with the dots gathered in its clouds; Carbon near black, weave relief a third; Holo dark chrome with narrow prismatic bands; Damascus dense half-and-half layers; Racing checks 3.1 cm; Hex panels satin |
| 3 | 5.8 | Sakura 7.5 and Damascus 7 best; Holo 4 (thin lines read as crayon); Hazard's stripes change direction from face to face (each face family has its own projection); Racing's faded band reads as a second texture; stray light triangles on some corner bevels; Carbon now too dark in the hall | Tiger and Hazard corrected for the in-hand colour shift (below); Damascus contrast halved; Holo cool silver foil with a broad soft sheen and real sparkles and stars; Nebula's bright stars four-point twinkles again. Judging stopped here: three judges in a row moved by less than a point and reversed each other on Carbon and Damascus, so the open items are listed under "Next" |

After round 3, against a fixed checklist rather than more judging rounds:

- **Stripes keep one direction across folds.** Every face family unfolds with u along the gun (`gun_uvs.py`), so a
  band square to the gun folds onto the top, the grip and round the barrel without turning; a 45-degree band turns at
  every fold and reads as a sawtooth. Hazard's bands now run straight across the gun. The other striped wraps already
  ran along the gun (Jersey, Rainbow, Fade, Creamsicle) or across it (Tiger, Zebra), which fold cleanly too.
- **The corner-bevel "triangles" are the guns' shading, not the wraps**: a plain grey wrap on the AR shows the same
  light and dark corner facets (the kit's bevels are flat-shaded). Nothing to do in the textures or the UVs; smoothing
  those normals would be a gun model change.
- Racing is one even 3.1 cm grid of charcoal and off-white over the whole gun, no faded band.
- Carbon a touch lighter (it read as plain black in the hall).
- **Every wrap's colour map goes through the in-hand colour pass** (`hall_comp` in `wrap_textures.py`, below) except
  the nine tuned by hand in the hall (`HALL_TUNED`).

Then one fresh judge on a broad sample (24 wraps in hand, `wrap-textures/in-hand-24.jpg`, place version 331): average
5.9; Sakura and Damascus 8, Koi 7.5; lowest Stained Glass 3.5, Aurora 4, Checkered Flag, Holo and Marble 4.5. No text,
codes or logos. What changed after it:

- **Stained Glass**: thirteen big panes in ruby, emerald and sapphire (amber only where a pane's neighbours use all
  three), no two neighbours alike, in thick 3 mm lead.
- **Aurora**: two broad soft curtains hanging in rays along the gun, green at the hem turning violet, no specks.
- **Marble**: warm clouded stone, long soft veins that taper out, one thin gold vein, honed.
- **Holo**: one prismatic sweep (cyan, pink, gold) that changes only along the gun, so every fold matches; fewer,
  bigger sparkles and stars; half metal, so the warm room no longer muddies it.
- **Checkered Flag**: warm charcoal and cream instead of black and white (also further from anything code-like).
- **Pale blank slabs** on up-facing faces (Kintsugi, Galaxy, Nebula) were the hall's ceiling lights mirrored by glossy
  wraps: no non-metal wrap is glossier than roughness 0.36 now (`ROUGH_MIN`).
- Galaxy's and Nebula's dots start at 1.6 px (under 1 px they read as specks), fewer of them.
- Then the judge's smaller notes: **Leopard** smaller, denser rosettes (big ones smeared on sloped faces, bare faces
  between); **Seigaiha** twice the scale and softer contrast (it read as busy noise); **Wood** dark walnut with a
  finer grain (it read as cartoon pine); **Ugly Sweater** a red jumper with staggered snowflakes and one thin green
  border (the stacked bands of zigzags, snowflakes and trees read as stripes in hand). Place version 335.
- A fresh judge on the same 24 then: **6.0** (5.9 before). Judging stopped there: the score has plateaued.

**Code-look audit (16 Nov, after the judge flagged three).** Every wrap with bars, grids or blocks was looked at for
anything a person or a scanner could take for a QR code or barcode. Checkered Flag is now 6.25 cm checks, so a grip or
magazine shows one to three whole checks instead of irregular cut-up bits (live, place version 336). Zebra (stripes that
now bend, fork and end in points, no straight parallel bars) and Circuit Board (a few gold legs on its chips instead of
rows of white pins) are redrawn too; their first uploads were blocked by the permission check, and went up once the owner allowed them
(live, place version 341). The rest are clear: Plaid, Sweater, Arcade, Digital Camo, Glitch and CRT are coloured or organic, and Hazard
(even bands), Receipt, Sheet, Memo and Stonks (grey bars for writing) have no varying black-and-white bars.

## What holds the score near 6

Five rounds of judging moved the hardest ten from 5.2 to 5.8 and a broad 24 from 5.9 to 6.0, and judges reversed
each other on the same wrap (Leopard's rosettes too big, then too small; Hazard's stripes at 45 degrees, then across).
What I think caps it, most important first:

1. **One tiling picture over every piece.** On a full wrap the pattern runs over the receiver, barrel, grip, sights
   and trims alike, so the gun reads as wallpapered. Premium skins treat a gun as parts: the pattern on the big panels,
   coordinated solid colours on the barrel, grip and small parts, metal trims kept. The wrap zones already exist
   (`_wzA` / `_wzB` / `_wzN`), and normal mode leaves the trims alone, but the judging was all on full mode, the
   busiest case. The likeliest step up: give each wrap a trim colour (a dark tone from its own palette) for the `_wzN`
   pieces and barrels even on full, and judge on normal mode.
2. **The guns are low-poly and flat-shaded.** Every bevel and chamfer is its own lit facet, so a pattern is cut into
   many small differently lit patches; the "triangles" and "pale slabs" judges kept seeing are mostly this. Smooth
   normals on the bevels (a gun model change, `gun_models.py`) would help every wrap at once.
3. **Perspective reads as scale jumps.** In first person the muzzle is about a metre away and the stock a hand's
   width from the eye, so the same texel density looks tiny on the barrel and huge on the scope cap. Judges called it
   inconsistent scale on Hex, Koi, Lava and Plaid. The UVs are one scale; the fix is designs that read at both
   distances (large forms with finer detail inside), not smaller patterns.
4. **One test room, warm light.** Every photo is in the training hall, whose lamps take blue out and crush darks
   ("In-hand colour" below). The colour pass corrects for it, but the hall is the harshest light in the game; a
   neutral-lit zone (the hub or a match) would judge the same wraps higher and more fairly.
5. **The judging itself.** Crops at 640 x 400 turn fine detail (knit, carbon weave, star dust) into speckle, and
   judges disagree by about a point. A score of 6 is the noise floor of this method, not a measure of the last
   change.

## In-hand colour

Colours in hand are not the map's colours. In the training hall (warm lamps, the first-person gun's own fill light,
the hall's colour correction) a wrap colour comes out shifted by about **(+5, -12, -35)** of 255, measured on Tiger and
Hazard over three rounds (`a24e18` came out `d23d00`, `8a562c` came out `863604`, `af7743` came out `be6b1c`, `b08a1e`
came out `ae7a02`). Blue is what goes, so any warm colour with a low blue channel turns hot and saturated: amber goes
traffic-cone orange, ochre goes school-bus yellow, plum goes near black. So:

- Draw warm colours with their blue (and green) channel kept up: Tiger's coat is `9c6c4a`..`aa7a56` to land near
  amber `a8662e` in hand; Hazard's band is `b09c58` for a muted ochre.
- Full metal (`metal = 1`) reflects the room and about doubles a pattern's contrast in hand: Damascus' layers sit
  only 0.13 apart in the map.
- Glossy panels (roughness under about 0.3) mirror the warm walls at grazing angles and read as tan patches (Hex).
- Judge colours from a hall photo, never from Blender or the map: Blender's neutral light hides all of this.

As a model, fitted to every measured pair (Tiger, Hazard, Sakura, Carbon over three rounds), red and green come out
near **1.2 × map − 33** and blue near **1.05 × map − 35** (0..255): more contrast, blue pulled down, darks crushed.
`hall_comp` draws each wrap as intended and then moves its colour map 70% of the way to the inverse of that
(`HALL_K = 0.7`: not all the way, since other zones light the guns more neutrally). In a neutral light the maps look a
little lighter and cooler than intended; in hand they land near it.

## Lessons

- **Under the halls' lamps warm colours run hot** because the light eats blue: see "In-hand colour" above. Three
  rounds of Tiger went from traffic-cone orange to amber only once the coat's blue channel was raised.
- **High contrast stripes read as zebra on a thin blade**: Damascus' first layers went from near black to near white;
  the katana's blade turned into a barcode. Steel layers sit between 0.42 and 0.68 grey now.
- **Stars**: any star you notice at first-person distance is a real star shape, five points or a four-point
  sparkle, 1 to 1.5 cm across (the owner's first ask: "actual stars and not little squares"); faint background stars
  are round dots. **Galaxy alone is all dots**, the owner's own later call for that wrap (16 Nov 2026, of the first
  Galaxy with its five-pointed stars: "get rid of the stars and just keep them like dots, I want it to look like an
  actual galaxy"). Galaxy is a deep-sky picture: violet and blue star clouds packed with round dots (white,
  blue-white and warm, 0.5 to 2 mm), a few bright ones with a soft round glow, soft dust, and two small spiral
  galaxies far off. Nebula keeps its bright four-point twinkles over dots; Holo has sparkles and five-pointed stars
  on its foil; Arcade keeps its stars. The dots are light added over the picture (`StarLight` in
  `wrap_textures.py`), each a Gaussian disc, so they stay round at any size.
- Petals and spots need to be about 1 to 1.5 cm on the gun to read in first person (40 to 60 px on a tile).
- A field's zero crossings (`|f| / |grad f|`) give single veins; `sin(k f)` gives nested contour lines that read as a
  map, not marble.
- The UV pass needs nothing from the gun builders: it works from the finished pieces, so a remodel keeps it.
