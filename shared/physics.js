// Box physics. Players are AABBs, projectiles are tiny AABBs, the world is AABBs.
// Position = feet (bottom center) for players.

export const PH = { halfW: 0.4, height: 1.8, eye: 1.6, step: 0.6 };
// shaped ground (shared/terrain.js): boxes.terrain is a heightfield bodies walk on. the stepped boxes under it ({ ter: 1 })
// are for everything else, and their top 0.7 m is soft to a body (below that they're a wall: the canyon's face)
const soft = (b, y) => b.ter === 1 && y > b.max[1] - 0.7;

// ------------------------------------------------------------ broadphase: a 2D grid over x/z so big maps stay fast
const CELL = 8;
let stamp = 1;
function gridOf(boxes) {
  if (boxes._grid && boxes._gridN === boxes.length) return boxes._grid;
  const cells = new Map();
  for (const b of boxes) {
    const x0 = Math.floor(b.min[0] / CELL), x1 = Math.floor(b.max[0] / CELL), z0 = Math.floor(b.min[2] / CELL), z1 = Math.floor(b.max[2] / CELL);
    for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
      const k = x * 100003 + z;
      let c = cells.get(k);
      if (!c) cells.set(k, (c = []));
      c.push(b);
    }
  }
  Object.defineProperty(boxes, '_grid', { value: cells, writable: true, configurable: true, enumerable: false });
  Object.defineProperty(boxes, '_gridN', { value: boxes.length, writable: true, configurable: true, enumerable: false });
  return cells;
}
export function resetGrid(boxes) { boxes._grid = null; boxes._gridN = -1; boxes._rgrid = null; }
// shaped ground: rays go against the heightfield itself (terrainRay), so their grid leaves its thousands of steps out
function rayGrid(boxes) {
  if (boxes._rgrid && boxes._rgridN === boxes.length) return boxes._rgrid;
  const cells = new Map();
  for (const b of boxes) {
    if (b.ter) continue;
    const x0 = Math.floor(b.min[0] / CELL), x1 = Math.floor(b.max[0] / CELL), z0 = Math.floor(b.min[2] / CELL), z1 = Math.floor(b.max[2] / CELL);
    for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) { const k = x * 100003 + z; let c = cells.get(k); if (!c) cells.set(k, (c = [])); c.push(b); }
  }
  Object.defineProperty(boxes, '_rgrid', { value: cells, writable: true, configurable: true, enumerable: false });
  Object.defineProperty(boxes, '_rgridN', { value: boxes.length, writable: true, configurable: true, enumerable: false });
  return cells;
}
// a ray against the heightfield: the first place it's under the surface (and not under the whole slab). stepped, then
// narrowed down. coming in from the side (out of the canyon, into its face) counts: that's a wall hit
function terrainRay(T, o, d, maxT) {
  let t0 = 0, t1 = maxT;
  for (const a of [0, 2]) {
    const lo = a ? T.z0 : T.x0, hi = lo + (a ? T.nz : T.nx);
    if (Math.abs(d[a]) < 1e-9) { if (o[a] < lo || o[a] > hi) return null; continue; }
    let p = (lo - o[a]) / d[a], q = (hi - o[a]) / d[a];
    if (p > q) { const w = p; p = q; q = w; }
    if (p > t0) t0 = p; if (q < t1) t1 = q;
    if (t0 > t1) return null;
  }
  if (d[1] > 1e-9) { const e = (T.hi - o[1]) / d[1]; if (e < t0) return null; if (e < t1) t1 = e; }
  else if (d[1] < -1e-9) { const e = (T.hi - o[1]) / d[1]; if (e > t0) t0 = e; if (t0 > t1) return null; }
  else if (o[1] > T.hi) return null;
  const under = (t) => { const g = T.at(o[0] + d[0] * t, o[2] + d[2] * t), y = o[1] + d[1] * t; return g != null && y < g && y > T.base - 0.02; };
  let pt = t0, side = true; // (side: the sample before was off the ground's edge)
  for (let t = t0; ; ) {
    if (under(t)) {
      if (t === t0) return { t, side: t > 0 };
      let a = pt, b = t;
      for (let i = 0; i < 9; i++) { const m = (a + b) / 2; if (under(m)) b = m; else a = m; }
      return { t: b, side };
    }
    if (t >= t1) return null;
    side = T.at(o[0] + d[0] * t, o[2] + d[2] * t) == null;
    pt = t; t = Math.min(t + 0.4, t1);
  }
}
// every box whose cell overlaps the x/z rectangle (deduped)
export function query(boxes, minx, minz, maxx, maxz, out = []) {
  const cells = gridOf(boxes);
  out.length = 0;
  const s = ++stamp;
  const x0 = Math.floor(minx / CELL), x1 = Math.floor(maxx / CELL), z0 = Math.floor(minz / CELL), z1 = Math.floor(maxz / CELL);
  if ((x1 - x0 + 1) * (z1 - z0 + 1) > 4000) return boxes; // absurdly big query: just test everything
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    const c = cells.get(x * 100003 + z);
    if (!c) continue;
    for (const b of c) if (b._q !== s) { b._q = s; out.push(b); }
  }
  return out;
}
const qMove = [], qProj = [];

