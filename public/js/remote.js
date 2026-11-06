// Other players (and bots): snapshot interpolation, janky mannequin animation, skins, ropes, effects.
import * as THREE from 'three';
import { BOXES } from '/shared/map.js';
import { raycast, playerBoxes } from '/shared/physics.js';
import { FLAGS } from '/shared/weapons.js';
import { INFECT } from '/shared/modes.js';
import { G } from './ctx.js';
import { buildCharacter, buildWeapon, makeNameTag, makeShadow, cardTex, setKatana, freeTree, teamLook } from './models.js';
import { fx, makeBeam, setBeam } from './fx.js';
import { emitSkinFx } from './skins.js';
import { wreckRemote, ballBoxes, wreckDispose } from './wreck.js';
import { jankify } from './jank.js';
import { rigRemote, rigBoxes, rigDispose } from './rig.js'; // overdrive rig killstreak
import { gearLook, dressGear } from './econ3d.js';
import { tacLook, tacSteps } from './tactical.js';
import { newTwirl, twirlShot, stepTwirl, applyTwirl } from './twirl.js';
import { makeRope, setRope, setRopeSkin } from './grapple.js';
import { sfx } from './audio.js';
import { remoteShredder } from './shredder.js';

// players ignore fog, glow a bit, and get an outline in their colour so you can spot them across the map
const noFog = new Map();
function visibleMat(m) {
  if (!m || m.isShaderMaterial || m.isSpriteMaterial) return m;
  if (Array.isArray(m)) return m.map(visibleMat); // the knife blade has a material per face
  if (!noFog.has(m)) {
    const c = m.clone();
    c.fog = false;
    if (c.emissive && c.color) c.emissive.copy(c.color).multiplyScalar(0.28);
    c.onBeforeCompile = () => {}; // no vertex wobble on players: it mushes them at a distance
    c.customProgramCacheKey = () => 'player';
    noFog.set(m, c);
  }
  return noFog.get(m);
}
const outlineMats = new Map();
function outlineMat(color) {
  if (!outlineMats.has(color)) outlineMats.set(color, new THREE.MeshBasicMaterial({ color, side: THREE.BackSide, fog: false }));
  return outlineMats.get(color);
}
let markerTex = null;
function markerTexture() {
  if (markerTex) return markerTex;
  const c = document.createElement('canvas'); c.width = c.height = 16;
  const g = c.getContext('2d');
  g.fillStyle = '#000'; g.beginPath(); g.moveTo(1, 2); g.lineTo(15, 2); g.lineTo(8, 14); g.fill();
  g.fillStyle = '#fff'; g.beginPath(); g.moveTo(3, 3); g.lineTo(13, 3); g.lineTo(8, 11); g.fill();
  markerTex = new THREE.CanvasTexture(c);
  markerTex.magFilter = THREE.NearestFilter; markerTex.minFilter = THREE.NearestFilter;
  return markerTex;
}
const camPos = new THREE.Vector3();
// sleep arrow: the Zs that float over a sleeper's head
let zTex = null;
function zTexture() {
  if (zTex) return zTex;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  g.font = 'bold 54px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineWidth = 8; g.strokeStyle = '#000'; g.strokeText('Z', 32, 34);
  g.fillStyle = '#b07dff'; g.fillText('Z', 32, 34);
  zTex = new THREE.CanvasTexture(c);
  return zTex;
}
const NAP_DIRS = [[0, 1, 1, 0], [0, -1, -1, 0], [-1, 0, 0, 1], [1, 0, 0, -1]]; // [local x, local z, tilt x, tilt z]: back, front, left, right
const napBox = new THREE.Box3();
// infection: a zombie is the same mannequin gone rotten green, clothes faded to grey, outlined in zombie green
const zombieLook = (lk) => ({ ...(lk || {}), skin: '#6f9a3a', topColor: '#4a5a3a', bottomColor: '#3a3a30', hairColor: '#2a3a1a' });

const tmpV = new THREE.Vector3(), tmpQ = new THREE.Quaternion(), tmpS = new THREE.Vector3();
// reverse card on: the UNO reverse arrows, life size, chasing each other round their waist
let unoParts = null;
function unoRing() {
  const R = 0.85, end = Math.PI * 0.72;
  unoParts ||= { arc: new THREE.TorusGeometry(R, 0.07, 6, 20, end), head: new THREE.ConeGeometry(0.17, 0.32, 8), mats: [0xff2a2a, 0xffd23b].map((c) => new THREE.MeshBasicMaterial({ color: c, fog: false })) };
  const g = new THREE.Group();
  for (let i = 0; i < 2; i++) {
    const a = new THREE.Group(), mat = unoParts.mats[i];
    a.add(new THREE.Mesh(unoParts.arc, mat));
    const h = new THREE.Mesh(unoParts.head, mat); // arrowhead at the end of the arc, pointing along it
    h.position.set(Math.cos(end) * R, Math.sin(end) * R, 0);
    h.rotation.z = end;
    a.add(h);
    a.rotation.z = i * Math.PI;
    g.add(a);
  }
  g.rotation.x = Math.PI / 2; // flat round the waist; spin it on z
  return g;
}
function lerpAngle(a, b, t) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * t;
}

