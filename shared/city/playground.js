// The districts as grapple playgrounds (owner: "take advantage of the grapple, and various mechanics"). Verticality
// first: glowing hook rings on everything that would hold a rope (gantries, masts, rib crowns, billboards, the 13),
// swing lines over the Long Stairs, the market, Rib Avenue and the highway, grapple-only secret alcoves (no stairs,
// no ladder: you swing in), and the PvP game's momentum toys (jump pads, a slide chute, banana peels and marbles).
// Each district generator calls its pass last. Swing lines are checked by tools/city/grapple.mjs (the real rope).
import { SLICE, hwY } from './slice.js';
import { rng, hash2 } from './plan.js';
import { hook, rampZ, PASTEL, pick } from './kit.js';

export const BANISTER = [SLICE.longStairs.x1 + 3, SLICE.longStairs.x1 + 5.4]; // x0, x1 (lane() opens the lip walls here)
const T = SLICE.bottom, zSouth = (k) => 256 - T.terr * k, yOf = (k) => k * T.rise, LANE = 7;
const inRect = (x0, z0, x1, z1, r) => x0 < r[2] && x1 > r[0] && z0 < r[3] && z1 > r[1];

// a gantry: two posts and a beam across at height y (on ground ya / yb either end), rings hanging under the beam
function gantry(B, xa, xb, z, ya, yb, y, rings = [0.5], o = {}) {
  const mat = o.mat || 'rust', t = o.tint;
  if (B.inside(xa, z)) B.add(xa - 0.25, ya, z - 0.25, xa + 0.25, y + 0.4, z + 0.25, mat, { tint: t });
  if (B.inside(xb, z)) B.add(xb - 0.25, yb, z - 0.25, xb + 0.25, y + 0.4, z + 0.25, mat, { tint: t });
  B.add(xa, y, z - 0.2, xb, y + 0.45, z + 0.2, mat, { tint: t }); // (clipped per chunk: each side keeps its half)
  for (const f of rings) hook(B, xa + (xb - xa) * f, y - 0.35, z, { yaw: 0 });
}
// a mast: a pole with a ring at the top (and a little lamp so you see it at night)
function mast(B, x, z, y0, h, o = {}) {
  if (!B.inside(x, z)) return;
  B.add(x - 0.18, y0, z - 0.18, x + 0.18, y0 + h, z + 0.18, o.mat || 'rust', { tint: o.tint });
  B.add(x - 0.9, y0 + h - 0.3, z - 0.08, x + 0.9, y0 + h - 0.1, z + 0.08, o.mat || 'rust', { nc: true, tint: o.tint });
  hook(B, x, y0 + h + 0.7, z, { yaw: o.yaw || 0 });
  B.light(x, y0 + h - 1, z, 0xffe14d, 7, 0.5);
}
// a jump pad (the PvP kind): a glowing slab with chevrons, throws you along v
function pad(B, x, y, z, v, name, w = 2.6) {
  if (!B.inside(x, z)) return;
  B.add(x - w / 2, y, z - w / 2, x + w / 2, y + 0.18, z + w / 2, 'metal', { tint: 0x2a2a30 });
  B.add(x - w / 2 + 0.2, y + 0.18, z - w / 2 + 0.2, x + w / 2 - 0.2, y + 0.22, z + w / 2 - 0.2, 'glow', { nc: true, tint: 0xffe14d });
  const d = Math.hypot(v[0], v[2]) > 0.1 ? [v[0] / Math.hypot(v[0], v[2]), v[2] / Math.hypot(v[0], v[2])] : [0, -1];
  for (const s of [-0.5, 0.2]) B.add(x + d[0] * s - 0.25, y + 0.22, z + d[1] * s - 0.25, x + d[0] * s + 0.25, y + 0.25, z + d[1] * s + 0.25, 'paint', { nc: true, tint: 0x111111 }); // arrows (squares, roughly)
  B.out.triggers.push({ kind: 'pad', box: [x - w / 2, y - 0.2, z - w / 2, x + w / 2, y + 1.2, z + w / 2], v, name });
  B.light(x, y + 1, z, 0xffe14d, 6, 0.6);
}
// banana peels or marbles on the floor: you go flying
function slip(B, x, y, z, w, d, what, r) {
  if (!B.inside(x, z)) return;
  for (let i = 0; i < (what === 'marbles' ? 4 : 3); i++) B.prop(what === 'marbles' ? 'marbles' : 'peel', x + (r() - 0.5) * w, y, z + (r() - 0.5) * d, r() * 6.28, 1, i);
  B.out.triggers.push({ kind: 'slip', box: [x - w / 2, y - 0.2, z - d / 2, x + w / 2, y + 0.6, z + d / 2], what });
}
// a secret alcove: a platform you can only swing to, with a stash crate, a ring above it and a mark for the quests
function alcove(B, id, x, y, z, o = {}) {
  if (!B.inside(x, z)) return;
  const w = o.w || 4;
  B.add(x - w / 2, y - 0.4, z - w / 2, x + w / 2, y, z + w / 2, o.mat || 'metal', { tint: o.tint || 0x8890a0 });
  B.prop('crate_soup', x, y, z, 0.3, 1, 0);
  hook(B, x, y + 5.5, z, {});
  B.light(x, y + 1.5, z, 0xff4fd8, 8, 0.8);
  B.out.marks.push({ id: 'secret.' + id, p: [x, y, z] });
}

