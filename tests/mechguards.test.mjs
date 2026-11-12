// mech drop: two server guards from the #310 review, on a stub room (the real methods, fake players and boxes).
// node --test tests/mechguards.test.mjs
import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { Room } from '../server/room.js';
import { MECH } from '../shared/mech.js';

const PP = MECH.paperplane;
after(() => setImmediate(() => process.exit(process.exitCode || 0))); // (the room module keeps timers running)
function stubRoom(boxes) {
  const R = Object.create(Room.prototype), out = [], hurts = [];
  Object.defineProperty(R, 'boxes', { value: boxes, writable: true }); // (boxes is a getter on the real room)
  Object.assign(R, { players: new Map(), cfg: { map: 'warehouse' }, round: { over: false }, broadcast: (m) => out.push(m), hurt: (t, o, w, a) => hurts.push({ t: t.id, w, a }), mechOn: () => true, mechEyeOf: (p) => p.eye, mechCenter: (p) => p.c });
  return { R, out, hurts };
}
// a pilot at x 0 and a target at x 12, the drone already pecking over the target
function droneScene(wall) {
  const boxes = wall ? [{ min: [5.8, -1, -3], max: [6.2, 8, 3] }] : [];
  const { R, out, hurts } = stubRoom(boxes);
  const o = { id: 1, alive: true, eye: [0, 3, 0] }, t = { id: 2, alive: true, c: [12, 1.2, 0] };
  R.players.set(1, o); R.players.set(2, t);
  const n = Date.now(), dr = { id: 7, o: 1, to: 2, p: [12, 2.6, 0], ph: 'peck', t: n, born: n, next: n, pecks: 0, sync: 0 };
  R._drones = new Map([[7, dr]]);
  return { R, out, hurts, dr, n };
}

test('crane drone: pecks a target it can see', () => {
  const { R, hurts, dr, n } = droneScene(false);
  R.tickDrones(n, 0.05);
  assert.equal(hurts.length, 1); assert.equal(hurts[0].w, 'mechcrane'); assert.equal(hurts[0].a, PP.crane.dmg); assert.equal(dr.pecks, 1);
});

test('crane drone: a wall between the pilot and the target and it stops pecking and heads home', () => {
  const { R, hurts, dr, n } = droneScene(true);
  R.tickDrones(n, 0.05);
  assert.equal(hurts.length, 0, 'no peck through the wall'); assert.equal(dr.ph, 'back');
  for (let i = 1; i <= 10; i++) R.tickDrones(n + i * 400, 0.05); // (it never comes back to peck them)
  assert.equal(hurts.length, 0);
});

test('bot mech earn: dropped after a map change or a new round, called in when nothing changed', async () => {
  const run = async (change) => {
    const { R } = stubRoom([]); const calls = [];
    const b = { id: 5, name: 'Gary', alive: true, isBot: true, pos: [0, 0, 0], yaw: 0 };
    R.players.set(5, b);
    Object.assign(R, { mechOf: () => null, isBall: () => false, mechCall: (p, at, f) => { calls.push({ at, f }); return true; } });
    R.mechBotEarn(b);
    change(R);
    await new Promise((r) => setTimeout(r, 900));
    return calls;
  };
  assert.equal((await run(() => {})).length, 1, 'no change: it calls one in');
  assert.equal((await run((R) => { R.cfg.map = 'bazaar'; })).length, 0, 'map changed: nothing');
  assert.equal((await run((R) => { R.round = { over: false }; })).length, 0, 'a new round: nothing');
  assert.equal((await run((R) => { R.players.delete(5); })).length, 0, 'the bot left: nothing');
});
