// Scary Forest, the client side: everyone has a flashlight (yours lights the woods in front of you, everyone else's is a
// beam you can see through the trees and a bright lens, and the nearest few light the woods too), the radio mast and the
// broken-down car blink, the mast has its guy wires, fireflies hang about, crickets chirp (they stop when HR is close).
// The Tall Guy From HR himself lives in hrguy.js.
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { sfx } from './audio.js';
import { FMATS } from './forestmats.js';
import { updateHR } from './hrguy.js';
import { PH } from '/shared/physics.js';
import { lookDir } from '/shared/hr.js';

let on = false, group = null, mine = null, pool = [], beams = new Map(), flies = null;
const POOL = 3; // other people's flashlights that really light things (a fixed number: adding lights recompiles shaders)
const FL = { color: 0xfff0d2, mine: 9, others: 6, dist: 46, angle: 0.44, pen: 0.55, decay: 1.05 };

function spot(i) {
  const s = new THREE.SpotLight(FL.color, 0, FL.dist, FL.angle, FL.pen, FL.decay);
  s.target = new THREE.Object3D();
  group.add(s, s.target);
  return s;
}
let beamGeo = null, beamMat = null, lensMat = null;
function beam() { // a cone of light from their head the way they look: bright at the lens, gone by 13 m
  if (!beamGeo) {
    const h = 13, g = new THREE.ConeGeometry(2.3, h, 16, 6, true);
    g.translate(0, -h / 2, 0); g.rotateX(Math.PI / 2);
    const p = g.attributes.position, c = [];
    for (let i = 0; i < p.count; i++) { const k = Math.pow(Math.max(0, 1 + p.getZ(i) / h), 2.2); c.push(k, k * 0.94, k * 0.8); }
    g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
    beamGeo = g;
    beamMat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.13, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
    lensMat = new THREE.SpriteMaterial({ color: 0xfff4d8, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  }
  const m = new THREE.Group();
  const cone = new THREE.Mesh(beamGeo, beamMat); cone.renderOrder = 3; m.add(cone);
  const lens = new THREE.Sprite(lensMat); lens.scale.setScalar(0.5); lens.position.z = -0.1; m.add(lens);
  m.rotation.order = 'YXZ';
  group.add(m);
  return m;
}
function fireflies() {
  const n = 70, pos = new Float32Array(n * 3), seed = [];
  for (let i = 0; i < n; i++) { // round the lake shore and the clearing
    const lake = i % 2, x = lake ? 66 + Math.random() * 10 : (Math.random() - 0.5) * 34, z = lake ? -60 + Math.random() * 110 : -10 + (Math.random() - 0.5) * 34;
    seed.push([x, 0.6 + Math.random() * 2.2, z, Math.random() * 6]);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const p = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xd8ff6a, size: 0.16, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false }));
  p.userData.seed = seed; p.frustumCulled = false;
  group.add(p);
  return p;
}
function wires() { // the mast's guy wires, down to anchors in the woods
  const top = [56, 8], mat = new THREE.LineBasicMaterial({ color: 0x3a4048 }), pts = [];
  for (let i = 0; i < 3; i++) {
    const a = 0.6 + (i / 3) * Math.PI * 2, ax = top[0] + Math.cos(a) * 22, az = top[1] + Math.sin(a) * 22;
    for (const y of [24, 44]) for (const s of [-1, 1]) pts.push(new THREE.Vector3(top[0] + s * Math.sin(a), y, top[1] - s * Math.cos(a)), new THREE.Vector3(ax, 0.3, az));
  }
  group.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), mat));
}

// called by world.js whenever the map changes
export function forestMap(map, id) {
  const want = !!(map && map.flashlights);
  if (want === on) return;
  on = want;
  if (group) { G.scene.remove(group); group.traverse((o) => { if (o.geometry && o.geometry !== beamGeo) o.geometry.dispose(); }); group = null; beams.clear(); pool = []; mine = null; flies = null; }
  if (!on) return;
  group = new THREE.Group();
  G.scene.add(group);
  mine = spot(0); mine.userData.mine = true; // lighting.js: yours can cast shadows (Too HD)
  for (let i = 0; i < POOL; i++) pool.push(spot(i + 1));
  flies = fireflies();
  if (id === 'forest') wires();
}