export class Remote {
  constructor(id, name, color, skins = {}, bot = false, look = null, team = 0) {
    Object.assign(this, {
      id, name, color, skins, bot, outfit: look, team, buf: [], pos: [0, -999, 0], vel: [0, 0, 0], yaw: 0, pitch: 0,
      w: null, hp: 100, alive: true, g: null, f: 0, k: 0, d: 0, walk: 0, burnUntil: 0,
      rope: null, shadow: null, ch: null, twitchUntil: 0, twitchNext: 2000 + Math.random() * 5000, twitch: null,
    });
    this.build();
  }

  build() {
    if (this.ch) { G.scene.remove(this.ch.root); this.free(); }
    this.ice = null; this.shells = []; this.glow = 0; this.zzz = null;
    // infection: a zombie. otherwise, on a team: team colour, not your clothes
    const color = this.zombie ? INFECT.color : this.color;
    this.ch = buildCharacter(color, this.zombie ? zombieLook(this.outfit) : gearLook(teamLook(this.outfit, this.team), this.gear)); // gearLook: no hat under a Plant & Defuse bucket
    if (this.gear && !this.zombie) dressGear(this.ch, this.gear, teamLook(this.outfit, this.team), this.team); // Plant & Defuse armor they bought
    this.ch.root.scale.setScalar(1.2); // a bit bigger than you so they read at crusty resolutions
    const outline = outlineMat(new THREE.Color(color).getHex());
    const parts = [];
    this.ch.body.traverse((o) => { if (o.isMesh) parts.push(o); });
    for (const o of parts) {
      o.material = visibleMat(o.material);
      if (o.userData.noShell) continue; // a small armor bit inside a bigger outline (econ3d.js)
      const shell = new THREE.Mesh(o.geometry, outline);
      shell.scale.setScalar(1.12);
      shell.userData.outline = true;
      o.add(shell);
      this.shells.push(shell);
    }
    this.marker = new THREE.Sprite(new THREE.SpriteMaterial({ map: markerTexture(), color, sizeAttenuation: false, fog: false, transparent: true }));
    this.marker.scale.set(0.035, 0.035, 1);
    this.marker.position.y = 2.75;
    this.ch.root.add(this.marker);
    this.tag = makeNameTag(this.name, this.color);
    this.tag.material.fog = false;
    this.tag.position.y = 2.3;
    this.ch.root.add(this.tag);
    G.scene.add(this.ch.root);
    if (!this.rope) { this.rope = makeRope(this.grap); this.rope.visible = false; G.scene.add(this.rope); }
    if (!this.shadow) { this.shadow = makeShadow(); G.scene.add(this.shadow); }
    this.card = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 1.05), new THREE.MeshBasicMaterial({ map: cardTex(), side: THREE.DoubleSide }));
    this.card.position.y = 2.9;
    this.card.visible = false;
    this.ch.root.add(this.card);
    const w = this.w;
    this.w = null;
    if (w) this.setWeapon(w);
  }

  setLook(look, color) {
    this.outfit = look; if (color) this.color = color;
    const keep = this.pos.slice();
    this.build();
    this.pos = keep;
  }
  // the old character's GPU copies: its geometries, name tag, marker, card and ice (shared materials stay)
  free() {
    freeTree(this.ch.root);
    this.tag.material.map.dispose(); this.tag.material.dispose();
    this.marker.material.dispose(); // its texture is shared
    this.card.material.dispose(); // so is the card's
    if (this.ice) this.ice.material.dispose();
    if (this.zzz) for (const z of this.zzz.children) z.material.dispose(); // the Z texture is shared
  }

  // Plant & Defuse: what they bought (vest 1, bucket 2, pliers 4) goes on the model
  setGear(bits) { bits = bits || 0; if (bits === (this.gear || 0)) return; this.gear = bits; this.setLook(this.outfit); }
  // infection: turn into a zombie (or back). the real look and colour stay put underneath
  setZombie(on) { if (!!this.zombie === on) return; this.zombie = on; this.setLook(this.outfit); }

  setKat(n) { this.katN = n; if (this.w === 'katana' && this.weaponMesh) setKatana(this.weaponMesh, n); }
  // revolver: a quick twirl after every shot, one turn per shot while they fan the hammer (same timing as yours).
  // the gun points forward for this shot's tracer; update() puts the spin back on
  revShot(fan) {
    twirlShot(this.tw || (this.tw = newTwirl()), fan);
    if (this.weaponMesh && this.w === 'revolver') applyTwirl(this.weaponMesh, 0, this.weaponMesh.scale.x);
  }
  setSkins(s) { this.skins = s || {}; const w = this.w; this.w = null; if (w) this.setWeapon(w); }
  setGrapple(id) { this.grap = id; setRopeSkin(this.rope, id); } // their grapple skin (unknown ids fall back to rope)

  setWeapon(w) {
    this.w = w;
    if (this.weaponMesh) freeTree(this.weaponMesh);
    this.ch.slot.clear();
    this.weaponMesh = null;
    if (w) {
      this.weaponMesh = buildWeapon(w, this.skins[w]);
      this.weaponMesh.traverse((o) => { // blade-kit meshes carry a [flat, bevel] material pair
        if (!o.isMesh) return;
        const arr = Array.isArray(o.material), ms = arr ? o.material : [o.material];
        if (ms.some((m) => m.transparent)) return;
        o.material = arr ? ms.map(visibleMat) : visibleMat(o.material);
      });
      this.weaponMesh.scale.setScalar(w === 'bread' ? 1.0 : 1.5);
      if (w === 'katana') setKatana(this.weaponMesh, this.katN || 0);
      this.ch.slot.add(this.weaponMesh);
    }
  }

  snap(t, e) {
    const [, x, y, z, vx, vy, vz, yaw, pitch, w, hp, alive, g, f, k, d] = e;
    if (alive && !this.alive) { this.buf.length = 0; this.frozenUntil = 0; this.nap = null; } // respawned: don't interpolate across the map, no ice, not asleep
    this.buf.push({ t, p: [x, y, z], v: [vx, vy, vz], yaw, pitch });
    if (this.buf.length > 60) this.buf.shift();
    this.vel = [vx, vy, vz];
    if (g && !this.g && alive && !this.ghost && this.buf.length > 1) sfx.grapple(this.grap, g); // their hook just landed: you hear it, a bit quieter
    this.hp = hp; this.alive = !!alive; this.g = g || null; this.f = f; this.k = k; this.d = d;
    if (w !== this.w) this.setWeapon(w);
  }

  // what you can hit matches what you see: far-away players are drawn (and hit-tested) bigger on your screen
  hitboxes() {
    if ((this.f & FLAGS.BALL) && this.alive) return ballBoxes(this.pos, this.distScale || 1); // a wrecking ball is one big ball
    const k = (this.distScale || 1);
    if (this.rigOn) return rigBoxes(this.pos, k); // the overdrive rig is a much bigger target
    const boxes = this.nap && this.napK > 0.5 ? this.napBoxes() : playerBoxes(this.pos);
    if (k === 1) return boxes;
    const [x, y, z] = this.pos;
    return boxes.map((b) => ({
      head: b.head,
      min: [x + (b.min[0] - x) * k, y + (b.min[1] - y) * k, z + (b.min[2] - z) * k],
      max: [x + (b.max[0] - x) * k, y + (b.max[1] - y) * k, z + (b.max[2] - z) * k],
    }));
  }

  // knocked flat by a sleep arrow: the body and head lie along the floor where the body is drawn
  napBoxes() {
    const n = this.nap, [x, y, z] = this.pos, c = Math.cos(this.yaw), s = Math.sin(this.yaw);
    const dx = n.dx * c + n.dz * s, dz = -n.dx * s + n.dz * c, y0 = y + n.liftW, rise = Math.tan(n.slope);
    const seg = (a, b, r, h, head) => {
      const ax = x + dx * a, az = z + dz * a, bx = x + dx * b, bz = z + dz * b, ya = y0 + a * rise, yb = y0 + b * rise;
      return { head, min: [Math.min(ax, bx) - r, Math.min(ya, yb) - 0.05, Math.min(az, bz) - r], max: [Math.max(ax, bx) + r, Math.max(ya, yb) + h, Math.max(az, bz) + r] };
    };
    return [seg(0, 1.75, 0.42, 0.75, false), seg(1.75, 2.35, 0.36, 0.7, true)];
  }

  // how to fall: with the shove if there's room, else whichever way has floor and no wall. tilted to the slope under them
  // and lifted so no part of them (backpack, hat, wings) goes through the floor
  pickNap(now) {
    const ch = this.ch, [x, y, z] = this.pos, c = Math.cos(this.yaw), s = Math.sin(this.yaw);
    const sc = ch.root.scale.y, L = 1.9 * sc;
    const lvx = this.vel[0] * c - this.vel[2] * s, lvz = this.vel[0] * s + this.vel[2] * c; // velocity in the body's frame
    const order = NAP_DIRS.slice().sort((a, b) => (b[0] * lvx + b[1] * lvz) - (a[0] * lvx + a[1] * lvz) + (a === NAP_DIRS[0] ? -0.5 : b === NAP_DIRS[0] ? 0.5 : 0));
    let best = null;
    for (const d of order) {
      const wx = d[0] * c + d[1] * s, wz = -d[0] * s + d[1] * c;
      const wall = raycast([x, y + 0.4, z], [wx, 0, wz], L + 0.3, BOXES);
      const free = wall ? wall.t : L + 0.3;
      const ground = [];
      for (const f of [0.33, 0.66, 1]) { const g = raycast([x + wx * L * f, y + 1.2, z + wz * L * f], [0, -1, 0], 4, BOXES); ground.push(g ? g.point[1] - y : -2); }
      const score = free + (ground[2] > -1.5 ? 1 : 0);
      if (!best || score > best.score + 0.01) best = { d, ground, score };
      if (!wall && ground[2] > -1.5) break;
    }
    const slope = Math.max(-0.45, Math.min(0.45, Math.atan2(best.ground[2], L)));
    let liftW = 0;
    best.ground.forEach((g, i) => { liftW = Math.max(liftW, g - L * [0.33, 0.66, 1][i] * Math.tan(slope)); });
    // how far below the feet the lying body reaches, measured on the real model in the lying pose
    const n = { t: now, wake: 0, dx: best.d[0], dz: best.d[1], tx: best.d[2], tz: best.d[3], slope, liftW, lift: 0 };
    const parts = [ch.body.rotation, ch.body.position, ch.legL.rotation, ch.legR.rotation, ch.kneeL.rotation, ch.kneeR.rotation, ch.arm.rotation, ch.armL.rotation, ch.head.rotation];
    if (ch.cape) parts.push(ch.cape.rotation);
    const keep = parts.map((v) => [v.x, v.y, v.z]);
    this.napPose(n, 1, Math.PI / 2 - slope, 0);
    ch.root.updateMatrixWorld(true);
    let minY = 0;
    ch.body.traverse((o) => {
      if (!o.isMesh || o.userData.outline || !o.geometry || !o.visible) return; // (hidden bits don't count)
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      napBox.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
      minY = Math.min(minY, (napBox.min.y - ch.root.position.y) / sc);
    });
    parts.forEach((v, i) => v.set(...keep[i]));
    n.lift = liftW / sc - minY + 0.05;
    return n;
  }
  // k: 0 standing .. 1 flat on the floor
  napPose(n, k, ang, y) {
    const ch = this.ch, mix = (a, b) => a + (b - a) * k;
    ch.body.rotation.x = n.tx * ang; ch.body.rotation.z = n.tz * ang;
    ch.body.position.y = y;
    ch.legL.rotation.x = mix(ch.legL.rotation.x, 0.06); ch.legR.rotation.x = mix(ch.legR.rotation.x, -0.04);
    ch.kneeL.rotation.x = mix(ch.kneeL.rotation.x, 0.1); ch.kneeR.rotation.x = mix(ch.kneeR.rotation.x, 0);
    ch.arm.rotation.x = mix(ch.arm.rotation.x, -1.35); ch.armL.rotation.x = mix(ch.armL.rotation.x, -1.45); // arms down by the sides
    ch.arm.rotation.y = mix(ch.arm.rotation.y, 0);
    ch.head.rotation.x = mix(ch.head.rotation.x, 0); ch.head.rotation.y = mix(ch.head.rotation.y, 0.5);
    if (ch.cape) ch.cape.rotation.x = mix(ch.cape.rotation.x, -0.05);
  }

  // sleep arrow: topples over, lies on the floor the whole nap with Zs over the head, then a quick get-up
  updateNap(now) {
    const ch = this.ch, asleep = !!(this.f & FLAGS.SLEEP);
    if (asleep && !this.nap) this.nap = this.pickNap(now);
    const n = this.nap;
    this.napK = 0;
    if (!n) return;
    if (asleep) n.wake = 0; else if (!n.wake) n.wake = now;
    const fall = Math.min(1, (now - n.t) / 450), up = n.wake ? Math.min(1, (now - n.wake) / 380) : 0;
    if (up >= 1) { this.nap = null; if (this.zzz) this.zzz.visible = false; return; }
    const k = fall * fall * (1 - up * up * (3 - 2 * up)); // falls like a plank, gets up quick
    const land = (now - n.t - 450) / 260, bounce = land > 0 && land < 1 && !n.wake ? Math.sin(land * Math.PI) * 0.07 : 0;
    this.napPose(n, k, (Math.PI / 2 - n.slope) * k - bounce, (n.lift + Math.sin(now * 0.0021) * 0.012) * k); // breathing
    this.napK = k;
    // Zzz over the head while they're down
    if (!this.zzz) {
      this.zzz = new THREE.Group();
      for (let i = 0; i < 3; i++) this.zzz.add(new THREE.Sprite(new THREE.SpriteMaterial({ map: zTexture(), transparent: true, depthWrite: false, fog: false })));
      ch.root.add(this.zzz);
    }
    const show = fall > 0.7 && !n.wake;
    this.zzz.visible = show;
    if (!show) return;
    const hl = 1.75 * Math.cos(n.slope), hy = n.lift + 1.75 * Math.sin(n.slope) + 0.35;
    this.zzz.position.set(n.dx * hl, hy, n.dz * hl);
    this.zzz.children.forEach((z, i) => {
      const ph = ((now - n.t) / 1600 + i / 3) % 1;
      z.position.set(Math.sin(ph * 5 + i * 2) * 0.12, ph * 0.9, 0);
      z.scale.setScalar(0.2 + ph * 0.22);
      z.material.opacity = Math.sin(ph * Math.PI);
      z.material.rotation = Math.sin(ph * 4 + i) * 0.3;
    });
  }

  look() {
    const cp = Math.cos(this.pitch);
    return [-Math.sin(this.yaw) * cp, Math.sin(this.pitch), -Math.cos(this.yaw) * cp];
  }

  muzzle() {
    if (!this.weaponMesh) return [this.pos[0], this.pos[1] + 1.2, this.pos[2]];
    this.ch.root.updateMatrixWorld(true);
    tmpV.copy(this.weaponMesh.userData.muzzle);
    this.weaponMesh.localToWorld(tmpV);
    return [tmpV.x, tmpV.y, tmpV.z];
  }

  // items (party popper, reverse card) pop into their hand for a moment, skin and all, then it's back to the gun
  popItem(id, ms) {
    if (this.itemMesh) this.itemMesh.removeFromParent();
    // one mesh per item, reused every pop: building one each time leaked geometries + noFog clones
    this.items ||= {};
    const key = id + JSON.stringify(this.skins[id] || '');
    let g = this.items[id];
    if (!g || g.userData.key !== key) { // only a new skin rebuilds it
      g = buildWeapon(id, this.skins[id]);
      g.traverse((o) => { if (o.isMesh && !o.material.transparent) o.material = visibleMat(o.material); });
      g.scale.setScalar(1.5);
      g.userData.key = key;
      this.items[id] = g;
    }
    this.itemMesh = g;
    this.ch.slot.add(g);
    this.itemUntil = performance.now() + ms;
  }
  itemMuzzle() {
    const g = this.itemMesh && this.itemMesh.parent ? this.itemMesh : this.weaponMesh;
    if (!g) return [this.pos[0], this.pos[1] + 1.2, this.pos[2]];
    this.ch.root.updateMatrixWorld(true);
    tmpV.copy(g.userData.muzzle);
    g.localToWorld(tmpV);
    return [tmpV.x, tmpV.y, tmpV.z];
  }
  // reverse card on: the card over their head gets big and bobs, the arrows go round them, their outline turns red
  unoFx(on, dt, now) {
    if (on && (!this.uno || this.uno.parent !== this.ch.root)) { this.uno = unoRing(); this.uno.position.y = 1.05; this.ch.root.add(this.uno); }
    if (this.uno) this.uno.visible = on;
    if (on) {
      this.uno.rotation.z -= dt * 6; this.uno.rotation.y = Math.sin(now * 0.004) * 0.2;
      const s = 1.6 + Math.sin(now * 0.012) * 0.15;
      this.card.scale.set(s, s, s); this.card.position.y = 3.2 + Math.sin(now * 0.006) * 0.1;
    } else if (this.card.scale.x !== 1) { this.card.scale.set(1, 1, 1); this.card.position.y = 2.9; } // back to the little card over their head
    const red = outlineMat(0xff2a2a), sh = this.shells || [];
    if (sh.length && on !== (sh[0].material === red)) { const mat = on ? red : outlineMat(new THREE.Color(this.color).getHex()); for (const s of sh) s.material = mat; }
  }

  // the mannequin comes apart. pieces get flung and bounce around for a few seconds.
  breakApart(vel) {
    if (!this.ch.root.visible) return;
    this.ch.root.updateMatrixWorld(true);
    const parts = [];
    this.ch.body.traverse((o) => { if (o.isMesh && !o.userData.outline) parts.push(o); });
    const floor = raycast([this.pos[0], this.pos[1] + 1, this.pos[2]], [0, -1, 0], 30, BOXES);
    const floorY = floor ? floor.point[1] : -1e9;
    for (const o of parts) {
      // each gib gets its own geometry: the character can be rebuilt (and freed) while they fly
      const own = !o.geometry.userData.shared;
      const m = new THREE.Mesh(own ? o.geometry.clone() : o.geometry, o.material);
      o.matrixWorld.decompose(m.position, m.quaternion, m.scale);
      G.scene.add(m);
      G.gibs.push({
        m, own, floorY, life: 4 + Math.random(),
        v: [vel[0] * 0.6 + (Math.random() - 0.5) * 7, vel[1] * 0.5 + 3 + Math.random() * 5, vel[2] * 0.6 + (Math.random() - 0.5) * 7],
        av: [(Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14],
      });
    }
    this.ch.root.visible = false;
  }

  update(rt, dt, now) {
    const b = this.buf, ch = this.ch;
    const show = this.alive && b.length > 0;
    const dashing = !!(this.f & FLAGS.DASH);
    ch.root.visible = show && !dashing;
    this.shadow.visible = show;
    if (!show) { this.rope.visible = false; return; }
    if (dashing) { fx.glitch(this.pos, this.vel, 6); this.shadow.visible = false; }

    let i = b.length - 1;
    while (i > 0 && b[i].t > rt) i--;
    const s0 = b[i], s1 = b[i + 1];
    if (s1 && rt >= s0.t) {
      const a = Math.min(1, (rt - s0.t) / Math.max(1, s1.t - s0.t));
      for (let k = 0; k < 3; k++) this.pos[k] = s0.p[k] + (s1.p[k] - s0.p[k]) * a;
      this.yaw = lerpAngle(s0.yaw, s1.yaw, a);
      this.pitch = s0.pitch + (s1.pitch - s0.pitch) * a;
    } else {
      const ex = Math.min(0.25, Math.max(0, (rt - s0.t) / 1000));
      for (let k = 0; k < 3; k++) this.pos[k] = s0.p[k] + s0.v[k] * ex;
      this.yaw = s0.yaw; this.pitch = s0.pitch;
    }
    if (i > 3) b.splice(0, i - 3);

    const [x, y, z] = this.pos;
    ch.root.position.set(x, y, z);
    ch.root.rotation.y = this.yaw;
    ch.arm.rotation.x = this.pitch;
    ch.armL.rotation.x = this.pitch;

    // stiff mannequin walk: hips swing, knees only bend one way (unless this one is broken)
    const hs = Math.hypot(this.vel[0], this.vel[2]);
    const grounded = Math.abs(this.vel[1]) < 1;
    this.walk += dt * Math.min(hs, 14) * 1.5;
    const amp = grounded ? Math.min(1, hs / 8) * 0.8 : 0.35;
    const sw = Math.sin(this.walk);
    ch.legL.rotation.x = sw * amp;
    ch.legR.rotation.x = -sw * amp;
    // frozen by snowballs: an ice block, no walking
    const frozen = now < (this.frozenUntil || 0);
    if (frozen && !this.ice) {
      this.ice = new THREE.Mesh(new THREE.BoxGeometry(1.0, 2.3, 1.0), new THREE.MeshBasicMaterial({ color: 0xbfe8ff, transparent: true, opacity: 0.45, depthWrite: false }));
      this.ice.position.y = 1.15;
      ch.root.add(this.ice);
    }
    if (this.ice) this.ice.visible = frozen;
    if (frozen) this.walk -= dt * Math.min(hs, 14) * 1.5;
    // cape streams out behind you the faster you go (negative tilt = backwards); wings flap in the air
    if (ch.cape) { const tgt = -(0.1 + Math.min(1.15, hs * 0.035) + (hs > 2 ? Math.sin(now * 0.014) * 0.07 : 0)); ch.cape.rotation.x += (tgt - ch.cape.rotation.x) * Math.min(1, dt * 8); }
    if (ch.wings) { const f = grounded ? 0 : Math.sin(now * 0.02) * 0.6; ch.wings[0].rotation.y = 0.25 + f; ch.wings[1].rotation.y = -0.25 - f; }
    const bend = ch.jank.wrongKnee ? -1 : 1;
    ch.kneeL.rotation.x = Math.max(0, -sw) * amp * 1.2 * bend + (grounded ? 0 : 0.8);
    ch.kneeR.rotation.x = Math.max(0, sw) * amp * 1.2 * bend + (grounded ? 0 : 0.8);

    // random twitches: head snaps, arm glitches out for a moment
    if (now > this.twitchNext) {
      this.twitch = Math.random() < 0.6 ? 'head' : 'arm';
      this.twitchUntil = now + 90 + Math.random() * 160;
      this.twitchNext = now + 1500 + Math.random() * 5000;
    }
    const tw = now < this.twitchUntil;
    ch.head.rotation.x = this.pitch * 0.5;
    const cg = (now - (this.coughT || -1e9)) / 1000; // coughing: three hacking jerks forward, fading out
    if (cg >= 0 && cg < 1) ch.head.rotation.x += Math.abs(Math.sin(cg * Math.PI * 3)) * (1 - cg) * 0.7;
    ch.head.rotation.y = tw && this.twitch === 'head' ? 1.4 : 0;
    ch.head.rotation.z = ch.jank.tilt + (tw && this.twitch === 'head' ? 0.6 : 0);
    if (tw && this.twitch === 'arm') ch.armL.rotation.z = 1.8; else ch.armL.rotation.z = 0;

    const slipping = this.f & FLAGS.SLIP;
    const sliding = this.f & FLAGS.SLIDE;
    const crouching = this.f & FLAGS.CROUCH;
    // crouch: sink the body and bend the knees
    const sink = crouching ? 0.45 : 0;
    ch.body.position.y += (-sink - ch.body.position.y) * Math.min(1, dt * 14);
    if (crouching) { ch.legL.rotation.x = -0.9; ch.legR.rotation.x = -0.9; ch.kneeL.rotation.x = 1.6; ch.kneeR.rotation.x = 1.6; }
    // melee swing everyone else can see
    const st = (now - (this.swingT || 0)) / 380;
    if (st >= 0 && st < 1) {
      const k = Math.sin(st * Math.PI);
      ch.arm.rotation.y = (st < 0.35 ? -1 : 1) * k * 1.3;
      ch.arm.rotation.x = this.pitch + k * 0.5;
    } else ch.arm.rotation.y = 0;
    // katana parry ('guard' event): blade snaps up across the body, holds through the window, drops back.
    // a parried hit (parryHitT) jolts it up a touch
    const pk = this.w === 'katana' ? (now - (this.parryT || -1e9)) / 560 : 1;
    if (pk >= 0 && pk < 1) {
      const k = pk < 0.09 ? pk / 0.09 : pk > 0.62 ? 1 - (pk - 0.62) / 0.38 : 1;
      const jolt = Math.max(0, 1 - (now - (this.parryHitT || -1e9)) / 140) * 0.3;
      ch.arm.rotation.x = this.pitch + (0.35 + jolt - this.pitch) * k;
      ch.arm.rotation.y = 0.75 * k;
      ch.slot.rotation.set(0.85 * k, 0.55 * k, 0);
    } else if (ch.slot.rotation.x) ch.slot.rotation.set(0, 0, 0);
    // marker + name tag stay readable far away
    G.camera.getWorldPosition(camPos);
    const dist = camPos.distanceTo(ch.root.position);
    const sat = now < (G.satUntil || 0);
    this.distScale = 1 + Math.max(0, Math.min(1, (dist - 25) / 60)) * 0.8;
    ch.root.scale.setScalar(1.2 * this.distScale);
    this.marker.visible = dist > 18 || sat;
    this.marker.material.depthTest = !sat; // spy satellite: see them through walls
    this.marker.renderOrder = sat ? 10 : 0;
    this.marker.scale.setScalar((sat ? 0.05 : 0.042) / (1.2 * this.distScale));
    // thicker outline the further away they are, so they still read as a person at crusty resolution
    const glow = 1.12 + Math.max(0, Math.min(1, (dist - 15) / 60)) * 0.6;
    if (this.shells && Math.abs((this.glow || 0) - glow) > 0.01) { this.glow = glow; for (const sh of this.shells) sh.scale.setScalar(glow); }
    this.tag.scale.set(1.8 * Math.max(1, dist / 22), 0.45 * Math.max(1, dist / 22), 1);
    this.tag.position.y = 2.3 + Math.max(0, dist / 22 - 1) * 0.25;
    tacLook(this); tacSteps(this, dt); // Plant & Defuse: no outline / tag on enemies, footsteps unless they slow walk
    const targetTilt = slipping ? -1.3 + Math.sin(now * 0.02) * 0.3 : sliding ? -0.6 : 0;
    ch.body.rotation.x += (targetTilt - ch.body.rotation.x) * Math.min(1, dt * 12);
    ch.body.rotation.z = slipping ? Math.sin(now * 0.013) * 0.6 : ch.jank.lean * 0.3;
    this.updateNap(now);

    if (this.g) {
      this.rope.visible = true;
      setRope(this.rope, this.muzzle(), this.g);
    } else this.rope.visible = false;
    wreckRemote(this, dt, now); // wrecking ball killstreak: a steel ball (and a chain) instead of the mannequin

    const sh = raycast([x, y + 0.1, z], [0, -1, 0], 80, BOXES);
    if (sh) { this.shadow.visible = true; this.shadow.position.set(x, sh.point[1] + 0.03, z); } else this.shadow.visible = false;
    rigRemote(this, dt, now, sh); // overdrive rig: the exo-frame (and its afterimages) instead of the mannequin

    const ld = this.look();
    const head = [x + ld[0] * 0.45, y + 1.5, z + ld[2] * 0.45];
    if ((this.f & FLAGS.SMOKE) && Math.random() < dt * 25) fx.smoke(head, 1);
    if (this.f & FLAGS.FIRE) fx.fireCone(head, ld, this.vel, 5);
    if (this.f & FLAGS.BLOW) fx.leaves(this.muzzle(), ld, this.vel);
    if (this.w === 'shredder') remoteShredder(this, dt);
    if (this.weaponMesh && this.weaponMesh.userData.barrels && (this.f & FLAGS.SPIN)) this.weaponMesh.userData.barrels.rotation.z += dt * 40;
    this.card.visible = !!(this.f & FLAGS.REVERSE) || now < (this.reverseUntil || 0);
    if (this.card.visible) this.card.rotation.y += dt * 9;
    this.unoFx(this.card.visible, dt, now);
    // a popped item hides the gun until it's done
    const holding = !!this.itemMesh && this.itemMesh.parent === this.ch.slot && now < this.itemUntil;
    if (this.itemMesh && !holding) { this.itemMesh.removeFromParent(); this.itemMesh = null; }
    if (this.weaponMesh) this.weaponMesh.visible = !holding;
    if (now < this.burnUntil && Math.random() < 0.7) fx.burn(this.pos);
    if (this.w !== 'revolver') this.tw = null;
    else if (this.tw && this.weaponMesh) applyTwirl(this.weaponMesh, stepTwirl(this.tw, dt), this.weaponMesh.scale.x);
    if (this.weaponMesh) { ch.root.updateMatrixWorld(true); emitSkinFx(G.skinFxWorld, this.weaponMesh, dt, this.w === 'bread' ? 1 : 1.5); }
  }

  dispose() {
    G.scene.remove(this.ch.root);
    G.scene.remove(this.rope);
    G.scene.remove(this.shadow);
    wreckDispose(this);
    this.free();
    rigDispose(this);
    // the rope is a grapple-skin group: its beams + hook share the skin's geometries and materials, nothing to free
    this.shadow.geometry.dispose(); this.shadow.material.dispose();
  }
}

// flying mannequin pieces
export function updateGibs(dt) {
  for (let i = G.gibs.length - 1; i >= 0; i--) {
    const g = G.gibs[i];
    g.life -= dt;
    g.v[1] -= 22 * dt;
    g.m.position.x += g.v[0] * dt; g.m.position.y += g.v[1] * dt; g.m.position.z += g.v[2] * dt;
    if (g.m.position.y < g.floorY + 0.05) {
      g.m.position.y = g.floorY + 0.05;
      g.v[1] = Math.abs(g.v[1]) * 0.35; g.v[0] *= 0.6; g.v[2] *= 0.6;
      g.av = g.av.map((a) => a * 0.6);
    }
    g.m.rotation.x += g.av[0] * dt; g.m.rotation.y += g.av[1] * dt; g.m.rotation.z += g.av[2] * dt;
    if (g.life < 0.5) g.m.scale.multiplyScalar(Math.max(0, 1 - dt * 6));
    if (g.life <= 0) { G.scene.remove(g.m); if (g.own) g.m.geometry.dispose(); G.gibs.splice(i, 1); }
  }
}
