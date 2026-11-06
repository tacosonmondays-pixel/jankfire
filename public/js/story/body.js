// OVERDUE body (WP5) on the client: the HYPE meter and Coupons on the HUD, what the slice's implants do to you, the
// Meat Mechanic's clinic screen, and the implants you can see on your mannequin. the sim (shared/story/bodysys.js)
// owns the body, HYPE and coupons; this shows them and runs the perks that live in your hands and legs.
//   Spring Knees: higher jumps (player.js ME.jumpMul); 1 in 20 landings the knee folds and you stumble
//   Pigeon Eyes: loot beams show through walls within 40 m; your view wobbles; now and then you see out of the back eye
//   Second Stomach: hold F on a dropped weapon to eat it for HP; burps every 30 s; three in a row and you vomit your gun
//   Cracked Punch-Clock: every 60 s a free magazine (no reload); under 20 HP time slows once a life; it ticks; clock in
import * as THREE from 'three';
import { G } from '../ctx.js';
import { hud } from '../hud.js';
import { ME } from '../player.js';
import { W, magOf } from '../weapons.js';
import { synth } from '../audio.js';
import { buildCharacter } from '../models.js';
import { showCharacter, renderPreview, resizePreview } from '../preview.js';
import { IMPLANTS, BODY_SLOTS, perk, UNINSTALL_FEE } from '/shared/story/implants.js';
import { HYPE, hypeCost } from '/shared/story/bodysys.js';
import { TEST } from '/shared/story/testmap.js';
import { IV, dropHeld } from './bar.js';
import { kindOf } from '/shared/story/items.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
export const B = { body: { slots: {}, perm: 0 }, drift: 0, budget: 3, band: 'cale', hype: 0, coupons: 0 };
let story = null, hudEl = null, clinic = null, clinicOn = false, clinicMsg = '', pvEl = null; // pvEl: the shared preview canvas (a redraw would detach it)
const P = {}; // the perks right now (implants.js perk()), by implant id
export const bodyDebug = () => st; // tests poke the timers
const st = { air: 0, wasGround: true, burpT: 0, flipT: 0, flipUntil: 0, freeT: 0, freeReady: false, slowUsed: false, slowUntil: 0, tickT: 0, clockT: 0, clockAsk: 0, stillT: 0, hold: null };

export function initBody(s) {
  story = s;
  s.on('body', (m) => { B.body = m.body; B.drift = m.drift; B.budget = m.budget; B.band = m.band; perks(); drawHud(); if (clinicOn) drawClinic(); });
  s.on('hype', (m) => { B.hype = m.v; drawHud(); if (m.why === 'short') hud.msg(`NEED ${m.need} HYPE (YOU HAVE ${m.v})`, 1.6); });
  s.on('coupons', (m) => { B.coupons = m.v; drawHud(); if (m.d) hud.msg(`${m.d > 0 ? '+' : ''}${m.d} COUPONS`, 1); if (clinicOn) drawClinic(); });
  s.on('clinicErr', (m) => { clinicMsg = m.err; if (clinicOn) drawClinic(); else hud.msg(m.err.toUpperCase(), 1.6); });
  s.on('installed', (m) => { const n = IMPLANTS[m.b] ? IMPLANTS[m.b].name : m.b; clinicMsg = m.op === 'install' ? `${n} is in. it's warm.` : `${n} is out. there's a hole now.`; synth.noise(0.25, 0.4, 'bandpass', 600, 200); synth.tone('sine', 300, 120, 0.3, 0.2); drawClinic(); });
  s.on('ate', (m) => { hud.msg(`ATE IT · +${m.hp} HP`, 1.2, 'brag'); synth.tone('square', 180, 70, 0.25, 0.25); synth.noise(0.2, 0.5, 'lowpass', 900, 200, null, 0.05); if (m.vomit) setTimeout(vomit, 400); });
  s.on('fined', (m) => { ME.hp = m.hp; hud.msg(`LATE. -${m.n} HP FINE.`, 1.8, 'brag'); synth.tone('square', 880, 440, 0.15, 0.2); });
  IV.on(() => { if (clinicOn) drawClinic(); });
}
const has = (id) => !!P[id];
function perks() {
  const ctx = {};
  for (const k of Object.keys(P)) delete P[k];
  for (const id of ['pigeon_eyes', 'spring_knees', 'core_second_stomach', 'core_cracked_punch_clock']) { const p = perk(B.body, id, ctx); if (p) P[id] = p; }
  ME.jumpMul = has('spring_knees') ? Math.sqrt(P.spring_knees.jump) : 1; // jump height x1.8 = jump speed x sqrt(1.8)
}
export function bodyLeave() { ME.jumpMul = 1; st.slowUntil = 0; if (hudEl) hudEl.classList.add('hidden'); if (clinicOn) toggleClinic(false); }
export const clinicOpen = () => clinicOn;
export const atClinic = () => Math.hypot(ME.pos[0] - TEST.clinic.p[0], ME.pos[2] - TEST.clinic.p[2]) < TEST.clinic.r;
// the Punch-Clock's low-HP slow (the weapon wheel's 20% is separate, main.js multiplies the two)
export const bodyTimeScale = () => (performance.now() < st.slowUntil ? P.core_cracked_punch_clock.slowScale : 1);
// pigeon eyes see loot beams through walls (bar.js asks per drop)
export const seesLoot = (dist) => has('pigeon_eyes') && dist < P.pigeon_eyes.seeLoot;

