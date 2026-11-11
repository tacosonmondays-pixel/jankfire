// Board Approved (pet all 5 hidden cats): Cat Ears and Cat Tail on the mannequin (the Maid Dress: clothes.js).
// The ears and tail are your hair colour (black when you're bald), so they always match each other.
// They animate themselves (an onBeforeRender on one of their meshes), so the ears twitch and the tail sways in the
// CHARACTER preview, on other players, in killcams: anywhere the character is drawn, with no update loop to hook.
import * as THREE from 'three';
import { M } from './models.js';

const PINK = 0xff9ad5, FRILL = 0xffffff, GOLD = 0xffc21a, INK = 0x15121a;
const mesh = (g, c) => new THREE.Mesh(g, M(c));
const box = (w, h, d, c, x, y, z) => { const m = mesh(new THREE.BoxGeometry(w, h, d), c); m.position.set(x, y, z); return m; };
const sph = (r, c, x, y, z, ws = 8, hs = 6) => { const m = mesh(new THREE.SphereGeometry(r, ws, hs), c); m.position.set(x, y, z); return m; };
const tone = (c, l, s = 0) => new THREE.Color(c).offsetHSL(0, s, l).getHex();
const clock = () => performance.now() / 1000;

// ------------------------------------------------------------ cat ears: a headband with two pointy ears on it
// each ear is a flat four-sided pyramid (a flat face to the front), a pink inner ear, a white tuft at the bottom.
// they twitch now and then, one at a time, and flatten back a little when you look down
export function catEars(H, lk) {
  const hc = new THREE.Color(lk.hairColor || '#1a1a1a').getHex();
  const big = lk.hair === 'afro' ? 1.42 : lk.hair === 'spiky' || lk.hair === 'bun' ? 1.12 : 1; // big hair: a bigger band
  const cy = 0.15 + (big - 1) * 0.12, rx = 0.135 * big, ry = 0.172 * big;
  const band = mesh(new THREE.TorusGeometry(1, 0.075, 4, 18, Math.PI), INK);
  band.scale.set(rx, ry, 0.16); band.position.set(0, cy, 0.004); band.rotation.z = 0; H.add(band); // (the torus tube scales too: 0.075 * r)
  const ears = [];
  for (const sx of [-1, 1]) {
    const a = 0.7, piv = new THREE.Group();
    piv.position.set(sx * Math.sin(a) * rx, cy + Math.cos(a) * ry - 0.01, -0.006);
    piv.rotation.set(-0.08, 0, -sx * 0.32); // leaning out, a touch forward
    H.add(piv);
    const outer = mesh(new THREE.ConeGeometry(0.08, 0.165, 4, 1).rotateY(Math.PI / 4).scale(1, 1, 0.42), hc);
    outer.position.y = 0.072; piv.add(outer);
    const inner = mesh(new THREE.ConeGeometry(0.052, 0.11, 4, 1).rotateY(Math.PI / 4).scale(1, 1, 0.3), PINK);
    inner.position.set(0, 0.058, -0.014); piv.add(inner);
    const tuft = mesh(new THREE.ConeGeometry(0.016, 0.05, 4).rotateY(Math.PI / 4), FRILL);
    tuft.position.set(sx * -0.012, 0.022, -0.02); tuft.rotation.z = sx * 0.5; piv.add(tuft);
    const tip = mesh(new THREE.ConeGeometry(0.02, 0.035, 4).rotateY(Math.PI / 4).scale(1, 1, 0.5), tone(hc, -0.08));
    tip.position.y = 0.138; piv.add(tip); // a darker tip
    ears.push({ piv, rz: -sx * 0.32, sx });
  }
  const seed = Math.random() * 100;
  let next = 1.5 + Math.random() * 3, who = 0, t0 = -9;
  ears[0].piv.children[1].onBeforeRender = () => {
    const t = clock() + seed;
    if (t > next) { t0 = t; who = Math.random() < 0.5 ? 0 : Math.random() < 0.7 ? 1 : 2; next = t + 2 + Math.random() * 4.5; }
    const k = t - t0, flick = k < 0.32 ? Math.sin((k / 0.32) * Math.PI) * (k < 0.16 ? 1 : 0.6) : 0; // a quick double flick
    for (let i = 0; i < 2; i++) {
      const e = ears[i], f = who === 2 || who === i ? flick : 0;
      e.piv.rotation.z = e.rz - e.sx * (0.42 * f) + Math.sin(t * 1.3 + i) * 0.02;
      e.piv.rotation.x = -0.08 + f * 0.25;
      e.piv.rotation.y = e.sx * f * 0.35; // the ear turns as it flicks, like it heard something
    }
  };
  return ears;
}

