// OVERDUE side questlines: THE COMMUTE. Schema: see side/bottom.js. The real lore NPCs from the sims live out here.

export const SIDE_COMMUTE = {
  sq_commute_the_region: {
    kind: "side", from: 1, title: "THE REGION", giver: "gary", district: "commute",
    locations: ["commute:gary_crater", "corphill:spire_lobby"], cast: ["gary"],
    requires: { missions: ["m02_sauce_run"], if: null },
    logline: "Gary, ninety-eight, still runs his site office on the lip of a crater. He's filed a quarterly report every quarter for sixty-one years. Deliver them.",
    twist: "244 reports. Every one lists, under ATTENDANCE, the same forty-one names, all marked PRESENT. They're his warehouse floor team. They were on the floor at 17:30; he was in the office, eating lunch late. The region is the crater. He's been taking the register for sixty-one years. When you deliver the reports to the Spire's inbox (a chute in the lobby), the clerk-bot stamps them RECEIVED, and Gary, told, says: 'oh. good. good. it's fine.' and, for once, it is.",
    beats: ["The portacabin, the mug, the walking frame. The sim Gary's voice, older.", "Carry 244 reports (a crate, heavy, on the Commute: raiders want the paper for armour).", "The Spire's inbox chute.", "Back to Gary."],
    steps: [
      { id: "meet", text: "visit the site office", goal: { type: "talk", who: "gary", talk: "region" }, marker: "commute:gary_crater" },
      { id: "deliver", text: "deliver 244 quarterly reports to the spire's inbox", goal: { type: "deliver", item: "gary_reports", zone: "corphill:spire_lobby" } },
      { id: "back", text: "tell gary", goal: { type: "talk", who: "gary", talk: "received" } },
    ],
    talks: {
      region: { with: "gary", cam: "closeup", nodes: {
        start: { say: ["oh. a visitor. nobody comes to the site office. that's why i picked it. sixty-one years ago.", "i'm gary. regional manager. the region's that hole.", "*he points out of the window at the crater. He says it the way you'd point at a car park.*"], opts: [["what happened to the region?", "what"], ["what are all these folders?", "folders"]] },
        what: { say: ["it's fine. i've been fine for eighty years.", "*long pause* i was eating lunch late. in here. the floor was on the floor."], next: "folders" },
        folders: { say: ["quarterly reports. every quarter. two hundred and forty-four of them. nobody's ever come to collect.", "attendance: present. all of them. i don't care what the crater says.", "would you take them up the hill? the inbox is in the spire lobby. i'd go myself. *he looks at the walking frame* the frame's on a deadline."], do: ["give:gary_reports"] },
      } },
      received: { with: "gary", nodes: { start: { say: ["received? they stamped it? 'received'?", "oh. good. good.", "*he looks out at the crater for a while*", "it's fine.", "*and, for once, it is.*"], do: ["flag:gary_reports_received"] } } },
    },
    choices: [],
    reward: { coupons: 500, standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. all present.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you used them as armour." },
  },

  sq_commute_smiles: {
    kind: "side", from: 2, title: "SMILES", giver: "smiles", district: "commute",
    locations: ["commute:smiles_hideout", "commute:carnival", "commute:spiral_freeway"], cast: ["smiles", "morale_officer"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "Under a collapsed overpass, a man in the old Mr. Smiles suit is hiding from the Fun Department. He wants to do one fun thing that isn't a job.",
    twist: "He was in the suit at a Big Value shelter event at 17:30. The suit saved him from the flash; the face under it didn't make it. He can't take the head off. The fun thing is a kite. He's never flown one; the Fun Department always said kites weren't 'scalable'. You get him to the top of the Spiral Freeway in a paper storm, which is perfect kite weather, and he flies it for a whole minute before the Morale Officer's convoy finds him. (If you've beaten her, it never comes, and he flies it until dark.)",
    beats: ["The hideout: a big round shadow, a little gas stove, mascot gloves drying on a line.", "He tells you about mandatory fun, and a little about 17:30.", "Build a kite (scavenge: a ☺ CORP banner, an umbrella, Gordo's string).", "The Spiral Freeway in a paper storm. The kite.", "The Fun Department arrives (or doesn't)."],
    steps: [
      { id: "meet", text: "find the shadow under the overpass", goal: { type: "talk", who: "smiles", talk: "hiding" }, marker: "commute:smiles_hideout" },
      { id: "kite", text: "build a kite", goal: { type: "pickup", item: "smiles_kite" } },
      { id: "fly", text: "take mr. smiles to the top of the spiral freeway in a paper storm", goal: { type: "escort", who: "smiles", zone: "commute:spiral_freeway" } },
    ],
    talks: {
      hiding: { with: "smiles", cam: "closeup", nodes: {
        start: { say: ["oh! a fan! nobody comes under here. that's the point of under here.", "i used to be the mascot. mr. smiles. now i'm a guy in a hot suit under a bridge. hiding from my old department."], opts: [["why are they after you?", "why"], ["take the head off.", "head"]] },
        why: { say: ["they want me back. delphine wants me back. she wants a witness.", "i was in the suit at a big value on the high street at half five. the shelter event. she wrote the ad. 'every big value is a shelter.' i was handing out balloons."], next: "fun" },
        head: { say: ["no.", "i can't take it off. i don't know what's under there. neither of us want to find out.", "*the big painted smile looks at you. Inside it, a long breath.*"], next: "fun" },
        fun: { say: ["if fun is mandatory it's a job. i did the maths. the maths broke me. then the world did.", "i'd like to do one fun thing that isn't a job. a kite. i've never flown a kite. they said kites weren't scalable."] },
      } },
    },
    choices: [],
    reward: { coupons: 400, flags: ["smiles_flew_kite"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. it flew.", meets: "MEETS EXPECTATIONS. it flew a bit.", see_me: "SEE ME. you flew it into a digit." },
  },

  sq_commute_first_intern: {
    kind: "side", from: 2, title: "THE FIRST INTERN", giver: "todd", district: "commute",
    locations: ["commute:todd_shrine", "commute:unpaid_camp", "commute:missing_texture"], cast: ["todd", "eotm", "missing_texture"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "Todd, about a hundred and twenty, sits in a lawn chair on a bus roof while the Unpaid worship him. Get him off the roof for one day.",
    twist: "Todd wrote the world's physics on his first day, from memory, and never finished it. There's a bit of the Commute that's just purple and black squares. It's been growing. In part 2 Todd takes you there to finish it, and it fights back. In part 3, if you've fought Employee of the Month, Todd finds out the warlord's intern badge says TODD: Craig is his grandson.",
    beats: ["The shrine: offerings of staplers and mugs; the Unpaid chanting 'the grind never stops'.", "Todd asks you, in a whisper, to get him down. A stealth extraction (or a fight, or an internship: with the Unpaid lanyard you can just walk him down as 'his assistant').", "Part 2: the Unfinished Bit. Secret boss: THE MISSING TEXTURE.", "Part 3: the badge."],
    steps: [
      { id: "meet", text: "climb the shrine", goal: { type: "talk", who: "todd", talk: "prophet" }, marker: "commute:todd_shrine" },
      { id: "down", text: "get todd off the bus roof", goal: { type: "escort", who: "todd", zone: "commute:ring_road" }, do: ["flag:todd_off_the_roof"] },
    ],
    parts: [
      { id: "unfinished", title: "THE UNFINISHED BIT", if: "flag:todd_off_the_roof", do: ["flag:texture_patched"],
        steps: [
          { id: "go", text: "take todd to the unfinished bit", goal: { type: "reach", zone: "commute:missing_texture" } },
          { id: "boss", text: "", goal: { type: "killBoss", boss: "missing_texture" }, boss: "missing_texture" },
        ] },
      { id: "grandson", title: "THE BADGE", if: "flag:texture_patched done:sq_commute_eotm", do: ["flag:todd_met_grandson"],
        steps: [ { id: "badge", text: "show todd employee of the month's badge", goal: { type: "talk", who: "todd", talk: "badge" } } ] },
    ],
    talks: {
      prophet: { with: "todd", cam: "closeup", nodes: { start: { say: ["oh hey! sorry, i'm on a deadline. the deadline was before the end of the world.", "please stop praying at me. *to the raiders below* PLEASE STOP PRAYING AT ME.", ["raider", "*chanting* the first intern speaks. the grind never stops."], "they feed me regrowth with a spoon. it tastes like pennies and guilt.", "*whispering* get me down. one day. i want to finish something. i never finish anything."] } } },
      badge: { with: "todd", cam: "closeup", nodes: { start: { say: ["*You hand Todd the badge you took off Employee of the Month: an old ☺ CORP intern badge, cracked. It says TODD.*", "that's... that's mine. that's my old one. i lost it in... i gave it to my son. when he was little. so he'd have something from my work.", "where did you...", "*he looks across the Commute at the war-rig, at the huge man in the plaques.*", "...oh.", "*he sits down on the bus roof. After a while, Craig climbs up and sits next to him. Neither of them knows what to say. They sit.*"] } } },
    },
    choices: [],
    reward: { coupons: 600, standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. finished.", meets: "MEETS EXPECTATIONS. mostly finished.", see_me: "SEE ME. // TODO" },
  },

  sq_commute_eotm: {
    kind: "side", from: 2, title: "PERFORMANCE REVIEW", giver: "eotm", district: "commute",
    locations: ["commute:unpaid_camp", "commute:ring_road"], cast: ["eotm", "todd"],
    requires: { missions: ["m02_sauce_run"], if: "act>=2" },
    logline: "The Unpaid want to become a company. A company needs a big win. Employee of the Month has decided the big win is you.",
    twist: "What he actually wants is a performance review: someone, anyone, to tell him how he's doing. If you took his internship in m02, you're 'staff' and you can give him one after the fight (a dialogue). Whatever you say, he takes it seriously. 'MEETS EXPECTATIONS' makes him cry. He takes one plaque off his chest and gives it to you. It has your face on it.",
    beats: ["Camp Onboarding: a bus depot made of desks. A job fair that's an ambush.", "World boss: EMPLOYEE OF THE MONTH on his war-rig.", "The review."],
    steps: [
      { id: "camp", text: "attend camp onboarding's job fair", goal: { type: "reach", zone: "commute:unpaid_camp" } },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "eotm" }, boss: "eotm" },
      { id: "review", text: "give him a performance review", goal: { type: "talk", who: "eotm", talk: "review" } },
    ],
    talks: {
      review: { with: "eotm", cam: "closeup", nodes: {
        start: { say: ["*On the stalled war-rig's roof, plaques cracked, Craig sits with his helmet off.*", "is this... is this a performance review?"], opts: [["exceeds expectations.", "exceeds"], ["meets expectations.", "meets"], ["see me.", "see"]] },
        exceeds: { say: ["*He stares.* nobody's ever... nobody's ever said that. i've said it. i've said it seven hundred and thirty-two times."], next: "plaque" },
        meets: { say: ["*His lip wobbles. He cries, enormously.* MEETS. i MEET them. i meet expectations."], next: "plaque" },
        see: { say: ["*He nods slowly.* ...that's fair. that's honest feedback. i'll take it on board. the board is a desk."], next: "plaque" },
        plaque: { say: ["*He unbolts one plaque from his chest and holds it out. It's been re-engraved, badly, with a nail: EMPLOYEE OF THE MONTH: THE MACHINE THING. Your face, scratched in.*"], do: ["flag:eotm_reviewed"] },
      } },
    },
    choices: [],
    reward: { coupons: 1200, loot: ["lt_boss_eotm"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME." },
  },

  sq_commute_mandatory_fun: {
    kind: "side", from: 2, title: "MANDATORY FUN", giver: "smiles", district: "commute",
    locations: ["commute:carnival"], cast: ["morale_officer", "smiles"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "The Fun Department's carnival comes out at night on the Commute. Every game is rigged, and losing one is a fight.",
    twist: "The Morale Officer wrote 'every Big Value is a shelter'. The carnival's noise is so she never has to hear the quiet. The way to beat her for good is to stop shooting and wait. Mr. Smiles, if he's with you, takes his own glove off (just the glove) and holds her hand while she takes her heads off.",
    beats: ["The Fun Fair: ring toss, hook-a-duck, whack-a-mole with real moles, a ghost train that's a real ghost train.", "Win three games (each loss is a mascot brawl).", "World boss: THE MORALE OFFICER.", "The quiet."],
    steps: [
      { id: "fair", text: "win 3 games at the fun fair", goal: { type: "interact", target: "commute:carnival" }, if: "clock.commute=20:00-04:00" },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "morale_officer" }, boss: "morale_officer" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 1100, loot: ["lt_boss_morale_officer"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. FUN!", meets: "MEETS EXPECTATIONS. fun.", see_me: "SEE ME. you had fun. it was mandatory." },
  },

  sq_commute_unlucky_13: {
    kind: "side", from: 2, title: "UNLUCKY 13", giver: "nell", district: "commute",
    locations: ["commute:digit_13", "numberworks:union_hall"], cast: ["nell", "unlucky_13"],
    requires: { missions: ["m15_rounding_down"], if: null },
    logline: "The fallen 13 on the Commute is waking up. It was one of Remainder's orbital billboards that guided the missiles, and its last target list is still loaded.",
    twist: "Its last target is the Bottom. It's been trying to fire for sixty-one years and never had the power. The fights you've had near it have been charging it. Nell's union were stamped with 13s because the satellite was a 13: 'they put the number on us that they put on the thing that killed us. management's sense of humour.'",
    beats: ["Nell: the Remainders want it dead. It's personal.", "The hot zone: radiation, glassed craters, toxic green glow.", "World boss: UNLUCKY 13.", "Its last panel: the target list, crossed out."],
    steps: [
      { id: "nell", text: "", goal: { type: "talk", who: "nell", talk: "thirteen" }, marker: "numberworks:union_hall" },
      { id: "boss", text: "shut down the 13", goal: { type: "killBoss", boss: "unlucky_13" }, boss: "unlucky_13", marker: "commute:digit_13" },
    ],
    talks: {
      thirteen: { with: "nell", nodes: { start: { say: ["*Nell, without the megaphone for once.*", "you know why they stamp us with thirteen? because the satellite was a thirteen. the one on the commute. it guided the first launch.", "they put the number on us that they put on the thing that killed us. management's sense of humour.", "it's waking up. the meters in the hot zone are climbing. motion: we turn it off. all in favour? *she raises her own hand.* carried."] } } },
    },
    choices: [],
    reward: { coupons: 1300, loot: ["lt_boss_unlucky_13"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. target cancelled.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you were rounded up." },
  },
};
