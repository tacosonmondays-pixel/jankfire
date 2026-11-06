// Plant & Defuse economy, client side (wf_econ/DESIGN.md §12-14): the buy menu, credits / armor / kill pops / the
// round's money on the HUD, the hotbar and ammo from the server's inventory, gear on the floor (pick up, swap, drop),
// spawn barriers you can't walk through, sitting out and spectating a teammate, round banners. No grapple, no streaks.
// The rules and numbers are the server's (server/econ.js) and /shared/econ.js; this file only shows them and asks.
import { WEAPONS, ITEMS, SLOTS } from '/shared/weapons.js';
import { ECON, GEAR, SD, buyList, ammoSpec, refillPrice, gearPrice } from '/shared/econ.js';
import { TEAMS, BOMB } from '/shared/modes.js';
import { BOXES } from '/shared/map.js';
import { raycast, PH } from '/shared/physics.js';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { ME, eye, look } from './player.js';
import { W, setSlots, playVM, rebuildOne, setLoadout, refillAmmo, syncItem, setItem, showSlots } from './weapons.js';
import { weaponIcon, itemIcon, objIcon } from './icons.js';
import { RP } from './replay.js';
import * as E3 from './econ3d.js';
import { tacRound, tacSync } from './tactical.js';
import { K } from './keys.js';

// this mode's keys are actions in keys.js (rebindable in Settings > Key bindings): 'buy' (B: the buy menu here, the
// pause menu everywhere else), 'drop' (H; Shift + it drops your item), 'pause' (P, every mode: Esc pauses too).
// pick up / swap is the grapple's key, because tryHook() hands the press to us
const IDLE = ['slot4', 'streak1', 'streak2', 'streak3', 'dash', 'scythe']; // scythe slot, killstreaks, dash: nothing to use here
const pickKey = () => K.label('grapple').toUpperCase(); // the grapple button (keys.js)
const keyIs = (e, k) => K.matches(k, e);
export const ecoKeyLabel = (k) => K.label(k).toUpperCase();

const $ = (id) => document.getElementById(id);
const S = G.settings;
const now = () => performance.now();
const money = (n) => '$' + Math.round(n).toLocaleString('en-US');
const wname = (id) => (WEAPONS[id] ? WEAPONS[id].name : ITEMS[id] ? ITEMS[id].name : GEAR[id] ? GEAR[id].name : { tbag: 'T-Bag', hook: 'Grapple', bomb: 'the bomb', smokegren: 'Smoke Bomb' }[id] || id);
const WHY = { elim: 'team wiped', time: 'time ran out', defused: 'bomb defused', exploded: 'bomb exploded' };
const ENO = {
  money: 'not enough credits', zone: 'go back to your spawn to buy', phase: 'buy time is over', full: "you can't carry more",
  limit: "you can't carry more this round", side: 'defenders only', dead: "you're out this round", bad: "can't do that",
  used: "already used: it can't go back", nothing: 'nothing to sell', far: 'too far away', gone: 'someone got there first',
  cant: "you can't pick that up", empty: 'nothing to drop', nowhere: 'no room to drop it here',
};
const SLOT_NAME = ['PRIMARY', 'SECONDARY', 'MELEE'];
let cb = { pause() {}, lock() {} };

// ------------------------------------------------------------ on / off
export const ecoOn = () => !!G.eco;
function on() {
  if (G.eco) return G.eco;
  const e = G.eco = { skinKey: null, inv: null, round: null, money: new Map(), buyEnd: 0, menu: false, out: false, spec: 0, want: null, tossT: 0, pending: null, lastIc: null, rebuy: [], shown: 0, target: null, fresh: true, kills: [], hintT: 0, zonesDrawn: false };
  document.body.classList.add('eco');
  W.eco = HOOKS; W.res = {}; W.skinOver = {};
  W.item = null;
  G.noHook = pick;
  ammoKey = ''; slotKey = ''; gearKey = '';
  for (const id of ['ecoMoney', 'ecoArmor']) $(id).classList.remove('hidden');
  hud.chat(null, null, `Plant & Defuse: buy your gear in the buy phase (${ecoKeyLabel('buy')}) · ${ecoKeyLabel('drop')} drops what you hold (Shift: your item) · ${pickKey()} picks up / swaps · ${ecoKeyLabel('pause')} pauses · ${K.label('sprint').toUpperCase()} slow walks`);
  return e;
}
// the mode ended (inv {off:1}) or you left: back to your own loadout, skins and item
function off(restore) {
  const e = G.eco;
  if (!e) return;
  closeMenu(false);
  G.eco = null; G.noHook = null;
  W.eco = null; W.res = null; W.skinOver = null;
  document.body.classList.remove('eco', 'eco-spec', 'eco-buy');
  ammoKey = ''; $('ammo').style.display = 'none';
  E3.dropsClear(); E3.barriersClear();
  for (const r of G.remotes.values()) { r.setGear(0); r.tag.visible = true; }
  for (const id of ['ecoMoney', 'ecoArmor', 'ecoTimer', 'ecoSpec', 'ecoPrompt', 'ecoHint', 'ecoPay']) $(id).classList.add('hidden');
  if (restore) {
    setLoadout(S.loadout); refillAmmo(); rebuildOne();
    if (e.lastIc && ITEMS[e.lastIc.i]) { syncItem(e.lastIc.i, e.lastIc.n, e.lastIc.next); setItem(e.lastIc.i); showSlots(); }
  }
}

// ------------------------------------------------------------ hooks for weapons.js (W.eco)
const inst = (id) => { const e = G.eco; if (!e || !e.inv) return null; for (const s of SLOTS) { const x = e.inv.sl[s]; if (x && x.id === id) return x; } return null; };
const buying = () => !!(G.eco && G.eco.buyEnd && now() < G.eco.buyEnd);
const HOOKS = {
  // true = no shot: the buy phase, a weapon on its way out of your hand, or a counted weapon with nothing left
  dry(id, quiet) {
    const e = G.eco;
    if (!e) return false;
    if (now() < e.tossT) return true;
    if (buying()) { if (!quiet) hint(id === 'item' ? 'no items in the buy phase' : 'no shooting in the buy phase', 1.2); return true; }
    if (id === 'item') return false;
    const x = inst(id);
    if (!x || !x.lim || x.cl) return false; // unlimited, or a magazine gun (its empty click + reload path handles it)
    if ((W.ammo[id] || 0) > 0) return false;
    if (!quiet) { sfx.empty(); outOfAmmo(id); }
    return true;
  },
  canReload(id) { if ((W.res[id] || 0) > 0) return true; outOfAmmo(id); return false; },
  reloading(id) { net.send({ t: 'rl', w: id }); },
  reloaded(id) { const w = WEAPONS[id], mv = Math.min(w.mag - (W.ammo[id] || 0), W.res[id] || 0); W.ammo[id] = (W.ammo[id] || 0) + mv; W.res[id] = (W.res[id] || 0) - mv; },
  hud(id, reloading) { ammoHud(id, reloading); },
};
// counted weapons (bow, launchers, cards, snowballs) spend a shot when a fire message leaves: mirror it here
const send0 = net.send.bind(net);
net.send = (o) => {
  if (G.eco && o && o.t === 'fire') { const x = inst(o.w); if (x && x.lim && !x.cl && o.ch == null) W.ammo[o.w] = Math.max(0, (W.ammo[o.w] || 0) - 1); }
  if (G.eco && o && o.t === 'lasso' && o.k === 'throw') { const x = inst('lasso'); if (x && x.lim) W.ammo.lasso = Math.max(0, (W.ammo.lasso || 0) - 1); } // a lasso throw spends one too
  return send0(o);
};

