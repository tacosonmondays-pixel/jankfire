// Plant & Defuse bots play like a lobby of real people (owner, 2026-11-10: "some should be amazing some should be really
// [bad]... consistent with head shots, peek angles, jiggle peeking, defend harder, avoid obvious line of sights, be more
// coordinated aggressive or defensive, tap strafing"). Nobody hits harder: every bot's bullets still do 0.7x. What
// changes is how they play. Each bot rolls a skill tier once (the room's difficulty moves the odds) and keeps it:
//   aim     where they point (head or chest, or somewhere near it), how much they wobble, how fast they react and turn,
//           how much of the spray they pull down against
//   feet    good ones stop dead to shoot and step sideways between shots (tap strafing); bad ones run, gun and jump
//   peeks   lost sight of someone: good ones hold the angle at head height and jiggle the corner for a moment before
//           swinging wide; bad ones just run at where they last saw you
//   cover   reloading or nearly dead with someone on them: good ones step behind the nearest thing that blocks the shot
// And each side picks a stance per round (attack: rush / default / slow; defense: forward / default / deep / stack).
// Mixed into Room by installSdSkill, after the econ + tactical installers (it wraps their bot methods). S&D only.
import { WEAPONS, BOT_DIFF } from '../shared/weapons.js';
import { PH } from '../shared/physics.js';
import { patternOf } from '../shared/tactical.js';

// head: share of fights they go for the head. err / react / turn: x the difficulty's. comp: share of the spray pattern
// pulled down. snap: how well the crosshair is actually on them when they click (1 = on, 0 = still swinging over). tap: stop-to-shoot discipline (0..1). peek: s they hold + jiggle a lost angle. duck: takes cover. hop: jumps in fights
export const SKILL = {
  cracked: { name: 'cracked', snap: 1, head: 0.85, err: 0.45, react: 0.7, turn: 1.5, comp: 0.92, tap: 1, peek: [0.9, 2], duck: 0.9, hop: 0 },
  good: { name: 'good', snap: 0.85, head: 0.55, err: 0.75, react: 0.9, turn: 1.2, comp: 0.75, tap: 0.85, peek: [1.2, 2.6], duck: 0.6, hop: 0 },
  average: { name: 'average', snap: 0.5, head: 0.25, err: 1.1, react: 1.1, turn: 1, comp: 0.5, tap: 0.45, peek: [0, 1.2], duck: 0.25, hop: 0.25 },
  bad: { name: 'bad', snap: 0.15, head: 0.06, err: 1.9, react: 1.6, turn: 0.7, comp: 0.15, tap: 0.05, peek: [0, 0], duck: 0, hop: 1 },
};
// who shows up at each difficulty: [cracked, good, average, bad]
const ODDS = { easy: [0, 0.15, 0.45, 0.4], normal: [0.1, 0.3, 0.4, 0.2], hard: [0.3, 0.4, 0.25, 0.05] };
const TIERS = ['cracked', 'good', 'average', 'bad'];
const FORCE = process.env.JF_SD_SKILL && SKILL[process.env.JF_SD_SKILL] ? process.env.JF_SD_SKILL : null; // test knob: every bot is this tier
const LOG = !!process.env.JF_SD_LOG;
export function rollTier(diff, r = Math.random()) {
  const o = ODDS[diff] || ODDS.normal;
  for (let i = 0; i < 4; i++) { if (r < o[i]) return TIERS[i]; r -= o[i]; }
  return 'average';
}
const now = () => Date.now();
const lerp = (ab, k) => ab[0] + (ab[1] - ab[0]) * k;

