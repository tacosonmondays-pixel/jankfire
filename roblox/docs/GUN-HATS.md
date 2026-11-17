# Weapon hats on Roblox (16 November 2026)

The owner asked: "can you start workin on the wepaon hats modeling them?". JANKFIRE's web game has a **hat** cosmetic:
a small hat that sits on your gun, one per weapon (`shared/cosmetics.js`, `COSMETICS.hat`: Party Hat, Traffic Cone,
Cowboy Hat, Chef Hat, Propeller Cap, Googly Eyes, Top Hat, Halo, Crown, Tiny Duck, plus None). The Roblox port now has
all ten, as new models built for Roblox, a Hat slot in the loadout, and the hat on every view of the gun; and one of its
own, the VIP-only **Royal Duck** (below).

What each hat is and roughly where it sits come from the web game (`public/js/skins.js` `HAT_BUILD` and its "sit it
on top" rule; `tools/blender/make_gunhats.py`). The shapes and colours are our own, in the gun kit's style: a few big
rounded masses, two or three flat colours, SmoothPlastic, no pictures; Neon only for the halo, whose glow is the
point. The aim was a polished charm in the class of Roblox RIVALS, not a joke prop.

Pictures (`gun-hats/`): **`hats-sheet.jpg`** (the live hats on the Assault Rifle, first person above third person,
place version 319), `hats-blender.png` (the ten models on their own), `round6-first-person.jpg` (the live round-6 hats on the Assault Rifle from the eye, place
version 312), `round6-seats.jpg` (the Marble Shotgun and the Katana), `round5-third-person.jpg` (third person on a
dummy's rifle, round 5), `round6-blender.png`, `round4-first-person.jpg` (the ten round-4 hats on the Assault Rifle in the training hall,
from the eye, place version 300), `round4-scopes.jpg` (Second Opinion and the Sniper from the eye), `round1-first-person.jpg` and `round1-third-person.jpg` (all ten round-1 hats on the Assault
Rifle in the training hall, from the eye and on a dummy's rifle), `round1-on-guns.jpg` (round-1 hats on the other guns
from the eye, the aim-down-sights shot, the hub rack), `loadout-hats-tab.jpg` (the HATS tab, a hat being tried on, the
Shredder's preview), `round4-blender.png` (the round-4 hats on their own) and `round4-seats-side.png` (round-4 seats on
the nine guns that moved, from the side).

## In the game

| where | what happens | code |
|---|---|---|
| the loadout screen (L) | a **HATS** tab beside **WRAPS** over the bottom bar: twelve cards (None and the eleven hats, each turning slowly with its moving bits going, a line in its rarity's colour); hover to try one on, click to put it on. The big preview and the slot cards show the hat | `LoadoutUI.client.luau` (the "hats" block, `previewModel(id, hat)`) |
| the server | one hat per weapon, checked against the hat list, saved with the loadout (`hats` in the DataStore payload beside `wraps`), published as the player attribute `Hats` = `"ar=crown;katana=duck"`; a change goes on at once (your third-person gun, the Shredder) | `Loadout.luau` (op `"hat"`) |
| first person | the hat rides the gun piece under it (so it moves with a slide, a feed cover or the Half a Shotgun's barrels), **hides while you aim** (aim 0.3 or more, as in the web game) so it is never in the sight picture, and rebuilds when you change it | `Viewmodel.luau` (`VM.set`, `VM.update`) |
| third person | on every player's held gun, drawn 1.5 times the first-person size (`GunHats.THIRD`: at 1x it was a few pixels on someone else's gun) | `Fight.showWeapon` |
| the Shredder (a Tool) | on its Handle in the kit model's frame (the frame is a constant in `GunHats.luau`, measured from the web Tool; a Tool may carry its own as attributes `HatFrame` / `HatK`) | `GunHats.attachTool`, `Loadout.syncTools` |
| the hub armory | the display guns on the boards (`Rack_w_<id>`) wear **your own** hat for that weapon, on your screen only | `GunHatsClient.client.luau` |
| moving bits | the propeller spins, the halo bobs, the googly pupils rattle: client only, every frame, skipped past 150 studs | `GunHats.step` |

**A wrap never paints a hat.** A hat is a Model named `GunHat` inside the gun's model (so it moves, hides and goes away
with the gun), and every hat part carries the attributes `NoWrap = true` and `WrapTr = 1`; `WeaponModels.wrap` skips
them (the wrap textures session was asked to keep that). Checked: a FULL wrap on the Assault Rifle left every hat part's
colour and material as it was.

## How it is built

| what | where |
|---|---|
| the eleven hats (one function each, on `gunkit.Gun`), the VIP list and what moves | `tools/roblox/hat_models.py` |
| where each hat sits on each gun (z along the gun, size, turn, notes) | `tools/roblox/hat_spots.json` |
| the height under each spot, measured on the kit model with a ray; writes the book | `tools/roblox/hat_spots.py` |
| the book the game reads (generated: hats, rarities, file bounds, asset id, spots, moving bits) | `roblox/src/shared/GunHatData.luau` |
| the hats in the game (build, attach, Tool, displays, aim hide, moving bits) | `roblox/src/shared/GunHats.luau` |
| the upload, its bounds, the asset ids per round | `roblox/assets/hats/` (`hats_upload.glb`, `hats.json`, `assets.json`) |
| Studio's import (`H.load(id)`, `H.check()`) | `roblox/studio-tools/HatImport.luau` = `ServerStorage.PolishBackup.HatImport` |
| the templates | `ReplicatedStorage.JankfireHats.hat_<id>` (pivot = the hat's foot; one stud = 0.1 m), exported as `roblox/place/ReplicatedStorage/JankfireHats.rbxm` |
| preview cards without Studio (the ten on their own; one hat on every gun from the eye or the side) | `tools/roblox/hat_preview.py` |
| how deep each hat cuts into each gun and skin; a seat finder for the ones that fail | `tools/roblox/hat_clip.py`, `tools/roblox/hat_solve.py` |
| photo sheets | `tools/roblox/photo_grid.py` |

The hat frame is the weapon frame (metres, x right, y up, z back), the hat's foot on y = 0, its front toward the
muzzle. A hat is about 7 cm across, built at the size it wears on a rifle; `s` in a spot scales it.

To change a hat or add one:

```
blender -b --factory-startup -P tools/roblox/hat_preview.py -- <dir> sheet          (look first)
blender -b --factory-startup -P tools/roblox/hat_preview.py -- <dir> eye <hat>      (on every gun, from the eye)
blender -b --factory-startup -P tools/roblox/hat_models.py -- roblox/assets/hats
```

upload `roblox/assets/hats/hats_upload.glb` (Open Cloud, Model), put the id in `roblox/assets/hats/assets.json` as
`hats`, run `blender -b --factory-startup -P tools/roblox/hat_spots.py --` (rewrites `GunHatData.luau`), push it, and
in Studio (Edit): `require(game.ServerStorage.PolishBackup.HatImport:Clone()).load(<id>)` then `.check()`.

To move a hat on a gun: edit its line in `hat_spots.json`, run `hat_spots.py`, push `GunHatData.luau`. Check it from
the eye (`hat_preview.py ... eye <hat> <gun>`, then in game).

**After any gun remodel, run `hat_spots.py` again and push `GunHatData.luau`:** a hat sits on the surface measured on
the kit model, so a gun whose top moves leaves its hat floating or sunk. (A pending one: the guns session's version C,
`GUN-MODELS.md`.)

## Where each hat sits

Measured on the **live gun set** (`tools/roblox/gun_set.py`, the owner's A/B/C picks of 16 Nov; `hat_spots.py --set kit`
measures the older round-8 models instead). On top of the gun, on a flat surface clear of the sights and of anything
that moves past it: the Assault Rifle's top rail, the SMG's receiver, the Hat Trick's carry handle, the Belt Sander's
feed cover (it rides the cover), the flat top of Second Opinion's box optic (ahead of the optic it was tiny from the
eye; it hides while you aim anyway), the Sniper's scope between its turret and its bell (elsewhere the scope hid it
from the eye), the Yeehaw's receiver between its barrel rib and sight rib (the sight rib ran through the crown at
first), the Shotgun's slotted barrel shield (the rear sight crowded it on the receiver), the Lawn Mower's receiver
with the propeller's whole spin clear of the mower deck, Half a Shotgun's barrels back from the bead (it tips down
with them), Plan B's slide back from the front sight, the Revolver's top strap, the Redline's deck behind its gauge
(the bigger gauge of the picked model stands where the hat first was), the Marble Shotgun's **jar lid** (the hat steps
away while the reload's bag pours marbles in: `GunHats.HIDE_CLIPS`), the Katana's **pommel**, standing off the end
of the handle (`pitch = 90`: on the blade it floated beside the edge), and the Shredder's body behind its bell.
`gun-hats/seats-live-set.png` shows all sixteen from the side.

