// Never Landed: finish a whole match without touching the ground after any spawn (3 s grace each spawn).
// The client knows exactly when you touch the ground, so it tracks the run and tells the server when it breaks.
// The server also watches your snapshots and decides at match end. This file is the client half + the HUD bits.
import { ME } from './player.js';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';

export const AIR = { on: false, failed: false, grace: 3000 };
const $ = (id) => document.getElementById(id);

const WING = '<svg viewBox="0 0 64 32" width="30" height="15" aria-hidden="true"><path fill="currentColor" d="M31 18C24 6 12 2 1 4c5 3 8 6 10 9-4 0-7 1-9 3 6 1 10 2 13 5-3 1-5 3-6 5 9-1 16-2 22-8zM33 18c7-12 19-16 30-14-5 3-8 6-10 9 4 0 7 1 9 3-6 1-10 2-13 5 3 1 5 3 6 5-9-1-16-2-22-8z"/></svg>';
// styles live here (not style.css) so this stays one self-contained feature
const CSS = `
#airInd { position: absolute; left: 16px; top: 150px; display: none; align-items: center; gap: 6px; font-size: 14px; color: #fff; background: rgba(0, 0, 0, 0.45); border: 2px solid #9ad0ff; padding: 2px 9px 2px 6px; transform: rotate(-2deg); text-shadow: 1px 1px 0 #000; }
#airInd svg { color: #9ad0ff; animation: airflap 0.5s infinite alternate ease-in-out; }
#airInd.grace { border-color: #ffe14d; } #airInd.grace small { color: #ffe14d; }
#airInd small { font-size: 11px; color: #aaa; }
@keyframes airflap { from { transform: scaleY(1); } to { transform: scaleY(0.45) translateY(3px); } }
#airFlourish { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; flex-direction: column; pointer-events: none; }
#airFlourish svg { width: min(520px, 70vw); height: auto; color: #fff; filter: drop-shadow(0 0 18px #9ad0ff) drop-shadow(4px 4px 0 #000); animation: airbig 0.35s infinite alternate ease-in-out, airin 0.6s ease-out; }
#airFlourish b { font-size: 46px; color: #9ad0ff; text-shadow: 3px 3px 0 #000; transform: rotate(-3deg); margin-top: -10px; }
#airFlourish i { position: absolute; width: 10px; height: 22px; border-radius: 50% 50% 50% 0; background: #fff; box-shadow: 0 0 6px #9ad0ff; animation: airfeather 2.6s ease-in forwards; }
@keyframes airbig { from { transform: scaleY(1); } to { transform: scaleY(0.6) translateY(14px); } }
@keyframes airin { from { opacity: 0; transform: scale(0.2); } to { opacity: 1; transform: scale(1); } }
@keyframes airfeather { from { transform: translate(0, 0) rotate(0); opacity: 1; } to { transform: translate(var(--dx), 260px) rotate(var(--r)); opacity: 0; } }
`;
let el = null, fl = null;
function ensure() {
  if (el) return;
  const st = document.createElement('style'); st.textContent = CSS; document.head.append(st);
  el = document.createElement('div'); el.id = 'airInd'; el.innerHTML = WING + '<span>NEVER LANDED</span><small></small>';
  el.title = 'Never Landed: finish this match without touching the ground';
  fl = document.createElement('div'); fl.id = 'airFlourish';
  ($('hud') || document.body).append(el, fl);
}

// called after every physics step: a single grounded tick (a bhop touch) counts, a jump pad launch doesn't
// grace runs from your last spawn or the run's start, whichever is later (the start can land a frame before its spawn)
const airT0 = () => Math.max(G.spawnT || 0, AIR.t0 || 0);
export function airTick(now) {
  if (!AIR.on || AIR.failed || !ME.alive || !ME.onGround) return;
  if (now - airT0() < AIR.grace) return;
  airFailed(true);
}
function airFailed(tell) {
  if (AIR.failed) return;
  AIR.failed = true; AIR.on = false;
  if (tell) net.send({ t: 'land' });
  hud.msg('YOU TOUCHED GRASS', 2.2, 'slip');
  hud.chat(null, null, 'Never Landed: you touched the ground. try again next match');
  sfx.error();
  render(performance.now());
}

// HUD: shows while your run is still clean, with the grace countdown after a spawn
export function airHud(now) {
  if (!el) return;
  const show = AIR.on && !AIR.failed && G.joined;
  el.style.display = show ? 'flex' : 'none';
  if (!show) return;
  const left = AIR.grace - (now - airT0());
  const g = ME.alive && left > 0;
  el.classList.toggle('grace', g);
  el.lastChild.textContent = g ? `get off the ground ${(left / 1000).toFixed(1)}` : '';
}
const render = (now) => airHud(now);
setInterval(() => { if (AIR.on || (el && el.style.display !== 'none')) airHud(performance.now()); }, 100); // idle in the menu
// new room: no run until the server says you're in from the start
export function airReset() { AIR.on = false; AIR.failed = false; render(performance.now()); }

// big flapping wings when you unlock it
export function airFlourish() {
  ensure();
  fl.innerHTML = WING.replace('width="30" height="15"', '') + '<b>NEVER LANDED</b>';
  for (let i = 0; i < 14; i++) {
    const f = document.createElement('i');
    f.style.left = 30 + Math.random() * 40 + '%'; f.style.top = 30 + Math.random() * 15 + '%';
    f.style.setProperty('--dx', (Math.random() - 0.5) * 300 + 'px'); f.style.setProperty('--r', (Math.random() - 0.5) * 720 + 'deg');
    f.style.animationDelay = Math.random() * 0.6 + 's';
    fl.append(f);
  }
  fl.style.display = 'flex';
  sfx.choir();
  clearTimeout(airFlourish.t);
  airFlourish.t = setTimeout(() => { fl.style.display = 'none'; fl.innerHTML = ''; }, 3200);
}

// the server says: your run started (match start / joined in time), it broke (it saw you standing), or the match ended
net.on('air', (m) => {
  ensure();
  if (m.on) { AIR.on = true; AIR.failed = false; AIR.t0 = performance.now(); if (m.grace) AIR.grace = m.grace; }
  else if (m.fail) airFailed(false);
  else if (m.end) {
    AIR.on = false;
    if (m.ok) hud.chat(null, null, m.acct ? 'Never Landed: clean run, not a single touch of the ground!' : 'Never Landed: clean run! log in so it counts');
  }
  render(performance.now());
});
