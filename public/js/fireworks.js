// Fireworks for no-scope headshots. A few rockets whistle up from where the victim stood, burst ~27 m up, and their
// sparks fly into place to spell the shooter's name + distance in the sky. Every client turns the text to its own
// camera. It twinkles for a few seconds, then falls and fades. The text is drawn small on a canvas and every lit
// pixel becomes one glowing spark (capped), so a long name just gets a smaller font.
import * as THREE from 'three';
import { G } from './ctx.js';
import { PSys } from './fx.js';
import { sfx } from './audio.js';

const CAP = 420; // sparks per name
const UP = 27; // metres above the victim's feet (lower in replays: their camera looks along the killer's aim)
const HOLD = 3; // seconds the name stays up once it's all there
const FALL = 1.8;
const COLS = [0xff4fd8, 0x4fd8ff, 0xffe14d, 0x7dff4f, 0xff7a1a, 0xb07dff];
const shows = [];
// burst sparks for live shows and replay shows: a = additive glow (flashes, trails, glitter), c = solid colour (additive alone
// washes out to white against a daytime sky). glow = letters + rocket heads, halo = their additive glow
let live = null, rp = null, glow = null, halo = null;
const R = (s = 1) => (Math.random() * 2 - 1) * s;
const tc = new THREE.Color(), Y = new THREE.Vector3(0, 1, 0), n = new THREE.Vector3(), rt = new THREE.Vector3(), up = new THREE.Vector3();

function init() {
  if (live) return;
  live = { a: new PSys(3000, THREE.AdditiveBlending), c: new PSys(1500, THREE.NormalBlending) };
  rp = { a: new PSys(2500, THREE.AdditiveBlending), c: new PSys(1500, THREE.NormalBlending) };
  // letters are solid colour (additive alone washes out to white against a daytime sky) with an additive halo behind
  halo = new PSys(CAP * 4 + 64, THREE.AdditiveBlending);
  glow = new PSys(CAP * 4 + 64, THREE.NormalBlending);
  halo.points.renderOrder = 1; glow.points.renderOrder = 2;
  G.scene.add(live.a.points, live.c.points, rp.a.points, rp.c.points, halo.points, glow.points);
}

// the label in a small canvas -> lit pixels in text space (canvas px, centred, y up). shrinks the font until it fits the cap
function letters(lines) {
  const c = document.createElement('canvas'), x = c.getContext('2d', { willReadFrequently: true });
  let pts = [], w = 1;
  for (let size = 20; size >= 7; size--) {
    const font = `bold ${size}px "Comic Sans MS", "Comic Neue", sans-serif`;
    x.font = font;
    w = Math.ceil(Math.max(...lines.map((l) => x.measureText(l).width))) + 4;
    const lh = Math.ceil(size * 1.15), h = lh * lines.length + 4;
    c.width = w; c.height = h;
    x.font = font; x.textAlign = 'center'; x.textBaseline = 'top'; x.fillStyle = '#fff';
    lines.forEach((l, i) => x.fillText(l, w / 2, 2 + i * lh));
    const d = x.getImageData(0, 0, w, h).data;
    pts = [];
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) if (d[(j * w + i) * 4 + 3] > 120) pts.push(i - w / 2, h / 2 - j);
    if (pts.length / 2 <= CAP * 1.15) break;
  }
  // still a few too many: drop random ones (shuffle the pairs, keep the first CAP)
  const m = pts.length / 2;
  if (m > CAP) {
    for (let i = m - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [pts[i * 2], pts[j * 2]] = [pts[j * 2], pts[i * 2]]; [pts[i * 2 + 1], pts[j * 2 + 1]] = [pts[j * 2 + 1], pts[i * 2 + 1]];
    }
    pts.length = CAP * 2;
  }
  return { pts, w };
}

// a plane through the text centre that faces this client's camera (falls back to the camera's own right when it's overhead)
function basis(c, cam) {
  n.set(cam.position.x - c[0], cam.position.y - c[1], cam.position.z - c[2]).normalize();
  rt.crossVectors(Y, n);
  if (rt.lengthSq() < 0.06) { rt.setFromMatrixColumn(cam.matrixWorld, 0); rt.addScaledVector(n, -rt.dot(n)); }
  rt.normalize();
  up.crossVectors(n, rt).normalize();
}

