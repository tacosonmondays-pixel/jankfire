// Zombies squad bots: a zombies squad is always 4. Bots take the empty slots; a person joining takes a bot's place
// (it leaves with a line in chat) and a person leaving gets one back. The bots really play: they shoot zombies with
// human-ish aim, earn and spend credits (doors, wall guns, ammo, the crate, Jank Cola, sometimes the Cheat Machine),
// nail planks back when it's safe, revive people (humans first), grab drops, flip the power and stay with the squad.
// They use the same rules as you: they walk up to things and hold 'use' (zmUse), with your loadout system too.
// Installed by server/zombies.js. It wraps a few Room methods (friendly, botThink, fillBots, remove, modeJoin) so
// server.js needs no changes.
import { WEAPONS, ITEMS, BOT_DIFF } from '../shared/weapons.js';
import { ZM_COLAS, zmUpPrice } from '../shared/zmshop.js';
import { ZM, zmAmmo, zmAreaAt, zmMachPrice } from '../shared/zombies.js';
import { flow, downhill, cellOf } from './zombies.js';
import { BOT_DROPS } from './zmextra.js';
import { GAMES } from '../shared/modes.js';
import { LINES } from './botlines.js';

const now = () => Date.now();
const pick = (a) => a[Math.floor(Math.random() * a.length)];
const STILL = { wx: 0, wz: 0, jump: false };
const LOG = !!process.env.JF_ZMBOT_LOG; // test knob: print what each bot decides to do
export const SQUAD = { size: Math.max(1, Math.min(4, Number(process.env.JF_ZM_SQUAD) || 4)), on: process.env.JF_ZM_BOTS !== '0' };
// each personality brings its own kit and its own idea of shopping
const KIT = {
  tryhard: { pistol: 'revolver', item: 'frag', perk: 'trustfund' },
  polite: { pistol: 'pistol', item: 'medkit', perk: 'quickhands' },
  unhinged: { pistol: 'sawnoff', item: 'frag', perk: 'rabbitfoot' },
  corpo: { pistol: 'pistol', item: 'frag', perk: 'coupons' },
  silent: { pistol: 'akimbo', item: 'medkit', perk: 'handyman' },
};
const USABLE = (w) => !!WEAPONS[w] && (WEAPONS[w].kind === 'hitscan' || WEAPONS[w].kind === 'proj'); // what a bot knows how to shoot
const flat = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);

