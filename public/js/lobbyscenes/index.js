// LOBBY SCENES (docs/menu/LOBBY_SCENES.md): a little 3D place behind each mode's lobby screen, with you and your party
// standing in it. the hub's lobby (hubmenu.js) mounts one per mode; main.js draws it instead of the map backdrop while
// it's up. each place is its own file, fetched the first time its mode is picked. drawn with the game's own renderer
// (no second webgl context), so the graphics preset (Potato pixels, vertex snap, bloom) applies like everywhere else.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { buildCharacter, buildWeapon, freeTree } from '../models.js';
import { idlePose } from '../loco.js';
import { postBegin, postEnd } from '../post.js';
import { jankify } from '../jank.js';
import { authored, want, whenGlb, missingGlb, withEnv } from '../glbkit.js';
import { DEFAULT_LOOK, SKIN_TONES, HAIR_COLORS, CLOTH_COLORS, HAIRS, TOPS, BOTTOMS, LOOK_COLORS } from '/shared/looks.js';
import { WEAPONS } from '/shared/weapons.js';
import { synth } from '../audio.js';
import * as party from '../party.js'; // the party (P, onParty) and the walkable lobbies' position relay
import * as hub from '../hubmenu.js'; // (lobbySceneFlag: the hub's lineup steps aside while a scene is up)
import { makeWalk, walker, poseWalker, wander, follow } from './walk.js';

const FILES = { isle: 'garage' }; // mode -> scene file (more land with their PRs: zm warehouse, br royale, qp/bomb hangar)
const mods = {};
const load = (f) => mods[f] || (mods[f] = import(`./${f}.js`).catch((e) => { delete mods[f]; throw e; }));
export const lobbySceneFor = (mode) => FILES[mode] || null;
export function lobbyScenePrefetch(mode) { if (FILES[mode]) load(FILES[mode]).catch(() => {}); } // (hovering a mode card)

let meFn = () => ({ name: 'you', color: '#ff4fd8', look: DEFAULT_LOOK, gun: 'ar', skin: null });
export function setLobbyMe(fn) { meFn = fn; } // main.js: your name, colour, look, gun and skin, read fresh each time
let ask = null, cur = null, flashT = 0, visit = false; // visit: this lobby visit already showed a mode (switching flashes)
const $ = (id) => document.getElementById(id);

// the hook. mode: the hub's mode key. o: { side: 'online' | 'offline', party, onMe(), onInvite() }
// party: [{ id, name, color, look, gun, skin, mech, ready, leader, bot, me }] or nothing (just you, the rest is filled in)
let flagged = false;
export function mountLobbyScene(mode, o = {}) {
  if (!flagged) { flagged = true; try { if (hub.lobbySceneFlag) hub.lobbySceneFlag(lobbySceneOn); } catch { /* (an older hub) */ } } // (here, not at load: the two modules import each other)
  const file = FILES[mode];
  if (!file) { ask = null; visit = true; if (cur) { flash(); drop(); } return; }
  const same = cur && cur.file === file, was = visit;
  visit = true;
  ask = { mode, file, side: o.side === 'offline' ? 'offline' : 'online', party: o.party || null, onMe: o.onMe, onInvite: o.onInvite, save: o.save };
  if (same) { cur.ask = ask; syncParty(); return; }
  const a = ask;
  load(file).then((m) => { if (ask !== a || !G.renderer) return; if (cur) drop(); if (was) flash(); start(m, a); }).catch((e) => console.warn('lobby scene', file, e));
}
export function setLobbyParty(party) { if (ask) ask.party = party || null; if (cur) syncParty(); }
export function unmountLobbyScene() { ask = null; visit = false; drop(); }
export const lobbySceneOn = () => !!cur;

