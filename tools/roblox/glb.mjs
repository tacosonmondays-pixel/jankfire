// a tiny glb reader for the Roblox tools: the json chunk, node world matrices and each mesh's bounds (from the
// accessors' min/max, so no vertex decoding). skips the far-away `lod1` copies, like the web game's prop loader
import fs from 'fs';

export function readGlb(file) {
  const b = fs.readFileSync(file);
  if (b.readUInt32LE(0) !== 0x46546c67) throw new Error('not a glb: ' + file);
  const len = b.readUInt32LE(12);
  return JSON.parse(b.slice(20, 20 + len).toString('utf8'));
}

// column-major 4x4 like glTF / three
export const ident = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
export function mul(a, b) {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return o;
}
export function trs(t = [0, 0, 0], q = [0, 0, 0, 1], s = [1, 1, 1]) {
  const [x, y, z, w] = q;
  return [
    (1 - 2 * (y * y + z * z)) * s[0], 2 * (x * y + z * w) * s[0], 2 * (x * z - y * w) * s[0], 0,
    2 * (x * y - z * w) * s[1], (1 - 2 * (x * x + z * z)) * s[1], 2 * (y * z + x * w) * s[1], 0,
    2 * (x * z + y * w) * s[2], 2 * (y * z - x * w) * s[2], (1 - 2 * (x * x + y * y)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
}
export const apply = (m, p) => [0, 1, 2].map((r) => m[r] * p[0] + m[4 + r] * p[1] + m[8 + r] * p[2] + m[12 + r]);
const local = (n) => n.matrix ? n.matrix.slice() : trs(n.translation, n.rotation, n.scale);
const strip = (s) => (s || '').replace(/\.\d+$/, '');

// walk the scene: { name, world, mesh, lod1, extras } per node
export function nodes(j) {
  const out = [], sc = j.scenes[j.scene || 0];
  const walk = (i, parent, far) => {
    const n = j.nodes[i], w = mul(parent, local(n)), lod1 = far || strip(n.name) === 'lod1';
    out.push({ i, name: n.name || '', world: w, mesh: n.mesh, lod1, extras: n.extras });
    for (const c of n.children || []) walk(c, w, lod1);
  };
  for (const r of sc.nodes) walk(r, ident(), false);
  return out;
}

// the bounds of the near (lod0) meshes, optionally under one node (a variant), in that node's frame
export function bounds(j, under = null) {
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  const all = nodes(j);
  let root = null, inv = ident();
  if (under != null) { root = all.find((n) => [String(under), 'n' + under, 'v' + under].includes(n.name)); if (root) inv = invert(root.world); }
  const inside = new Set();
  if (root) { const mark = (i) => { inside.add(i); for (const c of j.nodes[i].children || []) mark(c); }; mark(root.i); }
  for (const n of all) {
    if (n.mesh == null || n.lod1 || (root && !inside.has(n.i))) continue;
    const m = mul(inv, n.world);
    for (const pr of j.meshes[n.mesh].primitives) {
      const a = j.accessors[pr.attributes.POSITION];
      if (!a || !a.min) continue;
      for (let c = 0; c < 8; c++) {
        const p = apply(m, [c & 1 ? a.max[0] : a.min[0], c & 2 ? a.max[1] : a.min[1], c & 4 ? a.max[2] : a.min[2]]);
        for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], p[k]); hi[k] = Math.max(hi[k], p[k]); }
      }
    }
  }
  return { lo, hi };
}

// the game's prop metadata (glbkit.js metaOf: a node's extras.jf, JSON)
export function meta(j) {
  for (const n of j.nodes || []) if (n.extras && typeof n.extras.jf === 'string') { try { return JSON.parse(n.extras.jf); } catch { return null; } }
  return null;
}

// triangles per mesh (lod0 only), for the Roblox cap
export function tris(j) {
  let n = 0;
  for (const nd of nodes(j)) {
    if (nd.mesh == null || nd.lod1) continue;
    for (const pr of j.meshes[nd.mesh].primitives) {
      const c = pr.indices != null ? j.accessors[pr.indices].count : j.accessors[pr.attributes.POSITION].count;
      if ((pr.mode ?? 4) === 4) n += c / 3;
    }
  }
  return n;
}

export function invert(m) { // affine inverse (rotation/scale + translation)
  const a = [[m[0], m[4], m[8]], [m[1], m[5], m[9]], [m[2], m[6], m[10]]];
  const det = a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]);
  const inv = [
    [(a[1][1] * a[2][2] - a[1][2] * a[2][1]) / det, (a[0][2] * a[2][1] - a[0][1] * a[2][2]) / det, (a[0][1] * a[1][2] - a[0][2] * a[1][1]) / det],
    [(a[1][2] * a[2][0] - a[1][0] * a[2][2]) / det, (a[0][0] * a[2][2] - a[0][2] * a[2][0]) / det, (a[0][2] * a[1][0] - a[0][0] * a[1][2]) / det],
    [(a[1][0] * a[2][1] - a[1][1] * a[2][0]) / det, (a[0][1] * a[2][0] - a[0][0] * a[2][1]) / det, (a[0][0] * a[1][1] - a[0][1] * a[1][0]) / det],
  ];
  const t = [m[12], m[13], m[14]], it = [0, 1, 2].map((r) => -(inv[r][0] * t[0] + inv[r][1] * t[1] + inv[r][2] * t[2]));
  return [inv[0][0], inv[1][0], inv[2][0], 0, inv[0][1], inv[1][1], inv[2][1], 0, inv[0][2], inv[1][2], inv[2][2], 0, it[0], it[1], it[2], 1];
}
