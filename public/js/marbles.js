// Marbles from the Marble Shotgun. Damage is hitscan (decided when you fire); these are the visible marbles:
// they fly out along the pellet paths, bounce off whatever they hit, then rattle and roll round the floor for a few seconds.
import * as THREE from 'three';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';
import { jankify } from './jank.js';
import { sfx } from './audio.js';

const MAX = 1400, RAD = 0.026, SPEED = 70, GRAV = 22;
const PALETTES = {
  glass: [0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0xe8f6ff, 0x37d6ff, 0x9aff4f],
  gumball: [0xff2e63, 0xffd400, 0x00c2ff, 0x7dff4f, 0xff7a1a, 0xffffff, 0xb07dff, 0xff4fd8],
};
const P = new Float32Array(MAX * 3), V = new Float32Array(MAX * 3); // position, velocity
const A = new Float32Array(MAX * 3), D = new Float32Array(MAX * 3), N = new Float32Array(MAX * 3); // flight start, direction, hit normal
const flyT = new Float32Array(MAX), flyLen = new Float32Array(MAX), life = new Float32Array(MAX), floorY = new Float32Array(MAX);
const probe = new Float32Array(MAX * 2), spin = new Float32Array(MAX);
const state = new Uint8Array(MAX), hitKind = new Uint8Array(MAX); // state: 0 off, 1 flying, 2 bouncing, 3 rolling. hit: 0 air, 1 wall, 2 player
let mesh = null, next = 0, live = 0, clackT = 0;
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), pv = new THREE.Vector3(), col = new THREE.Color();
const axis = new THREE.Vector3();
// marbles on the floor you can slip on (the server owns them, see shared/marbles.js): each patch keeps its marbles
// (pin = the patch's key, H = its spot there) resting in its footprint for its whole life, so what you see is what slips you
const pin = new Float64Array(MAX), H = new Float32Array(MAX * 2), big = new Float32Array(MAX).fill(1), patches = new Map(); // key -> { c, r, n, end (performance.now() ms) }
function slot() { // the next free-ish marble, never one lying in a patch
  for (let k = 0; k < MAX; k++) { const i = next; next = (next + 1) % MAX; if (!pin[i]) return i; }
  return next;
}
const inFoot = (pt, x, y, z, pad = 0) => Math.abs(y - RAD * 1.5 - pt.c[1]) < 0.15 && Math.hypot(x - pt.c[0], z - pt.c[2]) < pt.r + pad;
// nothing solid between the patch's middle and (x, z): the server's patch stops at walls too (server.js slipsOn)
function seen(pt, x, z) {
  const dx = x - pt.c[0], dz = z - pt.c[2], l = Math.hypot(dx, dz);
  return l <= 0.05 || !raycast([pt.c[0], pt.c[1] + 0.3, pt.c[2]], [dx / l, 0, dz / l], l, BOXES);
}

function floorUnder(x, y, z) {
  const h = raycast([x, y + 0.25, z], [0, -1, 0], 80, BOXES);
  return h ? y + 0.25 - h.t : -1e4;
}