const methods = {
  // ---------------------------------------------------------- who's in the squad
  zhBots() { return [...this.players.values()].filter((p) => p.zmh && !p.zhLeaving); },
  // keep it at 4: bots for the empty slots, one leaves when a person comes in
  zhFill() {
    if (!this.zm || !SQUAD.on || this.zhBusy || this.closed || !this.humans().length) return; // (nobody left: the room's going away)
    this.zhBusy = true;
    try {
      const people = this.humans().filter((p) => !p.watch), bots = this.zhBots(), want = Math.max(0, SQUAD.size - people.length);
      for (let i = bots.length; i < want; i++) this.zhAdd();
      if (bots.length > want) {
        const order = bots.slice().sort((a, b) => (a.alive - b.alive) || ((a.z ? a.z.c : 0) - (b.z ? b.z.c : 0))); // the dead and the broke go first
        const by = people[people.length - 1];
        for (const b of order.slice(0, bots.length - want)) this.zhRetire(b, by);
      }
    } finally { this.zhBusy = false; }
  },
  zhAdd() {
    const zs = this.zs, b = this.addBot(); // its look, skins and personality (server/botflair.js)
    b.zmh = true; b.team = 1; b.grap = b.grap || 'rope'; b.kfx = 'none'; // (no finishers in zombies)
    b.zl = { ...(KIT[b.persona] || KIT.polite) };
    this.zmJoin(b);
    b.pos = this.pickSpawn(false, b); b.vel = [0, 0, 0];
    b.zh = this.zhState();
    this.zhArm(b);
    if (zs.st === 'live' && zs.n > 0 && this.zmSquad().some((h) => h !== b && h.alive)) { b.alive = false; b.hp = 0; b.respawnAt = Infinity; b.z.dead = true; } // mid-round: in from the next one, like a person
    this.broadcast({ t: 'teams', game: this.game, list: [[b.id, 1, b.color]] });
    this.botSay(b, 'zmhi', {}, 0.5);
    return b;
  },
  zhRetire(b, by) { // a person took this bot's place: a line in chat, then it goes
    b.zhLeaving = true;
    this.zhSayNow(b, 'zmleave', { v: by ? by.name : 'you' }); // always: it's the only goodbye they get
    setTimeout(() => { try { if (this.players.get(b.id) === b) this.remove(b); } catch (e) { console.error('zmbot leave', e); } }, 2300);
  },
  zhSayNow(b, ev, vars = {}) { // a line that skips the chat cooldowns (the bot is about to leave)
    const pool = LINES[ev], list = pool && (pool[b.persona] && Math.random() < 0.55 ? pool[b.persona] : pool.any);
    if (!list) return;
    const m = pick(list).replace(/\{v\}/g, String(vars.v || 'you').replace(/ \[bot\]$/, ''));
    setTimeout(() => { try { if (this.players.get(b.id) === b) this.broadcast({ t: 'chat', id: b.id, m }); } catch (e) { console.error('zmbot say', e); } }, 600);
  },
  zhState() { return { plan: 0, task: null, useT: 0, f: new Map(), seen: 0, chk: 0, chkPos: [0, 0, 0], stuck: 0, sideT: 0, side: 1, itemT: 0, buyT: now() + 4000, look: 0 }; },

  // ---------------------------------------------------------- one bot, one think (botThink hands squad bots over)
  zhThink(b, dt) {
    const zs = this.zs, z = b.z, n = now();
    if (!z || !zs || zs.st === 'over' || n < (b.sleepUntil || 0) || b.zhLeaving) return STILL;
    const h = b.zh || (b.zh = this.zhState());
    const D = this.zhDiff();
    this.zhArm(b);
    const th = this.zhThreat(b);
    if (n >= h.plan) {
      h.plan = n + 300 + Math.random() * 250; const was = h.task && h.task.key; h.task = this.zhPlan(b, th, h.task);
      if (LOG && (h.task && h.task.key) !== was) console.log(`[zmbot] r${zs.n} ${zs.st} ${b.name} c${z.c} ${b.w}:${z.ammo[b.w] ?? '-'} -> ${h.task ? h.task.k + ' ' + h.task.key : 'squad'}${th ? ' (zombie ' + th.d.toFixed(1) + 'm)' : ''}`);
    }
    let wx = 0, wz = 0, jump = false, busy = false;
    const t = h.task;
    if (LOG && t && n - (h.posLog || 0) > 1500) { h.posLog = n; console.log(`[zmbot] ${b.name} ${t.key} at ${b.pos.map((x) => x.toFixed(1))} -> ${t.stand.map((x) => x.toFixed(1))} way ${JSON.stringify(this.zhWay(b, t.stand).map((x) => +x.toFixed(2)))} v ${Math.hypot(b.vel[0], b.vel[2]).toFixed(1)}`); }
    // a job: walk to its spot, look at the thing, hold 'use' (or just walk into a drop)
    if (t) {
      const d = flat(b.pos, t.stand);
      if (d > (t.near || 0.6)) [wx, wz] = this.zhWay(b, t.stand);
      else if (t.look) {
        busy = true;
        if (t.swap && b.z.guns.length >= ZM.guns) { const worst = b.z.guns.slice().sort((x, y) => this.zhWorth(x) - this.zhWorth(y))[0]; if (b.w !== worst) { b.w = worst; b.ai.ammo = WEAPONS[worst].mag || 1; } } // a new gun replaces the one in hand: hold the worst
        this.zhFace(b, t.look, dt * 3, 0);
        if (n - h.useT >= 180 && (t.k === 'revive' || Math.abs(this.zhAng(b, t.look)) < 0.25)) { h.useT = n; this.zmUse(b); } // (a revive only needs you standing over them)
        if (LOG && !t.logged && n - t.t0 > 6000) { t.logged = 1; console.log(`[zmbot] ${b.name} stuck using ${t.key} at ${b.pos.map((x) => x.toFixed(1))} yaw ${b.yaw.toFixed(2)} pitch ${b.pitch.toFixed(2)} ang ${this.zhAng(b, t.look).toFixed(2)} zu ${JSON.stringify(b.zu && { k: b.zu.k, done: b.zu.done })}`); }
      }
    } else {
      const a = this.zhAnchor(b); // stay with the squad
      if (a && flat(b.pos, a) > 4.5) [wx, wz] = this.zhWay(b, a);
    }
    // zombies: shoot the nearest one we can see; back off from the ones in our face
    if (th) {
      const close = th.d < (th.t.zmz.run ? 6 : 4.2) && WEAPONS[b.w].kind !== 'melee'; // runners: back off sooner
      if (!busy || th.d < (t && t.k === 'revive' ? 2.5 : 6)) this.zhFight(b, th, D, dt, n); // mid-revive: only the one in our face
      if (close && !(t && t.k === 'revive' && th.d > 1.8)) { // backpedal (sideways a bit), unless we're mid-revive
        const dx = b.pos[0] - th.t.pos[0], dz = b.pos[2] - th.t.pos[2], l = Math.hypot(dx, dz) || 1;
        wx = dx / l + (-dz / l) * h.side * 0.6; wz = dz / l + (dx / l) * h.side * 0.6;
        if (Math.random() < dt * 0.8) h.side *= -1;
        if (b.onGround && th.d < 2 && Math.random() < dt * 2) jump = true;
      }
      if (WEAPONS[b.w].kind === 'melee' && !busy) { const dx = th.t.pos[0] - b.pos[0], dz = th.t.pos[2] - b.pos[2], l = Math.hypot(dx, dz) || 1; if (th.d > 1.1) { wx = dx / l; wz = dz / l; } } // knife only: get in there
      this.zhItem(b, th, n);
    } else if (!busy && !(wx || wz)) { // nothing to do: keep an eye on the nearest window
      if (n > h.look) { h.look = n + 2500 + Math.random() * 3000; h.lookAt = this.zhWatch(b); }
      if (h.lookAt) this.zhFace(b, h.lookAt, dt * 1.5, 0);
    }
    if (b.hp < 45) this.zhItem(b, null, n); // a medkit, if that's the item
    // wedged: hop and sidestep
    if (n - h.chk > 1100) {
      const moved = flat(b.pos, h.chkPos);
      if ((wx || wz) && moved < 0.5) { h.stuck++; jump = true; h.sideT = n + 600; h.side *= -1; } else h.stuck = 0;
      h.chk = n; h.chkPos = b.pos.slice();
      if (h.stuck > 6 && t) { h.task = null; h.stuck = 0; } // give up on that job
    }
    if (n < h.sideT) { const a = h.side * 1.2, c = Math.cos(a), s = Math.sin(a); [wx, wz] = [wx * c - wz * s, wx * s + wz * c]; }
    const l = Math.hypot(wx, wz);
    if (l > 1e-6) { wx /= l; wz /= l; }
    return { wx, wz, jump };
  },
  zhDiff() { // people-like: a bit slower and sloppier than a regular bot at the same setting, so they help and don't carry
    const D = BOT_DIFF[this.cfg.diff] || BOT_DIFF.normal;
    return { ...D, err: D.err + 0.004, react: D.react + 60, rate: Math.min(1, D.rate + 0.25), turn: D.turn * 0.9 }; // fire like a person holding the trigger, aim a bit worse than a regular bot
  },

  // ---------------------------------------------------------- fighting
  zhThreat(b) {
    const e = [b.pos[0], b.pos[1] + 1.6, b.pos[2]];
    let best = null, bd = 30;
    for (const t of this.players.values()) {
      if (!t.zmz || !t.alive) continue;
      const d = Math.hypot(t.pos[0] - b.pos[0], t.pos[1] - b.pos[1], t.pos[2] - b.pos[2]);
      const keep = t.id === b.ai.target ? 3 : 0; // stick with the one we're shooting unless another is a lot closer
      if (d - keep >= bd) continue;
      if (!this.canSee(e, [t.pos[0], t.pos[1] + 1.2, t.pos[2]])) continue;
      bd = d - keep; best = t;
    }
    return best ? { t: best, d: flat(best.pos, b.pos) } : null;
  },
  zhFight(b, th, D, dt, n) {
    const t = th.t, ai = b.ai, w = WEAPONS[b.w];
    const head = (t.id + (n / 700 | 0)) % 4 === 0; // now and then they go for the head
    const aimAt = [t.pos[0], t.pos[1] + (head ? 1.95 : 1.15), t.pos[2]];
    this.zhFace(b, aimAt, D.turn * dt, 1);
    if (ai.target !== t.id) { ai.target = t.id; ai.seenAt = n - (n - (ai.shotT || 0) < 1500 ? D.react * 0.7 : 0); } // already fighting: the next one comes quicker
    const ang = Math.abs(this.zhAng(b, aimAt));
    if (n < ai.nextShot || n < ai.reloadUntil || n - ai.seenAt < D.react) return;
    if (w.kind === 'melee') { if (th.d < (w.range || 1.5) + 0.2 && ang < 0.6) { ai.shotT = n; this.zhShoot(b, t, D); } return; }
    if (ang < 0.2 && th.d < (w.range || 60)) { ai.shotT = n; this.zhShoot(b, t, D); }
  },
  zhShoot(b, t, D) { // one shot through the regular bot gun code, off the bot's own ammo
    const z = b.z;
    if (z.ammo[b.w] != null && z.ammo[b.w] <= 0) { this.zhArm(b, true); return; }
    this.botFire(b, t, D);
    if (z.ammo[b.w] != null && !this.zxMod('bottomless', b)) z.ammo[b.w] = Math.max(0, z.ammo[b.w] - 1);
  },
  // the gun in hand: the best one that still has bullets (the knife when everything's empty)
  zhArm(b, force) {
    const z = b.z;
    if (!z) return;
    const ok = (w) => w && (w === z.melee || z.guns.includes(w)) && (z.ammo[w] == null || z.ammo[w] > 0);
    if (!force && ok(b.w) && (b.w !== z.melee || !z.guns.some((g) => ok(g) && USABLE(g)))) return;
    const guns = z.guns.filter((g) => ok(g) && USABLE(g)).sort((x, y) => this.zhWorth(y) - this.zhWorth(x));
    const w = guns[0] || z.melee || 'knife';
    if (w === b.w && !force) return;
    b.w = w; b.ai.ammo = WEAPONS[w].mag || 1; b.ai.reloadUntil = now() + 450;
  },
  zhWorth(w) { const bu = this.map.zm.buys.find((x) => x.w === w); return bu ? bu.price : z0(w); },
  zhItem(b, th, n) { // the G item: grenades into a crowd, a medkit when hurt
    const h = b.zh, it = ITEMS[b.item];
    if (!it || n < h.itemT || this.itemCharges(b).n <= 0) return;
    const e = [b.pos[0], b.pos[1] + 1.6, b.pos[2]];
    if (it.heal) { if (b.hp < 45) { h.itemT = n + 3000; this.useItem(b, { i: b.item, o: e, d: [0, -1, 0] }); } return; }
    if (!it.proj || !th || th.d < 6 || th.d > 18) return;
    let crowd = 0;
    for (const o of this.players.values()) if (o.zmz && o.alive && flat(o.pos, th.t.pos) < 4.5) crowd++;
    if (crowd < 3) return;
    for (const p of this.zmSquad()) if (p !== b && p.alive && flat(p.pos, th.t.pos) < 5) return; // not on a friend
    h.itemT = n + 6000;
    const cp = Math.cos(b.pitch + 0.25);
    this.useItem(b, { i: b.item, o: e, d: [-Math.sin(b.yaw) * cp, Math.sin(b.pitch + 0.25), -Math.cos(b.yaw) * cp] });
  },

  // ---------------------------------------------------------- what to do next
  zhPlan(b, th, cur) {
    const zs = this.zs, Z = this.map.zm, z = b.z, n = now(), claims = (zs.zhClaims ||= new Map());
    for (const [k, id] of claims) { const o = this.players.get(id); if (!o || !o.alive || !o.zh || !o.zh.task || o.zh.task.key !== k) claims.delete(k); }
    const free = (k) => !claims.has(k) || claims.get(k) === b.id;
    const take = (t) => { if (t) { claims.set(t.key, b.id); t.t0 = cur && cur.key === t.key ? cur.t0 : n; } return t; };
    if (cur && n - cur.t0 > 15000) { claims.delete(cur.key); cur = null; } // took too long: something else
    const danger = th && th.d < 6;
    // 1. a friend is down: people first, then the nearest
    let best = null, bs = Infinity;
    for (const p of this.zmSquad()) {
      if (p === b || p.alive || !p.z || !p.z.down || !free('r' + p.id)) continue;
      const s = flat(b.pos, p.z.down.at) - (p.isBot ? 0 : 30);
      if (s < bs) { bs = s; best = p; }
    }
    if (best && !(th && th.d < 2.5)) { const at = best.z.down.at; return take({ k: 'revive', key: 'r' + best.id, stand: [at[0], 0, at[2]], near: 1.1, look: [at[0], at[1] + 0.3, at[2]] }); }
    if (danger) return cur && (cur.k === 'drop' || cur.k === 'power') && th.d > 3.5 ? cur : null; // fight first (a drop or the power we're already on the way to is fine)
    // 3. the power switch, once the dock's open
    if (Z.power && !zs.power && zs.areas.has(zmAreaAt(Z, Z.power.at)) && free('power')) return take({ ...this.zhUseAt('power', Z.power.at, Z.power.n, 1.2), k: 'power' });
    // 4. shopping that matters: the gun in hand is running dry, or the pockets are full
    const quiet = zs.st !== 'live' || !th || th.d > 14;
    if (cur && (cur.k === 'buy' || cur.k === 'crate' || cur.k === 'take')) { if (cur.done || z.c < (cur.price || 0)) { claims.delete(cur.key); cur = null; } else return cur; }
    const dry = z.guns.some((g) => { const mx = zmAmmo(g); return mx != null && z.ammo[g] != null && z.ammo[g] < mx * 0.3; });
    const empty = !z.guns.some((g) => z.ammo[g] == null || z.ammo[g] > 0); // down to the knife: go get bullets unless one's in our face
    if ((quiet || (empty && (!th || th.d > 7))) && n >= b.zh.buyT && (dry || empty || z.c > 1400)) { const s = this.zhShop(b, free); b.zh.buyT = n + (s ? 2500 : 1500); if (s) return take(s); }
    // 5. a drop nobody's going for (the person nearby gets first dibs)
    for (const d of zs.drops || []) {
      if (!BOT_DROPS.has(d.k) || !free('d' + d.id) || !zs.areas.has(zmAreaAt(Z, d.at))) continue;
      const age = ZM.dropLife - (d.until - n), people = this.humans().filter((p) => p.alive && !p.watch);
      if (people.some((p) => flat(p.pos, d.at) < 12) && age < 8000) continue;
      if (this.zmSquad().some((p) => p !== b && p.alive && flat(p.pos, d.at) < flat(b.pos, d.at) - 1)) continue;
      return take({ k: 'drop', key: 'd' + d.id, stand: [d.at[0], 0, d.at[2]], near: 0.5 });
    }
    // 6. a window near the squad that's lost a couple of planks, with nothing climbing through it
    if (cur && cur.k === 'board' && zs.planks[cur.i] < ZM.planks && this.zhWindowSafe(cur.i)) return cur;
    const home = this.zhAnchor(b) || b.pos;
    let wi = -1, wd = 13;
    Z.windows.forEach((w, i) => {
      if (zs.planks[i] > ZM.planks - 2 || !zs.areas.has(w.area) || !free('w' + i) || !this.zhWindowSafe(i)) return;
      const d = flat(home, w.in) * 0.6 + flat(b.pos, w.in) * 0.4 + (zs.planks[i] === 0 ? -3 : 0);
      if (d < wd) { wd = d; wi = i; }
    });
    if (wi >= 0) { const w = Z.windows[wi]; return take({ k: 'board', key: 'w' + wi, i: wi, stand: [w.at[0] + w.n[0] * 1.5, 0, w.at[2] + w.n[2] * 1.5], near: 0.5, look: [w.at[0], 1.9, w.at[2]] }); }
    // 7. the rest of the shopping (between rounds, or when it's quiet)
    if (quiet && n >= b.zh.buyT) { const s = this.zhShop(b, free); b.zh.buyT = n + (s ? 2500 : 1500); if (s) return take(s); }
    return null;
  },
  zhWindowSafe(i) { const w = this.map.zm.windows[i]; for (const o of this.players.values()) if (o.zmz && o.alive && o.zmz.ph === 'hunt' && flat(o.pos, w.in) < 4) return false; return true; },
  zhUseAt(key, at, nrm, out = 1.3, y) { // stand in front of a thing on the wall and look at it
    const fl = (this.map.zm.floors || [0]).reduce((f, yy) => (yy <= at[1] + 0.2 && yy > f ? yy : f), (this.map.zm.floors || [0])[0]); // the floor that thing is on
    return { k: 'buy', key, stand: [at[0] + nrm[0] * out, fl, at[2] + nrm[2] * out], near: 0.5, look: [at[0], y ?? at[1], at[2]] };
  },
  // what this bot buys right now (null: saving up). personalities shop differently
  zhShop(b, free) {
    const zs = this.zs, Z = this.map.zm, z = b.z, per = b.persona, c = z.c, n = now();
    const price = (p) => this.zxPrice(b, p), inside = (at) => zs.areas.has(zmAreaAt(Z, at));
    // the box offered us a gun: go get it
    if (zs.box.st === 2 && zs.box.by === b.id && USABLE(zs.box.w)) return { ...this.zhUseAt('crate', [Z.crate.at[0], Z.crate.at[1] + 0.7, Z.crate.at[2]], [0, 0, 1], 1.5), k: 'take' };
    // unhinged: the Cheat Machine, right now
    const m = zs.mach, mp = price(zmMachPrice(m.uses));
    const machOk = Z.mach && zs.power && !m.st && n >= m.cd && inside(Z.mach.at) && c >= mp && free('mach');
    if (machOk && (per === 'unhinged' ? Math.random() < 0.8 : Math.random() < (c > 4000 ? 0.4 : c > mp * 2.5 ? 0.15 : 0.03))) { const at = [Z.mach.at[0] + Z.mach.n[0] * 0.4, Z.mach.at[1] + 1.4, Z.mach.at[2] + Z.mach.n[2] * 0.4]; return { ...this.zhUseAt('mach', at, Z.mach.n, 1.2), price: mp }; }
    // no power yet: the door that leads to it comes before new guns
    if (!zs.power && zs.n >= 2) { const d = this.zhDoor(b, free, price); if (d && (d.key === 'd1' || d.key === 'd4' || d.key === 'd2' || d.key === 'd6' || this.zhPowerDoors().has(Number(d.key.slice(1))))) return d; }
    // ammo for the gun we like, when it's running low
    for (const g of z.guns) {
      const bu = Z.buys.find((x) => x.w === g), max = zmAmmo(g);
      if (!bu || max == null || !inside(bu.at) || z.ammo[g] > max * 0.3 || c < price(Math.ceil(bu.price / 20) * 10) || !free('b' + bu.w)) continue;
      return { ...this.zhUseAt('b' + bu.w, bu.at, bu.n), price: price(Math.ceil(bu.price / 20) * 10) };
    }
    // Jank Cola once the power's on
    if (Z.cola && zs.power && !z.cola && inside(Z.cola.at) && c >= price(ZM.cola) + 300 && free('cola')) return { ...this.zhUseAt('cola', [Z.cola.at[0], Z.cola.at[1] + 1.3, Z.cola.at[2]], Z.cola.n, 1.4), price: price(ZM.cola) };
    // the other colas a bot gets something out of (more ammo, getting back up), then the Warranty Voider for the gun in its hands
    for (const cl of Z.colas || []) {
      const def = ZM_COLAS[cl.id];
      if (!def || (cl.id !== 'pockets' && cl.id !== 'getup') || !zs.power || this.zsHas(b, cl.id) || this.zsColaN(b) >= ZM.colaMax || !inside(cl.at) || c < price(def.price) + 500 || !free('cola:' + cl.id)) continue;
      return { ...this.zhUseAt('cola:' + cl.id, [cl.at[0], cl.at[1] + 1.3, cl.at[2]], cl.n, 1.4), price: price(def.price) };
    }
    const up = Z.up && zs.power && z.guns.includes(b.w) && inside(Z.up.at) ? zmUpPrice(((z.up || {})[b.w] || { t: 0 }).t) : null;
    if (up != null && c >= price(up) + (per === 'tryhard' ? 0 : 800) && free('up')) return { ...this.zhUseAt('up', [Z.up.at[0] + Z.up.n[0] * 0.4, Z.up.at[1] + 1.3, Z.up.at[2] + Z.up.n[2] * 0.4], Z.up.n, 1.3), price: price(up) };
    // a better wall gun (tryhards want the priciest one they can get, the rest something decent and some change left)
    const mine = Math.max(...z.guns.filter((g) => z.ammo[g] == null || z.ammo[g] > 0).map((g) => this.zhWorth(g)), 0), keep = per === 'tryhard' ? 0 : 250; // (an empty gun with no wall to refill it is worth nothing)
    const guns = Z.buys.filter((x) => USABLE(x.w) && x.price >= 900 && !z.guns.includes(x.w) && inside(x.at) && x.price > mine && c >= price(x.price) + keep && free('b' + x.w));
    if (guns.length) { guns.sort((x, y) => y.price - x.price); const g = per === 'tryhard' ? guns[0] : pick(guns.slice(0, 2)); return { ...this.zhUseAt('b' + g.w, g.at, g.n), price: price(g.price), swap: true }; }
    // the crate, now and then
    if (Z.crate && !zs.box.st && inside(Z.crate.at) && c >= price(ZM.crate) + 400 && free('crate') && Math.random() < (per === 'tryhard' ? 0.35 : 0.15)) return { ...this.zhUseAt('crate', [Z.crate.at[0], Z.crate.at[1] + 0.7, Z.crate.at[2]], [0, 0, 1], 1.5), k: 'crate', price: price(ZM.crate) };
    return this.zhDoor(b, free, price);
  },

  // the shut doors on a shortest way (fewest doors) from what's open to the room with the power switch: any map
  zhPowerDoors() {
    const zs = this.zs, Z = this.map.zm, out = new Set();
    if (!Z.power || zs.power) return out;
    const goal = zmAreaAt(Z, [Z.power.at[0] + Z.power.n[0], Z.power.at[1], Z.power.at[2] + Z.power.n[2]]);
    if (!goal || zs.areas.has(goal)) return out;
    const from = new Map([...zs.areas].map((a) => [a, -1])), q = [...zs.areas]; // area -> the door we came through
    for (let h = 0; h < q.length && !from.has(goal); h++) Z.doors.forEach((d, i) => { const o = d.a === q[h] ? d.b : d.b === q[h] ? d.a : null; if (o && !from.has(o)) { from.set(o, [i, q[h]]); q.push(o); } });
    for (let a = goal, n = 0; from.get(a) && from.get(a) !== -1 && n < 32; n++) { const [i, prev] = from.get(a); if (!zs.open[i]) out.add(i); a = prev; }
    return out;
  },
  zhDoor(b, free, price) { // a door: toward the power while it's off, otherwise the one nearest the squad
    const zs = this.zs, Z = this.map.zm, c = b.z.c, per = b.persona, pw = this.zhPowerDoors();
    let best = null, bs = Infinity;
    Z.doors.forEach((d, i) => {
      if (zs.open[i] || !free('d' + i)) return;
      const ina = zs.areas.has(d.a), inb = zs.areas.has(d.b);
      if (ina === inb || c < price(d.price) + (per === 'corpo' ? 0 : 150)) return;
      const toPower = d.b === 'toys' || d.b === 'dock' || pw.has(i);
      if (!toPower && c < 3000 && zs.open.filter(Boolean).length >= 2) return; // more doors = more windows to hold: only when rich
      const s = (!zs.power && (d.b === 'dock' || d.a === 'dock' || d.b === 'toys' || pw.has(i)) ? -80 : 0) + flat(b.pos, d.at) * 0.5 + Math.abs(b.pos[1] - d.box.min[1]) * 2 + d.price / 100; // the power first: it turns the cola on (a door on another floor is a walk)
      if (s < bs) { bs = s; best = { d, i, side: ina ? d.a : d.b }; }
    });
    if (best && (zs.n >= 2 || per === 'corpo' || per === 'tryhard')) {
      const { d, i, side } = best, thinX = d.box.max[0] - d.box.min[0] < 1;
      const fy = d.box.min[1]; // the floor the shutter stands on (maps with an upstairs)
      const opts = thinX ? [[d.at[0] - 1.3, fy, d.at[2]], [d.at[0] + 1.3, fy, d.at[2]]] : [[d.at[0], fy, d.at[2] - 1.3], [d.at[0], fy, d.at[2] + 1.3]];
      const stand = opts.find((p) => zmAreaAt(Z, [p[0], p[1] + 0.1, p[2]]) === side) || opts[0];
      return { k: 'buy', key: 'd' + i, stand, near: 0.5, look: [d.at[0], fy + 1.5, d.at[2]], price: price(d.price) };
    }
    return null;
  },

  // ---------------------------------------------------------- getting about
  zhAnchor(b) { // who to stay with: the nearest person, else the other bots, else the start
    let best = null, bd = Infinity;
    for (const p of this.humans()) if (p.alive && !p.watch) { const d = flat(p.pos, b.pos); if (d < bd) { bd = d; best = p.pos; } }
    if (best) return best;
    const o = this.zmSquad().filter((p) => p !== b && p.alive);
    if (o.length) { const lead = o.reduce((a, p) => (p.id < a.id ? p : a), o[0]); if (lead.id < b.id) return lead.pos; } // follow the oldest bot
    const a = this.map.zm.areas.find((x) => x.id === this.map.zm.start), r = a.r;
    return [(r[0] + r[2]) / 2, 0, (r[1] + r[3]) / 2 + 3];
  },
  zhWatch(b) { // the nearest window in an open area
    const Z = this.map.zm;
    let best = null, bd = 18;
    for (const w of Z.windows) if (this.zs.areas.has(w.area)) { const d = flat(b.pos, w.in); if (d < bd) { bd = d; best = [w.at[0], w.at[1] - 0.3, w.at[2]]; } }
    return best;
  },
  // which way to walk to p: straight if nothing's in the way, else downhill on a flow field from p
  zhWay(b, p) {
    const zs = this.zs, dx = p[0] - b.pos[0], dz = p[2] - b.pos[2], d = Math.hypot(dx, dz) || 1e-6;
    if (d < 10 && Math.abs((p[1] ?? b.pos[1]) - b.pos[1]) < 1.4 && this.zmClear(b.pos, [p[0], b.pos[1], p[2]], d)) return [dx / d, dz / d]; // (same floor)
    const nav = zs.nav, c = cellOf(nav, p);
    if (c < 0) return [dx / d, dz / d];
    const f = this.zhField(c, p);
    const q = downhill(nav, zs.open, f, b.pos, this.boxes);
    if (!q) return [dx / d, dz / d];
    const ex = q[0] - b.pos[0], ez = q[1] - b.pos[2], el = Math.hypot(ex, ez) || 1;
    return [ex / el, ez / el];
  },
  zhField(c, p) { // flow fields to a spot, shared by the squad, redone every few seconds and when a door opens
    const zs = this.zs, F = (zs.zhF ||= new Map()), n = now();
    let f = F.get(c);
    if (!f || n - f.t > 4000 || f.t < zs.fieldT) {
      if (!f) { if (F.size > 24) F.delete(F.keys().next().value); f = { d: new Float32Array(zs.nav.N), t: 0 }; F.set(c, f); }
      flow(zs.nav, zs.open, [p[0], (p[1] || 0) + 0.5, p[2]], this.boxes, f.d); f.t = n;
    }
    return f.d;
  },
  zhFace(b, at, k, eye) { // turn toward a point (eye = from the eyes, else from the chest)
    const e = [b.pos[0], b.pos[1] + 1.6, b.pos[2]], dx = at[0] - e[0], dy = at[1] - e[1], dz = at[2] - e[2], hd = Math.hypot(dx, dz) || 1e-6;
    const yaw = Math.atan2(-dx, -dz), pitch = Math.atan2(dy, hd);
    let d = yaw - b.yaw; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2;
    const t = Math.min(1, k);
    b.yaw += d * t; b.pitch += (pitch - b.pitch) * t;
    return eye;
  },
  zhAng(b, at) { const dx = at[0] - b.pos[0], dz = at[2] - b.pos[2]; let d = Math.atan2(-dx, -dz) - b.yaw; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2; return d; },
};
const z0 = (w) => (w === 'knife' ? -1 : 0); // guns that aren't on a wall (the start pistols, crate guns) rank low