// ------------------------------------------------------------ the inventory (authoritative)
function onInv(m) {
  if (m.off) { off(true); return; }
  const e = on(), prev = e.inv, t = now();
  const want = e.want && t - e.want.t < 2500 ? e.want : null;
  e.inv = m;
  // ammo and the skin of whoever bought each one
  const sk = {};
  for (const s of SLOTS) { const x = m.sl[s]; if (!x) continue; if (x.lim) { W.ammo[x.id] = x.m; W.res[x.id] = x.r; } if (Array.isArray(x.sk)) sk[x.id] = x.sk; }
  const skk = JSON.stringify(sk);
  if (skk !== e.skinKey) { e.skinKey = skk; W.skinOver = sk; rebuildOne(); } // the first one always: the viewmodels were dressed in your menu skins
  // G = the item you bought (hidden when you have none)
  W.item = m.it && ITEMS[m.it.id] ? m.it.id : null;
  if (W.item) syncItem(W.item, m.it.n, 0);
  // what's in each slot, and what goes in your hands
  const ids = SLOTS.map((s) => (m.sl[s] ? m.sl[s].id : null));
  let hold = null, anim = null;
  for (let i = 0; i < 3 && prev && !e.fresh; i++) {
    const x = m.sl[SLOTS[i]], px = prev.sl[SLOTS[i]];
    if (!x || (px && px.u === x.u)) continue;
    if (want && want.k === 'buy' && want.kind === 'w' && want.id === x.id) { hold = i; anim = 'econ_buy'; sfx.cash(); }
    else if (want && want.k === 'pick' && want.u === x.u) { hold = i; anim = 'econ_grab'; sfx.click(); sfx.thunk(); }
    else if (!x.def) { sfx.click(); flashSlot(i); } // walked over it into an empty slot: it's yours, no switch
  }
  if (prev && !e.fresh && want && want.k === 'buy' && want.kind === 'w' && hold == null) { // a refill: same gun, full again
    const x = m.sl[WEAPONS[want.id] ? WEAPONS[want.id].slot : ''], px = x && prev.sl[WEAPONS[want.id].slot];
    if (x && px && x.u === px.u && x.m + x.r > px.m + px.r) { sfx.reload(); sfx.cash(); }
  }
  if (prev && !e.fresh && want && want.k === 'buy' && want.kind !== 'w') {
    if (want.kind === 'g' && (m.ar > prev.ar || m.hm > prev.hm || m.kit > prev.kit)) { playVM('econ_strap', 'draw'); sfx.crunch(); setTimeout(() => sfx.crunch(), 140); }
    else if (want.kind === 'i') { sfx.click(); flashSlot('item'); }
  }
  if (prev && !e.fresh && want && want.k === 'pick' && !anim && (m.kit > prev.kit || (m.it && (!prev.it || m.it.n !== prev.it.n || m.it.id !== prev.it.id)))) { sfx.click(); sfx.thunk(); flashSlot(m.kit > prev.kit ? null : 'item'); }
  if (prev && m.$ > prev.$ && want && want.k === 'sell') sfx.pop();
  if (e.fresh || !ids.includes(W.cur) || (hold == null && ids[W.slot] !== W.cur)) hold = hold ?? [0, 1, 2].find((i) => ids[i]);
  e.fresh = false;
  if (t < e.tossT) e.pending = [ids, hold, anim]; // the old one is still flying out of your hand
  else { e.pending = null; setSlots(ids, hold, anim); }
  // sitting this round out (joined after the buy phase)
  if (m.out && !e.out) sitOut();
  if (!m.out) e.out = false;
  if (!e.zonesDrawn && m.zone && buying()) { e.zonesDrawn = true; E3.barriersSet([{ z: m.zone, team: G.myTeam }]); } // no team zones on this map: yours
  armorHud();
  if (e.menu) renderMenu();
}
function flashSlot(i) {
  const el = i === 'item' ? $('itemSlot') : $('slot-' + i);
  if (!el) return;
  el.classList.remove('eco-got'); void el.offsetWidth; el.classList.add('eco-got');
}

// ------------------------------------------------------------ ammo on the HUD
function ammoHud(id, reloading) {
  const a = $('ammo'), x = inst(id);
  let key = '', html = '', col = '#fff';
  if (x && x.lim) {
    const m = W.ammo[id] || 0, r = W.res[id] || 0, mag = WEAPONS[id].mag || 0;
    if (x.cl) { html = reloading ? `<b>…</b><small> / ${r}</small>` : `<b>${m}</b><small> / ${r}</small>`; col = m === 0 ? (r ? '#ffe14d' : '#ff5050') : m <= mag * 0.25 ? '#ffe14d' : '#fff'; }
    else { html = `<b>${m}</b><small> left</small>`; col = m === 0 ? '#ff5050' : m <= 3 ? '#ffe14d' : '#fff'; }
    key = html + col;
  }
  if (key === ammoKey) return;
  ammoKey = key;
  if (!key) { a.style.display = 'none'; return; }
  a.style.display = 'block'; a.innerHTML = html; a.style.color = col;
}
// out of ammo means out: say so, and what to do about it
function outOfAmmo(id) {
  const e = G.eco;
  if (!e || now() - e.hintT < 900) return;
  const other = [0, 1, 2].filter((i) => W.slots[i] && W.slots[i] !== id).map((i) => [i, W.slots[i]]).find(([, w]) => { const x = inst(w); return !x || !x.lim || (W.ammo[w] || 0) > 0 || (W.res[w] || 0) > 0; });
  hint(other ? `OUT OF AMMO · ${other[0] + 1}: ${wname(other[1])} · or pick a gun up (${pickKey()})` : `OUT OF AMMO · pick a gun up (${pickKey()})`, 2.4);
}
function hint(text, secs) {
  const e = G.eco;
  if (!e) return;
  e.hintT = now();
  const el = $('ecoHint');
  el.textContent = text; el.classList.remove('hidden');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.add('hidden'), secs * 1000);
}
function toast(text) {
  const el = $('ecoToast');
  el.textContent = text; el.classList.remove('hidden', 'go'); void el.offsetWidth; el.classList.add('go');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.add('hidden'), 1800);
}

