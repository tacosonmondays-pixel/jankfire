// OVERDUE driving (WP7) on the client: the story's cars in the world, F to get in and out, the car physics
// (shared/story/drive.js) in place of the player step while you drive, a chase camera that follows your mouse, drive-bys
// with a sidearm, crashes, getting thrown through the windscreen, and the boost heat on the HUD. the sim
// (shared/story/carsys.js) owns the cars and checks every update.
//   W / S: drive / brake + reverse · A / D: steer · Space: handbrake (drift) · Shift: boost (it overheats) · F: get out
import * as THREE from 'three';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { ME } from '../player.js';
import { W } from '../weapons.js';
import { synth } from '../audio.js';
import { makeCar, initCarMats, carMats } from '../cars.js';
import { BOXES } from '/shared/map.js';
import { query, raycast, PH } from '/shared/physics.js';
import { WEAPONS } from '/shared/weapons.js';
import { useBar } from './bar.js';
import { newCar, stepCar, carType, seatOf, speedOf, fwdOf, STORY_CARS } from '/shared/story/drive.js';

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const world = { query: (a, b, c, d, out) => query(BOXES, a, b, c, d, out), raycast: (o, d, m) => raycast(o, d, m, BOXES) };
const NAMES = { sofa: 'THE SOFA-CAR', hatch: 'A HATCHBACK', sedan: 'A SALOON', taxi: 'A TAXI', pickup: 'A PICKUP', van: 'A VAN', icecream: 'THE ICE CREAM VAN', bus: 'A BUS', truck: 'A BOX TRUCK' };
export const DV = { car: null, id: 0, meshes: new Map(), sendT: 0, heatEl: null }; // car: the one you drive (drive.js state)
let story = null;

export function initDrive(s) {
  story = s;
  s.on('cars', (m) => { clearCars(); for (const c of m.list || []) place(c); });
  s.on('carIn', (m) => getIn(m.car));
  s.on('carOut', (m) => { const x = DV.meshes.get(m.id); if (m.towed && x) { x.c.p = m.p; x.c.h = m.h; pose(x, m.p, m.h); hud.msg('YOUR CAR FELL INTO THE VOID. IT WAS TOWED.', 2); } });
  s.on('carFix', (m) => { // the sim said no (too fast / teleport / taken / too far)
    if (DV.car && DV.id === m.id && m.p) { Object.assign(DV.car, { x: m.p[0], y: m.p[1], z: m.p[2], h: m.h, vx: 0, vy: 0, vz: 0 }); }
    else if (m.why === 'taken') hud.msg('SOMEBODY\'S IN IT', 1.2);
  });
}
export const driving = () => !!DV.car;

