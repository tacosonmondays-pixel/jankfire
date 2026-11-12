// Softer edges on the Gut border (the world lane's terrain pass). The border's ground switched from dirt to flesh along
// one ruler-straight line, and the 4 m tissue cliff up into the Gut had only its stairs. Now:
//   - the flesh creeps: lumpy patches of it spread south over the dirt (more the nearer the Gut), patches of dirt
//     still show through the flesh past the line, and big lobes straddle the line itself so it never reads straight
//   - flesh ramps lean against the cliff between the stairs: a walkable slope up from the border to the Gut's floor
//     (stepped collision under a smooth drawn slope, like the slip road's), veins and fat lumps along their edges
// gut.js border() calls it last. render-only patches, so the border's collision only gains the ramps.
import { SLICE } from './slice.js';
import { rng, hash2 } from './plan.js';
import { pick } from './kit.js';
import { inGateArena } from './arenas.js';
import { BEV } from './act1set.js';

const Y = SLICE.border.y, GY = SLICE.gut.y, LINE = -24, FLESH = [0x8a1822, 0x7a121c, 0x9a2430, 0x6a0c18];
// the ramps: [x where it starts (low, at the border's floor), x where it meets the cliff's top]. between the stairs
export const RAMPS = [[-266, -250], [-214, -198], [-162, -146], [-110, -94], [24, 40], [72, 88]];
const RZ = [-46, -42.8]; // (the strip between the cliff's face and the border's back row of houses)

function blot(B, x, z, rx, rz, mat, tint, r, y) { // a flat lumpy patch lying on the ground
  const wob = Array.from({ length: 14 }, () => 0.7 + r() * 0.5);
  B.shape({ kind: 'lathe', c: [x, y, z], sc: [rx, 1, rz], prof: [[1.12, 0, 0.6], [1, 0.02], [0, 0.02]], wob, seg: 14, mat, tint, uvxz: 1, lod: false, pulse: mat === 'flesh' ? 2 : 0 });
}

// the cliff face itself (z -46, 4 m of flesh up to the Gut's floor): it was one flat red rectangle. now it bulges,
// veins run down it, its lip is lumpy against the sky and fat and bone have slumped at its foot. render only: walking
// is unchanged (the stairs at the avenues and the ramps between them are the way up, and the art keeps clear of both)
const FACE = -46, AVE_X = [-286, -234, -182, -130, -44, 8, 60]; // (gut.js AVES and the gate: their bone stairs)
export function cliffSkin(B) {
  const X0 = Math.max(B.X0, SLICE.border.rect[0]), X1 = Math.min(B.X1, SLICE.border.rect[2]);
  if (X1 <= X0 || !B.touches([X0, FACE - 3, X1, FACE + 3])) return;
  const clear = (x, m) => !AVE_X.some((a) => Math.abs(x - a) < 3 + m) && !RAMPS.some(([a, b]) => x > a - m && x < b + m);
  for (let x = Math.ceil(X0 / 2.5) * 2.5; x < X1; x += 2.5) {
    const r = rng(hash2(Math.round(x * 4), 46, 0xc11f)), xx = x + (r() - 0.5) * 1.2;
    if (!clear(xx, 1.2)) continue;
    const arena = inGateArena(xx - 1, FACE - 1, xx + 1, FACE + 1);
    // a bulge half sunk in the face, or a fat lump
    const g = 0.9 + r() * 1.3;
    B.shape({ kind: 'blob', c: [xx, Y + 0.8 + r() * 2.4, FACE + 0.05], r: [g * 1.3, g * (0.7 + r() * 0.4), 0.45 + r() * 0.5], seg: 8, mat: r() < 0.25 ? 'fat' : 'flesh', tint: pick(r, FLESH), pulse: 2, at: [xx, Y, FACE + 0.1] });
    // a vein from the lip down to the foot, wandering
    if (r() < 0.55) { const pts = [], vx = xx + (r() - 0.5) * 2; for (let k = 0; k <= 4; k++) { const t = k / 4; pts.push([vx + Math.sin(t * 5 + x) * 0.5, GY + 0.15 - t * (GY - Y - 0.1), FACE + 0.12 + Math.sin(t * 3.1) * 0.06]); } B.shape({ kind: 'tube', pts, r: 0.1 + r() * 0.1, seg: 5, mat: 'flesh', tint: 0x4c0a14, pulse: 3, step: 1, at: [vx, Y, FACE + 0.15] }); }
    // the lip: a lumpy roll over the top edge (the straight line against the sky goes)
    B.shape({ kind: 'blob', c: [x + (r() - 0.5) * 0.6, GY - 0.05, FACE - 0.35], r: [1.6 + r() * 0.8, 0.35 + r() * 0.25, 0.75], seg: 7, mat: 'flesh', tint: pick(r, FLESH), pulse: 2, at: [x, GY, FACE - 0.3] });
    // what slumped off it: fat and bits of bone at the foot (not in the gate arena: its acid gutters run there)
    if (!arena && r() < 0.6) { const s = 0.4 + r() * 0.6; B.shape({ kind: 'blob', c: [xx + (r() - 0.5) * 1.5, Y + s * 0.3, FACE + 0.5 + r() * 0.7], r: [s * 1.4, s, s * 1.1], seg: 6, mat: r() < 0.5 ? 'fat' : 'flesh', tint: r() < 0.5 ? 0xa8804a : pick(r, FLESH), at: [xx, Y, FACE + 0.6] }); }
    if (!arena && r() < 0.3) B.obb(xx + (r() - 0.5) * 2, Y + 0.12, FACE + 0.6 + r() * 0.8, 0.9 + r() * 0.6, 0.18, 0.22, r() * 3.14, 'bone', { tint: 0xe8dcc0 });
  }
}