## Clipping (checked on the models, every hat on every gun and skin)

`tools/roblox/hat_clip.py` puts every hat on every gun (and every gun skin in `gun_set.SKINS`) exactly as the game does
(the foot on the gun's top, its sink, the saddle, the turn, the size; and the third-person size, 1.5x), sweeps the
moving bits (the propeller's whole turn, the halo's bob), and measures how deep the hat goes into the gun and the gun
into the hat (each piece split into its closed solids; inside = an odd number of crossings along two of three rays).
`tools/roblox/hat_solve.py` finds a seat where nothing clips for a gun or skin that fails (along its top round the
spot, then a saddle, then a smaller hat, the nearest first) and can write it into `hat_spots.json`.

What it found and what changed (16 Nov 2026, round 9, live in place version 380, hats asset 70496262106000):
- the Cowboy Hat's brim dipped at its front and back into most guns' tops (1-1.6 mm): its droop is a third of what it
  was;
- the Redline: behind the gauge the bigger hats (third person) cut 4-15 mm into the raised block and the rear sight:
  back on the block, on a 4 mm saddle, a size smaller (its gauge still shows from the eye);
- the Marble Shotgun: behind the jar the seat sat on the lock beside its hammer (3-8 mm): on the jar's lid again, and
  the hat steps away while the reload pours the marbles in (`GunHats.HIDE_CLIPS`);
- the Sniper: the foot cut 4 mm into the eyepiece's rise: a 13 mm saddle;
- the gun skins (27): each now has its own seat (`hat_solve.py`), the Neon katana's on top of its handle (its pommel
  has a cord); `GunHats` uses `SPOTS["<gun>@<skin>"]` when the built gun or the Shredder Tool carries `Skin`.
