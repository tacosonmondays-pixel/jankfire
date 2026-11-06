# JANKFIRE

A low quality multiplayer FPS. Infinite momentum, a grappling hook, real guns, weapons that should not exist, killstreaks, and janky mannequins that fall apart when they die.

Three.js client (rendered crunchy on purpose, PS1 wobble on weapons) + one small Node WebSocket server. Every sound is synthesized. Every model is boxes, unless you plug in Tripo.

## Play it

### Windows app (exe)

Grab `JANKFIRE-1.0.0-win.zip`, unzip it anywhere, run **JANKFIRE.exe**. No browser and no Node install needed. The launcher gives you:

- **PLAY ONLINE**: connects to the official server, https://jankfire.onrender.com (set in `desktop/config.json`).
- **HOST ON THIS PC**: runs the server inside the app. Friends on your wifi join with the address it shows.
- **JOIN ADDRESS**: type a friend's address or any JANKFIRE server URL.

**Updates:** PLAY ONLINE loads the game from the server, so every time the server is redeployed (merge to `main` on GitHub and Render redeploys on its own) everyone playing online gets the new version the next time they open it. No new exe needed. HOST ON THIS PC runs the copy bundled inside the exe, so that one only changes when you download a new zip.

In game the main menu has CHANGE SERVER, FULLSCREEN and QUIT GAME. FULLSCREEN cycles **Windowed → Windowed fullscreen** (fills the screen, keeps the taskbar) **→ Fullscreen**; the same choice is in **Settings → Display**, and F11 toggles fullscreen. The app remembers your choice.

An installer (`JANKFIRE Setup.exe`) and a single-file portable exe are built on Windows: push the repo to GitHub and the **Build desktop app** action (`.github/workflows/build-desktop.yml`) produces them under Actions → Artifacts. Or on a Windows PC: `npm install` then `npm run dist:win`.

To point **PLAY ONLINE** at a different server, put its URL in `desktop/config.json` before building:

```json
{ "officialServer": "https://jankfire.onrender.com" }
```

### From source (any OS)

