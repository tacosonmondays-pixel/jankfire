// The HUD minimap ("SAT-NAV"), every mode and map. The map from above is painted once per map onto a canvas from its
// boxes (higher = brighter, walls get a cyan edge), then each frame only that picture is moved / turned under you and
// the markers drawn on top: no extra WebGL pass. Jank Royale keeps its own zone map but paints it with paintBoxes too.
// Markers: you, teammates, Plant & Defuse sites + the bomb (when your side would know), enemy pings when they fire
// (not in Plant & Defuse), everyone during a spy satellite. Settings: on/off, size S/M/L, rotate with you or north up.
import { G } from './ctx.js';
import { net } from './net.js';
import { ME } from './player.js';
import { RP } from './replay.js';
import { MAPS } from '/shared/map.js';
import { TEAMS } from '/shared/modes.js';

const SIZES = { s: [124, 36], m: [164, 46], l: [216, 58] }; // [px, metres from the middle to the edge]
const CSS = `
#mmWrap { position: absolute; left: 16px; top: 46px; display: none; transform: rotate(-1.2deg); pointer-events: none; font-family: var(--font); }
#mmWrap canvas { display: block; border: 3px solid #ff4fd8; box-shadow: 5px 5px 0 #4fd8ff; background: #0c0614; image-rendering: pixelated; }
#mmTag { position: absolute; left: -6px; top: -13px; background: #ffe14d; color: #000; border: 2px solid #000; box-shadow: 2px 2px 0 #000; font-size: 13px; line-height: 15px; font-weight: bold; padding: 0 6px; transform: rotate(-1.5deg); letter-spacing: 1.5px; white-space: nowrap; }
#mmN { position: absolute; right: -7px; top: -9px; width: 16px; height: 16px; line-height: 15px; text-align: center; background: #000; color: #ff4fd8; border: 2px solid #ff4fd8; font-size: 10px; font-weight: bold; }
body.mmOn #airInd { top: calc(var(--mmB, 220px) + 10px) !important; }
body.mmOn #nowPlaying.match { top: calc(var(--mmB, 220px) + 12px); } /* the song toast sits under the map, not on it */
body.mmOn #ecoPay { top: max(27%, calc(var(--mmB, 220px) + 14px)) !important; }
`;

