# Hub mini-games

Added 18 Nov 2026. The owner asked:

> "At the tables for the lobby hub can you add mini games that can actually be played, like arm wrestling based on
> hitting skill checks, another table has chess/checkers, maybe the arcade machine you can play like a mini version of
> the game against bots??"

There are three games. Each is a self-contained model that the server builds on a spot in the hub:

| Game | What you do | Alone |
|---|---|---|
| **ARM WRESTLING** | Two seats across a table, your avatar's own right hand clasped with theirs (IKControls). Timing checks: a needle sweeps a bar, hit the zone. A hit pushes the arms your way, a perfect hit more, a miss gives ground. The zone shrinks and the needle speeds up over 24 s. First to pin the other's hand wins: the slam, a recorded thud, a ring off the pin pad, the camera shakes. | A mannequin bot sits down: EASY, MEDIUM, HARD. |
| **CHESS · CHECKERS** | One table, pick the game at the table. Full chess rules (castling, en passant, promotion to a queen, check, mate, stalemate, the 50-move rule, threefold repetition, too little material). English checkers (captures forced, men take forward only, crowning ends the move, draw after 80 quiet moves or a threefold repeat). The server checks every move. RESIGN, OFFER DRAW, ACCEPT/DECLINE; 180 s a move. Anyone can stand and watch. | A bot (minimax with alpha-beta). Chess: depth 1 with noise, 3, 4. Checkers: 2 with noise, 4, 8. It takes a draw only when it is losing. |
| **ARCADE** | The camera goes into the cabinet's screen and the screen takes over: a top-down JANKFIRE in a walled yard with cover. You face waves of bots: grunts keep their distance and shoot, rushers charge, heavies spray. You have three of the game's guns (Redline, Shotgun, Sniper) and a dash. Kills in a quick chain score x1 to x3, and a cleared wave adds a bonus and some health. | Always solo. The per-server high scores show on the cabinet's screen, or who is playing and their score. |

## Rules for all three

- **Where:** hub only. The training zone is allowed too, if a spot is ever put there.
  - Never in a match or a map room. The server checks `Zones.of`, the client checks `MenuGate.allowed("minigame")`.
  - A player who leaves the hub, dies or walks off is taken out of the game.
- **Joining:** a ProximityPrompt (E, pad X, or click).
  - Tables: "Sit" on a free seat, or "Challenge" on a bot's seat between bouts or games.
  - Cabinet: "Play".
- **Leaving:** any time, with Backspace, pad B (PadNav calls back), the LEAVE button, or Space where the game has no use for it.
  - Mid-play it asks twice. Leaving forfeits the bout, resigns the game, or ends the run (the run still counts).
- **Nothing to farm:** no loot, currency, quests or stats. Only fun and the arcade's high-score board, which is per server and never saved.
  - The server sanity-checks a run's score against its length before it goes on the board.
- **The anti-cheat:** a seated body counts as "seat" in AntiCheat's `support()`. Every server move of a body here stamps `TeleportT` first. The furniture never moves.

## Files

- `shared/MiniGames.luau`: the config.
  - `L` is the layout in each model's own frame (origin = the spot's floor centre, -Z = its look).
  - Also the arm wrestling tuning (`ARM`), the bot depths (`BOARD`), the arcade's sanity numbers, and the fallback `SPOTS`.
- `shared/Chess.luau`, `shared/Checkers.luau`: the rules and the bots. They are pure, so the server plays the game and each client shows the legal moves.
  - Chess passes perft from the start position (20 / 400 / 8902), Kiwipete (48 / 2039) and position 3 (14 / 191 / 2812).
- `server/MiniGames.server.luau`: building on the spots, seats, joining and leaving, the zone and distance watch, the bots' bodies, the remote `JankfireRemotes.MiniGame`.
  - Test hook `ServerStorage.JankMiniTest` (Studio): `state`, `sit` (player, table id, side), `leave`, `op` (player, data), `spots`.
