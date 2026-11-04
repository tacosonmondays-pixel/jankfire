// Scales of Justice: the court weighs whoever you hit against you, right now.
// The server runs this at hit time with what it knows (that number is the only one that decides damage);
// the client runs it on the scoreboard it can see, to tip the scale in your hands before you swing.
//
// Every charge against them is a point of guilt, every point in their favour takes one off:
//   K/D this match        theirs is better than yours +1, worse -1
//   scoreboard            they're above you +1, below you -1; they lead the match (and it isn't you) +1 more
//   team modes            your team is behind +1, ahead -1
//   kill streak           3+ kills in a row +1, 5+ +2
//   revenge               they're the last one who killed you +2
// guilt g > 0: GUILTY, x(1 + 0.4g), at most x3 (35 -> 105: a one-shot)
// guilt g < 0: NOT GUILTY, x(1 - 0.25|g|), at least x0.4
// g = 0: HUNG JURY, x1
export const COURT = { guilt: 0.4, mercy: 0.25, min: 0.4, max: 3 };

const kd = (p) => (p.kills || 0) / Math.max(1, p.deaths || 0);
// scoreboard order: most kills first, fewest deaths breaks ties
const above = (a, b) => (a.kills || 0) > (b.kills || 0) || ((a.kills || 0) === (b.kills || 0) && (a.deaths || 0) < (b.deaths || 0));

// me / them: { kills, deaths } (+ them.streak). ctx: { board: everyone on the scoreboard, teams: [your score, theirs] or null, revenge }
export function verdict(me, them, ctx = {}) {
  let g = 0;
  const why = []; // [text, +1 / -1] for the readout
  const charge = (n, text) => { g += n; why.push([text, Math.sign(n)]); };
  const a = kd(them), b = kd(me);
  if (Math.abs(a - b) > 0.01) charge(a > b ? 1 : -1, a > b ? 'better K/D' : 'worse K/D');
  if (above(them, me)) {
    charge(1, 'above you');
    if ((them.kills || 0) > 0 && !(ctx.board || []).some((o) => above(o, them))) charge(1, 'match leader');
  } else if (above(me, them)) charge(-1, 'below you');
  if (ctx.teams && ctx.teams[0] !== ctx.teams[1]) charge(ctx.teams[0] < ctx.teams[1] ? 1 : -1, ctx.teams[0] < ctx.teams[1] ? 'your team is behind' : 'your team is ahead');
  const s = them.streak || 0;
  if (s >= 3) charge(s >= 5 ? 2 : 1, `${s} kill streak`);
  if (ctx.revenge) charge(2, 'killed you');
  const mult = g > 0 ? Math.min(COURT.max, 1 + COURT.guilt * g) : g < 0 ? Math.max(COURT.min, 1 - COURT.mercy * -g) : 1;
  return { g, mult: Math.round(mult * 100) / 100, why };
}

export const verdictName = (g) => (g > 0 ? 'GUILTY' : g < 0 ? 'NOT GUILTY' : 'HUNG JURY');
export const fmtMult = (m) => 'x' + String(Math.round(m * 100) / 100);
