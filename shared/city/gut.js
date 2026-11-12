// THE GUT: Gristle & Sons' old office campus on the plateau, grown over with living tissue. Tooth-cobble streets, rib
// arches over the avenue north from the border gate, Peristalsis Avenue (an intestine tube street that carries you),
// lung trampolines, vein cables with glowing nodes, eyes in the gutters, the Big Stomach (a crater with an acid lake),
// the Choir Lung, Tooth Market, and the Clocking In arena (the first Mr. Overtime fight).
// THE GUT BORDER: the top of the Bottom, pastel houses half swallowed by flesh, the gate at the top of the Long Stairs.
import { SLICE, PLACES } from './slice.js';
import { rng, hash2 } from './plan.js';
import { FLAGS as CF } from './chunk.js';
import { cube, stairsZ, line, rubble, stall, flightLen, retaining, PASTEL, pick, hook } from './kit.js';
import { playGut } from './playground.js';
import { gateArena, inGateArena } from './arenas.js';
import { shops, shopRects } from './shops.js';
import { GUT_LINK } from './roads.js';
import { bigHeart } from './bigheart.js';
import { act1Gut, act1Border, BEV } from './act1set.js';

const GY = SLICE.gut.y;
const inRect = (x0, z0, x1, z1, r) => x0 < r[2] && x1 > r[0] && z0 < r[3] && z1 > r[1];
const FLESH = [0x8e1622, 0xa82430, 0x7a121c, 0xc23a40, 0x4c0a14, 0xa8804a, 0x34101e]; // the darker Gut (the owner's pick): raw red, wet highlight, fold, old fat, bruise

// the campus street grid: avenues every 52 m in x (the rib avenue is one of them), streets every 44 m in z
const AVES = [-286, -234, -182, -130, -44, 8, 60], STREETS = [-232, -188, -100, -60];
const SW = 10; // street width
function streetAt(x, z) {
  const S = SLICE;
  if (z > S.peri.z0 - 1 && z < S.peri.z1 + 1) return 'peri';
  if (x > S.ribAve.x0 && x < S.ribAve.x1) return 'ave';
  for (const a of AVES) if (Math.abs(x - a) < SW / 2) return 'ave';
  for (const s of STREETS) if (Math.abs(z - s) < SW / 2) return 'st';
  return null;
}
const stomachD = (x, z) => Math.hypot(x - SLICE.stomach.x, z - SLICE.stomach.z);
const KEEP = () => [SLICE.arena.rect, SLICE.teeth.rect, [SLICE.choir.x - 26, SLICE.choir.z - 30, SLICE.choir.x + 26, SLICE.choir.z + 22], [SLICE.stomach.x - SLICE.stomach.r - 14, SLICE.stomach.z - SLICE.stomach.r - 14, SLICE.stomach.x + SLICE.stomach.r + 14, SLICE.stomach.z + SLICE.stomach.r + 14], ...shopRects('gut'), GUT_LINK.rect];

// a campus office block grown over: grey office box, lit windows, flesh coating patches, blobs on the corners,
// a sphincter for a door, the Gristle & Sons sign on some, vein cables to the neighbour
function office(B, x0, z0, x1, z1, r) {
  const h = 9 + Math.floor(r() * 6) * 3, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  const tint = pick(r, [0xc8c4cc, 0xd8d0c8, 0xb8c0c8, 0xe0d4d8, 0xa8d8d0, 0xe8e0b0]); // the old campus: office grey, hospital mint, memo yellow
  B.add(x0, GY, z0, x1, GY + h, z1, 'concrete', { tint });
  for (let y = GY + 3; y < GY + h - 1; y += 3) for (const [a, b, c, d] of [[x0 + 1, z0 - 0.04, x1 - 1, z0], [x0 + 1, z1, x1 - 1, z1 + 0.04]]) B.add(a, y, b, c, y + 1.3, d, r() < 0.7 ? 'window' : 'glass', { nc: true });
  for (let y = GY + 3; y < GY + h - 1; y += 3) for (const [a, b, c, d] of [[x0 - 0.04, z0 + 1, x0, z1 - 1], [x1, z0 + 1, x1 + 0.04, z1 - 1]]) B.add(a, y, b, c, y + 1.3, d, r() < 0.7 ? 'window' : 'glass', { nc: true });
  // flesh coating: slabs of skin hanging down the walls from the roof (render only, a little proud of the wall)
  const sides = [[x0, z0 - 0.2, x1, z0, 'x', z0, Math.PI], [x0, z1, x1, z1 + 0.2, 'x', z1, 0], [x0 - 0.2, z0, x0, z1, 'z', x0, -Math.PI / 2], [x1, z0, x1 + 0.2, z1, 'z', x1, Math.PI / 2]];
  for (const [a, b, c, d, ax] of sides) {
    const n = 1 + (r() * 3 | 0);
    for (let i = 0; i < n; i++) {
      const len = ax === 'x' ? c - a : d - b, s0 = r() * len * 0.7, w = 3 + r() * len * 0.4, drop = 2 + r() * h * 0.8;
      if (ax === 'x') B.add(a + s0, GY + h - drop, b - 0.05, Math.min(c, a + s0 + w), GY + h + 0.3, d + 0.05, pick(r, ['flesh', 'flesh', 'liver', 'fat']), { nc: true, tint: pick(r, FLESH) });
      else B.add(a - 0.05, GY + h - drop, b + s0, c + 0.05, GY + h + 0.3, Math.min(d, b + s0 + w), pick(r, ['flesh', 'flesh', 'liver', 'fat']), { nc: true, tint: pick(r, FLESH) });
    }
  }
  B.add(x0 - 0.3, GY + h, z0 - 0.3, x1 + 0.3, GY + h + 0.6, z1 + 0.3, 'flesh', { tint: 0x9a1a26 }); // the roof has grown a skin
  for (const [px, pz] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1]]) if (r() < 0.55) B.prop(r() < 0.5 ? 'fleshblob_a' : 'fleshblob_b', px, GY + (r() < 0.5 ? 0 : h * r()), pz, r() * 6.28, 1 + r() * 0.8, 0);
  // a sphincter door on the street side, a sign above it on one block in three
  const doorZ = r() < 0.5 ? z0 : z1, yaw = doorZ === z0 ? 0 : Math.PI;
  if (r() < 0.2 && x1 - x0 > 10) { // the odd shop still open under the skin: SUDS & SONS, with its tongue out
    B.prop('launderette', cx, GY, doorZ + (doorZ === z0 ? -0.02 : 0.02), yaw, 1, 0);
    B.light(cx, GY + 2.5, doorZ + (doorZ === z0 ? -3 : 3), 0xfff0d0, 9, 0.8);
  } else B.prop(r() < 0.75 ? 'sphincter' : 'tongue', cx, GY, doorZ + (doorZ === z0 ? -0.05 : 0.05), yaw, 1, 0);
  if (r() < 0.35) B.prop('gristlelogo', cx, GY + h - 4, doorZ + (doorZ === z0 ? -0.1 : 0.1), yaw, 1, 0);
  for (let i = 0; i < 3; i++) B.out.marks.push({ id: 'crowd', p: [cx + (r() - 0.5) * (x1 - x0 + 6), GY, doorZ + (doorZ === z0 ? -3 : 3)], kind: pick(r, ['choir', 'digester', 'lost']) });
  return h;
}

