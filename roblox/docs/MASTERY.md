# Weapon mastery

The owner, 18 Nov 2026: "you'll be able to level up weapons to unlock gold, damascus, diamond and galaxy camo for
their respective guns".

Every live weapon (guns, melee and gadgets) has its own level, 1 to 40, from XP earned with that weapon in real
matches. On the way up it unlocks four camos for that gun alone. They are never sold, never in a container, never in a
bundle or the VIP pack, never discounted and never gifted.

## The XP

| What | XP | To which weapon |
|---|---|---|
| A kill | 100 | the weapon that made it (a parry kill is the Katana's, the Scythe's rifle form is the Scythe) |
| The kill's last hit was a headshot | +25 | the same |
| An assist | 50 | you hurt the victim in the 10 s before someone on your side killed them: the weapon you hurt them most with |
| A round won | 50 | the weapon you held longest in that round |
| The match won | 50 | the weapon you held longest in the match |

Only real matches count, decided on the server by the same checks as the player card's numbers (`Stats.luau`):

- never the hub, the training hall, its dummies or the playground (a kill there isn't on an enemy in your match);
- never a ghost match (a Studio stand-in match) or a dev match (the owner's dev menu flags it: `m.dev`);
- never a cheater that has been restored (their XP goes with the rest of their numbers, and comes back on an undo).

The tbag blast and a fall after your grapple are kills on the card but have no weapon, so they give no weapon XP.

## The curve

Level n to n + 1 takes 300 + 60 × (n − 1) XP (`Mastery.STEP`, `Mastery.GROW`). XP stops at level 40.

| Level | Total XP | Camo | About (an even 1v1 to five gives the gun you use ~550 XP) |
|---|---|---|---|
| 10 | 4,860 | GOLD | 9 matches with that gun |
| 20 | 15,960 | DAMASCUS | 29 |
| 30 | 33,060 | DIAMOND | 60 |
| 40 | 56,160 | GALAXY | 102 |

## The camos

Wrap ids `mastery_gold`, `mastery_damascus`, `mastery_diamond` and `mastery_galaxy` (agreed with the gun-hats/wraps
session, which drew them: `tools/roblox/wrap_textures.py`, `studio-tools/WrapBook.luau`, the effects in WrapAnim).
Their Roster rows are named Mastery Gold, Mastery Damascus, Mastery Diamond and Mastery Galaxy, so they don't read the
same as the Spray Can's Gold, Damascus and Galaxy. The toasts use the ladder's own words: GOLD, DAMASCUS, DIAMOND,
GALAXY.

- **Out of every list that sells or rolls.** The rows are in `Roster.wrapById` and `Roster.masteryWraps`, never in
  `Roster.wraps`. The Spray Can's pool (`LootTable.cosmetics`), the shop's rotation (`Shop.singlesPool`), the bundles
  and the VIP pack all walk `Roster.wraps`, so none of them can hold one. `Loot.luau` also refuses a "buy" or any
  `Loot.grant` offer (a gift, a pack) with a mastery camo in it.
- **Granted per gun.** `Loot.grant(p, "mastery:mastery_gold@ar", "mastery:<userId>:mastery_gold@ar")`: only
  `MasteryXp` asks, the pair `mastery_gold@ar` goes into the loot save, once (the receipt, and ownership).
- **Live.** A camo shows (the WRAPS strip, the bars' next-camo swatch) and is granted only once its picture is in the
  place, `ReplicatedStorage.JankfireWraps.<id>` (the wraps session's WrapBook), or while `ReplicatedStorage` has the
  attribute `MasteryLive = true` (Studio tests). A player who passed a camo's level before it went live gets it on
  their next join, their next level up, or at once if they're in the server when it goes live.

## Where it lives

- `shared/Mastery.luau`: the numbers, the curve, the camos, `live`, `wrapList`, the attribute's encoding. Pure.
- `server/MasteryXp.luau`: adds XP, levels, grants (`sync`), tells the client. Stats binds its save here.
- `server/Stats.luau`: the save (`mx = { [weapon] = xp }` in `JankfireStats_v1`, session-locked, `_studio` in Studio)
  and every hook: kills and headshots (`onKill`), assists (`onHurt` keeps who hurt whom), rounds (`onRound`, the time
  held per weapon in `Cur.rwt`), the match won (`finish`). `masteryCounts` is the "does this match count" check.
- `server/Loot.luau`: the `mastery:` grant path, the refusals, `Loot.testDrop` (Studio only).
- `shared/Roster.luau`: the four rows (the wraps session's) and the move out of `Roster.wraps` (ours).
- `client/MasteryUI.luau`: the bars. `client/MasteryClient.client.luau`: the toasts and the match card.
- `client/LoadoutUI.client.luau`: calls the bars, lists the camos in WRAPS (after the free wraps), MASTERY · LV n as
  their source in the strip's header, LV n on their lock, "unlocks at <weapon> level n" when clicked locked.

## On screen

- **The loadout's weapon card** (the info panel, under the name and chips): LV n, the XP into the level / what it
  takes, a thin bar, and the next live camo as a small dimmed swatch with a lock and "GOLD AT LV 10". At 40: MAX.
- **The armory cards:** LV n bottom right and a hairline bar along the bottom.
- **WRAPS:** the four camos after the free wraps, locked with LV 10 / 20 / 30 / 40 until owned on that gun.
- **A level up:** a quiet plate at the top in the middle, under the account level's plate: LEVEL 12 over the weapon.
- **A camo:** the same plate with the camo's swatch: GOLD UNLOCKED · ASSAULT RIFLE, and the reward sting.
- **After a match:** a card left of the end screen (the ranked card has the right): WEAPON XP, each weapon used with
  +XP, LV n and its bar filling from where the match started. A narrow screen gets it along the bottom.
- Nothing takes input: keyboard, pad and touch play on through it.

## Clients

- The player attribute `Mastery` = `"ar=5120;smg=40"`, XP per weapon (`Mastery.decode`).
- The remote event `JankfireRemotes.MasteryPush` (made by `MasteryXp` if the place lacks it):
  `{ k = "level", w, lv }`, `{ k = "camo", w, c }`, `{ k = "match", gains = { [w] = xp }, xp = { [w] = total } }`.

## Studio tests

`ServerStorage.JankMasteryTest` (a BindableFunction, Studio only):

- `("read", p)`: `{ mx, levels, camos (owned pairs), live, attr }`.
- `("add", p, weapon, n)`, `("set", p, weapon, level)`, `("put", p, map)` (a backup back).
- `("live", true | false)`: every camo live, or back to "picture in place".
- `("drop", p)`: every mastery camo off the loot save with its receipts (a test's grants undone).
- `("sync", p)`, `("toast", p, "level" | "camo" | "match", ...)`.

A kill that counts, alone in Studio: `JankStatsTest("begin", p)` opens a test match, `JankStatsTest("ghost",
dummyName)` makes that dummy count as an enemy, then a real shot from the Client datamodel through the Fire remote
(`roblox-weapon-testing`). Back it all up first and put it back after, in this order: `JankMasteryTest("live",
false)` and `JankStatsTest("put", p, backup)` (the XP back) FIRST, then `JankMasteryTest("drop")`, then
`JankStatsTest("ghost", "")` and `("save")`. Dropping first re-grants the camo at once: the drop changes the loot save,
and the catch-up sees the XP still past the camo's level.

In the training hall any wrap can be worn ("trying", nothing saved), so "the camo is refused on another gun" is only
a real check in the hub.

## Tested

Solo Play at place version 980 (pushed as one guarded patch model, asset 81894793769478, dry-run first):

- **A dummy gives nothing:** an AR shot through the Fire remote killed `Dummy2` with no match open: no weapon XP.
- **A counted kill:** with a Stats test match and `Dummy` as the ghost, the same shot gave `ar=100`. The server didn't
  score that shot as a head hit (it was aimed at the head's position from the root; `Rules.headAimed`), so the +25
  wasn't seen.
- **The match won:** `JankStatsTest("finish", p, "W")` gave the AR +50 (`ar=150`), the weapon held in it.
- **Gold at 10, that gun only:** `("set", p, "ar", 10)` granted `mastery_gold@ar` and nothing else.
- **What a rejoin loads:** after a save, the `_studio` stores themselves held `mx.ar = 4860` and the pair
  `mastery_gold@ar` (read straight from the DataStores).
- **Wearing it:** in the hub the Loadout remote put Gold on the AR and refused it on the SMG. Loadout.luau's refusal
  still says "it's in spray cans" (the shop session's file): a follow-up.
- **A buy:** `buy "wrap:mastery_gold@smg"` was refused.
- **Put back:** the `_studio` saves were restored (no camo, no mastery receipt, no mastery XP; kills and XP as before).

On screen (the gun-hats session's photo once the camos went live, place version 981, in the training hall where
anything can be tried: `docs/wrap-textures/mastery-sheet.jpg`): the weapon card's bar (LV 1, 0 / 300 XP, GOLD AT
LV 10 with the locked gold swatch), LV 1 and the hairline bar on every armory card, the four camos in WRAPS right after
the free wraps, and the header "Mastery Galaxy MASTERY · LV 40".

Solo Play at place version 982 (Studio `fa0b2665`, the camos live), photos in `docs/mastery/`:

- `("set", p, "ar", 10)` in the hub: the level toast LEVEL 10 / ASSAULT RIFLE (`level-toast.jpg`), then GOLD UNLOCKED ·
  ASSAULT RIFLE with the gold swatch and WRAPS · LOADOUT (`unlock-toast.jpg`), under the account's level plate.
- The match card through `("toast", p, "match", ...)`: WEAPON XP, a row per weapon with +XP, LV n and its bar
  (`match-card.jpg`). With no end screen up it sits left of the screen's middle and goes after 10 s.
- The loadout at level 10 (`loadout-level-10.jpg`): the weapon card's LV 10 · 0 / 840 XP · DAMASCUS AT LV 20 with the
  locked swatch, the AR's armory card LV 10 (the rest LV 1), and in WRAPS Mastery Gold first (owned, NEW) and Mastery
  Damascus / Diamond / Galaxy locked LV 20 / 30 / 40.

- **A real rejoin:** that Play was stopped with the AR at level 10 and Gold owned; the next Play loaded both on join
  (`ar=4860`, `mastery_gold@ar`). Then the owner's `_studio` saves were put back (XP first, then the camo: nothing was
  re-granted) and read straight from the DataStores: no camo, no mastery receipt or XP, the rest as before.

Not yet seen: assists and round wins in a real match (the code path is the same `MasteryXp.add` the kill took), the
headshot's +25, the match card beside a real end screen, the phone layout.

## Not done

- A camo granted to a player later found cheating stays with them (the stats reset takes their mastery XP, not their
  loot). Taking camos back would be a `Loot` change.
- The shop's INVENTORY tab lists an owned camo like any wrap; it doesn't say "mastery" there.
- The match loadout's picker (between rounds) shows no weapon level.
