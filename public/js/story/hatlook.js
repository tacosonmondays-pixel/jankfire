// MADAM CHAIR and her hat OVERSIGHT (working id hat_lord; docs/story/cast/HAT_LORD.md): her skeleton and code puppet.
// looks.js registers this as LOOKS.hat_lord (it hands over its own kit, so this file imports nothing from it).
// The Blender model (public/models/cast/c_hat_lord.glb, tools/blender/cast/make_cast_hat_lord.py) is built on these
// joints and replaces every group marked codeOnly; the markers stay for both.
// She is the cast skeleton (person()) plus joints of her own: the hat creature on its telescoping neck, its brim in
// six pieces, the crown that lifts off the band (the band is a mouth), three growth clusters, HER eye pair with a lid
// each, a lid for each of the creature's five eyes, the two hands of fingers laced over where her eyes would be, and
// two-jointed fingers. EXTRA is the one list of them; the Blender build and the clips read it from joints.json.
// Her clips and the hat's life are in hatlord.js (HL).
import { FACES } from './face.js';
import { hlRegister } from './hatlord.js';

FACES.chair = { lid: 1, jaw: 0, st: 0.92, smile: 0.3, by: 0, bt: 0 }; // the resting face: pleasant, shut
FACES.chair_host = { lid: 1, jaw: 0.04, st: 1.08, smile: 0.62, by: 0, bt: 0 }; // offering you something
FACES.chair_flat = { lid: 1, jaw: 0, st: 0.82, smile: -0.05, by: 0, bt: 0 }; // "not carried."
FACES.chair_hurt = { lid: 1, jaw: 0.3, st: 0.8, smile: -0.5, by: 0, bt: 0 };

// her body is narrow (shoulders 0.4 m); the 1.46 m bar is the yoke of her cape. 2.95 m to the top of her head, and the
// head is long: 0.62 m, most of it under the hat
export const HATLORD = { s: 1, legS: 1.63, hipW: 0.075, torsoH: 0.659, shW: 0.2, upper: 0.4, fore: 0.38, headR: [0.165, 0.31, 0.17], neck: 0.091 };

// [name, parent, x, y, z, rx, ry, rz]: where the joint sits in its parent's frame (unit scale) and its rest turn
// (three.js XYZ euler, radians). front is -z, +x is HER right. the hat's low end and its feeler are on her right.
const EYE = [0, 0.17, -0.545]; // her pair, crown frame (+- 0.058 in x)
export const EXTRA = [
  ['bandR', 'head', 0.16, 0.42, -0.02, 0, 0, 0], ['bandL', 'head', -0.16, 0.42, -0.02, 0, 0, 0], // the hat's fingers over her eyes: hinged at each temple
  ['hatNeck', 'head', 0, 0.5, 0.04, 0, 0, 0], ['hatNeckB', 'hatNeck', 0, 0, 0, 0, 0, 0], // the neck telescopes: B rides out of the first tube, the hat out of B
  ['hat', 'hatNeckB', 0, 0.12, -0.04, -0.24, 0, -0.245], // tipped forward and down to her right, as drawn
  ['crown', 'hat', 0, 0.05, 0.27, 0, 0, 0], // hinged at the back of the band: + x opens the mouth
  ['brimR', 'hat', 0.34, 0.02, 0, 0, 0, -0.08], ['brimRb', 'brimR', 0.5, 0, 0, 0, 0, -0.3], ['feeler', 'brimRb', 0.42, 0.0, 0, 0, 0, 0.12], ['feelerB', 'feeler', 0.2, 0, 0, 0, 0, 0.14],
  ['brimL', 'hat', -0.34, 0.02, 0, 0, 0, 0.05], ['brimLb', 'brimL', -0.7, 0, 0, 0, 0, -0.14],
  ['brimF', 'hat', 0, 0.02, -0.33, 0, 0, 0], ['brimB', 'hat', 0, 0.02, 0.33, 0.05, 0, 0],
  ['growthA', 'crown', 0.25, 0.1, -0.3, 0, 0, 0], ['growthB', 'crown', -0.04, 0.24, -0.14, 0, 0, 0], ['growthC', 'crown', -0.24, 0.1, -0.36, 0, 0, 0],
  ['eyeHR', 'crown', 0.058, EYE[1], EYE[2], 0, 0, 0], ['eyeHL', 'crown', -0.058, EYE[1], EYE[2], 0, 0, 0], // HER eyes: the balls turn to look
  ['lidHR', 'crown', 0.058, EYE[1], EYE[2], 0, 0, 0], ['lidHL', 'crown', -0.058, EYE[1], EYE[2], 0, 0, 0], // their upper lids: - x shuts
  // the creature's five eyes: each lid sits on its eye, turned to face where that eye faces (- z of the lid's frame)
  ['lidCa', 'growthA', 0.085, 0.07, -0.085, -0.25, -0.75, 0], ['lidCb', 'growthA', 0.02, -0.03, -0.16, 0.2, -0.2, 0], ['lidCc', 'crown', -0.02, 0.29, -0.39, -0.9, 0.1, 0],
  ['lidCd', 'growthC', -0.06, 0.04, -0.07, -0.2, 0.7, 0], ['lidCe', 'growthB', 0.03, 0.01, 0.07, -0.5, 2.9, 0],
  ['idxR', 'handR', -0.03, -0.105, 0, 0, 0, 0], ['idxRb', 'idxR', 0, -0.085, 0, 0, 0, 0], ['finR', 'handR', 0.01, -0.105, 0, 0, 0, 0], ['finRb', 'finR', 0, -0.085, 0, 0, 0, 0], ['thumbR', 'handR', -0.04, -0.03, -0.012, 0, 0, 0],
  ['idxL', 'handL', 0.03, -0.105, 0, 0, 0, 0], ['idxLb', 'idxL', 0, -0.085, 0, 0, 0, 0], ['finL', 'handL', -0.01, -0.105, 0, 0, 0, 0], ['finLb', 'finL', 0, -0.085, 0, 0, 0, 0], ['thumbL', 'handL', 0.04, -0.03, -0.012, 0, 0, 0],
];
export const EXTRA_NAMES = EXTRA.map((e) => e[0]);

