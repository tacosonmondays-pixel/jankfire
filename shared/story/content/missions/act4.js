// OVERDUE main missions, Act IV: "Quarterly Review" (The Margins, Corp Hill). The act's question: who do you stand
// with? Same schema as missions/act1.js. m28 has three versions (parts), one per plan chosen in m24.

export const MISSIONS_ACT4 = {
  // ------------------------------------------------------------------ 26
  m26_exit_interview: {
    act: 4, n: 26, title: "EXIT INTERVIEW", kind: "main", giver: "old_pat", district: "margins",
    locations: ["margins:bus_stop", "margins:gnome_field", "margins:edge", "margins:forest", "margins:hr_cabin"],
    cast: ["old_pat", "janitor", "tall_guy"],
    requires: { missions: ["m25_tuesday_again"], if: null },
    logline: "At the edge of the world, the Tall Guy From HR can't be killed in his own forest. He just wants somebody to sign.",
    beats: [
      "The Last Bus Stop. The road ends in the void. Old Pat and the Margin Walkers stake gnomes to hold the ground. The Janitor mops the edge.",
      "Pat: Vacancy's Closing Agent keeps her page in a briefcase at the Show Home, and the Tall Guy walks the forest between here and there.",
      "The forest: he only moves when you don't look. You can't hurt him: his file says the forest is his place of work.",
      "The HR Cabin: filing cabinets to the ceiling. His file: Gerald Long, HR Business Partner, 31, volunteered for the void survey team on the Final Quarter. On loan to Vacancy. Never returned.",
      "In the file, an EXIT INTERVIEW form, unsigned. He's needed someone to sign him out for sixty-one years.",
      "Choice: sign it (he's released; a talk-down) or use the file to make him killable and fight him.",
      "C17: either way, at the edge, he gives you the SALE AGREEMENT: ☺ CORP has sold the Bottom to Vacancy, on completion of the Re-Merger.",
    ],
    reveals: {
      learn: ["☺ CORP has already sold the Bottom, all plots and all occupants, to Vacancy Holdings. Completion: on Re-Merger.", "The living who can't pay aren't staff, so they're land. The void comes up the hill."],
      suspect: ["Vacancy's page of Option C is the Bottom's title deed."],
      withheld: [],
    },
    steps: [
      { id: "pat", text: "find the margin walkers", goal: { type: "talk", who: "old_pat", talk: "gnomes" }, marker: "margins:gnome_field" },
      { id: "forest", text: "cross the forest", goal: { type: "reach", zone: "margins:forest" }, notes: "the Tall Guy stalks you; he can't be damaged; when he reaches you, you're 'interviewed' and wake at the gnome field" },
      { id: "cabin", text: "find his file in the hr cabin", goal: { type: "pickup", item: "tall_guy_file" }, marker: "margins:hr_cabin" },
      { id: "exit", text: "his exit interview", goal: { type: "flag", flag: "tall_guy_resolved" }, talk: "interview" },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "tall_guy" }, boss: "tall_guy", if: "flag:fought_tall_guy" },
      { id: "c17", text: "", goal: { type: "flag", flag: "seen_c17" }, scene: "c17_negative_space", do: ["give:sale_agreement"] },
    ],
    talks: {
      gnomes: {
        with: "old_pat", cam: "closeup",
        nodes: {
          start: { say: ["*The Gnome Field: hundreds of garden gnomes in rows on the last of the ground, facing the void like they're on guard. A tiny old woman in wellies hammers another one in.*", "that's ken. he's holding the bus stop. good lad, ken.", "the void can't take what's occupied. vacancy's lawyers haven't found a way round it. so we occupy.", "*she turns a gnome over: a name is painted under its feet. MARGARET ELLIS.* four hundred and twelve. one for everyone who's gone in."], opts: [["i'm looking for vacancy's page.", "page"], ["*help her plant one*", "plant"]] },
          plant: { say: ["*You hammer one in. She paints a name under it without asking you.* there. that's the hendersons. they went in this morning.", "you're a good lad. lass. lump. whatever you are. you're good."], do: ["standing.bottom:+2"], next: "page" },
          page: { say: ["the closing agent keeps her papers in a briefcase at the show home. she never puts it down. she sleeps with it.", "between here and there's the forest. and in the forest's him. hr. you can't shoot him. people've tried. he just... asks for a quick word.", "the janitor says he's lonely. the janitor says goodnight to him. nobody else does."] },
        },
      },
      interview: {
        with: "tall_guy", cam: "lowAngle",
        nodes: {
          start: { say: ["*The HR Cabin. You've got his file open on a desk. GERALD LONG. HR BUSINESS PARTNER. AGE 31. PHOTO: a nervous young man with big ears and a kind face. STATUS: ON LOAN (VACANCY HOLDINGS · VOID SURVEY). RETURNED: —.*", "*The cabin door opens and he folds himself in, joint by joint, until his head is level with yours.*", "you found my file. nobody reads the files.", "i volunteered. they said it was a two-week secondment. the void stretched me a bit. a lot. and nobody ever came to collect me.", "you can't leave a job until someone signs you out. that's policy. i've been asking everyone. they run."], opts: [["*sign the exit interview*", "sign"], ["(read the file) your place of work is the forest. if i strike that out, you can be hurt.", "fight"], ["why didn't you just leave?", "leave"]] },
          leave: { say: ["*He looks genuinely confused.*", "without signing out? that's... that's absence. i'd be absent.", "i'm HR. i can't be absent. who would i report myself to?"], next: "start2" },
          start2: { say: ["*He holds out a pen, very gently, with a hand at the end of a very long arm.*"], opts: [["*sign the exit interview*", "sign"], ["(cross out his place of work) fight him", "fight"]] },
          sign: { say: ["*You sign. Reason for leaving: you write whatever you like. (The game keeps it.)*", "*He reads it. He reads it again. His shoulders come down about a metre.*", "thank you. thank you. that's... a very good exit interview. i'd give it a five.", "i'll walk you to the edge. there's something you should see before i go. it's in my outbox. it's been in my outbox for a while."], do: ["flag:signed_tall_guy", "flag:tall_guy_resolved", "standing.bottom:+3", "drift:-1"] },
          fight: { say: ["*You strike out PLACE OF WORK: THE FOREST. The cabin goes cold.*", "oh.", "oh, that's... that's a disciplinary.", "*his arms start to get longer.*"], do: ["flag:fought_tall_guy", "flag:tall_guy_resolved"] },
        },
      },
    },
    choices: [],
    scenes: ["c17_negative_space"],
    reward: { coupons: 600, items: ["sale_agreement"], loot: ["lt_boss_tall_guy"], flags: ["act4_started"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you signed someone out. HR thanks you.", meets: "MEETS EXPECTATIONS. you had a quick word.", see_me: "SEE ME. you looked away." },
  },

  // ------------------------------------------------------------------ 27
  m27_negative_space: {
    act: 4, n: 27, title: "NEGATIVE SPACE", kind: "main", giver: "old_pat", district: "margins",
    locations: ["margins:show_home", "margins:edge", "bottom:landlord_pile", "bottom:lostfound"],
    cast: ["penny_plot", "old_pat", "tall_guy", "mr_deposit", "auntie"],
    requires: { missions: ["m26_exit_interview"], if: null },
    logline: "The deal closes today. Vacancy's Closing Agent is selling the Bottom to the void, and her page of Option C is the deed.",
    beats: [
      "The Show Home: a perfect show house on the edge, every plot sold marked by a pin on a map of the void. The Bottom is a cluster of red pins with 'PHASE TWO' written over it.",
      "Penny Plot: cheerful, monstrous, in a pink blazer over a hazmat suit. She tries to sell you a plot. She sold her own house at nineteen.",
      "Boss fight: PENNY PLOT, from the Show Home out onto the Edge, as she drops void bombs shaped like keyrings and the ground under you is sold off in chunks.",
      "Her briefcase: Vacancy's page. 'non-productive land clearance.' The Bottom listed as phase two.",
      "P6b: DEAL (Vacancy keeps the Margins, cancels the Bottom's sale, stops selling ground) or TAKEOVER (the Margin Walkers hold the edge).",
      "Back at the Lost & Found: five pages on the wall. Auntie: 'one left. it's on her desk.'",
    ],
    reveals: {
      learn: ["Vacancy page: void bombs for 'non-productive' districts that can't pay. The Bottom was always phase two.", "Option C planned for the living poor to be deleted, not just the dead to work."],
      suspect: ["The last page, on Hask's desk, ties it all together."],
      withheld: ["Page 6 (Act V)."],
    },
    steps: [
      { id: "show", text: "find the closing agent at the show home", goal: { type: "talk", who: "penny_plot", talk: "viewing" }, marker: "margins:show_home" },
      { id: "boss", text: "stop the sale", goal: { type: "killBoss", boss: "penny_plot" }, boss: "penny_plot" },
      { id: "page", text: "take vacancy's page from the briefcase", goal: { type: "pickup", item: "page_vacancy" }, do: ["flag:pages_vacancy", "flag:read_page_vacancy"] },
      { id: "choice", text: "decide who runs the margins", goal: { type: "flag", flag: "margins_decided" }, scene: "p6b_deal_or_takeover" },
      { id: "home", text: "take the page to auntie", goal: { type: "deliver", item: "page_vacancy", zone: "bottom:lostfound" }, talk: "five" },
    ],
    talks: {
      viewing: {
        with: "penny_plot", cam: "closeup",
        nodes: {
          start: { say: ["*The Show Home: scatter cushions, a bowl of plastic lemons, a kettle that's never been plugged in. On the wall, a huge map of the void with thousands of pins. Penny Plot in a pink blazer over a white hazmat suit, visor up, smile on.*", "hello! you must be here for the viewing. come in, come in. mind the floor. there isn't one past the rug.", "open plan! lots of light! well. no light. lots of plan."], opts: [["what's phase two?", "phase"], ["i'm here for your page.", "page"]] },
          phase: { say: ["*She taps the cluster of red pins.* the bottom! lots of potential. characterful. very... occupied. but on completion, all plots and all occupants transfer to vacancy, and vacancy transfers them to the void. location, location, nothing.", "it's not personal. it's a buyer's market. the buyer is the void."], next: "page" },
          page: { say: ["*The briefcase is handcuffed to her wrist. She pats it.*", "oh, the deed. you can't have the deed. the deed's the whole sale.", "i sold my own house at nineteen. right over there. it's void now. that's how you know i'm good.", "the deal closes today. so do you."], do: ["flag:penny_fight"] },
        },
      },
      five: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*The Lost & Found. Auntie pins the fifth page. Five frames full. One empty, under the ☺.*", "non-productive land clearance.", "the bottom was always phase two. before any of us were born. before the bottom existed. they planned for wherever the poor would end up, and they planned to delete it.", "*she puts the crayon down. She looks at the empty frame for a long time.*", "one left. it's on her desk.", "*quietly, to the wall* i've always known where it was. i just never had the stairs in me."] },
        },
      },
    },
    choices: [
      { id: "district_choice", prompt: "Penny Plot is clinging to a SOLD sign over the void. Old Pat has a wheelbarrow of gnomes. Who runs the Margins?", options: [
        { id: "deal", label: "DEAL: Vacancy keeps the Margins, and cancels the Bottom's sale", do: ["turf:margins=vacancy", "flag:margins_deal", "flag:margins_decided", "standing.corp:+3"], consequence: "Penny signs a cancellation with a pen shaped like a key and a smile you don't trust. Vacancy stops selling ground at the Margins and sends survey teams to the raid. The Bottom's sale is cancelled on paper, which means that if ☺ CORP wins, ☺ CORP just signs a new one." },
        { id: "takeover", label: "TAKEOVER: the Margin Walkers hold the edge", do: ["turf:margins=marginwalkers", "flag:margins_takeover", "flag:margins_decided", "standing.bottom:+5", "standing.corp:-5"], consequence: "Pat plants a gnome on the Show Home's doorstep: PENNY'S MUM. The Margin Walkers occupy every plot Vacancy hadn't sold yet; the void stops coming. Vacancy is hostile everywhere; Penny comes back as a raider estate agent on the Commute. The Bottom's sale still exists on ☺ CORP's side until the Clock is dealt with." },
      ] },
    ],
    scenes: ["p6b_deal_or_takeover"],
    reward: { coupons: 900, items: ["page_vacancy"], loot: ["lt_boss_penny_plot"], flags: ["beat_penny_plot"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. the deal didn't close.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you bought a plot." },
  },

  // ------------------------------------------------------------------ 28 (three versions)
  m28_the_plan: {
    act: 4, n: 28, title: "THE PLAN", kind: "main", giver: null, district: "corphill",
    locations: ["bottom:lostfound", "numberworks:press", "checkout:escalator", "corphill:fountain", "gut:digester_wall", "corphill:bleach_line"],
    cast: ["lumps", "gordo", "auntie", "pritchard", "chad_tempo", "dot"],
    requires: { missions: ["m27_negative_space"], if: null },
    logline: "Whatever you chose at the split, now it has to be built: a headcount, a demolition, or a print run. And whoever you didn't choose does something anyway.",
    beats: [
      "One of three versions plays, by plan (parts below). Each ends with the Bottom ready for 03:00.",
      "Whoever's plan you didn't follow acts on their own: Gordo takes his charges up the hill anyway; Lumps, if his mum is still in the Gut, goes to meet Pritchard.",
      "Pritchard, if he's been treated kindly, leaks the elevator override (1730) and the Twins' rotation.",
    ],
    reveals: {
      learn: ["The elevator override is 1730. Of course it is.", "(HEADCOUNT) The Restoration staffing table has the Bottom's dead on it, and none of its living.", "(DEMOLITION) The Master Clock runs on the Number Works substation and the Big Escalator's motor.", "(PRINT RUN) ☺ CORP News reaches every screen in the city from one relay under the Smiling Fountain."],
      suspect: ["Lumps might really take the deal."],
      withheld: ["Page 6 and the 17:10 call (Act V)."],
    },
    parts: [
      { id: "headcount", title: "HEADCOUNT (Lumps' plan)", if: "flag:plan_lumps", do: ["flag:headcount_done", "flag:plan_built"],
        steps: [
          { id: "onboard", text: "attend hask's onboarding interview at the bleach line", goal: { type: "talk", who: "pritchard", talk: "onboarding" }, marker: "corphill:bleach_line" },
          { id: "table", text: "get the bottom's people onto the staffing table", goal: { type: "interact", target: "corphill:bleach_line" }, notes: "a stealth hack in the onboarding office: type names in while Pritchard keeps the guards talking" },
          { id: "dot", text: "get dot out of the deep wall with the new paperwork", goal: { type: "escort", who: "dot", zone: "bottom:long_stairs" }, if: "fate.dot=gut", do: ["fate:dot=freed"] },
        ] },
      { id: "demolition", title: "DEMOLITION (Gordo's plan)", if: "flag:plan_gordo", do: ["flag:demolition_done", "flag:plan_built"],
        steps: [
          { id: "sub", text: "plant charges at the number works substation", goal: { type: "interact", target: "numberworks:press" }, marker: "numberworks:press" },
          { id: "esc", text: "plant charges on the big escalator's motor", goal: { type: "interact", target: "checkout:escalator" }, marker: "checkout:escalator", notes: "a climb up the 2 km escalator against its direction, with Overtime's lanyard on the employee gates" },
          { id: "det", text: "", goal: { type: "talk", who: "gordo", talk: "detonator" } },
        ] },
      { id: "print_run", title: "PRINT RUN (Auntie's plan)", if: "flag:plan_auntie", do: ["flag:print_ready", "flag:plan_built"],
        steps: [
          { id: "relay", text: "seize the ☺ corp news relay under the smiling fountain", goal: { type: "interact", target: "corphill:fountain" }, marker: "corphill:fountain", talk: "chad" },
          { id: "press", text: "get the price press ready to print six pages", goal: { type: "interact", target: "numberworks:press" }, marker: "numberworks:press" },
          { id: "auntie", text: "", goal: { type: "talk", who: "auntie", talk: "print" } },
        ] },
    ],
    steps: [
      { id: "plan", text: "do the plan", goal: { type: "flag", flag: "plan_built" }, notes: "runs the part whose `if` matches; the part's `do` sets its flag, then plan_built" },
      { id: "others", text: "", goal: { type: "flag", flag: "others_resolved" }, notes: "the gordo_alone and lumps_alone choices, if they apply" },
      { id: "leak", text: "", goal: { type: "talk", who: "pritchard", talk: "leak" }, if: "flag:pritchard_soft" },
      { id: "ready", text: "get some sleep. it's 03:00 tomorrow.", goal: { type: "reach", zone: "bottom:lostfound" }, talk: "night_before" },
    ],
    talks: {
      onboarding: {
        with: "pritchard", cam: "closeup",
        nodes: {
          start: { say: ["*A white onboarding office on the Bleach Line. Pritchard, in person for the first time: thin, three watches, a blazer too big for him. He stands up when you come in and knocks his chair over.*", "hi. hi. sorry. you're... you're early. that's good. that's very good. she'll like that.", "*He lowers his voice to nothing.* lumps told me. in his letter. what you're really doing. i burned the letter. then i felt bad and taped it back together. then i burned it again."], opts: [["will you help us?", "help"], ["why would you risk it?", "why"]] },
          why: { say: ["because he asks how i am.", "*he says it in one breath, like he's been holding it for years* and because i typed eleven thousand four hundred and two names that aren't on the table, and i can't stop seeing them when i close my eyes, and i've never had a minute to myself to think about it until right now."], next: "help" },
          help: { say: ["the table's on that terminal. i'll keep the guards on a 'compliance briefing'. i'll make it very long. i'm good at long.", "type fast. and... if you get his mum out. tell him i said hello."], do: ["flag:pritchard_ally"] },
        },
      },
      detonator: {
        with: "gordo", cam: "closeup",
        nodes: {
          start: { say: ["*Gordo on the roof of the Lost & Found, at night, holding a detonator made from a ☺ CORP pager. The Spire is lit up on the hill.*", "two charges. substation and escalator. at 03:15 the clock loses power for nine minutes. enough to break its teeth.", "*he turns the detonator over in his hands.* you know what i keep thinking? who sweeps up after. that's never been in my plans. who sweeps up."], opts: [["the bottom. together.", "together"], ["you don't have to know yet.", "know"]] },
          together: { say: ["*He snorts, which is as close as Gordo gets to crying.*", "the bottom couldn't sweep a porch together. ...we'll learn. we'll have to."], do: ["standing.bottom:+2"] },
          know: { say: ["i'm a planner. i always have to know.", "...ok. tomorrow i'll not know. one day. as a treat."] },
        },
      },
      chad: {
        with: "chad_tempo", cam: "overShoulder",
        nodes: {
          start: { say: ["*Under the Smiling Fountain: a broadcast relay, and at the desk, a mannequin news anchor with perfect hair reading the Schedule to an empty studio.*", "it's 21:14 on corp hill, and everybody's on time.", "*You unplug his autocue and plug Auntie's tape in. He reads the first line of it perfectly, without understanding a word.*", "option c. strategic write-off. confidential. board eyes only.", "*he smiles* in other news, traffic is fine."], do: ["flag:relay_seized"] },
        },
      },
      print: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*The Price Press at night. Auntie stands at the feed tray with the five pages in a folder, running her finger along the press like she's auditing it.*", "five pages. six when we get hers. on every price tag in the city by 06:00, and on every screen by 06:01.", "they'll say it's forged. they always say it's forged. so we print the signatures big."], opts: [["you're coming up the hill?", "coming"]] },
          coming: { say: ["i'm coming up the hill.", "*she says it the way other people say 'i'm going to die', and she knows you heard it that way.*", "i've been not going up that hill for sixty-one years, rory. i'm eighty-five. i'm out of excuses and i'm out of crayons."], do: ["flag:auntie_coming"] },
        },
      },
      leak: {
        with: "pritchard",
        nodes: {
          start: { say: [["pager", "*BEEP. A text message on the pager, typed very fast.*"], "the lift override is 1730. of course it's 1730. the twins rotate at 03:20. ms hask has a 03:41 with you. please be on time. please. i booked you lunch after. real lunch. sorry. P."], do: ["flag:have_override"] },
        },
      },
      night_before: {
        with: "auntie", cam: "wide",
        nodes: {
          start: { say: ["*The Lost & Found, the night before. Everyone who's coming up the hill is asleep on the floor in coats. Lumps snores like a tuba. Gordo is asleep sitting up with a map on his face. If she's free, Mina is asleep against your shoulder.*", "*Auntie is awake at the long table, writing.*", "can't sleep either? good. sit with me.", "i used to do this the night before audits. write down everything i knew. in case."], opts: [["what are you writing?", "writing"], ["*sit with her in silence*", "silence"]] },
          writing: { say: ["*She turns the notebook round. It's names. Everyone in the Bottom, everyone you've met, in crayon, with a line each.* 'lumps: eats four bowls.' 'gordo: right, mostly.' 'dale: sorry.' 'mina: waiting.' 'rory: late. came anyway.'", "in case.", "*she closes it.* go to sleep. it's 03:00 tomorrow."] },
          silence: { say: ["*You sit. The Machine hums. Your heart ticks. After a while she puts a hand over yours on the table, and leaves it there, and keeps writing with the other one.*"], do: ["standing.bottom:+1"] },
        },
      },
    },
    choices: [
      { id: "gordo_alone", prompt: "(if it wasn't his plan) Gordo is going up the hill alone tonight with his charges.", if: "!flag:plan_gordo", options: [
        { id: "stop", label: "stop him", do: ["flag:stopped_gordo", "flag:others_resolved"], consequence: "You find him on the Big Escalator with the charges and take the detonator. He lets you, which is worse than if he hadn't. He comes on the raid; he won't look at you until the Clock. In ON TIME he never speaks to you again before they take him." },
        { id: "let", label: "let him go", do: ["flag:let_gordo_go", "flag:others_resolved"], consequence: "His charges go off at 03:15 during the raid: the Clock loses power for nine minutes whatever plan you followed (the Fully Billable fight starts in the dark), and Corp's reserves are cut off at the escalator. He's hurt in the blast and is carried into the lobby." },
      ] },
      { id: "lumps_alone", prompt: "(if it wasn't his plan and Dot is still in the Gut) Lumps is going to meet Pritchard and take Hask's deal for his mum.", if: "!flag:plan_lumps fate.dot=gut", options: [
        { id: "stop", label: "go with him and make it a rescue instead", do: ["fate:dot=freed", "flag:lumps_rescue", "flag:others_resolved"], consequence: "You go into the deep wall with him that night instead. Dot comes out. Lumps carries her down the Long Stairs and comes on the raid." },
        { id: "let", label: "let him take the deal", do: ["flag:lumps_took_deal", "flag:others_resolved", "fate:dot=freed"], consequence: "Lumps signs. Dot is released into ☺ CORP's care, and Lumps is on the staffing table. In the raid he stands with you until the lobby, then he has to choose; his line at the elevator changes ('i signed. i'm still coming up.'). In LATE he never forgives himself; in ON TIME he's your first hire." },
      ] },
    ],
    scenes: [],
    reward: { coupons: 500, flags: ["plan_built"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. the plan survived contact.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you set off the charges in the lost & found." },
  },

  // ------------------------------------------------------------------ 29
  m29_the_missing_hour: {
    act: 4, n: 29, title: "03:00", kind: "main", giver: "gordo", district: "corphill",
    locations: ["corphill:bleach_line", "corphill:dividend_road", "corphill:fountain", "corphill:cathedral", "corphill:spire_lobby"],
    cast: ["auntie", "lumps", "gordo", "steering_committee", "mina", "pip", "wristband", "nell", "old_pat"],
    requires: { missions: ["m28_the_plan"], if: null },
    logline: "At 03:00, in the one hour nobody is booked into, the whole Bottom climbs Corp Hill with every ally you earned.",
    beats: [
      "C18: the Bleach Line at 02:59, the allies, the clocks turning to face Dividend Road.",
      "The climb: a big set piece up Dividend Road. Allies fight at junctions (each district's ruler holds one).",
      "Shaky company allies (from DEALs) turn if your Corp Standing is low: they'd rather be on ☺ CORP's side if they don't trust you to win. A goon, a segway, a forklift tank switches sides mid-fight.",
      "Boss fight: THE MEETING ROOM, a flying conference room gunship over the Cathedral of Shareholder Value, flown by the Steering Committee.",
      "The Spire's doors. Into the lobby.",
    ],
    reveals: {
      learn: ["Everyone you helped shows up. Everyone you didn't, doesn't."],
      suspect: [],
      withheld: [],
    },
    steps: [
      { id: "c18", text: "", goal: { type: "flag", flag: "seen_c18" }, scene: "c18_0300" },
      { id: "climb", text: "get up dividend road before 04:00", goal: { type: "reach", zone: "corphill:cathedral" }, timer: 900, notes: "the timer is the Missing Hour: at 04:00 the Schedule sees you and every reserve on the hill arrives; it doesn't fail the mission, it makes it much harder" },
      { id: "turn", text: "", goal: { type: "flag", flag: "allies_checked" }, notes: "engine: each DEAL ally checks standing.corp<-20 and may turn (a short Moment: the ally's leader on the radio, then they switch sides)", talk: "turncoat" },
      { id: "boss", text: "bring down the meeting room", goal: { type: "killBoss", boss: "meeting_room" }, boss: "meeting_room", marker: "corphill:cathedral" },
      { id: "doors", text: "get into the spire", goal: { type: "reach", zone: "corphill:spire_lobby" } },
    ],
    talks: {
      turncoat: {
        with: "pa",
        nodes: {
          start: { branch: [["flag:pinstripe_deal standing.corp<-20", "family"], ["flag:checkout_deal standing.corp<-20", "bigvalue"], ["flag:numberworks_deal standing.corp<-20", "remainder"], [null, "loyal"]] },
          family: { say: [["radio", "*Nonna, on a limo radio* merchandise. i priced it. you lose. the family is sorry. the family is never sorry. *the limos turn their guns*"]], do: ["flag:family_turned"] },
          bigvalue: { say: [["pa", "*Gail, on the loudhailer, crying* i'm sorry. head office rang. we're sorry for any inconvenience. *the segways turn*"]], do: ["flag:bigvalue_turned"] },
          remainder: { say: [["radio", "*Mr. Sevens, on a forklift tank radio* nothing personal. the odds moved. touch wood. *the forklifts turn*"]], do: ["flag:remainder_turned"] },
          loyal: { say: [["radio", "*static, then Pip, or Nell, or Wristband, or whoever's leading the nearest ally* we're still here, darling. we're still here."]] },
        },
      },
    },
    choices: [],
    scenes: ["c18_0300"],
    reward: { coupons: 1000, loot: ["lt_boss_meeting_room"], flags: ["beat_meeting_room"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. that meeting could have been an email.", meets: "MEETS EXPECTATIONS. you're in.", see_me: "SEE ME. it's 04:00." },
  },

  // ------------------------------------------------------------------ 30
  m30_the_lobby: {
    act: 4, n: 30, title: "THE LOBBY", kind: "main", giver: null, district: "corphill",
    locations: ["corphill:spire_lobby", "corphill:spire_top"],
    cast: ["twins", "auntie", "lumps", "gordo", "hask", "pritchard"],
    requires: { missions: ["m29_the_missing_hour"], if: null },
    logline: "The same lobby as 17:29. The Twins hold the elevator. Auntie sits down behind the reception desk.",
    beats: [
      "The lobby: the marble, the revolving door, the pillar Overtime stepped out from. The game plays the lobby's music from F4.",
      "Boss fight: THE TWINS, holding the elevator.",
      "C19: Auntie stays to hold the lobby. Her last line depends on the forgiveness choice. The elevator doesn't stop at 41.",
      "C20: the top floor. Hask explains why you're free: fired nineteen seconds before the end of the world. The lanyard on the desk. The last page, under it.",
      "The Master Clock opens behind the glass.",
    ],
    reveals: {
      learn: ["Why you're free, from Hask herself.", "The Restoration would use your recording as the template for all the dead.", "Auntie Spreadsheet doesn't come back."],
      suspect: ["The last page has the 17:30 backup clause."],
      withheld: ["The 17:10 call (Act V)."],
    },
    steps: [
      { id: "boss", text: "get to the elevator", goal: { type: "killBoss", boss: "twins" }, boss: "twins", marker: "corphill:spire_lobby" },
      { id: "c19", text: "", goal: { type: "flag", flag: "seen_c19" }, scene: "c19_the_lobby", do: ["fate:auntie=dead"] },
      { id: "lift", text: "go up", goal: { type: "reach", zone: "corphill:spire_top" }, talk: "lift" },
      { id: "c20", text: "", goal: { type: "flag", flag: "seen_c20" }, scene: "c20_final_offer", do: ["flag:act4_done"] },
    ],
    talks: {
      lift: {
        with: "lumps", cam: "closeup",
        nodes: {
          start: { say: ["*The elevator. Mirrored walls. Ninety floors. The floor counter climbs past 41 and doesn't stop.*", "*Lumps has his face to the wall. His shoulders are shaking. He's counting floors under his breath and losing count.*"], opts: [["*put a hand on his back*", "hand"], ["she chose it, lumps.", "chose"], ["(if Lumps took Hask's deal) are you still with me?", "deal", { if: "flag:lumps_took_deal" }]] },
          hand: { say: ["*He doesn't turn round. After a few floors he says, very quietly:* she didn't eat. this morning. she gave me hers.", "...i'm going to be so angry later. i'm not angry yet. i'm counting."] },
          chose: { say: ["i know she chose it. she chose it sixty years ago. she just took a long time to get there.", "*the counter: 88. 89. 90.*"] },
          deal: { say: ["*He wipes his face with a forearm the size of a door.*", "i signed. i'm still coming up. i don't know what that makes me. ask me at the top."] },
        },
      },
    },
    choices: [],
    scenes: ["c19_the_lobby", "c20_final_offer"],
    reward: { coupons: 0, loot: ["lt_boss_twins"], flags: ["beat_twins"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "no grade card after the lobby. END OF ACT IV plays over the Master Clock opening.",
  },
};
