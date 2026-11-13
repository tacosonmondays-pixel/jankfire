// VENDING MACHINE, the client (battle island support; kit: docs/mechs/ROSTER.md, numbers: MECH.vending in
// /shared/mech.js, the server judges it all: server/mech_vending.js). public/js/mech.js hands this kit your keys, your
// movement, the HUD row and the server's 'vm*' events. A waddling 5 m snack machine: hold LMB for the coin turret,
// Shift dispenses a Jank Cola (lobbed where you point, for your squad), E slams the OUT OF ORDER sign down as a wall,
// Q RESTOCKs everyone close. It jams sometimes: an ally walks up and kicks it (F). The colas and the walls out in the
// world (everyone's) live here too.
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { raycast, movePlayer } from '/shared/physics.js';
import { QUIZ } from '/shared/weapons.js';
import { MECH, MF, vmCharges } from '/shared/mech.js';
import { G } from './ctx.js';
import { ME, eye } from './player.js';
import { punchCam, isFriend } from './weapons.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { fx } from './fx.js';
import { K } from './keys.js';
import { rfx, rmesh } from './rigmodel.js';
import { mechsfx } from './mechsfx.js';
import { synth } from './audio.js';
import { MS, mechKitApi as A } from './mech.js';

const VM = MECH.vending;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const r2 = (x) => Math.round(x * 100) / 100;
const nowMs = () => performance.now();
const T = (...a) => synth.tone(...a), N = (...a) => synth.noise(...a);
const CAN_COLS = [0xff3030, 0x4fd8ff, 0x39ff14, 0xffe14d, 0xff4fd8, 0xff8a2a];
// its sounds: a coin's ching, the can's ka-chunk down the chute, the fizz, the sign's CLANG, the jam buzzer, the jingle
const sfx = {
  coin(pos, k = 1) { T('square', 2100 + Math.random() * 300, 2600, 0.05, 0.07 * k, pos); T('triangle', 3200, 3000, 0.08, 0.05 * k, pos, 0.02); T('sine', 180, 70, 0.07, 0.18 * k, pos); N(0.04, 0.2 * k, 'bandpass', 2600, 1800, pos); },
  ting(pos) { T('triangle', 4200, 3900, 0.12, 0.05, pos); },
  chunk(pos) { T('sine', 140, 50, 0.18, 0.5, pos); N(0.12, 0.5, 'lowpass', 1400, 200, pos); for (let i = 0; i < 4; i++) T('square', 600 + Math.random() * 500, 300, 0.04, 0.05, pos, 0.08 + i * 0.05); T('sine', 90, 40, 0.15, 0.4, pos, 0.3); }, // rattling down the chute, thunk into the flap
  fizz(pos) { N(0.5, 0.35, 'highpass', 6000, 2500, pos, 0, 0.7); T('sine', 300, 520, 0.08, 0.12, pos, 0.1); T('sine', 300, 520, 0.08, 0.12, pos, 0.28); }, // pssht, gulp gulp
  slam(pos) { mechsfx.clang(pos, 1.2); T('sine', 70, 25, 0.5, 0.8, pos); N(0.4, 0.7, 'lowpass', 900, 60, pos); },
  whit(pos, k) { mechsfx.clang(pos, clamp(0.3 + k * 0.03, 0.3, 0.9)); },
  crack(pos) { N(0.5, 0.8, 'highpass', 2000, 600, pos); mechsfx.ram(pos, true); T('square', 400, 60, 0.4, 0.15, pos); for (let i = 0; i < 6; i++) T('triangle', 900 + Math.random() * 1600, 500, 0.12, 0.06, pos, 0.05 + i * 0.07); },
  jam(pos) { for (let i = 0; i < 3; i++) T('square', 130, 120, 0.16, 0.18, pos, i * 0.2); for (let i = 0; i < 10; i++) T('square', 300 + Math.random() * 900, 200, 0.03, 0.05, pos, i * 0.05); }, // the error buzzer + a rattle
  rattle(pos) { for (let i = 0; i < 3; i++) T('square', 260 + Math.random() * 700, 180, 0.03, 0.04, pos, i * 0.04); },
  kick(pos) { T('sine', 160, 45, 0.25, 0.8, pos); mechsfx.ram(pos); T('square', 1320, 1320, 0.07, 0.1, pos, 0.18); T('square', 1760, 1760, 0.1, 0.1, pos, 0.26); }, // BONK, ding-ding
  stuck(pos) { this.chunk(pos); setTimeout(() => this.chunk(pos), 160); T('square', 1568, 1568, 0.08, 0.1, pos, 0.4); T('square', 2093, 2093, 0.14, 0.1, pos, 0.5); },
  stock(pos) { const n = [523, 659, 784, 1047, 1319]; n.forEach((f, i) => T('square', f, f, 0.12, 0.12, pos, i * 0.08)); T('sawtooth', 110, 220, 1.1, 0.15, pos); N(0.8, 0.3, 'bandpass', 900, 3000, pos, 0.1, 1.5); },
  ready() { T('square', 784, 784, 0.1, 0.1, null); T('square', 1047, 1047, 0.1, 0.1, null, 0.1); T('square', 1319, 1319, 0.16, 0.1, null, 0.2); },
};

