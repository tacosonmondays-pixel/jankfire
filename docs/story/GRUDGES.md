# OVERDUE: the Grudge Ledger

_Enemies who remember you. This is a design doc for the owner to approve before the systems lane builds anything. The data is in
`shared/story/content/grudges.js`. The full catalogue (33 adaptations, 33 triggers, 280 barks and the recap cards) is generated into
[GRUDGE_LEDGER.md](GRUDGE_LEDGER.md)._

## The pitch

Ordinary, nameless enemies (an Unpaid raider, a Punctuality Officer, a Collections repo man, a Gut Choir singer, a Family goon) can
get an **HR file** on you. A file opens when something memorable happens between you and one of them: they kill you, you run from
them, they survive you, or you do something stupid to them (run them over, slip them on marbles, set them on fire) and they live.

Later they **come back**, in the district where it happened, and they **remember**. A comic-panel card pops up (**PREVIOUSLY
BETWEEN YOU TWO**), they say a line about exactly what you did, and they're **wearing the consequences**: a neck brace with tyre
marks, shoes glued to the floor, head-to-toe bandages. Every adaptation is a physical gag on the model that changes **one**
behaviour and comes with **one** counter-trick that beats it. A neck brace means they dodge cars, but they can't look up, so you
attack from a roof.

Then you end it your way: **case closed** (beat them with their own counter), **they quit** (humiliate them until they hand in their
notice and get a desk job), or **reluctant ally** (spare them and they help you once and give you a small favour quest).

## How it plays (the rules)

