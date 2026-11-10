// OVERDUE grudges: "the Grudge Ledger". Ordinary named enemies who survive you, beat you or get humiliated by you
// get an HR file, and come back later remembering exactly what happened, with a physical, funny adaptation to show
// for it. Design doc: docs/story/GRUDGES.md (the rules, why it's its own design, the example stories).
// Pure data for the systems lane; nothing here runs.
//
// SCHEMA
//   GRUDGE_RULES     the numbers (caps, chances, timers): see the doc's "Rules" section
//   GRUDGE_FACTIONS[id] = { name, who (which enemies can open a file), districts: [DISTRICTS ids], names: [first names],
//                           tag (how the file labels them), voice (how they talk) }
//   GRUDGE_TRIGGERS[id] = { name, when (the exact game event), weapons?: [shared/weapons.js ids], adaptation (the
//                           ADAPTATIONS id it gives), opens (true = can open a new file) }
//   ADAPTATIONS[id]     = { name, from (a trigger id), look (on the model), effect (what changes, one thing), counter
//                           (the one trick that beats it), title (the epithet the file gives them: 'Neck Brace') }
//   RESOLUTIONS[id]     = { name, how (what you do), result, file (the stamp on the file) }
//   BARKS[faction][key] = [lines]   keys: BARK_KEYS. {you} = your name on the file, {name} = theirs, {district}
//   RECAPS[id]          = { when, title, lines: [templates] }  the PREVIOUSLY BETWEEN YOU TWO card
//                         placeholders: RECAP_FIELDS

export const GRUDGE_RULES = {
  maxActive: 12,          // open files per save; a 13th retires the one you've seen least recently ("transferred")
  maxHistory: 4,          // entries per file (oldest drops off; the recap only ever shows the last 3)
  maxAdaptations: 3,      // visible adaptations per enemy; a 4th replaces the oldest
  openChance: 0.35,       // chance a qualifying event opens a file on a nameless enemy (always on a kill of YOU)
  spawnEvery: 240,        // seconds of play in a file's district before its owner may turn up again
  spawnChance: 0.3,       // per check, once the timer's up (never during a story mission unless the mission allows it)
  oneAtATime: true,       // at most one grudge enemy in any fight
  expireDays: 7,          // in-game days without a meeting: the file goes cold and closes itself ("statute of limitations")
  recapOncePerSession: true,
  saveBytes: 3072,        // the whole ledger fits in 3 KB of the story save
};

export const RECAP_FIELDS = ["name", "tag", "district", "you", "what", "when", "adaptation", "trophy", "count"];
export const BARK_KEYS = ["spotted", "killed_you", "you_fled", "survived", "run_over", "slipped", "burned", "shocked", "flung", "humiliated", "trophy", "quit", "ally", "last_words"];

export const GRUDGE_FACTIONS = {
  unpaid: { name: "THE UNPAID", tag: "INTERN", who: "Unpaid raiders on the Commute and in raider camps", districts: ["commute", "bottom"],
    names: ["Kev", "Big Nathan", "Tamsin", "Lil Spreadsheet", "Doug from Onboarding", "Priya", "Stapler", "Mo", "Becky", "The Other Kev", "Jules", "Ahmed", "Hot Desk", "Sandwich"],
    voice: "startup bravado, networking words used as threats, very proud of their lanyards" },
  timekeeping: { name: "TIMEKEEPING ENFORCEMENT", tag: "OFFICER", who: "Punctuality Officers and Timekeeping cruisers (Late Fees ★1-★2)", districts: ["corphill", "bottom", "checkout", "numberworks", "pinstripe"],
    names: ["Officer Tick", "Officer Brisk", "Officer Pendle", "Sergeant Minute", "Officer Dial", "Officer Prompt", "Officer Hand", "Officer Quarter"],
    voice: "clipboard politeness, exact times, everything is 'noted'" },
  collectors: { name: "COLLECTIONS", tag: "COLLECTOR", who: "Collections van crews and repo men (Late Fees ★3)", districts: ["bottom", "commute", "lates", "margins"],
    names: ["Mr. Arrears", "Debbie", "Mr. Interest", "Clive", "The Repo Man", "Mrs. Overdraft", "Barry", "Lien"],
    voice: "debt-collector menace with paperwork: you owe them, and now it's personal and itemised" },
  choir: { name: "THE GUT CHOIR", tag: "CHORISTER", who: "Choir singers and Gristle & Sons guards in the Gut", districts: ["gut"],
    names: ["Brother Bile", "Sister Minutes", "Brother Lanyard", "Sister Tuesday", "Brother Gristle", "Sister Agenda's Cousin", "Brother Swallow", "Sister Chord"],
    voice: "sings half of every sentence, then drops into tired office talk; holds grudges as hymns" },
  goons: { name: "THE FAMILY'S GOONS", tag: "ASSOCIATE", who: "Pinstripe goons (huge, tiny hands)", districts: ["pinstripe"],
    names: ["Big Sal", "Tiny Tony", "Vincenzo", "Paulie Pinstripes", "Little Carlo", "Big Rita", "Enzo Two-Hands", "The Accountant"],
    voice: "wounded respect; everything is 'disrespect'; extremely polite about revenge" },
};

