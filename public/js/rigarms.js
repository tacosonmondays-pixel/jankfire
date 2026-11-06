// Overdrive Rig killstreak, first person: your guns are holstered and two giant mechanical forearms + fists fill the
// bottom of the screen. Servo sway and twitches, a heavy dip on every footstep, the wind-up (the fist pulled back,
// glowing, shaking harder as it charges), the rocket punch, the forearms crossed to block, a glance at the wrist deck to
// hack. The keyframes are the rig_* entries in anim.js; rig.js says what's going on.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { G } from './ctx.js';
import { ANIMS, sample, eventsBetween } from './anim.js';
import { jankify } from './jank.js';
import { cbox, taper, cyl, cylZ, C, NEON, glowTexture, screenTex, drawScreen } from './rigmodel.js';

const mats = new Map();
function lam(color, emi = 0.1) {
  const k = color + ':' + emi;
  if (!mats.has(k)) mats.set(k, jankify(new THREE.MeshLambertMaterial({ color, flatShading: true, emissive: new THREE.Color(color).multiplyScalar(emi) })));
  return mats.get(k);
}
function shiny(color) {
  const k = 's' + color;
  if (!mats.has(k)) mats.set(k, jankify(new THREE.MeshPhongMaterial({ color, specular: 0xe8f0ff, shininess: 80, flatShading: true, emissive: new THREE.Color(color).multiplyScalar(0.08) })));
  return mats.get(k);
}
let accent = null;
function accentMat() { if (!accent) accent = jankify(new THREE.MeshLambertMaterial({ color: G.myColor || '#ff4fd8', flatShading: true, emissive: new THREE.Color(G.myColor || '#ff4fd8').multiplyScalar(0.25) })); return accent; }
const basic = (color) => { const k = 'b' + color; if (!mats.has(k)) mats.set(k, new THREE.MeshBasicMaterial({ color })); return mats.get(k); };
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _p = new THREE.Vector3(), _one = new THREE.Vector3(1, 1, 1);

