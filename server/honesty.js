// SERVER HONESTY: what a client says it hit has to be something it could have hit. Movement is the client's, so every
// check here is LENIENT on purpose (lag, interpolation, snapshot age): it only refuses what no honest client at ~150 ms
// ping could send. Players only: bots and server-made shots never come through here.
//   - line of sight (hitscan, melee, cigarette, leaf blower): the shooter's eye (a few heights, a few recent positions,
//     a snapshot ahead) to a few points on the target's hitboxes (spots along its recent path, the client's far-away
//     scale-up, its soap bubble). the same solid boxes the client's bullets stop on (glass included, deco and smoke not).
//     any one clear line = ok. a ricochet gun (the revolver) also lands if its bounces trace back to a wall spot the
//     shooter can see, and a shot from their eye to that spot really bounces the way the client says
//   - CPU: no rays for a hit onHit would drop on its rate or range anyway, a refused hit uses up its rate slot, and each
//     player has a ray / time budget per hit and per second (a flood of impossible hits can't eat the server)
//   - the weapon: held (or swapped away from < grace ms ago; a hit with the gun you're swapping to waits for the snapshot
//     that says so), and in your loadout: the randomizer's roll, or one weapon per slot per life once the client's own
//     loadout switching window has closed. modes with their own rules (gun game, zombies, royale, econ, chaos) keep them
//   - cones: melee, cigarette and leaf blower targets roughly in front of where your snapshots looked (any way up close)
//   - Taser / TV Remote: held, in your loadout, and the mode allows them
//   - Chicken Strike / Giant Duck: the aim point in range and seen from you (refused = back in your tray)
//   - Clubs shockwave: not through walls
// Mixed into Room by installHonesty (wraps handle, onHit, onPush, onFire, sendLoadout, modeLoadout, resetLife).
import { WEAPONS, SLOTS, FLAGS, WRECK, STREAKS } from '../shared/weapons.js';
import { raycast, playerBoxes } from '../shared/physics.js';
import { rigBoxes, RIG } from '../shared/rig.js';
import { mechBoxes, MECH, mechFrame } from '../shared/mech.js';
import { trapBoxes } from '../shared/wand.js';

export const HON = {
  grace: 400, // ms: the gun you just swapped away from still counts this long (a hit already on its way)
  wait: 300, // ms: a hit with a gun you're swapping to (same frame, before the snapshot) waits this long for it
  lockAt: 6500, // ms after a life's first snapshot: one weapon per slot from here (the client switches loadouts only in the first 5 s)
  tHist: 650, // ms of the target's past positions tried (the client draws others ~110 ms back, plus the shooter's round trip: ~540 ms ping still lands)
  step: 0.6, // m: the target's past path is tried every this far (more on a long path: at most `samples` spots), not every snapshot
  samples: 16,
  eyes: [1.6, 1.3, 0.98], // eye heights: standing, in between, crouched / sliding (the client's eye slides between them)
  lead: 0.05, // s: the shooter a snapshot ahead (they fired before the next one went out)
  leadMax: 60, // m/s: the most that lead believes
  coneSlack: 0.45, // rad on top of a cone (the snapshot's look is up to a frame or two old)
  close: 2.2, // m: closer than this, any angle (the client takes 1.5 m; positions lag)
  looks: 300, // ms of looks kept for the cones
  aimRange: 300, aimSlack: 8, // chicken / duck: the client's aim ray is 300 m
  bounceTol: 0.12, // rad: a ricochet's bounce has to send the shot where the client says (plus the target's size, seen from the eye)
  rays: 7500, // line-of-sight rays per player per second (2-6 us each: ~3 refused full checks). past this, that second's hits are refused
  perHit: 2500, // rays one hit may cost (a full no takes ~2100 + a ricochet's). an honest one takes 1 (median), p99 under 100
  ms: 20, hitMs: 10, // and CPU time: per player per second, per hit (a ray costs 2 us on an open map, 14 on Jankburg). an honest hit takes ~0.02 ms
};
const now = () => Date.now();
const LOG = !!process.env.JF_HON_LOG; // test knob: print every refusal and why
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const v3 = (a) => (Array.isArray(a) && a.length === 3 && a.every(num) ? a : null);
const unit = (a) => { const l = a && Math.hypot(a[0], a[1], a[2]); return l > 1e-6 && l < 1e9 ? [a[0] / l, a[1] / l, a[2] / l] : null; };
const LAT = [0, -0.85, 0.85], UP = [0.5, 0.9, 0.12]; // where on a box: middle, then its sides / top / bottom (inset)
const PB = playerBoxes([0, 0, 0]); // a player's boxes around their feet
// scratch space for the checks (one check at a time: the server is one thread), so a hit allocates next to nothing
const vecs = (n) => Array.from({ length: n }, () => [0, 0, 0]);
const PAST = vecs(HON.samples + 1), EYES = vecs(64), PTS = vecs(160), RAW = vecs(64), DIR = [0, 0, 0], TMP = [0, 0, 0];
const BXS = Array.from({ length: 8 }, () => ({ min: [0, 0, 0], max: [0, 0, 0] }));
const set3 = (o, x, y, z) => { o[0] = x; o[1] = y; o[2] = z; return o; };
const d3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

