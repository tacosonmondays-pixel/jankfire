// Board Approved (pet all 5 hidden cats): Cat Ears, Cat Tail and the Maid Dress, on the mannequin.
// The ears and tail are your hair colour (black when you're bald), so they always match each other.
// They animate themselves (an onBeforeRender on one of their meshes), so the ears twitch and the tail sways in the
// CHARACTER preview, on other players, in killcams: anywhere the character is drawn, with no update loop to hook.
import * as THREE from 'three';
import { M } from './models.js';

const PINK = 0xff9ad5, WHITE = 0xf6f4ef, FRILL = 0xffffff, GOLD = 0xffc21a, INK = 0x15121a;
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

// ------------------------------------------------------------ maid dress
// black (or the colour you pick; the team colour in a team game) with a white apron: a bell skirt with pleats and a
// ruffled petticoat hem showing under it, the apron's frilled bib and straps, a sash round the waist tied in a big bow
// at the back, a frilly collar with a pink ribbon, puff sleeves with white cuffs, white knee socks and black shoes.
// with nothing on your head (or the Cat Ears) you also get the frilly headdress
function ruffleLathe(pts, segs, wave, amp, phiStart = 0, phiLen = Math.PI * 2) {
  const g = new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), segs, phiStart, phiLen);
  const p = g.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const r = Math.hypot(v.x, v.z); if (r < 1e-4) continue;
    const a = Math.atan2(v.x, v.z), y0 = pts[0][1], y1 = pts[pts.length - 1][1], k = Math.max(0, Math.min(1, (v.y - y0) / (y1 - y0 || 1)));
    const f = 1 + Math.sin(a * wave) * amp * (1 - k) * (1 - k); // folds grow toward the hem (the first point)
    p.setXYZ(i, (v.x / r) * r * f, v.y, (v.z / r) * r * f);
  }
  g.computeVertexNormals();
  return g;
}
export function maidDress(P, lk, col, legs) {
  const { body, arm, armL, kneeL, kneeR, head } = P;
  const D = col, Dk = tone(D, -0.04), add = (m) => { body.add(m); return m; };
  // bodice over the chest (like the tee shell), a little fitted
  const bod = sph(0.214, D, 0, 1.34, 0, 10, 8); bod.scale.set(1.18, 1.1, 0.75); add(bod);
  // skirt: a bell from the waist out to the knees, 12 pleats, the white petticoat ruffle peeking under the hem
  const sk = mesh(ruffleLathe([[0.36, 0.6], [0.33, 0.7], [0.27, 0.86], [0.19, 1.0], [0.135, 1.1]], 24, 12, 0.07), D);
  add(sk);
  add(mesh(new THREE.CylinderGeometry(0.19, 0.19, 0.012, 12), Dk)).position.y = 0.995; // (closes the skirt's top from below)
  const pet = mesh(ruffleLathe([[0.385, 0.57], [0.37, 0.61], [0.33, 0.63]], 30, 15, 0.12), FRILL); add(pet);
  // apron: a curved white panel down the front of the skirt with a frilled hem, then the bib, its frills and straps
  const ap = mesh(ruffleLathe([[0.358, 0.68], [0.33, 0.74], [0.27, 0.88], [0.205, 1.0], [0.15, 1.09]], 10, 0, 0, Math.PI - 0.72, 1.44), WHITE); add(ap);
  const apf = mesh(ruffleLathe([[0.375, 0.65], [0.365, 0.69], [0.345, 0.7]], 14, 22, 0.1, Math.PI - 0.8, 1.6), FRILL); add(apf);
  const bib = box(0.17, 0.2, 0.018, WHITE, 0, 1.3, -0.163); bib.rotation.x = -0.12; add(bib);
  for (const sx of [-1, 1]) {
    const fr = box(0.022, 0.2, 0.03, FRILL, sx * 0.095, 1.3, -0.165); fr.rotation.set(-0.12, 0, sx * 0.06); add(fr); // frills down the bib's sides
    for (let i = 0; i < 4; i++) { const n = box(0.024, 0.03, 0.03, FRILL, sx * 0.108, 1.22 + i * 0.05, -0.16 + i * 0.006); n.rotation.z = sx * 0.6; add(n); } // the ruffle teeth
    const st = box(0.036, 0.022, 0.3, WHITE, sx * 0.11, 1.53, 0.0); add(st); // straps over the shoulders
    const sb = box(0.036, 0.34, 0.02, WHITE, sx * 0.1, 1.36, 0.155); sb.rotation.z = sx * 0.16; add(sb); // crossing down the back
  }
  add(box(0.16, 0.02, 0.022, FRILL, 0, 1.405, -0.168)); // the bib's top frill
  // the sash round the waist, tied in a big bow at the back
  add(mesh(new THREE.CylinderGeometry(0.128, 0.136, 0.06, 12, 1, true), WHITE)).position.y = 1.1;
  const bow = new THREE.Group(); bow.position.set(0, 1.1, 0.14); add(bow);
  for (const sx of [-1, 1]) {
    const lp = box(0.12, 0.075, 0.035, WHITE, sx * 0.07, 0.01, 0.02); lp.rotation.set(0, sx * -0.25, sx * 0.3); bow.add(lp);
    const tl = box(0.04, 0.2, 0.014, WHITE, sx * 0.04, -0.12, 0.03); tl.rotation.set(0.15, 0, sx * 0.22); bow.add(tl);
  }
  bow.add(box(0.05, 0.06, 0.05, FRILL, 0, 0.005, 0.02));
  // collar: a ruffled white ring round the neck with a pink ribbon bow at the front
  const col2 = mesh(ruffleLathe([[0.135, 1.5], [0.11, 1.535], [0.07, 1.555]], 20, 10, 0.14), FRILL); add(col2);
  const rb = new THREE.Group(); rb.position.set(0, 1.52, -0.125); add(rb);
  for (const sx of [-1, 1]) {
    const lp = box(0.05, 0.035, 0.016, PINK, sx * 0.03, 0, 0); lp.rotation.z = sx * 0.35; rb.add(lp);
    const tl = box(0.016, 0.055, 0.01, PINK, sx * 0.014, -0.04, 0.002); tl.rotation.z = sx * 0.3; rb.add(tl);
  }
  rb.add(sph(0.014, tone(PINK, -0.1), 0, 0, -0.004, 6, 4));
  for (let i = 0; i < 2; i++) add(sph(0.011, GOLD, 0, 1.47 - i * 0.05, -0.155, 6, 4)); // two buttons above the bib
  // puff sleeves + white cuffs. the right arm points down -z (it holds the gun); the left one reaches across
  const puff = (p, x, z, ry) => {
    const pf = sph(0.088, D, x, -0.005, z, 9, 7); pf.scale.set(1, 0.95, 1.25); pf.rotation.y = ry; p.add(pf);
    const cuff = mesh(new THREE.TorusGeometry(0.056, 0.016, 5, 12), FRILL);
    cuff.position.set(x + Math.sin(ry) * -0.07, -0.005, z - Math.cos(ry) * 0.07); cuff.rotation.y = ry; p.add(cuff);
  };
  puff(arm, 0, -0.05, 0); puff(armL, 0.025, -0.045, -0.45);
  for (const sx of [-1, 1]) add(sph(0.085, D, 0.25 * sx, 1.45, 0, 8, 6)).scale.set(1, 0.9, 1); // the puffs over the shoulder joints
  // knee socks + shoes (bare legs only: pants keep their own)
  if (!legs) for (const kn of [kneeL, kneeR]) {
    const sock = mesh(new THREE.CylinderGeometry(0.06, 0.049, 0.3, 7), WHITE); sock.position.y = -0.25; kn.add(sock);
    const top = mesh(new THREE.TorusGeometry(0.058, 0.01, 4, 10), FRILL); top.position.y = -0.1; top.rotation.x = Math.PI / 2; kn.add(top);
    kn.add(box(0.108, 0.065, 0.23, INK, 0, -0.43, -0.05)); // black shoes over the bare feet
    kn.add(box(0.11, 0.012, 0.03, INK, 0, -0.395, -0.1)); // the strap across
  }
  // headdress: a frilly white crescent across the top of the head (with nothing else on it, or with the Cat Ears)
  if (!lk.head || lk.head === 'none' || lk.head === 'catears') {
    const big = lk.hair === 'afro' ? 1.42 : lk.hair === 'spiky' || lk.hair === 'bun' ? 1.12 : 1, cy = 0.15 + (big - 1) * 0.12, rx = 0.138 * big, ry = 0.176 * big;
    const hd = new THREE.Group(); hd.position.set(0, -0.01, -0.06); hd.rotation.x = -0.32; head.add(hd);
    for (let i = 0; i <= 8; i++) { // ruffle petals along the front of the band
      const a = -1.05 + (i / 8) * 2.1, x = Math.sin(a) * rx, y = cy + Math.cos(a) * ry;
      const pt = sph(0.027, FRILL, x, y + 0.008, 0, 6, 4); pt.scale.set(1, 1.2, 0.5); pt.rotation.z = -a; hd.add(pt);
    }
    const band = mesh(new THREE.TorusGeometry(1, 0.08, 4, 16, 2.2), WHITE);
    band.scale.set(rx, ry, 0.2); band.rotation.z = Math.PI / 2 - 1.1; band.position.y = cy; hd.add(band);
  }
}