// Peristalsis Avenue: an intestine tube street per chunk: the ribbed tube (inside out), the moving floor, a beat
function peri(B) {
  const P = SLICE.peri, x0 = Math.max(B.X0, P.x0), x1 = Math.min(B.X1, P.x1), zc = (P.z0 + P.z1) / 2;
  if (x1 <= x0) return;
  B.add(x0, GY - 0.02, P.z0, x1, GY + 0.04, P.z1, 'rib', { nc: true, tint: 0xa82430 });
  // the tube: a half-buried ribbed tube along the avenue, gaps where the avenues cross it
  const cuts = [SLICE.stomach.x, -44, ...AVES, PLACES['gut:digester_wall'].p[0]].filter((a) => a > x0 - 6 && a < x1 + 6).sort((a, b) => a - b); // (+ open in front of the Digester Wall, so you see it from the avenue)
  let s = x0;
  for (const c of [...cuts, x1 + 6]) {
    const e = Math.min(x1, c - 6);
    if (e - s > 6) B.shape({ kind: 'tube', pts: [[s, GY + 3, zc], [(s + e) / 2, GY + 3.4, zc], [e, GY + 3, zc]], r: 8.5, seg: 14, inside: true, ribs: 0.06, mat: 'rib', tint: 0xa82430, step: 1.4, pulse: 5 });
    s = c + 6;
  }
  // the walls of the tube are solid where the tube is (you ride it, you don't wander off through the side)
  B.out.triggers.push({ kind: 'conveyor', box: [x0, GY - 0.5, P.z0, x1, GY + 3, P.z1], dir: [1, 0, 0], speed: 16, beat: true, name: 'PERISTALSIS' });
  for (let x = Math.ceil(x0 / 9) * 9; x < x1; x += 9) B.prop('eyeball', x, GY, P.z0 + 0.2, Math.PI / 2, 1, 0);
  if (B.inside(-120, zc)) B.out.marks.push({ id: 'gut:peristalsis', p: [-120, GY, zc] });
}

// the Big Stomach: a crater ringed with teeth, its walls a ribbed stomach lining, acid lake at the bottom
function stomach(B, r) {
  const S = SLICE.stomach;
  const cell = 4;
  for (let x = Math.max(B.X0, S.x - S.r - 8); x < Math.min(B.X1, S.x + S.r + 8); x += cell) for (let z = Math.max(B.Z0, S.z - S.r - 8); z < Math.min(B.Z1, S.z + S.r + 8); z += cell) {
    const d = stomachD(x + cell / 2, z + cell / 2);
    if (d > S.r + 2) continue;
    // stepped bowl: 1.5 m rings down to the floor (walkable with a jump, climbable with the grapple)
    const t = Math.max(0, Math.min(1, (S.r - d) / (S.r * 0.75))), y = GY - Math.round(t * (GY - S.floor) / 1.5) * 1.5;
    B.add(x, S.floor - 6, z, x + cell, y, z + cell, d > S.r - 4 ? 'flesh' : t > 0.85 ? 'liver' : 'rib', { tint: t > 0.85 ? 0x4c0a14 : pick(r, FLESH) });
  }
  if (!B.touches([S.x - S.r, S.z - S.r, S.x + S.r, S.z + S.r])) return;
  // acid: a glowing lake you take damage in
  const ax0 = Math.max(B.X0, S.x - S.r * 0.4), ax1 = Math.min(B.X1, S.x + S.r * 0.4), az0 = Math.max(B.Z0, S.z - S.r * 0.4), az1 = Math.min(B.Z1, S.z + S.r * 0.4);
  B.light(S.x, S.acid + 1, S.z, 0xa6ff3a, 34, 1.3);
  if (ax1 > ax0 && az1 > az0) { B.add(ax0, S.floor, az0, ax1, S.acid, az1, 'acid', { nc: true }); B.out.triggers.push({ kind: 'acid', box: [ax0, S.floor - 1, az0, ax1, S.acid, az1], dps: 25 }); }
  // the rim: giant teeth, pulsing stomach folds, vein cables across
  for (let i = 0; i < 28; i++) {
    const a = (i / 28) * Math.PI * 2, x = S.x + Math.cos(a) * (S.r + 1), z = S.z + Math.sin(a) * (S.r + 1);
    if (B.inside(x, z)) B.prop(i % 3 ? 'tooth' : 'tooth_b', x, GY - 0.5, z, -a + Math.PI / 2, 9 + (i % 4) * 2, 0);
    const xa = S.x + Math.cos(a) * (S.r - 6), za = S.z + Math.sin(a) * (S.r - 6);
    B.shape({ kind: 'blob', c: [xa, GY - 4, za], r: [5, 3, 5], seg: 10, mat: pick(r, ['flesh', 'fat', 'liver']), pulse: 6 });
  }
  B.prop('sphincter', S.x, S.floor, S.z - S.r * 0.42, 0, 2, 0); // the belly button door (don't press it)
  if (B.inside(S.x, S.z)) B.out.marks.push({ id: 'gut:big_stomach', p: [S.x, GY, S.z + S.r + 4] }, { id: 'gut:belly_button', p: [S.x, S.floor, S.z - S.r * 0.42] });
}

