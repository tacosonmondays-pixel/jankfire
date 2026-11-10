// OVERDUE side questlines: THE BOTTOM. Quest schema as missions/act1.js, with kind: 'side', plus:
//   from    the act it becomes available            twist   the turn in its own little story (prose)
//   parts   optional [{ id, title, if, steps, do }] for questlines that continue later
// Side content keeps the game's goofy voice; it never jokes about the dead, the fallout or the Off-Spec (DESIGN §7.1).

export const SIDE_BOTTOM = {
  sq_bottom_deposit: {
    kind: "side", from: 1, title: "SECURITY DEPOSIT", giver: "sharon", district: "bottom",
    locations: ["bottom:landlord_pile", "bottom:soup_kitchen", "bottom:lostfound"], cast: ["sharon", "mr_deposit", "auntie"],
    requires: { missions: ["m02_sauce_run"], if: null },
    logline: "Mr. Deposit has taken a deposit off everyone who's slept near his rubble pile for fifty years. Nobody has ever got one back.",
    mechanic: { uses: ["fire", "washing_lines", "frag_smoke"], hook: "burn the armchairs off with the Cigarette, ride the washing lines round the shrinking pile, and post a grenade in the deposit box" },
    twist: "He can't stand up: the armchairs grew into him. The deposits are all he has. And his deed is the one Vacancy will staple to the Bottom's sale in Act IV.",
    beats: ["Sharon wants her deposit back (she paid it in soup in her twenties).", "Auntie gives you her itemised invoice: forty years of rent he owes the Lost & Found for 'storage of a man'.", "Serve it. He laughs so hard a key falls out.", "Collect three tenants' receipts (each a small errand: a lost cat, a stuck washing line, a roof leak).", "Boss: MR. DEPOSIT.", "His box bursts: fifty years of deposits rain on the Bottom."],
    steps: [
      { id: "ask", text: "ask sharon about the landlord", goal: { type: "talk", who: "sharon", talk: "deposit" } },
      { id: "invoice", text: "get auntie's invoice", goal: { type: "pickup", item: "auntie_invoice" }, marker: "bottom:lostfound" },
      { id: "serve", text: "serve mr. deposit the invoice", goal: { type: "talk", who: "mr_deposit", talk: "serve" }, marker: "bottom:landlord_pile" },
      { id: "receipts", text: "collect 3 tenants' receipts", goal: { type: "interact", target: "bottom:rooftops" }, notes: "three tiny errands around the terraces" },
      { id: "boss", text: "get the deposits back", goal: { type: "killBoss", boss: "landlord" }, boss: "landlord" },
    ],
    talks: {
      deposit: { with: "sharon", nodes: { start: { say: ["i paid that man a deposit when i was twenty-two. in soup. forty litres.", "i want it back. i don't want the soup back, it'd be off. i want the principle back."] } } },
      serve: { with: "mr_deposit", cam: "lowAngle", nodes: { start: { say: ["*A mountain of armchairs and keys, with a rubber face at the top wearing reading glasses.*", "a visitor! a tenant? no? a prospective tenant.", "*You hand him Auntie's invoice. He reads it. It's forty pages. It's in crayon. The total is circled four times.*", "'storage of a man'. 'wear and tear on the view'. 'emotional damp'. ha! HA! *a key falls out of him* she's good. she's very good.", "you're not getting it back, tenant. nobody gets their deposit back. it's the one law that survived the war."] } } },
    },
    choices: [],
    reward: { coupons: 800, loot: ["lt_boss_landlord"], flags: ["landlord_refunded"], standing: { bottom: 8 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. full refund.", meets: "MEETS EXPECTATIONS. partial refund.", see_me: "SEE ME. you paid a deposit." },
  },

  sq_bottom_one_shoe: {
    kind: "side", from: 1, title: "ONE SHOE GUY", giver: "shoe_guy", district: "bottom",
    locations: ["bottom:down_escalator", "gut:tooth_market", "gut:peristalsis"], cast: ["shoe_guy"],
    requires: { missions: ["m03_somethings_digesting"], if: null },
    logline: "A man by the Down Escalator sells one shoe for 10,000 coupons. He doesn't want to sell it. He wants the other one.",
    mechanic: { uses: ["lasso", "slide"], hook: "learn the lasso on the only thing small and fast enough: a living shoe surfing peristalsis" },
    twist: "The other shoe is in the Gut, and it's alive now: it walks, it has a tongue, and it doesn't want to go back. And Clement was born in a shoe shop on the first night of the Long Dark; the shoes were his dad's.",
    beats: ["Clement and his one brogue.", "Rumours: a shoe has been seen in Tooth Market, walking.", "Chase a living brogue down Peristalsis Avenue (it rides the contractions better than you).", "Catch it with the lasso. It cries.", "Choice: bring it back, or let it go."],
    steps: [
      { id: "meet", text: "talk to the man with one shoe", goal: { type: "talk", who: "shoe_guy", talk: "shoe" }, marker: "bottom:down_escalator" },
      { id: "rumour", text: "find the other shoe in the gut", goal: { type: "reach", zone: "gut:tooth_market" } },
      { id: "chase", text: "catch the shoe", goal: { type: "kill", who: "any", n: 1 }, marker: "gut:peristalsis", notes: "a non-lethal chase: the lasso catches it" },
      { id: "home", text: "", goal: { type: "flag", flag: "shoe_choice_made" } },
    ],
    talks: {
      shoe: { with: "shoe_guy", nodes: {
        start: { say: ["one shoe. very good shoe. ten thousand coupons.", "no, you can't have the pair. that's the problem."], opts: [["why don't you want to sell it?", "why"], ["where's the other one?", "where"]] },
        why: { say: ["*He puts a hand on it.* they were my dad's. he had a shoe shop on hillside road. i was born in it, the first night of the long dark. mum said the shoes were the only warm thing.", "the other one walked off when i was ten. the gut got into it."], next: "where" },
        where: { say: ["i'll know it when i see it. it'll be the one walking."] },
      } },
    },
    choices: [
      { id: "shoe", prompt: "The brogue squirms in your lasso. It has a little tongue. It's crying.", options: [
        { id: "return", label: "bring it back to Clement", do: ["flag:shoe_choice_made", "flag:shoe_returned"], consequence: "Clement puts it on. It stops crying when it's next to the other one. He limps anyway, out of habit, and gives you the Walking Sole (a secret implant)." },
        { id: "free", label: "let it go", do: ["flag:shoe_choice_made", "flag:shoe_freed"], consequence: "It runs off into the Gut. Clement laughs for the first time in years: 'good for it.' He gives you his one shoe 'for luck'. It's a legendary throwable (Sole Survivor). Weeks later, both shoes are seen walking together in Tooth Market." },
      ] },
    ],
    reward: { coupons: 300, flags: [], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. a pair.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you lost the other one too." },
  },

  sq_bottom_leg_day: {
    kind: "side", from: 1, title: "LEG DAY", giver: "lumps", district: "bottom",
    locations: ["bottom:gym", "bottom:long_stairs", "gut:stairs_top"], cast: ["lumps", "dumpling"],
    requires: { missions: ["m02_sauce_run"], if: null },
    logline: "Help Lumps train by carrying fridges up the Long Stairs. Drop one and it rolls all the way down.",
    mechanic: { uses: ["rig"], hook: "fridge physics up 1,000 steps, and Lumps' 'big one', an Overdrive Rig he built for carrying fridges" },
    twist: "It isn't training. Lumps is carrying the fridges up to the top of the stairs so that one day he can carry his mum down them. He's been practising the weight.",
    beats: ["Lumps' Gym: all the weights are fridges.", "Carry fridges up the Long Stairs (physics: drop one and it bounces down 1,000 steps, flattening bins; Dumpling commentates).", "Ten fridges. At the top, Lumps lines them up and looks over at the Gut.", "He tells you why."],
    steps: [
      { id: "gym", text: "spot lumps at the gym", goal: { type: "talk", who: "lumps", talk: "fridge" }, marker: "bottom:gym" },
      { id: "carry", text: "carry 10 fridges up the long stairs", goal: { type: "deliver", item: "fridge", zone: "gut:stairs_top" }, notes: "physics prop; the counter only goes up when one reaches the top; dropped fridges roll all the way down" },
      { id: "top", text: "", goal: { type: "talk", who: "lumps", talk: "why" } },
    ],
    talks: {
      fridge: { with: "lumps", nodes: { start: { say: ["leg day. you carry one, i carry one. we go up. we don't drop them.", ["dumpling", "last time he dropped one it went all the way down and through mrs. abara's kitchen."], "i said sorry. i bought her a fridge. it was the one i dropped."] } } },
      why: { with: "lumps", cam: "closeup", nodes: { start: { say: ["*Ten fridges in a row at the top of the stairs. Lumps sits on the last one, looking at the pink edge of the Gut.*", "mum's about a fridge and a half. i weighed her once. she hit me.", "one day i'm going to carry her down these. all of them. so i practise the weight.", "*he wipes his eyes* it's not the sunset. we're facing the wrong way for the sunset."], do: ["flag:leg_day_why", "standing.bottom:+2"] } } },
    },
    choices: [],
    reward: { coupons: 250, loot: ["lumps_ring"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. no fridges were dropped.", meets: "MEETS EXPECTATIONS. most fridges.", see_me: "SEE ME. mrs. abara wants a word." },
    notes: "Lumps' 'big one' is his copy of Pallet Jack, built on the outside because Lumps wouldn't let Bev cut him. After the train (m06) the intro changes: Lumps is carrying fridges up the Long Stairs because someone has to do Jack's round.",
  },

  sq_bottom_wok_the_dish: {
    kind: "side", from: 1, title: "WOK THE DISH", giver: "dumpling", district: "bottom",
    locations: ["bottom:rooftops", "bottom:school"], cast: ["dumpling", "auntie"],
    requires: { missions: ["m01_return_to_sender"], if: null },
    logline: "The Bottom's satellite dishes are woks. A storm has knocked them all out. Fix them by grappling between roofs while it's still blowing.",
    mechanic: { uses: ["grapple", "washing_lines"], hook: "a storm grapple puzzle: aim twelve wok dishes at the Spire while the wind swings you" },
    twist: "When the last wok is aligned, every TV in the Bottom picks up the same thing: a dead ☺ CORP channel that only broadcasts at 03:00. A test card, and a voice reading the Schedule. It's the first time anyone in the Bottom has heard the Missing Hour mentioned (and the start of the Satellite Ear trail).",
    beats: ["A storm: wind, rain, washing lines whipping.", "Twelve wok dishes across the stacked roofs. Each one needs aligning (aim it at the Spire) while the wind pushes you.", "Dumpling holds the TV aerial at the Crayon School and shouts.", "The last one: every TV shows a ☺ CORP test card."],
    steps: [
      { id: "storm", text: "wait for a storm", goal: { type: "flag", flag: "bottom_storm" } },
      { id: "woks", text: "realign 12 wok dishes", goal: { type: "interact", target: "bottom:rooftops" }, notes: "grapple and washing-line traversal in high wind; each wok is aimed at the Spire" },
      { id: "tv", text: "", goal: { type: "talk", who: "dumpling", talk: "test_card" }, marker: "bottom:school" },
    ],
    talks: {
      test_card: { with: "dumpling", nodes: { start: { say: ["*Every TV in the Crayon School flickers to a ☺ CORP test card. A smiling clock. A tinny voice:*", ["voice", "...03:00. no bookings. 03:00. no bookings. 03:00..."], "ghost, what's 03:00?", ["auntie", "*from the doorway* turn it off, dumpling.", ], ["auntie", "*after a moment* ...no. leave it on. write down what it says."]], do: ["flag:heard_test_card"] } } },
    },
    choices: [],
    reward: { coupons: 300, standing: { bottom: 4 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. perfect reception.", meets: "MEETS EXPECTATIONS. one channel.", see_me: "SEE ME. you're on the roof. you're in the wok." },
  },

  sq_bottom_lost_property: {
    kind: "side", from: 1, title: "LOST PROPERTY", giver: "dale", district: "bottom",
    locations: ["bottom:lostfound", "checkout:returns", "commute:ring_road", "pinstripe:restaurant", "numberworks:prime_lane"], cast: ["dale", "wristband", "gary"],
    requires: { missions: ["m01_return_to_sender"], if: null },
    logline: "Return ten items from the Lost & Found to their owners all over the city. One of them is a whole bus.",
    mechanic: { uses: ["cars", "grapple"], hook: "ten deliveries across the city, one of them a whole bus, one of them only reachable by grapple" },
    twist: "Item ten is a lunchbox with a note taped to it: 'don't be late tonight. it's our forty. love, j.' It has no owner left to return it to. Dale knows whose it is. It's one of Overtime's six memory fragments.",
    beats: ["Dale's ledger of lost things. Ten tags with names on them.", "Items: a pram (to a grandmother in Number Works), a trombone (a Punchline), a dog lead (the dog's still waiting), a wedding ring (Gary's), a bus (to the Unpaid, who are thrilled), a teddy (Wristband's, from the Stampede: he cries and gives it back to you to keep)...", "Item ten: the lunchbox. No owner. Dale tells you."],
    steps: [
      { id: "ledger", text: "get the lost property ledger from dale", goal: { type: "talk", who: "dale", talk: "ledger" }, marker: "bottom:lostfound" },
      { id: "return", text: "return 9 items to their owners", goal: { type: "deliver", item: "lost_property_tag", zone: "checkout:returns" }, notes: "nine deliveries across the city; the bus is driven" },
      { id: "lunchbox", text: "", goal: { type: "talk", who: "dale", talk: "lunchbox" } },
    ],
    talks: {
      ledger: { with: "dale", nodes: { start: { say: ["sixty-one years of lost things. people leave them, i keep them. it's a lost and found. the found's the hard bit.", "ten tags. ten names. some of them are still around. take them back. ...not the last one. bring the last one to me."] } } },
      lunchbox: { with: "dale", cam: "closeup", nodes: { start: { say: ["*A dented metal lunchbox. A note taped to the lid, in neat handwriting.*", "found it in the lobby of the spire. the day i went up there to fix the vending machines, years after. it was on the security desk.", "'don't be late tonight. it's our forty. love, j.'", "it's his. overtime's. sallow's. he never went home to eat it.", "keep it. he might want it back one day. ...people do, sometimes."], do: ["collect:ot_lunchbox"] } } },
    },
    choices: [],
    reward: { coupons: 600, standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. everything found its way home.", meets: "MEETS EXPECTATIONS. most things.", see_me: "SEE ME. you kept the bus." },
  },
  sq_bottom_line_run: {
    kind: "side", from: 1, title: "THE WASHING LINE RUN", giver: "dumpling", district: "bottom",
    locations: ["bottom:lostfound", "bottom:rooftops", "bottom:gym", "gut:stairs_top"], cast: ["dumpling", "sharon"],
    requires: { missions: ["m01_return_to_sender"], if: null },
    logline: "Dumpling has a stopwatch and a dare: ride the Bottom's washing lines from the Lost & Found to the Long Stairs without touching the ground.",
    mechanic: { uses: ["washing_lines", "grapple"], hook: "the first grapple time trial: forty-one lines, never touch the floor" },
    twist: "Dumpling's big brother did it once, years ago, and never told anyone how: there's a forty-first line, over the gym, that isn't on anyone's map. Ride all forty-one in one go under the gold time and a sock is waiting at the last pole with your name on it (the Sock Tendons secret).",
    beats: ["Dumpling's start board, in crayon: bronze, silver, gold, and a line marked 'the secret one'.", "The run: forty washing lines across the stacked roofs; touch the ground and Dumpling blows a whistle made of a biro.", "Sharon, from her kitchen window, on every lap: 'mind my sheets.'", "Gold: Dumpling's brother's old time. Then the forty-first line."],
    steps: [
      { id: "dare", text: "take dumpling's dare", goal: { type: "talk", who: "dumpling", talk: "dare" }, marker: "bottom:lostfound" },
      { id: "run", text: "ride the washing lines to the long stairs without touching the ground", goal: { type: "reach", zone: "gut:stairs_top" }, timer: 180, notes: "touching the ground resets you to the last pole; bronze 180 s, silver 120 s, gold 90 s; the timer is the bronze time" },
      { id: "done", text: "", goal: { type: "talk", who: "dumpling", talk: "time" } },
    ],
    talks: {
      dare: { with: "dumpling", nodes: { start: { say: ["ghost! ghost. i've got a stopwatch. it's dad's. it's for eggs.", "ride the lines from here to the long stairs and don't touch the floor. my brother did it in ninety seconds. he won't say how.", ["sharon", "*from a window* mind my sheets."]] } } },
      time: { with: "dumpling", nodes: { start: { say: ["*Dumpling looks at the egg timer for a long time.*", "...that's quite good. for a ghost.", "my brother says there's a secret line. over the gym. he says only real ones find it. i think he made it up. he makes a lot up. he's fourteen."], do: ["flag:line_run_done"] } } },
    },
    choices: [],
    reward: { coupons: 250, loot: ["washing_line"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you didn't touch the floor once.", meets: "MEETS EXPECTATIONS. you touched it a bit.", see_me: "SEE ME. you're in sharon's sheets." },
  },
};
