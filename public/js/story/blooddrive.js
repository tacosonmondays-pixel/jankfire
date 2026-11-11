// THE BLOOD DRIVE in your hands (OVERDUE only): the Blood Cross as a minigun (docs/story/TRAIN.md §3). Jack's old
// training frame: an arm cradle with six glass syringe barrels in a ring round your forearm, on a washing machine's belt.
// hold fire: the ring winds up (0.8 s), then 14 bolts a second, 2 HP each (free once you carry Jack's marrow).
// the room judges every bolt (server/storytrain.js driveFire: spin-up, rate, range, HP cost, what it hit); this is the
// view model (code-built: the Blender one comes later), the trigger, the tracers and the noise.
// it is the train's weapon: while trainfight.js says so, it replaces whatever you were holding
import * as THREE from 'three';
import { G } from '../ctx.js';
import { K } from '../keys.js';
import { net } from '../net.js';
import { hud } from '../hud.js';
import { fx } from '../fx.js';
import { sfx } from '../audio.js';
import { ME, eye, look } from '../player.js';
import { specVMKit, punchCam } from '../weapons.js';
import { WEAPONS } from '/shared/weapons.js';

const W = WEAPONS.blooddrive, RED = 0xff1f3d;
const r2 = (x) => Math.round(x * 100) / 100, r4 = (x) => Math.round(x * 1e4) / 1e4;

function build() {
  const g = new THREE.Group(), box = (w, h, d, c, x, y, z, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: c, roughness: 0.6, ...o })); m.position.set(x, y, z); g.add(m); return m; };
  const steel = { metalness: 0.75, roughness: 0.35 };
  box(0.085, 0.085, 0.36, 0xe6dccb, 0, 0, 0.02); // your forearm: mannequin plastic
  box(0.1, 0.012, 0.3, 0x6f7680, 0, -0.05, 0.02, steel); box(0.012, 0.07, 0.3, 0x6f7680, -0.052, -0.015, 0.02, steel); // the cradle: scaffold pole, cut down
  for (const z of [-0.1, 0.12]) box(0.112, 0.112, 0.026, 0x2a2a30, 0, 0, z); // seatbelt webbing
  box(0.078, 0.04, 0.1, 0xe6dccb, 0, 0.004, -0.21); // the hand, a finger gun
  box(0.019, 0.019, 0.09, 0xe6dccb, 0.012, 0.014, -0.3); box(0.019, 0.05, 0.019, 0xe6dccb, -0.03, 0.04, -0.2);
  const tip = box(0.022, 0.022, 0.012, RED, 0.012, 0.014, -0.348, { emissive: RED, emissiveIntensity: 1.2 });
  // six glass syringe barrels in a ring, each plumbed to the hand; they fill and empty in turn, so you read your HP off your arm
  const ring = new THREE.Group(), fills = [], glass = new THREE.MeshStandardMaterial({ color: 0xcfefff, transparent: true, opacity: 0.32, roughness: 0.1, metalness: 0.1, depthWrite: false });
  for (let i = 0; i < 6; i++) {
    const a = i * Math.PI / 3, x = Math.cos(a) * 0.082, y = Math.sin(a) * 0.082;
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.017, 0.017, 0.17, 8), glass); b.rotation.x = Math.PI / 2; b.position.set(x, y, 0); ring.add(b);
    const f = new THREE.Mesh(new THREE.CylinderGeometry(0.013, 0.013, 0.16, 6), new THREE.MeshStandardMaterial({ color: RED, emissive: RED, emissiveIntensity: 0.9, roughness: 0.3 })); f.rotation.x = Math.PI / 2; f.position.set(x, y, 0); ring.add(f); fills.push(f);
    const n = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.05, 5), new THREE.MeshStandardMaterial({ color: 0xb8c0c8, ...steel })); n.rotation.x = Math.PI / 2; n.position.set(x, y, -0.11); ring.add(n);
  }
  for (const z of [-0.075, 0.075]) { const h = new THREE.Mesh(new THREE.TorusGeometry(0.082, 0.008, 6, 18), new THREE.MeshStandardMaterial({ color: 0x8a9098, ...steel })); h.position.z = z; ring.add(h); }
  ring.position.z = 0.0; g.add(ring);
  // the belt-drive off a washing machine, slung under the cradle
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.05, 10), new THREE.MeshStandardMaterial({ color: 0xd8d8d0, roughness: 0.5 })); drum.rotation.x = Math.PI / 2; drum.position.set(0.02, -0.105, 0.09); g.add(drum);
  box(0.006, 0.1, 0.012, 0x1c1c1c, 0.05, -0.05, 0.085); box(0.006, 0.1, 0.012, 0x1c1c1c, -0.012, -0.05, 0.085);
  g.position.set(0.21, -0.2, -0.36); g.rotation.set(0.05, 0.1, -0.12);
  g.traverse((o) => { o.frustumCulled = false; });
  return { g, ring, fills, tip, drum };
}

