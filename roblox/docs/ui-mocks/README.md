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
- **Our own icon family.** Solid shapes in the weight of the gun silhouettes:
  - a grapple head for Hook;
  - a magazine for Reload;
  - a scope for Aim;
  - a cartridge for Fire;
  - blocky-body poses for Jump and Slide;
  - a frag grenade and a square-toothed gear;
  - Stab and Swap made from our own gun renders.
- The game's own gold coin and crate-ticket art.
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
The UI is built from the hub's own kit. One rule: only things you can press are plates. They are
bone-white, with the queue pads' thick lip. Everything you only read is type straight on the
world over a soft shade, or a flat panel with no lip.
- **PLAY** is the one big pad: ink, with the pads' cream rim and a CHANGE MODE plate attached to its side.
- **Panels are flat and near-square (3 px).** Only pressable things are rounded with a lip, so the radius itself says "press".
- **The secondaries** are a rail: the chosen gun's card is wider, locked guns show their level, guns you can't afford show what's missing.
- **The set's own mark** is a stencil slit through the big numbers and PLAY. In Roblox it is a UIGradient transparency band.
- **The action colour** is ink: PLAY, prices, the selected slot.
- **The team pastels** show only inside the score pads, the way a pad glows inside its rim.
- **The match HUD** is unframed numbers. The selected weapon has a bone bar under it.
- **The loadout** is numbered 1/2/3/G like the HUD. It has a mastery medallion, a mark on each stat bar for the secondary average, and Skin and Hat rows.
- **Type has two registers:** ExtraBold caps for names and numbers, Medium sentence case for anything said.
- **The shop** lets item art break out of the top of its plate. The coin packs use the shop's own renders.

Why it won't read as AI:
- one rule you can see (plate = press), taken from our own pads;
- light on the game, a deliberate and unusual choice;
- PLAY is the one pad, and the rest of the menu is plain type;
- one action colour; colour only where it means team or rarity;
- numbers that add up across screens.

Risk: the loudest on screen; light plates on the brightest arenas lean on the lip and drop shadow.

### B. BROADCAST: your match as a sports graphic
Hard square black slabs.
- **The one motif is a skew.** Everything you can press, and every active state, leans: PLAY, DONE, the prices, the active tab, the active hotbar slot, the round tab.
- **Surfaces:** two slab tones.
- **Type:** condensed Oswald caps for names and big numbers; Builder Sans ExtraBold caps for the nav, tabs and section labels; Builder Sans in sentence case for everything small.
- **Profile and settings** are labelled buttons in the player plate.
- **The match score is a broadcast bug:** a round tab, the two team blocks with their players inside, then the clock. The grapple is a HOOK ×2 tab on the HP slab.
- **The hub:** the menu is a lower-third bar beside a Butter PLAY slab, over a live ticker of every queue's count.
- **Colour:** black and white, plus the team pastels as solid score boxes. Butter marks only the next thing to press (PLAY, DONE, the price).
- **The shop:** a wide featured strap with the set's skins and hat as renders, then the daily list and the crates as running orders.

Why it won't read as AI:
- zero radius and one skew that means "press" or "active": a hard system of its own instead of soft cards;
- big numbers are the focal point, with no labels on things you can already see;
- the menu and ticker carry live information, not just buttons;
- one accent with one meaning (press this);
- no icons in menus: type does the work.

Risk: the most "esports" of the four; condensed caps can feel cold.

### C. OPEN (dropped after critic round 2)
Type straight on the world with no boxes, one huge word per screen. Dropped after round 2: its
critic named the no-container "editorial blur" look an AI default of its own, and it had the
weakest legibility of the four from round 0. Its frames are kept in the vault review notes.

### D. SIGNAL: the hubs' wayfinding signs
The hubs are stations, concourses and hotels, so the menus talk like their signs: deep green enamel with a thick cream rim (how real enamel signs are made), sentence case in Titillium Web, and platform badges for keys. Only menus are signs; the match HUD and the phone keys are translucent enamel with no rim.
- **Mounting:** nothing floats. Every sign hangs from the top edge, stands on the bottom edge, or sticks out of a side wall, and its rim stops where it meets the edge.
- **The rim means focus:** only the sign in focus (the hub sign, the selected slot, the featured set) has the cream rim; other signs are plain enamel.
- **Menu rows show live state,** each at its own height: a quest bar, party slots, your current guns, the daily reset.
- **The hub:** one sign named after the hub, hanging in the top-right corner, with Change hub and Settings by the name and the wallet in its footer. Play is a Butter wayfinding arrow with a mode selector under it.
- **The match score** is a two-line sign: each team's tile with its players, and the clock beside them.
- **The match HUD:** two registers. Only the score hangs as a sign; HP, ammo and the slots are bare type with a shadow, and the kill feed is borderless strips.
- **Buttons:** Butter enamel plates (Play, Buy, Done); no arrows, no mode pills.
- **The scoreboard:** dead players are greyed with a crossed head; your party has a "your party" chip.
- **The loadout:** the armory is a departures board.
- **Colour:** Butter only on the next thing to press.

Why it won't read as AI:
- a real-world sign system with its own rules (edge-mounted, enamel rim, platform badges);
- sentence case: the only direction that isn't all caps;
- signs for menus and bare type for the fight: the two registers a real game keeps;
- the departures board gives the loadout a structure of its own;
- the accent means "next step" and nothing else.

Risk: green enamel next to the pastel teams is the boldest colour choice of the three; it needs the hubs' signs to match.

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

## 5. Rebuild

```
python prep_images.py <folder with hub_spawn.jpg, hub_rotunda.jpg, match_crate.jpg, match_forest.jpg>
python mocks.py            # all four, or: python mocks.py a c --frames=hub,shop
python sheet.py            # comparison sheet + one board per direction
```