// p = where the victim stood, name + dist = what to write, replay = it's part of a killcam / play of the round
export function launchFireworks(p, name, dist, replay = false) {
  if (!G.scene || !G.camera) return;
  init();
  const nm = String(name || '???').toUpperCase().slice(0, 16), label = `${nm} ${dist}m`;
  const { pts, w } = letters(label.length > 14 ? [nm, `${dist}m`] : [label]);
  const c = [p[0], p[1] + (replay ? 16 : UP), p[2]];
  // about a third of the screen wide from wherever you are (sized once, from your camera, when it goes up)
  const cp = G.camera.position, vd = Math.hypot(c[0] - cp.x, c[1] - cp.y, c[2] - cp.z);
  const W = Math.max(16, Math.min(90, (replay ? 0.42 : 0.68) * vd * Math.tan(((G.settings.fov || 95) * Math.PI) / 360) * (G.camera.aspect || 1.6)));
  const px = W / w; // metres per canvas pixel
  const sp = replay ? 3 : 1; // a killcam ends ~1.5 s after the kill, so the show runs faster in replays
  const nr = w > 110 ? 5 : w > 70 ? 4 : 3, N = pts.length / 2;
  const rockets = [];
  for (let i = 0; i < nr; i++) rockets.push({ at: (i * 0.14 + Math.random() * 0.06) / sp, dur: (0.95 + Math.random() * 0.2) / sp, u: ((i + 0.5) / nr - 0.5) * w * 0.9, b: null, bt: -1, col: COLS[(Math.random() * COLS.length) | 0], trail: 0, glit: 0 });
  const s = {
    t: 0, replay, sp, o: [p[0], p[1] + 0.4, p[2]], c, px, w, k: W / 30, rockets, N, pts: Float32Array.from(pts),
    own: new Uint8Array(N), dl: new Float32Array(N), fl: new Float32Array(N), ph: new Float32Array(N), fq: new Float32Array(N),
    off: new Float32Array(N * 3), fallAt: new Float32Array(N).fill(Infinity), fp: new Float32Array(N * 3), fv: new Float32Array(N * 3), falling: new Uint8Array(N), end: 0,
  }; // fallAt stays far off until the last rocket has burst (then the hold starts)
  for (let i = 0; i < N; i++) {
    s.own[i] = Math.max(0, Math.min(nr - 1, Math.floor((s.pts[i * 2] / w + 0.5) * nr))); // each rocket owns a slice of the letters
    s.dl[i] = Math.random() * 0.12 / sp; s.fl[i] = (0.6 + Math.random() * 0.3) / sp;
    s.ph[i] = Math.random() * 6.28; s.fq[i] = 5 + Math.random() * 9;
    const a = [R(), R(), R()], l = Math.hypot(...a) || 1, k = (2 + Math.random() * 4) * px * 8;
    s.off[i * 3] = (a[0] / l) * k; s.off[i * 3 + 1] = (a[1] / l) * k; s.off[i * 3 + 2] = (a[2] / l) * k;
  }
  shows.push(s);
  if (shows.length > 4) shows.shift(); // nobody needs five names in the sky at once
}

export function clearFireworks() {
  shows.length = 0;
  if (!live) return;
  for (const sys of [live.a, live.c, rp.a, rp.c, glow, halo]) { sys.n = 0; sys.geo.setDrawRange(0, 0); }
}

const ease = (k) => 1 - (1 - k) * (1 - k) * (1 - k);
function rocketPos(s, r, k, out) {
  const e = 1 - (1 - k) * (1 - k); // fast off the ground, slowing at the top
  out[0] = s.o[0] + (r.b[0] - s.o[0]) * k + Math.sin(k * 9 + r.at * 40) * 0.25;
  out[1] = s.o[1] + (r.b[1] - s.o[1]) * e;
  out[2] = s.o[2] + (r.b[2] - s.o[2]) * k + Math.cos(k * 8 + r.at * 30) * 0.25;
  return out;
}
const rp3 = [0, 0, 0];

