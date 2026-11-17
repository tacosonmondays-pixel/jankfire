# The guns rebuilt for Roblox (15 and 16 November 2026)

On 15 November, after the guns were repainted, the owner wrote "the gun textures look a little messed up?" and then
"would it be easier to recreate them in roblox? you can look up other rivals weapons and skins!". On 16 November they
added "can you reference the rivals weapons when remodeling these please" and "im mostly discontent with the
snipers". So all sixteen weapons were remade as new models built for Roblox. Their shapes, colours and themes are
our own; Rivals' guns were studied for proportions and finish only. After round 5 the owner wrote "why do some guns
have like bullets attached on top?", that the Sniper's stock "isnt one piece", that Second Opinion had "an ugly
cross thingy", and "I think rivals weapons are a little blockier"; round 6 answered all four, round 7 made the guns
chunkier and gave back a signature to the guns that had lost theirs (below). After round 7: "not completly block some
rounded too look at rivals a bix of the two versions", so round 8 is a mix of round 5's rounder look and round 7's
blocks (live, place version 281). Then: "Makt he shapes cohesive reference an actual gun you know and referenbce
rivals heavily look at how they build their weapons, then put them side by side and ill pick each one": a third
version, **C**, each gun drawn from a real gun and built the way Rivals builds. The owner then picked per gun from
`gun-models/pick-1.jpg` to `-4.jpg` (below, "The picked set", `gun-models/final-set.jpg`). Then: "make sure the
magazine, stocks mount etc works for all of them and are connected pieces that look good" (`gun_check.py`, below). The
picked set is live (place version 298, then 313 with the wrap session's fixed UVs: flat projections, no shear),
every piece but the Neon and Glass ones marked `WrapUV`. In hand in the hall: `gun-models/picked-hall.jpg`.

**The reload check (16 Nov, after the owner's "make sure the magazine, stocks mount etc works for all of them").**
Every gun was reloaded (or fired, for the pump, bolt, lever, cylinder) in a Play test while a probe measured each
moving piece against the gun's body, every frame: how far it travelled and where it ended. Magazines (AR, SMG, Hat
Trick, Belt Sander, Second Opinion, Lawn Mower, Plan B), charging handles, the Belt Sander's feed cover, the Sniper's
bolt, the Yeehaw's lever and hammer, the Shotgun's pump, Plan B's slide and hammer, Half a Shotgun's break-open (barrels,
forend, both shells, hammers) all moved and came back to within 0.001 stud. The Redline's reload is its rev (the needle
swings into the red), the Marble Shotgun's is the hand pouring marbles into the jar; neither moves a gun piece, by
design. The Katana and the Shredder have no reload.

Two faults, fixed (place version 325):
- **Every held gun was fitted from the wrong box.** `WeaponModels.fitImported` read the template's size from
  `Model:GetBoundingBox()`, which on the kit models comes out larger than the parts (Plan B 41% too wide, the Yeehaw
  34%, the Redline 23%, the Hat Trick 14%, the Revolver 3.7% too tall ...). So every held gun was squashed across and
  shifted against its row's pivots. It now measures the parts themselves (`partsBox`): every template matches its
  file to within 0.08%.
- **The Revolver's cylinder** sat 8 mm off its axis after a shot (that same shift) and, being eight-sided, looked
  different after each 60-degree turn. Now six-sided with a dark groove on each face and twelve-sided rings: after two
  shots it had turned exactly 120 degrees and sat 0.0005 stud from where it belongs.

**No weapon number, name, mechanic or gimmick changed.** Every new model keeps its gun's muzzle, sight, port, grip
and fore spots, the names and pivots of the pieces that move, and the grip and handguard where the hands go, so the
hold, the aim line, the flash, the brass and every reload clip work unchanged.

Pictures: `gun-models/ar-sample.jpg` (the first sample, round 1), `gun-models/snipers-round2.jpg`,
`gun-models/pick-1.jpg` to `-4.jpg` (the owner's pick: A round 7, B round 8, C new, each held and from the side),
`gun-models/version-c.jpg` (all sixteen of version C from the side), `gun-models/round8-changes.jpg` (round 7 against
round 8 from the side), `gun-models/round8-hall.jpg` (round 8 in hand, with the fill light),
`gun-models/before-after-1.jpg` to `-4.jpg` (all sixteen in hand in the training hall: the old models left, round 8
right), `gun-models/round6-changes.jpg` (the owner's four notes, round 5 against round 6), `gun-models/round7-changes.jpg`
(round 6 against round 7), `gun-models/round7-hall.jpg`, `round6-hall.jpg` and `round5-hall.jpg` (every gun in hand, in
game), `gun-models/round5-side.jpg` (round 5 from the side),
`gun-models/skin-cardboard.jpg`. Style notes from studying Rivals: the vault, `Research/Rivals weapons and skins - style notes.md`.

## What changed

| | The web models (before) | The kit models (now) |
|---|---|---|
| Pieces | 10 to 59 parts a gun, 329 in all, many of them tiny (screws, stickers, cables) | 8 to 31 parts a gun, about 280 in all, each a big simple mass (a part per colour per moving piece; the Belt Sander's 12 belt rounds are one each) |
| Finish | Roblox `Metal`, `Plastic` and `Wood` (each adds its own grain), 42 pieces with printed pictures | `SmoothPlastic` and flat `Color` only; `Neon` on a sight dot, the vents and the lamps; `Glass` on the marble jar; no pictures, no `SurfaceAppearance` |
| Shapes | made for another renderer: thin parts, stickers, cables | a few big blocks with small crisp chamfers, straight sides, boxy stocks, upright slots, flat-faceted eight-sided barrels; thick barrels, ribbed magazines, square sights; no loose rounds on show |
| Colour | a calm paint over the old pieces | a charcoal base, ONE muted colour on the side panels and stock, a small accent where it says something |
| Triangles | 6,400 to 12,300 a gun | about 500 to 2,800 a gun |

Each gun keeps its own signature: the Belt Sander's sanding belt and its belt of links (they still count the ammo
down), the Marble Shotgun's jar of marbles on a blunderbuss, the Redline's rev-counter (its needle still follows
your HP and its vents still glow), the Lawn Mower's mower deck, drum magazine and pull start, the Hat Trick's carry
handle, Second Opinion's box optic, the Yeehaw's lever loop and stars, the Revolver's cylinder, Half a Shotgun's sawn
ends, the Shredder's hopper and teeth. Round 6 took off what the owner did not want: the Hat Trick's three rounds,
the Shotgun's shell saddle, the Belt Sander's brass rounds on top, Second Opinion's cross. Round 7 built a signature
back into those guns: three blue squares on the Hat Trick's carry handle (its three-round burst), a second small optic
beside Second Opinion's first (its name), a boxy slotted shield over the Shotgun's barrel (so it no longer reads like
the Yeehaw).

## The picked set (the owner's choice, 16 November 2026)

| Gun | Version | The owner's words |
|---|---|---|
| Assault Rifle | C (AK-12) | C |
| SMG | C (MP5) | C |
| Hat Trick | B | B |
| Belt Sander | C (M249) | C |
| Second Opinion | C (SVD + its second optic) | C |
| Sniper | A, the scope raised clear of the gun on its rings, a new one-piece stock (sloped underline, comb low under the eyepiece) | "A (without scope inside gun, fix stock)" |
| Yeehaw | C (Winchester 1873), the star bigger | "C (increase star size)" |
| Shotgun | A | A |
| Lawn Mower | C (AA-12: the top rail and carry handle) | "you pick prob one with top rail" |
| Half a Shotgun | C (coach gun), one trigger | "C but remove one trigger since it has 2" |
| Plan B | C (M1911) | C |
| Revolver | A's barrel, frame, cylinder, hammer and sights; C's rounded frame back, round guard, trigger and wood target grips | "I like how the held looks for volvie A but I like the handle of trigger area of C" |
| Redline | A, the trigger area closed (a post from the guard into the receiver), the tachometer 15% bigger round the same pivot | "A ... can you inclose the trigger area, and increase the guage a tinier bit bigger" |
| Marble Shotgun | C (blunderbuss), the flintlock's cock compact and low over the wrist | C, and "fix ... the little thing that sticks out above the handle" (read as this gun's cock) |
| Katana | C's blade (curve, temper line, bright tip) on B's handle | "blade look of C handle of B" |
| Shredder | C | "C love the shredder" |

Carl's Cardboard is rebuilt on the C rifle (a paper-tube barrel with tape bands, card window and tent sights, tape round
the receiver, corrugated butt, flaps).

