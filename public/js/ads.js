// The Laptop's pop-up ads, on your screen. The server says "you've been advertised to" (who did it, how many, how long);
// this draws the windows over the game, and you close them one at a time with the number in each one's close box (the
// mouse is busy aiming). Closing one sometimes gets you ARE YOU SURE?. They all go when the time is up, when you die,
// or when the match ends. Everyone else just sees the laptop come out, hears the chime, and sees windows fly off you.
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { ME } from './player.js';
import { ADS } from '/shared/weapons.js';

// [title, body, button]. original nonsense only: no real brands, nothing that could pass for a real ad
const COPY = [
  ['CONGRATULATIONS', 'you are the 1,000,000th person shot here today.', 'CLAIM NOTHING'],
  ['HOT SINGLE BOTS', 'in your area. 4 metres away. behind you.', 'TURN AROUND'],
  ['DOCTORS HATE HIM', 'local man stops dying with one weird trick (cover).', 'LEARN COVER'],
  ['JANK COLA', 'now with 30% more can.', 'THIRST'],
  ['YOUR PC HAS VIRUS', 'the virus is this window. click to make it worse.', 'MAKE IT WORSE'],
  ['FREE AIMBOT', 'download more aim. 0 kb. it is a picture of a duck.', 'DUCK'],
  ['EXTENDED WARRANTY', "we've been trying to reach you about your shopping cart.", 'HANG UP'],
  ['YOU WON A BOAT', 'the boat is a concept. shipping is $400.', 'PAY SHIPPING'],
  ['LOSE 100 HP FAST', 'ask the person who sent you this.', 'ASK THEM'],
  ['BREAD', "it's bread. buy bread.", 'BREAD'],
  ['ONE WEIRD SPOON', 'spoon owners in your area are furious.', 'SEE SPOON'],
  ['IS YOUR GRASS TOUCHED?', 'take our 40 minute quiz to find out.', 'START QUIZ'],
  ['DEAD MALL CLEARANCE', 'everything must go. it already went. come look at where it was.', 'LOOK'],
  ['PREMIUM WALLS', 'subscribe today. now 12% more solid.', 'WALL ME'],
  ['A MESSAGE FROM HR', 'the tall guy would like a word. he is not in this ad. he is somewhere else.', 'OH NO'],
  ['MARBLES!', 'you dropped these. all of them. everywhere.', 'PICK UP'],
  ['RATE THIS DEATH', 'how likely are you to recommend being shot to a friend?', '10/10'],
  ['FREE HAT', 'the hat is free. the head costs extra.', 'BUY HEAD'],
];
const SURE = ['ARE YOU SURE?', "closing ads hurts the ad's feelings.", "I'M SORRY"];
const BARS = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#39ff14', '#ff3030'];
// where the five slots sit (centre x %, centre y %): spread out, with one square on the crosshair
const SPOTS = [[50, 46], [26, 30], [74, 32], [30, 68], [72, 66]];

let layer = null, live = [], until = 0, sure = 0, queue = [], qT = 0, popN = 0, deck = [];
const on = () => live.length > 0 || queue.length > 0;

