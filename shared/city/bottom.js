// THE BOTTOM: the Off-Spec survivor town at the bottom of the hill. Nine terraces climb north 3 m at a time; each has
// a lane along its downhill lip and a row of stacked pastel cube houses (containers, plaster, vending machines) backed
// against the next retaining wall, so the top houses' roofs are the terrace above's floor. The Long Stairs run straight
// up the middle to the Gut border; washing lines along every lane are ziplines; festoon bulbs everywhere.
// Landmarks: the Lost & Found (the Machine), the market, Lumps' Gym, the Down Escalator.
import { SLICE, terraceOf } from './slice.js';
import { rng, hash2 } from './plan.js';
import { cube, stairsZ, sideStair, line, bulbs, retaining, rubble, stall, flightLen, PASTEL, pick } from './kit.js';

const T = SLICE.bottom, LANE = 7;
const zSouth = (k) => 256 - T.terr * k; // the downhill edge of terrace k
const yOf = (k) => k * T.rise;
const inRect = (x0, z0, x1, z1, r) => x0 < r[2] && x1 > r[0] && z0 < r[3] && z1 > r[1];
const KEEP_OUT = () => [SLICE.lostFound.rect, SLICE.plaza.rect, SLICE.gym.rect, [SLICE.longStairs.x0 - 5, 0, SLICE.longStairs.x1 + 5, 256], [SLICE.escalator.x - 5, 40, SLICE.escalator.x + 5, 90], [SLICE.bottom.rect[2] - 6, 0, SLICE.bottom.rect[2] + 2, 256]];

// the lots of terrace k: [x0, w, seed], laid out once along the whole terrace (deterministic, cached)
const lotCache = new Map();
function lots(k) {
  if (lotCache.has(k)) return lotCache.get(k);
  const r = rng(hash2(k, 4242)), out = [];
  for (let x = T.rect ? T.rect[0] : -320; x < 90;) {
    const w = 5 + Math.floor(r() * 4) * 1.5; // 5 - 9.5 m
    const gap = r() < 0.18 ? 2 + r() * 3 : 0.4; // an alley now and then
    out.push([x + gap, w, (r() * 4294967296) >>> 0]);
    x += gap + w;
  }
  lotCache.set(k, out);
  return out;
}

