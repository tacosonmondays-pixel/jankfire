# Progression: weapons by level, and the Robux weapons

The owner, 18 Nov 2026: "weapons are unlocked via level progression, some weapons are Robux exclusive but free for now
for everyone".

## The level

The level is the one the game already keeps: `Stats` holds your XP, `Ranks.levelOf(xp)` turns it into a level, and the
player attribute `Level` carries it. The player card shows it.

- **XP:** +20 for a kill on a player, +50 for a round won, and 2 a minute of match time (`Ranks.XP`, the web game's
  numbers). The hub and the training hall give nothing.
- **The curve:** level n needs (n - 1)² × 40 XP. A one-against-one match to five is about 250 XP on average (the winner
  nearer 360), so level 5 takes about 3 matches, level 10 about 13, and level 20 about 58.
- **On the HUD:** `UnlockClient.client.luau` shows LV n and a thin bar to the next level, top left, hidden under menus.
- **Level up:** a quiet plate at the top in the middle for 5 s, LEVEL n and the weapons that opened on the way, with
  the recorded reward sting (`loot_win_rare`). The first level read once your stats load isn't counted as a level-up.
- Quests give Brass and Crate Tickets, not XP. Giving them XP would be a change in Quests (another session's file).

## The level table

`shared/Unlocks.luau`, `Unlocks.LEVEL`. A weapon not listed opens at level 1.

| Level | XP | Opens |
|---|---|---|
| 1 | 0 | Assault Rifle, SMG, Shotgun, Pistol, Katana, Frag Grenade (the starter kit) |
| 2 | 40 | Revolver, Smoke Bomb |
| 3 | 160 | Burst Rifle, Knife, Medkit |
| 4 | 360 | Sniper, Party Popper |
| 5 | 640 | Sawed-Off, Shield Bubble |
| 6 | 1,000 | LMG, Rubber Duck, Snowball |
| 7 | 1,440 | Marksman Rifle, Hand Slapper |
| 8 | 1,960 | Lever Rifle, Bubble Wand |
| 9 | 2,560 | Marble Shotgun, Instant Camera, Slipper |
| 10 | 3,240 | Redline, Reverse Card |
| 11 | 4,000 | Card Deck |
| 12 | 4,840 | Auto Shotgun, Pop Quiz, Bow |
| 13 | 5,760 | Tennis Ball Launcher |
| 14 | 6,760 | Bread, Night Vision Goggles, Scythe (melee; the owner asked for it on 18 Nov) |
| 15 | 7,840 | Peel Shooter, Taser |
| 16 | 9,000 | Water Pistol, Speed Trap |
| 17 | 10,240 | Hot Sauce |
| 18 | 11,560 | Nail Gun, Laptop |
| 19 | 12,960 | Leaf Blower |
| 20 | 14,440 | Shredder, Lasso |
| 21 | 16,000 | Blood Cross |
| 22 | 17,640 | Bowling Ball Launcher |
| 23 | 19,360 | TV Remote |
| 24 | 21,160 | Scales of Justice |
| 25 | 23,040 | Shopping Cart Cannon |

Level 25 takes about 92 matches. The weapons batches C (place version 835) and D (870) brought the Snowball, Slipper,
Bow, Tennis Ball Launcher, Peel Shooter, Taser, Hot Sauce, Leaf Blower, Blood Cross, Bowling Ball Launcher, TV Remote and
Scales of Justice live at the levels they'd been given. Batch E (891) brought the last three: the Card Deck, the Lasso
and the Shopping Cart Cannon. Every ported weapon is now on Roblox. A weapon that isn't live shows in no lock and no
level-up list (`Unlocks.at` takes the live ones).

The new loadout default is the level-1 kit: Assault Rifle, Pistol, Katana, Frag Grenade. Until 18 Nov it was the
Redline and the Marble Shotgun.

## The Robux weapons

`Unlocks.ROBUX`: **Minigun**, **Big Laser Pointer**, **Chicken Rocket**, **Lefty & Righty**. These are the flashiest
signature weapons. All four are on Roblox: Lefty & Righty went live with batch E (place version 891).

All four stay Robux exclusives (18 Nov, shop-gui's call when weapons batches C and D went live). They don't get a
level as well.

- **`Unlocks.WEAPONS_ROBUX_FREE = true`** (the owner's switch, like `Config.LOOT_FREE`). While it's on, everyone has
  them at any level. The loadout marks them ROBUX · FREE FOR NOW, and the match picker ROBUX · FREE. Code asks
  `Unlocks.robuxFree()`, which a Studio play test of the paid shop can turn off (MONEY.md, "Testing in Studio").
- **Switched off,** each must be bought, once, for good (18 Nov: game passes are not used; `pass` stays 0):
  - with Robux: a developer product, `weapon:<id>`;
  - or with coins (Brass in the code), which the server takes.

  Prices are in `Shop.MONEY.weapons`: Minigun and Lefty & Righty 249 Robux or 5,000 coins; Big Laser Pointer and
  Chicken Rocket 199 or 4,000 coins. The server keeps what you bought (`Purchases.luau`) and sets `RobuxOwned`, which
  `Unlocks.forPlayer` reads.
- **Where to buy:** the shop's WEAPONS tab, or the loadout, whose EQUIP button splits into Robux and coins for a
  locked one; not enough coins opens the COINS tab. Everything about money is in MONEY.md.

## Ranked

Any weapon you've unlocked is allowed in ranked, and the Robux weapons are allowed while they're free. **For the
owner:** before switching `WEAPONS_ROBUX_FREE` off, decide whether paid weapons should be allowed in ranked. A paid
weapon in a rated match is a fairness question; one option is to keep ranked to the level weapons.

## How it's enforced

- **The server refuses a pick** (`Loadout.luau`, op "pick") that `Unlocks.forPlayer` doesn't allow, with "level 7
  unlocks it" or "a robux weapon". It reads the player's attributes, all of them set by the server. Trying anything in
  the training hall stays free.
- **The loadout screen:** an armory card for a weapon you don't have yet is greyed, with LEVEL n on it, and its EQUIP
  reads LEVEL n UNLOCKS IT. The match loadout's picker greys it the same way with LEVEL n, and says why if you click it.
- **Nobody loses anything.** `WeaponsKept` (worked out once per player in `Loadout.luau`, saved with the loadout)
  keeps, at any level, every weapon that player had picked, plus every weapon their stats show they've used
  (`Stats.usedWeapons`: any time held, shot or kill). That covers the owner's friends who tested.
- **Dev unlock-all:** `UnlockAll` is on for the owner (`game.CreatorId`) and for every Studio test, so nobody's tests
  hit a lock. To see the locks in Studio, call the Loadout remote with `("unlockall", false)`.

## Tested
In solo Play at place version 801. The Studio profile's dev unlock was switched off and its keep list cleared, with the
server's Level set to 1, so it showed what a fresh level-1 player sees:

- **Grandfathering:** before clearing, the profile's keep list had come out as duck, redline, revolver and sniper (its
  picks and the weapons its stats showed). It was at level 1.
- **Server refusals:** "pick primary lmg" was refused with "level 6 unlocks it". The Minigun (Robux, free for now) and
  the Shotgun (level 1) were allowed.
- **Loadout at level 1** (`docs/progression/loadout-locks.jpg`): Redline LEVEL 10, Shredder LEVEL 20, Sniper LEVEL 4,
  greyed. The focused Sniper's EQUIP read LEVEL 4 UNLOCKS IT. The Minigun was ROBUX · FREE FOR NOW
  (`loadout-robux-free.jpg`).
- **Level up:** Level 1 to 7 showed LEVEL 7 and the 14 weapons that opened on the way, with the sting
  (`level-up-toast-before-wrap.jpg`). That list ran past the plate's edges, so the plate now wraps it over lines, at
  most 560 wide: seen in a later run, two lines inside the plate, the chip at LV 7 (`level-up-toast.jpg`).
- **Dev unlock:** at level 7 the Shredder was refused ("level 20 unlocks it"). With `("unlockall", true)` it was
  allowed. The profile's own picks were put back afterwards.

- **The match picker at level 7** (`match-picker-locks.jpg`): Redline LEVEL 10, Shredder LEVEL 20, Lever Rifle LEVEL
  8, Auto Shotgun LEVEL 12, Nail Gun LEVEL 18, all greyed. The Minigun and the Big Laser Pointer (live since weapons
  batch B) read ROBUX · FREE.

- **Batches C and D** (Edit, place version 871): `Unlocks.at` lists each newly live weapon at its level (Snowball at 6,
  Slipper at 9, Bow at 12, Tennis Ball Launcher at 13, Scythe at 14, Peel Shooter and Taser at 15, Hot Sauce at 17, Leaf
  Blower at 19, then Blood Cross, Bowling Ball Launcher, TV Remote and Scales of Justice at 21 to 24), and nothing at
  11 or 25. The Chicken Rocket and Lefty & Righty pass the check at level 1.

- **Batch E** (Edit, place version 892): the Card Deck lists at 11, the Lasso at 20 beside the Shredder, the Shopping
  Cart Cannon at 25. Lefty & Righty is a Robux weapon and passes the check at level 1. No roster weapon is left not
  live.

Not tested: a real XP gain to the next level (the level was set by hand), the phone, a player with no save at all, and the LV chip at a level the XP agrees with.