export const GRUDGE_TRIGGERS = {
  killed_you: { name: "KILLED YOU", when: "they land the hit that dispenses you back at a terminal", adaptation: "your_hat", opens: true },
  you_fled: { name: "YOU RAN", when: "you leave a fight they're in while they're above 50% HP (they saw you go) or lose Late Fees while they were chasing you", adaptation: "stopwatch", opens: true },
  survived: { name: "SURVIVED YOU", when: "they get away below 20% HP (fled, rescued, or you were dispensed first)", adaptation: "hi_vis_survivor", opens: true },
  run_over: { name: "RUN OVER", when: "you hit them with a car (any car, the sofa-car counts double) and they live", adaptation: "neck_brace", opens: true },
  slipped: { name: "SLIPPED", when: "they slip on your marbles or banana peels and live", weapons: ["marbles", "banana"], adaptation: "glued_shoes", opens: true },
  burned: { name: "SET ON FIRE", when: "they catch fire from you (Cigarette, flame arrows, lit oil) and live", weapons: ["cig", "bow"], adaptation: "bandages", opens: true },
  shocked: { name: "TASED WET", when: "you soak them and tase them (or tase them in water) and they live", weapons: ["water", "taser"], adaptation: "rubber_suit", opens: true },
  flung: { name: "FLUNG", when: "you fling them with the lasso, a sniper body shot, the minigun or the Leaf Blower, and they land alive", weapons: ["lasso", "sniper", "minigun", "blower"], adaptation: "anchor_belt", opens: true },
  frozen: { name: "FROZEN", when: "you freeze them solid (four snowballs) and they thaw out alive", weapons: ["snowball"], adaptation: "peas_hat", opens: true },
  headshot: { name: "HEADSHOT SURVIVOR", when: "they live through a headshot (low damage weapon, armour, luck)", adaptation: "wok_helmet", opens: true },
  pinned: { name: "PINNED", when: "you nail them to a wall (Nail Gun) and they pull free", weapons: ["nailgun"], adaptation: "plank_armour", opens: true },
  bonked: { name: "HOME RUN", when: "you launch them with the Bread or the Hand Slapper and they live", weapons: ["bread", "slapper"], adaptation: "cardboard_box", opens: true },
  backstabbed: { name: "STABBED IN THE BACK", when: "a knife heavy stab from behind that doesn't kill (armour, or a co-op revive)", weapons: ["knife"], adaptation: "back_pillow", opens: true },
  grappled: { name: "YANKED", when: "you yank them off a ledge or roof with the grapple and they survive the fall", adaptation: "own_grapple", opens: true },
  bubbled: { name: "BUBBLED", when: "you seal them in a soap bubble and it pops somewhere embarrassing", adaptation: "pin_badge", opens: true },
  quizzed: { name: "POP QUIZ", when: "they get a Pop Quiz question right (they live and get a gold star)", adaptation: "calculator", opens: false },
  verdict: { name: "FOUND GUILTY", when: "the Scales of Justice rate them GUILTY and they live", weapons: ["scales"], adaptation: "lawyer", opens: false },
  bitten: { name: "BITTEN", when: "you bite them with the Bear Trap Jaw implant", adaptation: "scarf", opens: false },
  burped: { name: "BURPED AT", when: "the Second Stomach's burp gives you away to them and they find you", adaptation: "nose_peg", opens: false },
  photographed: { name: "PHOTOGRAPHED", when: "you snap them with the Instant Camera mid-fall, mid-slip or mid-bubble", adaptation: "your_photo", opens: false },
  mocked: { name: "MOCKED", when: "you spray, emote or dance over them while they're down and they get up", adaptation: "face_tattoo", opens: false },
  outran: { name: "OUTRUN", when: "you outrun them at over 100 km/h (on foot, bhop) and they clock it", adaptation: "roller_skates", opens: false },
  smoked: { name: "SMOKED OUT", when: "they lose you in your smoke or a paper storm", adaptation: "goggles", opens: false },
  flashed: { name: "FLASHED", when: "you flash them with the night vision goggles", adaptation: "sunglasses", opens: false },
  shoved: { name: "SHOVED", when: "you shove them off something with knockback (but not far enough)", adaptation: "sandbags", opens: false },
  fragged: { name: "FRAGGED", when: "they survive one of your grenades", adaptation: "oven_mitts", opens: false },
  sniped: { name: "SNIPED AT", when: "they survive a sniper or DMR shot from over 60 m", weapons: ["sniper", "dmr"], adaptation: "zigzag", opens: false },
  ticked: { name: "HEARD YOU TICKING", when: "they hear your Cracked Punch-Clock and find you", adaptation: "earmuffs", opens: false },
  reversed: { name: "REVERSED", when: "a Reverse Card sends their own shots back at them", adaptation: "mirror_shield", opens: false },
  duck: { name: "DUCKED", when: "they get dragged into your Rubber Duck's black hole and spat out", adaptation: "rubber_ring", opens: false },
  gassed: { name: "GASSED", when: "they survive a gas arrow or a Gut gas vent you lit", adaptation: "gas_mask", opens: false },
  shredded: { name: "NEARLY SHREDDED", when: "they escape the Shredder's intake", weapons: ["shredder"], adaptation: "duct_tape", opens: false },
  dog: { name: "OUT-DOGGED", when: "a stomach-dog fetches your grenade back at them (the Gut)", adaptation: "stomach_dog", opens: false },
};

