// Scales of Justice, client side: the verdict on whoever you aim at (readout + the scale tipping in your hands),
// pans swinging on their chains, and the gold stamp, gavel and coins when a hit lands.
// The client only guesses from the scoreboard it can see; the server's verdict is the one that decides damage.
import * as THREE from 'three';
import { WEAPONS } from '/shared/weapons.js';
import { verdict, verdictName, fmtMult } from '/shared/verdict.js';
import { GAMES } from '/shared/modes.js';
import { BOXES } from '/shared/map.js';
import { raycast, rayBox } from '/shared/physics.js';
import { G } from './ctx.js';
import { ME, eye, look } from './player.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { hud } from './hud.js';

// ------------------------------------------------------------ what the court knows
// snapshots carry everyone's kills + deaths; kill streaks and who killed you last come from the kill feed (main.js)
const streaks = new Map();
let lastKiller = 0, roomOf = 0;
function fresh() { if (roomOf !== G.myId) { roomOf = G.myId; streaks.clear(); lastKiller = 0; } } // new room, new court
export function courtKill(m) {
  fresh();
  if (m.k && m.k !== m.v) streaks.set(m.k, (streaks.get(m.k) || 0) + 1);
  streaks.delete(m.v); // only players on a streak are kept (coop sends a lot of wave bots through here)
  if (m.v === G.myId && m.k && m.k !== G.myId) lastKiller = m.k;
  else if (m.k === G.myId && m.v === lastKiller) lastKiller = 0; // revenge served
}
// a new match (main.js, round start): the server forgets grudges too. dropping the streaks is safe because the court
// only counts this match's kills of a streak (shared/verdict.js), which is all this map holds from here
export function courtReset() { lastKiller = 0; streaks.clear(); }
// on join the server sends the streaks so far (the kill feed only has them from here on): [[id, streak], ...]
export function courtSync(m) { fresh(); for (const [id, n] of m.s || []) if (n > 0) streaks.set(id, n); }
const friend = (r) => !!(G.myTeam && r.team && r.team === G.myTeam);
const dummy = (r) => r.bot && r.name === 'Dummy';

// the same formula the server runs, on the scoreboard this client can see
export function judge(r) {
  fresh();
  const me = { kills: G.kills, deaths: G.deaths }, board = [me];
  for (const o of G.remotes.values()) if (!dummy(o)) board.push({ kills: o.k, deaths: o.d });
  const R = G.round;
  let teams = null;
  if (R && GAMES[R.game] && GAMES[R.game].teams && G.myTeam && r.team) {
    const sc = R.game === 'bomb' && R.bomb ? R.bomb.wins : R.sc || [0, 0];
    teams = [sc[G.myTeam - 1] || 0, sc[r.team - 1] || 0];
  }
  return verdict(me, { kills: r.k, deaths: r.d, streak: streaks.get(r.id) || 0 }, { board, teams, revenge: !!lastKiller && lastKiller === r.id, npc: (G.mode === 'coop' && r.bot) || dummy(r) });
}

// who's on trial: whoever is under the crosshair, else the one a swing would hit closest to it.
// reach = the same cone test a swing uses (weapons.js conePlayers)
function accused(reach, cone) {
  const o = eye(), d = look(), cosC = Math.cos(cone), inReach = new Set();
  let ray = null, near = null, best = -2;
  for (const r of G.remotes.values()) {
    if (!r.alive || friend(r)) continue;
    for (const hb of r.hitboxes()) { const h = rayBox(o, d, hb, ray ? ray.t : 60); if (h && (!ray || h.t < ray.t)) ray = { t: h.t, r }; }
    const tx = r.pos[0] - o[0], ty = r.pos[1] + 1 - o[1], tz = r.pos[2] - o[2], dist = Math.hypot(tx, ty, tz);
    if (dist > reach || dist < 1e-3) continue;
    const dot = (tx * d[0] + ty * d[1] + tz * d[2]) / dist;
    if ((dist > 1.5 && dot < cosC) || raycast(o, [tx / dist, ty / dist, tz / dist], dist, BOXES)) continue;
    inReach.add(r);
    if (dot > best) { best = dot; near = r; }
  }
  if (ray && raycast(o, d, ray.t, BOXES)) ray = null; // behind a wall
  const r = ray && inReach.has(ray.r) ? ray.r : near || (ray && ray.r); // a swing hits whoever is in reach, so they come first
  return r ? { r, reach: inReach.has(r) } : null;
}

