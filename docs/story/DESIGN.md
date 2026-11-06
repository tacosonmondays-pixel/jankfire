# JANKFIRE: OVERDUE (story mode design doc)

> **Logline:** the world ended on the last day of the last quarter, when every division of ☺ CORP tried to hit its
> numbers at once. Years later (nobody knows how many, time is broken) the companies that ended it are still open for
> business in the ruins, and every gang of survivors wants a piece of what's left. You're a mannequin the old ☺ vending
> machine finally spat out: the first change it ever gave. Everything you know, you learned in its training sims.

Working title **OVERDUE**. On the home screen it's the new **STORY** button. Everything here is original: genre ideas
(a post-apocalyptic open city, crime-sandbox driving, rarity loot, cyber implants) are borrowed, and no names,
characters, maps or art are.

Companion docs: [ART_BIBLE.md](ART_BIBLE.md) · [TECH_PLAN.md](TECH_PLAN.md) · [SLICE_PLAN.md](SLICE_PLAN.md)

---

## 1. The world and its rules

**Greater Jankburg** is the walled corporate city from the battle royale (`shared/jankburg.js`), after the end of the
world. Ten districts are left on a giant hill of rubble: Corp Hill at the top, The Bottom at the bottom, because in this
city the org chart was always a map. Between them runs **The Commute**: jammed dead highways, paper storms (blizzards of
shredded paperwork) and raiders.

### Before: the merger (what the sims remember)
Everything players already know from the lore NPCs (`shared/secrets.js`) is the world *before*: ☺ CORP started as one
vending machine that never gave change, bought the government at an auction, merged with everyone, and made matches
the job ("kills are the only honest KPI"). The founder is a cat who typed `yyyyyyyyyyyy`. Todd wrote gravity from
memory. That world is gone. It lives on only as recordings inside the Machine's training sims (below).

### The Final Quarter (the apocalypse)
After the merger, every company on earth was a **division** of ☺ CORP, and every division had a target for the end of
Q4. On the last afternoon of the last quarter, all of them shipped whatever would hit the number. The world ended by
about 17:30.

| division (now its own company again) | what it shipped on the last day | what it did to the world |
|---|---|---|
| **☺ CORP Time & Scheduling** | overclocked **the Schedule** to fit more billable hours into the quarter | **time cracked.** every district runs on its own broken clock, and anything that falls behind rots into meat |
| **Gristle & Sons Biologics** | the "grow your own lunch" formula, three months early | a whole district grew alive: **The Gut**. it's still growing |
| **Big Value Retail** | the biggest sale in history, every door opened at once | **the Stampede** flattened half the city. the sale never ended |
| **Remainder Industries** (the number printers) | enough numbers to make every book balance | inflation went physical: **giant digits fell from the sky** and they're still half-buried everywhere |
| **Vacancy Holdings** (real estate) | repossessed everything with a late payment, including the ground | **the void**: the edges of the world were sold off as "premium negative space" |
| **Fazzoletti Family Insurance** | apocalypse cover, sold to everyone that morning | paid out nothing ("act of shareholders") and got very rich |

Then the merger fell apart: **THE DEMERGER**. Each division walked off with its slice of the city and became its own
company again. The board of directors (the cats) vanished. Nobody was left in charge except whoever had a building and
a logo.

### Now
- **The companies are still open.** Each one runs its district like the end of the world was a slow quarter: shops,
  security, slogans, prices. They're the reason the world ended, and they're the only ones with power, water and
  ammo. They fight each other for turf, and they all want to be the one that rebuilds the economy (and owns it).
- **☺ CORP wants the Re-Merger.** It still runs Corp Hill perfectly ON TIME, holds meetings in the ruins and sends
  **Late Fees** to survivors for "back pay owed since the Final Quarter". Its plan is to restart the **Master Clock** at
  the top of the ☺ Spire, put the whole city back on the Schedule and sign everyone back up as employees. By force.
- **Lateness rots reality.** Since the Final Quarter, anything that falls behind schedule goes *overdue*: first it gets
  sticky, then warm, then it gets a pulse. Overdue paperwork grows teeth. Overdue streets grow intestines. The ruins
  are slowly turning into meat from the bottom of the hill up.
- **Smaller groups want up.** Survivor towns, raider gangs, feral mascots, a gated suburb with a militia, scavenger
  surgeons: everyone without a logo is fighting to become the next one, or to make sure nobody does. The biggest of
  them is **The Bottom**.

### The Machine and the training sims (the PvP is in here)
- The original ☺ vending machine, the one that started it all, survived the Final Quarter. Nothing can kill it. It
  stands in the ruins of the Lost & Found at the Bottom, still humming, still not giving change.
- Inside it runs the **TRAINING SIMS**: recordings of the world from before the end. **Every multiplayer map and mode
  in JANKFIRE is a sim.** Dead Mall, Suburb, the Warehouse, the Desert, Jankburg's battle royale, Gun Game, Plant &
  Defuse: all simulations of places and jobs that don't exist anymore.
- That explains the jank in the PvP: respawning is free (it's a sim), Todd's broken gravity (it was recorded that way),
  the bots (recorded employees), and the containers that pay out (the Machine dispenses them into its tray). The lore
  NPCs you meet in the sims (Gary, Dale, the Janitor, Mr. Smiles, Todd) are **recordings who don't know the world
  ended**. In story mode you can find what's left of the real ones.
- The companies and gangs buy sim time to train their fighters, which is why every faction fights like a JANKFIRE
  player. The Bottom uses it to train its own.
- **In story mode, the Machine is the multiplayer menu.** Walk up to one of its terminals at a safehouse, press F, and
  you're in the normal PLAY menu: your sim results come back as containers in the tray.

### Change (the player)
- At the start of the story the Machine goes BEEP, then CLUNK, and drops a mannequin into its tray: you. Sim-trained,
  never scheduled, no receipt. The Bottom's people take one look and name you **CHANGE**: "the machine never gave
  change. then it gave you."
- Legally you don't exist (no calendar entry), so ☺ CORP's laws don't quite apply to you. You can respawn (a backup
  copy is in the Machine: die and it dispenses you again at the nearest terminal, minus a "restocking fee"), install
  organs that aren't yours, and stand in overdue places without rotting (much).
- Why did the Machine dispense you? That's the last mystery of the story (Act V).

### Rules of the world (gameplay-facing)
| rule | what the player feels |
|---|---|
| Time is broken | every district has its own **district clock** in the HUD, running at its own speed. Corp Hill is perfectly on time (shops open, patrols on rounds, trains on time); the Lates is stuck on Tuesday; the Gut doesn't care. |
| Lateness rots | overdue zones are fleshy, hostile and lucrative. The Gut is permanently overdue; other districts rot at night and when you cause chaos. |
| The companies own the turf | every district has a ruler. You can keep it in power or hand it to a smaller group (**Hostile Takeovers**, §6.11). |
| Momentum never ends (Todd) | all existing movement (bhop, slide, grapple, infinite momentum) works city-wide. Cars keep it too. |
| Respawning is a backup | death = the Machine dispenses a fresh you at the nearest terminal, minus some Coupons. |
| Money is coupons | after the Stampede, Big Value's coupons were the only thing that never expired. **Coupons** are the currency now. |
| The board are cats | the cats are hidden across the ruins. Petting them = promotions (perk points). |

---

## 2. Factions

### The companies that ended the world (and are still open)
| company | turf | wants | flavour |
|---|---|---|---|
| **☺ CORP** | Corp Hill and the ☺ Spire | the **Re-Merger**: restart the Master Clock and own everyone again | smiling, punctual, plastic, in total denial. "business as usual." |
| **Gristle & Sons Biologics** | The Gut | **organic growth**: grow the Gut over the whole city | the staff stayed at their desks while the building grew around them, and became the **Gut Choir**. The CEO is the Stomach Bishop. |
| **Big Value Retail** | The Checkout | keep the sale going forever; everyone a customer | Mall Security on segways, the **Forever Shoppers**, coupons as money |
| **Fazzoletti Family Insurance** | Pinstripe | protection money from everyone, including the other companies | "a family business since 1850." you're covered. you're always covered. |
| **Remainder Industries** | Number Works | to decide what everything costs | they print the prices. whoever prints the prices runs the market |
| **Vacancy Holdings** | The Margins | to sell what's left of the ground, plot by plot, to the void | estate agents in hazmat suits; they rent the Tall Guy From HR from ☺ CORP |

☺ CORP's departments the player meets: **Timekeeping Enforcement** (cops, collectors, Mr. Overtime), **HR** (special
forces, the Tall Guy From HR), **Facilities** (cleaners who scrub the meat back to plastic with bleach cannons) and
**Marketing** (a new mascot that's 90% mouth).

### The groups grabbing for power
| group | where | wants | attitude to you |
|---|---|---|---|
| **The Bottom** | The Bottom (rebel hub) | to get **up** the hill: a city where nobody owns time | home; they found you |
| **The Unpaid** | The Commute | to become a company ("we're doing a startup"). Raiders: interns who survived because nobody had counted them, in armour made of office chairs and filing cabinets. They worship Todd as the First Intern. Led by **EMPLOYEE OF THE MONTH**, a warlord who gave himself the award. | they rob you, then offer you an internship |
| **The Fun Department** | roaming (a carnival convoy on The Commute) | fun, mandatory. Feral ex-Marketing mascots in matted suits. Mr. Smiles quit them | they want you to have fun. they will make you |
| **The Punchlines** | Pinstripe | to take the Family over. The Don's two jesters, Pip Grinsworth and Long Larry, and every clown he ever laughed at | allies, if you laugh |
| **The Mall Rats** | The Checkout | to end the sale. Kids who grew up in the mall's air vents after the Stampede (they're 30 now) | allies, sneaky |
| **The Remainders** | Number Works | to be counted. A union of people stamped with the digits nobody wanted | grumpy allies |
| **The Meat Mechanics** | Chrome Gristle | the monopoly on organs, scavenged from the Gut | merchants (implant clinics) |
| **The HOA** | Evergreen Acres | to annex the ruins "for property values". A gated suburb that survived by refusing to admit anything happened, with an armed militia | passive-aggressive, then aggressive |
| **The Loopers** | The Lates | for it to stop being Tuesday | confused, helpful |
| **The Margin Walkers** | The Margins | to keep the void from eating more ground; they stake plots with garden gnomes | lonely, grateful |

