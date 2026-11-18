# Weapons batch A: minigun, water gun, nail gun, bread, slap (18 Nov 2026, place version 771)

Asked for by the weapons-port session. All are Pro Sound Effects recordings, levelled from `store.json` like the
others. Two new `store.json` fields, handled by `store_sounds.mjs`: `loop` (the Sound is Looped, over its region) and
`roll` ([RollMin, RollMax] attributes: how far Sfx lets a copy out in the world carry).

| name | for | take(s): id, title, cut (s) | Volume | notes |
| --- | --- | --- | --- | --- |
| `gun_minigun` | one shot at 25/s | 9116922304 / 9116922596 / 9116922611 Minigun Metallic Reflections 1 / 2 / 3, 80 ms slices (0.3, 0.5, 0.7 s in) | 1.04 | slices of a real burst: at 25/s two overlap and run together into the burst. Levelled on the burst's L −24, not the slice's |
| `minigun_spinup` | 0.6 s | 9116980359 Motor Whine Electric Whirring Buzzing 11, 0.05–0.65 (the motor starting) | 0.12 | the same motor as the loop and the spindown, so they join |
| `minigun_spin` | the barrels spinning | same recording, 0.8–2.8, **Looped** | 0.12 | steady part of the whine. Play it by cloning the library Sound: `Sfx.play`'s copy is destroyed after 6 s |
| `minigun_spindown` | 0.9 s | same recording, 3.0–3.9 (the motor stopping) | 0.12 | |
| `gun_water` | one squirt at 9/s | 9119518756 / 9119519807 / 9119519818 Spray Bottle 1 / 2 / 4, ~0.15 s each | 1.3 | carries 8–200 studs (`roll`) |
| `water_soak` | the soaked person | 9117946641 / 9117947974 Puddle Stomps Small Water Splashes 3 / 18, whole | 6 (set) | quiet recordings, so Volume set by hand; carries 6–120 |
| `gun_nailgun` | one shot at 11/s | 9117052716 / 9117051336 / 9117052397 Nail Gun Pneumatic Air Bursts 4 / 7 / 1, one burst each (~0.12 s) | 0.96 | |
| `nail_wall` | a nail into the wall, quiet | 9119579178 Staple Gun 1, 0.13–0.4 | 0.23 | carries 6–150 |
| `nail_pinned` | 4–5 nails into a pinned person | 9117053526 Nail Gun Single And Rapid Fire Nails 1, 0.02–0.6 | 0.26 | |
| `bread_bonk` | a big loaf hitting someone | 9113497639 Body Hit Ham Hits 12 and 9113487557 Body Hit 7, 0–0.3 | 1.95 | soft heavy thuds, nothing squeaky. The two takes sit 5 dB apart (L −31 / −26) |
| `slap_hit` | a big flat slap | 9114771792 / 9114772106 Hand Slap Claps 3 / 10, 0–0.25 | 1.84 | |
| `slap_whoosh` | the slap's swing | 9120972321 Wood Whoosh Slicing Air Quick Swings 4, 0.02–0.3 | 1.3 | |
| `draw_minigun` | the heavy draw | 9116357621 Machine Gun Bolt 4, 0–0.7 (bolt back and home) | 0.52 | |
| `reload_minigun` | the 3.5 s reload | 9113103014 Ammo Box Movement 2, 0.1–3.0 | 3 (the cap) | an ammo can handled, opened and shut, over 2.9 s |

Volume groups (SettingsApply `kind`): `gun_*` and `draw_minigun` follow WEAPONS. The rest follow EFFECTS unless
they're added to WEAPON_NAMES. Checked in Edit: every clip loads, every cut measured. Not heard in Play. The spin loop's
seam (2.8 → 0.8 s) wasn't checked by ear.

---

# Grenade cooking and the katana's new moves: eight new sounds (18 Nov 2026, place version 749)

Asked for by the utility session (the owner: "allow us to cook grenades pls") and the katana session (endless
parry, a crit return on a timed swing, a charged slash wave). All are Pro Sound Effects recordings, cut and levelled
by `store_sounds.mjs only=...` from `store.json`; L is the analyzer loudness of the cut.

