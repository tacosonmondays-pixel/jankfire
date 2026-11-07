// Plant & Defuse gunplay, client side (the rules are /shared/tactical.js): spray patterns, moving inaccuracy, the
// crosshair that shows it, quiet slow walk, footsteps you can hear, and no outlines / name tags on enemies.
// Everything here is off outside the mode (G.eco unset).
import { WEAPONS, FLAGS } from '/shared/weapons.js';
import { TAC, patternOf, patternAt, shotOffset, shotDir, shotSeed, tacSpread, landK } from '/shared/tactical.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { synth } from './audio.js';
import { sdRow } from '/shared/sdgun.js';
import { inSprayRange } from './sprayrange.js';

const $ = (id) => document.getElementById(id);
export const tacOn = () => !!G.eco;
const T = { q: 0, i: 0, lastT: -1e9, lastId: '', seed: 0, kick: [0, 0], recov: 0, sp: 0, cross: null };
const r4 = (x) => Math.round(x * 10000) / 10000;

// a new round (eround): the shot counter starts again with this round's seed
export function tacRound(n) { T.q = 0; T.i = 0; T.lastT = -1e9; T.seed = shotSeed(G.myId, n); T.kick = [0, 0]; }
// the server says where its shot count is (a refused shot): follow it
export function tacSync(q) { if (Number.isInteger(q) && q >= 0) T.q = q; }
const hs = () => Math.hypot(ME.vel[0], ME.vel[2]);
// the spread a shot would have right now, from the gun's own spread (`base`: sights, hipfire setting, no bloom)
export function tacSpreadNow(id, base, i = 0) {
  const v = ME.vel.map((x) => Math.round(x * 100) / 100); // what the server will see in the snapshot
  if (!ME.onGround || ME.hook) T.airT = performance.now(); // (on a rope counts as the air)
  return tacSpread(id, base, Math.hypot(v[0], v[2]), !ME.onGround || !!ME.hook, ME.crouching, i, landK(T.airT || -1e9, performance.now()));
}
// the spray index the next shot would get right now (for the crosshair's bloom)
function nextI(id, now) { const P = patternOf(id); return id === T.lastId && now - T.lastT <= (P ? P.reset : 400) ? T.i + 1 : 0; }
// S&D hit markers by zone: what your last shot at someone hit (the server's 'hurt' only says head or not)
const zones = new Map();
export function tacZone(id, h) { zones.set(id, { z: h.h ? 'h' : h.lg && h.lg >= h.n - h.h ? 'l' : 'b', t: performance.now() }); }
export function tacZoneOf(id) { const z = tacOn() && zones.get(id); return z && performance.now() - z.t < 900 ? z.z : null; }
// one shot: which spray shot it is, its spread, and a function giving pellet k's direction. call right before firing
export function tacShot(id, base, now) {
  const P = patternOf(id);
  if (id !== T.lastId || now - T.lastT > (P ? P.reset : 400)) T.i = 0;
  else T.i++;
  T.lastId = id; T.lastT = now;
  const q = T.q++, i = T.i, sp = tacSpreadNow(id, base, i), yaw = ME.yaw, pitch = ME.pitch, off = shotOffset(id, i);
  return {
    q, i, sp, dir: (k) => shotDir(yaw, pitch, off, sp, T.seed, q, k),
    msg: { q, i, a: [r4(yaw), r4(pitch)], sp: r4(sp) },
  };
}
// after the shot: the camera climbs by its share of the pattern (pull down against it to stay on target)
export function tacKick(id, i) {
  const a = patternAt(id, i), b = patternAt(id, i + 1), dx = (b[0] - a[0]) * TAC.view, dy = (b[1] - a[1]) * TAC.view;
  ME.pitch = Math.min(1.55, ME.pitch + dy); ME.yaw -= dx;
  T.kick[0] += dx; T.kick[1] += dy; T.recov = 0;
}
// every frame: after a pause the view drifts back down from the climb; the crosshair opens with your spread
export function tacFrame(dt, now, id, base) {
  if (!tacOn() && !(id && sdRow(id) && inSprayRange())) { if (T.cross) T.cross.classList.add('hidden'); document.body.classList.remove('tac'); return; } // (Training's spray range too)
  const P = id && patternOf(id);
  if (P && now - T.lastT > P.reset * 0.6 && (T.kick[0] || T.kick[1])) {
    const k = Math.min(1, dt * 7), dx = T.kick[0] * k, dy = T.kick[1] * k;
    ME.pitch -= dy; ME.yaw += dx; T.kick[0] -= dx; T.kick[1] -= dy;
    if (Math.abs(T.kick[1]) < 1e-4 && Math.abs(T.kick[0]) < 1e-4) T.kick = [0, 0];
  }
  cross(id && WEAPONS[id] && WEAPONS[id].kind === 'hitscan' ? tacSpreadNow(id, base, nextI(id, now)) : null);
}
function cross(sp) {
  if (!T.cross) {
    const c = T.cross = document.createElement('div');
    c.id = 'tacCross'; c.className = 'hidden';
    c.innerHTML = '<i class="t"></i><i class="b"></i><i class="l"></i><i class="r"></i><b></b>';
    $('hud').append(c);
  }
  const on = sp != null && ME.alive && !(G.settings && G.settings.sdNoCross); // (settings: keep the plain crosshair)
  document.body.classList.toggle('tac', on);
  T.cross.classList.toggle('hidden', !on);
  if (!on) return;
  // spread (rad) -> pixels at this field of view
  const cam = G.camera, h = G.renderer ? G.renderer.domElement.clientHeight : 720;
  const px = Math.round(Math.max(3, Math.min(260, (Math.tan(sp) * h) / (2 * Math.tan(((cam ? cam.fov : 90) * Math.PI) / 360)))));
  if (px !== T.px) { T.px = px; T.cross.style.setProperty('--g', px + 'px'); }
  const bad = sp > 0.05;
  if (bad !== T.bad) { T.bad = bad; T.cross.classList.toggle('wide', bad); }
}

