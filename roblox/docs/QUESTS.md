# Daily quests, Brass and the weekly track

The owner, 17 Nov 2026: "Add daily quests for rewards!! Rivals has keys so we can't use that but maybe a different
currency and weekly rewards grant you a case or maybe tickets to eventually redeem a case? I don't want to be too too
charitable".

## 1. What it is

- **Brass** is our own soft currency (spent shell casings). It is not a key, and it never buys a Crate. Only quests
  and the weekly track pay it, for now. It buys a Spray Can or a Duffel Bag in the shop.
- **Crate Tickets** come only from the weekly track. They redeem containers in the shop: 12 for a Crate, 6 for a
  Duffel Bag, 3 for a Spray Can.
- **Daily quests:** three a day: one easy, one medium and one hard. New ones come at 00:00 UTC, and you get one free
  reroll a day.
- **The weekly track:** every finished quest adds points to a weekly bar (easy 1, medium 2, hard 3). The bar pays
  Brass and Crate Tickets at its steps. It starts again on Monday 00:00 UTC.
- Nothing here gives anything VIP: containers never roll VIP things (`LootTable.vipOnly`).

### Why these choices

- **The name Brass:** a gun game's casings, short, and no clash with Rivals' keys. A second currency was weighed
  against the alternative, quests paying tickets straight away. Two currencies keep the Crate rare: tickets are
  scarce and slow, Brass is the everyday one.
- **One quest per tier:** every day has something quick, and the hard one is where the points are. A random mix of
  tiers would make some days worthless.
- **Rewards are paid on completion:** there is no claim button to forget. A toast says what you got.
- **Not too charitable:** the Crate is only reachable through tickets. A player who does every quest every day gets
  one about every 19 days; a regular player about every 7 weeks; a casual one about twice a year (section 3).

## 2. The numbers (`src/shared/QuestData.luau`)

| tier | Brass | weekly points | pool |
|---|---|---|---|
| easy | 30 | 1 | 11 quests |
| medium | 50 | 2 | 16 quests |
| hard | 80 | 3 | 14 quests |

41 quests in all. A full day pays 160 Brass and 6 points; a full week pays 42 points, and the bar fills at 40.

The weekly steps:

| points | reward |
|---|---|
| 3 | 75 Brass |
| 6 | 1 Crate Ticket |
| 10 | 100 Brass |
| 15 | 1 Crate Ticket |
| 21 | 150 Brass |
| 28 | 1 Crate Ticket |
| 34 | 200 Brass |
| 40 | 2 Crate Tickets |

So a full week gives 5 tickets and 525 Brass on top of the quests' 1,120.

Shop prices (`QuestData.PRICES`):

| container | Crate Tickets | Brass |
|---|---|---|
| Crate | 12 | not for sale |
| Duffel Bag | 6 | 2,500 |
| Spray Can | 3 | 1,000 |

## 3. The economy, simulated (`tools/roblox/quest_econ.mjs`)

Run it with `node tools/roblox/quest_econ.mjs 5000 52`: 5,000 players of each kind over 52 weeks.

What each kind of player does:

| kind | plays on | finishes easy | finishes medium | finishes hard |
|---|---|---|---|---|
| casual | 2 days a week | 85% | 45% | 12% |
| regular | 65% of days (4.6 a week) | 95% | 75% | 40% |
| grinder | every day, every quest | 100% | 100% | 95% |

The reroll swaps away the hard quest, giving it a little more chance. Results (17 Nov 2026):

| kind | quests a day | Brass a day | tickets a week | full weeks | days per Spray Can (Brass) | days per Duffel Bag (Brass) | days per Crate (tickets) |
|---|---|---|---|---|---|---|---|
| casual | 0.45 | 29 | 0.41 | 0% | 35 | 87 | 204 |
| regular | 1.43 | 99 | 1.75 | 0% | 10 | 25 | 48 |
| grinder | 2.95 | 231 | 4.42 | 71% | 4.3 | 11 | 19 |

The best a week can give is 1,645 Brass and 5 tickets: a Crate every 2.4 weeks and a Spray Can every 4.3 days on
Brass. A Spray Can comes often, a Duffel Bag sometimes and a Crate rarely, as the brief asked.

