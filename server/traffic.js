// Server-owned traffic: every car on every map is driven here so everyone sees the same ones (clients only draw them,
// see public/js/traffic.js). Cars follow their lane (shared/traffic.js), keep their distance, wait their turn at
// junctions, honk at people in the road and swerve a bit round them. Getting hit shoves you (fast ones kill), two cars
// meeting at speed both blow up, and a car shot or blasted enough blows up too. Knocked off its lane a car slides,
// tumbles and crashes into whatever's there.
import { CARS, CAR_IDS, CAR_COLORS, TRAFFIC_LEVELS, TRAFFIC_ORDER, trafficNet, trafficLevel, poseAt, carObb, obbOverlap, boxObb } from '../shared/traffic.js';
import { WEAPONS, fireRate } from '../shared/weapons.js';
import { query, raycast, PH } from '../shared/physics.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const rnd = (a, b) => a + Math.random() * (b - a);
const STEP = 1 / 30, SEND = 1 / 12;
// hits: below `bump` m/s it only shoves, from `kill` it's lethal (heavies kill sooner); boom: the crash explosion
export const CAR = { bump: 1.2, kill: 9, killHeavy: 7.5, crash: 3, wall: 8, boomR: 9, boomRBig: 12.5, boomDmg: 120, boomKb: 30, wreckMs: 14000, hitCd: 450 };
const F = { BRAKE: 1, HORN: 2, FREE: 4, SMOKE: 8, FIRE: 16, WRECK: 32, FLIP: 64, MUSIC: 128 };

function pickW(list) { // [[id, weight]]
  let t = 0; for (const [, w] of list) t += w;
  let r = Math.random() * t;
  for (const [id, w] of list) { r -= w; if (r <= 0) return id; }
  return list[list.length - 1][0];
}
const qBox = [];

export class Traffic {
  constructor(room) {
    this.room = room;
    this.cars = new Map(); this.nextId = 1;
    this.mapId = null; this.sel = null; this.acc = 0; this.sendAcc = 0; this.spawnAt = 0; this.jOcc = new Map();
    if (room.cfg.traffic == null) room.cfg.traffic = process.env.JF_TRAFFIC && Object.hasOwn(TRAFFIC_LEVELS, process.env.JF_TRAFFIC) ? process.env.JF_TRAFFIC : 'auto'; // test knob: JF_TRAFFIC=rush
  }
  get net() { return trafficNet(this.room.cfg.map); }
  level() { return trafficLevel(this.room.cfg.traffic, this.room.game, this.room.mode); }

  // ---------------------------------------------------------- settings: Match Settings > Traffic
  setCfg(m, changes) {
    if (typeof m.traffic !== 'string' || !Object.hasOwn(TRAFFIC_LEVELS, m.traffic) || m.traffic === this.room.cfg.traffic || this.room.mode === 'training') return;
    this.room.cfg.traffic = m.traffic;
    changes.push(`traffic → ${TRAFFIC_LEVELS[m.traffic].name}`);
  }

  clear() {
    for (const c of this.cars.values()) this.leaveJ(c);
    this.cars.clear(); this.jOcc.clear();
    this.room.broadcast({ t: 'trc' });
  }

  // ---------------------------------------------------------- spawning
  makeCar(e, s, net, L) {
    const ty = pickW(net.mix), T = CARS[ty], cfg = net.cfg;
    const v0 = e.v || cfg.v || [10, 15];
    const vmax = rnd(v0[0], v0[1]) * L.v * (T.wide ? 0.82 : ty === 'icecream' ? 0.7 : 1);
    const c = {
      id: this.nextId++, ty, T, col: (Math.random() * CAR_COLORS.length) | 0, e, s, lat: 0, latT: 0, v: vmax * 0.8, vmax, plan: [e],
      mode: 'drive', pos: [0, e.y, 0], h: 0, vel: [0, 0, 0], wy: 0, pitch: 0, roll: 0, wp: 0, wr: 0, hp: T.hp, by: 0, byT: 0,
      hornT: 0, hornCd: 0, brake: false, wait: 0, still: 0, grant: null, jIn: -1, boomAt: 0, wreckAt: 0, flip: false,
      reckless: !!net.grid && Math.random() < 0.06 * (L.reckless || 0), tail: Math.random() < 0.2, attn: process.env.JF_CAR_PHONE || Math.random() < 0.25 ? rnd(0.2, 0.35) : rnd(0.6, 1), pair: new Map(), born: now(), // attn: a quarter of them are on their phone
    };
    this.fillPlan(c);
    this.pose(c);
    this.cars.set(c.id, c);
    return c;
  }
  fillPlan(c) {
    while (c.plan.length < 3) {
      const last = c.plan[c.plan.length - 1];
      if (!last.next.length) break;
      c.plan.push(pickW(last.next.map((n) => [n, n.cls === 'turn' ? 0.55 : 1])));
    }
  }
  roomAt(x, z, gap) { for (const c of this.cars.values()) if (Math.hypot(c.pos[0] - x, c.pos[2] - z) < gap) return false; return true; }
  // fill the roads when traffic starts (nobody waits a minute for the first car to drive in from the horizon)
  populate(net, L, want) {
    const srcs = net.edges.filter((e) => e.src);
    for (let k = 0; k < want * 6 && this.cars.size < want; k++) {
      const e = srcs[(Math.random() * srcs.length) | 0], s = rnd(10, Math.max(11, e.len - 10)), p = poseAt(e, s);
      if (this.roomAt(p.x, p.z, 30)) this.makeCar(e, s, net, L);
    }
  }
  spawn(net, L, want) {
    const n = now();
    if (n < this.spawnAt) return;
    const ev = net.cfg.every || [3, 8];
    this.spawnAt = n + rnd(ev[0], ev[1]) * 1000 / Math.max(0.5, L.n);
    if (this.cars.size >= want) return;
    const routes = net.edges.filter((e) => e.route);
    if (routes.length) { // a lane's far end, out past the fog
      const e = routes[(Math.random() * routes.length) | 0];
      if (this.roomAt(e.pts[0][0], e.pts[0][1], 26)) this.makeCar(e, 0, net, L);
    } else this.populate(net, L, Math.min(want, this.cars.size + 1)); // city: somewhere quiet on the grid
  }

