// weather: the server's timeline (shared/weather.js), its 'wx' message (server/weather.js), the client's check of it,
// and every weather map's Blender kit on disk. node --test tests/weather.test.mjs
import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { WX_KINDS, WX_MAPS, WX_SPAN, WX_MAXPH, wxPlan, wxAt, wxStrikes, wxMsg, wxCheck } from '../shared/weather.js';
import { MAPS } from '../shared/map.js';
import { Room } from '../server/room.js';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
after(() => setImmediate(() => process.exit(process.exitCode || 0))); // (the room module keeps timers running)

test('the plan: same seed, same weather; different seeds differ', () => {
  assert.deepEqual(wxPlan('suburb', 1234), wxPlan('suburb', 1234));
  assert.deepEqual(wxStrikes(wxPlan('platform', 99), 0), wxStrikes(wxPlan('platform', 99), 0));
  assert.notDeepEqual(wxPlan('suburb', 1).ph, wxPlan('suburb', 2).ph);
});

test('the plan: starts clear, showers in range, in order, inside the span', () => {
  for (const map of Object.keys(WX_MAPS)) for (let seed = 1; seed < 60; seed++) {
    const p = wxPlan(map, seed * 7919), K = WX_KINDS[WX_MAPS[map].k];
    assert.ok(p.ph.length >= 3 && p.ph.length <= WX_MAXPH, `${map}: ${p.ph.length} showers`);
    assert.ok(p.ph[0][0] >= K.first[0] - 0.1 && p.ph[0][0] <= K.first[1] + 0.1, 'the first one rolls in after 1-2 minutes');
    assert.equal(wxAt(p, 10).s, 0, 'clear at the start');
    let last = 0;
    for (const [a, b, k, s] of p.ph) {
      assert.ok(a >= last && b > a && b <= WX_SPAN, 'in order, inside the span');
      assert.ok(b - a <= K.len[1] + 0.2, 'not longer than a shower');
      assert.equal(k, WX_MAPS[map].k);
      assert.ok(s >= WX_MAPS[map].s[0] && s <= WX_MAPS[map].s[1]);
      last = b + K.gap[0] - 0.2;
    }
    const [a, b, , s] = p.ph[0];
    assert.equal(wxAt(p, (a + b) / 2).s, s, 'full strength mid-shower');
    assert.ok(wxAt(p, a + 1).s < s && wxAt(p, a + 1).s > 0, 'rolls in');
    for (const [t, ang, dist, bolt] of wxStrikes(p, 0)) assert.ok(t >= a && t <= b && Number.isFinite(ang) && dist >= 140 && dist <= 300 && bolt >= 0 && bolt <= 2);
  }
});

test('no weather on the maps that get theirs later, and the test knob', () => {
  for (const map of ['crate', 'backrooms', 'desert', 'bazaar', 'islands', 'forest']) assert.equal(wxPlan(map, 5).ph.length, 0, map);
  assert.deepEqual(wxPlan('suburb', 5, 'rain').ph, [[0, WX_SPAN, 'rain', 1]]);
  assert.equal(wxPlan('suburb', 5, 'off').ph.length, 0);
  assert.equal(wxPlan('crate', 5, 'rain').ph.length, 0, 'the knob only rains where rain belongs');
});

test('every weather map exists, and its kit glb is on disk', () => {
  for (const [map, w] of Object.entries(WX_MAPS)) {
    assert.ok(MAPS[map], map);
    const f = path.join(ROOT, 'public/models/wx', WX_KINDS[w.k].kit + '.glb');
    assert.ok(fs.existsSync(f) && fs.statSync(f).size > 1000, f);
    const b = fs.readFileSync(f), j = JSON.parse(b.slice(20, 20 + b.readUInt32LE(12)).toString());
    const names = new Set(j.nodes.map((n) => n.name)), clips = new Set((j.animations || []).map((a) => a.name));
    for (const n of ['wx_curtain', 'wx_splash_a', 'wx_splash_b', 'wx_ripple', 'wx_puddle', 'wx_clouds', 'wx_bolt_0', 'wx_bolt_1', 'wx_bolt_2']) assert.ok(names.has(n), n);
    for (const c of ['wx_curtain_fall', 'wx_splash_a_clip', 'wx_splash_b_clip', 'wx_ripple_clip', 'wx_clouds_turn', 'strike_0', 'strike_1', 'strike_2']) assert.ok(clips.has(c), c);
    for (const a of j.animations) for (const c of a.channels) assert.ok(['translation', 'rotation', 'scale'].includes(c.target.path), 'transform clips only (no material animation)');
  }
});

