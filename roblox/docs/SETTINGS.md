# Settings (the page on P)

The owner, 17 Nov 2026: "A more detailed page for settings. Custom sensitivity for scoped in camera sniper, custom
cross hairs, volume, graphics, basically anything rivals has!!" Research: vault `Research/Rivals settings.md` (Rivals'
six tabs, Valorant's crosshair editor and code grammar, how other games set scope speed). Pictures stay local in
`References/settings/`. Inspired by, never copied: our own labels, our own layout, the game's Theme.

## Files

| file | what it is |
| --- | --- |
| `client/Settings.luau` | the values: `DEFAULTS`, `get` / `set` / `watch` / `changed` / `onAny`, `reset(prefixes)`, `row(tab, def)` for other scripts' rows, the save (remote `Settings`), `live` (aim, scoped, weapon, spread: FightHud writes it each frame), the colour-blind palettes (`teamHex`, `cbText`), the enemy outline colours |
| `client/Binds.luau` | the key bindings: 22 actions, two keyboard slots and a controller button each, `is` / `down` / `press` (hold or toggle) / `on` / `label`, swaps on a clash, reset |
| `client/Crosshair.luau` | draws the crosshair (FightHud's `Crosshair` frame and the page's preview) and reads / writes share codes |
| `client/SettingsApply.client.luau` | what the values do: look speed, the sound groups, graphics, the HUD's size, the FPS readout, the enemy outline |
| `client/SettingsUI.luau` | the page: tabs down the left, rows on the right |
| `client_root/JankSettings.client.luau` | the ScreenGui, the reminder in the top right corner, P opens and closes it (attribute `SettingsOpen`) |
| `server/SettingsServer.server.luau` | keeps the values per player: store `JankfireSettings_v1` through `Profiles.luau` (session-locked like loot, flair and stats) |

Only the values that differ from the defaults are saved, as `key = number / boolean / short string` (at most 200
keys). Changes save 1.5 s after the last one and when the page closes. Everything applies at once; nothing needs a
respawn. In Studio without API access the save runs in memory and the page's foot says KEPT FOR THIS SESSION.

## The tabs

