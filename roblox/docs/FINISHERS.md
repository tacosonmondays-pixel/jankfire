# Finishers (Roblox)

The owner asked on 17 Nov 2026: "Are you able to create a cinematic finisher with effects? Like finishers from Blade
Ball, you can look those up! Except it's for our guns, and only with high tier skins? Like with super dynamic and fluid
movement, angles, perspective."

A **finisher** is a short cinematic that plays when a high-tier skin that owns one lands the kill that wins a round or
the match. It is ours: inspired by how other games stage a winning kill, never copied (no names, shots, art or sounds of
theirs).

## Research, in short

The full note is in the vault: `Research\Finishers.md` (sources and clips to watch are listed there; nothing was saved
from them).

- **Blade Ball:** a cutscene on the kill that wins a round, the last one of a 1v1 standoff. The loser is its target.
  Ordinary kills only get a small kill effect. A finisher is a separate, very rare item on top of a top-rarity weapon.
  No skip was found. It fills the gap at the end of a round that is there anyway.
- **Valorant:** premium skin lines have a finisher at their top upgrade level. It plays on the last kill of a round,
  inside the fixed post-round window, so it never delays the next round. It is an effect in the world round the
  victim. The killer keeps their own view. Since 2025 the player who dies to one gets a cinematic camera of it,
  partly because the plain view misbehaved and the effects were too busy.
- **RIVALS:** no cinematic finisher. Its "finishers" are kill effects on every kill (ours: `FLAIR.md`). Its only staged
  camera moment is the win screen, where the winners pose in the arena.
- **Camera craft that works:** about 2 to 3 s in all, never over 3. Each shot held long enough to read (about 0.5 to
  1 s). Cuts on an impact. Ease every move. Orbits no faster than about 60 degrees a second. Little roll, and no shake
  in slow motion. At most a flash or two. Any input skips it. Never take the camera of someone still fighting.
  Roblox has no global time scale, so slow motion has to run on local copies of the bodies with slowed effects.
- **The owner's reference (17 Nov, an X post):** a breakdown of an anime-style special move: camera blocked on a
  mannequin first, then the video, then a VFX pass with an energy glow and orb, impact smoke, a cut-in and a two-tone
  grade. From it we took ideas, never its look: the CHARGE close-up on the gun with the light gathering at the muzzle,
  a two-tone impact frame in the skin's colour, and smoke at the hit. Blocking the camera on stand-in bodies before
  the effects is how `Finisher.preview` works too.

## What ours does

### When it plays, and who sees it

| the kill | the cut | who sees it | when |
|---|---|---|---|
| the one that **wins the match** | **full**, about 2.9 s | **everyone in the match** | the end-of-match window: the end screen is already up, nobody is playing |
| the one that **wins a round** (not the match) | **short**, about 1.7 s | the **killer** and the **victim** only | the 3 s between rounds (the round is over, nobody can be hurt) |
| a classic mode's last kill (Gun Game, Infection…) | **full** | everyone in the match | that mode's end |
| any other kill | none (only the kill effect) | | |

Rules:

- **Who triggers it:** the killer's skin on the weapon that made the kill must own a finisher. The killer must still be
  standing (a trade has no hero). The victim must be a player. A fall or the Shredder never plays one, because there
  is no shot to show.
- **Round finishers are only for the two of them.** The other players are between rounds anyway, but a cinematic every
  round for everyone would wear thin in a first-to-5 match. Everyone gets the big one at the end, as Blade Ball does.
- **Nothing waits on it.** The cuts fit windows that already exist:
  - A round's short cut (1.7 s) ends well inside the 3 s between rounds. A round going live or a respawn ends it anyway.
  - The match's full cut starts at the kill and is over before the play of the match is due (3.5 s after the end screen
    opens, which is itself 1.2 s after the kill).
  - The end screen opens under it and shows once it ends. Respawns, rounds and the trip home are untouched.