  // ---------------------------------------------------------- the loop
  tick(dt) {
    const net = this.net, L = this.level(), room = this.room;
    if (this.mapId !== room.cfg.map || this.sel !== L) { // new map or a new setting: start the roads over
      const first = this.mapId === null;
      this.mapId = room.cfg.map; this.sel = L;
      if (this.cars.size || !first) this.clear();
      if (net && L.n) this.populate(net, L, Math.round(net.cfg.n * L.n));
    }
    if (!net || !L.n) return;
    if (!room.players.size) return; // nobody watching: the world can wait
    this.acc = Math.min(this.acc + dt, 0.2);
    while (this.acc >= STEP) { this.acc -= STEP; this.step(STEP, net, L); }
    this.sendAcc += dt;
    if (this.sendAcc >= SEND) { this.sendAcc = 0; this.send(); }
  }
  step(dt, net, L) {
    const n = now();
    this.spawn(net, L, Math.round(net.cfg.n * L.n));
    for (const c of this.cars.values()) {
      if (c.boomAt && n >= c.boomAt) { c.boomAt = 0; this.boom(c, this.room.players.get(c.by) || null); }
      if (c.mode === 'drive') this.drive(c, dt, n, L);
      else this.free(c, dt, n);
      if (c.mode === 'gone') { this.leaveJ(c); this.cars.delete(c.id); }
    }
    if (process.env.JF_CAR_SWERVE) this.testSwerve(n);
    this.crashes(n);
    this.hits(n, L);
    this.balls(n);
  }

