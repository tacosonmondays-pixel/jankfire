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
  hold weapon skins (none on Roblox yet, so the Crate reads COMING SOON), Duffel Bags hats, Spray Cans wraps. Names
  and prices are the shop's; the pools and odds are the loot module's, read through `Shop.odds(id, owned)`
  (`LootTable.odds`, the function the server rolls by), so the screen never shows numbers the server doesn't use.
  The odds depend on what you own; when you own everything in one it reads YOU HAVE IT ALL.
- **bundles** `bundle_<name>`: a fixed themed set of wraps and a hat that dresses several guns, plus a `hero` (the
  weapon, wrap and hat the big preview and the hub's hologram show). Six to start: Night Shift, Field Issue, Tea House,
  Deep Space, Machine Shop, Quarry. A bundle's price is about 60% of its items one by one (`Shop.worth`).
- **singles** `wrap:<id>@<weapon>`, `hat:<id>@<weapon>`: one item for one weapon, on sale only while it is in
  today's rotation (`Shop.onSale`).

**Wraps and hats are owned per weapon** (the owner, 16 Nov: a spray can gives a wrap "for only one gun at a time").
Every item is `{ kind, id, weapon }`; where one string is needed it is `"<id>@<weapon>"` (`Shop.key` / `Shop.unkey`,
e.g. `"sakura@smg"`), and it reads "Sakura Storm · SMG" (`Shop.itemLabel`). The weapons are the live primaries,
secondaries and the katana (`Shop.WEAPONS`); a hat only for a weapon with a hat spot. An owned plain `"sakura"` (an
older save) counts for every weapon.

Wraps whose picture versions broke Roblox's image rules (QR Code, Barcode, Meat Suit, Organ Donor, CORP, Corporate
Memo, Jersey) never appear in a bundle or the rotation (`Shop.HELD_BACK`).

**The featured rotation** (`Shop.rotation(day)`): one hero bundle and six singles (four wraps, two hats, at least one
epic or better) a day, seeded by the UTC day number, so every server and every client agrees without storing
anything. It turns over at 00:00 UTC; a single from yesterday stays buyable for 5 minutes after the turn.

**Prices** (`Shop.PRICE`, Robux, unused while free): wraps 75 / 150 / 300 / 600, hats 100 / 200 / 400 / 750 by
rarity; containers 120 / 90 / 60; bundles from their worth.

Useful calls: `Shop.offer(id)`, `Shop.contents(offer)`, `Shop.free()`, `Shop.rotation()`, `Shop.secondsLeft()`,
`Shop.onSale(id)`, `Shop.odds(containerId, owned)`, `Shop.productFor(offer)`, `Shop.itemInfo(kind, id)`,
`Shop.itemLabel(item)`, `Shop.key(kind, id, weapon)`, `Shop.unkey(s)`, `Shop.weaponName(wid)`, `Shop.WEAPONS`.

## The screen

- **Open it:** the B key; the SHOP button over the LOADOUT button (bottom left, hub only); a hub hologram; or from
  any client script: `require(PlayerScripts.Jankfire.ShopUI).open(tab, offerId)`. A ProximityPrompt with the
  attribute `ShopOpen = "bundle_nightshift"` (or `"tab:containers"`) opens it on that offer when triggered.
  Not in a match, not over the loadout.
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
`"close"`, `"fake:844x390"` (lays the shop out in a phone-sized box with an amber edge), `"real"`.

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
