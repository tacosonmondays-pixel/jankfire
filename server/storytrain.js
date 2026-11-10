// REVENUE PROTECTION (OVERDUE, m06 TICKETS, PLEASE): the referee's half of the train fight, on the story room
// (server/storyref.js installs it after server/storyboss.js). the room owns the mask's HP and layers, the phases, the
// arms, every hit, THE GAP and the fail; the client only shows them (public/js/story/trainfight.js).
//   it is a boss like overtime_1 (a story enemy with sk.b, the same spawn, hold, hit, phase and defeat events), but
//   not a walking bot: its room player sits in the middle of the mask at z = -gap and does nothing by itself.
//   def (shared/story/refsys.js builds it from content/bosses.js + revenue_protection.parts.json), cleaned here:
//     { id, hp, health, crit: { knot, eye, insp }, phases: [{ name, line, to }], geo, train: true }
//   the fight's shape (the arena, the numbers table RP, arm paths, which part a ray lands on): shared/story/train.js
//   arms belong to the room: { id, k: grab | sweep | snatch, sock, st, t, dur, tgt, hp }. only the wrist knot takes a
//   hit in full; hits on the rope do little. a grabber that grips closes THE GAP; a sever or a flinch opens it
//   events (room.onStory, on top of hit / phase / defeat): gap · arm · arms · plate · stage · flinch · shrug · bloom ·
//   swept · snatched · lunge · bag · off · fail · reset · state (everything, on spawn and after a reset)
//   the BLOOD DRIVE (WEAPONS.blooddrive) is judged here too, in story rooms only: spin-up, rate, range, HP cost
import { WEAPONS, FLAGS } from '../shared/weapons.js';
import { raycast, PH } from '../shared/physics.js';
import { RP, ARENA, PLATES, LOW, geoFrom, rayFight, armLive, sweepZ, sweepY, wallA, deckAt, offTrain, onRoof, gripSpots, backSpot } from '../shared/story/train.js';

const fin = Number.isFinite;
const isName = (s) => typeof s === 'string' && /^[a-zA-Z0-9_]{1,24}$/.test(s);
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const r2 = (x) => Math.round(x * 100) / 100;
const v3 = (a, max = 1e5) => (Array.isArray(a) && a.length === 3 && a.every((x) => fin(x) && Math.abs(x) <= max) ? a.slice() : null);
const rnd = ([a, b]) => a + Math.random() * (b - a);
const tell = (p, o) => { if (p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify(o)); };
const MAXHIT = 1000; // one hit's cap, as for every boss
const BOT_SOFT = 0.6; // the room softens every bot's hit on a person to this outside the bots mode (room.js damage): RP's numbers are what lands

const SOCKS = { 1: [0, 1], [-1]: [5, 4] }; // the rim sockets that can reach a grip spot on the +x / -x side (the spots themselves: train.js gripSpots)

// a boss def as the room keeps it. null = not a fight anyone can have
export function cleanTrain(d) {
  if (!d || typeof d !== 'object' || !isName(d.id) || !fin(d.hp) || d.hp < 1 || !Array.isArray(d.phases) || d.phases.length !== 3 || !d.train || typeof d.train !== 'object') return null;
  const hp = Math.min(1e6, d.hp), phases = [];
  let last = 100;
  for (const p of d.phases) {
    if (!p || !fin(p.to) || p.to < 0 || p.to >= last) return null; // (each phase ends lower than the one before)
    last = p.to;
    phases.push({ name: typeof p.name === 'string' ? p.name.slice(0, 40) : '', line: typeof p.line === 'string' ? p.line.slice(0, 120) : '', to: p.to });
  }
  phases[2].to = 0;
  const c = d.train.crit && typeof d.train.crit === 'object' ? d.train.crit : {}, cr = (x, def) => (fin(x) ? clamp(x, 1, 10) : def);
  return { id: d.id, hp, health: fin(d.health) && d.health > 0 && d.health < hp ? d.health : hp, phases, train: true,
    crit: { knot: cr(c.knot, 2), eye: cr(c.eye, 2), insp: cr(c.insp, 2.5) }, geo: geoFrom(d.train.parts) };
}

