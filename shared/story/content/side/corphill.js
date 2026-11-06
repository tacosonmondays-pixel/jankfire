// OVERDUE side questlines: CORP HILL. Schema: see side/bottom.js. Corp Hill opens in Act IV but you can wander in
// earlier as a Late Fees magnet; these unlock from Act II with Overtime's lanyard.

export const SIDE_CORPHILL = {
  sq_corphill_punctuality_museum: {
    kind: "side", from: 2, title: "THE PUNCTUALITY MUSEUM", giver: null, district: "corphill",
    locations: ["corphill:museum"], cast: ["overtime"],
    requires: { missions: ["m13_rush_hour"], if: null },
    logline: "☺ CORP keeps printing new Overtimes. The newest one stands in the Punctuality Museum, among exhibits about being on time.",
    twist: "One exhibit is EMPLOYEE #1: A LIFE ON TIME, a glass case of Edwin Sallow's things, including a framed photo: Employee of the Month, the very first, with a cat on his lap and a woman out of focus at the edge of the frame, laughing. It's one of his six memory fragments. Every rehired Overtime stops in front of that case for exactly one second before he fights you. He doesn't know why.",
    beats: ["The museum: exhibits (THE FIRST TIME CARD, LATENESS THROUGH THE AGES, THE PENDULUM OF PUNCTUALITY), a gift shop that sells clocks.", "The EMPLOYEE #1 case.", "Boss: OVERTIME (REHIRED). Refightable every midnight: POSITION REFILLED."],
    steps: [
      { id: "museum", text: "visit the punctuality museum", goal: { type: "reach", zone: "corphill:museum" } },
      { id: "case", text: "look at the employee #1 exhibit", goal: { type: "interact", target: "corphill:museum" }, do: ["collect:ot_eotm_photo"] },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "overtime_rehire" }, boss: "overtime_rehire" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 900, loot: ["lt_boss_overtime_rehire"], standing: { corp: -5 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. exhibit closed.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you touched the exhibits." },
  },

  sq_corphill_reply_all: {
    kind: "side", from: 4, title: "REPLY ALL", giver: "pritchard", district: "corphill",
    locations: ["corphill:spire_60", "corphill:cathedral"], cast: ["pritchard"],
    requires: { missions: ["m24_the_split"], if: null },
    logline: "An email that will doom ☺ CORP is about to be sent. Chase it down the Spire's pneumatic tubes before it reaches everyone.",
    twist: "Pritchard sent it. By accident. It's his resignation letter, typed at 03:00 one night and saved as a draft for six years, and the Spire's mail system is pneumatic: it's a physical capsule racing through 400 km of tubes to every desk. You catch it at the last junction. He asks you to read it. It's one line: 'i would like a minute to myself.' He asks you to put it back in the tube. Or not.",
    beats: ["Pritchard on the pager, hyperventilating.", "A chase through the Spire's tube network (riding capsules, grappling junctions).", "The capsule.", "Choice: send it, or give it back to him."],
    steps: [
      { id: "page", text: "", goal: { type: "talk", who: "pritchard", talk: "oh_no" } },
      { id: "chase", text: "catch the email", goal: { type: "reach", zone: "corphill:spire_60" }, timer: 240 },
      { id: "choice", text: "", goal: { type: "flag", flag: "reply_all_choice_made" } },
    ],
    talks: {
      oh_no: { with: "pritchard", nodes: { start: { say: [["pager", "*BEEP BEEP BEEP BEEP BEEP*"], "i've sent something. i've sent something to everyone. it's in the tubes. it's going to every desk in the spire. please. please. it's a capsule. it's blue."] } } },
    },
    choices: [
      { id: "reply_all", prompt: "The blue capsule. One line: 'i would like a minute to myself.'", options: [
        { id: "send", label: "put it back in the tube", do: ["flag:reply_all_choice_made", "flag:pritchard_resigned"], consequence: "It reaches 11,000 desks. Nobody replies. At 09:00 Hask's calendar has a new entry: 'PRITCHARD: 1 MINUTE.' She approved it. He spends it on a bench by the Smiling Fountain. (He's still her assistant. It's a start.)" },
        { id: "return", label: "give it back to him", do: ["flag:reply_all_choice_made", "standing.corp:+2"], consequence: "He keeps it in his blazer pocket. 'not yet. but thank you for reading it.'" },
      ] },
    ],
    reward: { coupons: 500, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. delivered. or not.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you replied all." },
  },

  sq_corphill_casual_friday: {
    kind: "side", from: 4, title: "CASUAL FRIDAY", giver: "pip", district: "corphill",
    locations: ["corphill:spire_60", "corphill:fountain"], cast: ["pip"],
    requires: { missions: ["m24_the_split"], if: null },
    logline: "Ruin ☺ CORP's dress code: steal every tie in an office of 300 synced mannequin workers without being seen.",
    twist: "Without ties, the mannequin workers lose sync. They start walking at their own pace. One sits down. One looks out of the window. One, very slowly, loosens its collar and laughs. Pip, who set it up as a prank, watches through binoculars and goes quiet.",
    beats: ["Pip's challenge (Pip needs ties for a costume. 300 ties.)", "Stealth: the office moves on the beat of the clocks (On Time traversal).", "The workers out of sync."],
    steps: [ { id: "ties", text: "steal 300 ties", goal: { type: "pickup", item: "corp_tie" }, marker: "corphill:spire_60" } ],
    talks: {},
    choices: [],
    reward: { coupons: 450, standing: { bottom: 2, corp: -3 } },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. smart casual.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you're wearing all 300." },
  },

  sq_corphill_team_building: {
    kind: "side", from: 4, title: "TEAM BUILDING", giver: null, district: "corphill",
    locations: ["corphill:cathedral", "corphill:dividend_road"], cast: ["twins"],
    requires: { missions: ["m24_the_split"], if: null },
    logline: "Survive a ☺ CORP team-building exercise: a trust fall off a skyscraper.",
    twist: "It's run by the Twins (before the raid), who explain that this is how they were merged: a trust fall in the Merger's integration week, into a Gristle & Sons fusion vat. The exercise's 'catchers' are a Facilities team with a bleach cannon. You can fall (and grapple out at the last second), or push the Twins off instead and see who catches whom. Nobody catches anybody. They land in the Smiling Fountain, still agreeing.",
    beats: ["A rooftop. A whiteboard: TRUST.", "The fall (a skydiving grapple challenge down the Spire's side).", "Or the push."],
    steps: [ { id: "fall", text: "trust", goal: { type: "reach", zone: "corphill:dividend_road" } } ],
    talks: {},
    choices: [],
    reward: { coupons: 400, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you trusted nobody. correctly.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you caught the twins. why." },
  },

  sq_corphill_parking_permit: {
    kind: "side", from: 4, title: "PARKING PERMIT", giver: null, district: "corphill",
    locations: ["corphill:spire_lobby", "corphill:spire_60", "corphill:cathedral", "corphill:museum", "corphill:fountain"], cast: ["pritchard", "chad_tempo"],
    requires: { missions: ["m24_the_split"], if: null },
    logline: "Get a parking permit on Corp Hill. It's the hardest quest in the game.",
    twist: "It's a 19-step bureaucratic odyssey across every office on Corp Hill: forms that need forms, a queue that's a sim of a queue, a stamp that's in the museum, a signature from someone who died in the war (you have to go to the Lates for it), and finally an appointment with Pritchard, who looks at the form and says 'oh, you didn't need one of these. there's no parking on corp hill. there aren't any cars allowed.' The permit is a legendary (it's laminated).",
    beats: ["Form 1. Form 1a. Form 1a (revised).", "A queue (60 s of standing still; any movement sends you to the back).", "The stamp in the Punctuality Museum.", "A dead man's signature (the Lates).", "Pritchard."],
    steps: [
      { id: "forms", text: "complete the permit application (19 steps)", goal: { type: "interact", target: "corphill:spire_lobby" } },
      { id: "appt", text: "attend your permit appointment", goal: { type: "talk", who: "pritchard", talk: "permit" } },
    ],
    talks: {
      permit: { with: "pritchard", nodes: { start: { say: ["*He reads all nineteen forms carefully. It takes four minutes. He's very thorough.*", "this is wonderful. this is the most complete application i've ever seen.", "oh. you didn't need one. there's no parking on corp hill. cars aren't allowed.", "...i'll laminate it for you. you deserve that."], do: ["give:premium_parking_permit"] } } },
    },
    choices: [],
    reward: { coupons: 50, loot: ["premium_parking_permit"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. permitted.", meets: "MEETS EXPECTATIONS. pending.", see_me: "SEE ME. form 1a (revised) (revised)." },
  },
};