**The Bottom's leaders:**
- **Auntie Spreadsheet**, ex-accountant, runs the Lost & Found settlement and keeps the Bottom's books in crayon. She
  was in the Final Quarter's last meeting. She doesn't talk about it.
- **Lumps**, a huge rubber-faced man with enormous veiny forearms and a lot of gold rings, the Bottom's muscle. Gentle.
  Cries at sunsets. The Bottom's clock is broken, so the sunset comes at a random time every day and he's never ready.
- **Wee Gordo**, small, hunched, sagging lipped face, spiky hair, pink sweater. Lumps' best friend and the actual brains.
- **Dale** (the real one, older, still fixing the Machine). He's the only one who's ever looked inside it.

---

## 3. The main story

Five acts, ~25 main missions, each one an excuse for set pieces. Your choices tilt **Corp Standing** and **Bottom
Standing** (two hidden meters) and decide who runs each district (**turf**), which picks your allies in Act IV and the
ending in Act V.

### Act I: "Please Take Your Item" (The Bottom, The Gut)
1. **Please Take Your Item.** You're in a sim match (it looks exactly like normal JANKFIRE PvP: HUD, kill feed, the
   lot). You win. "TRAINING COMPLETE." The world freezes and the camera pulls out through the Machine's glass into the
   ruins: the match was inside it. CLUNK. You drop into the tray. Auntie Spreadsheet and Dale stare at you. Tutorial in
   the Lost & Found: Bread, movement, the grapple on the washing lines.
2. **Sauce Run.** Gristle & Sons trades medicine for soup. Lumps needs a car. Steal one (car basics), and drive the soup
   across the edge of The Commute to the Gut border while **The Unpaid** raid you.
3. **Something's Digesting.** In the Gut you meet the Choir (Gristle & Sons' old staff) and find out ☺ CORP is
   **selling them late people** as feedstock, in exchange for meat-power for the Master Clock.
4. **Clocking In.** ☺ CORP sends **Mr. Overtime** to collect forty quarters of back pay from the Bottom. First nemesis
   fight (see §5) on the Gut border. You crack his punch-clock heart, he retreats, a piece of it falls out: your first
   **organ core**. ("THAT'S A HEART. YOU CAN'T JUST HAVE A HEART." "watch me.")
5. **Second Stomach.** A Meat Mechanic installs the core. Implants unlocked. The Bottom now believes you're useful.

### Act II: "Hostile Takeovers" (Pinstripe, The Checkout, Number Works)
To climb the hill, the Bottom needs allies, coupons and roads. Three company districts, in any order. In each one you
either **make a deal** with the company (it stays in power, owes you, and is a shaky ally) or run a **takeover** with
the district's smaller group (they take over the district and become a loyal ally, the company becomes an enemy).
- **Pinstripe:** the Fazzoletti Family will fund the Bottom if you collect protection money... from ☺ CORP. Or help the
  Punchlines take the Family over. Either way it ends with **Don Grinaldi** (deal: he betrays you at the handshake;
  takeover: you cut his strings).
- **The Checkout:** Big Value is holding some of the Bottom's people in the Infinite Queue. Get them out by buying out
  their debt (deal) or by helping the Mall Rats end the sale (takeover). Boss: **The Cart Mother**.
- **Number Works:** steal the old Schedule printout (9 km of paper, the city's whole timetable from before the end).
  Deal with Remainder Industries, or let the Remainders union seize the presses. Boss: **Foreman Remainder**.
- Mid-act: Mr. Overtime ambushes you on The Commute (second nemesis fight, a car chase), and the Unpaid join the chase
  to rob whoever loses.

### Act III: "Off the Clock" (Chrome Gristle, Evergreen Acres, The Lates)
With the printout, Wee Gordo finds a hole: there's an hour on the Schedule that nobody is booked into, the **Missing
Hour** at 03:00. The Bottom plans to sneak up the hill during it. You recruit (or take over) the Meat Mechanics in
Chrome Gristle, break the HOA's blockade in Evergreen Acres, and go to **The Lates**, where the Schedule first cracked
and it's been Tuesday ever since.
- **The twist:** the Final Quarter **wasn't an accident**. ☺ CORP crashed the world on purpose. It was a
  *restructuring*: by going bankrupt at the end of Q4, ☺ CORP cancelled every wage, debt and pension it owed. Auntie
  Spreadsheet was in the meeting where they signed it off. She took minutes.
- The Missing Hour is where ☺ CORP keeps everything it needs for the **Re-Merger**: a sealed tank of overdue time (and
  the people it bought back from the Gut). Restart the Master Clock with it, and Q1 begins: everyone's back on the
  Schedule, back on the payroll, and back in debt. When that gets expensive, they can end the world again.
- The sims: ☺ CORP's been buying the Machine's sim time for years to train the security for the Re-Merger.
- Mr. Overtime fight 3, in the Lates: a time-loop arena where his punches arrive before he throws them.

### Act IV: "Quarterly Review" (The Margins, Corp Hill)
- The Missing Hour raid. The Bottom climbs the hill at 03:00. A mass battle up Dividend Road with everyone you
  allied with: whoever runs each district you dealt with or took over turns up (the Punchlines with pie cannons, the
  Mall Rats on rocket carts, the Remainders with a giant 7, or the shaky company allies, who might switch sides).
- At the Margins you learn that Vacancy Holdings has bought the Bottom from ☺ CORP: after the Re-Merger, the void
  gets it.
- You reach the ☺ Spire. **The Twins** (VP of Synergy) block the elevator.
- Choice point: Auntie Spreadsheet asks you to blow up the Master Clock; the Chief Punctuality Officer offers you a
  calendar, a name and a dental plan if you hand over the Bottom's leaders. You can also do neither.

### Act V: "Overdue" (the Master Clock), three endings
Final fight: **Mr. Overtime, Fully Billable**, wired into the Master Clock, in a clock tower made of gears, office
furniture and an enormous beating meat pendulum. Your allies and your choice decide who fights next to you.

The last mystery: in the clock room there's a second ☺ vending machine, identical to the one at the Bottom. Inside it,
asleep on the buttons, is **the founder** (a cat). It's been napping on the Machine's network since the Final Quarter.
The day you were dispensed, it rolled over onto the button. Legally, that's a yes.

| ending | how | what happens | epilogue line |
|---|---|---|---|
| **ON TIME** (☺ CORP) | hand over the Bottom; kill Overtime and take his job | the Re-Merger works. The lights come back on, the streets get scrubbed, the old world returns, and everyone is an employee again. You're the new Mr. Overtime: your punch-clock heart ticks in the HUD. The Bottom is sold to the void. | "welcome back to the economy. your first meeting was yesterday." |
| **LATE** (the Bottom) | smash the Master Clock with the Bottom and your allies | nobody owns time anymore. The companies lose their grip, the ruins belong to whoever lives in them, and the whole city slowly grows a pulse. Each district's epilogue depends on who you put in charge. | "nobody knows what time it is. lumps is crying at a sunset. it's the wrong time for it. he's thrilled." |
| **NAP TIME** (neither) | pet the founder 12 times instead | the founder wakes up, stretches across the Master Clock's keyboard and types `zzzzzzzzzzzz`. Legally, that's a nap. Every contract in the city is suspended: no Schedule, no Re-Merger, no rot, no back pay. The companies and the gangs just have to share. | "the board has entered a meeting. the meeting is a nap. it will run late." |

After any ending the city stays open (post-game), with the ending's look applied (LATE turns the fleshy look on in
every district; ON TIME scrubs the ruins white and makes the cops friendly to you; NAP TIME puts a sleeping cat on every
roof). The Machine keeps running the sims, whatever you chose.

---

## 4. The districts

Ten districts, laid out down a hill (top to bottom): Corp Hill → Chrome Gristle / Evergreen Acres / Number Works →
The Checkout / Pinstripe → The Lates / The Margins → The Gut → The Bottom. The BR's Jankburg districts are the ruins
of the old downtown, folded in: Corp Hill stays Corp Hill, Neon Market becomes Chrome Gristle, Number Works stays,
Liberal Lane becomes Evergreen Acres, Overdraft Heights collapsed down the hill into The Bottom. **The Commute** (dead
highways, paper storms, the Unpaid and the Fun Department's convoy) links them all, and the void eats at the edges.

Each district has a **ruler** (a company or a group). Six start under a company; the Hostile Takeovers questlines
(§6.11) can hand them to the smaller group that lives there.

Every district has a **traversal gimmick** (a rule it bends, like the BR POIs) and a **boss** who drops an **organ core**.
Bosses are **refightable**: their company (or their gang) re-hires them. A beaten boss's arena shows a "POSITION REFILLED" sign after the
next in-game midnight; walk in for a rematch with harder mods and another core roll.

### 4.1 The Bottom (slum / rebel hub, the starting district)
- **Theme:** a survivor town in the rubble at the bottom of the hill, where the Stampede and the Demerger washed
  everyone who didn't own anything. The bottom of the org chart, stacked on top of itself.
- **Look:** a steep street of stacked pastel cube houses (pink, yellow, teal, mint) built out of shipping containers,
  dead vending machines and fallen ☺ signage, washing lines, satellite dishes made of woks, stairs everywhere, tie-dye banners, string lights, a dark purple sky that's always slightly the wrong time.
- **Landmarks:** the **Lost & Found** (hub safehouse, a ruined returns depot, home of **the Machine**), **The Long Stairs** (1,000 steps up to the
  Gut border), **Lumps' Gym** (all the weights are fridges), the **Down Escalator** (it's broken; it only goes down).