// one lot: 1-2 rows of cubes stacked 1-4 high, shifted about, outside stairs, a roof garden of junk
function house(B, k, x0, w, seed) {
  const r = rng(seed), y = yOf(k), zs = zSouth(k), zBack = zs - T.terr + 0.2, zFront = zs - LANE;
  const depth = zFront - zBack, rows = depth > 13 && r() < 0.6 ? 2 : 1, cx = x0 + w / 2;
  const wallTop = yOf(k + 1); // the next terrace's floor: houses at the back reach it, their roofs join it
  let rowZ = zBack;
  for (let row = 0; row < rows; row++) {
    const d = rows === 2 ? depth / 2 - 0.3 : depth - 0.5, cz = rowZ + d / 2;
    const floors = row === 0 ? 2 + Math.floor(r() * 3) + (r() < 0.3 ? 1 : 0) : 1 + Math.floor(r() * 2); // the back row towers
    let fy = y, shift = 0, lastTop = y;
    for (let f = 0; f < floors; f++) {
      const h = 2.8 + Math.floor(r() * 3) * 0.2, ww = w - 0.4 - (f ? r() * 1.2 : 0), dd = d - (f ? r() * 1.5 : 0);
      shift = f ? Math.max(-1.2, Math.min(1.2, shift + (r() - 0.5) * 1.6)) : 0;
      const container = r() < 0.35;
      const c = cube(B, cx + shift, fy, cz + (f ? (r() - 0.5) : 0), ww, dd, h, r, {
        door: f === 0 ? (row === rows - 1 ? 2 : 1) : (r() < 0.5 ? 1 : 3), container, tint: container ? pick(r, [0xff7a9a, 0x5fd3c6, 0xffd24d, 0x9a7aff, 0xff9a4d]) : pick(r, PASTEL),
        roofTint: r() < 0.3 ? 0xd06a5a : 0,
      });
      // an outside stair up to this floor's roof from the one below (every third house)
      if (f < floors - 1 && r() < 0.45) sideStair(B, (r() < 0.5 ? c.x1 + 0.7 : c.x0 - 0.7), fy + 0.12, c.top, c.z1 - 0.2, -1);
      lastTop = c.top; fy = c.top;
      // junk on the roof: plastic chairs, a dish, a smiley sign, a sofa
      if (f === floors - 1) {
        const pr = r();
        if (pr < 0.25) B.prop('pchair', cx + (r() - 0.5) * (ww - 1), c.top, cz + (r() - 0.5) * (dd - 1), r() * 6.28, 1, (r() * 8) | 0);
        else if (pr < 0.35) B.prop('sofa', cx, c.top, cz, (r() * 4 | 0) * Math.PI / 2, 1, (r() * 8) | 0);
        else if (pr < 0.42) B.prop('smilesign', cx, c.top, cz, r() * 6.28, 0.7, 0);
        else if (pr < 0.55) B.prop('tarp', cx, c.top, cz, (r() * 4 | 0) * Math.PI / 2, 1, 0);
        if (r() < 0.35) B.prop('wokdish', c.x0, c.top - 0.6, cz, Math.PI / 2, 1, 0);
        if (r() < 0.3) B.prop('stringlights', cx, c.top + 2.2, cz, r() * 6.28, 1, 0);
      }
    }
    // the back row reaching the terrace above: a little bridge from its roof onto the next terrace
    if (row === 0 && Math.abs(lastTop - wallTop) < 1.2 && k < T.n - 1) B.add(cx - 1, Math.min(lastTop, wallTop) - 0.2, zBack - 1.2, cx + 1, Math.max(lastTop, wallTop) + 0.05, zBack + 0.6, 'wood');
    rowZ += d + 0.6;
  }
  // across the lane: bulbs from the house front to the lip, a banner now and then, an awning over the door
  const lr = rng(seed ^ 0x5eed);
  if (lr() < 0.45) bulbs(B, [cx + (lr() - 0.5) * w, y + 4.2 + lr(), zFront + 0.3], [cx + (lr() - 0.5) * 10, y + 4.5 + lr(), zs - 0.3], lr);
  if (lr() < 0.12) B.obb(cx, y + 5.4, (zFront + zs) / 2, 0.06, 1.2, LANE - 0.6, Math.PI / 2 * 0 + (lr() - 0.5) * 0.1, lr() < 0.5 ? 'tiedye' : 'tarp', { tint: pick(lr, [0xff7ab0, 0xffe14d, 0x4fd8c6]) });
  if (lr() < 0.3) B.prop('tarp', cx, y, zFront + 1.1, Math.PI, 0.8, 0);
  if (lr() < 0.06) stall(B, cx, y, zFront + 2.5, 2, lr);
  // street level: a fridge, a scooter, chairs out the front, a soup stack
  const sr = r();
  const fz = zFront + 1.2;
  if (sr < 0.3) B.prop('pchair', cx + (r() - 0.5) * w * 0.6, y, fz, r() * 6.28, 1, (r() * 8) | 0);
  else if (sr < 0.45) B.prop('fridge', x0 + 0.6, y, fz - 0.4, Math.PI, 1, (r() * 8) | 0);
  else if (sr < 0.55) B.prop('scooter', cx, y, fz + 0.6, r() * 6.28, 1, (r() * 8) | 0);
  else if (sr < 0.62) B.prop('crate_soup', cx, y, fz, r() * 6.28, 1, 0);
}

