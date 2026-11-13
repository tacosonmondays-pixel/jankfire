// The pre-game deck, client side (shared/pregame.js has the deck, server/pregame.js the rules). while a mode lobby
// counts down (its info has `pg`) the deck's boxes join BOXES so you walk on it, the fog opens up so the map's there
// in the distance, fire is a shove instead of a shot, items and streaks are off, and the big board shows the top 3.
// the look here is a stand-in (plain boxes + a canvas board): the Blender deck replaces it (PR 2, LOOKS in the shared file).
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { K } from './keys.js';
import { net } from './net.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { W, fireUp } from './weapons.js';
import { sceneryGroup } from './scenery.js';
import { BOXES, MAP, MAPS } from '/shared/map.js';
import { resetGrid } from '/shared/physics.js';
import { PREGAME, padFor, offPad, BOARD_STAT } from '/shared/pregame.js';
import { MODE_STATS, modeBoard } from '/shared/modestats.js';
import { LOBBY } from '/shared/lobby.js';

const S = { on: false, pad: null, info: null, grp: null, board: null, tex: null, rows: null, kind: '', drawn: '', fog: 0, shoveT: 0, bl: -1, map: '', sent: 0, got: 0, hid: [] };
export const pregameOn = () => S.on;
export const pregameInfo = () => (S.on ? { pad: S.pad && S.pad.c, rows: S.rows, boxes: S.pad ? S.pad.boxes.filter((b) => BOXES.includes(b)).length : 0, mesh: !!S.grp, kind: S.kind, shoves: [S.sent, S.got], hid: S.hid.length } : null);

// from the lobby info (welcome, 'lobby', every snapshot's r.warm): a pg = the deck's on. null / end = off
export function pregameSync(info) {
  if (info && !info.end && info.pg) {
    const fresh = !S.on;
    S.info = info; S.kind = info.k || ''; S.on = true; attach();
    if (fresh && S.pad && ME.alive) { ME.yaw = S.pad.face; ME.pitch = 0; } // (arrive looking out at the map)
    if (fresh) fireUp(); // (a trigger held down through the end of the match: let go, or it keeps firing here)
  }
  else if (S.on) off();
}
function attach() {
  const pad = padFor(MAPS[MAP.id]);
  if (!pad) return;
  if (pad !== S.pad) { detach(); S.pad = pad; }
  if ((BOXES.length !== S.bl || MAP.id !== S.map) && !BOXES.includes(pad.boxes[0])) { BOXES.push(...pad.boxes); resetGrid(BOXES); } // (a new map wiped BOXES: back on)
  S.bl = BOXES.length; S.map = MAP.id;
  if (!S.grp || S.grp.parent !== G.scene) build();
  G.noOob = true; // (out of the map's play area is the whole point here)
}
function detach() {
  if (S.pad) {
    let gone = false;
    for (const b of S.pad.boxes) { const i = BOXES.indexOf(b); if (i >= 0) { BOXES.splice(i, 1); gone = true; } }
    if (gone) resetGrid(BOXES);
  }
  if (S.grp) {
    S.grp.parent && S.grp.parent.remove(S.grp);
    S.grp.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose()); } });
    S.grp = null; S.board = null;
  }
  if (S.tex) { S.tex.dispose(); S.tex = null; }
  for (const o of S.hid) o.visible = true; // (the backdrop back)
  S.hid = [];
  S.drawn = ''; S.bl = -1;
}
function off() {
  S.on = false; detach(); S.pad = null; S.info = null; S.rows = null;
  G.noOob = false;
  if (S.fog && G.scene && G.scene.fog) G.scene.fog.far = MAP.fogFar; // (the map's own fog back)
  S.fog = 0;
}

