# Plant & Defuse: the economy mode (design + server contract)

Owner's ask: *"for the defuse mode, each team gets separated and then they have to purchase weapons before rounds, you earn
credits on win and kills like cs blah blah, you drop weapons on death, no grapple but weapons keep their property but limited
magazines you buy armor etc... no kill streaks!"*

This turns the existing **Plant & Defuse** game (`bomb` in `shared/modes.js`) into a round-based economy mode. Everything
here is an original design (names, numbers, UI): it borrows the *genre* of tactical round shooters, not any game's data.

- **Stage 1 (done, branch `claude/f-econ`):** the shared tables (`shared/econ.js`), the server (`server/econ.js` + small hooks
  in `server.js`) and ws tests.
- **Stage 2 (done, same branch):** the client. Section 14 lists everything it had to build; section 19 says how it was built. Sections 12 and 13 are the contract.

The economy switches on in Plant & Defuse with teams (Online and Bots rooms). `JF_ECON=0` turns it off (the old mode).
**No other game type changes.**

---

## 1. Files

| file | what |
|---|---|
| `shared/econ.js` (new) | All numbers: `ECON`, `ARMOR`, `GEAR`, `PRICES`, `ITEM_PRICES`, `OTHER_KILL`, `FALLBACK`, plus the helpers `weaponPrice`, `refillPrice`, `killReward`, `armorPen`, `ammoSpec`, `itemSpec`, `gearPrice`, `buyList`, `econWeapon`. The client imports it as `/shared/econ.js`. |
| `server/econ.js` (new) | `installEcon(Room, deps)` adds the `econ*` methods to `Room.prototype`; it throws if a name already exists. It also holds the test knobs. |
| `server.js` | Small hooks, each `if (this.isEcon()) …`, listed in section 15. No reformatting. |

The tables are data-driven. Any weapon whose `slot` is in `SLOTS` and any `ITEMS` entry is buyable. Ids without a row get
the fallback rules (section 6), so the weapons and items from the integration branch show up on their own.

---

## 2. Round flow and timings

| phase | length | what happens |
|---|---|---|
| **buy** | `ECON.buyTime` = **15 s** | Everyone respawns in their side's spawn zone, behind a barrier (section 9). Players can look around, switch weapons, buy, sell back, drop and pick up. Nobody can leave the zone. Firing, hits, items, the hook, t-bags and coughing are ignored. The bomb is handed out as before. |
| **live** | `BOMB.roundTime` = **110 s** | `elive` is sent and the barriers drop. The round clock (`bomb.left`) only starts now: `b.ends` is pushed back by the buy time. Buying stops. **No respawns.** |
| **between** | `BOMB.between` = 5 s | After a round win. Survivors can still move, fight and pick up. |

**Match.** First to `BOMB.wins` = **4** round wins. Sides swap after round `BOMB.swapAfter` = **3**, so the most a match can
last is 7 rounds. Round 1 and round 4 are **pistol rounds**: everyone has the start money and the default kit.

**At the half** (the first round after the swap):
- Everyone goes back to `ECON.start` credits and the default kit.
- Armor, kit and items are cleared.
- Loss streaks reset to 0.
- A chat line is sent: `HALF TIME: …`.

**Round wins** (`bombRoundWin(team, why)`):

| `why` | when |
|---|---|
| `exploded` | The bomb went off. |
| `defused` | A defender finished defusing. |
| `time` | The clock ran out with no plant. Defenders win. |
| `elim` (new) | One side has nobody left alive. |

How `elim` works:
- Before a plant, if every attacker is dead, the defenders win; if every defender is dead, the attackers win.
- After a plant, only *all defenders dead* ends the round (attackers win). If every attacker dies after the plant, the
  defenders still have to defuse.
- It only applies when both teams have at least one member, so an empty side doesn't hand out free wins.
- It is checked in `tickEcon`, never during buy or between, and never after the match is over.

**Death.**
- `kill()` runs as before: the kill message, katana reset and stats are unchanged.
- Then `econOnKill` runs:
  - `respawnAt = minRespawnAt = now + 1 day`, so the player stays dead until the next round's `resetWorld` brings everyone
    back. The `kill` message's `rs` still says 4500; the client must ignore it in this mode.
  - The kill reward is paid.
  - The victim's gear drops (section 8).

**Joiners mid-match** (`econJoin`, called in `addHuman` before `welcome`, and in `addBot`):
- Credits = the team's average credits, rounded down to 50, at least `ECON.joinerMin` = 800, at most `ECON.max`.
- They get the default kit.
- During the buy phase they play right away (zone set; bots shop 0.5-1.5 s later).
- After it they **sit out**: `alive = false`, `hp = 0`, and `inv.out = 1`. They play from the next round.
- A human joiner also gets `eround` and `drs` right after `welcome` (and `inv` / `ic`).

**Leaving.** If the player was alive, their gear drops where they stood, like a death. Their credits are gone, and a
reconnect counts as a new joiner. Bomb handling is unchanged.

**Mode change.** When the next match is not Plant & Defuse, `sendLoadout` calls `econEnd` for each player:
- their own skins come back, `kat` goes to 0, their own item comes back, `inv {off:1}` is sent;
- the floor is cleared (`drc`);
- humans then get the existing `loadout {lo:null}` (because `p.forced` was set), so their menu loadout comes back.

A map change or a new Plant & Defuse match goes through `newBombRound(true)` and starts a fresh economy.

---

## 3. The economy (all numbers are in `ECON` in shared/econ.js)

| | credits |
|---|---|
| start of each half (`start`) | **800** |
| cap (`max`) | **9000** (every payment is capped) |
| round win: elimination / time | **2600** |
| round win: bomb exploded / defused | **2900** |
| loss bonus by losses in a row (`loss`) | **1300, 1750, 2200, 2650** (2650 from the 4th loss on) |
| planter, when the plant completes (`plant`) | **+300** |
| every attacker, when they lose a round in which the bomb was planted (`plantTeam`) | **+600** |
| defuser (`defuse`) | **+300** |
| attackers still alive when time runs out with no plant | **0** loss bonus (`timeSurvivorBonus: false`) |
| kill rewards | per weapon, see section 4 (from 100 for the sniper to 1500 for the reverse card) |

- A **win resets** your side's loss ladder to 0. Each loss adds one step, up to 4.
- Losses are counted per team in `room.ec.lose`, and shown in `eround.lose` / `round.eco.lose`.
- **Kill rewards** are paid at the kill (`ecash`). Void and cough kills pay by the weapon that sent the victim (`via`).
  Teammates can't be damaged, so there are no team-kill rules.

