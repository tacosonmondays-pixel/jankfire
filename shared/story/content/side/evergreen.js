// OVERDUE side questlines: EVERGREEN ACRES. Schema: see side/bottom.js.

export const SIDE_EVERGREEN = {
  sq_evergreen_lawn_order: {
    kind: "side", from: 3, title: "LAWN ORDER", giver: "linda", district: "evergreen",
    locations: ["evergreen:culdesac", "evergreen:pumpkin"], cast: ["linda"],
    requires: { missions: ["m21_property_values"], if: null },
    logline: "Mow 50 lawns with the Lawn Mower, perfectly. The HOA measures each one to the millimetre.",
    mechanic: { uses: ["fire", "cars"], hook: "mow fifty lawns to the millimetre" },
    twist: "Lawn 50 belongs to the Prize Pumpkin, which has won every year because it's the only entry. Linda asks you not to mow too close to it. It's grown over the shelter's old air vent, and the pumpkin is the only thing on the street that came up from the shelter with them. Linda planted it at eleven. It's sixty years old, enormous, and very slightly alive.",
    beats: ["50 lawns, each with a target height in mm (the Lawn Mower legendary or any autoshot works; other weapons scorch).", "Mannequin families wave at you while you mow.", "The Pumpkin."],
    steps: [
      { id: "mow", text: "mow 50 lawns to regulation", goal: { type: "interact", target: "evergreen:culdesac" } },
      { id: "pumpkin", text: "the prize pumpkin's lawn", goal: { type: "talk", who: "linda", talk: "pumpkin" }, marker: "evergreen:pumpkin" },
    ],
    talks: {
      pumpkin: { with: "linda", nodes: { start: { say: ["*Linda, by a pumpkin the size of a car, with a rosette on it that's sixty years of rosettes stapled together.*", "not too close, please. that's not in the bylaws. that's... me asking.", "i planted it the day we came up. i was eleven. it was the only seed in the shelter. it's never lost.", "*she pats it. It's warm.*"] } } },
    },
    choices: [],
    reward: { coupons: 700, loot: ["keep_off_the_grass"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. 0 mm deviation.", meets: "MEETS EXPECTATIONS. 2 mm. you've been fined.", see_me: "SEE ME. you mowed a dog." },
  },

  sq_evergreen_block_party: {
    kind: "side", from: 3, title: "BLOCK PARTY", giver: "linda", district: "evergreen",
    locations: ["evergreen:culdesac", "evergreen:clubhouse"], cast: ["linda"],
    requires: { missions: ["m21_property_values"], if: null },
    logline: "Evergreen is having a block party. Attendance is compulsory. Survive it.",
    mechanic: { uses: ["chicken_strike", "frag_smoke"], hook: "a wave survival block party with a three-legged race" },
    twist: "It's a survival wave mode with BBQ dads, a bouncy castle that's a trap, a three-legged race (you and a mannequin tied together) and a talent show. The last act of the talent show is the pilot families singing in perfect harmony, a song from before the war, and if you left them plugged in, Linda's dad sings the lead. She mouths along. It's beautiful and it's horrible and it's both on purpose.",
    beats: ["Waves of compulsory fun.", "The talent show."],
    steps: [ { id: "party", text: "survive the block party", goal: { type: "survive", secs: 600 }, marker: "evergreen:culdesac" } ],
    talks: {},
    choices: [],
    reward: { coupons: 600, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you won the three-legged race. with a mannequin.", meets: "MEETS EXPECTATIONS. you attended.", see_me: "SEE ME. you left early. it's been noted." },
  },

  sq_evergreen_keeping_up: {
    kind: "side", from: 3, title: "KEEPING UP", giver: "linda", district: "evergreen",
    locations: ["evergreen:culdesac"], cast: ["linda"],
    requires: { missions: ["m21_property_values"], if: null },
    logline: "Evergreen's safehouse comes with a rule: you need the same car as the neighbours, or they call Late Fees on you.",
    mechanic: { uses: ["cars"], hook: "steal the right blue car from the Unpaid" },
    twist: "The neighbours' car is a pastel-blue estate that hasn't been made in sixty-one years. The only one left outside Evergreen is in the Unpaid's camp, as their 'company car'. Stealing it is a heist; trading for it costs you an internship. When you park it on the drive, the mannequin family next door waves, and for one frame its wave is out of sync.",
    beats: ["The safehouse's welcome pack: a bylaw.", "Find the car.", "Park it."],
    steps: [
      { id: "car", text: "get a car like the neighbours'", goal: { type: "enterCar" }, marker: "commute:unpaid_camp" },
      { id: "park", text: "park it on the drive", goal: { type: "reach", zone: "evergreen:culdesac" } },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 300, flags: ["evergreen_safehouse"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you blend in.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. it's the wrong blue." },
  },

  sq_evergreen_return_address: {
    kind: "side", from: 3, title: "RETURN ADDRESS", giver: "mailman", district: "evergreen",
    locations: ["evergreen:culdesac", "bottom:long_stairs", "commute:gary_crater", "lates:remainder_office"], cast: ["mailman", "gary", "pauline"],
    requires: { missions: ["m21_property_values"], if: null },
    logline: "Evergreen's mailman never stops walking. His satchel is full of letters posted on the Final Quarter that were never delivered.",
    mechanic: { uses: ["cars", "grapple"], hook: "follow the mailman at 4 km/h; the last letter is up the ruins by the Long Stairs" },
    twist: "One of them is addressed to MRS. JUNE SALLOW, 14 HILLSIDE ROAD. Hillside Road collapsed into the Bottom; number 14 is a ruin by the Long Stairs, and in it, on a dead hallway table, an answering machine still holds one message, 17:30:00 on the Final Quarter. It's the last of Overtime's six memory fragments: 'i'm here. i'm on my way, june.' The letter in your hand is a card from Edwin to June, posted at lunch: 'happy forty. i'll be on time. E.'",
    beats: ["Follow the mailman (he never stops; you read the envelopes as he walks).", "Deliver six letters to whoever's left: one to Gary (his own handwriting, a memo to himself), one to Pauline in the Lates (from her mother: she reads it 22,000 days late), others.", "The last: Mrs. June Sallow.", "14 Hillside Road. The answering machine."],
    steps: [
      { id: "follow", text: "keep up with the mailman", goal: { type: "escort", who: "mailman", zone: "evergreen:culdesac" } },
      { id: "deliver", text: "deliver the final quarter's letters", goal: { type: "deliver", item: "fq_letter", zone: "commute:gary_crater" } },
      { id: "june", text: "the letter for mrs. june sallow", goal: { type: "interact", target: "bottom:long_stairs" }, do: ["collect:ot_1730"], talk: "machine" },
    ],
    talks: {
      machine: { with: "june", cam: "closeup", nodes: { start: { say: ["*14 Hillside Road: a ruin, half a hallway, a table, a beige answering machine with a red light that has been blinking for sixty-one years on a battery somebody kept changing. (Dale? You'll never know.)*", "*You press play.*", ["voice", "*a man's voice, a lobby echo behind it* june, it's ed. i'm, i'm here. it's 17:30. i'm on my way."], "*June's own outgoing message, warm, wry:* \"ed. it's half five. the stew won't wait and neither will i.\"", "*The message ends. You have the end of Edwin Sallow's shift.*"] } } },
    },
    choices: [],
    reward: { coupons: 500, standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. all delivered.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you read them all first. it's a crime." },
  },
};
