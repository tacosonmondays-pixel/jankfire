// Build one 64 m city chunk from its district generators: deterministic, so the server and every client get the same
// chunk without a download. A generator draws whole features (a house, a street) with the builder below; the builder
// clips collision boxes to the chunk (a house across a border is built by both chunks, each keeps its half), and keeps
// props, deco and shapes whose anchor is inside the chunk. Output is packed into typed arrays (packChunk): that's the
// worker -> main thread transfer, the server cache's storage and what the hash test compares.
import { CHUNK, CITIES, MAT_ID, MATS, rng, hash2, strHash, chunkId } from './plan.js';
import { GENS } from './gens.js';

const F_NC = 1, F_HIDE = 2, F_FIT = 4, F_LOD = 8, F_L0 = 16, F_L1 = 32; // render-only, collision-only, texture once per face, keep in lod1 always, drawn in lod0 only, drawn in lod1 only (a cheap stand-in)
const F_TER = 64; // a hidden step under shaped ground (a 'field' shape, shared/city/ground.js): soft on top, bodies walk the field
export const FLAGS = { NC: F_NC, HIDE: F_HIDE, FIT: F_FIT, LOD: F_LOD, L0: F_L0, L1: F_L1, TER: F_TER };
export const TER_SOFT = 1.0; // (how deep a ground step's top is soft: physics.js soft)

// a builder for chunk (cx, cz). ox/oz/rot/oy: a local frame like shared/map.js local() (rot = quarter turns)
export function chunkBuilder(city, cx, cz, rect) {
  const X0 = rect ? rect[0] : cx * CHUNK, Z0 = rect ? rect[1] : cz * CHUNK, X1 = rect ? rect[2] : X0 + CHUNK, Z1 = rect ? rect[3] : Z0 + CHUNK;
  const out = { city, cx, cz, x0: X0, z0: Z0, x1: X1, z1: Z1, boxes: [], deco: [], props: [], shapes: [], lanes: [], spawns: [], triggers: [], marks: [], lights: [] };
  const inside = (x, z) => x >= X0 && x < X1 && z >= Z0 && z < Z1;
  // flags: nc (drawn, never bumped), hide (bumped, never drawn), fit, lod; tint: 0xrrggbb paint over the material
  const add = (x0, y0, z0, x1, y1, z1, mat = 'concrete', o) => {
    if (x1 < x0) [x0, x1] = [x1, x0];
    if (y1 < y0) [y0, y1] = [y1, y0];
    if (z1 < z0) [z0, z1] = [z1, z0];
    if (x1 - x0 < 0.01 || y1 - y0 < 0.01 || z1 - z0 < 0.01) return;
    const a = Math.max(x0, X0), b = Math.min(x1, X1), c = Math.max(z0, Z0), d = Math.min(z1, Z1);
    if (b - a < 0.005 || d - c < 0.005) return; // not in this chunk (or a sliver)
    const m = MAT_ID[mat] ?? MAT_ID.concrete;
    out.boxes.push([a, y0, c, b, y1, d, m, o ? (o.nc || o.l1 ? F_NC : 0) | (o.hide ? F_HIDE : 0) | (o.fit ? F_FIT : 0) | (o.lod ? F_LOD : 0) | (o.l0 ? F_L0 : 0) | (o.l1 ? F_L1 : 0) | (o.ter ? F_TER | F_HIDE : 0) : 0, o && o.tint ? o.tint >>> 0 : 0]);
  };
  const box = (x, y, z, sx, sy, sz, mat, o) => add(x - sx / 2, y - sy / 2, z - sz / 2, x + sx / 2, y + sy / 2, z + sz / 2, mat, o);
  // a turned box, render only (signs, planks, rebar): kept by the chunk its centre is in
  const obb = (x, y, z, sx, sy, sz, yaw, mat, o) => { if (inside(x, z)) out.deco.push([x, y, z, sx, sy, sz, yaw, MAT_ID[mat] ?? 0, o && o.tint ? o.tint >>> 0 : 0]); };
  // a Blender prop (public/models/story/s_<id>.glb, code fallback in public/js/city/props.js): an instance, visual only
  const prop = (id, x, y, z, yaw = 0, s = 1, v = 0) => { if (inside(x, z)) out.props.push([id, x, y, z, yaw, s, v]); };
  // a non-box render shape (tubes, blobs, lathes for flesh and pipes): meshed by shared/city/mesh.js. anchor = first point
  const shape = (s) => { const p = s.at || s.c || (s.pts && s.pts[0]); if (p && inside(p[0], p[2])) out.shapes.push(s); };
  // a baked light: warms the vertex colours of everything within r (mesh.js). kept if it reaches this chunk at all
  const light = (x, y, z, color, r = 8, k = 1) => { if (x > X0 - r && x < X1 + r && z > Z0 - r && z < Z1 + r) out.lights.push([x, y, z, color >>> 0, r, k]); };
  const local = (ox, oz, rot = 0, oy = 0) => {
    const T = (x, z) => [[x, z], [-z, x], [-x, -z], [z, -x]][rot & 3];
    const L = (x0, y0, z0, x1, y1, z1, mat, o) => { const [ax, az] = T(x0, z0), [bx, bz] = T(x1, z1); add(ox + ax, oy + y0, oz + az, ox + bx, oy + y1, oz + bz, mat, o); };
    L.B = (x, y, z, sx, sy, sz, mat, o) => L(x - sx / 2, y - sy / 2, z - sz / 2, x + sx / 2, y + sy / 2, z + sz / 2, mat, o);
    L.pt = (x, y, z) => { const [ax, az] = T(x, z); return [ox + ax, oy + y, oz + az]; };
    L.P = (id, x, y, z, yaw = 0, s = 1, v = 0) => { const [ax, az] = T(x, z); prop(id, ox + ax, oy + y, oz + az, yaw - (rot & 3) * Math.PI / 2, s, v); };
    L.O = (x, y, z, sx, sy, sz, yaw, mat, o) => { const [ax, az] = T(x, z); obb(ox + ax, oy + y, oz + az, sx, sy, sz, yaw - (rot & 3) * Math.PI / 2, mat, o); };
    L.rot = rot; L.ox = ox; L.oz = oz; L.oy = oy;
    return L;
  };
  // does rect [x0, z0, x1, z1] (grown by m) touch this chunk? generators use it to skip features
  const touches = (r, m = 0) => r[0] - m < X1 && r[2] + m > X0 && r[1] - m < Z1 && r[3] + m > Z0;
  return { out, add, box, obb, prop, shape, light, local, touches, inside, X0, Z0, X1, Z1 };
}