function overlap(minx, miny, minz, maxx, maxy, maxz, b) {
  return minx < b.max[0] && maxx > b.min[0] && miny < b.max[1] && maxy > b.min[1] && minz < b.max[2] && maxz > b.min[2];
}

export function playerOverlap(p, boxes) {
  const hw = PH.halfW;
  for (const b of query(boxes, p[0] - hw, p[2] - hw, p[0] + hw, p[2] + hw, [])) if (!soft(b, p[1] + 0.3) && overlap(p[0] - hw, p[1], p[2] - hw, p[0] + hw, p[1] + PH.height, p[2] + hw, b)) return b;
  return null;
}

// Moves pos by vel*dt with collisions. Mutates pos & vel. Substeps so infinite speed doesn't tunnel.
export function movePlayer(pos, vel, dt, allBoxes, canStep) {
  const hw = PH.halfW, h = PH.height;
  const m = hw + 0.7;
  const boxes = query(allBoxes, Math.min(pos[0], pos[0] + vel[0] * dt) - m, Math.min(pos[2], pos[2] + vel[2] * dt) - m,
    Math.max(pos[0], pos[0] + vel[0] * dt) + m, Math.max(pos[2], pos[2] + vel[2] * dt) + m, qMove);
  const dist = Math.hypot(vel[0], vel[1], vel[2]) * dt;
  const steps = Math.min(200, Math.max(1, Math.ceil(dist / 0.25)));
  const sdt = dt / steps;
  const res = { ground: null, wall: false, ceil: false };
  const order = [1, 0, 2], T = allBoxes.terrain;
  for (let i = 0; i < steps; i++) {
    let onBox = false; // (this substep: standing on a real box, a plank, a crate: the ground under it doesn't pull you down through it)
    for (const ax of order) {
      const d = vel[ax] * sdt;
      if (d === 0) continue;
      pos[ax] += d;
      for (const b of boxes) {
        if (!overlap(pos[0] - hw, pos[1], pos[2] - hw, pos[0] + hw, pos[1] + h, pos[2] + hw, b)) continue;
        if (T && soft(b, pos[1] + 0.3)) continue; // the heightfield is the ground here, not its steps
        if (ax === 1) {
          if (d < 0) { pos[1] = b.max[1]; res.ground = b; onBox = true; } else { pos[1] = b.min[1] - h - 1e-4; res.ceil = true; }
          vel[1] = 0;
        } else {
          const rise = b.max[1] - pos[1];
          if ((canStep || res.ground) && rise > 0 && rise <= PH.step) {
            const old = pos[1];
            pos[1] = b.max[1] + 1e-3;
            if (!overlapAny(pos, boxes)) { res.ground = b; onBox = true; continue; }
            pos[1] = old;
          }
          pos[ax] = d > 0 ? b.min[ax] - hw - 1e-4 : b.max[ax] + hw + 1e-4;
          vel[ax] = 0;
          res.wall = true;
        }
      }
    }
    if (T) { // shaped ground: sunk into it (a landing, walking uphill) = stand on it. walking downhill: stay stuck to it
      const g = T.at(pos[0], pos[2]);
      if (g != null && vel[1] <= 0.01 && ((pos[1] < g && pos[1] > g - 0.9) || (!onBox && (canStep || res.ground === T.box) && pos[1] - g < 0.16 && pos[1] >= g))) { pos[1] = g; vel[1] = 0; res.ground = T.box; }
    }
  }
  return res;
}

