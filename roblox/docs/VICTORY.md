# The victory scene and the stats card (27 Nov 2026)

The owner, 27 Nov:
- "when you win in rivals, it plays a small cinematic that shows off your characters doing like an action ... then it
  displays your stats and then if your teammates are there, they appear behind ... If you have the custom cinematic
  finishers it replaces the default!"
- "Everyoone sees it though, and if you win with a team and multipple people have different finishers, the person who
  did the best has theirs play against the enemy best because weapon finishers are usualy duels"
- "the victory screen will depend on the map! itll be a preloaded scene just placing our characters in!"

Plan, decisions and test history: side-session-notes `local_f6d4e505.../victory-scene/PLAN.md`. Sheets and clips are
in the same folder.

## What happens at a match's end
1. **The winning round** (Matches.checkRound) calls "X WINS THE MATCH". 1.2 s later endMatch runs the end hooks.
2. **VictoryServer** (an onEnd hook) holds the end screen on `m.finisherUntil` for `V.LEN` (5.0 s) + `V.SLACK`.
   - Once every other end hook has run (task.defer), it ranks everyone still in the server.
   - It asks FinisherServer for the cinematic: `Matches.endFinisher.pick` / `play`, the best winner with a scene
     finisher against the enemy's best.
   - Then it sends everyone in the match one message on `JankfireRemotes.Victory` (the shape is in the script's header),
     with the map's own spot when the arena has one.
   - At load it sets `Matches.victoryLive`, which turns FinisherServer's old match-winning-kill cut off.
3. **The client** (Victory.client) does one of three things:
   - **Default scene** (VictoryScene).
     - At the map's spot (the arena's `Victory` model), with the map's own light. Live bodies, NPCs and pets near it
       are hidden on screen while it plays.
     - Without a spot: on THE RISER, our set built far off the map.
     - The lens runs RISE, a close-up on the one in front, then WIDE, a push-in to the held group shot.
     - The card (VictoryCard) slides in at LEN - 0.8 s.
     - After `V.SKIP_AFTER` (2 s), Space, B or the SKIP chip jump to the held shot and the card.
   - **A finisher cinematic** played. Nothing happens until the end screen. Then the held shot of the winners comes up
     with no intro and no sting, plus the card.
   - **A draw / no winner.** The card alone, over the arena.
4. **The end screen.** Matches.endScreen fires Round "over" when the hold ends: at the cap, or 0.3 s after every viewer
   reported done or skipped. The card's foot counts down `next` / `nextLabel`.
   - Then the play of the match takes the screen (the client lets go 0.15 s before) or the trip home does (Round "hub").
   - backToHub and CrossServer.backHome come only after the end screen, so nobody goes home mid-scene.

## Rules
- **One ranking (`VictoryData.better`).** It picks the one in front, the teammates, the finisher player and its victim.
  - Team modes: most kills, then most damage, then most assists, then fewest deaths, then the lower UserId.
  - Classic modes: the mode's own result order (`m.results`) first.
  - Players who left are skipped.
- **The cinematic.** The best-ranked winner with a scene finisher equipped plays theirs against the enemy's best still
  here. If that play fails, the next-best enemy gets one try, then the default scene plays.
- **Teammates.** Up to 3 behind, placed by the held lens's angles so nobody stands behind the one in front: on the riser,
  or on the spot's Mate1-3.
