// Traffic, the client half: draws the server's cars (shared/traffic.js lanes, server/traffic.js driving), a little
// behind real time so they glide between updates. Wheels spin and steer, bodies dip when they brake and lean in the
// turns, headlights come on on dark maps, horns honk, the ice cream van plays its song. Crashes go off big: fireball,
// flash, shake, the wheels and doors fly, then a burning wreck for a while. You can stand on a car's roof (it carries
// you), you get pushed out of its side, and your bullets hit it instead of whoever is hiding behind it.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { MAP, BOXES } from '/shared/map.js';
import { CARS, CAR_IDS, CAR_COLORS, TRAFFIC_LEVELS, TRAFFIC_ORDER, trafficNet } from '/shared/traffic.js';
import { raycast, PH } from '/shared/physics.js';
import { makeCar, initCarMats, carMats } from './cars.js';
import { jankify } from './jank.js';
import { hazify } from './world.js';
import { fx } from './fx.js';
import { flameAt } from './flames.js';
import { sfx } from './audio.js';
import { ME } from './player.js';
import { hud } from './hud.js';
import { recordEv, RP_HOOKS } from './replay.js';

const LAG = 130; // ms behind the server clock (a bit more than the players: cars only update 12 times a second)
const F = { BRAKE: 1, HORN: 2, FREE: 4, SMOKE: 8, FIRE: 16, WRECK: 32, FLIP: 64 };
const cars = new Map(); // id -> view
const debris = [];
let ready = false, mapId = '', lightsOn = false;
const lastHit = new Map(); // victim id -> the car type that last hit them (for the kill line)

function patch(m) { // the map's look: jank vertex snap + the city's height haze
  jankify(m); const j = m.onBeforeCompile; hazify(m, 1); const h = m.onBeforeCompile;
  m.onBeforeCompile = (sh, r) => { j(sh, r); h(sh, r); };
  m.customProgramCacheKey = () => 'carhaze';
  return m;
}
function init() {
  if (ready) return;
  ready = true;
  initCarMats(patch);
}

// ------------------------------------------------------------ headlight beams + the pool of light on the road
let beamMat = null, poolMat = null;
const beamGeos = new Map();
function beamGeo(ty, lampPos) {
  if (beamGeos.has(ty)) return beamGeos.get(ty);
  const parts = [];
  for (const [x, y, z] of lampPos) {
    const len = 11, g = new THREE.ConeGeometry(1.9, len, 12, 1, true).toNonIndexed();
    g.rotateX(-Math.PI / 2); // apex back toward the lamp, open end forward
    g.rotateX(0.08); // aimed a little at the road
    g.translate(x, y - 0.35, z + len / 2);
    const pos = g.attributes.position, col = new Float32Array(pos.count * 4);
    for (let i = 0; i < pos.count; i++) { const k = Math.max(0, Math.min(1, (pos.getZ(i) - z) / len)); col[i * 4] = 1; col[i * 4 + 1] = 0.93; col[i * 4 + 2] = 0.72; col[i * 4 + 3] = 0.16 * (1 - k) * (1 - k); }
    g.setAttribute('color', new THREE.BufferAttribute(col, 4));
    g.deleteAttribute('uv'); g.deleteAttribute('normal');
    parts.push(g);
  }
  const m = parts.length > 1 ? (() => { const a = new THREE.BufferGeometry(), n = parts.reduce((s, p) => s + p.attributes.position.count, 0); const P = new Float32Array(n * 3), Cc = new Float32Array(n * 4); let o = 0; for (const p of parts) { P.set(p.attributes.position.array, o * 3); Cc.set(p.attributes.color.array, o * 4); o += p.attributes.position.count; } a.setAttribute('position', new THREE.BufferAttribute(P, 3)); a.setAttribute('color', new THREE.BufferAttribute(Cc, 4)); return a; })() : parts[0];
  beamGeos.set(ty, m);
  return m;
}
function lightMats() {
  if (beamMat) return;
  beamMat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 2, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,240,200,0.9)'); gr.addColorStop(0.5, 'rgba(255,220,160,0.35)'); gr.addColorStop(1, 'rgba(255,220,160,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  poolMat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.55, polygonOffset: true, polygonOffsetFactor: -4 });
}
const POOL_GEO = new THREE.PlaneGeometry(5, 9).rotateX(-Math.PI / 2);