test('the client checks the message: good ones pass, junk is dropped', () => {
  const p = wxPlan('rooftop', 42), m = JSON.parse(JSON.stringify(wxMsg(p, 12.34)));
  assert.equal(m.t, 'wx'); assert.equal(m.el, 12.3);
  assert.deepEqual(wxCheck(m).ph, p.ph);
  const bad = [null, 5, {}, { ...m, m: 7 }, { ...m, el: -1 }, { ...m, el: NaN }, { ...m, s: 'x' }, { ...m, ph: 'rain' }, { ...m, ph: [[0, 10, 'lava', 1]] },
    { ...m, ph: [[0, 10, 'rain', 2]] }, { ...m, ph: [[10, 5, 'rain', 1]] }, { ...m, ph: [[0, Infinity, 'rain', 1]] }, { ...m, ph: [[0, 10, 'rain']] },
    { ...m, ph: Array(WX_MAXPH + 1).fill([0, 10, 'rain', 1]) }, { ...m, ph: [[0, 10, '__proto__', 1]] }];
  for (const b of bad) assert.equal(wxCheck(b), null, JSON.stringify(b).slice(0, 80));
});

test('the room: a plan on the first join, the same plan for a late joiner, a new one on a map change or a new match', () => {
  const R = new Room('wxtest', 'bots'), got = new Map();
  const sock = (id) => { got.set(id, []); return { readyState: 1, send: (s) => got.get(id).push(JSON.parse(s)) }; };
  R.addHuman(sock('a'), { name: 'a', cfg: { map: 'suburb', bots: 0, game: 'dm' } });
  const first = got.get('a').filter((m) => m.t === 'wx');
  assert.equal(first.length, 1, 'one plan with the welcome');
  assert.equal(first[0].m, 'suburb'); assert.ok(wxCheck(first[0]), 'it passes the client check');
  const welcome = got.get('a').findIndex((m) => m.t === 'welcome'), wx = got.get('a').findIndex((m) => m.t === 'wx');
  assert.ok(welcome >= 0 && wx > welcome, 'after the welcome (the map is known by then)');
  R.wx.t0 -= 95e3; // 95 s later someone joins: same plan, the clock 95 s on
  R.addHuman(sock('b'), { name: 'b' });
  const late = got.get('b').filter((m) => m.t === 'wx');
  assert.equal(late.length, 1); assert.deepEqual(late[0].ph, first[0].ph); assert.equal(late[0].s, first[0].s);
  assert.ok(Math.abs(late[0].el - 95) < 1, 'the late joiner is told how far in it is');
  assert.equal(got.get('a').filter((m) => m.t === 'wx').length, 1, 'nobody else got it again');
  R.wxCheck(); assert.equal(got.get('a').filter((m) => m.t === 'wx').length, 1, 'nothing changed: nothing sent');
  R.cfg.map = 'crate'; R.wxCheck();
  const swap = got.get('a').filter((m) => m.t === 'wx').at(-1);
  assert.equal(swap.m, 'crate'); assert.equal(swap.ph.length, 0, 'a clear map clears it');
  R.cfg.map = 'platform'; R.wxCheck(); const s1 = got.get('b').filter((m) => m.t === 'wx').at(-1).s;
  R.round.t0 = Date.now() + 1; R.wxCheck();
  assert.notEqual(got.get('b').filter((m) => m.t === 'wx').at(-1).s, s1, 'a new match rolls new weather');
});
