// THE PENCIL on the big map (fullmap.js): pick PENCIL (or hold Shift) and drag on the map to draw a route. your side
// sees it on their big map, and faintly on their minimap / royale zone map, for 30 s (the last 5 it fades). WIPE MINE
// rubs out all of yours. The server relays strokes to your side only and caps them (server/pings.js onDraw).
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { MAPS } from '/shared/map.js';
import { DRAW, drawQ, inPingBox } from '/shared/pings.js';
import { FMX, pingCol } from './fullmap.js';
import { mmLayers } from './minimap.js';

const CSS = `
#fmTools { display: flex; gap: 8px; margin: 0 0 7px; align-items: center; flex-wrap: wrap; }
#fmTools button { font: bold 14px var(--font); padding: 2px 10px; background: #fff; color: #000; border: 3px solid #000; box-shadow: 3px 3px 0 #000; cursor: pointer; transform: rotate(-1deg); }
#fmTools button:nth-child(2) { transform: rotate(1.2deg); }
#fmTools button.on { background: #ffe14d; box-shadow: 3px 3px 0 #ff4fd8; }
#fmTools button.red { background: #ff3030; color: #fff; transform: rotate(0.6deg); }
#fmTools button:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 #000; }
#fmTools small { color: #bbb; font-size: 12px; }
#fmPanel.pen #fmCv { cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'%3E%3Cpath d='M2 22 L5 14 L17 2 L22 7 L10 19 Z' fill='%23ffe14d' stroke='black' stroke-width='2'/%3E%3C/svg%3E") 2 22, crosshair; }
@media (max-width: 560px) { #fmTools button { font-size: 12px; padding: 1px 7px; } #fmTools small { display: none; } }
`;
const strokes = new Map(); // id -> { id, by, pts, t, col }
const P = { tool: 'ping', live: null, el: null };

// ------------------------------------------------------------ drawing a stroke
// fewer points: Ramer-Douglas-Peucker on the flat [x, z, ...] list, looser until it fits DRAW.pts
function rdp(pts, eps) {
  const n = pts.length / 2;
  if (n < 3) return pts.slice();
  const keep = new Uint8Array(n); keep[0] = keep[n - 1] = 1;
  const st = [[0, n - 1]];
  while (st.length) {
    const [a, b] = st.pop();
    const ax = pts[a * 2], az = pts[a * 2 + 1], dx = pts[b * 2] - ax, dz = pts[b * 2 + 1] - az, L = Math.hypot(dx, dz) || 1e-9;
    let best = -1, bi = -1;
    for (let i = a + 1; i < b; i++) { const d = Math.abs((pts[i * 2] - ax) * dz - (pts[i * 2 + 1] - az) * dx) / L; if (d > best) { best = d; bi = i; } }
    if (best > eps) { keep[bi] = 1; st.push([a, bi], [bi, b]); }
  }
  const out = [];
  for (let i = 0; i < n; i++) if (keep[i]) out.push(pts[i * 2], pts[i * 2 + 1]);
  return out;
}
export function simplify(pts, span) {
  let eps = Math.max(DRAW.q, span / 500), out = rdp(pts, eps);
  while (out.length > DRAW.pts * 2) { eps *= 1.6; out = rdp(pts, eps); }
  const q = [];
  for (let i = 0; i < out.length; i += 2) { const x = drawQ(out[i]), z = drawQ(out[i + 1]); if (q.length && q[q.length - 2] === x && q[q.length - 1] === z) continue; q.push(x, z); }
  return q;
}
const map = () => MAPS[G.cfg.map];
FMX.wants = (e) => e.button === 0 && (P.tool === 'pen' || e.shiftKey); // (fullmap.js: a left drag that isn't this pans the map)
FMX.down = (e, wx, wz) => {
  if (e.button !== 0 || !(P.tool === 'pen' || e.shiftKey) || !map()) return false;
  P.live = { pts: inPingBox(map(), wx, wz) ? [wx, wz] : [], t: performance.now() };
  sfx.click();
  return true;
};
FMX.move = (e, wx, wz) => {
  const L = P.live;
  if (!L || !inPingBox(map(), wx, wz)) return;
  const n = L.pts.length;
  if (n && Math.hypot(wx - L.pts[n - 2], wz - L.pts[n - 1]) < 0.75) return;
  if (n < 2000) L.pts.push(wx, wz);
};
FMX.up = (e, cancel) => {
  const L = P.live; P.live = null;
  if (!L || cancel || L.pts.length < 4) return;
  const b = map() && map().royale && map().royale.zone0 ? map().royale.zone0[2] * 2 : 300;
  const pts = simplify(L.pts, b);
  if (pts.length >= 4) net.send({ t: 'mdraw', pts });
};

