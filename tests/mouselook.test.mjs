// node tests/mouselook.test.mjs : the shared mouse-look filter (public/js/mouselook.js) drops the events that make the
// camera snap (garbage right after locking, one fake giant jump) and keeps real moves, fast flicks included
import assert from 'node:assert/strict';
import { lookFilter } from '../public/js/mouselook.js';
const f = lookFilter();
f.locked(1000);
assert.equal(f.take(30, 0, 1050), false, 'the first ~120 ms after locking are dropped');
let kept = 0; for (let i = 0; i < 20; i++) kept += f.take(6, -2, 1200 + i * 8) ? 1 : 0;
assert.equal(kept, 20, 'normal moves all count');
assert.equal(f.take(-640, 120, 1400), false, 'one fake jump way bigger than recent moves is dropped');
assert.equal(f.take(6, 0, 1410), true, 'and the next normal move counts again');
let flick = 0; for (let i = 0; i < 12; i++) flick += f.take(40 + i * 8, 0, 1500 + i * 8) ? 1 : 0;
assert.equal(flick, 12, 'a real fast flick that builds up is kept');
console.log('ok mouselook: 5 checks');