export function installZmBots(Room) {
  Object.assign(Room.prototype, methods);
  const P = Room.prototype;
  const wrap = (name, fn) => { const orig = P[name]; P[name] = function (...a) { return fn.call(this, orig, ...a); }; };
  // zombies: the squad's bots are on the people's side (everyone else in there is a zombie)
  wrap('friendly', function (orig, a, b) { if (this.zm && a && b && a !== b && (a.zmh || b.zmh)) return !!a.zmz === !!b.zmz; return orig.call(this, a, b); });
  // the regular bot guns hit at 70% (they're softened for PvP). against zombies the squad's bots hit at 85%: a hand, not a carry
  wrap('applyHitscan', function (orig, p, t, wid, n, h, d, mul = 1) { return orig.call(this, p, t, wid, n, h, d, this.zm && p && p.zmh ? mul * (0.85 / 0.7) : mul); });
  wrap('botThink', function (orig, b, dt) { return this.zm && b.zmh ? this.zhThink(b, dt) : orig.call(this, b, dt); });
  // join a running zombies room while it still has a bot to swap out (4 = people + bots)
  wrap('botWant', function (orig, ...a) { if (GAMES[this.game] && GAMES[this.game].zombies && !this.lobby && SQUAD.on) return Math.max(0, SQUAD.size - this.humans().filter((p) => !p.watch).length); return orig.apply(this, a); });
  wrap('fillBots', function (orig, ...a) { if (this.zm) { this.zhFill(); return; } return orig.apply(this, a); });
  wrap('remove', function (orig, p) { const r = orig.call(this, p); if (this.zm && !p.isBot && !p.watch) this.zhFill(); return r; }); // a person left: a bot takes the slot
  wrap('modeJoin', function (orig, p) { const r = orig.call(this, p); if (this.zm && !p.isBot && !p.watch) this.zhFill(); return r; }); // a person came in: a bot makes room
  wrap('zmReset', function (orig, ...a) { const r = orig.apply(this, a); if (this.zm) { for (const b of this.zhBots()) { b.zh = this.zhState(); this.zhArm(b, true); } this.zhFill(); } return r; });
  // chat: going down, getting someone up, buying things
  wrap('zmKilled', function (orig, t, killer, w) { const r = orig.call(this, t, killer, w); if (t.zmh && t.z && t.z.down) this.botSay(t, 'zmdown', {}, 0.55); return r; });
  wrap('zmRevive', function (orig, h, by) {
    const r = orig.call(this, h, by);
    if (by && by.zmh) this.botSay(by, 'zmrevive', { v: h.name }, h.isBot ? 0.3 : 0.7, !h.isBot);
    else if (h.zmh && by) this.botSay(h, 'zmthanks', { v: by.name }, 0.7, true);
    if (h.zmh) this.zhArm(h, true);
    return r;
  });
  wrap('zmGrant', function (orig, p, w) { const r = orig.call(this, p, w); if (p.zmh) { this.zhArm(p, true); if (p.zh && p.zh.task) p.zh.task.done = true; this.botSay(p, 'zmbuy', { w: (WEAPONS[w] ? WEAPONS[w].name : w).toLowerCase() }, 0.5); } return r; });
  wrap('zxMach', function (orig, p, t) { const c = p.z && p.z.c; const r = orig.call(this, p, t); if (p.zmh && p.z.c < c) { if (p.zh && p.zh.task) p.zh.task.done = true; this.botSay(p, 'zmmach', {}, 0.8); } return r; });
  wrap('zmOpen', function (orig, i, by) { const r = orig.call(this, i, by); if (by && by.zmh && by.zh && by.zh.task) by.zh.task.done = true; return r; });
  wrap('zmCleared', function (orig, n, hs) { const r = orig.call(this, n, hs); const bs = this.zhBots().filter((b) => b.alive); if (bs.length && Math.random() < 0.5) this.botSay(pick(bs), 'zmround', { v: String(this.zs.n) }, 0.6); return r; });
  // a bot's jobs that finish with a 'use' (cola, ammo, the crate spin) are done when the money moves
  wrap('zmPay', function (orig, p, price, k) { const r = orig.call(this, p, price, k); if (r && p.zmh && p.zh && p.zh.task) p.zh.task.done = true; return r; });
}