// main.js, every frame: draws the scene if the lobby is the screen on show, else lets it go. true = it drew this frame
export function lobbySceneFrame(dt, showing) {
  if (flashT > 0) { flashT = Math.max(0, flashT - dt); const f = $('lsFlash'); if (f) f.style.opacity = String(Math.min(1, flashT / 0.18)); } // (the mode-switch flash fades with or without a scene)
  if (!showing) { if (cur || ask || visit) unmountLobbyScene(); return false; }
  if (!cur) return false;
  const c = cur, r = G.renderer;
  if (G.lsHold) { dt = G.lsAdvance || 0; G.lsAdvance = 0; } else dt *= G.lsTimeScale || 1; // (tests: slow motion, or one frame at a time for clips)
  c.t += dt;
  if (c.walk) c.walk.frame(dt, c.t); else frameCam(c, dt);
  c.api.update(dt, c.t);
  for (const p of c.people) posePerson(p, dt, c.t);
  plates(c);
  const post = postBegin(r);
  r.setClearColor(c.scene.background || 0x000000, 1); r.clear();
  withEnv(r, c.scene, () => r.render(c.scene, c.cam)); // (the Blender props' studio reflections)
  if (post && !postEnd(r)) { r.setRenderTarget(null); r.clear(); r.render(c.scene, c.cam); }
  return true;
}

// ---------------------------------------------------------------- mount / unmount
function start(m, a) {
  ensureDom();
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(36, innerWidth / innerHeight, 0.1, 600);
  const c = { file: a.file, ask: a, scene, cam, t: 0, people: [], spots: [], made: [], kids: [], ls: [], mx: 0, my: 0, hover: null, party, panels: true, walk: null };
  cur = c;
  c.visible = () => { const s = $('scr-hubby'); return !!s && !s.classList.contains('hidden') && !$('menu').classList.contains('hidden'); };
  c.setPanels = (on) => { c.panels = on; const s = $('scr-hubby'); if (s) s.classList.toggle('ls-panels', on); const b = $('lsPanBtn'); if (b) b.textContent = on ? 'WALK AROUND [TAB]' : 'MATCH SETTINGS [TAB]'; };
  c.lib = lib(c);
  c.api = m.build(c.lib);
  c.spots = c.api.spots;
  if (c.api.walk) startWalk(c);
  syncParty();
  document.body.classList.add('ls-on');
  on(c, $('scr-hubby'), 'pointermove', (e) => { c.mx = e.clientX / innerWidth - 0.5; c.my = e.clientY / innerHeight - 0.5; hover(c, e); });
  on(c, $('scr-hubby'), 'click', (e) => clickAt(c, e));
  on(c, window, 'resize', () => frameCam(c, 0, true));
  frameCam(c, 0, true);
}
function drop() {
  const c = cur;
  if (!c) return;
  cur = null;
  try { if (c.api && c.api.dispose) c.api.dispose(); } catch (e) { console.warn('lobby scene dispose', e); }
  for (const [el, ty, fn, cap] of c.ls) el.removeEventListener(ty, fn, !!cap);
  for (const p of c.people) freePerson(p);
  c.people.length = 0;
  c.scene.traverse((o) => { if (o.isLight && o.shadow && o.shadow.map) { o.shadow.map.dispose(); o.shadow.map = null; } });
  freeTree(c.scene);
  for (const x of c.made) x.dispose(); // our own materials and textures (shared Blender ones are left alone)
  c.scene.clear();
  const t = $('lsTags'); if (t) t.innerHTML = '';
  document.body.classList.remove('ls-on', 'ls-hot', 'ls-walk');
  const s = $('scr-hubby'); if (s) s.classList.remove('ls-panels');
}
function on(c, el, ty, fn) { if (!el) return; el.addEventListener(ty, fn); c.ls.push([el, ty, fn]); }
function flash() { const f = $('lsFlash'); if (!f) return; flashT = 0.22; f.style.opacity = '1'; try { synth.whoosh(0.25, 0.2, 500, 2400); } catch { /* (no audio yet) */ } }