// ------------------------------------------------------------ one car on screen
function addCar(id, code, set = cars) {
  init();
  const ty = CAR_IDS[code >> 4] || 'sedan', ci = code & 15, T = CARS[ty];
  const v = makeCar(ty, CAR_COLORS[ci % CAR_COLORS.length], ci, patch);
  G.scene.add(v.root);
  lightMats();
  const beams = new THREE.Mesh(beamGeo(ty, v.lampPos), beamMat); beams.frustumCulled = false;
  const pool = new THREE.Mesh(POOL_GEO, poolMat); pool.position.set(0, 0.06, T.L / 2 + 4.6);
  v.body.add(beams); v.root.add(pool);
  const car = { id, ty, T, ci, v, beams, pool, snaps: [], seen: 0, f: 0, pf: 0, x: 0, y: 0, z: 0, h: 0, sp: 0, pitch: 0, roll: 0, lastH: null, yawRate: 0, lastV: 0, acc: 0, wheelA: 0,
    hornT: 0, smokeT: 0, jingleT: Math.random() * 4000, passT: 0, wrecked: false, gone: 0, blink: 0 };
  set.set(id, car);
  return car;
}
function removeCar(c, set = cars) {
  G.scene.remove(c.v.root);
  set.delete(c.id);
}
function wreckLook(c) {
  if (c.wrecked) return;
  c.wrecked = true;
  c.v.bodyMesh.material = carMats.wreck;
  if (c.v.lamps) c.v.lamps.material = carMats.lampOff;
  if (c.v.tails) c.v.tails.material = carMats.lampOff;
  if (c.v.inds) c.v.inds.material = carMats.lampOff;
  for (const m of c.v.body.children) if (m.material && m.material.map) m.visible = false; // the livery burns off
  c.beams.visible = false; c.pool.visible = false;
  c.v.wheels.forEach((w, i) => { if (i !== 1) w.pivot.visible = false; }); // the wheels flew off (one hangs on)
}

// ------------------------------------------------------------ network
net.on('trc', () => clearTraffic());
function ingest(set, m) {
  for (const r of m.c) {
    const [id, code, x, y, z, h, sp, f, pitch, roll] = r;
    const c = set.get(id) || addCar(id, code, set);
    c.snaps.push({ s: m.s, x, y, z, h, sp, f, pitch, roll });
    if (c.snaps.length > 10) c.snaps.shift();
    c.seen = m.s;
  }
  for (const c of set.values()) if (c.seen !== m.s && !c.gone) c.gone = m.s; // dropped: out past the fog, or a wreck towed away
}
net.on('tr', (m) => {
  if (!G.scene) return;
  ingest(cars, m);
  recordEv(m); // (so your killcam has the cars too)
});
net.on('carx', (m) => {
  recordEv(m);
  const c = cars.get(m.id), p = m.p, big = m.r > 10;
  boomFx(p, m.r, c);
  if (c) wreckLook(c);
  const d = Math.hypot(p[0] - ME.pos[0], p[1] - ME.pos[1], p[2] - ME.pos[2]);
  G.shake = Math.max(G.shake, Math.max(0, 1.25 - d / (big ? 45 : 35)));
  if (d < 30) flash(Math.max(0.25, 1 - d / 30));
  // callouts: you blew it up, or you saw two cars meet
  if (m.by && m.by === G.myId) hud.msg(m.o ? 'INSURANCE FRAUD' : 'CAR BOMB', 1.4, 'brag');
  else if (m.o && d < 70 && m.id < m.o) hud.msg(pick(['TRAFFIC ACCIDENT', 'FENDER BENDER', 'CAR-NAGE', 'NO INSURANCE']), 1.2, 'brag');
});
net.on('carhit', (m) => {
  recordEv(m);
  lastHit.set(m.to, m.ty);
  const p = m.p, hard = m.s > 25;
  sfx.carHit(p, Math.min(1, m.s / 50));
  fx.dust([p[0], p[1] - 0.9, p[2]], hard ? 14 : 6);
  if (hard) fx.sparks(p, [0, 0, 0], 14, true);
  if (m.to === G.myId) {
    G.shake = Math.max(G.shake, hard ? 1.2 : 0.6);
    if (G.punch) { G.punch.vz = (G.punch.vz || 0) + (Math.random() < 0.5 ? -1 : 1) * (hard ? 26 : 10); G.punch.vx = (G.punch.vx || 0) - (hard ? 14 : 5); } // tumbling
    if (!m.ko) hud.msg(pick(['LOOK BOTH WAYS', 'BEEP BEEP', 'YEET', 'JAYWALKER']), 1.1, 'brag');
    flash(hard ? 0.7 : 0.3, '#ffffff');
  }
});
net.on('carcrash', (m) => sfx.carHit(m.p, 0.8));