const fwd = new THREE.Vector3(), tmp = new THREE.Vector3();
let blinkT = 0, crickT = 0, owlT = 20, sqT = 8;
export function updateForest(dt) {
  updateHR(dt);
  if (!on) return;
  const now = performance.now(), cam = G.camera;
  // the blinkers: the mast (slow red), the car's hazards, the dying lantern
  if (FMATS.mastlight) FMATS.mastlight.mat.color.setHex(now % 1600 < 520 ? 0xff1a1a : 0x2a0606);
  if (FMATS.hazard2) FMATS.hazard2.mat.color.setHex(now % 900 < 450 ? 0xffa21a : 0x2a1a06);
  if (FMATS.lantern && now > blinkT) { blinkT = now + 60 + Math.random() * 400; FMATS.lantern.mat.color.setHex(Math.random() < 0.2 ? 0x3a2410 : 0xffc46a); }
  // your flashlight: from a bit below and right of your eyes, the way you look
  const alive = G.joined && ME.alive;
  cam.getWorldDirection(fwd);
  mine.intensity = alive ? FL.mine : 0;
  mine.position.copy(cam.position).addScaledVector(fwd, 0.3); mine.position.y -= 0.25;
  mine.target.position.copy(cam.position).addScaledVector(fwd, 12);
  // everyone else's: a beam + lens each, and the nearest few light the woods for real
  const seen = new Set(), near = [];
  for (const [id, r] of G.remotes) {
    if (!r.alive || !r.pos || (r.ch && r.ch.root && !r.ch.root.visible)) continue;
    seen.add(id);
    let b = beams.get(id);
    if (!b) beams.set(id, (b = beam()));
    b.visible = true;
    b.position.set(r.pos[0], r.pos[1] + PH.eye - 0.15, r.pos[2]);
    b.rotation.set(r.pitch || 0, r.yaw || 0, 0);
    b.position.x += -Math.sin(r.yaw || 0) * 0.35; b.position.z += -Math.cos(r.yaw || 0) * 0.35;
    near.push([tmp.set(r.pos[0], r.pos[1], r.pos[2]).distanceTo(cam.position), r, b]);
  }
  for (const [id, b] of beams) if (!seen.has(id)) { b.visible = false; if (!G.remotes.has(id)) { group.remove(b); beams.delete(id); } }
  near.sort((a, c) => a[0] - c[0]);
  pool.forEach((s, i) => {
    const e = near[i];
    if (!e || e[0] > 55) { s.intensity = 0; return; }
    const [, r, b] = e, d = lookDir(r.yaw || 0, r.pitch || 0);
    s.intensity = FL.others; s.position.copy(b.position);
    s.target.position.set(b.position.x + d[0] * 12, b.position.y + d[1] * 12, b.position.z + d[2] * 12);
  });
  // fireflies drift
  if (flies) {
    const a = flies.geometry.attributes.position, t = now / 1000;
    flies.userData.seed.forEach(([x, y, z, ph], i) => a.setXYZ(i, x + Math.sin(t * 0.4 + ph) * 1.2, y + Math.sin(t * 0.9 + ph * 2) * 0.4, z + Math.cos(t * 0.33 + ph) * 1.2));
    a.needsUpdate = true;
    flies.material.opacity = 0.5 + 0.4 * Math.sin(t * 3.1);
  }
  // night noises round you. the crickets go quiet when he's close
  if (!G.joined) return;
  const hr = G.hrState, hrNear = hr && hr.on && hr.p && Math.hypot(hr.p[0] - ME.pos[0], hr.p[2] - ME.pos[2]) < 30;
  const around = (a, b) => { const ang = Math.random() * Math.PI * 2, d = a + Math.random() * (b - a); return [ME.pos[0] + Math.cos(ang) * d, ME.pos[1] + 1, ME.pos[2] + Math.sin(ang) * d]; };
  crickT -= dt; owlT -= dt; sqT -= dt;
  if (crickT <= 0) { crickT = 0.25 + Math.random() * 0.9; if (!hrNear) sfx.cricket(around(6, 22)); }
  if (owlT <= 0) { owlT = 25 + Math.random() * 40; sfx.owl(around(25, 45)); }
  if (sqT <= 0) { sqT = 9 + Math.random() * 10; if (Math.hypot(ME.pos[0] - 56, ME.pos[2] - 8) < 45) sfx.squelch([56, 3, 8]); }
}