- **Ruler:** The Bottom (a group). **NPCs:** tie-dye survivors, kids on scooters, scavengers with shopping carts,
  mannequins with odd limbs, street cooks, a guy who sells one shoe.
- **Side quests:**
  - *Lost Property*: return 10 items from the Lost & Found to people all over the city (one is a whole bus).
  - *Leg Day*: help Lumps train by carrying fridges up the Long Stairs; drop one and it rolls all the way down.
  - *Wok the Dish*: fix the satellite wok-dishes by grappling between roofs during a storm.
  - *One Shoe Guy*: find the other shoe. It's in the Gut. It's alive now.
- **Boss: THE LANDLORD (Mr. Deposit).** A gigantic rubber-faced man made of stuffed armchairs and keys, Vacancy
  Holdings' last agent in the Bottom, who "owns" the biggest pile of rubble and keeps everyone's deposits in his body. Gimmick: he swallows your weapons when he hits you (you get
  them back by hitting his "deposit box" belly); he raises the rent mid-fight (the arena floor shrinks). 
  **Core: Deposit Gland** (Guts slot): 30% of damage you take is held and refunded as healing 5 s later.
  *Downside:* if you die before the refund, the Landlord keeps it (you respawn with fewer coupons).
- **Traversal gimmick:** **Washing-line ziplines.** Every washing line is a grapple rail; slide along it at speed, drop
  socks as you go.
- **Music:** lo-fi hip hop played on a broken accordion, a warm bass, distant dogs.

### 4.2 The Gut (the living meat/organ district)
- **Theme:** Gristle & Sons Biologics' campus, where the "grow your own lunch" formula got out on the Final Quarter.
  The whole district went overdue and became alive. It digests. It's warm. It loves you. And it's still a company.
- **Look:** streets are intestine tubes with pink ribbed walls, ribcage arches over the avenues, tooth-cobble
  pavements, lungs inflating between buildings, the old shops still visible under skin (a launderette with a tongue for
  a door), vein-wires carrying light, pulsing sphincter doors. Colours: raw pink, liver purple, fat yellow, bile green.