**Balance check.**
- Round income averages about 2500: a win ~2600-2900 plus ~1-2 kills of 250-750; a loss ~1300-2200 plus kills.
- A **full buy** costs ~4650 for attackers (AR 3000 + vest and bucket 1000 + 2 frags 600) and ~5050 for defenders (+ kit
  400). That is roughly **2 round incomes**.
- **Eco rounds still have options:**
  - 800: a vest (650), or the knife (350) + a frag (300), or the popper/snowball.
  - ~2100 after a loss: SMG + vest (1900), shotgun + vest (1750), Peel Shooter (1400) + smoke, or marbles + vest + frag.
- **Force buys** at ~2500-3500: bowling launcher / redline + vest.

---

## 4. Price table: every weapon (`PRICES`, by slot)

`ammo`: **mag+reserve** for guns with a magazine (the reserve is `mags` × mag), **N shots** for weapons without one, or
**∞** (no ammo).
`pen`: the share of the armor's protection the weapon ignores (section 5).

| slot | id | name | price | kill reward | pen | ammo per purchase |
|---|---|---|---|---|---|---|
| primary | ar | Assault Rifle | 3000 | 250 | 0.3 | 30+90 |
| primary | smg | SMG | 1250 | 500 | 0.15 | 45+135 |
| primary | redline | Redline | 2500 | 250 | 0.25 | 40+120 |
| primary | shotgun | Shotgun | 1100 | 750 | 0 | 6+24 |
| primary | minigun | Minigun | 4200 | 150 | 0.1 | 250+250 |
| primary | sniper | Sniper | 4750 | 100 | 0.8 | 5+15 |
| primary | chicken | Chicken Rocket | 3200 | 200 | 0 (blast) | 6 shots |
| primary | bowling | Bowling Ball Launcher | 2100 | 450 | 0 | 8 shots |
| primary | bow | Bow | 1650 | 600 | 0.5 | 24 arrows |
| primary | banana | Peel Shooter | 1400 | 650 | 0 | 45 shots |
| secondary | revolver | Revolver (**the default sidearm**) | 250 | 250 | 0.5 | 6+24 |
| secondary | marbles | Marble Shotgun | 900 | 400 | 0 | 2+10 |
| secondary | cig | Cigarette | 450 | 900 | 0 | ∞ (charge / cough) |
| secondary | blower | Leaf Blower | 600 | 1000 | 0 | ∞ (its own fuel) |
| secondary | cards | Card Deck | 750 | 650 | 0 | 40 plays |
| secondary | popper | Party Popper | 350 | 1200 | 0 | ∞ |
| secondary | reverse | Reverse Card | 700 | 1500 | 0 | ∞ (its 6 s cooldown) |
| secondary | snowball | Snowball | 400 | 900 | 0 | 36 throws |
| melee | bread | Bread (**the default melee**) | free, not sold, never dropped | 1000 | 0 | ∞ |
| melee | slipper | Slipper | 450 | 850 | 0 | ∞ (it comes back) |
| melee | katana | Katana | 950 | 750 | 0 | ∞ (growth stays on the blade) |
| melee | knife | Knife | 350 | 1100 | 0.5 | ∞ |
| melee | slapper | Hand Slapper | 300 | 1050 | 0 | ∞ |
| melee | spoon | Spoon | 700 | 600 | 1 | ∞ |

**Kills with non-loadout things** (`OTHER_KILL`): frag 300, duck 350, smokegren 300, tbag 1500, bomb 0, scythe 0, hook 300.
Anything else: 300.

**Not buyable:** `slot` of `streak`, `hidden`, `item` or `null` (scythe, scythe_rifle, dash, card, duck-as-weapon, frag,
smokegren).

**Refill (resupply).** Buying a weapon you already hold refills its magazine and reserve for 25 % of its price, rounded up
to 50 (`refillPrice`): AR 750, revolver 100, sniper 1200… It is refused if the weapon is already full.

**Buying into an occupied slot** puts the old weapon on the floor at your feet. It counts as your drop, so you don't
auto-pick it straight back, and you can sell the new one and walk back over the old.

## 4b. Items (`ITEM_PRICES`): one item type in the G slot at a time

| id | name | price per charge | limit (most you carry, and most you can buy per round) |
|---|---|---|---|
| frag | Frag Grenade | 300 | 2 |
| medkit | Medkit | 400 | 1 |
| bubble | Shield Bubble | 650 | 1 |
| duck | Rubber Duck | 500 | 1 |
| smoke | Smoke Bomb | 250 | 2 |

- Each purchase adds **1 charge**.
- Charges **never recharge** in this mode (`ic.next` is always 0). They carry over if you survive and drop when you die.
- Buying a different item type puts your old charges on the floor (one type at a time).

---

## 5. Armor and the defuse kit (`ARMOR`, `GEAR`)

| gear id | name | price | |
|---|---|---|---|
| `vest` | Padded Vest | 650 | 100 armor points. Buying it again refills to 100. |
| `helm` | Vest + Bucket | 1000 total | Price = (650 if armor < 100) + (350 if no helmet). With a full vest, the bucket alone costs 350. |
| `kit` | Defuse Pliers | 400 | Defenders only. Defuse in **2.5 s** (`ECON.kitDefuse`) instead of 5. Drops when you die. |

**Damage model** (`econArmor`, called from `damage()` before HP drops; `dmg` messages carry the post-armor amount):

```
absorbed fraction = base × (1 − pen[weapon])
  base = ARMOR.head  0.40  for a headshot, and only with the helmet (no helmet: headshots ignore the vest)
       = ARMOR.blast 0.35  for explosions: chicken, frag, duck, bomb, tbag
       = ARMOR.body  0.45  for everything else
taken by armor = amount × fraction; armor points −= taken × ARMOR.wear (0.6)
if that would empty it: it takes only what it has left (points / 0.6), armor = 0 and the helmet goes too
```

Where armor does nothing:
- **No armor** against `void`, `cough`, or self-damage.
- **A player's sniper headshot always kills.** Armor and helmet are skipped, so the existing `lethal` rule stands. Bot sniper
  headshots are softened like any other headshot.
- A "headshot" for armor means the head flag on a **single-pellet hitscan** shot, or a bow arrow. Shotgun and marble pellets
  always count as body hits. A knife backstab (which uses the `hs` flag) is a body hit.

