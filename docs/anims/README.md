# Animation pass (katana, butterfly knife, melee, reloads)

Clips play at real speed (captured frame by frame on a frozen clock stepped 1/30 s, Too HD). Sheets are every few frames.

| file | what |
| --- | --- |
| `katana.mp4`, `katana_sheet.jpg` | iai draw, both two-handed cuts, parry, inspect (hamon + chiburi) |
| `katana_third_person.jpg` | what other players see: kamae, left arm on the kashira |
| `butterfly.mp4`, `butterfly_sheet.jpg` | balisong draw (basic open) and inspect (reverse basic, basic, grip switch + fan, aerial) |
| `reloads.mp4`, `reloads_sheet.jpg` | every new reload in order: AR, SMG, shotgun, sniper, revolver, Redline, minigun, nail gun, Marble Shotgun, reaper rifle, water pistol |
| `melee.mp4`, `melee_sheet.jpg` | the melee fixes: knife stab + inspect, spoon jab, slapper, bread draw, scythe |

## What changed and why

**Katana** (`public/js/katanavm.js`): held like a katana. Two fists on the tsuka (right behind the tsuba, left at the
kashira) with forearms that run back to your shoulders, so the hands never float. Kamae: hilt low right, blade rising
up and to the right. Poses are written as "where the blade points / which way the edge faces" and slerped (anim.js
`slerp`), so the big cuts turn the short way round. Swings: kesa-giri from over the right shoulder to the lower left,
then the backhand from over the left shoulder; hit stays at 0.12 s (server timing unchanged), 0.5 s long like before.
Draw: one-handed iai cut from the left hip, the left hand joins after. Inspect: let go, look down the hamon, roll it
over, chiburi flick (blood comes off). Parry: two-handed guard across the face. Third person: the left arm reaches the
kashira (2-bone IK), blade raised.

**Butterfly knife** (`public/js/balisong.js`): the held handle stays put while the blade and the free handle swing round
the pivot pins (the whole knife turns about the pivot). Draw: latch, bite handle out over the top, flick: open. Inspect:
reverse basic shut, basic open, grip switch and fan the other way, aerial (off the hand, a full turn, caught), latch.

**Melee review** (anim.js): fixed the ones that looked goofy in the bad way.
- Knife heavy stab, spoon jab + overhead stab, slapper slap, karambit hammer stab: the thrust pointed the blade straight
  away from the camera so only a floating fist showed. They now go in side-on toward the middle.
- Knives and the spoon: a fist closed round the handle instead of the box under it (the box read as a brick in the
  inspects that turn the knife over).
- Bread: its own draw (heaved up onto the shoulder). The shared toss-and-catch filled the whole screen with loaf.
- Scythe: the follow-through stays half on screen instead of vanishing for 0.3 s.
- Fine as they were: claw, scales, popper, cleaver, bowie, kitchen, switchblade, spoon skin.

**Reloads** (`public/js/reloads.js`): every gun that only had the generic dip. Each lasts exactly the gun's reload time
and now runs on the reload timer itself, so it ends on the frame the ammo refills (rifles + sidearms too). An off hand
with a forearm does the work and carries props.
- AR: mag out, fresh mag slapped in, yank the charging handle (the Blender AR's mag + charging handle are now their own nodes).
- SMG: HK style: cocking lever back and locked, mag swap, slap the lever down (Blender SMG mag + lever split out too).
- Shotgun: roll it belly up, thumb six shells into the port one by one, rack it.
- Sniper: bolt up and back (the empty flies), stripper clip of five thumbed down, clip flicked away, bolt home.
- Revolver: cylinder swings out on its crane, muzzle up so the empties fall out, speedloader in, twist, flick shut, spin.
- Redline: pit stop: a tiny jerry can glugs into it, then a twist of the wrist revs the tacho into the red.
- Minigun: the ammo box lid pops, a tiny arm climbs out, waves, shoves the new belt in, thumbs up, ducks back in.
- Nail gun: a fresh strip slid up into the mag, then a tiny pink hammer bonks it home three times.
- Marble Shotgun: flip the jar lid, tip a bag of marbles in (a couple bounce out), lid shut, pat it.
- Reaper rifle: the folded blade swings open, four glowing soul shells pushed in, SHING shut.
- Water pistol: a juice box, straw in, squeeze (the tank fills as it crumples), toss it, two pumps.
- New synth sounds for all of it in `audio.js` (`sfx.reloadFx`).
- Projectile / cooldown weapons (chicken, banana, bowling, duck, tennis, cart): none of them show a loaded round you
  could see go back in, so no reload was added (queued idea: split the bowling ball out of its model and roll a new one in).
