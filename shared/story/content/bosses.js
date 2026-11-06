// OVERDUE bosses. 20 named bosses (Mr. Overtime has four story fights and a refight, so 24 entries).
// Who they ARE is in the cast bible; this file is the fight.
// SCHEMA: BOSSES[id] = {
//   name, card, subtitle      the Boss Intro title card (DESIGN §8.2): NAME · JOB TITLE, and one deadpan subtitle
//   who        cast id           kind: 'nemesis' | 'story' | 'district' | 'world' | 'secret' | 'final'
//   district, arena (LOCATIONS id), quest (the mission or side quest it ends), unlock? (condition for world/secret bosses)
//   hp         base HP for one player (co-op: +60% per extra player, DESIGN §6.10)
//   look       body type per the art bible: 'puppet' | 'off-spec' | 'cyborg' | 'thing' + a line for the modeller
//   why        why they're here, in one or two sentences
//   phases     [{ name, hp: [from %, to %], line (said on entry), mechanics: [{ name, tell (what warns you), effect, counter }] }]
//   lines      { intro, hurt: [..], kill: [..] (when they kill you), low (under 20%), defeat }
//   defeat     the defeat scene (a Moment or a short talk)
//   core       the organ core it drops (implants.js id; quality rolls Bruised / Fresh / Prime / Premium)
//   refight    { mods: [..] (POSITION REFILLED rematch changes), line, card } (null = no refight)
//   drops      legendaries / loot tables / items it can drop
//   talk       optional mid-fight talk hook (a talk id in its quest)
// }

const REHIRE = "POSITION REFILLED";

