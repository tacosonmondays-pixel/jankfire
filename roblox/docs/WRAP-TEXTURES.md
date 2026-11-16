# Wrap textures (16 November 2026)

The owner asked: "start working on the wrap textures? if you do little details like stars and whatnot, they should be
actual stars and not little squares like before".

Before this, a wrap recoloured **whole pieces** of a gun in a pattern (`alt`, `cycle`, `speck`, `bands`, `fade`), so
Galaxy's "stars" were whole pieces turned lilac and every patterned wrap read as blocks. Now a wrap is a **picture**:
a seamless texture drawn as real shapes (five-pointed stars, notched petals, tapered stripes, smooth camo blobs, a
woven carbon twill, crisp checks), laid on the gun through UVs, with roughness, metalness, relief and glow where the
wrap needs them. Wraps are cosmetics, so they carry colour; each is still meant to look deliberate and calm.

Photos: `wrap-textures/` (see "Judging" below).

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

## Lessons

- **Under the halls' lamps warm colours run hot**: Tiger's first orange (`c25c18`) read as traffic-cone orange in
  hand; it went a step darker and greyer (`a14a14`). Same rule as the gun paint (`roblox-weapon-paint`).
- **High contrast stripes read as zebra on a thin blade**: Damascus' first layers went from near black to near white;
  the katana's blade turned into a barcode. Steel layers sit between 0.42 and 0.68 grey now.
- Stars, petals and spots need to be about 1 to 1.5 cm on the gun to read in first person (40 to 60 px on a tile).
- A field's zero crossings (`|f| / |grad f|`) give single veins; `sin(k f)` gives nested contour lines that read as a
  map, not marble.
- The UV pass needs nothing from the gun builders: it works from the finished pieces, so a remodel keeps it.
