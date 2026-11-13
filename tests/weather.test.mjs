// weather: the server's timeline (shared/weather.js), its 'wx' message (server/weather.js), the client's check of it,
// and every weather map's Blender kit on disk. node --test tests/weather.test.mjs
import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { WX_KINDS, WX_MAPS, WX_SPAN, WX_MAXPH, wxPlan, wxAt, wxStrikes, wxMsg, wxCheck, wxErupt, wxBombs, wxMeteors, wxKindsOf, wxOf } from '../shared/weather.js';
import { raycast } from '../shared/physics.js';
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
  for (const map of Object.keys(WX_MAPS).filter((m) => !WX_KINDS[WX_MAPS[m].k].after)) for (let seed = 1; seed < 60; seed++) {
    const p = wxPlan(map, seed * 7919), K = WX_KINDS[WX_MAPS[map].k];
    assert.ok(p.ph.length >= 3 && p.ph.length <= WX_MAXPH, `${map}: ${p.ph.length} showers`);
    assert.ok(p.ph[0][0] >= K.first[0] - 0.1 && p.ph[0][0] <= K.first[1] + 0.1, 'the first one rolls in after a minute or two');
    assert.equal(wxAt(p, 10).s, 0, 'clear at the start');
    let last = 0;
    for (const [a, b, k, s] of p.ph) {
      assert.ok(a >= last && b > a && b <= WX_SPAN, 'in order, inside the span');
      assert.ok(b - a <= WX_KINDS[k].len[1] + 0.2, 'not longer than a shower');
      assert.ok(wxKindsOf(map).includes(k), `${map}: ${k}`);
      assert.ok(s >= WX_MAPS[map].s[0] && s <= WX_MAPS[map].s[1]);
      last = b + Math.min(...wxKindsOf(map).map((q) => WX_KINDS[q].gap ? WX_KINDS[q].gap[0] : 0)) - 0.2;
    }
    const [a, b, , s] = p.ph[0];
    assert.equal(wxAt(p, (a + b) / 2).s, s, 'full strength mid-shower');
    assert.ok(wxAt(p, a + 1).s < s && wxAt(p, a + 1).s > 0, 'rolls in');
    for (const [t, ang, dist, bolt] of wxStrikes(p, 0)) assert.ok(t >= a && t <= b && Number.isFinite(ang) && dist >= 140 && dist <= 300 && bolt >= 0 && bolt <= 2);
  }
});

