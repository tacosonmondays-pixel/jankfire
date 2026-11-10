// Draws JANKFIRE's own effect sprite sheets (flipbooks) and writes them to public/sprites/*.png. Run: node tools/sprites/make.cjs
// Every sheet is ours, made here from noise: nothing downloaded. Three layers packed in one image:
//   R = shading (4 flat comic bands, lit from the top left)   G = the ink outline   A = the shape
// The game tints, lights and outlines them (public/js/flipbook.js), so one grey sheet does white smoke, dust, steam...
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const OUT = path.join(__dirname, '../../public/sprites');

// ---- tiny PNG writer (RGBA8)
const CRC = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc = (b) => { let c = -1; for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
function png(file, w, h, px) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; Buffer.from(px.buffer, y * w * 4, w * 4).copy(raw, y * (w * 4 + 1) + 1); }
  const ih = Buffer.alloc(13); ih.writeUInt32BE(w, 0); ih.writeUInt32BE(h, 4); ih[8] = 8; ih[9] = 6;
  fs.writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
  console.log(path.basename(file), `${w}x${h}`, (fs.statSync(file).size / 1024).toFixed(1) + ' kB');
}

// ---- noise
const hash = (x, y, z) => { let h = (x * 374761393 + y * 668265263 + z * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const sm = (t) => t * t * (3 - 2 * t), lerp = (a, b, t) => a + (b - a) * t;
function noise(x, y, z) {
  const X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z), u = sm(x - X), v = sm(y - Y), w = sm(z - Z);
  const n = (i, j, k) => hash(X + i, Y + j, Z + k);
  return lerp(lerp(lerp(n(0, 0, 0), n(1, 0, 0), u), lerp(n(0, 1, 0), n(1, 1, 0), u), v), lerp(lerp(n(0, 0, 1), n(1, 0, 1), u), lerp(n(0, 1, 1), n(1, 1, 1), u), v), w);
}
const fbm = (x, y, z, o = 4) => { let a = 0.5, s = 0, f = 1; for (let i = 0; i < o; i++) { s += a * noise(x * f, y * f, z * f); a *= 0.5; f *= 2; } return s; };
const billow = (x, y, z, o = 3) => { let a = 0.5, s = 0, f = 1; for (let i = 0; i < o; i++) { s += a * Math.abs(noise(x * f, y * f, z * f) * 2 - 1); a *= 0.5; f *= 2.1; } return s; }; // puffy lumps
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v)), sstep = (a, b, x) => sm(clamp((x - a) / (b - a)));
const BANDS = [0.18, 0.45, 0.72, 1]; // four flat tones
const band = (s) => BANDS[Math.min(3, Math.floor(clamp(s) * 4))];

// a sheet of n x n frames, each `size` px. field(u, v, t) -> density (> 0 = inside), u,v in -1..1 (v up), t 0..1
function sheet(name, n, size, field, ink = 0.07) {
  const W = n * size, px = new Uint8Array(W * W * 4), e = 2.5 / size, Lx = -0.45, Ly = 0.65, Lz = 0.6;
  for (let f = 0; f < n * n; f++) {
    const t = f / (n * n - 1), ox = (f % n) * size, oy = Math.floor(f / n) * size;
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      const u = ((x + 0.5) / size) * 2 - 1, v = 1 - ((y + 0.5) / size) * 2;
      const edge = Math.min(1, (1 - Math.max(Math.abs(u), Math.abs(v))) * 10); // nothing touches the frame's edge (no bleeding into the next frame)
      const d = field(u, v, t) * edge - (1 - edge) * 0.2;
      const i = ((oy + y) * W + ox + x) * 4;
      if (d <= 0) continue;
      // light it like a soft lump: the density is the height
      const hgt = (q) => Math.sqrt(clamp(q * 2.2));
      const nx = hgt(field(u - e, v, t)) - hgt(field(u + e, v, t)), ny = hgt(field(u, v - e, t)) - hgt(field(u, v + e, t)), nz = e * 2.6;
      const l = Math.hypot(nx, ny, nz), sh = (nx * Lx + ny * Ly + nz * Lz) / l;
      px[i] = Math.round(band(sh * 0.6 + 0.48) * 255);
      px[i + 1] = d < ink ? 255 : 0;
      px[i + 2] = Math.round(clamp(d * 2) * 255); // (B: how deep inside, spare for later tricks)
      px[i + 3] = 255;
    }
  }
  png(path.join(OUT, name + '.png'), W, W, px);
}