  // ---------------------------------------------------------- driving
  pose(c) {
    const p = poseAt(c.e, c.s, c.lat);
    c.pos[0] = p.x; c.pos[1] = p.y; c.pos[2] = p.z; c.h = p.h;
    c.vel[0] = Math.sin(c.h) * c.v; c.vel[1] = 0; c.vel[2] = Math.cos(c.h) * c.v;
  }
  // where the car's nose would be d metres further along its plan (null past the end of a lane that ends)
  ahead(c, d, out) {
    let s = c.s + d, i = 0;
    while (s > c.plan[i].len) { s -= c.plan[i].len; i++; if (i >= c.plan.length) return null; }
    poseAt(c.plan[i], s, i === 0 ? c.lat : 0, out); out.i = i;
    return out;
  }
  leaveJ(c) {
    if (c.jIn >= 0) { const o = this.jOcc.get(c.jIn); if (o) o.delete(c); c.jIn = -1; }
    c.grant = null;
  }
  jOk(c, m) { // may c drive into manoeuvre m? straight on alongside straight traffic on the same road, otherwise wait for empty
    const o = this.jOcc.get(m.j);
    if (!o || !o.size) return true;
    for (const q of o) if (q !== c && (m.cls === 'turn' || q.jCls !== m.cls)) return false;
    return true;
  }
  drive(c, dt, n, L) {
    const T = c.T, probe = 7 + c.v * 2.3;
    let gap = 1e9, vObs = 0, person = null, personLat = 0, stopLine = false;
    // look along the road ahead for cars, wrecks and people
    const P = {};
    for (let d = 0.4; d < probe; d += 1.25) {
      const a = this.ahead(c, T.L / 2 + d, P);
      if (!a) break;
      // a junction coming up: committed (granted) or wait at the line
      const m = c.plan[a.i];
      if (m.j >= 0 && c.grant !== m && c.jIn !== m.j) {
        if (c.reckless || c.wait > 7 || this.jOk(c, m)) { if (d < 22) { this.leaveJ(c); c.grant = m; c.jIn = m.j; c.jCls = m.cls; if (!this.jOcc.has(m.j)) this.jOcc.set(m.j, new Set()); this.jOcc.get(m.j).add(c); } }
        else if (d < gap) { gap = d; vObs = 0; stopLine = true; break; }
      }
      let hit = false;
      for (const q of this.cars.values()) {
        if (q === c || q.mode === 'gone' || Math.abs(q.pos[0] - a.x) > 8 || Math.abs(q.pos[2] - a.z) > 8 || Math.abs(q.pos[1] - c.pos[1]) > 3) continue;
        const lx = (a.x - q.pos[0]) * Math.sin(q.h) + (a.z - q.pos[2]) * Math.cos(q.h), lz = (a.x - q.pos[0]) * Math.cos(q.h) - (a.z - q.pos[2]) * Math.sin(q.h);
        const ox = Math.max(0, Math.abs(lx) - q.T.L / 2), oz = Math.max(0, Math.abs(lz) - q.T.W / 2);
        if (Math.hypot(ox, oz) < T.W / 2 + 0.35) { hit = true; vObs = Math.max(0, q.vel[0] * Math.sin(a.h) + q.vel[2] * Math.cos(a.h)); break; }
      }
      if (hit) { gap = d; break; }
      if (n < (c.rageT || 0)) continue; // had enough honking: going anyway
      for (const t of this.room.players.values()) { // people: only as far as this driver bothers to look
        if (!t.alive || d > probe * c.attn || t.pos[1] > c.pos[1] + T.H - 0.4 || t.pos[1] + PH.height < c.pos[1]) continue;
        const dx = t.pos[0] - a.x, dz = t.pos[2] - a.z;
        if (Math.abs(dx) > 3 || Math.abs(dz) > 3) continue;
        const lat = dx * Math.cos(a.h) - dz * Math.sin(a.h); // + = to the car's right
        if (Math.hypot(dx, dz) < T.W / 2 + 0.55) { hit = true; person = t; personLat = lat; break; }
      }
      if (hit) { gap = d; vObs = 0; break; }
    }
    // the speed that still stops in time (a tailgater thinks they brake better than they do)
    const b = c.tail ? 6.5 : 4.5, minGap = stopLine ? 0.2 : person ? 1.4 : c.tail ? 0.9 : 2.2;
    const allow = Math.sqrt(vObs * vObs + 2 * b * Math.max(0, gap - minGap));
    const want = Math.min(c.vmax, allow), v0 = c.v;
    if (want > c.v) c.v = Math.min(want, c.v + T.acc * dt);
    else c.v = Math.max(want, c.v - (person && c.attn < 0.4 ? 2.5 : gap < 6 ? 9.5 : 7) * dt); // looks up from the phone way too late
    if (gap < 0.3 && vObs < 0.5 && !person) c.v = Math.min(c.v, 0.3); // (people get hit instead: see hits)
    c.brake = c.v < v0 - 0.8 * dt || c.v < 0.3;
    // horn: someone in the road, or stuck behind something for a while
    c.still = c.v < 0.5 ? c.still + dt : 0;
    c.blockT = person && c.v < 1 ? (c.blockT || 0) + dt : 0;
    if (c.blockT > 4 + c.attn * 3) { c.rageT = n + 2500; c.blockT = 0; c.hornT = n + 1200; } // honked, waited, done waiting: MOVE
    c.wait = stopLine && c.v < 0.5 ? c.wait + dt : 0;
    if (c.hornCd > 0) c.hornCd -= dt;
    if (c.hornCd <= 0 && ((person && gap < probe * 0.8) || c.still > 3 + Math.random() * 3)) { c.hornT = n + (person ? 650 : 400); c.hornCd = person ? 1.4 : 3; if (!person) c.still = 0.5; }
    // swerve inside the lane's spare room away from whoever is in the way (never past it: the lane was checked that wide)
    c.latT = person && gap < 14 && c.e.slack ? -Math.sign(personLat || 1) * c.e.slack : 0;
    c.lat += Math.max(-1.6 * dt, Math.min(1.6 * dt, c.latT - c.lat));
    if (Math.abs(c.lat) > c.e.slack) c.lat = Math.sign(c.lat) * c.e.slack;
    // move along, onto the next bit of road
    c.s += c.v * dt;
    while (c.s > c.e.len) {
      if (c.plan.length < 2) { c.mode = 'gone'; return; } // the end of the road, out past the fog
      c.s -= c.e.len;
      if (c.e.j >= 0) this.leaveJ(c);
      c.plan.shift(); c.e = c.plan[0];
      if (c.lat && Math.abs(c.lat) > c.e.slack) c.lat = Math.sign(c.lat) * c.e.slack;
      this.fillPlan(c);
    }
    this.pose(c);
  }