test('no weather on the maps that get theirs later, and the test knob', () => {
  for (const map of ['crate', 'backrooms']) assert.equal(wxPlan(map, 5).ph.length, 0, map);
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
    const need = w.k === 'sand' ? [['wx_sand_wall', 'wx_sand_billow', 'wx_sand_grit', 'wx_sand_ribbon', 'wx_tumbleweed', 'wx_sand_rag'], ['sand_wall_turn', 'sand_billow_turn', 'sand_grit_blow', 'sand_ribbon_blow', 'tumble_bounce', 'rag_fly']] : w.k === 'snow' ? [['wx_snow_curtain', 'wx_snowpatch', 'wx_snow_clouds'], ['wx_snow_curtain_fall', 'wx_snow_clouds_turn']]
      : w.k === 'stars' ? [['wx_meteor', 'wx_meteor_big', 'wx_twinkle'], ['meteor_fly', 'meteor_big_fly', 'twinkle']] : w.k === 'erupt' ? [['wx_plume', 'wx_ash', 'wx_bomb', 'wx_trail', 'wx_splat', map === 'islands_sd' ? 'wx_pool_sd' : 'wx_pool'], ['plume_rise', 'plume_churn', 'ash_spread', 'bomb_arc', 'splat_pop', map === 'islands_sd' ? 'pool_rise_sd' : 'pool_rise']]
      : [['wx_curtain', 'wx_splash_a', 'wx_splash_b', 'wx_ripple', 'wx_puddle', 'wx_clouds', 'wx_bolt_0', 'wx_bolt_1', 'wx_bolt_2'], ['wx_curtain_fall', 'wx_splash_a_clip', 'wx_splash_b_clip', 'wx_ripple_clip', 'wx_clouds_turn', 'strike_0', 'strike_1', 'strike_2']];
    for (const n of need[0]) assert.ok(names.has(n), n);
    for (const c of need[1]) assert.ok(clips.has(c), c);
    for (const k of wxKindsOf(map)) assert.ok(fs.existsSync(path.join(ROOT, 'public/models/wx', WX_KINDS[k].kit + '.glb')), `${map}: its ${k} kit too`);
    if (WX_KINDS[w.k].after) assert.ok(fs.existsSync(path.join(ROOT, 'public/models/wx', WX_KINDS[WX_KINDS[w.k].after].kit + '.glb')), 'its downpour kit too');
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

test('Mount Kaboom: clear first, an eruption, its downpour straight after, quiet, again', () => {
  for (const map of ['islands', 'islands_sd']) for (let seed = 1; seed < 40; seed++) {
    const p = wxPlan(map, seed * 104729), K = WX_KINDS.erupt;
    assert.ok(p.ph.length >= 4 && p.ph.length <= WX_MAXPH && p.ph.length % 2 === 0);
    assert.equal(wxAt(p, 30).s, 0, 'clear at the start');
    assert.ok(p.ph[0][0] >= K.first[0] - 0.1 && p.ph[0][0] <= K.first[1] + 0.1);
    for (let i = 0; i < p.ph.length; i += 2) {
      const [a, b, k] = p.ph[i], [c, d, k2, s2] = p.ph[i + 1];
      assert.equal(k, 'erupt'); assert.equal(k2, 'rain'); assert.equal(c, b, 'the downpour follows right on');
      assert.ok(b - a >= K.len[0] - 0.2 && b - a <= K.len[1] + 0.2 && d > c && d <= WX_SPAN && s2 >= 0.75 && s2 <= 1);
      if (i) assert.ok(a - p.ph[i - 1][1] >= K.gap[0] - 0.2, 'a long quiet between');
      assert.equal(wxErupt(p.ph[i], a + 1).stage, 'build'); assert.equal(wxErupt(p.ph[i], a + K.build + 1).stage, 'blast'); assert.equal(wxErupt(p.ph[i], b - 1).stage, 'settle');
    }
  }
  assert.deepEqual(wxPlan('islands', 9, 'erupt').ph, [[-WX_KINDS.erupt.build, WX_SPAN, 'erupt', 1]], 'the knob: already erupting at second 0');
  assert.equal(wxErupt(wxPlan('islands', 9, 'erupt').ph[0], 0).stage, 'blast');
  assert.ok(wxCheck(wxMsg(wxPlan('islands', 9, 'erupt'), 0)), 'an early start passes the client check');
  assert.equal(wxCheck({ ...wxMsg(wxPlan('islands', 9, 'erupt'), 0), ph: [[-5000, 10, 'erupt', 1]] }), null);
  assert.deepEqual(wxPlan('islands', 9, 'rain').ph, [[0, WX_SPAN, 'rain', 1]], 'JF_WEATHER=rain: the downpour on its own');
});

test('lava bombs: the same landings everywhere, only while it blasts, on the ground or a box top (never under the map)', () => {
  for (const map of ['islands', 'islands_sd']) {
    const p = wxPlan(map, 31337), ph = p.ph[0], K = WX_KINDS.erupt, w = WX_MAPS[map];
    assert.deepEqual(wxBombs(p, ph[0] + 60), wxBombs(wxPlan(map, 31337), ph[0] + 60), 'deterministic from the plan');
    assert.deepEqual(wxBombs(p, ph[0] - 1), [], 'none before'); assert.deepEqual(wxBombs(p, ph[1] + 1), [], 'none after');
    const L = wxBombs(p, ph[0] + 1), M = MAPS[map];
    assert.ok(L.length > 20, `${map}: ${L.length} bombs`);
    for (const b of L) {
      for (const k of ['x', 'y', 'z', 't', 't0', 'sx', 'sy', 'sz', 'h']) assert.ok(Number.isFinite(b[k]), k);
      assert.ok(b.t0 >= ph[0] + K.build && b.t0 < ph[1] - K.settle && b.t > b.t0 && b.t < ph[1], 'launched in the blast, down before it ends');
      assert.ok(Math.hypot(b.x - w.vent[0], b.z - w.vent[2]) < 70, 'round the volcano');
      assert.ok(b.y >= M.seaY - 0.01 && b.y > M.killY, 'never under the sea or the map');
      const down = raycast([b.x, b.y + 0.5, b.z], [0, -1, 0], 2, M.boxes);
      assert.ok(down ? Math.abs(b.y + 0.5 - down.t - b.y) < 0.02 || b.y === M.seaY : b.y === M.seaY, `on a surface at ${b.x},${b.y},${b.z}`);
    }
    for (let i = 1; i < L.length; i++) assert.ok(L[i].t0 > L[i - 1].t0, 'in launch order');
  }
});

test('snow: the Scary Forest snows, Suburb snows instead of raining about 3 times in 10, the same for the same seed', () => {
  let n = 0, snow = 0;
  for (let seed = 1; seed < 400; seed++) for (const [, , k] of wxPlan('suburb', seed * 2654435761).ph) { n++; if (k === 'snow') snow++; else assert.equal(k, 'rain'); }
  assert.ok(snow / n > 0.24 && snow / n < 0.36, `suburb snow share ${(snow / n).toFixed(2)}`);
  assert.deepEqual(wxPlan('suburb', 99).ph, wxPlan('suburb', 99).ph);
  for (let seed = 1; seed < 50; seed++) for (const [a, b, k] of wxPlan('forest', seed).ph) { assert.equal(k, 'snow'); assert.ok((b - a >= WX_KINDS.snow.len[0] - 0.2 || b === WX_SPAN) && b - a <= WX_KINDS.snow.len[1] + 0.2); } // (the last one may be cut short by the hour)
  for (const [map, knob, kind] of [['forest', 'snow', 'snow'], ['suburb', 'snow', 'snow'], ['rooftop', 'stars', 'stars'], ['desert', 'stars', 'stars']]) assert.deepEqual(wxPlan(map, 3, knob).ph, [[0, WX_SPAN, kind, 1]], `${map} ${knob}`);
  for (const [map, knob] of [['platform', 'snow'], ['forest', 'stars'], ['desert', 'rain'], ['islands', 'snow']]) assert.equal(wxPlan(map, 3, knob).ph.length, 0, `${map} never ${knob}`);
  assert.ok(wxCheck(wxMsg(wxPlan('forest', 3), 1)) && wxCheck(wxMsg(wxPlan('desert', 3), 1)), 'the new kinds pass the client check');
});

test('star showers: Rooftop now and then, the Desert (going to dusk); the meteors are the same everywhere and inside the shower', () => {
  let stars = 0;
  for (let seed = 1; seed < 100; seed++) for (const [, , k] of wxPlan('rooftop', seed).ph) if (k === 'stars') stars++;
  assert.ok(stars > 20, 'rooftop gets star showers');
  assert.ok(WX_MAPS.desert.dusk && !WX_MAPS.rooftop.dusk);
  for (const map of ['desert', 'rooftop', 'desert_sd']) for (let seed = 1; seed < 30; seed++) {
    const p = wxPlan(map, seed), i = p.ph.findIndex((q) => q[2] === 'stars');
    if (i < 0) continue;
    const L = wxMeteors(p, i), [a, b] = p.ph[i];
    assert.deepEqual(L, wxMeteors(wxPlan(map, seed), i));
    assert.ok(L.length > 30, `${map} ${L.length} meteors`);
    for (const [t, az, el, hd, big] of L) assert.ok(t >= a && t <= b && el > 0.3 && el < 1.2 && Number.isFinite(az + hd) && (big === 0 || big === 1));
    assert.ok(L.some((m) => m[4]) || L.length < 60, 'a big one now and then');
  }
  assert.deepEqual(wxMeteors(wxPlan('suburb', 1), 0), [], 'only in a star shower');
});

test('every map that had weather before snow/stars still has it (range kept its rain)', () => {
  for (const m of ['suburb', 'warehouse', 'skyline', 'rooftop', 'range', 'platform', 'deadmall', 'jankburg', 'islands']) assert.ok(WX_MAPS[m], m);
  assert.equal(WX_MAPS.range.k, 'rain');
});

test('sandstorms: the Bazaar gets them, the Desert gets them or a star shower about half and half; the knob; the kit', () => {
  for (const map of ['bazaar', 'bazaar_sd']) for (let seed = 1; seed < 40; seed++) for (const [a, b, k, s] of wxPlan(map, seed * 977).ph) {
    assert.equal(k, 'sand'); assert.ok(s >= 0.7 && s <= 1 && (b - a <= WX_KINDS.sand.len[1] + 0.2));
  }
  for (const map of ['desert', 'desert_sd']) {
    let sand = 0, n = 0;
    for (let seed = 1; seed < 400; seed++) for (const [, , k] of wxPlan(map, seed * 2654435761).ph) { n++; if (k === 'sand') sand++; else assert.equal(k, 'stars'); }
    assert.ok(sand / n > 0.42 && sand / n < 0.58, `${map} sand share ${(sand / n).toFixed(2)}`);
    assert.deepEqual(wxKindsOf(map).sort(), ['sand', 'stars']);
  }
  assert.deepEqual(wxPlan('desert', 77).ph, wxPlan('desert', 77).ph, 'the same seed, the same storms for everyone');
  for (const map of ['desert', 'desert_sd', 'bazaar', 'bazaar_sd']) assert.deepEqual(wxPlan(map, 3, 'sand').ph, [[0, WX_SPAN, 'sand', 1]], `${map} JF_WEATHER=sand`);
  for (const map of ['suburb', 'rooftop', 'islands', 'forest', 'crate', 'jankburg']) assert.equal(wxPlan(map, 3, 'sand').ph.length, 0, `${map} never sand`);
  assert.equal(wxPlan('bazaar', 3, 'stars').ph.length, 0, 'the bazaar: no star shower');
  assert.ok(wxCheck(wxMsg(wxPlan('bazaar', 3), 1)) && wxCheck(wxMsg(wxPlan('desert', 3, 'sand'), 0)), 'sand passes the client check');
  assert.ok(WX_KINDS.sand.front > WX_KINDS.sand.fade && WX_KINDS.sand.front * 2 < WX_KINDS.sand.len[0], 'the wall rolls in and out inside the storm');
  const b = fs.readFileSync(path.join(ROOT, 'public/models/wx/wx_sand.glb')), j = JSON.parse(b.slice(20, 20 + b.readUInt32LE(12)).toString());
  const meta = JSON.parse(j.nodes.find((n) => n.name === 'wx_sand').extras.jf);
  assert.equal(meta.kind, 'sand'); assert.ok(meta.tile > 0 && meta.boing.length >= 3 && meta.len.tumble_bounce > 0 && meta.len.rag_fly > 0);
  assert.ok(j.meshes.length <= 6 && j.materials.length <= 2, 'a few draw calls: one mesh per piece, two materials');
});

test('every map with weather keeps it (one table line each: none swallowed into a comment)', () => {
  const want = { suburb: 'rain', suburb_sd: 'rain', warehouse: 'rain', warehouse_sd: 'rain', skyline: 'rain', skyline_sd: 'rain', rooftop: 'rain', rooftop_sd: 'rain', range: 'rain',
    platform: 'rain', platform_sd: 'rain', deadmall: 'rain', jankburg: 'rain', islands: 'erupt', islands_sd: 'erupt', forest: 'snow', desert: 'stars', desert_sd: 'stars', bazaar: 'sand', bazaar_sd: 'sand' };
  for (const [m, k] of Object.entries(want)) { assert.ok(WX_MAPS[m], m); assert.equal(WX_MAPS[m].k, k, m); assert.ok(wxPlan(m, 11).ph.length > 0, `${m} has weather`); }
  for (const m of ['suburb', 'suburb_sd']) assert.ok(wxKindsOf(m).includes('snow'));
  for (const m of ['rooftop', 'rooftop_sd', 'desert', 'desert_sd']) assert.ok(wxKindsOf(m).includes('stars'));
  for (const m of ['desert', 'desert_sd', 'bazaar', 'bazaar_sd']) assert.ok(wxKindsOf(m).includes('sand'));
  assert.equal(wxOf('br'), null, 'Battle Island stays dry');
});