// the lane along terrace k: paving, a curb, washing-line poles on the lip with ziplines between them
function lane(B, k, x0, x1) {
  const y = yOf(k), zs = zSouth(k), r = rng(hash2(k, 777));
  B.add(x0, y - 0.02, zs - LANE, x1, y + 0.02, zs, 'concrete', { nc: true, tint: 0xcab8b0 });
  if (k > 0) B.add(x0, y, zs - 0.4, x1, y + 0.9, zs, 'concrete', { tint: 0xe0d0c8 }); // the lip wall (you can jump it)
  // poles every 14-22 m along the lip, a line between neighbours: laundry on most, bulbs on some
  let px = -316 + r() * 6;
  const poles = [];
  while (px < 92) { poles.push(px); px += 14 + r() * 8; }
  for (let i = 0; i < poles.length; i++) {
    const p = poles[i];
    if (p < x0 - 30 || p > x1 + 30) continue;
    if (KEEP_OUT().some((q) => inRect(p - 1, zs - 1, p + 1, zs + 1, q))) continue;
    const h = 5.2 + (hash2(k, i) % 7) * 0.2;
    if (p >= x0 && p < x1) { B.add(p - 0.1, y, zs - 0.3, p + 0.1, y + h, zs - 0.1, 'rust'); }
    const q = poles[i + 1];
    if (q === undefined || KEEP_OUT().some((rr) => inRect(Math.min(p, q), zs - 1, Math.max(p, q), zs + 1, rr))) continue;
    const hq = 5.2 + (hash2(k, i + 1) % 7) * 0.2, a = [p, y + h, zs - 0.2], b = [q, y + hq, zs - 0.2];
    if ((hash2(k, i, 3) % 5) < 3) line(B, a, b, { zip: true, hang: ['laundry_a', 'laundry_b'], mat: 'metal' });
    else { bulbs(B, a, b, rng(hash2(k, i, 9))); if (B.inside((a[0] + b[0]) / 2, a[2])) B.out.triggers.push({ kind: 'zip', a, b, sag: Math.abs(b[0] - a[0]) * 0.08 }); }
  }
}

