// Hidden NPCs + cats, the client half (data: shared/secrets.js, models: lorenpcs.js / lorecats.js).
// Places them on the map you're on, shows "F TALK" / "F PET" when you're close enough (the server's own reach test,
// plus a line of sight so nobody pets through a wall), runs the zine dialogue box (F next, 1-3 to answer), the
// petting (purrs, hearts, reactions, the odd swat), and the LORE page in the menu.
// Plant & Defuse: nobody's around (secretsOff), so a round never stops for a chat.
import * as THREE from 'three';
import { G } from './ctx.js';
import { net } from './net.js';
import { MAP, BOXES } from '/shared/map.js';
import { raycast } from '/shared/physics.js';
import { ME, eye } from './player.js';
import { hud } from './hud.js';
import { sfx, synth } from './audio.js';
import { account } from './account.js';
import { achInv } from '/shared/cosmetics.js';
import { COSMETICS, CONTAINERS, TYPE_NAMES_ALL } from '/shared/cosmetics.js';
import { SECRETS, SECRET, CHAPTERS, NPC_IDS, CAT_IDS, CAT_GOAL, secretsOn, secretsOff, canReach, loreOf } from '/shared/secrets.js';
import { buildCat, updateCat, petCat } from './lorecats.js';
import { buildNpc } from './lorenpcs.js';

const $ = (id) => document.getElementById(id);
let builtKey = '', objs = [], target = null, D = null, petT = 0;
const guestFound = new Set(); // a guest's finds this session (the LORE page shows them, not saved)
const VOICE = { gary: 150, dale: 190, janitor: 115, smiles: 320, todd: 250 }; // talk blip pitch

// ---------------------------------------------------------------- DOM: the prompt and the dialogue box (in the HUD)
function ui() {
  if ($('loreBox')) return;
  const hudEl = $('hud');
  const p = document.createElement('div'); p.id = 'lorePrompt'; p.className = 'hidden'; hudEl.append(p);
  const b = document.createElement('div'); b.id = 'loreBox'; b.className = 'hidden';
  b.innerHTML = '<div class="lb-name"><b></b><span></span></div><div class="lb-text"></div><div class="lb-opts"></div><div class="lb-hint"></div>';
  hudEl.append(b);
}
const showPrompt = (txt) => { const p = $('lorePrompt'); if (!p) return; if (!txt) { p.classList.add('hidden'); return; } if (p.dataset.t !== txt) { p.innerHTML = txt; p.dataset.t = txt; } p.classList.remove('hidden'); };

// ---------------------------------------------------------------- building them on the map
function clear() {
  for (const o of objs) G.scene.remove(o.root);
  objs = []; target = null; closeTalk(true);
}
function sync() {
  const off = secretsOff(G.round && G.round.game) || !G.joined;
  const key = (G.joined ? MAP.id : '') + (off ? ':off' : '');
  if (key === builtKey) return;
  builtKey = key;
  clear();
  if (off || !G.scene) return;
  for (const id of secretsOn(MAP.id)) {
    const s = SECRETS[id];
    const o = s.kind === 'cat' ? { cat: buildCat(s) } : { npc: buildNpc(s) };
    o.root = o.cat ? o.cat.root : o.npc.root;
    // drop onto whatever box is under the spot (a map that moved a bit doesn't leave them floating or buried)
    const hit = raycast([s.p[0], s.p[1] + 0.6, s.p[2]], [0, -1, 0], 2.5, BOXES);
    o.y = hit ? hit.point[1] : s.p[1];
    o.root.position.set(s.p[0], o.y, s.p[2]);
    o.root.rotation.y = s.face || 0;
    Object.assign(o, { id, s });
    G.scene.add(o.root);
    objs.push(o);
  }
}

