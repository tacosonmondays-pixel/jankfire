// node tests/story/shotfit.test.mjs : face shots that fit the actor (public/js/story/shotfit.js, used by shots.js). the
// face's real facing comes from the head bone, not the actor's yaw; a close-up stands clear of a body that reaches out
// in front of the face (Pallet Jack's belly and arms in his last moment) and keeps its usual distance for everyone else
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { faceFwd, reachOf } from '../../public/js/story/shotfit.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };

// an actor like actors.js builds: ch.root (the body), ch.head (a joint under it), meshes on them
function actor({ yaw = 0, headYaw = 0, belly = 0.3, hidden = 0 } = {}) {
  const root = new THREE.Group(), head = new THREE.Group();
  root.rotation.y = yaw; head.position.set(0, 2.2, 0); head.rotation.y = headYaw; root.add(head);
  head.add(new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.4)));
  const body = new THREE.Mesh(new THREE.BoxGeometry(1, 1.6, belly * 2)); body.position.set(0, 1, 0); root.add(body); // reaches `belly` in front of (and behind) his middle
  if (hidden) { const arm = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, hidden * 2)); arm.position.set(0, 1.4, 0); arm.visible = false; root.add(arm); }
  root.updateMatrixWorld(true);
  return { yaw, ch: { root, head } };
}
const headAt = (a) => a.ch.head.getWorldPosition(new THREE.Vector3());
const yawFwd = (yaw) => new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw));

t('the face looks where the head bone looks: the same as the yaw for a normal actor', () => {
  for (const yaw of [0, 1, -2.5, Math.PI]) {
    const f = new THREE.Vector3();
    assert.ok(faceFwd(actor({ yaw }), f));
    assert.ok(f.distanceTo(yawFwd(yaw)) < 1e-6, `yaw ${yaw}`);
  }
});

t('a clip that turns the head away from the yaw: the face shot follows the head', () => {
  const a = actor({ yaw: 0, headYaw: Math.PI }), f = new THREE.Vector3();
  assert.ok(faceFwd(a, f));
  assert.ok(f.distanceTo(new THREE.Vector3(0, 0, 1)) < 1e-6, 'turned round: it faces +z, not the yaw\'s -z');
});

t('a head looking straight down: no facing from it (the yaw is used instead)', () => {
  const a = actor(); a.ch.head.rotation.x = -Math.PI / 2; a.ch.root.updateMatrixWorld(true);
  assert.equal(faceFwd(a, new THREE.Vector3()), false);
});

t('reach: how far the body sticks out in front of the face; a big belly reaches further; hidden pieces don\'t count', () => {
  const thin = actor({ belly: 0.3 }), big = actor({ belly: 1.4 }), f = yawFwd(0);
  assert.ok(Math.abs(reachOf(thin, headAt(thin), f) - 0.3) < 1e-6);
  assert.ok(Math.abs(reachOf(big, headAt(big), f) - 1.4) < 1e-6);
  const arm = actor({ belly: 0.3, hidden: 2 });
  assert.ok(Math.abs(reachOf(arm, headAt(arm), f) - 0.3) < 1e-6, 'an invisible damage piece doesn\'t push the camera back');
  assert.ok(reachOf(actor({ belly: 9 }), headAt(actor()), f) <= 2.5, 'capped: a close-up stays a close-up');
});

t('the close-up distance (shots.js): normal actors keep 1.3 m; a big one is framed from outside his belly', () => {
  const dist = (a) => { const f = new THREE.Vector3(); faceFwd(a, f); return Math.max(1.3, reachOf(a, headAt(a), f) + 0.5); };
  assert.equal(dist(actor({ belly: 0.3 })), 1.3);
  const big = actor({ belly: 1.4 });
  assert.ok(dist(big) > 1.4, 'the camera is in front of the belly, not inside it');
});

console.log(`${n} ok`);
