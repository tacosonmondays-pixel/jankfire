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
import { RAMP } from '/shared/city/act1set.js'; // (the Unpaid's jump ramp over the collapse: the ambush ends there)
import { hwY } from '/shared/city/slice.js';
import { actors, spawnActor, despawnActor, play, walkTo } from './actors.js';
import { talking } from './talk.js';
import { rigMesh, dogMesh, potMesh, potLevel, tradePostMesh } from './enc_looks.js';
import { glbLoader } from '../glbkit.js';
import { buildWeapon } from '../models.js';

// the art lane's models for encounter enemies (one line each to swap): a cast look drawn over the bot (the shared cast
// skeleton, walked by loco.js), or a vehicle glb. missing / not loaded = the code stand-ins in enc_looks.js
export const ENC_LOOKS = { intern: ['intern', 'intern_b'], collector: ['collector'] };
const VEHICLES = { war_rig: '/models/cast/c_war_rig.glb' }; // (front -z, ground y 0: wheel_*, castor_*, turret > gun > barrels)
const GLB = {};
function vehicle(kind) {
  const url = VEHICLES[kind]; if (!url) return null;
  if (!GLB[kind]) { GLB[kind] = { scene: null }; glbLoader().loadAsync(url).then((g) => { g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); GLB[kind].scene = g.scene; }).catch(() => { GLB[kind].bad = true; }); }
  if (!GLB[kind].scene) return null;
  const m = GLB[kind].scene.clone(true), by = (n) => m.getObjectByName(n);
  const lod = by('lod'); if (lod) lod.visible = false;
  m.userData = { glb: true, wheels: ['wheel_rl', 'wheel_rr', 'wheel_ml', 'wheel_mr', 'castor_l_spin', 'castor_r_spin'].map(by).filter(Boolean), castors: ['castor_l', 'castor_r'].map(by).filter(Boolean), turret: by('turret'), gun: by('gun'), barrels: by('barrels'), body: by('rig') || m };
  return m;
}

