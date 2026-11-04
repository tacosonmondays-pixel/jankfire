// Killcam picture-in-picture: two little boxes in the top right while any replay plays.
// POV: the same replay moment through the killer's own eyes (their gun as a viewmodel, scope when they aimed).
// LIVE REACTION: what the killer is doing right now in the real game, filmed from in front of their face.
// both are extra passes over the one shared scene (replay ghosts vs live remotes toggled), into small render targets
// at the game's own crunchy resolution, then pasted into the corner of the canvas every frame.
import * as THREE from 'three';
import { G } from './ctx.js';
import { buildWeapon, setKatana, M } from './models.js';
import { VM } from './weapons.js';
import { scaleU } from './fx.js';
import { FLAGS, WEAPONS } from '/shared/weapons.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';

const INTERP = 110; // ms behind the server clock, like main.js draws remotes
const FOV = 95; // nobody sends their fov: the default
let st = null; // the replay being watched (replay.js state: ghosts, opts, projs)
let ui = null, lay = null, tick = 0, turn = 0, ema = 16, lastNow = 0, liveDt = 0;
const povCam = new THREE.PerspectiveCamera(FOV, 16 / 9, 0.1, 1500);
povCam.rotation.order = 'YXZ';
const liveCam = new THREE.PerspectiveCamera(60, 16 / 9, 0.1, 1500);
const vmCam = new THREE.PerspectiveCamera(65, 16 / 9, 0.01, 10);
const vmScene = new THREE.Scene();
vmScene.add(new THREE.HemisphereLight(0xcfe8ff, 0x7a4a6a, 1.8));
const vmSun = new THREE.DirectionalLight(0xffffff, 1.5);
vmSun.position.set(0.5, 1, 0.8);
vmScene.add(vmSun);
const vms = new Map(); // weapon + skin -> viewmodel wrap (built once)
let vm = null;
// pasting a box into the canvas: one quad, ortho camera, the box's render target as its texture
const blitCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const blitMat = new THREE.ShaderMaterial({ // copies the pixels as they are (they're already encoded for the screen, see layout)
  uniforms: { map: { value: null } }, depthTest: false, depthWrite: false,
  vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
  fragmentShader: 'uniform sampler2D map; varying vec2 vUv; void main() { gl_FragColor = texture2D(map, vUv); }',
});
const blitScene = new THREE.Scene();
blitScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blitMat));
const boxes = { pov: { rt: null, has: false, lost: null }, live: { rt: null, has: false, lost: null, cam: null, yaw: 0 } };
export const PIP = { renders: 0, every: 1, force: false }; // stats for tests / the console. force: true / 'pov' / 'live' = re-render every frame (benchmarks)
const tv = new THREE.Vector3(), tv2 = new THREE.Vector3(), sz = new THREE.Vector2();

