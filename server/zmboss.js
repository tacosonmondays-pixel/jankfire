// Zombies: mini bosses. Every ZB.every rounds one clocks in: a huge mannequin with a job title, a long HP bar and
// two tricks. THE FLOOR MANAGER calls a meeting (ankle biters pile in, every zombie near him speeds up) and charges.
// THE MASCOT jumps on you and the floor ripples. They're zombies like the rest (same nav, same claws), so the mode's
// rules hold; the differences come in through a few zb* hooks. Numbers: shared/zmlimbs.js (ZT entries with boss: true).
import { raycast } from '../shared/physics.js';
import { zmHp } from '../shared/zombies.js';
import { ZT, ZB } from '../shared/zmlimbs.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const flat = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const FORCE = Object.hasOwn(ZT, process.env.JF_ZM_BOSS || '') && ZT[process.env.JF_ZM_BOSS].boss ? process.env.JF_ZM_BOSS : ''; // tests: this boss, every round

const methods = {
  // zmNextRound: is this a boss round? it walks in a few seconds after the round starts
  zbRound(n, hs) {
    const zs = this.zs;
    zs.boss = null;
    const kinds = Object.keys(ZT).filter((k) => ZT[k].boss);
    const due = FORCE || (zs.n % ZB.every === 0 ? kinds[(Math.floor(zs.n / ZB.every) - 1) % kinds.length] : '');
    if (!due) return;
    zs.bossDue = { ty: due, at: n + ZB.delay, hp: 0 };
    zs.toSpawn++; // one more on the round's list
    this.broadcast({ t: 'zlb', k: 'bosswarn', ty: due });
  },
  // zlSpawn asks: is the next one through the window the boss? returns its kind (and takes it off the list)
  zbNext(n) {
    const d = this.zs.bossDue;
    if (!d || n < d.at) return '';
    this.zs.bossDue = null; this.zs.bossHp = d.hp || 0;
    return d.ty;
  },
  // zlSpawn made it: boss HP (scaled by the squad), no limbs to lose, its tricks on their timers
  zbSpawn(b, n) {
    const zs = this.zs, z = b.zmz, def = ZT[z.ty], hs = this.zmSquad().length;
    const max = Math.round(zmHp(zs.n) * def.bossHp * (1 + ZB.perPlayer * (Math.max(1, hs) - 1)));
    b.hp = zs.bossHp > 0 ? Math.min(max, zs.bossHp) : max; zs.bossHp = 0;
    Object.assign(z, { boss: true, hp0: max, lim: 0, lhp: Infinity, t1: n + 6000, t2: n + 9000, charge: null, leap: false, leapT: 0 });
    zs.boss = { id: b.id, ty: z.ty, max };
    this.broadcast({ t: 'zlb', k: 'boss', id: b.id, ty: z.ty });
  },
  zbInfo() { // rides in zmInfo: [id, kind, hp, max] while one's alive
    const s = this.zs.boss, b = s && this.players.get(s.id);
    return b && b.alive ? { bs: [s.id, s.ty, Math.max(0, Math.round(b.hp)), s.max] } : null;
  },
  // zlHit: a boss shrugs most of a huge hit off (no one-shots: the sniper, ONE AND DONE), and keeps its limbs
  zbHit(t, amt) { return Math.min(amt, t.zmz.hp0 * ZB.hitCap); },
  // lost or wedged (zmRound is about to send it round to a window again): it comes back as itself, as hurt as it was
  zbLost(b) { this.zs.bossDue = { ty: b.zmz.ty, at: now() + 1500, hp: Math.max(1, b.hp) }; this.zs.boss = null; },

  // ---------------------------------------------------------- movement (zlSpeed / zmThink)
  zbSpeed(z, n) { // x its speed, or null = the usual rules
    if (z.charge) return n < z.charge.go ? 0 : n < z.charge.until ? ZT[z.ty].charge.speed / z.speed : null;
    return null;
  },
  zbSteer(b, z, n) { // mid-charge: straight on, whoever's in the way
    if (!z.boss || !z.charge) return;
    if (n >= z.charge.until) { z.charge = null; return; }
    z.wish = z.charge.dir.slice(); z.close = false;
  },

  // ---------------------------------------------------------- every tick (zmRound)
  zbTick(n, hs) {
    const zs = this.zs, s = zs.boss, b = s && this.players.get(s.id);
    if (!b || !b.alive || !b.zmz || b.zmz.ph !== 'hunt' || zs.st === 'over') return;
    const z = b.zmz, def = ZT[z.ty], t = this.players.get(z.target);
    const stun = n < (b.frozenUntil || 0) || n < (b.slipUntil || 0) || (b.sleepUntil || 0) > n;
    // a charge in progress: anyone it reaches goes flying (once each)
    if (z.charge && n >= z.charge.go && n < z.charge.until) {
      for (const h of hs) {
        if (!h.alive || z.charge.hit.has(h.id) || flat(h.pos, b.pos) > def.charge.reach || Math.abs(h.pos[1] - b.pos[1]) > 2.5) continue;
        z.charge.hit.add(h.id);
        this.hurt(h, b, 'bite', def.charge.dmg, [z.charge.dir[0] * def.charge.kb, 7, z.charge.dir[1] * def.charge.kb]);
      }
    }
    // a jump coming down: the floor ripples
    if (z.leap && n > z.leapT + 350 && b.onGround) {
      z.leap = false;
      const J = def.jump;
      this.broadcast({ t: 'zlb', k: 'slam', a: [r2(b.pos[0]), r2(b.pos[1]), r2(b.pos[2])], r: J.r });
      for (const h of hs) {
        const d = flat(h.pos, b.pos);
        if (!h.alive || d > J.r || Math.abs(h.pos[1] - b.pos[1]) > 2) continue;
        const f = 1 - (d / J.r) * 0.7, dx = (h.pos[0] - b.pos[0]) / (d || 1), dz = (h.pos[2] - b.pos[2]) / (d || 1);
        this.hurt(h, b, 'bite', J.dmg * f, [dx * 8 * f, 9 * f, dz * 8 * f]);
        if (h.alive && d < J.r * 0.6) this.slip(h);
      }
    }
    if (stun || z.charge || z.leap || !t || !t.alive) return;
    const d = flat(t.pos, b.pos), dy = Math.abs(t.pos[1] - b.pos[1]);
    if (def.meeting && n >= z.t1) { // the Floor Manager calls a meeting
      z.t1 = n + def.meeting.every * (0.85 + Math.random() * 0.3); z.yell = n + def.meeting.yell;
      if (zs.st === 'live') { zs.toSpawn += def.meeting.n; zs.pack = { n: def.meeting.n, win: this.zbWindow(b) }; zs.spawnAt = Math.min(zs.spawnAt, n + 400); } // ankle biters, through the window nearest him
      for (const o of zs.list) if (o !== b && flat(o.pos, b.pos) <= def.meeting.reach) o.zmz.hype = n + def.meeting.hype;
      this.broadcast({ t: 'zlb', k: 'meeting', id: b.id, a: [r2(b.pos[0]), r2(b.pos[1] + 3), r2(b.pos[2])] });
      return;
    }
    if (def.charge && n >= z.t2 && d > def.charge.min && d < def.charge.max && dy < 1.5 && this.zbSees(b, t, d)) { // ... and charges
      z.t2 = n + def.charge.every * (0.85 + Math.random() * 0.3);
      const dir = [(t.pos[0] - b.pos[0]) / d, (t.pos[2] - b.pos[2]) / d];
      z.charge = { dir, go: n + def.charge.windup, until: n + def.charge.windup + def.charge.ms, hit: new Set() };
      this.broadcast({ t: 'zlb', k: 'charge', id: b.id, d: dir.map(r2), ms: def.charge.windup });
      return;
    }
    if (def.jump && n >= z.t1 && b.onGround && d > def.jump.min && d < def.jump.max && dy < 3) { // the Mascot jumps on whoever it's after
      z.t1 = n + def.jump.every * (0.85 + Math.random() * 0.3);
      const T = (2 * def.jump.up) / 26; // seconds in the air (gravity 26)
      b.vel = [(t.pos[0] - b.pos[0]) / T, def.jump.up, (t.pos[2] - b.pos[2]) / T]; b.onGround = false; b.pos[1] += 0.05;
      z.leap = true; z.leapT = n;
      this.broadcast({ t: 'zlb', k: 'jump', id: b.id, to: [r2(t.pos[0]), r2(t.pos[1]), r2(t.pos[2])], ms: Math.round(T * 1000) });
    }
  },
  zbSees(b, t, d) { return !raycast([b.pos[0], b.pos[1] + 1.2, b.pos[2]], [(t.pos[0] - b.pos[0]) / d, 0, (t.pos[2] - b.pos[2]) / d], d, this.boxes); },
  zbWindow(b) { // the open-area window nearest the boss
    const Z = this.map.zm, zs = this.zs;
    let best = b.zmz.win, bd = Infinity;
    Z.windows.forEach((w, i) => { if (!zs.areas.has(w.area)) return; const d = flat(w.in, b.pos); if (d < bd) { bd = d; best = i; } });
    return best;
  },
  // zlKilled: it's down. everyone gets paid, a drop for certain, the round carries on without it
  zbKilled(t, killer) {
    const zs = this.zs, def = ZT[t.zmz.ty];
    zs.boss = null;
    for (const h of this.zmSquad()) if (h.z) this.zmGive(h, def.reward, 'boss');
    this.broadcast({ t: 'zlb', k: 'bossdead', id: t.id, ty: t.zmz.ty, by: killer && !killer.zmz ? killer.id : 0, a: [r2(t.pos[0]), r2(t.pos[1] + 2), r2(t.pos[2])] });
  },
};

export function installZmBoss(Room) { Object.assign(Room.prototype, methods); }
