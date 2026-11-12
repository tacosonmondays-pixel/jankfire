// OVERDUE face rig (ART_BIBLE §1 "Faces"): a jaw, two eyes that look at things, two eyelids that blink, two brows and a
// "stretch" that pulls the mouth corners out (the grin wider than the head). Built from code, on any head group.
// buildFace(head, o) -> rig. rig.set('grin'), rig.flap = 0..1 (the babble drives it), rig.look = a world point or null,
// rig.update(dt). Front of a head is -z (like the mannequin).
// held controls (a clip sets them on its stop-motion steps, they hold between): rig.sing = 0..1 more jaw on top of the
// babble's flap (the choir singing), rig.gaze = a world point the eyes stay on, over rig.look (the choir staring at you)
import * as THREE from 'three';
import { jankify } from '../jank.js';

const mats = new Map();
export function skinMat(color, rough = 0.42) { // rubbery: glossy-soft, no flat shading
  const k = color + ':' + rough;
  if (!mats.has(k)) mats.set(k, jankify(new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0 })));
  return mats.get(k);
}
const flat = (color) => skinMat(color, 0.6);
const lerp = (a, b, k) => a + (b - a) * k;

// face poses: lid = how open (1 open, 0 shut, >1 wide), jaw = resting open, st = mouth width, smile = corners up / down,
// by = brow height, bt = brow tilt (+ = angry, inner ends down)
export const FACES = {
  neutral: { lid: 1, jaw: 0, st: 1, smile: 0.2, by: 0, bt: 0 },
  grin: { lid: 0.75, jaw: 0.3, st: 1.85, smile: 1, by: 0.02, bt: -0.12 },
  squint: { lid: 0.32, jaw: 0, st: 0.9, smile: 0, by: -0.012, bt: 0.28 },
  sad: { lid: 0.65, jaw: 0.05, st: 0.85, smile: -0.8, by: 0.01, bt: -0.5 },
  shock: { lid: 1.25, jaw: 0.9, st: 0.75, smile: 0, by: 0.035, bt: -0.1 },
  angry: { lid: 0.62, jaw: 0.1, st: 1.1, smile: -0.6, by: -0.015, bt: 0.55 },
  sleepy: { lid: 0.18, jaw: 0.05, st: 0.9, smile: 0, by: -0.005, bt: -0.1 },
  choir: { lid: 0.66, jaw: 0.04, st: 2.05, smile: 1.15, by: 0.012, bt: 0.5 }, // (the gut choir: stretched into a smile wider than the face, the eyes still sad at their desks; bt + is what draws the inner ends up here)
};

