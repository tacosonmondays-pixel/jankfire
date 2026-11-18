# Controller support (gamepad)

Asked by the owner on 18 Nov 2026: "can you add controller support?" An Xbox or PlayStation pad plays the whole game through Roblox's Gamepad input, as keyboard and mouse and the phone do. It uses the same single input path: **Binds** (the KEYBINDS' third column), **Keys** and **Settings**. There is no second input system.

## Files
| file | what |
|---|---|
| `client/Pad.luau` | Which device is in your hands (`Pad.on()`, player attribute `PadOn`). It also holds the sticks and triggers, the button pictures and short names (`Pad.image`, `Pad.short`), the key-cap glyphs (`Pad.chip`, called by `Theme.key`) and hint text (`Pad.say`, called by `Keys.say`). |
| `client/PadLook.client.luau` | Right-stick look: deadzones, curve, speed, acceleration and pad-only aim assist. Turns the camera at `RenderPriority.Camera + 2`. |
| `client/PadNav.client.luau` | Menus: GuiService selection inside the top menu, the focus ring, B to back out, the bumpers for tabs, slider nudges, right-stick scrolling, and VIEW. |
| `client/Binds.luau` | The pad defaults (below) and `padToggle` (a pad's own hold or toggle). |
| `client/Settings.luau` | The `pad.*` defaults. |
| `client/SettingsUI.luau` | The **CONTROLLER** tab, slider nudges (`UI.nudge`), and View cancelling a rebind. |
| `client/SettingsApply.client.luau` | Roblox's own stick turn is off while `Pad.on()`, so nothing turns twice. |
| `client/FlairClient.client.luau` | The emote wheel: the right stick points at a slot, and the bumpers turn the page. |
| `client/LoadoutUI.client.luau` | B closes the screen (player attribute `MenuBack`). |
| `client/FightHud.luau` | The controls line shows pad buttons while a pad is in your hands. |

## The layout (defaults; every action can be rebound)
Rebind on the CONTROLLER tab or in the KEYBINDS' CONTROLLER column. Select a button, press A, then press the new button. View cancels.

| Xbox | PlayStation | in play | in a menu |
|---|---|---|---|
| RT | R2 | fire / swing | — |
| LT | L2 | aim down sights; the katana parries, the knife stabs | — |
| X | Square | reload | — |
| Y | Triangle | next weapon (round the loadout, the Shredder included) | — |
| RB | R1 | grapple (the hook, onto walls and people) | next tab |
| LB | L1 | utility (hold to cook a grenade, let go to throw) | previous tab |
| B | Circle | crouch / slide | back out |
| A | Cross | jump (rope: fling) | press the selected button |
| LS (click) | L3 | sprint (toggle by default) | — |
| RS (click) | R3 | melee weapon | — |
| D-Up | D-Up | READY before a round; goggles flash in play | move |
| D-Down | D-Down | third person | move |
| D-Left | D-Left | katana slash wave (the katana session's) | move / slider down |
| D-Right | D-Right | emote wheel (hold, point with the right stick, let go) | move / slider up |
| left stick | left stick | move | move |
| right stick | right stick | look | scroll |
| View | Touchpad | the buttons on screen: a pop-up, else the hub's menus and SETTINGS; in a match, SETTINGS | close SETTINGS |
| Menu | Options | Roblox's own menu (reserved: games can't take it) | — |

- **Why D-Up is shared.** READY only counts in the loadout window before a round, when you're held at your spawn. The goggles flash only counts in play. All 15 pad buttons are in use, so these two share one. Binds' swap logic still keeps a rebind unique.
- **Why View and not Start.** Start belongs to Roblox (`Binds.RESERVED`). There is no Tab scoreboard either: Tab is Roblox's own player list, and the match score is always on screen. So View is the menu button. It opens SETTINGS directly when SETTINGS is the only thing on screen (in a match).
- **No "previous weapon" default.** With three or four slots, Y cycles round them. The KEYBINDS keep slots 1–4 for players who want direct buttons.
- **Pad-only hold or toggle.** `pad.aimToggle` (hold), `pad.crouchToggle` (hold) and `pad.sprintToggle` (toggle). Binds reads them when the last press was a pad's (`lastPad`), so a keyboard player's own setting is untouched.

## Looking (PadLook.client, the CONTROLLER tab)
- **Speed:** full stick turns 240°/s at LOOK SENSITIVITY 1.00. That is Roblox's own pad camera: 4° a frame at 60 fps. Up and down is 0.77 of that (Roblox's ratio), times VERTICAL SENSITIVITY, times INVERT LOOK Y.
- **Deadzones (right stick):** INNER 12% (round, so diagonals feel the same) and OUTER 5% (that much of the edge counts as all the way).
- **Response curve** (how far over → how fast):
  - LINEAR: t
  - STANDARD (default): t^1.7, finer near the middle
  - DYNAMIC: an S-curve, 3t² − 2t³
