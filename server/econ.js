// Plant & Defuse economy, server side: credits, a buy phase behind spawn barriers, gear that drops when you die, ammo the
// server counts per weapon, armor, the defuse kit, no grapple, no killstreaks, bots that buy. The rules and numbers live in
// shared/econ.js; this file adds econ* methods to Room (installEcon, called from server.js). See DESIGN.md (wf_econ).
import { WEAPONS, ITEMS, FLAGS } from '../shared/weapons.js';
import { TAC } from '../shared/tactical.js';
import { BOMB } from '../shared/modes.js';
import { ECON, ARMOR, BLAST, GEAR, econWeapon, weaponPrice, refillPrice, killReward, armorPen, ammoSpec, itemSpec, gearPrice } from '../shared/econ.js';
import { raycast, PH } from '../shared/physics.js';
import AI, { aiDeps } from './econai.js'; // the team tactics (buying, executes, holds, rotations, retakes)

// test knobs: JF_ECON=0 turns the economy off (Plant & Defuse as before), short buy phases, start / max credits
const OFF = process.env.JF_ECON === '0';
if (process.env.JF_BUY_TIME) ECON.buyTime = Math.max(1, Number(process.env.JF_BUY_TIME) || ECON.buyTime);
if (process.env.JF_START_MONEY) ECON.start = Math.max(0, Number(process.env.JF_START_MONEY) || 0);
if (process.env.JF_ECON_MAX) ECON.max = Math.max(ECON.start, Number(process.env.JF_ECON_MAX) || ECON.max);

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const has = (T, k) => typeof k === 'string' && Object.hasOwn(T, k);
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
const pick = (a) => a[(Math.random() * a.length) | 0];
const DAY = 864e5; // "respawn" time for the dead: they come back with the next round
const BLASTS = new Set(BLAST);
const KINDS = { w: 1, i: 1, g: 1 };
const DROP_SLOTS = { primary: 1, secondary: 1, melee: 1, item: 1, kit: 1 };
const WSLOTS = ['primary', 'secondary', 'melee'];
const ZONES = new WeakMap(); // map -> side zones
// what bots buy: full buys pick from the first list, force buys from the second
const BOT_FULL = ['ar', 'ar', 'redline', 'redline', 'chicken', 'minigun', 'sniper'];
const BOT_FORCE = ['smg', 'smg', 'shotgun', 'banana', 'bowling'];
// bots fire hitscan guns and projectiles (botFire); anything else they could only carry
const botGun = (id) => has(WEAPONS, id) && WEAPONS[id].slot !== 'melee' && (WEAPONS[id].kind === 'hitscan' || WEAPONS[id].kind === 'proj');

let D = null; // helpers from server.js: send, cleanSkins, enforceSkins, refreshInv, logErr, BOT_GUNS

function zoneOf(list) {
  if (!Array.isArray(list) || !list.length) return null;
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const q of list) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], q[k]); max[k] = Math.max(max[k], q[k]); }
  const pd = ECON.zonePad;
  return { min: [r2(min[0] - pd), r2(min[1] - ECON.zoneBelow), r2(min[2] - pd)], max: [r2(max[0] + pd), r2(max[1] + ECON.zoneAbove), r2(max[2] + pd)] };
}
const inZone = (z, q, s = 0) => !!z && q[0] >= z.min[0] - s && q[0] <= z.max[0] + s && q[2] >= z.min[2] - s && q[2] <= z.max[2] + s;
function instView(x) {
  return x ? { u: x.u, id: x.id, m: x.m, r: x.r, lim: x.lim ? 1 : 0, cl: x.cl ? 1 : 0, sk: x.sk, by: x.byName, kat: x.kat || 0, def: x.def ? 1 : 0 } : null;
}
function dropView(d) {
  const v = { id: d.id, k: d.k, p: d.p };
  if (d.np && d.np.id) v.o = d.np.id; // who put it down (a drop, a swap, a buy): the client throws it from their hand
  if (d.k === 'w') Object.assign(v, { w: d.x.id, u: d.x.u, m: d.x.m, r: d.x.r, lim: d.x.lim ? 1 : 0, cl: d.x.cl ? 1 : 0, sk: d.x.sk, by: d.x.byName, kat: d.x.kat || 0 });
  else if (d.k === 'i') Object.assign(v, { w: d.iid, n: d.n });
  else v.w = 'kit';
  return v;
}

