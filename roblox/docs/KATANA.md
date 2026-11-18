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

### Results

(filled in after the Play test)
