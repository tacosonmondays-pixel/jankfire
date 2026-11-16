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
| Witching Hour (`set_halloween`) | Pumpkin Patch (SMG), Cauldron (Marble Shotgun), Hex Blade (Katana), Candlelight (Revolver), Bone Yard (Shotgun) | purple-black, bone, pumpkin; a hex band with bone rims |
| Tidecrest (`set_tidecrest`) | Sakura (Katana), Red Lacquer (Rifle), Cloudlock (Yeehaw), Night Tide (Second Opinion), Twin Tide (Half a Shotgun) | red and black lacquer, gold wave crests, cloud scrolls, sakura |
| Ducky (`set_ducky`, VIP) | Bubble Bath (Belt Sander), Bath Toy (Revolver), Duck Guard (Katana): all high tier | rubber-duck yellow, an orange bill at every front, a plump wing over the trigger |

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
