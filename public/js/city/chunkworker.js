// The chunk worker: builds chunks off the main thread (shared/city/chunk.js), meshes them (shared/city/mesh.js) and
// sends typed arrays back as transferables, so the main thread only uploads. Keeps a small LRU of packed chunks so a
// chunk moving between rings (near -> mid -> far) is never generated twice.
// in:  { op: 'chunk', id, city, cx, cz, want: { packed, mesh0, mesh1, cells } }  |  { op: 'far', key, city, ids: [[cx, cz]] }
//      { op: 'warm', city, spots: [[x, z]] }  (warm.js, before NEW GAME: build the chunks round them into the cache, no reply)
// out: { op: 'chunk', id, packed?, mesh0?, mesh1?, cells?, ms }                   |  { op: 'far', key, mesh, ms }
import { buildChunk, packChunk, transferList, hashChunk, chunkBuilder } from '/shared/city/chunk.js';
import { GENS } from '/shared/city/gens.js';
import { meshChunk, meshTransfer, impostorCells } from '/shared/city/mesh.js';
import { CHUNK } from '/shared/city/plan.js';

const cache = new Map(), MAX = 400;
const clonePacked = (p) => ({ ...p, box: p.box.slice(), mat: p.mat.slice(), flag: p.flag.slice(), tint: p.tint.slice(), deco: p.deco.slice(), dmat: p.dmat.slice(), dtint: p.dtint.slice(), prop: p.prop.slice() });
function get(city, cx, cz) {
  const id = city + ':' + cx + ':' + cz;
  let e = cache.get(id);
  if (e) { cache.delete(id); cache.set(id, e); return e; }
  const t = performance.now();
  e = { p: packChunk(buildChunk(city, cx, cz)), cells: null, buildMs: performance.now() - t };
  cache.set(id, e);
  if (cache.size > MAX) cache.delete(cache.keys().next().value);
  return e;
}

// the far ring's one mesh: a box per 16 m impostor cell, its top and walls, coloured like the tallest thing there
function farMesh(city, ids) {
  const N = 4, S = CHUNK / N;
  let n = 0;
  const cells = ids.map(([cx, cz]) => { const e = get(city, cx, cz); if (!e.cells) e.cells = impostorCells(e.p); return [cx, cz, e.cells]; });
  for (const [, , c] of cells) for (let i = 0; i < N * N; i++) if (c.top[i] > -1e8) n++;
  const pos = new Float32Array(n * 20 * 3), col = new Uint8Array(n * 20 * 3), nrm = new Int8Array(n * 20 * 3), idx = new Uint32Array(n * 30);
  let v = 0, k = 0;
  const quad = (pts, nx, ny, nz, r, g, b, sh) => {
    for (const p of pts) { pos.set(p, v * 3); nrm[v * 3] = nx * 127; nrm[v * 3 + 1] = ny * 127; nrm[v * 3 + 2] = nz * 127; col[v * 3] = r * sh; col[v * 3 + 1] = g * sh; col[v * 3 + 2] = b * sh; v++; }
    idx[k++] = v - 4; idx[k++] = v - 3; idx[k++] = v - 2; idx[k++] = v - 4; idx[k++] = v - 2; idx[k++] = v - 1;
  };
  for (const [cx, cz, c] of cells) for (let a = 0; a < N; a++) for (let b = 0; b < N; b++) {
    const i = a + b * N; if (c.top[i] < -1e8) continue;
    const x0 = cx * CHUNK + a * S, z0 = cz * CHUNK + b * S, x1 = x0 + S, z1 = z0 + S, y0 = c.base[i], y1 = c.top[i];
    const R = (c.col[i] >> 16) & 255, G = (c.col[i] >> 8) & 255, B = c.col[i] & 255;
    quad([[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]], 0, 1, 0, R, G, B, 1);
    quad([[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], 0, 0, 1, R, G, B, 0.8);
    quad([[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]], 0, 0, -1, R, G, B, 0.8);
    quad([[x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1]], 1, 0, 0, R, G, B, 0.7);
    quad([[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]], -1, 0, 0, R, G, B, 0.7);
  }
  return { pos, col, nrm, idx, verts: v, tris: k / 3 };
}

self.onmessage = (ev) => {
  const m = ev.data;
  try {
    if (m.op === 'chunk') {
      const t = performance.now(), e = get(m.city, m.cx, m.cz), out = { op: 'chunk', id: m.id, col: !!(m.want && m.want.col) }, tr = [];
      const w = m.want || {};
      if (w.packed) { out.packed = clonePacked(e.p); tr.push(...transferList(out.packed)); }
      if (w.mesh0) { out.mesh0 = meshChunk(e.p, 0); tr.push(...meshTransfer(out.mesh0)); }
      if (w.mesh1) { out.mesh1 = meshChunk(e.p, 1); tr.push(...meshTransfer(out.mesh1)); }
      if (w.hash) out.hash = hashChunk(e.p);
      out.ms = performance.now() - t; out.buildMs = e.buildMs;
      self.postMessage(out, tr);
    } else if (m.op === 'horizon') { // the skyline round the city: one render-only mesh, built once
      const t = performance.now(), B = chunkBuilder(m.city, 0, 0, [-3000, -3000, 3000, 3000]);
      GENS[m.gen](B, m.city);
      const mesh = meshChunk(packChunk(B.out), 1);
      self.postMessage({ op: 'horizon', mesh, ms: performance.now() - t }, meshTransfer(mesh));
    } else if (m.op === 'warm') { // (warm.js: build the 3 x 3 chunks round each spot into the cache, nearest first, before anyone asks. no reply: nobody's listening yet)
      const ids = new Map();
      for (const [x, z] of m.spots || []) { const cx = Math.floor(x / CHUNK), cz = Math.floor(z / CHUNK); for (const [dx, dz] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, 1], [1, -1], [-1, -1]]) ids.set((cx + dx) + ',' + (cz + dz), [cx + dx, cz + dz]); }
      for (const [cx, cz] of ids.values()) get(m.city, cx, cz);
    } else if (m.op === 'far') {
      const t = performance.now(), mesh = farMesh(m.city, m.ids);
      self.postMessage({ op: 'far', key: m.key, mesh, ms: performance.now() - t }, [mesh.pos.buffer, mesh.col.buffer, mesh.nrm.buffer, mesh.idx.buffer]);
    }
  } catch (e) { self.postMessage({ op: 'error', id: m.id, key: m.key, err: String(e && e.stack || e) }); }
};
