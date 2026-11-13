// The zombies lobby's people as Blender characters (x_lobby_deb / _gus / _marge.glb, tools/blender/lobby/make_lobby_npcs.py):
// one skinned mesh each with its clips baked in. This plays them: idle loops, talk while they speak, their gesture on cue
// (Deb stamps, Gus spins the revolver, Marge ticks her clipboard), the head (and a bit of the body) turns to whoever
// walks up, and one dark ink hull outlines them (Potato skips it). Visual only: the scene keeps its spots and pickers.
import * as THREE from 'three';
import { clone as skClone } from 'three/addons/utils/SkeletonUtils.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { AUTHORED } from '../glbkit.js';

const INK = 0x120818; // (the UI's near-black purple, like the mechs' ink)
const INK_VS = `#include <common>
#include <skinning_pars_vertex>
uniform float uThick; void main() {
  #include <beginnormal_vertex>
  #include <skinbase_vertex>
  #include <skinnormal_vertex>
  #include <begin_vertex>
  #include <skinning_vertex>
  vec4 mv = modelViewMatrix * vec4(transformed, 1.0);
  float k = uThick * clamp(-mv.z * 0.22, 1.0, 3.5); // (thicker far away: through the CRT blur it stays a line)
  gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed + normalize(objectNormal) * k, 1.0); }`;
const INK_FS = 'uniform vec3 uColor; void main() { gl_FragColor = vec4(uColor, 1.0); }';
const HULL = new WeakMap(); // source geometry -> its smooth hull (welded so the ink has no cracks), shared by every copy
function hullOf(g) {
  if (HULL.has(g)) return HULL.get(g);
  const h = new THREE.BufferGeometry();
  for (const k of ['position', 'skinIndex', 'skinWeight']) if (g.attributes[k]) h.setAttribute(k, g.attributes[k]);
  h.setIndex(g.index);
  const w = mergeVertices(h, 2e-3); w.computeVertexNormals(); w.userData.shared = true;
  HULL.set(g, w);
  return w;
}
const _v = new THREE.Vector3(), _w = new THREE.Vector3(), _q = new THREE.Quaternion(), _e = new THREE.Euler(0, 0, 0, 'YXZ'), _m = new THREE.Matrix4();
const ang = (a) => Math.atan2(Math.sin(a), Math.cos(a));