- **CONTROLS.** Look speed (`look.sens`, Roblox's `MouseDeltaSensitivity`), up and down speed, invert, AIMING,
  SNIPER SCOPE and SECOND OPINION SCOPE multipliers, controller look speed, field of view, screen shake, and hold or
  toggle for aim, crouch and sprint.
- **KEYBINDS.** Every action with KEYBOARD, SECOND KEY and CONTROLLER columns. Click a cap, press the new key.
  Backspace clears it, Esc keeps it, a click on the flashing cap binds the left mouse button. A key that another action
  had swaps over (that action takes this one's old key). Move, jump and look are Roblox's own and shown greyed.
- **CROSSHAIR.** A live preview at true size on a dark and a pale ground, four starting points (DEFAULT, DOT, SMALL
  CROSS, CIRCLE), style (cross, dot, circle, T), colour (six swatches or any #RRGGBB), length, thickness, gap, outline,
  centre dot, opacity, show spread, hide while aiming, and the share code.
- **AUDIO.** Master, weapons, effects and interface, 0 to 150 %, and the hit and kill sounds on or off.
- **GRAPHICS.** Quality AUTO / LOW / MEDIUM / HIGH (AUTO follows Roblox's own graphics level), shadows, particles,
  bloom and sun rays, colour grading, view distance, other players' kill effects and skin effects, FPS counter.
- **HUD.** HUD size, damage numbers, hit markers, kill feed, key hints, other players' crate openings, colour-blind
  mode (team colours), enemy outline colour.
- **PRIVACY.** HIDE MY STATS (Stats.luau keeps it) and SHOW MY OPENINGS (Loot.luau keeps it). The old
  `LootSettings.client` row lives here now.
- **TOUCH** (phones and tablets): touch look speed, button size (on top of the size that suits the device), button
  opacity, aim help, auto fire, aim button toggles, left-handed. TouchControls (the touch session's) reads them and
  turns the camera itself; a touch button's press is always a hold in `Binds.press` (TouchControls runs its own
  toggles). More rows can come from `Settings.row("touch", ...)`.

Every tab has RESET TAB (click twice).

## How the look speed works

The web game turns `0.0022 * sens * adsSens / zoom` while aiming (`main.js`). Here the zoom part follows the sights
coming up (the view narrows by `1 + (zoom - 1) * aim`) and the multiplier blends in with them:

    turn = look.sens * (1 + (m - 1) * aim) / (1 + (zoom - 1) * aim)

`m` is `look.sniper` with the Sniper (zoom 4), `look.dmr` with the Second Opinion (zoom 2.6), else `look.ads`. So at
1.00x a mouse move moves the view as far across the screen at every zoom as at the hip. Rivals has one scoped
multiplier at 50 % with no zoom matching; we keep the web game's matching and give each scope its own.

- The mouse goes through `UserInputService.MouseDeltaSensitivity`, which both Roblox's camera and the shoulder camera
  read (set every frame at `RenderPriority.Camera - 2`).
- A controller and a touch screen go through Roblox's camera input: `SettingsApply` wraps
  `PlayerModule.CameraModule.CameraInput.getRotation` and scales its turn by `look.pad` / `touch.sens` and the same aim
  factor. The up-down part is scaled by `look.ySpeed` and flipped by `look.invert` there too.
- The shoulder camera reads the player attribute `LookY` (up-down speed, -1 = inverted).

## Hooks in other scripts

Small, each one line or a few:

- **Arsenal:** `Binds.is` for fire, aim, reload, slots and next weapon, `Binds.press` for toggle aim, `H.step` gets
  the weapon and its spread, screen shake off, others' blade flames off.
- **FightHud:** the crosshair is `Crosshair.draw`; hit markers, damage numbers and the feed check their switches;
  the match line's team colours go through `Settings.cbText`; the controls line names the bound keys.
- **Move:** sprint, crouch, grapple and camera through `Binds`.
- **CrouchPoses, ThirdPerson:** the crouch is `Binds.on("crouch")` (held or toggled).
- **Hud** (H, team colours), **Utility** (G, N), **ShopClient** (B), **PlayClient** (J, M), **ProfileClient** (K),
  **LoadoutUI** (L), **ShredderSlot** (4), **FlairClient** (T, the flair session's own `BindsMod` hook).
- **Theme:** `T.hudScale` and `T.rescaled` (HUD SIZE). **Sfx:** `Sfx.mute`. **Fx:** `Fx.density` scales bursts.
  **ZoneCull:** attribute `Margin` (VIEW DISTANCE). **ShoulderCam:** attribute `LookY`. **LootShow:** others' openings.

The phone's buttons (`Keys.luau`, TouchControls) press an action's default key as a pretend input (`io.Touch`).
`Binds.is` matches those against the defaults, so a player's own keyboard binds never break a touch button.

## Sound groups

`SoundService.JankMaster` (MASTER) holds `Weapons`, `Effects` and `Interface`. Library sounds get their group by name
(`gun_*`, `draw_*`, handling, blades, hits and kills are WEAPONS; `loot_*`, `round_*` and `ui_*` are INTERFACE; the
rest is EFFECTS). Any other Sound that turns up without a group goes to EFFECTS, or to INTERFACE inside the screen
gui. There is no music or voice in the game yet, so there are no sliders for them.

## Graphics

- Presets: LOW = no shadows, 35 % particles, no bloom, near view; MEDIUM = shadows, 70 %, bloom, normal; HIGH = the
  game as it was (shadows, 100 %, bloom, normal view). FAR view is a choice of its own: ZoneCull's near-only drawing is
  what keeps the frame rate up. Touching a switch under the preset makes it CUSTOM.
- An off switch holds its property off even when a zone's look (HubLook) changes it, and gives back what the look
  last wanted when it is turned on again. Effects named `Jank*` (the goggles' night vision) are left alone.
- Particles: `Fx.density` scales Fx's bursts; emitters that run on their own have their Rate scaled (only below
  100 %). KillFx reads `gfx.particles` itself.

## Crosshair codes

`X1` + style letter (C cross, D dot, O circle, T) + colour hex + seven base-36 digits: length, thickness, gap,
outline, centre dot, opacity in tenths, flags (1 show spread, 2 hide while aiming). 16 letters and numbers, nothing
else (no links). The default is `X1CFFFFFF82510A2`.

## Testing

Studio only: the player attribute `SettingsTest` drives it (`"set:look.sniper=0.5"`, `"reset:xh."`, `"tab:audio"`,
`"dump"`; add `#n` to repeat one), `SettingsDump` reads back the values as JSON, `SettingsOpen = true` opens the page,
`SettingsAllTabs = true` shows the TOUCH tab on a desktop. Rows are named `Row_<key>` (dots as `_`), key rows
`Key_<action>` with caps `Cap1`..`Cap3`, pills `Pill_<value>`, swatches `Swatch_<value>`, so a test can click them by
path.
