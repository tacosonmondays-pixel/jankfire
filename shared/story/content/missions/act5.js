// OVERDUE main missions, Act V: "Overdue" (the Master Clock). The act's question: what do you become?
// Same schema as missions/act1.js. m32 ends in the_choice, which plays one of the four endings (endings.js).

export const MISSIONS_ACT5 = {
  // ------------------------------------------------------------------ 31
  m31_fully_billable: {
    act: 5, n: 31, title: "OVERDUE", kind: "main", giver: null, district: "corphill",
    locations: ["corphill:master_clock"],
    cast: ["overtime", "june", "lumps", "gordo"],
    requires: { missions: ["m30_the_lobby"], if: null },
    logline: "Mr. Overtime, wired into the Master Clock, holds the door one last time. If you found the end of his shift, you can give it back to him.",
    beats: [
      "C21: the Clock opens like a ribcage. Overtime plugs his stapler arms into the gears. 'your appointment is now.'",
      "Boss fight: MR. OVERTIME, FULLY BILLABLE (overtime_4). A vertical gearwork arena; every phase changes the clock speed (slow-mo rounds, fast-forward rounds).",
      "At the phase 2 break, he stops to 'process' you, and you get to talk. With all six of his memory fragments, you can show him the end of his shift.",
      "Talk-down: C22. He clocks out. 'first time i've left on time.' He gives you Cale's tape. Otherwise: phase 3, and you destroy him.",
    ],
    reveals: {
      learn: ["(talk-down) Overtime killed Cale at 17:29, then stood at the door at 17:30 with his coat on, on the phone to June: 'i'm on my way.'", "He kept Cale's tape in his chest slot for sixty-one years. He never handed it in."],
      suspect: [],
      withheld: [],
    },
    steps: [
      { id: "c21", text: "", goal: { type: "flag", flag: "seen_c21" }, scene: "c21_fully_billable" },
      { id: "boss", text: "stop the master clock", goal: { type: "killBoss", boss: "overtime_4" }, boss: "overtime_4", talk: "processing", notes: "the processing talk runs at the phase 2 break (the boss's `talk` hook)" },
      { id: "out", text: "", goal: { type: "flag", flag: "overtime_resolved" }, notes: "talk-down → C22, flag overtime_clocked_out, give cale_tape. Destroyed → the tape falls out of his chest slot; flag overtime_destroyed" },
    ],
    talks: {
      processing: {
        with: "overtime", cam: "closeup",
        nodes: {
          start: { say: ["*Phase 2 ends. Overtime grabs you in a stapler arm and holds you in front of his chest slot. The clock face in his heart is huge, cracked, ticking unevenly. He doesn't punch you in. He waits.*", "please hold still. you're being processed.", "...i don't know what to process you as. you're not on my list. you've never been on my list. you're absent and you're here.", "what are you?"], opts: [["(with all six fragments) i'm the one who's got your last backup.", "frags", { if: "frags.overtime>=6" }], ["(with some fragments) you have a wife. june.", "some", { if: "frags.overtime>=3 !frags.overtime>=6" }], ["i'm the one you killed.", "killed"], ["(cold) i'm your replacement.", "cold", { if: "drift>=4" }]] },
          frags: { say: ["*You show him, one by one: his first day, the founder on his lap. June's lunchbox note. His employee-of-the-month photo, number one. Hask's order to hold the lobby. Cale running, 17:29. And the last one: 17:30:00, the door, his coat on, the phone.*", "*His grip loosens. The clock in his chest slows down.*", "that's... that's the end of my shift.", "you've got the end of my shift."], opts: [["*give it to him*", "give"]] },
          give: { say: ["*He puts you down. Very carefully, like something that might break.*"], do: ["flag:overtime_clocked_out", "flag:overtime_resolved", "scene:c22_clocking_out", "give:cale_tape", "fate:overtime=clocked_out", "drift:-1"] },
          some: { say: ["june.", "*the grip tightens, then loosens, then tightens* june. june's at home. june's always at home. i'm always...", "no. no, i'm on shift. i can't remember the rest. i can't. you haven't got the rest."], do: ["flag:overtime_almost"], next: "fight" },
          killed: { say: ["*A long pause. The ticking stutters.*", "cale. 17:29. you were running.", "...it was policy. it was policy."], next: "fight" },
          cold: { say: ["*Something like relief in his visor.*", "oh. good. good. they've sent someone. i'm so tired."], do: ["drift:+1"], next: "fight" },
          fight: { say: ["*He lifts you to the slot. Then he flings you across the gearwork instead, and the Clock speeds up. Phase 3.*"], do: ["flag:overtime_destroyed_path"] },
        },
      },
    },
    choices: [],
    scenes: ["c21_fully_billable", "c22_clocking_out"],
    reward: { coupons: 0, items: ["cale_tape"], loot: ["lt_boss_overtime_4"], flags: ["beat_overtime_4"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "if destroyed: no C22; a Moment where his punch-clock stops, his visor goes dark, and the tape falls out of the slot onto the platform (give:cale_tape, flag:overtime_destroyed, fate:overtime=terminated).",
  },

  // ------------------------------------------------------------------ 32
  m32_fully_vested: {
    act: 5, n: 32, title: "FULLY VESTED", kind: "main", giver: null, district: "corphill",
    locations: ["corphill:master_clock", "corphill:spire_top", "corphill:clock_room"],
    cast: ["hask", "lumps", "gordo", "mina", "founder"],
    requires: { missions: ["m31_fully_billable"], if: null },
    logline: "Marion Hask shows you the last page and the body under her suit, and then it's your choice.",
    beats: [
      "C23: page six on the console. 'I signed at 16:59. At 17:10 Remainder telephoned me.' They'd hit target by half a percent. She launched anyway. The suit opens: a body of other people's organs, each one tagged with a name.",
      "If you hold Mr. Sevens' call log and Neville's envelope, extra lines: you can read them back to her.",
      "Boss fight: MARION HASK at the Clock's controls.",
      "C24: the ledger. The three choices in front of you (and the fourth, if the cats are all petted).",
      "The choice. Then the ending, the district epilogues, the credits drive.",
    ],
    reveals: {
      learn: ["☺ CORP page: the launch at 17:30 was timed so a full day's wages, every pension and every debt was written off at close of business, and the final backup was taken to keep the dead as workforce.", "At 17:10 Hask knew the launch wasn't needed. She launched because it was cheaper than not."],
      suspect: [],
      withheld: [],
    },
    steps: [
      { id: "c23", text: "", goal: { type: "flag", flag: "seen_c23" }, scene: "c23_fully_vested", do: ["give:page_corp", "flag:pages_corp"], talk: "evidence" },
      { id: "boss", text: "stop marion hask", goal: { type: "killBoss", boss: "hask" }, boss: "hask" },
      { id: "c24", text: "", goal: { type: "flag", flag: "seen_c24" }, scene: "c24_the_choice" },
      { id: "end", text: "choose", goal: { type: "flag", flag: "ending_chosen" } },
    ],
    talks: {
      evidence: {
        with: "hask", cam: "closeup",
        nodes: {
          start: { branch: [["has:sevens_call_log has:late_memo", "both"], ["has:late_memo", "memo"], [null, "none"]] },
          both: { say: ["*Before the suit opens, you put two things on the console: Mr. Sevens' call log (17:10, to M. HASK, 4 minutes) and Neville's envelope (TARGET MET +0.5%).*", "*Hask looks at them for exactly as long as it takes to read them.*", "Mr. Sevens kept a log. Of course he did. He touches wood.", "And Mr. Brisk's envelope. He was very late. It would not have mattered if he had been on time. I would have thanked him for his time too."], do: ["flag:confronted_hask_evidence"] },
          memo: { say: ["*You put Neville's envelope on the console: TARGET MET (+0.5%).*", "Mr. Brisk. He was very late. It would not have mattered if he had been on time."], do: ["flag:confronted_hask_evidence"] },
          none: { say: ["*She doesn't need you to bring proof. She tells you, because she has never once been ashamed of arithmetic.*"] },
        },
      },
    },
    choices: [
      { id: "the_choice", prompt: "The lanyard. The lever behind the glass. The six pages and the broadcast switch. (And, if you petted the whole board, a purring from the clock room.)", options: [
        { id: "sign", label: "ON TIME: put on the lanyard and restart the Clock", do: ["flag:ending_on_time", "flag:ending_chosen", "scene:e1_on_time", "fate:change=signed", "standing.corp:+50"], consequence: "The Restoration runs. Everyone is fed on schedule. The dead go to work forever with your recording as their template. The Bottom is sold to the void (unless its living are on the staffing table: Lumps' plan). Nobody in the city is free, including you." },
        { id: "smash", label: "LATE: break the Master Clock", do: ["flag:ending_late", "flag:ending_chosen", "scene:e2_late", "standing.bottom:+50"], consequence: "Nobody owns time again. The Restoration dies with the Clock. The companies lose their grip, the districts belong to whoever holds them, the rot spreads, and something green grows on the Long Stairs. No lights on Corp Hill, no food on schedule, nobody to stop the next warlord." },
        { id: "publish", label: "OFF THE BOOKS: publish Option C to every screen", if: "pages>=6", do: ["flag:ending_off_books", "flag:ending_chosen", "scene:e3_off_books", "standing.bottom:+30", "standing.corp:-30"], consequence: "All six pages, on every screen. The debts are void. The sims are opened to the dead as their own place. The companies survive, weakened, and have to bargain at a table with the people they wrote off. You walk out onto the Commute alone." },
        { id: "nap", label: "NAP TIME: open the small door", if: "cats>=12", do: ["flag:ending_nap_time", "flag:ending_chosen", "scene:e4_nap_time"], consequence: "The founder walks across the keyboard and types zzzzzzzzzzzz. Legally, that's a nap. Non-canon: after the credits the game asks you to choose again (the save keeps the NAP TIME unlock and the outfit)." },
      ] },
    ],
    scenes: ["c23_fully_vested", "c24_the_choice", "e1_on_time", "e2_late", "e3_off_books", "e4_nap_time", "credits_drive"],
    reward: { coupons: 0, items: ["page_corp"], loot: ["lt_boss_hask"], flags: ["beat_hask", "story_complete"], standing: {} },
    grade: { exceeds: "", meets: "", see_me: "" },
    notes: "after any canon ending the city stays open (post-game) with the ending's look applied (endings.js). The Machine keeps running the sims.",
  },
};