- `server/MiniArm.luau`, `server/MiniBoard.luau`, `server/MiniArcade.luau`: each game's server half.
- `client/MiniGames.client.luau`: the core.
  - The world look for everyone.
  - Your game's screen (`JankMiniGame`): the camera, MenuCursor "minigame", `LoadoutOpen`, the controls off, prompts hidden, leaving.
  - Test hooks: player attribute `MiniTest` = `leave` | `back` | `space` | a module's own (`arm:press`, `arm:perfect`, `board:pick:<sq>`, `board:move:<from>,<to>`, `arcade:start`, `arcade:auto`, `arcade:die`). `MiniState` holds the answer.
- `client/MiniArmUI.luau`, `client/MiniBoardUI.luau`, `client/MiniArcadeUI.luau`: each game's screen and look.
- `tools/roblox/minigame_models.py`: the furniture and pieces in Blender, built the chunky way (the knight's head and the king's cross are remeshed into their bodies).
  - It becomes one upload, asset 134966926271798.
  - `studio-tools/MiniGameImport.luau` puts it into `ReplicatedStorage.JankfireMiniGames.Kit`.

## Spots

The hub's builder drops spot markers:

- An invisible Part anywhere under `workspace.Map.Hub`.
- Tagged `MiniGameSpot`.
- Attribute `Game` = `"arm"` | `"board"` | `"arcade"`.
- Its CFrame is the footprint's centre on the floor.
- Its look: the arcade's screen faces it, and a table's seats sit at ±look.
- Clear room needed:
  - arm: 11 x 6 studs;
  - board: 11 x 7, plus room to watch;
  - arcade: 4.5 studs in front.

Since place v966 the hub's builder (the hub session's lobby) makes the three markers in `Rotunda.Scenery`, and remakes them on every rebuild:

- arm wrestling on the lobby's east rug, between two palms;
- chess and checkers on the west rug, mirrored;
- the cabinet against the east arcade's north wall, where the hub's old arcade prop stood.

`MiniGames.SPOTS` (fallback spots, used only when the map has no markers) is kept empty. The first fallback picks were overlapped by the lobby's sofas within the hour.

## Tested (18 Nov 2026, place versions 956 and 975)

Tested in solo Play in Studio, with the anti-cheat's movement checks on (`StudioOn`):

- **Against the bots:**
  - Arm wrestling vs the EASY bot: the countdown, the bout, the slam, YOU WIN, then AGAIN.
  - Chess vs the MEDIUM bot: e4, and the bot answered Nf6, with the legal-move dots showing.
  - The arcade: a run to wave 2, then game over. 1,800 points went on the server board as "BEST IN THE SERVER", and the cabinet's screen showed it.
