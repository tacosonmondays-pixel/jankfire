// OVERDUE side questlines: CHROME GRISTLE. Schema: see side/bottom.js.

export const SIDE_CHROMEGRISTLE = {
  sq_chromegristle_spare_parts: {
    kind: "side", from: 3, title: "SPARE PARTS", giver: "bev", district: "chromegristle",
    locations: ["chromegristle:jar_alley", "chromegristle:arcade", "chromegristle:noodle_shrine"], cast: ["bev"],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "A kidney got up and left Bev's clinic before its install. Retrieve it.",
    mechanic: { uses: ["grapple", "lasso"], hook: "chase a kidney along the neon sign line" },
    twist: "The kidney has been regrown so many times by different Meat Mechanics that it's become a little person: it has a job (it's working the noodle stall at the Noodle Shrine), friends, and a tiny paper hat. Its original owner, a man on the Commute, doesn't want it back: 'it's got a life now. i've got two.' You can leave it be, and it waves at you every time you pass.",
    beats: ["A chase through Jar Alley (jars blink at you).", "Arcade Row: it's been playing the old JANKFIRE cabinet and has the high score.", "The Noodle Shrine: it's working the stall.", "Talk to its original owner by pager."],
    steps: [
      { id: "jar", text: "follow the kidney's trail", goal: { type: "reach", zone: "chromegristle:jar_alley" } },
      { id: "arcade", text: "", goal: { type: "reach", zone: "chromegristle:arcade" } },
      { id: "shrine", text: "find the kidney", goal: { type: "reach", zone: "chromegristle:noodle_shrine" } },
      { id: "choice", text: "", goal: { type: "flag", flag: "kidney_choice_made" } },
    ],
    talks: {},
    choices: [
      { id: "kidney", prompt: "The kidney, in a paper hat, serving noodles, looks at you.", options: [
        { id: "leave", label: "leave it be", do: ["flag:kidney_choice_made", "flag:kidney_free", "standing.bottom:+2"], consequence: "Bev shrugs: 'organs have rights now, do they. fine.' The kidney gives you free noodles forever (a 25% heal snack, restocks daily)." },
        { id: "take", label: "take it back to bev", do: ["flag:kidney_choice_made", "flag:kidney_returned", "coupons:+600"], consequence: "Bev installs it in a paying customer. The noodle stall closes. Arcade Row's high score stays forever." },
      ] },
    ],
    reward: { coupons: 200, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you ate the noodles. you ate a lot of them." },
  },

  sq_chromegristle_second_opinion: {
    kind: "side", from: 3, title: "SECOND OPINION", giver: "bev", district: "chromegristle",
    locations: ["chromegristle:pawn", "chromegristle:upsell_clinic", "gut:clinic_bev"], cast: ["bev", "upsell"],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "Get two Meat Mechanics to diagnose the same rash. They disagree violently.",
    mechanic: { uses: ["implants"], hook: "the grid rash is Drift you can see" },
    twist: "The rash is on you: a pattern spreading under your plastic where your implants join, shaped exactly like the Schedule's grid. Both diagnoses are right. Bev says it's rejection; Upsell says it's 'the body accepting the schedule'. It's the first visible sign of Drift, and it fades if you uninstall parts or lower your Drift (the game tells you, in Bev's words, without a number).",
    beats: ["A rash. Bev's diagnosis.", "Upsell's diagnosis (book a consultation, or if he's beaten, his rehired self).", "They meet. They fight (a gunfight between two clinics).", "The truth."],
    steps: [
      { id: "bev", text: "get bev's opinion", goal: { type: "talk", who: "bev", talk: "rash" }, marker: "gut:clinic_bev" },
      { id: "upsell", text: "get a second opinion", goal: { type: "reach", zone: "chromegristle:upsell_clinic" } },
      { id: "fight", text: "survive the disagreement", goal: { type: "survive", secs: 120 } },
    ],
    talks: {
      rash: { with: "bev", cam: "closeup", nodes: { start: { say: ["*Bev looks at the grid-shaped rash spreading from your implants with a magnifier.*", "that's rejection, chassis. your body doesn't know where it ends any more. it's drawing itself a map.", "the more parts that aren't you, the more of this.", "go and ask upsell. he'll tell you it's a feature. he's half right, which is the worst amount of right."] } } },
    },
    choices: [],
    reward: { coupons: 400, flags: ["drift_explained_visibly"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. both opinions obtained.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you scratched it." },
  },

  sq_chromegristle_arcade_legend: {
    kind: "side", from: 3, title: "ARCADE LEGEND", giver: null, district: "chromegristle",
    locations: ["chromegristle:arcade"], cast: [],
    requires: { missions: ["m17_minutes"], if: null },
    logline: "Beat the high score on an Arcade Row cabinet that runs the old JANKFIRE.",
    mechanic: { uses: ["spinbot"], hook: "beat your own high score; the cabinet's cheat code is a Spinbot" },
    twist: "The cabinet is a tiny piece of the Machine's sims, salvaged. The high score belongs to CALE R. 4417, from sixty-one years ago, set on a lunch break. You're trying to beat yourself. When you do, the cabinet asks for initials, and if you type RC it plays a ten-second Cale memory: a lunch break, a cheap sandwich, Agnes leaning on the cabinet saying 'you're wasting your break, rory.' 'it's the only bit of the day that's mine.'",
    beats: ["The cabinet. The score: 4417 points, CALE R.", "Play (a short arcade-rules match against bots on a tiny map).", "Beat it. Enter initials."],
    steps: [
      { id: "play", text: "beat the high score", goal: { type: "flag", flag: "arcade_beaten" }, marker: "chromegristle:arcade" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 300, flags: [], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. NEW HIGH SCORE.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. insert coin." },
  },

  sq_chromegristle_organ_pawn: {
    kind: "side", from: 3, title: "BUY BACK", giver: null, district: "chromegristle",
    locations: ["chromegristle:pawn"], cast: ["lumps"],
    requires: { missions: ["m20_the_missing"], if: null },
    logline: "Organ Pawn has a kidney in its window with a tag: D. PELL. Lumps saw it.",
    mechanic: { uses: ["nvg", "grapple"], hook: "a pawn-shop heist past blinking jars" },
    twist: "Dot sold it, years ago, to pay for Lumps' tenth birthday (a bike made of a shopping trolley). The pawn tag has accrued sixty-one per cent a year in fees. It costs more than the Bottom earns in a year. Lumps can't afford it and won't let you pay. The only way is a Pawn Heist (a stealth job) or the Gold Member legendary's loot magnet, or simply... letting it go. Dot, told, says: 'it was a lovely bike.'",
    beats: ["Lumps, frozen at the shop window.", "The price.", "The choice: heist it, buy it with your own coupons (Lumps is cross and grateful), or leave it."],
    steps: [
      { id: "window", text: "", goal: { type: "talk", who: "lumps", talk: "window" }, marker: "chromegristle:pawn" },
      { id: "choice", text: "the kidney in the window", goal: { type: "flag", flag: "pawn_choice_made" } },
    ],
    talks: {
      window: { with: "lumps", cam: "closeup", nodes: { start: { say: ["*Lumps, standing in front of Organ Pawn's window, very still. A kidney in a jar. A tag: D. PELL. PAWNED. FEES ACCRUING.*", "she said she sold it. for my birthday. i got a bike. it was a trolley with pedals.", "i thought she meant she sold her earrings.", "*he puts a hand on the glass.* it's very expensive. it got more expensive every year i didn't know."] } } },
    },
    choices: [
      { id: "pawn", prompt: "Dot's kidney, in Organ Pawn's window.", options: [
        { id: "heist", label: "steal it back", do: ["flag:pawn_choice_made", "flag:pawn_heist", "fees:+2"], consequence: "A stealth heist (alarm jars, blink sensors, a guard with too many arms). Dot gets her kidney back from Bev that week. 'well. i'll have to get another birthday out of you, ambrose.'" },
        { id: "buy", label: "buy it (8,000 coupons)", do: ["flag:pawn_choice_made", "flag:pawn_bought", "coupons:-8000", "standing.bottom:+5"], consequence: "Lumps refuses, then cries, then lets you. He carries the jar home on his lap like the soup pot." },
        { id: "leave", label: "leave it", do: ["flag:pawn_choice_made", "flag:pawn_left"], consequence: "Lumps nods. When he tells Dot, she laughs: 'it was a lovely bike.'" },
      ] },
    ],
    reward: { coupons: 0, standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
  },
};