// a lung trampoline: the model + a bounce pad
function lungPad(B, x, z, s = 1) {
  B.prop('lung', x, GY, z, 0, s, 0);
  B.add(x - 2.6 * s, GY, z - 2.6 * s, x + 2.6 * s, GY + 1.2 * s, z + 2.6 * s, 'flesh', { hide: true });
  B.out.triggers.push({ kind: 'bounce', box: [x - 2.8 * s, GY + 0.8 * s, z - 2.8 * s, x + 2.8 * s, GY + 3 * s, z + 2.8 * s], v: 24, name: 'LUNG' });
}

// Clocking In: the old time office (punch clocks on the wall), a plaza with lungs to bounce over his slams
function arena(B) {
  const [x0, z0, x1, z1] = SLICE.arena.rect, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  B.add(x0, GY - 0.02, z0, x1, GY + 0.05, z1, 'gums', { nc: true });
  // ribs over the plaza (it's a ribcage now), mounds round the edge, the old time-office's queue rails
  for (const az of [z0 + 18, z1 - 16]) if (B.inside(cx, az)) { B.prop('ribarch', cx, GY, az, 0, 1.5, 0); B.add(cx - 13, GY, az - 1.2, cx - 10.5, GY + 9, az + 1.2, 'bone', { hide: true }); B.add(cx + 10.5, GY, az - 1.2, cx + 13, GY + 9, az + 1.2, 'bone', { hide: true }); }
  for (const [mx, mz] of [[x0 + 4, cz], [x1 - 4, cz - 8], [x0 + 26, z1 - 4], [x1 - 26, z0 + 22]]) if (B.inside(mx, mz)) B.prop(mx < cx ? 'fleshblob_a' : 'fleshblob_b', mx, GY, mz, mx < cx ? 0.5 : -0.5, 1.6, 0);
  for (let x = x0 + 14; x < x1 - 14; x += 6) if (B.inside(x, z0 + 6)) B.add(x, GY, z0 + 5.9, x + 4, GY + 1.0, z0 + 6.1, 'metal', { nc: true, tint: 0xd0c8b8 });
  // the time office along the north side, its front a wall of punch clocks (glow faces)
  // (an arcade through it where Rib Avenue runs, so the avenue goes on north: walk it or swing it)
  const RA = SLICE.ribAve;
  B.add(x0 + 10, GY, z0 - 14, RA.x0, GY + 14, z0, 'concrete', { tint: 0xd8d4cc }); B.add(RA.x1, GY, z0 - 14, x1 - 10, GY + 14, z0, 'concrete', { tint: 0xd8d4cc });
  B.add(RA.x0, GY + 9, z0 - 14, RA.x1, GY + 14, z0, 'concrete', { tint: 0xc8c4bc });
  hook(B, (RA.x0 + RA.x1) / 2, GY + 8.2, z0 - 7, { s: 1.2 }); // a ring in the arcade's ceiling
  for (let x = x0 + 12; x < x1 - 12; x += 3) if (x + 1.6 < SLICE.ribAve.x0 || x > SLICE.ribAve.x1) B.add(x, GY + 2, z0 + 0.01, x + 1.6, GY + 3.6, z0 + 0.05, 'window', { nc: true, tint: 0xfff0c0 });
  B.add(x0 + 10, GY + 14, z0 - 14, x1 - 10, GY + 15, z0, 'flesh', { tint: 0x9a1a26 });
  B.prop('gristlelogo', cx, GY + 9, z0 + 0.1, Math.PI, 1.4, 0);
  for (const [lx, lz] of [[x0 + 12, z0 + 12], [x1 - 12, z0 + 12], [x0 + 12, z1 - 12], [x1 - 12, z1 - 12]]) if (B.inside(lx, lz)) lungPad(B, lx, lz, 0.9);
  // low flesh walls round the edge (cover, and a ring he can't charge out of)
  for (const [a, b, c, d] of [[x0, z1 - 1, cx - 8, z1], [cx + 8, z1 - 1, x1, z1], [x0, z0, x0 + 1, z1], [x1 - 1, z0, x1, z1]]) B.add(a, GY, b, c, GY + 1.4, d, 'flesh', { tint: 0x7a121c });
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'landmark.time_office', p: [cx, GY, cz] }); // (Overtime's fight 1 moved to the Gut Border Gate: arenas.js)
}

