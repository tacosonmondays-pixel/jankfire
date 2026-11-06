// OVERDUE side questlines: PINSTRIPE. Schema: see side/bottom.js.

export const SIDE_PINSTRIPE = {
  sq_pinstripe_two_jesters: {
    kind: "side", from: 2, title: "TWO JESTERS", giver: "pip", district: "pinstripe",
    locations: ["pinstripe:clown_cellar", "pinstripe:restaurant", "pinstripe:bocce_pit", "pinstripe:sauce_works"], cast: ["pip", "larry", "don", "nonna"],
    requires: { missions: ["m07_an_offer"], if: null },
    logline: "Pip and Long Larry want you to prank the Family until it falls apart. Every prank is a weapon gimmick.",
    twist: "Larry writes every prank, Pip takes the credit, and the last prank is Larry's idea alone: he wants the Don, just once, to laugh at one of his jokes. In the last part it's Nonna who laughs. Up in the rafters, out loud, for the first time anyone can remember. Larry cries for an hour.",
    beats: ["Prank 1: banana-peel the Bocce Pit before a 'settlement' (Peel Shooter). The goons slip; the dispute is settled by slapstick.", "Prank 2: marbles in the Sauce Works (Marble Shotgun): the red river carries goons into the vats.", "Prank 3: the Party Popper in the restaurant's dessert trolley.", "Part 2 (after m08): Larry's joke. Set it up across the Villa with the Bubble Wand, a Rubber Duck and a meatball. The joke is very long. The punchline is a man walking into a bar."],
    steps: [
      { id: "cellar", text: "join the punchlines in the green room", goal: { type: "talk", who: "pip", talk: "pranks" }, marker: "pinstripe:clown_cellar" },
      { id: "p1", text: "peel the bocce pit", goal: { type: "interact", target: "pinstripe:bocce_pit" } },
      { id: "p2", text: "marble the sauce works", goal: { type: "interact", target: "pinstripe:sauce_works" } },
      { id: "p3", text: "pop the dessert trolley", goal: { type: "interact", target: "pinstripe:restaurant" } },
    ],
    parts: [
      { id: "larrys_joke", title: "LARRY'S JOKE", if: "done:m08_family_business", do: ["flag:nonna_laughed"],
        steps: [
          { id: "setup", text: "set up larry's joke across the villa", goal: { type: "interact", target: "pinstripe:villa" } },
          { id: "punch", text: "", goal: { type: "talk", who: "larry", talk: "punchline" } },
        ] },
    ],
    talks: {
      pranks: { with: "pip", nodes: { start: { say: ["darling! the merchandise! we're doing pranks. pranks are like gunfights with better timing.", ["larry", "i wrote them."], "LARRY wrote them. i perform them. it's a partnership. like a horse. i'm the front.", ["larry", "i'm the long bit."]] } } },
      punchline: { with: "larry", cam: "closeup", nodes: { start: { say: ["*The joke runs across the whole Villa: a bubble, a duck, a meatball, a chandelier, a goon. Everyone in the house watches. It ends with a man walking into a metal bar.*", "...he's hurt. that's the joke.", "*silence. Then, from the rafters, high and cracked and real: an old woman laughing.*", "*Larry looks up. His droopy nose shakes. He sits down on the marble floor and cries for a long time, and Pip sits next to him and, for once, doesn't say anything.*"] } } },
    },
    choices: [],
    reward: { coupons: 700, loot: ["lt_district_pinstripe"], standing: { bottom: 3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. ha.", meets: "MEETS EXPECTATIONS. ha ha.", see_me: "SEE ME. you explained the joke." },
  },

  sq_pinstripe_wet_work: {
    kind: "side", from: 2, title: "WET WORK", giver: "nonna", district: "pinstripe",
    locations: ["pinstripe:villa", "pinstripe:respect_bridge", "pinstripe:restaurant"], cast: ["nonna"],
    requires: { missions: ["m07_an_offer"], if: null },
    logline: "The Family needs some wet work done. Deliver the laundry. Actual laundry. They're very clean.",
    twist: "The laundry is the Don's: shirts, a hundred of them, every one with the same grin stain on the collar. Nonna has been washing her dead son's shirts every week for fifty years. The last basket has a note pinned to it for whoever did the delivery: 'thank you. he always liked them crisp.'",
    beats: ["A laundry basket that must arrive dry, uncreased and on time to five addresses (it's a driving delivery with a crease meter).", "Goons try to 'help' and drop it.", "The note."],
    steps: [
      { id: "basket", text: "pick up the family's laundry", goal: { type: "pickup", item: "family_laundry" }, marker: "pinstripe:villa" },
      { id: "deliver", text: "deliver it crisp", goal: { type: "deliver", item: "family_laundry", zone: "pinstripe:restaurant" }, timer: 300, notes: "a crease meter like the Sauce Run's slosh meter" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 400, standing: { corp: 1 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. crisp.", meets: "MEETS EXPECTATIONS. damp.", see_me: "SEE ME. you wore one." },
  },

  sq_pinstripe_claims_department: {
    kind: "side", from: 2, title: "CLAIMS DEPARTMENT", giver: null, district: "pinstripe",
    locations: ["pinstripe:claims"], cast: ["nonna"],
    requires: { missions: ["m07_an_offer"], if: null },
    logline: "Help survivors file claims on their apocalypse cover. Every claim is denied. Every denial is a gunfight.",
    twist: "After eight denials the ninth claimant is a little old man whose claim is for a single cat, lost on the Final Quarter. It's denied (act of shareholders). You can take it to Nonna in person. If you hold the Fazzoletti page, she reads it, looks at it for a long time, and approves it: the only claim the Family has ever paid. It pays 3 coupons. He frames it.",
    beats: ["The Claims Office queue. Each claim: a survivor, a policy, a reason for denial (act of shareholders, act of god, act of god's shareholders, 'you didn't read clause 9', 'clause 9 is blank').", "Each denial sends adjusters with tiny hands and big guns.", "The ninth claim."],
    steps: [
      { id: "claims", text: "help 8 survivors file their claims", goal: { type: "kill", who: "any", n: 8 } },
      { id: "cat", text: "the ninth claim", goal: { type: "talk", who: "nonna", talk: "approve" }, if: "has:page_family" },
    ],
    talks: {
      approve: { with: "nonna", cam: "closeup", nodes: { start: { say: ["*Nonna, in her nest, reads the little old man's claim. One cat, ginger, called Pickle, lost at 17:30 on the Final Quarter.*", "act of shareholders.", "*she looks at the page in your hand, the page with her signature on it.*", "...approved.", "*she stamps it. The stamp says APPROVED; it has never been used; the ink is dry. She licks it.* three coupons. the family pays nothing. the family has paid three coupons. don't tell anyone."], do: ["flag:first_claim_paid"] } } },
    },
    choices: [],
    reward: { coupons: 500, standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. a claim was paid. historians are confused.", meets: "MEETS EXPECTATIONS. claims denied. adjusters adjusted.", see_me: "SEE ME. you filed a claim on yourself." },
  },

  sq_pinstripe_meatball_run: {
    kind: "side", from: 2, title: "THE MEATBALL RUN", giver: null, district: "pinstripe",
    locations: ["pinstripe:respect_bridge", "pinstripe:restaurant"], cast: [],
    requires: { missions: ["m07_an_offer"], if: null },
    logline: "A meatball the size of a car got loose on Respect Bridge. Roll it home to Mamma Polizza's.",
    twist: "The meatball is Mamma Polizza's sixty-year-old sourdough-style 'mother meatball', from which every meatball in Pinstripe has been made. If it rolls into the river, Pinstripe's cuisine ends. The goons are weeping openly. A goon tells you the recipe in exchange (a secret implant clue: 'the secret ingredient is a knuckle').",
    beats: ["It's rolling. Downhill. Toward the river.", "Push it with knockback, block it with cars, lasso it (it drags you).", "Get it up the restaurant's stairs."],
    steps: [
      { id: "roll", text: "roll the meatball home", goal: { type: "escort", who: "goon", zone: "pinstripe:restaurant" }, notes: "a physics escort; the meatball is the 'who'" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 350, flags: ["knows_knuckle_clue"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. not a crumb lost.", meets: "MEETS EXPECTATIONS. a bit of gravel.", see_me: "SEE ME. it's in the river. pinstripe is in mourning." },
  },
};
