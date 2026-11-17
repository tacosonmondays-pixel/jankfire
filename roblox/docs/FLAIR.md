# Kill effects, emotes and grapple skins ("flair")

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
`COSMETICS.kill`: same ids, names, rarities), restyled to the serious look (no text anywhere, no gore), with the five
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
| shatter | Shatter | rare | 1.0 | glazes like ice for a beat, then breaks into ~28 ice wedges and glints |
| ember | Ember | rare | 1.4 | chars dark with a glowing orange edge, burns away from the head down into embers and ash |
| chicken | Chickens | epic | 1.5 | a soft pop of feathers; three small chunky chickens scatter and run off |
| bsod | Blue Screen | epic | 1.2 | a flat blue panel (blank bars, a filling bar) replaces the body, then switches off like an old monitor |
| yeet | Yeet | epic | 1.3 | launched straight up, spinning, a dotted streak under it, a glint high above |
| ink | Ink | epic | 1.2 | floods solid black, bursts into blots, flakes and droplets that fall |
| static | Static | epic | 1.0 | flickers, jitters and slices like a lost signal, then snaps out to a point |
| ascend | Ascend | legendary | 1.5 | a soft shaft of warm light (top 2.6 studs over the head) gathers; the body glows, lifts and goes up as motes |
| duck | Big Duck | legendary | 1.5 | a big rubber duck (round pieces, the game's duck yellow) drops on the body, squashes, gulps, shrinks away |
| blastzone | Blast Zone | legendary | 1.0 | a white-hot flash and shock ring; the body is knocked clean away from the killer, spinning, out of sight |

All drawn from the VFX pipeline's approved sprites (glow, sparkle, chips, dust 4x4, lumps 4x4, spark, ring, tracer,
feather) and plain client parts (stone, notes, cubes, balloons, chickens, the duck): no new uploads. Particle `Size` is half the width (VFX-PIPELINE.md).

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

| id | name | rarity | s | clip |
|---|---|---|---|---|
| wave | Wave | free | 2.97 | 132747832692830 (uploaded through Open Cloud) |
| salute | Salute | free | 2.97 | 134567333056285 (uploaded through Open Cloud) |
| clap | Slow Clap | common | 2.97 | 77903138772400 |
| victory | Fist Pump | rare | 2.47 | 89328448326408 |
| bow | Bow | rare | 2.97 | 87535060714783 |
| groove | Groove | epic | 3.97 (loops) | 135577596597530 |

The clips come from Studio's prompt-to-animation tool (`generate_animation`, the owner's rule), one or two tries each,
judged from pose strips. Prompts (all with `duration`):
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

## Equip screen (`client/FlairUI.luau`)

The loadout screen has a KILL EFFECT · EMOTES button left of DONE; it closes the loadout and opens this screen (not in
a match). Left: the kill effect grid (EQUIP) or the wheel's 8 slots over the emotes (pick a slot, pick an emote, PUT IN
SLOT n; EMPTY SLOT). Locked items show a padlock. Right: a client-only copy of your own avatar stands in the world in
front of you and plays what you point at, on a loop (a ViewportFrame can't draw particles). DONE or Esc closes.

## Owning and saving

- **Owned**: the loot save's (`Loot.owns(p, "kill" | "emote" | "grapple", id)`, bare ids like card looks). Free: kill
  none / confetti / dissolve; emote wave / salute; grapple rope. The rest roll from the Duffel Bag and sell in the shop (the loot and
  shop sessions wire `Shared.Flair` into LootTable and Shop the way they read CardStyles: `TYPES`, `info`, `ORDER`,
  `CONTAINER = "bag"`, `forSale`, `picture`).
- **Worn**: FlairServer's own session-locked store `JankfireFlair_v1` (Profiles.luau): `{ v = 1, kill, emotes = { 8 } }`.
  Nothing else's save is touched. A saved pick you don't own stays saved but isn't worn.
- Player attributes: `KillFx` (worn), `Emotes` ("wave,salute,,,,,,"), `Emote` (playing now), `FlairSave`.
- Remotes: `JankfireRemotes.Flair` (RemoteFunction: state / kill / slot / emote / stop) and `FlairKill` (RemoteEvent),
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