After: 700 hat-on-gun pairs (16 guns and 27 skins x 10 hats, first and third person, both counted in each pair's
worst): no hat body more than 1.4 mm into a gun, no gun more than 1.4 mm into a hat, feet 2 mm in by design (up to 4 mm
on one curved skin, the drill revolver). Moving parts: every part that moves under a hat carries it (Plan B's slide, the
Belt Sander's feed cover, Half a Shotgun's barrels); the bolts, charging handles and the Revolver's cylinder stay at
least a centimetre below their hat. The Marble Shotgun's lid (rebuilt with a hinge, 16 Nov) carries its hat: in
third person the lid flips open in the reload with the hat on it, and swept through the whole flip no hat touches the
gun (in first person the hat steps away for the pour).
Checked in Play (place version 380): the Marble Shotgun's cowboy hat on the lid under the crosshair and gone during
the reload; the Redline's top hat on the block with the gauge in view; the Sniper's crown on its saddle on the scope;
skinned builds (`WeaponModels.build(id, k, skin)`) seat their hat at the skin's own spot. `attachToolCopy` (the
loadout's Shredder preview) still uses the plain Shredder seat; the one Shredder skin (the Wood Chipper) has the same
seat. After any gun or skin remodel: `hat_spots.py`, then `hat_clip.py` (anything over 1.5 mm: `hat_solve.py`).