**Is every gun one connected thing?** `tools/roblox/gun_check.py` builds the live set and finds, for every solid of
every gun, whether it touches or sinks into another (a gap over 1.5 mm counts as loose), and whether the nodes the game
moves are all there. Its first run found two: Second Opinion's whole front (handguard, barrel, brake) stood 2 mm off
the receiver and its trigger 3 mm under it; the Hat Trick's grip 1.7 mm under the body. Both fixed; all sixteen now come
out as one piece each with every moving node present. What it cannot judge: how a join looks, and whether a moving
part clears the rest in motion (that is the reload test in game).

**How the picks are built:** `tools/roblox/gun_set.py` is the live set (`PICK` and `BUILD`, plus the mixed builders).
Each gun is built in its version's look with `gunkit.use_style('A' | 'B' | 'C')` (`gunkit.STYLES`: A = round 7's
switches, B = round 8's, C = Rivals' way), so A and B guns come out exactly as they were and C guns as in version C;
the mixed guns switch looks part by part. `gun_models.py` still holds the A/B builders, `gun_models_c*.py` the C ones.

## How it is built

| what | where |
|---|---|
| the kit: chamfered prisms, boxes, eight-sided barrels, rings, windows, panels, rivets, ribs | `tools/roblox/gunkit.py` |
| **the live set: which version each gun uses, the mixed builders, the skin** | `tools/roblox/gun_set.py` |
| the A/B builders (the frame and the rules are at the top of the file) and the old skin | `tools/roblox/gun_models.py` |
| version C: its look and shared pieces, its builders | `tools/roblox/gunkit_c.py`, `tools/roblox/gun_models_c.py` and `_c1` to `_c3` |
| preview cards without Studio (three-quarter, in hand, side view with the spots marked, the old model in hand) | `tools/roblox/gun_preview.py` |
| the models' source files (weapon frame, metres) | `roblox/assets/weapons-kit/src/w_*.glb` |
| the upload files (turned for Roblox, look in the piece names), the asset ids, the report | `roblox/assets/weapons-kit/` |
| the book Studio reads (asset ids, file bounds, each piece's colour) | `roblox/studio-tools/WeaponKit.luau` = `ServerStorage.PolishBackup.WeaponKit` (generated) |

To change a gun: edit its builder (find it through `gun_set.py`), then

```
blender -b --factory-startup -P tools/roblox/gun_preview.py -- <dir> --set live <id>                    (look first)
blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src <id>
blender -b --factory-startup -P tools/roblox/export_weapons.py -- roblox/assets/weapons-kit --kit roblox/assets/weapons-kit/src/w_<id>.glb
```

upload the `.glb` (Open Cloud, Model), put its id in `roblox/assets/weapons-kit/assets.json`, run the export line
once more with no file to rewrite the book, push the book (`node tools/roblox/push.mjs`), and in Studio (Edit):
`W.kit({ "<id>" })` then `W.models()`.

**Pieces are named `<node>_wz<zone>__<slot>`.** The node is what the piece is or what moves (`body`, `barrel`, `mag`,
`grip`, `stock`, `sight`, `charge`, `pump`, `bolt`, `slide`, `cylinder`, `hinge`, `needle`, `redline_vents`,
`kat_blade`, `lmg_heat`, `belt_00`..`belt_11` ...). The zone tells wraps which part they paint (A the big shell, B the
metal, N trims). The slot is the colour it wears from the gun's small palette (`body` = its one colour, `frame`
charcoal, `dark` near-black, plus `steel`, `wood`, `brass`, `glow`, `glass`, `accent` ...). A skin recolours slots and
swaps nodes by these names.

## The models are a switch: `kit` (the default) or `web`