// ------------------------------------------------------------ how strokes look
// a fat felt-tip line: black edge, the drawer's colour, round ends. k = px scale; faint = the minimap's version
function line(x, pts, at, col, k, alpha, faint) {
  if (pts.length < 4) return;
  x.save();
  x.globalAlpha = alpha; x.lineJoin = x.lineCap = 'round';
  x.beginPath();
  for (let i = 0; i < pts.length; i += 2) { const p = at(pts[i], pts[i + 1]); if (i) x.lineTo(p[0], p[1]); else x.moveTo(p[0], p[1]); }
  if (!faint) { x.strokeStyle = '#000'; x.lineWidth = 7 * k; x.stroke(); }
  x.strokeStyle = col; x.lineWidth = (faint ? 2 : 3.5) * k; x.stroke();
  if (!faint) { // an arrow head at the end: which way to go
    const n = pts.length, a = at(pts[n - 4], pts[n - 3]), b = at(pts[n - 2], pts[n - 1]), ang = Math.atan2(b[1] - a[1], b[0] - a[0]), r = 9 * k;
    x.fillStyle = col; x.strokeStyle = '#000'; x.lineWidth = 2 * k;
    x.beginPath(); x.moveTo(b[0] + Math.cos(ang) * r, b[1] + Math.sin(ang) * r); x.lineTo(b[0] + Math.cos(ang + 2.4) * r, b[1] + Math.sin(ang + 2.4) * r); x.lineTo(b[0] + Math.cos(ang - 2.4) * r, b[1] + Math.sin(ang - 2.4) * r); x.closePath(); x.fill(); x.stroke();
  }
  x.restore();
}
const fade = (s, now) => Math.max(0, Math.min(1, (DRAW.life - (now - s.t)) / 5000));
FMX.layers.push((x, toCv, now, dpr) => {
  for (const s of strokes.values()) { const a = fade(s, now); if (a > 0) line(x, s.pts, toCv, s.col, dpr, a, false); }
  if (P.live && P.live.pts.length >= 4) line(x, P.live.pts, toCv, pingCol(G.myId), dpr, 0.75, false); // the one you're drawing
});
mmLayers.push((x, at, now) => { for (const s of strokes.values()) { const a = fade(s, now); if (a > 0) line(x, s.pts, at, s.col, 1, 0.4 * a, true); } });

// ------------------------------------------------------------ the tool buttons
function setTool(t) {
  P.tool = t;
  if (!P.el) return;
  for (const b of P.el.querySelectorAll('[data-t]')) b.classList.toggle('on', b.dataset.t === t);
  const pn = document.getElementById('fmPanel'); if (pn) pn.classList.toggle('pen', t === 'pen');
}
FMX.built.push((panel) => {
  const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
  P.el = document.createElement('div'); P.el.id = 'fmTools';
  P.el.innerHTML = '<button data-t="ping">PING</button><button data-t="pen">PENCIL</button><button class="red" data-wipe="1">WIPE MINE</button><small>shift + drag draws too · lines last 30 s</small>';
  panel.insertBefore(P.el, document.getElementById('fmFoot'));
  P.el.addEventListener('click', (e) => {
    e.stopPropagation();
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.wipe) { net.send({ t: 'mdraw', clr: 1 }); sfx.click(); return; }
    setTool(b.dataset.t); sfx.click();
  });
  setTool(P.tool);
});

// ------------------------------------------------------------ from the server
function gotDraw(m) {
  if (m.no) { hud.msg('SLOW DOWN, PICASSO', 1.2); return; }
  if (m.clr) { for (const s of [...strokes.values()]) if (s.by === m.by) strokes.delete(s.id); return; }
  if (m.gone) strokes.delete(m.gone);
  const p = m.pts;
  if (!Number.isFinite(m.id) || !Array.isArray(p) || p.length < 4 || p.length > DRAW.pts * 2 || !p.every(Number.isFinite)) return;
  const mine = [...strokes.values()].filter((s) => s.by === m.by).sort((a, b) => a.t - b.t);
  while (mine.length >= DRAW.keep) strokes.delete(mine.shift().id); // (the server says gone too: belt and braces)
  strokes.set(m.id, { id: m.id, by: m.by, pts: p, t: performance.now(), col: pingCol(m.by) });
  if (m.by !== G.myId) sfx.mapScribble();
}
let tapped = false;
export function initMapPencil() {
  if (tapped) return;
  tapped = true;
  net.on('mdraw', gotDraw);
  net.tap((m) => { if (m.t === 'welcome') { strokes.clear(); P.live = null; } });
  setInterval(() => { const now = performance.now(); for (const s of [...strokes.values()]) if (now - s.t > DRAW.life || !G.joined) strokes.delete(s.id); }, 1000);
}
export const pencilState = () => ({ strokes, P }); // (tests + the console)
