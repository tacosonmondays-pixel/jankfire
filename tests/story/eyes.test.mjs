// the story cast's eyes (public/js/story/face.js, the look in actors.js): "NPC eyes are also funky"
//   an actor looking at you points both eyes at you: not cross-eyed at its own chin (actors.js handed the face a
//   scratch vector that pose() then filled with the head's position), not twitching on the puppets' 12 fps steps
//   the look is right from a turned, tilted head (yaw then pitch); at rest both eyes move together
//   shut lids cover the iris, pupil and glint wherever the eye is looking (a flat iris disc used to poke through)
//   the brows: bt + = angry (inner ends down), sad and the choir's eyes have the inner ends up
//   painted dot eyes (the temps) sit on the skin of the head, not 2 cm in front of it
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import * as THREE from 'three';
import { buildFace, FACES } from '../../public/js/story/face.js';

const ROOT = new URL('../../', import.meta.url);
const deg = (r) => (r * 180) / Math.PI;
const fwd = (o) => new THREE.Vector3(0, 0, -1).applyQuaternion(o.getWorldQuaternion(new THREE.Quaternion()));
const aimErr = (e, T) => fwd(e.piv).angleTo(T.clone().sub(e.piv.getWorldPosition(new THREE.Vector3())));

// actors.js for real, its heavy imports stood in for: a plain skeleton with the real face rig on its head
const js = (s) => 'data:text/javascript,' + encodeURIComponent(s);
const THREE_URL = import.meta.resolve('three'), FACE_URL = new URL('public/js/story/face.js', ROOT).href;
const STUB = {
  '/shared/map.js': js('export const BOXES = [];'),
  '/shared/physics.js': js('export function raycast() { return null; }'),
  '../loco.js': js('export function locoPose() {}'),
  './babble.js': js('export const voice = () => ({ update() {}, level: 0, blip() {} });'),
  './looks.js': js(`import * as THREE from ${JSON.stringify(THREE_URL)}; import { buildFace } from ${JSON.stringify(FACE_URL)};
export const faceLocked = () => false;
export function buildLook(id) {
  const g = (p, x = 0, y = 0, z = 0) => { const o = new THREE.Group(); o.position.set(x, y, z); if (p) p.add(o); return o; };
  const root = g(), body = g(root), spine = g(body, 0, 0.98, 0), neck = g(spine, 0, 0.6, 0), head = g(neck, 0, 0.02, 0);
  const legL = g(body, -0.1, 0.92), legR = g(body, 0.1, 0.92), kneeL = g(legL, 0, -0.44), kneeR = g(legR, 0, -0.44);
  const arm = g(spine, 0.25, 0.44), armL = g(spine, -0.25, 0.44), foreR = g(arm, 0, -0.26), foreL = g(armL, 0, -0.26), handR = g(foreR, 0, -0.26), handL = g(foreL, 0, -0.26);
  const egg = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshBasicMaterial()); egg.scale.set(0.12, 0.17, 0.13); egg.position.y = 0.17; head.add(egg);
  spine.rotation.x = -0.25; head.rotation.z = 0.12; // (a hunch and the jank tilt: the eyes must still find you)
  const face = buildFace(head, { z: -0.122, eyeR: 0.03, s: id === 'puppet' ? 1.3 : 1 });
  root.scale.setScalar(1.1);
  return { ch: { root, body, spine, neck, head, legL, legR, kneeL, kneeR, arm, armL, foreL, foreR, handL, handR }, face, kind: id, look: id };
}`),
};
register(js(`const STUB = ${JSON.stringify(STUB)};
export async function resolve(s, c, next) { if (c.parentURL && c.parentURL.endsWith('/public/js/story/actors.js') && STUB[s]) return { url: STUB[s], shortCircuit: true }; return next(s, c); }`));
const A = await import('../../public/js/story/actors.js');
const { G } = await import('../../public/js/ctx.js');
G.scene = new THREE.Scene();

