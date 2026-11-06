// Bubble Wand (item, G): soap bubbles in flight, people sealed in giant bubbles (what everyone sees), your own view
// from inside one, and the little wand you blow through. The server decides who is sealed in and for how long
// ('trap' / 'trapx', forwarded by main.js); movement is ours, so player.js floats us along while ME.trapUntil runs.
import * as THREE from 'three';
import { ITEMS } from '/shared/weapons.js';
import { soapAt, TRAP, trapBoxes } from '/shared/wand.js';
import { G } from './ctx.js';
import { ME, eye, releaseHook } from './player.js';
import { W } from './weapons.js';
import { soapBubble, soapFlail, M } from './models.js';
import { fx } from './fx.js';
import { sfx, loopSfx, setMuffle, stopLoops } from './audio.js';
import { hud } from './hud.js';
import { RP } from './replay.js';
import { authored, whenLate } from './glbkit.js'; // the Blender wand (tools/blender/make_wand.py)

const traps = new Map(); // player id -> { id, until, born, mesh }
const live = new Map(); // soap bubbles in flight, so we can pop them when the server takes one away
const bursts = []; // giant bubbles mid-pop
const nameOf = (id) => (G.names.get(id) || {}).name || '???';
const ease = (x) => x * x * (3 - 2 * x);

// ------------------------------------------------------------ soap bubbles in flight (main.js hands us every k === 'soap')
export function stepSoap(pr, dt, now) {
  if (!pr.p0) {
    pr.p0 = pr.p.slice(); pr.v0 = pr.v.slice(); pr.t0 = now;
    live.set(pr.id, pr);
    if (pr.o === G.myId) sfx.bloop(); // everyone else hears theirs from the 'ps'
  }
  const t = (now - pr.t0) / 1000;
  soapAt(pr.p0, pr.v0, pr.id, t, pr.p); // same path the server flies it on
  const k = Math.sin(t * 11 + pr.id) * 0.08;
  pr.mesh.position.set(pr.p[0], pr.p[1], pr.p[2]);
  pr.mesh.scale.set(1 + k, 1 - k, 1 + k * 0.6);
  pr.mesh.visible = !RP.active;
}

// ------------------------------------------------------------ sealed in / popped
export function trapStart(m) {
  const now = performance.now();
  drop(m.id);
  traps.set(m.id, { id: m.id, until: now + m.left, born: now, mesh: null });
  if (m.id === G.myId) {
    if (!ME.alive) return;
    ME.trapUntil = now + m.left; ME.trapV = m.v.slice();
    releaseHook();
    Object.assign(W, { held: false, aimHeld: false, dashHeld: false, draw: 0, charge: 0, exhale: 0, pendingSwing: 0, pendingThrow: 0 }); // you drop everything
    stopLoops();
    setMuffle(true);
    sfx.glorp();
    fx.droplets(eye(), 1.2, 30);
    hud.msg(m.by && m.by !== G.myId ? `BUBBLED BY ${nameOf(m.by)}` : 'BUBBLED', 1.6, 'slip');
    G.shake = Math.max(G.shake, 0.3);
    return;
  }
  const r = G.remotes.get(m.id);
  if (r) { r.trapUntil = now + m.left; sfx.glorp(r.pos); fx.droplets([r.pos[0], r.pos[1] + 1.1, r.pos[2]], 1, 24); }
  if (m.by === G.myId) hud.msg(`BUBBLED ${nameOf(m.id)}`, 1.3, 'brag');
}
export function trapEnd(m) {
  const T = traps.get(m.id);
  const loud = m.why !== 'gone'; // 'gone' = they respawned / the round reset: just tidy up
  traps.delete(m.id);
  const r = G.remotes.get(m.id);
  if (r) { r.trapUntil = 0; delete r.hitboxes; }
  if (m.id === G.myId) { if (m.p && ME.alive) ME.pos = m.p.slice(); if (ME.trapUntil) endMine(loud); } // p: we weren't where the bubble went
  else if (T && T.mesh) burst(T, loud);
  if (m.pb === G.myId && m.why === 'hit' && m.id !== G.myId) { hud.hit(false); hud.msg(`POPPED ${nameOf(m.id)}`, 0.9); }
}
function endMine(loud) {
  ME.trapUntil = 0;
  setMuffle(false, true);
  loopSfx('soapy', false);
  showOverlay(false, loud);
  if (!loud) return;
  sfx.bigPop();
  fx.droplets(eye(), 1.3, 60);
  G.shake = Math.max(G.shake, 0.45);
  hud.msg('POP!', 0.8, 'slip');
}
function burst(T, loud) {
  const m = T.mesh;
  T.mesh = null;
  if (!loud) { G.scene.remove(m); m.material.dispose(); return; }
  const p = m.position.toArray();
  sfx.bigPop(p);
  fx.droplets(p, m.scale.x, 70);
  G.shake = Math.max(G.shake, 0.5 - Math.hypot(p[0] - ME.pos[0], p[1] - ME.pos[1], p[2] - ME.pos[2]) / 30);
  bursts.push({ mesh: m, t: 0 }); // a quick swell and fade, see updateWand
}
function drop(id) {
  const T = traps.get(id);
  if (T && T.mesh) { G.scene.remove(T.mesh); T.mesh.material.dispose(); }
  traps.delete(id);
  const r = G.remotes.get(id);
  if (r) { r.trapUntil = 0; delete r.hitboxes; }
}
// a sealed-in player can be hit anywhere on their bubble (the server just pops it). stands in for Remote.hitboxes
function bubbleBoxes() { return trapBoxes(this.pos, this.distScale || 1); }