export const BOSSES = {
  // ================================================================ MR. OVERTIME (the nemesis)
  overtime_1: {
    name: "MR. OVERTIME", card: "MR. OVERTIME · HEAD OF TIMEKEEPING", subtitle: "has never been late. has never left.",
    who: "overtime", kind: "nemesis", district: "gut", arena: "gut:border", quest: "m04_clocking_in", hp: 4200,
    look: "cyborg: the full nemesis model (cast bible), first fight version: pristine suit, polished brogues, the clock face glowing white.",
    why: "He came to collect two hundred and forty-four quarters of back pay from the Bottom, in people. Lumps stood in front of the truck.",
    phases: [
      { name: "COLLECTION", hp: [100, 50], line: "please form a queue.",
        mechanics: [
          { name: "Staple Gun", tell: "his right stapler arm clacks twice and the staple glows at the tip", effect: "a staple the size of a crowbar that pins you to a wall or the floor (mash jump to rip free); the staple stays as a grapple point", counter: "strafe on the second clack; use stuck staples to grapple up behind him" },
          { name: "Overtime Slam", tell: "he checks his watch, crouches, steam vents from his collar", effect: "a jump and slam; a ring of frozen time (2 s) spreads from the impact", counter: "bounce on the Gut border's lung trampolines to be in the air when the ring passes" },
          { name: "Fines", tell: "he licks a thumb and peels a sheet off his clipboard", effect: "paper fines that stick to your screen (HUD cover) for 4 s", counter: "melee to tear them off, or shoot them out of the air" },
        ] },
      { name: "COFFEE BREAK", hp: [50, 45], line: "i'm on my break. this is my break.",
        mechanics: [
          { name: "Coffee Break", tell: "at half HP he stops, sits on the stairs and pours coffee from a flask", effect: "15 s of free hits on the clock face (crits); his collectors keep loading the truck behind him", counter: "go all in on the clock; or stop the collectors (a few fewer people end up in the truck: cosmetic only, the nine are always taken)" },
        ] },
      { name: "PUNCHING IN", hp: [45, 0], line: "break's over. you're all on the clock now.",
        mechanics: [
          { name: "Punch In", tell: "both arms open wide and the chest slot whirs open", effect: "the grab: you're shoved into his chest slot and 'scheduled' (a 3 s timer; at 0 you take a big hit)", counter: "shoot the clock face from inside to be spat out; dash sideways when the slot opens" },
          { name: "Staple Fan", tell: "both arms raised, ten clacks", effect: "a fan of five staples", counter: "slide under it" },
        ] },
    ],
    lines: { intro: "this will only take a minute. it will take exactly a minute.", hurt: ["that's company property.", "please don't touch the clock.", "you're damaging the schedule."], kill: ["processed.", "that's one."], low: "this is very irregular.", defeat: "this isn't finished. it's rescheduled." },
    defeat: "The Heart Rip moment (mo_heart_rip): you tear a piece of the punch-clock out. He checks his watch and retreats up the Long Stairs, exactly on time, a little lopsided.",
    core: "core_cracked_punch_clock", refight: null, drops: ["lt_boss_overtime_1"],
  },
  overtime_2: {
    name: "MR. OVERTIME", card: "MR. OVERTIME · HEAD OF TIMEKEEPING", subtitle: "he's not speeding. you are.",
    who: "overtime", kind: "nemesis", district: "commute", arena: "commute:spiral_freeway", quest: "m13_rush_hour", hp: 6000,
    look: "cyborg: a steel plate over the chest wound from fight 1, bungee tie streaming, running upright like a man late for a train.",
    why: "Now he knows your name. He chases your car up the Spiral Freeway on foot, at exactly the speed limit.",
    phases: [
      { name: "IN PURSUIT", hp: [100, 60], line: "please pull over. you're in breach of your schedule.",
        mechanics: [
          { name: "Barricade", tell: "he veers to the edge and his arm swings back toward a dead car", effect: "staples a dead car across the lane ahead of you", counter: "boost through the gap he leaves, or ramp off the car (cars keep momentum)" },
          { name: "Speed Limit", tell: "a road sign whips past", effect: "he always runs at exactly your speed when you're above the limit, and at the limit when you're below it", counter: "drop below the limit to make him overtake you, then hit him from behind; or use the paper storm to break his line" },
          { name: "Windscreen", tell: "he leaps onto a car roof beside you", effect: "Punch In through your windscreen (he grabs you out of the car)", counter: "handbrake turn; the grab misses and he skids" },
        ] },
      { name: "ROOFTOPS", hp: [60, 25], line: "you'll have to get out of the car. that's policy.",
        mechanics: [
          { name: "Jam Slam", tell: "the jam ahead shakes; car alarms start in a ring", effect: "slams the traffic jam: cars bounce into the air", counter: "get out and fight on the bouncing car roofs (Jams traversal); staples stuck in cars are grapple points" },
          { name: "Fines", tell: "paper storm thickens", effect: "fines stick to the screen; in the storm they come from every side", counter: "melee them off" },
        ] },
      { name: "LEFT BEHIND", hp: [25, 0], line: "i'm never late. i'm never... when was that?",
        mechanics: [
          { name: "Tangle", tell: "he grabs a city bus to stop it", effect: "he staples himself to it by mistake; a stationary target for 10 s", counter: "drive past and rip the lanyard off him (a prompt as you pass)" },
        ] },
    ],
    lines: { intro: "please pull over.", hurt: ["that's a moving violation.", "please keep both hands on the wheel."], kill: ["pulled over.", "processed."], low: "you were in the lobby. you were running.", defeat: "...when was that?" },
    defeat: "Left in the jam, half under a bus. You yank the lanyard off as you pass. His first glitch: 'you were in the lobby. you were running. ...when was that?'",
    core: "core_rush_hour_lung", refight: null, drops: ["lt_boss_overtime_2", "unpaid_overtime"],
  },
  overtime_3: {
    name: "MR. OVERTIME", card: "MR. OVERTIME · HEAD OF TIMEKEEPING", subtitle: "you've seen this one. so has he.",
    who: "overtime", kind: "nemesis", district: "lates", arena: "lates:waiting_room", quest: "m25_tuesday_again", hp: 8000,
    look: "cyborg: suit scorched, static on the visor, his movements stutter like a skipping tape. A torn time card in his chest slot.",
    why: "He came through the door at 03:00 for the first time. He's been doing the same slam in a car park for six hours. He's waiting for you.",
    phases: [
      { name: "LOOP ONE", hp: [100, 75], line: "this will only take a minute.",
        mechanics: [
          { name: "Remembered", tell: "a ghost of you from the last loop flickers where you stood", effect: "every 60 s the arena loops; his attacks are aimed where you were last loop (telegraphed by your own ghost)", counter: "don't repeat yourself: move somewhere new each loop" },
          { name: "Staple Gun / Slam / Fines", tell: "as fight 1", effect: "his whole moveset, faster", counter: "as fight 1" },
        ] },
      { name: "LOOP TWO", hp: [75, 50], line: "this will only... this will only take...",
        mechanics: [
          { name: "Replay", tell: "your bullets from the last loop hang in the air as faint lines", effect: "your past shots replay; they hit him again (and you, if you stand in them)", counter: "set up crossfires for your future self" },
          { name: "Glitch Step", tell: "his outline doubles", effect: "he skips 3 m forward like a tape jump", counter: "back off when he doubles" },
        ] },
      { name: "LOOP THREE", hp: [50, 20], line: "june's making the... june's making...",
        mechanics: [
          { name: "Wrong Slam", tell: "he slams, but the time-freeze ring freezes him instead of you", effect: "a free stagger window every slam", counter: "punish the slam" },
          { name: "Staple Rain", tell: "the ceiling fills with staples", effect: "a rain of staples across the car park", counter: "stand under the parked cars" },
        ] },
      { name: "LOOP FOUR", hp: [20, 0], line: "i was going home at 17:30.",
        mechanics: [
          { name: "Stop", tell: "he stops attacking", effect: "P16: he stands still and asks why he didn't go home; the fight ends in a talk (m25 'home')", counter: "talk to him" },
        ] },
    ],
    lines: { intro: "you're late.", hurt: ["that's... that's company...", "please hold... please..."], kill: ["processed. again.", "you've seen this one."], low: "why didn't i go home?", defeat: "i have to... i have an appointment." },
    defeat: "He stops. P16. The car park talk. His time card is torn down the middle: Late Fees can't reach ★5 until Act IV.",
    core: "core_deja_vu_lobe", refight: null, drops: ["lt_boss_overtime_3"],
  },
  overtime_4: {
    name: "MR. OVERTIME", card: "MR. OVERTIME · FULLY BILLABLE", subtitle: "the meeting is now. the meeting is forever.",
    who: "overtime", kind: "final", district: "corphill", arena: "corphill:master_clock", quest: "m31_fully_billable", hp: 16000,
    look: "cyborg: suit in tatters, cables from the Master Clock into his back, stapler arms driven into the gears; the clock in his chest is huge and cracked; he's a part of the Clock now.",
    why: "Hask told him that if the Clock restarts, everyone who's absent comes back on time. Including June.",
    talk: "processing",
    phases: [
      { name: "SLOW MOTION", hp: [100, 66], line: "your appointment is now.",
        mechanics: [
          { name: "Clock Speed: Slow", tell: "the pendulum swings slowly and the music drops a fifth", effect: "the whole arena runs at 50% speed; his staples are huge and slow; the gears are platforms that crawl", counter: "climb the gears; grapple to the pendulum; read everything" },
          { name: "Gear Teeth", tell: "a gear's teeth glow red", effect: "that gear crushes anything between its teeth on the next tick", counter: "jump on the tick sound" },
          { name: "Staple Gun", tell: "as before, giant", effect: "staples pin you to the gears, which carry you toward the teeth", counter: "mash free; use the staple as a grapple" },
        ] },
      { name: "FAST FORWARD", hp: [66, 33], line: "we're behind. we're so behind.",
        mechanics: [
          { name: "Clock Speed: Fast", tell: "the pendulum blurs and the music doubles", effect: "the arena runs at 150%; he attacks in bursts; your HYPE fills twice as fast", counter: "use streak items now (they're cheaper in fast time)" },
          { name: "Overtime Slam", tell: "he rips his arms out of the gears and leaps", effect: "a slam that freezes a ring of gears (the freeze ring is now a 5 m platform of stopped time you can stand on)", counter: "stand on the frozen ring: it's safe from the teeth" },
          { name: "Punch In: Processing", tell: "both arms open; the chest slot glows", effect: "at the end of this phase he always lands the grab and holds you at the slot: the 'processing' talk (the talk-down chance)", counter: "talk" },
        ] },
      { name: "OVERDUE", hp: [33, 0], line: "you're absent. everyone's absent. i don't know where everyone goes.",
        mechanics: [
          { name: "Every Clock", tell: "every clock face in the gearwork lights at once", effect: "the clock speed switches every 8 s, slow, fast, slow; the arena collapses gear by gear toward the heart", counter: "keep to the frozen rings; crit the chest" },
          { name: "Coffee Break (broken)", tell: "he reaches for a flask that isn't there", effect: "a 4 s stagger, once", counter: "free crits" },
        ] },
    ],
    lines: { intro: "your appointment is now.", hurt: ["company prop...", "june?"], kill: ["processed. processed. processed.", "you're absent."], low: "i've been holding the door.", defeat: "that's the end of my shift." },
    defeat: "Talked down (all six fragments): C22, he clocks out and gives you Cale's tape. Destroyed: his punch-clock stops, his visor goes dark, and the tape falls out of his chest slot.",
    core: "core_master_spring", refight: null, drops: ["lt_boss_overtime_4", "time_and_a_half"],
  },
  overtime_rehire: {
    name: "MR. OVERTIME", card: "MR. OVERTIME · REHIRED", subtitle: "he's been rescheduled.",
    who: "overtime", kind: "nemesis", district: "corphill", arena: "corphill:museum", quest: "sq_corphill_punctuality_museum", unlock: "done:m13_rush_hour", hp: 9000,
    look: "cyborg: a fresh body from the spares, the suit still creased from the packaging, a REHIRED sticker on the lapel.",
    why: "After Act II, ☺ CORP keeps printing new ones. The newest stands in the Punctuality Museum's main hall among exhibits about being on time, and he's also the ★5 Late Fees boss in the open world.",
    phases: [
      { name: "EXHIBIT A", hp: [100, 50], line: "please don't touch the exhibits.",
        mechanics: [
          { name: "The Full Moveset", tell: "as fights 1-3, rolled at random per rehire", effect: "staples, slam, fines, punch in, coffee break", counter: "as before" },
          { name: "Exhibits", tell: "a glass case lights up", effect: "he activates a museum exhibit: 'THE FIRST TIME CARD' (a giant card that sweeps the floor), 'THE PENDULUM OF PUNCTUALITY' (a swinging hazard), 'LATENESS THROUGH THE AGES' (mannequins of late people that block you)", counter: "smash the case first" },
        ] },
      { name: "EXHIBIT B", hp: [50, 0], line: "this is a historic moment. it will be exactly a moment.",
        mechanics: [
          { name: "Rehire Mods", tell: "the REHIRED sticker flashes", effect: "two random mods from the refight list", counter: "varies" },
        ] },
    ],
    lines: { intro: "welcome to the punctuality museum. you're late.", hurt: ["that's a priceless exhibit.", "please use the gift shop."], kill: ["exhibit closed.", "processed."], low: "i've been here before. haven't i.", defeat: "rescheduled." },
    defeat: "He walks into the exhibit case marked EMPLOYEE #1 and stands still. Next midnight: POSITION REFILLED.",
    core: "core_cracked_punch_clock",
    refight: { card: REHIRE, line: "i've been rehired. i don't remember being fired.", mods: ["Double Shift: two Overtimes, half HP each", "Unpaid: no coffee break", "Mandatory Meeting: the arena doors lock and the timer is 3:00", "Rush Hour: the whole fight on the museum's moving walkways", "Fully Staffed: Punctuality Officers join every 30 s"] },
    drops: ["lt_boss_overtime_rehire", "unpaid_overtime"],
  },

  // ================================================================ THE BOTTOM
  landlord: {
    name: "MR. DEPOSIT", card: "MR. DEPOSIT · THE LANDLORD", subtitle: "you're not getting it back.",
    who: "mr_deposit", kind: "district", district: "bottom", arena: "bottom:landlord_pile", quest: "sq_bottom_deposit", hp: 5000,
    look: "off-spec: a gigantic rubber-faced man grown into a mound of stuffed armchairs and keys, a brass deposit box for a belly.",
    why: "Vacancy's last agent in the Bottom, collecting deposits on a pile of rubble for fifty years. He keeps them in his body. He's never returned one.",
    phases: [
      { name: "VIEWING", hp: [100, 60], line: "welcome! characterful. cosy. a small admin charge.",
        mechanics: [
          { name: "Deposit", tell: "the deposit-box slot in his belly opens with a cash-register ding", effect: "when he hits you, he swallows the weapon in your hand (it drops into the box)", counter: "hit the box (glowing slot) to make it spit your weapon back; switch to melee when the slot opens" },
          { name: "Armchair Roll", tell: "the mound rocks back and forth three times", effect: "he rolls an armchair at you like a boulder", counter: "jump it; or catch it with the lasso and sling it back" },
        ] },
      { name: "RENT INCREASE", hp: [60, 25], line: "the rent's gone up. no, i didn't do it. the market did it. i'm the market.",
        mechanics: [
          { name: "Rent Increase", tell: "a bell rings and a sign drops: RENT INCREASE", effect: "the edges of the arena fall away (the floor shrinks) every 20 s", counter: "fight in the middle; ride the Bottom's washing lines around the pile" },
          { name: "Key Rain", tell: "jingling above", effect: "thousands of keys rain down", counter: "stand under the washing (it catches them)" },
        ] },
      { name: "EVICTION", hp: [25, 0], line: "*wheeze* i can't get up. i don't need to get up.",
        mechanics: [
          { name: "Sit Down", tell: "the armchairs sag", effect: "he sinks into the pile; only the deposit box is hittable, and it swallows anything you throw at it", counter: "throw in a live grenade" },
        ] },
    ],
    lines: { intro: "you're not getting it back, tenant.", hurt: ["that's coming out of your deposit.", "wear and tear!"], kill: ["evicted.", "deposit kept."], low: "the deposit. not the deposit.", defeat: "*a cascade of coins, keys, a shoe, and one live pigeon*" },
    defeat: "His box bursts: fifty years of deposits shower the Bottom (every NPC in the district gets coupons and says thank you). He sits in the rubble, finally able to stand up. He doesn't.",
    core: "core_deposit_gland",
    refight: { card: REHIRE, line: "vacancy's re-let me. i'm under new management. it's me.", mods: ["Furnished: twice the armchairs", "Bills Included: the arena floor shrinks from both sides", "Damp: the floor is slippery", "Guarantor: Mr. Deposit's cousin (a smaller Mr. Deposit) joins at 50%"] },
    drops: ["lt_boss_landlord", "the_deposit"],
  },

  // ================================================================ THE GUT
  bishop: {
    name: "THE STOMACH BISHOP", card: "THE STOMACH BISHOP · GUT CHOIR", subtitle: "he's already digesting you. spiritually.",
    who: "bishop", kind: "story", district: "gut", arena: "gut:big_stomach", quest: "m20_the_missing", hp: 11000,
    look: "off-spec: a tall pale smiling puppet priest whose robe is one big stomach, conducting with a femur baton; 10 m tall in phase 2's interior.",
    why: "The Choir's song holds the Gut together, and holds the Bottom's missing in the wall. To free anyone, the song has to stop.",
    phases: [
      { name: "COMMUNION", hp: [100, 65], line: "welcome to the body. we've been expecting you. we're always expecting.",
        mechanics: [
          { name: "Tongue Raft", tell: "he stands on a raft of tongues in the acid lake; the lake bubbles where he points", effect: "acid geysers where his baton points", counter: "keep moving on the floating organs; shoot the baton hand to stun" },
          { name: "Hymn", tell: "the Choir on the crater rim takes a breath", effect: "the Choir sings: a sound wave that pushes you toward the acid", counter: "duck behind the rib pillars; kill rim singers (they're people: they get up again, unhurt, afterwards)" },
          { name: "Communion", tell: "he raises a goblet", effect: "heals himself from the lake", counter: "shoot the goblet" },
        ] },
      { name: "INSIDE", hp: [65, 25], line: "come in. come in. we are all one body.",
        mechanics: [
          { name: "Swallow", tell: "his robe opens like a mouth", effect: "he swallows the arena: you fight inside him; the walls contract on a rhythm (peristalsis beats)", counter: "move on the beat: slide on the contraction for huge speed" },
          { name: "Stomach Lining", tell: "a section of wall pulses yellow", effect: "acid floods that section", counter: "use the lung trampolines" },
          { name: "Weak Points", tell: "glowing pink ulcers", effect: "the only places he takes damage inside", counter: "hit all four ulcers to be spat out" },
        ] },
      { name: "JUST A MOUTH", hp: [25, 0], line: "blessed are the overdue. for they shall be... absorbed...",
        mechanics: [
          { name: "Mouth", tell: "his whole body becomes a giant mouth on the lake", effect: "it inhales: a strong pull toward the teeth", counter: "grapple outward against the pull; feed it a grenade" },
        ] },
    ],
    lines: { intro: "you look delicious. spiritually.", hurt: ["that was a sacrament.", "growth hurts. growth always hurts."], kill: ["absorbed.", "welcome to the body."], low: "father?", defeat: "the song... someone stopped the song..." },
    defeat: "The Choir stops mid-note for the first time in sixty years. In the silence you can hear the digesters talking. The Bishop, broken-jawed, smiles anyway: 'listen. listen to them. they've been talking the whole time.'",
    core: "core_second_stomach",
    refight: { card: REHIRE, line: "gristle and sons reappointed me. growth never stops.", mods: ["Full Choir: rim singers come back twice as fast", "High Acid: the lake rises during phase 1", "Second Helping: two swallow phases", "Fasting: no communion heals, but double hymns"] },
    drops: ["lt_boss_bishop", "communion", "the_intestine"],
  },
  founding_partner: {
    name: "THE FOUNDING PARTNER", card: "AUGUSTUS GRISTLE · FOUNDING PARTNER", subtitle: "he'd like you to sign something.",
    who: "gristle_senior", kind: "secret", district: "gut", arena: "gut:belly_button", quest: "sq_gut_belly_button", unlock: "done:m20_the_missing", hp: 14000,
    look: "thing: a cathedral-sized organ that was once a man, a huge kindly old face, tiny reading glasses, hundreds of arms each holding a pen.",
    why: "Behind the door you were told not to press: the first man ever treated with Regrowth, and the author of 'post-event workforce recovery'.",
    phases: [
      { name: "TERMS", hp: [100, 60], line: "now then. you pressed it. everybody presses it.",
        mechanics: [
          { name: "Sign Here", tell: "a hand with a pen reaches toward you from the dark", effect: "if a pen touches you, you're 'signed': a random contract debuff for 20 s (no jumping, reversed controls, sing on every shot)", counter: "shoot the pen hands; melee rips contracts off" },
          { name: "Fine Print", tell: "tiny text crawls over the floor", effect: "the floor becomes a contract; standing in it signs you", counter: "stay on the bone islands" },
        ] },
      { name: "CLAUSES", hp: [60, 25], line: "and here. and here. i have a lot of hands, you see.",
        mechanics: [
          { name: "Arm Storm", tell: "the arms all rise at once", effect: "hundreds of arms sweep the chamber in waves", counter: "slide under, jump over, on the rhythm of his breathing" },
          { name: "Regrowth", tell: "he exhales pink mist", effect: "cut arms regrow", counter: "fire on the face while he's exhaling (it's open)" },
        ] },
      { name: "SIGNATURE", hp: [25, 0], line: "my son thinks i'm proud of him. i am. that's the problem.",
        mechanics: [
          { name: "Last Contract", tell: "one enormous hand with a gold pen", effect: "it chases you; if it signs you, you're 'merged' (stuck to the wall for 5 s)", counter: "lure it into the acid" },
        ] },
    ],
    lines: { intro: "sign here, please.", hurt: ["that's a breach.", "now, now."], kill: ["signed.", "witnessed."], low: "tell my son it was a failure. he'll want to hear it from someone.", defeat: "thank you. that's the first contract i've ever lost." },
    defeat: "He signs your arm with a gold pen (the Founding Signature implant) and asks you to tell his son it was a failure. If you tell the Bishop (a side quest step), the Choir sings a new song.",
    core: "core_founding_signature",
    refight: { card: REHIRE, line: "now then. back again? everybody comes back.", mods: ["Small Print: the contract floor covers twice as much", "Cooling-Off Period: every 30 s, all damage you dealt is undone unless you hit the face"] },
    drops: ["rider_clause", "lt_boss_founding_partner"],
  },

  // ================================================================ PINSTRIPE
  don: {
    name: "DON GRINALDI FAZZOLETTO", card: "DON GRINALDI FAZZOLETTO · HEAD OF THE FAMILY", subtitle: "he's got people. on strings.",
    who: "don", kind: "district", district: "pinstripe", arena: "pinstripe:villa", quest: "m08_family_business", hp: 9000,
    look: "puppet: a 7 m marionette in pinstripes, huge face and hands, tiny waist, strings up into the Villa ceiling; the grin unfolds wider than the head.",
    why: "The Family 'assesses' anyone who wants the page: an underwriter's assessment, in the marble ballroom.",
    phases: [
      { name: "THE ASSESSMENT", hp: [100, 60], line: "my friend. this is just a formality.",
        mechanics: [
          { name: "Strings", tell: "the strings over a limb glow gold", effect: "his limbs are worked from above: big sweeping slaps and stomps", counter: "shoot the strings to drop a limb (one arm, then the other)" },
          { name: "Goons", tell: "he snaps his fingers (late: the snap comes a second after the hand moves)", effect: "pinstriped goons with tiny hands come in through the doors", counter: "goons are slow; the Punchlines' clowns (if allied) heckle them into fleeing" },
          { name: "Meatball", tell: "a waiter who is only arms wheels in a trolley", effect: "a car-sized meatball rolls across the ballroom", counter: "jump it or lasso it into him" },
        ] },
      { name: "THE OFFER", hp: [60, 35], line: "my friend. this is unpleasant. a gift, and we skip to the end.",
        mechanics: [
          { name: "The Offer", tell: "the fight pauses; he holds out a purse", effect: "a mid-fight choice (don_bribe): take 600 coupons and skip this phase, or refuse", counter: "your call" },
          { name: "Policy Lapse", tell: "the chandelier rattles", effect: "the chandeliers drop", counter: "watch the shadows" },
        ] },
      { name: "THE JAW", hp: [35, 0], line: "*in a much older voice* that's enough, grinaldi. let mamma talk.",
        mechanics: [
          { name: "Jaw", tell: "his jaw falls off and keeps talking, in Nonna's voice", effect: "the jaw hops around biting; the body attacks on its own, out of time with the voice", counter: "the strings above the jaw are the weak point: follow them up into the rafters" },
          { name: "Rafters", tell: "the ceiling hatch opens", effect: "the last 15% is fought climbing the strings up into the rafters, where Nonna sits; she doesn't fight, she pulls", counter: "cut the last string (or don't, if you promised Larry: it ends when you reach her)" },
        ] },
    ],
    lines: { intro: "my friend. sit. eat. sign.", hurt: ["that's disrespect.", "you're not covered for that."], kill: ["act of shareholders.", "claim denied."], low: "*late* ha. ha. ha.", defeat: "*Nonna, from above* my son is resting. you will speak to me." },
    defeat: "The body hangs still. Up in the rafters, Nonna and the page (m08 rafters talk).",
    core: "core_smile_muscle",
    refight: { card: REHIRE, line: "the family restrung him. the family always restrings.", mods: ["Extra Strings: he grows a third and fourth arm", "Premium: goons wear armour", "No Offer: phase 2 has no bribe", "Under New Management: if the Punchlines rule Pinstripe, the rehire is the Don's body worked by a vengeful Nonna as a raider boss on the Commute"] },
    drops: ["lt_boss_don", "made_man", "nonnas_needles"],
  },

  // ================================================================ THE CHECKOUT
  cart_mother: {
    name: "THE CART MOTHER", card: "THE CART MOTHER · CUSTOMER SINCE 1999", subtitle: "she wants to speak to your manager. you don't have one.",
    who: "cart_mother", kind: "district", district: "checkout", arena: "checkout:food_court", quest: "m11_no_refunds", hp: 9500,
    look: "thing: every lost shopping cart in the city welded into a rolling mountain around one furious shopper in a fleece and visor holding a receipt.",
    why: "She swallowed Big Value's page with her receipt. Every morning at 09:00 she comes out when the doors open.",
    phases: [
      { name: "DOORBUSTER", hp: [100, 60], line: "I WANT TO SPEAK TO YOUR MANAGER.",
        mechanics: [
          { name: "Roll", tell: "every cart's wheel squeaks at once", effect: "she rolls across the food court, flattening tables", counter: "escalators: ride up out of the way (they boost in one direction)" },
          { name: "Stack", tell: "she rears up, carts sliding into a tower", effect: "a tower slam that sends carts flying", counter: "the tower is top-heavy: hit the base" },
          { name: "Heavier", tell: "—", effect: "every cart you fire into her with the Cart Cannon sticks to her and makes her heavier and slower", counter: "fire the Rat Cart Cannon into her (she can't help picking them up)" },
        ] },
      { name: "SWARM", hp: [60, 25], line: "I'VE BEEN A MEMBER SINCE 1999.",
        mechanics: [
          { name: "Split", tell: "she bursts with a cash-register ding", effect: "splits into a swarm of single carts that hunt you, then recombines after 15 s", counter: "cart-surf on one of her own carts; kill the carts with the glowing child-seat speakers (they carry her voice)" },
          { name: "Forever Shoppers", tell: "the PA: 'attention shoppers'", effect: "a stampede of Forever Shoppers through the arena toward a SALE sign", counter: "shoot the SALE sign to send them the other way, through her" },
        ] },
      { name: "RECEIPT", hp: [25, 0], line: "i didn't look back. you're not supposed to look back.",
        mechanics: [
          { name: "Brenda", tell: "the carts fall away", effect: "it's just Brenda: she doesn't attack; the remaining carts circle and shield her", counter: "break the circle; the fight ends in the refund talk" },
        ] },
    ],
    lines: { intro: "I WANT TO SPEAK TO YOUR MANAGER.", hurt: ["THAT'S DAMAGED GOODS.", "I'LL BE LEAVING A REVIEW."], kill: ["NO REFUNDS.", "CLEANUP ON AISLE YOU."], low: "is it 09:00? it's always 09:00.", defeat: "can i return it? the day? i've got the receipt." },
    defeat: "The carts fall away. Brenda on the food court floor with her receipt (m11 refund talk).",
    core: "core_coupon_liver",
    refight: { card: REHIRE, line: "BIG VALUE HAS PROMOTED ME. I'M A PLATINUM MEMBER NOW.", mods: ["Black Friday: two stampedes", "Trolley Dash: she's 30% faster", "Loyalty Points: every cart she picks up heals her", "Under New Management: if the Mall Rats run the Checkout, the rehire is a Big Value loyalist's cart pile out on the Commute"] },
    drops: ["lt_boss_cart_mother", "gold_member", "the_receipt"],
  },

  // ================================================================ NUMBER WORKS
  foreman: {
    name: "FOREMAN REMAINDER", card: "FOREMAN REMAINDER · NUMBER WORKS", subtitle: "carries the one. and you.",
    who: "foreman", kind: "district", district: "numberworks", arena: "numberworks:yard", quest: "m15_rounding_down", hp: 9800,
    look: "cyborg: a huge crane-armed foreman with a calculator face, hydraulic legs, a 7 and a 13 welded to the shoulders.",
    why: "He comes down for the 06:00 print run. Remainder's page is stored in his face.",
    phases: [
      { name: "ADDITION", hp: [100, 66], line: "your odds are seven to one. against. let's call it thirteen.",
        mechanics: [
          { name: "Rolled Damage", tell: "a number spins on his display over every hit", effect: "every hit on him rolls a number that becomes the damage: 7s crit, 13s heal him (the BR rule)", counter: "burst weapons roll more numbers; the Lucky Kidney (if you have it) is cruel here" },
          { name: "Crane Swing", tell: "a crane arm locks with a hydraulic hiss", effect: "a giant digit swung like a wrecking ball", counter: "ride the conveyors (they keep their momentum on you)" },
        ] },
      { name: "MULTIPLICATION", hp: [66, 33], line: "times two. times two again.",
        mechanics: [
          { name: "Multiply", tell: "his display shows ×2", effect: "he divides into two smaller Foremen (each with half his HP); at the next ×2, four", counter: "kill the copies in the order their numbers show (lowest first, or they recombine with a heal)" },
          { name: "Price Press", tell: "the presses stamp on a beat", effect: "the yard's stamping presses come down on the beat", counter: "move between beats" },
        ] },
      { name: "DIVISION", hp: [33, 0], line: "divide by... divide by...",
        mechanics: [
          { name: "Divide by Zero", tell: "his display shows ÷0 and the yard glitches", effect: "gravity, conveyors and digits all reverse every 5 s", counter: "fall up; ride the giant digits; crit the face" },
        ] },
    ],
    lines: { intro: "carries the one. and you.", hurt: ["rounding error.", "that's a remainder."], kill: ["carried.", "you've been rounded down."], low: "it adds up. it always adds up.", defeat: "4,112,006,551." },
    defeat: "He falls into the Remainder Pit. His face shows one number before it dies (m15 face talk).",
    core: "core_lucky_kidney",
    refight: { card: REHIRE, line: "remainder reissued me. version 13.", mods: ["Compound Interest: every multiply happens twice", "Long Division: the ÷0 phase starts at 50%", "Unlucky: 13s heal twice as much"] },
    drops: ["lt_boss_foreman", "carry_the_one"],
  },

  // ================================================================ CHROME GRISTLE
  upsell: {
    name: "DOCTOR UPSELL", card: "DOCTOR UPSELL · MEAT MECHANIC", subtitle: "would you like fries with that kidney?",
    who: "upsell", kind: "district", district: "chromegristle", arena: "chromegristle:upsell_clinic", quest: "m19_organ_donor", hp: 10000,
    look: "off-spec: a twelve-armed surgeon in a stained coat and a kidney tie, each arm a tool; two of the arms are Bev's old hands, and they wave.",
    why: "He has the Gristle page in a jar, and he'd like your punch-clock heart.",
    phases: [
      { name: "CONSULTATION", hp: [100, 60], line: "this procedure comes with a free consultation. the consultation is the procedure.",
        mechanics: [
          { name: "Twelve Tools", tell: "the arm with the tool glows: saw (red), defibrillator (blue), scalpel (white), card machine (yellow)", effect: "saw sweeps, defib shocks the wet floor, scalpel lunges, and the card machine charges you coupons on hit", counter: "read the colour; jump the shock (Chrome Gristle's floors are always wet)" },
          { name: "Grab and Install", tell: "two arms reach with a little jar", effect: "if he grabs you, he installs a temporary bad implant: reversed controls, fish eyes (fisheye FOV), chatter teeth (you can't aim down sights), a squeaky spine", counter: "melee key rips it out (3 presses)" },
        ] },
      { name: "UPSELL", hp: [60, 25], line: "have you considered a second spleen? everyone's getting one.",
        mechanics: [
          { name: "Special Offer", tell: "a neon SALE sign flashes over a clinic chair", effect: "the chair drags you in: a 'procedure' minigame (mash to escape) while he upsells you out loud", counter: "shoot the sign's letters (the neon-sign gimmick) to change it to 'NO' and break the chair" },
          { name: "Bev's Hands", tell: "the two waving hands stop waving", effect: "they slap you (Bev's hands don't like him either: if you're fast, they slap him)", counter: "if Bev asked you (flag bev_wants_hands), shoot them off; she wants them back" },
        ] },
      { name: "FINAL OFFER", hp: [25, 0], line: "you've got a lot to give.",
        mechanics: [
          { name: "Everything Must Go", tell: "all twelve arms rise", effect: "all twelve tools at once in a spinning storm", counter: "get behind him; his back has no arms" },
        ] },
    ],
    lines: { intro: "would you like fries with that kidney?", hurt: ["that's a cancellation fee.", "no refunds on surgery."], kill: ["thank you for your donation.", "harvested."], low: "i was nine. i dug with my hands.", defeat: "can i interest you in... anything..." },
    defeat: "He sits in his own chair, eleven arms limp, one still holding the card machine out. The jar with the page rolls off the shelf.",
    core: "core_spare_arm",
    refight: { card: REHIRE, line: "the meat mechanics re-elected me. it was unanimous. i voted twelve times.", mods: ["Premium Package: two bad implants per grab", "Locum: a second, smaller surgeon assists", "Waiting List: the clinic chairs drag every 10 s"] },
    drops: ["lt_boss_upsell", "the_upsell"],
  },

  // ================================================================ EVERGREEN ACRES
  hoa: {
    name: "THE HOA", card: "THE HOA · HOMEOWNERS ASSOCIATION", subtitle: "your lawn is 2 mm too long.",
    who: "hoa", kind: "district", district: "evergreen", arena: "evergreen:culdesac", quest: "m21_property_values", hp: 10500,
    look: "thing: every homeowner merged into a giant hedge beast covered in KEEP OFF THE GRASS signs, gnome teeth, a clipboard face, Linda's voice from a sprinkler.",
    why: "You found the pilot. The HOA votes to remove you.",
    phases: [
      { name: "MOTION TO FINE", hp: [100, 60], line: "MOTION TO FINE. SECONDED. CARRIED.",
        mechanics: [
          { name: "Fines", tell: "a gavel bang from somewhere inside the hedge", effect: "each fine is a debuff that stacks: Lawn Too Long (−speed), Bins Out (−jump), Noise Complaint (enemies hear you), Unapproved Paint (−damage)", counter: "pay a fine at a mailbox (coupons) to clear it, or mow (below)" },
          { name: "Regrow", tell: "unmown lawns sparkle", effect: "the HOA regrows from any lawn you haven't mowed", counter: "mow lawns with the Lawn Mower (or any weapon fired at the grass): a mowed lawn stops the regrowth" },
          { name: "Sprinklers", tell: "a hiss underfoot", effect: "sprinklers launch you (and it) into the air", counter: "use them: shoot it in the air" },
        ] },
      { name: "BLOCK PARTY", hp: [60, 30], line: "ALL IN FAVOUR OF A BLOCK PARTY.",
        mechanics: [
          { name: "Mannequin Families", tell: "the windows stop waving and the front doors open", effect: "(if you left the pilot running) the waving families come out with BBQ tongs and leaf blowers", counter: "they're recordings: they fall over and get up waving. Shoot the garage chargers to switch them off" },
          { name: "Militia", tell: "golf carts honk", effect: "the HOA militia in golf carts with leaf blowers", counter: "leaf blowers push you; stay behind fences" },
        ] },
      { name: "SPECIAL MEETING", hp: [30, 0], line: "the apocalypse is not to be discussed in the cul-de-sac.",
        mechanics: [
          { name: "Vote", tell: "the hedge splits into voting members", effect: "it splits into five hedge homeowners; it re-merges if more than half are standing for 10 s ('quorum')", counter: "keep at least three down at once" },
        ] },
    ],
    lines: { intro: "your lawn is 2 mm too long.", hurt: ["THAT'S A VIOLATION.", "we're writing this down."], kill: ["FINED.", "property values: protected."], low: "please keep off the grass. please.", defeat: "motion to... adjourn..." },
    defeat: "The hedge falls apart into bewildered homeowners, holding hands, blinking in a sunlight they've been pretending was real. Linda is in the middle with the clipboard.",
    core: "core_grass_lung",
    refight: { card: REHIRE, line: "the association has re-elected itself.", mods: ["Strict Bylaws: fines stack twice", "Neighbourhood Watch: the militia arrives at 100%", "Hosepipe Ban: no sprinklers (no launch), but no regrowth either"] },
    drops: ["lt_boss_hoa", "keep_off_the_grass"],
  },

  // ================================================================ THE LATES
  perpetual_tuesday: {
    name: "THE PERPETUAL TUESDAY", card: "THE PERPETUAL TUESDAY · LATE FOR A MEETING", subtitle: "you've seen this one.",
    who: "perpetual_tuesday", kind: "district", district: "lates", arena: "lates:tuesday_tower", quest: "m22_the_waiting_room", hp: 10000,
    look: "thing: a huge running office worker made of a hundred copies of the same man in the same brown suit, briefcases and watches, one Neville at the heart holding an envelope.",
    why: "The loop resets every time Neville misses his meeting. Getting him there means getting through him.",
    phases: [
      { name: "09:00", hp: [100, 70], line: "sorry i'm late. sorry i'm late. sorry i'm late.",
        mechanics: [
          { name: "The Loop", tell: "a phone rings in key; a clock with no hands appears", effect: "the fight loops every 60 s and resets the arena, but damage carries over (on both sides)", counter: "plan each 60 s" },
          { name: "Your Past Self", tell: "a grey you appears where you started the loop", effect: "your bullets from the last loop replay", counter: "your past shots still hit him; set up crossfires" },
          { name: "Rush", tell: "a hundred watches flash", effect: "he charges across the arena toward the lift doors", counter: "stand in the lift doorway; he stops to apologise" },
        ] },
      { name: "12:41", hp: [70, 35], line: "the lift. the lift. why is it always the lift.",
        mechanics: [
          { name: "Copies", tell: "copies peel off him and run", effect: "copies scatter with briefcases (briefcase swings, coffee throws)", counter: "copies are 1-hit; each one killed shrinks him" },
          { name: "Copy of a Copy", tell: "copies photocopy themselves at office copiers", effect: "more copies", counter: "shoot the copiers" },
        ] },
      { name: "16:58", hp: [35, 0], line: "it's important. it's very important. it's numbers.",
        mechanics: [
          { name: "Last Minute", tell: "the clock with no hands grows hands; they read 16:58", effect: "a 2-minute timer: the loop's last minutes; he's at full speed", counter: "get him to the Tower's lift (the meeting) before 16:59: knock him in" },
        ] },
    ],
    lines: { intro: "you've seen this one.", hurt: ["sorry! sorry!", "i'm late, i'm so late."], kill: ["sorry. sorry. you're late now.", "see you at 09:00."], low: "could you take this?", defeat: "could you take this? i'm late." },
    defeat: "The copies fall away and fade. One man is left, holding an envelope (m22 envelope talk).",
    core: "core_tuesday_gland",
    refight: { card: REHIRE, line: "sorry i'm late. again.", mods: ["Double Booked: two loops interleaved", "Overrun: 45 s loops", "Reply All: every copy is a copier"] },
    drops: ["lt_boss_perpetual_tuesday", "groundhog"],
  },
  prototype: {
    name: "EMPLOYEE 4417", card: "R. CALE · EMPLOYEE OF THE QUARTER", subtitle: "the one who signed.",
    who: "prototype", kind: "secret", district: "lates", arena: "lates:warehouse", quest: "sq_lates_quality_control", unlock: "done:m23_workforce_restoration", hp: 12000,
    look: "mannequin: your own body, perfectly clean, no tilt, no wrong knee, in a ☺ CORP uniform, a punch-clock heart; it copies your outfit's colours in corporate white.",
    why: "Hask had a copy of PROTOTYPE 0 built with the Schedule forced in, to see what you'd be on the payroll. It's very happy.",
    phases: [
      { name: "ONBOARDING", hp: [100, 60], line: "oh! you must be the original. you're late.",
        mechanics: [
          { name: "Your Loadout", tell: "it holds up each of your quick-bar slots in turn", effect: "it fights with a copy of your quick bar and your implants (perks only: none of the downsides; the Schedule removes them)", counter: "it has no jank: it never slips on marbles or peels and it never mis-steps, but it never improvises either. Break its routine: it can't handle bananas it didn't schedule" },
          { name: "On The Beat", tell: "a metronome tick", effect: "it fires exactly on the beat: every shot crits", counter: "move off-beat; it adjusts in 3 beats" },
        ] },
      { name: "PERFORMANCE REVIEW", hp: [60, 25], line: "i remember mina. she's on my list. under 17:30. it's fine. it's handled.",
        mechanics: [
          { name: "Peer Review", tell: "the warehouse mannequins turn their heads", effect: "spare bodies activate and help it", counter: "pull their cables (interact)" },
          { name: "Your Streaks", tell: "it calls your streak item's callout", effect: "it uses your killstreak items' effects", counter: "interrupt with a stun" },
        ] },
      { name: "WHAT TIME IS IT", hp: [25, 0], line: "what time is it? nobody's ever not told me.",
        mechanics: [
          { name: "Unscheduled", tell: "its Schedule display flickers --:--", effect: "it freezes for 2 s every time you do something it couldn't schedule (a grapple fling, a car through a wall, a spray, a dance)", counter: "be janky" },
        ] },
    ],
    lines: { intro: "we'd make a great team. well. i would.", hurt: ["noted for my review.", "that's off-schedule."], kill: ["processed. don't worry. it's on the list.", "you were always the draft."], low: "what time is it?", defeat: "nobody's ever not told me." },
    defeat: "It sits down on its empty dock and asks what time it is. You can tell it anything (a free-text answer the game keeps). Whatever you say, it repeats it, smiling, and switches off.",
    core: "core_schedule_chip",
    refight: { card: REHIRE, line: "oh! you're back. so am i. there's always another one of me.", mods: ["Template: two copies", "Fully Scheduled: it gets your newest implants", "Overtime: no 'unscheduled' freezes until 50%"] },
    drops: ["employee_of_the_quarter", "lt_boss_prototype"],
  },

  // ================================================================ THE MARGINS
  tall_guy: {
    name: "THE TALL GUY FROM HR", card: "THE TALL GUY FROM HR · HUMAN RESOURCES", subtitle: "he just wants a quick word.",
    who: "tall_guy", kind: "district", district: "margins", arena: "margins:forest", quest: "m26_exit_interview", unlock: "flag:fought_tall_guy", hp: 9000,
    look: "thing: a very tall thin man in a grey suit, arms as long as he wants, a polite smile, a manila folder.",
    why: "Only if you crossed out his place of work instead of signing him out. Then he's killable, and very disappointed.",
    phases: [
      { name: "QUICK WORD", hp: [100, 60], line: "this is a safe space. it's very large. it's mostly negative.",
        mechanics: [
          { name: "Don't Look", tell: "a creak of pines behind you", effect: "he only moves when you're not looking at him; he gets closer every time you look away", counter: "keep him on screen; fight backwards" },
          { name: "Long Arms", tell: "his shadow stretches across the ground toward you", effect: "his arms reach any distance and grab", counter: "break line of sight with a pine; the grab follows the shadow" },
        ] },
      { name: "DISCIPLINARY", hp: [60, 25], line: "i'm not angry. i'm disappointed. and very tall.",
        mechanics: [
          { name: "Many Folders", tell: "folders fall like leaves", effect: "file folders slice the air", counter: "shoot them" },
          { name: "Tall", tell: "he grows into the canopy", effect: "he stands above the trees and comes down like a fork", counter: "the Void Edges: fall into the void on purpose to respawn at a gnome behind him" },
        ] },
      { name: "EXIT", hp: [25, 0], line: "nobody returns anything.",
        mechanics: [
          { name: "Edge", tell: "the forest thins to the cliff", effect: "he drives you toward the Edge", counter: "fight on the lifeguard tower; he can't reach above his own height" },
        ] },
    ],
    lines: { intro: "he just wants a quick word.", hurt: ["that's noted.", "i'll have to raise this."], kill: ["thank you for your time.", "we'll be in touch."], low: "they never came to collect me.", defeat: "...could you still sign it? for my file?" },
    defeat: "He folds down onto the forest floor. He asks you to sign the exit interview anyway, for his file. You can.",
    core: "core_long_spine",
    refight: { card: REHIRE, line: "☺ corp has extended my loan.", mods: ["Night Shift: the forest is pitch dark", "Restructure: two of him", "Gardening Leave: no pines (open ground)"] },
    drops: ["lt_boss_tall_guy", "quick_word"],
  },
  penny_plot: {
    name: "PENNY PLOT", card: "PENNY PLOT · CLOSING AGENT", subtitle: "the deal closes today. so do you.",
    who: "penny_plot", kind: "story", district: "margins", arena: "margins:edge", quest: "m27_negative_space", hp: 11500,
    look: "normal: an estate agent in a white hazmat suit and pink blazer, a SOLD sign on a pole, a briefcase handcuffed to her wrist.",
    why: "Her briefcase is the Bottom's deed. She's closing the sale today.",
    phases: [
      { name: "VIEWING", hp: [100, 65], line: "open plan! lots of light!",
        mechanics: [
          { name: "Keyring Bombs", tell: "a jingle and a pink glow", effect: "void bombs shaped like keyrings delete circles of ground", counter: "keep moving; void falls respawn you at the nearest gnome with momentum (Margins gimmick)" },
          { name: "SOLD", tell: "she plants the SOLD sign", effect: "the ground in a cone in front of the sign is 'sold' and drops into the void after 2 s", counter: "shoot the sign over" },
        ] },
      { name: "OPEN HOUSE", hp: [65, 30], line: "it's a buyer's market. the buyer is the void.",
        mechanics: [
          { name: "Show Home", tell: "the Show Home's lights flash", effect: "survey drones and hazmat agents; the Show Home slides toward the edge", counter: "Old Pat's gnomes: planting a gnome on a plot makes it 'occupied' and stops it dropping" },
          { name: "Location", tell: "she points", effect: "the void rises in a wave", counter: "get high: the lifeguard tower" },
        ] },
      { name: "COMPLETION", hp: [30, 0], line: "location, location, nothing.",
        mechanics: [
          { name: "Final Sale", tell: "everything glows pink", effect: "she sells the ground under the whole arena: it falls away in chunks every 6 s", counter: "grapple between falling chunks; finish her on the last plot" },
        ] },
    ],
    lines: { intro: "the deal closes today. so do you.", hurt: ["that's devaluing the property!", "rude."], kill: ["sold!", "you're on the market."], low: "i sold my own house.", defeat: "can i interest you in... the plot you're standing on?" },
    defeat: "She clings to a SOLD sign over the void and tries to sell you the plot you're standing on. The briefcase pops open.",
    core: "core_open_plan_lung",
    refight: { card: REHIRE, line: "back on the market!", mods: ["Seller's Market: twice the keyring bombs", "Gazumped: a rival agent joins", "Chain Collapse: the arena drops 30% faster"] },
    drops: ["lt_boss_penny_plot", "open_plan"],
  },

  // ================================================================ CORP HILL
  meeting_room: {
    name: "THE MEETING ROOM", card: "THE MEETING ROOM · STEERING COMMITTEE", subtitle: "this could have been an email.",
    who: "steering_committee", kind: "story", district: "corphill", arena: "corphill:cathedral", quest: "m29_the_missing_hour", hp: 14000,
    look: "a flying conference-room gunship on four rotors with a projector eye, a long table inside and three monitor-headed executives in swivel chairs.",
    why: "☺ CORP's air defence for the raid: a meeting that never ends, armed.",
    phases: [
      { name: "AGENDA", hp: [100, 60], line: "can everyone see my screen?",
        mechanics: [
          { name: "Projector", tell: "a white beam sweeps the road", effect: "anyone caught in the beam is 'presenting': marked for every Corp unit (and slowed by a slide transition)", counter: "shoot the projector lens to blind it for 8 s" },
          { name: "Action Items", tell: "the side windows open", effect: "missiles labelled ACTION ITEM", counter: "lasso one and swing it back" },
          { name: "Minutes", tell: "paper fluttering", effect: "fines rain from the windows", counter: "melee them off" },
        ] },
      { name: "ANY OTHER BUSINESS", hp: [60, 25], line: "any other business? no? then fire.",
        mechanics: [
          { name: "Board It", tell: "it hovers low over the Cathedral roof", effect: "grapple aboard: inside, a fight around the long table with the Steering Committee", counter: "win the vote: knock all three out of their chairs" },
          { name: "Swivel", tell: "chairs spin", effect: "the committee spins and fires", counter: "stay on the table" },
        ] },
      { name: "TAKE IT OFFLINE", hp: [25, 0], line: "let's take this offline.",
        mechanics: [
          { name: "Crash", tell: "a rotor screams", effect: "it falls toward the Cathedral; jump out before it lands", counter: "parachute? no. bail onto the Cathedral roof" },
        ] },
    ],
    lines: { intro: "can everyone see my screen?", hurt: ["you're on mute.", "per my last email."], kill: ["minuted.", "actioned."], low: "this meeting could have been an email.", defeat: "*the Meeting Room crashes into the Smiling Fountain, still minuting*" },
    defeat: "It crashes into the Smiling Fountain. The three executives keep minuting the crash from inside it.",
    core: "core_projector_eye",
    refight: { card: REHIRE, line: "the meeting has been rescheduled.", mods: ["All-Hands: two Meeting Rooms", "Hybrid: half the committee is on a screen (immune unless you shoot the screen)"] },
    drops: ["lt_boss_meeting_room", "per_my_last_email"],
  },
  twins: {
    name: "THE TWINS", card: "THE TWINS · VP OF SYNERGY", subtitle: "they agree.",
    who: "twins", kind: "story", district: "corphill", arena: "corphill:spire_lobby", quest: "m30_the_lobby", hp: 13000,
    look: "cyborg: two executives merged at the hip in one double-breasted suit, one smile across two faces; one has a pistol arm, the other a riot-shield arm.",
    why: "They hold the elevator. Win and Win: they've never once disagreed in public.",
    phases: [
      { name: "ALIGNMENT", hp: [100, 55], line: "we agree.",
        mechanics: [
          { name: "Swap", tell: "they spin on the spot, suit flapping", effect: "they swap roles: the shield side and the gun side change", counter: "flank the gun side; the shield always faces you" },
          { name: "Circle Back", tell: "a bullet fired past you curves away", effect: "their attacks come back: shots return from behind 3 s later", counter: "keep moving in a line, not a circle" },
          { name: "Synergy", tell: "both faces grin at once", effect: "a combined charge", counter: "jump the lobby pillars" },
        ] },
      { name: "RESTRUCTURE", hp: [55, 0], line: "*the left one, alone* i never agreed. not once. not ONCE.",
        mechanics: [
          { name: "One Left", tell: "kill one half first (each half has its own HP bar)", effect: "the other one does both jobs, very badly: shoots its own shield, shields nothing, circles back into itself", counter: "enjoy it; it's still dangerous when it's angry" },
          { name: "Reorg", tell: "it drags the dead half behind it like a cape", effect: "the dead half's arm still fires sometimes", counter: "stay behind pillars" },
        ] },
    ],
    lines: { intro: "let's circle— —back.", hurt: ["noted— —noted.", "that's not— —aligned."], kill: ["we agree— —you're done.", "synergy."], low: "per our— —last email.", defeat: "*the survivor* finally. finally. i'm my own person." },
    defeat: "The survivor sits on the reception desk, laughing and sobbing. 'finally. i'm my own person.' Then Auntie sits down behind the desk (C19).",
    core: "core_synergy_node",
    refight: { card: REHIRE, line: "we've been— —re-merged.", mods: ["Three-Way Merger: a third VP", "Matrix Management: both halves have shields", "Silo: they can't hurt each other any more"] },
    drops: ["lt_boss_twins", "circle_back"],
  },
  hask: {
    name: "MARION HASK", card: "MARION HASK · CHIEF PUNCTUALITY OFFICER", subtitle: "she signed the end of the world. she'll sign the next one.",
    who: "hask", kind: "final", district: "corphill", arena: "corphill:master_clock", quest: "m32_fully_vested", hp: 18000,
    look: "cyborg: the white suit open like a cabinet; a clear ☺ CORP frame holding a body of other people's organs, each tagged with a paper label; she fights from the Clock's control cockpit.",
    why: "The last thing between you and the Clock. She never begs. She fights with the Master Clock's controls.",
    phases: [
      { name: "THE SCHEDULE", hp: [100, 66], line: "You are on my schedule now.",
        mechanics: [
          { name: "Slots", tell: "the floor tiles light up in a grid with times on them", effect: "she schedules the room: tiles fire in order on a timetable shown on the walls", counter: "read the timetable; stand in the tile whose time has just passed" },
          { name: "Late Fee", tell: "a ☺ clock face appears over you", effect: "a big hit if you're standing still when it fills", counter: "move" },
          { name: "Recall", tell: "she says a name from the ledger", effect: "she pulls a district's security back: Corp units from that district appear", counter: "the districts you made TAKEOVERs in have no Corp units to recall: those names fail" },
        ] },
      { name: "CONTINUITY", hp: [66, 33], line: "Every one of them is written down.",
        mechanics: [
          { name: "Donor Organs", tell: "a tagged organ in her frame glows", effect: "each glowing organ gives her a power (a lung: a shout that pushes; a heart: a heal; a liver: acid; a kidney: a dash); the label shows whose it was", counter: "shoot the glowing organ to shut that power down; the label falls; the game remembers the name" },
          { name: "Backup", tell: "the Machine's archive cable hums", effect: "she restores her last 10% of HP from a backup, once", counter: "cut the archive cable" },
        ] },
      { name: "CLOSE OF BUSINESS", hp: [33, 0], line: "Hitting the number would have cost us more than ending the world.",
        mechanics: [
          { name: "17:30", tell: "every clock in the room shows 17:29 and counts", effect: "a 60 s countdown; at 17:30 the room 'launches' (a huge blast that resets you to the phase start)", counter: "finish her before 17:30, or hide in the Clock's escapement (one safe spot)" },
          { name: "Signature", tell: "she raises a pen", effect: "she signs the air: a line of damage across the room", counter: "jump the line" },
        ] },
    ],
    lines: { intro: "Good evening. You are on time.", hurt: ["That was unnecessary.", "I will note that."], kill: ["Back in the bin.", "Retained."], low: "I was there for the Long Dark. You were in a vending machine.", defeat: "Somebody should read them." },
    defeat: "She sits down against the console with the ledger in her lap and starts reading names (C24).",
    core: "core_clear_frame",
    refight: null, drops: ["close_of_business", "lt_boss_hask"],
  },

  // ================================================================ THE COMMUTE (world bosses)
  eotm: {
    name: "EMPLOYEE OF THE MONTH", card: "EMPLOYEE OF THE MONTH · THE UNPAID", subtitle: "every month. since the end of the world.",
    who: "eotm", kind: "world", district: "commute", arena: "commute:ring_road", quest: "sq_commute_eotm", unlock: "act>=2", hp: 13000,
    look: "normal: a huge raider in office-chair and filing-cabinet armour, 732 plaques of his own face; the fight is on a war-rig made of a bus, forty desks and a photocopier.",
    why: "The Unpaid want to be a company. A company needs a big win. You're the big win.",
    phases: [
      { name: "THE CONVOY", hp: [100, 60], line: "we're not raiders. we're a startup.",
        mechanics: [
          { name: "120 km/h", tell: "the convoy horns", effect: "the fight is on and around a moving convoy at 120 km/h on the Ring Road", counter: "board it with the grapple; drive alongside and jump" },
          { name: "Interns", tell: "a photocopier flash", effect: "the photocopier on the war-rig prints raiders", counter: "break the photocopier (three panels: paper tray, toner, the big green button)" },
          { name: "Desk Wall", tell: "desks slide to the rig's edge", effect: "desks are shoved off the back as barricades", counter: "jump them; or knock interns off with them" },
        ] },
      { name: "THE PITCH", hp: [60, 25], line: "who gave me this award? i did. who deserved it? also me.",
        mechanics: [
          { name: "Plaque Shield", tell: "he raises a plaque", effect: "plaques block damage from the front; each one breaks with a sad little 'ding'", counter: "break the plaques; he gets angrier, slower and sadder" },
          { name: "Motivational Speech", tell: "he grabs a megaphone", effect: "interns get +50% damage while he's talking", counter: "shoot the megaphone" },
        ] },
      { name: "THE GRIND", hp: [25, 0], line: "the grind never stops. i've tried to stop it. it won't.",
        mechanics: [
          { name: "Hostile Takeover", tell: "he climbs to the bus's steering wheel", effect: "he steers the war-rig at you or off the road", counter: "fight him at the wheel" },
        ] },
    ],
    lines: { intro: "HALT. YOU ARE ENTERING A WORKSPACE.", hurt: ["that's a learning experience.", "feedback received."], kill: ["onboarded.", "you're our newest intern."], low: "is this a performance review?", defeat: "nobody's ever... given me... feedback." },
    defeat: "The war-rig coasts to a stop in a jam. He sits on the bus roof holding his oldest plaque. If you did Todd's questline, Todd climbs up next to him.",
    core: "core_lanyard_gland",
    refight: { card: REHIRE, line: "EMPLOYEE OF THE MONTH. AGAIN.", mods: ["Series A: two war-rigs", "Crunch: no breaks between phases", "Pivot: the convoy changes highways mid-fight"] },
    drops: ["lt_boss_eotm", "employee_of_the_month"],
  },
  morale_officer: {
    name: "THE MORALE OFFICER", card: "THE MORALE OFFICER · THE FUN DEPARTMENT", subtitle: "smile. that's not a request.",
    who: "morale_officer", kind: "world", district: "commute", arena: "commute:carnival", quest: "sq_commute_mandatory_fun", unlock: "act>=2", hp: 12500,
    look: "thing: a towering mascot made of a dozen matted ex-Marketing costumes stitched together, a megaphone, a confetti cannon, tired eyes in the top head's mouth.",
    why: "The Fun Department's carnival on the Commute, only at night, where losing a game is a fight.",
    phases: [
      { name: "STEP RIGHT UP", hp: [100, 65], line: "everybody wins! everybody HAS to win!",
        mechanics: [
          { name: "Mandatory Fun", tell: "a kazoo fanfare", effect: "a carnival game appears (ring toss, hook-a-duck, whack-a-mole with real moles): lose it and you're 'having fun' (forced dance, 3 s)", counter: "win the game (shoot the targets fast)" },
          { name: "Confetti Cannon", tell: "a party-popper wind-up", effect: "a confetti blast that shoves (like the Party Popper)", counter: "brace behind stalls" },
        ] },
      { name: "TEAM BUILDING", hp: [65, 30], line: "smile! that's not a request.",
        mechanics: [
          { name: "Heads", tell: "one costume head lights up (bear, hot dog, cloud, tooth)", effect: "each head has an attack: bear hug (grab), hot dog (mustard slick), cloud (rain + lightning), tooth (bite)", counter: "shoot the lit head off" },
          { name: "Mascots", tell: "the big top flap opens", effect: "feral mascots in matted suits pour out", counter: "they're people: they get up afterwards" },
        ] },
      { name: "THE QUIET", hp: [30, 0], line: "*quiet* i wrote the ad. 'every big value is a shelter.' it tested very well.",
        mechanics: [
          { name: "Silence", tell: "the music stops", effect: "she hates silence: she attacks wildly to make noise; if YOU stay silent (no shooting) for 5 s, she stops and takes a head off", counter: "stop shooting and wait. (a quiet kill: four 5-second silences end the fight)" },
        ] },
    ],
    lines: { intro: "smile! that's not a request.", hurt: ["that's not fun!", "where's your team spirit?"], kill: ["FUN!", "wasn't that fun?"], low: "please. make some noise.", defeat: "*she takes the last head off*" },
    defeat: "She takes the heads off one by one. Under the last is an old woman with tired eyes, who sits on a carousel horse and listens to the quiet.",
    core: "core_confetti_gland",
    refight: { card: REHIRE, line: "fun has been reinstated!", mods: ["Theme Park: every stall is a game", "Parade: the whole carnival is moving", "Silent Disco: the quiet phase starts at 60%"] },
    drops: ["lt_boss_morale_officer", "mandatory_fun"],
  },
  unlucky_13: {
    name: "UNLUCKY 13", card: "UNLUCKY 13 · REMAINDER ORBITAL ASSET", subtitle: "price check: everything.",
    who: "unlucky_13", kind: "world", district: "commute", arena: "commute:digit_13", quest: "sq_commute_unlucky_13", unlock: "done:m15_rounding_down", hp: 15000,
    look: "thing: a glowing fallen 13 the size of a building in a glassed crater, display panels still flickering prices, a targeting array on top, toxic green glow.",
    why: "One of Remainder's orbital billboards that guided the missiles. Its last target list is still loaded. Its last target is the Bottom.",
    phases: [
      { name: "FORECAST", hp: [100, 60], line: "FORECAST: 97% CASUALTY. ROUNDING UP.",
        mechanics: [
          { name: "Price Strike", tell: "a price tag appears on the ground with a number counting down", effect: "an orbital-style strike when the tag hits 0", counter: "get out of the tag; the higher the price, the bigger the blast" },
          { name: "Fallout", tell: "the radiation meter ticks faster", effect: "the hot zone drains HP slowly; it rises each phase", counter: "Lead-lined implants and the Commute's rad stations" },
        ] },
      { name: "TARGETING", hp: [60, 25], line: "TARGET ACQUIRED: THE BOTTOM. PRICE CHECK.",
        mechanics: [
          { name: "Power Up", tell: "it draws power from fights near it", effect: "a charge bar: if it fills, it 'fires' at the Bottom (a fail: the Bottom loses a house and the fight resets to phase 2)", counter: "destroy the three relay dishes on the crater rim (each one drains the bar)" },
          { name: "Digits", tell: "smaller digits detach from its panels", effect: "flying 1s and 3s that ram you", counter: "ride them (Number Works' digit-riding works here)" },
        ] },
      { name: "SALE ENDS NEVER", hp: [25, 0], line: "SALE ENDS NEVER.",
        mechanics: [
          { name: "Clearance", tell: "every panel flashes 0.00", effect: "price strikes everywhere, all at once, in a grid", counter: "the 13's own shadow is never targeted" },
        ] },
    ],
    lines: { intro: "PRICE: YOU. 0.00.", hurt: ["ADJUSTING.", "DISCOUNT APPLIED."], kill: ["SOLD.", "ROUNDED DOWN."], low: "FORECAST: ERROR.", defeat: "TARGET... CANCELLED." },
    defeat: "Its panels go dark one at a time. The last one shows the target list, and the Bottom on it, crossed out.",
    core: "core_forecast_lobe",
    refight: { card: REHIRE, line: "REMAINDER HAS RELAUNCHED THIS ASSET.", mods: ["Inflation: prices (blast sizes) up 50%", "Dark Sky: night, the tags are the only light", "Bad Luck: 13s on every damage roll heal it"] },
    drops: ["lt_boss_unlucky_13", "the_forecast"],
  },
  missing_texture: {
    name: "THE MISSING TEXTURE", card: "THE MISSING TEXTURE · TODO", subtitle: "it was supposed to be patched.",
    who: "missing_texture", kind: "secret", district: "commute", arena: "commute:missing_texture", quest: "sq_commute_first_intern", unlock: "flag:todd_off_the_roof", hp: 11000,
    look: "thing: a creature of purple-and-black checkerboard squares, unshaded, flickering between a cube, a T-pose, a floating hand and a half-loaded car, green code scrolling over it.",
    why: "The first thing Todd forgot to code, on his first day. It's been growing out of the Unfinished Bit ever since.",
    phases: [
      { name: "NOT FOUND", hp: [100, 60], line: "// TODO: finish this",
        mechanics: [
          { name: "No Collision", tell: "its squares flicker", effect: "parts of the arena lose collision: you fall through the floor", counter: "follow the bits that still have texture" },
          { name: "T-Pose", tell: "it snaps into a T-pose", effect: "a sweeping T-pose that knocks you into the unfinished sky", counter: "duck under the arms" },
        ] },
      { name: "NaN", hp: [60, 25], line: "NaN NaN NaN NaN",
        mechanics: [
          { name: "NaN", tell: "your HP bar shows NaN", effect: "for 5 s your HP is NaN: you can't die, and you can't heal; when it comes back it's a random number", counter: "use the window to attack" },
          { name: "Spawn Error", tell: "a half-loaded car appears", effect: "objects spawn in the wrong place (cars in the air, a bus inside you)", counter: "momentum: cars keep speed off ramps; ride them" },
        ] },
      { name: "PATCHED", hp: [25, 0], line: "// todd was here",
        mechanics: [
          { name: "Patch", tell: "Todd's voice: 'i'm patching it! i'm patching it!'", effect: "Todd (if he came) types patches: each patch gives it a texture, and textured parts can be hurt", counter: "protect Todd's lawn chair" },
        ] },
    ],
    lines: { intro: "texture not found.", hurt: ["ERROR", "warning: unused variable you"], kill: ["ERROR: you", "// removed"], low: "please don't patch me.", defeat: "texture... found." },
    defeat: "It turns, very slowly, into a texture: a plain grey concrete square. Todd cries. 'it's finished. it's finally finished.'",
    core: "core_todo_skin",
    refight: { card: REHIRE, line: "// TODO: TODO", mods: ["Regression: the patches come undone at 50%", "Hotfix: no Todd", "Merge Conflict: two of it"] },
    drops: ["the_missing_texture", "lt_boss_missing_texture"],
  },
};