// ---------------------------------------------------------------- every frame
const v3 = new THREE.Vector3();
export function updateLore(dt, now) {
  ui();
  sync();
  if (!objs.length) { showPrompt(''); return; }
  const e = eye(), alive = ME.alive;
  let best = null, bestD = 1e9;
  for (const o of objs) {
    const d = Math.hypot(e[0] - o.s.p[0], e[2] - o.s.p[2]);
    if (d > 70) continue; // too far to matter (and the fog has them anyway)
    const near = Math.max(0, Math.min(1, 1 - (d - 2.2) / 4));
    if (o.cat) updateCat(o.cat, dt, now, d < 9 ? e : null);
    else o.npc.update(dt, now, { eye: d < 12 ? e : null, near, talk: D && D.id === o.id, say: D && D.id === o.id && D.typing, dist: d, pos: o.s.p });
    if (alive && canReach([ME.pos[0], ME.pos[1] - (o.y - o.s.p[1]), ME.pos[2]], o.id) && d < bestD && seen(e, o)) { best = o; bestD = d; }
  }
  target = best;
  if (D) {
    const o = objs.find((q) => q.id === D.id);
    if (!o || !alive || Math.hypot(ME.pos[0] - o.s.p[0], ME.pos[2] - o.s.p[2]) > SECRET.reach + 2.2) closeTalk(); // walked off mid-sentence
    else tickTalk(dt);
  }
  showPrompt(!D && target ? `<b>F</b> ${target.cat ? 'PET THE CAT' : 'TALK'}` : '');
}
// can you see it (a ray from your eye to its middle that doesn't hit a wall first)
function seen(e, o) {
  const tx = o.s.p[0], ty = o.y + (o.cat ? 0.25 : 1.1), tz = o.s.p[2];
  const dx = tx - e[0], dy = ty - e[1], dz = tz - e[2], L = Math.hypot(dx, dy, dz);
  if (L < 0.8) return true;
  const h = raycast(e, [dx / L, dy / L, dz / L], L, BOXES);
  return !h || h.t > L - 0.6;
}

// ---------------------------------------------------------------- keys: F talks / pets / next line; 1-3 answer
export function loreKey(e) {
  if (D) {
    const m = /^Digit([1-4])$/.exec(e.code);
    if (m && D.opts && !D.typing) { const o = D.opts[Number(m[1]) - 1]; if (o) pick(o[1]); return true; }
    if (m && D.opts) return true; // (the number keys don't switch guns while you're answering)
    if (e.code === 'KeyF') { if (!e.repeat) advance(); return true; }
    return false;
  }
  if (e.code !== 'KeyF' || e.repeat || !target || !ME.alive) return false;
  if (target.cat) pet(target); else talk(target);
  return true;
}