- **Look acceleration (on):** held past 92% for 0.12 s, the side-to-side turn rises to 1.75× over 0.4 s, at the hip only. A turn-around doesn't take a second.
- **Aiming:** the web game's rule, as the mouse has it (SettingsApply's `aimK`): `(1 + (AIM SENSITIVITY − 1) · aim) / (1 + (zoom − 1) · aim)`. At 1.00 the screen moves under the crosshair at the same speed as at the hip.
- **Where it turns:** a change from this frame's look at Camera + 2, as the phone's look and the guns' kick already do.
  - First person and the shoulder camera read it back next frame. Recoil, the aim's framing and third person behave as with a mouse.
  - It stays still under a menu, a finisher, a crate reveal or the death cam, and with any other scripted camera.

## Aim assist (a controller only, never a mouse)
It ports `public/js/aimassist.js` and keeps its rules and ring:
- enemies only (never your Team)
- plain sight only (the map ray bullets use)
- the body, never the head
- only while a stick is moving (0.35 s after the last push)
- it only turns your own camera; hits are still the server's

| part | numbers |
|---|---|
| ring | 0.14 rad (~8°) + the target's own width, ÷ zoom when scoped; range 90 m |
| slow-down | the turn × `1 − min(0.6, 0.55·k) · (0.35 + 0.65·close)`: 0.81× at the ring's rim, 0.45× dead on at full strength |
| rotation | the crosshair follows 35%·k of a target's drift across your view (your strafe or theirs), at most 1.2 rad/s |
| tug | toward the body inside 0.085 rad (+ width): 60% of the phone's 0.38 rad/s × k, fading to nothing at the rim |
| strength `k` | AIM ASSIST STRENGTH (default 100%); AIM ASSIST off = 0 |
| ranked | `k` is capped at **0.6** while `HookLimit` is on (a RANKED duel or a PARTY RANKED match): slow-down 0.67× dead on, rotation 21%, tug 0.14 rad/s |

- It doesn't work in the hub or a map room (there is nothing to shoot), but it does work in training (the dummies).
- **Fair against a mouse:** the tug at full strength is 13°/s, and 8°/s in ranked. A mouse turns hundreds of degrees a second, so the assist only steadies a thumb; it never out-aims a hand. It never starts a turn on its own, and it never helps through a wall.

## Menus (PadNav.client)
- **The menus covered** (by their MenuCursor name): settings, shop, loadout, matchloadout, play, party, quests, card (the profile), loot, board, wheel, flair, report and anticheat.
  - Each has its ScreenGui, a back function and, where it has tabs, a bumper function (`Pad.MENUS`). A new screen adds its own row: `Pad.MENUS.<name> = { gui = "...", back = fn, tabs = fn }`.
- **Selection:** Roblox's own (`GuiService.SelectedObject`); the D-pad and left stick step it and A presses.
  - It starts on a sensible button: the settings tab you're on, else the top-left one.
  - After a screen rebuilds its buttons, it comes back to the button nearest where it was.
  - Full-screen catchers and buttons that only hold other buttons are never picked.
  - The screen's top frames are selection groups that stop at their edges, so the selection never wanders into the HUD.
  - A list scrolls the picked button into view, and the right stick scrolls too.
- **B** backs out of the newest menu:
  - the shop: confirm → odds → inspect → close
  - a crate: a reveal → DONE, the reel → SKIP
  - the loadout: `MenuBack`
  - the match picker's tray, the emote wheel: Escape through Keys
  - the others: their own `close()`
  - SETTINGS: B closes it, except while a button is being rebound (then B is the button you bind).
  - The Play panel is the lobby: LEAVE LOBBY is a button, and B leaves it alone.
