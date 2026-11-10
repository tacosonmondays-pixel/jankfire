// PALLET JACK (Jack Marsh, 41, the Bottom's delivery man; docs/story/TRAIN.md §2): his skeleton and code puppet.
// looks.js registers this as LOOKS.pallet_jack (it hands over its own kit, so this file imports nothing from it).
// The Blender model (public/models/cast/c_pallet_jack.glb, tools/blender/cast/make_cast_pallet_jack.py) is built on
// these joints and replaces every group marked codeOnly; the markers (not codeOnly) stay for both.
//   markers in L.parts (MK below): chest (left of the weld: where your hand goes), palmL (his open hand), gripR (what
//   his fist holds), fistAt (the knuckles), elbowAt (the rocket's exhaust), boilerAt fireAt gaugeAt bleedAt, stackTipL / R,
//   woundAt ventAt (the hole, front and back), armFrontEnd armBackEnd, marrowAt, seatAt (what sits on the rail), eyeAt
// His clips, damage states and fx are in palletjack.js (PJ).
import { FACES } from './face.js';
import { pjRegister } from './palletjack.js'; // (his clips register themselves the first time he is built)

// tired, kind: lids a third down, the inner brow ends up, the corners of the mouth up. his resting face
FACES.jack = { lid: 0.78, jaw: 0, st: 1.0, smile: 0.36, by: -0.003, bt: -0.3 };
FACES.jack_hurt = { lid: 0.5, jaw: 0.16, st: 0.95, smile: -0.25, by: 0.004, bt: -0.55 }; // run through, still being polite about it
FACES.jack_gone = { lid: 0.06, jaw: 0.12, st: 0.95, smile: 0.1, by: 0, bt: -0.2 }; // after

export const JACK = { s: 1.24, legS: 0.8, hipW: 0.17, torsoH: 0.58, shW: 0.415, upper: 0.27, fore: 0.27, headR: [0.13, 0.14, 0.128], neck: 0.03, hunch: 0.05 };

const MK = {
  chest: ['spine', -0.105, 0.402, -0.241], weldAt: ['spine', 0.029, 0.462, -0.225], // (your hand goes on `chest`: his left of the weld)
  boilerAt: ['spine', 0, 0.213, 0.378], fireAt: ['spine', 0, 0.126, 0.392], gaugeAt: ['spine', -0.138, 0.356, 0.335], bleedAt: ['spine', 0.137, 0.13, 0.369],
  stackTipL: ['spine', -0.29, 0.835, 0.378], stackTipR: ['spine', 0.29, 0.835, 0.378], stackTipBentL: ['spine', -0.41, 0.667, 0.457], stackTipBentR: ['spine', 0.326, 0.749, 0.519],
  woundAt: ['spine', 0.054, 0.186, -0.272], ventAt: ['spine', 0.062, 0.273, 0.378], armFrontEnd: ['spine', 0.071, 0.078, -0.519], armBackEnd: ['spine', 0.066, 0.354, 0.725], marrowAt: ['spine', 0, 0.227, 0.166],
  elbowAt: ['foreR', 0, 0.023, 0.17], fistAt: ['handR', 0, -0.184, -0.034], gripR: ['handR', 0, -0.125, 0.03], palmL: ['handL', 0, -0.1, 0.042],
  seatAt: ['body', 0, 0.79, 0.06], eyeAt: ['head', 0, 0.168, -0.12],
};

