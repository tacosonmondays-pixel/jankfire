// Ground with a shape: hills, dips, mounds and ditches instead of one flat slab. A map builder calls shapeGround at
// the end, on its own finished boxes, and gets:
//   - a heightfield (boxes.terrain: a 1 m grid, at(x, z) = the ground's height there). players and bots walk on it
//     (physics.js movePlayer), the client draws it as one mesh (world.js)
//   - hidden stepped boxes under it ({ ter: 1 }, one per cell or run of cells), so everything that only knows boxes
//     (bullets, grenades, grapples, marbles, the bots' eyes, the walk graph) still finds ground within a few cm
//   - everything that stood on the old flat ground moved with it: big things (buildings, walls, bridges, roads, the
//     canyon's lip) keep the ground flat round them and it rolls away from there; small things (cacti, crates, graves)
//     ride up and down with it on a little level pad of their own
// all of it worked out from the boxes and a seed, so the server and every client build the same ground.

const sm = (a, b, v) => { const k = Math.max(0, Math.min(1, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
// value noise on a lattice (integer hash, so it's the same on every machine), smooth between the points
export function lattice(seed) {
  const h = (i, j) => { let n = Math.imul(i, 374761393) ^ Math.imul(j, 668265263) ^ seed; n = Math.imul(n ^ (n >>> 13), 1274126177); return ((n ^ (n >>> 16)) >>> 0) / 4294967295 * 2 - 1; };
  return (x, z) => {
    const i = Math.floor(x), j = Math.floor(z), u = x - i, v = z - j, a = u * u * (3 - 2 * u), b = v * v * (3 - 2 * v);
    return (h(i, j) * (1 - a) + h(i + 1, j) * a) * (1 - b) + (h(i, j + 1) * (1 - a) + h(i + 1, j + 1) * a) * b;
  };
}

// o: { region: [x0, z0, x1, z1] (whole metres), mat (the ground slabs' material: slabs = boxes of it with their top at 0),
//      seed, up, down (how high the hills, how deep the dips), flat: [[x0, z0, x1, z1]] (kept level whatever stands there),
//      points: [[x, y, z], ...] (spawns and the like: lifted onto the new ground), near, far (m from something big where
//      the ground starts to move, and where it's free), big (m: a thing wider than this keeps its ground flat) }
export function shapeGround(B, D, o) {
  const [X0, Z0, X1, Z1] = o.region, nx = X1 - X0, nz = Z1 - Z0, vx = nx + 1, vz = nz + 1;
  const up = o.up ?? 1.5, down = o.down ?? 1.0, BIG = o.big ?? 7, mat = o.mat;
  const inR = (b) => b.max[0] > X0 && b.min[0] < X1 && b.max[2] > Z0 && b.min[2] < Z1;
  // a ground slab that runs on past the region (one lawn under a whole suburb) is cut: the piece inside is ours to shape, the rest stays as it was
  // (and to whole metres: the grid is 1 m, so a slab edge at x.4 keeps a flat strip of itself there instead of growing or shrinking)
  for (const b of B.boxes.filter((q) => q.mat === mat && q.max[1] === 0 && q.min[1] <= -1 && inR(q))) {
    const cx0 = Math.ceil(Math.max(b.min[0], X0) - 1e-6), cx1 = Math.floor(Math.min(b.max[0], X1) + 1e-6), cz0 = Math.ceil(Math.max(b.min[2], Z0) - 1e-6), cz1 = Math.floor(Math.min(b.max[2], Z1) + 1e-6);
    if (cx1 - cx0 < 1 || cz1 - cz0 < 1) continue; // (too thin to hold a cell: it stays a flat box)
    if (cx0 === b.min[0] && cx1 === b.max[0] && cz0 === b.min[2] && cz1 === b.max[2]) continue;
    const piece = (x0, z0, x1, z1) => { if (x1 - x0 > 0.01 && z1 - z0 > 0.01) B.boxes.push({ ...b, min: [x0, b.min[1], z0], max: [x1, b.max[1], z1] }); };
    piece(b.min[0], b.min[2], cx0, b.max[2]); piece(cx1, b.min[2], b.max[0], b.max[2]); piece(cx0, b.min[2], cx1, cz0); piece(cx0, cz1, cx1, b.max[2]);
    b.min[0] = cx0; b.max[0] = cx1; b.min[2] = cz0; b.max[2] = cz1;
  }
  const whole = (v) => Math.abs(v - Math.round(v)) < 1e-6;
  const slabs = B.boxes.filter((b) => b.mat === mat && b.max[1] === 0 && b.min[1] <= -1 && b.min[0] >= X0 && b.max[0] <= X1 && b.min[2] >= Z0 && b.max[2] <= Z1 && whole(b.min[0]) && whole(b.max[0]) && whole(b.min[2]) && whole(b.max[2]));
  // ---- paint: thin flat boxes of o.drape materials (a lawn, a patch of grass on sand) don't hold the ground level, they
  // become the ground's colour there: the cells under them are drawn in that material and the boxes themselves go
  const drape = new Set(o.drape || []), mats = [mat], paint = new Uint8Array(nx * nz), draped = new Set();
  for (const L of [B.boxes, D.boxes]) for (const b of L) {
    if (!drape.has(b.mat) || b.rot || b.max[1] > 0.13 || b.min[1] < -0.02 || !inR(b)) continue;
    let k = mats.indexOf(b.mat); if (k < 0) { mats.push(b.mat); k = mats.length - 1; }
    for (let i = Math.max(0, Math.floor(b.min[0] - X0 + 0.5)); i < Math.min(nx, Math.floor(b.max[0] - X0 + 0.5)); i++) for (let j = Math.max(0, Math.floor(b.min[2] - Z0 + 0.5)); j < Math.min(nz, Math.floor(b.max[2] - Z0 + 0.5)); j++) paint[i * nz + j] = k;
    b.ter = 1; draped.add(b);
  }
  const slabSet = new Set(slabs);
  const C = (i, j) => i * nz + j, V = (i, j) => i * vz + j;
  // ---- which cells have ground at all (a slab under their middle): the canyon and the mine shaft don't
  const ok = new Uint8Array(nx * nz);
  for (const s of slabs) for (let i = Math.max(0, Math.floor(s.min[0] - X0)); i < Math.min(nx, Math.ceil(s.max[0] - X0)); i++) for (let j = Math.max(0, Math.floor(s.min[2] - Z0)); j < Math.min(nz, Math.ceil(s.max[2] - Z0)); j++) {
    const cx = X0 + i + 0.5, cz = Z0 + j + 0.5;
    if (cx > s.min[0] && cx < s.max[0] && cz > s.min[2] && cz < s.max[2]) ok[C(i, j)] = 1;
  }
  // ---- the things standing on it: boxes that touch each other are one thing
  const items = [];
  for (const L of [B.boxes, D.boxes]) for (const b of L) if (!slabSet.has(b) && !draped.has(b) && !b.still && inR(b) && b.max[1] > 0.001 && b.min[1] < 40) items.push(b); // (still: stays where the map put it: a plug down a shaft)
  const par = items.map((_, k) => k), find = (k) => { while (par[k] !== k) k = par[k] = par[par[k]]; return k; };
  const T = 0.03, order = items.map((_, k) => k).sort((p, q) => items[p].min[0] - items[q].min[0]);
  for (let a = 0; a < order.length; a++) {
    const p = items[order[a]];
    for (let c = a + 1; c < order.length; c++) {
      const q = items[order[c]];
      if (q.min[0] > p.max[0] + T) break;
      if (q.min[2] <= p.max[2] + T && q.max[2] >= p.min[2] - T && q.min[1] <= p.max[1] + T && q.max[1] >= p.min[1] - T) par[find(order[a])] = find(order[c]);
    }
  }
  const comps = new Map();
  items.forEach((b, k) => {
    const r = find(k);
    let c = comps.get(r);
    if (!c) comps.set(r, (c = { list: [], x0: 1e9, z0: 1e9, x1: -1e9, z1: -1e9, y0: 1e9 }));
    if (b.av) c.av = 1; // (drawn by a baked model, public/js/archfield.js: the model can't move, so neither does this)
    c.list.push(b); c.x0 = Math.min(c.x0, b.min[0]); c.x1 = Math.max(c.x1, b.max[0]); c.z0 = Math.min(c.z0, b.min[2]); c.z1 = Math.max(c.z1, b.max[2]); c.y0 = Math.min(c.y0, b.min[1]);
  });
  const anchors = [], propsC = [];
  for (const c of comps.values()) {
    const w = c.x1 - c.x0, d = c.z1 - c.z0;
    if (c.y0 > 0.35) continue; // hangs in the air on its own (the sun, a bird): leave it be
    if (c.av || w > BIG || d > BIG || w * d > BIG * BIG * 0.75 || c.y0 < -0.5 || c.x0 < X0 + 0.5 || c.x1 > X1 - 0.5 || c.z0 < Z0 + 0.5 || c.z1 > Z1 - 0.5) anchors.push(c); else propsC.push(c);
  }
  // ---- how far every cell is from something that keeps the ground flat (chamfer distance, in m)
  const dist = new Float32Array(nx * nz).fill(1e4);
  const pin = (x0, z0, x1, z1) => { for (let i = Math.max(0, Math.floor(x0 - X0)); i < Math.min(nx, Math.ceil(x1 - X0)); i++) for (let j = Math.max(0, Math.floor(z0 - Z0)); j < Math.min(nz, Math.ceil(z1 - Z0)); j++) dist[C(i, j)] = 0; };
  for (const c of anchors) for (const b of c.list) if (b.min[1] < 12) pin(b.min[0], b.min[2], b.max[0], b.max[2]);
  for (const f of o.flat || []) pin(f[0], f[1], f[2], f[3]);
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) if (!ok[C(i, j)] || i === 0 || j === 0 || i === nx - 1 || j === nz - 1) dist[C(i, j)] = 0;
  const relax = (i, j, ii, jj, w) => { if (ii >= 0 && jj >= 0 && ii < nx && jj < nz && dist[C(ii, jj)] + w < dist[C(i, j)]) dist[C(i, j)] = dist[C(ii, jj)] + w; };
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) { relax(i, j, i - 1, j, 1); relax(i, j, i, j - 1, 1); relax(i, j, i - 1, j - 1, 1.414); relax(i, j, i - 1, j + 1, 1.414); }
  for (let i = nx - 1; i >= 0; i--) for (let j = nz - 1; j >= 0; j--) { relax(i, j, i + 1, j, 1); relax(i, j, i, j + 1, 1); relax(i, j, i + 1, j + 1, 1.414); relax(i, j, i + 1, j - 1, 1.414); }
  // ---- the shape: three sizes of noise, pushed so there are real hills and real hollows, held flat near the anchors
  const n1 = lattice(o.seed | 0), n2 = lattice((o.seed | 0) + 101), n3 = lattice((o.seed | 0) + 202);
  const near = o.near ?? 1.2, far = o.far ?? 5.5;
  const H = new Float32Array(vx * vz), fixed = new Uint8Array(vx * vz);
  const dv = (i, j) => { let m = 1e4; for (const [a, b] of [[i - 1, j - 1], [i, j - 1], [i - 1, j], [i, j]]) m = Math.min(m, a < 0 || b < 0 || a >= nx || b >= nz ? 0 : dist[C(a, b)]); return m; };
  for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) {
    const x = X0 + i, z = Z0 + j, d = dv(i, j);
    if (d <= 0) { fixed[V(i, j)] = 1; continue; }
    let n = (0.5 * n1(x / 27, z / 27) + 0.38 * n2(x / 12.5, z / 12.5) + 0.12 * n3(x / 6, z / 6)) * 2.4;
    n = Math.max(-1, Math.min(1, n));
    let h = n > 0 ? n * up : n * down;
    for (const w of o.washes || []) { // a wash: a dry ditch along a line of points, w.w m to each side, w.d deep in the middle
      let dd = 1e9;
      for (let q = 0; q + 1 < w.pts.length; q++) { const [ax, az] = w.pts[q], [bx, bz] = w.pts[q + 1], ex = bx - ax, ez = bz - az, t = Math.max(0, Math.min(1, ((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez))); dd = Math.min(dd, Math.hypot(x - ax - ex * t, z - az - ez * t)); }
      const k = 1 - sm(w.w * 0.25, w.w, dd);
      if (k > 0) h = h * (1 - k) + Math.min(h, -w.d) * k + 0.25 * sm(w.w, w.w * 1.5, dd) * 0; // (the bed sits at -d whatever the hill it cuts through)
    }
    H[V(i, j)] = h * sm(near, far, d);
  }
  // ---- ponds: a hollow with a natural outline dug under a water surface the map draws a little below the ground.
  // o.ponds = [{ c: [x, z], r: [rx, rz] (its rough size), d (how deep in the middle), wl (how far below the ground the
  // water lies), box (the water surface's rectangle), seed }]. the outline is a wobbly blob, the sand tapers down to the
  // waterline and on down under it, and the rest of the water's rectangle stays above the water (so only the blob shows)
  for (const p of o.ponds || []) {
    const [cx, cz] = p.c, [rx, rz] = p.r, wl = p.wl ?? 0.25, k = (p.seed || 1) * 1.7, R1 = 1.4; // (R1: where the bank has climbed back to the ground round it)
    const q = (x, z) => { const a = Math.atan2((z - cz) / rz, (x - cx) / rx); return Math.hypot((x - cx) / rx, (z - cz) / rz) / (1 + 0.17 * Math.sin(2 * a + k) + 0.11 * Math.sin(3 * a + k * 2.3) + 0.06 * Math.sin(5 * a + k * 0.7)); };
    const m = Math.max(rx, rz) * 2;
    for (let i = Math.max(0, Math.floor(cx - m - X0)); i <= Math.min(nx, Math.ceil(cx + m - X0)); i++) for (let j = Math.max(0, Math.floor(cz - m - Z0)); j <= Math.min(nz, Math.ceil(cz + m - Z0)); j++) {
      const x = X0 + i, z = Z0 + j, v = q(x, z), n = V(i, j), inBox = p.box && x >= p.box[0] && x <= p.box[2] && z >= p.box[1] && z <= p.box[3];
      if (v < 1) { H[n] = -wl - (p.d - wl) * sm(0, 0.62, 1 - v); fixed[n] = 1; } // under the water: shelving, then the deep middle
      else if (v < R1) { const t = sm(1, R1, v); H[n] = -wl * (1 - t) + Math.max(H[n], 0) * t; fixed[n] = 1; } // the bank: tapering down to the waterline
      else if (inBox && H[n] < -wl + 0.15) H[n] = -wl + 0.15; // (no second puddle with a ruler-straight edge)
    }
  }
  // ---- relief: big set shapes the map asks for by name (a volcano's cone). o.relief = [{ f: (x, z) => height or null, mat }]: where f
  // answers, that IS the ground (whatever stands near), drawn in mat. things built on it are put at y 0 and ride up with it
  const rocky = new Set();
  for (const rf of o.relief || []) {
    let k = mats.indexOf(rf.mat || mat); if (k < 0) { mats.push(rf.mat); k = mats.length - 1; }
    if (rf.rock) rocky.add(rf.mat || mat); // (drawn as hard facets, ridges lit and cracks dark: world.js)
    for (let i = 0; i < vx; i++) for (let j = 0; j < vz; j++) { const v = rf.f(X0 + i, Z0 + j); if (v != null) { H[V(i, j)] = v; fixed[V(i, j)] = 1; } }
    for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) if (rf.paint ? rf.paint(X0 + i + 0.5, Z0 + j + 0.5) : rf.f(X0 + i + 0.5, Z0 + j + 0.5) != null) paint[C(i, j)] = k; // (rf.paint: where it takes rf.mat; the rest keeps the ground's own)
  }
  // ---- small things get a level pad at the height the ground has under their middle, and go up or down with it
  const at0 = (x, z) => { const fx = Math.max(0, Math.min(nx - 1e-6, x - X0)), fz = Math.max(0, Math.min(nz - 1e-6, z - Z0)), i = Math.floor(fx), j = Math.floor(fz), u = fx - i, v = fz - j; return (H[V(i, j)] * (1 - u) + H[V(i + 1, j)] * u) * (1 - v) + (H[V(i, j + 1)] * (1 - u) + H[V(i + 1, j + 1)] * u) * v; };
  const PAD = o.pad ?? 2.2, sw = new Float32Array(vx * vz), swp = new Float32Array(vx * vz), mw = new Float32Array(vx * vz);
  for (const c of propsC) {
    c.p = at0((c.x0 + c.x1) / 2, (c.z0 + c.z1) / 2);
    for (let i = Math.max(0, Math.floor(c.x0 - PAD - X0)); i <= Math.min(nx, Math.ceil(c.x1 + PAD - X0)); i++) for (let j = Math.max(0, Math.floor(c.z0 - PAD - Z0)); j <= Math.min(nz, Math.ceil(c.z1 + PAD - Z0)); j++) {
      const x = X0 + i, z = Z0 + j, ox = Math.max(c.x0 - 0.5 - x, 0, x - c.x1 - 0.5), oz = Math.max(c.z0 - 0.5 - z, 0, z - c.z1 - 0.5), w = 1 - sm(0, PAD, Math.hypot(ox, oz));
      if (w <= 0) continue;
      const k = V(i, j); sw[k] += w; swp[k] += w * c.p; if (w > mw[k]) mw[k] = w;
    }
  }
  for (let k = 0; k < vx * vz; k++) if (mw[k] > 0 && !fixed[k]) { H[k] = H[k] * (1 - mw[k]) + (swp[k] / sw[k]) * mw[k]; }
  // ---- nothing steeper than you can run up without noticing: ease the steep bits (the flat parts stay put; two pads at different heights side by side give a little)
  const MAXS = o.slope ?? 0.36;
  for (let pass = 0; pass < 60; pass++) {
    let any = false;
    for (let i = 1; i < vx - 1; i++) for (let j = 1; j < vz - 1; j++) {
      const k = V(i, j);
      if (fixed[k]) continue;
      const a = H[V(i - 1, j)], b = H[V(i + 1, j)], c = H[V(i, j - 1)], d = H[V(i, j + 1)], h = H[k];
      if (Math.max(Math.abs(h - a), Math.abs(h - b), Math.abs(h - c), Math.abs(h - d)) > MAXS) { H[k] = (a + b + c + d + h * 2) / 6; any = true; }
    }
    if (!any) break;
  }
  // ---- o.coarse (a whole number of metres, huge maps): where a coarse x coarse block of cells is all ground, all one paint and has
  // nothing pinned off the patch inside it, its inner points are put on the plane-ish patch through its four corners, so the client can draw
  // the block as one quad (a quarter of the triangles at 2) and feet still land exactly where it's drawn. blocks[bi * nbz + bj] = 1
  const CS = o.coarse | 0, nbx = CS > 1 ? Math.floor(nx / CS) : 0, nbz = CS > 1 ? Math.floor(nz / CS) : 0, blocks = CS > 1 ? new Uint8Array(nbx * nbz) : null;
  for (let bi = 0; bi < nbx; bi++) for (let bj = 0; bj < nbz; bj++) {
    const i0 = bi * CS, j0 = bj * CS; let good = true;
    const a = H[V(i0, j0)], b = H[V(i0 + CS, j0)], c = H[V(i0, j0 + CS)], d = H[V(i0 + CS, j0 + CS)];
    for (let u = 0; u <= CS && good; u++) for (let v = 0; v <= CS; v++) {
      if (u < CS && v < CS && (!ok[C(i0 + u, j0 + v)] || paint[C(i0 + u, j0 + v)] !== paint[C(i0, j0)])) { good = false; break; }
      const fu = u / CS, fv = v / CS; // (a pinned point may stay if it's already on the patch: level ground under a road is all pinned, and all one plane)
      if (fixed[V(i0 + u, j0 + v)] && Math.abs(H[V(i0 + u, j0 + v)] - ((a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv)) > 1e-4) { good = false; break; }
    }
    if (!good) continue;
    blocks[bi * nbz + bj] = 1;
    for (let u = 0; u <= CS; u++) for (let v = 0; v <= CS; v++) { const fu = u / CS, fv = v / CS; H[V(i0 + u, j0 + v)] = (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv; }
  }
  const at = (x, z) => { const i = Math.floor(x - X0), j = Math.floor(z - Z0); return i < 0 || j < 0 || i >= nx || j >= nz || !ok[C(i, j)] ? null : at0(x, z); };
  for (const c of propsC) {
    let dy = 1e9;
    for (const [x, z] of [[(c.x0 + c.x1) / 2, (c.z0 + c.z1) / 2], [c.x0, c.z0], [c.x1, c.z0], [c.x0, c.z1], [c.x1, c.z1]]) dy = Math.min(dy, at0(x, z)); // on the lowest bit under it: nothing floats
    c.dy = dy;
    for (const b of c.list) { b.min[1] += dy; b.max[1] += dy; }
    for (const L of [B.boxes, D.boxes]) for (const p of L.props || []) { const q = p.p || p.a; if (q && !p._t && q[0] > c.x0 - 0.3 && q[0] < c.x1 + 0.3 && q[2] > c.z0 - 0.3 && q[2] < c.z1 + 0.3) { q[1] += dy; p._t = 1; } } // (p: a placed model, a: a kit prop's anchor, shared/propcap.js)
  }
  for (const L of [B.boxes, D.boxes]) for (const p of L.props || []) delete p._t;
  // ---- the hidden steps under it: every cell a box up to the middle of its four corners, runs of the same height merged
  let lo = 0, hi = 0;
  for (let k = 0; k < vx * vz; k++) { if (H[k] < lo) lo = H[k]; if (H[k] > hi) hi = H[k]; }
  const BASE = Math.min(-0.6, Math.floor((lo - 0.35) * 10) / 10);
  const UNDER = BASE - 0.5;
  for (const s of slabs) { s.max[1] = BASE; if (s.min[1] > UNDER) s.min[1] = UNDER; s.ter = 1; } // (a deep pond can go below the old slab's underside)
  // ...and below the top of whatever big layer lay under the slabs (the dirt): that comes down too, or it's an unseen floor across the pond
  for (const b of B.boxes) if (!b.ter && inR(b) && b.max[1] <= -1 && b.max[1] > UNDER && b.min[1] < UNDER - 0.5 && (b.max[0] - b.min[0]) * (b.max[2] - b.min[2]) > 1000) b.max[1] = UNDER;
  const top = new Int16Array(nx * nz); // in 5 cm steps
  const QS = o.step || 0.05;
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) top[C(i, j)] = Math.round((H[V(i, j)] + H[V(i + 1, j)] + H[V(i, j + 1)] + H[V(i + 1, j + 1)]) / 4 / QS);
  // (o.step: how coarse the hidden steps are, m. 0.05 unless a huge map asks for fewer, bigger ones: bodies ride the heightfield, the steps only stop you walking into a hillside)
  const runs = new Map(); // "z0,z1,q" -> the run in the column before, still growing along x
  let nTer = 0;
  for (let i = 0; i <= nx; i++) {
    const seen = new Set();
    if (i < nx) for (let j = 0; j < nz;) {
      if (!ok[C(i, j)]) { j++; continue; }
      let e = j + 1;
      while (e < nz && ok[C(i, e)] && top[C(i, e)] === top[C(i, j)]) e++;
      const key = j + ',' + e + ',' + top[C(i, j)], r = runs.get(key);
      if (r && r.x1 === i) r.x1 = i + 1; else { if (r) flush(r); runs.set(key, { j, e, q: top[C(i, j)], x0: i, x1: i + 1 }); }
      seen.add(key); j = e;
    }
    for (const [key, r] of runs) if (!seen.has(key)) { flush(r); runs.delete(key); }
  }
  function flush(r) { B.boxes.push({ min: [X0 + r.x0, BASE, Z0 + r.j], max: [X0 + r.x1, r.q * QS, Z0 + r.e], mat, ter: 1, ...(o.soft ? { sw: o.soft } : null) }); nTer++; }
  // ---- where the ground stops at a drop (the canyon's lip, the shaft): a strip of it down the face, so the lowered slab doesn't show as a gap
  let eTop = 0, eMat = mat;
  const edge = (x0, z0, x1, z1) => D.add(x0, UNDER, z0, x1, eTop, z1, eMat);
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) {
    if (!ok[C(i, j)]) continue;
    const x = X0 + i, z = Z0 + j, t = 0.04;
    eTop = Math.max(0, Math.min(H[V(i, j)], H[V(i + 1, j)], H[V(i, j + 1)], H[V(i + 1, j + 1)])); eMat = mats[paint[C(i, j)]]; // (a shaft down through a hill: its wall goes all the way up)
    if (i > 0 && !ok[C(i - 1, j)]) edge(x, z, x + t, z + 1);
    if (i < nx - 1 && !ok[C(i + 1, j)]) edge(x + 1 - t, z, x + 1, z + 1);
    if (j > 0 && !ok[C(i, j - 1)]) edge(x, z, x + 1, z + t);
    if (j < nz - 1 && !ok[C(i, j + 1)]) edge(x, z + 1 - t, x + 1, z + 1);
  }
  // ---- spawns and the like: onto the new ground
  for (const p of o.points || []) if (p[1] > -0.5 && p[1] < 0.6) { const g = at(p[0], p[2]); if (g != null) p[1] += g; }
  const terrain = { x0: X0, z0: Z0, nx, nz, H, ok, mat, mats, paint, rocky, lo, hi, coarse: CS > 1 ? { s: CS, nbx, nbz, blocks } : null, climb: 0.85 + ((o.soft || 0.7) - 0.7), base: BASE, at, box: { min: [X0, BASE, Z0], max: [X1, hi, Z1], mat, terr: 1 }, stats: { anchors: anchors.length, props: propsC.length, steps: nTer } };
  Object.defineProperty(B.boxes, 'terrain', { value: terrain, writable: true, configurable: true, enumerable: false });
  return terrain;
}
// the ground's height under a point on a map with shaped ground (0 where it's flat or there's none)
export const groundY = (boxes, x, z) => { const t = boxes && boxes.terrain, g = t ? t.at(x, z) : null; return g == null ? 0 : g; };
// a terrace's top 0.7 m is soft to a body whose feet are near the surface: the heightfield is the real ground there
// (below that it's a wall: the canyon's face, the side of the mine shaft)
export const softTer = (b, y) => b.ter === 1 && y > b.max[1] - (b.sw || 0.7); // (sw: a map with steep rock to walk up, o.soft, makes it deeper)
