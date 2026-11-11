// The hills, juiced (the free bits on top of shared/city/ground.js): a puff of dust where you land on a slope, a few
// loose rocks on the steep sides that go skittering down to the bottom when you walk into them, and litter the wind
// keeps lifting off the ridges and tumbling away downwind. All visual: nothing here touches collision or the server.
// ingame.js runs it while the streamed city is up; it reads the hills from BOXES.terrain (world.js joinFields).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { fx } from '../fx.js';
import { sfx } from '../audio.js';
import { BOXES } from '/shared/map.js';

const NR = 32, NL = 48;
let rocks = null, litter = null, root = null, was = true, vy0 = 0, litT = 0;
const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v3 = new THREE.Vector3(), sc = new THREE.Vector3(), ax = new THREE.Vector3();
const H = (f, i, j) => f.H[Math.max(0, Math.min(f.nx, i)) * (f.nz + 1) + Math.max(0, Math.min(f.nz, j))];
const hsh = (a, b, k) => { let n = Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263) ^ Math.imul(k, 1442695041); n = Math.imul(n ^ (n >>> 13), 1274126177); return ((n ^ (n >>> 16)) >>> 0) / 4294967295; };

export function startHills(scene) {
  stopHills();
  root = new THREE.Group(); scene.add(root);
  const rg = new THREE.IcosahedronGeometry(1, 0), rm = new THREE.MeshLambertMaterial({ color: 0xffffff, flatShading: true });
  rocks = { mesh: new THREE.InstancedMesh(rg, rm, NR), list: [], by: new Map() };
  rocks.mesh.count = 0; rocks.mesh.frustumCulled = false; root.add(rocks.mesh);
  const lg = new THREE.PlaneGeometry(0.3, 0.38), lm = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: true });
  litter = { mesh: new THREE.InstancedMesh(lg, lm, NL), p: [] };
  const c = new THREE.Color();
  for (let i = 0; i < NL; i++) { const k = Math.random(); litter.mesh.setColorAt(i, c.setHex(k < 0.1 ? 0xff5050 : k < 0.35 ? 0xfff2b8 : k < 0.45 ? 0xdde8ff : 0xf6f2ea)); }
  litter.mesh.count = 0; litter.mesh.frustumCulled = false; root.add(litter.mesh);
}
export function stopHills() { if (root) root.removeFromParent(); root = rocks = litter = null; }

// a few loose rocks per piece of ground, on its steepest spots (the same ones every time the chunk loads)
function seed(f) {
  const out = [], n = 2 + Math.floor(hsh(f.x0, f.z0, 1) * 3);
  for (let k = 0; k < 40 && out.length < n; k++) {
    const i = 1 + Math.floor(hsh(f.x0, f.z0, 10 + k) * (f.nx - 2)), j = 1 + Math.floor(hsh(f.x0, f.z0, 60 + k) * (f.nz - 2));
    const s = Math.hypot(H(f, i + 1, j) - H(f, i - 1, j), H(f, i, j + 1) - H(f, i, j - 1)) / (4 * f.cell);
    if (s < 0.14) continue;
    const r = 0.35 + hsh(f.x0, f.z0, 120 + k) * 0.45, x = f.x0 + i * f.cell, z = f.z0 + j * f.cell;
    out.push({ x, z, y: H(f, i, j), r, vx: 0, vz: 0, go: false, rest: 0, puff: 0, rot: new THREE.Quaternion().setFromEuler(e.set(k, k * 2.1, k * 0.7)), sq: [1, 0.7 + hsh(i, j, 3) * 0.3, 0.8 + hsh(i, j, 4) * 0.3], tint: 0x7a6250 + ((hsh(i, j, 5) * 0x18) | 0) * 0x10101 });
  }
  return out;
}
const grad = (T, x, z) => { const a = T.at(x + 0.5, z), b = T.at(x - 0.5, z), c = T.at(x, z + 0.5), d = T.at(x, z - 0.5); return a == null || b == null || c == null || d == null ? null : [a - b, c - d]; };

