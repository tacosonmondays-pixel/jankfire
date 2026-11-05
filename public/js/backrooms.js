// Backrooms extras: the fluorescent hum, the lights that flicker, and (very rarely) something tall and dark standing
// at the far end of a hallway. It's gone when you get close or look away. Client only, nobody else sees it.
import * as THREE from 'three';
import { G } from './ctx.js';
import { MAP, BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { hum } from './audio.js';

// ---- flicker: mostly on, now and then a burst of quick dips like a dying tube. each material dies on its own
const fls = new Map();
function flicker(mat, now) {
  let fl = fls.get(mat);
  if (!fl) fls.set(mat, (fl = { v: 1, until: now + Math.random() * 2000, burst: 0 }));
  if (now >= fl.until) {
    if (fl.burst > 0) { fl.burst--; fl.v = fl.v < 0.5 ? 0.85 + Math.random() * 0.15 : Math.random() * 0.25; fl.until = now + 30 + Math.random() * 120; }
    else if (Math.random() < 0.35) { fl.burst = 2 + ((Math.random() * 7) | 0); fl.v = 0.1; fl.until = now + 60; }
    else { fl.v = 1; fl.until = now + 400 + Math.random() * 3200; }
  }
  mat.emissiveIntensity = fl.v;
}

// ---- the thing at the end of the hall
let ent = null, nextTry = 0, quietUntil = 0;
const tmp = new THREE.Vector3();
function figure() {
  const g = new THREE.Group(), m = new THREE.MeshBasicMaterial({ color: 0x0b0906 });
  const part = (w, h, d, x, y) => { const p = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); p.position.set(x, y, 0); g.add(p); };
  part(0.46, 1.15, 0.26, 0, 1.76); part(0.3, 0.42, 0.3, 0, 2.55); // too tall, too thin
  part(0.1, 1.5, 0.1, -0.31, 1.58); part(0.1, 1.5, 0.1, 0.31, 1.58); // arms hanging past its knees
  part(0.13, 1.2, 0.13, -0.12, 0.6); part(0.13, 1.2, 0.13, 0.12, 0.6);
  return g;
}
function gone() {
  if (!ent) return;
  G.scene.remove(ent.mesh);
  ent.mesh.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
  ent.mesh.children[0].material.dispose();
  ent = null;
}
// look down a long straight hallway: put it at the far end. returns true if it showed up
function appear() {
  const cam = G.camera, e = cam.position;
  cam.getWorldDirection(tmp);
  const h = Math.hypot(tmp.x, tmp.z);
  if (h < 0.5) return false;
  const d = [tmp.x / h, 0, tmp.z / h], o = [e.x, e.y, e.z];
  const hit = raycast(o, d, 90, BOXES);
  if (!hit || hit.t < 26) return false;
  const p = [o[0] + d[0] * (hit.t - 1.4), o[1], o[2] + d[2] * (hit.t - 1.4)];
  const floor = raycast(p, [0, -1, 0], 4, BOXES);
  if (!floor) return false;
  const room = [];
  for (const s of [-1, 1]) { const w = raycast([p[0], p[1], p[2]], [-d[2] * s, 0, d[0] * s], 4, BOXES); if (!w) return false; room.push(w.t); } // only in hallways
  const s = room[0] > room[1] ? -1 : 1, off = Math.max(0, Math.min(1.1, Math.max(room[0], room[1]) - 0.45)); // off to one side, not hidden behind your crosshair
  p[0] += -d[2] * s * off; p[2] += d[0] * s * off;
  ent = { mesh: figure(), born: performance.now() };
  ent.mesh.position.set(p[0], floor.point[1], p[2]);
  ent.mesh.rotation.y = Math.atan2(-d[0], -d[2]) + Math.PI; // facing you
  G.scene.add(ent.mesh);
  return true;
}
export function summonEntity() { gone(); return appear(); } // for testing: try right now

export function updateBackrooms(dt, flickMats) {
  const now = performance.now(), here = MAP.id === 'backrooms' && G.joined;
  hum(here, ent ? 0 : 1); // the hum stops while it's there
  if (MAP.id === 'backrooms') for (const m of flickMats) flicker(m, now);
  if (!here) { gone(); return; }
  if (ent) {
    const p = ent.mesh.position, c = G.camera.position;
    const dx = p.x - c.x, dy = p.y + 2 - c.y, dz = p.z - c.z, dist = Math.hypot(dx, dy, dz);
    G.camera.getWorldDirection(tmp);
    const look = (tmp.x * dx + tmp.y * dy + tmp.z * dz) / dist;
    if (dist < 15 || look < 0.85 || now - ent.born > 9000 || raycast([c.x, c.y, c.z], [dx / dist, dy / dist, dz / dist], dist - 0.5, BOXES)) gone();
    return;
  }
  if (now < nextTry) return;
  nextTry = now + 1500;
  // very rarely: only while you happen to look down a long hallway (a few % of the time), then a small chance, never twice in 4 minutes
  if (now > quietUntil && Math.random() < 0.06 && appear()) quietUntil = now + 240000;
}