Worked numbers:

| hit | no armor | vest | vest + bucket |
|---|---|---|---|
| AR body (11) | 11 | **7.54** (shows as 8) | 7.54 |
| revolver body (40) | 40 | 31 | 31 |
| **revolver headshot (96)** | **96** | **96** (no helmet) | **76.8** |
| sniper body (55) | 55 | 50 | 50 |
| sniper headshot (player) | kill | **kill** | **kill** |
| shotgun full hit (10×8 = 80) | 80 | 44 | 44 |
| frag 100 | 100 | 65 | 65 |
| bomb 220 at the centre | 220 | 143 (still a kill) | 143 |

The armor update is sent to the victim as `ear`.

**Kit.** `tryUse` starts the defuse as before. On the next tick, `tickEcon` stamps `b.act.kit` (from the defuser's kit).
`Room.actMs(act)` gives the duration: plant 3 s, defuse 5 s, or 2.5 s with the kit. Both `tickBomb` and `roundInfo().bomb.act.f`
use it, so the progress bar is right.

---

## 6. Fallback rules (any id without an explicit row)

| | rule |
|---|---|
| weapon price | primary **2000**, secondary **600**, melee **500**. The id named in `ECON.defaultMelee` is never sold. |
| weapon kill reward | primary 300, secondary 450, melee 1000. Non-loadout kill ids: 300. |
| armor pen | 0 |
| ammo, gun with `mag` | mag + 3 × mag |
| ammo, kind `proj` / `bow` outside the melee slot | `clamp(round(6 / cd), 6, 60)` shots |
| ammo, anything else (melee, cones, `reverse`, unknown kinds such as a lasso) | unlimited |
| item | price **400**, limit = min(2, max(1, `ITEMS[id].charges`)) |

So when the integration branch adds the shredder, blood cross, scales or lasso, they appear in the buy menu with these
defaults. New items (bubble wand, party popper, reverse card) appear the same way. Add rows to `PRICES` / `ITEM_PRICES` to
tune them.

---

## 7. The ammo model (server-enforced)

**Instances.** Every weapon you hold is an instance. The server keeps:
`{ u, id, m (rounds in the magazine, or shots left), r (reserve), lim, cl (has a magazine to reload), sk, by, byName, kat, def, fresh }`.

**Kinds of weapon:**
- **Guns with `mag`** (hitscan): `m` + `r`, both shown.
- **Counted weapons** (chicken, bowling, banana, bow, cards, snowball; `cl: 0`): `m` is the shots left and `r` is 0. There is
  no reload.
- **Unlimited** (`lim: 0`).

**How a shot is counted:**
- **Hitscan.** The client sends a shot as its `hit` messages (one per target) and then its `fire`. The first of these pays
  one round; the rest of that shot ride on it (`econShot`).
  - The shot stays open for 150 ms, for up to 1 target, or 6 targets for pellet guns.
  - A pellet shot is one round.
  - With `m = 0` the server **ignores the `hit`s (no damage)** and the `fire` (not relayed), and answers `am` with the real
    count. A hitscan `hit` with no round left therefore does nothing.
  - Rate isn't checked for ammo (the client bunches up to 4 shots per frame). The existing `pairOk` per-target limiter still
    applies.
- **Counted weapons.** A round is spent only when a projectile, arrow or card actually left. `onFire` runs, and the shot
  counts if `p.lastFire[key]` changed (cooldowns can refuse a shot).
- **Reload.** The client sends `{t:'rl', w}` when it **starts** a reload. 75 % of the weapon's reload time later, the server
  moves `min(mag − m, r)` rounds and sends `am`.
  - A late `rl` is tolerated: a `fire` with `m = 0` finishes a pending reload that is ≥ 65 % done.
  - Switching weapon (the `s.w` you report) cancels a pending reload.
- **Bots** spend from the same instances (`econBotShot`). When a gun is empty they switch: primary → secondary → melee
  (bots melee in this mode).
- **Buy phase.** Nothing is spent (firing is ignored).
- **Picked-up weapons** keep `m` / `r` exactly.

---

## 8. Drops and pickups (server entities)

**A drop:** `{ id, k: 'w' | 'i' | 'k', p: [x, y, z] (on the floor, +0.15), x (weapon instance) | iid + n (item) | kit, np (no-pick: dropper id + until) }`.

**What drops on death:**
- primary, secondary, a bought melee (never the default bread), item charges, the kit;
- spread on a 0.65 m ring around the body, on the floor under it, or under the last place they stood (`p.ground`);
- if there is no floor (died over the void), it's gone;
- armor never drops;
- the bomb is handled by the existing code.

**Manual drop** `{t:'drop', s}`: at any time, buy phase included (hand a teammate a rifle in spawn).
- It lands 1.6 m in front of you, stopped by walls, and falls back to your feet over a ledge or the void.
- Allowed for the primary, the secondary, a melee upgrade (you get the default melee back), the item (all its charges) and
  the kit.

**Pickup:**
- **Auto:** walk within **1.3 m** (`autoR`, |dy| < 1.5).
  - A weapon is auto-picked only into an **empty** slot. The melee slot is never empty.
  - An item is auto-picked if you have none or the same type (up to its limit; the rest stays on the floor).
  - A kit is auto-picked by a defender without one.
  - Your own drop isn't auto-picked for 1.2 s (`dropNoPick`).
- **Manual swap** `{t:'pick', id}`: within **2.2 m** horizontally (+ up to 1 m for speed, `pickR`) and |dy| ≤ 2.5.
  - It takes the drop. What you had in that slot goes on the floor at the drop's spot (a default melee just disappears).
  - A different item type is swapped the same way. Attackers can't take a kit.

**State a weapon keeps:**
- ammo (`m`, `r`);
- the **buyer's skin** (`sk`) and `by` (buyer's name);
- **katana growth** (`kat`).

**How skins work:**
- While you hold a weapon, the server shows its `sk` in your `p.skins[id]` (`sk` broadcast), even if you don't own that skin.
  No `sk` means the default look, not yours.
- Your own cosmetics are saved in `p.ecOwnSkins` and come back when the mode ends.
- Changing your skin mid-match re-skins the instances **you bought** that you still hold.

**How katana growth works:**
- Kills grow `p.kat` as before, and the server copies it onto the katana instance.
- Dying resets `p.kat` (as before), but the dropped blade keeps its `kat`.
- Picking it up sets the picker's `p.kat` and broadcasts `kat`.

