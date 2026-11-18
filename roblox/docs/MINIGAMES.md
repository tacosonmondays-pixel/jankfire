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