export const marbles = {
  init(scene) {
    const mat = jankify(new THREE.MeshPhongMaterial({ color: 0xffffff, shininess: 90, specular: 0x666666, flatShading: true }));
    mesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(RAD, 1), mat, MAX);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    mesh.frustumCulled = false;
    m4.makeScale(0, 0, 0);
    for (let i = 0; i < MAX; i++) { mesh.setMatrixAt(i, m4); mesh.setColorAt(i, col.setHex(0xffffff)); }
    scene.add(mesh);
  },
  // shots: [{ a: [x,y,z] from, b: [x,y,z] to, n: wall normal or null, player: bool }]
  shoot(shots, palette = 'glass') {
    if (!mesh) return;
    const pal = PALETTES[palette] || PALETTES.glass;
    for (const s of shots) {
      const i = slot();
      if (!state[i]) live++;
      const dx = s.b[0] - s.a[0], dy = s.b[1] - s.a[1], dz = s.b[2] - s.a[2], L = Math.hypot(dx, dy, dz) || 1e-3;
      const i3 = i * 3;
      A[i3] = s.a[0]; A[i3 + 1] = s.a[1]; A[i3 + 2] = s.a[2];
      D[i3] = dx / L; D[i3 + 1] = dy / L; D[i3 + 2] = dz / L;
      P[i3] = s.a[0]; P[i3 + 1] = s.a[1]; P[i3 + 2] = s.a[2];
      const n = s.n || [0, 1, 0];
      N[i3] = n[0]; N[i3 + 1] = n[1]; N[i3 + 2] = n[2];
      hitKind[i] = s.player ? 2 : s.n ? 1 : 0;
      flyT[i] = -Math.random() * 0.04 * SPEED; // a ragged cloud, not a flat disc
      flyLen[i] = L; state[i] = 1; big[i] = 1;
      life[i] = 3.5 + Math.random() * 2.5; spin[i] = 0;
      mesh.setColorAt(i, col.setHex(pal[(Math.random() * pal.length) | 0]));
    }
    mesh.instanceColor.needsUpdate = true;
  },
  // other players / replays only send a dozen pellet paths: find the walls they ended on and spray extra marbles round them
  shootSegs(segs, muzzle, palette, extra = 3) {
    const shots = [];
    for (const s of segs || []) {
      if (!Array.isArray(s) || s.length < 6) continue;
      const a = muzzle || s.slice(0, 3);
      for (let k = 0; k <= extra; k++) {
        let b = s.slice(3, 6);
        if (k) { const L = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]), j = 0.06 * L; b = [b[0] + (Math.random() - 0.5) * j, b[1] + (Math.random() - 0.5) * j, b[2] + (Math.random() - 0.5) * j]; }
        const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], L = Math.hypot(...d) || 1;
        const h = raycast(a, d.map((x) => x / L), L + 0.3, BOXES);
        if (h) {
          const n = [0, 0, 0]; n[h.axis] = h.sign;
          shots.push({ a, b: a.map((v, j) => v + (d[j] / L) * h.t), n });
        } else shots.push({ a, b, n: null, player: L < 29 });
      }
    }
    marbles.shoot(shots, palette);
  },
  clear() {
    if (!mesh) return;
    state.fill(0); live = 0; pin.fill(0); patches.clear();
    m4.makeScale(0, 0, 0);
    for (let i = 0; i < MAX; i++) mesh.setMatrixAt(i, m4);
    mesh.instanceMatrix.needsUpdate = true;
  },
  update(dt, camPos) {
    if (mesh) mesh.visible = live > 0; // (no marbles out: don't draw 1400 hidden ones, here and in the shadow pass)
    if (!mesh || !live) return;
    dt = Math.min(dt, 0.05);
    clackT -= dt;
    let alive = 0;
    for (let i = 0; i < MAX; i++) {
      const st = state[i];
      if (!st) continue;
      const i3 = i * 3;
      life[i] -= dt;
      if (life[i] <= 0) { state[i] = 0; pin[i] = 0; m4.makeScale(0, 0, 0); mesh.setMatrixAt(i, m4); continue; }
      alive++;
      if (st === 1) { // flying out along its pellet path
        flyT[i] += dt * SPEED;
        const t = Math.max(0, Math.min(flyLen[i], flyT[i]));
        P[i3] = A[i3] + D[i3] * t; P[i3 + 1] = A[i3 + 1] + D[i3 + 1] * t; P[i3 + 2] = A[i3 + 2] + D[i3 + 2] * t;
        if (flyT[i] >= flyLen[i]) {
          const hk = hitKind[i];
          if (hk === 1) { // bounce off the wall/floor it hit
            const nx = N[i3], ny = N[i3 + 1], nz = N[i3 + 2], dn = D[i3] * nx + D[i3 + 1] * ny + D[i3 + 2] * nz;
            const sp = SPEED * (0.12 + Math.random() * 0.14);
            V[i3] = (D[i3] - 2 * dn * nx) * sp + (Math.random() - 0.5) * 2;
            V[i3 + 1] = (D[i3 + 1] - 2 * dn * ny) * sp + Math.random() * 2;
            V[i3 + 2] = (D[i3 + 2] - 2 * dn * nz) * sp + (Math.random() - 0.5) * 2;
            P[i3] += nx * RAD; P[i3 + 1] += ny * RAD; P[i3 + 2] += nz * RAD;
            if (clackT <= 0 && Math.random() < 0.25) { sfx.marble([P[i3], P[i3 + 1], P[i3 + 2]]); clackT = 0.035; }
          } else if (hk === 2) { // hit someone: drop off them
            V[i3] = -D[i3] * 2.5 + (Math.random() - 0.5) * 2; V[i3 + 1] = 1 + Math.random() * 2; V[i3 + 2] = -D[i3 + 2] * 2.5 + (Math.random() - 0.5) * 2;
          } else { V[i3] = D[i3] * SPEED * 0.2; V[i3 + 1] = D[i3 + 1] * SPEED * 0.2; V[i3 + 2] = D[i3 + 2] * SPEED * 0.2; }
          floorY[i] = floorUnder(P[i3], P[i3 + 1], P[i3 + 2]);
          probe[i * 2] = P[i3]; probe[i * 2 + 1] = P[i3 + 2];
          state[i] = 2;
        }
      } else { // bouncing / rolling on the floor
        const hs = Math.hypot(V[i3], V[i3 + 2]);
        if (hs > 2.5) { // fast enough to matter: don't roll through walls
          const step = hs * dt + RAD;
          const h = raycast([P[i3], P[i3 + 1], P[i3 + 2]], [V[i3] / hs, 0, V[i3 + 2] / hs], step, BOXES);
          if (h && h.axis !== 1) { if (h.axis === 0) V[i3] *= -0.5; else V[i3 + 2] *= -0.5; }
        }
        if (st === 2) V[i3 + 1] -= GRAV * dt;
        P[i3] += V[i3] * dt; P[i3 + 1] += V[i3 + 1] * dt; P[i3 + 2] += V[i3 + 2] * dt;
        // moved far enough to be over different ground? look again
        if (Math.abs(P[i3] - probe[i * 2]) + Math.abs(P[i3 + 2] - probe[i * 2 + 1]) > 0.4) {
          floorY[i] = floorUnder(P[i3], P[i3 + 1], P[i3 + 2]);
          probe[i * 2] = P[i3]; probe[i * 2 + 1] = P[i3 + 2];
          if (st === 3 && floorY[i] < P[i3 + 1] - RAD * big[i] - 0.03) { state[i] = 2; if (pin[i]) { pin[i] = 0; life[i] = Math.min(life[i], 1.5); } } // rolled off an edge
        }
        if (P[i3 + 1] - RAD * big[i] <= floorY[i]) {
          P[i3 + 1] = floorY[i] + RAD * big[i]; // (resting on the floor, not sunk into it, whatever its size)
          if (V[i3 + 1] < -1.4) {
            V[i3 + 1] = -V[i3 + 1] * 0.42; V[i3] *= 0.82; V[i3 + 2] *= 0.82;
            if (clackT <= 0 && Math.random() < 0.3) { sfx.marble([P[i3], P[i3 + 1], P[i3 + 2]]); clackT = 0.03; }
          } else { V[i3 + 1] = 0; state[i] = 3; if (!pin[i]) adopt(i); }
        }
        // a patch's marbles that got kicked to its edge stop there (the server's patch doesn't move)
        if (state[i] === 3) { const pt = pin[i] && patches.get(pin[i]), f = Math.max(0, 1 - (pt && !inFoot(pt, P[i3], P[i3 + 1], P[i3 + 2]) ? 9 : 1.8) * dt); V[i3] *= f; V[i3 + 2] *= f; }
        spin[i] += (hs / RAD) * dt;
        if (P[i3 + 1] < -200) life[i] = 0;
      }
      // roll round the axis across the direction of travel
      const hs2 = Math.hypot(V[i3], V[i3 + 2]);
      if (hs2 > 1e-3) axis.set(V[i3 + 2] / hs2, 0, -V[i3] / hs2); else axis.set(1, 0, 0);
      q.setFromAxisAngle(axis, spin[i]);
      const s = life[i] < 0.5 ? life[i] / 0.5 : 1;
      sc.setScalar(s * big[i]); // (a patch's marbles are a bit bigger so you can see it from a few steps away)
      pv.set(P[i3], P[i3 + 1], P[i3 + 2]);
      m4.compose(pv, q, sc);
      mesh.setMatrixAt(i, m4);
    }
    live = alive;
    mesh.instanceMatrix.needsUpdate = true;
  },
};