// ------------------------------------------------------------ juice
let flashEl = null;
function flash(k, color = '#ffb347') {
  if (!flashEl) {
    flashEl = document.createElement('div');
    Object.assign(flashEl.style, { position: 'fixed', inset: '0', pointerEvents: 'none', zIndex: 5, opacity: '0', transition: 'opacity 0.45s ease-out', mixBlendMode: 'screen' });
    document.body.append(flashEl);
  }
  flashEl.style.background = `radial-gradient(circle, ${color} 0%, rgba(255,80,20,0.5) 55%, rgba(255,40,0,0) 100%)`;
  flashEl.style.transition = 'none'; flashEl.style.opacity = String(Math.min(1, k));
  requestAnimationFrame(() => { flashEl.style.transition = 'opacity 0.5s ease-out'; flashEl.style.opacity = '0'; });
}
const pick = (a) => a[(Math.random() * a.length) | 0];
const R = (s = 1) => (Math.random() - 0.5) * 2 * s;
const panelMats = new Map();
function panelMat(hex) { if (!panelMats.has(hex)) panelMats.set(hex, patch(new THREE.MeshLambertMaterial({ color: hex, flatShading: true }))); return panelMats.get(hex); }
function boomFx(p, r, c) {
  sfx.carBoom(p, r > 10);
  fx.explosion(p, r * 0.55);
  fx.explosion([p[0] + R(1), p[1] + 1.2, p[2] + R(1)], r * 0.35);
  fx.ring([p[0], (c ? c.y : p[1] - 1), p[2]], r * 1.3, 0xfff2b0, 0.5);
  fx.ring([p[0], (c ? c.y : p[1] - 1), p[2]], r * 0.9, 0xff8a3a, 0.7);
  const P = fx.parts && fx.parts();
  if (P) {
    for (let i = 0; i < 90; i++) { const a = Math.random() * 6.28, s = 6 + Math.random() * 18, u = Math.random(); P.fire.spawn(p[0], p[1], p[2], Math.cos(a) * s * (1 - u * 0.6), 3 + u * 16, Math.sin(a) * s * (1 - u * 0.6), 0.5 + Math.random() * 0.6, 0.9, 3.2, 0xffffc0, 0xff3a00, 1, -3, 2.6); }
    for (let i = 0; i < 40; i++) P.smoke.spawn(p[0] + R(2), p[1] + Math.random() * 2, p[2] + R(2), R(4), 3 + Math.random() * 4, R(4), 2.2 + Math.random() * 1.5, 1.2, 5, 0x3a3434, 0x121010, 0.8, -0.6, 0.8);
    for (let i = 0; i < 40; i++) P.misc.spawn(p[0], p[1], p[2], R(12), 4 + Math.random() * 10, R(12), 1 + Math.random(), 0.09, 0.07, Math.random() < 0.5 ? 0xbfe4ff : 0xffffff, 0x88a8c8, 1, 22, 0.4); // glass
  }
  if (!c) return;
  // the wheels pop off and bounce away; doors, bonnet and a bumper go flying
  const sn = Math.sin(c.h), cs = Math.cos(c.h);
  for (const w of c.v.wheels) {
    if (debris.length > 60) break;
    const m = w.spin.children[0].clone();
    const wp = new THREE.Vector3(); w.pivot.getWorldPosition(wp);
    m.position.copy(wp); m.rotation.y = c.h + (w.side < 0 ? Math.PI : 0);
    G.scene.add(m);
    const out = [w.side * cs, w.side * -sn]; // sideways out of the car
    debris.push({ m, v: [out[0] * (5 + Math.random() * 6) + R(2), 7 + Math.random() * 7, out[1] * (5 + Math.random() * 6) + R(2)], w: [R(14), R(4), R(14)], r: w.r, life: 7, bounce: 0.55 });
  }
  const hex = CAR_COLORS[c.ci % CAR_COLORS.length];
  const panels = [[1.4, 0.05, 1.1], [0.06, 0.8, 1.0], [0.06, 0.8, 1.0], [c.T.W, 0.18, 0.14], [1.2, 0.05, 1.0]];
  for (const [sx, sy, sz] of panels) {
    if (debris.length > 60) break;
    const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), panelMat(c.ty === 'taxi' ? '#ffd21a' : hex));
    m.position.set(p[0] + R(1), p[1] + Math.random(), p[2] + R(1)); m.rotation.set(R(3), R(3), R(3));
    G.scene.add(m);
    debris.push({ m, v: [R(13), 9 + Math.random() * 12, R(13)], w: [R(10), R(10), R(10)], r: Math.max(sx, sy, sz) * 0.3, life: 6, bounce: 0.3, geo: true });
  }
}
function updateDebris(dt) {
  for (let i = debris.length - 1; i >= 0; i--) {
    const d = debris[i], m = d.m;
    d.life -= dt;
    d.v[1] -= 24 * dt;
    m.position.x += d.v[0] * dt; m.position.y += d.v[1] * dt; m.position.z += d.v[2] * dt;
    m.rotation.x += d.w[0] * dt; m.rotation.y += d.w[1] * dt; m.rotation.z += d.w[2] * dt;
    if (d.v[1] < 0) {
      const hit = raycast([m.position.x, m.position.y + 0.5, m.position.z], [0, -1, 0], 0.5 + d.r + Math.abs(d.v[1] * dt), BOXES);
      if (hit && m.position.y - d.r <= hit.point[1] + 0.02) {
        m.position.y = hit.point[1] + d.r;
        d.v[1] = Math.abs(d.v[1]) > 3 ? -d.v[1] * d.bounce : 0;
        d.v[0] *= 0.7; d.v[2] *= 0.7; d.w[0] *= 0.6; d.w[2] *= 0.6;
        if (Math.abs(d.v[1]) > 2) sfx.clang && Math.random() < 0.3 && sfx.clang([m.position.x, m.position.y, m.position.z], 0.25);
      }
    }
    if (d.life < 4 && Math.random() < dt * 6) fx.smoke([m.position.x, m.position.y + 0.2, m.position.z], 1, 0.1);
    if (d.life < 0.6) m.scale.setScalar(Math.max(0.01, d.life / 0.6));
    if (d.life <= 0 || m.position.y < MAP.killY - 60) { G.scene.remove(m); if (d.geo) m.geometry.dispose(); debris.splice(i, 1); }
  }
}