- **Skippable:** SPACE, B on a gamepad, or the SKIP button.
- **The killcam:** for the victim, the finisher is that death's camera. Their killcam is skipped for that one death.
- **Settings:** `gfx.othersFinisher` (off = don't show finishers you only watch). Your own always play.
  The settings session adds the row. Until then the default is on.

### How it fits the replay system

The finisher is built on the match recording and the replay player that the play-party-ranked session made
(`REPLAY.md`). There is no second recorder and no second set of bodies:

1. The server (`FinisherServer`) takes the last 1.65 s of the recording (`Recorder.recent`), cuts it down to the two
   fighters and sends it on `JankfireRemotes.Finisher`. That is about 2 KB.
2. The client plays it on the replay's **ghosts** (`Replay.makeGhost` / `poseGhost`): clean copies of each player's
   own avatar, posed by ThirdPerson with their real skin, wrap and gun hat, aiming and firing as recorded.
3. The camera uses the replay's **wall test** (`Replay.clearTo`). Every lens spot is pulled in front of anything solid
   between it and what it looks at. The side of each shot is the one with the most room.
4. Live bodies and the other screens are hidden while it plays, the same way a replay does it.

### The camera: one cut, four shots

| shot | full | short | what the lens does | the recording |
|---|---|---|---|---|
| **HERO** | 0.5 s | – | Low and in front of the shooter, off to the side with more room. It pushes in and up as they line up the shot (FOV 54 → 43, a slight tilt). | runs at about half speed up to the shot |
| **CHARGE** | 0.38 s | – | Tight on the gun from beside the muzzle, looking back along it, a slow push (FOV 44 → 36). The skin's light gathers into a swelling orb at the muzzle, motes drawn in from all round. | held a breath before the shot |
| **CHASE** | 0.48 s | 0.45 s | The killing shot becomes a slug in the skin's colours, leaving its trail and the theme's bits behind. The lens rides just behind and beside it with a wide FOV punch that settles (84 → 58). It whips in from the previous view. | frozen (bullet time) |
| *WHIP* (a blade) | 0.62 s | 0.45 s | Instead of the chase: the lens whips 150 degrees round the shooter through the swing. | runs through the swing |
| **IMPACT** | 0.42 s | 0.32 s | Close on the hit, tilted, pushing in (FOV 50 → 40). An impact frame: for 0.08 s the whole picture goes two-tone, black and the theme's colour, with a soft flash. Then smoke thrown back along the shot, a shock ring and the theme's burst. That is the cut's one flash. Effects run at a third of their speed. | the victim's last moment, slowed |
| **RESOLVE** | 1.12 s | 0.9 s | An orbit round the victim of 60 to 72 degrees, eased, rising and pulling out, while the theme plays out. The finisher's name and the skin's name come in. Then a fade to black and back. | the shooter barely moving |

Around the shots:

- **Letterbox bars** slide in over 0.2 s and out at the end.
- A **colour grade** per theme (tint, saturation, contrast) eases in.
- **On screen:** the finisher's name, the skin's name, and SKIP. No other words.

### The finishers

Each finisher belongs to a skin set. The skins that own one are that set's high-tier pieces (and the VIP Ducky set). The
first three are built. The other five are rows in the data, marked `built = false`, waiting for their themes.

| finisher | set | skins that own it | the theme |
|---|---|---|---|
| **Ascension** | Seraph | Seraph Rifle | A column of gold-white light falls on the victim. Two great wings of long rounded feathers (white with a gold leading edge) unfold behind them. They rise into the light and go to white. A gold halo settles over the head, feathers drift down, and they end in a burst of feathers. |
| **Hellgate** | Infernal | Infernal Rifle | Seven glowing cracks race out across the floor from under the victim. A pit opens with a molten rim. Flames, embers and smoke climb out. The victim tips forward and sinks into it, burning dark. A last gout of fire, and it seals over. |
| **Splashdown** | Ducky (VIP) | Bubble Bath, Wish Duck, Ribbon Duck | A giant rubber duck in the VIP set's look drops out of the sky: rubber yellow, an orange bill, a pink bow with a gold star clip. It stretches as it falls and casts a real shadow. It squashes on landing in a burst of soap bubbles and a pink ring, wobbles, quacks, then pops into bubbles and gold sparkles. |
| *High Noon* (planned) | Dust Drover | Dust Drover, Iron Horse | a slow standoff zoom on the shooter's eyes, a dust devil, a tumbleweed |
| *Inkfall* (planned) | Tidecrest | Sakura | one ink-wash brush slash across the frame, the victim breaks into sakura petals |
| *Warp Out* (planned) | Star Drover | Star Drover, Streamliner | a teal hard-light ring pulls the victim in, the stars streak past |
| *Lantern Light* (planned) | Witching Hour | Pumpkin Patch | a giant carved pumpkin closes round the victim and its face lights up from inside |
| *Starchart* (planned) | (lone skin) | Triangulum | stars light on the victim's joints, the lines draw between them, it fades to sky |

**Why the first three:** they are the first three on the owner's list. The Heaven and Hell pair shows how one shot list
carries two opposite moods (up into light, down into fire). The Ducky set is the VIP pack's.

**Which skins qualify.** Each high-tier skin owns its set's finisher, and the VIP Ducky set owns one. The high tier
today is:

| | skins |
|---|---|
| built | Seraph Rifle, Infernal Rifle, Bubble Bath, Wish Duck, Ribbon Duck |
| planned | Dust Drover, Iron Horse, Star Drover, Streamliner, Sakura, Pumpkin Patch, Triangulum |

These are all 12 high-tier skins in `SkinSets` (the gun models session checked the list, 17 Nov). The Lantern Light and
Starchart ideas come from that session's special-skins sheet. The gun models session will say when a new skin
ships as high tier.

### The victim's body

At the impact the victim leaves the replay's control: no gun, no walk cycle, no third-person pose. The theme then
moves them: lifted, sunk or squashed, tinted with a Highlight, and faded at the end.

Their body reaction comes from Studio's prompt-to-animation tool (`generate_animation`), following the owner's rules:
4 takes a clip, the best kept. There are three clips (`Finishers.ANIMS`):

| clip | the prompt's idea |
|---|---|
| `lift` | struck, then rising with the arms opening and the head back |
| `kneel` | struck, dropping to the knees, slumping forward |
| `shield` | struck, looking straight up, throwing the arms over the head |

Until a clip's id is in, the victim gets a code-only shove back and tilt. The shooter is never animated by a generated
clip, because the tool can't hold a weapon. Their gun pose is ThirdPerson's, as recorded.

### Cheap on phones

- Client-only parts and particles, at most a few dozen parts and about a dozen emitters per finisher.
- Particle counts follow the settings page's particle amount and drop to 60% on a phone.
- No depth of field and no bloom changes. The only screen effect is one ColorCorrection on the camera.
- The effects use the VFX pipeline's approved sprites (feather, spark, flame, smoke, bubble, heart, ring, glow,
  sparkle). Nothing new was uploaded.
