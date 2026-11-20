# The owner's dev menu and the OWNER title

Asked for on 18 Nov 2026: "can you give me a special title for being owner, I get a command menu where I can fly,
noclip, fling people like a troll thingy for being dev, essentially I can give myself weapons in hub like remote freeze
and rewind people XD".

Files:

- `src/server/OwnerDev.server.luau`: checks and runs every command.
- `src/client/OwnerDev.client.luau`: the menu, plus everyone's frozen-body hold.
- The OWNER title: `src/shared/CardStyles.luau` (`OWNER`, `styleTitle`) and `src/server/Stats.luau` (who may wear it).

## Who and where

- **Only the place's creator** (`game.CreatorId` of a user-owned place) can use it. No name is written in the code. Since 19 Nov the owner can lend the POWERS tab to a friend in the server for a while (FRIENDS, below); everything else stays the owner's.
  - The client builds the menu only for the creator, and only after the server says yes.
  - The server checks the creator on every single command. Anyone else gets "owner only", logged once.
- **It works everywhere, matches included.** The owner overrode the first "never in a match" rule on 18 Nov: "I can use it in matches, I'm the owner".
- **The safeguard: a match a dev power touches counts for nothing.** That covers the owner using any command in a match, having a power on while in one, or doing something to someone who is in one.
  - That match gets `m.dev = true`. It plays on normally.
  - From then on nobody's stats, rank, quests or loot change from it:
    - `Stats.liveFor`, `finish` and `onRound` skip it.
    - `Quests.matchCounts` skips it.
    - `RankedData.rate` and `onEnd` skip it, so a leaver's loss is skipped too.
  - Its players carry `MatchDev` (the match id). FightHud's end card then shows a small grey "DEV" in its top-right corner.
  - `MatchDev` comes off 15 s after the match is over for them.
  - Damage dealt before the flag went up already counted, because Stats writes hits as they land. The match's record, win/loss, XP and rank at the end are skipped entirely.
- **Every command is printed to the server log** as `[dev] <owner> <what> <target>`.
  - Refusals ("refused (not the owner)") and match flags ("match N flagged dev (...)") are logged too.

## Opening it

- **Keyboard:** F8, or `/dev` in chat. In the legacy chat the server hears `/dev` and bumps the `DevPanel` attribute.
- **Touch:** the small DEV button in the top-right corner, under the currency box. Only the owner has it.
- **Controller:** VIEW reaches the DEV button (it's in PadNav's menu column). Once the menu is open, B backs out.
- **Hotkeys, menu open or not, only while AIM KEYS is on:**
  - **X** flings whoever you're looking at.
  - **Z** freezes or lets go of whoever you're looking at.
  - **Y** shows a red card to whoever you're looking at.
  - **AIM KEYS** (since 19 Nov, because X is also the grapple's REEL IN) is a toggle at the top right of the POWERS tab. It's off by default and stays on until you turn it off (for the session). While it's on, a small gold "DEV KEYS ON" chip shows under the DEV button. While it's off, X, Z and Y do nothing for the dev menu, so X is just reel-in. Ctrl isn't used as a modifier, because Ctrl is crouch.
- The menu frees the mouse but doesn't hold you still (it's a cursor-only MenuCursor name). You can fly with it open.

## The powers

Each power is a server attribute on the owner. The owner's client acts on it.

| Power | Attribute | What it does |
|---|---|---|
| FLY | `DevFly` = speed (studs/s, 20 to 300, default 80) | Moves you where the camera looks (WASD or the stick). Space or pad A goes up; Ctrl, C or pad B goes down. With nothing pressed you hold still in the air. A LinearVelocity plus AlignOrientation and PlatformStand drive the body. `Move.client` stands down while `Body.flying` is set. |
| NOCLIP | `DevNoclip` | Your body's parts stop colliding every step. The Humanoid still stands on floors, so walls become air. |
| RUN SPEED | `DevSpeed` (1x to 4x, in 0.25 steps) | `Body.devSpeed` multiplies your run speed in `Move.client`. |
| WEAPONS IN HUB | `DevArms` | Weapons come out in the hub (see below). |
| INVISIBLE | `DevInvisible` | Everyone else stops seeing your body, gun, name, title and pet. The server makes every part and decal of your character fully see-through, switches off its lights, effects and labels, and hides the name (`DisplayDistanceType` None). Each value is kept so it can be put back, including anything added later, such as a new gun or a respawn. OverheadTitles, Pets and ThirdPerson skip an invisible player. Your own client draws a faint ghost of you from each part's `DevWas` attribute. Footsteps and shots can still be heard. |
| (all of the above) | `DevOn` | Set while any power is on, and for 3 s after the last one goes off. The anti-cheat's pass. |

**WEAPONS IN HUB:**