// a marble from a shot that comes to rest inside a patch stays there with it. one that stops outside every patch
// goes soon, so the patches are what's left on the floor (what you see is what slips you)
function adopt(i) {
  const i3 = i * 3, t = performance.now();
  for (const [key, pt] of patches) {
    if (!inFoot(pt, P[i3], P[i3 + 1], P[i3 + 2]) || !seen(pt, P[i3], P[i3 + 2])) continue;
    pin[i] = key; life[i] = Math.max(life[i], (pt.end - t) / 1000); H[i * 2] = P[i3]; H[i * 2 + 1] = P[i3 + 2];
    return;
  }
  life[i] = Math.min(life[i], 1 + Math.random());
}
// m = { c, r, n, left (ms) } from the server. drop its marbles into the footprint (with a little bounce), on its floor only
marbles.addPatch = (key, m, palette = 'glass') => {
  if (!mesh || patches.has(key)) return;
  const pal = PALETTES[palette] || PALETTES.glass, c = m.c, left = m.left / 1000;
  const pt = { c, r: m.r, n: m.n, end: performance.now() + m.left };
  for (let i = 0; i < MAX; i++) if (state[i] === 3 && !pin[i] && inFoot(pt, P[i * 3], P[i * 3 + 1], P[i * 3 + 2]) && seen(pt, P[i * 3], P[i * 3 + 2])) { pin[i] = key; life[i] = Math.max(life[i], left); H[i * 2] = P[i * 3]; H[i * 2 + 1] = P[i * 3 + 2]; } // already lying there
  patches.set(key, pt);
  for (let k = 0, tries = 0; k < m.n && tries < m.n * 3; tries++) {
    const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * m.r * 0.95;
    const x = c[0] + Math.cos(a) * d, z = c[2] + Math.sin(a) * d, fy = floorUnder(x, c[1] + 0.15, z);
    if (Math.abs(fy - c[1]) > 0.12 || !seen(pt, x, z)) continue; // over a gap / a step / behind a wall: the server only counts the patch's own floor
    k++;
    const i = slot(), i3 = i * 3;
    if (!state[i]) live++;
    P[i3] = x; P[i3 + 1] = fy + RAD * 2 + 0.1 + Math.random() * 0.5; P[i3 + 2] = z;
    V[i3] = (Math.random() - 0.5) * 0.6; V[i3 + 1] = -1 - Math.random() * 2; V[i3 + 2] = (Math.random() - 0.5) * 0.6;
    floorY[i] = fy; probe[i * 2] = x; probe[i * 2 + 1] = z; H[i * 2] = x; H[i * 2 + 1] = z;
    state[i] = 2; pin[i] = key; life[i] = left; spin[i] = Math.random() * 6; big[i] = 1.6 + Math.random() * 0.4;
    mesh.setColorAt(i, col.setHex(pal[(Math.random() * pal.length) | 0]));
  }
  mesh.instanceColor.needsUpdate = true;
};
// someone slipped: the patch shrinks to r and n marbles, the rest scatter away from where they fell (at)
marbles.thinPatch = (key, n, r, at) => {
  const pt = patches.get(key);
  if (!pt) return;
  pt.n = n; pt.r = r;
  const mine = [];
  for (let i = 0; i < MAX; i++) if (pin[i] === key && state[i]) mine.push(i);
  const d2 = (i) => (P[i * 3] - pt.c[0]) ** 2 + (P[i * 3 + 2] - pt.c[2]) ** 2;
  mine.sort((a, b) => d2(a) - d2(b));
  mine.forEach((i, k) => {
    if (k < n && Math.sqrt(d2(i)) < r) return;
    pin[i] = 0; life[i] = Math.min(life[i], 0.8 + Math.random() * 0.8);
    kickOne(i, at, 2.5 + Math.random() * 3);
  });
};
// the patch is gone (ran out, slipped to nothing, the map changed): its marbles fade out where they lie
marbles.dropPatch = (key) => {
  if (!patches.delete(key)) return;
  for (let i = 0; i < MAX; i++) if (pin[i] === key) { pin[i] = 0; life[i] = Math.min(life[i], 0.4 + Math.random() * 0.5); }
};
marbles.patches = patches;
marbles.seen = seen;
// someone runs through: marbles near their feet skitter away (looks only, they stay part of the patch)
marbles.kick = (pos, vel, R = 0.55) => {
  let n = 0;
  for (let i = 0; i < MAX; i++) {
    if (state[i] !== 3) continue;
    const i3 = i * 3, dx = P[i3] - pos[0], dz = P[i3 + 2] - pos[2];
    if (dx * dx + dz * dz > R * R || Math.abs(P[i3 + 1] - pos[1]) > 0.4 || Math.hypot(V[i3], V[i3 + 2]) > 1) continue;
    kickOne(i, pos, 1 + Math.random() * 1.6, vel);
    n++;
  }
  return n;
};
function kickOne(i, from, sp, vel) {
  const i3 = i * 3, pt = vel && pin[i] && patches.get(pin[i]);
  if (pt) { // a walk-through skitter: it hops and lands near its own spot in the patch (H), not away from you, so
    // walking through never clears a lane the server doesn't know about (any drift would, a step at a time)
    const a = Math.random() * 6.283, j = 0.08 + Math.random() * 0.22;
    let x = H[i * 2] + Math.cos(a) * j, z = H[i * 2 + 1] + Math.sin(a) * j;
    if (!seen(pt, x, z)) { x = H[i * 2]; z = H[i * 2 + 1]; }
    const tx = x - P[i3], tz = z - P[i3 + 2], l = Math.hypot(tx, tz) || 1, v = Math.min(2.4, l * 1.55); // (flies ~0.08 s, then rolls v / 1.8)
    V[i3] = (tx / l) * v; V[i3 + 1] = 0.5 + Math.random() * 0.6; V[i3 + 2] = (tz / l) * v;
    state[i] = 2; return;
  }
  const dx = P[i3] - from[0], dz = P[i3 + 2] - from[2], l = Math.hypot(dx, dz) || 1;
  const vx = vel ? Math.max(-3, Math.min(3, vel[0] * 0.2)) : 0, vz = vel ? Math.max(-3, Math.min(3, vel[2] * 0.2)) : 0;
  V[i3] = (dx / l) * sp + vx + (Math.random() - 0.5); V[i3 + 1] = 0.6 + Math.random() * 1.4; V[i3 + 2] = (dz / l) * sp + vz + (Math.random() - 0.5);
  state[i] = 2;
}
