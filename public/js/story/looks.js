// OVERDUE characters (ART_BIBLE §1): the three kinds of people, built in code on one skeleton that loco.js can walk.
//  · mannequins: the game's jointed mannequin (blank egg head, ball joints, a wrong knee), Corp temps get a painted smile
//  · normals: chunky survivors, 1 : 6 heads, simple faces with one or two modelled features
//  · puppets (the Off-Spec): one huge feature + one tiny one, rubbery skin, a full face rig (face.js)
// buildLook(id) -> { ch, face, look, height, eyeY }. ch has the mannequin's parts (root, body, legL/R, kneeL/R, head, arm,
// armL) so locoPose walks it, plus spine, foreL/R, handL/R for the actor's own gestures. Front is -z, like players.
// (Blender glb heads can replace these later: buildLook keeps the same parts.)
import * as THREE from 'three';
import { jankify } from '../jank.js';
import { buildFace, skinMat } from './face.js';
import { glbLoader } from '../glbkit.js';

const HIP = 0.92;
const g = (x = 0, y = 0, z = 0) => { const o = new THREE.Group(); o.position.set(x, y, z); return o; };
const mesh = (geo, mat, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; return m; };
const sph = (r, mat, x, y, z, sx = 1, sy = 1, sz = 1, seg = 12) => { const m = mesh(new THREE.SphereGeometry(r, seg, Math.max(6, seg * 0.66 | 0)), mat, x, y, z); m.scale.set(sx, sy, sz); return m; };
const cap = (r, len, mat, x, y, z) => mesh(new THREE.CapsuleGeometry(r, len, 4, 10), mat, x, y, z); // vertical
const box = (w, h, d, mat, x, y, z) => mesh(new THREE.BoxGeometry(w, h, d), mat, x, y, z);
const cyl = (r0, r1, h, mat, x, y, z, seg = 12) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), mat, x, y, z);
const flat = (c) => skinMat(c, 0.75);

// ---------------------------------------------------------------- small canvas patterns (ART_BIBLE §2), 64-128 px
const texCache = new Map();
function pattern(key, w, h, draw, rep = [1, 1]) {
  if (texCache.has(key)) return texCache.get(key);
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]);
  t.magFilter = THREE.NearestFilter; texCache.set(key, t); return t;
}
const patMat = (key, w, h, draw, rep, rough = 0.8) => { const k = 'm:' + key; if (!texCache.has(k)) texCache.set(k, jankify(new THREE.MeshStandardMaterial({ map: pattern(key, w, h, draw, rep), roughness: rough }))); return texCache.get(k); };
const speckle = (base, dots, n = 220, sz = 2) => (c, w, h) => { c.fillStyle = base; c.fillRect(0, 0, w, h); let s = 7; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647); for (let i = 0; i < n; i++) { c.fillStyle = dots[i % dots.length]; c.globalAlpha = 0.25 + r() * 0.4; c.fillRect(r() * w, r() * h, sz * (0.5 + r()), sz * (0.5 + r())); } c.globalAlpha = 1; };
const tiedye = (c, w, h) => { const cols = ['#ff4fd8', '#ffe14d', '#4fd8ff', '#7dff4f', '#ff8a3a']; for (let i = 9; i > 0; i--) { c.fillStyle = cols[i % cols.length]; c.beginPath(); for (let a = 0; a <= 64; a++) { const t = (a / 64) * Math.PI * 2, rr = (i / 9) * w * 0.75 * (1 + 0.15 * Math.sin(t * 5 + i)); c.lineTo(w / 2 + Math.cos(t) * rr, h / 2 + Math.sin(t) * rr); } c.fill(); } };
const grid = (bg, line) => (c, w, h) => { c.fillStyle = bg; c.fillRect(0, 0, w, h); c.strokeStyle = line; c.lineWidth = 2; for (let i = 0; i <= w; i += 16) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, h); c.stroke(); c.beginPath(); c.moveTo(0, i); c.lineTo(w, i); c.stroke(); } c.fillStyle = '#c0202a'; c.font = 'bold 9px monospace'; c.fillText('£', 4, 12); c.fillText('%', 36, 44); };
const knit = (base, dark) => (c, w, h) => { c.fillStyle = base; c.fillRect(0, 0, w, h); c.fillStyle = dark; for (let y = 0; y < h; y += 6) for (let x = (y / 6) % 2 ? 3 : 0; x < w; x += 6) c.fillRect(x, y, 3, 3); c.fillStyle = '#ffffff'; for (let x = 0; x < w; x += 16) { c.fillRect(x, 26, 8, 3); c.fillRect(x + 4, 23, 3, 9); } };
const veins = (base) => (c, w, h) => { speckle(base, ['#b8645a', '#d68a7a'], 160)(c, w, h); c.strokeStyle = 'rgba(120,60,150,0.55)'; c.lineWidth = 2.2; for (let i = 0; i < 5; i++) { c.beginPath(); let x = 10 + i * 24, y = 0; c.moveTo(x, y); while (y < h) { y += 10; x += Math.sin(y * 0.3 + i) * 6; c.lineTo(x, y); } c.stroke(); } };