// ------------------------------------------------------------ the HUD: HYPE + coupons
function drawHud() {
  if (!hudEl) { hudEl = el('div', 'st-hype'); hudEl.id = 'storyHype'; document.body.append(hudEl); }
  hudEl.innerHTML = '';
  const bar = el('div', 'st-hbar'), fill = el('i');
  fill.style.width = `${Math.max(0, Math.min(100, B.hype))}%`;
  bar.append(fill, el('b', null, `HYPE ${Math.round(B.hype)}`));
  hudEl.append(bar, el('span', 'st-coupons', `☺ ${B.coupons.toLocaleString('en')} COUPONS`));
  if (B.drift >= 2) hudEl.append(el('span', 'st-drift', `DRIFT ${B.drift}`));
}

// ------------------------------------------------------------ keys (story/main.js hands F + its release here first)
// Second Stomach: holding F on a weapon on the floor eats it; a tap still picks it up
export function bodyKey(e, down, drop) {
  if (down && drop && has('core_second_stomach') && drop.item && ['gun', 'melee'].includes(kindOf(drop.item.b))) { st.hold = { id: drop.id, t: performance.now() }; return 'hold'; }
  if (!down && st.hold) { const h = st.hold; st.hold = null; if (performance.now() - h.t < P.core_second_stomach.eatHold * 1000) return { pick: h.id }; return 'done'; }
  return null;
}