// ------------------------------------------------------------ credits, armor, pops, the round's money
function armorHud() {
  const e = G.eco, inv = e && e.inv;
  if (!inv) return;
  const el = $('ecoArmor');
  el.querySelector('b').textContent = String(inv.ar);
  el.querySelector('.bar i').style.width = inv.ar + '%';
  el.classList.toggle('none', inv.ar <= 0);
  el.classList.toggle('hm', !!inv.hm);
  el.classList.toggle('kit', !!inv.kit);
}
function pop(text, sub) {
  const box = $('ecoMoney').querySelector('.pops'), d = document.createElement('div');
  d.textContent = text;
  if (sub) { const s = document.createElement('small'); s.textContent = sub; d.append(s); }
  box.prepend(d);
  while (box.children.length > 4) box.lastChild.remove();
  setTimeout(() => d.remove(), 2600);
}
function payPanel(m) {
  const el = $('ecoPay');
  el.innerHTML = '';
  const row = (label, amt, cls) => { const d = document.createElement('div'); d.className = 'pl ' + (cls || ''); const a = document.createElement('span'); a.textContent = label; const b = document.createElement('b'); b.textContent = amt; d.append(a, b); el.append(d); };
  const h = document.createElement('div'); h.className = 'ph ' + (m.win ? 'win' : 'loss');
  h.innerHTML = `<b>${m.win ? 'ROUND WON' : 'ROUND LOST'}</b><span>${WHY[m.why] || ''}</span>`;
  el.append(h);
  for (const [k, a, x] of m.lines || []) {
    if (k === 'win') row('Round win', '+' + money(a));
    else if (k === 'loss') row(`Loss bonus ×${x}`, '+' + money(a));
    else if (k === 'nobonus') row('Survived a time loss: no bonus', money(0), 'dim');
    else if (k === 'plant') row('Bomb planted', '+' + money(a));
  }
  const kc = m.kills || [0, 0];
  if (kc[0]) row(`Kills ×${kc[0]} (paid as you got them)`, '+' + money(kc[1]), 'dim');
  const t = document.createElement('div'); t.className = 'pt';
  t.innerHTML = `<span>+${money(m.got)}${m.got < m.total ? ' (capped)' : ''}</span><b>${money(m.$)}</b>`;
  el.append(t);
  const next = ECON.loss[Math.min(m.streak || 0, ECON.loss.length - 1)];
  const nx = document.createElement('div'); nx.className = 'pn';
  nx.textContent = m.streak ? `${m.streak} loss${m.streak > 1 ? 'es' : ''} in a row · next loss pays ${money(next)}` : `next loss pays ${money(next)}`;
  el.append(nx);
  el.classList.remove('hidden', 'go'); void el.offsetWidth; el.classList.add('go');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.add('hidden'), 5200);
}
function banner(m) {
  const el = $('ecoBanner'), mine = G.myTeam === m.att, col = TEAMS[G.myTeam] ? TEAMS[G.myTeam].color : '#ffe14d';
  const b = G.round && G.round.bomb, wins = b && b.wins ? b.wins : [0, 0];
  const tags = [];
  if (m.half === 2 && m.pistol) tags.push(`HALF TIME · sides swapped · everyone back to ${money(m.start)}`);
  if (m.pistol) tags.push('PISTOL ROUND');
  if (m.n === BOMB.swapAfter) tags.push('LAST ROUND OF THE HALF');
  if (Math.max(...wins) >= BOMB.wins - 1) tags.push('MATCH POINT');
  el.innerHTML = `<div class="rs"><span class="r">ROUND ${m.n}</span><span class="s" style="color:${col}">${mine ? 'ATTACK' : 'DEFEND'}</span></div><div class="t">${[`BUY PHASE · ${ecoKeyLabel('buy')} to shop`, ...tags].map((x) => `<span>${x}</span>`).join('')}</div>`;
  el.classList.remove('hidden', 'go'); void el.offsetWidth; el.classList.add('go');
  clearTimeout(el._t); el._t = setTimeout(() => el.classList.add('hidden'), 3600);
}

// ------------------------------------------------------------ net
function initNet() {
  net.on('inv', onInv);
  net.on('eround', (m) => {
    const e = on();
    tacRound(m.n); // this round's shot seed, shot count from 0
    e.round = m; e.buyEnd = now() + (m.buy || 0); e.fresh = true; e.out = false;
    const zs = [];
    if (m.zones && m.zones.att) zs.push({ z: m.zones.att, team: m.att });
    if (m.zones && m.zones.def) zs.push({ z: m.zones.def, team: 3 - m.att });
    e.zonesDrawn = zs.length > 0;
    if (m.buy > 0) { E3.barriersSet(zs); banner(m); sfx.ting(); } // a joiner after the buy phase gets the round, not the walls
    else E3.barriersClear();
  });
  net.on('elive', () => {
    const e = G.eco;
    if (!e) return;
    e.buyEnd = 0;
    e.rebuy = e.inv && Array.isArray(e.inv.sell) && e.inv.sell.length ? e.inv.sell.slice() : e.rebuy; // what you bought this time
    if (e.inv) e.inv.zone = null;
    closeMenu(true);
    E3.barriersDrop();
    $('ecoTimer').classList.add('hidden');
    if (ME.alive) { hud.msg('GO GO GO', 1.0, 'brag'); sfx.whoops(); sfx.thunk(); }
  });
  net.on('ezone', (m) => { if (Array.isArray(m.p) && m.p.length === 3 && ME.alive) { ME.pos = m.p.slice(); ME.vel[0] = 0; ME.vel[2] = 0; } });
  net.on('drs', (m) => { on(); E3.dropsClear(); for (const d of m.list || []) E3.dropAdd(d, null); });
  net.on('dr+', (m) => {
    on();
    if (E3.dropEntry(m.id)) { E3.dropUpdate(m); return; }
    const d = E3.dropAdd(m, throwFrom(m));
    d.onLand = (en, n) => sfx[n === 1 ? 'thunk' : 'click']([en.pos.x, en.pos.y, en.pos.z]);
  });
  net.on('drx', (m) => { E3.dropRemove(m.id, m.by); });
  net.on('drc', () => E3.dropsClear());
  net.on('ecash', (m) => {
    const e = G.eco;
    if (!e) return;
    if (e.inv) e.inv.$ = m.$;
    pop(`+${money(m.got)} ${m.why === 'kill' ? wname(m.w) : m.why === 'plant' ? 'BOMB PLANTED' : 'BOMB DEFUSED'}`, m.got < m.a ? `max ${money(ECON.max)}` : '');
    sfx.cash();
    if (e.menu) renderMenu();
  });
  net.on('epay', (m) => { const e = G.eco; if (!e) return; if (e.inv) e.inv.$ = m.$; payPanel(m); });
  net.on('emoney', (m) => { const e = G.eco; if (!e || !Array.isArray(m.m)) return; e.money = new Map(m.m); if (e.menu) renderTeam(); });
  net.on('ear', (m) => {
    const e = G.eco;
    if (!e || !e.inv) return;
    e.inv.ar = m.ar; e.inv.hm = m.hm;
    armorHud();
    const el = $('ecoArmor');
    el.classList.remove('hit'); void el.offsetWidth; el.classList.add('hit');
    if (m.a > 0) (m.hm ? sfx.ting : sfx.thwack)();
  });
  net.on('am', (m) => {
    const x = inst(m.w);
    if (!x || x.u !== m.u) return;
    x.m = m.m; x.r = m.r; W.ammo[m.w] = m.m; W.res[m.w] = m.r;
    if (m.q != null) tacSync(m.q); // the server's shot count (it refused one)
  });
  net.on('eno', (m) => { toast(ENO[m.why] || m.why || 'no'); sfx.error(); });
}
// where a new drop comes from: the hand of whoever put it down, or the body it fell off
function throwFrom(d) {
  const t = now();
  if (d.o === G.myId && ME.alive) { const e = eye(), l = look(); return [e[0] + l[0] * 0.5, e[1] - 0.35, e[2] + l[2] * 0.5]; }
  const r = d.o && G.remotes.get(d.o);
  if (r && r.alive) return r.muzzle();
  const e = G.eco, k = e && e.kills.find((k2) => t - k2.t < 1500 && Math.hypot(k2.p[0] - d.p[0], k2.p[2] - d.p[2]) < 2.5);
  if (k) return [k.p[0], k.p[1] + 1.3, k.p[2]];
  return null;
}