// ---------------------------------------------------------------- the shared skeleton
// o: { skin, joint, legS (leg scale), legCol, shoe, torso (fn), torsoH, shW (shoulder half width), armR, upper, fore, foreS
//      (forearm scale), hand, headR [x, y, z], neck, face {...}, s (root scale), hunch }
function person(o) {
  const skin = o.skinMat || skinMat(o.skin ?? 0xe6b08a), joint = o.jointMat || skin;
  const root = g(), lift = g(), body = g();
  root.add(lift); lift.add(body);
  const ls = o.legS ?? 1;
  lift.position.y = -HIP * (1 - ls) + (o.liftY || 0);
  const legL = g(-(o.hipW ?? 0.1), HIP, 0), legR = g(o.hipW ?? 0.1, HIP, 0), kneeL = g(0, -0.44, 0), kneeR = g(0, -0.44, 0);
  const legM = o.legMat || (o.legCol != null ? flat(o.legCol) : skin), shoeM = flat(o.shoe ?? 0x2a2420);
  for (const [leg, knee] of [[legL, kneeL], [legR, kneeR]]) {
    leg.scale.setScalar(ls);
    leg.add(sph(0.08 * (o.thigh ?? 1), joint, 0, 0, 0));
    leg.add(cap(0.07 * (o.thigh ?? 1), 0.3, legM, 0, -0.22, 0));
    knee.add(sph(0.062, joint, 0, 0, 0));
    knee.add(cap(0.056 * (o.shin ?? 1), 0.3, o.shinMat || legM, 0, -0.2, 0));
    knee.add(box(0.12 * (o.foot ?? 1), 0.07, 0.24 * (o.foot ?? 1), shoeM, 0, -0.42, -0.05));
    leg.add(knee); body.add(leg);
  }
  // pelvis + spine (the torso pivots here for hunches, breaths and bows)
  if (o.pelvis !== false) body.add(sph(0.16, o.pelvisMat || legM, 0, HIP + 0.04, 0, 1.15, 0.7, 0.85));
  if (o.hips) o.hips(body, skin); // (a skirt hangs from the hips, not the hunched spine)
  const spine = g(0, HIP + 0.06, 0); body.add(spine);
  spine.rotation.x = -(o.hunch || 0); // (- = forward)
  const tH = o.torsoH ?? 0.52;
  if (o.torso) o.torso(spine, tH, skin); else spine.add(sph(0.2, skin, 0, tH * 0.55, 0, 1.15, 1.25, 0.75));
  const shY = tH * 0.85, shW = o.shW ?? 0.25;
  // arms: shoulder pivot -> upper arm down -> elbow (fore) -> hand. both hang along -y (rotation.x swings them forward)
  const mkArm = (sx) => {
    const a = g(sx * shW, shY, 0); spine.add(a);
    a.add(sph(0.068 * (o.armR ?? 1), o.sleeveMat || joint, 0, 0, 0));
    a.add(cap(0.05 * (o.armR ?? 1), (o.upper ?? 0.26) - 0.05, o.sleeveMat || skin, 0, -(o.upper ?? 0.26) / 2, 0));
    const f = g(0, -(o.upper ?? 0.26), 0); a.add(f);
    f.add(sph(0.05 * (o.armR ?? 1), joint, 0, 0, 0));
    const fs = o.foreS ?? 1;
    const fm = cap(0.045 * fs, (o.fore ?? 0.24) - 0.04, o.foreMat || skin, 0, -(o.fore ?? 0.24) / 2, 0); fm.scale.set(fs > 1 ? 1 : 1, 1, 1); f.add(fm);
    const hs = o.handS ?? 1;
    const h = g(0, -(o.fore ?? 0.24) - 0.02 * hs, 0); f.add(h);
    h.add(box(0.075 * hs, 0.1 * hs, 0.05 * hs, o.handMat || skin, 0, -0.04 * hs, 0)); // mitt
    h.add(box(0.03 * hs, 0.05 * hs, 0.03 * hs, o.handMat || skin, sx * -0.04 * hs, -0.03 * hs, -0.02 * hs)); // thumb
    a.rotation.z = sx * 0.08;
    return { a, f, h };
  };
  const L = mkArm(-1), R = mkArm(1);
  const neck = g(0, tH + (o.neck ?? 0.08), 0); spine.add(neck);
  if (o.neck !== 0) neck.add(cyl(0.045, 0.05, 0.12, skin, 0, -0.03, 0, 8));
  const head = g(0, 0.02, 0); neck.add(head);
  const hr = o.headR ?? [0.12, 0.17, 0.13];
  const egg = o.headMat || skin;
  if (o.head) o.head(head, hr, egg); else head.add(sph(1, egg, 0, hr[1], 0, hr[0], hr[1], hr[2], 16));
  const face = o.face === false ? null : buildFace(head, { z: -hr[2] * 0.94, skin: o.skin, ...(o.face || {}) });
  root.scale.setScalar(o.s ?? 1.1);
  const ch = { root, lift, body, spine, legL, legR, kneeL, kneeR, head, neck, arm: R.a, armL: L.a, foreL: L.f, foreR: R.f, handL: L.h, handR: R.h,
    slot: g(), pupils: [], jank: { tilt: (Math.random() - 0.5) * 0.3, shoulder: 0, lean: (Math.random() - 0.5) * 0.08, wrongKnee: !!o.wrongKnee } };
  head.rotation.z = o.tilt ?? ch.jank.tilt * 0.5;
  return { ch, face };
}