// o: { z: face plane (front, < 0), eyeR, eyeSep, eyeY, iris, pupil, mouthW, mouthY, lip, lipR, teeth: 'needle' | 'tomb' | 'none',
//      skin, brow, browW, inner (mouth inside), glasses, flatFace (normals: painted dot eyes, no lids), rest (a FACES-style
//      pose this face uses for 'neutral': mina's level, narrowed look) }
export function buildFace(head, o = {}) {
  const S = o.s || 1;
  const z = o.z ?? -0.13, er = (o.eyeR ?? 0.045) * S, sep = (o.eyeSep ?? 0.06) * S, ey = o.eyeY ?? 0.17;
  const rig = { face: 'neutral', flap: 0, look: null, cur: { ...(o.rest || FACES.neutral) }, rest: o.rest || null, blinkT: 1 + Math.random() * 3, blink: 0, eyes: [], lids: [], brows: [], t: Math.random() * 10 };
  const root = new THREE.Group(); root.position.set(0, 0, 0); head.add(root); rig.root = root;
  // ---- eyes: a white ball, an iris disc and a pupil, in a pivot that turns to look
  for (const sx of [-1, 1]) {
    const piv = new THREE.Group(); piv.position.set(sx * sep, ey, z + er * 0.35); root.add(piv);
    if (o.flatFace) {
      const dot = new THREE.Mesh(new THREE.SphereGeometry(er * 0.55, 8, 6), flat(o.pupil ?? 0x111111)); dot.scale.z = 0.4; dot.position.z = -er * 0.6; piv.add(dot);
      rig.eyes.push({ piv, ball: dot, sx }); rig.lids.push(null);
    } else {
      const ball = new THREE.Mesh(new THREE.SphereGeometry(er, 14, 10), skinMat(o.white ?? 0xf6f2e8, 0.15)); piv.add(ball);
      const iris = new THREE.Mesh(new THREE.CircleGeometry(er * 0.55, 14), skinMat(o.iris ?? 0x3fbf5a, 0.2)); iris.position.z = -er * 1.0; iris.rotation.y = Math.PI; piv.add(iris);
      const pup = new THREE.Mesh(new THREE.CircleGeometry(er * 0.27, 12), flat(0x0a0a0a)); pup.position.z = -er * 1.01; pup.rotation.y = Math.PI; piv.add(pup);
      const glint = new THREE.Mesh(new THREE.CircleGeometry(er * 0.1, 6), new THREE.MeshBasicMaterial({ color: 0xffffff })); glint.position.set(er * 0.22, er * 0.25, -er * 1.02); glint.rotation.y = Math.PI; piv.add(glint);
      if (o.redRim) { const rim = new THREE.Mesh(new THREE.TorusGeometry(er * 0.98, er * 0.08, 6, 16), flat(0xd0405a)); rim.position.z = -er * 0.2; piv.add(rim); }
      // lids: skin caps a touch bigger than the eye, hinged on its centre (they don't turn with the look)
      const lp = new THREE.Group(); lp.position.copy(piv.position); root.add(lp);
      const lidG = new THREE.SphereGeometry(er * 1.12, 14, 7, 0, Math.PI * 2, 0, Math.PI / 2);
      const top = new THREE.Mesh(lidG, skinMat(o.lidColor ?? o.skin ?? 0xe6b08a)); lp.add(top);
      const bot = new THREE.Mesh(lidG, skinMat(o.lidColor ?? o.skin ?? 0xe6b08a)); bot.rotation.x = Math.PI; lp.add(bot);
      rig.eyes.push({ piv, ball, sx }); rig.lids.push({ top, bot });
    }
    // brows
    if (o.brow !== false) {
      const b = new THREE.Mesh(new THREE.BoxGeometry((o.browW ?? 0.065) * S, 0.018 * S, 0.025), flat(o.brow ?? 0x3a2418));
      b.position.set(sx * sep, ey + er * 1.45, z + er * 0.1); root.add(b); rig.brows.push({ m: b, sx, y0: b.position.y });
    }
  }
  if (o.glasses) { // huge round glasses (auntie): two rings and a bridge
    for (const sx of [-1, 1]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(er * 1.7, er * 0.16, 6, 18), flat(o.glasses)); ring.position.set(sx * sep * 1.05, ey, z - er * 0.6); root.add(ring);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(er * 1.65, 18), new THREE.MeshBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.18, depthWrite: false })); lens.position.copy(ring.position); lens.position.z -= 0.002; lens.rotation.y = Math.PI; root.add(lens); }
    const br = new THREE.Mesh(new THREE.BoxGeometry(sep * 0.5, er * 0.2, er * 0.2), flat(o.glasses)); br.position.set(0, ey + er * 0.3, z - er * 0.6); root.add(br);
  }
  // ---- mouth: a dark inside, an upper lip made of a few segments bent by the smile, the jaw (lower lip + chin) hinged
  // behind it, teeth on the upper lip. the whole mouth group scales out for the stretch
  const mw = (o.mouthW ?? 0.09) * S, my = o.mouthY ?? 0.06, lr = (o.lipR ?? 0.016) * S, mz = (o.mouthZ ?? z) - 0.004;
  const mouth = new THREE.Group(); mouth.position.set(0, my, mz); root.add(mouth); rig.mouth = mouth;
  const inner = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), flat(o.inner ?? 0x3a0a18)); inner.scale.set(mw * 0.5, 0.001, 0.02); inner.position.z = 0.01; mouth.add(inner); rig.inner = inner;
  const lipM = o.lip ? skinMat(o.lip, 0.3) : skinMat(o.skin ?? 0xe6b08a);
  const SEG = 6, segs = [];
  for (let i = 0; i < SEG; i++) { const s = new THREE.Mesh(new THREE.CapsuleGeometry(lr, mw / SEG, 3, 8).rotateZ(Math.PI / 2), lipM); mouth.add(s); segs.push(s); }
  rig.segs = segs;
  const jaw = new THREE.Group(); jaw.position.set(0, lr * 0.5, 0.03); mouth.add(jaw); rig.jaw = jaw;
  const low = []; for (let i = 0; i < SEG - 1; i++) { const s = new THREE.Mesh(new THREE.CapsuleGeometry(lr * 1.1, mw / SEG, 3, 8).rotateZ(Math.PI / 2), lipM); jaw.add(s); low.push(s); }
  rig.low = low;
  if (o.teeth && o.teeth !== 'none') {
    const tm = skinMat(o.teethColor ?? (o.teeth === 'tomb' ? 0xf2e6a0 : 0xfafaf2), 0.25), n = o.teeth === 'tomb' ? 4 : 9;
    for (let i = 0; i < n; i++) {
      const x = (i / (n - 1) - 0.5) * mw * 0.75;
      const t = o.teeth === 'tomb' ? new THREE.Mesh(new THREE.BoxGeometry(mw * 0.13, lr * 2.2, lr), tm) : new THREE.Mesh(new THREE.ConeGeometry(lr * 0.45, lr * 2, 4).rotateX(Math.PI), tm);
      t.position.set(x, -lr * 1.2, 0.004); t.userData.x = x; mouth.add(t); (rig.teeth ||= []).push(t);
    }
  }
  rig.mw = mw; rig.lr = lr;
  rig.set = (f) => { rig.face = FACES[f] ? f : 'neutral'; };
  rig.update = (dt) => update(rig, dt);
  update(rig, 0);
  return rig;
}

