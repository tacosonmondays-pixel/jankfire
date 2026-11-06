// The city's crowd: the people standing about at the generators' crowd spots (chunk marks 'crowd', 'enemy.unpaid',
// 'npc.*'), drawn near the camera only (the 40 nearest), animated procedurally on their joint nodes (the Blender
// characters are segmented puppets: hips > spine > chest > neck > head > jaw, arms, legs; s_<id>.glb, make_story_people.py).
// Look only: no collision, no AI. Each one idles (breath, sway, a look round), some wander a few metres and back,
// some talk (the jaw flaps), the stomach-dogs trot about. The sim's real NPCs (WP8) can reuse the same rigs.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const KINDS = { // crowd mark kind -> the characters it can be
  local: ['local_tiedye', 'local_cook', 'local_scooter'], shopper: ['local_tiedye', 'local_cook'], cook: ['local_cook'], scooter: ['local_scooter'],
  lost: ['local_tiedye'], choir: ['local_tiedye'], digester: ['local_cook'], unpaid: ['raider_chair', 'raider_cabinet'], dog: ['stomachdog'],
};
const MAX = 40, RANGE = 70;
const loader = new GLTFLoader();
const tpl = new Map(); // id -> { scene, joints } | 'loading' | null

function template(id, have) {
  if (tpl.has(id)) return tpl.get(id);
  if (!have.has('s_' + id)) { tpl.set(id, null); return null; }
  tpl.set(id, 'loading');
  loader.load('/models/story/s_' + id + '.glb', (g) => {
    g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; if (/_lod1/.test(o.name)) o.visible = false; } });
    tpl.set(id, { scene: g.scene });
  }, undefined, () => tpl.set(id, null));
  return 'loading';
}
const hash = (x, z) => { let h = Math.imul((x * 100) | 0, 73856093) ^ Math.imul((z * 100) | 0, 19349663); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

export class Crowd {
  constructor(scene) {
    this.root = new THREE.Group(); this.root.name = 'crowd'; scene.add(this.root);
    this.live = new Map(); // key -> npc
    this.have = null;
    fetch('/models/story/index.json').then((r) => r.json()).then((l) => { this.have = new Set(l); }).catch(() => { this.have = new Set(); });
    this.t = 0;
  }
  // marks: [{ id, p, kind, face }] round the camera (stream.marks())
  update(marks, cam, dt) {
    this.t += dt;
    if (!this.have) return;
    const want = [];
    for (const m of marks) {
      let kind = null;
      if (m.id === 'crowd') kind = m.kind || 'local';
      else if (m.id === 'enemy.unpaid') kind = 'unpaid';
      else if (m.id && m.id.startsWith('npc.')) kind = 'local';
      if (!kind || !KINDS[kind]) continue;
      const d = Math.hypot(m.p[0] - cam.x, m.p[2] - cam.z);
      if (d < RANGE) want.push([d, m, kind]);
    }
    // the Gut gets stomach-dogs: every third Gut crowd spot has one sniffing about nearby
    for (const [, m, kind] of want.slice()) if ((kind === 'choir' || kind === 'digester') && hash(m.p[0], m.p[2]) < 0.35) want.push([0, { ...m, p: [m.p[0] + 2, m.p[1], m.p[2] + 1.5] }, 'dog']);
    want.sort((a, b) => a[0] - b[0]);
    const keep = new Set();
    for (const [, m, kind] of want.slice(0, MAX)) {
      const key = kind + ':' + m.p[0].toFixed(1) + ':' + m.p[2].toFixed(1);
      keep.add(key);
      if (this.live.has(key)) continue;
      const list = KINDS[kind], h = hash(m.p[0], m.p[2]), id = list[(h * list.length) | 0];
      const t = template(id, this.have);
      if (!t || t === 'loading') continue;
      const obj = t.scene.clone(true), J = {};
      obj.traverse((o) => { if (o.name) J[o.name.replace(/\.\d+$/, '')] = o; });
      for (const o of Object.values(J)) o.userData.rest = o.quaternion.clone();
      obj.position.set(m.p[0], m.p[1], m.p[2]);
      const face = m.face ?? h * 6.283;
      obj.rotation.y = face;
      // a tint for the clothes (materials named *paint*), from the spot's hash
      const tint = new THREE.Color().setHSL(h * 7 % 1, 0.55, 0.62);
      obj.traverse((o) => { if (o.isMesh && o.material && /paint/.test(o.material.name)) { o.material = o.material.clone(); o.material.color.multiply(tint); } });
      this.root.add(obj);
      this.live.set(key, { obj, J, kind, id, home: m.p.slice(), face, ph: h * 100, wander: kind !== 'unpaid' && h > 0.55, talk: h > 0.3 && h < 0.6, dog: kind === 'dog' });
    }
    for (const [key, n] of this.live) if (!keep.has(key)) { n.obj.removeFromParent(); this.live.delete(key); }
    for (const n of this.live.values()) this.animate(n, cam);
  }

  animate(n, cam) {
    const t = this.t + n.ph, J = n.J, q = new THREE.Quaternion(), e = new THREE.Euler();
    const set = (name, x, y, z) => { const o = J[name]; if (!o) return; e.set(x, y, z); o.quaternion.copy(o.userData.rest).multiply(q.setFromEuler(e)); };
    let walk = 0;
    if (n.wander) { // a few metres along their facing and back, with a turn at each end
      const L = 4, cyc = (t * 0.25) % 2, s = cyc < 1 ? cyc : 2 - cyc, dir = cyc < 1 ? 1 : -1;
      const fx = -Math.sin(n.face), fz = -Math.cos(n.face);
      n.obj.position.set(n.home[0] + fx * (s - 0.5) * L, n.home[1], n.home[2] + fz * (s - 0.5) * L);
      n.obj.rotation.y = n.face + (dir < 0 ? Math.PI : 0);
      walk = Math.min(1, Math.min(s, 1 - s) * 8); // slow down into the turns
    }
    if (n.dog) {
      const st = t * 9 * (0.4 + walk), b = Math.abs(Math.sin(st)) * 0.05;
      n.obj.position.y = n.home[1] + b;
      set('legFL', Math.sin(st) * 0.7 * walk, 0, 0); set('legBR', Math.sin(st) * 0.7 * walk, 0, 0);
      set('legFR', -Math.sin(st) * 0.7 * walk, 0, 0); set('legBL', -Math.sin(st) * 0.7 * walk, 0, 0);
      set('tail', 0, Math.sin(t * 11) * 0.6, 0); set('tail2', 0, Math.sin(t * 11 - 1) * 0.7, 0);
      set('head', Math.sin(t * 1.3) * 0.15, Math.sin(t * 0.7) * 0.4, 0); set('jaw', Math.max(0, Math.sin(t * 5)) * 0.35, 0, 0);
      set('body', 0, 0, Math.sin(st) * 0.06);
      return;
    }
    const st = t * 6.2, sw = Math.sin(st) * walk;
    // walk: legs swing, knees bend on the back swing, arms counter-swing, a bob and a hip roll (with the game's jank)
    set('legL', sw * 0.55, 0, 0); set('legR', -sw * 0.55, 0, 0);
    set('shinL', Math.max(0, -Math.sin(st)) * 0.8 * walk, 0, 0); set('shinR', Math.max(0, Math.sin(st)) * 0.8 * walk, 0, 0);
    set('footL', -sw * 0.2, 0, 0); set('footR', sw * 0.2, 0, 0);
    const breathe = Math.sin(t * 1.6) * 0.03, look = Math.sin(t * 0.37) * 0.6 + Math.sin(t * 0.13) * 0.4;
    // idle: breathing, a slow weight shift, looking round (and at you when you're close)
    const toCam = Math.atan2(cam.x - n.obj.position.x, cam.z - n.obj.position.z) - n.obj.rotation.y - Math.PI;
    const close = Math.hypot(cam.x - n.obj.position.x, cam.z - n.obj.position.z) < 6 && !walk;
    let headY = close ? Math.atan2(Math.sin(toCam), Math.cos(toCam)) : look * (1 - walk);
    headY = Math.max(-1.1, Math.min(1.1, headY));
    set('hips', 0, sw * 0.12, Math.sin(t * 0.5) * 0.04 * (1 - walk));
    if (J.hips) J.hips.position.y = (J.hips.userData.y0 ??= J.hips.position.y) + Math.abs(Math.cos(st)) * 0.04 * walk;
    set('spine', breathe + 0.05 * walk, -sw * 0.1, 0);
    set('chest', breathe * 0.6, 0, 0);
    set('head', Math.sin(t * 0.9) * 0.05 + (n.talk ? Math.sin(t * 3) * 0.04 : 0), headY * 0.75, Math.sin(t * 0.4) * 0.05);
    set('neck', 0, headY * 0.25, 0);
    const gesture = n.talk && !walk ? Math.max(0, Math.sin(t * 0.8)) : 0; // talkers wave a hand about
    set('armL', -sw * 0.45, 0, 0); set('foreL', -0.15 - Math.max(0, sw) * 0.3, 0, 0);
    set('armR', sw * 0.45 - gesture * 1.1, 0, -gesture * 0.3); set('foreR', -0.15 - gesture * (0.9 + Math.sin(t * 4) * 0.25), 0, 0);
    set('jaw', n.talk ? Math.max(0, Math.sin(t * 13) * Math.sin(t * 2.1)) * 0.3 : 0, 0, 0);
  }
  dispose() { this.root.removeFromParent(); this.live.clear(); }
}