// ---- smoke puff: a cartoon cloud of balls that swells, rolls outward, then pops away ball by ball. 6x6 frames
sheet('puff', 6, 96, (u, v, t) => {
  const z = t * 1.2, grow = Math.sqrt(Math.min(1, t * 2.4)), S = 0.5 + 0.5 * grow;
  const x = u + (fbm(u * 1.5 + 7, v * 1.5, z) - 0.5) * 0.16, y = v + (fbm(u * 1.5, v * 1.5 + 9, z) - 0.5) * 0.16;
  let d = 0.36 * S - Math.hypot(x, y); // the middle
  for (let k = 0; k < 10; k++) {
    const a = k * 2.399 + (hash(k, 1, 7) - 0.5) * 0.8 + t * (hash(k, 2, 7) - 0.5) * 1.6; // (they drift round a bit: it rolls)
    const dist = (0.2 + 0.26 * hash(k, 3, 7)) * S * (1 + 0.25 * t), r = (0.2 + 0.14 * hash(k, 4, 7)) * S;
    const die = 0.55 + 0.4 * hash(k, 5, 7), life = 1 - sstep(die, Math.min(1, die + 0.22), t); // each ball pops at its own time
    d = Math.max(d, r * life - Math.hypot(x - Math.cos(a) * dist, y - Math.sin(a) * dist - 0.05 * t));
  }
  d -= sstep(0.72, 1, t) * 0.5; // and the middle goes last
  return d + (billow(x * 3, y * 3, z + 3) - 0.35) * 0.05;
}, 0.05);

// ---- ripple (seen from above): two wobbly foam rings running outward, breaking up. 4x4 frames
sheet('ripple', 4, 128, (u, v, t) => {
  const r = Math.hypot(u, v), a = Math.atan2(v, u);
  const wob = (fbm(Math.cos(a) * 1.6 + 5, Math.sin(a) * 1.6, t * 2 + 1) - 0.5) * 0.14;
  const ring = (r0, w) => w - Math.abs(r - r0 - wob);
  const r1 = 0.14 + 0.72 * Math.sqrt(t), r2 = r1 * 0.58;
  const gaps = fbm(Math.cos(a) * 3 + 2, Math.sin(a) * 3, t * 1.5 + r * 2) - 0.28 - t * 0.3; // the foam line tears as it thins
  let d = Math.max(ring(r1, 0.075 * (1 - t * 0.55)), t > 0.12 ? ring(r2, 0.05 * (1 - t * 0.7)) : -1);
  if (t < 0.2) d = Math.max(d, (0.16 - t * 0.6) - r); // the first frames: a blob of foam where it went in
  return Math.min(d, gaps * 0.4 + 0.02);
}, 0.02);

// ---- splash (seen from the side, the water line at the bottom): a crown that jumps up, fingers out and falls as drops. 4x4 frames
sheet('splash', 4, 128, (u, v, t) => {
  const y = v + 0.86; // 0 at the water line
  const up = Math.sin(Math.min(1, t * 1.25) * Math.PI) ** 0.8, W = 0.3 + 0.42 * Math.sqrt(t);
  const x = u / W;
  if (Math.abs(x) > 1.25) return -1;
  const finger = 0.55 + 0.45 * Math.abs(Math.sin(x * 5.5 + 0.6)) + (noise(x * 4 + 3, 1, t * 2) - 0.5) * 0.5; // the crown's points
  const rim = 0.55 + 0.45 * x * x; // higher at the sides: it's a ring seen side on
  const H = 1.25 * up * finger * rim * (1 - 0.3 * t);
  let d = Math.min(H - y, (1.05 - Math.abs(x)) * 0.5, y + 0.02) * 0.6;
  d -= sstep(0.45, 1, t) * 0.5 * fbm(u * 5, v * 5, t * 3); // the sheet tears into drops
  // drops thrown clear of it
  for (let k = 0; k < 7; k++) {
    const a = 0.5 + hash(k, 3, 1) * 2.14, sp = 0.9 + hash(k, 5, 2) * 0.9, tt = t * 1.15;
    const dx = Math.cos(a) * sp * tt * 0.75, dy = Math.sin(a) * sp * tt * 1.9 - 2.3 * tt * tt;
    d = Math.max(d, (0.05 + 0.03 * hash(k, 9, 4)) * (1 - t * 0.5) - Math.hypot(u - dx, (y - 0.1 - dy) * 0.8));
  }
  return y < 0 ? -1 : d;
}, 0.035);

