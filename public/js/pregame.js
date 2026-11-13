// The pre-game deck, client side (shared/pregame.js has the deck, server/pregame.js the rules). while a mode lobby
// counts down (its info has `pg`) the deck's boxes join BOXES so you walk on it, the fog opens up so the map's there
// in the distance, fire is a shove instead of a shot, items and streaks are off, and the big board shows the top 3.
// the look is a Blender model (x_lobby_<look>.glb, the look of the week: LOOKS in the shared file): plain boxes stand in
// till it lands (or if it's missing). the top 3 stand on its podiums in their own outfits; its fans spin, balloons bob.
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { K } from './keys.js';
import { net } from './net.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { sceneryGroup } from './scenery.js';
import { buildCharacter, freeTree } from './models.js';
import { idlePose } from './loco.js';
import { authored, want, whenGlb, missingGlb } from './glbkit.js';
import { DEFAULT_LOOK } from '/shared/looks.js';
import { BOXES, MAP, MAPS } from '/shared/map.js';
import { resetGrid } from '/shared/physics.js';
import { PREGAME, padFor, offPad, BOARD_STAT, LOOKS } from '/shared/pregame.js';
import { MODE_STATS, modeBoard } from '/shared/modestats.js';
import { LOBBY } from '/shared/lobby.js';

const S = { on: false, pad: null, info: null, grp: null, board: null, tex: null, rows: null, kind: '', drawn: '', fog: 0, shoveT: 0, bl: -1, map: '', sent: 0, got: 0, hid: [], glb: null, fans: [], balloons: [], pods: [], podKey: '', screenMat: null };
export const pregameOn = () => S.on;
export const pregameInfo = () => (S.on ? { pad: S.pad && S.pad.c, rows: S.rows, boxes: S.pad ? S.pad.boxes.filter((b) => BOXES.includes(b)).length : 0, mesh: !!S.grp, kind: S.kind, shoves: [S.sent, S.got], hid: S.hid.length, glb: S.glb ? S.glb.userData.glbId : null, pods: S.pods.length } : null);

