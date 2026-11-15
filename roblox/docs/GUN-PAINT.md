# The guns' calm paint and the first-person gloves (15 November 2026)

The owner's direction that day: the weapons and mechanics come from JANKFIRE, the finish is serious and polished in
the class of Rivals, and less colourful. So every weapon was repainted and the bare first-person arms were dressed.
**No number, name, mechanic or gimmick changed, and no model shape changed.** Saved in place version 215.

Pictures: `gun-paint/before-after-1.jpg` to `-4.jpg`, all sixteen weapons in hand in the training hall, the web
paint on the left and the calm paint on the right.

## What the calm paint is

- A quiet body: black polymer, dark and mid steel.
- One muted furniture colour per gun (olive, tan, walnut, slate, graphite, dusk violet, machine green).
- One small accent per gun, in the hue the web game gave it, so the guns are still told apart at a glance.
- Bright only where it tells the player something: sight dots, lenses, the heat glow, live shells, the marbles.
- Joke stickers, charms and tags take the colour of the surface under them. Chrome goes to mid steel, gold to brass.

| Weapon | Web paint | Calm paint |
|---|---|---|
| Assault Rifle | olive with a pink see-through magazine, neon strip, charm | olive furniture on gunmetal, a smoked magazine |
| SMG | black, teal slab and magazine base | black and charcoal, the whole magazine is the teal accent |
| Hat Trick | bright blue glitter body, yellow controls, baguette rounds | slate body, darker panels, blue magazine, three dark brass rounds |
| Belt Sander | orange body, hazard stripes, green box | graphite body and box, orange feed cover and switches |
| Second Opinion | purple marbled stock, pink tubing, stickers | dusk violet furniture on black steel |
| Sniper | hot pink glitter stock, gold | smooth grey-tan stock on black steel, violet lens, one small magenta mark |
| Yeehaw | pink and blue patterned stock, gems, gold | saddle walnut, steel receiver, brass trim |
| Shotgun | orange wood | dark walnut, blued steel, red shells |
| Lawn Mower | bright green, red drum, striped cord | charcoal furniture, a machine green magazine; drum and cord gunmetal |
| Half a Shotgun | candy orange and blue pattern | dark cherry wood, steel barrels, red shells |
| Plan B | pearl white and silver, gold | the dark handgun: black frame, gunmetal slide, a blue rib and controls |
| Revolver | pink pearl grip, chrome, gold | the steel handgun: gunmetal frame, dark cylinder, black grip, brass trim |
| Redline | black and red | the same; grip and tape lose their pictures, chrome to steel |
| Marble Shotgun | bright brass, blue jar with a label, rainbow marbles | aged brass, walnut, a dark smoked jar, marbles in one blue family |
| Katana | grey blade, royal blue dotted wrap | bright polished blade, black cord wrap |
| Shredder | yellow hopper, hazard stripes, speckled grey housing | dark steel hopper and housing, one flat amber band, dark red teeth tips |

## The first-person arms

Before: your avatar's bare arms, which on a pale avatar blew out to plain white shapes under the lamps. Now: a matte
dark slate glove and a plain near-black sleeve, made from your avatar's own arm shapes so they fit any body
(`AvatarArms.KIT`). Nothing is added at the wrist: three cuff designs were tried and each read as a fault from the
player's eye. The sleeve is drawn unlit, because every lit finish flashed pale or pebbled when a lamp was straight
above the forearm.

## How it was judged

An independent judge (a separate agent that saw only the pictures) scored every weapon against "would this sit next
to the guns of a polished competitive Roblox shooter?", first the web paint against the first calm paint, then the
reworked paint. The weakest of each round were reworked before the next.

| Weapon | Web paint | First calm paint | After the rework |
|---|---|---|---|
| Assault Rifle | 4 | 7 | 7.5 |
| SMG | 6 | 6.5 | 7 |
| Hat Trick | 3 | 6.5 | 6.5 |
| Belt Sander | 4 | 7.5 | 7.5 |
| Second Opinion | 4 | 7.5 | 7.5 |
| Sniper | 2 | 6 | 6.5 |
| Yeehaw | 3 | 8 | 8 |
| Shotgun | 6 | 7.5 | 7.5 |
| Lawn Mower | 4 | 5.5 | 6.5 |
| Half a Shotgun | 3 | 8 | 8 |
| Plan B | 4 | 7.5 | 8 |
| Revolver | 3.5 | 6 | 6.5 |
| Redline | 7.5 | 7.5 | 7.5 |
| Marble Shotgun | 4.5 | 5 | 6 |
| Katana | 3 | 4 | 4.5 |
| Shredder | 3 | 7.5 | 7.5 |

Scores are out of 10. On average the sixteen went from about 4 to about 7. The judge's own summary of the second
round: "Not at the bar yet": nine guns at 7.5 or more, six between 6 and 7, and the Katana at 4.5.

After the second round one more set of paint fixes went in, which **no judge has scored**: the SMG's teal moved onto
its whole magazine, the Lawn Mower's green moved off the furniture onto its magazine (it had looked like the Assault
Rifle), the Revolver's frame went from a lavender grey to neutral gunmetal, the Sniper's stock went smooth and
greyer, the Hat Trick's rounds went to dark brass, the Marble Shotgun's jar went dark, the near-black bodies of the
Assault Rifle, Lawn Mower and Redline were lifted to charcoal so their second value shows, and the arms changed to a
darker matte glove with a plain near-black sleeve. The pictures show this final state.

## What paint cannot fix

These came up in judging and are about the hold and the hand shapes, not colour. They are the next job if the guns
are to go further:

- The katana is held edge-on, so the blade is a thin line, and the gloves cover the hilt.
- The hands are fingerless blocks; the support hand sits beside the handguard instead of under it, and the pistol
  hand is a scoop under the grip rather than a hand round it. A glove clips the Shredder's cone.
- Shapes that are toy-like by design: the Lawn Mower's drum, the Marble Shotgun's jar, the Hat Trick's slab
  receiver and oversized rounds, the Revolver's block sights, the Sniper's plank stock.
- The HUD's colour chips for the Sniper (magenta) and the Yeehaw (pink) still show the web colours, which the guns
  no longer wear. They come from each gun's `color` in `Weapons`, which this pass did not touch.

## Switching paints

The web paint is not lost: every model file and every uploaded asset still carries it. `roblox/README.md`, "The
paint is a switch", has the commands. In short, in Studio (Edit):

```lua
local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())
W.use("web")        -- or W.use() for the calm paint; W.shredder("web") / W.shredder("calm") for the Shredder
```

and `ReplicatedStorage.Jankfire.AvatarArms`' attribute `Look = "avatar"` brings the bare arms back.

## Checked, and not checked

- Checked: all sixteen weapons build and are held in a Play test; the Assault Rifle fires, hits and reloads with
  the off hand hiding as before; a wrap goes on and comes off every repainted template leaving each piece exactly
  as it was (six weapons tried); the three oldest templates (Redline, Marble Shotgun, Katana) were re-imported
  through the exporter and match the hand-imported ones to 0.00001 m.
- Not checked: the guns in another player's hands (third person, needs two players), the Rooftop's daylight (all
  photos are from the training hall), the loadout screen's weapon previews, every wrap on every gun.
