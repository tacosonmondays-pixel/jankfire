// Kill effects: what happens to the people you kill. Some replace the gibs, some go on top of them.
import * as THREE from 'three';
import { G } from './ctx.js';
import { fx } from './fx.js';
import { sfx } from './audio.js';
import { buildCharacter, buildProjectile, M, freeTree } from './models.js';
import { raycast } from '/shared/physics.js';
import { BOXES } from '/shared/map.js';

const live = []; // { obj, age, life, step(o, dt, age) }
const R = (s = 1) => (Math.random() * 2 - 1) * s;

function floorAt(p) {
  const h = raycast([p[0], p[1] + 1, p[2]], [0, -1, 0], 40, BOXES);
  return h ? h.point[1] : p[1];
}
function add(obj, life, step) { G.scene.add(obj); live.push({ obj, age: 0, life, step }); return obj; }
const own = (m) => { m.userData.own = true; return m; }; // made for one effect: freed with it
function drop(obj) { // done: give its GPU copies back (the shared M() materials stay)
  G.scene.remove(obj);
  freeTree(obj);
  obj.traverse((o) => { const m = o.material; if (m && m.userData && m.userData.own) { if (m.map) m.map.dispose(); m.dispose(); } });
}

// a copy of the victim's mannequin to do horrible things to
function body(c) {
  const ch = buildCharacter(c.color, c.look);
  ch.root.position.set(c.pos[0], c.pos[1], c.pos[2]);
  ch.root.rotation.y = c.yaw || 0;
  ch.root.scale.setScalar(1.2);
  return ch;
}

function textTex(lines, w, h, bg, fg, font) {
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const x = cv.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, w, h);
  x.fillStyle = fg; x.textAlign = 'left'; x.textBaseline = 'top';
  let y = 8;
  for (const [t, size] of lines) { x.font = `${size}px ${font || '"Comic Neue", sans-serif'}`; x.fillText(t, 10, y); y += size * 1.15; }
  const tex = new THREE.CanvasTexture(cv);
  tex.magFilter = THREE.NearestFilter; tex.minFilter = THREE.NearestFilter;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// Blast Zone's size (1 = the original big burst). a knob so it's easy to tune
export const BLASTZONE = { scale: 1 };

