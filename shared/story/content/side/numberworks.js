// OVERDUE side questlines: NUMBER WORKS. Schema: see side/bottom.js.

export const SIDE_NUMBERWORKS = {
  sq_numberworks_carry_the_one: {
    kind: "side", from: 2, title: "CARRY THE ONE", giver: "nell", district: "numberworks",
    locations: ["numberworks:yard", "numberworks:prime_lane", "numberworks:calculator"], cast: ["nell"],
    requires: { missions: ["m14_price_of_everything"], if: null },
    logline: "Escort a giant 1 across Number Works. Everybody wants it: you can't carry anything without one.",
    mechanic: { uses: ["bounce_shots", "cars"], hook: "escort a giant 1; the union banks tennis balls off digits" },
    twist: "Halfway, the 1 gets a 3 attached to it by Remainder's 'rounding' crews and becomes a 13, and the union refuses to touch an unlucky number. Nell holds a vote, mid-ambush, on whether a 13 is still a 1 with friends. It passes 7-6. You carry the 13.",
    beats: ["A building-sized 1 on a flatbed, from the Smokestacks to the Big Calculator.", "Ambushes by rounding crews.", "The vote."],
    steps: [
      { id: "escort", text: "carry the one to the big calculator", goal: { type: "escort", who: "nell", zone: "numberworks:calculator" }, talk: "vote" },
    ],
    talks: {
      vote: { with: "nell", nodes: { start: { say: ["*mid-firefight, through the megaphone* motion: a thirteen is just a one with friends. all in favour?", "*seven hands, some of them holding guns.*", "against?", "*six hands.*", "motion carried. KEEP CARRYING."] } } },
    },
    choices: [],
    reward: { coupons: 450, loot: ["lt_district_numberworks"], standing: { bottom: 2 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. carried.", meets: "MEETS EXPECTATIONS. carried, mostly.", see_me: "SEE ME. you dropped the one. now it's a zero." },
  },

  sq_numberworks_rounding_error: {
    kind: "side", from: 2, title: "ROUNDING ERROR", giver: "nell", district: "numberworks",
    locations: ["numberworks:archive", "numberworks:pit", "numberworks:press"], cast: ["nell", "mr_sevens", "foreman"],
    requires: { missions: ["m14_price_of_everything"], if: null },
    logline: "Someone's been stealing halves. Every worker's wage has been rounded down by 0.5 coupons for sixty-one years. Find out who.",
    mechanic: { uses: ["camera"], hook: "a stakeout in the Remainder Pit" },
    twist: "It's the Price Press itself: Remainder's oldest program, still running the rule it was given on the Final Quarter: 'round all outstanding values down by 0.5 until the books balance'. The books will never balance, because the 0.5 it's trying to make up is the 0.5% Q4 revision that came in that morning and was ignored. In the Forecast Archive you find the original rule card, with a note from the 09:00 forecasting team: 'we hit it. tell the board.' (A clue toward the Act III memo, and a Cale memory flash if Drift is low: Agnes saying 'remainder's always half a percent out.')",
    beats: ["Payslips from union members: every one 0.5 short.", "A stakeout in the Remainder Pit (where leftover numbers go): a conveyor of halves going into the Price Press.", "The Forecast Archive: spools of paper, a rule card.", "Choice: turn the rule off (wages go up 0.5; Remainder notices) or leave it and take the card to Mr. Sevens (he pays you to keep quiet)."],
    steps: [
      { id: "payslips", text: "check the payslips", goal: { type: "talk", who: "nell", talk: "half" }, marker: "numberworks:union_hall" },
      { id: "pit", text: "stake out the remainder pit", goal: { type: "survive", secs: 120 }, marker: "numberworks:pit" },
      { id: "archive", text: "follow the halves to the archive", goal: { type: "pickup", item: "rule_card" }, marker: "numberworks:archive" },
      { id: "choice", text: "the rule", goal: { type: "flag", flag: "rounding_choice_made" } },
    ],
    talks: {
      half: { with: "nell", nodes: { start: { say: ["*Nell slaps a stack of payslips on the table.* every one. half a coupon short. every week. sixty-one years.", "management calls it rounding. we call it theft. find out where the halves go."] } } },
    },
    choices: [
      { id: "rule", prompt: "The rule card: 'ROUND ALL OUTSTANDING VALUES DOWN BY 0.5 UNTIL THE BOOKS BALANCE.' And a note: 'we hit it. tell the board.'", options: [
        { id: "off", label: "turn the rule off", do: ["flag:rounding_choice_made", "flag:rounding_fixed", "standing.bottom:+4", "standing.corp:-2"], consequence: "Wages go up by 0.5 coupons. The union throws you a party with exactly 13 balloons. Mr. Sevens touches wood very hard." },
        { id: "sell", label: "sell the card to mr. sevens", do: ["flag:rounding_choice_made", "flag:rounding_sold", "coupons:+1500", "standing.corp:+3", "standing.bottom:-4"], consequence: "He pays 1,500 coupons and burns the card on his one piece of real wood. The halves keep going. (He keeps a copy of the note, for luck; it turns up in his call-log envelope if you DEAL in m15.)" },
      ] },
    ],
    reward: { coupons: 400, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. it balances. a bit.", meets: "MEETS EXPECTATIONS. rounded.", see_me: "SEE ME. you rounded yourself down." },
  },

  sq_numberworks_divide_by_zero: {
    kind: "side", from: 2, title: "DIVIDE BY ZERO", giver: "foreman", district: "numberworks",
    locations: ["numberworks:calculator", "numberworks:smokestacks"], cast: ["foreman"],
    requires: { missions: ["m15_rounding_down"], if: null },
    logline: "There's a button on top of the Big Calculator labelled ÷0. Every sign in Number Works says don't.",
    mechanic: { uses: ["rocket_jump", "grapple", "quiz"], hook: "an hour of NaN: gravity reverses, digits walk, and pop quizzes have no right answer" },
    twist: "You do. For one in-game hour Number Works stops making sense: gravity's a suggestion, prices are NaN (everything costs nothing and also infinity, so shops give you whatever you can carry), smokestacks puff the wrong way, and the giant digits get up and walk around. The Foreman (rehired) shows up and, for the first time since he was nine, laughs. 'i always wanted to press that.' The secret: at the top of the tallest Smokestack, a Lucky Thirteenth Rib (secret implant) is just sitting there, because in NaN-time nothing is unlucky.",
    beats: ["Climb the Big Calculator (conveyors, digit-riding).", "Press ÷0.", "An hour of chaos: loot the shops, ride the digits.", "The Foreman on the roof."],
    steps: [
      { id: "climb", text: "climb the big calculator", goal: { type: "reach", zone: "numberworks:calculator" } },
      { id: "press", text: "don't", goal: { type: "interact", target: "numberworks:calculator" }, do: ["flag:divided_by_zero"] },
      { id: "chaos", text: "survive an hour of NaN", goal: { type: "survive", secs: 300 } },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 0, loot: ["lt_district_numberworks"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. NaN.", meets: "MEETS EXPECTATIONS. NaN.", see_me: "SEE ME. NaN." },
  },
};