  // knocked off the road: slides, spins, tumbles, lands. a car that comes to rest the right way up near a lane drives on
  unhook(c) {
    if (c.mode !== 'drive') return;
    this.leaveJ(c);
    c.mode = 'free';
    c.restT = 0;
  }
  free(c, dt, n) {
    const T = c.T, room = this.room;
    c.vel[1] -= 22 * dt;
    for (let k = 0; k < 3; k++) c.pos[k] += c.vel[k] * dt;
    c.h += c.wy * dt; c.pitch += c.wp * dt; c.roll += c.wr * dt;
    // the floor
    const fl = raycast([c.pos[0], c.pos[1] + 1.2, c.pos[2]], [0, -1, 0], 6, room.boxes);
    const fy = fl ? fl.point[1] : null;
    let ground = false;
    if (fy != null && c.pos[1] <= fy + 0.01 && c.vel[1] <= 0) {
      c.pos[1] = fy; ground = true;
      if (c.vel[1] < -7) { c.vel[1] *= -0.28; ground = false; } else c.vel[1] = 0;
      const k = Math.exp(-1.7 * dt); c.vel[0] *= k; c.vel[2] *= k; c.wy *= Math.exp(-2.4 * dt);
      // tumble settles onto its wheels or its roof, whichever it's closer to
      const settle = (a) => { const t = Math.round(a / Math.PI) * Math.PI; return a + (t - a) * Math.min(1, dt * 7); };
      c.pitch = settle(c.pitch); c.roll = settle(c.roll); c.wp *= 0.5; c.wr *= 0.5;
      c.flip = Math.abs(Math.cos(c.roll) * Math.cos(c.pitch)) < 0.5 || Math.cos(c.roll) * Math.cos(c.pitch) < 0;
    }
    // walls and props: pushed back out; hitting one hard enough is a crash
    const ob = carObb(c.pos[0], c.pos[2], c.h, T), r = T.L / 2 + 1;
    for (const b of query(room.boxes, c.pos[0] - r, c.pos[2] - r, c.pos[0] + r, c.pos[2] + r, qBox)) {
      if (b.max[1] <= c.pos[1] + 0.35 || b.min[1] >= c.pos[1] + T.H) continue;
      const bo = boxObb(b);
      if (!obbOverlap(ob, bo)) continue;
      // push out along x or z (the boxes are axis-aligned), whichever is the shallower way out
      const ex = Math.abs(ob.ux) * ob.hu + Math.abs(ob.uz) * ob.hv, ez = Math.abs(ob.uz) * ob.hu + Math.abs(ob.ux) * ob.hv;
      const px = Math.min(c.pos[0] + ex - b.min[0], b.max[0] - (c.pos[0] - ex)), pz = Math.min(c.pos[2] + ez - b.min[2], b.max[2] - (c.pos[2] - ez));
      const ax = px < pz ? 0 : 2, sgn = c.pos[ax] < (b.min[ax] + b.max[ax]) / 2 ? -1 : 1, pen = Math.min(px, pz);
      if (pen > 3) continue; // deep inside something big: let the floor deal with it
      c.pos[ax] += sgn * pen;
      const into = -sgn * c.vel[ax];
      if (into > 0) {
        if (into > CAR.wall && c.mode === 'free') { this.boom(c, room.players.get(c.by) || null); return; }
        c.vel[ax] = sgn * into * 0.3; c.wy += (Math.random() - 0.5) * into * 0.4;
      }
    }
    if (c.pos[1] < Math.min(room.map.killY, c.e.y - 30)) { c.mode = 'gone'; return; } // (the city streets are below the kill line)
    const sp = Math.hypot(c.vel[0], c.vel[2]);
    if (c.mode === 'wreck') { if (n > c.wreckAt + CAR.wreckMs) c.mode = 'gone'; return; }
    c.restT = ground && sp < 0.7 ? c.restT + dt : 0;
    if (c.restT > 1.2) {
      if (!c.flip && c.hp > c.T.hp * 0.3 && this.relane(c)) return; // shakes it off and drives on
      if (!c.boomAt) { c.boomAt = n + rnd(4000, 6500); c.hp = Math.min(c.hp, c.T.hp * 0.2); } // totalled: smoke, fire, boom
    }
  }
  relane(c) {
    const net = this.net;
    if (!net) return false;
    let best = null, bd = 2.5;
    for (const e of net.edges) {
      for (let i = 1; i < e.pts.length; i++) {
        const [ax, az] = e.pts[i - 1], [bx, bz] = e.pts[i], l = Math.hypot(bx - ax, bz - az) || 1;
        const ux = (bx - ax) / l, uz = (bz - az) / l, t = Math.max(0, Math.min(l, (c.pos[0] - ax) * ux + (c.pos[2] - az) * uz));
        const d = Math.hypot(ax + ux * t - c.pos[0], az + uz * t - c.pos[2]);
        if (d >= bd || Math.abs(c.pos[1] - e.y) > 0.6) continue;
        let dh = Math.atan2(ux, uz) - c.h; while (dh > Math.PI) dh -= Math.PI * 2; while (dh < -Math.PI) dh += Math.PI * 2;
        if (Math.abs(dh) > 0.9) continue;
        best = { e, s: e.cum[i - 1] + t }; bd = d;
      }
    }
    if (!best) return false;
    Object.assign(c, { mode: 'drive', e: best.e, s: best.s, lat: 0, latT: 0, v: 0, plan: [best.e], wy: 0, wp: 0, wr: 0, pitch: 0, roll: 0, grant: null });
    this.fillPlan(c);
    return true;
  }
  // a shove from a blast, a ball or a big gun. big enough and the car leaves its lane
  shove(c, imp, spin = 0) {
    if (c.mode === 'gone') return;
    const m = c.T.mass, dv = imp.map((x) => x / m);
    if (c.mode === 'drive') {
      if (Math.hypot(dv[0], dv[2]) < 2.2 && dv[1] < 3) { c.v = Math.max(0, c.v - Math.hypot(dv[0], dv[2]) * 0.5); return; } // rocks on its springs
      this.unhook(c);
    }
    for (let k = 0; k < 3; k++) c.vel[k] += dv[k];
    c.wy += (Math.random() - 0.5) * (spin + Math.hypot(dv[0], dv[2])) * 0.35;
    if (dv[1] > 4) { c.wp += (Math.random() - 0.5) * dv[1] * 0.9; c.wr += (Math.random() - 0.5) * dv[1] * 1.2; }
  }

