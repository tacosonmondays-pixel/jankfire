# BOARD GAME NIGHT: the party board mode (design, not built yet)

Owner: "mario party mode but hte mini games are quick play modes, if you land on someones space, its a duel, theres like
a 3v1 mode 4vboss 1v1v1v1 2v2 etc some are actual party games like maybe one involbes the chopping cart, etc"

Our own party board game, inspired by the genre and never copied: our names, our board, our money, our prize, our rules.
Four pawns (bots fill) roll round a cardboard board on a kitchen table. Between turns everyone gets dropped into a
short minigame, and most of those are JANKFIRE modes we already have, on small maps with a 60-90 s clock. Every number
here is a default the owner can change.

## 1. Names

| thing | name | notes |
|---|---|---|
| the mode | **BOARD GAME NIGHT** | hub tile tagged **PARTY**. the code calls it `bgn` (`p.party` is already the party system's id) |
| currency | **COUPONS** | expired, crumpled, still legal tender |
| the prize | **GOLDEN BREAD** | a gold-leaf loaf (the Bread's big brother). most bread wins |
| the board | **THE KITCHEN TABLE** | a fold-out cardboard board on a real kitchen table at night: soda cans, a pizza box, a chip bag as scenery |
| start space | **THE BOX LID** | pawns start on the upturned lid |
| the die | **THE FOAM DIE** | one chunky foam d6, thrown onto the table |
| the host | **THE RULES GUY** | a mannequin in a cardigan holding the rulebook upside down. reads the rules wrong, deadpan |
| the shortcut | **THE CREASE** | the fold down the middle of the board. shorter, but sticky |
| the bread shop | **THE BAKERY** | the space where golden bread is sold. moves after every sale |
| the item shop | **CORNER STORE** | |
| last 3 rounds | **LAST CALL** | the twist (section 2.9) |
| the ending | **THE TOASTING** | the winner pops out of a giant toaster holding the golden bread. fireworks |

Space types (each one a colour and an icon on the board):

| space | colour | on landing | callout |
|---|---|---|---|
| COUPON | green `#39ff14` | +3 coupons (+6 in LAST CALL) | `+3 COUPONS` |
| LATE FEE | red `#ff3030` | -3 coupons (never below 0) | `LATE FEE` |
| JANK | magenta `#ff00dc` | a chaos event (2.5) | `JANK!` |
| CORNER STORE | yellow `#ffe14d` | the shop opens (2.4) | `SHOP'S OPEN` |
| SODA SPILL | brown, crease only | sticky: next turn you move half your roll (rounded up) | `STUCK` |
| THE BAKERY | gold | buy golden bread, passing counts (2.6) | `GOLDEN BREAD!` |
| THE BOX LID | white | start. passing it: +5 coupons | `ALLOWANCE` |

Voice samples. The Rules Guy: "that's not how you play. anyway.", "rolled a one. bold.", "the bread has moved. don't ask me
how." Item and event text is one or two plain sentences with a joke, as in `shared/weapons.js`.

## 2. The board loop

```
 BOX LID > + + - J + $ + - + J + - +  >──────────────┐
    ^                                                 v
    + ┌─fork A──── THE CREASE (7) ─────── fork B ─┐  -
    J │  ~ J ~ + ~ - ~   (~ = soda spill)          │  +
    - └──────────────────────────────────────────-┘  J
    + < - + J + $ + - + J + - + + - < ───────────────┘
 main loop: 36 spaces, 6 of them "plates" the bakery can sit on. the crease skips 12 spaces of the loop for 7
```

A session is **N rounds** (default 10; 5 / 10 / 15 to pick). One round is every seat taking a turn, then a minigame.

### 2.1 Seats and turn order
- 4 seats. Humans first, bots fill the rest (`[bot]` names, same as today). Everyone starts on the Box Lid with
  10 coupons and 0 bread.
- **Round 1:** everyone throws the foam die at once ("DIBS"). Highest goes first, ties throw again.
- **Every round after:** standings reversed, so last place goes first. Ranking is bread, then coupons. It's a small
  catch-up and it gives the turn order a meaning.

### 2.2 A turn
1. **Before the roll:** you may use one item from your bag (2.4).
2. **ROLL:** you hit ROLL. The server rolls 1-6 (never the client). The client throws the die so it lands on that face.
3. **Move:** the pawn hops space by space (0.35 s each). These interrupt the walk: the Box Lid (+5), the Bakery (2.6),
   a WET FLOOR SIGN (stop), a BANANA PEEL (slip back 3), and a fork (4).
4. **Fork:** at fork A you pick LOOP or CREASE (8 s, then the server picks). Fork B only joins the paths back up.
5. **Land:** if someone else's pawn is on the space, it's a **DUEL** first (2.7). Then the space's effect.
6. Next seat. Once every seat has gone, it's minigame time (2.8).

Choice timers: 10 s online, 30 s offline (solo players get thinking time). On a timeout the server makes the choice
with the same brain the bots use, so an AFK player still plays (badly).

### 2.3 Landing effects
See the space table. Two coupon rules: coupons never go below 0, and every change is a server event with a reason, so the HUD
can show "+3 COUPONS" or "LATE FEE" over the right pawn.

### 2.4 Corner Store and items
Land on a store and buy up to one item (bag max 3). An item is used before your roll, one per turn. Items change the
board, never your stats.

| item | cost | what it does (in-game text) |
|---|---|---|
| BANANA PEEL | 5 | "drop it on your space. the next pawn through slips back 3. hard bananas, soft landing." |
| WET FLOOR SIGN | 6 | "put it up to 6 spaces ahead. the next pawn to get there has to stop. legally." |
| SHOPPING CART | 8 | "roll the die twice and ride. you can't stop at shops or the bakery. carts don't have brakes." |
| FAKE BREAD | 10 | "turn any COUPON space into a fake bakery. whoever buys there pays you and gets a sponge." |
| LASSO | 12 | "yank any pawn onto your space. that's a duel." (once per round per seat) |

A space holds one trap at a time (peel, sign or fake bread). Traps last until something triggers them, or for 3 rounds.

### 2.5 JANK spaces (chaos)
The Rules Guy spins a little wheel. Each event is equally likely, and you never get the same one twice in a row:

| event | effect | callout |
|---|---|---|
| MARBLES! | every pawn slides 1-3 spaces, random direction (no duels from sliding) | `MARBLES!` |
| DUCK RAIN | 3 random spaces get a duck; pawns there lose 5 coupons | `DUCKS INBOUND` |
| TAX AUDIT | the richest seat pays the poorest 10 | `AUDITED` |
| MISREAD THE RULES | the bakery moves right now | `HE MISREAD IT` |
| SWAP MEET | you swap places with a random pawn | `SWAP MEET` |

### 2.6 The Bakery (the moving golden-prize space)
- The bakery sits on one of 6 plate spaces on the main loop (never in the crease). Passing or landing on it stops you
  with "BUY GOLDEN BREAD? 20 COUPONS" (YES yellow, NO white). One bread per visit.
- After every sale it moves to a different plate at least 8 spaces away, with a puff of flour and "THE BREAD HAS MOVED".
- If you can't afford it: "come back with 20 coupons." The pawn walks on.
- FAKE BREAD looks the same from far off. Up close it's a bit too shiny (the client draws a sponge texture).

### 2.7 Duels
- **Trigger:** your move *ends* on a space with another pawn on it (passing doesn't count), or you lasso someone. With
  two pawns there, you pick which one.
- **Stakes:** the lander picks one: **10 COUPONS** (the loser pays up to 10), or from round 4 **1 GOLDEN BREAD** (only
  if the target has one; it costs the lander 10 coupons to put it on the table, paid even on a loss).
- **Format:** 1v1 in a minigame from the duel pool (section 3), 60 s, chosen by The Rules Guy (random, no repeat of the
  last 3). The other two seats watch: they're benched and get the spectator cam.
- **Tie:** sudden death, +20 s, first point wins. Still tied: `HUNG JURY`, the stake goes back.
- **Bot vs bot:** if no human is in the duel, it's settled on the board in 3 s ("THEY SETTLED IT OUTSIDE": a slap-fight
  dust cloud and a weighted coin flip). `JF_BGN_BOTDUEL=1` plays it out for tests.

### 2.8 The end-of-round minigame
**Picking the format.** It's rolled with weights: FFA 1v1v1v1 40, 2v2 25, 3v1 20, 4 vs BOSS 15. Never the same format twice in a
row. Round N/2 is always a BOSS (HALFTIME BOSS). Then a minigame of that format, with no repeat in the last 4.

**Who's on which side.**
- 2v2: 1st and 4th place vs 2nd and 3rd, so it's balanced. In round 1, random pairs.
- 3v1: **EVERYONE VS THE LEADER**. The leader is the 1 (random if tied). The 1 gets a mode-specific edge (patient zero,
  the Overdrive Rig).
- BOSS: all 4 seats on one team against a bot boss (a 5th, temporary player).

**Payouts (coupons):**

| format | win | lose | notes |
|---|---|---|---|
| FFA 1v1v1v1 | 1st +10, 2nd +6, 3rd +3 | 4th +1 | the +1 is a "participation coupon" |
| 2v2 | +8 each | +1 each | team score from the mode |
| 3v1 | the 1 wins: +15 | the 3 win: +5 each | the leader takes a real risk |
| 4 vs BOSS | boss down: +8 each, +5 MVP (most damage) | boss lives: +2 each | `RENT IS DUE` on a loss |
| duel | the stake | | |

The flow is: an intro card (5 s: name, format, one line of rules, controls, 3-2-1), the game, then a results card (6 s), then back to the board.

### 2.9 LAST CALL (the last 3 rounds)
The Rules Guy finds "the back of the box": COUPON spaces pay double, and the seat in last place picks one HOUSE RULE out of 3
for the rest of the game:
- **CHEAP BREAD**: bread costs 10.
- **NO MORE FEES**: every LATE FEE becomes a JANK.
- **BOSS RUSH**: the next minigame is a BOSS.

### 2.10 The end, ties and The Toasting
- After the last round's minigame, the most golden bread wins and coupons break ties. Still tied, it's a **TIEBREAKER**:
  a sudden-death spoon fight (Spoons & Grapples on Crate, first kill) between the tied seats.
- **THE TOASTING:** the pawns line up on a cereal-box podium, a giant toaster pops the winner up with the golden bread,
  fireworks (`public/js/fireworks.js`), and a callout like `TOASTED`.
  Then the usual end screen: PLAY AGAIN / LOBBY (`server/hubback.js`).
- Rewards: the winner gets the normal match win (`wins` stat, XP, a container roll), with the usual eligibility (offline:
  3 bots, online: 2 real people). Minigames themselves pay no rolls.

## 3. The minigames

Small maps only: **Crate** (a 30 x 30 m toy box floating in the sky, 4 spawns), **Platform** (the oil rig deck,
about 72 x 52 m) and **Rooftop** (two towers and the pool deck). Every map change is a `cfg` broadcast plus a `loadMap`
on the client (main.js), so we stick to these three.

**Build** column: **config** means the board installer only sets `setGame` + map + round time and target. **code** means the mode needs changes.
Team rows also need the forced sides from section 4.3, which is shared code built once.

| # | name | formats | reuses (game / map) | timer | win rule | build |
|---|---|---|---|---|---|---|
| 1 | CRATE BRAWL | FFA, 1v1 | `dm` / Crate | 60 s | most kills | config |
| 2 | SPOON FIGHT | FFA, 1v1, 2v2 | `spoons` / Crate | 60 s | most kills (team kills in 2v2) | config (2v2: sides) |
| 3 | HOT FLOOR | FFA, 1v1 | `lava` / Platform | 75 s | most kills, lava deaths count against you | config |
| 4 | DUCK DODGE | FFA | `duckrain` / Rooftop | 60 s | most kills | config |
| 5 | MYSTERY MEAT | FFA, 1v1 | `rand` / Crate | 60 s | most kills | config |
| 6 | ONE-SHOT WONDER | FFA, 1v1 | `oitc` / Crate | 90 s | last one standing, 2 lives | code: lives per room (`GAMES.oitc.lives` is global) |
| 7 | SPEED LADDER | FFA, 1v1 | `gun` / Crate | 90 s | first spoon kill, else the highest rung | code: a 6-rung ladder per room (`GG_FIXED` is env only) |
| 8 | RED VS BLUE | 2v2 | `tdm` / Platform | 75 s | team kills | config + sides |
| 9 | TAG SALE | 2v2 | `tags` / Platform | 75 s | team tags | config + sides |
| 10 | EVERYONE VS THE LEADER | 3v1 | `inf` / Rooftop | 60 s | the 1 (patient zero) turns all three: they win, else the three | code: patient zero = the 1 (`tickInfect` picks at random) |
| 11 | THE BIG GUY | 3v1 | `tdm` / Platform | 75 s | the 1 spawns in an Overdrive Rig (`server/rig.js`, a fresh rig every life). team kills, the 1's kills count x3 | code: rig at spawn, kill weight |
| 12 | BOSS: THE LANDLORD | 4 vs BOSS | `tdm` / Platform | 90 s | break his mech | code (4.4) |
| 13 | BOSS: THE NIGHT MANAGER | 4 vs BOSS | `tdm` / Platform | 90 s | break his mech | code (4.4) |
| 14 | **BUMPER CARTS** (custom) | FFA, 2v2, 1v1 | new `bgcarts` / Crate | 75 s | last cart on the box; else fewest falls | new |
| 15 | **DUCK CATCH** (custom) | FFA, 2v2, 1v1 | new `bgducks` / Platform | 60 s | most ducks caught (team total in 2v2) | new |

**Duel pool (1v1):** 1, 2, 3, 5, 6, 7, 14, 15. **The tiebreaker:** 2, first kill wins.

**Bots per minigame.** Rows 1-10 run on the bot AI those modes already have: `botThink` / `botGoal` in `server/room.js`,
`botChaosThink` / `botChaosFire` for the spoon and one-in-the-chamber kits, the lava hops, the gun game rungs, infection's
claw speed, and tags pickup in `botGoal`. Row 11 uses the rig's bot code in `server/rig.js`. In rows 12-13 the boss is a bot
piloting a hero mech through `mechBotStep` (`server/mech.js` plus the frame's `bot()`), and the four seats' bots play TDM against
it. Rows 14-15 need new bot code (below).

### 3.1 Custom 1: BUMPER CARTS (the shopping cart one)
Everyone starts **riding a shopping cart** (the Cart Cannon's ridden carts, `server/primaries.js` + `CART.ride`) on the
Crate, which floats in the sky. Ramming someone hard knocks them out of their cart and toward the edge. Off the edge is
"into the void" and you're out (respawning back into a cart in 2v2, team lives 3). Last cart standing wins.
- **Changes:** the ploughs deal no damage, knockback goes up a lot (`kb x 2.2`, `up x 0.6`), and you get a cart back on
  respawn. A cart you fall out of rolls on as a hazard. A BOOST on LMB (a 1.5 s cooldown burst, judged by the server like
  the ride's speed check).
- **Kill feed:** "returned to the store", "price checked into the void".
- **Bots:** new. Today "bots: no riding" (primaries.js). A bot driver aims at the nearest rival's position, adding a lead,
  boosts when lined up within 10 m, and steers back toward the middle when it gets near the edge. It reuses `navSteer`
  on Crate's open floor.
- **Fallback if bot riding is too costly:** every seat drives a **Trolley** hero mech instead (bots already drive it:
  `trBot` in `server/mech_trolley.js`). The catch is that mech size is a global knob (`JF_MECH_SCALE`), and a 4 m
  trolley on a 30 m box is a tight fit (open question 3).

### 3.2 Custom 2: DUCK CATCH
Rubber ducks rain onto the Platform deck. Duck Rain's drop schedule and the client's falling-shadow markers already exist
(`DUCKRAIN`, `tickDuckRain`). Here the ducks land as pickups, not black holes. Catch one in the air (+2) or pick it up
off the floor (+1). A **gold duck** is +5. Every 10 s one **cursed duck** lands as a real black hole, and anyone it pulls in
drops half their ducks.
- The only weapon is the Hand Slapper: a slap makes the target drop 3 ducks. No guns.
- **Bots:** the server knows where every duck will land, so a bot walks to the closest shadow it can reach in time (gold
  first), slaps any rival holding 5+ ducks within 3 m, and steers away from a cursed duck's shadow.
- Queued for later: ROOFTOP POOL CHICKEN (2v2 shoulder-ride wrestling in the rooftop pool. The mech and lasso "hold"
  code is a start).

## 4. Server design

### 4.1 Where it lives
- `shared/bgn.js` holds the rules and numbers (`BGN`), items, events, payouts and formats. `shared/bgnboard.js` holds the board graph:
  spaces `{ id, k, p: [x, z], next: [ids], plate? }`. `shared/bgnmini.js` holds the minigame table. The minigames' extra
  `GAMES` rows (`bgcarts`, `bgducks`, the boss rows) are added **without** pushing them to `GAME_ORDER`, so they never
  show up in quick play, the vote or the hub's game list (`inQuickPlay` and `gamesOf` both read `GAME_ORDER`).
- `server/bgn.js` is `installBgn(Room, H)`, the same pattern as `installLobby` / `installZombies`. `server/bgnbots.js` holds the board
  brain, which also covers AFK timeouts. `server/bgnmini.js` (PR 3) holds the custom minigames and the boss.
- The room is an ordinary `Room` of type `bots` (offline) or `ffa` (online lobby). It has to be: dozens of mode gates
  check `this.mode === 'ffa' || this.mode === 'bots'` (`chaosKit`, `lavaOn`, `livesOn`, `teamsOn`, `modeJoin`...).
  While the board is up, `room.game` is `bgn` (`GAMES.bgn = { name: 'Board Game Night', board: true }`), parked on Crate.

### 4.2 State shape (`room.bgn`)
```js
room.bgn = {
  ph: 'intro' | 'dibs' | 'turn' | 'move' | 'ask' | 'event' | 'duel' | 'mgintro' | 'mg' | 'mgres' | 'last' | 'tie' | 'cere' | 'done',
  round: 1, rounds: 10, last: null,            // last: the HOUSE RULE picked in LAST CALL
  seats: [{ i: 0, pid: 12, name: 'kevin', color: '#ff4fd8', bot: false, coupons: 10, bread: 0,
            at: 0, stuck: false, bag: ['peel'], lassoR: 0, stats: { duels: 0, spent: 0, mgWins: 0 } }, /* x4 */],
  order: [2, 0, 3, 1], turn: 0,                // seat indexes, whose turn
  bakery: 17, traps: Map<spaceId, { k: 'peel' | 'sign' | 'fake', by: seat, until: round }>,
  ask: { k: 'roll' | 'path' | 'bread' | 'shop' | 'stake' | 'who' | 'house', seat: 1, opts: [...], until: ms } | null,
  walk: { seat, left, path: [spaceIds] } | null,
  mg: { id: 'spoons', fmt: 'ffa' | '2v2' | '3v1' | 'boss' | 'duel', sides: [[0, 3], [1, 2]], teams: true,
        ends: ms, duel: { a, b, stake: 'coupons' | 'bread' }, boss: playerId } | null,
  hist: { fmt: ['ffa'], mg: ['dm', 'tags'], jank: 'tax' },
};
```
Seats are by **index**, never player id. A player id only says who sits there right now. Clients get a trimmed copy
(`bgnInfo()`), with no timers in the future and the full bags (it's a party game, bags are public).

### 4.3 Messages: client to server (choices only)
Every choice is one message type, `{ t: 'bg', k, ... }`, and goes to `onBgn(p, m)` from `handle()`. That covers `typeof m.k === 'string'`
and `has(K, m.k)`, plus a rate limit of 6 per second per player (`p.bgnT`, a list of times like `plp`). A message is only accepted when it's
**your seat's turn** (`seat.pid === p.id && ask.seat === seat.i`) and `ask.k` matches. Anything else is dropped without
an answer. Wrong-phase spam can't move anything.

| k | fields | checks |
|---|---|---|
| `roll` | none | `ask.k === 'roll'`. the value comes from the server |
| `use` | `it`, `to?` | before your roll only. `has(BGN.items, it)`, it's in your bag, one per turn. `to`: `Number.isInteger`, a seat 0-3 that isn't you (lasso, once a round), or a space id within range (sign: 1-6 ahead along the graph, fake bread: a COUPON space with no trap) |
| `path` | `i` | `Number.isInteger(i)`, `0 <= i < ask.opts.length` |
| `bread` | `yes` | `typeof yes === 'boolean'`, coupons >= price |
| `buy` | `it` (or `null` to leave) | `has(BGN.items, it)`, in this store's stock, coupons >= cost, bag < 3 |
| `stake` | `s` | `s === 'coupons'`, or `'bread'` when round >= 4, the target has a bread and you have 10 coupons |
| `who` | `seat` | an integer from `ask.opts` (two pawns on your space) |
| `house` | `i` | an integer index into the 3 house rules, last place only |
| `ok` | none | skip an intro or results card. every human `ok` = go now (like READY in `server/lobby.js`) |

During board phases, every fight message (`s`, `fire`, `hit`, `deploy`, `item`, `use`, `push`, `parry`, `spray`, `tbag`) is dropped,
and everyone is benched (4.5). The settings menu's `cfg` game and map changes are refused while `room.bgn` is set, and so is `/skip`.

Server to client: `{ t: 'bg', k: 'st', s: bgnInfo() }` on every phase change and join. Then small events: `roll`
`{ seat, v }`, `step` `{ seat, to }`, `cash` `{ seat, d, why }`, `bread` `{ seat, d, why }`, `trap`, `jank`
`{ e }`, `duel` `{ a, b, stake }`, `mg` `{ id, fmt, sides, ms }`, `res` `{ place, pay }`, `last`, `cere` `{ final }`.

### 4.4 Board to minigame and back (where it plugs in)
Every hook is a one-line addition in `server/room.js`. The work is done in `server/bgn.js`.

| hook (room.js) | added line | why |
|---|---|---|
| `tickRound()`, beside the `this.warm` early-out | `if (this.bgn && this.bgnTick(n)) return;` | the board runs its own clock while no minigame is on |
| `endRound()`, at the top | `if (this.bgn && this.bgn.mg) { this.bgnMgEnd(); return; }` | no end screen, perf, rolls or vote after a minigame: rank, pay, go back to the board |
| `startVote()`, at the top | `if (this.bgn) return;` | the same as the `hubBack` early-out |
| `teamsOn()` | `if (this.bgn && this.bgn.mg) return !!this.bgn.mg.teams;` | spoons 2v2, uneven 3v1 |
| `assignTeams()` / `joinTeam()` | `if (this.bgn && this.bgnTeams()) return;` | sides come from the board, not `teamPlan` |
| `fighters()` | filter `!p.bench` | benched seats don't count for limits, infection or the last one standing |
| `botWant()` | `if (this.bgn) return this.bgnBotWant();` | 4 seats (+1 while a boss is up) |
| `addHuman()` / `remove()` | `this.bgnJoin(p)` / `this.bgnLeave(p)` | the seat handover (4.5) |
| `handle()` | `case 'bg': this.onBgn(p, m); break;` | |
| `roundInfo()` | `if (this.bgn) r.bg = this.bgnInfo();` | late joiners and reconnects |
| `tickInfect()` | patient zero = `this.bgnOne()` when it's set | row 10 |
| `startModes()` | per-room ladder, `this.bgnLadder` before `rollLadder` | row 7 |

Starting a minigame is what `server/lobby.js` `startMatch` already does: `setGame(def.game)`, `cfg.map = mapForGame(...)`,
`broadcast({ t: 'cfg' })`, mark the bench, then `startRound()`. After that, `round.ends = now + def.time` and
`round.target = def.target` (the same override `enterWarm` makes). The minigame ends the usual way: a kill limit, the clock,
the last one standing (`tickLives`), the spoon kill (`ggKill`) or infection's side (`endInfect`). All of them call `endRound`, and the hook takes it from there.
`bgnMgEnd` ranks seats with the same sort `endRound` uses (`modeSort`, lives, team scores), pays out, then calls
`setGame('bgn')` and benches everyone again. Kills, deaths and medals still count toward account stats as in any match.

**The boss (rows 12-13):** `addBot()` adds THE LANDLORD (the Wrecking Ball frame) or THE NIGHT MANAGER (Night Shift) on
team 2. He spawns already inside his mech, using a new `mechSpawnIn(b, frame, hp)` helper that does `mechCall` + `mechLand` +
`mechEnter` with no fall, at armour x (2 + 0.5 per human seat). Damage is tallied per seat for the MVP. When his mech breaks
(`mechWreck`) the minigame ends. He's removed afterwards. `JF_MECH_HP` still scales him for tests.

### 4.5 Bench, disconnects and joins
- **Bench:** `p.bench = true; p.alive = false; p.respawnAt = Infinity` (the `JF_WATCH` observer's trick, but switchable).
  Everyone is benched on the board. The two non-duelists are benched in a duel and get the spectator cam (`specfp.js`).
- **A human leaves:** the seat keeps everything. A bot takes it at once (`addBot`, then `seat.pid = bot.id`,
  `seat.bot = true`) and is named after them ("kevin's bot"). Mid-minigame, the bot joins the same side and spawns in.
  Mid-choice, the ask timer is cut to 1 s and the bot brain answers.
- **A human joins** (online lobby, party ticket): between turns, they take the first bot seat. The bot retires
  (`retireBot`) and the seat's coupons, bread and bag are theirs. No rejoin-your-own-seat in v1 (queued).
- **Everyone leaves:** the room closes, as it does today (`remove()`, `rooms.delete`).

### 4.6 Test knobs (`JF_*`, read at the top of `server/bgn.js`)
| knob | does |
|---|---|
| `JF_BGN_ROUNDS=2` | rounds per game |
| `JF_BGN_FAST=10` | board timings / 10 (hops, cards, choice timers) |
| `JF_BGN_DIE=3,3,6` | the die rolls these, in order, then random |
| `JF_BGN_MG=spoons` / `JF_BGN_FMT=2v2` | force the next minigame / format |
| `JF_BGN_MGTIME=15` | minigame seconds |
| `JF_BGN_COUPONS=99` / `JF_BGN_PRICE=5` | starting coupons / bread price |
| `JF_BGN_ROUND=9` | start at round 9 (LAST CALL, the end) |
| `JF_BGN_BOTDUEL=1` | bot vs bot duels get played out |

Existing knobs still apply: `JF_WATCH` (a ws observer that runs a bots-only game), `JF_MECH_HP`, `JF_LIVES`, `JF_DUCKS`.

## 5. Client design
- **Files:** `public/js/bgn/` holds `scene.js` (the board, pawns, die, camera), `hud.js`, `shop.js`, `ceremony.js`. They load
  on the first `bg` message, the same way lobby scenes load.
- **The board scene** is drawn with the game's own renderer, the way `lobbyscenes/index.js` does it (no second WebGL context), so
  Potato to Too HD presets apply. While `bg.ph` isn't `mg`, main.js draws the board instead of the map, frees the pointer
  lock and shows the cursor.
- **The model:** `public/models/x_bgn_kitchen.glb`, from `tools/blender/bgn/make_kitchen.py`: the table, the fold-out
  board with printed spaces, the crease, the snack scenery, a lamp. Spaces are empties named `sp_00`...`sp_42`. The
  `jf` blob carries their positions so the code can check them against `shared/bgnboard.js`. It's visual only and
  falls back to a **code board** (boxes and cylinders from the space list in each space's colour) if the file is missing.
  Glossy bevelled look, candy-coloured spaces, crusty cardboard edges. The bakery and The Rules Guy are their own
  `x_bgn_*.glb` files.
- **Pawns:** mini mannequins (`buildCharacter`, scale about 0.22) in each player's look, with a random tilt and the wrong
  knee, hopping with a squash on every space. Bots get their bot outfits.
- **The die:** a foam d6 (`x_bgn_die.glb`, with a code cube as fallback) thrown from the active pawn's side. The client
  plays a tumble that ends on the server's face (pre-solved, so everyone sees the same face). A loud rattle and a THUNK.
- **Camera:** a table-height 3/4 view that follows the moving pawn, with a quick zoom-in on landings and duels, an
  overview at the start of each round, and a top-down view on Tab / M.
- **HUD (comic UI):** four seat cards in the corners, each a dark purple-black panel (`rgba(18,8,24,0.92)`) with a 4 px
  pink border, the seat's colour stripe, the name, the bread count with a bread icon, coupons, and the bag as item icons.
  The active seat gets the hard cyan `8px 8px 0` shadow. Top centre: `ROUND 4/10` (`LAST CALL` in red for the last 3).
  The ROLL button is the yellow `#ffe14d` main button, tilted a degree or two, with the pink offset shadow (Space / click).
  Choices (path, bread YES/NO, stake, who) use white buttons with black borders.
- **Shop UI:** a CORNER STORE panel with 3 item cards (white, black border, hard shadow, the item's icon, cost and its
  one-line joke). Ones you can't afford are greyed with "broke". LEAVE is a plain white button.
- **Callouts:** big ALL CAPS on the board: `+3 COUPONS`, `LATE FEE`, `JANK!`, `DUEL!`, `GOLDEN BREAD!`, `SLIPPED`,
  `MINIGAME TIME`, `EVERYONE VS THE LEADER`, `RENT IS DUE`, `HUNG JURY`, `LAST CALL`, `TOASTED`.
  Sounds are new `audio.js` synth recipes: die rattle, hop blip, coupon chime, a sad trombone for fees, a slap, a toaster pop.
- **Minigame cards:** the intro card shows the name, the format art (a red/blue split for 2v2, a big "1" for 3v1,
  the boss's silhouette), one rules line, controls and 3-2-1. The results card shows places and coupon changes ticking up.
- **Mobile (`touch.js`):** board phases are all taps. A big ROLL button bottom-right, fork arrows tappable on the
  board, shop cards full width. In portrait the camera pulls back. Minigames use the normal touch controls.

## 6. The hub
- **Tile:** `HUB.bgn = { name: 'BOARD GAME NIGHT', art: 'bgn', desc: 'roll the die, buy golden bread, minigames between turns', lobby: 'bgn', games: ['bgn'], tag: 'PARTY' }`.
  It's added to `ORDER` and `COL` in `public/js/hubmenu.js`, with mode art in `modeart.js`.
- **Offline:** `plan()` sends `['bots', { priv: true, game: 'bgn', hub: 'bgn', rounds, diff }]`. `roomFor` makes the
  private room, and `addHuman` sees `cfg.game === 'bgn'` and calls `bgnStart(rounds)`. The settings are ROUNDS (5 / 10 / 15)
  and BOT DIFFICULTY. Add `'bgn'` to `HUB_BACK` so the end screen offers PLAY AGAIN / LOBBY.
- **Online:** a new lobby kind in `shared/lobby.js`:
  `bgn: { name: 'BOARD GAME NIGHT', game: 'bgn', min: 1, cap: 4, squad: 4, desc: '...' }`. It's like zombies: 4 seats,
  people take bots' places, a 60 s countdown. `startMatch()` calls `bgnStart()` instead of a normal round when the
  lobby kind is `bgn`.
- **Parties:** add `'bgn'` to `MODES` / `MODE_NAMES` in `server/party.js`. `go()` already refuses a party bigger than the
  kind's `cap` ("board game night takes 4. there are 5 of you"), and tickets land the whole party in one room.
- **Lobby scene:** the hangar to start (`lobbyscenes/index.js` `FILES.bgn = 'hangar'`). PR 4 replaces it with the
  kitchen at night, the board on the table, and the party standing around it.

## 7. PR plan

| PR | what | its tests prove |
|---|---|---|
| **2. Board loop + bots + existing modes** | `shared/bgn*.js`, `server/bgn.js` + `bgnbots.js`, the room.js hooks, the bench, the seat handover, the lobby kind, the hub tile, the code board, HUD, die, shop, callouts. Minigames 1-10 (config rows plus the small code for oitc lives, the short ladder and patient zero) and duels | ws script `t_bgn_loop.cjs` (bots-only, `JF_WATCH`, `JF_BGN_FAST`, `JF_BGN_ROUNDS=3`): it plays a whole game through every phase and ends with a winner. Coupons are conserved in duels. Each format's sides and payouts are right. Every validation drops bad input: the wrong seat, wrong phase, `NaN`, `'__proto__'` items, out-of-range path, roll spam. A human leaving mid-turn and mid-minigame hands the seat to a bot with the same coupons, bread and bag. Minigames 1-10 each start and end on their map (`JF_BGN_MG`). Playwright: screenshots of the board, shop and a minigame intro at Too HD. `regress2.sh` stays green against main |
| **3. Boss + custom minigames** | `server/bgnmini.js`: THE BIG GUY, the two bosses (`mechSpawnIn`), BUMPER CARTS (with bot cart drivers), DUCK CATCH | ws tests: the boss spawns in his mech with the right armour, and both ends happen (a boss break pays the MVP, the timer pays the pity). Bumper carts: a ram knocks a rider into the void, the last cart wins, and bots stay on the box for 60 s when nobody hits them. Duck catch: catches are judged by the server (no catching from 5 m away), slaps drop ducks, and a cursed duck halves the pile. HD clips of each |
| **4. Blender board + ceremony** | `x_bgn_kitchen.glb`, the die, the bakery, The Rules Guy, the toaster podium, THE TOASTING, the kitchen lobby scene | asset QA sheets (`blender-asset-qa`). The fallback still loads with the .glb removed. Screenshots of every space type and the camera at each preset. A clip of a full LAST CALL round into The Toasting |

## 8. Open questions for the owner
1. **Names:** BOARD GAME NIGHT, COUPONS, GOLDEN BREAD, THE KITCHEN TABLE, THE RULES GUY, THE TOASTING. *Default: these.*
2. **Length:** 10 rounds is about 25-30 minutes. *Default: offer 5 / 10 / 15, with 10 picked.*
3. **Bumper Carts:** player-sized shopping carts (funnier, but bots need new driving code) or Trolley mechs (bots
   already drive them, but they're big on a small map)? *Default: player-sized carts, with Trolley mechs as the fallback.*
4. **Bread duels:** can a duel take a golden bread? *Default: yes, from round 4, and it costs the lander 10 coupons to try.*
5. **Online:** public matchmaking (strangers, 4 max, bots fill) or friends and parties only? *Default: both, through the
   lobby kind.*

## Hard parts in the code (known up front)
- **Mode gates are keyed on the room type.** That's fine because a board room is `bots` / `ffa`. But the vote, `/skip`, the
  settings menu and `hubBack` all assume one match follows another, so each one needs a `bgn` early-out.
- **Teams are all or nothing.** `teamsOn()` reads `GAMES[g].teams`, and `assignTeams` only keeps parties together
  (`teamPlan`). Spoons 2v2, 3v1 and boss sides need the override hook.
- **Nobody can sit out today.** Only the `JF_WATCH` test observer and one-in-the-chamber's "out" exist. A real bench has to keep out
  of `fighters()`, respawns, bot targeting, the kill limit and Never Landed (`airStart`).
- **`endRound` does everything at once**: the end screen, `perf`, container rolls, the `wins` stat, the vote. Minigames need it
  skipped completely, but kill and medal stats should keep working.
- **Global knobs that need to be per room:** `GAMES.oitc.lives`, the ladder (`GG_FIXED` env only), `TARGETS`, `ROUND` times,
  and the mech scale (`mechScale` is server-wide).
- **Infection picks patient zero at random** in `tickInfect`, so the 3v1 needs a hook.
- **Bots can't ride carts** (`primaries.js`: "bots: no riding"), and riding is client-authoritative for humans, so cart
  sumo needs new bot code plus a fair server check on the boost.
- **Every minigame reloads a map** on the client (`loadMap` on `cfg`). Keeping it to Crate, Platform and Rooftop keeps that
  quick, and the bots' walk graphs are warmed per map the first time (`warmMap`).
- **`p.party` is taken** (it's the party system's id string), so the board state is `room.bgn` / `p.bench`, never "party".