**Lifetime:**
- Every drop is cleared when the next round starts (`drc`).
- At most **48** are on the floor; the oldest goes first (`drx`).
- Joiners get the full list in `drs`.

---

## 9. Spawn barriers (geometry and enforcement)

**Zones** (`econZones`, cached per map):
- Each side's zone is the AABB of `map.teamSpawns.att` / `.def`, padded by **4 m** in x and z (`zonePad`).
- In y it runs from 2 m below the lowest spawn to 10 m above the highest (`zoneBelow`, `zoneAbove`).
- Enforcement is a **column** in x and z; y is only used to draw the barrier.

Bazaar:
- attackers `min [-20, -1.9, 54]  max [20, 10.1, 74]`. This sits inside the walled encampment (x ±22, z 52..76), so the barrier
  closes the north door (x −6..6, z 52) and the east/west doors (z 58..66).
- defenders `min [-20, -1.9, -74]  max [20, 10.1, -57]`. This closes the north passage (x −3..3) and the garden exits east and
  west.

**Fallback.** If a player spawned outside their side's zone (a map without `teamSpawns`, or one whose bomb spawns are
elsewhere), they get a personal zone: ±3.5 m around their spawn (`personalZone`), y −2..+10.

**Enforcement (server):**
- During the buy phase, `tickEcon` checks every living player each tick.
- More than **0.75 m** past the edge (`zoneSlack`):
  - the server clamps them 0.3 m inside and zeroes their horizontal velocity;
  - for humans, it sends `{t:'ezone', p}` (at most every 150 ms). The client must put the player at `p`.
- Others always see the clamped position (snapshots), even if a client ignores `ezone`.
- **Buying needs both** the server-held position *and* the position your last `s` reported (same `seq`) to be inside the
  zone.
- Bots are clamped silently and stand still during the buy phase.

**What else the buy phase blocks:**
- `fire`, `hit`, `push`, `item`, `tbag` and `cough` are ignored;
- the bomb-carrier AFK timer is held;
- buying itself is allowed.

`zones` are sent in `eround`, and your own zone is in `inv.zone`.

---

## 10. Grapple and killstreak switches (every one of them)

`ECON.grapple = false` and `ECON.streaks = false`. `Room.hookOff()` and `Room.streaksOn()` read them.

**Server (done):**
- `econHandle`: `push` with `w: 'hook'` is ignored. `s.g` is nulled, so no rope is shown or recorded.
- Bots: the grapple block in `botThink` has `&& !this.hookOff()`. `stepBot`'s rope code never runs, because `ai.hook` is never
  set.
- Streak earning in `kill()` has `&& this.streaksOn()`, so there's no pocket, no `streak {earned}` and no "earned …" chat.
- `deploy` is ignored.
- At match start, `econInitPlayer` clears `pocket` and `scythe` and the streak counter, and sends `{t:'streak', reset:1}`.
- The scythe can't be used (it isn't owned). `hit` and `fire` with weapons you don't own are ignored.

**Client (to do):**
- `tryHook` does nothing in this mode. The hook button is the **pickup** key (section 14).
- No rope drawing.
- Hide the streak tray and don't send `deploy`.
- Keys 5/6/7 do nothing, and so does V (dash).

---

## 11. Bots

**Buying** (`econBotBuy`): each bot shops 0.7-3.2 s into the buy phase, capped at 60 % of it. Rules:

| decision | when | what it buys |
|---|---|---|
| **full** | credits ≥ AR + vest + bucket (+ kit on defense) = 4000 / 4400, or already holding a usable primary and ≥ 1000 | If it has no primary: a random affordable rifle-tier gun from `ar` ×2, `redline` ×2, `chicken`, `minigun`, `sniper` (the repeats weigh more), keeping 1000 for armor if it can, else 650. Then vest + bucket (or the vest), a kit on defense, and a frag when ≥ 500 is left. |
| **pistol** | the first round of a half | A vest 60 % of the time. |
| **force** | the last round of the half, match point for either side, or credits ≥ 2400 | A random one of `smg` ×2, `shotgun`, `banana`, `bowling` that leaves 650 for a vest (else any it can afford), else `marbles`. Then a vest. |
| **eco** | otherwise | Nothing: it saves. |

A primary that is almost out of ammo (< 10 rounds) gets refilled when it can afford it.

**Weapon in hand.** The best gun with ammo, in the order primary → secondary → melee. Bots only take guns they can fire
(hitscan and projectile kinds outside the melee slot). With no ammo left they melee: they close to 1.2 m, swing at
`cd` / difficulty rate, and use the weapon's dmg, kb and slip.

**Pickups** (`econBotGoal` / `econBotWant`):
- every 0.7 s a bot looks for drops within 20 m with a clear path;
- what it values:
  - a usable gun worth more than 300 over what it holds in that slot;
  - a kit (defenders without one);
  - a frag (when it has no item);
- it walks over when it isn't fighting, and swaps on arrival;
- the bomb carrier, and defenders while the bomb is down, don't detour.

**Items.** A bot with a frag throws it at a visible target 9-26 m away, arcing it, every 1.5-4 s.

**No grapple** (section 10). During the buy phase bots stand still behind the barrier.

---

## 12. Message contracts, client → server

All are validated in `econHandle` the same way as in update 1: `has()` / `Object.hasOwn` for table keys,
`typeof` / `Number.isInteger`, alive and phase checks.
- `buy`, `sell`, `drop` and `pick` share a token bucket: 10 burst, refilling 10 per second.
- Outside this mode these types fall into `handle()`'s switch and are ignored.
- Every refusal answers `{t:'eno', why, of: <message type>}` (section 13).

