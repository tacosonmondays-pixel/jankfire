# Mech style MK2: serious hardware, silly idea

The owner, 2026-11-13: "I want the mechs to be cooler different style from base game like gundam". The base game is
chunky toy-like low poly. The hero mechs (MECH DROP frames and Battle Island heroes) now step up to an anime
mecha look: real-robot hardware, sharp and layered, still one joke each. PAPER PLANE is the pilot
(`tools/blender/mechs/paperplane_mk2.py`). NIGHT SHIFT, WRECKING BALL, VENDING MACHINE and TROLLEY follow once the
owner says yes to it.

**Refs.** The owner's four pictures are on the `claude/look-refs` branch, in `docs/looks/refs/owner_2026-11-13_mecha/`.
They are REFS ONLY. Never copy a design, name, logo, pilot or character from them, and never put those images on `main`.
We take the mood from them: layered plates over a dark frame, glowing edge lines, sharp visors, stencils, a silly
idea built as serious hardware. Nothing else. The same goes for famous robots: no twin V-fin crest, no copied face
grille, no copied chest vents, no copied colour layouts. Every head, crest and chest is ours.

## The rules

1. **Heroic proportions.** A small head, a broad chest and shoulders, long legs, big hands and feet. The head
   is about a fifth of the shoulder span. The joints never move (the game binds them), so the proportions come
   from the armour: wide pauldrons, deep chest plates, chunky feet, a helmet kept tight to the skull.
2. **Layered armour over a dark frame.** White or team-colour shells sit over a gunmetal inner frame, and the
   frame shows at every joint: hips, knees, elbows, neck, waist, ankles, wrists. Plates overlap in two or three
   layers with gaps (seams) between them, never one smooth blob.
3. **Machined detail where it reads.** Panel seams, louvred vents, thruster bells with cooling rings, pistons and
   hydraulic rams at the joints, bolts around plates, hinges and hoses. Every edge gets a crisp chamfer, so the
   light draws a bright line along it. Detail parts go in `dt()` so the far LOD drops them.
4. **Clean paint: three tones and one accent.** Main (pearl white), team colour (the `paint` role: it takes the
   player's colour), dark frame (gunmetal and navy), and one small accent (yellow). Clear-coat car paint from
   `metalkit.py`. No gradients and no grime: crusty textures are for props.
5. **Glows.** Glowing eyes or a visor (the `glow` role) and emissive edge lines (the `thrust` role, cyan by
   default) set into dark channels: along wing edges, chest chevrons, shins and forearms. A few strong lines, not
   neon everywhere.
6. **Decals.** Unit numbers, chevrons, NO STEP and caution stencils, a serial plate, and our own maker names:
   JANK MOTORS, JANK AERO, PAPERWORKS. Stencil font, white or black, small. One sticker sheet per mech
   (one draw call).
7. **One silhouette idea per mech.** You can name the mech from its outline at 30 m:

   | hero | the idea |
   | --- | --- |
   | PAPER PLANE | two big folded delta wings in a high V behind the shoulders (a paper dart), a dart-nose crest |
   | NIGHT SHIFT | a knight with a tower shield and a long blade, a tall beacon crest |
   | WRECKING BALL | a round armoured pod body on a crane boom, the ball on its chain |
   | VENDING MACHINE | a tall glowing cabinet on legs, marquee crown |
   | TROLLEY | a low wide cart chassis, push bar, big casters |

8. **The joke, built for real.** Keep each hero's joke concept and execute it as hardware a studio would sign
   off on. PAPER PLANE's origami becomes crisp folded armour with real crease lines; the homing pencils become hex
   missile tubes whose warheads are sharpened like pencils; the highlighter cannons become twin beam barrels with
   chisel-cut muzzles; the origami crane drone becomes a faceted recon bit with a glowing eye.
9. **One small jank detail per mech.** Exactly one, small, found on a second look: a paperclip antenna, a cup
   holder, a sticker. It's JANKFIRE, but the rest stays serious.

## Tech (unchanged from MECHS.md)

- The joints, markers, clips and spray slots keep their names and joints, so the game binds a restyled mech
  without a code change. Markers keep their exact spots.
- Built with `make_hero.py` (two-pass far LOD, `metalkit` look, `merge_trim`, then `skin_glb.py`: one rigid-skinned
  mesh per LOD).
- Budgets: about 60-80k triangles near and about 15k far; 15-30 draw calls near and under 10 far, ink outline
  included (measured with `draws_game.cjs`).
- The QA gate (`make_hero.py ... qa`) passes with 0 errors on both LODs.
- Shots for every mech: a turnaround, a hero pose, and in-game Too HD + Potato next to the old model.
