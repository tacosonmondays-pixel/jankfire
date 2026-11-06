// Instant Camera (item, G): the photos, the frames they print into, going through one, and the camera in your hands.
// Nobody uploads a picture: the server says where a photo was taken ('snap': spot + yaw + pitch) and every client
// renders that view itself, right then, so everyone's copy has the people who were standing there in it. A frame
// ('frame') shows that photo; walking into one is the server's call ('ptp' moves you, 'fx' 'tele' is the show).
import * as THREE from 'three';
import { PHOTO } from '/shared/weapons.js';
import { PH } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME, releaseHook } from './player.js';
import { W } from './weapons.js';
import { instantCamera, photoFrame, FRAME } from './gearmodels.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';
import { RP, RP_HOOKS, recordEv } from './replay.js';
import { whenLate } from './glbkit.js';

const photos = new Map(); // photo n -> { tex, url, by }
const frames = new Map(); // live frames: id -> F
const ghostFrames = new Map(); // the same in a replay
let mine = 0; // the photo n you're holding (0 = none)
const ease = (x) => x * x * (3 - 2 * x);
const nameOf = (id) => (G.names.get(id) || {}).name || '???';

// ------------------------------------------------------------ taking the picture (every client, from the server's pose)
let rt = null, pcam = null, px = null, film = null;
function renderPhoto(n, by, p, yaw, pitch) {
  const S = PHOTO.res, R = G.renderer;
  if (!R || !G.scene) return null;
  if (!rt) {
    rt = new THREE.WebGLRenderTarget(S, S, { depthBuffer: true });
    rt.texture.colorSpace = THREE.SRGBColorSpace;
    pcam = new THREE.PerspectiveCamera(72, 1, 0.1, 1500); pcam.rotation.order = 'YXZ';
    px = new Uint8Array(S * S * 4);
  }
  pcam.position.set(p[0], p[1] + PH.eye, p[2]);
  pcam.rotation.set(pitch, yaw, 0);
  pcam.updateMatrixWorld();
  // the photographer isn't in their own photo (the camera is in their head)
  const r = G.remotes.get(by), was = r && r.ch.root.visible;
  if (r) { r.ch.root.visible = false; if (r.tag) r.tag.visible = false; }
  const hidden = [];
  for (const o of [...G.remotes.values()]) if (o.tag && o.tag.visible) { o.tag.visible = false; hidden.push(o); } // no name tags in the picture
  const prev = R.getRenderTarget(), ac = R.autoClear;
  R.setRenderTarget(rt); R.autoClear = true; R.render(G.scene, pcam); R.autoClear = ac; R.setRenderTarget(prev);
  if (r) r.ch.root.visible = was;
  for (const o of hidden) o.tag.visible = true;
  R.readRenderTargetPixels(rt, 0, 0, S, S, px);
  // onto a canvas (flipped: GL rows go bottom up), then the instant film look: warm, a bit faded, vignette, a date stamp
  const c = document.createElement('canvas'); c.width = c.height = S;
  const x = c.getContext('2d'), im = x.createImageData(S, S);
  for (let row = 0; row < S; row++) im.data.set(px.subarray((S - 1 - row) * S * 4, (S - row) * S * 4), row * S * 4);
  for (let i = 0; i < im.data.length; i += 4) {
    const d = im.data;
    d[i] = Math.min(255, d[i] * 0.92 + 22); d[i + 1] = Math.min(255, d[i + 1] * 0.9 + 14); d[i + 2] = Math.min(255, d[i + 2] * 0.82 + 18);
  }
  x.putImageData(im, 0, 0);
  const v = x.createRadialGradient(S / 2, S / 2, S * 0.3, S / 2, S / 2, S * 0.75);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(40,10,30,0.55)');
  x.fillStyle = v; x.fillRect(0, 0, S, S);
  const dt = new Date();
  x.font = 'bold 15px monospace'; x.fillStyle = '#ff8a2a'; x.textAlign = 'right';
  x.fillText(`'${String(dt.getFullYear()).slice(2)} ${dt.getMonth() + 1} ${dt.getDate()}`, S - 8, S - 9);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const P = { tex, by, url: null, c };
  const old = photos.get(n); if (old) old.tex.dispose();
  photos.set(n, P);
  // keep the last few (frames and replays still want them), drop the oldest
  if (photos.size > 24) { const k = photos.keys().next().value; if (![...frames.values()].some((F) => F.n === k)) { photos.get(k).tex.dispose(); photos.delete(k); } }
  return P;
}
function photoOf(n, pose, by) { return photos.get(n) || renderPhoto(n, by, pose.p, pose.y, pose.x); }

