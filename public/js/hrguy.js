// The Tall Guy From HR, what you see and hear (the server decides everything: server/hrguy.js, rules in shared/hr.js).
// He's 3.5 m of cheap grey suit and no face: long legs, arms down past his knees, a red tie, a lanyard with a badge,
// a clipboard, a bluetooth earpiece blinking. He never moves while watched, so he's never animated: every time he
// blinks closer he's just standing there in a slightly different, slightly worse pose.
// Staring at him: static over your screen, the picture shakes, a hiss gets louder. Near you: a low drone (even behind you).
import * as THREE from 'three';
import { G } from './ctx.js';
import { ME } from './player.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx, hrLevel } from './audio.js';
import { MAP, MAPS } from '/shared/map.js';
import { HR, HR_LINES, hrSight } from '/shared/hr.js';
import { PH } from '/shared/physics.js';
import { nvOn } from './goggles.js';
import { AUTHORED, LAZY, authored, nodeIn, prefetch, whenLate } from './glbkit.js';

const $ = (id) => document.getElementById(id);
const pick = (a) => a[(Math.random() * a.length) | 0];
const S = { on: false, p: null, yaw: 0, pose: 0, tg: 0, st: 0, stShow: 0, near: 0, called: 0, take: 0, mesh: null, nvg: false, code: false }; // code: tests draw the box version