**VIP players** also claim the VIP daily reward (Trisangle in the VIP room, the shop session's
`VipDailyData.TABLE`, one claim a day). Its odds come from the shop session on 17 Nov, with the main session's
decision the same day: the Crate went from 2% to 1%, and the freed 1% went to the Spray Can.

| prize | chance |
|---|---|
| 40 Brass | 42.4% |
| 100 Brass | 27.3% |
| 250 Brass | 11.1% |
| Spray Can | 13.1% |
| Duffel Bag | 5.1% |
| Crate | 1.0% |

Brass is paid through `Quests.giveBrass` (section 6b); containers go straight into stock. Assuming the VIP claims on
the days they play, every source counted together (Brass prices, tickets, the daily's own containers):

| kind | Brass a day | days per Spray Can | days per Duffel Bag | days per Crate |
|---|---|---|---|---|
| casual + VIP | 50 | 11.5 | 27 | 132 |
| regular + VIP | 147 | 4.2 | 9.7 | 36 |
| grinder + VIP | 302 | 2.3 | 5.8 | 16 |

**Days to a Crate**, with and without VIP:

| kind | without VIP | with VIP |
|---|---|---|
| regular | 48 | 36 |
| grinder | 19 | 16 |

The daily roughly doubles a VIP's Spray Cans and Duffel Bags: a fair perk. At 1% its Crate cuts a quarter off a
regular VIP's wait, and a grinder stays above two weeks. The 2% first planned would have taken a regular VIP to 27
days and a grinder to 14.

Ticket redeems instead of Brass: a Spray Can costs 3 tickets, a quarter of a Crate. A grinder could take a Spray Can
every 5 days from tickets alone, but then never reaches a Crate.

## 4. What counts (`src/server/Quests.luau`)

The server counts everything; the client only shows it. **Only real matches count:**

- Both players are in the same match, on opposite teams, and the round is live: the same rule as the player cards'
  stats (`Stats.luau`). Hub fights, training dummies, the back lot and Studio ghost matches never count.
- **No AFK:**
  - A match counts towards "play" and "win" quests only if you took part: you hurt an enemy at least once, or got a
    kill.
  - A round counts towards "win rounds" only if you hurt an enemy in that round.
  - Leaving a match counts nothing.
- **Weapons:** only live Roster weapons and items count (`Roster.byId[w].live`), never a test hook's made-up "test".
- **The range quests** are the one exception to "matches only". They use Cardboard Carl's: one run's score on a plate
  is counted on the server by `RangeTest`, through its `onRun` hook. Its kill rules keep it honest: only the runner,
  nobody faster than 0.12 s. A range run can't be farmed by standing still.

The counters (`stat` in the pool):

| stat | what the server sees |
|---|---|
| `kill` | a kill on an enemy player (a void kill counts with the weapon that knocked them off) |
| `kill:<group>` | the same, with a weapon of that group (`QuestData.CLASSES`: auto, marksman, shotgun, side, sniper, smg, katana, shredder, item) |
| `hskill` | a kill whose last hit was a headshot, within 2 s |
| `slidekill` | the killer's character `Pose` is `slide` at the kill (`PoseRelay`) |
| `grapplekill` | the killer is on the grapple (hooked and not let go), or let go less than 1.5 s ago (the `Grapple` remote) |
| `voidkill` | a kill by knocking someone off the map (`w = "void"` with a killer) |
| `longkill` | a Sniper kill from 40 m (120 studs) or more |
| `hs` | a headshot hit on an enemy player |
| `dmg` | damage dealt to enemy players |
| `item` | an item use in a live round (the server's `ItemN` count going down: `Utility.luau`) |
| `streak` | kills in a row without dying in one match (the best counts) |
| `round` | a round your team won, if you hurt an enemy in it |
| `play` / `win` | a match finished / won, if you took part |
| `flawless` | a match won where no other team took a round |
| `ranked` / `rankedwin` | the same for ranked matches (`Matches` `m.ranked`) |
| `party` | a match finished while you were in a party of two or more (`Party.sizeOf`) |
| `range:<plate>` | one range run's score on Easy (CHILL), Medium (NORMAL) or Hard (SWEATY): the best counts |

## 5. The save

The save is its own session-locked store through `Profiles.luau`, the layer the loot and stats saves use:
`JankfireQuests_v1`, or `JankfireQuests_studio` in Studio, so tests never touch live players.

```
{ v, brass, tix,                       -- the wallet
  day, list = { { id, n, done } x3 },  -- today's quests and their progress
  rolls, avoid,                        -- rerolls used today, ids not to roll again today
  week, pts, got,                      -- this week's points, steps paid
  earned = { [day] = { b, x } },       -- what quests and steps paid, per UTC day (60 days): what a cheat restore takes back
  owed = { b, x },                     -- a restore took back more than was left: future pay goes here first
  pending = { [id] = { kind, cur, price, t } },  -- a redeem between "paid" and "granted" (section 6)
  nextId, voids, backup, total = { quests, brass, tix } }
```

## 6. Redeeming in the shop

The loot session owns containers and the shop session owns the shop screen. The path:

1. The shop shows each container's ticket price, and its Brass price if it has one, next to its Robux price. It shows
   the wallet from the player attributes `Brass` and `CrateTickets`.
2. A press calls `JankfireRemotes.Quests:InvokeServer("redeem", kind, "tix" | "brass")`.
3. The server checks the price and the balance. It takes the price and writes a pending entry, then saves the quest
   save (this must succeed). Then it calls `Loot.grant(player, kind, "q<userId>-<n>")`.
4. `Loot.grant` puts one container in stock and is idempotent by that id. On success the pending entry goes. On
   failure the price comes back.
5. A crash between steps 3 and 4 leaves the pending entry. On the next join the server calls `Loot.grant` again with
   the same id: either it was already granted (true, nothing doubles) or it is granted now. So a container is never
   both lost and paid.
6. While `Config.LOOT_FREE` keeps containers free, `Loot` caps stock at 10. A redeem is refused when you already have
   10 of that kind ("open some first"), so tickets are never spent into the cap.

The answer is `{ ok, why?, stock, state }`. The shop then opens the container the usual way, from stock.

## 6b. Brass from other modules (the VIP daily reward)

- `Quests.grant(player, amount, reason, id?)` returns `(ok, why?)`:
  - It pays Brass only. Crate Tickets come from the weekly track and nowhere else.
  - It is written to the save before it answers true. A failed save takes it back and answers false, `"couldn't save"`.
  - It is idempotent by `id`: the same id twice pays once, and the second call answers true, `"already"`.
  - It is capped at `Quests.GRANT_DAY` (300) Brass a UTC day per player, across all callers.
  - It is logged: the save keeps the last 50 grants, and the output prints each one.
  - What it pays counts as earned that day, so a cheat restore takes it back too.
  - `false, "loading"` means the save isn't loaded yet: try again on the next join, with the same id.
- `Quests.giveBrass(player, amount, receiptId)` returns a boolean. It is the shop's VIP daily call, the same as
  `grant(..., "vip daily", receiptId)`.
- The player attributes `Brass`, `CrateTickets` and `QuestsDone` are set on every player at join, 0 until the save
  loads. `QuestSave` says when it has.

## 7. Cheaters

`Quests.restoreFor(userId, since)` is what the anti-cheat calls, with the same shape as `Stats.restoreFor` and
`RankedData.restoreFor`. Everything quests and steps paid from the UTC day of `since` onwards comes off the wallet.
What was already spent becomes `owed`, and future pay clears that first. Quest progress stops for them in this server.

- A player in this server is fixed at once.
- An offline player gets a pending entry in `JankfireQuestsFix_v1` (`_studio` in Studio), applied on their next join.
  A MessagingService nudge (`JankQuestsFix`) reaches the server that has them now.
- `Quests.undoRestore(userId)` gives it all back if the catch was wrong.
- Both are idempotent: a restore runs once per `since`.

Containers already opened stay opened. Taking items back is the loot module's call, and the owed tickets already make
a cheater earn them twice.

## 8. The screen (`src/client/QuestUI.luau`, `QuestClient.client.luau`)

- **U** or the QUESTS button opens the panel. The button sits in the hub's button column, over PLAY.
- **The panel:** three quest cards (tier, name, which weapons count, a progress bar, Brass and points, REROLL), the
  weekly bar with its steps and rewards, the wallet, and the time to the next reset. OPEN SHOP goes to the
  containers.
- **The wallet chip:** Brass and tickets in the top-right corner, in the hub.
- **A toast:** a short plate at the top when a quest finishes or a weekly step pays.
- **Look:** Theme's plates, one amber accent, quest names only and no flavour text (the owner's rule). The Brass and
  ticket icons are drawn from frames: no uploads.
- **Phone** (agreed with the touch-controls session): when the player attribute `TouchOn` is true, `TouchControls`
  moves the one child of `PlayerGui.JankQuestsButton.Scaled` (the button) into its right-hand stack, and the wallet
  (its own ScreenGui, `JankQuestsWallet`) moves down to y 58, under the EMOTE / SETTINGS pills. The tap on the moved
  button opens the panel; there is no extra phone button. `QuestUI.open()` / `toggle()` is the API.

## 9. Test hooks (Studio only)

`ServerStorage.JankQuestTest` (BindableFunction):

- `("count", on)` makes Studio ghost and held matches count, and waives the took-part rule for them. It is off by
  default, so other sessions' tests never touch quests.
- `("ghost", dummyName)` makes that dummy count as an enemy player while the test player is in a match. `""` turns it
  off.
- `("hit", player, dummyName, dmg, weapon, headshot)` is a real `Fight.hurt` from the player on that dummy. A kill
  goes through `Fight.onKill` like any other.
- `("set", player, slot, questId)` puts a quest in a slot.
- `("bump", player, stat, n)` adds to a counter.
- `("data", player)`, `("put", player, data)` and `("reset", player)` read, put back or reset the save.
- `("clock", secs)` moves the quest clock, to test the day and week resets.
- `("restore", uid, since)` and `("undo", uid)` run the cheat calls.

The client has the player attribute `QuestTest`: `open`, `close`, `toast`, `fake:844x390` (a phone-sized box) and
`real`.

## 10. State (17 Nov 2026, place version 544)

Live in Studio and saved: QuestData, Quests, QuestServer, QuestUI, QuestClient, the remotes `Quests` / `QuestPush`, and
the `RangeTest.onRun` hook. Code pushes were Open Cloud models `jf_push_quests_1..3` (91381068390597, 99913709052116,
80363362067463), with no images uploaded. The icons are frames.

**Tested in one solo Play test:**
- The save loaded on the cloud (`JankfireQuests_studio`).
- A fresh roll gave three quests, one of each tier.
- The free reroll: the first was taken, and the second answered "no rerolls left today".
- The real match: `JankMatchTest` ghost match on the 1v1 pad (arena Platform) with the player on team 1, test counting
  on, the `Stand` dummy as the ghost enemy, and three real `Fight.hurt` kills.
  - "Get 3 kills in a row without dying" went 2/3, then 3/3.
  - When the match ended (team 1), "Win a match" and "Win a match without losing a round" were paid.
  - The total: 235 Brass (160 from quests and 75 from the 3-point step), plus 1 Crate Ticket at 6 points.
  - Five toasts.
- The party check: a stand-in joined through `JankPlayTest`, so `Party.sizeOf` was 2 and the match counted as a party
  match.
- Redeem with 13 tickets: Brass for a Crate is refused ("Brass can't buy that"). Tickets for a Crate took the stock
  from 0 to 1 and the tickets from 13 to 1. A second try is refused ("not enough Crate Tickets"). The shop's
  containers tab shows YOU HAVE 1.
- The cheat restore: today's 235 Brass and 1 ticket came off and progress froze. Running it twice changed nothing, and
  the undo put it all back.
- Grant: a repeated id answers "already" and pays once.

**Fixed after the test** (in Studio and saved in 544, but not photographed):
- The DONE tick was drawn upside down: its two strokes had their rotations swapped.
- In a match the toast now sits at y 76, under the score plate.

**Not tested yet:**
- Range quests (they need a full range run).
- Slide and grapple kills, item uses, ranked quests (`JankPlayTest` held ranked match) and two real players.
- The shop's REDEEM buttons and the VIP daily's `giveBrass`: these are the shop session's next push.
- A phone-sized photo of the panel.

**Note for the owner's save:** the redeem test added one Crate to the owner's loot stock (the live loot store; Studio
shares it). Containers are free while `LOOT_FREE` is on, so it changes nothing that matters.

Photos: `docs/quests/` (panel in progress, the toast, the panel done, the shop after the redeem).
