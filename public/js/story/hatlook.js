// MADAM CHAIR and her hat OVERSIGHT (working id hat_lord; docs/story/cast/HAT_LORD.md): her skeleton and code puppet.
// looks.js registers this as LOOKS.hat_lord (it hands over its own kit, so this file imports nothing from it).
// The Blender model (public/models/cast/c_hat_lord.glb, tools/blender/cast/make_cast_hat_lord.py) is built on these
// joints and replaces every group marked codeOnly; the markers stay for both.
// She is the cast skeleton (person()) plus joints of her own: the hat creature on its telescoping neck, its brim in
// six pieces, the crown that lifts off the band (the band is a mouth), three growth clusters, HER eye pair with a lid
// each, a lid for each of the creature's five eyes, the two hands of fingers laced over where her eyes would be, the
// two halves of her cape, and two-jointed fingers. EXTRA is the one list of them; the Blender build and the clips read it from joints.json.
// Her clips and the hat's life are in hatlord.js (HL).
import { FACES } from './face.js';
import { hlRegister } from './hatlord.js';

FACES.chair = { lid: 1, jaw: 0, st: 0.92, smile: 0.3, by: 0, bt: 0 }; // the resting face: pleasant, shut
FACES.chair_host = { lid: 1, jaw: 0.04, st: 1.08, smile: 0.62, by: 0, bt: 0 }; // offering you something
FACES.chair_flat = { lid: 1, jaw: 0, st: 0.82, smile: -0.05, by: 0, bt: 0 }; // "not carried."
FACES.chair_hurt = { lid: 1, jaw: 0.3, st: 0.8, smile: -0.5, by: 0, bt: 0 };

// her body is the owner's Tripo model (docs/story/cast_refs/hat_lord_tripo_owner.glb, rebuilt by
// tools/blender/cast/rebuild_hat_lord_tripo.py): 2.96 m to the top of her head, legs to 1.85 m on heels, long thin
// arms, fingers longer than her forearm. the hat sits on a short neck rooted in the top of her skull
export const HATLORD = { s: 1, legS: 2.0064, hipW: 0.1167, torsoH: 0.6161, shW: 0.1824, upper: 0.583, fore: 0.432, headR: [0.1, 0.16, 0.12], neck: -0.0049 };
// fitted to the Tripo model (tools/blender/cast/hl_fit.py): where its joints really are, and the pose it was made in
// (an A-pose) as their rest, so the skinned glb binds where it stands. [joint, position, rest turn]. the clips set these
// joints outright (hl_clips.py REST is the stance)
export const FIT = [
  ['legL', [-0.1167, 0.92, 0], [-0.064, -0.0014, 0.0213]], ['legR', [0.1167, 0.92, 0], [-0.064, 0.0014, -0.0211]],
  ['kneeL', [0, -0.3426, 0], [0, 0, 0]], ['kneeR', [0, -0.3426, 0], [0, 0, 0]],
  ['arm', [0.1752, 0.5237, 0.0731], [0, 0, 0.6087]], ['armL', [-0.1896, 0.5237, 0.0731], [0, 0, -0.588]],
  ['foreR', [0, -0.587, 0], [0.1006, 0.0094, 0.0924]], ['foreL', [0, -0.5787, 0], [0.1006, -0.01, -0.0984]],
  ['handR', [0, -0.4651, 0], [0.0104, -0.0025, -0.2365]], ['handL', [0, -0.4393, 0], [0.0208, 0.0045, 0.2133]],
  ['neck', [0, 0.6112, 0.0877], [0, 0, 0]], ['head', [0, 0.123, -0.038], [0, 0, 0]],
];