function ensure() {
  if (layer) return layer;
  const st = document.createElement('style');
  st.textContent = `
#adsLayer { position: fixed; inset: 0; z-index: 40; pointer-events: none; overflow: hidden; font-family: var(--font); }
#adsLayer .ad { position: absolute; width: clamp(230px, 27vw, 380px); transform: translate(-50%, -50%) rotate(var(--r)) scale(0.2); opacity: 0;
  background: rgba(18,8,24,0.96); border: 4px solid #ff4fd8; box-shadow: 8px 8px 0 #4fd8ff; color: #fff; transition: transform 0.12s cubic-bezier(.3,1.7,.5,1), opacity 0.08s; }
#adsLayer .ad.in { transform: translate(-50%, -50%) rotate(var(--r)) scale(1); opacity: 1; }
#adsLayer .ad.out { transform: translate(-50%, -30%) rotate(calc(var(--r) * 6)) scale(0.1); opacity: 0; transition: transform 0.16s ease-in, opacity 0.16s; }
#adsLayer .bar { display: flex; align-items: center; justify-content: space-between; background: var(--c); color: #000; font-weight: 700; padding: 3px 4px 3px 10px; border-bottom: 3px solid #000; font-size: clamp(13px, 1.5vw, 19px); letter-spacing: 1px; }
#adsLayer .x { background: #ff3030; color: #fff; border: 3px solid #000; box-shadow: 3px 3px 0 #000; padding: 0 9px; font-size: clamp(16px, 1.9vw, 24px); line-height: 1.3; white-space: nowrap; }
#adsLayer .x b { color: #ffe14d; }
#adsLayer .body { padding: 12px 12px 8px; font-size: clamp(14px, 1.55vw, 20px); line-height: 1.25; min-height: 3.2em; }
#adsLayer .btn { display: inline-block; margin: 0 12px 14px; background: #ffe14d; color: #000; font-weight: 700; border: 3px solid #000; box-shadow: 4px 4px 0 #ff4fd8; padding: 3px 14px; transform: rotate(-2deg); font-size: clamp(13px, 1.4vw, 18px); }
#adsLayer .ad.sure { border-color: #ff3030; }
#adsLayer .tip { position: absolute; left: 50%; top: 9%; z-index: 99999; transform: translateX(-50%) rotate(-1deg); background: #ffe14d; color: #000; font-weight: 700; border: 3px solid #000; box-shadow: 4px 4px 0 #ff4fd8; padding: 2px 12px; font-size: clamp(13px, 1.5vw, 19px); white-space: nowrap; }
`;
  document.head.append(st);
  layer = document.createElement('div');
  layer.id = 'adsLayer';
  document.body.append(layer);
  return layer;
}
function el(cls, txt) { const e = document.createElement('div'); e.className = cls; if (txt != null) e.textContent = txt; return e; }
function nextCopy() { if (!deck.length) deck = COPY.map((_, i) => i).sort(() => Math.random() - 0.5); return COPY[deck.pop()]; }
// one window in slot (0-4; its key is slot + 1)
function open(slot, copy, isSure) {
  if (live.some((a) => a.slot === slot)) return;
  const L = ensure(), ad = el('ad' + (isSure ? ' sure' : ''));
  const [x, y] = SPOTS[slot];
  ad.style.left = `${x + (Math.random() - 0.5) * 6}%`; ad.style.top = `${y + (Math.random() - 0.5) * 6}%`;
  ad.style.setProperty('--r', `${(Math.random() - 0.5) * 7}deg`);
  ad.style.zIndex = String(++popN);
  const bar = el('bar'); bar.style.setProperty('--c', isSure ? '#ff3030' : BARS[popN % BARS.length]);
  const close = el('x'); close.append('✕ '); const k = document.createElement('b'); k.textContent = String(slot + 1); close.append(k);
  bar.append(el('', copy[0]), close);
  ad.append(bar, el('body', copy[1]), el('btn', copy[2]));
  L.append(ad);
  requestAnimationFrame(() => requestAnimationFrame(() => ad.classList.add('in')));
  live.push({ slot, el: ad, isSure });
  if (isSure) sfx.adSure(); else sfx.adPop(popN);
}
function shut(a, quiet) {
  live = live.filter((o) => o !== a);
  a.el.classList.remove('in'); a.el.classList.add('out');
  setTimeout(() => a.el.remove(), 200);
  if (!quiet) sfx.adClose();
}
function tip() {
  if (!layer) return;
  let t = layer.querySelector('.tip');
  if (!on()) { if (t) t.remove(); return; }
  if (!t) { t = el('tip'); layer.append(t); }
  t.textContent = `press the number on an ad to close it · ${live.length + queue.length} left`;
}
export function adsReset() {
  for (const a of live.slice()) shut(a, true);
  queue = []; until = 0; sure = 0;
  tip();
}
// the server: you've been advertised to
function onAds(m) {
  const n = Math.max(1, Math.min(SPOTS.length, Math.floor(Number(m.n)) || ADS.n)), dur = Math.max(1, Math.min(20, Number(m.dur) || ADS.dur));
  adsReset();
  until = performance.now() + dur * 1000;
  sure = Math.max(0, Math.min(4, Math.floor(Number(m.sure)) || 0));
  queue = [...Array(n).keys()].sort(() => Math.random() - 0.5); // which slot opens when
  qT = 0;
  const by = m.by === G.myId ? null : (G.names.get(m.by) || {}).name;
  hud.msg(by ? 'YOU HAVE BEEN ADVERTISED TO' : 'YOUR OWN ADS', 2, 'slip');
  if (by) hud.chat(null, null, `${by} opened a laptop at you. press the number on each ad to close it`);
}
// 1-5 close the ad in that slot (and do nothing else while it's there: that key is busy)
export function adsKey(e) {
  if (!live.length || e.repeat) return false;
  const m = /^(?:Digit|Numpad)([1-5])$/.exec(e.code || '');
  if (!m) return false;
  const a = live.find((o) => o.slot === Number(m[1]) - 1);
  if (!a) return false;
  shut(a);
  if (!a.isSure && sure > 0 && Math.random() < 0.45) { sure--; const s = a.slot; setTimeout(() => { if (performance.now() < until) { open(s, SURE, true); tip(); } }, 260); }
  tip();
  return true;
}
export function updateAds(dt, now) {
  if (!until) return;
  if (now >= until || !G.joined || !ME.alive) { adsReset(); return; } // time's up, left, or dead: the ads let you go
  if (queue.length && (qT -= dt) <= 0) { qT = 0.16; open(queue.shift(), nextCopy(), false); tip(); }
}
// what everyone sees: windows fly off the victim, the laptop pops into the user's hand, the chime plays where they stand
export function adsFx(m) {
  if (m.k !== 'ads') return false;
  const u = G.remotes.get(m.id), v = G.remotes.get(m.to);
  if (u) { u.popItem('laptop', 900); sfx.laptopOpen(u.pos); }
  if (v && v.pos) fx.spray([v.pos[0], v.pos[1] + 1.7, v.pos[2]], 16, [0xff4fd8, 0x4fd8ff, 0xffe14d, 0xffffff], 5, 0.9, 0.16, 3, 1.2);
  if (m.id === G.myId && m.to !== G.myId) { const nm = (G.names.get(m.to) || {}).name; hud.msg(nm ? `ADS SERVED TO ${nm.toUpperCase()}` : 'ADS SERVED', 1.4, 'brag'); }
  return true;
}
export function initAds() {
  net.on('ads', onAds);
  net.on('ads!', () => { hud.msg('NO SIGNAL · POINT IT AT SOMEONE', 1, 'slip'); sfx.empty(); }); // nobody in front of it: the charge came back
}
export const adsOn = on;
