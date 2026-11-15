# JANKFIRE sounds for Roblox (step 2)

Rendered from the web game's synth (`public/js/audio.js`) by `tools/roblox/render_sounds.cjs`. Roblox only plays
uploaded audio, so: upload each `.ogg` (Studio: **View > Asset Manager > Bulk Import**, or Creator Hub > Development Items >
Audio), then paste its id into the Sound with the same name in **ReplicatedStorage > JankfireSounds** (property
`SoundId`, as `rbxassetid://123...`). Until a Sound has an id, that sound just stays silent.

| file | what it is | length |
| --- | --- | --- |
| `gun_redline_k0.ogg` | Redline shot at full HP | 0.18 s |
| `gun_redline_k5.ogg` | Redline shot at half HP | 0.13 s |
| `gun_redline_k10.ogg` | Redline shot near death (screaming) | 0.11 s |
| `gun_marbles.ogg` | Marble Shotgun shot (boom + glassy clinks) | 0.33 s |
| `swing.ogg` | melee whoosh (katana swing / draw / parry) | 0.24 s |
| `bonk.ogg` | melee hit | 0.26 s |
| `hit.ogg` | hit marker tick (you hit someone) | 0.13 s |
| `headshot.ogg` | DINK: you landed a headshot | 0.4 s |
| `headshot_ko.ogg` | DINK, killing headshot | 0.63 s |
| `headshot_taken.ogg` | TONK: you took a headshot | 0.34 s |
| `headshot_taken_ko.ogg` | TONK, it killed you | 1.64 s |
| `hurt.ogg` | you got hurt | 0.3 s |
| `kill.ogg` | you got a kill (brass fanfare) | 0.98 s |
| `death.ogg` | you died (sad horn) | 1.62 s |
| `parry.ogg` | katana parry (struck blade) | 1.18 s |
| `parry_perfect.ogg` | katana PERFECT parry | 1.62 s |
| `tink.ogg` | small parry tink (more parries in one window) | 0.2 s |
| `ricochet.ogg` | perfect parry sends the bullets home | 0.26 s |
| `ting.ogg` | katana draw shing | 0.58 s |
| `clatter.ogg` | MARBLES! a pile of marbles going everywhere (you slipped) | 0.39 s |
| `whoops.ogg` | WHOOPS slide whistle (you slipped) | 0.78 s |
| `marble.ogg` | one marble clack | 0.11 s |
| `click.ogg` | weapon swap click / reload click | 0.11 s |
| `empty.ogg` | dry fire | 0.1 s |
| `reload.ogg` | generic reload | 0.31 s |
| `glug.ogg` | Redline reload: jerry can glug | 0.25 s |
| `rev_up.ogg` | Redline reload: VRRRAAP | 0.5 s |
| `boing.ogg` | Marble Shotgun reload: a marble bounces out | 0.35 s |
| `thwack.ogg` | Marble Shotgun reload: lid thwack | 0.14 s |
| `round_start.ogg` | ROUND START | 2.36 s |
| `round_end.ogg` | match over | 1.16 s |
