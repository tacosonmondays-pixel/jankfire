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

The owner, 17 Nov, after the first version: "I don't like the names of it though, can they be like csgo settings?
Default names". So every label is the plain name competitive shooters use (keys and saved values unchanged, so no
player loses a setting).

- **CONTROLS.** SENSITIVITY (`look.sens`, Roblox's `MouseDeltaSensitivity`), VERTICAL SENSITIVITY (`look.ySpeed`),
  INVERT MOUSE Y, ZOOM SENSITIVITY RATIO (`look.ads`, sights and red dots), SCOPED SENSITIVITY for the Sniper
  (`look.sniper`) and the Marksman Rifle (`look.dmr`), CONTROLLER SENSITIVITY, FIELD OF VIEW, FOV KICK (`fov.kick`), VISUAL RECOIL (`gfx.recoil`: the gun's tilt and view punch only, Arsenal),
  SCREEN SHAKE, and hold or toggle for AIM DOWN SIGHTS, CROUCH and SPRINT.
- **KEYBINDS.** Every action with KEY, ALTERNATE and CONTROLLER columns: FIRE, AIM DOWN SIGHTS, RELOAD, PRIMARY /
  SECONDARY / MELEE / SPECIAL WEAPON, NEXT WEAPON, UTILITY, UTILITY ALT, SPRINT, CROUCH, GRAPPLE, TOGGLE THIRD PERSON,
  EMOTE WHEEL, the menus, SHOW KEY HINTS and QUICK JOIN (F, the hub pad pop-up). Click a cap, press the new key.
  Backspace clears it, Esc cancels, a click on the flashing cap binds the left mouse button. A key that another
  action had swaps over. MOVE FORWARD / BACK / LEFT / RIGHT and JUMP are Roblox's own and shown greyed.
- **CROSSHAIR.** A true-size PREVIEW on a dark and a pale ground, four starting points (DEFAULT, DOT, SMALL CROSS,
  CIRCLE), STYLE (cross, dot, circle, T), COLOR (six swatches or any #RRGGBB), SIZE, THICKNESS, GAP, OUTLINE, DOT,
  ALPHA, DYNAMIC (the gap follows the spread), HIDE WHILE AIMING and the CROSSHAIR CODE.
  - WEAPON RETICLES (`xh.weapon`, default on, since 21 Nov; owner: "special reticles like shotgun can have a circle
    crosshair depending on the spread of it"): each kind of weapon gets a reticle from its own numbers in Weapons.luau,
    read live (`Crosshair.luau`, `XH.class` / `XH.drawFor`). The player's colour, outline, opacity, thickness and dot
    apply to all of them. Off: the player's own crosshair on every weapon.
    - Shotguns (more than one pellet): a circle on the pellet cone. Every pellet lands inside its line, at any FOV or
      zoom. It shrinks down the sights (`ads.spread`) and stays up there, half faded.
    - Automatics: the player's own crosshair, its gap always opening with spread + bloom.
    - Precision guns (pistols, revolver, lever rifle): a dot and four short ticks just outside the cone. The revolver's
      fan opens them shot by shot.
    - Scoped guns from the hip: a dot and a faint ring on the hip spread.
    - Launchers, throws, the bow: a dot and short marks under it where the shot has dropped at 30, 60 and 90 studs.
    - The leaf blower, hot sauce, taser and TV remote: a faint ring on the cone they reach.
    - Melee and the rest: a small dot.
    - The spread maths: Hitbox.spreadDir puts a shot up to `spread` across the look (a tangent), so the cone's radius is
      `spread / tan(FOV / 2) x half the screen height` (`XH.spreadPx`).
    - Sheet: `settings/weapon-reticles-sheet.jpg` (every class drawn by the real code, and the shotgun circle with real
      pellet holes inside it, from the hip and down the sights).
- **AUDIO.** MASTER, WEAPON, EFFECTS, UI and MUSIC VOLUME (0 to 150 %), HIT SOUND, KILL SOUND and OTHERS' EMOTE MUSIC.
  - MUSIC (`vol.music`, the `Music` group, since 19 Nov, the flair session's) is the dance emotes' licensed tracks, played
    from the dancer (`client/EmoteMusic.client.luau`).
  - OTHERS' EMOTE MUSIC (`snd.emoteMusic`, default on) turns other players' emote music off. Your own still plays.
  - There is no voice audio anywhere.
- **GRAPHICS.** GRAPHICS QUALITY AUTO / LOW / MEDIUM / HIGH (AUTO follows Roblox's own level), SHADOWS, PARTICLE DETAIL,
  BLOOM, COLOR CORRECTION, SPEED LINES (`gfx.speedLines`: streaks, wind and its sound, SpeedLines.client), RENDER
  DISTANCE (ZoneCull), OTHER PLAYERS' KILL EFFECTS, SHOW TITLES (`gfx.titles`, OverheadTitles.client), OTHER
  PLAYERS' SKIN EFFECTS, OTHER PLAYERS' FINISHERS (`gfx.othersFinisher`, FinisherClient: off skips finishers you only
  watch), SHOW FPS (and ping). No motion blur: the game has none.
- **HUD.** HUD SCALE, DAMAGE NUMBERS, HIT MARKERS, KILL FEED, SHOW KEY HINTS, OTHER PLAYERS' CRATE OPENINGS, QUICK
  JOIN POP-UPS (`hud.quickJoin`, QuickJoinUI), COLORBLIND MODE (team colors), ENEMY HIGHLIGHT COLOR.
- **PRIVACY.** HIDE MY STATS (Stats.luau keeps it) and SHARE MY CRATE OPENINGS (Loot.luau keeps it). The old
  `LootSettings.client` row lives here now.
- **TOUCH** (phones and tablets, or whenever TouchControls' layout is on: `TouchOn`): TOUCH SENSITIVITY, BUTTON
  SIZE (on top of the device's own size), AIM ASSIST, BUTTON OPACITY, AUTO FIRE, TOGGLE AIM DOWN SIGHTS, LEFT-HANDED
  LAYOUT. TouchControls (the touch session's) reads them and turns the camera itself; a touch button's press is always
  a hold in `Binds.press` (TouchControls runs its own toggles). More rows can come from `Settings.row("touch", ...)`.
- **CREDITS** (since 19 Nov): the creators whose packs are in the game, as their licences ask ("with attribution").
  Section titles and plain lines, nothing to click, read from `shared/Credits.luau` (`Credits.SECTIONS`). A session
  that brings in outside work adds its line there, as "<what>: <creator> (<pack>)"; the page needs no change.
  Photo: `settings/settings-credits-tab.jpg`.

Every tab but CREDITS has RESET TO DEFAULT (click twice).

## How the look speed works

The web game turns `0.0022 * sens * adsSens / zoom` while aiming (`main.js`). Here the zoom part follows the sights
coming up (the view narrows by `1 + (zoom - 1) * aim`) and the multiplier blends in with them:

    turn = look.sens * (1 + (m - 1) * aim) / (1 + (zoom - 1) * aim)

`m` is `look.sniper` with the Sniper (zoom 4), `look.dmr` with the Marksman Rifle (zoom 2.6), else `look.ads`. So at
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
(`gun_*`, `draw_*`, `skin_*` (special skins' shot and reload layers), handling, blades, hits and kills are WEAPONS; `loot_*`, `round_*` and `ui_*` are INTERFACE; the
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

## The hub's menu stack and HUD (18 Nov, place version 1020)

The owner: "M play should be at the top of the menus on the left in the main hub; holstered weapon and hp and m/s
should not be visible".

- **Order:** `client/HubStack.luau` holds the left-hand stack's order, top to bottom: PLAY, QUESTS, PARTY, PROFILE,
  SHOP, LOADOUT. Each button's script asks `HubStack.pos(id)` for its spot (8 px gaps, ending just over the health
  plate), so a new button or a new order is one line there.
  - The phone layout (TouchControls moves the same buttons to the right) follows the positions.
  - So does a controller (PadNav sorts the column by height).
  - Phones' saved layouts (`tl<n>.<id>`) don't hold these buttons, so nothing old overrides the order.
- **Hub HUD:** in the `hub` zone (the player's `Zone` attribute, from `Matches.zoneOf`), FightHud hides the health
  plate and the weapon card, and Hud hides the m/s plate.
  - All three are back in training, the playground, a map room (`staging`) and a match.
  - They also show while the owner's dev weapons are out (`DevArms`), as Arsenal arms you then.

Sheet: `settings/hub-menu-order-before-after.jpg` (the old layout in the hub; the new one in the hub, in training, and on
a phone-sized screen in the hub).
