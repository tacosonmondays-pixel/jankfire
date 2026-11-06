// THE GUT: Gristle & Sons' old office campus on the plateau, grown over with living tissue. Tooth-cobble streets, rib
// arches over the avenue north from the border gate, Peristalsis Avenue (an intestine tube street that carries you),
// lung trampolines, vein cables with glowing nodes, eyes in the gutters, the Big Stomach (a crater with an acid lake),
// the Choir Lung, Tooth Market, and the Clocking In arena (the first Mr. Overtime fight).
// THE GUT BORDER: the top of the Bottom, pastel houses half swallowed by flesh, the gate at the top of the Long Stairs.
import { SLICE, PLACES } from './slice.js';
import { rng, hash2 } from './plan.js';
import { cube, stairsZ, line, rubble, stall, flightLen, retaining, PASTEL, pick } from './kit.js';

const GY = SLICE.gut.y;
const inRect = (x0, z0, x1, z1, r) => x0 < r[2] && x1 > r[0] && z0 < r[3] && z1 > r[1];
const FLESH = [0xff6f91, 0xff8aa6, 0xe85a7a, 0xffa0b4];

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
const KEEP = () => [SLICE.arena.rect, SLICE.teeth.rect, [SLICE.choir.x - 26, SLICE.choir.z - 30, SLICE.choir.x + 26, SLICE.choir.z + 22], [SLICE.stomach.x - SLICE.stomach.r - 14, SLICE.stomach.z - SLICE.stomach.r - 14, SLICE.stomach.x + SLICE.stomach.r + 14, SLICE.stomach.z + SLICE.stomach.r + 14]];

// a campus office block grown over: grey office box, lit windows, flesh coating patches, blobs on the corners,
// a sphincter for a door, the Gristle & Sons sign on some, vein cables to the neighbour
function office(B, x0, z0, x1, z1, r) {
  const h = 9 + Math.floor(r() * 6) * 3, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  const tint = pick(r, [0xc8c4cc, 0xd8d0c8, 0xb8c0c8, 0xe0d4d8]);
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
  B.add(x0 - 0.3, GY + h, z0 - 0.3, x1 + 0.3, GY + h + 0.6, z1 + 0.3, 'flesh', { tint: 0xe86a88 }); // the roof has grown a skin
  for (const [px, pz] of [[x0, z0], [x1, z0], [x0, z1], [x1, z1]]) if (r() < 0.55) B.prop(r() < 0.5 ? 'fleshblob_a' : 'fleshblob_b', px, GY + (r() < 0.5 ? 0 : h * r()), pz, r() * 6.28, 1 + r() * 0.8, 0);
  // a sphincter door on the street side, a sign above it on one block in three
  const doorZ = r() < 0.5 ? z0 : z1, yaw = doorZ === z0 ? 0 : Math.PI;
  B.prop('sphincter', cx, GY, doorZ + (doorZ === z0 ? -0.05 : 0.05), yaw, 1, 0);
  if (r() < 0.35) B.prop('gristlelogo', cx, GY + h - 4, doorZ + (doorZ === z0 ? -0.1 : 0.1), yaw, 1, 0);
  for (let i = 0; i < 3; i++) B.out.marks.push({ id: 'crowd', p: [cx + (r() - 0.5) * (x1 - x0 + 6), GY, doorZ + (doorZ === z0 ? -3 : 3)], kind: pick(r, ['choir', 'digester', 'lost']) });
  return h;
}