- **Landmarks:** **The Big Stomach** (the district's heart, a crater of churning acid lake), **Peristalsis Avenue**
  (the moving street), **The Choir Lung** (a cathedral that breathes), **Tooth Market** (everything costs teeth).
- **Ruler:** Gristle & Sons Biologics (a company; its staff are the **Gut Choir** now, still wearing their lanyards
  under the robes). **NPCs:** robed choir singers with puppet faces stretched into permanent smiles, "digesters"
  (half-absorbed people grown into the walls, still chatting), wandering stomach-dogs, a few normal people lost on
  their way to work.
- **Side quests:**
  - *Reflux*: the acid lake is rising. Plug burping vents with cars.
  - *Hairball*: something is stuck in Peristalsis Avenue. It's a guy's whole house. Push it through.
  - *Choir Practice*: the Choir needs a tenor. Collect three voice boxes from overdue ☺ CORP offices.
  - *Quarterly Growth*: Gristle & Sons wants the Gut to hit its growth target. Feed it, or sabotage the feeding tubes
    (decides whether the Gut spreads into the Bottom later).
  - *Wisdom Tooth*: pull a giant tooth out of the Tooth Market square with the lasso and a car.
  - *Belly Button*: there's a door in the Big Stomach. Don't press it. (You press it.)
- **Boss: THE STOMACH BISHOP.** Gristle & Sons' CEO and the Choir's leader: a tall, pale, smiling priest whose robes are one big stomach,
  conducting the district with a femur baton. Phase 1 he fights in the acid lake on a raft of tongues; phase 2 he
  swallows the arena and you fight *inside him* while the walls contract on a rhythm (peristalsis beats); phase 3 he's
  just a mouth. **Core: Second Stomach** (Guts slot): hold F on any dropped weapon to eat it for HP (rarer = more HP).
  *Downside:* you burp loudly every 30 s and give away your position; eating three in a row makes you vomit your
  current weapon.
- **Traversal gimmick:** **Peristalsis.** Certain streets contract in waves and carry you along like a conveyor (huge
  speed if you slide in on the beat). Lungs are trampolines. Intestine tubes are slides.
- **Music:** a choir humming one chord, a giant heartbeat as the kick drum, wet synth pads.

### 4.3 Pinstripe (the mafia district)
- **Theme:** Fazzoletti Family Insurance's old-money quarter. It came through the Final Quarter almost untouched,
  because it was insured (by itself). A family of grotesque puppet-faced giants who think they're elegant, selling
  protection to the ruins.
- **Look:** gothic stone mansions, marble floors, red-and-white pinstripe awnings, gold medallions, velvet ropes,
  spaghetti restaurants with checkerboard floors (red, blue, black), pink stucco interiors.
- **Landmarks:** **Villa Fazzoletto** (the Don's house, a cathedral of marble and meatballs), **The Sauce Works**
  (the family's front business, a sauce factory with a red river), **Respect Bridge**, the **Bocce Pit**.
- **Ruler:** Fazzoletti Family Insurance (a company). Takeover group: **the Punchlines**. **NPCs:** huge pinstriped puppet goons with stretched faces and tiny hands,
  tiny accountants with huge heads, jesters (the family keeps two court jesters, see Art Bible), restaurant waiters
  who are only arms.
- **Side quests:**
  - *Wet Work*: deliver laundry. Actual laundry. They're very clean.
  - *The Meatball Run*: a meatball the size of a car got loose on Respect Bridge. Roll it home.
  - *Two Jesters*: the Don's jesters, **Pip Grinsworth** (short, giant horned head, needle teeth) and **Long Larry**
    (tall, lilac, droopy nose), are secretly the Punchlines. They want you to prank the Family until it falls apart.
    Every prank is a weapon gimmick.
  - *Protection*: collect protection money from ☺ CORP's tax office. With a minigun.
  - *Claims Department*: help survivors file claims on their apocalypse cover. Every claim is denied. Every denial is
    a gunfight.
- **Boss: DON GRINALDI FAZZOLETTO.** A looming giant in a pinstripe suit, bald, a stretched puppet face with a grin
  you can see from orbit, a gold medallion, a tie as long as a car. He's a marionette: his strings go up into the
  ceiling of the Villa. Gimmick: shoot the strings to drop his limbs (one arm, then the other, then his jaw falls off
  and keeps talking). He "makes you an offer": a mid-fight dialogue choice lets you take a bribe and skip phase 2.
  **Core: Smile Muscle** (Mouth slot): NPC prices -25%, and you can "make an offer" to non-boss enemies to make them
  switch sides for 15 s (once per minute). *Downside:* your face is stuck in a grin, and on low HP you laugh
  uncontrollably (enemies hear you).
- **Traversal gimmick:** **Strings.** Marionette strings hang from the sky over the district (the Family is held up from
  somewhere). Grapple onto them for free infinite-length swings.
- **Music:** a mandolin and a tuba playing a waltz that slowly detunes, a crooner who only sings vowels.

### 4.4 The Checkout (the shopping district)
- **Theme:** Big Value's flagship mall, where the Stampede started. The sale that ended the world never stopped:
  the shoppers are still in there, and so is the stock.
- **Look:** the Dead Mall scaled up and half-collapsed: a cracked glass dome over the streets, escalators between them, fountains with coins, food courts the size of plazas,
  sale banners, mannequin shoppers in every window, neon SALE signs in pink and yellow. Clean on top, gross in the
  service corridors.
- **Landmarks:** **The Infinite Queue** (a queue that winds around the district 14 times), **Food Court Colosseum**,
  **The Big Escalator** (2 km, goes up to Corp Hill, employees only), **Returns Desk Zero**.
- **Ruler:** Big Value Retail (a company): Mall Security (rent-a-cops on segways) and the **Forever Shoppers** (zombie
  consumers who stampede toward discounts). Takeover group: **the Mall Rats**, who live in the vents.
- **Side quests:**
  - *Price Check on Aisle Everything*: scan 30 hidden barcodes with the Instant Camera.
  - *Doorbuster*: a 2-minute stampede survival. Shoppers trample anything between them and the TV.
  - *Mall Walker*: race the Mall Walkers' club of terrifyingly fast grandmas.
  - *Lost Child*: the lost child from the day of the Stampede is 40 now. He's fine. He runs the Mall Rats.
- **Boss: THE CART MOTHER.** Every lost shopping cart in the city, welded around a single furious shopper who was first
  through the doors at the Stampede and never got her refund. Big Value made her their mascot. She rolls, she stacks, she splits into a swarm of carts and recombines. The Shopping Cart Cannon is the
  counter (shoot carts into her to make her heavier and slower). **Core: Coupon Liver** (Guts slot): 15% of loot drops
  roll one rarity higher. *Downside:* you auto-buy the first thing you look at in any shop for 3 seconds. Spend wisely.
  Or don't look.
- **Traversal gimmick:** **Escalators.** Every escalator is a speed booster in one direction and a treadmill in the
  other. Cart surfing: ride shopping carts like skateboards.
- **Music:** mall muzak, slowed to half speed, with a cash register on every downbeat.

### 4.5 Corp Hill and the ☺ Spire (Corp HQ)
- **Theme:** the top of the hill, and the only place that still looks like before. Perfectly punctual, perfectly
  plastic, every second accounted for, in total denial that the world ended.
- **Look:** a clean bubble in the ruins: a bleach line on the road where the rubble stops and the white starts. White
  and cyan glass towers, chrome, giant ☺ logos, pristine lawns cut to exactly 1 inch, public clocks on
  every corner all ticking in sync, huge LED schedules on building sides. Inside: grey-carpet open plan offices going
  on forever. People walk in sync.
- **Landmarks:** **The ☺ Spire** (HQ, with the Master Clock at the top), **The Cathedral of Shareholder Value**,
  **Dividend Road**, **The Smiling Fountain**, **The Punctuality Museum**.
- **Ruler:** ☺ CORP (a company; can't be taken over, only ended). **NPCs:** mannequin office workers in sync, executives with tiny monitor heads, Timekeeping
  officers, cleaners with bleach cannons, the Marketing mascot.
- **Side quests:**
  - *Reply All*: an email that will doom ☺ CORP is about to be sent. Chase it down the Spire's pneumatic tubes.
  - *Casual Friday*: ruin the dress code by stealing every tie in an office.
  - *Team Building*: survive a corporate trust-fall exercise off a skyscraper.
  - *Parking Permit*: get one. It's the hardest quest in the game.
- **Boss: THE TWINS (VP of Synergy).** Two executives merged at the hip in the big merger, sharing one suit and one
  smile, one always agreeing with the other. They swap roles (one shoots, one shields) and "circle back": attacks that
  return later. Kill one first and the other one does both jobs, very badly. **Core: Synergy Node** (Head slot): your
  first shot on a target is copied by a ghost shot 0.5 s later. *Downside:* you also copy *damage*: every hit you take
  repeats at 20%.
- **Traversal gimmick:** **On Time.** Everything moves on the beat of the clocks: moving walkways, elevators and
  window-cleaning gondolas on fixed timers. Be on time and you fly; be late and the door shuts in your face.
- **Music:** a ticking clock as the hi-hat, cheerful corporate ukulele, and a choir that sings "synergy" off-key.

### 4.6 Chrome Gristle (implant clinic / night market)
- **Theme:** the old Neon Market, now the black market of the ruins: the place to get organs (scavenged from the Gut)
  installed, swapped, pawned and stolen.
- **Look:** narrow neon lanes, pink and cyan signs, noodle stalls, back-alley clinics behind hanging butcher curtains,
  chrome and gristle together (jars of eyes, mechanical hearts in shop windows), rain on the floor, always night.
- **Landmarks:** **Organ Pawn** (sell your organs, buy them back later at a markup), **Doctor Upsell's Clinic**,
  **Arcade Row**, the **Noodle Shrine**.
- **Ruler:** the Meat Mechanics (a group trying to become a company: their logo is a kidney). **NPCs:** surgeons with too many arms, customers in bandages, noodle chefs, chrome
  hustlers.
- **Side quests:**
  - *Spare Parts*: retrieve a kidney that got up and left.
  - *Second Opinion*: get two Meat Mechanics to diagnose the same rash. They disagree violently.
  - *Arcade Legend*: beat the high score on a cabinet that runs the old JANKFIRE.
- **Boss: DOCTOR UPSELL.** A twelve-armed surgeon who tries to sell you procedures *during* the fight. Each arm has a
  different tool (bone saw, defibrillator, scalpel, card machine). Gimmick: he installs temporary bad implants on you
  if he grabs you (reverse controls, fish eyes); rip them out with the melee key. **Core: Spare Arm** (Arms slot):
  a third arm that auto-fires your sidearm at the nearest enemy. *Downside:* it sometimes slaps you instead.
- **Traversal gimmick:** **Neon signs.** Sign letters are grapple points; shooting a sign's letters spells new words
  and changes nearby shop prices.
- **Music:** fast synthwave, a koto, rain, a dentist's drill as a lead synth.

### 4.7 Number Works (the factory district)
- **Theme:** Remainder Industries' factory, which printed the numbers that crushed the world. Giant digits from the
  Final Quarter are still half-buried across the city. The presses are still running: whoever prints the prices runs
  the market.
- **Look:** yellow and black industrial yards, conveyor belts carrying giant numbers, smokestacks puffing digits,
  lucky 7s and unlucky 13s on everything, chunky friendly machines with faces.
- **Landmarks:** **The Smokestacks**, **The Remainder Pit** (where leftover numbers go), **The Big Calculator**
  (a building), **Prime Lane**.
- **Ruler:** Remainder Industries (a company). Takeover group: **the Remainders** (a union of people stamped with the
  digits nobody wanted).
- **Side quests:** *Carry the One* (escort a giant 1 across the district), *Rounding Error* (find who's been stealing
  0.5s), *Divide by Zero* (don't).
- **Boss: FOREMAN REMAINDER.** A huge crane-armed foreman with a calculator face. Every hit on him rolls a number that
  becomes the damage (the BR's "lucky 7 / unlucky 13" rule), and he can multiply or divide the arena (spawning more
  of himself, smaller). **Core: Lucky Kidney** (Guts slot): crits deal x7. *Downside:* every 13th shot deals 13 damage
  to you.
- **Traversal gimmick:** **Conveyor belts** that keep their momentum on you, and giant digits you can ride.
- **Music:** a drum machine made of stamping presses, an accordion counting out loud.

### 4.8 Evergreen Acres (the too-nice suburb)
- **Theme:** the normal-looking district. A gated suburb that survived the end of the world by refusing to admit it
  happened. Lawns, picket fences, sitcom families, a wall of sandbags painted to look like a hedge. It's the most
  horrifying place in the city because it's *fine*. (Liberal Lane's helpings and the Suburb map grow into this.)
- **Look:** perfect pastel houses, identical cars, sprinklers, a mannequin family waving in every window at the same
  time, a laugh track you can hear in the street.
- **Landmarks:** **The Cul-de-sac**, the **HOA Clubhouse**, **The Prize Pumpkin**, the **Community Pool** (it's deep).
- **Ruler:** the HOA (a group, with a militia, that wants to annex the ruins "for property values"). **NPCs:** mannequin families, a mailman who never stops, BBQ dads, dogs that are really two
  kids in a suit.
- **Side quests:** *Lawn Order* (mow 50 lawns with the Lawn Mower, perfectly), *Block Party* (survive one),
  *Keeping Up* (your safehouse here needs the same car as the neighbours or they call the Late Fees on you).
- **Boss: THE HOA.** Every homeowner in the association merged into a giant hedge-sculpted beast covered in
  "PLEASE KEEP OFF THE GRASS" signs, with a clipboard for a face. Gimmick: it fines you (each fine is a debuff), and it
  regrows from any lawn you haven't mowed. **Core: Grass Lung** (Lungs slot): standing on grass heals you
  ("YOU TOUCHED GRASS"). *Downside:* you sneeze on pollen and fire your weapon.
- **Traversal gimmick:** **Sprinklers** launch you; trampolines in every garden.
- **Music:** a happy sitcom theme on a loop that gets slightly slower and more out of tune every time it repeats.

### 4.9 The Lates (the overdue liminal zone)
- **Theme:** ground zero of the Final Quarter, where the overclocked Schedule cracked first. It's been the same
  Tuesday ever since. The Backrooms are its basement.
- **Look:** yellow wallpaper offices, flickering lights, empty car parks, identical streets that repeat, a clock tower
  with no hands, half-flesh carpet where it's started to rot.
- **Landmarks:** **The Waiting Room** (infinite, with chairs), **Tuesday Tower**, **The Backrooms Stairwell**.
- **Ruler:** nobody. The Loopers (people stuck since the Final Quarter, who've learned the loop by heart) just live
  here.
- **Side quests:** *Groundhog Lunch* (fix one guy's Tuesday so he can finally have Wednesday), *Copy of a Copy*
  (photocopy yourself out of a locked room), *Hold Music* (find the source of the hold music).
- **Boss: THE PERPETUAL TUESDAY.** A huge office worker made of a hundred copies of the same man, all late for the
  same meeting. Gimmick: the fight loops every 60 s and resets the arena, but damage carries over (and so do your
  mistakes: your past self's bullets replay). **Core: Tuesday Gland** (Head slot): press a key to rewind yourself 3 s
  (position and HP). *Downside:* there's a 1-in-10 chance you rewind to the *wrong* 3 seconds.
- **Traversal gimmick:** **Loops.** Walk off one edge of a street and arrive at the other; momentum is kept. Infinite
  falls between floors build insane speed.
- **Music:** hold music, a distant phone ringing in key, fluorescent hum.

### 4.10 The Margins (the void shore / forest edge)
- **Theme:** the edge of the world, where Vacancy Holdings repossessed the ground itself and keeps selling it to the
  void, plot by plot. The Scary Forest grows here, and the Tall Guy From HR (on loan from ☺ CORP) walks it.
- **Look:** dark pines, crumbling roads that end in nothing, houses half-eaten by a glossy black void, "PREMIUM
  NEGATIVE SPACE" billboards, foreclosure notices nailed to trees.
- **Landmarks:** **The Last Bus Stop**, **HR Cabin**, **The Edge** (a cliff into the void with a lifeguard tower).
- **Ruler:** Vacancy Holdings (a company; estate agents in hazmat suits). Takeover group: **the Margin Walkers**
  (lonely people who stake ground to stop the void, with garden gnomes).
- **Side quests:** *Staking Claims* (plant gnomes to hold ground), *Lifeguard* (pull people out of the void with the
  lasso; they've lost the dental), *Exit Interview* (find out what the Tall Guy wants: it's a signature).
- **Boss: THE TALL GUY FROM HR** (refightable in the open world, not just the forest map). He's unkillable in his own
  forest, until you find his file in the HR Cabin. Gimmick: he only moves when you're not looking, and his arms are
  as long as he wants. **Core: Long Spine** (Spine slot): your melee range doubles and you're 30% taller.
  *Downside:* you're 30% taller. Doorways hurt.
- **Traversal gimmick:** **Void Edges.** Falling into the void respawns you at the nearest staked gnome (no death),
  keeping your momentum. Fall in on purpose.
- **Music:** a single drone, wind, a far-away music box playing the ☺ CORP jingle.

### 4.11 The Commute (the wastes between districts)
Not a district: the connective wasteland. The old ring road and the highways from the BR's Jankburg, jammed with dead
cars from the evening rush hour of the Final Quarter, collapsed overpasses, giant digits stuck in the tarmac, and
**paper storms** (blizzards of shredded paperwork that cut visibility to 20 m and hide you from Late Fees).
- **Who's here:** **the Unpaid** (intern raiders in office-chair armour, on war-rigs welded from desks and buses),
  **the Fun Department** (a feral mascot carnival convoy that only comes out at night), scavengers, the occasional
  Vacancy Holdings survey team.
- **Activities:** raider camps to clear (each one held turns into a Bottom outpost), convoy ambushes, the Fun
  Department's travelling carnival (mini-games where losing is a fight), salvage runs in the wrecks, races.
- **World boss: EMPLOYEE OF THE MONTH.** The Unpaid's warlord, on a moving war-rig made of a bus, forty office desks
  and a photocopier that prints raiders. He gave himself the award every month since the Final Quarter. Gimmick: a
  fight on and around a moving convoy at 120 km/h; board it with the grapple, knock his interns off, and break the
  photocopier. **Core: Lanyard Gland** (Skin slot): raiders and low-rank enemies sometimes mistake you for staff and
  don't shoot. *Downside:* sometimes your boss calls (a pager goes off at full volume).
- **Traversal gimmick:** **Jams.** The dead traffic is a road made of roofs: car-roof parkour at full bhop speed.
- **Music:** a road-trip rock riff on a kazoo, dust, distant car alarms that never stop.

---

## 5. The nemesis: MR. OVERTIME

> Head of Timekeeping Enforcement. Employee #1. Has never been late. Has never left. He didn't notice the end of the
> world; he just noted that everyone else was absent. Now he's collecting forty quarters of back pay from the ruins.

**Look:** a 4.5 m corporate cyborg in a grey suit stretched over pistons, with a huge **punch-clock built into his
chest** (the time-card slot glows, the clock face is his heart and it ticks loudly), **two heavy-duty stapler arms**, a
small human head sunk between his shoulders with a puppet-like stretched smile and a desk-lamp visor, a lanyard
with forty years of employee-of-the-month badges, and polished brogues the size of cars. The tie is a bungee cord.
He steams when angry. He's polite. "this will only take a minute. it will take exactly a minute."

**Moveset (shared by every fight, remixed):**
- **Staple Gun:** fires huge staples that pin you to walls (mash jump to rip free; the staple stays as a grapple
  point).
- **Punch In:** the grab. He shoves you into his chest slot and punches your card: you're stunned and "scheduled" (a
  timer appears; if it runs out you take a big hit). Shoot the clock face to get spat out.
- **Overtime Slam:** jumps and slams; the shockwave stops time in a ring (anything inside freezes for 2 s).
- **Coffee Break:** at half HP he stops to drink coffee. Free hits, unless you're on the coffee's schedule too...
- **Fines:** he throws paper fines that stick to your screen (HUD obstruction).
- **Weak point:** the punch-clock heart. Crit it to stagger him; in later fights the armour around it changes.

**The fights:**
| # | where | mission | gimmick | ends with |
|---|---|---|---|---|
| 1 | the Gut border, Act I | *Clocking In* | basic moveset in a small arena; Gut lungs bounce you over his slams | crack the clock: he retreats; drops **Cracked Punch-Clock** core |
| 2 | the Spiral Freeway on The Commute, Act II | *Rush Hour* | a car chase: he runs after your car (on time!), staples cars into barricades; fight from the car and on the roofs | he's left behind in the jams; you steal his lanyard (☺ CORP access) |
| 3 | The Lates, Act III | *Tuesday Again* | time loop arena: he knows what you'll do (his attacks are telegraphed from your *last* loop) | his time card is torn: Late Fees can't reach ★5 for a while |
| 4 | the Master Clock, Act V | *Overdue* | "Fully Billable": fused with the clock, the arena is a vertical gearwork; every phase changes the clock speed (slow-mo / fast-forward rounds) | the ending you chose |

Refights: after Act II, Overtime is the "★5 boss" of the Late Fees system (§6.2), and his rehired version can be fought
again at the Punctuality Museum for core rerolls.

**Cracked Punch-Clock** (Heart slot): every 60 s your next magazine has no reload ("unpaid overtime"), and at low HP
time slows around you for 3 s (once per life). *Downside:* it ticks. Loudly. Enemies hear the ticking near you,
and once an hour (game time) you have to stand still for 5 s to "clock in" or take a fine.

---

## 6. Systems

### 6.1 The open-world loop
`roam → find trouble (quest, crime, loot, boss, cat) → fight / drive / chase → loot and money → install, upgrade,
buy → story mission unlocks → new district opens → repeat.`
- **Scavenge everything.** It's the end of the world: wrecks, ruins, collapsed shops and raider camps are full of loot,
  junk to sell and coupons.
- A day-night cycle (1 game day = 48 real minutes), but time is broken, so each district has its own **district clock**
  that runs fast, slow, backwards or not at all (Corp Hill is the only one exactly on time). Shops, patrols, trains and
  some quests follow the local clock. At night the rot spreads: districts get fleshier, enemies tougher, loot better.
- Story missions are gated by act; districts open as the story reaches them (the Bottom and the Gut are open from the
  start; the rest open in Act II; Corp Hill's Spire opens in Act IV). You can wander into higher districts early,
  they're just Late Fees magnets.
- **Chaos is rewarded.** Spectacle kills, car crashes, flinging people off stairs and long grapples fill the **HYPE**
  meter, which powers killstreak items (§6.6).

### 6.2 Late Fees (the wanted level)
Late Fees are ☺ CORP's wanted level: it still thinks it owns the city and everyone in it owes back pay. Crimes,
chaos, and being on ☺ CORP property (which, according to ☺ CORP, is everywhere) add **Late Fees**. Stars are drawn as little ☺ clock
faces. Each level sends something new:

| level | name | who comes | how they fight |
|---|---|---|---|
| ★1 | **Running Late** | Punctuality Officers on foot (mannequin cops with whistles and clipboards) | tasers, whistles stun, tickets stick to your screen |
| ★2 | **Overdue** | Timekeeping cruisers (Corp cop cars), officers with batons and pistols | roadblocks, pit manoeuvres, spike strips made of staples |
| ★3 | **Final Notice** | Collections vans + **Reminder Drones** (flying alarm clocks) | net guns, repo hooks that steal your car, drones that ring and mark you |
| ★4 | **Disciplinary** | HR Tactical (SWAT with filing-cabinet shields), an armoured "Meeting Room" (a flying conference room gunship) | flashbangs that say "PER MY LAST EMAIL", snipers |
| ★5 | **TERMINATED** | **Mr. Overtime** himself, plus everything above | the nemesis moveset in the open world |

**Losing them:** break line of sight and stay hidden until the clock faces drain (the classic); duck into an
**overdue zone** (Gut, Lates: Corp won't follow past ★3); change outfit at a safehouse; ride a **Calendar Reset**
bus (a clean schedule for a fee); or pay at a **Late Desk** (coupons, price scales with stars). Killing Corp forces at
★5 is allowed and very loud. The Bottom's districts give a "nobody saw nothing" bonus (fees drain faster).

**Other rulers' heat:** in a district run by another company or group, crimes against them raise **their** heat
instead (★1-★3 only): the Family sends pinstripe goons in bocce-ball limos, Big Value sends Mall Security on segways
and a Forever Shopper stampede, the HOA's militia shows up in golf carts with leaf blowers, the Unpaid just rob you.
Rulers you're allied with ignore small stuff.

### 6.3 Police chases and drivable cars (new)
- The traffic cars (`server/traffic.js`, `public/js/cars.js`: supermini, saloon, pickup, panel van, city bus, box
  truck, ice cream van, taxi) become **drivable**. F on a driver's door to yank them out (they ragdoll); F on a
  parked car to get in.
- **Handling:** arcade, jank-forward. Handbrake drifts, a boost that lasts as long as you hold it but overheats,
  infinite momentum (cars keep speed off ramps, you can grapple *from* a car to slingshot it), slippery on marbles and
  banana peels, ragdoll ejection on big crashes (the existing car-meets-car explosion rules stay).
- **Combat from cars:** drive-by with sidearms; passengers (co-op) get their full loadout. Lasso a car to tow it.
- **District vehicles:** meat buggies in the Gut (they bleed instead of smoke), bocce-ball limos in Pinstripe,
  shopping carts with rocket motors in the Checkout, Corp segways, the Bottom's sofa-car.
- **Chases:** Corp cops use the same lanes as traffic, with pursuit AI: box-in, PIT, roadblocks at junctions ahead,
  spike strips, repo hooks at ★3. Losing them is about line of sight, alleys, and jumps they won't take.
- **Garages:** park a car at a safehouse to keep it. Paint it with the existing wraps system.

### 6.4 The quick bar, the weapon wheel and the inventory
- **Quick bar:** 8 slots on keys 1-8 (scroll to cycle), like the game's current slots but bigger. Anything fits:
  guns, melee, gear, killstreak items, consumables.
- **Weapon wheel:** hold Q (or Tab) for a radial wheel of the quick bar plus the categories (guns / melee / gear /
  streaks / snacks), time slows to 20% while it's open (solo) or 70% (co-op, it's shared time).
- **Inventory:** the **Tote Bag** grid (starts at 20 slots, upgrades to 60 with side quests). Weapons, implants
  (uninstalled), cores, quest items, snacks, junk to sell. Safehouses have a **Locker** (stash).
- **Hotkeys you already know stay:** reload, G for the item, V/X weapon actions, grapple, lasso.

### 6.5 Loot (rarity rolls, no durability)
Weapons drop from enemies, crates, vending machines (shoot them), bosses and quests. They **never break**.
- **Rarities:** Common (green) → Rare (blue) → Epic (purple) → Legendary (orange) → **☺ PREMIUM** (hot pink, boss and
  late-night only). Same colours as the cosmetics `RARITY` table, plus the new top tier.
- **Base weapon:** one of the game's 30+ weapons (Redline, Marble Shotgun, Scales of Justice, Peel Shooter, Nail Gun,
  Bowling Ball Launcher...). Each keeps its gimmick.
- **Stat rolls:** damage, fire rate, magazine, reload speed, spread, knockback, projectile speed, each rolled in a
  range per rarity (e.g. Common ±10%, Legendary +10..+35%). Stats show as cards with comic arrows (▲▼) against what
  you're holding.
- **Brands (who made it):** decides its flavour and look (paint, wrap zones `_wzA/_wzB/_wzN`).
  | brand | flavour |
  |---|---|
  | **☺ CORP Standard Issue** | reliable, accurate, boring; beeps when you're late on a reload |
  | **Bottom Scrap Co.** | taped together, random extra part (a scope on a shotgun), cheap |
  | **Meat Mechanics** | organic: magazine regenerates, gun bleeds when you're hurt |
  | **Famiglia Arms** | pinstripe paint, crits on enemies who "disrespected" you (hit you first) |
  | **Value Pack** | comes in twos (akimbo), jams sometimes, prices slashed |
  | **Number Works** | damage numbers matter: 7s and 13s |
- **Modifiers:** one or two rolled prefixes: *Bouncy* (knockback ++), *Sticky* (projectiles stick), *Overdue* (more
  damage the longer since your last reload), *Punctual* (on-beat shots crit), *Greasy* (drops banana peels on reload),
  *Haunted* (shoots by itself sometimes), *Rubbery* (bullets bounce once).
- **Named legendaries** (fixed quirks, flavour text):
  | name | base | quirk | flavour |
  |---|---|---|---|
  | **The Late Bloomer** | AR | more damage the later you are for the current mission timer | "better late than never. much better." |
  | **Grandma's Hands** | Hand Slapper | each slap heals you a bit and calls the target "sweetie" | "she slaps because she loves." |
  | **Mother's Ladle** | Bread → Ladle | splash damage of hot soup; leaves slippery puddles | "eat something." |
  | **Severance Package** | Shotgun | kills pay you 50 coupons | "it's not personal. it's paperwork." |
  | **Sunday Best** | Revolver | every shot is a headshot on Sundays (game time) | "dress for the job you want. the job is murder." |
  | **The Intestine** | Lasso | 40 m long and it pulls *you* to them | "nine metres of personal space." |
  | **Reply All** | Minigun | every bullet that hits copies itself to everyone near the target | "per my last bullet." |
  | **Quiet Quitter** | Sniper | silent, and does nothing at all between 17:00 and 09:00 | "outside working hours." |
  | **Lumps' Ring** | Rocket Punch | knockback x3, you cry on kills | "he made it himself." |
  | **The Receipt** | Card Deck | cards are 3 m long receipts that slice everything in a line | "you'll want to keep this." |
- **Loot rules:** each player sees their own drops (no loot fights in co-op). Pickups show a rarity beam (in the rarity
  colour) and a comic sound per tier (the ☺ PREMIUM drop plays a choir).

### 6.6 Killstreaks become items
- The existing streaks (Moon Boots, Chicken Strike, Scythe Rifle, Spinbot, Wrecking Ball, Spy Satellite, Overdrive
  Rig, Giant Duck) become **consumable streak items** in the Tote Bag: dropped by bosses, found in rare crates, bought
  at Chrome Gristle.
- Using one needs **HYPE**: a meter filled by kills, stylish kills, crashes and long grapples. Each item has a HYPE
  cost (Moon Boots 25%, Giant Duck 100%). HYPE slowly drains when you're quiet.
- They stack (max 3 of each) and can go on the quick bar. Using one plays its big HUD callout as now.
- New story-only streak items: **Calendar Invite** (summons the Bottom's crew to fight with you for 30 s), **Fire
  Drill** (everyone in the area runs outside in a panic), **Lunch Break** (all Corp enemies sit down to eat for 10 s).

### 6.7 Bio-implants
Your mannequin body has **body slots**. Every implant is a perk or passive *and* a visible change to your body *and* a
jank downside. Installed at Meat Mechanics clinics (or by Auntie Spreadsheet, badly).

| slot | example implants |
|---|---|
| **Head** (brain) | Tuesday Gland, Synergy Node, *Spreadsheet Lobe* (see enemy HP bars; downside: you see *everyone's* numbers, including how much they earn) |
| **Eyes** | *Pigeon Eyes* (see loot through walls in a big radius; downside: one eye looks backwards, small view wobble), *Price Tag Eyes* |
| **Mouth** | Smile Muscle, *Bear Trap Jaw* (melee bite heals; downside: you bite NPCs you talk to sometimes) |
| **Heart** | Cracked Punch-Clock, *Spare Ventricle* (a second HP bar that only fills from healing) |
| **Lungs** | Grass Lung, *Balloon Lungs* (hold jump to float; downside: you deflate with a rude noise) |
| **Guts** | Second Stomach, Deposit Gland, Coupon Liver, Lucky Kidney |
| **Spine** | Long Spine, *Slinky Spine* (slide distance x2; downside: you bounce at the end) |
| **Arms** | Spare Arm, *Pistol Fingers* (an extra weak hitscan when unarmed; downside: you point at things you look at) |
| **Legs** | *Spring Knees* (huge jumps, built-in wrong knee; downside: 1 in 20 landings, your knee folds backwards and you stumble) |
| **Skin** | *Rubber Skin* (fall damage off, bounce off walls; downside: you squeak) |

- **Organ cores** from bosses are rare implants with big perks. Bosses are refightable, and each refight rolls the
  core's **quality** (Bruised / Fresh / Prime / Premium) which scales its perk (and sometimes its downside).
- **Overload:** you can install more than your **Body Budget** allows (budget grows with promotions = cats petted and
  the story). Over budget, the downsides get louder (rejection: your body visibly lumps and twitches).
- **Visible:** each implant adds a model change on your mannequin (a third arm, a clock in your chest, a big smile,
  a ribcage that shows). Other players see it.

### 6.8 Money, shops, safehouses, saving
- **Coupons** are money. After the Stampede, Big Value's coupons were the only thing in the city that said "never
  expires", so everyone uses them (old ☺bucks are worthless; people burn them for heat). Earned from loot, quests,
  side activities, selling junk, robbing. Remainder Industries prints the prices, so prices change with who runs
  Number Works. Containers (crates, bags, boxes) keep coming out of the Machine's tray as before, for cosmetics.
- **Shops:** gun shops (rolled stock that refreshes at midnight), Meat Mechanics (implants, installs, uninstall fees),
  Tooth Market (pay in teeth), vending machines (shoot them), car dealers, outfit shops (the existing cosmetics).
- **Safehouses:** one per district, unlocked by a quest. Save point, stash locker, garage, wardrobe, bed (skip time),
  and a **Machine terminal** (respawn point, and the door into the training sims). The Lost & Found is the first.
- **Saving:** autosave at safehouses, mission starts and boss kills; a manual save at safehouses. 3 save slots per
  account, stored server-side (TECH_PLAN §7).

### 6.9 Side activities
- **Cat Board Hunt:** the board of directors (cats) hide across the city. Pet them for promotions (+1 Body Budget).
- **Rampages:** "OVERTIME!" kill-frenzy challenges with a weapon the game hands you.
- **Delivery runs** in silly vehicles (soup van, ice cream van, a hearse full of balloons).
- **Races:** street, rooftop grapple races, cart races in the Checkout, peristalsis surfing in the Gut.
- **Training sims:** every Machine terminal opens the normal multiplayer menu (Online, Bots, Coop, Training, the
  battle royale): the PvP is the sims. Story mode adds **sim contracts**: a faction pays you coupons to win a
  particular sim ("Big Value wants a Dead Mall win with the Shopping Cart Cannon").
- **Fight clubs:** the existing modes as bot fights inside the ruins themselves, run by the rulers (gun game in Number
  Works, Plant & Defuse in Pinstripe), with loot.
- **Stunt jumps** (huge ramps, MLG overlays), **graffiti** (sprays), **jobs** (taxi, repo man, Corp mail runner).
- **The real lore NPCs:** the Gary, Dale, Janitor, Mr. Smiles and Todd in the sims are recordings who don't know the
  world ended. The real ones are out in the ruins, older, with new lines: Gary still runs his site office (the region
  is now a crater), the Janitor is still mopping right up to the void, Mr. Smiles hides from the Fun Department, and
  Todd is the Unpaid's prophet, who would like everyone to stop worshipping him.

### 6.10 Co-op
- **Drop-in co-op** for 2-4 players. You can join a friend if your story progress is within one act of theirs (so
  nobody sees an ending they haven't earned). Otherwise you can still join them in **free roam**.
- **Mission sync:** the host's mission runs. Joiners get credit if they've unlocked that mission or earlier; if
  they're behind, they get a "temp contractor" credit (loot and coupons, no story progress). Side quests credit everyone.
- **Loot:** instanced per player. Shared kills give everyone their own drops. Trading in a safehouse.
- **Boss refights:** everyone in the arena gets their own core roll. Boss HP scales with players (+60% per player).
- **Late Fees** are shared per group (one star count), and so is HYPE (shared meter, any player can use it).
- **Revives:** a downed co-op player can be revived ("paperwork processed") for 10 s before respawning at a safehouse.
- **Cars:** passengers shoot, drivers drive. A car fits 2-4 depending on model.

### 6.11 Hostile Takeovers (who runs the city)
The companies caused the end of the world and still hold the turf; the smaller groups want it. That fight is a system.
- **Every district has a ruler**, shown on the map in its colours: ☺ CORP, Gristle & Sons, Big Value, the Family,
  Remainder Industries, Vacancy Holdings, or a group (the Bottom, the Punchlines, the Mall Rats, the Remainders, the
  Meat Mechanics, the HOA, the Margin Walkers, the Unpaid).
- **Each company district has a takeover questline** (3-5 missions) that ends with the district's boss. At its last
  mission you choose: **DEAL** (the company stays, owes you, gives you a discount and a shaky ally) or **TAKEOVER** (the
  group runs it, the company becomes hostile there, the group is a loyal ally).
- **What a ruler changes:** shop stock and prices, who patrols (and who comes after you there), the district's look
  over time (a Mall Rats Checkout gets graffiti, rope bridges and free samples; a Big Value one gets more SALE signs and
  turnstiles), music, side quests, and the boss's re-hire (a toppled company's boss comes back as a raider leader).
- **Raider camps on The Commute** can be cleared and handed to whoever you like as an outpost (a fast-travel point and
  a safe garage).
- **Act IV:** every ally you made shows up for the Missing Hour raid. Shaky company allies can switch sides mid-battle
  if your Corp Standing is high.
- **Endings:** each district gets its own epilogue panel based on who runs it.
- **Co-op:** the host's world sets the rulers; joiners keep their own for their own save.

---

## 7. Tone guide (where the gross lives)

The owner wants it nasty: pulsing flesh, puppet faces, body horror, gore, intestines. **But not everywhere**, so it
hits harder when it shows up.

| zone | dial | what's there |
|---|---|---|
| The Gut, the Big Stomach, overdue offices, boss arenas | **10/10** | pulsing walls, intestine streets, half-digested people chatting, eyes in the floor, organ cores pulled out wet, gore and gibs on kills |
| Pinstripe, Chrome Gristle, The Bottom at night | **6/10** | puppet faces, stretched grins, jars of organs, implant surgery, the occasional twitching thing |
| The Commute, the ruins | **5/10, wasteland** | dead traffic, skeletons still in lanyards, raider trophies made of office supplies, paper storms; grim but goofy |
| The Lates, The Margins | **4/10, creepy** | liminal, wrong, quiet; rot creeping into the carpet; the Tall Guy |
| The Checkout, Number Works, The Bottom by day | **3/10, cartoon** | silly, bright, slapstick violence; mannequin shoppers |
| Corp Hill, Evergreen Acres | **1/10, too clean** | spotless and smiling, and *that's* the horror; blood gets bleached by cleaners within seconds |

- **Normal people** are everywhere: chunky low-poly survivors with normal proportions, in scavenged clothes. Most
  of the city is them.
- **The training sims** (the PvP maps) keep their current look and tone: they're clean recordings of the world before
  the end, which makes the ruins outside hit harder.
- **Mannequin NPCs** (the game's jointed mannequins, built-in jank: tilt, wrong knee) are Corp workers, returns,
  shoppers, suburb families. They're the "extras" of the city.
- **Puppet people** (huge heads, rubbery skin, uncanny faces) are the district factions' characters: the mafia,
  the jesters, the Choir, Lumps and Wee Gordo.
- **Body horror is always cartoony and readable**, never realistic: bright saturated flesh, glossy rubber, chunky
  shapes. Gross like claymation, not like a medical photo.
- **Kills** keep the game's gibs and kill effects; in the Gut they're wetter, in Corp Hill they're confetti.
- **A "Squeamish" toggle** (settings) swaps the gore for confetti and the flesh walls for pink foam, for streams and
  younger players.
- **Writing voice:** deadpan, lowercase, cheeky. The grossest things are described the most casually ("the street is
  digesting a bus. don't stand near it. it's eating.").

---

## 8. Cutscenes and story presentation

The owner wants **cutscenes and stuff**. Every story beat gets shown, not just told, and it all runs **in-engine**,
in real time, with the game's own models, so your outfit, your implants and your co-op friends are in every shot (a
third arm from Spare Arm waves in the background of the ending).

### 8.1 The six kinds of scene
| kind | length | what it is | used for |
|---|---|---|---|
| **Cinematic** | 30-120 s | full in-engine scene: camera tracks, character animation, lip-flap, music stings, letterbox bars in pink | act openers and closers, big twists, endings |
| **Comic Panels** | 5-20 s | the scene freezes into 3-6 tilted comic panels with halftone shading and speech bubbles in the zine UI (Comic Neue, pink borders, cyan offset shadow), slammed in one by one with SFX words (*SPLUT*, *DING*, *CLOCK*) | quick beats, mission intros, flashbacks, "meanwhile at ☺ CORP..." |
| **Talk** | free | the existing lore-NPC dialogue tree (`shared/secrets.js` format) with a cinematic camera: over-the-shoulder, a slow push-in, the NPC's puppet face fills a third of the screen. The world keeps running behind it | quest givers, shops, every NPC with something to say |
| **Boss Intro** | 4-6 s | the camera whips to the boss, time stops, a huge anime-style title card: name, job title and a cheeky subtitle, red impact frame, a stinger | every boss and every rematch ("REHIRED" stamp on refights) |
| **Moment** | 1-3 s | gameplay-camera micro-scenes: a slow-mo kill cam on a boss kill, the core being ripped out, a car flipping into frame on a mission start | juice, never blocks control for long |
| **Previously on OVERDUE** | 10-15 s | loading a save plays a quick comic-panel recap of the last 3 beats, narrated by Auntie Spreadsheet in crayon captions | coming back after a break |

Rules for every scene:
- **Skippable.** Hold SPACE to skip (a filling ring). In co-op, everyone votes with the existing skip vote
  (`public/js/skipvote.js`): it skips when everyone has voted or 2 of 3.
- **Short.** No cinematic over 2 minutes. If it's longer, split it and let the player play in between.
- **Gameplay starts where the scene ends**: the last shot blends into the player camera at the player's real spot.
- **Voices are babble.** No voice acting: each character gets a synthesized "babble voice" in `audio.js` (pitch,
  speed, a timbre: Lumps is a low tuba hum, Wee Gordo a squeaky kazoo, Mr. Overtime a dial-tone with a typewriter
  click per word). Text shows in speech bubbles or subtitles. The mouth flaps with the babble.
- **Puppet faces act.** Faces have a jaw, two eye bones, eyelids and brows, so every character can blink, squint,
  grin wider than their head and stretch.
- **Replay:** every watched scene goes into the **THEATRE** tab in the pause menu (with a photo mode, the existing
  `photo.js`).

### 8.2 Boss title cards
Big yellow-on-black slam text, the boss's colour, ALL CAPS, one deadpan subtitle.

| boss | card | subtitle |
|---|---|---|
| Mr. Overtime | **MR. OVERTIME** · HEAD OF TIMEKEEPING | "has never been late. has never left." |
| The Landlord | **MR. DEPOSIT** · THE LANDLORD | "you're not getting it back." |
| The Stomach Bishop | **THE STOMACH BISHOP** · GUT CHOIR | "he's already digesting you. spiritually." |
| Don Grinaldi | **DON GRINALDI FAZZOLETTO** · HEAD OF THE FAMILY | "he's got people. on strings." |
| The Cart Mother | **THE CART MOTHER** · CUSTOMER SINCE 1999 | "she wants to speak to your manager. you don't have one." |
| The Twins | **THE TWINS** · VP OF SYNERGY | "they agree." |
| Doctor Upsell | **DOCTOR UPSELL** · MEAT MECHANIC | "would you like fries with that kidney?" |
| Foreman Remainder | **FOREMAN REMAINDER** · NUMBER WORKS | "carries the one. and you." |
| The HOA | **THE HOA** · HOMEOWNERS ASSOCIATION | "your lawn is 2 mm too long." |
| The Perpetual Tuesday | **THE PERPETUAL TUESDAY** · LATE FOR A MEETING | "you've seen this one." |
| The Tall Guy From HR | **THE TALL GUY FROM HR** · HUMAN RESOURCES | "he just wants a quick word." |
| Employee of the Month | **EMPLOYEE OF THE MONTH** · THE UNPAID | "every month. since the end of the world." |
| Mr. Overtime, Fully Billable | **MR. OVERTIME** · FULLY BILLABLE | "the meeting is now. the meeting is forever." |

### 8.3 The story's scene list
**C** = cinematic, **P** = comic panels, **B** = boss intro. About 45 scenes, ~38 minutes of cinematics in total.

**Act I: Please Take Your Item**
- **C1 "Please Take Your Item"** (opening, 90 s). It starts as a normal JANKFIRE match: the real HUD, the kill feed,
  the Suburb map, your loadout. You get the last kill. "TRAINING COMPLETE." Everything freezes. The camera pulls back
  through the glass of a vending machine: the match was inside it, a tiny glowing world behind the Jank Cola cans. It
  keeps pulling back, out of the ruined Lost & Found, up over the Bottom, up the whole rubble hill (the title card flies
  past: **JANKFIRE: OVERDUE**), the Gut breathing, Pinstripe's strings, the broken clocks, all the way to the ☺ Spire,
  the only lit building in the dark. Then it falls all the way back down into the Machine. BEEP. CLUNK. A mannequin
  drops into the tray: you. Dale and Auntie Spreadsheet stare at you. "it's never given anything." "it gave change."
  Your wrong knee clicks into place. Control.
- **P1b "The Final Quarter"** (the flashback, 6 panels, Auntie narrating in crayon captions): 16:59, the last
  afternoon of Q4. ☺ CORP turns the Schedule up to 11 (the clocks crack). Gristle & Sons ships early (a building grows
  a tongue). Big Value opens the doors (*STAMPEDE*). Remainder Industries prints the numbers (a giant 9 lands on a
  bus). Vacancy Holdings repossesses the ground (a street slides into black). 17:30: a cat walks across a keyboard.
  "and that was the end of the world. anyway. you hungry?"
- **P2 "Sauce Run"** briefing: Lumps holds up a pot. Lumps holds up a car key. Lumps cries. Wee Gordo: "he means
  steal a car. and watch out for interns."
- **C3 "It's Breathing"** (40 s). Driving into the Gut for the first time: the camera pulls ahead of your car as the
  street turns from tarmac to pink skin, a rib arch rises overhead, the Choir turns its stretched faces to you all at
  once and starts humming.
- **C4 "Clocking In"** (60 s). The Bottom. The sunset comes early today, and Lumps is crying at it. Every clock in the Bottom stops.
  Ticking. Huge brogues step down the Long Stairs, crushing them. Mr. Overtime ducks under a washing line, takes out a
  clipboard. "the bottom. you owe forty quarters of back pay. i'm here to collect." He staples Lumps to a wall. → **B: MR.
  OVERTIME**.
- **Moment "Heart Rip"**: in slow-mo, you yank a piece of the punch-clock out of his chest. It's warm. It ticks.
- **C5 "Second Stomach"** (45 s). A Meat Mechanic clinic, a dentist's chair, a lamp swings. Auntie holds the core.
  "this is a terrible idea." The Mechanic: "you'll be fine." Cut to black. *SQUELCH*. *TICK*. You wake up with a clock
  ticking in your chest. Implants unlocked.

**Act II: Hostile Takeovers**
- **P6 "Meanwhile at ☺ CORP"**: Mr. Overtime in a spotless boardroom at the top of a ruined world, with empty chairs
  and one cat. "a nobody. with my heart." The cat yawns. That's a yes.
- **P6b "Deal or Takeover"** (one per district, at the choice): split panels, the company's boss on one side with a
  contract, the group's leader on the other with a crowbar. Your pick slams in with a stamp: DEAL or TAKEOVER.
- **C7 "An Offer"** (Pinstripe, 60 s). A checkerboard restaurant. Pip Grinsworth and Long Larry flank the door with
  praying hands. The Don leans down from the ceiling on his strings, his grin unfolding wider and wider. "you got a lot
  of heart. i heard it's not yours."
- **C8 "Doorbusters"** (Checkout, 40 s). The doors open at 09:00. 10,000 Forever Shoppers stampede in slow-mo; a
  single shopping cart rolls out of the dust towards you. Then another. Then all of them. → **B: THE CART MOTHER**.
- **P9 "Nine Kilometres"**: the Schedule printout unrolls down the Number Works' chimneys; Wee Gordo reads it and
  gasps. "there's an hour missing."
- **C10 "Rush Hour"** (45 s, opening a chase). The Spiral Freeway on The Commute, through the jams and a paper storm.
  Your car. Unpaid war-rigs on the horizon. In the mirror: Mr. Overtime, running,
  at exactly the speed limit. He checks his watch.

**Act III: Off the Clock**
- **C11 "The Missing Hour"** (90 s). The Lates. A clock tower with no hands. At 03:00 the world goes grey and silent
  and a door appears in the sky. Inside: a tank the size of a district, full of glowing overdue time, and pipes going
  down the hill. Down to the Gut. Through the glass: people. "they're feeding it *us*."
- **C11b "Minutes of the Meeting"** (50 s). Auntie Spreadsheet finally opens her crayon notebook: she took the minutes
  of the last ☺ CORP meeting before the Final Quarter. Flashback in sepia comic panels: the board room, the execs
  (the Twins, before the merger merged them), a slide that says RESTRUCTURING: OPTION C (END OF WORLD). Everyone votes
  yes. "it wasn't an accident. it was a write-off."
- **P12 "Tuesday Again"**: the same panel four times. In the fourth, Mr. Overtime is already standing behind you.
- **C13 "Lumps' Speech"** (50 s). The Lost & Found, everyone from every district you helped (whoever runs them now:
  the scene is cast from your turf choices). Lumps stands on a
  fridge. He cries. He says one word ("up."). Everyone cheers. Wee Gordo explains the actual plan.

**Act IV: Quarterly Review**
- **C14 "03:00"** (60 s). The Missing Hour. The Bottom marches up Dividend Road in silence with every ally you made:
  the sofa-cars, the Punchlines or the Family's limos, the Mall Rats on rocket carts or Big Value's segways, a
  Wrecking Ball on a chain. Corp Hill's clocks all turn to face them.
- **C15 "Negative Space"** (40 s). The Margins. A house slides into the void. The Tall Guy From HR hands you a
  folder: SALE AGREEMENT: THE BOTTOM, ☺ CORP TO VACANCY HOLDINGS. He's sad about it. He's tall about it.
- **C16 "The Offer"** (60 s, the choice). The Spire's top floor. Two doors. Auntie Spreadsheet on a walkie: "blow it
  up." The Chief Punctuality Officer (a mannequin with a perfect smile and a lanyard to the floor) holds out a
  calendar with your name on it. A cat sleeps on the desk between them. The game asks you: **ON TIME**, **LATE**,
  or... (pet the cat).

**Act V: Overdue**
- **C17 "Fully Billable"** (60 s). The Master Clock opens like a ribcage. Mr. Overtime plugs his stapler arms into
  the gears, his suit tears, the meat pendulum swings. "your appointment is now." → **B: FULLY BILLABLE**.
- **Endings** (2-3 min each, the longest scenes in the game):
  - **E1 ON TIME**: you're issued a suit. The clock in your chest stops ticking and starts *keeping* time. A montage of
    the lights coming back on across the ruins, district by district, the rubble scrubbed white, everyone in a lanyard
    again, and the Bottom's houses folding into the void one by one. Your first meeting. The chair has your name on
    it. It's already warm.
  - **E2 LATE**: the Master Clock bursts. Every clock in the city melts. A wave of pink flesh rolls down the hill (from
    the top this time), soft and warm. ☺ CORP workers look at their wrists and see nothing. One of them laughs. One
    epilogue panel per district, by who runs it. Lumps cries at a sunset at 14:10. Wee Gordo puts his feet up.
  - **E3 NAP TIME**: the founder is asleep in the second vending machine in the clock room (it's been dispensing
    things in its sleep, including you). You pet it twelve times. It purrs, walks across the keyboard, types `zzzzzzzzzzzz`, and
    curls up on the Master Clock. Everything in the city slows, stops, and lies down: cops, shoppers, the Choir, Mr.
    Overtime (he gets a blanket). Credits roll over a city-wide nap. The cats are awake.
- **Credits**: rolled over a drive down the whole hill (you can drive; it's playable), with every NPC you met waving
  from the roadside.

**Side quest scenes:** every side questline gets a comic-panel opener and closer; big ones get a short cinematic
(Two Jesters gets three, because they insist).

### 8.4 Other story presentation
- **Mission start / end cards**: comic slam title ("MISSION: SAUCE RUN"), and an end card that grades you like a
  performance review ("MEETS EXPECTATIONS", "EXCEEDS", "SEE ME").
- **Phone calls**: NPCs call you on a ☺ Corp pager while you drive (comic bubble in the corner, babble voice).
- **Radio**: car radios have stations per district (Gut Choir FM, Pinstripe's crooner, mall muzak, Corp news that
  reads the Schedule) with DJs that comment on what you did ("someone stapled a guy to the fountain. traffic is
  fine.").
- **Billboards and TVs** in the world react to the story (wanted posters of you after Act I, Overtime's employee of
  the month ads, the ending's look).
- **The Chronicle**: the pause menu's story log, a scrapbook of comic panels unlocked as you play.