const A = (from, name, title, look, effect, counter) => ({ from, name, title, look, effect, counter });
export const ADAPTATIONS = {
  your_hat: A("killed_you", "YOUR HAT", "Hat Thief", "they wear the cosmetic hat (or a recognisable bit of your outfit) they took when they killed you; a photo of you pinned to their lanyard", "they get +1 confidence: they never flee at low HP", "shoot the hat off: they stop fighting to chase it, and you can take it back (it's returned to your wardrobe)"),
  stopwatch: A("you_fled", "A STOPWATCH", "Personal Best", "a big stopwatch round their neck with your best escape time on it", "they chase you at exactly your speed and time out loud how long you last", "they can't stop timing: lead them over a ledge or into a hazard; they don't look down"),
  hi_vis_survivor: A("survived", "AN 'I SURVIVED' VEST", "Survivor", "a hand-painted hi-vis vest that says I SURVIVED {YOU} with a tally of how many times", "louder and braver: they shout to bring others in", "the vest is bright: they're visible through smoke and paper storms, and from twice as far"),
  neck_brace: A("run_over", "A NECK BRACE", "Neck Brace", "a big foam neck brace with tyre marks on it", "they can't be run over again: they dive out of a car's path and shoot the tyres", "they can't look up: attack from above, from a roof or a grapple swing"),
  glued_shoes: A("slipped", "GLUED SHOES", "Sticky Feet", "shoes visibly glued to the soles with dried glue blobs; marbles stuck to them like studs", "they can't slip on marbles or peels any more", "they can't jump either: knock them off a ledge, or use the Leaf Blower and they slide, glued, along the floor"),
  bandages: A("burned", "BANDAGES", "The Singed", "head-to-toe bandages, eyebrows drawn on in marker, still smoking a little", "they're terrified of fire: they never go near flames and they shoot any fire source", "light anything (a cigarette, a barrel, oil) and they run from it in a straight line"),
  rubber_suit: A("shocked", "A RUBBER SUIT", "The Insulated", "a rubber fishing suit and yellow wellies two sizes too big; hair still standing up", "immune to tasers and electric hazards", "the suit is hot: they're slow, and soaking them makes it so heavy they waddle"),
  anchor_belt: A("flung", "AN ANCHOR BELT", "Grounded", "a belt with a little ship's anchor on a chain, which they drop on the floor before a fight", "they can't be flung, shoved or lassoed far (the anchor holds)", "the chain's only so long: step out of its reach and they can't follow; or grapple the anchor and drag them"),
  peas_hat: A("frozen", "A BAG OF FROZEN PEAS", "Cold Head", "a bag of frozen peas taped to their head and a scarf; teeth still chattering", "immune to frost", "fire melts the peas: they stop to complain about the drip and their hat falls in their eyes"),
  wok_helmet: A("headshot", "A WOK HELMET", "Wok Head", "a Bottom wok-dish worn as a helmet, dented where your bullet hit", "headshots bonk off the wok (once per fight it rings and they're fine)", "hit the wok with a melee: GONG. They're stunned for 2 s and the whole street hears it"),
  plank_armour: A("pinned", "PLANK ARMOUR", "The Boarded", "wooden planks nailed onto their chest and back, with the nail holes you made", "they can't be pinned to a wall", "planks burn: one fire hit and the armour falls off, still smouldering"),
  cardboard_box: A("bonked", "A CARDBOARD BOX", "Box", "a big cardboard box worn like a barrel, arm holes cut out, FRAGILE stamped on it", "the first big knockback hit just crumples the box", "the box is soggy if it's wet: soak it and it falls apart; or set it on fire"),
  back_pillow: A("backstabbed", "A PILLOW ON THEIR BACK", "Pillowback", "a floral pillow strapped to their back with a belt", "no backstabs: a heavy stab from behind goes into the pillow", "they turn very slowly to keep the pillow behind them: circle-strafe and hit them from the front while they're turning"),
  own_grapple: A("grappled", "THEIR OWN GRAPPLE", "Hook", "a homemade grapple: a garden hook on a washing line", "they grapple after you, and they yank you too", "their rope is a washing line: cut it with any melee or the katana mid-swing and they fall"),
  pin_badge: A("bubbled", "A PIN", "Pin", "a safety pin through their lapel, pointy end out", "they pop your bubbles instantly", "they keep popping things: drop a Rubber Duck near them and they pop it too, and it opens on them"),
  calculator: A("quizzed", "A CALCULATOR", "Top Set", "a pocket calculator on a lanyard and a gold star sticker on their forehead", "they answer any Pop Quiz instantly and get the heal", "they can't stop showing their working: throw a quiz and they stop for 2 s to do it out loud"),
  lawyer: A("verdict", "A LAWYER", "Appealing", "a tiny lawyer (a Fazzoletti associate in a briefcase) riding on their shoulder", "they appeal: the next Scales verdict on them is always NOT GUILTY", "shoot the lawyer first: they're very small and very upset"),
  scarf: A("bitten", "A CHAINMAIL SCARF", "Scarf", "a chainmail scarf over their neck and a little plaster", "your Bear Trap Jaw bite heals you nothing on them", "the scarf is metal: a taser through it stuns them twice as long"),
  nose_peg: A("burped", "A NOSE PEG", "Peg", "a wooden clothes peg on their nose", "your burps don't give you away to them any more", "they can't smell smoke either: they walk right into your smoke bomb and get lost"),
  your_photo: A("photographed", "YOUR PHOTO", "Fan", "your photo of them, framed, on a string round their neck, captioned in marker", "a disguise doesn't work on them: changing outfit at a safehouse doesn't lose their Late Fees", "they stop to show the photo to anyone nearby: a 3 s window every time they spot you"),
  face_tattoo: A("mocked", "A TATTOO OF YOUR FACE", "Number One Fan", "a badly drawn tattoo of your mannequin face on their forearm (or forehead)", "they get angrier: +20% damage while they can see you", "emote or spray at them again: they cry and sit down for 4 s"),
  roller_skates: A("outran", "ROLLER SKATES", "Wheels", "a pair of roller skates and knee pads", "they keep up with you on flat ground at sprint speed", "stairs: they can't do stairs. And marbles are a disaster"),
  goggles: A("smoked", "SWIMMING GOGGLES", "Goggles", "tight swimming goggles, a bit misty", "they see through smoke and paper storms", "the goggles steam up near fire or in the Gut: they're blind for 3 s"),
  sunglasses: A("flashed", "SUNGLASSES", "Shades", "very dark sunglasses, worn at all times, including indoors and at night", "immune to the NVG flash", "they can't see in the dark at all: fight them at night, or in the Lates' basement"),
  sandbags: A("shoved", "SANDBAGS", "Sandbags", "sandbags strapped to their legs and arms", "no knockback shoves them", "they can't jump: anything above knee height is out of their reach, and they sink in water and the acid lake"),
  oven_mitts: A("fragged", "OVEN MITTS", "Mitts", "big floral oven mitts", "they catch your grenades and throw them back", "cook the grenade first (hold it): mitts don't help with a frag that goes off in the hand"),
  zigzag: A("sniped", "A ZIGZAG", "Zigzag", "no item: they just never walk in a straight line again, and keep looking over their shoulder", "long-range shots are much harder (they zigzag)", "up close they're easy: the zigzag goes into your shotgun"),
  earmuffs: A("ticked", "EARMUFFS", "Muffs", "fluffy pink earmuffs", "they always hear your Punch-Clock ticking from further away", "they can't hear anything else: they don't hear their own backup arriving or your footsteps behind them"),
  mirror_shield: A("reversed", "A MIRROR", "Mirror", "a bathroom mirror held as a shield", "reflects lasers and Reverse Cards back", "they keep checking their hair in it: 2 s of vanity every time they raise it"),
  rubber_ring: A("duck", "A RUBBER RING", "Floaty", "an inflatable rubber ring round their waist, duck-shaped", "they're immune to the Rubber Duck's pull (they float)", "one pin or nail and it pops: they shoot up into the air and come down slowly"),
  gas_mask: A("gassed", "A GAS MASK", "Mask", "an old ☺ CORP gas mask with a smiley painted on", "immune to gas and smoke", "they can't hear well in it and they can't eat: they never pick up health"),
  duct_tape: A("shredded", "DUCT TAPE", "Taped", "half their clothes duct-taped back together after the Shredder", "the Shredder can't pull them in (they're taped to something)", "they're taped to something: whatever it is (a bin, a bike, a door) comes with them, slowly"),
  stomach_dog: A("dog", "A STOMACH-DOG", "Dog Person", "they've adopted a stomach-dog on a lead", "the dog sniffs you out through walls", "the dog will eat any dropped weapon: drop one and the dog drags them away to eat it"),
};

