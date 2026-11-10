// Touch controls for phones and tablets. Only loaded when touchboot.js tagged the page (html.touch), so desktop never runs it.
// No second input path: every button presses the key its action is bound to (keys.js) by sending the same keydown / mousedown
// the keyboard would, so modes, items and rebinding all behave like on desktop. only looking around is its own thing (main.js look).
// the stick is 8-way on purpose: movement is forward/back/left/right keys everywhere else too.
import { K, ACTIONS } from './keys.js';
import { G } from './ctx.js';

const $ = (id) => document.getElementById(id);
const DEF = Object.fromEntries(ACTIONS.map((a) => [a.id, a.def[0]]));
const codeFor = (id) => { const b = K.get(id); return b[0] || b[1] || DEF[id] || ''; };
const KEYNAME = { Space: ' ', Enter: 'Enter', Tab: 'Tab' };

// [id, action or '' (custom), label, x, y, size, opts]: x / y = the button's centre from the bottom corner on the fire side, in finger px
const BTNS = [
  ['fire', 'fire', 'FIRE', 100, 92, 84, { look: 1 }],
  ['jump', 'jump', 'JUMP', 36, 50, 58, {}],
  ['crouch', 'crouch', 'SLIDE', 34, 120, 50, {}],
  ['aim', 'aim', 'AIM', 44, 184, 50, { look: 1 }],
  ['grapple', 'grapple', 'HOOK', 112, 176, 56, { look: 1 }],
  ['melee', 'slot3', 'STAB', 176, 152, 44, {}],
  ['swap', 'lastSlot', 'SWAP', 180, 98, 44, {}],
  ['reload', 'reload', 'RELOAD', 176, 44, 46, {}],
  ['use', 'use', 'USE', 242, 126, 46, { ctx: 1 }],
  ['buy', 'buy', 'BUY', 242, 72, 44, { ctx: 1 }],
  ['kh', '', 'DROP', 242, 180, 40, { ctx: 1, code: 'KeyH' }],
  // the corner on the fire side, top: small ones
  ['pause', '', 'II', 26, 26, 36, { top: 1 }],
  ['chat', '', 'CHAT', 70, 26, 36, { top: 1 }],
  ['scores', 'scores', 'TAB', 114, 26, 36, { top: 1 }],
  ['spray', 'spray', 'SPRAY', 158, 26, 36, { top: 1 }],
];