| name | plays | take(s): Pro Sound Effects id, title, cut (s) | L | Volume |
| --- | --- | --- | --- | --- |
| `pin` | on you as you start cooking a frag or smoke (G) | 9114659833 Grenade Pull Pin 2, whole (0.33 s) | −40 | 3 (the cap) |
| `fuse_tick` | on you, 4 times in a cooked grenade's last second | 9114071134 Dial Switch Twisting Sharp Ticking 79, 0.13–0.23; 9114068074 … Ticking 26, 0.18–0.28 | −42 / −44 | 2.6 |
| `crit_return` | the katana batting a bullet back on a timed swing | 9119028721 Sever Metal Hit 2, 0–0.6; 9119746759 Sword Hit 3, 0–0.4 | −12 / −15 | 0.55 (1.5 dB over `parry_perfect`) |
| `wave_cast` | the charged slash wave leaving the blade | 9120728815 Whoosh Heavy Punches 1 and 9120729339 … 7, both 0.03–0.6 | −19 | 0.65 |
| `wave_fly` | the wave in flight, positional | 9119227910 Slow Whoosh Beefy Airy Pass By 4, 0–0.85; 9119228137 … 6, 0–0.8 | −27 | 0.73 |
| `wave_hit` | the wave hitting a body | 9113502506 Body Hits 8, 0–0.45 | −25 | 1.16 |
| `wave_wall` | the wave breaking on a wall: impact + short ice crackle | 9114857473 Ice Chunk Drop Onto Concrete Some Break 3, 0.38–1.1; 9114857058 … 5, 0.33–1.03 | −18 / −19 | 0.55 |
| `edge_full` | the katana meter full, on you only | 9119076918 Shing Ringy 4, 0.03–0.6 | −16 | 0.18 |

Pitch jitter 3% on all but `pin` and `edge_full`. Every cut was measured in Studio: each ends 35 dB or more below
its peak, except `wave_wall`'s first take, which stops 21 dB down inside its crackle. `Sword Stab 1` was dropped from
`wave_hit`: its second sound runs past the cut. Volume groups (SettingsApply `kind`): all eight fall under EFFECTS,
since none is `gun_`/`skin_` or in WEAPON_NAMES. Checked in Edit (each clip loads), not heard in Play.

---

# Gunfire where it happens (17 Nov 2026, place version 737)

The owner, from the live preview: "gun fire audio should be proportional to where players are". `Sfx.luau` now
places every sound that has a position in the world the same way:

- **Where:** someone else's shot plays as a 3D sound at their muzzle. That's the gun's `Muzzle` (or `TP.muzzle`, where
  you see their gun) at the moment their `Shot` event reaches you; the server sends it to everyone but the shooter, so
  it's always their position, never yours. Their swings, gadget throws, blasts and (new) reloads play where they
  happen too. Your own shots stay close and on you, as before.