const M = {
  hon(p) { return p.hon || (p.hon = { prevW: null, swapT: 0, pend: [], lk: new Float64Array(48), lkN: 0, lo: {}, life: p.spawnT, firstT: 0, rays: 0, ms: 0, rayT: 0 }); },
  // checks only for people, in rooms where the server has the walls (story rooms run their own referee)
  honOn(p) { return !!p && !p.isBot && this.mode !== 'story'; },
  spinbotOn(p) { const u = p.usedAt && p.usedAt.spinbot; return !!u && now() - u < (STREAKS.spinbot.dur || 10) * 1000 + 1000; },

  // ------------------------------------------------------------ the weapon
  // held now, or the one before it for a moment after a swap
  honHeld(p, wid) {
    if (wid === 'dash') return p.w === 'scythe' || p.w === 'scythe_rifle' || this.honHeld(p, 'scythe') || this.honHeld(p, 'scythe_rifle'); // the scythe's dash
    if (p.w === wid) return true;
    const H = this.hon(p);
    return H.prevW === wid && now() - H.swapT < HON.grace;
  },
  // one weapon per slot per life, once the loadout can't change any more (plain matches: the modes have their own rules)
  honLockOn(p) {
    return (this.mode === 'ffa' || this.mode === 'bots') && !this.warm && !p.roll && !this.modeWeapon(p) && !this.chaosKit && !this.brOn && !this.isleOn && !this.zm && !this.bgn && !(this.isEcon && this.isEcon());
  },
  // in the loadout the server knows you have: the randomizer's roll, else this life's slot lock
  honLoadout(p, wid) {
    const w = WEAPONS[wid];
    if (!w || !SLOTS.includes(w.slot)) return true; // streak / mode / item weapons: onHit's own checks (scythe, allowed, popper)
    if (p.roll && (this.mode === 'ffa' || this.mode === 'bots')) return p.roll[w.slot] === wid;
    if (!this.honLockOn(p)) return true;
    const H = this.hon(p);
    this.honLife(p);
    return !H.lo[w.slot] || H.lo[w.slot] === wid;
  },
  honLife(p) { const H = this.hon(p); if (H.life !== p.spawnT) { H.life = p.spawnT; H.lo = {}; H.pend.length = 0; H.prevW = null; H.firstT = 0; } },
  // every snapshot: the swap clock, the look history, the slot lock, and any hit that was waiting for this gun
  honSnap(p, w0) {
    const H = this.hon(p), n = now();
    this.honLife(p);
    if (!H.firstT) H.firstT = n; // (the lock's clock starts when the client is really playing this life: a slow map load or a laggy join can't eat its 5 s)
    if (p.w !== w0) {
      H.prevW = w0; H.swapT = n;
      if (H.pend.length) {
        const go = H.pend.filter((e) => e.m.w === p.w && n - e.t <= HON.wait);
        H.pend.length = 0;
        for (const e of go) this.onHit(p, e.m); // (now it's held: the usual checks run)
      }
    } else if (H.pend.length && n - H.pend[0].t > HON.wait) H.pend.length = 0;
    const i = (H.lkN++ % 16) * 3; H.lk[i] = n; H.lk[i + 1] = p.yaw || 0; H.lk[i + 2] = p.pitch || 0; // (a ring: no array per snapshot)
    const w = WEAPONS[p.w];
    if (w && SLOTS.includes(w.slot) && n - H.firstT >= HON.lockAt && !H.lo[w.slot] && this.honLockOn(p)) H.lo[w.slot] = p.w;
  },

  // ------------------------------------------------------------ positions
  // where t was over the last ms (the speed trap's trail: every snapshot / bot tick, server/secondaries.js), newest first,
  // as spots along the path every HON.step m (further apart on a long path): a fast mover's snapshots can be metres apart,
  // a still one is one spot. into out, returns how many
  honPast(t, ms, out) {
    const tr = t.strail, n = now();
    let nr = 0, L = 0;
    set3(RAW[nr++], t.pos[0], t.pos[1], t.pos[2]);
    if (tr) for (let i = tr.length - 1; i >= 0 && nr < RAW.length; i--) {
      const s = tr[i];
      if (s[0] < n - ms) break;
      const r = set3(RAW[nr], s[1], s[2], s[3]), dl = d3(r, RAW[nr - 1]);
      if (dl < 0.01) continue;
      L += dl; nr++;
    }
    const cap = out.length - 1, step = Math.max(HON.step, L / (cap - 1));
    let k = 0, next = 0, walked = 0;
    for (let i = 0; i < nr; i++) {
      if (i > 0) {
        const a = RAW[i - 1], b = RAW[i], dl = d3(a, b);
        while (next <= walked + dl && k < cap) { const f = dl > 0 ? (next - walked) / dl : 0; set3(out[k++], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f); next += step; }
        walked += dl;
      } else { set3(out[k++], RAW[0][0], RAW[0][1], RAW[0][2]); next = step; }
    }
    if (nr > 1 && k < out.length && d3(out[k - 1], RAW[nr - 1]) > 0.05) set3(out[k++], RAW[nr - 1][0], RAW[nr - 1][1], RAW[nr - 1][2]); // (the oldest end too)
    return k;
  },
  // how fast p is going, believed: the claimed speed, but no faster than the server saw them go: over its 600 ms average
  // (speedOf) or, right after a launch (rocket jump, pad, fling), over the last two snapshots (x1.25), capped
  honSpeed(p) {
    const tr = p.strail, l = tr && tr.length;
    let recent = 0;
    if (l >= 2) { const a = tr[l - 2], b = tr[l - 1], dt = (b[0] - a[0]) / 1000; if (dt >= 0.015) recent = Math.hypot(b[1] - a[1], b[2] - a[2], b[3] - a[3]) / dt * 1.25; }
    return Math.min(Math.hypot(p.vel[0], p.vel[1], p.vel[2]), HON.leadMax, Math.max(this.speedOf(p), recent));
  },
  // the shooter's eyes: now and a snapshot ahead (a hit always goes out after the snapshot before it, so the eye that fired
  // is at or past the newest position), at each eye height. into EYES, returns how many
  honEyes(p) {
    const hs = this.honHeights(p);
    let ne = 0, nq = 0;
    const add = (x, y, z) => { // (a spot within 0.25 m of one already in is the same spot)
      for (let i = 0; i < nq; i++) { const e = EYES[i * hs.length]; if (Math.abs(e[0] - x) < 0.25 && Math.abs(e[1] - hs[0] - y) < 0.25 && Math.abs(e[2] - z) < 0.25) return; }
      for (const h of hs) set3(EYES[ne++], x, y + h, z);
      nq++;
    };
    add(p.pos[0], p.pos[1], p.pos[2]);
    const sp = this.honSpeed(p), v = unit(p.vel);
    if (v && sp > 0.5) add(p.pos[0] + v[0] * sp * HON.lead, p.pos[1] + v[1] * sp * HON.lead, p.pos[2] + v[2] * sp * HON.lead);
    return ne;
  },
  // eye heights: a body streak's eye is its own (a mech's cockpit, the rig's 2.05 m and its crouch, the ball's middle)
  honHeights(p) {
    if (this.mechOn(p) && p.mech) return [MECH[mechFrame(p.mech.f)].eye, ...HON.eyes];
    if (this.rigOn(p)) return [RIG.eye, ...HON.eyes];
    if (this.isBall(p)) return [WRECK.r * 2, ...HON.eyes];
    return HON.eyes;
  },
  // what the shooter's client aims at for t standing at q: its hitboxes, scaled up far away like the client draws them.
  // into BXS, returns how many
  honBoxes(t, q, dist) {
    let k = 1 + Math.max(0, Math.min(1, (dist - 25) / 60)) * 0.8;
    if (this.zm) k *= 1.5; // (zombies: Chonks and big-head mode are bigger on the client)
    const put = (list) => { for (let i = 0; i < list.length && i < BXS.length; i++) { set3(BXS[i].min, ...list[i].min); set3(BXS[i].max, ...list[i].max); } return Math.min(list.length, BXS.length); };
    if (t.trap) return put(trapBoxes(q, k)); // in a soap bubble: everyone shoots the bubble
    if (this.isBall(t)) { const r = WRECK.r * k; set3(BXS[0].min, q[0] - r, q[1], q[2] - r); set3(BXS[0].max, q[0] + r, q[1] + 2 * r, q[2] + r); return 1; }
    if (this.rigOn(t)) return put(rigBoxes(q, k));
    if (this.mechOn(t) && t.mech) return put(mechBoxes(q, t.mech.f, k));
    for (let i = 0; i < 2; i++) for (let a = 0; a < 3; a++) { BXS[i].min[a] = q[a] + PB[i].min[a] * k; BXS[i].max[a] = q[a] + PB[i].max[a] * k; }
    let nb = 2;
    if ((t.f & FLAGS.SLEEP) || t.sleepUntil > now()) for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { // knocked flat: lying along the floor, any way (the client's body reaches 2.35 m)
      set3(BXS[nb].min, q[0] + dx * 1.9 - 0.45, q[1], q[2] + dz * 1.9 - 0.45); set3(BXS[nb].max, q[0] + dx * 1.9 + 0.45, q[1] + 0.75, q[2] + dz * 1.9 + 0.45); nb++;
    }
    return nb;
  },
  // points on a box into PTS from index n: the middle first, then its sides (across the line of sight), top and bottom.
  // corners: its 8 corners instead (a sliver of a box past a wall's edge: only tried before a refusal)
  honPts(b, side, n, corners) {
    if (corners) {
      for (const y of [b.min[1] + 0.03, b.max[1] - 0.03]) for (const x of [b.min[0] + 0.03, b.max[0] - 0.03]) for (const z of [b.min[2] + 0.03, b.max[2] - 0.03]) set3(PTS[n++], x, y, z);
      return n;
    }
    const cx = (b.min[0] + b.max[0]) / 2, cz = (b.min[2] + b.max[2]) / 2, hx = (b.max[0] - b.min[0]) / 2, hz = (b.max[2] - b.min[2]) / 2;
    for (const u of UP) for (const l of LAT) set3(PTS[n++], cx + side[0] * hx * l, b.min[1] + (b.max[1] - b.min[1]) * u, cz + side[1] * hz * l);
    return n;
  },
  // one line-of-sight ray, counted against p's budget
  honClear(H, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], l = Math.hypot(dx, dy, dz);
    if (l < 0.05) return true;
    if (H) H.rays++;
    return !raycast(a, set3(DIR, dx / l, dy / l, dz / l), l - 0.02, this.boxes);
  },
  // the per-player ray budget: false = spent for this second (a flood of impossible hits can't eat the server's time)
  honBudget(p) {
    const H = this.hon(p), n = now();
    if (n - H.rayT >= 1000) { H.rayT = n; H.rays = 0; H.ms = 0; }
    return H.rays < HON.rays && H.ms < HON.ms;
  },
  // could p's shot (or swing, or puff) have reached t? w: the weapon (ricochets), d: the shot's last direction.
  // cheapest first: each spot's box middles, then all the points, then the newest spots' corners, then a ricochet
  shotSeen(p, t, w, d) {
    const H = this.hon(p);
    if (!this.honBudget(p)) return this.honNo(p, 'over the ray budget', { t: 'los', to: t.id });
    const t0 = performance.now();
    try { return this.honSeen(H, p, t, w, d, t0); } finally { H.ms += performance.now() - t0; }
  },
  honSeen(H, p, t, w, d, t0) {
    const ne = this.honEyes(p), np = this.honPast(t, HON.tHist, PAST), stop = H.rays + HON.perHit;
    const side = [0, 0];
    for (let pass = 0; pass < 3; pass++) {
      for (let i = 0; i < (pass === 2 ? Math.min(2, np) : np); i++) {
        const q = PAST[i], dx = q[0] - p.pos[0], dz = q[2] - p.pos[2], hl = Math.hypot(dx, dz) || 1;
        side[0] = -dz / hl; side[1] = dx / hl;
        const nb = this.honBoxes(t, q, Math.hypot(dx, q[1] - p.pos[1], dz));
        let n = 0;
        for (let b = 0; b < nb; b++) n = this.honPts(BXS[b], side, n, pass === 2);
        for (let e = 0; e < ne; e++) for (let j = 0; j < n; j++) {
          if (pass === 0 ? j % 9 : pass === 1 && !(j % 9)) continue; // (pass 0: the middles; pass 1: the rest)
          if (this.honClear(H, EYES[e], PTS[j])) return true;
          if (H.rays > stop || (!(H.rays & 31) && performance.now() - t0 > HON.hitMs)) return this.honNo(p, 'too many rays for one hit', { t: 'los', to: t.id });
        }
      }
    }
    if (w && w.ricochet && d) for (let i = 0; i < np; i++) {
      const q = PAST[i], dx = q[0] - p.pos[0], dz = q[2] - p.pos[2], hl = Math.hypot(dx, dz) || 1;
      side[0] = -dz / hl; side[1] = dx / hl;
      const nb = this.honBoxes(t, q, Math.hypot(dx, q[1] - p.pos[1], dz));
      let n = 0;
      for (let b = 0; b < nb; b++) n = this.honPts(BXS[b], side, n, false);
      for (let j = 0; j < n; j += 3) { if (this.honBounce(H, ne, PTS[j], d, w, t, q)) return true; if (H.rays > stop || performance.now() - t0 > HON.hitMs) return false; }
    }
    return false;
  },
  // a bounced shot, traced back from where it met them: each wall it came off, nearest first. it counts if the shooter can
  // see that spot AND a shot from their eye to it really bounces the way the client says (the client sends the last leg's
  // direction; the legs before it are its mirror images off each wall)
  honBounce(H, ne, pt, d, w, t, q) {
    let o = pt, back = [-d[0], -d[1], -d[2]], fwd = [d[0], d[1], d[2]], left = w.range || 250;
    for (let b = 0; b < w.ricochet; b++) {
      H.rays++;
      const h = raycast(o, back, left, this.boxes);
      if (!h || !h.normal || (!h.normal[0] && !h.normal[1] && !h.normal[2])) return false;
      const nn = h.normal, P = [h.point[0] + nn[0] * 0.05, h.point[1] + nn[1] * 0.05, h.point[2] + nn[2] * 0.05];
      const tol = Math.min(0.35, HON.bounceTol + Math.atan2(1.2, Math.max(0.5, d3(P, q)))); // (where on their body it met them shifts the bounce spot)
      for (let e = 0; e < ne; e++) {
        const E = EYES[e], u = unit([P[0] - E[0], P[1] - E[1], P[2] - E[2]]);
        if (!u) continue;
        const k = u[0] * nn[0] + u[1] * nn[1] + u[2] * nn[2], r = [u[0] - 2 * k * nn[0], u[1] - 2 * k * nn[1], u[2] - 2 * k * nn[2]];
        if (Math.acos(Math.max(-1, Math.min(1, r[0] * fwd[0] + r[1] * fwd[1] + r[2] * fwd[2]))) <= tol && this.honClear(H, E, P)) return true;
      }
      const k = fwd[0] * nn[0] + fwd[1] * nn[1] + fwd[2] * nn[2]; // the leg before: the mirror image of this one off the wall
      fwd = [fwd[0] - 2 * k * nn[0], fwd[1] - 2 * k * nn[1], fwd[2] - 2 * k * nn[2]];
      back = [-fwd[0], -fwd[1], -fwd[2]];
      o = P; left -= h.t;
      if (left <= 0) return false;
    }
    return false;
  },
  // is t roughly in front of where p's snapshots looked (any of the last few), or right up close? cone in radians
  honCone(p, t, cone) {
    if (this.spinbotOn(p)) return true; // the spinbot's snapshots send a spinning yaw; its shots follow the aimbot's lock
    const H = this.hon(p), n0 = now(), ne = this.honEyes(p), np = this.honPast(t, HON.tHist, PAST);
    for (let i = 0; i < np; i++) for (let e = 0; e < ne; e += HON.eyes.length) {
      const q = PAST[i], E = EYES[e], c = set3(TMP, q[0] - E[0], q[1] + 1 - E[1], q[2] - E[2]), dist = Math.hypot(c[0], c[1], c[2]);
      if (dist < HON.close) return true;
      const allow = Math.cos(Math.min(Math.PI, cone + HON.coneSlack + Math.atan2(0.7, dist)));
      const look = (y, x) => { const cp = Math.cos(x); return (-Math.sin(y) * cp * c[0] + Math.sin(x) * c[1] - Math.cos(y) * cp * c[2]) / dist >= allow; };
      if (look(p.yaw || 0, p.pitch || 0)) return true;
      for (let j = 0; j < 16 && j < H.lkN; j++) if (n0 - H.lk[j * 3] <= HON.looks && look(H.lk[j * 3 + 1], H.lk[j * 3 + 2])) return true;
    }
    return false;
  },
  // onHit / onPush's rate clock for this hit: the same key and gap they use (null: the revolver keeps its own cylinder)
  honKey(p, t, w, m) {
    if (m.t === 'push') return ['blow', 75];
    if (w.kind === 'hitscan') return w.fanHammer ? null : ['hs' + m.w + (w.hands && m.hd === 1 ? 'L' : ''), (1000 / this.rateOf(m.w, w, p.hp)) * 0.6];
    if (w.kind === 'melee') { const hv = m.heavy === 1 && w.heavy ? w.heavy : null; return hv ? ['mh' + m.w, hv.cd * 750] : ['m' + m.w, w.cd * 750]; }
    if (m.w === 'cig') return ['cig', 75];
    return null;
  },
  // would onHit / onPush drop this anyway on its rate or range? (looked at, not touched). false = yes: no rays spent on it
  honGate(p, t, w, m) {
    const k = this.honKey(p, t, w, m);
    if (k && now() - ((p.pair && p.pair.get(k[0] + ':' + t.id)) || 0) < k[1]) return false;
    const hv = w.kind === 'melee' && m.heavy === 1 && w.heavy ? w.heavy : null;
    const range = m.t === 'push' ? w.range : hv ? hv.range : w.range + (m.w === 'katana' ? (p.kat || 0) * (w.grow || 0) : 0);
    return this.rangeOk(p, t, range);
  },
  // a refused hit was still a shot: it used up that rate slot, like onHit's pairOk would have (a flood of impossible
  // hits on one target is then dropped by the rate check for free)
  honSpent(p, t, w, m) {
    const k = this.honKey(p, t, w, m);
    if (k && p.pair) p.pair.set(k[0] + ':' + t.id, now());
    return false;
  },

  // ------------------------------------------------------------ the message checks (false = drop it)
  honNo(p, why, m) { if (LOG) { const t = this.players.get(m.to); console.log(`[honesty] ${p.name} ${m.t} ${m.w || m.r || ''} -> ${m.to ?? ''}: ${why} (from ${p.pos.map((x) => x.toFixed(1))}${t ? ' at ' + t.pos.map((x) => x.toFixed(1)) : ''}, map ${this.cfg.map})`); } return false; },
  honHit(p, m) {
    if (m.mk !== undefined) return true; // an empty mech: mechShot checks held gun, aim and walls itself
    const w = typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) ? WEAPONS[m.w] : null;
    const t = this.players.get(m.to);
    if (!w || !t || t === p || !t.alive || !p.alive || this.rigOn(p) || this.mechOn(p)) return true; // onHit drops these itself
    if (m.w === 'popper') return true; // an item: popperHit only counts right after a real pop
    if (w.kind !== 'hitscan' && w.kind !== 'melee' && w.kind !== 'dash' && m.w !== 'cig') return true; // nothing else lands here
    if (!this.honLoadout(p, m.w)) return this.honNo(p, 'not in the loadout', m);
    if (!this.honHeld(p, m.w)) { // swapped and fired in one frame: wait for the snapshot that says so
      const H = this.hon(p);
      if (H.pend.length < 6) H.pend.push({ m, t: now() });
      return this.honNo(p, 'not held (waiting for the snapshot)', m);
    }
    if (w.kind === 'dash') return true; // the client's own check is 2.6 m around you, walls or not
    if (!this.honGate(p, t, w, m)) return true; // too soon / too far: onHit drops it (no rays spent)
    if (this.zm && t.zmz) return w.kind !== 'melee' || this.honCone(p, t, w.cone || 0.8) || this.honNo(p, 'not in front', m); // zombies: co-op vs the horde (limbs, crawlers, Chonks): no wall check
    const d = unit(v3(m.d));
    if (w.kind === 'hitscan') return this.shotSeen(p, t, w, d) || this.honSpent(p, t, w, m) || this.honNo(p, 'no line of sight', m);
    const hv = w.kind === 'melee' && m.heavy === 1 && w.heavy ? w.heavy : null;
    if (!this.honCone(p, t, hv ? hv.cone : w.cone || 0.8)) return this.honSpent(p, t, w, m) || this.honNo(p, 'not in front', m);
    return this.shotSeen(p, t, null, null) || this.honSpent(p, t, w, m) || this.honNo(p, 'no line of sight', m);
  },
  honPush(p, m) {
    if (m.w !== 'blower' && m.w !== 'shredder') return true; // the grapple's tug: onPush's own range / rate checks
    const t = this.players.get(m.to);
    if (!t || t === p || !t.alive || !p.alive) return true;
    if (!this.honLoadout(p, m.w) || !this.honHeld(p, m.w)) return this.honNo(p, 'not held / not in the loadout', m);
    if (m.w === 'shredder') return true; // shredPull checks its cone and walls itself
    if (!this.honGate(p, t, WEAPONS.blower, m)) return true;
    if (!this.honCone(p, t, WEAPONS.blower.cone)) return this.honSpent(p, t, WEAPONS.blower, m) || this.honNo(p, 'not in front', m);
    return this.shotSeen(p, t, null, null) || this.honSpent(p, t, WEAPONS.blower, m) || this.honNo(p, 'no line of sight', m);
  },
  // the taser and the remote skip onFire's checks (server/secondaries.js takes them first): the same rules here
  honSecFire(p, m) {
    if (!p.alive || !this.honOn(p)) return true;
    const id = m.w;
    if (!this.allowed(p, id) || (this.zm && !this.zmArm(p, id))) return this.honNo(p, 'not in this mode', m);
    if (this.chaosKit && !this.chaosKit.slots.includes(id)) return this.honNo(p, 'not in the kit', m);
    return (this.honLoadout(p, id) && this.honHeld(p, id)) || this.honNo(p, 'not held / not in the loadout', m);
  },
  // chicken strike / giant duck: the client aims with a 300 m ray from your eye (60 m into the air when it hits nothing)
  honAim(p, at) {
    if (!this.honBudget(p)) return false;
    const H = this.hon(p), ne = this.honEyes(p), sp = this.speedOf(p);
    for (let i = 0; i < ne; i++) {
      const e = EYES[i], d = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
      if (l > HON.aimRange + HON.aimSlack + sp * 0.3) continue;
      if (l < 1) return true;
      H.rays++;
      const h = raycast(e, [d[0] / l, d[1] / l, d[2] / l], l, this.boxes);
      if (!h || h.t >= l - 1.2) return true; // nothing in the way before the spot (the spot itself is on a wall / the floor)
    }
    return false;
  },
  // the Clubs shockwave: like the wrecking ball's, not through walls or the floor (a few points on them, from your middle)
  honWave(p, t) {
    const c = [p.pos[0], p.pos[1] + 1, p.pos[2]];
    for (const h of [1, 1.7, 0.3]) if (this.honClear(null, c, [t.pos[0], t.pos[1] + h, t.pos[2]])) return true;
    return false;
  },
};

