// can you swing it? node tools/city/grapple.mjs [route ...] | --from x,y,z --to x,y,z [--r 4] [--walk] [--hooks 10]
// A search over landing spots with the real physics: from where you stand, hook any anchor in range you can see (the
// kit's 'grapple' marks, plus roof edges), fly the classic rope (shared/hookphys.js, the one players use), let go at a
// few moments (on arrival, or early with a grapple jump), and see where you land. Each landing is a new place to hook
// from. Prints the hooks of the first route found. Named routes (below) are the slice's designed swing lines; with
// --walk a route must ALSO be impossible on foot (the grapple-only alcoves). Exit code 1 if any route fails.
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { CHUNK } from '../../shared/city/plan.js';
import { classicRopeStep, classicRopeJump } from '../../shared/hookphys.js';
import { HOOK } from '../../shared/weapons.js';
import '../../shared/city/gens.js';

const G = 26, EYE = 1.6, DT = 1 / 60;
// the slice's swing lines (DESIGN: the districts are grapple playgrounds). from -> to (r = how close counts)
export const ROUTES = {
  longstairs: { from: [-44, 4.3, 226], to: [-44, 36.3, -20], r: 8, note: 'the Bottom: up the Long Stairs by the gantries' },
  market: { from: [-140, 0.3, 246], to: [-44, 12.3, 170], r: 12, note: 'the Bottom: market masts up onto the terraces' },
  ribave: { from: [-44, 40.3, -64], to: [-44, 40.3, -240], r: 10, note: 'the Gut: down Rib Avenue arch to arch' },
  ribrun: { from: [-44, 40.3, -112], to: [-160, 40.3, -128], r: 12, note: 'the Gut: THE RIB RUN over Peristalsis Avenue to the stomach rim' },
  gate_roofs: { from: [-44, 36.3, -4], to: [-73, 44.7, -13], r: 2.6, note: 'Overtime 1: from the stairs top up onto the highest roof' },
  gantries: { from: [182, 9.2, 196], to: [182, 31.6, -70], r: 14, note: 'the Commute: THE GANTRIES, sign to sign up the Ring Road' },
  pileup: { from: [212, 27, -20], to: [222, 34.5, -20], r: 3, note: 'the Commute: onto the Pile-Up' },
  crows_nest: { from: [-160, 8.3, 200], to: [-154, 29.8, 182], r: 2.2, walk: true, note: 'secret: the Crow\'s Nest (Lost & Found crane)' },
  wishbone: { from: [-44, 40.3, -196], to: [-44, 59, -213], r: 2.2, walk: true, note: 'secret: the Wishbone (Rib Avenue)' },
  smiles_hat: { from: [200, 33.5, -84], to: [208.8, 45.7, -90], r: 2.4, walk: true, note: 'secret: the Smile\'s Hat (a billboard)' },
};

function world(lo, hi) {
  const W = new ChunkWorld([]), marks = [];
  for (let cx = Math.floor(lo[0] / CHUNK); cx <= Math.floor(hi[0] / CHUNK); cx++) for (let cz = Math.floor(lo[1] / CHUNK); cz <= Math.floor(hi[1] / CHUNK); cz++) {
    const p = packChunk(buildChunk('slice', cx, cz));
    W.set(cx + ':' + cz, chunkBoxes(p));
    for (const m of p.marks || []) if (m.id === 'grapple') marks.push(m.p);
  }
  W.sync();
  // roof edges count too (you can hook any box): the top centre of every big flat-topped box well above the street
  const roofs = [];
  for (const b of W.boxes) { const w = b.max[0] - b.min[0], d = b.max[2] - b.min[2]; if (w > 3 && d > 3 && w * d < 900 && b.max[1] > 4) roofs.push([(b.min[0] + b.max[0]) / 2, b.max[1] - 0.2, (b.min[2] + b.max[2]) / 2]); }
  return { W, anchors: [...marks.map((p) => ({ p, ring: true })), ...roofs.map((p) => ({ p, ring: false }))] };
}