function ensureDom() {
  if ($('lsTags')) return;
  const css = document.createElement('style');
  css.textContent = `
body.ls-on #menu.home-on { background: none; }
body.ls-on #menu.home-on::before { opacity: 0.22; }
body.ls-on #hubStage #preview { visibility: hidden; }
body.ls-hot #scr-hubby { cursor: pointer; }
#lsTags { position: fixed; inset: 0; pointer-events: none; z-index: 1; font-family: var(--font); overflow: hidden; }
#lsTags > div { position: absolute; left: 0; top: 0; will-change: transform; }
#lsTags .np { text-align: center; white-space: nowrap; }
#lsTags .np b { display: block; font-size: 15px; color: #fff; text-shadow: 2px 2px 0 #120818, -1px -1px 0 #120818; letter-spacing: 1px; }
#lsTags .np i { display: inline-block; font-style: normal; font-size: 11px; font-weight: 900; color: #120818; background: #7dff4f; border: 2px solid #000; padding: 0 6px; transform: rotate(-2deg); }
#lsTags .np i.no { background: #fff; } #lsTags .np i.bot { background: #4fd8ff; } #lsTags .np i.you { background: #ffe14d; }
#lsTags .np .crown { display: block; font-size: 16px; line-height: 1; color: #ffe14d; text-shadow: 2px 2px 0 #120818; }
#lsTags .np.inv b { color: #4fd8ff; } #lsTags .np.inv i { background: #fff; }
#lsTags .bub { max-width: 230px; background: #fff; color: #120818; border: 3px solid #000; box-shadow: 5px 5px 0 #ff4fd8; padding: 6px 10px; font-size: 14px; font-weight: 700; line-height: 1.15; }
#lsTags .bub small { display: block; font-size: 11px; color: #ff00dc; font-weight: 900; letter-spacing: 1px; margin-bottom: 2px; }
#lsTags .ui { pointer-events: auto; }
#lsFlash { position: fixed; inset: 0; background: #fff; opacity: 0; pointer-events: none; z-index: 1; }
body.ls-walk #scr-hubby:not(.ls-panels) .hub-panel { display: none; }
body.ls-walk #scr-hubby:not(.ls-panels) .hub-head p { display: none; }
#lsTags .ls-use { display: flex; gap: 6px; align-items: center; font-weight: 900; font-size: 16px; color: #fff; text-shadow: 2px 2px 0 #120818; white-space: nowrap; }
#lsTags .ls-use kbd { font: 900 15px var(--font); background: #ffe14d; color: #120818; border: 3px solid #000; box-shadow: 3px 3px 0 #ff4fd8; padding: 0 7px; }
#lsPanBtn { position: fixed; right: clamp(34px, 5vmin, 58px); top: clamp(170px, 26vh, 200px); z-index: 3; font: 900 14px var(--font); letter-spacing: 1px; background: #fff; color: #120818; border: 3px solid #000; box-shadow: 4px 4px 0 var(--pink, #ff4fd8); padding: 5px 12px; cursor: pointer; transform: rotate(1deg); display: none; }
body.ls-walk #lsPanBtn { display: block; }
body.ls-walk #scr-hubby.ls-panels #lsPanBtn { top: auto; bottom: clamp(22px, 4vmin, 44px); }
#lsHelp { position: fixed; left: clamp(34px, 5vmin, 58px); bottom: clamp(22px, 4vmin, 44px); z-index: 2; font-size: 13px; color: #fff; text-shadow: 2px 2px 0 #120818; display: none; max-width: 30vw; line-height: 1.35; }
#lsHelp b { color: #ffe14d; }
body.ls-walk #scr-hubby:not(.ls-panels) #lsHelp { display: block; }
`;
  document.head.append(css);
  const t = document.createElement('div'); t.id = 'lsTags';
  const f = document.createElement('div'); f.id = 'lsFlash';
  const scr = $('scr-hubby');
  (scr || document.body).prepend(t, f); // (inside the lobby screen, under its panels)
  const b = document.createElement('button'); b.id = 'lsPanBtn'; b.textContent = 'MATCH SETTINGS [TAB]';
  b.addEventListener('click', (e) => { e.stopPropagation(); if (cur) cur.setPanels(!cur.panels); });
  const h = document.createElement('div'); h.id = 'lsHelp';
  h.innerHTML = '<b>WASD</b> walk · <b>SHIFT</b> run · <b>SPACE</b> jump · <b>DRAG</b> look · <b>E</b> use · <b>Z</b> wave · <b>TAB</b> match settings';
  if (scr) scr.append(b, h);
}
// a walkable scene: you're a walker the keys drive, the panels fold away (TAB / the corner button / Esc bring them back)
function startWalk(c) {
  document.body.classList.add('ls-walk');
  c.setPanels(false);
}

