// OVERDUE main missions, Act III: "Off the Clock" (Number Works, Chrome Gristle, The Gut, Evergreen Acres, The Lates).
// The act's question: what are they planning? Same schema as missions/act1.js.

export const MISSIONS_ACT3 = {
  // ------------------------------------------------------------------ 18
  m18_nine_kilometres: {
    act: 3, n: 18, title: "NINE KILOMETRES", kind: "main", giver: "gordo", district: "numberworks",
    locations: ["bottom:gordo_den", "corphill:bleach_line", "numberworks:press", "numberworks:smokestacks"],
    cast: ["gordo", "nell", "mr_sevens", "foreman"],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "With Overtime's lanyard you can pull ☺ CORP's master Schedule off the network. Printed out, it's nine kilometres long, and it has a hole in it.",
    mechanic: { uses: ["shredder", "late_fees", "grapple"], hook: "the Timekeeping relay is a stealth climb with grapple shortcuts, and the backup shredder clears the paper storm on the way out" },
    beats: [
      "Gordo: if ☺ CORP keeps the dead for a reason, the reason's in the Schedule. Overtime's lanyard opens the Timekeeping relay on the Bleach Line.",
      "A stealth-or-loud job at the relay: plug the lanyard in, download the Schedule to a tape. Late Fees ★3.",
      "Number Works prints it (Sevens grudgingly if you made a DEAL; the union gleefully if they run it). P12: the paper waterfall.",
      "Gordo finds the gap: 03:00-04:00, the Missing Hour. Nobody's booked, not even ☺ CORP.",
      "Two odd entries in it: Evergreen Acres is the only district with slots at 03:00 ('CHARGE'), and the Lates has a single entry at 03:00 every night: 'DOOR'.",
      "Gordo, on the paper in the yard, tells you he was born at 03:14.",
    ],
    reveals: {
      learn: ["The Schedule has a blind spot: 03:00-04:00, an hour nobody is booked into.", "Evergreen charges something at 03:00. The Lates opens a 'door' at 03:00.", "Gordo was born in the Missing Hour; the Schedule put his family outside for it."],
      suspect: ["Whatever ☺ CORP is building happens in that hour."],
      withheld: ["Workforce Restoration (m23)."],
    },
    steps: [
      { id: "plan", text: "talk to gordo", goal: { type: "talk", who: "gordo", talk: "relay_plan" }, marker: "bottom:gordo_den" },
      { id: "relay", text: "download the schedule at the timekeeping relay", goal: { type: "interact", target: "corphill:bleach_line" }, marker: "corphill:bleach_line", notes: "needs overtime_lanyard; Late Fees ★3 on the way out" },
      { id: "escape", text: "lose the late fees", goal: { type: "loseFees" } },
      { id: "print", text: "print it at number works", goal: { type: "reach", zone: "numberworks:press" }, talk: "print" },
      { id: "p12", text: "", goal: { type: "flag", flag: "found_missing_hour" }, scene: "p12_nine_kilometres" },
      { id: "born", text: "", goal: { type: "talk", who: "gordo", talk: "born_late" } },
    ],
    talks: {
      relay_plan: {
        with: "gordo", cam: "overShoulder",
        nodes: {
          start: { say: ["*Gordo's den has a new piece of string, from the wall of pages to a picture of a clock.*", "auntie's right about one thing. corp doesn't keep anything for continuity. it keeps things to sell.", "so if it's kept the dead sixty-one years, it's got a plan for them. and corp writes every plan in the schedule. every minute of every day, booked.", "overtime's lanyard opens the timekeeping relay on the bleach line. you plug it in, it thinks employee number one wants a copy. nobody's ever said no to employee number one."], opts: [["and then what?", "then"], ["what if it's a trap?", "trap"]] },
          then: { say: ["then we print it. the whole thing. and we read it. all of it. every line.", "*he looks almost happy* i've wanted to read it my whole life."] },
          trap: { say: ["it's corp. everything's a trap. the trick is to be a trap they haven't priced in."] },
        },
      },
      print: {
        with: "nell", cam: "wide",
        nodes: {
          start: { branch: [["turf.numberworks=remainders", "union"], [null, "sevens"]] },
          union: { say: ["*Nell, on the press floor, megaphone in hand.* motion: we print ☺ corp's schedule and read it out loud in the yard. all in favour?", "*every hand in the yard.*", "motion carried. RUN IT."] },
          sevens: { say: [["mr_sevens", "*touches wood twice* you want to print their schedule on my press. you want to print the one thing they'd kill us for."], ["mr_sevens", "...fine. a deal's a deal. but if anyone asks, it was a misprint. touch wood."]] },
        },
      },
      born_late: {
        with: "gordo", cam: "closeup",
        nodes: {
          start: { say: ["*Later. The yard is empty. The Schedule is still lying across it in loops, kilometres of it, and Gordo is sitting in the middle of the white band where nobody is.*", "my mum was a cleaner in the spire. my dad fixed the lifts. they had a slot. a flat on floor 22. three rations a day.", "she went into labour on a shift change. 02:40. the medical bay was booked. she had me in a stairwell at 03:14.", "at 04:00 the schedule did its count and there were three of us in a slot for two. so they put us outside. a newborn, at night, in the ash."], opts: [["gordo...", "gordo"], ["that's why you want it burned.", "burn"]] },
          gordo: { say: ["don't. i'm not sad. i'm accurate.", "i was born in the missing hour. the one hour corp can't see. it's the only reason they didn't count me till it was too late.", "*he looks up the hill at the Spire.* and now i know what it's for."], do: ["flag:gordo_told_birth", "standing.bottom:+2"] },
          burn: { say: ["that's why i want it burned. and that's why i'm right. a clock that can throw a baby outside for being early is a clock you don't fix."], do: ["flag:gordo_told_birth"] },
        },
      },
    },
    choices: [],
    scenes: ["p12_nine_kilometres"],
    reward: { coupons: 500, items: ["schedule_printout"], flags: ["act3_started"], standing: { corp: -5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you read all nine kilometres.", meets: "MEETS EXPECTATIONS. you found the hole.", see_me: "SEE ME. you tripped over the schedule and fell into a chimney." },
  },

  // ------------------------------------------------------------------ 19
  m19_organ_donor: {
    act: 3, n: 19, title: "ORGAN DONOR", kind: "main", giver: "bev", district: "chromegristle",
    locations: ["gut:clinic_bev", "chromegristle:pawn", "chromegristle:jar_alley", "chromegristle:upsell_clinic"],
    cast: ["bev", "upsell"],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "Gristle & Sons' page of Option C was stolen and sold. Doctor Upsell bought it, because he knew what it really was: a patent.",
    mechanic: { uses: ["nailgun", "grapple", "remote"], hook: "Bev pins a kidney to show you the Nail Gun; Upsell's twelve arms are torn off one by one with the grapple" },
    beats: [
      "Bev: Upsell has the Gristle page in a jar in his clinic. He bought it off the Choir black market years ago.",
      "Chrome Gristle at night: neon, rain, jars that blink. Book a consultation at Upsell's clinic (pawn something at Organ Pawn to afford it, or have Bev forge a referral).",
      "The consultation: Upsell sells you procedures while explaining, with pride, what the page is.",
      "He tries to 'harvest' your Punch-Clock. Boss fight: DOCTOR UPSELL. Rip out his bad temporary implants with melee.",
      "The page: 'post-event workforce recovery'. Regrowth was meant to raise the dead as workers, on contract to ☺ CORP. It made the Gut instead.",
      "Bev takes two of her old hands back off him.",
    ],
    reveals: {
      learn: ["Gristle page: the dead were always meant to be a workforce. The Gut was the first attempt, and it failed.", "☺ CORP planned to own the dead's labour from the day it signed."],
      suspect: ["If Regrowth was attempt one, the warehouse is attempt two."],
      withheld: ["What attempt two looks like (m23)."],
    },
    steps: [
      { id: "bev", text: "talk to bev", goal: { type: "talk", who: "bev", talk: "jar" }, marker: "gut:clinic_bev" },
      { id: "afford", text: "get an appointment with doctor upsell", goal: { type: "flag", flag: "upsell_appointment" }, notes: "pawn an implant at Organ Pawn (you can buy it back later at a markup), or bring Bev a jar from Jar Alley so she forges a referral" },
      { id: "consult", text: "attend your consultation", goal: { type: "talk", who: "upsell", talk: "consult" }, marker: "chromegristle:upsell_clinic" },
      { id: "boss", text: "decline the procedure", goal: { type: "killBoss", boss: "upsell" }, boss: "upsell" },
      { id: "page", text: "take the page from the jar", goal: { type: "pickup", item: "page_gristle" }, do: ["flag:pages_gristle", "flag:read_page_gristle"] },
      { id: "home", text: "take the page to auntie", goal: { type: "deliver", item: "page_gristle", zone: "bottom:lostfound" }, talk: "wall" },
    ],
    talks: {
      jar: {
        with: "bev",
        nodes: {
          start: { say: ["*Bev's clinic. She's re-stitching her apron with two hands and smoking with a third. The fourth points at you.*", "you want the gut's page. course you do. it's in a jar. upsell's clinic, chrome gristle, top shelf behind the till.", "he bought it off the choir's back door years ago. paid a kidney. somebody's kidney.", "he doesn't keep it because it's evidence. he keeps it because it's a patent."], opts: [["how do i get to it?", "how"], ["you used to work for him.", "worked"]] },
          worked: { say: ["eleven years. he paid me in arms. i had four of my own once. two of them are on him now. they wave at me. i want them to stop waving at me."], do: ["flag:bev_wants_hands"], next: "how" },
          how: { say: ["book a consultation. he'll see anyone with coupons or parts. pawn something at organ pawn, buy it back after. or bring me a nice jar from jar alley and i'll write you a referral he can't say no to. i still have his letterhead. i have his everything."] },
        },
      },
      consult: {
        with: "upsell", cam: "closeup",
        nodes: {
          start: { say: ["*Doctor Upsell's clinic: twelve chairs, one doctor, twelve arms. Each arm holds a tool. One holds a card machine. Two of them are Bev's, and they wave.*", "welcome! welcome. a returning customer. well. a returned customer. ha. would you like fries with that kidney?", "have you considered a second spleen? everyone's getting one."], opts: [["i'm here about the jar on the top shelf.", "jar"], ["what's the procedure?", "procedure"]] },
          procedure: { say: ["ah, a value shopper. i'm offering, today only, the full workforce package: a reliability gland, a compliance lobe, and a lovely little cable port, here, at the back of the neck. you'll never be late again."], next: "jar" },
          jar: { say: ["*Three arms stop. Nine keep going.*", "the patent. you've got a good eye.", "*He takes the jar down himself. In it, floating, a page with the Gristle & Sons crest: POST-EVENT WORKFORCE RECOVERY.*", "gristle and sons signed this. regrowth, to raise the dead, on contract to ☺ corp. the war makes the bodies, regrowth makes them work, corp books their hours. growth!", "it didn't work, of course. the dead got up and became the gut. the old man messed up the formula. but the idea. the idea's beautiful.", "i've been trying to get it to work on the living. you'd be amazed how much a living person has to give."], opts: [["they were going to make the dead work. from the start.", "start"], ["give me the page.", "give"]] },
          start: { say: ["from the first day. corp didn't sign that page for the money. corp signed it for the staff.", "*he smiles with the whole face.* and now look at you. corp's trying again, isn't it? with you plastic ones. i'd love a look inside. hold still."], next: "give" },
          give: { say: ["no. but i'll take your punch-clock. it's a fascinating part. it's free. well. it's free for me.", "*all twelve arms rise.*"], do: ["flag:upsell_fight"] },
        },
      },
      wall: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*Auntie pins page four. She reads it twice, the second time with her finger under every word.*", "post-event workforce recovery.", "they were never going to let the dead stay dead. from the first minute.", "*she looks at you, and for once she doesn't look away.* ...they wanted you, rory. all of you. that was the point of the backup clause. it wasn't continuity. it was stock.", "that's four."] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 700, items: ["page_gristle"], loot: ["lt_boss_upsell"], flags: ["beat_upsell"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you declined every upgrade.", meets: "MEETS EXPECTATIONS. you kept your kidneys.", see_me: "SEE ME. you bought a second spleen." },
  },

  // ------------------------------------------------------------------ 20
  m20_the_missing: {
    act: 3, n: 20, title: "THE MISSING", kind: "main", giver: "lumps", district: "gut",
    locations: ["bottom:soup_kitchen", "gut:choir_lung", "gut:digester_wall", "gut:big_stomach", "gut:feed_dock"],
    cast: ["lumps", "sharon", "sister_agenda", "bishop", "dot", "mina", "dumpling"],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "Pages first, then mum. It's then. Go into the Gut for the nine, and for Mina.",
    mechanic: { uses: ["slide", "grapple", "marbles", "bloodcross", "lasso"], hook: "the rescue is an escort down Peristalsis Avenue on the beat; the Bishop's ulcers, the marble-slip weakness, and the lasso to drag digesters free" },
    beats: [
      "Lumps doesn't ask. He's standing at the Long Stairs with a crowbar and a pot of the yellow soup.",
      "Sharon tells you what the soup is for: Gristle doesn't eat it. It feeds the digester wall. Her soup has kept the Bottom's missing alive.",
      "Sister Agenda trades her minutes (a voice box if you did Choir Practice, or your word). The truck number (if you chased it) finds them fast; otherwise you search.",
      "The digester wall, deep. Mina, grown in to her waist, a grey braid, climbing gloves. 'you're late.' The reunion.",
      "To free anyone the Gut has to let go. The Choir's song holds it. Stop the Bishop.",
      "Boss fight: THE STOMACH BISHOP. In the acid lake, then inside him, then just a mouth.",
      "P6b: DEAL (Gristle stays; stops buying from ☺ CORP; releases the outer wall, keeps Dot as collateral) or TAKEOVER (the Bottom takes the Gut; the Choir stops singing; everyone can come out, but the oldest digesters won't survive leaving).",
      "Mina comes out either way. If Lumps gets his mum, he carries her down the Long Stairs.",
    ],
    reveals: {
      learn: ["The Bottom's soup keeps the digesters alive.", "Mina is alive. She remembers Rory. She forgives them in one second."],
      suspect: ["Hask is buying organs from the Gut (Agenda: 'UP THE HILL, priority')."],
      withheld: ["Whose body the organs go into (Hask, Act V)."],
    },
    steps: [
      { id: "stairs", text: "meet lumps at the long stairs", goal: { type: "talk", who: "lumps", talk: "then" }, marker: "bottom:long_stairs" },
      { id: "sharon", text: "", goal: { type: "talk", who: "sharon", talk: "soup_truth" }, marker: "bottom:soup_kitchen" },
      { id: "agenda", text: "get the choir's minutes", goal: { type: "talk", who: "sister_agenda", talk: "trade" }, marker: "gut:choir_lung" },
      { id: "wall", text: "find the bottom's missing in the digester wall", goal: { type: "reach", zone: "gut:digester_wall" } },
      { id: "mina", text: "", goal: { type: "talk", who: "mina", talk: "late" } },
      { id: "boss", text: "stop the choir: stop the stomach bishop", goal: { type: "killBoss", boss: "bishop" }, boss: "bishop", marker: "gut:big_stomach" },
      { id: "choice", text: "decide who runs the gut", goal: { type: "flag", flag: "gut_decided" }, scene: "p6b_deal_or_takeover" },
      { id: "out", text: "get them out", goal: { type: "escort", who: "mina", zone: "bottom:long_stairs" }, talk: "home" },
    ],
    talks: {
      then: {
        with: "lumps", cam: "closeup",
        nodes: {
          start: { say: ["*Lumps at the bottom of the Long Stairs with a crowbar in one hand and the yellow soup in the other.*", "pages first. then mum. you said.", "it's then."], opts: [["it's then.", "go"], ["(if you promised Dot) i promised her.", "promised", { if: "flag:promised_dot" }]] },
          promised: { say: ["*He nods, once. His eyes are wet and it isn't sunset.*", "she told you not to. i heard her. she says that about all the good promises."], next: "go" },
          go: { say: ["ok. nine hundred and ninety-nine stairs. then the gut. then mum. i'll count."] },
        },
      },
      soup_truth: {
        with: "sharon", cam: "closeup",
        nodes: {
          start: { say: ["*Sharon stops you at the kitchen door with a ladle across the doorway.*", "before you go in. you should know what the soup's for. you asked me once and i didn't say.", "gristle don't eat it. they feed it to the wall. to the ones in the wall. so they don't go soft. so they keep talking.", "i found out a year ago. a choir lass let it slip. every pot i've sent up that hill for twenty years has been dinner for dot. for everyone.", "*her voice cracks* i could've stopped. i'd have starved them. so i didn't stop."], opts: [["you kept them alive.", "alive"], ["why didn't you tell lumps?", "tell"]] },
          alive: { say: ["i kept them in the wall. that's not the same.", "*she pushes a pot into your arms* take this. the yellow. it's dot's favourite."], do: ["give:yellow_soup"] },
          tell: { say: ["because he'd have gone in. and he'd be in the wall. and then who'd carry the fridges.", "*she pushes a pot into your arms* take the yellow. it's her favourite."], do: ["give:yellow_soup"] },
        },
      },
      trade: {
        with: "sister_agenda", cam: "overShoulder",
        nodes: {
          start: { say: ["*Sister Agenda at her pew-desk. She's already open at the right page.*", "*sung* the nine, the nine... *not sung* you want the nine. and the old woman. truck forty-four. i wrote it all down."], opts: [["(if you chased the truck) truck forty-four. i saw it.", "saw", { if: "flag:chased_truck" }], ["(if you did Choir Practice) i brought your voice box.", "voice", { if: "done:sq_gut_choir_practice" }], ["please. i'll owe you.", "owe"]] },
          saw: { say: ["you saw it. then you know. they're in the east wall, by the feed dock. go quickly. the wall's hungry today."], do: ["flag:found_the_nine_fast"] },
          voice: { say: ["*She takes the voice box and holds it against her throat, and for one line she sings in a voice that is completely her own.* thank you. east wall. by the feed dock. go."], do: ["flag:found_the_nine_fast"] },
          owe: { say: ["everyone owes. it's the only thing this city makes. ...east wall. somewhere. i'll mark the pages. it'll take you longer."] },
        },
      },
      late: {
        with: "mina", cam: "closeup",
        nodes: {
          start: { say: ["*The east wall, by the feed dock. The nine, grown into the warm pink tissue at different depths, some chatting, some asleep. Dumpling's dad, waving. Old Ken. And further in, up to her waist, an old woman with a grey braid and Mall Rat climbing gloves, her eyes closed, her lips moving.*", "*Dot, nearby, sees you first* oh! plastic! mina, mina love, wake up. it's them. it's the one i told you about.", "*The old woman opens her eyes. She looks at your face for a long time. Then at the barcode. Then at your knee.*", { t: "...you're late.", do: ["anim:mina/late"] }], opts: [["i know.", "know"], ["mina?", "mina"], ["(cold) do i know you?", "cold", { if: "drift>=3" }]] },
          know: { say: ["*Something in her face gives way and is put back, fast, the way you'd put a plate back on a shelf before it falls.*", "sixty-one years. you'd better have a good excuse.", "*she reaches out with a gloved hand. You take it. It's warm. The wall is warm. Her hand is warmer.*"], next: "memory" },
          mina: { say: ["*She laughs, one short laugh, and it turns into something else halfway.*", "mina. yes. you used to say it like that when you couldn't find me in the shop. 'mina?' like a question you already knew the answer to.", "*she reaches out with a gloved hand. You take it.*"], next: "memory" },
          cold: { say: ["*She holds your gaze. She doesn't flinch.*", "no. no, you don't. that's all right.", "i remember enough for both of us. take my hand anyway. humour an old woman."], do: ["flag:mina_cold_meeting"], next: "memory" },
          memory: { say: ["*If Drift is low, a flash: a strawberry keyring on a backpack, a small hand in yours at a crossing, a voice saying 'rory, the green man'. If Drift is high, nothing. Just her hand.*", "i waited at the gate till mrs. okafor made me go. then i waited in the vents. then i waited here.", "don't you dare apologise. you were coming. i know you were coming. you'd have been on time if anyone had let you."], opts: [["i was coming. i'm here now.", "here"], ["i don't remember you. i'm sorry.", "sorry"]] },
          here: { say: ["*She squeezes your hand twice, quickly, like a signal from a long time ago.*", "then get me out of this wall, rory. my legs have gone to sleep for two months."], do: ["flag:mina_reunited", "drift:-1"] },
          sorry: { say: ["that's all right. you've got a lot of me missing. i've got a lot of you. we'll swap.", "now get me out of this wall. my legs have gone to sleep for two months."], do: ["flag:mina_reunited"] },
        },
      },
      home: {
        with: "mina", cam: "wide",
        nodes: {
          start: { say: ["*The Long Stairs, going down. The freed come out of the Gut blinking, wrapped in Choir robes, held up by Bottom people who've come up the stairs for them.*", "*If Dot is free: Lumps carries her down on his back, counting out loud, both of them crying, Dot telling him off for crying.*", "*If Dot was kept as collateral: Lumps walks down beside you, empty-handed, not counting.*", "*Dumpling runs up the stairs three at a time to their dad and stops calling you ghost.*", ["dumpling", "CHANGE! change! you got him! you got my dad!"], "*Mina, leaning on you, watching all of it.*", "this is the bottom, then. i lived on the top terrace forty years. i never once looked at it from up here."], opts: [["i'll get you a blanket.", "blanket"], ["mina. tell me about me.", "tell"]] },
          blanket: { say: ["get me tea. a blanket's for old people."] },
          tell: { say: ["*She thinks for a long time.*", "you were always running. you ran for buses you didn't need. you ran to the shop. you ran up the stairs to the flat so you could say you'd done it in forty seconds.", "and you always came back for me. every single time. except once.", "...i'll tell you the rest over tea. there's a lot of rest."], do: ["flag:mina_told_rory"] },
        },
      },
    },
    choices: [
      { id: "district_choice", prompt: "The Bishop is down. The Choir has stopped mid-note. The Gut is holding its breath. Who runs it?", options: [
        { id: "deal", label: "DEAL: Gristle & Sons stays, stops buying from ☺ CORP, lets the outer wall go", do: ["turf:gut=gristle", "flag:gut_deal", "flag:gut_decided", "fate:mina=freed", "fate:dot=gut", "flag:dot_collateral", "standing.corp:+3"], consequence: "The Bishop, smiling through a broken jaw, agrees: no more trucks from ☺ CORP, and the outer wall is released (Mina, Dumpling's dad and seven others). Dot is in the deep wall; he keeps her 'as collateral' until the contract is honoured. Lumps hears it. The Choir keeps singing, so the old digesters live. Gristle sells you organs at a discount and sends a choir to the raid." },
        { id: "takeover", label: "TAKEOVER: the Bottom takes the Gut", do: ["turf:gut=bottom", "flag:gut_takeover", "flag:gut_decided", "fate:mina=freed", "fate:dot=freed", "standing.bottom:+8", "standing.corp:-5"], consequence: "Lumps puts the crowbar into the deep wall and the Gut, without its song, lets go. Everyone from the Bottom comes out, Dot on Lumps' back. But the Choir stops singing for good, and the digesters who've been in the wall for forty years and more don't survive coming out; Sister Agenda writes every name. The Gut becomes the Bottom's, raw and dangerous, and Gristle & Sons is hostile everywhere." },
      ] },
    ],
    scenes: ["p6b_deal_or_takeover"],
    reward: { coupons: 900, loot: ["lt_boss_bishop"], flags: ["beat_bishop", "freed_the_nine"], standing: { bottom: 10 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you brought the missing home.", meets: "MEETS EXPECTATIONS.", see_me: "" },
  },

  // ------------------------------------------------------------------ 21
  m21_property_values: {
    act: 3, n: 21, title: "PROPERTY VALUES", kind: "main", giver: "gordo", district: "evergreen",
    locations: ["evergreen:culdesac", "evergreen:clubhouse", "evergreen:charging_garage", "evergreen:shelter"],
    cast: ["linda", "hoa", "gordo", "mailman"],
    requires: { missions: ["m18_nine_kilometres"], if: null },
    logline: "Evergreen Acres is the only district on the Schedule with something booked at 03:00: 'CHARGE'. Every window has a mannequin family waving.",
    mechanic: { uses: ["fire", "cars", "grapple"], hook: "mow lawns to stop the HOA regrowing, steal a militia golf cart, and swing the porch gutters round the cul-de-sac" },
    beats: [
      "Evergreen: perfect lawns, a laugh track you can hear in the street, a mannequin family in every window waving at the same time.",
      "Linda Fairway and the HOA: 'your lawn is 2 mm too long.' You're fined on sight. Every fine is a debuff.",
      "Garage 03 behind any house: a charging dock with a ☺ CORP cable. At 03:00 the families walk into their garages and plug themselves in.",
      "Down into the shelter where Evergreen waited out the Long Dark: the pilot agreement on the wall. The families are recordings of the dead, loaded with the Schedule. Some of them are Linda's own family.",
      "Linda, in the shelter, is eleven years old again. The first thing she saw when they came up was the dead city, and she decided it wasn't there.",
      "The HOA rises from the lawns. Boss fight: THE HOA.",
      "Choice: unplug Evergreen's pilot (the families stop, forever) or leave them waving.",
    ],
    reveals: {
      learn: ["Workforce Restoration has a pilot: Evergreen's mannequin families are the Machine's dead with the Schedule loaded.", "They're delivered through the Lates at 03:00 and update every night.", "Loaded with the Schedule, the dead are cheerful, tidy and never ask anything."],
      suspect: ["The Lates' 03:00 'door' is the delivery route."],
      withheld: ["The scale of it (m23)."],
    },
    steps: [
      { id: "arrive", text: "find out what evergreen charges at 03:00", goal: { type: "reach", zone: "evergreen:culdesac" }, talk: "fined" },
      { id: "garage", text: "look in a garage at 03:00", goal: { type: "interact", target: "evergreen:charging_garage" }, if: "clock.evergreen=03:00-03:30", notes: "a stealth wait: the families walk past you to their docks. One stops and waves at you. Its lanyard reads a name from the Machine's archive." },
      { id: "shelter", text: "get into the shelter", goal: { type: "reach", zone: "evergreen:shelter" } },
      { id: "linda", text: "", goal: { type: "talk", who: "linda", talk: "shelter" } },
      { id: "boss", text: "survive the homeowners association", goal: { type: "killBoss", boss: "hoa" }, boss: "hoa", marker: "evergreen:culdesac" },
      { id: "pilot", text: "decide about the pilot", goal: { type: "flag", flag: "evergreen_decided" } },
    ],
    talks: {
      fined: {
        with: "linda", cam: "overShoulder",
        nodes: {
          start: { say: ["*A perfect cul-de-sac. Sprinklers ticking. A laugh track from nowhere. In every window, a mannequin family: mum, dad, two kids, waving. At exactly the same time.*", "*Linda Fairway walks up the drive, smiling, clipboard out.*", "hello! you must be new. we don't get new.", "your lawn is 2 mm too long.", "i'm sorry? oh, you don't have a lawn. that's worse. that's a fine."], opts: [["what are the people in the windows?", "windows"], ["what happens at 03:00?", "three"]] },
          windows: { say: ["the families? they wave. isn't that nice? they always wave.", "they're so tidy. they never complain. property values have never been higher."], next: "three" },
          three: { say: ["*The smile doesn't move at all.*", "per section four, the bylaws are not to be discussed after dark. and per section nine, the dark is not to be discussed."], do: ["flag:fined_by_hoa"] },
        },
      },
      shelter: {
        with: "linda", cam: "closeup",
        nodes: {
          start: { say: ["*The shelter under the cul-de-sac: concrete, bunks, a mural of a sunny street painted by children, thirty years of tally marks. On the wall, framed like a certificate: ☺ CORP WORKFORCE RESTORATION · PILOT AGREEMENT · EVERGREEN ACRES HOA. Signed: L. Fairway. Countersigned: M. Hask.*", "*Linda is sitting on a bottom bunk. She's taken her cardigan off. She looks small.*", "i was born down here. i was eleven when the door opened.", "everyone went up the stairs cheering, and the first thing i saw was the city. all of it. the way it was. the valley. the bodies.", "and i decided it wasn't there."], opts: [["the families are the dead.", "dead"], ["you signed this.", "signed"]] },
          dead: { say: ["they're recordings. from the machine. the nice lady from the pilot programme sends them through the lates at three in the morning. they update at three. they charge.", "*she looks at the mural.* the dad in number four is my dad. he died the day before we came up. he waves at me every morning. he's never once asked how i am."], do: ["flag:knows_pilot"], next: "signed" },
          signed: { say: ["the lawns are perfect. nobody complains. nothing bad has happened here in forty years.", "*She looks at you, and she's eleven.* please don't make it be there again."], do: ["flag:knows_pilot"] },
        },
      },
    },
    choices: [
      { id: "pilot", prompt: "In every garage, a family is plugged into a ☺ CORP cable. You can pull Evergreen's main feed.", options: [
        { id: "unplug", label: "unplug the pilot", do: ["flag:evergreen_unplugged", "flag:evergreen_decided", "standing.corp:-5", "standing.bottom:+2"], consequence: "Every mannequin in Evergreen stops mid-wave and stays like that, hand up, forever. Linda sits on her lawn beside her father and doesn't move for a day. ☺ CORP loses its pilot data (the Restoration's Act IV defences are slower to update). The HOA is hostile to you for the rest of the game; in LATE, Linda plants vegetables." },
        { id: "leave", label: "leave them waving", do: ["flag:evergreen_left", "flag:evergreen_decided", "standing.corp:+2"], consequence: "The families keep waving. Linda thanks you very quietly and hates you a little. The HOA becomes a grudging ally (its militia holds Dividend Road's lower junction in the raid). Evergreen is the model for the ON TIME ending." },
      ] },
    ],
    scenes: [],
    reward: { coupons: 700, loot: ["lt_boss_hoa"], flags: ["beat_hoa"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. lawn mowed.", meets: "MEETS EXPECTATIONS. fined eleven times.", see_me: "SEE ME. your lawn is 40 cm too long." },
  },

  // ------------------------------------------------------------------ 22
  m22_the_waiting_room: {
    act: 3, n: 22, title: "THE WAITING ROOM", kind: "main", giver: "pauline", district: "lates",
    locations: ["lates:waiting_room", "lates:canteen", "lates:remainder_office", "lates:tuesday_tower"],
    cast: ["pauline", "perpetual_tuesday", "gus"],
    requires: { missions: ["m18_nine_kilometres"], if: null },
    logline: "In the Lates it has been the same Tuesday for sixty-one years. Pauline from Accounts knows every second of it, and she knows a man who has been late for the same meeting twenty-two thousand times.",
    mechanic: { uses: ["loops", "frost", "remote"], hook: "the Lates teaches Loops (fall forever, keep the speed); freeze or rewind Neville to break his loop" },
    beats: [
      "The Waiting Room: infinite, with chairs. Pauline finds you, because you're new, and nobody is ever new.",
      "She knows the loop: 09:00-17:30, then 09:00 again. Loopers don't age. She's watched a door open in the sky at 03:00 in the gap of the loop.",
      "To get to 03:00 you have to get the loop to let you stay past 17:30. It resets every time Neville Brisk misses his meeting.",
      "Neville: the man who left the Remainder downtown office at 09:00 with an envelope for a 16:59 meeting in the Spire. He's become the Perpetual Tuesday: a hundred copies of himself, running.",
      "Boss fight: THE PERPETUAL TUESDAY. The fight loops every 60 s, damage carries over, your past self's bullets replay.",
      "Beaten, one man hands you the envelope: 'could you take this? i'm late.' Inside: Remainder's revised Q4 numbers. TARGET MET (+0.5%).",
    ],
    reveals: {
      learn: ["The Q4 numbers were revised that morning: the divisions hit target by 0.5%. Option C wasn't necessary.", "The memo never arrived."],
      suspect: ["Hask's 'half a percent' call at 17:10 was this. She knew.", "The world ended over a late memo, or over something worse."],
      withheld: ["That Hask launched knowing (Act V)."],
    },
    steps: [
      { id: "arrive", text: "find somebody who isn't waiting", goal: { type: "reach", zone: "lates:waiting_room" }, talk: "new" },
      { id: "lunch", text: "have lunch with pauline (it's lasagne)", goal: { type: "reach", zone: "lates:canteen" }, talk: "loop" },
      { id: "office", text: "find neville at the remainder office before 09:01", goal: { type: "reach", zone: "lates:remainder_office" }, notes: "you chase Neville across the looping streets; he becomes the boss at Tuesday Tower" },
      { id: "boss", text: "get neville to his meeting", goal: { type: "killBoss", boss: "perpetual_tuesday" }, boss: "perpetual_tuesday", marker: "lates:tuesday_tower" },
      { id: "envelope", text: "", goal: { type: "talk", who: "perpetual_tuesday", talk: "envelope" } },
    ],
    talks: {
      new: {
        with: "pauline", cam: "closeup",
        nodes: {
          start: { say: ["*The Waiting Room: chairs to the horizon, a ticket machine on ticket 0, fluorescent hum. A woman in a 61-year-old cardigan with a mug that says WORLD'S OKAYEST ACCOUNTANT stands up and stares at you.*", "you're new.", "nobody's new. this is very exciting and i hate it.", "i'm pauline. accounts. i've been here since 09:00. that's twenty-two thousand days ago, give or take. i keep count."], opts: [["how do you know it's been that long?", "count"], ["what happens at 17:30?", "1730"]] },
          count: { say: ["*She shows you the notebook. Tiny handwriting. Every page the same day, timestamped to the second, with small differences circled.*", "i write down everything. the lift dings at 09:04. it's empty. it's always empty. gus drops his fork at 12:41. at 17:30 it all goes back to 09:00. except me. i keep the notebook in my head."], next: "1730" },
          "1730": { say: ["it resets. everyone forgets. i don't. i don't know why. i think i'm too stubborn to reset.", "come and have lunch. it's lasagne. it's been lasagne for twenty-two thousand days."] },
        },
      },
      loop: {
        with: "pauline", cam: "overShoulder",
        nodes: {
          start: { say: ["*The canteen. Gus drops his fork at 12:41, exactly. Pauline doesn't look.*", "the loop resets when one man misses one meeting. neville brisk. remainder industries. he leaves the downtown office at 09:00 with an envelope for a 16:59 in the spire. he never gets there.", "i've tried to help him four thousand times. i've driven him. i've carried him. once i tied him to a bus.", "he's not a man any more. he's... a lot of men. you'll see."], opts: [["what's in the envelope?", "envelope"], ["what's at 03:00?", "door"]] },
          envelope: { say: ["numbers. he says 'it's important, it's very important, it's numbers'. he's from remainder. it's always numbers."], next: "door" },
          door: { say: ["*She puts her fork down.*", "nobody else has ever asked me that.", "the loop has a gap. 17:30 jumps to 09:00, but if you're awake, you feel the bit in between. an hour where nobody is. i've been awake in it.", "at 03:00 a door opens in the sky over the waiting room. trucks come through it from nowhere. they go to evergreen.", "if neville gets to his meeting, the loop might let us stay past 17:30. then you can see the door for yourself."], do: ["flag:pauline_told_door"] },
        },
      },
      envelope: {
        with: "perpetual_tuesday", cam: "closeup",
        nodes: {
          start: { say: ["*The copies peel away and fall, one by one, into the looping street, and fade. One man is left: thirty-four, brown suit, sweat-soaked, holding a manila envelope with REMAINDER INDUSTRIES · URGENT · BOARD 16:59 on it.*", "sorry i'm late. sorry. sorry i'm late.", "could you take this? i'm late. it's important. it's very important. it's numbers.", "*He presses it into your hands, and his face is the face of someone putting down something heavy for the first time in a very long time.*"], opts: [["*open it*", "open"]] },
          open: { say: ["*Inside: one sheet. REMAINDER INDUSTRIES · Q4 REVISED (09:00) · ALL DIVISIONS · TARGET MET (+0.5%). A pencilled note: 'the 17:30 thing won't be needed now. N.'*", "*Neville sits down on a bench. He looks at his watch. It's moving.*", "they didn't need to do it. did they. whatever it was.", "i was carrying the reason not to. all day. i was just late."], do: ["give:late_memo", "flag:read_late_memo"] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 700, items: ["late_memo"], loot: ["lt_boss_perpetual_tuesday"], flags: ["beat_perpetual_tuesday"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you've seen this one.", meets: "MEETS EXPECTATIONS. it's still tuesday. but less.", see_me: "SEE ME. you were late." },
  },

  // ------------------------------------------------------------------ 23
  m23_workforce_restoration: {
    act: 3, n: 23, title: "WORKFORCE RESTORATION", kind: "main", giver: "pauline", district: "lates",
    locations: ["lates:tuesday_tower", "lates:missing_door", "lates:warehouse"],
    cast: ["pauline", "gordo"],
    requires: { missions: ["m22_the_waiting_room", "m21_property_values", "m19_organ_donor"], if: null },
    logline: "At 03:00, in the hour nobody's booked into, a door opens in the sky over the Lates. Behind it is what ☺ CORP has been planning for the dead.",
    mechanic: { uses: ["nvg", "grapple"], hook: "the Missing Hour is grey: night vision goggles and a grapple swing down the cable trunks above the rows" },
    beats: [
      "With Neville delivered, the loop lets you stay past 17:30. You wait with Pauline and Gordo on Tuesday Tower.",
      "C13: 03:00, the grey, the door, the warehouse: mannequin bodies to the horizon, cables to the Machine's archive, the Master Clock's schedule. PROTOTYPE 0 (SCHEDULE NOT LOADED).",
      "Walk the rows (playable): lanyards with names from the archive. If you look, you can find Cale's colleagues, the man with the fish tank, a lanyard that says E. SALLOW (spare).",
      "The mannequins wake and turn. Restoration Security (HR Tactical) comes through the door. Escape down the grey stairs before 04:00, when the hour closes.",
      "Pauline on the tower after, watching 04:00 become 09:00: 'that's what they want the whole city to be. this. tuesday, forever. just tidier.'",
    ],
    reveals: {
      learn: ["Workforce Restoration: every recording in the Machine loaded into a mannequin body and run on the Master Clock, forever, unpaid, obedient.", "You were the prototype. Your recording came out without the Schedule because you were 'terminated'. ☺ CORP was studying you so it could delete you.", "There's a spare body for Overtime too."],
      suspect: ["The Bottom isn't in the plan at all. Living people who can't pay aren't on the schedule."],
      withheld: ["The living are being sold to Vacancy (Act IV)."],
    },
    steps: [
      { id: "wait", text: "wait for 03:00 on tuesday tower", goal: { type: "reach", zone: "lates:tuesday_tower" } },
      { id: "c13", text: "", goal: { type: "flag", flag: "seen_c13" }, scene: "c13_workforce_restoration" },
      { id: "rows", text: "walk the rows", goal: { type: "interact", target: "lates:warehouse" }, talk: "rows", notes: "optional lanyards to read (collectibles: cr_lanyard_*)" },
      { id: "escape", text: "get out before 04:00", goal: { type: "reach", zone: "lates:tuesday_tower" }, timer: 300, fail: { type: "timer" }, notes: "fail = the hour closes with you inside: you wake at the Lost & Found terminal, minus a restocking fee, and the step is done anyway (the Machine dispenses you)" },
      { id: "after", text: "", goal: { type: "talk", who: "pauline", talk: "tidier" } },
    ],
    talks: {
      rows: {
        with: "gordo",
        nodes: {
          start: { say: ["*Barks as you walk the rows; each lanyard can be read:*", "*a lanyard: K. OSEI · SENIOR ANALYST · 60TH FLOOR. You knew her. Her desk was by the window. She gave you a biscuit on your first day.*", "*a lanyard: D. PRYCE · FACILITIES. He's holding a fish tank. The body is holding a fish tank.*", "*a lanyard: E. SALLOW · SPARE (3 of 3).*", "they've even got spares for him.", "*a lanyard, at the end of a row, a single empty dock with no body in it: CALE R. 4417 · PROTOTYPE 0 · RETURN TO DOCK.*", "...they kept you a parking space."] },
        },
      },
      tidier: {
        with: "pauline", cam: "wide",
        nodes: {
          start: { say: ["*Tuesday Tower, 04:00. The grey drains away. The door folds into nothing. The sky goes yellow-beige. 04:00 becomes 09:00 with a little jolt, and below, the Loopers start their Tuesday again.*", "that's what they want the whole city to be. this. tuesday, forever.", "just tidier.", "*She opens her notebook to a clean page for the first time in twenty-two thousand days and writes: 03:00. warehouse. tell someone.*", "i'm telling you. i've never had anyone to tell."], opts: [["we'll stop it.", "stop"], ["what happens to you if we do?", "you"]] },
          stop: { say: ["good. please. i'd like a wednesday. i'd like to find out it's horrible."] },
          you: { say: ["i find out i'm forty-six and everyone i knew outside is dead.", "*she shrugs* i've had twenty-two thousand days to get used to the idea. i'm ready for one day to not get used to it."] },
        },
      },
    },
    choices: [],
    scenes: ["c13_workforce_restoration"],
    reward: { coupons: 500, flags: ["knows_restoration", "knows_prototype"], standing: { corp: -5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you found your parking space.", meets: "MEETS EXPECTATIONS. you got out by 04:00.", see_me: "SEE ME. you were restocked." },
  },

  // ------------------------------------------------------------------ 24
  m24_the_split: {
    act: 3, n: 24, title: "THE SPLIT", kind: "main", giver: "auntie", district: "bottom",
    locations: ["bottom:lostfound", "bottom:dale_shed"],
    cast: ["hask", "dale", "auntie", "lumps", "gordo", "mina", "pritchard"],
    requires: { missions: ["m23_workforce_restoration", "m20_the_missing"], if: null },
    logline: "Marion Hask calls you on the Machine's own terminal with an offer, and the Bottom splits three ways over what to do about it.",
    mechanic: { uses: ["implants"], hook: "a talking mission: the split is about what you are, and your installed implants change which lines you're offered" },
    beats: [
      "C14: Hask on Dale's terminal. The Long Dark footage. 'the dead do not mind working.' The offer: a name, a job, a life that doesn't end.",
      "Pritchard rings back on the pager to book you a slot. You can talk to him.",
      "Dale's confession: the monthly maintenance reports, the batteries, forty years. That's how she got in. And Mina: she asked him every year.",
      "If Mina is free, she slaps Dale. He says thank you.",
      "If you deferred forgiving Auntie, you can do it now.",
      "C15: the split. Lumps: take the deal for the Gut's people. Gordo: blow up the Master Clock at 03:00. Auntie: publish all six pages.",
      "You choose whose plan the raid follows.",
    ],
    reveals: {
      learn: ["Dale has reported to ☺ CORP Facilities every month for forty years.", "Hask's case: the Long Dark, the famine; the Schedule kept the Spire alive.", "Lumps has been writing to Pritchard."],
      suspect: ["Hask needs you: a prototype that came out free is a flaw she can't afford."],
      withheld: ["Why you came out free, in her words (C20).", "What she did at 17:10 (Act V)."],
    },
    steps: [
      { id: "c14", text: "", goal: { type: "flag", flag: "seen_c14" }, scene: "c14_the_offer", marker: "bottom:dale_shed" },
      { id: "pritchard", text: "answer the pager", goal: { type: "talk", who: "pritchard", talk: "booking" } },
      { id: "dale", text: "talk to dale", goal: { type: "talk", who: "dale", talk: "batteries" }, marker: "bottom:dale_shed" },
      { id: "forgive", text: "", goal: { type: "talk", who: "auntie", talk: "pending" }, if: "flag:deferred_forgiveness" },
      { id: "c15", text: "the whole bottom's waiting", goal: { type: "flag", flag: "plan_chosen" }, scene: "c15_the_split", marker: "bottom:lostfound" },
    ],
    talks: {
      booking: {
        with: "pritchard",
        nodes: {
          start: { say: [["pager", "*BEEP BEEP BEEP. A tinny voice, fast, breathless.*"], "hello! hi. this is owen pritchard, executive assistant to the chief punctuality officer. sorry. sorry, that's my 23:00 alarm. and my 23:01.", "ms. hask would like to offer you an onboarding interview. i have a four-minute window on the 3rd at 22:16. or i can make one. i'll make one."], opts: [["are you the one who answers lumps' letters?", "lumps"], ["what's onboarding?", "onboard"], ["no.", "no"]] },
          lumps: { say: ["*a long silence on the pager*", "...he writes very nicely. he always asks how i am. nobody asks how i am. i'm booked.", "i've been lowering his mother's price. don't tell anybody. i'll be deleted. i'll be rescheduled into a skip."], do: ["flag:pritchard_soft"] },
          onboard: { say: ["a name, a lanyard, a slot. you'd be... um. the template. for the rest. they'd all be a bit like you. but on time.", "*quieter* there are eleven thousand four hundred and two people from the bottom who aren't on the staffing table. i typed every one. i just... thought you should know that."], do: ["flag:pritchard_warned"] },
          no: { say: ["that's... that's ok. i'll put you down as 'tentative'. i put everyone down as tentative. it's the kindest box."] },
        },
      },
      batteries: {
        with: "dale", cam: "closeup",
        nodes: {
          start: { say: ["*Dale's shed. Forty years of batteries, stacked like bricks, floor to ceiling, every one stamped ☺ CORP FACILITIES. A pager on a nail.*", "...she got in through my terminal. because my terminal reports to her. every month. 'machine status: humming. tray: empty. anomalies: none.' for forty years.", "they pay me in batteries. look at them. that's what i cost. that's what she costs.", "the month you came out i wrote 'anomalies: one'. i didn't think. sixty years of habit. that's how they knew where to look."], opts: [["why?", "why"], ["did mina ask you to let me out?", "mina", { if: "flag:knows_mina" }]] },
          why: { say: ["because the bottom needed light. and because she was going to keep humming whether i fixed her or not, and if i didn't fix her they'd send someone who'd ask fewer questions.", "...those are reasons. they're not excuses. i know the difference. i've had a long time to learn it."], next: "mina" },
          mina: { say: ["*He doesn't look up.*", "every year. new year's eve. she'd come down the stairs with a bottle and sit where you're standing and say 'is rory in there, dale?'", "and i'd say 'i don't know, love. she doesn't give anything back.'", "i knew. i could see the sim on the menu. i just never pressed it.", "then she stopped coming. she got old. and then they took her. and the next week you walked off the edge of the map for the four hundredth time. and i pressed it."], branch: [["fate.mina=freed", "slap"]] },
          slap: { say: [["mina", "*Mina is in the doorway. She's heard all of it. She crosses the shed in four steps and slaps Dale across the face, hard, with a Mall Rat glove.*"], "*Dale doesn't move.* ...thank you.", ["mina", "*She sits down next to him on a stack of batteries and takes his hand, the same way she took yours.* idiot."]], do: ["flag:mina_slapped_dale"] },
        },
      },
      pending: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*Auntie, at the long table, writing. Her notebook is open at the page that says 'pending.'*", "you said ask you again."], opts: [["i forgive you.", "yes"], ["not yet.", "no"]] },
          yes: { say: ["*She crosses out 'pending' and writes 'forgiven. 1 entry.' in crayon. Her hand is very steady until the last letter.*", "...thank you, rory."], do: ["flag:forgave_auntie", "unflag:deferred_forgiveness", "drift:-1"] },
          no: { say: ["*She nods, and leaves it.* pending. that's fair. i'll take pending."] },
        },
      },
    },
    choices: [
      { id: "whose_plan", prompt: "Lumps, Wee Gordo and Auntie are all looking at you. Whose plan does the Missing Hour raid follow?", options: [
        { id: "lumps", label: "lumps: take what she's offering for the gut's people, then turn it on her", do: ["flag:plan_lumps", "flag:plan_chosen", "standing.corp:+5"], consequence: "Act IV's m28 is HEADCOUNT: you play Hask's onboarding to get the Bottom's people on the staffing table and Dot out (if she's still in), then use the access to open the Spire at 03:00. Lumps is with you in everything. Gordo goes off on his own with his charges. In ON TIME the Gut's people are spared and given jobs." },
        { id: "gordo", label: "gordo: blow up the master clock in the missing hour", do: ["flag:plan_gordo", "flag:plan_chosen", "standing.bottom:+5", "standing.corp:-5"], consequence: "Act IV's m28 is DEMOLITION: charges on the Clock's power feeds (the Number Works substation, the Big Escalator) and a route up for the raid. Gordo is with you in everything. Lumps, if Dot is still in the Gut, goes to meet Pritchard alone. The LATE ending is the natural end of this road." },
        { id: "auntie", label: "auntie: get the last two pages and publish option c", do: ["flag:plan_auntie", "flag:plan_chosen", "standing.bottom:+3"], consequence: "Act IV's m28 is PRINT RUN: seize ☺ CORP News' broadcast relay and get the Price Press ready to print six pages on every tag in the city. Auntie goes up the hill with the raid herself. Gordo goes with his charges anyway; Lumps may go to Pritchard. The OFF THE BOOKS ending is the natural end of this road." },
      ] },
    ],
    scenes: ["c14_the_offer", "c15_the_split"],
    reward: { coupons: 0, flags: ["met_hask"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "every ending is still possible whatever the plan; the plan changes Act IV's missions, who stands where in the raid, and the endings' details.",
  },

  // ------------------------------------------------------------------ 25
  m25_tuesday_again: {
    act: 3, n: 25, title: "TUESDAY AGAIN", kind: "main", giver: null, district: "lates",
    locations: ["lates:waiting_room", "lates:tuesday_tower"],
    cast: ["overtime", "pauline"],
    requires: { missions: ["m24_the_split"], if: null },
    logline: "Overtime comes for you in the Lates, where every minute happens again, and every time it happens he remembers a little more.",
    mechanic: { uses: ["loops", "frost", "camera", "grapple"], hook: "the loop fight: take a photo of where his weak point was and walk back into it next loop" },
    beats: [
      "The Lates. Pauline warns you: 'he came through the door at 03:00. he's never come through the door before.'",
      "Boss fight: overtime_3 in the loop. His attacks are telegraphed from your last loop; he glitches more every loop.",
      "Loop four: he stops attacking. P16. 'i was going home at 17:30. why didn't i go home?'",
      "A conversation with him in the empty car park. What you say plants the talk-down in Act V.",
      "His time card is torn: Late Fees can't reach ★5 for a while.",
      "END OF ACT III.",
    ],
    reveals: {
      learn: ["Overtime is remembering: the door, 17:30, home.", "He has a wife. He was going home."],
      suspect: ["You can reach him."],
      withheld: ["June, the anniversary, the last phone call (his fragments, Act V)."],
    },
    steps: [
      { id: "warn", text: "", goal: { type: "talk", who: "pauline", talk: "door" }, marker: "lates:waiting_room" },
      { id: "boss", text: "survive mr. overtime (again, and again)", goal: { type: "killBoss", boss: "overtime_3" }, boss: "overtime_3" },
      { id: "p16", text: "", goal: { type: "flag", flag: "seen_p16" }, scene: "p16_tuesday_again" },
      { id: "talk", text: "", goal: { type: "talk", who: "overtime", talk: "home" }, do: ["flag:act3_done"] },
    ],
    talks: {
      door: {
        with: "pauline",
        nodes: {
          start: { say: ["he came through the door at 03:00. he's never come through the door before.", "he's in the car park. he's been in the car park since 09:00. he's been doing the same slam for six hours. it's very loud.", "i think he's waiting for you. i think it's the only appointment he's got left."] },
        },
      },
      home: {
        with: "overtime", cam: "closeup",
        nodes: {
          start: { say: ["*The looping car park, empty. Overtime standing still in the middle of it with his arms at his sides, steam coming off him in the rain. His punch-clock heart ticks unevenly. He's holding his time card. It's torn down the middle.*", "i was going home at 17:30.", "why didn't i go home?"], opts: [["because something happened at 17:30.", "happened"], ["you were in the lobby. you stopped me.", "lobby"], ["(cold) you're still on shift. get back to work.", "cold", { if: "drift>=3" }]] },
          happened: { say: ["something happened. yes. there was a... the clocks. the clocks cracked.", "*his visor flickers* and then i was at my desk. and it was 09:00. and everyone was absent. everyone's been absent for a very long time.", "where does everyone go?"], opts: [["they died. everyone died at 17:30. you did too.", "died"], ["home. they went home.", "homegentle"]] },
          lobby: { say: ["*He looks at you. Really looks.*", "cale. cale, r. you were running.", "i... punched your card.", "*the punch-clock skips three beats.* that's not... that's policy. that was policy."], do: ["flag:overtime_remembers_cale"], next: "happened" },
          died: { say: ["*A very long silence. The rain stops in mid-air, the Lates' loop catching on something.*", "no. no, i'd have been told. there'd be a memo.", "*he looks at his time card, the tear down the middle.*", "...there was a phone. at the door. somebody on the phone. she said..."], do: ["flag:told_overtime_he_died", "flag:overtime_reached"], next: "end" },
          homegentle: { say: ["home. yes. everyone went home. and i stayed. i always stay. june says i always stay.", "...june."], do: ["flag:overtime_said_june", "flag:overtime_reached"], next: "end" },
          cold: { say: ["*His posture straightens. The clock steadies. He's relieved.*", "yes. yes, of course. thank you. i'm on shift.", "*he walks away, perfectly on time.*"], do: ["flag:overtime_sent_back", "drift:+1"] },
          end: { say: ["*His punch-clock heart ticks back up to speed. He backs away from you, as if you're something hot.*", "i have to... i have an appointment.", "*He goes. He's late. For the first time, he's late.*"] },
        },
      },
    },
    choices: [],
    scenes: ["p16_tuesday_again"],
    reward: { coupons: 900, loot: ["lt_boss_overtime_3"], flags: ["beat_overtime_3", "overtime_card_torn"], standing: { corp: -5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. he's late.", meets: "MEETS EXPECTATIONS. you've seen this one.", see_me: "SEE ME. you were stapled to tuesday." },
  },
};
