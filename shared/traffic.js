// Traffic: the lanes cars drive on, per map, and the car types. Shared by the server (which drives every car) and the
// client (which draws them). Lanes are polylines with rounded corners; every lane is checked against the map's boxes
// when it's built so a car following it never clips into a building, a prop or a parked car.
// Render-only scenery (map.deco) that sits on a lane (a scattered tree, a camel) is cleared off it: nobody can touch it
// anyway, and both sides build the same thing, so server and client agree on what's left.
import { MAPS } from './map.js';

// L/W/H in metres (real ones: a supermini, a family saloon, a pickup, a panel van, a city bus, a box truck). wide = only
// on wide roads. mass decides who wins a shove, hp how much shooting it takes
export const CARS = {
  hatch: { L: 3.95, W: 1.76, H: 1.5, hp: 150, mass: 1.0, acc: 3.4 },
  sedan: { L: 4.7, W: 1.84, H: 1.46, hp: 190, mass: 1.25, acc: 3.0 },
  taxi: { L: 4.7, W: 1.84, H: 1.78, hp: 190, mass: 1.25, acc: 3.2 },
  pickup: { L: 5.4, W: 2.0, H: 1.92, hp: 240, mass: 1.7, acc: 2.6 },
  van: { L: 5.1, W: 2.0, H: 2.4, hp: 240, mass: 1.6, acc: 2.4 },
  icecream: { L: 5.4, W: 2.1, H: 3.05, hp: 240, mass: 1.7, acc: 2.0 },
  bus: { L: 11.8, W: 2.55, H: 3.25, hp: 520, mass: 5, acc: 1.5, wide: true },
  truck: { L: 8.8, W: 2.5, H: 3.75, hp: 460, mass: 4, acc: 1.6, wide: true },
};
export const CAR_IDS = Object.keys(CARS);
export const CAR_COLORS = ['#e8323c', '#2f6fe0', '#f2f2ee', '#26262c', '#3fae5a', '#f2c230', '#ff7ab8', '#7a4ad8', '#5ad8e8', '#b0b4bc', '#e86a22', '#8a1f2c'];

// how busy the roads are. auto: none in Plant & Defuse (it's the competitive one, with an economy) or training. calm =
// half the cars, slower, hits only shove
export const TRAFFIC_LEVELS = {
  auto: { name: 'Auto' },
  on: { name: 'On', n: 1, v: 1, lethal: true, reckless: 1 },
  calm: { name: 'Calm', n: 0.5, v: 0.65, lethal: false, reckless: 0 },
  off: { name: 'Off', n: 0 },
  rush: { name: 'Rush Hour', n: 1.8, v: 1.15, lethal: true, reckless: 3 },
};
export const TRAFFIC_ORDER = ['auto', 'on', 'calm', 'rush', 'off'];
export function trafficLevel(sel, game, mode) {
  if (mode === 'training') return TRAFFIC_LEVELS.off;
  if (!Object.hasOwn(TRAFFIC_LEVELS, sel) || sel === 'auto') return game === 'bomb' ? TRAFFIC_LEVELS.off : TRAFFIC_LEVELS.on; // competitive: no cars unless the host asks
  return TRAFFIC_LEVELS[sel];
}

// per map: routes run from a start out past the fog to an end out past the fog (cars appear and vanish where nobody can
// see), city grids are closed networks with junctions and U-turns at the edge. n = how many cars at once, every = the
// gap between spawns (s), v = speed range (m/s), mix = car type weights, lights = headlights on (dark maps)
const SUBURB_A = [[-430, -2.5], [-114, -2.5], [-100, 0], [42, 0], [49, -10.5], [62, -13], [75, -10.5], [76.3, 0], [75, 10.5], [62, 13], [49, 10.5], [42, 2.5], [13, 2.5],
  [8.5, 5.6], [-12.5, 5.6], [-17, 2.5], [-102, 2.5], [-114, 2.5], [-430, 2.5]];
