# Menu cleanup: before / after

## Home
| before | after |
|---|---|
| left nav: GUIDE, LORE, PATCH NOTES, LOADOUT, COSMETICS, CONTAINERS, LEADERBOARD, SETTINGS | **CUSTOMIZE**, **CONTAINERS**, **LEADERBOARD**, and a row of round icons: SETTINGS · GUIDE · LORE · PATCH NOTES (NEW badge kept) |
| hero: CUSTOMIZE button (went to CHARACTER) + EQUIPPED gun (went to LOADOUT) | click the 3D mannequin itself → CHARACTER; the EQUIPPED gun → LOADOUT. CUSTOMIZE button gone (it was a second, differently named way into CHARACTER) |
| right: ONLINE / WITH BOTS / COOP / TRAINING | same, under a **PLAY** heading |
| account bar: Lv, name, rolls, PROFILE, LOG OUT | Lv, name, rolls, PROFILE (LOG OUT is on the profile page, it was in both) |

## The CUSTOMIZE hub (one set of tabs on top of all four)
| before (separate screens) | after |
|---|---|
| LOADOUT screen (weapon chips, item chips, killstreak chips) | **LOADOUT** tab = the customize screen in loadout mode: weapon list by slot (E = equipped), 3D weapon, **EQUIP AS PRIMARY/SECONDARY/MELEE** on the info card (or double-click a row), item row and killstreak row as 3D/drawn tiles (pick 3, same draft rule) |
| COSMETICS → customize screen (skin / wrap / charm / effect / finisher) | **WEAPONS** tab (unchanged features; the info card's EQUIP button works here too; RANDOM LOOK button) |
| CHARACTER screen (outfits + a kill effect row) | **CHARACTER** tab. The kill effect row is gone from here: it's WEAPONS > FINISHER (it was in 3 places) |
| classic locker (old weapon list, wraps, hats, effects, kill effects, grapples, sprays) | **GRAPPLE & SPRAY** tab: only grapples + sprays. Everything else it had is in WEAPONS |
| customize buttons: COPY LOOK TO ALL, RESET, CHARACTER, LOADOUT, CONTAINERS, GRAPPLE + SPRAY | COPY LOOK TO ALL, RESET, RANDOM LOOK (the others are the hub tabs / home nav) |

## Pause
| before | after |
|---|---|
| RESUME, LOADOUT, CHARACTER, COSMETICS, MATCH SETTINGS, SETTINGS, QUIT TO MENU | RESUME, **CUSTOMIZE** (the hub, LEAVE comes back here), MATCH SETTINGS (hidden in mode lobbies, where nobody can change the match), SETTINGS, QUIT TO MENU |

## Other screens
- PROFILE: the COSMETICS button is gone (home nav / hub). LOG OUT stays.
- CONTAINERS: TO COSMETICS gone. The cards show the 3D crate / duffel bag / box; opening one plays it live: it rattles harder while the strip spins and bursts (lid off, planks, confetti in the rarity colour) on the reveal.
- Unchanged: guide, lore, patch notes, leaderboard, settings (+ KEY BINDINGS), mode pickers (their cards were already 3D-rendered by modeart.js), bots setup, match settings, account, name card.

## 3D and cost
- home hero (mannequin holding your gun): already live 3D; now drawn at 30 fps and resting after 20 s with no input (the browser pauses it when the tab is hidden)
- customize: 30 fps while turning / dragged / hovered, stops after 14 s idle
- container opening: its own small renderer, drawing only while it plays (potato renders at 35%)
- item pictures from the real models (grenade, duck, smoke bomb, popper, reverse card, camera, calculator, goggles); medkit, shield bubble, bubble wand and speed trap keep their drawings

## Old screens kept for scripts
`#scr-loadout` (hidden, still built when LOADOUT opens, so `JANK.show('loadout')` + `#lo-item button` scripts still work) and the classic list's elements (hidden).
