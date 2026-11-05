# Work split: one branch per task

All task branches start from `claude/ship-update2` (= main + update 2 merged, commit 657074e) unless noted.
Each one ships as its own draft PR; the owner marks it ready and merges. Read `CLAUDE.md` (on
`claude/weapon-feel-update`, PR #5) and `HANDOFF.md` (`git show origin/claude/handoff:HANDOFF.md`) first.

Effort: **max** for maps, models, animation and UI; **high** for gameplay, merges and fixes; **medium** for reviews.
Start these sessions on the **jankfire** cloud environment (it installs Blender 4.0.2 and the npm packages).

| Branch | What | Effort | Depends on |
|---|---|---|---|
| `claude/ship-update2` | Finish shipping update 2 | high | - |
| `claude/ship-update3` | Merge the finished update-3 features | high | ship-update2 merged |
| `claude/map-pass` | Rework the current maps | max | ship-update2 |
| `claude/ui-endscreen` | End-of-match screen, 2-stage vote, menu polish | max | ship-update2 |
| `claude/blender-pipeline` | Blender -> glTF -> game pipeline + first weapon models | max | ship-update2 |
| `claude/battle-royale` | BR mode + the Jankburg city map + BR bots | max | map-pass, blender-pipeline |

## claude/ship-update2 (high)
Main is already merged into update 2 here (conflicts resolved keeping both sides; the server boots and serves).
1. Fix the absolute scratchpad paths in `handoff/tests/*.sh|*.cjs` (from `claude/handoff`), run
   `regress2.sh <checkout> <port>`, compare with `handoff/baseline-main.txt` (18 pass; t_anim + t_flash were already stale).
2. Play-test the merged spots: killcam / play-of-the-round skip vs unskippable EPIC killcams, sleeping + bubble-sealed
   players, Training streaks with chaos kits, replays of sleepers.
3. Draft PR to main. Remind the owner to re-run `supabase.sql` (adds airborne, wings_old, sniper_feats).

## claude/ship-update3 (high)
Merge, test and PR in this order, one at a time: `claude/f-keys` (rebindable keys) -> `claude/f-music` (ask the owner
for the track's real name) -> `claude/f-slip` (WITHOUT the WIP commit 4fb8e6b unless it tests fine) -> `claude/f-zombies`.
They were built on update 2 before update 1, so expect conflicts. Then add the dedicated rebindable "Parry" action.

## claude/map-pass (max)
Everything in `handoff/map_todo/MAP_FIXES.md` (+ its two screenshots): out-of-bounds "RETURN TO THE MAP 3 2 1"
countdown (server-enforced), a bigger Suburb (cul-de-sac in the spirit of the owner's reference: two rows of houses
across a street, a bus/truck as middle cover, tree ring border, no cliff), street levels under Skyline and Rooftop,
the Skyline bridge that ends in mid-air, Warehouse props (forklifts, pallets, shelving rows) + fenced yard + skyline,
Bazaar gaps. Then push every map toward the art direction in `docs/CITY_DESIGN.md` ("The vibe"): clashing
Cruelty-Squad-ugly textures, glossy Nubby-style toy props, cyberpunk neon. Maps stay box-based (`shared/map.js`:
server physics + bots use the same boxes); Blender props are visual-only once `blender-pipeline` lands. Keep the bot
walk graph working on every map and screenshot before/after.

## claude/ui-endscreen (max)
Owner's reference: a Krunker-style flow. Take the STRUCTURE, not the look or any branding:
- End of match: huge VICTORY/DEFEAT title, "Next round in 0:19", then the vote as big thumbnail cards
  (map picture + mode + vote count), tabs: Leaderboard / Performance (score, kills, deaths, KDR, rank, XP earned) /
  Medals / Rewards. Make it the **two-stage vote** from HANDOFF.md: pick the mode first, then the map.
- Main menu: logo centre-top, character preview + "Customize" in the middle, a right-hand column of big play buttons
  (Quick Match, Bots, Host, Find Game, Training), a "Now playing: <mode> on <map>" strip, side links on the left.
- Style: JANKFIRE's pink/magenta + yellow comic UI plus the Cruelty Squad / Nubby / cyberpunk vibe
  (fleshy/biomech screen frame, glossy toy buttons). Check open PR #6 (kimi's "Corporate Punishment Terminal" reskin)
  first and build on it or agree with the owner which way to go. Screenshots at 1080p and a small window.

## claude/blender-pipeline (max)
1. Client: load `.glb` with three's `GLTFLoader` (three 0.170 is in node_modules) from `public/models/`, cache them,
   fall back to the current code-built model if a file is missing. Visual only: collisions stay boxes.
2. `tools/blender/`: headless build scripts (`blender -b --python make_<thing>.py`) that build a model from code,
   export glb (no Draco: the apt Blender lacks it; use `@gltf-transform/cli` to optimize instead) and render a
   turnaround sheet with EEVEE for review.
3. First models: 2-3 weapons from real references (real proportions), then props for the map pass
   (forklift, pallet, shelving, bus, cars, street lights, toy-like number balls). Compare against the code models in
   the real game (Playwright screenshots at Too HD and Potato).

## claude/battle-royale (max)
`docs/CITY_DESIGN.md` is the map brief. Mode + bots are described in HANDOFF.md (queued requests).
Draw the master plan and agree it with the owner before building.

## Tools and plugins
Installed in the jankfire environment: Blender 4.0.2 (headless: modelling, glTF export, EEVEE renders through
software GL), numpy, Node 22 + the repo's packages, Chromium + Playwright.

Blender add-ons that come with Blender (enable in Preferences > Add-ons, or `addon_utils.enable()` in scripts):
glTF 2.0 importer/exporter (the route into Three.js), Archimesh (walls, doors, windows, stairs), Sapling Tree Gen
(trees for map borders), Bool Tool, LoopTools, Snap Utilities Line, Extra Objects.

Worth adding (free): Building Tools (github.com/ranjian0/building_tools: procedural floors, windows, doors, roofs, good
for the house variants), Kit Ops 2 free (kitbashing parts for weapons), Poly Haven assets (CC0 textures/HDRIs).
Paid, optional: Hard Ops + Boxcutter (hard-surface weapons), ProtoBlock ($10, grid blockouts), Tykuii's Level Design
Toolkit ($20, needs Blender 5.1+, the apt Blender is 4.0).

For the owner's own PC: Blender MCP (github.com/ahujasid/blender-mcp) lets Claude drive a running desktop Blender.
Cloud sessions don't need it: they run Blender directly with scripts.