export const RESOLUTIONS = {
  closed: { name: "CASE CLOSED", how: "beat them while using their own counter (shoot the hat off, gong the wok, light the fire they fear) and then finish them", result: "they don't come back; the file is stamped and filed; you get their adaptation as a junk trophy item to sell or keep in the Locker", file: "CLOSED" },
  quit: { name: "THEY QUIT", how: "humiliate them three times in one meeting with three DIFFERENT triggers (slip, then fling, then a bubble...) without killing them", result: "they hand in their notice on the spot. You'll see them later with a desk job: a Late Desk clerk, a Lost & Found volunteer, a Returns Desk Zero trainee. They say something nice (barks.quit)", file: "RESIGNED" },
  ally: { name: "RELUCTANT ALLY", how: "spare them when they're down at the end of their third meeting (an F prompt: 'help them up'), or finish a small favour they ask (a grudge favour)", result: "they turn up once to help you in a fight in their district (barks.ally), and give you a one-step grudge favour side quest (fetch their thing back from another grudge, deliver a letter to their mum)", file: "SETTLED" },
  cold: { name: "GONE COLD", how: "don't meet them for 7 in-game days", result: "the file closes itself: they've moved on. No reward. The ledger notes it in a line", file: "COLD" },
  transferred: { name: "TRANSFERRED", how: "the ledger is full (12) and a new file opens", result: "the file you've seen least recently is moved out of your area: it's not deleted, it just leaves the active list (no reward)", file: "TRANSFERRED" },
};

