// The Wrecking Ball and the Overdrive Rig last until they break (rules: /shared/bodyhp.js, the server owns the HP).
// Here: the pools as the server reports them ('bhp'), hitmarkers for whoever hit one, sparks and smoke on a pool that's
// dropping, the break itself ('bbreak': the ball splits in half / the rig bursts into scrap, a crack, the kill feed, a
// shout for whoever broke it) and the health bar over other people's balls and rigs.
import * as THREE from 'three';
import { FLAGS } from '/shared/weapons.js';
import { BODY } from '/shared/bodyhp.js';
import { G } from './ctx.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { sfx } from './audio.js';
import { fx } from './fx.js';
import { ME, endBall } from './player.js';
import { wreckBurst, wreckDied } from './wreck.js';
import { RS, rigDied, rigBroke } from './rig.js';

export const BH = new Map(); // player id -> { k, hp, max, t }
const MECHB = { paperplane: 5, nightshift: 6 }; // mechs' pools (shared/mech.js): their bar goes this high
const NAME = { wreckingball: 'WRECKING BALL', overdrive: 'OVERDRIVE RIG' };
const nameOf = (id) => (id === G.myId ? { name: G.myName || 'you', color: G.myColor || '#fff' } : G.names.get(id) || { name: '???', color: '#fff' });
// your own pool, for the HUD (null when you're in neither)
export const myBody = () => BH.get(G.myId) || null;

net.on('bhp', (m) => {
  if (!m || !Number.isFinite(m.hp) || !Number.isFinite(m.max) || !BODY[m.k]) return;
  const prev = BH.get(m.id);
  BH.set(m.id, { k: m.k, hp: m.hp, max: m.max, t: performance.now() });
  if (m.id === G.myId) { G.myBody = { k: m.k, hp: m.hp, max: m.max }; if (m.k === 'overdrive') RS.shield = m.hp; return; }
  if (Array.isArray(m.from) && m.from.includes(G.myId)) { hud.hit(false); sfx.hit(); } // you hit it
  const r = G.remotes.get(m.id);
  if (!r || !prev || m.hp >= prev.hp - 1) return;
  // it's taking hits: sparks off it, and smoke once it's under half
  const lost = prev.hp - m.hp, c = [r.pos[0], r.pos[1] + (m.k === 'wreckingball' ? 1.8 : 1.6), r.pos[2]];
  fx.spray(c, Math.min(14, 3 + Math.round(lost / 12)), [0xfff2b0, 0xffb040, 0xffffff], 6, 0.35, 0.08, 10, 1);
  if (m.hp < m.max * 0.5 && Math.random() < 0.5) fx.smoke(c, 2, 0.4);
});

net.on('bbreak', (m) => {
  if (!m || !BODY[m.k]) return;
  BH.delete(m.id);
  if (m.id === G.myId) G.myBody = null;
  const mine = m.id === G.myId, who = nameOf(m.id), by = m.by ? nameOf(m.by) : null, what = NAME[m.k];
  const p = Array.isArray(m.p) && m.p.length === 3 ? m.p : null;
  if (mine) {
    if (m.k === 'wreckingball') { wreckBurst([ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]], ME.vel); endBall(); }
    else rigBroke();
    G.shake = Math.max(G.shake, 0.8);
    hud.msg(m.why === 'out' ? `${what} WORE OUT` : `${what} BROKEN`, 1.6, 'slip');
  } else {
    const r = G.remotes.get(m.id);
    if (r) { if (m.k === 'wreckingball') wreckDied(r, r.vel); else rigDied(r, r.vel); }
    else if (p && m.k === 'wreckingball') wreckBurst([p[0], p[1] + 1.6, p[2]]);
  }
  if (p) { sfx.crack(mine ? null : p); sfx.clang(mine ? null : p, 1); }
  // the kill feed: who broke whose (a wear-out says so quietly), and a shout for whoever did it
  if (by) hud.feed([[by.name, by.color], ['  BROKE  ', '#ffe14d'], [`${who.name}'s ${what === 'WRECKING BALL' ? 'Wrecking Ball' : 'Overdrive Rig'}`, who.color]]);
  else hud.feed([[`${who.name}'s ${what === 'WRECKING BALL' ? 'Wrecking Ball' : 'Overdrive Rig'}`, who.color], ['  wore out', '#aaa']]);
  if (m.by === G.myId) { hud.msg(`BROKE ${who.name.toUpperCase()}'S ${what}`, 2, 'brag'); sfx.hit(); }
});
// a new round / mode / you left: forget them all
export function bodyReset() { BH.clear(); G.myBody = null; }

// ------------------------------------------------------------ the bar over someone's ball / rig
const W = 128, H = 20;
function bar(r) {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const tex = new THREE.CanvasTexture(c); tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.NearestFilter;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: true, fog: false }));
  s.renderOrder = 5;
  r.ch.root.add(s);
  return { s, c, tex, key: '', root: r.ch.root };
}
function draw(b, k, f) {
  const g = b.c.getContext('2d');
  g.clearRect(0, 0, W, H);
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(255,255,255,0.15)'; g.fillRect(3, 3, W - 6, H - 6);
  g.fillStyle = f > 0.5 ? (k === 'overdrive' ? '#4fd8ff' : '#cfd6de') : f > 0.25 ? '#ffe14d' : '#ff3030';
  g.fillRect(3, 3, Math.max(0, (W - 6) * f), H - 6);
  for (let x = 3 + (W - 6) / 4; x < W - 4; x += (W - 6) / 4) { g.fillStyle = 'rgba(0,0,0,0.55)'; g.fillRect(Math.round(x), 3, 2, H - 6); } // chunks
  b.tex.needsUpdate = true;
}
// remote.js, every frame: shows the bar while they're a ball or a rig and the server has told us its HP
export function bodyBar(r) {
  const e = BH.get(r.id), on = r.alive && e && ((e.k === 'wreckingball' && (r.f & FLAGS.BALL)) || (e.k === 'overdrive' && (r.f & FLAGS.RIG)) || (MECHB[e.k] && (r.f & FLAGS.MECH)));
  if (!on) { if (r.bodyBar) r.bodyBar.s.visible = false; return; }
  if (r.bodyBar && r.bodyBar.root !== r.ch.root) r.bodyBar = null; // their model was rebuilt (new look, team, armour)
  const b = r.bodyBar || (r.bodyBar = bar(r));
  const f = Math.max(0, Math.min(1, e.hp / e.max)), key = e.k + Math.round(f * 60);
  if (b.key !== key) { b.key = key; draw(b, e.k, f); }
  // above the ball (3.6 m) or the rig's head (3.1 m), the same size on screen far away (the root is scaled up)
  const k = r.distScale || 1;
  b.s.position.set(0, (MECHB[e.k] ? MECHB[e.k] + 0.4 : e.k === 'wreckingball' ? 3.9 : 3.3) / 1.2, 0); // (a mech's bar over its cockpit)
  b.s.scale.set(1.5 * k / 1.2, 0.24 * k / 1.2, 1);
  b.s.visible = true;
}