const CSS = `
#pipWrap { position: absolute; inset: 0; pointer-events: none; }
.pipbox { position: absolute; outline: 2px solid var(--pc, #ff4fd8); box-shadow: 4px 4px 0 #000; overflow: hidden; }
.pipbox .plab { position: absolute; left: 0; top: 0; padding: 1px 6px 2px; font-size: 12px; line-height: 14px; color: #fff; background: rgba(10, 0, 20, 0.8); text-shadow: 1px 1px 0 #000; white-space: nowrap; max-width: calc(100% - 12px); overflow: hidden; text-overflow: ellipsis; }
.pipbox .plab b { color: var(--kc, #fff); }
#pipLive { --pc: #ff3030; }
#pipLive .plab i { display: inline-block; width: 8px; height: 8px; margin-right: 5px; border-radius: 50%; background: #ff3030; box-shadow: 0 0 6px #ff3030; }
.pipbox .pcross { position: absolute; left: 50%; top: 50%; width: 9px; height: 9px; margin: -5px 0 0 -5px; background: linear-gradient(#fff, #fff) center / 100% 1px no-repeat, linear-gradient(#fff, #fff) center / 1px 100% no-repeat; filter: drop-shadow(1px 1px 0 #000); }
.pipbox .pscope { position: absolute; inset: 0; display: none; background: radial-gradient(circle at center, transparent 0 38%, #000 calc(38% + 1px)), linear-gradient(#000, #000) center / 100% 1px no-repeat, linear-gradient(#000, #000) center / 1px 100% no-repeat; }
.pipbox.scoped .pscope { display: block; }
.pipbox.scoped .pcross { display: none; }
.pipbox .plost { position: absolute; inset: 0; display: none; background: #222; text-align: center; }
.pipbox.lost .plost { display: block; }
.pipbox.lost .pcross, .pipbox.lost .pscope { display: none; }
.plost canvas { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; opacity: 0.85; }
.plost .bars { position: absolute; left: 0; right: 0; top: 0; height: 22%; background: linear-gradient(90deg, #c0c0c0 0 14%, #c0c000 0 28%, #00c0c0 0 43%, #00c000 0 57%, #c000c0 0 71%, #c00000 0 86%, #0000c0 0); opacity: 0.55; }
.plost b { position: absolute; left: 0; right: 0; top: 40%; font-size: clamp(14px, 1.6vw, 24px); color: #fff; letter-spacing: 2px; text-shadow: 2px 2px 0 #000; transform: rotate(-3deg); }
.plost span { position: absolute; left: 0; right: 0; top: calc(40% + clamp(18px, 2vw, 30px)); font-size: clamp(10px, 0.9vw, 14px); color: #ffe14d; text-shadow: 1px 1px 0 #000; }
#pipLive .pcross { display: none; }
body.pip-on #feed { top: var(--pip-b, 14px); }
body.pip-on #votePanel { top: max(34%, var(--pip-b, 0px)); } /* (the end-of-match vote shows up during the play of the round) */
`;

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function box(id) {
  const b = el('div', 'pipbox'); b.id = id;
  const lost = el('div', 'plost'), cv = el('canvas');
  cv.width = 64; cv.height = 36;
  lost.append(cv, el('div', 'bars'), el('b', '', 'SIGNAL LOST'), el('span'));
  b.append(el('div', 'pcross'), el('div', 'pscope'), lost, el('div', 'plab'));
  return { el: b, lab: b.querySelector('.plab'), cv, msg: lost.querySelector('span'), noiseT: 0 };
}
function initUI() {
  const s = el('style'); s.textContent = CSS; document.head.append(s);
  const root = el('div'); root.id = 'pipWrap'; root.className = 'hidden';
  const pov = box('pipPov'), live = box('pipLive');
  const dot = el('i');
  live.lab.append(dot, 'LIVE REACTION');
  root.append(pov.el, live.el);
  (document.getElementById('replay') || document.body).append(root);
  ui = { root, pov, live, dot, ph: -1 };
}

// the replay calls these
export function pipStart(state) {
  st = state;
  boxes.pov.has = boxes.live.has = false; boxes.live.cam = boxes.live.off = null; lay = null; turn = 0;
  if (!ui) initUI();
  const inf = (st.clip.info || {})[st.opts.focus] || {};
  ui.pov.lab.replaceChildren(el('b', '', inf.name || '???'), ' POV');
  ui.pov.lab.style.setProperty('--kc', inf.color || '#fff');
  ui.pov.lab.title = '';
}
export function pipStop() {
  st = null;
  if (ui) ui.root.classList.add('hidden');
  document.body.classList.remove('pip-on');
}