// ---------------------------------------------------------------- the Bottom
export function playBottom(B) {
  const LS = SLICE.longStairs;
  // the Long Stairs: a hook gantry across every flight, so you can climb the whole hill without touching a step
  if (B.touches([LS.x0 - 6, 0, LS.x1 + 6, 256])) for (let k = 0; k < T.n; k++) {
    const zl = zSouth(k) - LANE, zt = k === T.n - 1 ? 0 : zSouth(k + 1), top = k === T.n - 1 ? SLICE.border.y : yOf(k + 1);
    const z = zl - (zl - zt) * 0.55, yStep = yOf(k) + (top - yOf(k)) * 0.55;
    gantry(B, LS.x0 - 1.8, LS.x1 + 1.8, z, yOf(k), yOf(k), yStep + 10, [0.5], { tint: [0xff7ab0, 0x5fd3c6, 0xffe14d][k % 3] });
  }
  // THE BANISTER: a slide chute down beside the Long Stairs, the whole hill (the lanes cross it on the flat; the lip walls
  // are open for it). slide on it and you hit the market at 30 m/s
  const bx0 = BANISTER[0], bx1 = BANISTER[1];
  if (B.touches([bx0 - 1, 0, bx1 + 1, 256])) for (let k = 0; k < T.n; k++) {
    const zl = zSouth(k) - LANE, zt = k === T.n - 1 ? 0 : zSouth(k + 1), top = k === T.n - 1 ? SLICE.border.y : yOf(k + 1), ya = yOf(k);
    const za = Math.max(B.Z0, zt), zb = Math.min(B.Z1, zl);
    if (!(zb > za && bx1 > B.X0 && bx0 < B.X1)) continue;
    const yAt = (z) => top + (ya - top) * (z - zt) / (zl - zt);
    rampZ(B, bx0, bx1, zb, za, yAt(zb), yAt(za), 'metal', { tint: 0xffe14d });
    B.out.triggers.push({ kind: 'slide', box: [bx0, Math.min(yAt(za), yAt(zb)) - 0.5, za, bx1, Math.max(yAt(za), yAt(zb)) + 3, zb + LANE], dir: [0, 0, 1], speed: 24, name: 'THE BANISTER' });
    for (const x of [bx0 - 0.15, bx1]) B.add(x, ya, za, x + 0.15, Math.max(yAt(za), yAt(zb)) + 0.35, zb, 'metal', { nc: true, tint: 0xff4fd8 }); // pink rails (look)
  }
  if (B.inside(bx0 + 1, -2)) B.out.marks.push({ id: 'bottom:banister_top', p: [bx0 + 1.1, SLICE.border.y + 1, -2] });
  // the market: four tall masts to swing round over the stalls, peels and marbles where the fruit stalls spill
  const [mx0, mz0, mx1, mz1] = SLICE.plaza.rect, mr = rng(7117);
  for (let i = 0; i < 4; i++) mast(B, mx0 + 12 + i * 22, (mz0 + mz1) / 2 + (i % 2 ? 4 : -4), 0, 13 + (i % 2) * 3, { tint: pick(mr, PASTEL) });
  for (let i = 0; i < 5; i++) slip(B, mx0 + 8 + i * 18 + mr() * 4, 0.02, mz0 + 8 + mr() * (mz1 - mz0 - 16), 3, 2.5, i % 2 ? 'marbles' : 'banana', mr);
  pad(B, mx0 + 4, 0, mz0 + 3, [0, 19, -9], 'UP AND OUT'); // the plaza's north edge: up onto terrace 1's roofs
  // the Lost & Found: a pad onto its roof, a mast over the hole; the Crow's Nest (grapple only) up the old crane
  const [lx0, lz0, lx1, lz1] = SLICE.lostFound.rect, ly = yOf(2);
  pad(B, lx0 - 3, ly, lz1 + 3, [2, 22, -6], 'ROOF PLEASE');
  mast(B, (lx0 + lx1) / 2, lz0 + 13, ly + 11.4, 8, { tint: 0xff4fd8 });
  const cx = lx1 + 10, cz = lz0 + 4;
  if (B.inside(cx, cz)) { B.add(cx - 0.5, ly, cz - 0.5, cx + 0.5, ly + 21, cz + 0.5, 'rust', { tint: 0xffb070 }); B.add(cx - 0.5, ly + 21, cz - 7, cx + 0.5, ly + 21.8, cz + 0.5, 'rust', { tint: 0xffb070 }); hook(B, cx, ly + 21 - 0.3, cz - 6.5, {}); }
  alcove(B, 'crows_nest', cx, ly + 21.8, cz, { w: 3, tint: 0xffb070 });
  // every lane's poles get rings (lane() hooks every other pole top); plus a mast at the top of each narrow stair
  for (let k = 1; k < T.n; k += 2) { const r = rng(hash2(k, 0x9a57)); for (let x = -300 + r() * 30; x < 80; x += 52 + r() * 30) if (!inRect(x - 4, zSouth(k) - 10, x + 4, zSouth(k), [LS.x0 - 8, 0, LS.x1 + 8, 256]) && !inRect(x - 4, zSouth(k) - 10, x + 4, zSouth(k), SLICE.lostFound.rect) && !inRect(x - 4, zSouth(k) - 10, x + 4, zSouth(k), SLICE.plaza.rect)) mast(B, x, zSouth(k) - LANE + 0.6, yOf(k), 12 + r() * 4, { tint: pick(r, PASTEL) }); }
}