export const TRAFFIC = {
  // the cul-de-sac: in past the barricade (somebody moved two of the barriers), down the middle between the bus and the
  // truck, round the founder's statue and back out, squeezing past the truck on the way. nobody reads ROAD CLOSED signs
  suburb: { n: 9, every: [2.5, 6], routes: [{ pts: SUBURB_A, v: [9, 15] }], mix: { hatch: 3, sedan: 3, pickup: 2, van: 1, icecream: 1.2 },
    open: { box: [-140, -3.8, -104, 3.8], mats: ['jersey', 'wood', 'leaves', 'leaves2', 'blossom', 'hedge'] } },
  // the road past the gate, both ways, out to the horizon
  warehouse: { n: 7, every: [3.5, 9], lights: true, mix: { sedan: 2, hatch: 2, pickup: 2, van: 2, truck: 2.5, bus: 1 },
    // (found from the road itself, so the lanes follow it if the map moves it: two lanes 3 m either side of its middle)
    routes: (map) => { const r = map.boxes.filter((b) => b.mat === 'roadz').sort((a, b) => (b.max[2] - b.min[2]) - (a.max[2] - a.min[2]))[0]; if (!r) return [];
      const cx = (r.min[0] + r.max[0]) / 2; return [{ pts: [[cx + 3, -430], [cx + 3, 430]], v: [14, 22] }, { pts: [[cx - 3, 430], [cx - 3, -430]], v: [14, 22] }]; } },
  // a desert track past the west gate, out on the sand (jump off the battlements and it's right there). north-south,
  // because east-west would have to jump the canyon
  desert: { n: 3, every: [7, 16], mix: { pickup: 4, van: 1, hatch: 1.2 },
    routes: [{ pts: [[-131, -600], [-131, 180], [-106, 207], [-106, 240], [-131, 265], [-131, 600]], v: [12, 19] }, // (round the big mesa)
      { pts: [[-137, 600], [-137, 265], [-112, 240], [-112, 207], [-137, 180], [-137, -600]], v: [12, 19] }] },
  // the neon street grids far below the towers: junctions (cars wait their turn, the odd one doesn't), U-turns at the edge
  skyline: { n: 16, lights: true, mix: { taxi: 4, sedan: 3, hatch: 2, van: 1.2, bus: 0.8, truck: 0.8 }, v: [8, 15],
    grid: { xs: [-135, -67.5, 0, 67.5, 135], zs: [-135, -67.5, 0, 67.5, 135], w: 18, S: 190, y: -100 + 0.08, off: 5 } },
  rooftop: { n: 12, lights: true, mix: { taxi: 4, sedan: 3, hatch: 2, van: 1.2, bus: 0.8, truck: 0.8 }, v: [8, 15],
    grid: { xs: [-140, -55, 55, 140], zs: [-140, -55, 55, 140], w: 18, S: 180, y: -142 + 0.08, off: 5 } },
};

TRAFFIC.warehouse_sd = TRAFFIC.warehouse; // the Plant & Defuse version keeps the same road (traffic there is off unless the host turns it on)

// ------------------------------------------------------------ geometry
// an oriented box on the ground plane: centre (x, z), unit axis (ux, uz) with half length hu, the other axis half hv
export function obbOverlap(a, b) {
  const dx = b.x - a.x, dz = b.z - a.z;
  for (const [ax, az] of [[a.ux, a.uz], [-a.uz, a.ux], [b.ux, b.uz], [-b.uz, b.ux]]) {
    const ra = a.hu * Math.abs(a.ux * ax + a.uz * az) + a.hv * Math.abs(-a.uz * ax + a.ux * az);
    const rb = b.hu * Math.abs(b.ux * ax + b.uz * az) + b.hv * Math.abs(-b.uz * ax + b.ux * az);
    if (Math.abs(dx * ax + dz * az) > ra + rb) return false;
  }
  return true;
}
// a map box as an OBB on the ground (deco boxes can be turned: rot = yaw, three's rotation.y)
export function boxObb(b) {
  const x = (b.min[0] + b.max[0]) / 2, z = (b.min[2] + b.max[2]) / 2, hu = (b.max[0] - b.min[0]) / 2, hv = (b.max[2] - b.min[2]) / 2;
  if (!b.rot) return { x, z, ux: 1, uz: 0, hu, hv };
  return { x, z, ux: Math.cos(b.rot), uz: -Math.sin(b.rot), hu, hv };
}
// a car (heading h: forward = (sin h, cos h)) as an OBB, grown by m on every side
export function carObb(x, z, h, T, m = 0) { return { x, z, ux: Math.sin(h), uz: Math.cos(h), hu: T.L / 2 + m, hv: T.W / 2 + m }; }