// [name, parent, x, y, z, rx, ry, rz]: where the joint sits in its parent's frame (unit scale) and its rest turn
// (three.js XYZ euler, radians). front is -z, +x is HER right. the hat's low end and its feeler are on her right.
// placed on the Tripo model (tools/blender/cast/hl_fit.py and the rebuild): the brim's wings lie along their joint's x
// (out to her right is +x, to her left -x), the feeler hangs down its x, every eye looks down its -z
export const EXTRA = [
  ['bandR', 'head', 0.115, 0.16, -0.0597, 0, 0, 0], ['bandL', 'head', -0.11, 0.16, -0.0547, 0, 0, 0], // the hat's fingers over her eyes: hinged at each temple
  ['hatNeck', 'head', 0, 0.3099, -0.01, 0, 0, 0], ['hatNeckB', 'hatNeck', 0, 0, 0, 0, 0, 0], // the neck stretches: B rides out of the first part, the hat out of B
  ['hat', 'hatNeckB', 0.006, 0.08, -0.0007, 0, 0, -0.097], // tipped down to her right, as made
  ['crown', 'hat', 0.0229, 0.0123, 0.621, 0, 0, 0], // hinged at the back of the band: + x opens the mouth
  ['brimR', 'hat', 0.4577, -0.0157, 0.211, 0.0124, -0.1269, -0.3523], ['brimRb', 'brimR', 0.4424, 0.0028, 0.0496, -0.0086, 0.0178, -0.1948],
  ['feeler', 'brimRb', 0.4683, 0.0019, 0.0298, 0.0154, 0.1458, -0.8085], ['feelerB', 'feeler', 0.4071, -0.0002, -0.0199, -0.0234, -0.1862, -0.0849],
  ['brimL', 'hat', -0.4327, 0.0483, 0.211, 0, 0, -0.253], ['brimLb', 'brimL', -0.6707, 0, 0.05, 0.0274, -0.075, -0.0952],
  ['brimF', 'hat', 0.0496, -0.0555, -0.309, 0, 0, 0], ['brimB', 'hat', -0.0069, 0.0094, 0.651, 0, 0, 0],
  ['growthA', 'crown', 0.3178, 0.1414, -0.49, 0, 0, 0], ['growthB', 'crown', -0.0026, 0.1304, -0.06, 0, 0, 0], ['growthC', 'crown', -0.334, 0.1283, -0.53, 0, 0, 0],
  // HER eyes, in the big socket at the front of the crown: the balls turn to look; their upper lids (- x shuts)
  ['eyeHR', 'crown', 0.1166, 0.1394, -0.8695, 0.0629, -0.2178, 0.1084], ['eyeHL', 'crown', 0.0276, 0.1268, -0.8899, 0.0629, -0.2178, 0.1084],
  ['lidHR', 'crown', 0.1166, 0.1394, -0.8695, 0.0629, -0.2178, 0.1084], ['lidHL', 'crown', 0.0276, 0.1268, -0.8899, 0.0629, -0.2178, 0.1084],
  // the creature's five lidded eyes: each lid sits on its eye, turned to face where that eye faces (- z of the lid's frame)
  ['lidCa', 'growthA', 0.0387, -0.0153, -0.027, -0.0364, -1.3843, -0.0339], ['lidCb', 'growthA', -0.0621, -0.0844, -0.269, -0.0974, -0.7119, -0.0626],
  ['lidCc', 'crown', -0.1414, 0.2043, -0.828, 0.0745, 0.32, -0.0243], ['lidCd', 'growthC', 0.0836, -0.0331, -0.227, -0.0488, 0.6491, 0.0282],
  ['lidCe', 'growthB', -0.0376, -0.0368, 0.038, -3.1064, 0.0596, 3.1396],
  // the cape's two halves: hinged on the pin down her back (a straight line leaning out behind her). capeR.y - / capeL.y + parts them
  ['capeR', 'spine', 0, 0.5941, 0.26, -0.158, 0, 0], ['capeL', 'spine', 0, 0.5941, 0.26, -0.158, 0, 0],
  // the fingers: index, the other three together, thumb. each frame's -y runs down the finger and +z is the palm side, so .x - curls
  ['idxR', 'handR', 0.0138, -0.2692, -0.0479, -2.6888, -0.8684, -2.6811], ['idxRb', 'idxR', 0, -0.2388, 0, -0.1555, -0.0087, 0.0552],
  ['finR', 'handR', 0, -0.2605, 0, -2.5793, -0.8071, -2.462], ['finRb', 'finR', 0, -0.2618, 0, -0.226, 0, 0],
  ['thumbR', 'handR', -0.008, -0.0937, -0.0521, -2.2134, -0.7473, -2.5911],
  ['idxL', 'handL', -0.0182, -0.2908, -0.0449, -2.7004, 0.8326, 2.6705], ['idxLb', 'idxL', 0, -0.2384, 0, -0.1491, 0.0072, -0.0477],
  ['finL', 'handL', 0, -0.2794, 0, -2.6462, 0.7893, 2.4938], ['finLb', 'finL', 0, -0.2536, 0, -0.2124, 0, 0],
  ['thumbL', 'handL', 0.0055, -0.1045, -0.0497, -2.2509, 0.7348, 2.6117],
];
export const EXTRA_NAMES = EXTRA.map((e) => e[0]);

