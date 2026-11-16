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
`wrap-textures/round3/` (the ten after the second judging, in hand in the hall, place version 324),
`wrap-textures/round2/` (in the hall on the flat-UV guns, plus Blender renders),
`wrap-textures/galaxy-dots-before-after.jpg` (the owner's Galaxy note),
`wrap-textures/batch1-sheet.jpg` and `wrap-textures/judge1/` (the first round).

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
| 2 | 5.75 | the mapping problems gone (stretch measured: no face over 1.8 times, and only small corner facets); warm and saturated bases ran hot under the hall's lamps (Tiger, Hazard, Sakura, Camo); carbon read as chrome basketweave; holo a pastel toy; damascus a contour map; small checks blurred to grey at range; hex panels mirrored the tan walls | Tiger amber-brown with dark brown stripes, Hazard ochre, Sakura plum-charcoal with blossoms of four sizes, Camo olive drab, Galaxy near-black with the dots gathered in its clouds; Carbon near black, weave relief a third; Holo dark chrome with narrow prismatic bands (no stickers); Damascus dense half-and-half layers; Racing checks 3.1 cm; Hex panels satin |

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

## Lessons

- **Under the halls' lamps warm colours run hot** because the light eats blue: see "In-hand colour" above. Three
  rounds of Tiger went from traffic-cone orange to amber only once the coat's blue channel was raised.
- **High contrast stripes read as zebra on a thin blade**: Damascus' first layers went from near black to near white;
  the katana's blade turned into a barcode. Steel layers sit between 0.42 and 0.68 grey now.
- **Space is drawn as space** (owner, 16 Nov 2026, of the first Galaxy with its five-pointed stars: "get rid of the
  stars and just keep them like dots, I want it to look like an actual galaxy"). Galaxy is now a deep-sky picture:
  violet and blue star clouds packed with thousands of round dots (white, blue-white and warm, 0.5 to 2 mm), a few
  bright ones with a soft round glow, dark dust lanes, and two small spiral galaxies far off. Nebula's twinkles became
  round dots too. Stars as emblems (Holo's stickers, Arcade) keep their points. The dots are light added over the
  picture (`StarLight` in `wrap_textures.py`), each a Gaussian disc, so they stay round at any size.
- Petals and spots need to be about 1 to 1.5 cm on the gun to read in first person (40 to 60 px on a tile).
- A field's zero crossings (`|f| / |grad f|`) give single veins; `sin(k f)` gives nested contour lines that read as a
  map, not marble.
- The UV pass needs nothing from the gun builders: it works from the finished pieces, so a remodel keeps it.