export const RECAPS = {
  first_back: { when: "the first time a grudge enemy turns up after their file opened", title: "PREVIOUSLY BETWEEN YOU TWO",
    lines: ["{when}, in {district}: {what}.", "{name} remembers.", "{name} has {adaptation} now."] },
  rematch: { when: "every later return (once per session)", title: "PREVIOUSLY BETWEEN YOU TWO",
    lines: ["you and {name} have met {count} times.", "last time: {what}.", "they're wearing {trophy}. it's yours."] },
  killed_you: { when: "they killed you last time", title: "PREVIOUSLY BETWEEN YOU TWO",
    lines: ["{when}: {name} dispensed you back at a terminal.", "they kept {trophy}.", "they've been telling everyone in {district}."] },
  you_fled: { when: "you ran last time", title: "PREVIOUSLY BETWEEN YOU TWO",
    lines: ["{when}: you ran.", "{name} timed it.", "they have a stopwatch now. it's the most important thing they own."] },
  coop: { when: "a shared grudge in co-op", title: "PREVIOUSLY BETWEEN YOU LOT",
    lines: ["{when}, in {district}: {what}.", "{name} remembers all of you.", "{you} especially."] },
};

// ---------------------------------------------------------------- barks: 5 factions × 14 keys
export const BARKS = {
  unpaid: {
    spotted: ["oh it's YOU. i've got you in my calendar.", "remember me? i'm in your network now.", "circle back time, {you}.", "the grind never stops and neither do i."],
    killed_you: ["that's a learning experience for you.", "put it on your linkedin.", "i'm keeping your hat. it's equity.", "employee of the month. it's not me. but it could be."],
    you_fled: ["ran off last time. i timed it. eleven seconds. i've told everyone.", "you left the meeting early, {you}.", "back for round two? round one was a forfeit.", "you ran so fast i got a stopwatch. look. LOOK."],
    survived: ["i'm still here. i'm resilient. it's a soft skill.", "you didn't finish me. that's on you.", "i pivoted. i lived.", "i survived you. i've got a vest about it."],
    run_over: ["you ran me over with a SOFA.", "my neck's in a brace because of you and your little car.", "i can't look up. i've been training to not need to.", "i hear an engine and i dive. every time. at night too."],
    slipped: ["glued my shoes. you won't slip me twice.", "i'm still finding marbles in places, {you}.", "the floor's my enemy now. you made the floor my enemy.", "studs. i've got marble studs now. thanks."],
    burned: ["i've got no eyebrows. i've drawn them on.", "put the fire away. put the fire AWAY.", "i still smell like a barbecue.", "every time someone lights a cigarette i think it's you."],
    shocked: ["rubber suit. can't tase this. go on. try.", "my hair hasn't gone down since.", "you soaked me and zapped me. who does that.", "i'm insulated now. emotionally too."],
    flung: ["i went over three cars because of you.", "i've got an anchor now. i'm not going anywhere.", "i landed on a bus. the bus is fine.", "i had a nice flight. i didn't enjoy it."],
    humiliated: ["that's not a review, that's an attack.", "my whole team saw that.", "i'm putting that in my exit interview.", "you've made me a meme in the camp."],
    trophy: ["nice hat. oh wait. it's mine now.", "you looking for this? come and get your hat.", "i wear it to meetings.", "it's my lucky hat. you're my unlucky person."],
    quit: ["i've taken a job at the late desk. it's paid. i didn't know you could be paid.", "i'm out. i'm doing something with plants.", "i quit. i'm free. this is terrifying.", "thanks for ending my career. i mean that. it was a bad career."],
    ally: ["fine. i'll help. don't make it weird.", "network effect. you scratch my back.", "i'm on your side today. it's a trial period.", "i owe you. i hate that i owe you."],
    last_words: ["tell kev... the other kev...", "my lanyard... take my lanyard...", "this is a hostile takeover...", "worth it. for the exposure."],
  },
  timekeeping: {
    spotted: ["{you}. 14:02. noted.", "i have a file on you. it's very thick.", "you're overdue, {you}. personally overdue.", "this will only take a minute. i'll make it take longer."],
    killed_you: ["processed. i've kept a souvenir.", "that's a late fee paid in full.", "your hat has been confiscated as evidence.", "noted, logged, and laminated."],
    you_fled: ["fleeing a punctuality officer. that's a separate charge.", "you left at 14:06. i was there till 14:07.", "you can run. i can write it down.", "i timed your escape. it's in your file. it's embarrassing."],
    survived: ["i'm still on shift.", "you didn't clock me out.", "i have a vest. it says i survived. it's regulation.", "i've taken no sick days. i'll take none now."],
    run_over: ["you struck an officer with a vehicle. a sofa vehicle.", "neck brace. regulation colour.", "i've filed it under 'traffic'. and 'personal'.", "i dive at engines now. it's in my training."],
    slipped: ["slipping is not in the handbook. i've added it.", "glued footwear. approved by facilities.", "you made a punctuality officer fall over in public.", "i had marbles in my clipboard."],
    burned: ["my whistle melted.", "the bandages are temporary. the grudge is permanent.", "fire is against policy. you are against policy.", "i'm scared of candles now. on birthdays."],
    shocked: ["assaulting an officer with water. then electricity.", "rubber. head to toe. regulation rubber.", "my clipboard still crackles.", "my hair is not regulation and it's your fault."],
    flung: ["unauthorised flight. noted.", "i landed on the ☺ fountain. it smiled at me.", "anchored. i've requisitioned an anchor.", "i was airborne for 3.4 seconds. i counted."],
    humiliated: ["the other officers saw.", "i'll be the subject of a training video.", "you've undermined the schedule. and my dignity.", "i'm writing myself up for this."],
    trophy: ["evidence locker. your hat. my head.", "lost property: one hat. found: by me.", "i'll release it when you've paid.", "it's very comfortable. that's not the point."],
    quit: ["i've requested a transfer. to a desk. any desk.", "i've clocked out. permanently. thank you.", "i'm on the late desk now. i'm very sorry for your inconvenience.", "i resign. effective now. i've never done anything 'now' before."],
    ally: ["off the record: they're coming from the north.", "i'm on my break. my break is helping you.", "this didn't happen. i'll write it down so we remember it didn't.", "i'm making an exception. i've never made an exception."],
    last_words: ["note the... time...", "i was... on time...", "file it under... done...", "tell my clipboard..."],
  },
  collectors: {
    spotted: ["{you}. you owe me. personally now.", "your account's been flagged. by me. with a pen.", "i've added interest. emotional interest.", "collection day, {you}."],
    killed_you: ["the restocking fee's mine.", "i've repossessed your hat.", "paid in full. well. in part.", "that's a payment plan, that is."],
    you_fled: ["running from your debts. classic.", "i chased you for six streets. six. i'm fifty-two.", "you skipped your payment and your fight.", "next time, i've got the van."],
    survived: ["i always come back. like a bill.", "can't write me off.", "i've survived worse. i've collected from the family.", "i'm a recurring charge."],
    run_over: ["you ran over a repo man. in a car you hadn't paid for.", "neck brace. it's on my expenses.", "i'm repossessing your sofa-car. on principle.", "i hear an engine, i see your face."],
    slipped: ["marbles. on a public pavement. i've sent you an invoice.", "glued my boots. you won't get me twice.", "i fell on my clipboard. it left a mark.", "i'm billing you for the shoes."],
    burned: ["my van's still on fire.", "the bandages are going on your bill.", "i'm scared of lighters. i used to love lighters.", "i smell burning and i check my wallet."],
    shocked: ["water damage AND electrical damage.", "rubber suit. tax deductible.", "my teeth buzz when i think about you.", "you short-circuited my calculator."],
    flung: ["i went through a hedge in evergreen. they fined me.", "i'm anchored. i've anchored myself to the debt.", "you threw a collector. collectors don't get thrown.", "i landed on my own van."],
    humiliated: ["i'll be adding a humiliation surcharge.", "the whole queue saw.", "that's going in the final notice.", "i'm putting your name on the van."],
    trophy: ["your hat's collateral.", "pay up and you'll get your hat back. you won't pay up.", "i wear it on collection days.", "it's in the van. no, it's on my head. it's both."],
    quit: ["i've gone into debt counselling. on the other side.", "i've written it off. you. all of it.", "i'm a volunteer at the lost & found now. i give things BACK.", "i resign. please don't send me a bill."],
    ally: ["just this once. it's not a favour, it's a loan.", "i know where corp keeps its vans. come on.", "we're square. nearly square.", "consider this a payment holiday."],
    last_words: ["you still... owe me...", "final... notice...", "put it on... my tab...", "written off..."],
  },
  choir: {
    spotted: ["*sung* there you are, there you are... *not sung* we've been expecting you.", "*sung* the body remembers... *not sung* and so do i.", "you're back in the gut, {you}. it's digesting the news.", "*sung* hymn number four: you."],
    killed_you: ["*sung* returned to the body... *not sung* well, to a machine.", "i've kept your hat. it's a relic now.", "*sung* blessed is the respawn...", "the gut thanks you for your contribution."],
    you_fled: ["*sung* you ran, you ran... *not sung* we sang about it.", "the whole choir knows you ran.", "there's a verse about you now. it's not flattering.", "you left mid-hymn. that's rude in church."],
    survived: ["*sung* i rose again...", "still singing.", "the body heals. the body remembers.", "i got up. we always get up."],
    run_over: ["*sung* a car came down the avenue... *not sung* on a sunday.", "neck brace. i can only sing to the floor now.", "you drove on holy skin.", "i hear tyres in my prayers."],
    slipped: ["*sung* slipped upon the marbles... *not sung* in front of everyone.", "glued sandals. i'm sticking to the floor.", "the floor here is already slippery. you made it worse.", "marbles in my robes. still."],
    burned: ["*sung* i saw fire...", "my robe's half gone.", "no candles. no candles in the gut, ever, now.", "i'm afraid of my own censer."],
    shocked: ["*sung* lightning in the lung...", "rubber robe. it squeaks when i bow.", "the body conducts. i learnt that.", "my hair's a hymn now. a loud one."],
    flung: ["*sung* i flew over the stomach...", "anchored. the gut holds me now.", "i landed in a lung. it was nice. it wasn't nice.", "the choir watched me go."],
    humiliated: ["*sung* oh the shame, the shame...", "there's a verse about this. i wrote it. it's sad.", "you've made me a lesson in sunday school.", "the bishop laughed. the bishop never laughs."],
    trophy: ["your hat is a relic now. we pray to it on tuesdays.", "*sung* the hat, the hat...", "it's on the altar. it's on my head. it's both.", "come and worship it."],
    quit: ["i've left the choir. i'm in accounts now. it's quieter.", "*not sung* i'm done singing.", "i've taken a job on the tooth market. i count teeth. it's peaceful.", "thank you. i didn't know you could leave."],
    ally: ["*sung* this once, this once...", "the gut owes you. i owe you.", "i'll sing you through. stay behind me.", "*not sung* go left. the walls are hungry on the right."],
    last_words: ["*sung* the meeting... is moved...", "return me... to the body...", "*sung*...", "it's warm. it's always warm."],
  },
  goons: {
    spotted: ["you. you disrespected me.", "my friend. we have unfinished business.", "the family remembers. i remember better.", "{you}. sit. no, don't sit. fight."],
    killed_you: ["that's respect, that is.", "your hat. my hat now. a gift.", "nonna will be proud.", "you're covered. by me. on the floor."],
    you_fled: ["you walked away from respect.", "running's disrespect, my friend.", "the bridge saw you run. the whole bridge.", "next time you'll stay for dinner."],
    survived: ["you can't kill family.", "i got up. family gets up.", "i've got a vest. it's pinstripe.", "still standing. tiny hands, big heart."],
    run_over: ["you ran me over on respect bridge. on RESPECT bridge.", "a neck brace. pinstripe. very tasteful.", "i see headlights, i say a prayer.", "my suit's still got tyre marks."],
    slipped: ["you slipped me in front of the don.", "glued shoes. italian glue.", "the marbles are a disgrace. to me. to my family.", "i've got peel stains on my good trousers."],
    burned: ["the suit was my dad's.", "no fire. not near me. not near the sauce.", "bandages under the pinstripes. you can't tell. you can tell.", "i used to love a candle at dinner."],
    shocked: ["rubber. under the suit. very uncomfortable.", "you electrified a family man.", "my medallion still sparks.", "you wet my suit. then you zapped it."],
    flung: ["i went in the river. the sauce river.", "i've got an anchor. it's gold.", "nobody throws family.", "i landed in a restaurant. they charged me."],
    humiliated: ["pip saw. pip will never let it go.", "that's disrespect.", "you embarrassed me in front of my tiny hands.", "the jesters are writing a song about it."],
    trophy: ["your hat. it goes with the suit.", "come and ask for it. nicely.", "nonna says it suits me.", "it's on my head and it's staying there. with respect."],
    quit: ["i'm out. i'm opening a little café. tiny cups.", "the family's not for me. i'm doing claims. approving them.", "i've quit. tell nonna. no, don't tell nonna.", "thank you. i always wanted to cook."],
    ally: ["for respect. this once.", "the family owes you a favour. i'm the favour.", "i'll hold the bridge. go.", "you and me, we're square. with respect."],
    last_words: ["tell nonna... the sauce...", "respect...", "my suit... look after my suit...", "covered..."],
  },
};
