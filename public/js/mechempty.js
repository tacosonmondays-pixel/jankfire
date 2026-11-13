// Empty mechs take hits (the rules: server/mech.js mechShot / mechHarm). Here: your bullets and swings stop on an enemy's
// empty mech (waiting after it lands, idle after a hop-out) and tell the server ('hit' with mk = the mech's id), the
// sparks and damage numbers when the server says one took a hit ('mech' k 'hurt'), and the armour bar over a damaged one
// (the same bar a ball, a rig or a piloted mech gets: bodyhp.js).
import { MECH, mechFrame, mechBoxes } from '/shared/mech.js';
import { rayBox } from '/shared/physics.js';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { rfx } from './rigmodel.js';
import { mechWorld } from './mech.js';
import { isFriend } from './weapons.js';
import { sceneBar, drawBar } from './bodyhp.js';

const r2 = (x) => Math.round(x * 100) / 100;
const empty = (m) => m.st === 'wait' || m.st === 'idle';
// one you may hurt: not yours, not your team's / squad's
function foe(m) {
  if (!empty(m) || m.o === G.myId) return false;
  const r = G.remotes.get(m.o);
  return !(r && isFriend(r));
}
// the nearest enemy empty mech along a ray before maxT: { t, id, head } or null
export function emptyMechRay(o, d, maxT) {
  let best = null;
  for (const m of mechWorld()) {
    if (!foe(m)) continue;
    for (const b of mechBoxes(m.p, m.f)) {
      const h = rayBox(o, d, b, best ? best.t : maxT);
      if (h && (!best || h.t < best.t)) best = { t: h.t, id: m.id, head: b.head };
    }
  }
  return best;
}
// a melee swing that found nobody: an enemy empty mech in front within reach takes it
export function emptyMechSwing(o, d, reach, w, hv) {
  const h = emptyMechRay(o, d, reach + 0.6);
  if (!h) return false;
  net.send({ t: 'hit', mk: h.id, w, d: d.map(r2), heavy: hv ? 1 : undefined });
  const p = [o[0] + d[0] * h.t, o[1] + d[1] * h.t, o[2] + d[2] * h.t];
  fx.sparks(p, d.map((x) => -x), 10, false);
  fx.blast(p, hv ? 1.1 : 0.6, 0xffffff, 0xffe14d);
  return true;
}

// ------------------------------------------------------------ the server's word: hits, and the bar
const BARS = new Map(); // mech id -> { b (the sprite), hp, max, key }
function setBar(id, hp, max) {
  if (!Number.isFinite(hp) || !Number.isFinite(max) || max <= 0) return;
  const e = BARS.get(id) || { b: sceneBar(), key: '' };
  e.hp = hp; e.max = max;
  BARS.set(id, e);
  tick();
}
function dropBar(id) { const e = BARS.get(id); if (!e) return; e.b.s.removeFromParent(); e.b.tex.dispose(); e.b.s.material.dispose(); BARS.delete(id); }
let raf = 0;
function tick() { // only runs while a bar is up
  raf = 0;
  if (!BARS.size) return;
  const live = new Map(mechWorld().map((m) => [m.id, m]));
  for (const [id, e] of BARS) {
    const m = live.get(id);
    if (!m || !empty(m)) { dropBar(id); continue; }
    if (e.b.s.parent !== G.scene && G.scene) G.scene.add(e.b.s); // (a new map rebuilt the scene)
    const f = Math.max(0, Math.min(1, e.hp / e.max)), key = Math.round(f * 60);
    if (e.key !== key) { e.key = key; drawBar(e.b, 'mech', f); }
    e.b.s.position.set(m.p[0], m.p[1] + MECH[mechFrame(m.f)].h + 0.7, m.p[2]);
    e.b.s.scale.set(2.2, 0.35, 1);
    e.b.s.visible = true;
  }
  if (BARS.size) raf = requestAnimationFrame(tick);
}
let shotT = 0;
const P = (x) => (Array.isArray(x) && x.length === 3 && x.every(Number.isFinite) ? x : null);
net.tap((m) => {
  if (!m || m.t !== 'mech') return;
  if (m.k === 'hurt') {
    const p = P(m.p);
    if (p) rfx.sparks(p, m.hs ? 18 : 10, m.hs ? 10 : 8, [0xffffff, 0xfff2b0, 0xffb040, 0x4fd8ff], 0.3, 0.1);
    setBar(m.m, m.hp, m.max);
    if (m.by === G.myId && p) { // you hit it: the marker, the ding, the number
      hud.hit(!!m.hs);
      if (m.hs) sfx.headshot(m.hp <= 0); else sfx.hit();
      const cam = G.camera;
      if (cam) {
        const v = cam.position.clone().set(p[0], p[1], p[2]).project(cam);
        if (v.z < 1) hud.dmgNum((v.x * 0.5 + 0.5) * innerWidth + (Math.random() - 0.5) * 30, (-v.y * 0.5 + 0.5) * innerHeight, m.a, !!m.hs);
      }
    }
    if (m.o === G.myId && m.hp > 0 && performance.now() - shotT > 3000) { shotT = performance.now(); hud.msg('YOUR MECH IS GETTING SHOT', 1.2, 'slip'); } // (it's standing there empty)
  } else if (m.k === 'list' && Array.isArray(m.m)) { // late joiners: the damaged ones get their bar
    for (const e of m.m) if (Array.isArray(e) && (e[7] === 'wait' || e[7] === 'idle') && Number.isFinite(e[9]) && e[9] < e[10]) { const b = BARS.get(e[0]); if (!b || b.hp !== e[9]) setBar(e[0], e[9], e[10]); }
  } else if ((m.k === 'down' && m.e) || m.k === 'gone') dropBar(m.m);
});