function overlapAny(p, boxes) {
  const hw = PH.halfW;
  for (const b of boxes) if (!soft(b, p[1] + 0.3) && overlap(p[0] - hw, p[1], p[2] - hw, p[0] + hw, p[1] + PH.height, p[2] + hw, b)) return b;
  return null;
}

// Slab ray vs box. Returns {t, axis, sign} (sign = normal direction on that axis) or null.
export function rayBox(o, d, b, maxT) {
  let tmin = 0, tmax = maxT, axis = -1, sign = 0;
  for (let a = 0; a < 3; a++) {
    if (Math.abs(d[a]) < 1e-9) {
      if (o[a] < b.min[a] || o[a] > b.max[a]) return null;
      continue;
    }
    const inv = 1 / d[a];
    let t1 = (b.min[a] - o[a]) * inv, t2 = (b.max[a] - o[a]) * inv, s = -1;
    if (t1 > t2) { const tmp = t1; t1 = t2; t2 = tmp; s = 1; }
    if (t1 > tmin) { tmin = t1; axis = a; sign = s; }
    if (t2 < tmax) tmax = t2;
    if (tmin > tmax) return null;
  }
  return { t: tmin, axis, sign };
}

// Nearest hit against a list of boxes. Returns {t, point, normal, box} or null.
export function raycast(o, d, maxT, boxes) {
  let best = null;
  const s = ++stamp;
  const test = (cell) => {
    if (!cell) return;
    for (const b of cell) {
      if (b._r === s) continue;
      b._r = s;
      const h = rayBox(o, d, b, best ? best.t : maxT);
      if (h && (!best || h.t < best.t)) best = { t: h.t, axis: h.axis, sign: h.sign, box: b };
    }
  };
  // walk the grid cells the ray passes through (2D DDA on x/z), stop once we're past the best hit
  const T = boxes.terrain, cells = T ? rayGrid(boxes) : gridOf(boxes);
  let cx = Math.floor(o[0] / CELL), cz = Math.floor(o[2] / CELL);
  const sx = d[0] > 0 ? 1 : -1, sz = d[2] > 0 ? 1 : -1;
  const dtx = Math.abs(d[0]) > 1e-9 ? CELL / Math.abs(d[0]) : Infinity, dtz = Math.abs(d[2]) > 1e-9 ? CELL / Math.abs(d[2]) : Infinity;
  let tx = Math.abs(d[0]) > 1e-9 ? ((d[0] > 0 ? (cx + 1) * CELL - o[0] : o[0] - cx * CELL) / Math.abs(d[0])) : Infinity;
  let tz = Math.abs(d[2]) > 1e-9 ? ((d[2] > 0 ? (cz + 1) * CELL - o[2] : o[2] - cz * CELL) / Math.abs(d[2])) : Infinity;
  let t = 0;
  for (let i = 0; i < 2000; i++) {
    test(cells.get(cx * 100003 + cz));
    if (best && best.t <= t) break;
    if (t > maxT) break;
    if (tx < tz) { t = tx; tx += dtx; cx += sx; } else { t = tz; tz += dtz; cz += sz; }
    if (t > maxT && !best) break;
  }
  if (T) { // shaped ground: nearer than whatever box it hit?
    const h = terrainRay(T, o, d, best ? best.t : maxT);
    if (h) { const ax = h.side ? (Math.abs(d[0]) > Math.abs(d[2]) ? 0 : 2) : 1; best = { t: h.t, axis: ax, sign: ax === 1 ? 1 : d[ax] > 0 ? -1 : 1, box: T.box }; }
  }
  if (!best) return null;
  const normal = [0, 0, 0];
  if (best.axis >= 0) normal[best.axis] = best.sign;
  best.normal = normal;
  best.point = [o[0] + d[0] * best.t, o[1] + d[1] * best.t, o[2] + d[2] * best.t];
  return best;
}

