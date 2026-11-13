// SERVER HONESTY: what a client says it hit has to be something it could have hit. Movement is the client's, so every
// check here is LENIENT on purpose (lag, interpolation, snapshot age): it only refuses what no honest client at ~150 ms
// ping could send. Players only: bots and server-made shots never come through here.
//   - line of sight (hitscan, melee, cigarette, leaf blower): the shooter's eye (a few heights, a few recent positions,
//     a snapshot ahead) to a few points on the target's hitboxes (a few recent positions, the client's far-away scale-up).
//     the same solid boxes the client's bullets stop on (glass included, deco and smoke not). any one clear line = ok.
//     a ricochet gun (the revolver) also lands if its bounces trace back to a wall spot the shooter can see
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
import { rigBoxes } from '../shared/rig.js';
import { mechBoxes } from '../shared/mech.js';

export const HON = {
  grace: 400, // ms: the gun you just swapped away from still counts this long (a hit already on its way)
  wait: 300, // ms: a hit with a gun you're swapping to (same frame, before the snapshot) waits this long for it
  lockAt: 6500, // ms into a life: one weapon per slot from here (the client switches loadouts only in the first 5 s)
  tHist: 450, // ms of the target's past positions tried (the client draws others ~110 ms back, plus ping)
  sHist: 220, // ms of the shooter's own
  gap: 100, // ms between the past positions tried
  eyes: [1.6, 1.3, 0.98], // eye heights: standing, in between, crouched / sliding (the client's eye slides between them)
  lead: 0.05, // s: the shooter a snapshot ahead (they fired before the next one went out)
  coneSlack: 0.45, // rad on top of a cone (the snapshot's look is up to a frame or two old)
  close: 2.2, // m: closer than this, any angle (the client takes 1.5 m; positions lag)
  looks: 300, // ms of looks kept for the cones
  aimRange: 300, aimSlack: 8, // chicken / duck: the client's aim ray is 300 m
  budget: 8, // full checks per second that come back "no" before the cheap one takes over (CPU, vs a spammer)
};
const now = () => Date.now();
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const v3 = (a) => (Array.isArray(a) && a.length === 3 && a.every(num) ? a : null);
const unit = (a) => { const l = a && Math.hypot(a[0], a[1], a[2]); return l > 1e-6 && l < 1e9 ? [a[0] / l, a[1] / l, a[2] / l] : null; };
const LAT = [0, -0.85, 0.85], UP = [0.5, 0.9, 0.12]; // where on a box: middle, then its sides / top / bottom (inset)

