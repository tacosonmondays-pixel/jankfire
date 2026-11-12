// Map edits (the map editor, public/editor.html): a list of ops replayed on top of a map's built layout.
// Pure data in and out, no three, so the server can run the same replay later (shared/mapedits/<map>.json).
// A "thing" is what you pick in the editor: one Blender prop (its model placement + the boxes it stands in for), one
// Blender building (arch placement + its tagged boxes) or one plain box. Ops name things by a signature of where they
// are right now (rounded), not by array index, so a map that gets remodelled under an edit file just reports the
// ops that no longer find their thing (stale) instead of moving the wrong box.
// ops:
//   { t: 'xf', sel: [sig], o: [x, y, z], k: 1, q: 0, d: [dx, dy, dz] }  scale k round o, turn q quarter turns (three yaw +90deg each), then move d
//   { t: 'del', sel: [sig] }
//   { t: 'add', items: [{ list: 'b'|'d', boxes: [box], prop?, arch? }] }  boxes are map boxes ({ min, max, mat, ... })

const R = (v) => Math.round(v * 1e4) / 1e4; // keep files tidy (and the same on every machine)
const r2 = (a) => a.map((v) => Math.round(v * 100) / 100).join(',');
const TURN = [[1, 0], [0, 1], [-1, 0], [0, -1]]; // cos, sin of q * 90deg

// every editable thing on a map. def = MAPS[id]. terrain steps (b.ter) aren't things: the heightfield owns them
export function indexMap(def) {
  const things = [], of = new Map();
  for (const [lk, list] of [['b', def.boxes], ['d', def.deco]]) {
    if (!list) continue;
    if (lk === 'b' && list.arch) list.arch.forEach((a, ai) => { const t = { kind: 'arch', list: lk, arch: a, boxes: [] }; things.push(t); a._t = t; });
    // each tagged box goes to the prop of its kind that holds it with the nearest anchor (pines in a clump overlap)
    const C = 6, cells = new Map(), key = (i, j) => i * 100003 + j;
    for (const p of list.props || []) {
      const t = { kind: 'prop', list: lk, prop: p, boxes: [] }, { lo, hi } = propBounds(p);
      things.push(t);
      for (let i = Math.floor(lo[0] / C); i <= Math.floor(hi[0] / C); i++) for (let j = Math.floor(lo[2] / C); j <= Math.floor(hi[2] / C); j++) {
        const k = key(i, j); if (!cells.has(k)) cells.set(k, []); cells.get(k).push(t);
      }
    }
    for (const b of list) {
      if (!b.pv || b.ter) continue;
      const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2;
      let best = null, bd = 1e18;
      for (const t of cells.get(key(Math.floor(cx / C), Math.floor(cz / C))) || []) {
        const p = t.prop; if (p.id !== b.pv || !insideProp(b, p)) continue;
        const a = p.a || p.p, d = (a[0] - cx) ** 2 + (a[2] - cz) ** 2;
        if (d < bd) { bd = d; best = t; }
      }
      if (best) { best.boxes.push(b); of.set(b, best); }
    }
    for (const b of list) {
      if (b.ter || of.has(b)) continue;
      if (lk === 'b' && b.ai !== undefined && list.arch && list.arch[b.ai]) { const t = list.arch[b.ai]._t; t.boxes.push(b); of.set(b, t); continue; }
      const t = { kind: 'box', list: lk, boxes: [b] }; things.push(t); of.set(b, t);
    }
    if (lk === 'b' && list.arch) for (const a of list.arch) delete a._t;
  }
  return { things, of };
}
// a prop's world-space footprint (round 1 records: a generous circle)
function propBounds(p) {
  if (!p.a) { const r = 8 * (p.s || 1); return { lo: [p.p[0] - r, 0, p.p[2] - r], hi: [p.p[0] + r, 0, p.p[2] + r] }; }
  const fr = p.f !== undefined ? p.f : p.y, c = Math.cos(fr), s = Math.sin(fr), lo = [1e9, 0, 1e9], hi = [-1e9, 0, -1e9];
  for (const x of [p.lo[0], p.hi[0]]) for (const z of [p.lo[2], p.hi[2]]) {
    const wx = p.a[0] + x * c + z * s, wz = p.a[2] - x * s + z * c;
    lo[0] = Math.min(lo[0], wx); hi[0] = Math.max(hi[0], wx); lo[2] = Math.min(lo[2], wz); hi[2] = Math.max(hi[2], wz);
  }
  lo[0] -= 0.1; lo[2] -= 0.1; hi[0] += 0.1; hi[2] += 0.1;
  return { lo, hi };
}
// is box b one of prop p's? (its centre inside the prop's fitted extent, in the prop's own frame)
function insideProp(b, p) {
  const cx = (b.min[0] + b.max[0]) / 2, cy = (b.min[1] + b.max[1]) / 2, cz = (b.min[2] + b.max[2]) / 2;
  if (!p.a) { const q = p.p; return Math.hypot(cx - q[0], cz - q[2]) < 8 * (p.s || 1) && cy > q[1] - 1 && cy < q[1] + 12 * (p.s || 1); } // (round 1 records: near enough)
  const fr = p.f !== undefined ? p.f : p.y, c = Math.cos(fr), s = Math.sin(fr), px = cx - p.a[0], pz = cz - p.a[2];
  const lx = px * c - pz * s, lz = px * s + pz * c, ly = cy - p.a[1], e = 0.06;
  return lx > p.lo[0] - e && lx < p.hi[0] + e && ly > p.lo[1] - e && ly < p.hi[1] + e && lz > p.lo[2] - e && lz < p.hi[2] + e;
}