// Projectile: {p, v, r, bounce}. Returns first hit {axis, sign, box} this step (or null).
export function stepProjectile(pr, dt, allBoxes, grav) {
  const p = pr.p, v = pr.v, r = pr.r;
  v[1] -= grav * dt;
  const m = r + 0.5;
  const boxes = query(allBoxes, Math.min(p[0], p[0] + v[0] * dt) - m, Math.min(p[2], p[2] + v[2] * dt) - m,
    Math.max(p[0], p[0] + v[0] * dt) + m, Math.max(p[2], p[2] + v[2] * dt) + m, qProj);
  const dist = Math.hypot(v[0], v[1], v[2]) * dt;
  const steps = Math.min(100, Math.max(1, Math.ceil(dist / Math.max(0.1, r))));
  const sdt = dt / steps;
  let hit = null;
  for (let i = 0; i < steps; i++) {
    for (let ax = 0; ax < 3; ax++) {
      const d = v[ax] * sdt;
      if (!d) continue;
      p[ax] += d;
      for (const b of boxes) {
        if (!overlap(p[0] - r, p[1] - r, p[2] - r, p[0] + r, p[1] + r, p[2] + r, b)) continue;
        p[ax] = d > 0 ? b.min[ax] - r - 1e-4 : b.max[ax] + r + 1e-4;
        if (!hit) hit = { axis: ax, sign: d > 0 ? -1 : 1, box: b };
        v[ax] = -v[ax] * (pr.bounce || 0);
        if (!pr.bounce) return hit;
      }
    }
  }
  return hit;
}

export function playerBoxes(pos) {
  const [x, y, z] = pos;
  return [
    { min: [x - 0.52, y, z - 0.52], max: [x + 0.52, y + 1.62, z + 0.52], head: false },
    { min: [x - 0.38, y + 1.62, z - 0.38], max: [x + 0.38, y + 2.3, z + 0.38], head: true },
  ];
}

// rubber duck black holes eat momentum: within R of c (a body centre) velocity bleeds off at up to k per second,
// harder toward the middle, except the part falling straight in. returns the distance to c, or -1 when outside
export function holeDrag(pos, vel, c, R, k, dt) {
  const dx = c[0] - pos[0], dy = c[1] - (pos[1] + 0.9), dz = c[2] - pos[2];
  const d = Math.hypot(dx, dy, dz);
  if (!(d < R)) return -1;
  const f = 1 - d / R, keep = Math.exp(-k * f * (2 - f) * dt);
  const u = d > 0.5 ? Math.max(0, vel[0] * dx + vel[1] * dy + vel[2] * dz) / (d * d) : 0;
  const ix = dx * u, iy = dy * u, iz = dz * u;
  vel[0] = ix + (vel[0] - ix) * keep; vel[1] = iy + (vel[1] - iy) * keep; vel[2] = iz + (vel[2] - iz) * keep;
  return d;
}
// turn v toward the direction `to` by at most maxA radians, keeping its speed (homing ducks)
export function steer(v, to, maxA) {
  const sp = Math.hypot(v[0], v[1], v[2]), tl = Math.hypot(to[0], to[1], to[2]);
  if (sp < 1e-6 || tl < 1e-6) return;
  const a0 = [v[0] / sp, v[1] / sp, v[2] / sp], b = [to[0] / tl, to[1] / tl, to[2] / tl];
  const ang = Math.acos(Math.max(-1, Math.min(1, a0[0] * b[0] + a0[1] * b[1] + a0[2] * b[2])));
  if (ang < 1e-4) return;
  const a = Math.min(ang, maxA), s = Math.sin(ang);
  if (s < 1e-4) return; // flying straight away: no defined way to turn
  const k0 = Math.sin(ang - a) / s, k1 = Math.sin(a) / s;
  for (let i = 0; i < 3; i++) v[i] = (a0[i] * k0 + b[i] * k1) * sp;
}
