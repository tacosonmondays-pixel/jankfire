// story encounters (OVERDUE Act I): what some story enemies do on top of being the game's bots. installed on the Room
// by shared/story/encsys.js once the referee's room is up (solo: the story worker), so nothing here touches a match.
//   war_rig       a desk war-rig: drives like a car (shared/story/drive.js, the same physics as yours) straight at you,
//                 rams, backs off, comes again; its minigun is the bot's own gun (botThink aims and fires it)
//   intern        a bot that also lobs "business cards" (frags) when you're at throwing range
//   stomach_dog   fast, and leaps at you from a few metres out
// every special thing it does goes out through room.onEnc(ev): { type: 'ram', b, t, v } · { type: 'card', b } ·
// { type: 'leap', b }. encsys turns rams into damage (less if you're in a car) and the client into juice.
import { newCar, stepCar, carType, fwdOf, topOf } from '../shared/story/drive.js';
import { query, raycast } from '../shared/physics.js';
import { WEAPONS } from '../shared/weapons.js';

export const ENC = {
  rig: { ty: 'van', top: 0.8, ramCd: 1.6, backFor: 1.1, ramV: 5, maxV: 34 },
  card: { min: 6, max: 24, cd: [5000, 8500] },
  dog: { spd: 1.35, min: 3.5, max: 9, cd: [2200, 3800], v: 15, up: 6.5 },
};
const now = () => Date.now();
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const rnd = (a) => a[0] + Math.random() * (a[1] - a[0]);

