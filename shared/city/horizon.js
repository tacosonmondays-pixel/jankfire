// The rest of Greater Jankburg round the slice, as one render-only silhouette mesh (no collision, no chunks): the hill
// climbing north through the other districts to Corp Hill and the ☺ Spire, the ruined lowlands and dead highways on
// stilts to the south, east and west, and the void eating the far edge. Built once by the chunk worker (op 'horizon')
// and drawn with a haze that ignores the district fog, so the skyline always shows. Deterministic like everything else.
import { rng, hash2 } from './plan.js';

const PAST = [0xffb3c7, 0xffe58a, 0x5fd3c6, 0xd2b6ff, 0xffc8a0, 0xa8e6ff];
// districts up the hill: [name, centre z, base y, colours, tall?]
const UPHILL = [
  ['the lates / margins', -420, 52, [0xd8c890, 0xb8b090, 0x5a6a5a], 0.5],
  ['pinstripe + checkout', -620, 78, [0xd0303a, 0xf0e0c8, 0xffe14d, 0xff4fd8], 0.8],
  ['number works / chrome gristle / evergreen', -860, 110, [0xffe14d, 0x2a2a30, 0xff00dc, 0x7dff4f], 1],
  ['corp hill', -1150, 150, [0xffffff, 0xe8f4ff, 0x4fd8ff], 1.4],
];

export function horizon(B) {
  const r = rng(hash2(7, 7, 0x4012));
  const blk = (x, z, w, d, y0, h, tint, mat = 'plaster') => B.add(x - w / 2, y0, z - d / 2, x + w / 2, y0 + h, z + d / 2, mat, { nc: true, tint });
  // ground: the hill, in broad terraces rising north, ruined lowlands round the other sides
  for (let z = -1500; z < 1300; z += 100) for (let x = -1500; x < 1500; x += 100) {
    if (x > -380 && x < 380 && z > -320 && z < 320) continue; // the slice itself
    const up = z < -300 ? Math.min(160, (-300 - z) * 0.14) : z > 300 ? -6 - (z - 300) * 0.02 : 0;
    const y = Math.round(up / 4) * 4 + (r() - 0.5) * 2;
    blk(x + 50, z + 50, 100, 100, y - 30, 30, z < -300 ? 0x8a6a78 : 0x7a6a70, 'ground');
  }
  // the city up the hill: dense blocks, taller toward Corp Hill
  for (const [, cz, by, cols, tall] of UPHILL) for (let i = 0; i < 220; i++) {
    const x = (r() - 0.5) * 2600, z = cz + (r() - 0.5) * 240, w = 10 + r() * 30, d = 10 + r() * 30, h = (6 + r() * r() * 70) * tall;
    if (Math.abs(x) < 380 && z > -330) continue;
    blk(x, z, w, d, by + (cz - z) * 0.1, h, cols[(r() * cols.length) | 0], r() < 0.3 ? 'concrete' : 'plaster');
  }
  // landmarks you can see from anywhere: the ☺ Spire (white, a smiley disc on top), the smokestacks, the mall dome
  blk(60, -1200, 26, 26, 150, 260, 0xffffff, 'concrete');
  blk(60, -1200, 12, 12, 410, 60, 0xe8f4ff, 'concrete');
  B.add(60 - 30, 470, -1200 - 2, 60 + 30, 530, -1200 + 2, 'glow', { nc: true, tint: 0xffe14d }); // the ☺ (a lit disc, square up close)
  B.add(60 - 16, 505, -1200 - 2.3, 60 - 8, 515, -1200 - 2.1, 'glow', { nc: true, tint: 0x111111 }); B.add(60 + 8, 505, -1200 - 2.3, 60 + 16, 515, -1200 - 2.1, 'glow', { nc: true, tint: 0x111111 });
  B.add(60 - 18, 484, -1200 - 2.3, 60 + 18, 490, -1200 - 2.1, 'glow', { nc: true, tint: 0x111111 });
  for (let i = 0; i < 6; i++) blk(-500 + i * 40, -880, 9, 9, 110, 90 + r() * 40, 0x3a3430, 'brick');
  for (let i = 0; i < 6; i++) B.add(-500 + i * 40 - 5, 200 + 70 + i * 3, -880 - 5, -500 + i * 40 + 5, 205 + 70 + i * 3, -880 + 5, 'glow', { nc: true, tint: 0xff7a1a });
  blk(420, -640, 160, 160, 78, 30, 0xffe14d, 'concrete'); blk(420, -640, 110, 110, 108, 22, 0xfff0a0, 'glass'); // the Checkout's dome (stepped)
  // dead highways on stilts across the lowlands, jammed
  for (const [x0, z0, x1, z1] of [[-1500, 600, 1500, 640], [700, -1400, 740, 1200], [-1500, -150, -380, -130]]) {
    const len = Math.max(x1 - x0, z1 - z0), alongX = x1 - x0 > z1 - z0;
    for (let s = 0; s < len; s += 60) {
      const x = alongX ? x0 + s : (x0 + x1) / 2, z = alongX ? (z0 + z1) / 2 : z0 + s, y = z < -300 ? Math.min(160, (-300 - z) * 0.14) : 0;
      blk(x, z, alongX ? 60 : 30, alongX ? 30 : 60, y + 18, 2.5, 0x9a9490, 'concrete');
      blk(x, z, 4, 4, y - 10, 28, 0x8a8480, 'concrete');
    }
  }
  // ruins in the lowlands (south, east, west): broken shells, the odd fire glow
  for (let i = 0; i < 260; i++) {
    const a = r() * Math.PI * 2, d = 420 + r() * 1000, x = Math.cos(a) * d, z = Math.sin(a) * d * 0.9 + 200;
    if (z < -300 || (Math.abs(x) < 380 && Math.abs(z) < 330)) continue;
    const h = 4 + r() * 26;
    blk(x, z, 8 + r() * 24, 8 + r() * 24, 0, h, PAST[(r() * PAST.length) | 0], r() < 0.5 ? 'brick' : 'concrete');
    if (r() < 0.12) B.add(x - 2, h, z - 2, x + 2, h + 3, z + 2, 'glow', { nc: true, tint: 0xff9a3a });
  }
  // the void at the far south edge: a black lip with a magenta shine
  B.add(-2000, -60, 1300, 2000, -2, 1400, 'glow', { nc: true, tint: 0x14001a });
}
