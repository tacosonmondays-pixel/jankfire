// OVERDUE side questlines: THE LATES. Schema: see side/bottom.js.

export const SIDE_LATES = {
  sq_lates_groundhog_lunch: {
    kind: "side", from: 3, title: "GROUNDHOG LUNCH", giver: "gus", district: "lates",
    locations: ["lates:canteen"], cast: ["gus", "pauline"],
    requires: { missions: ["m22_the_waiting_room"], if: null },
    logline: "Gus has been trying to finish the same lasagne for 22,000 days. Something interrupts him at the last bite every time.",
    twist: "Every interruption is a different Looper's small Tuesday disaster (a fire alarm, a dropped tray, a fight over a stapler), and fixing one makes the next one happen. When you finally clear all eleven, Gus holds up the last bite and doesn't eat it. 'if i finish it, it'll be wednesday. and my wife will be dead.' You can tell him to eat it, or not. Either is kind.",
    beats: ["Gus and the lasagne.", "Eleven interruptions, each a micro-puzzle across one loop (a chain: fix the alarm at 12:31 and the tray falls at 12:33).", "The last bite."],
    steps: [
      { id: "meet", text: "have lunch with gus", goal: { type: "talk", who: "gus", talk: "lasagne" }, marker: "lates:canteen" },
      { id: "chain", text: "stop 11 interruptions in one loop", goal: { type: "interact", target: "lates:canteen" } },
      { id: "bite", text: "", goal: { type: "talk", who: "gus", talk: "bite" } },
    ],
    talks: {
      lasagne: { with: "gus", nodes: { start: { say: ["it's lasagne!", "nearly got the last bite yesterday. well. today. it's always today.", ["pauline", "*not looking up* he's said that twenty-two thousand times."], "and i'll say it again! it's lasagne!"] } } },
      bite: { with: "gus", cam: "closeup", nodes: { start: { say: ["*The canteen, 12:59. Nothing has interrupted. Gus holds the last bite on his fork.*", "...if i finish it, it'll be wednesday. won't it.", "my wife makes it better. made. makes. on wednesday i'll find out which."], opts: [["eat it, gus.", "eat"], ["you don't have to. not today.", "wait"]] },
        eat: { say: ["*He eats it. He chews for a long time.*", "...it's quite bad, actually.", "*he laughs, and it turns into something else, and Pauline puts her hand on his.*"], do: ["flag:gus_finished"] },
        wait: { say: ["*He puts the fork down. Relieved.*", "tomorrow. well. today. thanks."], do: ["flag:gus_waited"] } } },
    },
    choices: [],
    reward: { coupons: 400, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS.", meets: "MEETS EXPECTATIONS. it's lasagne.", see_me: "SEE ME. you ate his lasagne." },
  },

  sq_lates_copy_of_a_copy: {
    kind: "side", from: 3, title: "COPY OF A COPY", giver: "pauline", district: "lates",
    locations: ["lates:remainder_office", "lates:waiting_room"], cast: ["pauline"],
    requires: { missions: ["m22_the_waiting_room"], if: null },
    logline: "You're locked in an office in the Lates. The only way out is to photocopy yourself.",
    twist: "Each copy is a little worse (blurrier, a wrong colour, a knee that bends two ways), and each copy needs to stand on a pressure plate. By copy six you're arguing with yourself. The last copy, very faded, asks the original: 'are we the same person?' The puzzle's answer is no; the door opens when you say so.",
    beats: ["An office, a copier, six pressure plates.", "Copies follow your inputs with a delay (a co-op puzzle with yourself).", "The faded copy's question."],
    steps: [ { id: "copy", text: "photocopy yourself out", goal: { type: "interact", target: "lates:remainder_office" }, talk: "copy" } ],
    talks: {
      copy: { with: "change", nodes: { start: { say: [["voice", "*your sixth copy, faint grey, a wrong knee both ways* are we the same person?"]], opts: [["yes.", "yes"], ["no.", "no"]] },
        yes: { say: [["voice", "*the door stays shut* ...then why am i so faint?"]], next: "start" },
        no: { say: [["voice", "*the door clicks* good. i didn't think so. good luck, original."]], do: ["flag:copy_puzzle_done"] } } },
    },
    choices: [],
    reward: { coupons: 350, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. one of you got out.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you're still in there. all six." },
  },

  sq_lates_hold_music: {
    kind: "side", from: 3, title: "HOLD MUSIC", giver: "pauline", district: "lates",
    locations: ["lates:waiting_room", "lates:stairwell", "lates:tuesday_tower"], cast: ["pauline"],
    requires: { missions: ["m22_the_waiting_room"], if: null },
    logline: "The Lates' hold music plays everywhere, all day. Nobody knows where it comes from. Find the source.",
    twist: "It's a woman in the Backrooms Stairwell, deep down, at a switchboard, humming into the line to keep 4,000 callers company: the Lates' Remainder call centre has had 4,000 people on hold since 17:29. She's been humming for sixty-one years. One of the held calls is from the Spire's lobby security desk, 17:29: in the background, a running man's footsteps and a polite voice saying 'that's against policy'. It's one of Overtime's memory fragments.",
    beats: ["Follow the music (it gets louder near certain walls; a Backrooms descent).", "The switchboard.", "The held calls; one from the lobby."],
    steps: [
      { id: "follow", text: "find where the hold music comes from", goal: { type: "reach", zone: "lates:stairwell" } },
      { id: "line", text: "listen to the held calls", goal: { type: "interact", target: "lates:stairwell" }, do: ["collect:ot_1729"] },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 400, standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. your call is important.", meets: "MEETS EXPECTATIONS. please hold.", see_me: "SEE ME. you hung up on 4,000 people." },
  },

  sq_lates_quality_control: {
    kind: "side", from: 3, title: "QUALITY CONTROL", giver: null, district: "lates",
    locations: ["lates:missing_door", "lates:warehouse"], cast: ["prototype"],
    requires: { missions: ["m23_workforce_restoration"], if: null },
    logline: "Go back through the door at 03:00. At the end of a row there was an empty dock with your name on it. It isn't empty any more.",
    twist: "Hask had a copy of you built with the Schedule forced in, to see what you'd be on the payroll. It's happy. It remembers Mina and doesn't think she's important. Beating it gets you its chip: the strongest head implant in the game, which loads a little of the Schedule into you. It costs two permanent Drift. The game asks you twice.",
    beats: ["Any night after m23, at 03:00, the door is there for anyone who knows.", "The dock: CALE R. 4417 · EMPLOYEE OF THE QUARTER.", "Secret boss: EMPLOYEE 4417.", "It asks what time it is."],
    steps: [
      { id: "door", text: "go back through the door at 03:00", goal: { type: "reach", zone: "lates:warehouse" }, if: "clock.lates=03:00-04:00" },
      { id: "boss", text: "", goal: { type: "killBoss", boss: "prototype" }, boss: "prototype" },
    ],
    talks: {},
    choices: [],
    reward: { coupons: 1000, loot: ["lt_boss_prototype"], standing: {} },
    grade: { exceeds: "EXCEEDS EXPECTATIONS. you were better than you.", meets: "MEETS EXPECTATIONS.", see_me: "SEE ME. you lost to you." },
  },
};