export function installStoryEnc(Room) {
  const P = Room.prototype;
  if (P.encInstalled) return;
  P.encInstalled = true;
  const step0 = P.stepBot;
  P.stepBot = function (b, dt) {
    const k = this.mode === 'story' && b.sk && !b.sk.b ? b.sk.kind : '';
    if (k === 'war_rig') return this.encRig(b, dt);
    const r = step0.call(this, b, dt);
    if (k === 'intern' && !b.sk.hold) this.encCard(b);
    else if (k === 'stomach_dog' && !b.sk.hold) this.encDog(b);
    return r;
  };
  // the room's boxes as a drive.js world
  P.encWorld = function () {
    const B = this.boxes;
    if (!this.encW || this.encW.B !== B) this.encW = { B, query: (a, b, c, d, out) => query(B, a, b, c, d, out), raycast: (o, d, m) => raycast(o, d, m, B) };
    return this.encW;
  };
  P.encTarget = function (b) {
    let best = null, bd = 1e9;
    for (const p of this.players.values()) if (p.alive && p !== b && !this.friendly(b, p) && !(p.sk && p.sk.side === b.sk.side)) { const d = Math.hypot(p.pos[0] - b.pos[0], p.pos[2] - b.pos[2]); if (d < bd) { bd = d; best = p; } }
    return best;
  };
  P.encRig = function (b, dt) {
    const R = ENC.rig;
    const t = this.encTarget(b), n = now();
    if (!b.encCar) b.encCar = { car: newCar(R.ty, b.pos.slice(), t ? Math.atan2(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]) : b.yaw + Math.PI), back: 0, ramT: 0 }; // (it arrives facing you)
    const g = b.encCar, c = g.car, T = carType(c.ty);
    if (!b.sk.hold) this.botThink(b, dt); // aims and fires the minigun (its walking wish is ignored: a rig drives)
    let inp = { f: false, b: true, l: false, r: false, hand: false, boost: false };
    if (!b.sk.hold && t) {
      const dx = t.pos[0] - c.x, dz = t.pos[2] - c.z, flee = !!b.sk.flee;
      const want = flee ? Math.atan2(-dx, -dz) : Math.atan2(dx, dz), diff = wrapA(want - c.h), rev = g.back > 0;
      if (rev) g.back -= dt;
      const vf = c.vx * Math.sin(c.h) + c.vz * Math.cos(c.h), top = topOf(T) * R.top;
      inp = { f: !rev && vf < top, b: rev, l: rev ? g.side < 0 : diff > 0.1, r: rev ? g.side > 0 : diff < -0.1, hand: !rev && Math.abs(diff) > 1.4 && vf > 10, boost: false };
      // stuck on something (a crate, a kerb, a parked car): back up turning, then try again
      g.stuck = !rev && Math.abs(vf) < 1.5 ? (g.stuck || 0) + dt : 0;
      if (g.stuck > 0.8) { g.stuck = 0; g.back = 1.2; g.side = Math.random() < 0.5 ? -1 : 1; }
      // a ram: the nose (or the side) reaches you while closing fast
      const f = fwdOf(c), along = Math.max(-T.L / 2, Math.min(T.L / 2, dx * f[0] + dz * f[2])), px = c.x + f[0] * along - t.pos[0], pz = c.z + f[2] * along - t.pos[2];
      const close = Math.hypot(px, pz) < T.W / 2 + 0.9 && t.pos[1] < c.y + T.H + 0.5 && t.pos[1] > c.y - 2.5;
      const rv = [c.vx - (t.vel ? t.vel[0] : 0), c.vz - (t.vel ? t.vel[2] : 0)], closing = (rv[0] * dx + rv[1] * dz) / (Math.hypot(dx, dz) || 1);
      if (!flee && close && closing > R.ramV && n > g.ramT) {
        g.ramT = n + R.ramCd * 1000; g.back = R.backFor; g.side = 0;
        if (this.onEnc) this.onEnc({ type: 'ram', b, t, v: [c.vx, Math.max(4, closing * 0.35), c.vz], speed: closing });
        c.vx *= -0.3; c.vz *= -0.3; // the rig bounces off what it hit
      }
    }
    stepCar(c, inp, dt, this.encWorld());
    const sp = Math.hypot(c.vx, c.vz); if (sp > R.maxV) { c.vx *= R.maxV / sp; c.vz *= R.maxV / sp; }
    b.pos[0] = c.x; b.pos[1] = c.y; b.pos[2] = c.z; b.vel[0] = c.vx; b.vel[1] = c.vy; b.vel[2] = c.vz;
    b.onGround = c.ground; b.f = 0;
    if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
  };
  // business cards: an intern at throwing range lobs a frag at you now and then
  P.encCard = function (b) {
    const t = this.players.get(b.ai && b.ai.target), n = now(), C = ENC.card;
    if (!t || !t.alive || !b.alive || this.friendly(b, t)) return;
    if (n < (b.cardT ??= n + rnd(C.cd))) return;
    const e = [b.pos[0], b.pos[1] + 1.5, b.pos[2]], dx = t.pos[0] - e[0], dz = t.pos[2] - e[2], hd = Math.hypot(dx, dz);
    if (hd < C.min || hd > C.max || !b.ai.seenAt) return;
    b.cardT = n + rnd(C.cd);
    const w = WEAPONS.frag, sp = Math.min(w.speed || 22, 8 + hd * 0.9), tt = hd / sp; // lob it: up by half the drop over the flight
    const vy = (t.pos[1] + 0.5 - e[1]) / tt + 0.5 * (w.grav || 22) * tt;
    this.makeProj(b, 'frag', [e[0] + dx / hd * 0.7, e[1], e[2] + dz / hd * 0.7], [dx / hd * sp, Math.min(18, vy), dz / hd * sp]);
    if (this.onEnc) this.onEnc({ type: 'card', b });
  };
  // stomach-dogs: quick, and they leap the last few metres
  P.encDog = function (b) {
    const D = ENC.dog, t = this.players.get(b.ai && b.ai.target), n = now();
    if (b.ai) b.ai.spd = D.spd;
    if (!t || !t.alive || !b.alive || !b.onGround || n < (b.leapT || 0)) return;
    const dx = t.pos[0] - b.pos[0], dz = t.pos[2] - b.pos[2], d = Math.hypot(dx, dz);
    if (d < D.min || d > D.max) return;
    b.leapT = n + rnd(D.cd);
    b.vel[0] = dx / d * D.v; b.vel[2] = dz / d * D.v; b.vel[1] = D.up; b.onGround = false; b.pos[1] += 0.05;
    if (this.onEnc) this.onEnc({ type: 'leap', b });
  };
}