// from the lobby info (welcome, 'lobby', every snapshot's r.warm): a pg = the deck's on. null / end = off
export function pregameSync(info) {
  if (info && !info.end && info.pg) {
    const fresh = !S.on;
    S.info = info; S.kind = info.k || ''; S.on = true; attach();
    if (fresh && S.pad && ME.alive) { ME.yaw = S.pad.face; ME.pitch = 0; } // (arrive looking out at the map)
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
    clearPods();
    S.grp.traverse((o) => { if (o.isMesh && o.userData.pgOwn) { o.geometry.dispose(); o.material.dispose(); } }); // (the glb's geometry and materials are shared with its cache: left alone)
    if (S.screenMat) { S.screenMat.dispose(); S.screenMat = null; }
    S.grp = null; S.board = null; S.glb = null; S.fans = []; S.balloons = [];
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

// ---- the look: the Blender deck for this week's look, placed on the deck's centre. not loaded (yet): plain boxes in
// the game's colours stand in, and it swaps in when the model lands
const COL = { floor: 0x2a1838, rail: 0xffe14d, board: 0x120818, crate: 0xff4fd8, podium: 0x4fd8ff, pole: 0x3a3c46 };
const lookId = () => { const l = S.info && S.info.pg && S.info.pg.look; return 'x_lobby_' + (LOOKS.some((x) => x.id === l) ? l : LOOKS[0].id); };
function build() {
  if (!G.scene || !S.pad) return;
  if (S.grp) detach();
  const grp = new THREE.Group(); grp.name = 'pregame';
  const id = lookId(), a = authored(id), bd = S.pad.board;
  S.screenMat = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false });
  if (a) {
    const o = a.obj; o.position.set(...S.pad.c); grp.add(o); S.glb = o;
    o.traverse((m) => { if (m.isMesh) { m.castShadow = !/screen/.test(m.name); m.receiveShadow = true; } });
    S.board = o.getObjectByName('screen');
    if (S.board) S.board.material = S.screenMat;
    S.fans = ((a.meta && a.meta.fans) || []).map((n) => o.getObjectByName(n)).filter(Boolean);
    S.balloons = ((a.meta && a.meta.balloons) || []).map((n) => o.getObjectByName(n)).filter(Boolean).map((b) => ({ o: b, y: b.position.y, r: b.rotation.z }));
  } else {
    for (const b of S.pad.boxes) {
      const sx = b.max[0] - b.min[0], sy = b.max[1] - b.min[1], sz = b.max[2] - b.min[2];
      const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), new THREE.MeshStandardMaterial({ color: COL[b.pg] || 0x888888, roughness: 0.7, metalness: b.pg === 'rail' ? 0.3 : 0 }));
      m.position.set((b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2);
      m.castShadow = b.pg !== 'floor'; m.receiveShadow = true; m.userData.pgOwn = 1;
      grp.add(m);
    }
    if (missingGlb(id)) { want(id, 3); whenGlb([id], () => { if (S.on && S.grp === grp && authored(id)) build(); }); } // (the real deck, as soon as it's here)
  }
  if (!S.board) { S.board = new THREE.Mesh(new THREE.PlaneGeometry(bd.w, bd.h), S.screenMat); S.board.userData.pgOwn = 0; S.board.position.set(...bd.p); S.board.rotation.y = bd.yaw; grp.add(S.board); }
  G.scene.add(grp); S.grp = grp; S.drawn = ''; S.podKey = '';
  clearScenery();
  drawBoard();
}
// the top 3 on their podiums, in their own outfits (you: your saved look). 1st has both arms up, 2nd waves one, 3rd
// stands there. rebuilt when the board changes (whoever's gone: their character goes too)
function clearPods() { for (const p of S.pods) { p.ch.root.parent && p.ch.root.parent.remove(p.ch.root); freeTree(p.ch.root); } S.pods = []; }
function podiums() {
  if (!S.grp || !S.pad) return;
  const rows = S.rows || [], k = JSON.stringify(rows.map((r) => r.id));
  if (k === S.podKey) return;
  S.podKey = k; clearPods();
  rows.slice(0, 3).forEach((r, i) => {
    let color, look;
    if (r.id === G.myId) { color = G.myColor; look = { ...DEFAULT_LOOK, ...((G.settings && G.settings.look) || {}) }; }
    else { const rm = G.remotes && G.remotes.get(r.id); if (!rm) return; color = rm.color; look = { ...DEFAULT_LOOK, ...(rm.outfit || {}) }; }
    let ch;
    try { ch = buildCharacter(color || '#ff4fd8', look); } catch { return; }
    ch.root.scale.setScalar(1.2); // (game size, like everyone else)
    ch.root.position.set(...S.pad.podiums[i]);
    ch.root.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    S.grp.add(ch.root); S.pods.push({ ch, i, t0: i * 1.7 });
  });
  if (S.pods.length < Math.min(3, rows.length)) S.podKey = ''; // (someone's not in the room list yet: try again in a second)
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
  const c = document.createElement('canvas'); c.width = 1024; c.height = 404; // (the screen's shape: 9.6 x 3.8)
  const x = c.getContext('2d'), font = getComputedStyle(document.body).getPropertyValue('--font') || 'sans-serif';
  x.fillStyle = '#120818'; x.fillRect(0, 0, 1024, 404);
  const M = Object.hasOwn(MODE_STATS, S.kind) ? MODE_STATS[S.kind] : MODE_STATS.qp, b = modeBoard(Object.hasOwn(MODE_STATS, S.kind) ? S.kind : 'qp', BOARD_STAT[S.kind] || 'kills');
  const kn = (LOBBY.kinds[S.kind] && LOBBY.kinds[S.kind].name) || M.name;
  x.fillStyle = '#ffe14d'; x.font = `bold 50px ${font}`; x.textAlign = 'center'; x.fillText('TOP 3 IN THIS LOBBY', 512, 56);
  x.fillStyle = '#4fd8ff'; x.font = `bold 28px ${font}`; x.fillText(`${kn} · ${(b ? b.title : 'record').toUpperCase()}`, 512, 94);
  const rows = S.rows || [], medal = ['#ffd84f', '#d8e0ea', '#e09a5a'];
  for (let i = 0; i < 3; i++) {
    const r = rows[i], y = 170 + i * 90;
    x.fillStyle = i % 2 ? '#1e1028' : '#26123a'; x.fillRect(30, y - 56, 964, 82);
    x.fillStyle = medal[i]; x.font = `bold 64px ${font}`; x.textAlign = 'left'; x.fillText(String(i + 1), 56, y + 8);
    if (!r) { x.fillStyle = '#5a4a6a'; x.font = `bold 44px ${font}`; x.fillText('nobody yet', 160, y); continue; }
    x.fillStyle = r.bot ? '#a89ab8' : '#ffffff'; x.font = `bold 52px ${font}`; x.fillText(r.name.slice(0, 18), 160, y);
    x.textAlign = 'right';
    if (r.v == null) { x.fillStyle = '#ff4fd8'; x.font = `bold 40px ${font}`; x.fillText(r.bot ? 'A BOT' : 'UNRANKED', 960, y); }
    else { x.fillStyle = '#7dff4f'; x.font = `bold 56px ${font}`; x.fillText((b && b.pre ? 'R' : '') + r.v.toLocaleString('en-US') + (b && b.unit === 'cr' ? ' cr' : ''), 960, y); }
  }
  if (S.tex) S.tex.dispose();
  S.tex = new THREE.CanvasTexture(c); S.tex.colorSpace = THREE.SRGBColorSpace; S.tex.anisotropy = 4;
  S.board.material.map = S.tex; S.board.material.needsUpdate = true;
  podiums();
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
  if (ME.alive && offPad(pad, ME.pos)) { // jumped or flew off: straight back on (the server does the same if we don't)
    const s = pad.spawns[Math.floor(Math.random() * pad.spawns.length)];
    ME.pos = [s[0], s[1] + 0.1, s[2]]; ME.vel = [0, 0, 0]; ME.hook = null; ME.yaw = pad.face;
    sfx.bonk(ME.pos); hud.msg('BACK ON THE DECK', 1.2, 'slip');
  }
  const t = performance.now() / 1000;
  for (const [i, f] of S.fans.entries()) f.rotation.y = t * (9 + i * 0.7) * (i % 2 ? -1 : 1); // the fans under the deck
  for (const [i, b] of S.balloons.entries()) { b.o.position.y = b.y + Math.sin(t * 1.1 + i * 2) * 0.25; b.o.rotation.z = b.r + Math.sin(t * 0.7 + i) * 0.06; }
  if (!S.podKey && t - (S.podT || 0) > 1) { S.podT = t; podiums(); }
  for (const p of S.pods) { // the top 3 showing off
    const ch = p.ch, tt = t + p.t0; idlePose(ch, tt);
    if (p.i === 0) { const pump = 1.9 + Math.sin(tt * 6) * 0.35; ch.arm.rotation.x = pump; ch.armL.rotation.x = pump; ch.body.position.y = Math.abs(Math.sin(tt * 3)) * 0.08; }
    else if (p.i === 1) { ch.arm.rotation.x = 2.0; ch.arm.rotation.z = Math.sin(tt * 4) * 0.4; ch.armL.rotation.x = -0.9; }
    else { ch.arm.rotation.x = -1.0; ch.armL.rotation.x = -1.0; }
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