export function palletJackLook(K) {
  pjRegister();
  const { person, g, sph, cap, box, cyl, flat, patMat, speckle } = K;
  const SK = 0xeea488, tH = JACK.torsoH;
  const skin = patMat('pjskin', 64, 64, speckle('#eea488', ['#c46a56', '#ffc8b0']), [2, 2], 0.42);
  const hivis = patMat('pjhivis', 64, 64, (c, w, h) => { c.fillStyle = '#e8f03a'; c.fillRect(0, 0, w, h); c.fillStyle = '#c8ccd0'; c.fillRect(0, 14, w, 7); c.fillRect(0, 40, w, 7); c.fillStyle = '#1a1a1e'; c.font = 'bold 9px sans-serif'; c.fillText('MARSH', 14, 34); }, [1, 1], 0.8);
  const singlet = flat(0xd8d2c0), canvas = patMat('pjcanvas', 64, 64, speckle('#5a5648', ['#4a463a', '#6a6656'], 260, 2), [2, 2], 0.85);
  const steel = flat(0x8a9098), dark = flat(0x2a2a30), red = flat(0xb03a2a), chrome = flat(0xd0d4dc);
  const parts = {}, all = {};
  const grp = (name, parent, x = 0, y = 0, z = 0, codeOnly = true) => { const o = g(x, y, z); o.name = 'ot_' + name; o.userData.codeOnly = codeOnly; parent.add(o); parts[name] = o; all[name] = [o]; return o; };
  const p = person({ skin: SK, skinMat: skin, legMat: canvas, shoe: 0x3a2a1c, s: JACK.s, legS: JACK.legS, hipW: JACK.hipW, thigh: 1.75, shin: 1.5, foot: 1.5, torsoH: tH, shW: JACK.shW, armR: 1.6,
    upper: JACK.upper, fore: JACK.fore, foreS: 2.0, handS: 1.7, sleeveMat: skin, hunch: JACK.hunch, wrongKnee: false, headR: JACK.headR, neck: JACK.neck,
    torso: (sp) => { sp.add(sph(0.3, singlet, 0, tH * 0.52, 0, 1.45, 1.05, 0.92, 16)); sp.add(sph(0.2, skin, 0, tH * 0.95, 0.0, 1.9, 0.5, 1.0)); },
    head: (h, r, m) => { h.add(sph(1, m, 0, r[1], 0, r[0], r[1], r[2], 16)); h.add(sph(0.03, m, 0.004, r[1] * 0.82, -r[2] * 1.02, 1.1, 1.3, 1.2)); for (const sx of [-1, 1]) h.add(sph(0.03, m, sx * r[0], r[1], 0, 0.5, 1, 0.8)); h.add(sph(0.125, flat(0x3a2a22), 0, r[1] * 1.45, 0.02, 1.02, 0.6, 1.02)); },
    // (the eyes sit back in their sockets under the brow: z is the face plane, the mouth keeps its own)
    face: { z: -0.108, eyeR: 0.025, eyeSep: 0.054, eyeY: 0.168, iris: 0x7a5a36, mouthW: 0.088, mouthY: 0.064, mouthZ: -0.12, lip: 0xc27866, lipR: 0.0115, teeth: 'tomb', brow: 0x3a2a22, browW: 0.072, lidColor: 0xe2957c } });
  const c = p.ch;
  p.face.set('jack');
  for (const b of p.face.brows) { b.m.position.z = -0.143; b.m.scale.set(1, 1.3, 1); } // (heavy brows, out on the ridge of the model's brow)
  // ---- the code stand-ins (the Blender model replaces these) and the markers (kept)
  const vest = grp('vest', c.spine); vest.add(box(0.74, 0.5, 0.02, hivis, 0, tH * 0.5, -0.27)); vest.add(box(0.74, 0.44, 0.02, hivis, 0, tH * 0.55, 0.27));
  const collar = grp('collar', c.spine); const bar = cyl(0.022, 0.022, 0.7, steel, 0, tH * 0.9, -0.17, 8); bar.rotation.z = Math.PI / 2; collar.add(bar); collar.add(sph(0.035, steel, 0.03, tH * 0.9, -0.18));
  const boiler = grp('boiler', c.spine); boiler.add(cyl(0.16, 0.16, 0.36, dark, 0, 0.15, 0.24, 14)); boiler.add(cyl(0.165, 0.165, 0.03, steel, 0, 0.27, 0.24, 14)); boiler.add(cyl(0.165, 0.165, 0.03, steel, 0, 0.03, 0.24, 14));
  for (const [sx, nm] of [[-1, 'L'], [1, 'R']]) {
    const st = grp('stack' + nm, c.spine); const tube = cyl(0.035, 0.04, 0.44, chrome, sx * 0.13, 0.52, 0.33, 10); tube.rotation.x = 0.12; st.add(tube);
    const knee = nm === 'L' ? c.kneeL : c.kneeR, shin = grp('shin' + nm, knee);
    shin.add(cyl(0.03, 0.03, 0.2, red, 0, -0.1, -0.07, 8)); shin.add(cyl(0.016, 0.016, 0.3, chrome, 0, -0.18, -0.07, 8));
  }
  const fist = grp('fist', c.handR); fist.add(box(0.14, 0.05, 0.1, steel, 0, -0.12, -0.02));
  const ram = grp('ram', c.foreR); ram.add(cyl(0.06, 0.06, 0.06, steel, 0, -0.25, 0, 10));
  const towel = grp('towel', c.body); towel.add(box(0.09, 0.16, 0.02, flat(0xf0ead8), 0.14, 0.9, 0.2));
  // markers (joint space, unit scale): the model's own spots (c_pallet_jack.parts.json `markers`, copied by hand)
  for (const [name, [joint, x, y, z]] of Object.entries(MK)) grp(name, c[joint], x, y, z, false);
  parts.headJoint = c.head;
  return { ...p, parts, partsAll: all, kind: 'cyborg', height: 2.12, eyeY: 1.97 };
}
