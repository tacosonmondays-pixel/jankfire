# UI mocks: three art directions (21-26 Nov 2026)

The owner, 21 Nov 2026: "Let's get some new ui mocks!! The current one screams ai!!"

The owner, 25 Nov: "We need a better ui that doesnt look like ai! I also dont want it to look like
roblox slop games", with 15 reference pictures (vault) and the openvector link. Research: vault
`Research/UI resources (26 Nov) - index.md`.

These are design mocks for the owner to pick from. Nothing in the game has changed. Each direction
mocks the same six screens: the hub HUD with the menu, the in-match HUD, the loadout, the shop home,
the in-match HUD on a phone, and the held-Tab scoreboard. Every round is judged by the owner's
anti-AI player critic (a fresh agent per direction, PNGs only), logged in vault
`Reviews/UI mocks - anti-AI critic round N.md`; scores are in `verdicts.json`. All are built in HTML/CSS with our own SVG icons and
rendered with headless Chrome, so every size, colour and font can be copied straight into Roblox.

- Comparison sheet (today plus A, B and D, screen by screen): `sheets/ui_mocks_directions.jpg`
  (also in the side-session notes folder as `ui_mocks_directions.jpg`)
- One board per direction, with its rationale: `sheets/ui_mocks_<A..D>_*.jpg`
- Frames: `png/<a|b|d>_<hub|match|loadout|shop|phone|scoreboard>.png` (1920x1080; phone 844x390 at 2x)
- Source: `mocks.py` (renders), `common.py` (fonts, icons, the game's real labels), `dir_a.py`, `dir_b.py`,
  `dir_d.py` (one file per direction), `prep_images.py` (pictures), `sheet.py` (the sheets)

## 1. What reads as "AI" in today's UI

Looked at: the hub HUD and left menu (`docs/settings/hub-menu-order-before-after.jpg`, the three
hubs sheet), the in-match HUD and end screen (team-colours frames), the loadout and armory
(`docs/shop/loadout-skins-after.jpg`, `match-loadout-picker.jpg`), the shop, containers and the
opening (`docs/shop/shop-sheet.jpg`, `shop-deals.jpg`, `docs/loot/loot-sheet.jpg`), settings
(`docs/settings/settings-tabs-sheet.jpg`), the player card (`docs/profiles/profiles-sheet.jpg`),
quests (`docs/quests/`) and the phone HUD (`docs/touch/phone-hud-after-v957.jpg`).

1. **One panel recipe for everything.** HP, m/s, the weapon card, the score bar, loadout cards,
   quests, settings rows, shop cards, the end screen and the player card are all the same near-black
   rounded box at about 90% opacity, same radius, same 1 px lighter edge. A readout, a button and a
   whole screen look like the same object, so nothing has a role.
2. **Keycap chips on everything.** "M PLAY", "U QUESTS", "J PARTY", "P settings", "L LOADOUT",
   "G Frag Grenade", "DONE [L]", "READY [Space]", "EQUIP IT · KEY 1", "CLOSE B". The key is often
   louder than the label.
3. **A tiny grey caps label over every value.** PRIMARY / SECONDARY / MELEE / UTILITY, HP, m/s,
   K/D, WIN RATE, ROUNDS WON, "SAVED TO YOUR ACCOUNT", "P TO CLOSE". The two-tier label-and-value of
   a dashboard template, at sizes a phone can't read.
4. **One stock yellow for every "primary" thing:** CLAIM, EQUIP, PLAY, switches, selected tabs,
   progress fills, YOU WIN. It now competes with the pastel team colours: two accent systems at once.
5. **The thin coloured stripe down the left edge** of the weapon card, the utility card, the
   end-screen row, the player card's loadout tiles and the armory tiles: a very common generated tell.
6. **Equal grids with no focal point.** The shop is rows of identical cards with identical yellow
   buttons; quests are three identical cards; the player card is six identical stat tiles; the
   loadout bar is four identical cards; in the hub menu PLAY is the same size as SHOP.
7. **A centred modal over the game for everything** (end screen, quests, settings, loadout picker)
   instead of screens that own the space.
8. **One default font at three sizes** (Gotham-style bold caps), no display face, and the JANKFIRE
   wordmark nowhere in the UI. Nothing says this game.
9. **Filler copy in a lowercase whisper:** "four slots. choose violence.", "the honest gun.
   somebody has to be.", "picks go in your hands now", "Free while we test. The prices are for
   later." It breaks the no-flavour rule and reads like generated microcopy.
10. **Thin 2-3 px lines everywhere** (XP, HP, the loadout timer, the end-screen countdown) and grey
    text on charcoal.
11. **Wide empty boxes:** the score bar is a 460 px box for "1v1 ROUND 1 0-0", and "0 m/s" gets a box
    of the same weight as HP.

## 2. Research (kind of thing, never the look)

Vault notes read: `References/UI/*` (the 19 Nov Rivals screens and their "Ideas for JANKFIRE" list),
`shop-home`, `settings-audio-menu`, `loadout-grid-mobile`, `loadout-workbench-dark`,
`weapon-inspect-screen`, `wrap-picker-strip`, `season-pass-track`, `player-card-popup`,
`lobby-spawn-with-hud`, `Research/Shop GUIs.md`, `Research/Rivals settings.md`.

What polished shooters do that ours doesn't, taken as principles only:
- one clear focal point per screen (the gun on the weapon page, PLAY in the lobby, the score in a match);
- the item is the picture: the loadout and shop lead with big renders, text is secondary;
- type with character and real size contrast (a display face, numbers you read at a glance);
- a motif that belongs to the game, repeated (shape, edge treatment, icon family);
- few colours, each with a job; prices in two currencies get two looks;
- deliberate asymmetry: menus anchored to one side, the world left open.

Nothing below copies another game's layout, art or wording. Self-check per frame: could this be
mistaken for another game's screen? Rivals (white stroked text, a green Play, a dock of 3D icons),
Valorant (red, thin tech lines), Fortnite (blue-violet, heavy italics) and CoD (military) were the
ones checked against.

## 3. The directions

Common to all directions:
- Roblox fonts only, with tabular figures.
- The owner's pastels as the only team colours (Blossom #f4a7c8, Sky #a3cbf2, Butter #f5dd8a, Mint #a6e3c4).
- A quiet base with one accent.
- Real labels only: weapon names, modes, prices. No jokes and no slogans.
- **One icon family: solid silhouettes at the guns' weight**, with no strokes and no inner lines:
  - the guns, the katana and the frag grenade are silhouettes of our own models;
  - the HOOK (E) is a crane hook on its rope, never an anchor;
  - Reload is a magazine with a round at its lips;
  - Jump and Slide are the blocky Roblox body;
  - the lock and the Robux mark are solid.
- **Our own coin and crate-ticket marks:** a gold coin with a square hole and a notched ticket, drawn flat. The game's star coin read as simulator clipart, and at HUD size it blurred into a dot.
- No decorative dots, status lights or "A · B · C" meta lines.
- **The grapple's charges** show in every match HUD and on the phone's hook key as one readout (the hook and "×2"): it is the game's own mechanic.
- **The score** carries each side's players inside its own team block, with the dead ones crossed out (they agree with the kill feed). It is not laid out like Valorant's bar (heads either side of the score and the timer).
- **The phone** puts its action keys on a thumb arc round Fire, with a grenade key and no text labels. There is no menu icon: the score is the scoreboard button, with a "Scores" pull tab under it.
- **The scoreboard** shows avatar headshots (blocky placeholders here for the players' real Roblox thumbnails) and marks dead players.
- **Honest states:** prices you can't afford are muted ("need 2,550 more"), a gun above your level shows its lock level, your own kill-feed row is outlined, and the loadout preview wears its hat.
- **The shop hero is a skin set** (SERAPH: five skins, R$3,300 = the sum of its skins). It is not VIP, which the mock player already owns. The five skins are laid out flat together at their true relative sizes, with the name, a skin count and the price. There is no kicker, paragraph, thumbnail strip or small print: critics read those as a website header.
- **Coin packs are plain rows** with the game's own coin. The pile, sack and chest art reads as a simulator store.
- **Rarity is a word** in the line's own colour. The blue, purple and gold ladder reads as Fortnite's; the loot opening keeps the game's rarity colours.
- **A party is a labelled bracket** beside its rows on the scoreboard, not a pill.
- Only PLAY shows its key; the rest show while the key-hint key is held, as today.
- The top-left corner stays clear for Roblox's own buttons.

### A. PLATE: made of the same parts as the world
The UI is built from the hub's own kit, light on the game. Panels are flat and near-square (3 px). Only what you buy is a rounded plate with the queue pads' lip.
- **PLAY** is a flat ink block with the stencil-cut PLAY, the mode and rating under it, and a flat CHANGE MODE plate. Its text sits on the page's 62 px axis.
- **The set's own mark** is a stencil slit through every hero number (PLAY, HP, ammo, scores, SERAPH). In Roblox it is a UIGradient transparency band.
- **The score:** one flat rounded tile per team on the HUD, phone and board, with that team's players inside. Round and clock sit on a tab below.
- **The match HUD:** unframed numbers, the HOOK with its key (E ×2), and slot silhouettes on dark backings.
- **The loadout:** keyed rows 1/2/3/G/E, a stat panel with the secondary-average tick, and a secondaries rail. In the rail, the equipped card shows its skin, owned guns show their mastery, and locked guns are dimmed whole.
- **The shop:**
  - a tall SERAPH card with the set stacked down it;
  - the daily pick breaking out of its card;
  - wrap rows with "need X more";
  - crate prices in tickets or Robux, each its own button;
  - coin packs as plain rows.
- **Leaving a screen** is the word plus its key (CLOSE ESC, DONE ESC).
- **Type has two registers:** ExtraBold caps for names and numbers, Medium sentence case for anything said.

Why it won't read as AI:
- the radius itself means something (rounded with a lip = you can buy it), taken from our own pads;
- light on the game, a deliberate and unusual choice;
- the stencil cut appears only on hero numbers;
- one action colour (ink), with colour only for team or rarity;
- numbers that add up across screens.

Risk: the loudest on screen; light panels on the brightest arenas need the soft shade behind them.

### B. BROADCAST: your match as a sports graphic
Hard square black slabs.
- **Two marks, each with one meaning:** a skew means "press" (PLAY, DONE, a price you can afford, the active tab and slot); a cut corner means "you or selected" (your kill row, your board row, the selected loadout row, the equipped card, your team's score cell).
- **Type:** condensed Oswald for names and big numbers; Builder Sans ExtraBold caps for the nav, tabs and labels; Builder Sans sentence case for everything small.
- **The hub:** a name, level and XP strip, PROFILE and SETTINGS beside it, a Butter PLAY slab carrying the mode, your rating and your party, the nav bar, and a live ticker of every queue with CHANGE HUB on the hub's own tab.
- **The match HUD:**
  - a broadcast score bug: a round tab, the two team cells with their players inside, then the clock;
  - HP and ammo as bare numbers on a rule;
  - the hook as an E slot in the hotbar.
- **The shop:**
  - the SERAPH rifle large and angled, with the other four laid out beside it over the hub it belongs to;
  - the daily list and crates as running orders;
  - coin packs as base + bonus.
- **Colour:** black and white, plus the team pastels as solid score cells. Butter marks only what you can press now.

Why it won't read as AI:
- zero radius, with two marks that each mean one thing: a hard system of its own instead of soft cards;
- big numbers are the focal point, with no labels on things you can already see;
- the menu and ticker carry live information, not just buttons;
- one accent with one meaning (press this).

Risk: the most "esports" of the three; critics keep calling it a Valorant/CoD composite.

### C. OPEN (dropped after critic round 2)
Type straight on the world with no boxes, one huge word per screen. Dropped after round 2: its
critic named the no-container "editorial blur" look an AI default of its own, and it had the
weakest legibility of the four from round 0. Its frames are kept in the vault review notes.

### D. SIGNAL: the hubs' wayfinding signs
The hubs are stations, concourses and hotels, so the menus talk like their signs: deep green enamel, sentence case in Titillium Web, and platform badges for keys. No rims anywhere.
- **The wayfinding arrow is the one shape.** It marks what's chosen or next:
  - Play, Buy and Done are Butter arrows;
  - the selected loadout slot points at the gun;
  - the chosen shop tab points down at the page;
  - the featured set's sign ends in an arrow;
  - a "you are here" arrow marks your team in the score and your row on the board.
- **Mounting:** nothing floats. Every sign hangs from the top edge, stands on the bottom edge, or sticks out of a side wall.
- **The hub:** one sign named after the hub (Change hub beside the name), the Play arrow with a mode selector under it, then Quests, Party, Loadout and Shop rows. Each row is one height, a label over its live state: the next quest, who's in your party, your guns, the daily reset and your wallet.
- **The match HUD:** two registers. Only the score hangs as a sign (two lines, each team's tile with its players); HP, ammo and the slots are bare type with small backings.
- **The loadout:** five gates (1/2/3/G/E), the armory as a departures board, and one base strip across the foot holding the stats and cosmetics.
- **The shop:**
  - the featured set's sign;
  - a daily list showing each wrap close up on its pattern;
  - crates and coins as rows on a band along the bottom.
- **Colour:** Butter only on the next thing to press.

Why it won't read as AI:
- a real-world sign system with its own rules (edge-mounted, platform badges, the wayfinding arrow);
- sentence case: the only direction that isn't all caps;
- signs for menus and bare type for the fight: the two registers a real game keeps;
- the departures board gives the loadout a structure of its own.

Risk: green enamel next to the pastel teams is the boldest colour choice of the three; it needs the hubs' signs to match.

## The critic loop: where it stands

Eleven rounds (0-10) have been logged in `verdicts.json` and the vault (`Reviews/UI mocks - anti-AI critic round N.md`). All three directions climbed to 7 by round 3, and no critic has given 8 since. Round 10 scored A 7, B 7 and D 7. From round 6 on, each fresh critic mostly reverses the last one's asks, so another round would only trade one set of tells for another. The owner picking one direction is the better next step.

**What the critics agree on, every round:**
- Numbers that reconcile across screens are the strongest human signal. Examples: kills against deaths, round against score, every "need X more", the coin-pack rate, the XP and mastery fills.
- The stat bars' "secondary average" tick reads as a designer's idea.
- No decorative lights and no slogans.
- Every screen should agree with every other one: the same score tile, the same dead marker, the same icon family, and the same party and mode data.
- Small icons must be solid silhouettes at the guns' weight. Stroked or hairline glyphs read as Lucide or Material.

**Where the critics reverse each other from round to round, so the mocks hold one line on purpose:**
- **Coin art.** Piles were called "simulator", then wanted back, then called simulator again. The mocks hold: no art, written as base + bonus.
- **Rarity colour.** "Fortnite's ladder", then "every real shop colours rarity", then "Fortnite's" again. The mocks hold: our own muted ladder (steel, terracotta, brass), on the word and the tile edge only. This is a proposal; the game's loot colours are unchanged.
- **Row arrows and the phone stick shape.** Each was asked for and then against.
- **Prices are the real ones** from `roblox/docs/MONEY.md`. Critics flag R$4,500 for breaking the x99 pattern; that is the owner's price.

**Structures every critic still names:** Valorant's top bar and Tab board, Fortnite's yellow PLAY and item shop. These are genre conventions players expect. The mocks take them apart where they can (heads inside the team tiles, the set shown whole, the hub ticker) but don't throw out what players expect.

## 4. Building one in Roblox later

The stack (research: vault `Research/UI resources 26 Nov - Roblox libraries and pipelines.md`):
- No framework rewrite. Roblox's own UI Styling: tokens, themes and tag rules live since Jan 2026.
  One `Theme.luau` builds the stylesheet in code, so every screen takes the chosen direction from it.
- Native pieces:
  - UIShadow for soft depth;
  - per-corner UICorner (D's edge-mounted signs);
  - inner and scaled UIStroke (A's rim, D's keyline);
  - UIGradient for C's edge shade.
- Item and gun icons pre-rendered from our Blender models. The selected item gets one live ViewportFrame.
- Our icon family is exported to PNG and uploaded through Open Cloud (Asphalt, MIT). openvector (MIT)
  can trace Blender silhouettes into clean vectors first.
- spr (MIT) for spring motion. UI Labs or Flipbook to preview screens in Edit.
- A blur and slight desaturation behind menus, and a sound on every press.
- Fonts: `Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.ExtraBold)`, and
  likewise `BuilderMono.json`, `BuilderExtended.json`, `Oswald.json`, `TitilliumWeb.json`.
  - All ship with Roblox; Roblox can't import fonts.
  - The render copies them from the local install into `fonts/`, which is not in git.
- A: a plate is a Frame (UICorner 18) over a second Frame 5 px lower in the lip colour. Only pressable
  plates get the lip.
- B: Frames with no UICorner at 8% transparency. The tabs are their own Frames, and the ticker is a
  tweened row.
- C: TextLabels only, with a UIStroke at 70-80% transparency for the shadow. The edge shade is one
  Frame with a UIGradient.
- D: per-corner UICorner, so a sign mounted on an edge keeps its outer corners square. The keyline
  is an inner UIStroke.
- Price glyphs: "R$" here stands in for Roblox's own Robux glyph (`utf8.char(0xE002)` in game).
- Avatar heads on the scoreboard stand in for `Players:GetUserThumbnailAsync` headshots.

Placeholders, all mock values:
- player names;
- the level, XP and wallet;
- daily prices and level locks;
- the quests' rewards.

Container, coin pack and VIP prices come from `docs/MONEY.md`. Pictures are our own renders and
Studio captures (HUD hidden, 21 Nov), keyed by `prep_images.py`.

## 5. The owner's picks, built in the game (27 Nov 2026)

The owner marked the directions sheet (side-session-notes `ui_mocks_OWNER_PICKS_27nov.webp`, kept outside git):

| screen | built as | where the code is |
|---|---|---|
| hub menu | A PLATE: PLAY an ink block with the slit through the word; QUESTS, PARTY, LOADOUT, SHOP as white words on the world; HUBS, PROFILE smaller; bone key caps | `client/HubStack.luau` (`HubStack.style`, the order and sizes); one `style` call in each button's script |
| match HUD | A PLATE: health and ammo bare on the world with the slit; the score as a pastel tile per side with its players' heads, the round and clock on an ink tab; the kill feed on dark backings, names in their side's colour | `client/FightHud.luau` |
| loadout | A's layout in B's colours (the owner's arrow, "with this color"): slot rows down the left, the chosen one white with a cut corner; the preview in the middle; the weapon's card on the right with the slot-average ticks; the armory and the looks along the bottom on tabs; DONE and EQUIP as Butter skews | `client/LoadoutUI.client.luau` |
| Tab scoreboard | B BROADCAST: the score bug (round on a skew tab, each side's score on its colour, the clock), the map, then each side as a black table; your row white with a cut corner, your party in a Butter bracket, a player who is down greyed and struck through | `client/ScoreboardUI.luau` |
| shop | A PLATE's colours: bone panels and cards, ink words and buttons, 3 px corners | `client/ShopUI.luau` (its `T` is `UiKit.themeA()`) |
| phone | A PLATE: bone discs with ink words, FIRE an ink disc with a bone rim, the stick a bone ring and knob | `client/TouchControls.client.luau` (`style`) |

The parts both looks are built from are in `client/UiKit.luau`: the palettes (`K.A`, `K.B`), the triangle (a hard
UIGradient step, so no images and no rotation), the cut corner, the skew, A's slit (a transparency band), the hero number
(a number with a soft shadow, slit) and `K.themeA()` (Theme in A's colours for a light menu).

The hub's other menus (the Play screen, the map vote, party, quests, the leaderboard, the modes tab, the profile) take
`UiKit.themeA()` too, one line each. Settings stays as it was for now: its side rail is drawn dark in its own code.

**How it went in:** one guarded push per Studio turn (scratchpad tools, not in git): every edit is an exact old/new pair
that must match once in Studio's current source, and every script is compiled inside a function wrapper before it is
written; a script that fails either check is left alone. The patcher travels as a Model uploaded through Open Cloud.

**The critic, in the game** (vault `Reviews/UI build - anti-AI critic in-game round N.md`, a fresh critic each round,
judging Play captures only):

| round | score | what it said |
|---|---|---|
| 1 (v1413) | 5 | the structure reads real (menu hierarchy, loadout layout, the Tab table); overlaps, unlabelled marks, three icon styles in the loadout, the shop's top row unreadable, numbers that don't add up |
| 2 (v1426) | 6 | the fixes held; "two design systems" (the A+B mix) is now its first point |
| 3 (not saved) | 6 | the loadout and Tab board "would pass"; the A+B mix again |
| 4 (v1437) | 7 | one icon family missing (shaded coin, emoji padlock), collisions, orphans |
| all-B (v1441) | 6 | the A screens in B's colours, on one switch (`ReplicatedStorage` attribute `UiLook` = "B"): bare words on a light floor and dark phone buttons scored lower. The owner's picks stay the main look; both are on side-session-notes `ui_build_picks_vs_allB.jpg` |
| 5 (v1451) | 6 | contrast, phone overlaps, mixed fonts |
| 6 (v1456) | 6.5 | told "the direction is the owner's": key cap families, contradictory states, right edges, test data |
| 7 (v1464) | 7 | data adds up; the Tab board "the best screen" |
| 8 (v1477) | 7 | "every number I checked adds up"; alignment and contrast slips |
| 9 (v1488, 4a2715e) | 7 | "the PC loadout, shop and Tab board would pass as shipped work"; the phone buttons, the picker's mixed type, the score-bar seam |
| final (v1501, bac7013) | 7 | with the phone glyphs; found the phone hub stack off the bottom of a 390-point phone and over the crosshair (fixed in v1510, 8e9a5f9) |

**The loop stopped at a steady 7** (main's call): the last critics reversed each other ("need 12" wanted, then called a
repeat; a your-side bar asked for, then called an unlabelled mark). What they still name goes against the owner's picks
(the PLAY slab's face, the hub menu bare on the world, the HUD score and the Tab header as two designs), or is the
shop's own content.

**The phone's glyphs** (v1501/v1510): `tools/roblox/touch_glyphs.py` draws one family of 20 flat white glyphs on one
sprite sheet (no text or digits: the upload rules), uploaded once as an Image (v2: 79409184361495); `client/TouchGlyphs.luau`
puts each on its button, tinted like the button's words, the word under it (a pill: the word after it; SETTINGS a gear
alone). On a phone the hub stack drops 30 (not 76) and PLAY is 210 wide, checked in 844x390 and 780x360 boxes.

**Final screens:** side-session-notes `ui_build_final.jpg` (PC hub, loadout, shop, picker, live HUD, Tab board; the
phone in a match, and the phone hub at 390 and 360 points tall).

## 6. Rebuild the mocks

```
python prep_images.py <folder with hub_spawn.jpg, hub_rotunda.jpg, match_crate.jpg, match_forest.jpg>
python mocks.py            # all four, or: python mocks.py a c --frames=hub,shop
python sheet.py            # comparison sheet + one board per direction
```
