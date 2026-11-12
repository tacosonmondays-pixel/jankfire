# Mechs: concept pass (phase 1)

Owner's ask: "a mech with that feel" (late-2010s anime battle-royale mechs), way higher quality than everything else.
Two original JANKFIRE frames. The research behind them (Super Mecha Champions, mobile-suit design language, the
anime feel, and what we avoid) is in `docs/mechs/RESEARCH.md`. Nothing here is copied: no names, logos, silhouettes or signature shapes from any game
or show (no V-fin, no wing binders, no capes, no crests from anything). Working names; the owner can rename them.

**Status: waiting for the owner's look approval.** Phase 2 (final detail, full rigs, clips, LODs, game files) starts
only after that.

## The pictures (all in `docs/mechs/concept/`)
| file | what |
|---|---|
| `paperplane_turnaround.jpg` | PAPER PLANE: front, side, back (rest pose, orthographic), 3/4 stance in colour A and B, jet mode |
| `nightshift_turnaround.jpg` | NIGHT SHIFT: front, side, back, 3/4 stance in colour A and B, a helmet close-up |
| `mechs_colours.jpg` | the two colour options for each, side by side |
| `mechs_silhouette_30m.jpg` | flat black at 30 m in the game's default view (FOV 95, 1080p): real pixel size inset, 3x zoom |
| `mechs_scale.jpg` | next to a 1.8 m mannequin and the Overdrive Rig, with a 1 m ruler |
| `paperplane_hero.jpg`, `nightshift_hero.jpg`, `mechs_duo.jpg` | path-traced hero shots |
| `ingame_*.jpg`, `mechs_ingame.jpg` | the same models in the real game (Training, Too HD), next to the game's mannequin |

## PAPER PLANE (the light flyer)
- **Size:** 4.85 m to the top of the helmet crest, wing tips at about 5.8 m. Long legs, narrow waist, small head.
- **Idea:** folded paper. Every plate is a crisp origami facet; the chest is a paper plane's nose with the cockpit
  canopy on its keel (the nose is the hatch); a crest fold runs over the helmet; the ears are folded flaps. The face
  is a **split shutter visor**: three glowing slats either side of a white keel (no eyes, on purpose). A
  **folded-crane emblem** on the chest.
- **Wing drone:** a little **origami crane** docked on the left wing (its own joint). It peels off, pecks the target
  and comes back.
- **Wings:** two folded paper halves hinged at the shoulder blades. Stowed up and out like a V behind the shoulders
  (the heroic silhouette); for jet mode they swing down flat into a dart. A FOLD HERE line with scissors on top,
  notebook paper underneath (blue rules, red margin, a biro smiley, "80 GSM").
- **Weapons:** homing missile pods on both shoulders, three sharpened **pencil missiles** each (pink erasers out the back).
- **Jank details:** a paperclip antenna on the left ear, a coffee cup in a cup holder on the right hip skirt, a
  HOW'S MY PILOTING? sticker on the backpack, a PERMIT 0451 parking sticker on the shin, A4 on the pod, 07 on the thighs.
- **Jet mode (shown):** body flat, legs together with the feet pointed, arms tucked, head up, pods turned forward,
  wings down. In phase 2 the legs can also fold at the knee if the owner wants a shorter jet.
- **Colours:** A **SKY MAIL** (sky blue, white, yellow, navy frame, yellow visor, cyan thrust).
  B **PINK SLIP** (hot pink, white, yellow, plum frame, cyan visor, pink thrust).

## NIGHT SHIFT (the heavy knight)
- **Size:** 5.7 m to the top of the helmet, about 6 m to the top of the beacon. Broad, heavy, short legs, big feet.
- **Idea:** a knight who works night security. A great helm with a **hard-hat ridge and peak** (hi-vis yellow), one
  glowing visor bar and a spinning amber **security beacon** on top (instead of a plume), a walkie-talkie antenna, a
  barrel breastplate with **hi-vis reflective bands**, a brass NIGHT SHIFT badge and a **timecard** stuck in a slot
  (clocked in, never out). The breastplate is the cockpit hatch (it drops like a drawbridge). Boosters on the back
  and low on each calf.
- **Sword:** a **snap-off blade** the size of a car (a box cutter's angled tip and snap lines) with glowing energy edges,
  a slider on the housing, a rubber grip and a chunky guard.
- **Shield:** a tower shield with a **PLEASE HOLD** LED display (a hold-music note, a progress bar stuck at 25%),
  hazard stripes, rivets and a STAFF PARKING ONLY sticker on the back. Held up in front, it reads the right way up.
- **Jank details:** a giant keyring with three keys and a coffee thermos (JANK COFFEE) on the belt, a torch on the
  right pauldron, 24/7 on the pauldrons, a HOW'S MY PILOTING? CALL 1-800-JANK sticker on the backpack.
- **Colours:** A **GRAVEYARD SHIFT** (royal blue, white, hi-vis yellow, navy, amber visor and edges).
  B **OVERTIME** (red, white, gold, near-black, cyan visor and edges).

## How they're built (so phase 2 keeps it)
- Code-built in Blender 5.2: `tools/blender/mechs/` (`mechkit.py` the kit, `paperplane.py`, `nightshift.py`,
  `make_mechs_concept.py` the sheets, `mech_game.cjs` the in-game shots, `preview.py` quick looks).
- A tree of joints (empties at their pivots) with rigid parts under each one: posing is turning joints, and the same
  tree becomes the skinned rig in phase 2. Joint names are in `docs/mechs/MECHS.md`.
- Paint is one material per role (`pp_paint`, `pp_white`, ... / `ns_paint`, ...), so team colours and the B colours
  are a colour swap. Glossy clear coat on the paint, metal frame, emissive visor / thrusters / edges.
- Concept files only: `docs/mechs/concept/*_concept.glb` (rest pose, colour A) + `*_poses.json` (the stance and jet
  mode as three.js quaternions per joint). Nothing is wired into the game yet and nothing ships in `public/`.
- Blockout tris: PAPER PLANE ~31k, NIGHT SHIFT ~37k (one LOD, solid colours, box UVs). Phase 2 adds the real detail,
  an atlas, crusty wear, LODs and the tri report per LOD.
- Asset gate: 0 errors on both (`-- mech=<name>` runs it). Warnings accepted for a blockout: box UV overlap, flat n-gons.

## Run it
```
blender52 -b -P tools/blender/mechs/make_mechs_concept.py -- mech=paperplane   # QA gate, glb + poses, turnaround, hero
blender52 -b -P tools/blender/mechs/make_mechs_concept.py -- mech=nightshift
blender52 -b -P tools/blender/mechs/make_mechs_concept.py -- stage=combine     # scale, silhouettes, colours, duo
PORT=3100 node server.js &  node tools/blender/mechs/mech_game.cjs 3100         # in-game shots (Too HD)
blender52 -b -P tools/blender/mechs/preview.py -- paperplane <dir> q,front,side 16 ready   # quick looks
```

## Questions for the owner
1. Do the two looks feel right? Anything to push harder (more anime, more jank, bigger/smaller)?
2. Colour A or B as the default for each (team modes use the team colour on the paint either way)?
3. Names: keep PAPER PLANE and NIGHT SHIFT?
4. Jet mode: straight legs (shown, sleeker dart) or legs folded at the knee (shorter, chunkier)?