// main.js asks before every attack, item, streak, grapple and dash: no to all of it while you're sealed in
let nopeT = 0;
export function stuckInBubble(nope) {
  const now = performance.now(), stuck = G.joined && ME.alive && now < (ME.trapUntil || 0);
  if (stuck && nope && now - nopeT > 700) { nopeT = now; sfx.blub(); hud.msg('you are in a bubble', 0.7, 'slip'); }
  return stuck;
}

// ------------------------------------------------------------ every frame (after the remotes have moved)
export function updateWand(dt, now) {
  if (!G.joined) { if (traps.size || bursts.length || ME.trapUntil) reset(); stepVM(dt); return; }
  // me: a soap film round the edges of the screen, everything muffled, the world swaying a little
  const mine = ME.alive && now < (ME.trapUntil || 0);
  if (ME.trapUntil && !mine) endMine(ME.alive); // our timer ran out a hair before the server's pop arrived (or we died)
  showOverlay(mine);
  loopSfx('soapy', mine);
  if (mine) {
    W.held = false; W.dashHeld = false;
    const left = Math.max(0, ME.trapUntil - now) / 1000;
    hud.meter(left / ITEMS.wand.dur, `IN A BUBBLE · pops in ${left.toFixed(1)}s`, '#9fe8ff');
    if (G.punch) { G.punch.vz += Math.sin(now * 0.0021) * 7 * dt; G.punch.vx += Math.sin(now * 0.0016 + 1) * 3 * dt; }
    if (Math.random() < dt * 1.6) sfx.blub();
  }
  // everyone else in a bubble: a big shimmering one round their mannequin, and they flail about in it
  for (const T of traps.values()) {
    if (T.id === G.myId) continue;
    const r = G.remotes.get(T.id);
    if (now > T.until + 1500 || (r && !r.alive) || (!r && T.mesh)) { drop(T.id); continue; } // over, dead, or they left
    if (!r) continue; // we only just joined: they show up with the next snapshot
    r.trapUntil = T.until;
    if (r.hitboxes !== bubbleBoxes) r.hitboxes = bubbleBoxes;
    if (!T.mesh) { T.mesh = soapBubble(1, 28, 0.025); G.scene.add(T.mesh); }
    const ds = r.distScale || 1, age = (now - T.born) / 1000, left = (T.until - now) / 1000;
    const x = Math.min(1, age / 0.3) - 1, grow = 1 + 2.70158 * x * x * x + 1.70158 * x * x; // pops in with an overshoot
    T.mesh.position.set(r.pos[0], r.pos[1] + TRAP.y * ds, r.pos[2]);
    T.mesh.scale.setScalar(TRAP.r * ds * Math.max(0.2, grow));
    T.mesh.material.uniforms.uWob.value = 0.025 + (left < 1 ? (1 - Math.max(0, left)) * 0.07 : 0); // shakier right before it pops
    T.mesh.visible = r.ch.root.visible;
    soapFlail(r.ch, now * 0.001 + T.id);
  }
  // soap bubbles the server just took away (hit a wall, sealed someone in, ran out of life): pop
  for (const [id, pr] of live) if (!G.projs.has(id)) { live.delete(id); fx.droplets(pr.p, 0.36, 10); sfx.plip(pr.p); }
  for (let i = bursts.length - 1; i >= 0; i--) {
    const b = bursts[i];
    b.t += dt;
    if (b.t >= 0.14) { G.scene.remove(b.mesh); b.mesh.material.dispose(); bursts.splice(i, 1); continue; }
    b.mesh.scale.multiplyScalar(1 + dt * 2.4);
    b.mesh.material.uniforms.uAlpha.value = 1 - b.t / 0.14;
  }
  stepVM(dt);
}
function reset() {
  for (const id of [...traps.keys()]) drop(id);
  for (const b of bursts) G.scene.remove(b.mesh);
  bursts.length = 0;
  live.clear();
  if (ME.trapUntil) { ME.trapUntil = 0; setMuffle(false, true); }
  loopSfx('soapy', false);
  showOverlay(false);
}