**After the guns' z-fight fix** (e83ff58, place version 401: faces of different looks pulled apart by up to 8 mm): six
seats measured 3-7 mm higher (the Burst, the cardboard AR, the Uzi and label SMGs, the cue and golden Snipers), and
five cut in by up to 6.6 mm where a trim or rail had moved up beside the foot. Re-seated with `hat_solve.py`: the
Assault Rifle's hat 1 cm forward on its rib, the toy AR 2 cm forward, the Neon katana 1 cm along its handle, the hot-rod
Redline 2 cm back, the Uzi on a 6 mm saddle. After: every hat on every gun and skin at most 1.1 mm in, the gun at most
0.4 mm into a hat. Live in place version 404. (A Studio raycast check of the seats reads the parts' collision shapes, not
their meshes: on the calculator pistol and the leaf LMG it shows the foot 5 mm "in" where the mesh check gives the
designed 2 mm; trust `hat_clip.py`.)

## The Royal Duck (VIP only, 16 Nov 2026, round 10)

The main session asked for a VIP-exclusive duck hat, "clearly a step above the common Tiny Duck"; the shop session
leads VIP. **`royalduck`, "Royal Duck"**: a polished gold duck (the Tiny Duck's masses a size smaller, so the two read
as one family) in a tiny crown (five points with ball tips, a wine velvet dome, tipped a little to one side), sitting on
a wine velvet cushion with gold piping and a gold ball at each corner, on the set's slate foot. The duck turns on the
cushion toward the side the player sees; the cushion stays square to the gun. Its gold is the only **Metal** in the set
(look code `m`: `HatImport` paints it `Enum.Material.Metal`); everything else is SmoothPlastic like the other hats.
`gun-hats/royal-duck.png` has the Blender close-ups.

- VIP only: `hat_models.VIP` -> its GunHatData row says `vip = true` (rarity `legendary`). `LootTable.vipOnly` reads
  that, so it is in no container; `Loot.owns` counts a VIP hat on every gun once owned. The shop's single rotation must
  skip it too (`Shop.singlesPool`, the shop session's). An unowned VIP hat in the HATS tab says it comes with VIP.
- Upload: round 10, asset 134178407944653 (all eleven hats; the ten old ones unchanged).
- Clipping: every hat on every gun and skin, now 16 guns and **52 skins** (the skin sets added 25: Seraph, Infernal,
  Ducky, Hex, Sakura, Nighttide, Cauldron, Candle ... in `gun_sets*.py`), first and third person: 1,496 pairs. The
  Royal Duck itself: at most 0.5 mm in, a gun at most 0.7 mm into it, feet at their 2 mm (3.6 mm on the Ducky LMG's
  round back). All hats: at most 1.1 mm in, 1.0 mm out; feet up to 4 mm on the drill revolver, 3.5 on the sniper scope
  (as before).
- The new skins first took their gun's seat; eight failed for every hat and were re-seated: the Seraph AR on the
  receiver rib ahead of its halo sight (the solver put the hat on top of the halo, 6 cm over the gun), the Infernal AR
  2 cm forward, the Ducky LMG 2 cm back, the Cauldron marble gun 2 cm back on its lid, the Candle revolver 3 cm forward, and the
  katana skins on their own pommel ends (the Infernal on a 1 cm saddle off its flared end).
- Two tool fixes found on the way. (1) `hat_clip.py` / `hat_solve.py` / `hat_preview.py` lifted a saddle straight up;
  the game lifts it along the hat's own up, which on a pommel seat (`pitch = 90`) is off the end. No live seat had both,
  so nothing in the game changed. (2) `hat_solve.py --write` dropped a pommel seat's fixed height (`y = 0`, the handle's
  axis), so `hat_spots.py` measured the handle's top instead: the Baguette, Bokken and Shirasaya hats stood about
  1.8 cm off-centre on their pommels since round 9. Both fixed; those three are back on the axis.