export function makeBloodDrive({ rayEnd, free }) {
  const D = { on: false, held: false, spin: 0, acc: 0, keep: 0, dryT: 0, kick: 0, vm: null, free: () => { try { return !!free(); } catch { return false; } } };
  const tmp = new THREE.Vector3();
  const muzzle = () => { const m = D.vm; m.g.updateWorldMatrix(true, true); m.tip.getWorldPosition(tmp); G.camera.updateMatrixWorld(); G.camera.localToWorld(tmp); return [tmp.x, tmp.y, tmp.z]; }; // (the view model lives in the camera's space)
  function bolt() {
    if (!D.free() && ME.hp - W.cost < 1) { // out of blood to spend: the ring runs dry (the room refuses it too)
      const n = performance.now(); if (n - D.dryT > 450) { D.dryT = n; sfx.bdDry(); hud.msg('THIN BLOOD', 0.6, 'reverse'); }
      return;
    }
    const o = eye(), l = look(), s = 0.006, d = [l[0] + (Math.random() - 0.5) * s, l[1] + (Math.random() - 0.5) * s, l[2] + (Math.random() - 0.5) * s], dl = Math.hypot(d[0], d[1], d[2]), dn = d.map((x) => x / dl);
    net.send({ t: 'fire', w: 'blooddrive', o: o.map(r2), d: dn.map(r4) });
    const h = rayEnd(o, dn, W.range), a = muzzle();
    fx.tracer(a, h.at, RED, 0.045, 0.11);
    if (h.part && h.part !== 'wall') fx.blood(h.at, [-dn[0], -dn[1], -dn[2]], 3, 0);
    else if (h.part === 'wall') fx.sparks(h.at, [-dn[0], 0, -dn[2]], 3);
    sfx.bdBolt(); D.kick = 1; punchCam(0.0035, (Math.random() - 0.5) * 0.004, 0);
  }
  const release = () => { if (D.held) { D.held = false; net.send({ t: 'fire', w: 'blooddrive', k: 'stop' }); } };
  // the window lost you (alt-tab, another tab): the trigger is up
  if (typeof window !== 'undefined') { window.addEventListener('blur', release); document.addEventListener('visibilitychange', () => { if (document.hidden) release(); }); }
  // the fire key is ours while it's in your hands (story main.js asks, once the bag and the wheel have had theirs)
  D.key = (e, down) => {
    if (!D.on || (down && D.safe === false)) return false;
    if (down && K.matches('fire', e)) { if (!D.held) { D.held = true; D.keep = 0; net.send({ t: 'fire', w: 'blooddrive', k: 'spin' }); sfx.bdSpin(); } return true; }
    if (!down && K.up('fire', e)) release();
    return false;
  };
  D.tick = (dt, on, safe = true) => { // safe false: the bag, the wheel or the pause menu is up (the trigger is off)
    D.safe = safe; if (!safe) release();
    if (on !== D.on) { D.on = on; specVMKit.own(!on); if (!on) release(); }
    if (!on) { if (D.vm) D.vm.g.visible = false; D.spin = 0; D.acc = 0; return; }
    if (!D.vm) { D.vm = build(); G.vmScene.add(D.vm.g); }
    const m = D.vm; m.g.visible = true; specVMKit.own(false);
    D.spin = D.held ? Math.min(W.spin, D.spin + dt) : Math.max(0, D.spin - dt * 1.6);
    if (D.held && (D.keep += dt) > 0.4) { D.keep = 0; net.send({ t: 'fire', w: 'blooddrive', k: 'spin' }); } // (the room lets the ring wind down if it hears nothing)
    if (D.held && D.spin >= W.spin && ME.alive) { D.acc = Math.min(3, D.acc + dt * W.rate); while (D.acc >= 1) { D.acc -= 1; bolt(); } } else D.acc = 0;
    const k = D.spin / W.spin; D.kick = Math.max(0, D.kick - dt * 14);
    m.ring.rotation.z -= dt * 34 * k * k; m.drum.rotation.y += dt * 60 * k;
    m.g.position.set(0.21 + (Math.random() - 0.5) * 0.004 * k, -0.2 + (Math.random() - 0.5) * 0.004 * k, -0.36 + D.kick * 0.018);
    m.tip.material.emissiveIntensity = 1 + k * 2.5 + D.kick * 3;
    const hp = D.free() ? 6 : Math.max(0, (ME.hp - 1) / 99) * 6; // the barrels: your blood, a sixth each
    for (let i = 0; i < 6; i++) { const f = Math.max(0.02, Math.min(1, hp - i)); m.fills[i].scale.y = f; m.fills[i].position.z = 0.08 * (1 - f); m.fills[i].visible = f > 0.03; }
  };
  return D;
}