// one forearm + fist. built along -z from the elbow (just under the bottom of the screen) to the knuckles
function buildArm(s) {
  const big = s > 0; // the right arm punches; the left one wears the hack deck
  const root = new THREE.Group(), fist = new THREE.Group();
  root.rotation.order = 'YXZ';
  fist.position.set(0, 0, -0.64);
  root.add(fist);
  const groups = new Map();
  const put = (grp, geo, mat, x, y, z, r = [0, 0, 0]) => {
    _m.compose(_p.set(x * s, y, z), _q.setFromEuler(_e.set(r[0], r[1] * s, r[2] * s)), _one);
    const g = geo.index ? geo.toNonIndexed() : geo;
    g.applyMatrix4(_m);
    if (g.attributes.uv) g.deleteAttribute('uv');
    if (g.attributes.normal) g.deleteAttribute('normal');
    const key = grp.uuid;
    if (!groups.has(key)) groups.set(key, { grp, by: new Map() });
    const by = groups.get(key).by;
    if (!by.has(mat)) by.set(mat, []);
    by.get(mat).push(g);
  };
  // forearm: a tapered industrial ram that swells toward the fist. from first person you see its top and inner side,
  // so that's where the detail is: three overlapping armour plates (salvage, all different), rivet rows, hazard
  // chevrons, a stripe in your colour, ribs, a neon strip down the inside
  const ac = accentMat();
  put(root, taper(cbox(0.13, 0.14, 0.62, 0.025), 1.38, 1.32), lam(C.gun), 0, 0, -0.31);
  const plates = big ? [[C.steel, -0.2, 0.16], [C.ochre, -0.36, 0.17], [C.rust, -0.52, 0.18]] : [[C.olive, -0.2, 0.16], [C.steel, -0.36, 0.17], [C.teal, -0.52, 0.18]];
  plates.forEach(([c, z, w], i) => {
    put(root, cbox(w, 0.03, 0.17, 0.012), lam(c, 0.14), 0, 0.083 + i * 0.006, z, [0.09, 0, 0]);
    for (const x of [-1, 1]) put(root, new THREE.SphereGeometry(0.0075, 5, 3), shiny(C.chrome), x * (w / 2 - 0.016), 0.1 + i * 0.006, z + 0.06);
  });
  put(root, cbox(0.03, 0.005, 0.15, 0.002), ac, 0.045, 0.106, -0.36, [0.09, 0, 0]); // your colour
  if (big) for (let i = 0; i < 4; i++) put(root, new THREE.BoxGeometry(0.014, 0.004, 0.034), lam(C.black, 0.02), -0.03, 0.105, -0.39 + i * 0.022, [0.09, 0.7, 0]); // hazard chevrons on the ochre plate
  put(root, cbox(0.03, 0.13, 0.42, 0.01), lam(big ? C.steel : C.olive), 0.098, 0, -0.36);
  put(root, cbox(0.03, 0.1, 0.3, 0.01), lam(big ? C.rust : C.steel, 0.12), -0.085, -0.005, -0.42); // the inner side: the one you see
  put(root, new THREE.BoxGeometry(0.012, 0.012, 0.36), basic(NEON.mag), 0.116, 0.05, -0.36);
  put(root, new THREE.BoxGeometry(0.008, 0.012, 0.3), basic(NEON.cyan), -0.102, 0.03, -0.42);
  for (let i = 0; i < 3; i++) put(root, cbox(0.175 + i * 0.016, 0.175 + i * 0.016, 0.016, 0.006), lam(C.black, 0.02), 0, 0, -0.1 - i * 0.05);
  put(root, cbox(0.12, 0.12, 0.07, 0.02), lam(C.black, 0.02), 0, 0, -0.63); // wrist joint
  put(root, cylZ(0.05, 0.03, 10), shiny(C.chrome), 0, 0, -0.61); // wrist bearing
  // thrusters on the outer side, pointing back: they fire on the punch dash
  for (const z of [-0.1, -0.22]) put(root, cyl(0.022, 0.03, 0.05, 8).rotateX(Math.PI / 2 - 0.4), lam(C.gun), 0.11, -0.03, z);
  if (big) for (let i = 0; i < 5; i++) put(root, new THREE.TorusGeometry(0.022, 0.007, 4, 8), lam(C.steel), -0.05 + i * 0.026, 0.07 - (i % 2) * 0.006, -0.56 - (i % 2) * 0.012, [i % 2 ? 0 : Math.PI / 2, 0.4, 0]); // a chain wrapped round the wrist
  else { // the hack deck: a screen on the inner side of the forearm, angled up at you
    put(root, cbox(0.03, 0.12, 0.18, 0.01), lam(C.black, 0.02), -0.088, 0.03, -0.3, [0, 0, 0.5]);
    put(root, new THREE.BoxGeometry(0.008, 0.012, 0.18), basic(NEON.cyan), -0.1, 0.095, -0.3);
  }
  // fist: big (comic proportions: the fists are the show), knuckle block, four chunky fingers curled under, a thumb
  // over the inside, a knuckle plate in your colour with chrome studs and a glow strip
  const F = 1.35;
  put(fist, cbox(0.19 * F, 0.13 * F, 0.15 * F, 0.025), lam(C.steel), 0, 0, -0.03);
  put(fist, cbox(0.17 * F, 0.02, 0.1 * F, 0.008), lam(C.gun), 0, 0.07 * F, -0.02); // back-of-hand plate
  for (let i = 0; i < 4; i++) {
    const x = (-0.068 + i * 0.045) * F;
    put(fist, cbox(0.04 * F, 0.05 * F, 0.055 * F, 0.012), lam(C.gun), x, -0.035 * F, -0.12 * F, [-0.4, 0, 0]);
    put(fist, cbox(0.04 * F, 0.045 * F, 0.045 * F, 0.012), lam(C.gun), x, -0.075 * F, -0.09 * F, [-1.2, 0, 0]);
    put(fist, new THREE.SphereGeometry(0.016 * F, 6, 4), lam(C.black, 0.02), x, -0.012 * F, -0.1 * F); // knuckle joints
  }
  put(fist, cbox(0.05 * F, 0.05 * F, 0.09 * F, 0.012), lam(C.gun), -0.105 * F, -0.02 * F, -0.07 * F, [0, 0.4, 0.3]);
  put(fist, cbox(0.2 * F, 0.045 * F, 0.06 * F, 0.012), ac, 0, 0.03 * F, -0.11 * F, [-0.25, 0, 0]);
  for (let i = 0; i < 4; i++) put(fist, new THREE.ConeGeometry(0.013 * F, 0.04 * F, 4).rotateX(-Math.PI / 2), shiny(C.chrome), (-0.068 + i * 0.045) * F, 0.03 * F, -0.155 * F);
  // bake: one mesh per material per group
  for (const { grp, by } of groups.values()) for (const [mat, list] of by) {
    const g = mergeGeometries(list, false);
    g.computeVertexNormals();
    grp.add(new THREE.Mesh(g, mat));
  }
  // own (animated) bits: the glowing knuckle strip, its glow, the piston rod, the thruster flames, the deck screen
  const glow = new THREE.MeshBasicMaterial({ color: 0x4a0f3e });
  const strip = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.014, 0.014), glow);
  strip.position.set(0, 0.072, -0.17); strip.rotation.x = -0.25; fist.add(strip);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: NEON.mag, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0 }));
  sprite.position.set(0, 0.04, -0.23); sprite.scale.setScalar(0.001); fist.add(sprite);
  const body = new THREE.Mesh(cylZ(0.016, 0.3).translate(0, 0, -0.15), shiny(0x7f8892));
  body.position.set(-0.075 * s, 0.035, -0.04); root.add(body);
  const rod = new THREE.Mesh(cylZ(0.009, 0.3).translate(0, 0, -0.15), shiny(C.chrome));
  rod.position.set(-0.075 * s, 0.035, -0.24); root.add(rod);
  const flames = [-0.1, -0.22].map((z) => {
    const f = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.22, 6, 1, true).translate(0, 0.11, 0).rotateX(Math.PI / 2 - 0.4),
      new THREE.MeshBasicMaterial({ color: 0xff7ae8, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    f.position.set(0.125 * s, -0.03, z + 0.02); f.visible = false; root.add(f);
    return f;
  });
  let screen = null;
  if (!big) {
    screen = new THREE.MeshBasicMaterial({ map: screenTex() });
    const sc = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.1), screen);
    sc.rotation.y = Math.PI / 2; sc.rotateX(-0.5); sc.position.set(0.106, 0.035, -0.3); root.add(sc); // (mirrored: on the inner side)
  }
  root.traverse((o) => { if (o.isMesh || o.isSprite) { o.frustumCulled = false; o.renderOrder = 2; } });
  root.scale.setScalar(SCALE);
  return { s, root, fist, glow, sprite, rod, flames, screen, bob: 0, bobV: 0, kick: 0, kickV: 0, twitch: [0, 0, 0], twitchT: 0 };
}