// ---------------------------------------------------------------- the looks
const LOOKS = {
  // a ☺ CORP temp: the game's mannequin, a painted smile and a lanyard
  mannequin() {
    const SK = 0xe6cba2, JT = 0xbf9f74;
    const p = person({ skin: SK, skinMat: flat(SK), jointMat: flat(JT), legCol: 0x2b3a55, shoe: 0x111111, wrongKnee: Math.random() < 0.5, s: 1.08,
      torso: (sp, tH) => { sp.add(sph(0.2, flat(0xf4f4f0), 0, tH * 0.55, 0, 1.15, 1.25, 0.75)); sp.add(box(0.04, 0.24, 0.02, flat(0x4fd8ff), 0, tH * 0.6, -0.15));
        const badge = box(0.07, 0.09, 0.01, flat(0xffffff), 0.06, tH * 0.42, -0.155); sp.add(badge); },
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0] * 0.92, r[1] * 1.1, r[2])); h.add(box(0.006, r[1] * 1.6, r[2] * 2.1, flat(JT), 0, r[1], 0)); },
      face: { flatFace: true, eyeR: 0.022, pupil: 0x1a1a1a, mouthW: 0.08, lipR: 0.008, lip: 0x1a1a1a, brow: false, eyeY: 0.2, mouthY: 0.1 } });
    p.face.set('grin'); FACE_LOCK.set(p.face, 'grin'); // the smile is painted on. it never changes
    return { ...p, kind: 'mannequin', height: 1.95, eyeY: 1.85 };
  },
  // AUNTIE SPREADSHEET (Agnes Pell, 85): a normal. grid dress, huge glasses, a crayon behind her ear, the old auditor badge
  auntie() {
    const SK = 0xf0c4a0;
    const dress = patMat('grid', 64, 64, grid('#f4f0e0', '#4a6ad0'), [3, 3]);
    const p = person({ skin: SK, legCol: SK, shoe: 0x5a2a3a, s: 0.98, hunch: 0.22, torsoH: 0.48, shW: 0.21, legS: 0.92, foot: 0.9,
      hips: (b) => b.add(cyl(0.2, 0.31, 0.5, dress, 0, HIP - 0.12, 0.02, 14)), // the dress, down past the knees
      torso: (sp, tH, skin) => {
        sp.add(cyl(0.17, 0.2, 0.3, dress, 0, tH * 0.25, 0, 14));
        sp.add(sph(0.19, dress, 0, tH * 0.62, 0, 1.05, 1.15, 0.8));
        sp.add(box(0.11, 0.08, 0.012, flat(0xffffff), 0.08, tH * 0.66, -0.16)); sp.add(box(0.11, 0.02, 0.014, flat(0xff4fd8), 0.08, tH * 0.69, -0.161)); // badge
        sp.add(cyl(0.2, 0.2, 0.05, flat(0x8a3a5a), 0, tH * 0.9, 0, 12)); // a cardigan collar
      },
      sleeveMat: flat(0x8a3a5a),
      headR: [0.13, 0.15, 0.13],
      head: (h, r, m) => {
        h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16));
        h.add(sph(0.1, flat(0xd8d4cc), 0, r[1] * 1.9, 0.04, 1, 0.8, 1)); // the bun
        for (const sx of [-1, 1]) h.add(sph(0.09, flat(0xd8d4cc), sx * 0.09, r[1] * 1.5, 0.03, 0.8, 1, 1));
        h.add(sph(0.032, m, 0, r[1] * 0.85, -r[2] * 1.0, 1, 1.3, 1)); // a nose
        const cr = cyl(0.008, 0.008, 0.14, flat(0xff3030), 0.12, r[1] * 1.2, 0.02, 6); cr.rotation.x = 1.2; cr.rotation.z = 0.3; h.add(cr); // the crayon
        for (const sx of [-1, 1]) h.add(sph(0.03, m, sx * r[0], r[1], 0, 0.5, 1, 0.8)); // ears
      },
      face: { eyeR: 0.03, eyeSep: 0.055, eyeY: 0.16, iris: 0x5a7ad0, glasses: 0x2a1a10, mouthW: 0.07, mouthY: 0.06, lip: 0xc0707a, brow: 0xd8d4cc, browW: 0.05 } });
    return { ...p, kind: 'normal', height: 1.6, eyeY: 1.5 };
  },
  // DALE: fixes the machine. overalls, a cap, a beard, a wrench in his back pocket
  dale() {
    const SK = 0xe8b896, OV = 0x3a5a8a;
    const p = person({ skin: SK, legCol: OV, shoe: 0x4a2a1a, s: 1.06, hunch: 0.1,
      torso: (sp, tH) => { sp.add(sph(0.2, flat(0xd8c8a0), 0, tH * 0.55, 0, 1.2, 1.25, 0.78)); sp.add(box(0.3, 0.3, 0.05, flat(OV), 0, tH * 0.42, -0.13));
        for (const sx of [-1, 1]) sp.add(box(0.04, 0.3, 0.02, flat(OV), sx * 0.1, tH * 0.7, -0.15));
        const w = box(0.04, 0.22, 0.02, flat(0x9aa0aa), 0.1, tH * 0.05, 0.16); w.rotation.z = 0.3; sp.add(w); },
      sleeveMat: flat(0xd8c8a0), headR: [0.12, 0.15, 0.13],
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16));
        h.add(cyl(0.135, 0.135, 0.07, flat(0xc04030), 0, r[1] * 1.75, 0, 14)); const bill = box(0.2, 0.015, 0.12, flat(0xc04030), 0, r[1] * 1.6, -0.15); bill.rotation.x = -0.15; h.add(bill);
        const beard = sph(0.12, flat(0xe8e4dc), 0, r[1] * 0.35, -0.04, 1, 1.1, 0.8); h.add(beard);
        h.add(sph(0.035, m, 0, r[1] * 0.95, -r[2] * 1.02, 1.1, 1, 1.2)); },
      face: { eyeR: 0.028, eyeY: 0.19, iris: 0x6a5030, mouthW: 0.07, mouthY: 0.085, lip: 0xb07060, brow: 0xe8e4dc, browW: 0.06, glasses: 0x666666 } });
    return { ...p, kind: 'normal', height: 1.85, eyeY: 1.78 };
  },
  // LUMPS (puppet): gigantic veiny forearms with gold rings + a small head on a huge body, tiny legs. tie-dye tee
  lumps() {
    const SK = 0xf0a080, skin = patMat('lumpskin', 64, 64, speckle('#f0a080', ['#c86a50', '#ffc0a0']), [2, 2], 0.42);
    const tee = patMat('tiedye', 96, 96, tiedye, [1, 1]);
    const vein = patMat('veins', 128, 64, veins('#f0a080'), [1, 1], 0.4);
    const gold = skinMat(0xffc830, 0.2);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x3a3a50, shoe: 0x202020, legS: 0.5, thigh: 1.5, shin: 1.4, foot: 1.3, s: 1.45, hipW: 0.14,
      torsoH: 0.7, shW: 0.42, armR: 1.3, upper: 0.3, fore: 0.42, foreS: 3.1, handS: 2.4, foreMat: vein, sleeveMat: tee,
      torso: (sp, tH) => { const t = sph(0.38, tee, 0, tH * 0.5, 0, 1.12, 1.0, 0.82, 16); sp.add(t); sp.add(sph(0.2, skin, 0, tH * 0.92, -0.02, 1.3, 0.5, 1)); },
      headR: [0.1, 0.12, 0.105], neck: 0.02,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16));
        const sg = box(0.17, 0.035, 0.022, flat(0x101010), 0, r[1] * 1.95, -0.02); sg.rotation.x = -1.1; h.add(sg); // sunglasses pushed up
        for (const sx of [-1, 1]) h.add(sph(0.025, m, sx * r[0], r[1], 0, 0.6, 1, 1));
        h.add(sph(0.028, m, 0, r[1] * 0.85, -r[2] * 1.05, 1.2, 1, 1.3)); },
      face: { s: 0.75, eyeR: 0.034, eyeSep: 0.048, eyeY: 0.14, iris: 0x58c04a, mouthW: 0.08, mouthY: 0.055, lip: 0xd0607a, teeth: 'tomb', brow: 0x3a2418, lidColor: SK } });
    for (const h of [p.ch.handL, p.ch.handR]) for (let i = 0; i < 3; i++) h.add(cyl(0.03, 0.03, 0.03, gold, (i - 1) * 0.055, -0.17, -0.07, 10)).rotation.x = Math.PI / 2;
    p.ch.foreL.children[1].scale.x = p.ch.foreR.children[1].scale.x = 0.9;
    return { ...p, kind: 'puppet', height: 2.55, eyeY: 2.35 };
  },
  // WEE GORDO (puppet): a huge sagging lipped face on a tiny hunched body. spiky hair, a pink sweater
  gordo() {
    const SK = 0xe8c0d8, skin = patMat('gordoskin', 64, 64, speckle('#e8c0d8', ['#b07898', '#ffd8ec']), [2, 2], 0.45);
    const sweat = patMat('knit', 64, 64, knit('#ff6fc8', '#e040a8'), [2, 1]);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x2a2a3a, shoe: 0x1a1a1a, legS: 0.62, s: 0.95, hunch: 0.42, torsoH: 0.4, shW: 0.17, armR: 0.8, upper: 0.2, fore: 0.18, handS: 0.75, sleeveMat: sweat,
      torso: (sp, tH) => { sp.add(sph(0.16, sweat, 0, tH * 0.5, 0, 1.1, 1.15, 0.9)); sp.add(sph(0.12, sweat, 0, tH * 0.75, 0.06, 1, 0.7, 1)); },
      headR: [0.27, 0.3, 0.25], neck: 0.0,
      head: (h, r, m) => {
        h.add(sph(1, m, 0, r[1] * 0.95, 0, r[0], r[1], r[2], 18));
        const jowl = sph(1, m, 0, r[1] * 0.35, -0.04, r[0] * 0.95, r[1] * 0.55, r[2] * 0.95, 16); h.add(jowl); // the sag
        for (let i = 0; i < 9; i++) { const a = (i / 8 - 0.5) * 2.2, sp = mesh(new THREE.ConeGeometry(0.05, 0.22, 5), flat(0x2a1a3a), Math.sin(a) * 0.2, r[1] * 1.9 + 0.04 - Math.abs(a) * 0.05, 0.03 + (i % 2) * 0.06); sp.rotation.z = -a * 0.55; sp.rotation.x = (i % 2 ? 0.3 : -0.2); h.add(sp); }
        h.add(sph(0.06, m, 0, r[1] * 0.85, -r[2] * 1.0, 1, 1.6, 1.1)); // the long nose
        for (const sx of [-1, 1]) h.add(sph(0.05, m, sx * r[0] * 0.98, r[1] * 0.95, 0, 0.5, 1.2, 0.9));
      },
      face: { s: 1.6, eyeR: 0.04, eyeSep: 0.07, eyeY: 0.36, iris: 0xe8d030, redRim: true, mouthW: 0.13, mouthY: 0.14, mouthZ: -0.235, lip: 0xb04870, lipR: 0.022, teeth: 'needle', brow: 0x2a1a3a, browW: 0.07, lidColor: SK, z: -0.21 } });
    p.face.root.position.z = -0.0;
    return { ...p, kind: 'puppet', height: 1.35, eyeY: 1.3 };
  },  // BIG SAUCE SHARON (puppet): broad, a tiny head, one hand that's a ladle. hairnet over a mohawk, a Big Value banner apron
  sharon() {
    const SK = 0xd8b8f0, skin = patMat('sharonskin', 64, 64, speckle('#d8b8f0', ['#a080c0', '#f0e0ff']), [2, 2], 0.45);
    const apron = patMat('bvbanner', 64, 64, (c, w, h) => { c.fillStyle = '#ffe14d'; c.fillRect(0, 0, w, h); c.fillStyle = '#c04030'; c.fillRect(0, 18, w, 26); c.fillStyle = '#ffe14d'; c.font = 'bold 11px sans-serif'; c.fillText('BIG VAL', 6, 36); }, [1, 1]);
    const steel = skinMat(0xc8ccd4, 0.25);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x2a2a3a, shoe: 0xf4f4f0, s: 1.12, hipW: 0.15, thigh: 1.5, shin: 1.35, foot: 1.2, torsoH: 0.62, shW: 0.36, armR: 1.4, upper: 0.3, fore: 0.28, foreS: 1.6, sleeveMat: flat(0xf4f4f0),
      torso: (sp, tH) => { sp.add(sph(0.34, flat(0xf4f4f0), 0, tH * 0.5, 0, 1.1, 1.05, 0.85, 16)); sp.add(box(0.46, 0.5, 0.04, apron, 0, tH * 0.38, -0.27)); },
      headR: [0.09, 0.11, 0.095], neck: 0.03,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 14));
        for (let i = 0; i < 6; i++) h.add(box(0.025, 0.08, 0.035, flat(0x39ff14), 0, r[1] * 1.85 + 0.02, -0.06 + i * 0.03)); // the mohawk
        h.add(sph(0.11, flat(0xf4f4f0), 0, r[1] * 1.6, 0.01, 1, 0.75, 1.1)); }, // hairnet
      face: { s: 0.7, eyeR: 0.032, eyeSep: 0.045, eyeY: 0.13, iris: 0xd0405a, mouthW: 0.08, mouthY: 0.05, lip: 0x7a3a8a, teeth: 'tomb', brow: 0x2a1a3a, lidColor: SK } });
    const hR = p.ch.handR; for (const c of [...hR.children]) hR.remove(c); // the right hand is a ladle
    hR.add(cyl(0.02, 0.02, 0.3, steel, 0, -0.15, 0, 8)); const bowl = sph(0.11, steel, 0, -0.33, -0.03, 1, 0.55, 1); hR.add(bowl);
    return { ...p, kind: 'puppet', height: 2.1, eyeY: 2.0 };
  },
  // DUMPLING (puppet): a tiny kid with enormous ears, a lanyard on backwards, a shopping basket scooter
  dumpling() {
    const SK = 0xc8e0b0, skin = patMat('dumpskin', 64, 64, speckle('#c8e0b0', ['#90b078', '#e8f8d8']), [2, 2], 0.45);
    const hood = patMat('dumphood', 64, 64, knit('#ff8a3a', '#c05a1a'), [2, 1]);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x3a5a8a, shoe: 0xff4fd8, s: 0.72, legS: 0.8, torsoH: 0.44, shW: 0.19, armR: 0.85, upper: 0.21, fore: 0.19, sleeveMat: hood,
      torso: (sp, tH) => { sp.add(sph(0.18, hood, 0, tH * 0.5, 0, 1.1, 1.15, 0.85)); sp.add(box(0.03, 0.2, 0.01, flat(0x4fd8ff), 0, tH * 0.55, 0.165)); sp.add(box(0.08, 0.1, 0.01, flat(0xffffff), 0, tH * 0.32, 0.17)); }, // lanyard on the back
      headR: [0.15, 0.16, 0.15], neck: 0.03,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16));
        for (const sx of [-1, 1]) { const e = sph(0.16, m, sx * 0.25, r[1] * 1.2, 0.02, 0.35, 1.0, 0.75); e.rotation.z = sx * -0.5; h.add(e); } // the ears
        h.add(sph(0.025, m, 0, r[1] * 0.8, -r[2], 1, 1, 1.2)); },
      face: { s: 1.1, eyeR: 0.04, eyeSep: 0.06, eyeY: 0.18, iris: 0x3fbf5a, mouthW: 0.08, mouthY: 0.07, lip: 0xd0607a, teeth: 'none', brow: 0x3a2418, lidColor: SK } });
    return { ...p, kind: 'puppet', height: 1.25, eyeY: 1.2 };
  },
  // EMPLOYEE OF THE MONTH (normal, a huge raider): office-chair armour, a filing-cabinet chest, plaques of his own face
  eotm() {
    const SK = 0xe8b896, grey = skinMat(0x8a8e96, 0.5), black = flat(0x1a1a1e), gold = skinMat(0xd8a840, 0.3);
    const p = person({ skin: SK, legCol: 0x2a2a30, shoe: 0x101010, s: 1.38, hipW: 0.13, thigh: 1.4, shin: 1.3, foot: 1.3, torsoH: 0.6, shW: 0.34, armR: 1.35, upper: 0.29, fore: 0.27, foreS: 1.5, sleeveMat: black, foreMat: grey,
      torso: (sp, tH) => { sp.add(sph(0.3, black, 0, tH * 0.5, 0, 1.15, 1.1, 0.85, 14)); sp.add(box(0.5, 0.46, 0.3, grey, 0, tH * 0.5, -0.12)); // the cabinet
        for (let i = 0; i < 9; i++) sp.add(box(0.1, 0.12, 0.015, gold, -0.17 + (i % 3) * 0.17, tH * 0.35 + ((i / 3) | 0) * 0.14, -0.275));
        for (const sx of [-1, 1]) { const pad = cyl(0.17, 0.17, 0.06, black, sx * 0.36, tH * 0.92, 0, 10); pad.rotation.z = sx * 0.4; sp.add(pad); } }, // chair seats on the shoulders
      headR: [0.12, 0.14, 0.13], neck: 0.06,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 14)); h.add(box(0.3, 0.05, 0.3, grey, 0, r[1] * 1.85, 0)); }, // photocopier lid hat
      face: { eyeR: 0.028, eyeY: 0.16, iris: 0x6a5030, mouthW: 0.08, mouthY: 0.07, lip: 0xb07060, brow: 0x2a1a10, browW: 0.07 } });
    return { ...p, kind: 'normal', height: 2.55, eyeY: 2.42 };
  },
  // SISTER AGENDA (puppet): a Choir robe, a face stretched into a permanent smile, a Filofax grown into her hand
  sister_agenda() {
    const SK = 0xf6e08a, robe = patMat('choirrobe', 64, 64, speckle('#5a2a7a', ['#4a1a6a', '#6a3a8a']), [2, 2], 0.8);
    const p = person({ skin: SK, skinMat: patMat('agendaskin', 64, 64, speckle('#f6e08a', ['#c8a860', '#fff0b0']), [2, 2], 0.4), legCol: 0x5a2a7a, legMat: robe, shoe: 0x1a1a1a, s: 1.05, hunch: 0.08, torsoH: 0.55, shW: 0.22, sleeveMat: robe,
      hips: (b) => b.add(cyl(0.22, 0.34, 0.86, robe, 0, HIP - 0.42, 0, 14)),
      torso: (sp, tH) => { sp.add(sph(0.2, robe, 0, tH * 0.55, 0, 1.1, 1.3, 0.8)); sp.add(cyl(0.16, 0.22, 0.08, flat(0xf4f4f0), 0, tH * 0.92, 0, 12)); }, // the choir collar
      headR: [0.14, 0.17, 0.14], neck: 0.05,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16)); h.add(sph(1, robe, 0, r[1] * 1.15, 0.03, r[0] * 1.15, r[1] * 1.05, r[2] * 1.15, 14)); }, // the hood
      face: { s: 1.2, eyeR: 0.034, eyeSep: 0.06, eyeY: 0.2, iris: 0x5a7ad0, mouthW: 0.16, mouthY: 0.08, lip: 0xd0607a, teeth: 'tomb', brow: 0x8a6a30, lidColor: SK } });
    p.face.set('grin'); FACE_LOCK.set(p.face, 'grin'); // the smile's stuck. she talks through it
    p.ch.handL.add(box(0.14, 0.18, 0.05, flat(0x8a3a2a), 0, -0.09, -0.03)); // the Filofax
    return { ...p, kind: 'puppet', height: 1.9, eyeY: 1.82 };
  },
  // DOT (puppet): small and round, Lumps-ish forearms, grown into the pink wall up to her chest. curlers, a soup ladle
  dot() {
    const SK = 0xffc8a0, skin = patMat('dotskin', 64, 64, speckle('#ffc8a0', ['#d08a6a', '#ffe0c8']), [2, 2], 0.42);
    const wall = patMat('pinkwall', 64, 64, speckle('#e06aa0', ['#b04878', '#ff9ac8']), [3, 3], 0.6), steel = skinMat(0xc8ccd4, 0.25);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x8a3a5a, shoe: 0x1a1a1a, s: 0.95, legS: 0.6, torsoH: 0.46, shW: 0.27, armR: 1.1, upper: 0.24, fore: 0.3, foreS: 2.0, handS: 1.6, sleeveMat: flat(0x4fd8ff),
      hips: (b) => b.add(sph(0.6, wall, 0, HIP - 0.2, 0.05, 1.1, 0.85, 1.0, 16)), // the wall, up to her chest
      torso: (sp, tH) => sp.add(sph(0.26, flat(0x4fd8ff), 0, tH * 0.5, 0, 1.15, 1.05, 0.9, 14)),
      headR: [0.13, 0.14, 0.13], neck: 0.03,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16));
        for (let i = 0; i < 6; i++) { const c = cyl(0.03, 0.03, 0.08, flat([0xff4fd8, 0xffe14d, 0x4fd8ff][i % 3]), -0.1 + (i % 3) * 0.1, r[1] * 1.7 + ((i / 3) | 0) * 0.02, -0.03 + ((i / 3) | 0) * 0.08, 8); c.rotation.z = Math.PI / 2; h.add(c); } },
      face: { eyeR: 0.032, eyeSep: 0.055, eyeY: 0.16, iris: 0x6a5030, mouthW: 0.08, mouthY: 0.06, lip: 0xc0505a, teeth: 'tomb', brow: 0x6a4a3a, lidColor: SK } });
    p.ch.handR.add(cyl(0.015, 0.015, 0.25, steel, 0, -0.14, 0, 8)); p.ch.handR.add(sph(0.06, steel, 0, -0.28, -0.02, 1, 0.55, 1));
    return { ...p, kind: 'puppet', height: 1.5, eyeY: 1.45 };
  },
  // BEV (puppet): a four-armed surgeon. butcher's apron, a headlamp, magnifier lenses on a hinge, a cigarette behind each ear
  bev() {
    const SK = 0xb8c8e0, skin = patMat('bevskin', 64, 64, speckle('#b8c8e0', ['#8a9ab8', '#dce8f8']), [2, 2], 0.42);
    const apron = patMat('bevapron', 64, 64, speckle('#f4f0e8', ['#c04030', '#8a2a20'], 60, 4), [1, 1], 0.7);
    const p = person({ skin: SK, skinMat: skin, legCol: 0x3a5a5a, shoe: 0xf4f4f0, s: 1.05, hunch: 0.18, torsoH: 0.58, shW: 0.24, sleeveMat: flat(0x6aa8a0),
      torso: (sp, tH) => { sp.add(sph(0.22, flat(0x6aa8a0), 0, tH * 0.55, 0, 1.1, 1.25, 0.8)); sp.add(box(0.36, 0.66, 0.03, apron, 0, tH * 0.28, -0.17));
        for (const sx of [-1, 1]) { const a = g(sx * 0.2, tH * 0.5, -0.04); a.rotation.set(-0.9, 0, sx * 0.2); a.add(cap(0.04, 0.2, skin, 0, -0.14, 0)); const f = g(0, -0.26, 0); f.rotation.x = -0.9; f.add(cap(0.036, 0.18, skin, 0, -0.1, 0)); f.add(box(0.06, 0.08, 0.04, skin, 0, -0.22, 0)); a.add(f); sp.add(a); } }, // the busy pair
      headR: [0.12, 0.15, 0.13], neck: 0.07,
      head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16)); h.add(sph(0.13, flat(0x2a2a3a), 0, r[1] * 1.6, 0.05, 1, 0.65, 1.0));
        h.add(cyl(0.128, 0.128, 0.03, flat(0x2a2a2a), 0, r[1] * 1.55, 0, 14)); const lamp = cyl(0.03, 0.03, 0.03, flat(0xfff6c0), 0, r[1] * 1.6, -0.13, 10); lamp.rotation.x = Math.PI / 2; h.add(lamp); // headlamp
        for (const sx of [-1, 1]) { const c = cyl(0.008, 0.008, 0.08, flat(0xf4f4f0), sx * 0.125, r[1] * 1.15, 0.0, 6); c.rotation.x = 1.4; h.add(c); } },
      face: { eyeR: 0.03, eyeY: 0.17, iris: 0xd0405a, mouthW: 0.07, mouthY: 0.075, lip: 0x7a5a8a, brow: 0x2a2a3a, browW: 0.06, glasses: 0x444444 } });
    return { ...p, kind: 'puppet', height: 1.85, eyeY: 1.78 };
  },
};
// everyone else in the script gets a seeded look from their cast entry (body: mannequin / normal / puppet) until they
// get a hand-made one: skin, clothes and pattern from the palette; puppets pick one huge + one tiny feature, and the
// cast bible's description nudges which (forearms, head, nose, hands, legs, eyes)
const SKINS = [0xf0a080, 0xe8c0d8, 0xc8e0b0, 0xf6e08a, 0xffc8a0, 0xb8c8e0, 0xd8b8f0, 0xe8b896, 0x9a6a50];
const CLOTH = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff8a3a, 0x8a3a5a, 0x3a5a8a, 0x2a2a3a, 0xf4f4f0, 0xc04030];
function generic(id, hint = {}) {
  let sd = 7; for (const ch of id) sd = (sd * 31 + ch.charCodeAt(0)) >>> 0;
  const r = () => ((sd = (sd * 16807) % 2147483647) / 2147483647), pick = (a) => a[Math.floor(r() * a.length)];
  const body = hint.body || 'normal', desc = (hint.desc || '').toLowerCase();
  if (body === 'mannequin' || body === 'cyborg') return LOOKS.mannequin();
  const SK = pick(SKINS), top = pick(CLOTH), leg = pick([0x2a2a3a, 0x3a5a8a, 0x5a3a2a, 0x3a3a50, top]);
  const topM = r() < 0.5 ? patMat('k' + top, 64, 64, knit('#' + top.toString(16).padStart(6, '0'), '#000000'), [2, 1]) : flat(top);
  if (body !== 'puppet') {
    const p = person({ skin: SK, legCol: leg, shoe: pick([0x2a2420, 0x5a2a3a, 0x111111]), s: 0.95 + r() * 0.15, hunch: r() * 0.15, sleeveMat: topM,
      torso: (sp, tH) => sp.add(sph(0.2, topM, 0, tH * 0.55, 0, 1.15, 1.2, 0.78)), headR: [0.12, 0.15, 0.13],
      head: (h, rr, m) => { h.add(sph(1, m, 0, rr[1], 0, rr[0], rr[1], rr[2], 14)); h.add(sph(0.03, m, 0, rr[1] * 0.9, -rr[2], 1, 1.2, 1.1));
        if (r() < 0.7) h.add(sph(0.13, flat(pick([0x1a1a1a, 0xd8d4cc, 0x8a4a2a, 0xffe14d, 0xff4fd8])), 0, rr[1] * 1.5, 0.03, 1.05, 0.7, 1.05)); },
      face: { eyeR: 0.028, eyeY: 0.17, iris: pick([0x3fbf5a, 0x5a7ad0, 0x6a5030]), mouthW: 0.07, mouthY: 0.07, lip: 0xc0707a, glasses: r() < 0.25 ? 0x222222 : undefined } });
    return { ...p, kind: 'normal', height: 1.8, eyeY: 1.72 };
  }
  // puppets: one huge, one tiny (ART_BIBLE §1)
  const want = ['forearm', 'head', 'face', 'nose', 'hand', 'leg', 'eye'].filter((w) => desc.includes(w));
  const huge = want[0] || pick(['head', 'forearm', 'nose', 'hand']), tiny = pick(['leg', 'head', 'hand'].filter((t) => t !== huge));
  const bigHead = huge === 'head' || huge === 'face', tinyHead = tiny === 'head';
  const hr = bigHead ? [0.25, 0.28, 0.24] : tinyHead ? [0.09, 0.11, 0.1] : [0.13, 0.16, 0.14];
  const skin = patMat('sk' + SK, 64, 64, speckle('#' + SK.toString(16).padStart(6, '0'), ['#a06a60', '#ffffff']), [2, 2], 0.42);
  const p = person({ skin: SK, skinMat: skin, legCol: leg, shoe: 0x1a1a1a, s: 0.9 + r() * 0.5, legS: tiny === 'leg' ? 0.55 : 0.9, hunch: r() * 0.3,
    foreS: huge === 'forearm' ? 2.6 : 1, handS: huge === 'hand' ? 2.4 : tiny === 'hand' ? 0.6 : 1, armR: huge === 'forearm' ? 1.2 : 1, fore: huge === 'forearm' ? 0.38 : 0.24, sleeveMat: topM,
    torso: (sp, tH) => sp.add(sph(huge === 'forearm' ? 0.3 : 0.2, topM, 0, tH * 0.55, 0, 1.15, 1.2, 0.8)), headR: hr, neck: bigHead ? 0 : 0.06,
    head: (h, rr, m) => { h.add(sph(1, m, 0, rr[1], 0, rr[0], rr[1], rr[2], 16)); const ns = huge === 'nose' ? 2.6 : 1; h.add(sph(0.035 * ns, m, 0, rr[1] * 0.85, -rr[2] * 1.02 - 0.02 * ns, 1, 1.3, 1.6));
      if (r() < 0.6) for (let i = 0; i < 7; i++) { const a = (i / 6 - 0.5) * 2, sp = mesh(new THREE.ConeGeometry(0.04, 0.16, 5), flat(pick([0x2a1a3a, 0xffe14d, 0x7dff4f])), Math.sin(a) * rr[0] * 0.7, rr[1] * 1.95, 0.02); sp.rotation.z = -a * 0.6; h.add(sp); } },
    face: { s: bigHead ? 1.5 : tinyHead ? 0.7 : 1, eyeR: huge === 'eye' ? 0.06 : 0.038, eyeY: hr[1] * 1.15, iris: pick([0xe8d030, 0x3fbf5a, 0xd0405a]), redRim: r() < 0.4, mouthW: 0.1, mouthY: hr[1] * 0.45,
      lip: pick([0xb04870, 0xd0607a, 0x7a3a8a]), teeth: pick(['needle', 'tomb', 'none']), brow: 0x2a1a3a, lidColor: SK, z: -hr[2] * 0.94 } });
  return { ...p, kind: 'puppet', height: 1.9, eyeY: 1.8 };
}
const FACE_LOCK = new WeakMap();
export const faceLocked = (face) => FACE_LOCK.get(face);
export const LOOK_IDS = Object.keys(LOOKS);

