// New gear, server half: the Big Laser Pointer (charge beam primary), the Instant Camera (photo portals), the Pop Quiz
// (thrown calculator: answer or die) and the Night Vision Goggles (flash everyone you can see). Mixed into Room by
// installGear: every method here runs as a Room method (this = the room). The server owns all of it: charge times,
// beam hits, where photos were taken, who walks into a frame, the questions and their answers, who a flash reaches.
import { WEAPONS, ITEMS, FLAGS, BOT_DIFF, PHOTO, QUIZ, NVG } from '../shared/weapons.js';

let H; // helpers from server.js (now, send, raycast...)
const L = WEAPONS.laser;
const lerp = (ab, k) => ab[0] + (ab[1] - ab[0]) * k;
const ri = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
const yawOf = (d) => Math.atan2(-d[0], -d[2]);
const GEAR = ['nvg', 'quiz', 'camera', 'quiz', 'nvg', 'radar', 'radar', 'laptop', 'laptop', null, null, null]; // what a bot carries (lots carry nothing; radar = the speed trap, server/secondaries.js)

// ---------------------------------------------------------------- pop quiz questions (the answer never leaves the server)
// one in a few is a two-step one; numbers stay small enough to do in your head in 6 s while panicking
export function makeQuestion() {
  const kind = ri(0, 9);
  let q, a;
  if (kind <= 1) { const x = ri(12, 79), y = ri(11, 49); q = `${x} + ${y}`; a = x + y; }
  else if (kind === 2) { const x = ri(40, 99), y = ri(11, x - 5); q = `${x} − ${y}`; a = x - y; }
  else if (kind <= 4) { const x = ri(3, 12), y = ri(3, 12); q = `${x} × ${y}`; a = x * y; }
  else if (kind === 5) { const y = ri(2, 9), a0 = ri(3, 12); q = `${a0 * y} ÷ ${y}`; a = a0; }
  else if (kind === 6) { const x = ri(2, 9), y = ri(2, 9), z = ri(2, 20); q = `${x} × ${y} + ${z}`; a = x * y + z; }
  else if (kind === 7) { const x = ri(2, 13); q = `${x}²`; a = x * x; }
  else if (kind === 8) { const x = ri(10, 60) * 2; q = `half of ${x}`; a = x / 2; }
  else { const x = ri(20, 60), y = ri(5, 19), z = ri(2, 15); q = `${x} − ${y} + ${z}`; a = x - y + z; }
  // wrong answers that look right: off by a bit, off by ten, digits swapped
  const opts = new Set([a]);
  const tries = [a + 1, a - 1, a + 2, a - 2, a + 10, a - 10, Number(String(a).split('').reverse().join('')), a + ri(3, 9), a - ri(3, 9)];
  while (opts.size < 4) {
    const v = tries.length ? tries.splice(ri(0, tries.length - 1), 1)[0] : a + ri(-20, 20);
    if (Number.isInteger(v) && v >= 0) opts.add(v);
  }
  const list = [...opts].sort(() => Math.random() - 0.5);
  return { q, a: list, ok: list.indexOf(a) };
}

export function installGear(Room, helpers) {
  H = helpers;
  Object.assign(Room.prototype, gear);
}

