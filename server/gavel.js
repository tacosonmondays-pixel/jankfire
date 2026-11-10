// Scales of Justice, ranged: the SUMMONS (shared/weapons.js GAVEL). Mixed into Room by installGavel. The server picks
// where the ring opens, keeps the recharge, and when the pillar lands works out who is still in it and what they
// deserve (verdictOf, the same court as a swing). Bots holding the scales use it too.
import { WEAPONS, GAVEL } from '../shared/weapons.js';

let H; // helpers from room.js (now, send, raycast, eyeOf, lookOf, norm, vec3, r2, center)

export function installGavel(Room, helpers) {
  H = helpers;
  const P = Room.prototype, o = { handle: P.handle, tickGear: P.tickGear, ggKill: P.ggKill };
  Object.assign(P, gavel, {
    handle(p, m) {
      if (m && m.t === 'gavel') { this.onGavel(p, m); return; }
      return o.handle.call(this, p, m);
    },
    tickGear(n) { o.tickGear.call(this, n); this.tickGavels(n); },
    // gun game: a summons kill moves you up the scales' rung like a swing would (and, not being a melee hit, humiliates nobody)
    ggKill(t, killer, kw) {
      const L = this.ggL(), i = killer ? killer.gg || 0 : -1;
      if (kw !== 'gavel' || !killer || L[i] !== 'scales') return o.ggKill.call(this, t, killer, kw);
      L[i] = 'gavel'; // for the length of this one call: the rung matches the kill
      try { return o.ggKill.call(this, t, killer, kw); } finally { L[i] = 'scales'; }
    },
  });
}

const gavel = {
  // {t:'gavel', o, d}: right click with the scales out
  onGavel(p, m) {
    const n = H.now();
    if (!p.alive || p.w !== 'scales' || !this.allowed(p, 'scales') || p.trap || p.quiz || (this.round && this.round.over)) return;
    if (this.rigOn(p) || this.isBall(p) || (this.isEcon && this.isEcon()) || this.zm) return; // bodies with no hands; modes that don't have the scales
    if (n < (p.gavelT || 0)) { H.send(p, { t: 'gavel', cd: p.gavelT - n }); return; }
    let o = H.vec3(m.o);
    const eye = H.eyeOf(p);
    if (!o || Math.hypot(o[0] - eye[0], o[1] - eye[1], o[2] - eye[2]) > 4) o = eye;
    const d = H.norm(H.vec3(m.d)) || H.lookOf(p);
    this.castGavel(p, o, d, n);
  },
  castGavel(p, o, d, n) {
    // whoever is nearest the aim, in range and in sight; otherwise the ground where they point
    let best = null, bd = Math.cos(GAVEL.cone);
    for (const t of this.players.values()) {
      if (t === p || !t.alive || this.friendly(p, t)) continue;
      const to = [t.pos[0] - o[0], t.pos[1] + 1.1 - o[1], t.pos[2] - o[2]], dist = Math.hypot(...to);
      if (dist > GAVEL.range || dist < 0.01) continue;
      const dot = (to[0] * d[0] + to[1] * d[1] + to[2] * d[2]) / dist;
      if (dot < bd) continue;
      const wall = H.raycast(o, to.map((x) => x / dist), dist, this.boxes);
      if (wall && wall.t < dist - 0.6) continue;
      best = t; bd = dot;
    }
    let at = best ? best.pos.slice() : null;
    if (!at) { const h = H.raycast(o, d, GAVEL.range, this.boxes); if (h) at = [o[0] + d[0] * h.t, o[1] + d[1] * h.t, o[2] + d[2] * h.t]; }
    if (!at) { if (!p.isBot) H.send(p, { t: 'gavel', no: 1 }); return false; } // pointed at the sky: nothing to stand a court on
    const g = H.raycast([at[0], at[1] + 0.6, at[2]], [0, -1, 0], 12, this.boxes); // drop the ring onto the floor under that point
    if (g) at[1] = at[1] + 0.6 - g.t;
    p.gavelT = n + GAVEL.cd * 1000;
    const id = (this.nextGavel = (this.nextGavel || 0) + 1);
    (this.gavels ||= new Map()).set(id, { id, o: p.id, p: at.map(H.r2), at: n + GAVEL.delay * 1000 });
    this.broadcast({ t: 'fx', k: 'gavel', gid: id, id: p.id, to: best ? best.id : 0, p: at.map(H.r2), r: GAVEL.r, d: GAVEL.delay });
    if (!p.isBot) H.send(p, { t: 'gavel', cd: GAVEL.cd * 1000, ok: 1 });
    return true;
  },
  tickGavels(n) {
    if (this.gavels && this.gavels.size) for (const g of [...this.gavels.values()]) {
      if (n < g.at) continue;
      this.gavels.delete(g.id);
      const owner = this.players.get(g.o);
      const hit = [];
      if (owner && !(this.round && this.round.over)) for (const v of [...this.players.values()]) {
        if (v === owner || !v.alive || this.friendly(owner, v)) continue;
        if (Math.hypot(v.pos[0] - g.p[0], v.pos[2] - g.p[2]) > GAVEL.r || v.pos[1] - g.p[1] > GAVEL.h || g.p[1] - v.pos[1] > 1.5) continue;
        const vd = this.verdictOf(owner, v), hp0 = v.hp;
        this.hurt(v, owner, 'gavel', GAVEL.dmg * vd.mult, [0, GAVEL.kbUp, 0]);
        if (v.hp < hp0) { hit.push(v.id); this.broadcast({ t: 'fx', k: 'verdict', id: v.id, by: owner.id, m: vd.mult, g: vd.g, one: 0, p: H.center(v).map(H.r2) }); }
      }
      this.broadcast({ t: 'fx', k: 'gavelx', gid: g.id, p: g.p, r: GAVEL.r, hit });
    }
    // bots on the scales (gun game's rung, mostly): summon whoever they're walking at but can't reach yet
    for (const b of this.players.values()) {
      if (!b.isBot || !b.alive || b.w !== 'scales' || !b.ai || b.ai.dummy || n < (b.gavelT || 0) || n < (b.ai.gavelNext || 0)) continue;
      b.ai.gavelNext = n + 400;
      const t = this.players.get(b.ai.target);
      if (!t || !t.alive || !b.ai.seenAt || this.zm || (this.isEcon && this.isEcon())) continue;
      const e = H.eyeOf(b), to = [t.pos[0] - e[0], t.pos[1] + 1.1 - e[1], t.pos[2] - e[2]], dist = Math.hypot(...to);
      if (dist < 6 || dist > GAVEL.range * 0.85) continue;
      this.castGavel(b, e, to.map((x) => x / dist), n);
    }
  },
};
