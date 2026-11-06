// Out of bounds: leave the map's play area (map.bounds) and a big "RETURN TO THE MAP 3.. 2.. 1.." takes over the screen.
// Come back in time and it clears. The server runs the same clock (shared/bounds.js) and kills you when it runs out.
import { ME } from './player.js';
import { G } from './ctx.js';
import { sfx } from './audio.js';
import { MAPS, MAP } from '/shared/map.js';
import { OOB, outOfBounds } from '/shared/bounds.js';

// styles live here (not style.css) so this stays one self-contained feature
const CSS = `
#oob { position: absolute; inset: 0; display: none; pointer-events: none; align-items: center; justify-content: center; flex-direction: column; z-index: 6;
  background: repeating-linear-gradient(-45deg, rgba(255, 30, 60, 0.16) 0 26px, rgba(0, 0, 0, 0.12) 26px 52px);
  box-shadow: inset 0 0 0 10px #ff2a4a, inset 0 0 140px 30px rgba(255, 0, 40, 0.55); animation: oobpulse 0.5s infinite alternate; }
#oob b { font-size: clamp(26px, 6vw, 64px); color: #fff; letter-spacing: 2px; text-shadow: 4px 4px 0 #ff2a4a, -3px -2px 0 #19e6ff, 6px 6px 0 #000; transform: rotate(-3deg); white-space: nowrap; }
#oob i { font-style: normal; font-size: clamp(90px, 22vw, 230px); line-height: 1; color: #ffe14d; text-shadow: 6px 6px 0 #ff2a4a, 12px 12px 0 #000; margin-top: 6px; }
#oob i.pop { animation: oobnum 0.5s cubic-bezier(0.2, 1.8, 0.4, 1); }
#oob small { font-size: clamp(11px, 1.6vw, 16px); color: #ffd0d8; background: rgba(0, 0, 0, 0.6); padding: 3px 10px; margin-top: 10px; letter-spacing: 1px; }
@keyframes oobpulse { from { box-shadow: inset 0 0 0 10px #ff2a4a, inset 0 0 140px 30px rgba(255, 0, 40, 0.55); } to { box-shadow: inset 0 0 0 16px #ffe14d, inset 0 0 190px 50px rgba(255, 0, 40, 0.75); } }
@keyframes oobnum { from { transform: scale(2.4) rotate(12deg); opacity: 0; } to { transform: scale(1) rotate(0); opacity: 1; } }
`;
const LINES = ['you are leaving the licensed play area', 'your warranty does not cover the outside', 'the outside is a premium feature', 'trespassing fines will be taken from your organs', 'please remain inside the product'];
let el = null, num = null, t0 = 0, shown = -1;
function ensure() {
  if (el) return;
  const st = document.createElement('style'); st.textContent = CSS; document.head.append(st);
  el = document.createElement('div'); el.id = 'oob';
  el.innerHTML = '<b>RETURN TO THE MAP</b><i>3</i><small></small>';
  num = el.querySelector('i');
  (document.getElementById('hud') || document.body).append(el);
}

// every frame
export function oobTick(now) {
  const map = MAPS[MAP.id];
  const out = G.joined && ME.alive && map && map.bounds && outOfBounds(map, ME.pos);
  if (!out) {
    if (t0) { t0 = 0; shown = -1; el.style.display = 'none'; }
    return;
  }
  ensure();
  if (!t0) { t0 = now; el.querySelector('small').textContent = LINES[(Math.random() * LINES.length) | 0]; el.style.display = 'flex'; }
  const left = Math.max(0, OOB.secs - (now - t0) / 1000), k = Math.ceil(left);
  if (k !== shown) {
    shown = k;
    num.textContent = k > 0 ? k : 'BYE';
    num.classList.remove('pop'); void num.offsetWidth; num.classList.add('pop');
    if (k > 0) sfx.oob(k === 1);
  }
}