function choir(B, r) {
  const C = SLICE.choir;
  if (!B.touches([C.x - 30, C.z - 34, C.x + 30, C.z + 26])) return;
  B.add(C.x - 24, GY - 0.02, C.z - 28, C.x + 24, GY + 0.05, C.z + 20, 'bone', { nc: true, tint: 0xc4b288 });
  // the cathedral is a lung: a huge breathing blob over a bone colonnade, windpipe organ pipes in a ring
  B.shape({ kind: 'blob', c: [C.x, GY + 16, C.z - 4], r: [20, 15, 18], seg: 18, mat: 'flesh', tint: 0xa82430, pulse: 7 });
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2, x = C.x + Math.cos(a) * 21, z = C.z - 4 + Math.sin(a) * 19;
    if (Math.sin(a) > 0.75) continue; // the doorway (south)
    B.add(x - 1, GY, z - 1, x + 1, GY + 10, z + 1, 'bone', { tint: 0xccba92 });
    B.prop('choirpipe', x, GY + 10, z, -a, 1, 0);
  }
  B.add(C.x - 20, GY + 9, C.z - 24, C.x + 20, GY + 10, C.z + 16, 'flesh', { hide: true }); // the inside ceiling (collision for grapples)
  if (B.inside(C.x, C.z)) B.out.marks.push({ id: 'gut:choir_lung', p: [C.x, GY, C.z + 18] });
  for (let i = 0; i < 8; i++) B.out.marks.push({ id: 'crowd', p: [C.x + (r() - 0.5) * 30, GY, C.z - 4 + (r() - 0.5) * 26], kind: 'choir' });
}

function toothMarket(B, r) {
  const [x0, z0, x1, z1] = SLICE.teeth.rect;
  B.add(x0, GY - 0.02, z0, x1, GY + 0.05, z1, 'gums', { nc: true });
  for (let i = 0; i < 10; i++) stall(B, x0 + 6 + (i % 5) * 12, GY, z0 + 8 + Math.floor(i / 5) * 30, i < 5 ? 0 : 2, r);
  for (let i = 0; i < 6; i++) B.prop('organjar', x0 + 8 + i * 9, GY, z0 + 20, r() * 6.28, 1, 0);
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  B.prop('tooth_b', cx, GY, cz, 0.4, 14, 0); B.add(cx - 3, GY, cz - 3, cx + 3, GY + 9, cz + 3, 'teeth', { hide: true }); // the Wisdom Tooth
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'gut:tooth_market', p: [cx, GY, z1 - 4] }, { id: 'gut.wisdom_tooth', p: [cx, GY, cz] });
}

