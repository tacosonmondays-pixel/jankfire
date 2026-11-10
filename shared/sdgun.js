// Search & Destroy gunplay numbers (owner, 2026-11-07: "match like valorants guns and dmg"). Plant & Defuse only: the
// server's damage (server/sdtune.js), the client's spread (shared/tactical.js tacSpread) and the bots all read this.
// original numbers in the spirit of tactical shooters, not copied from any of them. 100 HP, armour from shared/econ.js.
//   hd / bd / lg: damage per bullet (per pellet for shotguns) to the head / body / legs
//   fo: range falloff, [[from m, damage share], ...] (the last step you're past wins)
//   fs: first-shot spread standing still, from the hip (rad). ads: the same when aiming down sights (omitted = fs)
//   bl / bc: bloom, spread added per shot of a spray / its cap (resets with the spray pattern's reset time). kept small so the
//   spray pattern, not luck, decides where a held spray goes (owner: learnable patterns)
//   rof: shots per second in this mode only, where the everywhere-else rate is too spammy for a tactical round (owner, 2026-11-10:
//   "reduce the fire rate on some weapons"). omitted = the gun's normal rate (the Redline keeps its low-HP ramp)
//   rc: recoil, the spray pattern (shared/tactical.js PATTERNS) scaled by this (1: the patterns there are already S&D-sized)
export const SDG = {
  // sidearms: a tap pistol, a pocket shotgun, two machine pistols, the hand cannon
  pistol: { hd: 72, bd: 24, lg: 20, fo: [[25, 0.85]], fs: 0.004, ads: 0.003, bl: 0.002, bc: 0.008, rc: 1 },
  sawnoff: { hd: 11, bd: 8, lg: 7, fo: [[7, 0.6], [14, 0.25]], fs: 0.11, bl: 0, bc: 0, rc: 1 },
  akimbo: { rof: 7.5, hd: 40, bd: 15, lg: 12, fo: [[18, 0.8]], fs: 0.009, bl: 0.0008, bc: 0.005, rc: 1 },
  revolver: { hd: 152, bd: 46, lg: 38, fo: [[30, 0.85]], fs: 0.002, ads: 0.0015, bl: 0.004, bc: 0.015, rc: 1 },
  // smgs: several body shots, they fall off past 20 m, light on the move
  smg: { rof: 13, hd: 62, bd: 24, lg: 20, fo: [[20, 0.85], [40, 0.7]], fs: 0.006, ads: 0.004, bl: 0.0006, bc: 0.004, rc: 1 },
  redline: { hd: 66, bd: 26, lg: 22, fo: [[20, 0.85], [40, 0.7]], fs: 0.006, ads: 0.004, bl: 0.0006, bc: 0.004, rc: 1 },
  // shotguns: a one-shot close up, a tickle at range
  shotgun: { hd: 24, bd: 15, lg: 12, fo: [[8, 0.6], [14, 0.25]], fs: 0.075, bl: 0, bc: 0, rc: 1 },
  autoshot: { hd: 18, bd: 11, lg: 9, fo: [[7, 0.6], [12, 0.25]], fs: 0.07, bl: 0.002, bc: 0.01, rc: 1 },
  // rifles: a headshot is a one-tap, four-ish to the body
  lever: { hd: 124, bd: 52, lg: 44, fo: [], fs: 0.003, ads: 0.001, bl: 0.003, bc: 0.01, rc: 1 },
  burst: { hd: 104, bd: 34, lg: 29, fo: [[35, 0.9]], fs: 0.004, ads: 0.002, bl: 0.0006, bc: 0.003, rc: 1 },
  ar: { hd: 156, bd: 39, lg: 33, fo: [], fs: 0.003, ads: 0.0015, bl: 0.0008, bc: 0.004, rc: 1 },
  // snipers + the lmg: the marksman rifle one-taps heads, the big one kills on the body. both are hopeless from the hip
  dmr: { hd: 150, bd: 58, lg: 48, fo: [], fs: 0.03, ads: 0.0008, bl: 0.004, bc: 0.012, rc: 1 },
  sniper: { rof: 0.75, hd: 250, bd: 150, lg: 115, fo: [], fs: 0.09, ads: 0, bl: 0, bc: 0, rc: 1 },
  lmg: { rof: 10, hd: 118, bd: 32, lg: 27, fo: [[30, 0.9]], fs: 0.005, ads: 0.004, bl: 0.0005, bc: 0.005, rc: 1 },
};
// how moving spreads every gun here (the TAC numbers in shared/tactical.js, but meaner): walking costs a little,
// running a lot, jumping everything. counter-strafing works because it's all from your speed right now
// owner, twice: "moving and jumping while shooting makes it super inaccurate". running ~= a 12 degree cone (rarely lands past
// 10 m), in the air / on a rope ~= 26 degrees (point-blank shotguns only). landing: `land` spread on touchdown, gone after landMs
export const SDMOVE = { walk: 5.4, walkSpread: 0.05, runSpread: 0.21, airSpread: 0.45, crouch: 0.55, land: 0.16, landMs: 450 };
// bots: a body hit lands in the legs this often (a player's client says which zone it hit)
export const BOT_LEGS = 0.18;
// bots: their bullets do 0.7x everywhere (server/room.js botDmg). here hard bots do this instead: with one-tap headshots 1x deletes
// people, but 0.7x let a hard bot lose duels it had won (owner + coordinator, 2026-11-10). easy and normal stay at 0.7x
export const BOT_DMG_HARD = 0.85;

// shots per second for gun `id` in S&D (per hand for Lefty & Righty): its rof here, else whatever it does everywhere (`normal`)
export const sdRate = (id, normal) => { const r = sdRow(id); return r && r.rof > 0 ? r.rof : normal; };
export const sdRow = (id) => (typeof id === 'string' && Object.hasOwn(SDG, id) ? SDG[id] : null);
// damage of one bullet / pellet to zone z ('h' head, 'b' body, 'l' legs) at d metres
export function sdDamage(id, z, d) {
  const r = sdRow(id);
  if (!r) return null;
  let k = 1;
  for (const [from, mul] of r.fo) if (d >= from) k = mul;
  return (z === 'h' ? r.hd : z === 'l' ? r.lg : r.bd) * k;
}
// bloom for spray shot i (0 = the first shot: none)
export const sdBloom = (id, i) => { const r = sdRow(id); return r && i > 0 ? Math.min(r.bc, r.bl * i) : 0; };
// the gun's own first-shot spread: hip -> sights by aim (0..1)
export function sdBase(id, aim = 0) { const r = sdRow(id); if (!r) return null; const a = r.ads ?? r.fs; return r.fs + (a - r.fs) * aim; }
// the least of the two (what the server allows: it can't see whether you're aiming)
export function sdMinBase(id) { const r = sdRow(id); return r ? Math.min(r.fs, r.ads ?? r.fs) : null; }
// (recoil `rc` is applied to the spray patterns in shared/tactical.js, which imports this table)