// ---- the stand-in look: the deck's boxes in the game's colours, the board's face a canvas
const COL = { floor: 0x2a1838, rail: 0xffe14d, step: 0x3a2050, board: 0x120818, crate: 0xff4fd8 };
function build() {
  if (!G.scene || !S.pad) return;
  if (S.grp) detach();
  const grp = new THREE.Group(); grp.name = 'pregame';
  for (const b of S.pad.boxes) {
    const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2];
    const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), new THREE.MeshStandardMaterial({ color: COL[b.pg] || 0x888888, roughness: 0.7, metalness: b.pg === 'rail' ? 0.3 : 0 }));
    m.position.set((b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2);
    m.castShadow = b.pg !== 'floor'; m.receiveShadow = true;
    grp.add(m);
  }
  const bd = S.pad.board;
  S.board = new THREE.Mesh(new THREE.PlaneGeometry(9.6, 5.6), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }));
  S.board.position.set(bd.p[0], bd.p[1], bd.p[2] - 0.01); S.board.rotation.y = bd.yaw;
  grp.add(S.board);
  G.scene.add(grp); S.grp = grp; S.drawn = '';
  clearScenery();
  drawBoard();
}
// the backdrop (scenery.js: towers, hills, trees round the map) is only for looking at, so some of it can stand where
// the deck goes: whatever pokes into the deck's space hides while it's up
function clearScenery() {
  const sg = sceneryGroup();
  if (!sg || !S.pad) return;
  const q = new THREE.Box3(new THREE.Vector3(S.pad.lo[0] - 8, S.pad.c[1] - 4, S.pad.lo[2] - 8), new THREE.Vector3(S.pad.hi[0] + 8, S.pad.c[1] + 30, S.pad.hi[2] + 8)), bb = new THREE.Box3();
  sg.updateMatrixWorld(true);
  sg.traverse((o) => { if (o.isMesh && o.visible && !o.isInstancedMesh && bb.setFromObject(o).intersectsBox(q)) { o.visible = false; S.hid.push(o); } });
}
// the big board: TOP 3 in this mode, by its stat. nobody ranked yet: the best of whoever's here
function drawBoard() {
  if (!S.board) return;
  const k = JSON.stringify([S.kind, S.rows]);
  if (k === S.drawn) return; S.drawn = k;
  const c = document.createElement('canvas'); c.width = 1024; c.height = 600;
  const x = c.getContext('2d'), font = getComputedStyle(document.body).getPropertyValue('--font') || 'sans-serif';
  x.fillStyle = '#120818'; x.fillRect(0, 0, 1024, 600);
  x.strokeStyle = '#ff4fd8'; x.lineWidth = 14; x.strokeRect(7, 7, 1010, 586);
  const M = Object.hasOwn(MODE_STATS, S.kind) ? MODE_STATS[S.kind] : MODE_STATS.qp, b = modeBoard(Object.hasOwn(MODE_STATS, S.kind) ? S.kind : 'qp', BOARD_STAT[S.kind] || 'kills');
  const kn = (LOBBY.kinds[S.kind] && LOBBY.kinds[S.kind].name) || M.name;
  x.fillStyle = '#ffe14d'; x.font = `bold 64px ${font}`; x.textAlign = 'center'; x.fillText('TOP 3 IN THIS LOBBY', 512, 92);
  x.fillStyle = '#4fd8ff'; x.font = `bold 34px ${font}`; x.fillText(`${kn} · ${(b ? b.title : 'record').toUpperCase()}`, 512, 142);
  const rows = S.rows || [], medal = ['#ffd84f', '#d8e0ea', '#e09a5a'];
  for (let i = 0; i < 3; i++) {
    const r = rows[i], y = 238 + i * 120;
    x.fillStyle = i % 2 ? '#1e1028' : '#26123a'; x.fillRect(40, y - 70, 944, 104);
    x.fillStyle = medal[i]; x.font = `bold 76px ${font}`; x.textAlign = 'left'; x.fillText(String(i + 1), 66, y + 8);
    if (!r) { x.fillStyle = '#5a4a6a'; x.font = `bold 44px ${font}`; x.fillText('nobody yet', 160, y); continue; }
    x.fillStyle = r.bot ? '#a89ab8' : '#ffffff'; x.font = `bold 52px ${font}`; x.fillText(r.name.slice(0, 18), 160, y);
    x.textAlign = 'right';
    if (r.v == null) { x.fillStyle = '#ff4fd8'; x.font = `bold 40px ${font}`; x.fillText(r.bot ? 'A BOT' : 'UNRANKED', 960, y); }
    else { x.fillStyle = '#7dff4f'; x.font = `bold 56px ${font}`; x.fillText((b && b.pre ? 'R' : '') + r.v.toLocaleString('en-US') + (b && b.unit === 'cr' ? ' cr' : ''), 960, y); }
  }
  if (S.tex) S.tex.dispose();
  S.tex = new THREE.CanvasTexture(c); S.tex.colorSpace = THREE.SRGBColorSpace; S.tex.anisotropy = 4;
  S.board.material.map = S.tex; S.board.material.needsUpdate = true;
}
net.on('pgb', (m) => { if (m && Array.isArray(m.rows)) { S.rows = m.rows.slice(0, 3).filter((r) => r && typeof r.name === 'string'); if (typeof m.k === 'string') S.kind = m.k; drawBoard(); } });
// someone got shoved: a slap and a bonk. you: the screen jolts
net.on('pgs', (m) => {
  S.got++;
  const to = m.to === G.myId ? ME : G.remotes && G.remotes.get(m.to);
  if (to && to.pos) sfx.bonk(to.pos);
  if (m.to === G.myId) { G.shake = Math.max(G.shake || 0, 0.6); hud.msg('SHOVED', 0.9, 'slip'); }
});