export function installStoryTrain(Room) {
  const P = Room.prototype;
  const ev = (room, b, type, rp) => { if (room.onStory) room.onStory({ type, t: b, rp: rp || {} }); };
  const humans = (room) => [...room.players.values()].filter((p) => !p.sk && !p.isBot);
  const view = (B) => ({ gap: B.gap - B.rear, arms: B.arms, plates: B.plates.map((p) => p.st), open: B.t < B.openUntil, eyeL: B.eyeL, smile: B.smile });
  const armMsg = (a) => ({ id: a.id, k: a.k, sock: a.sock, mouth: a.mouth ? 1 : 0, st: a.st, dur: r2(a.dur), tgt: a.tgt.map(r2), hi: a.hi ? 1 : 0, side: a.side || 0, ...(a.rear ? { rear: a.rear } : {}), ...(fin(a.wa) ? { wa: r2(a.wa) } : {}), ...(a.gp ? { gp: a.gp.map(r2) } : {}), hp: Math.max(0, Math.round(a.hp)), max: RP.arm.hp });
  const snap = (B) => ({ phase: B.phase, hp: B.hp, stage: B.stage, eyeL: B.eyeL, smile: B.smile, marrow: B.marrow, plates: B.plates.map((p) => ({ ...p })) });
  const stateMsg = (B) => ({ gap: r2(B.gap), rear: B.rear, hp: Math.round(B.hp), max: B.def.hp, phase: B.phase, name: B.def.phases[B.phase].name, stage: B.stage, plates: B.plates.map((p) => p.st), open: Math.max(0, r2(B.openUntil - B.t)), marrow: B.marrow, arms: B.arms.map(armMsg), jack: B.phase === 0 ? r2(1 - B.jack / RP.jack) : 0 });
  const place = (b, B) => { b.pos = [0, ARENA.cy, B.rear - B.gap]; b.vel = [0, 0, 0]; b.yaw = Math.PI; b.onGround = true; b.f = 0; };
  const sendGap = (room, b, B, rate) => { B.sentT = B.t; B.sentGap = B.gap; B.sentRate = rate; ev(room, b, 'gap', { gap: r2(B.gap), rate, jack: B.phase === 0 ? r2(1 - B.jack / RP.jack) : 0 }); };
  const setHp = (b, B) => { b.hp = Math.max(1, 100 * B.hp / B.def.hp); }; // (it never dies in the room: the story ends the fight)
  const hurt = (room, p, dmg, b, w) => room.damage(p, dmg / BOT_SOFT, b, w);
  const clearArms = (room, b, B) => { if (B.arms.length) { B.arms.length = 0; ev(room, b, 'arms', { clear: true }); } B.lunge = null; };

  const init0 = P.bossInit, ray0 = P.bossRay, dmg0 = P.bossDamage, step0 = P.bossStep, fire0 = P.onFire;
  // the fight's state on a story enemy (storySpawn calls bossInit). a def with `train` is this fight
  P.bossInit = function (b, d) {
    if (!d || !d.train) return init0.call(this, b, d);
    const def = cleanTrain(d); if (!def) return false;
    b.sk.max = def.hp; b.sk.boss = true;
    if (Object.hasOwn(this, 'boxes')) delete this.boxes; // (a fight before this one bit the wagon off: it is back)
    b.sk.b = { train: true, def, id: def.id, rear: 0, hp: def.hp, phase: 0, state: 'fight', t: 0, cutT: 0, failT: 0, first: true, calm: false,
      gap: RP.gap.start, sentT: -9, sentGap: -1, sentRate: 0, arms: [], nextId: 1, nextArm: RP.arm.first, severs: [], openUntil: 0,
      plates: Array.from({ length: PLATES }, () => ({ hp: RP.mask.plateHp, st: 0 })), stage: 0, eyeL: false, smile: false, marrow: false,
      jack: 0, bagT: RP.bag.every, lungeT: 0, lunge: null, shrugT: -9, cp: null, ray: null };
    b.ai.nextShot = Infinity; place(b, b.sk.b);
    return true;
  };
  // which part a shot lands on (storyboss's onHit asks: a 'hit' from any other gun is judged by the same ray)
  P.bossRay = function (b, o, d) { const B = b.sk.b; return B.train ? (B.state === 'fight' ? rayFight(B.def.geo, view(B), o, d) : null) : ray0.call(this, b, o, d); };

  // ---------------------------------------------------------------- hits
  function heal(room, p, n) { const a = p && p.alive ? Math.max(0, Math.min(n, 100 - p.hp)) : 0; if (a > 0) room.heal(p, a); return Math.round(a); } // (the room tells the client)
  function flinch(room, b, B) { // four arms inside ten seconds: the eye housings swing open, and it gives ground
    B.severs.length = 0; B.openUntil = B.t + RP.flinch.open; B.gap = Math.min(RP.gap.max, B.gap + RP.gap.flinch); B.nextArm = Math.max(B.nextArm, B.t + 2);
    ev(room, b, 'flinch', { open: RP.flinch.open, gap: r2(B.gap) });
  }
  function sever(room, b, B, a, by) {
    a.st = 'cut'; a.t = 0; a.dur = RP.arm.cut; a.hp = 0;
    B.gap = Math.min(RP.gap.max, B.gap + RP.gap.sever);
    ev(room, b, 'arm', { ...armMsg(a), blood: heal(room, by, RP.arm.blood) }); // (a severed arm gives blood back)
    B.severs = B.severs.filter((t) => B.t - t < RP.flinch.within); B.severs.push(B.t);
    if (B.severs.length >= RP.flinch.n) flinch(room, b, B);
  }
  function hitArm(room, b, B, h, amt, by, w) {
    const a = B.arms.find((x) => x.id === h.arm); if (!a || !armLive(a)) return false;
    const crit = h.part === 'knot', dealt = Math.min(a.hp, amt * (crit ? B.def.crit.knot : RP.arm.rope));
    a.hp -= dealt;
    room.broadcast({ t: 'dmg', to: b.id, from: by ? by.id : 0, a: Math.round(Math.min(dealt, 999)), w, hs: crit });
    if (room.onStory) room.onStory({ type: 'hit', t: b, by, w, dmg: dealt, head: false, part: h.part, crit, hp: Math.round(B.hp), max: B.def.hp, arm: a.id });
    if (a.hp <= 0.01) sever(room, b, B, a, by);
    return true;
  }
  function plateHit(room, b, B, i, dealt) {
    const p = B.plates[i]; if (!p || p.st === 2) return;
    p.hp -= dealt;
    const st = p.hp <= 0 ? 2 : p.hp <= RP.mask.plateHp * RP.mask.craze ? 1 : 0;
    if (st !== p.st) { p.st = st; ev(room, b, 'plate', { i, st }); }
  }
  // the break stages, in order, at their HP lines (phase 2 on): hairline, the left eye, the smile
  function stages(room, b, B) {
    while (B.phase >= 1 && B.stage < RP.stages.length && 100 * B.hp / B.def.hp <= RP.stages[B.stage][1] + 1e-9) {
      const name = RP.stages[B.stage++][0];
      if (name === 'left_eye') B.eyeL = true;
      if (name === 'smile') { B.smile = true; for (const i of LOW) if (B.plates[i].st !== 2) { B.plates[i].st = 2; B.plates[i].hp = 0; ev(room, b, 'plate', { i, st: 2 }); } }
      ev(room, b, 'stage', { stage: B.stage, name });
    }
  }
  function phase(room, b, B, i) {
    if (i <= B.phase || i >= B.def.phases.length) return;
    B.phase = i; B.state = 'cut'; B.cutT = B.t; clearArms(room, b, B); B.openUntil = 0; B.severs.length = 0;
    if (i === 1) { // the scripted end of phase 1: Jack's armour breaks. it holds at 6 m, and after it you have his marrow
      B.hp = Math.min(B.hp, B.def.hp * B.def.phases[0].to / 100); setHp(b, B);
      B.gap = RP.gap.moment; B.marrow = true;
    }
    sendGap(room, b, B, 0);
    const ph = B.def.phases[i];
    if (room.onStory) room.onStory({ type: 'phase', t: b, phase: i, name: ph.name, line: ph.line, invuln: true });
  }
  function defeat(room, b, B, by, w) {
    if (B.state === 'done') return;
    B.state = 'done'; clearArms(room, b, B); b.sk.hold = true;
    if (room.onStory) room.onStory({ type: 'defeat', t: b, by, w });
  }
  function hitMask(room, b, B, h, amt, by, w) {
    const D = B.def, ph = B.phase, part = h.part; let mul = 0, crit = false;
    if (part === 'eye' && ph < 2) { mul = D.crit.eye; crit = true; } // into an open (or blown) housing
    else if (ph === 1) mul = part === 'plate' ? 1 : RP.mask.soft; // the plates break; holes, lamps and blasts are soft
    else if (ph === 2) { if (part === 'insp') { mul = D.crit.insp; crit = true; } else mul = part === 'inspbody' ? 1 : RP.mask.far; }
    if (!mul) { // phase 1: the mask shrugs bolts off
      if (B.t - B.shrugT > 0.2 && h.at) { B.shrugT = B.t; ev(room, b, 'shrug', { at: h.at.map(r2) }); }
      return false;
    }
    const floor = D.hp * D.phases[ph].to / 100, hp0 = B.hp; // (a phase never skips: this hit stops at its end)
    B.hp = Math.max(floor, B.hp - amt * mul);
    const dealt = hp0 - B.hp; if (dealt <= 0) return false;
    if (part === 'plate' && fin(h.i)) plateHit(room, b, B, h.i, dealt);
    setHp(b, B); b.lastHs = false; room.tag(b, by, w);
    room.broadcast({ t: 'dmg', to: b.id, from: by ? by.id : 0, a: Math.round(Math.min(dealt, 999)), w, hs: crit });
    if (room.onStory) room.onStory({ type: 'hit', t: b, by, w, dmg: dealt, head: false, part, crit, hp: Math.round(B.hp), max: D.hp });
    stages(room, b, B);
    if (B.hp <= floor + 1e-9) { if (ph >= D.phases.length - 1) defeat(room, b, B, by, w); else phase(room, b, B, ph + 1); }
    return true;
  }
  // damage to it (storyref's damage hands it over). amt is in real HP; with no ray (a blast, a scripted hurt) it lands on the face
  P.bossDamage = function (t, amt, attacker, w, hs, from) {
    const B = t.sk.b; if (!B.train) return dmg0.call(this, t, amt, attacker, w, hs, from);
    if (!fin(amt) || amt <= 0 || !t.alive) return false;
    if (B.state !== 'fight' || t.sk.hold) return false; // a cutscene, between phases, caught, or done
    if (this.hitBlocked(t, attacker, w, from)) return false;
    const h = B.ray || { part: 'blast' }; amt = Math.min(amt, MAXHIT);
    return h.arm ? hitArm(this, t, B, h, amt, attacker, w) : hitMask(this, t, B, h, amt, attacker, w);
  };

  // ---------------------------------------------------------------- arms
  function addArm(room, b, B, a) {
    const arm = { id: B.nextId++, mouth: false, st: 'reach', t: 0, hp: RP.arm.hp, ...a };
    B.arms.push(arm); ev(room, b, 'arm', armMsg(arm));
    return arm;
  }
  const used = (B, mouth) => new Set(B.arms.filter((a) => !!a.mouth === mouth).map((a) => a.sock));
  const snatchAt = (p) => [p.pos[0], p.pos[1] + RP.snatch.up, p.pos[2] - 0.2];
  // one more arm of kind k, if there is a socket (and a rail spot) for it. true = it came
  function spawnArm(room, b, B, k, o = {}) {
    const me = humans(room).find((p) => p.alive);
    if (k === 'grab') {
      const rim = used(B, false), mo = used(B, true), taken = new Set(B.arms.filter((a) => a.k === 'grab').map((a) => a.spot)), all = gripSpots(B.rear);
      for (const i of all.map((_, n) => n).filter((n) => !taken.has(n)).sort(() => Math.random() - 0.5)) {
        const sp = all[i], gp = sp.p, tgt = [gp[0] + sp.o[0] * 0.95, gp[1] + 0.75, gp[2] + sp.o[1] * 0.95];
        const free = SOCKS[sp.side].filter((n) => !rim.has(n)), mfree = B.smile ? [0, 1, 2, 3].filter((n) => !mo.has(n) && (n < 2) === (sp.side < 0)) : [];
        if (mfree.length && (!free.length || Math.random() < 0.5)) { addArm(room, b, B, { k, sock: mfree[0], mouth: true, spot: i, tgt, gp, dur: RP.grab.reach * 0.7 }); return true; } // out of the mouth: faster
        if (free.length) { addArm(room, b, B, { k, sock: free[0], spot: i, tgt, gp, dur: RP.grab.reach }); return true; }
      }
      return false;
    }
    if (k === 'sweep') {
      if (B.arms.some((a) => a.k === 'sweep')) return false; // one at a time: it has to be readable
      const side = o.side === 1 || o.side === -1 ? o.side : Math.random() < 0.5 ? 1 : -1, hi = typeof o.hi === 'boolean' ? o.hi : Math.random() < 0.5, a = { hi, rear: B.rear, st: 'tell' }, y = sweepY(a), z = sweepZ(a);
      addArm(room, b, B, { k, sock: side > 0 ? 11 : 6, side, hi, rear: B.rear, wa: wallA(side, y), tgt: [-side * RP.sweep.x, y, z], st: 'tell', dur: RP.sweep.tell, z, hit: new Set() });
      return true;
    }
    if (k === 'snatch') {
      if (!me) return false;
      const free = [2, 3].filter((n) => !used(B, false).has(n)), n = B.phase >= 1 ? 2 : 1; // (they come in pairs from phase 2)
      if (!free.length || B.arms.filter((a) => a.k === 'snatch').length >= n) return false;
      for (const sock of free.slice(0, n)) addArm(room, b, B, { k, sock, who: me.id, tgt: snatchAt(me), dur: RP.snatch.reach });
      return true;
    }
    return false;
  }
  function stepArms(room, b, B, dt) {
    for (let i = B.arms.length - 1; i >= 0; i--) {
      const a = B.arms[i], done = (a.t += dt) >= a.dur, go = (st, dur) => { a.st = st; a.t = 0; a.dur = dur; ev(room, b, 'arm', armMsg(a)); };
      if (a.st === 'cut' || a.st === 'back') { if (done) { B.arms.splice(i, 1); ev(room, b, 'arm', { id: a.id, k: a.k, st: 'gone' }); } continue; }
      if (a.k === 'grab') { if (a.st === 'reach' && done) go('grip', 0); } // it has the rail: THE GAP closes while it holds
      else if (a.k === 'sweep') {
        if (a.st === 'tell' && done) go('sweep', (RP.sweep.z1 - a.z) / RP.sweep.speed);
        else if (a.st === 'sweep') {
          const z0 = a.z, z = sweepZ(a); a.z = z; a.tgt[2] = z; a.tgt[1] = sweepY(a, z);
          for (const p of humans(room)) { // the bar passes you once: over it (knee height) or under it (head height), or it takes you along
            if (!p.alive || a.hit.has(p.id) || p.pos[2] < z0 - RP.sweep.half || p.pos[2] > z + RP.sweep.half || Math.abs(p.pos[0]) > 3.8) continue;
            a.hit.add(p.id);
            const up = p.pos[1] - deckAt(p.pos[2]), dodged = a.hi ? !!(p.f & (FLAGS.SLIDE | FLAGS.CROUCH)) || up >= RP.sweep.over : up >= RP.sweep.low; // (on the van's roof both pass under you)
            if (dodged) continue;
            hurt(room, p, RP.sweep.dmg, b, 'sweeper'); room.knock(p, [-a.side * RP.sweep.kb[0], RP.sweep.kb[1], RP.sweep.kb[2]], 'sweeper');
            ev(room, b, 'swept', { arm: a.id, hi: a.hi ? 1 : 0 });
          }
          if (done) go('back', RP.arm.back);
        }
      } else if (a.k === 'snatch') {
        const p = room.players.get(a.who);
        if (!p || !p.alive) { go('back', RP.arm.back); continue; }
        a.tgt = snatchAt(p);
        if (a.st === 'reach' && done) go('hold', RP.snatch.hold); // it has you: six seconds to shoot it off
        else if (a.st === 'hold' && done) {
          hurt(room, p, RP.snatch.dmg, b, 'snatcher'); B.gap = Math.max(0, B.gap - RP.snatch.gap);
          ev(room, b, 'snatched', { arm: a.id, gap: r2(B.gap) }); go('back', RP.arm.back);
        }
      }
    }
  }
  function nextArm(room, b, B) {
    if (B.calm || B.t < B.nextArm) return;
    B.nextArm = B.t + rnd(RP.arm.every[B.phase]);
    if (B.arms.filter(armLive).length >= RP.arm.max[B.phase]) return;
    const mix = RP.arm.mix[B.phase], ks = Object.keys(mix).sort(() => Math.random() - 0.5); let r = Math.random() * ks.reduce((n, k) => n + mix[k], 0);
    const first = humans(room).some((p) => p.alive && onRoof(p.pos)) && Math.random() < RP.snatch.roof ? 'snatch' : ks.find((k) => (r -= mix[k]) < 0) || 'grab'; // (they favour whoever is up on the van)
    for (const k of [first, ...ks]) if (spawnArm(room, b, B, k)) return;
  }
  // phase 3: it stops hauling politely. it rears, then takes ground; close enough, it bites the wagon (be on the flatbed)
  function stepLunge(room, b, B, dt) {
    if (B.phase < 2) return;
    if (!B.lunge) { if (!B.calm && B.t >= B.lungeT) { B.lunge = { t: 0 }; ev(room, b, 'lunge', { st: 'tell', dur: RP.lunge.tell }); } return; }
    if ((B.lunge.t += dt) < RP.lunge.tell) return;
    B.lunge = null; B.lungeT = B.t + rnd(RP.lunge.every);
    B.gap = Math.max(Math.min(B.gap, RP.lunge.min), B.gap - RP.lunge.gap);
    let bit = 0; const cut = !B.rear;
    const bite = (p) => { bit++; hurt(room, p, RP.lunge.dmg, b, 'lunge'); room.knock(p, [0, 6, 9], 'lunge'); };
    if (cut) { // the first lunge bites the rear wagon off: the fight is the flatbed and the van now, and THE GAP is measured from the flatbed's back
      clearArms(room, b, B); B.rear = ARENA.cut;
      Object.defineProperty(room, 'boxes', { value: room.map.boxes.filter((x) => x.car !== 'wagon'), configurable: true, writable: true }); // (this room's own list: the map's is everyone's)
      for (const p of humans(room)) if (p.alive && p.pos[2] < ARENA.cut - 0.2) { bite(p); if (p.alive) { const to = backSpot(B.rear); p.pos = to.slice(); p.vel = [0, 0, 0]; p.rpOffT = B.t + RP.off.grace; tell(p, { t: 'tp', p: to }); } } // whoever was still on it is thrown onto the flatbed, less some of themselves
    } else if (B.gap <= RP.lunge.bite) for (const p of humans(room)) if (p.alive && p.pos[2] < B.rear + RP.lunge.reach) bite(p);
    ev(room, b, 'lunge', { st: 'hit', gap: r2(B.gap), bit, ...(cut ? { cut: 1, rear: B.rear } : {}) });
  }
  // caught: the fight stops, and starts again from the last phase's beginning once you are back
  function fail(room, b, B, why) {
    if (B.state !== 'fight') return;
    B.state = 'failed'; B.failT = B.t; clearArms(room, b, B);
    ev(room, b, 'fail', { why, line: 'fare evaded. briefly.' });
    if (why === 'gap') for (const p of humans(room)) if (p.alive) room.kill(p, b, 'caught');
  }
  function reset(room, b, B) {
    const c = B.cp;
    if (Object.hasOwn(room, 'boxes')) delete room.boxes; // the wagon is back on
    Object.assign(B, { rear: 0, phase: c.phase, hp: c.hp, stage: c.stage, eyeL: c.eyeL, smile: c.smile, marrow: c.marrow, plates: c.plates.map((p) => ({ ...p })), state: 'fight', gap: c.phase === 0 ? RP.gap.start : RP.gap.retry,
      severs: [], openUntil: 0, nextArm: B.t + RP.arm.first, lungeT: B.t + rnd(RP.lunge.every), jack: 0, bagT: B.t + RP.bag.every });
    setHp(b, B); place(b, B);
    ev(room, b, 'reset', {}); ev(room, b, 'state', stateMsg(B));
  }

  // ---------------------------------------------------------------- its turn, every room tick
  P.bossStep = function (b, dt) {
    const B = b.sk.b; if (!B.train) return step0.call(this, b, dt);
    place(b, B);
    if (B.state === 'done' || b.sk.hold) return; // (held: a cutscene or a talk. nothing moves, THE GAP holds)
    B.t += dt;
    if (B.first) { B.first = false; B.cp = snap(B); ev(this, b, 'state', stateMsg(B)); }
    const hs = humans(this), up = hs.filter((p) => p.alive);
    if (B.state === 'cut') { // the client's scene holds it (sk.hold); after it, a beat, then the next phase is on
      if (B.t - B.cutT < RP.cut) return;
      B.state = 'fight'; B.nextArm = B.t + RP.arm.first; B.lungeT = B.t + rnd(RP.lunge.every); B.bagT = B.t + RP.bag.every;
      this.onStory && this.onStory({ type: 'phase', t: b, phase: B.phase, name: B.def.phases[B.phase].name, line: '', invuln: false });
      stages(this, b, B); B.cp = snap(B);
      return;
    }
    if (B.state === 'failed') { if (B.t - B.failT >= RP.fail && up.length) reset(this, b, B); return; }
    if (hs.length && !up.length) return fail(this, b, B, 'dead');
    // off the train: the track takes some of you, and you are put back
    for (const p of up) {
      if (!offTrain(p.pos, B.rear) || B.t < (p.rpOffT || 0)) continue;
      p.rpOffT = B.t + RP.off.grace;
      hurt(this, p, RP.off.dmg, b, 'track');
      if (p.alive) { const to = backSpot(B.rear); p.pos = to.slice(); p.vel = [0, 0, 0]; tell(p, { t: 'tp', p: to }); }
      ev(this, b, 'off', {});
    }
    stepArms(this, b, B, dt); stepLunge(this, b, B, dt); nextArm(this, b, B);
    const rate = B.pin ? 0 : -RP.gap.grab * B.arms.filter((a) => a.st === 'grip').length; // (pin: a dev hold on THE GAP, for screenshots)
    B.gap = clamp(B.gap + rate * dt, 0, RP.gap.max);
    if (B.phase === 0 && !B.calm && (B.jack += dt) >= RP.jack) phase(this, b, B, 1); // Jack's bar ran out before the mask's did
    if (B.t >= B.bagT) { B.bagT = B.t + RP.bag.every; for (const p of up) { const a = heal(this, p, RP.bag.hp); if (a) ev(this, b, 'bag', { hp: a }); } }
    if (B.state === 'fight' && (rate !== B.sentRate || (B.t - B.sentT >= RP.gap.send && Math.abs(B.gap - B.sentGap) > 0.01))) sendGap(this, b, B, rate);
    if (B.state === 'fight' && B.gap <= 0) fail(this, b, B, 'gap');
  };
  // tests and screenshots (?storydev=1; refsys checks sim.dev): stage the fight a moment at a time
  P.rpDev = function (b, m) {
    const B = b.sk.b, me = humans(this).find((p) => p.alive) || null; if (!B.train || !m || typeof m !== 'object') return;
    if (typeof m.calm === 'boolean') B.calm = m.calm;
    if (typeof m.pin === 'boolean') B.pin = m.pin;
    if (fin(m.gap)) { B.gap = clamp(m.gap, 0.2, RP.gap.max); sendGap(this, b, B, 0); }
    if (B.state !== 'fight') return;
    if (m.want === 'grab' || m.want === 'sweep' || m.want === 'snatch') spawnArm(this, b, B, m.want, { hi: m.hi, side: m.side });
    if (m.want === 'lunge' && B.phase === 2) B.lungeT = B.t;
    if (m.grip === true) for (const a of B.arms) if (a.st === 'reach' || a.st === 'tell') a.t = a.dur; // (skip the tells)
    if (m.sever === true) for (const a of B.arms.filter(armLive)) { B.ray = { part: 'knot', arm: a.id }; try { this.damage(b, MAXHIT, me, 'blooddrive'); } finally { B.ray = null; } }
    if (fin(m.dmg) && m.dmg > 0 && (m.part === undefined || isName(m.part))) { const part = m.part || (B.phase === 0 ? 'eye' : B.phase === 1 ? 'plate' : 'inspbody'); B.ray = { part, i: clamp(m.i | 0, 0, PLATES - 1) }; try { this.damage(b, Math.min(m.dmg, MAXHIT), me, 'blooddrive'); } finally { B.ray = null; } }
  };

  // ---------------------------------------------------------------- the BLOOD DRIVE (story rooms only)
  const trainBoss = (room) => { for (const p of room.players.values()) if (p.sk && p.sk.b && p.sk.b.train) return p; return null; };
  // Jack's marrow: free while it spins. the story's flag (refsys sets room.storyFree), or this fight past its middle
  P.driveFree = function (p) { const b = trainBoss(this); return !!((this.storyFree && this.storyFree(p)) || (b && b.sk.b.marrow)); };
  P.onFire = function (p, m) {
    if (this.mode === 'story' && m && m.w === 'blooddrive') return this.driveFire(p, m);
    return fire0.call(this, p, m);
  };
  P.driveFire = function (p, m) {
    const w = WEAPONS.blooddrive, n = Date.now();
    if (!p || p.sk || !p.alive) return;
    const D = (p.bd ||= { on: 0, last: 0, tok: 0, tokT: n, key: '', n: 0, dryT: 0 });
    if (n - D.last > 1500) D.on = 0; // let go (nothing for a while; a held trigger keeps saying 'spin'): it winds down
    if (m.k === 'stop') { D.on = 0; return; }
    if (m.k === 'spin' || !D.on) { if (!D.on) { D.on = n; D.tok = 0; D.tokT = n; } D.last = n; return; } // the trigger goes down: the ring winds up. no bolt yet
    const d = v3(m.d, 2), l = d ? Math.hypot(d[0], d[1], d[2]) : 0; if (!d || l < 0.5) return;
    D.last = n;
    if (n - D.on < w.spin * 750) return; // still winding up (0.75: the slack every cooldown here gets)
    D.tok = Math.min(3, D.tok + (n - D.tokT) * w.rate * 1.1 / 1000); D.tokT = n; // 14 a second: bunched frames pass, a flood doesn't
    if (D.tok < 1) return;
    D.tok -= 1;
    if (!this.driveFree(p)) { // paid in your own blood. it never takes your last HP: it runs dry instead
      if (p.hp - w.cost < 1) { if (n - D.dryT > 500) { D.dryT = n; tell(p, { t: 'bdrive', k: 'dry' }); } return; }
      p.hp -= w.cost; p.selfHurtT = n;
    }
    const eye = [p.pos[0], p.pos[1] + PH.eye, p.pos[2]], o0 = v3(m.o), o = o0 && Math.hypot(o0[0] - eye[0], o0[1] - eye[1], o0[2] - eye[2]) <= 4 ? o0 : eye, dn = d.map((x) => x / l);
    const wall = raycast(o, dn, w.range, this.boxes), reach = wall ? wall.t : w.range, b = trainBoss(this), B = b && b.sk.b;
    let h = B && b.alive && B.state === 'fight' && !b.sk.hold ? rayFight(B.def.geo, view(B), o, dn, reach) : null, body = null, bt = h ? h.t : reach;
    for (const t of this.players.values()) { // anyone else with a body (story enemies): a box round them
      if (t === p || !t.alive || !t.sk || t.sk.b || this.friendly(p, t)) continue;
      let t0 = 0, t1 = bt; const c = [t.pos[0], t.pos[1] + 0.95, t.pos[2]], hh = [0.5, 1.0, 0.5];
      for (let a = 0; a < 3 && t0 <= t1; a++) { if (Math.abs(dn[a]) < 1e-9) { if (Math.abs(o[a] - c[a]) > hh[a]) t0 = 1e9; continue; } let x0 = (c[a] - hh[a] - o[a]) / dn[a], x1 = (c[a] + hh[a] - o[a]) / dn[a]; if (x0 > x1) [x0, x1] = [x1, x0]; t0 = Math.max(t0, x0); t1 = Math.min(t1, x1); }
      if (t0 <= t1) { body = t; bt = t0; h = null; }
    }
    if (!h && !body) return;
    const key = body ? 'p' + body.id : h.arm ? 'a' + h.arm : 'mask';
    D.n = D.key === key ? D.n + 1 : 1; D.key = key;
    const bloom = D.n >= w.bloomEvery; if (bloom) D.n = 0; // every sixth bolt in the same target blooms a cross
    if (body) {
      this.damage(body, w.dmg, p, 'blooddrive');
      if (bloom && body.alive && this.stickCross) this.stickCross({ id: this.nextProj++, o: p.id, p: [o[0] + dn[0] * bt, o[1] + dn[1] * bt, o[2] + dn[2] * bt], v: dn.map((x) => x * 75), cost: 0, thin: 0 }, body); // the Blood Cross's own burst and pop
      if (!body.alive) heal(this, p, w.heal);
      return;
    }
    B.ray = h;
    try { this.damage(b, w.dmg + (bloom ? w.bloomDmg : 0), p, 'blooddrive'); } finally { B.ray = null; }
    if (bloom) ev(this, b, 'bloom', { at: h.at.map(r2), part: h.part });
  };
}