export function installHonesty(Room, deps) {
  const P = Room.prototype;
  for (const [k, fn] of Object.entries(M)) {
    if (k in P) throw new Error('honesty: Room already has ' + k);
    P[k] = fn;
  }
  const orig = {};
  for (const k of ['handle', 'onHit', 'onPush', 'onFire', 'sendLoadout', 'modeLoadout', 'resetLife']) {
    if (typeof P[k] !== 'function') throw new Error('honesty: Room is missing ' + k);
    orig[k] = P[k];
  }
  Object.assign(P, {
    handle(p, m) {
      if (!m || typeof m !== 'object' || !p || p.isBot) return orig.handle.call(this, p, m);
      if (m.t === 's') { const w0 = p.w, r = orig.handle.call(this, p, m); if (p.alive) this.honSnap(p, w0); return r; }
      if (m.t === 'deploy' && (m.r === 'chickenstrike' || m.r === 'giantduck') && !p.zmDeploy && this.honOn(p) && p.alive && (p.pocket || []).includes(m.r)) {
        const at = v3(m.at);
        if (at && !this.honAim(p, at)) { this.honNo(p, 'aim point too far / not seen', m); deps.send(p, { t: 'streak', earned: m.r, n: p.streak || 0 }); return; } // too far / not seen: back in your tray
      }
      return orig.handle.call(this, p, m);
    },
    onHit(p, m) {
      if (!m || !this.honOn(p) || this.honHit(p, m)) return orig.onHit.call(this, p, m);
    },
    onPush(p, m) {
      if (!m || !this.honOn(p) || this.honPush(p, m)) return orig.onPush.call(this, p, m);
    },
    onFire(p, m) {
      const w = m && typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) ? WEAPONS[m.w] : null;
      if (w && (w.kind === 'zap' || w.kind === 'remote') && p && !p.isBot && !this.honSecFire(p, m)) return;
      return orig.onFire.call(this, p, m);
    },
    // a loadout handed out (every spawn, and the modes' own moments): the slot lock and the roll start over
    sendLoadout(p) { if (p) { p.roll = null; if (p.hon) p.hon.lo = {}; } return orig.sendLoadout.call(this, p); },
    modeLoadout(p) { if (p && p.hon) p.hon.lo = {}; return orig.modeLoadout.call(this, p); },
    resetLife(p) { const r = orig.resetLife.call(this, p); if (p) p.hon = null; return r; },
  });
}
