// Card Deck: thrown cards you can actually follow. each card is a real 3D card (cardmesh.js) banked and spinning flat,
// with a soft glow and a glowing trail in its suit's colour. where it ends up comes from the server's 'pd' (the hit itself,
// damage, markers: all unchanged): into a player = a puff of suit symbols, into a wall or floor = it sticks in at an angle
// for a few seconds with a paper flick and a "thk", nothing near = it flutters down and lands. everything here is pooled
// (cardpool.js caps), and Potato gets no glow, a short hard trail, fewer stuck cards and plain particles for the puff
import * as THREE from 'three';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { ME } from './player.js';
import { BOXES } from '/shared/map.js';
import { WEAPONS } from '/shared/weapons.js';
import { stepProjectile, raycast } from '/shared/physics.js';
import { CARD_H, GLOW, CAPS, STICK_S, STICK_S_POTATO, TRAIL, Pool, suitFor } from './cardpool.js';
import { buildCard3D, dressCard, cardKit } from './cardmesh.js';

const potato = () => ((G.settings || {}).jank | 0) === 0;
const ends = { hit: 0, wall: 0, fall: 0, far: 0 }; // (tests: how cards ended)
const last = new Map(); // owner -> { suit, t }: their last played card (see suitFor)
const lastThrow = new Map(); // owner -> when we last played a throw sound (a fan is 6 cards in one tick: one riffle)
const _x = new THREE.Vector3(), _y = new THREE.Vector3(), _z = new THREE.Vector3(), _c = new THREE.Vector3(), _m = new THREE.Matrix4();
const UP = new THREE.Vector3(0, 1, 0);

// ------------------------------------------------------------ pools
const ROWS = 7, LANES = 3; // the trail: 7 rows of 3 verts (soft edge, bright middle, soft edge)
function makeTrail() {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(ROWS * LANES * 3), 3));
  const col = new Float32Array(ROWS * LANES * 3);
  for (let r = 0; r < ROWS; r++) for (let l = 0; l < LANES; l++) { const a = (1 - r / (ROWS - 1)) ** 1.6 * (l === 1 ? 1 : 0); col.set([a, a, a], (r * LANES + l) * 3); }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const idx = [];
  for (let r = 0; r < ROWS - 1; r++) for (let l = 0; l < LANES - 1; l++) { const a = r * LANES + l, b = a + LANES; idx.push(a, b, a + 1, a + 1, b, b + 1); }
  geo.setIndex(idx);
  const mesh = new THREE.Mesh(geo, cardKit().S.s.trail);
  mesh.frustumCulled = false; mesh.renderOrder = 2;
  return mesh;
}
const fly = new Pool(CAPS.fly, () => {
  const root = buildCard3D('s');
  const glow = new THREE.Sprite(cardKit().S.s.glow); glow.scale.setScalar(0.95); root.add(glow);
  const trail = makeTrail(); trail.visible = false;
  return { root, glow, trail, pr: null };
}, (s) => { if (s.pr) { s.pr.card = null; s.pr.mesh = GONE; } s.pr = null; }); // too many in the air: the oldest stops being drawn
const GONE = new THREE.Group(); // (what a stolen card's projectile holds instead: never in the scene)
const stuck = new Pool(CAPS.stuck, () => ({ root: buildCard3D('s'), t: 0, life: 0, p: [0, 0, 0], q: new THREE.Quaternion(), fall: null }), (s) => G.scene.remove(s.root));
const puffs = new Pool(CAPS.puff, () => ({ spr: new THREE.Sprite(cardKit().S.s.sym), t: 0, v: [0, 0, 0], s: 0.3 }), (s) => G.scene.remove(s.spr));

// ------------------------------------------------------------ in flight
// 'fx' k:'card': remember the suit they just played (its cards land in the next 'ps' messages)
export function cardPlayed(m) {
  if (m && Number.isInteger(m.id) && typeof m.suit === 'string') last.set(m.id, { suit: m.joker ? 'j' : GLOW[m.suit] ? m.suit : 's', t: performance.now() });
}