export function borderSoft(B) {
  const [rx0, rz0, rx1, rz1] = SLICE.border.rect, X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  const r = rng(hash2(B.out.cx, B.out.cz, 0xb0a5));
  // each patch on a layer of its own among the ones it overlaps (1.05 cm apart, 7 layers, all 1.5 cm under the houses' floors at 12 cm):
  // overlapping patches a few mm apart flickered
  const laid = [], lift = (x, z, rx, rz) => { const used = new Set(laid.filter((p) => Math.abs(p[0] - x) < p[2] + rx * 1.4 && Math.abs(p[1] - z) < p[3] + rz * 1.4).map((p) => p[4])); const k0 = ((B.out.cx * 3 + B.out.cz * 5) % 7 + 7) % 7; let k = k0, n = 0; while (used.has(k) && n++ < 6) k = (k + 1) % 7; /* (each chunk starts on its own layer: patches spill over the seams) */ laid.push([x, z, rx * 1.4, rz * 1.4, k]); return Y + 0.022 + 0.0105 * k; };
  // the creep: patches every few metres, flesh on the dirt side thinning out south, dirt on the flesh side thinning out north
  for (let i = 0; i < 70; i++) {
    const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0), d = z - LINE; // (d > 0: the dirt side)
    const want = d > 0 ? Math.pow(1 - Math.min(1, d / 24), 1.6) : 0.45 * Math.pow(1 - Math.min(1, -d / 18), 2);
    if (r() > want || inGateArena(x - 3, z - 3, x + 3, z + 3) || (x > BEV.rect[0] - 5 && x < BEV.rect[2] + 5 && z > BEV.rect[1] - 5 && z < BEV.rect[3] + 5)) continue; // (not through Bev's clinic floor)
    const s = 1.2 + r() * 3.2 * (d > 0 ? 1 : 0.7);
    const sz = s * (0.6 + r() * 0.6), tint = d > 0 ? pick(r, FLESH) : pick(r, [0xc0a0a0, 0xb09090, 0xa88888]); r(); // (the draw the old random height took)
    blot(B, x, z, s, sz, d > 0 ? 'flesh' : 'ground', tint, r, lift(x, z, s, sz));
  }
  for (let x = Math.ceil(X0 / 7) * 7; x < X1; x += 7) { // big lobes along the line: never a straight edge
    if (r() < 0.25 || inGateArena(x - 4, LINE - 4, x + 4, LINE + 4) || (x > BEV.rect[0] - 6 && x < BEV.rect[2] + 6 && LINE > BEV.rect[1] - 6 && LINE < BEV.rect[3] + 6)) continue;
    { const bx = x + (r() - 0.5) * 4, bz = LINE + (r() - 0.3) * 3, rx = 3 + r() * 2.5, rz = 2 + r() * 2.5; blot(B, bx, bz, rx, rz, 'flesh', pick(r, FLESH), r, lift(bx, bz, rx, rz)); }
  }
  cliffSkin(B);
  // the ramps up the cliff
  for (const [xa, xb] of RAMPS) {
    if (!B.touches([xa, RZ[0], xb, RZ[1]])) continue;
    const n = Math.ceil((GY - Y) / 0.12), dx = (xb - xa) / n, rr = rng(hash2(xa, 77, 0x4a3));
    for (let i = 0; i < n; i++) B.add(xa + i * dx, Y - 0.5, RZ[0], xa + (i + 1) * dx, Y + (GY - Y) * (i + 1) / n, RZ[1], 'flesh', { hide: true }); // (0.12 m treads: you just walk up)
    const ya = Y + 0.06, yb = GY + 0.06;
    B.shape({ kind: 'quad', q: [[xa, ya, RZ[1]], [xb, yb, RZ[1]], [xb, yb, RZ[0]], [xa, ya, RZ[0]]], mat: 'flesh', tint: 0x8a1822, at: [xa + 0.1, ya, RZ[0] + 0.1] });
    B.shape({ kind: 'quad', q: [[xa, Y, RZ[1]], [xb, Y, RZ[1]], [xb, yb, RZ[1]], [xa, ya, RZ[1]]], mat: 'flesh', tint: 0x6a0c18, at: [xa + 0.2, Y, RZ[0] + 0.1] }); // its open side
    const pts = []; for (let k = 0; k <= 8; k++) { const t = k / 8; pts.push([xa + (xb - xa) * t, ya + (yb - ya) * t + 0.15, RZ[1] - 0.25 + Math.sin(t * 9 + xa) * 0.12]); }
    B.shape({ kind: 'tube', pts, r: 0.22, seg: 6, mat: 'flesh', tint: 0x5a0c18, step: 1, pulse: 5, at: [xa + 0.3, ya, RZ[0] + 0.3] }); // a vein for a handrail
    for (let k = 0; k < 3; k++) { const t = rr(), g = 0.6 + rr() * 0.7; B.shape({ kind: 'blob', c: [xa + (xb - xa) * t, Y + (GY - Y) * t * 0.5, RZ[1] + 0.4 + rr() * 0.6], r: [g * 1.4, g, g], seg: 8, mat: rr() < 0.4 ? 'fat' : 'flesh', pulse: 5, at: [xa + 0.4, Y, RZ[0] + 0.4] }); }
    if (B.inside(xa + 0.1, RZ[0] + 0.1)) B.out.marks.push({ id: 'gut.flesh_ramp', p: [xa - 1, Y, (RZ[0] + RZ[1]) / 2] });
  }
}
