// DOM HUD. Comic Sans is load-bearing.
import { WEAPONS, SUITS as SUITSH, RANKS as RANKSH } from '/shared/weapons.js';

const $ = (id) => document.getElementById(id);
let centerT = 0, hitT = 0, hurtV = 0, weaponT = 0;
let lastHp = 100, lostT = 0, lostFrom = 100, glitchT = 0, nanT = 0, nanText = '';
const GARBAGE = ['NaN HP', 'ERR', 'undefined', '-0 HP', 'HP HP', '???', '1e3 HP', 'null'];

const MACH = 1235; // km/h

function span(text, color) {
  const s = document.createElement('span');
  s.textContent = text;
  if (color) s.style.color = color;
  return s;
}

export const hud = {
  init() {},
  // hotbar (bottom middle): weapon pictures in slots, the one you're holding pops up
  slots(ids, icons = []) {
    const bar = $('weapons');
    bar.innerHTML = '';
    ids.forEach((id, i) => {
      const w = WEAPONS[id];
      if (!w) return;
      const d = document.createElement('div');
      d.className = 'hslot';
      d.id = 'slot-' + i;
      d.style.setProperty('--c', w.color);
      if (icons[i]) { const im = document.createElement('img'); im.src = icons[i]; im.alt = ''; d.append(im); }
      const k = document.createElement('span'); k.className = 'key'; k.textContent = String(i + 1);
      const n = document.createElement('span'); n.className = 'nm'; n.textContent = w.name;
      d.append(k, n);
      bar.append(d);
    });
  },
  ammo(n, mag, reloading) {
    const a = $('ammo');
    if (n == null) { a.style.display = 'none'; return; }
    a.style.display = 'block';
    a.textContent = reloading ? 'reloading' : `${n} / ${mag}`;
    a.style.color = n === 0 || reloading ? '#ff5050' : n <= mag * 0.25 ? '#ffe14d' : '#fff';
  },
  show(v) { $('hud').classList.toggle('hidden', !v); },
  hp(v) {
    const p = Math.max(0, Math.min(100, v));
    if (p < lastHp - 0.5) this.hpGlitch(lastHp - p, lastHp, p);
    if (p > lastHp + 0.5) { lostT = 0; $('hpLost').style.width = '0'; }
    lastHp = p;
    $('hpbox').classList.toggle('lowhp', p > 0 && p < 30);
    $('hpbar').style.width = p + '%';
    $('hpbar').style.background = p > 60 ? '#5dff4f' : p > 30 ? '#ffe14d' : '#ff3030';
    $('hptext').textContent = nanT > 0 ? nanText : Math.ceil(p) + ' HP';
  },
  // taking damage: the lost chunk turns into missing texture, the bar glitches, little error squares spray out
  hpGlitch(amt, from, to) {
    const lost = $('hpLost');
    if (lostT <= 0) lostFrom = from;
    lost.style.transition = 'none';
    lost.style.left = to + '%';
    lost.style.width = Math.max(0, lostFrom - to) + '%';
    lostT = 0.55;
    const box = $('hpbox');
    box.classList.remove('glitch'); void box.offsetWidth; box.classList.add('glitch');
    glitchT = 0.35;
    const g = $('hpGlitch');
    const n = Math.min(12, 2 + Math.floor(amt / 5));
    for (let i = 0; i < n; i++) {
      const d = document.createElement('div');
      d.className = 'mt';
      const sz = 6 + Math.random() * 16;
      d.style.width = sz + 'px'; d.style.height = sz * (0.5 + Math.random()) + 'px';
      d.style.left = (to * 2.4 - 20 + Math.random() * (amt * 2.4 + 50)) + 'px';
      d.style.top = (-18 + Math.random() * 60) + 'px';
      g.append(d);
      setTimeout(() => d.remove(), 150 + Math.random() * 400);
    }
    if (amt >= 18) { nanT = 0.2; nanText = GARBAGE[(Math.random() * GARBAGE.length) | 0]; }
  },
  crossFade(k) { const c = $('crosshair'); const v = String(Math.round(k * 100) / 100); if (c.style.opacity !== v) c.style.opacity = v; },
  scope(on) {
    $('scope').classList.toggle('on', on);
    $('crosshair').style.display = on ? 'none' : '';
  },
  wave(info) {
    const el = $('wave');
    if (!info) { el.textContent = ''; return; }
    if (info.inter > 0) el.textContent = info.n ? `wave ${info.n} cleared · next in ${Math.ceil(info.inter / 1000)}` : `first wave in ${Math.ceil(info.inter / 1000)}`;
    else el.textContent = `WAVE ${info.n} · ${info.left} left`;
  },
  // the five cards you're holding, along the bottom of the screen
  cards(hand, sel) {
    const el = $('hand');
    if (!hand) { if (el.childElementCount) el.innerHTML = ''; el.style.display = 'none'; return; }
    el.style.display = 'flex';
    const key = hand.join(',') + '|' + sel;
    if (el.dataset.key === key) return;
    el.dataset.key = key;
    el.innerHTML = '';
    hand.forEach((c, i) => {
      const suit = SUITSH[c[0]], rank = RANKSH[Number(c.slice(1))];
      const d = document.createElement('div');
      d.className = 'pcard' + (i === sel ? ' sel' : '');
      d.style.color = suit.color === '#111111' ? '#111' : suit.color;
      d.textContent = c[0] === 'j' ? 'JOKER' : `${rank}${suit.sym}`;
      el.append(d);
    });
    if (!hand.length) el.textContent = 'shuffling...';
  },
  label(text) { $('modeLabel').textContent = text; },
  speed(ms) {
    const kmh = Math.round(ms * 3.6);
    $('speedNum').textContent = kmh;
    $('speedLabel').textContent = kmh >= MACH ? `MACH ${(kmh / MACH).toFixed(1)}` : '';
    $('speed').classList.toggle('shake', kmh >= 200);
    $('speed').style.fontSize = Math.min(64, 26 + kmh / 25) + 'px';
  },
  combo(n) { $('combo').textContent = n >= 2 ? `BHOP x${n}` : ''; },
  // the item box at the end of the hotbar: picture, G key, charges, refill pie
  itemSlot(id, icon) {
    let el = $('itemSlot');
    if (!el) { el = document.createElement('div'); el.id = 'itemSlot'; el.className = 'hslot item'; }
    $('weapons').append(el);
    el.innerHTML = '';
    if (!id) { el.remove(); return; }
    const im = document.createElement('img'); im.src = icon; im.alt = '';
    const k = document.createElement('span'); k.className = 'key'; k.textContent = 'G';
    const n = document.createElement('span'); n.className = 'nm'; n.id = 'itemN';
    const pie = document.createElement('div'); pie.className = 'pie'; pie.id = 'itemPie';
    el.append(pie, im, k, n);
    el.dataset.key = '';
  },
  item(n, max, frac) {
    const el = $('itemN');
    if (!el) return;
    const key = n + '/' + max + '/' + Math.round(frac * 20);
    if (el.dataset.key === key) return;
    el.dataset.key = key;
    el.textContent = `x${n}`;
    $('itemSlot').classList.toggle('empty', n <= 0);
    $('itemPie').style.background = frac < 1 ? `conic-gradient(rgba(255,255,255,0.28) ${frac * 360}deg, transparent 0)` : 'transparent';
  },
  slotOn(slot) { for (let i = 0; i < 6; i++) { const el = $('slot-' + i); if (el) el.classList.toggle('on', i === slot); } },
  weapon(id, slot) {
    for (let i = 0; i < 6; i++) { const el = $('slot-' + i); if (el) el.classList.toggle('on', i === slot); }
    const w = WEAPONS[id];
    if (!w) return;
    $('weaponName').innerHTML = '';
    $('weaponName').append(span(w.name, w.color), document.createElement('br'), span(w.desc, '#fff'));
    $('weaponName').style.opacity = 1;
    weaponT = 3;
  },
  meter(frac, label, color) {
    const m = $('meter');
    if (frac == null) { m.style.display = 'none'; return; }
    m.style.display = 'block';
    $('meterFill').style.width = Math.max(0, Math.min(1, frac)) * 100 + '%';
    $('meterFill').style.background = color;
    $('meterLabel').textContent = label;
  },
  // parts: [[text, color], ...]
  feed(parts) {
    const f = $('feed');
    const d = document.createElement('div');
    for (const [t, c] of parts) d.append(span(t, c));
    f.prepend(d);
    while (f.children.length > 6) f.lastChild.remove();
    setTimeout(() => d.remove(), 7000);
  },
  msg(text, dur = 1.5, cls = '') {
    const c = $('center');
    c.textContent = text;
    c.className = cls;
    c.style.opacity = 1;
    centerT = dur;
  },
  hit(hs) {
    const h = $('hitmarker');
    h.style.opacity = 1;
    h.style.color = hs ? '#ff3030' : '#fff';
    h.textContent = hs ? '✖' : 'x';
    hitT = 0.18;
  },
  hurt(a) { hurtV = Math.min(1, hurtV + a / 40); },
  dmgNum(x, y, amt, hs) {
    const d = document.createElement('div');
    d.className = 'num';
    d.textContent = hs ? amt + '!!' : amt;
    d.style.left = x + 'px'; d.style.top = y + 'px';
    d.style.color = hs ? '#ff3030' : '#ffe14d';
    $('nums').append(d);
    setTimeout(() => d.remove(), 900);
  },
  dead(show, parts) {
    $('dead').classList.toggle('hidden', !show);
    if (show) {
      const t = $('deadText');
      t.innerHTML = '';
      for (const [s, c] of parts) t.append(span(s, c));
    }
  },
  deadTimer(s) { $('deadTimer').textContent = s > 0 ? `respawning in ${s.toFixed(1)}...` : 'respawning...'; },
  scores(show, rows) {
    const el = $('scores');
    el.classList.toggle('hidden', !show);
    if (!show) return;
    el.innerHTML = '<div class="srow head"><span>bozo</span><span>K</span><span>D</span></div>';
    for (const r of rows) {
      const d = document.createElement('div');
      d.className = 'srow' + (r.me ? ' me' : '');
      const nm = span(r.name, r.color);
      if (r.card) { const im = document.createElement('img'); im.className = 'sc-card'; im.src = r.card; im.alt = ''; nm.prepend(im); }
      d.append(nm, span(String(r.k)), span(String(r.d)));
      el.append(d);
    }
  },
  chat(name, color, text) {
    const log = $('chatlog');
    const d = document.createElement('div');
    if (name) d.append(span(name + ': ', color));
    d.append(span(text, name ? '#fff' : '#aaa'));
    log.append(d);
    while (log.children.length > 8) log.firstChild.remove();
    setTimeout(() => d.remove(), 12000);
  },
  ping(ms) { $('ping').textContent = ms + 'ms'; },
  update(dt) {
    if (lostT > 0) {
      lostT -= dt;
      if (lostT <= 0) { const l = $('hpLost'); l.style.transition = 'width 0.35s steps(5)'; l.style.width = '0'; }
    }
    if (glitchT > 0) { glitchT -= dt; if (glitchT <= 0) $('hpbox').classList.remove('glitch'); }
    if (nanT > 0) nanT -= dt;
    if (centerT > 0) { centerT -= dt; if (centerT <= 0) $('center').style.opacity = 0; }
    if (hitT > 0) { hitT -= dt; if (hitT <= 0) $('hitmarker').style.opacity = 0; }
    if (weaponT > 0) { weaponT -= dt; if (weaponT <= 0) $('weaponName').style.opacity = 0; }
    hurtV = Math.max(0, hurtV - dt * 1.5);
    $('vignette').style.opacity = hurtV;
  },
};