// ------------------------------------------------------------ the scale itself
const court = { seen: 0, ruling: null, pv: null, yaw: 0, push: new THREE.Vector3() };
const VM_G = new THREE.Vector3(0, -7, 0), WORLD_G = new THREE.Vector3(0, -9.8, 0);
const V1 = new THREE.Vector3(), V2 = new THREE.Vector3(), V3 = new THREE.Vector3(), Q = new THREE.Quaternion(), DOWN = new THREE.Vector3(0, -1, 0);
const tilt = (g) => Math.sign(g) * Math.min(0.42, 0.12 * Math.abs(g)); // guilty tips the heart pan down, innocent the feather

// one step of a scale: the beam springs toward the verdict's tilt; each pan is a weight on a chain (a point that swings
// and can go slack), so walking, bobbing and swinging the scale all throw the pans around for free.
// grav / push: accelerations in the scale's own scene, units per second²
export function stepScale(g, dt, guilt, grav, push, now) {
  const c = g.userData.court;
  if (!c || dt <= 0) return;
  if (now - (c.t || 0) > 250) for (const pan of c.pans) pan.userData.sim = null; // not drawn for a while: hang straight again
  c.t = now;
  dt = Math.min(dt, 0.05);
  const k = c.wobble ? 70 : 110, damp = c.wobble ? 4 : 11; // the toy is springy and never quite settles
  c.tv = c.tv || 0;
  c.tv += ((tilt(guilt) - c.beam.rotation.z) * k - c.tv * damp) * dt;
  c.beam.rotation.z += c.tv * dt;
  if (c.wobble) { c.body.rotation.z = Math.sin(now * 0.011) * 0.025 - c.tv * 0.05; c.body.rotation.x = Math.sin(now * 0.0083 + 1) * 0.02; }
  g.updateWorldMatrix(true, true);
  const L = c.len * c.beam.getWorldScale(V3).y;
  c.beam.getWorldQuaternion(Q).invert();
  for (const pan of c.pans) {
    const a = c.beam.localToWorld(V1.copy(pan.userData.pivot));
    let s = pan.userData.sim;
    if (!s) s = pan.userData.sim = { p: a.clone().addScaledVector(DOWN, L), v: new THREE.Vector3() };
    s.v.addScaledVector(grav, dt);
    if (push) s.v.addScaledVector(push, dt);
    s.v.multiplyScalar(Math.exp(-1.4 * dt)).clampLength(0, L * 30); // chain friction, and no orbiting the beam
    V2.copy(s.p).addScaledVector(s.v, dt).sub(a);
    if (V2.length() > L) V2.setLength(L); // the chain is taut: the pan can't get further than its length
    V2.add(a);
    s.v.subVectors(V2, s.p).divideScalar(dt);
    s.p.copy(V2);
    pan.quaternion.setFromUnitVectors(DOWN, V2.sub(a).applyQuaternion(Q).normalize()); // hang toward the weight
  }
}

// weapons.js calls this every frame while the scales are out
export function tickScalesVM(g, dt, now) {
  if (now - court.seen > 250) court.pv = null; // just pulled out again: no stale motion
  court.seen = now;
  const w = WEAPONS.scales;
  const a = ME.alive && !document.body.classList.contains('replaying') ? accused(w.range, w.cone) : null;
  const v = a ? judge(a.r) : null;
  if (a && a.reach) {
    const why = v.why.map(([t, s]) => (s > 0 ? '+' : '-') + t).join('  ');
    hud.verdict(`${verdictName(v.g)} ${fmtMult(v.mult)}`, why, v.g > 0 ? 'guilty' : v.g < 0 ? 'innocent' : '');
  } else hud.verdict(null);
  // the server just ruled on your hit: the scale slams to its verdict for a moment
  const ruled = court.ruling && now < court.ruling.until ? court.ruling.g : null;
  // you carry it around: speeding up, turning and landing throw the pans the other way
  const cy = Math.cos(ME.yaw), sy = Math.sin(ME.yaw);
  const vel = [ME.vel[0] * cy - ME.vel[2] * sy, ME.vel[1], -ME.vel[0] * sy - ME.vel[2] * cy]; // right, up, forward
  let dyaw = ME.yaw - court.yaw; while (dyaw > Math.PI) dyaw -= Math.PI * 2; while (dyaw < -Math.PI) dyaw += Math.PI * 2;
  court.yaw = ME.yaw;
  const push = court.push.set(0, 0, 0);
  if (court.pv && dt > 0) {
    const cl = (x) => Math.max(-25, Math.min(25, x));
    push.set(cl(-(vel[0] - court.pv[0]) / dt * 0.04 + (dyaw / dt) * 0.5), cl(-(vel[1] - court.pv[1]) / dt * 0.04), cl((vel[2] - court.pv[2]) / dt * 0.04));
  }
  court.pv = vel;
  stepScale(g, dt, ruled ?? (v ? v.g : 0), VM_G, push, now);
}

