// Reloads for the guns that only had the generic dip. The standard ones move their real parts (the AR / SMG mag and
// charging handle, the shotgun's forend, the sniper's bolt, the revolver's cylinder on its crane); the goofy ones get a
// bit: a juice box into the water pistol, a bag of marbles tipped into the jar, a tiny arm that climbs out of the
// minigun's ammo box to shove the belt in, a little hammer for the nail strip, a jerry can + a rev for the Redline,
// glowing shells for the reaper's rifle. Each one lasts exactly the gun's reload time (shared/weapons.js), so the ammo
// refills on the last frame; fire / ADS / switching cancel or block them like any reload (weapons.js).
// Channels (anim.js sampleCh), all optional:
//   mag [dy, dz, rx]   the mag off its seat (hidden below -0.3)      charge [dz]   charging handle / cocking lever back
//   pump [dz]          shotgun forend / water pistol pump back       bolt [up, back] 0..1 each (sniper)
//   cyl [out, spin]    revolver crane 0 shut..1 out, extra turns     fold [a]  reaper blade swung open
//   lid [a]            marble jar lid flipped                         fill [k]  water tank filled toward full
//   needle [k]         Redline tacho forced toward the red
//   lh [k, f, x, y, z, rx, ry, rz]   the off hand: k 0 off screen..1 there; f = what (x, y, z) is measured from
//                      (0 the gun, 1 the mag, 2 the charging handle, 3 the pump, 4 the bolt, 5 the cylinder),
//                      fractions blend two of them. gun units (the model's own space), rotation on top of the gun's
//   p_<prop> [show, x, y, z, rx, ry, rz, squash]   a prop (built below): show 0 hidden..1 (a prop with rounds shows
//                      that fraction of them), offsets from where it sits (on the off hand, or on the gun)
import * as THREE from 'three';
import { ANIMS } from './anim.js';
import { M } from './models.js';
import { WEAPONS } from '/shared/weapons.js';
import { G } from './ctx.js';
import { sfx } from './audio.js';

const PI = Math.PI, PI2 = PI * 2;
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });

// ------------------------------------------------------------ props (hand props in real metres, gun props in gun units)
const box = (w, h, d, c, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c)); m.position.set(x, y, z); return m; };
const cyl = (r, h, c, x = 0, y = 0, z = 0, seg = 8, basic = false) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), M(c, basic)); m.position.set(x, y, z); return m; };
const ballM = (r, c, x = 0, y = 0, z = 0, basic = false) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 8, 6), M(c, basic)); m.position.set(x, y, z); return m; };
const along = (o) => { o.rotation.x = PI / 2; return o; }; // cylinders lie along z
const MARBLES = [0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0x37d6ff];
const PROPS = {
  shell() { const g = new THREE.Group(); g.add(along(cyl(0.0095, 0.05, 0xd8262a, 0, 0, 0, 10)), along(cyl(0.0102, 0.012, 0xd9a53a, 0, 0, 0.024, 10))); return g; }, // a red shell, brass head back
  speedloader() { // six rounds held on a black knurled disc, a knob to twist
    const g = new THREE.Group(), rounds = new THREE.Group(); g.add(rounds);
    g.add(along(cyl(0.021, 0.01, 0x18181c, 0, 0, 0.012, 12)), along(cyl(0.008, 0.02, 0x2a2a30, 0, 0, 0.026, 8)));
    for (let i = 0; i < 6; i++) { const a = (i / 6) * PI2, r = new THREE.Group(); r.position.set(Math.cos(a) * 0.0135, Math.sin(a) * 0.0135, 0); r.add(along(cyl(0.0048, 0.026, 0xd9a53a, 0, 0, 0, 8)), along(cyl(0.004, 0.008, 0xb87333, 0, 0, -0.016, 8))); rounds.add(r); }
    g.userData.rounds = rounds.children; return g;
  },
  clip() { // a stripper clip of five
    const g = new THREE.Group(), rounds = [];
    g.add(box(0.012, 0.004, 0.056, 0x8a8f99, 0, -0.026, 0));
    for (let i = 0; i < 5; i++) { const r = new THREE.Group(); r.position.set(0, 0, -0.022 + i * 0.011); r.add(cyl(0.0042, 0.048, 0xd9a53a, 0, 0, 0, 8), cyl(0.0036, 0.012, 0xb87333, 0, 0.028, 0, 8)); g.add(r); rounds.push(r); }
    g.userData.rounds = rounds; return g;
  },
  juice() { // a juice box: pink with a yellow band, a bendy straw out of the top corner
    const g = new THREE.Group();
    g.add(box(0.042, 0.064, 0.026, 0xff4fd8), box(0.0425, 0.016, 0.0265, 0xffe14d, 0, 0.008, 0), box(0.012, 0.012, 0.0268, 0x39ff14, 0.008, -0.016, 0));
    const st = cyl(0.0022, 0.05, 0xffffff, 0.012, 0.055, 0, 6); st.rotation.z = -0.35; g.add(st);
    return g;
  },
  bag() { // a little net bag of marbles
    const g = new THREE.Group();
    const net = new THREE.Mesh(new THREE.SphereGeometry(0.034, 9, 7), new THREE.MeshLambertMaterial({ color: 0xff4fd8, wireframe: true })); net.scale.set(1, 1.2, 1); g.add(net);
    for (let i = 0; i < 9; i++) { const a = i * 2.4; g.add(ballM(0.011, MARBLES[i % 7], Math.cos(a) * 0.016, -0.015 + (i % 3) * 0.012, Math.sin(a) * 0.016)); }
    g.add(cyl(0.006, 0.02, 0xffe14d, 0, 0.044, 0, 6)); // the drawstring knot
    return g;
  },
  can() { // a tiny red jerry can with a spout
    const g = new THREE.Group(); g.scale.setScalar(0.7);
    g.add(box(0.05, 0.062, 0.022, 0xe0201a), box(0.05, 0.008, 0.0222, 0xffe14d, 0, 0.012, 0), box(0.016, 0.01, 0.012, 0x1a1a1a, -0.014, 0.036, 0));
    const sp = cyl(0.004, 0.035, 0x2a2a2a, 0.02, 0.045, 0, 6); sp.rotation.z = -0.8; g.add(sp);
    return g;
  },
  strip() { // a fresh strip of nails, heads up, glued on a paper band
    const g = new THREE.Group();
    g.add(box(0.03, 0.15, 0.006, 0xf2e6c8, 0, 0, 0.012));
    for (let i = 0; i < 10; i++) g.add(box(0.034, 0.004, 0.05, 0xc8d0d8, 0, -0.066 + i * 0.0145, -0.012));
    return g;
  },
  hammer() { // a tiny claw hammer, pink handle
    const g = new THREE.Group();
    g.add(box(0.012, 0.075, 0.012, 0xff4fd8, 0, 0.03, 0), box(0.014, 0.016, 0.04, 0x9aa2ac, 0, 0.07, -0.006), box(0.012, 0.012, 0.018, 0x9aa2ac, 0, 0.074, 0.02));
    return g;
  },
  souls() { // four glowing cyan rounds (the reaper's)
    const g = new THREE.Group(), rounds = [];
    for (let i = 0; i < 4; i++) { const r = new THREE.Group(); r.position.set(-0.006 + (i % 2) * 0.012, 0, -0.01 + Math.floor(i / 2) * 0.014); r.add(cyl(0.0055, 0.04, 0x3ee6c8, 0, 0, 0, 8, true), cyl(0.0058, 0.008, 0x1a1a1a, 0, -0.022, 0, 8)); g.add(r); rounds.push(r); }
    g.userData.rounds = rounds; return g;
  },
  crounds() { // six brass rims at the back of the chambers
    const g = new THREE.Group();
    for (let i = 0; i < 6; i++) { const a = (i / 6) * PI2 + PI / 6; g.add(along(cyl(0.0055, 0.006, 0xd9a53a, Math.cos(a) * 0.015, Math.sin(a) * 0.015, 0, 8))); }
    return g;
  },
  // ---- gun props (gun units): the minigun's ammo box lid, a tiny arm in the box, and the new belt
  mlid() { const g = new THREE.Group(); g.add(box(0.104, 0.012, 0.144, 0x5a4a22, 0, 0, -0.072)); g.add(box(0.03, 0.008, 0.02, 0xffe14d, 0, 0.008, -0.13)); return g; }, // hinged at its back edge
  arm() { // a tiny mannequin arm: upper, elbow, forearm, a fist with a thumb (rotation x / z on the shoulder)
    const g = new THREE.Group(), SK = 0xf1c27d;
    g.add(cyl(0.012, 0.07, SK, 0, 0.035, 0, 6), ballM(0.013, 0xe3ae68, 0, 0.07, 0));
    const fore = new THREE.Group(); fore.position.y = 0.07; g.add(fore); fore.add(cyl(0.011, 0.06, SK, 0, 0.03, 0, 6), box(0.026, 0.024, 0.026, SK, 0, 0.068, 0), box(0.008, 0.02, 0.008, SK, 0.014, 0.084, 0));
    g.userData.fore = fore; return g;
  },
  belt() { // a belt of 8 rounds on links, lying across (along x)
    const g = new THREE.Group();
    for (let i = 0; i < 8; i++) { g.add(box(0.012, 0.016, 0.03, 0x4a4a4a, i * 0.016, 0, 0)); g.add(cyl(0.006, 0.05, 0xd9a53a, i * 0.016, 0.008, 0, 8)); g.children[g.children.length - 1].rotation.x = PI / 2; }
    return g;
  },
};