// ---------------------------------------------------------------- the Gut
const GY = SLICE.gut.y;
export function playGut(B) {
  // Rib Avenue: a ring in every arch's crown, 18 m apart: swing the whole avenue
  const RA = SLICE.ribAve, rx = (RA.x0 + RA.x1) / 2;
  for (let z = -60; z > -250; z -= 18) if (!inRect(rx - 8, z - 2, rx + 8, z + 2, SLICE.arena.rect)) hook(B, rx, GY + 11.6, z, { s: 1.8 });
  // THE WISHBONE: a bone fork up out of the avenue's median with a ledge at the top. grapple only
  const wz = -213, wy = GY + 19;
  if (B.inside(rx, wz)) {
    for (const s of [-1, 1]) B.shape({ kind: 'tube', pts: [[rx + s * 3.2, GY - 0.5, wz], [rx + s * 2.6, GY + 8, wz], [rx + s * 1.2, GY + 15, wz], [rx, wy - 0.5, wz]], r: 0.55, seg: 8, mat: 'bone', tint: 0xc4b288, step: 1, at: [rx, GY, wz] });
    for (const s of [-1, 1]) B.add(rx + s * 3.2 - 0.5, GY, wz - 0.5, rx + s * 3.2 + 0.5, GY + 7, wz + 0.5, 'bone', { hide: true });
  }
  alcove(B, 'wishbone', rx, wy, wz, { w: 3.2, mat: 'bone', tint: 0xc4b288 });
  // THE RIB RUN: rib arches spanning Peristalsis Avenue from Rib Avenue west to the Big Stomach's rim, a ring in every
  // crown, lungs on the pavements between them (bounce to keep your height), down to the rim
  const P = SLICE.peri, pz = (P.z0 + P.z1) / 2, S0 = SLICE.stomach;
  for (let i = 0, x = rx - 18; x > S0.x + 8; i++, x -= 17) {
    // (x1.35: the avenue is a tube 8.5 m round, so the arches straddle it, legs on the pavements, crown over the top)
    if (B.inside(x, pz)) { B.prop('ribarch', x, GY, pz, Math.PI / 2, 1.35, 0); B.add(x - 1.2, GY, pz - 11.6, x + 1.2, GY + 9.5, pz - 9.4, 'bone', { hide: true }); B.add(x - 1.2, GY, pz + 9.4, x + 1.2, GY + 9.5, pz + 11.6, 'bone', { hide: true }); }
    hook(B, x, GY + 16.8, pz, { s: 2, yaw: Math.PI / 2 });
    const lx = x - 8.5, lz = i % 2 ? P.z0 - 5.5 : P.z1 + 5.5;
    if (B.inside(lx, lz)) { B.prop('lung', lx, GY, lz, i, 0.6, 0); B.add(lx - 1.6, GY, lz - 1.6, lx + 1.6, GY + 0.7, lz + 1.6, 'flesh', { hide: true }); B.out.triggers.push({ kind: 'bounce', box: [lx - 1.7, GY + 0.4, lz - 1.7, lx + 1.7, GY + 2.2, lz + 1.7], v: 22, name: 'LUNG' }); }
  }
  if (B.inside(S0.x + 4, pz)) B.out.marks.push({ id: 'route.rib_run_end', p: [S0.x + 4, GY, S0.z + S0.r + 2] });
  // the choir pipes: rings on the tall ones; the Big Stomach: rings round the rim to swing over the acid
  const C = SLICE.choir;
  for (let i = 0; i < 3; i++) { const a = -0.6 + i * 0.6; hook(B, C.x + Math.sin(a) * 14, GY + 17, C.z - Math.cos(a) * 14, { s: 1.6 }); }
  const S = SLICE.stomach;
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2, x = S.x + Math.cos(a) * (S.r * 0.55), z = S.z + Math.sin(a) * (S.r * 0.55); if (!B.inside(x, z)) continue; B.add(x - 0.3, GY + 14, z - 0.3, x + 0.3, GY + 24, z + 0.3, 'flesh', { nc: true, tint: 0x7a121c }); B.shape({ kind: 'blob', c: [x, GY + 24, z], r: [3, 1.4, 3], seg: 8, mat: 'flesh', tint: 0x8e1622, pulse: 4 }); hook(B, x, GY + 14, z, { s: 1.8 }); } // hanging from the membrane (tendons)
}