- **The action.** All of it is Mixamo mocap, converted for R15 + R6 in one upload each (`V.POSES`). The poses were picked
  from stick-figure sheets with the gun drawn along the forearm.
  - **The one in front** always takes a victory pose with the weapon up: a fighter's guard with the gun by the face, or
    both arms up (`V.HERO_POSES`).
  - **Teammates** play their own emote (the first wheel slot that isn't one of the 8 defaults, `V.emoteOf`). Otherwise
    each gets a different pose (`V.MATE_POSES`): a cheer, an aim, a low crouch, a lean.
  - On THE RISER, the second teammate sits on the front edge (`V.SIT_POSE`). Its seat is measured off the body's own
    torso.
  - **Weapons.** Every body in a pose holds its own weapon: the one in hand at the end, else the loadout's first. It
    carries its skin, wrap and hat, gripped as Fight.showWeapon grips a held gun. A dancing body holds none.
- **Losers.** The same winners' scene, seen from a long, low lens with a colder, greyer grade, then DEFEAT on their card.
- **Stings.** From Roblox's licensed APM library, played under the MUSIC volume:
  - win: "Rise Of Champions" (9041815642);
  - lose: "Accepting Defeat StingA" (1848015457), faded out from 4.6 s.
- **The card's numbers.**
  - The board is K/D/A/DMG from `Scoreboard.board`, the same counts as the Tab board, or a classic mode's own columns.
    A free-for-all is one list, with your place.
  - XP and coins are the change in the Xp / Brass attributes since the match began; the coins row shows the wallet.
  - Mastery comes from MasteryPush "match".
  - Quests are those whose count moved (the Quests remote's state, then and now).
- **The card's look.** A PLATE, ui-mocks' UiKit, judged by the anti-AI critic (rounds and fixes in PLAN.md):
  - the stencil slit on the result word only;
  - one score tile per side, the winner's filled and the other outlined;
  - your row in ink;
  - one right edge for every number;
  - the countdown as a 2 px line on the plate's bottom edge.

## A map's victory spot
- **What it is.** A Model named `Victory` anywhere inside the arena's model, so arena copies carry it.
  - `Hero`, `Mate1`, `Mate2`, `Mate3`: invisible Parts on the floor; LookVector = the way that body faces.
  - `RiseA`, `RiseB`, `WideA`, `WideB` (+ optional `LoseA`, `LoseB`, `Hold`): lens keys. Position = the lens,
    LookVector = where it looks, attribute `Fov`.
  - `Lights` (optional): Lights off in the map, switched on, on screen only, during the scene.
- **How they're made.** All 15 maps got theirs from `studio-tools/VictorySpots.luau`:
  - the one in front stands at the middle of a team's spawns, facing the arena's middle;
  - rays find the floors and test the lens lines, looking past invisible walls;
  - the wide lenses frame about 13 studs at any distance.
- **Seen in Play:** RooftopV2, RooftopV3, Crate, DesertV2, The Gut, Arctic Cabin. The others are placed but not yet
  photographed; move a weak one by hand by editing its Parts.

## Files
- `shared/VictoryData.luau`: the switch `V.ON`, the timings, the poses and the ranking.
- `server/VictoryServer.server.luau`: the ranking, the cinematic call, the spot, the message, the hold, the done
  reports and the Studio hook `JankVictoryTest`.
- `client/Victory.client.luau`: the flow, the rewards, the skip, and the Studio preview `VictoryTest`.
- `client/VictoryScene.luau`: THE RISER and the map spots, the bodies, their poses and weapons, the lens, the look and
  the sting.
- `client/VictoryCard.luau`: the card, in A PLATE from `client/UiKit.luau`.
- `tools/roblox/victory_stage.py`: THE RISER as a Blender kit (upload 76083103868358). Its import paints it in Studio:
  `ReplicatedStorage.JankfireVictory.Stage`, plus the Sounds `Win` and `Lose`.
- `studio-tools/VictorySpots.luau`: the spot generator.
- Hunks in others' files:
  - Arsenal's Round handler skips FightHud's end screen while `VictoryOn`;
  - MasteryClient delays its own match card 0.6 s and skips it while `VictoryOn`.

## Testing (Studio)
- **Preview without a match.** Set the LocalPlayer attribute `VictoryTest` to `win`, `lose`, `win:3`, `lose:1`, `cine`,
  `card`, `draw`, `skip` or `stop`. Every body is your own look, and the rows and rewards are sample numbers.
- **Photos.** Workspace `VictoryFreeze` = seconds holds the lens at that moment. Workspace `VictoryShots` = JSON
  overrides THE RISER's lens numbers (VictoryScene's `tuned`).
- **The real flow.**
  - `JankMatchTest("ghost", "2v2", "<Arena>", secs, player, 1)`. The last argument is the winning team: 1 is yours, 2 a
    loss. It plays at that map's spot.
  - For teammates, first run `JankVictoryTest("fake", player, { { name, look = userId, mine = true, k, d, a, dmg } })`.
    They are ranked with everyone.
  - A classic mode: `JankModeTest("start", "rand", player, { "Ghost1", "Ghost2" })`, then
    `("kill", player, <your fighter name>, "Ghost1")` until the target.
  - The cinematic's path: in a ghost match, `JankVictoryTest("cinehold", player, secs)` marks a finisher's hold, as
    FinisherServer's holdFor does. Their own `JankFinisherTest("victory", ...)` plays the scene itself; it needs a
    second fighter in the match's recording.
  - `JankVictoryTest("pick", player)`: the finisher FinisherServer says this player would bring.