- **How loud by distance:** `RollOffMode` InverseTapered for every world copy. RollOffMin / Max by name in `ROLL_EXACT`
  / `ROLL_PREFIX` (a Sound's `RollMin` / `RollMax` attributes still win):

  | sounds | Min | Max | so |
  | --- | --- | --- | --- |
  | `gun_*` (shots) | 12 | 520 | full inside 12 studs, −10 dB at 40, −21 dB at 120, −29 dB at 300 (with the far take), gone past 520 |
  | `boom` / `blow` / `hole` (blasts) | 24 / 16 / 18 | 1100 / 650 / 750 | carry further than a shot |
  | `skin_*` (skin layers) | 8 | 220 | a decoration: fades before the shot does |
  | `swing`, `ting`, `bonk`, `tink`, `thwack` (melee) | 6 | 150–170 | |
  | `click`, `reload`, `empty` (handling) | 4 | 60–90 | a reload is heard a few strides off |
  | everything else | 15 | 600 | (footsteps keep their own `RollMax` 110) |
- **Far away sounds far:** gunshots and blasts get a far take. From 60 to 90 studs (`NEAR_END`, `FAR_FULL`) the close
  take crossfades (equal power) into a copy that's thin and dull (EQ Low −8, Mid 0, High −20 dB, ×0.9). Both arrive
  late by the distance over the speed of sound (1,225 studs/s, so 0.1 s at 120 studs; at most 0.4 s).
- **Walls:** one ray per sound from your camera (the listener) to the sound. Players' bodies and non-colliding parts
  don't count. If something solid is in the way, the sound dips: Mid −5, High −12 dB and ×0.6.
- **Others' reloads:** `ThirdPerson` replays another player's reload from the reload flag on their rig. Now it also
  plays the mag out (`click`, lower) as it starts and the mag in (`reload`) 60% through, at their gun.
- **Recorded distance takes slot in by name.** This is for a library like BOOM's Tactical Guns, recorded 0–100 m.
  Add Sounds named `<sound>@<studs>` next to `<sound>` (1 m = 3.57 studs: 25 m = `gun_ar@89`, 50 m = `gun_ar@179`,
  100 m = `gun_ar@357`). Sfx finds them by name (no code change) and then, for that gun, drops the made-up far take.
  A shot crossfades between the two recordings either side of its distance (the plain one counts as 0 studs), and
  the roll-off, delay and wall still apply. `store_sounds.mjs` levels an `@` take like its close take unless
  `store.json` gives it its own target.

Checks (v737, one solo Play). A test platform at y 2000 held stand-ins (a Head only) at 10, 40, 75, 120 and 300
studs straight ahead, one 40 studs to the left and one 40 to the right. The real `Shot` event was sent to the
client from each (`w = "ar"`), with the camera (the listener) pinned at the ear point looking at them. A log on the
client read every world Sound as it started: its distance, the engine's gain (InverseTapered), Volume, EQ, wall,
delay, and where it sat in camera space.

| shot from | layer | level | vs 10 studs | EQ (low/mid/high) | late | side |
| --- | --- | --- | --- | --- | --- | --- |
| 10 studs ahead | near | 0.520 | 0 dB | none | 0.008 s | centre |
| 40 ahead | near | 0.156 | −10.4 dB | none | 0.033 s | centre |
| 75 ahead | near + far, half each | 0.059 + 0.053 | −16.3 dB | far copy −8/0/−20 | 0.061 s | centre |
| 120 ahead | far | 0.047 | −20.9 dB | −8/0/−20 | 0.098 s | centre |
| 300 ahead | far | 0.019 | −28.9 dB | −8/0/−20 | 0.245 s | centre |
| 40 to the left | near | 0.156 | −10.4 dB | none | 0.033 s | LEFT, −90° |
| 40 to the right | near | 0.156 | −10.4 dB | none | 0.033 s | RIGHT, +90° |
| 40 behind a wall | near | 0.094 | −14.8 dB (−4.4 for the wall) | 0/−5/−12 | 0.033 s | centre |
| 120 behind a wall | far | 0.028 | −25.3 dB (−4.4 for the wall) | −8/−5/−32 | 0.098 s | centre |

Each sound sat exactly at its shooter's head, the muzzle stand-in, in camera space: (0,0,−40) ahead, (−40,0,0)
left, (40,0,0) right. Roblox pans a 3D Sound by where it sits from the camera, so the left and right shots come
out of the left and right ear. For someone else's reload, a copy of the player tagged `TPRig` stood 6 studs off
with the reload flag raised. The test heard `click` at 7 studs (gain 0.57) as the reload started, then `reload` at
6 studs 1.0 s later, both from the right where that copy stood. Your own shots take the unchanged path, no position,
in SoundService: not re-tested this run. No new errors in the output.

---

# No crowd sound anywhere; grapple charge sounds (17 Nov 2026, place version 665)

The owner: "why is the crowd sfx still there i want it gone completely". The crowd was the hub's area sting,
`zone_hub` (Freesound "Murmur.wav" by stewadosan, 466767), which played on arriving in the hub from anywhere.
- `ZoneSounds.client` plays nothing on arriving in the hub, from anywhere: training, the playground, the lot, the VIP
  room or after a match. No other sound replaces it.
- The Sound `zone_hub` is deleted from `JankfireSounds`, its row is out of `store.json` (so `store_sounds.mjs` can't bring
  it back), and its cut `recorded/zone_hub.wav` is deleted. The credit line stays, marked unused.
- The audit: every Sound saved in the place was listed (144: 139 in `JankfireSounds`, 5 on the back lot's timer
  panel), with every asset's title, plus every script that makes a Sound at runtime (only `SpeedLines`' wind loop,
  PSE 9113286782). No other crowd, murmur, chatter, cheer or voice sound. There is no hub ambience loop.
- One more, to be safe: `slide` was "Baseball Runner Slide On Dirt Into Home Plate" (PSE), whose recording has a steady
  background bed about 20 dB under the slide. It could have been a ballpark crowd. Now it's "Slide On Wood 1 (SFX)"
  [0.05–0.85 s], a clean studio take that falls to silence after the scrape.