// ---------------------------------------------------------------- Blender cast models (tools/blender/cast/)
// public/models/cast/c_<id>.glb: the body as part_<joint> meshes modelled in root space at the rest pose. each one
// goes into that joint of the code skeleton (so loco.js walks it and the gestures pose it) and the joint's code meshes
// go. the code face rig stays on the head. no file (or not loaded yet) = the code puppet
const CAST = new Map();
export async function loadCast(ids, ms = 15000) {
  const L = glbLoader();
  await Promise.race([Promise.all(ids.map((id) => L.loadAsync(`/models/cast/c_${id}.glb`).then((g) => { prepCast(g.scene); CAST.set(id, g.scene); }).catch(() => {}))), new Promise((r) => setTimeout(r, ms))]);
  return [...CAST.keys()];
}
function prepCast(scene) {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true; o.receiveShadow = true; o.geometry.userData.shared = true;
    for (const m of [].concat(o.material)) { if (m.map) { m.map.magFilter = THREE.NearestFilter; m.map.colorSpace = THREE.SRGBColorSpace; } jankify(m); }
  });
}
export const castLoaded = (id) => CAST.has(id);
export function buildLookCode(id, hint) { const c = CAST.get(id); CAST.delete(id); try { return buildLook(id, hint); } finally { if (c) CAST.set(id, c); } } // (the code puppet, for side-by-sides)
function dressCast(L, scene) {
  const ch = L.ch, s = ch.root.scale.x;
  const tilt = ch.head.rotation.z; ch.head.rotation.z = 0; // (parts are modelled untilted; the jank tilt comes back after, for the head and its face together)
  ch.root.scale.setScalar(1); ch.root.position.set(0, 0, 0); ch.root.rotation.set(0, 0, 0); ch.root.updateMatrixWorld(true);
  const keep = L.face ? L.face.root : null, inv = new THREE.Matrix4();
  scene.updateMatrixWorld(true);
  let n = 0;
  scene.traverse((o) => {
    if (!o.isMesh) return;
    let p = o; while (p && !/^part_[A-Za-z]+/.test(p.name)) p = p.parent; // (a part with several materials is a group of meshes)
    const m0 = p && /^part_([A-Za-z]+)/.exec(p.name);
    if (!m0) return;
    const G = ch[m0[1]];
    if (!G) return;
    if (!G.userData.dressed) { for (const c of [...G.children]) if (c.isMesh && c !== keep) G.remove(c); G.userData.dressed = true; }
    const m = o.clone(); m.matrix.copy(o.matrixWorld); m.matrix.decompose(m.position, m.quaternion, m.scale);
    inv.copy(G.matrixWorld).invert(); m.applyMatrix4(inv);
    G.add(m); n++;
  });
  ch.head.rotation.z = tilt; ch.root.scale.setScalar(s); ch.root.updateMatrixWorld(true);
  L.blender = n > 0;
}

// hint: { body, desc } from the cast bible, for characters without a hand-made look yet
export function buildLook(id, hint) {
  const L = LOOKS[id] ? LOOKS[id]() : hint ? generic(String(id || 'x'), hint) : LOOKS.mannequin();
  L.look = LOOKS[id] ? id : hint ? 'generic' : 'mannequin';
  if (CAST.has(L.look)) dressCast(L, CAST.get(L.look));
  L.ch.root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
  return L;
}