// ------------------------------------------------------------ the ruling: stamp, gavel, gold
const live = []; // { obj, age, life, step }
const R = (s = 1) => (Math.random() * 2 - 1) * s;
function add(obj, life, step) { G.scene.add(obj); live.push({ obj, age: 0, life, step }); }

const stampTexs = new Map();
function stampTex(title, sub, ink) {
  const key = title + sub;
  if (stampTexs.has(key)) return stampTexs.get(key);
  const c = document.createElement('canvas'); c.width = 512; c.height = 256;
  const x = c.getContext('2d');
  x.translate(256, 128);
  x.strokeStyle = '#ffc83a'; x.fillStyle = '#ffc83a';
  x.lineWidth = 12; x.beginPath(); x.roundRect(-238, -100, 476, 200, 24); x.stroke();
  x.lineWidth = 4; x.beginPath(); x.roundRect(-220, -84, 440, 168, 14); x.stroke();
  x.textAlign = 'center'; x.textBaseline = 'middle'; x.lineJoin = 'round';
  const words = (text, size, y) => {
    x.font = `bold ${size}px "Comic Neue", "Comic Sans MS", sans-serif`;
    x.strokeStyle = ink; x.lineWidth = size * 0.16; x.strokeText(text, 0, y);
    x.fillText(text, 0, y);
  };
  words(title, title.length > 8 ? 74 : 96, sub ? -22 : 0);
  if (sub) words(sub, sub.length > 8 ? 34 : 58, 56);
  // rubber stamp: knock specks out of the ink
  x.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < 320; i++) x.fillRect(-256 + Math.random() * 512, -128 + Math.random() * 256, 1 + Math.random() * 4, 1 + Math.random() * 3);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  stampTexs.set(key, t);
  return t;
}
// the stamp slams down over the victim, settles, then fades. it follows them until they die, then stays put.
// mine (your own hit): big and through everything. anyone else's is a normal thing in the world: walls hide it, distance shrinks it
function stamp(p, title, sub, ink, who, big, mine) {
  const mat = new THREE.SpriteMaterial({ map: stampTex(title, sub, ink), transparent: true, depthTest: !mine, depthWrite: false, fog: false });
  mat.rotation = -0.1 + R(0.1);
  const s = new THREE.Sprite(mat);
  s.renderOrder = 30;
  s.position.set(p[0], p[1] + 1.35, p[2]);
  add(s, big ? 2.4 : 1.75, (o, dt, age) => {
    if (who && (!who.alive || !who.ch.root.visible)) who = null; // dead (or gone): the stamp stays where they fell
    if (who) o.position.set(who.pos[0], who.pos[1] + 2.25, who.pos[2]);
    const slam = Math.min(1, age / 0.1);
    const k = slam < 1 ? 1 + (1 - slam * slam) * 1.8 : 1 + Math.max(0, 0.1 - (age - 0.1)) * 0.6 * Math.sin((age - 0.1) * 60);
    const w = (mine ? Math.max(2.2, o.position.distanceTo(G.camera.position) * 0.7) : 2.2) * (big ? 1.35 : 1); // yours: never smaller than a fifth of the screen
    o.scale.set(w * k, w * 0.5 * k, 1);
    const fade = big ? 1.95 : 1.3;
    mat.opacity = slam < 1 ? slam : age > fade ? Math.max(0, 1 - (age - fade) / 0.45) : 1;
  });
}
const COIN_GEO = new THREE.CylinderGeometry(0.075, 0.075, 0.018, 10);
let coinMat = null;
function coins(p, n) {
  coinMat ||= new THREE.MeshLambertMaterial({ color: 0xffc21a, emissive: 0x5a3a00 });
  const fl = raycast([p[0], p[1] + 0.5, p[2]], [0, -1, 0], 30, BOXES), fy = fl ? fl.point[1] + 0.01 : -1e9;
  for (let i = 0; i < n; i++) {
    const m = new THREE.Mesh(COIN_GEO, coinMat);
    m.position.set(p[0] + R(0.2), p[1] + 0.5, p[2] + R(0.2));
    const v = [R(3.5), 4 + Math.random() * 4, R(3.5)], av = [R(16), R(6), R(16)], life = 2 + Math.random();
    add(m, life, (o, dt, age) => {
      v[1] -= 18 * dt;
      o.position.x += v[0] * dt; o.position.y += v[1] * dt; o.position.z += v[2] * dt;
      if (o.position.y < fy) { o.position.y = fy; v[1] = Math.abs(v[1]) * 0.4; v[0] *= 0.6; v[2] *= 0.6; av[0] *= 0.4; av[2] *= 0.4; } // clink, bounce, settle
      o.rotation.x += av[0] * dt; o.rotation.y += av[1] * dt; o.rotation.z += av[2] * dt;
      if (life - age < 0.4) o.scale.setScalar(Math.max(0.01, (life - age) / 0.4));
    });
  }
}