// ------------------------------------------------------------ the reloads
// magSwap: out at t0, gone by t0+0.24, the fresh one comes up from below and is seated (with a slap) at tIn
const magSwap = (t0, tIn, drop = 0.36, rock = 0) => [[0, 0, 0, 0], [t0, 0, 0, 0], [t0 + 0.08, -0.05, 0.01, rock * 0.5], [t0 + 0.24, -drop, 0.06, rock], [tIn - 0.42, -drop, 0, rock], [tIn - 0.06, -0.05, 0, rock * 0.5], [tIn, 0.006, 0, 0], [tIn + 0.05, 0, 0, 0]];
const H0 = [0, 0, 0, 0, 0, 0, 0]; // off hand, away
const RL = {
  // ---- Assault Rifle: tip it, drop the mag, a fresh one slapped home, reach over and yank the charging handle
  ar: { dur: 1.7, keys: [
    K(0), K(0.2, [-0.09, 0.08, -0.08], [0.18, 0.46, 0.55]), K(0.78, [-0.092, 0.078, -0.08], [0.17, 0.47, 0.58]),
    K(1.08, [-0.09, 0.094, -0.085], [0.23, 0.46, 0.52], 'snap'), K(1.16, [-0.09, 0.08, -0.08], [0.18, 0.46, 0.55]),
    K(1.36, [0.01, 0.02, 0.03], [0.1, 0.15, -0.35]), K(1.48, [0.01, 0.02, 0.047], [0.1, 0.15, -0.36], 'snap'), K(1.7),
  ], ch: { mag: magSwap(0.22, 1.08), charge: [[0, 0], [1.38, 0], [1.45, 0.09], [1.5, 0.09], [1.56, 0]],
    lh: [[0.1, 0, 1, 0, -0.12, 0.01], [0.24, 1, 1, 0, -0.12, 0.01], [0.42, 1, 1, 0, -0.12, 0.01], [0.66, 1, 1, 0, -0.12, 0.01], [1.1, 1, 1, 0, -0.12, 0.01], [1.2, 0.9, 1.5, 0, -0.04, 0.03, -0.4], [1.36, 1, 2, -0.01, 0.025, 0.02, -0.4], [1.56, 1, 2, -0.01, 0.025, 0.02, -0.4], [1.68, 0, 2, -0.01, 0.025, 0.02, -0.4]] },
  events: [[0.24, 'magOut'], [1.08, 'magIn'], [1.45, 'chargeBack'], [1.56, 'chargeHome']] },
  // ---- SMG: the HK way: cocking lever back and locked, mag swap, slap the lever down
  smg: { dur: 1.5, keys: [
    K(0), K(0.12, [-0.02, 0.03, 0.03], [0.12, 0.35, -0.25]), K(0.22, [-0.02, 0.03, 0.04], [0.12, 0.35, -0.25], 'snap'),
    K(0.36, [-0.08, 0.075, -0.06], [0.18, 0.46, 0.55]), K(0.88, [-0.082, 0.073, -0.06], [0.17, 0.47, 0.58]),
    K(1.0, [-0.08, 0.09, -0.065], [0.24, 0.46, 0.5], 'snap'), K(1.12, [-0.02, 0.03, 0.03], [0.12, 0.35, -0.25]),
    K(1.22, [-0.02, 0.02, 0.025], [0.08, 0.35, -0.28], 'snap'), K(1.5),
  ], ch: { mag: magSwap(0.36, 1.0, 0.36), charge: [[0, 0], [0.12, 0], [0.2, 0.07], [1.18, 0.07], [1.22, 0]],
    lh: [[0, 0, 2, -0.02, 0, 0.02], [0.1, 1, 2, -0.02, 0, 0.02], [0.22, 1, 2, -0.02, 0, 0.02], [0.34, 0.6, 1.5, 0, -0.06, 0], [0.42, 1, 1, 0, -0.14, 0.01], [1.02, 1, 1, 0, -0.14, 0.01], [1.1, 1, 2, -0.02, 0.03, 0.02], [1.24, 1, 2, -0.02, -0.01, 0.02], [1.42, 0, 2, -0.02, -0.01, 0.02]] },
  events: [[0.2, 'chargeBack'], [0.38, 'magOut'], [1.0, 'magIn'], [1.22, 'hkSlap']] },
  // ---- Revolver: swing the cylinder out, muzzle up so the empties fall out, speedloader in, twist, flick it shut, spin
  revolver: { dur: 2.0, keys: [
    K(0), K(0.16, [-0.05, 0.03, 0.01], [0.15, 0.25, -0.55]),
    K(0.32, [-0.05, 0.07, 0.03], [1.05, 0.2, -0.45], 'snap'), K(0.5, [-0.05, 0.065, 0.03], [1.0, 0.2, -0.45]), // muzzle up: brass out
    K(0.66, [-0.06, 0.03, -0.02], [-0.3, 0.75, -0.35]), K(1.2, [-0.06, 0.032, -0.02], [-0.28, 0.75, -0.35]), // muzzle down for the loader
    K(1.38, [-0.03, 0.03, 0], [0.05, 0.1, 0.25], 'snap'), // flick it shut
    K(1.5, [-0.02, 0.02, 0], [0, 0.05, -0.1]), K(2.0),
  ], ch: { cyl: [[0, 0, 0], [0.14, 0, 0], [0.26, 1, 0], [1.33, 1, 0], [1.4, 0, 0], [1.5, 0, 0], [1.92, 0, PI2 * 2]],
    lh: [[0.32, 0, 5, -0.03, -0.03, 0.08], [0.5, 0.4, 5, -0.03, -0.03, 0.12], [0.76, 1, 5, -0.006, -0.012, 0.11], [0.92, 1, 5, -0.006, -0.012, 0.065], [1.1, 1, 5, -0.006, -0.012, 0.065, 0, 0, 1.2], [1.24, 0.5, 5, -0.03, -0.05, 0.12, 0, 0, 1.2], [1.34, 0, 5, -0.03, -0.07, 0.14]],
    p_speedloader: [[0.5, 1, 0, 0, 0], [0.95, 1, 0, 0, 0], [0.96, 0.0001, 0, 0, 0], [1.3, 0.0001, 0, 0, 0], [1.32, 0, 0, 0, 0]], p_crounds: [[0, 0], [0.95, 0], [0.96, 1], [1.99, 1]] }, // the rounds stay in the chambers
  events: [[0.26, 'cylOut'], [0.34, 'casings'], [0.95, 'loaderIn'], [1.1, 'loaderTwist'], [1.38, 'cylIn'], [1.5, 'spinCyl']] },
  // ---- Shotgun: roll it to show the loading port, thumb six shells in, rack it
  shotgun: { dur: 2.0, keys: (() => {
    const k = [K(0), K(0.2, [-0.07, 0.08, -0.06], [0.1, 0.4, -1.45])];
    for (let i = 0; i < 6; i++) { const t = 0.3 + i * 0.2; k.push(K(t + 0.12, [-0.07, 0.086, -0.06], [0.13, 0.4, -1.45], 'snap'), K(t + 0.2, [-0.07, 0.08, -0.06], [0.1, 0.4, -1.45])); }
    k.push(K(1.6, [0, 0.01, 0.02], [0.05, 0, -0.15]), K(1.7, [0, 0.0, 0.05], [0.12, 0, -0.18]), K(1.8, [0, -0.005, -0.01], [0.05, 0, -0.15], 'snap'), K(2.0));
    return k;
  })(), ch: (() => {
    const lh = [[0.16, 0, 0, 0, -0.12, -0.02, 0.4, 0, 0]], sh = [[0.16, 1, 0, 0, 0]];
    for (let i = 0; i < 6; i++) {
      const t = 0.3 + i * 0.2;
      lh.push([t, 1, 0, -0.01, -0.13, 0.0, 0.4, 0, 0], [t + 0.12, 1, 0, -0.01, -0.075, -0.06, 0.4, 0, 0], [t + 0.17, 0.75, 0, -0.01, -0.13, 0.01, 0.4, 0, 0]);
      sh.push([t + 0.11, 1, 0, 0, 0], [t + 0.125, 0, 0, 0, 0], [t + 0.18, 1, 0, 0, 0]);
    }
    lh.push([1.5, 0.5, 1, 0, -0.1, 0], [1.6, 1, 3, 0, -0.045, 0], [1.86, 1, 3, 0, -0.045, 0], [1.98, 0, 3, 0, -0.045, 0]);
    sh.push([1.42, 1, 0, 0, 0], [1.43, 0, 0, 0, 0]);
    return { lh, p_shell: sh, pump: [[0, 0], [1.62, 0], [1.7, 1], [1.74, 1], [1.8, 0]] };
  })(), events: [0, 1, 2, 3, 4, 5].map((i) => [0.42 + i * 0.2, 'shellIn']).concat([[1.68, 'pumpBack'], [1.8, 'pumpHome']]) },
  // ---- Sniper: bolt up and back (the empty flies), a stripper clip of five thumbed down into the action, clip
  // flicked away, bolt home and down
  sniper: { dur: 2.2, keys: [
    K(0), K(0.18, [-0.02, 0.03, 0.03], [0.12, -0.1, 0.9]),
    K(1.4, [-0.025, 0.03, 0.03], [0.12, -0.1, 0.93]), K(1.48, [-0.02, 0.035, 0.03], [0.17, -0.12, 0.85], 'snap'),
    K(1.62, [-0.02, 0.03, 0.03], [0.12, -0.1, 0.9]), K(1.8, [-0.02, 0.025, 0.04], [0.1, -0.08, 0.9], 'snap'), K(2.2),
  ], ch: { bolt: [[0, 0, 0], [0.2, 0, 0], [0.28, 1, 0], [0.4, 1, 1], [1.62, 1, 1], [1.72, 1, 0], [1.8, 0, 0]],
    lh: [[0.12, 0, 4, 0.03, 0.01, 0.0], [0.22, 1, 4, 0.03, 0.01, 0], [0.4, 1, 4, 0.03, 0.01, 0.12], [0.5, 0.6, 0, 0, 0.12, -0.02, 0, 0, 0], [0.62, 1, 0, 0, 0.13, -0.08, 0, 0, 0], [0.8, 1, 0, 0, 0.12, -0.08], [1.3, 1, 0, 0, 0.075, -0.08], [1.42, 1, 0, 0.04, 0.12, -0.08, 0, 0, -0.8], [1.52, 0.8, 4, 0.03, 0.02, 0.12], [1.62, 1, 4, 0.03, 0.01, 0.12], [1.72, 1, 4, 0.03, 0.01, 0], [1.82, 1, 4, 0.03, 0.0, 0], [1.95, 0, 4, 0.03, 0, 0]],
    p_clip: [[0.5, 1, 0, -0.02, 0], [0.84, 1, 0, -0.02, 0], [0.9, 1, 0, -0.03, 0], [1.3, 0.25, 0, -0.03, 0], [1.42, 0.0001, 0, -0.03, 0], [1.5, 0.0001, 0.1, 0.08, 0, 0, 0, 2.5], [1.52, 0, 0.1, 0.08, 0]] },
  events: [[0.28, 'boltUp'], [0.4, 'boltBack'], [0.42, 'shell'], [0.92, 'shellIn'], [1.02, 'shellIn'], [1.12, 'shellIn'], [1.22, 'shellIn'], [1.3, 'shellIn'], [1.44, 'clipFlick'], [1.72, 'boltHome'], [1.8, 'boltDown']] },
  // ---- Redline: pit stop. a jerry can glugs into the filler, then a twist of the wrist revs it into the red
  redline: { dur: 1.8, keys: [
    K(0), K(0.2, [-0.04, 0.04, 0.02], [0.22, 0.3, 0.5]), K(1.12, [-0.04, 0.042, 0.02], [0.24, 0.3, 0.52]),
    K(1.28, [0, 0.01, 0.01], [0.04, 0.05, 0]), K(1.36, [0, 0.016, 0.02], [0.1, 0.05, -0.22], 'snap'), // rev...
    K(1.46, [0.004, 0.012, 0.02], [0.08, 0.05, -0.18]), K(1.52, [-0.002, 0.016, 0.02], [0.11, 0.05, -0.24]), K(1.8),
  ], ch: { needle: [[0, 0], [1.3, 0], [1.42, 1], [1.46, 0.9], [1.5, 1], [1.56, 0.92], [1.76, 0]],
    lh: [[0.18, 0, 0, 0, 0.12, -0.04, 0, 0, -0.6], [0.36, 1, 0, -0.02, 0.12, -0.04, 0, 0, -0.6], [0.48, 1, 0, -0.02, 0.11, -0.04, 0, 0, -1.6], [1.0, 1, 0, -0.02, 0.11, -0.04, 0, 0, -1.7], [1.12, 1, 0, -0.02, 0.12, -0.04, 0, 0, -0.6], [1.26, 0, 0, 0, 0.12, -0.04, 0, 0, -0.6]],
    p_can: [[0, 1, 0, 0, 0]] },
  events: [[0.5, 'glug'], [0.72, 'glug'], [0.94, 'glug'], [1.3, 'revUp'], [1.6, 'click']] },
  // ---- Minigun: the ammo box lid pops, a tiny arm climbs out, waves, shoves the new belt in, thumbs up, ducks back
  minigun: { dur: 3.5, keys: [
    K(0), K(0.35, [-0.11, 0.12, -0.02], [0.25, 0.62, -0.25]), K(3.0, [-0.11, 0.125, -0.02], [0.25, 0.63, -0.25]),
    K(3.12, [-0.11, 0.11, -0.02], [0.2, 0.62, -0.25], 'snap'), K(3.5),
  ], ch: {
    p_mlid: [[0, 1, 0, 0, 0, 0, 0, 0], [0.42, 1, 0, 0, 0, 0, 0, 0], [0.5, 1, 0, 0, 0, -1.6, 0, 0], [2.9, 1, 0, 0, 0, -1.6, 0, 0], [3.0, 1, 0, 0, 0, 0, 0, 0]],
    p_arm: [[0.5, 0, 0, -0.1, 0], [0.55, 1, 0, -0.1, 0, 0, 0, 0], [0.8, 1, 0, 0, 0, 0, 0, 0], // pops up
      [0.95, 1, 0, 0, 0, 0, 0, 0.6], [1.08, 1, 0, 0, 0, 0, 0, -0.4], [1.2, 1, 0, 0, 0, 0, 0, 0.6], [1.32, 1, 0, 0, 0, 0, 0, 0], // waves
      [1.5, 1, 0, 0, 0, -0.9, 0, 0.9], [1.7, 1, 0, 0, 0, -1.1, 0, 1.3], [2.1, 1, 0, 0, 0, -1.1, 0, 1.4], [2.3, 1, 0, 0, 0, -0.2, 0, 0.2], // shoves
      [2.45, 1, 0, 0.01, 0, 0, 0, 0], [2.7, 1, 0, 0.01, 0, 0, 0, 0], [2.88, 1, 0, -0.1, 0, 0, 0, 0], [2.9, 0, 0, -0.1, 0]],
    p_belt: [[0, 0, 0, 0, 0], [1.4, 0, 0, 0, 0], [1.42, 1, 0, 0, 0], [1.7, 1, -0.02, 0, 0], [2.1, 1, -0.11, 0, 0], [2.2, 1, -0.14, 0, 0], [2.22, 0, -0.14, 0, 0]],
    armFore: [[0, 0], [0.8, 0], [1.5, 0], [1.7, -0.9], [2.1, -0.2], [2.4, 0], [2.45, 0], [2.55, -2.2], [2.7, -2.2], [2.8, 0]],
  }, events: [[0.45, 'boxPop'], [0.7, 'tinyHi'], [1.0, 'tinyHi'], [1.7, 'tinyGrunt'], [2.0, 'tinyGrunt'], [2.18, 'belt'], [2.55, 'tinyYes'], [3.0, 'coverSlam'], [3.15, 'spin']] },
  // ---- Nail gun: a fresh strip slid up into the mag, then the little hammer bonks it home (three times, to be sure)
  nailgun: { dur: 1.9, keys: [
    K(0), K(0.2, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]),
    K(1.12, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]), K(1.15, [-0.07, 0.078, -0.04], [0.16, 0.38, 0.5], 'snap'), K(1.24, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]),
    K(1.32, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]), K(1.35, [-0.07, 0.078, -0.04], [0.16, 0.38, 0.5], 'snap'), K(1.44, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]),
    K(1.52, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]), K(1.55, [-0.07, 0.082, -0.04], [0.18, 0.38, 0.5], 'snap'), K(1.64, [-0.07, 0.07, -0.04], [0.12, 0.38, 0.5]), K(1.9),
  ], ch: {
    lh: [[0.2, 0, 0, 0, -0.42, -0.36, 0.37], [0.4, 1, 0, 0, -0.36, -0.34, 0.37], [0.92, 1, 0, 0, -0.27, -0.3, 0.37], [0.98, 0.7, 0, 0, -0.32, -0.33, 0.37], // the strip goes up
      [1.06, 1, 0, 0, -0.36, -0.3, 0.37, 0, 0], [1.15, 1, 0, 0, -0.33, -0.29, 0.6, 0, 0], [1.24, 1, 0, 0, -0.37, -0.31, 0.2], // bonk
      [1.35, 1, 0, 0, -0.33, -0.29, 0.6], [1.44, 1, 0, 0, -0.37, -0.31, 0.2], [1.55, 1, 0, 0, -0.33, -0.29, 0.6], [1.66, 1, 0, 0, -0.38, -0.32, 0.2], [1.8, 0, 0, 0, -0.42, -0.36, 0.2]],
    p_strip: [[0, 1, 0, 0, 0], [0.92, 1, 0, 0, 0], [0.94, 0, 0, 0, 0]], p_hammer: [[0, 0, 0, 0, 0], [0.98, 0, 0, 0, 0], [1.0, 1, 0, 0, 0]],
  }, events: [[0.3, 'click'], [0.93, 'nailIn'], [1.15, 'bonk'], [1.35, 'bonk'], [1.55, 'bonkBig']] },
  // ---- Marble Shotgun: flip the jar lid, tip a whole bag of marbles in (a couple bounce out), lid shut, pat it
  marbles: { dur: 1.9, keys: [
    K(0), K(0.22, [-0.05, 0.02, 0.02], [0.05, 0.35, 0.3]), K(1.42, [-0.05, 0.022, 0.02], [0.06, 0.35, 0.3]),
    K(1.52, [-0.05, 0.014, 0.02], [0.02, 0.35, 0.3], 'snap'), K(1.62, [-0.05, 0.022, 0.02], [0.06, 0.35, 0.3]), K(1.9),
  ], ch: { lid: [[0, 0], [0.26, 0], [0.34, 1], [1.4, 1], [1.5, 0]],
    lh: [[0.24, 0, 0, 0.0, 0.25, -0.04, 0, 0, 0], [0.48, 1, 0, 0.0, 0.25, -0.04, 0, 0, 0], [0.62, 1, 0, 0.0, 0.24, -0.04, 0, 0, 2.2], [1.1, 1, 0, 0.0, 0.25, -0.04, 0, 0, 2.3], [1.16, 1, 0, 0.0, 0.26, -0.04, 0, 0, 2.6], [1.22, 1, 0, 0.0, 0.25, -0.04, 0, 0, 2.2], [1.3, 1, 0, 0, 0.25, -0.04, 0, 0, 0.4], [1.4, 0.7, 0, 0, 0.24, -0.04], [1.5, 1, 0, 0, 0.19, -0.04], [1.66, 0, 0, 0, 0.24, -0.04]],
    p_bag: [[0, 1, 0, 0, 0], [1.4, 1, 0, 0, 0], [1.41, 0, 0, 0, 0]] },
  events: [[0.34, 'click'], [0.66, 'marblePour'], [0.78, 'marblePour'], [0.9, 'marblePour'], [1.02, 'marblePour'], [1.12, 'marbleBounce'], [1.18, 'marblePour'], [1.5, 'thwack'], [1.53, 'click']] },
  // ---- Water Pistol: a juice box, straw in the filler, SQUEEZE (the tank fills), toss it, two pumps
  water: { dur: 1.6, keys: [
    K(0), K(0.18, [-0.04, 0.035, 0.02], [0.2, 0.4, 0.25]), K(1.0, [-0.04, 0.037, 0.02], [0.22, 0.4, 0.25]),
    K(1.14, [-0.01, 0.01, 0.01], [0.04, 0.1, 0.05]), K(1.6),
  ], ch: { fill: [[0, 0], [0.42, 0], [0.92, 1]], pump: [[0, 0], [1.14, 0], [1.22, 1], [1.3, 0], [1.38, 1], [1.46, 0]],
    lh: [[0.14, 0, 0, 0.01, 0.2, 0.02, 0, 0, 0.3], [0.34, 1, 0, 0.01, 0.2, 0.02, 0, 0, 0.3], [0.42, 1, 0, 0.005, 0.19, 0.02, 0, 0, 0.3], [0.94, 1, 0, 0.005, 0.19, 0.02, 0, 0, 0.3], [1.04, 0.4, 0, 0.1, 0.25, 0.05, 0, 0, -1.2], [1.12, 0.8, 3, 0, -0.035, 0, 0, 0, 0], [1.16, 1, 3, 0, -0.035, 0], [1.46, 1, 3, 0, -0.035, 0], [1.56, 0, 3, 0, -0.035, 0]],
    p_juice: [[0, 1, 0, 0, 0, 0, 0, 0, 1], [0.44, 1, 0, 0, 0, 0, 0, 0, 1], [0.92, 1, 0, 0, 0, 0, 0, 0, 0.35], [1.02, 1, 0, 0, 0, 0, 0, 0, 0.35], [1.04, 0, 0, 0, 0, 0, 0, 0, 0.35]] },
  events: [[0.44, 'slurp'], [0.66, 'squish'], [0.86, 'squish'], [1.04, 'toss'], [1.22, 'squeak'], [1.38, 'squeak']] },
  // ---- Reaper rifle: the blade swings open off the barrel, four glowing shells pushed in, SHING shut
  scythe_rifle: { dur: 1.8, keys: [
    K(0), K(0.2, [-0.07, 0.08, -0.05], [0.08, 0.5, 0.35]), K(1.3, [-0.07, 0.082, -0.05], [0.09, 0.5, 0.36]),
    K(1.4, [-0.02, 0.05, 0.0], [0.4, -0.2, 0.4], 'snap'), K(1.52, [-0.01, 0.02, 0.0], [0.05, -0.05, 0.05]), K(1.8),
  ], ch: { fold: [[0, 0], [0.24, 0], [0.36, 1], [1.32, 1], [1.4, 0]], bolt: [[0, 0, 0], [0.22, 0, 0], [0.28, 1, 0], [0.34, 1, 1], [1.26, 1, 1], [1.32, 1, 0], [1.38, 0, 0]],
    lh: [[0.3, 0, 0, -0.04, -0.12, -0.14], [0.52, 1, 0, 0, -0.1, -0.15], [0.62, 1, 0, 0, -0.075, -0.15], [0.7, 1, 0, 0, -0.09, -0.15], [0.8, 1, 0, 0, -0.075, -0.15], [0.88, 1, 0, 0, -0.09, -0.15], [0.98, 1, 0, 0, -0.075, -0.15], [1.06, 1, 0, 0, -0.09, -0.15], [1.16, 1, 0, 0, -0.075, -0.15], [1.28, 0, 0, 0, -0.12, -0.14]],
    p_souls: [[0, 1, 0, 0, 0], [0.62, 1, 0, 0, 0], [0.63, 0.75, 0, 0, 0], [0.8, 0.75, 0, 0, 0], [0.81, 0.5, 0, 0, 0], [0.98, 0.5, 0, 0, 0], [0.99, 0.25, 0, 0, 0], [1.16, 0.25, 0, 0, 0], [1.17, 0, 0, 0, 0]] },
  events: [[0.28, 'boltUp'], [0.34, 'boltBack'], [0.3, 'shing'], [1.32, 'boltHome'], [0.62, 'soulIn'], [0.8, 'soulIn'], [0.98, 'soulIn'], [1.16, 'soulIn'], [1.4, 'shingShut']] },
};
// where the props sit: on the off hand (hand space, metres) or on the gun (gun units). the minigun's bits sit on its box
const PROP_AT = {
  revolver: { speedloader: { at: 'hand', p: [0.006, 0.012, -0.042] }, crounds: { at: 'cyl', p: [0, 0, 0.03] } },
  shotgun: { shell: { at: 'hand', p: [0.004, 0.036, -0.036], r: [0.4, 0, 0] } },
  sniper: { clip: { at: 'hand', p: [0, 0.03, -0.02] } },
  redline: { can: { at: 'hand', p: [0.0, 0.04, -0.02] } },
  minigun: { mlid: { at: 'gun', p: [0.12, 0.012, 0.15] }, arm: { at: 'gun', p: [0.12, -0.01, 0.08] }, belt: { at: 'gun', p: [0.07, 0.015, 0.05] } },
  nailgun: { strip: { at: 'hand', p: [0, 0.07, -0.01], r: [0.37, 0, 0] }, hammer: { at: 'hand', p: [0.02, 0.01, -0.03], r: [0, 0, -0.3] } },
  marbles: { bag: { at: 'hand', p: [0, 0.035, -0.02] } },
  water: { juice: { at: 'hand', p: [0, 0.03, -0.01] } },
  scythe_rifle: { souls: { at: 'hand', p: [0, 0.03, -0.015] } },
};
export const RELOADS = new Set(Object.keys(RL));
for (const [id, a] of Object.entries(RL)) {
  const last = a.keys[a.keys.length - 1].t, want = WEAPONS[id] && WEAPONS[id].reload;
  if (Math.abs(last - a.dur) > 1e-6 || (want && Math.abs(want - a.dur) > 1e-6)) console.warn('reload_' + id, 'is', last, 's, the gun reloads in', want);
  ANIMS['reload_' + id] = a;
}