// ------------------------------------------------------------ you, in it
const WS = { lmb: false, coinNext: 0, coinT: -1e9, dispT: -1e9, wallT: -1e9, stockT: -1e9, kickT: -1e9, jamUntil: 0, ch: { n: VM.cola.charges, t: 0 }, jumpWas: false, stepPh: 0, ultWas: 0, rattleT: 0 };
function clearState() { Object.assign(WS, { lmb: false, coinT: -1e9, dispT: -1e9, wallT: -1e9, stockT: -1e9, kickT: -1e9, jamUntil: 0, ch: { n: VM.cola.charges, t: nowMs() } }); }
const fwdOf = (yaw) => [-Math.sin(yaw), -Math.cos(yaw)];
const S = () => MECH.scale || 1; // (the size-1 machine's spots x the shared mech size: read live, the welcome can change it)
const slotAt = () => { const f = fwdOf(ME.yaw), k = S(); return [ME.pos[0] + f[0] * 0.9 * k, ME.pos[1] + 4.0 * k, ME.pos[2] + f[1] * 0.9 * k]; }; // (the server's coin slot)
const flapAt = () => { const f = fwdOf(ME.yaw), k = S(); return [ME.pos[0] + f[0] * 1.2 * k, ME.pos[1] + 1.5 * k, ME.pos[2] + f[1] * 1.2 * k]; };
const no = (t) => { hud.msg(t, 0.8); mechsfx.denied(); };
const cdLeft = (k, now) => Math.max(0, (MS.cd[k] || 0) - now);

function key(e, down, now) {
  if (!down) { if (K.matches('fire', e) || K.up('fire', e)) WS.lmb = false; return undefined; }
  if (e.repeat) return undefined;
  if (K.matches('fire', e)) { WS.lmb = true; return true; }
  if (K.matches('sprint', e)) { dispense(now); return true; }
  if (K.matches('grapple', e)) { wall(now); return true; }
  if (K.matches('lastSlot', e)) { restock(now); return true; }
  return undefined;
}
const jammed = (now) => { if (now < WS.jamUntil) { no('JAMMED · GET AN ALLY TO KICK IT'); sfx.rattle(null); return true; } return false; };
// Shift: a can out of the flap, lobbed onto the floor you're pointing at (in reach), else just in front
function dispense(now) {
  if (jammed(now) || now - WS.dispT < VM.cola.gap * 1000) return;
  if (vmCharges(WS.ch, now) < 1) { no(`SOLD OUT · ${((WS.ch.t + VM.cola.every * 1000 - now) / 1000).toFixed(1)}s`); return; }
  WS.dispT = now; WS.ch.n--;
  const p = A.aimDir().p, fl = flapAt(), near = Math.hypot(p[0] - fl[0], p[2] - fl[2]) <= VM.cola.toss && Math.abs(p[1] - ME.pos[1]) < 4;
  net.send({ t: 'mech', k: 'disp', ...(near ? { p: p.map(r2) } : null) });
  sfx.chunk(null); G.shake = Math.max(G.shake, 0.15);
}
// E: OUT OF ORDER
function wall(now) {
  if (jammed(now)) return;
  if (cdLeft('wall', now)) { no(`OUT OF ORDER ${(cdLeft('wall', now) / 1000).toFixed(1)}s`); return; }
  if (myWall()) { no('ONE WALL AT A TIME'); return; }
  MS.cd.wall = now + VM.wall.cd * 1000; WS.wallT = now;
  net.send({ t: 'mech', k: 'wall' });
  mechsfx.servo(null, 1.2);
}
// Q: RESTOCK
function restock(now) {
  if ((MS.ult || 0) < 100) { no(`RESTOCK ${Math.floor(MS.ult || 0)}%`); return; }
  if (jammed(now)) return;
  net.send({ t: 'mech', k: 'stock' });
}
const myWall = () => { for (const w of WALLS.values()) if (w.o === G.myId && !w.dying) return w; return null; };

// ------------------------------------------------------------ movement: a waddling walker (night shift's step)
function step(dt, inp, now) {
  const F = VM, v = ME.vel, p = ME.pos;
  ME.hook = null; ME.sliding = false; ME.crouching = false; ME.sprinting = false; ME.dashing = false;
  const fw = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), st = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
  const s = Math.sin(ME.yaw), c = Math.cos(ME.yaw);
  let wx = -s * fw + c * st, wz = -c * fw - s * st;
  const wl = Math.hypot(wx, wz);
  if (wl) { wx /= wl; wz /= wl; }
  let top = F.speed * (now < (ME.fastUntil || 0) ? QUIZ.fast : 1); // (a cola's sugar rush: the server allows the same)
  if (now < WS.jamUntil) top *= 0.55; // jammed: it rattles along
  if (now - WS.stockT < VM.restock.hold * 1000) top *= 0.3; // arms up for the RESTOCK
  const jumpNew = inp.jump && !WS.jumpWas; WS.jumpWas = !!inp.jump;
  const hs = Math.hypot(v[0], v[2]);
  if (ME.onGround) {
    if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * F.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= ns; v[2] *= ns; }
    if (wl) push(v, wx, wz, top, F.accel, dt);
    if (jumpNew) { v[1] = F.hop; ME.onGround = false; p[1] += 0.03; MS.boostT = 0; mechsfx.boost(null, 0.4); rfx.dust(p, 10, 1.2, 4); sfx.rattle(null); } // a hop on its heel jets
  } else if (wl) push(v, wx, wz, Math.min(top, F.airCap), F.accel * 0.6, dt);
  v[1] -= F.grav * dt * 0.5;
  const was = ME.onGround;
  if (!was && v[1] < (MS.minVy || 0)) MS.minVy = v[1];
  const res = movePlayer(p, v, dt, BOXES, was);
  if (!res.ground) v[1] -= F.grav * dt * 0.5;
  ME.onGround = !!res.ground && v[1] <= 0.01;
  if (ME.onGround && !was) land();
  if (ME.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; ME.onGround = false; }
  // footsteps: short stubby ones, the cans inside rattle with every one
  const hs2 = Math.hypot(v[0], v[2]);
  if (ME.onGround && hs2 > 1.2) {
    const w0 = Math.floor(WS.stepPh);
    WS.stepPh += dt * (1.1 + hs2 * 0.2);
    if (Math.floor(WS.stepPh) !== w0) { const k = clamp(hs2 / F.speed, 0, 1.2); G.shake = Math.max(G.shake, 0.1 + k * 0.08); punchCam(-0.004 - k * 0.005); mechsfx.step(null, 0.45 + k * 0.3, false); if (Math.random() < 0.6) sfx.rattle(null); rfx.dust(ME.pos, 3 + Math.round(k * 3), 0.7, 2 + k); }
  }
  ME.eyeH += (F.eye - ME.eyeH) * Math.min(1, dt * 8);
  return true;
}
function push(v, wx, wz, top, accel, dt) { const cur = v[0] * wx + v[2] * wz, add = top - cur; if (add > 0) { const a = Math.min(add, accel * top * dt); v[0] += a * wx; v[2] += a * wz; } }
function land() {
  const impact = -(MS.minVy || 0); MS.minVy = 0;
  const k = clamp((impact - 6) / 26, 0, 1);
  MS.landT = 0; MS.landK = k;
  if (impact > 7) { A.dustRing(ME.pos, 2.2 + k * 3, k); mechsfx.step(null, 1.1, true); sfx.rattle(null); G.shake = Math.max(G.shake, 0.3 + k * 0.4); punchCam(-0.03 - k * 0.03); }
}