- `hat_clip.py --hat <id>` checks one hat (no report written).
- **After the guns' remodel batch** (16 Nov, ~22:00 UTC: the angel wings, Keytar v2, 24 remodelled skins, 10 cute
  concept skins `ar_cute_a..e` / `pistol_cute_a..e`, two Ducky skins dropped): 76 seats (16 guns, 60 skins). 14 failed;
  12 re-seated with `hat_solve.py`: the Pepper sawn-off 2 cm forward (its old seat measured down between the barrels,
  25 mm in), the toy AR 3 cm forward, the Pen DMR 6 cm back onto the scope's rear, the calculator pistol 3 cm back on a
  6 mm saddle, the lacquer AR on a 6 mm saddle, the drill revolver 3 cm back, the leaf and Ducky LMGs 1-2 cm back, the
  trimmer, umbrella shotgun and musket 1 cm, the Ducky katana on its own (wider) pommel end. After: 1,672 pairs, at most
  1.1 mm in, 1.0 mm out, feet at most 3.5 mm (checked again on the final models of place version 450). Live in place
  version 452; skinned builds in Studio seat their hat at the new spots.
- Live in place version 447. Checked there: the template's gold, crown, cushion and piping parts are Metal, the rest
  SmoothPlastic (`H.check()`: hats ok). In Edit, the Royal Duck on the Assault Rifle and the SMG (built like the held gun)
  reads as polished gold. In Play: `LootTable.vipOnly("hat", "royalduck")` is true and no container lists it; with the
  dev unlock the "hat" op put it on the AR and the SMG, and the hub racks showed it; on the held Redline it was on the
  first-person gun, the third-person gun and the held model, under the crosshair on the Redline's block. The owner's
  saved hats were put back after the test.

## Round 11: the ducks get a real bill (16 Nov 2026, place version 476)

The owner said the Ducky guns' beak (two thin orange rods) "looks nothing like a beak", and the guns session gave them a
wide flat rounded bill. The two duck hats had a smooth ellipsoid lump: not rods, but no mouth line and no lift, so both
(the Royal Duck and the Tiny Duck, one family) now share `duckbill()` in `hat_models.py`. It is a wide flat spatula, a
little wider toward its round tip, the tip turned up 2 mm, about 10 mm out of the head. The upper bill is flat underneath
and the lower one is narrower and stops short. A darker seam (a new `seam` slot: `3a2618` on the Royal Duck, `4a3024`
on the Tiny Duck) is sunk between them, so the mouth line reads from the side and the front. The bill colours are unchanged.
`gun-hats/royal-duck.png` has the new close-ups.

- Upload: round 11, asset 83292486542416, with all eleven hats; the other nine are unchanged. Each duck has one more
  piece: Tiny Duck 7, Royal Duck 10.
- Clipping: both ducks on all 76 seats, first and third person (304 pairs). The bill touches nothing. The hats' bounds
  grew under 1 mm. The only changes from the place version 452 report come from the guns session's slim-sights rework,
  which was still uncommitted (sniper scopes, the Cue sniper's felt, the Redline's gauge). The live seats were not touched.
- Studio: the seat data (only the two duck rows and the asset id) was pushed, `H.load(83292486542416)`, `H.check()`:
  hats ok. In Edit, the Royal Duck on the AR shows the flat bill with its mouth line and lifted tip. Saved as place
  version 476.

## Seats for the space-western pair and the Japanese concepts (17 Nov 2026, place version 481)

The guns session installed 17 skins in place version 478. Ten are live: Dust Drover and Star Drover on the revolver,
lever, sawn-off, sniper and katana. Seven are concepts, not sold: `ar_jp_a..c`, `dmr_jp_a`, `sawnoff_jp_a`,
`lever_jp_a` and `katana_jp_a`. Their builders are in-progress files, built only when named:
`JF_EXTRA=gun_sets_west,gun_sets_japan2` before `hat_spots.py`, `hat_clip.py`, `hat_solve.py` and `hat_preview.py`.
The builders gave the same bounds as the installed source glbs. The rest of the shared tree still had the guns
session's slim-sights rework, so only the 17 new rows went into `GunHatData`; every other seat stayed as it is live.