// ------------------------------------------------------------ the wand you blow through (viewmodel, bottom left)
let vm = null, blowT = -1, lastItemT = 0;
const LOW = [-0.15, -0.34, -0.3], MOUTH = [-0.055, -0.085, -0.22];
// the wand + its soap film. the Blender wand (x_wand.glb) has its ring centre at the origin like ours
export function wandMesh() {
  const g = new THREE.Group();
  const bl = authored('x_wand');
  if (bl) { g.add(bl.obj); g.userData.glb = 'blender'; } else {
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.0055, 0.007, 0.15, 6), M(0xff7ad8));
    stick.position.y = -0.105;
    g.add(stick, new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.0055, 6, 16), M(0xff7ad8)));
  }
  const film = soapBubble(1, 12, 0);
  film.scale.set(0.03, 0.03, 0.004);
  g.add(film);
  g.userData.film = film;
  return g;
}
function wandVM() {
  if (vm) return vm;
  vm = wandMesh();
  vm.visible = false;
  G.vmScene.add(vm);
  return vm;
}
whenLate('x_wand', () => { if (vm && blowT < 0) { vm.removeFromParent(); vm = null; } }); // it landed: the next blow uses it
function stepVM(dt) {
  if (W.itemT && W.itemT !== lastItemT) { lastItemT = W.itemT; if (W.item === 'wand') blowT = 0; } // you just used it
  if (blowT < 0) return;
  const m = wandVM();
  blowT += dt;
  if (blowT > 0.85 || !ME.alive || !G.joined) { blowT = -1; m.visible = false; return; }
  const up = blowT < 0.13 ? ease(blowT / 0.13) : blowT > 0.62 ? 1 - ease(Math.min(1, (blowT - 0.62) / 0.23)) : 1;
  for (let i = 0; i < 3; i++) m.position.setComponent(i, LOW[i] + (MOUTH[i] - LOW[i]) * up);
  m.rotation.set(0.15 * (1 - up), 0.35, -0.25 + Math.sin(blowT * 30) * 0.08 * up);
  // the film bulges out each time a bubble leaves the ring
  const blowing = blowT > 0.1 && blowT < 0.1 + ITEMS.wand.bubbles * (ITEMS.wand.gap / 1000);
  m.userData.film.scale.z = blowing ? 0.004 + (((blowT - 0.1) * 1000) % ITEMS.wand.gap) / ITEMS.wand.gap * 0.03 : 0.004;
  m.visible = !W.scoped;
}