// ---------------------------------------------------------------- the Commute
export function playCommute(B) {
  const H = SLICE.highway, hx0 = H.x0, hx1 = H.x1;
  // sign gantries over the highway every 60 m (yellow, the old exit signs), two rings each: swing the jam
  for (let z = 220; z > H.zTop + 10; z -= 60) {
    if (z > 80 && z < 106) continue; // (the collapse)
    const y = hwY(z) + 8.5, g = hwY(z, true);
    gantry(B, hx0 - 1.2, hx1 + 1.2, z, Math.min(g, hwY(z)), Math.min(g, hwY(z)), y, [0.28, 0.72], { mat: 'metal', tint: 0x9aa0a8 });
    if (B.inside((hx0 + hx1) / 2, z)) B.add(hx0 + 6, y + 0.45, z - 0.1, hx1 - 6, y + 2.6, z + 0.1, 'paint', { tint: 0xffe14d }); // the sign board (EXIT 17:29)
  }
  // power poles: a ring on every other one (lines between them are the swing line up the east side)
  for (let z = Math.ceil(H.zTop / 30) * 30; z < H.zLow; z += 60) { const x = hx1 + 7, y = hwY(z, true); hook(B, x, y + 9.8, z, { s: 1.2 }); }
  // the fallen 13: a ring on top of the 1, and one on the 3
  const D = SLICE.digit, dy = hwY(D.z, true);
  hook(B, D.x - 5, dy + 15, D.z, { s: 1.6 }); hook(B, D.x + 3, dy + 14.4, D.z, { s: 1.6 });
  // THE PILE-UP: five wrecks stacked into a tower by the camp, a pad to get on, a ring on top; and on the board of the
  // first ☺ billboard north of the camp, the Smile's Hat: a ledge you can only swing to
  const px = 222, pz = -20, py = hwY(pz, true);
  if (B.inside(px, pz)) {
    for (let i = 0; i < 5; i++) { const yy = py + i * 1.6; B.prop('carwreck', px, yy, pz, i * 1.1, 1, i); B.add(px - 2.2, yy, pz - 2.2, px + 2.2, yy + 1.55, pz + 2.2, 'metal', { hide: true }); }
    hook(B, px, py + 8 + 4, pz, {});
  }
  pad(B, px + 6, py, pz, [-6, 17, 0], 'PILE ON');
  let bz = Math.ceil(H.zTop / 30) * 30;
  while ((Math.round(bz / 30) & 3) !== 1) bz += 30; // the first billboard (commute.js puts one where (z / 30) & 3 is 1)
  const bx = hx1 + 7 + 4.15, by = hwY(bz, true) + 12;
  alcove(B, 'smiles_hat', bx + 1.6, by + 0.2, bz, { w: 3.4, tint: 0xffe14d });
}
