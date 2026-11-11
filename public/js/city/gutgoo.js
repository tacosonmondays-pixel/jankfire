// THE GUT'S BILE POOLS, the live part: bubbles that swell out of the goo and pop (with a small wet sound), and the
// ground mist catching the pools' green light (gutfog.js draws that; this file tells it where the nearest pools are).
// The owner: "make the acid glow a bit, a few bubbles that pop with sound effects ... make the fog reflect the light so
// it's a bit green over the puddles". The pools themselves (shape, bank, stain, light) are in shared/city/gut.js.
import * as THREE from 'three';
import { sfx } from '../audio.js';
import { setGutGoo } from './gutfog.js';

export const GUT_GOO = { on: true, bubbles: 14, near: 34, every: [0.18, 0.7], size: [0.07, 0.2], hear: 22, fog: 1 };
let Z = null;
export function startGoo(parent) { stopGoo(); Z = { parent, root: null, pool: [], spots: [], v: -1, next: 0.5 }; }
export function stopGoo() { if (!Z) return; if (Z.root) { Z.root.removeFromParent(); Z.geo.dispose(); Z.ringGeo.dispose(); Z.mat.dispose(); for (const b of Z.pool) b.ring.material.dispose(); } setGutGoo([]); Z = null; }
function build() {
  Z.root = new THREE.Group(); Z.root.name = 'gutgoo';
  Z.geo = new THREE.SphereGeometry(1, 10, 6, 0, Math.PI * 2, 0, Math.PI * 0.62); Z.ringGeo = new THREE.RingGeometry(0.82, 1, 14);
  Z.mat = new THREE.MeshBasicMaterial({ color: 0xd8ff7a, transparent: true, opacity: 0.62, depthWrite: false, fog: false });
  for (let i = 0; i < GUT_GOO.bubbles; i++) {
    const m = new THREE.Mesh(Z.geo, Z.mat), ring = new THREE.Mesh(Z.ringGeo, new THREE.MeshBasicMaterial({ color: 0xf0ffb0, transparent: true, opacity: 0, depthWrite: false, fog: false, side: THREE.DoubleSide }));
    ring.rotation.x = -Math.PI / 2; m.visible = ring.visible = false; m.userData.noShadow = ring.userData.noShadow = true; m.renderOrder = ring.renderOrder = 2;
    Z.root.add(m, ring); Z.pool.push({ m, ring, t: -1, life: 1, size: 0.1, pop: -1 });
  }
  Z.parent.add(Z.root);
}
// every bile pool in the loaded chunks (found again only when the set of chunks changes)
function spots(S) {
  if (Z.v === S.world.version) return Z.spots;
  const out = []; for (const r of S.chunks.values()) if (r && r.packed && r.packed.shapes) for (const s of r.packed.shapes) if (s.goo) out.push([s.goo[0], s.goo[3], s.goo[1], s.goo[2], s.sc[0], s.sc[2]]);
  Z.spots = out; Z.v = S.world.version; return out;
}
// once a frame from ingame.js
export function updateGoo(dt, S, camera) {
  if (!Z) return;
  const p = camera.position, all = GUT_GOO.on ? spots(S) : [], near = [];
  for (const g of all) { const d = Math.hypot(g[0] - p.x, g[2] - p.z); if (d < 60) near.push([d, g]); }
  near.sort((a, b) => a[0] - b[0]);
  setGutGoo(near.slice(0, 6).map(([d, g]) => [g[0], g[2], g[3], GUT_GOO.fog * Math.min(1, (60 - d) / 14)]));
  if (!near.length && !Z.root) return;
  if (!Z.root) build();
  // a new bubble now and then, in one of the pools close by (closer pools more often)
  Z.next -= dt;
  const close = near.filter((n) => n[0] < GUT_GOO.near);
  if (Z.next <= 0 && close.length) {
    Z.next = (GUT_GOO.every[0] + Math.random() * (GUT_GOO.every[1] - GUT_GOO.every[0])) * Math.max(1, 3 / close.length);
    const b = Z.pool.find((q) => q.t < 0 && q.pop < 0), g = close[Math.floor(Math.random() * Math.random() * close.length)][1];
    if (b) { const a = Math.random() * 6.283, r = Math.sqrt(Math.random()) * 0.5; // (inside the narrowest the lumpy outline gets)
      b.m.position.set(g[0] + Math.cos(a) * r * g[4], g[1], g[2] + Math.sin(a) * r * g[5]); b.size = GUT_GOO.size[0] + Math.random() * Math.random() * (GUT_GOO.size[1] - GUT_GOO.size[0]) * 2;
      b.life = 0.5 + Math.random() * 1.3; b.t = 0; b.m.visible = true; }
  }
  for (const b of Z.pool) {
    if (b.t >= 0) { // swelling: slow, then a wobble just before it goes
      b.t += dt; const k = Math.min(1, b.t / b.life), s = b.size * (0.15 + 0.85 * Math.sin(k * 1.5708)) * (1 + (k > 0.8 ? 0.08 * Math.sin(b.t * 40) : 0));
      b.m.scale.set(s, s * (0.7 + 0.3 * k), s);
      if (k >= 1) { b.t = -1; b.m.visible = false; b.pop = 0; b.ring.position.copy(b.m.position); b.ring.position.y += 0.02; b.ring.visible = true;
        const d = Math.hypot(b.m.position.x - p.x, b.m.position.y - p.y, b.m.position.z - p.z); if (d < GUT_GOO.hear) sfx.gooPop([b.m.position.x, b.m.position.y, b.m.position.z], 0.5 + b.size * 3); }
    } else if (b.pop >= 0) { // the pop: a ring running out over the goo
      b.pop += dt; const k = b.pop / 0.28, s = b.size * (1 + 2.6 * k); b.ring.scale.set(s, s, s); b.ring.material.opacity = 0.8 * (1 - k);
      if (k >= 1) { b.pop = -1; b.ring.visible = false; }
    }
  }
}
export const gooState = () => (Z ? { pools: Z.spots.length, live: Z.pool.filter((b) => b.t >= 0).length } : null);