// ---------------------------------------------------------------- the camera: frames the scene's focus box in the stage
// (the middle column between the panels, whatever the window size), drifting slowly, leaning a little toward the mouse
const _v = new THREE.Vector3(), _d = new THREE.Vector3(), _a = new THREE.Vector3(), _b = new THREE.Vector3();
// the stage: the middle column between the panels, top to the big button (feet may stand a bit behind the button)
function stageRect() {
  const st = $('hubStage'), W = innerWidth, H = innerHeight, rc = st && st.getBoundingClientRect();
  if (!rc || rc.width < 60 || rc.height < 60) return { x: W * 0.28, y: H * 0.25, w: W * 0.44, h: H * 0.6 };
  const go = $('hubGo'), gr = go && go.getBoundingClientRect(), bot = gr && gr.height ? Math.max(rc.bottom, gr.top + gr.height * 0.35) : rc.bottom;
  return { x: rc.left, y: rc.top, w: rc.width, h: bot - rc.top };
}
// how far back the camera sits: F.top lands on the stage's top edge and F.bot on its bottom (bisection: the gap
// between them on screen shrinks as the camera backs off), and F.w metres across must fit the stage's width
function fitD(c, R) {
  const F = c.api.focus, cam = c.cam, H = innerHeight, tn = Math.tan((cam.fov * Math.PI) / 360);
  cam.clearViewOffset(); cam.updateProjectionMatrix();
  const gap = (d) => { cam.position.copy(F.at).addScaledVector(F.dir, d); cam.lookAt(F.at); cam.updateMatrixWorld(true); _a.copy(F.top).project(cam); _b.copy(F.bot).project(cam); return ((_a.y - _b.y) / 2) * H; };
  let lo = 1, hi = 200;
  for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (gap(m) > R.h) lo = m; else hi = m; }
  return Math.max(hi, (F.w * H) / (2 * tn * R.w), F.min || 0);
}
function frameCam(c, dt, now) {
  const F = c.api.focus, cam = c.cam, W = innerWidth, H = innerHeight;
  cam.fov = F.fov || 36; cam.aspect = W / H;
  if (now || !c.R) { c.R = stageRect(); c.fitD = fitD(c, c.R); }
  if (now || !c.camD) c.camD = c.fitD; else c.camD += (c.fitD - c.camD) * Math.min(1, dt * 4);
  // where top / bottom land on screen at that distance (no offset yet): shift the picture so their middle is the stage's
  cam.clearViewOffset(); cam.updateProjectionMatrix();
  cam.position.copy(F.at).addScaledVector(F.dir, c.camD); cam.lookAt(F.at); cam.updateMatrixWorld(true);
  _a.copy(F.top).project(cam); _b.copy(F.bot).project(cam);
  const midY = ((1 - (_a.y + _b.y) / 2) / 2) * H, cx = c.R.x + c.R.w / 2, cy = c.R.y + c.R.h / 2;
  const sway = Math.sin(c.t * 0.21) * (F.drift ?? 0.06) + c.mx * 0.05, bob = Math.sin(c.t * 0.33) * 0.015 - c.my * 0.025 + (F.bob ? Math.sin(c.t * 0.9) * F.bob : 0);
  _d.copy(F.dir).applyAxisAngle(THREE.Object3D.DEFAULT_UP, sway); _d.y += bob; _d.normalize();
  cam.position.copy(F.at).addScaledVector(_d, c.camD);
  cam.lookAt(F.at);
  const L = c.lib; if (L && L.shake > 0) { const k = L.shake * L.shake * 0.25; cam.position.x += (Math.random() - 0.5) * k; cam.position.y += (Math.random() - 0.5) * k; L.shake = Math.max(0, L.shake - dt * 1.6); } // (a mech landing)
  cam.setViewOffset(W, H, W / 2 - cx, midY - cy, W, H); // the focus lands in the middle of the stage, not of the window
  cam.updateProjectionMatrix();
}