const titleOf = (g) => (g > 0 ? 'GUILTY!' : g < 0 ? 'NOT GUILTY' : 'HUNG JURY');
// stamp, gold and gavel where the ruling landed. mine: the hit is yours (or, in a replay, the one the camera follows).
// someone else's trial far away gets no stamp, coins or sparks (they'd flood the screen and give away where the fight is)
function ruling(m, p, victim, mine, stampIt) {
  if (mine || G.camera.position.distanceTo(V1.set(p[0], p[1], p[2])) < 35) {
    const ink = m.g > 0 ? '#6a0a00' : m.g < 0 ? '#0a2a5a' : '#3a2a10';
    if (stampIt) stamp(p, titleOf(m.g), m.one ? 'THE COURT HAS SPOKEN' : fmtMult(m.m), ink, victim, m.one, mine);
    fx.spray([p[0], p[1] + 0.7, p[2]], Math.round(18 + 14 * m.m), [0xffd23b, 0xfff2a0, 0xffb31a, 0xffffff], 9, 0.9, 0.12, 9, 1.4);
    coins(p, Math.round(2 + 4 * m.m));
  }
  sfx.gavel(p, m.one ? 3 : 1);
  if (m.g > 0) sfx.guilty(p, m.one); else if (m.g < 0) sfx.acquit(p);
}

// the server ruled on a scales hit: { id: victim, by: attacker, m: multiplier, g: guilt, one: one-shot, p: where }
export function courtVerdict(m) {
  const now = performance.now();
  const victim = m.id === G.myId ? null : G.remotes.get(m.id);
  const p = m.p || (victim ? [victim.pos[0], victim.pos[1] + 0.9, victim.pos[2]] : ME.pos);
  const title = titleOf(m.g);
  const mine = m.by === G.myId;
  ruling(m, p, victim, mine, m.id !== G.myId);
  if (mine) {
    court.ruling = { g: m.g, until: now + 900 };
    if (m.one) { hud.msg('THE COURT HAS SPOKEN', 1.8, 'court'); G.shake = Math.max(G.shake, 0.6); }
  } else { const h = G.remotes.get(m.by); if (h) h.ruling = { g: m.g, until: now + 1200 }; }
  if (m.id === G.myId) hud.msg(m.one ? 'THE COURT HAS SPOKEN' : `${title} ${fmtMult(m.m)}`, 1.3, 'court');
}
// the same ruling in a killcam or highlight (replay.js): victim is their ghost, focus whoever the camera follows
export function courtReplay(m, victim, focus) {
  const p = m.p || (victim && [victim.pos[0], victim.pos[1] + 0.9, victim.pos[2]]);
  if (p) ruling(m, p, victim, m.by === focus, true);
}

// every frame (main.js): other people's scales, stamps, coins
export function updateCourt(dt, now) {
  if (now - court.seen > 150) hud.verdict(null); // scales put away
  // everyone else's scale: the pans swing as they run about, the beam tips when one of their hits gets a verdict
  for (const r of G.remotes.values()) {
    const g = r.weaponMesh;
    if (!g || !g.userData.court || !r.ch.root.visible) continue;
    stepScale(g, dt, r.ruling && now < r.ruling.until ? r.ruling.g : 0, WORLD_G, null, now);
  }
  for (let i = live.length - 1; i >= 0; i--) {
    const e = live[i];
    e.age += dt;
    if (e.age >= e.life) { G.scene.remove(e.obj); if (e.obj.isSprite) e.obj.material.dispose(); live.splice(i, 1); continue; }
    e.step(e.obj, dt, e.age);
  }
}