- Removed on the spot at the end or on SKIP.

### Selling and showing it

A finisher comes with its skin. There is no separate purchase, unlike Blade Ball, so it raises the value of the high
tier (as Valorant's top level does).

The shop session shows it:
- a **FINISHER** badge on the skin's card, from `Finishers.forSkin(skinId)`;
- a **preview** button that calls `Finisher.preview(id)`. That plays the full cut in front of you, from a made-up
  recording of you and a stand-in.

## Where it lives

| file | what |
|---|---|
| `src/shared/Finishers.luau` | the data: `LIST` (each finisher's name, set, skins, theme, colours, grade, victim clip, `built`), `BY_SKIN`, `ANIMS`, the shot lists `CUTS`, `LEAD`, `FRESH`, `forSkin`, `cut`, `length`, the pure `decide` |
| `src/server/FinisherServer.server.luau` | the kill and round hooks, the clip cut to two, the remote, the Studio test hook |
| `src/client/Finisher.luau` | the player: ghosts, the shots, the wall test, the overlay, the grade, SKIP, `preview` |
| `src/client/FinisherFx.luau` | the slug and the three themes |
| `src/client/FinisherClient.client.luau` | the remote, stopping on a round or a respawn, the settings row, the test attribute |
| `Recorder.luau` (small) | `Recorder.recent(fighter, secs)` |
| `Replay.luau` (small) | exports `decode`, `makeGhost`, `poseGhost`, `eyeOf`, `clearTo`, `hideLive`, `ghostFolder`; a ghost may be built from a given body (`info.template`) |
| `ReplayClient.client.luau` (one line) | no killcam while a finisher is that death's camera (the player attribute `Finishing`) |

**To add a finisher:**
1. Add a row to `Finishers.LIST`.
2. Add a theme to `FinisherFx.THEMES`: its slug look, flash colour, orbit, sounds, and `impact` / `resolve` functions.
3. Set `built = true`.

The shot lists are shared. A theme only says how its orbit moves and what happens in it.

## Testing alone (Studio)

- `ServerStorage.JankFinisherTest`:
  - `("arm", player, skinId, "full" | "short", all?)`: the player's next kill plays that skin's finisher.
  - `("kill", player, n | name, weapon)`: kills a training dummy through `Fight.hurt`.
  - `("decide", t)` and `("state")`.
- Recording a test kill: `ServerStorage.JankReplayTest("record", player)` first (the training hall, every dummy
  recorded), then arm, then kill.
- The player attribute `FinisherTest`:
  - `preview:<id>` or `preview:<id>:short`: the cut, staged in front of you;
  - `stop`.
- Workspace attributes for photos:
  - `FinisherSpeed`: 0 to 1, slows the whole cut;
  - `FinisherFreeze`: holds the cut at that many seconds.
  - The player attribute `FinisherT` shows where the cut is.