export function sigOf(t) {
  if (t.kind === 'prop') return 'p|' + t.list + '|' + t.prop.id + '|' + r2(t.prop.a || t.prop.p);
  if (t.kind === 'arch') return 'a|' + t.arch.id + '|' + r2(t.arch.p);
  const b = t.boxes[0];
  if (!b) return 'b|' + t.list + '|?';
  return 'b|' + t.list + '|' + b.mat + '|' + r2(b.min) + '|' + r2(b.max);
}
// sig -> thing (a second thing with the same sig, a box doubled up in one spot, is 'sig#2'). m.sig: thing -> sig
export function bySig(idx) {
  const m = new Map(), back = new Map();
  for (const t of idx.things) { let s = sigOf(t); if (m.has(s)) { let n = 2; while (m.has(s + '#' + n)) n++; s += '#' + n; } m.set(s, t); back.set(t, s); }
  m.sig = back;
  return m;
}

// world-space bounds of a thing (its boxes, or the prop's fitted extent when it has none: deco-only models)
export function boundsOf(t) {
  const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  const grow = (x, y, z) => { if (x < lo[0]) lo[0] = x; if (y < lo[1]) lo[1] = y; if (z < lo[2]) lo[2] = z; if (x > hi[0]) hi[0] = x; if (y > hi[1]) hi[1] = y; if (z > hi[2]) hi[2] = z; };
  for (const b of t.boxes) { grow(...b.min); grow(...b.max); }
  if (!t.boxes.length && t.prop && t.prop.a) {
    const p = t.prop, c = Math.cos(p.y), s = Math.sin(p.y);
    for (const x of [p.lo[0], p.hi[0]]) for (const z of [p.lo[2], p.hi[2]]) for (const y of [p.lo[1], p.hi[1]]) grow(p.a[0] + x * c + z * s, p.a[1] + y, p.a[2] - x * s + z * c);
  }
  if (lo[0] > hi[0]) { const a = (t.prop && (t.prop.a || t.prop.p)) || (t.arch && t.arch.p) || [0, 0, 0]; grow(...a); }
  return { lo, hi };
}
// where a thing turns round: a prop's anchor, else the bottom middle of its boxes
export function pivotOf(t) {
  if (t.prop) return [...(t.prop.a || t.prop.p)];
  const { lo, hi } = boundsOf(t); // (a building too: many sit at p = the map's centre, far from their walls)
  return [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2];
}
export const canScale = (t) => t.kind !== 'arch';

