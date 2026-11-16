# Sounds (take 2, 16 Nov 2026)

The owner asked "can we get better sound effects?". Every sound the Roblox game plays has been rebuilt. The game now
also has footsteps, jumps, landings and slides of its own in place of Roblox's default plastic clip.

## What changed

| | before | after |
| --- | --- | --- |
| how they're made | the web game's Web Audio recipes copied 1:1 (`render_guns/items/loot.mjs`, `render_sounds.cjs`): one oscillator and one filtered noise each | `tools/roblox/render_sfx.mjs`: layered synthesis (transient, body, mechanical detail, room/echo tail), then saturation, a look-ahead limiter and peak normalising |
| levels | each file at whatever level its recipe gave; old gun shots sat at -21 to -35 LUFS as heard (the automatic guns quietest) | every Sound's `Volume` is set from its measured loudness so each category sits at a fixed level (table below) |
| repeats | one file per sound, the same every time | 2 to 4 takes for the sounds heard in runs (automatic guns, footsteps, swings, marbles); `Sfx` picks one at random, never the same twice running, plus a small random pitch nudge (`Jitter`) |
| distance | full brightness at any range | out in the world, the top end falls away with distance (from 40 studs, -14 dB above 4 kHz at 300 studs) |
| footsteps | Roblox's default `RbxCharacterSounds`: one looping plastic clip at a fixed rate, for every floor and speed | `Steps.client.luau`: a step per stride (pace rises with speed), by floor (hard, metal, wood, soft); jump, landing (louder the harder you land), slide scrape; other players' steps carry about 110 studs |

Spectrograms (40 Hz at the bottom, 20 kHz at the top, waveform above each):
[guns before](sounds/guns-before.png), [guns after](sounds/guns-after.png),
[confirms, handling, movement after](sounds/confirms-moves-after.png).

## Every sound, where it's played, before and after

All of them are `Sound`s in `ReplicatedStorage.JankfireSounds`, played by name through `client/Sfx.luau`
(`Sfx.play(name, at?, vol?, pitch?)`); `LootOpening.luau` goes through `Sfx` too, and `TheLot` / `RangeTest` on the
server play the same Sounds. Names didn't change, so no caller changed. Takes are `<name>#2`, `#3`, ...

**Guns** (`Arsenal.client.luau`, `Sfx.gun`; others' shots out in the world)

| sound | before | after (takes) |
| --- | --- | --- |
| `gun_ar` | 0.20 s noise sweep + square blip | rifle crack (N-wave), saturated blast with an 850 Hz body, chest thump, bolt clack, room + street echoes (x3) |
| `gun_smg` | 0.15 s, very thin | lighter, brighter 9 mm snap, short tail (x3) |
| `gun_burst` | 0.16 s | tight rifle shot for the three-round burst (x3) |
| `gun_lmg` | 0.18 s, quietest gun | heavy rifle, deeper body, belt-link rattle; heat still makes it louder and lower (x3) |
| `gun_dmr` | 0.5 s | hard supersonic crack, big body, long echo |
| `gun_sniper` | 0.8 s | the biggest crack, rolling echoes off the buildings to 1.8 s |
| `gun_shotgun` | boom + a square-wave "pump" baked in | big pink-noise boom, low thump, long tail (the pump comes from its own clip) |
| `gun_sawnoff` | 0.68 s | the biggest, lowest boom |
| `gun_autoshot` | 0.38 s | automatic shotgun boom with the action clacking twice (x2) |
| `gun_lever` | 0.4 s | rifle crack with a warm 520 Hz body, long echo |
| `gun_revolver` | 0.42 s | magnum: sharp crack, heavy boom, echo |
| `gun_pistol` | 0.24 s | snappy light pistol with the slide (x2) |
| `gun_marbles` | boom + clinks | shotgun thoomp, then 14 glass marbles clicking off things |
| `gun_redline_k0/k5/k10` | thin buzz by HP | rifle shot riding an engine bark: low and slow at full HP, screaming and short (0.16 s, up to 22 a second) near death |

**Hits and kills** (`Arsenal.client.luau`: the `Dmg` / `Callout` events)

| sound | before | after |
| --- | --- | --- |
| `hit` | 0.13 s blip | crisp high tick (2.9 / 4.4 / 6.3 kHz partials) over a small knock; cuts through gunfire |
| `headshot` | "DINK" square | bright metal dink (five inharmonic partials) over the hit tick |
| `headshot_ko` | longer dink | the dink, a lower bell under it, and weight |
| `headshot_taken` | "TONK" | dull helmet tonk, muffled |
| `headshot_taken_ko` | 1.6 s | tonk, muffled boom, a short faint ring |
| `hurt` | 0.3 s | muffled body hit |
| `kill` | brass fanfare | a punch and two clean chimes a fifth apart (A5, E6) |
| `death` | sad horn | low hit, the world going muffled, a soft falling tone |

**Melee** (katana): `swing` (whoosh, x2), `bonk` (the blade landing), `tink` (small parry / blade on a wall, x2),
`ting` (draw: the blade sliding out and ringing), `parry` (blade on blade), `parry_perfect` (bigger clang + rising
chime), `ricochet` (bullet whining off, x2). Before: single tones and noise bursts.

**Handling** (reloads and swaps: `Arsenal.client.luau`'s clip events): `click` (two-stage metal click, used at pitches
0.8 to 1.5 for most reload parts and UI), `empty` (dry fire), `reload` (mag seating, then the catch), `thwack` (heavy
clunk), `marble` (glass clack, also cases and belt links, x2), `glug`, `rev_up` (Redline engine rev), `boing` (a
marble bouncing out, seven bounces). Before: one blip each.

**Movement** (new, `Steps.client.luau`): `step_hard`, `step_metal`, `step_wood`, `step_soft` (x4 each), `jump` (x2),
`land` (x2), `slide`. Before: Roblox's default `Running` / `Jumping` / `Landing` (now silenced, with `Died`).

**Items** (`Utility.client.luau`): `boom` (frag: crack, blast, debris, 2.6 s rumble and echoes), `heal`, `reverse`,
`pop`, `blow`, `popper`, `squeak`, `quack`, `hole`, `ropesnap`, `shutter`, `whirr` (also the training doors),
`photoin`, `photoout`, `framepop`, `bloop`, `plip`, `glorp`, `bigpop`, `blub`. Same jobs as before, each rebuilt
with a transient, a body and a little room; the toy ones (duck, bubbles) kept their character but cleaner.

**Rounds, slips, loot** (`Arsenal.client.luau`, `TrainingDoors.client.luau`, `LootOpening.luau`): `round_start` (riser
into a bright hit and A-major chord), `round_end` (soft hit, settled D chord), `whoops` (a slip: falling whoosh, was a
slide whistle), `clatter` (28 marbles), `loot_tick`, `loot_land` (heavy crate), `loot_pop` (latch, air, lid),
`loot_win_common/rare/epic/legendary` (one chime, two, three + chord, riser + chord + arpeggio).

**Ambience**: none in the game yet (no Sound plays on its own); see "Not done".

## Levels

Target loudness as heard at the Sound's `Volume` (LUFS, loudest 400 ms; the calls' own `vol` multipliers come on top).
`render_sfx.mjs` measures each render and writes `vol` into `roblox/assets/sounds/v2/list.json`.

