// Walk graphs for maze maps. Bots can't path-find on their own (they walk straight at things), so a maze map
// can carry a graph: a node in the middle of every grid cell you can stand in, links between neighbouring cells
// you can walk straight between, plus stairs and one-way drops between levels. Built once by the map generator
// from its own boxes; the server's bots follow it whenever the straight line to where they want to go is blocked.

const R = 0.45; // bot half-width + a bit of slack
const K = (i, j) => (i + 100) * 1000 + j + 100; // cell key (cells can be a little outside the grid)

// does the 2D segment (ax, az) + t*(dx, dz), t in [0, 1], pass through rect [x0, z0, x1, z1] shrunk by s?
function hits(r, s, ax, az, dx, dz) {
  let t0 = 0, t1 = 1;
  const x0 = r[0] + s, z0 = r[1] + s, x1 = r[2] - s, z1 = r[3] - s;
  if (Math.abs(dx) < 1e-9) { if (ax <= x0 || ax >= x1) return false; } else {
    let a = (x0 - ax) / dx, b = (x1 - ax) / dx;
    if (a > b) { const q = a; a = b; b = q; }
    if (a > t0) t0 = a; if (b < t1) t1 = b; if (t0 >= t1) return false;
  }
  if (Math.abs(dz) < 1e-9) { if (az <= z0 || az >= z1) return false; } else {
    let a = (z0 - az) / dz, b = (z1 - az) / dz;
    if (a > b) { const q = a; a = b; b = q; }
    if (a > t0) t0 = a; if (b < t1) t1 = b; if (t0 >= t1) return false;
  }
  return true;
}

// can a bot walk in a straight line from a to b on level lv? (no walls, pillars, rails or holes in the way)
// already brushing something at the start? then only the thing itself blocks, not the slack around it
export function navClear(g, lv, ax, az, bx, bz) {
  const C = g.cell, ob = g.obs[lv], dx = bx - ax, dz = bz - az;
  let cx = Math.floor((ax - g.x0) / C), cz = Math.floor((az - g.z0) / C);
  const sx = dx > 0 ? 1 : -1, sz = dz > 0 ? 1 : -1;
  const tdx = Math.abs(dx) > 1e-9 ? C / Math.abs(dx) : Infinity, tdz = Math.abs(dz) > 1e-9 ? C / Math.abs(dz) : Infinity;
  let tx = Math.abs(dx) > 1e-9 ? (dx > 0 ? g.x0 + (cx + 1) * C - ax : ax - g.x0 - cx * C) / Math.abs(dx) : Infinity;
  let tz = Math.abs(dz) > 1e-9 ? (dz > 0 ? g.z0 + (cz + 1) * C - az : az - g.z0 - cz * C) / Math.abs(dz) : Infinity;
  for (let n = 0; n < 1000; n++) {
    const list = ob.get(K(cx, cz));
    if (list) for (const r of list) if (hits(r, ax > r[0] && ax < r[2] && az > r[1] && az < r[3] ? R : 0, ax, az, dx, dz)) return false;
    if (Math.min(tx, tz) > 1) return true;
    if (tx < tz) { tx += tdx; cx += sx; } else { tz += tdz; cz += sz; }
  }
  return true;
}