  // test knob JF_CAR_SWERVE=<seconds>: every so often the two oncoming cars closest to a person swerve into each other
  testSwerve(n) {
    if (n < (this.swerveAt || 0)) return;
    const who = [...this.room.players.values()].find((p) => !p.isBot && p.alive);
    if (!who) return;
    let best = null, bd = 45;
    const list = [...this.cars.values()].filter((c) => c.mode === 'drive' && c.v > 5);
    for (const a of list) for (const b of list) {
      if (a === b || Math.sin(a.h) * Math.sin(b.h) + Math.cos(a.h) * Math.cos(b.h) > -0.7) continue;
      const d = Math.hypot(a.pos[0] - b.pos[0], a.pos[2] - b.pos[2]), dw = Math.hypot(a.pos[0] - who.pos[0], a.pos[2] - who.pos[2]);
      const closing = (b.pos[0] - a.pos[0]) * Math.sin(a.h) + (b.pos[2] - a.pos[2]) * Math.cos(a.h) > 0;
      if (d > 9 && d < 22 && closing && dw < bd) { bd = dw; best = [a, b]; }
    }
    if (!best) return;
    this.swerveAt = n + Number(process.env.JF_CAR_SWERVE) * 1000;
    const [a, b] = best, dx = b.pos[0] - a.pos[0], dz = b.pos[2] - a.pos[2], l = Math.hypot(dx, dz);
    this.unhook(a); a.vel[0] = (dx / l) * a.v * 1.1; a.vel[2] = (dz / l) * a.v * 1.1; a.wy = 0.6;
  }