// ------------------------------------------------------------ per model: find the parts, build the props + off hand
const find = (g, n) => (n ? g.getObjectByName(n) : null);
function bind(m, id) {
  const g = m.g;
  if (g.userData.rl && g.userData.rl.id === id) return g.userData.rl;
  const ud = g.userData, gp = ud.parts || {}, b = { id, props: {} };
  b.mag = ud.mag || find(g, 'mag'); b.charge = ud.charge || find(g, 'charge');
  b.pump = gp.pump || ud.pump || find(g, 'pump'); b.bolt = gp.bolt || null; b.cyl = gp.cyl || find(g, 'cyl');
  b.lid = find(g, 'lid'); b.fold = [find(g, 'fold'), find(g, 'fold2'), find(g, 'folded_wzB')].filter(Boolean); // (code model / Blender model) b.water = ud.water || null;
  for (const k of ['mag', 'charge', 'pump', 'bolt', 'cyl', 'lid', ...b.fold.map((_, i) => 'f' + i)]) {
    const o = k[0] === 'f' && k.length === 2 ? b.fold[Number(k[1])] : b[k];
    if (o) o.userData.rl0 = o.userData.rl0 || { p: o.position.clone(), r: o.rotation.clone() };
  }
  if (b.fold.length) { // hinge: the back end of the blade, on its bottom edge (gun space)
    g.updateMatrixWorld(true); bbA.makeEmpty(); for (const o of b.fold) bbA.expandByObject(o);
    const lo = bbA.min.clone(), hi = bbA.max.clone(); g.worldToLocal(lo); g.worldToLocal(hi);
    b.pin = [0, Math.min(lo.y, hi.y), Math.max(lo.z, hi.z)];
  }
  // the off hand: a fist with a thumb and a bit of forearm trailing back off screen
  const h = new THREE.Group(), SK = 0xf1c27d;
  h.add(box(0.036, 0.042, 0.058, SK), box(0.014, 0.016, 0.04, 0xe3ae68, 0.021, 0.016, -0.024));
  h.visible = false; m.wrap.add(h); b.hand = h;
  const fa = new THREE.Group(), fm = cyl(0.022, 0.3, SK, 0, 0.15, 0, 7); fa.add(fm); fa.add(cyl(0.025, 0.026, 0xff4fd8, 0, 0.04, 0, 7)); // forearm (+ the sweatband)
  fa.visible = false; m.wrap.add(fa); b.fore = fa;
  for (const [name, at] of Object.entries(PROP_AT[id] || {})) {
    const o = PROPS[name](); o.visible = false;
    o.userData.base = { p: new THREE.Vector3(...(at.p || [0, 0, 0])), r: new THREE.Euler(...(at.r || [0, 0, 0])), s: o.scale.x };
    (at.at === 'gun' ? g : at.at === 'cyl' && b.cyl ? b.cyl : h).add(o);
    b.props[name] = o;
  }
  g.userData.rl = b;
  return b;
}