// ---------------------------------------------------------------- people: you, the party, bots, empty spots
const BOT_NAMES = ['Gary', 'Linda', 'Steve', 'Brenda', 'Kevin', 'Doug', 'Karen', 'Phil', 'Tina', 'Rick', 'Carl', 'Pam']; // (the server's bot names)
const GUNS = ['ar', 'smg', 'shotgun', 'sniper', 'pistol'].filter((g) => WEAPONS[g]);
const rndOf = (seed) => rnd(seed);
function rnd(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function botLook(seed) { // a bot outfit, the same one for the same spot (no flicker on every redraw)
  const r = rnd(seed * 7919 + 13), p = (a) => a[Math.floor(r() * a.length)], k = (o) => p(Object.keys(o).filter((x) => !o[x].ach));
  return { ...DEFAULT_LOOK, skin: p(SKIN_TONES.slice(0, 7)), hair: k(HAIRS), hairColor: p(HAIR_COLORS), top: k(TOPS), topColor: p(CLOTH_COLORS), bottom: k(BOTTOMS), bottomColor: p(CLOTH_COLORS), build: p(['', 'm', 'f']) };
}
// who stands where: your party in order (you first), then bots (offline) or + INVITE spots (online)
function lineup(c) {
  const a = c.ask, me = { ...meFn(), id: 'me', me: true };
  let given = Array.isArray(a.party) && a.party.length ? a.party : null;
  const PP = party.P;
  if (!given && PP && PP.on && PP.ms && PP.ms.length > 1) // the hub's party (party.js): its members, you from your live settings
    given = PP.ms.map((m) => (m.id === PP.me ? { me: true, leader: m.id === PP.lead, ready: !!m.ready } : { id: m.id, name: m.name, look: m.look, color: (m.look && m.look.color) || LOOK_COLORS[(m.id | 0) % LOOK_COLORS.length], gun: m.gun, mech: m.mf, ready: !!m.ready, leader: m.id === PP.lead, busy: !!m.busy }));
  const list = given ? given.map((p) => (p.me ? { ...me, ...p } : p)) : [me];
  if (!list.some((p) => p.me)) list.unshift(me);
  list.sort((x, y) => (y.me ? 1 : 0) - (x.me ? 1 : 0));
  const out = list.slice(0, c.spots.length);
  for (let i = out.length; i < c.spots.length; i++) {
    if (a.side === 'offline' && c.api.bots !== false) { const r = rnd(i * 31 + 7); out.push({ id: 'bot' + i, bot: true, name: BOT_NAMES[(i * 5 + 3) % BOT_NAMES.length], color: LOOK_COLORS[(i * 3) % LOOK_COLORS.length], look: botLook(i), gun: GUNS[Math.floor(r() * GUNS.length)] }); }
    else out.push({ id: 'inv' + i, invite: true });
  }
  return out;
}
const keyOf = (p) => p.invite ? 'inv' : JSON.stringify([p.id, p.color, p.look, p.gun, p.skin && (p.skin.id || p.skin)]);
function syncParty() {
  const c = cur;
  if (!c) return;
  const list = lineup(c);
  for (let i = 0; i < c.spots.length; i++) {
    const p = list[i], k = keyOf(p), old = c.people[i];
    if (old && old.key === k) { old.info = p; plateText(old); continue; }
    if (old) freePerson(old);
    c.people[i] = makePerson(c, i, p, k);
  }
  if (c.api.party) c.api.party(list);
}
function makePerson(c, i, info, key) {
  const sp = c.spots[i], P = { key, info, i, wrap: new THREE.Group(), ch: null, plate: null, pose: POSES[(i * 3 + 1) % POSES.length], t0: i * 2.3, emo: 0 };
  P.wrap.position.set(sp.x, sp.y || 0, sp.z); P.wrap.rotation.y = sp.ry || 0;
  c.scene.add(P.wrap);
  if (!info.invite) {
    const ch = buildCharacter(info.color || '#ff4fd8', { ...DEFAULT_LOOK, ...(info.look || {}) });
    if (c.walk || c.api.walk) { ch.root.scale.setScalar(1.2); P.r = walker(ch, info.gun, [sp.x, 0, sp.z, sp.yaw || 0]); P.wrap.rotation.y = 0; } // (game size; it walks)
    else ch.root.rotation.y = Math.PI; // (characters face -z; the spots face the camera)
    ch.root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.userData.lsMe = info.me ? 1 : 0; } });
    if (info.gun && WEAPONS[info.gun]) { const w = buildWeapon(info.gun, info.skin); w.scale.setScalar(1.5); w.traverse((o) => { if (o.isMesh) o.castShadow = true; }); ch.slot.add(w); ch.gun = w; }
    P.wrap.add(ch.root); P.ch = ch;
  } else if (c.api.inviteSpot) c.api.inviteSpot(P.wrap, i);
  const d = document.createElement('div'); d.className = 'np' + (info.invite ? ' inv' : '');
  $('lsTags').append(d); P.plate = d; plateText(P);
  P.head = new THREE.Vector3(0, info.invite ? (c.api.inviteH || 1.3) : P.r ? 2.5 : 2.05, 0);
  if (P.r && info.me && c.api.walk) { const old = c.walkMe; if (old) { P.r.pos = old.pos.slice(); P.r.yaw = old.yaw; } c.walkMe = P.r; c.walk = c.walk || makeWalk(c, c.lib, c.api.walk, P.r); c.walk.me = P.r; c.walk.reMe && c.walk.reMe(P.r); } // (a new look: same spot)
  return P;
}
function plateText(P) {
  const p = P.info, d = P.plate;
  if (!d) return;
  if (p.invite) { d.innerHTML = '<b>+ INVITE</b><i>PARTY UP</i>'; return; }
  const tag = p.me ? ['you', 'YOU'] : p.bot ? ['bot', 'BOT'] : p.ready ? ['', 'READY'] : ['no', 'NOT READY'];
  d.innerHTML = (p.leader ? '<span class="crown">♛</span>' : '') + '<b></b><i></i>';
  d.querySelector('b').textContent = String(p.name || '???').slice(0, 20);
  const i = d.querySelector('i'); i.textContent = tag[1]; if (tag[0]) i.className = tag[0];
  if (P.wasReady === false && p.ready) P.emo = 1.2; // READY: a little celebration
  P.wasReady = !!p.ready;
}
function freePerson(P) {
  if (P.wrap.parent) P.wrap.parent.remove(P.wrap);
  freeTree(P.wrap);
  if (P.plate) P.plate.remove();
}
function plates(c) {
  const W = innerWidth, H = innerHeight;
  for (const P of c.people) {
    if (!P.plate) continue;
    _v.copy(P.head); P.wrap.localToWorld(_v); _v.project(c.cam);
    const vis = _v.z < 1 && Math.abs(_v.x) < 1.2 && Math.abs(_v.y) < 1.2 && P.wrap.visible;
    P.plate.style.display = vis ? '' : 'none';
    if (vis) P.plate.style.transform = `translate(${((_v.x + 1) / 2) * W}px, ${((1 - _v.y) / 2) * H}px) translate(-50%, -100%)`;
  }
  if (c.api.tags) c.api.tags(c, W, H);
}