// ------------------------------------------------------------ pick up / drop
function pick() {
  const e = G.eco;
  if (!e || !ME.alive || e.out) return;
  const t = e.target;
  if (!t) return;
  net.send({ t: 'pick', id: t.d.id });
  e.want = { k: 'pick', id: t.d.id, u: t.d.u, t: now() };
}
function drop(item) {
  const e = G.eco;
  if (!e || !ME.alive || e.out || !e.inv) return;
  if (item) { if (e.inv.it) { net.send({ t: 'drop', s: 'item' }); sfx.swing(); } else toast('no item to drop'); return; }
  const slot = SLOTS[W.slot], x = e.inv.sl[slot];
  if (!x || x.def) { toast(`your ${wname(x ? x.id : ECON.defaultMelee)} stays with you`); return; }
  net.send({ t: 'drop', s: slot });
  e.tossT = now() + 260; // toss it, then the next one comes up
  playVM('econ_toss', 'toss');
  sfx.swing();
}
// the drop you'd pick up: the one under the crosshair, or the nearest within reach
function aimDrop() {
  const o = eye(), l = look();
  let best = null, ba = 0.5, near = null, nd = 1e9;
  for (const en of E3.dropList()) {
    const p = en.pos, dx = p.x - ME.pos[0], dz = p.z - ME.pos[2], h = Math.hypot(dx, dz);
    if (h > ECON.pickR - 0.05 || Math.abs(p.y - ME.pos[1]) > 2.3) continue;
    const vx = p.x - o[0], vy = p.y + 0.05 - o[1], vz = p.z - o[2], vl = Math.hypot(vx, vy, vz) || 1;
    const ang = Math.acos(Math.max(-1, Math.min(1, (vx * l[0] + vy * l[1] + vz * l[2]) / vl)));
    if (ang < ba && !raycast(o, [vx / vl, vy / vl, vz / vl], Math.max(0, vl - 0.25), BOXES)) { ba = ang; best = en; }
    if (h < nd) { nd = h; near = en; }
  }
  return best || near;
}
function promptText(en) {
  const e = G.eco, d = en.d, inv = e.inv;
  if (!inv) return '';
  const key = pickKey();
  if (d.k === 'w') {
    const x = WEAPONS[d.w];
    if (!x) return '';
    const ammo = d.lim ? (d.cl ? ` ${d.m}/${d.r}` : ` ${d.m} left`) : '';
    const by = d.by && d.by !== G.myName ? `${d.by}'s` : '';
    const info = [ammo.trim(), by].filter(Boolean).join(', ');
    const cur = inv.sl[x.slot];
    const sw = cur ? ` · ${cur.def ? 'replaces' : 'swaps'} your ${wname(cur.id)}` : '';
    return `${key}: pick up ${x.name}${info ? ` (${info})` : ''}${sw}`;
  }
  if (d.k === 'i') {
    const it = ITEMS[d.w], name = it ? it.name : d.w;
    const sw = inv.it && inv.it.id !== d.w ? ` · swaps your ${wname(inv.it.id)} x${inv.it.n}` : '';
    return `${key}: pick up ${name} x${d.n}${sw}`;
  }
  const att = G.round && G.round.bomb && G.round.bomb.att === G.myTeam;
  return att ? 'Defuse Pliers (defenders only)' : inv.kit ? 'Defuse Pliers (you have some)' : `${key}: pick up Defuse Pliers`;
}