// o: { x0, z0, n, cell, levels: [floor y, ...], stairs: [{ top, bot }], drops: [{ from, to }] } (points are [x, y, z]),
// band (floors up to this much above a level count as that level), keep(x, z) (false = no node there)
export function buildNav(boxes, o) {
  const { x0, z0, n, cell: C } = o;
  // memory: a city-sized map has ~140k nodes and ~1M links, so links are packed into typed arrays (see packNav below)
  // instead of an array per node, and the cell -> nodes lookup is a linked list in typed arrays, not a Map of arrays
  const g = { x0, z0, n, cell: C, levels: o.levels, obs: [], nodes: [], lvl: [] };
  const at = []; // per level: cell -> node index
  let ea = new Int32Array(1 << 16), eb = new Int32Array(1 << 16), ec = new Float64Array(1 << 16), ne = 0; // links, one entry per direction
  const addNode = (p, lv) => {
    const k = g.nodes.length;
    g.nodes.push(p); g.lvl.push(lv);
    return k;
  };
  const edge = (a, b, c) => {
    if (ne === ea.length) { const grow = (t) => { const u = new t.constructor(t.length * 2); u.set(t); return u; }; ea = grow(ea); eb = grow(eb); ec = grow(ec); }
    ea[ne] = a; eb[ne] = b; ec[ne] = c; ne++;
  };
  const link = (a, b, oneWay) => {
    const p = g.nodes[a], q = g.nodes[b], c = Math.hypot(p[0] - q[0], p[2] - q[2]) + Math.abs(p[1] - q[1]) * 0.5;
    edge(a, b, c);
    if (!oneWay) edge(b, a, c);
  };
  const bucket = (ob, r) => {
    for (let i = Math.floor((r[0] - x0) / C); i <= Math.floor((r[2] - x0) / C); i++) for (let j = Math.floor((r[1] - z0) / C); j <= Math.floor((r[3] - z0) / C); j++) {
      const k = K(i, j);
      if (!ob.has(k)) ob.set(k, []);
      ob.get(k).push(r);
    }
  };
  const band = o.band || 0; // outdoor maps: every floor top from y up to y + band (curbs, sidewalks, porches) is one level
  o.levels.forEach((y, lv) => {
    const ob = new Map(), floor = new Uint8Array(n * n);
    for (const b of boxes) {
      if (b.pad) { bucket(ob, [b.min[0] - R, b.min[2] - R, b.max[0] + R, b.max[2] + R]); continue; } // jump pads: a bot walking over one gets launched
      if (b.max[1] > y - 0.06 && b.max[1] < y + band + 0.06) { // a floor on this level: mark the cells whose middle it holds up
        const i0 = Math.floor((b.min[0] - x0) / C), i1 = Math.floor((b.max[0] - x0) / C), j0 = Math.floor((b.min[2] - z0) / C), j1 = Math.floor((b.max[2] - z0) / C);
        for (let i = Math.max(0, i0); i <= Math.min(n - 1, i1); i++) for (let j = Math.max(0, j0); j <= Math.min(n - 1, j1); j++) {
          const cx = x0 + (i + 0.5) * C, cz = z0 + (j + 0.5) * C;
          if (cx > b.min[0] && cx < b.max[0] && cz > b.min[2] && cz < b.max[2]) floor[i * n + j] = 1;
        }
      }
      if (b.max[1] > y + (band ? band + 0.06 : 0.3) && b.min[1] < y + 1.75) bucket(ob, [b.min[0] - R, b.min[2] - R, b.max[0] + R, b.max[2] + R]); // a standing body would bump into it
    }
    // no floor = in the way too (that's how you end up on the level below). a hole cell with holes all round it is
    // skipped: a straight line from any node has to cross a hole cell on the edge of the hole first, and that blocks it
    const hole = (i, j) => i < 0 || j < 0 || i >= n || j >= n || !floor[i * n + j];
    const inner = (i, j) => i > 0 && j > 0 && i < n - 1 && j < n - 1 && hole(i - 1, j - 1) && hole(i - 1, j) && hole(i - 1, j + 1) && hole(i, j - 1) && hole(i, j + 1) && hole(i + 1, j - 1) && hole(i + 1, j) && hole(i + 1, j + 1);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (!floor[i * n + j] && !inner(i, j)) bucket(ob, [x0 + i * C - R, z0 + j * C - R, x0 + (i + 1) * C + R, z0 + (j + 1) * C + R]);
    g.obs.push(ob);
    const idx = new Int32Array(n * n).fill(-1);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      if (!floor[i * n + j]) continue;
      const cx = x0 + (i + 0.5) * C, cz = z0 + (j + 0.5) * C;
      if (o.keep && !o.keep(cx, cz)) continue; // e.g. outside the play area
      if ((ob.get(K(i, j)) || []).some((r) => cx > r[0] && cx < r[2] && cz > r[1] && cz < r[3])) continue;
      idx[i * n + j] = addNode([cx, y, cz], lv);
    }
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const a = idx[i * n + j];
      if (a < 0) continue;
      for (const [di, dj] of [[1, 0], [0, 1], [1, 1], [1, -1]]) {
        const ii = i + di, jj = j + dj;
        if (ii < 0 || jj < 0 || ii >= n || jj >= n || idx[ii * n + jj] < 0) continue;
        const b = idx[ii * n + jj], p = g.nodes[a], q = g.nodes[b];
        if (navClear(g, lv, p[0], p[2], q[0], q[2])) link(a, b);
      }
    }
    at.push(idx);
  });
  const lvOf = (p) => o.levels.reduce((best, y, lv) => (Math.abs(p[1] - y) < Math.abs(p[1] - o.levels[best]) ? lv : best), 0);
  const cellOf = (p) => { const i = Math.floor((p[0] - x0) / C), j = Math.floor((p[2] - z0) / C); return i >= 0 && j >= 0 && i < n && j < n ? at[lvOf(p)][i * n + j] : -1; };
  g.bad = [];
  for (const s of o.stairs || []) { // top landing <-> middle of the flight <-> bottom landing
    const a = cellOf(s.top), b = cellOf(s.bot);
    if (a < 0 || b < 0) { g.bad.push(s); continue; }
    const m = addNode([(s.top[0] + s.bot[0]) / 2, (s.top[1] + s.bot[1]) / 2, (s.top[2] + s.bot[2]) / 2], lvOf(s.bot));
    link(a, m); link(m, b);
  }
  for (const d of o.drops || []) { // walk off the edge, land below. no way back up the same way
    const a = cellOf(d.from), b = cellOf(d.to);
    if (a >= 0 && b >= 0) link(a, b, true); else g.bad.push(d);
  }
  packNav(g, ea, eb, ec, ne);
  return g;
}