// markers (joint space): the model's own spots (c_hat_lord.parts.json `markers`). eyeAt / eyeHRAt / eyeHLAt = HER eyes,
// on the hat: what a camera or a look-at should treat as her eyes. socketAt = the empty heart socket.
const MK = {
  eyeAt: ['crown', 0, EYE[1], EYE[2] - 0.036], eyeHRAt: ['crown', 0.058, EYE[1], EYE[2] - 0.036], eyeHLAt: ['crown', -0.058, EYE[1], EYE[2] - 0.036],
  faceAt: ['head', 0, 0.25, -0.14], mouthAt: ['head', 0, 0.1, -0.12], socketAt: ['spine', -0.04, 0.43, -0.105],
  hatMouthAt: ['hat', 0, 0.06, -0.31], hatTopAt: ['crown', 0, 0.31, -0.27], brimTipR: ['feeler', 0, 0, 0], brimTipL: ['brimLb', -0.58, 0, 0], feelerTip: ['feelerB', 0.23, 0, 0],
  weakA: ['growthA', 0.085, 0.07, -0.085], weakB: ['growthA', 0.02, -0.03, -0.16], weakC: ['crown', -0.02, 0.29, -0.39], weakD: ['growthC', -0.06, 0.04, -0.07], weakE: ['growthB', 0.03, 0.01, 0.07],
  palmR: ['handR', 0, -0.06, 0.02], palmL: ['handL', 0, -0.06, 0.02], fingerTipR: ['idxRb', 0, -0.11, 0], fingerTipL: ['idxLb', 0, -0.11, 0],
};