// ---------------------------------------------------------------- talking
function talk(o) {
  D = { id: o.id, s: o.s, node: 'start', lines: [], i: 0, shown: 0, typing: false, opts: null, reply: null, done: false, told: false };
  net.send({ t: 'sec', id: o.id });
  const box = $('loreBox');
  box.querySelector('.lb-name b').textContent = o.s.name;
  box.querySelector('.lb-name span').textContent = o.s.title;
  box.classList.remove('hidden');
  enter('start');
}
function nodeLines(node) {
  const n = D.s.lines[node];
  if (node !== 'end') return n.say;
  const first = !D.reply || D.reply.first || D.reply.guest;
  const L = [...(first ? n.got : n.again)];
  if (D.reply && D.reply.guest) L.push(D.s.gift ? '*(you\'re a guest. log in and come back: the gift and the lore only count on an account.)*' : '*(you\'re a guest. log in so the LORE page remembers this.)*');
  return L;
}
function enter(node) {
  if (!D.s.lines[node]) node = 'end';
  D.node = node; D.lines = nodeLines(node); D.i = 0; D.opts = null;
  line();
}
function line() { D.shown = 0; D.typing = true; D.cur = D.lines[D.i]; render(); }
function render() {
  const box = $('loreBox'); if (!box) return;
  const txt = D.cur.slice(0, Math.floor(D.shown)), it = D.cur.startsWith('*');
  const t = box.querySelector('.lb-text'); t.textContent = it ? txt.replace(/\*/g, '') : txt; t.classList.toggle('act', it);
  const ob = box.querySelector('.lb-opts'); ob.innerHTML = '';
  if (D.opts && !D.typing) D.opts.forEach((o, i) => { const b = document.createElement('div'); b.className = 'lb-opt'; b.innerHTML = `<i>${i + 1}</i>`; b.append(document.createTextNode(o[0])); b.addEventListener('click', () => pick(o[1])); ob.append(b); });
  box.querySelector('.lb-hint').innerHTML = D.typing ? '<b>F</b> skip' : D.opts ? 'press <b>1</b>-<b>' + D.opts.length + '</b>' : D.i < D.lines.length - 1 ? '<b>F</b> next' : '<b>F</b> bye';
}
function tickTalk(dt) {
  if (!D.typing) return;
  const before = Math.floor(D.shown);
  D.shown = Math.min(D.cur.length, D.shown + dt * 48);
  const now2 = Math.floor(D.shown);
  if (now2 !== before) {
    if (now2 % 2 === 0 && /[a-z0-9?!]/i.test(D.cur[now2 - 1] || '') && !D.cur.startsWith('*')) { const f = (VOICE[D.s.look] || 200) * (0.9 + Math.random() * 0.25); synth.tone('square', f, f * 1.04, 0.035, 0.045); } // talk blips
    if (now2 >= D.cur.length) { D.typing = false; if (D.i === D.lines.length - 1) lastLine(); }
    render();
  }
}
function lastLine() {
  const n = D.s.lines[D.node];
  if (n.opts) D.opts = n.opts;
  if (D.node === 'end' && !D.told) { D.told = true; tell(); }
}
function advance() {
  if (D.typing) { D.shown = D.cur.length - 0.01; tickTalk(1); return; }
  if (D.i < D.lines.length - 1) { D.i++; line(); return; }
  if (D.opts) return;
  if (D.node !== 'end') { enter('end'); return; } // every chat ends on the end node (the gift line)
  closeTalk();
}
function pick(node) { if (!D) return; sfx.click(); enter(node); }
function closeTalk(quiet) {
  if (!D) return;
  if (!quiet && !D.told) tell();
  D = null;
  const b = $('loreBox'); if (b) b.classList.add('hidden');
}
// the callouts for a chat: lore found, the gift. waits for the server's answer (it's usually already here)
function tell() {
  const r = D && D.reply, s = D && D.s;
  if (!r || !s) { if (D) D.told = false; return; }
  if (r.first) {
    const ch = CHAPTERS.find((c) => c.id === s.chapter), n = NPC_IDS.filter((k) => (r.lore || []).includes(k)).length;
    hud.msg(`LORE FOUND: ${ch ? ch.name : ''} (${n}/${NPC_IDS.length})`, 2.6, 'brag');
    hud.chat(null, null, `lore found: ${ch ? ch.name.toLowerCase() : ''}, from ${s.name.toLowerCase()}. it's in LORE in the menu now.`);
    sfx.rankUp();
    if (r.gift) setTimeout(() => { hud.msg(`YOU GOT: ${giftName(r.gift).toUpperCase()}`, 2.6, 'brag'); sfx.cash(); hud.chat(null, null, `${s.name.toLowerCase()} gave you ${giftName(r.gift)}${r.gift.roll ? ' (open it in CONTAINERS)' : ' (equip it in CHARACTER or COSMETICS)'}`); }, 1500);
  } else if (r.guest) guestFound.add(D.id);
}
function giftName(g) {
  if (g.roll) return `a ${CONTAINERS[g.roll].name}`;
  const c = COSMETICS[g.type] && COSMETICS[g.type][g.id];
  return c ? `the ${c.name} ${(TYPE_NAMES_ALL[g.type] || '').toLowerCase()}` : 'something';
}