Two quiet sounds for the ranked grapple limit (2 charges, one back every 6 s; `HookChargesUI`, the
play-party-ranked session's), both on your screen only:

| Sound | when | recording |
| --- | --- | --- |
| `hook_empty` | you press grapple with no charge left | PSE: Wood Hit Giant Wood Beam Dull Thuds Knocks 1 (SFX) [0.02–0.4 s]: one dull knock |
| `hook_ready` | a charge comes back | PSE: Metal Ratchet Small Ratchet Clicks 13 (SFX) [0.08–0.32 s]: four quick ratchet ticks |

Levels: targets −31 and −32 (quieter than the dry-fire click), slide −29 as before.

Checks: one Play test (17:30 UTC, place version 665), logging every sound that started except footsteps. Through the hub's real door to training (`RotundaToTraining`): `zone_training`. Back to the hub: nothing. To the playground: `zone_playground`. Back to the hub: nothing. As a session-only VIP, to the VIP door, into the room and back out: only `door_vip_slide`, `door_vip_bell` and the closing slide. `zone_hub` no longer exists in the library. `slide`, `hook_empty` and `hook_ready` all load. The grapple sounds weren't triggered here: the play-party-ranked session hears them in its ranked test.

---

# VIP door, jump pads, the RANKED flame (17 Nov 2026, place version 654)

Four recordings, each asked for by the owner:

| Sound | what | where it's played | recording |
| --- | --- | --- | --- |
| `door_vip_slide` | the VIP door's leaves sliding open (and, softer and a little lower, shut) | `HubVip.client`, at the door, VIPs only | PSE: Sliding Glass Door 1 (SFX) [0.05–1.0 s] |
| `door_vip_bell` | a counter bell, once the leaves are fully open | `HubVip.client`, at the door | PSE: Desk Bell Counter Service Single Ringing Din (SFX) [0.17–1.4 s] |
| `pad_launch` | a jump pad throwing a body | `Steps.client`: yours on you, anyone else's at the pad, quieter | PSE: Air Bolt Gun 4 (SFX) [0–0.5 s], pitch ±4% |
| `ranked_fire` | the RANKED switch's flames lighting | `PlayUI` (`setFire`), on your screen | Freesound: "Fire Trap" by qubodup (739487), CC0 |

**VIP door.** The owner: "the door to the vip can you make a sliding door sound with the bell happening before it
opens? make it to it cant be spammed!", then "when the vip doors open after they open ding, I think thats a good spot".
Each door is one state (closed, opening, open, closing). It opens within 10 studs and closes only past 14, so walking
along the edge can't flap it. It stays open at least 2 s. It dings once per opening, and never twice within 5 s (a quick
reopen just slides). Non-VIPs: the door stays shut and silent. When ZoneCull brings the hub back, the door is set
straight to where it should be, with no sound. The owner also said "when you step out I think there's like a crowd
sound effect, I don't want that, cut it to just the bell", so `ZoneSounds` plays nothing between the hub and the VIP
room in either direction. `zone_vip` is now never played. (`zone_hub` still played for every other way into the hub
until place version 665, which removed it.)