// ------------------------------------------------------------ every frame
export function bodyTick(dt, cam) {
  const now = performance.now(), on = G.joined && G.mode === 'story' && ME.alive;
  if (hudEl) hudEl.classList.toggle('hidden', !(G.joined && G.mode === 'story'));
  if (clinicOn) { renderPreview(dt); if (!atClinic() || !$('menu').classList.contains('hidden')) toggleClinic(false); }
  if (!on) return;
  if (st.hold && now - st.hold.t >= (P.core_second_stomach ? P.core_second_stomach.eatHold * 1000 : 1e9)) { story.send('eatDrop', { id: st.hold.id }); st.hold = null; }
  // Spring Knees: count air time; a hard landing folds the wrong knee 1 in 20 times
  if (!ME.onGround) st.air += dt;
  if (ME.onGround && !st.wasGround) {
    if (has('spring_knees') && st.air > 0.35 && Math.random() < P.spring_knees.fold) {
      st.folds = (st.folds || 0) + 1; ME.frozenUntil = now + P.spring_knees.stumble * 1000; G.shake = Math.max(G.shake || 0, 0.8);
      hud.msg('YOUR KNEE FOLDED THE WRONG WAY', 1.2, 'brag'); synth.noise(0.12, 0.7, 'highpass', 2500, 800); synth.tone('square', 140, 60, 0.15, 0.25);
    } else if (has('spring_knees') && st.air > 0.35) synth.tone('sine', 220, 660, 0.12, 0.08); // boing
    st.air = 0;
  }
  st.wasGround = ME.onGround;
  // Pigeon Eyes: a little wobble, and now and then a look out of the back eye
  if (has('pigeon_eyes') && cam) {
    const p = P.pigeon_eyes;
    cam.rotation.z += Math.sin(now / 430) * p.wobble;
    st.flipT += dt;
    if (st.flipT > p.flipEvery * (0.6 + Math.random() * 0.8)) { st.flipT = 0; st.flipUntil = now + p.flipFor * 1000; synth.tone('triangle', 900, 1400, 0.06, 0.06); }
    if (now < st.flipUntil) cam.rotation.y += Math.PI; // the backwards eye
  }
  // Second Stomach: burps (they give you away; co-op will hear them)
  if (has('core_second_stomach')) {
    st.burpT += dt;
    if (st.burpT > P.core_second_stomach.burpEvery) { st.burpT = 0; hud.msg('*BUUURP*', 1, 'brag'); synth.tone('sawtooth', 110, 70, 0.5, 0.3); synth.noise(0.45, 0.35, 'lowpass', 400, 150); }
  }
  // the Cracked Punch-Clock
  if (has('core_cracked_punch_clock')) {
    const p = P.core_cracked_punch_clock;
    st.tickT += dt;
    if (st.tickT >= 1) { st.tickT = 0; synth.tone('square', 2600, 2600, 0.01, 0.05); } // it ticks. loudly
    st.freeT += dt;
    if (!st.freeReady && st.freeT >= p.freeMagEvery) { st.freeReady = true; hud.msg('UNPAID OVERTIME READY', 1, 'brag'); }
    const w = W.cur;
    if (st.freeReady && w && magOf(w) && W.ammo[w] <= 0) { W.ammo[w] = magOf(w); W.reloadId = null; st.freeReady = false; st.freeT = 0; hud.msg('UNPAID OVERTIME: NO RELOAD', 1.2, 'brag'); synth.tone('square', 1200, 2400, 0.08, 0.12); }
    if (ME.hp > 60) st.slowUsed = false; // a new life (or healed up): the slow is back
    if (!st.slowUsed && ME.hp > 0 && ME.hp < p.slowAt) { st.slowUsed = true; st.slowUntil = now + p.slowFor * 1000; hud.msg('OVERTIME', 1.4, 'brag'); synth.tone('sine', 400, 100, 1.2, 0.2); }
    // clock in: every so often, stand still for 5 s or pay a fine
    st.clockT += dt;
    if (!st.clockAsk && st.clockT >= p.clockEvery) { st.clockAsk = now; st.stillT = 0; hud.msg(`CLOCK IN: STAND STILL ${p.clockStill} S`, 2.5, 'brag'); }
    if (st.clockAsk) {
      const still = Math.hypot(ME.vel[0], ME.vel[2]) < 0.4 && ME.onGround;
      st.stillT = still ? st.stillT + dt : 0;
      if (st.stillT >= p.clockStill) { st.clockAsk = 0; st.clockT = 0; hud.msg('CLOCKED IN', 1, 'brag'); synth.tone('square', 600, 600, 0.1, 0.15); synth.tone('square', 900, 900, 0.1, 0.15, null, 0.12); }
      else if (now - st.clockAsk > 15000) { st.clockAsk = 0; st.clockT = 0; story.send('fine', {}); }
    }
  }
}
function vomit() { hud.msg('BLEUUURGH', 1.4, 'brag'); synth.noise(0.6, 0.7, 'lowpass', 700, 120); dropHeld(); } // three weapons in a row: your gun comes back up