| message | fields and validation | effect |
|---|---|---|
| `{t:'buy', k, id}` | `k` ∈ `'w'` (weapon), `'i'` (item), `'g'` (gear) via `has(KINDS, k)`. `id` a string and a real key: `econWeapon` + `weaponPrice != null`, `ITEMS`, or `GEAR`. Needs the buy phase, alive and not sitting out, and the zone (both positions). | Section 4. Refusals: `phase`, `dead`, `zone`, `bad`, `money`, `full`, `limit`, `side`. |
| `{t:'sell', k, id}` | Same checks as `buy`. | Undoes your **latest** purchase of that (k, id) in this buy phase, if it's untouched: a weapon still held and never fired or dropped; armor and helmet as that purchase left them (for `vest` / `helm`); the kit still held (for `kit`). Sell LIFO: after vest then bucket, sell the bucket first. Full refund. Refusals: `used`, `nothing`. The sell list resets when the round goes live. |
| `{t:'drop', s}` | `s` ∈ `primary`, `secondary`, `melee`, `item`, `kit`. Alive. Any phase. | Drops it in front of you (section 8). Refusals: `dead`, `bad`, `empty` (nothing there, or the default melee), `nowhere`. |
| `{t:'pick', id}` | `id` an integer and a live drop. Alive. Within `pickR` (+ speed) horizontally and \|dy\| ≤ 2.5. | Takes or swaps (section 8). Refusals: `bad`, `gone`, `dead`, `far`, `cant` (an attacker and a kit, an item over its limit). |
| `{t:'rl', w}` | `w` a real `WEAPONS` key that you hold, with a magazine (`cl`), not full, reserve > 0, and no reload already pending for it. | The reload lands 0.75 × reload later. No answer when refused. |

**Existing messages that behave differently in this mode:**

| message | in this mode |
|---|---|
| `s` | `w` is ignored unless you hold it. `g` is always null. A changed `w` cancels a pending reload. The reported `p` (if `q` matches) is remembered for the zone check. |
| `fire` | Ignored during the buy phase or for a weapon you don't hold. Spends ammo (section 7). Refused shots get `am`. |
| `hit` | Ignored during the buy phase, for a weapon you don't hold, or for a hitscan with no round left. Otherwise as before (`pairOk`, `rangeOk`…). |
| `push` | `w:'hook'` is always ignored. `blower` only if held, and not in the buy phase. |
| `item` | Uses your bought charges (`{i, o, d}` as before). It must match `inv.it.id`. No recharge. Ignored in the buy phase. |
| `itemsel`, `deploy` | Ignored. |
| `tbag`, `cough` | Ignored in the buy phase. |
| `redraw` | Only if you hold the cards. |
| `skin` | Your own skins are updated, and instances you bought are re-skinned. The visible set is the overlay. A fresh `inv` follows (stage 2), so your own viewmodel shows the new look. |
| `use` | Unchanged (plant / defuse). |

---

## 13. Message contracts, server → client

| message | fields | when |
|---|---|---|
| **`inv`** | `$` credits; `sl: {primary, secondary, melee}` each `W` or null; `it: {id, n}` or null; `ar` 0..100 (int); `hm` 0/1; `kit` 0/1; `zone: {min:[x,y,z], max:[x,y,z]}` or null (only during the buy phase); `out` 0/1 (sitting this round out); `ib: {itemId: chargesBoughtThisRound}`; `sell: [[k, id], …]` (what can be sold back right now). **`W` = `{u, id, m, r, lim, cl, sk, by, kat, def}`**: `u` instance id; `m` rounds in the magazine or shots left; `r` reserve; `lim` 1 = ammo counts; `cl` 1 = has a magazine (reload); `sk` buyer's skin `[wrap, hat, effect, model]` or null (default look); `by` buyer's name; `kat` katana length; `def` 1 = the free default melee. | To the player, after every change: buy, sell, drop, pickup, death, round start (after `spawn`), use of an item. **Authoritative**: rebuild the slots from it. |
| `{t:'inv', off:1}` | | The mode ended: go back to the menu loadout (a `loadout {lo:null}` follows). |
| **`eround`** | `n` round; `att` attacking team; `half` 1/2; `pistol` 0/1; `buy` ms left in the buy phase; `zones: {att: Z, def: Z}` (null on maps without team spawns); `lose: [team1, team2]` losses in a row; `start`; `max` | Broadcast at every round start, before the `spawn`s. Sent to a joiner after `welcome`. |
| **`elive`** | | Broadcast when the buy phase ends: barriers drop, buying and selling stop. |
| **`ezone`** | `p: [x,y,z]` | You were outside your zone during the buy phase. Set `ME.pos = p` and zero the horizontal velocity, with no effects. |
| **`drs`** | `list: [D…]` | Every drop, for a joiner. |
| **`dr+`** | `D` = `{id, k, p:[x,y,z], w, o?}`, with `k` one of `'w'` (weapon), `'i'` (item) or `'k'` (kit). Weapons add `u, m, r, lim, cl, sk, by, kat`. Items add `n` (charges). For a kit, `w` = `'kit'`. `o` (stage 2) = the player who put it down (a drop, a swap, a buy into a full slot); absent for deaths. The client throws it from that hand. | Broadcast when something lands, or a pile of item charges shrinks. **Upsert by id.** |
| **`drx`** | `id`, `by` (picker id; absent when it expired or hit the cap) | Broadcast when a drop goes. |
| **`drc`** | | Broadcast: the floor was cleared (round start, mode end). |
| **`ecash`** | `a` amount; `got` what was really added (after the cap); `why` ∈ `kill`, `plant`, `defuse`; `$` new total; for kills also `w` (weapon) and `v` (victim id) | To the earner: the money pop. |
| **`epay`** | `win` 0/1; `why` (`elim`, `time`, `defused`, `exploded`); `lines: [[key, amount, extra?], …]` with keys `win`, `loss` (`extra` = losses in a row), `nobonus` (survived a time loss), `plant` (team plant bonus); `kills: [count, creditsFromKills]` this round; `total`; `got`; `$`; `streak` (your team's losses in a row now) | To each player at the round's end: the money summary. |
| **`emoney`** | `m: [[playerId, credits], …]` | Your team only, at most every 400 ms after changes: scoreboard money. |
| **`ear`** | `ar` armor left; `hm` 0/1; `a` absorbed | To the victim when armor took part of a hit. |
| **`am`** | `u` instance; `w` weapon; `m`; `r` | To the shooter: a refused shot (the real count), or a reload done. |
| **`eno`** | `why`; `of` (the message type refused) | A refused `buy` / `sell` / `drop` / `pick`. |
| `round` / `sn` round info | `round.eco = {buy: ms left, lose: [l1, l2], gear?: [[id, bits], …]}` (only in this mode); `round.bomb.act.f` honours the kit. `gear` (stage 2): living players' armor, `bits` = vest 1, bucket 2, pliers 4 (only players with something); the client dresses their models. | **`round.eco` present = the economy is on.** That's the client's switch. |

**Existing messages, in this mode:**
- `kill.rs` is meaningless: the dead wait for the next round.
- `ic` keeps working for the G slot, and `next` is always 0. But `inv.it` is the authority. At round start `resetWorld` sends one stale `ic` (full charges of the old item id) right before the `inv` that corrects it, so in this mode take the G slot from `inv` only.
- `sk` carries the instance skins of what someone holds.
- `kat` follows the katana *instance*.
- `streak {reset:1}` is sent at match start.
- `loadout` is never sent during the mode.

---

## 14. The client stage: what to build

All of this is keyed on `G.round && G.round.eco` (or on having received `inv` without `off`).

1. **State.**
   - Keep `G.eco = { inv, round: lastEround, drops: Map, money: Map(id → credits) }`.
   - On `inv`, rebuild `W.slots` from `inv.sl`. Key 1 is always the primary, 2 the secondary, 3 the melee. An empty
     primary or secondary shows as an empty hotbar box and its key does nothing. If the weapon in hand is gone (dropped or
     swapped), equip the next one that exists.
   - Set `W.ammo[id] = inv.sl[*].m` and the reserve per id from `r`, and the G slot from `inv.it` (hidden when null).
   - **Don't** apply `S.loadout` or `setLoadout(S.loadout)` while the mode is on (`applyLoadout`, `spawn` and
     `pendingLoadout`). Only cosmetics apply.
   - Ignore the `streaks` UI. On `inv {off:1}`, drop `G.eco`; the `loadout {lo:null}` that follows restores the menu
     loadout.