**Jump pads.** The owner: "do bounce pads have a sound effect?" `Move.client` throws you off a part whose `Pad`
attribute is a Vector3. `Steps.client` watches every body: when one leaves the ground going up faster than 25
studs/s, one short ray down asks whether it left a pad, and if so `pad_launch` plays, at most once per 0.4 s per body.
The same spot calls `PadSignal.fire(pad, character, mine)` (the VFX session's module, found without waiting) so the
pad's glow and the sound start together.

**RANKED flame.** The owner: "also there should be like a rahh flame fshhh sound when its turned on". It plays as the
flame sweep starts when you switch RANKED on, never when the panel opens with ranked already on (that's drawn
instantly). At most one per 1.5 s, and switching off while it plays fades it out in 0.2 s instead of stacking another.
Party Ranked's bubbles stay quiet. `Sfx.play` now returns the playing copy so a caller can fade or stop it.

Levels (an AudioAnalyzer's loudest 0.4 s → targets, `store.json` `targets`): bell −27, slide −26, pad −27, flame
−25, set by `node tools/roblox/store_sounds.mjs only=door_,pad_,ranked_`. All four load.

Checks (place version 654, one Play test, 16:57–17:02 UTC, logging when each sound starts):
- VIP door, as a session-only VIP: from 21 studs out to 8, the slide at 1.03 s and the bell at 1.30 s (the
  leaves done). Six hops between 12 and 13.5 studs, then the doorway: nothing. Out to 19 studs: the soft slide. Back
  within 5 s: the slide, no bell. Out again, wait 6 s, back: slide and bell. Into the VIP room and out: no `zone_*`.
- Hub pad (the Rotunda's): placed on it twice, 3 s apart: thrown twice, `pad_launch` twice, each 0.04 s after the throw.
- RANKED: ON, OFF 0.5 s later, ON 0.4 s after that: one `ranked_fire`, faded out at OFF, none at the second ON.
  Closing and reopening the panel (the `PlayTest` hook) with ranked on: silent.
- Not proved: a Rooftop pad. Standing on `Map.Rooftop.Pads.pad` outside a match didn't throw the body at all
  (`Move.client`'s own check), so there was nothing to hear. The sound code doesn't depend on which map the pad is in.
  Nobody here can listen: the owner's ears are the real check.

---

# Special skin layers and area stings (17 Nov 2026)

## Special skins (place version 583)

The owner: "make sure special weapons have custom bullet trails and sfx that match the style of the gun". Each
high-tier skin plays a short themed recording ON TOP of its base gun's own sound, quieter (about 8 dB under the shot)
and at most about 0.6 s, so gunfeel and loudness stay fair. Table: `roblox/src/shared/SkinSounds.luau`; played by
`Sfx.gun` (your shots and other players', found by who stands at the muzzle), `Sfx.skinEvent` (one line in
`Arsenal`'s `VM.onEvent`) and `Sfx.skinHit` (one line at the katana hit). Bullet trails are the VFX session's. The
`skin_*` Sounds follow the WEAPONS volume (SettingsApply, place version 577).

| skin | layer, when | layer, when |
| --- | --- | --- |
| Seraph Rifle `ar_seraph` | shot: PSE: Glass Tinks 2 (SFX) [0.15–0.65 s] | mag in: PSE: Violin String Pluck Single Notes 3 (SFX) [0–0.5 s] |
| Infernal Rifle `ar_infernal` | shot: PSE: Fire Whoosh 15 (SFX) [0.05–0.6 s] | mag in: PSE: Sizzle Short And Explosive Sear 12 (SFX) [0.07–0.6 s] |
| Pumpkin Patch `smg_pumpkin` | shot: PSE: Wood Impacts Soft Impacts On Temple Blocks 1 (SFX) | mag in: PSE: Wood Groan Creak Opening Wood Chest Coffin 1 (SFX) [0.1–0.6 s] |
| Sakura `katana_sakura` | swing: PSE: Wind Chimes Random Metal Ceramic Clinks 1 (SFX) [0.1–0.6 s] | hit: PSE: Wood Impacts Soft Impacts On Temple Blocks 6 (SFX) |
| Bubble Bath `lmg_ducky` | shot (+ squeak every 5th): PSE: Pop Airy 9 (SFX) [0–0.1 s] | mag in: PSE: Mud Puddle Splash Shallow Water Impacts Hits (SFX) [0–0.6 s]; squeak: PSE: Squeeze Toy Squeaky Rubber With Noisemaker H (SFX) [0–0.3 s] |
| Wish Duck `revolver_ducky` | shot: PSE: Synth Sparkle Tone High Pitch Tone Burst Pin (SFX) [0–0.6 s] | cylinder spin: PSE: Squeeze Toy Squeaky Rubber With Noisemaker H (SFX) [0–0.26 s] |
| Ribbon Duck `katana_ducky` |  | hit: PSE: Squeeze Toy Squeaky Rubber With Noisemaker H (SFX) [0.26–0.56 s] |
| Dust Drover `revolver_dust` | 35% of shots: PSE: Ricochet Reverberant 3 (SFX) [0.06–0.6 s] | cylinder spin: PSE: Horse Harness Bells Small Metallic Ringing 3 (SFX) [0.84–1.4 s] |
| Iron Horse `lever_dust` | shot: Freesound: "Musket Explosion" by Willlewis (244345) | lever cycle: PSE: Steam Piston Pump 10 (SFX) [0.04–0.6 s] |
| Star Drover `revolver_star` | shot: PSE: Laser Cannon 1702 (SFX) [0.34–0.9 s] | cylinder in: PSE: Servo Motor 1 (SFX) [0.05–0.52 s] |
| Streamliner `lever_star` | shot: PSE: Plasma Swish 1 (SFX) [0.03–0.5 s] | lever cycle: PSE: Relay Clicks 9 (SFX) [0–0.3 s] |
| Triangulum `sniper_triangulum` | shot: PSE: Magic Glows Soft Clusters Of Chiming Hits 2 (SFX) [0–1 s] | bolt: PSE: Synth Sparkle Tone High Pitch Bell Tone Burs (SFX) [0.25–0.7 s] |

Iron Horse has no train whistle on a kill (the sheet called it optional).

## Area stings (place version 583)

The owner: "can you have a sfx when entering and leaving areas?" `roblox/src/client/ZoneSounds.client.luau` plays
one soft sting, for you alone, as you arrive in an area, so leaving one plays the next one's. About a second each,
quiet (between footsteps and gunfire), on the EFFECTS volume.

| area | how it's known | sting |
| --- | --- | --- |
| hub | server `Zone` = hub | none since place version 665 (was a crowd murmur, Freesound "Murmur.wav" by stewadosan, 466767: the owner wanted it gone) |
| training hall | `Zone` = training | Freesound: "Air Hiss" by Jofae (367125) |
| playground | `Zone` = playground | Freesound: "light slow swoosh.mp3" by Mikes-MultiMedia (349698) |
| back lot | `OnLot` (TheLot) | Freesound: "Wind Gust" by crashoverride6 (146932) |
| VIP room | inside the part tagged `VipRoom` | Freesound: "singing bowl strike sound" by inoshirodesign (271370); since place version 654 never played (the door's slide and bell instead) |
| private lobby | inside a room of `workspace.PartyLobbies` | PSE: Soft Suck Explosion Med Whoosh 8 (SFX) [0–1 s] |

Quiet on purpose: the first area after spawning or respawning, anything to or from a match (the round has its own
sounds), and a second sting within 1.5 s. The shop corner isn't an area of its own.

Checks (place version 583, Play test): all 30 new Sounds load; the skin lookup maps each skin's weapon to its rows and
every named Sound exists; moving the test character gave `zone_lot`, `zone_hub`, `zone_playground`, `zone_hub` in
order. A second test (11:25 UTC) entered training through a door the server moves you by, and the VIP room as a
session-only VIP (the VIP remote's Studio "dev" unlock): `zone_training`, `zone_hub`, `zone_vip`, `zone_hub`, so all six
areas but the private lobby (its rooms only exist while a party is in one) were seen to start playing. Not checked: firing a
skinned gun end to end (it needs a skin equipped; the test left the
player's real skins alone). Nobody here can listen: the owner's ears are the real check.

---

# Sounds (take 3, 16 Nov 2026): recordings

The owner, after take 2: "I don't want code generated sounds", and pointed at Freesound. Every sound the game plays is
now a real recording: about half from **Pro Sound Effects**, the professional library Roblox licenses for every
experience (played straight from Roblox, nothing uploaded, no licence to track), and the rest from **Freesound**,
CC0 (public domain) only, downloaded as the site's public high-quality previews, cut to one event each and uploaded
to the owner's account. No user uploads from the Creator Store (many are rips from other games), no voices.

How they were picked, since nobody here can listen: each candidate was played silently into an `AudioAnalyzer` in
Studio (or decoded with Blender's audio module for the Freesound files) to read its length, peak, loudness and the
moments new events start, so each take is ONE shot / step / hit. A `PlaybackRegion` plays just that slice of a
longer library clip. Volumes put each name at the level take 2 planned for its category (`store.json`).

| name | takes: source, recording |
| --- | --- |
| **Guns** | |
| `gun_ar` (x3) | PSE: Machine Gun 1 (SFX) [0–0.6 s]; PSE: Machine Gun 6 (SFX) [0–0.8 s]; PSE: Machine Gun 4 (SFX) [0–0.85 s] |
| `gun_smg` (x3) | PSE: 9 Mm Gun Firing 1 (SFX) [0–0.5 s]; PSE: 9 Mm Gun Firing 2 (SFX) [0–0.5 s]; PSE: 9 Mm Gun Firing 5 (SFX) [0–0.5 s] |
| `gun_burst` (x3) | PSE: Assault Rifle 3 (SFX) [0–0.4 s]; PSE: Assault Rifle 9 (SFX) [0.01–0.34 s]; PSE: Assault Rifle 13 (SFX) [0–0.35 s] |
| `gun_lmg` (x3) | PSE: Machine Gun 4 (SFX) [0–0.8 s]; PSE: Machine Gun 6 (SFX) [0–0.8 s]; PSE: Machine Gun 2 (SFX) [0–0.7 s] |
| `gun_dmr` | PSE: Gun Retort 1 (SFX) [0.03–2.2 s] |
| `gun_sniper` | PSE: Rifle Single Shots 1 (SFX) [0–2.6 s] |
| `gun_shotgun` | PSE: Gun Live Ammunition 5 (SFX) [1.78–3.6 s] |
| `gun_sawnoff` | PSE: 12 Gauge Shotgun 4 (SFX) [0–1.45 s] |
| `gun_autoshot` (x2) | PSE: 12 Gauge Shotgun 301 (SFX) [0–0.9 s]; PSE: 12 Gauge Shotgun 101 (SFX) [0–0.9 s] |
| `gun_lever` | PSE: Machine Gun 1 (SFX) [0–2 s] |
| `gun_revolver` | PSE: Smith Wesson 357 Magnum 11 (SFX) [0–2 s] |
| `gun_pistol` (x2) | PSE: Gun Live Ammunition 101 (SFX) [0–0.6 s]; PSE: Gun 9 Mm Beretta 101 (SFX) [0–0.6 s] |
| `gun_marbles` | PSE: Gun Live Ammunition 3 (SFX) [0–0.9 s] |
| `gun_redline_k0` | PSE: Machine Gun 5 (SFX) [0–0.4 s] |
| `gun_redline_k5` | PSE: Pistol Single Shots 1 (SFX) [0–0.3 s] |
| `gun_redline_k10` | PSE: Colt 22 Revolver 1 (SFX) [0–0.18 s] |
| **Hits and kills** | |
| `hit` | PSE: Shield Impacts 1 (SFX) |
| `headshot` | PSE: Anvil Hits Ringing Metal Clinks Blacksmith 4 (SFX) |
| `headshot_ko` | PSE: Anvil Hits Ringing Metal Clinks Blacksmith 8 (SFX) |
| `headshot_taken` | PSE: Shield Impacts 2 (SFX) |
| `headshot_taken_ko` | PSE: Robot Impact Miscellaneous Metal Clangs Clun (SFX) |
| `hurt` | PSE: Punch Kit Beefy Hit 1 (SFX) [0.01–0.3 s] |
| `kill` | PSE: Synth Sparkle Tone High Pitch Tone Burst Din (SFX) |
| `death` | Freesound: "Low impact.wav" by AudioPapkin (430978) |
| **Melee** | |
| `swing` (x2) | PSE: Swish Med High End Sharp Swords Fast Punches (SFX) [0.08–0.46 s]; PSE: Swish Med High End Sharp Swords Fast Punches (SFX) [0.06–0.46 s] |
| `bonk` | PSE: Sword Impact 102 (SFX) [0–0.45 s] |
| `tink` (x2) | PSE: Anvil Hits Ringing Metal Clinks Blacksmith 1 (SFX) [0–0.25 s]; PSE: Anvil Hits Ringing Metal Clinks Some Muted 3 (SFX) [0–0.25 s] |
| `ting` | PSE: Sword Draw Clang Unsheathing Two Sabers 30 (SFX) |
| `parry` | PSE: Shield Clang As Hit Metal Sword Hubcap 1 (SFX) |
| `parry_perfect` | PSE: Shield Clang As Hit Metal Sword Hubcap 2 (SFX) |
| `ricochet` (x2) | PSE: Ricochet Metal 1 (SFX) [0.16–0.61 s]; PSE: Ricochet Metal 4 (SFX) [0.16–0.61 s] |
| **Handling** | |
| `click` | PSE: Pistol Handling 7 (SFX) [0.01–0.14 s] |
| `empty` | PSE: Pistol Handling 2 (SFX) [0.01–0.14 s] |
| `reload` | PSE: Ammo Magazine 3 (SFX) [0.01–0.35 s] |
| `thwack` | PSE: Metal Hatch 2 (SFX) [0.08–0.43 s] |
| `glug` | PSE: Plastic Water Jug Glugs 4 (SFX) [0–0.5 s] |
| `rev_up` | PSE: Surreal Car Rev 3 (SFX) [0.18–0.88 s] |
| `marble` (x2) | Freesound: "marble drop" by D.S.G. (240313); Freesound: "marble.wav" by jradcoolness (334222) |
| `boing` | Freesound: "marble.wav" by jradcoolness (334222) |
| **Movement** | |
| `step_metal` (x4) | PSE: Footsteps Truck Bed 3 (SFX) [0.01–0.28 s]; PSE: Footsteps Truck Bed 3 (SFX) [0.48–0.78 s]; PSE: Footsteps Truck Bed 3 (SFX) [2.95–3.25 s]; PSE: Footsteps Truck Bed 3 (SFX) [3.81–4.11 s] |
| `jump` (x2) | PSE: Jump Swish 1 (SFX) [0.1–0.4 s]; PSE: Jump Swish 2 (SFX) [0.15–0.45 s] |
| `land` (x2) | PSE: Gym Bag Thudding 5 (SFX) [0.12–0.52 s]; PSE: Body Fall Wood 2 (SFX) [0.07–0.47 s] |
| `step_hard` (x4) | Freesound: "Hiking Boot Footsteps on Stone" by Fission9 (521590) |
| `step_wood` (x4) | Freesound: "Footsteps_Boots_Wood_Mono.wav" by Nox_Sound (533044) |
| `step_soft` (x4) | Freesound: "Hiking Boot Footsteps on Grass" by Fission9 (521587) |
| `slide` | PSE: Baseball Runner Slide On Dirt Into Home Plat (SFX) [1.42–2.22 s] |
| **Rounds, slips, loot** | |
| `loot_tick` | PSE: Switch Click On Or Off Toggle Button 2 (SFX) [0–0.08 s] |
| `loot_win_common` | PSE: Synth Chime Single Synth Tone 2 (SFX) [0–0.9 s] |
| `loot_win_rare` | PSE: Synth Sparkle Tone High Pitch Bell Tone Ding (SFX) [0.1–1.2 s] |
| `loot_win_epic` | PSE: Synth Sparkle Tone High Pitch Bell Tone Ding (SFX) [0.3–2 s] |
| `loot_win_legendary` | PSE: Magic Synth Stinger Glassine Multi Tone Burs (SFX) |
| `whoops` | Freesound: "quick woosh" by florianreichelt (683101) |
| `clatter` | Freesound: "Marbles Rolling.wav" by DANGEROUSmusicKC (648957) |
| `round_start` | Freesound: "Transition Hit SFX -001.wav" by AudioPapkin (648534) |
| `round_end` | Freesound: "Transition (hit and whoosh)" by xkeril (736852) |
| `loot_land` | Freesound: "drop05.wav" by newagesoup (339365) |
| `loot_pop` | Freesound: "Metallic latch release.wav" by Crinkem (481789) |
| **Items** | |
| `boom` | PSE: Dirt Explosion 3 (SFX) [0–2.6 s] |
| `heal` | PSE: Aerosol Spray Can 4 (SFX) [0–0.8 s] |
| `reverse` | PSE: Spaceship Pre Blast Electric Charge Up Glass (SFX) [0.33–1.23 s] |
| `pop` | PSE: Layered Rips High End Short Energy Bursts Sp (SFX) [0.08–0.53 s] |
| `blow` | PSE: Pressure Blast 43 (SFX) [0.03–1.13 s] |
| `squeak` | PSE: Squeeze Toy Squeaky Rubber With Noisemaker H (SFX) [0–0.3 s] |
| `hole` | PSE: Time Warp Searing Build Up Large Suck Rumble (SFX) [0.12–2.75 s] |
| `shutter` | PSE: Camera Shutter 1 (SFX) [0.31–0.61 s] |
| `whirr` | PSE: Polaroid Camera 2 (SFX) [0.05–0.75 s] |
| `photoin` | PSE: Whoosh Back Zoom Swoosh Fast Camera In And O (SFX) [0.1–0.7 s] |
| `photoout` | PSE: Whoosh Back Zoom Swoosh Fast Camera In And O (SFX) [0.58–1.08 s] |
| `framepop` | PSE: Scrapbook Close 3 (SFX) [0–0.3 s] |
| `bloop` | PSE: Bubble Bloop High Pitched Cute 6 (SFX) [0–0.2 s] |
| `plip` | PSE: Pop Airy 9 (SFX) [0–0.1 s] |
| `glorp` | PSE: Tentacle Slime 1 (SFX) [0.05–0.55 s] |
| `bigpop` | PSE: Balloon Pop 1 (SFX) |
| `blub` | PSE: Underwater Bubbles Deeper Med Short Bursts 6 (SFX) [0.04–0.24 s] |
| `quack` | Freesound: "single quack from a duck" by Mikes-MultiMedia (418509) |
| `popper` | Freesound: "partypopper.flac" by Streety (26349) |
| `ropesnap` | PSE: Towel Cracks Low Intensity Whipping Hits 2 (SFX) [0–0.4 s] |

### Checks (16 Nov 2026, 20:21 UTC, place version 438)
- All 105 Sounds load in a Play test; every one of the 77 names played with a real level; the short regions stop where
  they should. Walking 5 s gave 10 footsteps cycling through the stone takes, and a jump played its second take.
- A level sweep (each sound played once, peak `PlaybackLoudness`) found some recordings off target; 31 Volumes were set
  by hand afterwards (`store.json` "vol"): quieter smoke-bomb hiss, duck squeak, hurt thud and parry; louder SMG,
  sniper, shotguns, headshot dings, camera shutter, slide, reload clicks and several item and loot sounds.
- Nobody here can listen: each pick was judged from its title, measured length, onsets and loudness. Stand-ins where
  the libraries had nothing better: the lever-action rifle uses a single rifle shot, the rope snap a towel crack, the
  slide a baseball slide on dirt, the Marble Shotgun a short-barrel 12 gauge. Any one can be swapped in `store.json`.

Freesound credits (all CC0, kept for traceability): `roblox/assets/sounds/freesound-credits.md`.

### Tools
- `tools/roblox/freesound_web.mjs`: search freesound.org for CC0 sounds (no API key) and download previews.
- `tools/roblox/audio_to_wav.py`: decode ogg/mp3 to WAV with Blender's audio module (no ffmpeg here).
- `tools/roblox/sfx_cut.mjs`: list a clip's onsets and loudness; cut one event, fade, normalise.
- `tools/roblox/sfx_sheet.mjs`: waveform + spectrogram sheet to look at clips.
- `roblox/assets/sounds/store.json` + `tools/roblox/store_sounds.mjs`: the picks and the Luau that puts them in Studio.
- To go back: each Sound keeps `SoundIdV2` / `VolumeV2` (take 2, synth) and `SoundIdV1` / `VolumeV1` (take 1).

The distance muffling, random takes, pitch nudge (`Sfx.luau`) and the footsteps script (`Steps.client.luau`) from
take 2 stay as they were.

---

# Take 2 (16 Nov 2026, replaced the same day by recordings): layered synthesis

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
