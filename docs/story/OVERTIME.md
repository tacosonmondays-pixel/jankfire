# Mr. Overtime: model, moves and fight hooks (WP9, the presentation half)

The combat referee (systems lane) owns HP, phases, hits and timing. This side owns how he looks and moves, the
cutscenes, and the preview fx. Story mode only.

## Model
- `public/models/cast/c_overtime.glb`, built by `tools/blender/cast/make_cast_overtime.py`. It is about 23.6k tris,
  plus a decimated far LOD per part. Built at unit scale; the game scales the root x2.5, so he is 5 m tall to the
  top of the lamp.
- Code fallback: `looks.js` `overtime()`, the same skeleton with the same named parts.
- Named pieces (`part_<joint>__<name>` in the glb), exposed as `L.parts[name]` and `L.partsAll[name]`:

| name | what | joint |
|---|---|---|
| `plate` | riveted chest plate with a porthole and a grapple handle | spine |
| `heart` | the punch-clock dial (glows white), the weak point | spine |
| `slot` | the glowing time-card slot (Punch In) | spine |
| `card` | his time card in the breast pocket | spine |
| `tie` | the bungee tie (the fight-2 tow). `tieEnd` marks the hook | spine |
| `cables` | the back cable bundle (fight 4) | spine |
| `gunR`, `gunL` | stapler forearms. `muzzleR` / `muzzleL` mark the staple | foreR / foreL |
| `head` | head, hair and the desk-lamp visor | head |
| `dmgCrack`, `dmgRip`, `dmgCardTorn` | damage pieces, hidden until needed | spine |
| `lod` | far LOD, shown past 45 m | every joint |

- Hitboxes for the referee's worker: `public/models/cast/c_overtime.parts.json`. Regenerate it with
  `node tools/blender/cast/otparts.cjs <port>` after any change to the model or to a clip's timing. Contents:
  - `parts`: centre and half extents of each piece, in metres, root space
  - `body`: a capsule
  - `markers`
  - `marks`: clip → mark → seconds
  - `clips`: hips and right stapler offsets through the big moves, sampled every 0.2 s

## Moves (`public/js/story/overtime.js`)
- Clips, played on the story actor:
  - `ot_idle`, `ot_stalk`
  - attacks: `ot_staple`, `ot_fan`, `ot_slam`, `ot_punchin`
  - phase and reaction moves: `ot_coffee`, `ot_roar`, `ot_flinch`, `ot_plate_rip`
  - endings: `ot_kneel`, `ot_limp`, `ot_clockout`
- Marks: sounds, steam and the preview fx fire at these times, so the tells line up with the referee's windows.
  - staple: clack 0.35, clack 0.7, fire 0.85
  - fan: ten clacks from 0.4, fan 1.6
  - slam: watch 0.3, steam 0.7, jump 0.92, land 1.42
  - punch in: slotOpen 0.35, grab 1.1, slotClose 2.3
- API, also on `window.JF_OT`:
  - `OT.play(a, clip)`
  - `OT.dmg(a, 'plate_off' | 'cracked' | 'sparking' | 'ripped' | 'card_torn' | 'fresh')`
  - `OT.variant(a, 1 | 2 | 3 | 4 | 'rehire')`: his look per fight, from `content/bosses.js`
  - `OT.on(ev => ...)`: `{ mark, clip, id, at }`
  - `OT.fx = false` turns off the preview staples and the slam ring
- Always on: steam from his stacks (more when he's angry), sparks from a broken heart, a ticking clock with a limp
  after the Heart Rip, a mug and flask on his coffee break, and the plate tumbling to the floor.

## Fight hooks (`public/js/story/bossfight.js`)
- Events arrive through `G.story.combat(ev)`, from the referee:
  - `hit`: a crit plays a flinch
  - `phase`: plays the phase cutscene, then his pose for that phase
  - `part`: shows the damage state
  - `act`: plays that attack clip
  - `kill`: the quest's `killBoss`
- Fight 1 (`m04_clocking_in`):
  - C4 gives him his stalk and idle poses, then the boss card.
  - Phase 1 plays `ot1_coffee` (he sits and pours).
  - Phase 2 plays `ot1_punching_in` (the roar).
  - The Heart Rip step sets ripped and kneeling.
  - After the 'rescheduled' talk, `ot1_retreat` plays: he limps off up the stairs.
  - The scenes are in `shared/story/content/scenes_overtime.js`.
- Fights 2–4 and the museum: the step whose `killBoss` names him puts him in that fight's look.
- Rehearsal stand-in for the referee: `JF_STORY.boss.test('overtime_1', 0.49)` = he's at 49% HP.

## Previews
- `?story=1&otpreview=1`: he runs his whole set on the Gut border landing, no damage, with captions.
  Record it with `node tools/otpreview.cjs --port <p>`, which writes `docs/story/scenes/ot_preview.mp4` and a sheet.
- `node tools/otscenes.cjs --port <p> [ids]`: films the fight-1 cutscenes (`ot1_coffee`, `ot1_punching_in`, `ot1_retreat`) on the gate
  arena's boss spot, one exact story step per frame however slow the renderer is. Writes `docs/story/scenes/<id>.mp4`
  and `<id>_sheet.jpg`. Slow: about 15 minutes a scene headless.
- `node tools/blender/cast/otstates.cjs <port> out.png`: every damage state, key pose and fight look.
- Turnaround: `tools/blender/sheets/c_overtime.jpg`.