2. **Ammo mirror.**
   - Fire only while `m > 0`.
   - The reload refills from the reserve: `min(mag − m, r)`. Send `{t:'rl', w}` when a reload **starts**.
   - `refillAmmo()` must not refill in this mode (on `spawn`, take `inv`).
   - Counted weapons (`cl: 0`, `lim: 1`): show "N left", no reload.
   - On `am`, overwrite `m` / `r` for that instance.
   - HUD: `mag / reserve`, or `N` for counted weapons, or nothing for unlimited.
   - An empty weapon clicks (`sfx.empty`). Suggest switching, or show "OUT OF AMMO: pick one up".
3. **Buy menu.**
   - **B opens it in this mode.** The conflict is resolved: in this mode B is buy and the pause menu stays on Escape. Pointer
     lock already pauses on Esc, so also add **P** as pause in every mode. Outside this mode B still pauses. Register both as
     key-registry actions (`buy`, default B; `pause`, B outside the mode, else P/Esc) so the keybinds branch can rebind them.
   - Columns: **Primary | Secondary | Melee | Items | Gear**, built from `buyList()`, which includes new weapons and items
     automatically. Each card shows the weapon icon (with your skin), name, price, kill reward (`kill`), and ammo
     (`ammo.mag + ammo.res` or `N shots`).
   - Grey out what you can't afford, show "OWNED · refill X" for held weapons (`refillPrice`), "FULL", "x/limit" for items
     (from `inv.it` and `inv.ib`), and attackers-only / defenders-only (kit).
   - Gear prices come from `gearPrice(id, inv.ar, inv.hm, inv.kit)`.
   - Right-click (or a SELL button) on things listed in `inv.sell` sends `sell`.
   - Number-key quick buy is optional.
   - Show credits big at the top and the buy-phase countdown (`round.eco.buy`).
   - It can be opened (to browse) any time; buying only works while `eco.buy > 0`, alive, and in the zone (else show
     why). Close it on `elive`.
   - Show the `eno.why` text as a toast: `money` "not enough credits", `zone` "go back to your spawn", `phase` "buy time is
     over", `full`, `limit` "you can't carry more", `side` "defenders only".
4. **Credits HUD.** Credits always on screen (bottom left, near the HP). Animate on `ecash` / `epay`.
5. **Armor on the HP box.** A second bar or number for `inv.ar`, a bucket icon when `hm`, and pliers when `kit`. Update from
   `ear`, and flash it on absorb.
6. **Kill reward pops.** On `ecash`, show "+250 · Revolver" (`why:'kill'`), "+300 PLANT", "+300 DEFUSE".
7. **Round-end money summary.** On `epay`, show a panel for ~4 s: WIN or LOSS (reason), each line ("Round win +2900",
   "Loss bonus ×3 +2200", "Survived a time loss: no bonus", "Bomb planted +600"), "Kills ×2 +500", the total, and the new
   credits. Also show the next loss bonus (`streak` → `ECON.loss[min(streak, 4) − 1]`).
8. **Scoreboard money.** Teammates' credits from `emoney`, and your own from `inv`. The enemy's are hidden. Show armor and kit
   icons for yourself.
9. **Barriers and countdown.**
   - From `eround.zones`, draw each zone's 4 side walls as translucent team-coloured planes, `min.y..max.y`, with a scrolling
     stripe.
   - While `round.eco.buy > 0`, show a big "BUY PHASE 0:12" countdown and "barriers drop in…". Remove the walls on `elive`.
   - Add the walls as client-side collision boxes during the buy phase, so honest players never get an `ezone`. On `ezone`,
     set the position silently.
   - Zones can be null (maps without team spawns): then draw `inv.zone` (your personal one) only.
10. **Drops in the world.**
    - Render `dr+`, `drs` and `drc` / `drx` as the weapon model (`buildWeapon(w, sk)` with the drop's skin, scaled by `kat`
      for katanas) lying on the floor, slowly spinning, with an outline. Items get their icon model and kits a small pliers
      box.
    - Looking at one within 2.2 m shows a prompt: "E: pick up Shotgun (6/24, p1's) · swaps your AR". Use the actual
      hook/pickup key name.
11. **Keys** (register these in the key registry):
    - **Pickup / swap** = the grapple button (E, or the mouse side buttons, or right-click with `swapAim`). It sends
      `{t:'pick', id}` for the drop under the crosshair, or the nearest one within reach.
    - **Drop** = **H** (stage 2 changed it from Z: Z is the spray on the integration branch). It sends `{t:'drop', s: <slot of the held weapon>}`, and Shift+H drops the item.
    - Both work only in this mode.
12. **Death and sitting out.**
    - On your death, show the death card, then "OUT UNTIL NEXT ROUND" (ignore `kill.rs`) and spectate a living teammate
      (follow their interpolated remote; Space / click cycles).
    - If `inv.out` arrives right after `welcome`, set `ME.alive = false` and spectate.
    - The next `spawn` brings you back.
13. **No hook, no streaks** (section 10): hide the rope and the tray; 5/6/7 and V do nothing. The killcam can stay.
14. **Remote players.**
    - Nothing new: `sk` already carries the instance skins, and `kat` the blade length.
    - The first-person viewmodel uses the instance `sk` from `inv`, not `G.equipped`, for weapons someone else bought.