export function installSdSkill(Room) {
  const P = Room.prototype;
  const o = { botThink: P.botThink, botFire: P.botFire, botGoal: P.botGoal, botD: P.botD, econAiAttack: P.econAiAttack, econAiDefense: P.econAiDefense };
  for (const [k, f] of Object.entries(o)) if (typeof f !== 'function') throw new Error('sdskill: Room is missing ' + k);

  // a bot's skill sheet: rolled once, re-rolled if the room's difficulty changes
  P.sdSkill = function (b) {
    const ai = b.ai;
    if (!ai.sk || ai.sk.diff !== ai.diff) {
      const tier = FORCE || rollTier(ai.diff);
      ai.sk = { ...SKILL[tier], diff: ai.diff, seed: Math.random() * 1000, fight: 0, head: Math.random() < SKILL[tier].head, lostT: 0, lost: null, cover: null, coverT: 0 };
      ai.comp = ai.sk.comp; // (server/tactical.js tacBotAim)
      if (LOG) console.log(`[sdskill] ${b.name} is ${tier} (${ai.diff})`);
    }
    return ai.sk;
  };
  // reaction, wobble and turn speed: the difficulty's numbers through this bot's skill
  P.botD = function (b) {
    const D = o.botD.call(this, b);
    if (!this.isEcon() || !b.ai || b.ai.dummy) return D;
    const sk = this.sdSkill(b);
    if (sk.D && sk.Dof === D) return sk.D;
    sk.Dof = D; sk.D = { ...D, react: D.react * sk.react, err: D.err * sk.err, turn: D.turn * sk.turn };
    return sk.D;
  };
  P.botGoal = function (b) { const g = o.botGoal.call(this, b); if (b.ai) b.ai.goalNow = g; return g; };

  // the shot: point at the head (or the chest, or roughly at them) for this one bullet
  P.botFire = function (b, t, D) {
    const w = WEAPONS[b.w];
    if (!this.isEcon() || !t || !w || w.kind !== 'hitscan' || !b.ai || b.ai.dummy) return o.botFire.call(this, b, t, D);
    const sk = this.sdSkill(b), n = now();
    if (sk.fight !== b.ai.seenAt) { sk.fight = b.ai.seenAt; sk.aimHead = Math.random() < SKILL[sk.name].head; sk.aimOff = (Math.random() - 0.5) * 0.5 * sk.err; } // a new fight: where this one is aimed
    const pellets = (w.pellets || 1) > 1, ey = b.pos[1] + PH.eye;
    const ty = t.pos[1] + (sk.aimHead && !pellets ? 1.9 : 1.15) + sk.aimOff + Math.sin(n * 0.004 + sk.seed) * 0.12 * sk.err;
    const hd = Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]) || 1, keep = b.pitch;
    // counter-strafing: someone who just hit the brakes waits until they've actually stopped (moving wrecks the shot here)
    if (n - (sk.stopT || 0) < 500 && b.onGround && hd > 5 && Math.hypot(b.vel[0], b.vel[2]) > 1.3 && n - (sk.waitT || 0) < 450) { b.ai.nextShot = n + 40; return; }
    sk.waitT = n;
    let dy = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])) - b.yaw; dy = ((dy + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
    b.yaw += dy * sk.snap + (Math.random() - 0.5) * D.err * 0.8; // the flick: good ones land on you, bad ones are still swinging past
    b.pitch = Math.atan2(ty - ey, hd);
    try { return o.botFire.call(this, b, t, D); } finally { b.pitch = keep; }
  };

  // feet, peeks and cover: rework what botThink decided for this tick
  P.botThink = function (b, dt) {
    const out = o.botThink.call(this, b, dt);
    if (!this.isEcon() || !out || !b.ai || b.ai.dummy || !b.alive) return out;
    const ai = b.ai, sk = this.sdSkill(b), n = now(), goal = ai.goalNow, w = WEAPONS[b.w];
    if (!w || w.kind !== 'hitscan' || (goal && (goal.use || goal.tac === 'throw' || goal.tac === 'save' || goal.tac === 'defuse')) || n < (b.blindUntil || 0)) return out;
    const t = this.players.get(ai.target), P0 = patternOf(b.w);
    // on the clock (carrying, defusing, or an attacker once the push is called): still stop to shoot, but no holding angles or hiding
    const B = this.bomb, A = this.ec && this.ec.tac && this.ec.tac.A;
    const push = !!(B && b.team === B.att && B.ph !== 'planted' && A && A.phase === 'exec'), forced = !!(goal && goal.force) || push;
    if (!t || !t.alive) { sk.lost = null; return out; }
    const dx = t.pos[0] - b.pos[0], dz = t.pos[2] - b.pos[2], hd = Math.hypot(dx, dz) || 1, sx = -dz / hd, sz = dx / hd; // (sx, sz): sideways to them
    if (ai.seenAt) {
      sk.lost = { p: t.pos.slice(), t: n, id: t.id, hold: lerp(sk.peek, Math.random()) * 1000 };
      if (sk.hop < 1) out.jump = out.jump && Math.random() < sk.hop; // jumping throws the shot away: only bad players do it
      if (hd > (w.range || 60)) return out;
      // cover: reloading or nearly dead with someone looking at you
      if ((n < ai.reloadUntil || b.hp < 35) && sk.duck > 0 && (!forced || (push && !(goal && goal.force)))) { // (pushing attackers still hide to reload; the carrier keeps going)
        if (n > sk.coverT) { sk.coverT = n + 500; sk.cover = Math.random() < sk.duck ? this.sdCover(b, t) : null; }
        if (sk.cover) { const cx = sk.cover[0] - b.pos[0], cz = sk.cover[2] - b.pos[2], cl = Math.hypot(cx, cz); if (cl > 0.4) { out.wx = cx / cl; out.wz = cz / cl; return out; } out.wx = 0; out.wz = 0; return out; }
      }
      if (!P0 || P0.move < 0.3) return out; // shotguns don't care
      const ready = n >= ai.nextShot - 260 && n >= ai.reloadUntil;
      if (sk.tapFor !== ai.seenAt) { sk.tapFor = ai.seenAt; sk.taps = Math.random() < sk.tap; } // decided once a fight: disciplined this time, or not
      if (sk.taps) {
        if (ready) { out.wx = 0; out.wz = 0; out.jump = false; sk.stopT = n; } // stop dead, then shoot
        else { const s = Math.sin(n * 0.006 + sk.seed) > 0 ? 1 : -1; out.wx = sx * s; out.wz = sz * s; } // between shots: a step sideways
      } else if (sk.tap < 0.2) { const s = ai.strafeDir || 1; out.wx += sx * s * 0.8; out.wz += sz * s * 0.8; } // run and gun
      return out;
    }
    // they went behind something: hold the angle at head height and jiggle the corner, then swing (or just run at it)
    const L = sk.lost;
    if (L && L.id === t.id && n - L.t < L.hold && !forced) {
      const ex = L.p[0] - b.pos[0], ez = L.p[2] - b.pos[2], el = Math.hypot(ex, ez) || 1;
      const yaw = Math.atan2(-ex, -ez), pitch = Math.atan2(L.p[1] + 1.9 - (b.pos[1] + PH.eye), el);
      let d = yaw - b.yaw; d = ((d + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
      b.yaw += d * Math.min(1, 10 * dt); b.pitch += (pitch - b.pitch) * Math.min(1, 10 * dt);
      const ph = ((n - L.t) % 800) / 800, s = (Math.sin(sk.seed) > 0 ? 1 : -1) * (ph < 0.3 ? 1 : ph < 0.6 ? -1 : 0); // out, back, wait
      out.wx = (-ez / el) * s; out.wz = (ex / el) * s; out.jump = false;
    }
    return out;
  };
  // somewhere within a few steps where a wall stands between this bot and t
  P.sdCover = function (b, t) {
    let best = null, bd = 1e9;
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * Math.PI * 2, q = [b.pos[0] + Math.cos(a) * 2.4, b.pos[1], b.pos[2] + Math.sin(a) * 2.4];
      if (!this.econAiCover(q, t.pos) || !this.clearPath(b.pos, q)) continue;
      const d = Math.hypot(q[0] - t.pos[0], q[2] - t.pos[2]);
      if (d < bd) { bd = d; best = q; } // the one nearest them: shortest way back into the fight
    }
    return best;
  };

  // ---------------------------------------------------------- team stances, one per side and round
  // attack: rush = go the moment two are staged (or 9 s in), slow = sit on the stage a while first. the plan itself is econai's
  P.econAiAttack = function (T, S, n) {
    const had = T.A;
    if (had && had.stance === 'slow' && had.phase === 'gather' && this.bomb.ph !== 'planted' && n - T.live < 13000 && this.econAiLeft() > 60
      && !this.econAiBots(this.bomb.att).some((b) => b.ai.seenAt)) return; // slow: nobody has seen us, so sit on the stage and let them get bored
    o.econAiAttack.call(this, T, S, n);
    const A = T.A;
    if (!A) return;
    if (!had) { const r = Math.random(); A.stance = r < 0.3 ? 'rush' : r < 0.55 ? 'slow' : 'default'; this.tacLog(T, `attack stance: ${A.stance}`); }
    if (A.phase !== 'gather') return;
    if (A.stance === 'rush' && n - T.live > 9000) {
      const s = S.sites[A.site];
      let staged = 0;
      for (const g of A.groups) for (const id of g.ids) { const b = this.players.get(id); if (b && b.alive && Math.hypot(b.pos[0] - s.attE[g.lane].stage[0], b.pos[2] - s.attE[g.lane].stage[2]) < 9) staged++; }
      if (staged >= 2) { A.phase = 'exec'; A.execAt = n; this.econAiUtilPlan(A, s, this.econAiBots(this.bomb.att)); this.tacLog(T, `EXECUTE ${A.site}: rush, ${staged} staged`); }
    }
  };
  // defense: forward = holds nearest the attackers, deep = holds nearest home, stack = one more body on the favoured site
  P.econAiDefense = function (T, S, n) {
    const had = T.Dd;
    o.econAiDefense.call(this, T, S, n);
    const Dd = T.Dd;
    if (!Dd || had) return;
    const r = Math.random();
    Dd.stance = r < 0.25 ? 'forward' : r < 0.5 ? 'deep' : r < 0.7 ? 'stack' : 'default';
    const bots = this.econAiBots(3 - this.bomb.att), hyp = (a, c) => Math.hypot(a[0] - c[0], a[2] - c[2]);
    if (Dd.stance === 'forward' || Dd.stance === 'deep') {
      const used = new Set(), sign = Dd.stance === 'forward' ? 1 : -1;
      for (const b of bots) {
        const a = Dd.assign.get(b.id), s = a && S.sites[a.site];
        if (!s || !s.holds.length) continue;
        const free = s.holds.filter((h) => !used.has(h)).sort((x, y) => sign * (hyp(x.p, S.attC) - hyp(y.p, S.attC)));
        if (free[0]) { a.spot = free[0]; used.add(free[0]); }
      }
    } else if (Dd.stance === 'stack' && bots.length >= 4) {
      const per = {};
      for (const a of Dd.assign.values()) per[a.site] = (per[a.site] || 0) + 1;
      const [big, small] = Object.keys(per).sort((x, y) => per[y] - per[x]);
      const mv = small && per[small] > 1 && bots.find((b) => Dd.assign.get(b.id) && Dd.assign.get(b.id).site === small);
      if (mv) { const s = S.sites[big], taken = new Set([...Dd.assign.values()].map((a) => a.spot)); Dd.assign.set(mv.id, { site: big, spot: this.econAiPickHold(s, taken, 'any') }); }
    }
    this.tacLog(T, `defense stance: ${Dd.stance}`);
  };
}
