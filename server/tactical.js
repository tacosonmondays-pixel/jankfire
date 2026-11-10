// Plant & Defuse gunplay, server side (rules: shared/tactical.js). A hitscan shot in this mode carries its shot number
// (q), spray index (i), the aim it was fired at (a) and its spread (sp). The server checks that
//   - q is the next shot (a couple ahead is fine: the server may have refused one), i is within one of its own count,
//   - a matches the aim in the snapshot the client sends right before every shot,
//   - sp is at least what the server thinks you deserve (your speed, air, crouch, the room's hipfire setting),
//   - the hit's direction is exactly where that aim + the pattern + the shared per-shot random spread put it
//     (or a ricochet of it). Pellet guns: inside the cone.
// A hit that fails does nothing. Bots use the same patterns and moving spread, and pull down against them by difficulty.
import { WEAPONS, HIPFIRE, FLAGS } from '../shared/weapons.js';
import { TAC, patternOf, shotOffset, shotDir, shotSeed, tacSpread, angleBetween, landK } from '../shared/tactical.js';
import { raycast, PH } from '../shared/physics.js';
import { sdRow, sdMinBase, sdBase } from '../shared/sdgun.js'; // S&D: first-shot spread + bloom per gun

const now = () => Date.now();
const LOG = !!process.env.JF_TAC_LOG;
const wrapA = (a) => { a = ((a + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI; return a; };
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const BOT_COMP = { easy: 0.25, normal: 0.55, hard: 0.8 }; // how much of the pattern a bot pulls down against

const M = {
  tacState(p) {
    const n = this.bomb ? this.bomb.n : 0;
    if (!p.tac || p.tac.n !== n) p.tac = { n, q: 0, i: 0, lastT: -1e9, lastId: '', seed: shotSeed(p.id, n), bad: 0 };
    return p.tac;
  },
  // standing on something? (the client's own onGround decides its spread; this is the lenient server view)
  tacAir(p) {
    if (Math.abs(p.vel[1]) < 1.2) return false;
    return !raycast([p.pos[0], p.pos[1] + 0.3, p.pos[2]], [0, -1, 0], 0.9, this.boxes);
  },
  // the least spread this shot can honestly have
  tacMinSpread(p, w, id, fan, i = 0) {
    const hip = (HIPFIRE[this.cfg.hip] || HIPFIRE.normal).mul;
    let base = (w.spread || 0) * hip * (w.ads ? Math.min(1, w.ads.spread ?? 1) : 1);
    if (sdRow(id)) { const r = sdRow(id); base = Math.min(r.fs * hip, (r.ads ?? r.fs) * Math.min(1, hip)); } // (sights or hip: the lower one)
    if (fan && w.fanHammer) base = w.fanHammer.spread * hip;
    const speed = Math.hypot(p.vel[0], p.vel[2]);
    return tacSpread(id, base, speed, this.tacAir(p), !!(p.f & FLAGS.CROUCH), i, landK((p.tacAirT || -1e9) - 200, now())); // (200 ms grace: snapshots lag)
  },
  // econShot opened a new shot from message m: is it the next one, at the right spray index?
  tacOpen(p, x, w, m) {
    const T = this.tacState(p), n = now(), P = patternOf(x.id);
    const sh = x.shot;
    sh.tac = null;
    const q = m.q, i = m.i;
    if (!Number.isInteger(q) || !Number.isInteger(i) || q < T.q || q > T.q + 2 || i < 0 || i > 400) { this.tacNo(p, x, 'q', { q, want: T.q }); return; }
    // the spray index: carrying on (the next shot, within one) after a short gap, or a fresh spray (0, or 1) after a pause.
    // near the reset time either reading is fine: frames and the network shift the gap a little. a restart still needs a
    // real pause (75 % of the reset), and carrying on is never more accurate
    const rs = P ? P.reset : 400, gap = T.lastId === x.id ? n - T.lastT : 1e9;
    const carry = gap <= rs + 400 && Math.abs(i - (T.i + 1)) <= 1, fresh = gap >= rs * 0.75 && i <= 1;
    if (!carry && !fresh) { this.tacNo(p, x, 'i', { i, was: T.i, gap }); T.q = q + 1; return; }
    T.q = q + 1; T.i = i; T.lastT = n; T.lastId = x.id;
    const a = Array.isArray(m.a) && m.a.length === 2 && num(m.a[0]) && num(m.a[1]) ? m.a : null;
    if (!a || !num(m.sp) || m.sp < 0 || m.sp > 1) { this.tacNo(p, x, 'a', {}); return; }
    // the aim you claim is the aim of the snapshot you just sent
    if (Math.abs(wrapA(a[0] - (p.yaw || 0))) > TAC.aimTol || Math.abs(a[1] - (p.pitch || 0)) > TAC.aimTol) { this.tacNo(p, x, 'aim', { a, y: p.yaw, x: p.pitch }); return; }
    const min = this.tacMinSpread(p, w, x.id, m.fan === 1, i);
    if (m.sp < min * TAC.spTol - 0.002) { this.tacNo(p, x, 'sp', { sp: m.sp, min }); return; }
    sh.tac = { q, i, a, sp: m.sp, off: shotOffset(x.id, i), seed: T.seed };
  },
  tacNo(p, x, why, info) {
    x.shot.tac = null;
    const T = this.tacState(p);
    T.bad++;
    if (LOG) console.log(`[tacno] ${p.name} ${x.id} ${why} ${JSON.stringify(info)}`);
    if (!p.isBot) { const D = this.tacD; if (D) D.send(p, { t: 'am', u: x.u, w: x.id, m: x.m, r: x.r, q: T.q }); }
  },
  // a hit of an open shot: false = it doesn't count
  tacHitOk(p, x, w, m) {
    const s = x.shot && x.shot.tac;
    if (!s) return false;
    const d = Array.isArray(m.d) && m.d.length === 3 && m.d.every(num) ? m.d : null;
    const l = d && Math.hypot(d[0], d[1], d[2]);
    if (!l) return false;
    const dn = d.map((v) => v / l);
    if ((w.pellets || 1) > 1) { // a pellet gun: the hit has to be inside the cone
      const c = shotDir(s.a[0], s.a[1], s.off, 0, s.seed, s.q);
      return angleBetween(dn, c) <= s.sp + TAC.dirTol + 0.01;
    }
    const want = shotDir(s.a[0], s.a[1], s.off, s.sp, s.seed, s.q, 0);
    if (angleBetween(dn, want) <= TAC.dirTol) return true;
    if (w.ricochet) { // a bounced shot: follow the same bounces the client did
      let o = [p.pos[0], p.pos[1] + (p.f & FLAGS.CROUCH ? 1.05 : PH.eye), p.pos[2]], v = want, left = w.range;
      for (let b = 0; b < w.ricochet; b++) {
        const h = raycast(o, v, left, this.boxes);
        if (!h) break;
        const k = v[0] * h.normal[0] + v[1] * h.normal[1] + v[2] * h.normal[2];
        v = [v[0] - 2 * k * h.normal[0], v[1] - 2 * k * h.normal[1], v[2] - 2 * k * h.normal[2]];
        if (angleBetween(dn, v) <= TAC.dirTol * 2) return true;
        o = [h.point[0] + h.normal[0] * 0.02, h.point[1] + h.normal[1] * 0.02, h.point[2] + h.normal[2] * 0.02]; left -= h.t;
      }
    }
    if (LOG) console.log(`[tacno] ${p.name} ${x.id} dir off by ${angleBetween(dn, want).toFixed(4)} (q ${s.q} i ${s.i} sp ${s.sp})`);
    return false;
  },
  // bots: their hitscan shot goes through the same pattern (pulled down against by difficulty) and moving spread
  tacBotAim(b, w, aim, spread, D) {
    const ai = b.ai, n = now(), P = patternOf(b.w);
    const t = ai.tac || (ai.tac = { i: 0, lastT: -1e9, id: '' });
    t.i = t.id === b.w && n - t.lastT <= (P ? P.reset : 400) ? t.i + 1 : 0; t.lastT = n; t.id = b.w;
    const comp = ai.comp ?? BOT_COMP[ai.diff] ?? BOT_COMP.normal, o = shotOffset(b.w, t.i); // (ai.comp: this bot's own spray control, server/sdskill.js)
    const cp = Math.cos(b.pitch + o[1] * (1 - comp)), yaw = b.yaw - o[0] * (1 - comp);
    const a = [-Math.sin(yaw) * cp, Math.sin(b.pitch + o[1] * (1 - comp)), -Math.cos(yaw) * cp];
    const speed = Math.hypot(b.vel[0], b.vel[2]);
    if (sdRow(b.w)) { // S&D: the gun's own first shot + bloom (as if aiming), plus a smaller difficulty wobble
      const hip = (HIPFIRE[this.cfg.hip] || HIPFIRE.normal).mul;
      spread = sdBase(b.w, 1) * Math.min(1, hip) + (D && D.err ? D.err * 0.55 : 0);
      this.tacBotTrigger(b, w, t.i, n);
    }
    const sp = tacSpread(b.w, spread, speed, !b.onGround, false, sdRow(b.w) ? t.i : 0);
    return [a, sp];
  },
  // S&D trigger discipline: tap at range (wait out the spray reset), short bursts at mid range, hold it up close
  tacBotTrigger(b, w, i, n) {
    const ai = b.ai, tg = this.players.get(ai.target), P = patternOf(b.w);
    if (!w.auto || !tg || !P) return;
    const d = Math.hypot(tg.pos[0] - b.pos[0], tg.pos[2] - b.pos[2]);
    const burst = d > 28 ? 1 : d > 14 ? 3 : 99;
    if ((i + 1) % burst === 0) ai.nextShot = Math.max(ai.nextShot, n + P.reset + 40 + Math.random() * 120);
  },
};

export function installTactical(Room, deps) {
  for (const [k, fn] of Object.entries(M)) {
    if (k in Room.prototype) throw new Error('tactical: Room already has ' + k);
    Room.prototype[k] = fn;
  }
  Room.prototype.tacD = deps;
}