const M = {
  // ---------------------------------------------------------- switches
  // the economy runs in Plant & Defuse with teams on (Online + Bots rooms), unless JF_ECON=0
  isEcon() { return !OFF && !!this.bomb && ECON.games.includes(this.game) && this.teamsOn(); },
  hookOff() { return !ECON.grapple && this.isEcon(); }, // no grappling hook (players or bots)
  streaksOn() { return ECON.streaks || !this.isEcon(); }, // killstreaks can be earned
  econBuying(n = now()) { const b = this.bomb; return !!(b && b.buyUntil && n < b.buyUntil); },
  // how long a plant / defuse takes (a defuse kit makes it shorter)
  actMs(a) { return (a.kind === 'plant' ? BOMB.plant : a.kit ? ECON.kitDefuse : BOMB.defuse) * 1000; },

  ecRoom() {
    return this.ec || (this.ec = { lose: { 1: 0, 2: 0 }, att: this.bomb ? this.bomb.att : 1, drops: new Map(), nextDrop: 1, nextU: 1, planted: false, defuser: 0, dirty: new Set(), moneyT: 0 });
  },
  econNewInst(id, owner, def) {
    const a = ammoSpec(id), sk = owner && owner.ecOwnSkins && owner.ecOwnSkins[id];
    return {
      u: this.ecRoom().nextU++, id, m: a ? a.mag : 0, r: a ? a.res : 0, lim: !!a, cl: !!(a && a.clip),
      sk: Array.isArray(sk) ? sk.slice() : null, by: owner ? owner.id : 0, byName: owner ? owner.name : '', kat: 0, def: !!def, fresh: true, shot: null,
    };
  },
  econInst(p, id) {
    const e = p.ec;
    if (!e || typeof id !== 'string') return null;
    for (const s of WSLOTS) if (e.sl[s] && e.sl[s].id === id) return e.sl[s];
    return null;
  },
  econOwns(p, id) { return !!this.econInst(p, id); },

  // ---------------------------------------------------------- players
  econInitPlayer(p, money) {
    if (!p.ec) { p.ecOwnSkins = { ...(p.skins || {}) }; p.ecOwnItem = p.item; }
    p.ec = { $: money, sl: { primary: null, secondary: null, melee: null }, it: null, ar: 0, hm: false, kit: false, rc: [], ib: {}, out: false, zone: null, rk: 0, rkm: 0, rl: null, fresh: !p.isBot, zT: 0, buyAt: 0 };
    if (!p.isBot) p.forced = true; // when the mode ends, sendLoadout hands the player their own loadout back
    p.pocket = []; p.scythe = false; p.streak = 0; p.nextItem = null;
    if (!p.isBot) D.send(p, { t: 'streak', reset: 1 });
    if (p.kat) { p.kat = 0; this.broadcast({ t: 'kat', id: p.id, n: 0 }); }
    this.econDefaultKit(p);
    return p.ec;
  },
  econDefaultKit(p) {
    const e = p.ec;
    if (!e.sl.secondary && econWeapon(ECON.defaultSecondary)) e.sl.secondary = this.econNewInst(ECON.defaultSecondary, p);
    if (!e.sl.melee) e.sl.melee = this.econNewInst(ECON.defaultMelee, p, true);
  },
  econStrip(p) {
    const e = p.ec;
    e.sl = { primary: null, secondary: null, melee: null }; e.it = null; e.ar = 0; e.hm = false; e.kit = false; e.rl = null;
    if (p.kat) { p.kat = 0; this.broadcast({ t: 'kat', id: p.id, n: 0 }); }
  },
  // someone joins a match that's already going (a human from addHuman before 'welcome', a bot from addBot): the team's
  // average credits, and if the round is past its buy phase they sit it out
  econJoin(p) {
    this.ecRoom();
    const mates = this.fighters().filter((o) => o !== p && o.team === p.team && o.ec);
    const avg = mates.length ? mates.reduce((s, o) => s + o.ec.$, 0) / mates.length : ECON.start;
    this.econInitPlayer(p, Math.min(ECON.max, Math.max(ECON.joinerMin, Math.floor(avg / 50) * 50)));
    if (!this.econBuying()) { p.alive = false; p.hp = 0; p.respawnAt = p.minRespawnAt = now() + DAY; p.ec.out = true; }
    else { p.ec.zone = this.econZoneFor(p); if (p.isBot) p.ec.buyAt = now() + 500 + Math.random() * 1000; }
    this.econSync(p);
  },
  econLeave(p) { if (p.ec && p.alive && !p.ec.out) this.econDropAll(p); },
  // the mode ended (sendLoadout outside the economy): your own skins, item and loadout again
  econEnd(p) {
    if (this.ec) { if (this.ec.drops.size) this.broadcast({ t: 'drc' }); this.ec = null; }
    if (!p.ec) return;
    const own = p.ecOwnSkins || {};
    if (JSON.stringify(own) !== JSON.stringify(p.skins || {})) { p.skins = own; this.broadcast({ t: 'sk', id: p.id, s: own }, p.id); }
    if (p.kat) { p.kat = 0; this.broadcast({ t: 'kat', id: p.id, n: 0 }); }
    if (has(ITEMS, p.ecOwnItem)) p.item = p.ecOwnItem;
    p.ic = null; p.ec = null; p.ecOwnSkins = null; p.ecOwnItem = null;
    if (p.isBot) { p.w = pick(D.BOT_GUNS); p.ai.ammo = WEAPONS[p.w].mag || 1; return; }
    this.sendIc(p);
    D.send(p, { t: 'inv', off: 1 });
  },
  // sendLoadout in this mode: the round's gear instead of a loadout (after every 'spawn' and right after 'welcome')
  econLoadout(p) {
    if (!p.ec) this.econJoin(p);
    if (p.alive && this.econBuying()) p.ec.zone = this.econZoneFor(p);
    this.econSync(p);
    if (p.isBot) return;
    if (p.ec.fresh) { // a joiner: the round and the floor as they are now
      p.ec.fresh = false;
      D.send(p, { t: 'eround', ...this.econRoundView() });
      D.send(p, { t: 'drs', list: [...this.ec.drops.values()].map(dropView) });
    }
    this.econSend(p);
  },
  // inventory -> the state the rest of the server reads: item + charges, katana length, skins on show, held weapon
  econSync(p) {
    const e = p.ec;
    if (!e) return;
    if (e.it && has(ITEMS, e.it.id) && e.it.n > 0) { p.item = e.it.id; p.ic = { i: e.it.id, n: e.it.n, next: 0 }; }
    else { e.it = null; if (!has(ITEMS, p.item)) p.item = 'frag'; p.ic = { i: p.item, n: 0, next: 0 }; }
    const mel = e.sl.melee, kat = mel && mel.id === 'katana' ? mel.kat || 0 : 0;
    if ((p.kat || 0) !== kat) { p.kat = kat; this.broadcast({ t: 'kat', id: p.id, n: kat }); }
    // a weapon shows the skin of whoever bought it (no skin = the default look, not yours)
    const s = { ...(p.ecOwnSkins || {}) };
    for (const x of Object.values(e.sl)) if (x) { if (x.sk) s[x.id] = x.sk; else delete s[x.id]; }
    if (JSON.stringify(s) !== JSON.stringify(p.skins || {})) { p.skins = s; this.broadcast({ t: 'sk', id: p.id, s }, p.id); }
    if (p.isBot) this.econBotWeapon(p);
    else if (!this.econOwns(p, p.w)) p.w = (e.sl.primary || e.sl.secondary || e.sl.melee).id;
  },
  econView(p) {
    const e = p.ec;
    return {
      $: e.$, sl: { primary: instView(e.sl.primary), secondary: instView(e.sl.secondary), melee: instView(e.sl.melee) },
      it: e.it ? { id: e.it.id, n: e.it.n } : null, ar: Math.round(e.ar), hm: e.hm ? 1 : 0, kit: e.kit ? 1 : 0,
      zone: e.zone, out: e.out ? 1 : 0, ib: e.ib, sell: e.rc.filter((r) => r.ok()).map((r) => [r.k, r.id]),
    };
  },
  econSend(p) {
    this.ecRoom().dirty.add(p.team);
    if (p.isBot) return;
    D.send(p, { t: 'inv', ...this.econView(p) });
    this.sendIc(p);
  },
  econPay(p, a, why, extra) {
    const e = p.ec;
    if (!e) return;
    const before = e.$;
    e.$ = clamp(e.$ + a, 0, ECON.max);
    this.ecRoom().dirty.add(p.team);
    if (!p.isBot) D.send(p, { t: 'ecash', a, got: e.$ - before, why, $: e.$, ...extra });
  },
  econFlushMoney() {
    const ec = this.ec;
    ec.moneyT = now();
    for (const team of ec.dirty) {
      const list = this.fighters().filter((p) => p.team === team && p.ec);
      const m = list.map((p) => [p.id, p.ec.$]);
      for (const p of list) if (!p.isBot) D.send(p, { t: 'emoney', m });
    }
    ec.dirty.clear();
  },

  // ---------------------------------------------------------- rounds
  econRoundView() {
    const b = this.bomb, ec = this.ecRoom();
    return {
      n: b.n, att: b.att, half: b.n > BOMB.swapAfter ? 2 : 1, pistol: b.n === 1 || b.n === BOMB.swapAfter + 1 ? 1 : 0,
      buy: Math.max(0, (b.buyUntil || 0) - now()), zones: this.econZones(), lose: [ec.lose[1], ec.lose[2]], start: ECON.start, max: ECON.max,
    };
  },
  econRoundInfo(r) {
    const b = this.bomb, ec = this.ec;
    if (!ec) return;
    r.eco = { buy: Math.max(0, (b.buyUntil || 0) - now()), lose: [ec.lose[1], ec.lose[2]] };
    // what everyone wears (vest 1, bucket 2, pliers 4): the client puts it on their models
    const g = [];
    for (const p of this.fighters()) { const e = p.ec; if (e && p.alive && !e.out) { const k = (e.ar > 0 ? 1 : 0) | (e.hm ? 2 : 0) | (e.kit ? 4 : 0); if (k) g.push([p.id, k]); } }
    if (g.length) r.eco.gear = g;
  },
  // newBombRound, before everyone respawns: a fresh match, the half (sides swapped: credits reset), or the next round
  econNewRound(first) {
    const b = this.bomb, n = now();
    const half = !first && !!this.ec && b.att !== this.ec.att;
    if (first || !this.ec) this.ec = null;
    const ec = this.ecRoom();
    ec.att = b.att;
    if (first || half) ec.lose = { 1: 0, 2: 0 };
    if (ec.drops.size) { ec.drops.clear(); this.broadcast({ t: 'drc' }); }
    for (const p of this.fighters()) {
      if (first || half || !p.ec) this.econInitPlayer(p, ECON.start);
      else if (!p.alive || p.ec.out) { this.econStrip(p); this.econDefaultKit(p); } // died (or sat out): the default kit
      const e = p.ec;
      e.out = false; e.rc = []; e.ib = {}; e.rk = 0; e.rkm = 0; e.rl = null; e.zone = null; e.fresh = false; e.said = null; // 'eround' below tells them
      for (const x of Object.values(e.sl)) if (x) x.shot = null;
      e.buyAt = p.isBot ? n + Math.min(ECON.buyTime * 600, 700 + Math.random() * 2500) : 0; // bots shop in the first seconds
    }
    if (half) this.broadcast({ t: 'chat', id: 0, m: `HALF TIME: sides swapped, everyone back to ${ECON.start} credits` });
    ec.planted = false; ec.defuser = 0;
    b.buyUntil = n + ECON.buyTime * 1000;
    b.ends += ECON.buyTime * 1000; // the round clock starts when the barriers drop
    ec.dirty.add(1); ec.dirty.add(2);
    this.broadcast({ t: 'eround', ...this.econRoundView() });
  },
  // bombRoundWin: pay everyone for the round (kill rewards were paid as they happened)
  econRoundEnd(win, why) {
    const b = this.bomb, ec = this.ecRoom(), lose = 3 - win;
    ec.lose[win] = 0;
    ec.lose[lose] = Math.min(ECON.loss.length, ec.lose[lose] + 1);
    const lossPay = ECON.loss[ec.lose[lose] - 1];
    if (why === 'defused' && ec.defuser) { const d = this.players.get(ec.defuser); if (d && d.ec) this.econPay(d, ECON.defuse, 'defuse'); }
    for (const p of this.fighters()) {
      const e = p.ec;
      if (!e || !p.team) continue;
      const lines = [];
      if (p.team === win) lines.push(['win', ECON.win[why] ?? ECON.win.elim]);
      else {
        // attackers who hide out the clock without planting don't get the loss bonus
        const saver = why === 'time' && p.team === b.att && p.alive && !e.out && !ec.planted && !ECON.timeSurvivorBonus;
        lines.push(saver ? ['nobonus', 0] : ['loss', lossPay, ec.lose[lose]]);
        if (p.team === b.att && ec.planted) lines.push(['plant', ECON.plantTeam]);
      }
      let total = 0;
      for (const l of lines) total += l[1];
      const before = e.$;
      e.$ = clamp(e.$ + total, 0, ECON.max);
      if (!p.isBot) D.send(p, { t: 'epay', win: p.team === win ? 1 : 0, why, lines, kills: [e.rk, e.rkm], total, got: e.$ - before, $: e.$, streak: ec.lose[p.team] });
    }
    ec.dirty.add(1); ec.dirty.add(2);
    this.econFlushMoney();
    this.econAiRoundEnd(win, why);
  },
  // end of kill(): no respawn this round, the kill reward, and the victim's gear goes on the floor
  econOnKill(t, killer, w, via) {
    t.respawnAt = t.minRespawnAt = now() + DAY;
    if (killer && killer !== t && killer.ec && killer.team !== t.team) {
      const wid = w === 'void' || w === 'cough' ? via || w : w;
      const a = killReward(wid);
      killer.ec.rk++; killer.ec.rkm += a;
      this.econPay(killer, a, 'kill', { w: wid, v: t.id });
      const mel = killer.ec.sl.melee;
      if (wid === 'katana' && mel && mel.id === 'katana') mel.kat = killer.kat || 0; // the blade keeps its length
    }
    if (t.ec && !t.ec.out) { this.econDropAll(t); this.econSync(t); this.econSend(t); }
    this.econAiDeath(t, killer);
  },

  // ---------------------------------------------------------- spawn barriers
  econZones() {
    const m = this.map, ts = m.teamSpawns;
    if (!ts) return { att: null, def: null };
    let z = ZONES.get(m);
    if (!z) { z = { att: zoneOf(ts.att), def: zoneOf(ts.def) }; ZONES.set(m, z); }
    return z;
  },
  // your side's zone if you spawned in it, else a box around where you spawned (maps without team spawns)
  econZoneFor(p) {
    const z = this.econZones()[p.team === this.bomb.att ? 'att' : 'def'];
    if (inZone(z, p.pos)) return z;
    const s = ECON.personalZone, q = p.pos;
    return { min: [r2(q[0] - s), r2(q[1] - ECON.zoneBelow), r2(q[2] - s)], max: [r2(q[0] + s), r2(q[1] + ECON.zoneAbove), r2(q[2] + s)] };
  },
  // where the server holds you and where your client last said you are both have to be inside
  econInZone(p) { const e = p.ec; return !!e && inZone(e.zone, p.pos, ECON.zoneSlack) && (!e.said || inZone(e.zone, e.said, ECON.zoneSlack)); },
  // during the buy phase nobody leaves their zone: past the edge (plus slack) the server puts you back inside
  econHold(p, n) {
    const z = p.ec.zone;
    if (inZone(z, p.pos, ECON.zoneSlack)) return;
    const q = p.pos;
    p.pos = [clamp(q[0], z.min[0] + 0.3, z.max[0] - 0.3), q[1], clamp(q[2], z.min[2] + 0.3, z.max[2] - 0.3)];
    p.vel[0] = 0; p.vel[2] = 0;
    if (p.isBot) { if (p.ai) p.ai.route = null; return; }
    if (n - p.ec.zT > 150) { p.ec.zT = n; D.send(p, { t: 'ezone', p: p.pos.map(r2) }); }
  },

  // ---------------------------------------------------------- the floor: dropped gear
  econDrop(k, data, at, noPickId) {
    if (!at) return null;
    const ec = this.ecRoom();
    const d = { id: ec.nextDrop++, k, p: at.map(r2), born: now(), ...data, np: noPickId ? { id: noPickId, until: now() + ECON.dropNoPick } : null };
    if (d.x) { d.x.fresh = false; d.x.shot = null; }
    ec.drops.set(d.id, d);
    this.broadcast({ t: 'dr+', ...dropView(d) });
    while (ec.drops.size > ECON.maxDrops) { const old = ec.drops.keys().next().value; ec.drops.delete(old); this.broadcast({ t: 'drx', id: old }); }
    return d;
  },
  econFeet(p) {
    let f = this.floorAt(p.pos);
    if (f) return [p.pos[0], f[1] + 0.15, p.pos[2]];
    f = this.floorAt(p.ground);
    return f ? [f[0], f[1] + 0.15, f[2]] : null;
  },
  // a manual drop lands a step in front of you (not through a wall, not off a ledge into the void)
  econAhead(p) {
    const e = [p.pos[0], p.pos[1] + PH.eye, p.pos[2]], f = [-Math.sin(p.yaw || 0), 0, -Math.cos(p.yaw || 0)];
    const h = raycast(e, f, 1.6, this.boxes), d = h ? Math.max(0, h.t - 0.45) : 1.6;
    const q = [p.pos[0] + f[0] * d, p.pos[1] + 0.5, p.pos[2] + f[2] * d];
    const fl = this.floorAt(q);
    if (fl && fl[1] > p.pos[1] - 3) return [q[0], fl[1] + 0.15, q[2]];
    return this.econFeet(p);
  },
  // dying: everything but the default melee goes on the floor around the body (lost if they died over the void)
  econDropAll(t) {
    const e = t.ec, list = [];
    for (const s of WSLOTS) { const x = e.sl[s]; if (x && !x.def) list.push(['w', { x }]); }
    if (e.it && e.it.n > 0) list.push(['i', { iid: e.it.id, n: e.it.n }]);
    if (e.kit) list.push(['k', {}]);
    const at = this.econFeet(t);
    if (at) list.forEach(([k, data], i) => {
      const a = (i / list.length) * Math.PI * 2 + (t.yaw || 0), rr = list.length > 1 ? 0.65 : 0;
      const q = [at[0] + Math.cos(a) * rr, at[1], at[2] + Math.sin(a) * rr], f = this.floorAt(q);
      this.econDrop(k, data, f && Math.abs(f[1] + 0.15 - at[1]) < 1 ? [q[0], f[1] + 0.15, q[2]] : at, 0);
    });
    this.econStrip(t);
    e.sl.melee = this.econNewInst(ECON.defaultMelee, t, true);
  },
  // pick up drop d: auto (walking over it) only fills an empty slot; manual swaps with what you have
  econTake(p, d, manual) {
    const e = p.ec, ec = this.ec;
    const gone = () => {
      ec.drops.delete(d.id); this.broadcast({ t: 'drx', id: d.id, by: p.id });
      if (p.isBot && p.ai && p.ai.gift === d.id) { p.ai.gift = 0; if (ec.tac) this.tacLog(ec.tac, `${p.name} picks up the ${WEAPONS[d.x.id].name} a teammate dropped`); }
    };
    if (d.k === 'w') {
      const x = d.x, slot = WEAPONS[x.id].slot, cur = e.sl[slot];
      if (cur && !manual) return false;
      gone();
      if (cur && !cur.def) this.econDrop('w', { x: cur }, d.p, p.id); // swap: yours goes where that one was
      e.sl[slot] = x;
    } else if (d.k === 'i') {
      const s = itemSpec(d.iid);
      if (!s) return false;
      const other = e.it && e.it.id !== d.iid && e.it.n > 0;
      if (other && !manual) return false;
      const have = e.it && e.it.id === d.iid ? e.it.n : 0, take = Math.min(d.n, s.limit - have);
      if (take <= 0) return false;
      if (other) this.econDrop('i', { iid: e.it.id, n: e.it.n }, d.p, p.id);
      e.it = { id: d.iid, n: have + take };
      d.n -= take;
      if (d.n <= 0) gone(); else this.broadcast({ t: 'dr+', ...dropView(d) });
    } else {
      if (e.kit || p.team === this.bomb.att) return false;
      gone();
      e.kit = true;
    }
    this.econSync(p);
    this.econSend(p);
    return true;
  },
  econAutoPicks(n) {
    const R = ECON.autoR;
    for (const p of this.fighters()) {
      if (!p.alive || !p.ec || p.ec.out) continue;
      for (const d of this.ec.drops.values()) {
        if (d.np && d.np.id === p.id && n < d.np.until) continue;
        if (Math.abs(p.pos[1] - d.p[1]) > 1.5 || Math.hypot(p.pos[0] - d.p[0], p.pos[2] - d.p[2]) > R) continue;
        if (this.econTake(p, d, false)) break;
      }
    }
  },

  // ---------------------------------------------------------- client messages
  // called first thing in Room.handle while the economy is on: true = this message is handled (or refused) here
  econHandle(p, m) {
    const buying = this.econBuying();
    switch (m.t) {
      case 's': { // the weapon you say you hold must be one you have; there's no grapple to report
        if (has(WEAPONS, m.w) && !this.econOwns(p, m.w)) m.w = undefined;
        m.g = null;
        // slow walk (silent footsteps) only at slow walk speed: running with the flag on just clears it
        if (typeof m.f === 'number' && (m.f & FLAGS.WALK) && Array.isArray(m.v) && Math.hypot(Number(m.v[0]) || 0, Number(m.v[2]) || 0) > TAC.run * TAC.walkMul + 1) m.f &= ~FLAGS.WALK;
        if (p.ec && p.alive && m.q === p.seq && Array.isArray(m.p) && m.p.length === 3 && m.p.every((v) => typeof v === 'number' && Number.isFinite(v))) p.ec.said = m.p.slice(0, 3);
        const rl = p.ec && p.ec.rl;
        if (rl && has(WEAPONS, m.w)) { const x = this.econInst(p, m.w); if (!x || x.u !== rl.u) p.ec.rl = null; } // switched away: reload cancelled
        return false;
      }
      case 'fire': this.econFire(p, m, buying); return true;
      case 'hit': return !this.econHitOk(p, m, buying);
      case 'push': return m.w === 'hook' || buying || !this.econOwns(p, m.w);
      case 'item': this.econItem(p, m, buying); return true;
      case 'itemsel': case 'deploy': return true; // items come from the buy menu; no killstreaks
      case 'tbag': case 'cough': return buying;
      case 'redraw': return !this.econOwns(p, 'cards');
      case 'skin': this.econSkin(p, m); return true;
      case 'buy': this.econBuy(p, m); return true;
      case 'sell': this.econSell(p, m); return true;
      case 'drop': this.econDropCmd(p, m); return true;
      case 'pick': this.econPickCmd(p, m); return true;
      case 'rl': this.econReload(p, m); return true;
    }
    return false;
  },
  econNo(p, why, m) { if (!p.isBot) D.send(p, { t: 'eno', why, of: typeof m.t === 'string' ? m.t : '' }); return false; },
  // buy / sell / drop / pick share a token bucket: bursts of 10, 10 more per second (frames can arrive bunched up)
  econRate(p) {
    const n = now();
    p.ecB = Math.min(10, (p.ecB ?? 10) + (n - (p.ecBT || n)) * 0.01); p.ecBT = n;
    if (p.ecB < 1) return false;
    p.ecB--;
    return true;
  },
  econCanBuy(p, m) {
    const e = p.ec;
    if (!e || !this.econBuying()) return this.econNo(p, 'phase', m);
    if (!p.alive || e.out) return this.econNo(p, 'dead', m);
    if (!this.econInZone(p)) return this.econNo(p, 'zone', m);
    if (!has(KINDS, m.k) || typeof m.id !== 'string') return this.econNo(p, 'bad', m);
    return true;
  },
  // {t:'buy', k: 'w' | 'i' | 'g', id}. bots call it too (bot = true skips the rate limit)
  econBuy(p, m, bot) {
    if (!bot && !this.econRate(p)) return false;
    if (!this.econCanBuy(p, m)) return false;
    const e = p.ec, id = m.id;
    if (m.k === 'w') {
      const price0 = weaponPrice(id);
      if (price0 == null) return this.econNo(p, 'bad', m);
      const slot = WEAPONS[id].slot, cur = e.sl[slot];
      if (cur && cur.id === id) { // you have one: refill its ammo
        const a = ammoSpec(id), price = refillPrice(id);
        if (!a || (cur.m >= a.mag && cur.r >= a.res)) return this.econNo(p, 'full', m);
        if (e.$ < price) return this.econNo(p, 'money', m);
        const prev = [cur.m, cur.r];
        e.$ -= price; cur.m = a.mag; cur.r = a.res;
        e.rc.push({ k: 'w', id, paid: price, ok: () => e.sl[slot] === cur && cur.m === a.mag && cur.r === a.res, undo: () => { [cur.m, cur.r] = prev; } });
      } else {
        if (e.$ < price0) return this.econNo(p, 'money', m);
        e.$ -= price0;
        const x = this.econNewInst(id, p);
        if (cur && !cur.def) this.econDrop('w', { x: cur }, this.econFeet(p), p.id); // the one you had goes on the floor
        e.sl[slot] = x;
        e.rc.push({ k: 'w', id, paid: price0, ok: () => e.sl[slot] === x && x.fresh, undo: () => { e.sl[slot] = slot === 'melee' ? this.econNewInst(ECON.defaultMelee, p, true) : null; } });
      }
    } else if (m.k === 'i') {
      const s = itemSpec(id);
      if (!s) return this.econNo(p, 'bad', m);
      const bought = e.ib[id] || 0, have = e.it && e.it.id === id ? e.it.n : 0;
      if (have >= s.limit) return this.econNo(p, 'full', m);
      if (bought >= s.limit) return this.econNo(p, 'limit', m);
      if (e.$ < s.price) return this.econNo(p, 'money', m);
      if (e.it && e.it.id !== id && e.it.n > 0) this.econDrop('i', { iid: e.it.id, n: e.it.n }, this.econFeet(p), p.id); // one item type at a time
      e.$ -= s.price;
      const it = e.it = { id, n: have + 1 };
      e.ib[id] = bought + 1;
      e.rc.push({ k: 'i', id, paid: s.price, ok: () => e.it === it && it.n >= 1, undo: () => { it.n--; e.ib[id]--; if (it.n <= 0) e.it = null; } });
    } else {
      if (!has(GEAR, id)) return this.econNo(p, 'bad', m);
      if (GEAR[id].def && p.team === this.bomb.att) return this.econNo(p, 'side', m);
      const price = gearPrice(id, e.ar, e.hm, e.kit);
      if (price == null) return this.econNo(p, 'full', m);
      if (e.$ < price) return this.econNo(p, 'money', m);
      e.$ -= price;
      // a receipt only watches what this purchase changed: armor + helmet, or the kit
      if (id === 'kit') {
        e.kit = true;
        e.rc.push({ k: 'g', id, paid: price, ok: () => e.kit, undo: () => { e.kit = false; } });
      } else {
        const prev = [e.ar, e.hm];
        e.ar = ARMOR.max; if (id === 'helm') e.hm = true;
        const after = [e.ar, e.hm];
        e.rc.push({ k: 'g', id, paid: price, ok: () => e.ar === after[0] && e.hm === after[1], undo: () => { [e.ar, e.hm] = prev; } });
      }
    }
    this.econSync(p);
    this.econSend(p);
    return true;
  },
  // {t:'sell', k, id}: during the buy phase, undo your latest untouched purchase of that thing for a full refund
  econSell(p, m) {
    if (!this.econRate(p) || !this.econCanBuy(p, m)) return false;
    const e = p.ec;
    for (let i = e.rc.length - 1; i >= 0; i--) {
      const r = e.rc[i];
      if (r.k !== m.k || r.id !== m.id) continue;
      if (!r.ok()) return this.econNo(p, 'used', m);
      r.undo();
      e.rc.splice(i, 1);
      e.$ = clamp(e.$ + r.paid, 0, ECON.max);
      this.econSync(p);
      this.econSend(p);
      return true;
    }
    return this.econNo(p, 'nothing', m);
  },
  // {t:'drop', s: 'primary' | 'secondary' | 'melee' | 'item' | 'kit'}: put it on the floor in front of you (any time)
  econDropCmd(p, m) {
    if (!this.econRate(p)) return false;
    const e = p.ec;
    if (!e || !p.alive || e.out) return this.econNo(p, 'dead', m);
    if (!has(DROP_SLOTS, m.s)) return this.econNo(p, 'bad', m);
    const at = this.econAhead(p);
    if (!at) return this.econNo(p, 'nowhere', m);
    if (m.s === 'item') {
      if (!e.it || e.it.n <= 0) return this.econNo(p, 'empty', m);
      this.econDrop('i', { iid: e.it.id, n: e.it.n }, at, p.id);
      e.it = null;
    } else if (m.s === 'kit') {
      if (!e.kit) return this.econNo(p, 'empty', m);
      this.econDrop('k', {}, at, p.id);
      e.kit = false;
    } else {
      const x = e.sl[m.s];
      if (!x || x.def) return this.econNo(p, 'empty', m); // the default melee stays in your hand
      e.sl[m.s] = m.s === 'melee' ? this.econNewInst(ECON.defaultMelee, p, true) : null;
      if (e.rl && e.rl.u === x.u) e.rl = null;
      this.econDrop('w', { x }, at, p.id);
    }
    this.econSync(p);
    this.econSend(p);
    return true;
  },
  // {t:'pick', id}: pick up (or swap for) a drop within reach
  econPickCmd(p, m) {
    if (!this.econRate(p)) return false;
    const e = p.ec;
    if (!Number.isInteger(m.id)) return this.econNo(p, 'bad', m);
    const d = this.ec.drops.get(m.id);
    if (!d) return this.econNo(p, 'gone', m);
    if (!e || !p.alive || e.out) return this.econNo(p, 'dead', m);
    const reach = ECON.pickR + Math.min(1, Math.hypot(p.vel[0], p.vel[1], p.vel[2]) * 0.1);
    if (Math.hypot(p.pos[0] - d.p[0], p.pos[2] - d.p[2]) > reach || Math.abs(p.pos[1] - d.p[1]) > 2.5) return this.econNo(p, 'far', m);
    if (!this.econTake(p, d, true)) return this.econNo(p, 'cant', m);
    return true;
  },
  // {t:'rl', w}: you started reloading w. the rounds move from the reserve to the magazine a bit before your reload ends
  econReload(p, m) {
    const e = p.ec;
    if (!e || !p.alive || !has(WEAPONS, m.w)) return;
    const x = this.econInst(p, m.w), w = WEAPONS[m.w];
    if (!x || !x.cl || x.m >= w.mag || x.r <= 0 || (e.rl && e.rl.u === x.u)) return;
    e.rl = { u: x.u, at: now() + w.reload * 750, ms: w.reload * 1000 };
  },
  econFinishReload(p) {
    const e = p.ec, rl = e.rl;
    e.rl = null;
    const x = Object.values(e.sl).find((y) => y && y.u === rl.u);
    if (!x || !x.cl) return;
    const mv = Math.min(WEAPONS[x.id].mag - x.m, x.r);
    x.m += mv; x.r -= mv;
    this.econAm(p, x);
  },
  econAm(p, x) { if (!p.isBot) D.send(p, { t: 'am', u: x.u, w: x.id, m: x.m, r: x.r, q: p.tac ? p.tac.q : undefined }); },
  // a hitscan shot reaches the server as its 'hit' messages (one per target) and then its 'fire'. the first of them
  // pays the round; the rest of that shot rides on it. no round left = no shot (and no damage)
  econShot(p, x, w, isHit, m) {
    const n = now(), s = x.shot, open = s && !s.fired && n - s.t < 150;
    if (isHit && open) { if (s.hits >= ((w.pellets || 1) > 1 ? 6 : 1)) return false; s.hits++; return true; }
    if (!isHit && open) { s.fired = true; return true; }
    if (x.m <= 0) {
      const rl = p.ec.rl;
      if (rl && rl.u === x.u && n >= rl.at - rl.ms * 0.1) this.econFinishReload(p); // the reload message ran late (65 % done is enough)
      if (x.m <= 0) return false;
    }
    x.m--; x.fresh = false;
    x.shot = { t: n, hits: isHit ? 1 : 0, fired: !isHit };
    if (m && !p.isBot) this.tacOpen(p, x, w, m); // which spray shot this is, and is it honest (server/tactical.js)
    return true;
  },
  econFire(p, m, buying) {
    const w = has(WEAPONS, m.w) && WEAPONS[m.w];
    if (!w || !p.alive || buying) return;
    const x = this.econInst(p, m.w);
    if (!x) return; // not yours
    if (!x.lim) { this.onFire(p, m); return; } // melee, cones, the reverse card: no ammo
    if (w.kind === 'hitscan') {
      if (!this.econShot(p, x, w, false, m)) { this.econAm(p, x); return; }
      this.onFire(p, m);
      return;
    }
    // counted shots (projectiles, arrows, cards): pay only when one really left (cooldowns can refuse it)
    if (x.m <= 0) { this.econAm(p, x); return; }
    const key = w.kind === 'bow' ? 'bow' : w.kind === 'cards' ? 'cards' : m.w, before = p.lastFire[key];
    this.onFire(p, m);
    if (p.lastFire[key] !== before) { x.m--; x.fresh = false; }
  },
  econHitOk(p, m, buying) {
    if (buying) return false;
    const w = has(WEAPONS, m.w) && WEAPONS[m.w];
    if (!w) return false;
    const x = this.econInst(p, m.w);
    if (!x) return false;
    if (w.kind === 'hitscan' && x.lim) return this.econShot(p, x, w, true, m) && this.tacHitOk(p, x, w, m);
    return true;
  },
  // {t:'item', i, o, d}: the charges are the ones you bought; they don't come back
  econItem(p, m, buying) {
    const e = p.ec;
    if (!e || buying || !p.alive) return;
    if (!e.it || m.i !== e.it.id || e.it.n <= 0) { this.econSend(p); return; }
    p.item = e.it.id; p.ic = { i: e.it.id, n: e.it.n, next: 0 };
    this.useItem(p, m);
    p.ic.next = 0;
    if (p.ic.n !== e.it.n) { e.it.n = p.ic.n; if (e.it.n <= 0) e.it = null; this.econSync(p); this.econSend(p); }
  },
  econSkin(p, m) {
    if (now() - p.skinT <= 250) return;
    p.skinT = now();
    (async () => {
      await D.refreshInv(p);
      if (!p.ec) return;
      p.ecOwnSkins = D.enforceSkins(D.cleanSkins(m.s), p.inv);
      for (const x of Object.values(p.ec.sl)) if (x && x.by === p.id) { const sk = p.ecOwnSkins[x.id]; x.sk = Array.isArray(sk) ? sk.slice() : null; }
      this.econSync(p);
      this.econSend(p); // your own viewmodel shows the new look too
    })().catch((e) => D.logErr('skin', e));
  },
  // armor (from damage()): returns the damage that gets through
  econArmor(t, amt, attacker, w, hs) {
    const e = t.ec;
    if (!e || e.ar <= 0 || w === 'void' || w === 'cough' || attacker === t) return amt;
    if (w === 'sniper' && hs && attacker && !attacker.isBot) return amt; // a player's sniper headshot always kills
    const W = has(WEAPONS, w) ? WEAPONS[w] : null;
    const head = !!hs && !!W && ((W.kind === 'hitscan' && (W.pellets || 1) <= 1) || w === 'bow'); // a knife backstab is no headshot
    if (head && !e.hm) return amt;
    const frac = (head ? ARMOR.head : BLASTS.has(w) ? ARMOR.blast : ARMOR.body) * (1 - armorPen(w));
    if (frac <= 0) return amt;
    let take = amt * frac;
    if (take * ARMOR.wear >= e.ar) { take = e.ar / ARMOR.wear; e.ar = 0; e.hm = false; } else e.ar -= take * ARMOR.wear;
    if (!t.isBot) D.send(t, { t: 'ear', ar: Math.round(e.ar), hm: e.hm ? 1 : 0, a: Math.round(take) });
    return amt - take;
  },

  // ---------------------------------------------------------- bots
  // what a bot holds: its best gun that still has ammo, else its melee
  econBotWeapon(b) {
    const e = b.ec, ok = (x) => x && botGun(x.id) && (!x.lim || x.m > 0 || (x.cl && x.r > 0));
    const x = ok(e.sl.primary) ? e.sl.primary : ok(e.sl.secondary) ? e.sl.secondary : e.sl.melee;
    if (x && b.w !== x.id) { b.w = x.id; b.ai.ammo = x.cl ? Math.max(1, x.m) : 1; b.ai.reloadUntil = 0; }
  },
  // top of botFire: false = don't shoot. the bot's rounds come out of the same weapon instance
  econBotShot(b, t, Dif) {
    if (this.econBuying()) return false;
    const x = this.econInst(b, b.w), w = WEAPONS[b.w];
    if (!x || !w) { this.econBotWeapon(b); return false; }
    if (w.kind === 'melee') { this.econBotMelee(b, t, w, Dif); return false; }
    if (!x.lim) return true;
    if (x.m <= 0) {
      if (x.cl && x.r > 0) { const mv = Math.min(w.mag, x.r); x.m += mv; x.r -= mv; b.ai.ammo = x.m; } // botFire already waited out the reload
      else { this.econBotWeapon(b); return false; }
    }
    x.m--; x.fresh = false;
    return true;
  },
  econBotMelee(b, t, w, Dif) {
    const n = now();
    b.ai.nextShot = n + (w.cd * 1000) / Dif.rate;
    if (Math.hypot(t.pos[0] - b.pos[0], t.pos[1] - b.pos[1], t.pos[2] - b.pos[2]) > (w.range || 2) + 0.8) return;
    const e = [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], c = [t.pos[0] - e[0], t.pos[1] + 1 - e[1], t.pos[2] - e[2]], l = Math.hypot(...c) || 1, d = c.map((v) => v / l);
    this.broadcast({ t: 'fx', k: 'swing', w: b.w, id: b.id, a: e.map(r2) });
    this.hurt(t, b, b.w, w.dmg || 0, [d[0] * (w.kb || 0), d[1] * (w.kb || 0) + (w.kbUp || 0), d[2] * (w.kb || 0)], { slip: !!w.slip });
  },
  // eco (save), force (cheap gun + vest), full (rifle, armor, kit, a frag). pistol rounds: a vest or nothing
  econBotBuy(b) {
    if (this.econAiBuy(b)) return; // maps with sites: the team's plan (econai.js). below: the simple rules
    const e = b.ec, B = this.bomb, att = b.team === B.att;
    const buy = (k, id) => this.econBuy(b, { k, id }, true);
    const pistol = B.n === 1 || B.n === BOMB.swapAfter + 1;
    const late = B.n === BOMB.swapAfter || Math.max(B.wins[1], B.wins[2]) >= BOMB.wins - 1;
    const full = (weaponPrice('ar') || 3000) + GEAR.vest.price + GEAR.helm.price + (att ? 0 : GEAR.kit.price);
    const hasGun = !!(e.sl.primary && botGun(e.sl.primary.id));
    const mode = e.$ >= full || (hasGun && e.$ >= 1000) ? 'full' : pistol ? 'pistol' : late || e.$ >= 2400 ? 'force' : 'eco';
    e.mode = mode;
    // a random one of the guns on the list it can afford while keeping `keep` (repeats in the list weigh more)
    const gun = (list, keep) => {
      const ok = list.filter((id) => econWeapon(id) && weaponPrice(id) != null && weaponPrice(id) + keep <= e.$);
      return ok.length > 0 && buy('w', pick(ok));
    };
    if (mode === 'pistol') { if (Math.random() < 0.6) buy('g', 'vest'); }
    else if (mode === 'full') {
      if (!hasGun) gun(BOT_FULL, 1000) || gun(BOT_FULL, 650) || gun(BOT_FORCE, 650);
      if (!buy('g', 'helm')) buy('g', 'vest');
      if (!att) buy('g', 'kit');
      if (e.$ >= 500) buy('i', 'frag');
    } else if (mode === 'force') {
      if (!hasGun && !gun(BOT_FORCE, 650) && !gun(BOT_FORCE, 0) && e.$ >= 900) buy('w', 'marbles');
      buy('g', 'vest');
    }
    if (e.sl.primary && e.sl.primary.lim && e.sl.primary.m + e.sl.primary.r < 10 && refillPrice(e.sl.primary.id) <= e.$) buy('w', e.sl.primary.id);
  },
  // top of botGoal: stand still behind the barrier; otherwise walk to a better gun lying close by (when not fighting)
  econBotGoal(b) {
    const n = now(), ai = b.ai, ec = this.ec, B = this.bomb;
    if (this.econBuying(n)) {
      const gd = ai.gift && ec && ec.drops.get(ai.gift); // a teammate dropped a rifle for us: go get it (inside the spawn)
      if (gd && !(b.ec.sl.primary)) return { p: gd.p, r: 0, force: true };
      ai.gift = 0;
      return { p: b.pos, r: 0, force: true };
    }
    const tac = this.econAiGoal(b);
    // pick up a better gun lying close by, unless the bot is busy with something that can't wait
    const busy = tac && (tac.tac === 'plant' || tac.tac === 'carry' || tac.tac === 'defuse' || tac.tac === 'throw' || tac.tac === 'push' || tac.tac === 'save' || (tac.tac === 'clear' && B.ph === 'live'));
    if (!ec || !ec.drops.size || busy || B.carrier === b.id || (B.ph === 'planted' && b.team !== B.att && !tac)) { ai.ecDrop = 0; return tac; }
    if (n >= (ai.ecPickT || 0)) { ai.ecPickT = n + 700; ai.ecDrop = this.econBotWant(b, tac ? 14 : 20); }
    const d = ai.ecDrop && ec.drops.get(ai.ecDrop);
    if (!d) { ai.ecDrop = 0; return tac; }
    if (Math.hypot(d.p[0] - b.pos[0], d.p[2] - b.pos[2]) < 1.6 && Math.abs(d.p[1] - b.pos[1]) < 2) { this.econTake(b, d, true); ai.ecDrop = 0; return tac; }
    return { p: d.p, r: 0 };
  },
  econBotWant(b, range = 20) {
    const e = b.ec;
    let best = 0, bs = 0;
    const val = (x) => (x && botGun(x.id) && (!x.lim || x.m + x.r > 0) ? weaponPrice(x.id) || 0 : 0);
    for (const d of this.ec.drops.values()) {
      const dist = Math.hypot(d.p[0] - b.pos[0], d.p[2] - b.pos[2]);
      if (dist > range || Math.abs(d.p[1] - b.pos[1]) > 3) continue;
      let gain = 0;
      if (d.k === 'w' && botGun(d.x.id) && (!d.x.lim || d.x.m + d.x.r > 0)) gain = val(d.x) - val(e.sl[WEAPONS[d.x.id].slot]) - 300;
      else if (d.k === 'k' && !e.kit && b.team !== this.bomb.att) gain = 400;
      else if (d.k === 'i' && (d.iid === 'frag' || d.iid === 'smoke') && !e.it) gain = 200;
      if (gain <= 0) continue;
      const s = gain / (5 + dist);
      if (s > bs && this.clearPath(b.pos, [d.p[0], d.p[2]])) { bs = s; best = d.id; }
    }
    return best;
  },
  // bots throw the frags they bought at someone they can see, not too close
  econBotItem(b, n) {
    const e = b.ec, ai = b.ai;
    if (!e.it || e.it.id !== 'frag' || n < (ai.itemT || 0) || this.econBuying(n)) return;
    const T = this.ec && this.ec.tac, A = T && T.A;
    if (A && b.team === this.bomb.att && (A.phase === 'gather' || A.util.some((u) => !u.done && u.id === b.id))) return; // saved for the execute
    ai.itemT = n + 1500 + Math.random() * 2500;
    const t = this.players.get(ai.target);
    if (!t || !t.alive || !ai.seenAt) return;
    const dx = t.pos[0] - b.pos[0], dy = t.pos[1] - b.pos[1], dz = t.pos[2] - b.pos[2], hd = Math.hypot(dx, dz);
    if (hd < 9 || hd > 26) return;
    const v = [dx, dy + hd * 0.45 + 2, dz], l = Math.hypot(...v);
    this.econItem(b, { i: 'frag', o: [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], d: v.map((q) => q / l) }, false);
  },

  // ---------------------------------------------------------- every tick
  tickEcon(n) {
    const b = this.bomb, ec = this.ec;
    if (!b || !ec) return;
    if (b.buyUntil) {
      if (n < b.buyUntil) {
        b.idle = null; // standing in spawn with the bomb isn't being AFK
        for (const p of this.fighters()) if (p.alive && p.ec && p.ec.zone) this.econHold(p, n);
      } else {
        b.buyUntil = 0;
        for (const p of this.fighters()) if (p.ec) { p.ec.rc = []; p.ec.zone = null; }
        this.broadcast({ t: 'elive' });
      }
    }
    for (const p of this.fighters()) {
      const e = p.ec;
      if (!e) continue;
      if (e.rl && n >= e.rl.at) this.econFinishReload(p);
      if (p.isBot && e.buyAt && n >= e.buyAt) { e.buyAt = 0; if (p.alive && this.econBuying(n)) this.econBotBuy(p); }
      if (p.isBot && p.alive) this.econBotItem(p, n);
    }
    if (ec.drops.size) this.econAutoPicks(n);
    this.econAiTick(n);
    if (b.act && b.act.kind === 'defuse') {
      ec.defuser = b.act.id;
      if (b.act.kit == null) { const d = this.players.get(b.act.id); b.act.kit = !!(d && d.ec && d.ec.kit); }
    }
    if (b.ph === 'planted' && !ec.planted) {
      ec.planted = true;
      const pl = this.players.get(b.planter);
      if (pl && pl.ec) this.econPay(pl, ECON.plant, 'plant');
    }
    // a side with nobody left alive loses (with the bomb down, only the defenders running out ends it early)
    if (!b.buyUntil && !b.between && (b.ph === 'live' || b.ph === 'planted') && !(this.round && this.round.over)) {
      const c = { 1: [0, 0], 2: [0, 0] };
      for (const p of this.fighters()) if (c[p.team]) { c[p.team][0]++; if (p.alive) c[p.team][1]++; }
      if (c[1][0] && c[2][0]) {
        const att = b.att, def = 3 - att;
        if (b.ph === 'live' && !c[att][1]) this.bombRoundWin(def, 'elim');
        else if (!c[def][1]) this.bombRoundWin(att, 'elim');
      }
    }
    if (this.ec && this.ec.dirty.size && n - this.ec.moneyT > 400) this.econFlushMoney();
  },
};

// test knob JF_FFA_BOMB=n: the Online room starts a Plant & Defuse match on Bazaar once n humans are in (ws tests)
M.econTestStart = function () {
  const want = Number(process.env.JF_FFA_BOMB) || 0;
  if (this.mode !== 'ffa' || !want || this.humans().length !== want || (this.bomb && !this.round.over)) return;
  if (this.cfg.map !== 'bazaar') { this.cfg.map = 'bazaar'; this.broadcast({ t: 'cfg', cfg: this.cfg }); }
  this.setGame('bomb');
  this.startRound();
};

export function installEcon(Room, deps) {
  D = deps;
  aiDeps(deps);
  for (const [k, fn] of Object.entries({ ...M, ...AI })) {
    if (k in Room.prototype) throw new Error('econ: Room already has ' + k);
    Room.prototype[k] = fn;
  }
}
export { dropView, instView };
