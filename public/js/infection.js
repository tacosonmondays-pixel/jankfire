// Infection on your screen: green zombies (tinted mannequins that groan), survivors left, the clock,
// the green haze while you're one of them, and the big YOU ARE INFECTED moment.
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { ME } from './player.js';
import { INFECT } from '/shared/modes.js';
import { modeFriends } from './weapons.js';
import { serverNow } from './replay.js';

const $ = (id) => document.getElementById(id);
G.infected = new Set(); // ids of everyone who's a zombie right now
G.zombie = false; // am I?
G.infOn = false; // is an infection match running (your own side is see-through for your shots)
G.infT = new Map(); // id -> server time they turned (killcams draw them as zombies from then)
G.infSide = null; // who took the last match: 'inf' or 'surv'
modeFriends.push((r) => G.infOn && !!r.zombie === !!G.zombie);
const nameOf = (id) => (id === G.myId ? G.myName : (G.names.get(id) || {}).name || '???');
const fmt = (ms) => { const s = Math.ceil(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };

// the big moment: green flash, huge wobbly text, a groan and a sting
// the banner + flash are one-shot CSS animations: take the class off when they finish, or pausing (the HUD is hidden
// while the menu is up) and resuming replays them and tells you you're infected again
for (const [id, cls] of [['infBig', 'go'], ['infFx', 'flash']]) {
  const el = $(id);
  if (el) el.addEventListener('animationend', () => el.classList.remove(cls));
}
function bigMoment(title, sub) {
  const el = $('infBig');
  el.innerHTML = '';
  const b = document.createElement('b'); b.textContent = title;
  const s = document.createElement('span'); s.textContent = sub || '';
  el.append(b, s);
  el.classList.remove('go'); void el.offsetWidth; el.classList.add('go');
  const fx = $('infFx');
  fx.classList.remove('flash'); void fx.offsetWidth; fx.classList.add('flash');
  sfx.infected(); sfx.groan();
  G.shake = Math.max(G.shake || 0, 0.8);
}
// a zombie now: green in the kill feed too (the next match's team colours put it back). your own colour stays,
// it's also your menu preview
function turn(id, late) {
  G.infected.add(id);
  if (!G.infT.has(id)) G.infT.set(id, late ? 1 : serverNow());
  const n = G.names.get(id);
  if (n) n.color = INFECT.color;
  if (id === G.myId) G.zombie = true;
}

net.on('infect', (m) => {
  if (m.side) { G.infSide = m.side; return; } // the match is over: the 'round' message right after shows it
  if (m.all) {
    G.infected = new Set(); G.infT.clear();
    if (!m.all.length) G.infSide = null;
    const was = G.zombie;
    G.zombie = false;
    for (const id of m.all) turn(id, true);
    if (G.zombie && !was) bigMoment('YOU ARE INFECTED', 'you showed up late: you start as a zombie');
    return;
  }
  if (m.last) {
    const me = m.last === G.myId;
    hud.msg(me ? 'YOU ARE THE LAST SURVIVOR' : `${nameOf(m.last).toUpperCase()} IS THE LAST SURVIVOR`, 2.6, 'brag');
    hud.chat(null, null, me ? 'everyone else turned. hold on till the clock runs out' : `${nameOf(m.last)} is the last one left`);
    sfx.ting();
    return;
  }
  const name = nameOf(m.id);
  turn(m.id);
  if (m.id === G.myId) bigMoment('YOU ARE INFECTED', m.first ? 'patient zero: infect them all' : m.late ? 'you showed up late: you start as a zombie' : 'claw the survivors: two swipes each');
  else {
    if (m.first) hud.msg(`${name.toUpperCase()} IS PATIENT ZERO`, 2.4, 'brag');
    hud.chat(null, null, m.first ? `${name} is patient zero. run` : `${name} turned into a zombie`);
    const r = G.remotes.get(m.id);
    sfx.groan(r ? r.pos : null);
  }
});

export function updateInfection(dt) {
  const r = G.round;
  G.infOn = !!(G.joined && r && r.game === 'inf');
  document.body.classList.toggle('mode-inf', G.infOn);
  document.body.classList.toggle('zombie', G.infOn && G.zombie);
  for (const rm of G.remotes.values()) rm.setZombie(G.infOn && G.infected.has(rm.id));
  const bar = $('infBar');
  bar.classList.toggle('hidden', !G.infOn || r.over);
  if (!G.infOn) { if ($('infLine').textContent) $('infLine').textContent = ''; return; } // no stale numbers next time it shows
  // zombies moan now and then (only the ones near enough to matter)
  for (const rm of G.remotes.values()) {
    if (!rm.zombie || !rm.alive || Math.random() > dt * 0.16) continue;
    if (Math.hypot(rm.pos[0] - ME.pos[0], rm.pos[1] - ME.pos[1], rm.pos[2] - ME.pos[2]) < 45) sfx.groan(rm.pos);
  }
  if (r.over) return;
  const i = r.inf || { s: 0, z: 0, t0: 0 };
  const line = i.t0 > 0 ? `someone turns in ${Math.ceil(i.t0 / 1000)}... spread out`
    : G.zombie ? `YOU ARE A ZOMBIE · ${i.s} left to infect · ${fmt(r.left)}`
      : `SURVIVE ${fmt(r.left)} · ${i.s} survivor${i.s === 1 ? '' : 's'} · ${i.z} zombie${i.z === 1 ? '' : 's'}`;
  const el = $('infLine');
  if (el.textContent !== line) el.textContent = line;
  const k = i.s + i.z ? i.z / (i.s + i.z) : 0;
  const fill = $('infMeter').firstChild;
  const wv = Math.round(k * 100) + '%';
  if (fill.style.width !== wv) fill.style.width = wv;
}

export function infRoundText(r) {
  if (r.game !== 'inf' || r.over) return null;
  return 'infection'; // the clock is in the bar right under it
}
// end screen title: which side took it (and whether that's you)
export function infRoundTitle(m) {
  const side = m.side || G.infSide;
  if (m.game !== 'inf' || !side) return null;
  const mine = (side === 'inf') === G.zombie;
  return [`${side === 'inf' ? 'THE INFECTED WIN' : 'SURVIVORS WIN'}${mine ? ' (YOU)' : ''}`, side === 'inf' ? INFECT.color : '#ffffff'];
}
export function infRowNote(id, m) {
  if (m.game !== 'inf') return '';
  return (id === G.myId ? G.zombie : G.infected.has(id)) ? 'zombie' : 'survivor';
}
// TAB scores: survivors on top, zombies in green
export function infScoreRows(rows) {
  if (!G.infOn) return;
  const z = (r) => (r.me ? G.zombie : G.infected.has(r.id));
  rows.sort((a, b) => z(a) - z(b));
  for (const r of rows) if (z(r)) { r.color = INFECT.color; r.name += '  (zombie)'; }
}
// your killcam: who was already a zombie (replay.js draws them green)
export function infClipInfo(info) {
  if (!G.infOn) return;
  for (const id of Object.keys(info)) { const n = Number(id); if (G.infected.has(n) && info[id]) info[id].zs = G.infT.get(n) || 1; }
}
// zombie HP goes past 100: the HP number says so (the bar just stays full)
const hpBase = hud.hp;
hud.hp = function (v) {
  hpBase.call(this, v);
  const el = $('hptext');
  if (G.infOn && G.zombie && v > 100 && el.textContent.endsWith(' HP')) el.textContent = Math.ceil(v) + ' HP';
};
export function resetInfection() {
  G.infected.clear(); G.infT.clear(); G.zombie = false; G.infOn = false; G.infSide = null;
  $('infLine').textContent = ''; $('infMeter').firstChild.style.width = '0%';
  document.body.classList.remove('mode-inf', 'zombie');
  $('infBar').classList.add('hidden');
}