// ------------------------------------------------------------ every frame, in it
function update(dt, now, inst) {
  // the coin turret: held fire, 10 a second, from the coin slot to whatever the crosshair's on. your tracer right away
  if (WS.lmb && now >= WS.coinNext) {
    WS.coinNext = now + 1000 / VM.coin.rate; WS.coinT = now;
    const o = slotAt(), aimP = A.aimDir().p, v = [aimP[0] - o[0], aimP[1] - o[1], aimP[2] - o[2]], l = Math.hypot(v[0], v[1], v[2]) || 1, d = v.map((x) => x / l);
    net.send({ t: 'mech', k: 'coin', d: d.map((x) => Math.round(x * 1000) / 1000) });
    const h = raycast(o, d, VM.coin.range, BOXES), end = h && h.t < l ? h.point : l < VM.coin.range ? aimP : [o[0] + d[0] * VM.coin.range, o[1] + d[1] * VM.coin.range, o[2] + d[2] * VM.coin.range];
    coinFx(inst, end, null, true);
    punchCam(-0.005, (Math.random() - 0.5) * 0.004); G.shake = Math.max(G.shake, 0.07);
  }
  if (now < WS.jamUntil) { // jammed: the whole cabinet rattles, the screen too
    G.shake = Math.max(G.shake, 0.12);
    if (now > WS.rattleT) { WS.rattleT = now + 260 + Math.random() * 200; sfx.rattle(null); }
  }
  const u = Math.floor(MS.ult || 0);
  if (u >= 100 && WS.ultWas < 100) { hud.msg(`RESTOCK READY · ${K.label('lastSlot')}`, 1.6, 'brag'); sfx.ready(); }
  WS.ultWas = u;
  canHud(now);
}
// a coin: a gold tracer from the coin slot, a glint at the far end, a spinning coin popping out the side
function coinFx(inst, end, from, mine) {
  const mz = inst && inst.att.mk_muzzle;
  const o = from || (mz ? mz.getWorldPosition(new THREE.Vector3()).toArray() : slotAt());
  fx.tracer(o, end, 0xffd23a, mine ? 0.12 : 0.09, 0.18);
  rfx.sparks(end, 5, 5, [0xffffff, 0xffe14d, 0xffb000], 0.25, 0.09);
  rfx.sparks(o, 4, 3, [0xfff2a0, 0xffd23a], 0.12, 0.1);
  if (Math.random() < 0.5) rfx.sparks(o, 1, 4, [0xffd23a], 0.6, 0.16, [Math.random() - 0.5, 1, Math.random() - 0.5]); // a coin flicks out
  sfx.coin(mine ? null : o, mine ? 0.8 : 0.6);
}
// the cans left (three little cans over the mech panel) + JAMMED
let canEl = null;
function canHud(now) {
  if (!canEl) {
    canEl = document.createElement('div');
    canEl.style.cssText = 'position:absolute;left:18px;bottom:212px;padding:4px 10px;font-family:var(--font);font-weight:bold;font-size:14px;color:#fff;background:rgba(18,8,24,.92);border:3px solid #ff4fd8;box-shadow:5px 5px 0 #4fd8ff;transform:rotate(-1.5deg);pointer-events:none;display:flex;gap:6px;align-items:center';
    const h = document.getElementById('hud'); if (h) h.append(canEl);
  }
  canEl.style.display = MS.on ? 'flex' : 'none';
  if (!MS.on) return;
  const n = vmCharges(WS.ch, now), left = n < VM.cola.charges ? Math.max(0, (WS.ch.t + VM.cola.every * 1000 - now) / 1000) : 0, jam = now < WS.jamUntil;
  const key = `${n}|${Math.ceil(left * 2)}|${jam ? Math.ceil((WS.jamUntil - now) / 250) : 0}`;
  if (canEl.dataset.key === key) return;
  canEl.dataset.key = key;
  const cans = Array.from({ length: VM.cola.charges }, (_, i) => `<i style="display:inline-block;width:11px;height:19px;border:2px solid #000;border-radius:2px;background:${i < n ? '#ff3030' : '#3a2a40'};box-shadow:inset 0 4px 0 ${i < n ? '#fff' : '#3a2a40'}"></i>`).join('');
  canEl.innerHTML = jam ? `<span style="color:#ff3030;font-size:17px">JAMMED! GET KICKED</span>` : `<span style="color:#ffe14d">COLA</span>${cans}<span style="color:#4fd8ff;width:34px">${left ? left.toFixed(1) + 's' : ''}</span>`;
  canEl.style.borderColor = jam ? (Math.floor(now / 250) % 2 ? '#ff3030' : '#ffe14d') : '#ff4fd8';
}
function flags(now) { return (now < WS.jamUntil ? MF.VJAM : 0) | (now - WS.stockT < VM.restock.hold * 1000 ? MF.VSTOCK : 0) | (now - WS.coinT < 250 ? MF.VCOIN : 0); }
function pose(now) {
  return { coinT: (now - WS.coinT) / 1000, coining: WS.lmb, dispT: (now - WS.dispT) / 1000, wallT: (now - WS.wallT) / 1000, stockT: (now - WS.stockT) / 1000,
    kickT: (now - WS.kickT) / 1000, jam: now < WS.jamUntil ? 1 : 0, signOut: !!myWall(), boost: MS.boostT < 0.3 ? 1 - MS.boostT / 0.3 : 0 };
}

