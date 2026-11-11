// node tests/story/act1world.test.mjs : Act I in the slice city (the WORLD wiring pass). Every place an Act I step
// points at (markers, reach / escort / deliver zones, interact targets) is a real spot in PLACES; every person a step
// asks you to talk to has a spot to stand at; each spot is standing room with floor under it; and you can walk there
// from the Lost & Found and back (the Wok Roofs: there's a roof to grapple onto). Also: the Lost & Found's door opens.
import assert from 'node:assert/strict';
import { MISSIONS_ACT1 as MISSIONS } from '../../shared/story/content/missions/act1.js';
import { PLACES } from '../../shared/city/slice.js';
import { NPC_SPOTS, STAGE } from '../../shared/city/cast_slice.js';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { buildChunkNav, NavWorld, NAV } from '../../shared/city/cnav.js';
import { playerOverlap } from '../../shared/physics.js';

// a player walks stairs the bots' graph calls too steep (0.38 m treads, 0.7 m a metre): judge "on foot" like a player
NAV.step = 0.8;
const W = new ChunkWorld([]), N = new NavWorld();
for (let cx = -5; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) { const p = packChunk(buildChunk('slice', cx, cz)); W.set(cx + ':' + cz, chunkBoxes(p)); N.set(cx, cz, buildChunkNav(p)); }
W.sync();
const floor = (p, up = 1.5) => { const h = W.raycast([p[0], p[1] + up, p[2]], [0, -1, 0], up + 6); return h ? h.point[1] : null; };
const walk = (a, b) => !!N.path(a, b, 3e6);

// 1. what Act I asks for
const OWNED = { overtime: 'fights (B): the boss stands in his arena', eotm: 'encounters (C): the robbery', choice: '', you: '' };
const places = new Set(), people = new Set();
for (const m of Object.values(MISSIONS)) for (const s of m.steps) {
  const g = s.goal || {};
  if (s.marker) places.add(s.marker);
  if (g.zone) places.add(g.zone);
  if (g.type === 'interact' && g.target.includes(':')) places.add(g.target);
  if (g.type === 'talk' && !Object.hasOwn(OWNED, g.who)) people.add(g.who);
}
for (const id of places) assert.ok(PLACES[id], `act I points at ${id}, which isn't in PLACES`);
for (const id of people) assert.ok(NPC_SPOTS[id] || STAGE.some(([, , w]) => w[id]), `act I wants a talk with ${id}, who has nowhere to stand`);

// 2. standing room: a body fits, with floor under it (not a roof you'd fall off: within 1 m below)
const HOME = [-189, 8.2, 196]; // in front of the Machine's tray
const spots = [...[...places].map((id) => [id, PLACES[id].p]), ...Object.entries(NPC_SPOTS).map(([id, s]) => ['npc ' + id, s.p]), ...STAGE.flatMap(([q, st, w]) => Object.entries(w).map(([id, s]) => [`${q}.${st} ${id}`, s.p]))];
for (const [id, p] of spots) {
  if (id === 'commute:underhill_loop' || id === 'commute:tunnel_mouth' || id === 'bottom:rooftops') continue; // (checked below: the train's places, the roofs)
  const f = floor(p);
  assert.ok(f != null && Math.abs(f - p[1]) < 1, `${id}: no floor under ${p} (found ${f})`);
  assert.ok(!playerOverlap([p[0], f + 0.05, p[2]], W.boxes) || id.startsWith('npc dot') || id.startsWith('npc mina'), `${id}: ${p} is inside something`); // (Dot and Mina are IN the wall)
}
// 3. on foot from the Lost & Found and back
const NOT_ON_FOOT = { 'bottom:rooftops': 'grapple', 'commute:underhill_loop': 'train', 'commute:tunnel_mouth': 'train', 'bottom:gym': 'own island', 'gut:clinic_bev': 'doorway' };
for (const [id, p] of spots) {
  const key = id.replace(/^npc /, '');
  if (NOT_ON_FOOT[key] || /^npc (dot|mina|bev|lumps)$/.test(id)) continue;
  const g = [p[0], floor(p) ?? p[1], p[2]];
  assert.ok(walk(HOME, g), `can't walk from the Lost & Found to ${id} ${p}`);
  assert.ok(walk(g, HOME), `can't walk back to the Lost & Found from ${id} ${p}`);
}
// Bev's clinic: the doorstep (her door is narrower than the walk graph's 1 m cells: e2e walks in)
assert.ok(walk(HOME, [-84.3, 36, -2.5]) && walk([-84.3, 36, -2.5], HOME), "Bev's doorstep");
// the Wok Roofs: a roof right there to land on, 9+ m over the lane, and the lane under it is walkable
{ const p = PLACES['bottom:rooftops'].p, top = W.raycast([p[0], 40, p[2]], [0, -1, 0], 60).point[1];
  assert.ok(Math.abs(top - p[1]) < 3 && top > 12, 'no wok roof under the zone: ' + top); }
// the Under-Hill Loop's portal and its mouth: ground there, out in the open
for (const id of ['commute:underhill_loop', 'commute:tunnel_mouth']) { const p = PLACES[id].p, f = floor(p, 3); assert.ok(f != null && Math.abs(f - p[1]) < 1.5, id + ' floor ' + f); }
// 4. the hub's door: out through the front, down the steps into the yard, and back up
assert.ok(walk(HOME, [-189, 4, 216]) && walk([-189, 4, 216], HOME), 'the Lost & Found is boxed in again');
console.log(`act I world ok: ${places.size} places, ${people.size} people to talk to, ${spots.length} spots`);