- **Bumpers:** the SETTINGS tabs, the shop tabs, the Play panel's DUELS / MODES.
- **Sliders:** the selected slider steps with D-Left / D-Right or the left stick, a fortieth of its range a step (or its own step), and repeats when held.
- **The focus ring:** one quiet white rounded ring, 2 px, with a 7% white wash (`PlayerGui.SelectionImageObject`). A mouse player never sees it: the selection is cleared the moment the mouse moves.
- **VIEW** goes to the buttons on screen, in this order:
  1. what someone threw at you: pop-up ads (A closes the picked one, as its number key would, and the next one is picked) and a pop quiz's answers
  2. the match loadout strip (slots, READY)
  3. an invite (JOIN / DECLINE)
  4. QUICK JOIN
  5. a vote
  6. the hub's menu column (LOADOUT, PLAY, PARTY, SHOP, PROFILE, QUESTS) and then SETTINGS, which opens with A

  B or VIEW again leaves them. While they're picked, the left stick moves the selection, not you.

## Prompts and glyphs
- **Key caps** (`Theme.key`): while a pad is in your hands, every cap shows the pad's own picture of the button for the same action (`UserInputService:GetImageForKeyCode`, so Roblox picks Xbox or PlayStation pictures). It keeps the same cap and the caps' white. A mouse or a key switches back.
  - The cap's action comes from its letter: the key as bound now, or the default.
  - An action with no pad button leaves an empty cap (nothing drawn), e.g. the hub menus' L / B / M / K. A lone number (an answer, a vote, an ad) is always empty: on a pad you select it.
  - A cap can name its button: attribute `Pad = "ButtonB"` or `PadAction = "<bind id>"`. PadNav marks the View glyph by SETTINGS, the match loadout header, QUICK JOIN and the ads' and quiz's caps, and B on the shop's CLOSE and on the finisher and killcam SKIP.
- **Words:** `Keys.say` (every callout and note) and bracketed hints in menus ("DONE  [L]", "SKIP  [SPACE]") follow the pad, using the button's short name or dropping a key the pad has no button for. A crate's SKIP is A. FightHud's controls line lists pad buttons.

## Tests (Studio, no real pad)
- Set `PadForce = true` on the player (or on StarterPlayer, in Edit, removed before saving): `Pad.on()` is then true.
- `PadTest` attribute:
  - `stick2:x,y` / `stick1:x,y` (a pretend stick), `trigger:ButtonR2,1`, `clear`
  - `press:<KeyCode>` / `release:<KeyCode>`: a pretend button through `Keys.padPress`. Every Keys listener hears it as a pad's (UserInputType Gamepad1), and Binds matches the player's own controller column.
  - `state`: `PadState` JSON with the look this frame, the slow-down, tug, rotation, target angle, k and the selection.
- `PadNavTest` attribute: `bar`, `back`, `tab:1`, `nudge:1`, `select:<full name>`. With `PadNavWatch = true`, `PadNavState` holds the top menu and the selection.
- **Measured in solo Play with a forced pad** (place v765 and v772; photos in `docs/controller/`):
  - Every key cap swaps to the pad's picture: the View glyph by SETTINGS, the hub menus' caps empty. The controls line reads "Y next weapon, RS melee, LB <item>, RT fire, LT aim / parry, X reload, LS run, B slide, hold RB grapple, D-DOWN camera" (`hud-controller-glyphs-v765.jpg`).
  - VIEW in the hub puts the ring on the menu column (`hub-view-focus-ring-v772.jpg`).
  - SETTINGS:
    - The CONTROLLER tab opens with the ring on a row (`settings-controller-tab-focus-v765.jpg`).
    - A slider nudge steps LOOK SENSITIVITY 1.00 → 1.10.
    - RB goes to CROSSHAIR, with the selection on its nearest pill.
    - B closes it.
  - The emote wheel: hold D-Right, push the right stick up-right, and slot 2 lights (`emote-wheel-right-stick-v772.jpg`). Letting go plays it and closes the wheel.
  - Pad buttons through Binds (pretend Gamepad1 presses): RS takes out the katana, and Y goes round to the SMG, then the revolver.
  - The right stick held fully over turns the shoulder camera about 7° a frame once the acceleration is up.
  - Aim assist on the training Stand 12 studs away:
    - Only the move stick pushed, 3.2° off the body: the crosshair settles 0.25° off in 0.6 s.
    - The look slows to 0.46× near dead on.
    - From 40 studs behind an arcade column it does nothing (the wall check).
- **Not tested without a real pad:**
  - Roblox's own selection stepping with a real D-pad and stick
  - A pressing a selected button
  - B, View and the bumpers through real input (only the test hooks)
  - the PlayStation pictures
  - a trigger's pull threshold
  - whether the left stick is held while a button is selected
