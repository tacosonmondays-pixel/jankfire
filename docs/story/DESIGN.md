# JANKFIRE: OVERDUE (story mode design doc)

> **Logline:** ☺ CORP owns time. Everyone in Greater Jankburg is booked into the Schedule, down to the minute, and
> anything that runs late starts to *rot into meat*. You are an Unscheduled nobody, a returned mannequin who woke up in
> the Lost & Found with no calendar entry. Legally you don't exist. That makes you the only person in the city who can
> be late on purpose.

Working title **OVERDUE**. On the home screen it's the new **STORY** button. Everything here is original: genre ideas
(an open crime-sandbox city, rarity loot, cyber implants) are borrowed, and no names, characters, maps or art are.

Companion docs: [ART_BIBLE.md](ART_BIBLE.md) · [TECH_PLAN.md](TECH_PLAN.md) · [SLICE_PLAN.md](SLICE_PLAN.md)

---

## 1. The world and its rules

**Greater Jankburg** is the walled corporate city from the battle royale (`shared/jankburg.js`), finally zoomed out.
The BR city is just the middle: ten districts sprawl down a giant hill, Corp Hill at the top, The Bottom at the bottom,
because in this city the org chart is a map.

What players already know from the lore NPCs (`shared/secrets.js`) stays true: ☺ CORP started as one vending machine
that never gave change, bought the government at an auction, merged with everyone, and the founder is a cat who
typed `yyyyyyyyyyyy`. Respawning is in the benefits package (returned mannequins from the stockroom). Todd wrote gravity
from memory. The void is premium negative space. Story mode adds the thing underneath all of it:

### The Schedule
- After the merger, ☺ CORP bought **time**. Not clocks. Time. Every minute in the city is a licensed product.
- Every person, building, car and pigeon has a slot in **the Schedule**, run by the **Master Clock** at the top of the
  ☺ Spire. You are where your calendar says, when it says. Lunch is 11:57 to 12:03.
- **Lateness rots reality.** Anything that falls behind schedule goes *overdue*: first it gets sticky, then it gets
  warm, then it gets a pulse. Overdue paperwork grows teeth. Overdue streets grow intestines. A whole district that
  missed its deadline forty years ago is now **The Gut**: a living, digesting neighbourhood.
- Corp's whole religion is **staying ON TIME**. The higher up the hill, the more punctual, clean and plastic it is.
  The further down, the later, fleshier and more alive.
- **Late Fees** are how the Corp punishes lateness (the wanted level, see §6.2). Pay them, or outrun them.

### The Unscheduled
- People who fell off the Schedule (fired, lost, too poor for a calendar) become **the Unscheduled**. Time doesn't
  officially apply to them, so neither do Corp laws. Most hide at **The Bottom**.
- **You** are one: a mannequin body returned to the stockroom with a missing receipt. You were never booked in. You
  have no meetings. That is illegal.
- Being unscheduled is why you can do things nobody else can: respawn without paperwork, install organs that aren't
  yours, and stand in places that are overdue without rotting (much).

### Rules of the world (gameplay-facing)
| rule | what the player feels |
|---|---|
| Time is owned | a **City Clock** in the HUD. Corp districts run on it (shops open, patrols on rounds, trains on time). |
| Lateness rots | overdue zones are fleshy, hostile and lucrative. The Gut is permanently overdue; other districts rot at night and when you cause chaos. |
| Momentum never ends (Todd) | all existing movement (bhop, slide, grapple, infinite momentum) works city-wide. Cars keep it too. |
| Respawning is a benefit | death = wake up at the last safehouse in a fresh mannequin, minus some cash ("restocking fee"). |
| The board are cats | the cats are still hidden across the city. Petting them = promotions (perk points). |

---

## 2. Factions

### The big two
**☺ CORP** (top of the hill). Smiling, punctual, plastic. Wants the Schedule kept at any cost because a late city is a
city they can't bill. Departments the player meets:
- **Timekeeping Enforcement** (police, collectors, Mr. Overtime)
- **HR** (special forces, and the Tall Guy From HR)
- **Facilities** (cleaners who scrub the meat back to plastic with industrial bleach cannons)
- **Marketing** (Mr. Smiles' replacement, a mascot that's 90% mouth)

**THE BOTTOM** (bottom of the hill). The Unscheduled, the fired, the overdue. Stacked pastel houses, tie-dye, jury-rigged
everything. They don't want to rule time, they want to *get up* the hill. Leaders:
- **Auntie Spreadsheet**, ex-accountant, runs the Lost & Found hub, keeps the Bottom's books in crayon.
- **Lumps**, a huge rubber-faced man with enormous veiny forearms and a lot of gold rings, the Bottom's muscle. Gentle.
  Cries at sunsets. Sunsets are on the Schedule so he's always crying at 19:42 exactly.