// a 'ps' for a card: a pooled 3D card in its suit, banked a little (left and right in turn, so a fan reads as a fan)
export function cardMesh(m) {
  const now = performance.now(), suit = suitFor(last, m.o, now), s = fly.take();
  dressCard(s.root, suit);
  const K = cardKit().S[suit];
  s.glow.material = K.glow; s.trail.material = K.trail;
  s.suit = suit; s.bank = ((m.id & 1) ? 1 : -1) * (0.45 + Math.random() * 0.3); s.spin = Math.random() * 6.28; s.born = now;
  s.from = m.p.slice(); s.whoosh = m.o === G.myId; s.held = null; s.pr = null;
  s.root.visible = true;
  s.root.userData.slot = s;
  if (!s.trail.parent) G.scene.add(s.trail);
  if (now - (lastThrow.get(m.o) || 0) > 90) { lastThrow.set(m.o, now); sfx.cardThrow(m.o === G.myId ? null : m.p); } // one riffle per throw
  return s.root;
}
export function cardBind(pr) { const s = pr.mesh.userData.slot; if (s) { s.pr = pr; pr.card = s; } } // (spawnProj, once pr exists)

// every frame for a card in flight (main.js): move it (it stops dead at a wall it reaches before the server says so),
// aim it along its flight, spin it, glow, trail, and a whoosh if it goes right past your head
export function cardStep(pr, dt, now) {
  const s = pr.mesh.userData.slot;
  if (!s || s.pr !== pr) return;
  if (!s.held) {
    const v = pr.v, sp = Math.hypot(v[0], v[1], v[2]);
    if (sp > 1e-3) s.dir = [v[0] / sp, v[1] / sp, v[2] / sp];
    const h = stepProjectile(pr, dt, BOXES, WEAPONS.card.grav);
    if (h) s.held = h; // (the 'pd' sticks it properly in a moment)
  }
  const d = s.dir || [0, 0, 1], p = pr.p;
  pr.mesh.position.set(p[0], p[1], p[2]);
  aim(pr.mesh, d, s.bank);
  s.spin += dt * (s.held ? 0 : 32);
  s.root.userData.card.spin.rotation.y = s.spin;
  const pot = potato(), cam = G.camera.position;
  s.glow.visible = !pot;
  if (!pot) s.glow.material.opacity = 0.7 + Math.sin(now * 0.03 + pr.id) * 0.15;
  // the trail: back along the flight, as long as it has flown (so it grows out of the hand), wider when it's near you
  const traveled = Math.hypot(p[0] - s.from[0], p[1] - s.from[1], p[2] - s.from[2]);
  const camD = Math.hypot(cam.x - p[0], cam.y - p[1], cam.z - p[2]);
  const near = pot ? 1 : 1 + Math.max(0, 1 - camD / 7) * 1.6; // the close-range streak
  const len = Math.min(pot ? TRAIL.lenPotato : TRAIL.len * (near > 1.4 ? 1.3 : 1), traveled), w = (pot ? TRAIL.wPotato : TRAIL.w) * near;
  s.trail.visible = len > 0.2 && !s.held && pr.mesh.visible;
  if (s.trail.visible) trail(s.trail, p, d, len, w, cam, pot);
  // a whoosh when one goes past your head (not your own: those got the throw sound)
  if (!s.whoosh && camD < 3.2 && now - s.born > 60) { s.whoosh = true; sfx.cardWhoosh(p); }
}

function aim(obj, d, bank) {
  _z.set(d[0], d[1], d[2]);
  _x.crossVectors(UP, _z); if (_x.lengthSq() < 1e-6) _x.set(1, 0, 0); _x.normalize();
  _y.crossVectors(_z, _x);
  const c = Math.cos(bank), s = Math.sin(bank);
  _c.copy(_x).multiplyScalar(c).addScaledVector(_y, s); _y.multiplyScalar(c).addScaledVector(_x, -s); _x.copy(_c); // bank round the flight
  _m.makeBasis(_x, _y, _z); obj.quaternion.setFromRotationMatrix(_m);
}