// ------------------------------------------------------------ the clinic (F at the Meat Mechanic's chair)
export function toggleClinic(on = !clinicOn) {
  clinicOn = on;
  if (!clinic) { clinic = el('div', 'st-pick st-clinicwrap hidden'); clinic.id = 'storyClinic'; document.body.append(clinic); }
  clinic.classList.toggle('hidden', !on);
  if (on) { clinicMsg = 'sit down. this will only hurt a lot.'; if (document.pointerLockElement) document.exitPointerLock(); drawClinic(); }
  else { const home = $('heroSlot'); if (pvEl && home && clinic.contains(pvEl)) home.append(pvEl); }
}
const BAND = { cale: "you're still you. mostly.", fading: 'the memories are getting quiet.', employee: "you'd make a perfect employee." };
function drawClinic() {
  const inv = IV.inv;
  if (!inv) return;
  clinic.innerHTML = '';
  const panel = el('div', 'st-panel st-clinic');
  const top = el('div', 'st-bagtop');
  top.append(el('h2', null, 'MEAT MECHANIC'), el('span', 'st-sub', `budget ${Object.keys(B.body.slots).length}/${B.budget} · drift ${B.drift} · ${BAND[B.band]}`));
  const close = el('button', 'st-btn', 'LEAVE'); close.addEventListener('click', () => toggleClinic(false)); top.append(close);
  panel.append(top, el('div', 'st-info', clinicMsg || ''));
  const cols = el('div', 'st-ccols');
  // you, on the plinth, with your implants on
  const me = el('div', 'st-cme');
  me.append(el('b', 'st-lbl', 'YOU (MOSTLY)'));
  const slot = el('div', 'st-cprev'); me.append(slot);
  const pv = pvEl = pvEl || $('preview');
  if (pv) { slot.append(pv); const ids = Object.values(B.body.slots).map((x) => x.b); const look = G.settings.look || {}; showCharacter((c, l) => implantLook(buildCharacter(c, l), ids, Object.keys(B.body.slots).length > B.budget), G.myColor || '#ff4fd8', look); setTimeout(resizePreview, 0); }
  cols.append(me);
  // body slots
  const body = el('div', 'st-cbody');
  body.append(el('b', 'st-lbl', 'YOUR BODY'));
  for (const s of BODY_SLOTS) {
    const x = B.body.slots[s], row = el('div', 'st-crow' + (x ? ' full' : ''));
    row.append(el('span', 'st-cslot', s.toUpperCase()), el('span', null, x ? IMPLANTS[x.b].name + (x.ql ? ` (${x.ql})` : '') : '—'));
    if (x) { const b = el('button', 'st-btn small', `TAKE OUT · ${UNINSTALL_FEE}`); b.addEventListener('click', () => story.send('clinic', { op: 'uninstall', slot: s })); row.append(b); row.title = `${IMPLANTS[x.b].perk}\ndownside: ${IMPLANTS[x.b].downside}`; }
    body.append(row);
  }
  cols.append(body);
  // what's in your bag, and what's for sale
  const shop = el('div', 'st-cshop');
  shop.append(el('b', 'st-lbl', 'IN YOUR BAG'));
  const mine = inv.bag.filter((it) => it && IMPLANTS[it.b]);
  if (!mine.length) shop.append(el('div', 'st-sub', 'no spare organs. buy one, or take one off a boss.'));
  for (const it of mine) shop.append(implantRow(it.b, it.ql, el('button', 'st-btn yellow small', 'INSTALL'), () => story.send('clinic', { op: 'install', u: it.u })));
  shop.append(el('b', 'st-lbl', `FOR SALE · you have ☺ ${B.coupons.toLocaleString('en')}`));
  for (const [id, I] of Object.entries(IMPLANTS)) if (I.kind === 'shop') shop.append(implantRow(id, null, el('button', 'st-btn small', `BUY · ${I.cost}`), () => story.send('clinic', { op: 'buy', id })));
  cols.append(shop);
  panel.append(cols);
  clinic.append(panel);
}
function implantRow(id, ql, btn, fn) {
  const I = IMPLANTS[id], row = el('div', 'st-crow');
  row.append(el('span', 'st-cslot', I.slot.toUpperCase()), el('span', 'st-cname2', I.name + (ql ? ` (${ql})` : '')), btn);
  btn.addEventListener('click', fn);
  row.title = `${I.text}\nperk: ${I.perk}\ndownside: ${I.downside}`;
  row.addEventListener('mouseenter', () => { const i = clinic.querySelector('.st-info'); if (i) i.textContent = `${I.name}: ${I.perk}. downside: ${I.downside}.`; });
  return row;
}

