# The shop

The SHOP screen sells the cosmetics that are on Roblox today: wraps, weapon hats, the three loot containers and
themed bundles. Everything is **free while we test** (`Config.LOOT_FREE`). Every offer already has a Robux price and a
slot for its developer product, and the purchase prompts and receipt routing are wired but **off**
(`Config.LOOT_ROBUX = false`, read as `Shop.ROBUX`).

Research behind it (other games' shops, Roblox's rules for paid random items, kits worth borrowing):
`JANKFIRE Vault\Research\Shop GUIs.md` (outside git; other games' pictures stay there).

## Who owns what

| piece | file | owner |
| --- | --- | --- |
| the catalog: containers, bundles, singles, daily rotation, prices, product ids | `src/shared/Shop.luau` (`ReplicatedStorage.Jankfire.Shop`) | shop |
| the screen | `src/client/ShopUI.luau` (ModuleScript) + `src/client/ShopClient.client.luau` (key, button, prompts, test hook) | shop |
| Robux prompts and receipts (off) | `src/server/ShopReceipts.server.luau`, remote `JankfireRemotes.ShopBuy` | shop |
| the inventory, its save, buy / open / claim, `Loot.grant` | `JankfireRemotes.Loot`, `src/server/Loot.luau` | loot |
| the pools and the odds | `src/shared/LootTable.luau` (`LootTable.odds`, `.soon`, `.RARITY`) | loot |
| the opening sequence (after a container is bought or opened) | `src/client/LootOpening.luau` (`play(kind, res, opts)`, yields) | loot |
| the bundle holograms in the hub | the hub | hub |

What the shop asks the loot server (`JankfireRemotes.Loot`, a RemoteFunction; full list in `Loot.luau`):
`("inventory")` when it opens and whenever the player attributes `LootOwned` / `LootStock` change;
`("buy", offerId)` for CLAIM (a bundle's items, a single, or one container into your stock);
`("open", kind)` then `LootOpening.play(kind, res, { again = true })`, again while it answers "again".
The loadout only wears wraps and hats you own (`Loot.owns`, the loot session's change in `Loadout.luau`).

## The catalog (`Shop.luau`)

Three kinds of offer, each with an id:

- **containers** `crate`, `bag`, `spray` (Crate, Duffel Bag, Spray Can): one random item you don't own yet. Crates
  hold weapon skins (the ones whose models are in the place), Duffel Bags hats and card looks, Spray Cans wraps. Names
  and prices are the shop's; the pools and odds are the loot module's, read through `Shop.odds(id, owned)`
  (`LootTable.odds`, the function the server rolls by), so the screen never shows numbers the server doesn't use.
  The odds depend on what you own; when you own everything in one it reads YOU HAVE IT ALL.
- **bundles** `bundle_<name>`: a fixed themed set of wraps and a hat that dresses several guns, plus a `hero` (the
  weapon, wrap and hat the big preview and the hub's hologram show). Six to start: Night Shift, Field Issue, Tea House,
  Deep Space, Machine Shop, Quarry. A bundle's price is about 60% of its items one by one (`Shop.worth`).
- **singles** `wrap:<id>@<weapon>`, `hat:<id>@<weapon>`: one item for one weapon; `skin:<id>`: one weapon skin
  (see "Weapon skins and skin sets" below); `border:<id>` / `banner:<id>` / `title:<id>`: one player card look;
  `kill:<id>` / `emote:<id>`: one kill effect or emote (see "Kill effects and emotes" below). On sale only while it is
  in today's rotation (`Shop.onSale`).
- **skin sets** `<set id>` (`set_seraph`): every skin of one set, with a banner.

**Wraps and hats are owned per weapon** (the owner, 16 Nov: a spray can gives a wrap "for only one gun at a time").
Every item is `{ kind, id, weapon }`; where one string is needed it is `"<id>@<weapon>"` (`Shop.key` / `Shop.unkey`,
e.g. `"sakura@smg"`), and it reads "Sakura Storm · SMG" (`Shop.itemLabel`). The weapons are the live primaries,
secondaries and the katana (`Shop.WEAPONS`); a hat only for a weapon with a hat spot. An owned plain `"sakura"` (an
older save) counts for every weapon.

Wraps whose picture versions broke Roblox's image rules (QR Code, Barcode, Meat Suit, Organ Donor, CORP, Corporate
Memo, Jersey) never appear in a bundle or the rotation (`Shop.HELD_BACK`).

**The featured rotation** (`Shop.rotation(day)`): one hero bundle and six singles a day, seeded by the UTC day number,
so every server and every client agrees without storing anything. The six, with everything in the place: two wraps,
one hat, one player card look, one weapon skin and one kill effect or emote, at least one epic or better (without the
card looks, skins or flair, wraps fill their slots, and there are two hats when there's no flair). It turns over at 00:00 UTC; a single from yesterday stays buyable for 5 minutes after the turn.

**Prices** (`Shop.PRICE`, Robux, unused while free): wraps 75 / 150 / 300 / 600, hats 100 / 200 / 400 / 750,
weapon skins 150 / 300 / 600 / 1,200, kill effects and emotes 100 / 200 / 400 / 800 by rarity (common / rare / epic /
legendary); card looks less; containers 120 / 90 / 60; bundles from their worth.

Useful calls: `Shop.offer(id)`, `Shop.contents(offer)`, `Shop.free()`, `Shop.rotation()`, `Shop.secondsLeft()`,
`Shop.onSale(id)`, `Shop.odds(containerId, owned)`, `Shop.productFor(offer)`, `Shop.itemInfo(kind, id)`,
`Shop.itemLabel(item)`, `Shop.key(kind, id, weapon)`, `Shop.unkey(s)`, `Shop.weaponName(wid)`, `Shop.WEAPONS`.

## The screen

- **Open it:** the B key; the SHOP button over the LOADOUT button (bottom left, hub only); a hub hologram; or from
  any client script: `require(PlayerScripts.Jankfire.ShopUI).open(tab, offerId)`. A ProximityPrompt with the
  attribute `ShopOpen = "bundle_nightshift"` (or `"tab:containers"`) opens it on that offer when triggered.
  Not in a match, not over the loadout.
- **Opened straight onto one offer** (a hologram, `open(tab, offerId)` from another screen, while the shop was shut):
  BACK closes the whole shop and you're back in the game, and an opening started there ends back in the game too (the
  owner, 16 Nov). Opened with B or the button and then into an offer, BACK goes back to the list as before
  (`S.deep`, `ShopUI.back`).
- **Tabs:** FEATURED (today's bundle big, with what's in it, and the six daily singles with a countdown),
  BUNDLES, CONTAINERS (each with ODDS, OPEN and CLAIM), INVENTORY (containers to open, then wraps and hats grouped
  by weapon; filters).
- **Inspect:** any card opens a big turnable 3D preview (drag to turn). A bundle lists its items ("Sakura Storm ·
  SMG"); tapping one shows it on its own weapon. Every wrap and hat is shown on the weapon it's for (a hat drawn
  half again its size on a small card, true size in the inspect panel).
- **Buying:** CLAIM / BUY opens a confirm panel first. A container's confirm panel shows its odds, and a paid
  container can't be bought when the odds can't be read. Then the till (`Loot` "buy") is asked; a container is opened
  at once and the loot module's opening plays while the shop steps aside; the inventory tab shows what you got.
- **Several at once:** each container (card and inspect panel) has an x1 / x5 / x10 pick. CLAIM xN shows the odds
  once, asks `("buy", kind, n)` then `("open", kind, n)` (one batch, never the same item twice), and the opening shows
  them all; OPEN ANOTHER opens the same number again. OPEN xN opens from your stock.
- **Look:** `Theme.luau`: dark plates and cards, white and grey text, one amber accent (the active tab's mark, the
  main button, the featured label), rarity colour only as a thin line or dot. Builder Sans, Builder Extended titles.
- **Screens:** laid out 720 design pixels tall on a computer (wider screens get more width) and 400 tall on a short
  screen (a phone on its side, 375-430 points tall), so on a phone one design pixel is about one point: the shop
  fills the screen and every button is at least 44 points tall. The title row sits in Roblox's top bar, right of
  Roblox's own buttons, inside the phone's safe area; on a narrow phone the FREE pill, then the title, give way to
  the tabs and CLOSE. Checked at 844 x 390 (a phone) and 1334 x 750.
- **While it's up:** it raises the player attribute `LoadoutOpen` too (the flag every script reads as "a menu is
  up": no jumping, shooting or items, mouse arrow on) and its own `ShopOpen`.

## VIP (a game pass)

The owner, 16 Nov: "the ducky set is a high tier set you get by purchasing vip, it comes with a couple skins, a hat,
a wrap, a border and a title? it also lets you enter the vip room?"

- **Who is VIP** is decided on the server only, by `src/server/Vip.luau` (`ServerScriptService.Jankfire.Vip`, started
  by `ShopReceipts` at server start). Any of these makes a player VIP:
  - the game pass (`Shop.VIP_PASS`, 0 until it's made): `UserOwnsGamePassAsync` on join, and
    `PromptGamePassPurchaseFinished` for a purchase made now;
  - while the shop is free (`Config.LOOT_FREE`), anyone's **GET VIP · FREE WHILE TESTING**, kept in the DataStore
    `JankfireVip_v1` so it lasts (and counts only while the shop is free);
  - the place's owner in Studio: `JankfireRemotes.Vip ("dev", "unlock" | "lock")` turns VIP on or off for that session.
- **For other server scripts** (the hub's VIP room door):
  - `require(game.ServerScriptService.Jankfire:WaitForChild("Vip")).isVip(player)`;
  - `Vip.changed:Connect(function(player, isVip) end)`.
  The player attribute `VIP` is set by the server for client visuals only; never decide with it.
- **The pack** is the shop's offer `"vip"` (type `"pass"`). Its contents (`Shop.vipItems()`) are everything that
  exists and the loot module calls VIP-only (`LootTable.vipOnly`, read through `Shop.vipOnly`): the VIP skin set's
  skins (`set_ducky`), every wrap and hat with `vip = true` (no weapon: worn on every gun), and the VIP card looks
  (rarity `"vip"`).
  - `Vip.luau` hands it over with `Loot.grant(p, "vip", "vip-<n>-<signature>")`, so a pack that gains things later
    is granted again, once, and only the new things land.
  - VIP things are never sold: no bundle, set banner, daily single or container (`Shop.vipOnly` filters, and the
    loot module's pools).
- **On screen:**
  - A VIP tile tops BUNDLES: GAME PASS, VIP, the two perks, GET VIP, and the pack's top skin wearing the VIP hat
    with every pack item along the bottom.
  - Its inspect panel lists the pack ("Ducky · Every gun") and says "and the VIP room in the hub".
  - VIP things sit in their own VIP section of the inventory, each once.
- **Robux later:** make the pass on the Creator Hub (priced as `Shop.vip.robux`, 399), put its id in `Shop.VIP_PASS`
  and turn `Config.LOOT_ROBUX` on. GET VIP then asks the server, which shows Roblox's pass prompt.

Tested in solo Play (place version 437, the owner's account; photo sheet `roblox/docs/shop/shop-vip.jpg`):
- **Before VIP:** the VIP tile topped BUNDLES above the real set banners (Seraph | Infernal, Witching Hour |
  Tidecrest; the Ducky set not among them). Locked out of VIP, a character put inside the VIP room was moved back out
  within 1.7 s (the hub's door, `HubVip`).
- **Claiming:** GET VIP · FREE WHILE TESTING (from a panel opened straight onto `"vip"`) made the player VIP in
  0.8 s. The pack landed: the 3 Ducky skins, the Ducky wrap on all 16 guns, the Ducky border and the VIP title. The
  panel then read YOU'RE VIP with every item OWNED, and BACK shut the shop.
- **In the room and wearing:** as VIP the character stayed inside the room. Bubble Bath was worn on the LMG
  (then put back) and the Ducky border on the player card (left on: the owner is VIP now).
- **Locking and unlocking:** the owner's Studio "lock" moved the character out of the room again, and "unlock" made
  them VIP again at once.

Later checks:
- **The Royal Duck (place version 447):** joined the pack by itself, which now holds 7 things. The VIP tile shows the
  Ducky LMG wearing it. It is not in the daily pool or sold on its own (checked by reading the shop in a running server).
- **The hub's server-only door (version 448), walked with the W key in Play (place version 453):**
  - Locked out of VIP, the character's collision group was Default and it stopped at the door, 0.5 studs short of
    the doors' line.
  - Unlocked, its group was VipGuest and it walked 18.6 studs through into the room.
- **Concept skins:** the guns session's concepts (`SkinSets.CONCEPTS`) are never on sale (`Shop.skinLive` refuses
  them).

## VIP daily reward (Trisangle, 17 Nov)

The owner: "If you talk to Trisangle in the vip room as long as you have vip you get a random daily reward with the best
thing being a special wrap skin hat anddddd skin case. Bags cans coins etc will be filler rewards".

- **Where:** a ProximityPrompt (E) on Trisangle's seat in the VIP room. It goes on the hub's HubNPC spot whose `Who` is
  Trisangle, or any HubNPC part with `VipDaily = true`. Each player's prompt reads "Daily reward" when ready, "Back in
  7h 12m" once taken, and "VIP daily reward" for a player who isn't VIP.
- **Who:** VIP only, checked on the server (`Vip.isVip`). A press without VIP opens the shop straight onto the VIP
  tile.
- **When:** once a day per player; a new day starts at 00:00 UTC. A second press the same day gets "Tomorrow." from
  her and the time left.
- **The save:** its own session-locked profile (`Profiles.luau`, `JankfireVipDaily_v1`, `_studio` in Studio). A claim
  writes the day and the prize before paying, so a second claim that day is refused, in this server or any other.
- **Paying:** each prize is paid with the receipt id `vd-<userId>-<day>`, and both payers are idempotent.
  - Brass: through the quests server (`Quests.giveBrass`).
  - A container or one of the three daily-only items: through `Loot.grant`.
  - If a pay fails, the prize stays pending and is paid on the next try or the next join.
- **The prompt moves with her:** the hub walks her between the VIP room's seats and moves the prompt onto her avatar.
  The spot keeps a `VipDailyHooked` mark, so no second prompt is made.
- **The reveal:** Trisangle says "Here." over her head, then the loot session's `LootOpening.reward` reel plays,
  titled DAILY REWARD, FROM TRISANGLE, with the prize's card and DONE. If that isn't in the place, a plain reel in
  the shop's style lands on the prize instead.
- **Files:** `src/shared/VipDailyData.luau` (the table, the roll, the odds), `src/server/VipDaily.luau` (claim, save,
  pay, the prompt), `src/client/VipDailyClient.client.luau` (the prompt's words, her line, the reveal). `ShopReceipts`
  starts the server module.

**The table** (`VipDailyData.TABLE`, weights out of 1,000):

| prize | tier | weight | chance | about every |
|---|---|---|---|---|
| 40 Brass | filler | 420 | 42.4% | 2.4 days |
| 100 Brass | filler | 270 | 27.3% | 3.7 days |
| Spray Can | filler | 130 | 13.1% | 7.6 days |
| 250 Brass | filler | 110 | 11.1% | 9 days |
| Duffel Bag | filler | 50 | 5.1% | 20 days |
| Crate (the skin case) | rare | 10 | 1.0% | 99 days |
| the daily wrap | best | 4 | 0.4% | 250 days |
| the daily hat | best | 3 | 0.3% | 333 days |
| the daily weapon skin | best | 3 | 0.3% | 333 days |

The chances are for today, with the three daily-only things off: they don't exist yet, so the other 990 share the
odds. Once all three are on, the filler and the Crate drop a little (42.0%, 27.0%, 13.0%, 11.0%, 5.0%, 1.0%) and
one of the three comes about every 100 days.

The Crate was 2% at first. The quests session ran the odds through its economy sim (QUESTS.md, section 3): at 2%,
the daily nearly halved a regular VIP's wait for a Crate (48 days to 27). It suggested 0.5%, but that would make the
Crate rarer than the daily-only wrap. So it's 1%, with the other 1% on the Spray Can: the Crate stays mainly a ticket
reward and stays above the three in the order the owner gave.

**How generous:** about 72 Brass a day, plus containers worth about 255 Brass more at the shop's Brass prices. That's
about 330 Brass' worth a day, next to a quest grinder's 231 Brass a day (QUESTS.md). A Crate about every 100 days on
top of the quests' one every 19 to 204 days.

**Rules on top:**
- One of the three you already have becomes another of them you lack; with all three owned, a Crate.
- While containers are free, a container you already hold 10 of (`Loot`'s cap) becomes 100 Brass.

**The three daily-only things** are the Triangulum trio, from the skin-concepts session (shared notes
`triangulum-vip-brief.md`). They are listed in `VipDailyData.EXCLUSIVE`:
- wrap `triangulum` (wraps session);
- hat `tricorne`, Star Tricorne (hats session);
- skin `sniper_triangulum`, Triangulum, for the Sniper (gun models session).

That list is the daily-only mark: no `daily` flag on the items, and never `vip`, since the VIP pack gives every vip
thing (`Shop.vipItems` skips them anyway). A slot turns on by itself once its item is in the place:
- the roll includes it;
- the shop never sells it (`Shop.dailyOnly`: not a single, not in the rotation, a bundle or the VIP pack);
- the server pays it through the hidden offer `"vipdaily:<kind>:<id>"` (type `"pass"`, so the loot server's buy
  refuses it). A wrap or hat comes on every gun, like the VIP pack's.
- The loot module's container pools skip them (`LootTable.exclusive`, which asks `VipDailyData.isExclusive`), and
  the skin has a `LootTable.SKINS` row so the grant can write it.

**Simulated** (10,000 claims, seed 17, owning none of the three, room for everything):
- three off: 40 Brass 4,273 · 100 Brass 2,671 · Spray Can 1,296 · 250 Brass 1,121 · Duffel Bag 544 · Crate 95;
- three on: 4,237 · 2,632 · 1,286 · 1,098 · 556 · 99, and wrap 29 · hat 31 · skin 32.
- Owning all three, with the Spray Can at the cap (3,000 claims): no daily-only item; Crate 67 (2.2%: its own 1%
  plus the three's 1%); 100 Brass 1,163 (38.8%: its own 27% plus the Spray Can's 13%).

**Tested in solo Play (place version 549)**, as the owner (VIP):
- A claim with the prize forced to a Spray Can (`JankVipDailyTest("claim", p, "spray")`) answered "won". The day was
  written (`VipDailyNext` = the next 00:00 UTC) and the Spray Can was in stock. The loot session's reveal played:
  DAILY REWARD, FROM TRISANGLE, the reel, then the Spray Can card and DONE (photo `docs/shop/vip-daily-reveal.jpg`).
- A second claim the same day answered "later", with the next one 890 minutes away.
- A Brass prize (40) was paid through `Quests.giveBrass`: the wallet went 600 to 640.
- Not VIP: the client's answer opened the shop straight onto the VIP panel. It now says "and the VIP room in the
  hub, with a daily reward" (`vip-daily-notvip.jpg`).
- The server's own VIP refusal was tested later (place version 569). The owner's Studio lock went through the real
  Vip remote and the claim through `JankVipDailyTest`: the answer was "notvip", with nothing written (the day stayed
  unclaimed). In the first test a command-bar `require` of Vip had made second copies of Vip and Loot that took over
  their remotes (see the trap under "Testing it in Play").
- Put back afterwards: the owner's Studio quest balance (1 ticket, 335 Brass), and the daily (claimable again).
- Not put back: the second loot copy blocked the restore, so the owner kept a Spray Can in stock and one SMG item
  from the redeemed Duffel Bag. Both are free while testing.

## Redeeming with Crate Tickets and Brass (17 Nov, place version 549)

The quests session's currencies (roblox/docs/QUESTS.md, section 6) buy containers in the shop.
- **The wallet:** the player attributes `Brass` and `CrateTickets` (the quests server sets them on everyone at join),
  with the quests' icons (`QuestUI.icon`). On a computer it's a line under the FREE pill and CLOSE; on a phone it takes
  the pill's place.
- **The prices:** `QuestData.PRICES`, read by `Shop.redeemPrice(cid)`: a Crate is 12 tickets (Brass never buys a
  Crate), a Duffel Bag 6 tickets or 2,500 Brass, a Spray Can 3 tickets or 1,000 Brass. On a computer each container
  card shows them over its buttons ("OR 6 TICKETS · 2,500 BRASS").
- **The buttons:** CLAIM / BUY opens the confirm panel, where the odds are on screen. It has a row over CANCEL and
  BUY: "REDEEM · 6 TICKETS" and "REDEEM · 2,500 BRASS", greyed when you have too little ("REDEEM 1 · ..." with x5 or
  x10 picked: a redeem is always one).
- **The call:** `JankfireRemotes.Quests:InvokeServer("redeem", cid, "tix" | "brass")`. The quests server takes the
  price and has `Loot.grant` put one in stock, then the shop opens it like any other. A refusal shows its words as a
  callout ("not enough Brass", "you have 10 of those: open some first"...).
- **Where paid random items aren't allowed** (PolicyService): CLAIM / BUY reads REDEEM, since tickets and Brass are
  earned, not bought.

Tested in solo Play (place version 549), with 13 tickets and 600 Brass:
- The CONTAINERS tab showed the wallet (600 and 13 with their icons), each card's redeem prices, and the three
  containers' 3D previews (`docs/shop/shop-redeem-containers.jpg`). The quests session's earlier photo with empty
  previews was taken before the meshes had loaded.
- The Duffel Bag's confirm panel had REDEEM · 6 TICKETS lit and REDEEM · 2,500 BRASS grey (`shop-redeem-confirm.jpg`).
- REDEEM · 6 TICKETS took the tickets from 13 to 7 and the Duffel Bag's opening played.

## The owner's deals (17 Nov)

The owner: "I give players 3 special discounts on random skins if you talk to me!" The owner's own avatar is the
shopkeeper in the training area's gun shop. Its "Deals" prompt (the training session's, `ShopOpen = "tab:deals"`) opens
the shop on the DEALS tab.

**The rule** (`Shop.DEALS`, `DEAL_OFF`, `DEAL_TOP`, `DEAL_PICK`; `src/server/Deals.luau` picks and keeps them):
- **Three per player per day,** new at 00:00 UTC. They are picked the first time the player asks that day and kept
  in a session-locked save (`JankfireDeals_v1`, `_studio` in Studio), so they stay the same all day.
- **Which skins:** weapon skins on sale (`Shop.liveSkins`: not VIP, not the daily-only ones, not concepts) that the
  player doesn't own.
  - Picked by rarity weight: common 40, rare 35, epic 20, legendary 5.
  - At most one legendary.
  - Variety: a skin from a set already picked counts a tenth as likely, and one for a gun already picked a quarter.
- **The discount:** by rarity, off its single price: common 20%, rare 25%, epic 30%, legendary 35%. The rarest of the
  three gets 5% more, so 20 to 40% in all. Prices round like the rest (`Shop.dealPrice`). Examples:
  - a legendary skin, 1,200, is 719 at 40% (as the rarest) or 779 at 35%;
  - an epic, 600, is 419 at 30%;
  - a rare, 300, is 229 at 25%;
  - a common, 150, is 119 at 20%.
- **One each:** a deal can be had once. It reads YOURS after, or OWNED if the skin came another way.
- **Free while testing,** like the rest of the shop: CLAIM opens the confirm panel and the server grants it
  (`Loot.grant("skin:<id>")`, receipt `deal-<uid>-<day>-<id>`).
- **With Robux on:** BUY sends ShopBuy `"deal:<skin>"`. ShopReceipts checks it's one of the player's own deals today
  (`Deals.offerFor`) and prompts the product for its rarity and discount, `"deal:<rarity>:<pct>"` in `Shop.PRODUCTS`.
  On the receipt it calls `Deals.grant`.

**On screen:** a DEALS tab after FEATURED, headed OWNER'S PICKS with the time to new ones. Three cards, each with:
- a thin amber edge and a faint amber wash;
- "OWNER'S PICK · 30% OFF";
- the skin in 3D, its name, gun and rarity;
- the deal price, with the normal price struck through;
- CLAIM or BUY.

The tabs are a little narrower with five (108, or 86 on a phone).

Tested in solo Play (place version 569), as the owner:
- DEALS showed three: Cauldron (epic, Marble Shotgun) 35% off, 600 to 389; Bullpup (rare, Assault Rifle) 25% off,
  300 to 229; Baguette Katana (rare) 25% off, 300 to 229. That's three guns, the rarest with the extra 5%
  (`docs/shop/shop-deals.jpg`).
- CLAIM on the Bullpup opened the confirm panel, and the claim made it owned. The toast read "BULLPUP · ASSAULT RIFLE
  ADDED", and a second buy answered "you've had that deal".
- Closed and reopened: the same three, with the Bullpup reading YOURS.
- At phone size (844 x 390) all five tabs fit, with the wallet in the pill's place (`shop-deals-phone.jpg`).
- Put back afterwards: the owner's inventory (through the loot remote) and the test deals (`JankDealsTest` reset).

## Try anything in training (17 Nov)

The owner: "when you're in the training hub you're free to use any weapon, and when you leave it reloads your previous
loadout".

- **Where:** the training hall (with its back lot and basement) and the playground: `Zones.training(p)`, the shared
  helper `Zones.luau` (the utility-items session's, also used for free items in training) over `Matches.zoneOf`.
- **What changes there (`Loadout.luau`):** the first loadout change (pick, wrap, hat or skin) copies the saved
  loadout into a try layer (`d.try`). Changes go to that layer with no ownership checks, and it arms you at once
  (`tryArm`). The saved loadout, which is what gets written to the DataStore, is never touched. Concept skins
  (`SkinSets.CONCEPTS`) are refused even there.
- **Leaving:** a check every 0.2 s drops the layer once you're outside both zones, republishes the saved loadout and
  re-arms you with it (`endTry`). Coming back starts again from the saved one. A match (`armed` while not in a try
  zone) drops the layer before arming, so nothing tried reaches a match, a replay or a finisher.
- **On screen (`LoadoutUI`):** while trying (the attribute `Trying`, or Zone training/playground) the subtitle reads
  TRY ANYTHING HERE · YOUR LOADOUT COMES BACK WHEN YOU LEAVE, and things you don't own carry an accent TRY mark
  instead of the padlock. The shop's inspect blurb for a skin, wrap or hat you don't own ends "try it on in the
  training hall first."

Tested in solo Play (place version 684):
- In the training hall, picking the Assault Rifle, the Keytar skin and the Halo hat (none owned) all went through,
  with `Trying` = true; a concept skin was refused ("that one's still a concept"). The loadout showed the
  training subtitle and TRY on what isn't owned (`docs/shop/loadout-try-training.jpg`).
- Back in the hub: `Trying` cleared, skins, hats and picks were the saved ones again (Shredder on 1).
- Tried again in the hall, then a ghost 1v1 started with the player in it: in the match, the Shredder in hand and the
  saved skins and hats, nothing tried.

## The Loadout's strips scroll (17 Nov)

The owner: "The weapons run off and you can [not] scroll through!!" The SKINS strip was a plain frame, so the Assault
Rifle's many skins ran off the panel.

- The wraps, hats and skins strips are horizontal ScrollingFrames: mouse wheel, drag, swipe on a phone, a scroll bar,
  and ‹ › buttons at the ends that page along (shown only when there's more that way). `CanvasPosition` turned out to
  be in screen pixels even under a UIScale (measured in Play: its furthest is `AbsoluteCanvasSize - AbsoluteWindowSize`),
  so the paging works in screen pixels on the desktop fit and the phone layout alike.
- What you wear comes into view when the screen opens, when you switch tab and when you focus another weapon
  (`showWorn`).
- The owner on the HATS tab: "This is right and easily fixable by allowing scroll!!" So the SKINS row is the HATS
  row exactly: the same place in the same panel, cards `CW` wide (86 today) with an 88 px picture, a rarity line, the
  name under it, and 8 px between them. Hat cards shrink to fit up to thirteen hats as before, never under 86 px; past
  that the strip scrolls. The wraps strip keeps its swatches (86 px, the same width) and its filter row; it already scrolled inside its panel and now has the same 8 px spacing and ‹ › buttons.
- Concept skins (`SkinSets.CONCEPTS`, the guns session's) are never shown to players. The owner (in Studio, or the
  place's creator) sees them at the end of the strip, tagged CONCEPT, to look at in the big preview; clicking one
  says it's a concept. Their names come from the builders' notes: Velvet, Starlight, Glasswing, Sweet Shop (cute
  A to D), Duckling. The owner's Tripo picks have no names yet and show their ids. A test sees the players' strip
  with the player attribute `PlayerView = true`.
- Tested in solo Play (place version 684): before, the Assault Rifle's skins ran off the panel under dev names
  (`docs/shop/loadout-skins-before.jpg`); after, they sit in the panel at the hats' size with a › at the end, the
  concepts named and tagged (`loadout-skins-after.jpg`), the wheel scrolls the row, and the hats row and the phone
  layout (844 x 390) are unchanged and inside their panels (`loadout-hats-after.jpg`, `loadout-hats-phone.jpg`).
- The flair screen's kill effect, emote and grapple grids (the flair session's `FlairUI`) already clip and scroll, and
  stay as they are.

## After an opening, back to the game (17 Nov)

The owner: "after opening chests it shouldnt take you back to your inventory just back to the game". Every container
opening goes through `ShopUI.openBox` (the inventory's OPEN, the CONTAINERS tab, the inspect panel, a redeem). When
the reveal (`LootOpening.play`) closes with DONE, the shop closes too: camera, controls and HUD back, no inventory.
OPEN ANOTHER still opens the next one first. Only an open that never started (refused, none in stock) leaves you in
the shop, with the reason. Test ops (`ShopTest`): `openbox:<container>` or `openbox:<container>:<n>` presses its
OPEN; `finish` or `finish:again` presses the reveal's DONE or OPEN ANOTHER.

Tested in solo Play (place version 684): a Duffel Bag opened from INVENTORY and one from CONTAINERS; DONE on the
reveal (`docs/shop/chest-reveal.jpg`) left the shop shut, the camera Custom, no blur and the HUD back
(`chest-done-back-in-game.jpg`). The inventory was put back afterwards (the loot remote's dev `set`).

## The mouse in menus: MenuCursor (17 Nov)

The owner: "sometimes your mouse cursor disappears when you open crates and stuff". The arrow used to follow one flag,
LoadoutOpen (JankSettings showed it only while that was true), and every screen saves that flag when it opens and puts
it back when it closes. Screens don't close in the order they opened, so the flag could read false with a menu still
up: the arrow hid, and the shoulder camera and the emote camera locked the mouse again. One case is certain: the shop
closing over the Loadout cleared it (`ShopUI.loadoutUp` looked at the Loadout's ScreenGui, which the shop itself had
switched off).

`client/MenuCursor.luau` is now the one place that says a menu needs the mouse. Each screen puts its name in while
it's up and takes it out when it goes, with an optional alive check. A screen that went away without taking its name
out is let go on the next frame:

    MenuCursor.set("shop", true, function() return S.open end)   ...   MenuCursor.set("shop", false)

Names: shop (with its inventory), loot (a crate, bag or spray-can reveal, to DONE or OPEN ANOTHER), loadout, settings,
quests, card (the player card), play, party, board, flair (the equip screen), wheel (the emote wheel), report, anticheat.

While any name is in:
- the mouse is free (MouseBehavior Default) and the arrow shows (MouseIconEnabled). This is written every frame at
  RenderPriority Last + 100, after Roblox's first person, ShoulderCam and the Play panel's lineup;
- the player attribute MenuCursor is true (ShoulderCam and FlairClient's emote camera don't lock while it is), and
  MenuCursorBy lists the names;
- LoadoutOpen (the hold-still flag for hands, weapons and movement) stays up. If a screen clears it on its way out
  while another is still up, it goes straight back up.

When the last name goes, the game's own rule comes back on the next frame: first person and the shoulder camera lock
the mouse, and JankSettings hides the arrow. A cinematic that only holds still (a finisher, the play of the match) still
shows the arrow through LoadoutOpen, as before.

Tested in solo Play, in first person, on the hub (not saved yet, C: had 0.5 GB free). A test RenderStep after
everything logged the mouse every frame (1,628 frames, 109 s). In every frame where a menu held the mouse, it was
Default with the arrow showing; once each flow ended, it was LockCenter with the arrow hidden:
- INVENTORY, then a Crate: the reveal had loot and shop in; DONE closed both and gave LockCenter back.
- CONTAINERS, then a Spray Can, OPEN ANOTHER, a second one, then DONE: no frame lost the mouse between the two openings.
- Quests (QuestTest open), then the real OPEN SHOP button, then a Duffel Bag from CONTAINERS, then DONE: back in the game.
- The shop opened and closed four times in 1.2 s: LockCenter after, nothing left in.
- The Loadout (L), then the shop on top: the shop doesn't open over the Loadout (canOpen refuses), and the Loadout kept
  the mouse. After the shop's close and the Loadout's close (L): LockCenter, arrow hidden.
- The owner's inventory was put back afterwards (249 items, via the loot dev `set` op). Stock was 0 in all three
  kinds, so every opening was a free one.

The rest, tested after (place version 717, solo Play, one per-frame log, 0 frames in any of 18 phases with a menu up
and the mouse locked or the arrow hidden). Each screen went through its own test hook, and each gave Default with the
arrow showing while it was open and LockCenter with the arrow hidden once it closed:
- the emote wheel (FlairTest wheel / close), the equip screen (ui / uiclose), the party panel (PlayTest party /
  unparty), the leaderboard (board / noboard), the Play panel (play / close);
- third person (V): the shop opened and closed over the shoulder camera. Toggle Cursor there held the look through
  mouse moves (0 degrees), and off gave LockCenter again;
- the phone layout (TouchForce): the shop opened and closed the same way.

Not tested: a report (ReportUI), the anti-cheat panel.

## Toggle Cursor (17 Nov)

The owner: "allow a button to toggle mouse cursor", then "we need mouse unlock". **Left Alt** frees the mouse and shows
the arrow without opening a menu, and pressing it again locks the mouse again. The key can be changed in Settings >
KEYBINDS (TOGGLE CURSOR, Binds action `cursor`, MENUS group). The script is `client/CursorToggle.client.luau`.

- It's a MenuCursor name, `toggle`, put in **cursor only**: the mouse is free and the arrow shows the same way as
  under a menu, but it isn't a menu. LoadoutOpen isn't raised or kept up, so movement, jumping, reloading and the
  other keys work as normal. `MenuCursor.menu()` says whether a real menu is in.
- With a menu up, the key only turns the toggle off (the menu has the mouse anyway). Turned off under a menu, the
  menu keeps the mouse.
- While the mouse is free (the toggle or any menu, the MenuCursor attribute), clicks don't fire, swing or aim
  (Arsenal's fire and aim keys and its auto and fan loops). A Tool in your hands (the Shredder) is set to
  ManualActivationOnly, so a click can't start it. The camera holds its look.
- A plate at the top in the middle (below the match score) shows CURSOR FREE and the bound key.
- It turns itself off at a death, a respawn and a round's start (the Round remote's `start`). In a live round it can
  be turned on again, and it still can't fire.
- Phones: the key does nothing (no mouse).
- Test hooks (Studio): the player attribute `CursorFree` is true while it's on; `CursorTest = "on" | "off"` sets it.

Tested in solo Play, in first person (place version 717). The live checks read MouseBehavior, MouseIconEnabled,
MenuCursorBy, LoadoutOpen and the camera's look, and the real Left Alt key and mouse clicks went through the Studio
input tools:
- In the hub: Left Alt gave Default with the arrow shown, the toggle in, LoadoutOpen not raised and the plate up
  (key "Alt"). Moving the mouse about, and a right-button drag, turned the camera 0.02 and 0 degrees. W held for
  0.9 s walked 25.5 studs.
- The shop opened over the toggle (shop and toggle in) and closed again: the toggle kept the mouse. Left Alt inside
  the shop turned the toggle off and left the shop the mouse. A Crate opened from there, and DONE gave LockCenter,
  the arrow hidden and nothing in.
- A ghost 1v1 on RooftopV3 with the toggle on before it: the round's start turned it off (LockCenter). In the live
  round Left Alt turned it on: two clicks fired nothing (5 / 5 in the magazine). Left Alt off, then one click fired
  (4 / 5).
- With the toggle on, a death (Health 0 from the server) turned it off at once.

Not tested: the Shredder held with the toggle on, third person, a controller, a rebound key.

## The match loadout screen (18 Nov)

The owner: "can you have renders when selecting loadout look up rivals pregame loadout thing, I want something
similar". It's `client/MatchLoadout.client.luau` (play-party-ranked's text picker, rewritten), with the window rules
unchanged. Matches sets LoadoutWindow for 8 s before round 1 and 6 s between rounds; Loadout.luau takes a "pick" only
inside it and puts it in your hands at once.

**What the research said, as function only.** Rivals: four slots (primary, secondary, melee, utility), each weapon shown
in its skin, changed between rounds under a short countdown; ranked caps swaps per duel. Little more could be found
about the screen itself, and nothing of its layout or look is used here. We keep our own rules: no swap cap.

**Ours:**
- While the window is open, without taking the mouse, a strip of the four slots sits low in the middle. Each slot is a
  live picture of the weapon in your own skin, hat and wrap, turning a little. The header shows LOADOUT, the L key, the
  seconds left in big amber numbers, and a thin bar that runs down with them.
- L (the loadout key) takes the mouse (MenuCursor `matchloadout`: clicks don't fire, you still move) and opens the
  picker on PRIMARY. Every live weapon for that slot is a picture in your looks, with the one you have marked; one click
  picks it. The picker stays open: click another slot or press 1 to 4. L, Esc or DONE closes it, and so does the window
  shutting. With Toggle Cursor (Alt) on, the slots can be clicked straight away.
- Phone (or a screen under 900 x 560): the strip sits at the top under the score and the picker under it, between the
  stick and the fire buttons. A slot is tapped straight away.
- Colours: the HUD's dark plates, white names, amber only on the seconds, the bar and the marked slot or weapon.
- The pictures come from `client/GunPreview.luau`, the loadout screen's preview builders as a module: `viewport`,
  `put(vp, cam, weapon)` (rebuilt only when the looks change), `turn`, `clear`. LoadoutUI still has its own copy.
- Test hook: `MatchLoadoutTest` = open | slot:<slot> | close | pick:<slot>:<weapon> | fake:844x390 | real. The
  server's `JankMatchTest("between", player, secs)` opens a window that long.

Tested in solo Play (place version 728) in a ghost 1v1:
- The strip came up with round 1's countdown, with all four pictures (`docs/shop/match-loadout-strip.jpg`).
- L opened PRIMARY's 11 weapons (`match-loadout-picker.jpg`). A real click on SHOTGUN picked it: LoadoutNext changed
  and it was in my hands at once.
- The phone layout (TouchForce, an 844 x 390 box) showed the utility slot's 13 items and PRIMARY
  (`match-loadout-phone.jpg`).
- The window shutting hid the strip and gave the mouse back (LockCenter, arrow hidden, nothing in MenuCursor).
- The owner's primary was put back afterwards (LMG).

Not tested: a pick while dead between rounds, a team match, a controller.

## READY: lock in, a longer window, an early start (18 Nov)

The owner: "give more time for loadouts! until move people lock in their set once both are ready idk research rivals!"

**Research, function only.** Rivals skips its 12 s matchmade duel countdown once every player has connected (patch
notes, June 2026); its duel pads count in from 3. Nothing about a ready button or a loadout lock-in could be found.
Main's rules (below) are kept: an early start once everyone is in is the same idea.

**The rules** (server `Matches.luau`, shop-gui's part of it since 18 Nov; play-party-ranked's map rooms untouched):
- The window is `READY_FIRST` = 20 s before round 1 and `WINDOW` = 15 s between rounds (the 3 s break, then 12 s at
  your spawn). The server's `LoadoutWindow` still says when it shuts.
- You're held at your spawn while the round counts in (`holdSpawns`): the server anchors your body's root 0.6 s after
  it appears and lets go the moment the round goes live. Moving was free in the count before this. An anchored body
  doesn't move, so the anti-cheat's checks have nothing to judge: with the movement checks on (StudioOn), a 20 s
  window held gave 0 points and no verdicts.
- READY locks your set for the round: the header's button, Space (the new `ready` bind, READY (LOCK IN LOADOUT),
  MENUS, controller D-pad up; Enter until the owner asked for Space, 18 Nov) or a tap. While the window is open the
  ready key is sunk at ContextActionService priority 3500, so Space only readies: no jump, and none queued for the
  moment the hold lets go (MatchLoadout also clears Humanoid.Jump then). Shut, Space is a jump again. A saved custom bind
  is kept (Settings stores only what differs from the default). Tested at place version 757: Space readied in round 1's
  window and in a break's (`docs/shop/match-ready-space.jpg`), the hold let go with no jump either time (Running, y
  unchanged), and in the live round Space jumped (4.9 studs).
  It goes through the `MatchReady` remote to `Matches.ready`; the server sets
  `LoadoutReady` on you, and `Loadout.luau` refuses picks after that ("you're locked in for this round").
- Who is ready: `ReadyTeams` on every player in the match, per team "1" a player locked in, "0" not ("1,0|0"). The
  header draws one tick a player, by team, after a thin bar in the team's colour. No names.
- Everyone still in the match ready: the window shuts at once (LoadoutWindow cleared), ALL READY, and the round goes
  live `GO` = 3 s later, still held. From the break, the next round starts at once with that 3 s count. Whoever doesn't
  lock in keeps what they had when the time runs out. A leaver is out of the count (PlayerRemoving checks again).
- Every round-based match, casual and ranked, the same. A classic mode has no window and refuses READY.
- Test ops (`JankMatchTest`): `"standin", player, team, ready[, index]` (a pretend player in the count),
  `"queued", player, ranked, secs` (a Play-queue match alone, held like a ghost match). Client: `MatchLoadoutTest =
  "ready"`.

Tested in solo Play (place version 739):
- A ghost 1v1 with a stand-in that never readied. The 20 s window ran with me held from 1.6 s. Enter at 6.4 s gave
  LOCKED IN and the ticks 1|0 (`docs/shop/match-ready-desktop.jpg`; the phone layout:
  `match-ready-phone-locked.jpg`). The time ran out: the strip went on the clock (20.62 s), the round went live
  (20.65 s) and the hold let go (20.68 s). Anti-cheat: 0 points, no verdicts.
- The phone layout before locking in: READY in the header (`match-ready-phone.jpg`).
- A ranked Play-queue match ("queued"), alone. Enter with 10 s left: everyone in, so the window shut that frame, then
  live 3.0 s later and let go.

Not tested: two real players, an early start from the break with real players (the stand-in run ended with the ghost
match), the map room handing over into round 1 (its code path is unchanged: stageGo -> startMatch -> startRound), a
controller.

## Gadget wraps and skins, and the Classic gun skins (18 Nov)

**Gadgets** (the owner: "Gadgets should have skins and be wrappable"). The utility-items session made the models (in
JankfireSkins, Weapon = the gadget, Item = true, with WrapUV), the catalogue (`shared/ItemSkins.luau`) and the
held/thrown/third-person looks. Mine:
- **LootTable:** the gadgets take wraps, owned per gadget like a gun's ("galaxy@frag"; utility-items' hunk). The
  eight gadget skins have fallback rows until ItemSkins is in the place, and its rows win after that.
- **Server Loadout:** wraps and skins go on the utility slot. Hats stay on guns.
- **LoadoutUI:** the WRAPS and SKINS tabs open on the utility slot, and its preview is the skin's model wearing the wrap.
- **Pictures:** `GunPreview.itemModel(id, skin)` clones the skin's model, or the gadget's own from JankfireItems. The
  loadout, the match picker and the shop's cards (ShopUI `V.gun`) draw gadgets with it. The crate reveal already
  falls back to the skin's model at its file size.
- Crates roll them like a gun's skin, and the shop's daily and deal rotations may offer them (LOOT_FREE as for
  everything).

**Classic set** (the gun-models session's `<weapon>_classic` skins: one per standard gun, shaped like its real type).
They're free for every player: LootTable rows with rarity "free" (`L.isFree`: `Loot.owns` says yes for anyone). Rows
are ready for all twelve guns, and one shows once its model is in the place. They're never in a crate (`L.cosmetics`)
or the shop's rotations (`Shop.liveSkins`), and the loadout shows them with no lock.

Tested in solo Play (place version 823):
- The crate pool and the shop's rotation hold no Classic, but do hold the gadget skins.
- `ar_classic` went on with nothing owned.
- `frag_lantern` was refused as not owned. With the owner's Studio loot unlock it went on, and so did Galaxy on the
  Frag.
- The loadout on the Frag Grenade showed the Paper Lantern wearing Galaxy, with Galaxy marked in WRAPS
  (`docs/shop/gadget-wrap.jpg`). SKINS showed Default, Powder Keg and Paper Lantern, the Lantern picked
  (`gadget-skin.jpg`).
- The test profile's own looks were put back afterwards.

Not seen yet: a gadget skin won from a crate's reveal on screen, and a gadget card in the shop.

## Robux, later

1. Make the developer products on the Creator Hub (one per container and bundle; one per kind and rarity for the
   singles) and paste their ids into `Shop.PRODUCTS`.
2. Turn `Config.LOOT_FREE` off and `Config.LOOT_ROBUX` on.
3. Then: the client asks the server (`ShopBuy`), the server checks the offer and shows Roblox's prompt, Roblox calls
   `ProcessReceipt` (`ShopReceipts.server.luau`, the only script that sets it), which has the loot server grant the
   offer (`Loot.grant(player, offerId, purchaseId)`, saved with the purchase id so a repeated receipt is granted once)
   and answers `PurchaseGranted` only after that save.
4. Paid random items: the odds are shown before any purchase (the ODDS button, the inspect panel and the confirm
   panel, every chance as a percentage with a TOTAL row), and a paid container can't be confirmed when its odds
   can't be read. Where `PolicyService` says `ArePaidRandomItemsRestricted` (the loot server's `restricted`), paid
   containers read NOT AVAILABLE HERE.
5. Roblox now also offers `MarketplaceService:BindReceiptHandler` (the docs call `ProcessReceipt` the legacy
   callback); either works, `ShopReceipts` uses `ProcessReceipt`. Prices shown with Robux on are the products' own
   (`GetProductInfo`, so regional prices are right); `Shop.PRICE` / `robux` are only what to price the products at.

## Testing it in Play

Set the local player's attribute `ShopTest` from the Client datamodel: `"open"`, `"open:bundles"`, `"count:spray:5"` (the x1/x5/x10 pick),
`"open::bundle_nightshift"`, `"inspect:crate"`, `"odds:crate"`, `"ask:bundle_quarry"`, `"commit"`, `"back"`,
`"close"`, `"fake:844x390"` (lays the shop out in a phone-sized box with an amber edge), `"real"`,
`"redeem:tix"` / `"redeem:brass"` (the confirm panel's REDEEM), `"askdeal:<skin>"` (one of the owner's deals).

The server side has its own test hooks, BindableFunctions in ServerStorage that reach the running modules:
- `JankVipDailyTest`: `("claim", p, prizeId?)`, `("reset", p)`, `("state", p)`, `("sim", n, "best"?)`.
- `JankDealsTest`: `("state", p)`, `("reset", p)`.
- The loot server's `dev` ops and Vip's `("dev", "lock" | "unlock")`, through their remotes from the Client
  datamodel.

**The trap: never `require` a server module from the command bar during a Play test** (execute_luau in the Server
datamodel). The command bar has its own module cache, so the `require` builds a second copy of the module, and of
anything it pulls in. A module that starts itself on require (Vip, Loot's remote handler, VipDaily, Deals) then sets
up again and takes over the shared remotes with empty state. Every later call goes to the copy: "still loading", a
Studio VIP lock that the real module never sees, an inventory restore that can't happen. This happened on 17 Nov
(place version 549). Reach a running module only through its test hook or its remote. Reading `Source` or instances
is fine, and so is requiring a `Clone()` of a pure shared module (one with no start code) in Edit.

## Tested (16 Nov 2026, solo Play, place version 367)

Photo sheet: `roblox/docs/shop/shop-sheet.jpg` (tiles 2 and 4 are from the first push, before the title row moved into
Roblox's top bar and the previews were fitted to their frames).

- Opened by the B key, the SHOP button and the client API (`open(tab, offerId)` through the `ShopTest` hook);
  a hub hologram uses the same `open`, through a ProximityPrompt's `ShopOpen` attribute.
- All four scripts compile; Studio's sources match the files byte for byte (checksums at each push).
- Featured: hero bundle, six daily singles, countdown. Bundles grid, containers, inspect with the item list.
- Claimed Field Issue (free): its four camos and the Cowboy Hat landed in the saved inventory (`Loot` "inventory").
- Claimed a Spray Can and a Duffel Bag: the confirm panel showed the odds (55 / 28 / 13 / 4 %, total 100.0%), the
  loot opening played (reel, reveal, DONE) with the shop stepped aside, and the inventory tab came back showing the
  new item (Camo, Crown) with a toast.
- The Crate reads COMING SOON (no weapon skins on Roblox yet).
- Loadout: an owned wrap (Camo) and hat (Crown) went on; an unowned wrap (Galaxy) was refused ("you don't own that
  one yet"); the owner's loadout was put back as it was.
- Phone-sized box (844 x 390): featured and inspect lay out; the inspect list scrolls.
- Fixed in the test: odds rows all reading TOTAL (a field-name clash), the inspect panel's list drawing through the
  confirm panel (the inspect panel now hides under it), a stale inspect panel after an opening.

Not tested: a real phone or tablet (only the phone-sized box), Robux (off), the hub's holograms (the hub session's).

## Player card looks (16 Nov, place version 398)

Borders, backgrounds ("banner") and titles from the player-cards session's `Shared.CardStyles` are sold too, when that
module is in the place: gun-less items `{ kind = "border"|"banner"|"title", id }`, singles `"border:<id>"` etc. (one
of the six daily singles), and the **Head Office** bundle (Brackets + Carbon + HEAD OF HR). They're drawn as flat card
tiles (`CardStyles.preview` in a sized 2.4 : 1 frame), never a 3D model; a card-only bundle has no hero, so it's never
the featured bundle or a hub hologram. The inventory has a PLAYER CARD section and a CARD filter. Ownership is the
loot inventory's bare ids (`inv.border` / `inv.banner` / `inv.title`).

Tested in solo Play (v398): Head Office claimed (all three owned), x5 Spray Cans with the live batch open (five reels,
"YOU GOT 5" grid, back to the shop: "5 THINGS ARE YOURS"), the CARD inventory section.

## Kill effects and emotes (17 Nov, place version 517)

The flair session's `Shared.Flair` (`roblox/src/shared/Flair.luau`) is sold like the card looks, when it's in the
place: gun-less items `{ kind = "kill"|"emote", id }`, singles `"kill:<id>"` / `"emote:<id>"` kept under the bare id.
- **What's for sale** is `Flair.forSale(kind)`: not free, not VIP, and an emote only once its clip is uploaded. Today
  that's Ember (rare), Ink and Ascend (epic), Static (legendary); Slow Clap (common), Fist Pump and Bow (rare), Groove
  (epic). Dissolve, Shatter, Wave, Salute and the default ("none") are free for everyone and never sold.
- **Where:** one of the six daily singles is a kill effect or an emote (it takes a hat's place). The Duffel Bag's line
  names them once the loot module keeps them (`LootTable.ownTypes()` has `kill` and `emote`).
- **On screen:** a square tile drawn by `Flair.picture` (`V.flair`), never a 3D model, so the inspect panel shows no
  DRAG TO TURN. A card reads "FOR EVERY KILL" or "FOR YOUR EMOTE WHEEL"; a claim's toast says PICK IT IN THE LOADOUT
  [L] (the equip screen is the flair session's FlairUI, from the loadout's KILL EFFECT · EMOTES button).
- **Inventory:** KILL EFFECTS and EMOTES sections and filters. The filter row scrolls sideways when it doesn't fit
  (a phone), and keeps the picked filter in view.
- **VIP:** a kill effect or emote of rarity "vip" (`Flair.isVip`) would join the VIP pack by itself; none is yet.

Tested in solo Play (place version 517): today's six had Static first (photo `docs/shop/shop-flair-daily.jpg`); its
inspect panel showed the tile, "LEGENDARY · KILL EFFECT · FOR EVERY KILL" and CLAIM 800 (`shop-flair-inspect.jpg`);
CLAIM gave the owner Static (the loot inventory's `kill` list) with "STATIC ADDED. PICK IT IN THE LOADOUT [L]"; the
KILL EFFECTS filter showed it (`shop-flair-inventory.jpg`); at phone size (844 x 390) the filters scrolled. The owner's
inventory was put back afterwards (195 things, no kill effect). Not seen on screen: an emote tile, and the picked
filter scrolling into view (added after the test).

### Moving previews (17 Nov)

The owner: "for kill effects in shop can they be small previews? same with in inv?" Kill effect and emote tiles on
cards (the daily row, the inventory, the inspect panel) play a small loop over their still tile. A chip in a list
stays still. `src/client/FlairAnim.luau` does it; anyone may use `FlairAnim.attach(frame, kind, id)`.
- **Kill effects:** a flipbook per effect, because a ViewportFrame can't draw particles. The VFX session captures
  each effect in Studio on a stand-in, as a 1024 x 1024 sheet of 4 x 4 frames on the tile's dark, with no text.
  The sheets are listed in `Shared.FlairSheets` (`kill[id] = { image, cols, rows, px, n, fps, hold, words? }`), and
  Blue Screen's words are drawn live over its frames. An effect with no sheet yet keeps its still tile.
- **Emotes:** a copy of your own avatar in a ViewportFrame inside a WorldModel (so it animates), doing the emote on a
  loop.
- **Cheap:** one stepper runs them all. Only a preview that's on screen plays: its gui on, every parent visible,
  inside its scrolling frame's view. At most 8 play at once; the rest hold still (emotes pause).
- **Grapples** aren't sold in the shop, so they have none.
- **Emote timing** follows the flair session's stand-in. A one-shot emote plays at priority Action4, in over 0.3 s,
  is let go 0.35 s before its end, rests 0.7 s, and starts again, so it never snaps at a loop's seam. A looping emote
  just loops. The clip, length and loop flag are read from `Flair.info` each time, because the emotes get remade.

Tested in solo Play (place version 588):
- With three emotes owned for the test, the inventory's EMOTES section showed the owner's own avatar doing each one
  (`docs/shop/shop-anim-emotes.jpg`). The tracks moved: 0.06 s to 0.88 s in 0.8 s.
- Switched to FEATURED, the same tracks held at speed 0.
- The inspect panel showed Groove big (`shop-anim-inspect.jpg`).
- The owner's inventory was put back.
- The kill effects' sheets came from the VFX session: 16 in place version 625, and Ink in version 630, retaken on a
  lighter wall and mapped back to the card's dark so its black ink shows. All 17 move now.

Tested in solo Play (place version 626), with six kill effects and two emotes owned for the test:
- The KILL EFFECTS cards stepped their flipbooks: Ascend, Big Duck, Blue Screen, Chickens, Shatter, Tombstone.
  Blue Screen showed its "FATAL ERROR" words live on its panel (`docs/shop/shop-anim-kills.jpg`).
- The emote cards' avatar copies, cameras and tracks were all there and playing, but the tiles were blank. The
  Studio window was hidden in that test, so no 3D drew anywhere: not the world, not the guns' previews. The new
  framing (on the body, feet near the bottom) still needs a look with the window shown.
- Looked at later with the window shown (place version 626, no change): Groove, Fist Pump and Slow Clap fill their
  tiles, feet near the bottom, the pastels cleaner than before (`docs/shop/shop-anim-emotes-framed.jpg`). A tall
  accessory, the owner's strawberry staff, touches the top edge, since the body is what's framed.
- The longest finisher blurb (the Infernal Rifle's, Hellgate) fits in full now that the blurb grows to its text
  (`shop-finisher-blurb.jpg`).
- The owner's inventory was put back.

### Kill effects on you (17 Nov, place version 638)

The owner: "kill effects should display your character over surrounds, and the preview should be your avatar, when
you look at it in the shop it looks pretty bad". So the flipbooks of a grey stand-in are out (kept only for a player
with no avatar to copy):
- **Cards** (and the inspect panel's view): a copy of your own avatar stands on a small set inside the card. The set
  is a floor disc with a thin ring in the item's rarity colour and a dark backdrop, the game's quiet palette. Your
  avatar stands in Roblox's idle. The flair session's real KillFx runs on it inside the card once KillFx sets
  `K.VIEWPORT` (its `opts.parent` / `opts.camera`). A ViewportFrame draws its solid pieces and the body's fades and
  moves (Big Duck, Tombstone, Chickens, Shatter's wedges), not particles, Highlights or Blue Screen's SurfaceGui
  words. Gibs is thrown by hand, since a WorldModel doesn't simulate. Emote cards stand on the same set.
- **PREVIEW ON YOU** in the inspect panel: the real effect, particles and all, played full screen on a copy of you.
  It runs on a set built high above the map (y 1,800), with a warm key light and a cool fill, the camera easing in. It
  takes about 2 to 3 s; SKIP / SPACE / a click ends it early. Every ScreenGui steps aside and comes back after, and so
  do the shop's blur and tint.

Tested in solo Play (place version 638), as the owner:
- Three kill effects in the inventory showed the owner's avatar on the set (`docs/shop/shop-kill-cards-set.jpg`).
  KillFx's viewport option isn't in Studio yet, so the effect doesn't run on the cards yet.
- Big Duck's inspect view showed the avatar big on the set with its gold ring (`shop-kill-inspect-set.jpg`).
- PREVIEW ON YOU played the real Big Duck on the set (`shop-kill-preview-on-you.jpg`), then the shop came back with
  the camera on Custom and the set gone.
- In the first try the set sat 11 studs low (its model pivot wasn't its origin) and the backdrop was nearly black.
  Both are fixed: `WorldPivot` at the origin, and two front lights.
- The ring on the big set is now a thin plain line, dimmed a little, and two side walls close the room, so no sky
  shows.

With KillFx's viewport option in (the flair session's place version 639), tested in solo Play (place version 648):
- The cards play the real effects on the owner's avatar (`docs/shop/shop-kill-cards-live-1.jpg`, `-2.jpg`): Ascend
  lifts it out of the frame, Big Duck turns it into the duck, Chickens run off, Tombstone rises, Balloons lift it.
  Shatter's wedges and Ascend's light are brief. Each loop rests on the empty set for a moment before the avatar
  comes back.
- The inspect view showed Balloons lifting the avatar (`shop-kill-inspect-live.jpg`).
- PREVIEW ON YOU on Balloons played the real effect, strings and glow, in the closed room with the thin blue ring
  (`shop-kill-preview-on-you-2.jpg`).
- The owner's inventory was put back.

**The card loop** (place versions 651 to 668, after the main session saw too many empty cards):
- Each loop starts with you standing (0.7 s); the effect plays; a beat of 0.3 s; then you're back.
- Cards side by side start up to 1.6 s apart, so a row never goes blank at once.
- The camera follows the body up and sideways while it rises or flies (Ascend, Balloons, Yeet), never down, so
  Tombstone stays framed with its stone. The frame is a little wider for kill effects.
- Once nothing of the body or the run's pieces (the duck, chickens, wedges) is in view for 0.25 s, the loop ends
  early.
- Each loop starts from a fresh copy of you. A KillFx run that ends on its own hides the body for good, as a dead
  body should, and `K.reset` only undoes a run still going, so after the first loop the cards stayed empty until
  this fix (version 668).
- Tested (version 668), with captures several loops in (`docs/shop/shop-kill-cards-loop-1.jpg`, `-2.jpg`): the
  avatar comes back every loop, and five of six cards show you or the effect at any moment.

### Finishers on skin cards (17 Nov)

The finishers session's cinematic finishers (roblox/docs/FINISHERS.md) belong to a few top-tier skins:
`Shared.Finishers.forSkin(skinId)` gives the finisher's id and its row (name, colour). In the shop:
- **A FINISHER pill** in the finisher's colour, top right, on a skin's daily card, deal card and inventory card, in
  the inspect panel's view, and left of OWNED on a list row (a set's or the VIP pack's).
- **PREVIEW FINISHER** in the inspect panel, over CLAIM: for a skin with one, or for a set or the VIP pack, the first
  of its skins that has one. It calls the client's `Finisher.preview(id, { skin = skinId })`, which plays the full
  cut (about 2.9 s) in front of you. That takes the camera and the screen and gives both back; the shop needs no
  camera of its own. The skin's blurb names its finisher.
- Built so far: ar_seraph, ar_infernal, lmg_ducky, revolver_ducky, katana_ducky.
- While a finisher plays, the shop's own blur and grey tint are off, so they don't sit over the cut. They come back
  once `Finisher.isPlaying()` goes false, if the shop is still up. A single's blurb has room for a third line.

Tested in solo Play (place version 603):
- The Seraph Rifle's inspect panel had the FINISHER pill, the blurb naming Ascension, and PREVIEW FINISHER over the
  buy button (`docs/shop/shop-finisher-inspect.jpg`).
- Pressing it played the cut sharp, with SKIP (`shop-finisher-preview.jpg`). After it, the shop was back with its
  blur and the camera was Custom.
- The inventory's VIP row showed the pill on the three Ducky skins (`shop-finisher-inventory.jpg`).
- In the first try the shop's blur stayed over the cut; that's what the fix above is for.
- The bigger, warmer emote tiles (body framing, the shop's light) are in this push but not yet looked at on
  screen.

### More than eight kill cards on screen (17 Nov, place version 689)

The equip screen's kill grid shows 12 cards; `FlairAnim` plays at most `MAX` = 8 at once. A card that lost its turn
mid-run let KillFx finish on its own, which leaves the body hidden for good, and it waited on an empty set; the same
eight always got the turns (the kill-fx-emotes session found it: MAKE IT RAIN, MISSING TEXTURE, CHICKENS, BLUE SCREEN
and YEET sat empty). Now:
- a kill card paused mid-run resets at once (a fresh copy of you, standing) and starts again soon after it's back on;
- with more than 8 on screen a window of 8 moves along them every `TURN` = 4.5 s, so every card plays.

Tested in solo Play: 12 test cards (Cash to Ink) in a grid, 8 playing at a time, and over three shots every card
played or stood with you in it; the top row that sat empty before played its turn (`docs/shop/kill-cards-12-turns.jpg`).

## Weapon skins and skin sets (16 Nov)

**Weapon skins** (a whole other body for one gun: `GunSkins.luau`, models in `ReplicatedStorage.JankfireSkins`, names
and rarities in `LootTable.SKINS`) are sold too. A skin is already one gun's, so it is owned under its bare id like a
card look (`Shop.gunless`). A skin is on sale once the loot module knows it and its model is in the place
(`Shop.skinLive`, the same check the loot module rolls the Crate by). One of the six daily singles is a skin
(`"skin:<id>"`, priced 150 / 300 / 600 / 1200 by rarity). The inventory shows skins first in each gun's section, with
a SKINS filter. Every preview builds the skin's body with `WeaponModels.build(weapon, 3, skinId)`.

**Skin sets** are the guns session's `Shared.SkinSets` (`SETS[setId] = { name, pair?, colour, accent, order,
members }`). Each set is a bundle whose offer id is the set id (`"set_seraph"`, `type = "bundle"`, `set = setId`):
- Its contents are its skins, and its hero is its top piece (the rarest skin), so a set can be the day's featured
  bundle or a hub hologram (`hero.skin`).
- It is on sale only when every skin in it is (`Shop.ready`). Bundle lists should use `Shop.shown(true)`.
- Its price is 60% of its skins one by one. Completing a set you have some of costs that share of the set's price
  (`Shop.setPrice(o, missing)`). The loot server's `("buy", "set_seraph")` gives only the skins you lack.
- With Robux on there is one product for the whole set and one per count left (`"set_seraph:3"`).
  `Shop.productFor(o, missing)` picks the product, and `ShopReceipts` counts what the buyer lacks.

On screen:
- **The banners** sit at the top of BUNDLES, under SKIN SETS. A pair (`pair`, e.g. Seraph | Infernal) shares one row,
  joined; lone sets go two to a row. Each banner has:
  - the set's colour washed in from the right and a little glow in its accent colour, with a 3 px accent line along the
    bottom;
  - its top piece turning slowly in 3D;
  - the name, "2 / 5 OWNED" and a bar in the accent colour;
  - the price, or SET COMPLETE;
  - its five skins along the bottom: the ones you own lit with an accent line, the rest dimmed.
- **Complete the set** is the set's inspect panel:
  - the five skins, each OWNED or not (tap one to see it big);
  - "N / 5 OWNED" with the bar;
  - one button: CLAIM THE SET, COMPLETE THE SET · 3 LEFT, or SET COMPLETE.

No uploaded banner art: every picture is the live models in 3D.

The words on screen were also cut to what a player needs (the owner's no-flavour-text rule). Bundles say what's in
them (`Shop.describe`: "4 wraps and a hat for the Assault Rifle, SMG, Revolver and Pistol."), containers say what
they give, and the top line is just "Free while we test. The prices are for later."

Tested in solo Play (place version 423). The guns session's set models weren't in the place yet, so the test used a
temporary `SkinSets` of four sets made from live skins, deleted before saving. Photo sheet:
`roblox/docs/shop/shop-sets.jpg`.
- Banners: the pair joined on one row and the two lone sets on the next, each with its top piece, progress and five
  chips.
- Completing a set: owning 2 of 5 (set with the loot `dev set` op) showed "3 LEFT · 1,399" and COMPLETE THE SET ·
  3 LEFT. CLAIM gave exactly the 3 missing skins, then the panel read SET COMPLETE and the banner 5 / 5 with every
  chip lit.
- The phone-sized box (844 x 390) showed the banners.
- Opened straight onto a bundle (`open::bundle_nightshift`), BACK closed the shop. Opened normally and then into the
  same bundle, BACK went back to the list.
- Opened straight onto the Spray Can, a claim played the opening, and DONE (clicked) ended back in the game with the
  shop shut.
- The owner's inventory was put back to its 138 items afterwards.

Later:
- The real sets showed up by themselves (place version 437): Seraph | Infernal on one row, Witching Hour and Tidecrest
  on the next. Ducky is VIP only, so it isn't among them.
- The space-western pair (place version 478): Dust Drover | Star Drover (`set_dust`, `set_star`, orders 6 and 7) are
  both ready, with 5 skins each, a revolver as the top piece and 2,339 each. They take the third row, as a pair. This
  was checked by reading the shop in Edit, not on screen.
- The 17 concepts (the new decorated ones included) aren't live and have no offer.