- Every hub weapon check lets `DevArms` through. That covers `Fight.holstered`, Combat, HubHolster, HoldWeapons, WeaponProj, WeaponTricks (the TV Remote), ScytheDash, Lasso, Cart, CardDeck and Utility on the server, and Arsenal, Katana, SaucePour, ScytheDash, Utility, TouchControls and PadLook on the client.
- `Zones.training` is true for the owner in the hub while `DevArms` is on. So any weapon picked goes into the loadout's try layer, the one training uses: never saved, and gone when the switch goes off.
- The menu's GIVE ME A WEAPON grid lists every live roster weapon. A click switches DEV weapons on if needed, then picks the weapon through the Loadout remote.
- The TV Remote works on anyone in the hub: left click pauses them, right click rewinds them 2 s.

**What it can do to others** (any player, in a match too; in Studio also a training dummy, the test stand-in):

| Command | What it does |
|---|---|
| FLING | 170 studs/s away from you and 130 up, through `Fight.knock`, so the anti-cheat sees the push. It also tags the victim, so a fall afterwards counts as yours. |
| FREEZE / LET GO | Holds them still where they are. Their own client anchors the body (`DevFrozen`) and `Rules.stun` stops their shots. They are let go if they die or leave, and everyone is let go when the owner leaves. |
| GO TO / BRING | Moves you 5 studs in front of them, or them in front of you. Anywhere: a map room or a match keeps its own list of who's in it, so a player brought out is still counted there. |
| JAIL / FREE | Sends them to the jail (below), or lets them out to the hub. |
| RED CARD | Football style. On every screen the owner's right arm goes up with a red card in the hand for 1.2 s, and a referee's whistle blows where they stand. The whistle is a recording: Pro Sound Effects "Referee Whistle, Exterior, Single Blast", asset 9118113825, from Roblox's licensed library. The target's screen flashes a red card shape, with no text. Then they're sent to the jail. |
| UNFREEZE EVERYONE, EMPTY THE JAIL, ALL MY POWERS OFF | Buttons under the player list. |