// ------------------------------------------------------------ everyone else's (and the replay's ghosts)
const vst = (st) => st.vm || (st.vm = { coinT: -1e9, dispT: -1e9, wallT: -1e9, stockT: -1e9, kickT: -1e9 });
function remote(r, st, dt, now) {
  const V = vst(st), fl = r.f;
  if (fl & MF.VCOIN) V.coinT = Math.max(V.coinT, now - 120); // (the turret's going: keep the loop on)
  if ((fl & MF.VJAM) && Math.random() < dt * 4 && !r.ghost) sfx.rattle(r.pos);
  return { coinT: (now - V.coinT) / 1000, coining: !!(fl & MF.VCOIN), dispT: (now - V.dispT) / 1000, wallT: (now - V.wallT) / 1000, stockT: !!(fl & MF.VSTOCK) ? Math.min(0.5, (now - V.stockT) / 1000) : (now - V.stockT) / 1000,
    kickT: (now - V.kickT) / 1000, jam: fl & MF.VJAM ? 1 : 0, signOut: (() => { for (const w of WALLS.values()) if (w.o === r.id && !w.dying) return true; return false; })() };
}

// ------------------------------------------------------------ the world: colas and walls (everyone's)
const COLAS = new Map(), WALLS = new Map();
const mats = {};
function canTex() {
  if (mats.canTex) return mats.canTex;
  const c = document.createElement('canvas'); c.width = 128; c.height = 64;
  const g = c.getContext('2d');
  g.fillStyle = '#e8141c'; g.fillRect(0, 0, 128, 64);
  g.fillStyle = '#fff'; g.fillRect(0, 22, 128, 20);
  g.fillStyle = '#e8141c'; g.font = 'bold 18px sans-serif'; g.textAlign = 'center'; g.fillText('JANK', 64, 39);
  g.fillStyle = '#ffe14d'; for (let x = 0; x < 128; x += 16) g.fillRect(x, 6, 8, 4);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping;
  return (mats.canTex = t);
}
function colaMesh() {
  const g = new THREE.Group();
  if (!mats.can) {
    mats.can = new THREE.MeshPhongMaterial({ map: canTex(), specular: 0xffffff, shininess: 90, emissive: 0x401010 });
    mats.lid = new THREE.MeshPhongMaterial({ color: 0xd8dee6, specular: 0xffffff, shininess: 120 });
    mats.halo = new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    mats.beam = new THREE.MeshBasicMaterial({ color: 0xff6a6a, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    mats.ring = new THREE.MeshBasicMaterial({ color: 0xffe14d, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    mats.geo = { body: new THREE.CylinderGeometry(0.2, 0.2, 0.62, 14), lid: new THREE.CylinderGeometry(0.17, 0.2, 0.06, 14), tab: new THREE.TorusGeometry(0.05, 0.015, 4, 8),
      halo: new THREE.SphereGeometry(0.55, 12, 8), beam: new THREE.CylinderGeometry(0.12, 0.25, 6, 8, 1, true).translate(0, 3, 0), ring: new THREE.RingGeometry(0.55, 0.75, 24).rotateX(-Math.PI / 2) };
  }
  const G2 = mats.geo, can = new THREE.Group();
  can.add(new THREE.Mesh(G2.body, mats.can));
  const lid = new THREE.Mesh(G2.lid, mats.lid); lid.position.y = 0.34; can.add(lid);
  const bot = new THREE.Mesh(G2.lid, mats.lid); bot.position.y = -0.34; bot.rotation.x = Math.PI; can.add(bot);
  const tab = new THREE.Mesh(G2.tab, mats.lid); tab.position.set(0.05, 0.38, 0); tab.rotation.x = Math.PI / 2; can.add(tab);
  can.rotation.z = 0.25;
  const halo = new THREE.Mesh(G2.halo, mats.halo), beam = new THREE.Mesh(G2.beam, mats.beam), ring = new THREE.Mesh(G2.ring, mats.ring);
  ring.position.y = -0.62;
  g.add(can, halo, beam, ring);
  g.userData = { can, halo, ring };
  return g;
}
function colaAdd(id, o, p, ms, from) {
  if (COLAS.has(id)) return COLAS.get(id);
  const m = colaMesh();
  G.scene.add(m);
  const c = { id, o, p, until: nowMs() + ms, mesh: m, t0: nowMs(), from: from || null, ph: Math.random() * 6 };
  COLAS.set(id, c);
  return c;
}
function colaDrop(id, burst) {
  const c = COLAS.get(id);
  if (!c) return;
  if (burst) { rfx.sparks([c.p[0], c.p[1] + 0.8, c.p[2]], 18, 5, [0xffffff, 0xff3030, 0xffe14d], 0.4, 0.1, [0, 1, 0]); rmesh.ring([c.p[0], c.p[1], c.p[2]], 1.2, 0xff3030, 0.3); }
  c.mesh.removeFromParent(); COLAS.delete(id);
}
// the OUT OF ORDER sign: a canvas panel (big letters, hazard edges), its cracks drawn on as it takes damage
function signTex(x2) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 288;
  const g = c.getContext('2d');
  g.fillStyle = '#fff6d8'; g.fillRect(0, 0, 512, 288);
  for (let x = -40; x < 560; x += 40) { g.fillStyle = '#16161a'; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 20, 0); g.lineTo(x + 40, 26); g.lineTo(x + 20, 26); g.fill(); g.beginPath(); g.moveTo(x, 262); g.lineTo(x + 20, 262); g.lineTo(x + 40, 288); g.lineTo(x + 20, 288); g.fill(); }
  g.fillStyle = '#ffd23a'; for (let x = -40; x < 560; x += 40) { g.beginPath(); g.moveTo(x + 20, 0); g.lineTo(x + 40, 0); g.lineTo(x + 60, 26); g.lineTo(x + 40, 26); g.fill(); g.beginPath(); g.moveTo(x + 20, 262); g.lineTo(x + 40, 262); g.lineTo(x + 60, 288); g.lineTo(x + 40, 288); g.fill(); }
  g.save(); g.translate(256, 150); g.rotate(-0.04);
  g.font = 'bold 92px "Comic Neue", "Comic Sans MS", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 12; g.strokeStyle = '#000'; g.strokeText('OUT OF', 0, -48); g.strokeText('ORDER', 0, 42);
  g.fillStyle = '#ff3030'; g.fillText('OUT OF', 0, -48); g.fillStyle = '#ff00dc'; g.fillText('ORDER', 0, 42);
  g.restore();
  g.font = 'bold 22px "Comic Neue", sans-serif'; g.fillStyle = '#16161a'; g.textAlign = 'center'; g.fillText('sorry for the inconvenience :(', 256, 248);
  if (x2) { g.save(); g.translate(440, 66); g.rotate(0.3); g.fillStyle = '#39ff14'; g.fillRect(-56, -24, 112, 48); g.strokeStyle = '#000'; g.lineWidth = 5; g.strokeRect(-56, -24, 112, 48); g.fillStyle = '#000'; g.font = 'bold 30px "Comic Neue", sans-serif'; g.fillText('x2 !!', 0, 10); g.restore(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return { t, c, g };
}
function crackOn(w, k) { // k: 0..1 of the wall gone. a few jagged lines from where it got hit
  const { g, c } = w.tex;
  g.strokeStyle = 'rgba(20,10,10,0.9)'; g.lineWidth = 3 + k * 3;
  for (let n = 0; n < 2; n++) {
    let x = 60 + Math.random() * 392, y = 40 + Math.random() * 200;
    g.beginPath(); g.moveTo(x, y);
    for (let i = 0; i < 6; i++) { x += (Math.random() - 0.5) * 70; y += (Math.random() - 0.5) * 70; g.lineTo(x, y); }
    g.stroke();
  }
  w.tex.t.needsUpdate = true;
  void c;
}
function wallMesh(w) {
  const half = (x) => (Number.isFinite(x) && x > 0 && x <= VM.wall.w / 2 + 0.01 ? x : VM.wall.w / 2); // (the server clips each half where a building is)
  w.wl = half(w.wl); w.wr = half(w.wr);
  const g = new THREE.Group(), Wd = w.wl + w.wr, cx = (w.wr - w.wl) / 2, H = VM.wall.h;
  w.tex = signTex(w.x2);
  const face = new THREE.MeshLambertMaterial({ map: w.tex.t, emissive: 0x302810, side: THREE.DoubleSide });
  const dark = new THREE.MeshLambertMaterial({ color: 0x22202a, flatShading: true });
  const post = new THREE.MeshPhongMaterial({ color: 0xffd23a, specular: 0xffffff, shininess: 60, flatShading: true, emissive: 0x2a2000 });
  const lamp = new THREE.MeshBasicMaterial({ color: 0xff3030 });
  w.mats = [face, dark, post, lamp];
  const panel = new THREE.Mesh(new THREE.BoxGeometry(Wd, H - 0.5, 0.18), [dark, dark, dark, dark, face, face]);
  panel.position.set(cx, 0.5 + (H - 0.5) / 2, 0);
  g.add(panel);
  for (const sx of [-1, 1]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.32, H + 0.2, 0.32), post); p.position.set(cx + sx * (Wd / 2 + 0.05), (H + 0.2) / 2, 0); g.add(p);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.2, 1.4), dark); foot.position.set(cx + sx * (Wd / 2 + 0.05), 0.1, 0); g.add(foot);
    const l = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 6), lamp); l.position.set(cx + sx * (Wd / 2 + 0.05), H + 0.35, 0); g.add(l); (w.lamps ||= []).push(l);
  }
  const bar = new THREE.Mesh(new THREE.BoxGeometry(Wd + 0.4, 0.22, 0.26), post); bar.position.set(cx, H + 0.05, 0); g.add(bar);
  g.position.set(w.p[0], w.p[1], w.p[2]); g.rotation.y = w.yaw;
  w.panel = panel;
  return g;
}
function wallAdd(m, live) {
  if (WALLS.has(m.w)) return WALLS.get(m.w);
  const w = { id: m.w, o: m.id, p: m.p, yaw: Number(m.yaw) || 0, wl: m.wl, wr: m.wr, hp: m.hp, max: m.max || VM.wall.hp, x2: !!m.x2, t0: nowMs(), until: nowMs() + (m.ms || 10000), cracks: 0, flick: 0 };
  w.g = wallMesh(w);
  G.scene.add(w.g);
  WALLS.set(w.id, w);
  if (live) {
    const at = [w.p[0], w.p[1], w.p[2]];
    setTimeout(() => { if (!WALLS.has(w.id)) return; sfx.slam(at); A.dustRing(at, 4.5, 0.9); rfx.debris(at, 18, 7); rfx.sparks([at[0], at[1] + 0.3, at[2]], 24, 8, [0xffffff, 0xffe14d], 0.4, 0.12); A.shakeNear(at, 0.9, 30); }, 180);
  }
  return w;
}
function wallDrop(id, why) {
  const w = WALLS.get(id);
  if (!w) return;
  WALLS.delete(id);
  if (why === 'break') { // a nice break: the panel splits into chunks that fly, sparks, a crunch
    const at = [w.p[0], w.p[1] + 2.2, w.p[2]];
    sfx.crack(at); rfx.sparks(at, 60, 12, [0xffffff, 0xffe14d, 0xff3030, 0xff00dc], 0.7, 0.16); rfx.debris(at, 40, 11); rmesh.flash(at, 4, 0xfff0c0, 0.2); A.shakeNear(at, 0.8, 30);
    w.g.updateMatrixWorld(true);
    const fx0 = -Math.sin(w.yaw), fz0 = -Math.cos(w.yaw), rx = Math.cos(w.yaw), rz = -Math.sin(w.yaw);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) { // 8 chunks of the sign, each with its share of the canvas
      const Wd = w.wl + w.wr, geo = new THREE.BoxGeometry(Wd / 4, (VM.wall.h - 0.5) / 2, 0.18), uv = geo.attributes.uv;
      for (let k = 0; k < uv.count; k++) uv.setXY(k, (i + uv.getX(k)) / 4, (j + uv.getY(k)) / 2);
      const m = new THREE.Mesh(geo, w.mats[0].clone()), lx = (w.wr - w.wl) / 2 + (i - 1.5) * Wd / 4, ly = 0.5 + (j + 0.5) * (VM.wall.h - 0.5) / 2;
      m.position.set(w.p[0] + rx * lx, w.p[1] + ly, w.p[2] + rz * lx); m.rotation.y = w.yaw;
      G.scene.add(m);
      const out = (Math.random() - 0.5) * 2, k2 = 4 + Math.random() * 6;
      G.gibs.push({ m, own: true, floorY: w.p[1] + 0.1, life: 3 + Math.random() * 1.5, v: [fx0 * k2 * out + rx * lx * 1.5, 4 + Math.random() * 7, fz0 * k2 * out + rz * lx * 1.5], av: [(Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10] });
    }
    w.g.removeFromParent(); w.mats.slice(1).forEach((m) => m.dispose()); w.tex.t.dispose();
    return;
  }
  w.dying = { t0: nowMs() }; // time's up (or gone): it folds down into the floor
  WALLS.set(id, w);
}
function wallFree(w) { w.g.removeFromParent(); w.g.traverse((o) => { if (o.isMesh) o.geometry.dispose(); }); for (const m of w.mats) m.dispose(); w.tex.t.dispose(); WALLS.delete(w.id); }
function world(dt, now, replaying) {
  for (const c of [...COLAS.values()]) {
    if (now > c.until + 500 || !G.joined) { colaDrop(c.id); continue; }
    const m = c.mesh, U = m.userData, k = clamp((now - c.t0) / 350, 0, 1);
    m.visible = !replaying;
    if (k < 1 && c.from) { // popping out of the flap in an arc
      const a = c.from, b = c.p;
      m.position.set(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] + 0.7 - a[1]) * k + Math.sin(k * Math.PI) * 1.4, a[2] + (b[2] - a[2]) * k);
      U.can.rotation.x += dt * 20;
    } else {
      m.position.set(c.p[0], c.p[1] + 0.7 + Math.sin(now * 0.004 + c.ph) * 0.12, c.p[2]);
      U.can.rotation.x = 0; U.can.rotation.y += dt * 2.2;
    }
    const left = (c.until - now) / 1000, blink = left < 4 ? (Math.floor(now / 120) % 2 ? 0.3 : 1) : 1; // going flat: it blinks
    U.halo.material.opacity = 0.25 + Math.sin(now * 0.008 + c.ph) * 0.1; U.halo.scale.setScalar(blink);
    U.ring.rotation.y = now * 0.002; U.can.visible = blink > 0.5 || left > 4;
    if (Math.random() < dt * 3 && !replaying) rfx.sparks([m.position.x + (Math.random() - 0.5) * 0.5, m.position.y + 0.3, m.position.z + (Math.random() - 0.5) * 0.5], 1, 1.5, [0xffffff, 0xffe14d], 0.5, 0.07, [0, 1, 0]); // a sparkle
  }
  for (const w of [...WALLS.values()]) {
    w.g.visible = !replaying;
    if (w.dying) { const k = (now - w.dying.t0) / 450; w.g.rotation.x = -Math.min(1, k) * 1.5; w.g.position.y = w.p[1] - Math.max(0, k - 0.6) * 3; if (k > 1.6) wallFree(w); continue; }
    const k = clamp((now - w.t0) / 180, 0, 1); // slammed down from the sky
    w.g.position.y = w.p[1] + (1 - k) * (1 - k) * 5;
    w.g.scale.set(1, k < 1 ? 1 : 1 + Math.max(0, 0.12 - (now - w.t0 - 180) / 1500), 1); // (a little squash on impact)
    const hp = w.hp / w.max, lowF = hp < 0.3 && Math.random() < 0.15; // low: the sign flickers
    w.mats[0].emissive.setHex(lowF ? 0x000000 : 0x302810);
    for (const l of w.lamps || []) l.visible = Math.floor(now / 300) % 2 === 0;
    const want = Math.floor((1 - hp) * 6);
    while (w.cracks < want) { w.cracks++; crackOn(w, 1 - hp); }
    if (now > w.until + 1500) wallDrop(w.id, 'time');
  }
  prompt(now);
}
// on foot near a jammed ally's machine: F KICKS IT
let pr = null;
function jammedNear() {
  if (MS.on || !ME.alive || !G.joined) return null;
  let best = null, bd = VM.jam.reach + VM.hw - 0.2;
  for (const r of G.remotes.values()) {
    if (!r.alive || !r.mechOn || r.mechF !== 'vending' || !(r.f & MF.VJAM) || !isFriend(r)) continue;
    const d = Math.hypot(r.pos[0] - ME.pos[0], r.pos[2] - ME.pos[2]);
    if (d < bd) { bd = d; best = r; }
  }
  return best;
}
function prompt(now) {
  const r = jammedNear();
  if (!pr && !r) return;
  if (!pr) { pr = document.createElement('div'); pr.style.cssText = 'display:none;position:absolute;left:50%;top:58%;transform:translateX(-50%) rotate(-2deg);padding:6px 14px;font-family:var(--font);font-weight:bold;font-size:22px;background:#ff3030;color:#fff;border:3px solid #000;box-shadow:5px 5px 0 #ffe14d;pointer-events:none'; const h = document.getElementById('hud'); if (h) h.append(pr); }
  pr.style.display = r ? 'block' : 'none';
  if (r) pr.textContent = `${K.label('use')} · KICK THE MACHINE`;
  pr.style.transform = `translateX(-50%) rotate(${Math.floor(now / 150) % 2 ? -3 : 2}deg)`;
}
function footKey(e, now) {
  const r = jammedNear();
  if (!r) return false;
  if (now - WS.kickT < 300) return true;
  WS.kickT = now;
  net.send({ t: 'mech', k: 'kick', to: r.id });
  punchCam(0.04); G.shake = Math.max(G.shake, 0.3);
  return true;
}