// ------------------------------------------------------------ every frame
const lerpA = (a, b, k) => { let d = b - a; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2; return a + d * k; };
export function clearTraffic() {
  for (const c of [...cars.values()]) removeCar(c);
  for (const d of debris) G.scene.remove(d.m);
  debris.length = 0;
}
export function updateTraffic(dt, now, hide) {
  if (!G.scene) return;
  if (MAP.id !== mapId) { mapId = MAP.id; clearTraffic(); const net0 = trafficNet(mapId); lightsOn = !!(net0 && net0.lights); }
  syncUI();
  updateDebris(dt);
  if (cars.size) drawSet(cars, now + G.offset - LAG, dt, now, hide);
}
// move + animate one set of cars to time rt (server clock): the live ones, or a replay's ghosts
function drawSet(set, rt, dt, now, hide) {
  const cam = G.camera.position;
  for (const c of [...set.values()]) {
    if (c.gone && rt > c.gone + 200) { removeCar(c, set); continue; }
    const sn = c.snaps;
    if (!sn.length) continue;
    let a = sn[0], b = sn[0];
    for (let i = sn.length - 1; i >= 0; i--) if (sn[i].s <= rt) { a = sn[i]; b = sn[i + 1] || sn[i]; break; }
    const span = b.s - a.s, k = span > 0 ? Math.max(0, Math.min(1, (rt - a.s) / span)) : 0;
    let x = a.x + (b.x - a.x) * k, y = a.y + (b.y - a.y) * k, z = a.z + (b.z - a.z) * k;
    const h = lerpA(a.h, b.h, k), sp = a.sp + (b.sp - a.sp) * k;
    if (b === a && rt > a.s && !(a.f & F.WRECK)) { const ex = Math.min(0.15, (rt - a.s) / 1000); x += Math.sin(h) * sp * ex; z += Math.cos(h) * sp * ex; } // a beat late: keep rolling
    const f = (rt >= b.s ? b : a).f;
    c.pf = c.f; c.f = f;
    // derived motion: turn rate (steering), acceleration (pitch), lean
    if (c.lastH != null && dt > 0) { c.yawRate += (lerpA(0, h - c.lastH, 1) / dt - c.yawRate) * Math.min(1, dt * 8); c.acc += ((sp - c.lastV) / dt - c.acc) * Math.min(1, dt * 6); }
    c.lastH = h; c.lastV = sp;
    c.x = x; c.y = y; c.z = z; c.h = h; c.sp = sp;
    const V = c.v, root = V.root;
    root.position.set(x, y, z);
    const free = !!(f & F.FREE);
    root.rotation.order = 'YXZ';
    if (free) root.rotation.set(lerpA(a.pitch, b.pitch, k), h, lerpA(a.roll, b.roll, k));
    else root.rotation.set(0, h, 0);
    if (f & F.WRECK) wreckLook(c);
    const near = Math.hypot(x - cam.x, z - cam.z), vis = !hide && near < (G.scene.fog ? G.scene.fog.far + 30 : 600);
    root.visible = vis;
    if (!vis) continue;
    if (!c.wrecked) {
      const steer = free ? 0 : Math.max(-0.55, Math.min(0.55, Math.atan(V.wb * c.yawRate / Math.max(2.5, sp))));
      c.wheelA += (free ? 0 : sp) * dt;
      for (const w of V.wheels) { w.spin.rotation.x = c.wheelA / w.r; if (w.front) w.pivot.rotation.y += (steer - w.pivot.rotation.y) * Math.min(1, dt * 10); }
      V.body.rotation.x = Math.max(-0.05, Math.min(0.06, -c.acc * 0.011));
      V.body.rotation.z = Math.max(-0.07, Math.min(0.07, sp * c.yawRate * 0.016));
      V.body.position.y = Math.sin(now * 0.017 + c.id) * 0.012 * Math.min(1, sp / 8);
      if (V.tails) V.tails.material = f & F.BRAKE || lightsOn ? carMats.tailOn : carMats.tail;
      c.blink += dt;
      const hazards = (free || f & F.FIRE) && Math.floor(c.blink * 2.5) % 2 === 0;
      if (V.inds) V.inds.material = hazards ? carMats.indOn : carMats.ind;
      c.beams.visible = lightsOn; c.pool.visible = lightsOn && !free;
    }
    // sounds: honk on the rising edge, the song, a whoosh going past you
    const pos = [x, y + 1, z];
    if (f & F.HORN && !(c.pf & F.HORN) && now > c.hornT) { c.hornT = now + 450; sfx.horn(pos, c.ty); }
    if (c.ty === 'icecream' && !c.wrecked && near < 80 && now > c.jingleT) { c.jingleT = now + 6500; sfx.jingle(pos); }
    if (!c.wrecked && sp > 9 && near < 6 && now > c.passT) { c.passT = now + 1500; sfx.carPass(pos, sp); }
    // smoke and fire (real flames on the hood, the whole wreck going up once it's wrecked: flames.js)
    if (f & (F.FIRE | F.WRECK)) {
      if (c.wrecked) { flameAt('car' + c.id, [x, y + c.T.H * 0.15, z], c.T.W * 1.1, c.T.H * 1.5, 1.1); flameAt('car' + c.id + 'b', [x + Math.sin(h) * c.T.L * 0.3, y + c.T.H * 0.3, z + Math.cos(h) * c.T.L * 0.3], c.T.W * 0.8, c.T.H * 1.1, 1.2); }
      else flameAt('car' + c.id, [x + Math.sin(h) * c.T.L * 0.32, y + c.T.H * 0.62, z + Math.cos(h) * c.T.L * 0.32], c.T.W * 0.55, 1.2, 1);
    }
    c.smokeT -= dt;
    if (c.smokeT <= 0 && f & (F.SMOKE | F.FIRE | F.WRECK)) {
      c.smokeT = f & F.WRECK ? 0.03 : 0.08;
      const hood = c.wrecked ? [x, y + c.T.H * 0.6, z] : [x + Math.sin(h) * c.T.L * 0.32, y + c.T.H * 0.75, z + Math.cos(h) * c.T.L * 0.32];
      const P = fx.parts && fx.parts();
      if (f & (F.FIRE | F.WRECK) && Math.random() < 0.3) fx.burn([hood[0] + R(c.wrecked ? c.T.W * 0.4 : 0.3), hood[1] - 0.6, hood[2] + R(c.wrecked ? c.T.L * 0.3 : 0.3)]); // (a few loose sparks)
      if (P) P.smoke.spawn(hood[0] + R(0.3), hood[1], hood[2] + R(0.3), R(0.4), 1.6 + Math.random(), R(0.4), 2.4 + Math.random(), 0.4, c.wrecked ? 3.4 : 2, f & (F.FIRE | F.WRECK) ? 0x2a2626 : 0xd8d8d8, f & (F.FIRE | F.WRECK) ? 0x0e0c0c : 0x8a8a8a, 0.6, -0.4, 0.4);
      else fx.smoke(hood, 1, 0.2);
    }
  }
}