- First check, every hat on the gun's own seat (374 pairs): 11 passed. Six clipped: the three AR concepts on their
  lacquered body, the Japanese katana's gold trims, the Star lever's canopy, and the Japanese sawn-off's gold hinge.
  The two Drover katanas sat at 1 mm.
- `hat_solve.py` moved eight: the AR concepts 1-2 cm forward, the Japanese sawn-off 1 cm forward, the Star lever 1 cm
  back, and the three katanas 1-2 mm further off their pommel ends.
- After: at most 0.8 mm into the Star lever, no gun into any hat, feet at most 3.2 mm. The spyglass snipers keep the
  sniper's 13 mm saddle on their scope. Skinned builds in Studio wear the hat at the new seats (all 17).
- `hat_preview.py` needs its own line for a skin; use `--spots` with a copy of `hat_spots.json` that adds inherited lines.
- **The Ducky VIP guns rebuilt (v3, place version 480):** the Bubble Bath LMG, Wish Duck revolver and Ribbon Duck katana
  keep their keys. Build them with `JF_EXTRA=gun_sets_ducky_v3`. `hat_spots.py` now needs every in-progress set that has
  its own line in `hat_spots.json`: `JF_EXTRA=gun_sets_west,gun_sets_japan2,gun_sets_ducky_v3`. The LMG keeps its seat
  on the feed cover, now 1.6 cm higher on the rebuilt cover. The revolver keeps its seat. The katana's pommel end moved
  in to z 0.1315, so its hat would have floated 6 mm off it; it now stands at z 0.130 on a 3 mm riser. All three: no
  hat into a gun, no gun into a hat (place version 483).
- **After the slim sights (place version 484, 50 guns and skins with slimmer Rivals-style sights and scopes):** all 50
  match their installed glbs, and every seat was measured again (the default build plus
  `JF_EXTRA=gun_sets_west,gun_sets_japan2`). 13 rows changed, all on those guns:
  - Eight are only lower: burst, DMR and its Pen and Nighttide skins, label SMG, base sniper and its Infernal skin, and
    the Musket (5 to 16 mm, the slimmer sights and scopes).
  - Five failed the full check and were re-seated with `hat_solve.py`:
    - Redline: the hats sat 14 mm lower, into the tach housing. They now stand on top of the receiver 12 cm forward,
      just ahead of the gauge, without a saddle.
    - Bullpup: its tall sight is gone, so it moved 9 cm lower and 1 cm back.
    - Golden sniper: 5 cm back on its scope, off the crown, which moved onto the new turret.
    - Cue sniper: 1 cm back.
    - Infernal burst: 1 cm forward (its foot sank 4.3 mm).
  - The base sniper keeps its seat and 13 mm saddle on the slimmer scope, now 13 mm lower, so it no longer floats.
  - Full check: 93 seats, 2,046 pairs, at most 1.1 mm of hat in a gun, 1.0 mm of gun in a hat, feet at most 3.5 mm (the
    same limits as before). Built guns in Studio wear their hats at the 13 changed seats. Live in place version 487.

## Checked (16 November 2026, solo Play tests in Studio, round-1 to round-3 models)

- every hat on the Assault Rifle from the eye; one hat on each of the other guns from the eye: nothing over the
  crosshair or the sights; aiming down the sights hides the hat;
- third person: all ten on a training dummy's rifle (the same code as a player's held gun), and on the player's own
  Redline and Assault Rifle;
- the hat remote: a good hat goes on, an unknown one is refused ("that hat doesn't exist");
- **respawn:** killed and respawned, the hat was back on the first-person gun and the third-person gun;
- **rejoin:** the hats picked in one Play test were there in the next (DataStore, "saves to your account");
- **wrap change:** a FULL wrap on the Assault Rifle left the hat untouched;
- the loadout's HATS tab: the cards, hover to try on ("trying it on" and the preview), the Shredder's preview with
  its hat;
