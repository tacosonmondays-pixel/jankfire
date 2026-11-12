// MECH DROP killstreak, the server side (numbers: shared/mech.js, design: docs/mechs/PLAY.md). Movement is the client's,
// but everything that hurts, helps or costs is judged here: the drop marker (range, line of sight, a floor, open sky),
// the landing shockwave, climbing in, the armour (a body pool, server/bodyhp.js) with the knight's shield, energy and
// cooldowns, speed caps, every move's hits, stomps, rams, overtime marks, the eject blast. installMech(Room, helpers)
// adds the methods; room.js calls them from one-line hooks (grep "mech").
// Mechs live in room._mechs: { id, o (owner), f (frame), p, yaw, st: 'fall' | 'wait' | 'in' | 'idle', t, until, hp }.
// The pilot carries p.mech: { id, f, E (energy), cd, ... } while inside.
import { ISLE } from '../shared/island.js'; // (battle island: the zone vs mechs)
import { FLAGS, WEAPONS } from '../shared/weapons.js';
import { BODY } from '../shared/bodyhp.js';
import { MECH, MF, MECH_BITS, mechFrame, isFrame, mechBoxes, energyAt, spend, newEnergy, speedCap, inArc, ramHit, dropHit, addMark } from '../shared/mech.js';
import { inFront } from '../shared/rig.js';
import { outOfBounds, boundsCenter } from '../shared/bounds.js';
import { raycast, movePlayer, playerBoxes, rayBox, PH } from '../shared/physics.js';

const PP = MECH.paperplane, NS = MECH.nightshift;
const lookOf = (p) => { const c = Math.cos(p.pitch || 0); return [-Math.sin(p.yaw) * c, Math.sin(p.pitch || 0), -Math.cos(p.yaw) * c]; };
const hdist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const hopUp = (F) => F.hop * F.hop / (2 * F.grav) + 1.5; // how high a hop goes (+ slack): the rise budget a floor gives you
// shortest distance from point c to the segment a-b
function segDist(a, b, c) {
  const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2];
  const t = l2 > 1e-9 ? Math.max(0, Math.min(1, ((c[0] - a[0]) * ab[0] + (c[1] - a[1]) * ab[1] + (c[2] - a[2]) * ab[2]) / l2)) : 0;
  return Math.hypot(a[0] + ab[0] * t - c[0], a[1] + ab[1] * t - c[1], a[2] + ab[2] * t - c[2]);
}
// nothing solid between a and b
function clear(a, b, boxes) {
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(d[0], d[1], d[2]);
  return l < 0.35 || !raycast(a, [d[0] / l, d[1] / l, d[2] / l], l - 0.3, boxes);
}
const MSG_PER_S = 30; // 'mech' messages a second per player (cannons are 8): more get dropped

