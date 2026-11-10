// Zombies: limbs that come off, and the special zombies. Shared so the server (which decides) and the client
// (which draws it and shapes the hitboxes) agree on the bits, the sizes and the names.

// limb bits (a zombie's mask says which ones are gone). head only ever goes on the shot that kills
export const ZL = { armL: 1, armR: 2, legL: 4, legR: 8, head: 16 };
export const ZL_ARMS = ZL.armL | ZL.armR, ZL_LEGS = ZL.legL | ZL.legR;
export const ZL_LIMBS = ['armL', 'armR', 'legL', 'legR'];
export const zlCrawl = (mask) => (mask & ZL_LEGS) === ZL_LEGS; // no legs: it drags itself along
export const zlHop = (mask) => !!(mask & ZL_LEGS) && !zlCrawl(mask); // one leg: it hops
// numbers: a limb comes off after it soaks limbHp x the zombie's full HP (never less than limbMin); +limbPay each
export const ZLN = { limbHp: 0.3, limbMin: 20, limbPay: 10, crawl: 1.4, hop: 0.55, crawlUp: 0.9, crawlHead: 0.55, noArms: 0.5, oneArmCd: 1.4, noArmTear: 2.5, bornArmless: 0.18 };

// the special zombies (i = the number that goes over the wire, 0 = a plain one). from = first round they show up,
// w = how often next to the others, cap = how many at once. hp / claw multiply the round's numbers, speed replaces the gait
export const ZT = {
  chonk: { i: 1, name: 'CHONK', from: 5, w: 2, cap: 1, scale: 1.4, hp: 3.5, speed: 2.3, run: 0, claw: 1.6, color: '#b07dff', pay: 100, blast: 5, blastZ: 180, blastP: 18 }, // huge, slow, pops when it dies: everything nearby goes flying
  biter: { i: 2, name: 'ANKLE BITER', from: 3, w: 3, cap: 6, scale: 0.6, hp: 0.4, speed: 8.2, run: 2, claw: 0.5, cd: 0.7, pack: 3, color: '#ffe14d' }, // tiny, fast, three at a time
  hardhat: { i: 3, name: 'HARD HAT', from: 4, w: 3, cap: 4, scale: 1, hp: 1.2, hat: 3 }, // headshots only dink off the hat until it flies off
  screamer: { i: 4, name: 'SCREAMER', from: 6, w: 1.5, cap: 1, scale: 1.08, hp: 0.7, color: '#ff4fd8', pay: 40, every: 9000, yell: 1300, reach: 14, hype: 6000, boost: 1.45, see: 20 }, // shrieks: every zombie near it speeds up
};
export const ZT_IDS = ['', ...Object.keys(ZT)]; // index over the wire -> id
export const zlTypeChance = (r) => Math.min(0.4, Math.max(0, 0.07 * (r - 2))); // how many spawns are special, by round
export function zlPickType(r, alive = {}, rnd = Math.random) {
  if (rnd() >= zlTypeChance(r)) return '';
  const pool = Object.entries(ZT).filter(([id, d]) => r >= d.from && (alive[id] || 0) < d.cap);
  let t = rnd() * pool.reduce((a, [, d]) => a + d.w, 0);
  for (const [id, d] of pool) if ((t -= d.w) <= 0) return id;
  return '';
}

// which part a shot from eye e along d (unit) went through, for a zombie standing at pos facing yaw, drawn k times
// normal size. the shot is a line past its spine: how high it passes says legs / arms / torso, which side says left / right.
// sizes are the drawn mannequin's (1.2x a player). crawl: flat on the floor, so only arms or torso
export function zlZone(e, d, pos, yaw, k = 1, crawl = false, rnd = Math.random) {
  const hx = d[0] * d[0] + d[2] * d[2];
  if (hx < 1e-4) return 'torso'; // straight down on top of it
  const s = ((pos[0] - e[0]) * d[0] + (pos[2] - e[2]) * d[2]) / hx;
  const px = e[0] + d[0] * s - pos[0], pz = e[2] + d[2] * s - pos[2];
  const rel = (e[1] + d[1] * s - pos[1]) / k, off = Math.hypot(px, pz) / k;
  let side = px * Math.cos(yaw) - pz * Math.sin(yaw); // + = its right
  if (Math.abs(side) < 0.04 * k) side = rnd() - 0.5; // from the side you can't tell which: either
  const R = side > 0;
  if (crawl) return off > 0.18 ? (R ? 'armR' : 'armL') : 'torso';
  if (rel < 1.0) return R ? 'legR' : 'legL';
  if (rel >= 1.2 && rel < 1.9 && off > 0.2) return R ? 'armR' : 'armL';
  return 'torso';
}