// ---- the transform
function xfPoint(v, o, k, q, d) {
  const [c, s] = TURN[q & 3], x = (v[0] - o[0]) * k, y = (v[1] - o[1]) * k, z = (v[2] - o[2]) * k;
  return [R(x * c + z * s + o[0] + d[0]), R(y + o[1] + d[1]), R(-x * s + z * c + o[2] + d[2])];
}
export function xfThing(t, o, k, q, d) {
  q &= 3; const th = q * Math.PI / 2;
  if (t.kind === 'arch') k = 1;
  for (const b of t.boxes) {
    if (b.rot) { // a turned deco box: its centre moves, its size scales, its turn adds up
      const c = [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2], h = [0, 1, 2].map((i) => (b.max[i] - b.min[i]) / 2 * k), n = xfPoint(c, o, k, q, d);
      b.min = [R(n[0] - h[0]), R(n[1] - h[1]), R(n[2] - h[2])]; b.max = [R(n[0] + h[0]), R(n[1] + h[1]), R(n[2] + h[2])]; b.rot += th;
    } else {
      const a = xfPoint(b.min, o, k, q, d), z = xfPoint(b.max, o, k, q, d);
      b.min = [Math.min(a[0], z[0]), Math.min(a[1], z[1]), Math.min(a[2], z[2])]; b.max = [Math.max(a[0], z[0]), Math.max(a[1], z[1]), Math.max(a[2], z[2])];
    }
    if (b.pad && q) { const [c, s] = TURN[q], [x, y, z] = b.pad; b.pad = [x * c + z * s, y, -x * s + z * c]; } // (a jump pad's push turns with it)
  }
  const p = t.prop;
  if (p && p.a) {
    p.a = xfPoint(p.a, o, k, q, d); p.y = (p.y || 0) + th; if (p.f !== undefined) p.f += th;
    if (k !== 1) { p.lo = p.lo.map((v) => R(v * k)); p.hi = p.hi.map((v) => R(v * k)); }
  } else if (p) { p.p = xfPoint(p.p, o, k, q, d); p.r = ((p.r || 0) - q) & 3; if (k !== 1) p.s = R((p.s || 1) * k); }
  if (t.arch) { t.arch.p = xfPoint(t.arch.p, o, 1, q, d); t.arch.r = ((t.arch.r || 0) - q) & 3; }
}
// the transform that undoes xf(o, k, q, d): move back, turn back round the moved pivot, scale back
export function xfUndo(o, k, q, d) { const o2 = [o[0] + d[0], o[1] + d[1], o[2] + d[2]]; return [o2, 1 / k, (4 - (q & 3)) & 3, [o[0] - o2[0], o[1] - o2[1], o[2] - o2[2]]]; }

// ---- take things out of / put things into the map
const listOf = (def, lk) => (lk === 'd' ? (def.deco || (def.deco = Object.assign([], { props: [] }))) : def.boxes);
export function removeThing(def, idx, t) {
  const list = listOf(def, t.list), gone = new Set(t.boxes);
  for (let i = list.length - 1; i >= 0; i--) if (gone.has(list[i])) list.splice(i, 1);
  if (t.prop) { const pl = list.props || [], i = pl.indexOf(t.prop); if (i >= 0) pl.splice(i, 1); }
  if (t.arch) {
    const al = list.arch, ai = al.indexOf(t.arch);
    if (ai >= 0) { al.splice(ai, 1); for (const b of list) if (b.ai !== undefined && b.ai > ai) b.ai--; } // (the boxes after it point one placement earlier now)
  }
  for (const b of t.boxes) idx.of.delete(b);
  const i = idx.things.indexOf(t); if (i >= 0) idx.things.splice(i, 1);
}
export function insertThing(def, idx, t) {
  const list = listOf(def, t.list);
  if (t.arch) { if (!list.arch) list.arch = []; list.arch.push(t.arch); const ai = list.arch.length - 1; for (const b of t.boxes) b.ai = ai; }
  if (t.prop) { if (!list.props) list.props = []; list.props.push(t.prop); }
  for (const b of t.boxes) { list.push(b); idx.of.set(b, t); }
  idx.things.push(t);
}
// a thing as plain data (an 'add' op item), and back
const clean = (o) => JSON.parse(JSON.stringify(o, (k, v) => (k.startsWith('_') ? undefined : v)));
export function thingData(t) { const o = { list: t.list, boxes: t.boxes.map(clean) }; if (t.prop) o.prop = clean(t.prop); if (t.arch) o.arch = clean(t.arch); return o; }
export function thingFrom(o) {
  const boxes = (o.boxes || []).map((b) => ({ ...b, min: [...b.min], max: [...b.max] }));
  const t = { kind: o.arch ? 'arch' : o.prop ? 'prop' : 'box', list: o.list === 'd' ? 'd' : 'b', boxes };
  if (o.prop) t.prop = clean(o.prop); if (o.arch) t.arch = clean(o.arch);
  return t;
}