// a fresh copy of a loaded npc model, or null. keep(x) registers what the scene should dispose (its ink material)
export function npcRig(id, keep, inkOn) {
  const a = AUTHORED[id];
  if (!a || !a.meta || a.meta.kind !== 'npc') return null;
  const src = a.scene, root = skClone(src), meta = a.meta;
  let skin = null;
  root.traverse((o) => { if (o.isSkinnedMesh) { skin = skin || o; o.frustumCulled = false; o.castShadow = true; o.receiveShadow = true; } });
  if (!skin) return null;
  const clips = {}; for (const c of src.animations || []) clips[c.name] = c;
  if (!clips.idle) return null;
  const mixer = new THREE.AnimationMixer(root), act = {};
  for (const [n, c] of Object.entries(clips)) {
    const x = mixer.clipAction(c); x.enabled = true; x.setEffectiveWeight(0);
    if (n === 'gesture') { x.setLoop(THREE.LoopOnce, 1); x.clampWhenFinished = true; }
    act[n] = x;
  }
  act.idle.setEffectiveWeight(1).play(); act.idle.time = Math.random() * clips.idle.duration; // (the three don't breathe in step)
  // the ink: one skinned hull on the same skeleton
  const inkMat = keep(new THREE.ShaderMaterial({ uniforms: { uThick: { value: 0.014 }, uColor: { value: new THREE.Color(INK) } }, vertexShader: INK_VS, fragmentShader: INK_FS, side: THREE.BackSide }));
  const ink = new THREE.SkinnedMesh(hullOf(skin.geometry), inkMat); ink.name = 'ink'; ink.frustumCulled = false; ink.userData.noWrap = true;
  ink.position.copy(skin.position); ink.quaternion.copy(skin.quaternion); ink.scale.copy(skin.scale);
  ink.bind(skin.skeleton, skin.bindMatrix); skin.parent.add(ink);
  const bone = (n) => root.getObjectByName(n);
  const R = {
    root, meta, mixer, act, ink, head: bone('head'), neck: bone('neck'), chest: bone('chest'),
    want: 'idle', fade: 0.3, gestT: 0, talkT: 0, look: { y: 0, x: 0, body: 0 },
    baseYaw: 0,
    // talk for a while (a speech bubble's worth), then back to idle
    talk(sec = 2.4) { if (!act.talk) return; this.talkT = sec; if (this.want !== 'gesture') this.to('talk', 0.2); },
    gesture() {
      if (!act.gesture) return false;
      act.gesture.reset().play(); this.gestT = clips.gesture.duration; this.to('gesture', 0.15);
      return true;
    },
    busy() { return this.want === 'gesture'; },
    to(n, fade) { this.want = n; this.fade = fade; if (!act[n].isRunning()) act[n].play(); },
    // dt; at = the world point they look at (or null), inkOn = draw the outline
    update(dt, at) {
      if (this.gestT > 0) { this.gestT -= dt; if (this.gestT <= 0.3 && this.want === 'gesture') this.to(this.talkT > 0 ? 'talk' : 'idle', 0.3); }
      if (this.talkT > 0) { this.talkT -= dt; if (this.talkT <= 0 && this.want === 'talk') this.to('idle', 0.4); }
      for (const [n, x] of Object.entries(act)) { // (weights slide to the clip we want: a cross-fade without time warping)
        const tgt = n === this.want ? 1 : 0, cur = x.getEffectiveWeight();
        const nw = cur + Math.sign(tgt - cur) * Math.min(Math.abs(tgt - cur), dt / Math.max(0.05, this.fade));
        x.setEffectiveWeight(nw);
        if (nw <= 0 && n !== 'idle' && x.isRunning()) x.stop();
      }
      const t0 = {}; for (const [n, x] of Object.entries(act)) t0[n] = x.time;
      mixer.update(dt);
      for (const [n, x] of Object.entries(act)) { // (the clips' cues: the stamp's thump, the spin, the tick, the gum's pop)
        const ms = meta.clips && meta.clips[n] && Array.isArray(meta.clips[n].marks) ? meta.clips[n].marks : null;
        if (!ms || !ms.length || !x.isRunning() || x.getEffectiveWeight() < 0.5 || !this.onMark) continue;
        const a = t0[n], b = x.time, wrap = b < a; // (a loop came round)
        for (const [mt, name] of ms) if (Number.isFinite(mt) && (wrap ? (mt > a || mt <= b) : (mt > a && mt <= b))) this.onMark(name);
      }
      // look at them: the body turns a little (inside meta.look.body), the head does the rest (meta.look.head)
      const L = meta.look || {}, bodyMax = L.body ?? 0.3, headMax = L.head ?? 0.8;
      let yaw = 0, pitch = 0;
      if (at && this.head) {
        this.head.getWorldPosition(_v); _w.copy(at).sub(_v);
        const d = Math.hypot(_w.x, _w.z), worldYaw = Math.atan2(-_w.x, -_w.z); // (they face -z at yaw 0)
        const rel = ang(worldYaw - this.baseYaw);
        yaw = Math.max(-bodyMax - headMax, Math.min(bodyMax + headMax, rel));
        pitch = Math.max(-0.35, Math.min(0.3, Math.atan2(_w.y, d) * 0.8));
      }
      const k = Math.min(1, dt * 4);
      const by = Math.max(-bodyMax, Math.min(bodyMax, yaw * 0.45));
      this.look.body += (by - this.look.body) * k; this.look.y += (yaw - this.look.body - this.look.y) * k; this.look.x += (pitch - this.look.x) * k;
      root.rotation.y = this.look.body; // (the scene's holder carries baseYaw)
      if (this.head) { _e.set(this.look.x, Math.max(-headMax, Math.min(headMax, this.look.y)), 0); _q.setFromEuler(_e); this.head.quaternion.premultiply(_q); }
      ink.visible = !!inkOn();
    },
    dispose() { mixer.stopAllAction(); mixer.uncacheRoot(root); },
  };
  return R;
}
