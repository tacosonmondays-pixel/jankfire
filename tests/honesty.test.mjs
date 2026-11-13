// node tests/honesty.test.mjs : the honesty checks (server/honesty.js) in-process, on Crate (a 5 m block in the middle):
// targets in a soap bubble, fast targets crossing a gap, shots right after a launch, revolver bounces that don't add
// up, and the CPU a flood of impossible hits can cost (vs an honest sprayer at full rate, who never comes near it)
import assert from 'node:assert/strict';
import { Room } from '../server/room.js';
import { HON } from '../server/honesty.js';
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const room = new Room('honesty_test', 'ffa');
const human = (name) => room.addHuman({ readyState: 1, send: () => {}, bufferedAmount: 0 }, { t: 'join', name, mode: 'ffa' });
room.cfg.map = 'crate';
const A = human('A'), B = human('B');
const T = Date.now;
// someone standing (or moving) along a 30 Hz trail that ends now
const put = (p, pos, trail) => { p.pos = pos.slice(); p.vel = [0, 0, 0]; p.alive = true; p.trap = null; p.strail = trail || [[T() - 900, ...pos], [T() - 10, ...pos]]; p.trail = p.strail.map((x) => x.slice()); };
const fresh = (w = 'ar') => { A.w = w; A.hon = null; A.pair = new Map(); };
const hit = (w = 'ar', d = [0, 0, 1], o = {}) => { fresh(w); return room.honHit(A, { t: 'hit', to: B.id, w, d, n: 1, h: 0, ...o }); };
const unit = (v) => { const l = Math.hypot(...v); return v.map((x) => Math.round((x / l) * 100) / 100); };

await t('a target in a soap bubble is shot on the bubble: its edge past the block is enough', () => {
  put(A, [0, 0, -8]); put(B, [4.6, 0, 4]);
  assert.equal(hit(), false, 'without the bubble only the block shows');
  B.trap = { until: T() + 5000 };
  assert.equal(hit(), true, 'the bubble (±1.1 m) sticks out past the corner');
  B.trap = null;
});

await t('a fast target crossing a 1.5 m gap in a wall lands at 10-40 m/s (every timing)', () => {
  const base = room.map.boxes.filter((b) => b.min[1] < 0); // (just the floor)
  const boxes = [...base, { min: [-20, 0, -0.2], max: [-0.75, 4, 0.2] }, { min: [0.75, 0, -0.2], max: [20, 4, 0.2] }];
  Object.defineProperty(room, 'boxes', { get: () => boxes, configurable: true });
  try {
    for (const v of [10, 20, 30, 40]) {
      let lands = 0;
      for (let ph = 0; ph < 30; ph++) {
        const n0 = T(), tr = [], t0 = n0 - 400 + ph * 1.1;
        for (let k = t0; k <= n0; k += 33) tr.push([k, -v * 0.2 + ((k - t0) / 1000) * v, 0, 10]);
        put(B, [tr.at(-1)[1], 0, 10], tr); B.vel = [v, 0, 0];
        put(A, [0, 0, -10], [[n0 - 500, 0, 0, -10]]);
        if (hit('ar', [0, 0, 1])) lands++;
      }
      assert.equal(lands, 30, `${v} m/s: ${lands}/30`);
    }
  } finally { delete room.boxes; }
});

await t('a shot right after a launch (rocket jump: 25 m/s up, 100 ms ago) is judged from where the jump took you', () => {
  const base = room.map.boxes.filter((b) => b.min[1] < 0);
  const boxes = [...base, { min: [-20, 0, -0.2], max: [20, 4, 0.2] }]; // a 4 m wall: only seen over from up high
  Object.defineProperty(room, 'boxes', { get: () => boxes, configurable: true });
  try {
    const n0 = T();
    put(B, [0, 0, 6], [[n0 - 700, 0, 0, 6], [n0 - 5, 0, 0, 6]]);
    const tr = [[n0 - 600, 0, 0, -1], [n0 - 300, 0, 0, -1], [n0 - 100, 0, 0, -1], [n0 - 50, 0, 1.2, -1], [n0, 0, 2.3, -1]];
    put(A, [0, 2.3, -1], tr); A.vel = [0, 25, 0];
    assert.equal(hit('ar', [0, -0.3, 0.95], { h: 1 }), true);
    put(A, [0, 2.3, -1], [[n0 - 600, 0, 2.3, -1], [n0, 0, 2.3, -1]]); A.vel = [0, 25, 0]; // (claiming 25 m/s while standing still: no lead)
    assert.equal(hit('ar', [0, -0.3, 0.95], { h: 1 }), false);
  } finally { delete room.boxes; }
});