| category | targets |
| --- | --- |
| guns | heavy (sniper, sawn-off, shotgun) -17.5 to -18, DMR / lever / revolver -18.5, rifles and the Redline -19 to -21, light (SMG, pistol) -20.5 to -21 |
| confirms | headshot / kill -21 to -22.5, hit -25, hurt -25 |
| melee | parry -19.5 to -20.5, katana hit -21, swing -26 |
| handling | reload -26, click -29, dry fire -28 |
| movement | landing -27, slide -29, steps -33.5 (soft -35), jump -34 |
| items | frag -17.5, the rest -22 to -30 |
| rounds and loot | stings -20 to -24, crate land -21.5, tick -32 |

The new guns are 7 to 15 dB louder than the old renders as heard: the old automatic guns were so quiet the hit tick
was louder than the shot.

## How to change a sound

1. Edit its recipe in `tools/roblox/render_sfx.mjs` (DSP kit: `tools/roblox/sfx_dsp.mjs`), then
   `node tools/roblox/render_sfx.mjs only=<name>` (writes `roblox/assets/sounds/v2/<name>.wav` and its line in `list.json`).
2. Look at it: `node tools/roblox/sfx_sheet.mjs out.png roblox/assets/sounds/v2/<name>.wav` (waveform + spectrogram).
3. Upload the .wav as Audio (Open Cloud `POST /assets/v1/assets`, creator user 2833796200, from the approved upload
   folder), poll the operation for the id, put the id in `roblox/assets/sounds/v2/ids.json`.
4. In Studio set the Sound's `SoundId` and `Volume` (from `list.json`). Takes are Sounds `<name>#2`, `#3`.

To go back to the first renders: every replaced Sound keeps its old id and volume in the attributes `SoundIdV1` /
`VolumeV1`.

## Checks

- Every render looked at as a waveform + spectrogram sheet before upload (no clipping, no DC, tails fade to silence,
  no voice or words anywhere: it's all synthesis). Upload rules: `roblox-upload-content-rules`.
- 105 files uploaded on 16 Nov 2026 (ids in `roblox/assets/sounds/v2/ids.json`). In Studio: 77 Sounds swapped, 7 of
  them new (the steps, jump, land, slide), plus 28 takes: 105 Sounds in `JankfireSounds`. Saved as place version 417.
- Play test (16 Nov, 19:01 UTC): all 105 Sounds loaded (`IsLoaded`, real `TimeLength`); every one of the 77 played
  on its own with a peak `PlaybackLoudness` between 100 and 580 (none silent); walking 5 s on the hub's floor gave
  13 `step_hard` steps rotating through all four takes with the pitch nudge, and a jump played `jump`; the
  default `Running` / `Jumping` / `Landing` / `Died` Sounds were muted; no script errors.
- Not checked by ear: the sessions can't listen. Each render was judged from its spectrogram and loudness, so the
  owner's ears are the real test; any sound can be re-tuned in `render_sfx.mjs` and swapped by name.

## Not done (follow-ups)

- The reload clips still map most parts (mag out, charging handle, bolt, pump, shells) to `click` at different
  pitches (`VM.onEvent` in `Arsenal.client.luau`, owned by the guns session). Distinct `mag_out`, `bolt_back`,
  `pump`, `shell_in` sounds would need that mapping changed.
- No ambience: a quiet bed per zone (rooftop wind and distant city, hub room tone) would need a small client script
  keyed on the player's `Zone` attribute.
- No `splash` Sound exists yet (`Fx.luau` plays `splash` for water hits; it stays silent).