15. **Round banner.** On `eround`, show "ROUND n · ATTACK / DEFEND · BUY PHASE", plus "PISTOL ROUND" and "HALF TIME:
    credits reset" (when `half` is 2 and `pistol`). Add `elim` to the `bombev win` reason texts ("team wiped").

---

## 15. Hooks in server.js (all additive)

- **import:** `installEcon` from `./server/econ.js`, then `installEcon(Room, {send, cleanSkins, enforceSkins, logErr, BOT_GUNS, refreshInv})` after the class.
- **`handle()`:** the first line is `if (this.isEcon() && this.econHandle(p, m)) return;`.
- **`sendLoadout()`:** in this mode, `econLoadout(p)`. Otherwise, a leftover `p.ec` gets `econEnd(p)`.
- **`addHuman`:** `econJoin(p)` before `welcome`. **`addBot`:** `econJoin(b)`.
- **`remove`:** `econLeave(p)`.
- **`botThink`:**
  - the melee range preference `[0, 1.2]`;
  - the grapple block has `&& !this.hookOff()`;
  - `botGoal` first asks `econBotGoal`;
  - `botFire` first asks `econBotShot`.
- **`damage()`:** `amt = this.econArmor(...)`.
- **`kill()`:** streak earning has `&& this.streaksOn()`, and the end calls `econOnKill(t, killer, w, via)`.
- **`roundInfo()`:** `act.f` uses `this.actMs(b.act)`, and `econRoundInfo(r)` adds `r.eco`.
- **Bomb rounds:**
  - `newBombRound`: `econNewRound(first)` before `resetWorld`;
  - `bombRoundWin`: `econRoundEnd(team, why)` after the win broadcast;
  - `tickBomb`: uses `this.actMs(b.act)`.
- **`tick()`:** `tickEcon(n)` right after `tickRound()`.
- **Test knob:** `addHuman` calls `econTestStart()` when `JF_FFA_BOMB` is set.

---

## 16. Test knobs

| knob | effect |
|---|---|
| `JF_ECON=0` | Economy off (the old Plant & Defuse). |
| `JF_BUY_TIME=s` | Buy phase length (≥ 1). |
| `JF_START_MONEY=n` | Start credits. |
| `JF_ECON_MAX=n` | Cap. |
| `JF_FFA_BOMB=n` | The Online room starts Plant & Defuse on Bazaar once n humans are in (2-team ws tests). |

The existing `JF_BOMB_WINS`, `JF_BOMB_ROUND` and `JF_BOMB_FUSE` still work.

---

## 17. Test plan and results

Scripts are in `wf_econ/tests/`. Run with `run2v2.sh <port>` and `runbots.sh <port>`; the others are plain `node`.

1. **`t_armor.mjs`: unit tests**, 26 checks. Armor math (vest, helmet, pen, blast, wear, the sniper headshot rule, the 96
   revolver), every weapon and item priced, unbuyable ids, the fallbacks for new weapons, items and kinds, gear and refill
   prices.
2. **`t_match2v2.cjs`: Online room, 4 scripted humans (2v2) plus a mid-match joiner, a whole match**, 84 checks. Server:
   `JF_FFA_BOMB=4 JF_START_MONEY=5000 JF_BUY_TIME=10 JF_BOMB_ROUND=30 JF_BOMB_FUSE=8 JF_BOMB_WINS=3`.
   - **Buying and selling:**
     - buys, gear upgrade pricing, the attackers' kit refusal, the item limit, the vest still sellable after buying the kit;
     - selling back, the old weapon dropped and auto-picked back after selling;
     - 40 junk messages that change nothing: `__proto__`, arrays, objects, `null`, `1e999`, negatives, floats, strings,
       streak and hidden weapons, nesting that is too deep;
     - a `__proto__`-keyed buy that is an ordinary buy.
   - **The buy phase:** no firing, damage, hook or t-bag. Walking through the barrier: `ezone`, others see you inside, the buy
     is refused.
   - **Damage and ammo:**
     - AR through a vest = 8;
     - a revolver headshot without a helmet = 96;
     - the kill pays 250.
   - **Drops and pickups:**
     - the dead player's gear drops with its ammo, skin and buyer;
     - picking up from 6 m is `far`;
     - the manual swap keeps the instance and skin, and others see the buyer's skin;
     - the swapped-out AR drops with its 27 rounds.
   - **Bomb:**
     - plant +300;
     - defuse with the kit in ~2.5 s, +300;
     - payouts 2900 versus 1300 + 600.
   - **Running dry:** the revolver drained to `am m=0 r=0` with reloads; then a hit does no damage.
   - **Survivors and katana kills:** survivors keep their gear; the dead get the default kit. Katana kills pay 750 and the
     blade grows to 2. No streaks; the hook is ignored.
   - **The joiner:** sits out, gets the team's average credits, plays the next round, and drops their gear on disconnect.
   - **The katana drop:** the bomb explodes and the katana owner's dropped blade keeps `kat 2`. Picked up, the picker's `kat`
     is 2.
   - **The half:** sides swap, credits reset, loss streaks reset.
   - **Endings and the ladder:**
     - a time-out gives the surviving attackers no bonus;
     - the loss ladder pays 1300 then 1750;
     - the match ends first to 3.
   - **Weapons you don't hold:** a sniper `hit`, a chicken `fire` and a scythe `hit` are all ignored.
   - **Over the whole match:** no streak was ever earned, and items never recharge.
   - Result: **84 passed, 0 failed**, server log clean.
3. **`t_botsmatch.cjs`: bots room, 1 scripted human + 7 bots, a whole match** (`JF_BUY_TIME=3 JF_BOMB_ROUND=25 JF_BOMB_FUSE=8`,
   first to 4).
   - **Credits:** everyone starts on 800; the vest buy leaves 150.
   - **Bot buying by credits:** pistol rounds are on revolvers. Teammate bots' credits match what they hold (eco → revolver,
     force → bowling / banana / smg, full → AR / redline…).
   - **Death:** a t-bag death drops the revolver, and no respawn follows within the round.
   - **Payouts:** every one matches the tables. The ladder climbs and resets, including at the half.
   - **The half:** back to 800 and the default kit.
   - **Bot behaviour:** bots never grapple (0 hook frames), only hold usable guns, and pick things up. Bots buy primaries in
     non-pistol rounds.
   - **The end:** the match ends first to 4, and no streaks were earned.
   - Result: **18 passed, 0 failed** (several runs), server log clean.