// one flight: hook a, hold for `hold` s (Infinity = until you arrive), let go (jump = a grapple jump), fly until you land
function fly(W, p0, a, hold, jump, goal) {
  const p = p0.slice(), v = [0, 0, 0], h = { len: null };
  let t = 0, on = true, ground = true, path = [];
  for (let k = 0; k < 60 * 9; k++) {
    v[1] -= G * DT;
    if (on) {
      classicRopeStep(h, a, p, v, DT, G);
      if (t >= hold || h.dist < 2.4) { on = false; if (jump) classicRopeJump(v); else if (ground) return null; }
    } else { // air control toward the goal (players steer)
      const gx = goal[0] - p[0], gz = goal[2] - p[2], gl = Math.hypot(gx, gz) || 1, along = (v[0] * gx + v[2] * gz) / gl;
      if (along < 9) { v[0] += (gx / gl) * 10 * DT; v[2] += (gz / gl) * 10 * DT; }
    }
    const r = W.movePlayer(p, v, DT, ground);
    ground = !!r.ground; t += DT;
    if (k % 2 === 0) path.push([...p.map((x) => +x.toFixed(2)), on ? 1 : 0, ...(on ? a.map((x) => +x.toFixed(2)) : [0, 0, 0])]); // 30 Hz, for --path
    if (p[1] < -30) return null;
    if (!on && ground && t > 0.1) return { p, t, path };
  }
  return null;
}

export function search(from, to, o = {}) {
  const R = o.r || 4, maxHooks = o.hooks || 10, K = o.k || 14;
  const lo = [Math.min(from[0], to[0]) - 110, Math.min(from[2], to[2]) - 110], hi = [Math.max(from[0], to[0]) + 110, Math.max(from[2], to[2]) + 110];
  const { W, anchors } = world(lo, hi);
  // settle the start on the ground
  const s = from.slice(), sv = [0, 0, 0];
  for (let k = 0; k < 120; k++) { sv[1] -= G * DT; if (W.movePlayer(s, sv, DT, true).ground && k > 4) break; }
  const key = (p) => Math.round(p[0] / 2) + ':' + Math.round(p[1] / 1.5) + ':' + Math.round(p[2] / 2);
  const seen = new Set([key(s)]), close = (p) => Math.hypot(p[0] - to[0], p[2] - to[2]) < R && Math.abs(p[1] - to[1]) < 3;
  let front = [{ p: s, hops: [] }], sims = 0;
  for (let depth = 0; depth < maxHooks && front.length; depth++) {
    const next = [];
    for (const n of front) {
      const eye = [n.p[0], n.p[1] + EYE, n.p[2]], dNow = Math.hypot(n.p[0] - to[0], n.p[2] - to[2]);
      // anchors in range that you can see, best (closest to the goal, and up when the goal is up) first
      const cand = [];
      for (const an of anchors) {
        const d = [an.p[0] - eye[0], an.p[1] - eye[1], an.p[2] - eye[2]], L = Math.hypot(...d);
        if (L > HOOK.range || L < 3) continue;
        const hit = W.raycast(eye, d.map((x) => x / L), L + 1);
        if (!hit || hit.t < L - (an.ring ? 1.2 : 2)) continue; // something's in the way
        const g = Math.hypot(an.p[0] - to[0], an.p[2] - to[2]) - Math.max(0, an.p[1] - n.p[1]) * 0.3 * Math.sign(to[1] - n.p[1] + 0.01);
        if (g > dNow + 25) continue;
        cand.push([g, hit.point, an]);
      }
      cand.sort((a, b) => a[0] - b[0]);
      for (const [, pt] of cand.slice(0, K)) for (const [hold, jump] of [[Infinity, true], [Infinity, false], [0.5, true], [0.9, true], [1.4, true]]) {
        sims++;
        const f = fly(W, n.p, pt, hold, jump, to);
        if (!f) continue;
        const hop = { at: pt.map((x) => +x.toFixed(1)), land: f.p.map((x) => +x.toFixed(1)), hold, jump, path: f.path };
        if (close(f.p)) return { ok: true, hops: [...n.hops, hop], sims, anchors: anchors.length, rings: anchors.filter((a) => a.ring).length };
        const k = key(f.p);
        if (seen.has(k)) continue;
        seen.add(k); next.push({ p: f.p, hops: [...n.hops, hop] });
      }
    }
    // keep the most promising landings (closest to the goal, height counting extra)
    const score = (p) => Math.hypot(p[0] - to[0], p[2] - to[2]) + Math.abs(p[1] - to[1]) * 1.5;
    next.sort((a, b) => score(a.p) - score(b.p));
    front = next.slice(0, o.beam || 40);
  }
  return { ok: false, sims, anchors: anchors.length, rings: anchors.filter((a) => a.ring).length, best: front[0] && front[0].p };
}

