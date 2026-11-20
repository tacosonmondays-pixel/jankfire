# The katana: endless parry, crit return, slash wave

The owner asked for this on 18 Nov 2026 (about 02:10 UTC): "allow katana parry to parry as many bullets but if you
manually swing it to counter bullets it does a crit return! build enough parry and you can send a large forward slash
like getsugatensho".

The anime attack was only a feel reference. The wave is our own design: a wide crescent in the katana's quiet ice blue
(`9fe8ff`), with no borrowed name, shape or colours.

What we built:

1. **The guard holds.** Right click now stays up while it's held, and blocks every bullet and pellet that reaches you from the front.
2. **A timed swing returns bullets.** A left-click swing that meets incoming bullets sends them back at the shooter for double damage.
3. **The wave.** Everything you parry fills a small meter. When it's full, one key sends a wide slash wave forward.

The server decides all of it; clients only draw it.

Names, used in code comments and this doc only, never on screen (`no-flavour-text`):

- **Return to Sender** is the crit return.
- **Cold Front** is the slash wave.

On screen, the only words are the quiet callouts under the crosshair, the same kind the parry already had: `PARRY!`,
`PERFECT PARRY!` and `CRIT RETURN` (Hud `KINDS`: small).

## 1. The held guard

| | |
|---|---|
| Input | right click (`aim` bind), hold. Toggle aim: one press up, the next press down. Phone: the AIM button (it toggles) |
| How long | as long as it's held, up to **1.5 s** (`PARRY.hold`). A tap still gives the old **0.35 s** (`PARRY.win`) |
| What it stops | **every** bullet and pellet from the front arc (**140°**, ±70° side to side; straight above or below always counts), and swords |
| Perfect | the first **0.15 s** of each guard (+0.05 s network slack) sends the bullets home at ×1, as before |
| Cooldown | **0.8 s** after a tap, growing evenly to **1.4 s** after a full 1.5 s hold (`PARRY.cd` + `PARRY.holdCd` × share held) |
| Turning | while it's held, its front follows your look (the client sends its yaw 10 times a second: `PARRY.turn`) |
| Training | no cooldown (the owner's rule for the training hall and playground) |

**Why these numbers.**

- **Full blocks.** The longest automatic sprays still get fully blocked: a whole SMG burst of 16 a second for over a second, the LMG, a shotgun's ten pellets.
- **Cost.** The guard can be up at most about half the time: a 1.5 s hold, then 1.4 s down.
- **Counterplay.** You can't swing while guarding. Side and back shots still land, and so do explosions.
- **What it beats.** It beats a lone sprayer in front of you. It doesn't beat a flank or a team that waits out the 1.5 s.

**On screen.**

- The parry ring at the crosshair is full while the guard is up. It drains over that guard's own cooldown and blinks when the guard is ready again.
- First person and third person both hold the guard pose for as long as it's up: `Viewmodel.holdAt` and `ThirdPerson.holdKat`.
- Everyone else sees your guard go up (`guard`) and come down (`guardEnd`).
- In a spray, the first bullet gets the full spark, sound and jolt. Each one after it gets a smaller spark and a lighter jolt. Their sounds are spaced at least 85 ms apart, so a 16-a-second spray doesn't turn into a buzz.

## 2. Return to Sender: the crit return

| | |
|---|---|
| Input | a plain katana swing (left click) |
| When | bullets that reach you **0.02 to 0.20 s** after the click, the blade's sweep (`CRIT.from` / `CRIT.to`, +0.04 s slack) |
| Where from | the swing's own front: where you looked as you swung (sent with the swing), **110°** wide (±55°) |
| Payout | the same bullets go into the shooter at **×2** damage (`CRIT.mul`); a Sniper headshot stays lethal. No damage to you |
| Credit | the katana (`"parry"`, which Stats, Quests, Modes and the finishers already count as the katana's) |
| Cost | the swing's 0.5 s cooldown, and a bullet one frame outside the window simply hits you |

**Why.**

- **Timing.** The window is the length of the blade's visible sweep, shorter than the guard's and much shorter than a held guard. You must swing into the shot you expect: the sniper's next shot, the shotgunner's next pump, the middle of a spray.
- **Reward.** A guard only blocks. A swing pays double, and a skilled player gets it in exchange for risking the hit.
- **Examples.** A Sniper body shot returns 110. A Shotgun's ten pellets return 160. Four SMG bullets caught in one swing return 56.

**What you see and hear.**

- **At the blade:** a sharp four-point star flash, an ice halo, hard white streaks thrown back and a quick light.
- **The line home:** a bright white line with an ice core runs back to the shooter, thicker and longer-lived than a perfect parry's.
- **Sound:** its own recording, `crit_return` (a metal "sever" hit layered with a sword hit, 1.5 dB over `parry_perfect`).
- **In your hands:** a 0.16 s hit-stop and a small ice-white screen flash.
- **Third person too:** everyone sees the flash and the line.

## 3. The edge meter

**What fills it:** points equal to the damage of what you stopped:

| What you did | Points |
|---|---|
| Guarded a bullet | its damage ×1 |
| Perfect parry | its damage ×1.25 |
| Crit return | its damage ×1.5 |
| Parried a sword | 30 (perfect: 40) |
| Guarded a wave | half the wave's damage |

All of it is ×3 in training. Teammates' shots never count.

| | |
|---|---|
| Full | **240** points (`EDGE.max`) |
| Emptied | by the wave, or by dying (a new life starts empty) |

**Why 240.** It takes real work, but it's reachable within one fight:

- about 34 SMG bullets guarded (two held guards against a sprayer);
- or four Sniper shots;
- or three Shotgun blasts;
- or one good crit return plus a guard.

**On screen.** Five small bars inside the weapon plate, where a gun's ammo count sits. They show only while the katana is out, and carry no text.

- **Filling:** the bars fill ice blue, and each new piece flashes white for a moment.
- **Full:** they turn bright and pulse softly, and `edge_full` (a quiet blade ring) plays for you only.
- **Pressed too early:** the bars blink.

**Server side.** The meter is the server's (`f.edge`). Clients read it from the player attributes `Edge` (0 to 1) and `EdgeFull`.

## 4. Cold Front: the slash wave

| | |
|---|---|
| Input | **Q** (keyboard), **D-pad left** (controller), the phone's **WAVE** button (shown with the katana out, lit when full). Rebind: Settings → KEYBINDS → WEAPONS → "KATANA SLASH WAVE" (`Binds` id `wave`) |
| Needs | the katana out, the meter full, not staggered, not guarding, not mid-swing |
| Leaves | **0.12 s** after the key (`WAVE.windup`), from your chest, along your look (pitch kept within ±20°) |
| Flies | **180 studs/s** (60 m/s) for up to **120 studs** (40 m): about 0.67 s to full range |
| Hit box | **18 studs** (6 m) side to side, **6 studs** (2 m) top to bottom round its line (a jump over it can dodge it) |
| Damage | **70** to each enemy it passes through, at most **3**, each once, plus a shove along it (9 m/s, 4 up) |
| Stops | at the first wall on its line; at its third victim; on a guard (or a crit swing) facing it, which takes no damage and gets half the wave's damage in meter points |
| Through cover | never: the line from the wave's middle to the victim must be clear |
| Credit | the katana (`"katana"`: it grows the blade, counts in Stats, Quests, finishers) |
| Lock | no swing or guard for **0.45 s** after the key (`WAVE.lock`) |

**Why.**

- **Not a free kill.** 70 doesn't kill from full health. A wave plus one katana hit (48) does.
- **Rewarding for teams.** It can catch a group in a doorway.
- **Answerable.** It travels at 60 m/s and is 2 m tall, so a jump at the right moment clears it.
- **The guard beats it.** A guard facing it breaks it, so it is an opener, not a guaranteed finisher.

**The look (ours, quiet).**

- **The shape:** a wide crescent of camera-facing light, built from three layers. A hot pale core edge leads, an ice-blue glow surrounds it, and a dimmer deep-blue body trails a stride behind. Its tips sweep back and up, and it is rolled 9° like a real slash.
- **In flight:** frost motes and small four-point glints shed behind it, and an ice light rides with it.
- **When it hits:** a white-ice flash and streaks on the victim.
- **On a wall:** a burst of ice shards and glints, a flash and a light pop. At full range it just fades.

**What you hear.**

- `wave_cast` as it leaves.
- `wave_fly`, positional, which rides with the wave.
- `wave_hit` on a body.
- `wave_wall` where it breaks.

**Third person.** Everyone sees the slash on the caster's body (a `swing`), the crescent, its hits and its break.

**Your own wave is drawn the moment you press.** If the server doesn't accept it within 0.9 s (a meter that had just been spent), it fades quietly.

## 5. Mocap: the moves from the Katana Combat Pack

On 20 Nov 2026 the owner bought robloxanimations.com's "Katana Combat Pack - 34 Animations" (BuiltByBit 117603). The
kill-effects session vetted it, and main asked for it on the katana. The hand-made poses for these moves are replaced
by the pack's motion capture:

- **Third person:** what everyone sees on your body.
- **First person:** your blade.

**The licence.** The pack's files stay in the vault (`Documents\JANKFIRE Vault\Tools\Packs-20nov\katana-combat\`) and
never go in git. Only the clips we use are published, as Animations on the owner's account. Their ids are the only part
of the pack that is ours.

All the ids are in one shared table, `src/shared/PackAnims.luau` (`PackAnims.katana.*`). Cinematic-finishers' Tidecrest
uses the same full-body Equip / Unequip uploads.

| Move | Pack clip (R15) | Uploaded as | Played at | So that |
|---|---|---|---|---|
| Held guard | Animations Block (2 s; up by 0.1 s, then still) | upper body, 86655046417517 | ×1.4, frozen at 0.1 s while held | the guard is up in 0.07 s and stays up |
| A parry lands (the guard's first hit, a perfect one, a sword) | Animations DeflectedUp | upper, 100089422703963 | ×1 | the blade knocked up; the Block comes back while you still hold |
| Swing 1 / 2 / 3 (the combo) | BasicAttackTypes Light01 / 02 / 03 | upper, 95363076019189 / 94835463875042 / 132114568020105 | ×1.389 / ×1.389 / ×2.083 | each clip's own hit marker (0.167 / 0.167 / 0.25 s) lands on the katana's `hitT` 0.12 s; the blade's trail falls inside the crit window (0.096-0.19, 0.12-0.22, 0.14-0.20 s) |
| Your swing parried | Stagger Types KatanaParry Left | upper, 140232916534684 | ×1 | the 0.67 s clip covers the 0.55 s stagger |
| The wave's cast | BasicAttackTypes Ultimate, from 0.4 s | upper, 122543974629370 | ×1.389 | its swing marker lands on the 0.12 s wind-up, as the crescent leaves |
| (finishers) | Animations Equip / Unequip, full body | 87695619849581 / 109417036578604 | | Tidecrest |
| (spare) | Animations Equip, upper | 127861015989285 | | the katana's own draw still uses the hand-made clip |

"Upper body" means the legs are dropped and the root and lower torso unweighted, so the moves play over a walk or a run.
The clips keep the pack's own timing and markers. The speed is set when they play, so the gameplay numbers don't
change: the clips follow the timing.

**Third person** (`ThirdPerson.luau`, the scythe's route; R15 bodies):

- **Playing:** your own client plays the clip on your own Animator, which replicates to everyone. Everyone else's
  client spots it by its id each frame (`stepRig`) and blends the waist, neck and right arm to it.
- **The katana:** sits in the animated right hand the way the pack holds its own. Its blade runs along the hand's −Z,
  with our handle's grip on the hand's middle. The left hand stays on the hilt by IK.
- **The held guard:** freezes your Block track (`AdjustSpeed(0)`) at its hold time while the button is down
  (`TP.holdKat`). It stops it on release.
- **R6 bodies** keep the hand-made katana poses (the `KAT` rows), as the scythe's mocap does.

**First person** (`Anims.luau` rows `kat_*`, from `tools/roblox/katana_vm.py`):

- **The blade points** where the pack's blade points as its swinger sees it. The turn blends in from our rest hold over
  the clip's first moment.
- **The grip** moves 0.4 of the pack hand's move, never nearer the eye than 0.32 m, nor above eye level. For the Block
  it moves 0.25 and stays 0.12 m below eye level, so the guard doesn't cover the crosshair.
- **Arsenal plays** `kat_light1..3` as the katana's 3-hit chain (the scythe's chain counter), `kat_block` for the guard
  (held at its `hold`), `kat_deflect`, `kat_stagger`, and `kat_wave` from the wave key.
- **The old clips** (`swing_katana`, `parry_katana`, ...) stay as fallbacks.

**Tools:**

| Command | What it does |
|---|---|
| `py -E -P tools/roblox/katana_pack.py <pack.rbxm> list` | every clip, its length and markers |
| `... export <clip> <out.rbxm> --upper` | one clip as an Animation file, outside the repo |
| `... hand <clip> <out.json>` | the right hand through the clip, by forward kinematics on the pack's own rig |
| `py -E -P tools/roblox/katana_vm.py <hand.json> <name> --speed k ...` | the first-person row |

The pack's binary reader runs nothing in the file.

**Photo hooks (Studio):**

- **Your first person:** the player attribute `KatanaClip` plays an `Anims` row, and `VMClipHold` freezes it.
- **A third-person stand-in:** a `TPRig` body with `TPMocap = "kat_light1:0.17"` freezes a pack clip at that clip time;
  `TPKatPose` freezes the old pose.

### Mocap results (20 Nov 2026, one solo Play in training, place v1118)

The test used an R15 player and two stand-ins: an R15 copy and an R6 body. Before and after:
`docs/katana/mocap-before-after-v1118.jpg`. The gameplay numbers (Weapons PARRY / CRIT / EDGE / WAVE) didn't change.

| Check | Result |
|---|---|
| Held guard, 18-round SMG spray at 16/s, button held 1.7 s | 18 of 18 parried, meter full (240). The Block played at ×1.4, then held still at 0.12 s (speed 0) until release. The deflect played on the first hit, and the Block came back while still held |
| 3-hit combo, clicks 0.38 s apart under a 20-round spray | Light01 / 02 / 03 played at ×1.389 / ×1.389 / ×2.083, and the server logged 8 crit returns |
| Your swing parried (the server's melee parry Fx) | KatanaParry Left played |
| Wave with a full meter, Q | the Ultimate played at ×1.389, and the server flew the crescent (2 hits, then its end) |
| Third person | the R15 stand-in takes each clip (`TPMocap`); the R6 stand-in keeps the hand-made `KAT` poses |
| Errors | none from these scripts in the output |

**Left as is:**

- **Same-frame deflects:** three bullets landing in the same frame start the deflect three times. Each start replaces
  the last, so only one shows.
- **The first-person Block:** points the blade down and to the left across the view, where the pack's swinger has it.

**Not checked:** a second player's view (it uses the scythe's route, which was checked in v979), an R6 player's own body
(R6 keeps the `KAT` keys), and a phone.

## Server authority, anti-cheat

- **The guard.** `Rules.parryStart` / `parryStop` / `parryTurn` / `parryAt` own its timing. A client that never lets go still gets at most 1.5 s, then the full cooldown. The yaw a client sends can only turn the guard while it's up, and Combat's message budget limits how often.
- **The crit.** `Rules.critAt` checks the server's own swing record: its time, and the yaw the swing came with. The bullet's direction comes from the shooter's position as the server knows it.
- **The meter.** It moves only through `Katana.charge`, called from the server's own parry and crit results.
- **The wave.** The server flies it (`Katana.step`) and refuses a key press without a full meter. It finds the victims itself, and sends its own wall distance to everyone.
- **Anti-cheat.** Nothing new moves the caster. The wave's shove goes through `Fight.hurt` → `Fight.knock`, which the anti-cheat already reads as a push.

## Files

**Server and shared:**

- `src/shared/Weapons.luau`: the numbers, `PARRY` (hold, holdCd, turn), `CRIT`, `EDGE` and `WAVE`, plus the katana's description. `Roster.luau` holds the long description.
- `src/server/Rules.luau`: the held guard (`parryStart` / `parryOpen` / `parryCd` / `parryReady` / `parryStop` / `parryTurn` / `parryAt`), `critAt`, and the swing's yaw. Unit tests in `tests/weapons.luau`.
- `src/server/Combat.server.luau`: the Parry remote (down, `"turn"`, `false` = let go), and the crit check before the guard in `applyHitscan`. Parried shots charge the meter, and the swing carries its yaw.
- `src/server/Katana.luau` (new): the meter, the crit payout, the wave, and the test hook.

**Client:**

- `src/client/Katana.client.luau` (new): the meter HUD, the wave key, every crescent, the crit flash, and others' held guards.
- `src/client/Arsenal.client.luau`: the held guard's input, its pose and ring, and the swing's yaw. A spray's parries play smaller.
- `src/client/Viewmodel.luau` (`VM.holdAt`) and `ThirdPerson.luau` (`TP.holdKat`).
- `Hud.luau` (`CRIT RETURN` small), `Binds.luau` (`wave`) and `TouchControls.client.luau` (WAVE button).

**Project and sounds:**

- `default.project.json`: the RemoteEvent `KatanaWave`. `Katana.luau` also makes it if a place lacks it.
- Sounds: `crit_return`, `wave_cast`, `wave_fly`, `wave_hit`, `wave_wall` and `edge_full`, added by the sounds session (place v749, `docs/SOUNDS.md`, all Pro Sound Effects recordings).

## Testing

`ServerStorage.JankKatanaTest` exists in Studio only.

| Call | What it does |
|---|---|
| `("state", p)` | the guard, the swing and the meter |
| `("edge", p, pts)` | sets the meter |
| `("spray", p, { by = "Stand", w = "smg", n = 18, rate = 16 })` | a stand-in shooter: a dummy fires through the real hitscan path (guard, crit, meter), with tracers |
| `("cast", p, look)` | sends a wave with no meter |
| `("log", "clear")` | returns the last 120 events |

**Photos:** set the client attribute `KatanaFreeze` (on the player) to `"crit"` or `"wave"`. It freezes the effect clocks, this script's and `Fx`'s (`FxTimeScale`), a moment into the next crit flash or wave flight.

**Recipe:** solo Play, then:

1. `workspace:SetAttribute("ZoneCull", false)` on the server.
2. `JankTest "arm" { "katana", "smg", "revolver" }`.
3. Stamp `TeleportT`, then `PivotTo` 15 studs in front of a training `Stand`, with a wall behind it.
4. Put a waiter on the server: when `state.open` turns true, spray. Then hold right click.
5. For the crit: when `state.swingT` is fresh, spray six rounds. Then click.
6. For the wave: set the Stand's HP to 60 and press Q.

### Results (18 Nov 2026, solo Play in training, place v769 / v770)

The stand-in shooter was a training `Stand`, firing through the real hitscan path (`JankKatanaTest "spray"`, so the
guard, crit and meter code all ran). All four checks passed, with no script errors.

| Check | What happened |
|---|---|
| Spray fully parried | 18 SMG rounds at 16 a second during one held guard: all 18 parried, 0 HP lost. The guard closed at the let-go after 1.4 s |
| Crit return by swing | A real left click, then the Stand fired six rounds the moment the swing reached the server. The first four (the swing's window) went back at ×2: 14 each, 56 off the Stand. The last two, 0.25 s and 0.31 s in, hit me (2 × 4.9) |
| Meter filling | 0 → 240 (full) from that one spray (training ×3). +126 from the four crits. Shown in the plate as 5 bars, full ones glowing |
| Wave | From a full meter, in the Stand's direction: it passed through a Stand (70, alive) and a 60 HP Stand (killed). It stopped on the wall behind them, 35.5 studs out (`waveEnd wall`). The first run hit one Stand and stopped at 33.5 |

**Photos** in `docs/katana/`:

- `katana-sheet.jpg`: all four in one sheet.
- `wave-midflight-v769.jpg`: the wave mid-flight, frozen 0.055 s into its flight.
- `crit-return-flash-v770.jpg`: the crit flash, frozen 0.03 s in, as the defender sees it. A first version at the blade, 1.6 studs from the eye, filled a sixth of the screen. Your own flash now sits a stride further out and at half the size.
- `hud-meter-v769.jpg` and its zoomed crop: the meter at 70%.

**Test traps.**

- `JankTest "all"` lists more than one fighter named `Stand`. The spray hook fires from the FIRST one, so take positions from the first match. My first run held the guard facing the wrong Stand, and every bullet rightly got through.
- A `user_mouse_input` `moveTo` can turn the first-person camera. Point the camera (`CFrame` once, Custom) after the move, then press.
- Once mid-test, keys and clicks stopped reaching the game. The direct remotes still work for the server's side:
  - `Parry:FireServer(yaw)` and `(yaw, false)`;
  - `Swing:FireServer("katana", nil, yaw)`;
  - `KatanaWave:FireServer(look)`.
- For a side photo, set the client's `LoadoutOpen = true` while the camera is Scriptable. Otherwise ShoulderCam's watchdog puts the camera back after 0.7 s.

**Not checked in Play:**

- the phone's WAVE button (its row and visibility are code-only);
- a second player seeing your guard hold, the crescent and the flash. Others' clients get the same Fx events; the third-person guard hold goes through `TP.holdKat`;
- the Lune unit tests (`tests/weapons.luau` updated for the held guard and the crit). Lune isn't installed on this PC.