// ------------------------------------------------------------ server messages
export function onSnap(m) {
  recordEv(m);
  const P = renderPhoto(m.n, m.id, m.p, m.y, m.x);
  if (m.id === G.myId) {
    mine = m.n;
    if (P) thumb(P);
    hud.msg('PHOTO TAKEN · G TO PRINT IT', 1.6, 'brag');
  } else {
    const r = G.remotes.get(m.id);
    if (r) { sfx.shutter(r.pos); fx.blast([r.pos[0], r.pos[1] + 1.9, r.pos[2]], 0.4, 0xffffff, 0xffffff); }
  }
}
export function onPhotoNope(m) { hud.msg(`NO PHOTO: ${String(m.why || '').toUpperCase()}`, 1.4, 'slip'); sfx.empty && sfx.empty(); }
function buildFrame(m, scene) {
  const P = photoOf(m.ph.n, m.ph, m.o);
  const mesh = photoFrame(P ? P.tex : null);
  mesh.position.set(m.p[0], m.p[1], m.p[2]);
  mesh.rotation.y = m.y;
  mesh.scale.setScalar(0.01);
  scene.add(mesh);
  return { id: m.id, o: m.o, n: m.ph.n, mesh, born: performance.now(), until: performance.now() + (m.left ?? PHOTO.life * 1000), going: 0 };
}
export function onFrame(m) {
  recordEv(m);
  dropFrame(frames, m.id, true);
  const F = buildFrame(m, G.scene);
  frames.set(m.id, F);
  if (m.o === G.myId) { mine = 0; thumb(null); }
  sfx.printWhirr(m.p); sfx.framePop(m.p);
  fx.spray([m.p[0], m.p[1] + 1.2, m.p[2]], 30, [0xff4fd8, 0xffffff, 0xffe14d], 6, 1, 0.12, 8, 1);
}
export function onFrameGone(m) { recordEv(m); dropFrame(frames, m.id, m.why === 'gone'); }
function dropFrame(map, id, quiet) {
  const F = map.get(id);
  if (!F) return;
  map.delete(id);
  if (!quiet) { const p = F.mesh.position; fx.spray([p.x, p.y + 1.2, p.z], 40, [0xffffff, 0xf8f5ec, 0xff4fd8], 7, 1.2, 0.1, 9, 1); sfx.framePop([p.x, p.y, p.z]); }
  F.mesh.parent && F.mesh.parent.remove(F.mesh);
  F.mesh.traverse((o) => { if (o.isMesh && o.userData.noWrap && o.material.dispose && o.material.isShaderMaterial) o.material.dispose(); });
}
// you went through: there you are, facing the way the photo was taken
export function onPhotoTp(m) {
  if (!ME.alive) return;
  ME.pos = m.p.slice(); ME.vel = [0, 0, 0];
  ME.yaw = m.y; ME.pitch = m.x;
  releaseHook();
  sfx.photoIn();
  hud.flash(0.85, 0.35);
  G.shake = Math.max(G.shake, 0.4);
  hud.msg('WISH YOU WERE HERE', 1.3, 'brag');
}
// the show: someone went into a frame at a and came out at b
export function teleFx(m, ghosts) {
  const who = ghosts ? ghosts.get(m.id) : G.remotes.get(m.id);
  for (const [p, out] of [[m.a, false], [m.b, true]]) {
    fx.spray(p, out ? 50 : 34, [0xff4fd8, 0xffffff, 0x4fd8ff, 0xffe14d], out ? 9 : 6, 1.2, 0.12, 10, 1.2);
    fx.blast(p, out ? 1.6 : 1.1, 0xffffff, 0xff4fd8);
  }
  if (m.id !== G.myId || ghosts) { sfx.photoOut(m.a); sfx.photoIn(m.b); }
  if (who && who.buf) who.buf.length = 0; // don't slide them across the map between snapshots
  if (!ghosts && m.id !== G.myId) {
    const F = frames.get(m.f);
    if (F && F.o === G.myId) hud.msg(`${nameOf(m.id)} WENT IN YOUR PHOTO`, 1.2, 'brag');
  }
}