// ------------------------------------------------------------ the picture, shared with royale.js
// how far a map goes: its bounds if it has them, else its boxes (scenery past the play area is cut at 320 m)
export function mapExtent(map) {
  if (map.royale && map.royale.zone0) { const [cx, cz, r] = map.royale.zone0; return [cx - r * 1.05, cz - r * 1.05, cx + r * 1.05, cz + r * 1.05]; }
  if (map.bounds) { const b = map.bounds; return [b[0] - 6, b[1] - 6, b[2] + 6, b[3] + 6]; }
  let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9;
  for (const b of map.boxes) { if (b.noCol) continue; x0 = Math.min(x0, b.min[0]); z0 = Math.min(z0, b.min[2]); x1 = Math.max(x1, b.max[0]); z1 = Math.max(z1, b.max[2]); }
  const c = (v) => Math.max(-320, Math.min(320, v));
  return [c(x0) - 4, c(z0) - 4, c(x1) + 4, c(z1) + 4];
}
// the height band people play in: from the lowest spawn down a bit, up to the highest spawn + a floor or two
function playBand(map) {
  const ys = (map.spawns || []).map((s) => (Array.isArray(s) ? s[1] : s && s.p ? s.p[1] : 0)).filter(Number.isFinite);
  const lo = ys.length ? Math.min(...ys) : 0, hi = ys.length ? Math.max(...ys) : 0;
  return { floor: lo, top: Math.min(hi + 7.5, map.ceiling ? map.ceiling + lo - 0.3 : 1e9), head: hi + 3.2, deep: lo - 8 };
}
const ROAD = new Set(['road', 'asphalt', 'dirtroad']), GREEN = new Set(['grass', 'moss', 'hedge', 'leaves']), SAND = new Set(['sand', 'dirt']);
const NEON = (b, k) => (ROAD.has(b.mat) ? '#3a3046' : GREEN.has(b.mat) ? `hsl(120, 38%, ${20 + k * 22}%)` : SAND.has(b.mat) ? `hsl(35, 38%, ${22 + k * 22}%)` : `hsl(${285 - k * 95}, ${40 + k * 30}%, ${24 + k * 40}%)`);
const ROYALE = (b, k) => (ROAD.has(b.mat) ? '#7a5a3a' : b.mat === 'grass' ? '#3f7a32' : SAND.has(b.mat) ? '#c9a36a' : `hsl(${300 - k * 40}, ${30 + k * 30}%, ${30 + k * 35}%)`);
// paint the boxes of a map, lowest first, so roofs and walls end up on top. toMap(wx, wz) -> [px, py] on x
export function paintBoxes(x, map, toMap, S, opt = {}) {
  const band = playBand(map), royale = opt.style === 'royale';
  const boxes = map.boxes.filter((b) => !b.noCol && (royale ? b.max[1] > -3 && b.max[1] < 60 : b.max[1] > band.deep && b.min[1] < band.top && !(b.min[1] > band.head && b.max[1] - b.min[1] < 1.2))).sort((a, b) => a.max[1] - b.max[1]);
  for (const b of boxes) {
    const [px0, pz0] = toMap(b.min[0], b.min[2]), [px1, pz1] = toMap(b.max[0], b.max[2]);
    if (px1 < 0 || pz1 < 0 || px0 > S || pz0 > S) continue;
    const k = royale ? Math.max(0, Math.min(1, (b.max[1] + 2) / 14)) : Math.max(0, Math.min(1, (b.max[1] - band.floor + 1) / 12));
    x.fillStyle = (royale ? ROYALE : NEON)(b, k);
    const w = Math.max(1, px1 - px0), h = Math.max(1, pz1 - pz0);
    x.fillRect(px0, pz0, w, h);
    if (!royale && !b.ter && b.max[1] - b.min[1] > 1.6 && b.max[1] > band.floor + 1.2) { x.strokeStyle = 'rgba(79,216,255,0.55)'; x.lineWidth = 1; x.strokeRect(px0 + 0.5, pz0 + 0.5, w - 1, h - 1); } // walls + buildings: a cyan edge
  }
}

// ------------------------------------------------------------ the HUD minimap
let wrap = null, cv = null, base = null, baseFor = '', ext = null, ppm = 1, drawT = 0, shownSize = '';
const pings = new Map(); // id -> [x, z, time]: enemies that just fired
function build() {
  const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
  wrap = document.createElement('div'); wrap.id = 'mmWrap';
  wrap.innerHTML = '<canvas id="mmCv"></canvas><div id="mmTag">SAT-NAV</div><div id="mmN">N</div>';
  (document.getElementById('hud') || document.body).appendChild(wrap);
  cv = wrap.querySelector('canvas');
}
function bake(id) {
  const map = MAPS[id];
  ext = mapExtent(map);
  const w = ext[2] - ext[0], h = ext[3] - ext[1];
  ppm = Math.min(4, 1600 / Math.max(w, h));
  const c = document.createElement('canvas'); c.width = Math.ceil(w * ppm); c.height = Math.ceil(h * ppm);
  const x = c.getContext('2d');
  paintBoxes(x, map, (wx, wz) => [(wx - ext[0]) * ppm, (wz - ext[1]) * ppm], Math.max(c.width, c.height));
  if (map.bounds) { const b = map.bounds; x.strokeStyle = '#ff4fd8'; x.lineWidth = Math.max(2, ppm * 0.6); x.setLineDash([ppm * 3, ppm * 2]); x.strokeRect((b[0] - ext[0]) * ppm, (b[1] - ext[1]) * ppm, (b[2] - b[0]) * ppm, (b[3] - b[1]) * ppm); x.setLineDash([]); } // the edge of the play area
  base = c; baseFor = id;
}