// ---- run one op. returns { ok, missing: [sig], made: [thing], hit: [thing] }
export function applyOp(def, idx, op, look = bySig(idx)) {
  const missing = [], hit = [];
  for (const s of op.sel || []) { const t = look.get(s); if (t) hit.push(t); else missing.push(s); }
  if (op.t === 'xf') for (const t of hit) xfThing(t, op.o, op.k || 1, op.q || 0, op.d || [0, 0, 0]);
  else if (op.t === 'del') for (const t of hit) removeThing(def, idx, t);
  const made = [];
  if (op.t === 'add') for (const it of op.items || []) { const t = thingFrom(it); insertThing(def, idx, t); made.push(t); }
  return { ok: !missing.length, missing, made, hit };
}
// replay a whole edit file on a freshly built map: { ops } -> what didn't apply (stale ops after a remodel)
export function applyEdits(def, edits) {
  const idx = indexMap(def), stale = [];
  for (const op of (edits && edits.ops) || []) { const r = applyOp(def, idx, op); if (!r.ok) stale.push({ op, missing: r.missing }); }
  return { idx, stale };
}

// ---- checking an edit file that came from outside (import, and later the server): shapes, numbers, sizes
const num = (v) => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) < 1e5;
const vec = (v) => Array.isArray(v) && v.length === 3 && v.every(num);
const str = (v, n = 200) => typeof v === 'string' && v.length <= n;
const opt = (v, f) => v === undefined || f(v);
function okBox(b) { return b && typeof b === 'object' && vec(b.min) && vec(b.max) && str(b.mat, 40) && opt(b.rot, num) && opt(b.pad, vec) && opt(b.pv, str) && opt(b.av, str) && opt(b.ai, Number.isInteger); }
function okItem(it) {
  if (!it || typeof it !== 'object' || !Array.isArray(it.boxes) || it.boxes.length > 400 || !it.boxes.every(okBox)) return false;
  if (!it.boxes.length && !it.prop && !it.arch) return false; // (nothing to be)
  const p = it.prop, a = it.arch;
  if (p && !(typeof p === 'object' && str(p.id, 60) && (p.a !== undefined ? vec(p.a) && vec(p.lo) && vec(p.hi) && opt(p.y, num) && opt(p.f, num) : vec(p.p) && opt(p.r, Number.isInteger) && opt(p.s, num)))) return false;
  if (a && !(typeof a === 'object' && str(a.id, 60) && vec(a.p) && opt(a.r, Number.isInteger) && it.boxes.length)) return false;
  return true;
}
export function validEdits(e) {
  if (!e || typeof e !== 'object' || !str(e.map, 40) || !Array.isArray(e.ops) || e.ops.length > 5000) return false;
  for (const op of e.ops) {
    if (!op || typeof op !== 'object') return false;
    if (op.sel !== undefined && !(Array.isArray(op.sel) && op.sel.length <= 2000 && op.sel.every((s) => str(s)))) return false;
    if (op.t === 'xf') { if (!vec(op.o) || !vec(op.d) || !num(op.k) || op.k <= 0.01 || op.k > 100 || !Number.isInteger(op.q)) return false; }
    else if (op.t === 'del') { if (!op.sel) return false; }
    else if (op.t === 'add') { if (!Array.isArray(op.items) || op.items.length > 500 || !op.items.every(okItem)) return false; }
    else return false;
  }
  return true;
}