// a bile or blood puddle: no square tiles, and it goes DOWN, not up (the owner: "the puddles should go down not
// protrude"). one lumpy outline (a lathe with a wobble): a dark stain flush on the skin round it, a dark wall dropping
// 0.34 m from the outline, and the goo lying at the bottom of that. the ground's picture gets a hole for it (cutHoles,
// below); the ground's collision does not, so you, bots and cars still cross it as flat floor (no pits to get stuck
// in), and nothing about the district's collision moves. on its own dice.
// the goo shape carries goo: [x, z, r, y] for the client (bubbles that pop, the mist going green over it: gutgoo.js)
const PIT = 0.34, P_GOO = [[0.94, -0.72], [0, -0.72]], P_WALL = [[1, 0], [0.97, -0.25], [0.92, -1]], P_STAIN = [[1.22, 1], [1, 1]];
function puddle(B, cx, cz, rx, rz, blood, joined, X0, Z0, X1, Z1) {
  const q = rng(hash2(Math.round(cx * 8), Math.round(cz * 8), 0xb11e)), N = 20, wob = [];
  const k2 = joined ? 0.3 : 0.1 + q() * 0.1, p2 = q() * 6.283, k3 = 0.08 + q() * 0.08, p3 = q() * 6.283, k5 = 0.04 + q() * 0.04, p5 = q() * 6.283;
  for (let i = 0; i < N; i++) { const t = i / N * 6.283; wob.push(Math.max(0.6, 1 + k2 * Math.cos(2 * t + p2) + k3 * Math.cos(3 * t + p3) + k5 * Math.cos(5 * t + p5))); }
  // the hole is the outline's bounding box; it has to sit inside this chunk (the next chunk knows nothing about it)
  const wm = Math.max(...wob), hx = rx * wm + 0.05, hz = rz * wm + 0.05;
  if (X1 - X0 < 2 * hx + 0.5 || Z1 - Z0 < 2 * hz + 0.5) return;
  cx = Math.min(X1 - hx - 0.2, Math.max(X0 + hx + 0.2, cx)); cz = Math.min(Z1 - hz - 0.2, Math.max(Z0 + hz + 0.2, cz));
  if (!B.inside(cx, cz) || stomachD(cx, cz) < SLICE.stomach.r + 5 + Math.max(hx, hz) || inRect(cx - hx, cz - hz, cx + hx, cz + hz, SLICE.arena.rect)) return;
  (B.holes || (B.holes = [])).push([cx - hx, cz - hz, cx + hx, cz + hz]);
  const ring = (prof, h, mat, tint, o) => B.shape({ kind: 'lathe', c: [cx, GY, cz], sc: [rx, h, rz], prof, wob, seg: N, mat, tint, lod: false, ...o });
  // the stain: lumpy at the pool's lip, a round edge wide enough to cover the hole's corners, a hair over the skin
  const f = 1.45 * wm;
  ring([[f, 1, 0], [f * 0.8, 1, 0.4], [1, 1]], 0.02, 'flesh', blood ? 0x74101c : 0x76161c, { uvxz: 1 });
  ring([[1.55, 1, 0.7], [1, 1]], 0.028, 'flesh', blood ? 0x520c16 : 0x541416, { uvxz: 1 });
  ring(P_STAIN, 0.036, 'flesh', blood ? 0x30070d : 0x2e1109, { uvxz: 1 });
  ring(P_WALL, PIT, 'flesh', blood ? 0x22050a : 0x200c07, { pulse: 0 });
  ring(P_GOO, PIT, blood ? 'blood' : 'bile', blood ? 0x8a0a20 : 0xb8ff4a, blood ? { pulse: 0 } : { goo: [cx, cz, Math.max(rx, rz), GY - PIT * 0.72] });
  if (!blood) B.light(cx, GY + 0.45, cz, 0xa6e22e, 4 + Math.max(rx, rz), 0.6); // every bile pool glows a bit
}
// the holes the pools need in the ground's picture. a ground slab keeps its collision and is still drawn far off
// (L1), and up close is drawn as strips round the hole (L0, no collision); thin things lying on the ground (the
// street cobbles) are cut the same way. called last, when everything flat is down.
function cutHoles(B) {
  const F = CF.NC | CF.L0, out = B.out.boxes;
  for (const [hx0, hz0, hx1, hz1] of B.holes || []) for (let i = out.length - 1; i >= 0; i--) {
    const b = out[i], slab = b[1] === -4 && b[4] === GY && !(b[7] & (CF.HIDE | CF.L1)), skin = b[7] & CF.NC && !(b[7] & CF.L1) && b[4] <= GY + 0.06 && (b[1] >= GY - 1e-6 || (b[1] === -4 && b[4] === GY));
    if (!(slab || skin) || b[0] >= hx1 || b[3] <= hx0 || b[2] >= hz1 || b[5] <= hz0) continue;
    const fl = skin ? b[7] : F, add = (x0, z0, x1, z1) => { if (x1 - x0 > 0.01 && z1 - z0 > 0.01) out.push([x0, b[1], z0, x1, b[4], z1, b[6], fl, b[8]]); };
    add(b[0], b[2], b[3], Math.min(b[5], hz0)); add(b[0], Math.max(b[2], hz1), b[3], b[5]); // the strips north and south of the hole
    add(b[0], Math.max(b[2], hz0), Math.min(b[3], hx0), Math.min(b[5], hz1)); add(Math.max(b[0], hx1), Math.max(b[2], hz0), b[3], Math.min(b[5], hz1)); // west and east
    if (skin) out.splice(i, 1); else b[7] |= CF.L1;
  }
}