4. **`t_othermodes.cjs`: other modes unchanged**, 12 checks.
   - Online deathmatch: no `round.eco`; econ messages are ignored and nothing econ is sent back.
   - The hook push lands (`kb`). The 3-kill streak is earned and deploys. Respawns happen. The frag recharges.
   - A bots-room deathmatch: bots grapple, and there are no econ messages.
5. **`t_reload.cjs`: reload timing**, 4 checks. An empty magazine stays empty at 50 % of a reload. A late `rl` is
   tolerated at ~70 %. Switching weapon cancels a pending reload.
6. **Playwright regression subset**, `regress2.sh <wt-econ> 4764 t_items t_streak t_replay t_bomb`.
   - With the economy on, 4/4 pass. `t_bomb` runs a whole bots match through the buy phases: bots plant, defuse and fetch
     the dropped bomb.
   - With `JF_ECON=0`: `t_streak` and `t_bomb` pass.
   - The baseline is `scratchpad/baseline-main.txt`, where all four pass. `t_streak`'s `spin` flag is timing noise: it read
     false once on this branch, then true on a rerun (the deathmatch path never enters econ code).
7. **Long bots match** (`BT=8 BR=80 BF=20 runbots.sh`). With 80 s rounds the attacking bots plant, the defenders defuse,
   and bomb wins and defuses are paid. Bots full-buy at ≥ 4000 (chicken, AR), force at ~3000-3800 (bowling), and eco in
   between.

---

## 18. Merge notes

- `econ*` method names are unique: `installEcon` throws on a clash.
- New weapons, items and modes need no econ change. Add price rows to tune them.
- `ECON.games` lists the game types that run the economy. The Backrooms map works through the personal-zone fallback if its
  bomb spawns aren't `teamSpawns`. Per-map `roundTime` keeps working, because the buy time is *added* to `b.ends` after it is
  set.
- The client keybinds branch should own the keys: `buy` (B in this mode), `drop` (H), `pickup` (= the hook key), and a
  `pause` fallback (P). They're all in `ECON_KEYS` in econ.js.

---

## 19. Stage 2: the client (how it's built)

**Files.**

| file | what |
|---|---|
| `public/js/econ.js` (new) | State (`G.eco`), the econ message handlers, the buy menu, credits / armor / pops / money summary / banners on the HUD, pick up + drop, the client-side barrier, sitting out + spectating, `ECON_KEYS`. Hooks for main.js and weapons.js. |
| `public/js/econ3d.js` (new) | 3D: the armor on player models (plate carrier, bucket, pliers), gear on the floor (real weapon models that tumble and settle), the barrier walls, gear icons, the first-person `econ_buy` / `econ_grab` / `econ_toss` / `econ_strap` moves. |
| `main.js` | One import + ~15 one-line hooks (below). |
| `weapons.js` | `setSlots(ids, i, anim)` and `playVM(name)`; `W.skinOver` (instance skins) where `G.equipped` was read; `W.eco` hooks (`dry`, `canReload`, `reloading`, `reloaded`, `hud`); empty slots can't be switched to; no refill / no item recharge when `W.eco` is set. |
| `remote.js` | `setGear(bits)`; `build()` builds with `gearLook()` (no hat under the bucket) and calls `dressGear()`; small armor bits skip their own outline shell (`userData.noShell`). |
| `player.js` | `tryHook()` hands the press to `G.noHook` (pick up) when it's set. |
| `icons.js` | `objIcon(key, build)`: any model as a picture with the weapon icons' lights (the gear cards). |
| `style.css` | One appended block. `index.html` is unchanged (econ.js builds its DOM). |
| `server/econ.js` | Three small additions: `round.eco.gear`, `dr+.o`, and a fresh `inv` after a `skin` change (section 13). |

**main.js hooks:** `initEcon({pause, lock})` at setup; `econKey(e)` first in keydown (after the in-game check); `econMouse(e)` in
mousedown (after the killcam check); `!econMenuOpen()` in the pointer-lock pause; `econWelcome(m)`, `econKill(m)`, `econSpawn(m)`
in those handlers; `econIc(m)` first in `onIc`; `econLoadout()` first in `applyLoadout`; `econReset()` in `resetWorldState`;
`econFrame(dt)` right after the movement steps; `econDead()` for the dead-screen line; `econCam(cam, dt)` after the replay
camera; `econHideVM()` on the viewmodel scene; `W.skinOver` in `skinOf`; `bombev` round banner suppressed (`ecoOn()`) and
`elim: 'team wiped'`.

**Keys** (all in `ECON_KEYS` in econ.js, one place for the keybinds merge):

| action | key | notes |
|---|---|---|
| buy menu | **B** | This mode only. Everywhere else B still pauses. In the menu: 1-5 picks a column, then 1-9 / 0 buys; Backspace goes back; B / Esc closes. |
| pause | **P** | Every mode. Esc still pauses through pointer lock. |
| drop | **H** | What you hold; **Shift+H** drops your item. Not Z (Z is the spray on the integration branch). |
| pick up / swap | the grapple button | E, mouse 4/5, or right click with `swapAim`: `tryHook()` calls `G.noHook`. |
| nothing | 4, 5, 6, 7, V | Scythe slot, killstreaks, dash. |

**Behaviour notes.**
- The client-side barrier clamps you `PH.halfW` inside your `inv.zone` during the buy phase (after the movement steps), so
  honest players never get an `ezone`.
- A new instance in a slot goes in your hands with `econ_buy` when you just bought it, `econ_grab` when you just picked it up on
  purpose; walking over something into an empty slot doesn't switch. Dropping what you hold plays `econ_toss` and the next weapon
  draws after it (the inventory change waits for the toss).
- Counted weapons spend a shot when a `fire` message leaves (net.send is wrapped); magazine guns use the normal path, and a reload
  only starts with rounds in the reserve (`rl` is sent then). `am` and `inv` overwrite the counts.
- In the buy phase the client doesn't fire or throw items (the server ignores them and wouldn't correct the counts).
- Spectating starts 2.6 s after you die (after the killcam if there is one): a chase camera behind a living teammate's shoulder,
  Space / click for the next one. A joiner who sits out spectates at once.
- Other players' armor comes from `round.eco.gear` in every snapshot; a model is rebuilt only when its bits change (never
  while dead, so the gibs keep the armor).
- `round.eco.gear` makes armor visible to everyone, enemies included, as on real player models.