const gear = {
  // ---------------------------------------------------------------- Big Laser Pointer
  // press: { w: 'laser', ch: 1 } starts the charge (its time is ours). release: { w: 'laser' } fires whatever we timed
  laserFire(p, m) {
    const n = H.now();
    if (m.ch === 0) { p.laserT = 0; return; } // switched away mid-charge
    if (m.ch === 1) { if (!p.beam && n >= (p.lastFire.laser || 0)) p.laserT = n; return; }
    if (!p.laserT || p.beam || n < (p.lastFire.laser || 0)) { p.laserT = 0; return; }
    // only time spent actually holding it counts (your snapshots say what's in your hands; bots always hold theirs)
    const held = p.isBot || p.w === 'laser' ? (n - p.laserT) / 1000 : 0, k = Math.max(0, Math.min(1, (held - L.tap) / (L.charge - L.tap)));
    p.laserT = 0;
    const dur = lerp(L.dur, k);
    p.beam = { k, until: n + dur * 1000, next: 0 };
    p.lastFire.laser = n + (dur + L.cd) * 1000;
    this.broadcast({ t: 'fx', k: 'beam', id: p.id, c: H.r2(k), dur: H.r2(dur) }, p.isBot ? undefined : p.id);
  },
  // the beam follows where you look for as long as it lasts, goes through everyone in it, stops at walls
  tickBeams(n) {
    for (const p of this.players.values()) {
      const b = p.beam;
      if (!b) continue;
      if (!p.alive || n > b.until || p.trap || p.quiz) { p.beam = null; continue; }
      if (n < b.next) continue;
      b.next = n + L.tick * 1000;
      const e = H.eyeOf(p), d = H.lookOf(p);
      const wall = H.raycast(e, d, L.range, this.boxes), len = wall ? wall.t : L.range;
      const end = [e[0] + d[0] * len, e[1] + d[1] * len, e[2] + d[2] * len];
      const kb = lerp(L.kb, b.k), dmg = lerp(L.dmg, b.k);
      for (const v of this.sweep(e, end, lerp(L.r, b.k), (t) => t === p || this.friendly(p, t))) {
        this.hurt(v.t, p, 'laser', dmg, [d[0] * kb, d[1] * kb + L.kbUp, d[2] * kb]);
      }
    }
  },
  // bots: start charging, let go 0.9-1.4 s later (botFire calls back in once nextShot comes round)
  botLaser(b) {
    const n = H.now();
    if (!b.laserT) { if (n >= (b.lastFire.laser || 0)) { this.laserFire(b, { ch: 1 }); b.ai.nextShot = n + 900 + Math.random() * 500; } return; }
    this.laserFire(b, {});
    b.ai.nextShot = n + (L.cd + 0.6) * 1000 + Math.random() * 600;
  },

  // ---------------------------------------------------------------- items that aren't the usual "spend a charge" (G)
  // true = handled here (photo snap, a goggles flash with no goggles on). the camera's first press is free
  gearItem(p, m) {
    if (m.i !== 'camera' && m.i !== 'nvg') return false;
    if (m.i !== p.item || this.modeWeapon(p) || (this.chaosKit && this.chaosKit.noItem)) return false; // the normal path says no
    if (m.i === 'nvg') { if (p.nvOn) return false; this.sendIc(p); return true; } // flash only with them on
    if (p.photo) return false; // second press: print (costs the charge)
    const n = H.now();
    if (n - (p.itemT || 0) < 400 || p.trap || p.quiz) return true;
    p.itemT = n;
    this.snapPhoto(p, H.norm(H.vec3(m.d)) || H.lookOf(p));
    return true;
  },
  // after the normal path spent a charge: print the photo, or flash
  gearUse(p, m, o, d) {
    if (m.i === 'camera') { this.printPhoto(p, d); return true; }
    if (m.i === 'nvg') { this.nvFlash(p, d); return true; }
    if (m.i === 'quiz') { // a calculator, thrown a bit softer than a frag
      const w = WEAPONS.calc;
      const pr = this.makeProj(p, 'calc', [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7],
        [d[0] * w.speed + p.vel[0] * 0.3, d[1] * w.speed + 2 + p.vel[1] * 0.3, d[2] * w.speed + p.vel[2] * 0.3]);
      pr.born = H.now();
      return true;
    }
    return false;
  },

  // ---------------------------------------------------------------- Instant Camera
  // a photo remembers where you really stood (our copy of your position, dropped onto the floor under you) and which
  // way you faced. no floor under you (mid-air over the void, off the map) = no photo
  snapPhoto(p, d) {
    const fl = H.raycast([p.pos[0], p.pos[1] + 0.3, p.pos[2]], [0, -1, 0], PHOTO.drop + 0.3, this.boxes);
    if (!fl || fl.normal[1] < 0.5 || fl.point[1] < this.map.killY + 2) { H.send(p, { t: 'photo!', why: 'nothing to stand on there' }); return; }
    const pos = [p.pos[0], fl.point[1] + 0.02, p.pos[2]].map(H.r2);
    p.photo = { n: (this.nextPhoto = (this.nextPhoto || 0) + 1), pos, y: H.r2(yawOf(d)), x: H.r2(Math.asin(Math.max(-1, Math.min(1, d[1])))) };
    this.broadcast({ t: 'snap', id: p.id, n: p.photo.n, p: pos, y: p.photo.y, x: p.photo.x });
  },
  // the frame stands up in front of you facing you (pushed back off walls, on the floor). one frame each: a new one
  // replaces your old one
  printPhoto(p, d) {
    const ph = p.photo;
    if (!ph) return;
    p.photo = null;
    const f = H.norm([d[0], 0, d[2]]) || [-Math.sin(p.yaw), 0, -Math.cos(p.yaw)];
    const e = H.eyeOf(p);
    const wall = H.raycast([e[0], p.pos[1] + 1, e[2]], f, PHOTO.at + 0.6, this.boxes);
    const at = wall ? Math.max(0.6, wall.t - 0.6) : PHOTO.at;
    const base = [p.pos[0] + f[0] * at, p.pos[1], p.pos[2] + f[2] * at];
    const fl = H.raycast([base[0], base[1] + 1.2, base[2]], [0, -1, 0], 3.5, this.boxes);
    if (fl) base[1] = fl.point[1];
    this.frames ||= new Map();
    for (const fr of this.frames.values()) if (fr.o === p.id) this.dropFrame(fr);
    const fr = { id: (this.nextFrame = (this.nextFrame || 0) + 1), o: p.id, p: base.map(H.r2), y: H.r2(yawOf([-f[0], 0, -f[2]])), n: [-f[0], -f[2]],
      dest: ph, until: H.now() + PHOTO.life * 1000, used: new Map(), last: new Map() };
    this.frames.set(fr.id, fr);
    this.broadcast(this.frameMsg(fr));
  },
  frameMsg(fr) { return { t: 'frame', id: fr.id, o: fr.o, p: fr.p, y: fr.y, ph: { n: fr.dest.n, p: fr.dest.pos, y: fr.dest.y, x: fr.dest.x }, left: Math.max(0, fr.until - H.now()) }; },
  dropFrame(fr, why) { this.frames.delete(fr.id); this.broadcast({ t: 'framex', id: fr.id, why }); },
  // anyone walking into the opening goes through, from either side. a fast mover is caught by crossing the plane
  // between two ticks too
  tickFrames(n) {
    if (!this.frames || !this.frames.size) return;
    for (const fr of [...this.frames.values()]) {
      if (n >= fr.until) { this.dropFrame(fr, 'time'); continue; }
      const nx = fr.n[0], nz = fr.n[1], sx = -nz, sz = nx;
      for (const t of this.players.values()) {
        if (!t.alive || t.trap || t.quiz || (t.isBot && t.ai && t.ai.dummy)) continue;
        const rx = t.pos[0] - fr.p[0], ry = t.pos[1] - fr.p[1], rz = t.pos[2] - fr.p[2];
        const dn = rx * nx + rz * nz, lat = rx * sx + rz * sz, was = fr.last.get(t.id);
        fr.last.set(t.id, [dn, lat]);
        if (ry < -0.8 || ry > PHOTO.h - 0.6) continue;
        // inside the opening now, or went through it since last tick: the crossing point has to be in the opening too,
        // and close (a respawn or another teleport that jumps across the plane far away is not walking through it)
        const inside = Math.abs(dn) < PHOTO.depth / 2 && Math.abs(lat) < PHOTO.w / 2;
        let crossed = false;
        if (!inside && was && Math.sign(was[0]) !== Math.sign(dn) && Math.abs(was[0]) < 3 && Math.abs(dn) < 3) {
          const k = was[0] / (was[0] - dn);
          crossed = Math.abs(was[1] + (lat - was[1]) * k) < PHOTO.w / 2;
        }
        if (!inside && !crossed) continue;
        if (n - (fr.used.get(t.id) || 0) < PHOTO.cd * 1000) continue;
        fr.used.set(t.id, n);
        this.photoTeleport(t, fr);
      }
    }
  },
  // out where the photo was taken, facing the same way. whoever is standing right there gets telefragged (your kill).
  // an enemy using your frame is tagged by you: whatever happens to them over there is on you
  photoTeleport(t, fr) {
    const D = fr.dest, to = D.pos.slice(), owner = this.players.get(fr.o);
    for (const u of this.players.values()) {
      if (u === t || !u.alive || this.friendly(t, u)) continue;
      if (Math.hypot(u.pos[0] - to[0], u.pos[2] - to[2]) < PHOTO.frag && Math.abs(u.pos[1] - to[1]) < 1.6) {
        this.hurt(u, t, 'camera', 999, [Math.random() * 10 - 5, 16, Math.random() * 10 - 5]);
      }
    }
    if (owner && owner !== t && !this.friendly(owner, t)) this.tag(t, owner, 'camera');
    if (this.lassoCut) this.lassoCut(t, 'drop'); // a lasso rope can't follow you through a photo
    t.g = null; t.pos = to.slice(); t.vel = [0, 0, 0];
    if (t.isBot) { t.yaw = D.y; t.pitch = D.x; t.onGround = false; if (t.ai) { t.ai.hook = null; t.ai.route = null; t.ai.nav = null; t.ai.portal = null; } }
    else H.send(t, { t: 'ptp', p: to, y: D.y, x: D.x, f: fr.id });
    this.broadcast({ t: 'fx', k: 'tele', id: t.id, a: [fr.p[0], fr.p[1] + 1, fr.p[2]], b: [to[0], to[1] + 1, to[2]], f: fr.id });
  },

  // ---------------------------------------------------------------- Pop Quiz
  calcHit(pr, owner, v) {
    pr.p = v.at;
    this.removeProj(pr, { q: 1 });
    if (v.t.trap) { this.hurt(v.t, owner, 'quiz', 0, null); return; } // a soap bubble just pops
    if (owner) this.startQuiz(v.t, owner);
  },
  startQuiz(t, by, reflected) {
    const n = H.now();
    if (!t.alive || t.quiz || n < (t.quizSafe || 0) || (this.round && this.round.over) || this.isBall(t, n)) return false;
    if (by !== t && !t.isBot && n - t.spawnT < 1200) return false; // spawn protection
    if (this.friendly(by, t)) return false;
    if (this.bubbleBlocks(by, t)) { this.broadcast({ t: 'fx', k: 'bubhit', p: [t.pos[0], t.pos[1] + 0.9, t.pos[2]].map(H.r2) }); return false; }
    if (!reflected && by !== t && by.alive && t.reverseUntil > n) { // reverse card: the thrower sits the exam
      this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: by.id });
      return this.startQuiz(by, t, true);
    }
    const Q = makeQuestion();
    t.quiz = { by: by.id, q: Q.q, a: Q.a, ok: Q.ok, until: n + QUIZ.time * 1000, at: t.pos.slice(), seq: t.seq };
    t.g = null; t.beam = null; t.laserT = 0;
    if (t.isBot) {
      const D = t.ai ? t.ai.diff : 'normal';
      t.frozenUntil = t.quiz.until;
      t.quiz.botAt = n + lerp(QUIZ.botT, Math.random()) * 1000;
      t.quiz.botOk = Math.random() < (QUIZ.bot[D] ?? QUIZ.bot.normal);
      if (t.ai) { t.ai.hook = null; t.ai.route = null; }
    }
    this.tag(t, by, 'quiz');
    this.broadcast({ t: 'quiz', id: t.id, by: by.id, q: Q.q, a: Q.a, left: QUIZ.time * 1000 });
    return true;
  },
  onAnswer(p, m) {
    if (!p.quiz || !Number.isInteger(m.i) || m.i < 0 || m.i > 3) return;
    this.endQuiz(p, m.i);
  },
  // i = their pick (-1 = out of time). right: a gold star, HP and a few seconds nothing can hurt them. wrong: dead
  endQuiz(t, i, gone) {
    const q = t.quiz;
    if (!q) return;
    t.quiz = null;
    t.quizSafe = H.now() + QUIZ.safe * 1000;
    if (t.isBot) t.frozenUntil = 0;
    const right = i === q.ok;
    this.broadcast({ t: 'quizx', id: t.id, i, c: q.ok, ok: right ? 1 : 0, gone: gone ? 1 : undefined });
    if (gone) return;
    if (right) {
      // Smarty Pants: right answers count for logged-in players, from someone else's calculator, outside Training
      if (t.acct && q.by !== t.id && this.mode !== 'training') { H.stat(t, 'quiz_right', 1); H.send(t, { t: 'quizpt', n: H.liveStats(t).quiz_right || 0 }); }
      t.invulnUntil = H.now() + QUIZ.invuln * 1000;
      t.fastUntil = H.now() + QUIZ.fastT * 1000;
      this.heal(t, QUIZ.heal, 125);
    } else if (!(this.round && this.round.over)) {
      const by = this.players.get(q.by);
      this.kill(t, by && by !== t ? by : null, 'quiz');
    }
  },
  tickQuizzes(n) {
    for (const t of this.players.values()) {
      const q = t.quiz;
      if (!q) continue;
      if (!t.alive || q.seq !== t.seq) { this.endQuiz(t, -1, true); continue; }
      if (q.botAt && n >= q.botAt) { this.endQuiz(t, q.botOk ? q.ok : (q.ok + ri(1, 3)) % 4); continue; }
      if (n >= q.until + 150) { this.endQuiz(t, -1); continue; } // (a hair of slack for an answer that left just in time)
      if (t.isBot) { t.vel = [0, 0, 0]; t.pos = q.at.slice(); }
    }
  },
  // movement is the client's, but you can't walk out of an exam: your position stays where the calculator got you
  holdQuiz(p) {
    const q = p.quiz, d = H.dist3(p.pos, q.at);
    if (d > 0.8) for (let k = 0; k < 3; k++) p.pos[k] = q.at[k] + (p.pos[k] - q.at[k]) * (0.8 / d);
    p.vel = [0, 0, 0]; p.g = null;
  },
  invulnerable(t, n = H.now()) { return !!t.quiz || n < (t.invulnUntil || 0); },

  // ---------------------------------------------------------------- Night Vision Goggles
  onNv(p, m) {
    const n = H.now();
    if (!p.alive || p.item !== 'nvg' || n - (p.nvT || 0) < NVG.toggle * 700) return;
    if (this.brOn || (this.isEcon && this.isEcon() && !(p.ec && p.ec.it && p.ec.it.id === 'nvg'))) { p.nvOn = false; return; } // no goggles in a royale; bought ones only in S&D
    if (this.modeWeapon(p) || (this.chaosKit && this.chaosKit.noItem)) return;
    p.nvT = n;
    p.nvOn = m.on === 1;
  },
  // everyone you can see (walls + smoke block it) near your crosshair gets flashed: longest for whoever was looking
  // right at you, and twice as long for anyone wearing goggles. a reverse card flashes it back
  nvFlash(p, d, reflected) {
    const e = H.eyeOf(p), n = H.now(), cc = Math.cos(NVG.cone);
    if (!reflected) this.broadcast({ t: 'fx', k: 'nvflash', id: p.id, p: e.map(H.r2), d: d.map(H.r2) });
    for (const t of this.players.values()) {
      if (t === p || !t.alive || this.friendly(p, t)) continue;
      const h = H.eyeOf(t), v = [h[0] - e[0], h[1] - e[1], h[2] - e[2]], dist = Math.hypot(...v);
      if (dist > NVG.range || dist < 0.01) continue;
      const u = v.map((x) => x / dist);
      if (u[0] * d[0] + u[1] * d[1] + u[2] * d[2] < cc && dist > 2) continue;
      if (H.raycast(e, u, Math.max(0, dist - 0.3), this.boxes) || this.smokeBlocks(e, h) || this.bubbleBlocks(p, t)) continue;
      if (!reflected && t.reverseUntil > n) { this.broadcast({ t: 'fx', k: 'reflect', id: t.id, by: p.id }); this.nvFlash(t, u.map((x) => -x), true); continue; }
      const tl = H.lookOf(t), face = -(tl[0] * u[0] + tl[1] * u[1] + tl[2] * u[2]); // 1 = staring right at you
      const k = Math.max(0, Math.min(1, (face + 0.2) / 1.1));
      const s = lerp(NVG.dur, k) * (t.nvOn ? NVG.nvMul : 1) * (1 - 0.3 * dist / NVG.range);
      this.tag(t, p, 'nvg');
      if (t.isBot) { t.blindUntil = Math.max(t.blindUntil || 0, n + s * 1000); if (t.ai) t.ai.seenAt = 0; }
      else H.send(t, { t: 'flashed', by: p.id, s: H.r2(s), p: e.map(H.r2) });
    }
  },

  // ---------------------------------------------------------------- every tick
  tickGear(n) {
    this.tickBeams(n);
    this.tickFrames(n);
    this.tickQuizzes(n);
    for (const b of this.players.values()) {
      if (!b.isBot || !b.alive || (b.ai && b.ai.dummy)) continue;
      if (b.laserT && n - b.laserT > 2600) this.laserFire(b, {}); // lost them mid-charge: let it rip anyway
      if (b.laserT) b.f |= FLAGS.CHARGE;
      if (b.nvOn) b.f |= FLAGS.NV;
      this.botGear(b, n);
    }
  },
  // humans: only what the server agrees with goes out in snapshots
  gearSnap(p) {
    if ((p.f & FLAGS.NV) && !p.nvOn) p.f &= ~FLAGS.NV;
    if ((p.f & FLAGS.CHARGE) && !p.laserT) p.f &= ~FLAGS.CHARGE;
    if (p.quiz) this.holdQuiz(p);
  },
  gearJoin(p) { // a late joiner sees the frames standing and anyone mid-exam
    if (this.frames) for (const fr of this.frames.values()) H.send(p, this.frameMsg(fr));
    for (const t of this.players.values()) if (t.quiz) H.send(p, { t: 'quiz', id: t.id, by: t.quiz.by, q: t.quiz.q, a: t.quiz.a, left: Math.max(0, t.quiz.until - H.now()) });
  },
  gearReset(p) { // a new life
    p.photo = null; p.nvOn = false; p.beam = null; p.laserT = 0; p.blindUntil = 0; p.invulnUntil = 0; p.fastUntil = 0;
    if (p.quiz) this.endQuiz(p, -1, true);
  },
  gearWorldReset() {
    if (this.frames) for (const fr of [...this.frames.values()]) this.dropFrame(fr, 'gone');
  },
  // replays: frames printed before the clip that are still standing at t0 (their 'frame' event is from before)
  framePreroll(ev, t0) {
    return ev.filter((e) => (e.m.t === 'frame' && e.s < t0 && e.s + e.m.left > t0 && !ev.some((x) => x.m.t === 'framex' && x.m.id === e.m.id && x.s >= e.s && x.s < t0)) ||
      (e.m.t === 'snap' && e.s < t0 && e.s > t0 - 30000));
  },

  // ---------------------------------------------------------------- bots: blind stumbling + gadgets
  botBlind(b, dt) {
    const ai = b.ai;
    if (Math.random() < dt * 2) ai.blindDir = Math.random() * Math.PI * 2;
    b.pitch *= 0.9;
    b.yaw += Math.sin(H.now() * 0.004 + ai.seed) * dt * 2;
    const a = ai.blindDir || 0;
    return { wx: Math.cos(a) * 0.5, wz: Math.sin(a) * 0.5, jump: false };
  },
  botGear(b, n) {
    const ai = b.ai;
    // jank royale: bots use what they picked up (brBotGadget). Search & Destroy: only what they bought (the goggles flash)
    if (this.brOn) { b.nvOn = false; return; }
    if (this.isEcon && this.isEcon()) { if (this.econAiFlash) this.econAiFlash(b, n); else b.nvOn = false; return; }
    if (ai.gear === undefined) ai.gear = process.env.JF_BOT_GEAR ? (process.env.JF_BOT_GEAR === 'none' ? null : process.env.JF_BOT_GEAR) : GEAR[(Math.random() * GEAR.length) | 0]; // test knob: JF_BOT_GEAR=quiz
    const g = ai.gear;
    if (!g || b.zmz || this.mode === 'training' || this.modeWeapon(b) || (this.chaosKit && this.chaosKit.noItem)) { b.nvOn = false; return; } // zombies don't carry gear
    if (b.trap || b.quiz || n < (b.frozenUntil || 0) || n < (b.sleepUntil || 0) || n < (b.blindUntil || 0)) return;
    const t = this.players.get(ai.target), cd = ITEMS[g].recharge * 1000;
    const vis = t && t.alive && ai.seenAt && n - ai.seenAt > (BOT_DIFF[ai.diff] || BOT_DIFF.normal).react;
    const dist = t ? H.dist3(t.pos, b.pos) : 1e9;
    if (g === 'nvg') {
      if (!b.nvOn && n > (ai.gearT || 0)) { b.nvOn = true; ai.gearT = n + 4000; }
      if (b.nvOn && vis && dist < NVG.range * 0.8 && n > (ai.gearNext || 0)) {
        ai.gearNext = n + cd * (0.8 + Math.random() * 0.6);
        this.nvFlash(b, H.lookOf(b));
      }
    } else if (g === 'quiz') {
      if (vis && dist > 5 && dist < 26 && !t.quiz && n >= (t.quizSafe || 0) && n > (ai.gearNext || 0)) {
        ai.gearNext = n + cd * (0.9 + Math.random() * 0.8);
        const e = H.eyeOf(b), tc = [t.pos[0], t.pos[1] + 1, t.pos[2]], w = WEAPONS.calc;
        const hd = Math.hypot(tc[0] - e[0], tc[2] - e[2]), tt = hd / w.speed; // lob it: aim up by the drop over the flight
        const d = H.norm([tc[0] - e[0], tc[1] - e[1] + 0.5 * w.grav * tt * tt - 2 * tt, tc[2] - e[2]]);
        if (d) this.gearUse(b, { i: 'quiz' }, e, d);
      }
    } else if (g === 'camera') {
      // a photo while it's calm, a frame home when a fight goes badly, then walk into it
      if (!b.photo && !vis && b.onGround && b.hp >= 80 && n > (ai.gearNext || 0)) { ai.gearNext = n + 3000; this.snapPhoto(b, H.lookOf(b)); }
      else if (b.photo && vis && b.hp < 45 && n > (ai.gearNext || 0) && H.dist3(b.photo.pos, b.pos) > 12) {
        ai.gearNext = n + cd;
        this.printPhoto(b, H.lookOf(b));
        const fr = [...(this.frames || new Map()).values()].find((f) => f.o === b.id);
        if (fr) ai.portal = { p: fr.p, until: n + 2500 };
      }
    }
  },
  // walking into its own frame beats everything else it wanted to do
  botGearSteer(b, wx, wz) {
    const P = b.ai && b.ai.portal;
    if (!P) return [wx, wz];
    if (H.now() > P.until) { b.ai.portal = null; return [wx, wz]; }
    const dx = P.p[0] - b.pos[0], dz = P.p[2] - b.pos[2], l = Math.hypot(dx, dz) || 1;
    return [dx / l, dz / l];
  },
};
