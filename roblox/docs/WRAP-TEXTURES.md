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
   everything.
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
