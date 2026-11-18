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
| 6 | 1,000 | LMG, Rubber Duck |
| 7 | 1,440 | Marksman Rifle, Hand Slapper |
| 8 | 1,960 | Lever Rifle, Bubble Wand |
| 9 | 2,560 | Marble Shotgun, Instant Camera |
| 10 | 3,240 | Redline, Reverse Card |
| 12 | 4,840 | Auto Shotgun, Pop Quiz |
| 14 | 6,760 | Bread, Night Vision Goggles |
| 16 | 9,000 | Water Pistol, Speed Trap |
| 18 | 11,560 | Nail Gun, Laptop |
| 20 | 14,440 | Shredder |

Not on Roblox yet, with levels ready for when they go live: Snowball 6, Slipper 9, Card Deck 11, Bow 12, Tennis Ball
Launcher 13, Peel Shooter 15, Taser 15, Hot Sauce 17, Leaf Blower 19, Lasso 20, Blood Cross 21, Bowling Ball Launcher
22, TV Remote 23, Scales of Justice 24, Shopping Cart Cannon 25.

The new loadout default is the level-1 kit: Assault Rifle, Pistol, Katana, Frag Grenade. Until 18 Nov it was the
Redline and the Marble Shotgun.

## The Robux weapons

`Unlocks.ROBUX`: **Minigun**, **Big Laser Pointer**, **Chicken Rocket**, **Lefty & Righty**. These are the flashiest
signature weapons. Only the Minigun is on Roblox now; the other three have their mark ready.

- **`Unlocks.WEAPONS_ROBUX_FREE = true`** (the owner's switch, like `Config.LOOT_FREE`). While it's on, everyone has
  them at any level. The loadout marks them ROBUX · FREE FOR NOW, and the match picker ROBUX · FREE.
- **Switched off,** each needs its game pass. `Unlocks.ROBUX[id].pass` is 0, a placeholder: the owner makes the passes
  and puts their ids there. Nothing here creates a product or sets a price. The server-side check for owning a pass
  (a `RobuxOwned` attribute the server sets from `MarketplaceService:UserOwnsGamePassAsync`) still has to be written
  when the passes exist. `Unlocks.forPlayer` already reads that attribute.
- **The shop** doesn't list weapons. It would need a WEAPONS shelf with the passes once they exist; that's left for
  then.

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
  most 560 wide. The wrap is in version 801 but hasn't been seen on screen yet.
- **Dev unlock:** at level 7 the Shredder was refused ("level 20 unlocks it"). With `("unlockall", true)` it was
  allowed. The profile's own picks were put back afterwards.

Not tested: a real XP gain to the next level (the level was set by hand), the match picker's LEVEL marks on screen,
the phone, a player with no save at all, and the LV chip at a level the XP agrees with.