await t('revolver ricochets: a real bounce around the block lands, a bounce that does not add up is refused', () => {
  // B behind the block; A bounces it off the low wall's face at z 9.5 (mirror B in the wall: the line from A's eye to it)
  put(A, [-6, 0, -6]); put(B, [0, 0, 6]);
  const e = [-6, 1.6, -6], Bc = [0, 1.1, 6], Bm = [0, 1.1, 13], k = (9.5 - e[2]) / (Bm[2] - e[2]);
  const W = [e[0] + (Bm[0] - e[0]) * k, e[1] + (Bm[1] - e[1]) * k, 9.5];
  assert.equal(hit('ar', [0, 0, 1]), false, 'no straight line');
  assert.equal(hit('revolver', unit([Bc[0] - W[0], Bc[1] - W[1], Bc[2] - W[2]])), true, 'the real bounce');
  // the reviewer's cheat: the last leg "comes up off the floor" at a spot A can see, but nothing A fires bounces that way
  put(A, [0, 0, -8]); put(B, [0, 0, 6]);
  assert.equal(hit('revolver', unit([0 - 6.5, 1.1 - 0, 6 - 4])), false, 'a floor bounce from a visible spot that no shot from A makes');
});

await t('a flood of impossible hits costs at most the per-player budget; an honest full-rate sprayer never comes near it', () => {
  // the flood: 9 targets running behind the block (a fresh rate slot each), 400 hits in one go
  put(A, [0, 0, -8]);
  const others = [];
  for (let i = 0; i < 9; i++) { const o = human('F' + i), n0 = T(), tr = []; for (let k = 650; k >= 0; k -= 33) tr.push([n0 - k, -1.2 + i * 0.3, 0, 9.5 - k / 108]); put(o, [-1.2 + i * 0.3, 0, 9.5], tr); o.vel = [0, 0, 9]; others.push(o); } // (in the block's shadow all the way: 9 m/s away from A)
  fresh('ar');
  const t0 = performance.now();
  for (const o of others) o.spawnT = 0; // (no spawn protection: a hit that got through would show)
  for (let i = 0; i < 400; i++) room.handle(A, { t: 'hit', to: others[i % 9].id, w: 'ar', d: [0, 0, 1], n: 1, h: 0 });
  const ms = performance.now() - t0, H = A.hon;
  assert.ok(others.every((o) => o.hp === 100), 'nothing landed');
  assert.ok(H.rays <= HON.rays + HON.perHit && H.ms <= HON.ms + HON.hitMs + 2, `budget: ${H.rays} rays, ${H.ms.toFixed(1)} ms`);
  console.log(`   flood: 400 impossible hits on 9 moving targets cost ${ms.toFixed(1)} ms, ${H.rays} rays`);
  for (const o of others) room.remove ? room.remove(o) : room.players.delete(o.id);
  // honest sprayers: minigun 25/s, akimbo 2 x 9/s, marbles (1 hit per shot): 2 s at a target strafing 7 m/s in the open
  for (const [w, rate, extra] of [['minigun', 25, {}], ['akimbo', 18, {}], ['marbles', 1.2, { n: 20 }]]) {
    fresh(w); let ok = 0, sent = 0, maxRays = 0, maxMs = 0;
    for (let s = 0; s < 2 * rate; s++) {
      const n0 = T(), x = -10 + (s / rate) * 7, tr = [];
      for (let k = 650; k >= 0; k -= 33) tr.push([n0 - k, x - k * 0.007, 0, 7]);
      put(B, [x, 0, 7], tr); B.vel = [7, 0, 0]; put(A, [-10, 0, 0]);
      A.pair = new Map(); // (onHit's own rate clock isn't what's tested here)
      sent++; if (room.honHit(A, { t: 'hit', to: B.id, w, d: unit([x + 10, 1.1 - 1.6, 7]), n: 1, h: 0, ...extra })) ok++;
      maxRays = Math.max(maxRays, A.hon.rays); maxMs = Math.max(maxMs, A.hon.ms);
    }
    assert.equal(ok, sent, `${w}: ${ok}/${sent}`);
    assert.ok(maxRays < HON.rays / 10, `${w}: ${maxRays} rays in a second`);
    console.log(`   ${w}: ${ok}/${sent} land, at most ${maxRays} rays / ${maxMs.toFixed(2)} ms of a second's budget (${HON.rays} rays, ${HON.ms} ms)`);
  }
});

console.log(n, 'passed');
process.exit(0);
