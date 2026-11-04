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
- Any Node host with WebSockets works (Railway, Fly.io, a VPS). The server reads `PORT`.

## Controls

| | |
|---|---|
| WASD | move |
| Shift | run |
| Space | jump (hold to bhop). Jump while grappling to launch off the rope with your momentum |
| C / Ctrl | crouch; crouch while fast to slide. Spam it too long and your knees explode. As the Wrecking Ball: ground slam (in the air) / brake |
| Left mouse | fire / swing / play a card / draw the bow (hold, release) |
| Right mouse | aim down sights · **Knife: heavy stab** · Card Deck: pick a card |
| E / mouse side buttons | grapple (hold) |
| R | reload (Card Deck: redraw) |
| F | inspect your weapon · **Plant & Defuse: hold F to plant / defuse** |
| G | **use your item** (grenade, medkit, shield bubble, duck, smoke) |
| 5 / 6 / 7 | **use your killstreaks** (the tray on the right shows which are ready) |
| 1 / 2 / 3, wheel, Q | primary / secondary / melee, last weapon. 4 = Scythe Rifle if you have it |
| V (hold) / X | Scythe Rifle: glitch dash / switch to rifle mode |
| 1 / 2 / 3 (between rounds) | vote for the next map + mode |
| Space / click | skip a killcam or the play of the round |
| B / Esc | pause menu · Tab scoreboard · T / Enter chat |

Settings: display (windowed / windowed fullscreen / fullscreen), grapple on right click instead, toggle aim, sensitivity, ADS sensitivity, fov, fov kick, shake, blood, fps counter, quality, speed lines, killcam, show other players' uploaded name cards.

## Modes

| Where | What it is |
|---|---|
| Play | Online with real people, one shared room. After every match everyone votes on the next map + mode. |
| Bots | Private match vs 1-12 bots. Pick the mode, map, difficulty and hipfire. |
| Coop | Everyone vs endless waves of bots. No friendly fire. A container every 5 waves. |
| Training | Target dummies, infinite ammo, a movement playground. Good for testing kill effects and the katana. |

Game modes (Play + Bots):

| Mode | Rules |
|---|---|
| Deathmatch | everyone for themselves, first to the kill limit |
| Team Deathmatch | red vs blue, first team to the kill limit. No friendly fire. |
| Tags | kills drop a tag. Grab enemy tags to score, grab your own team's to deny them. |
| Plant & Defuse | attackers carry the bomb to site A or B and hold F to plant (3 s). Defenders stop them or hold F to defuse (5 s). First to 4 rounds, sides swap after round 3. |
| Randomizer | everyone gets a random loadout every life |

Bots play the objectives too: they carry and plant the bomb, defuse it, and grab tags. They also use the grapple to chase, to get up high, and to save themselves from the void.

**Match Settings** (pause menu): map, hipfire accuracy, bot difficulty, bot count, and (in Bots) the mode.

## Weapons

- **Primary:** Assault Rifle, SMG, Shotgun, Minigun, Sniper, Chicken Rocket, Bowling Ball Launcher, Bow, Peel Shooter
- **Secondary:** Revolver, Cigarette (smoke it, blow fire), Leaf Blower, Card Deck, Party Popper, Reverse Card, **Snowball**
- **Melee:** Bread, Slipper (throw it, it comes back), Knife, Hand Slapper (point blank, launches + makes them slip), **Katana**, Spoon, **Scales of Justice**
- **Item (G):** Frag Grenade (x2, bounces, 2 s fuse, grenade-jump with it), Medkit, Shield Bubble (nothing from outside hurts anyone inside for 7 s), Rubber Duck (black hole), Smoke Bomb (x2), **Bubble Wand** (x2, seals enemies in floating soap bubbles). Charges refill over time.

**Only the minigun shoves people with bullets**: hold it on someone and they get pushed away (the price for spraying). Melee and explosives still knock people around, and your own movement tricks (shotgun jumps, minigun flying) still work.

**Knife (CS-style):** left click alternates diagonal slashes, right click is a heavy stab (windup, 90 damage, a backstab kills). Every knife skin moves like its real-world family: the Butterfly's handles flip around the blade, the Karambit spins on your finger through the ring, the Switchblade flicks open, the Kitchen knife rolls like a bayonet, the Bowie does a barrel-roll toss, the Cleaver balances on a fingertip.

**Katana:** the blade gets longer (and reaches further) with every kill you get with it. Resets when you die.

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

**Snowball:** barely hurts, but every hit adds frost. 4 hits freezes them solid for a moment; hit a frozen target and they shatter.