// build chunk (cx, cz) of a city: every district whose rect (+ its margin) touches the chunk draws into it
// rect: build any rectangle in one go instead (the border tests compare that with the chunks)
export function buildChunk(city, cx, cz, rect) {
  const C = CITIES[city];
  if (!C) throw new Error('no city ' + city);
  const B = chunkBuilder(city, cx, cz, rect);
  const seed = hash2(cx, cz, strHash(city));
  for (const d of C.districts) {
    const g = GENS[d.gen];
    if (!g || !B.touches(d.rect, d.margin ?? 32)) continue;
    g(B, d, rng(seed ^ strHash(d.id)), city);
  }
  if (C.post) GENS[C.post] && GENS[C.post](B, C, rng(seed ^ 0x51ced), city); // a city-wide pass (the void edge, the far skyline)
  return B.out;
}

// ---------------------------------------------------------------- packing (typed arrays: transfer, cache, hash)
export function packChunk(o) {
  const n = o.boxes.length, nd = o.deco.length, np = o.props.length;
  const box = new Float32Array(n * 6), mat = new Uint8Array(n), flag = new Uint8Array(n), tint = new Uint32Array(n);
  o.boxes.forEach((b, i) => { for (let k = 0; k < 6; k++) box[i * 6 + k] = b[k]; mat[i] = b[6]; flag[i] = b[7]; tint[i] = b[8]; });
  const deco = new Float32Array(nd * 7), dmat = new Uint8Array(nd), dtint = new Uint32Array(nd);
  o.deco.forEach((b, i) => { for (let k = 0; k < 7; k++) deco[i * 7 + k] = b[k]; dmat[i] = b[7]; dtint[i] = b[8]; });
  const ids = [], prop = new Float32Array(np * 7);
  o.props.forEach((p, i) => {
    let k = ids.indexOf(p[0]); if (k < 0) { k = ids.length; ids.push(p[0]); }
    prop[i * 7] = k; for (let j = 1; j < 7; j++) prop[i * 7 + j] = p[j];
  });
  return {
    id: chunkId(o.city, o.cx, o.cz), city: o.city, cx: o.cx, cz: o.cz, box, mat, flag, tint, deco, dmat, dtint, ids, prop,
    shapes: o.shapes, lanes: o.lanes, spawns: o.spawns, triggers: o.triggers, marks: o.marks, lights: o.lights || [],
  };
}
export const transferList = (p) => [p.box.buffer, p.mat.buffer, p.flag.buffer, p.tint.buffer, p.deco.buffer, p.dmat.buffer, p.dtint.buffer, p.prop.buffer];

// collision boxes as the physics wants them ({ min, max, mat }), from the packed floats, so server and client agree
// to the bit. render-only (nc) boxes are left out. shaped ground (a 'field' shape) comes along as out.fields: ChunkWorld
// joins the loaded ones into the heightfield bodies walk on, and its hidden steps are marked ter (soft on top)
export function chunkBoxes(p) {
  const out = [];
  for (let i = 0; i < p.mat.length; i++) {
    if (p.flag[i] & F_NC) continue;
    const j = i * 6, mt = MATS[p.mat[i]];
    const b = { min: [p.box[j], p.box[j + 1], p.box[j + 2]], max: [p.box[j + 3], p.box[j + 4], p.box[j + 5]], mat: mt ? mt[0] : 'concrete' };
    if (p.flag[i] & F_TER) { b.ter = 1; b.sw = TER_SOFT; }
    out.push(b);
  }
  const f = (p.shapes || []).filter((s) => s.kind === 'field' && s.ground);
  if (f.length) out.fields = f;
  return out;
}

// FNV-1a over everything that matters (boxes, deco, props, shapes, lanes, spawns, triggers): the determinism test
export function hashChunk(p) {
  let h = 2166136261;
  const bytes = (a) => { const u = new Uint8Array(a.buffer, a.byteOffset, a.byteLength); for (let i = 0; i < u.length; i++) h = Math.imul(h ^ u[i], 16777619); };
  for (const a of [p.box, p.mat, p.flag, p.tint, p.deco, p.dmat, p.dtint, p.prop]) bytes(a);
  const s = JSON.stringify([p.ids, p.shapes, p.lanes, p.spawns, p.triggers, p.marks, p.lights], (k, v) => (typeof v === 'number' ? Math.fround(v) : v));
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return (h >>> 0).toString(16).padStart(8, '0');
}
export const packedBytes = (p) => p.box.byteLength + p.mat.byteLength + p.flag.byteLength + p.tint.byteLength + p.deco.byteLength + p.dmat.byteLength + p.dtint.byteLength + p.prop.byteLength
  + JSON.stringify([p.ids, p.shapes, p.lanes, p.spawns, p.triggers, p.marks, p.lights]).length;