// links -> g.off / g.to / g.cw (node k's links are to[off[k] .. off[k + 1]), cost cw[same]), in the order they were
// made; cells -> g.cellHead (per grid cell, the first node in it) / g.cellNext (the next node in the same cell)
function packNav(g, ea, eb, ec, ne) {
  const N = g.nodes.length, off = new Int32Array(N + 1), to = new Int32Array(ne), cw = new Float64Array(ne);
  for (let e = 0; e < ne; e++) off[ea[e] + 1]++;
  for (let k = 0; k < N; k++) off[k + 1] += off[k];
  const fill = off.slice(0, N);
  for (let e = 0; e < ne; e++) { const p = fill[ea[e]]++; to[p] = eb[e]; cw[p] = ec[e]; }
  Object.assign(g, { off, to, cw });
  const head = new Int32Array(g.n * g.n).fill(-1), next = new Int32Array(N).fill(-1), out = new Map(); // out: nodes off the grid
  for (let k = N - 1; k >= 0; k--) { // backwards, so each cell's list runs in node order
    const p = g.nodes[k], i = Math.floor((p[0] - g.x0) / g.cell), j = Math.floor((p[2] - g.z0) / g.cell);
    if (i >= 0 && j >= 0 && i < g.n && j < g.n) { next[k] = head[i * g.n + j]; head[i * g.n + j] = k; } else { const ck = K(i, j); out.set(ck, [k, ...(out.get(ck) || [])]); }
  }
  Object.assign(g, { cellHead: head, cellNext: next, cellOut: out });
}
// the nodes in grid cell (i, j)
function cellNodes(g, i, j, fn) {
  if (i >= 0 && j >= 0 && i < g.n && j < g.n) { for (let k = g.cellHead[i * g.n + j]; k >= 0; k = g.cellNext[k]) fn(k); return; }
  const list = g.cellOut.get(K(i, j));
  if (list) for (const k of list) fn(k);
}

// the node a point belongs to (nodes on a floor above you count for a lot less: you'd need stairs to get there)
export function navLocate(g, p) {
  const i = Math.floor((p[0] - g.x0) / g.cell), j = Math.floor((p[2] - g.z0) / g.cell);
  let best = -1, bs = 1e9;
  for (let r = 1; r <= 3 && best < 0; r++) {
    for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) {
      cellNodes(g, i + di, j + dj, (k) => {
        const q = g.nodes[k], dy = q[1] - p[1];
        const s = Math.hypot(q[0] - p[0], q[2] - p[2]) + (dy > 0.6 ? dy * 6 : Math.abs(dy) * 2);
        if (s < bs) { bs = s; best = k; }
      });
    }
  }
  return best;
}