// round every corner of a polyline with an arc (radius r, smaller where the legs are short), points every ~1 m on arcs
function fillet(pts, r) {
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const [px, pz] = pts[i - 1], [bx, bz] = pts[i], [nx, nz] = pts[i + 1];
    let ax = bx - px, az = bz - pz, cx = nx - bx, cz = nz - bz;
    const la = Math.hypot(ax, az), lc = Math.hypot(cx, cz);
    ax /= la; az /= la; cx /= lc; cz /= lc;
    const phi = Math.acos(Math.max(-1, Math.min(1, ax * cx + az * cz)));
    if (phi < 1e-3) { out.push(pts[i]); continue; }
    const t = Math.min(r * Math.tan(phi / 2), la * 0.5, lc * 0.5), rr = t / Math.tan(phi / 2);
    const t1 = [bx - ax * t, bz - az * t], t2 = [bx + cx * t, bz + cz * t];
    let mx = cx - ax, mz = cz - az; const ml = Math.hypot(mx, mz); mx /= ml; mz /= ml; // the bisector, into the turn
    const dc = rr / Math.cos(phi / 2), ox = bx + mx * dc, oz = bz + mz * dc;
    let a1 = Math.atan2(t1[1] - oz, t1[0] - ox), a2 = Math.atan2(t2[1] - oz, t2[0] - ox);
    let da = a2 - a1; while (da > Math.PI) da -= Math.PI * 2; while (da < -Math.PI) da += Math.PI * 2;
    const n = Math.max(2, Math.ceil(Math.abs(da) * rr / 1.0));
    for (let k = 0; k <= n; k++) { const a = a1 + (da * k) / n; out.push([ox + Math.cos(a) * rr, oz + Math.sin(a) * rr]); }
  }
  out.push(pts[pts.length - 1]);
  return out.filter((p, i, l) => i === 0 || Math.hypot(p[0] - l[i - 1][0], p[1] - l[i - 1][1]) > 0.05);
}

function makeEdge(pts, y, o = {}) {
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return { pts, cum, len: cum[cum.length - 1], y, next: [], src: false, sink: false, slack: 0, j: -1, cls: '', ...o };
}
// where a car with its middle s metres along an edge is, and which way it faces (lat: metres to its right)
export function poseAt(e, s, lat = 0, out = {}) {
  s = Math.max(0, Math.min(e.len, s));
  let lo = 0, hi = e.cum.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (e.cum[m] <= s) lo = m; else hi = m; }
  const a = e.pts[lo], b = e.pts[hi], sl = e.cum[hi] - e.cum[lo] || 1, k = (s - e.cum[lo]) / sl;
  const dx = (b[0] - a[0]) / sl, dz = (b[1] - a[1]) / sl;
  out.x = a[0] + (b[0] - a[0]) * k + dz * lat; out.z = a[1] + (b[1] - a[1]) * k - dx * lat;
  out.h = Math.atan2(dx, dz); out.y = e.y;
  return out;
}