function burst(s, r, sys, loud) {
  const [x, y, z] = r.b, k = s.k; // bigger text (you're further away) = bigger bang
  for (let i = 0; i < 14; i++) sys.a.spawn(x, y, z, R(26 * k), R(26 * k), R(26 * k), 0.14, 1.4 * k, 0.2 * k, 0xffffff, r.col, 1, 0, 6); // flash
  for (let i = 0; i < 90; i++) { // a ball of sparks, every third one glowing
    const a = [R(), R(), R()], l = Math.hypot(...a) || 1, v = (9 + Math.random() * 7) * k, life = 1 + Math.random() * 0.7;
    const vx = (a[0] / l) * v, vy = (a[1] / l) * v, vz = (a[2] / l) * v;
    sys.c.spawn(x, y, z, vx, vy, vz, life, 0.42 * k, 0.12 * k, Math.random() < 0.2 ? 0xffffff : r.col, r.col, 1, 5 * k, 1.8);
    if (i % 3 === 0) sys.a.spawn(x, y, z, vx, vy, vz, life * 0.8, 1.1 * k, 0.2 * k, r.col, r.col, 0.45, 5 * k, 1.8);
  }
  if (loud) { sfx.fwBang(r.b); sfx.fwCrackle(r.b); }
}

// one spark: a solid core plus a bigger, dimmer additive halo
function put(i, x, y, z, col, a, size, ha, hk = 2.1) {
  const i3 = i * 3;
  for (const sys of [glow, halo]) { sys.p[i3] = x; sys.p[i3 + 1] = y; sys.p[i3 + 2] = z; sys.col[i3] = col.r; sys.col[i3 + 1] = col.g; sys.col[i3 + 2] = col.b; }
  glow.alpha[i] = a; glow.size[i] = size;
  halo.alpha[i] = ha; halo.size[i] = size * hk;
}