**Bubble Wand (item):** G blows a stream of 4 slow, wobbly soap bubbles (2 charges, 15 s to refill each; they float about 10 m). The first enemy one touches is sealed in a giant soap bubble for 5 s: no moving, shooting, items or streaks, just looking around while it floats them up (2 m/s) and away from you (1.5 m/s). Then it pops and drops them: no fall damage, but over the void that's your kill. Any hit (bullet, melee, projectile, explosion) pops it instead of hurting them, so teammates can shoot a friend free and enemies can wait until they're over the void (shoot it open there and the kill is yours). You, your teammates, anyone in a Shield Bubble and a rolling Wrecking Ball can't be bubbled; blow one at someone with a Reverse Card up and you're the one floating away. After a pop nobody can be bubbled again for a while: 1.5 s, or 60% of however long they were in (3 s after a full float), so two wands can't keep someone in one for good. Inside, everything sounds underwater and the world wobbles behind a rainbow soap film.

**Bow:** hold to draw, release to fire. Every arrow gets a random tip, shown on the HUD: regular, power, knockback, flame, explosion, gas, sleep.

**Card Deck:** you hold 5 cards from a real 54-card deck. Right click picks, left click flicks it out of the fan, R redraws.
Hearts heal by the number · Spades throw that many cards · Clubs blast people back · Diamonds dash you forward · Aces teleport you · J / Q / K are ultimates · Jokers fire a random ultimate.

**Aim down sights:** the rifles, SMG, revolver and peel shooter have real iron sights (the shotgun has a bead), and ADS lines the sight up with the exact middle of the screen with the gun below it. Launchers, the minigun and the bow stay low and to the side. Hats tuck away while you aim.

**Feel:** springy recoil with camera punch, muzzle flashes, ejected shells, shotgun pump and sniper bolt after each shot, smear trails on swings, a tiny freeze when a melee hit connects, draw animations, weapon sway, speed lines when you go fast.

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
| 10 | Giant Duck: a giant black hole where you aim that pulls in everyone but you |

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

Every map has scenery around it now: plateaus with cliffs down to a valley, mesas and dunes, a city of lit towers below, an ocean, a cloud sea, mountains on the horizon.

**Bazaar** is an original market town built on classic bomb-map rules (the same ones that make Dust 2 work):
- three lanes: **Canal Street** (a long street with a sunken canal you can drop into), the **Market Hall** in the middle (covered, stalls for cover, banners that hide your head but not your feet), and the **Cistern** (an underground tunnel to B)
- defenders spawn about 2.5x closer to both sites than attackers, so they get set up first; every lane ends in a chokepoint (the Canal Gate, the Cistern arch, the mid plaza)
- each site has three ways in for retakes, and its own look: A is a raised tiled terrace with orange canopies, B is a fountain court with blue walls and an arcade
- upper levels: climb the crates in A's approach onto the **Bridge** rooftop overlooking A, the **upper canal walkway**, the **mid gallery** over the hall, go upstairs in the **Spice House** and out onto the balcony over B, or climb onto the **arcade roof** above B

## Accounts, levels, achievements

Sign up from the main menu. Accounts save loadout, cosmetics, character, name card, settings, stats and unlocks on the server and follow you to any device. Guests can play but keep nothing and only get free cosmetics.

- **Stats:** wins, kills, deaths, bot kills, headshots, void kills, best coop wave, top speed, play time (PROFILE).
- **Levels:** XP from kills, bot kills, round wins, coop waves, playtime. **Leaderboard:** wins, kills, speed, coop wave, level.
- Passwords are hashed (scrypt), logins are rate-limited.

## Character

**CHARACTER** on the main menu: your colour (name + outline), skin tone, hair (9 styles, any colour), top (sash, t-shirt, hoodie, jacket, suit, nothing) and bottom (shorts, pants, skirt) with their colours, a head, face and back accessory, your kill effect and your name card. Everyone sees your look. Capes hang from your shoulders and stream behind you when you're fast, wings flap in the air, backpacks and jetpacks have straps.

Achievement accessories:

| Achievement | How | Unlocks |
|---|---|---|
| First Blood | get a kill | Bandana |
| Champion | win 10 rounds | Champion Crown |
| Speed Demon | hit 500 km/h | Racing Helmet |
| Frequent Flyer | hit 1000 km/h | Wings |
| Survivor | reach coop wave 10 | Hard Hat |
| Void Lord | knock 25 people into the void | Void Cape |
| Sharpshooter | 50 headshots | Visor |
| Knee Trouble | t-bag so hard you explode | Ice Pack |
| No Life | play 5 hours | Jetpack |