// ------------------------------------------------------------ you vs cars: pushed out of the side, carried on the roof
const box = (c) => ({ x: c.x, z: c.z, s: Math.sin(c.h), co: Math.cos(c.h), hu: c.T.L / 2, hv: c.T.W / 2 });
export function carCollide(dt) {
  if (!ME.alive || !cars.size) return;
  const p = ME.pos, R0 = PH.halfW;
  for (const c of cars.values()) {
    if (c.gone || Math.abs(c.x - p[0]) > c.T.L || Math.abs(c.z - p[2]) > c.T.L) continue;
    const top = c.y + c.T.H * (c.f & F.FLIP ? 0.7 : 1);
    if (p[1] > top + 0.6 || p[1] + PH.height < c.y + 0.15) continue;
    const b = box(c), dx = p[0] - b.x, dz = p[2] - b.z, lu = dx * b.s + dz * b.co, lv = dx * b.co - dz * b.s;
    const ou = b.hu + R0 - Math.abs(lu), ov = b.hv + R0 - Math.abs(lv);
    if (ou <= 0 || ov <= 0) continue;
    const vx = c.f & F.FREE ? 0 : Math.sin(c.h) * c.sp, vz = c.f & F.FREE ? 0 : Math.cos(c.h) * c.sp;
    if (p[1] >= top - 0.55 && ME.vel[1] <= 0.5) { // on the roof: stand there and ride along. car surfing
      p[1] = top; if (ME.vel[1] < 0) ME.vel[1] = 0; ME.onGround = true;
      p[0] += vx * dt; p[2] += vz * dt;
      continue;
    }
    if (c.sp > 2 && !(c.f & F.WRECK)) continue; // a moving car hits you (the server's call), it doesn't nudge you along in front of it
    // against the side: out the shallow way, and lose the speed you had going into it
    if (ou < ov) { const sg = Math.sign(lu) || 1; p[0] += b.s * sg * ou; p[2] += b.co * sg * ou; const into = -(ME.vel[0] * b.s + ME.vel[2] * b.co) * sg; if (into > 0) { ME.vel[0] += b.s * sg * into; ME.vel[2] += b.co * sg * into; } }
    else { const sg = Math.sign(lv) || 1; p[0] += b.co * sg * ov; p[2] -= b.s * sg * ov; const into = -(ME.vel[0] * b.co - ME.vel[2] * b.s) * sg; if (into > 0) { ME.vel[0] += b.co * sg * into; ME.vel[2] -= b.s * sg * into; } }
  }
}

