// THE COMMUTE (the slice's strip): the old ring road climbing the hill's east side from the Bottom (y 0) up to the Gut
// (y 30), jammed with the dead traffic of the Final Quarter's evening rush. A collapsed span you have to jump, the Unpaid
// raider camp under it (filing-cabinet barricades, tents, a war-rig made of a bus and desks), the wasteland on terraces
// either side with ruined shells, paper drifts and a fallen glowing 7 stuck in the tarmac.
// The jam is the traversal gimmick: car roofs make a road (cars are props with real collision boxes).
import { SLICE, hwY } from './slice.js';
import { rng, hash2 } from './plan.js';
import { rubble, line, PASTEL, pick } from './kit.js';
import { playCommute } from './playground.js';
import { shops, shopRects } from './shops.js';
import { slipRoad, SLIP } from './roads.js';
import { act1Commute } from './act1set.js';

const H = SLICE.highway;
const GAP = [86, 100]; // the collapsed span (z)
const CAR = [[-2.2, 0.3, -0.92, 2.2, 0.95, 0.92], [-1.1, 0.95, -0.8, 0.9, 1.55, 0.8]]; // a car's collision (front +x)

function wreck(B, x, y, z, yaw4, r, id = 'carwreck') {
  const L = B.local(x, z, yaw4, y);
  for (const [a, b, c, d, e, f] of CAR) L(a, b, c, d, e, f, 'rust', { hide: true });
  L.P(id, 0, 0, 0, -Math.PI / 2 + (r() - 0.5) * 0.3, 1, (r() * 8) | 0); // the model's front is -z, the boxes' +x
}