// lobby poses on the mannequin (arms are one piece from the shoulder: x -1.5 hangs, 0 points ahead). each person gets
// one, breathes, shifts their weight, and now and then looks around. READY plays a little hop + fist pump
const POSES = [
  { name: 'low ready', r: [-0.85, 0.12, 0], l: [-0.7, 0.55, 0] },
  { name: 'shoulder', r: [0.55, -0.15, 0.15], l: [-1.45, 0, -0.1] },
  { name: 'hang loose', r: [-1.4, 0, 0.12], l: [-1.42, 0, -0.14] },
  { name: 'hip', r: [-1.2, 0.2, 0.55], l: [-1.0, -0.3, -0.75] },
];
function posePerson(P, dt, t) {
  const ch = P.ch;
  if (!ch) return;
  if (P.r) { // a walker: you (the keys), a bot (wanders), a party member (the relay)
    const r = P.r, c = cur;
    if (!P.info.me) { if (P.info.bot && c.api.walk.wander) wander(r, dt, c.api.walk, P.rnd || (P.rnd = rndOf(P.i * 977 + 3))); else follow(r, dt); }
    P.wrap.position.set(r.pos[0], r.pos[1], r.pos[2]); P.wrap.rotation.y = r.yaw; P.wrap.visible = !r.hidden;
    if (P.emo > 0) { r.emo = P.emo; P.emo = 0; }
    poseWalker(r, dt, t);
    return;
  }
  const tt = t + P.t0;
  idlePose(ch, tt);
  const look = Math.sin(tt * 0.37) > 0.82 ? Math.sin(tt * 0.9) * 0.45 : 0; // the odd glance around
  ch.head.rotation.y += (look - ch.head.rotation.y) * Math.min(1, dt * 4);
  const p = P.pose;
  if (P.emo > 0) { // ready! hop + pump
    P.emo = Math.max(0, P.emo - dt);
    const k = Math.sin(((1.2 - P.emo) / 1.2) * Math.PI);
    ch.arm.rotation.set(-0.2 + k * 2.6, 0, 0.1); ch.armL.rotation.set(-1.3, 0, -0.1);
    P.wrap.position.y = (cur && cur.spots[P.i] ? cur.spots[P.i].y || 0 : 0) + Math.max(0, Math.sin(((1.2 - P.emo) / 1.2) * Math.PI * 2)) * 0.25;
    return;
  }
  const s = Math.sin(tt * 1.3) * 0.03;
  ch.arm.rotation.set(p.r[0] + s, p.r[1], p.r[2]);
  ch.armL.rotation.set(p.l[0] - s, p.l[1], p.l[2]);
}