export function installMech(Room, U) {
  const { now, num, vec3, norm, r2, center, safe, send, REC_T } = U;
  REC_T.add('mech'); // drops, swings, slams and blasts show up in killcams and the play of the round

  Object.assign(Room.prototype, {
    mechMap() { return this._mechs || (this._mechs = new Map()); },
    mechOn(p, n = now()) { return !!(p && p.alive && p.mech && p.mech.on); },
    mechOf(p) { for (const m of this.mechMap().values()) if (m.o === p.id) return m; return null; }, // your mech out there (one at a time)
    // the middle of a body for the moves' hit tests: a mech's is up in its chest
    mechCenter(t) { return this.mechOn(t) ? [t.pos[0], t.pos[1] + MECH[t.mech.f].h * 0.45, t.pos[2]] : center(t); },
    mechEyeOf(p) { return [p.pos[0], p.pos[1] + MECH[p.mech.f].eye, p.pos[2]]; },
    mechShrug(t, v) { // knockback on a mech: mostly ignored, and the speed check lets the rest through
      const k = v.map((x) => x * MECH.kbTake);
      t.mech.bank = Math.min(40, (t.mech.bank || 0) + Math.hypot(k[0], k[2]) * 0.8);
      if (k[1] > 0) t.mech.ub = Math.min(60, (t.mech.ub || 0) + k[1] * k[1] / (2 * MECH[t.mech.f].grav) + 0.3); // (and a pop upwards may go up)
      return k;
    },
    mechHitBoxes(t) { return this.mechOn(t) ? mechBoxes(t.pos, t.mech.f) : null; },
    // a gun's headshot on a mech is the cockpit: MECH.head instead of the gun's own head multiplier
    mechHeadMul(w, n, h) { return (n - h + h * MECH.head) / (n - h + h * (w.head || 1)); },
    mechNo(p, why) { if (!p.isBot) send(p, { t: 'mech', k: 'no', why }); },

    // ------------------------------------------------------------ calling it in (from 'deploy')
    // the marker: within range of your eyes, in plain sight, a floor under it, open sky over it. returns false (and
    // says why) to keep the streak in your tray
    mechCall(p, at, frame) {
      const n = now(), e = [p.pos[0], p.pos[1] + 1.6, p.pos[2]];
      if (this.mechOf(p)) { this.mechNo(p, 'your mech is already out'); return false; }
      if (!at) { this.mechNo(p, 'aim at the floor'); return false; }
      const d = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
      if (l > MECH.drop.range + 1) { this.mechNo(p, `too far (${MECH.drop.range} m max)`); return false; }
      if (l > 0.6 && raycast(e, [d[0] / l, d[1] / l, d[2] / l], l - 0.6, this.boxes)) { this.mechNo(p, "can't see there"); return false; }
      const fl = raycast([at[0], at[1] + 0.5, at[2]], [0, -1, 0], 4.5, this.boxes);
      if (!fl || fl.box.pad) { this.mechNo(p, 'no floor there'); return false; }
      const g = [at[0], fl.point[1], at[2]];
      if (this.map.seaY != null && this.map.seaY - g[1] > (this.map.wade || 1.5)) { this.mechNo(p, 'not into deep water'); return false; } // (a sea map: the floor under the water doesn't count)
      if (raycast([g[0], g[1] + 0.2, g[2]], [0, 1, 0], MECH.drop.sky, this.boxes)) { this.mechNo(p, 'it needs open sky'); return false; }
      const f = mechFrame(isFrame(frame) ? frame : p.mechFrame);
      const id = this.nextMech = (this.nextMech || 0) + 1;
      const yaw = Math.atan2(e[0] - g[0], e[2] - g[2]) + Math.PI; // facing the way you looked
      const m = { id, o: p.id, f, p: g, yaw: r2(yaw), st: 'fall', t: n, until: n + MECH.drop.delay * 1000, hp: MECH[f].hp };
      this.mechMap().set(id, m);
      this.broadcast({ t: 'mech', k: 'call', id, o: p.id, f, p: g.map(r2), yaw: m.yaw, ms: MECH.drop.delay * 1000 });
      return true;
    },
    // it lands: the shockwave (not through walls), anyone right on the marker squashed flat
    mechLand(m, n) {
      m.st = 'wait'; m.t = n; m.until = n + MECH.wait * 1000;
      const owner = this.players.get(m.o);
      this.broadcast({ t: 'mech', k: 'land', id: m.id, o: m.o, f: m.f, p: m.p.map(r2), yaw: m.yaw });
      const c = [m.p[0], m.p[1] + 0.6, m.p[2]];
      for (const t of this.players.values()) {
        if (!t.alive || t === owner || (owner && this.friendly(owner, t))) continue;
        const tc = center(t), dh = hdist(t.pos, m.p), dy = t.pos[1] - m.p[1];
        if (dh <= MECH.drop.squash && dy > -1 && dy < 3.5 && !this.mechOn(t)) { // right under it
          this.broadcast({ t: 'mech', k: 'squash', id: m.o, to: t.id, p: t.pos.map(r2) });
          this.hurt(t, owner || null, 'mechdrop', 999, [0, -4, 0]);
          continue;
        }
        const d = Math.hypot(tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]), h = dropHit(d);
        if (!h || !clear(c, tc, this.boxes)) continue;
        const out = dh > 0.2 ? [(t.pos[0] - m.p[0]) / dh, (t.pos[2] - m.p[2]) / dh] : [0, 0];
        this.hurt(t, owner || null, 'mechdrop', h.dmg, [out[0] * h.kb, h.up, out[1] * h.kb]);
      }
      if (owner && owner.isBot) setTimeout(safe('botmech', () => { if (this.players.get(owner.id) === owner && owner.alive && this.mechMap().get(m.id) === m && m.st === 'wait') { owner.pos = m.p.slice(); this.mechEnter(owner); } }), 500); // bots climb straight in (if it's still there: a reset may have cleared it)
    },
    mechGone(m, why = 'leave') {
      this.mechMap().delete(m.id);
      this.broadcast({ t: 'mech', k: 'gone', m: m.id, why });
      const o = this.players.get(m.o);
      if (o && this.isleOn) this.isleMechEnd(o); // battle island: it flew off: the meter restarts at 25%
      if (o && this.mode === 'training') (o.trainCd ||= {}).mechdrop = now() + 3000; // training: it's back in your tray 3 s after it's gone
    },

    // ------------------------------------------------------------ in / out
    mechEnter(p, n = now()) {
      const m = this.mechOf(p);
      if (!p.alive || !m || (m.st !== 'wait' && m.st !== 'idle') || p.mech) return false;
      if (p.rig || this.isBall(p) || p.ballUntil > n || p.trap || p.dn) { this.mechNo(p, 'not right now'); return false; } // (p.dn: battle island, down on the floor)
      if (hdist(p.pos, m.p) > MECH.reach + 0.5 || Math.abs(p.pos[1] - m.p[1]) > 3.5) { this.mechNo(p, 'get closer'); return false; }
      if (n < (m.backT || 0)) { this.mechNo(p, 'still climbing down'); return false; } // (no hop out + in to skip a cooldown)
      const F = MECH[m.f];
      m.st = 'in';
      p.pos = m.p.slice(); p.vel = [0, 0, 0]; p.yaw = m.yaw; p.g = null;
      if (p.ai) p.ai.hook = null;
      if (this.lassoDrop) this.lassoDrop(p, 'gone');
      p.mech = { on: true, id: m.id, f: m.f, E: m.E || newEnergy(n), cd: m.cd || {}, combo: { i: -1, t: 0 }, dash: null, jetUntil: 0, slam: null, blockT: 0, marks: null, // (energy + cooldowns live on the mech)
        last: p.pos.slice(), snapT: n, bank: MECH.slack, grace: n + 600, fixT: 0, minVy: 0, ramT: new Map(), stompT: new Map(), msg: { n: 0, t: n }, enT: 0,
        ub: hopUp(F), air: false, peak: p.pos[1], peakT: n, mv: null, mvA: { t: n, p: p.pos.slice() } };
      this.bodyStart(p, m.f);
      if (p.body) p.body.hp = Math.min(F.hp, m.hp);
      this.bodyFlush(p, true);
      this.broadcast({ t: 'mech', k: 'in', id: p.id, m: m.id, f: m.f, p: m.p.map(r2), yaw: m.yaw, hp: Math.round(p.body ? p.body.hp : m.hp), max: F.hp });
      this.mechEn(p, true);
      return true;
    },
    // out of it. why: 'hop' (F: it waits 10 s), 'boom' (armour broke or you died in it: it blows up), 'quiet' (round
    // over, mode change, left: it just goes)
    mechExit(p, why, by = null) {
      const M = p.mech;
      if (!M) return;
      const m = this.mechMap().get(M.id), F = MECH[M.f];
      const hp = p.body ? Math.max(0, p.body.hp) : 0;
      p.mech = null; p.f &= ~MECH_BITS;
      this.bodyClear(p);
      this.dronesOf(p.id, true);
      const at = p.pos.slice();
      if (why === 'hop' && m && hp > 0) {
        m.st = 'idle'; m.p = at; m.yaw = r2(p.yaw); m.hp = hp; m.t = now(); m.until = m.t + MECH.idle * 1000;
        m.E = M.E; m.cd = M.cd; m.backT = m.t + 1000;
        this.broadcast({ t: 'mech', k: 'out', id: p.id, m: M.id, why, p: at.map(r2), yaw: m.yaw, ms: MECH.idle * 1000 });
        const c = Math.cos(p.yaw), s = Math.sin(p.yaw);
        p.pos = this.mechOutSpot(at, [[c, -s], [-c, s], [s, c], [-s, -c]], 2.2); // you climb down off its side (one with no wall in the way)
        if (p.isBot) p.vel = [0, 4, 0]; else send(p, { t: 'mech', k: 'pos', p: p.pos.map(r2), v: [0, 6, 0] });
        return;
      }
      if (m) this.mechMap().delete(m.id);
      if (this.isleOn) this.isleMechEnd(p); // battle island: the meter restarts at 25% (server/islemeter.js)
      if (why !== 'boom') { this.broadcast({ t: 'mech', k: 'out', id: p.id, m: M.id, why: 'quiet', p: at.map(r2) }); return; }
      // EJECT! EJECT!: flung up and back out of the cockpit, the mech goes up behind you
      let back = [Math.sin(p.yaw), Math.cos(p.yaw)]; const B = MECH.boom;
      if (this.map.bounds && outOfBounds(this.map, [at[0] + back[0] * B.back * 1.4, 0, at[2] + back[1] * B.back * 1.4])) { // (backed up to the edge: fling them inwards, not out of the map)
        const c = boundsCenter(this.map), dx = c[0] - at[0], dz = c[1] - at[2], l = Math.hypot(dx, dz) || 1;
        back = [dx / l, dz / l];
      }
      const v = [back[0] * B.back, B.up, back[1] * B.back];
      if (p.alive) {
        p.pos = [at[0], at[1] + F.h * 0.8, at[2]]; // (mk_eject: out of the top of the chest)
        if (raycast([at[0], at[1] + 1, at[2]], [0, 1, 0], F.h * 0.8 + 0.6, this.boxes)) { const o = this.mechOutSpot(at, [back, [-back[0], -back[1]], [back[1], -back[0]], [-back[1], back[0]]], 2.5); p.pos = [o[0], o[1] + 0.3, o[2]]; } // (a roof over it: out the back instead)
        if (p.isBot) { p.vel = v.slice(); p.onGround = false; } else send(p, { t: 'mech', k: 'pos', p: p.pos.map(r2), v });
      }
      this.broadcast({ t: 'mech', k: 'down', id: p.id, m: M.id, f: M.f, by: by ? by.id : 0, p: at.map(r2), v: v.map(r2) });
      this.mechBlast(at, p, by);
    },
    // somewhere to climb out to: d m off in the first of dirs with no wall in the way (knee and head height), a floor
    // under it, inside the map. none of them: the mech's own spot
    mechOutSpot(at, dirs, d) {
      for (const [dx, dz] of dirs) {
        if (raycast([at[0], at[1] + 0.5, at[2]], [dx, 0, dz], d + 0.5, this.boxes) || raycast([at[0], at[1] + 1.7, at[2]], [dx, 0, dz], d + 0.5, this.boxes)) continue;
        const s = [at[0] + dx * d, at[1], at[2] + dz * d], fl = raycast([s[0], at[1] + 1.2, s[2]], [0, -1, 0], 4, this.boxes);
        if (!fl || fl.box.pad || (this.map.bounds && outOfBounds(this.map, s))) continue;
        return [s[0], fl.point[1] + 0.02, s[2]];
      }
      return at.slice();
    },
    // the blast: B.dmg in B.r, on everyone but the pilot, credited to whoever broke it
    mechBlast(at, pilot, by) {
      const B = MECH.boom, c = [at[0], at[1] + 1.5, at[2]];
      for (const t of this.players.values()) {
        if (!t.alive || t === pilot || t === by || this.friendly(by || pilot, t)) continue; // (nobody broke it, e.g. the zone: the pilot's own side is safe)
        const tc = center(t), d = Math.hypot(tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]);
        if (d > B.r || !clear(c, tc, this.boxes)) continue;
        const f = 1 - d / B.r, hl = Math.hypot(tc[0] - c[0], tc[2] - c[2]) || 1;
        this.hurt(t, by, 'mechboom', B.dmg * (0.5 + 0.5 * f), [(tc[0] - c[0]) / hl * 10 * f, 6 + 6 * f, (tc[2] - c[2]) / hl * 10 * f], { from: c });
      }
      this.mechBoom(c, B.r, B.dmg, by, 'mechboom', 0.5); // (and any empty mech next to it: chain reactions)
    },
    // bodyhp.js: the armour hit 0
    mechBroke(t, by) { this.mechExit(t, 'boom', by); },
    // kill(): died in it some other way (void, a train, lava): it blows up, the blast credited to your killer
    mechDeath(t, attacker) {
      if (!t.mech) return;
      const by = attacker && attacker !== t ? attacker : t.lastAttacker && now() - (t.lastAttackT || 0) < 10000 ? this.players.get(t.lastAttacker) || null : null;
      this.mechExit(t, 'boom', by);
    },
    mechLife(p) { if (p.mech) this.mechExit(p, 'quiet'); }, // resetLife: a new round / life ends it quietly
    mechLeave(p) { // disconnected: their mechs go with them
      if (p.mech) this.mechExit(p, 'quiet');
      for (const m of [...this.mechMap().values()]) if (m.o === p.id) this.mechGone(m, 'owner');
      this.dronesOf(p.id, true);
    },
    mechReset() { // a new round, map or mode: no mech anywhere
      for (const p of this.players.values()) if (p.mech) this.mechExit(p, 'quiet');
      for (const m of [...this.mechMap().values()]) this.mechGone(m, 'reset');
      if (this._drones) this._drones.clear();
    },

    // ------------------------------------------------------------ armour: the knight's shield first, then the pool
    mechSoak(t, amt, attacker, w, from) {
      const M = t.mech, n = now();
      if (!M || !this.mechOn(t, n) || !(amt > 0)) return amt;
      const src = attacker && attacker !== t ? attacker.pos : from;
      if (M.f === 'nightshift' && (t.f & MF.SHIELD) && src && inFront(t.yaw, t.pos, src, NS.shield.cos)) {
        const b = amt * NS.shield.cut;
        amt -= b; M.blockT = n;
        if (n - (M.blkT || 0) > 90) { M.blkT = n; this.broadcast({ t: 'mech', k: 'blk', id: t.id, a: Math.round(b), p: src.map(r2) }); }
      }
      M.hitT = n;
      if (w === 'zone' && this.isleOn) return this.bodySoak(t, amt * ISLE.zoneMech, attacker, 'islezone'); // battle island: the zone eats a mech's armour (its pilot's HP is safe)
      return this.bodySoak(t, amt, attacker, w);
    },

    // ------------------------------------------------------------ empty mechs take hits too
    // one waiting after it lands ('wait') or after a hop-out ('idle') is a target: its box (the frame's, cockpit = head),
    // judged here like any hit. its owner's squad / team can't touch it. the pilot climbs back into what's left, and at 0
    // it blows up like a broken mech: MECH DOWN, the blast credited to whoever broke it. (no more hopping out to save it)
    mechEmpty(m) { return !!m && (m.st === 'wait' || m.st === 'idle'); },
    mechEmpties() { const out = []; for (const m of this.mechMap().values()) if (this.mechEmpty(m)) out.push(m); return out; },
    mechCanHit(m, by) {
      if (!this.mechEmpty(m) || !by || !by.alive || (this.round && this.round.over)) return false;
      const o = this.players.get(m.o);
      return !!o && o !== by && !this.friendly(o, by);
    },
    // the frame as one box (+ grow on every side), and the middle of it
    mechBox(m, grow = 0) { const F = MECH[m.f]; return { min: [m.p[0] - F.hw - grow, m.p[1] - grow, m.p[2] - F.hw - grow], max: [m.p[0] + F.hw + grow, m.p[1] + F.h + grow, m.p[2] + F.hw + grow] }; },
    mechMid(m) { return [m.p[0], m.p[1] + MECH[m.f].h * 0.5, m.p[2]]; },
    // the closest spot on its box to c, and a line of sight to it (or its middle): nothing solid between
    mechNear(m, c) { const b = this.mechBox(m); return [0, 1, 2].map((i) => Math.max(b.min[i], Math.min(b.max[i], c[i]))); },
    mechSeen(m, c) { const q = this.mechNear(m, c); return clear(c, q, this.boxes) || clear(c, this.mechMid(m), this.boxes); },
    // the damage: off its armour (a single hit takes at most BODY.cap, like any pool). at 0: it blows up
    mechHarm(m, by, w, amt, hs, at) {
      if (!(amt > 0) || !this.mechCanHit(m, by)) return false;
      const F = MECH[m.f], a = Math.min(amt, BODY.cap), was = m.hp;
      m.hp = was - a; m.hitT = now(); m.by = by.id;
      if (this.isleOn) this.isleMeter(by, Math.min(a, Math.max(0, was)) * ISLE.meter.dmg, 'dmg'); // battle island: hurting a mech fills your meter (like a piloted one)
      this.broadcast({ t: 'mech', k: 'hurt', m: m.id, o: m.o, by: by.id, a: Math.round(a), hp: Math.max(0, Math.round(m.hp)), max: F.hp, hs: hs ? 1 : undefined, w, p: (at || this.mechMid(m)).map(r2) });
      if (m.hp <= 0) this.mechWreck(m, by);
      return true;
    },
    // broke while empty: the same MECH DOWN as a piloted one (feed, blast, credit), the owner's meter / streak as if it broke
    mechWreck(m, by) {
      if (this.mechMap().get(m.id) !== m) return;
      this.broadcast({ t: 'mech', k: 'down', id: m.o, m: m.id, f: m.f, by: by ? by.id : 0, p: m.p.map(r2), v: [0, 0, 0], e: 1 }); // (e: nobody inside)
      this.mechGone(m, 'boom'); // (gone before its blast: a chain of mechs can't loop)
      this.mechBlast(m.p, null, by);
    },
    // a gun or melee hit on an empty mech: 'hit' with mk (the mech's id) instead of to. the shot has to come from where
    // the server has you, at the rate your weapon fires, in range, pointing at the box, with no wall in between
    mechShot(p, m) {
      const n = now(), w = typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) && WEAPONS[m.w];
      const mm = Number.isInteger(m.mk) ? this.mechMap().get(m.mk) : null, d = norm(vec3(m.d));
      if (!w || !mm || !d || !p.alive || (w.kind !== 'hitscan' && w.kind !== 'melee') || p.w !== m.w) return;
      if (this.isBall(p) || n < (p.staggerUntil || 0) || !this.allowed(p, m.w) || (this.zm && !this.zmArm(p, m.w))) return;
      if (!this.mechCanHit(mm, p)) return;
      const melee = w.kind === 'melee', hv = melee && m.heavy === 1 && w.heavy ? w.heavy : null;
      const rate = melee ? 0 : Math.max(this.rateOf(m.w, w, p.hp), w.fanHammer ? w.fanHammer.rate : 0) * (w.hands || 1);
      const iv = melee ? (hv ? hv.cd : w.cd || 0.4) * 750 : 1000 / rate * 0.6;
      const T = p.mkT || (p.mkT = new Map()); // one clock per mech, whatever you hold: swapping guns can't add rates up
      if (n - (T.get(mm.id) || 0) < iv) return;
      if (T.size > 8) for (const k of T.keys()) if (!this.mechMap().has(k)) T.delete(k);
      T.set(mm.id, n);
      const e = [p.pos[0], p.pos[1] + PH.eye, p.pos[2]], slack = (melee ? 1.5 : 3) + Math.hypot(...p.vel) * 0.3; // (measured to its box, not its feet: less slack than a player gets)
      const reach = (melee ? (hv ? hv.range : w.range + (m.w === 'katana' ? (p.kat || 0) * (w.grow || 0) : 0)) : w.range || 200) + slack;
      const q = this.mechNear(mm, e), dq = Math.hypot(q[0] - e[0], q[1] - e[1], q[2] - e[2]);
      if (dq > reach) return;
      let at = q, head = false;
      if (melee) { // a swing: roughly toward it (or right up against it)
        const cone = Math.min(1.45, (hv ? hv.cone : w.cone || 0.6) + 0.35);
        if (dq > 1.5 && (d[0] * (q[0] - e[0]) + d[1] * (q[1] - e[1]) + d[2] * (q[2] - e[2])) / dq < Math.cos(cone)) return;
        if (!this.mechSeen(mm, e)) return;
      } else { // a bullet: its line has to pass through the box (a little slack for lag), with no wall before it
        const h = rayBox(e, d, this.mechBox(mm, 0.6 + Math.hypot(...p.vel) * 0.08), reach);
        if (!h) return;
        at = [e[0] + d[0] * h.t, e[1] + d[1] * h.t, e[2] + d[2] * h.t];
        if (h.t > 0.4 && raycast(e, d, h.t - 0.3, this.boxes)) return;
        head = at[1] >= mm.p[1] + MECH[mm.f].c0 && at[1] <= mm.p[1] + MECH[mm.f].c1;
      }
      let dmg;
      if (melee) dmg = hv ? hv.dmg : w.dmg;
      else {
        const pellets = w.pellets || 1, F = MECH[mm.f], R = (w.spread || 0) * dq * 0.7; // most pellets that could land on a box this size at this distance
        const most = pellets <= 1 ? 1 : Math.max(1, Math.min(pellets, Math.ceil(pellets * Math.min(1, (2 * F.hw * F.h) / (Math.PI * R * R || 1)) * 1.35 + 2)));
        const pit = { min: [mm.p[0] - F.hw - 0.6, mm.p[1] + F.c0 - 0.6, mm.p[2] - F.hw - 0.6], max: [mm.p[0] + F.hw + 0.6, mm.p[1] + F.c1 + 0.6, mm.p[2] + F.hw + 0.6] }; // the cockpit (+ lag slack)
        const cnt = Math.max(1, Math.min(most, Math.floor(Number(m.n)) || 1)), hs = rayBox(e, d, pit, reach) ? Math.max(0, Math.min(cnt, Math.floor(Number(m.h)) || 0)) : 0; // (a headshot has to be aimed at the cockpit)
        dmg = (w.fanHammer && m.fan === 1 ? w.fanHammer.dmg : w.dmg) * (cnt - hs + hs * MECH.head);
        head = hs > 0;
      }
      this.mechHarm(mm, p, m.w, dmg, head, at);
    },
    // anything thrown or fired that the server flies (arrows, bananas, chickens, cards...): true = it hit an empty mech
    mechProjHit(pr, prev, owner) {
      if (!owner || !this._mechs || !this._mechs.size) return false;
      const seg = [pr.p[0] - prev[0], pr.p[1] - prev[1], pr.p[2] - prev[2]], len = Math.hypot(...seg);
      if (len < 1e-6) return false;
      const dir = seg.map((x) => x / len);
      for (const m of this.mechEmpties()) {
        if (!this.mechCanHit(m, owner)) continue;
        const h = rayBox(prev, dir, this.mechBox(m, pr.r || 0.1), len + 1e-3);
        if (!h) continue;
        pr.p = [prev[0] + dir[0] * h.t, prev[1] + dir[1] * h.t, prev[2] + dir[2] * h.t];
        const w = WEAPONS[pr.k] || {};
        if (pr.k === 'chicken') { this.projectiles.delete(pr.id); this.explode(pr); return true; } // (explode() blasts the mech)
        if (pr.k === 'bow' || pr.k === 'card') {
          if (pr.tip !== 'explosion') this.mechHarm(m, owner, pr.k === 'bow' ? 'bow' : 'cards', pr.k === 'bow' ? 30 : pr.dmg ?? (WEAPONS.card ? WEAPONS.card.dmg : 9), false, pr.p);
          this.arrowHit(pr, owner, null); return true; // (an exploding tip blasts it instead)
        }
        this.mechHarm(m, owner, pr.k, (Number(w.dmg) || 10) * (pr.k === 'bowling' ? 2 : 1), false, pr.p);
        this.removeProj(pr, { b: 1 });
        return true;
      }
      return false;
    },
    // a blast (frags, chickens, rig missiles, a mech going up, a slam): every empty mech in r of c that it can see,
    // dmg at the middle down to k x dmg at the edge (measured to its box, not its feet)
    mechBoom(c, r, dmg, by, w, k = 0.3) {
      if (!by || !this._mechs || !this._mechs.size) return;
      for (const m of this.mechEmpties()) {
        if (!this.mechCanHit(m, by)) continue;
        const q = this.mechNear(m, c), d = Math.hypot(q[0] - c[0], q[1] - c[1], q[2] - c[2]);
        if (d > r || !this.mechSeen(m, c)) continue;
        this.mechHarm(m, by, w, dmg * (k + (1 - k) * (1 - d / r)), false, q);
      }
    },
    // a mech's own hitscan / arc / path vs empty mechs (the cannons, the sword, the bash, the lunge, triple shift)
    mechRayEmpty(p, o, d, range) {
      let best = null;
      for (const m of this.mechEmpties()) {
        if (!this.mechCanHit(m, p)) continue;
        const h = rayBox(o, d, this.mechBox(m), best ? best.t : range);
        if (h && (!best || h.t < best.t)) best = { m, t: h.t };
      }
      return best;
    },
    mechArcEmpty(p, reach, cos, w, dmg) {
      for (const m of this.mechEmpties()) {
        if (!this.mechCanHit(m, p) || !inArc(p.pos, p.yaw, m.p, reach + MECH[m.f].hw, cos, NS.h) || !this.mechSeen(m, this.mechCenter(p))) continue;
        this.mechHarm(m, p, w, dmg, false, this.mechNear(m, this.mechCenter(p)));
      }
    },

    // ------------------------------------------------------------ snapshots: flags + speed caps
    // the mech flags only count from someone really in one, and only for what the server agrees they're doing. then
    // the speed check: a budget of metres that fills at the cap for what you're doing (+ knockback, jump pads), and
    // each snapshot spends what you moved. overspend and you're put back where you last were fine
    mechSnap(p) {
      const M = p.mech, n = now();
      if (!M || !this.mechOn(p, n)) { p.f &= ~MECH_BITS; return; }
      const dt = Math.min(0.25, Math.max(0, (n - M.snapT) / 1000));
      M.snapT = n;
      let f = FLAGS.MECH;
      const want = p.f;
      if (M.f === 'paperplane') {
        if ((want & MF.HOVER) && energyAt(M.E, n) > 0 && n >= M.jetUntil) { f |= MF.HOVER; M.E.v = Math.max(0, M.E.v - PP.hover.drain * dt); M.E.t = n; if (M.E.v <= 0) this.mechEn(p, true); }
        if (n < M.jetUntil) f |= MF.JET;
        if (M.dash && n < M.dash.until) f |= MF.DASH;
      } else {
        if ((want & MF.SHIELD) && !(M.dash && n < M.dash.until) && !M.slam) { f |= MF.SHIELD; if (!M.shUp && n - (M.shT || 0) > 1000) { M.shT = n; M.bank += 2.5; } M.shUp = true; } else M.shUp = false; // (raising it: a moment to slow down)
        if (M.slam && n - M.slam.t < NS.slam.win * 1000) f |= MF.SLAM;
        if (M.dash && n < M.dash.until) f |= MF.SLASH;
      }
      p.f = (want & ~MECH_BITS) | f;
      // speed
      const F = MECH[M.f], pp = M.f === 'paperplane';
      const pos = p.pos, last = M.last, fl = raycast([last[0], last[1] + 0.3, last[2]], [0, -1, 0], 1.2, this.boxes);
      if (fl && fl.box.pad) { M.bank += Math.hypot(fl.box.pad[0], fl.box.pad[2]) * 1.5 + 4; M.ub = Math.max(M.ub, fl.box.pad[1] * fl.box.pad[1] / (2 * F.grav) + 2); } // a jump pad throws you
      const cap = speedCap(M.f, f) * 1.12, maxBank = MECH.slack + cap * 0.35;
      M.bank = Math.min(Math.max(maxBank, M.bank), M.bank + cap * dt);
      if (M.bank > maxBank) M.bank = Math.max(maxBank, M.bank - 6 * dt); // (knockback allowance drains back to normal)
      const moved = hdist(pos, last), rise = pos[1] - last[1];
      // just climbed in / just corrected: a snapshot from before that (far from where the server has you) is stale:
      // dropped, nothing gained. anything else is checked like always (a grace window is no free pass)
      if (n < M.grace && (moved > 3 || Math.abs(rise) > 3)) { p.pos = last.slice(); p.vel = [0, 0, 0]; return; }
      // going up: a budget of metres. a floor under you tops it up to a hop; hovering, the jet, the lunge pay for more
      // as they go (the slam, pads and knockback add theirs); climbing spends it. no flying without what pays for it
      if (pp && (f & MF.JET)) M.ub += PP.jet.speed * dt;
      else if (pp && (f & MF.DASH)) M.ub += PP.lunge.speed * dt;
      else if (pp && (f & MF.HOVER)) M.ub += PP.hover.up * 1.4 * dt;
      M.ub = Math.min(60, M.ub);
      M.bank -= moved;
      if (M.bank < -0.01 || rise > M.ub + 0.05) {
        p.pos = last.slice(); p.vel = [0, 0, 0];
        M.bank = 0; M.grace = n + 350; // (a correction gives nothing back: the budget refills at the cap from here)
        if (n - M.fixT > 300) { M.fixT = n; M.fixes = (M.fixes || 0) + 1; send(p, { t: 'mech', k: 'fix', p: last.map(r2), v: [0, 0, 0] }); }
        return;
      }
      if (rise > 0) M.ub -= rise;
      const hv = Math.hypot(p.vel[0], p.vel[2]);
      if (hv > cap + 2) { p.vel[0] *= cap / hv; p.vel[2] *= cap / hv; } // (what everyone else sees)
      M.last = pos.slice();
      // how fast it really goes (what rams count): measured from where the server has you, over ~0.15 s
      const A = M.mvA;
      if (n - A.t >= 150) { const s = (n - A.t) / 1000; M.mv = [(pos[0] - A.p[0]) / s, (pos[2] - A.p[2]) / s]; M.mvA = { t: n, p: pos.slice() }; }
      // landing: a stomp if it really came down from high enough (the height lost since it left the floor, over at
      // least about the time that fall takes), not whatever speed the client says
      if (raycast([pos[0], pos[1] + 0.3, pos[2]], [0, -1, 0], 0.9, this.boxes)) {
        if (M.air) { const drop = M.peak - pos[1]; if (drop >= MECH.stomp.vy * MECH.stomp.vy / (2 * F.grav) && n - M.peakT >= Math.sqrt(2 * drop / F.grav) * 500) this.mechStomp(p, n); }
        M.air = false; M.peak = pos[1]; M.peakT = n; M.ub = Math.max(M.ub, hopUp(F));
      } else { M.air = true; if (pos[1] >= M.peak) { M.peak = pos[1]; M.peakT = n; } } // (peak starts at the floor you left)
    },
    // energy + cooldowns to the pilot (their client predicts, this keeps it honest)
    mechEn(p, force) {
      const M = p.mech, n = now();
      if (!M || p.isBot || (!force && n - M.enT < 400)) return;
      M.enT = n;
      const cd = {};
      for (const [k, t] of Object.entries(M.cd)) if (t > n) cd[k] = Math.round(t - n);
      send(p, { t: 'mech', k: 'en', v: Math.round(energyAt(M.E, n)), cd, jet: M.jetUntil > n ? Math.round(M.jetUntil - n) : 0 });
    },
    mechCd(M, k, s, n) { if (n < (M.cd[k] || 0) - 150) return false; M.cd[k] = n + s * 1000; return true; },

    // ------------------------------------------------------------ client messages ({ t: 'mech', k })
    onMech(p, m) {
      const n = now();
      if (!p.alive || typeof m.k !== 'string' || m.k.length > 12) return;
      if (m.k === 'in') { if (n - (p.mechInT || 0) < 300) return; p.mechInT = n; if (!this.mechEnter(p, n) && !this.mechOf(p)) this.mechNo(p, 'no mech of yours here'); return; } // (a few a second at most)
      const M = p.mech;
      if (!M || !this.mechOn(p, n)) return;
      const q = M.msg; // rate limit (a busy pilot sends ~10 a second)
      if (n - q.t > 1000) { q.t = n; q.n = 0; }
      if (++q.n > MSG_PER_S) return;
      if (this.secStopped && this.secStopped(p, n) && m.k !== 'out') return; // tased / CLOCKED OUT: hands off everything
      if (m.k === 'out') { if (M.hitT && n - M.hitT < 1500) { this.mechNo(p, "can't hop out under fire"); return; } this.mechExit(p, 'hop'); return; } // (no dodging MECH DOWN)
      const pp = M.f === 'paperplane', d = norm(vec3(m.d));
      switch (m.k) {
        case 'gun': if (pp && d) this.mechGun(p, d, n); break;
        case 'lunge': if (pp) this.mechLunge(p, d, num(m.to), n); break;
        case 'crane': if (pp) this.mechCrane(p, num(m.to), n); break;
        case 'swarm': if (pp && d) this.mechSwarm(p, d, n); break;
        case 'jet': if (pp) this.mechJet(p, m.on === 1, n); break;
        case 'swing': if (!pp) this.mechSwing(p, n); break;
        case 'bash': if (!pp) this.mechBash(p, n); break;
        case 'triple': if (!pp) this.mechTriple(p, n); break;
        case 'slam': if (!pp) this.mechSlam(p, n); break;
        case 'slamland': if (!pp) this.mechSlamLand(p, vec3(m.p), n); break;
      }
    },
    // a shot's direction has to be roughly where the server has you looking (a snapshot old: some slack)
    mechAimOk(p, d, cos) { const l = lookOf(p); return l[0] * d[0] + l[1] * d[1] + l[2] * d[2] >= cos; },
    // the first body (or wall) along a ray: boxes of whoever's a mech are its frame + cockpit
    mechRay(p, o, d, range) {
      const wall = raycast(o, d, range, this.boxes);
      let best = wall ? wall.t : range, hit = null, head = false;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        for (const hb of this.mechHitBoxes(t) || playerBoxes(t.pos)) {
          const h = rayBox(o, d, hb, best);
          if (h && h.t < best) { best = h.t; hit = t; head = hb.head; }
        }
      }
      return { t: hit, head, at: [o[0] + d[0] * best, o[1] + d[1] * best, o[2] + d[2] * best] };
    },

    // ---- PAPER PLANE
    // twin cannons: a hitscan from the cockpit along your aim, alternating left / right barrel for the look
    mechGun(p, d, n) {
      const M = p.mech, G = PP.gun;
      if (n < M.jetUntil || n - (M.gunT || 0) < 1000 / G.rate * 0.7 || !this.mechAimOk(p, d, G.cone)) return;
      M.gunT = n; M.side = -(M.side || 1);
      const o = this.mechEyeOf(p), r = this.mechRay(p, o, d, G.range);
      const em = this.mechRayEmpty(p, o, d, Math.min(G.range, Math.hypot(r.at[0] - o[0], r.at[1] - o[1], r.at[2] - o[2]))); // an empty mech in front of whatever it hit
      if (em) { r.t = null; r.at = [o[0] + d[0] * em.t, o[1] + d[1] * em.t, o[2] + d[2] * em.t]; }
      this.broadcast({ t: 'mech', k: 'gun', id: p.id, s: M.side, b: r.at.map(r2), h: r.t || em ? 1 : 0 }, p.isBot ? undefined : p.id);
      if (r.t) this.hurt(r.t, p, 'mechgun', G.dmg * (r.head ? MECH.head : 1), [d[0] * 1.5, 0.5, d[2] * 1.5], { hs: r.head });
      else if (em) { const hd = r.at[1] >= em.m.p[1] + MECH[em.m.f].c0 && r.at[1] <= em.m.p[1] + MECH[em.m.f].c1; this.mechHarm(em.m, p, 'mechgun', G.dmg * (hd ? MECH.head : 1), hd, r.at); }
    },
    // boost lunge: locks the enemy nearest the crosshair (the client's pick if it holds up, else the server's own),
    // or just rockets straight. the path gets swept as you move (tickMech); what it deals repairs the mech
    mechLunge(p, d, to, n) {
      const M = p.mech, L = PP.lunge;
      if (M.dash && n < M.dash.until) return;
      if (!spend(M.E, L.cost, n)) { this.mechNo(p, 'no energy'); this.mechEn(p, true); return; }
      const e = this.mechEyeOf(p), look = d || lookOf(p);
      let t = to ? this.players.get(to) : null;
      if (t && !this.mechLockOk(p, t, e, look, L.lock + 3, L.cos - 0.08)) t = null;
      if (!t) t = this.mechPick(p, e, look, L.lock, L.cos);
      M.dash = { k: 'lunge', t0: n, until: n + (L.dist / L.speed) * 1000 + 250, prev: p.pos.slice(), hit: new Set(), to: t ? t.id : 0 };
      this.broadcast({ t: 'mech', k: 'lunge', id: p.id, to: t ? t.id : 0 });
      this.mechEn(p, true);
      return t;
    },
    mechLockOk(p, t, e, d, range, cos) {
      if (!t || t === p || !t.alive || this.friendly(p, t) || (this.bubbleBlocks && this.bubbleBlocks(p, t))) return false;
      const c = this.mechCenter(t), v = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]);
      return l <= range && l > 0.5 && (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l >= cos && clear(e, c, this.boxes);
    },
    // the enemy nearest the crosshair (cone around d, in range, in sight)
    mechPick(p, e, d, range, cos) {
      let best = null, bs = -1;
      for (const t of this.players.values()) {
        if (!this.mechLockOk(p, t, e, d, range, cos)) continue;
        const c = this.mechCenter(t), v = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], l = Math.hypot(v[0], v[1], v[2]);
        const s = (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / l - l * 0.002;
        if (s > bs) { bs = s; best = t; }
      }
      return best;
    },
    // the crane drone: peels off a wing, flies to them, pecks, flies home (tickDrones)
    mechCrane(p, to, n) {
      const M = p.mech, C = PP.crane, e = this.mechEyeOf(p), d = lookOf(p);
      let t = to ? this.players.get(to) : null;
      if (t && !this.mechLockOk(p, t, e, d, C.range + 3, C.cos - 0.1)) t = null;
      if (!t) t = this.mechPick(p, e, d, C.range, C.cos);
      if (!t) { this.mechNo(p, 'crane: no target'); return; }
      if (!this.mechCd(M, 'crane', C.cd, n)) return;
      const dr = { id: (this.nextDrone = (this.nextDrone || 0) + 1), o: p.id, to: t.id, p: [e[0] + 1.6, e[1], e[2]], ph: 'out', t: n, born: n, pecks: 0, sync: 0 };
      (this._drones ||= new Map()).set(dr.id, dr);
      this.broadcast({ t: 'mech', k: 'crane', id: p.id, d: dr.id, to: t.id, p: dr.p.map(r2) });
      this.mechEn(p, true);
    },
    dronesOf(id, kill) { if (!this._drones) return; for (const d of [...this._drones.values()]) if (d.o === id && kill) { this._drones.delete(d.id); this.broadcast({ t: 'mech', k: 'cranex', d: d.id }); } },
    tickDrones(n, dt) {
      if (!this._drones) return;
      const C = PP.crane;
      for (const dr of [...this._drones.values()]) {
        const o = this.players.get(dr.o), t = this.players.get(dr.to);
        if (!o || !this.mechOn(o, n) || n - dr.born > C.life * 1000) { this._drones.delete(dr.id); this.broadcast({ t: 'mech', k: 'cranex', d: dr.id }); continue; }
        if (dr.ph !== 'back' && (!t || !t.alive)) dr.ph = 'back';
        const goal = dr.ph === 'back' ? this.mechEyeOf(o) : (() => { const c = this.mechCenter(t); return [c[0], c[1] + 1.4, c[2]]; })();
        const v = [goal[0] - dr.p[0], goal[1] - dr.p[1], goal[2] - dr.p[2]], l = Math.hypot(v[0], v[1], v[2]);
        if (dr.ph === 'peck') { // hovering over them, pecking
          dr.p = goal;
          if (n >= dr.next && !clear(this.mechEyeOf(o), this.mechCenter(t), this.boxes)) dr.ph = 'back'; // (they ducked behind a wall: it gives up)
          else if (n >= dr.next) {
            dr.next = n + C.gap * 1000; dr.pecks++;
            this.broadcast({ t: 'mech', k: 'peck', d: dr.id, id: o.id, to: t.id, p: dr.p.map(r2) });
            this.hurt(t, o, 'mechcrane', C.dmg, [0, 1.5, 0]);
            if (dr.pecks >= C.pecks) dr.ph = 'back';
          }
        } else {
          const step = C.speed * dt;
          if (l <= step + 0.3) { if (dr.ph === 'out') { dr.ph = 'peck'; dr.next = n; } else { this._drones.delete(dr.id); this.broadcast({ t: 'mech', k: 'cranex', d: dr.id, home: 1 }); continue; } }
          else dr.p = [dr.p[0] + v[0] / l * step, dr.p[1] + v[1] / l * step, dr.p[2] + v[2] / l * step];
        }
        dr.sync -= dt;
        if (dr.sync <= 0) { dr.sync = 0.1; this.broadcast({ t: 'mech', k: 'cp', d: dr.id, p: dr.p.map(r2), ph: dr.ph }); }
      }
    },
    // the missile swarm: the rig's homing missiles (server/rig.js rigMissileStep), twelve of them, corkscrewing
    mechSwarm(p, d, n) {
      const M = p.mech, S = PP.swarm;
      if (n < M.jetUntil || !this.mechCd(M, 'swarm', S.cd, n)) return;
      const e = this.mechEyeOf(p), tg = this.rigTargets(p, e, d, S.cos, S.seek).slice(0, 3);
      this.broadcast({ t: 'mech', k: 'swarm', id: p.id, tg: tg.map((t) => t.id) });
      this.mechEn(p, true);
      const per = Math.ceil(S.n / S.kicks.length); // missile_salvo: each kick fires 2 pencils a side
      for (let i = 0; i < S.n; i++) {
        setTimeout(safe('mechmiss', () => {
          if (this.players.get(p.id) !== p || !this.mechOn(p)) return; // the pods went down with the mech
          const s = Math.sin(p.yaw), c = Math.cos(p.yaw), side = i % 2 ? 1 : -1, row = (i >> 1) % 3, F = MECH[p.mech.f];
          const fw = [-s, -c], rt = [c, -s];
          const pos = [p.pos[0] + rt[0] * side * 1.3 - fw[0] * 0.6, p.pos[1] + F.h * 0.86 + row * 0.12, p.pos[2] + rt[1] * side * 1.3 - fw[1] * 0.6];
          const out = 4 + Math.random() * 3, upv = 12 + Math.random() * 5;
          const vel = [rt[0] * side * out + fw[0] * 4 + p.vel[0] * 0.4, upv, rt[1] * side * out + fw[1] * 4 + p.vel[2] * 0.4];
          const pr = this.makeProj(p, 'mechmissile', pos, vel, { tg: tg.length ? tg[i % tg.length].id : 0, aim: d, seekT: 0, M: S, ph: Math.random() * 6.28 });
          pr.born = now();
        }), S.kicks[Math.min(S.kicks.length - 1, Math.floor(i / per))] * 1000 + (i % per) * 25);
      }
    },
    // one swarm missile, every tick: a corkscrew on top of the rig missile's homing (it turns back onto the target)
    mechMissileStep(pr, dt) {
      const S = PP.swarm, v = pr.v, sp = Math.hypot(v[0], v[1], v[2]);
      if (sp > 1 && (now() - pr.born) / 1000 > S.boost) {
        pr.ph += S.spin * dt;
        const f = [v[0] / sp, v[1] / sp, v[2] / sp], up = Math.abs(f[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0];
        const a = norm([f[1] * up[2] - f[2] * up[1], f[2] * up[0] - f[0] * up[2], f[0] * up[1] - f[1] * up[0]]) || [1, 0, 0];
        const b = [f[1] * a[2] - f[2] * a[1], f[2] * a[0] - f[0] * a[2], f[0] * a[1] - f[1] * a[0]];
        const k = S.wob * S.spin * dt * sp, cs = Math.cos(pr.ph), sn = Math.sin(pr.ph);
        for (let i = 0; i < 3; i++) v[i] += (a[i] * cs + b[i] * sn) * k;
      }
      this.rigMissileStep(pr, dt);
    },
    // jet mode: fold up and fly where you look for a few seconds (rams in tickMech). on: 1 starts it, 0 folds back early
    mechJet(p, on, n) {
      const M = p.mech, J = PP.jet;
      if (!on) { if (n < M.jetUntil) { M.jetUntil = n; this.broadcast({ t: 'mech', k: 'jet', id: p.id, on: 0 }); } return; }
      if (n < M.jetUntil || !this.mechCd(M, 'jet', J.cd + J.dur, n)) return;
      M.jetUntil = n + J.dur * 1000 + 150; M.jetHit = new Set(); M.bank += 10;
      this.broadcast({ t: 'mech', k: 'jet', id: p.id, on: 1, ms: J.dur * 1000 });
      this.mechEn(p, true);
    },

    // ---- NIGHT SHIFT
    // sword combo: three swings in a wide arc in front (from the server's own yaw), the third the big one
    mechSwing(p, n) {
      const M = p.mech, S = NS.sword, C = M.combo;
      if (M.slam || (M.dash && n < M.dash.until) || (p.f & MF.SHIELD)) return; // (shield up: no swinging behind it)
      const i = C.i >= 0 && C.i < 2 && n - C.t < S.combo * 1000 + S.cd[C.i] * 1000 ? C.i + 1 : 0;
      if (C.i >= 0 && n - C.t < S.cd[C.i] * 1000 - 120) return; // the last swing isn't through yet
      C.i = i; C.t = n;
      this.broadcast({ t: 'mech', k: 'swing', id: p.id, i });
      setTimeout(safe('mechswing', () => this.mechSwingHit(p, M, i)), S.hit[i] * 1000); // judged when the blade lands (sword_combo_N's hit frame)
    },
    mechSwingHit(p, M, i) {
      const S = NS.sword, n = now();
      if (this.players.get(p.id) !== p || !this.mechOn(p) || p.mech !== M) return;
      const fw = [-Math.sin(p.yaw), -Math.cos(p.yaw)];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        if (!inArc(p.pos, p.yaw, t.pos, S.reach + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.5), S.cos, NS.h)) continue;
        if (!clear(this.mechCenter(p), this.mechCenter(t), this.boxes)) continue;
        this.mechCut(p, t, 'mechsword', S.dmg[i], [fw[0] * S.kb[i], S.up[i], fw[1] * S.kb[i]], n);
      }
      this.mechArcEmpty(p, S.reach, S.cos, 'mechsword', S.dmg[i]);
    },
    // a sword hit (swing or triple shift): damage, and an overtime mark. the 4th clocks them out
    mechCut(p, t, w, dmg, kb, n) {
      const got = this.hurt(t, p, w, dmg, kb);
      this.broadcast({ t: 'mech', k: 'cut', id: p.id, to: t.id, p: this.mechCenter(t).map(r2), w });
      if (got !== t || !t.alive) return;
      const o = t.ot || (t.ot = { n: 0, until: 0, immune: 0 });
      if (addMark(o, n)) {
        const T = NS.overtime;
        this.stun(t, p, T.stun);
        this.broadcast({ t: 'mech', k: 'clock', id: p.id, to: t.id, ms: T.stun * 1000 });
      } else if (n >= o.immune) this.broadcast({ t: 'mech', k: 'mark', id: p.id, to: t.id, n: o.n, ms: NS.overtime.fade * 1000 });
    },
    // shield bash: let go of the shield right after it blocked something
    mechBash(p, n) {
      const M = p.mech, S = NS.shield;
      if (n - M.blockT > S.bashWin * 1000 || !this.mechCd(M, 'bash', S.bashCd, n)) return;
      M.blockT = 0;
      this.broadcast({ t: 'mech', k: 'bash', id: p.id });
      setTimeout(safe('mechbash', () => this.mechBashHit(p, M)), S.bashHit * 1000); // (shield_bash's hit frame)
    },
    mechBashHit(p, M) {
      const S = NS.shield;
      if (this.players.get(p.id) !== p || !this.mechOn(p) || p.mech !== M) return;
      const fw = [-Math.sin(p.yaw), -Math.cos(p.yaw)];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        if (!inArc(p.pos, p.yaw, t.pos, S.bashR + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.5), 0.35, NS.h)) continue;
        this.hurt(t, p, 'mechbash', S.bash, [fw[0] * S.bashKb, 9, fw[1] * S.bashKb]);
        this.broadcast({ t: 'mech', k: 'cut', id: p.id, to: t.id, p: this.mechCenter(t).map(r2), w: 'mechbash' });
      }
      this.mechArcEmpty(p, S.bashR, 0.35, 'mechbash', S.bash);
    },
    // TRIPLE SHIFT: three short dashing cuts; the client dashes, the server sweeps the path you really took (tickMech)
    mechTriple(p, n) {
      const M = p.mech, T = NS.triple;
      if ((M.dash && n < M.dash.until) || M.slam) return;
      if (!spend(M.E, T.cost, n)) { this.mechNo(p, 'no energy'); this.mechEn(p, true); return; }
      M.dash = { k: 'triple', t0: n, until: n + (T.lead + T.gap * (T.n - 1) + T.len) * 1000 + 300, prev: p.pos.slice(), hit: new Map() };
      this.broadcast({ t: 'mech', k: 'triple', id: p.id });
      this.mechEn(p, true);
    },
    // ground slam: up, then down. the landing (slamland) has to come from that jump, near where the server has you, on a floor
    mechSlam(p, n) {
      const M = p.mech, S = NS.slam;
      if (M.slam || !this.mechCd(M, 'slam', S.cd, n)) return;
      M.slam = { t: n, top: p.pos[1] };
      M.ub = Math.max(M.ub, NS.slam.up * NS.slam.up / (2 * NS.grav) + 1.5); // (the jump up is allowed)
      this.broadcast({ t: 'mech', k: 'slam', id: p.id });
      this.mechEn(p, true);
    },
    mechSlamLand(p, at, n) {
      const M = p.mech, S = NS.slam, Sl = M.slam;
      if (!Sl || n - Sl.t < 250) return;
      M.slam = null;
      if (n - Sl.t > S.win * 1000) return;
      if (!at || hdist(at, p.pos) > 4 + Math.hypot(p.vel[0], p.vel[2]) * 0.15 || Math.abs(at[1] - p.pos[1]) > 4) at = p.pos.slice();
      const fl = raycast([at[0], at[1] + 0.6, at[2]], [0, -1, 0], 3, this.boxes);
      if (!fl) return;
      const c = [at[0], fl.point[1] + 0.5, at[2]];
      this.broadcast({ t: 'mech', k: 'quake', id: p.id, p: [r2(at[0]), r2(fl.point[1]), r2(at[2])], r: S.r });
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const tc = center(t), to = [tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]], d = Math.hypot(to[0], to[1], to[2]);
        if (d > S.r || !clear(c, tc, this.boxes)) continue;
        const f = 1 - d / S.r, hl = Math.hypot(to[0], to[2]), out = hl > 0.2 ? [to[0] / hl, to[2] / hl] : [0, 0];
        this.hurt(t, p, 'mechslam', S.dmg * (0.35 + 0.65 * f), [out[0] * S.kb * (0.5 + f), S.kbUp * (0.6 + 0.4 * f), out[1] * S.kb * (0.5 + f)]);
      }
      this.mechBoom(c, S.r, S.dmg, p, 'mechslam', 0.35);
      this.mechStomp(p, n);
    },

    // ---- both
    // stomp: coming down on someone squashes them flat (knocked flat on the floor like a sleep arrow: the camera drops)
    mechStomp(p, n) {
      const F = MECH[p.mech.f];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        const dy = t.pos[1] - p.pos[1];
        if (hdist(t.pos, p.pos) > F.hw + 0.45 || dy < -2.4 || dy > 0.9 || n < (p.mech.stompT.get(t.id) || 0)) continue;
        p.mech.stompT.set(t.id, n + 1000); // (once a second each: no stomp spam)
        if (!this.mechOn(t)) this.sleep(t, p, MECH.stomp.flat);
        this.hurt(t, p, 'mechstomp', MECH.stomp.dmg, [0, -2, 0]);
        this.broadcast({ t: 'mech', k: 'stomp', id: p.id, to: t.id, p: t.pos.map(r2), ms: MECH.stomp.flat * 1000 });
      }
    },
    // every tick, per pilot: the dash / jet sweeps, rams, a bot's plan
    tickMech(n, dt) {
      for (const m of [...this.mechMap().values()]) {
        if (!this.players.has(m.o)) { this.mechGone(m, 'owner'); continue; }
        if (m.st === 'fall' && n >= m.until) this.mechLand(m, n);
        else if ((m.st === 'wait' || m.st === 'idle') && n >= m.until) this.mechGone(m, 'leave');
        else if (m.st === 'in') { const o = this.players.get(m.o); if (!o.mech || o.mech.id !== m.id) this.mechGone(m, 'leave'); }
      }
      this.tickDrones(n, dt);
      if (n - (this.mechListT || 0) > 1000 && this.mechMap().size) { // late joiners (and anyone who missed an event) catch up
        this.mechListT = n;
        this.broadcast({ t: 'mech', k: 'list', m: [...this.mechMap().values()].map((m) => [m.id, m.o, m.f, ...m.p.map(r2), m.yaw, m.st, Math.round(m.until - n), Math.max(0, Math.round(m.hp)), MECH[m.f].hp]) }); // (+ armour: the bar over a damaged empty one)
      }
      for (const p of this.players.values()) {
        const M = p.mech;
        if (!M) continue;
        if (!p.alive) { this.mechExit(p, 'quiet'); continue; } // (kill() blows it up first; this is a safety net)
        if (M.dash) this.mechSweep(p, M, n);
        if (n < M.jetUntil) this.mechJetRam(p, M, n);
        else if (!(M.dash && n < M.dash.until)) this.mechRam(p, M, n);
        if (M.slam && n - M.slam.t > NS.slam.win * 1000 + 500) M.slam = null;
        this.mechEn(p, false);
      }
    },
    // the lunge / triple shift: whoever the mech's path passes gets cut (from where the server has it: snapshots for
    // players, its own steps for bots). the lunge repairs the mech by half of what it deals
    mechSweep(p, M, n) {
      const D = M.dash, F = MECH[M.f];
      if (n > D.until) { M.dash = null; return; }
      const a = [D.prev[0], D.prev[1] + F.h * 0.45, D.prev[2]], b = [p.pos[0], p.pos[1] + F.h * 0.45, p.pos[2]];
      D.prev = p.pos.slice();
      const L = PP.lunge, T = NS.triple, lunge = D.k === 'lunge';
      const r = (lunge ? L.r : T.r) + F.hw * 0.5;
      const cut = lunge ? 0 : Math.min(T.n - 1, Math.max(0, Math.floor((n - D.t0 - T.lead * 1000) / (T.gap * 1000))));
      const dir = norm([b[0] - a[0], 0, b[2] - a[2]]) || [-Math.sin(p.yaw), 0, -Math.cos(p.yaw)];
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t)) continue;
        if (lunge ? D.hit.has(t.id) : (D.hit.get(t.id) ?? -1) >= cut) continue;
        const tc = this.mechCenter(t);
        if (segDist(a, b, tc) > r + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.6) || !clear(b, tc, this.boxes)) continue;
        if (lunge) {
          D.hit.add(t.id);
          const hp0 = this.mechOn(t) && t.body ? t.body.hp : t.hp, got = this.hurt(t, p, 'mechlunge', L.dmg, [dir[0] * L.kb, L.kbUp, dir[2] * L.kb]);
          const dealt = got === t ? Math.max(0, hp0 - (this.mechOn(t) && t.body ? t.body.hp : t.alive ? t.hp : 0)) : 0;
          this.broadcast({ t: 'mech', k: 'cut', id: p.id, to: t.id, p: tc.map(r2), w: 'mechlunge' });
          if (dealt > 0 && p.body) { p.body.hp = Math.min(p.body.max, p.body.hp + dealt * L.heal); this.bodyFlush(p, true); this.broadcast({ t: 'mech', k: 'heal', id: p.id, a: Math.round(dealt * L.heal) }); }
        } else {
          D.hit.set(t.id, cut);
          this.mechCut(p, t, 'mechtriple', T.dmg, [dir[0] * T.kb, 5, dir[2] * T.kb], n);
        }
      }
      for (const m of this.mechEmpties()) { // empty mechs in the way: a cut each (once per lunge, once per triple-shift cut)
        const k = 'm' + m.id, mc = this.mechMid(m);
        if (!this.mechCanHit(m, p) || (lunge ? D.hit.has(k) : (D.hit.get(k) ?? -1) >= cut) || segDist(a, b, mc) > r + MECH[m.f].hw || !this.mechSeen(m, b)) continue;
        if (lunge) D.hit.add(k); else D.hit.set(k, cut);
        this.mechHarm(m, p, lunge ? 'mechlunge' : 'mechtriple', lunge ? L.dmg : T.dmg, false, mc);
      }
    },
    // jet ram: anyone the jet passes through gets it once a jet, and flies
    mechJetRam(p, M, n) {
      const J = PP.jet, c = this.mechCenter(p), v = p.vel, sp = Math.hypot(v[0], v[1], v[2]) || 1;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t) || M.jetHit.has(t.id)) continue;
        const tc = this.mechCenter(t);
        if (Math.hypot(tc[0] - c[0], tc[1] - c[1], tc[2] - c[2]) > J.r + (this.mechOn(t) ? MECH[t.mech.f].hw : 0.6)) continue;
        M.jetHit.add(t.id);
        this.hurt(t, p, 'mechjet', J.dmg, [v[0] / sp * J.kb, J.kbUp, v[2] / sp * J.kb]);
        this.broadcast({ t: 'mech', k: 'ram', id: p.id, to: t.id, p: tc.map(r2), big: 1 });
      }
    },
    // walking into people at speed shoves them (faster = harder)
    mechRam(p, M, n) {
      const F = MECH[M.f], v = p.isBot ? [p.vel[0], p.vel[2]] : M.mv && n - M.snapT < 300 ? M.mv : [0, 0]; // (a player's: measured, not what the client claims)
      const hs = Math.hypot(v[0], v[1]), h = ramHit(hs);
      if (!h) return;
      const fx = v[0] / hs, fz = v[1] / hs;
      for (const t of this.players.values()) {
        if (t === p || !t.alive || this.friendly(p, t) || n < (M.ramT.get(t.id) || 0)) continue;
        const dx = t.pos[0] - p.pos[0], dz = t.pos[2] - p.pos[2], l = Math.hypot(dx, dz), dy = t.pos[1] - p.pos[1];
        if (l > F.hw + 0.7 || dy < -1.8 || dy > F.h * 0.7 || (l > 0.3 && (dx * fx + dz * fz) / l < 0.3)) continue;
        M.ramT.set(t.id, n + MECH.ram.cd * 1000);
        this.hurt(t, p, 'mechram', h.dmg, [fx * h.kb, h.up, fz * h.kb]);
        this.broadcast({ t: 'mech', k: 'ram', id: p.id, to: t.id, p: center(t).map(r2) });
      }
    },

    // ------------------------------------------------------------ bots
    // a bot that earns it calls it in a few metres ahead of itself (near the fight) and climbs in when it lands
    mechBotEarn(b) {
      if (this.mechOf(b) || b.mech) return;
      const mk = this.cfg.map, rd = this.round;
      setTimeout(safe('botmech', () => {
        if (this.players.get(b.id) !== b || !b.alive || b.rig || b.mech || this.isBall(b) || (this.round && this.round.over) || this.cfg.map !== mk || this.round !== rd) return; // (not after a map / round change)
        const env = process.env.JF_MECH_FRAME, f = isFrame(env) ? env : Math.random() < 0.5 ? 'paperplane' : 'nightshift';
        const fw = [-Math.sin(b.yaw), -Math.cos(b.yaw)];
        for (const k of [5, 2.5, 0]) {
          const at = [b.pos[0] + fw[0] * k, b.pos[1] + 0.3, b.pos[2] + fw[1] * k];
          if (this.mechCall(b, at, f)) { this.broadcast({ t: 'chat', id: 0, m: `${b.name} used Mech Drop` }); return; }
        }
      }), 700);
    },
    // a bot in a mech: its own movement and a little plan per frame (PLAY.md). every hit goes through the same checks
    // as a player's
    mechBotStep(b, think, dt, n) {
      const M = b.mech, F = MECH[M.f], v = b.vel, ai = b.ai, pp = M.f === 'paperplane';
      b.g = null; ai.hook = null;
      let t = this.players.get(ai.target);
      if (t && (!t.alive || this.friendly(b, t))) t = null;
      const e = this.mechEyeOf(b), tc = t ? this.mechCenter(t) : null, dv = t ? [tc[0] - e[0], tc[1] - e[1], tc[2] - e[2]] : null;
      const dist = t ? Math.hypot(dv[0], dv[1], dv[2]) : 1e9, flat = t ? Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]) : 1e9;
      const vis = !!(t && clear(e, tc, this.boxes));
      if (t) { b.yaw = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])); b.pitch = Math.atan2(dv[1], Math.hypot(dv[0], dv[2])); }
      const look = lookOf(b), easy = ai.diff === 'easy' ? 0.5 : 1, B = M.bai || (M.bai = { shieldT: 0, nextGun: 0 });
      const floorY = (() => { const h = raycast([b.pos[0], b.pos[1] + 0.3, b.pos[2]], [0, -1, 0], 60, this.boxes); return h ? h.point[1] : -1e9; })();
      const hitNow = M.hitT && n - M.hitT < 400;
      let f = FLAGS.MECH, wx = 0, wz = 0, sp = F.speed;
      if (t) { const l = flat || 1; wx = (t.pos[0] - b.pos[0]) / l; wz = (t.pos[2] - b.pos[2]) / l; }
      else { wx = think.wx; wz = think.wz; }
      if (pp) {
        // ---- PAPER PLANE: hangs at mid height, cannons, swarm, crane, lunges in close, jets in from far
        if (t && flat < 14) { const ox = wx; wx = -wz * 0.8 + ox * 0.2; wz = ox * 0.8 + wz * 0.2; } // circle-strafe close up (not into their face)
        if (vis && dist < PP.gun.range && n >= B.nextGun) {
          B.nextGun = n + 1000 / PP.gun.rate + (ai.diff === 'easy' ? 120 : 0);
          const err = ai.diff === 'hard' ? 0.02 : ai.diff === 'easy' ? 0.08 : 0.045;
          this.mechGun(b, norm([dv[0] / dist + (Math.random() - 0.5) * err * 2, dv[1] / dist + (Math.random() - 0.5) * err * 2, dv[2] / dist + (Math.random() - 0.5) * err * 2]), n);
        }
        if (vis && dist > 10 && dist < PP.swarm.seek && n >= (M.cd.swarm || 0) && Math.random() < dt * 1.5 * easy) this.mechSwarm(b, look, n);
        if (vis && dist < PP.crane.range && n >= (M.cd.crane || 0) && Math.random() < dt * easy) this.mechCrane(b, t.id, n);
        if (vis && dist > 5 && dist < PP.lunge.lock && !M.dash && energyAt(M.E, n) > 45 && Math.random() < dt * 0.8 * easy) {
          const tg = this.mechLunge(b, look, t.id, n);
          if (tg) M.bdash = { dir: norm([dv[0], dv[1] * 0.4, dv[2]]) || look, until: n + Math.min(PP.lunge.dist, dist) / PP.lunge.speed * 1000 };
        }
        if (t && flat > 28 && n >= (M.cd.jet || 0) && n >= M.jetUntil && Math.random() < dt * 0.5 * easy) this.mechJet(b, true, n);
        if (n < M.jetUntil) { // flying in at them: a ram, then fold back up
          const d = t ? norm([tc[0] - b.pos[0], tc[1] - b.pos[1] - 1, tc[2] - b.pos[2]]) || look : look;
          v[0] = d[0] * PP.jet.speed; v[1] = d[1] * PP.jet.speed; v[2] = d[2] * PP.jet.speed; f |= MF.JET;
          if ((M.jetHit && M.jetHit.size) || !t) this.mechJet(b, false, n);
        } else if (M.bdash && n < M.bdash.until) {
          const d = M.bdash.dir; v[0] = d[0] * PP.lunge.speed; v[1] = d[1] * PP.lunge.speed; v[2] = d[2] * PP.lunge.speed; f |= MF.DASH;
        } else {
          if (M.bdash) { M.bdash = null; v[0] *= 0.3; v[2] *= 0.3; v[1] = Math.min(v[1], 3); }
          const above = b.pos[1] - floorY, en = energyAt(M.E, n);
          const hover = (B.hover ? en > 2 : en > 40) && t && (above < 7 || floorY < this.map.killY + 1) && !(above > 9);
          B.hover = hover;
          if (hover) { M.E.v = Math.max(0, en - PP.hover.drain * dt); M.E.t = n; v[1] += ((above < 6 ? PP.hover.up : 0) - v[1]) * Math.min(1, dt * 4); f |= MF.HOVER; sp = PP.hover.speed; }
          else v[1] -= F.grav * dt;
          this.mechBotWalk(b, v, wx, wz, sp, F, dt, hover);
        }
      } else {
        // ---- NIGHT SHIFT: walks at you, shield up when shot, triple shift to close, slam a crowd, swing in reach
        if (hitNow && t && flat > 7) B.shieldT = n + 1200;
        const shield = n < B.shieldT && !M.dash && !M.slam;
        if (shield) { f |= MF.SHIELD; sp *= NS.shield.slow; }
        const near = [...this.players.values()].filter((o) => o !== b && o.alive && !this.friendly(b, o) && hdist(o.pos, b.pos) < 7).length;
        if (!M.slam && b.onGround && n >= (M.cd.slam || 0) && (near >= 2 || (near === 1 && Math.random() < dt * 0.3 * easy))) { this.mechSlam(b, n); v[1] = NS.slam.up; b.onGround = false; b.pos[1] += 0.05; }
        else if (t && vis && !M.dash && !M.slam && flat > 6 && flat < 16 && energyAt(M.E, n) >= NS.triple.cost && Math.random() < dt * 0.9 * easy) { this.mechTriple(b, n); M.bt = { t0: n }; }
        else if (t && flat < NS.sword.reach + 0.5 && !M.dash && !M.slam && n - M.combo.t > NS.sword.cd[Math.max(0, M.combo.i)] * 1000 + (ai.diff === 'easy' ? 250 : 60)) { this.mechSwing(b, n); }
        if (M.slam) {
          f |= MF.SLAM;
          if (v[1] < 0) v[1] = -NS.slam.down; else v[1] -= F.grav * dt;
          this.mechBotWalk(b, v, wx, wz, sp * 0.6, F, dt, false);
          if (b.onGround) this.mechSlamLand(b, b.pos.slice(), n);
        } else if (M.bt && M.dash && n < M.dash.until) { // the three dashes: dash, stop, dash, stop, dash
          const k = (n - M.bt.t0) / 1000 - NS.triple.lead, inDash = k >= 0 && k % NS.triple.gap < NS.triple.len;
          const d = t ? norm([t.pos[0] - b.pos[0], 0, t.pos[2] - b.pos[2]]) || look : look;
          if (inDash) { v[0] = d[0] * NS.triple.speed; v[2] = d[2] * NS.triple.speed; } else { v[0] *= 0.5; v[2] *= 0.5; }
          v[1] -= F.grav * dt; f |= MF.SLASH;
          this.mechBotMove(b, v, dt);
        } else {
          M.bt = null;
          v[1] -= F.grav * dt;
          if (b.onGround && t && t.pos[1] - b.pos[1] > 2.5 && flat < 20 && Math.random() < dt * 2) { v[1] = F.hop; b.onGround = false; }
          this.mechBotWalk(b, v, wx, wz, flat < 3.5 ? 0 : sp, F, dt, false);
        }
      }
      b.f = f;
      if (v[1] < M.minVy) M.minVy = v[1];
      if (b.onGround && M.minVy < MECH.stomp.vy) { M.minVy = 0; this.mechStomp(b, n); }
      else if (b.onGround) M.minVy = 0;
      if (b.onGround) b.ground = b.pos.slice();
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    },
    // heavy ground movement toward (wx, wz) at sp, then the move
    mechBotWalk(b, v, wx, wz, sp, F, dt, air) {
      const wl = Math.hypot(wx, wz);
      if (wl) { wx /= wl; wz /= wl; }
      const hs = Math.hypot(v[0], v[2]);
      if (b.onGround || air) {
        if (hs > 0) { const ns = Math.max(0, hs - Math.max(hs, 3) * F.fric * (wl ? 0.45 : 1) * dt) / hs; v[0] *= ns; v[2] *= ns; }
        if (wl) { const cur = v[0] * wx + v[2] * wz, add = sp - cur; if (add > 0) { const a = Math.min(add, F.accel * sp * dt); v[0] += a * wx; v[2] += a * wz; } }
      }
      this.mechBotMove(b, v, dt);
    },
    mechBotMove(b, v, dt) {
      const res = movePlayer(b.pos, v, dt, this.boxes, b.onGround);
      b.onGround = !!res.ground && v[1] <= 0.01;
      if (b.onGround) v[1] = 0;
      if (b.onGround && res.ground.pad) { const pd = res.ground.pad; v[0] += pd[0]; v[1] = pd[1]; v[2] += pd[2]; b.onGround = false; }
      if (res.wall && b.mech && b.mech.bdash) { b.mech.bdash = null; v[0] *= 0.3; v[2] *= 0.3; }
    },
  });
}