function trail(mesh, p, d, len, w, cam, pot) {
  const a = mesh.geometry.attributes.position, arr = a.array;
  // flat to the camera: across = flight x (to camera)
  let sx = d[1] * (cam.z - p[2]) - d[2] * (cam.y - p[1]), sy = d[2] * (cam.x - p[0]) - d[0] * (cam.z - p[2]), sz = d[0] * (cam.y - p[1]) - d[1] * (cam.x - p[0]);
  const l = Math.hypot(sx, sy, sz) || 1; sx /= l; sy /= l; sz /= l;
  for (let r = 0; r < ROWS; r++) {
    const k = r / (ROWS - 1), cx = p[0] - d[0] * len * k, cy = p[1] - d[1] * len * k, cz = p[2] - d[2] * len * k;
    const hw = w * (pot ? 1 : 1 - k * 0.85);
    for (let ln = 0; ln < LANES; ln++) {
      const o = (ln - 1) * hw, i = (r * LANES + ln) * 3;
      arr[i] = cx + sx * o; arr[i + 1] = cy + sy * o; arr[i + 2] = cz + sz * o;
    }
  }
  a.needsUpdate = true;
}

function freeFly(s) {
  s.trail.visible = false; s.root.visible = false; s.root.userData.slot = null;
  if (s.pr) s.pr.card = null;
  s.pr = null;
  fly.give(s);
}

// ------------------------------------------------------------ where it ended up
// the server's 'pd' for a card (main.js has already taken it out of the scene): a player, a wall, or nowhere
export function cardEnd(pr, m) {
  const s = pr.mesh.userData.slot;
  const suit = s ? s.suit : 's', d = (s && s.dir) || norm(pr.v) || [0, 0, 1];
  if (s) freeFly(s);
  const p = Array.isArray(m.p) && m.p.length === 3 && m.p.every(Number.isFinite) ? m.p : pr.p;
  if (Math.hypot(p[0] - ME.pos[0], p[1] - ME.pos[1], p[2] - ME.pos[2]) > 160) { ends.far++; return; } // too far away to see
  if (hitPlayer(p, pr.o)) { ends.hit++; burst(p, d, suit); return; }
  const h = surface(p, d);
  if (h) {
    const { at, n } = h;
    ends.wall++;
    stick(at, d, n, suit, false);
    flick(at, n, suit);
    sfx.cardThk(at);
    return;
  }
  ends.fall++;
  fallFrom(p, d, suit); // flew off: it flutters down and lands where you can see it
}

// the surface it ended on: along its flight first, else straight out each way (the server stops a card one hit radius
// short of the box face it touched, so a flat shot at the floor ends 0.26 m above it, off to the side of its flight line)
const AX = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
function surface(p, d) {
  const o = [p[0] - d[0] * 1.5, p[1] - d[1] * 1.5, p[2] - d[2] * 1.5], h = raycast(o, d, 3, BOXES);
  if (h) { const n = [0, 0, 0]; n[h.axis] = h.sign; return { at: [o[0] + d[0] * h.t, o[1] + d[1] * h.t, o[2] + d[2] * h.t], n }; }
  let best = null;
  for (const a of AX) {
    const q = raycast(p, a, WEAPONS.card.r + 0.15, BOXES);
    if (q && (!best || q.t < best.t)) best = { t: q.t, a, axis: q.axis, sign: q.sign };
  }
  if (!best) return null;
  const n = [0, 0, 0]; n[best.axis] = best.sign;
  return { at: [p[0] + best.a[0] * best.t, p[1] + best.a[1] * best.t, p[2] + best.a[2] * best.t], n };
}

const norm = (v) => { const l = Math.hypot(v[0], v[1], v[2]); return l > 1e-6 ? [v[0] / l, v[1] / l, v[2] / l] : null; };

