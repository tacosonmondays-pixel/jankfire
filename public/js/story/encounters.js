// OVERDUE Act I encounters, the presentation + director half: watches the quest step and stages the set pieces that
// aren't boss fights. the sim half (shared/story/encsys.js + server/storyenc.js) owns the enemies: HP, hits, the
// rigs' driving and rams, the interns' business cards, the dogs' leaps. here: who stands where, when each wave comes,
// the soup, the HUD, the barks, the callouts, the sounds, and drawing the stand-ins over the referee's bots.
//   m02 SAUCE RUN       Lumps rides shotgun with the pot, the slosh meter, desk war-rigs on the Commute, the Ring
//                       Road ambush (EOTM's robbery and internship, 90 s to hold), the Choir clerk counting soup
// made by boot.js: makeEncounters(ST, { where }) -> { frame(dt, now), grade(quest) }. frame runs before the actors
// update (so anyone riding in a car is placed this frame, not the last).
import * as THREE from 'three';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { ME } from '../player.js';
import { encSfx } from '../audio.js';
import { BOXES } from '/shared/map.js';
import { raycast, query } from '/shared/physics.js';
import { carBoxes, carType } from '/shared/story/drive.js';
import { MISSIONS_ACT1 } from '/shared/story/content/missions/act1.js';
import { DV } from './drive.js';
import { actors, spawnActor, despawnActor, play, walkTo } from './actors.js';
import { talking } from './talk.js';
import { rigMesh, dogMesh, internBits, potMesh, potLevel, barricadeMesh, tradePostMesh } from './enc_looks.js';

const $ = (id) => document.getElementById(id);
const fin = Number.isFinite;
const pick = (a) => a[(Math.random() * a.length) | 0];
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
// tuning, in one place
export const ENC = {
  soup: { brake: 34, land: 6, perV: 2.2, cap: 22, ram: [9, 0.45, 24], lowAt: 35, barkCd: 5 }, // brake: m/s² the car can change speed by itself; land: a fall (m/s) the pot shrugs off; a ram: base + per m/s, capped
  ambush: { secs: 90, rigsAt: 96, grace: 2.5 }, // rigsAt: the rigs come once you're this far east (the Commute starts at x 96)
  ringRoad: [182, 0.8, 236], // (shared/city/slice.js PLACES 'commute:ring_road')
};
const SOUP_VAR = 'm02.soup';

// ------------------------------------------------------------ hud: the soup meter, the clock, barks
function css() {
  if ($('encCss')) return;
  const s = document.createElement('style'); s.id = 'encCss';
  s.textContent = `
#encHud{position:fixed;left:22px;top:44px;transform:rotate(-1deg);z-index:18;display:flex;flex-direction:column;align-items:flex-start;gap:12px;pointer-events:none;font-family:var(--font)}
#encHud.hidden,#encHud>.hidden{display:none}
#encHud>div{background:rgba(18,8,24,0.92);border:4px solid #ff4fd8;box-shadow:8px 8px 0 #4fd8ff;padding:6px 12px;color:#fff;display:flex;align-items:center;gap:8px;font-weight:700}
#encHud b{color:#ffe14d;letter-spacing:1px}
#encHud .bar{width:150px;height:16px;border:3px solid #000;background:#2a1020;position:relative;overflow:hidden}
#encHud .bar i{position:absolute;left:0;top:0;bottom:0;background:#e0401a;transition:width .15s}
#encHud .soup.low .bar i{background:#ff3030;animation:encblink .4s steps(2) infinite}
#encHud .soup.shake{animation:encshake .35s}
#encHud .clock span{font-size:26px;color:#fff;min-width:64px;text-align:center}
#encHud .clock.hot span{color:#ff3030}
#encHud .count{font-size:15px}
#encBark{position:fixed;left:50%;bottom:150px;transform:translateX(-50%) rotate(0.8deg);z-index:19;pointer-events:none;font-family:var(--font);background:#fff;color:#120818;border:4px solid #000;box-shadow:6px 6px 0 #ff4fd8;padding:6px 14px;font-size:20px;font-weight:700;max-width:70vw;transition:opacity .25s}
#encBark.hidden{opacity:0}
#encBark b{color:#ff00dc;margin-right:8px}
@keyframes encblink{50%{opacity:.35}}
@keyframes encshake{20%{transform:translate(-6px,2px) rotate(-3deg)}40%{transform:translate(5px,-2px) rotate(2deg)}60%{transform:translate(-3px,1px)}80%{transform:translate(2px,0)}}`;
  document.head.append(s);
}
function hudEl() {
  if ($('encHud')) return $('encHud');
  css();
  const h = document.createElement('div'); h.id = 'encHud'; h.className = 'hidden';
  h.innerHTML = '<div class="soup hidden"><b>SOUP</b><span class="bar"><i></i></span><em>100%</em></div><div class="clock hidden"><b class="lbl">HOLD THE ROAD</b><span>1:30</span><em class="count"></em></div>';
  document.body.append(h);
  const b = document.createElement('div'); b.id = 'encBark'; b.className = 'hidden'; document.body.append(b);
  return h;
}
let barkT = 0;
function bark(who, text, dur = 3) {
  hudEl(); const b = $('encBark');
  b.innerHTML = ''; const n = document.createElement('b'); n.textContent = who.toUpperCase(); b.append(n, document.createTextNode(text));
  b.classList.remove('hidden'); barkT = performance.now() + dur * 1000;
}

