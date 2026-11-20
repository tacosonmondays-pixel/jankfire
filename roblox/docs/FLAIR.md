# Kill effects, emotes, grapple skins and pets ("flair")

17 Nov 2026. The owner asked: "Can we also have basic kill effects? Reference the rivals ones!! As well as other
games and maybe some emotes??" Built by the flair session (a side session of the main session).

Research: vault `Research\Kill effects and emotes.md` (Rivals finishers and emotes, Valorant, Fortnite, CS2, Apex, CoD),
with reference pictures kept locally in `References\kill-effects-emotes\` (never in git). Inspired by, never copied: no
Rivals finisher, emote, name or menu layout is reproduced.

## What the research settled

| Question | Rivals | Ours |
|---|---|---|
| When does a kill effect play? | every elimination | every kill in a match or the training hall (not the hub) |
| Who sees it? | everyone | everyone (FlairKill to every client) |
| How long? | 2-4 s readable part | 1.5 s at most (the owner's brief), body-sized |
| Equip | one per weapon | one per player: the web game's own rule (`shared/cosmetics.js`: "one per player, not per weapon") |
| Default death | ragdoll | the body falls apart, as before ("Default", the web's "Gibs") |
| Emote key | hold T (D-pad right) | hold T (D-pad right), 8-slot wheel; a phone button |
| Emotes mid-match | yes; third-person camera; enemies behind walls hidden | yes, the same: third-person camera, enemies you couldn't see are hidden from you while you emote |
| Cooldown | none found | 2 s (spam guard) |

Rules kept from the research (section F): no tall light pillars or domes, no floor marks (also the owner's match-floor
rule), effect parts never collide, low flashes, quiet colours.

## Kill effects (`shared/Flair.luau` "kill", drawn by `client/KillFx.luau`)

Since the same afternoon (the owner via the main session) the set is the **web game's own twelve** (`shared/cosmetics.js`
`COSMETICS.kill`: same ids, names, rarities), restyled to the serious look (no gore; no text except Blue Screen's own words), with the five
built from the Rivals research beside them. Free: Gibs, Confetti, Dissolve; the rest roll from the Duffel Bag.

| id | name | rarity | s | what plays |
|---|---|---|---|---|
| none | Gibs | free | - | the body falls apart, as it always has (no blood) |
| confetti | Confetti | free | 1.3 | a white pop, then paper confetti (cream, amber, slate, clay) flutters down |
| dissolve | Dissolve | free | 1.3 | washes pale, comes apart from the feet up into fine motes that drift up |
| grave | Tombstone | common | 1.5 | the body sinks into the floor as a plain stone marker (no words) rises where it stood, then both go |
| cash | Make It Rain | common | 1.4 | the body pops into 22 plain paper notes (no print) that drift down |
| pixel | Missing Texture | rare | 1.2 | flickers, breaks into small near-black and muted-magenta cubes that drift and blink out |
| balloon | Balloons | rare | 1.5 | five plain balloons tie on and the body floats up 6.5 studs, fading |
| shatter | Shatter | rare | 1.0 | glazes like ice for a beat, then breaks into ~28 clear glass wedges with a pack ice burst and frost flakes (KillIceBurst) |
| ember | Ember | rare | 1.4 | chars dark with a glowing orange edge, burns away from the head down into embers and ash |
| chicken | Chickens | epic | 1.5 | a soft pop of feathers; three small chunky chickens scatter and run off |
| bsod | Blue Screen | epic | 1.2 | a flat blue panel (FATAL ERROR, player.exe, a filling bar) replaces the body, then switches off like an old monitor. The only kill effect with words: the owner allowed it (17 Nov); drawn live with TextLabels in the game's font, never an uploaded picture |
| yeet | Yeet | epic | 1.3 | launched straight up, spinning, a dotted streak under it, a glint high above |
| ink | Ink | epic | 1.2 | floods solid black, bursts into blots, flakes and droplets that fall |
| static | Static | epic | 1.0 | flickers and jitters like a lost signal while pack electric bolts crawl over it three times (KillStaticArc), then snaps out to a point in a spark burst (KillStaticPop) |
| ascend | Ascend | legendary | 1.5 | a soft shaft of warm light (top 2.6 studs over the head) gathers; pack rays and a soft core open round the body (KillRays) as it glows, lifts and goes up as motes |
| duck | Big Duck | legendary | 1.5 | a big rubber duck (round pieces, the game's duck yellow) drops on the body, squashes, gulps, shrinks away |
| blastzone | Blast Zone | legendary | 1.0 | a white-hot flash and shock ring; the body is knocked clean away from the killer, spinning, out of sight (a 100+ pack ring to come: KillBlastRing) |

All drawn from the VFX pipeline's approved sprites (glow, sparkle, chips, dust 4x4, lumps 4x4, spark, ring, tracer,
feather) and plain client parts (stone, notes, cubes, balloons, chickens, the duck): no new uploads. Particle `Size` is half the width (VFX-PIPELINE.md).

### The bought VFX packs on kill effects (20 Nov, place v1116)

The owner: "we purchased the vfx lets use them when we can!!" The weakest kill effects (from the 17 Nov photo sheets) were
upgraded first: STATIC, SHATTER and ASCEND. BLAST ZONE is next, with a ring from the 100+ pack once the VFX session has
photographed them. Guard break and Slam stay theirs, for parry and landings: a kill must not look like a parry.
- **Which pack effect goes where** is in the shared table `side-session-notes/.../pack-effects-usage.md`:
  - KillStaticArc: Shock Aura + Blue Lightning
  - KillStaticPop: Eletricity + Golden Eletricity
  - KillIceBurst: Frigid Blast, without its smoke layer
  - KillRays: Treasure
  - All four are from the Combat VFX Asset Pack by coldd Development, credited in `shared/Credits.luau`.
- **Templates:** they sit in `ReplicatedStorage.JankfireVfx` and are played by the VFX session's `client/VfxEmit.luau`.
  `studio-tools/KillVfxImport.luau` (PolishBackup) builds them from the pack effects in the place:
  - It shrinks each emitter to body size. Size, speed and acceleration scale by min(kmax, maxSize ÷ biggest size).
    Life is capped.
  - Continuous emitters get `EmitDuration`, so they play as short bursts.
  - Recolour uses the VFX session's rule: whites stay, other colours turn to the effect's accent with 30% of their
    saturation out, Brightness ≤ 4, LightEmission -1..1.
  - The raw effects come in from the VFX session's offline converter (`to_luau.py`, only the named effects, never the
    Blood folder) and are deleted after the build. The pack's own settings never go in git.
- **KillFx:**
  - `PACK` maps keys to template names. `pack(r, key, cf)` plays one sized to the body. It returns false when it can't
    play: no template, a shop card's ViewportFrame (particles don't draw there), or `KillFxPacks = false` on the
    workspace or on that body's model. In those cases the effect draws its old particles.
  - Static's slice bars give way to the bolts. Shatter's dust gives way to the ice burst, and its wedges go clear Glass.
- **Photos:**
  - VfxEmit parks (and clears) an effect when its life is up, on its own clock, even while `FlairTimeScale` is 0.
  - For a frozen photo, add a hidden emitter (`EmitDelay` 25, `EmitCount` 1, transparent) to each template and each
    pooled clone in that Play.
  - Before/after rows: six copies, the left three with `KillFxPacks = false`.
- **Checked** (solo Play, v1116 and v1119; photo `flair/kill-effects-packs-before-after.jpg`):
  - All four templates play on copies of the owner's avatar and stay within about 4 studs. They are done by 1.4 s.
  - No script errors.
  - The first ice burst carried the pack's smoke (a 20-stud white fog), so the smoke layer was dropped.
  - Shatter's clear glass wedges read dark against a dark wall: they show what's behind them.

How it works:
- **Server** (`server/FlairServer.server.luau`, hooked on `Fight.onKill`): the killer must be a player, not the victim;
  not a void fall or the Shredder's own kill; the killer's Zone not "hub". The killer's WORN effect (owned, else
  Default) is the one. In the same step as the death (before its joints break and the parts fly) the body is frozen:
  every part anchored, CanCollide / CanQuery / CanTouch off; the model gets attributes `FlairFrozen`, `KillFx`. Then
  `FlairKill` { m, fx, k } goes to every client. The server's kill credit is the only source: a client can't ask for an
  effect on anyone.
- **Clients** (`KillFx.play(model, id)`): the body's parts fade with `LocalTransparencyModifier` (nothing replicates), one
  Highlight tints them, 1-3 emitters on client-only parts do the rest; at the end the body is hidden for good (and
  anything added to it later) until the respawn replaces the model. A body more than 320 studs from the camera just
  hides. Your own body is left to the camera scripts (only the particles show).
- **Cost** (per effect): one Highlight (client limit 255), 1-3 ParticleEmitters, up to ~130 particles over its life;
  Shatter adds ~28 client wedges moved by script for 1 s; Static 5 thin bars. Everything is destroyed 1.2 s after the
  end. Measured: see "Test results".
- **Photos**: the workspace attribute `FlairTimeScale` (0..1, set on a client) slows or freezes every running effect,
  particles included (like the VFX pipeline's `FxTimeScale`).

## Emotes (`shared/Flair.luau` "emote", played by `client/FlairClient.client.luau`)

**Since 17 Nov (place v670) the emotes are Roblox's own.** The owner: our generated ones "looked really really bad", and
"are there free roblox emotes we can download? I have purchased some with robux".

The free set, every one free for everybody and never sold (`Flair.luau` EMOTES, the one table):

| id | name | s | loops | animation | from |
|---|---|---|---|---|---|
| wave | Wave | 1.75 | no | 507770239 | Roblox's default emote |
| hello | Hello | 1.77 | no | 10714359093 | catalog emote 3576686446 |
| salute | Salute | 3.70 | no | 10714389988 | catalog emote 3360689775 |
| point | Point | 2.30 | no | 10714395441 | catalog emote 3576823880 |
| shrug | Shrug | 2.03 | no | 10714374484 | catalog emote 3576968026 |
| cheer | Cheer | 2.50 | no | 507770677 | Roblox's default emote |
| laugh | Laugh | 3.29 | no | 507770818 | Roblox's default emote |
| stadium | Stadium | 3.63 | yes | 10714356920 | catalog emote 3360686498 |
| tilt | Tilt | 4.80 | yes | 10714338461 | catalog emote 3360692915 |
| dance | Dance | 1.08 | yes | 507771019 | Roblox's default emote |

- **How the animations were found.** Each catalog emote is a model holding one full-body Animation (all 16 joints; Roblox names them "<X> Face" since the 2022 face update). It's read with `InsertService:LoadAsset`, and lengths and looping come from `KeyframeSequenceProvider`.
- **Why our own system plays them** (not `Humanoid:PlayEmote`): they're Roblox's, so they play in any game for any account, and our blend, camera, holster, cooldown and match rules all apply.
- **Wheels saved before (save v1)** get these in their empty slots on load. The default wheel is wave, hello, salute, point, shrug, cheer, laugh, dance.
- **Our generated clips are gone:** Slow Clap and the retakes are out of the catalogue.

**Your own Roblox emotes** (the wheel's ROBLOX pages):
- `StarterPlayer.UserEmotesEnabled` is on, so a player's bought emotes are in their character's HumanoidDescription.
- FlairServer reads `GetEmotes` once the look has loaded: the ones equipped on Roblox first, then the rest by name, up to 96. It publishes them as the `RbxEmotes` attribute (JSON `[{n, a}]`).
- The wheel shows them 8 to a page, behind the JANKFIRE / ROBLOX tabs over the ring. Clicking ROBLOX again goes to its next page; the mouse wheel goes through every page. Each slot's picture is Roblox's catalog thumbnail.
- Playing one (`emote` with id `rbx:<name>`): the server checks it's on your avatar and loads the catalog emote's animation the first time anyone plays it, then keeps it. Creators' own emotes load too. It sends the id back, and the client plays it on our track, with its length and looping read off the clip.
- Roblox's own emote menu is turned off (`SetCoreGuiEnabled(EmotesMenu, false)`), so the T wheel is the only one.
- The owner's avatar has 98 emotes, none equipped on Roblox.

Photos: `docs/flair/roblox-emotes-sheet.jpg`.

The generated set, for the record (all removed):

**Removed 17 Nov** (the owner, in a Play test: "remove groove, fist bump and bow they dont work"):
- Fist Pump (105471344218974), Bow (87535060714783) and Groove (115189819491542) are out of the catalogue.
- That takes them out of the wheel, the equip screen, the shop and the Duffel Bag, which all read `Flair`.
- When a save loads, FlairServer empties any wheel slot holding an emote that's gone. It also resets a kill effect or grapple that's gone.
- What the server saw in that test: the owner owned only the free Wave and Salute, and those were the only two on their wheel. The other emotes, Slow Clap included, show LOCKED for them, so they can only be previewed.
- All six clips loaded for the owner's account (`ContentProvider:PreloadAsync`: Success), and neither log had a flair error.
- Play check (place v639): Wave, Salute and Slow Clap each blend in by 0.47 s, fade out from 2.65 s to their last frame, and end. The server answers Groove with "no such emote".

**The gun vanishing after the loadout's KILL EFFECT · EMOTES button** (the owner, 17 Nov: "when you go to loadout and
kill effects then leave it it renders your gun away for a second"):
- Cause: the button closes the loadout, then opens this screen 0.05 s later, while the loadout's camera is still out at its showcase spot. This screen saved that spot as the camera to return to.
- On closing, the camera flew back out there. First person hides the gun whenever the camera is more than 4.5 studs from the body, so the gun stayed hidden until Roblox's camera took over again.
- The server's re-arm on closing the loadout isn't it: with no weapon change it answers "same" and rebuilds nothing.
- Fix (v639): the button passes the loadout's saved view (your own, from before the loadout opened) and `FlairUI.open(tab, home)` returns to it. Opened while any other screen's camera is out, it returns to your own eyes.
- Play check (v639, no edits): the button sits off the top of Studio's short viewport, so the same timing was made by hand. The loadout was opened in the training hall and closed with L, and the equip screen opened 0.05 s later, while the loadout's camera was still out (CameraType Scriptable at that moment: the bug's condition). That's the no-`home` fallback path; the button's path differs only by passing the loadout's saved view. Logged every frame for each tab:
  - kill: gun back 0.02 s after closing, camera at most 2.7 studs from the body, no rebuild;
  - emote: 0.03 s, 2.4 studs, no rebuild;
  - grapple: 0.03 s, 2.4 studs, no rebuild.

**KillFx for the shop's cards** (v639): `K.play(m, id, { parent = WorldModel, camera = Camera })` puts the run's pieces under `parent` and faces `camera`. `K.VIEWPORT = true` says the options are there.

The clips come from Studio's prompt-to-animation tool (`generate_animation`, the owner's rule).

### Retakes (17 Nov, the owner: "the animations seem really stiff..")

Five of the six were remade with prompts that ask for loose, relaxed motion with the torso, head and legs moving along,
facing forward with the feet planted. The owner's rule for anything generated is 4 at a time, so each got 4 takes (made
in parallel, one rig each). The best take was kept, judged on a 6-frame pose strip (`docs/flair/emote-retakes-sheet.jpg`)
and a motion meter. The meter samples each clip at 30 Hz on a rig:
- **holds**: the share of time the body moves at under 35% of its median speed (frozen key poses);
- **spike**: the 95th-percentile speed over the median (snapping from pose to pose);
- **sec**: the share of all turning outside the arms (secondary motion);
- **turn**: how far the body's root swings from where it started (two wave takes and the old groove turned sideways);
- **home**: how far the last frame is from the first (does it settle; for a loop, the seam).

| emote | old clip | kept take | why |
|---|---|---|---|
| wave | holds 24%, spike 3.3, sec 19%, turn 8° | holds 4%, spike 2.2, sec 21%, turn 19° | the only take that didn't turn sideways or end with the arm up |
| salute | holds 25%, spike 2.2, sec 31%, home 141 | holds 21%, spike 1.9, sec 29%, home 116 | smoothest, settles closest to where it began |
| clap | holds 2%, spike 2.3, sec 12%, home 176 | holds 1%, spike 2.0, sec 15%, home 156 | best on every count |
| fist pump | holds 10%, spike 2.2, sec 27%, 2.47 s | holds 21%, spike 1.7, sec 34%, 2.97 s | smoothest; the arm comes down and settles |
| groove | holds 34%, turn 82°, seam 694 | holds 19%, sec 44%, turn 27°, seam 0 | faces forward and loops without a jump |

Bow was kept from the first set. In game every emote now fades in over 0.3 s and out over 0.35 s; a one-shot starts its
fade-out 0.35 s before its last frame, so it settles into the idle instead of snapping. Switching straight from one
emote to another cross-fades too.

Play check (place v614): the new wave's weight, logged every 0.1 s, rose 0 to 1 over 0.3 s and fell back to 0 over 0.35 s
with no jump. The same log showed that a clip's first play waits about 0.6 s for the asset while the timer counts, which
cut the end off. One-shots now end on the track's own time (`TimePosition >= len - 0.35`), in the game and on the equip
screen's preview. The equip screen's emote and kill cards also run the shop session's moving previews (`FlairAnim`).
Re-checked in Play the same day (no change, no save). A first play again waited about 0.2 s for the asset. The fade-out
began at 2.62 s and ended on the clip's last frame (2.97 s). The groove looped twice in 9 s at full weight and stayed on
until stopped. On the equip screen, all six emote cards moved, each showing a small copy of the avatar doing its emote.

Retake prompts (3 s; groove 4 s):
- wave: "A person standing relaxed with loose arms casually raises the right hand and waves it side to side in a friendly, easy way; the shoulders, torso and head sway gently with each wave and the weight shifts slightly between the feet, then the arm drops back down naturally with a little follow-through into a relaxed standing idle."
- salute: "A crisp salute: a person standing relaxed, facing forward with the feet planted, draws up straight and smoothly brings the right hand up to the brow, holds it while breathing and settling slightly, then lowers the arm with an easy follow-through and relaxes back into a loose standing idle with the shoulders dropping."
- clap: "A slow clap: a person standing relaxed, facing forward with the feet planted and loose arms, claps slowly and steadily four times in front of the chest; the shoulders, elbows and upper body move naturally with each clap and the head nods a little to the rhythm, then the hands drop easily back down into a relaxed standing idle."
- fist pump: "A fist pump: a person standing relaxed, facing forward with the feet planted, pumps the right fist up into the air with energy twice; the torso and hips follow each pump, the weight rocks back slightly and the head tilts up, then the arm comes down and shakes out loosely as the body settles into a relaxed standing idle."
- groove: "A relaxed groove: a person dances a smooth groove in place facing forward, bouncing lightly on the knees to a steady beat, hips swaying side to side and shoulders rolling, arms loose and swinging naturally with the body, a continuous flowing motion with no stiff poses, ending in the same pose it started in so it loops seamlessly."

Lessons: "facing forward with the feet planted" matters (without it 2 of 4 wave takes swung the body sideways). Eight
calls at once took 6 minutes, four took 3; most return their id, the ones that time out still leave their clip. The
takes are in `ServerStorage.RBX_ASSISTANT_ANIMGEN` as `w2_*`, `s2_*`, `c2_*`, `v2_*`, `g2_*`.

### First set (one or two tries each, judged from pose strips). Prompts (all with `duration`):
- wave (3 s): "A person stands relaxed, raises the right hand above the shoulder and waves it side to side three times, then lowers the arm back down to a relaxed standing pose."
- salute (3 s): "A person stands at attention, brings the right hand up to the forehead in a crisp military salute, holds it still for one second, then lowers the hand back to a relaxed standing pose."
- clap (3 s): "A person stands relaxed and claps both hands together slowly four times in front of the chest, then lowers the hands to a relaxed standing pose."
- groove (4 s): "A person dances a relaxed groove in place, stepping side to side to the beat, bobbing the head and rolling the shoulders with the arms swinging loosely, and keeps the same groove going."
- victory (2.5 s): "A person stands relaxed, then punches the right fist straight up into the air in celebration twice, then lowers the arm to a relaxed standing pose."
- bow (3 s): "A person stands upright, places the right hand flat on the chest and bows forward from the waist, holds the bow for one second, then stands back up to a relaxed standing pose."
- A shrug (2.5 s) was made and dropped (it barely read). Its clip and the rest are in `ServerStorage.RBX_ASSISTANT_ANIMGEN` (`flair_*`).

The tool's lessons (17 Nov): `duration` is honoured now (2.47 / 2.97 / 3.97 s, 30 keys a second), unlike the 14 Nov
trial's fixed 5.97 s. Parallel calls time out at the MCP but still make the clip (no published id then): export the
KeyframeSequence (`SerializationService` + Base64, read back in 96,000-character slices) and upload it as an
`Animation` through Open Cloud (`/assets/v1/assets`, `.rbxm`). One call at a time returns the id. It needs a rig in the
Workspace (`instance_path` can't point into ServerStorage).

How it works:
- **The wheel**: hold T (or D-pad right), point at a slot, let go (or click). A quick tap leaves it up for a click; Esc
  closes. On a phone the EMOTE button (bottom left, over SHOP) opens it; a tap plays. While it's up `LoadoutOpen` is
  raised (hands, weapons and other screens hold still; the mouse is free).
- **Playing**: the client asks the server ("emote", id): owned, on your wheel, alive, 2 s since the last. The server
  sets the player attribute `Emote` and puts the weapon away (the `HeldWeapon` model and any Tool) for as long as it
  plays; the client plays the clip on its own Animator (Action4; it replicates to everyone) and swings the camera out
  to 9 studs behind you (the mouse turns it round you, walls pull it in). Moving, jumping, a weapon or item key, a
  click, T again, a death, a respawn or a shot (server) ends it; the weapon comes back. A loop (Groove) runs until you
  move (the server ends it after 30 s).
- **In a match**: while you emote, other players you couldn't see from your own eyes (rays against `workspace.Map`,
  three heights) are hidden from you, refreshed every 0.15 s; teammates stay.

## Trend emotes (19 Nov 2026)

The owner: "are there free emotes we can take based of current dances memes or trends?" Real ones only: the generated
emotes were "really really bad".
- **Source 1: the Marketplace's free emotes** (price 0). The public catalog search for Category 12 / Subcategory 39 with
  MaxPrice 0 gives 43, sorted by favourites.
  - Seven are Roblox's own. Six were already ours; Applaud is new.
  - The rest are creator-made free limiteds, mostly given away in other games.
  - Every pick was checked in Studio: it loads with `InsertService:LoadAsset`, holds exactly one Animation, is R15
    (KeyframeSequence poses on UpperTorso/LowerTorso), loops, and has no Sound.
- **Left out:**
  - named routines: a song's, a creator's or another game's dance (Floss, Griddy, Macarena, the battle-royale default
    dance, Electro Shuffle, the boat-race "aura" dance);
  - brands and other IP: a cosmetics brand's emote, a fashion brand's, a snack group's bow, a comic's execution move,
    another shooter's promo sprint;
  - one emote its maker says was generated.
- **Names** are plain move names, never the item's, a song's or a creator's.
- **The 15**, newest first, all free, with a NEW dot (Flair EMOTES' 8th column) until the equip screen has shown them
  (FlairServer `freeSeen`, op `freeseen`): Worm, Fancy Feet, Dab, Slide Step, Vibe, Flow, Sway, Two Step, Flap,
  Hype Clap, Float, Flex, Kicking Feet, Shy Wave, Applaud. Their catalog ids are in `Flair.luau`.
- **R15 only,** as every catalog emote: on an R6 body the emote doesn't play.
- **BIRDBRAIN** (the owner asked by name): no free version exists. About ten creator versions, all 55-105 Robux;
  nothing bought, ripped or hand-made.
- **Source 2: Mixamo dance mocap** (20 Nov), from the owner's account: real mocap, royalty-free for games.
  - The scythe session downloaded 10 clips to the vault (`Assets\mixamo-20nov-dance`, never git): FBX Binary, Without
    Skin, 30 fps.
  - Clips named after a famous song were skipped (The Twist, Charleston).
  - `tools/blender/mixamo_r15.py` made each an R15 KeyframeSequence (looped, drift taken out, priority Action). Each was
    uploaded as the owner's Animation.
  - **The ten, listed first and NEW:** Hip Hop, Robot, Shuffle, Breakdance, House, Swing, Tutting, Body Wave, Silly Dance,
    Spin (3.8 to 26.2 s loops). Their ids are in `Flair.luau`.
  - They're R15 only, like the converter's rig. R6 emotes would need an R6 mode in the converter.
- **The owner's packs (20 Nov),** vetted offline (`side-session-notes/.../packs-20nov-vetting.md`):
  - three are copies of other games' emotes and song routines: OUT;
  - the bought Soul Sword Combat Pack is R6 combat, not emotes. It waits on its licence.
- Preview: `flair/trend-emotes-sheet.jpg`.

## Emote music (19 Nov 2026)

The owner: "si there a copyright free instriumental to go with it?" An instrumental of a trend song is still that song,
and covers or "type beats" of its melody are out. So each dance emote gets one track from Roblox's own licensed library.
- **Source:** APM Music production music (the library's creator APMOfficial), cleared for use in Roblox experiences. Found
  with `AssetService:SearchAudio` (AudioSubType Music) and kept only where the Creator is APMOfficial: DistroKid artists'
  songs mostly have vocals, and user uploads aren't cleared.
- **Picked as instrumentals** by genre and title: beats, grooves and funk, no singer's songs. Not ear-checked, since
  nobody here can listen.
- **Timing:** each starts just before its first strong beat (AudioAnalyzer onsets, measured silently, all tracks at once)
  and plays a 60 s stretch. An emote ends by 30 s, so its loop seam is never reached.
- **The picks** (`Flair.MUSIC`):
  - Worm: Check It Out (Nicolas Baudino)
  - Fancy Feet: Playful Electro Funk (AXS)
  - Dab: Music Report (Mr De La Main). It replaced "No Smoking" on 20 Nov: no tobacco in a title someone might read.
  - Slide Step: Soul Dancefloor (Mr De La Main)
  - Vibe: Lo-fi Chill A (Hip Hop Shop)
  - Flow: Moving Round The Block (Afro Dizzy)
  - Sway: Beach Cushions (Afro Dizzy)
  - Two Step: Discoball (a) (KPM)
  - Flap: Hot Potato 60 (John Stuart)
  - Kicking Feet: Jolly Pranks (Yannick Kalfayan)
  - Float: Chill Groove to Gamma (a) (Lee Briskett)
  - Hype Clap: Wake Up Beat (Bastien Thomas Deshayes)
  - Dance: Hype (Samson Robin Penot)
  - The Mixamo ten:
    - Hip Hop: Play Hard - Underscore (Ty Noam Frankel)
    - Robot: Robot Tiger (Joel Vandroogenbroeck)
    - Shuffle: No Doubt D (Mark Nolan)
    - Breakdance: Breakbeat Mansion (Mikel Ross Giffin)
    - House: Cubico B (Sonoton Music)
    - Swing: Swing Fever (Laurent Bernadoy)
    - Tutting: Digital Takeover (Kosinus)
    - Body Wave: Urban Sweet B (Machan Sasaki Taylor)
    - Silly Dance: Funk Jam - Underscore (Steve Michael Lucas)
    - Spin: Soul Groove (A) (Andrew Howard Pask)
  - Tracks with a quiet intro and no beat in their first 9 s were passed over (Tech Syndrome, The Machine).
- **Playing** (`client/EmoteMusic.client.luau`, each screen its own):
  - A Sound in the dancer's HumanoidRootPart, InverseTapered, full within 8 studs, gone by 40, low (0.35).
  - It starts with the emote (the player attribute `Emote`) and fades out in 0.25 s when it ends.
  - Never while a match round is live (Zone `match` with `RoundEnds` set): the hub, lobbies, between rounds and after
    the match only.
- **Settings** (AUDIO tab):
  - MUSIC VOLUME (`vol.music`, a `Music` group under the master);
  - OTHERS' EMOTE MUSIC (`snd.emoteMusic`). Your own always plays; the slider can still mute it.

## Grapple skins

The web game's eight (`COSMETICS.grapple`): Rope (free), Chain, Candy Cane (common), Plunger, Jungle Vine (rare), Laser,
Sticky Hand (epic), Rainbow (legendary). One per player, everyone sees it. Worn grapple: `JankfireFlair_v1` (`grapple`),
player attribute `Grapple`; the GRAPPLE tab of the equip screen. The look (Blender heads after the web game's own
`make_grapples.py`, rope textures, `shared/GrappleLook.luau`, `client/GrappleSkins.client.luau`) is in GRAPPLES.md.
A skin only rolls or sells once its head is in `ReplicatedStorage.JankfireGrapples` (`Flair.grappleReady`).

## Pets (18 Nov 2026)

The owner: "Secret pets: when you find jank npc you'll have a mini scaled down version that follows you. Another one
could be the train, a slug made of hardware with his mask, it crawls using his hands from in game. Those like fleshy
meat dogs?" Main's spec: one pet worn at a time, earned only by finding secrets, following you everywhere, cheap, and
everyone sees everyone's.

**Shipped: the Mini Mannequin only** (18 Nov, the owner: "Maybe just jank player pet for now"). The slug and the dog are
parked, each behind its own switch (the last column of `Flair.luau` PETS). A parked pet is not in the PETS tab, its secret
doesn't run (no train counting, no kennel in the Gut), nothing can grant or wear it, and nobody draws it. Their models, the
skinned take 2 and the code all stay; turning a switch on brings that pet back (then `PetImport.build({ "dog" })` makes its
template).

**The three** (headless Blender; sheets `flair/pets-models-sheet.jpg` (take 1) and `flair/pets-before-after.jpg` (take 2)):
- **Mini Mannequin** (`mannequin`, `tools/roblox/pets_models.py`): the hub egg's mannequin, from its own dump of the web game's player, at 0.95 studs per web
  metre (1.9 studs, knee high), with the pink outline rim. Two stiff pieces (body, outline) that waddle together, rocking from
  foot to foot like a wind-up toy. Upload 93735950095362.
- **Train Slug** (`slug`, `tools/roblox/pets_skinned.py`): one tapering steel body with plate seams and rivets on its skin, a
  stack and a valve wheel. The Gut train's ☺ enamel mask sits in a socket carved into its own collar. Two cable arms come
  out of steel shoulders through an elbow and a wrist (the boss's blue knots) to mitten hands it drags itself along on.
  3.1 long. Upload 70466317838874.
- **Meat Dog** (`dog`, `pets_skinned.py`): one pink body; the two sausage links are a soft waist with a cream twine groove.
  Hips and shoulders melt into stubby legs with knees and paws; the neck flows into the head; floppy ears grow from the head
  and the tail from the rump. Button eyes, a raised teal collar band with a tag. 2.6 long. Flat clean pinks: nothing raw, no
  organs, bones or blood (the account has one warning). Upload 131881237894353.
- **Take 2 (18 Nov):** the owner on the first sheet: "The dog looks very AI-ish, which I think is characterized by the lack
  of joins and the segmented body!! Same with the train boss pet!!" Take 1 was primitives butted together (uploads
  77552236809847 and 75123181576256, never put in the place). Take 2 builds each as a metaball field: soft lumps that melt into
  one another, so every join has its own fillet. It is then meshed, smoothed, reduced (dog 8.1k tris, slug 12.6k), coloured
  per vertex (smooth edges between colours) and skinned to a few bones (dog: body, head, tail, four legs; slug: five
  along the body, an upper arm and a forearm each side). One MeshPart with its Bones; Roblox's import puts it in the file's
  own frame (bones exactly where `pets2_layout.json` says).
- The mannequin's pieces carry their joints (`pets_layout.json`, written into `PolishBackup.PetImport` by
  `tools/roblox/pets_import_luau.py`). Colours are baked vertex colours (`rbxglb`), so Color stays white.
- **The find's recording** (`PetImport.SOUNDS`, a `Found` Sound in each template, played for the finder alone):
  - mannequin: the hub egg's toy-top run;
  - slug: four quick clanks from Pro Sound Effects "Metal Pole Impact With Wrench Bat 2" (6.8 to 7.95 s, measured);
  - dog: Freesound 468443 "Squeaky Toy #1" by Breviceps (CC0), upload 75582875806945.

**Finding them** (`server/PetSecrets.server.luau`; nothing on screen hints at any of them):
- **Mannequin:** find the hub egg. Anyone who owns its OG title has the pet, checked when the loot save loads and on
  `Loot.changed`, so players who found it before pets existed get theirs too. `HubEgg.server` is unchanged (agreed with the
  training session).
- **Slug:** be on the Gut's platform when the train passes behind the glass, three times, across any matches. The count is
  saved (`seen.train`). `GutTrain.server`'s `TrainAt` says when a run reaches the station; the server checks who is on that
  arena's platform then.
- **Dog:** a little kennel (upload 114456936297774: cream walls, a dusty rose roof, a dark doorway, a paw print on a blank
  plaque, a teal bowl) in the subway's south-west corner, against the end wall, beside the glass, behind the last column.
  Walk up to its door. `PetSecrets` places one in every Gut arena at run time (`workspace.Map.Gut` and its copies), from
  `ServerStorage.JankfirePetKit.Kennel`. An unseen box round its walls stops you and shots like any wall.
- A find shows "NEW PET · <NAME>" (the announcer line) and plays a short recording for the finder alone. Your first pet is
  worn at once.

**Saving:** pets are not in `Flair.TYPES`, so the loot and shop hooks never see them: they're never sold or rolled. Found
pets are kept in FlairServer's own save (`pets`, `pet` worn, `seen` counts). The player attribute `Pet` holds the worn pet.
The remote `Flair` takes `("pet", id)` ("" for none), and `state` returns `pets` and `pet`. Server scripts use
`FlairServer.PetOps` (BindableFunction): `grant` / `owns` / `bump` / `count` / `forget` (Studio only).

**Following** (`client/Pets.client.luau` + `client/PetRig.luau`, nothing on the server):
- Each screen draws every player's pet, one anchored model per pet in `workspace.ClientPets`, moved with one `BulkMoveTo` a
  frame. A pet more than 165 studs from your camera is parked out of the world and not moved at all; it snaps back to its
  owner when you come near.
- It walks where its owner walked: a trail of the owner's footing (points 0.5 studs apart, only while they stand on
  something), heading for the point a few studs back along it, off to one side when there's room. So it goes round corners
  and up the same stairs, not through a wall the owner went round. It catches up faster the further behind it is and turns
  slowly to its owner when they stop.
- **The floor** (18 Nov, v922; the owner: "also the pet clips through too"):
  - Every frame, two rays from the pet's OWN height (2.4 over its feet; they ignore bodies, pets and things you walk through):
    one under it, one a step ahead. Take 1 looked only now and then, from the owner's height: under a balcony that found the
    floor above and lifted the pet through it, and on stairs it eased up late into the steps.
  - Its feet never go below the floor under it. It rises as a step comes (the look-ahead) and eases down steps and slopes.
  - Over a gap it keeps its height for 0.6 s, then takes its owner's trail's.
  - A wall in its way stops it and it slides along it.
- It jumps back to its owner in four cases:
  - after a teleport (the body moved 25+ studs in a frame);
  - past 42 studs behind;
  - 12+ studs above or below for 1.2 s (pads, lifts);
  - held by a wall (barely moving, 3+ studs behind) for a second.
- No collisions, queries or touches: it can't be shot, stood on or block anything.
- **First person (18 Nov, v961):** you see your own pet as in third person. The owner said "when in first person your pet
  doesn't always show up": take 1 hid your own pet whenever it was in front of you in first person, as the first spec asked.
  Now only a pet right at the camera (within 1.3 studs) hides, and its visibility is written again every 0.5 s, so no other
  script can leave it transparent.
- Gaits are sums of sines (`client/PetRig.luau`): the mannequin's pieces turn about its feet (the waddle). The dog's and
  the slug's bones get a `Transform` each frame, written in the pet's own frame and carried into the bone's (rest^-1 · move ·
  rest). The slug crawls: its body bunches in a wave, and each arm lifts at the shoulder and the elbow in turn. The dog trots:
  diagonal legs, a bob, a nod, and a tail that always wags. Standing, each idles.

**The picker:** the equip screen's PETS tab. NO PET comes first, then the three. A found pet shows in its own colours with
its name; one you haven't found is a black silhouette named "???", with no hint. The preview walks the pet in a ring round
the copy of you.

**Tests (Studio):**
- `ServerStorage.PetTest`, for the first player:
  - `state`
  - `train`: a train passes now in every Gut arena, by the same path as a real run
  - `platform` / `kennel`: stand on Map.Gut's platform, or at the kennel's door
  - `grant` id / `forget` id|all
- Workspace attribute `PetFreeze` holds every pose (for photos).
- A Model tagged `PetStandIn` with an attribute `Pet` walks a pet like a player.
- `FlairTest = "ui:pet"` opens the tab.

**Checked in Play** (place v833, then v843 with the slug and the dog parked):
- `HubEggTest "find"` gave the OG title, and the mini mannequin with it, worn at once.
- It followed 2.6 to 3.3 studs behind and 1.8 to 2.8 to the side, in the hub.
- The tab shows only NO PET and MINI MANNEQUIN (EQUIPPED). The preview draws it in colour (v843 fixed it starting as a silhouette before the found list came in).
- With the slug and the dog parked: granting them answers "no such pet", and no kennel is placed in the Gut.
- Not tested live: the train-pass and kennel finds, which need a Gut match. They're parked now anyway.
- Photos: `flair/pets-mannequin-hub.jpg`, `flair/pets-picker.jpg`.
- **The floor fix (v922):** the owner walked up the hub's two ring steps (gym floor 239.98, steps 240.70 and 241.40) and back
  down; then on the training bay's step, and the lounge floor.
  - Measured every frame against the floor under the pet: worst sink 0.000 on every route.
  - Up to 1.35 over the floor for a frame or two, gliding down off the top step.
  - Inside a part for 1 frame of 71.
  - Training itself couldn't be walked: the hall is sealed against a teleported test player, who lands back in the hub. The
    pet then sat on the lounge floor at its exact height (239.95).
  - Photo: `flair/pets-floor-steps.jpg`.
- **First person (v961):** the pet was visible (LocalTransparencyModifier 0, drawn on screen when looked at) in each case:
  - in first person, facing it and looking down at it;
  - after V to third person and V back;
  - after a respawn;
  - in a ghost match, and back in the hub when it ended (3.4 studs away each time).
  - The test camera was tipped down with a render step after the game's camera, because simulated mouse moves don't turn
    the locked first-person view.
  - Photo: `flair/pets-first-person.jpg`.

## Settings hooks (the settings page, P)

Three rows of the settings session's page reach in here, each looked up once (FindFirstChild + pcall) with today's
behaviour as the fallback: GRAPHICS "OTHERS' KILL EFFECTS" off = someone else's kills only hide the body
(`KillFx.play(..., { quiet = true })`); `gfx.particles` (0.25-1) scales every burst and stream; the emote key is
`Binds.is("emote", io)` (T and D-pad right until rebound).

## Equip screen (`client/FlairUI.luau`)

The loadout screen has a KILL EFFECT · EMOTES button left of DONE; it closes the loadout and opens this screen (not in
a match). Four tabs: KILL EFFECT, EMOTES, GRAPPLE, PETS (see Pets). A grid of cards (EQUIP), or the wheel's 8 slots over the emotes (pick
a slot, pick an emote, PUT IN SLOT n; EMPTY SLOT). Locked items show a padlock. On the right a client-only copy of your
own avatar stands in the world in front of you and plays what you point at, on a loop (a ViewportFrame can't draw
particles). DONE or Esc closes.

Two layouts (17 Nov, after the mobile session measured the desktop one at ~36 % on a phone, DONE ~18 pt):
- **Desktop:** a 1920 x 1080 stage scaled to fit; the wheel's slots as a ring.
- **Phones and tablets** (`Keys.isTouch`, the touch-controls session's; else touch and no keyboard): a compact 960 x 440
  stage inside the device's safe area (`ScreenInsets`), three cards across, the wheel's slots as a row of squares, every
  tap target 52 design px or more. Measured in an 844 x 390 box: tabs and DONE 46 pt, EQUIP 47, slots 51, cards
  144 x 149; in 1133 x 744 everything x1.18 (DONE 61 pt). Photos: `flair/equip-screen-phone-sheet.jpg`.
- Test hook: the player attribute `FlairTest = "fake:844x390"` puts the compact layout in a box that size; `"real"` undoes it.

Input and the phone (the touch-controls session): every key arrives through its `Keys` (`Keys.began` / `Keys.ended`,
real input plus the phone's buttons as plain tables with `Touch = true`); its EMOTE button opens the touch wheel; FIRE,
AIM, JUMP, HOOK and the rest stop an emote as their keys do. My own phone EMOTE button only shows when its phone layout
(`TouchOn`) isn't on. Trap met: reading `.Touch` on a real InputObject throws, so it checks `typeof(io) == "table"` first.

## Owning and saving

- **Owned**: the loot save's (`Loot.owns(p, "kill" | "emote" | "grapple", id)`, bare ids like card looks). Free: kill
  none / confetti / dissolve; emote wave / salute; grapple rope. The rest roll from the Duffel Bag and sell in the shop (the loot and
  shop sessions wire `Shared.Flair` into LootTable and Shop the way they read CardStyles: `TYPES`, `info`, `ORDER`,
  `CONTAINER = "bag"`, `forSale`, `picture`).
- **Worn**: FlairServer's own session-locked store `JankfireFlair_v1` (Profiles.luau): `{ v = 1, kill, emotes = { 8 } }`.
  Nothing else's save is touched. A saved pick you don't own stays saved but isn't worn.
- Player attributes: `KillFx` (worn), `Emotes` ("wave,salute,,,,,,"), `Emote` (playing now), `FlairSave`.
- Remotes: `JankfireRemotes.Flair` (RemoteFunction: state / kill / grapple / slot / emote / stop; every request pays
  the rate budget first, "state" too: the anti-cheat audit) and `FlairKill` (RemoteEvent),
  made by FlairServer when missing (also in `default.project.json`).

## Test hooks

- Server, Studio only: `ServerStorage.JankFlairTest:Invoke(op, ...)`: `("fx", model, id)` an effect on any model as a
  kill would; `("kill", player, n | "Stand")` you kill a training dummy through `Fight.hurt`; `("unlock", player, on)`
  wear anything this session (nothing saved); `("state", player)`.
- Client: the player attribute `FlairTest` = `wheel` | `wheel:touch` | `hover:<slot>` | `close` | `pick:<slot>` |
  `emote:<id>` | `stop` | `ui` | `ui:emote` | `uiclose` | `preview:<id>`.
- Photos: a row of copies of your avatar with the effect started 0.2-0.3 s apart, then `FlairTimeScale = 0` on the
  client: one capture shows five stages.

## Test results (17 Nov 2026, Studio Play tests; saved in place v521 and v526)

Photos: `roblox/docs/flair/kill-effects-sheet.jpg` (all six, five stages each), `emotes-wheel-sheet.jpg` (the wheel,
an emote, a real dummy kill), `emote-clips-sheet.jpg` (the clips as pose strips), `equip-screen-sheet.jpg`.

- **Every effect plays in Play** on copies of the owner's avatar in the training hall (rows of five started 0.2-0.33 s
  apart, frozen with `FlairTimeScale`). No script errors.
- **A real kill**: the test player (wearing Shatter, then Ember) killed a training Stand through `Fight.hurt`. The
  server froze the body (`FlairFrozen`, `KillFx` on the model, root anchored), every client got `FlairKill`, the body
  broke into ice shards. Found and fixed: the dummy's katana showed again after the body went (the third-person script
  un-hides a dead fighter's gun): every part's hidden value is now held until the body is gone.
- **Cost**, 8 effects at once (all six kinds) on one client: frame time 16.67 ms idle vs 16.79 ms average with them
  running (one 37 ms frame as eight start in the same frame); at most 98 instances in the effects folder; all gone
  1.2 s after the end. Studio on an RTX 4080, so a real phone has less headroom; the one-frame spike is the eight
  Highlights + emitters + shard parts being made at once.
- **Emotes**: the wheel opens on T in the hub and training; pointing at a slot lights it and names it; a click plays
  it. The server's own view of the character shows the emote's track playing (so everyone sees it) and the
  `HeldWeapon` gone. The camera swings out to 9 studs. Found and fixed: your own body stayed hidden (first person's
  hiding stays on when the camera turns Scriptable): it's shown while the camera is out and each part's own value
  goes back after, so first person stays clean.
- **Equip screen** (v526): opens from the test hook and the loadout's button path; the kill grid shows Default worn,
  the free ones open and the rest padlocked with LOCKED / "FROM DUFFEL BAGS AND THE SHOP"; the emote tab shows the
  ring of 8 slots (Wave, Salute) over the six emotes. The copy of you plays the picked emote (its head drops 1.1
  studs at the bow's low point, measured) and the picked kill effect. Photos: `equip-screen-sheet.jpg`.
- **Not tested**: the mid-match enemy hiding (needs a match with a second player); the phone button on a real phone;
  the 2 s cooldown note; two players watching each other's effects (Studio solo).
- **Saves**: the owner's flair save was put back to the defaults after the tests (kill none, wave + salute).

Known limits / next:
- The generated clips are a first set: Bow and Salute read well; Wave, Clap and Fist Pump are small moves; Groove is
  busy. More takes (one prompt at a time) can replace any of them: upload the new clip and change its id in Flair.
- No sounds yet (Rivals finishers have them). Pro Sound Effects search works in Studio (`AssetService:SearchAudio`,
  Artist "Pro Sound Effects"); a short recorded sound per effect, played at the body, plus a "mute others' kill
  effects" settings row would be the next step.
- Rivals hides the crosshair while you emote; ours stays.
- The loadout's KILL EFFECT · EMOTES button was not photographed (it sits left of DONE at the top).

## Newest first and NEW (18 Nov, shop-gui)

Every grid in this picker runs: what you have, newest first; then the free ones, the plain one first (no kill
effect, the rope, no pet); then the rest as listed. A small amber NEW dot sits top left on a new card and on its tab
until you change tab or close.
- Kill effects, emotes and grapples: the loot save's order and NEW marks (the Loot remote's `"inventory"`, and
  `"seen"`).
- Pets: this save's own. `grantPet` records `d.petsAt[id]` (the order found) and `d.petsNew[id]`. `"state"` sends
  `petsAt` and `petsNew`, and `("petseen", ids)` clears them.
- Opened without a tab (the loadout's button), the picker lands on the newest NEW thing's tab, with it picked.

Doc: `SHOP.md` (Newest first, and NEW dots). Photo: `docs/shop/newest-first-pets.jpg`.