- **Wee Gordo**, small, hunched, sagging lipped face, spiky hair, pink sweater. Lumps' best friend and the actual brains.

### District factions
| faction | district | wants | attitude to you |
|---|---|---|---|
| **The Gut Choir** | The Gut | to be digested into the city's big warm stomach and finally rest | friendly-creepy; they sing at you |
| **The Fazzoletti Family** | Pinstripe | protection money, respect, spaghetti | business partners or targets |
| **Mall Security & the Forever Shoppers** | The Checkout | sales, eternally | hostile in sales, neutral otherwise |
| **The Remainders** | Number Works | to be counted | grumpy union workers |
| **Meat Mechanics** | Chrome Gristle | your organs, ideally for money | merchants (implant clinics) |
| **The HOA** | Evergreen Acres | nobody different, ever | passive-aggressive, then aggressive |
| **The Loopers** | The Lates | for it to stop being Tuesday | confused, helpful |
| **The Margin Walkers** | The Margins | to keep the void from eating more ground | lonely, grateful |

### The player
- No name (the HUD calls you **UNSCHEDULED #0000**; other NPCs give you nicknames based on what you do: "sauce
  boy", "the late one", "that freak with the stomach").
- Customisable in the existing outfit/cosmetics system, plus implants that visibly change your body.
- Silent-ish: you pick dialogue options (the existing lore-NPC dialogue tree format), never voiced.

---

## 3. The main story

Five acts, ~25 main missions, each one an excuse for set pieces. Choices along the way tilt **Corp Standing** and
**Bottom Standing** (two hidden meters), which pick the ending in Act V.

### Act I: "Missing Receipt" (The Bottom, The Gut)
1. **Return to Sender.** You wake in a returns bin at the Lost & Found. Auntie Spreadsheet stamps you UNSCHEDULED and
   gives you Bread (tutorial: melee, movement, grapple on the washing lines).
2. **Sauce Run.** Lumps needs a car. You learn to steal one (car basics) and drive soup to the Gut border.
3. **Something's Digesting.** The Gut is spreading: a street in the Bottom grew a tongue. Go into the Gut, meet the
   Gut Choir, find out the Corp is *dumping late people* into it to keep their own schedules clean.
4. **Clocking In.** Corp sends **Mr. Overtime** to collect the Bottom's Late Fees. First nemesis fight (see §5) on the
   Gut border. You crack his punch-clock heart, he retreats, a piece of it falls out: your first **organ core**.
   ("THAT'S A HEART. YOU CAN'T JUST HAVE A HEART." "watch me.")
5. **Second Stomach.** A Meat Mechanic installs the core. Implants unlocked. The Bottom now believes you're useful.

### Act II: "Networking" (Pinstripe, The Checkout, Number Works)
The Bottom needs allies and money to go up the hill. Three districts, any order:
- **Pinstripe:** get the Fazzoletti Family to fund the Bottom. They want you to collect protection money... from the
  Corp. Ends in a fight with **Don Grinaldi**.
- **The Checkout:** the Mall holds a Black Friday that has lasted since 1999. Rescue the Bottom folks trapped in the
  queue. Boss: **The Cart Mother**.
- **Number Works:** steal a Schedule printout (the city's whole timetable, 9 km of paper). Boss: **Foreman Remainder**.
- Mid-act twist: Mr. Overtime ambushes you on the freeway (second nemesis fight, a vehicle chase).

### Act III: "Off the Clock" (Chrome Gristle, Evergreen Acres, The Lates)
With the printout, Wee Gordo finds a hole: the Schedule has a **missing hour** at 03:00 every night that nobody is
booked into. The Bottom plans to sneak an army up the hill during the Missing Hour.
- Recruit the Meat Mechanics (Chrome Gristle), sabotage the HOA's curfew (Evergreen Acres), and go to **The Lates**,
  where it's been Tuesday for 40 years, to find out what the Missing Hour is.
- **The twist:** the Missing Hour is where the Corp stores all the lateness it scrubs out of itself. It's a sealed
  tank of overdue time, and it's *the Gut's food*. The Gut isn't spreading on its own. The Corp's been feeding it.
  And the Corp has been feeding it *people*.
- Mr. Overtime fight 3, in the Lates: a time-loop arena where his punches arrive before he throws them.

### Act IV: "Quarterly Review" (The Margins, Corp Hill)
- The Missing Hour raid. The Bottom climbs the hill at 03:00. Mass battle up Dividend Road with the Bottom's people,
  cars and a Wrecking Ball.
- At the Margins you learn the void isn't repossessing ground at random: it eats **unscheduled** things. The Corp
  plans to unschedule the Bottom completely and let the void take it.
- You reach the ☺ Spire. **The Twins** (VP of Synergy) block the elevator.
- Choice point: Auntie Spreadsheet asks you to blow up the Master Clock; the Corp's Chief Punctuality Officer offers
  you a calendar, a name and a dental plan if you hand over the Bottom's leaders. You can also do neither.

### Act V: "Overdue" (the Master Clock), three endings
Final fight: **Mr. Overtime, Fully Billable**, wired into the Master Clock, in a clock tower made of gears, office
furniture and an enormous beating meat pendulum. Which side helps you depends on your choice.

| ending | how | what happens | epilogue line |
|---|---|---|---|
| **ON TIME** (Corp) | hand over the Bottom; kill Overtime and take his job | you get scheduled. You become the new Mr. Overtime: your punch-clock heart ticks in the HUD. The Bottom is unscheduled and the void moves in. The city is perfectly clean and perfectly empty. | "congratulations on your promotion. your first meeting was yesterday." |
| **LATE** (Bottom) | smash the Master Clock with the Bottom | time stops being owned. Every district goes overdue at once and the whole city grows a pulse. It's horrifying and warm and everyone is finally free to be late. The Bottom moves up the hill. | "nobody knows what time it is. lumps is crying at a sunset. it's the wrong time for it. he's thrilled." |
| **NAP TIME** (neither) | find the founder (a cat) in the clock room, pet it 12 times | the founder lies down on the Master Clock's keyboard and types `zzzzzzzzzzzz`. Legally that's a nap. Time is suspended for everyone equally: no Corp schedule, no rot. | "the board has entered a meeting. the meeting is a nap. it will run late." |

After any ending the city stays open (post-game), with the ending's look applied (the LATE ending turns fleshy
cosmetics on in every district; ON TIME makes everything bleach-white and cops are friendly to you; NAP TIME puts a
sleeping cat on every roof).

---

## 4. The districts

Ten districts, laid out down a hill (top to bottom): Corp Hill → Chrome Gristle / Evergreen Acres / Number Works →
The Checkout / Pinstripe → The Lates / The Margins → The Gut → The Bottom. The BR's Jankburg districts are folded in:
Corp Hill stays Corp Hill, Neon Market becomes Chrome Gristle, Number Works stays, Liberal Lane becomes Evergreen Acres,
Overdraft Heights slides down to The Bottom.

Every district has a **traversal gimmick** (a rule it bends, like the BR POIs) and a **boss** who drops an **organ core**.
Bosses are **refightable**: the Corp re-hires them. A beaten boss's arena shows a "POSITION REFILLED" sign after the
next in-game midnight; walk in for a rematch with harder mods and another core roll.

### 4.1 The Bottom (slum / rebel hub, the starting district)
- **Theme:** the bottom of the org chart. Where the Unscheduled live, stacked on top of each other.
- **Look:** a steep street of stacked pastel cube houses (pink, yellow, teal, mint), washing lines, satellite dishes made
  of woks, stairs everywhere, tie-dye banners, string lights, a dark purple sky that's always slightly the wrong time.
- **Landmarks:** the **Lost & Found** (hub safehouse, a giant returns depot), **The Long Stairs** (1,000 steps up to the
  Gut border), **Lumps' Gym** (all the weights are fridges), the **Down Escalator** (it's broken; it only goes down).