1. Install **Node.js** 20.12 or newer (https://nodejs.org).
2. Double-click the launcher: `Start JANKFIRE (Windows).bat`, `Start JANKFIRE (Mac).command`, or `start-linux.sh`. Or run `npm install` then `npm start`.
3. It opens `http://localhost:3000`. Friends on the same wifi use the address it prints.

`npm run desktop` runs the exe version from source.

## Keep multiplayer online 24/7 (no PC needed)

1. Put this folder on GitHub (no `node_modules`, no `data`, no `.env`).
2. **Supabase** (accounts that survive restarts):
   1. Make a free project at https://supabase.com.
   2. **SQL Editor** → paste all of `supabase.sql` → Run.
   3. **Project Settings → API Keys → Secret keys**: copy the secret key (starts with `sb_secret_`). Not the publishable key: that one can't touch the locked-down table. (A legacy `service_role` key also works.)
   4. Test it locally: copy `.env.example` to `.env` (the project URL is already filled in), paste the secret key, run `npm run check-supabase`. It should say everything is OK.
3. **Render**: open https://render.com/deploy?repo=https://github.com/tacosonmondays-pixel/jankfire (or **New → Blueprint** → pick your repo). The URL is already in `render.yaml`; paste the secret key as `SUPABASE_SERVICE_KEY` when it asks. You get a `https://jankfire-xxxx.onrender.com` link.
4. Put that link in `desktop/config.json` and rebuild the exe (above).

Notes:
- The **secret key is a secret.** It only ever goes in `.env` or Render's environment settings. Never in the exe, never in `desktop/config.json`, never in chat or a public repo. The exe talks to your server; only the server talks to Supabase.
- `render.yaml` uses the **Starter** plan (about $7/month) so it never sleeps. The free plan works but sleeps after 15 idle minutes and takes ~30-60 s to wake.
- Without Supabase, accounts live in `data/jankfire-db.json` (or the app's user-data folder for the exe). Fine on your own PC, wiped whenever a host like Render restarts.
- Set up Supabase with an older version? Run `supabase.sql` again after updating: it adds new stat columns (like `sniper_feats` for Sniper Royalty) and keeps every account. `npm run check-supabase` tells you if one is missing.
- Any Node host with WebSockets works (Railway, Fly.io, a VPS). The server reads `PORT`.

## Controls

| | |
|---|---|
| WASD | move |
| Shift | run |
| Space | jump (hold to bhop). Jump while grappling to launch off the rope with your momentum |
| C / Ctrl | crouch; crouch while fast to slide. Spam it too long and your knees explode. As the Wrecking Ball: ground slam (in the air) / brake |
| Left mouse | fire / swing / play a card / draw the bow (hold, release) |
| Right mouse | aim down sights · **Knife: heavy stab** · **Katana: parry** · Card Deck: pick a card |
| E / mouse side buttons | grapple (hold) |
| R | reload (Card Deck: redraw) |
| F | inspect your weapon · **Plant & Defuse: hold F to plant / defuse** |
| G | **use your item** (grenade, medkit, shield bubble, duck, smoke, party popper, reverse card, bubble wand, instant camera, pop quiz). Night Vision Goggles: G puts them on / takes them off |
| H | **Night Vision Goggles: flash** everyone you can see (goggles on) |
| 1 / 2 / 3 / 4 (in a pop quiz) | answer the question |
| Z | **spray** your graffiti on the wall, floor or ceiling you're looking at (one at a time, every 10 s) |
| 5 / 6 / 7 | **use your killstreaks** (the tray on the right shows which are ready) |
| 1 / 2 / 3, wheel, Q | primary / secondary / melee, last weapon. 4 = Scythe Rifle if you have it |
| V (hold) / X | Scythe Rifle: glitch dash / switch to rifle mode |
| 1 / 2 / 3 (between rounds) | vote for the next map + mode |
| Space / click | skip a killcam (not an EPIC one, and never the play of the round) |
| B / Esc | pause menu · Tab scoreboard · T / Enter chat |

Settings: display (windowed / windowed fullscreen / fullscreen), grapple on right click instead, toggle aim, sensitivity, ADS sensitivity, fov, fov kick, shake, blood, fps counter, quality, speed lines, killcam, show other players' uploaded name cards.

## Modes

| Where | What it is |
|---|---|
| Play | Online with real people, one shared room. After every match everyone votes on the next map + mode. |
| Bots | Private match vs 1-12 bots. Pick the mode, map, difficulty and hipfire. |
| Coop | Everyone vs endless waves of bots. No friendly fire. A container every 5 waves. |
| Training | Target dummies, infinite ammo, a movement playground. Your 3 picked killstreaks are always in the tray (a used one comes back a few seconds after it runs out). Good for testing kill effects, the katana and the streaks. |

Game modes (Play + Bots):

| Mode | Rules |
|---|---|
| Deathmatch | everyone for themselves, first to the kill limit |
| Team Deathmatch | red vs blue, first team to the kill limit. No friendly fire. |
| Tags | kills drop a tag. Grab enemy tags to score, grab your own team's to deny them. |
| Plant & Defuse | attackers carry the bomb to site A or B and hold F to plant (3 s). Defenders stop them or hold F to defuse (5 s). First to 4 rounds, sides swap after round 3. |
| Randomizer | everyone gets a random loadout every life (weapons only: your item and its charges stay yours) |
| Gun Game | everyone climbs the same 19-rung ladder holding only that rung's weapon (no other slots, items or killstreaks): AR, SMG, Redline, Shotgun, Minigun, Shredder, Revolver, Marble Shotgun, Sniper, Bow, Chicken Rocket, Blood Cross, Peel Shooter, Card Deck, Hand Slapper, Bread, Scales of Justice, Katana, Spoon. A kill with your rung's weapon moves you up; dying to any melee weapon knocks you back one (HUMILIATED). Everyone hears when someone reaches the spoon, and the first spoon kill wins. 10 minute clock, highest rung wins if it runs out. |
| Infection | a few seconds in, one random player turns (two from 8 players). Zombies are green, groan, have 200 HP, run 30% faster and only get the Zombie Claw (two swipes kill). Survivors keep their loadout, but anyone who dies as a survivor comes back as a zombie, and late joiners start as one. Survivors win if anyone is alive when the 3 minute clock runs out (the round and the roll go to the best survivor who got a kill); the infected win once everyone has turned. |
| Spoons & Grapples | free for all with nothing but the Spoon (one hit kills, point blank) and the grappling hook, which pulls 35% harder. No guns, no items, no killstreaks. |
| Duck Rain | deathmatch, but rubber ducks rain from the sky (a drop every 2.4 s down to 1.1 s as the match goes on, 1-4 ducks each depending on map size, half of them near someone) and land as black holes. A red ring and a shadow on the ground plus a falling whistle show where each one lands. A sky duck kill is a suicide unless someone hurt you in the last 6 s (they get it). Sky ducks are the real Rubber Duck: they fall straight down (no homing, so you can dodge the red ring), but one that lands on you sticks and the hole rides you. Only a thrown duck homes in. |
| Floor Is Lava | the map's ground floor burns: 20 damage per touch, then 4 every 0.3 s for 1.4 s, and it bounces you back up. Crates, roofs, walls and ledges are safe, spawns are always on safe ground. The ground floor is worked out per map (the lowest height with a real amount of floor, plus curbs half a metre above it). Only on maps that have one (not Platform or Skyline). No Never Landed run here (the lava keeps everyone off the floor anyway). |
| One in the Chamber | a Revolver with one bullet (any hit kills, no reloading) and a knife. Each kill gives a bullet (max 3). 3 lives each, out of lives = spectate (click to watch the next one). Last one standing wins. |

Bots play the objectives too: they carry and plant the bomb, defuse it, and grab tags. They also use the grapple to chase, to get up high, and to save themselves from the void. On maps with bomb lanes (Bazaar and the classic maps) they walk the lanes as a graph and re-plan when they get stuck; on the Backrooms a walk graph of the whole maze (both levels, stairs and drops) steers them in every mode.
In the chaos modes they rush you with the spoon (grappling in from afar), stop at lava edges and grapple back out when they fall in, and in One in the Chamber only spend their bullet on a close enough shot, knifing you otherwise.

**Match Settings** (pause menu): map, hipfire accuracy, bot difficulty, bot count, and (in Bots) the mode.

## Weapons

- **Primary:** Assault Rifle, SMG, **Redline**, Shotgun, Minigun, Sniper (a headshot from a player always kills), Chicken Rocket, Bowling Ball Launcher, Bow, Peel Shooter, **Shredder**, **Big Laser Pointer**
- **Secondary:** Revolver, Marble Shotgun, Cigarette (smoke it, blow fire), Leaf Blower, Card Deck, **Snowball**, **Blood Cross**
- **Melee:** Bread, Slipper (throw it, it comes back), Knife, Hand Slapper (point blank, launches + makes them slip), **Katana**, Spoon, **Scales of Justice**
- **Item (G):** one per loadout, see below. The Party Popper and the Reverse Card used to be secondaries; they're items now.

### Items (G)

Charges refill over time (the pie on the item box), and you get them all back when you respawn, so **charges = what you get per life**, **refill = how often in a long life**.

| Item | Charges | Refill | What it does |
|---|---|---|---|
| Frag Grenade | 2 | 18 s | bounces, blows up after 2 s: 105 at the centre, knocks people (and you) flying. Grenade-jump with it |
| Medkit | 2 | 20 s | heals 45 over 2 s |
| Shield Bubble | 1 | 28 s | a dome for 7 s: nothing from outside hurts anyone inside |
| Rubber Duck | 1 | 20 s | homes in and sticks to an enemy: the black hole opens on them and follows them, drags their friends in, eats everyone's momentum and snaps grapples, then pops |
| Smoke Bomb | 3 | 14 s | a cloud nobody can see through for 10 s |
| **Party Popper** | 2 | 9 s | yank it: a confetti blast shoves everyone in front of you away hard and launches you backwards. Zero damage, all void kills and escapes |
| **Reverse Card** | 1 | 22 s | for 3 s every bullet, blast and shove aimed at you goes back to whoever sent it. A big spinning UNO card over your head, the arrows circling you and a red outline tell everyone not to shoot |
| **Bubble Wand** | 2 | 15 s | blows 4 soap bubbles: the first enemy one touches is sealed in a giant bubble that floats up and away for 5 s, then pops (see below) |
| **Instant Camera** | 1 | 25 s | G snaps a photo of what's in front of you (free). G again prints it: a giant photo stands up in front of you for 20 s, and walking into it puts you back where you took it, facing the same way. Anyone can use it (see below) |
| **Pop Quiz** | 1 | 22 s | a calculator you throw. A hit freezes them with a maths question for 6 s: wrong or too slow = dead (your kill), right = +25 HP, 2.5 s where nothing hurts them and a speed boost |
| **Night Vision Goggles** | 2 | 14 s | G flips them down (free): green view, the dark lifts, everyone glows. H spends a charge to flash everyone you can see near your crosshair (blinded 0.6-3.2 s, longer the more they were looking at you). Wearing them doubles how long any flash blinds you |

The popper and the reverse card pop into your left hand for a moment (wearing their Champagne / Skip Card skins if you have them) while your gun stays out. Other players see them in your hand too.

Why the numbers:
- **Frag** is the only item that kills outright, and a movement tool on top: still 2 a life, but the refill went 16 → 18 s.
- **Medkit** was one heal of 60 a life, which lost to the bubble and the reverse card. Now 2 × 45 (90 a life): the pick for staying in fights. Refill 22 → 20 s.
- **Shield Bubble** is the biggest defensive play (7 s, protects your whole team): 1 charge, the longest refill. Unchanged.
- **Rubber Duck** sets up kills and void kills (it homes in, sticks and holds people in the hole; the pop does 45): 1 charge, 20 s, unchanged.
- **Smoke Bomb** has no damage and no protection, so it gets the most charges and a fast refill: 2 → 3 charges, 18 → 14 s.
- **Party Popper** is mostly movement (a shotgun-jump-sized launch, one per yank) and a shove with zero damage: a short refill, but only 2 at a time (it used to be infinite with a 1 s cooldown as a secondary).
- **Reverse Card** can turn a sniper headshot back on the sniper, so 3 s once a life with a long refill (it used to be 1.2 s every 6 s and cost you a secondary slot).
- **Bubble Wand** takes someone out of the fight for 5 s and can float them over the void, but any hit (a teammate's too) pops it and nobody can be re-bubbled straight away: 2 charges, a 15 s refill.

**Only two guns shove people with bullets**: the minigun (hold it on someone and they get pushed away, the price for spraying) and the sniper (a body shot sends them flying off the map). Melee and explosives still knock people around, and your own movement tricks (shotgun jumps, minigun flying) still work.

**Knife (CS-style):** left click alternates diagonal slashes, right click is a heavy stab (windup, 90 damage, a backstab kills). Every knife skin moves like its real-world family: the Butterfly's handles flip around the blade, the Karambit spins on your finger through the ring, the Switchblade flicks open, the Kitchen knife rolls like a bayonet, the Bowie does a barrel-roll toss, the Cleaver balances on a fingertip.

**Katana:** the blade gets longer (and reaches further) with every kill you get with it. Resets when you die.
**Right click parries:** a 0.35 s window, then a 0.8 s cooldown (a ring round the crosshair). Anything that hits you from the front (140 degrees, judged by the server from its own positions) bounces off: bullets are blocked, and in the first 0.15 s (a perfect parry) they go back into the shooter as a Katana Parry kill; projectiles get batted back at the thrower; melee attackers get shoved back and staggered (no guard of their own until it wears off). Explosions aren't parried. SHING, sparks, PARRY! / PERFECT PARRY!, and it shows in killcams.

**Marble Shotgun:** a hundred marbles a shot, and they stay on the floor. Where most of a shot lands together the server leaves a **patch of marbles** (worked out from the shooter's own position and its own map raycasts) for 9 s, and you can see every marble in it. Run, sprint, slide or bhop across one and your feet go out from under you (MARBLES!, the banana slip); **crouch-walk** over it (or walk round) and you're fine, with any weapon out (except the Spoon, which crouches straight into a slide). Patches stop at walls: the far side of a wall isn't on them. Everyone slips, the shooter on their own marbles too, except teammates. After a slip you get 2 s before marbles can get you again, and each slip scatters some of them: the patch gets smaller and thinner, and goes after about four slips. Slipping off a ledge or into the void is the shooter's kill. Bots slip too, and patches show in killcams. 3 patches per shooter, 10 per room.

**Scales of Justice:** a big brass balance scale swung like a mace (overhead smash, click again for a side swing). 35 damage times a **verdict** the server decides at hit time from how the target stands next to you right now. Each charge is a point of guilt, each thing in their favour takes one off:

| | guilt |
|---|---|
| their K/D this match is better / worse than yours | +1 / -1 |
| they're above / below you on the scoreboard | +1 / -1 |
| they lead the match (and it isn't you) | +1 |
| team modes: your team is behind / ahead | +1 / -1 |
| they're on a 3+ / 5+ kill streak (kills from this match) | +1 / +2 |
| they're the last one who killed you (until you get revenge, or the match ends) | +2 |

Coop wave bots and training dummies aren't on the scoreboard, so only their streak and revenge count (a fresh one is a HUNG JURY, x1). GUILTY: x(1 + 0.4 per point), up to x3, which one-shots (THE COURT HAS SPOKEN). NOT GUILTY: x(1 - 0.25 per point), down to x0.4. Zero points: HUNG JURY, x1. The scale in your hands tips toward the verdict for whoever is under your crosshair (heart pan = guilty, feather pan = innocent) and a readout under the crosshair says it, e.g. `GUILTY x2.2`. Every hit gets a gavel bang, a shower of coins and a gold stamp over the victim (yours shows through walls; other people's only nearby), in killcams and highlights too. Skin: **Kangaroo Court**, a wobbly wooden toy scale with a kangaroo judge.

**Revolver:** tap for a dead-accurate 40 damage shot (a headshot does 96: almost a kill), and after every shot it does a quick cowboy twirl round your trigger finger, back in the hand before you can fire again. **Hold fire to fan the hammer:** after the first shot the rest of the cylinder goes at about 6 a second, with way more spread and 28 damage a shot (67 to the head), the gun spinning in your hand the whole time to rapid hammer clicks. Your off hand holds it down, so fanning kicks less than tapping. Aim down sights for plain single shots. Everyone else (and the killcam) sees your revolver spin too. The server checks it all: hits that come faster than a tap only do fan damage, nothing counts faster than a fan, and after 6 hits it wants a reload.

**Sniper no-scopes:** a sniper hit when you're not fully scoped gets a NO SCOPE badge with the distance by your crosshair and a no-scope icon in the kill feed (damage is the same). Get no-scoped from 25 m+ and you get the full MLG treatment: a spinning rainbow NO-SCOPED, hitmarkers, lens flares, stickers and an airhorn, and your killcam waits for it. A no-scope headshot at any range sends up fireworks that spell the shooter's name and the distance, for everyone (killcams and the play of the round too).

**Slipper:** thrown like a boomerang, it curves into the nearest enemy in front of it on the way out (and keeps flying out a bit longer while it has a lock), then flies back to you.

**Snowball:** barely hurts, but every hit adds frost. 4 hits freezes them solid for a moment; hit a frozen target and they shatter.

**Bubble Wand (item):** G blows a stream of 4 slow, wobbly soap bubbles (2 charges, 15 s to refill each; they float about 10 m). The first enemy one touches is sealed in a giant soap bubble for 5 s: no moving, shooting, items or streaks, just looking around while it floats them up (2 m/s) and away from you (1.5 m/s). Then it pops and drops them: no fall damage, but over the void that's your kill. Any hit (bullet, melee, projectile, explosion) pops it instead of hurting them, so teammates can shoot a friend free and enemies can wait until they're over the void (shoot it open there and the kill is yours). You, your teammates, anyone in a Shield Bubble and a rolling Wrecking Ball can't be bubbled; blow one at someone with a Reverse Card up and you're the one floating away. After a pop nobody can be bubbled again for a while: 1.5 s, or 60% of however long they were in (3 s after a full float), so two wands can't keep someone in one for good. Inside, everything sounds underwater and the world wobbles behind a rainbow soap film.
**Big Laser Pointer:** an office laser pointer the size of a leg (taped-on pistol grip, two D-cells, a cat charm). Hold to charge: 1.2 s for a full one, you walk at 72% speed, the meter LEDs fill and the lens glows and whines (everyone sees and hears it). Let go: a thick green beam down where you look that follows your aim for up to 0.6 s, goes through everyone in the line, stops at walls, ticks 5-21 damage every 0.1 s and shoves a little (about 130 if they stand in a full one). A tap is a weak little zap. The server times the charge and does the hits. Bots carry it.

**Instant Camera (item):** the first G is free: it snaps a photo (the server remembers where you stood, on the floor under you, and which way you faced; no floor under you = no photo). Every client renders the picture itself, so whoever was standing there is in it. The photo shows by your item slot until you print it (G, costs the charge) or die. The print is a giant instant photo on a kickstand, 1.9 m in front of you, for 20 s (one each: a new one replaces the old one). Walk into it from either side and you come out where the photo was taken, facing the same way. Anyone can walk through, enemies too, and an enemy who does is tagged by you, so anything that happens to them over there in the next 10 s is your kill. Whoever is standing on the spot when someone comes out gets telefragged (the traveller's kill). Killcams show frames and teleports. Bots with one snap a photo when it's quiet and print it to escape when a fight goes badly.

**Pop Quiz (item):** the calculator flies in an arc and bounces. Whoever it hits is frozen with a maths question (sums, times tables, squares, halves, two-step ones) and 4 answers: keys 1-4 (or click) within 6 s. The server picks the question and keeps the answer. While they're sitting it nothing can hurt them and they can't attack; everyone else sees a giant calculator in front of their face and the sum on a sign over their head. Wrong or too slow: dead, your kill ("failed maths"). Right: a gold star, +25 HP (up to 125), 2.5 s where nothing hurts them and 4 s at 1.25x speed. Nobody can be quizzed again for 10 s after one. Teammates, shield bubbles, spawn protection and wrecking balls are immune; a Reverse Card sends the exam back to the thrower. Bots answer right 50 / 70 / 85% of the time (easy / normal / hard) after 1-4 s.

**Night Vision Goggles (item):** G flips them down from your forehead (free, everyone sees them on your face with the lenses lit). The view goes green and grainy inside the two eyepieces, dark maps get readable (it lifts more the darker the map is), fog thins and everyone's outline glows. With them on, H flashes: everyone you can see (walls, smoke and shield bubbles block it) within 34 m and about 35° of your crosshair is whited out for 0.6 s (looking away) to 3.2 s (looking right at you), with ringing ears and a blurry afterimage. Anyone wearing goggles gets twice that. A Reverse Card flashes it back. Bots wear them and flash you.

**Shredder:** an industrial vacuum-shredder. Hold to suck: a 14 m cone (35° each side) pulls people toward the intake, harder the closer they are (sprint and you can get away at long range; within a few metres it just yanks you in). Their gun goes in first. Whoever reaches the intake hangs in the spinning teeth and gets chewed (150 damage a second, dead in about 0.7 s); a Shredder kill takes them apart, the pieces go into the machine and come out of the exhaust chute in chunks, with blood and confetti. About 4 s of sucking overheats it (the teeth glow red-hot, the gauge hits the red, it steams), then it has to cool. Teammates are safe, bots carry it too, and the server does the pulling and the shredding from its own positions. Skin: Wood Chipper.

**Bow:** hold to draw, release to fire. Every arrow gets a random tip, shown on the HUD: regular, power, knockback, flame, explosion, gas, sleep (knocks them flat on the floor for 4 s, Zzz).

**Card Deck:** you hold 5 cards from a real 54-card deck. Right click picks, left click flicks it out of the fan, R redraws.
Hearts heal by the number · Spades throw that many cards · Clubs blast people back · Diamonds dash you forward · Aces teleport you · J / Q / K are ultimates · Jokers fire a random ultimate.

**Blood Cross:** no gun, just your hand doing finger guns (the thumb is the hammer). Every shot costs you 12 HP (it never takes your last one, so it can't kill you), about one shot every 0.7 s. The glowing blood bolt flies dead straight and sticks where it lands: on a player a small glowing X carves into their body and rides along with them, 0.6 s later two 2.5 m blood spikes burst out through them in a big X, then they pop for 75 damage plus a small blast (3 m, up to 35) on anyone else close by (not your team), blood all over the walls. A kill with it pays the 12 HP back. On walls and floors it leaves an X that fizzles out. Everyone sees the mark, the spikes and the pop (killcams and the play of the round too); when it's you, the X is on your screen. Inspect blows the blood off your fingertip. In Training the blood you spent comes back 2 s after your last shot. Skin: Shadow Cross, a charred hand that bleeds purple.

**Aim down sights:** the rifles, SMG, revolver and peel shooter have real iron sights (the shotgun has a bead), and ADS lines the sight up with the exact middle of the screen with the gun below it. Launchers, the minigun and the bow stay low and to the side. Hats tuck away while you aim.

**Feel:** springy recoil with camera punch, muzzle flashes, ejected shells, shotgun pump and sniper bolt after each shot, smear trails on swings, a tiny freeze when a melee hit connects, draw animations, weapon sway, speed lines when you go fast. Headshots go DINK (a heavier TONK on a kill, damped under automatic fire).

## Killstreaks

Pick **3** in LOADOUT. Kills in one life (the count resets when you die) earn them, and they wait in the tray on the right until you press **5 / 6 / 7**. Earned-but-unused ones survive dying.

| Kills | Killstreak |
|---|---|
| 3 | Moon Boots: low gravity + huge jumps for 25 s |
| 4 | Chicken Strike: rain exploding chickens where you aim |
| 5 | Scythe Rifle in slot 4: X switches to rifle mode, hold V to glitch dash |
| 6 | Spinbot: 10 s of aimbot + spinning. You are now a cheater |
| 6 | Wrecking Ball: 20 s as a giant steel demolition ball in third person: ram, chain-swing, ground slam (see below) |
| 7 | Spy Satellite: every enemy shows through walls for 20 s |
| 10 | Giant Duck: a giant black hole where you aim that pulls in everyone but you and eats their momentum |

**Wrecking Ball:** you curl up inside a 2.2 m riveted steel demolition ball (a stripe in your colour, a chain stub on top, your eyes peeking out of a slot) and the camera pulls out behind and above you. No guns for 20 s (a box at the top shows the time left, your speed and what a ram or a slam would do right now), but:
- **Roll:** heavy and fast (about 95 km/h from just pushing), low friction so it keeps rolling, turns slowly, bounces off walls with a clang, falls hard. Space is a small hop, crouch on the floor brakes.
- **Ram:** roll into people. Damage scales with your speed: 2 x your speed in m/s up to rolling top speed (from 6 m/s, so a slow roll barely taps them; 52 at a full-speed roll), then it climbs much faster: about 75 at 31 m/s, 97 at 36, 120 (the cap) from 41. So a chain swing or a big drop into someone is brutal. They get launched the way you were going. Teammates are safe.
- **Chain (E):** the grapple becomes a heavy chain on a crane winch: it hauls you up while you hang or drag along, then lets you swing in long pendulum arcs that keep all your momentum. When it snaps tight your speed turns into swing instead of stopping you. Hold W to pump the swing higher (it only pushes while you're swinging that way). Jump to let go. Hook a person to reel yourself into them.
- **Ground slam (C / Ctrl in the air):** straight down, very fast. The higher you were, the bigger it is: off a small hop it's 30 at the centre across 4 m, from 18 m up or more it's 150 across 10 m, falling off with distance, knocking everyone up and out. It bounces you back up 5 to 12 m (higher the higher you came from) so you can slam again: 1.5 s cooldown, hold crouch to chain them.
- The server judges every ram and slam from its own positions, velocities and map (including how high you got); the client can't claim hits, and a ball hanging up on its chain can't slam the floor below. Slams don't go through walls or floors.
- Code: `public/js/wreck.js` has the ball's looks, its chain, the third-person camera and the HUD box; the rolling, chain and slam physics are in `player.js` (`ballStep`, `ballHookStep`); rams and slams are judged in `server.js` (`tickBalls`, `onSlam`); the numbers are `WRECK` in `shared/weapons.js`.

## Maps

| Map | Size | |
|---|---|---|
| Crate | tiny | one little platform, pure chaos |
| Platform | small | a flat gray slab over a sea of clouds |
| Rooftop | medium | top of a skyscraper above the city, towers to grapple to |
| Suburb | medium | a T-shaped street, two-floor houses with rooms and climbable garages, corner store, park, back alleys |
| Warehouse | large | indoor hall, catwalks, offices, pallet racks, loading yard, pits |
| Desert | large | sand town: walk-in buildings, rooftops, a canyon, market |
| **Bazaar** | large | the Plant & Defuse map (below) |
| Islands | large | floating islands over the ocean |
| Skyline | huge | real towers with floors, sky bridges, a construction site with a crane |
| **Backrooms** | extra large | the biggest by far: an endless yellow maze round a huge hall (below) |

Every map has scenery around it now: plateaus with cliffs down to a valley, mesas and dunes, a city of lit towers below, an ocean, a cloud sea, mountains on the horizon.

**Bazaar** is an original market town built on classic bomb-map rules (the same ones that make Dust 2 work):
- three lanes: **Canal Street** (a long street with a sunken canal you can drop into), the **Market Hall** in the middle (covered, stalls for cover, banners that hide your head but not your feet), and the **Cistern** (an underground tunnel to B)
- defenders spawn about 2.5x closer to both sites than attackers, so they get set up first; every lane ends in a chokepoint (the Canal Gate, the Cistern arch, the mid plaza)
- each site has three ways in for retakes, and its own look: A is a raised tiled terrace with orange canopies, B is a fountain court with blue walls and an arcade
- upper levels: climb the crates in A's approach onto the **Bridge** rooftop overlooking A, the **upper canal walkway**, the **mid gallery** over the hall, go upstairs in the **Spice House** and out onto the balcony over B, or climb onto the **arcade roof** above B

**Backrooms** is an original take on the "Level 0" internet legend: 240 x 240 m of mono-yellow wallpaper, damp beige carpet and buzzing fluorescent panels, sealed in (no sky, nothing outside), with a warm haze that swallows everything past ~100 m:
- the **Hall** in the middle: 64 x 64 m under a 7.5 m ceiling, sparse pillars, freestanding walls (one with a window) and low walls for cover, long fights across it
- around it, the maze: rooms of every size with doorways, long straight halls for sightlines, pillar rooms, the odd dead-end alcove, and a 3 m drop ceiling (you can still jump, and grapple the ceiling)
- a hole in the floor in the south-west drops you into the flooded **Pool Rooms** below; they run north under the west side, and stairs come back up in three places, one of them right into B
- Plant & Defuse: **A** is the **Office** (cubicles, grey-blue carpet) north-east of the Hall, **B** is the **Wet Room** (white tiles, the pool stairs) north-west of it; defenders spawn at the north end, attackers at the south, and rounds are longer here (150 s). In TDM and Tags you spawn all over the map, away from enemies, not back in the lobbies. Bots find their way through the maze with a walk graph (`shared/nav.js`)
- some lights flicker, some are dead, the hum never stops (`public/js/backrooms.js`). you are probably alone

## Accounts, levels, achievements

Sign up from the main menu. Accounts save loadout, cosmetics, character, name card, settings, stats and unlocks on the server and follow you to any device. Guests can play but keep nothing and only get free cosmetics.

- **Stats:** wins, kills, deaths, bot kills, headshots, void kills, best coop wave, top speed, play time (PROFILE).
- **Levels:** XP from kills, bot kills, round wins, coop waves, playtime. **Leaderboard:** wins, kills, speed, coop wave, level.
- Passwords are hashed (scrypt), logins are rate-limited.

## Character

**CHARACTER** on the main menu: your colour (name + outline), skin tone, hair (9 styles, any colour), top (sash, t-shirt, hoodie, jacket, suit, runner jacket, nothing) and bottom (shorts, pants, skirt) with their colours, a head, face and back accessory, your kill effect and your name card. Everyone sees your look. The runner jacket is an oversized hi-vis bomber: the top colour paints its body (hi-vis yellow if you don't pick one), the black panels and reflective tape stay. Capes hang from your shoulders and stream behind you when you're fast, wings flap in the air, backpacks and jetpacks have straps.

Achievement unlocks (accessories, plus one weapon skin):

| Achievement | How | Unlocks |
|---|---|---|
| First Blood | get a kill | Bandana |
| Champion | win 10 rounds | Champion Crown |
| Speed Demon | hit 500 km/h | Racing Helmet |
| Frequent Flyer | hit 1000 km/h | Flight Goggles |
| Survivor | reach coop wave 10 | Hard Hat |
| Void Lord | knock 25 people into the void | Void Cape |
| Sharpshooter | 50 headshots | Visor |
| Knee Trouble | t-bag so hard you explode | Ice Pack |
| No Life | play 5 hours | Jetpack |
| Never Landed | finish a whole match without touching the ground after any spawn | Wings |
| Sniper Royalty | three kinds of sniper kill (below) | **Golden Sniper** (a sniper skin) |

**Never Landed:** be in the match from the start (or join in the first 5 seconds) until the end-of-match screen. After every spawn you get 3 seconds to leave the ground; after that, any touch of a floor, roof, box top or platform ends the run for that match, even a single bhop tick. Walls, the grapple and jump pads (as long as you don't stand on them) are fine, and so is dying: every respawn gives a fresh 3 seconds. A **NEVER LANDED** tag with a little wing shows on the left while your run is clean; **YOU TOUCHED GRASS** when it breaks. Your client reports the touch, and the server also checks your snapshots against the map (resting on a box top twice in a row = landed), so a client that just never reports doesn't get it. Leaving and rejoining doesn't wipe a broken run. Online and Bots matches, logged-in players only.

The Wings used to come from Frequent Flyer: everyone who had Frequent Flyer before the change keeps them (Supabase hosts: run the end of `supabase.sql` once to add the new columns and grandfather them; until then the server skips just those stats and logs a hint).

**Sniper Royalty → the Golden Sniper.** Get each of these Sniper kills at least once, in any order, over any number of matches: a **LONG SHOT** (50 m or more, measured by the server from its own positions), a **QUICK-SCOPE / NO-SCOPE** (either one: fired within 0.35 s of the scope fully coming up, or without the scope at all) and a **HEADSHOT**. One kill can tick several. Every new tick pops a gold toast (`SNIPER ROYALTY 2/3  QUICK-SCOPE / NO-SCOPE`) with the three boxes; the boxes also show in the achievements list here, and in COSMETICS > Sniper when you hover the locked skin. The last one plays the achievement unlock plus a big gold GOLDEN SNIPER UNLOCKED, and the skin goes straight onto your sniper.
- Logged-in players only (a guest is told what would have counted: "log in so it counts"). Kills on bots count too; training dummies don't.
- Anti-farm: a kill on someone who hadn't really moved for 5 s (the server tracks it from the snapshots; respawning or being knocked around doesn't count as moving) never ticks a box, so no farming it on an AFK player or a friend standing still.
- Quick-scope and no-scope are the shooter's word (`qs: 1` / `ns: 1` on sniper hits), so they only ever buy progress, never damage, and claiming both at once counts for neither.

## Name cards, killcam, play of the round

- **Name card:** a 256x64 banner. CHARACTER → EDIT NAME CARD: brush, spray, fill, text, eraser, colour picker, preset backgrounds, or **UPLOAD IMAGE** (it gets cropped to fit). Saved as a small JPEG. If you don't make one you get a generated card. Other players can turn uploaded cards off in Settings.
- **Killcam:** when someone kills you, you watch the last ~4 seconds over their shoulder in slow motion at the end, with their name card. Skip with Space or click. You respawn when it ends (turn it off in Settings for instant respawns).
- **EPIC kills can't be skipped:** the server decides at kill time, from its own positions: any kill from 60 m+, a headshot from 40 m+ (sniper, revolver, bow: one careful bullet), mid-air (nothing under any part of you for 3 m) or grappling or 300+ km/h from 30 m+, on under 10 HP from 25 m+ (not if you hurt yourself this life, e.g. coughing), a no-scope from 20 m+, or two of those at once from 20 m+. Distances are scaled per weapon (a 28 m shotgun kill counts as far; the AR needs a bit more; melee counts 2.5x but only up to its reach). Rockets, arrows, slippers and the rest count from where (and how) you fired them, and not at all if you died before they landed. The victim's killcam turns into TOO EPIC TO SKIP: more build-up, slower, punches in on them, EPIC SHOT · 64m when it lands, and the server holds their respawn until it's over (about 8 s, never past the 9 s killcam cap). The killer gets UNSKIPPABLE. Killcam off in Settings still means no killcam. Bots never get one, and there are none in Coop or Training. Never epic: a victim who hadn't moved for 5 s (respawning or getting shoved around doesn't count as moving; running while being shot does), kills credited to you after they fell or coughed themselves to death, spinbot (aimbot) kills, chicken strikes, shots bounced back by a reverse card, burn / gas ticks. A knife backstab isn't a headshot. Speed has to be real (the server checks how far you actually went) and a grapple has to be within hook range. Play of the round prefers epic kills. Rules in `shared/epic.js`.
- **Play of the round:** the server keeps a short recording, scores every kill (multikills, speed, distance, void kills, headshots) and plays the best one for everyone when the round ends, with that player's name card. Nobody can skip it. Then the scoreboard.

## Cosmetics + containers

**Skins** are different models and belong to one weapon each, like a CS knife: every weapon has at least one (Toy Blaster and Bullpup for the AR, Pocket Uzi, Double Barrel, Old Gatling, Musket and the Golden Sniper, Flintlock, Turkey Launcher, Hand Cannon, Bunch Blaster, Compound Bow, Fat Cigar, Hair Dryer, Champagne, Skip Card, Ice Cube, Ladle, Croc, Reaper scythe, plus Karambit / Butterfly / Switchblade / Cleaver / Bowie / Kitchen knives, Foam Finger and Bear Paw slappers, the Croissant).
The **Golden Sniper** is never in a crate: it's the reward for the Sniper Royalty achievement (see Character) and the server only lets you wear it once you have it. Gold plate with darker gold scrollwork, jewels set in the receiver, a small jewelled crown on the scope and a glint that hops around the metal; everyone sees it, and it stays gold under any wrap.
**Wraps** (paint), **hats** and **effects** go on **every weapon at once** by default (untick the box in COSMETICS to dress weapons one by one). The Scythe Rifle and the items you hold up (Party Popper, Reverse Card) can be dressed too. One **kill effect**, one **grapple skin** and one **spray** per player.

**CONTAINERS** (main menu) is where you open them:

| Container | Contains |
|---|---|
| Crate | weapon skins |
| Duffel Bag | hats, effects, kill effects, grapples |
| Box | wraps, sprays |

New accounts get one of each. Win a round (Online needs 2+ real players, Bots needs 3+ bots) for a random container; coop gives one every 5 waves. Odds: Common 55%, Rare 28%, Epic 13%, Legendary 4%. Own everything in a type and it turns into 100 XP.

**Kill effects** (what happens to people you kill): Gibs, Confetti (free), Tombstone, Make It Rain, Missing Texture, Balloons, Chickens, Blue Screen, Yeet, Ascend, Big Duck, Blast Zone (knocked clean off the screen: they rocket away and a burst of colour jets back at the map).

**Grapple skins** (your rope and the thing on the end, everyone sees it, each lands with its own sound): Rope + iron hook (free), Chain + claw, Candy Cane, Plunger, Jungle Vine + wooden hook, Laser + emitter, Sticky Hand (stretchy), Rainbow + star. Pick one in COSMETICS (hover a card to try it in the preview).

**Sprays** (press **Z**): graffiti you paint where you're looking, up to 6 m away. Flat on walls, turned to face you on floors and ceilings, cut off at edges and doorways. One per player (a new one replaces your old one), every 10 s, wiped when the map changes; people who join later still see them. Free: GG (the default), EZ, WP, GL. From boxes: L, NOOB, ?, OOF (common), RIP, Heart, Smiley (rare), Skull, Flame, Rubber Duck (epic), the rainbow JANKFIRE logo (legendary). Pick yours in COSMETICS.

The hotbar at the bottom shows a picture of each weapon you carry, with your skin on it, plus your item and its charges.

## Movement

- **No speed cap.** Jump on the tick you land and friction never touches you.
- Air strafe to gain speed. Grapple, then jump to launch off the rope with your momentum.
- **The grapple is a pendulum rope** (`shared/hookphys.js`, the same one for bots): a steady pull toward the point plus a reel that winds in, it keeps your swing so you go round in arcs, and catching a fall or reaching the point eases in instead of snapping. The camera leans into the rope a little. **Grapple jump:** let go with a fling along your swing plus a hop, on top of your momentum (more on the upswing, swinging the way you look).
- Self-launch: shotgun the floor, chicken rocket your feet, minigun downward, bread a wall, leaf blower, frag grenade, party popper (G: aim down to fly up, aim at a wall to fly off it).
- Fall into the void and whoever hit you in the last 10 s gets the kill.

## Tripo models (optional)

```bash
TRIPO_API_KEY=tsk_your_key npm run models
```

Prompts live in `tools/models.json`; models land in `public/models/<id>.glb` and load on refresh, skins still apply.

## How it works

- `server.js`: static files + WebSocket `/ws`. Rooms: shared Online and Coop, private Bots and Training. Movement is client-authoritative; the server owns HP, kills, projectiles, arrows, cards, items, frost, streaks, modes (teams, tags, the bomb), the map/mode vote, cosmetics ownership, achievements, round recordings for highlights, and bots (including their objective routes and grappling).
- `server/`: accounts, stats, containers, leaderboard (`/api/*`), stored in a local file or Supabase.
- `shared/`: `map.js` maps + box physics + bot routes · `modes.js` game modes, teams, bomb rules, vote timing · `weapons.js` weapons, items, killstreaks, loadout rules · `cosmetics.js` skins/wraps/effects/kill effects/hats + crates · `looks.js` character outfits · `verdict.js` the Scales of Justice verdict (server decides, client previews) · `epic.js` EPIC kill rules · `hookphys.js` the pendulum grapple rope (players and bots) · `homing.js` homing slippers · `wand.js` soap-bubble traps · `nav.js` walk graphs for maze maps (Backrooms bots) · `lava.js` Floor Is Lava's floor + safe ground.
- `public/js/`: `main.js` menus + net + loop · `player.js` movement · `weapons.js` viewmodels, recoil springs, ADS, items · `anim.js` swing/inspect keyframes (per-knife styles) · `speedlines.js` · `remote.js` other players · `replay.js` killcam + highlights · `killfx.js` kill effects · `royal.js` Sniper Royalty toasts + the Golden Sniper unlock · `scales.js` Scales of Justice: verdict readout, tipping beam, pendulum pans, stamps · `sprays.js` sprays (drawn on a canvas, decals cut to the map) · `cards.js` name cards · `objective.js` bomb sites, tags, team bar · `icons.js` hotbar/item/streak pictures · `models.js` · `skins.js` · `fx.js` · `world.js` · `scenery.js` the land around each map · `hud.js` · `audio.js` · `shredder.js` · `bloodcross.js` · `gungame.js` + `infection.js` · `chaos.js` the chaos modes · `backrooms.js` the Backrooms' hum, flicker and visitor.
- `desktop/`: the Electron app (launcher, in-app server, display modes).