// ------------------------------------------------------------ other players
// no outlines, name tags or far-away markers on enemies; teammates keep a small name tag (the one you watch has none)
export function tacLook(r) {
  const on = tacOn(), enemy = on && !!r.team && r.team !== G.myTeam;
  if (r.shells && (on || r._tacE) && (r._tacE !== enemy || r._tacSh !== r.shells)) { r._tacE = enemy; r._tacSh = r.shells; for (const s of r.shells) s.visible = !enemy; } // (a rebuilt model has new shells)
  if (!on) { if (r._tacOn) { r._tacOn = false; r.tag.visible = true; } return; } // the mode ended: tags back
  r._tacOn = true;
  if (enemy) { r.tag.visible = false; r.marker.visible = false; return; }
  r.tag.visible = !(G.eco && G.eco.spec === r.id);
  r.tag.scale.set(1.1, 0.28, 1); r.tag.position.y = 2.25;
}
// footsteps: anyone running on the floor thuds (louder the faster); slow walking (WALK) and crouching are silent
export function tacSteps(r, dt) {
  if (!tacOn() || !r.alive || !synth.ac) return;
  const v = r.vel || [0, 0, 0], sp = Math.hypot(v[0], v[2]);
  const quiet = (r.f & FLAGS.WALK) || (r.f & FLAGS.CROUCH) || Math.abs(v[1]) > 2 || sp < TAC.run * TAC.walkMul + 0.6;
  if (quiet) { r._stepT = 0.15; return; }
  r._stepT = (r._stepT ?? 0.15) - dt * (sp / 7.5);
  if (r._stepT > 0) return;
  r._stepT = 0.34;
  const p = [r.pos[0], r.pos[1], r.pos[2]], k = Math.min(1, sp / TAC.run);
  r._side = !r._side;
  synth.noise(0.07, 0.42 * k, 'lowpass', r._side ? 520 : 460, 90, p);
  synth.tone('sine', r._side ? 95 : 85, 45, 0.08, 0.32 * k, p);
}
