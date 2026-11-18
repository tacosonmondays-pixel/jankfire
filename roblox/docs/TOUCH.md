# Touch controls (phones and tablets)

Ported from the web game (`public/js/touch.js`, `touch.css`, `autofire.js`), 17 Nov 2026.

## Where

- `src/client/Keys.luau`: the one input path. `Keys.began(fn)` / `Keys.ended(fn)` hear UserInputService's
  InputBegan / InputEnded **and** the touch buttons, which press an action's default key as a pretend InputObject
  (a table: `KeyCode`, `UserInputType`, `UserInputState`, `Touch = true`, gameProcessed false). Also `Keys.isDown`
  (real key or a touch button holding it), `Keys.isTouch`, `Keys.name`, `Keys.say` (a hint's keys swapped for button
  names on a phone).
  **Rule for every listener:** tell a touch press apart with `Keys.fromTouch(io)`, never `io.Touch`. A real
  InputObject throws on a field it doesn't have ("Touch is not a valid member of InputObject"); on 17 Nov that broke the
  settings page's Binds (08:55-08:59 UTC) and the emote wheel until both guarded it.
- `src/client/TouchControls.client.luau`: the layer, the stick, the look, auto fire, the HUD moves.
- One-line hooks (a listener moved from `UIS.InputBegan` to `Keys.began`, etc.): `Move.client` (Shift, C, Space, E),
  `Arsenal.client` (fire, aim, R, 1-3), `Utility.client` (G down/up, ad numbers, a tapped ad presses its number,
  the ad tip), `Hud` (callouts through `Keys.say`), `Theme.key` (no key caps on a phone; a button that kept room for
  one centres its words), `CrouchPoses.client` / `ThirdPerson` (`Keys.isDown(C)` for the crouch pose).
- Settings: the settings page's store (`Settings.luau`, keys `touch.sens`, `touch.size`, `touch.alpha`,
  `touch.aimToggle`, `touch.autofire`, `touch.lefty`), saved per player by its server. Until that module is in the
  place, TouchControls runs on the web's defaults.

## What it does

- Only when `UIS.TouchEnabled` and not `KeyboardEnabled`. Roblox's own thumbstick and jump button are switched off
  (`GuiService.TouchControlsEnabled = false`, `DevTouchMovementMode = Scriptable`): no doubles.
- **Stick** (left 42 %): appears where the thumb lands; 8-way, like the keys; all the way up runs (Shift). It drives
  the control module's own `moveFunction`, the call the keyboard makes, so `Move.client` sees fresh keys.
- **Look** (anywhere else, and while a thumb is on FIRE, AIM or HOOK): 0.0088 rad per point × look speed (the web's
  rate), slower by as much as the view is zoomed. The camera module's own touch turning is off while these are on
  (its `CameraInput.getRotation` returns zero), so it never turns twice.
- **Buttons** at the web's places (points from the bottom corner on the fire side; × button size): FIRE (100, 92),
  JUMP (36, 50), SLIDE (34, 120), AIM (44, 184), HOOK (112, 176), STAB (176, 152: slot 3), SWAP (180, 98: your last
  weapon), RELOAD (176, 44). WAVE (112, 240) shows with the katana out. YANK (56, 244, 18 Nov) shows only while
  your rope is on a person and the yank is ready (the player attributes `HookBody` from Move.client and `YankT` from
  the server); it presses F, the yank's default key. Top row: AUTO, SETTINGS (taps P). The HUD's boxes are buttons too: three weapon chips
  (slots 1-3), the ammo plate (reload) and the item plate (G, held while held).
- **AIM** is a tap toggle by default (the web's first-run rule): it holds the aim key down while on.
- **Auto fire** (`autofire.js` rules kept): presses the same fire key as FIRE once the crosshair is on an enemy in
  range and plain sight (the game's own hit boxes, 0.12 m padding; walls block; same Team never), after a 120-260 ms
  blink; holds for automatics, taps semi-autos at a finger's pace, snipers only when scoped in. A thumb on FIRE wins.
- **The hub**: no weapons, so the fight buttons, chips and AUTO go, and the PLAY / PARTY / PROFILE / SHOP / LOADOUT
  stack moves to the right side (the left is the stick's). In a fight the ammo and item plates move to the bottom
  middle over the chips (the web's `touch.css` did the same).
- Safe areas: the layer is a `DeviceSafeInsets` ScreenGui; the hub stack keeps clear of the right inset.

## Testing in Studio

Studio's device emulator can't be driven from a script (`StudioDeviceEmulatorService` is hidden from them), so a
test fakes the screen:

- `game.StarterPlayer:SetAttribute("TouchForce", true)` in Edit before Play makes the client a "phone" from the
  start (key caps hidden too). **Remove it before saving.** A player attribute `TouchForce` also works mid-test.
- Player attribute `TouchTest`: `fake:844x390` (phone) / `fake:1133x744` (iPad mini) lays every `Scaled` HUD frame
  and the touch layer out in a box of that size; `real` puts it back. Presses: `down:<id>`, `up:<id>`, `tap:<id>`
  (ids: fire, jump, crouch, aim, hook, melee, swap, reload), `stick:<x>,<y>` (`stick:0,0` lets go), `look:<dx>,<dy>`,
  `chip:<n>`, `item:down|up`, `ammo`, `auto:on|off`, `settings`, `state` (writes `TouchState` JSON).
- Real touches can't be sent; the hook calls the same press functions the buttons do.

## Tested (17 Nov, place versions 560 and 572, phone box 844x390 and tablet box 1133x744)

Sheet: `docs/touch/touch-sheet.jpg`. In training, through the TouchTest presses (the same press functions the buttons
call): look 100 pt = 50.5 deg (the web's 0.0088 rad/pt); stick walks 10 m/s, a full push runs 14.5 m/s (Shift),
stops dead on release; JUMP; HOOK on and off the rope; FIRE held, 4 hits on the Stand; AIM toggle 80 -> 71 deg and
back, lit while on; auto fire 4 hits on the body, 0 through a wall; aim assist pulls onto the body (0.2 deg after
0.6 s), nothing with strength 0, no target through a wall; RELOAD; chips 1/2/3; SWAP back to the last weapon; STAB =
katana; EMOTE pill opens the touch wheel and an emote plays; SETTINGS pill opens the settings page; Loadout phone
pages; Shop's own phone layout. Not checked: a real phone, two-finger use (Studio sends one pointer), slide speed
(the run hit a wall), the Laptop item use.
