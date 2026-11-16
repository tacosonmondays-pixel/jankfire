# The guns' calm paint, the first-person gloves and the hold (15 November 2026)

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

Before: your avatar's bare arms, which on a pale avatar blew out to plain white shapes under the lamps. Now: a dark
slate glove and a near-black sleeve, made from your avatar's own hand and forearm shapes so they fit any body
(`AvatarArms.KIT`). Nothing is added at the wrist: three cuff designs were tried and each read as a fault from the
player's eye. Since the hold rework (below) both are smooth and lit: the glove is a step lighter than the guns, so a
hand never vanishes into a dark gun, and the sleeve clearly darker than the glove.

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

## The hold (the same day, place version 237)

What the paint judges had called out next was how the weapons are held: the katana edge-on with fists over the hilt,
the support hand beside the handguard on a forearm that rose as a pointed wedge, the pistol hand a scoop under the
grip, a glove through the Shredder's cone, and the off hand hidden for every reload. All of that was reworked.
**No number, name, mechanic or gimmick changed, the paint is as it was, and the hands are still your own Roblox
avatar's** (a four-finger glove modelled in Blender was tried first and taken out the same hour: the owner wants
Roblox's own hands).

Pictures: `gun-hold/before-after-1.jpg` to `-4.jpg` (all sixteen, the old hold on the left) and
`gun-hold/in-motion.jpg` (the katana's parry and cut, the off hand in reloads, a wrap).

**How it works now**

- **One table says how every weapon is held:** `tools/roblox/holds.json`, written into `src/shared/Holds.luau` by
  `py tools/roblox/holds.py`. Per weapon and hand: where the fist is on the weapon, how it is turned, its size; where
  each forearm comes from (an elbow spot in camera space); the katana's rest and parry poses.
- **The hand grips at its own grip attachment,** the spot Roblox itself uses for a held Tool, so the grip is right
  for any avatar's hand shape. What it holds runs through the fist: a pistol grip, the katana's hilt, a handguard.
  The hand then turns about that handle until its wrist faces the elbow.
- **The forearm is not glued to the weapon.** Every frame it runs from the wrist to the elbow spot
  (`AvatarArms.aim`), so it cannot sweep across the screen when the gun rolls onto its side, swings or twirls. Hand
  and forearm are lined up by their rig attachments, not their boxes (a box-aligned forearm was the old wedge).
- **The support hand** grips the handguard from under, on a short steep forearm, and a sidearm's arm comes up from
  nearer the eye so the fist and wrist show round the grip.
- **The Katana** has a new rest pose and a new parry pose laid over the web game's clips: the blade runs up across the
  screen with its flat, the guard and the wrapped handle toward you, the hands apart on the hilt. The cut itself is
  the web game's: the new pose eases out as a swing winds up and back in as it recovers (`Holds.katana`,
  `katanaFix` in `Viewmodel.luau`). Reach, cooldown, cone, parry window and timings are untouched.
- **The off hand is back in reloads.** It goes down and back with the magazine, rides the Shotgun's pump, holds the
  Redline's can and the marble bag from under, steps clear while the Yeehaw spins, and otherwise keeps its place
  on the gun (`offHand` in `Viewmodel.luau`).
