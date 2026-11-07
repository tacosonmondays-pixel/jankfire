// MR. OVERTIME's fight-1 cutscenes (WP9, the presentation half): the phase changes and the retreat. The fight itself
// opens with c4_clocking_in (scenes_act1.js), which ends on his boss card. Played by public/js/story/scene.js in its
// native track format (title: [big, small, secs]); the boss hooks (public/js/story/bossfight.js) start the phase scenes
// when the referee's HP crosses content/bosses.js overtime_1's phase lines, and the retreat when the
// 'rescheduled' talk is done. Lines are his, from bosses.js / the cast bible.
export const SCENES_OVERTIME = {
  // 50%: he stops, sits down where he is and pours a coffee. 15 s of free hits on the clock
  ot1_coffee: {
    kind: "cinematic", act: 1, mission: "m04_clocking_in", len: 6.2, bars: false,
    cast: { ot: "overtime" },
    tracks: [
      { t: 0, cam: { shot: "wide", target: "ot", dur: 6 }, anim: ["ot", "ot_coffee", true], slowmo: [0.7, 1.0] },
      { t: 1.2, say: ["ot", "i'm on my break. this is my break."] },
      { t: 2.0, cam: { shot: "closeup", target: "ot", dur: 4 } },
      { t: 2.6, title: ["COFFEE BREAK", "free hits on the clock. you've got fifteen seconds", 2.6] },
    ],
  },
  // 45%: break's over. the roar, steam out of every seam, the slot whirs: now he grabs
  ot1_punching_in: {
    kind: "cinematic", act: 1, mission: "m04_clocking_in", len: 4.4, bars: false,
    cast: { ot: "overtime" },
    tracks: [
      { t: 0, cam: { shot: "lowAngle", target: "ot", dur: 4 }, anim: ["ot", "ot_roar"] },
      { t: 0.3, impact: "red", shake: 0.8, hitstop: 0.12 },
      { t: 1.4, say: ["ot", "break's over. you're all on the clock now."] },
      { t: 2.2, title: ["PUNCHING IN", "he grabs now. shoot the clock from inside", 2.2] },
    ],
  },
  // after the 'rescheduled' talk: he gets up off his knee, checks his watch, and walks away up the stairs, exactly on
  // time, a little lopsided, steam pouring out of the hole in his chest. the clock ticks with a limp
  ot1_retreat: {
    kind: "cinematic", act: 1, mission: "m04_clocking_in", len: 10,
    cast: { ot: "overtime" },
    tracks: [
      { t: 0, cam: { shot: "wide", target: "ot", dur: 4 }, anim: ["ot", "ot_kneel", true] },
      { t: 1.4, anim: ["ot", "ot_limp", true] },
      { t: 2.0, sfx: "tick" },
      { t: 2.6, move: ["ot", ["ot_retreat"], 1.6] },
      { t: 4.0, cam: { shot: "highAngle", target: "ot", dur: 6 } },
      { t: 6.5, title: ["RESCHEDULED", "he'll be back. on time.", 2.6] },
    ],
  },
};