// ------------------------------------------------------------ bullets and swings hit cars
// the nearest car a ray from o along d hits before maxT: { t, id, n } or null
export function carRay(o, d, maxT) {
  let best = null;
  for (const c of cars.values()) {
    if (c.gone || c.wrecked) continue;
    const s = Math.sin(c.h), co = Math.cos(c.h);
    // into the car's frame: u forward, v sideways, y up
    const ox = o[0] - c.x, oz = o[2] - c.z, ou = ox * s + oz * co, ov = ox * co - oz * s, oy = o[1] - c.y;
    const du = d[0] * s + d[2] * co, dv = d[0] * co - d[2] * s, dy = d[1];
    let t0 = 0, t1 = best ? best.t : maxT, ax = -1;
    for (const [oo, dd, lo, hi, k] of [[ou, du, -c.T.L / 2, c.T.L / 2, 0], [ov, dv, -c.T.W / 2, c.T.W / 2, 1], [oy, dy, 0.25, c.T.H, 2]]) {
      if (Math.abs(dd) < 1e-8) { if (oo < lo || oo > hi) { t0 = 1e9; break; } continue; }
      let a = (lo - oo) / dd, b = (hi - oo) / dd; if (a > b) [a, b] = [b, a];
      if (a > t0) { t0 = a; ax = k; }
      if (b < t1) t1 = b;
      if (t0 > t1) break;
    }
    if (t0 <= t1 && t0 < (best ? best.t : maxT) && t0 >= 0) {
      const n = ax === 0 ? [s * -Math.sign(du), 0, co * -Math.sign(du)] : ax === 1 ? [co * -Math.sign(dv), 0, -s * -Math.sign(dv)] : [0, -Math.sign(dy), 0];
      best = { t: t0, id: c.id, n };
    }
  }
  return best;
}
export function carHit(id, w, n, d) {
  net.send({ t: 'car', id, w, n, d: d.map((x) => Math.round(x * 100) / 100) });
}
// a melee swing: the nearest car in front within reach
export function carSwing(o, d, reach, w) {
  const h = carRay(o, d, reach + 0.8);
  if (!h) return false;
  carHit(h.id, w, 1, d);
  const p = [o[0] + d[0] * h.t, o[1] + d[1] * h.t, o[2] + d[2] * h.t];
  fx.sparks(p, d, 10, false); sfx.carHit(p, 0.3);
  return true;
}