## Name cards, killcam, play of the round

- **Name card:** a 256x64 banner. CHARACTER → EDIT NAME CARD: brush, spray, fill, text, eraser, colour picker, preset backgrounds, or **UPLOAD IMAGE** (it gets cropped to fit). Saved as a small JPEG. If you don't make one you get a generated card. Other players can turn uploaded cards off in Settings.
- **Killcam:** when someone kills you, you watch the last ~4 seconds over their shoulder in slow motion at the end, with their name card. Skip with Space or click. You respawn when it ends (turn it off in Settings for instant respawns).
- **Play of the round:** the server keeps a short recording, scores every kill (multikills, speed, distance, void kills, headshots) and plays the best one for everyone when the round ends, with that player's name card. Then the scoreboard.

## Cosmetics + containers

**Skins** are different models and belong to one weapon each, like a CS knife: every weapon has at least one (Toy Blaster and Bullpup for the AR, Pocket Uzi, Double Barrel, Old Gatling, Musket, Flintlock, Turkey Launcher, Hand Cannon, Bunch Blaster, Compound Bow, Fat Cigar, Hair Dryer, Champagne, Skip Card, Ice Cube, Ladle, Croc, Reaper scythe, plus Karambit / Butterfly / Switchblade / Cleaver / Bowie / Kitchen knives, Foam Finger and Bear Paw slappers, the Croissant).
**Wraps** (paint), **hats** and **effects** go on **every weapon at once** by default (untick the box in COSMETICS to dress weapons one by one). The Scythe Rifle can be dressed too. One **kill effect** per player.

**CONTAINERS** (main menu) is where you open them:

| Container | Contains |
|---|---|
| Crate | weapon skins |
| Duffel Bag | hats, effects, kill effects |
| Box | wraps |

New accounts get one of each. Win a round (Online needs 2+ real players, Bots needs 3+ bots) for a random container; coop gives one every 5 waves. Odds: Common 55%, Rare 28%, Epic 13%, Legendary 4%. Own everything in a type and it turns into 100 XP.

**Kill effects** (what happens to people you kill): Gibs, Confetti (free), Tombstone, Make It Rain, Missing Texture, Balloons, Chickens, Blue Screen, Yeet, Ascend, Big Duck.

The hotbar at the bottom shows a picture of each weapon you carry, with your skin on it, plus your item and its charges.

## Movement

- **No speed cap.** Jump on the tick you land and friction never touches you.
- Air strafe to gain speed. Grapple, then jump to launch off the rope with your momentum.
- Self-launch: shotgun the floor, chicken rocket your feet, minigun downward, bread a wall, leaf blower, party popper recoil.
- Fall into the void and whoever hit you in the last 10 s gets the kill.

## Tripo models (optional)

```bash
TRIPO_API_KEY=tsk_your_key npm run models
```

Prompts live in `tools/models.json`; models land in `public/models/<id>.glb` and load on refresh, skins still apply.

## How it works

- `server.js`: static files + WebSocket `/ws`. Rooms: shared Online and Coop, private Bots and Training. Movement is client-authoritative; the server owns HP, kills, projectiles, arrows, cards, items, frost, streaks, modes (teams, tags, the bomb), the map/mode vote, cosmetics ownership, achievements, round recordings for highlights, and bots (including their objective routes and grappling).
- `server/`: accounts, stats, containers, leaderboard (`/api/*`), stored in a local file or Supabase.
- `shared/`: `map.js` maps + box physics + bot routes · `modes.js` game modes, teams, bomb rules, vote timing · `weapons.js` weapons, items, killstreaks, loadout rules · `cosmetics.js` skins/wraps/effects/kill effects/hats + crates · `looks.js` character outfits · `verdict.js` the Scales of Justice verdict (server decides, client previews).
- `public/js/`: `main.js` menus + net + loop · `player.js` movement · `weapons.js` viewmodels, recoil springs, ADS, items · `anim.js` swing/inspect keyframes (per-knife styles) · `speedlines.js` · `remote.js` other players · `replay.js` killcam + highlights · `killfx.js` kill effects · `scales.js` Scales of Justice: verdict readout, tipping beam, pendulum pans, stamps · `cards.js` name cards · `objective.js` bomb sites, tags, team bar · `icons.js` hotbar/item/streak pictures · `models.js` · `skins.js` · `fx.js` · `world.js` · `scenery.js` the land around each map · `hud.js` · `audio.js`.
- `desktop/`: the Electron app (launcher, in-app server, display modes).
