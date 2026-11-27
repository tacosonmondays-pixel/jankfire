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
2. **VictoryServer** (an onEnd hook) holds the end screen on `m.finisherUntil` for `V.LEN` (5.6 s; a walk spot: its own `Len`) + `V.SLACK`.
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
     - THE WALK-UP: everyone walks up toward the lens and lands a pose. The lens runs CLOSE, a wide low lens in front
       of the one in front that pushes in as they walk at it, then cuts to WIDE, a push-in to the held group shot.
     - A walk spot (the Spooky Forest) is its own scene instead: THE WALK, below.
     - The card (VictoryCard) slides in at LEN - 0.8 s (a walk spot: just after its startle).
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
- **The action: THE WALK-UP** (the owner, 27 Nov: "a walk up into a dynamic pose with a perspective shot"). No emotes.
  All of it is Mixamo mocap, converted for R15 + R6 in one upload each (`V.POSES`), picked from stick-figure sheets
  with the gun drawn along the forearm.
  - **The walk.** Each body starts behind its mark (`V.ARRIVE`: 8 studs for the one in front, 5.5 for teammates; on
    THE RISER 5.5 and 1.8). Rays cut a walk short where a wall, a drop or a step is behind. They walk Roblox's own walk,
    its clip following the distance walked, and slow onto the mark.
  - **The landing.** On the mark, a "move into a pose" stretch plays once and holds its last frame. The one in front
    gets the charge's arm thrust (the weapon comes at the lens) or the victory's arms flung up (`V.HERO_POSES`).
    Teammates each get a different one (`V.MATE_POSES`): the rally's arm straight up, the fist pump, an aim, a cheer.
  - **The timing.** The one in front lands first, never sooner than 1.3 s (a short walk starts late, from an idle).
    Each teammate lands 0.2 s after the last.
  - **Everything is set from the scene's clock each frame**, the tracks paused and scrubbed, so a frozen photo is exactly
    that moment and a skip puts everyone on their mark in their pose.
  - **Weapons.** Every body holds its own weapon: the one in hand at the end, else the loadout's first. It carries its
    skin, wrap and hat, gripped as Fight.showWeapon grips a held gun.
- **The lens (winners).** CLOSE from 0 until 0.6 s after the one in front lands: low (knee height), close and wide (FOV
  60 to 70), a little to their off hand's side (on the weapon side the walk's arm swing blacked out the glass and the
  raised arm hid the face), pushing from 5.6 to 3.6 studs as they walk at it. A small kick as the pose
  lands, then a settle. A wall in front pulls the lens in. Then a cut to the spot's WIDE (THE RISER: its stage shot).
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
- **Seen in Play: all 15** (27 Nov spot check, place v1544: a forced 4v4 win on each map with three stand-ins, frozen
  at the close lens's landing and at the wide shot with the card). OK as placed: Rooftop, RooftopV2, RooftopV3, Crate,
  Platform, Bazaar, The Gut, DesertV2, SuburbV2, Backrooms, Arctic Cabin, Station; Forest is the walk.
  - Fixed: BazaarV2's wide lenses (the kit's pole and a crate stood in front: now straight on, 11 studs out, 5.2 up)
    and Skatepark's (outside the arena's wall, drawn in Play: now 7.5 studs out inside it). Each spot says how in its
    `Reaimed` attribute.
  - **Check lenses in Play, not Edit:** the visible kit is swapped in at Play start ("471 Blender models swapped in"),
    so Edit rays miss poles, crates and walls that the camera sees; walled arenas' invisible walls are drawn in Play.
  - Skatepark's spot has no Mate3 (no floor there): a 4v4 shows three of the four.
  - The pet (workspace.ClientPets) is hidden every frame: its follower rewrites its parts' transparency, and its pink
    Highlight outline draws even with the parts hidden.
