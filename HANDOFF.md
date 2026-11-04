# JANKFIRE handoff (2026-11-04)

Read this first in a new session. Everything below is on GitHub (tacosonmondays-pixel/jankfire).
The old session's scratch folder is gone, so the test tooling was copied into `handoff/` on this branch.

## What's live (main, auto-deployed to https://jankfire.onrender.com by Render)
- Update 1 (PR #1): the review fixes (74 findings), strict server input validation, guns update (Marble Shotgun, Redline),
  one hotbar (bottom/right), corner killstreaks, rebuilt knife/katana models, sniper headshots kill, revolver headshot 96.
- Update 1.1 (PR #2): sniper knockback back (minigun + sniper are the only guns that shove); killcam victim stays until the
  killing shot, then explodes.
- Update 1.2 (PR #3): sleep arrow knocks you flat for 4 s (everyone sees it); the play of the round is skippable.

## Update 2: almost done -> `claude/int-features` (head 2b29c0a)
Already merged and fixed in it: update 1, plus
bubble wand, Scales of Justice, Wrecking Ball, revolver twirl + fan, unskippable EPIC killcams, no-scope hype, grapple skins,
duck rework, headshot DINK/TONK + homing slippers, katana parry, pendulum grapple, sprays (Z), popper/reverse as items (8 items),
Never Landed (wings), Shredder, Blood Cross, Golden Sniper (Sniper Royalty), Backrooms map, Gun Game, Infection,
Spoons & Grapples, Duck Rain, Floor Is Lava, One in the Chamber, Runner Jacket.
Its own commits explain every cross-feature decision (`git log --oneline be76a3a..claude/int-features`).

To ship it:
1. `git merge origin/main` into claude/int-features (brings in 1.1 + 1.2; expect small conflicts in replay.js / remote.js /
   main.js / server.js around the killcam alive-flag fix and the sleep knock-down flag).
2. Run the regression: `handoff/tests/regress2.sh <checkout> <port>` (fix the absolute scratchpad paths in the scripts first:
   they point at the old session's folder; pwlock.cjs caps headless browsers at 2). Baseline on update 1:
   `handoff/baseline-main.txt` (18 pass; t_anim and t_flash were already stale/failing).
3. The owner must re-run `supabase.sql` in Supabase (update 2 adds columns: airborne, wings_old, sniper_feats);
   `check-supabase` reports what's missing.
4. PR to main (draft first, owner marks ready + merges), rebuild the exe (`desktop/`, build-desktop.yml).

## Update 3 branches (all pushed)
Finished and reviewed, not merged anywhere yet (built on e8fe212 = int-features before update 1 unless noted):
- `claude/f-zombies` (e8bc3b5, based on ac5f9eb): co-op Zombies on the Dead Mall (credits, shutters, wall guns, crate, power, Jank Cola, revives).
- `claude/f-slip` (73b54ae): parry window 0.6 s (perfect 0.25 s) + marbles on the floor make people slip.
  The commit after it (4fb8e6b) is a WIP parry-animation polish: unfinished, test before keeping.
- `claude/f-music` (c1e3378): music system + the owner's track (public/music/untitled.mp3, listed as "Untitled": ask for the real name).
- `claude/f-keys` (cc1fe7c): rebindable keybinds (Settings > Controls), built + reviewed + fixed.
Partly built (WIP, untested):
- `claude/f-econ`: competitive Plant & Defuse. Server side DONE and tested (c56d5bf; design in `handoff/econ_DESIGN.md`).
  Client (buy menu, HUD, drops, armor models) is WIP in e599992.
- `claude/f-lasso` (495ee7b): lasso secondary with holder-run spring physics (the Roblox fling trick). Build was in progress.
- `claude/f-pip` (48940b1, WIP): killcam picture-in-picture (killer's POV box + LIVE reaction box).
- `claude/f-rig` (3e09b6e, WIP, based on update 1): OVERDRIVE RIG killstreak (cyber exo-frame: speed + afterimages,
  shield, charged punch + block, grapple quickhack, homing missiles, charged leap). Original design, no copied names.

## Queued requests (not started)
- Map pass: `handoff/map_todo/MAP_FIXES.md` (+ 2 screenshots): Suburb bigger and Nuketown-like with a tree border,
  Skyline/Rooftop streets below, Warehouse props + fenced yard, Bazaar gaps, out-of-bounds "RETURN 3 2 1" countdown.
- Two-stage end-of-match vote: mode first, then map (about 12 modes now).
- Parry: a dedicated rebindable "Parry" action once keybinds land.

## Rules that stay in force
- The Supabase secret key (sb_secret_..., service_role) stays server-side only (.env / Render env). Never in the exe,
  desktop/config.json, chat or the repo. Don't ask for or accept the DB password.
- Commits: identity `Claude <noreply@anthropic.com>`, messages end with the Co-Authored-By + Claude-Session trailers.
- Original designs only (no copied characters, logos or names from other games/shows).
- The owner merges PRs on GitHub; GitHub releases are created by the owner (release creation is blocked from sessions).
- Workflow subagents only see the user's LATEST message as "the request": for work asked earlier, use plain agents with the
  request quoted in the prompt, or they refuse.