// markers (joint space): the model's own spots, copied from c_hat_lord.parts.json `markers` (rebuild_hat_lord_tripo.py
// prints them as JF_MK_JS; tests/story/hat_lord.test.mjs checks they still agree). eyeAt / eyeHRAt / eyeHLAt = HER eyes, on the hat: what a camera or a look-at should treat as
// her eyes. weakA..E = the creature's five eyes. socketAt = the empty heart socket.
const MK = {
  mouthAt: ['head', 0.0055, 0.0582, -0.1326], faceAt: ['head', 0.0, 0.1599, -0.1597], socketAt: ['spine', 0.0055, 0.4001, -0.1817],
  palmR: ['handR', -0.0193, -0.1239, -0.0146], fingerTipR: ['idxRb', 0.0, -0.2, 0.0001], palmL: ['handL', 0.0191, -0.1251, -0.0153], fingerTipL: ['idxLb', 0.0, -0.2, 0.0],
  feelerTip: ['feelerB', 0.368, -0.0012, 0.0191], brimTipR: ['feeler', 0.0, 0.0, 0.0], brimTipL: ['brimLb', -0.8311, -0.0268, 0.2092],
  hatMouthAt: ['hat', 0.008, 0.1435, -0.311], hatTopAt: ['hat', 0.0035, 0.403, 0.1132],
  eyeAt: ['crown', 0.076, 0.1342, -0.8972], eyeHRAt: ['crown', 0.1204, 0.1405, -0.887], eyeHLAt: ['crown', 0.0315, 0.1279, -0.9074],
  weakA: ['lidCa', 0.0, 0.0, -0.1049], weakB: ['lidCb', 0.0, 0.0, -0.074], weakC: ['lidCc', 0.0, 0.0, -0.0639], weakD: ['lidCd', 0.0, 0.0, -0.0932],
  weakE: ['lidCe', 0.0, 0.0, -0.092],
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
    torso: (sp) => { sp.add(cyl(0.15, 0.1, tH * 0.9, suit, 0, tH * 0.45, 0, 10)); sp.add(box(1.46, 0.07, 0.16, suit, 0, tH * 0.97, 0.12)); },
    head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 14)); },
    // (no eyes in her face: the rig's are hidden below. the mouth is the game's, so she talks like everyone else)
    face: { z: -0.15, eyeR: 0.02, eyeSep: 0.04, eyeY: 0.16, brow: false, mouthW: 0.06, mouthY: 0.036, mouthZ: -0.152, lip: 0x5a1230, lipR: 0.007, teeth: 'needle', lidColor: SK } });
  const c = p.ch;
  for (const [j, at, r] of FIT) { c[j].position.set(...at); c[j].rotation.set(...r); } // (her joints where the model's are)
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
  for (const jn of ['eyeHR', 'eyeHL']) { const o = grp(jn + 'Code', c[jn]); o.add(sph(0.0175, flat(0xf6f2e8), 0, 0, 0)); o.add(sph(0.009, flat(0x7a4a22), 0, 0, -0.0125)); }
  for (const [jn, sx] of [['capeR', 1], ['capeL', -1]]) { const o = grp(jn + 'Code', c[jn]); o.add(box(0.44, 2.05, 0.3, suit, sx * 0.23, -0.5, -0.16)); }
  for (const jn of ['growthA', 'growthB', 'growthC']) { const o = grp(jn + 'Code', c[jn]); o.add(sph(0.1, flat(0xd9a060), 0, 0, 0)); }
  const sock = grp('socketCode', c.spine); const ring = cyl(0.04, 0.04, 0.012, brass, MK.socketAt[1], MK.socketAt[2], MK.socketAt[3], 12); ring.rotation.x = Math.PI / 2; sock.add(ring);
  for (const [name, [joint, x, y, z]] of Object.entries(MK)) grp(name, c[joint], x, y, z, false);
  parts.headJoint = c.head;
  return { ...p, parts, partsAll: all, kind: 'lord', height: 3.4, eyeY: 3.16, extra: EXTRA_NAMES };
}