for (const kind of ['normal', 'puppet']) test(`a ${kind} looking at you: both eyes on you, every frame, not cross-eyed`, () => {
  A.clearActors();
  const a = A.spawnActor('t_' + kind, { look: kind, voice: {} }, [0, 0, 0], 0.4);
  const T = new THREE.Vector3(0.9, 1.85, -2.3), eye = T.toArray(); // (you: in front, off to their left, a bit above)
  let t = 0, worst = 0, jump = 0, prev = null;
  for (let i = 0; i < 150; i++) { // 2.5 s at 60 fps (puppets pose on 12 fps steps, the face runs every frame)
    t += 1 / 60; A.updateActors(1 / 60, t * 1000, eye); a.ch.root.updateMatrixWorld(true);
    if (i < 60) continue; // (the head turns to you first)
    const d = a.face.eyes.map((e) => fwd(e.piv));
    for (const e of a.face.eyes) worst = Math.max(worst, aimErr(e, T));
    if (prev) jump = Math.max(jump, ...d.map((v, k) => v.angleTo(prev[k])));
    prev = d;
  }
  assert.ok(deg(worst) < 1, `each eye points at you (worst ${deg(worst).toFixed(1)} deg off)`);
  assert.ok(deg(jump) < 1, `no jump on the steps (${deg(jump).toFixed(2)} deg in a frame)`);
  const [l, r] = a.face.eyes.map((e) => fwd(e.piv)), conv = deg(l.angleTo(r));
  assert.ok(conv < 6, `the two eyes nearly parallel at 2.5 m, not crossed (${conv.toFixed(1)} deg apart)`);
  A.clearActors();
});

test('the look: right from a turned, tilted, hunched head, yaw then pitch', () => {
  const root = new THREE.Group(), head = new THREE.Group(); root.add(head);
  root.rotation.set(-0.3, 0.8, 0.15); root.position.set(1, 1.6, -2);
  const r = buildFace(head, { eyeR: 0.04 }); root.updateMatrixWorld(true);
  for (const T of [[0.6, 0.55, -2], [-0.5, -0.3, -2.5], [0.9, 0.9, -2.2]].map((p) => root.localToWorld(new THREE.Vector3(...p)))) { // (in the head's frame: up to 0.4 rad across, 0.3 up)
    r.look = T; for (let i = 0; i < 60; i++) r.update(1 / 60);
    for (const e of r.eyes) assert.ok(deg(aimErr(e, T)) < 0.5, `eye ${e.sx} on ${T.toArray()} (${deg(aimErr(e, T)).toFixed(2)} deg off)`);
  }
  r.look = root.localToWorld(new THREE.Vector3(-30, 0.2, -2)); for (let i = 0; i < 60; i++) r.update(1 / 60); // (way off past the corner of the eye: a look lets go)
  assert.ok(r.eyes.every((e) => Math.abs(e.piv.rotation.y) < 0.3), 'a look out past where eyes go: they go with the head instead of straining');
  r.gaze = r.look; for (let i = 0; i < 60; i++) r.update(1 / 60);
  assert.ok(r.eyes.every((e) => Math.abs(e.piv.rotation.y) > 0.55), 'a gaze holds on (the choir\'s stare)');
});

test('at rest the two eyes move together', () => {
  const r = buildFace(new THREE.Group(), {});
  let moved = 0;
  for (let i = 0; i < 600; i++) {
    r.update(1 / 60);
    const [a, b] = r.eyes.map((e) => e.piv.rotation);
    assert.ok(Math.abs(a.x - b.x) < 1e-9 && Math.abs(a.y - b.y) < 1e-9, `same look up / down and across (${a.x} vs ${b.x})`);
    moved = Math.max(moved, Math.abs(a.y));
  }
  assert.ok(moved > 0.01, 'and they still glance about');
});