// ---------------------------------------------------------------- petting
const PURR = (pos, k = 1) => { for (let i = 0; i < 26; i++) synth.noise(0.035, 0.22 * k, 'lowpass', 220, 120, pos, i * 0.042); }; // ~24 rumbles a second
const MEOW = (pos, hi = 1) => { synth.tone('sawtooth', 520 * hi, 820 * hi, 0.16, 0.12, pos); synth.tone('sawtooth', 820 * hi, 460 * hi, 0.24, 0.12, pos, 0.15); synth.tone('sine', 1100 * hi, 700 * hi, 0.3, 0.05, pos, 0.05); };
const HISS = (pos) => synth.noise(0.5, 0.45, 'highpass', 3000, 5000, pos);
function pet(o, remote) {
  const now = performance.now();
  if (!remote && now - petT < 900) return;
  if (!remote) petT = now;
  const k = petCat(o.cat, now, remote ? (Math.random() < 0.5 ? 'squint' : 'blink') : null);
  const pos = [o.s.p[0], o.y + 0.3, o.s.p[2]];
  if (k === 'swat') {
    HISS(pos);
    if (!remote) { // a sassy swat: shoved back a bit, screen jolts
      const dx = ME.pos[0] - o.s.p[0], dz = ME.pos[2] - o.s.p[2], L = Math.hypot(dx, dz) || 1;
      ME.vel[0] += (dx / L) * 7; ME.vel[2] += (dz / L) * 7; ME.vel[1] = Math.max(ME.vel[1], 3.5);
      G.shake = Math.max(G.shake, 0.6); hud.msg('HSSSS', 1, 'brag');
    }
  } else { PURR(pos, remote ? 0.6 : 1); if (Math.random() < 0.45) MEOW(pos, o.s.coat === 'grey' ? 0.8 : o.s.coat === 'cream' ? 1.2 : 1); hearts(pos, remote ? 4 : 9); }
  if (!remote) net.send({ t: 'sec', id: o.id });
}
// hearts: little canvas sprites that float up and wobble
let heartTex = null;
const hearts = (p, n) => {
  if (!heartTex) {
    const c = document.createElement('canvas'); c.width = c.height = 32; const g = c.getContext('2d');
    g.fillStyle = '#ff4fd8'; g.strokeStyle = '#000'; g.lineWidth = 3; g.beginPath(); g.moveTo(16, 28); g.bezierCurveTo(-6, 12, 6, -4, 16, 8); g.bezierCurveTo(26, -4, 38, 12, 16, 28); g.fill(); g.stroke();
    heartTex = new THREE.CanvasTexture(c);
  }
  for (let i = 0; i < n; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: heartTex, transparent: true, depthWrite: false }));
    s.scale.setScalar(0.2 + Math.random() * 0.12); s.position.set(p[0] + (Math.random() - 0.5) * 0.5, p[1] + Math.random() * 0.3, p[2] + (Math.random() - 0.5) * 0.5);
    s.userData = { t: performance.now() + i * 90, life: 1300 + Math.random() * 500, vx: (Math.random() - 0.5) * 0.3, ph: Math.random() * 6 };
    s.visible = false; G.scene.add(s); floaters.push(s);
  }
};
const floaters = [];
export function updateLoreFx(now) {
  for (let i = floaters.length - 1; i >= 0; i--) {
    const s = floaters[i], u = s.userData, k = (now - u.t) / u.life;
    if (k < 0) continue;
    if (k >= 1) { G.scene.remove(s); s.material.dispose(); floaters.splice(i, 1); continue; }
    s.visible = true;
    s.position.y += 0.012; s.position.x += Math.sin(now * 0.006 + u.ph) * 0.004 + u.vx * 0.01;
    s.material.opacity = k < 0.15 ? k / 0.15 : 1 - (k - 0.15) / 0.85;
  }
}

