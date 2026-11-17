# Player cards: stats, rank and custom profiles (Roblox)

The owner asked on 16 Nov 2026: "when you click on someone you should see their track record their most used weapons,
their rank, kills in percentage etc we can maybe have those custom profiles or something idk custom borders
backgrounds idk".

What came of it: every player has a **card**. It shows:

- the background, border and title they wear;
- their headshot, name, rank badge and XP bar;
- their numbers: K/D, win rate, headshot %, accuracy, kills, best streak, and a row of smaller facts;
- their three most used weapons, with usage bars;
- their last 10 matches;
- the loadout they carry.

Ways to open a card:

- **Someone else's:** click them in the hub (the crosshair or the mouse arrow on them, a tap on a phone), or tap them on the card's PLAYERS tab.
- **Your own:** press **K**, or use the **PROFILE** button over SHOP (hub only).

On your own card you pick your border, background and title. The settings panel (**P**) has **HIDE MY STATS**. With it
on, others see only your name, rank and card.

## Where it lives

| file | what |
|---|---|
| `src/shared/Ranks.luau` | XP, level and rank: the web game's level curve, our tiers, the drawn badge |
| `src/shared/CardStyles.luau` | the borders, backgrounds and titles: ids, names, rarities, and how each is drawn |
| `src/server/Stats.luau` | the numbers, the XP, the card's look and the privacy switch; the remote; the test hook |
| `src/server/ProfileServer.server.luau` | starts Stats with the Fight and Matches modules |
| `src/client/ProfileUI.luau` | the card screen (PROFILE / CUSTOMIZE / PLAYERS tabs) |
| `src/client/ProfileClient.client.luau` | K, the PROFILE button, click / tap on a player in the hub, the test hook |
| `src/client_root/JankSettings.client.luau` | the HIDE MY STATS row in the P panel |
| hooks in `Fight.luau`, `Combat.server.luau`, `Matches.luau` | `Fight.onShot` / `Fight.shot` (every attack the server took), the headshot flag on `Fight.onHurt`, `Matches.onStart` / `onRound` / `onEnd` / `matchOf` |
| `ReplicatedStorage.JankfireRemotes.Profile` | RemoteFunction (in `default.project.json`) |

## What counts

Only real matches count:

- both players are in the same match, on opposite teams;
- the round is live.

The hub, the training hall and its dummies count for nothing. The web game's lobby and training mode give no XP either.