// ------------------------------------------------------------ what implants look like on the mannequin
// chunky low-poly bits on the code mannequin (models.js buildCharacter's parts). the slice's four get their own look;
// anything else is a pink lump where it lives. over budget the body lumps and twitches
const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.35, metalness: o.metal || 0, emissive: o.em || 0x000000, emissiveIntensity: o.em ? 0.5 : 0 });
const SLOT_AT = { head: [0, 1.78, 0], eyes: [0, 1.66, -0.12], mouth: [0, 1.56, -0.12], heart: [0.07, 1.36, -0.14], lungs: [-0.08, 1.36, -0.13], guts: [0, 1.12, -0.13], spine: [0, 1.25, 0.14], arms: [0.3, 1.3, 0], legs: [0.1, 0.5, -0.05], skin: [0, 1.0, 0.13] };
export function implantLook(ch, ids, over) {
  const g = new THREE.Group(); g.name = 'implants';
  for (const id of ids) {
    if (id === 'pigeon_eyes') {
      for (const [x, back] of [[-0.05, false], [0.05, true]]) {
        const eye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 10, 8), M(0xff8a1a));
        const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), M(0x111111));
        pupil.position.z = back ? 0.04 : -0.04; eye.add(pupil);
        eye.position.set(x, 1.67, back ? 0.1 : -0.11); g.add(eye); // one looks backwards
      }
    } else if (id === 'spring_knees') {
      for (const k of [ch.kneeL, ch.kneeR]) {
        if (!k) continue;
        for (let i = 0; i < 4; i++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.012, 6, 12), M(0xdddddd, { metal: 0.9 })); ring.rotation.x = Math.PI / 2; ring.position.y = 0.06 - i * 0.03; k.add(ring); }
      }
    } else if (id === 'core_second_stomach') {
      const frame = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.17, 0.02), M(0x333333, { metal: 0.6 })); frame.position.set(0, 1.12, -0.135); g.add(frame);
      const glass = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.13, 0.022), new THREE.MeshStandardMaterial({ color: 0x99ddff, transparent: true, opacity: 0.35, roughness: 0.05 })); glass.position.set(0, 1.12, -0.14); g.add(glass);
      const tum = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 8), M(0xff6fae, { em: 0x501030 })); tum.scale.set(1.2, 0.9, 0.6); tum.position.set(0, 1.12, -0.12); g.add(tum);
    } else if (id === 'core_cracked_punch_clock') {
      const face = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.025, 16), M(0xffffff)); face.rotation.x = Math.PI / 2; face.position.set(0.04, 1.37, -0.14); g.add(face);
      for (const [l, a] of [[0.06, 0.4], [0.045, 2.2]]) { const h = new THREE.Mesh(new THREE.BoxGeometry(0.008, l, 0.006), M(0x111111)); h.position.set(0.04 + Math.sin(a) * l / 2, 1.37 + Math.cos(a) * l / 2, -0.155); h.rotation.z = -a; g.add(h); }
      const crack = new THREE.Mesh(new THREE.BoxGeometry(0.005, 0.12, 0.004), M(0xff3030)); crack.position.set(0.02, 1.38, -0.156); crack.rotation.z = 0.5; g.add(crack);
      g.userData.clock = face;
    } else if (IMPLANTS[id]) {
      const at = SLOT_AT[IMPLANTS[id].slot] || [0, 1.2, -0.13];
      const lump = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 6), M(0xff4fd8, { em: 0x400020 })); lump.position.set(...at); g.add(lump);
    }
  }
  if (over) for (let i = 0; i < 5; i++) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.03 + Math.random() * 0.03, 6, 5), M(0xd9668f)); l.position.set((Math.random() - 0.5) * 0.35, 0.9 + Math.random() * 0.7, (Math.random() - 0.5) * 0.3); g.add(l); } // rejection lumps
  ch.body.add(g);
  return ch;
}
export const BODY_CSS = `
.st-hype{position:fixed;left:20px;bottom:58px;z-index:15;display:flex;gap:10px;align-items:center;font-family:var(--font);pointer-events:none}
.st-hype.hidden,.st-clinicwrap.hidden{display:none}
.st-hbar{position:relative;width:200px;height:22px;background:rgba(18,8,24,.85);border:3px solid #000;box-shadow:3px 3px 0 #4fd8ff;transform:rotate(-1deg)}
.st-hbar i{position:absolute;left:0;top:0;bottom:0;background:#ff00dc}.st-hbar b{position:relative;padding-left:6px;color:#fff;font-size:14px;line-height:22px;text-shadow:1px 1px 0 #000}
.st-coupons{background:#ffe14d;color:#000;font-weight:700;border:3px solid #000;box-shadow:3px 3px 0 #ff4fd8;padding:1px 8px;transform:rotate(1.5deg)}
.st-drift{background:#2a1030;color:#ff4fd8;border:2px solid #ff4fd8;padding:1px 6px;font-weight:700}
.st-clinic{width:min(1120px,97vw);transform:rotate(-.4deg)}
.st-ccols{display:grid;grid-template-columns:260px 300px 1fr;gap:14px}
.st-cprev{width:250px;height:300px;border:3px solid #000;background:#1a0a20;box-shadow:4px 4px 0 #ff4fd8}.st-cprev canvas{width:100%!important;height:100%!important}
.st-crow{display:flex;gap:8px;align-items:center;padding:3px 0;border-bottom:1px dashed rgba(255,79,216,.35);font-size:14px}
.st-crow.full span:nth-child(2){color:#ff4fd8;font-weight:700}
.st-cslot{color:#4fd8ff;width:56px;font-size:12px;font-weight:700}.st-cname2{flex:1}
.st-cshop{max-height:62vh;overflow:auto}
.st-btn.small{font-size:13px;padding:2px 8px;margin-left:auto}
`;
