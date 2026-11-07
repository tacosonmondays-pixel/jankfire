// Search & Destroy gunplay numbers (owner, 2026-11-07: "match like valorants guns and dmg"). Plant & Defuse only: the
// server's damage (server/sdtune.js), the client's spread (shared/tactical.js tacSpread) and the bots all read this.
// original numbers in the spirit of tactical shooters, not copied from any of them. 100 HP, armour from shared/econ.js.
//   hd / bd / lg: damage per bullet (per pellet for shotguns) to the head / body / legs
//   fo: range falloff, [[from m, damage share], ...] (the last step you're past wins)
//   fs: first-shot spread standing still, from the hip (rad). ads: the same when aiming down sights (omitted = fs)
//   bl / bc: bloom, spread added per shot of a spray / its cap (resets with the spray pattern's reset time)
//   rc: recoil, the spray pattern (shared/tactical.js PATTERNS) scaled by this
export const SDG = {
  // sidearms: a tap pistol, a pocket shotgun, two machine pistols, the hand cannon
  pistol: { hd: 72, bd: 24, lg: 20, fo: [[25, 0.85]], fs: 0.004, ads: 0.003, bl: 0.008, bc: 0.05, rc: 1.2 },
  sawnoff: { hd: 11, bd: 8, lg: 7, fo: [[7, 0.6], [14, 0.25]], fs: 0.11, bl: 0, bc: 0, rc: 1 },
  akimbo: { hd: 40, bd: 15, lg: 12, fo: [[18, 0.8]], fs: 0.02, bl: 0.004, bc: 0.05, rc: 1.3 },
  revolver: { hd: 152, bd: 46, lg: 38, fo: [[30, 0.85]], fs: 0.002, ads: 0.0015, bl: 0.02, bc: 0.08, rc: 1.4 },
  // smgs: several body shots, they fall off past 20 m, light on the move
  smg: { hd: 62, bd: 24, lg: 20, fo: [[20, 0.85], [40, 0.7]], fs: 0.012, ads: 0.008, bl: 0.003, bc: 0.035, rc: 1.2 },
  redline: { hd: 66, bd: 26, lg: 22, fo: [[20, 0.85], [40, 0.7]], fs: 0.012, ads: 0.008, bl: 0.003, bc: 0.04, rc: 1.2 },
  // shotguns: a one-shot close up, a tickle at range
  shotgun: { hd: 24, bd: 15, lg: 12, fo: [[8, 0.6], [14, 0.25]], fs: 0.075, bl: 0, bc: 0, rc: 1 },
  autoshot: { hd: 18, bd: 11, lg: 9, fo: [[7, 0.6], [12, 0.25]], fs: 0.07, bl: 0.004, bc: 0.02, rc: 1 },
  // rifles: a headshot is a one-tap, four-ish to the body
  lever: { hd: 124, bd: 52, lg: 44, fo: [], fs: 0.003, ads: 0.001, bl: 0.01, bc: 0.04, rc: 1.2 },
  burst: { hd: 104, bd: 34, lg: 29, fo: [[35, 0.9]], fs: 0.004, ads: 0.002, bl: 0.004, bc: 0.025, rc: 1.15 },
  ar: { hd: 156, bd: 39, lg: 33, fo: [], fs: 0.003, ads: 0.0015, bl: 0.0045, bc: 0.035, rc: 1.3 },
  // snipers + the lmg: the marksman rifle one-taps heads, the big one kills on the body. both are hopeless from the hip
  dmr: { hd: 150, bd: 58, lg: 48, fo: [], fs: 0.03, ads: 0.0008, bl: 0.012, bc: 0.04, rc: 1 },
  sniper: { hd: 250, bd: 150, lg: 115, fo: [], fs: 0.09, ads: 0, bl: 0, bc: 0, rc: 1 },
  lmg: { hd: 118, bd: 32, lg: 27, fo: [[30, 0.9]], fs: 0.008, ads: 0.006, bl: 0.0035, bc: 0.05, rc: 1.2 },
};
// how moving spreads every gun here (the TAC numbers in shared/tactical.js, but meaner): walking costs a little,
// running a lot, jumping everything. counter-strafing works because it's all from your speed right now
export const SDMOVE = { walk: 5.4, walkSpread: 0.022, runSpread: 0.12, airSpread: 0.24, crouch: 0.55 };
// bots: a body hit lands in the legs this often (a player's client says which zone it hit)
export const BOT_LEGS = 0.18;

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
