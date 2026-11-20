# The Bath Ducky skin reveal (storyboard, 19 Nov 2026)

The owner sent their own storyboard for a "BATH DUCKY SKIN" reveal (runtime about 0:25-0:30, comedy / skin reveal),
asked "are you able to story board this?" and then "we can meshy or tripo the ducks!". This is that storyboard, staged in
Studio with our own pieces, and a plan for building it as a real in-game cinematic. **Nothing is in the game yet: the
build waits for the owner's OK on the plan below.**

![the sheet](bath-ducky/bath_ducky_storyboard.jpg)

Single panels: `bath-ducky/panel_01.jpg` to `panel_09.jpg`. The same sheet is in the vault under
`References/Animation/Bath Ducky reveal/`.

## The nine beats (the owner's)

| # | beat | time | what happens | camera |
|---|---|---|---|---|
| 01 | Peaceful bath time | 0:00-0:03 | the player relaxes in a bubbly bath, foam hair with a tiny duck on it, candles, tiles | slow push-in |
| 02 | Something beneath | 0:03-0:06 | the water darkens; a huge duck-shaped shadow slides in under the player | low, on the water line |
| 03 | The reveal | 0:06-0:09 | the giant Bath Ducky erupts: crown, foam cap, big splash, light rays | dramatic rise |
| 04 | The duck march | 0:09-0:13 | the Bath Ducky marches out in its robe, an army of small foam-capped duckies behind | tracking with the march |
| 05 | Formation | 0:13-0:15 | everyone stops and lines up facing the lens, the player (robe, foam hair) beside the giant | centre framing |
| 06 | The stare | 0:15-0:17 | dead silence; the player and every duck half-lidded and blank | slow push-in |
| 07 | Water attack | 0:17-0:22 | everyone squirts water at the camera at once | quick zoom + shake |
| 08 | Splash out | 0:22-0:24 | the screen is completely soaked | full-screen splash |
| 09 | Reveal end card | 0:24-0:28 | SKIN UNLOCKED, the player cheering among ducks and bubbles | hold |

## What it is made of

- **Which skin.** The giant duck wears a crown, so the board follows the **VIP Ducky set** (the Royal Duck guns: rubber
  yellow, white foam, sky blue, a gold crown). The end card's name is the owner's own, "BATH DUCKY". If the reveal is
  meant for Ducky Classic's Bubble Bath LMG instead (pink bow, hearts), the ducks get that set's palette; the shapes
  stay.
- **The ducks** are the owner's Tripo account (Smart Mesh, texture off, quad 5k), four takes each, compared side by side
  (the comparison sheet is in the vault, `Assets/tripo-19nov-bath-ducky/bath_ducky_takes.jpg`: Tripo renders stay
  out of git):
  - giant: take 1 (`d1f18221`) kept for the clearest crown, the bubbly foam cap and the tied robe;
  - army duck: take 2 (`4acdb2b6`) kept for the foam cap that reads as foam (with soap bubbles) and its own half lids.
    Take 4 of that run never left Tripo's queue.
  - Both went through Tripo's **Segment** tool (crown, foam, bill, eyes, robe, belt, wings, feet as separate parts),
    so each part takes one flat colour from the set's palette. `tools/roblox/bath_ducky_models.py` paints them, adds the
    giant's pupils and a separate half-lid piece (on for the stare), and builds the clawfoot tub and its water. The
    foam cap and head came as one part on the giant: a tilted "hairline" plane splits them.
  - The Tripo files stay in the vault (`Assets/tripo-19nov-bath-ducky/`), never in git.
  - Uploads (Model, all approved): giant `119395047122064`, army duck `111415394427988`, tub + water `112698164363965`.
- **The player** is a real R15 avatar (`Players:CreateHumanoidModelFromDescription`). Every pose is one keyframe of
  Roblox's own R15 animations, picked by a measurement, never keyed by hand: sit (the bath), idle (the line-up), point
  (the squirt: the frame with the furthest reach), cheer (the frame with the highest hands). Faces are the dynamic
  head's own FaceControls (eyes closed and smiling, jaw drop, half lids).
- **The stage** is `tools/roblox/bath_ducky_board.luau`: a bathroom far off every map, built, photographed panel by
  panel and removed in one Studio turn. Panel 8 is a lens pass over panel 7's frame and panel 9's label is drawn on
  the photo (`tools/roblox/bath_ducky_sheet.py`).

## Plan: the real in-game cinematic (for the owner to approve)

**When it plays.** Once, the first time the skin becomes yours (bought, a VIP pack that grew, a code, a gift). It waits
for a break the way the gift present does (`GiftReveal`): never over a live round; in the hub, between rounds, or at
the end of a match. Afterwards it can be watched again from the shop's inspect panel (a PREVIEW REVEAL button next to
PREVIEW FINISHER).

**Who sees it.** Only the player who got the skin. Nobody else's screen changes and nothing waits on it.

**How it is skipped.** SPACE, B on a gamepad, or the SKIP button (bottom right, as the finishers have it) jumps straight
to the end card; the card closes on any key or CLOSE. A round going live, a respawn or a teleport ends it at once.

**How it is built.** A client-only player like `Finisher.luau`, on a private stage under the map:
- the camera bound after Roblox's own (`BindToRenderStep`, `RenderPriority.Last` + a margin), Scriptable, eased moves
  between the board's lenses (push-ins, the rise, the tracking shot, the zoom-and-shake), letterbox bars in and out;
- the player's own avatar as a clone (the replay's ghost), posed from Roblox's R15 clips: sit, idle, point, cheer, plus
  a walk cycle for the march and the dynamic head's expressions;
- the ducks as client clones of the board's models, waddling (a roll and a bob per step) on a march path;
- water, foam and the splash as chunky parts plus the VFX pipeline's approved bubble and splash sprites; the soaked
  screen as a ScreenGui water sheet with beads that run;
- sound from recordings only, no voices: water lapping, a deep bloop as the shadow passes, the big splash, squeaky
  footsteps for the march, silence for the stare, the squirts, then the loot win sting on the card;
- on screen only the end card's label (SKIN UNLOCKED and the skin's name) and SKIP;
- cheap on phones: a few dozen parts, particle counts from the settings page.

**Questions for the owner.**
1. Which skin does it reveal: the VIP Ducky set (the crown) or a new "Bath Ducky" skin? (The board assumes the VIP set.)
2. 25 seconds is long for something that plays on its own. Keep the full cut for the first unlock and the shop preview,
   with SKIP always on screen?