// ------------------------------------------------------------ the director
export function makeEncounters(ST, { where } = {}) {
  const E = { cur: '', st: null, units: new Map(), wrapped: null, hooked: false, soupPrev: null, barkCd: 0, carId: 0, props: [], t: 0 };
  const S = () => ST.S;
  const flag = (f) => !!(S() && S().st.flags[f]);
  const q = (id) => S() && S().st.quests[id];
  const send = (k, o) => G.story && G.story.send && G.story.send(k, o);
  const npcDef = (id) => S().defs.npcs[id];
  // someone from the cast, stood somewhere for an encounter (the roster leaves them alone while enc is set)
  function stand(id, p, yaw = 0) {
    let a = actors.get(id);
    if (!a) { const d = npcDef(id); if (!d) return null; a = spawnActor(id, d, p, yaw); }
    else { a.pos[0] = p[0]; a.pos[1] = p[1]; a.pos[2] = p[2]; a.home.p = p.slice(); a.home.face = yaw; a.yaw = yaw; a.path = null; }
    a.enc = true; a.hidden = false;
    return a;
  }
  function release(id) { const a = actors.get(id); if (a && a.enc) { a.enc = false; a.hold = false; a.ride = null; despawnActor(id); } }
  function prop(mesh, p, yaw = 0) { mesh.position.set(p[0], p[1], p[2]); mesh.rotation.y = yaw; G.scene.add(mesh); E.props.push(mesh); return mesh; }
  function clearProps() { for (const m of E.props) G.scene.remove(m); E.props = []; }
  // the floor under (x, z), from up to `up` above y; null over the void
  function floorAt(x, y, z, up = 30) { const h = raycast([x, y + up, z], [0, -1, 0], up + 40, BOXES); return h ? h.point[1] : null; }
  // somewhere a rig (or a pack of interns) can arrive from: open floor near p, about `dist` out along a direction
  function openSpot(p, dist, dirs) {
    for (const a of dirs) for (const d of [dist, dist * 0.75, dist * 1.25, dist * 0.5]) {
      const x = p[0] + Math.sin(a) * d, z = p[2] + Math.cos(a) * d, y = floorAt(x, p[1], z);
      if (y == null || Math.abs(y - p[1]) > 12) continue;
      const hits = query(BOXES, x - 2.2, z - 3, x + 2.2, z + 3, []).filter((b) => b.max[1] > y + 0.7 && b.min[1] < y + 2.6 && b.max[0] > x - 2.2 && b.min[0] < x + 2.2 && b.max[2] > z - 3 && b.min[2] < z + 3);
      if (!hits.length) return [x, y + 0.2, z];
    }
    return null;
  }
  function spawn(g, kind, at, n = 1, o = {}) { if (at) send('enc', { op: 'spawn', g, kind, at: at.map((v) => Math.round(v * 100) / 100), n, ...o }); }
  const clear = (g) => send('enc', g ? { op: 'clear', g } : { op: 'clear' });
  const alive = (g) => [...E.units.values()].filter((u) => u.g === g && !u.dead).length;

  // ---------------------------------------------------------- the sim's news
  function hook() {
    if (E.hooked || !G.story || !G.story.on) return;
    E.hooked = true;
    G.story.on('encOn', (m) => { for (const u of m.list || []) if (fin(u.pid)) E.units.set(u.pid, { pid: u.pid, id: String(u.id), kind: String(u.kind), g: String(m.g), dead: false, mesh: null, h: null }); });
    G.story.on('enc', (m) => onEnc(m.ev || {}));
    G.story.on('carIn', (m) => { if (m.car && fin(m.car.id)) E.carId = m.car.id; if (S()) S().emit({ type: 'enterCar', car: m.car && m.car.ty }); }); // any car you get into counts for 'steal a car'
  }
  function wrapCombat() {
    if (!G.story || G.story.combat === E.wrapped) return;
    const prev = G.story.combat;
    E.wrapped = (ev) => { if (typeof prev === 'function') prev(ev); onCombat(ev); };
    G.story.combat = E.wrapped;
  }
  function unitByTarget(id) { for (const u of E.units.values()) if (u.id === id) return u; return null; }
  function onCombat(ev) {
    if (!ev) return;
    if (ev.type === 'kill') {
      const u = unitByTarget(ev.target); if (!u) return;
      u.dead = true;
      const pos = Array.isArray(ev.at) ? ev.at : null;
      if (u.kind === 'war_rig') { encSfx.rigBoom(pos); hud.msg('RIG DECOMMISSIONED', 1.8, 'brag'); hud.impact(0.8); G.shake = Math.max(G.shake || 0, 1); }
      else if (u.kind === 'intern') { hud.msg(pick(['LET GO', 'CONTRACT NOT RENEWED', 'UNPAID LEAVE', 'EXIT INTERVIEW', 'RESTRUCTURED']), 0.9, 'brag'); }
      else if (u.kind === 'stomach_dog') { hud.msg(pick(['WALKIES CANCELLED', 'DIGESTED', 'NO']), 0.9, 'brag'); }
      if (E.st && E.st.onKill) E.st.onKill(u, ev);
    } else if (ev.type === 'down' && ev.who === 'me') { if (E.st && E.st.onDown) E.st.onDown(); }
    else if (ev.type === 'up' && ev.who === 'me') { if (E.st && E.st.onUp) E.st.onUp(); }
  }
  function onEnc(ev) {
    const u = E.units.get(ev.pid), r = G.remotes && G.remotes.get(ev.pid), pos = r ? r.pos : null;
    if (ev.type === 'ram') {
      encSfx.ram(Math.min(1.4, (ev.speed || 10) / 18), pos);
      G.shake = Math.max(G.shake || 0, ev.car ? 1.1 : 1.4); hud.impact(ev.car ? 0.5 : 0.9);
      hud.msg(ev.car ? pick(['RAMMED', 'CRUNCH', 'DESK TO THE FACE', 'SYNERGY']) : 'RUN OVER BY A DESK', 1.1, 'brag');
      if (ev.car && DV.car && Array.isArray(ev.v)) { DV.car.vx += ev.v[0] * 0.5; DV.car.vz += ev.v[2] * 0.5; DV.car.vy += Math.min(6, ev.v[1]); DV.car.ground = false; DV.car.spin = (DV.car.spin || 0) + (Math.random() - 0.5) * 2.4; }
      if (ev.car) soupHit(ENC.soup.ram[0] + (ev.speed || 0) * ENC.soup.ram[1], 'ram');
    } else if (ev.type === 'card') { encSfx.card(pos); if (Math.random() < 0.5) hud.msg(pick(['BUSINESS CARD!', "LET'S CONNECT!", 'NETWORKING!']), 0.8, 'brag'); }
    else if (ev.type === 'leap') encSfx.leap(pos);
    if (u && ev.type === 'leap' && u.mesh) u.mesh.userData.leapT = 0.5;
  }

  // ---------------------------------------------------------- drawing the stand-ins over the referee's bots
  function adopt(u, r) {
    if (u.adopted === r) return;
    u.adopted = r;
    if (u.kind === 'intern') { const b = internBits(); r.ch.root.add(b); u.bits = b; return; }
    if (u.kind !== 'war_rig' && u.kind !== 'stomach_dog') return;
    u.mesh = u.kind === 'war_rig' ? rigMesh() : dogMesh();
    G.scene.add(u.mesh);
    const upd = r.update.bind(r);
    r.update = (...a) => { upd(...a); r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; };
    if (u.kind === 'war_rig') r.hitboxes = () => (r.alive ? carBoxes({ ty: 'van', x: r.pos[0], y: r.pos[1], z: r.pos[2], h: u.h || 0 }) : []); // you shoot the rig, not a man-sized box in it
    else r.hitboxes = () => { const [x, y, z] = r.pos; return r.alive ? [{ min: [x - 0.6, y + 0.35, z - 0.6], max: [x + 0.6, y + 1.35, z + 0.6] }, { min: [x - 0.25, y + 0.95, z - 0.25], max: [x + 0.25, y + 1.4, z + 0.25], head: true }] : []; };
  }
  function drawUnits(dt) {
    for (const [pid, u] of E.units) {
      const r = G.remotes && G.remotes.get(pid);
      if (!r) { if (u.mesh) { G.scene.remove(u.mesh); u.mesh = null; } if (u.seenGone == null) u.seenGone = E.t; if (E.t - u.seenGone > 3 || u.dead) E.units.delete(pid); continue; }
      u.seenGone = null;
      adopt(u, r);
      if (!u.mesh) continue;
      const m = u.mesh, sp = Math.hypot(r.vel[0], r.vel[2]);
      if (sp > 1.2) { const h = Math.atan2(r.vel[0], r.vel[2]); u.h = u.h == null ? h : u.h + wrapA(h - u.h) * Math.min(1, dt * (u.kind === 'war_rig' ? 6 : 10)); }
      if (u.h == null) u.h = Math.atan2(ME.pos[0] - r.pos[0], ME.pos[2] - r.pos[2]);
      m.position.set(r.pos[0], r.pos[1], r.pos[2]); m.rotation.y = u.h;
      const U = m.userData;
      if (u.kind === 'war_rig') {
        for (const w of U.wheels) { w.sp.rotation.x += (sp / 0.42) * dt; if (w.steer) w.piv.rotation.y = Math.sin(E.t * 3 + pid) * 0.15; }
        U.body.rotation.z = Math.sin(E.t * 9 + pid) * 0.015 * Math.min(1, sp / 10); // the desks rattle
        if (!r.alive) { U.body.rotation.z = Math.min(1.2, U.body.rotation.z + dt * 2); m.position.y -= Math.min(0.6, (u.deadT = (u.deadT || 0) + dt) * 0.3); }
        if (u.honkT == null) u.honkT = E.t + 2 + Math.random() * 4;
        if (E.t > u.honkT && r.alive) { u.honkT = E.t + 5 + Math.random() * 6; encSfx.honk(r.pos); }
      } else { // the dog: legs at its speed, the jaw open when it's near you, a wag of intestine
        const ph = E.t * (4 + sp * 1.4);
        for (const l of U.legs) { l.hip.rotation.x = Math.sin(ph + l.ph) * 0.7 * Math.min(1, sp / 3); l.knee.rotation.x = Math.max(0, Math.sin(ph + l.ph + 1)) * 0.9 * Math.min(1, sp / 3); }
        const near = Math.hypot(ME.pos[0] - r.pos[0], ME.pos[2] - r.pos[2]) < 6;
        U.jaw.rotation.x = (near ? 0.55 : 0.12) + Math.sin(E.t * 14) * 0.08;
        U.tail.rotation.z = Math.sin(E.t * 10) * 0.5;
        if (U.leapT > 0) { U.leapT -= dt; m.rotation.x = -0.4; } else m.rotation.x = 0;
        if (!r.alive) { m.rotation.z = Math.min(Math.PI / 2, (m.rotation.z || 0) + dt * 5); }
        if (u.growlT == null) u.growlT = E.t + Math.random() * 3;
        if (E.t > u.growlT && r.alive) { u.growlT = E.t + 3 + Math.random() * 4; encSfx.growl(r.pos); }
      }
    }
  }

  // ---------------------------------------------------------- the soup (m02): a hidden 0-100 meter, shown while it rides
  const soup = () => { const v = S().st.vars[SOUP_VAR]; return fin(v) ? v : 100; };
  function soupHit(loss, why) {
    if (!soupOn() || flag('soup_spilled') || !(loss > 0.5)) return;
    const was = soup(), now = Math.max(0, was - Math.min(loss, ENC.soup.cap));
    S().st.vars[SOUP_VAR] = Math.round(now * 10) / 10;
    encSfx.slosh(Math.min(1.5, loss / 10));
    const h = hudEl().querySelector('.soup'); h.classList.remove('shake'); void h.offsetWidth; h.classList.add('shake');
    if (loss > 6) hud.msg(loss > 14 ? 'SPLOSH!' : 'SLOSH', 0.8, 'brag');
    if (now <= 0) {
      S().run(['flag:soup_spilled'], 'soup');
      encSfx.spill(); hud.msg('THE SOUP IS GONE', 2.6, 'brag'); G.shake = Math.max(G.shake || 0, 0.8);
      setTimeout(() => bark('lumps', "...that was forty people's.", 3.5), 900);
      return;
    }
    if (E.t > E.barkCd) {
      E.barkCd = E.t + ENC.soup.barkCd;
      const low = now < ENC.soup.lowAt;
      bark('lumps', low ? pick(["there's not much left in her.", 'please. please drive like a nan.', "sharon's going to ladle us."]) : why === 'ram' ? pick(['they hit the soup!', "that's a desk. why is it a car.", 'hold on to her!']) : pick(['slower on the bumps.', '...nobody saw that.', "she's full to the top.", 'mind the soup, mind the soup.']));
    }
  }
  const soupOn = () => { const Q = q('m02_sauce_run'); return !!(Q && !Q.done && !Q.failed && ['drive', 'ambush', 'deliver'].includes(Q.step) && ST.inv && ST.inv.has('soup_pot')); };
  function soupFrame(dt) {
    const on = soupOn(), h = hudEl().querySelector('.soup');
    h.classList.toggle('hidden', !on);
    if (!on) { E.soupPrev = null; return; }
    const v = soup(), spilled = flag('soup_spilled');
    h.querySelector('.bar i').style.width = `${spilled ? 0 : v}%`;
    h.querySelector('em').textContent = spilled ? 'EMPTY' : `${Math.ceil(v)}%`;
    h.classList.toggle('low', !spilled && v < ENC.soup.lowAt);
    // jolts: a landing (whatever you were falling at, past a kerb's worth) or the car's speed changing faster than the
    // brakes can manage (a wall, a parked car, a kerb at 80). by speeds, not per frame, so a slow machine slops the same
    const c = DV.car;
    if (c && dt > 0 && dt < 0.5) {
      const P = E.soupPrev, vh = [c.vx, c.vz];
      if (P) {
        const dvh = Math.hypot(vh[0] - P.vh[0], vh[1] - P.vh[1]) - (ENC.soup.brake * dt + 2.5);
        const land = c.ground && !P.ground ? -P.vy - ENC.soup.land : 0;
        const loss = Math.max(0, dvh) * ENC.soup.perV + Math.max(0, land) * ENC.soup.perV;
        if (loss > 0.5) soupHit(loss, 'jolt');
      }
      E.soupPrev = { vh, vy: c.vy, ground: c.ground };
    } else E.soupPrev = null;
  }

  // ---------------------------------------------------------- lumps riding shotgun with the pot
  let pot = null;
  function carMesh() { const x = DV.meshes.get(DV.car ? DV.id : E.carId); return x || null; }
  function ride(on) {
    const x = on ? carMesh() : null;
    if (!x) { const a = actors.get('lumps'); if (a && a.ride) { a.ride = null; a.hold = false; } if (pot) pot.visible = false; return false; }
    const c = DV.car && DV.id === x.c.id ? { x: DV.car.x, y: DV.car.y, z: DV.car.z, h: DV.car.h, ty: DV.car.ty } : { x: x.c.p[0], y: x.c.p[1], z: x.c.p[2], h: x.c.h, ty: x.c.ty };
    const T = carType(c.ty), f = [Math.sin(c.h), 0, Math.cos(c.h)], s = [f[2], 0, -f[0]];
    const seat = [c.x - f[0] * T.L * 0.08 - s[0] * T.W * 0.22, c.y + Math.max(0.15, T.H * 0.62 - 1.45), c.z - f[2] * T.L * 0.08 - s[2] * T.W * 0.22]; // the passenger side (yours is the right)
    const a = stand('lumps', seat, c.h + Math.PI); if (!a) return false;
    a.ride = x.c.id; a.hold = true; a.pos[0] = seat[0]; a.pos[1] = seat[1]; a.pos[2] = seat[2]; a.yaw = c.h + Math.PI;
    if (!pot) { pot = potMesh(); G.scene.add(pot); }
    pot.visible = true; potLevel(pot, flag('soup_spilled') ? 0 : soup() / 100);
    pot.position.set(seat[0] + f[0] * 0.45, seat[1] + 0.95, seat[2] + f[2] * 0.45); pot.rotation.set(Math.sin(E.t * 7) * 0.04 * Math.min(1, DV.car ? Math.hypot(DV.car.vx, DV.car.vz) / 10 : 0), c.h, 0);
    pot.userData.lid.rotation.z = Math.sin(E.t * 31) * 0.05; pot.userData.lid.position.y = 0.48 + Math.abs(Math.sin(E.t * 23)) * 0.02;
    return true;
  }

  // ---------------------------------------------------------- the clock
  function clockHud(on, left, label, count) {
    const h = hudEl().querySelector('.clock');
    h.classList.toggle('hidden', !on); if (!on) return;
    h.querySelector('.lbl').textContent = label;
    const s = Math.max(0, Math.ceil(left));
    h.querySelector('span').textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
    h.classList.toggle('hot', s <= 10);
    h.querySelector('.count').textContent = count || '';
  }

  // ---------------------------------------------------------- m02 SAUCE RUN, step by step
  const M02 = 'm02_sauce_run';
  const kitchen = () => (where && where('bottom:soup_kitchen')) || [-105, 0, 238];
  const STEPS = {
    [M02]: {
      brief: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); } },
      car: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); bark('lumps', 'he means steal a car. take the sofa one. tony won\'t wake up.', 4); } },
      pot: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); } },
      drive: {
        enter(st) { st.rigs = false; S().st.vars[SOUP_VAR] ??= 100; },
        tick(st, dt) {
          if (!ride(true)) { const a = actors.get('lumps'); if (!a) stand('lumps', [ME.pos[0] + 1.5, ME.pos[1], ME.pos[2] + 1.5], ME.yaw); else if (!a.path && Math.hypot(a.pos[0] - ME.pos[0], a.pos[2] - ME.pos[2]) > 4) walkTo(a, [[ME.pos[0] + 1.2, ME.pos[1], ME.pos[2] + 1.2]], 6); }
          // the Commute: the Unpaid come out to meet you before you even reach the road
          if (!st.rigs && ME.pos[0] > ENC.ambush.rigsAt && DV.car) {
            st.rigs = true;
            const ahead = Math.atan2(ENC.ringRoad[0] - ME.pos[0], ENC.ringRoad[2] - ME.pos[2]);
            for (const da of [0.5, -0.5]) spawn('m02rig', 'war_rig', openSpot(ME.pos, 55, [ahead + da, ahead + da * 2, ahead + Math.PI / 2 * Math.sign(da)]));
            hud.msg('THE UNPAID', 2, 'brag'); encSfx.honk(); bark('lumps', "rigs. that's the unpaid. hold on to the soup.", 3.5);
          }
        },
        exit() {},
      },
      ambush: {
        enter(st) {
          st.phase = 'talk'; st.t0 = E.t; st.wave = 0; st.left = ENC.ambush.secs; st.deaths = 0;
          const rr = ENC.ringRoad, by = floorAt(rr[0], rr[1], rr[2] - 20) ?? rr[1];
          st.home = [rr[0], (floorAt(rr[0], rr[1], rr[2]) ?? rr[1]) + 0.2, rr[2]];
          prop(barricadeMesh(24), [rr[0], by, rr[2] - 20], 0);
          const ey = floorAt(rr[0] + 3, rr[1] + 8, rr[2] - 10, 6) ?? by;
          stand('eotm', [rr[0] + 3, ey, rr[2] - 10], 0); // in front of the desks, up on whatever's there (a car roof, if the jam put one there)
          send('hold', { all: true, on: true });
          encSfx.honk(); setTimeout(() => encSfx.honk(), 450);
          hud.msg('HALT', 1.4, 'brag');
        },
        tick(st, dt) {
          ride(true);
          const Q = q(M02);
          if (st.phase === 'talk') {
            const chose = flag('fought_the_unpaid') || flag('paid_the_unpaid') || flag('eotm_offered_internship');
            if ((chose && !talking()) || (!talking() && E.t - st.t0 > 5)) startFight(st);
            if (Q) Q.t = 0; // the survive clock starts when the shooting does
            return;
          }
          st.left = Math.max(0, ENC.ambush.secs - (Q ? Q.t : 0));
          clockHud(true, st.left, st.fight ? 'HOLD THE ROAD' : 'THEY HAVE TWO DEPARTMENTS', `the unpaid: ${alive('m02a') + alive('m02b') + alive('m02c') + alive('m02rig')}`);
          const el = ENC.ambush.secs - st.left;
          // waves: the second department, then the overtime department
          if (st.wave === 1 && el > 28) { st.wave = 2; wave(st, st.fight ? 5 : 4, 'm02b'); hud.msg(st.fight ? 'MORE INTERNS' : "THEY DIDN'T GET THE MEMO", 1.5, 'brag'); }
          if (st.wave === 2 && el > 55) { st.wave = 3; if (st.fight) { spawn('m02rig', 'war_rig', openSpot(st.home, 50, [Math.PI, Math.PI * 0.75, Math.PI * 1.25])); hud.msg('ANOTHER RIG', 1.5, 'brag'); encSfx.honk(); } wave(st, 3, 'm02c'); }
          if (Math.ceil(st.left) !== st.tickS && st.left <= 10) { st.tickS = Math.ceil(st.left); encSfx.tick(st.left <= 3); }
          // EOTM up top keeps the meeting going
          if ((st.motT ??= E.t + 6) < E.t) { st.motT = E.t + 7 + Math.random() * 5; bark('employee of the month', pick(['SYNERGY!', 'the grind never stops.', 'this is a learning opportunity.', 'who wants to be employee of the month? ME. AGAIN.', "we're a family. a family that robs.", 'CIRCLE BACK ON THAT SOUP.']), 2.6); }
          // you fell behind: ride back to the road (a death restarts the meeting)
          if (Math.hypot(ME.pos[0] - st.home[0], ME.pos[2] - st.home[2]) > 140 && !st.warned) { st.warned = true; bark('lumps', "we can't leave. they'll follow the soup.", 3); }
        },
        onDown(st) { st.deaths++; },
        onUp(st) { // back up (the Machine dispensed you miles away): you're put back at the road, and the meeting starts again
          ME.pos = st.home.slice(); ME.vel = [0, 0, 0];
          clear('m02a'); clear('m02b'); clear('m02c');
          const Q = q(M02); if (Q) Q.t = 0;
          st.wave = 0; startFight(st, true);
          hud.msg('THE MEETING STARTS AGAIN', 2, 'brag');
        },
        exit(st) {
          clockHud(false);
          for (const g of ['m02a', 'm02b', 'm02c', 'm02rig']) clear(g);
          clearProps();
          const a = actors.get('eotm'); if (a) { bark('employee of the month', "the pizza's gone. WE'LL CIRCLE BACK.", 3.5); setTimeout(() => release('eotm'), 3500); }
          if (st.phase !== 'talk') { encSfx.clockout(); hud.msg('THE PIZZA RAN OUT', 2.4, 'brag'); }
        },
      },
      deliver: {
        enter(st) { tradePost(); st.said = false; },
        tick(st) {
          ride(true);
          if (!st.said && ME.pos[2] < 120 && ME.pos[0] < 96) { st.said = true; bark('lumps', "up the hill. the gut's at the top. don't touch the walls.", 4); }
        },
      },
      count: { enter() { tradePost(); lumpsAtCounter(); }, exit() {} },
      count_empty: { enter() { tradePost(); lumpsAtCounter(); } },
    },
  };
  // the trade post: a counter at the border gate, the clerk behind it
  function tradePost() {
    if (E.post) return;
    const b = (where && where('gut:border')) || [-44, 36, -14], x = b[0] + 6, z = b[2] - 1.5, y = floorAt(x, b[1], z) ?? b[1];
    E.post = prop(tradePostMesh(), [x, y, z], -Math.PI / 2);
    stand('sister_agenda', [x - 0.9, y, z], Math.PI / 2); // behind the counter, facing the stairs
  }
  function lumpsAtCounter() {
    const b = (where && where('gut:border')) || [-44, 36, -14], y = floorAt(b[0] + 3.5, b[1], b[2] + 1) ?? b[1];
    const a = stand('lumps', [b[0] + 3.5, y, b[2] + 1], Math.PI); if (a) { a.hold = false; a.ride = null; }
    if (pot) pot.visible = false;
  }
  function wave(st, n, g) {
    const home = st.home, back = Math.atan2(home[0] - ME.pos[0], home[2] - ME.pos[2]); // (they come from the barricade side)
    const at = openSpot(home, 24, [Math.PI, Math.PI * 0.8, Math.PI * 1.2, back]) || [home[0], home[1], home[2] - 20];
    const shoot = Math.ceil(n * 0.6);
    spawn(g, 'intern', at, shoot, { w: 'pistol', name: 'UNPAID INTERN' });
    if (n - shoot > 0) spawn(g, 'intern', at.map((v, i) => (i === 0 ? v + 4 : v)), n - shoot);
  }
  function startFight(st, again) {
    st.phase = 'fight'; st.fight = flag('fought_the_unpaid') || !(flag('paid_the_unpaid') || flag('eotm_offered_internship'));
    send('hold', { all: true, on: false });
    if (!again) {
      if (st.fight) { hud.msg('ONBOARDING', 1.8, 'brag'); }
      else { send('enc', { op: 'flee', g: 'm02rig' }); encSfx.honk(); setTimeout(() => clear('m02rig'), 7000); hud.msg('THE RIGS PULL BACK', 1.6, 'brag'); setTimeout(() => bark('lumps', "i think there's two departments.", 3), 1800); }
    }
    st.wave = 1; wave(st, st.fight ? 6 : 4, 'm02a');
  }

  // ---------------------------------------------------------- every frame (from boot.js, before the actors move)
  E.frame = (dt, now) => {
    E.t += dt;
    hook(); wrapCombat();
    if (!S() || !ST.on) return;
    // which of our steps is on (the tracked main quest first)
    let key = '', qid = '', sid = '';
    for (const id of Object.keys(STEPS)) { const Q = q(id); if (Q && !Q.done && !Q.failed && Q.step && STEPS[id][Q.step]) { key = `${id}/${Q.step}`; qid = id; sid = Q.step; break; } }
    if (key !== E.cur) {
      const [oq, os] = E.cur.split('/'), old = oq && STEPS[oq] && STEPS[oq][os];
      if (old && old.exit) { try { old.exit(E.st); } catch (e) { console.warn('enc exit', e); } }
      E.cur = key; E.st = null;
      if (key) { const h = STEPS[qid][sid]; E.st = { onKill: null, onDown: () => h.onDown && h.onDown(E.st), onUp: () => h.onUp && h.onUp(E.st) }; try { if (h.enter) h.enter(E.st); } catch (e) { console.warn('enc enter', e); } }
      if (!key || qid !== M02) { const a = actors.get('lumps'); if (a && a.enc && !qid) release('lumps'); if (pot && qid !== M02) pot.visible = false; }
    }
    if (key) { const h = STEPS[qid][sid]; if (h.tick) { try { h.tick(E.st, dt); } catch (e) { console.warn('enc tick', e); } } }
    soupFrame(dt);
    drawUnits(dt);
    const H = hudEl(); H.classList.toggle('hidden', !!(ST.scene && ST.scene.playing()) || talking());
    if (barkT && performance.now() > barkT) { barkT = 0; $('encBark').classList.add('hidden'); }
  };
  // the review card's grade (boot.js asks on questDone): the soup decides m02's
  E.grade = (quest) => {
    if (quest !== M02) return null;
    const g = MISSIONS_ACT1[M02] && MISSIONS_ACT1[M02].grade; if (!g) return null;
    return flag('soup_spilled') ? g.see_me : soup() >= 98 ? g.exceeds : g.meets;
  };
  E.soupHit = soupHit; // (tests)
  E.units0 = E.units;
  return E;
}