export function commute(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect, r = rng(hash2(B.out.cx, B.out.cz, 0xc0e));
  const X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  // wasteland ground: 2 m steps following the climb (a ramp of terraces), ash-orange dirt
  for (let z = Z0; z < Z1; z += 4) {
    const zc = z + 2, top = z < H.westZ[1] && z + 4 > -256 ? hwY(H.zTop, true) : hwY(zc, true);
    B.add(X0, -4, z, X1, top, Math.min(Z1, z + 4), z < -150 ? 'ash' : 'ground', { tint: z < -150 ? 0x8a7a78 : 0xc8a078 });
  }
  // the highway deck: ~0.12 m steps (smooth to drive and run), crash barriers, lane paint; the gap at the collapse
  const hx0 = H.x0, hx1 = H.x1;
  if (B.touches([hx0 - 2, H.zTop - 40, hx1 + 2, H.zLow + 12])) {
    for (let z = Math.max(Z0, H.zTop); z < Math.min(Z1, H.zLow); z += 1.5) {
      if (z + 1.5 > GAP[0] && z < GAP[1]) continue;
      const y = hwY(z + 0.75);
      B.add(hx0, y - 1.2, z, hx1, y, Math.min(z + 1.5, Z1), 'road', { tint: 0x5a5658, hide: true }); // collision steps (0.11 m: you just roll up them)
      const ze = Math.min(z + 1.5, Z1), ya = hwY(z) + 0.07, yb = hwY(ze) + 0.07; // ...drawn as one smooth slope just above them
      B.shape({ kind: 'quad', q: [[hx0, ya, z], [hx1, ya, z], [hx1, yb, ze], [hx0, yb, ze]], mat: 'road', tint: 0x5a5658, at: [hx0, ya, z] });
      B.shape({ kind: 'quad', q: [[hx0, ya - 1.2, z], [hx0, ya, z], [hx0, yb, ze], [hx0, yb - 1.2, ze]], mat: 'concrete', tint: 0xa8a098, at: [hx0, ya, z] });
      B.shape({ kind: 'quad', q: [[hx1, ya, z], [hx1, ya - 1.2, z], [hx1, yb - 1.2, ze], [hx1, yb, ze]], mat: 'concrete', tint: 0xa8a098, at: [hx1, ya, z] });
      B.add(hx0 - 0.6, y, z, hx0, y + 1, Math.min(z + 1.5, Z1), 'concrete', { tint: 0xd0c8c0 });
      B.add(hx1, y, z, hx1 + 0.6, y + 1, Math.min(z + 1.5, Z1), 'concrete', { tint: 0xd0c8c0 });
      if (Math.floor(z / 6) % 2 === 0) B.shape({ kind: 'quad', q: [[(hx0 + hx1) / 2 - 0.12, ya + 0.02, z], [(hx0 + hx1) / 2 + 0.12, ya + 0.02, z], [(hx0 + hx1) / 2 + 0.12, yb + 0.02, ze], [(hx0 + hx1) / 2 - 0.12, yb + 0.02, ze]], mat: 'paint', tint: 0xffe14d, at: [(hx0 + hx1) / 2, ya, z] });
    }
    // pillars under the deck where it's high
    for (let z = Math.ceil(Math.max(Z0, H.zTop) / 24) * 24; z < Math.min(Z1, H.zLow); z += 24) {
      const y = hwY(z), g = hwY(z, true) - 4;
      if (y - g > 3 && !(z > GAP[0] - 4 && z < GAP[1] + 4)) for (const px of [hx0 + 3, hx1 - 3]) B.add(px - 1, g, z - 1, px + 1, y - 1.2, z + 1, 'concrete', { tint: 0xbab0a8 });
    }
    // jersey barriers closing the lanes before the collapse, cones, the stopped district clock at the on-ramp
    for (const [z, s] of [[GAP[0] - 3, 1], [GAP[1] + 3, -1]]) for (let x = hx0 + 2; x < hx1 - 1; x += 3.2) if (B.inside(x, z)) { B.prop('jersey', x, hwY(z), z, (s > 0 ? 0 : Math.PI) + (r() - 0.5) * 0.3, 1, 0); B.add(x - 1.5, hwY(z), z - 0.35, x + 1.5, hwY(z) + 0.85, z + 0.35, 'concrete', { hide: true }); }
    if (B.inside(hx1 + 2.5, 238)) { B.prop('brokenclock', hx1 + 2.5, hwY(238, true), 238, Math.PI / 2, 1, 0); B.add(hx1 + 2.3, hwY(238, true), 237.8, hx1 + 2.7, hwY(238, true) + 5, 238.2, 'metal', { hide: true }); }
    // the collapse: the broken ends hang down, slabs in the gap below
    for (const [z, s] of [[GAP[0], -1], [GAP[1], 1]]) if (z >= Z0 && z < Z1) B.obb((hx0 + hx1) / 2, hwY(z) - 1.6, z + s * 1.5, hx1 - hx0, 0.8, 4, 0, 'concrete', { tint: 0xa8a098 });
    if (B.touches([hx0, GAP[0], hx1, GAP[1]])) rubble(B, (hx0 + hx1) / 2, hwY(93, true), 93, 8, r);
    // the jam: dead cars nose to tail, two lanes each way, the odd bus; some on their roofs, some on fire
    const jr = rng(4711);
    for (let z = H.zTop + 6; z < H.zLow - 4; z += 5.2 + jr() * 2) {
      for (const lane of [0.18, 0.4, 0.62, 0.84]) {
        const go = jr();
        if (go < 0.2 || (z > GAP[0] - 6 && z < GAP[1] + 6)) continue;
        const x = hx0 + (hx1 - hx0) * lane + (jr() - 0.5) * 0.8, y = hwY(z);
        if (!B.inside(x, z)) continue;
        if (go > 0.96) { B.prop('bus', x, y, z, Math.PI / 2 + (jr() - 0.5) * 0.2, 1, 0); B.add(x - 1.3, y, z - 5.5, x + 1.3, y + 3.1, z + 5.5, 'rust', { hide: true }); z += 7; continue; }
        wreck(B, x, y, z, 1, jr);
        if (jr() < 0.05) B.prop('skeleton_lanyard', x + 1.3, y, z + (jr() - 0.5), -Math.PI / 2, 1, 0); // still waiting to get home
        if (jr() < 0.04) B.prop('cone', x + 1.6, y, z + 2.6, jr() * 6.28, 1, 0);
        if (jr() < 0.07) { B.prop('firebarrel', x + 1.5, y, z, 0, 1, 0); B.light(x + 1.5, y + 1.6, z, 0xff8a2a, 9, 1); }
      }
    }
    // the west turn into the Gut at the top
    for (let x = Math.max(X0, 96); x < Math.min(X1, hx0); x += 1.5) {
      const [za, zb] = H.westZ;
      if (zb < Z0 || za > Z1) continue;
      B.add(x, H.yTop - 1.2, Math.max(za, Z0), Math.min(x + 1.5, X1), H.yTop, Math.min(zb, Z1), 'road', { tint: 0x5a5658 });
    }
    B.add(Math.max(X0, hx0), H.yTop - 1.2, Math.max(Z0, H.westZ[0]), Math.min(X1, hx1), H.yTop, Math.min(Z1, H.zTop), 'road', { tint: 0x5a5658 });
    if (B.inside(182, 236)) B.out.marks.push({ id: 'commute:ring_road', p: [182, hwY(236), 236] });
  }
  // ruined shells on the wasteland: broken walls of pre-war shops, sun-bleached, no roofs
  const keepOut = [...SLIP.rects, [96, H.westZ[0] - 3, hx0, H.westZ[1] + 3], [hx0 - 6, -256, hx1 + 6, 256], [SLICE.camp.x - 36, SLICE.camp.z - 30, SLICE.camp.x + 36, SLICE.camp.z + 44], [SLICE.digit.x - 14, SLICE.digit.z - 14, SLICE.digit.x + 14, SLICE.digit.z + 14], ...shopRects('commute')];
  for (let i = 0; i < 6; i++) {
    const x = X0 + 6 + r() * (X1 - X0 - 12), z = Z0 + 6 + r() * (Z1 - Z0 - 12);
    if (keepOut.some((q) => x > q[0] && x < q[2] && z > q[1] && z < q[3])) continue;
    const y = hwY(z, true), w = 8 + r() * 8, dd = 6 + r() * 6, h = 2 + r() * 6, tint = pick(r, PASTEL);
    B.add(x - w / 2, y, z - dd / 2, x + w / 2, y + h, z - dd / 2 + 0.4, 'brick', { tint });
    B.add(x - w / 2, y, z - dd / 2, x - w / 2 + 0.4, y + h * (0.4 + r() * 0.6), z + dd / 2, 'brick', { tint });
    if (r() < 0.6) B.add(x + w / 2 - 0.4, y, z - dd / 2, x + w / 2, y + h * r(), z + dd / 2, 'brick', { tint });
    rubble(B, x + (r() - 0.5) * w, y, z + (r() - 0.5) * dd, 2 + r() * 3, r);
    B.prop(r() < 0.5 ? 'rubble_a' : 'rubble_b', x + (r() - 0.5) * w * 0.6, y, z + dd / 2 + 1.5, r() * 6.28, 0.8 + r() * 0.6, 0);
    if (r() < 0.5) B.prop('brokenwall', x, y, z + dd / 2 - 0.2, Math.PI, 1, 0); // a shopfront with a blast shadow on it
    if (r() < 0.5) B.prop('filecab', x, y, z, r() * 6.28, 1, 0);
  }
  for (let i = 0; i < 5; i++) { const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0); if (!keepOut.some((q) => x > q[0] && x < q[2] && z > q[1] && z < q[3])) wreck(B, x, hwY(z, true), z, (r() * 4) | 0, r); }
  // the Unpaid camp under the highway: a ring of filing-cabinet barricades, tents, fire barrels, the war-rig
  const C = SLICE.camp;
  if (B.touches([C.x - 26, C.z - 22, C.x + 26, C.z + 22])) {
    const y = hwY(C.z, true), cr = rng(8080);
    for (let i = 0; i < 26; i++) {
      const a = (i / 26) * Math.PI * 2, x = C.x + Math.cos(a) * 22, z = C.z + Math.sin(a) * 18;
      if (Math.abs(Math.cos(a)) < 0.2 && Math.sin(a) > 0) continue; // the way in (south)
      if (!B.inside(x, z) || (x > hx0 - 2 && x < hx1 + 2)) continue;
      B.add(x - 1.2, y, z - 1.2, x + 1.2, y + 1.6, z + 1.2, 'metal', { hide: true });
      B.prop(cr() < 0.7 ? 'filecab' : 'officechair', x, y, z, -a, 1, 0);
    }
    for (let i = 0; i < 5; i++) { const x = C.x - 14 + i * 7, z = C.z - 8 + (i % 2) * 14; if (B.inside(x, z) && !(x > hx0 - 2 && x < hx1 + 2)) { B.prop('raidertent', x, y, z, i * 1.3, 1, 0); B.add(x - 1.5, y, z - 1.5, x + 1.5, y + 2, z + 1.5, 'tarp', { hide: true }); } }
    for (let i = 0; i < 4; i++) { const x = C.x + (cr() - 0.5) * 30, z = C.z + (cr() - 0.5) * 24; if (B.inside(x, z)) B.prop('firebarrel', x, y, z, 0, 1, 0); B.light(x, y + 1.6, z, 0xff8a2a, 11, 1.2); }
    if (B.inside(C.x + 12, C.z + 4)) { B.prop('bus', C.x + 12, y, C.z + 4, 0.2, 1, 0); B.add(C.x + 6, y, C.z + 2.7, C.x + 18, y + 3.1, C.z + 5.3, 'rust', { hide: true }); }
    for (let i = 0; i < 4; i++) { const x = C.x - 18 + i * 12, z = C.z - 14 + (i % 2) * 28; if (B.inside(x, z) && !(x > hx0 - 2 && x < hx1 + 2)) { B.prop('tirestack', x, y, z, i, 1, 0); B.add(x - 0.6, y, z - 0.6, x + 0.6, y + 1.6, z + 0.6, 'rubble', { hide: true }); } }
    if (B.inside(C.x, C.z)) B.out.marks.push({ id: 'commute:unpaid_camp', p: [C.x, y, C.z + 20] }, ...Array.from({ length: 8 }, (_, k) => ({ id: 'enemy.unpaid', p: [C.x + Math.cos(k) * 12, y, C.z + Math.sin(k) * 10], face: k })));
  }
  // the fallen 13: a giant glowing orbital digit stuck in the tarmac, a ring of glassed ground (a hot zone)
  const D = SLICE.digit;
  if (B.touches([D.x - 14, D.z - 14, D.x + 14, D.z + 14])) {
    const y = hwY(D.z, true);
    B.light(D.x, y + 6, D.z, 0x39ff14, 30, 1.3);
    B.add(Math.max(X0, D.x - 12), y, Math.max(Z0, D.z - 12), Math.min(X1, D.x + 12), y + 0.06, Math.min(Z1, D.z + 12), 'ash', { nc: true, tint: 0x2a3a2a });
    if (B.inside(D.x, D.z)) {
      // the 13, leaning half-buried: the 1, then the 3 (three bars and two uprights on the right)
      const L = B.local(D.x, D.z, 0, y);
      L.O(-5, 7, 0, 3, 14, 3, 0.35, 'greenglow'); L.O(-6.2, 12.5, 0, 2.4, 2, 3, 0.35, 'greenglow');
      for (const yy of [1.5, 7, 12.5]) L.O(1.5, yy, 0, 7, 2.4, 3, 0.35, 'greenglow');
      L.O(4.6, 4.2, 0, 2.4, 6, 3, 0.35, 'greenglow'); L.O(4.6, 9.8, 0, 2.4, 6, 3, 0.35, 'greenglow');
      B.add(D.x - 6, y, D.z - 1.5, D.x + 6, y + 14, D.z + 1.5, 'metal', { hide: true });
      B.out.marks.push({ id: 'commute:digit_13', p: [D.x, y, D.z + 10] });
      B.out.triggers.push({ kind: 'hot', box: [D.x - 12, y - 1, D.z - 12, D.x + 12, y + 20, D.z + 12], name: 'HOT ZONE' });
    }
  }
  // the wasteland: old car parks with their line paint, dead trees, ash mounds, a lot more junk lying about
  const free = (x, z, m = 4) => !keepOut.some((q) => x > q[0] - m && x < q[2] + m && z > q[1] - m && z < q[3] + m);
  if (r() < 0.5) { // a car park
    const px = X0 + 6 + r() * (X1 - X0 - 36), pz = Z0 + 6 + r() * (Z1 - Z0 - 30);
    if (free(px + 15, pz + 12, 14)) {
      const y = hwY(pz + 12, true) + 0.02;
      B.add(px, y - 0.02, pz, px + 30, y + 0.03, pz + 24, 'asphalt', { nc: true, tint: 0x6a6460 });
      for (let i = 0; i <= 10; i++) { B.add(px + 1 + i * 2.8, y + 0.03, pz + 2, px + 1.12 + i * 2.8, y + 0.04, pz + 8, 'paint', { nc: true, tint: 0xe8e0d0 }); B.add(px + 1 + i * 2.8, y + 0.03, pz + 16, px + 1.12 + i * 2.8, y + 0.04, pz + 22, 'paint', { nc: true, tint: 0xe8e0d0 }); }
      const taken = new Set();
      for (let i = 0; i < 4; i++) { const bay = (r() * 10) | 0, row = r() < 0.5 ? 0 : 1; taken.add(bay + ':' + row); wreck(B, px + 2.4 + bay * 2.8, y, pz + (row ? 19 : 5), 0, r); }
      for (let bay = 0; bay < 10; bay++) for (const row of [0, 1]) if (!taken.has(bay + ':' + row) && B.inside(px + 2.4 + bay * 2.8, pz + (row ? 19 : 5))) B.out.marks.push({ id: 'park', p: [px + 2.4 + bay * 2.8, y, pz + (row ? 19 : 5)], yaw: row ? 0 : Math.PI, lot: true }); // the empty bays: parked cars (WP7)
    }
  }
  for (let i = 0; i < 4; i++) { // dead trees: a trunk and a few bare branches (render only, a box to bump)
    const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0);
    if (!free(x, z)) continue;
    const y = hwY(z, true), h = 4 + r() * 4, tips = [];
    B.shape({ kind: 'tube', pts: [[x, y - 0.2, z], [x + (r() - 0.5), y + h * 0.5, z + (r() - 0.5)], [x + (r() - 0.5) * 2, y + h, z + (r() - 0.5) * 2]], r: [0.32, 0.12], seg: 6, mat: 'wood', tint: 0x4a3428, step: 1.5 });
    for (let k = 0; k < 4; k++) { const a = r() * 6.28, by = y + h * (0.5 + r() * 0.4); tips.push(1); B.shape({ kind: 'tube', pts: [[x, by, z], [x + Math.cos(a) * 1.6, by + 1 + r(), z + Math.sin(a) * 1.6], [x + Math.cos(a) * 2.6, by + 1.4 + r() * 1.5, z + Math.sin(a) * 2.6]], r: [0.1, 0.03], seg: 4, mat: 'wood', tint: 0x4a3428, step: 1.5, at: [x, by, z] }); }
    B.add(x - 0.3, y, z - 0.3, x + 0.3, y + h * 0.7, z + 0.3, 'wood', { hide: true });
  }
  for (let i = 0; i < 3; i++) { const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0); if (free(x, z)) B.shape({ kind: 'blob', c: [x, hwY(z, true), z], r: [3 + r() * 4, 0.8 + r(), 3 + r() * 3], seg: 8, mat: 'ash', tint: 0x9a8a80 }); }
  for (let i = 0; i < 8; i++) {
    const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0);
    if (!free(x, z, 2) || (x > hx0 - 3 && x < hx1 + 3)) continue;
    const id = pick(r, ['rubble_a', 'rubble_b', 'tirestack', 'cone', 'filecab', 'paperdrift', 'officechair', 'cone']);
    B.prop(id, x, hwY(z, true), z, r() * 6.28, id.startsWith('rubble') ? 0.7 + r() * 0.8 : 1, 0);
  }
  // power poles along the east side of the highway, cables sagging between them, a ☺ billboard now and then
  for (let z = Math.ceil(Math.max(Z0, H.zTop) / 30) * 30; z < Math.min(Z1, H.zLow); z += 30) {
    const x = hx1 + 7, y = hwY(z, true);
    if (!B.inside(x, z)) continue;
    B.add(x - 0.15, y, z - 0.15, x + 0.15, y + 9, z + 0.15, 'wood', { tint: 0x6a4a32 });
    B.add(x - 1.4, y + 8.2, z - 0.08, x + 1.4, y + 8.4, z + 0.08, 'wood', { nc: true, tint: 0x6a4a32 });
    const y2 = hwY(z + 30, true);
    for (const dx of [-1.2, 1.2]) line(B, [x + dx, y + 8.4, z], [x + dx, y2 + 8.4, z + 30], { r: 0.025, mat: 'metal', tint: 0x202024, sag: 1.4 });
    if ((Math.round(z / 30) & 3) === 1) { // a billboard: the old ☺ on stilts, half the bulbs out
      B.add(x + 4, y, z - 3, x + 4.3, y + 7, z - 2.6, 'metal'); B.add(x + 4, y, z + 2.6, x + 4.3, y + 7, z + 3, 'metal');
      const bx = x + 4.15, cy = y + 9.5;
      B.add(bx - 0.1, cy - 2.5, z - 4, bx + 0.1, cy + 2.5, z + 4, 'paint', { tint: 0xffe14d }); // the board, facing the road (-x)
      B.add(bx - 0.14, cy - 2.6, z - 4.1, bx - 0.1, cy + 2.6, z - 3.9, 'cyanglow', { nc: true }); B.add(bx - 0.14, cy - 2.6, z + 3.9, bx - 0.1, cy + 2.6, z + 4.1, 'cyanglow', { nc: true });
      B.add(bx - 0.14, cy + 2.5, z - 4.1, bx - 0.1, cy + 2.6, z + 4.1, 'cyanglow', { nc: true });
      for (const ez of [-1.4, 1.4]) B.add(bx - 0.13, cy + 0.5, z + ez - 0.45, bx - 0.1, cy + 1.4, z + ez + 0.45, 'paint', { nc: true, tint: 0x111111 }); // ☺
      B.add(bx - 0.13, cy - 1.3, z - 2, bx - 0.1, cy - 0.8, z + 2, 'paint', { nc: true, tint: 0x111111 });
      B.add(bx - 0.13, cy - 0.8, z - 2.4, bx - 0.1, cy - 0.3, z - 1.9, 'paint', { nc: true, tint: 0x111111 }); B.add(bx - 0.13, cy - 0.8, z + 1.9, bx - 0.1, cy - 0.3, z + 2.4, 'paint', { nc: true, tint: 0x111111 });
      B.light(bx - 3, cy, z, 0x4fd8ff, 10, 0.6);
    }
  }
  // paper drifts: the paper storm's floor (the storm itself is weather in the client)
  for (let i = 0; i < 5; i++) { const x = X0 + r() * (X1 - X0), z = Z0 + r() * (Z1 - Z0); B.prop('paperdrift', x, hwY(z, true), z, r() * 6.28, 0.8 + r() * 0.8, 0); }
  // the war, still lying where it stopped: a ☺ CORP walker tank, one leg gone, half sunk in the wasteland
  if (B.inside(262, -150)) { const y = hwY(-150, true); B.prop('warmech', 262, y, -150, 0.6, 1, 0); B.add(256, y, -156, 268, y + 6, -144, 'metal', { hide: true }); B.out.marks.push({ id: 'commute.warmech', p: [262, y, -138] }); }
  B.out.triggers.push({ kind: 'paper', box: [X0, -10, Z0, X1, 80, Z1] });
  playCommute(B); // sign gantries, rings, the Pile-Up, the Smile's Hat (playground.js)
  act1Commute(B); // act I: the Under-Hill Loop's portal (act1set.js)
  shops(B, 'commute'); // the car dealer, the petrol station (shops.js)
  slipRoad(B); // the Bottom's slip road down onto the Commute (roads.js)
}
