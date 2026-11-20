# VFX practice loop (from 20 Nov 2026)

The owner: "Are you training off the vfx!! Copy what you see, review it try again and again until you get better and
better at it!!" The bought packs are the teacher. The pack effects stay what we ship where they fit; this loop exists
so we get better at making our own. What we learn goes in [PLAYBOOK.md](../PLAYBOOK.md).

## The loop, per category
1. **Pick** one pack effect (the teacher).
2. **Capture** it: the practice rig fires six copies, each timed so that at the freeze it is 0.05 / 0.1 / 0.2 / 0.35 /
   0.6 / 1.0 s old, and freezes them together (TimeScale 0). One photo shows the whole life, left to right. It's shot
   on a mid-grey wall and on a near-black one (black halos hide on dark). A third-size copy on the sheet shows the far
   view.
3. **Dissect** it from its settings into a written anatomy ([anatomy.md](anatomy.md)).
4. **Rebuild** it as our own, with our own textures only: numpy drawings in `tools/roblox/vfx/practice/draw_*.py`
   plus the library in `roblox/assets/vfx`. Layer specs per round are in `tools/roblox/vfx/practice/own_effects.py`.
5. **Review**: the pack's row and ours in the same photo. A critic subagent scores ours 1-10 against the pack and lists
   concrete fixes.
6. **Repeat** until 8/10 or 6 rounds. Every round's sheet is kept in `r<n>/`.

## Teachers (round 0, place version 1148)
| Category | Teacher | Template |
|---|---|---|
| Hit flash | Combat "Punch-01" | JankfireVfx.HitPunch1 |
| Guard break | Combat "Guard break" + "Guard break 2" | JankfireVfx.GuardBreak1 + GuardBreak2 |
| Dash / speed lines | Combat "dash" | JankfireVfx.DashPuff |
| Slash | Combat "Slash-03" (a spin slash; Slash-04 read as a sparkle burst, see r0) | VfxPractice.T_Slash3 |
| Ground impact / crack | Combat "Slam" (+ "Crack-02") | JankfireVfx.HitSlam + VfxPractice.T_Crack2 |
| Explosion | 100+ pack effect #50 (an anime ink blast) | VfxPractice.T_X50 |

## Results (six rounds, 20 Nov 2026)
| Category | Round 1 | Best | Progress sheet |
|---|---|---|---|
| Hit flash | 4 | 8 (round 5) | `progress/hit.jpg` |
| Slash | 4 | 8 (round 4) | `progress/slash.jpg` |
| Explosion | 5 | 8 (round 6) | `progress/explosion.jpg` |
| Guard break | 3 | 7 (round 6) | `progress/guard.jpg` |
| Dash | 2 | 7 (round 6) | `progress/dash.jpg` |
| Ground impact | 3 | 7 (round 5; round 6 slipped to 6) | `progress/slam.jpg` |

Each progress sheet shows round 1 against the best round. The lessons are in `docs/vfx/PLAYBOOK.md`.

The critic's notes for a seventh round, if one is wanted:
- **Guard break:** fewer, mostly whole, thicker rings, and four big blade clusters.
- **Dash:** speed lines half as bright, and none left after 0.35 s.
- **Ground impact:** clouds back to 10-40 studs/s and size 1.6, to reopen the hollow middle.
- **Explosion:** 2-3 fat flicks at 0.2 s instead of about 8 thin needles.

## Where things live
- **Studio, all in ServerStorage (never shipped to players):**
  - `ServerStorage.VfxPractice`: the teachers built from the packs (T_*) and our rebuilds (O_*).
  - `ServerStorage.VfxPracticeRig`: the rig module.
  - In Play the server copies both into ReplicatedStorage (`VfxPracticeRT`, `VfxPracticeRigRT`). The client then calls
    `require(ReplicatedStorage.VfxPracticeRigRT)({ cat, D, bg, ground, ages, rows = { {names, scale, dy, spin}, ... } })`.
- **Our practice textures** (white on transparent; uploaded under the owner):
  - vfx_hitstar_4x4 123343427727495
  - vfx_gbreak_ring_4x4 88961349137378
  - vfx_gbreak_burst_4x4 113903648900633
  - vfx_arc 119340562514320