// off the map: a dark void grid with hatching and a few dead pixels, pinned to the world so it slides as you move
let voidPat = null;
function voidPattern(x) {
  if (voidPat) return voidPat;
  const t = document.createElement('canvas'); t.width = t.height = 32;
  const g = t.getContext('2d');
  g.fillStyle = '#0a0412'; g.fillRect(0, 0, 32, 32);
  g.strokeStyle = '#1b0c2c'; g.lineWidth = 3;
  for (let i = -32; i < 64; i += 8) { g.beginPath(); g.moveTo(i, 32); g.lineTo(i + 32, 0); g.stroke(); } // hatching
  g.fillStyle = '#3a1858'; g.fillRect(0, 0, 32, 1); g.fillRect(0, 0, 1, 32); // the grid
  g.fillStyle = '#5a2a80'; for (const [a, b] of [[5, 21], [19, 9], [27, 26], [12, 14]]) g.fillRect(a, b, 1, 1); // dead pixels
  voidPat = x.createPattern(t, 'repeat');
  return voidPat;
}

let tapped = false;
export function initMinimap() {
  if (tapped) return;
  tapped = true;
  build();
  // a shot from someone else: an enemy ping for a moment (who counts as an enemy is decided when it's drawn)
  net.tap((m) => {
    if (m.t === 'fx' && m.k === 'shot' && m.id && m.id !== G.myId) { const r = G.remotes.get(m.id); if (r) pings.set(m.id, [r.pos[0], r.pos[2], performance.now()]); }
    else if (m.t === 'welcome') pings.clear();
  });
}

const ally = (r) => (G.myTeam ? r.team === G.myTeam : (G.mode === 'coop' || G.game === 'zombies') && !r.bot);
const bombGame = () => !!(G.round && G.round.game === 'bomb' && G.round.bomb);
// hidden: off in settings, not in a match, in a replay / killcam, dead, story mode, royale (its own map), the end screen
function wanted(opts) {
  const S = G.settings;
  return S.mmOn !== false && G.joined && !RP.active && !G.killcamPending && ME.alive && !G.story && !opts.royale && !opts.endscreen && MAPS[G.cfg.map];
}