// ------------------------------------------------------------ every frame
function stepFrames(map, now, hide) {
  for (const F of map.values()) {
    const u = F.mesh.userData, age = (now - F.born) / 1000, left = (F.until - now) / 1000;
    // pops up out of the floor with a wobble, develops from brown over 1.6 s, flickers in its last 3 s
    const x = Math.min(1, age / 0.45) - 1, grow = 1 + 2.70158 * x * x * x + 1.70158 * x * x;
    F.mesh.scale.set(Math.max(0.01, grow), Math.max(0.01, Math.min(1.08, age / 0.3) * grow), Math.max(0.01, grow));
    u.inner.rotation.z = Math.sin(age * 9) * 0.06 * Math.exp(-age * 2.5);
    u.pm.uniforms.uT.value = now / 1000;
    u.pm.uniforms.uDev.value = Math.min(1, age / 1.6);
    u.pm.uniforms.uFade.value = left < 3 ? 0.55 + 0.45 * Math.round(0.5 + 0.5 * Math.sin(now * (0.012 + (3 - left) * 0.01))) : 1;
    u.pool.material.opacity = 0.18 + Math.sin(now * 0.004) * 0.07;
    F.mesh.visible = !hide;
  }
}
export function updatePhoto(dt, now) {
  if (!G.joined) { if (frames.size) for (const id of [...frames.keys()]) dropFrame(frames, id, true); mine = 0; thumb(null); stepVM(dt, now); return; }
  for (const [id, F] of frames) if (now > F.until + 1500) dropFrame(frames, id, true);
  stepFrames(frames, now, RP.active);
  if (mine && !ME.alive) { mine = 0; thumb(null); } // the photo goes with you when you die (the server forgets it too)
  stepVM(dt, now);
}
export function photoReset() { for (const id of [...frames.keys()]) dropFrame(frames, id, true); mine = 0; thumb(null); }
export function holdingPhoto() { return !!mine; }

// ------------------------------------------------------------ the photo you're holding, next to the item slot
let th = null;
function thumb(P) {
  if (!th) {
    th = document.createElement('div'); th.id = 'photoThumb';
    th.innerHTML = '<img alt=""><b>G: PRINT</b>';
    const st = document.createElement('style');
    st.textContent = `#photoThumb { position: absolute; left: 16px; bottom: 150px; width: 104px; padding: 7px 7px 26px; background: #f8f5ec;
      border: 3px solid #111; box-shadow: 6px 6px 0 #ff4fd8; transform: rotate(-4deg); pointer-events: none; display: none; z-index: 6; }
      #photoThumb img { display: block; width: 100%; image-rendering: auto; border: 1px solid #0003; }
      #photoThumb b { position: absolute; left: 0; right: 0; bottom: 4px; text-align: center; font: 700 14px var(--font, sans-serif); color: #111; }
      body.replaying #photoThumb { display: none !important; }`;
    document.head.append(st);
    document.body.append(th);
  }
  if (!P) { th.style.display = 'none'; return; }
  P.url ||= P.c.toDataURL('image/jpeg', 0.8);
  th.querySelector('img').src = P.url;
  th.style.display = 'block';
}