| number | how |
|---|---|
| kills, deaths | a kill on a player on the other team, and your deaths in a live round. A fall into the void is a kill for whoever shoved you (the weapon is what they last hit you with) |
| K/D | kills ÷ deaths |
| matches, wins, win rate | a match ends as W or L. Leaving mid-match is an L |
| rounds played / won | each round of a match |
| accuracy | attacks that hurt somebody ÷ attacks. An attack is a shot the server took (after `Rules.fire`) or a swing. A shotgun volley that hits two people counts once |
| headshot % | hits that were headshots ÷ hits (the web game's Headshot % is the same, hsh / hits). The server decides the headshot (`Rules.headAimed` for one-bullet guns) |
| best streak | kills in one match without dying |
| per weapon | kills, attacks, attacks that hurt, headshots, seconds held while alive in live rounds, damage. **Most used** = longest held |
| last matches | newest first, 10 kept: when, mode, arena, W/L, the score, kills / deaths, the weapon held longest, damage |

There are no assists. The web game has none, and its `tag()` only remembers the last attacker for kill credit.

## Rank

- **XP and level are the web game's, exactly.**
  - `levelOf(xp) = floor(sqrt(xp / 40)) + 1` and `xpForLevel(l) = (l - 1)² × 40`, with no cap (`server/accounts.js`).
  - XP on Roblox comes from what exists here (`server/room.js`): **+20** a kill on a player, **+50** a round won, **2 a minute** of live match time.
  - Web XP sources that have no Roblox mode yet (coop waves, zombies, bomb plants, board game night) aren't ported.
- **The rank is ours**, because the web game has none. It has eight tiers over the levels, with three divisions each (III → II → I):

| tier | from level |
|---|---|
| Iron | 1 |
| Bronze | 5 |
| Silver | 10 |
| Gold | 15 |
| Platinum | 22 |
| Diamond | 30 |
| Master | 40 |
| Apex | 55, then it shows the level: APEX 61 |

- Roughly, a match is worth 150 to 350 XP. Silver takes about 13 matches, Gold about 35, Diamond about 135.
- The badge is drawn from frames, so there are no pictures to moderate:
  - a diamond in the tier's metal;
  - a ring from Silver;
  - wings from Platinum (two pairs from Diamond);
  - a crest from Master.
  - Inside the diamond, 1 to 3 bars show the division.

**Ranked (17 Nov, place version 502).** Agreed with the play/party/ranked session (option B): "rank" means the ranked ladder, and the XP side is a level.
- **The card:** shows LV and the XP bar (amber). On the right is the player's ranked badge with its line (for example "GOLD II · 2v2 · 1,640", "PLACEMENTS 2/5" or "UNRANKED"), drawn by the ranked session's `ReplicatedStorage.Jankfire.RankedStyle` (`badge(parent, size, ranked)`, `label(ranked)`, `color(ranked)`) from `card.ranked`. The player list rows show the same.
- **Until that module and data exist:** a quiet plate with the level number ("LEVEL 17").
- **The ranked data:** comes in through `Stats.cardExtra(fn)`, where `fn(target, viewer, card)` runs for every card and list row (private players too), each one pcall'd. The ranked session keeps its own store `JankfireRanked_v1`.
- **The XP tier names** (Iron..Apex) left the card. Ranked may use those names and colours for its own badge.
- **Party Ranked (17 Nov):** the classic modes' second ladder. When a player has played it, the ranked session's `card.partyRanked` (`ladder = "party"`) is drawn by the same `RankedStyle.badge`, smaller:
  - **Card header:** 55% of the main badge (53 px on PC, 41 on a phone), tucked at the main badge's lower left and clear of its line. Its label ("CARDBOARD II  ·  PARTY") goes on a second, smaller line under the main one, in `RankedStyle.color`.
  - **PLAYERS rows:** only the small badge (60%), at the main badge's lower left. The name and the YOU chip move left to make room.
  - With no `partyRanked` nothing extra is drawn. The badge is pcall'd, so a slip in it never breaks the card.

## Custom profiles

Everything is drawn in the GUI from frames, gradients and strokes. Nothing is uploaded, and no picture holds text,
codes or logos (see `roblox-upload-content-rules`).

| type | free (everyone owns) | in the loot pool |
|---|---|---|
| border (9 + Ducky, VIP) | Hairline, Steel | Brass, Twin Line (common) · Brackets, Ember (rare) · Gilded, Prism (epic) · Halo (legendary) |
| background (12) | Slate, Concrete, Metal | Sunset, Night Sky, Camo (common) · Furnace, Carbon, Static (rare) · Aurora, Molten (epic) · Eclipse (legendary) |
| title (16 + VIP) | none, ROOKIE, NEW HIRE | the web game's end-of-match medals: FIRST BLOOD, TWO FOR ONE, FILED A COMPLAINT, CONSCIENTIOUS OBJECTOR (common) · HEAD OF HR, LONG DISTANCE CALL, HANDS-ON MANAGER, WASTE DISPOSAL (rare) · BULK DISCOUNT, ON A TEAR, OVER THE LIMIT (epic) · UNTOUCHABLE, EMPLOYEE OF THE MONTH (legendary) |

- **VIP only** (rarity `vip`, added 16 Nov for the shop session's VIP pack):
  - **Ducky** border: a yellow-gold shimmer, a warm glow, gold corners, and a small duck drawn from rounded shapes, sitting on the top edge;
  - **VIP** title (the shop session picks its words).

  They are granted only through `Loot.grant` of the VIP offer. LootTable's card hook skips rarities it doesn't know, so they never roll from a container. `CardStyles.forSale` leaves them out of the shop's rotation. In the picker, a VIP item you don't own shows locked: "VIP pack only".
- **Night Sky:** round stars and four-point sparkles (the owner: stars "should be actual stars and not little squares"). Static keeps its square pixels on purpose.

**Backgrounds are real pictures (since 16 Nov, place version 461).** The owner said: "The banners look very ai ish, can we take some free to use ones from internet?". So every background except Slate (a plain gradient) and Static (drawn TV noise) is now a photo or texture that is free to use with no conditions: public-domain NASA photos and CC0 Poly Haven / ambientCG skies and textures. Each was checked at full size (no text, logos, faces or watermarks), cropped to 1024x320, graded quieter, and uploaded as an Image (all Approved). Two candidates were turned down: both NASA sun photos carry printed timestamps, a web address and a logo.

| id | name | source | licence | image |
|---|---|---|---|---|
| concrete | Concrete (free) | Poly Haven `concrete_wall_008` | CC0 | rbxassetid://80093131602053 |
| metal | Metal (free) | Poly Haven `metal_plate_02` | CC0 | rbxassetid://119268820513573 |
| sunset | Sunset | Poly Haven HDRI `the_sky_is_on_fire` (the sky, cropped above the buildings) | CC0 | rbxassetid://131169722023201 |
| stars | Night Sky | Poly Haven HDRI `satara_night_no_lamps` (the Milky Way over trees) | CC0 | rbxassetid://109006184975619 |
| camo | Camo | Poly Haven `japanese_sycamore` (plane-tree bark, nature's camo) | CC0 | rbxassetid://131795114784336 |
| flames | Furnace | ambientCG `Lava004` | CC0 | rbxassetid://76170896329040 |
| carbon | Carbon | ambientCG `Fabric004` (carbon fibre) | CC0 | rbxassetid://126045915944582 |
| aurora | Aurora | NASA `iss058e005282` (an aurora over the Earth's limb, seen from the ISS) | public domain | rbxassetid://88607740740565 |
| molten | Molten | ambientCG `Lava001` | CC0 | rbxassetid://77558571123420 |
| eclipse | Eclipse | NASA / Carla Thomas `AFRC2017-0233-005` (2017 total eclipse; ring placed right on black) | public domain | rbxassetid://76928894691984 |

The free Stripes and Grid are gone. Nobody could own them (free), and a card still wearing one falls back to Slate on load. The crops and grading are `CardStyles.CREDITS` / `C.IMAGES`. The working files (crop boxes, grades) were `cardbg_work/crop.py` in the session scratchpad.

- **Backgrounds** first started from the web game's name-card backgrounds (`public/js/cards.js`: stripes, grid, sunset, stars, camo, flames, static), made quieter.
- **Left out:** the web game's magenta "missing texture" checker (too loud), and ORGAN DONOR (gore).
- **Animated pieces:** Ember, Prism and Halo turn slowly, and so do Aurora, Molten and Eclipse. One loop drives every gradient on screen.

**Ownership** sits in the loot save, as gun-less types like a weapon skin (`Loot.owns(p, "border", id)`). Until the
loot session adds the types to `LootTable`, only the free ones are owned. The others show locked: "from Duffel Bags
or the shop".

## Save

- **Store:** `Profiles.new("JankfireStats_v1", …)`, key `u<UserId>`. This is the loot save's session-locked layer, as a store of its own, so a stats write never touches inventory or receipts.
- **Writes:** autosave every 60 s while it changed, and a save right after every finished match. On leaving or shutdown the save is written and released.
- **Shape (v 1):** `xp k d m w rp rw sh hi hc hs hk dmg best time`, plus:
  - `wpn[weapon] = { k s h hs t dmg }`;
  - `recent` (10 matches);
  - `look = { border, banner, title }`;
  - `private`;
  - `since`;
  - `log`: the last 100 matches, one record each (see Cheat restores);
  - `fixed`, `voids`, `reset`, `backup`: what restores have done.
- **Looks you don't own:** a worn look you no longer own goes back to the default once the loot save has loaded.

## Cheat restores

The owner's rule (17 Nov): "If someone is caught cheating give back any ranked stuff or stats!!" The anti-cheat calls this when it confirms a cheater. The ranked session's `RankedData.restoreFor` does the same for RP and MMR, with the same call shape.

```lua
local Stats = require(ServerScriptService.Jankfire.Stats)
task.spawn(function()
	local res = Stats.restoreFor(cheaterUserId, since) -- since = os.time() seconds; nil or 0 = all 100 logged matches
	-- res = { ok = true, matches, victims, now, queued, failed } or { ok = false, why }
end)
```

- **Per-match records.** Every finished match writes one record into each player's own save (`log`, newest first, 100 kept), keyed by the match's `key`. `Matches` now gives every match a key that is unique across servers (`<first 8 of JobId>-<id>-<os.time>`), and `matchOf(p)` returns it. A record holds `{ id = key, t (the end), mode, map, team, ranked?, r, k, d, rp, rw, xp, foes = { userIds }, mates = { userIds } }`. Foes are taken when the match starts, so a player who leaves is still in it. The `recent` rows carry the key too.
- **The victims.** These are everyone on the other side of the cheater in each logged match that ended at or after `since`. Each victim gets that match's **deaths** taken off. If they **lost** it, the match and the rounds they lost come off too. Their kills, their XP and a win stay. On the card, a lost row shows **VOID** in grey.
- **The cheater** (my call: **reset**). Every number and the XP go back to zero: totals, weapons, recent matches, best streak, level. Their card shows a **STATS RESET** strip with the day, to everyone, even when the player keeps their stats private. Hiding the numbers would have kept fake records (a best streak, weapon numbers) waiting to come back. A reset of the whole save, not only the period, is safer because a catch usually comes after cheating started. The look, the privacy switch and the loot are left alone.
  - The old numbers are kept in `backup`. If a catch was wrong, `Stats.undoRestore(userId)` adds them back to whatever was played since. Victims keep their restore.
- **When the anti-cheat calls it (agreed 17 Nov):**
  - **`restoreFor`:** only when the owner presses CONFIRM CHEATER or bans from the panel. Never from the auto-ban or an automatic flag.
  - **`since`:** the earliest evidence on record minus one day (their first catch or the first report against them; both are kept 30 days). It is 0 when the owner picks ALL or there is no evidence.
  - **`undoRestore`:** only the panel's UNCONFIRM. UNBAN and a timed ban running out never call it, because a served ban isn't a wrong catch.
  - Both calls run in `task.spawn`. Results go into the anti-cheat's moderation log, and a failed read is retried.
  - While a restored cheater stays in this server, nothing more counts for them. That covers the moment between the call and a kick.
- **Who gets it when:**
  - **Players in this server:** at once, and their save is written.
  - **Everyone else:** a pending entry in `JankfireStatsFix_v1` (`JankfireStatsFix_studio` in Studio), key `u<userId>`. It is applied when they next join, written to their save, and only then taken off the list.
  - **A server that has them now:** a MessagingService message on the topic `JankStatsFix` makes it take the pending entries at once. The same message tells every server to watch the cheater.
- **A match still being played:** victims in a match with the cheater get it taken off when that match ends.
- **A cheater kicked just before the call:** this server keeps the logs of players who left in the last 10 minutes, so the newest match is in it.
- **Idempotent.** A match is undone once per victim (`fixed[key]`), and a reset happens once per `since` (`voids`). The pending store merges entries by id. Running the same call twice changes nothing. A later call with an earlier `since` only adds the older matches.
- **For ranked:** `Stats.matchesOf(userId, since)` returns the cheater's logged matches `{ key, t, mode, ranked, team, r, foes, mates }`, so ranked needs only its own rating changes per match, keyed by the same key.
- **Limits:** only the last 100 matches of the cheater can be restored, and only matches played after this shipped (older saves have no log). A victim's own record has to be in their last 100 too, or there is nothing to take off (the match is marked done).

## The remote and the attributes

The remote is `JankfireRemotes.Profile:InvokeServer(op, …)`. It always answers a table `{ ok, why?, … }`:

- `("card", userId)`: anyone in this server. A private player's card has no `stats`, `weapons` or `recent`.
- `("list")`: everyone here: id, name, display, xp, look, private.
- `("owned")`: which card looks you may wear.
- `("look", "border" | "banner" | "title", id)`: wear one. It must be free or yours.
- `("private", bool)`: the switch.

Player attributes:

- `Xp`, `Level`;
- `StatsSave` (`loading` / `cloud` / `off` / `lost`);
- `StatsPrivate`.

The loadout on a card is read from the player's own attributes (`LoadoutNext`, `Wraps`, `Hats`).

## Testing in Studio

- **`ServerStorage.JankStatsTest`** (BindableFunction, Studio only):
  - `("begin", p)` / `("finish", p, "W")`: a test match;
  - `("ghost", "Stand")`: that training dummy counts as an enemy player while you're in a match;
  - `("data", p)`, `("card", p, viewer)`, `("save", p)`, `("reset", p)`, `("xp", p, n)`;
  - `("unlock", p, true)`: wear any look this session; nothing about owning is saved.
  - `("begin", p, mode, arena, foes)` returns the test match's key; `("round", p, won)` is a round of it; `("put", p, data)` puts a backup taken with `data` back.
  - cheat restores, with stand-ins under made-up negative userIds: `("stand", uid, online)`, `("drop", uid)`, `("fake", uid, { key, r, k, d, rp, rw, foes, t? })` (a finished match, totals and record), `("view", uid)`, `("pending", uid)`, `("join", uid)` (takes what waits), `("restore", uid, since)`, `("undo", uid)`, `("clean", uid)` (no pending entries, not watched).
- **`JankMatchTest:Invoke("ghost", padName, nil, secs, player, winTeam)`** now puts the test player in the ghost match (team 1) and picks who wins when its time is up.
- **The player's `ProfileTest` attribute** (from the Client):
  - `open`, `open:<userId>`;
  - `tab:profile|customize|players`;
  - `close`;
  - `fake:844x390` (a phone-sized layout), `real`;
  - `scroll:<y>`.

## Test results (16 Nov 2026, solo Play, place versions 393 and 399)

| check | result |
|---|---|
| a ghost match with the player in it (JankMatchTest `ghost` 1v1, arena RooftopV3, team 1 wins) | recorded: m 1, w 1, recent[1] = { map RooftopV3, mode 1v1, W, 1 / 0, weapon ar, dmg 100 } |
| attacks and time | Fire shots count (`sh`); seconds held per weapon and match time count while the round is live |
| real AR shots at the ghost dummy in the training hall | 10 shots, 10 hits counted (`hi`), damage and the kill credited to `ar`, streak 1 |
| kills and XP | kill +20, 2 XP a minute: 21 XP after the first test, 41 after the second |
| privacy | with HIDE MY STATS on, a stranger's card has no stats, weapons or recent, but keeps XP and look; your own card keeps everything |
| rejoin | the save was released on stop (GetAsync shows it with no lock); the next Play test loaded m 1, w 1, k 1, xp 21 |
| click | a real mouse click (crosshair) on a stand-in in the hub opened the card |
| layout | PC 1289x753 and a phone-sized 844x390 box (fills it, the body scrolls, buttons ≥ 46 px) |

| looks you own, through real grants (place version 435) | the shop's Head Office bundle, claimed into the owner's loot inventory, shows in the picker as owned: Brackets, Carbon, HEAD OF HR. They can be worn; Halo and Ducky (not owned) are refused and shown locked. Ducky's lock reads "VIP pack only" |
| VIP looks (Studio unlock) | the Ducky border (the duck on the top edge) and the gold VIP title draw on the card and in the player list |

| test data kept out (place version 445) | only real live weapons count (`Roster`, `live`): a test hook's "test" damage adds nothing. A Studio ghost match with the player in it adds no match, time or XP. The stand-in dummy and ghost matches count only while `JankStatsTest("ghost", name)` is on, and `"ghost", ""` turns it off again (the default). Real AR shots still count (3 of 3) |

**Cheat restores (17 Nov, solo Play with stand-ins, place version 523):**
- P = the test player. The stand-ins use made-up userIds: C = cheater (in the server), V1 = victim (away), V2 = victim (in the server). C2 = a second cheater caught while a match against them was still on.
- `since` = an hour ago.

| check | result |
|---|---|
| a real match end writes the record | P lost a test match to C (one real death, rounds 1 of 3): `log[1]` = { key, d 1, rp 3, rw 1, L, foes { C } } |
| the call | `restoreFor(C, since)` → matches 3 (a match from before `since` left out), victims 3, now 3 (P, V2, C), queued 1 (V1) |
| a victim who lost | P: deaths 1 → 0, matches 1 → 0, rounds played 3 → 1 (the round they won stays), the row shows VOID |
| a victim who won | V2: that match's 2 deaths come off (6 → 4), the win stays (2 matches, 1 win), the 2 lost rounds come off. Their match from before `since` is untouched |
| the cheater | C: every number 0, `reset` set, `backup.k` = 10 |
| twice | the same call again: all numbers the same, V1 still has 1 pending entry (merged) |
| away, then joins | V1 had only the pending entry. On joining: deaths 3 → 0, matches 1 → 0, rounds played 5 → 2, kills 2 kept, pending list empty. A third call changed nothing |
| caught mid-match | P died in a live test match against C2. C2 was restored before the end (matches 0: nothing logged yet). When the match ended, P's death, match and lost round came off (back to what they were before it) |
| undo | `undoRestore(C)` → k 10, d 8, m 4, w 3, rp 18, rw 11 (as before the call), no reset mark. A second undo changed nothing |
| the card | the remote card's recent rows carry `x`, and draw VOID. A reset player's card shows STATS RESET with the day |

The owner's save was put back exactly as it was from a copy taken first (zero stats, the Ducky look kept) and saved. The stand-ins' pending entries were removed from `JankfireStatsFix_studio`.

Not tested: two real servers. That covers the MessagingService nudge and a cheater online in another server. Studio runs one server.

![restore photos](profiles/restore-sheet.jpg)

After the tests the owner's stats were reset to zero (saved). Their look was left as they wear it (Ducky border, Eclipse background, from the VIP pack).

Not checked end to end:

- **Headshots.** My hand-made headshot claims were judged body shots by the server's own head check. The headshot flag reaches the stats through `Fight.onHurt`; the counting itself is the same code path as hits.
- **A card look won from a Duffel Bag.** Ownership itself is proven by the shop's grants (the same `give` path). The loot dev `set` erred on card types; the loot session has fixed it.
- **A real second player.** Studio's MCP only starts solo tests.

![photo sheet](profiles/profiles-sheet.jpg)

## Titles over heads (17 Nov 2026, place v672)

The owner: "can titles appear above head".
- **Where it comes from:** `server/Stats.luau` publishes the card title you wear as the player attribute `CardTitle` (on load, on every look change, and when a title you no longer own comes off).
- **Who draws it:** `client/OverheadTitles.client.luau` draws it for every player, just under their Roblox name: one fixed-size BillboardGui per character, made on each client (nothing replicates).
- **Look:** the title's words in its rarity colour (`CardStyles.RARITY_COLOR`), Montserrat Bold with a dark outline. It's made like the regulars' nametags: on the character's Head, 7 studs wide, words scaled to fit up to 22 px, not AlwaysOnTop. An AlwaysOnTop billboard didn't draw at all in a Play test (v686). "No Title" (`none`) shows nothing.
- **Hidden** on anyone in a match (Zone `match`): it stays on the scoreboard and the card. Hidden behind walls (one ray per player, 10 times a second). Your own title shows only when your camera is out, not from your own eyes.
- **Studio stand-in:** a Model with the attribute `TitleStandIn = true` and its own `CardTitle` shows like a player (for photos).
- **Fade:** from 45 to 60 studs; gone past 60.
- **Switch:** Settings `gfx.titles` (SHOW TITLES on the settings page, GRAPHICS > OTHER PLAYERS; nil = on).
- **Studio test hook:** the attribute `TitleZoneTest = "match"` stands a player in a match.
- **Play check (v672, a test title on the attribute only):**
  - text EMPLOYEE OF THE MONTH, on its head;
  - 10 and 30 studs on, 50 at fade 0.34, 58 at 0.87, 70 off;
  - in a match off, switch off off, switch back on.
  - No photo yet: the test camera never framed the avatar.
- **Adding a title** is one row in `CardStyles` TITLES (`{ id, WORDS, rarity }`). The card, shop, crates and the overhead title all read it.
- **17 Nov, the owner's picks** (v685): 31 titles, rarities set by the main session.
  - Cute: PRINCESS, STARDUST, DUCKLING, SOFT SERVE, CUTIE, BUNNY, BONBON, KITTEN, SQUISHY.
  - Cool: APEX, PHANTOM, DEADEYE, ZERO RECOIL, NIGHTSHADE, HEADHUNTER, AFTERBURNER, COLD BLOODED, BLACKOUT, IRONCLAD.
  - Meme: SIGMA, SKILL ISSUE, ALPHA, LONE WOLF, SWEAT, NPC, BOT, CHUD.
  - JANKFIRE's own: JANK CERTIFIED, PATIENT ZERO, DUCK RAIN SURVIVOR, SPOON MAIN.
  - Photographed in Play on v686 (`docs/profiles/titles-sheet.jpg`): DUCK RAIN SURVIVOR over a stand-in's head, and all of them on the card's CUSTOMIZE tab, where DUCK RAIN SURVIVOR fits on one line.
  - During a real emote there was no HeldWeapon, no Tool and no visible viewmodel.