// ------------------------------------------------------------ the model
function badgeTex() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 88;
  const g = c.getContext('2d');
  g.fillStyle = '#f4f2ec'; g.fillRect(0, 0, 64, 88);
  g.fillStyle = '#2a6cff'; g.fillRect(0, 0, 64, 16);
  g.fillStyle = '#fff'; g.font = 'bold 11px Arial'; g.textAlign = 'center'; g.fillText('☺ CORP', 32, 12);
  g.fillStyle = '#cfcac0'; g.fillRect(14, 22, 36, 32); // the photo: an egg
  g.fillStyle = '#ece8e0'; g.beginPath(); g.ellipse(32, 40, 10, 13, 0, 0, 7); g.fill();
  g.fillStyle = '#4a5060'; g.fillRect(18, 50, 28, 4);
  g.fillStyle = '#120818'; g.font = 'bold 16px Arial'; g.fillText('HR', 32, 72);
  g.font = '8px Arial'; g.fillText("hi! i'm from HR", 32, 83);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.NearestFilter;
  return t;
}
const MATS = {};
function mats() {
  if (MATS.suit) return MATS;
  const lam = (color, o = {}) => new THREE.MeshLambertMaterial({ color, ...o });
  Object.assign(MATS, {
    suit: new THREE.MeshPhongMaterial({ color: 0x565c6c, shininess: 30, specular: 0x30343c }), // a cheap sheen
    suitDark: lam(0x3a3f4c), pants: lam(0x2c2f38), shoe: new THREE.MeshPhongMaterial({ color: 0x0c0c0e, shininess: 90, specular: 0x888888 }),
    shirt: lam(0xe8e8ea, { emissive: 0x1a1a1c }), tie: lam(0xb81a26), strap: lam(0x2a6cff, { emissive: 0x081840 }),
    skin: lam(0xe6e0d6, { emissive: 0x56524c }), // pale, a little bit lit from nowhere: that's what you spot between the trees
    badge: new THREE.MeshLambertMaterial({ map: badgeTex(), emissive: 0x0a0a0a }), clip: lam(0x6a4a2a), paper: lam(0xf4f2ec, { emissive: 0x1a1a1a }),
    ear: new THREE.MeshBasicMaterial({ color: 0x19a8ff }), dark: lam(0x111114),
  });
  return MATS;
}
function part(parent, geo, mat, x, y, z) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); parent.add(m); return m; }
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
// front is -z (like the players' mannequins): he turns to face whoever he's after
function buildHR() {
  const M = mats(), g = new THREE.Group(), body = new THREE.Group();
  g.add(body);
  // legs: far too long, a crease down the front, shiny shoes
  const legs = [];
  for (const s of [-1, 1]) {
    const L = new THREE.Group(); L.position.set(s * 0.11, 1.86, 0); body.add(L); legs.push(L);
    part(L, box(0.14, 0.95, 0.16), M.pants, 0, -0.47, 0);
    part(L, box(0.12, 0.92, 0.14), M.pants, 0, -1.38, 0.0);
    part(L, box(0.02, 1.8, 0.01), M.suitDark, 0, -0.92, -0.08);
    part(L, box(0.13, 0.09, 0.36), M.shoe, 0, -1.8, -0.08);
  }
  // the jacket: narrow at the waist, shoulder pads that think they're in charge
  part(body, box(0.42, 0.52, 0.24), M.suit, 0, 2.12, 0);
  part(body, box(0.54, 0.6, 0.26), M.suit, 0, 2.66, 0);
  for (const s of [-1, 1]) part(body, box(0.16, 0.08, 0.28), M.suit, s * 0.3, 2.95, 0);
  part(body, box(0.44, 0.14, 0.25), M.suitDark, 0, 1.9, 0); // the jacket's hem
  part(body, box(0.16, 0.44, 0.02), M.shirt, 0, 2.74, -0.135); // the shirt in the V
  for (const s of [-1, 1]) { const lap = part(body, box(0.09, 0.42, 0.02), M.suitDark, s * 0.1, 2.75, -0.142); lap.rotation.z = s * 0.28; }
  part(body, box(0.07, 0.07, 0.03), M.tie, 0, 2.93, -0.15); // the knot
  const tie = part(body, box(0.06, 0.5, 0.02), M.tie, 0, 2.64, -0.152); tie.rotation.z = 0.04;
  part(body, box(0.09, 0.08, 0.02), M.tie, 0.01, 2.37, -0.152);
  for (const y of [2.3, 2.12]) part(body, box(0.03, 0.03, 0.01), M.dark, 0, y, -0.124);
  // the lanyard: two straps down from the collar to a badge on his chest
  for (const s of [-1, 1]) { const st = part(body, box(0.025, 0.5, 0.01), M.strap, s * 0.07, 2.72, -0.16); st.rotation.z = -s * 0.12; }
  part(body, box(0.05, 0.04, 0.02), M.dark, 0, 2.47, -0.165);
  part(body, box(0.15, 0.2, 0.012), M.badge, 0, 2.35, -0.17);
  // neck and head: a smooth pale egg, nothing on it. and a bluetooth earpiece
  part(body, box(0.1, 0.16, 0.1), M.skin, 0, 3.02, 0);
  const head = new THREE.Group(); head.position.set(0, 3.08, 0); body.add(head);
  const egg = part(head, new THREE.SphereGeometry(1, 9, 7), M.skin, 0, 0.25, 0); egg.scale.set(0.19, 0.27, 0.21);
  part(head, box(0.04, 0.07, 0.05), M.dark, 0.19, 0.24, -0.02);
  const ear = part(head, box(0.02, 0.02, 0.02), M.ear, 0.215, 0.27, -0.04);
  // arms: from the shoulder pads all the way down past his knees, long fingers
  const arms = [];
  for (const s of [-1, 1]) {
    const A = new THREE.Group(); A.position.set(s * 0.33, 2.9, 0); body.add(A); arms.push(A);
    part(A, box(0.11, 0.78, 0.12), M.suit, 0, -0.39, 0);
    const F = new THREE.Group(); F.position.set(0, -0.78, 0); A.add(F);
    part(F, box(0.1, 0.74, 0.11), M.suit, 0, -0.37, 0);
    part(F, box(0.11, 0.06, 0.12), M.shirt, 0, -0.73, 0); // shirt cuff
    part(F, box(0.08, 0.16, 0.06), M.skin, 0, -0.84, 0);
    for (let i = 0; i < 4; i++) part(F, box(0.016, 0.24 + (i === 1 || i === 2 ? 0.05 : 0), 0.016), M.skin, -0.03 + i * 0.02, -1.04, -0.01);
    A.userData.fore = F;
  }
  // the clipboard, in his right hand
  const clip = new THREE.Group(); clip.position.set(0, -0.92, -0.05); arms[1].userData.fore.add(clip);
  part(clip, box(0.24, 0.32, 0.015), M.clip, 0, -0.12, 0);
  part(clip, box(0.2, 0.26, 0.004), M.paper, 0, -0.14, -0.01);
  part(clip, box(0.08, 0.03, 0.025), M.dark, 0, 0.03, -0.005);
  clip.rotation.x = -0.15;
  g.userData = { body, head, arms, legs, ear, clip };
  return g;
}
// the Blender one (tools/blender/make_hrguy.py, x_hrguy.glb): built on the same rig, an empty per joint at the same spot
// with the same parents (hr_body > hr_head, hr_armL > hr_foreL, hr_armR > hr_foreR > hr_clip, hr_legL...), so pose()
// turns the same nodes and nothing else changes. the badge's card gets our canvas (it still flashes in your
// flashlight), the earpiece's LED is what blinks. downloaded once you're on a map he haunts; the boxes until it lands
const GLB = 'x_hrguy', GLB_MATS = new Set();
function buildGlb() {
  if (S.code || !AUTHORED[GLB]) return null; // (not authored() on a miss: whenLate below swaps him when it lands)
  const a = authored(GLB), g = a.obj, n = (k) => nodeIn(g, 'hr_' + k);
  const body = n('body'), head = n('head'), arms = [n('armL'), n('armR')], fore = [n('foreL'), n('foreR')], legs = [n('legL'), n('legR')], clip = n('clip'), ear = n('led');
  if (![body, head, ...arms, ...fore, ...legs, clip, ear].every(Boolean)) return null;
  arms[0].userData.fore = fore[0]; arms[1].userData.fore = fore[1];
  const M = mats();
  g.traverse((o) => {
    if (!o.isMesh) return;
    if (o.material.name === 'hr_badge') { o.material = M.badge; return; }
    GLB_MATS.add(o.material);
  });
  for (const m of GLB_MATS) if (!m.userData.hr) { m.userData.hr = true; if ('envMapIntensity' in m && m.metalness < 0.5) m.envMapIntensity = 0.12; } // (the studio reflection lit him up in the dark woods)
  Object.assign(g.userData, { body, head, arms, legs, ear, clip, glb: true });
  return g;
}
function makeHR() {
  const g = buildGlb() || buildHR();
  if (g.userData.glb && S.nvg) hrNightVision(true); // (goggles already down: his new materials come out of the fog too)
  return g;
}
whenLate(GLB, () => { // it landed while he was about: swap him, same spot, same pose
  if (!S.mesh || S.mesh.userData.glb) return;
  const g = buildGlb();
  if (!g) return;
  const old = S.mesh, on = !!old.parent;
  if (on) old.parent.remove(old);
  old.traverse((o) => { if (o.geometry && !o.geometry.userData.shared) o.geometry.dispose(); });
  S.mesh = g; pose(g, S.pose);
  if (S.p) g.position.set(S.p[0], S.p[1], S.p[2]);
  g.rotation.y = S.yaw;
  if (on) G.scene.add(g);
  hrNightVision(S.nvg);
});
// a new pose every time he blinks: head tilted further, one shoulder down, the clipboard up to his chest... all wrong
function pose(g, seed) {
  let s = seed + 1;
  const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  const { body, head, arms } = g.userData;
  head.rotation.set((r() - 0.5) * 0.3, (r() - 0.5) * 0.6, (r() < 0.5 ? -1 : 1) * (0.15 + r() * 0.45));
  body.rotation.z = (r() - 0.5) * 0.08;
  arms[0].rotation.set((r() - 0.5) * 0.2, 0, -0.06 - r() * 0.12); arms[0].userData.fore.rotation.x = -r() * 0.3;
  const up = r() < 0.4; // reading his clipboard. about you
  arms[1].rotation.set(up ? 0.5 : (r() - 0.5) * 0.15, 0, 0.06 + r() * 0.1); arms[1].userData.fore.rotation.x = up ? 1.2 : -r() * 0.25; // (+x brings it up in front: the old -x put it behind his back)
}