// ------------------------------------------------------------ building + checking
// a coarse grid of boxes (rotated ones by their turned footprint) so checking a long lane stays quick
function grid(boxes, kind) {
  const C = 16, cells = new Map();
  for (const b of boxes) {
    const o = boxObb(b), ex = Math.abs(o.ux) * o.hu + Math.abs(o.uz) * o.hv, ez = Math.abs(o.uz) * o.hu + Math.abs(o.ux) * o.hv;
    for (let i = Math.floor((o.x - ex) / C); i <= Math.floor((o.x + ex) / C); i++) for (let j = Math.floor((o.z - ez) / C); j <= Math.floor((o.z + ez) / C); j++) {
      const k = i * 7919 + j; if (!cells.has(k)) cells.set(k, []); cells.get(k).push(b);
    }
  }
  return { C, cells, kind };
}
function near(g, x0, z0, x1, z1, out) {
  for (let i = Math.floor(x0 / g.C); i <= Math.floor(x1 / g.C); i++) for (let j = Math.floor(z0 / g.C); j <= Math.floor(z1 / g.C); j++) for (const b of g.cells.get(i * 7919 + j) || []) out.add(b);
  return out;
}
// the floor under a point: the highest top within a metre of where the lane says the road is
function floorAt(gs, x, z, y0) {
  let best = -1e9;
  for (const g of gs) for (const b of near(g, x, z, x, z, new Set())) {
    if (b.rot || x < b.min[0] || x > b.max[0] || z < b.min[2] || z > b.max[2]) continue;
    if (b.max[1] <= y0 + 1 && b.max[1] > best) best = b.max[1];
  }
  return best > -1e8 ? best : y0;
}
// every box a car the size of T would touch anywhere along an edge (grown sideways by slack): the swept corridor is cut
// into one OBB per segment, stretched by half a car each way so its nose and tail are covered at the corners too
function blockers(e, T, gs, slack = 0) {
  const hits = new Set();
  for (let i = 1; i < e.pts.length; i++) {
    const [ax, az] = e.pts[i - 1], [bx, bz] = e.pts[i], l = Math.hypot(bx - ax, bz - az);
    if (l < 1e-4) continue;
    const ob = { x: (ax + bx) / 2, z: (az + bz) / 2, ux: (bx - ax) / l, uz: (bz - az) / l, hu: l / 2 + T.L / 2, hv: T.W / 2 + 0.25 + slack };
    const r = ob.hu + ob.hv, y0 = e.y + 0.3, y1 = e.y + T.H + 0.25;
    for (const g of gs) for (const b of near(g, ob.x - r, ob.z - r, ob.x + r, ob.z + r, new Set())) {
      if (b.max[1] <= y0 || b.min[1] >= y1 || b.noCar) continue;
      if (obbOverlap(ob, boxObb(b))) hits.add(b);
    }
  }
  return hits;
}