  // ---------------------------------------------------------- crashes: two cars meeting at speed both blow up
  crashes(n) {
    const list = [...this.cars.values()].filter((c) => c.mode !== 'gone');
    for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
      const a = list[i], b = list[j];
      if (Math.abs(a.pos[0] - b.pos[0]) > 13 || Math.abs(a.pos[2] - b.pos[2]) > 13 || Math.abs(a.pos[1] - b.pos[1]) > Math.max(a.T.H, b.T.H)) continue;
      if (!obbOverlap(carObb(a.pos[0], a.pos[2], a.h, a.T), carObb(b.pos[0], b.pos[2], b.h, b.T))) continue;
      const rel = Math.hypot(a.vel[0] - b.vel[0], a.vel[1] - b.vel[1], a.vel[2] - b.vel[2]);
      if (rel > CAR.crash && !(a.mode === 'wreck' && b.mode === 'wreck')) {
        const by = this.room.players.get(a.byT > b.byT ? a.by : b.by) || null; // whoever shoved or shot one of them last
        if (a.mode !== 'wreck') this.boom(a, by, b);
        if (b.mode !== 'wreck') this.boom(b, by, a);
        if (a.mode === 'wreck' && b.mode === 'wreck') this.room.broadcast({ t: 'carcrash', a: a.id, b: b.id, p: [(a.pos[0] + b.pos[0]) / 2, a.pos[1] + 1, (a.pos[2] + b.pos[2]) / 2].map(r2), s: Math.round(rel) });
      } else { // a nudge: the free one gets pushed off, drivers just stop (their lookahead already slowed them)
        const dx = b.pos[0] - a.pos[0], dz = b.pos[2] - a.pos[2], l = Math.hypot(dx, dz) || 1;
        for (const [c, s] of [[a, -1], [b, 1]]) if (c.mode !== 'drive') { c.pos[0] += (dx / l) * s * 0.05; c.pos[2] += (dz / l) * s * 0.05; c.vel[0] += (dx / l) * s * 0.5; c.vel[2] += (dz / l) * s * 0.5; }
      }
    }
  }

  // ---------------------------------------------------------- BOOM
  boom(c, by, other) {
    if (c.mode === 'gone' || c.mode === 'wreck') return;
    const room = this.room, n = now(), T = c.T;
    const big = T.mass >= 3, R = big ? CAR.boomRBig : CAR.boomR;
    const at = [c.pos[0], c.pos[1] + T.H * 0.45, c.pos[2]];
    if (by && !room.players.has(by.id)) by = null;
    if (by && n - c.byT > 10000) by = null; // shot it ages ago: nobody's car bomb
    this.unhook(c);
    c.mode = 'wreck'; c.wreckAt = n; c.hp = 0; c.boomAt = 0;
    c.vel[1] = rnd(5, 8) / Math.sqrt(T.mass); c.wp = rnd(-2, 2); c.wr = rnd(-3, 3); c.wy += rnd(-2, 2); // the bang throws it about
    room.broadcast({ t: 'carx', id: c.id, p: at.map(r2), r: R, ty: c.ty, by: by ? by.id : 0, o: other ? other.id : 0 });
    // people: hurt and thrown, not through walls. whoever shot/shoved it gets the kills
    for (const t of room.players.values()) {
      if (!t.alive) continue;
      const tc = [t.pos[0], t.pos[1] + 0.9, t.pos[2]], to = [tc[0] - at[0], tc[1] - at[1], tc[2] - at[2]], d = Math.hypot(...to);
      if (d > R) continue;
      if (d > 0.5 && raycast(at, to.map((x) => x / d), d - 0.3, room.boxes)) continue;
      const f = 1 - d / R, hl = Math.hypot(to[0], to[2]) || 1, k = CAR.boomKb * (0.4 + 0.6 * f) * (big ? 1.2 : 1);
      const kb = [to[0] / hl * k, 7 + 9 * f, to[2] / hl * k], dmg = CAR.boomDmg * (big ? 1.25 : 1) * (0.25 + 0.75 * f);
      const att = by && by !== t ? by : null;
      if (dmg >= t.hp && !t.isBot) t.vel = kb.slice(); // the gibs fly the way the blast threw them
      room.hurt(t, att, 'carboom', dmg, kb, { from: at });
    }
    // other cars: shoved off the road, hurt, and the ones that had enough go up a moment later (chain reactions)
    for (const q of this.cars.values()) {
      if (q === c || q.mode === 'gone') continue;
      const to = [q.pos[0] - at[0], q.pos[1] + 0.8 - at[1], q.pos[2] - at[2]], d = Math.hypot(...to);
      if (d > R * 1.1) continue;
      const f = 1 - d / (R * 1.1), hl = Math.hypot(to[0], to[2]) || 1;
      this.shove(q, [to[0] / hl * 16 * f, 6 + 8 * f, to[2] / hl * 16 * f], 4);
      if (q.mode === 'wreck') continue;
      q.hp -= 260 * f + 40;
      if (by && (!q.by || n - q.byT > 3000)) { q.by = by.id; q.byT = n; }
      if (q.hp <= 0 && !q.boomAt) q.boomAt = n + rnd(180, 520);
    }
  }

  // ---------------------------------------------------------- hitting people
  hits(n, L) {
    const room = this.room;
    for (const c of this.cars.values()) {
      if (c.mode === 'gone') continue;
      const sp = Math.hypot(c.vel[0], c.vel[1], c.vel[2]);
      if (sp < 0.4) continue;
      const T = c.T, sn = Math.sin(c.h), cs = Math.cos(c.h), heavy = T.mass >= 3;
      for (const t of room.players.values()) {
        if (!t.alive || (t.isBot && t.ai && t.ai.dummy && t.ai.dummy.move)) continue;
        const dx = t.pos[0] - c.pos[0], dz = t.pos[2] - c.pos[2];
        if (Math.abs(dx) > T.L / 2 + 1.5 || Math.abs(dz) > T.L / 2 + 1.5) continue;
        const roof = c.pos[1] + T.H * (c.flip ? 0.7 : 1);
        if (t.pos[1] >= roof - 0.45 || t.pos[1] + PH.height < c.pos[1] + 0.15) continue; // car surfing (or under it, somehow)
        const lu = dx * sn + dz * cs, lv = dx * cs - dz * sn, R = PH.halfW + 0.05;
        const ou = Math.abs(lu) - T.L / 2, ov = Math.abs(lv) - T.W / 2;
        if (ou > R || ov > R) continue;
        // which face they're against, and how hard the car is coming at them through it
        const nrm = ou > ov ? [sn * Math.sign(lu), cs * Math.sign(lu)] : [cs * Math.sign(lv), -sn * Math.sign(lv)];
        const impact = (c.vel[0] - t.vel[0]) * nrm[0] + (c.vel[2] - t.vel[2]) * nrm[1];
        if (!this.pairOk(c, t, n)) continue;
        if (impact < CAR.bump) { // just leaning on it, or it rolled into them: out of the way you go
          room.knock(t, [nrm[0] * (2.5 + Math.max(0, impact) * 2), 1.2, nrm[1] * (2.5 + Math.max(0, impact) * 2)], 'car');
          continue;
        }
        const fwd = [c.vel[0] / (sp || 1), c.vel[2] / (sp || 1)];
        const k = Math.min(42, impact * 1.45 + 4) * (heavy ? 1.25 : 1);
        const kb = [nrm[0] * k + fwd[0] * impact * 0.35, Math.min(15, 3.5 + impact * 0.6), nrm[1] * k + fwd[1] * impact * 0.35];
        const protectedT = n - (t.spawnT || 0) < 1500 && !t.isBot;
        let dmg = impact < 5 ? 5 + impact * 3 : 20 + (impact - 5) * 9;
        if (heavy) dmg *= 1.3;
        const lethal = L.lethal && impact >= (heavy ? CAR.killHeavy : CAR.kill);
        if (lethal) dmg = Math.max(dmg, t.hp + 50);
        if (!L.lethal) dmg = Math.min(dmg, 30);
        if (protectedT) dmg = 0;
        room.broadcast({ t: 'carhit', id: c.id, to: t.id, s: Math.round(impact * 3.6), ty: c.ty, p: [t.pos[0], t.pos[1] + 1, t.pos[2]].map(r2), ko: dmg >= t.hp ? 1 : undefined });
        if (dmg >= t.hp && !t.isBot) t.vel = kb.slice();
        if (dmg > 0) room.hurt(t, null, 'car', dmg, kb, { from: c.pos.slice() });
        else room.knock(t, kb, 'car');
        // the car feels it a bit too
        c.hornT = n + 500;
        if (c.mode === 'drive') c.v *= heavy ? 0.95 : 0.8;
        else { c.vel[0] *= 0.85; c.vel[2] *= 0.85; }
      }
    }
  }
  pairOk(c, t, n) {
    if (n - (c.pair.get(t.id) || 0) < CAR.hitCd) return false;
    c.pair.set(t.id, n);
    return true;
  }

  // ---------------------------------------------------------- wrecking balls ram cars too
  balls(n) {
    const room = this.room;
    for (const p of room.players.values()) {
      if (!room.isBall(p, n)) continue;
      const sp = Math.hypot(p.vel[0], p.vel[2]);
      if (sp < 6) continue;
      for (const c of this.cars.values()) {
        if (c.mode === 'gone' || Math.hypot(c.pos[0] - p.pos[0], c.pos[2] - p.pos[2]) > c.T.L / 2 + 2.2 || Math.abs(c.pos[1] - p.pos[1]) > 3) continue;
        if (!obbOverlap(carObb(c.pos[0], c.pos[2], c.h, c.T, 1.2), { x: p.pos[0], z: p.pos[2], ux: 1, uz: 0, hu: 0.1, hv: 0.1 })) continue;
        if (n - (c.pair.get('ball' + p.id) || 0) < 600) continue;
        c.pair.set('ball' + p.id, n);
        c.by = p.id; c.byT = n;
        this.shove(c, [p.vel[0] * 1.1, 4 + sp * 0.25, p.vel[2] * 1.1], 6);
        this.damage(c, sp * 6, p);
        room.broadcast({ t: 'fx', k: 'ram', id: p.id, to: 0, p: c.pos.map(r2), s: Math.round(sp) });
      }
    }
  }

  // ---------------------------------------------------------- shooting cars
  damage(c, amt, by) {
    if (c.mode === 'gone' || c.mode === 'wreck' || !(amt > 0)) return;
    c.hp -= amt;
    if (by) { c.by = by.id; c.byT = now(); }
    if (c.hp <= 0 && !c.boomAt) this.boom(c, by);
    else if (c.hp < c.T.hp * 0.25 && !c.boomAt) c.boomAt = now() + rnd(2200, 4000); // on fire: it's going up in a moment
  }
  // 'car' { id, w, n, d }: a bullet / swing from p hit car id. checked like any hit: holding that weapon, its fire rate,
  // in range of where the server has the car, nothing solid in between
  onHit(p, m) {
    const c = this.cars.get(m.id), w = typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) && WEAPONS[m.w];
    if (!c || !w || !p.alive || c.mode === 'gone' || c.mode === 'wreck' || p.w !== m.w || this.room.isBall(p)) return;
    if (w.kind !== 'hitscan' && w.kind !== 'melee') return;
    if (!this.room.allowed(p, m.w)) return;
    const n = now(), key = 'car' + m.w, iv = w.kind === 'hitscan' ? (1000 / fireRate(w, p.hp)) * 0.6 : (w.cd || 0.4) * 750;
    p.carT ||= {};
    if (n - (p.carT[key] || 0) < iv) return;
    p.carT[key] = n;
    const e = [p.pos[0], p.pos[1] + PH.eye, p.pos[2]], to = [c.pos[0] - e[0], c.pos[1] + c.T.H / 2 - e[1], c.pos[2] - e[2]], dist = Math.hypot(...to);
    const reach = (w.kind === 'melee' ? (w.range || 2) + 1.5 : w.range || 200) + c.T.L / 2 + c.v * 0.25 + 2;
    if (dist > reach) return;
    const wall = raycast(e, to.map((x) => x / dist), dist, this.room.boxes);
    if (wall && wall.t < dist - c.T.L / 2 - 1) return;
    const pellets = Math.max(1, Math.min(w.pellets || 1, Math.floor(Number(m.n) || 1)));
    const dmg = (w.dmg || 10) * pellets * (w.kind === 'melee' ? 1.5 : 1);
    const d = Array.isArray(m.d) && m.d.length === 3 && m.d.every(Number.isFinite) ? m.d : to.map((x) => x / dist);
    const dl = Math.hypot(...d) || 1, kb = (w.kb || 0) * pellets + (w.kind === 'melee' ? 3 : 0);
    if (kb > 0) this.shove(c, [(d[0] / dl) * kb * 0.6, Math.max(0, (d[1] / dl) * kb * 0.3) + kb * 0.08, (d[2] / dl) * kb * 0.6]);
    if (w.kind === 'melee') c.hornT = n + 450; // HONK. how rude
    this.damage(c, dmg, p);
  }
  // explosions (frags, chickens, the bomb, exploding arrows) shove and hurt cars in range
  blast(at, R, dmg, kb, owner) {
    const n = now();
    for (const c of this.cars.values()) {
      if (c.mode === 'gone') continue;
      const to = [c.pos[0] - at[0], c.pos[1] + 0.8 - at[1], c.pos[2] - at[2]], d = Math.hypot(...to) - c.T.W / 2;
      if (d > R) continue;
      const f = 1 - Math.max(0, d) / R, hl = Math.hypot(to[0], to[2]) || 1, k = (kb || 20) * (0.4 + 0.6 * f);
      if (owner) { c.by = owner.id; c.byT = n; }
      this.shove(c, [to[0] / hl * k, 3 + 7 * f, to[2] / hl * k], 3);
      this.damage(c, (dmg || 60) * (0.4 + 0.6 * f) * 1.4, owner);
    }
  }
  // flying stuff (chickens, arrows, bananas, bowling balls, cards...) hitting a car on the way: true = used up
  projHit(pr, prev, owner) {
    if (!this.cars.size) return false;
    const w = WEAPONS[pr.k];
    for (const c of this.cars.values()) {
      if (c.mode === 'gone' || Math.abs(c.pos[0] - pr.p[0]) > c.T.L || Math.abs(c.pos[2] - pr.p[2]) > c.T.L) continue;
      if (pr.p[1] < c.pos[1] + 0.2 || pr.p[1] > c.pos[1] + c.T.H) continue;
      if (!obbOverlap(carObb(c.pos[0], c.pos[2], c.h, c.T, (pr.r || 0.1)), { x: pr.p[0], z: pr.p[2], ux: 1, uz: 0, hu: 0.01, hv: 0.01 })) continue;
      const room = this.room;
      if (pr.k === 'chicken') { room.projectiles.delete(pr.id); room.explode(pr); return true; } // explode() blasts the car too
      const d = Math.hypot(...pr.v) || 1;
      this.shove(c, pr.v.map((x) => (x / d) * (w.kb || 4) * 0.5));
      if (pr.k === 'bow' || pr.k === 'card') { if (pr.tip !== 'explosion') this.damage(c, pr.k === 'bow' ? 30 : 9, owner || null); room.arrowHit(pr, owner, null, null); return true; } // (an exploding tip blasts it instead)
      this.damage(c, (w.dmg || 10) * (pr.k === 'bowling' ? 2 : 1), owner || null);
      room.removeProj(pr, { b: 1 });
      return true;
    }
    return false;
  }

  // ---------------------------------------------------------- bots look both ways (mostly)
  botYield(b, think) {
    if (!this.cars.size || !b.alive || b.ai.dummy) return;
    const n = now(), ai = b.ai;
    if (n > (ai.carRoll || 0)) { ai.carRoll = n + 500 + Math.random() * 400; ai.carLook = Math.random() < ({ easy: 0.6, normal: 0.8, hard: 0.93 }[ai.diff] || 0.8); }
    if (!ai.carLook) return; // not looking. good luck
    for (const c of this.cars.values()) {
      if (c.mode === 'gone' || c.mode === 'wreck' || Math.abs(c.pos[1] - b.pos[1]) > 2.5) continue;
      const sp = Math.hypot(c.vel[0], c.vel[2]);
      if (c.mode === 'free' && sp < 1.5) continue;
      const fx = c.mode === 'drive' ? Math.sin(c.h) : c.vel[0] / sp, fz = c.mode === 'drive' ? Math.cos(c.h) : c.vel[2] / sp, reach = c.T.L / 2 + Math.max(sp, 3) * 2.6 + 4; // (a car waiting for you to move counts)
      const lane = (x, z) => { const dx = x - c.pos[0], dz = z - c.pos[2], u = dx * fx + dz * fz, v = dx * fz - dz * fx; return u > -c.T.L / 2 - 0.5 && u < reach && Math.abs(v) < c.T.W / 2 + 1.3 ? v || 0.01 : 0; };
      const now0 = lane(b.pos[0], b.pos[2]);
      if (now0) { // in the road with a car coming: get off it, sideways, away from the middle of the car's path
        const s = Math.sign(now0);
        think.wx = fz * s; think.wz = -fx * s;
        if (Math.random() < 0.02) think.jump = true;
        return;
      }
      if ((think.wx || think.wz) && lane(b.pos[0] + think.wx * 1.6, b.pos[2] + think.wz * 1.6)) { think.wx = 0; think.wz = 0; return; } // wait at the kerb
    }
  }

  // ---------------------------------------------------------- what everyone sees
  send() {
    const room = this.room, n = now(), rows = [];
    for (const c of this.cars.values()) {
      let f = 0;
      if (c.brake) f |= F.BRAKE;
      if (n < c.hornT) f |= F.HORN;
      if (c.mode !== 'drive') f |= F.FREE;
      if (c.mode === 'wreck') f |= F.WRECK | F.FIRE;
      else if (c.hp < c.T.hp * 0.25 || c.boomAt) f |= F.FIRE | F.SMOKE;
      else if (c.hp < c.T.hp * 0.55) f |= F.SMOKE;
      if (c.flip) f |= F.FLIP;
      rows.push([c.id, CAR_IDS.indexOf(c.ty) * 16 + c.col, r2(c.pos[0]), r2(c.pos[1]), r2(c.pos[2]), r2(c.h), r2(c.mode === 'drive' ? c.v : Math.hypot(c.vel[0], c.vel[2])), f, r2(c.pitch), r2(c.roll)]);
    }
    if (!rows.length && !this.sentAny) return;
    this.sentAny = rows.length > 0;
    room.broadcast({ t: 'tr', s: n, c: rows });
  }
}
export { TRAFFIC_ORDER, TRAFFIC_LEVELS };