// ------------------------------------------------------------ static over your screen
let stat = null, sg = null, game = null;
function staticCanvas() {
  if (stat) return;
  stat = document.createElement('canvas'); stat.id = 'hrStatic'; stat.width = 160; stat.height = 90;
  sg = stat.getContext('2d');
  $('hud').prepend(stat);
  game = $('game');
}
function drawStatic(k) {
  const img = sg.createImageData(160, 90), d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    const v = Math.random() * 255, line = (i / 640 | 0) % 3 === 0 ? 0.6 : 1;
    d[i] = v * line; d[i + 1] = v * line * (0.85 + Math.random() * 0.15); d[i + 2] = v * line; d[i + 3] = 255;
  }
  sg.putImageData(img, 0, 0);
  if (Math.random() < k * 0.5) { sg.fillStyle = `rgba(255,${(Math.random() * 60) | 0},60,0.5)`; sg.fillRect(0, (Math.random() * 90) | 0, 160, 2 + Math.random() * 8); } // a red tear
}
function distort(k, now) {
  if (!game) return;
  if (k < 0.05) { if (game.style.transform) { game.style.transform = ''; game.style.filter = ''; } stat.style.opacity = 0; return; }
  const j = k * k * 14, tear = Math.random() < k * 0.3 ? (Math.random() - 0.5) * 40 * k : 0;
  game.style.transform = `translate(${((Math.random() - 0.5) * j + tear) | 0}px, ${((Math.random() - 0.5) * j * 0.6) | 0}px) skewX(${(Math.sin(now * 0.03) * k * 3).toFixed(2)}deg)`;
  game.style.filter = `brightness(${(1 + k * 0.5).toFixed(2)}) saturate(${(1 - k * 0.75).toFixed(2)}) hue-rotate(${(Math.random() < k * 0.2 ? 160 : 0)}deg)`; // washed out, never crushed to black
  stat.style.opacity = Math.min(0.72, k * 0.62 + (Math.random() < k * 0.15 ? 0.25 : 0)).toFixed(2);
  drawStatic(k);
}

