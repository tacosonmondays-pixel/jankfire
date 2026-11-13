// node tests/story/camctl.test.mjs : the cutscene / talk camera (public/js/story/camctl.js). once a shot has blended in it
// holds still: it used to drop its weight every other frame (1 -> 0.967 -> 1 ...), so the picture slid 0.3% back toward
// your own eye and view and snapped back, a 30 Hz shake in every scene and talk. blending in and out stays smooth.
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { wantShot, takeCamera, shotOn } from '../../public/js/story/camctl.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };

const eye = new THREE.Vector3(0, 1.6, 0); // the player's own camera: placed by main.js every frame, before the shot
const cam = new THREE.PerspectiveCamera(70, 16 / 9, 0.05, 1000);
const frame = (dt = 1 / 60) => { cam.position.copy(eye); cam.rotation.set(0, 0, 0); cam.fov = 70; takeCamera(cam, dt); return cam.position.clone(); };
const shot = () => ({ pos: new THREE.Vector3(30, 5, 20), look: new THREE.Vector3(30, 4, 0), fov: 45, blend: 0.5, follow: 10 });

t('a held shot stays exactly on its mark, frame after frame (no every-other-frame shake)', () => {
  const s = shot();
  for (let i = 0; i < 90; i++) { wantShot({ ...s, pos: s.pos.clone(), look: s.look.clone() }); frame(); } // (scene.js asks again every frame)
  const ps = [], qs = [];
  for (let i = 0; i < 60; i++) { wantShot({ ...s, pos: s.pos.clone(), look: s.look.clone() }); ps.push(frame()); qs.push(cam.quaternion.clone()); }
  for (const p of ps) assert.ok(p.distanceTo(s.pos) < 1e-6, `on the mark: ${p.toArray()}`);
  for (let i = 1; i < qs.length; i++) assert.ok(qs[i].angleTo(qs[i - 1]) < 1e-6, 'no turn while held');
  assert.ok(Math.abs(cam.fov - 45) < 1e-6, 'the shot\'s fov');
});

t('blending in and out moves one way only (no back-and-forth)', () => {
  wantShot(null); for (let i = 0; i < 120; i++) frame(); assert.equal(shotOn(), false);
  const s = shot(); let last = -1;
  for (let i = 0; i < 40; i++) { wantShot({ ...s, pos: s.pos.clone(), look: s.look.clone() }); const d = frame().distanceTo(eye); assert.ok(d >= last - 1e-9, `in: ${d} after ${last}`); last = d; }
  wantShot(null); last = 1e9;
  for (let i = 0; i < 60; i++) { const d = frame().distanceTo(eye); assert.ok(d <= last + 1e-9, `out: ${d} after ${last}`); last = d; }
  assert.ok(last < 1e-6, 'back on your own eye'); assert.equal(shotOn(), false);
});

console.log(`${n} ok`);