// Peristalsis Avenue: an intestine tube street per chunk: the ribbed tube (inside out), the moving floor, a beat
function peri(B) {
  const P = SLICE.peri, x0 = Math.max(B.X0, P.x0), x1 = Math.min(B.X1, P.x1), zc = (P.z0 + P.z1) / 2;
  if (x1 <= x0) return;
  B.add(x0, GY - 0.02, P.z0, x1, GY + 0.04, P.z1, 'rib', { nc: true, tint: 0xff7a96 });
  // the tube: a half-buried ribbed tube along the avenue, gaps where the avenues cross it
  const cuts = [SLICE.stomach.x, -44, ...AVES].filter((a) => a > x0 - 6 && a < x1 + 6).sort((a, b) => a - b);
  let s = x0;
  for (const c of [...cuts, x1 + 6]) {
    const e = Math.min(x1, c - 6);
    if (e - s > 6) B.shape({ kind: 'tube', pts: [[s, GY + 3, zc], [(s + e) / 2, GY + 3.4, zc], [e, GY + 3, zc]], r: 8.5, seg: 14, inside: true, ribs: 0.06, mat: 'rib', tint: 0xff8aa6, step: 1.4, pulse: 5 });
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
    B.add(x, S.floor - 6, z, x + cell, y, z + cell, d > S.r - 4 ? 'flesh' : t > 0.85 ? 'liver' : 'rib', { tint: t > 0.85 ? 0x9a3050 : pick(r, FLESH) });
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
  B.add(x0, GY - 0.02, z0, x1, GY + 0.05, z1, 'tile', { nc: true, tint: 0xc8c0b0 });
  // the time office along the north side, its front a wall of punch clocks (glow faces)
  B.add(x0 + 10, GY, z0 - 14, x1 - 10, GY + 14, z0, 'concrete', { tint: 0xd8d4cc });
  for (let x = x0 + 12; x < x1 - 12; x += 3) B.add(x, GY + 2, z0 + 0.01, x + 1.6, GY + 3.6, z0 + 0.05, 'window', { nc: true, tint: 0xfff0c0 });
  B.add(x0 + 10, GY + 14, z0 - 14, x1 - 10, GY + 15, z0, 'flesh', { tint: 0xe86a88 });
  B.prop('gristlelogo', cx, GY + 9, z0 + 0.1, Math.PI, 1.4, 0);
  for (const [lx, lz] of [[x0 + 12, z0 + 12], [x1 - 12, z0 + 12], [x0 + 12, z1 - 12], [x1 - 12, z1 - 12]]) if (B.inside(lx, lz)) lungPad(B, lx, lz, 0.9);
  // low flesh walls round the edge (cover, and a ring he can't charge out of)
  for (const [a, b, c, d] of [[x0, z1 - 1, cx - 8, z1], [cx + 8, z1 - 1, x1, z1], [x0, z0, x0 + 1, z1], [x1 - 1, z0, x1, z1]]) B.add(a, GY, b, c, GY + 1.4, d, 'flesh', { tint: 0xd85a78 });
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'gut:border', p: [cx, GY, cz] }, { id: 'boss.overtime.spawn', p: [cx, GY, z0 + 8], face: 0 }, { id: 'boss.overtime.entry', p: [cx, GY, z1 - 3], face: Math.PI });
}

function choir(B, r) {
  const C = SLICE.choir;
  if (!B.touches([C.x - 30, C.z - 34, C.x + 30, C.z + 26])) return;
  B.add(C.x - 24, GY - 0.02, C.z - 28, C.x + 24, GY + 0.05, C.z + 20, 'bone', { nc: true, tint: 0xf0e0d0 });
  // the cathedral is a lung: a huge breathing blob over a bone colonnade, windpipe organ pipes in a ring
  B.shape({ kind: 'blob', c: [C.x, GY + 16, C.z - 4], r: [20, 15, 18], seg: 18, mat: 'flesh', tint: 0xff8aa6, pulse: 7 });
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2, x = C.x + Math.cos(a) * 21, z = C.z - 4 + Math.sin(a) * 19;
    if (Math.sin(a) > 0.75) continue; // the doorway (south)
    B.add(x - 1, GY, z - 1, x + 1, GY + 10, z + 1, 'bone', { tint: 0xf4ead8 });
    B.prop('choirpipe', x, GY + 10, z, -a, 1, 0);
  }
  B.add(C.x - 20, GY + 9, C.z - 24, C.x + 20, GY + 10, C.z + 16, 'flesh', { hide: true }); // the inside ceiling (collision for grapples)
  if (B.inside(C.x, C.z)) B.out.marks.push({ id: 'gut:choir_lung', p: [C.x, GY, C.z + 18] });
  for (let i = 0; i < 8; i++) B.out.marks.push({ id: 'crowd', p: [C.x + (r() - 0.5) * 30, GY, C.z - 4 + (r() - 0.5) * 26], kind: 'choir' });
}

