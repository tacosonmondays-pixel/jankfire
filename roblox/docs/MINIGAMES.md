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

## BOXING (19 Nov 2026, place versions 1010 to 1019)

The owner asked: "when you step into the ring can it be a boxing mini game? perfect dodge, counter b low, upper cut jab, hook, we can look through mixamo for those! weave duck you know !", then: "I want to freely move in the boxing arena!"

**Where:** the hub gym's ring.

- The hub's builder drops a `MiniGameSpot` with `Game = "box"` at the middle of `RingMat`'s top, its look along the ring's right (`RingMatLine`). It is live since place version 1012.
- Without a marker, the server falls back to the `RingMat` part itself, giving the same spot.
- Each round starts with the boxers on their marks, ±3 studs along the look (out of reach of each other). The "Box" prompts sit at ±4.6.

**Free in the ring** (since place version 1016):

- You walk the ring with WASD, the left stick, or a stick that appears under your left thumb on a phone (the game's own phone stick hides while you play).
  - The pace is the guard's: JANKFIRE's run (30 studs/s) x 0.55, about a Roblox walk. The full run would cross the 22-stud ring in under a second.
  - You always face the other boxer (an `AlignOrientation` on your root), so you circle them.
  - No jumping.
- **The ropes are walls.** Your own client puts up four invisible walls at the ropes that only you collide with, so nobody else is fenced in. The server keeps a bot inside too. Walking far past the ropes (a fall, a teleport) takes you out of the game.
- **STEP:** a quick dash-step in the direction you're moving, or straight back with no keys.
  - Keys: Space, a direction tapped twice, pad LB, or the phone's STEP button.
  - About 3.5 studs, braked at the end.
  - Costs 6 stamina, at most one every 0.4 s.
- Duck, weave and block all work while you move.
- **A punch is a real hit in space.** The server judges it, never your client. It lands only if, when judged, the other boxer is:
  - within its reach (middle to middle, flat);
  - inside 50° of where you face.
  - Otherwise it is a WHIFF: a whoosh at your fist, and 0.18 s more recovery.
  - With a person in the bout, reach gets 0.35 studs of slack, because the server sees their body a moment late.
  - Stepping out of reach is a dodge too, but gives no counter.
- During a knockdown the downed boxer can't move. Both are back on their marks for each round.

**Joining:** the "Box" prompt in either corner.

- Alone: BOT · EASY, MEDIUM or HARD.
- Two people: both step in and the bout starts.
- LEAVE works like the other games. Mid-bout it asks twice and you forfeit.
- Gloves are welded on for the bout only: the kit's `mg_glove` (one fused fist, cream cuff, a thin gold band), sized to your hand. Corner A is muted red, B muted blue. On R6 the glove sits at the end of the arm.

**Offence** (wind-up / recovery in seconds, damage, stamina, reach in studs):

| Move | Wind-up | Recovery | Damage | Stamina | Reach | Notes |
|---|---|---|---|---|---|---|
| JAB | 0.20 | 0.22 | 5 | 5 | 3.9 | fast, the longest |
| HOOK | 0.36 | 0.38 | 11 | 10 | 3.3 | big; your right hand, so it arrives on their left |
| UPPERCUT | 0.48 | 0.45 | 16 | 15 | 3.0 | big; x1.4 into a duck; the shortest |
| BODY | 0.30 | 0.34 | 8 | 8 | 3.5 | the low shot: a block doesn't stop it; drains 10 of their stamina |

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

**The bot** reads your wind-up and dodges, blocks, or takes the hit. It walks on its own feet: its own Humanoid, the server's physics, owned by the server. Its torso and head are solid, so you bump into it rather than through it.

- **Footwork:**
  - It hovers just out of your jab (5.0 / 4.8 / 4.6 studs) and circles, turning round every 1.2 to 2.8 s and off the ropes.
  - When it decides to punch, it steps in to that punch's reach, then closes a little more during the wind-up. The tell shows all of it.
  - After a punch or a hit it sometimes backs off (20 / 40 / 55%).
  - Medium and hard sometimes answer your wind-up by slipping out of reach (20 / 30%).
- **Difficulty** (easy / medium / hard) also sets:
  - its own wind-up: x1.7, x1.35, x1.12 (easy is slow and readable);
  - how often it reads you: 18%, 38%, 58%;
  - its reaction time;
  - feints: 0, 12%, 25%;
  - how often it blocks;
  - its pace: 8, 10, 12 studs/s.

**Controls:**

- **Keyboard and mouse:** WASD walk, Space STEP (or a direction tapped twice), click JAB, right click HOOK, E UPPER, X (or the middle button) BODY, F BLOCK (held), C or Ctrl DUCK, Q / R WEAVE.
  - S is now walking back, so it no longer turns a punch into a body shot.
- **Pad:** the left stick walks, LB step, RT jab, RB hook, Y upper, X body, LT block, A duck. The d-pad or a flick of the right stick weaves; flicking it down ducks.
- **Touch:** a stick under your left thumb. On the right: JAB, HOOK, UPPER, BODY, BLOCK, DUCK, STEP, ◀ and ▶.
- A short keys line sits at the bottom. No other text.

**Camera:** behind and above you, swung 44° round to your right, always turned toward the other boxer.

- It sits 7.2 studs out plus 0.4 x the gap, and 3.9 studs up plus 0.15 x the gap, looking at a point 55% of the way to them. As the gap grows it pulls back to keep you both in frame.
- The first try (38°, 8.5 out) framed both boxers too small. The 44° shot shows the bot's face, its gloves and the tell.
- The core eases it, so it swings round gently as you circle. A big hit shakes it lightly; a perfect dodge's slow beat narrows it a little.
- Straight behind, the owner's big avatar hid the bot, hence the swing to the side.
- Your whole look stays (the table rules). Only an accessory that really blocks the other boxer's head or middle fades to 0.6, and hair never fades.

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

- `server/MiniBox.luau`: the bout, the rules, where the bodies are (reach and cone), the bot and its footwork.
- `client/MiniBoxUI.luau`: poses, clips, the screen, input, your feet (walls, facing, STEP, the phone stick), the camera.
- `MG.BOX` and `L.box` (`bound`, `wall`, `cam`) in `shared/MiniGames.luau`.
- The core:
  - `MiniGames.server`: `ctx.toMark` and the walking bot body (`MiniFace`).
  - `MiniGames.client`: `api.move(on)` turns your controls on, and `api.walk(dir)` feeds a direction through the control module's own hook, so `Move.client` takes it as input.
- `Body.mini` (Body.luau, used in Move.client's speed): the guard's pace. Put back to 1 when you leave.
- `tools/roblox/boxing_models.py`: the glove, asset 93628648477968. `MiniGameImport.MORE` merges it into the kit.

**Test hooks:**

- `JankMiniTest:Invoke("sit", p, "box1", "A")`, then `("op", p, { op = "bot", level = "easy" })`.
- A second boxer: `("standin", "box1", "B", nil, "r6")`, with `("as", "box1", "B", { op = "act", a = "hook", t = now })`.
- Client `MiniTest`:
  - `box:auto`: perfect-dodges every punch and counters;
  - `box:<act>`, `box:block:on|off`;
  - `box:hold:<s>`: freezes your next perfect dodge for a photo;
  - `box:walk:<F|B|L|R>:<s>`: walk that way for s seconds, relative to facing the other boxer;
  - `box:step:<F|B|L|R>`: a STEP that way.
  - Clear `MiniTest` on the server before each command. The client clears it only on its own side, so the same value sent twice would not replicate.

**Tested with free movement** (place version 1016, solo Play, owner's avatar, EASY bot):

- The bot walks: it stepped in, circled, and threw from range. Its body punches at 3.9 and 4.6 studs whiffed (reach 3.5 + 0.35).
- Walking back to 5.1 studs and jabbing gave `whiff:A:jab:5.0`.
- Circling left for 1.6 s took you from 27° to 155° around the bot, still facing it (dot 0.98).
- Perfect dodges into counters (`perfect:A:hook`, then `hit:B:hook:big,counter`), with the PERFECT · COUNTER line and the amber ring.
- The anti-cheat with `StudioOn`: 0 points, no verdicts, no catches.
- Again at place version 1019 with the autopilot:
  - KNOCKOUT in 30 s: the bot down three times, you never, and the server kept the bot's body.
  - An R6 stand-in: gloves at the ends of its arms, turned to face you. Its hook landed once you walked into reach.
  - After leaving, everything was back: turning, jumping, no walls, normal pace, the normal camera, no gloves.
  - Anti-cheat: 0 points again.
- Fixed during that test:
  - The bot's body had been handed to the player's physics. The server now takes it back once a second.
  - The screen's PERFECT/COUNTER line never showed. Its event pattern read the whole rest of the event as "who".

**Tested with the fixed stance** (place versions 1010 and 1013, solo Play on the owner's R15 avatar, EASY bot):

- Five perfect dodges in a row, each followed by a big counter.
- Three knockdowns, the get-ups between them, and YOU WIN · KNOCKOUT with the bot and AGAIN buttons.
- An R6 stand-in in corner B: gloves at the ends of its arms, its guard and hook poses.
- No crosshair while in the ring; it is back after leaving.
- The anti-cheat with `StudioOn`: 0 points, no verdicts.
- The first test found the gloves staying on after you left. `ctx.leave` clears the seat before the game's `left` hook runs, so the hook couldn't find your body. Fixed in place version 1013 (the leaver is passed in), and checked: 2 gloves during the bout, none after leaving.

**Photos** in `docs/minigames/`:

- Free movement (`box_free_*.jpg`):
  - the camera with the bot's JAB tell;
  - the frozen perfect dodge with PERFECT · COUNTER (from the first, straight-behind camera, where the big avatar hides the bot);
  - the KO;
  - the R6 stand-in.
- The first, fixed-stance version (`box_*.jpg`): the side shot mid-hook, the knockdown, the KO, the R6 stand-in.

## SLAP GOLF (19 Nov 2026)

The owner asked: "mini game where you toss dummies with the hand slapper, almost like mini golf". Our own design:

**The course:** six holes on one raised bed (2 studs high), two rows of three cells, each cell 14 x 38 studs (12 x 36 of lawn inside round wood rails). Everything is plain parts in the hub's quiet colours, built by `server/MiniGolf.luau` (`build`) on the hub's `MiniGameSpot` with `Game = "golf"` (the footprint's middle on the floor, its look along the long side; `MG.L.golf`: 44 x 80 studs).

- **The lawn:** sage green in rolled stripes, 3 studs deep, alternating two tones. Cream bed and stone strips between the cells.
- **The cup:** a cream rim, a dark hole and a pole with an amber flag carrying the hole's number. The flag is the one accent.
- **The holes** (all play toward the spot's look; `MG.GOLF.HOLES`):

| Hole | Par | What's on it |
|---|---|---|
| 1 | 2 | a log across the lane to tumble over |
| 2 | 3 | a long planter with bushes down one side: go round it |
| 3 | 3 | a ramp up to a raised green |
| 4 | 3 | a bar turning across the lane (it shoves the dummy) |
| 5 | 3 | five bouncy posts |
| 6 | 3 | a kicker ramp over a pit: short is out of bounds |

**Playing:**

- **Joining:** the PLAY / JOIN prompt at the front of the course. Up to four golfers; the first one in presses START.
- **Each golfer** gets the Hand Slapper in their right hand (the weapon's own model, welded) and their own ragdoll dummy: the training room's cardboard dummy, its chest ring's middle in the golfer's colour.
- **Your shot:**
  - You stand beside your dummy, on its left, facing your aim: your right hand swings into it, and the camera behind the dummy sees it past you.
  - Turn the camera to aim: A / D or the arrow keys, drag with the right mouse button, the pad's left stick, or a drag on a phone.
  - Hold to charge (click, Space, RT or A, the phone's SLAP button): the meter fills in 1.1 s and falls back again.
  - Let go to slap. The dummy flies along your aim at 10 to 56 studs/s, 0.36 of that upward, tumbling.
- **The server owns the dummies,** so everyone sees the same flight, and it judges each shot:
  - **In the cup:** the dummy's middle within 2.8 studs of the cup, low (within 1.6 studs of the lawn), slower than 14 studs/s. One flying over it fast doesn't count (the first test sank a dummy that skimmed over at speed).
  - **Out of bounds:** off its cell, or down into a pit. It goes back where it was hit from, +1 stroke.
  - **At rest:** slower than 1.4 studs/s for 0.5 s, or 9 s after the slap.
- **Turns** go round the golfers who aren't in yet. Picked up at par + 4. A shot not taken in 30 s is taken for you (soft, at the cup).
- **The card** shows between holes (4 s) and at the end: strokes per hole, the total, and against par. AGAIN (the host) plays another round with whoever's there.
- **The dummies** are in their own collision group (`MiniGolfDummy`). They touch the course, never people or each other.
- **No rewards,** like the other hub games, and never in matches.

**Juice:**

- The slap: a whoosh, then a smack whose pitch drops with power, the dummy flashing white, a dust puff, the Slapper's hand squashing, the golfer's arm swinging through (wound back while you charge), and a small shake on your own slap.
- A bouncy post: `boing`. A rail: `bonk`.
- The cup: `popper` and `pop`, confetti in the course's colours, the flag wiggling.
- Out of bounds: `whoops`. The end of a round: `loot_win_rare`.
- Recordings only.

**Camera:** behind your dummy along your aim (10 back, 5.5 up, looking 9 past it). In flight it chases the dummy. In the lobby and between holes it looks down the next hole.

**Files:**

- `server/MiniGolf.luau`: the course, the dummies (ragdolls made from an R15 body: ball-socket joints in limits, no Humanoid), the turns and the judging.
- `client/MiniGolfUI.luau`: the screen, the aim and the meter, the camera, the juice, the arm swing.
- `MG.GOLF` and `MG.L.golf` in `shared/MiniGames.luau`.
- In the core: one prompt for several places (side `"*"`, `pickSide`), a game's own `refresh`, the course's walk-away box, the stand-in on the first tee, and `JankMiniTest:Invoke("place", kind, cf)` to build a game anywhere for a test.

**Test hooks:**

- `JankMiniTest:Invoke("sit", p, "golf1", "*")`, then `("op", p, { op = "start" })`.
- A second golfer: `("standin", "golf1", "B")`, then `("as", "golf1", "B", { op = "slap", yaw = ..., power = ... })`.
- Client `MiniTest`:
  - `golf:slap:<power>`: at the cup;
  - `golf:slapyaw:<degrees>:<power>`: that far off the cup line;
  - `golf:aim:<degrees>`;
  - `golf:start`.

**SLAP GOLF tested** (place versions 1055 and 1061):

- Built on a test spot over the hub with `JankMiniTest:Invoke("place", "golf", cf)`; the hub's golf wing isn't built yet. The course: 243 parts.
- You and a stand-in played hole 1 through:
  - a full-power slap sideways: a rail bonk, then out of bounds (+1, back to the spot);
  - rests;
  - both in the cup (4 and 5 strokes);
  - the hole's card.
- The first test sank a dummy flying low over the cup at speed. Fixed: the cup now wants it within 1.6 studs of the lawn and slower than 14 studs/s.
- The first stance put you between the camera and your dummy. Fixed: you now stand at its left, Slapper out.
- The anti-cheat: 0 points.
- Photos: `docs/minigames/golf_your_shot.jpg`, `golf_card.jpg`.

## The owner's notes of 19 Nov (place version 1061)

The anti-cheat session forwarded them:

> "hitting skillchecks in arm wrestly makes it smaller, chess pieces should be easier to tell what they are"

> "add seating spots on top of the arcade machine, apeaking of arcade machjine add a leaderboard option, give a minitool tip before arm wrestling, seats ointhe lounge are sittable loot will wait until ther is a seat open if therye all being sat on"

> "seats in vip room work too"

- **Arm wrestling:**
  - Each side's zone now shrinks with that side's hits (`MG.ARM`):
    - a hit x0.88, a perfect x0.82, down to 0.05;
    - a miss gives some back (x1.25, up to the starting 0.15).
  - The needle still quickens over the bout.
  - **The tip:** during the countdown, "PRESS SPACE WHEN THE NEEDLE IS IN THE ZONE · EACH HIT SHRINKS IT" (TAP on a phone, the pad's button on a pad). It stays 2 s into the bout. Seen at place version 1074 (`docs/minigames/arm_tip.jpg`).
- **Chess:**
  - New pieces (kit v2, asset 96758810630944; `minigame_models.py`):
    - the pawn's big round head;
    - the rook's four battlements;
    - a thicker knight with ears and a long snout (still turned side-on at the table);
    - the bishop's tall pointed mitre with a slit (a boolean cut, applied before the export);
    - the queen's crown of eight beads;
    - the king's big cross.
  - A clear step in height, from the pawn (0.54) to the king (1.03).
  - The piece you point at, pick, or have the pad's square on is named under the board (PAWN, KNIGHT ...).
  - Photos: `chess_pieces_v2.jpg`, `kit_pieces_v2.jpg`.
- **The arcade:**
  - **LEADERBOARD** beside START on the attract screen: ALL TIME and THIS SERVER, 10 each, and BACK (pad B closes it too).
    - The all-time board is each player's best in an OrderedDataStore: `JankArcadeBest`, or `JankArcadeBest_studio` in Studio, so tests never touch the live board.
    - It is read every 60 s and after each better run.
    - Tested: a 1,250 run went onto both boards. The panel is solid since place version 1074 (the attract screen showed through it).
    - Photo: `arcade_leaderboard.jpg`.
  - The cabinet's own screen takes turns between HIGH SCORES (this server) and ALL-TIME BEST.
  - Two cushions on the lid (kit v2) and two HubSeat parts on them (`L.arcade.topSeats`).
- **Seats** (`server/HubSeats.server.luau`, new):
  - Any part tagged `HubSeat` gets a Seat and a Sit prompt. The server seats you, stamping TeleportT for the anti-cheat; a jump stands you up; touching a seat never sits you.
  - While someone sits there, `SeatTaken` is set on the tagged part. A regular's place with `NpcHere` counts as taken.
  - The lounge and VIP sofas are the hub's to tag. It will, once its new layout is live, and make HubNPCs (Looticus and the others) skip or wait on a taken seat.
  - The prompt's reach is 9 studs, since the cabinet's lid is over your head.
  - Studio hook `ServerStorage.JankSeatTest`:
    - `("sit", player, taggedPart)` runs the prompt's own checks;
    - `("list")` shows who sits where.
  - Tested at place version 1074, through that hook:
    - you sat on the lid's first seat;
    - `SeatTaken` went true, and its prompt hid;
    - standing up freed it again.
  - Photo: the cushions on the lid. Your own body is hidden on your own first-person screen, so it doesn't show sitting there.
  - A test script's `ProximityPrompt:InputHoldBegin()` never fires a prompt, so use the hook.
  - **A prompt shows only while it is on screen** (21 Nov). After a server teleport the client camera keeps its old heading, so a prompt beside or behind it never shows, and that looks like a bug. To check a prompt, turn the client camera toward it (Scriptable, `CFrame.lookAt`), read the texts in `PlayerGui.ProximityPrompts`, then set the camera back to Custom. Studio's screen capture never draws prompt pop-ups.
- **Boxing, several rings:**
  - One bout per `box` marker, all at once.
  - Each ring's publish timer is its own.
  - A marker's `Ring` (1..4) names its table (box1..box4).
  - Its `Half` (the mat's middle to the inside of its ropes, 12.75 for today's mat) sets both the walls and the bot's bound.
  - Tested in the gym's four rings (the hub's new layout, live at place version 1086):
    - the four markers made box1..box4, each with Half 12.75;
    - in one Play, you vs an easy bot in ring 1 and a Studio stand-in vs a medium bot in ring 2 fought at the same time;
    - both bots walked on their own;
    - ring 1's bot was knocked down while ring 2's took the stand-in to 39;
    - the anti-cheat: 0 points.
  - Photo: `docs/minigames/box_gym_two_bouts.jpg`.

## Several hubs at once (20 Nov 2026, place version 1191)

The owner wants all three hub concepts built, with travel between them: THE SQUARE, THE CONCOURSE and THE ATRIUM. The hub session's convention is `side-session-notes/HUB-MARKERS.md`.

- **Markers:** every `MiniGameSpot` under `workspace.Map` makes a table, and all of them run at once.
- **A hub:** a folder right under `Map.Hub` (`Map.Hub.Square`, ...). Its markers sit in its `Scenery` and carry `Hub` = its id (`"square"`).
  - Their tables are built in a `MiniGames` folder inside that hub folder. ZoneCull culls each child of `Map.Hub` per client, so a hub's games show and hide with it.
  - Their ids carry the hub: `box1_square`..`box4_square`, `arm1_square`, `board1_square`, `arcade1_square`, `golf1_square`.
- **The legacy ring's markers** carry no `Hub`. They stay in `Map.Hub.MiniGames` as `box1`..`box4`, `arm1`, `board1`, `arcade1`.
- **Numbers** count per hub and kind. A ring's own `Ring` wins. Two markers giving the same id: the second is skipped with a warning.
- **Staging:** anything under an ancestor with `MiniGamesOff = true` is skipped, so a builder's staging copy builds nothing.
- **Later markers:** a marker that turns up while a server runs is built when it appears, half a second after its tag. Nothing is built twice.
- **A golf room's door** (20 Nov, for THE CYLINDER): the golf course is 44 x 80, centred on its marker, and its PLAY prompt (reach 12) normally stands at the course's back end. That suits a room with walkways and its door at that end (the Square and the Concourse, 54 x 94).
  - A room the course fills wall to wall, with its door at the side, gives the marker a `Door` attribute: a Vector3, the doorway's floor centre in the marker's own space.
  - The prompt then sits 4 studs in from the door, toward the room's middle, at 4.5 up.
  - LEAVE puts the golfer back in the doorway, facing out. Walking off leaves them where they are.
  - The Cylinder's is `Vector3.new(-23, 0, -7)`.
- **The arcade boards** (this server's and the all-time) are written to every folder that has a cabinet, so every hub's cabinets show the same boards.
- **Tested** in one Play:
  - the ring's 7 tables kept their ids;
  - a test hub (`Map.Hub.TestHub`, `Hub = "testhub"`, a box, an arcade and an arm marker in its `Scenery`, added during the Play) got `box1_testhub`, `arcade1_testhub` and `arm1_testhub` in its own `MiniGames` folder, with the all-time board on it;
  - a staging copy with `MiniGamesOff` built nothing;
  - a bout in `box1_testhub` started;
  - the anti-cheat: 0 points.
- **THE SQUARE**, the first new hub (live since place version 1203; checked at 1211):
  - all 8 of its tables built in `Map.Hub.Square.MiniGames` at the hub's spots: arm, board and arcade in the lounge street, the four 22-stud rings in the gym (`Half` 10.2), and golf in its own 54 x 94 room;
  - nothing of the hub's stands inside the course;
  - a golf hole played through in the room (in the cup in 4), and a bout ran in `box1_square`;
  - the anti-cheat: 0 points;
  - photos: `docs/minigames/square_golf_room.jpg`, `square_box_ring.jpg`.
- **THE CONCOURSE** (live since place version 1227):
  - all 8 tables built in `Map.Hub.Concourse.MiniGames` at the hub's spots; golf in its 54 x 94 room east of the hall, the prompt by the west-wall door;
  - nothing of the hub's stands inside the course;
  - a golf hole played through (picked up at par + 4, the card shown), and a bout ran in `box1_concourse`;
  - the anti-cheat: 0 points;
  - photo: `docs/minigames/concourse_golf_room.jpg`.
  - The room's warm lights make the course look more saturated than in the Square; that's the hub's lighting.
- **THE ATRIUM** (live since place version 1229; no golf room):
  - all 8 tables built in `Map.Hub.Atrium.MiniGames` at the hub's spots: board, arm and the two cabinets (`arcade1_atrium`, `arcade2_atrium`) on level 2 (y 255, reached by the jump pads by the spawn), the four 22-stud rings in the gym through the SE portal (`Half` 10.2);
  - nothing of the hub's stands in any table's room or inside the ropes;
  - all four level-2 tables seat you (the player's `Hub` reads `atrium`), an arm bout ran there against a stand-in, and a bout ran in `box1_atrium`;
  - the anti-cheat: 0 points;
  - photos: `docs/minigames/atrium_arm_level2.jpg`, `atrium_box_ring.jpg`.
- **THE RING retires** after the Atrium (the hub session's turn, 20 Nov): `Map.Hub.Rotunda` and its 7 markers go, so the bare ids (`box1`, `arm1`, ...) go with them. Tests use the hub ids (`box1_square`, `golf1_concourse`, ...). Nothing here reads the ring directly: markers are found by tag, the `RingMat` fallback runs only when there is no box marker, and `Map.Hub.MiniGames` stays as an empty folder.