// ------------------------------------------------------------ the kill feed: its own icon and silly lines
const LINES = {
  hatch: 'got beeped out of existence', sedan: 'got hit by a car', taxi: 'took the wrong taxi', pickup: 'got truck-kun\'d by a pickup',
  van: 'got hit by a suspicious van', icecream: 'got run over by the ice cream van (it was pink)', bus: 'missed the bus. the bus did not miss', truck: 'got isekai\'d by a truck',
};
const EXTRA = ['forgot to look both ways', 'became a speed bump', 'jaywalked into the afterlife', 'lost a fight with traffic'];
export function carKill(m, kn, kc, vn, vc, wname, wcolor) {
  const ty = lastHit.get(m.v);
  if (m.w === 'car') {
    const line = ty && Math.random() < 0.75 ? LINES[ty] : pick(EXTRA);
    if (m.k) return { parts: [[kn, kc], [`  [${wname(m.via)}]  `, wcolor(m.via)], ['[CAR]', '#ffe14d'], [vn, vc], ['  into traffic', '#aaa']], dead: [[kn, kc], [' shoved you into traffic', '#fff'], [`  (${wname(m.via)})`, wcolor(m.via)]] };
    return { parts: [[vn, vc], ['  ', '#fff'], ['[CAR]', '#ffe14d'], [`  ${line}`, '#ff8a3a']], dead: [[`you ${line.replace(/^got /, 'got ')}`, '#fff']] };
  }
  if (m.k && m.k !== m.v && !m.via) return { parts: [[kn, kc], ['  [Car Bomb]  ', '#ff7a1a'], ['[CAR]', '#ffe14d'], [vn, vc]], dead: [['killed by ', '#fff'], [kn, kc], ["'s car bomb", '#ff7a1a']] };
  if (m.k && m.via) return { parts: [[kn, kc], [`  [${wname(m.via)}]  `, wcolor(m.via)], ['[CAR]', '#ffe14d'], [vn, vc], ['  into a car crash', '#aaa']], dead: [[kn, kc], [' threw you into a car crash', '#fff']] };
  return { parts: [[vn, vc], ['  ', '#fff'], ['[CAR]', '#ffe14d'], ['  was too close to a car crash', '#ff8a3a']], dead: [['you were too close to a car crash', '#fff']] };
}
// swap the [CAR] tag in the newest feed line for the little car icon
const ICON = 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 20"><path d="M3 14 L3 9 L9 8 L14 3 L27 3 L32 8 L38 9 L38 14 Z" fill="#ff4fd8" stroke="#111" stroke-width="2" stroke-linejoin="round"/><path d="M15 5 L20 5 L20 8 L12 8 Z M22 5 L26 5 L29 8 L22 8 Z" fill="#4fd8ff"/><circle cx="11" cy="15" r="3.6" fill="#ffe14d" stroke="#111" stroke-width="2"/><circle cx="30" cy="15" r="3.6" fill="#ffe14d" stroke="#111" stroke-width="2"/></svg>`);
export function carFeedIcon() {
  const line = document.querySelector('#feed > div');
  if (!line) return;
  for (const s of line.children) if (s.textContent === '[CAR]') { s.textContent = ''; const im = document.createElement('img'); im.src = ICON; Object.assign(im.style, { height: '1.05em', verticalAlign: '-0.15em', margin: '0 0.2em' }); s.append(im); }
}