1. **Opening a file.** A trigger (the [trigger list](GRUDGE_LEDGER.md#triggers)) happens with an enemy from one of the 5 grudge
   factions. The triggers marked "opens a file" have a 35% chance to promote a nameless enemy into a named one: they get a first name
   from their faction's pool, a seed (for their mannequin tilt, colours and voice pitch), and the district. **Killing you always opens a
   file.** Never more than 12 open files.
2. **Adding to a file.** Any trigger with someone who already has a file adds a history entry (max 4, oldest drops) and gives them
   that trigger's adaptation (max 3 on the model; a 4th replaces the oldest). Adaptations don't stack into anything bigger. They're
   just more stuff on the model, each with its own counter.
3. **Coming back.** After 240 s of play in a file's district, there's a 30% chance per check that they turn up in the next ordinary
   fight there. That's never during a story mission (unless the mission says so) and only one grudge enemy per fight. They get an intro
   bark (`spotted`), a name tag (`KEV · INTERN · "NECK BRACE"`), and the first time back, the recap card.
4. **The meeting.** It's a normal fight with one more enemy, wearing their adaptations. Each adaptation changes one thing and
   shows its counter visually (the hat is shootable, the wok has a dent, the anchor chain is on the floor). They bark on the
   [bark keys](GRUDGE_LEDGER.md#barks-280-lines) as things happen.
5. **After the meeting** something gets written to the file:
   - kill them normally → they **survive it** (stretchered off, a little bandage); the file stays open with a `survived` entry. Up to
     the third meeting, a normal kill doesn't close the file. That's how they keep coming back without needing a hierarchy.
   - kill them **using their counter** (any meeting) → **CASE CLOSED**.
   - **3 different humiliations in one meeting** without killing them → **THEY QUIT**.
   - from the third meeting on, when they go down you get **F: help them up** → **RELUCTANT ALLY**. Or you finish them, which
     closes the file.
6. **Going cold.** 7 in-game days without a meeting and the file closes itself. If the ledger is full, the least-recently-seen file is
   **transferred** out to make room for the new one. You don't lose anything; it just leaves the active list.

The pace target is 1-3 files open by the end of Act 1, around 6-10 at peak, and a returning grudge maybe once every 15-20 minutes of
free roam. It's a running gag, not a grind.

## Resolutions (how a file ends)

| ending | how | what you get | what you see after |
|---|---|---|---|
| **CASE CLOSED** | finish them with their own counter (shoot the hat off, GONG the wok, light the fire they fear) | their adaptation as a junk trophy item (sell it, or keep it in the Locker), your stolen cosmetic back, their Coupons | a red CLOSED stamp on the file |
| **THEY QUIT** | 3 different humiliations in one meeting (slip, then fling, then bubble...) without killing | a nice `quit` line and a 10% discount wherever they end up | they turn up at a desk job: a Late Desk clerk, a Lost & Found volunteer, a Returns Desk trainee, a Pinstripe café owner. They say hi |
| **RELUCTANT ALLY** | spare them at the end of their third meeting (F: help them up) | they show up once to help in a fight in their district (`ally` barks), then give you a one-step **grudge favour** (deliver a letter to their mum, get their thing back from another grudge) | SETTLED stamp |
| GONE COLD | 7 in-game days with no meeting | nothing | a line in the ledger: "kev has moved on. kev is doing pilates." |
| TRANSFERRED | the ledger is full and a new file opens | nothing | the file moves to the archive drawer |

## Ties into the rest of OVERDUE (kept simple)

- **Late Fees.** Timekeeping (★1-★2) and Collections (★3) are grudge factions. When you get Late Fees, an officer or collector
  with an open file on you is **first to respond** if they're in the district. Losing your stars while they were chasing you counts
  as `you_fled`, which is where the stopwatch comes from.
- **Coupons.** When a grudge enemy kills you, they take the **restocking fee** (the Coupons you lose at the terminal) and keep it in
  their file. You get it back when the file closes (any resolution except cold or transferred).
- **Implants.** Some triggers only exist with implants: biting someone with the **Bear Trap Jaw** (chainmail scarf), your
  **Second Stomach** burp giving you away (nose peg), and someone hearing your **Cracked Punch-Clock** tick (earmuffs).
- **Employee 4417.** In its secret fight (`prototype`, the Lates warehouse), 4417 has read your files. Its intro mentions your
  oldest open grudge by name, and in phase 2 that grudge enemy turns up as an add, still wearing everything. If you'd closed every
  file, 4417 is annoyed instead: "you've been very thorough. i respect that. i've got nobody to bring."
- **Cosmetic trophies.** When a grudge enemy kills you, they wear a copy of one cosmetic you have equipped (hat first, then
  glasses, then a back item). If you have none, they take your lanyard photo. Shooting it off makes them chase it, and you get it back.

## Co-op: shared grudges

- A file belongs to the **party that was there**. Every player present when it opened (or is added to) gets the file in their own
  story save. The file lists them all, and the recap says who did what ("Kev remembers all of you. Sam especially.", using the
  `coop` card).
- A grudge enemy spawns if **any** player in the session has their file open, and the host's district timer decides when.
- Resolutions apply to everyone present. Someone who wasn't there keeps their copy open, and their Kev is still mad at them.
- Cosmetic trophies take from whoever got killed. The server validates it: it only copies a cosmetic that player actually owns.

## UI: the Ledger

- **The Ledger** is a tab in the story pause menu. It's a beige filing cabinet drawer in the comic style: dark panel, pink border,
  cyan offset shadow. Each grudge is a **manila folder** with a polaroid of them (their current look, rendered on open), their name
  and tag, the district, how many times you've met, and their adaptations as little stickers. The folders are **flat** and sorted by
  last seen. There's nothing above or below anyone.
- Closed files get a big rubber stamp: CLOSED (red), RESIGNED (yellow), SETTLED (green), COLD (grey). They go in an "archive" drawer
  you can flip through.
- In the world, a grudge enemy has a little **paperclipped folder** icon over their head instead of a normal enemy marker, plus their
  name and epithet.
- **The recap card** uses the existing `recap` scene type: 3 comic panels, captions from [the recap
  templates](GRUDGE_LEDGER.md#recap-cards), 2 seconds, skippable, and only once per grudge per session.

## The data (for the systems lane)

`shared/story/content/grudges.js` exports plain data. The schema is at the top of the file. Summary:

- `GRUDGE_RULES`: all the numbers above.
- `GRUDGE_FACTIONS[id]`: `{ name, tag, who, districts, names, voice }`.
- `GRUDGE_TRIGGERS[id]`: `{ name, when, weapons?, adaptation, opens }`.
- `ADAPTATIONS[id]`: `{ from, name, title, look, effect, counter }`.
- `RESOLUTIONS`, `RECAPS` (with the fields in `RECAP_FIELDS`), `BARKS[faction][key]` (keys in `BARK_KEYS`). A trigger with no bark key
  of its own falls back to `survived`.

### Save shape

Everything lives in the story save under one cleaned part (`savePart('grudges', fn)`), capped at 3 KB. One file:

```js
{ id: 'g7',            // short id, unique per save
  fac: 'unpaid',       // GRUDGE_FACTIONS id
  seed: 48213,         // looks + voice pitch + which name (names are picked from the pool by seed, not stored)
  d: 'commute',        // district it lives in
  born: 3,             // in-game day it opened
  seen: 5,             // in-game day of the last meeting
  n: 2,                // meetings so far
  hist: [['run_over', 3], ['killed_you', 5]],   // ≤4 [trigger, day]
  ad: ['neck_brace', 'your_hat'],               // ≤3 adaptation ids
  troph: 'hat_bucket',  // the cosmetic id they took, or null
  fee: 120,            // Coupons they're holding
  by: ['p1'],          // co-op: which party slots were there (just 'p1' solo)
  st: 'open' }         // open | closed | quit | ally | cold | moved
```

Closed files are squashed to `{ id, fac, seed, st, n }` and the oldest closed files drop off after 24, so the archive stays small.
The cleaner rejects unknown faction, trigger or adaptation ids, clamps numbers, and truncates the arrays. 12 open files plus 24
closed ones comes to about 2.5 KB of JSON.

### Hooks the engine needs (not built yet)

- `grudge.event(enemy, trigger, players)` is called by combat on each trigger. It rolls to open a file, or appends to an existing one.
- `grudge.tick(district, dt)` runs the spawn timer and picks a file, then hands the encounter spawner one enemy id plus the
  adaptation list.
- Adaptations are **flags on the enemy** (`noJump`, `fearFire`, `noLookUp`, `catchFrags`...) plus a model attachment. Each counter
  is a hit/condition check that the server already validates (fire hit, melee on the head, cosmetic hitbox shot). No new stats.
- The server owns the file, like HP and kills, and the client only renders it. Triggers are detected server-side from real hits,
  so nobody can fake a CASE CLOSED.

## How it stays its own design

WB holds a patent on the "Nemesis System" from Shadow of Mordor / Shadow of War. **This doc is not legal advice; please have a lawyer
look at it before any commercial release.** We built the Grudge Ledger to be clearly different in structure and presentation:

| the patented-style system has... | the Grudge Ledger instead... |
|---|---|
| an **army power hierarchy**: enemies hold ranks/tiers, get promoted, fight over positions | has **no ranks, tiers, levels or promotion**. Every file is a flat, one-to-one record between you and one person. Nobody is above or below anyone |
| enemies **gaining power** and becoming stronger the more they win | adaptations are **sideways, not up**: each is a single physical gag that swaps one behaviour for one weakness. Three adaptations is three gags, not a stronger enemy |
| enemy-vs-enemy **power struggles**, duels, successions, captains/warchiefs/forts | has **none**. Grudge enemies don't interact with each other, don't climb anything, and don't hold territory. They're just in a district, the way a neighbour is |
| **followers, domination, recruiting, betrayal** | has **no army and no recruiting**. The ally ending is **one** favour and **one** helping hand, then it's over. Nobody betrays anybody |
| a hierarchy screen of portraits arranged in tiers | uses a **flat filing cabinet** of manila folders sorted by date, with rubber stamps (an office/HR joke that fits OVERDUE) |
| enemies remembering you as a vehicle for power growth | is built around **memory as comedy**: recap card, a specific bark, a visible physical consequence, and a trick to beat it |
| permanent enemy death or "cheating death" as a core loop | they survive by being **stretchered off** (a joke), only up to the third meeting, and then they **quit**, **ally** or are **closed** |

We'll keep it this way: if someone wants to add ranks, promotions, enemy power struggles or an army later, that needs the owner (and
ideally a lawyer) first.

## Three grudge stories (for the owner)

### 1. Kev and the sofa

_Act 1, the Commute._ You've just "borrowed" the sofa-car. An Unpaid raider steps out from behind a bus and you hit him at 80. He
bounces off the windscreen, cartwheels over a barrier, and is still alive. The file opens: **KEV · INTERN**.

Twenty minutes later you're back on the Commute shooting your way through a raider camp. The screen goes comic: **PREVIOUSLY BETWEEN
YOU TWO**. Panel 1 is a sofa doing 80. Panel 2 is Kev in the air. Panel 3 is Kev now, in **a big foam neck brace with tyre marks on
it**. "you ran me over with a SOFA." You go for the car again. Kev hears the engine, dives sideways like he's practised it (he has),
and shoots your tyres out. Then you notice he can't look up. You grapple onto the bus shelter roof and drop on him from above.
He goes down, stretchered off by two other interns. "this isn't over. i'm resilient. it's a soft skill."

Third meeting: Kev has the brace and **glued shoes** (you marbled him last time). He can't jump either. You wait on a ledge until
he walks under it, then blow him off a railway bridge with the Leaf Blower. He can't slip any more, but he can fly. You catch him in a soap
bubble on the way down and snap a photo of him floating over the tracks. That's three different humiliations (flung, bubbled, photographed). **KEV QUITS.** A week later he's at the Late Desk in a cardigan. "i've taken a job
at the late desk. it's paid. i didn't know you could be paid."

### 2. Officer Tick wants your hat

_Act 2, Corp Hill._ ★2 Late Fees. A Punctuality Officer clips you in an alley and you're dispensed back at a terminal. She takes your
restocking fee and a copy of your **bucket hat**. File: **OFFICER TICK · OFFICER · "HAT THIEF"**.

Every time you get stars in Corp Hill now, Tick is first on the scene, wearing your hat over her cap. "evidence locker. your hat. my
head." You run again (that's the stopwatch: she times you out loud, "nineteen seconds. noted."). Third meeting: you spot the hat,
shoot it off, and she drops everything to chase it across the plaza. You finish her while she's bent over picking it up. **CASE
CLOSED.** The hat's back in your wardrobe, you get your Coupons back, and the stopwatch goes in your Locker as a trophy.

### 3. Brother Bile and the fire (and the help)

_Act 3, the Gut._ You light a Choir singer up with the Cigarette in a gas vent room. He runs off screaming, still alive. File:
**BROTHER BILE · CHORISTER**. He comes back **in bandages, eyebrows drawn on in marker**, and terrified of fire. "*sung* i saw
fire..." He shoots every candle in the room. The counter's easy: light anything and he runs in a straight line. But you're
doing a stealth bit, so you don't. You knock him out with the Bread instead.

Third meeting, in the Choir's hall. He's down, and the prompt comes up: **F: help them up**. You do. "*sung* this once, this
once..." Two fights later, a Gristle & Sons patrol has you pinned in a lung corridor, and Brother Bile walks in singing, bandages
flapping. "*not sung* go left. the walls are hungry on the right." Then he gives you a favour: take his letter to his mum at the
tooth market. **SETTLED.**

_(Employee 4417, much later: "i've read your files. brother bile says hello. no, he doesn't. i brought officer tick.")_

## Questions for the owner

1. Is a 35% chance to open a file on a nameless enemy right, or should it be rarer (special) or more common (chaos)?
2. Should killing you take a cosmetic copy every time, or only the first time per file?
3. Should grudges be in the normal multiplayer modes too (bots remembering you), or only in OVERDUE? This doc assumes OVERDUE only.