// ------------------------------------------------------------ cat tail: eight tapering segments out of the lower back
// in a lazy question-mark curl, with a pink ribbon bow and a little gold bell near the base. a wave runs down it
// (slow and swishy standing, the tip curls and uncurls), and every so often the tip flicks
export function catTail(ch, lk, back) {
  const hc = new THREE.Color(lk.hairColor || '#1a1a1a').getHex();
  const N = 8, segs = [], base = new THREE.Group();
  base.position.set(0, 0.99, back); base.rotation.x = 2.15; // out the back and down
  ch.body.add(base);
  let parent = base;
  const curl = [0.0, -0.18, -0.3, -0.36, -0.38, -0.4, -0.42, -0.5]; // how much each joint bends up
  for (let i = 0; i < N; i++) {
    const k = i / (N - 1), r0 = 0.034 - k * 0.011, r1 = 0.034 - (k + 1 / N) * 0.011, L = 0.098;
    const g = new THREE.Group(); g.position.y = i ? 0.098 : 0; g.rotation.x = curl[i];
    parent.add(g);
    const s = mesh(new THREE.CylinderGeometry(Math.max(0.02, r1), r0, L + 0.012, 7), hc); s.position.y = L / 2; g.add(s);
    g.add(sph(r0 * 1.02, hc, 0, 0, 0, 7, 5)); // a round joint so the bends don't show gaps
    segs.push({ g, rx: curl[i] });
    parent = g;
  }
  const tip = sph(0.03, tone(hc, 0.06), 0, 0.1, 0, 8, 6); tip.scale.set(1, 1.35, 1); parent.add(tip); // a fluffy tip
  // the ribbon on the second segment: two loops, two tails, a knot, a bell
  const rib = segs[1].g, R = 0xff4fd8;
  rib.add(box(0.074, 0.03, 0.074, R, 0, 0.03, 0)); // the band round the tail
  for (const sx of [-1, 1]) {
    const lp = box(0.075, 0.05, 0.022, R, sx * 0.05, 0.03, -0.045); lp.rotation.z = sx * 0.45; rib.add(lp);
    const tl = box(0.022, 0.07, 0.014, tone(R, -0.08), sx * 0.022, -0.012, -0.05); tl.rotation.z = sx * 0.35; rib.add(tl);
  }
  rib.add(sph(0.018, tone(R, -0.1), 0, 0.03, -0.05, 6, 4));
  const bell = sph(0.022, GOLD, 0, -0.005, -0.068, 8, 6); rib.add(bell);
  rib.add(box(0.03, 0.004, 0.006, 0x6a4a00, 0, -0.012, -0.089)); // the bell's slot
  const seed = Math.random() * 100, speed = 0.85 + Math.random() * 0.3;
  let flickAt = 3 + Math.random() * 4;
  tip.onBeforeRender = () => {
    const t = clock() * speed + seed;
    if (t > flickAt + 0.6) flickAt = t + 2.5 + Math.random() * 5;
    const fk = t > flickAt ? Math.sin(((t - flickAt) / 0.6) * Math.PI) : 0;
    for (let i = 0; i < N; i++) {
      const s = segs[i], w = 0.25 + i / N;
      s.g.rotation.z = Math.sin(t * 1.7 - i * 0.55) * 0.16 * w; // the side-to-side swish travelling down it
      s.g.rotation.x = s.rx + Math.sin(t * 1.1 - i * 0.4) * 0.05 * w - (i > 4 ? fk * 0.35 : 0); // the curl breathes; the flick curls the tip
    }
    bell.position.x = Math.sin(t * 3.4) * 0.006; // the bell swings a hair
  };
  ch.tail = base;
  return base;
}