// ------------------------------------------------------------ the cars in the world
function sofaCar(colHex) { // the Bottom's sofa-car (ART_BIBLE model 9): a pink couch bolted onto a go-kart frame
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const M = (c) => new THREE.MeshLambertMaterial({ color: c, flatShading: true });
  const box = (w, h, d, c, x, y, z, rx = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c)); m.position.set(x, y, z); m.rotation.x = rx; body.add(m); return m; };
  const col = new THREE.Color(colHex).getHex(), dark = new THREE.Color(colHex).multiplyScalar(0.7).getHex();
  box(1.7, 0.12, 2.8, 0x3a3a44, 0, 0.42, 0); // the frame
  box(1.7, 0.38, 1.5, col, 0, 0.7, -0.3); box(1.7, 0.75, 0.32, col, 0, 1.15, -1.05, -0.12); // seat + back
  for (const sx of [-0.92, 0.92]) box(0.26, 0.55, 1.5, dark, sx, 0.88, -0.3); // arms
  for (const sx of [-0.4, 0.4]) box(0.78, 0.14, 1.3, 0xffb3d9, sx, 0.95, -0.25); // cushions
  box(0.06, 0.6, 0.06, 0x222222, 0, 0.9, 0.75, -0.6); const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.035, 6, 14), M(0x222222)); wheel.position.set(0, 1.18, 0.6); wheel.rotation.x = -0.9; body.add(wheel);
  box(0.25, 0.2, 0.15, 0xffe14d, 0.6, 0.6, 1.4); box(0.25, 0.2, 0.15, 0xffe14d, -0.6, 0.6, 1.4); // headlights (two desk lamps)
  box(0.5, 0.35, 0.4, 0x7dff4f, 0, 0.6, 1.2); // a crate of something on the front
  const wheels = [];
  for (const [x, z] of [[-0.95, 0.95], [0.95, 0.95], [-0.95, -0.95], [0.95, -0.95]]) {
    const pivot = new THREE.Group(), spin = new THREE.Group(); pivot.position.set(x, 0.32, z);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.25, 10), M(0x1a1a1a)); m.rotation.z = Math.PI / 2;
    spin.add(m); pivot.add(spin); root.add(pivot); wheels.push({ pivot, spin, r: 0.32, steer: z > 0 });
  }
  return { root, body, wheels };
}
function build(c) {
  if (c.ty === 'sofa') return sofaCar(c.col);
  if (!carMats.body) initCarMats((m) => m);
  const v = makeCar(c.ty, c.col, c.id, (m) => m);
  v.wheels.forEach((w) => { w.steer = w.z > 0; });
  return v;
}
function place(c) {
  if (!G.scene) return;
  const v = build(c);
  G.scene.add(v.root);
  const x = { c, v };
  DV.meshes.set(c.id, x);
  pose(x, c.p, c.h);
}
function pose(x, p, h, roll = 0, pitch = 0) { x.v.root.position.set(p[0], p[1], p[2]); x.v.root.rotation.set(0, h, 0); x.v.body.rotation.set(pitch, 0, roll); }
export function clearCars() { for (const x of DV.meshes.values()) G.scene.remove(x.v.root); DV.meshes.clear(); if (DV.car) endDrive(false); }
export function nearestCar(r = 3.6) {
  let best = null, bd = r;
  for (const x of DV.meshes.values()) { if (x.c.driver && x.c.id !== DV.id) continue; const T = carType(x.c.ty), d = Math.hypot(ME.pos[0] - x.c.p[0], ME.pos[2] - x.c.p[2]) - T.W / 2 - Math.max(0, T.L / 2 - T.W / 2) * 0.6; if (d < bd && Math.abs(ME.pos[1] - x.c.p[1]) < 3) { bd = d; best = x.c; } }
  return best;
}
export const carName = (c) => NAMES[c.ty] || 'A CAR';

// ------------------------------------------------------------ in and out
export function tryEnter() { const c = nearestCar(); if (c) story.send('carIn', { id: c.id }); return !!c; }
function getIn(c) {
  const x = DV.meshes.get(c.id);
  if (!x) return;
  DV.car = newCar(c.ty, c.p, c.h); DV.car.hp = c.hp; DV.id = c.id; x.c.driver = 1;
  ME.yaw = c.h + Math.PI; ME.pitch = -0.12; // look the way it faces (the camera's forward is -z at yaw 0)
  hud.msg(`YOU'RE DRIVING ${carName(c)}`, 1.4, 'brag');
  synth.tone('sawtooth', 70, 140, 0.5, 0.15); synth.noise(0.4, 0.3, 'lowpass', 300, 900);
  const sec = W.slots.findIndex((id) => id && WEAPONS[id] && WEAPONS[id].slot === 'secondary'); // drive-bys are sidearms
  if (sec >= 0 && sec !== W.slot) useBar(sec);
}
// out you get: beside the door (or thrown out the front at speed)
export function endDrive(send = true, fling = null) {
  const car = DV.car, x = DV.meshes.get(DV.id);
  if (!car) return;
  const f = fwdOf(car), left = [f[2], 0, -f[0]], T = carType(car.ty);
  if (fling) { ME.pos = [car.x + f[0] * (T.L / 2 + 0.6), car.y + T.H + 0.3, car.z + f[2] * (T.L / 2 + 0.6)]; ME.vel = [car.vx * 0.9, 9, car.vz * 0.9]; }
  else { ME.pos = exitSpot(car, T, f, left); ME.vel = [car.vx * 0.3, 0, car.vz * 0.3]; }
  if (x) { x.c.p = [car.x, car.y, car.z]; x.c.h = car.h; x.c.driver = 0; x.c.hp = car.hp; }
  if (send) story.send('carOut', { id: DV.id, p: [car.x, car.y, car.z], h: car.h });
  DV.car = null; DV.id = 0;
  if (DV.heatEl) DV.heatEl.classList.add('hidden');
}