// ---------------------------------------------------------------- pointer: hover + click on things in the scene
const ray = new THREE.Raycaster(), _m = new THREE.Vector2();
function overScene(e) { // only where no panel or button is on top
  const el = e.target;
  return el && (el.id === 'scr-hubby' || el.id === 'hubStage' || el.id === 'preview' || el.id === 'hubFrame' || el.closest('#hubFrame') || el.id === 'lsTags');
}
function hit(c, e) {
  if (!overScene(e)) return null;
  _m.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  ray.setFromCamera(_m, c.cam);
  const hits = ray.intersectObjects(c.scene.children, true);
  for (const h of hits) {
    if (h.object.userData.lsMe) return { kind: 'me' };
    for (let o = h.object; o; o = o.parent) if (o.userData.lsPick) return { kind: o.userData.lsPick, obj: o, point: h.point };
    if (!h.object.userData.lsSee) break; // (glass, fx: look through it)
  }
  return null;
}
function hover(c, e) {
  const h = hit(c, e), k = h ? h.kind + (h.obj ? h.obj.id : '') : null;
  document.body.classList.toggle('ls-hot', !!h);
  if (k !== c.hover) { c.hover = k; if (c.api.hover) c.api.hover(h); }
}
function clickAt(c, e) {
  if (c.walk && c.walk.dragged()) return; // (that was a look-round, not a click)
  const h = hit(c, e);
  if (!h) return;
  if (h.kind === 'me') { if (c.ask.onMe) c.ask.onMe(); return; }
  if (h.kind === 'invite') { if (c.ask.onInvite) c.ask.onInvite(); return; }
  if (c.api.click) c.api.click(h);
}