- the Shredder Tool: picked as primary, it came with its hat on the Handle (then the owner's pick was put back);
- the hub racks wear your hats;
- the console: nothing from the hats. One old `Asset type does not match` line (not ours), and once
  `ShredderClient:72: attempt to index nil with 'Position'` when the test gave the Shredder and took it back within a
  second (its script looks for `sh_hub` without waiting; the piece is there). Not seen otherwise; worth a look by
  whoever owns the Shredder.

## Judging

An independent judge looks at in-hall Play photos from the player's eye and in third person, against the design
principles (vault `Principles/Design principles.md`) and the Rivals-class bar.

| round | score | what it said | what changed |
|---|---|---|---|
| 1 (models r3) | 5 / 10 | readable and clean, but loud primaries (safety orange, lemon, pure Neon yellow), no shared look, uneven sizes (crown, duck, eyes half the others' weight), the googly eyes and the halo toy-jank; jammed or floating on six guns (Yeehaw, Second Opinion, Shotgun, Half a Shotgun, Lawn Mower, Marble Shotgun) and beside the Katana's blade. Nothing over the crosshair; the sight picture clean | round 4 |
| 2 (models r4, place v300) | 6 / 10 | the cowboy, top hat and chef hat premium; the set still no shared palette, the "gold" a bright yellow plastic at a different value on every hat, no common mount; the halo a flat yellow Neon sticker; the crown's points like cat ears; the eyes' tray and rims noise; the scoped guns' hats a speck or sunk into the optic. Nothing over the crosshair | round 5 |
| 3 (models r5, place v307) | 6.5 / 10 | top hat 8, cowboy and crown 7.5; the halo a donut on a cake pick (the stem), the eyes a gag sticker, the palette louder in game than in Blender; the Marble Shotgun's hat hidden by the jar. One more round should reach about 7.5 | round 6 |
| 4 (models r6, place v312) | 7 / 10 | cowboy and top hat 8; the set holds together; the eyes fixed; the halo an onion ring floating far over an empty foot; the palette tuned in Blender, not in the hall (the crown, cone, cap and duck brighter in game); the cap a desk bell; the Katana's hat a sliver at the screen's edge; the spinning and rattling bits always in view. One more round: about 7.6, then stop | round 7 |
| 5 (models r7, place v315) | 7.3 / 10 | cowboy 8.5, top hat and duck 8; nothing over the crosshair; from other players' view the halo closed into a solid pale disc and the eyes showed only their backs; the other eight at the point where model changes stop being noticed (on screen a hat is about 100 px wide): one targeted round on the halo still pays, then stop | round 8 (halo, eyes); then stopped |

**Round 4** (`hat_models.py` top of the hats): one calm palette for the whole set (mid values, saturation a third
lower), one shared trim on every hat in brushed gold (`GOLD`: the party hat's roll, the cone's collar, the cowboy and
top hat's buckles, the chef hat's line, the propeller's hub and post, the eyes' bezels, the crown itself), the top
hat slate-charcoal (never near-black), the chef hat warm off-white (never pure white), the propeller slate blue with
cream blades twice as thick; the **googly eyes rebuilt** (two eyes half again as big in a rounded grey brow, gold bezels,
facing up and back so the player and anyone beside them see the faces); the **halo rebuilt** (a flat oval band of
muted gold Neon, a fifth see-through, tipped 15 degrees toward the player); the **crown** five chunky rounded points and
three big flush stones on the side the player sees (the ball tips and pin gems smeared into a blob in third person);
the duck butter yellow and turned 35 degrees so the player sees its face; sizes evened (`SIZE`: the crown and duck up
about a third); the seats above.

**Round 5:** every colour a step darker and greyer than it should look (the hall's lamps lift warm colours and
saturate them: the round-4 brass read as yellow plastic); ONE brass (`GOLD` 8f7849) for every trim; **every hat on the
same small slate foot with a brass rim** (`FOOT`: the set's mount; the cone keeps its own square slate foot); the
halo a solid pale-gold ring, round and thick so it shades, inside a thin see-through Neon glow shell, on a brass stem
from its foot; the crown's points twice as tall with a ball on each tip, one stone front and back; the eyes plain white
with slate pupils on a slate pill-shaped foot (no tray, no rims); the chef's pleats shallower, the propeller cap a
darker band and wider blades, the top hat a lighter slate; sizes evened again (the duck and the chef a little smaller,
the crown larger). Seats: the scoped guns' hats on the rear of the optic or scope on a **saddle** (a slate puck,
`spot.saddle`, so a flat foot sits on a round tube), the Marble Shotgun's off the jar onto the barrel.

**Round 6** (live in place version 312): the halo floats again over its foot (no stem), half as thick, its glow
shell denser; the googly eyes set into a low grey felt cap (a hat, not a sticker); the party hat sage, the cone
terracotta on the set's round foot (no square base of its own), the duck ochre with real eyes, the crown's velvet a
step deeper; the Marble Shotgun's hat behind the jar on the barrel nearest the eye (ahead of the jar, the jar hid it).
Under the hall's lamps the duck still reads as a bright yellow and the crown's gold as a warm gold: a darker hex moves
them less than it should.

**Round 7** (live in place version 315): colours tuned against the in-game photos (the cone, cap and duck a fifth less
saturated, the crown in a darker brass and a deeper wine with smaller stones, and smaller overall); the halo a wide,
thin ring of muted-gold Neon (a fifth see-through) just over its foot; a real peak on the propeller cap; the party
hat's foot roll thinner; calmer motion (the propeller at 9 rad/s, the halo's bob halved, the pupils' rattle every
0.11 s); the Katana's hat hidden in first person (`GunHats.HIDE_FIRST_PERSON`: on the pommel it was a sliver under the
HUD); the Marble Shotgun's hat a little further back, clear of the jar's foot.

