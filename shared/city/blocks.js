// The stress city's generator: 1 x 1 km of generic blocks on a 96 m road grid that doesn't line up with the 64 m chunks
// on purpose, so most buildings straddle a chunk border (the clipping, the border physics and the hash all get tested).
// Towers, hollow shells you can walk through, roof ramps, streetlights, parked cars, a tube or two.
import { rng, hash2 } from './plan.js';

const ROAD = 96, RW = 12; // road pitch and width
const PAINTS = [0xffb3c7, 0xffe58a, 0x5fd3c6, 0xb6f2c8, 0xd2b6ff, 0xffc8a0, 0xe8e0d0, 0xa0c8ff];

function lot(B, x0, z0, x1, z1, r) {
  const w = x1 - x0, d = z1 - z0, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  const kind = r(), paint = PAINTS[(r() * PAINTS.length) | 0];
  if (kind < 0.5) { // a solid tower with lit window strips and a parapet
    const h = 8 + Math.floor(r() * 12) * 4;
    B.add(x0 + 2, 0, z0 + 2, x1 - 2, h, z1 - 2, 'plaster', { tint: paint });
    for (let y = 3; y < h - 1; y += 4) { // windows: render-only strips just proud of the wall
      B.add(x0 + 3, y, z0 + 1.95, x1 - 3, y + 1.4, z0 + 2, 'window', { nc: true });
      B.add(x0 + 3, y, z1 - 2, x1 - 3, y + 1.4, z1 - 1.95, 'window', { nc: true });
      B.add(x0 + 1.95, y, z0 + 3, x0 + 2, y + 1.4, z1 - 3, 'window', { nc: true });
      B.add(x1 - 2, y, z0 + 3, x1 - 1.95, y + 1.4, z1 - 3, 'window', { nc: true });
    }
    B.add(x0 + 2, h, z0 + 2, x1 - 2, h + 1, z0 + 2.4, 'concrete'); B.add(x0 + 2, h, z1 - 2.4, x1 - 2, h + 1, z1 - 2, 'concrete');
    B.add(x0 + 2, h, z0 + 2.4, x0 + 2.4, h + 1, z1 - 2.4, 'concrete'); B.add(x1 - 2.4, h, z0 + 2.4, x1 - 2, h + 1, z1 - 2.4, 'concrete');
    if (r() < 0.4) B.prop('watertank', cx, h, cz, r() * 6.28, 1);
  } else if (kind < 0.8) { // a hollow shell: floors, doors, an inside stair. bullets, grenades and players go in
    const floors = 2 + ((r() * 3) | 0), F = 4, t = 0.4;
    for (let f = 0; f < floors; f++) {
      const y0 = f * F, y1 = y0 + F;
      const door = f === 0 ? 2.6 : 0;
      // walls with a door gap in the middle of each side on the ground floor, windows above
      for (const [ax, a0, a1, fx] of [['x', x0 + 2, x1 - 2, z0 + 2], ['x', x0 + 2, x1 - 2, z1 - 2 - t], ['z', z0 + 2, z1 - 2, x0 + 2], ['z', z0 + 2, z1 - 2, x1 - 2 - t]]) {
        const m = (a0 + a1) / 2, gap = door ? 1.4 : 0;
        const seg = (s0, s1, yy0, yy1) => { if (s1 - s0 < 0.05) return; if (ax === 'x') B.add(s0, yy0, fx, s1, yy1, fx + t, 'brick', { tint: paint }); else B.add(fx, yy0, s0, fx + t, yy1, s1, 'brick', { tint: paint }); };
        if (gap) { seg(a0, m - gap, y0, y1); seg(m + gap, a1, y0, y1); seg(m - gap, m + gap, y0 + door, y1); } else { seg(a0, a1, y0, y0 + 1); seg(a0, a1, y0 + 2.6, y1); for (let s = a0; s < a1 - 2; s += 4) seg(s, s + 1.2, y0 + 1, y0 + 2.6); }
      }
      // the slab above, with a stair hole in one corner, and the flight up to it
      const sy = y1, hx = x0 + 3, hz = z0 + 3;
      if (f < floors - 1) {
        B.add(x0 + 2, sy, z0 + 2, x1 - 2, sy + 0.3, hz, 'concrete'); B.add(x0 + 2, sy, hz + 7, x1 - 2, sy + 0.3, z1 - 2, 'concrete');
        B.add(x0 + 2, sy, hz, hx, sy + 0.3, hz + 7, 'concrete'); B.add(hx + 2, sy, hz, x1 - 2, sy + 0.3, hz + 7, 'concrete');
        const n = 9, rise = (F + 0.3) / n;
        for (let i = 0; i < n; i++) B.add(hx, y0, hz + i * 0.75, hx + 2, y0 + (i + 1) * rise, hz + (i + 1) * 0.75, 'wood');
      } else B.add(x0 + 2, sy, z0 + 2, x1 - 2, sy + 0.4, z1 - 2, 'concrete');
    }
    B.prop('crate', cx, 0, cz, r() * 6.28, 1);
    B.prop('chair', cx + 2, 0, cz + 1, r() * 6.28, 1);
  } else { // a stepped ramp up to a low roof: steps of 0.25 m (walkable), crossing whatever chunk border is there
    const h = 6, steps = 24;
    B.add(x0 + 2, 0, z0 + 2, x1 - 2, h, cz, 'concrete', { tint: paint });
    for (let i = 0; i < steps; i++) B.add(x0 + 4, 0, cz + i * ((z1 - 2 - cz) / steps), x0 + 9, h - i * (h / steps), cz + (i + 1) * ((z1 - 2 - cz) / steps), 'concrete');
    B.prop('bench', x1 - 6, h, z0 + 6, 0, 1);
  }
}