// where you can stand when you get out: the left door, the right, behind, else on the roof (never inside a wall)
function exitSpot(car, T, f, left) {
  const free = (p) => !query(BOXES, p[0] - PH.halfW, p[2] - PH.halfW, p[0] + PH.halfW, p[2] + PH.halfW, []).some((b) => !b.car && b.max[1] > p[1] + PH.step && b.min[1] < p[1] + PH.height && b.max[0] > p[0] - PH.halfW && b.min[0] < p[0] + PH.halfW && b.max[2] > p[2] - PH.halfW && b.min[2] < p[2] + PH.halfW);
  const side = T.W / 2 + 0.9, back = T.L / 2 + 0.9;
  for (const [dx, dz] of [[left[0] * side, left[2] * side], [-left[0] * side, -left[2] * side], [-f[0] * back, -f[2] * back], [f[0] * back, f[2] * back]]) {
    const p = [car.x + dx, car.y + 0.1, car.z + dz];
    if (free(p)) return p;
  }
  return [car.x, car.y + T.H + 0.2, car.z]; // boxed in: out of the sunroof
}
// ------------------------------------------------------------ the physics step (main.js calls this instead of stepPlayer)
// slippery: banana peels on the floor (marbles too, once solo has them) under the car
function slipAt(x, z) { for (const pl of G.peels.values()) if (Math.hypot(pl.position.x - x, pl.position.z - z) < 1.6) return 0.12; return 1; }
export function driveStep(dt, inp, now) {
  const car = DV.car;
  if (!car) return false;
  const ev = stepCar(car, { f: inp.f, b: inp.b, l: inp.l, r: inp.r, hand: inp.jump, boost: inp.sprint }, dt, world, { slip: slipAt });
  for (const e of ev) {
    if (e.eject) { hud.msg('THROUGH THE WINDSCREEN', 1.8, 'brag'); G.shake = 1.4; synth.noise(0.6, 1, 'lowpass', 1500, 80); synth.tone('square', 220, 40, 0.4, 0.3); endDrive(true, true); return true; }
    if (e.crash) { hud.msg(e.v > 20 ? 'CRUNCH' : 'BONK', 0.8, 'brag'); G.shake = Math.max(G.shake || 0, Math.min(1.2, e.v / 20)); synth.noise(0.3, 0.8, 'lowpass', 1200, 120); }
    if (e.overheat) { hud.msg('ENGINE OVERHEATED', 1.2, 'brag'); synth.noise(0.8, 0.4, 'highpass', 3000, 6000); }
    if (e.land && e.v > 6) { G.shake = Math.max(G.shake || 0, 0.5); synth.tone('square', 90, 50, 0.2, 0.2); }
  }
  // you ride along: your feet go where the seat is (the eye at the seat), your speed is the car's
  const s = seatOf(car);
  ME.pos = [s[0], s[1] - PH.eye, s[2]]; ME.vel = [car.vx, car.vy, car.vz]; ME.onGround = car.ground;
  if (car.hp <= 0) { hud.msg('THE CAR GAVE UP', 1.4, 'brag'); endDrive(true); }
  if (car.y < -200) endDrive(true); // fell out of the world: the sim tows it
  return true;
}