export function updateHills(dt) {
  const T = BOXES.terrain;
  if (!root || !T || !T.fields) { if (rocks) rocks.mesh.count = 0; if (litter) litter.mesh.count = 0; was = ME.onGround; return; }
  const cam = G.camera.position, p = ME.pos, now = performance.now() / 1000;
  // landing on a hillside: dust where you hit, more the harder and the steeper, and a little rolls off downhill
  const g0 = T.at(p[0], p[2]);
  if (!was && ME.onGround && vy0 < -5 && g0 != null && Math.abs(p[1] - g0) < 0.12) {
    const gr = grad(T, p[0], p[2]) || [0, 0], s = Math.hypot(gr[0], gr[1]);
    fx.dust(p, Math.round(5 + Math.min(10, -vy0 * 0.5) + s * 20));
    if (s > 0.08) for (let k = 1; k <= 3; k++) { const x = p[0] - gr[0] / s * k * 0.9, z = p[2] - gr[1] / s * k * 0.9, y = T.at(x, z); if (y != null) fx.dust([x, y, z], 3); }
  }
  was = ME.onGround; vy0 = ME.vel ? ME.vel[1] : 0;
  // the loose rocks on the ground near you
  const near = new Set();
  for (const l of T.fields.values()) for (const f of l) {
    const cx = f.x0 + f.nx * f.cell / 2, cz = f.z0 + f.nz * f.cell / 2;
    if (Math.hypot(cx - cam.x, cz - cam.z) > 110) continue;
    near.add(f);
    if (!rocks.by.has(f)) rocks.by.set(f, seed(f));
  }
  for (const f of rocks.by.keys()) if (!near.has(f)) rocks.by.delete(f);
  let n = 0;
  const c = new THREE.Color();
  for (const list of rocks.by.values()) for (const r of list) {
    if (!r.go && Math.hypot(r.x - p[0], r.z - p[2]) < r.r + 1.3 && Math.abs(r.y - p[1]) < 2) { // walked into: off it goes, away from you and downhill
      const gr = grad(T, r.x, r.z) || [0, 0], s = Math.hypot(gr[0], gr[1]) || 1, ax0 = r.x - p[0], az0 = r.z - p[2], l = Math.hypot(ax0, az0) || 1;
      r.vx = -gr[0] / s * 3 + ax0 / l * 2.5; r.vz = -gr[1] / s * 3 + az0 / l * 2.5; r.go = true; r.rest = 0;
      sfx.rockslide([r.x, r.y, r.z]); fx.dust([r.x, r.y, r.z], 6);
    }
    if (r.go) {
      const gr = grad(T, r.x, r.z);
      if (!gr) { r.go = false; } else {
        r.vx += (-gr[0] * 16 - r.vx * 0.9) * dt; r.vz += (-gr[1] * 16 - r.vz * 0.9) * dt;
        r.x += r.vx * dt; r.z += r.vz * dt;
        const y = T.at(r.x, r.z); if (y != null) r.y = y;
        const sp = Math.hypot(r.vx, r.vz);
        if (sp > 0.05) { ax.set(r.vz, 0, -r.vx).normalize(); r.rot.premultiply(q.setFromAxisAngle(ax, sp * dt / r.r)); }
        r.puff -= dt; if (r.puff < 0 && sp > 1.5) { r.puff = 0.12; fx.dust([r.x, r.y, r.z], 2); }
        if (sp < 0.35 && Math.hypot(gr[0], gr[1]) < 0.09) { r.rest += dt; if (r.rest > 0.4) { r.go = false; r.vx = r.vz = 0; sfx.thunk([r.x, r.y, r.z]); } }
      }
    }
    if (n >= NR) continue;
    m4.compose(v3.set(r.x, r.y + r.r * 0.55, r.z), r.rot, sc.set(r.r, r.r * r.sq[1], r.r * r.sq[2]));
    rocks.mesh.setMatrixAt(n, m4); rocks.mesh.setColorAt(n, c.setHex(r.tint)); n++;
  }
  rocks.mesh.count = n; rocks.mesh.instanceMatrix.needsUpdate = true; if (rocks.mesh.instanceColor) rocks.mesh.instanceColor.needsUpdate = true;
  // litter off the ridges: now and then a sheet lifts off a crest near you and tumbles away downwind (north-west wind, as the paper storm)
  litT -= dt;
  if (litT < 0 && litter.p.length < NL) {
    litT = 0.25 + Math.random() * 0.35;
    for (let k = 0; k < 6; k++) {
      const x = cam.x + (Math.random() - 0.5) * 70, z = cam.z + (Math.random() - 0.5) * 70, y = T.at(x, z);
      if (y == null) continue;
      const a = T.at(x + 5, z), b = T.at(x - 5, z), cc = T.at(x, z + 5), d = T.at(x, z - 5);
      if (a == null || b == null || cc == null || d == null || y < Math.max(a, b, cc, d) - 0.05) continue; // (a crest: the highest point round here)
      litter.p.push({ x, y: y + 0.1, z, vy: 1.6 + Math.random() * 1.5, t: 0, life: 3 + Math.random() * 2.5, r: [Math.random() * 6, Math.random() * 6, Math.random() * 6], s: [(Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10] });
      break;
    }
  }
  const gust = 1 + 0.5 * Math.sin(now * 0.7);
  let m = 0;
  for (let i = litter.p.length - 1; i >= 0; i--) {
    const s = litter.p[i];
    s.t += dt;
    if (s.t > s.life) { litter.p.splice(i, 1); continue; }
    s.x += 6 * gust * dt; s.z += 4 * gust * dt; s.vy -= 0.9 * dt; s.y += s.vy * dt;
    const gy = T.at(s.x, s.z); if (gy != null && s.y < gy + 0.05) { s.y = gy + 0.05; s.vy = Math.abs(s.vy) * 0.3 + 0.4; }
    for (let k = 0; k < 3; k++) s.r[k] += s.s[k] * dt;
    const fade = Math.min(1, (s.life - s.t) * 2, s.t * 4);
    m4.compose(v3.set(s.x, s.y, s.z), q.setFromEuler(e.set(s.r[0], s.r[1], s.r[2])), sc.set(fade, fade, fade));
    litter.mesh.setMatrixAt(m++, m4);
  }
  litter.mesh.count = m; litter.mesh.instanceMatrix.needsUpdate = true;
}