function cityGrid(o, edges) {
  const half = o.w / 2, off = o.off, end = o.S - 14, J = [];
  for (const X of o.xs) for (const Z of o.zs) J.push({ x: X, z: Z });
  const jid = (X, Z) => J.findIndex((j) => j.x === X && j.z === Z);
  // a directed lane: axis 'z' runs along z on the road at line=X, axis 'x' along x at line=Z; d = +1 / -1
  const lanes = [];
  for (const X of o.xs) for (const d of [1, -1]) lanes.push({ axis: 'z', line: X, d, cross: o.zs });
  for (const Z of o.zs) for (const d of [1, -1]) lanes.push({ axis: 'x', line: Z, d, cross: o.xs });
  const P = (L, along) => (L.axis === 'z' ? [L.line + L.d * off, along] : [along, L.line - L.d * off]); // keep to the right
  const key = (L) => `${L.axis}${L.line}${L.d}`;
  const into = new Map(); // `${junction}|${lane}`: the link that arrives there; `start|lane`: the lane's first link
  const out = new Map(); // `${junction}|${lane}`: the link that leaves from there
  for (const L of lanes) {
    const cs = [...L.cross].sort((a, b) => (a - b) * L.d);
    let from = -L.d * end, prev = 'start';
    for (const c of cs) {
      const e = makeEdge([P(L, from), P(L, c - L.d * (half + 1))], o.y, { src: true });
      edges.push(e);
      into.set(`${L.axis === 'z' ? jid(L.line, c) : jid(c, L.line)}|${key(L)}`, e);
      if (prev === 'start') into.set(`start|${key(L)}`, e); else out.get(prev).next.push(e);
      prev = `${L.axis === 'z' ? jid(L.line, c) : jid(c, L.line)}|${key(L)}`;
      out.set(prev, { next: [] });
      from = c + L.d * (half + 1);
    }
    const last = makeEdge([P(L, from), P(L, L.d * end)], o.y, { src: true, endOf: key(L) });
    edges.push(last); out.get(prev).next.push(last);
  }
  // manoeuvres inside each junction: straight on, or round the corner into the other road
  for (const [k, slot] of out) {
    const [j, lk] = k.split('|'), jj = J[+j], Lin = lanes.find((L) => key(L) === lk), arrive = into.get(k);
    const exitOf = (L) => out.get(`${j}|${key(L)}`);
    for (const L of lanes) {
      const crossing = L.axis !== Lin.axis && L.line === (Lin.axis === 'z' ? jj.z : jj.x);
      const ahead = key(L) === lk;
      if (!crossing && !ahead) continue;
      const a = arrive.pts[arrive.pts.length - 1], ex = exitOf(L), b = ex.next[0].pts[0];
      let pts;
      if (ahead) pts = [a, b];
      else { const corner = Lin.axis === 'z' ? [a[0], b[1]] : [b[0], a[1]]; pts = fillet([a, corner, b], 40); }
      const m = makeEdge(pts, o.y, { j: +j, cls: ahead ? Lin.axis : 'turn' });
      m.next = ex.next; // (filled in below: the link out)
      edges.push(m); arrive.next.push(m);
    }
  }
  // the link out of each junction was a placeholder: point the manoeuvres at the real one
  for (const e of edges) if (e.j >= 0) e.next = e.next.slice();
  // U-turns at the edge of the grid, onto the other side of the same road
  for (const L of lanes) {
    const lastE = edges.find((e) => e.endOf === key(L)), R = lanes.find((q) => q.axis === L.axis && q.line === L.line && q.d === -L.d), back = into.get(`start|${key(R)}`);
    const c = L.axis === 'z' ? [L.line, L.d * end] : [L.d * end, L.line], pts = [];
    for (let k = 0; k <= 16; k++) {
      const t = (Math.PI * k) / 16;
      if (L.axis === 'z') pts.push([c[0] + L.d * off * Math.cos(t), c[1] + L.d * off * Math.sin(t)]);
      else pts.push([c[0] + L.d * off * Math.sin(t), c[1] - L.d * off * Math.cos(t)]);
    }
    const u = makeEdge(pts, o.y, { uturn: true });
    u.next = [back]; lastE.next = [u]; edges.push(u);
  }
  return J.map((j) => ({ x0: j.x - half, x1: j.x + half, z0: j.z - half, z1: j.z + half }));
}

