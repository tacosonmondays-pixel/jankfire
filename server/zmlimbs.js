// Zombies: dismemberment and the special zombies. Shots that land on an arm or a leg add up; enough and it comes off.
// No legs: it crawls (slow, can't jump, can't reach you on a crate). One leg: it hops. No arms: it headbutts for half
// and is useless at planks. The specials (shared/zmlimbs.js): Chonk, Ankle Biters, Hard Hats, the Screamer.
// Installed onto Room by server/zombies.js; the mode calls in through a few zl* hooks.
import { WEAPONS, FLAGS } from '../shared/weapons.js';
import { ZM } from '../shared/zombies.js';
import { ZL, ZL_ARMS, ZL_LIMBS, ZLN, ZT, zlCrawl, zlHop, zlPickType, zlZone } from '../shared/zmlimbs.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const FORCE = Object.hasOwn(ZT, process.env.JF_ZM_TYPE || '') ? process.env.JF_ZM_TYPE : ''; // tests: every zombie is this one
const LIMB_MUL = Number(process.env.JF_ZM_LIMB) > 0 ? Number(process.env.JF_ZM_LIMB) : 1; // tests: x limb HP (0.01 = first hit takes it off)
const fin3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);

const methods = {
  // zmSpawn hook: what kind this one is, and its limbs. g = its gait, D = the room's difficulty
  zlSpawn(b, D, n) {
    const zs = this.zs, z = b.zmz, alive = {};
    for (const o of zs.list) if (o.zmz.ty) alive[o.zmz.ty] = (alive[o.zmz.ty] || 0) + 1;
    let ty = zs.pack && zs.pack.n > 0 ? 'biter' : FORCE || zlPickType(zs.n, alive);
    if (FORCE && (alive[FORCE] || 0) >= ZT[FORCE].cap + 3) ty = ''; // (tests still get a few plain ones)
    const def = ZT[ty] || null;
    Object.assign(z, { ty, lim: 0, ld: {}, hat: 0, k: 1, hype: 0, yell: 0, yellAt: n + 4000 + Math.random() * 4000 });
    if (def) {
      b.hp = Math.max(1, Math.round(b.hp * def.hp));
      if (def.speed) z.speed = def.speed * D.speed * (0.94 + Math.random() * 0.12);
      if (def.run != null) z.run = def.run;
      if (def.color) b.color = def.color;
      z.hat = def.hat || 0; z.k = def.scale || 1;
      if (def.pack) { if (zs.pack && zs.pack.n > 0) zs.pack.n--; else zs.pack = { n: Math.min(def.pack - 1, zs.toSpawn - 1), win: z.win }; } // the rest of the litter comes through the same window
    } else if (Math.random() < ZLN.bornArmless) z.lim = ZL.armL; // the odd one turns up an arm short
    z.hp0 = b.hp; z.lhp = Math.max(ZLN.limbMin, b.hp * ZLN.limbHp) * LIMB_MUL;
  },
  zlPackWin() { const pk = this.zs.pack; return pk && pk.n > 0 && this.zs.areas.has(this.map.zm.windows[pk.win].area) ? pk.win : -1; },
  // what everyone needs to draw them (rides in zmInfo): [id, type, limbs gone, 1 = hat on | 2 = hyped up | 4 = shrieking]
  zlInfo(n) {
    const out = [];
    for (const b of this.zs.list) {
      const z = b.zmz, def = ZT[z.ty], fl = (z.hat > 0 ? 1 : 0) | (n < z.hype ? 2 : 0) | (n < z.yell ? 4 : 0);
      if (def || z.lim || fl) out.push([b.id, def ? def.i : 0, z.lim, fl]);
    }
    return { lb: out };
  },

  // ---------------------------------------------------------- hits (zmDamage, a squad member hitting a zombie)
  zlHit(t, amt, a, w, hs) {
    const z = t.zmz;
    if (!z || amt <= 0) return amt;
    const aim = a.zlz && a.zlz.id === t.id ? a.zlz : null, wd = WEAPONS[w], dir = aim ? aim.d : this.zlAway(a, t);
    let zone = hs ? 'head' : aim ? aim.zone : null;
    if (zone === 'head' && z.hat > 0) { // HARD HAT: it dinks off the hat, body damage at best
      z.hat--; amt *= 0.35;
      this.broadcast({ t: 'zlb', k: z.hat ? 'dink' : 'hat', id: t.id, d: dir.map(r2) });
    }
    const left = ZL_LIMBS.filter((l) => !(z.lim & ZL[l]));
    if (!zone) zone = left.length && Math.random() < 0.35 ? left[(Math.random() * left.length) | 0] : 'torso'; // bots, blasts, things thrown: now and then it's a limb
    const lethal = amt >= t.hp;
    if (ZL[zone] && zone !== 'head' && !(z.lim & ZL[zone])) {
      z.ld[zone] = (z.ld[zone] || 0) + amt;
      if (lethal || z.ld[zone] >= z.lhp) this.zlCut(t, zone, a, dir, lethal);
    } else if (zone === 'head' && lethal) this.zlCut(t, 'head', a, dir, true);
    if (lethal && wd && wd.kind !== 'hitscan' && wd.kind !== 'melee') { // blown up / bowled over: more bits
      for (const l of ZL_LIMBS) if (!(z.lim & ZL[l]) && Math.random() < 0.5) this.zlCut(t, l, a, dir, true);
    }
    return amt;
  },
  zlAway(a, t) { const dx = t.pos[0] - a.pos[0], dz = t.pos[2] - a.pos[2], l = Math.hypot(dx, dz) || 1; return [dx / l, 0.3, dz / l]; },
  // a limb comes off. dead: this hit kills it anyway (just for show: no pay, nothing to slow down)
  zlCut(t, limb, a, dir, dead) {
    const z = t.zmz, bit = ZL[limb];
    if (!bit || (z.lim & bit)) return;
    z.lim |= bit;
    if (!dead) {
      if (a && a.z && !a.zmz) { this.zmGive(a, ZLN.limbPay, 'limb'); a.z.limbs = (a.z.limbs || 0) + 1; }
      if (zlCrawl(z.lim) || zlHop(z.lim)) z.run = 0; // no more sprinting
    }
    this.broadcast({ t: 'zlb', k: 'cut', id: t.id, l: bit, m: z.lim, d: (dir || [0, 0.3, 0]).map(r2), by: a ? a.id : 0, x: dead ? 1 : undefined });
  },

  // ---------------------------------------------------------- what missing bits (and being special) do: zmStep / zmSwipe / zxTear
  zlSpeed(z, n) { // x its normal speed
    if (n < z.yell) return 0; // busy shrieking
    const base = zlCrawl(z.lim) ? Math.min(1, ZLN.crawl / Math.max(0.1, z.speed)) : zlHop(z.lim) ? ZLN.hop : 1;
    return base * (n < z.hype ? ZT.screamer.boost : 1);
  },
  zlCanJump(z) { return !(z.lim & (ZL.legL | ZL.legR)); },
  zlReachUp(z) { return zlCrawl(z.lim) ? ZLN.crawlUp : ZM.reachUp * Math.min(1.15, z.k || 1); },
  zlHeadY(z) { return zlCrawl(z.lim) ? ZLN.crawlHead : 1.9 * (z.k || 1); },
  zlClaw(z) { const def = ZT[z.ty]; return ((def && def.claw) || 1) * ((z.lim & ZL_ARMS) === ZL_ARMS ? ZLN.noArms : 1); },
  zlCd(z) { const def = ZT[z.ty]; return ((def && def.cd) || 1) * (z.lim & ZL_ARMS ? ZLN.oneArmCd : 1); },
  zlTear(z) { return (z.lim & ZL_ARMS) === ZL_ARMS ? ZLN.noArmTear : z.lim & ZL_ARMS ? 1.3 : 1; },
  zlFlags(z) { return zlCrawl(z.lim) ? FLAGS.CROUCH : 0; },

  // ---------------------------------------------------------- every tick (zmRound): the Screamer, Chonks going off
  zlTick(n) {
    const zs = this.zs, S = ZT.screamer;
    for (const b of zs.list) {
      const z = b.zmz;
      if (z.ty !== 'screamer' || z.ph !== 'hunt' || n < z.yellAt || zs.st === 'over') continue;
      const t = this.players.get(z.target);
      if (!t || !t.alive || Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]) > S.see) { z.yellAt = n + 800; continue; }
      z.yellAt = n + S.every * (0.85 + Math.random() * 0.3); z.yell = n + S.yell;
      for (const o of zs.list) if (o !== b && Math.hypot(o.pos[0] - b.pos[0], o.pos[2] - b.pos[2]) <= S.reach) o.zmz.hype = n + S.hype;
      this.broadcast({ t: 'zlb', k: 'scream', id: b.id, a: [r2(b.pos[0]), r2(b.pos[1] + 1.7), r2(b.pos[2])] });
    }
    if (!zs.pops || !zs.pops.length) return;
    const pops = zs.pops; zs.pops = [];
    for (const p of pops) this.zlPop(p);
  },
  // a Chonk died: it pops. zombies near it take the blast (the kills are the shooter's), people get shoved and slip in it
  zlPop(p) {
    const C = ZT.chonk, by = this.players.get(p.by) || null;
    this.broadcast({ t: 'zlb', k: 'pop', a: p.at.map(r2) });
    for (const o of [...this.players.values()]) {
      if (!o.alive) continue;
      const dx = o.pos[0] - p.at[0], dz = o.pos[2] - p.at[2], d = Math.hypot(dx, dz), l = d || 1;
      if (d > C.blast || Math.abs(o.pos[1] - p.at[1]) > 3) continue;
      const f = 1 - (d / C.blast) * 0.6, kb = [(dx / l) * 13 * f, 8 * f, (dz / l) * 13 * f];
      if (o.zmz) { if (by && by.alive) this.hurt(o, by, 'chonk', C.blastZ * f, kb); else { this.knock(o, kb, 'chonk'); this.damage(o, C.blastZ * f, null, 'chonk'); } }
      else if (o.z) { this.knock(o, kb, 'chonk'); this.damage(o, C.blastP * f, null, 'chonk'); if (o.alive && d < C.blast * 0.7) this.slip(o); }
    }
  },
  // zmKilled hook (a zombie died): the bonus for the specials, and a Chonk queues its pop for the next tick
  zlKilled(t, killer) {
    const z = t.zmz, def = ZT[z.ty];
    if (!def) return;
    if (def.pay && killer && killer.z && !killer.zmz) this.zmGive(killer, def.pay, z.ty);
    if (def.blast) (this.zs.pops ||= []).push({ at: t.pos.slice(), by: killer && !killer.zmz ? killer.id : 0 });
  },
};

export function installZmLimbs(Room) {
  Object.assign(Room.prototype, methods);
  const P = Room.prototype, onHit = P.onHit;
  // a 'hit' on a zombie: work out which part the shot went through before the usual rules run (the head is theirs to judge).
  // the direction is the shooter's word like the rest of the hit; all it buys is which limb, never more damage
  P.onHit = function (p, m) {
    const t = this.zm && m && typeof m.to === 'number' ? this.players.get(m.to) : null;
    if (!t || !t.zmz || !t.alive || !p.alive || !fin3(m.d)) return onHit.call(this, p, m);
    const l = Math.hypot(m.d[0], m.d[1], m.d[2]);
    if (l < 1e-6) return onHit.call(this, p, m);
    const d = [m.d[0] / l, m.d[1] / l, m.d[2] / l], e = [p.pos[0], p.pos[1] + (p.f & FLAGS.CROUCH ? 1.05 : 1.6), p.pos[2]];
    p.zlz = { id: t.id, zone: zlZone(e, d, t.pos, t.yaw || 0, t.zmz.k || 1, zlCrawl(t.zmz.lim)), d };
    try { return onHit.call(this, p, m); } finally { p.zlz = null; }
  };
}