- **Faction:** The Bottom. **NPCs:** tie-dye locals, kids on scooters, mannequin returns with odd limbs, street
  cooks, a guy who sells one shoe.
- **Side quests:**
  - *Lost Property*: return 10 items from the Lost & Found to people all over the city (one is a whole bus).
  - *Leg Day*: help Lumps train by carrying fridges up the Long Stairs; drop one and it rolls all the way down.
  - *Wok the Dish*: fix the satellite wok-dishes by grappling between roofs during a storm.
  - *One Shoe Guy*: find the other shoe. It's in the Gut. It's alive now.
- **Boss: THE LANDLORD (Mr. Deposit).** A gigantic rubber-faced man made of stuffed armchairs and keys, who lives in the
  biggest house and keeps everyone's deposits in his body. Gimmick: he swallows your weapons when he hits you (you get
  them back by hitting his "deposit box" belly); he raises the rent mid-fight (the arena floor shrinks). 
  **Core: Deposit Gland** (Guts slot): 30% of damage you take is held and refunded as healing 5 s later.
  *Downside:* if you die before the refund, the Landlord keeps it (you respawn with less cash).
- **Traversal gimmick:** **Washing-line ziplines.** Every washing line is a grapple rail; slide along it at speed, drop
  socks as you go.
- **Music:** lo-fi hip hop played on a broken accordion, a warm bass, distant dogs.