// is the card's end point on someone's body (not the thrower's)? the server's hit point sits on the body it swept into
function hitPlayer(p, owner) {
  const on = (pos) => p[0] > pos[0] - 0.9 && p[0] < pos[0] + 0.9 && p[2] > pos[2] - 0.9 && p[2] < pos[2] + 0.9 && p[1] > pos[1] - 0.4 && p[1] < pos[1] + 2.1;
  if (owner !== G.myId && ME.alive && on(ME.pos)) return true;
  for (const r of G.remotes.values()) if (r.id !== owner && r.alive && on(r.pos)) return true;
  return false;
}

// a card stuck in a surface: its leading edge buried a little, the rest sticking out back along the way it came,
// knocked off true a bit. lie: a fallen card lying flat on the floor instead
function stick(at, d, n, suit, lie) {
  const pot = potato(), s = stuck.take();
  if (pot) stuck.trim(CAPS.stuckPotato, (o) => G.scene.remove(o.root));
  dressCard(s.root, suit);
  const c = s.root.userData.card;
  if (lie) {
    s.root.position.set(at[0], at[1] + 0.012, at[2]);
    s.root.quaternion.setFromAxisAngle(UP, Math.random() * 6.28);
    c.spin.position.set(0, 0, 0); c.spin.rotation.set(0, 0, Math.random() < 0.15 ? Math.PI : 0); // sometimes face down
  } else {
    // into the surface at the angle it came in, nudged so it never lies flush (it should look stabbed in)
    let dz = [d[0] + (Math.random() - 0.5) * 0.35, d[1] + (Math.random() - 0.5) * 0.35, d[2] + (Math.random() - 0.5) * 0.35];
    const into = dz[0] * n[0] + dz[1] * n[1] + dz[2] * n[2];
    if (into > -0.35) dz = [dz[0] - n[0] * (0.35 + into), dz[1] - n[1] * (0.35 + into), dz[2] - n[2] * (0.35 + into)];
    dz = norm(dz) || [-n[0], -n[1], -n[2]];
    const depth = 0.07;
    s.root.position.set(at[0] + dz[0] * depth, at[1] + dz[1] * depth, at[2] + dz[2] * depth); // the pivot: in the wall
    aim(s.root, dz, (Math.random() - 0.5) * 2.4);
    c.spin.position.set(0, 0, -CARD_H / 2); c.spin.rotation.set(0, 0, 0); // the card sticks back out of the wall
  }
  s.t = 0; s.life = pot ? STICK_S_POTATO : STICK_S; s.lie = lie; s.suit = suit; s.q.copy(s.root.quaternion); s.fall = null;
  s.root.scale.setScalar(1); s.root.visible = true;
  G.scene.add(s.root);
}

// the paper flick off a stuck card: white scraps and a few in the suit's colour, off the surface
function flick(p, n, suit) {
  const pot = potato();
  fx.spray([p[0] + n[0] * 0.05, p[1] + n[1] * 0.05, p[2] + n[2] * 0.05], pot ? 4 : 9, [0xffffff, 0xfffaf0, GLOW[suit]], 3.2, 0.45, pot ? 0.1 : 0.07, 9, 2);
}

// a hit on someone: a puff of suit symbols bursting off them (Potato: just the coloured scraps), plus paper shreds
function burst(p, d, suit) {
  const pot = potato();
  fx.spray(p, pot ? 8 : 14, [0xffffff, GLOW[suit], 0x111111], 6, 0.55, pot ? 0.12 : 0.09, 8, 2);
  sfx.cardBurst(p);
  if (pot) return;
  const mat = cardKit().S[suit].sym, n = 7;
  for (let i = 0; i < n; i++) {
    const s = puffs.take(), a = (i / n) * 6.28 + Math.random() * 0.5;
    s.spr.material = mat;
    s.spr.position.set(p[0], p[1], p[2]);
    s.v = [Math.cos(a) * 3.2 - d[0] * 1.2, 2.2 + Math.random() * 2.4, Math.sin(a) * 3.2 - d[2] * 1.2];
    s.t = 0; s.s = 0.26 + Math.random() * 0.14; s.spr.scale.setScalar(0.01);
    G.scene.add(s.spr);
  }
}

