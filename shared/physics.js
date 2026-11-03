// Box physics. Players are AABBs, projectiles are tiny AABBs, the world is AABBs.
// Position = feet (bottom center) for players.

export const PH = { halfW: 0.4, height: 1.8, eye: 1.6, step: 0.6 };

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
export function resetGrid(boxes) { boxes._grid = null; boxes._gridN = -1; }
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
  for (const b of query(boxes, p[0] - hw, p[2] - hw, p[0] + hw, p[2] + hw, [])) if (overlap(p[0] - hw, p[1], p[2] - hw, p[0] + hw, p[1] + PH.height, p[2] + hw, b)) return b;
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
  const order = [1, 0, 2];
  for (let i = 0; i < steps; i++) {
    for (const ax of order) {
      const d = vel[ax] * sdt;
      if (d === 0) continue;
      pos[ax] += d;
      for (const b of boxes) {
        if (!overlap(pos[0] - hw, pos[1], pos[2] - hw, pos[0] + hw, pos[1] + h, pos[2] + hw, b)) continue;
        if (ax === 1) {
          if (d < 0) { pos[1] = b.max[1]; res.ground = b; } else { pos[1] = b.min[1] - h - 1e-4; res.ceil = true; }
          vel[1] = 0;
        } else {
          const rise = b.max[1] - pos[1];
          if ((canStep || res.ground) && rise > 0 && rise <= PH.step) {
            const old = pos[1];
            pos[1] = b.max[1] + 1e-3;
            if (!overlapAny(pos, boxes)) { res.ground = b; continue; }
            pos[1] = old;
          }
          pos[ax] = d > 0 ? b.min[ax] - hw - 1e-4 : b.max[ax] + hw + 1e-4;
          vel[ax] = 0;
          res.wall = true;
        }
      }
    }
  }
  return res;
}

function overlapAny(p, boxes) {
  const hw = PH.halfW;
  for (const b of boxes) if (overlap(p[0] - hw, p[1], p[2] - hw, p[0] + hw, p[1] + PH.height, p[2] + hw, b)) return b;
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
  const cells = gridOf(boxes);
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