// ---- option B, soft smoke: a billowing volume with soft edges and smooth shading, no ink (the realistic one). 6x6 frames
// (meant to be a Blender smoke sim baked to a sheet; Blender isn't on the build machine, so this marches a noise volume instead)
{
  const n = 6, size = 96, W = n * size, px = new Uint8Array(W * W * 4);
  const dens = (x, y, z, t) => {
    const wz = t * 0.9, wx = (fbm(x * 1.4 + 3, y * 1.4, z * 1.4 + wz, 3) - 0.5) * 0.7, wy = (fbm(x * 1.4, y * 1.4 + 5, z * 1.4 + wz, 3) - 0.5) * 0.7;
    const R = 0.42 + 0.4 * Math.sqrt(Math.min(1, t * 2));
    const d = 1 - Math.hypot(x + wx, y + wy - 0.1 * t, z) / R + (fbm(x * 3 + wx * 2, y * 3 + wy * 2, z * 3 + wz * 1.5, 4) - 0.5) * 1.1;
    return clamp(d * 1.6 - sstep(0.55, 1, t) * 1.5 * (0.3 + noise(x * 2.4 + 9, y * 2.4, z * 2.4 + wz)));
  };
  for (let f = 0; f < n * n; f++) {
    const t = f / (n * n - 1), ox = (f % n) * size, oy = Math.floor(f / n) * size;
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      const u = ((x + 0.5) / size) * 2 - 1, v = 1 - ((y + 0.5) / size) * 2;
      let T = 1, L = 0; // march front to back: what's left of the view, the light collected
      for (let k = 0; k < 12 && T > 0.03; k++) {
        const z = 0.85 - (k + 0.5) * (1.7 / 12), d = dens(u, v, z, t);
        if (d <= 0.01) continue;
        const sh = Math.exp(-2.2 * (dens(u - 0.12, v + 0.2, z + 0.1, t) + dens(u - 0.24, v + 0.4, z + 0.2, t)) * 0.5); // how much smoke is between here and the light (top left)
        const a = 1 - Math.exp(-d * 0.75);
        L += T * a * (0.3 + 0.7 * sh); T *= 1 - a;
      }
      const A = (1 - T) * Math.min(1, (1 - Math.max(Math.abs(u), Math.abs(v))) * 8), i = ((oy + y) * W + ox + x) * 4;
      if (A < 0.004) continue;
      px[i] = Math.round(clamp(L / Math.max(0.001, 1 - T)) * 255); px[i + 1] = 0; px[i + 2] = 0; px[i + 3] = Math.round(clamp(A) * 255);
    }
  }
  png(path.join(OUT, 'puffsoft.png'), W, W, px);
}

// ---- option B, water: a tiling ripple normal map (256 px = one tile). rings from many drops + short wind wavelets, wrapped
{
  const N = 256, H = new Float32Array(N * N), px = new Uint8Array(N * N * 4);
  const drops = []; for (let k = 0; k < 26; k++) drops.push([hash(k, 1, 31) * N, hash(k, 2, 31) * N, 10 + hash(k, 3, 31) * 34, 0.5 + hash(k, 4, 31) * 0.7]);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let h = 0;
    for (const [cx, cy, r, a] of drops) { // nearest wrapped copy of each drop
      let dx = Math.abs(x - cx), dy = Math.abs(y - cy); dx = Math.min(dx, N - dx); dy = Math.min(dy, N - dy);
      const d = Math.hypot(dx, dy);
      if (d < r * 1.6) h += a * Math.cos((d / r) * Math.PI * 3) * Math.exp(-((d / r) ** 2) * 1.6) * Math.min(1, d / 3);
    }
    const tw = (Math.PI * 2) / N; // wavelets that tile exactly
    h += 0.35 * Math.sin(x * tw * 5 + Math.sin(y * tw * 3) * 1.5) + 0.25 * Math.sin(y * tw * 7 + Math.sin(x * tw * 4) * 1.2) + 0.15 * Math.sin((x + y) * tw * 11);
    H[y * N + x] = h;
  }
  const at = (x, y) => H[((y + N) % N) * N + ((x + N) % N)];
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const nx = (at(x - 1, y) - at(x + 1, y)) * 1.4, ny = (at(x, y - 1) - at(x, y + 1)) * 1.4, l = Math.hypot(nx, ny, 1), i = (y * N + x) * 4;
    px[i] = Math.round((nx / l * 0.5 + 0.5) * 255); px[i + 1] = Math.round((ny / l * 0.5 + 0.5) * 255); px[i + 2] = Math.round((1 / l * 0.5 + 0.5) * 255); px[i + 3] = 255;
  }
  png(path.join(OUT, 'ripplenormal.png'), N, N, px);
}
