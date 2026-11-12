// The Wrecking Ball and the Overdrive Rig last until they BREAK (numbers + why: shared/bodyhp.js). The server owns each
// pool: p.body = { kind, hp, max }. damage() hands hits to bodySoak while you're in one (the rig's front block cuts first,
// in rigSoak), the pool drains a little every second, and at 0 bodyBreak ends the streak: a knock, the break for
// everyone to see and hear, a kill-feed line for whoever did it. Breaking isn't a kill: you're back at the HP you had.
// Messages: { t: 'bhp', id, k, hp, max, from? } (the pool now, batched; from = who hit it, for hitmarkers)
//           { t: 'bbreak', id, k, by, why: 'broke' | 'out', p } (it broke: by = who broke it, 0 = it wore out)
import { FLAGS } from '../shared/weapons.js';
import { BODY } from '../shared/bodyhp.js';

export function installBody(Room, U) {
  const { now, send, r2 } = U;
  const M = {
    bodyStart(p, kind) {
      const B = BODY[kind];
      if (!B) return;
      p.body = { kind, hp: B.hp, max: B.hp, from: new Set(), sentT: 0, dirty: false };
      this.broadcast({ t: 'bhp', id: p.id, k: kind, hp: B.hp, max: B.hp });
    },
    // still in it? (the ball's clock is now only a safety net: the pool or the decay ends it first)
    bodyOn(p, n = now()) {
      const b = p && p.body;
      if (!b || !p.alive) return false;
      return b.kind === 'wreckingball' ? p.ballUntil > n : p.mech ? this.mechOn(p, n) : this.rigOn(p, n); // (a mech's pool: server/mech.js)
    },
    // from damage() (and the rig's soak after its block): everything comes off the pool, nothing off your HP.
    // the floor, the zone and your own cough still hurt you. returns what's left for HP
    bodySoak(t, amt, attacker, w) {
      const b = t.body;
      if (!b || !(amt > 0) || !this.bodyOn(t) || BODY.bypass.includes(w)) return amt;
      b.hp -= Math.min(amt, BODY.cap);
      if (attacker && attacker !== t) { b.from.add(attacker.id); b.by = attacker.id; b.byT = now(); }
      if (b.hp <= 0) this.bodyBreak(t, attacker && attacker !== t ? attacker : null, 'broke');
      else this.bodyFlush(t, false);
      return 0;
    },
    // hits go out batched (a minigun is 25 a second)
    bodyFlush(t, force) {
      const b = t.body, n = now();
      if (!b) return;
      if (!force && n - b.sentT < 100) { b.dirty = true; return; }
      b.sentT = n; b.dirty = false;
      if (t.rig) t.rig.shield = Math.max(0, b.hp); // (the rig's own shield events read it)
      this.broadcast({ t: 'bhp', id: t.id, k: b.kind, hp: Math.max(0, Math.round(b.hp)), max: b.max, from: b.from.size ? [...b.from].slice(0, 8) : undefined });
      b.from.clear();
    },
    // it broke (by someone, or it wore out): the break first (clients burst the model while it's still there), then the
    // streak ends the usual way, and a pop up out of it
    bodyBreak(t, by, why) {
      const b = t.body;
      if (!b) return;
      t.body = null;
      this.bodyGone(t, b);
      if (t.mech) { this.mechBroke(t, by); return; } // a mech: EJECT! EJECT! and the blast (server/mech.js)
      this.broadcast({ t: 'bbreak', id: t.id, k: b.kind, by: by ? by.id : 0, why, p: t.pos.map(r2) });
      if (b.kind === 'wreckingball') { t.ballUntil = 0; t.f &= ~FLAGS.BALL; t.slamT = 0; }
      else if (t.rig) this.rigEnd(t);
      if (t.isBot) t.vel[1] = Math.max(t.vel[1], BODY.knock);
      else send(t, { t: 'kb', v: [0, BODY.knock, 0], w: 'break' });
    },
    // gone without a break (died, round over, mode change, left): no effect, nothing in the feed
    bodyClear(p) { if (p.body) this.bodyGone(p, p.body); p.body = null; },
    // training: a used streak comes back 3 s after it's over (the tray's clock was its old fixed length)
    bodyGone(p, b) { if (this.mode === 'training') (p.trainCd ||= {})[b.kind] = now() + 3000; },
    // every tick: the slow drain, batched updates, and a pool whose streak ended some other way goes too
    tickBody(n, dt) {
      for (const p of this.players.values()) {
        const b = p.body;
        if (!b) continue;
        if (!this.bodyOn(p, n)) { this.bodyClear(p); continue; }
        b.hp -= BODY[b.kind].decay * dt;
        if (b.hp <= 0) { // drained to nothing: still the last shooter's break if they were on it a moment ago
          const by = b.by && n - (b.byT || 0) < 4000 ? this.players.get(b.by) : null;
          this.bodyBreak(p, by && by.alive !== undefined ? by : null, by ? 'broke' : 'out');
        }
        else if (b.dirty || n - b.sentT > 1000) this.bodyFlush(p, true);
      }
    },
  };
  for (const [k, fn] of Object.entries(M)) {
    if (k in Room.prototype) throw new Error('bodyhp: Room already has ' + k);
    Room.prototype[k] = fn;
  }
}