// ---------------------------------------------------------------- what scene files get: helpers that clean up after themselves
function lib(c) {
  const keep = (x) => { c.made.push(x); return x; };
  const L = {
    THREE, G, cur: () => c,
    get side() { return c.ask.side; },
    get mode() { return c.ask.mode; },
    potato: () => (G.settings && G.settings.jank | 0) === 0,
    shadows: () => !!G.realShadows,
    mat: (color, rough = 0.6, metal = 0, emi = 0) => keep(jankify(new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, emissive: emi }))),
    basic: (color, o = {}) => keep(jankify(new THREE.MeshBasicMaterial({ color, ...o }))),
    tex: (t) => keep(t),
    box(par, w, h, d, m, x = 0, y = 0, z = 0, ry = 0) { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.rotation.y = ry; o.castShadow = o.receiveShadow = true; par.add(o); return o; },
    cyl(par, r0, r1, h, m, x = 0, y = 0, z = 0, seg = 10) { const o = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m); o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; par.add(o); return o; },
    // a Blender model (x_lobby_*.glb, lazy like the gear ones): a fresh copy now, or later via cb when it lands
    glb(id, cb) {
      const a = authored(id);
      if (a) { cb(a.obj, a.meta); return; }
      if (!missingGlb(id)) return;
      want(id, 3);
      const mine = c;
      whenGlb([id], () => { if (cur !== mine) return; const b = authored(id); if (b) cb(b.obj, b.meta); });
    },
    // a canvas texture with text on it (signs, screens). the house font
    label(txt, { bg = '#ffe14d', fg = '#120818', w = 256, h = 64, border = '#000' } = {}) {
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h; const x = cv.getContext('2d');
      x.fillStyle = bg; x.fillRect(0, 0, w, h); if (border) { x.strokeStyle = border; x.lineWidth = Math.max(4, h / 10); x.strokeRect(0, 0, w, h); }
      x.fillStyle = fg; x.font = `900 ${Math.floor(h * 0.55)}px "Comic Neue", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(txt, w / 2, h / 2 + 2);
      const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 2; return keep(t);
    },
    // speckled, seamed floor / wall textures, tiny, nearest-filtered (the house crunch)
    speck(hex, rep = 8, seams = true, n = 32) {
      const cv = document.createElement('canvas'); cv.width = cv.height = n; const g = cv.getContext('2d'), col = new THREE.Color(hex), r = rnd(hex);
      for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const k = 0.82 + r() * 0.3; g.fillStyle = `rgb(${(col.r * 255 * k) | 0},${(col.g * 255 * k) | 0},${(col.b * 255 * k) | 0})`; g.fillRect(x, y, 1, 1); }
      if (seams) { g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, 0, n, 1); g.fillRect(0, 0, 1, n); }
      const t = new THREE.CanvasTexture(cv); t.magFilter = THREE.NearestFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.colorSpace = THREE.SRGBColorSpace; return keep(t);
    },
    stripes(rep = 8, a = '#ffe14d', b = '#120818') { // hazard tape
      const cv = document.createElement('canvas'); cv.width = 64; cv.height = 16; const x = cv.getContext('2d');
      x.fillStyle = a; x.fillRect(0, 0, 64, 16); x.fillStyle = b;
      for (let i = -1; i < 9; i++) { x.beginPath(); x.moveTo(i * 16, 16); x.lineTo(i * 16 + 8, 16); x.lineTo(i * 16 + 16, 0); x.lineTo(i * 16 + 8, 0); x.fill(); }
      const t = new THREE.CanvasTexture(cv); t.wrapS = THREE.RepeatWrapping; t.repeat.set(rep, 1); t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace; return keep(t);
    },
    tag(cls, html) { const d = document.createElement('div'); d.className = cls; d.innerHTML = html; $('lsTags').append(d); return d; }, // (removed with the scene)
    at(d, v, dx = 0, dy = 0) { // put a tag over a world point
      _v.copy(v).project(c.cam);
      const vis = _v.z < 1 && Math.abs(_v.x) < 1.2 && Math.abs(_v.y) < 1.2;
      d.style.display = vis ? '' : 'none';
      if (vis) d.style.transform = `translate(${((_v.x + 1) / 2) * innerWidth + dx}px, ${((1 - _v.y) / 2) * innerHeight + dy}px) translate(-50%, -100%)`;
    },
    shake: 0,
    people: () => c.people,
    sfx: synth,
  };
  return L;
}
// tests: what's up and how much it holds
export const lobbySceneInfo = () => (cur ? { file: cur.file, mode: cur.ask.mode, people: cur.people.map((p) => (p.info.invite ? 'invite' : p.info.bot ? 'bot' : p.info.me ? 'me' : 'mate')), extra: cur.api.info ? cur.api.info() : null } : null);

// the party's spots in the walkable lobbies (party.js relays them ~10 a second): each member walks to theirs.
// a = what they're doing (walk.js): 1 = in their mech (the scene moves it), 2 = waving
if (party.onLobbyPos) party.onLobbyPos((m) => {
  const c = cur;
  if (!c || !c.walk || !m || !Array.isArray(m.p)) return;
  const P = c.people.find((x) => x.info && x.info.id === m.id && x.r);
  if (!P) return;
  P.r.tgt = m.p; P.r.tyaw = m.yaw;
  if (m.a === 2 && !(P.r.emo > 0)) P.r.emo = 1.4;
  P.r.hidden = m.a === 1;
  if (c.api.remote) c.api.remote(P.i, m);
});
if (party.onParty) party.onParty(() => { if (cur) syncParty(); });
