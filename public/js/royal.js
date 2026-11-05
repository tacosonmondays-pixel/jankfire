// Sniper Royalty on screen: the gold toast when you tick a box, the four boxes for the menus, and the big
// GOLDEN SNIPER UNLOCKED moment. The server decides every tick (and who owns the skin); this only shows them.
import { ROYAL_FEATS } from '/shared/looks.js';
import { sfx } from './audio.js';

const $ = (id) => document.getElementById(id);
export const featsDone = (bits) => ROYAL_FEATS.filter((_, i) => bits & (1 << i)).length;
// a little gold crown (inline svg, no files)
const CROWN = '<svg viewBox="0 0 64 48" aria-hidden="true"><defs><linearGradient id="rgc" x1="0" y1="0" x2="0" y2="1">'
  + '<stop offset="0" stop-color="#fff3a0"/><stop offset="0.55" stop-color="#ffc21a"/><stop offset="1" stop-color="#b07410"/></linearGradient></defs>'
  + '<path d="M6 40 L3 12 L18 26 L32 4 L46 26 L61 12 L58 40 Z" fill="url(#rgc)" stroke="#5a3a00" stroke-width="2.5" stroke-linejoin="round"/>'
  + '<rect x="6" y="38" width="52" height="8" rx="2" fill="url(#rgc)" stroke="#5a3a00" stroke-width="2.5"/>'
  + '<circle cx="32" cy="30" r="4.5" fill="#ff1f45" stroke="#5a0010" stroke-width="1.5"/><circle cx="18" cy="33" r="3.2" fill="#2a6bff"/><circle cx="46" cy="33" r="3.2" fill="#18d060"/>'
  + '<circle cx="3" cy="11" r="2.6" fill="#fff6e0"/><circle cx="32" cy="4" r="2.6" fill="#fff6e0"/><circle cx="61" cy="11" r="2.6" fill="#fff6e0"/></svg>';
let crowns = 0;
function crown(cls) { const d = document.createElement('div'); d.className = cls; d.innerHTML = CROWN.replaceAll('rgc', 'rgc' + ++crowns); return d; } // own gradient id each

// the four feats as boxes, ticked or not. fresh = the ones you just got (they pop)
export function royalBoxes(bits, fresh = 0, feats = ROYAL_FEATS) {
  const d = document.createElement('div');
  d.className = 'rfeats';
  feats.forEach((f, i) => {
    const on = bits & (1 << i), b = document.createElement('span'), box = document.createElement('i');
    b.className = 'rf' + (on ? ' on' : '') + (fresh & (1 << i) ? ' new' : '');
    box.textContent = on ? '✔' : '';
    b.append(box, f.name);
    b.title = f.desc;
    d.append(b);
  });
  return d;
}

// "SNIPER ROYALTY 2/4  QUICK-SCOPE" + the boxes, top middle. guests are told it would have counted
let toastT = null;
export function royalToast(all, add, guest) {
  const el = $('royalToast');
  if (!el) return;
  el.innerHTML = '';
  const h = document.createElement('div'); h.className = 'rt';
  const n = document.createElement('b'); n.textContent = `SNIPER ROYALTY ${featsDone(all)}/${ROYAL_FEATS.length}`;
  const what = document.createElement('span'); what.textContent = ROYAL_FEATS.filter((_, i) => add & (1 << i)).map((f) => f.name).join(' + ');
  h.append(crown('rcrown'), n, what);
  el.append(h, royalBoxes(all, add));
  if (guest) { const s = document.createElement('div'); s.className = 'rsub'; s.textContent = 'log in so it counts'; el.append(s); }
  el.classList.remove('show'); void el.offsetWidth; el.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(() => el.classList.remove('show'), 3800);
  sfx.ting(); setTimeout(() => sfx.cash(), 90);
}

// the whole thing done: crown, gold rays, GOLDEN SNIPER UNLOCKED, sparks flying out. a few seconds, then it fades
let bigT = null;
export function royalUnlock(sub) {
  const el = $('royalBig');
  if (!el) return;
  el.innerHTML = '';
  const rays = document.createElement('div'); rays.className = 'rrays';
  const t = document.createElement('div'); t.className = 'rbig'; t.textContent = 'GOLDEN SNIPER UNLOCKED';
  const s = document.createElement('div'); s.className = 'rsub'; s.textContent = sub || '';
  const sparks = document.createElement('div'); sparks.className = 'rsparks';
  for (let i = 0; i < 28; i++) {
    const p = document.createElement('i');
    const a = (i / 28) * Math.PI * 2 + Math.random() * 0.2, r = 160 + Math.random() * 260;
    p.style.setProperty('--dx', `${Math.cos(a) * r}px`); p.style.setProperty('--dy', `${Math.sin(a) * r * 0.6}px`);
    p.style.animationDelay = `${Math.random() * 0.25}s`;
    sparks.append(p);
  }
  el.append(rays, crown('rcrownbig'), t, s, sparks);
  el.classList.remove('show'); void el.offsetWidth; el.classList.add('show');
  clearTimeout(bigT);
  bigT = setTimeout(() => el.classList.remove('show'), 4600);
  sfx.choir(); sfx.cash(); setTimeout(() => sfx.ting(), 350);
}