- **Nothing pops in** (27 Nov, the owner: "Things pop in because it renders as the clip plays"; PERFORMANCE.md, "Films:
  nothing pops in"). The round that takes the match (Matches.onRound, 1.2 s before endMatch) sends everyone the spot
  and the winners' ids (`t = "warm"`). The client (`Scene.warm`) then:
  - builds the winners' bodies at once, into the scene's own folder, parked far below THE RISER. A body put in the
    world for the first time drew grey for a few frames while its clothes went on; one moved to another folder went
    invisible for 2-3 frames while an R15 body redid its clothes. The scene takes these bodies where they are.
  - runs `CineKit.prewarm` on every lens the scene will use (the walk-in close lens, the wide, the losers', the hold,
    the walk-in starts, the Forest path), THE RISER's kit, the stings, every pose and walk clip and the bodies' looks:
    ZoneCull keeps those map pieces and their assets load. 0.2-2.8 s per map in Studio, all "ok".
  - Classic modes end another way: their scene starts the same warm itself. THE RISER's meshes are Precise (Edit).
  - The first-person viewmodel (workspace.CurrentCamera) and the pet are hidden every frame from the scene's first
    frame. Scene.start doesn't step itself: the bound step runs after the viewmodel's and the pet's own.
  - Each ready body gets its weapon at the warm too, and with no map spot the warm puts THE RISER in the workspace
    (48,000 studs out, kept there between matches): preloaded isn't drawn, a mesh cloned on the first frame lags.
  - Every body copy is stripped of TPGun / TPItem / TPRigArms / HeldWeapon and every tag the moment it's made
    (ThirdPerson draws on a TPRig-tagged copy).
  - The scene opens black for at least 3 frames and 0.1 s: the scene's light comes in on its first frame and the
    renderer catches up a frame later, and an R6 body's clothes could lag 3 frames (v1618: Station and THE RISER
    clean from the first visible frame, fresh Play).
  - Test it: `JankVictoryTest("warm", player)` sends the warm (a ghost match ends on its clock, never through a round);
    call it ~1.2 s before the ghost's end. Frame check: record, `tools/roblox/vid_all.py`, `popscan.py`.
- **Phone:** the card follows TouchTest's `fake:WxH` box (player attribute `FakeScreen`); on a short screen it pins near
  the top and shrinks to fit (a 4v4 card with the PLAY AGAIN row fits 844x390 with room).

## THE WALK (a walk spot: the Spooky Forest)
- The owner, 27 Nov: "For scary map can you try make them walk in the forest scared as the screen distorts?"
- **The spot.** A `Victory` model with the attribute `Kind` = "walk", `Len` (seconds, 7 on the Forest) and Parts
  `Path1`..`PathN` on the floor in order. `studio-tools/VictoryWalkPath.luau` makes one from the arena's pose spot, which
  it keeps as `VictoryPose` (rename them back to switch).
- **The walk.** The winners walk the path. The one in front leads with the weapon up in a guard; teammates huddle behind
  (`V.WALK.mates`), each glancing back at its own moment.
- **The lens.** TRACK, a slow backward track in front of them; LOW, at their side looking up through the trees; BEHIND,
  over the last one's shoulder into the dark; then the STARTLE, a whip in on the one in front.
- **The screen.** Over the walk: colour draining toward a cold green, a breathing FOV, a heartbeat-timed vignette and
  blur, double-vision flickers, a rising shake. At the stinger: a flash, a kick, and everyone snaps into a guard.
- **Sounds** (kit `WalkAmb`, `Heartbeat`, `Stinger`, all APM under MUSIC): "Haunted Forest a 30" (1841594571),
  "Heartbeat" (1840104783), "Horror Hits 9" (1840927250).
- **Live on the Forest since Studio v1476** (two earlier tries parked: lenses crowding the bodies, a knockdown startle).
- **Mocap.** Roblox's walk slowed, under upper-body layers from the vault, until the owner's Mixamo clips arrive
  (side-session-notes `MIXAMO-CLIPS-NEEDED.md` items 10-14).

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
- `studio-tools/VictorySpots.luau`: the spot generator. `studio-tools/VictoryWalkPath.luau`: a walk spot's path.
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