const $ = (id) => document.getElementById(id);
const fin = Number.isFinite;
const pick = (a) => a[(Math.random() * a.length) | 0];
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
// tuning, in one place
export const ENC = {
  soup: { brake: 34, land: 6, perV: 2.2, cap: 22, ram: [9, 0.45, 24], lowAt: 35, barkCd: 5 }, // brake: m/s² the car can change speed by itself; land: a fall (m/s) the pot shrugs off; a ram: base + per m/s, capped
  ambush: { secs: 90, rigsAt: 96, grace: 2.5 }, // rigsAt: the rigs come once you're this far east (the Commute starts at x 96)
  ringRoad: [182, 0.8, 236], // (shared/city/slice.js PLACES 'commute:ring_road')
  // m03: Lumps' walk from where he waits on Peristalsis Avenue (cast_slice.js STAGE) east to his mum's wall
  escort: { speed: 1.4, hurry: 4.5, wait: 7, path: [[-114, 40, -138.4], [-108, 40, -137.2], [-102, 40, -136.6], [-96.5, 40, -137.2], [-91.5, 40, -137.6]],
    lines: [[0, "it's warm. you get used to it. that's the bad bit."], [1, 'that was a bus stop. people waited at it. some of them still are.'], [3, "she'll say i look thin. i don't. i'm enormous."]] },
  // m03 'out': the stomach-dog chase from the Choir Lung to the Gut border gate
  chase: { max: 6, every: 13, lumpsSpeed: 9, carryFor: 2.2, carryUp: 9, land: [-44, 36.6, -15],
    carryAt: (p) => p[2] > -66 && p[2] < -28 && Math.abs(p[0] + 44) < 42 && p[1] > 38, // (the Clocking In plaza's south end, the last lungs before the gate)
    cps: [[-150, 40.4, -130, (p) => p[0] > -150 && p[2] < -110, 1], [-44, 40.4, -110, (p) => p[0] > -60 && p[2] > -118, 2]] },
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
    G.story.on('carIn', (m) => { if (m.car && fin(m.car.id)) E.carId = m.car.id; }); // (the car Lumps rides in. boot.js counts getting in for 'steal a car')
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
    if (ENC_LOOKS[u.kind]) { // a cast look over the bot: an actor that goes where the bot goes, holding its gun
      const looks = ENC_LOOKS[u.kind], a = spawnActor(`enc_${u.pid}`, { look: looks[u.pid % looks.length], idle: 'idle' }, r.pos.slice(), r.yaw);
      a.enc = true; a.encUnit = true; u.actor = a;
      if (r.w && a.ch.slot) { try { const wm = buildWeapon(r.w); a.ch.slot.add(wm); u.wm = r.w; } catch { /* (no gun drawn: still fights) */ } }
      const upd = r.update.bind(r);
      r.update = (...x) => { upd(...x); r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; };
      return;
    }
    if (u.kind !== 'war_rig' && u.kind !== 'stomach_dog') return;
    u.mesh = (u.kind === 'war_rig' && vehicle('war_rig')) || (u.kind === 'war_rig' ? rigMesh() : dogMesh());
    G.scene.add(u.mesh);
    const upd = r.update.bind(r);
    r.update = (...a) => { upd(...a); r.ch.root.visible = false; if (r.shadow) r.shadow.visible = false; };
    if (u.kind === 'war_rig') r.hitboxes = () => (r.alive ? carBoxes({ ty: 'van', x: r.pos[0], y: r.pos[1], z: r.pos[2], h: u.h || 0 }) : []); // you shoot the rig, not a man-sized box in it
    else r.hitboxes = () => { const [x, y, z] = r.pos; return r.alive ? [{ min: [x - 0.6, y + 0.35, z - 0.6], max: [x + 0.6, y + 1.35, z + 0.6] }, { min: [x - 0.25, y + 0.95, z - 0.25], max: [x + 0.25, y + 1.4, z + 0.25], head: true }] : []; };
  }
  function drawUnits(dt) {
    for (const [pid, u] of E.units) {
      const r = G.remotes && G.remotes.get(pid);
      if (!r) { if (u.mesh) { G.scene.remove(u.mesh); u.mesh = null; } if (u.actor) { despawnActor(u.actor.id); u.actor = null; } if (u.seenGone == null) u.seenGone = E.t; if (E.t - u.seenGone > 3 || u.dead) E.units.delete(pid); continue; }
      u.seenGone = null;
      adopt(u, r);
      if (u.actor) { // walk where the bot walks; down when it's down (tipped over, then gone with the body)
        const a = u.actor; a.pos[0] = r.pos[0]; a.pos[1] = r.pos[1]; a.pos[2] = r.pos[2]; a.yaw = r.yaw; a.home.face = r.yaw;
        if (r.w !== u.wm && a.ch.slot) { a.ch.slot.clear(); try { if (r.w) a.ch.slot.add(buildWeapon(r.w)); } catch { /* fine */ } u.wm = r.w; }
        a.ch.root.rotation.x = r.alive ? 0 : Math.max(-Math.PI / 2, (a.ch.root.rotation.x || 0) - dt * 6);
        continue;
      }
      if (!u.mesh) continue;
      const m = u.mesh, sp = Math.hypot(r.vel[0], r.vel[2]);
      if (sp > 1.2) { const h = Math.atan2(r.vel[0], r.vel[2]); u.h = u.h == null ? h : u.h + wrapA(h - u.h) * Math.min(1, dt * (u.kind === 'war_rig' ? 6 : 10)); }
      if (u.h == null) u.h = Math.atan2(ME.pos[0] - r.pos[0], ME.pos[2] - r.pos[2]);
      m.position.set(r.pos[0], r.pos[1], r.pos[2]); m.rotation.y = u.h;
      const U = m.userData;
      if (u.kind === 'war_rig' && U.glb) { // the art lane's rig: front is -z, so turned round; wheels, castors, the turret on you
        m.rotation.y = u.h + Math.PI;
        for (const w of U.wheels) w.rotation.x -= (sp / 0.45) * dt;
        for (const c of U.castors) c.rotation.y = Math.sin(E.t * 3 + pid) * 0.2;
        if (U.turret) { const want = Math.atan2(-(ME.pos[0] - r.pos[0]), -(ME.pos[2] - r.pos[2])) - m.rotation.y; U.turret.rotation.y += wrapA(want - U.turret.rotation.y) * Math.min(1, dt * 5); }
        if (U.barrels && r.alive) U.barrels.rotation.z += dt * 14; // (always spinning up: it's a minigun on a chair base)
        U.body.rotation.z = r.alive ? Math.sin(E.t * 9 + pid) * 0.012 * Math.min(1, sp / 10) : Math.min(1.1, U.body.rotation.z + dt * 2);
        if (!r.alive) m.position.y -= Math.min(0.6, (u.deadT = (u.deadT || 0) + dt) * 0.3);
        if (u.honkT == null) u.honkT = E.t + 2 + Math.random() * 4;
        if (E.t > u.honkT && r.alive) { u.honkT = E.t + 5 + Math.random() * 6; encSfx.honk(r.pos); }
      } else if (u.kind === 'war_rig') {
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
  const M02 = 'm02_sauce_run', M03 = 'm03_somethings_digesting';
  const kitchen = () => (where && where('bottom:soup_kitchen')) || [-105, 0, 238];
  const STEPS = {
    [M02]: {
      brief: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); } },
      car: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); bark('lumps', 'he means steal a car. take the sofa one. tony won\'t wake up.', 4); } },
      pot: { enter() { const k = kitchen(); stand('lumps', [k[0] + 3.2, k[1], k[2] - 2.5], -0.6); } },
      drive: {
        enter(st) { st.rigs = false; S().st.vars[SOUP_VAR] ??= 100; },
        tick(st, dt) {
          vehicle('war_rig'); // (start loading the rig's model before the Commute)
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
          st.phase = 'talk'; st.t0 = E.t; st.wave = 0; st.left = ENC.ambush.secs; st.won = 0;
          const rr = ENC.ringRoad;
          st.home = [rr[0], (floorAt(rr[0], rr[1], rr[2]) ?? rr[1]) + 0.2, rr[2]];
          // EOTM up on the jam beside the clear lanes, to rob you; then he's at the ramp (the Unpaid built it, he's proud of it)
          const ex = rr[0] + 7, ez = rr[2] - 9, ey = floorAt(ex, rr[1] + 6, ez, 8) ?? rr[1];
          stand('eotm', [ex, ey, ez], Math.atan2(-(ME.pos[0] - ex), -(ME.pos[2] - ez)));
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
          const n = alive('m02a') + alive('m02b') + alive('m02c') + alive('m02rig');
          clockHud(!st.won, st.left, 'SURVIVE THE UNPAID', `${n} after you · or jump the collapse`);
          const el = ENC.ambush.secs - st.left;
          // waves along the deck: the second department, then the overtime department
          if (st.wave === 1 && el > 28) { st.wave = 2; deckWave(st, [140, 118], st.fight ? 2 : 1, 'm02b'); wave(st, 3, 'm02b'); hud.msg(st.fight ? 'MORE INTERNS' : "THEY DIDN'T GET THE MEMO", 1.5, 'brag'); }
          if (st.wave === 2 && el > 55) { st.wave = 3; if (st.fight) { spawn('m02rig', 'war_rig', openSpot(ME.pos, 50, [Math.atan2(0, 1), 0.5, -0.5])); hud.msg('ANOTHER RIG', 1.5, 'brag'); encSfx.honk(); } wave(st, 3, 'm02c'); }
          if (Math.ceil(st.left) !== st.tickS && st.left <= 10 && !st.won) { st.tickS = Math.ceil(st.left); encSfx.tick(st.left <= 3); }
          // the climax: the Unpaid's own ramp over the collapse. land it (or climb out of the gap) and they can't follow
          if (!st.won && ME.pos[2] < RAMP.exit[0] && ME.pos[0] > RAMP.x0 - 12 && ME.pos[0] < RAMP.x1 + 12 && ME.pos[1] > hwY(ME.pos[2]) - 1.5) {
            st.won = E.t; encSfx.clockout();
            setTimeout(() => hud.msg("THEY DIDN'T BUDGET FOR THE JUMP", 2.4, 'brag'), 1400);
            bark('employee of the month', pick(['THAT WAS NOT IN THE BUDGET.', 'THAT RAMP IS COMPANY PROPERTY.', "WE'LL CIRCLE BACK. ON FOOT."]), 3);
          }
          if (st.won && E.t - st.won > 2.5 && Q && Q.t < ENC.ambush.secs) Q.t = ENC.ambush.secs; // (survived: they stop at the edge)
          // on the deck: the ramp comes into view
          if (!st.rampSaid && ME.pos[2] < RAMP.z1 + 45 && ME.pos[2] > RAMP.z1) { st.rampSaid = true; bark('lumps', "they built a ramp. why did they build a ramp. ...go faster.", 3.5); }
          // EOTM at the ramp keeps the meeting going
          if ((st.motT ??= E.t + 6) < E.t && !st.won) { st.motT = E.t + 7 + Math.random() * 5; bark('employee of the month', pick(['SYNERGY!', 'the grind never stops.', 'this is a learning opportunity.', 'who wants to be employee of the month? ME. AGAIN.', "we're a family. a family that robs.", 'JUMP IT! THAT\'S A STRETCH GOAL!']), 2.6); }
          if (Math.hypot(ME.pos[0] - st.home[0], ME.pos[2] - st.home[2]) > 220 && !st.warned) { st.warned = true; bark('lumps', "we can't leave. they'll follow the soup.", 3); }
        },
        onUp(st) { // back up (the Machine dispensed you miles away): you're put back at the road, and the meeting starts again
          if (st.won) return;
          ME.pos = st.home.slice(); ME.vel = [0, 0, 0];
          for (const g of ['m02a', 'm02b', 'm02c']) clear(g);
          const Q = q(M02); if (Q) Q.t = 0;
          st.wave = 0; startFight(st, true);
          hud.msg('THE MEETING STARTS AGAIN', 2, 'brag');
        },
        exit(st) {
          clockHud(false);
          for (const g of ['m02a', 'm02b', 'm02c', 'm02rig']) clear(g);
          clearProps();
          if (actors.get('eotm')) { if (!st.won) bark('employee of the month', "the pizza's gone. WE'LL CIRCLE BACK.", 3.5); setTimeout(() => release('eotm'), 3500); }
          if (st.phase !== 'talk' && !st.won) { encSfx.clockout(); hud.msg('THE PIZZA RAN OUT', 2.4, 'brag'); }
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
    [M03]: {
      walk: { // Lumps leads you down Peristalsis Avenue to his mum: walks, waits for you, talks, hates every metre of it
        enter(st) {
          st.path = ENC.escort.path.map((p) => p.slice()); st.i = 0; st.said = 0; st.waitT = 0;
          const a = stand('lumps', st.path[0], -Math.PI / 2); if (a) { a.hold = false; a.ride = null; }
          bark('lumps', "this way. stay close. and don't touch the walls.", 3.5);
        },
        tick(st, dt) {
          const a = actors.get('lumps'); if (!a) { stand('lumps', st.path[Math.min(st.i, st.path.length - 1)], -Math.PI / 2); return; }
          a.enc = true;
          const ahead = ME.pos[0] - a.pos[0]; // (the avenue runs east to his mum: + = you're ahead of him)
          if (st.i < st.path.length) {
            if (ahead < -ENC.escort.wait) { // you're lagging: he stops, turns round, waits
              if (a.path) { a.path = null; }
              if ((st.waitT += dt) > 4) { st.waitT = -6; bark('lumps', pick(["come on. please. i don't like standing still in here.", 'change. CHANGE. things that get lost in here turn into wall.', "it's this way. it's always this way."]), 3); }
            } else if (!a.path) {
              st.waitT = 0;
              const hurry = ahead > 6; // you rode the middle of the street: he jogs to catch up, mortified
              if (hurry && !st.hurried) { st.hurried = true; bark('lumps', "not the middle! it takes you places! ...slow down. it's my mum. i want to arrive like a normal person.", 4.5); }
              walkTo(a, [st.path[st.i]], hurry ? ENC.escort.hurry : ENC.escort.speed, () => { st.i++; a.path = null; });
            }
          } else if (!st.arrived) { // he's there: that's the escort done (quests.js: escort waits for the npc)
            st.arrived = true; a.faceTarget = 0; S().emit({ type: 'reach', zone: 'gut:digester_wall', npc: 'lumps' });
          }
          // the things he says on the way (one per stretch of the avenue)
          const lines = ENC.escort.lines;
          if (st.said < lines.length && st.i >= lines[st.said][0] && !st.hurried) { bark('lumps', lines[st.said][1], 4); st.said++; }
        },
        exit() { const a = actors.get('lumps'); if (a) { a.enc = false; a.path = null; } },
      },
      out: { // the stomach-dogs chase you out of the Gut; Lumps runs with you and carries you over the last bit
        enter(st) {
          st.cp = [ME.pos[0], ME.pos[1] + 0.2, ME.pos[2]]; st.next = E.t + 1.5; st.wave = 0; st.carry = null; st.done = false;
          encSfx.growl(); setTimeout(() => encSfx.growl(), 600);
          hud.msg('STOMACH-DOGS', 2, 'brag');
          bark('lumps', "that's the bishop's dogs. they're not the nice dogs. RUN.", 3.5);
          const a = stand('lumps', [ME.pos[0] + 1.5, ME.pos[1], ME.pos[2] + 1.5], ME.yaw); if (a) { a.hold = false; a.ride = null; }
        },
        tick(st, dt) {
          const a = actors.get('lumps');
          if (st.carry) return carryTick(st, dt, a);
          // lumps runs with you (not in your way: a step behind and to the side)
          if (a) {
            a.enc = true;
            const d = Math.hypot(ME.pos[0] - a.pos[0], ME.pos[2] - a.pos[2]);
            if (d > 30) { a.pos[0] = ME.pos[0] + 2; a.pos[1] = ME.pos[1]; a.pos[2] = ME.pos[2] + 2; a.path = null; }
            else if (d > 3.5 && !a.path) walkTo(a, [[ME.pos[0] + Math.sin(ME.yaw + 2.2) * 2, ME.pos[1], ME.pos[2] + Math.cos(ME.yaw + 2.2) * 2]], ENC.chase.lumpsSpeed, () => { a.path = null; });
          }
          // checkpoints: the avenue, the rib avenue (a death puts you back at the last one)
          for (const c of ENC.chase.cps) if (c[3](ME.pos) && !(st.cpN >= c[4])) { st.cp = c.slice(0, 3); st.cpN = c[4]; }
          // the dogs: a pack bursts out behind you, then more come in from behind and the sides, herding you on
          if (!st.done && E.t > st.next && alive('m03dog') < ENC.chase.max) {
            st.next = E.t + (st.wave ? ENC.chase.every : 0.1); st.wave++;
            const back = ME.yaw; // (behind you: openSpot's angles go x += sin, z += cos, and you face (-sin yaw, -cos yaw))
            const n = st.wave === 1 ? 3 : 2;
            for (let i = 0; i < n; i++) spawn('m03dog', 'stomach_dog', openSpot(ME.pos, st.wave === 1 ? 18 : 24, [back + (i - (n - 1) / 2) * 0.9, back + 0.5, back - 0.5]));
            if (st.wave === 2) bark('lumps', "they're herding us. don't stop. they want you to stop.", 3);
            if (st.wave > 1) encSfx.growl();
          }
          // the last stretch: Lumps picks you up and goes over the top
          if (!st.done && ENC.chase.carryAt(ME.pos)) startCarry(st, a);
        },
        onUp(st) { // dispensed back in the Bottom: you're put back at the last checkpoint, the dogs start over
          if (st.done) return;
          ME.pos = st.cp.slice(); ME.vel = [0, 0, 0];
          clear('m03dog'); st.next = E.t + 3; st.wave = 0;
          hud.msg('THE DOGS GOT BORED. THEY CAME BACK.', 2, 'brag');
        },
        exit(st) { clear('m03dog'); const a = actors.get('lumps'); if (a) { a.enc = false; a.hold = false; a.path = null; } if (st && st.carry) st.carry = null; },
      },
    },
  };
  // the carry: a short Moment. Lumps scoops you up and leaps the last lung to the gate; the dogs stop at the line
  function startCarry(st, a) {
    st.done = true;
    const to = ENC.chase.land.slice();
    st.carry = { t: 0, from: ME.pos.slice(), to, len: ENC.chase.carryFor };
    hud.msg('LUMPS HAS YOU', 1.6, 'brag'); G.shake = Math.max(G.shake || 0, 0.6);
    bark('lumps', 'sorry. sorry. hold on.', 2.5);
    if (a) { a.hold = true; a.path = null; play(a, 'flex'); }
    encSfx.leap(); send('enc', { op: 'flee', g: 'm03dog' });
  }
  function carryTick(st, dt, a) {
    const c = st.carry; c.t += dt;
    const k = Math.min(1, c.t / c.len), e = k * k * (3 - 2 * k), up = Math.sin(k * Math.PI) * ENC.chase.carryUp;
    ME.pos = [c.from[0] + (c.to[0] - c.from[0]) * e, c.from[1] + (c.to[1] - c.from[1]) * e + up, c.from[2] + (c.to[2] - c.from[2]) * e]; ME.vel = [0, 0, 0];
    if (a) { a.enc = true; a.pos[0] = ME.pos[0] - 0.7; a.pos[1] = ME.pos[1] - 0.9; a.pos[2] = ME.pos[2] - 0.4; a.yaw = Math.atan2(-(c.to[0] - c.from[0]), -(c.to[2] - c.from[2])); }
    if (k >= 1) {
      st.carry = null; clear('m03dog');
      G.shake = Math.max(G.shake || 0, 0.9); encSfx.ram(0.6);
      hud.msg('THE DOGS STOP AT THE GATE', 2.2, 'brag');
      if (a) { a.hold = false; a.pos[1] = c.to[1]; }
      setTimeout(() => bark('lumps', "they're not allowed past the gate. it's in their contract. ...sorry i picked you up.", 4), 900);
    }
  }
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
  // a pack of interns where they'll come at you from: behind (they chase you up the road)
  function wave(st, n, g) {
    const back = DV.car ? DV.car.h + Math.PI : ME.yaw; // (openSpot's angles: x += sin, z += cos. a car faces (sin h, cos h); you face (-sin yaw, -cos yaw))
    const at = openSpot(ME.pos, 26, [back, back + 0.6, back - 0.6, Math.PI]) || [ME.pos[0], ME.pos[1], ME.pos[2] + 20];
    const shoot = Math.max(1, Math.round(n / 3)); // (a third shoot: the rest run at you with whatever's to hand)
    spawn(g, 'intern', at, shoot, { w: 'pistol' });
    if (n - shoot > 0) spawn(g, 'intern', [at[0] + 3, at[1], at[2]], n - shoot);
  }
  // interns up on the jam either side of the clear lanes, waiting for you to drive past (z: along the deck)
  function deckWave(st, zs, per, g) {
    let k = 0;
    for (const z of zs) for (const x of [RAMP.x0 - 6, RAMP.x1 + 6]) { const y = floorAt(x, hwY(z) + 4, z, 6); if (y != null) spawn(g, 'intern', [x, y + 0.2, z], per, k++ % 2 ? {} : { w: 'pistol' }); } // (every other post has a gun)
  }
  function startFight(st, again) {
    st.phase = 'fight'; st.fight = flag('fought_the_unpaid') || !(flag('paid_the_unpaid') || flag('eotm_offered_internship'));
    send('hold', { all: true, on: false });
    if (!again) {
      if (st.fight) { hud.msg('ONBOARDING', 1.8, 'brag'); }
      else { send('enc', { op: 'flee', g: 'm02rig' }); encSfx.honk(); setTimeout(() => clear('m02rig'), 7000); hud.msg('THE RIGS PULL BACK', 1.6, 'brag'); setTimeout(() => bark('lumps', "i think there's two departments.", 3), 1800); }
    }
    st.wave = 1; wave(st, st.fight ? 4 : 3, 'm02a');
    if (!again) deckWave(st, [200, 165], 1, 'm02a');
    // EOTM goes to stand by his ramp (the meeting continues there)
    const R = RAMP, ex = R.x1 + 2.4, ez = R.z0 + 3, ey = floorAt(ex, hwY(ez) + 3, ez, 5);
    if (ey != null) stand('eotm', [ex, ey, ez], 0);
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
      if (qid !== M02) { const a = actors.get('lumps'); if (a && a.ride) { a.ride = null; a.hold = false; } }
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