// ------------------------------------------------------------ the pair, and what they're doing
let arms = null;
// at rest the fists sit low left / right, knuckles forward, forearms running back out of the bottom corners
const REST = { p: [0.36, -0.33, -0.1], r: [0.26, 0.26, 0.14] }, SCALE = 0.78;
const anims = [];
let punchFrom = null, hidden = true, t0 = 0;
export function armsReady() {
  if (arms || !G.vmScene) return !!arms;
  const grp = new THREE.Group();
  arms = { grp, R: buildArm(1), L: buildArm(-1) };
  grp.add(arms.R.root, arms.L.root);
  grp.visible = false;
  G.vmScene.add(grp);
  return true;
}
export const armsObj = () => arms; // (pose sheets)
export function playArms(name, k = 1) { if (ANIMS[name]) { anims.push({ name, t: 0, k }); if (name === 'rig_punch' && arms) punchFrom = arms.charge || null; } }
export function armsOn() { if (!armsReady()) return; if (accent) { accent.color.set(G.myColor || '#ff4fd8'); accent.emissive.set(G.myColor || '#ff4fd8').multiplyScalar(0.25); } hidden = false; arms.grp.visible = true; anims.length = 0; playArms('rig_on'); }
export function armsOff() { if (!arms) return; anims.length = 0; playArms('rig_off'); hidden = true; }
export function armsHide() { if (arms) { arms.grp.visible = false; anims.length = 0; hidden = true; } }
// a heavy footstep: both arms dip, the one on that side a bit more
export function armsStep(side, k = 1) { if (!arms) return; for (const A of [arms.R, arms.L]) A.bobV -= (A.s === side ? 0.5 : 0.32) * k; }
export function armsJolt(k = 1) { if (!arms) return; arms.R.kickV += 0.9 * k; arms.L.kickV += 0.9 * k; }

