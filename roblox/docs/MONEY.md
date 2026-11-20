# Money: passes, products, prices and the switch

Everything the game sells for Robux, what it costs, where the ids are, and how real money is turned on. Written by the
shop session (18 Nov 2026). The owner asked:
- "Make them for the shop bundles as well, bundles, coins, buying weapons with coins make sure thats a thing"
- "we then also need a shop page for coins yea"
- coin packs at 99, 499, 1999 and 4500 Robux

**Coins** are the one soft currency. In the code they are still Brass: the quests' wallet (`QuestData`, the player
attribute `Brass`, `Quests.luau`, the id `"brass"`). Since 18 Nov every screen calls them Coins and shows the gold coin
(`QuestData.CURRENCY.brass = "Coins"`, `QuestUI.icon`). They are:
- earned from quests and the weekly track;
- bought in coin packs;
- spent on containers (redeem) and on the Robux weapons.

There is no second currency: two would confuse players.

## THE ROBUX RULE (19 Nov 2026, the owner: "make sure only skins cost robux!" and "weapons shouldnt have a tab then!")

In the place since version 1070 (live at the owner's next publish). `Shop.robuxFor(o)` decides it, and every screen and
the receipts follow it.

**What Robux buys:**
- weapon skins, singly or as a skin set (coins buy them too: the buy panel shows Robux first, then "OR N COINS");
- containers: Crate, Duffel Bag, Spray Can (coins and tickets too; the odds and the restriction checks as before);
- coin packs (99 / 499 / 1,999 / 4,500, with the big packs' extras) and the VIP pass;
- gifts of those: a weapon skin, a skin set, coins, a container, VIP ("VIP Gift").

**Coins only:**
- every weapon:
  - the four Robux weapons are locked (`Unlocks.WEAPONS_ROBUX_FREE = false`) and bought for their coin price in
    the loadout's armory (4,000 / 5,000);
  - level weapons open by level, or early with coins (the early-unlock table);
- gadgets (by level or early coins);
- wraps, hats, card looks, kill effects, emotes, and the bundles of those (40% under their pieces' coin prices);
- the owner's deals (a coin discount on a skin);
- the weapon bundles (Assault, Explosives): coin bundles in the armory (below).

**The shop has no WEAPONS tab** (its page is never opened; a prompt for it opens FEATURED).

**Already bought for Robux stays bought.** The weapon and weapon-bundle developer products are OFF SALE
(3733204206, 3733204303, 3733204322, 3733204340, 3733671860, 3733671907): never prompted, never in a gift. Their
receipts are still granted. The other products for coins-only things stay on sale but are never prompted (late
receipts granted).

**Loadout:** a saved pick of a weapon the player can't carry now is carried as the slot's default. The pick stays saved
and comes back the moment the weapon is theirs: bought, unlocked, levelled or gifted. Nothing is erased.

**Tested 19 Nov, place version 1070** (solo Play, the owner's `_studio` saves, restored after):
- Locking: at level 1 with UnlockAll off, a saved Minigun pick was carried as the AR and the Revolver as the Pistol.
- Buying back: the Minigun bought for 5,000 coins was in the loadout at once.
- Dev-menu gift: GIFT gave the Big Laser Pointer.
- Bundle quotes: Explosives 17,100 coins (parts 22,800); Assault 5,200 with the Minigun already owned.
- Bundle purchase: buying Assault unlocked the Burst Rifle, LMG and Marksman Rifle and gave its cosmetics, then
  its quote showed YOURS.
- Shop screens: no WEAPONS tab; the Crate's panel shows BUY 120 Robux, OR 900 COINS, REDEEM 12 TICKETS.
- Armory photo: `money/armory-coin-bundles.jpg`.

## The coins-only shop (ON since 19 Nov, the owner approved the prices; live at the next publish)

The owner: "wraps and skins that aren't a part of bundles should be coin purchased; the only thing you buy with robux are
weapons, gadgets and bundles, like in rivals". Built and tested; in the place since version 1037, and **on** since 19 Nov:
`Shop.SINGLES_COINS_ONLY = true` in `shared/Shop.luau` (the owner: "Default everything else", the proposed prices accepted).

With it on:
- **Robux:** the four Robux weapons (or coins, as now), bundles and skin sets, coin packs, VIP.
- **Coins only, no Robux button:**
  - single wraps, hats, weapon skins, kill effects, emotes, card borders, backgrounds and titles;
  - the owner's deals (a coin discount);
  - containers (Crate, Duffel Bag, Spray Can), which tickets still redeem.
- **The server takes the coins** (`JankfireRemotes.Purchases` "coins": a pending mark, `Quests.spendBrass`, then
  `Loot.grant` / `Deals.grant`, idempotent by the id; settled on the next join after a crash).
- **The paid-random-items rules stay:** odds before every open, and no coins for containers where the policy restricts
  a player.
- **Not enough coins** opens the COINS tab.
- **The developer products for singles, deals and containers** stay on Roblox but are no longer prompted. A late
  receipt for one is still granted.
- **Gadgets:** none are sold. All 13 live gadgets open by level (Unlocks.LEVEL). The ones that would fit a Robux or
  coins buy, like the four weapons: Reverse Card, Instant Camera, Pop Quiz, Night Vision Goggles, Speed Trap, Laptop,
  Rubber Duck. That's the owner's call; nothing is built for it.

**Coin prices** (`Shop.MONEY.coinPrices`), paced to what a player earns: quests pay 30 / 50 / 80 coins (three a day,
about 160) and the weekly track 525 a week. That's up to about 1,650 a week, and 1,000-1,500 for a regular player:

| Coins | Common | Rare | Epic | Legendary |
|---|---|---|---|---|
| Weapon skin | 300 | 800 | 2,000 | 5,000 |
| Wrap | 200 | 500 | 1,200 | 3,000 |
| Hat | 250 | 600 | 1,500 | 3,500 |
| Kill effect | 250 | 600 | 1,500 | 3,500 |
| Emote | 250 | 600 | 1,500 | 3,500 |
| Card border | 150 | 400 | 900 | 2,000 |
| Card background | 150 | 400 | 900 | 2,000 |
| Card title | 100 | 300 | 700 | 1,500 |

| Containers | Coins | Or tickets |
|---|---|---|
| Crate (a weapon skin) | 900 | 12 |
| Duffel Bag (a hat, card look, kill effect or emote) | 600 | 6 |
| Spray Can (a wrap for one gun) | 500 | 3 |

**Both prices, every count** (19 Nov, the owner: "if you have coins the robux icon disappers for containers"). A container's card and its inspect panel show the Robux price (with the Robux mark) and the coin price side by side at x1, x5 and x10 (`ShopBundles.pair`). Before, x5 and x10 had no Robux product, so they showed coins only and the Robux mark vanished. The five and ten packs now have their own products, plain multiples of one (`Shop.containerProduct(cid, n)`, key `"crate:5"`): the client asks `ShopBuy` with `"crate:5"`, and the receipt grants five into stock under the one purchase id (`Loot.grant(p, "crate", pid, 5)`). The same restricted-player and odds checks apply. A coin price you can't afford is greyed; pressing it opens COINS. Pressing it when you can afford it opens the confirm with coins first and Robux as the other way.

Deals: the skin's coin price less the deal's 20-40% (an epic skin at 35% off: 1,300).

**Early unlocks** (19 Nov, the owner: "coin is supposed to be able to buy weapons early!"). Switch
`Shop.EARLY_ON = true` since 19 Nov (Studio test attribute: `EarlyTest`). A weapon or gadget that opens at a level (Unlocks.LEVEL, 2 and up) can
be bought with coins before the player reaches that level:
- It's kept for good. The server takes the coins and records it like a Robux weapon (Purchases "early", the
  RobuxOwned list), and reaching the level later changes nothing.
- The armory tile says "LV 7 · or 1,500 COINS", and its button says UNLOCK NOW, then SURE?.
- The shop's WEAPONS tab has an UNLOCK EARLY row with every weapon the player hasn't reached yet.
- The four Robux weapons keep their own Robux and coin prices.

| Opens at level | Coins |
|---|---|
| 2-3 | 500 |
| 4-6 | 1,000 |
| 7-9 | 1,500 |
| 10-12 | 2,000 |
| 13-15 | 2,500 |
| 16-18 | 3,000 |
| 19-21 | 3,500 |
| 22-25 | 4,000 |

The top band stays under the Robux weapons' coin prices (4,000-5,000). At about 1,300 coins a week, a level-2 weapon
is about 3 days of coins, and a level-25 one about 3 weeks.

**The pace** at about 1,300 a week:
- a common skin in about 2 days, a rare in 4;
- an epic in about 1.5 weeks, a legendary in about 4.

Each container costs about what its items are worth on average at the odds (the Crate's skins average about 850), and it
never gives a duplicate. No change to quest or match rewards is needed for this pace.

**For the owner to look at:**
- **Coin packs against these prices.** The cheapest pack (1,200 coins for 99 Robux) buys four common skins, and the
  biggest one's rate makes a legendary skin about 320 Robux of coins. A single legendary used to be 1,200 Robux. If
  that is too generous, the packs can give fewer coins.
- **Redeem prices.** With the switch on, the quests' coin redeem prices (QuestData.PRICES: Duffel Bag 2,500, Spray Can
  1,000) are replaced by the table above; ticket prices are unchanged.

Tested 18 Nov, place version 1037 (`CoinsOnlyTest` on in the Play server only):
- a legendary skin from the day's singles for 5,000 coins; a second buy said "you have it already";
- a Spray Can for 500;
- a Crate refused while restricted;
- an epic deal at 35% off for 1,300;
- a bundle refused for coins ("that's sold for robux");
- the FEATURED and CONTAINERS tabs show coin prices (`money/coins-only-featured.jpg`, `money/coins-only-containers.jpg`).

The loot and coins saves were put back. The test deal stays marked as had on the `_studio` save until the day turns.

## Weapon bundles (ON since 19 Nov; COIN bundles in the armory since the Robux rule, below the top)

Since the owner's Robux rule (top of this file) they are **coins, in the loadout's armory**, not the shop. Each one unlocks
every weapon in it the player can't carry yet (its Robux weapon at its coin price, each level weapon at its early-unlock
price) and gives the cosmetics they lack, 25% under those coin prices (`Shop.WBUNDLE_OFF`, Purchases "wbquote" /
"wbundle"). Assault from nothing: 8,950 coins (parts 11,950). Explosives: 17,100 (parts 22,800). The Robux text below
is how they were first built.

The owner: "we should have bundles that include some free weapons too, maybe assault bundle can come with like burst
minigun smg etc. Explosives janky can come with like pepper a couple other silly ones". Robux only.
- **The switch:** `Shop.WEAPON_BUNDLES_ON = true` since 19 Nov in `shared/Shop.luau` (Studio: `ReplicatedStorage` attribute
  `WeaponBundlesTest` in a Play test).
- **Where they show:** the shop's WEAPONS tab, a WEAPON BUNDLES row under the four Robux weapons. Each card opens the
  bundle's panel (BUY, and GIFT once gifts are on). They are not in the BUNDLES grid, the featured pick or the hub's
  holograms; the armory's hologram pads can show them later.
- **What they give:**
  - the bundle's Robux weapon, for good (`Purchases.giveWeapon`), so it stays unlocked when `WEAPONS_ROBUX_FREE`
    goes off;
  - a wrap for each weapon in it, for that weapon only (the cosmetic bundles' wraps are on every gun);
  - a hat or card looks.
  - Existing wraps, hats and card looks only, because skins are paused.

| Bundle | Weapons (each with its wrap) | Also | Parts one by one | Price |
|---|---|---|---|---|
| **Assault** | Minigun (Tiger), Assault Rifle (Camo), SMG (Duct Tape), Burst Rifle (Ghost), LMG (Moss), Marksman Rifle (Wood Burl) | title ZERO RECOIL, background Camo | 1,359 | **799** |
| **Explosives** | Chicken Rocket (Lava, and the Googly Eyes hat), Bowling Ball Launcher (Bowling Alley), Hot Sauce (Ketchup & Mustard), Frag Grenade (Hazard Stripes), Party Popper (Sprinkles), Peel Shooter (Memphis 90s), Shopping Cart Cannon (Receipt) | background Furnace | 1,474 | **799** |

The parts are priced at today's Robux prices: the weapon (Minigun 249, Chicken Rocket 199) plus each wrap, hat and card
look at its single price. Both bundles cost about 41-46% less than their parts.
- **Products:** "Assault Weapon Bundle" 3733671860 and "Explosives Weapon Bundle" 3733671907, both 799.
- **Receipts:** ShopReceipts gives the weapon first, then `Loot.grant` gives the cosmetics. Each step is idempotent by
  the purchase id.

**For the owner:**
- **Someone who already owns the weapon** pays the same price. Splitting the price would need a second product per
  bundle.
- **"Pepper"** is read as Hot Sauce.

## The big coin packs' extras (ON since 19 Nov)

The owner: "the bigger packs should come with rewards like rivals gives you, weapon skins for the 2 biggest packs, a
finisher for a random weapon I think, a gold wrap, a skin case etc".
- **The switch:** `Shop.PACK_EXTRAS_ON = true` since 19 Nov (Studio: `PackExtrasTest`).
- **1,999 Robux pack:** 28,000 coins, plus ONE legendary weapon skin the player picks, plus 1 Crate.
- **4,500 Robux pack:** 70,000 coins, plus ONE skin with a finisher the player picks, plus the Bullion wrap on every
  gun, plus 3 Crates.
- **The tiles** list the extras under the coin amount: "+ LEGENDARY SKIN · + CRATE" and
  "+ FINISHER SKIN · + GOLD WRAP · + 3 CRATES".

**How the skin works:**
- **Picked, never random.** A random item bought with Robux would be another paid random item.
- **The pick waits in the buyer's save** (`Purchases`, `data.extras`, the player attribute `PackPicks`) until it's made.
  The shop's PICK panel comes up right after the purchase and every time the shop opens until then. A crash never
  loses it.
- **The lists** (`Shop.PICKS`; any skin not in the place drops out):
  - legendary: Keytar, Neon Tube, Musket, Butterfly, Reaper, Golden Duck, Anime Aura (legendary skins that are no
    set's piece);
  - finisher: Seraph Rifle, Infernal Rifle, Sakura, Pumpkin Patch, Dust Drover, Iron Horse, Star Drover,
    Streamliner.
- **Already own the whole list:** the skin comes as 5,000 coins instead (a legendary skin's coin price), and the
  panel says so.

**Bullion** (`packgold`, Roster) is a new wrap made only for the 4,500 pack:
- antique gold with bright gold pieces, metal. Not Mastery Gold, which stays earned by weapon level;
- never in a container, the rotation or a bundle (`Shop.PACK_GOLD`, `LootTable.exclusive`);
- already owned: 3,000 coins instead.

**The Crates** follow the paid-random-items rules:
- odds are shown before any opening;
- a player Roblox's policy restricts gets coins instead, 900 a Crate.

**Every purchase gives the extras again**, with the same coins rules. Each part is decided once, written, then given
under its own id (`<purchase>:crates`, `:gold`, `:skin`), so a receipt Roblox sends twice gives nothing twice.

**For the owner:**
- **Every finisher skin is a skin set's piece** (Shared.Finishers): the 4,500 pack gives a player one piece of a set,
  and buying that set later costs only the pieces they're missing.
- **The legendary list** leaves out set pieces, so sets keep their own rule.

## Gifts (ON since 19 Nov)

The owner: "weapon bundles should be gamepasses too! I want people to be able to gift them! Should all passes be game
passes?"
- **Why not game passes.** Roblox has no gifting of game passes: a pass is only ever bought for your own account. So
  the bundles stay developer products, and the shop gifts them itself.
- **VIP stays a game pass** (a perk for yourself). To give VIP to someone else there is a separate product,
  "VIP Gift" (3733671921, 399), that grants VIP.
- **The switch:** `Shop.GIFTS_ON = true` since 19 Nov (Studio: `GiftsTest`).

**What can be gifted** (`Shop.giftable`):
- the cosmetic bundles, the weapon bundles, a whole skin set and the coin packs;
- VIP, through "VIP Gift";
- never a container or a single item.

**How it works:**
1. **GIFT** sits beside BUY in a bundle's or set's panel and in VIP's, and next to each coin pack's price.
2. The buyer picks who gets it: anyone in the server, or a Roblox user name. A name is accepted only if that player has
   played the game before (a loot save of theirs exists).
3. The buyer pays the offer's own product. The server remembers who it's for (`ShopReceipts`, the ask).
4. The receipt writes the gift into the receiver's **gift box** before it's granted. The box is its own data store,
   `JankfireGiftBox_v1` (`_studio` in Studio, one key per receiver; `server/Gifts.luau`).
5. The box empties into the receiver's things as soon as they're in a server:
   - in this server: at once;
   - in another: that server is told over MessagingService;
   - offline: on their next join.
   Each gift is given once, by `gift:<purchase id>`.
6. **Everyone is told:**
   - the receiver gets the present-box reveal (GiftReveal, DevFx "gift");
   - the chat says "<buyer> gifted <receiver> <what>" in the receiver's server, and in the buyer's too if that's
     another server;
   - the buyer's shop says "GIFT SENT TO <name>".
7. **A restricted receiver** (Roblox's paid-random-items policy) never gets a container: a gifted pack's Crates come as
   coins, decided for the receiver.

If the server restarts between the prompt and the receipt, the ask is lost and the purchase goes to the buyer instead
(VIP Gift: VIP for the buyer).

## Review build tested (19 Nov 2026, place version 1058, every switch OFF in the place)

A solo Play on the owner's `_studio` saves. Every switch was on in the Play server only (`MoneyTest`,
`WeaponBundlesTest`, `PackExtrasTest`, `GiftsTest`, `EarlyTest`). Receipts were simulated with
`JankMoneyTest`; nothing was charged.

**Early unlock** (level 1, UnlockAll off for the test):
- Revolver for 500 coins: open at once, and RobuxOwned lists it.
- Buying it again is refused ("you have it already"); so are the level-1 AR and the Robux Minigun.

**Assault receipt:**
- Minigun kept for good, plus Tiger@minigun, Camo@ar, Wood Burl@dmr, ZERO RECOIL and the Camo background.
- The same receipt again was granted once only.

**Coin packs, as a restricted player:**
- 1,999 pack: +28,000 coins, plus 900 coins instead of the Crate, plus a legendary pick waiting.
- 4,500 pack: +70,000 coins, plus 2,700 coins instead of 3 Crates, plus Bullion on every gun (gadgets too), plus a
  finisher pick waiting. No container stock was added.
- **The PICK panel** showed the 4 live legendary skins, then the 8 finisher skins (`money/pack-pick-panel.jpg`).
  - An off-list skin was refused.
  - Keytar and Infernal Rifle were given; a second pick under the same purchase gave nothing; PackPicks cleared.

**Gift** (the hook only, to the tester): the Quarry bundle landed through the gift box, with the present reveal
"GIFT FROM ..." and its six items (`money/gift-reveal.jpg`).

**Restored afterwards:**
- the loot inventory (42 things, no every-gun marks, stock 0);
- the quests save, exactly (coins 0);
- the Minigun and Revolver forgotten, the extras records cleared.

**The look pass:** `money/look-pass-before-after.jpg`, desktop. Phone-size photos are still to take.

**Others' openings:**
- A bystander's view: `money/bystander-opening.jpg`.
- The inventory bench (800 wraps): 1.36 s and about 11 fps before; 0.22 s and about 60 fps after.

## The switch

Real money is **LIVE** since 18 Nov 2026 (place version 1034, published about 22:36 UTC). The two lines in
`roblox/src/shared/Config.luau`:

| Switch | Now (version 1034) | Off again |
|---|---|---|
| `Config.LOOT_FREE` | `false`: things cost Robux (or coins / tickets for a redeem) | `true`: everything free to claim |
| `Config.LOOT_ROBUX` | `true` (**the** switch, `Shop.ROBUX`): prompts and receipts on | `false`: no prompt, no `ProcessReceipt` |
| `Unlocks.WEAPONS_ROBUX_FREE` (`shared/Unlocks.luau`) | `true`: the four Robux weapons are free for everyone (FREE FOR NOW), the owner's call | `false`: they must be bought |

- While `LOOT_FREE` is on, `Shop.free()` wins: nothing prompts even with `LOOT_ROBUX` on. The coin packs then read NOT
  FOR SALE YET, with their prices struck through.
- `WEAPONS_ROBUX_FREE` only locks the weapons. With it off and `LOOT_ROBUX` still off, they can be bought with coins
  but not with Robux.

## Going live (LIVE since 18 Nov 2026, about 22:36 UTC, place version 1034)

The owner: "Lets get the shop going!". It is one change, in one Studio turn under main's OWNER HOLD:

1. `Config.luau`: `LOOT_FREE = false`, `LOOT_ROBUX = true` (two lines; the shop session's prepared swap checks the
   base and compile, then saves).
2. Put the VIP pass on sale: `PATCH /game-passes/v1/universes/10776367667/game-passes/2093409349` with `isForSale`
   true (scope `game-pass:write`). `Shop.VIP_PASS` is already 2093409349.
3. The owner publishes.

**The log (18 Nov 2026, UTC):**
- 22:3x: `LOOT_FREE = false`, `LOOT_ROBUX = true` in Studio (the shop session, in its turn under main's OWNER HOLD);
  saved as place version 1034.
- about 22:36: the owner published version 1034. Real money is live.
- 22:53: main put the VIP pass on sale (PATCH `isForSale` true, 399). A GET at 22:53:11 confirms it.

The live data stores (`JankfirePurchases_v1` and the rest) can't be read from here: Open Cloud's data-store scope
isn't granted to the assistant. Watch the first real purchases in the live server's output (`[jankfire] purchases:` /
`quests: ... bought` lines) or with a Studio read of the live store. Sanity Play before the save:
- the 1,200-coin pack and the Crate showed Roblox's real purchase prompts (cancelled: `PromptProductPurchaseFinished`
  with false for 3733204424 and 3733200177);
- the VIP tile's buy prompted the pass;
- the items claimed while free were all still owned.

`Unlocks.WEAPONS_ROBUX_FREE` was not part of it. The owner decided on 19 Nov ("lock them"), so it's `false` since then:
- **Locked:** the Minigun, Lefty & Righty, Big Laser Pointer and Chicken Rocket need buying, with Robux or coins
  (Shop.MONEY.weapons), or come from their weapon bundle or a gift (the dev menu's GIFT, or a paid gift).
- **Nothing is erased.** A player whose saved pick is one they don't own carries the slot's default (Loadout's carry
  check, `carried`), and the pick stays saved, so it comes back the moment they own it.
- **WeaponsKept** (the 18 Nov grandfathering) never held a Robux weapon, because Unlocks.level of one is 1, so no one
  keeps a free copy.

Also for the owner, on the Creator Hub:
- Answer the experience questionnaire: the game has paid random items (the containers). See LOOT.md, "Roblox's rules
  for paid random items". The odds and PolicyService parts are already built.

**Players keep everything they claimed while the shop was free.** Nothing was taken back at go-live:
- items claimed (wraps, hats, skins, card looks, kill effects, emotes) stay in the loot save;
- containers in stock stay, and still open;
- a deal had stays had;
- **a free VIP claim stays VIP for good** (`Vip.luau`: a claim made while the shop was free keeps counting; only the
  claim itself needed the shop free; since 18 Nov);
- if the Robux weapons are ever locked, `WeaponsKept` keeps the ones a player already used (PROGRESSION.md).

Only new claims stop: CLAIM buttons become BUY, and containers need stock or a purchase to open.

## Every price (one table: `Shop.MONEY` in `shared/Shop.luau`)

Change a Robux price in **both** places: `Shop.MONEY`, and the product on the Creator Hub (Monetization > Developer
Products). Roblox charges the product's price. With Robux on, the shop shows the products' own prices
(`ShopUI.livePrices`), so a mismatch shows the right number but the catalog is wrong. Coin prices are only in the
table.

| What | Robux | Coins |
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
| **1,200 Coins** | **99** | |
| **6,500 Coins** (6,000 + 500 bonus) | **499** | |
| **28,000 Coins** (24,000 + 4,000 bonus) | **1,999** | |
| **70,000 Coins** (54,000 + 16,000 bonus) | **4,500** | |

Why these numbers:
- **Coin packs.** The base rate is 12 coins a Robux. The bigger packs add a bonus of 8%, 17% and 30%.
  - Even the best rate (about 15.6 a Robux) keeps coin-bought things dearer than their own Robux price: a Spray Can's
    1,000 coins is about 64 Robux against its 60, and a 4,000-coin weapon about 257 against 199.
  - So the packs never undercut the shop.
- **Weapons for coins.** An active player earns roughly 1,000-1,500 coins a week from quests and the weekly track, so a
  weapon is 3-5 weeks of play.
- **No pay-to-win beyond what was already planned.** The four weapons were already the Robux exclusives
  (PROGRESSION.md). They now also come from play, with coins.

## The VIP game pass

| Pass | Id | Price | State |
|---|---|---|---|
| VIP | **2093409349** | 399 | off sale; icon: the gold Royal Duck (asset 113037419360696); made by the main session |

`Shop.VIP_PASS = 2093409349`. `Vip.luau` checks `UserOwnsGamePassAsync` on join. While the shop is free, anyone can
still claim VIP from the shop (unchanged). With Robux on, GET VIP shows the pass prompt.

## Developer products

88 made on 18 Nov with Open Cloud (`POST /developer-products/v2/universes/10776367667/developer-products`, scope
`developer-product:write`, multipart with an icon). Each is on sale with its store page off, so it can only be bought
from an in-game prompt; the game prompts nothing while `LOOT_ROBUX` is off. Their ids are in `Shop.PRODUCTS`; the full
list is under "Every product".

The icons, all in `roblox/docs/money/icons/` (the owner-approved upload folder):
- coin packs: guns-remodel's pack renders (`pack_99.png` ... `pack_4500.png`);
- the four weapons: crops of the web game's model render sheets (`roblox/tools/icon_crop.ps1`);
- skins, hats and wraps: one crop each, shared by those products: the Golden Sniper for skins, the Top Hat for hats,
  bags and card looks, the plain rifle for wraps and bundles.

None has text or codes.

Images for the GUI (uploaded as Image assets): the coin 140006087004657, the ticket 93857045911579, and the packs
76861915103827, 88259913823049, 93667428578542 and 125116964696727.

## How a purchase works

- **The client asks.** It fires `JankfireRemotes.ShopBuy` with an offer id:
  - a container, bundle, set or single (`Shop.offer`);
  - `deal:<skin>`;
  - `weapon:<id>` (`Shop.weaponOffer`);
  - `coins:<pack>` (`Shop.coinPack`).
- **The server prompts** (`ShopReceipts.server.luau`). It checks the offer and the product, remembers what was asked
  (singles and deals share a product per tier), and shows Roblox's prompt. It won't prompt for a weapon the player
  already owns.
- **Roblox calls `ProcessReceipt`.** ShopReceipts:
  1. answers `PurchaseGranted` for a receipt it already granted (`Purchases.seen`: the receipt record);
  2. grants the purchase:
     - loot: `Loot.grant(p, offer, purchaseId)`;
     - a deal: `Deals.grant`;
     - a weapon: `Purchases.giveWeapon(p, wid, "robux", purchaseId)`;
     - coins: `Quests.buyBrass(p, amount, purchaseId)`;
  3. marks the receipt (`Purchases.mark`), then answers `PurchaseGranted`.

  Every grant is written to its save before it answers true, and each is idempotent by the purchase id. So a receipt
  sent twice is granted once even if the record write was lost. Anything that fails answers `NotProcessedYet`, and
  Roblox tries again on the player's next join.
- **The receipt record** is in `Purchases.luau`'s save:
  - store `JankfirePurchases_v1`, and `JankfirePurchases_v1_studio` in Studio (`Profiles.new` adds it), never the live
    one;
  - session-locked per player;
  - the newest 500 receipts.
- **Bought coins** (`Quests.buyBrass`):
  - no daily cap;
  - they never count as earned, so a cheat restore leaves them;
  - idempotent per receipt in their own list (`bought`).

## Paid random items (Roblox's policy, checked 18 Nov before go-live)

Roblox's rules (create.roblox.com/docs/production/monetization/paid-random-items) cover random items bought with
Robux, **or with a currency that can be bought with Robux**. Coins can be bought, so a container redeemed with coins
counts. Tickets are only ever earned (the weekly track), and nothing sells them for Robux or coins, so ticket redeems
don't.

**Where the policy restricts a player** (PolicyService `ArePaidRandomItemsRestricted`; `Loot.restricted(p)`, true
until Roblox answers):
- **Robux:**
  - the shop's BUY on a container reads NOT AVAILABLE HERE;
  - ShopReceipts never prompts a container for them;
  - a container receipt that arrives anyway is never granted (it waits, and Roblox returns the Robux).
- **Coins:** the REDEEM option for coins reads COINS · NOT AVAILABLE HERE. The server refuses it too, before anything is
  spent (`Quests` "redeem": "not available where you are").
- **Tickets:** still redeem, and the containers they open still show their odds.
- **Everything else** isn't random and stays on sale: coin packs, bundles, sets, singles, deals, weapons, VIP.

**The odds**, before anything is bought by any route:
- The container cards have an **ODDS** button (a word, not an icon).
- The ODDS panel lists the rarities with their chances and a TOTAL row of 100%.
- Below them, **EVERY ITEM**: every final outcome with its own chance, one line per rarity and gun ("LEGENDARY ·
  ASSAULT RIFLE · each item below: 0.0046136%", then the items). The roll picks a rarity, then a gun evenly, then an
  item for it, so the items in one line share a chance (`LootTable.oddsDetail`).
- Chances are rounded four places past their first digit, with Roblox's disclaimer ("Probabilities are rounded; the
  total of the displayed individual probabilities may not equal 100%").
- The confirm panel (every buy and redeem of a container) shows the rarity odds again.
- What you own is never rolled, so every number follows your collection.
- Checked: the per-item chances add up to exactly 100% for all three containers: the Crate 44 outcomes, the Duffel Bag
  378, the Spray Can 5,049.

**Studio test:** the loot remote's `("dev", "restricted", true | false)` (Studio and the owner only, this session only).

Tested 18 Nov, place version 1033 (`MoneyTest` on):
- **Restricted:**
  - Robux receipts for a Crate, a Duffel Bag and a Spray Can: NotProcessedYet, stock unchanged;
  - coin redeems of a bag and a can: refused, coins unchanged (9,000);
  - a ticket redeem of a can: done (30 to 27 tickets);
  - a coin-pack receipt and the Head Office bundle: granted.
- **Not restricted:** a coin redeem of a bag (10,200 to 7,700) and a Crate receipt: both done.
- **Photos:** `money/odds-every-item.jpg`, `money/confirm-restricted.jpg`.
- **Put back:** the containers opened, the loot save set back to its 17 / 17 / 8, the coins save back to its snapshot.
  A fresh Play read it all back as it was.

## The shop's WEAPONS and COINS tabs

- **WEAPONS:** the four Robux weapons. Each has a Robux button (the prompt) and a coins button.
  - The coins button asks for a second press ("SURE? 4,000") before it spends.
  - Not enough coins opens the COINS tab.
  - While `WEAPONS_ROBUX_FREE` is on, the cards say FREE FOR NOW and sell nothing.
- **COINS:** the balance with the coin at the top right, and the four packs as tiles. Each tile has its picture, the
  amount, a small "+N" chip for the bonus, and the Robux price on its button.
  - The HUD's wallet (top right) opens this tab.
  - So does "not enough coins" in the shop or in the loadout.
- **The loadout:** for a locked Robux weapon, the EQUIP button splits into Robux and coins.

## The Robux weapons, kept

- **Which:** `Unlocks.ROBUX`: `minigun`, `laser`, `chicken`, `akimbo`. Prices are in `Shop.MONEY.weapons`.
- **Kept by `Purchases.luau`.** It sets the player attribute `RobuxOwned` (`"laser,minigun"`), which
  `Unlocks.forPlayer` reads on both sides. The loadout server refuses a pick of one you don't own once they aren't
  free.
- **A coins buy runs on the server** (`JankfireRemotes.Purchases` `"brass"`, wid). It checks the price and the coins,
  then writes three things in order:
  1. a pending mark (Purchases);
  2. the coins, taken by `Quests.spendBrass` in the quests' save (idempotent by the id `weapon:<wid>`);
  3. the weapon (Purchases).

  A crash between them is settled on the next join: `Quests.spent` tells whether the coins went.

## Gifts from the owner (the dev menu's GIFT tab)

| Gift | Call |
|---|---|
| Coins (and tickets) | `Quests.gift(player, coins, tickets, id)`: uncapped, idempotent by id, not counted as earned |
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
- **The coins:** `ServerStorage.JankQuestTest` `("data", player)` and `("put", player, data)` for a snapshot and its
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

## Tested (18 Nov, solo Play on the owner's _studio saves, place version 1029)

With `MoneyTest` on inside the Play server:
- **COINS tab:** the balance with the coin (9,000 test coins, later 71,200), four pack tiles with their pictures,
  +500 / +4,000 / +16,000 chips and the Robux prices (`money/shop-coins-tab.jpg`).
- **Weapons for coins:** the Big Laser Pointer (4,000) and then the Minigun (5,000) from 9,000 coins left 0; a second
  buy said "you have it already". The armory read Chicken Rocket LIVE · yours and Minigun ROBUX.
- **WEAPONS tab:** OWNED on the bought ones, Robux and coins buttons on the others (`money/shop-weapons-tab.jpg`).
- **Simulated receipts** (`JankMoneyTest`):
  - 1,200 coins: granted, +1,200; the same receipt again: granted, nothing more paid;
  - 70,000 coins: +70,000;
  - the Chicken Rocket for Robux: granted, RobuxOwned gained chicken;
  - the Field Issue bundle: granted (its wraps on every gun);
  - a Seraph set completion after its ask: granted, the five Seraph skins;
  - a completion with no ask: NotProcessedYet;
  - an unknown product: NotProcessedYet.
- **Prompts:**
  - `ShopBuy "coins:coins_1200"` and a direct `PromptProductPurchase` ran without error, and `GetProductInfo` read
    "1,200 Coins", 99, for sale;
  - the VIP "buy" answered `prompted = true` (pass 2093409349);
  - Studio's purchase dialog itself (CoreGui) doesn't show in screen captures, so the dialog wasn't seen.
- **VIP gift:** `Vip.gift` wrote `{ gift = true }` on the VIP key, and `false` took it back. The key was then
  restored exactly (it hadn't existed).
- **Default first:** the AR's skins strip reads Default, then the newest owned (`money/loadout-default-first.jpg`).

**Put back afterwards:**
- the loot save to its 17 wraps, 17 hats and 8 skins;
- the coins save to its snapshot (0 coins, no bought or spent entries);
- the bought weapons taken back;
- `UnlockAll` on again.

The test receipts (5 ids) stay in the new `_studio` purchases record; they are only test marks.

**Not tested:** a real purchase completed through Studio's dialog (by a click), a crash between the three writes of a
coins buy, and two servers.

## Every product

| Key | Name | Robux | Product id |
|---|---|---|---|
| `crate` | Crate | 120 | 3733200177 |
| `bag` | Duffel Bag | 90 | 3733200704 |
| `spray` | Spray Can | 60 | 3733200725 |
| `crate:5` / `crate:10` | 5 / 10 Crates | 600 / 1,200 | 3733759267 / 3733759286 |
| `bag:5` / `bag:10` | 5 / 10 Duffel Bags | 450 / 900 | 3733759307 / 3733759328 |
| `spray:5` / `spray:10` | 5 / 10 Spray Cans | 300 / 600 | 3733759347 / 3733759369 |
| `bundle_nightshift` | Night Shift | 1,099 | 3733200745 |
| `bundle_fieldissue` | Field Issue | 289 | 3733200855 |
| `bundle_teahouse` | Tea House | 869 | 3733200884 |
| `bundle_deepspace` | Deep Space | 1,499 | 3733200908 |
| `bundle_machineshop` | Machine Shop | 619 | 3733201016 |
| `bundle_quarry` | Quarry | 1,219 | 3733201039 |
| `bundle_cards` | Head Office | 169 | 3733201064 |
| `set_seraph` | Seraph Set | 3,300 | 3733201174 |
| `set_seraph:1` | Seraph Set, last 1 | 660 | 3733201190 |
| `set_seraph:2` | Seraph Set, last 2 | 1,320 | 3733201209 |
| `set_seraph:3` | Seraph Set, last 3 | 1,980 | 3733201426 |
| `set_seraph:4` | Seraph Set, last 4 | 2,640 | 3733201313 |
| `set_infernal` | Infernal Set | 3,300 | 3733201329 |
| `set_infernal:1` | Infernal Set, last 1 | 660 | 3733201448 |
| `set_infernal:2` | Infernal Set, last 2 | 1,320 | 3733201459 |
| `set_infernal:3` | Infernal Set, last 3 | 1,980 | 3733201580 |
| `set_infernal:4` | Infernal Set, last 4 | 2,640 | 3733201598 |
| `set_halloween` | Witching Hour Set | 3,300 | 3733201617 |
| `set_halloween:1` | Witching Hour Set, last 1 | 660 | 3733201706 |
| `set_halloween:2` | Witching Hour Set, last 2 | 1,320 | 3733201726 |
| `set_halloween:3` | Witching Hour Set, last 3 | 1,980 | 3733201741 |
| `set_halloween:4` | Witching Hour Set, last 4 | 2,640 | 3733201837 |
| `set_tidecrest` | Tidecrest Set | 3,000 | 3733201862 |
| `set_tidecrest:1` | Tidecrest Set, last 1 | 600 | 3733201889 |
| `set_tidecrest:2` | Tidecrest Set, last 2 | 1,200 | 3733201991 |
| `set_tidecrest:3` | Tidecrest Set, last 3 | 1,800 | 3733202011 |
| `set_tidecrest:4` | Tidecrest Set, last 4 | 2,400 | 3733202029 |
| `set_dust` | Dust Drover Set | 3,900 | 3733202122 |
| `set_dust:1` | Dust Drover Set, last 1 | 780 | 3733202140 |
| `set_dust:2` | Dust Drover Set, last 2 | 1,560 | 3733202160 |
| `set_dust:3` | Dust Drover Set, last 3 | 2,340 | 3733202240 |
| `set_dust:4` | Dust Drover Set, last 4 | 3,120 | 3733202257 |
| `set_star` | Star Drover Set | 3,900 | 3733202273 |
| `set_star:1` | Star Drover Set, last 1 | 780 | 3733202349 |
| `set_star:2` | Star Drover Set, last 2 | 1,560 | 3733202363 |
| `set_star:3` | Star Drover Set, last 3 | 2,340 | 3733202382 |
| `set_star:4` | Star Drover Set, last 4 | 3,120 | 3733202477 |
| `banner:common` | Common Card Background | 50 | 3733202493 |
| `banner:rare` | Rare Card Background | 100 | 3733202511 |
| `banner:epic` | Epic Card Background | 200 | 3733202602 |
| `banner:legendary` | Legendary Card Background | 400 | 3733202625 |
| `border:common` | Common Card Border | 50 | 3733202645 |
| `border:rare` | Rare Card Border | 100 | 3733202732 |
| `border:epic` | Epic Card Border | 200 | 3733202751 |
| `border:legendary` | Legendary Card Border | 400 | 3733202769 |
| `emote:common` | Common Emote | 100 | 3733202887 |
| `emote:rare` | Rare Emote | 200 | 3733202906 |
| `emote:epic` | Epic Emote | 400 | 3733202924 |
| `emote:legendary` | Legendary Emote | 800 | 3733203016 |
| `hat:common` | Common Hat | 100 | 3733203035 |
| `hat:rare` | Rare Hat | 200 | 3733203049 |
| `hat:epic` | Epic Hat | 400 | 3733203160 |
| `hat:legendary` | Legendary Hat | 750 | 3733203176 |
| `kill:common` | Common Kill Effect | 100 | 3733203199 |
| `kill:rare` | Rare Kill Effect | 200 | 3733203280 |
| `kill:epic` | Epic Kill Effect | 400 | 3733203293 |
| `kill:legendary` | Legendary Kill Effect | 800 | 3733203306 |
| `skin:common` | Common Weapon Skin | 150 | 3733203365 |
| `skin:rare` | Rare Weapon Skin | 300 | 3733203381 |
| `skin:epic` | Epic Weapon Skin | 600 | 3733203397 |
| `skin:legendary` | Legendary Weapon Skin | 1,200 | 3733203496 |
| `title:common` | Common Card Title | 40 | 3733203514 |
| `title:rare` | Rare Card Title | 80 | 3733203535 |
| `title:epic` | Epic Card Title | 160 | 3733203612 |
| `title:legendary` | Legendary Card Title | 320 | 3733203626 |
| `wrap:common` | Common Wrap | 75 | 3733203644 |
| `wrap:rare` | Rare Wrap | 150 | 3733203745 |
| `wrap:epic` | Epic Wrap | 300 | 3733203760 |
| `wrap:legendary` | Legendary Wrap | 600 | 3733203775 |
| `deal:common:20` | Deal: Common Skin, 20% Off | 119 | 3733203865 |
| `deal:common:25` | Deal: Common Skin, 25% Off | 109 | 3733203886 |
| `deal:rare:25` | Deal: Rare Skin, 25% Off | 229 | 3733203909 |
| `deal:rare:30` | Deal: Rare Skin, 30% Off | 209 | 3733204023 |
| `deal:epic:30` | Deal: Epic Skin, 30% Off | 419 | 3733204043 |
| `deal:epic:35` | Deal: Epic Skin, 35% Off | 389 | 3733204068 |
| `deal:legendary:35` | Deal: Legendary Skin, 35% Off | 779 | 3733204169 |
| `deal:legendary:40` | Deal: Legendary Skin, 40% Off | 719 | 3733204190 |
| `weapon:minigun` | Minigun | 249 | 3733204206 |
| `weapon:laser` | Big Laser Pointer | 199 | 3733204303 |
| `weapon:chicken` | Chicken Rocket | 199 | 3733204322 |
| `weapon:akimbo` | Lefty & Righty | 249 | 3733204340 |
| `coins:coins_1200` | 1,200 Coins | 99 | 3733204424 |
| `coins:coins_6500` | 6,500 Coins | 499 | 3733204431 |
| `coins:coins_28000` | 28,000 Coins | 1,999 | 3733204444 |
| `coins:coins_70000` | 70,000 Coins | 4,500 | 3733204487 |