- **Two players**, using the Studio stand-in second player (a seated body the server treats as a person, with its moves sent as a client's would be):
  - an arm wrestling bout with both sides pressing;
  - four chess moves, the stand-in's illegal move refused, its draw offer, and ACCEPT, giving "DRAW AGREED".
- **The anti-cheat:** joining, sitting, playing and leaving all three games gave 0 points and no verdicts.
- **Not tested:** two real clients (Studio's MCP runs only a solo Play test), a real controller, a real phone, and checkers played through to the end (only its rules and its bot were checked, in Edit).

Photos are in `docs/minigames/`:

- `minigames_sheet.jpg`: arm wrestling against the stand-in, the draw offer at the board, an arcade run, and the cabinet in the lobby.
- The kit renders.
- Two shots from before the 18 Nov camera fix, where a big avatar's accessories and title blocked the table.

## Your look at the tables (19 Nov 2026, place version 1001)

The owner said: "when I sit down at the table all my accessories come off and im bald". The 18 Nov camera fix had hidden every accessory on your own screen while you sat at a table. Now:

- **Your whole look stays.** Hair and accessories are never hidden wholesale.
- **The cameras look past your head:**
  - arm wrestling: high behind you and a little to the left, about 2 studs over your head, down onto the grip;
  - the board: high over your right shoulder.
- **A measured fade instead:**
  - The game lists what the camera must see in `api.viewPoints`: the clasp and the pin pads, or the board's corners and middle.
  - If a line from the camera to one of those points crosses an accessory's part box, that one accessory fades to 0.6, and only while it blocks.
  - Hair never fades.
- **Your title over your head** stays hidden on your own screen while you sit.
- **Everything comes back:** standing up, leaving, and dying mid-game all put it back.
- **Tested** on the owner's avatar (9 accessories, including hair and a big cake): all 9 stay fully shown at the arm table, the board and the cabinet. After a death mid-game, the screen, camera, movement and prompts all return.
- **Photos:** `docs/minigames/seated_*.jpg`.

**The arm-wrestling camera since place version 1003** is side-on, like a broadcast shot (main, 19 Nov):

- It sits on your right, 6.6 studs out from the locked hands and 1.7 above them, turned 10° toward your end.
- Both players are seen from the side, with the hands in the middle of the frame.
- At 30° the owner's big hat stood in front of the hands, so it was cut to 10°.
- Winning still moves the hands to the left of the screen, like the meter.
- The slam's shake stays.
- Photo: `docs/minigames/seated_arm_side.jpg`.

## Your crosshair at the games (19 Nov 2026, place version 1010)

The gun's crosshair sat in the middle of the screen, over the locked hands and the board (main, 19 Nov). `FightHud.step` now hides it while the server's `MiniGame` player attribute is set: seated at a table, at the cabinet, or in the ring. It comes back the moment you leave. The scythe's charge circles follow it, as they follow the crosshair everywhere.

## BOXING (19 Nov 2026, place version 1010)

The owner asked: "when you step into the ring can it be a boxing mini game? perfect dodge, counter b low, upper cut jab, hook, we can look through mixamo for those! weave duck you know !"

**Where:** the hub gym's ring.

- The hub's builder drops a `MiniGameSpot` with `Game = "box"` at the middle of `RingMat`'s top, its look along the ring's right (`RingMatLine`).
- Until that marker is live, the server falls back to the `RingMat` part itself, giving the same spot.
- The two corners stand at ±2.3 studs along the look. The prompts "Box" sit at ±4.6.

**Joining:** the "Box" prompt in either corner.

- Alone: BOT · EASY, MEDIUM or HARD.
- Two people: both step in and the bout starts.
- LEAVE works like the other games. Mid-bout it asks twice and you forfeit.
- Gloves are welded on for the bout only: the kit's `mg_glove` (one fused fist, cream cuff, a thin gold band), sized to your hand. Corner A is muted red, B muted blue. On R6 the glove sits at the end of the arm.

**Offence** (wind-up / recovery in seconds, damage, stamina):

| Move | Wind-up | Recovery | Damage | Stamina | Notes |
|---|---|---|---|---|---|
| JAB | 0.20 | 0.22 | 5 | 5 | fast, short |
| HOOK | 0.36 | 0.38 | 11 | 10 | big; your right hand, so it arrives on their left |
| UPPERCUT | 0.48 | 0.45 | 16 | 15 | big; x1.4 into a duck |
| BODY | 0.30 | 0.34 | 8 | 8 | the low shot: a block doesn't stop it; drains 10 of their stamina |

**Defence:**

- **BLOCK** (held): a blocked punch does 15-25% of its damage and costs the blocker 7 stamina. Holding it drains stamina. A block at 0 stamina is no block. It never stops a body shot.
- **DUCK:** slips jabs and hooks for 0.42 s, and eats the uppercut.
- **WEAVE** left or right: slips the jab, the uppercut and the body shot, and a hook only from the side you weave to (the tell shows an arrow).
- **A perfect dodge:** a dodge that starts in the last 0.15 s before the punch lands.
  - The world slows to 0.3 speed for 0.4 s and the camera leans in.
  - An amber ring and "PERFECT · COUNTER" appear.
  - The puncher is left open for 0.75 s.
  - Your punch in the next 0.9 s is a COUNTER: x1.8 damage, a faster wind-up, and always big.

**Feel:**

- A landed big punch freezes both bodies for 0.085 s (hit-stop), with a ring at the spot and a light shake.
- A knockdown gets a heavier shake.

**Bars and winning:**

- Health 100 and stamina 100 for both. Stamina refills at 15 a second after 0.6 s without punching. A punch thrown without the stamina it costs does half damage.
- A knockdown at 0 health: up after 4 s with 55, then 40, then 25.
- The third knockdown ends it: KNOCKOUT.
- Otherwise it goes to the most damage over 3 rounds of 45 s, with 5 s rests (+12 health each).

**The bot** reads your wind-up and dodges, blocks, or takes the hit. Difficulty sets:

- its own wind-up (x1.7, x1.35, x1.12: easy is slow and readable);
- how often it reads you (18%, 38%, 58%);
- its reaction time;
- feints (0, 12%, 25%);
- how often it blocks.

**Controls:**

- **Keyboard and mouse:** click JAB, right click HOOK, E UPPER, S + a punch BODY, F BLOCK (held), C or Ctrl DUCK, Q / R WEAVE.
- **Pad:** RT jab, RB hook, Y upper, X body, LT block, A duck, a flick of the left stick or the d-pad weaves.
- **Touch:** buttons.
- A short keys line sits at the bottom. No other text.

**Camera:** a side-on 3/4 shot from your right, 9.5 studs out, turned 14° toward your corner. Your whole look stays (the table rules).

**Animations:**

- Mixamo mocap retargeted to R15 with `tools/blender/mixamo_r15.py`, uploaded as 12 animations: idle bounce, jab, lead and rear hooks, uppercut, body jab, high block, head, big and body hits, knockdown, get-up.
- The ids are in `MG.BOX.CLIPS`.
- Duck, weave and the open stagger are procedural poses.
- An R6 body gets procedural poses for everything.
- The FBX files stay in the vault (`JANKFIRE Vault/Assets/mixamo-18nov-boxing`), never in git.

**Sounds:** recordings only, no crowd or voices:

- `hurt` and `bread_bonk` for a landed punch, with `lasso_slam` on a big one;
- `land` for a block;
- `swing` for a dodge;
- `wave_fly` for a perfect dodge;
- `bowl_hit` for a knockdown;
- `door_vip_bell` pitched down for the bell.

**Files:**

- `server/MiniBox.luau`: the bout, the rules, the bot.
- `client/MiniBoxUI.luau`: poses, clips, the screen, input, the camera.
- `MG.BOX` and `L.box` in `shared/MiniGames.luau`.
- `tools/roblox/boxing_models.py`: the glove, asset 93628648477968. `MiniGameImport.MORE` merges it into the kit.

**Test hooks:**

- `JankMiniTest:Invoke("sit", p, "box1", "A")`, then `("op", p, { op = "bot", level = "easy" })`.
- A second boxer: `("standin", "box1", "B", nil, "r6")`, with `("as", "box1", "B", { op = "act", a = "hook", t = now })`.
- Client `MiniTest`:
  - `box:auto`: perfect-dodges every punch and counters;
  - `box:<act>`, `box:block:on|off`;
  - `box:hold:<s>`: freezes your next perfect dodge for a photo.

**Tested** in solo Play on the owner's R15 avatar against the EASY bot:

- Five perfect dodges in a row, each followed by a big counter.
- Three knockdowns, the get-ups between them, and YOU WIN · KNOCKOUT with the bot and AGAIN buttons.
- An R6 stand-in in corner B: gloves at the ends of its arms, its guard and hook poses.
- No crosshair while in the ring; it is back after leaving.
- The anti-cheat with `StudioOn`: 0 points, no verdicts.
- The first test found the gloves staying on after you left. `ctx.leave` clears the seat before the game's `left` hook runs, so the hook couldn't find your body. Fixed in place version 1013 (the leaver is passed in), and checked: 2 gloves during the bout, none after leaving.

**Photos:** `docs/minigames/box_*.jpg`: the side shot mid-hook (with the tell), the knockdown, the KO, and the R6 stand-in.
