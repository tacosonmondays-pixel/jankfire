# The 100+ Combat VFX pack, photographed (20 Nov 2026)

The pack (skaterstudios, bought by the owner; the raw file stays in the vault, never in git) is 96 Parts, all named
"VFXTemplate". Here they are numbered by their order among the pack's Parts. That is the number `pack_templates.py`
takes as a `#n` pick, e.g. `"#40=BlastBurst"`.

## The sheets
- **Files:** `b1.jpg` … `b8.jpg`, 12 effects each in a 4 x 3 grid, frozen at 0.15 s and at 0.5 s, on mid-grey.
- **Sizes:** each effect is scaled to fit its cell, so the sheets do not compare sizes.
- **Teacher:** #50 is the practice loop's explosion teacher.
- **Tools:**
  - `tools/roblox/vfx/packs/catalogue.luau` is the rig. It runs client-side in Play, with the templates built there only and nothing added to the place.
  - `catalogue_sheet.py` numbers the cells.
- **Missing cells:** a few cells are empty at 0.15 s. Those effects start late or only run as a loop (an aura).

## What each one is (a first look; check the sheet before using one)
| # | Look |
|---|---|
| 1, 3 | small dark smoke puffs |
| 2, 8, 14, 20 | small bursts with dark bits |
| 4, 40 | big white star of spikes inside a shock ring, black streaks, gone by 0.5 s. #40 has an open middle and only 5 emitters: **BlastBurst** (the explosion's first beat, `Fx.explosion`) |
| 5 | white glow, then rippling rings on the floor plane |
| 6, 26 | faint swirl rings |
| 7, 42, 75 | white glow oval with dark dots, held to 0.5 s |
| 9, 12, 24, 41, 69, 77, 80 | wind lines and streaks |
| 10, 54, 66, 70, 73 | red bursts and red specks (read as blood: not used) |
| 11 | crossed slash lines in a sphere |
| 13 | white sparkle orb, then crackles |
| 15 | big pink-white starburst |
| 16 | white spark spray |
| 17 | dark smoke with a streak |
| 18, 27, 60 | soft glow balls (pink, red, orange) |
| 19, 30, 58, 63 | anime ink impacts: white core, black ink spikes and rings |
| 21 | orange star with yellow lightning, then grey smoke and sparks (a fiery blast with smoke) |
| 22, 31, 44, 47, 88 | red slash streaks |
| 23 | red and black spike burst |
| 25 | big purple lightning burst |
| 29, 87, 91 | orange fire ring with swirls and embers (87 and 91 show a square edge: check the black-backed rule) |
| 33 | gold lightning burst |
| 34, 81, 89 | white smoke puffs |
| 35 | white glow ball with sparks, then **a clean shockwave ring** at 0.5 s |
| 37 | black ink blobs |
| 38, 57 | debris and needles |
| 39, 46, 51 | white crescent / V slashes |
| 43 | white spark ring with needles |
| 45 | small white glow, then a ring |
| 48 | small lavender star |
| 49 | soft white smoke, then a big white crackle burst at 0.5 s (late) |
| 50 | the anime ink blast (practice teacher T_X50) |
| 52 | orange sun glow with a yellow star |
| 53 | faint grey sphere and ring |
| 55 | faint vertical ellipse |
| 61 | **cyan lightning** and a white burst inside a black ring (teal: the Star Drover set's impacts?) |
| 62 | thin red ring with spikes |
| 64, 67, 76 | white streak / motion smear |
| 68 | white sparkle cluster with black dots |
| 71 | cartoon white puffs, then dark cartoon smoke with green bits |
| 72 | white flash with spikes and **a glow ring** |
| 74, 93 | faint swirls |
| 78 | gold sparks, then a gold orb |
| 79, 90 | dark red smoke and red slash lines |
| 82 | blue electric orb with a spark ring |
| 83, 92, 94 | faint grey dust and scribbles |
| 84 | small ring, then a whirlpool vortex at 0.5 s |
| 85 | white swirl burst |
| 95 | gold flash, ring and needles |
| 96 | black and white vertical ink slashes |
| 28, 32, 36, 56, 59, 65, 86 | nearly empty in the photos (late or looping) |

## Picks so far
- **#40 → BlastBurst:** explosions (`Fx.explosion`: frag, Chicken Rocket, Overdrive).
- **Kill-effects' BLAST ZONE ring:** #35 or #72 (suggested).
- **Star Drover's teal spark:** #61 (suggested).