// ------------------------------------------------------------ messages from the server
let scene = null;
function show(on) {
  if (on && !S.mesh) { S.mesh = makeHR(); }
  if (S.mesh) { if (on && !S.mesh.parent) G.scene.add(S.mesh); if (!on && S.mesh.parent) S.mesh.parent.remove(S.mesh); }
}
export function hrMsg(m) {
  if (!m.on) { S.on = false; S.st = 0; show(false); return; }
  const was = S.on, moved = !S.p || Math.hypot(m.p[0] - S.p[0], m.p[2] - S.p[2]) > 0.5;
  S.on = true; S.yaw = Number(m.y) || 0; S.tg = m.tg; S.st = Math.max(0, Math.min(1, Number(m.st) || 0));
  if (!was) { S.p = m.p.slice(); S.pose = m.pose; S.called = 0; S.born = performance.now(); if (m.tg === G.myId) sfx.hrPing(); } // you have (1) new meeting
  show(true);
  if (moved && was) { sfx.hrStep([m.p[0], m.p[1] + 1, m.p[2]]); if (Math.random() < 0.5) sfx.twig([m.p[0], m.p[1], m.p[2]]); }
  S.p = m.p.slice();
  if (m.pose !== S.pose || !was) { S.pose = m.pose; pose(S.mesh, S.pose); }
  S.mesh.position.set(S.p[0], S.p[1], S.p[2]);
  S.mesh.rotation.y = S.yaw;
}
export function hrTake(m) { // he got someone. if it's you: everything at once
  S.on = false; show(false);
  if (m.id === G.myId) { sfx.hrTake(); S.take = performance.now(); hud.msg('HR WANTS A WORD', 2.2, 'hr'); }
  else if (m.p && G.camera.position.distanceTo(new THREE.Vector3(m.p[0], m.p[1], m.p[2])) < 60) sfx.squelch(m.p);
}
export function hrTeleport(m) { // transferred somewhere awful
  if (!Array.isArray(m.p) || m.p.length !== 3 || !m.p.every(Number.isFinite)) return;
  ME.pos = m.p.slice(); ME.vel = [0, 0, 0];
  setTimeout(() => hud.msg(`TRANSFERRED TO: ${String(m.where || 'SOMEWHERE AWFUL').slice(0, 40)}`, 3, 'hr'), 400);
}
// the kill feed and the death screen (main.js asks when a kill's weapon is 'hr')
export function hrFeed(vn, vc) { return [['Tall Guy From HR', '#cfd6e6'], ['  [LANYARD]  ', '#4f8cff'], [vn, vc], [`  ${pick(HR_LINES.feed)}`, '#aaa']]; }
export function hrDead() { return [[pick(HR_LINES.dead), '#fff']]; }