const tv = new THREE.Vector3(), hv = new THREE.Vector3(), hq = new THREE.Quaternion();
function update(r, dt) {
  r.t += dt;
  const F = (r.face === 'neutral' && r.rest) || FACES[r.face] || FACES.neutral, c = r.cur, k = dt > 0 ? Math.min(1, dt * 9) : 1;
  for (const key in F) c[key] = lerp(c[key], F[key], k);
  // blinks: every 2-5 s, sometimes a double
  r.blinkT -= dt;
  if (r.blinkT <= 0) { r.blink = 1; r.blinkT = Math.random() < 0.2 ? 0.25 : 2 + Math.random() * 3; }
  r.blink = Math.max(0, r.blink - dt * 7);
  const shut = Math.sin(Math.min(1, r.blink) * Math.PI) > 0.01 ? Math.sin(r.blink * Math.PI) : 0;
  const open = Math.max(0, c.lid * (1 - shut));
  for (const L of r.lids) if (L) { L.top.rotation.x = lerp(-1.5, 0.55, Math.min(1, open)) + Math.max(0, open - 1) * 0.6; L.bot.rotation.x = Math.PI - lerp(-0.6, 0.85, Math.min(1, open)); }
  for (const e of r.eyes) if (!r.lids[0]) e.ball.scale.y = Math.max(0.12, Math.min(1.2, open)); // painted dot eyes squash for blinks
  // eyes look at a world point (eased, clamped), or wander a bit
  for (const e of r.eyes) {
    let yx = Math.sin(r.t * 0.7 + e.sx) * 0.08, yy = Math.sin(r.t * 0.43) * 0.12;
    if (r.gaze || r.look) {
      e.piv.getWorldPosition(hv); tv.copy(r.gaze || r.look).sub(hv);
      e.piv.parent.getWorldQuaternion(hq); tv.applyQuaternion(hq.invert());
      yy = Math.atan2(-tv.x, -tv.z); yx = Math.atan2(tv.y, Math.hypot(tv.x, tv.z));
    }
    e.piv.rotation.y = lerp(e.piv.rotation.y, Math.max(-0.6, Math.min(0.6, yy)), k);
    e.piv.rotation.x = lerp(e.piv.rotation.x, Math.max(-0.4, Math.min(0.4, yx)), k);
  }
  for (const b of r.brows) { b.m.position.y = b.y0 + c.by + r.flap * 0.008; b.m.rotation.z = b.sx * -c.bt * 0.6; }
  // mouth: width (stretch), the bend of the lips, the jaw: resting open + the flap of the babble
  const st = c.st * (1 + r.flap * 0.08), sm = c.smile, jaw = Math.min(1.2, c.jaw + r.flap * 0.85 + (r.sing || 0));
  const n = r.segs.length, w = r.mw * st, curve = (x) => sm * 1.3 * (x / w) * (x / w) * w * 0.55, slope = (x) => sm * 1.3 * 2 * (x / w) * 0.55;
  for (let i = 0; i < n; i++) { // (the lips spread apart for the stretch instead of scaling, so they stay round)
    const x = (i / (n - 1) - 0.5) * w, s = r.segs[i];
    s.position.set(x, curve(x), 0); s.rotation.z = Math.atan(slope(x)); s.scale.x = st;
  }
  r.jaw.rotation.x = -jaw * 0.55;
  for (let i = 0; i < r.low.length; i++) {
    const x = ((i + 0.5) / n - 0.5) * w, s = r.low[i];
    s.position.set(x, curve(x) * 0.8 - r.lr * 1.6 - jaw * 0.02, -0.03); s.rotation.z = Math.atan(slope(x)) * 0.8; s.scale.x = st;
  }
  r.inner.scale.x = r.mw * 0.5 * st;
  r.inner.scale.y = r.lr * 0.6 + jaw * 0.022;
  r.inner.position.y = -jaw * 0.012;
  if (r.teeth) for (const t of r.teeth) { const x = t.userData.x * st; t.position.x = x; t.position.y = curve(x) - r.lr * 1.1; }
}