// flew off into nothing: a flutter down from where it stopped
function fallFrom(p, d, suit) {
  const s = stuck.take();
  if (potato()) stuck.trim(CAPS.stuckPotato, (o) => G.scene.remove(o.root));
  dressCard(s.root, suit);
  const c = s.root.userData.card;
  c.spin.position.set(0, 0, 0);
  s.root.position.set(p[0], p[1], p[2]); s.root.scale.setScalar(1); s.root.visible = true;
  s.fall = { p: p.slice(), v: [d[0] * 4, 1.2, d[2] * 4], r: 0.05, t: 0, w: Math.random() * 6.28 };
  s.t = 0; s.life = 99; s.lie = false; s.suit = suit;
  G.scene.add(s.root);
}

// ------------------------------------------------------------ every frame
export function cardFrame(dt, now) {
  for (let i = stuck.live.length - 1; i >= 0; i--) {
    const s = stuck.live[i];
    s.t += dt;
    if (s.fall) { // fluttering down: drifts, rocks side to side, slow
      const f = s.fall;
      f.t += dt; f.v[0] *= 1 - dt * 1.5; f.v[2] *= 1 - dt * 1.5;
      f.v[1] = Math.max(f.v[1] - 7 * dt, -3.2);
      const h = stepProjectile(f, dt, BOXES, 0);
      s.root.position.set(f.p[0], f.p[1], f.p[2]);
      s.root.rotation.set(Math.sin(f.t * 7 + f.w) * 0.7, f.w + f.t * 2.5, Math.cos(f.t * 5) * 0.4);
      if (h && h.axis === 1 && h.sign === 1) { // landed on top of something
        const at = [f.p[0], f.p[1] - f.r, f.p[2]];
        G.scene.remove(s.root); stuck.give(s);
        stick(at, [0, -1, 0], [0, 1, 0], s.suit, true);
        sfx.cardFlop(at);
        continue;
      }
      if (f.t > 4 || f.p[1] < -60) { G.scene.remove(s.root); stuck.give(s); }
      continue;
    }
    // stuck: a quick twang when it lands, then it sits, then pops away
    if (!s.lie && s.t < 0.5) { s.root.quaternion.copy(s.q); s.root.rotateX(Math.sin(s.t * 55) * 0.3 * Math.exp(-s.t * 9)); }
    const out = s.life - s.t;
    if (out < 0.25) s.root.scale.setScalar(Math.max(0.001, out / 0.25));
    if (out <= 0) { G.scene.remove(s.root); stuck.give(s); }
  }
  for (let i = puffs.live.length - 1; i >= 0; i--) {
    const s = puffs.live[i];
    s.t += dt;
    s.v[1] -= 6 * dt; s.v[0] *= 1 - dt * 2.5; s.v[2] *= 1 - dt * 2.5;
    s.spr.position.x += s.v[0] * dt; s.spr.position.y += s.v[1] * dt; s.spr.position.z += s.v[2] * dt;
    const k = s.t < 0.12 ? s.t / 0.12 * 1.25 : s.t < 0.2 ? 1.25 - (s.t - 0.12) / 0.08 * 0.25 : Math.max(0, 1 - (s.t - 0.4) / 0.3); // pop big, settle, shrink away
    s.spr.scale.setScalar(Math.max(0.001, s.s * k));
    if (s.t > 0.7) { G.scene.remove(s.spr); puffs.give(s); }
  }
}

// leaving a match: everything back in its pool
export function clearCards() {
  fly.clear((s) => { s.trail.visible = false; s.root.visible = false; s.root.userData.slot = null; s.pr = null; });
  stuck.clear((s) => G.scene.remove(s.root));
  puffs.clear((s) => G.scene.remove(s.spr));
  last.clear(); lastThrow.clear();
}
export const cardStats = () => ({ fly: fly.live.length, flyMade: fly.made, stuck: stuck.live.length, stuckMade: stuck.made, puff: puffs.live.length, puffMade: puffs.made, ...ends }); // (tests)