export function blocks(B, d) {
  const [rx0, rz0, rx1, rz1] = d.rect;
  // ground: one slab under the chunk, roads painted on top (render-only, so collision stays one box)
  B.add(Math.max(B.X0, rx0), -1, Math.max(B.Z0, rz0), Math.min(B.X1, rx1), 0, Math.min(B.Z1, rz1), 'concrete');
  const i0 = Math.floor((B.X0 - RW) / ROAD), i1 = Math.floor((B.X1 + RW) / ROAD), j0 = Math.floor((B.Z0 - RW) / ROAD), j1 = Math.floor((B.Z1 + RW) / ROAD);
  for (let i = i0; i <= i1; i++) {
    const x = i * ROAD;
    B.add(x - RW / 2, 0, B.Z0, x + RW / 2, 0.02, B.Z1, 'road', { nc: true });
    for (let z = Math.ceil(B.Z0 / 24) * 24; z < B.Z1; z += 24) { B.prop('streetlight', x + RW / 2 + 0.6, 0.15, z, Math.PI, 1); B.add(x - 0.15, 0.02, z, x + 0.15, 0.03, z + 3, 'paint', { nc: true }); }
  }
  for (let j = j0; j <= j1; j++) {
    const z = j * ROAD;
    B.add(B.X0, 0, z - RW / 2, B.X1, 0.021, z + RW / 2, 'road', { nc: true });
  }
  // blocks: each one a curb + 2 x 2 lots (seeded by the block, not the chunk)
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
    const bx0 = i * ROAD + RW / 2, bz0 = j * ROAD + RW / 2, bx1 = (i + 1) * ROAD - RW / 2, bz1 = (j + 1) * ROAD - RW / 2;
    if (bx1 <= rx0 || bx0 >= rx1 || bz1 <= rz0 || bz0 >= rz1) continue;
    if (!B.touches([bx0, bz0, bx1, bz1])) continue;
    B.add(bx0, 0, bz0, bx1, 0.15, bz1, 'tile');
    const r = rng(hash2(i, j, 77));
    const mx = (bx0 + bx1) / 2, mz = (bz0 + bz1) / 2;
    for (const [a, b, c, e] of [[bx0, bz0, mx, mz], [mx, bz0, bx1, mz], [bx0, mz, mx, bz1], [mx, mz, bx1, bz1]]) {
      const lr = rng((r() * 4294967296) >>> 0);
      if (B.touches([a, b, c, e], 1)) lot({ ...B, add: (x0, y0, z0, x1, y1, z1, m, o) => B.add(x0, y0 + 0.15, z0, x1, y1 + 0.15, z1, m, o), prop: (id, x, y, z, ...rest) => B.prop(id, x, y + 0.15, z, ...rest) }, a, b, c, e, lr);
    }
    const cr = rng(hash2(i, j, 99));
    for (let k = 0; k < 3; k++) B.prop('car', bx0 - 3, 0, bz0 + 10 + cr() * (bz1 - bz0 - 20), cr() < 0.5 ? 0 : Math.PI, 1, (cr() * 6) | 0);
    if (cr() < 0.3) B.shape({ kind: 'tube', pts: [[mx - 10, 0.15, mz], [mx, 6, mz + 4], [mx + 10, 0.15, mz]], r: 1.2, mat: 'flesh', seg: 12 });
  }
}