// ------------------------------------------------------------ inside a bubble: you see everything through the film
// a faint swirl over the whole view, thick rainbow film toward the edges, a bright rim all the way round where the
// wall curves away, and the whole thing wobbles
let ov = null, ovOn = false, popT = 0;
const CSS = `
#bubbleFx { position: absolute; inset: 0; pointer-events: none; overflow: hidden; opacity: 0; transition: opacity 0.35s; }
#bubbleFx.on { opacity: 1; }
#bubbleFx.pop { transition: opacity 0.16s ease-out; }
#bubbleFx .wob { position: absolute; inset: -4%; animation: bubWob 2.3s ease-in-out infinite alternate; }
#bubbleFx.pop .wob { animation: none; transform: scale(1.5); transition: transform 0.16s ease-out; }
#bubbleFx .all, #bubbleFx .edge { position: absolute; inset: 0; overflow: hidden; }
#bubbleFx .all { opacity: 0.14; }
#bubbleFx .edge { opacity: 0.62; -webkit-mask-image: radial-gradient(ellipse 50% 50% at 50% 50%, transparent 44%, #000 96%); mask-image: radial-gradient(ellipse 50% 50% at 50% 50%, transparent 44%, #000 96%); }
#bubbleFx .film { position: absolute; left: 50%; top: 50%; width: 170vmax; height: 170vmax; margin: -85vmax 0 0 -85vmax;
  background: conic-gradient(#ff8ad8, #ffe680, #8dffb8, #7ad8ff, #c39bff, #ff8ad8); animation: bubSpin 9s linear infinite; }
#bubbleFx .all .film { animation-duration: 14s; animation-direction: reverse; }
#bubbleFx .rim { position: absolute; inset: 3%; border-radius: 50%; border: 3px solid rgba(255, 255, 255, 0.55);
  box-shadow: inset 0 0 26px 4px rgba(255, 255, 255, 0.5), inset 0 0 120px 24px rgba(170, 225, 255, 0.3), 0 0 22px 3px rgba(255, 255, 255, 0.4), 0 0 0 100vmax rgba(215, 240, 255, 0.28); }
#bubbleFx .glint { position: absolute; left: 11%; top: 10%; width: 30%; height: 18%; border-radius: 50%; border-top: 7px solid rgba(255, 255, 255, 0.6); transform: rotate(-20deg); filter: blur(1px); }
#bubbleFx .glint.b { left: auto; top: auto; right: 12%; bottom: 12%; width: 16%; height: 10%; border-top: 0; border-bottom: 5px solid rgba(255, 255, 255, 0.45); }
#bubbleFx .tint { position: absolute; inset: 0; background: radial-gradient(ellipse 60% 60% at 50% 50%, rgba(190, 235, 255, 0.05) 40%, rgba(160, 215, 255, 0.22) 100%); }
@keyframes bubWob { from { transform: scale(1, 1.035) rotate(-0.7deg); } to { transform: scale(1.04, 0.985) rotate(0.7deg); } }
@keyframes bubSpin { to { transform: rotate(360deg); } }`;
function showOverlay(on, popped) {
  if (on === ovOn && !popped) return;
  if (!ov) {
    const st = document.createElement('style');
    st.textContent = CSS;
    document.head.append(st);
    ov = document.createElement('div');
    ov.id = 'bubbleFx';
    ov.innerHTML = '<div class="tint"></div><div class="wob"><div class="all"><div class="film"></div></div><div class="edge"><div class="film"></div></div>' +
      '<div class="rim"></div><div class="glint"></div><div class="glint b"></div></div>';
    const ref = document.getElementById('freezeFx'); // under the crosshair and the rest of the HUD
    if (ref) ref.after(ov); else document.body.append(ov);
  }
  ovOn = on;
  ov.classList.toggle('on', on);
  if (on) ov.classList.remove('pop');
  else if (popped) { ov.classList.add('pop'); clearTimeout(popT); popT = setTimeout(() => ov.classList.remove('pop'), 350); }
}
