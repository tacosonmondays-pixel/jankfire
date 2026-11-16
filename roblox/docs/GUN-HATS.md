# Weapon hats on Roblox (16 November 2026)

The owner asked: "can you start workin on the wepaon hats modeling them?". JANKFIRE's web game has a **hat** cosmetic:
a small hat that sits on your gun, one per weapon (`shared/cosmetics.js`, `COSMETICS.hat`: Party Hat, Traffic Cone,
Cowboy Hat, Chef Hat, Propeller Cap, Googly Eyes, Top Hat, Halo, Crown, Tiny Duck, plus None). The Roblox port now has
all ten, as new models built for Roblox, a Hat slot in the loadout, and the hat on every view of the gun.

What each hat is and roughly where it sits come from the web game (`public/js/skins.js` `HAT_BUILD` and its "sit it
on top" rule; `tools/blender/make_gunhats.py`). The shapes and colours are our own, in the gun kit's style: a few big
rounded masses, two or three flat colours, SmoothPlastic, no pictures; Neon only for the halo, whose glow is the
point. The aim was a polished charm in the class of Roblox RIVALS, not a joke prop.

Pictures (`gun-hats/`): `round4-first-person.jpg` (the ten round-4 hats on the Assault Rifle in the training hall,
from the eye, place version 300), `round4-scopes.jpg` (Second Opinion and the Sniper from the eye), `round1-first-person.jpg` and `round1-third-person.jpg` (all ten round-1 hats on the Assault
Rifle in the training hall, from the eye and on a dummy's rifle), `round1-on-guns.jpg` (round-1 hats on the other guns
from the eye, the aim-down-sights shot, the hub rack), `loadout-hats-tab.jpg` (the HATS tab, a hat being tried on, the
Shredder's preview), `round4-blender.png` (the round-4 hats on their own) and `round4-seats-side.png` (round-4 seats on
the nine guns that moved, from the side).

## In the game

| where | what happens | code |
|---|---|---|
| the loadout screen (L) | a **HATS** tab beside **WRAPS** over the bottom bar: eleven cards (None and the ten hats, each turning slowly with its moving bits going, a line in its rarity's colour); hover to try one on, click to put it on. The big preview and the slot cards show the hat | `LoadoutUI.client.luau` (the "hats" block, `previewModel(id, hat)`) |
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
| the ten hats (one function each, on `gunkit.Gun`) and what moves | `tools/roblox/hat_models.py` |
| where each hat sits on each gun (z along the gun, size, turn, notes) | `tools/roblox/hat_spots.json` |
| the height under each spot, measured on the kit model with a ray; writes the book | `tools/roblox/hat_spots.py` |
| the book the game reads (generated: hats, rarities, file bounds, asset id, spots, moving bits) | `roblox/src/shared/GunHatData.luau` |
| the hats in the game (build, attach, Tool, displays, aim hide, moving bits) | `roblox/src/shared/GunHats.luau` |
| the upload, its bounds, the asset ids per round | `roblox/assets/hats/` (`hats_upload.glb`, `hats.json`, `assets.json`) |
| Studio's import (`H.load(id)`, `H.check()`) | `roblox/studio-tools/HatImport.luau` = `ServerStorage.PolishBackup.HatImport` |
| the templates | `ReplicatedStorage.JankfireHats.hat_<id>` (pivot = the hat's foot; one stud = 0.1 m), exported as `roblox/place/ReplicatedStorage/JankfireHats.rbxm` |
| preview cards without Studio (the ten on their own; one hat on every gun from the eye or the side) | `tools/roblox/hat_preview.py` |
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

## Not done / open

- Round 4 went live in place version 300 (16 Nov 2026, ~10:06 UTC) on the owner's picked guns (place version 298);
  round 5 (asset 103202603989161) follows. Older hat uploads and the push models are no longer used.
- The hats are all free to pick (the Roblox port has no inventory or crates yet, the same as wraps).
- The Googly Eyes face the player who holds the gun (they look back at you); from in front, other players see their
  white backs.
