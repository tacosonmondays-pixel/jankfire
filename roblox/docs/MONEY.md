# Money: passes, products, prices and the switch

Everything the game sells for Robux, what it costs, where the ids are, and how real money is turned on. Written by the
shop session (18 Nov 2026). The owner asked: "Make them for the shop bundles as well, bundles, coins, buying weapons
with coins make sure thats a thing".

**Coins are Brass**, the quests' soft currency (`QuestData`, the HUD's Brass, the player attribute `Brass`). There is
no second currency.

## The switch

Real money is **off**. Two lines in `roblox/src/shared/Config.luau` turn it on:

| Switch | Now | For real money |
|---|---|---|
| `Config.LOOT_FREE` | `true`: everything in the shop is free to claim | `false` |
| `Config.LOOT_ROBUX` | `false`: no prompt is ever shown, `ProcessReceipt` isn't even set | `true` (**the** switch: `Shop.ROBUX`) |
| `Unlocks.WEAPONS_ROBUX_FREE` (`shared/Unlocks.luau`) | `true`: the four Robux weapons are free for everyone ("FREE FOR NOW") | `false` |

- While `LOOT_FREE` is on, `Shop.free()` wins: nothing prompts even if `LOOT_ROBUX` is on.
- `WEAPONS_ROBUX_FREE` only locks the weapons. With it off and `LOOT_ROBUX` still off, they can be bought with Brass
  but not with Robux.

**Before the switch goes on:**

1. Put the VIP pass on sale (Creator Hub > Monetization > Passes). It was made off sale.
2. Answer the experience questionnaire: the game has paid random items (the containers). See LOOT.md, "Roblox's rules
   for paid random items". The odds and PolicyService parts are already built.
3. Decide whether paid weapons may be used in ranked (PROGRESSION.md, "Ranked").
4. Publish.

## Every price (one table: `Shop.MONEY` in `shared/Shop.luau`)

Change a Robux price in **both** places: `Shop.MONEY`, and the product on the Creator Hub (Monetization > Developer
Products). Roblox charges the product's price. With Robux on, the shop shows the products' own prices
(`ShopUI.livePrices`), so a mismatch shows the right number but the catalog is wrong. Brass prices are only in the
table.

| What | Robux | Brass |
|---|---|---|
| VIP (game pass) | 399 | |
| Crate / Duffel Bag / Spray Can | 120 / 90 / 60 | redeem: `QuestData.PRICES` (Bag 2,500, Spray 1,000; tickets 12 / 6 / 3) |
| A wrap, by rarity common / rare / epic / legendary | 75 / 150 / 300 / 600 | |
| A hat | 100 / 200 / 400 / 750 | |
| A weapon skin | 150 / 300 / 600 / 1,200 | |
| A card border or background | 50 / 100 / 200 / 400 | |
| A card title | 40 / 80 / 160 / 320 | |
| A kill effect or emote | 100 / 200 / 400 / 800 | |
| A themed bundle | 60% of its items' singles, ending in 9 (`bundleShare`) | |
| A skin set | its skins' whole worth; completing it: that share, rounded up | |
| A deal | the skin's price less 20-40% (`Shop.DEAL_OFF`, `DEAL_TOP`) | |
| **Minigun** | **249** | **5,000** |
| **Big Laser Pointer** | **199** | **4,000** |
| **Chicken Rocket** | **199** | **4,000** |
| **Lefty & Righty** | **249** | **5,000** |
| **500 Brass** | **39** | |
| **1,100 Brass** (1,000 + 100) | **79** | |
| **2,400 Brass** (2,000 + 400) | **159** | |
| **6,500 Brass** (5,000 + 1,500) | **399** | |

Why these numbers:
- **Brass packs.** The bigger packs give 9%, 18% and 27% more Brass per Robux than the small one.
  - Even the best rate (6,500 for 399, about 16.3 Brass a Robux) makes Brass-bought containers cost more than buying
    them with Robux: a Spray Can's 1,000 Brass is about 61 Robux against its own 60.
  - So the packs never undercut the shop.
- **Weapons for Brass.** An active player earns roughly 1,000-1,500 Brass a week from quests and the weekly track, so a
  weapon is 3-5 weeks of play.
  - Buying that Brass in packs costs more than the weapon's Robux price (4,000 Brass is about 245 Robux against 199).