- **The Shredder** takes its hands from the same table (its row is in the tool's own frame): the left palm is under
  the body behind the cone, and nothing clips.
- **The HUD's colour chips** for the Sniper and the Yeehaw are their calm accents now (`a2457c`, `a58640`; `color`
  in `Weapons`, and the loadout screen's `Roster`).

**How it was judged**

Twice, by an independent agent that saw only the before and after pictures and was told the avatar's hand shapes
are fixed. Scores out of 10 for the hold and hands as seen; "before" is the state the paint pass left.

| Weapon | Before | Round 1 | Round 2 | Round 3 |
|---|---|---|---|---|
| Assault Rifle | 3 | 6.5 | 6 | 6 |
| SMG | 3 | 6.5 | 6 | 5.5 |
| Hat Trick | 3.5 | 5 | 5.5 | 6 |
| Belt Sander | 3 | 6 | 5.5 | 5.5 |
| Second Opinion | 3 | 7 | 6 | 5.5 |
| Sniper | 2 | 6.5 | 5.5 | 5 |
| Yeehaw | 3 | 6 | 6 | 4.5 |
| Shotgun | 3.5 | 7 | 5.5 | 5.5 |
| Lawn Mower | 3 | 6.5 | 5 | 5.5 |
| Half a Shotgun | 5 | 6 | 5 | 4 |
| Plan B | 5 | 6.5 | 4 | 4 |
| Revolver | 5 | 5 | 5.5 | 3 |
| Redline | 3 | 6 | 6 | 5.5 |
| Marble Shotgun | 3.5 | 6.5 | 6 | 5 |
| Katana | 2 | 7.5 | 7 | 5.5 |
| Shredder | 3 | 6 | 6.5 | 5 |

("Before" is the first judge's score; the second judge scored the same pictures within half a point, the third about
one point higher. Round 3 was the first one at the larger size.)

- **Round 1** (the first avatar-hand hold): "close, not at the bar". Weakest: the Revolver (no hand could be told
  from the grip), the Hat Trick (a hook under the fore-end), the Shredder (a thin arm, no hand), and on every long
  gun a left forearm that crossed the screen as a long glossy plank. Reworked: the hands moved onto their grip
  attachments, the support arm became short and steep, the sidearms got an arm of their own, the glove was lightened.
- **Round 2**: again "close, not at the bar", the long planks and rock-like fists gone, the Katana the best. Plan B
  went backwards (a hand far too big swallowed the grip), and the judge asked for thicker forearms ("a stick under a
  ball"), a glove between dark and clay grey, a sleeve that is not a flat black cut-out, the off hand round the
  handguard rather than under it, and smaller pistol hands.
- **Between rounds 2 and 3 the owner asked for bigger guns** ("Can the weapons be a little larger, that way the arms
  dont look so long and lanky"): every weapon in first person is now drawn 25% larger, the hands with it (`_size` in
  `holds.json`; the third-person guns and the loadout previews are unchanged). The round-2 fixes went in with it:
  smaller pistol hands on an arm from farther out, forearms a fifth thicker, the glove at 50, 52, 58 and the sleeve
  at 26, 28, 32, the support hands a little higher, and the sidearms and the katana lifted clear of the HUD.

- **Round 3** (25% larger): the rifles "from clearly unfinished to close", the Hat Trick and the Assault Rifle the
  best. It found the size right for the rifles but too much for the one-handed guns (the Revolver and Plan B came so
  close to the camera that the hand and gun merged), the forearm still a thin pole that vanished against black guns,
  and the Redline's reload can a placeholder. Last changes after it (place version 237, not judged): the one-handed
  guns drawn at 0.8 of the new size (`scale` in `holds.json`, back to the web game's size), the forearm a third
  thicker and its sleeve lighter (36, 38, 43) so its outline holds against a black gun. The sheets in `gun-hold/`
  show that state.

The judges' shared verdict: **close, not at the bar.** The Katana went from the worst hold to one of the best; the
long guns are coherent; the sidearms, the Yeehaw and the reload props are the weakest.

## Matched to the Rivals layout (16 November 2026, place version 347)

The owner: "can you look at how all the weapons and stuff are held in rivals so you can reference look and sizes of
stuff?" Rivals' first-person views were measured from videos (an all-weapons showcase against a plain sky, two plain
gameplay videos) on a 5 % grid; the numbers and what they mean are in the vault note `Research/Rivals first-person
holds.md` (no Rivals picture is kept in git or anywhere outside the vault). What they show:

- Every gun points at the crosshair: the muzzle sits just below and right of it (about 55.5 / 58 % of a 16:9 screen).
- A rifle covers about a quarter of the screen's width and leaves the bottom edge at 60 to 80 % across; the lower right
  quarter stays empty. Pistols are small and show their side. The support forearm comes up from the bottom edge,
  left of centre; the trigger hand hides under the gun. A katana stands nearly upright in the right half.

Ours were about 44 % wide, their back ends ran into the right edge and their muzzles sat 3 to 9 % lower and further
right. The game's default FOV is 80 (`JankSettings`), not Roblox's 70, which `tools/roblox/hold_screen.py` (new) takes
into account: it prints where each gun lands on a 16:9 screen from the kit's part boxes, checked against Play photos.

What changed (`holds.json`, nothing in the gun models, the paint, the hands' look or any mechanic):

- Every gun's rest pose moved (`shift`, camera space): most sit about 0.35 m further from the camera and a little
  left, so the muzzle lands on the Rivals spot and the gun covers 54 to 80 % across. Every gun is drawn at the same
  scale (1 against `_size` 1.25; the Marble Shotgun 0.9), so the hands are the same size from gun to gun.
- New `tilt` (degrees added to the rest turn, `Viewmodel.luau`): Plan B 18 and the Revolver 24 about y, so their side
  shows instead of their back end; Half a Shotgun turned straight ahead so its barrels run to the crosshair.
- Plan B's and the Revolver's fists moved down their grips (the butt and the magazine base poked out below the fist).
- The Marble Shotgun drawn a little smaller and lower, its jar below the crosshair.
- The Katana's rest stands nearly upright on the right, the flat of the blade toward you (guard at about 65 / 72 %).
- The forearms are thicker (`AvatarArms.SLEEVE` 1.6, was 1.35): further off, they had thinned to poles.
- The utility items (the items session, place version 343): their held spot moved 0.2 studs left so they sit about
  16 % left of and 24 % below the crosshair, the mirror of Rivals' held grenade; the frag and the duck drawn smaller.

Judged by an independent judge from before and after photos against the measurement boxes (sheets
`gun-hold/rivals-1.jpg` to `rivals-4.jpg`: ours before, ours after, the Rivals-class box; no Rivals picture):

| Weapon | Before | After |
|---|---|---|
| Assault Rifle | 4 | 8 |
| Hat Trick | 4 | 7 |
| SMG | 4 | 7 |
| Sniper | 3 | 7 |
| Shotgun | 5 | 7 |
| Plan B | 5 | 7 |
| Revolver | 4 | 5 |
| Katana | 2 | 9 |
| Belt Sander, Second Opinion, Yeehaw, Lawn Mower | | 6, 7, 7, 7 |
| Redline, Marble Shotgun, Half a Shotgun | | 6, 4, 5 |

Its verdict: "yes, a lot"; every gun now points at the crosshair and the rifles sit inside the box. Its three weakest
(the Marble Shotgun's jar at crosshair height, the Revolver's grip poking out below the fist, Half a Shotgun pointing
below the crosshair) were fixed after it, with the thicker forearms, and checked in a Play photo, not judged again.

Checked in Play (place version 347): all fifteen guns photographed in hand at the new spots (the Shredder's hold did
not change); hats sit right (party, cowboy, chef, cone on four guns); wraps read (camo, galaxy, hex, hazard);
Half a Shotgun fires twice and reloads in about 2 s; the Revolver's sights come to the crosshair (aim unchanged).
Not checked: other avatar bodies, the Shredder with the thicker forearm, aim on every gun, third person, the Rooftop's
daylight, reloads on every gun at the new spot.

## Three looks per weapon: before, after, combined (16 November 2026, place version 358)

The owner, after the Rivals sheets: "I think the closer up befores look better for some of them, can you do back to
back again like we had athem before just havingt the barrel faced in the new version like combine the new angles with
the closer look?" So every weapon now keeps three looks in `holds.json` (`looks`), and `use` says which one is in play:

- **before** (place version 340): near and big, the muzzle low and right of the crosshair.
- **after** (place version 347): the Rivals layout above, further off, a quarter of the screen.
- **combined** (live on every weapon): before's size and nearness, the muzzle moved onto after's spot just below and
  right of the crosshair so the barrel points at it; Plan B and the Revolver keep after's turn so their side shows.
  The Katana keeps before's guard spot (nearer the middle) with after's upright blade; the Shredder sits between the
  two (`shredder.vm_looks`, read by `ShredderClient`). Aiming keeps after's work (the sight on the crosshair, both
  scopes); the one-handed guns aim a little nearer than in after, to match their closer rest.

Flip one weapon back by changing its `use` to `before` or `after` and running `py tools/roblox/holds.py`. In a Play
test, the player's `HoldLook` attribute shows one look on every weapon at once (`Viewmodel.look`, `ShredderClient`).
`py tools/roblox/hold_screen.py --look before|after|combined` prints where each look puts each gun.

Sheets for the owner (each row: before | after | combined): `gun-hold/looks-1.jpg` to `looks-3.jpg`.
Checked in Play: every weapon in all three looks photographed; aiming on the SMG, Plan B and the Sniper lines up in
combined; the Shredder's first-person copy no longer stays in the camera when its tool is removed (an older fault:
the tool's own script dies with it, so Arsenal now clears a copy whose `Owner` tool is gone; place version 360). Its
heat bar still stays until you respawn in that case. Not checked: other avatar bodies in the combined look (checked in after), third
person (on the owner's avatar the held gun points backward; older code, not touched, needs its own fix).

## What is still not at the bar

- The hands are Roblox's own, so on a blocky avatar they are mittens with no fingers: a trigger finger or fingers
  round a handguard cannot be shown. That is by choice.
- Shapes that are toy-like by design: the Lawn Mower's drum, the Marble Shotgun's jar, the Hat Trick's slab
  receiver and oversized rounds, the Revolver's block sights, the Sniper's plank stock.
- The reload props are simple: the Redline's can is a flat red box, and the things the off hand would fetch (a
  spare magazine, shells, a speedloader) are not modelled, so its hand goes with what is there.
- The off hand props a long gun from below (one palm-up hold for every handguard) rather than wrapping it, and the
  trigger hand is mostly hidden behind the gun at this camera angle.
- The 25% size is one number (`_size`), chosen from the owner's words and the judges' read; since the Rivals pass the
  guns sit further off at that size, so they look like Rivals' on screen; the owner has not yet seen it.
- The trigger arm still shows as a second forearm beside the stock on the Shotgun, the Sniper, the Second Opinion and
  the Yeehaw (Rivals hides it), and long guns show the flat end of their stock in the lower right.

## Switching paints

The web paint is not lost: every model file and every uploaded asset still carries it. `roblox/README.md`, "The
paint is a switch", has the commands. In short, in Studio (Edit):

```lua
local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())
W.use("web")        -- or W.use() for the calm paint; W.shredder("web") / W.shredder("calm") for the Shredder
```

and `ReplicatedStorage.Jankfire.AvatarArms`' attribute `Look = "avatar"` brings the bare arms back (in the same
hold).

## Checked, and not checked

The paint pass (version 215):

- Checked: all sixteen weapons build and are held in a Play test; the Assault Rifle fires, hits and reloads; a wrap
  goes on and comes off every repainted template leaving each piece exactly as it was (six weapons tried); the three
  oldest templates (Redline, Marble Shotgun, Katana) were re-imported through the exporter and match the
  hand-imported ones to 0.00001 m.

The hold (version 237), all in solo Play tests in the training hall:

- Checked: all sixteen weapons photographed in hand. Firing, hitting and reloading on the SMG (15 shots, 15 hits,
  1.5 s), the Shotgun (2, 2, 2.0 s, the hand riding the pump) and Plan B (3, 3, 1.4 s), and on the first version of
  the hold also the Assault Rifle. Wraps on the SMG (full), the Shotgun (normal) and Plan B (reverse): they paint
  the gun, never the arms, and come off again. The katana's parry and cut, the SMG's magazine, the Redline's can and
  the Yeehaw being loaded were stopped mid-move and looked at.
- Not checked: other avatars (only the owner's blocky one was tried; the code reads each avatar's own grip, wrist
  and elbow attachments, but a slim or a bundle body has not been seen in it); the `"avatar"` look (bare skin and
  shirt) in the new hold; aiming down sights with every gun; the Rooftop's daylight; the guns in another player's
  hands (third person is unchanged by this); the loadout screen's previews; the marble bag reload and the
  Shredder while it runs.