// ------------------------------------------------------------ every frame: poses, the chase cam, sending, the HUD
const tmpV = new THREE.Vector3();
export function driveTick(dt, cam) {
  const car = DV.car, now = performance.now();
  for (const x of DV.meshes.values()) {
    if (x.c.id === DV.id && car) {
      const sp = speedOf(car), f = fwdOf(car), vf = car.vx * f[0] + car.vz * f[2];
      pose(x, [car.x, car.y, car.z], car.h, -car.steer * Math.min(1, sp / 25) * 0.06, car.ground ? -Math.max(-1, Math.min(1, (vf - (x.lastV || vf)) / dt / 40)) * 0.05 : 0.08);
      x.lastV = vf;
      for (const w of x.v.wheels) { w.spin.rotation.x += (vf / (w.r || 0.35)) * dt; if (w.steer) w.pivot.rotation.y = -car.steer * 0.45; }
    }
  }
  if (!car) return;
  // chase cam: behind and above, aimed where you look (the mouse orbits it); never through a wall
  if (cam) {
    const T = carType(car.ty), back = 4.5 + T.L * 0.55, up = 1.6 + T.H * 0.4;
    const look = [-Math.sin(ME.yaw) * Math.cos(ME.pitch), Math.sin(ME.pitch), -Math.cos(ME.yaw) * Math.cos(ME.pitch)];
    const c0 = [car.x, car.y + T.H + 0.4, car.z], want = [c0[0] - look[0] * back, c0[1] - look[1] * back + up * 0.5, c0[2] - look[2] * back];
    const d = [want[0] - c0[0], want[1] - c0[1], want[2] - c0[2]], L = Math.hypot(...d);
    const hit = L > 0.1 ? raycast(c0, d.map((x) => x / L), L, BOXES) : null, k = hit ? Math.max(0.15, (hit.t - 0.4) / L) : 1;
    cam.position.set(c0[0] + d[0] * k, c0[1] + d[1] * k, c0[2] + d[2] * k);
    cam.lookAt(tmpV.set(c0[0] + look[0] * 6, c0[1] + look[1] * 6, c0[2] + look[2] * 6));
  }
  if (now - DV.sendT > 100) { DV.sendT = now; story.send('car', { id: DV.id, p: [car.x, car.y, car.z].map((v) => Math.round(v * 100) / 100), h: Math.round(car.h * 1000) / 1000, v: [car.vx, car.vy, car.vz].map((v) => Math.round(v * 10) / 10), hp: Math.round(car.hp) }); }
  if (!DV.heatEl) { DV.heatEl = el('div', 'st-heat'); DV.heatEl.id = 'storyHeat'; document.body.append(DV.heatEl); }
  DV.heatEl.classList.remove('hidden');
  DV.heatEl.innerHTML = '';
  const bar = el('div', 'st-hbar'), fill = el('i'); fill.style.width = `${Math.round(car.heat * 100)}%`; fill.style.background = car.hot > 0 ? '#ff3030' : '#ffe14d';
  bar.append(fill, el('b', null, car.hot > 0 ? 'OVERHEATED' : `BOOST HEAT ${Math.round(car.heat * 100)}`));
  DV.heatEl.append(bar, el('span', 'st-coupons', `${Math.round(speedOf(car) * 3.6)} KM/H`));
}
// drive-bys: only a sidearm fires from the driver's seat
export function blockFire() { return driving() && !(W.cur && WEAPONS[W.cur] && WEAPONS[W.cur].slot === 'secondary'); }
export const DRIVE_CSS = `
.st-heat{position:fixed;left:50%;bottom:78px;transform:translateX(-50%);z-index:15;display:flex;gap:10px;align-items:center;font-family:var(--font);pointer-events:none}
.st-heat.hidden{display:none}
`;
export { STORY_CARS };