const EFFECTS = {
  confetti(c) {
    const p = [c.pos[0], c.pos[1] + 1.2, c.pos[2]];
    fx.confetti(p, [0, 1, 0], [0, 0, 0]);
    setTimeout(() => fx.confetti(p, [0, 0.6, 0], [0, 2, 0]), 120);
    sfx.popper(p); sfx.partyHorn(p);
    return false;
  },
  grave(c) {
    const fy = floorAt(c.pos);
    const g = new THREE.Group();
    const stone = M(0x8a8f99);
    const slab = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.0, 0.22), stone);
    slab.position.y = 0.5;
    const top = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.22, 10, 1, false, 0, Math.PI), stone);
    top.rotation.x = Math.PI / 2; top.rotation.z = Math.PI / 2; top.position.y = 1.0;
    const face = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.7), own(new THREE.MeshBasicMaterial({ map: textTex([['R.I.P.', 34], [String(c.name || 'bozo').slice(0, 12), 22], ['skill issue', 16]], 200, 170, '#8a8f99', '#2a2a30') })));
    face.position.set(0, 0.62, 0.115);
    const dirt = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.08, 1.6), M(0x5a3a20));
    dirt.position.set(0, 0.04, 0.8);
    g.add(slab, top, face, dirt);
    g.position.set(c.pos[0], fy - 1.2, c.pos[2]);
    g.rotation.y = c.yaw || 0;
    add(g, 7, (o, dt, age) => {
      o.position.y = fy - 1.2 + Math.min(1, age / 0.35) * 1.2 - Math.max(0, age - 6.4) * 2;
      if (age < 0.35) fx.dust([o.position.x, fy, o.position.z], 2);
    });
    sfx.thunk(c.pos); sfx.ting(c.pos);
    return false;
  },
  cash(c) {
    const p = [c.pos[0], c.pos[1] + 1.2, c.pos[2]];
    fx.spray(p, 90, [0x3bbf4a, 0x2a8a35, 0xffd21a], 12, 2.2, 0.2, 4, 2.2);
    for (let i = 0; i < 14; i++) {
      const bill = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.15), own(new THREE.MeshBasicMaterial({ color: 0x5fd36a, side: THREE.DoubleSide })));
      bill.position.set(p[0], p[1], p[2]);
      const v = [R(5), 4 + Math.random() * 6, R(5)], av = [R(8), R(8), R(8)];
      add(bill, 3 + Math.random(), (o, dt) => {
        v[1] -= 6 * dt; v[0] *= 1 - dt; v[2] *= 1 - dt; v[1] = Math.max(v[1], -1.5);
        o.position.x += v[0] * dt; o.position.y += v[1] * dt; o.position.z += v[2] * dt;
        o.rotation.x += av[0] * dt; o.rotation.y += av[1] * dt; o.rotation.z += av[2] * dt;
      });
    }
    sfx.cash(p);
    return false;
  },
  pixel(c) {
    const fy = floorAt(c.pos);
    const mats = [M(0xff00dc, true), M(0x000000, true)];
    const geo = new THREE.BoxGeometry(0.22, 0.22, 0.22);
    for (let i = 0; i < 46; i++) {
      const m = new THREE.Mesh(geo, mats[i & 1]);
      m.position.set(c.pos[0] + R(0.35), c.pos[1] + 0.2 + Math.random() * 1.9, c.pos[2] + R(0.35));
      G.scene.add(m);
      G.gibs.push({ m, floorY: fy, life: 2.5 + Math.random() * 2, v: [c.vel[0] * 0.3 + R(5), 2 + Math.random() * 5, c.vel[2] * 0.3 + R(5)], av: [R(10), R(10), R(10)] });
    }
    setTimeout(() => geo.dispose(), 5000); // after the last of those gibs is gone
    fx.glitch([c.pos[0], c.pos[1], c.pos[2]], [0, 0, 0], 40);
    sfx.glitch(c.pos);
    return true;
  },
  balloon(c) {
    const ch = body(c);
    ch.arm.rotation.x = Math.PI * 0.9; ch.armL.rotation.x = Math.PI * 0.9;
    const cols = [0xff3040, 0x4fd8ff, 0xffe14d, 0x7dff4f];
    const balloons = new THREE.Group();
    for (let i = 0; i < 4; i++) {
      const b = new THREE.Mesh(new THREE.SphereGeometry(0.32, 8, 6), M(cols[i]));
      b.scale.y = 1.2;
      b.position.set(Math.cos(i * 1.6) * 0.45, 3.4 + (i % 2) * 0.35, Math.sin(i * 1.6) * 0.45);
      const str = new THREE.Mesh(new THREE.BoxGeometry(0.015, 1.4, 0.015), M(0xffffff, true));
      str.position.set(b.position.x * 0.5, 2.7, b.position.z * 0.5);
      balloons.add(b, str);
    }
    ch.root.add(balloons);
    const y0 = c.pos[1];
    add(ch.root, 5.5, (o, dt, age) => {
      o.position.y = y0 + age * age * 0.6 + age * 1.2;
      o.position.x += Math.sin(age * 2) * dt * 0.6;
      o.rotation.z = Math.sin(age * 2.3) * 0.15;
      ch.legL.rotation.x = Math.sin(age * 9) * 0.6; ch.legR.rotation.x = -Math.sin(age * 9) * 0.6; // kicking
      if (age > 5.3 && !o.userData.popped) { o.userData.popped = true; sfx.pop([o.position.x, o.position.y, o.position.z]); fx.confetti([o.position.x, o.position.y + 3, o.position.z], [0, 0.3, 0], [0, 0, 0]); }
    });
    sfx.squeak(c.pos);
    return true;
  },
  chicken(c) {
    const fy = floorAt(c.pos);
    fx.feathers([c.pos[0], c.pos[1] + 1, c.pos[2]], 50);
    fx.smoke([c.pos[0], c.pos[1] + 1, c.pos[2]], 12, 0.6);
    for (let i = 0; i < 6; i++) {
      const m = buildProjectile('chicken');
      const a = (i / 6) * Math.PI * 2 + Math.random() * 0.5, sp = 4 + Math.random() * 3;
      m.position.set(c.pos[0], fy + 0.25, c.pos[2]);
      m.scale.setScalar(0.9);
      const v = [Math.cos(a) * sp, Math.sin(a) * sp];
      add(m, 3.2, (o, dt, age) => {
        o.position.x += v[0] * dt; o.position.z += v[1] * dt;
        o.position.y = fy + 0.25 + Math.abs(Math.sin(age * 16)) * 0.25;
        o.lookAt(o.position.x - v[0], o.position.y, o.position.z - v[1]);
        if (age > 3.0 && !o.userData.p) { o.userData.p = 1; fx.feathers([o.position.x, o.position.y, o.position.z], 8); }
      });
    }
    sfx.squawk(c.pos); setTimeout(() => sfx.squawk(c.pos), 180);
    return true;
  },
  bsod(c) {
    const tex = textTex([[':(', 60], ['your player ran into a problem', 17], ['and needs to respawn.', 17], ['', 8], [`STOP CODE: ${String(c.name || 'BOZO').toUpperCase().slice(0, 10)}_DIED`, 13]], 320, 200, '#0a57c2', '#ffffff', 'monospace');
    const panel = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.5), own(new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, fog: false })));
    panel.position.set(c.pos[0], c.pos[1] + 1.4, c.pos[2]);
    add(panel, 3.2, (o, dt, age) => {
      o.quaternion.copy(G.camera.quaternion);
      o.visible = age > 0.25 || Math.random() < 0.5; // flicker on
      const k = age > 2.9 ? Math.max(0.01, 1 - (age - 2.9) / 0.3) : 1;
      o.scale.set(1, k, 1);
    });
    fx.glitch([c.pos[0], c.pos[1], c.pos[2]], [0, 0, 0], 25);
    sfx.error(c.pos);
    return false;
  },
  yeet(c) {
    const ch = body(c);
    const a = Math.random() * Math.PI * 2;
    const v = [Math.cos(a) * 25 + c.vel[0] * 0.5, 70, Math.sin(a) * 25 + c.vel[2] * 0.5];
    add(ch.root, 2.4, (o, dt, age) => {
      o.position.x += v[0] * dt; o.position.y += v[1] * dt; o.position.z += v[2] * dt;
      o.rotation.x += dt * 14; o.rotation.z += dt * 9;
      if (Math.random() < 0.6) fx.smoke([o.position.x, o.position.y, o.position.z], 1, 0.1);
      if (age > 2.2 && !o.userData.d) { o.userData.d = 1; fx.spray([o.position.x, o.position.y, o.position.z], 30, [0xffffff, 0xffe14d], 6, 0.8, 0.5, 0, 1); sfx.ting([o.position.x, o.position.y, o.position.z]); }
    });
    sfx.yeet(c.pos);
    return true;
  },
  // blast zone: knocked clean off the screen. they rocket away spinning with a trail, and where they "hit the edge" a
  // huge burst of colour jets back toward where they got hit, with a shockwave ring. loud
  blastzone(c) {
    const ch = body(c);
    const hv = Math.hypot(c.vel[0], c.vel[2]);
    const a = hv > 2 ? Math.atan2(c.vel[2], c.vel[0]) : Math.random() * Math.PI * 2;
    const dir = new THREE.Vector3(Math.cos(a), 0.55, Math.sin(a)).normalize(), sp = 60 * Math.sqrt(BLASTZONE.scale); // a smaller burst = a shorter flight too
    const start = new THREE.Vector3(c.pos[0], c.pos[1] + 1, c.pos[2]), FLY = 0.55;
    const tint = new THREE.Color(c.color || '#ff4fd8').getHex();
    add(ch.root, FLY, (o, dt, age) => {
      const k = Math.min(1, age / FLY), d = sp * age * (1 - k * 0.15);
      o.position.set(start.x + dir.x * d, start.y - 1 + dir.y * d, start.z + dir.z * d);
      o.rotation.x += dt * 22; o.rotation.z += dt * 15;
      fx.spray([o.position.x, o.position.y + 1, o.position.z], 2, [0xffffff, 0xffe14d, tint], 1.5, 0.35, 0.22, 0, 2); // the streak behind them
      if (age + dt >= FLY && !o.userData.boom) { o.userData.boom = 1; boom([o.position.x, o.position.y + 1, o.position.z]); }
    });
    const boom = (p) => {
      const at = new THREE.Vector3(...p), back = start.clone().sub(at).normalize(); // the burst points back at the map
      // ...but stops well short of where they got hit, and of the camera, so it's a big column you see, not a pink screen
      const cam = G.camera ? G.camera.position.distanceTo(at) : 60, reach = Math.max(8, Math.min(start.distanceTo(at) * 0.75, cam * 0.6));
      const beam = (len, r, color, spread, life) => {
        const f = Math.min(1, reach / 46), k = BLASTZONE.scale; len *= f * k; r *= Math.max(0.5, f) * k;
        const geo = new THREE.ConeGeometry(r, len, 14, 1, true);
        geo.translate(0, -len / 2, 0); // the tip at the blast point, opening toward the map
        const m = new THREE.Mesh(geo, own(new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9, depthWrite: false, side: THREE.DoubleSide, fog: false }))); // solid colour (not additive) so it reads on bright skies too
        const d = back.clone().add(new THREE.Vector3(R(spread), R(spread), R(spread))).normalize();
        m.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), d);
        m.position.copy(at); m.scale.set(0.2, 0.2, 0.2);
        add(m, life, (o, dt, age) => {
          const k = age / life, grow = Math.min(1, age / 0.08);
          o.scale.set(grow * (1 + k * 0.6), grow * (1 + k * 0.25), grow * (1 + k * 0.6));
          o.material.opacity = 0.95 * (1 - k) * (1 - k);
        });
      };
      beam(46, 7, 0xffffff, 0, 0.9); // the white core
      beam(40, 9.5, tint, 0.08, 1.1); // the victim's colour
      for (const col of [0xff4fd8, 0xffe14d, 0x4fd8ff, 0x7dff4f]) beam(26 + Math.random() * 14, 3 + Math.random() * 2, col, 0.45, 0.8 + Math.random() * 0.4); // rays fanning out
      const k = BLASTZONE.scale;
      fx.ring(p, 14 * k, 0xffffff, 0.5); fx.ring(p, 9 * k, tint, 0.7);
      fx.explosion(p, 6 * k);
      fx.spray(p, Math.round(80 * k), [0xffffff, 0xffe14d, 0xff4fd8, 0x4fd8ff, tint], 26 * Math.sqrt(k), 1.2, 0.3, 4, 1.5);
      sfx.boom(p); sfx.airhorn(true);
    };
    sfx.yeet(c.pos);
    return true;
  },
  ascend(c) {
    const ch = body(c);
    ch.arm.rotation.z = -1.3; ch.armL.rotation.z = 1.3; // t-pose to heaven
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.3, 120, 12, 1, true), own(new THREE.MeshBasicMaterial({ color: 0xfff6c0, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false })));
    beam.position.set(c.pos[0], c.pos[1] + 58, c.pos[2]);
    add(beam, 4.2, (o, dt, age) => { o.material.opacity = Math.min(0.55, age * 2) * Math.min(1, (4.2 - age) * 2); });
    const y0 = c.pos[1];
    add(ch.root, 4.2, (o, dt, age) => {
      o.position.y = y0 + Math.max(0, age - 0.4) * 2.2;
      o.rotation.y += dt * 1.5;
      if (Math.random() < 0.8) fx.spray([o.position.x + R(1), o.position.y + Math.random() * 2, o.position.z + R(1)], 1, [0xffffff, 0xfff2a0], 1, 0.9, 0.12, -1, 0);
    });
    sfx.choir(c.pos);
    return true;
  },
  duck(c) {
    const fy = floorAt(c.pos);
    const d = buildProjectile('duck');
    d.scale.setScalar(0.01);
    d.position.set(c.pos[0], fy, c.pos[2]);
    d.rotation.y = (c.yaw || 0) + Math.PI;
    const ch = body(c);
    const y0 = c.pos[1];
    add(ch.root, 0.9, (o, dt, age) => { o.position.y = y0 + age * 1.5; o.scale.setScalar(1.2 * Math.max(0.05, 1 - age / 0.9)); o.rotation.y += dt * 8; });
    add(d, 2.6, (o, dt, age) => {
      const k = age < 0.35 ? age / 0.35 : age > 2.1 ? Math.max(0.01, 1 - (age - 2.1) / 0.5) : 1;
      o.scale.setScalar(9 * k * (1 + Math.sin(age * 18) * 0.04));
      if (age > 0.8 && age < 0.85) sfx.squeak([o.position.x, o.position.y, o.position.z]);
    });
    sfx.squeak(c.pos); fx.dust([c.pos[0], fy, c.pos[2]], 20);
    return true;
  },
};

export const KILL_FX = Object.keys(EFFECTS);

// c = { pos, vel, yaw, color, look, name }. returns true when the effect replaced the gibs.
export function playKillFx(id, c) {
  const f = EFFECTS[id];
  if (!f) return false;
  try { return f({ vel: [0, 0, 0], yaw: 0, ...c }); } catch (e) { console.warn('kill fx', id, e); return false; }
}

export function updateKillFx(dt) {
  for (let i = live.length - 1; i >= 0; i--) {
    const l = live[i];
    l.age += dt;
    if (l.age >= l.life) { drop(l.obj); live.splice(i, 1); continue; }
    l.step(l.obj, dt, l.age);
  }
}
export function clearKillFx() { for (const l of live) drop(l.obj); live.length = 0; }