**Round 8** (live in place version 319, the last): the halo thinner (tube 2.5 mm on a 32 mm ring) with a bigger
opening, tipped 20 degrees toward the player, a dimmer Neon: from the side it now reads as a thin ring, not a disc; the
googly eyes splayed 30 degrees out to the sides and tipped less far back, each pupil rattling in its own eye's plane.
**Where it stopped, and why:** the fifth judge put the set at 7.3 and said further rounds on these models would not
be noticed; the rest of the gap to the Rivals bar is presentation (a shop or equip render, how a hat looks when it is
won), not geometry. The googly eyes are the weakest idea for other players (they look back at their owner, so from in
front others see their backs); a new concept would do more for it than another round.

## Not done / open

- **Live: round 11** (asset 83292486542416: the two ducks with a real bill), place version 476; seats on 16 guns and
  77 skins since place version 481. Round 10 (asset
  134178407944653: round 9's ten hats unchanged plus the VIP Royal Duck) went live in place version 447
  (16 Nov 2026, ~21:57 UTC), with seats on 16 guns and 52 skins; seats re-solved for the guns' remodel batch in place
  version 452 (16 guns, 60 skins). Round 9 (asset 70496262106000) went live in place
  version 380; its seats were re-measured after the guns' z-fight fix in version 404. Older hat uploads and the push
  models are no longer used.
- **After the guns' squash fix** (59fb8b4, place version 325: held guns were up to 41% squashed): the seats are measured
  on the gun files, so they were right; checked every gun's held model in Play (place version 326): each hat's foot
  sits 0 to 4 mm into the surface under it (its sink), none floats more than 2 mm. The hub racks' copies used the
  template's `GetBoundingBox()` like the old fit and are now measured from the parts too (`GunHats` `partsBox`):
  every rack hat within 0.02 studs of its gun.
- The Katana's hat stands on its pommel and is hidden in first person; it shows in third person, on the racks and in
  the loadout.
- Under the training hall's lamps warm colours still read brighter than their hex (the duck, the crown's gold). A
  darker hex moves them less than expected; judge colours from in-game photos, never from Blender.
- The hats are all free to pick (the Roblox port has no inventory or crates yet, the same as wraps).
- The Googly Eyes face the player who holds the gun (they look back at you); from in front, other players see their
  white backs.