// the Lost & Found: a ruined returns depot on terrace 2, open at the front, a hole in the roof, the Machine inside
function lostFound(B) {
  const [x0, z0, x1, z1] = SLICE.lostFound.rect, y = yOf(2), H = 11;
  B.add(x0, y - 0.2, z0, x1, y + 0.15, z1, 'tile', { tint: 0xd8d0c0 });
  B.add(x0, y, z0, x0 + 0.6, y + H, z1, 'brick', { tint: 0xffb3c7 }); B.add(x1 - 0.6, y, z0, x1, y + H, z1, 'brick', { tint: 0xffb3c7 });
  B.add(x0, y, z0, x1, y + H, z0 + 0.6, 'brick', { tint: 0xf0a0b8 }); // back wall (uphill)
  // front: two pillars and a big lintel with the sign; the middle is wide open
  B.add(x0, y, z1 - 0.6, x0 + 10, y + H, z1, 'brick', { tint: 0xffb3c7 }); B.add(x1 - 10, y, z1 - 0.6, x1, y + H, z1, 'brick', { tint: 0xffb3c7 });
  B.add(x0 + 10, y + 7.5, z1 - 0.6, x1 - 10, y + H, z1, 'brick', { tint: 0xf8c0d0 });
  B.prop('lostfound_sign', (x0 + x1) / 2, y + 8.2, z1 + 0.05, 0, 1, 0); B.light((x0 + x1) / 2, y + 7, z1 + 3, 0xffe14d, 12, 1);
  // roof with a collapsed hole over the middle (light falls on the Machine)
  B.add(x0, y + H, z0, x1, y + H + 0.4, z0 + 9, 'concrete'); B.add(x0, y + H, z0 + 17, x1, y + H + 0.4, z1, 'concrete');
  B.add(x0, y + H, z0 + 9, x0 + 16, y + H + 0.4, z0 + 17, 'concrete'); B.add(x1 - 16, y + H, z0 + 9, x1, y + H + 0.4, z0 + 17, 'concrete');
  const r = rng(5150);
  rubble(B, (x0 + x1) / 2 + 6, y + 0.15, z0 + 13, 4, r);
  // the Machine at the back, the returns counter, shelves of lost things, a mezzanine with stairs
  B.add(-195, y + 0.15, z0 + 1, -183, y + 7.2, z0 + 5, 'metal', { hide: true }); // the Machine's collision
  B.prop('machine', -189, y + 0.15, z0 + 3.2, 0, 1, 0); B.light(-189, y + 4, z0 + 7, 0xff4fd8, 18, 1.4); B.light(-189, y + 2, z0 + 6, 0x4fd8ff, 10, 0.8); B.light(-189, y + 10, z0 + 13, 0xb0a0ff, 14, 0.6); // the Machine glows; moonlight through the hole
  B.add(x0 + 4, y + 0.15, z0 + 14, x0 + 16, y + 1.1, z0 + 15.2, 'wood'); B.prop('returns_counter', x0 + 10, y + 0.15, z0 + 14.6, 0, 1, 0);
  for (let i = 0; i < 4; i++) { const sx = x1 - 6 - i * 0.01; B.add(sx - 1.2, y + 0.15, z0 + 4 + i * 4.5, sx, y + 3.2, z0 + 7 + i * 4.5, 'metal', { tint: 0x9aa8b8 }); B.prop('lostpile', sx - 3, y + 0.15, z0 + 5.5 + i * 4.5, r() * 6.28, 1, i); }
  B.add(x0 + 0.6, y + 4.2, z0 + 0.6, x0 + 12, y + 4.5, z0 + 12, 'wood'); // mezzanine: the bunks (the safehouse)
  stairsZ(B, x0 + 12.2, x0 + 13.6, z0 + 12.5, -1, y + 0.15, y + 4.5, 'metal');
  B.prop('bed', x0 + 3, y + 4.5, z0 + 3, 0, 1, 0); B.prop('locker', x0 + 8, y + 4.5, z0 + 1.2, 0, 1, 3); B.prop('wardrobe', x0 + 10.5, y + 4.5, z0 + 1.4, 0, 1, 0);
  B.prop('garagedoor', x1 - 5, y + 0.15, z1 - 0.1, 0, 1, 0);
  bulbs(B, [x0 + 2, y + 9.5, z1 - 2], [x1 - 2, y + 9.5, z0 + 3], rng(77)); bulbs(B, [x1 - 2, y + 9.5, z1 - 2], [x0 + 2, y + 9.5, z0 + 3], rng(78));
  // the way in: steps from terrace 1 up to the depot floor (it covers terrace 2's lip)
  stairsZ(B, x0 + 12, x1 - 12, z1 + flightLen(y + 0.15 - yOf(1)), -1, yOf(1), y + 0.15, 'concrete');
  B.out.marks.push({ id: 'bottom.machine', p: [-189, y + 0.15, z0 + 7], r: 0 }, { id: 'bottom.lost_found', p: [(x0 + x1) / 2, y + 0.15, z1 - 4] });
  B.out.spawns.push([-189, y + 0.3, z0 + 8]);
}

// the market: stalls, fire barrels, a canopy of bulbs, the bottom of the Long Stairs
function plaza(B) {
  const [x0, z0, x1, z1] = SLICE.plaza.rect, r = rng(9191);
  B.add(x0, -0.05, z0, x1, 0.02, z1, 'tile', { nc: true, tint: 0xe8c8b8 });
  for (let i = 0; i < 14; i++) stall(B, x0 + 6 + (i % 7) * 12.5, 0, z0 + 6 + Math.floor(i / 7) * 12, r() < 0.5 ? 0 : 2, r);
  for (let i = 0; i < 6; i++) { const fx = x0 + 10 + i * 14 + r() * 4, fz = z0 + 12 + r() * 6; B.prop('firebarrel', fx, 0, fz, 0, 1, 0); B.light(fx, 1.6, fz, 0xff8a2a, 11, 1.2); }
  for (let i = 0; i < 6; i++) bulbs(B, [x0 + 2 + i * 15, 6.5, z0 + 1], [x0 + 10 + i * 15, 6.5, z1 - 1], rng(400 + i));
  B.out.marks.push({ id: 'bottom.plaza', p: [(x0 + x1) / 2, 0, (z0 + z1) / 2] });
  for (let i = 0; i < 24; i++) B.out.marks.push({ id: 'crowd', p: [x0 + 4 + r() * (x1 - x0 - 8), 0, z0 + 4 + r() * (z1 - z0 - 8)], kind: 'shopper' }); // NPC crowd spots
}