// every frame (main.js): the deck stays under you (a new map can wipe BOXES), off the edge = back on, the fog opens up
export function pregameFrame() {
  if (!S.on) return;
  attach();
  const pad = S.pad;
  if (!pad) return;
  W.held = false; // (fire is a shove here: nothing stays held)
  if (ME.alive && offPad(pad, ME.pos)) { // jumped or flew off: straight back on (the server does the same if we don't)
    const s = pad.spawns[Math.floor(Math.random() * pad.spawns.length)];
    ME.pos = [s[0], s[1] + 0.1, s[2]]; ME.vel = [0, 0, 0]; ME.hook = null; ME.yaw = pad.face;
    sfx.bonk(ME.pos); hud.msg('BACK ON THE DECK', 1.2, 'slip');
  }
  const f = G.scene && G.scene.fog;
  if (f) { // the map out there: far enough to see it from the deck
    const B = MAPS[MAP.id] && MAPS[MAP.id].bounds, cx = B ? (B[0] + B[2]) / 2 : 0, cz = B ? (B[1] + B[3]) / 2 : 0;
    const want = Math.hypot(pad.c[0] - cx, pad.c[2] - cz) + 70;
    if (f.far < want) { f.far = want; S.fog = 1; }
  }
}
// a key in game while on the deck: fire shoves whoever's in front of you; items and streaks do nothing. true = ours
export function pregameKey(e) {
  if (!S.on) return false;
  if (K.matches('fire', e)) { if (!e.repeat) shove(); return true; }
  return K.matches(['item', 'streak1', 'streak2', 'streak3'], e);
}
function shove() {
  const n = performance.now();
  if (!ME.alive || n - S.shoveT < PREGAME.shove.cd) return;
  S.shoveT = n;
  const fx = -Math.sin(ME.yaw), fz = -Math.cos(ME.yaw);
  let best = null, bd = PREGAME.shove.range;
  for (const r of (G.remotes ? G.remotes.values() : [])) {
    if (!r.alive) continue;
    const dx = r.pos[0] - ME.pos[0], dz = r.pos[2] - ME.pos[2], d = Math.hypot(dx, dz);
    if (d < bd && Math.abs(r.pos[1] - ME.pos[1]) < 2.5 && (d < 0.8 || (dx * fx + dz * fz) / d > 0.35)) { bd = d; best = r; }
  }
  sfx.swing(ME.pos);
  if (best) { net.send({ t: 'shove', to: best.id }); S.sent++; }
}
