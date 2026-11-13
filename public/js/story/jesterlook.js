// THE HEADLINER, Lord of Entertainment (working id jester_lord; docs/story/cast/JESTER_LORD_MODEL.md): his skeleton and
// code puppet. looks.js registers this as LOOKS.jester_lord (it hands over its own kit, so this file imports nothing
// from it). He is a puppet jester from the waist up on a big spider: the cast skeleton (person(); its human legs are
// unused and empty) plus his own joints from jl_clipdata.js (written by tools/blender/cast/jl_clips.py from jl_rig.py):
// the thorax and the big top, eight legs of femur > tibia > foot > bell, the hat's horns with a bell each, the dummy
// jaw, the lids (shut: they open once), the brows, the collar's bells and the marotte (his own little head on a
// stick). The Blender model (public/models/cast/c_jester_lord.glb) is skinned on these joints and replaces every
// group marked codeOnly; the markers stay for both. His clips and his life are in jesterlord.js (JL).
import { FACES } from './face.js';
import { JL_DATA } from './jl_clipdata.js';
import { jlRegister } from './jesterlord.js';

FACES.headliner = { lid: 0, jaw: 0.12, st: 2.0, smile: 1.25, by: 0.01, bt: -0.3 }; // shut, smug, grinning past his ears
FACES.headliner_talk = { lid: 0, jaw: 0.2, st: 1.9, smile: 1.1, by: 0.02, bt: -0.25 };
FACES.headliner_tada = { lid: 0, jaw: 0.35, st: 2.1, smile: 1.4, by: 0.03, bt: -0.4 };
FACES.headliner_ow = { lid: 1.35, jaw: 0.8, st: 0.9, smile: -0.3, by: 0.04, bt: -0.2 }; // the one time his eyes open

export const RIG = JL_DATA.rig; // [name, parent, [x, y, z], [rx, ry, rz]]: local place and rest turn (three.js XYZ)
export const OWN = RIG.map((e) => e[0]).filter((n) => !JL_DATA.std.includes(n));
export const LEGS = ['A', 'B', 'C', 'D'].flatMap((p) => ['R', 'L'].map((s) => s + p));
const at = Object.fromEntries(RIG.map((e) => [e[0], e]));

// markers (joint space): the model's own spots, copied from c_jester_lord.parts.json `markers` (make_cast_jester_lord.py
// prints them as JF_MK_JS; tests/story/jester_lord.test.mjs checks they agree). eyeAt = between his (shut) eyes: what a
// camera or a look-at should treat as his eyes. stumpAt = where his right second leg comes off
const MK = {
  eyeAt: ['head', 0.0, 0.481, -0.3165], eyeRAt: ['lidR', 0.0, 0.0, -0.05], eyeLAt: ['lidL', 0.0, 0.0, -0.05], faceAt: ['head', 0.0, 0.39, -0.338],
  mouthAt: ['jaw', 0.0, -0.026, -0.299], noseTip: ['head', 0.0, 0.3588, -0.8255], hatTipR: ['bellHR', 0.0, 0.0, 0.0],
  palmR: ['handR', 0.0, -0.07, 0.0], hatTipL: ['bellHL', 0.0, 0.0, 0.0], palmL: ['handL', 0.0, -0.07, 0.0], marotteAt: ['marotte', 0.0, 0.0, -0.06],
  stumpAt: ['thorax', 0.5246, -0.0241, -0.2006], topAt: ['abdo', 0.0, 1.5128, 0.86], spinneret: ['abdo', 0.0, 0.0964, 1.74],
  chestAt: ['spine', 0.0, 0.42, -0.18],
};