// ------------------------------------------------------------ Match Settings > traffic
let sel = null;
function syncUI() {
  if (!sel) {
    const hip = document.getElementById('cfgHip');
    if (!hip) return;
    const lab = document.createElement('label');
    lab.textContent = 'traffic ';
    sel = document.createElement('select'); sel.id = 'cfgTraffic';
    for (const k of TRAFFIC_ORDER) { const o = document.createElement('option'); o.value = k; o.textContent = TRAFFIC_LEVELS[k].name + (k === 'auto' ? ' (off in Plant & Defuse)' : ''); sel.append(o); }
    lab.append(sel);
    hip.parentElement.after(lab);
    sel.addEventListener('change', () => net.send({ t: 'cfg', traffic: sel.value }));
  }
  const want = (G.cfg && G.cfg.traffic) || 'auto';
  if (sel.value !== want && document.activeElement !== sel) sel.value = want;
  sel.parentElement.style.display = G.mode === 'training' || !trafficNet(G.cfg && G.cfg.map) ? 'none' : '';
}
export const trafficDebug = () => [...cars.values()].map((c) => [c.id, c.ty, Math.round(c.x), Math.round(c.z), Math.round(c.sp), c.f]); // (tests and clip recorders read this)

// ------------------------------------------------------------ killcams + the play of the round: ghost cars
// the clips carry the cars' updates ('tr') and their crashes and hits as events; this draws them at replay time
const ghosts = new Map();
RP_HOOKS.push({
  ev(m) {
    if (m.t === 'tr') { if (G.scene) ingest(ghosts, m); return true; }
    if (m.t === 'carx') { const c = ghosts.get(m.id); boomFx(m.p, m.r, c); if (c) wreckLook(c); return true; }
    if (m.t === 'carhit') { sfx.carHit(m.p, Math.min(1, m.s / 50)); fx.dust([m.p[0], m.p[1] - 0.9, m.p[2]], 10); return true; }
    return false;
  },
  step(t, _g, dt) { if (ghosts.size) drawSet(ghosts, t - 90, dt, performance.now(), false); },
  stop() { for (const c of [...ghosts.values()]) removeCar(c, ghosts); },
});
export const trafficGhosts = () => [...ghosts.values()].filter((c) => c.v.root.visible).map((c) => [c.id, c.ty, Math.round(c.x), Math.round(c.z)]); // (tests)