const FOLD_PIN = [0, 0, 0], bbA = new THREE.Box3(); // the reaper blade's hinge (gun units): its back end, worked out per model
const tA = new THREE.Vector3(), tB = new THREE.Vector3(), eA = new THREE.Euler(), qA = new THREE.Quaternion(), REST = new THREE.Vector3(-0.1, -0.5, -0.2), SHOULDER = new THREE.Vector3(-0.34, -0.6, 0.1), UPV = new THREE.Vector3(0, 1, 0);
const rest = (o) => { const r = o.userData.rl0; o.position.copy(r.p); o.rotation.copy(r.r); };
// a spot (gun units) on one of the parts the hand can follow
function anchor(b, g, f, out) { // (Blender parts sit a group or two down inside g: go through the world)
  const o = [null, b.mag, b.charge, b.pump, b.bolt, b.cyl][f];
  if (!o) return out.set(0, 0, 0);
  o.getWorldPosition(out); return g.worldToLocal(out);
}

// every frame for these guns, after the code + Blender part steppers (so a reload wins over the resting pose)
export function reloadStep(m, id, an, at, sampleCh, W) {
  if (!RELOADS.has(id)) return;
  const b = bind(m, id), g = m.g, mine = an === 'reload_' + id;
  const ch = (n) => (mine ? sampleCh(an, n, at) : null);
  // ---- the gun's own parts
  if (b.mag) { rest(b.mag); const v = ch('mag'); if (v) { b.mag.position.y += v[0]; b.mag.position.z += v[1]; b.mag.rotation.x += v[2]; } b.mag.visible = !v || v[0] > -0.3; }
  if (b.charge) { rest(b.charge); const v = ch('charge'); if (v) b.charge.position.z += v[0]; }
  if (b.pump && mine) { const v = ch('pump'); if (v) { rest(b.pump); b.pump.position.z += v[0] * (id === 'water' ? 0.035 : (g.userData.parts && g.userData.parts.travel) || 0.09); } }
  if (b.bolt && mine && g.userData.parts) { const v = ch('bolt'); const gp = g.userData.parts; if (v) { b.bolt.rotation.z = v[0] * gp.lift; b.bolt.position.z = gp.bolt0 + v[1] * gp.btravel; } }
  if (b.cyl) { // out on the crane (a pin under it, parallel to the bore): swings down and to the left
    const v = ch('cyl'), r = b.cyl.userData.rl0, th = v ? v[0] * 1.2 : 0, R = 0.034;
    b.cyl.position.set(r.p.x - R * Math.sin(th), r.p.y + R * Math.cos(th) - R, r.p.z + (v ? v[0] * 0.004 : 0));
    if (v && v[1] && g.userData.parts && g.userData.parts.cyl === b.cyl) b.cyl.rotation.z -= v[1];
  }
  if (b.lid) { rest(b.lid); const v = ch('lid'); if (v) { b.lid.rotation.z = v[0] * 2.2; b.lid.position.x -= Math.sin(v[0] * 1.1) * 0.03; b.lid.position.y += Math.sin(v[0] * 2.2) * 0.02; } }
  if (b.fold.length) { // the folded blade swings down off the barrel round its back end
    const v = ch('fold'), a = v ? v[0] * 0.38 : 0, FP = b.pin || FOLD_PIN;
    for (const o of b.fold) { // round a hinge at the blade's back end, whatever the node's own origin is
      const r = o.userData.rl0, dy = r.p.y - FP[1], dz = r.p.z - FP[2], c = Math.cos(-a), sn = Math.sin(-a);
      o.position.set(r.p.x, FP[1] + dy * c - dz * sn, FP[2] + dy * sn + dz * c); o.rotation.set(r.r.x - a, r.r.y, r.r.z);
    }
  }
  if (b.water) { const v = ch('fill'); if (v) { const w = WEAPONS.water, k0 = Math.max(0.04, Math.min(1, (W.ammo.water ?? w.mag) / w.mag)); b.water.scale.y = k0 + (1 - k0) * v[0]; } } // (secondaries.js eases it back to the ammo after)
  if (g.userData.needle) { const v = ch('needle'); if (v) g.userData.needle.rotation.x = -2.3 + 4.6 * Math.min(1, v[0]); }
  // ---- the off hand
  const lh = ch('lh'), h = b.hand;
  if (lh) m.wrap.updateMatrixWorld(true);
  h.visible = !!(lh && lh[0] > 0.01 && m.wrap.visible);
  if (h.visible) {
    const f = Math.max(0, Math.min(5, lh[1])), f0 = Math.floor(f), f1 = Math.min(5, f0 + 1), u = f - f0;
    anchor(b, g, f0, tA); anchor(b, g, f1, tB); tA.lerp(tB, u);
    tA.x += lh[2]; tA.y += lh[3]; tA.z += lh[4];
    tA.applyMatrix4(g.matrix); // gun units -> wrap space
    tB.copy(REST); m.wrap.parent.localToWorld(tB); m.wrap.worldToLocal(tB); // (where it waits: camera space, low left)
    h.position.copy(tB).lerp(tA, Math.min(1, lh[0]));
    eA.set(lh[5] || 0, lh[6] || 0, lh[7] || 0); qA.setFromEuler(eA);
    h.quaternion.copy(g.quaternion).multiply(qA);
    // the forearm runs from the wrist back to your left shoulder (off screen), so the hand never floats
    m.wrap.updateMatrixWorld(true);
    tB.copy(SHOULDER); m.wrap.parent.localToWorld(tB); m.wrap.worldToLocal(tB);
    tB.sub(h.position).normalize();
    b.fore.position.copy(h.position).addScaledVector(tB, 0.02); b.fore.quaternion.setFromUnitVectors(UPV, tB);
  }
  b.fore.visible = h.visible;
  // ---- props
  for (const [name, o] of Object.entries(b.props)) {
    const v = ch('p_' + name), base = o.userData.base;
    o.visible = !!(v && v[0] > 0 && (o.parent !== h || h.visible) && m.wrap.visible);
    if (!o.visible) continue;
    o.position.copy(base.p); o.rotation.copy(base.r);
    o.position.x += v[1] || 0; o.position.y += v[2] || 0; o.position.z += v[3] || 0;
    o.rotation.x += v[4] || 0; o.rotation.y += v[5] || 0; o.rotation.z += v[6] || 0;
    o.scale.set(base.s, base.s * (v[7] || 1), base.s);
    const rs = o.userData.rounds; if (rs) { const n = Math.round(v[0] * rs.length); rs.forEach((r, i) => { r.visible = i < n; }); }
    if (name === 'arm') { const fv = ch('armFore'); o.userData.fore.rotation.x = fv ? fv[0] : 0; }
  }
}