// where the boxes go (css px) and the same rect in the canvas' own (low-res) pixels
function layout() {
  const vw = innerWidth, vh = innerHeight, epic = !!document.querySelector('#replay.epic');
  const top = Math.round(16 + (epic ? vh * 0.08 : 0)), gap = 8;
  const w = Math.round(Math.max(140, Math.min(440, vw * 0.22, ((vh * 0.56 - top - gap) / 2) * 16 / 9))), h = Math.round(w * 9 / 16);
  const key = `${vw}x${vh}|${top}|${G.renderer.domElement.width}`;
  if (lay && lay.key === key) return lay;
  G.renderer.getSize(sz);
  const sx = sz.x / vw, sy = sz.y / vh, left = vw - 16 - w;
  const rect = (y) => ({ css: [left, y, w, h], px: [Math.round(left * sx), Math.round(sz.y - (y + h) * sy), Math.max(16, Math.round(w * sx)), Math.max(9, Math.round(h * sy))] });
  lay = { key, pov: rect(top), live: rect(top + h + gap), bottom: top + 2 * h + gap + 10, W: sz.x, H: sz.y };
  for (const k of ['pov', 'live']) {
    const [x, y, ww, hh] = lay[k].css, s = ui[k].el.style;
    s.left = x + 'px'; s.top = y + 'px'; s.width = ww + 'px'; s.height = hh + 'px';
    const [, , pw, ph] = lay[k].px, b = boxes[k];
    if (!b.rt) {
      b.rt = new THREE.WebGLRenderTarget(pw, ph, { magFilter: THREE.NearestFilter, minFilter: THREE.NearestFilter });
      // render into it exactly like into the screen (srgb out, plain rgba8 storage): a normal render target makes three swap
      // every material's shader program on every pass, and that cost far more than the passes themselves
      b.rt.isXRRenderTarget = true; b.rt.texture.colorSpace = THREE.SRGBColorSpace; b.rt.texture.internalFormat = 'RGBA8';
    }
    else b.rt.setSize(pw, ph);
    b.has = false;
  }
  document.body.style.setProperty('--pip-b', lay.bottom + 'px');
  return lay;
}