export function initTouch(api) {
  const S = api.S;
  const canvas = $('game'), root = document.documentElement;
  const scale = () => (window.JF_TOUCH && window.JF_TOUCH.scale) || 1; // page px -> finger px
  if (S.tSens == null) S.tSens = 1;
  if (S.tSize == null) S.tSize = scale() >= 1 && Math.min(screen.width, screen.height) >= 700 ? 1.2 : 1; // tablets: bigger hands-off distance, bigger buttons
  if (S.tAlpha == null) S.tAlpha = 0.75;
  if (S.tFull == null) S.tFull = true;
  if (S.tInit !== 1) { S.tInit = 1; S.toggleAim = true; api.save(); } // first run on a phone: tap AIM to scope, tap again to stop (holding a button while steering is a hand cramp)

  // ---------------------------------------------------------- the layer
  const ui = document.createElement('div');
  ui.id = 'touchUI'; ui.className = 'hidden';
  const stick = document.createElement('div'); stick.className = 'tstick'; stick.innerHTML = '<i></i>';
  ui.append(stick);
  const els = {};
  for (const [id, act, label, x, y, size, o] of BTNS) {
    const b = document.createElement('div');
    b.className = 'tb tb-' + id + (o.top ? ' top' : '') + (o.ctx ? ' hidden' : '');
    b.dataset.b = id; b.textContent = label;
    b.style.setProperty('--x', x); b.style.setProperty('--y', y); b.style.setProperty('--d', size);
    ui.append(b);
    els[id] = { el: b, act, o, code: '' };
  }
  document.body.insertBefore(ui, $('hud')); // under the HUD: the end screen, buy menu and backpack sit on top and take their own taps
  const rot = document.createElement('div');
  rot.id = 'touchRot';
  rot.innerHTML = '<div><b>TURN YOUR PHONE</b><span>jankfire only works sideways. like a crab.</span></div>';
  document.body.append(rot);

  function applyLook() {
    root.style.setProperty('--ts', String(Math.max(0.6, Math.min(1.5, Number(S.tSize) || 1))));
    root.style.setProperty('--ta', String(Math.max(0.15, Math.min(1, Number(S.tAlpha) || 0.75))));
    root.classList.toggle('lefty', !!S.tLefty);
  }
  applyLook();
  root.classList.toggle('tsmall', scale() < 1);

  // ---------------------------------------------------------- sending keys
  function send(code, down) {
    if (!code) return;
    const m = /^Mouse(\d)$/.exec(code);
    if (m) canvas.dispatchEvent(new MouseEvent(down ? 'mousedown' : 'mouseup', { button: Number(m[1]), bubbles: true, cancelable: true }));
    else window.dispatchEvent(new KeyboardEvent(down ? 'keydown' : 'keyup', { code, key: KEYNAME[code] || '', bubbles: true, cancelable: true }));
  }
  const tap = (code) => { send(code, true); send(code, false); };
  const buzz = (ms) => { try { if (navigator.vibrate) navigator.vibrate(ms); } catch { /* no motor */ } };

  // ---------------------------------------------------------- buttons
  function btnDown(id) {
    const b = els[id];
    if (!b || b.code) return;
    b.el.classList.add('on'); buzz(8);
    if (id === 'pause') { releaseAll(); api.pause(); return; }
    if (id === 'chat') { releaseAll(); api.chat(); const c = $('chatin'); if (c) c.focus(); return; } // focus inside the tap, or iOS keeps the keyboard shut
    b.code = b.o.code || codeFor(b.act);
    send(b.code, true);
  }
  function btnUp(id) {
    const b = els[id];
    if (!b) return;
    b.el.classList.remove('on');
    if (b.code) { send(b.code, false); b.code = ''; }
  }

  // ---------------------------------------------------------- the stick: presses the move keys
  const mv = { id: null, ox: 0, oy: 0, keys: {} };
  const MOVE = ['forward', 'back', 'left', 'right', 'sprint'];
  function setMove(want) {
    for (const a of MOVE) {
      const cur = mv.keys[a];
      if (want[a] && !cur) { const c = codeFor(a); mv.keys[a] = c; send(c, true); }
      else if (!want[a] && cur) { send(cur, false); mv.keys[a] = ''; }
    }
  }
  const R = () => 52 * (Number(S.tSize) || 1) / scale(); // stick radius in page px
  function stickAt(x, y, show) {
    stick.style.left = x + 'px'; stick.style.top = y + 'px';
    stick.classList.toggle('live', !!show);
  }
  function stickMove(t) {
    const r = R();
    let dx = (t.clientX - mv.ox) / r, dy = (t.clientY - mv.oy) / r;
    const m = Math.hypot(dx, dy);
    if (m > 1) { dx /= m; dy /= m; }
    stick.firstChild.style.transform = `translate(${dx * r * 0.62}px, ${dy * r * 0.62}px)`;
    const on = m > 0.24;
    const fw = on && dy < -0.36;
    setMove({
      forward: fw, back: on && dy > 0.36, left: on && dx < -0.36, right: on && dx > 0.36,
      // all the way up = run. Plant & Defuse flips it (that key is the quiet walk there): a small push sneaks
      sprint: G.eco ? on && m < 0.62 : fw && m > 0.9,
    });
  }
  function stickEnd() {
    mv.id = null; setMove({});
    stick.firstChild.style.transform = '';
    stick.classList.remove('live'); stick.style.left = ''; stick.style.top = '';
  }

  // ---------------------------------------------------------- touches
  const touches = new Map(); // touch id -> { kind: 'btn' | 'look' | 'move', id, x, y }
  const stickSide = (x) => (S.tLefty ? x > innerWidth * 0.58 : x < innerWidth * 0.42);
  function start(e) {
    e.preventDefault(); // no page scroll / zoom / text selection, and no fake mouse click afterwards
    for (const t of e.changedTouches) {
      const hit = t.target && t.target.closest ? t.target.closest('.tb') : null;
      if (hit) {
        const id = hit.dataset.b;
        touches.set(t.identifier, { kind: 'btn', id, x: t.clientX, y: t.clientY, look: !!els[id].o.look });
        btnDown(id);
      } else if (mv.id == null && stickSide(t.clientX) && !api.gate()) {
        mv.id = t.identifier; mv.ox = t.clientX; mv.oy = t.clientY;
        touches.set(t.identifier, { kind: 'move' });
        stickAt(t.clientX, t.clientY, true);
      } else {
        touches.set(t.identifier, { kind: 'look', x: t.clientX, y: t.clientY, look: true });
        if (api.gate()) tap('Mouse0'); // TAP TO DROP IN, skip the killcam, watch the next player: what a click does
      }
    }
  }
  function move(e) {
    e.preventDefault();
    for (const t of e.changedTouches) {
      const s = touches.get(t.identifier);
      if (!s) continue;
      if (s.kind === 'move') { stickMove(t); continue; }
      if (!s.look) continue;
      const k = scale(); // same finger distance = same turn on every screen
      api.look((t.clientX - s.x) * k, (t.clientY - s.y) * k);
      s.x = t.clientX; s.y = t.clientY;
    }
  }
  function end(e) {
    e.preventDefault();
    for (const t of e.changedTouches) {
      const s = touches.get(t.identifier);
      touches.delete(t.identifier);
      if (!s) continue;
      if (s.kind === 'btn') btnUp(s.id);
      else if (s.kind === 'move') stickEnd();
    }
  }
  function releaseAll() {
    touches.clear();
    for (const id in els) btnUp(id);
    if (mv.id != null || MOVE.some((a) => mv.keys[a])) stickEnd();
  }
  ui.addEventListener('touchstart', start, { passive: false });
  ui.addEventListener('touchmove', move, { passive: false });
  ui.addEventListener('touchend', end, { passive: false });
  ui.addEventListener('touchcancel', end, { passive: false });

  // ---------------------------------------------------------- the HUD's own boxes are buttons too: hotbar, item, killstreaks, ammo (reload), ready up, the vote
  const HUDTAP = '#weapons .hslot, #streakTray .kstreak, #ammo, #lbReady, #voteOpts > *';
  $('hud').addEventListener('touchstart', (e) => {
    const t = e.target && e.target.closest ? e.target.closest(HUDTAP) : null;
    if (!t || !api.inGame()) return;
    e.preventDefault();
    buzz(8);
    const idx = (el) => Array.prototype.indexOf.call(el.parentNode.children, el);
    if (t.id === 'itemSlot') tap(codeFor('item'));
    else if (t.id === 'ammo') tap(codeFor('reload'));
    else if (t.id === 'lbReady') tap(codeFor('ready'));
    else if (t.classList.contains('kstreak')) tap(codeFor('streak' + (idx(t) + 1)));
    else if (t.classList.contains('hslot')) { const m = /^slot-(\d)$/.exec(t.id); if (m) tap(codeFor('slot' + (Number(m[1]) + 1))); }
    else tap(codeFor('vote' + (idx(t) + 1)));
  }, { passive: false });

  // ---------------------------------------------------------- page manners: no pinch zoom, no long-press menu, fullscreen when the browser lets us
  for (const t of ['gesturestart', 'gesturechange', 'gestureend']) document.addEventListener(t, (e) => e.preventDefault(), { passive: false }); // iOS pinch
  let lastEnd = 0;
  document.addEventListener('touchend', (e) => { // iOS double-tap zoom (it ignores user-scalable=no)
    const now = performance.now();
    if (now - lastEnd < 320 && !(e.target && e.target.closest && e.target.closest('input, select, textarea'))) e.preventDefault();
    lastEnd = now;
  }, { passive: false });
  function goFull() {
    if (S.tFull === false || scale() < 1) return; // a zoomed-out phone stays out: Chrome's fullscreen forces the page back to 1:1 and the HUD goes giant. those get fullscreen from ADD TO HOME SCREEN
    try {
      const el = document.documentElement;
      const req = el.requestFullscreen || el.webkitRequestFullscreen;
      if (!req || document.fullscreenElement || document.webkitFullscreenElement) return;
      const p = req.call(el, { navigationUI: 'hide' });
      const lockLand = () => { try { const q = screen.orientation && screen.orientation.lock && screen.orientation.lock('landscape'); if (q && q.catch) q.catch(() => {}); } catch { /* not allowed */ } };
      if (p && p.then) p.then(lockLand).catch(() => {}); else lockLand();
    } catch { /* iPhone Safari: no fullscreen for pages. add to home screen instead */ }
  }
  // any PLAY-ish button is a fine moment (it has to be inside a tap)
  document.addEventListener('click', (e) => { if (e.target && e.target.closest && e.target.closest('[data-mode], #setupGo, #resume, .tfull')) goFull(); }, true);

  // ---------------------------------------------------------- show / hide with the game, and the buttons only some modes have
  let shown = false;
  function tick() {
    const on = api.inGame();
    if (on !== shown) {
      shown = on;
      ui.classList.toggle('hidden', !on);
      root.classList.toggle('tgame', on);
      if (!on) releaseAll();
    }
    if (!on) return;
    document.body.classList.remove('hotbar-right'); // (a synced desktop setting: the right side is thumbs here)
    const c = api.ctx();
    els.use.el.classList.toggle('hidden', !c.use);
    els.buy.el.classList.toggle('hidden', !c.eco);
    els.kh.el.classList.toggle('hidden', !(c.eco || c.royale));
    els.kh.el.textContent = c.royale ? 'HEAL' : 'DROP';
    els.melee.el.classList.toggle('hidden', !!c.royale); // royale: slots are whatever you looted, the hotbar does it
    ui.classList.toggle('gate', !!api.gate());
    ui.classList.toggle('watch', !!c.watch); // a replay is playing: nothing to press but pause
  }
  setInterval(tick, 120);
  addEventListener('blur', releaseAll);
  document.addEventListener('visibilitychange', () => { if (document.hidden) releaseAll(); });

  return { applyLook, releaseAll, goFull };
}