Both sets live in `ServerStorage.PolishBackup.WeaponSets.{kit,web}` (the Shredder's Tool too). In Studio (Edit):

```lua
local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())
W.models()          -- the kit models in ReplicatedStorage.JankfireWeapons and JankfireTools.Shredder
W.models("web")     -- the web models back (their calm paint as before; W.use / W.shredder still repaint them)
W.models("kit", { "ar" })   -- one gun only
```

`JankfireWeapons` says which set is in with its `Models` attribute. A kit model's box is not the web model's, so every
template carries its own file bounds (`FileLo`, `FileHi`); `WeaponModels.build` reads them before the gun's row.

**Wraps** work on the kit models: every wrap (102) in every mode (3) went on and came off all seventeen kit models
(sixteen guns and the skin) leaving each piece exactly as it was.

## Skins

A skin is a kit model of its own, `w_<id>@<skin>`: the base gun with its slots recoloured and some nodes swapped. It
keeps the grip, handguard, muzzle, sight line and moving nodes, so it needs nothing from the game but the model.
`W.skin("ar", "cardboard")` puts one on as the live template (for everyone: a look test); `W.skin("ar")` takes it off.

**The proof: Carl's Cardboard** for the Assault Rifle (`ar@cardboard`). The rifle cut from parcel boxes, after the
game's own Cardboard Carl: grey-brown board, a paper-tube barrel, folded-card sights, pale parcel tape over the
joins, corrugated cut ends, pale cut edges along the top, a flap standing off the receiver and two on the stock.
Nothing printed. Picture: `gun-models/skin-cardboard.jpg`.

Five skin ideas of our own (none is a Rivals theme):

1. **Carl's Cardboard** (built): parcel boxes, tape, a paper tube.
2. **Night Shift**: the warehouse crew's kit. Matte black, one amber hazard band, the front sight a glowing work lamp,
   the magazine a battery pack with a charge light.
3. **Bowling Night**: from the hub's bowling centre. Lane-wood body with the arrow marks as inset panels, a pin-white
   stock with two red neck stripes, the magazine a ball-return hood.
4. **Glazed**: a ceramic set. Off-white glazed body with cobalt brush bands as inset panels, the barrel a vase neck,
   the grip a teapot handle.
5. **Smog Runner**: from the smog under the map. Weathered grey-green, the muzzle a respirator filter, an amber visor
   glass for the sight, hose loops in place of the sling.

## The web game's skins on the live guns (16 November 2026, place version 379)

The 26 skins the web game has for the sixteen live weapons (`shared/cosmetics.js`, `COSMETICS.model` and `SKINS_2`)
are kit models now, one whole other body each, built in look C. The crate gives them (the loot session's
`LootTable.SKINS`: names and rarities) and the loadout's SKINS tab puts them on.

| Weapon | Skins |
|---|---|
| Assault Rifle | Toy Blaster, Bullpup, Keytar |
| SMG | Pocket Uzi, Label Maker |
| Burst | Take A Number |
| LMG | Leaf Shredder |
| DMR | Fountain Pen |
| Auto Shotgun | Weed Whacker |
| Sniper | Musket, Pool Cue, Golden (the web game's Sniper Royalty prize: built, not in the crate) |
| Lever Rifle | Cap Gun |
| Shotgun | Double Barrel, Brolly |
| Half a Shotgun | Pepper Mills |
| Marble Shotgun | Gumball Machine |
| Redline | Hot Rod |
| Pistol | Calculator |
| Revolver | Flintlock, Cordless Drill |
| Katana | Bokken, Shirasaya, Baguette Katana, Neon Tube |
| Shredder | Wood Chipper |

**The contract** (top of `tools/roblox/gunskin_kit.py`): a skin keeps its gun's spots (muzzle, sight, port, grip,
fore: copied), the names and places of the nodes the game moves, about its size (within ~10%), and wrap zones in its
piece names. `gun_check.py -- skins` proves each is one connected piece with its moving nodes. Left out on purpose,
because the object has no such part: the Musket's bolt, the Flintlock's cylinder and the Cordless Drill's hammer
(nothing moves there). No text, numbers, logos or code-like patterns anywhere: the Calculator's keys are plain
blocks, the Label Maker's tape is blank.

**Building**: the builders are `gun_skins_1.py` .. `gun_skins_3.py`; `gun_set.py` collects them into `SKINS`
(`"<weapon>@<skin id>"`, file `w_<weapon>@<skin id>`). They go through the same export, upload and `WeaponKit.luau`
as the guns.

**In Studio**: `W.kit()` brings them in with the guns, then `W.skins()` copies every `w_<weapon>@<skin id>` from
`WeaponSets.kit` to `ReplicatedStorage.JankfireSkins` as `<skin id>` with attribute `Weapon`. The Wood Chipper is a
Tool (the Shredder is one): `JankfireTools["Shredder@shredder_chipper"]`, plus a marker model in `JankfireSkins`.
Carl's Cardboard stays a look test (not in the crate).

**In the game**:
- `GunSkins.luau` (shared): `skinFor(player, weapon)` reads the player's `Skins` attribute ("ar=ar_toy;...").
- `WeaponModels.build(id, k, skin)` draws the skin's template instead of the gun's and marks the model `Skin`. Hats
  key on `weapon@skin`.
- Viewmodel (first person) and Fight (third person, players only) pass the skin. A new skin rebuilds the held gun.
- Loadout (server) keeps `skins` in the save, publishes `Skins`, and takes the remote op `("skin", weapon, id)` or
  `"default"`. It only equips a skin the player owns: `Loot.owns(player, "skin", id)`. The Wood Chipper is handed over
  as the Tool renamed "Shredder" with attribute `Skin`.
- The loadout screen has a SKINS tab: a card per weapon, DEFAULT first, hover to try, click to put on.

Ideas of our own for later (not built, none a Rivals theme): Night Shift (matte black, an amber hazard band, a work-lamp
sight), Bowling Night (lane wood, pin-white stock), Glazed (white ceramic with cobalt bands), Smog Runner (weathered
grey-green, a respirator muzzle).

## The Marble Shotgun's jar and reload (16 November 2026)

The owner: "gumball shotgun should lose less gumballs? idk how that would work, the reload is like this cage thing".

- **The jar shows the ammo, fuller for longer.** The jar holds 14 balls, each its own node (`marble_00` at the
  bottom .. `marble_13` at the top), on the gun and on the Gumball Machine. `GunParts` shows
  `floor((ammo / mag) ^ 0.6 * 14 + 0.5)` of them, so half the ammo still shows 9 balls. An empty gun shows none. The
  rest settle with a small bob when a shot takes some.
- **The reload pours them back.** The lid (`lid`) flips open on its front hinge (0.42 to 0.6 s), the bag pours
  (0.66 to 1.18 s) while the balls fill back up from the bottom, and the lid snaps shut (1.42 to 1.5 s). The Gumball
  Machine's crank (`crank`) turns once after the off hand slaps the lid shut (1.55 to 1.75 s). It keeps the web
  game's reload time (1.9 s). The off hand (the bag, the slap on the lid, the hand riding the crank) is the hold
  session's, in Viewmodel.
- The numbers are in the Marble Shotgun's row in `Weapons.luau` (`mdl.parts`: jar, lid, crank).
- Pictures: `gun-models/marbles-reload.jpg` (posed in Studio from the game code, without the hand) and
  `gun-models/skins-in-studio.jpg` (25 of the 26 skins side by side).

## No z-fighting inside a gun (16 November 2026, place version 401)

The hub's flicker scan (`ZFight`) found about a dozen pairs of faces inside the armory's display guns, gaps of 0.002 to
0.019 studs. These are two pieces of different looks lying in one plane, facing the same way and overlapping, so the
GPU can't tell which is in front. `tools/roblox/gun_zfix.py` now runs on every gun and skin as it is built
(`gun_set.py` wraps each builder). It uses the flicker session's `zfightfix.py` finder.

- **Where a gun is checked:** in the studs of its smallest static display, the armory racks (long guns 6.6 studs,
  the rest 3.9). That is about 3.2 to 11.5 studs a metre.
- **How a pair is fixed:** it is pulled apart to 0.04 studs there, or 8 mm at most on the gun. On the long guns shown
  small (Sniper, Shotgun, Hat Trick, about 3.2 studs a metre) 0.04 studs would be 12 mm and change their look; 8 mm
  is about 0.026 studs, still clear of the scan's 0.02.
- **Which face moves:** the one already in front moves further out (it is the detail meant to be seen: the Hat
  Trick's blue blocks on its handle panel). Of two level faces, a trim (`_wzN`: bands, stripes, lenses) stands out
  over a shell; between two of a kind, the smaller face. Faces always move outward. Only a face's own corners move
  (within 0.3 mm of its plane), so a thin stripe keeps its back on the body.
- **Two traps found on the way:**
  - The finder reads triangles by vertex index, and a builder's mesh can carry stale indices. The fix then saw
    garbage and the first round looked clean here but not in Studio (place version 396 still had 8 pairs). The
    indices are refreshed first now.
  - `zfightfix` skips triangles under 0.01 sq studs each, which suits the map kits. A gun's top faces are cut into
    small triangles, so here every triangle counts and a pair needs 0.004 sq studs of overlap.
- **Checks:**
  - `gun_zfix.py -- all`, before (`JF_NOZFIX=1`): 424 pairs on 40 of the 42 models. After: 5, all at 0.025 studs or
    more, clear of the scan.
  - The exported files, scanned the same way: the same.
  - `gun_check.py`: every gun and skin is still one connected piece.
  - In Studio, the armory's 12 display guns: 0 hits (`ZFight`, tol 0.02).
- **The look:** a few millimetres at most. The Hat Trick, Shotgun and Lawn Mower lost speckled seams and now show
  their side panels and top ribs cleanly; the rest look the same (`JF_NOZFIX=1` builds them as before, to compare).

## Skin sets and tiers (16 November 2026, place version 433)

The owner: "can the weapon skins, not all of them but a couple, be like sets? Halloween style. maybe demon vs angels,
maybe japanese like. look how rivals does their skins and then apply that logic to our game", then "can you create a
cute ducky themed skin set?". The logic (vault note `Research/Rivals skin sets.md`, Rivals' designs left alone): a set
is about five skins over primaries, a secondary and the melee. They share one name family, one palette and one motif
placed the same way on every piece. The top piece gets the biggest reshape and the glow.

| Set (id) | Skins (top first) | Palette and motif |
|---|---|---|
| Seraph (`set_seraph`) | Rifle, Sniper, Hat Trick, Katana, Plan B | ivory and gold; halo, feathered wings, a sunburst core |
| Infernal (`set_infernal`) | the same five | black and crimson with ember glow; horns, blade wings, lava cracks, a slit eye |
| Witching Hour (`set_halloween`) | Pumpkin Patch (SMG), Cauldron (Marble Shotgun), Hex Blade (Katana), Vigil (Revolver), Gravekeeper (Shotgun) | purple-black, bone, pumpkin; a hex band with bone rims |
| Tidecrest (`set_tidecrest`) | Sakura (Katana), Yoroi (Rifle), Cloudlock (Yeehaw), Kintsugi (Second Opinion), Twin Tide (Half a Shotgun) | red and black lacquer, gold wave crests, cloud scrolls, sakura |
| Ducky (`set_ducky`, VIP) | Bubble Bath (Belt Sander), Wish Duck (Revolver), Ribbon Duck (Katana): all high tier | magical-girl rubber duck (since v450): each gun shaped as a duck, a pink bow with a gold star clip, pearl wings, glowing heart gems |

Seraph and Infernal are a pair: the same weapons, the same layout, the motifs swapped one for one. Ducky is the VIP
game pass's set (the owner: "the ducky set is a high tier set you get by purchasing vip"): `vip = true`, never in crates or
the shop, all three high tier. The rifles' high-tier glow follows the research brief (vault `Research/Skin concepts`):
Heaven's light shown inside a frame (a gold arcade of pointed arches over a glowing pane), Hell's light escaping between
black plates (glowing fractures), lit muzzles, and the glow along every feather's ridge.

- **Tiers** (the owner: "basic tier can be simple modifications, mid tiers can be like new models, high tiers will be
  remodeled with vfx"):
  - basic = the base gun with small changes, rarity rare;
  - mid = a new model, epic;
  - high = a full remodel plus effects on the gun, legendary.
  Every set's top piece is high. The 26 older skins keep their web rarities and only get a tier: three are basic,
  the rest mid.
- **The files:**
  - `roblox/src/shared/SkinSets.luau`: `SETS`, `SKINS` (name, rarity, weapon, set, tier), `TIER` for every skin, and
    `FX`, the high tiers' effects. The VFX session's `Fx.skinIdle` plays the effects: feathers and a halo sparkle,
    embers and heat haze, sakura petals, smoke and embers off the pumpkin, soap bubbles.
  - The loot session merges `SKINS` into `LootTable.SKINS`. The shop bundles each set by its id, once all five
    models are in `JankfireSkins`.
  - The models: `tools/roblox/gun_sets.py` (the pair), `gun_sets_halloween.py`, `gun_sets_japan.py`,
    `gun_sets_ducky.py`. `gun_set.py` collects them.
- **The wings took six rounds.** The owner sent pictures of winged guns. An art-judge agent laid our renders over
  those pictures and measured shape match, reach, angles and tone.
  - What lasted: a swept wing, about a third of the gun long. Its top feather is nearly level and the tips step back
    down a diagonal from a row of roots, with a shoulder of short coverts over the roots.
  - The feathers are real 3D shapes (`feather3d`): a ridge down the middle, thin edges and a slight curl.
    - Angel: long round-tipped quills, gold by turns, under an ivory arm.
    - Demon: blades that widen to a sharp point on the leading edge, crimson and black by turns, with the glow
      running along each ridge.
  - A small wing stands up off the front of the handguard (or the slide on Plan B), so the wings show in first person.
  - Flat cut-out feathers read as "a fan of leaves", "a saw" or "spiky hair", whatever their outline.
- Pictures: `gun-models/sets-heaven-hell.jpg`, `sets-witching-hour.jpg`, `sets-tidecrest.jpg` (side view and in hand),
  `sets-wings-vs-refs.jpg` (the owner's pictures, the round before and round 6). Not checked yet: the wings against the
  shooter's own shoulder in third person on a real player, and the VFX session's frame-cost check on the high tiers.

### After the review (16 November 2026, place version 450)

The owner: "some of the current skins either look bad or are too simple", "keytar is one I would say looks bad", "I want
more interesting shapes and designs that could pass off as guns". A review agent scored all 49 skin cards out of 10
against their tier (the table is in the shared notes, `review.md`); 25 scored under 6. All 24 that are not Ducky were
rebuilt, each with one big new shape the hand view sees, and fewer colours.

- **The angel wing, round 7** (the owner: "you keep trying to just do ovals make other shapes"; then picked B, "eagle
  fingers is way better"). `angel_wing()` in `gun_sets.py`: every feather a gold shaft with a narrow light leading vane
  and a wide darker trailing vane (`vane_feather`). The tips are cut by job: five notched "finger" primaries splayed up
  behind the rear sight (the outer two glow amber along their leading edge), square-notched secondaries under a thick
  ivory arm, pointed coverts. The small wings and the Seraph katana's guard use the same feathers. Knobs: `EAGLE`
  (override with the `JF_EAGLE` JSON env var); `ANGEL_WING` picks 'B' (default) or 'A' (falcon fold). The Infernal side
  keeps its blade wings, glowing cracks and red horns (the owner: "the demon variant looks cool").
- **The rebuilt skins.** Files `gun_skins_fix.py` (Keytar: the gun is the keytar, a wedge body, a two-octave keyboard on
  top, a magenta neon neck), `gun_skins_fix2.py`, `gun_skins_fix3.py`, `gun_skins_fix4.py` (eight each). Two took new
  names, kept in `SkinSets.RENAME` (the loot session applies them): `smg_uzi` is now Hairdryer, `sawnoff_pepper` Double
  Chili. `shotgun_double` moved to basic. Four set skins took new names (the table above).
- **Ducky, magical-girl** (`gun_sets_ducky_alt.py`, the owner: "can you make the duck magical kawaii girl kinda thing";
  "skins can change how the gun looks within reason like the shark shotgun"): the LMG's body is the duck, the revolver's
  barrel is its neck with the bill as the muzzle, the katana's guard is a duck with ribbon tails. `SkinSets.FX` gives all
  three sparkles off the gems, soap bubbles, a pink-gold trail, a pink flash and tracer.
- **Cute concepts** (`gun_sets_cute.py`): five looks, A to E, each as a rifle and a pistol, in the game for the owner to
  pick from. They are listed in `SkinSets.CONCEPTS`, so they are not sold and can't roll from crates.
- Checked: `gun_check.py` (0 loose parts on all 48), the z-fight scan on each gun, the install in Studio (48 guns, 0
  problems, 59 skins in `JankfireSkins`), and in hand in a Play test (Keytar, Bubble Bath, cute B). Pictures:
  `gun-models/skins-in-hand-v450.jpg`, `review-fix2.jpg`, `review-fix3.jpg`, `review-fix4.jpg`, `keytar.jpg`,
  `ducky-magical.jpg`, `cute-concepts.jpg`, `angel-eagle.jpg`. Not checked: the new effects' frame cost on a slow
  device, and the cute concepts in third person.

### Space western and the decorated Japanese concepts (17 November 2026, place version 478)

- **Space western, a pair (live).** The owner asked for a classic and a futuristic look of the same weapons, after
  seeing a frontier line elsewhere; ours is our own. Both sets: Revolver and Yeehaw high, Half a Shotgun and Sniper mid,
  Katana basic.
  - Dust Drover (`set_dust`): Dust Drover revolver (horse-head grip, a 7-point star), Iron Horse (Yeehaw as a
    locomotive), Wagon Wheel (Half a Shotgun), Brass Spyglass (Sniper), Horseshoe (Katana).
  - Star Drover (`set_star`): the same five in plum graphite, tan ceramic and teal hard light (Star Drover, Streamliner,
    Warp Wheel, Star Spyglass, Star Horseshoe).
  - Models: `tools/roblox/gun_sets_west.py`. Its `EFFECTS` proposes shot and lever-cycle puffs and sparks for the VFX
    session. `SkinSets.FX` has the high pieces' idle effects.
- **Decorated Japanese (concepts, not sold).** The owner: "more decoared ... use referenmces". Three systems on the
  Rifle, J-A carried across the set: J-A Maki-e (`ar_jp_a`, `dmr_jp_a`, `sawnoff_jp_a`, `lever_jp_a`, `katana_jp_a`),
  J-B Odoshi (`ar_jp_b`), J-C Zogan (`ar_jp_c`). They are in `SkinSets.CONCEPTS` until the owner picks one; the pick is
  rebuilt under Tidecrest's own keys. Models: `tools/roblox/gun_sets_japan2.py`.
- Both files build only when named (`JF_EXTRA=gun_sets_west,gun_sets_japan2`), so an unfinished set can't change live
  skins in other builds.
- Checked: `gun_check` (0 loose on all 17), the install (17 guns, 0 problems, 76 skins in `JankfireSkins`), and in hand
  in Play (Dust Drover with a wood wrap on, Streamliner, J-A rifle). Pictures: `gun-models/space-western.jpg`,
  `japanese-decorated.jpg`, `skins-in-hand-v478.jpg`.

### Ducky VIP v3 (17 November 2026, place version 480)

The owner: "Can we do a complete redo of the ducky guns except the revolver it looks clean on it and cute!!", then
"The duck beak is what looks bad looks nothing like beak!!".
- Bubble Bath (Belt Sander) and Ribbon Duck (Katana) are rebuilt in Wish Duck's clean style, on their base guns' own
  outlines. All three keep their keys, so VIP owners keep them.
- **The shared bill:** one rubber-duck bill on all three, shaped like the Royal Duck hat's bill. It is `duck_bill()` in
  `tools/roblox/gun_sets_ducky_v3.py`: a wide flat spoon about 1.8 times as wide as it is deep, the upper half
  overhanging, a dark seam, the tip turned up.
- Wish Duck changed only its bill. Its barrel is now a slim muzzle tube coming out of the mouth.
- **Bubble Bath:** the duck's head holds the barrel, three glowing hearts sit on the dark ammo box, and soap bubbles
  puff from the bill after a burst (`SkinSets.FX`, `afterFire`).
- **Ribbon Duck:** a clean blade with the duck's head as the guard and hearts on the pommel.
- **Checked:** `gun_check` 0 loose, the z-fight scan 0 pairs on the exported glbs, the install, and in hand in Play.
- **Pictures:** `gun-models/ducky-v3.jpg`, `ducky-v3-bills.jpg`, `ducky-v3-in-hand.jpg`. The revolver in the in-hand
  photo wears the test player's wood wrap.
- **Not yet right:** the dimmed hearts still look pale near the camera. The exporter brightens the Neon colour, so the
  dim slot needs a darker source colour. That fix goes in with the slim-sights rebuild.
- `gun_sets_ducky_v3.py` builds only when named (`JF_EXTRA=gun_sets_ducky_v3`) until the slim-sight kit
  (`gun_sights.py`) it imports is committed.

## Slim sights (17 November 2026, place version 484)

The owner: "my issue is just the iron sights or the scopes look bulky and not like the ones in rivals".

- **What Rivals does** (vault note `Research/Rivals sights.md`): its sights are not tiny. They read as slim because
  they are thin, open and under the aim line: a washer-thin rear ring, a hooded pointed front post at the receiver's
  front, low notch blocks on pistols and shotguns, and near-black sights even on pale bodies.
- **The kit:** `tools/roblox/gun_sights.py`, imported everywhere as `SG` through `gunkit_c.py`.
  - `rifle_rear`, `rifle_front`, `notch`, `blade`, `bead`, `red_dot`, `holo`, `scope_slim`.
  - Each is placed from the gun's `g.spots['sight']`. Walls are at least 3.5 to 4 mm.
- **Where it went:** every base gun and every skin with sights, 50 guns in this install. The gun bodies did not change.
  - Themed skins keep their theme on thin, low sights.
  - The Seraph guns keep their old sights until the angel set is installed; the cute concepts until cute v3.
- **Aim points:**
  - The Half a Shotgun's aim point moved from y 0.037 to 0.065: its old line ran inside the action. `Weapons.luau`
    was updated to match.
  - The Redline keeps its spot. The cover's hump was lowered so the line through its ring is clear.
- **Checked:**
  - `gun_check` 0 loose on all 50, and the z-fight scan finds no pair involving a sight.
  - Three judge rounds against the Rivals note.
  - The install, and in Play: the rifle's thin ring at the hip, and when aiming, the front post inside the ring with
    the target clear around it.
- **Pictures:** `gun-models/sights-before-after.jpg` (side and aimed render, before and after),
  `sights-all-after.jpg`, `sights-in-game-v484.jpg`.
- **Not done here:**
  - How big the ring sits on screen when aiming is the hold session's framing. It is about 4–5% of the screen width
    now, against Rivals' 13%.
  - The hat seats on the changed guns are re-seated by the hats session.
- **Install note:** `W.kit(keys)` only loads models into `WeaponSets.kit`. After it, the base guns also need
  `W.models("kit", ids)` to become the live templates; skins go live through `W.skins()`.

### Cute set v3 concepts (17 November 2026, place version 493)

The owner, after the first cute concepts: "the shapes are irregular and aren't cohesive to how a gun should look",
then "I want bigger more noticeable decorations".

- **The rule** (the skin-concepts brief "Cute set v3"): each concept is the live Rifle and Plan B kept whole, plus one
  big hero piece on the left flank, under the sight line, and reshaped ends. Outlines grow about 12–22%.
  - A Velvet: a jewel locket, fur muff, pom-pom and cushion stock.
  - B Starlight: puffy wings, a star collar and a big stock star.
  - C Glasswing: a stained-glass butterfly and crystals.
  - D Sweet Shop: a big bow, a candy cane hooked down at the muzzle, gumdrop lights and a wrapper-fan stock.
- **Built:** `tools/roblox/gun_sets_cute3.py`, in the default build, same keys `ar_cute_a..d` / `pistol_cute_a..d`.
  - A weight pass brought them down from as much as 43k triangles to at most 15k per rifle and 11k per Plan B.
  - Concept E (Daydream) is dropped. It is out of `SkinSets.CONCEPTS`, `assets.json` and the place.
- **Status:** concepts only, not sold and not in crates, until the owner picks one; the pick becomes a full set. The
  judges call Starlight's Plan B the weakest: its wing reads as a rosette in first person.
- **Pictures:** `gun-models/cute-v3.jpg`, `cute-v3-in-hand.jpg` (Velvet rifle, Sweet Shop Plan B).

### Tidecrest becomes J-A Maki-e (17 November 2026, place version 498)

The owner marked the decorated Japanese sheet: J-A Maki-e yes, J-B and J-C no. On the J-A set pieces they marked Second
Opinion and Yeehaw yes, and Half a Shotgun and the Katana yes twice.

- **Live:** J-A is the Tidecrest set now, built by `tools/roblox/gun_sets_japan2.py` under the set's existing keys, so
  owners keep their pieces. Black lacquer and gold, with the names kept:
  - Yoroi `ar_lacquer`;
  - Kintsugi `dmr_nighttide`;
  - Twin Tide `sawnoff_twintide`;
  - Cloudlock `lever_cloudlock`;
  - Sakura `katana_sakura`, the J-A katana, the set's high piece.
  The set's banner colours are now black lacquer and gold.
- **Removed:** the seven concept keys (`ar_jp_a/b/c` and the J-A set copies) are gone from `SkinSets.CONCEPTS`,
  `assets.json` and the place.
- **Checked:** `gun_check` 0 loose on all five, the install, and in hand in Play (Twin Tide, Sakura). Picture:
  `gun-models/tidecrest-maki-e-in-hand.jpg`.

## The Blender-artist method: trial on the AR and Revolver (17 November 2026, test in place version 504)

The owner: "can you try making them in blender ... with the idea that it's for Roblox and should look like Rivals?",
then: if it goes well, apply it to all the new guns.

- **The kit:** `tools/roblox/artist_kit.py`, with a README at its top. It does four things:
  1. **Modelling:** real Blender tools.
     - Filled, extruded and bevelled curves (`curve_slab`), and curves swept along paths (`curve_sweep`).
     - Exact booleans, cleaned by a planar Decimate and a Weld.
     - A Bevel modifier and a Weighted Normal pass, all applied.
  2. **An atlas packer:** laid out like `gun_uvs.py` (left side upright, u along the gun).
  3. **`bake_gun()`:** bakes ambient occlusion, a soft top-down gradient and a light edge line over the flat slot colours.
  4. **Export and wrap shells:** `roblox_export` carries the texture into Roblox, and `shell_luau` writes the shade
     shells.
- **The trial guns:** `tools/roblox/gun_artist.py` holds the two descriptions, `ar@ar_artist` and
  `revolver@revolver_artist`. Build them with `JF_EXTRA=gun_artist`.
- **Two ways the bake travels into Roblox:**
  - **T, the baked picture as each piece's TextureID:** works today. `export_weapons.py` now keeps a pictured piece's
    UVs and its own slot colour. But a wrap laid on the baked atlas comes out about 6× too big and seamed.
  - **S, the plain kit gun plus a shade shell (recommended):** each node gets a shell 0.8 mm off the surface, wearing
    the shade map as a SurfaceAppearance with AlphaMode Transparency. Wraps stay exactly as today, and the baked
    shading lies over the paint and over any wrap. The cost is about twice the triangles (AR about 25k) and one more
    1024 image per gun.
- **Tested in Studio (v504):**
  - Both routes load the right way round.
  - In the hall the baked guns look softer and more modelled than the live ones.
  - A galaxy wrap shows the T scale problem and S working.
  - In hand and aimed the S rifle is clean.
  - The trial is kept in `PolishBackup.ArtistTrial`, not live.
- **Judges:** AR 7 against the current 5, Revolver 6 against 5.
- **Picture:** `gun-models/artist-trial.jpg`.

### The Ducklings: Blender-method Ducky concepts (17 November 2026, place version 511)

The owner: "Can you also tell it to make a few blender ducky skins?"
- **The guns:** three concepts in Wish Duck's family, built with the Blender-artist method: `ar_duckling`,
  `smg_duckling`, `pistol_duckling`. The builder is `tools/roblox/gun_sets_ducky_art.py` (`JF_EXTRA=gun_sets_ducky_art`).
- **The look:** each has a round head at the barrel's root with the muzzle out of the shared bill, a pink bow with a gold
  star clip, pearl-over-pink wings, a chunky tail, coral feet on the grip, dimmed pink heart gems, and a plum business end.
  The Plan B's slide nose is the duck's head and moves with the slide.
- **Shading:** baked shade shells (route S). Each gun stays at or under 15k triangles including the shells.
- **Not live:** they are concepts in `SkinSets.CONCEPTS`, so not sold, not in crates and not in the VIP pack.
- **Where they live in the place:** the loaded models are kept in `PolishBackup.DucklingTrial`, and the live copies in
  `WeaponSets.kit` / `JankfireSkins`. They are not in `assets.json`; their ids are in the upload log.
- **Pictures:** `gun-models/ducklings.jpg`, `ducklings-in-hand.jpg`.
- **Install trap (found by the hats session):** a model put into `WeaponSets.kit` by hand (not through `W.kit`) needs
  its `FileLo` / `FileHi` attributes set to its own export bounds. Without them `WeaponModels.build` fits it into the
  base gun's box from `Weapons.luau`, squashing it per axis. In v511 the Duckling AR came out 55% as wide and 118% as
  tall. `W.kit` sets them from the kit book; a hand install must copy the import's box check values.

### Tripo pieces: AI-made decoration, cleaned for the kit (17 November 2026, not in the place)

The owner tried Tripo (AI text-to-3D, shape only) and approved five results: a bow, a teddy charm, a crystal cluster, a
duck head and a duck-headed SMG (a reference only). They are the owner's generated files and stay local: the raw files and
everything made from them are in the vault (`Assets/tripo-17nov/`, cleaned copies in `clean/`), never in git. Only the
cleanup code is here: `tools/roblox/gun_tripo.py` (`blender -b --factory-startup -P tools/roblox/gun_tripo.py -- clean
[bow teddy crystals duck]`).
- **On hold.** The plan was to seat the pieces on the concept guns (the bow on Sweet Shop v3, the crystals on Glasswing
  v3, the teddy on Velvet v3 as the Plush take, the duck head on the Duckling SMG). The owner then said "wait with
  concept skins, tripo does a really good job", so none of that is built. Our own method stays for gun bodies; Tripo's
  angel wing and angel rifle were rejected earlier.
- **The numbers** (triangles):

  | Piece | Raw | Final | What worked |
  |---|---|---|---|
  | bow | 39,958 | 1,500 | clean from the start: a plain Collapse decimate |
  | teddy | 41,032 | 2,400 | a masked Smooth modifier, then Collapse in two passes with the face features held |
  | crystals | 40,798 | 1,500 | a plain Collapse (Planar only reached 23.8k: Tripo's facets aren't flat) |
  | duck head | 34,498 | 1,700 | the open bill cut away and patched, a voxel remesh, then the two-pass Collapse |

- **The cleanup, every piece:** import through Blender's glTF importer; apply transforms; merge by distance (1e-4); keep
  only the biggest connected part; fill holes up to 64 edges; normals out; decimate; split into colour regions by face
  (grow from a seed face up to the concave creases, or oval zones round features). Then flat colours from the set's
  palette and Route S shade shells, as the Ducklings have.
- **Traps:**
  - Blender 5.3's Collapse ignores a vertex group's factor: weight 0 just freezes those vertices. One pass with the
    features frozen turned the rest of the teddy into shards. Use two passes: about 5k first, then the target.
  - A Laplacian smooth erases small features (the teddy's eyes). Mask them off first.
  - A voxel remesh softens crisp shapes (the bow's tails). Use it only after cutting and patching.
  - Region borders are jaggy at 1.5-2.5k triangles (eyes, ear cups). Snap border vertices to the zone outline if it matters.
  - Smooth shading turns crystal facets soft. They need sharp, angle-based shading when built.
  - Small features vanish at gun size: a 9 cm teddy has eyes about 2 mm across.
- **Asking Tripo for pieces that clean up well:** smooth, relief-like objects with big shapes (the bow came out nearly
  ready). Ask for a clean vinyl-toy or clay look, a closed mouth, and oversized eyes and nose. Avoid fur or noise texture,
  open mouths and other cavities, tiny facial features, thin dangly bits (the teddy's tail), and "faceted" crystals,
  which come back rounded. About 40k raw triangles is plenty. Aim for 1.5k for a bow or crystal cluster and 1.7-2.4k for
  a head or a teddy.

### Whole Tripo guns: the owner's skin pipeline and the angel rifle (17 November 2026)

The owner's plan: a picture per skin (ChatGPT, given our base gun's picture and a style), built whole in Tripo, then
cleaned, fitted and coloured here.
- **Reference pictures** of every base gun and live skin (left side and three-quarter, plain, no markers):
  `tools/roblox/gun_refs.py`. The pictures live in the vault (`Assets/base-guns-17nov`, `Assets/skins-17nov`).
- **The tool:** `tools/roblox/tripo_gun.py`, with a recipe per skin. It:
  - welds and repairs the mesh;
  - turns and scales it onto the base gun: muzzle, grip and the sight line;
  - drops floating or sight-blocking parts;
  - reshapes parts (scale, flatten onto a side, thickness, sharp feather tips);
  - cuts moving nodes;
  - adds the slim kit sights and small kit parts;
  - colours regions by rule and adds gold rims;
  - bakes Route S shade shells;
  - renders a check sheet, with before/now panels and an aim view with a hide list.
  `-- parts <raw.glb>` lists and renders every loose part first. Recipes, cleaned meshes and sheets stay in the vault
  (`Assets/tripo-*/<gun>/`), never in git. `JF_EXTRA=tripo_gun` registers whatever exists there.
- **The angelic rifle** (`ar_seraph_tripo`, a concept in `SkinSets.CONCEPTS`, not sold). The owner's picks over four rounds:
  - v1's big rear wings: they stand above the sight line, so they are hidden while aiming (`holds.json` →
    `ads.skins.ar_seraph_tripo.hide = rwing_*`);
  - no front wings: they read as unattached;
  - a front-sight block like a real AR's: a pearl tower, a gold post with a bead on the sight line, two gold ears;
  - the floating halo rebuilt as a gold ring round the barrel.

  A clean-up pass (v5) made the colour borders follow the surface and tidied the grip joint, front-sight base and
  bore. 12,619 triangles with shells; asset 140181802705874 (place version 627); the shade picture's packed strips blurred before
  upload so nothing in it reads as text.

  v6 (place version 669, asset 130346853233717) answered "the barrel needs some touch up on angel, also, can there be
  more glowing parts". The changes:
  - the bare barrel became a pearl shroud with two gold bands;
  - the brake is a 12-sided pearl brake with three ports a side and a lit star let into each flank;
  - new lit lines run round the rear wings' tops, down the handguard flanks and along the butt edge.

  13,843 triangles. The lit lines' points for the VFX session are in the notes folder's `angel-v6-lit-lines.json`.
- **The Ducky bundle** (place version 669, all four in `SkinSets.CONCEPTS`). These are the owner's own Tripo models of
  their bundle picks. The owner asked to "break down the weapons into pieces the best you can, and repair what needs to
  be repaired", so each was split into its parts, and each part was repaired on its own (straightened, holes closed,
  mirrored). A part too broken to save was rebuilt from kit shapes.
  - `smg_ducky_tripo` (99482354209343): the lopsided rail to the barrel was straightened and centred, and the whole
    gun mirrored. The keychain charm now hangs from an anchor ring and links.
  - `katana_ducky_tripo` (121784713173285): Tripo's blade was a soft lump with 167 open edges, so it was replaced with a
    kit blade: a bevel down to the edge, a wave band, a gold spine. The grip is a kit candy-stripe grip, and the pommel
    a kit life-ring loop. The duck guard, crown and collar are Tripo's own, centred and mirrored.
  - `sniper_ducky_tripo` (138491983190218):
    - mirroring the body gave the duck head both eyes;
    - Tripo's scope was swapped for the live slim scope on the live sight axis;
    - the chain was fixed at both ends;
    - the one-sided props (life ring, wing, banner) were kept as they were.
  - `pistol_ducky_tripo` (100816221116160): the fused body was cut into a `slide` node and the frame, with `mag` and
    `hammer` nodes and one low sight. The duck nose and crown sit under the sight line.

  Every new kit piece and cutting fix is in `tools/roblox/tripo_gun.py`. The Tripo files and recipes stay in the vault.

  v2 (place version 683) added the concepts' painted details, cut into the mesh as flat colour regions by the `decals`
  recipe step (no picture textures):
  - SMG: blue curling waves, foam dots and drops, plus a duck print on each receiver side;
  - sniper: a wave band along the barrel;
  - katana: curling crests with foam curls and dots on the blade;
  - Plan B: waves along the slide's lower edge and on the grip panels.

  The light slot moved halfway from pearl toward each concept's blush (e.g. SMG `ebdfde`). Some shade shells were
  dropped to stay under 15k triangles. Assets:
  - SMG 96541562068186
  - katana 122632316158289
  - sniper 112944176569314
  - Plan B 117844930479923

  v3 (place version 708) answered two owner notes. "It's a good base but with a lot of these you might have to rebuild
  them a bit!! Make sure it has proper gun elements" got round-2 shapes from `tripo_gun.py`:
  - Plan B's red-pen marks fixed: notched rear sight and a front post (no dot: `gun_sights.blade` adds its glow
    insert only on a post taller than this one, like the base guns), round duck head under the sight line, clean
    frame seam, flat reliefs, slide serrations, an ejection port, a bore in the duck's mouth;
  - SMG and sniper bores and ports.

  "Ducky looks so simple now" got a baked surface from `tools/roblox/tripo_bake.py`:
  - the same meshes with the shade shells dropped;
  - 1024 atlases (SMG 2, Plan B 2, sniper 3, katana 1), each with a NormalMap from Tripo's own surface, a painted
    ColorMap (AO, cavity, edge light, foam lines, clouds, mag wave bands, banner crown and duck, piping, rivets) and
    glossy Roughness plus gold Metalness;
  - one SurfaceAppearance per pictured piece (AlphaMode Overlay, white). Dark, metal, neon and glass pieces stay plain;
  - `WrapUV` is off on these skins because a wrap picture on the atlas UVs would come out 2 to 5 times too big. Picture
    wraps fall back to their palette colours on them, and solid wraps work. Taking a wrap off brings the baked look back.

  Before upload, every normal, metal and roughness map went through `tools/roblox/bake_guard.py`. It blurs the packed
  small-island strips and drops lone metal motifs (a banner crown on its side reads like a letter). The katana's
  blade dots that landed on the gold spine were painted out by hand. Triangles: SMG 12,272, Plan B 12,654, sniper
  13,755, katana 10,252. Models:
  - SMG 72904091721393
  - katana 73021117796404
  - sniper 139142913295194
  - Plan B 81405719351973, then 128878054607229 (v709, below)

  v709: the hold session's aim check found Plan B's raised blue strap across the slide top (recipe `add[0]`, top at
  0.0555, between the notch and the post) hid the front post below 0.0552. The strap is out of the recipe and the
  game mesh. The blue-white-blue band stays as paint on the slide top (the bake spec already painted it there), and
  the slide was re-baked; only atlas A1 changed. From the eye, the whole post now shows in the notch. A lesson for
  every themed gun: nothing may rise above the slide top between the notch and the post.

  The 32 map ids are in the notes folder's `gun-models-uploads-16nov.md`. The install is
  `w_<key>_install.luau`-style Luau run in Edit: the maps are PluginSecurity. The live angel v6 was left as it is; its
  bake is kept as an option only.
- **Prompt lessons:**
  - Our base AR's two ring sights come back as "two scopes": ask for one low sight and no scope rings.
  - ChatGPT refused "hellhound" and "cute devil" wordings; "stylized cartoon game cosmetic" wording passed.
  - Ask for solid attached parts only, nothing tall on top, a plain background and no text.
- **Images to ChatGPT:** the built-in browser pane can't attach files. The ChatGPT desktop app, driven by computer use,
  can: its file dialog takes a typed path.

## How it was judged

An independent judge (a separate agent that saw only the pictures and the style notes) scored every weapon against
"would this sit next to Rivals' guns in a polished Roblox shooter?" (Rivals' own plain guns about 8 to 9). The
weakest were reworked after each round, with Rivals' matching guns open as the reference.

| Round | Average | What it said most | What changed next |
|---|---|---|---|
| 1 (first build, in the hall) | 6.2 | bright colour covering the whole top of every gun; look-alike pairs (Assault Rifle / Lawn Mower, Sniper / Second Opinion); the Revolver had no cylinder | charcoal tops, colour on side panels and stocks, a third less saturation; the scoped rifles, Revolver, Lawn Mower rebuilt; solid sight posts |
| 2 (Blender renders) | 6.6 | pencil barrels, thin rods, plank grips, empty boards; the snipers still generic | the Sniper and Second Opinion rebuilt again; thick guards; lighter tops on the charcoal guns; shrouds; signatures moved into view |
| 3 (in the hall) | 6.8 | pure-black sights and scopes under the crosshair; thin barrels; colours too strong under the lamps; the Sniper's changes invisible from the eye | round 4: charcoal sights and scopes, darker and dustier colours, the Sniper's barrel fat all its length and a lit eyepiece, the Lawn Mower's deck on top, the sanding belt as the Belt Sander's hero |
| 4 (in the hall) | 7.4 | the Sniper's new eyepiece did not show from the eye; wood, tan and brass turn orange-gold under the lamps, so the set was not calmer than the old one; the Belt Sander, Lawn Mower and Half a Shotgun weakest | round 5 (below) |
| 5 (in the hall) | 7.3 | the Sniper's lens now shows; the guns go near-black in hand (charcoal and the colour blocks merge), so fixes in the lighter values vanish; gold accents and a few full reds; the theme guns wear their theme as add-ons. Weakest: Belt Sander, Lawn Mower, Half a Shotgun | round 6 (below), with the owner's four notes |
| 6 (in the hall) | 7.25 | all four owner notes answered (no rounds on top, the Sniper's stock one piece, no cross, blockier in the side views); still near-black in hand; "blockier" only partly: Rivals' blockiness is thick masses and the long guns are still slim; the Shotgun, Hat Trick and Second Opinion lost their signature with what was taken off. Weakest: Belt Sander, Shotgun, Lawn Mower | round 7: thicker barrels and tubes, chunkier long guns, a signature built into the body where one was taken off |
| 7 (in the hall) | 7.5 | the owner's four notes still hold; the Hat Trick's squares and Second Opinion's second optic read in first person; the compact guns are properly blocky, the long guns still 4 to 5 times as long as tall (Rivals about 3); the held gun's left side faces away from the hall's lamps, so colour blocks go near-black. Weakest: Shotgun, Plan B, Belt Sander | first a fill light on the held gun (viewmodel code), re-shoot, then decide on another model round |
| 8 (in the hall, with the fill light) | 7.5 | the mix shows from the side but is timid in first person (the rounding went onto grips and magazines, which the hands hide); 8-sided leftovers next to the round barrels; most of the brighter look is the new fill light. Weakest: Shredder, Second Opinion, Revolver | round 8b (below): round what the player sees; then the owner asked for version C |

Round 1 per gun: AR 6.5, SMG 5.5, Hat Trick 6, Belt Sander 6.5, Second Opinion 6, Sniper 6, Yeehaw 7, Shotgun 7.5,
Lawn Mower 5, Redline 6.5, Marble Shotgun 6.5, Katana 6.5, Plan B 6.5, Revolver 4.5, Half a Shotgun 5.5, Shredder 7.
Round 3 per gun: AR 7, SMG 6.5, Hat Trick 7, Belt Sander 6, Second Opinion 7, Sniper 6.5, Yeehaw 7.5, Shotgun 7.5,
Lawn Mower 5.5, Redline 7, Marble Shotgun 7, Katana 7.5, Plan B 7.5, Revolver 6.5, Half a Shotgun 6, Shredder 7;
the Cardboard skin 5.

Round 4 per gun: AR 7.5, SMG 7.5, Hat Trick 7, Belt Sander 6.5, Second Opinion 7.5, Sniper 7, Yeehaw 7.5, Shotgun 8,
Lawn Mower 6.5, Redline 8, Marble Shotgun 8, Katana 7.5, Plan B 7.5, Revolver 7.5, Half a Shotgun 6.5, Shredder 8;
the Cardboard skin 5.5.

The judge after round 4: "about a point under" Rivals' plain guns, with the Shotgun, Redline, Marble Shotgun and
Shredder touching the low edge of the bar, and the set "less garish, not less colourful" than the old models.

Round 5 per gun: AR 7.5, SMG 7.5, Hat Trick 7, Belt Sander 6.5, Second Opinion 7, Sniper 7.5, Yeehaw 7.5, Shotgun 7.5,
Lawn Mower 6.5, Redline 8, Marble Shotgun 8, Katana 8, Plan B 7, Revolver 7, Half a Shotgun 6.5, Shredder 7.5; the
Cardboard skin 7. It called the set plainly less colourful than the old models ("now overshoots into dark and drab
rather than calm") and the Sniper "the best it has been", but "a black tube and a white disc" from the eye.

**Round 6** (the owner's notes plus judge round 5): the kit itself made blockier (every chamfer half as wide, wedge
sections straightened, barrels flat-faceted, vents as upright slots, front sights square blocks, the AR, SMG, Belt
Sander, Lawn Mower and Redline stocks boxy L shapes); no loose rounds (the Hat Trick's three rounds and the Shotgun's
shell saddle gone, the Belt Sander's belt now charcoal links low on the left, still counting the ammo down); the
Sniper's stock one solid block with no thumbhole, cheek pad or panel; Second Opinion's cross gone; every charcoal,
near-black and colour block a step lighter; gold accents (Katana guard, Revolver ring, Marble bell, Shredder hopper,
Yeehaw receiver) greyed; the Lawn Mower's knobs brick, the Shredder's lamps small, the Redline's red stock band dark;
the Revolver's cylinder lighter steel than its frame; a pale rib between Half a Shotgun's barrels.

Round 6 per gun: AR 7, SMG 7.5, Hat Trick 7, Belt Sander 6.5, Second Opinion 7, Sniper 7.5, Yeehaw 7, Shotgun 6.5,
Lawn Mower 6.5, Redline 7.5, Marble Shotgun 8, Katana 7.5, Plan B 7, Revolver 8, Half a Shotgun 8, Shredder 7.5; the
Cardboard skin 7.5. The judge measured the hall's floor at the same brightness in rounds 5 and 6, so the near-black
guns are not the photos: the held gun is lit darker than Blender shows, and a step lighter in the colours moved the
gun's dark pixels only 0 to 6 levels. That points at the light on the held gun more than at the models (see "Not
checked").

**Round 7** (judge round 6): every barrel 1.2 times as thick (`BARREL_K` in `gunkit.py`, bores too); charcoal,
near-black and the top decks another step lighter, the Assault Rifle's top rail on the deck colour; the Hat Trick's
three blue squares; Second Opinion's second optic; the Shotgun's wider receiver, fatter pump and slotted barrel
shield, the dark patch off its stock; the Belt Sander's links thinner with gaps; the Yeehaw's bands widened and one
star; Plan B's rear sight charcoal; a green panel on the Lawn Mower's receiver, an amber strip on the Shredder's motor.

Round 7 per gun: AR 7.5, SMG 7.5, Hat Trick 8, Belt Sander 7, Second Opinion 7.5, Sniper 8, Yeehaw 7.5, Shotgun 6.5,
Lawn Mower 7, Redline 8, Marble Shotgun 8, Katana 7.5, Plan B 7, Revolver 7.5, Half a Shotgun 7.5, Shredder 8; the
Cardboard skin 7.5. The judge's advice: more model rounds might add about 0.3; a soft fill light that travels with
the held gun, aimed at its top and left side, would likely add 0.5 or more to every gun at once (most already look
about 8 in Blender's neutral light). If another model round follows, its list: the long guns thicker in mass
(handguards, receivers, stocks, not only barrels), the Shotgun's shield and receiver top on the deck colour, Plan B's
blue moved onto the slide's left side, the Lawn Mower's green as one block, the Belt Sander's stock charcoal and a fat
ammo box feeding the belt, fewer and deeper magazine ribs.

**Round 8** (the owner: "not completely blocky, some rounded too, a mix of the two versions"): `gunkit.py` round 8
switches, for every gun at once: every chamfer a soft round edge (`BEV_SEG` steps, shaded smooth while the flat faces
stay crisp) at three quarters of the builder's width; tapers back to two thirds (`WTOP_K`); barrels, tubes and rings
round again, with more sides the bigger they are (`round_sides`: 12, 16 or 24); the side-view corners of grips,
magazines, stocks, pumps and handguards rounded (`CORNER`, square where they join the gun so no notch opens); the
parts the hand holds and the scopes a fuller round edge (`ROUND_NODES`, `ROUND_K`). Judge 8 (7.5, per gun: AR 8, SMG
7.5, Hat Trick 7.5, Belt Sander 7.5, Second Opinion 7, Sniper 8, Yeehaw 8, Shotgun 7.5, Lawn Mower 7, Half a Shotgun 8,
Plan B 8, Revolver 7, Redline 7.5, Marble Shotgun 7.5, Katana 7.5, Shredder 6.5; Cardboard 7.5) said the mix was timid
where the player looks, so **round 8b** rounded what is seen: the big masses (body, slide, motor ...) get the full round
edge twice as wide (`BODY_NODES`, `BODY_K`), stocks' corners rounder, round rear sights on the Assault Rifle and the
Belt Sander, the Shredder's hopper smooth and round with round cage posts and its motor's top in amber, Second
Opinion's optics two round scopes (one fat, one small beside it) with purple on the receiver and a body-wide magazine,
the Revolver's cylinder round with six dark flutes, its underlug as wide as the barrel and the guard closed to the
grip, the Lawn Mower's drum round. Live in place version 281 (the hub rebuilt, 0 problems).

## Version C: a real gun each, built the way Rivals builds (for the owner's pick)

The owner asked for cohesive shapes, each from a real gun, "reference rivals heavily, look at how they build their
weapons". Rivals' plain guns were looked at again (16 Nov; nothing saved): every one is a real gun's silhouette
simplified (an AR with a ring sight, an M16 with its carry handle, an Uzi, a pump gun, a coach gun, a thumbhole
sniper, a blocky handgun, a revolver with an underlug); boxes with ONE clean, fairly wide chamfer; every tube
8-sided and shaded round; chunky; charcoal with one colour. Version C follows those rules for all sixteen
(`tools/roblox/gunkit_c.py` sets the style and holds the shared pieces; builders in `gun_models_c.py` and its parts
`gun_models_c1.py` to `c3.py`), each drawn from a real gun and NOT from Rivals' own models (where Rivals has the same
kind of gun, ours is a different real one):

| Gun | Drawn from | Gun | Drawn from |
|---|---|---|---|
| Assault Rifle | AK-12 (ribbed cover, rail, rear aperture, curved magazine) | Shotgun | SPAS-12 (perforated shield) |
| SMG | HK MP5 (hooded post, drum sight, cocking tube) | Lawn Mower | AA-12 (drum, carry handle) |
| Hat Trick | FAMAS (it is a bullpup already; long carry handle) | Half a Shotgun | a sawn-off coach gun with two hammers |
| Belt Sander | M249 SAW (feed cover, box, belt into the left side) | Plan B | Colt M1911 |
| Second Opinion | SVD Dragunov (thumbhole stock) + a second small optic | Revolver | S&W Model 29 (half underlug, target grips) |
| Sniper | Remington 700 / M40 (one-piece stock, heavy fluted barrel) | Redline | Thompson M1928 (finned barrel = the glowing vents) |
| Yeehaw | Winchester 1873 (octagon barrel, lever loop) | Marble Shotgun | a flintlock blunderbuss with the jar |
| Katana | a real katana (temper line, round tsuba, wrapped grip) | Shredder | a garden wood-chipper (style pass) |

Every C builder takes its spots from the current builder and keeps every node the game moves; sizes within about 8%;
1,900 to 4,400 triangles. Things to settle if a C gun is picked: the hold session may nudge a hand on the Shotgun
(the grip is in the stock), the Sniper and the SMG (the handguards' undersides moved about 1 cm), and the Redline's
left hand (a vertical foregrip); the Belt Sander's belt now empties from the box end; the Cardboard skin is built on
the A/B Assault Rifle and would need its own C version. Preview: `gun_preview.py -- <dir> --set c <ids>`.

## Checked, and not checked

- **Checked in Studio:** all sixteen load from their assets facing the right way (each template's box matches the
  exporter's to 0.0001 m); every piece is SmoothPlastic, Neon or Glass with no picture and no SurfaceAppearance (0
  pieces outside that on the live templates); every wrap (102) in every mode (3) goes on and comes off all seventeen
  kit models leaving each piece exactly as it was; the Assault Rifle fires through the game's own remote in a Play
  test (8 shots, 8 hits, the magazine 30 to 22, the dummy down 88 = 8 x 11, the rifle's damage); the third-person model
  the server builds in your hand comes from the new template; all sixteen photographed in hand in the training hall
  after each round (round 6: place version 261, round 7: 263, round 8: 279, round 8b: 281), and the hold session
  moved three fists (Plan B, Revolver, Shredder) onto the new grips. Version C is built and carded in Blender only.
- **Not checked:** every gun firing (only the Assault Rifle was shot; the others were armed and held, and the game's
  spots and moving-part names are unchanged, so their firing code has nothing new to meet); the reload animations'
  moving pieces on each new model (mag drops, pump, bolt, lever, cylinder, hinge) in motion; the Belt Sander's belt
  links counting down (same names, `belt_00`..`belt_11`, as before); the Redline's needle and vents reacting to HP; guns in another player's hands (needs two
  players); the Rooftop's daylight; phones; the loadout screen's previews (they build from the same templates, not
  looked at).
- **Done since:** the soft fill light on the held gun (a separate session, place version 280): the guns read in
  colour in hand from round 8 on. The Shredder (a Tool) has no fill light yet.
- **Open:** the owner's pick, A, B or C per gun; then one rebuild, upload and import of the picked set (with the wrap
  session's UVs at the export step).
- **Uploads:** each round's models are new Roblox assets (`jf_kit_*` to `jf_kit9_*`, private to the owner; the list up to 8b, with times and states, is in the shared
  notes, `gun-models-uploads-16nov.md`); only the
  ids in `roblox/assets/weapons-kit/assets.json` are used. The older ones are harmless and can be deleted from the
  creator dashboard.