// a funny static card instead of a picture (killer left / died / is you)
function lost(k, why) {
  const b = boxes[k], u = ui[k];
  if (b.lost !== why) { b.lost = why; b.has = false; u.el.classList.toggle('lost', !!why); if (why) u.msg.textContent = why; }
  if (!why) return;
  const now = performance.now();
  if (now - u.noiseT < 70) return;
  u.noiseT = now;
  const g = u.cv.getContext('2d'), im = g.createImageData(64, 36), d = im.data;
  for (let i = 0; i < d.length; i += 4) { const v = Math.random() * 255 | 0; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
  g.putImageData(im, 0, 0);
}

// ------------------------------------------------------------ POV: through the killer's eyes, in the replay
function viewmodel(g) {
  const id = g.w;
  if (!id || !VM[id]) return null;
  const key = id + JSON.stringify((g.skins || {})[id] || '');
  let m = vms.get(key);
  if (!m) { // their gun with their skin, held like yours (same poses as weapons.js), and a fist
    const cfg = VM[id], wrap = new THREE.Group(), w = buildWeapon(id, (g.skins || {})[id]);
    w.scale.setScalar(cfg.s);
    wrap.add(w);
    const hand = new THREE.Mesh(new THREE.BoxGeometry(0.052, 0.062, 0.09), M(0xf1c27d));
    hand.position.set(0.004, -0.042, 0.03);
    wrap.add(hand);
    m = { wrap, w, cfg };
    vms.set(key, m);
  }
  if (id === 'katana') setKatana(m.w, g.katN || 0);
  return m;
}
function povPass(f, now) {
  const w = WEAPONS[f.w], ads = !!(f.f & FLAGS.ADS) && !!(w && w.ads), scoped = ads && !!w.ads.scope;
  ui.pov.el.classList.toggle('scoped', scoped);
  povCam.position.set(f.pos[0], f.pos[1] + (f.f & FLAGS.SLIDE ? 0.95 : f.f & FLAGS.CROUCH ? 1.05 : 1.6), f.pos[2]);
  povCam.rotation.set(f.pitch, f.yaw, 0);
  const fov = ads ? FOV / (w.ads.zoom || 1) : FOV;
  if (povCam.fov !== fov) { povCam.fov = fov; povCam.updateProjectionMatrix(); }
  // the gun: hip pose, slid to the middle while aiming, kicked back on every shot, swung on melee
  const m = viewmodel(f);
  if (vm !== m) { if (vm) vmScene.remove(vm.wrap); vm = m; if (m) vmScene.add(m.wrap); }
  if (m) {
    const c = m.cfg, a = ads ? 1 : 0, kick = Math.max(0, 1 - (now - (f.shotT || -1e9)) / 140), sw = (now - (f.swingT || -1e9)) / 380;
    const bob = Math.min(1, Math.hypot(f.vel[0], f.vel[2]) / 10) * 0.012, ph = now * 0.012;
    m.wrap.position.set(c.p[0] * (1 - a * 0.9) + Math.sin(ph) * bob, c.p[1] * (1 - a * 0.45) + Math.abs(Math.cos(ph)) * bob, c.p[2] + kick * 0.05);
    m.wrap.rotation.set(c.r[0] * (1 - a) + kick * 0.15, c.r[1] * (1 - a), c.r[2] * (1 - a));
    if (sw >= 0 && sw < 1) { const k = Math.sin(sw * Math.PI); m.wrap.rotation.y += (sw < 0.35 ? 1 : -1) * k * 1.1; m.wrap.rotation.x -= k * 0.5; }
    m.wrap.visible = !scoped && !(f.f & FLAGS.BALL) && f.ch.body.visible !== false;
  }
  // their own ghost would be in the way of their own eyes
  const hide = [f.ch.root, f.shadow], was = hide.map((o) => o.visible);
  for (const o of hide) o.visible = false;
  render(boxes.pov, povCam, true);
  hide.forEach((o, i) => { o.visible = was[i]; });
}

// ------------------------------------------------------------ LIVE: the killer right now, in the real game
function livePass(r, dt) {
  // the replay owns the scene: its ghosts + projectiles go away, the live players come back, just for this pass
  const off = [];
  const hide = (o) => { if (o && o.visible) { off.push(o); o.visible = false; } };
  for (const g of st.ghosts.values()) { hide(g.ch.root); hide(g.rope); hide(g.shadow); if (g.soap) hide(g.soap.mesh); }
  for (const m of st.projs.values()) hide(m);
  const rt = performance.now() + G.offset - INTERP, now = performance.now();
  for (const o of G.remotes.values()) { o.update(rt, dt, now); o.distScale = 1; o.ch.root.scale.setScalar(1.2); }
  for (const p of G.projs.values()) if (p.mesh) p.mesh.visible = true;
  r.tag.visible = false; r.marker.visible = false;
  // in front of their face, a bit to the side, following their turning (smoothly: spinbots exist)
  const head = tv.set(r.pos[0], r.pos[1] + (r.f & FLAGS.CROUCH ? 1.35 : 1.85), r.pos[2]);
  const B = boxes.live, k = Math.min(1, dt * 5);
  if (!B.cam) B.yaw = r.yaw;
  let d = r.yaw - B.yaw; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2;
  B.yaw += d * k;
  // front-right, front-left, straight on, then the sides: whichever has room (the last pick wins ties, so it doesn't flip)
  let best = null;
  for (const off of [B.off ?? 0.42, 0.42, -0.42, 0, 1.3, -1.3]) {
    const a = B.yaw + off, dir = [-Math.sin(a) * 0.987, 0.16, -Math.cos(a) * 0.987];
    const hit = raycast([head.x, head.y, head.z], dir, 2.9, BOXES), free = hit ? Math.max(0.6, hit.t - 0.3) : 2.9;
    if (!best || free > best.free + 0.3) best = { off, dir, free };
    if (free >= 2.9) break;
  }
  B.off = best.off;
  tv2.set(head.x + best.dir[0] * best.free, head.y + best.dir[1] * best.free, head.z + best.dir[2] * best.free);
  if (!B.cam || B.cam.distanceTo(tv2) > 12) B.cam = tv2.clone(); else B.cam.lerp(tv2, k);
  liveCam.position.copy(B.cam);
  liveCam.lookAt(head.x, head.y - 0.3, head.z);
  render(B, liveCam, false);
  for (const o of off) o.visible = true;
  for (const o of G.remotes.values()) { o.ch.root.visible = false; o.rope.visible = false; o.shadow.visible = false; o.tag.visible = !o.ghost; }
  for (const p of G.projs.values()) if (p.mesh) p.mesh.visible = false;
}

// draw a pass into its box's render target (particle sizes follow its height, then go back)
function render(b, cam, withVm) {
  const r = G.renderer, keep = scaleU.value;
  scaleU.value = b.rt.height / (2 * Math.tan((cam.fov * Math.PI) / 360));
  cam.updateMatrixWorld();
  r.setRenderTarget(b.rt);
  r.clear();
  r.render(G.scene, cam);
  if (withVm && vm) { r.clearDepth(); r.render(vmScene, vmCam); }
  r.setRenderTarget(null);
  scaleU.value = keep;
  b.has = true;
}
function paste(b, px) {
  const r = G.renderer;
  blitMat.uniforms.map.value = b.rt.texture;
  r.setViewport(px[0], px[1], px[2], px[3]);
  r.setScissor(px[0], px[1], px[2], px[3]);
  r.setScissorTest(true);
  r.render(blitScene, blitCam);
  r.setScissorTest(false);
}

// once a frame, after the main view is drawn. returns how many boxes were re-rendered (for the frame-time test)
export function renderPip(dt, now) {
  const on = !!st && G.settings.pip !== false;
  const f = on ? st.ghosts.get(st.opts.focus) : null;
  if (!on || !f) { if (ui && !ui.root.classList.contains('hidden')) { ui.root.classList.add('hidden'); document.body.classList.remove('pip-on'); } return 0; }
  if (ui.root.classList.contains('hidden')) { ui.root.classList.remove('hidden'); document.body.classList.add('pip-on'); }
  const L = layout();
  // the LIVE dot pulses from here, 4 steps a second (a css animation made software-composited frames ~15% slower)
  const ph = Math.floor(now / 250) % 4;
  if (ph !== ui.ph) { ui.ph = ph; ui.dot.style.opacity = [1, 0.6, 0.25, 0.6][ph]; ui.dot.style.transform = `scale(${[1, 0.85, 0.65, 0.85][ph]})`; }
  // budget: at most one box per frame, alternating; on slow frames (under ~40 / ~25 fps) only every 2nd / 3rd frame
  const ms = lastNow ? now - lastNow : 16;
  lastNow = now;
  ema += (Math.min(200, ms) - ema) * 0.1;
  liveDt += dt;
  const every = ema > 40 ? 3 : ema > 25 ? 2 : 1;
  let did = 0;
  const id = st.opts.focus, r = G.remotes.get(id);
  lost('pov', f.alive || !f.buf.length ? null : 'they died too. karma');
  const fresh = r && r.buf.length && performance.now() + G.offset - r.buf[r.buf.length - 1].t < 1500;
  lost('live', id === G.myId ? "it's you. hi you" : !r ? (f.bot ? 'the bot got unplugged' : 'they rage quit') : !r.alive ? 'they died lol. karma' : !fresh ? 'connection: potato' : null);
  const want = ['pov', 'live'].filter((k) => !boxes[k].lost && (k === 'live' || f.buf.length)); // (no POV till their ghost has a snapshot)
  const due = PIP.force ? want.filter((k) => PIP.force === true || PIP.force === k) : want.filter((k) => !boxes[k].has);
  if (!due.length && want.length && ++tick % every === 0) due.push(want[turn++ % want.length]);
  for (const k of due.slice(0, boxes.pov.has || boxes.live.has ? PIP.force ? 2 : 1 : 2)) {
    if (k === 'pov') povPass(f, now); else { livePass(r, Math.min(0.25, liveDt)); liveDt = 0; }
    did++;
  }
  PIP.renders += did; PIP.every = every;
  G.renderer.getSize(sz);
  for (const k of want) if (boxes[k].has) paste(boxes[k], L[k].px);
  G.renderer.setViewport(0, 0, sz.x, sz.y);
  return did;
}
