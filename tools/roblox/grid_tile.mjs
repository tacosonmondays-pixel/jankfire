// the playground's tile: white with thin grey seams and a "+" at each corner, as one PNG (no dependencies).
// 512 px = 8 studs in Roblox (the MaterialVariant "JankGrid", StudsPerTile 8), so blocks sized in 8s line up.
// run: node tools/roblox/grid_tile.mjs <out.png>
import fs from 'node:fs';
import zlib from 'node:zlib';

const N = 512;
const out = process.argv[2] || 'grid_tile.png';
const px = Buffer.alloc(N * N * 3);
const BASE = [244, 245, 248], SEAM = [196, 199, 208], PLUS = [150, 154, 166], SHADE = [232, 234, 239];
for (let y = 0; y < N; y++) {
  for (let x = 0; x < N; x++) {
    const ex = Math.min(x, N - 1 - x), ey = Math.min(y, N - 1 - y), e = Math.min(ex, ey);
    let c = BASE;
    if (e < 10) c = SHADE;                                    // a soft bevel just inside the seam
    if (e < 3) c = SEAM;                                      // the seam (two tiles make it 6 px wide)
    if ((ex < 5 && ey < 34) || (ey < 5 && ex < 34)) c = PLUS; // the + at each corner
    px.set(c, (y * N + x) * 3);
  }
}
const raw = Buffer.alloc(N * (N * 3 + 1));
for (let y = 0; y < N; y++) px.copy(raw, y * (N * 3 + 1) + 1, y * N * 3, (y + 1) * N * 3);
const table = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = (b) => { let c = 0xffffffff; for (const v of b) c = table[(c ^ v) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
const chunk = (t, d) => {
  const len = Buffer.alloc(4); len.writeUInt32BE(d.length);
  const td = Buffer.concat([Buffer.from(t), d]);
  const c = Buffer.alloc(4); c.writeUInt32BE(crc(td));
  return Buffer.concat([len, td, c]);
};
const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(N, 0); ihdr.writeUInt32BE(N, 4); ihdr[8] = 8; ihdr[9] = 2;
fs.writeFileSync(out, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
console.log('wrote', out, fs.statSync(out).size, 'bytes');