function toothMarket(B, r) {
  const [x0, z0, x1, z1] = SLICE.teeth.rect;
  B.add(x0, GY - 0.02, z0, x1, GY + 0.05, z1, 'teeth', { nc: true });
  for (let i = 0; i < 10; i++) stall(B, x0 + 6 + (i % 5) * 12, GY, z0 + 8 + Math.floor(i / 5) * 30, i < 5 ? 0 : 2, r);
  for (let i = 0; i < 6; i++) B.prop('organjar', x0 + 8 + i * 9, GY, z0 + 20, r() * 6.28, 1, 0);
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  B.prop('tooth_b', cx, GY, cz, 0.4, 14, 0); B.add(cx - 3, GY, cz - 3, cx + 3, GY + 9, cz + 3, 'teeth', { hide: true }); // the Wisdom Tooth
  if (B.inside(cx, cz)) B.out.marks.push({ id: 'gut:tooth_market', p: [cx, GY, z1 - 4] }, { id: 'gut.wisdom_tooth', p: [cx, GY, cz] });
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
      for (let a = x; a < xe; a += 4) for (let b = z; b < ze; b += 4) if (stomachD(a + 2, b + 2) > S.r + 2) B.add(a, -4, b, Math.min(xe, a + 4), GY, Math.min(ze, b + 4), 'flesh', { tint: 0xd86a80 });
      continue;
    }
    const gr = rng(hash2(Math.floor(x / 16), Math.floor(z / 16), 0x9f));
    B.add(x, -4, z, xe, GY, ze, gr() < 0.7 ? 'flesh' : gr() < 0.5 ? 'liver' : 'bruise', { tint: pick(gr, [0xd86a80, 0xc85a78, 0xe07a8a, 0xb84a6a, 0xd0607a]) });
  }
  // bile puddles (glowing), fat mounds, a tissue membrane overhead here and there ("it's a ceiling in places")
  for (let i = 0; i < 5; i++) {
    const x = X0 + r() * (X1 - X0 - 6), z = Z0 + r() * (Z1 - Z0 - 6), w = 2 + r() * 5, d0 = 2 + r() * 4;
    if (stomachD(x, z) < S.r + 4 || KEEP().slice(0, 1).some((q) => inRect(x, z, x + w, z + d0, q))) continue;
    B.add(x, GY, z, x + w, GY + 0.05, z + d0, 'bile', { nc: true, tint: 0xb8ff4a });
    if (i < 2) B.light(x + w / 2, GY + 0.6, z + d0 / 2, 0xa6e22e, 6, 0.6);
  }
  if (r() < 0.5) { const mx = X0 + 10 + r() * (X1 - X0 - 20), mz = Z0 + 10 + r() * (Z1 - Z0 - 20); if (stomachD(mx, mz) > S.r + 30) B.shape({ kind: 'blob', c: [mx, GY + 26 + r() * 8, mz], r: [18 + r() * 10, 2.2, 14 + r() * 8], seg: 14, mat: 'flesh', tint: 0xc85070, pulse: 7 }); }
  // streets: tooth cobbles (texture) with real teeth scattered at the edges, eyes in the gutters, heart lamps
  for (let x = Math.floor(X0 / 2) * 2; x < X1; x += 2) for (let z = Math.floor(Z0 / 2) * 2; z < Z1; z += 2) {
    const s = streetAt(x + 1, z + 1);
    if (!s || s === 'peri' || stomachD(x, z) < S.r + 3) continue;
    B.add(x, GY, z, x + 2, GY + 0.03, z + 2, 'teeth', { nc: true });
    if (r() < 0.06) B.prop(r() < 0.7 ? 'tooth' : 'tooth_b', x + r() * 2, GY, z + r() * 2, r() * 6.28, 0.8 + r() * 0.6, 0);
  }
  for (const a of AVES) if (a > X0 - 6 && a < X1 + 6) for (let z = Math.ceil(Z0 / 16) * 16; z < Z1; z += 16) {
    if (streetAt(a, z) === 'peri' || stomachD(a, z) < S.r + 6 || KEEP().some((q) => inRect(a - 6, z - 2, a + 6, z + 2, q))) continue;
    B.prop('heartlamp', a + SW / 2 + 0.3, GY, z, Math.PI, 1, 0); B.light(a + SW / 2, GY + 4.5, z, 0xff3060, 11, 1.1); B.prop('eyeball', a - SW / 2 + 0.2, GY, z + 6, -Math.PI / 2, 1, 0);
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
    if (br() < 0.7) { const vz = bz0 + 4 + br() * (bz1 - bz0 - 8), vx = bx1 + 2; if (B.inside(vx, vz)) B.prop('veincable', vx + SW / 2, GY + 9 + br() * 4, vz, 0, (SW + 6) / 4, 0); }
  }
  // the guts themselves: intestines arcing out of the ground over the streets and back in, veins across the cobbles,
  // wet mounds with eyes. seeded per chunk, anchored in it (keep clear of the arena and the stomach's bowl)
  const keepG = KEEP();
  for (let i = 0; i < 4; i++) {
    const ax = X0 + 6 + r() * (X1 - X0 - 12), az = Z0 + 6 + r() * (Z1 - Z0 - 12), ang = r() * 6.283, len = 14 + r() * 22;
    const bx = ax + Math.cos(ang) * len, bz = az + Math.sin(ang) * len, h = 6 + r() * 10, rad = 1.1 + r() * 1.6;
    if (keepG.slice(0, 1).some((q) => inRect(Math.min(ax, bx), Math.min(az, bz), Math.max(ax, bx), Math.max(az, bz), q)) || stomachD(ax, az) < S.r + 4) continue;
    const mx = (ax + bx) / 2 + (r() - 0.5) * 8, mz = (az + bz) / 2 + (r() - 0.5) * 8;
    B.shape({ kind: 'tube', pts: [[ax, GY - 1.5, az], [ax + (mx - ax) * 0.4, GY + h * 0.8, az + (mz - az) * 0.4], [mx, GY + h, mz], [bx + (mx - bx) * 0.4, GY + h * 0.8, bz + (mz - bz) * 0.4], [bx, GY - 1.5, bz]], r: rad, seg: 10, ribs: 0.12, mat: r() < 0.7 ? 'flesh' : 'fat', tint: pick(r, FLESH), step: 1.0, pulse: 5 });
    B.shape({ kind: 'blob', c: [ax, GY, az], r: [rad * 2, rad * 0.9, rad * 2], seg: 8, mat: 'liver', pulse: 3 });
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
}