// A* from node a to node b: list of node indices, or null if there's no way
export function navPath(g, a, b, max = g.maxExpand || Infinity) { // max: give up after expanding this many nodes (huge maps)
  const N = g.nodes.length;
  if (!g._gs || g._gs.length !== N) Object.assign(g, { _gs: new Float64Array(N), _fs: new Float64Array(N), _from: new Int32Array(N), _seen: new Uint32Array(N), _done: new Uint32Array(N), _stamp: 0 });
  const gs = g._gs, fs = g._fs, from = g._from, seen = g._seen, done = g._done, st = ++g._stamp, goal = g.nodes[b];
  const h = (k) => { const p = g.nodes[k]; return Math.hypot(p[0] - goal[0], p[2] - goal[2]) + Math.abs(p[1] - goal[1]) * 0.5; };
  const heap = [];
  const push = (k) => { let i = heap.length; heap.push(k); while (i > 0) { const p = (i - 1) >> 1; if (fs[heap[p]] <= fs[k]) break; heap[i] = heap[p]; i = p; } heap[i] = k; };
  const pop = () => {
    const top = heap[0], last = heap.pop();
    if (heap.length) {
      let i = 0;
      for (;;) { let c = 2 * i + 1; if (c >= heap.length) break; if (c + 1 < heap.length && fs[heap[c + 1]] < fs[heap[c]]) c++; if (fs[heap[c]] >= fs[last]) break; heap[i] = heap[c]; i = c; }
      heap[i] = last;
    }
    return top;
  };
  gs[a] = 0; fs[a] = h(a); from[a] = -1; seen[a] = st; push(a);
  let budget = max;
  while (heap.length) {
    if (--budget < 0) return null;
    const k = pop();
    if (k === b) { const path = []; for (let x = b; x !== -1; x = from[x]) path.push(x); return path.reverse(); }
    if (done[k] === st) continue;
    done[k] = st;
    for (let e = g.off[k], e1 = g.off[k + 1]; e < e1; e++) {
      const m = g.to[e], ng = gs[k] + g.cw[e];
      if (seen[m] === st && ng >= gs[m]) continue;
      seen[m] = st; gs[m] = ng; fs[m] = ng + h(m); from[m] = k;
      push(m);
    }
  }
  return null;
}

// Which way should a bot walk to reach goal? [x, z, hop] (a unit direction; hop = jump, it's getting itself unstuck),
// or null when it can just walk straight at it. st is the bot's own scratch object (keeps its path between calls).
export function navSteer(g, st, pos, goal, now) {
  if (now - (st.last || 0) > 400) { st.mx = pos[0]; st.mz = pos[2]; st.mt = now; } // wasn't navigating just now: restart the stuck clock
  st.last = now;
  // stuck (pushing into something for a while): sidestep and hop for a moment, then plan again
  if (now > st.mt + 1300) {
    if (Math.hypot(pos[0] - st.mx, pos[2] - st.mz) < 1.2) { st.stuck = now + 650; st.side = -(st.side || 1); st.path = null; }
    st.mx = pos[0]; st.mz = pos[2]; st.mt = now;
  }
  const a = navLocate(g, pos), b = navLocate(g, goal);
  if (a < 0 || b < 0) return null;
  const lv = g.lvl[a], stuck = now < (st.stuck || 0);
  if (now >= (st.chk || 0)) { // a straight shot? (re-checked a few times a second)
    st.chk = now + 250; st.cut = true;
    st.straight = lv === g.lvl[b] && Math.abs(goal[1] - pos[1]) < 1.5 && navClear(g, lv, pos[0], pos[2], goal[0], goal[2]);
  }
  if (st.straight && !stuck) return null;
  // plan again when the goal really moved (not every time a moving target steps into the next cell), when the plan is
  // old, and not every tick for a goal there's no way to (that searched the whole graph each time)
  const moved = st.end !== b && !(st.gx != null && Math.hypot(goal[0] - st.gx, goal[2] - st.gz) < 3);
  if (!st.path || moved || now > st.t + 3500) {
    if (st.failB === b && now < st.failT) return null;
    st.path = navPath(g, a, b); st.k = 0; st.t = now; st.end = b; st.cut = true; st.gx = goal[0]; st.gz = goal[2];
    if (!st.path) { st.failB = b; st.failT = now + 2500; return null; }
  }
  const P = st.path, N = g.nodes;
  while (st.k < P.length && Math.hypot(N[P[st.k]][0] - pos[0], N[P[st.k]][2] - pos[2]) < 1.3 && Math.abs(N[P[st.k]][1] - pos[1]) < 1.6) st.k++;
  if (st.cut) { // cut corners: skip waypoints we can already walk straight past
    st.cut = false;
    for (let s = 0; s < 8 && st.k + 1 < P.length; s++) {
      const q = N[P[st.k + 1]];
      if (g.lvl[P[st.k + 1]] !== lv || g.lvl[P[st.k]] !== lv || Math.abs(q[1] - pos[1]) > 1 || !navClear(g, lv, pos[0], pos[2], q[0], q[2])) break;
      st.k++;
    }
  }
  const tgt = st.k < P.length ? N[P[st.k]] : goal;
  let dx = tgt[0] - pos[0], dz = tgt[2] - pos[2];
  const l = Math.hypot(dx, dz) || 1;
  dx /= l; dz /= l;
  if (stuck) return [dx * 0.4 - dz * st.side, dz * 0.4 + dx * st.side, true];
  return [dx, dz, false];
}