export function gut(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect, r = rng(hash2(B.out.cx, B.out.cz, 0x6a7));
  const X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  // ground: the plateau in 16 m tiles (the Big Stomach's cells cut it out), flesh with tooth-cobble streets on top
  const S = SLICE.stomach;
  for (let x = X0; x < X1; x += 16) for (let z = Z0; z < Z1; z += 16) {
    const xe = Math.min(X1, x + 16), ze = Math.min(Z1, z + 16);
    if (inRect(x, z, xe, ze, [S.x - S.r - 2, S.z - S.r - 2, S.x + S.r + 2, S.z + S.r + 2])) {
      // tiles that overlap the crater: fill only the 4 m cells outside the bowl
      for (let a = x; a < xe; a += 4) for (let b = z; b < ze; b += 4) if (stomachD(a + 2, b + 2) > S.r + 2) B.add(a, -4, b, Math.min(xe, a + 4), GY, Math.min(ze, b + 4), 'flesh', { tint: 0x86141f });
      continue;
    }
    const gr = rng(hash2(Math.floor(x / 16), Math.floor(z / 16), 0x9f));
    B.add(x, -4, z, xe, GY, ze, gr() < 0.7 ? 'flesh' : gr() < 0.5 ? 'liver' : 'bruise', { tint: pick(gr, [0x8e1622, 0x7c121c, 0x9a1c28, 0x6a0e18, 0x84141f]) });
  }
  // bile puddles (glowing), fat mounds, a tissue membrane overhead here and there ("it's a ceiling in places")
  for (let i = 0; i < 9; i++) {
    const x = X0 + r() * (X1 - X0 - 6), z = Z0 + r() * (Z1 - Z0 - 6), w = 2 + r() * 5, d0 = 2 + r() * 4;
    if (stomachD(x, z) < S.r + 4 || KEEP().slice(1, 2).some((q) => inRect(x, z, x + w, z + d0, q))) continue;
    const blood = i % 2 === 1;
    puddle(B, x + w / 2, z + d0 / 2, w * 0.56, d0 * 0.56, blood, i % 3 === 0, X0, Z0, X1, Z1);
  }

  // streets: tooth cobbles (texture) with real teeth scattered at the edges, eyes in the gutters, heart lamps
  for (let x = Math.floor(X0 / 2) * 2; x < X1; x += 2) for (let z = Math.floor(Z0 / 2) * 2; z < Z1; z += 2) {
    const s = streetAt(x + 1, z + 1);
    if (!s || s === 'peri' || stomachD(x, z) < S.r + 3) continue;
    B.add(x, GY, z, x + 2, GY + 0.03, z + 2, 'gums', { nc: true });
    if (r() < 0.06) B.prop(r() < 0.7 ? 'tooth' : 'tooth_b', x + r() * 2, GY, z + r() * 2, r() * 6.28, 0.8 + r() * 0.6, 0);
  }
  for (const a of AVES) if (a > X0 - 6 && a < X1 + 6) for (let z = Math.ceil(Z0 / 16) * 16; z < Z1; z += 16) {
    if (streetAt(a, z) === 'peri' || stomachD(a, z) < S.r + 6 || KEEP().some((q) => inRect(a - 6, z - 2, a + 6, z + 2, q))) continue;
    B.prop('heartlamp', a + SW / 2 + 0.3, GY, z, Math.PI, 1, 0); B.light(a + SW / 2, GY + 4.5, z, 0xd01c2c, 11, 1.1); B.prop('eyeball', a - SW / 2 + 0.2, GY, z + 6, -Math.PI / 2, 1, 0);
  }
  // the rib avenue: arches every 18 m from the gate north
  const RA = SLICE.ribAve, rx = (RA.x0 + RA.x1) / 2;
  if (rx > X0 - 10 && rx < X1 + 10) for (let z = -60; z > -250; z -= 18) if (B.inside(rx, z) && !inRect(rx - 8, z - 2, rx + 8, z + 2, SLICE.arena.rect)) { B.prop('ribarch', rx, GY, z, 0, 1, 0); B.add(rx - 8.6, GY, z - 0.9, rx - 7, GY + 7, z + 0.9, 'bone', { hide: true }); B.add(rx + 7, GY, z - 0.9, rx + 8.6, GY + 7, z + 0.9, 'bone', { hide: true }); }
  // campus blocks between the streets
  const keep = KEEP();
  const xs = [-320, ...AVES.map((a) => [a - SW / 2, a + SW / 2]).flat(), 96], zs = [-256, ...STREETS.map((s) => [s - SW / 2, s + SW / 2]).flat(), SLICE.peri.z0 - 1, SLICE.peri.z1 + 1, -48].sort((a, b) => a - b);
  const xsS = [...xs].sort((a, b) => a - b);
  for (let i = 0; i + 1 < xsS.length; i += 2) for (let j = 0; j + 1 < zs.length; j++) {
    const bx0 = xsS[i] + 2, bx1 = xsS[i + 1] - 2, bz0 = zs[j] + 2, bz1 = zs[j + 1] - 2;
    if (bx1 - bx0 < 10 || bz1 - bz0 < 10) continue;
    if (!B.touches([bx0, bz0, bx1, bz1])) continue;
    if (inRect(bx0, bz0, bx1, bz1, [SLICE.peri.x0, SLICE.peri.z0 - 1, SLICE.peri.x1, SLICE.peri.z1 + 1])) continue;
    // each block: 1-3 offices along it, gaps between (lungs and vein cables in the gaps)
    const br = rng(hash2(i, j, 0xb10c)), n = Math.max(1, Math.min(3, Math.floor((bx1 - bx0) / 16)));
    const w = (bx1 - bx0) / n;
    for (let k = 0; k < n; k++) {
      const ox0 = bx0 + k * w + 1.5, ox1 = bx0 + (k + 1) * w - 1.5, oz0 = bz0 + 1, oz1 = bz1 - 1;
      if (keep.some((q) => inRect(ox0, oz0, ox1, oz1, q)) || stomachD((ox0 + ox1) / 2, (oz0 + oz1) / 2) < S.r + 16) { if (br() < 0.3) br(); continue; }
      const h = office(B, ox0, oz0, ox1, oz1, rng((br() * 4294967296) >>> 0));
      if (k < n - 1 && br() < 0.6) line(B, [ox1, GY + h * 0.7, (oz0 + oz1) / 2], [ox1 + 3, GY + h * 0.6, (oz0 + oz1) / 2 + 2], { r: 0.18, mat: 'liver' });
      if (k < n - 1 && br() < 0.35) { const lx = ox1 + 1.5, lz = (oz0 + oz1) / 2; if (B.inside(lx, lz)) lungPad(B, lx, lz, 0.5); }
    }
    // vein cables across the street to the next block (they glow)
    if (br() < 0.7) { const vz = bz0 + 4 + br() * (bz1 - bz0 - 8), vx = bx1 + 2; if (B.inside(vx, vz)) { const vy = GY + 9 + br() * 4; B.prop('veincable', vx + SW / 2, vy, vz, 0, (SW + 6) / 4, 0); hook(B, vx + SW / 2, vy + 0.3, vz, { s: 1.4 }); } }
  }
  // the guts themselves: intestines arcing out of the ground over the streets and back in, veins across the cobbles,
  // wet mounds with eyes. seeded per chunk, anchored in it (keep clear of the arena and the stomach's bowl)
  const keepG = KEEP();
  for (let i = 0; i < 4; i++) {
    const ax = X0 + 6 + r() * (X1 - X0 - 12), az = Z0 + 6 + r() * (Z1 - Z0 - 12), ang = r() * 6.283, len = 14 + r() * 22;
    const bx = ax + Math.cos(ang) * len, bz = az + Math.sin(ang) * len, h = 6 + r() * 10, rad = 1.1 + r() * 1.6;
    if ([keepG[0], ...shopRects('gut')].some((q) => inRect(Math.min(ax, bx) - 4, Math.min(az, bz) - 4, Math.max(ax, bx) + 4, Math.max(az, bz) + 4, q)) || stomachD(ax, az) < S.r + 4) continue; // (not over the arena or a shopfront)
    const mx = (ax + bx) / 2 + (r() - 0.5) * 8, mz = (az + bz) / 2 + (r() - 0.5) * 8;
    B.shape({ kind: 'tube', pts: [[ax, GY - 1.5, az], [ax + (mx - ax) * 0.4, GY + h * 0.8, az + (mz - az) * 0.4], [mx, GY + h, mz], [bx + (mx - bx) * 0.4, GY + h * 0.8, bz + (mz - bz) * 0.4], [bx, GY - 1.5, bz]], r: rad, seg: 10, ribs: 0.12, mat: r() < 0.7 ? 'flesh' : 'fat', tint: pick(r, FLESH), step: 1.0, pulse: 5 });
    B.shape({ kind: 'blob', c: [ax, GY, az], r: [rad * 2, rad * 0.9, rad * 2], seg: 8, mat: 'liver', pulse: 3 });
    hook(B, mx, GY + h + rad + 0.65, mz, { s: 1.6 }); // a grapple ring on the crown (swing the guts)
    B.shape({ kind: 'blob', c: [bx, GY, bz], r: [rad * 2, rad * 0.9, rad * 2], seg: 8, mat: 'liver', pulse: 3, at: [bx, GY, bz] });
  }
  for (let i = 0; i < 10; i++) { // veins: thin purple-red tubes snaking along the ground
    const ax = X0 + r() * (X1 - X0), az = Z0 + r() * (Z1 - Z0), pts = [[ax, GY + 0.05, az]];
    let x = ax, z = az, a = r() * 6.283;
    for (let k = 0; k < 5; k++) { a += (r() - 0.5) * 1.4; x += Math.cos(a) * 3; z += Math.sin(a) * 3; pts.push([x, GY + 0.05 + r() * 0.1, z]); }
    if (stomachD(ax, az) > S.r + 2) B.shape({ kind: 'tube', pts, r: 0.08 + r() * 0.1, seg: 5, mat: r() < 0.5 ? 'bruise' : 'liver', step: 1.5, pulse: 2, lod: false });
  }
  for (let i = 0; i < 3; i++) { // wet mounds with a staring eye
    const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0);
    if (streetAt(x, z) || stomachD(x, z) < S.r + 6 || keepG.some((q) => inRect(x - 3, z - 3, x + 3, z + 3, q))) continue;
    const s0 = 1.5 + r() * 2;
    B.shape({ kind: 'blob', c: [x, GY, z], r: [s0, s0 * 0.7, s0], seg: 10, mat: pick(r, ['flesh', 'fat', 'flesh']), tint: pick(r, FLESH), pulse: 6 });
    B.prop('eyeball', x, GY + s0 * 0.55, z, r() * 6.28, s0 * 0.5, 0);
  }
  if (B.touches([SLICE.peri.x0, SLICE.peri.z0, SLICE.peri.x1, SLICE.peri.z1])) peri(B);
  if (B.touches([S.x - S.r - 10, S.z - S.r - 10, S.x + S.r + 10, S.z + S.r + 10])) stomach(B, r);
  if (B.touches(SLICE.arena.rect, 16)) arena(B);
  choir(B, r);
  if (B.touches(SLICE.teeth.rect, 2)) toothMarket(B, r);
  playGut(B); // grapple rings, the Wishbone (playground.js)
  act1Gut(B); // act I: the Digester Wall (act1set.js)
  shops(B, 'gut'); // Meat Mechanics, Bone Arms, the Tooth Market's stalls, vending (shops.js)
  bigHeart(B); // the Big Heart: its collision, light and mark (bigheart.js)
  cutHoles(B); // the pools' pits (last: the ground and the cobbles are all down)
}