// on foot only (no grapple): flood the walkable spots with the real physics (walk 8 dirs, jumps), for --walk
export function walkable(from, to, o = {}) {
  const R = o.r || 4, lo = [Math.min(from[0], to[0]) - 80, Math.min(from[2], to[2]) - 80], hi = [Math.max(from[0], to[0]) + 80, Math.max(from[2], to[2]) + 80];
  const { W } = world(lo, hi);
  const key = (p) => Math.round(p[0] / 1.5) + ':' + Math.round(p[1]) + ':' + Math.round(p[2] / 1.5);
  const s = from.slice(), seen = new Set([key(s)]);
  let front = [s];
  for (let it = 0; it < 4000 && front.length; it++) {
    const n = front.shift();
    if (Math.hypot(n[0] - to[0], n[2] - to[2]) < R && Math.abs(n[1] - to[1]) < 2.5) return true;
    for (let a = 0; a < 8; a++) for (const jump of [false, true]) {
      const p = n.slice(), v = [Math.cos(a * Math.PI / 4) * 7.5, jump ? 9.2 : 0, Math.sin(a * Math.PI / 4) * 7.5];
      let g = !jump;
      for (let k = 0; k < 40; k++) { v[1] -= G * DT; const r = W.movePlayer(p, v, DT, g); g = !!r.ground; if (k > 12 && g) break; }
      if (!g || p[1] < -30 || p[0] < lo[0] || p[0] > hi[0] || p[2] < lo[1] || p[2] > hi[1]) continue;
      const k = key(p); if (seen.has(k)) continue; seen.add(k); front.push(p);
    }
  }
  return false;
}

if (import.meta.url === 'file://' + process.argv[1]) {
  const a = process.argv.slice(2), arg = (k) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : null; };
  const jobs = [];
  if (arg('--from')) jobs.push(['custom', { from: arg('--from').split(',').map(Number), to: arg('--to').split(',').map(Number), r: +(arg('--r') || 4), walk: a.includes('--walk') }]);
  else { const names = a.filter((x, i) => !x.startsWith('-') && !(i > 0 && /^--(path|hooks|r)$/.test(a[i - 1]))); for (const n of names.length ? names : Object.keys(ROUTES)) jobs.push([n, ROUTES[n]]); }
  let bad = 0;
  for (const [name, r] of jobs) {
    const t0 = Date.now(), res = search(r.from, r.to, { r: r.r, hooks: +(arg('--hooks') || 10) });
    let foot = null;
    if (r.walk) foot = walkable(r.from, r.to, { r: r.r });
    const ok = res.ok && (!r.walk || !foot);
    if (!ok) bad++;
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${name}: ${res.ok ? res.hops.length + ' hooks' : 'no swing found (best ' + (res.best || []).map((x) => x.toFixed(0)) + ')'}${r.walk ? (foot ? ', but WALKABLE too' : ', grapple-only') : ''} · ${res.rings} rings + ${res.anchors - res.rings} roof edges · ${res.sims} flights · ${Date.now() - t0} ms${r.note ? ' · ' + r.note : ''}`);
    if (res.ok && a.includes('-v')) for (const h of res.hops) console.log('   hook', h.at.join(','), 'hold', h.hold, h.jump ? 'jump' : '', '-> land', h.land.join(','));
    if (res.ok && arg('--path')) { const fs = await import('node:fs'); fs.writeFileSync(arg('--path'), JSON.stringify({ route: name, from: r.from, pts: res.hops.flatMap((h) => h.path) })); }
  }
  process.exit(bad ? 1 : 0);
}