// ------------------------------------------------------------ sounds + bits flying (weapons.js animEvent passes these on)
const pV = new THREE.Vector3();
export function reloadEvent(ev, g) {
  const sys = G.skinFxVM, R = (k) => (Math.random() - 0.5) * k, b = g.userData.rl;
  const at = (o, x = 0, y = 0, z = 0) => { g.updateMatrixWorld(true); pV.set(x, y, z); if (o) o.localToWorld(pV); else g.localToWorld(pV); return pV; };
  switch (ev) {
    case 'casings': // six empties drop out of the back of the cylinder
      sfx.reloadFx('casings');
      if (sys && b && b.cyl) { at(b.cyl, 0, 0, 0.04); for (let i = 0; i < 6; i++) sys.norm.spawn(pV.x + R(0.02), pV.y + R(0.02), pV.z + R(0.02), R(0.3), -0.2 - Math.random() * 0.3, 0.2 + R(0.2), 0.8, 0.012, 0.011, 0xd9a53a, 0xb8862a, 1, 4, 0.2); }
      break;
    case 'marblePour': case 'marbleBounce': { // marbles rattle out of the bag into the jar (and one or two bounce out)
      sfx.marble(); sfx.marble();
      if (!sys || !b || !b.hand) break;
      b.hand.updateMatrixWorld(true); pV.set(0, 0.0, -0.03); b.hand.localToWorld(pV);
      const out = ev === 'marbleBounce';
      for (let i = 0; i < (out ? 2 : 4); i++) { const c = MARBLES[(Math.random() * 7) | 0]; sys.norm.spawn(pV.x + R(0.015), pV.y, pV.z + R(0.015), out ? R(0.8) + 0.3 : R(0.05), out ? 0.6 : -0.4, out ? R(0.6) : R(0.05), out ? 0.9 : 0.35, 0.011, 0.011, c, c, 1, out ? 4 : 2, 0.1); }
      if (out) sfx.reloadFx('boing');
      break;
    }
    case 'glug': sfx.reloadFx('glug'); break;
    case 'slurp': sfx.reloadFx('slurp'); break;
    case 'squish': sfx.reloadFx('squish'); if (sys && b && b.hand) { b.hand.updateMatrixWorld(true); pV.set(0.012, 0.09, -0.01); b.hand.localToWorld(pV); for (let i = 0; i < 4; i++) sys.norm.spawn(pV.x, pV.y, pV.z, R(0.3), 0.3 + Math.random() * 0.3, R(0.3), 0.4, 0.006, 0.003, 0xff6ad8, 0xff4fd8, 1, 3, 0.2); } break;
    case 'toss': case 'clipFlick': sfx.swing(); break;
    case 'nailIn': case 'boltUp': case 'boltDown': case 'cylOut': case 'cylIn': case 'loaderIn': case 'loaderTwist': case 'pumpBack': case 'pumpHome': case 'hkSlap': case 'boltBack': case 'boltHome': case 'spinCyl': case 'bonk': case 'bonkBig': case 'boxPop': case 'tinyHi': case 'tinyGrunt': case 'tinyYes': case 'soulIn': case 'shingShut': case 'revUp': case 'latch': case 'balClack':
      sfx.reloadFx(ev);
      if (ev === 'bonkBig' && sys && b && b.hand) { b.hand.updateMatrixWorld(true); pV.set(0.02, 0.08, -0.03); b.hand.localToWorld(pV); for (let i = 0; i < 7; i++) sys.add.spawn(pV.x, pV.y, pV.z, R(0.6), R(0.6), R(0.6), 0.25, 0.012, 0.002, 0xffe14d, 0xff7a1a); }
      if (ev === 'soulIn' && sys && b && b.hand) { b.hand.updateMatrixWorld(true); pV.set(0, 0.05, -0.02); b.hand.localToWorld(pV); for (let i = 0; i < 6; i++) sys.add.spawn(pV.x + R(0.02), pV.y, pV.z + R(0.02), R(0.1), 0.15 + Math.random() * 0.2, R(0.1), 0.5, 0.012, 0.002, 0x3ee6c8, 0x1a6a5a); }
      break;
    default: return false;
  }
  return true;
}
