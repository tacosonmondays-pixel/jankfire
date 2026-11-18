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

## The layout editor and the phone HUD (18 Nov)

The owner, after playing on a phone: "ui on mobile is a bit clunky, can you add a custom ui like remapping and a
button resizer for mobile players, and they can move buttons where they want".

### The layout (`src/client/TouchLayout.luau`)

- Every touch thing is a record: the ten buttons (FIRE, JUMP, SLIDE, AIM, HOOK, STAB, SWAP, RELOAD, the katana's WAVE
  / the Scythe's FORM, YANK), the top row (SETTINGS, AUTO, EMOTE), the move stick, and the HUD's two boxes: WEAPON
  (Utility's item plate, FightHud's ammo plate and the three slot chips, stacked) and HEALTH (the speed plate over a
  slimmer health plate). Each has a place (its middle in thousandths of the safe area; none = its default place), a
  size (60-160 %), its own opacity (20-100 % of the TOUCH tab's BUTTON OPACITY), an action, and hidden or not.
- **Actions** (`TL.ACTIONS`; a button can be given any of `TL.PICK`): FIRE, AIM, JUMP, SLIDE, RUN, HOOK, RELOAD, SWAP,
  SLOT 1, SLOT 2, STAB, ITEM, CAMERA (third person), EMOTE. Each presses its action's default key through `Keys`, as
  before. Not in the list: the goggles' flash (Utility listens to the keyboard alone, not to `Keys`), ping and inspect
  (the game has neither). WAVE and YANK keep their own actions: they show only when they can be used.
- **Extra buttons**: up to six (`x1`..`x6`), any action from the list.
- **Can't be hidden**: SETTINGS (it is the way back into the editor), the stick, the two boxes. The boxes can be moved
  but not sized or faded.
- **Three layouts per player** in the settings save (`Settings.luau` / `SettingsServer`): `tl<n>.<id>` =
  `"x,y,size,alpha,action,hidden"` for each thing that differs from the default, and `tl.slot` = the layout in use.
  The save takes plain values of up to 64 characters and up to 200 keys; three full layouts are about 60. `tl` is not
  under `touch.`, so the TOUCH tab's RESET leaves layouts alone.
- **Left-handed** (`touch.lefty`) mirrors the buttons, the stick and the health box, custom places included (they are
  stored unmirrored).
- `TL.place` works out every middle and size for TouchControls and the editor alike. It keeps things inside the safe
  area and below Roblox's own buttons (`GuiService.TopbarInset`). The top row's default spot drops under a match's
  scoreboard and mode line when they would touch (`TL.pillTop`).

### The editor (`src/client/TouchEdit.client.luau`)

- **Opening it**: Settings → CONTROLS → TOUCH LAYOUT: EDIT (the row is there while the touch controls are on), and the
  same row at the top of the TOUCH tab. Both set the player attribute `TouchEditOpen`. Roblox's own pause menu can't
  take a game's buttons, so the settings page is the way in.
- **The screen**: it dims and draws every thing where it is, with a light grid (lines every 16 points, snapping every
  8). Drag a thing to move it; it stays in the safe area. Tap one to get its panel.
- **The panel**: SIZE and OPACITY sliders; ACTION (a list of the actions); HIDE / SHOW; STICK: FLOATING (it appears
  where your thumb lands, on the side it rests on) or FIXED (it only takes a thumb on or near it, and stays put);
  REMOVE for an added button; DONE.
- **The bar**: LAYOUT 1 2 3, ADD BUTTON, RESET (the layout shown, back to the default), CANCEL, SAVE (it saves and
  uses the layout shown).
- **While it is open**: the panel sits in the half of the screen away from the thing you picked. MenuCursor holds
  the game still, and TouchControls hides its own buttons.

### The phone HUD (TouchControls)

- On a phone (short side under 600 points) the fight HUD's guis (`JankfireFight`, `JankfireHud`, `JankfireModes`) are
  drawn at `clamp(height / 560, 0.62, 0.86)`: 0.70 on a 390-point phone and 0.75 on the owner's (about 932 x 420
  points). At 1x, plates laid out for a 720-tall screen had covered a third of the view. This goes through
  `Theme.guiK[<gui name>]`, which `Theme.scaled` reads. The menus keep their own phone layouts. Tablets stay at 1x.
- **The WEAPON box** (by default): small, at the bottom, its right edge left of the middle, so it sits clear of the gun
  in your hands. From the top: the item plate, the ammo plate, then the three slot chips (76 x 28 each).
  - Tap the ammo plate to reload (on letting go). Swipe it sideways to change to the next or previous weapon.
- **The HEALTH box**: the speed plate over the health plate, which is slimmer on a phone (160 wide, not 212), in the
  bottom-left corner under the stick's resting place.
- **The top row**: slimmer (28 tall, small words, fixed widths), right to left. It moves under the scoreboard when they
  would touch (on narrow phones).

### Testing it (Studio)

- As before: `StarterPlayer` attribute `TouchForce = true` in Edit before Play (take it off before saving), then
  TouchTest `fake:932x420` (the owner's phone, about 932 x 420 points), `fake:844x390` or `fake:1133x744` (a tablet).
- **TouchTest** also takes `swipe:1` / `swipe:-1` (the ammo plate's swipe). Its `state` JSON now has `btns` (id,
  action, middle x, middle y, width, shown), `pills`, `stick` (middle, width, float / fixed), `area`, `phoneK`, `slot`
  and `pressed` (the last action a button pressed).
- **TouchEditTest** drives the editor: `open`, `slot:<n>`, `select:<id>`, `move:<id>,<x>,<y>`, `size:<id>,<pct>`,
  `alpha:<id>,<pct>`, `act:<id>,<action>`, `hide:<id>` / `show:<id>`, `add:<action>`, `remove:<id>`,
  `stick:fixed|float`, `pick:act|add|none`, `reset`, `save`, `cancel`, `state` (writes `TouchEditState`). Mouse drags
  work too, because TouchForce makes the mouse a finger.
- Settings saves in Studio go to the `_studio` stores (Profiles), so these tests never touch a live save. Still, clear
  the test layouts afterwards with SettingsTest `reset:tl`.

### Tested (18 Nov, place version 957, 932 x 420 phone box, in training)

Sheet: `touch/touch-layout-sheet.jpg` (before: the owner's own screenshot, with a player's name blurred; after;
the editor; the saved layout in play).

- **Phone HUD at 0.75**: the weapon box sits at 235-412 x, clear of the gun. The health box and stick are clear of
  each other, and the top row sits at the top in training.
- **Editor**: JUMP moved to (560, 330) and snapped to (560, 328), with SIZE 130 % and OPACITY 60 %. It was remapped
  to SLOT 2. RELOAD was added as `x1`, EMOTE hidden and the stick set to FIXED, then saved.
  - The settings save (state "cloud") then held `tl1.jump = "601,781,130,60,slot2,0"`, `tl1.x1`, `tl1.emote` and
    `tl1.stick`.
  - The game rebuilt its buttons from it. Tapping JUMP pressed slot 2 and the revolver came up; tapping the new
    button pressed reload.
- **Rejoin** (a second Play, 17:26 UTC): the layout came back from the save. JUMP was SLOT 2 at (560, 328) at 75
  points, the RELOAD extra was there, EMOTE hidden and the stick FIXED. SettingsTest `reset:tl` then cleared every
  `tl` key (0 left).
- **The default layout at other sizes**:
  - 844 x 390 (`touch/phone-hud-844-v957.jpg`): HUD at 0.70.
  - A 1133 x 744 tablet (`touch/tablet-hud-1133-v957.jpg`): HUD at 1x, buttons at 1.2x, as before.
- **Not checked yet**:
  - the top row dropping under a match's scoreboard (no match in these tests)
  - left-handed
  - a real phone (real drags, two fingers)