// ---------------------------------------------------------------- the server's answers
net.on('sec', (m) => {
  if (typeof m.id !== 'string' || !Object.hasOwn(SECRETS, m.id)) return;
  const s = SECRETS[m.id];
  if (m.no) {
    if (D && D.id === m.id) closeTalk(true);
    hud.msg(m.no === 'bomb' ? 'NOT DURING A ROUND' : m.no === 'far' ? 'GET CLOSER' : 'NOBODY HERE', 1.4);
    return;
  }
  if (m.first && account.me) { // keep the account copy in step (LORE page, inventories, the cat count)
    const me = account.me; me.inv = { ...(me.inv || {}), lore: Array.isArray(m.lore) ? m.lore.filter((k) => Object.hasOwn(SECRETS, k)) : [...loreOf(me.inv), m.id] };
    if (m.gift && m.gift.type) me.inv[m.gift.type] = [...(me.inv[m.gift.type] || []), m.gift.id];
    if (m.gift && m.gift.roll && me.rolls) me.rolls[m.gift.roll] = (me.rolls[m.gift.roll] || 0) + 1;
    if (s.kind === 'cat') me.stats = { ...(me.stats || {}), cats: CAT_IDS.filter((k) => me.inv.lore.includes(k)).length };
    G.inv = achInv(me.inv, me.achs);
  }
  if (s.kind === 'npc') { if (D && D.id === m.id) { D.reply = m; if (D.node === 'end') { D.lines = nodeLines('end'); if (!D.told && !D.typing && D.i === D.lines.length - 1) { D.told = true; tell(); } } } else { const keep = D; D = { id: m.id, s, reply: m }; tell(); D = keep; } return; }
  // a cat
  if (m.guest) { guestFound.add(m.id); hud.msg(`${s.name} PURRS`, 1.6); hud.chat(null, null, `${s.name.toLowerCase()} (${s.title}) likes you. you're a guest though: log in so the board remembers.`); return; }
  if (!m.first) { hud.msg(`${s.name} PURRS`, 1.2); return; }
  const n = CAT_IDS.filter((k) => (m.lore || []).includes(k)).length;
  hud.msg(`PETTED ${s.name} · ${Math.min(n, CAT_GOAL)}/${CAT_GOAL}`, 2.4, 'brag');
  hud.chat(null, null, `you petted ${s.name.toLowerCase()}, ${s.title}. the board: ${Math.min(n, CAT_GOAL)}/${CAT_GOAL}`);
  if (n >= CAT_GOAL) setTimeout(() => { hud.msg('THE BOARD APPROVES', 3, 'brag'); sfx.rankUp(); }, 2500);
});
// someone else petted a cat (or chatted): the cat purrs for them too
net.on('secfx', (m) => {
  const o = objs.find((q) => q.id === m.id);
  if (o && o.cat) pet(o, true);
});

// ---------------------------------------------------------------- the LORE page (menu)
export function renderLore(el) {
  const found = new Set([...loreOf(account.me && account.me.inv), ...guestFound]);
  const guest = !account.me;
  const nFound = NPC_IDS.filter((k) => found.has(k)).length, nCats = CAT_IDS.filter((k) => found.has(k)).length;
  el.innerHTML = '';
  const add = (tag, cls, txt) => { const d = document.createElement(tag); if (cls) d.className = cls; if (txt != null) d.textContent = txt; el.append(d); return d; };
  add('div', 'lore-count', `lore found ${nFound}/${NPC_IDS.length} · board petted ${Math.min(nCats, CAT_GOAL)}/${CAT_GOAL}`);
  for (const ch of CHAPTERS) {
    const id = NPC_IDS.find((k) => SECRETS[k].chapter === ch.id), s = SECRETS[id], got = found.has(id);
    const d = add('div', 'lore-ch' + (got ? ' got' : ''));
    const h = document.createElement('b'); h.textContent = got ? ch.name : '???'; d.append(h);
    const who = document.createElement('span'); who.textContent = got ? `told by ${s.name.toLowerCase()}, ${s.title}` : `someone knows. ${s.where}. press F near them`; d.append(who);
    if (got) { const p = document.createElement('p'); p.textContent = ch.file; d.append(p); }
  }
  const b = add('div', 'lore-board');
  const h = document.createElement('b'); h.textContent = 'THE BOARD OF DIRECTORS'; b.append(h);
  const row = document.createElement('div'); row.className = 'lore-cats'; b.append(row);
  for (const id of CAT_IDS) {
    const s = SECRETS[id], got = found.has(id), c = document.createElement('div');
    c.className = 'lore-cat' + (got ? ' got' : '');
    c.innerHTML = `<i>${got ? '=^.^=' : '?'}</i>`;
    const t = document.createElement('div'); t.textContent = got ? `${s.name.toLowerCase()} · ${s.title}` : `hiding in ${s.where}`; c.append(t);
    row.append(c);
  }
  add('div', 'lore-note', guest ? 'guest: what you find this session shows here, but nothing is saved. log in.' : nCats >= CAT_GOAL ? 'the board approves. your ears, tail and dress are in CHARACTER.' : 'pet the whole board. they have a dress code for their favourite staff.');
}
