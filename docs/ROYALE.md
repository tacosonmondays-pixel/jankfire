# JANK ROYALE (battle royale)

Pick **Jank Royale** as the game in Bots setup (or vote it in Online). Maps: Desert (main), Warehouse, Suburb; Jankburg next.

## How a match goes
1. Everyone boards the **JANK AIR** blimp (a smiling pink blimp) that flies a random line over the town.
2. **SPACE** jumps. Look down to dive faster. The umbrella opens by itself about 40 m up (or press SPACE again).
3. Loot is on the floor: indoors is better than roofs, roofs are better than the street.
   - Guns come with their own bullets; **Ammo Buckets** top up every gun you carry.
   - 2 gun slots + a melee slot (everyone lands with Bread). One gadget slot (G): frag, smoke, popper, duck, bubble, wand, reverse card.
   - Heals (**H**): Jank Cola (+25) and Medkits (+75). Armour: Cardboard Plate (+25), Bin Lid Vest (+50), Riot Fridge (full). Armour takes 60% of each hit until it breaks.
   - Rarity: Common / Uncommon / Rare / Epic / Legendary (white, green, cyan, pink, yellow). Better tiers hit harder (x1.08 to x1.4). Rare and up have light beams.
   - **F** picks up or swaps (you swap the gun in your hands). Walking over ammo, heals and armour grabs them.
4. The violet zone closes in 6 circles (55 s to loot first). Outside it hurts 2, 4, 7, 11, 16, then 25 HP/s. Armour doesn't help.
5. Out = spectate whoever got you (click or space for the next person). Last one standing wins; the end screen shows placements.

Server-owned: loot, inventories, every bullet, armour, zone damage. A hit with a gun you don't carry, or with no bullets left, does nothing.

## Bots
They pick a landing area (a few go for the hot drop, most spread out to quiet ones) and jump when the blimp is closest to it.
After landing, with only bread they run for the nearest gun. They loot upgrades (better guns, armour, heals, ammo, gadgets), swap their worst gun, and heal when nobody's shooting.
They pick the gun for the range (shotgun up close, AR mid, sniper far). They throw frags and ducks, and use smoke, bubble or reverse card when losing. Hurt bots leave far-off people alone; everyone prefers a target that's already being shot (third-partying).
Careful bots skip long-range fights and leave for the next circle early; the rest leave when the walk needs it. They don't hop toward drops.

### Test matches (15 bots, Desert, `JF_WATCH=1 JF_BR_LOG=1`)
| match | length | winner and why | zone deaths | canyon deaths | gadgets used |
|---|---|---|---|---|---|
| 1 | 4:44 | Steve: Rare Sniper + Legendary Cig, 68 armour, stayed out of fights | 2 | 0 | 10 |
| 2 | 4:08 | Tina: 3 kills (Redline, Revolver), ended on a Legendary Bowling Ball + Sniper; the last bot left had only bread and the zone got it | 1 | 0 | 8 |
| 3 | 2:09 | Karen: 4 kills, 85 armour, Rare Sniper + Legendary Blood Cross | 0 | 1 | 4 |

Typical deaths: hot-drop bread fights in the first 20 s; mid-game kills with real kits (minigun, redline, chicken); late game is decided by armour and who already rotated.
Run your own: `JF_WATCH=1 JF_BR_LOG=1 node server.js`, then join a Bots room as `watch...` (the watcher never fights). `JF_BR_DUMP=1` prints what every bot is doing every 8 s; `JF_BR_BOTS=n` sets the bot count.

## Ideas: what makes it ours (brainstorm, not built yet)
**POI modifiers.** Each named place bends one rule while you're inside it. The minimap and a callout show it when you walk in.
- **Liberal Lane**: liberal helpings. Every pick-up there comes in a large (double ammo and heals, +1 rarity tier). It's the hottest drop.
- **Pronoun Park**: inside the park, name tags and the kill feed show pronouns instead of names ("THEY [AR] YOU"). Nobody knows who's who, so third-partying is a gamble.
- **Overdraft Heights** (the silly one): your credit score went negative, and so did gravity. Moon jumps, slow falls, and the umbrella works off every roof.
- Also: **Number Works** (damage numbers hit for their own value: 7s and 13s), **Neon Market** (vending machines spit out a random gadget when shot), **Corp Hill** (each kill there pays a "shareholder dividend" of armour).

**Rules other BRs don't have:**
- **Return to Sender**: your first death before circle 2 mails you back in a cardboard box from the blimp, once.
- **Kill-leader bounty**: whoever has the most kills glows on everyone's minimap and drops a Legendary when they die.
- **The zone is an eviction notice**: the wall shoves you as well as hurting you, so ride it with a grapple.
- **Supply blimp**: twice a match the blimp drops a crate that you have to grapple onto before it lands.
- **Loot goblin**: a running vending machine full of Epics. Shoot it and everything inside spills out.
- **Daily rumours**: each match two random POIs get a modifier, announced on the blimp ("today at Pronoun Park: LOW GRAVITY").