const M = {
  hon(p) { return p.hon || (p.hon = { prevW: null, swapT: 0, pend: [], looks: [], lo: {}, life: p.spawnT, fails: [] }); },
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
  honLife(p) { const H = this.hon(p); if (H.life !== p.spawnT) { H.life = p.spawnT; H.lo = {}; H.pend.length = 0; H.prevW = null; } },
  // every snapshot: the swap clock, the look history, the slot lock, and any hit that was waiting for this gun
  honSnap(p, w0) {
    const H = this.hon(p), n = now();
    this.honLife(p);
    if (p.w !== w0) {
      H.prevW = w0; H.swapT = n;
      const go = H.pend.filter((e) => e.m.w === p.w && n - e.t <= HON.wait);
      H.pend.length = 0;
      for (const e of go) this.onHit(p, e.m); // (now it's held: the usual checks run)
    } else if (H.pend.length && n - H.pend[0].t > HON.wait) H.pend.length = 0;
    H.looks.push([n, p.yaw || 0, p.pitch || 0]);
    while (H.looks.length > 1 && H.looks[0][0] < n - HON.looks) H.looks.shift();
    const w = WEAPONS[p.w];
    if (w && SLOTS.includes(w.slot) && n - (p.spawnT || 0) >= HON.lockAt && !H.lo[w.slot] && this.honLockOn(p)) H.lo[w.slot] = p.w;
  },

  // ------------------------------------------------------------ positions
  // where someone was over the last ms: now first, then every HON.gap ms back (the speed trap's trail: every snapshot /
  // bot tick, server/secondaries.js)
  honPast(t, ms) {
    const out = [t.pos], tr = t.strail, n = now();
    if (!tr) return out;
    let last = n;
    for (let i = tr.length - 1; i >= 0 && out.length < 7; i--) {
      const s = tr[i];
      if (s[0] < n - ms) break;
      if (last - s[0] < HON.gap) continue;
      last = s[0]; out.push([s[1], s[2], s[3]]);
    }
    return out;
  },
  // the shooter's eyes: now, a snapshot ahead (no faster than the server saw them go), a moment back; at each eye height
  honEyes(p, cheap) {
    const sp = Math.min(Math.hypot(p.vel[0], p.vel[1], p.vel[2]), this.speedOf(p)), v = unit(p.vel);
    const at = [p.pos];
    if (v && sp > 0.5) at.push([p.pos[0] + v[0] * sp * HON.lead, p.pos[1] + v[1] * sp * HON.lead, p.pos[2] + v[2] * sp * HON.lead]);
    if (!cheap) at.push(...this.honPast(p, HON.sHist).slice(1));
    const out = [];
    for (const q of at) for (const h of HON.eyes) out.push([q[0], q[1] + h, q[2]]);
    return out;
  },
  // what the shooter's client aims at for t standing at q: its hitboxes, scaled up far away like the client draws them
  honBoxes(t, q, dist) {
    let k = 1 + Math.max(0, Math.min(1, (dist - 25) / 60)) * 0.8;
    if (this.zm) k *= 1.5; // (zombies: Chonks and big-head mode are bigger on the client)
    if (this.isBall(t)) { const r = WRECK.r * k; return [{ min: [q[0] - r, q[1], q[2] - r], max: [q[0] + r, q[1] + 2 * r, q[2] + r] }]; }
    if (this.rigOn(t)) return rigBoxes(q, k);
    if (this.mechOn(t) && t.mech) return mechBoxes(q, t.mech.f, k);
    const bs = playerBoxes(q), out = bs.map((b) => ({ min: b.min.map((x, i) => q[i] + (x - q[i]) * k), max: b.max.map((x, i) => q[i] + (x - q[i]) * k) }));
    if ((t.f & FLAGS.SLEEP) || t.sleepUntil > now()) for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) out.push({ min: [q[0] + dx * 1.6 - 0.4, q[1], q[2] + dz * 1.6 - 0.4], max: [q[0] + dx * 1.6 + 0.4, q[1] + 0.7, q[2] + dz * 1.6 + 0.4] }); // knocked flat: lying along the floor, any way
    return out;
  },
  // points on a box: the middle first, then its sides (across the line of sight), top and bottom
  honPts(b, side) {
    const c = [(b.min[0] + b.max[0]) / 2, 0, (b.min[2] + b.max[2]) / 2], hx = (b.max[0] - b.min[0]) / 2, hz = (b.max[2] - b.min[2]) / 2, out = [];
    for (const u of UP) for (const l of LAT) out.push([c[0] + side[0] * hx * l, b.min[1] + (b.max[1] - b.min[1]) * u, c[2] + side[1] * hz * l]);
    return out;
  },
  honClear(a, b) {
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], l = Math.hypot(d[0], d[1], d[2]);
    return l < 0.05 || !raycast(a, [d[0] / l, d[1] / l, d[2] / l], l - 0.02, this.boxes);
  },
  // too many "no"s this second: only the cheap version (the newest positions) from here
  honCheap(p) { const H = this.hon(p), n = now(); while (H.fails.length && H.fails[0] < n - 1000) H.fails.shift(); return H.fails.length >= HON.budget; },
  honFail(p) { this.hon(p).fails.push(now()); return false; },
  // could p's shot (or swing, or puff) have reached t? w: the weapon (ricochets), d: the shot's last direction
  shotSeen(p, t, w, d) {
    const cheap = this.honCheap(p), eyes = this.honEyes(p, cheap), past = cheap ? [t.pos] : this.honPast(t, HON.tHist);
    for (const q of past) {
      const dx = q[0] - p.pos[0], dz = q[2] - p.pos[2], hl = Math.hypot(dx, dz) || 1, side = [-dz / hl, dx / hl];
      const pts = [];
      for (const b of this.honBoxes(t, q, Math.hypot(dx, q[1] - p.pos[1], dz))) pts.push(...this.honPts(b, side));
      pts.sort((a, b) => Math.abs(a[1] - q[1] - 1.1) - Math.abs(b[1] - q[1] - 1.1)); // chest height first: most hits end on the first ray
      for (const e of eyes) for (const pt of pts) if (this.honClear(e, pt)) return true;
      if (w && w.ricochet && d && !cheap) for (const pt of pts.slice(0, 9)) if (this.honBounce(eyes, pt, d, w)) return true;
    }
    return this.honFail(p);
  },
  // a bounced shot, traced back from where it met them: each wall it came off, nearest first. one the shooter can see = ok
  // (the client sends the last leg's direction; the legs before it are its mirror images off each wall)
  honBounce(eyes, pt, d, w) {
    let o = pt, v = [-d[0], -d[1], -d[2]], left = w.range || 250;
    for (let b = 0; b < w.ricochet; b++) {
      const h = raycast(o, v, left, this.boxes);
      if (!h || !h.normal || (!h.normal[0] && !h.normal[1] && !h.normal[2])) return false;
      const P = [h.point[0] + h.normal[0] * 0.05, h.point[1] + h.normal[1] * 0.05, h.point[2] + h.normal[2] * 0.05];
      for (const e of eyes) if (this.honClear(e, P)) return true;
      const k = v[0] * h.normal[0] + v[1] * h.normal[1] + v[2] * h.normal[2]; // (mirror the backward ray off the wall: the leg before)
      v = [v[0] - 2 * k * h.normal[0], v[1] - 2 * k * h.normal[1], v[2] - 2 * k * h.normal[2]];
      o = P; left -= h.t;
      if (left <= 0) return false;
    }
    return false;
  },
  // is t roughly in front of where p's snapshots looked (any of the last few), or right up close? cone in radians
  honCone(p, t, cone) {
    if (this.spinbotOn(p)) return true; // the spinbot's snapshots send a spinning yaw; its shots follow the aimbot's lock
    const H = this.hon(p), looks = [[0, p.yaw || 0, p.pitch || 0], ...H.looks];
    const eyes = this.honEyes(p, true);
    for (const q of this.honPast(t, HON.tHist)) for (const e of eyes) {
      const c = [q[0] - e[0], q[1] + 1 - e[1], q[2] - e[2]], dist = Math.hypot(c[0], c[1], c[2]);
      if (dist < HON.close) return true;
      const allow = Math.cos(Math.min(Math.PI, cone + HON.coneSlack + Math.atan2(0.7, dist)));
      for (const [, y, x] of looks) {
        const cp = Math.cos(x), L = [-Math.sin(y) * cp, Math.sin(x), -Math.cos(y) * cp];
        if ((L[0] * c[0] + L[1] * c[1] + L[2] * c[2]) / dist >= allow) return true;
      }
    }
    return false;
  },

  // ------------------------------------------------------------ the message checks (false = drop it)
  honHit(p, m) {
    if (m.mk !== undefined) return true; // an empty mech: mechShot checks held gun, aim and walls itself
    const w = typeof m.w === 'string' && Object.hasOwn(WEAPONS, m.w) ? WEAPONS[m.w] : null;
    const t = this.players.get(m.to);
    if (!w || !t || t === p || !t.alive || !p.alive || this.rigOn(p) || this.mechOn(p)) return true; // onHit drops these itself
    if (m.w === 'popper') return true; // an item: popperHit only counts right after a real pop
    if (w.kind !== 'hitscan' && w.kind !== 'melee' && w.kind !== 'dash' && m.w !== 'cig') return true; // nothing else lands here
    if (!this.honLoadout(p, m.w)) return false;
    if (!this.honHeld(p, m.w)) { // swapped and fired in one frame: wait for the snapshot that says so
      const H = this.hon(p);
      if (H.pend.length < 6) H.pend.push({ m, t: now() });
      return false;
    }
    if (w.kind === 'dash') return true; // the client's own check is 2.6 m around you, walls or not
    const d = unit(v3(m.d));
    if (w.kind === 'hitscan') return this.shotSeen(p, t, w, d);
    const hv = w.kind === 'melee' && m.heavy === 1 && w.heavy ? w.heavy : null;
    return this.honCone(p, t, hv ? hv.cone : w.cone || 0.8) && this.shotSeen(p, t, null, null);
  },
  honPush(p, m) {
    if (m.w !== 'blower' && m.w !== 'shredder') return true; // the grapple's tug: onPush's own range / rate checks
    const t = this.players.get(m.to);
    if (!t || t === p || !t.alive || !p.alive) return true;
    if (!this.honLoadout(p, m.w) || !this.honHeld(p, m.w)) return false;
    if (m.w === 'shredder') return true; // shredPull checks its cone and walls itself
    return this.honCone(p, t, WEAPONS.blower.cone) && this.shotSeen(p, t, null, null);
  },
  // the taser and the remote skip onFire's checks (server/secondaries.js takes them first): the same rules here
  honSecFire(p, m) {
    if (!p.alive) return true;
    const id = m.w;
    if (!this.allowed(p, id) || (this.zm && !this.zmArm(p, id))) return false;
    if (this.chaosKit && !this.chaosKit.slots.includes(id)) return false;
    return this.honLoadout(p, id) && this.honHeld(p, id);
  },
  // chicken strike / giant duck: the client aims with a 300 m ray from your eye (60 m into the air when it hits nothing)
  honAim(p, at) {
    const eyes = this.honEyes(p, false);
    for (const e of eyes) {
      const d = [at[0] - e[0], at[1] - e[1], at[2] - e[2]], l = Math.hypot(d[0], d[1], d[2]);
      if (l > HON.aimRange + HON.aimSlack + this.speedOf(p) * 0.3) continue;
      if (l < 1) return true;
      const h = raycast(e, [d[0] / l, d[1] / l, d[2] / l], l, this.boxes);
      if (!h || h.t >= l - 1.2) return true; // nothing in the way before the spot (the spot itself is on a wall / the floor)
    }
    return false;
  },
  // the Clubs shockwave: like the wrecking ball's, not through walls or the floor (a few points on them, from your middle)
  honWave(p, t) {
    const c = [p.pos[0], p.pos[1] + 1, p.pos[2]];
    for (const h of [1, 1.7, 0.3]) if (this.honClear(c, [t.pos[0], t.pos[1] + h, t.pos[2]])) return true;
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
        if (at && !this.honAim(p, at)) { deps.send(p, { t: 'streak', earned: m.r, n: p.streak || 0 }); return; } // too far / not seen: back in your tray
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