- **No pay-to-win beyond what was already planned.** The four weapons were already the Robux exclusives
  (PROGRESSION.md). They now also come from play, with Brass.

## The VIP game pass

| Pass | Id | Price | State |
|---|---|---|---|
| VIP | **2093409349** | 399 | off sale; icon: the gold Royal Duck (asset 113037419360696); made by the main session |

`Shop.VIP_PASS = 2093409349`. `Vip.luau` checks `UserOwnsGamePassAsync` on join. While the shop is free, anyone can
still claim VIP from the shop (unchanged). With Robux on, GET VIP shows the pass prompt.

## Developer products

None existed before. They are made with Open Cloud (`POST /developer-products/v2/universes/10776367667/developer-products`, scope
`developer-product:write`, multipart with an icon image). Each is on sale but its store page is off, so it can only be
bought from an in-game prompt, and the game prompts nothing while `LOOT_ROBUX` is off.

**State: not made yet.** The create call only takes multipart, and the upload tool only sends multipart with an image
file. The icons folder `roblox/docs/money/icons` isn't an approved upload folder yet (Assistant Settings > MCP
Permissions). 88 products are ready to make: the list is below.

| Key in `Shop.PRODUCTS` | Name | Robux | Icon | Id |
|---|---|---|---|---|
| `crate` / `bag` / `spray` | Crate / Duffel Bag / Spray Can | 120 / 90 / 60 | skins / hats / wraps | |
| `bundle_nightshift` ... `bundle_quarry` (6) | Night Shift 1,099, Field Issue 289, Tea House 869, Deep Space 1,499, Machine Shop 619, Quarry 1,219 | | wraps | |
| `bundle_cards` | Head Office | 169 | hats | |
| `set_<id>` (6 sets) | Seraph, Infernal, Witching Hour Set 3,300; Tidecrest 3,000; Dust Drover, Star Drover 3,900 | | skins | |
| `set_<id>:1` .. `:4` (24) | "<Set> Set, last n" (the n skins you're missing) | a fifth of the set per skin | skins | |
| `<kind>:<rarity>` (32) | "Epic Wrap", "Legendary Card Title" ... (8 kinds x 4 rarities) | the singles table | by kind | |
| `deal:<rarity>:<pct>` (8) | "Deal: Epic Skin, 30% Off" ... | 109-779 | skins | |
| `weapon:minigun` ... (4) | the weapon's name | 199-249 | the weapon | |
| `brass:brass_500` ... (4) | "500 Brass" ... | 39-399 | brass | |

The icons are crops of the web game's model render sheets (`tools/blender/sheets`, the 3/4 view, no text).
`roblox/tools/icon_crop.ps1` cuts them; the eight are in `roblox/docs/money/icons/`.

## How a purchase works

- **The client asks.** It fires `JankfireRemotes.ShopBuy` with an offer id:
  - a container, bundle, set or single (`Shop.offer`);
  - `deal:<skin>`;
  - `weapon:<id>` (`Shop.weaponOffer`);
  - `brass:<pack>` (`Shop.brassPack`).
- **The server prompts** (`ShopReceipts.server.luau`). It checks the offer and the product, remembers what was asked
  (singles and deals share a product per tier), and shows Roblox's prompt. It won't prompt for a weapon the player
  already owns.
- **Roblox calls `ProcessReceipt`.** ShopReceipts:
  1. answers `PurchaseGranted` for a receipt it already granted (`Purchases.seen`: the receipt record);
  2. grants the purchase:
     - loot: `Loot.grant(p, offer, purchaseId)`;
     - a deal: `Deals.grant`;
     - a weapon: `Purchases.giveWeapon(p, wid, "robux", purchaseId)`;
     - Brass: `Quests.buyBrass(p, amount, purchaseId)`;
  3. marks the receipt (`Purchases.mark`), then answers `PurchaseGranted`.

  Every grant is written to its save before it answers true, and each is idempotent by the purchase id. So a receipt
  sent twice is granted once even if the record write was lost. Anything that fails answers `NotProcessedYet`, and
  Roblox tries again on the player's next join.
- **The receipt record** is in `Purchases.luau`'s save:
  - store `JankfirePurchases_v1`, and `JankfirePurchases_v1_studio` in Studio (`Profiles.new` adds it), never the live
    one;
  - session-locked per player;
  - the newest 500 receipts.

## The Robux weapons, for Robux or Brass

- **Which:** `Unlocks.ROBUX`: `minigun`, `laser`, `chicken`, `akimbo`. Prices are in `Shop.MONEY.weapons`.
- **Kept by `Purchases.luau`.** It sets the player attribute `RobuxOwned` (`"laser,minigun"`), which
  `Unlocks.forPlayer` reads on both sides. The loadout server refuses a pick of one you don't own once they aren't
  free.
- **With Brass, the server buys it** (`JankfireRemotes.Purchases` `"brass"`, wid). It checks the price and your Brass,
  then writes three things in order:
  1. a pending mark (Purchases);
  2. the Brass, taken by `Quests.spendBrass` in the quests' save (idempotent by the id `weapon:<wid>`);
  3. the weapon (Purchases).

  A crash between them is settled on the next join: `Quests.spent` tells whether the Brass went.
- **Where to buy:**
  - the shop's **WEAPONS** tab: the four weapons, with Robux and Brass buttons, and the Brass packs below them;
  - the loadout: the EQUIP button splits into Robux and Brass for a locked one.

  The Brass button asks for a second press ("SURE? 4,000") before it spends. While `WEAPONS_ROBUX_FREE` is on, the cards
  say FREE FOR NOW and sell nothing.

## Gifts from the owner (the dev menu's GIFT tab)

| Gift | Call |
|---|---|
| Brass (and tickets) | `Quests.gift(player, brass, tickets, id)`: uncapped, idempotent by id, not counted as earned |
| VIP | `Vip.gift(player, on?)`: VIP for good whatever the switches, saved on the player's VIP key; `false` takes it back |
| A Robux weapon | `Purchases.giveWeapon(player, wid, "gift", id)` |
| Containers, bundles, items | `Loot.grant` (as before) |

## Testing in Studio

Studio test purchases charge nothing.
- **Turn the paid shop on inside a Play test:** from the **Play server's** command bar:

  ```lua
  game.ReplicatedStorage:SetAttribute("MoneyTest", true)
  ```

  - `Shop.ROBUX` turns on and `Shop.free()` turns off, on the server and on every client.
  - The Robux weapons lock (`Unlocks.robuxFree`), and ShopReceipts sets `ProcessReceipt`.
  - It's read only in Studio, and it goes when Play stops (never saved).
- **`UnlockAll`:** the owner and Studio start with every weapon open. The Loadout remote's `("unlockall", false)`
  shows the locks.
- **`ServerStorage.JankMoneyTest`** (a BindableFunction):
  - `("receipt", userId, productId, purchaseId)` gives the decision a simulated receipt gets;
  - `("ask", userId, offerId, productId)` remembers an ask, for a shared product;
  - `("vipgift", userId, on)` calls `Vip.gift`.
- **`JankfireRemotes.Purchases`:** `("state")`, `("brass", wid)`, and `("dev", "forget", wid)` (Studio + owner: takes a
  weapon back).
- **The quests' Brass:** `ServerStorage.JankQuestTest` `("data", uid)` and `("put", uid, data)` for a snapshot and its
  restore.

## Planned but not built (the audit, 18 Nov)

Found in SHOP.md, LOOT.md, PROGRESSION.md, PORT-PLAN.md, LootTable and Vip; none of these were built here.
- **Paid private servers.** Roblox sells them from the Creator Hub (Monetization > Private Servers, a monthly price);
  the game needs no code. The match servers CrossServer reserves are free, and unrelated.
- **Premium Payouts.** Roblox pays them on Premium members' playtime, with no code. A Premium perk in game
  (`MembershipType`) isn't planned anywhere.
- **A season / battle pass.** PORT-PLAN question 5 lists a "season pass" among the wanted lobby menus. The weekly
  quest track exists (QUESTS.md); a paid track does not.
- **"Premium" in the hub armory means 26 gimmick weapons** (PORT-PLAN section 53, the owner's rule: "anything that isnt a
  standard real life gun"). Only four of them are Robux weapons; the rest open by level. Selling more of them would be
  a progression change for the owner to decide.
- **Paid weapons in ranked:** the owner's call before `WEAPONS_ROBUX_FREE` goes off (PROGRESSION.md).