const NETS = {};
const LOG = [];
function build(id) {
  const cfg = TRAFFIC[id], map = MAPS[id];
  if (!cfg || !map) return null;
  const edges = [];
  let junctions = [];
  if (cfg.grid) { // the street height comes from the streets themselves (the y in TRAFFIC is only a fallback)
    const X = cfg.grid.xs[0], road = map.deco.find((b) => b.mat === 'wetroadz' && !b.rot && b.min[0] <= X && b.max[0] >= X && b.max[2] - b.min[2] > 100);
    junctions = cityGrid(road ? { ...cfg.grid, y: road.max[1] } : cfg.grid, edges);
  }
  for (const r of (typeof cfg.routes === 'function' ? cfg.routes(map) : cfg.routes) || []) {
    const e = makeEdge(fillet(r.pts, r.r || 14), 0, { src: true, sink: true, v: r.v, route: true });
    edges.push(e);
  }
  // the lanes' own clearing: deco on a lane goes, and so does anything the map lets traffic move (map.open)
  if (cfg.open) {
    const [x0, z0, x1, z1] = cfg.open.box;
    const gone = new Set(map.boxes.filter((b) => cfg.open.mats.includes(b.mat) && b.max[0] > x0 && b.min[0] < x1 && b.max[2] > z0 && b.min[2] < z1));
    // a tree goes whole: the trunk takes its canopy with it
    for (const b of map.boxes) if (cfg.open.mats.includes(b.mat) && [...gone].some((q) => Math.hypot((q.min[0] + q.max[0] - b.min[0] - b.max[0]) / 2, (q.min[2] + q.max[2] - b.min[2] - b.max[2]) / 2) < 0.3)) gone.add(b);
    if (gone.size) { const keep = map.boxes.filter((b) => !gone.has(b)); map.boxes.length = 0; map.boxes.push(...keep); LOG.push(`${id}: opened ${gone.size} boxes for the road`); }
  }
  const gB = grid(map.boxes, 'B');
  const types = Object.keys(cfg.mix).filter((t) => CARS[t]);
  const biggest = (list) => ({ L: Math.max(...list.map((t) => CARS[t].L)), W: Math.max(...list.map((t) => CARS[t].W)), H: Math.max(...list.map((t) => CARS[t].H)) });
  // floors first (route lanes take the height of whatever road they're on), then deco off the lanes
  for (const e of edges) if (e.route) { e.y = floorAt([gB, grid(map.deco, 'D')], e.pts[0][0], e.pts[0][1], 0.2); }
  const T = biggest(types);
  const decoHits = new Set();
  let gD = grid(map.deco, 'D');
  for (const e of edges) for (const b of blockers(e, T, [gD])) decoHits.add(b);
  if (decoHits.size) {
    const gone = new Set(decoHits); // and whatever stands on the same spot (a tree's canopy, a camel's head)
    const col = (q, b) => Math.hypot((q.min[0] + q.max[0] - b.min[0] - b.max[0]) / 2, (q.min[2] + q.max[2] - b.min[2] - b.max[2]) / 2) < 0.8 && b.max[1] - b.min[1] > 0.15 && b.max[1] - b.min[1] < 30;
    for (const b of map.deco) if (!gone.has(b) && [...decoHits].some((q) => col(q, b) || b.max[0] > q.min[0] - 0.4 && b.min[0] < q.max[0] + 0.4 && b.max[2] > q.min[2] - 0.4 && b.min[2] < q.max[2] + 0.4 && Math.hypot((q.min[0] + q.max[0] - b.min[0] - b.max[0]) / 2, (q.min[2] + q.max[2] - b.min[2] - b.max[2]) / 2) < 3.5 && b.min[1] >= q.min[1] - 0.05 && b.max[1] > q.min[1] + 0.3 && b.min[1] < q.max[1] + 8 && b.max[1] - b.min[1] < 30)) gone.add(b);
    const keep = map.deco.filter((b) => !gone.has(b)); map.deco.length = 0; map.deco.push(...keep);
    LOG.push(`${id}: cleared ${gone.size} deco boxes off the lanes`);
    gD = grid(map.deco, 'D');
  }
  // solid stuff can't be moved: a lane that hits any is dropped (and the big types go first if only they don't fit)
  let ok = types.slice();
  const bad = new Set();
  for (const e of edges) {
    const h = blockers(e, biggest(ok), [gB, gD]);
    if (h.size && ok.some((t) => CARS[t].wide)) {
      const narrow = ok.filter((t) => !CARS[t].wide);
      if (narrow.length && !blockers(e, biggest(narrow), [gB, gD]).size) { LOG.push(`${id}: no buses or trucks (${[...h][0].mat} at ${[...h][0].min.map(Math.round)})`); ok = narrow; continue; }
    }
    if (h.size) { bad.add(e); LOG.push(`${id}: lane dropped, ${h.size} boxes in the way (${[...h].slice(0, 6).map((b) => `${b.mat}@${b.min.map((v) => v.toFixed(1))}..${b.max.map((v) => v.toFixed(1))}`).join(' ')})`); }
  }
  const live = edges.filter((e) => !bad.has(e));
  for (const e of live) e.next = e.next.filter((n) => !bad.has(n));
  for (const e of live) { // room to swerve round someone without leaving the clear corridor
    for (const s of [1.2, 0.8, 0.4]) if (!blockers(e, biggest(ok), [gB, gD], s).size) { e.slack = s; break; }
  }
  live.forEach((e, i) => { e.id = i; });
  const mix = ok.map((t) => [t, cfg.mix[t]]);
  return { id, edges: live, junctions, mix, cfg, lights: !!cfg.lights };
}
export function trafficNet(id) { return Object.hasOwn(NETS, id) ? NETS[id] : null; }
export function trafficLog() { return LOG.slice(); }
for (const id of Object.keys(TRAFFIC)) { try { NETS[id] = build(id); } catch (e) { LOG.push(`${id}: traffic failed to build: ${e.message}`); NETS[id] = null; } }