// the border: the Bottom's top houses, half eaten. ground creeps from pastel to flesh going north; the gate at the
// top of the Long Stairs; a 3 m tissue cliff along z = -48 with steps up into the Gut at the avenues and the gate
export function border(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect, y = SLICE.border.y;
  const X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  for (let z = Z0; z < Z1; z += 8) { const t = (0 - z) / 48; B.add(X0, -4, z, X1, y, Math.min(Z1, z + 8), t > 0.5 ? 'flesh' : 'ground', { tint: t > 0.5 ? 0xd87088 : 0xc0a0a0 }); }
  // the cliff up into the Gut: flesh, with steps at the gate and the avenues
  if (Z0 <= -48 + 0.1 && Z1 > -48) { // (the chunk holds the cliff line)
    B.add(X0, y, -48, X1, SLICE.gut.y, -46, 'flesh', { tint: 0xe06a86 });
  }
  if (B.touches([X0, -50, X1, -40])) for (const a of [-44, ...AVES]) if (a > X0 - 4 && a < X1 + 4) stairsZ(B, a - 3, a + 3, -48 + flightLen(SLICE.gut.y - y), -1, y, SLICE.gut.y, 'bone', { tint: 0xf0e0d0 });
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
    B.prop('gutgate', G.x, y, G.z, 0, 1, 0);
    B.add(G.x - 9, y, G.z - 1.5, G.x - 6, y + 12, G.z + 1.5, 'flesh', { hide: true }); B.add(G.x + 6, y, G.z - 1.5, G.x + 9, y + 12, G.z + 1.5, 'flesh', { hide: true });
    B.add(G.x - 9, y + 10, G.z - 1.5, G.x + 9, y + 13, G.z + 1.5, 'flesh', { hide: true });
    B.out.marks.push({ id: 'gut:stairs_top', p: [G.x, y, G.z + 6], face: 0 });
  }
  for (let i = 0; i < 4; i++) { const cx = X0 + r0() * (X1 - X0), cz = Z0 + r0() * (Z1 - Z0); if (cz > -21 && cz < -19) B.out.marks.push({ id: 'crowd', p: [cx, y, cz], kind: 'lost' }); }
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