// replaying: a killcam or play of the round owns the camera (live shows hide, replay shows play)
export function updateFireworks(dt, cam, replaying) {
  if (!live) return;
  if (!G.joined) { if (shows.length || live.a.n || live.c.n || rp.a.n || rp.c.n) clearFireworks(); return; } // back at the menu: nothing left hanging in the sky
  if (!replaying) {
    for (let i = shows.length - 1; i >= 0; i--) if (shows[i].replay) shows.splice(i, 1);
    for (const sys of [rp.a, rp.c]) if (sys.n) { sys.n = 0; sys.geo.setDrawRange(0, 0); } // whatever the replay left in the air goes with it
  }
  live.a.points.visible = live.c.points.visible = !replaying; rp.a.points.visible = rp.c.points.visible = replaying;
  let gi = 0;
  for (let si = shows.length - 1; si >= 0; si--) {
    const s = shows[si], sys = s.replay ? rp : live, shown = s.replay === replaying;
    s.t += dt;
    basis(s.c, cam);
    // rockets
    for (const r of s.rockets) {
      if (s.t < r.at) continue;
      if (!r.b) { // pick where it bursts: over its slice of the letters, as this camera sees them
        r.b = [s.c[0] + rt.x * r.u * s.px + R(1), s.c[1] + R(1.5), s.c[2] + rt.z * r.u * s.px + R(1)];
        if (shown) sfx.fwWhistle([s.o[0], s.o[1] + 8, s.o[2]], r.dur * 1.05);
      }
      const k = (s.t - r.at) / r.dur;
      if (k < 1) {
        const [x, y, z] = rocketPos(s, r, k, rp3);
        r.trail += dt * 90;
        for (; r.trail >= 1; r.trail--) sys.a.spawn(x + R(0.1), y, z + R(0.1), R(0.9), -2 + R(0.8), R(0.9), 0.45 + Math.random() * 0.35, 0.32 * s.k, 0.05, 0xffd27a, 0xff2a00, 1, 2, 1);
        if (shown && gi < glow.max) put(gi++, x, y, z, tc.setHex(0xfff2c0), 1, (0.35 + Math.random() * 0.25) * s.k, 0.45, 1.8);
      } else if (r.bt < 0) {
        r.bt = s.t;
        burst(s, r, sys, shown);
      } else if (s.t - r.bt < 1.5) { // glitter crackling where it burst
        r.glit += dt * 30;
        const rad = 3 + (s.t - r.bt) * 6;
        for (; r.glit >= 1; r.glit--) sys.a.spawn(r.b[0] + R(rad * s.k), r.b[1] + R(rad * s.k) - (s.t - r.bt) * 2, r.b[2] + R(rad * s.k), 0, -1, 0, 0.08 + Math.random() * 0.12, 0.45 * s.k, 0.2 * s.k, 0xffffff, 0xffd060, 1, 0, 0);
      }
    }
    // letters
    const lastBurst = Math.max(...s.rockets.map((r) => (r.bt < 0 ? Infinity : r.bt)));
    if (!s.end && Number.isFinite(lastBurst)) {
      s.end = lastBurst + 1 / s.sp + (s.replay ? 2.5 : HOLD);
      for (let i = 0; i < s.N; i++) s.fallAt[i] = s.end + Math.random() * 0.5;
    }
    let alive = s.rockets.some((r) => r.bt < 0 || s.t - r.bt < 1.5);
    for (let i = 0; i < s.N; i++) {
      const r = s.rockets[s.own[i]];
      if (r.bt < 0) { alive = true; continue; }
      const t0 = r.bt + s.dl[i];
      if (s.t < t0) { alive = true; continue; }
      const u = s.pts[i * 2] * s.px, v = s.pts[i * 2 + 1] * s.px, i3 = i * 3;
      let x, y, z, a = 1, ha = 0.22, size = s.px * 1.3;
      const hue = ((s.pts[i * 2] / s.w + 0.5) * 0.85 + s.t * 0.15) % 1;
      if (s.t < s.fallAt[i]) {
        alive = true;
        const tx = s.c[0] + rt.x * u + up.x * v, ty = s.c[1] + rt.y * u + up.y * v, tz = s.c[2] + rt.z * u + up.z * v;
        const k = Math.min(1, (s.t - t0) / s.fl[i]);
        if (k < 1) { // flying into place on a curve
          const e = ease(k), bend = Math.sin(Math.PI * k) * (1 - k * 0.5);
          x = r.b[0] + (tx - r.b[0]) * e + s.off[i3] * bend;
          y = r.b[1] + (ty - r.b[1]) * e + s.off[i3 + 1] * bend;
          z = r.b[2] + (tz - r.b[2]) * e + s.off[i3 + 2] * bend;
          tc.setHSL(hue, 1, 0.6 + (1 - k) * 0.3);
          size *= 1.5 - k * 0.5; ha = 0.35;
        } else { // twinkle
          x = tx; y = ty; z = tz;
          const tw = Math.sin(s.t * s.fq[i] + s.ph[i]);
          a = 0.8 + 0.2 * tw; ha = 0.06 + 0.2 * tw * tw;
          if (Math.sin(s.t * s.fq[i] * 1.7 + s.ph[i] * 3) > 0.995) { tc.setHex(0xffffff); size *= 1.6; ha = 0.5; } else tc.setHSL(hue, 1, 0.56); // a glint now and then (~3% at once)
        }
        s.fp[i3] = x; s.fp[i3 + 1] = y; s.fp[i3 + 2] = z;
      } else { // falling embers
        const k = (s.t - s.fallAt[i]) / FALL;
        if (k >= 1) continue;
        alive = true;
        if (!s.falling[i]) { s.falling[i] = 1; s.fv[i3] = R(0.8); s.fv[i3 + 1] = 0.4 + Math.random() * 0.8; s.fv[i3 + 2] = R(0.8); }
        s.fv[i3 + 1] -= 6 * dt;
        for (let q = 0; q < 3; q++) { s.fv[i3 + q] *= 1 - 0.5 * dt; s.fp[i3 + q] += s.fv[i3 + q] * dt; }
        x = s.fp[i3]; y = s.fp[i3 + 1]; z = s.fp[i3 + 2];
        tc.setHSL(hue + (0.08 - hue) * k, 1, 0.6 - k * 0.2);
        a = (1 - k) * (1 - k) * (0.7 + Math.random() * 0.3); ha = a * 0.3;
        size *= 1 - k * 0.6;
      }
      if (shown && gi < glow.max) put(gi++, x, y, z, tc, a, size, ha);
    }
    if (!alive) shows.splice(si, 1);
  }
  for (const sys of [glow, halo]) {
    sys.geo.setDrawRange(0, gi);
    sys.posAttr.needsUpdate = true; sys.colAttr.needsUpdate = true; sys.aAttr.needsUpdate = true; sys.sAttr.needsUpdate = true;
  }
  for (const sys of [live.a, live.c, rp.a, rp.c]) sys.update(dt);
}