export function hatLordLook(K) {
  hlRegister();
  const { person, g, sph, box, cyl, flat } = K;
  const SK = 0xd9cfe6, SUIT = 0x4a0f24, tH = HATLORD.torsoH;
  const suit = flat(SUIT), hide = flat(0x6a2a4a), bone = flat(0xe8dcc0), brass = flat(0xc8a040), pink = flat(0xff6f91);
  const parts = {}, all = {};
  const grp = (name, parent, x = 0, y = 0, z = 0, codeOnly = true) => { const o = g(x, y, z); o.name = 'ot_' + name; o.userData.codeOnly = codeOnly; parent.add(o); parts[name] = o; all[name] = [o]; return o; };
  const p = person({ skin: SK, legMat: suit, shoe: 0x14060c, s: HATLORD.s, legS: HATLORD.legS, hipW: HATLORD.hipW, thigh: 0.8, shin: 0.8, foot: 0.6, torsoH: tH, shW: HATLORD.shW, armR: 0.8,
    upper: HATLORD.upper, fore: HATLORD.fore, sleeveMat: suit, foreMat: suit, hunch: 0, wrongKnee: false, headR: HATLORD.headR, neck: HATLORD.neck, tilt: 0, pelvisMat: suit,
    torso: (sp) => { sp.add(cyl(0.15, 0.1, tH * 0.9, suit, 0, tH * 0.45, 0, 10)); sp.add(box(1.46, 0.07, 0.16, suit, 0, tH * 0.97, 0.12)); const cl = cyl(0.6, 0.38, 1.55, suit, 0, -0.72, 0.14, 12); cl.scale.z = 0.35; sp.add(cl); },
    head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 14)); },
    // (no eyes in her face: the rig's are hidden below. the mouth is the game's, so she talks like everyone else)
    face: { z: -0.13, eyeR: 0.02, eyeSep: 0.04, eyeY: 0.34, brow: false, mouthW: 0.066, mouthY: 0.1, mouthZ: -0.116, lip: 0x5a1230, lipR: 0.008, teeth: 'needle', lidColor: SK } });
  const c = p.ch;
  c.jank.tilt = 0; c.jank.lean = 0; c.jank.shoulder = 0; // (she is immaculate: no random tilt, no lean)
  for (const e of p.face.eyes) e.piv.visible = false;
  for (const l of p.face.lids) if (l) { l.top.visible = false; l.bot.visible = false; }
  p.face.set('chair');
  // ---- her own joints
  for (const [n, par, x, y, z, rx, ry, rz] of EXTRA) { const o = g(x, y, z); o.rotation.set(rx, ry, rz); o.name = 'hl_' + n; c[par].add(o); c[n] = o; }
  // ---- the code stand-ins (the Blender model replaces these) and the markers (kept)
  const hat = grp('hatCode', c.hat); const cr = cyl(0.27, 0.3, 0.3, hide, 0, 0.2, 0, 14); hat.add(cr);
  const band = cyl(0.31, 0.31, 0.08, bone, 0, 0.05, 0, 14); hat.add(band);
  const brim = grp('brimCode', c.hat); const bd = cyl(0.36, 0.36, 0.02, hide, 0, 0.02, 0, 16); bd.scale.set(1, 1, 1.9); brim.add(bd);
  for (const [jn, x, w, d] of [['brimR', 0.27, 0.56, 1.3], ['brimRb', 0.24, 0.5, 0.8], ['brimL', -0.36, 0.74, 1.4], ['brimLb', -0.33, 0.68, 0.9]]) { const o = grp(jn + 'Code', c[jn]); o.add(box(w, 0.02, d, pink, x, 0, 0)); }
  for (const [jn, z] of [['brimF', -0.16], ['brimB', 0.18]]) { const o = grp(jn + 'Code', c[jn]); o.add(box(0.7, 0.02, 0.34, pink, 0, 0, z)); }
  const fe = grp('feelerCode', c.feeler); const fr = cyl(0.006, 0.01, 0.2, bone, 0.1, 0, 0, 5); fr.rotation.z = Math.PI / 2; fe.add(fr);
  for (const jn of ['eyeHR', 'eyeHL']) { const o = grp(jn + 'Code', c[jn]); o.add(sph(0.036, flat(0xf6f2e8), 0, 0, 0)); o.add(sph(0.018, flat(0x7a4a22), 0, 0, -0.026)); }
  for (const jn of ['growthA', 'growthB', 'growthC']) { const o = grp(jn + 'Code', c[jn]); o.add(sph(0.1, flat(0xd9a060), 0, 0, 0)); }
  const sock = grp('socketCode', c.spine); const ring = cyl(0.04, 0.04, 0.012, brass, MK.socketAt[1], MK.socketAt[2], MK.socketAt[3], 12); ring.rotation.x = Math.PI / 2; sock.add(ring);
  for (const [name, [joint, x, y, z]] of Object.entries(MK)) grp(name, c[joint], x, y, z, false);
  parts.headJoint = c.head;
  return { ...p, parts, partsAll: all, kind: 'lord', height: 3.3, eyeY: 2.6, extra: EXTRA_NAMES };
}