// ------------------------------------------------------------ the setting (match settings + the bots setup screen)
let uiDone = false;
function hrUI() {
  if (uiDone || !$('cfgHr')) return;
  uiDone = true;
  for (const id of ['cfgHr', 'setupHr']) {
    const el = $(id);
    for (const [k, v] of Object.entries(HR.names)) { const o = document.createElement('option'); o.value = k; o.textContent = v; el.append(o); }
    el.value = 'on';
  }
  $('cfgHr').addEventListener('change', () => net.send({ t: 'cfg', hr: $('cfgHr').value }));
}
export function hrNightVision(on) { // night vision goggles down: he isn't hidden by the fog any more
  S.nvg = !!on;
  for (const m of [...Object.values(mats()), ...GLB_MATS]) if (m.fog !== !on) { m.fog = !on; m.needsUpdate = true; }
}

// ------------------------------------------------------------ every frame
const v3 = new THREE.Vector3();
export function updateHR(dt) {
  hrUI();
  if (G.cfg && G.cfg.hr && $('cfgHr') && document.activeElement !== $('cfgHr') && $('cfgHr').value !== G.cfg.hr) $('cfgHr').value = G.cfg.hr;
  staticCanvas();
  const now = performance.now(), here = !!(MAPS[MAP.id] && MAPS[MAP.id].hr) && G.joined;
  if (!here) { if (S.on) { S.on = false; show(false); } hrLevel(0, 0); distort(0, now); return; }
  if (!S.asked && LAZY.has(GLB)) { S.asked = true; prefetch([GLB], 1); } // his Blender model, before his first visit
  if (nvOn() !== S.nvg) hrNightVision(nvOn()); // night vision goggles (goggles.js): the fog stops hiding him
  let k = 0, near = 0;
  if (S.on && S.p && ME.alive) {
    const e = [ME.pos[0], ME.pos[1] + PH.eye, ME.pos[2]], s = hrSight(e, ME.yaw, ME.pitch, S.p, S.nvg);
    // the server's meter (10 a second), eased so the static doesn't step
    S.stShow += (S.st - S.stShow) * Math.min(1, dt * 8);
    k = S.stShow;
    near = S.tg === G.myId ? Math.max(0, 1 - s.d / 30) : Math.max(0, 1 - s.d / 14) * 0.6;
    if (k > 0.45 && !S.called) { S.called = 1; hud.msg(pick(HR_LINES.stare), 1.6, 'hr'); }
    // his earpiece blinks. your flashlight makes the badge flash back at you
    if (S.mesh) {
      S.mesh.userData.ear.visible = Math.floor(now / 700) % 3 === 0;
      const lit = s.d < 30 && s.ang < 0.45 ? 1 - s.d / 30 : 0;
      mats().badge.emissive.setScalar(0.04 + lit * 0.3);
    }
  } else S.stShow = 0;
  if (now - S.take < 1200) k = Math.max(k, 1 - (now - S.take) / 1200); // the take: full static, fading out
  hrLevel(k, near);
  distort(k, now);
}
G.hrState = S; // tests poke at it
net.on('hr', hrMsg);
net.on('hrx', hrTake);
net.on('hrtp', hrTeleport);