test('shut lids cover the iris, pupil and glint, wherever the eye looks', () => {
  for (const o of [{}, { s: 1.6, eyeR: 0.04, redRim: true }, { eyeR: 0.025 }]) {
    const head = new THREE.Group(), r = buildFace(head, o), er = r.eyes[0].ball.geometry.parameters.radius;
    for (const [yy, yx] of [[0, 0], [0.6, 0], [-0.6, 0], [0, 0.4], [0, -0.4], [0.6, 0.4], [-0.6, -0.4]]) {
      for (const e of r.eyes) e.piv.rotation.set(yx, yy, 0);
      r.blink = 0.5; r.blinkT = 9; r.update(0); for (const e of r.eyes) e.piv.rotation.set(yx, yy, 0); // (update(0) eases the look in one go: put it back)
      head.updateMatrixWorld(true);
      r.eyes.forEach((e, i) => {
        const { top, bot } = r.lids[i], lp = top.parent, v = new THREE.Vector3();
        e.piv.traverse((m) => {
          if (!m.isMesh || m === e.ball) return;
          const p = m.geometry.attributes.position;
          for (let k = 0; k < p.count; k++) {
            v.fromBufferAttribute(p, k).applyMatrix4(m.matrixWorld); lp.worldToLocal(v);
            assert.ok(v.length() < er * 1.12, `inside the lids' ball (${(v.length() / er).toFixed(3)} x the eye's radius)`);
            const up = (L) => v.clone().applyQuaternion(L.quaternion.clone().invert()).y > -1e-9;
            assert.ok(up(top) || up(bot), `under a lid at look ${yy}, ${yx}`);
          }
        });
      });
    }
    if (o.redRim) assert.ok(r.eyes.every((e) => !e.piv.children.some((m) => m.geometry && m.geometry.type === 'TorusGeometry')), 'the red rim stays on the socket (it drew a line across the white turning with the eye)');
  }
});

test('the lids follow the eye up and down a little', () => {
  const r = buildFace(new THREE.Group(), {});
  r.blinkT = 9; r.update(0); const top0 = r.lids[0].top.rotation.x;
  r.look = new THREE.Vector3(0, 3, -1); r.update(0);
  assert.ok(r.lids[0].top.rotation.x > top0 + 0.1, 'looking up lifts the top lid');
});

test('brows: angry pulls the inner ends down, sad and the choir lift them', () => {
  const inner = (f) => { const head = new THREE.Group(), r = buildFace(head, {}); r.set(f); for (let i = 0; i < 40; i++) r.update(0.05); head.updateMatrixWorld(true);
    return r.brows.map((b) => { const p = b.m.geometry.attributes.position, vs = []; for (let i = 0; i < p.count; i++) vs.push(new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(b.m.matrixWorld));
      vs.sort((a, c) => Math.abs(a.x) - Math.abs(c.x)); const y = (a) => a.reduce((s, v) => s + v.y, 0) / a.length; return y(vs.slice(0, vs.length / 2)) - y(vs.slice(vs.length / 2)); }); };
  assert.ok(FACES.angry.bt > 0 && FACES.sad.bt < 0);
  for (const d of inner('angry')) assert.ok(d < -0.01, 'angry: inner ends down ' + d);
  for (const d of inner('sad')) assert.ok(d > 0.01, 'sad: inner ends up ' + d);
  for (const d of inner('choir')) assert.ok(d > 0.01, 'the choir: sad eyes over the smile ' + d);
});

test('painted dot eyes sit on the skin of the head', () => {
  const head = new THREE.Group(), egg = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), new THREE.MeshBasicMaterial());
  egg.scale.set(0.11, 0.187, 0.13); egg.position.y = 0.17; head.add(egg); head.rotation.z = 0.1; head.scale.setScalar(1.08);
  const r = buildFace(head, { flatFace: true, eyeR: 0.022, eyeY: 0.2, brow: false, z: -0.122 });
  assert.equal(r.fit(head), 2, 'both dots found the skin');
  head.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(egg.matrixWorld).invert();
  for (const e of r.eyes) {
    const c = e.ball.getWorldPosition(new THREE.Vector3()).applyMatrix4(inv).length(); // (1 = on the egg's surface)
    assert.ok(Math.abs(c - 1) < 0.03, `the dot's centre on the egg (${c.toFixed(3)} x its radius)`);
  }
  r.look = new THREE.Vector3(3, 0.2, -1); for (let i = 0; i < 60; i++) r.update(1 / 60); head.updateMatrixWorld(true);
  for (const e of r.eyes) assert.ok(Math.abs(e.ball.getWorldPosition(new THREE.Vector3()).applyMatrix4(inv).length() - 1) < 0.03, 'and stays on it looking at you');
});