const _w = new THREE.Vector3();
const R = (k) => (Math.random() - 0.5) * k;
// st: { charge 0..1, charging, block, dash, hack, speed, run (0..1), phase (gait), swayX, swayY, visible }
// returns events crossed this frame (for sounds)
export function updateArms(dt, st, onEvent) {
  if (!arms) return;
  t0 += dt;
  const { R: AR, L: AL } = arms;
  // anims: advance, drop the finished ones (rig_off hides the arms when it's done)
  const off = [];
  for (let i = anims.length - 1; i >= 0; i--) {
    const a = anims[i], was = a.t;
    a.t += dt;
    for (const ev of eventsBetween(a.name, was, a.t)) if (onEvent) onEvent(ev);
    if (a.t >= ANIMS[a.name].dur) { anims.splice(i, 1); if (a.name === 'rig_off') arms.grp.visible = false; if (a.name === 'rig_punch') punchFrom = null; }
  }
  void off;
  if (hidden && !anims.some((a) => a.name === 'rig_off')) { arms.grp.visible = false; return; }
  arms.grp.visible = st.visible !== false;
  const cw = arms.cw = (arms.cw || 0) + ((st.charging ? 1 : 0) - (arms.cw || 0)) * Math.min(1, dt * 14);
  const bw = arms.bw = (arms.bw || 0) + ((st.block ? 1 : 0) - (arms.bw || 0)) * Math.min(1, dt * 16);
  const lw = arms.lw = (arms.lw || 0) + ((st.leap || 0) - (arms.lw || 0)) * Math.min(1, dt * 12);
  const ck = Math.max(0, Math.min(1, st.charge || 0));
  for (const A of [AR, AL]) {
    const s = A.s, isR = s > 0;
    // springs: the footstep dip and the blocked-hit kick
    // (substepped: one big step on a slow frame would blow the springs up)
    const ns = Math.min(40, Math.max(1, Math.ceil(dt * 240))), h = dt / ns;
    for (let i = 0; i < ns; i++) {
      A.bobV += (-260 * A.bob - 20 * A.bobV) * h; A.bob += A.bobV * h;
      A.kickV += (-300 * A.kick - 22 * A.kickV) * h; A.kick += A.kickV * h;
    }
    // servo twitch: every now and then a joint steps a hair and holds, like a cheap servo hunting
    A.twitchT -= dt;
    if (A.twitchT <= 0) { A.twitchT = 0.7 + Math.random() * 1.6; A.twitch = [R(0.008), R(0.006), R(0.03)]; }
    const p = [REST.p[0] * s, REST.p[1], REST.p[2]], r = [REST.r[0], REST.r[1] * s, REST.r[2] * s];
    // breathing sway, mouse lag, pumping when you run, the footstep dip
    const br = t0 * 1.4 + (isR ? 0 : 1.7);
    p[0] += Math.sin(br) * 0.004 + (st.swayX || 0) * 0.22 + A.twitch[0];
    p[1] += Math.sin(br * 1.3) * 0.004 - (st.swayY || 0) * 0.14 + A.bob * 0.16 + A.twitch[1];
    r[2] += A.twitch[2] + (st.swayX || 0) * 0.6 * s;
    const pump = Math.sin((st.phase || 0) * Math.PI * 2 + (isR ? 0 : Math.PI)) * (st.run || 0);
    p[2] += pump * 0.06; p[1] += Math.abs(pump) * 0.012; r[0] += pump * 0.12;
    p[2] += A.kick * 0.25; r[0] -= A.kick * 0.9;
    // the wind-up (right): pulled back toward you, up, and shaking harder the more it's charged
    if (isR && cw > 0.01) {
      const j = ck * ck * 0.014;
      const cp = [0.05 + R(j), -0.05 - ck * 0.02 + R(j), 0.1 + ck * 0.04 + R(j)], cr = [0.08 + ck * 0.06 + R(j * 6), 0.1 + ck * 0.05, 0.3 + ck * 0.1 + R(j * 6)];
      for (let i = 0; i < 3; i++) { p[i] += cp[i] * cw; r[i] += cr[i] * cw; }
      arms.charge = { p: cp.map((x) => x * cw), r: cr.map((x) => x * cw) };
    } else if (isR) arms.charge = null;
    if (isR && punchFrom) { // the punch starts from where the wind-up left the fist
      const a = anims.find((x) => x.name === 'rig_punch'), k = a ? Math.max(0, 1 - a.t / 0.06) : 0;
      for (let i = 0; i < 3; i++) { p[i] += punchFrom.p[i] * k; r[i] += punchFrom.r[i] * k; }
    }
    // block: the two forearms crossed in front of you, low enough to see over
    if (bw > 0.01) {
      const bp = [-0.09 * s, isR ? -0.08 : -0.1, isR ? -0.13 : -0.1], brr = [0.05, 0.62 * s, -0.75 * s];
      for (let i = 0; i < 3; i++) { p[i] += bp[i] * bw; r[i] += brr[i] * bw; }
    }
    // leap wind-up: both pulled down and back
    if (lw > 0.01) { p[1] -= 0.1 * lw; p[2] += 0.1 * lw; r[0] += 0.38 * lw; p[0] += 0.03 * s * lw; }
    for (const a of anims) {
      const spec = ANIMS[a.name];
      if (spec.arm !== 'both' && (spec.arm === 'r') !== isR) continue;
      const o = sample(a.name, a.t);
      if (!o) continue;
      const m = spec.arm === 'both' ? s : 1, k = a.k;
      p[0] += o.p[0] * m * k; p[1] += o.p[1] * k; p[2] += o.p[2] * k;
      r[0] += o.r[0] * k; r[1] += o.r[1] * m * k; r[2] += o.r[2] * m * k;
    }
    A.root.position.set(p[0], p[1], p[2]);
    A.root.rotation.set(r[0], r[1], r[2]);
    // the piston rod slides out as the fist cocks back
    A.rod.position.z = -0.24 + (isR ? cw * 0.06 : 0) - bw * 0.03;
    // glow: dull magenta -> white-hot at full charge (and a flash on the punch)
    const pa = isR ? anims.find((x) => x.name === 'rig_punch') : null;
    const g = isR ? Math.max(ck * cw, pa ? Math.max(0, 1 - pa.t / 0.4) : 0) : (st.hack ? 0.6 : 0);
    if (isR && ck >= 1 && cw > 0.5) A.glow.color.setRGB(1, 0.8 + Math.random() * 0.2, 1);
    else A.glow.color.setRGB(0.29 + 0.71 * g, 0.06 + 0.25 * g * g, 0.24 + 0.6 * g);
    A.sprite.material.opacity = Math.min(1, g * 1.2);
    A.sprite.scale.setScalar(0.001 + g * (0.16 + (ck >= 1 && cw > 0.5 ? Math.random() * 0.06 : 0)));
    if (isR && g > 0.5 && Math.random() < dt * 40 * g && G.skinFxVM) { // sparks crawling off the charged fist
      A.sprite.getWorldPosition(_w);
      G.skinFxVM.add.spawn(_w.x + R(0.08), _w.y + R(0.05), _w.z + R(0.05), R(0.6), 0.2 + Math.random() * 0.4, R(0.4), 0.25 + Math.random() * 0.2, 0.02, 0, Math.random() < 0.5 ? 0xffffff : NEON.mag, 0x401040, 1, 1.5, 1);
    }
    // thrusters fire through the punch dash
    const fire = isR && (st.dash || (pa && pa.t < 0.2));
    for (const f of A.flames) { f.visible = !!fire; if (fire) f.scale.set(1 + R(0.4), 0.8 + Math.random() * 0.8, 1 + R(0.4)); }
    if (A.screen && (st.hack || Math.random() < dt * 3)) drawScreen(A.screen.map, st.hack ? 1 : 0);
  }
}