// Lumps' Gym: an open-sided container shed on terrace 4 where all the weights are fridges
function gym(B) {
  const [x0, z0, x1, z1] = SLICE.gym.rect, y = yOf(4), r = rng(2024);
  B.add(x0, y, z0, x1, y + 0.2, z1, 'tile', { tint: 0x5fd3c6 });
  for (const [a, b] of [[x0, x0 + 0.8], [x1 - 0.8, x1]]) for (const [c, d] of [[z0, z0 + 0.8], [z1 - 0.8, z1]]) B.add(a, y, c, b, y + 5, d, 'rust');
  B.add(x0 - 0.5, y + 5, z0 - 0.5, x1 + 0.5, y + 5.4, z1 + 0.5, 'container', { tint: 0xff7a9a });
  for (let i = 0; i < 10; i++) B.prop('fridge', x0 + 3 + (i % 5) * 6, y + 0.2, z0 + 5 + Math.floor(i / 5) * 9, r() * 6.28, 0.9 + r() * 0.3, (r() * 8) | 0);
  B.add(x0 + 12, y + 0.2, z0 + 9, x1 - 12, y + 1.0, z0 + 10, 'metal', { tint: 0x3a3a40 }); // the bench (a bus stop seat)
  B.out.marks.push({ id: 'bottom.gym', p: [(x0 + x1) / 2, y + 0.2, (z0 + z1) / 2] }, { id: 'npc.lumps', p: [x0 + 16, y + 0.2, z0 + 12], face: Math.PI });
}

// the Down Escalator: a dead mall escalator bridging from terrace 8 down over terrace 7 to terrace 6. it only goes down
function escalator(B) {
  const E = SLICE.escalator, x = E.x, za = zSouth(8) + 0.5, zb = zSouth(6) - LANE - 1, ya = yOf(8), yb = yOf(6);
  const n = 40;
  for (let i = 0; i < n; i++) {
    const z = za + (zb - za) * i / n, z2 = za + (zb - za) * (i + 1) / n, yy = ya + (yb - ya) * (i + 1) / n;
    B.add(x - 1, yy - 0.6, z, x + 1, yy, z2, 'metal', { tint: 0x8890a0 });
  }
  for (const s of [-1, 1]) B.shape({ kind: 'tube', pts: [[x + s * 1.1, ya + 1, za], [x + s * 1.1, yb + 1, zb]], r: 0.08, seg: 6, mat: 'rust', at: [x, ya, za] });
  B.add(x - 1.2, yb - 0.5, zb, x + 1.2, ya, zb + 0.5, 'metal', { nc: true, tint: 0x606878 });
  B.out.triggers.push({ kind: 'conveyor', box: [x - 1, yb - 0.5, za, x + 1, ya + 2, zb], dir: [0, 0, 1], speed: 6, name: 'DOWN ESCALATOR' });
  B.out.marks.push({ id: 'bottom.escalator', p: [x, ya, za] });
}