### 4.2 The Gut (the living meat/organ district)
- **Theme:** a district that went overdue forty years ago and became alive. It digests. It's warm. It loves you.
- **Look:** streets are intestine tubes with pink ribbed walls, ribcage arches over the avenues, tooth-cobble
  pavements, lungs inflating between buildings, the old shops still visible under skin (a launderette with a tongue for
  a door), vein-wires carrying light, pulsing sphincter doors. Colours: raw pink, liver purple, fat yellow, bile green.
- **Landmarks:** **The Big Stomach** (the district's heart, a crater of churning acid lake), **Peristalsis Avenue**
  (the moving street), **The Choir Lung** (a cathedral that breathes), **Tooth Market** (everything costs teeth).
- **Faction:** The Gut Choir. **NPCs:** robed choir singers with puppet faces stretched into permanent smiles, "digesters"
  (half-absorbed people grown into the walls, still chatting), wandering stomach-dogs, a few normal people lost on
  their way to work.
- **Side quests:**
  - *Reflux*: the acid lake is rising. Plug burping vents with cars.
  - *Hairball*: something is stuck in Peristalsis Avenue. It's a guy's whole house. Push it through.
  - *Choir Practice*: the Choir needs a tenor. Collect three voice boxes from overdue Corp offices.
  - *Wisdom Tooth*: pull a giant tooth out of the Tooth Market square with the lasso and a car.
  - *Belly Button*: there's a door in the Big Stomach. Don't press it. (You press it.)
- **Boss: THE STOMACH BISHOP.** The Choir's leader: a tall, pale, smiling priest whose robes are one big stomach,
  conducting the district with a femur baton. Phase 1 he fights in the acid lake on a raft of tongues; phase 2 he
  swallows the arena and you fight *inside him* while the walls contract on a rhythm (peristalsis beats); phase 3 he's
  just a mouth. **Core: Second Stomach** (Guts slot): hold F on any dropped weapon to eat it for HP (rarer = more HP).
  *Downside:* you burp loudly every 30 s and give away your position; eating three in a row makes you vomit your
  current weapon.
- **Traversal gimmick:** **Peristalsis.** Certain streets contract in waves and carry you along like a conveyor (huge
  speed if you slide in on the beat). Lungs are trampolines. Intestine tubes are slides.
- **Music:** a choir humming one chord, a giant heartbeat as the kick drum, wet synth pads.

### 4.3 Pinstripe (the mafia district)
- **Theme:** an old-money neighbourhood run by a family of grotesque puppet-faced giants who think they're elegant.
- **Look:** gothic stone mansions, marble floors, red-and-white pinstripe awnings, gold medallions, velvet ropes,
  spaghetti restaurants with checkerboard floors (red, blue, black), pink stucco interiors.
- **Landmarks:** **Villa Fazzoletto** (the Don's house, a cathedral of marble and meatballs), **The Sauce Works**
  (the family's front business, a sauce factory with a red river), **Respect Bridge**, the **Bocce Pit**.
- **Faction:** The Fazzoletti Family. **NPCs:** huge pinstriped puppet goons with stretched faces and tiny hands,
  tiny accountants with huge heads, jesters (the family keeps two court jesters, see Art Bible), restaurant waiters
  who are only arms.
- **Side quests:**
  - *Wet Work*: deliver laundry. Actual laundry. They're very clean.
  - *The Meatball Run*: a meatball the size of a car got loose on Respect Bridge. Roll it home.
  - *Two Jesters*: the Don's jesters, **Pip Grinsworth** (short, giant horned head, needle teeth) and **Long Larry**
    (tall, lilac, droopy nose), want you to prank a rival family. Every prank is a weapon gimmick.
  - *Protection*: collect protection money from the Corp's tax office. With a minigun.
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
- **Theme:** a mall that ate the neighbourhood. Black Friday has been running since 1999.
- **Look:** the Dead Mall scaled up: escalators between streets, fountains with coins, food courts the size of plazas,
  sale banners, mannequin shoppers in every window, neon SALE signs in pink and yellow. Clean on top, gross in the
  service corridors.
- **Landmarks:** **The Infinite Queue** (a queue that winds around the district 14 times), **Food Court Colosseum**,
  **The Big Escalator** (2 km, goes up to Corp Hill, employees only), **Returns Desk Zero**.
- **Faction:** Mall Security (rent-a-cops on segways) and the **Forever Shoppers** (zombie consumers who stampede
  toward discounts).
- **Side quests:**
  - *Price Check on Aisle Everything*: scan 30 hidden barcodes with the Instant Camera.
  - *Doorbuster*: a 2-minute stampede survival. Shoppers trample anything between them and the TV.
  - *Mall Walker*: race the Mall Walkers' club of terrifyingly fast grandmas.
  - *Lost Child*: the lost child is 40 now. He's fine. He works here.
- **Boss: THE CART MOTHER.** Every lost shopping cart in the city, welded around a single furious shopper who never got
  her refund. She rolls, she stacks, she splits into a swarm of carts and recombines. The Shopping Cart Cannon is the
  counter (shoot carts into her to make her heavier and slower). **Core: Coupon Liver** (Guts slot): 15% of loot drops
  roll one rarity higher. *Downside:* you auto-buy the first thing you look at in any shop for 3 seconds. Spend wisely.
  Or don't look.
- **Traversal gimmick:** **Escalators.** Every escalator is a speed booster in one direction and a treadmill in the
  other. Cart surfing: ride shopping carts like skateboards.
- **Music:** mall muzak, slowed to half speed, with a cash register on every downbeat.

### 4.5 Corp Hill and the ☺ Spire (Corp HQ)
- **Theme:** the top of the hill. Perfectly punctual. Perfectly plastic. Every second accounted for.
- **Look:** white and cyan glass towers, chrome, giant ☺ logos, pristine lawns cut to exactly 1 inch, public clocks on
  every corner all ticking in sync, huge LED schedules on building sides. Inside: grey-carpet open plan offices going
  on forever. People walk in sync.
- **Landmarks:** **The ☺ Spire** (HQ, with the Master Clock at the top), **The Cathedral of Shareholder Value**,
  **Dividend Road**, **The Smiling Fountain**, **The Punctuality Museum**.
- **Faction:** ☺ CORP. **NPCs:** mannequin office workers in sync, executives with tiny monitor heads, Timekeeping
  officers, cleaners with bleach cannons, the Marketing mascot.
- **Side quests:**
  - *Reply All*: an email that will doom the Corp is about to be sent. Chase it down the Spire's pneumatic tubes.
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
- **Theme:** the Neon Market went cyber-meat: the place to get organs installed, swapped, pawned and stolen.
- **Look:** narrow neon lanes, pink and cyan signs, noodle stalls, back-alley clinics behind hanging butcher curtains,
  chrome and gristle together (jars of eyes, mechanical hearts in shop windows), rain on the floor, always night.
- **Landmarks:** **Organ Pawn** (sell your organs, buy them back later at a markup), **Doctor Upsell's Clinic**,
  **Arcade Row**, the **Noodle Shrine**.
- **Faction:** Meat Mechanics. **NPCs:** surgeons with too many arms, customers in bandages, noodle chefs, chrome
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
- **Theme:** the factory that makes the numbers. All of them. Every price, score and time in the city is printed here.
- **Look:** yellow and black industrial yards, conveyor belts carrying giant numbers, smokestacks puffing digits,
  lucky 7s and unlucky 13s on everything, chunky friendly machines with faces.
- **Landmarks:** **The Smokestacks**, **The Remainder Pit** (where leftover numbers go), **The Big Calculator**
  (a building), **Prime Lane**.
- **Faction:** The Remainders (a union of leftover numbers, people stamped with the digits nobody wanted).
- **Side quests:** *Carry the One* (escort a giant 1 across the district), *Rounding Error* (find who's been stealing
  0.5s), *Divide by Zero* (don't).
- **Boss: FOREMAN REMAINDER.** A huge crane-armed foreman with a calculator face. Every hit on him rolls a number that
  becomes the damage (the BR's "lucky 7 / unlucky 13" rule), and he can multiply or divide the arena (spawning more
  of himself, smaller). **Core: Lucky Kidney** (Guts slot): crits deal x7. *Downside:* every 13th shot deals 13 damage
  to you.
- **Traversal gimmick:** **Conveyor belts** that keep their momentum on you, and giant digits you can ride.
- **Music:** a drum machine made of stamping presses, an accordion counting out loud.

### 4.8 Evergreen Acres (the too-nice suburb)
- **Theme:** the normal-looking district. Lawns, picket fences, sitcom families. It's the most horrifying place in the
  city because it's *fine*. (Liberal Lane's helpings and the Suburb map grow into this.)
- **Look:** perfect pastel houses, identical cars, sprinklers, a mannequin family waving in every window at the same
  time, a laugh track you can hear in the street.
- **Landmarks:** **The Cul-de-sac**, the **HOA Clubhouse**, **The Prize Pumpkin**, the **Community Pool** (it's deep).
- **Faction:** The HOA. **NPCs:** mannequin families, a mailman who never stops, BBQ dads, dogs that are really two
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
- **Theme:** a district that missed one deadline and has been stuck on the same Tuesday since. The Backrooms are its
  basement.
- **Look:** yellow wallpaper offices, flickering lights, empty car parks, identical streets that repeat, a clock tower
  with no hands, half-flesh carpet where it's started to rot.
- **Landmarks:** **The Waiting Room** (infinite, with chairs), **Tuesday Tower**, **The Backrooms Stairwell**.
- **Faction:** The Loopers (stuck people who've learned the loop by heart).
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
- **Theme:** the edge of the licensed play area, where the void repossesses ground every bad quarter. The Scary
  Forest grows here, and the Tall Guy From HR walks it.
- **Look:** dark pines, crumbling roads that end in nothing, houses half-eaten by a glossy black void, "PREMIUM
  NEGATIVE SPACE" billboards, foreclosure notices nailed to trees.
- **Landmarks:** **The Last Bus Stop**, **HR Cabin**, **The Edge** (a cliff into the void with a lifeguard tower).
- **Faction:** Margin Walkers (lonely people who stake ground to stop the void, with garden gnomes).
- **Side quests:** *Staking Claims* (plant gnomes to hold ground), *Lifeguard* (pull people out of the void with the
  lasso; they've lost the dental), *Exit Interview* (find out what the Tall Guy wants: it's a signature).
- **Boss: THE TALL GUY FROM HR** (refightable in the open world, not just the forest map). He's unkillable in his own
  forest, until you find his file in the HR Cabin. Gimmick: he only moves when you're not looking, and his arms are
  as long as he wants. **Core: Long Spine** (Spine slot): your melee range doubles and you're 30% taller.
  *Downside:* you're 30% taller. Doorways hurt.
- **Traversal gimmick:** **Void Edges.** Falling into the void respawns you at the nearest staked gnome (no death),
  keeping your momentum. Fall in on purpose.
- **Music:** a single drone, wind, a far-away music box playing the ☺ CORP jingle.

---

## 5. The nemesis: MR. OVERTIME

> Head of Timekeeping Enforcement. Employee #1. Has never been late. Has never left.

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
| 2 | the Spiral Freeway, Act II | *Rush Hour* | a car chase: he runs after your car (on time!), staples cars into barricades; fight from the car and on the roofs | he's left behind in traffic; you steal his lanyard (Corp access) |
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
- A day-night **City Clock** (1 game day = 48 real minutes). Shops, patrols, trains and some quests are on the clock.
  The Gut and the Lates don't care. At night the rot spreads: districts get fleshier, enemies tougher, loot better.
- Story missions are gated by act; districts open as the story reaches them (the Bottom and the Gut are open from the
  start; the rest open in Act II; Corp Hill's Spire opens in Act IV). You can wander into higher districts early,
  they're just Late Fees magnets.
- **Chaos is rewarded.** Spectacle kills, car crashes, flinging people off stairs and long grapples fill the **HYPE**
  meter, which powers killstreak items (§6.6).

### 6.2 Late Fees (the wanted level)
Crimes, chaos and being where your Schedule says you shouldn't be add **Late Fees**. Stars are drawn as little ☺ clock
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
bus (a clean schedule for a fee); or pay at a **Late Desk** (cash, price scales with stars). Killing Corp forces at
★5 is allowed and very loud. The Bottom's districts give a "nobody saw nothing" bonus (fees drain faster).

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
  | **Severance Package** | Shotgun | kills pay you 50 cash | "it's not personal. it's paperwork." |
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
- **Cash** (Corp dollars, "☺bucks") from loot, quests, side activities, selling junk, robbing. Containers (crates,
  bags, boxes) keep dropping as before for cosmetics.
- **Shops:** gun shops (rolled stock that refreshes at midnight), Meat Mechanics (implants, installs, uninstall fees),
  Tooth Market (pay in teeth), vending machines (shoot them), car dealers, outfit shops (the existing cosmetics).
- **Safehouses:** one per district, unlocked by a quest. Save point, stash locker, garage, wardrobe, bed (skip time).
  The Lost & Found is the first.
- **Saving:** autosave at safehouses, mission starts and boss kills; a manual save at safehouses. 3 save slots per
  account, stored server-side (TECH_PLAN §7).

### 6.9 Side activities
- **Cat Board Hunt:** the board of directors (cats) hide across the city. Pet them for promotions (+1 Body Budget).
- **Rampages:** "OVERTIME!" kill-frenzy challenges with a weapon the game hands you.
- **Delivery runs** in silly vehicles (soup van, ice cream van, a hearse full of balloons).
- **Races:** street, rooftop grapple races, cart races in the Checkout, peristalsis surfing in the Gut.
- **Arenas:** the existing multiplayer modes as "fight clubs" in each district (gun game in Number Works, Plant &
  Defuse in Pinstripe), against bots, with loot.
- **Stunt jumps** (huge ramps, MLG overlays), **graffiti** (sprays), **jobs** (taxi, repo man, Corp mail runner).
- **Lore NPCs:** Gary, Dale, the Janitor, Mr. Smiles and Todd all live somewhere in the city now, with new lines.

### 6.10 Co-op
- **Drop-in co-op** for 2-4 players. You can join a friend if your story progress is within one act of theirs (so
  nobody sees an ending they haven't earned). Otherwise you can still join them in **free roam**.
- **Mission sync:** the host's mission runs. Joiners get credit if they've unlocked that mission or earlier; if
  they're behind, they get a "temp contractor" credit (loot and cash, no story progress). Side quests credit everyone.
- **Loot:** instanced per player. Shared kills give everyone their own drops. Trading in a safehouse.
- **Boss refights:** everyone in the arena gets their own core roll. Boss HP scales with players (+60% per player).
- **Late Fees** are shared per group (one star count), and so is HYPE (shared meter, any player can use it).
- **Revives:** a downed co-op player can be revived ("paperwork processed") for 10 s before respawning at a safehouse.
- **Cars:** passengers shoot, drivers drive. A car fits 2-4 depending on model.

---

## 7. Tone guide (where the gross lives)

The owner wants it nasty: pulsing flesh, puppet faces, body horror, gore, intestines. **But not everywhere**, so it
hits harder when it shows up.

| zone | dial | what's there |
|---|---|---|
| The Gut, the Big Stomach, overdue offices, boss arenas | **10/10** | pulsing walls, intestine streets, half-digested people chatting, eyes in the floor, organ cores pulled out wet, gore and gibs on kills |
| Pinstripe, Chrome Gristle, The Bottom at night | **6/10** | puppet faces, stretched grins, jars of organs, implant surgery, the occasional twitching thing |
| The Lates, The Margins | **4/10, creepy** | liminal, wrong, quiet; rot creeping into the carpet; the Tall Guy |
| The Checkout, Number Works, The Bottom by day | **3/10, cartoon** | silly, bright, slapstick violence; mannequin shoppers |
| Corp Hill, Evergreen Acres | **1/10, too clean** | spotless and smiling, and *that's* the horror; blood gets bleached by cleaners within seconds |

- **Normal people** are everywhere: chunky low-poly folks with normal proportions. Most of the city is them.
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
| Mr. Overtime, Fully Billable | **MR. OVERTIME** · FULLY BILLABLE | "the meeting is now. the meeting is forever." |

### 8.3 The story's scene list
**C** = cinematic, **P** = comic panels, **B** = boss intro. About 40 scenes, ~35 minutes of cinematics in total.

**Act I: Missing Receipt**
- **C1 "Return to Sender"** (opening, 90 s). Black screen, the ☺ jingle. A conveyor in the Corp stockroom carries
  mannequins past a scanner: BEEP, BEEP, BEEP... *BOOP*. One has no receipt. A robot arm drops it down a chute
  marked RETURNS. It tumbles down the whole city (the title card flies past: **JANKFIRE: OVERDUE**), we see every
  district on the way down in one long fall (Corp Hill's clocks, Pinstripe's strings, the Gut breathing), and it lands
  in a returns bin at the Lost & Found. Auntie Spreadsheet looks into the bin. "huh. no receipt." *STAMP*:
  UNSCHEDULED. Your mannequin's wrong knee clicks into place. Control.
- **P2 "Sauce Run"** briefing: Lumps holds up a pot. Lumps holds up a car key. Lumps cries. Wee Gordo: "he means
  steal a car."
- **C3 "It's Breathing"** (40 s). Driving into the Gut for the first time: the camera pulls ahead of your car as the
  street turns from tarmac to pink skin, a rib arch rises overhead, the Choir turns its stretched faces to you all at
  once and starts humming.
- **C4 "Clocking In"** (60 s). The Bottom at 19:42. Lumps is crying at the sunset. Every clock in the Bottom stops.
  Ticking. Huge brogues step down the Long Stairs, crushing them. Mr. Overtime ducks under a washing line, takes out a
  clipboard. "the bottom. you are forty years late. i'm here to collect." He staples Lumps to a wall. → **B: MR.
  OVERTIME**.
- **Moment "Heart Rip"**: in slow-mo, you yank a piece of the punch-clock out of his chest. It's warm. It ticks.
- **C5 "Second Stomach"** (45 s). A Meat Mechanic clinic, a dentist's chair, a lamp swings. Auntie holds the core.
  "this is a terrible idea." The Mechanic: "you'll be fine." Cut to black. *SQUELCH*. *TICK*. You wake up with a clock
  ticking in your chest. Implants unlocked.

**Act II: Networking**
- **P6 "Meanwhile at ☺ CORP"**: Mr. Overtime in a boardroom of empty chairs and one cat. "a nobody. with my heart."
  The cat yawns. That's a yes.
- **C7 "An Offer"** (Pinstripe, 60 s). A checkerboard restaurant. Pip Grinsworth and Long Larry flank the door with
  praying hands. The Don leans down from the ceiling on his strings, his grin unfolding wider and wider. "you got a lot
  of heart. i heard it's not yours."
- **C8 "Doorbusters"** (Checkout, 40 s). The doors open at 09:00. 10,000 Forever Shoppers stampede in slow-mo; a
  single shopping cart rolls out of the dust towards you. Then another. Then all of them. → **B: THE CART MOTHER**.
- **P9 "Nine Kilometres"**: the Schedule printout unrolls down the Number Works' chimneys; Wee Gordo reads it and
  gasps. "there's an hour missing."
- **C10 "Rush Hour"** (45 s, opening a chase). The Spiral Freeway. Your car. In the mirror: Mr. Overtime, running,
  at exactly the speed limit. He checks his watch.

**Act III: Off the Clock**
- **C11 "The Missing Hour"** (90 s). The Lates. A clock tower with no hands. At 03:00 the world goes grey and silent
  and a door appears in the sky. Inside: a tank the size of a district, full of glowing overdue time, and pipes going
  down the hill. Down to the Gut. Through the glass: people. "they're feeding it *us*."
- **P12 "Tuesday Again"**: the same panel four times. In the fourth, Mr. Overtime is already standing behind you.
- **C13 "Lumps' Speech"** (50 s). The Lost & Found, everyone from every district you helped. Lumps stands on a
  fridge. He cries. He says one word ("up."). Everyone cheers. Wee Gordo explains the actual plan.

**Act IV: Quarterly Review**
- **C14 "03:00"** (60 s). The Missing Hour. The Bottom marches up Dividend Road in silence, the sofa-cars, the Choir,
  the jesters, a Wrecking Ball on a chain. Corp Hill's clocks all turn to face them.
- **C15 "Negative Space"** (40 s). The Margins. A house slides into the void. The Tall Guy From HR hands you a
  folder: UNSCHEDULING ORDER: THE BOTTOM. He's sad about it. He's tall about it.
- **C16 "The Offer"** (60 s, the choice). The Spire's top floor. Two doors. Auntie Spreadsheet on a walkie: "blow it
  up." The Chief Punctuality Officer (a mannequin with a perfect smile and a lanyard to the floor) holds out a
  calendar with your name on it. A cat sleeps on the desk between them. The game asks you: **ON TIME**, **LATE**,
  or... (pet the cat).

**Act V: Overdue**
- **C17 "Fully Billable"** (60 s). The Master Clock opens like a ribcage. Mr. Overtime plugs his stapler arms into
  the gears, his suit tears, the meat pendulum swings. "your appointment is now." → **B: FULLY BILLABLE**.
- **Endings** (2-3 min each, the longest scenes in the game):
  - **E1 ON TIME**: you're issued a suit. The clock in your chest stops ticking and starts *keeping* time. A montage of
    the city getting scrubbed white, the Bottom's houses folding into the void one by one. Your first meeting. The
    chair has your name on it. It's already warm.
  - **E2 LATE**: the Master Clock bursts. Every clock in the city melts. A wave of pink flesh rolls down the hill (from
    the top this time), soft and warm. Corp workers look at their wrists and see nothing. One of them laughs. Lumps
    cries at a sunset at 14:10. Wee Gordo puts his feet up.
  - **E3 NAP TIME**: you pet the founder twelve times. It purrs, walks across the keyboard, types `zzzzzzzzzzzz`, and
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