export function minimapFrame(now, opts = {}) {
  if (!wrap) return;
  const S = G.settings, bm = document.getElementById('brMap');
  if (bm) { const px = SIZES[S.mmSize] ? SIZES[S.mmSize][0] + 12 : 176; bm.style.display = S.mmOn === false ? 'none' : ''; bm.style.width = bm.style.height = px + 'px'; } // royale's zone map follows the settings
  const on = !!wanted(opts);
  if (!on) { if (wrap.style.display !== 'none') { wrap.style.display = 'none'; document.body.classList.remove('mmOn'); } return; }
  if (now - drawT < 45) return; // ~20 fps is plenty
  drawT = now;
  const [px, R0] = SIZES[S.mmSize] || SIZES.m;
  if (shownSize !== S.mmSize || wrap.style.display !== 'block') {
    shownSize = S.mmSize; cv.width = cv.height = px; wrap.style.display = 'block';
    document.body.classList.add('mmOn'); document.body.style.setProperty('--mmB', `${46 + px + 8}px`);
  }
  if (baseFor !== G.cfg.map) bake(G.cfg.map);
  const R = Math.min(R0, Math.max(16, Math.max(ext[2] - ext[0], ext[3] - ext[1]) * 0.42)); // small maps (Crate) zoom in so the map fills the frame
  const x = cv.getContext('2d'), rot = S.mmRot !== false, yaw = ME.yaw || 0, s = px / (2 * R), mx = ME.pos[0], mz = ME.pos[2];
  wrap.querySelector('#mmN').style.transform = rot ? `rotate(${yaw}rad)` : '';
  x.setTransform(1, 0, 0, 1, 0, 0);
  x.save(); x.translate(px / 2, px / 2); if (rot) x.rotate(yaw); x.scale(s, s); x.translate(-mx, -mz);
  const vp = voidPattern(x); vp.setTransform(new DOMMatrix().scale(0.25)); // a 32 px tile = 8 m
  x.fillStyle = vp; x.fillRect(mx - R * 1.5, mz - R * 1.5, R * 3, R * 3);
  x.imageSmoothingEnabled = false;
  x.drawImage(base, ext[0], ext[1], base.width / ppm, base.height / ppm);
  x.restore();
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const at = (wx, wz) => { const dx = (wx - mx) * s, dz = (wz - mz) * s; return rot ? [px / 2 + dx * cy - dz * sy, px / 2 + dx * sy + dz * cy] : [px / 2 + dx, px / 2 + dz]; };
  const edge = ([a, b]) => [Math.max(7, Math.min(px - 7, a)), Math.max(7, Math.min(px - 7, b))]; // objectives stay on the rim when far
  const dot = (p, col, r = 3.5) => { x.fillStyle = col; x.strokeStyle = '#000'; x.lineWidth = 2; x.beginPath(); x.arc(p[0], p[1], r, 0, 7); x.stroke(); x.fill(); };
  // Plant & Defuse: the sites and the bomb
  const bomb = bombGame() && G.round.bomb, map = MAPS[G.cfg.map];
  if (bomb && map.sites) {
    x.font = 'bold 11px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
    for (const st of map.sites) {
      const p = edge(at((st.min[0] + st.max[0]) / 2, (st.min[2] + st.max[2]) / 2)), hot = bomb.ph === 'planted' && bomb.site === st.id;
      x.fillStyle = hot ? '#ff3030' : '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2; x.fillRect(p[0] - 7, p[1] - 7, 14, 14); x.strokeRect(p[0] - 7, p[1] - 7, 14, 14);
      x.fillStyle = '#000'; x.fillText(st.id, p[0], p[1] + 1);
    }
    const att = G.myTeam && G.myTeam === bomb.att, bp = bomb.p || (att && bomb.drop);
    if (bp && Math.sin(now / 110) > -0.3) dot(edge(at(bp[0], bp[2])), bomb.p ? '#ff3030' : '#ffb04f', 4.5);
  }
  // people: teammates always, enemies on a spy satellite, or for a moment after they fire (never in Plant & Defuse)
  const sat = now < (G.satUntil || 0);
  for (const r of G.remotes.values()) {
    if (!r.alive || (r.bot && r.name === 'Dummy' && G.mode !== 'training')) continue;
    if (ally(r)) {
      const p = at(r.pos[0], r.pos[2]);
      if (p[0] < 0 || p[1] < 0 || p[0] > px || p[1] > px) continue;
      dot(p, TEAMS[r.team] ? TEAMS[r.team].color : '#4fd8ff');
      if (bomb && bomb.carrier === r.id) { x.strokeStyle = '#ffb04f'; x.lineWidth = 2; x.beginPath(); x.arc(p[0], p[1], 6.5, 0, 7); x.stroke(); }
      continue;
    }
    const pg = pings.get(r.id), age = pg ? now - pg[2] : 1e9;
    if (sat) dot(at(r.pos[0], r.pos[2]), '#ff3030', 3.5);
    else if (!bomb && age < 1600) { x.globalAlpha = 1 - age / 1600; dot(at(pg[0], pg[1]), '#ff3030', 3.5 + (age < 200 ? 2 : 0)); x.globalAlpha = 1; }
  }
  // you: the arrow
  x.save(); x.translate(px / 2, px / 2); if (!rot) x.rotate(-yaw);
  x.fillStyle = '#ffe14d'; x.strokeStyle = '#000'; x.lineWidth = 2;
  x.beginPath(); x.moveTo(0, -7); x.lineTo(5, 5); x.lineTo(0, 2); x.lineTo(-5, 5); x.closePath(); x.stroke(); x.fill(); x.restore();
}