// the border: the Bottom's top houses, half eaten. ground creeps from pastel to flesh going north; the gate at the
// top of the Long Stairs; a 3 m tissue cliff along z = -48 with steps up into the Gut at the avenues and the gate
export function border(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect, y = SLICE.border.y;
  const X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  for (let z = Z0; z < Z1; z += 8) { const t = (0 - z) / 48; B.add(X0, -4, z, X1, y, Math.min(Z1, z + 8), t > 0.5 ? 'flesh' : 'ground', { tint: t > 0.5 ? 0x8a1822 : 0xc0a0a0 }); }
  // the cliff up into the Gut: flesh, with steps at the gate and the avenues
  if (Z0 <= -48 + 0.1 && Z1 > -48) { // (the chunk holds the cliff line)
    B.add(X0, y, -48, X1, SLICE.gut.y, -46, 'flesh', { tint: 0x7a121c });
  }
  if (B.touches([X0, -50, X1, -40])) for (const a of [-44, ...AVES]) if (a > X0 - 4 && a < X1 + 4) stairsZ(B, a - 3, a + 3, -48 + flightLen(SLICE.gut.y - y), -1, y, SLICE.gut.y, 'bone', { tint: 0xc4b288 });
  // the south lip (down to the Bottom's top terrace): a retaining wall with stairs every ~60 m (the Long Stairs has its own)
  if (Z1 >= 0 && Z0 < 0) {
    const top8 = (SLICE.bottom.n - 1) * SLICE.bottom.rise;
    retaining(B, X0, X1, 0, top8, y, rng(hash2(B.out.cx, 0, 0x11)));
    for (let sx = -290; sx < 90; sx += 58) if (sx > X0 - 2 && sx < X1 + 2 && Math.abs(sx + 44) > 10 && Math.abs(sx + 112) > 8) stairsZ(B, sx - 1.2, sx + 1.2, flightLen(y - top8), -1, top8, y, 'concrete');
  }
  // houses along two rows, eaten more the further north they are
  const G = SLICE.gate, r0 = rng(hash2(B.out.cx, B.out.cz, 0xb0d));
  for (let row = 0; row < 2; row++) {
    const zz0 = row ? -36 : -18, zz1 = row ? -22 : -4, eat = row ? 0.8 : 0.4;
    const lr = rng(row * 31 + 7);
    for (let x = -318; x < 92;) {
      const w = 6 + Math.floor(lr() * 4) * 1.5, seed = (lr() * 4294967296) >>> 0, gap = lr() < 0.2 ? 3 : 0.5;
      const lx0 = x + gap; x += gap + w;
      if (lx0 + w < X0 - 6 || lx0 > X1 + 6) continue;
      if (Math.abs(lx0 + w / 2 - G.x) < 14 || Math.abs(lx0 + w / 2 + 112) < 8) continue; // the gate's avenue, the escalator top
      if (inGateArena(lx0, zz0, lx0 + w, zz1)) continue; // Overtime's arena (arenas.js builds its own houses)
      if (inRect(lx0, zz0, lx0 + w, zz1, BEV.rect)) continue; // Bev's clinic stands on this plot (act1set.js)
      const hr = rng(seed), floors = 1 + (hr() * 3 | 0);
      let fy = y;
      for (let f = 0; f < floors; f++) {
        const c = cube(B, lx0 + w / 2, fy, (zz0 + zz1) / 2, w - 0.5, zz1 - zz0 - 0.5, 2.8, hr, { door: f ? 1 : 2 });
        if (hr() < eat) B.prop(hr() < 0.5 ? 'fleshblob_a' : 'fleshblob_b', lx0 + w * hr(), fy + hr() * 2, zz0 + hr() * (zz1 - zz0), hr() * 6.28, 1 + hr(), 0);
        if (hr() < eat * 0.7) B.add(c.x0 - 0.1, fy + 2.8 * hr(), c.z0 - 0.15, c.x0 + (c.x1 - c.x0) * (0.3 + hr() * 0.6), c.top + 0.2, c.z0 + 0.05, 'flesh', { nc: true, tint: pick(hr, FLESH) });
        fy = c.top;
      }
      if (hr() < 0.4) B.prop('veincable', lx0 + w / 2, fy + 1, zz1 + 2, Math.PI / 2, 1.5, 0);
    }
  }
  // the gate: the arch at the top of the Long Stairs, flesh-swallowed pastel, the Gristle & Sons sign over it
  if (B.inside(G.x, G.z)) {
    B.prop('gutgate', G.x, y, G.z, Math.PI, 1, 0); // faces the Long Stairs (south)
    B.add(G.x - 9, y, G.z - 1.5, G.x - 6, y + 12, G.z + 1.5, 'flesh', { hide: true }); B.add(G.x + 6, y, G.z - 1.5, G.x + 9, y + 12, G.z + 1.5, 'flesh', { hide: true });
    B.add(G.x - 9, y + 10, G.z - 1.5, G.x + 9, y + 13, G.z + 1.5, 'flesh', { hide: true });
    B.out.marks.push({ id: 'gut:stairs_top', p: [G.x, y, G.z + 6], face: 0 });
  }
  for (let i = 0; i < 4; i++) { const cx = X0 + r0() * (X1 - X0), cz = Z0 + r0() * (Z1 - Z0); if (cz > -21 && cz < -19) B.out.marks.push({ id: 'crowd', p: [cx, y, cz], kind: 'lost' }); }
  gateArena(B); // THE GUT BORDER GATE (arenas.js)
  act1Border(B); // act I: Bev's clinic (act1set.js)
}