export function bottom(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect;
  const X0 = Math.max(B.X0, rx0), X1 = Math.min(B.X1, rx1), Z0 = Math.max(B.Z0, rz0), Z1 = Math.min(B.Z1, rz1);
  if (X1 <= X0 || Z1 <= Z0) return;
  // terraces: one ground box per terrace strip, a retaining wall on each lip
  for (let k = 0; k < T.n; k++) {
    const za = k === T.n - 1 ? 0 : zSouth(k + 1), zb = zSouth(k);
    if (zb <= Z0 || za >= Z1) continue;
    B.add(X0, -4, Math.max(za, Z0), X1, yOf(k), Math.min(zb, Z1), 'ground', { tint: [0xb89890, 0xa89098, 0xb8a090][k % 3] });
    if (k > 0 && zb > Z0 && zb <= Z1) retaining(B, X0, X1, zb, yOf(k - 1), yOf(k), rng(hash2(k, B.out.cx, 31)));
  }
  const keep = KEEP_OUT();
  for (let k = 0; k < T.n; k++) {
    const zs = zSouth(k), zn = zs - T.terr;
    if (!B.touches([-320, zn, 96, zs], 2)) continue;
    lane(B, k, X0, X1);
    for (const [x0, w, seed] of lots(k)) {
      if (x0 + w < X0 - 12 || x0 > X1 + 12) continue; // only lots touching this chunk (+ a stair's width)
      if (keep.some((q) => inRect(x0, zn, x0 + w, zs - LANE, q))) continue;
      house(B, k, x0, w, seed);
    }
    // a narrow stair up to the next terrace every ~70 m (plus the Long Stairs), so every lane connects
    if (k < T.n - 1) for (let sx = -300 + (k * 23) % 40; sx < 90; sx += 66 + (k * 7) % 12) {
      if (keep.some((q) => inRect(sx - 1, zn - 6, sx + 1, zn + 6, q))) continue;
      if (sx < X0 - 3 || sx > X1 + 3) continue;
      stairsZ(B, sx - 1, sx + 1, zn + flightLen(T.rise), -1, yOf(k), yOf(k + 1), 'concrete');
    }
  }
  // the Long Stairs: 9 flights straight up the middle, banners and bulbs over them
  const LS = SLICE.longStairs;
  if (B.touches([LS.x0 - 4, 0, LS.x1 + 4, 256])) {
    for (let k = 0; k < T.n; k++) {
      const zs = zSouth(k), top = k === T.n - 1 ? SLICE.border.y : yOf(k + 1), zt = k === T.n - 1 ? 0 : zSouth(k + 1);
      stairsZ(B, LS.x0, LS.x1, zt + flightLen(top - yOf(k)), -1, yOf(k), top, 'concrete', { tint: 0xf0e0d0 });
      B.add(LS.x0 - 0.3, yOf(k), zt, LS.x0, yOf(k) + 1, zs, 'metal', { nc: true }); B.add(LS.x1, yOf(k), zt, LS.x1 + 0.3, yOf(k) + 1, zs, 'metal', { nc: true });
      if (k % 2 === 0) bulbs(B, [LS.x0 - 0.5, yOf(k) + 6, zs - 4], [LS.x1 + 0.5, yOf(k) + 6, zs - 12], rng(600 + k));
      B.obb((LS.x0 + LS.x1) / 2, yOf(k) + 7.2, zs - 9, 7, 1.4, 0.05, 0, 'tiedye'); // a banner across
    }
    B.out.marks.push({ id: 'bottom.long_stairs', p: [(LS.x0 + LS.x1) / 2, 0, 236] });
  }
  if (B.touches(SLICE.lostFound.rect, 6)) lostFound(B);
  if (B.touches(SLICE.plaza.rect, 2)) plaza(B);
  if (B.touches(SLICE.gym.rect, 2)) gym(B);
  if (B.touches([SLICE.escalator.x - 3, 0, SLICE.escalator.x + 3, 100])) escalator(B);
  // crowd spots along the lanes (WP8 / the crowd sim fills them)
  const cr = rng(hash2(B.out.cx, B.out.cz, 55));
  for (let i = 0; i < 6; i++) { const x = X0 + cr() * (X1 - X0), z = Z0 + cr() * (Z1 - Z0), k = terraceOf(z); if (z < zSouth(k) - 0.5 && z > zSouth(k) - LANE + 0.5) B.out.marks.push({ id: 'crowd', p: [x, yOf(k), z], kind: pick(cr, ['local', 'scooter', 'cook']) }); }
}
