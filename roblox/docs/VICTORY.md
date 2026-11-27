# The victory scene and the stats card (27 Nov 2026)

The owner, 27 Nov: "when you win in rivals, it plays a small cinematic that shows off your characters doing like an
action ... then it displays your stats and then if your teammates are there, they appear behind ... If you have the
custom cinematic finishers it replaces the default!"

## What happens at a match's end
1. **The winning round** (Matches.checkRound) calls "X WINS THE MATCH". 1.2 s later endMatch runs the end hooks.
2. **VictoryServer** (an onEnd hook) holds the end screen on `m.finisherUntil` for `V.LEN` (5.0 s) + `V.SLACK`. Then,
   once every other end hook has run (task.defer), it sends everyone in the match one message on
   `JankfireRemotes.Victory` (the shape is in the script's header).
3. **The client** (Victory.client) does one of three things:
   - **Default scene** (VictoryScene). THE RISER is built far off the map. The winning side stands on it and the
     camera runs RISE then STAGE. The card (VictoryCard) slides in at LEN - 0.8 s. After `V.SKIP_AFTER` (2 s), Space, B
     or the SKIP chip jump to the held shot and the card.
   - **A finisher cinematic** played (FinisherServer's hold: `m.finisherFrom` within `V.CINE_WINDOW`). Nothing happens
     until the end screen. Then THE RISER's held shot comes up with no intro and no sting, plus the card.
   - **A draw / no winner.** The card alone, over the arena.
4. **The end screen.** Matches.endScreen fires Round "over" when the hold ends: at the cap, or 0.3 s after every viewer
   reported done or skipped. The card's wait bar shows `next` / `nextLabel`.
   - Then the play of the match takes the screen (the client lets go 0.15 s before) or the trip home does (Round "hub").
   - backToHub and CrossServer.backHome come only after the end screen, so nobody goes home mid-scene.

## Rules
- **The one in front.**
  - Team modes: the match-winning kill's killer, if they are on the winning side. Otherwise the MVP: most kills, then
    most damage, then most assists, then fewest deaths, then the name (`VictoryData.front`).
  - Classic modes: the last kill's maker if they took first place, else the top of the mode's own result order.
- **Teammates.** Up to 3 behind, on the riser: left, right, then centre-high.
- **The action.**
  - A body plays the first slot of its player's emote wheel that isn't one of the 8 default emotes (`V.emoteOf`).
  - Otherwise it plays a Mixamo victory pose, converted for R15 + R6 in one upload: `V.POSES`.
    - The one in front gets Victory or Fist Pump.
    - Teammates get Victory Idle x3 or Cheering, each a different one where possible.
- **Losers.** The same winners' scene, seen from a long, low lens with a colder, greyer grade, then DEFEAT on their
  card.
- **Stings.** From Roblox's licensed APM library, played under the MUSIC volume:
  - win: "Rise Of Champions" (9041815642);
  - lose: "Accepting Defeat StingA" (1848015457), faded out from 4.6 s.
- **The card's numbers.**
  - K/D/A/DMG come from `Scoreboard.board`, the same counts as the Tab board.
  - XP and coins are the change in the Xp / Brass attributes since the match began.
  - Mastery comes from MasteryPush "match".
  - Quests are those whose count moved (the Quests remote's state, then and now).

## Files
- `shared/VictoryData.luau`: the switch `V.ON`, the timings, the poses and the rules.
- `server/VictoryServer.server.luau`: the message, the hold, the done reports and the Studio hook `JankVictoryTest`.
- `client/Victory.client.luau`: the flow, the rewards, the skip, and the Studio preview `VictoryTest`.
- `client/VictoryScene.luau`: the stage, the bodies, the lens, the look and the sting.
- `client/VictoryCard.luau`: the card, in A PLATE from `client/UiKit.luau`.
- `tools/roblox/victory_stage.py`: the set as a Blender kit (upload 76083103868358). Its import paints it in Studio:
  `ReplicatedStorage.JankfireVictory.Stage`, plus the Sounds `Win` and `Lose`.
- Hunks in others' files:
  - Arsenal's Round handler skips FightHud's end screen while `VictoryOn`;
  - MasteryClient delays its own match card 0.6 s and skips it while `VictoryOn`.

## Testing (Studio)
- **Preview without a match.** Set the LocalPlayer attribute `VictoryTest` to `win`, `lose`, `win:3`, `lose:1`, `cine`,
  `card`, `draw`, `skip` or `stop`. Every body is your own look.
- **Photos.** Workspace `VictoryFreeze` = seconds holds the lens at that moment. Workspace `VictoryShots` = JSON
  overrides the lens numbers (VictoryScene's `tuned`).
- **The real flow.**
  - Run `JankMatchTest("ghost", "1v1", nil, secs, player, 1)`. The last argument is the winning team: 1 is yours, 2 a
    loss.
  - For teammates behind, first run `JankVictoryTest("fake", player, { { name, look = userId, mine = true, k, d, a, dmg } })`.
  - Finisher replace: the recipe in memory roblox-finishers (`JankFinisherTest`).