**The jail** (the owner's "small room for funsey"):

- **The room:** `Map.DevJail`, built by the server the first time someone is sent there. It sits 420 studs over the hub's `Origin`, because anything 60 studs under it is the void.
  - It's a `ZonePiece`, so ZoneCull draws it only for whoever is near it.
  - Inside it's 22 x 12 x 18 studs, in quiet greys: bars across the front with a dark sealed corridor behind them, a bench with a rounded edge, a white ceiling light panel, and a small bright window behind glass. There's no text.
  - Every piece is solid and anchored, so walking, jumping and a grapple's ray all stop at the walls. The bars' gaps are 1.15 studs, narrower than a body.
- **Going in:** being sent there is a server move (`TeleportT`). The first 2.5 s put them back in if their client still reports the old spot.
  - A player sent from a match is taken out of it first (`Matches.pull`, as if they'd left). The match is flagged dev, so it counts for nothing.
- **Getting out:** whichever comes first:
  - 60 s pass (`JAIL_TIME`; the `DevJailed` attribute is the end time);
  - the owner frees them;
  - they join a party or a lobby;
  - they die, or anything else moves them out;
  - they leave the game.
- **Where they go:** a timed or freed release goes to their hub spawn (`Fight.spawnAt`). After a match, that's the hub, or their lobby's plinth if they're in a party.

## GIFT (the menu's second tab)

Asked for on 18 Nov: "let me gift people stuff! bundles, cases bags cans at any quantity coins vip etc".

- **Who gets it:** anyone in the server, or you (YOU is first in the list).
- **What, and the server call that gives it** (never the client; the server re-checks the creator on every gift):

| Kind | Server call |
|---|---|
| Crates, Duffel Bags, Spray Cans, 1 to 999 | `Loot.grant(p, id, receipt, n)`: one write, one receipt, past the free mode's stock cap of 10. The count is the loot module's (`Loot.GRANT_COUNT`, agreed with shop-gui); a client's "buy" stays capped. |
| A shop bundle or skin set, whole | `Loot.grant(p, bundleId, receipt)` |
| One item from the searchable list (skins, wraps, hats, kill effects, emotes, grapples, card looks) | `Loot.grant(p, "gift:<kind>:<id>", receipt)`. Wraps and hats go on every gun. |
| Coins (the game shows Brass as Coins; one currency, internal id brass) and Crate Tickets, any amount | `Quests.gift(p, brass, tickets, receipt)`. Not capped, logged in the quests save's grants, and not counted as earned, so a cheat restore leaves a gift alone. |
| VIP, for good | `Vip.gift(p, true)` (the shop's): saved on the player's key in `JankfireVip` |
| A Robux weapon (`Unlocks.ROBUX`: minigun, laser, chicken, akimbo), for good | On the UNLOCKS page since 19 Nov (below). The old `"weapon"` kind (`Purchases.giveWeapon`) still works for other code. |
| Account XP, or a level; weapon mastery XP, or a mastery level | `Stats.gift(p, what, receipt)` (XP and UNLOCKS, below) |
| One weapon with a lock, or UNLOCK ALL WEAPONS | `Purchases.unlockWeapons(p, wids, "gift", receipt)` (XP and UNLOCKS, below) |

- **The receiver** gets the present (below). In a match the present waits, and one plain line shows at the top of the screen for 3.5 s instead, such as "GIFT · 5 CRATES" or "GIFT · VIP" (DevFx "gift"). Containers land in their inventory to open as usual.
- **Who it's for:** TO also lists EVERYONE HERE and ALL SERVERS (since 19 Nov; see GIFT EVERYONE below).
- **Everyone in the server sees it in the chat** (since 18 Nov: the owner said "it has to be noticeable"). A gift to someone else posts one gold system line, such as "Pompompoo gifted Sam 5 Crates" or "... gifted Sam VIP".
  - The server builds the line from the two display names and the item's own plain name, never from anything typed.
  - Each client posts it: `ChatMakeSystemMessage` in this place's legacy chat, or a TextChatService system message if the place ever moves to it.
  - A gift to yourself posts nothing.
- **The receiver's present** (since 18 Nov; the owner: "a present box come up and appear, use squash and stretch, it comes up, spins and opens to reveal what you've received"; `client/GiftReveal.client.luau`).
  - **The box:** chunky and navy, with a gold ribbon and bow, in a ViewportFrame at the middle of the screen, under "GIFT FROM <giver>".
  - **The motion:** it pops up from below, squashed on arrival, stretched as it rises, and settles with an overshoot. Two wobbles, then a fast spin that slows. The lid pops off with a squash, a burst of light and confetti. The squash and stretch rescale the box's own parts in 3D.
  - **The reveal:** the loot opening's own cards (`LootOpening.card`, exported for this), with "x5" on a count, and a grid for a bundle.
  - **Sounds:** recorded ones from the library: `pop`, `slap_whoosh`, `loot_pop`, and `loot_win_<best rarity>`.
  - **Skipping and closing:** any key, click or tap jumps to the reveal. CLOSE, or B on a pad, puts it away (`Pad.MENUS.giftbox`).
  - **In a match:** it waits for the break between rounds (`LoadoutWindow`) or the hub, and the small toast says it came. It never plays over a live round or a loot opening.
  - **Self-gifts** play the present too (for tests), and stay silent in chat.
  - **Studio test hook:** `GiftHold` = "rise" / "spin" / "reveal" holds the animation at that moment for a photo.
- **The gift log:** every gift is written to DataStore `JankDevGifts_v1` (`JankDevGifts_v1_studio` in Studio), key `log`, last 500: when, giver, receiver (user ids only), what, how many. It's printed to the server log too.
- **In a match:** a gift works there and doesn't flag the match, because it doesn't change the fight.

## XP and UNLOCKS (GIFT tab pages, since 19 Nov)

Asked for on 19 Nov: "allow me to also give people xp, I want to be able to unlock stuff for my friends!!" Both pages work with every receiver on TO (a player, YOU, EVERYONE HERE, ALL SERVERS).

- **XP page, account:** GIVE XP adds any amount (1 to 10,000,000; quick 100 / 1,000 / 10,000 / 100,000). SET LEVEL (2 to 500) raises them to the start of that level. For one receiver the page shows their level and XP now.
- **XP page, weapon mastery:** pick a weapon (every live one). GIVE MASTERY XP adds any amount; SET MASTERY LEVEL (2 to 40, quick LV 10 GOLD / 20 DAMASCUS / 30 DIAMOND / 40 GALAXY) raises that weapon to it. For one receiver it shows that weapon's mastery now.
- **A level only goes up.** Below it, they're raised to it. At it or past it, nothing happens ("they're past that already"). So SET LEVEL to everyone never lowers anyone.
- **The normal level system does the rest:** it's the same XP a match gives (`Xp` / `Level` attributes), so the level-up toast and the weapons a level opens come as usual (`UnlockClient`). Mastery goes through `MasteryXp.add` (the weapon-mastery session's call): its level toast, and the camos at their levels (Gold 10, Damascus 20, Diamond 30, Galaxy 40) through `Loot.grant` once each.
- **Never ranked:** the XP never goes on a match's log (`cur.xp`), so a cheat restore for someone else doesn't take it, and ranked (`RankedData`) never sees it. A cheat restore *of* the receiver resets their XP like any other.
- **Exactly once:** `Stats.gift` keeps the receipt in the stats save (`data.gifts`, the last 200 ids) next to the XP, so both go in the same write. A gift-everyone event uses `ownerev-<id>` as for the rest.
- **UNLOCKS page:** UNLOCK ALL WEAPONS, then a list of every weapon with a lock: the 4 premium ones first (PREMIUM), then each level one by its level. UNLOCK opens one. For one receiver each row says THEY HAVE IT, LOCKED FOR THEM, or OPEN (DEV UNLOCK).
- **How an unlock is kept:** `Purchases.unlockWeapons` writes `data.weapons[wid] = { how = "gift" }`, the same record an early coin unlock leaves. It's in `RobuxOwned`, which `Unlocks` treats as open whatever the level. All of them go in one write; ones they have are skipped; nothing is ever taken away. UNLOCK ALL covers the weapons live at the time; a weapon added later stays locked until it's unlocked too.
- **The present:** an XP card ("XP" or "LV 12" in big gold letters), a mastery card (the weapon as the loadout shows it, with "LV 10" or "+5,000"), or a weapon card (the weapon) for an unlock, "ALL" for every weapon. The chat line reads "Pompompoo gifted Sam Level 12", "... gifted Sam AR Mastery 10", "... gifted Sam Minigun", "... gifted everyone every weapon".
- **Never the OWNER title:** `GiftFx.describe` refuses it ("the OWNER title stays yours alone"), and `Stats.owns` would refuse to put it on anyone else anyway.
- **The VIP page** no longer lists the Robux weapons (they're on UNLOCKS).

## FRIENDS: lend the powers (TEMP DEV, the menu's fourth tab, since 19 Nov)

Asked for on 19 Nov: "allow me to temp give command panel to friends exclude the gifting portion of it".

- **The tab (owner only):** every player in the server, with 15 MIN / 30 MIN / 1 HOUR / UNTIL THEY LEAVE, their state ("DEV UNTIL 21:45", "DEV UNTIL THEY LEAVE"), REVOKE for a friend who has it, and REVOKE ALL. Lending it again sets the new time.
- **Held by the server's memory only, never saved.** It ends at its time, when they leave, when the server closes, or on REVOKE / REVOKE ALL. Only the place's creator can lend it (checked on the server for every command); a friend never can.
- **What a friend gets:** the POWERS tab only, opened the same way (F8, `/dev`, the DEV button): fly, noclip, run speed, invisible, weapons in the hub, and fling, freeze, go to, bring, jail, red card (the AIM KEYS too).
- **What a friend never gets** (the server refuses it by who sent it, `TEMP_OPS`, not just by the hidden tabs): GIFT with XP and UNLOCKS, anything that changes saves or money, ANNOUNCE, the anti-cheat panel (its kicks and bans stay the owner's), lending, UNFREEZE EVERYONE and EMPTY THE JAIL (they'd undo the owner's too). Refused: "the owner's only".
- **The owner is protected:** a friend can't fling, freeze, bring, jail, red-card or go to the owner ("not the owner"), can't touch another friend with dev ("not another dev"), and can't let go or move someone the owner froze or jailed ("the owner is holding them"). Their dev weapons can't hurt the owner or another friend (`Matches.devHit`).
- **The same safety as the owner's use:** a match a friend's power touches counts for nothing (`m.dev`); the anti-cheat's `devOn` covers them while it lasts (`DevTemp`, which only OwnerDev.server writes); every command they use is in the server log as `[dev temp] <name> ...` and in the anti-cheat panel's log (kind `tempdev`, "(temp dev from <owner>)"), with the lending and the end too. No OWNER title for them.
- **What they see:** one plain line at the top as it starts and ends ("DEV ACCESS UNTIL 21:45 · F8", "DEV ACCESS ENDED"), and the menu's status line says "DEV ACCESS UNTIL 21:45". When it ends, every power goes off, the people they froze go free, the menu shuts and the DEV button goes; lent again, it comes back.
- **Attributes:** `DevTemp` on the friend = the `os.time()` it ends, or 0 = until they leave.

## GIFT EVERYONE

Asked for on 19 Nov, with ANNOUNCE: "from my command menu allow me to gift everyone stuff and write announcements that go across the screen across all servers, it'll be helpful for admin abuse!!"

- **Where:** on the GIFT tab, pick EVERYONE HERE (this server) or ALL SERVERS (every live server) at the top of TO, then any gift button: containers in any number, bundles, items, coins, Crate Tickets, VIP, Robux weapons.
  - ALL SERVERS asks for a second press of the same GIVE within 5 s.
- **Who gets it:** the players in the server right then, once each. Anyone who joins later gets nothing, because it's a live event. The tab says so under the list.
- **How it travels:** an event `{ id, k = "gift", by, from, kind, item, qty }`.
  - "This server" plays it here.
  - "All servers" publishes it once over MessagingService (topic `JankOwnerEvent`; `JankOwnerEvent_studio` in Studio, so a test never reaches a live server), and every live server plays it.
  - Only this game's own servers can publish to the topic, and only the owner's command does. A server plays only events whose `by` is the place's creator, and each event id only once.
  - If the publish fails on a live server, nothing happens anywhere, and the menu says so.
- **Exactly once per player:** each player gets it under the receipt `ownerev-<id>`.
  - Loot's receipts (`Loot.hasReceipt`, new) and Quests' grant ids make a second delivery, a retry, or a player who hopped servers give nothing.
  - VIP they already have, or a Robux weapon they own, is skipped.
  - A save still loading is tried again every 3 s for a minute.
- **What people see:** each player gets their present (at the break in a match). Each server gets one chat line, such as "Pompompoo gifted everyone 3 Crates".
- **Limits:** one gift-everyone every 5 s.
- **Reach and the log:** each server adds itself and the players it gave to a MemoryStore hash map (`jf_ownerev`, or `jfs_ownerev` in Studio, kept a day).
  - 75 s later the owner's server reads it, prints it to the dev log, writes the event to the gift log (key `events`, last 200: when, id, kind, scope, what, servers, players), and toasts the owner: "GIFT EVERYONE · 12 SERVERS · 84 PLAYERS".

## ANNOUNCE (the menu's third tab)

- **The tab:** a text box (up to 120 letters, with a counter), SEND TO THIS SERVER, and SEND TO ALL SERVERS (asks for a second press within 5 s).
- **Roblox's filter first:** the owner's server runs `TextService:FilterStringAsync(text, owner, Enum.TextFilterContext.PublicChat)`, then `GetNonChatStringForBroadcastAsync()`, before anything is sent or shown.
  - If the filter doesn't answer, nothing is sent, and the menu says so.
  - If the filter changed words, the menu says that too.
  - Only the filtered text travels, shown as plain text (never rich text).
- **How it travels:** the same events as GIFT EVERYONE (`k = "announce"`, `text`), here or over MessagingService to every server, each id once.
- **What everyone sees:** `client/AnnounceBanner.client.luau`.
  - A dark band sweeps in across the screen between two gold lines. "ANNOUNCEMENT · <OWNER>" and the line ride in from the right and land in the middle.
  - It holds about 6 s (a long line a little longer), then the line rides off to the left and the band follows.
  - Outside a match: a big band in the upper third, with up to 30 px text, shrunk to fit.
  - In a match: a slimmer band high on the screen, well clear of the crosshair, with up to 21 px text.
  - Sounds: `slap_whoosh` as it sweeps in, `ting` as the line lands. One at a time, with at most 3 waiting.
  - The chat gets the same line in gold: "[ANNOUNCEMENT] Pompompoo: <text>".
- **Limits:** one announcement every 10 s.
- **Reach:** reach, log and toast as for GIFT EVERYONE ("ANNOUNCEMENT · 12 SERVERS · 84 PLAYERS").

## For other code: GiftFx (the shared gift look)

`server/GiftFx.luau` is what a gift looks like to people, for anything on the server that gives something. The shop's paid gifts can use it. It gives nothing itself; call it after the owning module (Loot, Quests, Vip, Purchases) has answered yes.

| Call | What it does |
|---|---|
| `GiftFx.describe(kind, id, n) -> spec?, why?` | Names a giftable thing and builds its present cards. kind: `"container"` (id crate / bag / spray, n 1 to 999), `"bundle"` (a shop bundle or skin set id), `"item"` (id `"<type>:<id>"`), `"brass"` or `"coins"` (n 1 to 1,000,000), `"tickets"`, `"vip"`, `"weapon"` (a Robux weapon). Since 19 Nov also `"xp"` (n XP), `"level"` (n the level), `"mastery"` (id a weapon, n XP), `"masterylevel"` (id a weapon, n the level): spec.kind `"xp"`, `spec.stats` = what `Stats.gift` takes. `"unlock"` (id any weapon with a lock) and `"unlockall"`: spec.kind `"unlock"`, `spec.ids` for `Purchases.unlockWeapons`. The OWNER title is refused. spec = `{ kind, id, qty, label = "5 CRATES", plain = "5 Crates", items, what }`. |
| `GiftFx.lockable(wid)`, `GiftFx.lockables()` | A weapon with a lock (live, and Robux or past level 1), and all of them in roster order. |
| `GiftFx.present(to, fromName, spec)` | The receiver's present box (GiftReveal.client). In a match: the toast now, the present at the break. |
| `GiftFx.say(byName, toName, what)` | "<by> gifted <to> <what>" as a gold system line in this server's chat, for everyone. Use display names and `spec.plain`, never typed text. |
| `GiftFx.line(text)` | Any gold system line (announcements use it). Typed text must be filtered first. |
| `GiftFx.remote` | The RemoteEvent all of it goes through (`JankfireRemotes.DevFx`, made by GiftFx). |

## Nothing counts

- **Saves:** no power or command writes anyone's saves, stats, rank, quests, currency or loot. GIFT is the one exception, and it only ever adds.
- **Damage:** the owner's dev weapons can hurt players outside a match (`Matches.devHit`). Stats and quests only count hits in live matches, so those hits are never counted.
- **Kills:** a kill outside a match by the owner (a dev weapon, or a fall after a fling) goes through `Fight.devKill`. It shows no kill feed, runs no kill hooks (stats, quests, kill effects, finishers), and the kill and death counts are taken back. The victim respawns in the hub 1 s later.
- **Victims and the anti-cheat:** victims of a fling, bring or freeze get the anti-cheat's usual pass for a server move (`ACGrace`, `TeleportT`), the same as a TV Remote rewind. They do not get the owner's dev exemption.

## The anti-cheat

- **The flag:** `AntiCheat.server`'s `devOn(p)` is true only while `DevOn` is set and the player is the place's creator.
- **While it's on:**
  - No movement checks run.
  - A verdict "dev powers on: movement not checked" shows as the owner's last line in the F7 panel.
  - The owner's aim flags are written with a `[dev]` prefix.
- **When it goes off:** the checks start afresh from wherever the body is, after a 1 s grace.

## The OWNER title

- **Data:** CardStyles title `owner`, words "OWNER", rarity `owner`.
- **Look:** a warm gold, with a slow white light running across the words. One pass takes 3.5 s, followed by 2 s still (`CardStyles.styleTitle`).
  - The same look appears over the head (`OverheadTitles`), on the player card and its list (`ProfileUI`), and in the picker's sample.
- **Only the creator can wear it.** `Stats.owns` asks for the creator id, whatever any save, grant or Studio unlock says.
  - It is put on for the creator once, on their first visit after it came (`ownerTitle` in their stats save). They can take it off like any other title.
- **It can never be sold, rolled, bundled or granted.**
  - `CardStyles.isSecret` covers it, which keeps it out of the shop's singles, bundles and rotation.
  - `forSale` leaves it out, and the loot tables never roll a rarity they don't know.
  - The card's picker hides it from everyone else.

## Studio tests

- **Server script attributes:** `TestNotOwner = true` on `ServerScriptService.Jankfire.OwnerDev` makes the owner a stranger, so every command is refused.
- **`ServerStorage.JankDev`** (Studio only) answers:
  - `"state"`: the owner's switches, who's frozen, and the log.
  - `"as"` (player, op, a, b): runs a command as that player.
  - `"log"`: the log.
  - `"giftLine"` (giver, name, what): a gift's chat line to a stand-in name.
  - `"event"` (an event table): plays it as another server would on receiving it (each id once).
  - `"forget"` (an event id): this server forgets it played that id, as a server that never had it would.
  - `"events"`: how many events came in over MessagingService, and the ids played here.
  - `"grant"` (player, minutes or 0, seconds?): TEMP DEV on that player as if the owner lent it (seconds: a short one to see it run out). With `TestNotOwner` on, the Studio player is the friend. `"revoke"` (player), `"temps"` (who has it, and how long is left).
  - A training dummy with the attribute `DevStandIn = "owner"` or `"temp"` stands in for the owner or another friend with dev, for the refusals.
- **Client:** the player attribute `DevMenuTest` = `"open"`, `"close"`, `"gift"`, `"announce"` or `"friends"` opens or closes the menu, or opens it on that tab. `AnnounceTest` = a text shows the banner on your screen only; `AnnounceHold = true` holds it there.
- **Commands from the Client datamodel:**
  ```lua
  game.ReplicatedStorage.JankfireRemotes.OwnerDev:InvokeServer("set", "fly", true)
  ```
  Other ops: `"players"`, `"fling"` / `"freeze"` / `"goto"` / `"bring"` with a Player or a dummy Model, `"flingAim"` / `"freezeAim"` with a look vector, `"unfreezeAll"`.
- **A match:** `ServerStorage.JankMatchTest:Invoke("ghost", "<pad>", nil, 30, player)`.
- **The anti-cheat in Studio:** set `StudioOn = true` on `ServerScriptService.Jankfire.AntiCheat` to switch it on.

## Test results

**Round 1, place version 943** (solo Play, a training dummy as the stand-in):
- Fly holds its height exactly with nothing pressed. Noclip turns the body's parts non-colliding.
- With dev powers on, a 60-stud client jump scored 0 points; the panel's verdict was "dev powers on".
- The stand-in was brought to the hub, flung 30 studs up in 0.45 s, and frozen mid-air.
- WEAPONS in the hub: the TV Remote went into the try layer (`Trying`), and its pause froze the stand-in. The rewind fired, but the stand-in had stood still, so it didn't move.
- `TestNotOwner` made every command "owner only".
- A ghost match with the player: a power worked, and the match was flagged (`MatchDev` set).

**Round 2, place version 950:**
- A red card on the stand-in: the card was in the owner's hand with the arm at 172 degrees. The stand-in was in the jail 1.2 s later with its 60 s running.
- The jail is sealed: rays out of its middle hit the walls on all four sides and the ceiling.
- Invisible, as the server sees it (and so everyone else): 25 of 25 body parts fully hidden and the name off. The owner's own head showed at 0.72, a ghost. Switching it off brought everything back: 1 of 25 hidden (the root, as before) and the name back.
  - The first try at switching it off left the body hidden. The kept values sat in a weak-keyed table, and Roblox can drop Instance keys from one while the parts still exist. Fixed with a strong table, plus the `DevWas` fallback.

**Not tested yet:**
- On a second real player: fling, freeze, jail and the red card on a player rather than a stand-in, jailing someone out of a real match, and invisible as seen from another client.

**Photo turn, 17:12 UTC (no code change):**
- A stand-in sent to the jail came out at 60 s and stood back at its home spot.
- The player card shows OWNER in gold under the name. The overhead OWNER title shows in gold.
- A second stand-in flung and frozen 28 studs up.
- Studio's Play-mode `screen_capture` camera won't frame your own avatar, so these were shot through a held Scriptable camera. The red-card pose was only caught from behind.

**Photos:** `docs/owner-dev/`:
- `menu_v950.jpg`
- `jail_v950.jpg`
- `red_card_flash_v950.jpg`
- `owner_title_card.jpg`
- `owner_title_overhead_red_card.jpg`
- `fling_frozen_midair.jpg`

**GIFT, place version 1015** (solo Play on the owner's `_studio` saves):
- Gifted to yourself: 3 Crates (stock 0 → 3), the Night Shift bundle, a kill effect, 500 Brass and 2 Crate Tickets. Each answered ok and showed its toast; the HUD showed the Brass and tickets.
- VIP and Robux weapons answered "not in yet": they wait for the shop's `Vip.gift` and `Purchases`, coming with its next install.
- Afterwards the three saves (loot, quests, VIP) were put back exactly from a snapshot taken before Play, and an uncached read-back compared equal.
- Containers go one grant per box (at most 25 at a time) until the loot module takes a count (`Loot.GRANT_COUNT`).
- Photo: `gift_tab_v1015.jpg`.

**GIFT round 2, place version 1026:**
- 50 Crates and 12 Duffel Bags landed in one write each, past the free mode's stock cap of 10.
- "Coins" gave 500 Brass.
- VIP and a Robux weapon answered "not in yet": shop-gui's `Vip.gift` and `Purchases` weren't installed in Studio yet.
- The owner's `_studio` saves were restored exactly afterwards.

**GIFT round 3, place version 1030** (after shop-gui's v1029 install):
- A Robux weapon gift landed (the minigun, `RobuxOwned`).
- 250 coins landed with "GIFT · 250 COINS".
- VIP: "already VIP" for an owner who is VIP. With Vip's Studio dev lock on, the gift made them VIP.
- The loot, quests, VIP and purchases `_studio` saves were restored exactly afterwards.

**GIFT present and chat line, place version 1042:**
- 3 crates gifted to yourself played the present: rise, spin, then the Crate card with x3. Photos: `gift_present_rise.jpg`, `gift_present_spin.jpg`, `gift_present_reveal.jpg`.
- The chat line to a stand-in name showed in gold: "Pompompoo gifted TestFriend 5 Crates". The self-gift posted nothing.
- **Not tested yet:** a bundle's grid, a gift held back during a match, and closing with B on a pad.

**GIFT EVERYONE, ANNOUNCE, body size, AIM KEYS: place version 1054** (one solo Play on the owner's `_studio` saves, 19 Nov):
- **The bundle present:** Night Shift revealed 5 cards in a row, under "GIFT FROM POMPOMPOO". B on a pad (PadNavTest "back") closed it in the hub. Photo: `gift_present_bundle.jpg`.
- **EVERYONE HERE:** 1 crate, stock 0 → 1.
  - The same event id played again (as a second delivery) was refused: "already".
  - With this server made to forget the id (as a server the player hopped to), the event played again and gave nothing: the receipt held, and the stock stayed at 1.
- **ALL SERVERS:** the publish came back over MessagingService (`JankOwnerEvent_studio`) in 1.3 s. The echo was ignored, and the stock went up by exactly one (1 → 2).
- **ANNOUNCE:** "one every 10 s" refused a second send at once.
  - The hub banner shows big in the upper third, and the match banner slim and high, under the score bar and clear of the crosshair. Photos: `announce_hub.jpg`, `announce_match.jpg`.
  - The filter ran: in Studio it returns the text as typed.
- **Body size:** the owner's own R15 body spawned with standard scales and its root 3.00 studs over the feet (the hit box's feet 0.04 studs off the real ones).
  - A tiny stand-in (scales 0.5): root 1.60 → 3.00 studs; its box's feet went from 1.40 studs below its real feet to 0.00.
  - A huge stand-in (height 1.6, rthro body type): root 5.83 → 3.00; its box's feet went from 2.83 studs above its real feet to 0.00. Both ended with standard scales.
- **In a match:** a present plays in the pre-round loadout window (a break, by design).
  - **Found:** one that started there stayed up when the round went live, because the reveal waits for CLOSE. In that match, B didn't close it either; most likely the match's own menus take B first (not checked).
  - Fixed in place version 1060: a present that's up when the round goes live is put away at once, and plays again at the next break if its cards weren't shown yet. Tested: a present begun 1 s before the round went live was hidden as the round started; at the next break it played again and reached its cards.
- The loot and quests `_studio` saves were restored exactly afterwards (uncached read-back, compared key by key).
- **Not tested:** the AIM KEYS toggle by hand (it's a local switch on the key handler, compiled in v1054), and anything across two real live servers (the reach count and the toast come 75 s after an event).

### 19 Nov, place version 1079: XP, UNLOCKS and FRIENDS (one solo Play, the owner's `_studio` saves)

- **The push:** one guarded package, 7 scripts (OwnerDev server and client, GiftFx, Stats, Purchases, GiftReveal, AntiCheat): all 44 pairs found in Studio's own text and compiled before anything was written.
- **XP:**
  - GIVE XP 5,000 took the owner from 22 XP (level 1) to 5,022 (level 12).
  - SET LEVEL 12 after that answered "they're past that already", and so did SET LEVEL 5: a level only goes up.
- **Mastery:** SET MASTERY LEVEL 10 on the Redline (it had none) made it level 10. The Gold camo was granted on its own (`mastery_gold@redline`). The present showed the Redline with "LV 10". Photo: `gift_mastery_card.jpg`.
- **Unlocks** (with the owner's dev unlock off, so the locks were real):
  - The Minigun (premium) and the Shopping Cart Cannon (level 25) were locked before and open after (`RobuxOwned` = "cart,minigun").
  - UNLOCK ALL to EVERYONE HERE took the owned weapons from 2 to 46. Replaying the same event id gave nothing (46 stayed 46).
- **XP to everyone:** +100 (5,022 → 5,122). Replaying the same event id gave nothing.
- **The OWNER title** as an item gift: refused, "the OWNER title stays yours alone".
- **FRIENDS** (the Studio player made a stranger with `TestNotOwner`, then lent dev for 40 s):
  - **Before the loan:** "owner only".
  - **During it:** hello answered temp, with its end time. Fly, noclip, weapons and invisible all switched on, with `DevOn` set. On a dummy, fling, go to, bring, freeze and let go, jail and free, and red card all worked.
  - **Refused:**
    - The owner's stand-in dummy: "not the owner".
    - Another friend's stand-in: "not another dev".
    - GIFT, GIFT EVERYONE, ANNOUNCE, lending, REVOKE ALL, UNFREEZE EVERYONE and EMPTY THE JAIL: "the owner's only".
  - **Their menu:** POWERS only, with no GIFT, ANNOUNCE or FRIENDS tab and no UNFREEZE EVERYONE or EMPTY THE JAIL. The status line read "DEV ACCESS UNTIL 18:12". The owner's and the friend's rows showed OWNER / DEV with their buttons greyed. Photo: `tempdev_menu.jpg`.
  - **Every command** went in the server log as `[dev temp] ...` and in the anti-cheat log as `tempdev`, with who lent it.
  - **The timer:** at 40 s the loan ended. `DevTemp` went, fly went off, and `DevOn` was gone 3 s later. The next command answered "owner only". Their screen showed "DEV ACCESS ENDED", and the menu and the DEV button went.
  - **Lend and revoke:** lending 15 min set `DevTemp`; REVOKE took it away.
- The stats, loot and purchases `_studio` saves were restored exactly afterwards (uncached read-back, compared key by key). `TestNotOwner` was cleared before the save.
- **Not tested:**
  - "The owner is holding them". A friend freeing someone the owner froze needs two real players.
  - The FRIENDS tab's buttons by hand. The server ops behind them were tested.
  - A loan across a real live server with friends.