// ------------------------------------------------------------ sitting out + spectating a teammate
function sitOut() {
  const e = G.eco;
  e.out = true;
  ME.alive = false;
  G.deadAt = now() - 10000;
  hud.dead(true, [['you joined mid-round: ', '#fff'], ['OUT UNTIL NEXT ROUND', '#ffe14d']]);
}
const specList = () => [...G.remotes.values()].filter((r) => r.alive && r.team && r.team === G.myTeam && r.buf.length && !(r.bot && r.name === 'Dummy'));
// the one you watch has no name tag in your face
function setSpec(id) {
  const e = G.eco, was = e.spec && G.remotes.get(e.spec);
  if (was) was.tag.visible = true;
  e.spec = id; e.camP = null;
  const r = id && G.remotes.get(id);
  if (r) r.tag.visible = false;
}
function nextSpec(dir) {
  const e = G.eco, list = specList();
  if (!list.length) { setSpec(0); return; }
  const i = list.findIndex((r) => r.id === e.spec);
  setSpec(list[(i + dir + list.length) % list.length].id);
  sfx.click();
}
function specTick(t) {
  const e = G.eco;
  const want = G.joined && !ME.alive && !RP.active && !G.killcamPending && (e.out || t - (G.deadAt || t) > 2600);
  document.body.classList.toggle('eco-spec', want);
  $('ecoSpec').classList.toggle('hidden', !want);
  if (!want) { if (e.spec) setSpec(0); return; }
  let r = e.spec && G.remotes.get(e.spec);
  if (!r || !r.alive) {
    if (r && !e.lostT) e.lostT = t;
    if (!r || t - e.lostT > 1100) { e.lostT = 0; nextSpec(1); r = e.spec && G.remotes.get(e.spec); }
  } else e.lostT = 0;
  const text = r ? `<b>OUT UNTIL NEXT ROUND</b> · watching <span style="color:${r.color}">${esc(r.name)}</span> · ${Math.max(0, Math.round(r.hp))} HP · <i>SPACE / CLICK: next</i>`
    : '<b>OUT UNTIL NEXT ROUND</b> · no teammates left standing';
  const el = $('ecoSpec');
  if (el._k !== text) { el._k = text; el.innerHTML = text; }
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// main.js frame, after the replay had its go: follow the teammate from behind their shoulder
export function econCam(cam, dt) {
  const e = G.eco;
  if (!e || !e.spec || ME.alive || RP.active) return false;
  const r = G.remotes.get(e.spec);
  if (!r) return false;
  const k = 1.2 * (r.distScale || 1), head = [r.pos[0], r.pos[1] + 1.95 * k, r.pos[2]];
  const cp = Math.cos(r.pitch), ld = [-Math.sin(r.yaw) * cp, Math.sin(r.pitch), -Math.cos(r.yaw) * cp], rt = [Math.cos(r.yaw), 0, -Math.sin(r.yaw)];
  const want = [head[0] - ld[0] * 3.1 + rt[0] * 0.6, head[1] - ld[1] * 3.1 + 0.55, head[2] - ld[2] * 3.1 + rt[2] * 0.6];
  const dv = [want[0] - head[0], want[1] - head[1], want[2] - head[2]], dl = Math.hypot(...dv) || 1;
  const hit = raycast(head, dv.map((v) => v / dl), dl, BOXES);
  const s = hit ? Math.max(0.3, hit.t - 0.25) / dl : 1;
  const tgt = [head[0] + dv[0] * s, head[1] + dv[1] * s, head[2] + dv[2] * s];
  if (!e.camP) e.camP = tgt.slice();
  for (let i = 0; i < 3; i++) e.camP[i] += (tgt[i] - e.camP[i]) * Math.min(1, dt * 9);
  cam.position.set(e.camP[0], e.camP[1], e.camP[2]);
  cam.lookAt(head[0] + ld[0] * 10, head[1] + ld[1] * 10, head[2] + ld[2] * 10);
  return true;
}
export const econHideVM = () => !!(G.eco && !ME.alive); // out this round: no weapon in your face (spectating or not)

// ------------------------------------------------------------ the buy menu
// Search & Destroy columns: sidearms, smgs, shotguns, rifles, snipers + heavy, utility, armour (shared/econ.js SD.cats)
const COLS = SD.cats.map(([cat, label]) => [cat, label]);
let LIST = null, qcol = -1, built = false;
const lists = () => LIST || (LIST = COLS.map(([cat]) => buyList().filter((x) => x.cat === cat)));
const iconCache = new Map();
let ammoKey = '', gearKey = '', gearMap = new Map(), slotKey = '';
function iconFor(it) {
  const team = G.myTeam || 1, key = it.k + it.id + (it.k === 'w' ? JSON.stringify((G.equipped || {})[it.id] || '') : it.k === 'g' ? team : '');
  if (iconCache.has(key)) return iconCache.get(key);
  let url = '';
  if (it.k === 'w') url = weaponIcon(it.id, (G.equipped || {})[it.id]);
  else if (it.k === 'i') url = itemIcon(it.id);
  else url = objIcon('gear:' + it.id + team, () => E3.gearModel(it.id, team));
  iconCache.set(key, url);
  return url;
}
function buildMenu() {
  const root = $('ecoBuy');
  root.innerHTML = `<div class="eb"><div class="eb-top"><div class="eb-money"><small>CREDITS</small><b></b></div><div class="eb-mid"><div class="eb-timer"></div><div class="eb-status"></div></div><div class="eb-team"></div></div><div class="eb-cols"></div><div class="eb-foot"><span class="eb-help"></span><button class="eb-rebuy">REBUY</button><button class="eb-close">CLOSE (${ecoKeyLabel('buy')})</button></div></div>`;
  const cols = root.querySelector('.eb-cols');
  cols.style.gridTemplateColumns = `repeat(${COLS.length}, minmax(0, 1fr))`; cols.classList.add('eb-sd');
  lists().forEach((items, c) => {
    const col = document.createElement('div'); col.className = 'eb-col'; col.dataset.c = c;
    const h = document.createElement('div'); h.className = 'eb-h'; h.innerHTML = `<b>${c + 1}</b>${COLS[c][1]}`;
    h.addEventListener('click', () => { qcol = qcol === c ? -1 : c; renderMenu(); });
    const list = document.createElement('div'); list.className = 'eb-list';
    items.forEach((it, i) => {
      const card = document.createElement('div'); card.className = 'eb-card';
      const color = it.k === 'w' ? WEAPONS[it.id].color : it.k === 'i' ? ITEMS[it.id].color || '#9ab04a' : '#c8a46a';
      card.style.setProperty('--c', color);
      const sub = it.k === 'i' && it.id === 'nvg' ? `the flash · max ${it.limit}` : it.k === 'w' ? `kill +${money(it.kill)} · ${it.ammo ? (it.ammo.clip ? `${it.ammo.mag}+${it.ammo.res}` : `${it.ammo.mag} shots`) : '∞'}` : it.k === 'i' ? `max ${it.limit}` : GEAR[it.id].def ? 'defenders only' : it.id === 'vest' ? '100 armor' : 'vest + headshots';
      card.innerHTML = `<b class="eb-key">${(i + 1) % 10}</b><img alt=""><div class="eb-name"></div><div class="eb-sub"></div><div class="eb-price"></div><div class="eb-tag"></div><button class="eb-sell" title="sell it back (right click)">SELL</button>`;
      card.querySelector('.eb-name').textContent = it.name;
      card.querySelector('.eb-sub').textContent = sub;
      card.addEventListener('click', (ev) => { if (ev.target.classList.contains('eb-sell')) sellIt(it); else buyIt(it); });
      card.addEventListener('contextmenu', (ev) => { ev.preventDefault(); sellIt(it); });
      card.addEventListener('mouseenter', () => { const d = it.k === 'w' ? WEAPONS[it.id].desc : it.k === 'i' ? ITEMS[it.id].desc : GEAR[it.id].desc; const st = G.eco && G.eco.inv ? cardState(it, G.eco.inv) : {}; root.querySelector('.eb-help').textContent = `${it.name}: ${d}${st.note ? ' · ' + st.note : ''}`; });
      card.addEventListener('mouseleave', () => helpText());
      it.el = card;
      list.append(card);
    });
    col.append(h, list);
    cols.append(col);
  });
  root.querySelector('.eb-rebuy').addEventListener('click', rebuy);
  root.querySelector('.eb-close').addEventListener('click', () => closeMenu(true));
  root.addEventListener('mousedown', (ev) => ev.stopPropagation());
  built = true;
}
// the icons are rendered a few at a time so opening the menu the first time doesn't hitch
function warmIcons() {
  const team = G.myTeam || 1;
  for (const it of lists().flat()) if (it.k === 'g' && it.iconTeam !== team) { it.iconUrl = ''; it.iconTeam = team; } // the trim is your team's colour
  const todo = lists().flat().filter((it) => !it.iconUrl);
  let i = 0;
  const step = () => {
    for (let n = 0; n < 3 && i < todo.length; n++, i++) { const it = todo[i]; it.iconUrl = iconFor(it); if (it.el) it.el.querySelector('img').src = it.iconUrl; }
    if (i < todo.length) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
function helpText() {
  const el = $('ecoBuy').querySelector('.eb-help');
  if (el) el.textContent = qcol >= 0 ? `${COLS[qcol][1]}: press 1-${Math.min(9, lists()[qcol].length)}${lists()[qcol].length > 9 ? ' or 0' : ''} to buy · BACKSPACE back` : `CLICK buy · RIGHT CLICK sell back · keys: 1-${COLS.length} then a number · ${ecoKeyLabel('buy')} / ESC close`;
}
// why you can't buy right now (null = you can)
function cantBuy() {
  const e = G.eco;
  if (!buying()) return 'buy time is over';
  if (!ME.alive || e.out) return "you're out this round: buy next round";
  const z = e.inv && e.inv.zone, p = ME.pos, s = ECON.zoneSlack;
  if (z && (p[0] < z.min[0] - s || p[0] > z.max[0] + s || p[2] < z.min[2] - s || p[2] > z.max[2] + s)) return 'go back to your spawn to buy';
  return null;
}
const side = () => (G.round && G.round.bomb && G.round.bomb.att === G.myTeam ? 'att' : 'def');
// what a card says and whether it can be bought: price, owned / refill / full / limit / side
function cardState(it, inv) {
  const $$ = inv.$, out = { price: it.price, tag: '', cls: '' };
  if (it.k === 'w') {
    const cur = inv.sl[WEAPONS[it.id].slot];
    if (cur && cur.id === it.id) {
      const a = ammoSpec(it.id);
      if (!a || (cur.m >= a.mag && cur.r >= a.res)) return { price: null, tag: 'OWNED', cls: 'owned full', block: a ? "it's full already" : 'you have it', note: a ? 'full of ammo' : '' };
      const rp = refillPrice(it.id);
      return { price: rp, tag: 'REFILL', cls: 'owned' + (rp > $$ ? ' poor' : ''), block: rp > $$ ? 'not enough credits' : '', note: `you have it: buying it again refills its ammo for ${money(rp)}` };
    }
    if (cur && !cur.def) out.note = `buying it drops your ${wname(cur.id)} at your feet`;
  } else if (it.k === 'i') {
    const have = inv.it && inv.it.id === it.id ? inv.it.n : 0, got = (inv.ib || {})[it.id] || 0;
    out.tag = `${have}/${it.limit}`;
    if (have >= it.limit) return { price: null, tag: `${have}/${it.limit} FULL`, cls: 'owned full', block: "you can't carry more" };
    if (got >= it.limit) return { price: it.price, tag: 'LIMIT', cls: 'limit', block: "you can't carry more this round", note: `${it.limit} a round at most` };
    if (inv.it && inv.it.id !== it.id && inv.it.n > 0) out.note = `one item type at a time: buying it drops your ${wname(inv.it.id)} x${inv.it.n}`;
  } else {
    if (GEAR[it.id].def && side() === 'att') return { price: it.price, tag: 'DEF ONLY', cls: 'side', block: 'defenders only' };
    const p = gearPrice(it.id, inv.ar, inv.hm, inv.kit);
    if (p == null) return { price: null, tag: it.id === 'kit' ? 'OWNED' : 'FULL', cls: 'owned full', block: it.id === 'kit' ? 'you have pliers' : 'your armor is full' };
    out.price = p;
    if (it.id === 'helm' && inv.ar >= 100) { out.tag = '+BUCKET'; out.note = 'your vest is full: just the bucket'; }
    else if (inv.ar > 0 && inv.ar < 100) { out.tag = 'REFILL'; out.note = `tops your vest up from ${inv.ar} to 100`; }
  }
  if (out.price > $$) { out.cls += ' poor'; out.block = 'not enough credits'; }
  return out;
}
const sellable = (it, inv) => (inv.sell || []).some(([k, id]) => k === it.k && id === it.id);
function buyIt(it) {
  const e = G.eco;
  if (!e || !e.inv) return;
  const why = cantBuy() || cardState(it, e.inv).block;
  if (why) { toast(why); sfx.error(); return; }
  net.send({ t: 'buy', k: it.k, id: it.id });
  e.want = { k: 'buy', kind: it.k, id: it.id, t: now() };
}
function sellIt(it) {
  const e = G.eco;
  if (!e || !e.inv) return;
  if (!sellable(it, e.inv)) { toast('only what you bought this buy phase (and haven\'t used) sells back'); return; }
  const why = cantBuy();
  if (why) { toast(why); sfx.error(); return; }
  net.send({ t: 'sell', k: it.k, id: it.id });
  e.want = { k: 'sell', kind: it.k, id: it.id, t: now() };
}
// buy again what you bought last time (that you don't have)
function rebuy() {
  const e = G.eco;
  if (!e || !e.inv || !e.rebuy.length) { toast('nothing to rebuy yet'); return; }
  const why = cantBuy();
  if (why) { toast(why); sfx.error(); return; }
  const all = lists().flat();
  let n = 0;
  for (const [k, id] of e.rebuy) {
    const it = all.find((x) => x.k === k && x.id === id);
    if (!it || cardState(it, e.inv).block) continue;
    net.send({ t: 'buy', k, id }); n++;
    e.want = { k: 'buy', kind: k, id, t: now() };
  }
  if (!n) toast('you already have all of it');
}
function renderTeam() {
  const e = G.eco, el = $('ecoBuy').querySelector('.eb-team');
  if (!el || !e) return;
  const rows = [];
  for (const [id, m] of e.money) {
    if (id === G.myId) continue;
    const n = G.names.get(id);
    rows.push(`<span><i style="color:${n ? n.color : '#fff'}">${esc(n ? n.name : '???')}</i> ${money(m)}</span>`);
  }
  el.innerHTML = rows.length ? `<small>TEAM</small>${rows.join('')}` : '';
}
function renderMenu() {
  const e = G.eco;
  if (!e || !e.inv || !built) return;
  const inv = e.inv, root = $('ecoBuy');
  root.querySelector('.eb-money b').textContent = money(inv.$);
  const why = cantBuy();
  root.querySelector('.eb-status').textContent = why || `you can buy · loss bonus next: ${money(ECON.loss[Math.min((e.round && e.round.lose ? e.round.lose[(G.myTeam || 1) - 1] : 0), ECON.loss.length - 1)])}`;
  root.classList.toggle('closed', !!why);
  root.querySelector('.eb-rebuy').disabled = !e.rebuy.length;
  root.querySelectorAll('.eb-col').forEach((c, i) => c.classList.toggle('sel', i === qcol));
  for (const it of lists().flat()) {
    const el = it.el, st = cardState(it, inv);
    el.className = 'eb-card ' + st.cls + (sellable(it, inv) ? ' sell' : '') + (st.tag ? ' tagged' : '');
    el.querySelector('.eb-price').textContent = st.price != null ? money(st.price) : '';
    el.querySelector('.eb-tag').textContent = st.tag;
  }
  helpText();
  renderTeam();
}
function menuTick(t) {
  const e = G.eco, root = $('ecoBuy');
  const left = e.buyEnd ? Math.max(0, e.buyEnd - t) : 0, s = Math.ceil(left / 1000);
  const txt = left > 0 ? `BUY PHASE 0:${String(s).padStart(2, '0')}` : 'BUY TIME IS OVER';
  const tm = root.querySelector('.eb-timer');
  if (tm && tm.textContent !== txt) { tm.textContent = txt; tm.classList.toggle('low', left > 0 && s <= 5); renderMenu(); }
}
function openMenu() {
  const e = G.eco;
  if (!e || e.menu) return;
  if (!built) buildMenu();
  warmIcons();
  e.menu = true; qcol = -1;
  $('ecoBuy').classList.remove('hidden');
  document.body.classList.add('eco-buy');
  if (document.pointerLockElement) document.exitPointerLock(); // a real cursor for clicking (the pause menu stays shut)
  W.held = false; W.aimHeld = false;
  renderMenu();
  sfx.click();
}
function closeMenu(relock) {
  const e = G.eco;
  if (!e || !e.menu) return;
  e.menu = false; qcol = -1;
  $('ecoBuy').classList.add('hidden');
  document.body.classList.remove('eco-buy');
  if (relock && G.joined && $('menu').classList.contains('hidden')) cb.lock();
}
export const econMenuOpen = () => !!(G.eco && G.eco.menu);
function quickKey(n) {
  const L = lists();
  if (qcol < 0) { if (n >= 1 && n <= L.length) { qcol = n - 1; renderMenu(); sfx.click(); } return; }
  const it = L[qcol][(n + 9) % 10];
  if (it) { buyIt(it); qcol = -1; renderMenu(); }
}

// ------------------------------------------------------------ hooks for main.js
// keydown, after main.js's in-game check. true = it was ours
export function econKey(e) {
  if (keyIs(e, 'pause')) { if (!e.repeat) { closeMenu(false); cb.pause(); } return true; } // every mode
  const ec = G.eco;
  if (!ec) return false;
  if (ec.menu) {
    if (e.code === 'Escape' || keyIs(e, 'buy')) { if (!e.repeat) closeMenu(true); return true; }
    if (/^Digit\d$/.test(e.code)) { if (!e.repeat) quickKey(Number(e.code.slice(5))); return true; }
    if (e.code === 'Backspace') { qcol = -1; renderMenu(); return true; }
  }
  if (keyIs(e, 'buy')) { if (!e.repeat) openMenu(); return true; }
  if (keyIs(e, 'drop')) { if (!e.repeat) drop(e.shiftKey); return true; }
  if (IDLE.some((a) => K.matches(a, e))) return true;
  if (ec.spec && e.code === 'Space' && !RP.active && !G.killcamPending) { if (!e.repeat) nextSpec(1); return true; }
  return false;
}
// mousedown, after the killcam check: the menu has the mouse; a click while spectating watches the next teammate
export function econMouse(e) {
  const ec = G.eco;
  if (!ec) return false;
  if (ec.menu) return true;
  if (ec.spec && e.button === 0) { nextSpec(1); return true; }
  return false;
}
// welcome: a match with the economy already going
export function econWelcome(m) {
  if (m.round && m.round.eco) on();
  else if (G.eco) off(true);
}
export function econSpawn() {
  const e = G.eco;
  if (!e) return;
  e.out = false; setSpec(0); e.fresh = true;
  document.body.classList.remove('eco-spec');
  $('ecoSpec').classList.add('hidden');
}
// any kill: yours ends your round; the victim's gear is about to land around where they stood
export function econKill(m) {
  const e = G.eco;
  if (!e) return;
  const v = m.v === G.myId ? ME : G.remotes.get(m.v);
  if (v && v.pos) { e.kills.push({ t: now(), p: v.pos.slice() }); if (e.kills.length > 8) e.kills.shift(); }
  if (m.v === G.myId) { closeMenu(false); $('deadTimer').textContent = 'OUT UNTIL NEXT ROUND'; }
}
// the item charges: in this mode the inventory says (and the one sent at round start is stale). kept for when it ends
export function econIc(m) { const e = G.eco; if (!e) return false; e.lastIc = m; return true; }
// applyLoadout: the menu loadout waits for the mode to end (cosmetics still apply)
export function econLoadout() {
  if (!G.eco) return false;
  $('loNote').textContent = `Plant & Defuse: you buy your weapons (${ecoKeyLabel('buy')}). your loadout is back after the match`;
  return true;
}
// the dead screen's line (true = handled)
export function econDead() {
  const e = G.eco;
  if (!e) return false;
  if (!G.killcamPending) { const el = $('deadTimer'); const t = e.out ? 'OUT UNTIL NEXT ROUND · you can watch your team' : 'OUT UNTIL NEXT ROUND'; if (el.textContent !== t) el.textContent = t; }
  return true;
}
export function econReset() { off(true); }

// ------------------------------------------------------------ every frame (main.js, right after the movement steps)
export function econFrame(dt) {
  const e = G.eco;
  if (!e) return;
  const t = now(), left = e.buyEnd ? Math.max(0, e.buyEnd - t) : 0;
  if (e.pending && t >= e.tossT) { const p = e.pending; e.pending = null; setSlots(...p); }
  // the barrier: honest players never leave their zone during the buy phase (the server would put them back)
  const z = e.inv && e.inv.zone;
  if (left > 0 && z && ME.alive) {
    const p = ME.pos, v = ME.vel, m = PH.halfW + 0.03;
    if (p[0] > z.min[0] - 1 && p[0] < z.max[0] + 1 && p[2] > z.min[2] - 1 && p[2] < z.max[2] + 1) {
      if (p[0] < z.min[0] + m) { p[0] = z.min[0] + m; if (v[0] < 0) v[0] = 0; }
      if (p[0] > z.max[0] - m) { p[0] = z.max[0] - m; if (v[0] > 0) v[0] = 0; }
      if (p[2] < z.min[2] + m) { p[2] = z.min[2] + m; if (v[2] < 0) v[2] = 0; }
      if (p[2] > z.max[2] - m) { p[2] = z.max[2] - m; if (v[2] > 0) v[2] = 0; }
    }
  }
  E3.barriersTick(dt, t, left);
  // the floor: what you'd pick up glows, and says what it is
  e.target = ME.alive && !e.out && !e.menu ? aimDrop() : null;
  E3.dropsTick(dt, t, e.target ? e.target.d.id : 0);
  const pr = $('ecoPrompt'), ptxt = e.target ? promptText(e.target) : '';
  if (pr._k !== ptxt) { pr._k = ptxt; pr.textContent = ptxt; pr.classList.toggle('hidden', !ptxt); }
  // other people's armor, from the round info in every snapshot
  const g = G.round && G.round.eco && G.round.eco.gear, gk = g ? g.map((x) => x.join(':')).join(',') : '';
  if (gk !== gearKey) { gearKey = gk; gearMap = new Map(g || []); }
  for (const r of G.remotes.values()) if (r.alive && r.buf.length) r.setGear(gearMap.get(r.id) || 0);
  // the buy phase countdown
  const tm = $('ecoTimer');
  if (left > 0) {
    const s = Math.ceil(left / 1000), txt = `<b>BUY PHASE 0:${String(s).padStart(2, '0')}</b><span>barriers drop in ${s} · ${ecoKeyLabel('buy')}: buy menu</span>`;
    if (tm._k !== txt) { tm._k = txt; tm.innerHTML = txt; tm.classList.toggle('low', s <= 3); }
    tm.classList.remove('hidden');
  } else if (!tm.classList.contains('hidden')) tm.classList.add('hidden');
  if (e.menu) menuTick(t);
  // credits count up / down to the real number
  const real = e.inv ? e.inv.$ : 0;
  if (e.shown !== real) {
    e.shown += (real - e.shown) * Math.min(1, dt * 7);
    if (Math.abs(real - e.shown) < 6) e.shown = real;
    $('ecoMoney').querySelector('b').textContent = money(e.shown);
  }
  // ammo counts on the hotbar boxes
  const sk = W.slots.map((id) => { const x = id && inst(id); return x && x.lim ? (x.cl ? `${W.ammo[id] || 0}/${W.res[id] || 0}` : `${W.ammo[id] || 0}`) : ''; }).join('|');
  if (sk !== slotKey) {
    slotKey = sk;
    sk.split('|').forEach((a, i) => {
      const el = $('slot-' + i);
      if (!el) return;
      let b = el.querySelector('.am');
      if (!b) { b = document.createElement('span'); b.className = 'am'; el.append(b); }
      b.textContent = a; b.classList.toggle('dry', a === '0' || a === '0/0');
    });
  }
  specTick(t);
}

// ------------------------------------------------------------ hotbar + scoreboard additions
function wrapHud() {
  // empty primary / secondary boxes: their keys do nothing until you buy or pick one up
  const slots0 = hud.slots.bind(hud);
  hud.slots = (ids, icons) => {
    slots0(ids, icons);
    slotKey = '';
    if (!G.eco) return;
    const bar = $('weapons');
    ids.forEach((id, i) => {
      if (id || i > 2) return;
      const d = document.createElement('div'); d.className = 'hslot empty'; d.id = 'slot-' + i;
      d.innerHTML = `<span class="key">${i + 1}</span><span class="nm">${SLOT_NAME[i]}</span>`;
      const next = [...bar.children].find((c) => c.id === 'itemSlot' || (c.id.startsWith('slot-') && Number(c.id.slice(5)) > i));
      bar.insertBefore(d, next || null);
    });
  };
  // teammates' credits (and your own) on the scoreboard; the other team's stay secret
  const scores0 = hud.scores.bind(hud);
  hud.scores = (show, rows) => {
    scores0(show, rows);
    const e = G.eco, el = $('scores');
    el.classList.remove('eco');
    if (!show || !e || !rows) return;
    const kids = [...el.querySelectorAll('.srow')];
    if (kids.length !== rows.length + 1) return;
    el.classList.add('eco');
    kids[0].children[0].after(Object.assign(document.createElement('span'), { textContent: '$' }));
    rows.forEach((r, i) => {
      const id = r.me ? G.myId : r.id, mine = r.me || (id && G.remotes.get(id) && G.remotes.get(id).team === G.myTeam);
      const m = r.me ? (e.inv ? e.inv.$ : null) : mine ? e.money.get(id) : null;
      const s = document.createElement('span'); s.className = 'sm';
      s.textContent = id && m != null ? money(m) : '';
      if (r.me && e.inv) s.textContent += (e.inv.ar > 0 ? ' ⛨' : '') + (e.inv.hm ? '⛑' : '') + (e.inv.kit ? '✂' : '');
      kids[i + 1].children[0].after(s);
    });
  };
}

// HUD pieces (credits + armor live by the HP box, the rest float where they're needed)
function makeHud() {
  const h = $('hud');
  const el = (id, html, cls = 'hidden') => { const d = document.createElement('div'); d.id = id; d.className = cls; d.innerHTML = html || ''; h.append(d); return d; };
  el('ecoMoney', '<b>$0</b><div class="pops"></div>');
  el('ecoArmor', '<i class="ic vest"></i><b>0</b><div class="bar"><i></i></div><i class="ic helm" title="bucket"></i><i class="ic kit" title="defuse pliers"></i>');
  el('ecoTimer'); el('ecoBanner'); el('ecoPay'); el('ecoToast'); el('ecoPrompt'); el('ecoHint'); el('ecoSpec');
  el('ecoBuy');
  const icon = (draw) => { const c = document.createElement('canvas'); c.width = c.height = 16; const x = c.getContext('2d'); draw(x); return `url(${c.toDataURL()})`; };
  const px = (x, col, r) => { x.fillStyle = col; for (const [a, b, w, hh] of r) x.fillRect(a, b, w, hh); };
  const set = (sel, url) => { for (const n of document.querySelectorAll('#ecoArmor .ic.' + sel)) n.style.backgroundImage = url; };
  set('vest', icon((x) => { px(x, '#000', [[2, 1, 12, 14]]); px(x, '#b8955e', [[3, 2, 3, 12], [10, 2, 3, 12], [3, 6, 10, 8]]); px(x, '#7e6440', [[4, 9, 2, 4], [7, 9, 2, 4], [10, 9, 2, 4]]); }));
  set('helm', icon((x) => { px(x, '#000', [[2, 3, 12, 10], [4, 1, 8, 3]]); px(x, '#c4cdd4', [[3, 4, 10, 8], [5, 2, 6, 3]]); px(x, '#8a949c', [[3, 7, 10, 1]]); px(x, '#e8eef2', [[2, 11, 12, 2]]); }));
  set('kit', icon((x) => { px(x, '#000', [[3, 1, 4, 9], [9, 1, 4, 9], [5, 9, 6, 6]]); px(x, '#d02a2a', [[4, 2, 2, 7], [10, 2, 2, 7]]); px(x, '#c4ccd2', [[6, 10, 4, 4]]); }));
}

export function initEcon(callbacks) {
  cb = { ...cb, ...callbacks };
  makeHud();
  initNet();
  wrapHud();
}
