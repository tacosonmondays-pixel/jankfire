// OVERDUE main missions, Act II: "Hostile Takeovers" (Pinstripe, The Checkout, Number Works, The Commute, and the
// Last Workday flashbacks inside the sims). The act's question: who did this? Same schema as missions/act1.js.
// The three company districts can be played in any order; the flashbacks unlock by how many pages you hold
// (pages>=1, >=2, >=3), not by which district, so they always play 16:00 → 16:45 → 17:20 → 17:29.

export const MISSIONS_ACT2 = {
  // ------------------------------------------------------------------ 6
  m06_option_c: {
    act: 2, n: 6, title: "OPTION C", kind: "main", giver: "auntie", district: "bottom",
    locations: ["bottom:lostfound", "bottom:gordo_den", "bottom:machine"],
    cast: ["auntie", "gordo", "lumps", "dale"],
    requires: { missions: ["m05_second_stomach"], if: null },
    logline: "Auntie lays out her wall of evidence: six companies signed the end of the world, each one kept its page, and with all six she can prove every debt they collect is a lie.",
    beats: [
      "C6: the wall, the six frames. Auntie explains Option C. Gordo asks how she knows; she dodges again.",
      "Dale: the Machine has a sim in it that's never been played, locked, and the lock is a document.",
      "Gordo's den: string, maps, stolen binders. His intel on where the three nearest pages are: Pinstripe (the Villa, 'up'), the Checkout ('it went into the Cart Mother'), Number Works ('in the Foreman's head, apparently, which is either a metaphor or worse').",
      "Lumps wants to go to the Gut for the nine. Auntie: not yet; the pages first, because the pages are how you stop the trucks for good. Lumps agrees, badly.",
      "The districts open. Pick where to go first.",
    ],
    reveals: {
      learn: ["Option C was a document: a deck and a contract, signed by six boards at 16:59.", "Each company kept its page. Together they prove the launch was deliberate and the debts are fake.", "The Machine holds a locked sim that a page might open."],
      suspect: ["Auntie knows far too much for 'an auditor'.", "The locked sim is about you."],
      withheld: ["What's on each page.", "That Auntie was there (m17)."],
    },
    steps: [
      { id: "wall", text: "", goal: { type: "flag", flag: "seen_c6" }, scene: "c6_option_c", marker: "bottom:lostfound" },
      { id: "den", text: "talk to wee gordo about the pages", goal: { type: "talk", who: "gordo", talk: "intel" }, marker: "bottom:gordo_den" },
      { id: "lumps", text: "", goal: { type: "talk", who: "lumps", talk: "not_yet" } },
      { id: "go", text: "pick a district: pinstripe, the checkout or number works", goal: { type: "flag", flag: "act2_open" }, do: ["unlock:pinstripe:respect_bridge", "unlock:checkout:doors", "unlock:numberworks:yard"] },
    ],
    talks: {
      intel: {
        with: "gordo", cam: "overShoulder",
        nodes: {
          start: { say: ["*Gordo's den: a shipping container wallpapered with maps, red string, and ☺ CORP binders with the spines cut off. A photo of Marion Hask with the eyes crossed out in crayon.*", "right. listen. three pages close enough to steal. three that aren't. we start with the close ones.", "pinstripe. the family keeps theirs in the villa. everyone says 'it's upstairs'. nobody's been upstairs. there's no upstairs. there's strings.", "the checkout. big value's page went into the cart mother. 'into'. i asked twice.", "number works. remainder keeps it in the foreman's head. that's either a metaphor or it's worse."], opts: [["who's the woman with the crossed-out eyes?", "hask"], ["what about the other three?", "others"], ["why are you helping auntie?", "why"]] },
          hask: { say: ["marion hask. ☺ corp's chief punctuality officer. she runs the schedule. she signed for ☺ corp, if auntie's right.", "she's a hundred and one. she's been a hundred and one for a while. she's got very good doctors.", "*he taps the photo.* she's the reason my family's down here."], opts: [["what happened?", "family"], ["what about the other three pages?", "others"]] },
          family: { say: ["*a beat too long*", "we were late. it doesn't matter. ask me when we've burned something."], do: ["flag:gordo_hinted_birth"], next: "others" },
          others: { say: ["gristle and sons in the gut. nobody knows. vacancy holdings at the margins, which is past the edge of anything i've mapped.", "and ☺ corp's own copy. top of the spire. on her desk, i'd bet. where else would you keep the end of the world."] },
          why: { say: ["i'm not helping auntie. auntie's helping me.", "she wants to prove they lied. i want to prove it and then light it.", "*he holds up a match. he doesn't strike it.* we can share."] },
        },
      },
      not_yet: {
        with: "lumps",
        nodes: {
          start: { say: ["*Lumps is outside, sitting on a fridge, looking up the hill toward the Gut.*", "nine. mum makes ten.", "nan says pages first. pages stop the trucks for good. i know. i'm not stupid. i know.", "it's just... they're in the wall right now. today. pages are tomorrow."], opts: [["we'll get them out. after the pages.", "after"], ["you're right. we should go now.", "now"], ["*sit on the fridge with him*", "sit"]] },
          after: { say: ["*He nods slowly.*", "ok. i believe you. i'm going to hold you to it. i hold on to things."], do: ["flag:promised_lumps_after_pages", "standing.bottom:+1"] },
          now: { say: ["*He looks at you with enormous gratitude, then at the Lost & Found door.*", "...she's right though. nan's always right. i hate it.", "pages. then mum. ok."], do: ["flag:sided_with_lumps_early", "standing.bottom:+2"] },
          sit: { say: ["*The fridge creaks. You sit there for a while. A kid on a scooter goes past and waves at you both.*", "this is nice. you're nice for a vending machine thing.", "pages. then mum. ok."], do: ["standing.bottom:+2"] },
        },
      },
    },
    choices: [],
    scenes: ["c6_option_c"],
    reward: { coupons: 100, flags: ["act2_started"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you understood the string.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you asked who the cat was. it was a cushion." },
  },

  // ------------------------------------------------------------------ 7 (pinstripe 1/2)
  m07_an_offer: {
    act: 2, n: 7, title: "AN OFFER", kind: "main", giver: "don", district: "pinstripe",
    locations: ["pinstripe:respect_bridge", "pinstripe:restaurant", "pinstripe:clown_cellar", "corphill:bleach_line"],
    cast: ["don", "pip", "larry"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "In Pinstripe the Don makes you an offer you could refuse, and his jesters make you a different one.",
    beats: [
      "Respect Bridge: pay respect (coupons, or a compliment to a goon, who's touched).",
      "C7 at Mamma Polizza's: Pip and Larry at the door; the Don descends on his strings. 'everybody wants that page. nobody wants what comes with it.' His job: collect the Family's premium from ☺ CORP's tax office on the Bleach Line.",
      "Pip catches you outside. The Punchlines want the Family to fall apart; Pip noticed the Don laughs a second late. Their job: a prank on the same tax run (swap the premium for a cake that explodes into confetti on the Don's table).",
      "The run: hit ☺ CORP's tax office (Late Fees go up). Collect the premium. Decide whose job you finish (it decides who trusts you going into the Villa, not the district).",
      "Larry, alone, at the end: 'i know where the strings go. i've always known. nobody asked.'",
    ],
    reveals: {
      learn: ["The Family insured every side of the war and paid out nothing ('act of shareholders').", "The Don's strings go up into the Villa ceiling, and nobody knows who's up there."],
      suspect: ["The Don laughs a second late, like someone else is doing the laughing.", "Larry knows."],
      withheld: ["Nonna (m08)."],
    },
    steps: [
      { id: "bridge", text: "cross respect bridge", goal: { type: "reach", zone: "pinstripe:respect_bridge" }, talk: "respect" },
      { id: "dinner", text: "meet the family at mamma polizza's", goal: { type: "reach", zone: "pinstripe:restaurant" }, scene: "c7_an_offer" },
      { id: "pip", text: "", goal: { type: "talk", who: "pip", talk: "punchlines" } },
      { id: "tax", text: "collect the family's premium from the ☺ corp tax office", goal: { type: "pickup", item: "family_premium" }, marker: "corphill:bleach_line", notes: "the tax office sits right on the Bleach Line: Late Fees ★2 guaranteed on the way out" },
      { id: "whose", text: "deliver the premium", goal: { type: "flag", flag: "premium_choice_made" } },
      { id: "larry", text: "", goal: { type: "talk", who: "larry", talk: "strings" } },
    ],
    talks: {
      respect: {
        with: "goon",
        nodes: {
          start: { say: [["goon", "*a huge pinstriped puppet with tiny hands blocks the bridge* respect bridge. you pay respect."]], opts: [["*pay 50 coupons*", "pay"], ["that's a beautiful suit.", "suit"], ["*keep walking*", "walk"]] },
          pay: { say: [["goon", "respect received. very respectful."]], do: ["coupons:-50"] },
          suit: { say: [["goon", "*long pause* ...nobody's ever said that. it's my dad's."], ["goon", "*he steps aside, wiping an eye with a tiny hand* go on. go on."]], do: ["flag:complimented_goon"] },
          walk: { say: [["goon", "that's disrespect."]], do: ["flag:disrespected_family"] },
        },
      },
      punchlines: {
        with: "pip", cam: "closeup",
        nodes: {
          start: { say: ["*An alley behind the restaurant. Pip sits on a bin. Larry stands next to it, which makes him about the height of the lamp post.*", "darling. you were wonderful. the meatballs were terrified.", "here's a joke. what's got strings, a grin, and laughs one second after i do?", ["larry", "...the don."], "LARRY. you don't say the punchline. we've discussed this.", "the family's been hollow for years, darling. somebody up in that ceiling is working him. and i'd like to know who before i cut the strings."], opts: [["what do you want from me?", "want"], ["why do you want to bring the family down?", "why"], ["i'm only here for a page.", "page"]] },
          want: { say: ["you're running the don's errand to the tax office. lovely. run ours at the same time.", "*Larry produces a cake from inside his coat. It's enormous. It ticks.*", "swap the premium for the cake. the don opens it at dinner. confetti. everywhere. in his mouth. nobody laughs, and we see who's laughing."], next: "page" },
          why: { say: ["*For one line Pip stops smiling.*", "my mum filed a claim on her own policy. against the family. the claim was denied. so was she.", "*the smile comes back, wider* anyway! cake!"], do: ["flag:pip_told_mum"], next: "want" },
          page: { say: ["the page is up, darling. everything in this family is up. we'll get you up. if you're funny."] },
        },
      },
      strings: {
        with: "larry", cam: "closeup",
        nodes: {
          start: { say: ["*Later. Larry finds you on Respect Bridge, alone. Pip isn't with him. That's rare.*", "a man walks into a bar. it's a metal bar. he's hurt. that's the joke.", "*you wait. he doesn't explain it this time.*", "i know where the strings go. i've always known. nobody asked."], opts: [["where do they go?", "where"], ["why didn't you tell pip?", "pip"]] },
          where: { say: ["up. to someone who was kind to me once. when i was small. she gave me soup.", "i'll show you the way up. the crawlspace. if you promise me one thing.", "don't hurt her. she's very old."], opts: [["i promise.", "promise"], ["i can't promise that.", "cant"]] },
          pip: { say: ["pip would cut the strings without looking up. pip's angry. pip's allowed to be angry.", "i just think you should look up first."], next: "where" },
          promise: { say: ["*His droopy nose twitches. It might be a smile.*", "thank you. that's the first promise anybody's made me. it's long. like me."], do: ["flag:larry_crawlspace", "flag:promised_larry"] },
          cant: { say: ["...no. that's fair. nobody promises anything in pinstripe. it's an insurance district.", "i'll show you anyway. look up first. that's all."], do: ["flag:larry_crawlspace"] },
        },
      },
    },
    choices: [
      { id: "premium", prompt: "You've got the Family's premium from the tax office. Pip gave you a ticking cake.", options: [
        { id: "don", label: "deliver the premium to the Don", do: ["flag:did_don_job", "flag:premium_choice_made", "standing.corp:-2"], consequence: "The Family trusts you. In m08 you walk into the Villa through the front door, as a guest, and the DEAL is easier to get (Nonna's price is lower). Pip is cool with you for a while." },
        { id: "pip", label: "swap it for Pip's cake", do: ["flag:did_pip_job", "flag:premium_choice_made", "flag:cake_prank"], consequence: "At dinner the cake explodes into confetti in the Don's mouth. The Don laughs one full second after everyone else. Every goon in the room sees it. In m08 the Family is rattled (fewer guards at the Villa), the Punchlines trust you, and you keep the premium (+400 coupons)." },
      ] },
    ],
    scenes: ["c7_an_offer"],
    reward: { coupons: 250, loot: ["lt_district_pinstripe"], flags: ["met_family", "met_punchlines"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. the meatball rolled off the table in your favour.", meets: "MEETS EXPECTATIONS. you're covered.", see_me: "SEE ME. you disrespected a bridge." },
  },

  // ------------------------------------------------------------------ 8 (pinstripe 2/2)
  m08_family_business: {
    act: 2, n: 8, title: "FAMILY BUSINESS", kind: "main", giver: "pip", district: "pinstripe",
    locations: ["pinstripe:villa", "pinstripe:rafters", "pinstripe:clown_cellar"],
    cast: ["don", "nonna", "pip", "larry"],
    requires: { missions: ["m07_an_offer"], if: null },
    logline: "The Family's page is up in Villa Fazzoletto. So is whoever works the Don's strings.",
    beats: [
      "Into the Villa: as a guest (did_don_job), through the Punchlines' green room (did_pip_job), or up Larry's crawlspace (larry_crawlspace).",
      "The Don 'assesses' you: an underwriter's assessment, in the marble ballroom. Boss fight: DON GRINALDI FAZZOLETTO. Shoot the strings, drop the limbs.",
      "Mid-fight he makes an offer: take the bribe and skip phase 2.",
      "His jaw falls off and keeps talking, in a different, older voice. Phase 3: up in the rafters, Nonna.",
      "Nonna in her nest of pulleys, the Don's body hanging below, the page pinned to her knitting. The Don died in the Long Dark's fourth winter. She's been doing his voice ever since.",
      "P6b, the district choice: DEAL with Nonna, or TAKEOVER (Pip cuts the strings).",
      "The page: 'act of shareholders'. Page 1 (or whichever number) goes on Auntie's wall.",
    ],
    reveals: {
      learn: ["Fazzoletti page: 'act of shareholders' — no policy pays out on a loss the policyholders' own board caused. They insured the war knowing they'd started it.", "Nonna was the Family's signatory. The Don was always a puppet."],
      suspect: ["Every company has someone else holding the strings.", "Insurance-by-design: the war was budgeted."],
      withheld: ["The other five pages."],
    },
    steps: [
      { id: "in", text: "get into villa fazzoletto", goal: { type: "reach", zone: "pinstripe:villa" }, talk: "way_in" },
      { id: "don", text: "survive the family's assessment", goal: { type: "killBoss", boss: "don" }, boss: "don", marker: "pinstripe:villa" },
      { id: "up", text: "climb to the rafters", goal: { type: "reach", zone: "pinstripe:rafters" } },
      { id: "nonna", text: "talk to whoever's holding the strings", goal: { type: "talk", who: "nonna", talk: "rafters" } },
      { id: "choice", text: "decide who runs pinstripe", goal: { type: "flag", flag: "pinstripe_decided" }, scene: "p6b_deal_or_takeover" },
      { id: "home", text: "take the page to auntie", goal: { type: "deliver", item: "page_family", zone: "bottom:lostfound" }, talk: "wall" },
    ],
    talks: {
      way_in: {
        with: "pip",
        nodes: {
          start: { say: ["*Outside the Villa: a cathedral of marble and meatballs. Strings rise from its roof into the clouds.*"], opts: [["*go in the front door, as a guest*", "front", { if: "flag:did_don_job" }], ["*go in through the green room with the punchlines*", "green", { if: "flag:did_pip_job" }], ["*take larry's crawlspace*", "crawl", { if: "flag:larry_crawlspace" }], ["*go in shooting*", "loud"]] },
          front: { say: [["goon", "the guest. come in. the don's expecting you. shoes off. it's marble."]], do: ["flag:villa_as_guest"] },
          green: { say: ["*The Punchlines' green room under the Villa: mirrors, red noses, a hundred clowns doing warm-ups.*", "darling. second floor's ours. after that you're on your own. break a leg. not literally. well. if necessary."], do: ["flag:villa_via_punchlines"] },
          crawl: { say: [["larry", "*Larry folds himself into a hatch behind the bins, which shouldn't be possible.*"], ["larry", "mind your head. mind your everything. it's a crawlspace. it's very much a crawlspace."]], do: ["flag:villa_via_crawlspace"] },
          loud: { say: [["goon", "that's disrespect."]], do: ["flag:disrespected_family", "fees:+1"] },
        },
      },
      rafters: {
        with: "nonna", cam: "closeup",
        nodes: {
          start: { say: ["*The rafters above the Villa: a vast dark attic of pulleys and marionette bars, the Don's strings running over wheels to a nest in the middle. In it, a tiny ancient woman in black lace with a huge head and huge spectacles, knitting with the end of the strings.*", "*Below her, hanging from the bars, the Don's body sways. Up close the grin is wax. The eyes have been closed for a long time.*", "my son is resting. you will speak to me.", "assunta fazzoletto. nonna, to the family. the board, to anyone who reads the paperwork. nobody reads the paperwork."], opts: [["how long has he been dead?", "dead"], ["you signed option c.", "signed"], ["i want the page.", "page"]] },
          dead: { say: ["the fourth winter of the long dark. in his sleep. he was smiling. he always smiled. i had them treat him so it would hold.", "a family needs a face. a face needs a grin. a grin needs someone to pull it.", "*she gives one string a tug. Far below, the Don's hand waves to nobody.*"], next: "signed" },
          signed: { say: ["of course i signed. my son smiled for the photograph. i held the pen.", "everything is a risk. i price it. we insured every side of that war, and every bunker, and every pension.", "and then we wrote one clause. act of shareholders. no policy pays out on a loss the policyholders' own board caused. their own board. the boards that signed.", "*she smiles, thinly* nobody is to blame. that's the beauty of it."], do: ["flag:read_page_family"], next: "page" },
          page: { say: ["*She lifts her knitting. Pinned to it, a single sheet of heavy paper with the Fazzoletti crest, a clause, and her signature next to her son's photograph.*", "take it. it's no use to me now. the family pays nothing. the family has paid for nothing since 1850. a piece of paper doesn't change that.", "the question, merchandise, is what you pay for it."], do: ["give:page_family"] },
        },
      },
      wall: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*Auntie takes the page with both hands, the way you'd hold a baby you didn't trust. She reads it twice. She pins it into its masking-tape frame.*", "act of shareholders.", "they insured the war knowing they'd started it. they sold people policies against the end of the world and wrote the end of the world out of the policy.", "*she writes it in the notebook in crayon.* that's one.", ["dale", "*from the Machine* agnes. she's doing something. the sim. it's unlocking."]] },
        },
      },
    },
    choices: [
      { id: "don_bribe", prompt: "Mid-fight, the Don stops. 'my friend. this is unpleasant. a gift, and we skip to the end.' (a purse of 600 coupons)", options: [
        { id: "take", label: "take the bribe", do: ["coupons:+600", "flag:took_don_bribe", "standing.corp:+1"], consequence: "Phase 2 is skipped. Nonna remembers you as someone with a price, which lowers the cost of a DEAL and means the Family thinks it owns you (in Act IV it asks for a favour back)." },
        { id: "refuse", label: "keep shooting", do: ["flag:refused_don_bribe"], consequence: "Phase 2 plays. Pip, watching from the gallery, laughs on time for once." },
      ] },
      { id: "district_choice", prompt: "Nonna holds the strings. Pip has a pair of scissors. Who runs Pinstripe?", options: [
        { id: "deal", label: "DEAL: the Family stays, and owes you", do: ["turf:pinstripe=family", "flag:pinstripe_deal", "flag:pinstripe_decided", "standing.corp:+5", "flag:pages_family"], consequence: "Nonna keeps the strings and keeps her word to the letter: the Family stops collecting protection from the Bottom, gives you 25% off in Pinstripe and sends its limos to the Act IV raid (if Corp Standing is high it may turn mid-raid). The Punchlines stay jesters. Pip doesn't forgive you until the epilogue." },
        { id: "takeover", label: "TAKEOVER: the Punchlines run Pinstripe", do: ["turf:pinstripe=punchlines", "flag:pinstripe_takeover", "flag:pinstripe_decided", "standing.bottom:+5", "standing.corp:-5", "flag:pages_family"], consequence: "Pip cuts the strings. The Don falls; they bury him properly, as a joke that isn't one. Nonna climbs down by herself, slowly, for the first time in fifty years. The Punchlines run Pinstripe (red noses on every door, pranks instead of protection) and are loyal allies in the raid. The Family's goons become hostile there and its boss comes back as a raider." },
      ] },
    ],
    scenes: ["p6b_deal_or_takeover"],
    reward: { coupons: 800, items: ["page_family"], loot: ["lt_boss_don"], flags: ["beat_don"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you looked up first.", meets: "MEETS EXPECTATIONS. one page, one family, some strings.", see_me: "SEE ME. you shot the strings. all of them. the chandelier too." },
  },

  // ------------------------------------------------------------------ 9 (flashback F1)
  m09_workday_1600: {
    act: 2, n: 9, title: "THE LAST WORKDAY: 16:00", kind: "flashback", giver: "dale", district: "sims",
    locations: ["bottom:machine", "sims:lobby", "sims:spire_60"],
    cast: ["cale", "agnes", "overtime", "dale", "auntie"],
    requires: { missions: [], if: "pages>=1" },
    logline: "The first page unlocks a sim nobody has ever played: you, as R. Cale, on the 60th floor of the ☺ Spire, on the last afternoon of the world.",
    beats: [
      "Dale opens the locked sim. Auntie watches from the doorway and leaves before it starts.",
      "15:55: the ☺ Spire lobby, as it was. Cale comes back from a coffee run with six coffees. Mr. Overtime at the security desk, cleaner and newer, an overcoat over his chair: 'you're cutting it fine, cale.'",
      "The lift up to 60: colleagues chatting about New Year's Eve, a party, going home early. Cale's calendar on the lanyard screen: '17:30 M'.",
      "The 60th floor, Internal Audit: walk the floor, hand out coffees, a small audit task (spot the fake invoice) so the player gets Cale's job in their hands.",
      "16:00: Agnes Pell, 24, calls Cale into her office. Closes both doors. The deck on her screen: OPTION C: STRATEGIC WRITE-OFF.",
      "She makes Cale read slide 31 out loud. The target lists are cities. The timestamp on the launch slide is 17:30.",
      "Agnes: they need a copy. A real one, on tape, from the print room drive. Cale has a sister to pick up at 17:30.",
      "The sim glitches at 16:20 and spits you out.",
    ],
    reveals: {
      learn: ["You were R. Cale, a junior auditor on the 60th floor.", "Agnes Pell found Option C and showed it to Cale at 16:00.", "Cale had someone to pick up at 17:30: 'M'.", "Overtime was already in the Spire, already Head of Timekeeping, before the war."],
      suspect: ["Agnes Pell is Auntie Spreadsheet.", "'M' is Mina."],
      withheld: ["What happens to Cale (F4).", "That Auntie froze on the stairs."],
    },
    steps: [
      { id: "load", text: "let dale load the locked sim", goal: { type: "talk", who: "dale", talk: "locked" }, marker: "bottom:machine" },
      { id: "lobby", text: "deliver the coffees (it's 15:55)", goal: { type: "reach", zone: "sims:lobby" }, talk: "lobby_1555" },
      { id: "lift", text: "take the lift to 60", goal: { type: "reach", zone: "sims:spire_60" }, talk: "lift" },
      { id: "floor", text: "hand out the coffees", goal: { type: "interact", target: "sims:spire_60" }, notes: "six desks; each colleague has one line; the last coffee is Agnes's" },
      { id: "invoice", text: "find the fake invoice", goal: { type: "interact", target: "sims:spire_60" }, notes: "a 20-second spot-the-difference on three invoices: teaches that Cale was good at the job" },
      { id: "agnes", text: "agnes wants you in her office", goal: { type: "talk", who: "agnes", talk: "deck" } },
      { id: "out", text: "", goal: { type: "flag", flag: "f1_done" }, talk: "after_f1" },
    ],
    talks: {
      locked: {
        with: "dale", cam: "closeup",
        nodes: {
          start: { say: ["*Dale has the Machine's service panel open. Wires everywhere. A green menu on a tiny screen with one item that's been greyed out for sixty-one years: LAST WORKDAY (LOCKED: DOC REQ).*", "she's had this in her since the end. sixty-one years. never played. you hold the page against the glass.", "*Auntie is in the doorway behind you. When the menu item goes white, she turns and leaves.*", "...ignore her. she gets like that about the machine. lean your head on the glass. that's it. it's cold. you'll go in."], opts: [["what is it?", "what"], ["*lean on the glass*", "go"]] },
          what: { say: ["a sim. a recording. somebody's last afternoon. the menu says yours. the menu's been wrong before. ...not often."], next: "go" },
          go: { say: ["*The glass is cold. The hum gets louder. The ruins go white.*"], do: ["flag:f1_loaded"] },
        },
      },
      lobby_1555: {
        with: "overtime", cam: "lowAngle",
        nodes: {
          start: { say: ["*The ☺ Spire lobby before the end: marble, sunlight, a revolving door, staff in a hurry, New Year's Eve tinsel on the security desk. You're holding a cardboard tray of six coffees. Your trainers are in your backpack; you're in work shoes that pinch.*", "*At the desk: Mr. Overtime, the same 4.5 m body, the same punch-clock heart ticking, but newer, cleaner, the suit pressed. A huge grey overcoat is folded over his chair. A lunchbox with a note taped to it.*", "cale. you're cutting it fine. 16:00 is in four minutes.", "that's six coffees. is one of them for me? no. i don't drink it on shift. i'm only asking."], opts: [["sorry, mr. sallow. agnes wanted them.", "agnes"], ["what's in the lunchbox?", "lunch"], ["are you going home early tonight?", "home"]] },
          agnes: { say: ["ms. pell. she works you hard. good. hard work is how you get a desk by a window.", "go on. lift three. it's on time."] },
          lunch: { say: ["*He looks at the note. For a moment his stretched smile changes into something smaller and real.*", "my wife. june. 'don't be late tonight. it's our forty. love, j.'", "forty years. i've never once been late for anything. except her. she says i'm always late for her.", "17:30 tonight. on the dot. go on, cale. lift three."], do: ["flag:saw_june_note"] },
          home: { say: ["17:30. the same as every day. no earlier. we're asked to keep the lobby until close of business tonight. some lockdown thing. ms. hask's orders.", "...but at 17:30 i'm out of that door. it's our anniversary. go on. lift three."], do: ["flag:heard_lockdown"] },
        },
      },
      lift: {
        with: "agnes", cam: "overShoulder",
        nodes: {
          start: { say: ["*Lift three. Colleagues squashed in with you, all talking at once about tonight.*", ["voice", "are you going to kev's thing?"], ["voice", "i'm going home. i'm going home and i'm lying on the floor."], ["voice", "they said q4's a disaster. like, a disaster disaster. somebody on 100 was crying in the toilets."], ["voice", "it's new year's eve, who cares. it's next year's problem."], "*Your lanyard screen shows your calendar for today. It's empty except for one entry: 17:30 M.*"] },
        },
      },
      deck: {
        with: "agnes", cam: "closeup",
        nodes: {
          start: { say: ["*Agnes Pell's office: a window desk on 60, a view of the whole city before the end, spreadsheets taped to the glass. Agnes is twenty-four, in a grid blazer, red pen in her teeth. She takes her coffee without looking at it.*", "cale. close the door. no, the other door. both doors.", "*you close both doors.*", "sit. don't touch anything. look at this."], next: "screen" },
          screen: { say: ["*On her monitor: a slide deck. A ☺ CORP logo, five more logos, and a title: OPTION C: STRATEGIC WRITE-OFF. CONFIDENTIAL. BOARD EYES ONLY.*", "it was in a printer queue on 58. somebody on the hundredth floor sent forty pages to the wrong printer and then cancelled it. i got there before the cancel.", "slide thirty-one. read me the number in the corner. out loud."], opts: [["(read it) '4,112,006,551'.", "read"], ["agnes, what is this?", "what"]] },
          what: { say: ["read it first. out loud. if i say it, it's me saying it. if you say it, it's a reading."], next: "read" },
          read: { say: ["*You read it. Four billion, one hundred and twelve million, six thousand, five hundred and fifty-one. Underneath: FORECAST: POST-EVENT HEADCOUNT REDUCTION. And a list. You know some of the names on the list. They're cities.*", "*Agnes taps the next slide with the red pen. EXECUTION: 17:30 TODAY (CLOSE OF BUSINESS). A cheerful clip-art clock.*", "that's not a forecast, that's a target list. those are cities. this is a launch order with a spreadsheet attached.", "and slide forty. 'liabilities extinguished at close of business: wages, pensions, debts, all divisions.' they're writing off the world, cale. so they don't have to pay for it."], opts: [["we have to tell someone.", "tell"], ["this can't be real.", "real"], ["what do you want me to do?", "do"]] },
          tell: { say: ["who? security works for them. the police work for them. the government was bought at an auction. it's them all the way down.", "we don't tell. we copy. we get it out of the building and put it everywhere at once."], next: "do" },
          real: { say: ["it's real. i audited the printer. *a laugh with no air in it* i actually audited the printer. it's real."], next: "do" },
          do: { say: ["the print room drive on this floor writes to tape. it's slow, it's ancient, and it's the only thing in the building that doesn't log to the hundredth floor.", "i need a copy on tape. by five. then we walk out at close of business like everybody else, and we give it to every newsroom that's left.", "you're faster than me. you're faster than everyone on this floor. that's not a compliment, it's logistics."], opts: [["i have to pick my sister up at half five.", "mina"], ["ok. i'll do it.", "yes"]] },
          mina: { say: ["*She looks at the clip-art clock on the slide. Then at you.*", "then we'd better be done by five, hadn't we.", "cale. if this is real, there isn't going to be a half five. not for her. not for anybody."], next: "yes" },
          yes: { say: ["*She pulls the red pen out of her teeth and writes on a sticky note: TAPE. 16:45. PRINT ROOM. She sticks it on your lanyard.*", "go and look normal. drink a coffee. i'll come and get you.", "*As you open the door, she says it to the screen, not to you:* thank you, rory."] },
        },
      },
      after_f1: {
        with: "dale", cam: "closeup",
        nodes: {
          start: { say: ["*The sim glitches: the office smears, the city outside the window goes grey, the coffee in your hand pixelates. You're back with your forehead on the Machine's glass.*", "...you all right? you went white. you can't go white. you're plastic.", "*Dale looks at the menu.* there's more. it's locked again. it wants another page."], opts: [["she called me rory.", "rory"], ["where's auntie?", "auntie"]] },
          rory: { say: ["*Dale takes a long time to put a screwdriver back in his pocket.*", "...yeah. i'd bet she did."], do: ["flag:knows_name_rory"] },
          auntie: { say: ["went for a walk. she doesn't go for walks.", "she'll be back. she always comes back to the machine. we both do."] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 0, flags: ["f1_done", "knows_cale"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you found the fake invoice in four seconds. you were good at your job.", meets: "MEETS EXPECTATIONS. 16:00.", see_me: "SEE ME. you spilled agnes's coffee. she'll remember. she does." },
    notes: "the sims look clean and bright (DESIGN §7.2): the contrast with the ruins is the point. Drift: at drift>=3 the colleagues' faces are blank and the lines are dimmer.",
  },

  // ------------------------------------------------------------------ 10 (checkout 1/2)
  m10_doorbusters: {
    act: 2, n: 10, title: "LOST CHILD", kind: "main", giver: "wristband", district: "checkout",
    locations: ["checkout:queue", "checkout:vents", "checkout:pa_booth", "checkout:returns"],
    cast: ["wristband", "gail", "cart_mother"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "In the Big Value mall's air vents, the lost child from the Stampede is sixty-six now. He reads the barcode on your neck and goes white.",
    beats: [
      "The Checkout: the Infinite Queue, the dome, mannequin shoppers in every window. Gail on the PA. 'we're sorry for any inconvenience.'",
      "Cart surfing and escalators to the vents, chased by Mall Security on segways.",
      "The Mall Rats: families in the air vents, rope bridges, hammocks, a school. Wristband: soft, polite, old.",
      "He reads your barcode: CALE. He tells you about the Stampede: the doors opened at 17:30 for members only. A girl of nine lifted him into a vent. Her name tag said MINA CALE. She said her big sibling worked at the Spire and was coming at half five.",
      "If you heard 'rory?' on the truck: you know where Mina is. In the Gut.",
      "Big Value's page went into the Cart Mother: she read it while she waited at the doors, and swallowed it with her receipt.",
      "The Mall Rats give you the Shopping Cart Cannon: the counter to the Cart Mother. Gail, on the PA, says the doors open at 09:00. They always do.",
    ],
    reveals: {
      learn: ["The Stampede: Big Value's doors only opened for members. Thousands died outside.", "Cale had a nine-year-old sister, Mina, who survived the Stampede in the vents.", "Mina is the old woman Overtime took (if you've put it together)."],
      suspect: ["Gail is hiding something about the doors."],
      withheld: ["Who pressed the door lock (Gail, m11).", "That Mina is still alive in the Gut wall (m20)."],
    },
    steps: [
      { id: "queue", text: "get past the infinite queue", goal: { type: "reach", zone: "checkout:queue" }, notes: "cart surfing and escalators; the Mall Security segway patrol" },
      { id: "vents", text: "get into the vents", goal: { type: "reach", zone: "checkout:vents" } },
      { id: "milo", text: "talk to the mall rats' leader", goal: { type: "talk", who: "wristband", talk: "lost_child" }, marker: "checkout:vents" },
      { id: "cannon", text: "get the shopping cart cannon from the mall rats", goal: { type: "pickup", item: "mallrat_cart_cannon" } },
      { id: "pa", text: "", goal: { type: "talk", who: "gail", talk: "pa" }, notes: "Gail talks to you over the PA as you leave the vents; you can't reach her booth yet" },
    ],
    talks: {
      lost_child: {
        with: "wristband", cam: "closeup",
        nodes: {
          start: { say: ["*The vents: a whole village in the ducts above the Checkout. Hammocks, rope bridges, a classroom with a blackboard made of a SALE sign. Kids in goggles. An old man in a patched hoodie and a climbing harness pours you tea from a flask.*", "thank you for coming. nobody comes up. that's what a sale is.", "i'm milo. they call me wristband.", "*He holds up his wrist. A child's Big Value wristband, faded, cutting into the skin: LOST CHILD. PLEASE TAKE ME TO THE CUSTOMER SERVICE DESK.*", "may i see your neck? the barcode. i'm sorry. old habit. we read everything up here. it's how we know who's security."], opts: [["*turn round*", "scan"]] },
          scan: { say: ["*He reads it with a torch. Then he reads it again. His hand with the flask starts to shake.*", "c. a. l. e.", "...i'm sorry. i'm sorry. please sit. i need to sit."], next: "story" },
          story: { say: ["the doors. at 17:30 the sirens went and all the ads said every big value was a shelter. everybody came. my mum brought me. there were thousands of us outside.", "the doors opened for members. only members. they had a list. the people at the back didn't know. they kept coming. the people at the front couldn't go anywhere.", "*he's reading it like a list, very precisely, the way he's told it a thousand times.*", "i was five. i lost my mum at 17:34. a girl picked me up. she was nine. she had a strawberry on her bag.", "she put her wristband on me so the grown-ups would know i was lost. then she lifted me into a vent. and climbed in after me. we were in the dark for three days. she held my hand the whole time."], opts: [["what was her name?", "name"]] },
          name: { say: ["she never said her surname. i read it on her school name tag. i read it every day for three days because it was the only thing i could see.", "mina cale.", "she said her big sibling worked at the spire. she said they were coming to get her at half five.", "*he looks at you.* they never came."], do: ["flag:knows_mina"], next: "mina" },
          mina: { say: ["*He waits. He has been waiting a long time to say the next thing to somebody.*"], opts: [["...the woman on the truck. she said 'rory'.", "truck", { if: "flag:asked_about_rory" }], ["she was waiting for me.", "me"], ["is she alive?", "alive"]] },
          truck: { say: ["*He closes his eyes.*", "she left the mall at twenty. she went to find the spire. she got as far as the bottom. she wrote to me every year.", "if she's on a gristle truck, she's in the gut. people in the gut are alive for a long time. that's the worst thing about it. that's also the only good thing.", "please. if you're who that barcode says. please go and get her."], do: ["flag:knows_mina_in_gut", "standing.bottom:+3"], next: "page" },
          me: { say: ["*He doesn't say anything for a long time. He refills your tea though you haven't drunk any.*", "she never stopped. she used to say 'they're just late. they're always late.'"], next: "alive" },
          alive: { say: ["she lives in the bottom. top terrace. or she did. the letters stopped this month.", "*he looks at you, and you can see him working it out from your face.* ...oh.", "if she's been taken, she's in the gut. people in the gut are alive for a long time. that's the worst thing about it. and the only good thing."], do: ["flag:knows_mina_in_gut"], next: "page" },
          page: { say: ["you came for the page. big value's page. we know. we read everything.", "it went into the cart mother. brenda. she was first through the doors, a gold member. she read the page while she waited at the front of the queue, from a manager's clipboard, and when she understood it she swallowed it with her receipt.", "she's been big value's mascot ever since. every lost cart in the city goes to her.", "take this. *a Shopping Cart Cannon, painted with green rat faces.* shoot carts into her. she can't help picking them up. it makes her slow."], do: ["give:mallrat_cart_cannon"] },
        },
      },
      pa: {
        with: "gail",
        nodes: {
          start: { say: [["pa", "attention shoppers. there is a lost item in the vents. would the lost item please make its way to returns desk zero."], ["pa", "*a pause, then quieter, off the script* ...you're the one from the machine. aren't you. i read the security feed."], ["pa", "the doors open at 09:00. they always do. she comes out when they open. please don't hurt her. she's the only one who still shops."], ["pa", "we're sorry for any inconvenience."]] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 300, items: ["mallrat_cart_cannon"], loot: ["lt_district_checkout"], flags: ["met_mallrats"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you didn't buy anything.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you bought fourteen things." },
  },

  // ------------------------------------------------------------------ 11 (checkout 2/2)
  m11_no_refunds: {
    act: 2, n: 11, title: "NO REFUNDS", kind: "main", giver: "wristband", district: "checkout",
    locations: ["checkout:doors", "checkout:food_court", "checkout:cart_corral", "checkout:pa_booth"],
    cast: ["cart_mother", "wristband", "gail"],
    requires: { missions: ["m10_doorbusters"], if: null },
    logline: "The doors open at 09:00, like they have every day since the Stampede, and every lost cart in the city comes for you.",
    beats: [
      "C8 Doorbusters. The Cart Mother.",
      "Boss fight across the Food Court Colosseum and the Cart Corral. Shopping-cart cannon carts make her heavy.",
      "Phase 3: the carts fall away and it's Brenda, eighty-nine, holding a receipt. She wants to return the day. The page comes out with the receipt.",
      "Gail's booth. The old woman at the microphones. She pressed the lock at 17:31, on head office's instruction. She's said sorry over the PA every morning in code.",
      "P6b: DEAL with Gail (Big Value stays) or TAKEOVER (the Mall Rats shut the doors for good).",
    ],
    reveals: {
      learn: ["Big Value page: 'members-only continuity': shelter doors open for paid members only; non-members are 'stock shrinkage'. The Stampede was in the plan.", "Gail locked the doors on head office's orders."],
      suspect: ["Every page so far budgets for the dead in advance."],
      withheld: [],
    },
    steps: [
      { id: "doors", text: "be at the doors at 09:00", goal: { type: "reach", zone: "checkout:doors" }, scene: "c8_doorbusters" },
      { id: "boss", text: "stop the cart mother", goal: { type: "killBoss", boss: "cart_mother" }, boss: "cart_mother" },
      { id: "brenda", text: "", goal: { type: "talk", who: "cart_mother", talk: "refund" } },
      { id: "booth", text: "find gail", goal: { type: "talk", who: "gail", talk: "booth" }, marker: "checkout:pa_booth" },
      { id: "choice", text: "decide who runs the checkout", goal: { type: "flag", flag: "checkout_decided" }, scene: "p6b_deal_or_takeover" },
      { id: "home", text: "take the page to auntie", goal: { type: "deliver", item: "page_bigvalue", zone: "bottom:lostfound" }, talk: "wall" },
    ],
    talks: {
      refund: {
        with: "cart_mother", cam: "closeup",
        nodes: {
          start: { say: ["*The last carts clatter off her and roll away across the food court on their own. In the middle of the wreck: a small old woman in a fleece and a visor, sitting on the floor with her legs out like a child. She's holding a receipt.*", "i was first. i was a gold member. since 1999. i had my card out.", "i didn't look back. you're not supposed to look back. it's a sale."], opts: [["what's on the receipt?", "receipt"], ["you read the page.", "page"]] },
          receipt: { say: ["one emergency membership, gold. one shelter place. one bottle of water. and a page. folded in with it. the manager's page, off his clipboard. it fell. i picked it up. i read it while i waited.", "'members-only continuity. non-members to be treated as stock shrinkage.'", "stock shrinkage. that's what they called the people behind me. that's what they called milo."], next: "page" },
          page: { say: ["*She unfolds the receipt. Folded inside it is a page of thick paper with the Big Value logo and six signatures' worth of initials. It's sixty-one years soft.*", "can i return it? the day? i've got the receipt.", "*She holds the receipt and the page out to you. Her hand shakes.*"], opts: [["no. but i'll take the page.", "take"], ["i'm sorry. you can't return a day.", "sorry"]] },
          take: { say: ["*She lets go of it. She keeps the receipt.*", "i'll keep this. in case."], do: ["give:page_bigvalue", "flag:read_page_bigvalue"] },
          sorry: { say: ["*She nods, like she'd known for sixty-one years and needed someone at a desk to say it.*", "...no. you can't. i asked every day. nobody ever said no. they just said 'we're sorry for any inconvenience'.", "*she gives you the page. She keeps the receipt.*"], do: ["give:page_bigvalue", "flag:read_page_bigvalue", "flag:told_brenda_no"] },
        },
      },
      booth: {
        with: "gail", cam: "closeup",
        nodes: {
          start: { say: ["*The PA booth: a glass box over the dome, full of microphones, cassette tapes labelled by year, cold tea in a stack of mugs. A tiny old woman in a Big Value fleece sits with her hand on the switch.*", "*off-mic* you're the one from the machine. you've got her page.", "i was the assistant manager. on the day. the manager was on his break. head office rang. they said 'lock the doors at 17:31. members are in.' so i pressed it.", "i heard it from in here. through the glass. i've heard it every morning since."], opts: [["'we're sorry for any inconvenience.'", "sorry"], ["why are the doors still opening?", "doors"]] },
          sorry: { say: ["every morning. it's the only thing i was allowed to say. i've said it twenty-two thousand times. it doesn't take."], next: "doors" },
          doors: { say: ["because if the store closes, it was all for nothing. all of them. for nothing.", "*She looks out over the dome.* i keep it open so it meant something. that's stupid, isn't it. i know it's stupid."] },
        },
      },
      wall: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*Auntie pins page two in its frame. She reads 'stock shrinkage' out loud and then stops reading out loud.*", "they put the stampede in the plan.", "they knew there'd be people at the doors. they priced them.", "*she writes it in the notebook. Her crayon snaps.* ...that's two.", ["dale", "she's unlocking again, agnes."]] },
        },
      },
    },
    choices: [
      { id: "district_choice", prompt: "Gail has her hand on the switch. Wristband has a welding torch. Who runs the Checkout?", options: [
        { id: "deal", label: "DEAL: Big Value stays, and opens the vents", do: ["turf:checkout=bigvalue", "flag:checkout_deal", "flag:checkout_decided", "standing.corp:+5", "flag:pages_bigvalue"], consequence: "Gail keeps the store open and makes the Mall Rats a deal: free rations in the vents, no Security in the ducts. Big Value gives you 20% off and sends segways to the raid (shaky if Corp Standing is high). The doors still open at 09:00." },
        { id: "takeover", label: "TAKEOVER: the Mall Rats shut the doors for good", do: ["turf:checkout=mallrats", "flag:checkout_takeover", "flag:checkout_decided", "standing.bottom:+5", "standing.corp:-5", "flag:pages_bigvalue"], consequence: "Wristband welds the Big Doors shut. Gail makes her last announcement (\"attention shoppers. the store is closed. we're sorry. we're sorry. we're sorry.\") and switches the PA off. The Mall Rats run the Checkout: graffiti, rope bridges, free samples. They ride rocket carts in the raid. Big Value's Security turns hostile there." },
      ] },
    ],
    scenes: ["c8_doorbusters", "p6b_deal_or_takeover"],
    reward: { coupons: 800, items: ["page_bigvalue"], loot: ["lt_boss_cart_mother"], flags: ["beat_cart_mother"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. no refunds. one page.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you were run over by forty carts. one of them was yours." },
  },

  // ------------------------------------------------------------------ 12 (flashback F2)
  m12_workday_1645: {
    act: 2, n: 12, title: "THE LAST WORKDAY: 16:45", kind: "flashback", giver: "dale", district: "sims",
    locations: ["bottom:machine", "sims:spire_60", "sims:print_room"],
    cast: ["cale", "agnes", "hask", "dale"],
    requires: { missions: ["m09_workday_1600"], if: "pages>=2" },
    logline: "16:45 on the last workday. Copy the end of the world onto a tape drive that is very, very slow.",
    beats: [
      "Back in the sim. 16:43. Agnes gets you into the print room on 60. She keeps watch.",
      "The tape drive: an ancient ☺ CORP cartridge unit. The copy takes four minutes. A progress bar.",
      "Stealth while it copies: a Timekeeping officer does rounds of the floor; colleagues come in to print party invitations.",
      "Cale phones Hillside Primary on the print room phone. The school says the children are being walked to the nearest Big Value: 'it's a shelter, it's on the news, they'll be safe there'. Cale says to tell Mina they'll be there at half five.",
      "17:10: the tape finishes. Walking back past the executive lifts, Cale has to hide behind a pillar as Marion Hask, forty, steps out of a lift on a phone call: 'Half a percent. Thank you for letting me know. No. That will not change anything. Good afternoon.'",
      "Agnes: the lifts lock at 17:20. They'll take the stairs. Sixty floors.",
    ],
    reveals: {
      learn: ["Cale copied Option C onto a tape cartridge at about 17:10.", "Mina's school sent the children to Big Value. (You know what happened there.)", "Marion Hask was in the Spire, on a phone call about 'half a percent', at 17:10."],
      suspect: ["'Half a percent' means something. Hask knew something and launched anyway."],
      withheld: ["What the call was (Act III: Neville's memo; Act V: Hask)."],
    },
    steps: [
      { id: "load", text: "go back in", goal: { type: "interact", target: "bottom:machine" } },
      { id: "copy", text: "copy option c onto tape (don't get caught)", goal: { type: "survive", secs: 240 }, marker: "sims:print_room", notes: "stealth while the progress bar fills; getting seen by the officer restarts the copy (not a fail); colleagues can be talked to" },
      { id: "phone", text: "call the school", goal: { type: "talk", who: "cale", talk: "school" } },
      { id: "hask", text: "get back to agnes", goal: { type: "reach", zone: "sims:spire_60" }, talk: "half_a_percent" },
      { id: "out", text: "", goal: { type: "flag", flag: "f2_done" }, talk: "stairs_plan" },
    ],
    talks: {
      school: {
        with: "cale", cam: "closeup",
        nodes: {
          start: { say: ["*The print room phone is beige and has a cord you could hang washing on. You dial from memory.*", ["voice", "hillside primary, it's mrs. okafor."], "hi, it's rory cale, mina's, i'm mina's, i'm picking her up at half five, is she, is everything"], next: "school2" },
          school2: { say: [["voice", "oh, rory. there's sirens on the news, have you seen? they've said every big value is a shelter. we're walking the after-school club down to the big value on the high street. it's two minutes. they'll be safe there, it's on the news."]], opts: [["no. keep her at school. please.", "keep"], ["...ok. tell her i'm coming.", "tell"]] },
          keep: { say: [["voice", "rory, i can't keep one child behind when the whole town's going. it's on the news. it's a shelter."], ["voice", "i'll tell her you rang. i'll tell her half five."], "*the line goes to a dial tone. You hold the phone for a second too long.*"], do: ["flag:cale_tried_school"] },
          tell: { say: [["voice", "i'll tell her. half five. she's got her strawberry bag on, she's fine. don't run on the stairs, love."], "*dial tone.*"] },
        },
      },
      half_a_percent: {
        with: "hask", cam: "overShoulder",
        nodes: {
          start: { say: ["*17:10. You're walking back along the 60th floor with the tape cartridge in your jacket. The executive lift at the end of the corridor dings. You duck behind a pillar.*", "*A woman steps out: forty, tall, white suit, silver-blonde hair in a perfect knot, a phone to her ear. Two security officers behind her. She walks like the floor is her calendar.*", "Yes. I understand.", "Half a percent.", "Thank you for letting me know. No. That will not change anything.", "*She stops, three metres from your pillar, and checks her watch.*", "It is already priced in. Good afternoon.", "*She hangs up and walks on. She doesn't see you. Her heels are perfectly in time with the clock on the wall.*"], do: ["flag:saw_hask_1710"] },
        },
      },
      stairs_plan: {
        with: "agnes", cam: "closeup",
        nodes: {
          start: { say: ["*Agnes's office. She takes the cartridge, holds it to the light, and hands it straight back to you.*", "you've got it. good. keep it. you're faster.", "the lifts lock at 17:20 for the 'drill'. they're keeping everybody in the building until close of business. so it's the stairs.", "sixty floors. we'll make it by half five if we don't stop."], opts: [["that woman by the lifts. who was she?", "hask"], ["we won't stop.", "go"]] },
          hask: { say: ["marion hask. chief punctuality officer. she runs the schedule. she's the one they say will be ceo.", "*Agnes goes very still.* ...she's on the deck. her signature block. for ☺ corp.", "don't think about her. think about stairs."], next: "go" },
          go: { say: ["*She smiles at you, a quick, frightened, brilliant smile.*", "we won't stop. i'm right behind you, rory."] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 0, flags: ["f2_done"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. nobody saw you. you saw everything.", meets: "MEETS EXPECTATIONS. the tape's done.", see_me: "SEE ME. you printed forty party invitations by accident." },
  },

  // ------------------------------------------------------------------ 13 (overtime fight 2)
  m13_rush_hour: {
    act: 2, n: 13, title: "RUSH HOUR", kind: "main", giver: "gordo", district: "commute",
    locations: ["commute:spiral_freeway", "commute:ring_road"],
    cast: ["gordo", "overtime"],
    requires: { missions: ["m06_option_c"], if: "pages>=1" },
    logline: "On the Spiral Freeway, in a paper storm, Mr. Overtime chases your car on foot, at exactly the speed limit.",
    beats: [
      "Gordo needs a ride up the Spiral Freeway to the Number Works side of the hill (or back from it).",
      "C10: the paper storm, the mirror, Overtime running. 'please pull over. you're in breach of your schedule.'",
      "Boss fight: overtime_2, a chase. He staples dead cars into barricades, punches in through your windscreen, slams the road. Fight from the car (Gordo drives if you climb on the roof) and on the jam's car roofs.",
      "He gets left behind in the jams, tangled in a stapled bus. As you pass, you rip his lanyard off.",
      "He says something new, the first glitch: 'you were in the lobby. you were running. ...when was that?'",
      "Gordo, after: 'he doesn't know. does he. he doesn't know he's dead.'",
    ],
    reveals: {
      learn: ["Overtime's lanyard is ☺ CORP access (later: the Big Escalator, the Spire service doors).", "Overtime is starting to remember you."],
      suspect: ["Overtime is a recording, like you.", "He doesn't know the world ended."],
      withheld: ["That he killed Cale (F4).", "June (Act V)."],
    },
    steps: [
      { id: "car", text: "get gordo a car", goal: { type: "enterCar" } },
      { id: "storm", text: "drive up the spiral freeway", goal: { type: "reach", zone: "commute:spiral_freeway" }, scene: "c10_rush_hour" },
      { id: "chase", text: "lose mr. overtime", goal: { type: "killBoss", boss: "overtime_2" }, boss: "overtime_2" },
      { id: "lanyard", text: "", goal: { type: "pickup", item: "overtime_lanyard" }, talk: "when" },
      { id: "after", text: "", goal: { type: "talk", who: "gordo", talk: "dead" } },
    ],
    talks: {
      when: {
        with: "overtime", cam: "closeup",
        nodes: {
          start: { say: ["*Overtime, half under a bus he stapled himself to, steaming. As your car crawls past, you lean out and yank the lanyard off his neck. Ninety years of employee-of-the-month badges clatter.*", "that's... company property.", "*He looks at you, through the window, properly, for the first time.*", "you were in the lobby. you were running.", "...when was that?", "*His punch-clock heart skips. He looks down at it like it's someone else's.*"], do: ["flag:overtime_glitch_1"] },
        },
      },
      dead: {
        with: "gordo", cam: "overShoulder",
        nodes: {
          start: { say: ["*The jam, after. Gordo is very quiet, which is new.*", "he doesn't know. does he.", "he doesn't know he's dead. he doesn't know anybody's dead. he thinks we're all just... off sick.", "*He looks at the lanyard in your hand.*", "you're the same thing he is. you know that, right? a recording in a body. corp's recording."], opts: [["i know.", "know"], ["i'm not like him.", "not"], ["(cold) maybe he's the one who's got it right.", "cold", { if: "drift>=2" }]] },
          know: { say: ["*He nods.* ...good. good. just checking you checked."], do: ["standing.bottom:+1"] },
          not: { say: ["no. you're not. he's never once said 'i'm not like him'.", "that's the difference. keep saying it."], do: ["standing.bottom:+2"] },
          cold: { say: ["*Gordo looks at you for a long time. Then he strikes the match and lets it burn down to his fingers.*", "don't say that again in front of lumps."], do: ["drift:+1", "standing.bottom:-2", "flag:said_cold_overtime"] },
        },
      },
    },
    choices: [],
    scenes: ["c10_rush_hour"],
    reward: { coupons: 600, items: ["overtime_lanyard"], loot: ["lt_boss_overtime_2"], flags: ["beat_overtime_2"], standing: { corp: -5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you lost him. he was on time.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. he overtook you. on foot." },
  },

  // ------------------------------------------------------------------ 14 (number works 1/2)
  m14_price_of_everything: {
    act: 2, n: 14, title: "THE PRICE OF EVERYTHING", kind: "main", giver: "nell", district: "numberworks",
    locations: ["numberworks:yard", "numberworks:union_hall", "numberworks:press", "numberworks:smokestacks"],
    cast: ["nell", "foreman", "mr_sevens"],
    requires: { missions: ["m06_option_c"], if: null },
    logline: "Number Works prints the city's prices every morning at 06:00. The union stamped with the unwanted numbers wants a vote. Management wants a strike broken.",
    beats: [
      "The Number Yard: conveyors of giant numbers, smokestacks puffing digits, a shift of workers stamped 13, 0 and 0.5.",
      "Union Hall 13: Nell Thirteen and a vote on whether to let you speak (motion carried, 7-6).",
      "Nell: Remainder keeps its page in the Foreman's face. Remainder calculated the war, and every morning it calculates what the city can afford to eat.",
      "Mr. Sevens, upstairs at the Price Press, makes the other offer: break the strike tomorrow morning and he'll get the Foreman to 'show you his face'.",
      "Either way: the 06:00 print run. Either sabotage it for the union (a fair price list goes out) or keep it running for Sevens (strikers scatter). Fight through the press either way, with the Foreman watching from the Big Calculator.",
    ],
    reveals: {
      learn: ["Remainder Industries calculated the war: every target list, every casualty forecast.", "Prices in the city are printed by Remainder; whoever holds Number Works decides what bread costs."],
      suspect: ["Remainder knew something about Q4 nobody else did (Nell: 'ask management about the half'). "],
      withheld: ["The 0.5% (Act III).", "The 17:10 call (Act V)."],
    },
    steps: [
      { id: "yard", text: "find the union hall", goal: { type: "reach", zone: "numberworks:union_hall" } },
      { id: "vote", text: "address the union", goal: { type: "talk", who: "nell", talk: "motion" } },
      { id: "sevens", text: "", goal: { type: "talk", who: "mr_sevens", talk: "offer" }, marker: "numberworks:press" },
      { id: "print", text: "the 06:00 print run", goal: { type: "flag", flag: "print_run_done" }, marker: "numberworks:press", notes: "the print_run choice; either way, a fight through the Price Press as the presses stamp on a beat" },
    ],
    talks: {
      motion: {
        with: "nell", cam: "wide",
        nodes: {
          start: { say: ["*Union Hall 13: thirteen chairs, one person always standing (it's Nell). Workers with 13s, 0s and 0.5s stamped on their foreheads. A banner: WE ARE THE REMAINDER.*", "motion: the plastic person from the bottom gets five minutes. all in favour?", "*seven hands.*", "against?", "*six hands, one of them holding a sandwich.*", "motion carried. five minutes. go."], opts: [["i'm here for remainder's page of option c.", "page"], ["what do you want?", "want"]] },
          want: { say: ["to be counted. remainder stamps people with the numbers it doesn't want. thirteens. zeros. halves. we do the jobs that don't divide.", "we want a seat on the board, a vote on the prices, and for management to stop rounding our wages down."], next: "page" },
          page: { say: ["*A murmur.*", "the page is in the foreman. in his face. it's a calculator, his face. it stores things. he says it's the only safe place in the district.", "remainder calculated the war. every target list. every 'forecast'. and every morning at 06:00 it calculates what this city's allowed to eat. bread's 13 coupons today because the foreman's display says so.", "*she taps the 13 on her forehead* and ask management about the half. they never want to talk about the half."], opts: [["what half?", "half"], ["how do i get to the foreman?", "how"]] },
          half: { say: ["half a percent. it's an old joke on the floor. 'remainder's always half a percent out.' the old timers say it like it's the worst thing that ever happened. none of them will say why."], do: ["flag:heard_about_the_half"], next: "how" },
          how: { say: ["he comes down for the 06:00 print run. every morning. if the print run goes wrong, he comes down angry.", "help us print a fair list tomorrow. one morning of honest prices. he'll come down. we'll give you the floor."] },
        },
      },
      offer: {
        with: "mr_sevens", cam: "closeup",
        nodes: {
          start: { say: ["*The Price Press office: gold, clovers, rabbit's feet, a single piece of real wood on the desk that Mr. Sevens touches every few seconds. His Regrowth face is fixed in a jackpot grin.*", "seven's my number. thirteen's yours. no offence. *touches wood*", "you've been talking to the union. charming people. very... indivisible.", "here's a better deal. the union's planning to sabotage tomorrow's run. you keep the presses rolling, the strikers go home, and i'll have the foreman show you his face. page and all."], opts: [["why do you care what bread costs?", "bread"], ["what's the half?", "half", { if: "flag:heard_about_the_half" }], ["i'll think about it.", "think"]] },
          bread: { say: ["i don't. i care who decides. whoever prints the prices runs the market. whoever runs the market runs everything. touch wood."], next: "think" },
          half: { say: ["*For a quarter of a second the grin slips. He touches the wood twice.*", "a rounding error. a long time ago. everybody rounds.", "the offer's open till 06:00."], do: ["flag:sevens_flinched"] },
          think: { say: ["the market rewards decisiveness. touch wood."] },
        },
      },
    },
    choices: [
      { id: "print_run", prompt: "06:00. The presses start. The union wants a fair price list; Mr. Sevens wants the strike broken.", options: [
        { id: "union", label: "sabotage the run for the union", do: ["flag:print_run_done", "flag:helped_union", "standing.bottom:+3", "standing.corp:-3"], consequence: "For one morning every price tag in the city is fair (bread costs 2). People in the Bottom talk about it for weeks. The Foreman comes down angry, and the union holds the yard for your fight. Nell's TAKEOVER is easier in m15." },
        { id: "sevens", label: "keep the presses running for Mr. Sevens", do: ["flag:print_run_done", "flag:helped_sevens", "standing.corp:+3", "standing.bottom:-3"], consequence: "The strikers scatter; three are fined. The Foreman comes down calm and fights you in a cleared yard. Sevens' DEAL is easier in m15, and he likes you, which nobody else does." },
      ] },
    ],
    scenes: [],
    reward: { coupons: 400, loot: ["lt_district_numberworks"], flags: ["met_remainders"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you carried the one.", meets: "MEETS EXPECTATIONS. rounded to the nearest.", see_me: "SEE ME. you divided by zero." },
  },

  // ------------------------------------------------------------------ 15 (number works 2/2)
  m15_rounding_down: {
    act: 2, n: 15, title: "ROUNDING DOWN", kind: "main", giver: "nell", district: "numberworks",
    locations: ["numberworks:calculator", "numberworks:yard", "numberworks:pit"],
    cast: ["foreman", "nell", "mr_sevens"],
    requires: { missions: ["m14_price_of_everything"], if: null },
    logline: "Foreman Remainder comes down for the print run, and the page is in his face.",
    beats: [
      "Boss fight: FOREMAN REMAINDER on the conveyor yard and up the Big Calculator. He multiplies and divides.",
      "Beaten, his face flickers and shows one number before it dies: 4,112,006,551. You've seen it before, on slide 31.",
      "Inside the cracked display, folded small: Remainder's page. The forecast.",
      "He tells you he did the arithmetic on the forecast as a nine-year-old with a pencil because the computers were busy.",
      "P6b: DEAL with Mr. Sevens or TAKEOVER for the Remainders. If DEAL, Sevens hands you a sealed call log 'as insurance'.",
    ],
    reveals: {
      learn: ["Remainder page: 'the forecast': target lists, casualty estimates, the orbital billboards used as missile guidance.", "4,112,006,551: the forecast was the number of people who'd die."],
      suspect: ["Remainder phoned someone at 17:10 (if you take the DEAL, you hold the log)."],
      withheld: ["What was said on the call (Act V)."],
    },
    steps: [
      { id: "boss", text: "stop foreman remainder", goal: { type: "killBoss", boss: "foreman" }, boss: "foreman", marker: "numberworks:yard" },
      { id: "face", text: "", goal: { type: "talk", who: "foreman", talk: "face" } },
      { id: "choice", text: "decide who runs number works", goal: { type: "flag", flag: "numberworks_decided" }, scene: "p6b_deal_or_takeover" },
      { id: "home", text: "take the page to auntie", goal: { type: "deliver", item: "page_remainder", zone: "bottom:lostfound" }, talk: "wall" },
    ],
    talks: {
      face: {
        with: "foreman", cam: "closeup",
        nodes: {
          start: { say: ["*The Foreman on his back at the bottom of the Remainder Pit, crane arms limp. His calculator face is cracked. The green digits flicker: 13. 7. 0.5. Then, steady:*", "*4,112,006,551.*", "that's the forecast. that's the one i did.", "i was nine. my mum cleaned the forecasting floor. the computers were busy. a man in a nice suit gave me a pencil and a sheet and said 'add these up, son, there's a sweet in it'.", "i added them up. i got the sweet."], opts: [["you were a child.", "child"], ["give me the page.", "page"]] },
          child: { say: ["i was a calculator. that's what they made me. that's what i made me.", "*his display flickers 0.* it adds up. it always adds up. that's what's wrong with it."], next: "page" },
          page: { say: ["*A panel in his face springs open. Folded inside, very small, a page with Remainder's crest: THE FORECAST. The same number, in pencil, in a child's handwriting, in the margin.*", "take it. i've been carrying it long enough. carries the one."], do: ["give:page_remainder", "flag:read_page_remainder"] },
        },
      },
      wall: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*Auntie pins page three. She looks at the number in the margin, the child's handwriting, for a long time.*", "four billion, one hundred and twelve million, six thousand, five hundred and fifty-one.", "*she doesn't need to read it. She says it like a phone number she's known all her life.*", "...that's three.", ["dale", "agnes. she's opening the last one but one. you should be here for it."], "*Auntie closes the notebook.* no. i shouldn't."] },
        },
      },
    },
    choices: [
      { id: "district_choice", prompt: "Mr. Sevens has a contract and a rabbit's foot. Nell has a megaphone and a motion. Who runs Number Works?", options: [
        { id: "deal", label: "DEAL: Remainder stays, and owes you", do: ["turf:numberworks=remainder", "flag:numberworks_deal", "flag:numberworks_decided", "standing.corp:+5", "flag:pages_remainder", "give:sevens_call_log"], consequence: "Prices stay Remainder's, but the Bottom's bread is frozen at 3. Sevens hands you a sealed envelope 'as insurance against our mutual friend at the top': the 17:10 call log (time and duration only; it matters in Act V). Remainder sends forklift tanks to the raid, shakily." },
        { id: "takeover", label: "TAKEOVER: the Remainders run Number Works", do: ["turf:numberworks=remainders", "flag:numberworks_takeover", "flag:numberworks_decided", "standing.bottom:+5", "standing.corp:-5", "flag:pages_remainder"], consequence: "Motion carried. The union runs the Price Press by vote: prices drop, meetings are long. The Remainders march in the raid. Sevens flees to Corp Hill; in the press office he leaves behind his piece of wood, and the 17:10 log is in the drawer under it (found in Act IV instead)." },
      ] },
    ],
    scenes: ["p6b_deal_or_takeover"],
    reward: { coupons: 800, items: ["page_remainder"], loot: ["lt_boss_foreman"], flags: ["beat_foreman"], standing: { bottom: 5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. it added up.", meets: "MEETS EXPECTATIONS. carried the one.", see_me: "SEE ME. you were rounded down." },
  },

  // ------------------------------------------------------------------ 16 (flashback F3)
  m16_workday_1720: {
    act: 2, n: 16, title: "THE LAST WORKDAY: 17:20", kind: "flashback", giver: "dale", district: "sims",
    locations: ["bottom:machine", "sims:stairwell"],
    cast: ["cale", "agnes", "dale"],
    requires: { missions: ["m12_workday_1645"], if: "pages>=3" },
    logline: "Sixty floors of Stairwell B at 17:20, with the sirens going and the clocks starting to crack.",
    beats: [
      "17:20: the lifts lock. The sirens start. Cale and Agnes go into Stairwell B.",
      "A descent level: floors counting down, staff panicking on landings, Timekeeping officers locking floor doors, a man carrying a fish tank, the clocks on every landing cracking from the middle out (the Schedule Bomb warming up downtown).",
      "Cale talks to themselves on the stairs. Agnes keeps up, then lags.",
      "The 41st-floor landing. Agnes sits down. 'go. i'll... go.' The player has to choose: try to pull her, or go.",
      "Either way Cale goes on alone. The flashback ends at floor 1, 17:28, the fire door to the lobby.",
    ],
    reveals: {
      learn: ["Agnes stopped on the 41st floor, and Cale went on alone."],
      suspect: ["Auntie is Agnes. She let Cale go. (Most players know now.)"],
      withheld: ["Cale's death (F4)."],
    },
    steps: [
      { id: "load", text: "go back in", goal: { type: "interact", target: "bottom:machine" } },
      { id: "down", text: "get down sixty floors before 17:30", goal: { type: "reach", zone: "sims:stairwell" }, timer: 480, talk: "stairs", notes: "the timer can't fail: at 0 the scene still runs; it just makes you run" },
      { id: "41", text: "", goal: { type: "talk", who: "agnes", talk: "landing" } },
      { id: "out", text: "", goal: { type: "flag", flag: "f3_done" } },
    ],
    talks: {
      stairs: {
        with: "cale",
        nodes: {
          start: { say: ["*Barks as Cale runs, one per few floors (the builder plays them on landing triggers):*", "sixty. fifty-nine. ok. ok, ok, ok.", "forty-one floors. you can do forty-one floors. you did forty-one floors this morning. in the lift. it counts.", ["agnes", "keep going. i'm right behind you."], "sorry! sorry. excuse me. end of the world, sorry.", ["voice", "*a man with a fish tank* i couldn't leave him!"], "mina. i'm coming. i'm coming. i'm coming.", "*every clock on every landing has a crack across the middle, getting longer.*"] },
        },
      },
      landing: {
        with: "agnes", cam: "closeup",
        nodes: {
          start: { say: ["*The 41st-floor landing. Agnes is a flight behind you. Then she isn't coming. She's sitting on the top step, her glasses in her hand, breathing in a way that isn't about the stairs.*", "rory. rory, i can't. i can't do the next bit.", "my legs won't. it's not my legs."], opts: [["*go back up and pull her*", "pull"], ["agnes, come on. please. it's twenty floors.", "please"], ["*keep going*", "go"]] },
          pull: { say: ["*You climb back. You take her arm. She lets you pull her up one step, and then she sits back down.*", "no. no. you're faster. it's logistics. it's always been logistics.", "*she pushes the cartridge back into your hand, closes your fingers over it.*"], next: "last" },
          please: { say: ["*She looks at you, and for a second she nearly gets up.*", "twenty floors. i know. i know how many floors it is. i count things."], next: "last" },
          go: { say: ["*You take one step down. You look back.*"], next: "last" },
          last: { say: ["go. go. i'll... go.", "i'm right behind you.", "*She isn't. You both know. You go.*"], do: ["flag:f3_done"] },
        },
      },
    },
    choices: [],
    scenes: [],
    reward: { coupons: 0, flags: ["f3_done"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "no performance-review card after F3: the screen just shows 17:28 and fades. It's the only mission with no grade.",
  },

  // ------------------------------------------------------------------ 17 (F4 + the confession)
  m17_minutes: {
    act: 2, n: 17, title: "MINUTES OF THE MEETING", kind: "main", giver: "dale", district: "bottom",
    locations: ["bottom:machine", "sims:lobby", "bottom:lostfound"],
    cast: ["cale", "overtime", "auntie", "dale"],
    requires: { missions: ["m16_workday_1720", "m13_rush_hour"], if: null },
    logline: "17:29. Cale reaches the lobby with the copy, and Mr. Overtime is waiting. Then Auntie tells you the truth.",
    beats: [
      "Dale: one more. She's been holding it back. It's the last few minutes.",
      "F4: the lobby, 17:28. Playable until the middle of the floor. Overtime steps out. 'you're running. that's against policy.' 17:29:41. Black. The clock counts to 17:30:00. BEEP.",
      "You come out of the Machine. Dale is crying and doesn't hide it.",
      "C11: Auntie at the long table. 'i was your boss.' Everything: the printer queue, the stairs, the 41st floor. 'your name's rory. rory cale.' Mina.",
      "Choice: forgive her, or don't, or say you can't yet.",
      "Act II ends.",
    ],
    reveals: {
      learn: ["Mr. Overtime killed Cale in the lobby at 17:29:41 by punching their card: a termination.", "Auntie is Agnes Pell. She sent Cale down the stairs and stopped.", "Your name is Rory Cale. You had a sister, Mina."],
      suspect: ["Being 'terminated' at 17:29 is why the Machine couldn't hold you (Act III makes this concrete).", "The tape: where did the copy go?"],
      withheld: ["What ☺ CORP is planning (Act III).", "The tape cartridge was taken by Overtime into the Spire (he keeps it on his desk; Act IV)."],
    },
    steps: [
      { id: "load", text: "go back in, one last time", goal: { type: "talk", who: "dale", talk: "last_one" }, marker: "bottom:machine" },
      { id: "f4", text: "get out of the building", goal: { type: "flag", flag: "seen_f4" }, scene: "f4_1729" },
      { id: "out", text: "", goal: { type: "talk", who: "dale", talk: "after_f4" } },
      { id: "c11", text: "auntie's waiting", goal: { type: "flag", flag: "seen_c11" }, scene: "c11_minutes", marker: "bottom:lostfound" },
      { id: "end", text: "", goal: { type: "talk", who: "auntie", talk: "after_c11" }, do: ["flag:act2_done"] },
    ],
    talks: {
      last_one: {
        with: "dale",
        nodes: {
          start: { say: ["*Dale has the panel open. He doesn't look at you.*", "there's one more. a few minutes. she's been holding it back. i think she didn't want to show you.", "she doesn't want to do a lot of things. she does them anyway. like me."], opts: [["*lean on the glass*", "go"], ["do you know what's on it?", "know"]] },
          know: { say: ["*long pause*", "i can guess. i've had sixty-one years to guess."], next: "go" },
          go: { say: ["*The glass. The cold. The hum. White.*"] },
        },
      },
      after_f4: {
        with: "dale", cam: "closeup",
        nodes: {
          start: { say: ["*You're on the floor of the Lost & Found. You don't remember falling. Dale is sitting next to you with his back against the Machine. He's crying and he isn't hiding it.*", "...17:30. i was in the basement. i was fixing her. at 17:30 she went BEEP. the only time she's ever been on time.", "i didn't know what it was. i know now."], opts: [["he killed me.", "killed"], ["*say nothing*", "silent"]] },
          killed: { say: ["he did. and then she backed you up. and then he forgot. and now you're here.", "*he wipes his face with an oily rag, which makes it worse.* go on. she's waiting for you. she's been waiting a lot longer than me."] },
          silent: { say: ["*He puts a hand on your shoulder. It's very heavy and very gentle.*", "go on. she's waiting for you."] },
        },
      },
      after_c11: {
        with: "auntie", cam: "closeup",
        nodes: {
          start: { say: ["*After the choice. The rain's stopped. Auntie writes something in the notebook in crayon, closes it, and puts both hands flat on top of it.*"], opts: [["what now?", "now"]] },
          now: { say: ["now?", "*she looks at the three pages on the wall.*", "now we find out what they're doing with the ones like you. because ☺ corp didn't put that backup clause in for continuity, rory. corp doesn't do anything for continuity.", "they kept the dead for a reason.", "*If you forgave her:* go to bed. ...thank you.", "*If you didn't:* go to bed. i'll be here. i'm always here. that's the problem."] },
        },
      },
    },
    choices: [
      { id: "forgive_auntie", prompt: "\"i don't want you to say anything nice. i want it written down.\"", options: [
        { id: "forgive", label: "you didn't kill me. he did. i forgive you.", do: ["flag:forgave_auntie", "standing.bottom:+5", "drift:-1"], consequence: "Auntie writes it down: 'forgiven. 1 entry.' She cries for the first time anyone's seen. In the Spire lobby in Act IV her last line is 'thank you for the stairs, rory. i'd have done them for you.' It also brings a Cale memory flash back if Drift had stopped them." },
        { id: "blame", label: "you sent me down there. you sat down.", do: ["flag:blamed_auntie"], consequence: "Auntie writes it down: 'not forgiven. correct.' She thanks you for being honest and means it. In the lobby in Act IV her last line is 'it balances now. go on.'" },
        { id: "cant", label: "i don't remember enough to forgive you. ask me again.", do: ["flag:deferred_forgiveness"], consequence: "Auntie writes: 'pending.' You can forgive her later (a dialogue option at the Lost & Found in Act III, before m24). If you never do, her last line is 'pending. that's all right. that's fair. i'll take pending.'" },
        { id: "cold", label: "(cold) it doesn't matter. he'd have stopped either of us.", if: "drift>=3", do: ["flag:cold_to_auntie", "drift:+1"], consequence: "Auntie looks at you like she's looking at a stranger, which she is. She writes nothing. Her last line in the lobby is 'you sound like them. i'm sorry. that's on me too.'" },
      ] },
    ],
    scenes: ["f4_1729", "c11_minutes"],
    reward: { coupons: 0, flags: ["act2_done", "knows_auntie_secret"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "no performance-review card. The act card: END OF ACT II.",
  },
};
