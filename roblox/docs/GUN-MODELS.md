# The guns rebuilt for Roblox (15 and 16 November 2026)

On 15 November, after the guns were repainted, the owner wrote "the gun textures look a little messed up?" and then
"would it be easier to recreate them in roblox? you can look up other rivals weapons and skins!". On 16 November they
added "can you reference the rivals weapons when remodeling these please" and "im mostly discontent with the
snipers". So all sixteen weapons were remade as new models built for Roblox. Their shapes, colours and themes are
our own; Rivals' guns were studied for proportions and finish only.

**No weapon number, name, mechanic or gimmick changed.** Every new model keeps its gun's muzzle, sight, port, grip
and fore spots, the names and pivots of the pieces that move, and the grip and handguard where the hands go, so the
hold, the aim line, the flash, the brass and every reload clip work unchanged.

Pictures: `gun-models/ar-sample.jpg` (the first sample, round 1), `gun-models/snipers-round2.jpg`,
`gun-models/before-after-1.jpg` to `-4.jpg` (all sixteen in hand in the training hall: the old models left, the new
right), `gun-models/skin-cardboard.jpg`, `gun-models/round5-side.jpg` (the final round from the side; its in-hall photos were not taken:
Studio's window was minimised). Style notes from studying Rivals: the vault, `Research/Rivals weapons and skins - style notes.md`.

## What changed

| | The web models (before) | The kit models (now) |
|---|---|---|
| Pieces | 10 to 59 parts a gun, 329 in all, many of them tiny (screws, stickers, cables) | 8 to 31 parts a gun, about 280 in all, each a big simple mass (a part per colour per moving piece; the Belt Sander's 12 belt rounds are one each) |
| Finish | Roblox `Metal`, `Plastic` and `Wood` (each adds its own grain), 42 pieces with printed pictures | `SmoothPlastic` and flat `Color` only; `Neon` on a sight dot, the vents and the lamps; `Glass` on the marble jar; no pictures, no `SurfaceAppearance` |
| Shapes | made for another renderer: thin parts, stickers, cables | a few big chamfered blocks and eight-sided barrels; thick barrels, ribbed magazines, solid sights |
| Colour | a calm paint over the old pieces | a charcoal base, ONE muted colour on the side panels and stock, a small accent where it says something |
| Triangles | 6,400 to 12,300 a gun | about 500 to 2,800 a gun |

Each gun keeps its own signature: the Belt Sander's sanding belt and cable, the Marble Shotgun's jar of marbles on a
blunderbuss, the Redline's rev-counter (its needle still follows your HP and its vents still glow), the Lawn Mower's
drum magazine and pull start, the Hat Trick's three rounds, Second Opinion's medic cross on its box optic, the
Yeehaw's lever loop and stars, the Revolver's cylinder, Half a Shotgun's sawn ends, the Shredder's hopper and teeth.

## How it is built

| what | where |
|---|---|
| the kit: chamfered prisms, boxes, eight-sided barrels, rings, windows, panels, rivets, ribs | `tools/roblox/gunkit.py` |
| one builder per gun (the frame and the rules are at the top of the file) and the skins | `tools/roblox/gun_models.py` |
| preview cards without Studio (three-quarter, in hand, side view with the spots marked, the old model in hand) | `tools/roblox/gun_preview.py` |
| the models' source files (weapon frame, metres) | `roblox/assets/weapons-kit/src/w_*.glb` |
| the upload files (turned for Roblox, look in the piece names), the asset ids, the report | `roblox/assets/weapons-kit/` |
| the book Studio reads (asset ids, file bounds, each piece's colour) | `roblox/studio-tools/WeaponKit.luau` = `ServerStorage.PolishBackup.WeaponKit` (generated) |

To change a gun: edit its builder, then

```
blender -b --factory-startup -P tools/roblox/gun_preview.py -- <dir> --old <web models dir> <id>        (look first)
blender -b --factory-startup -P tools/roblox/gun_models.py -- roblox/assets/weapons-kit/src <id>
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
game's own Cardboard Carl: kraft board, a paper-tube barrel, folded-card sights, yellow parcel tape over the joins,
corrugated cut ends, two box flaps standing on the stock. Nothing printed. Picture: `gun-models/skin-cardboard.jpg`.

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

Not built: owning and picking skins (the loadout's picker, the save, the shop). That is the cosmetics batch
(PORT-PLAN, "cosmetics order"): ProfileStore first.

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
| 5 | not judged | | the Sniper's eyepiece faces the player with a pale lens, its scope and barrel a step lighter, a calmer wine; every wood, tan and brass greyed; reds calmed; the Belt Sander's belt a thick loop; the Lawn Mower's deck a wide skirt; fatter sawn-off barrels; a lighter Hat Trick carry block; the Shotgun's muzzle block; the cardboard skin grey-brown |

Round 1 per gun: AR 6.5, SMG 5.5, Hat Trick 6, Belt Sander 6.5, Second Opinion 6, Sniper 6, Yeehaw 7, Shotgun 7.5,
Lawn Mower 5, Redline 6.5, Marble Shotgun 6.5, Katana 6.5, Plan B 6.5, Revolver 4.5, Half a Shotgun 5.5, Shredder 7.
Round 3 per gun: AR 7, SMG 6.5, Hat Trick 7, Belt Sander 6, Second Opinion 7, Sniper 6.5, Yeehaw 7.5, Shotgun 7.5,
Lawn Mower 5.5, Redline 7, Marble Shotgun 7, Katana 7.5, Plan B 7.5, Revolver 6.5, Half a Shotgun 6, Shredder 7;
the Cardboard skin 5.

Round 4 per gun: AR 7.5, SMG 7.5, Hat Trick 7, Belt Sander 6.5, Second Opinion 7.5, Sniper 7, Yeehaw 7.5, Shotgun 8,
Lawn Mower 6.5, Redline 8, Marble Shotgun 8, Katana 7.5, Plan B 7.5, Revolver 7.5, Half a Shotgun 6.5, Shredder 8;
the Cardboard skin 5.5.

The judge after round 4: "about a point under" Rivals' plain guns, with the Shotgun, Redline, Marble Shotgun and
Shredder touching the low edge of the bar. On colour it said plainly that the set was "less garish, not less
colourful" than the old models; round 5 answered that by greying every warm colour and the reds, and was not judged
again. On the Sniper it said the round-4 fixes did not show from the player's eye; round 5 put a pale lens on the
eyepiece facing the player and lightened the scope and barrel. The Sniper is the gun to look at first.

## Checked, and not checked

- **Checked in Studio:** all sixteen load from their assets facing the right way (each template's box matches the
  exporter's to 0.0001 m); every piece is SmoothPlastic, Neon or Glass with no picture and no SurfaceAppearance (0
  pieces outside that on the live templates); every wrap (102) in every mode (3) goes on and comes off all seventeen
  kit models leaving each piece exactly as it was; the Assault Rifle fires through the game's own remote in a Play
  test (8 shots, 8 hits, the magazine 30 to 22, the dummy down 88 = 8 x 11, the rifle's damage); the third-person model
  the server builds in your hand comes from the new template; all sixteen photographed in hand in the training hall
  after each round, and the hold session moved three fists (Plan B, Revolver, Shredder) onto the new grips.
- **Not checked:** every gun firing (only the Assault Rifle was shot; the others were armed and held, and the game's
  spots and moving-part names are unchanged, so their firing code has nothing new to meet); the reload animations'
  moving pieces on each new model (mag drops, pump, bolt, lever, cylinder, hinge) in motion; the Belt Sander's belt
  rounds counting down; the Redline's needle and vents reacting to HP; guns in another player's hands (needs two
  players); the Rooftop's daylight; phones; the loadout screen's previews (they build from the same templates, not
  looked at).
- **Uploads:** each round's models are new Roblox assets (`jf_kit_*` to `jf_kit4_*`, private to the owner); only the
  ids in `roblox/assets/weapons-kit/assets.json` are used. The older ones are harmless and can be deleted from the
  creator dashboard.