// ------------------------------------------------------------ the server's events
const EVENTS = new Set(['vmcoin', 'vmcola', 'vmcolax', 'vmdisp', 'vmdrink', 'vmwall', 'vmwhit', 'vmwallx', 'vmjam', 'vmkick', 'vmstuck', 'vmstock', 'vmlist']);
function event(m, getR, live, me, r, st) {
  const P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
  const V = st ? vst(st) : null, pos = A.posOf(m.id, getR), now = nowMs();
  switch (m.k) {
    case 'vmcoin': {
      const b = P(m.b);
      if (!b || me) break;
      if (V) V.coinT = now;
      coinFx(A.instOf(m.id, getR), b, A.instOf(m.id, getR) ? null : pos ? [pos[0], pos[1] + 4 * S(), pos[2]] : b, false);
      if (m.h === 2) sfx.whit(b, 2);
      break;
    }
    case 'vmdisp': if (V && !me) V.dispT = now; break;
    case 'vmcola': {
      const p = P(m.p), from = P(m.from);
      if (!p) break;
      if (live) colaAdd(m.c, m.id, p, Number(m.ms) || 20000, from);
      if (V && !me) V.dispT = now;
      if (from && !me) sfx.chunk(from);
      break;
    }
    case 'vmcolax': colaDrop(m.c, true); break;
    case 'vmdrink': {
      const c = COLAS.get(m.c);
      const at = c ? [c.p[0], c.p[1] + 0.8, c.p[2]] : A.posOf(m.to, getR);
      colaDrop(m.c, true);
      if (at) { sfx.fizz(at); rfx.sparks(at, 20, 4, [0xffffff, 0xff3030, 0x9fe8ff], 0.5, 0.1, [0, 1, 0]); }
      if (live && m.to === G.myId) {
        if (Number.isFinite(m.ms)) ME.fastUntil = Math.max(ME.fastUntil || 0, now + m.ms);
        hud.msg(`+${m.a | 0} ${m.ar ? 'ARMOUR' : 'HP'} · SUGAR RUSH`, 1.3, 'brag'); hud.flash && hud.flash(0.2, 0.15);
      } else if (live && m.id === G.myId && m.a > 0) hud.msg(`${(A.nameOf(m.to) || {}).name || 'ALLY'} +${m.a | 0}`, 0.8, 'brag');
      break;
    }
    case 'vmwall': {
      const p = P(m.p);
      if (!p) break;
      if (live) wallAdd({ ...m, p }, true);
      if (V && !me) V.wallT = now;
      if (me) { WS.wallT = Math.max(WS.wallT, now - 300); hud.msg(m.x2 ? 'OUT OF ORDER x2' : 'OUT OF ORDER', 1.1, 'brag'); }
      break;
    }
    case 'vmwhit': {
      const w = WALLS.get(m.w), p = P(m.p);
      if (w && Number.isFinite(m.hp)) w.hp = m.hp;
      if (p) { rfx.sparks(p, 6 + Math.min(20, (m.a | 0) / 3), 7, [0xffffff, 0xffe14d, 0xff8a2a], 0.3, 0.1); sfx.whit(p, m.a | 0); rmesh.flash(p, 0.8, 0xfff0b0, 0.08); }
      if (w && w.panel) { w.panel.position.z = 0.06; setTimeout(() => { if (w.panel) w.panel.position.z = 0; }, 60); } // (it jolts)
      break;
    }
    case 'vmwallx': {
      wallDrop(m.w, m.why);
      if (live && m.why === 'break' && m.id === G.myId) hud.msg('YOUR SIGN BROKE', 1, 'slip');
      if (live && m.why === 'break' && m.by === G.myId && m.id !== G.myId) hud.msg('OUT OF ORDER? NOT ANYMORE', 1.2, 'brag');
      break;
    }
    case 'vmjam': {
      if (V) V.jamT = now;
      if (pos) { sfx.jam(me ? null : pos); rfx.smoke([pos[0], pos[1] + 4.6 * S(), pos[2]], 10, 0x2c2c30, 0.7, 1.2, 1.4, 0.4); rfx.sparks([pos[0], pos[1] + 2, pos[2]], 14, 6, [0xffffff, 0xff3030], 0.3, 0.1); }
      if (me) { WS.jamUntil = now + (Number(m.ms) || 4000); WS.ch.n = Math.min(VM.cola.charges, WS.ch.n + (m.w === 'disp' ? 1 : 0)); if (m.w === 'wall') MS.cd.wall = 0; hud.msg('JAMMED! GET AN ALLY TO KICK IT', 1.8, 'slip'); G.shake = Math.max(G.shake, 0.6); }
      else if (live && r && isFriend(r) && pos && Math.hypot(pos[0] - ME.pos[0], pos[2] - ME.pos[2]) < 25 && !MS.on) hud.msg(`${(A.nameOf(m.id) || {}).name || 'THE MACHINE'} IS JAMMED · ${K.label('use')} TO KICK IT`, 1.6, 'slip');
      break;
    }
    case 'vmkick': {
      if (V) V.kickT = now;
      if (pos) { sfx.kick(me ? null : pos); rfx.sparks([pos[0], pos[1] + 1.5, pos[2]], 26, 9, [0xffffff, 0xffe14d, 0xff4fd8], 0.4, 0.12); rmesh.flash([pos[0], pos[1] + 1.5, pos[2]], 2, 0xffffff, 0.12); }
      if (me) { WS.jamUntil = 0; WS.kickT = now; hud.msg('UNSTUCK!', 1.2, 'brag'); G.shake = Math.max(G.shake, 0.7); punchCam(-0.05); }
      if (live && m.by === G.myId) { hud.msg('KICKED IT · UNSTUCK!', 1.2, 'brag'); G.shake = Math.max(G.shake, 0.4); }
      break;
    }
    case 'vmstuck': {
      if (pos) sfx.stuck(me ? null : pos);
      if (me) { hud.msg('STUCK! x2', 1.2, 'brag'); punchCam(0.03); }
      break;
    }
    case 'vmstock': { // RESTOCK: a ring out to 15 m, confetti in can colours, the marquee flashing, everyone it reached told
      const p = P(m.p), R = Number.isFinite(m.r) ? clamp(m.r, 1, 30) : VM.restock.r;
      if (V) V.stockT = now;
      if (me) WS.stockT = now;
      if (p) {
        sfx.stock(me ? null : p);
        rmesh.ring(p, R, 0x39ff14, 0.9); rmesh.ring(p, R * 0.66, 0xffe14d, 0.7); rmesh.ring(p, R * 0.33, 0xff4fd8, 0.5);
        rmesh.flash([p[0], p[1] + 3, p[2]], 5, 0xfff8c0, 0.3);
        rfx.sparks([p[0], p[1] + 5, p[2]], 80, 12, CAN_COLS, 1.2, 0.18, [0, 1, 0]);
        if (live && !me) A.shakeNear(p, 0.6, 30);
      }
      if (live && Array.isArray(m.l)) for (const e of m.l) {
        if (!Array.isArray(e)) continue;
        const at = A.posOf(e[0], getR);
        if (at && e[0] !== m.id) { fx.tracer && p && fx.tracer([p[0], p[1] + 4.6 * S(), p[2]], [at[0], at[1] + 1.2, at[2]], 0x39ff14, 0.1, 0.4); rfx.sparks([at[0], at[1] + 1.2, at[2]], 20, 5, [0x39ff14, 0xffffff], 0.5, 0.1, [0, 1, 0]); }
        if (e[0] === G.myId && !me) { hud.msg(`RESTOCKED +${e[1] | 0}`, 1.6, 'brag'); hud.flash && hud.flash(0.3, 0.2); }
      }
      if (me) { const n = Array.isArray(m.l) ? m.l.length - 1 : 0; hud.msg(n > 0 ? `RESTOCK! ${n} RESTOCKED` : 'RESTOCK!', 1.6, 'brag'); G.shake = Math.max(G.shake, 0.9); punchCam(-0.06); if (hud.impact) hud.impact(0.7); WS.ch = { n: VM.cola.charges, t: now }; }
      break;
    }
    case 'vmlist': { // the server's list: anything we missed comes in, anything it doesn't have goes
      if (!live) break;
      const cs = new Set(), ws = new Set();
      for (const e of Array.isArray(m.c) ? m.c : []) { if (!Array.isArray(e) || e.length < 6) continue; const p = P([e[2], e[3], e[4]]); if (!p) continue; cs.add(e[0]); if (!COLAS.has(e[0])) colaAdd(e[0], e[1], p, Number(e[5]) || 0, null); }
      for (const e of Array.isArray(m.w) ? m.w : []) { if (!Array.isArray(e) || e.length < 10) continue; const p = P([e[2], e[3], e[4]]); if (!p) continue; ws.add(e[0]); const w = WALLS.get(e[0]); if (!w) wallAdd({ w: e[0], id: e[1], p, yaw: e[5], hp: e[6], max: e[7], ms: e[8], x2: e[9], wl: e[10], wr: e[11] }, false); else if (!w.dying) w.hp = Number(e[6]) || w.hp; }
      for (const c of [...COLAS.values()]) if (!cs.has(c.id) && now - c.t0 > 1500) colaDrop(c.id);
      for (const w of [...WALLS.values()]) if (!ws.has(w.id) && !w.dying && now - w.t0 > 1500) wallDrop(w.id, 'gone');
      break;
    }
  }
}
function en(m, now) {
  if (Number.isFinite(m.ch)) WS.ch = { n: m.ch, t: Number.isFinite(m.chT) && m.chT > 0 ? now + m.chT - VM.cola.every * 1000 : now };
  if (Number.isFinite(m.jam)) WS.jamUntil = m.jam > 0 ? now + m.jam : Math.min(WS.jamUntil, now);
}
function resetWorld() { for (const id of [...COLAS.keys()]) colaDrop(id); for (const w of [...WALLS.values()]) wallFree(w); if (pr) pr.style.display = 'none'; }

export const VMK = {
  abil: [['fire', 'COINS', ''], ['sprint', 'DISPENSE', 'disp'], ['grapple', 'OUT OF ORDER', 'wall'], ['lastSlot', 'RESTOCK', 'ult']],
  cds: ['wall'],
  events: EVENTS,
  help: () => `hold ${K.label('fire')} coin turret · ${K.label('sprint')} dispense a Jank Cola where you point · ${K.label('grapple')} OUT OF ORDER wall · ${K.label('lastSlot')} RESTOCK · jammed? an ally kicks it (${K.label('use')})`,
  start() { clearState(); WS.ultWas = 0; },
  end() { clearState(); if (canEl) canEl.style.display = 'none'; },
  reset() { clearState(); resetWorld(); if (canEl) canEl.style.display = 'none'; },
  denied(why) { if (/sold out/.test(why)) WS.ch.n = 0; },
  key, step, update, flags, pose, remote, event, en, world, footKey,
};
// (screenshot scripts: the colas and walls out in the world)
export const vmDebug = () => ({ COLAS, WALLS, WS });