// ------------------------------------------------------------ the camera in your hands (viewmodel)
// snap: up to your eye, CLACK, a white flash, back down. print: up in front of you turned round, the print whirrs out of
// the slot showing your photo (developing), then you flick it forward and it becomes the frame
const VM = { g: null, print: null, anim: null, t: 0 };
whenLate('x_camera', () => { if (VM.g && !VM.anim) { VM.g.removeFromParent(); VM.g = null; VM.print = null; } }); // the Blender camera landed: the next snap uses it
let lastItemT = 0;
function camVM() {
  if (VM.g) return VM.g;
  VM.g = instantCamera();
  VM.print = VM.g.userData.print;
  VM.g.visible = false;
  G.vmScene.add(VM.g);
  return VM.g;
}
const SNAP = [ // t, pos, rot (x, y, z): up to just under your right eye (the viewfinder), CLACK, back down
  [0, [0.24, -0.42, -0.32], [-0.5, 0.3, 0.5]],
  [0.16, [0.06, -0.1, -0.24], [0.04, 0.1, 0.04]],
  [0.3, [0.055, -0.095, -0.23], [0, 0.08, 0.02]],
  [0.38, [0.055, -0.09, -0.21], [0.14, 0.08, -0.03]], // the shutter kick
  [0.52, [0.055, -0.095, -0.23], [0.02, 0.08, 0.02]],
  [0.85, [0.22, -0.42, -0.3], [-0.4, 0.25, 0.45]],
];
const PRINT = [ // turned round so the print comes out toward you (you watch it develop), then flicked forward
  [0, [0.1, -0.45, -0.32], [0.3, Math.PI, 0.4]],
  [0.2, [0.01, 0.01, -0.44], [0.45, Math.PI, 0.05]], // held up mid-screen, tipped so the print faces you (lower and it slid off the bottom)
  [0.82, [0, 0.02, -0.44], [0.4, Math.PI, -0.04]],
  [1.0, [0.02, 0.02, -0.42], [0.2, Math.PI, 0.0]],
  [1.3, [0.04, 0.05, -0.9], [-0.6, Math.PI, 0.3]], // flicked forward
];
// your photo on the print, turned the right way up for you (it comes out toward you top edge first, like a real one).
// a clone shares the photo's GPU texture, only its uv turn differs; one alive at a time
function vmPic(tex) {
  if (VM.pt && VM.pt.src === tex) return VM.pt.t;
  if (VM.pt) VM.pt.t.dispose();
  const t = tex.clone(); t.center.set(0.5, 0.5); t.rotation = Math.PI; t.needsUpdate = true;
  VM.pt = { src: tex, t };
  return t;
}
function samplePath(K, t) {
  if (t >= K[K.length - 1][0]) return null;
  let i = 0; while (i < K.length - 2 && K[i + 1][0] <= t) i++;
  const a = K[i], b = K[i + 1], k = ease(Math.max(0, Math.min(1, (t - a[0]) / (b[0] - a[0]))));
  return { p: a[1].map((v, j) => v + (b[1][j] - v) * k), r: a[2].map((v, j) => v + (b[2][j] - v) * k) };
}
function stepVM(dt, now) {
  if (W.itemT && W.itemT !== lastItemT) { // you just pressed G with the camera
    lastItemT = W.itemT;
    if (W.item === 'camera' && ME.alive) { VM.anim = W.camPrint ? 'print' : 'snap'; VM.t = 0; VM.fired = false; }
  }
  const g = camVM();
  if (!VM.anim || !ME.alive || !G.joined) { g.visible = false; VM.anim = null; return; }
  const t0 = VM.t; VM.t += dt;
  const a = samplePath(VM.anim === 'snap' ? SNAP : PRINT, VM.t);
  if (!a) { g.visible = false; VM.anim = null; VM.print.visible = false; return; }
  g.position.set(...a.p); g.rotation.set(...a.r); g.visible = !W.scoped;
  const ud = g.userData;
  if (VM.anim === 'snap') {
    if (t0 < 0.3 && VM.t >= 0.3) { sfx.shutter(); hud.flash(1, 0.22); G.shake = Math.max(G.shake, 0.15); }
    ud.shutter.position.z = -0.04 + (VM.t > 0.3 && VM.t < 0.45 ? 0.003 : 0);
    ud.flash.material.color.setHex(VM.t > 0.3 && VM.t < 0.4 ? 0xffffff : 0xcfc8b8);
    VM.print.visible = false;
  } else {
    // out of the slot toward you, developing as it comes
    const out = Math.max(0, Math.min(1, (VM.t - 0.2) / 0.55));
    VM.print.visible = VM.t > 0.18;
    VM.print.position.set(0, -0.04, -0.03 - out * 0.075);
    const P = photos.get(W.camN || mine);
    const pm = ud.pic.material;
    const pt = P && vmPic(P.tex);
    if (pt && pm.map !== pt) { pm.map = pt; pm.needsUpdate = true; }
    const dev = Math.max(0, Math.min(1, (VM.t - 0.3) / 0.8));
    pm.color.setRGB(0.25 + 0.75 * dev, 0.17 + 0.83 * dev, 0.12 + 0.88 * dev);
    if (t0 < 0.82 && VM.t >= 0.82) sfx.swing();
  }
}

// ------------------------------------------------------------ replays: frames standing, people going through
function ghostEv(m, ghosts) {
  if (m.t === 'snap') { if (!photos.has(m.n)) renderPhoto(m.n, m.id, m.p, m.y, m.x); return true; }
  if (m.t === 'frame') { dropFrame(ghostFrames, m.id, true); const F = buildFrame(m, G.scene); ghostFrames.set(m.id, F); sfx.framePop(m.p); return true; }
  if (m.t === 'framex') { dropFrame(ghostFrames, m.id, m.why === 'gone'); return true; }
  if (m.t === 'fx' && m.k === 'tele') { teleFx(m, ghosts); return true; }
  return false;
}
RP_HOOKS.push({
  ev: ghostEv,
  pre(m, ghosts, s, t0) { // a frame put up before the clip: already standing, already developed
    if (m.t === 'snap' && !photos.has(m.n)) renderPhoto(m.n, m.id, m.p, m.y, m.x);
    if (m.t === 'frame') { dropFrame(ghostFrames, m.id, true); const F = buildFrame(m, G.scene); F.born -= 5000; ghostFrames.set(m.id, F); }
    if (m.t === 'framex') dropFrame(ghostFrames, m.id, true);
  },
  step(t, ghosts, dt) { stepFrames(ghostFrames, performance.now(), false); },
  stop() { for (const id of [...ghostFrames.keys()]) dropFrame(ghostFrames, id, true); },
  preroll(ev, t0) { return ev.filter((e) => e.s < t0 && (e.m.t === 'frame' || e.m.t === 'snap' || e.m.t === 'framex')); },
});
export { FRAME };