export function jesterLordLook(K) {
  jlRegister();
  const { person, g, sph, cyl, flat, patMat } = K;
  const PINK = 0xff4fc0, YEL = 0xffe14d, LAQ = 0x2a1236;
  const pink = flat(PINK), yel = flat(YEL), laq = flat(LAQ), wht = flat(0xf6f2ec), blk = flat(0x17111c), brass = flat(0xd8a840);
  const diamonds = (a, b) => (c, w, h) => { c.fillStyle = b; c.fillRect(0, 0, w, h); c.fillStyle = a; c.beginPath(); c.moveTo(w / 2, 0); c.lineTo(w, h / 2); c.lineTo(w / 2, h); c.lineTo(0, h / 2); c.fill(); };
  const dPY = patMat('jl_dpy', 32, 48, diamonds('#ff4fc0', '#ffe14d'), [2, 6]), dBW = patMat('jl_dbw', 32, 48, diamonds('#17111c', '#f6f2ec'), [2, 6]);
  const stripes = patMat('jl_top', 64, 8, (c, w, h) => { for (let i = 0; i < 8; i++) { c.fillStyle = i % 2 ? '#ffe14d' : '#ff4fc0'; c.fillRect((i * w) / 8, 0, w / 8 + 1, h); } }, [2, 1]);
  const parts = {}, all = {};
  const grp = (name, parent, x = 0, y = 0, z = 0, codeOnly = true) => { const o = g(x, y, z); o.name = 'ot_' + name; o.userData.codeOnly = codeOnly; parent.add(o); parts[name] = o; all[name] = [o]; return o; };
  const HS = 1.3;
  const p = person({ skin: 0xf7efe6, s: 1, legS: 1, torsoH: 0.77, shW: 0.37, upper: 0.43, fore: 0.39, headR: [0.235 * HS, 0.3 * HS, 0.245 * HS], neck: 0.07, tilt: 0, wrongKnee: false, pelvis: false,
    sleeveMat: pink, foreMat: dBW, handMat: wht, jointMat: blk,
    torso: (sp) => { const t = cyl(0.33, 0.13, 0.77, pink, 0, 0.385, 0, 12); sp.add(t); },
    face: { z: -0.32, eyeR: 0.05, eyeSep: 0.127, eyeY: 0.481, iris: 0x111111, mouthW: 0.3, mouthY: 0.24, lip: 0xd8105c, lipR: 0.016, teeth: 'tomb', brow: 0x17111c, browW: 0.07 } });
  const c = p.ch;
  // he has a spider for legs: the human ones stay as empty joints
  for (const j of ['legL', 'legR', 'kneeL', 'kneeR']) for (const m of [...c[j].children]) if (m.isMesh) c[j].remove(m);
  // ---- every joint where the rig puts it (the cast's own ones too: the spine rides the thorax)
  for (const [n, par, pos, rot] of RIG) {
    let o = c[n];
    if (!o) { o = g(); o.name = 'jl_' + n; c[n] = o; }
    if (par && o.parent !== c[par]) c[par].add(o);
    o.position.set(...pos); o.rotation.set(...rot);
  }
  c.jank.tilt = 0; c.jank.lean = 0; c.jank.shoulder = 0;
  p.face.set('headliner');
  // ---- the code stand-ins (the Blender model replaces these) and the markers (kept)
  const t = grp('thoraxCode', c.thorax); t.add(sph(1, laq, 0, 0, 0, 0.5, 0.3, 0.56, 16));
  const ab = grp('abdoCode', c.abdo); ab.add(sph(1, stripes, 0, 0.34, 0.86, 0.68, 0.58, 0.88, 16));
  const along = (parent, len, r0, r1, mat) => { const m = cyl(r1, r0, len, mat, len / 2, 0, 0, 8); m.rotation.z = -Math.PI / 2; parent.add(m); };
  for (const L of LEGS) {
    const [s, q] = [L[0], L[1]];
    const fm = c['fem' + s + q], tb = c['tib' + s + q], ft = c['foot' + s + q], bl = c['bell' + s + q];
    const l1 = at['tib' + s + q][2][0], l2 = at['foot' + s + q][2][0], l3 = at['bell' + s + q][2][0];
    along(grp('fem' + L + 'Code', fm), l1, 0.08, 0.06, dPY); along(grp('tib' + L + 'Code', tb), l2, 0.064, 0.046, dBW); along(grp('foot' + L + 'Code', ft), l3 * 0.8, 0.05, 0.035, blk);
    grp('knee' + L + 'Code', tb).add(sph(0.088, laq, 0, 0, 0)); grp('bell' + L + 'Code', bl).add(sph(0.064, brass, 0, -0.075, 0));
  }
  for (const [s, mat] of [['R', pink], ['L', yel]]) {
    const h = grp('hat' + s + 'Code', c['hat' + s]); const k = cyl(0.02, 0.15, 0.6, mat, 0, 0.25, 0.1, 10); k.rotation.x = -0.5; k.rotation.z = s === 'R' ? -0.3 : 0.3; h.add(k);
    grp('bellH' + s + 'Code', c['bellH' + s]).add(sph(0.06, brass, 0, -0.07, 0));
  }
  const nose = cyl(0.0, 0.05, 0.42, wht, 0, 0.36, -0.52, 8); nose.rotation.x = -Math.PI / 2; grp('noseCode', c.head).add(nose);
  const stick = cyl(0.017, 0.017, 0.5, blk, 0, -0.085, -0.13, 6); stick.rotation.x = Math.PI / 2; grp('marotteCode', c.handL).add(stick);
  grp('marotteHeadCode', c.marotte).add(sph(0.09, wht, 0, 0, -0.08));
  const col = grp('collarCode', c.collar); for (let i = 0; i < 8; i++) { const a = ((i + 0.5) / 8) * Math.PI * 2; col.add(sph(0.034, brass, Math.sin(a) * 0.41, -0.15, -Math.cos(a) * 0.41)); }
  for (const [name, [joint, x, y, z]] of Object.entries(MK)) grp(name, c[joint], x, y, z, false);
  parts.headJoint = c.head;
  return { ...p, parts, partsAll: all, kind: 'lord', height: 3.3, eyeY: 2.84, extra: OWN };
}