// the slice's edges: nobody walks off the world. west: a wall of stacked containers; south: a rubble berm; north:
// a cliff of tissue (the Gut keeps going up the hill); east: a collapsed overpass and a rubble cliff
export function edges(B) {
  const r = rng(hash2(B.out.cx, B.out.cz, 0xed6e));
  const S = SLICE;
  if (B.X0 <= S.x0) for (let z = B.Z0; z < B.Z1; z += 6) { const top = (z < -48 ? S.gut.y : 0) + 10 + r() * 16; B.add(S.x0, -4, z, S.x0 + 6, top, z + 6, z < -48 ? 'flesh' : 'container', { tint: z < -48 ? pick(r, FLESH) : pick(r, [0xff7a9a, 0x5fd3c6, 0xffd24d, 0x9a7aff, 0xff9a4d]) }); }
  if (B.Z1 >= S.z1) for (let x = B.X0; x < B.X1; x += 8) { B.add(x, -4, S.z1 - 5, x + 8, 7 + r() * 5, S.z1, 'rubble', { tint: 0xa89890 }); rubble(B, x + 4, 7, S.z1 - 6, 4 + r() * 3, r); }
  if (B.Z0 <= S.z0) for (let x = B.X0; x < B.X1; x += 8) { const g = x < 96 ? S.gut.y : 30; B.add(x, -4, S.z0, x + 8, g + 30 + r() * 20, S.z0 + 5, 'flesh', { tint: pick(r, FLESH) }); if (r() < 0.5) B.shape({ kind: 'blob', c: [x + 4, g + 12 + r() * 20, S.z0 + 6], r: [5, 6, 3], seg: 10, mat: 'flesh', pulse: 6 }); }
  if (B.X1 >= S.x1) for (let z = B.Z0; z < B.Z1; z += 8) { const g = Math.max(0, Math.min(30, (244 - z) / 394 * 30)); B.add(S.x1 - 6, -4, z, S.x1, g + 14 + r() * 10, z + 8, 'rubble', { tint: 0xb09080 }); }
}
export { PLACES };
