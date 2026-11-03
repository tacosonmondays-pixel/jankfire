# JANKFIRE

A low quality multiplayer FPS. Infinite momentum, a grappling hook, real guns, weapons that should not exist, killstreaks, and janky mannequins that fall apart when they die.

Three.js client (rendered crunchy on purpose, PS1 wobble on weapons) + one small Node WebSocket server. Every sound is synthesized. Every model is boxes, unless you plug in Tripo.

## Play it

### Windows app (exe)

Grab `JANKFIRE-1.0.0-win.zip`, unzip it anywhere, run **JANKFIRE.exe**. No browser and no Node install needed. The launcher gives you:

- **PLAY ONLINE**: connects to the official server (set in `desktop/config.json`, see below).
- **HOST ON THIS PC**: runs the server inside the app. Friends on your wifi join with the address it shows.
- **JOIN ADDRESS**: type a friend's address or any JANKFIRE server URL.

In game the main menu has CHANGE SERVER, FULLSCREEN and QUIT GAME.

An installer (`JANKFIRE Setup.exe`) and a single-file portable exe are built on Windows: push the repo to GitHub and the **Build desktop app** action (`.github/workflows/build-desktop.yml`) produces them under Actions → Artifacts. Or on a Windows PC: `npm install` then `npm run dist:win`.

To make **PLAY ONLINE** point at your hosted server, put its URL in `desktop/config.json` before building:

```json
{ "officialServer": "https://jankfire-xxxx.onrender.com" }
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
| C / Ctrl | crouch; crouch while fast to slide. Spam it too long and your knees explode |
| Right mouse | aim down sights (Card Deck: pick a card) |
| E / mouse side buttons | grapple (hold) |
| Left mouse | fire / play card / draw the bow (hold, release to shoot) |
| R | reload (Card Deck: redraw) |
| F | inspect your weapon (melees have special ones) |
| 1 / 2 / 3, wheel, Q | primary / secondary / melee, last weapon. 4 = Scythe Rifle if you have it |
| G | use a pocket killstreak (Chicken Strike, Giant Duck) |
| V (hold) / X | Scythe Rifle: glitch dash / switch to rifle mode |
| Space / click | skip a killcam or the play of the round |
| B / Esc | pause menu · Tab scoreboard · T / Enter chat |

Settings: grapple on right click instead (aim moves to E), toggle aim, sensitivity, ADS sensitivity, fov, fov kick, shake, blood, fps counter, quality, **killcam on/off**, **show other players' uploaded name cards**.

## Modes

| Mode | What it is |
|---|---|
| Play | Online free-for-all with real people, one shared room. Rounds: first to 20 kills or 6 minutes. |
| Bots | Private FFA vs 1-12 bots. Pick map, difficulty, hipfire. First to 15 or 5 minutes. |
| Coop | Everyone vs endless waves of bots. No friendly fire. A container every 5 waves. |
| Training | Target dummies, infinite ammo, a movement playground. Good for testing kill effects. |

**Match Settings** (pause menu) change the room for everyone: map, hipfire accuracy, bot difficulty, bot count.

## Weapons

- **Primary:** Assault Rifle, SMG, Shotgun, Minigun, Sniper (huge knockback), Chicken Rocket, Bowling Ball Launcher, **Bow**, Peel Shooter
- **Secondary:** Revolver, Cigarette (smoke it, blow fire), Leaf Blower, **Card Deck**, Party Popper, Reverse Card, Rubber Duck (black hole)
- **Melee:** Bread, Slipper (throw it, it comes back), **Knife** (backstabs do triple), **Hand Slapper** (point blank, launches + makes them slip), Spoon

**Bow:** hold to draw, release to fire. Every arrow gets a random tip, shown on the HUD: regular, power (faster, harder), knockback, flame (sets them on fire), explosion, gas (a poison cloud), sleep (they pass out).

**Card Deck:** you hold 5 cards from a real 54-card deck, shown at the bottom of the screen. Right click picks, left click plays, R redraws.
Hearts heal by the number · Spades throw that many cards · Clubs blast people back · Diamonds dash you forward · Aces teleport you where you aim · J / Q / K are ultimate versions of their suit · Jokers fire a random ultimate.

## Killstreaks

Kills in one life (reset when you die):

| Kills | Reward |
|---|---|
| 3 | Moon Boots: low gravity + huge jumps for 25 s |
| 4 | Chicken Strike (G): rain exploding chickens where you aim |
| 5 | **Scythe Rifle** in slot 4: X switches to rifle mode, hold V to glitch dash (up to 5 s, contact hits) |
| 6 | Spinbot: 10 s of aimbot + spinning. You are now a cheater |
| 7 | Spy Satellite: every enemy shows through walls for 20 s |
| 10 | Giant Duck (G): a giant black hole that pulls in everyone but you |

## Maps

| Map | Size | |
|---|---|---|
| Crate | tiny | one little platform, pure chaos |
| Platform | small | a flat gray slab, nowhere to hide |
| Rooftop | medium | top of a skyscraper, towers to grapple to, long fall |
| Suburb | medium | a T-shaped street, two-floor houses with rooms and climbable garages, corner store, park, back alleys |
| Warehouse | large | indoor hall, catwalks, offices, pallet racks, loading yard, pits into the void |
| Desert | large | sand town: walk-in buildings, rooftops, a canyon, market |
| Islands | large | the original floating islands |
| Skyline | huge | real towers with floors, sky bridges, a construction site with a crane |

Maps are box lists in `shared/map.js`.

## Accounts, levels, achievements

Sign up from the main menu. Accounts save loadout, cosmetics, character, name card, settings, stats and unlocks on the server and follow you to any device. Guests can play but keep nothing and only get free cosmetics.

- **Stats:** wins, kills, deaths, bot kills, headshots, void kills, best coop wave, top speed, play time (PROFILE).
- **Levels:** XP from kills, bot kills, round wins, coop waves, playtime. **Leaderboard:** wins, kills, speed, coop wave, level.
- Passwords are hashed (scrypt), logins are rate-limited.

## Character

**CHARACTER** on the main menu: body colour, a head, face and back accessory, your kill effect and your name card. Everyone sees your look on your mannequin.

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

Every weapon has its own: **skin** (a different model, e.g. Karambit, Butterfly, Switchblade, Cleaver, Bowie for the knife; Foam Finger, Bear Paw for the slapper; Croissant for bread), **wrap** (the paint: Gold, Chrome, Carbon Fiber, Tiger, Fade, Lava, Galaxy, Rainbow, Missing Texture...), **hat** (sits on the weapon) and **effect** (particles). Plus one **kill effect** per player.

| Container | Contains |
|---|---|
| Crate | weapon skins |
| Duffel Bag | hats, effects, kill effects |
| Box | wraps |

New accounts get one of each. Win a round (Online needs 2+ real players, Bots needs 3+ bots) for a random container; coop gives one every 5 waves. Open them in COSMETICS. Odds: Common 55%, Rare 28%, Epic 13%, Legendary 4%. Own everything in a type and it turns into 100 XP.

**Kill effects** (what happens to people you kill): Gibs, Confetti (free), Tombstone, Make It Rain, Missing Texture, Balloons, Chickens, Blue Screen, Yeet, Ascend, Big Duck.

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

- `server.js`: static files + WebSocket `/ws`. Rooms: shared Online and Coop, private Bots and Training. Movement is client-authoritative; the server owns HP, kills, projectiles, arrows, cards, streaks, cosmetics ownership, achievements, round highlights and bots.
- `server/`: accounts, stats, containers, leaderboard (`/api/*`), stored in a local file or Supabase.
- `shared/`: maps, box physics, weapons, cosmetics, character looks.
- `public/js/`: `main.js` menus + net + loop · `player.js` movement · `weapons.js` viewmodels · `anim.js` swing/inspect keyframes · `remote.js` other players · `replay.js` killcam + highlights · `killfx.js` kill effects · `cards.js` name cards · `models.js` · `skins.js` · `fx.js` · `world.js` · `hud.js` · `audio.js`.
- `desktop/`: the Electron app (launcher + in-app server).
