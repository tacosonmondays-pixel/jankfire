// Zombies: co-op wave survival for the Online and Bots rooms. Endless rounds of zombie bots climb in through the
// windows of whichever areas are open and walk the map's nav grid to the nearest player. Hits and kills earn credits,
// spent with F on shutters, wall guns, the mystery crate and the cola machine. A downed player can be revived by a
// friend; when everyone's down it's game over and the vote picks what's next. Installed onto Room (server.js) so the
// match code only needs a few hooks.
import { MAPS } from '../shared/map.js';
import { WEAPONS, FLAGS, fireRate } from '../shared/weapons.js';
import { GAMES, VOTE_MS } from '../shared/modes.js';
import { raycast, movePlayer, query } from '../shared/physics.js';
import { randomContainer } from '../shared/cosmetics.js';
import { ZM, zmCount, zmHp, zmMaxAlive, zmGap, zmGait, zmAmmo, zmAmmoPrice, zmPick, zmTarget, zmAreaAt, zmOpenAreas } from '../shared/zombies.js';

let send = () => {}, stat = () => {}, store = null;
const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const pick = (a) => a[(Math.random() * a.length) | 0];
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
function turn(a, b, t) { let d = b - a; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2; return a + d * Math.min(1, t); }
const USE_GAP = 1000; // ms between 'use' messages that still count as holding F (slow clients send them late)
const eyeOf = (p) => [p.pos[0], p.pos[1] + (p.f & FLAGS.CROUCH ? 1.05 : 1.6), p.pos[2]];
const lookOf = (p) => { const cp = Math.cos(p.pitch || 0); return [-Math.sin(p.yaw || 0) * cp, Math.sin(p.pitch || 0), -Math.cos(p.yaw || 0) * cp]; };
// bot difficulty scales the zombies (Bots room setting)
const DIFF = { easy: { hp: 0.85, speed: 0.9, dmg: 0.75 }, normal: { hp: 1, speed: 1, dmg: 1 }, hard: { hp: 1.2, speed: 1.12, dmg: 1.3 } };
// rotten mannequins: green skin, clothes gone grey and brown. outline: green shamblers, orange runners, red sprinters
const SKIN = ['#6f9a3a', '#7f9f4a', '#5e8a3a', '#8aa860', '#6a8a50', '#9aae6a', '#8a9a6a'];
const RAGS = ['#4a5a3a', '#5a4a3a', '#3a3a44', '#6a6050', '#2a3a2a', '#5a3a3a', '#44403a', '#3a4a5a'];
const GLOW = ['#8fd14f', '#ffb347', '#ff5a3a'];
function zombieLook() {
  return {
    color: '', head: 'none', face: 'none', back: 'none', skin: pick(SKIN), hair: pick(['none', 'none', 'short', 'long', 'spiky', 'bowl', 'mohawk']),
    hairColor: pick(['#1a1a1a', '#4a2a10', '#3a3a30', '#6a6a60', '#8a8a80']), top: pick(['tee', 'tee', 'jacket', 'hoodie', 'tank', 'suit', 'none']),
    topColor: pick(RAGS), bottom: pick(['pants', 'pants', 'shorts', 'skirt']), bottomColor: pick(RAGS),
  };
}

// ---------------------------------------------------------------- the nav grid: 1 m cells over the map. a cell is walkable
// if a zombie fits standing on it; cells only blocked by a shutter are gated by that door (open = walkable). links go to
// the 8 neighbours, at most a step up or down, no cutting corners. one flow field per player says how far each cell is
// from them on foot, so every zombie just walks downhill toward whoever is closest.
const NAV = new Map();
function navFor(id) {
  if (!NAV.has(id)) NAV.set(id, buildNav(MAPS[id]));
  return NAV.get(id);
}
export function buildNav(map) {
  const [x0, z0, x1, z1] = map.zm.bounds, W = Math.ceil(x1 - x0), D = Math.ceil(z1 - z0), top = map.zm.H - 0.3;
  const floor = new Float32Array(W * D).fill(NaN), door = new Int16Array(W * D).fill(-1), q = [];
  const fits = (b, x, y, z, r = 0.35) => x - r < b.max[0] && x + r > b.min[0] && y + 0.3 < b.max[1] && y + 1.75 > b.min[1] && z - r < b.max[2] && z + r > b.min[2];
  for (let j = 0; j < D; j++) for (let i = 0; i < W; i++) {
    const x = x0 + i + 0.5, z = z0 + j + 0.5;
    const h = raycast([x, top, z], [0, -1, 0], top + 2, map.boxes);
    if (!h || h.normal[1] !== 1) continue; // no floor, or we started inside a wall
    const y = h.point[1];
    if (query(map.boxes, x - 0.4, z - 0.4, x + 0.4, z + 0.4, q).some((b) => fits(b, x, y, z))) continue;
    floor[j * W + i] = y;
    door[j * W + i] = map.zm.doors.findIndex((d) => fits(d.box, x, y, z, 0.5)); // the whole cell: shutters are thinner than one
  }
  return { x0, z0, W, D, floor, door };
}
const D8 = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414]];
const walkable = (nav, open, c) => nav.floor[c] === nav.floor[c] && (nav.door[c] < 0 || !!open[nav.door[c]]);
function link(nav, open, c, di, dj) { // the neighbour cell a zombie can step to from c, or -1
  const i = (c % nav.W) + di, j = ((c / nav.W) | 0) + dj;
  if (i < 0 || j < 0 || i >= nav.W || j >= nav.D) return -1;
  const n = j * nav.W + i;
  if (!walkable(nav, open, n) || Math.abs(nav.floor[n] - nav.floor[c]) > 0.55) return -1;
  if (di && dj && (!walkable(nav, open, c + di) || !walkable(nav, open, c + dj * nav.W))) return -1;
  return n;
}
function cellOf(nav, p) {
  const i = Math.floor(p[0] - nav.x0), j = Math.floor(p[2] - nav.z0);
  return i >= 0 && j >= 0 && i < nav.W && j < nav.D ? j * nav.W + i : -1;
}
const center = (nav, c) => [nav.x0 + (c % nav.W) + 0.5, nav.z0 + ((c / nav.W) | 0) + 0.5];
// Dijkstra out from the player (seeded on the cells round them they can see: they might be up on a table)
function flow(nav, open, at, boxes, out) {
  out.fill(Infinity);
  const hc = [], hd = [];
  const push = (c, d) => { let i = hc.length; hc.push(c); hd.push(d); while (i > 0) { const p = (i - 1) >> 1; if (hd[p] <= d) break; hc[i] = hc[p]; hd[i] = hd[p]; i = p; } hc[i] = c; hd[i] = d; };
  const pop = () => {
    const c = hc[0], d = hd[0], lc = hc.pop(), ld = hd.pop();
    if (hc.length) { let i = 0; for (;;) { let k = 2 * i + 1; if (k >= hc.length) break; if (k + 1 < hc.length && hd[k + 1] < hd[k]) k++; if (hd[k] >= ld) break; hc[i] = hc[k]; hd[i] = hd[k]; i = k; } hc[i] = lc; hd[i] = ld; }
    return [c, d];
  };
  const ci = Math.floor(at[0] - nav.x0), cj = Math.floor(at[2] - nav.z0);
  for (let dj = -2; dj <= 2; dj++) for (let di = -2; di <= 2; di++) {
    const i = ci + di, j = cj + dj;
    if (i < 0 || j < 0 || i >= nav.W || j >= nav.D) continue;
    const c = j * nav.W + i;
    if (!walkable(nav, open, c)) continue;
    const [x, z] = center(nav, c), dx = x - at[0], dz = z - at[2], d = Math.hypot(dx, dz);
    if (d > 2.2) continue;
    if (d > 0.3 && raycast([at[0], at[1] + 0.5, at[2]], [dx / d, 0, dz / d], d, boxes)) continue; // not through a wall (from their height: over a table they're on)
    if (d < out[c]) { out[c] = d; push(c, d); }
  }
  while (hc.length) {
    const [c, d] = pop();
    if (d > out[c]) continue;
    for (const [di, dj, w] of D8) { const n = link(nav, open, c, di, dj); if (n >= 0 && d + w < out[n]) { out[n] = d + w; push(n, d + w); } }
  }
}
// walk downhill on a field: a few cells ahead, as far as there's a straight line to it. null if we're at the bottom
function downhill(nav, open, f, pos, boxes) {
  let c = cellOf(nav, pos), out = null;
  if (c < 0) return null;
  for (let s = 0; s < 4; s++) {
    let nb = -1, nd = f[c];
    const on = walkable(nav, open, c);
    for (const [di, dj] of D8) {
      let n = on ? link(nav, open, c, di, dj) : -1;
      if (!on) { const i = (c % nav.W) + di, j = ((c / nav.W) | 0) + dj; if (i >= 0 && j >= 0 && i < nav.W && j < nav.D && walkable(nav, open, j * nav.W + i)) n = j * nav.W + i; } // knocked off the grid: any way back on
      if (n >= 0 && f[n] < nd) { nd = f[n]; nb = n; }
    }
    if (nb < 0) break;
    c = nb;
    const p = center(nav, c), dx = p[0] - pos[0], dz = p[1] - pos[2], d = Math.hypot(dx, dz);
    if (s && d > 0.2 && raycast([pos[0], pos[1] + 0.45, pos[2]], [dx / d, 0, dz / d], d, boxes)) break;
    out = p;
  }
  return out;
}

// ---------------------------------------------------------------- the mode, as Room methods
const methods = {
  // a new match (startRound): set zombies up if that's what's on, otherwise clear the last game's zombies away
  zmReset() {
    const on = !!GAMES[this.game].zombies && (this.mode === 'ffa' || this.mode === 'bots') && !!this.map.zm;
    const had = !!this.zs;
    for (const p of [...this.players.values()]) if (p.isBot && (p.zmz || (on && !p.ai.dummy))) this.remove(p); // regular bots sit this one out
    for (const p of this.players.values()) { p.z = null; p.zu = null; }
    this.zs = null;
    if (!on) { if (had && this.mode === 'bots') this.fillBots(); return; }
    const n = now(), Z = this.map.zm;
    this.zs = {
      map: this.cfg.map, nav: navFor(this.cfg.map), open: Z.doors.map(() => false), power: false,
      n: Math.max(0, (ZM.startRound || 1) - 1), st: 'pre', until: n + ZM.first, toSpawn: 0, spawnAt: 0,
      box: { st: 0, by: 0, w: '', until: 0 }, fields: new Map(), fieldT: n, win: Z.windows.map(() => 0), dead: [], list: [], tick: 0, lastT: n,
    };
    this.zs.boxes = this.zmBoxes();
    this.zs.areas = this.zmAreas();
    const hs = this.humans();
    for (const p of hs) { this.zmJoin(p); p.team = 1; } // one team, so friends' bullets pass through each other on screen
    this.broadcast({ t: 'teams', game: this.game, list: hs.map((p) => [p.id, 1, p.color]) });
  },
  // a fresh kit: 500 credits, the revolver and the knife
  zmJoin(p) {
    p.z = { c: ZM.start, guns: [], melee: '', ammo: {}, shotT: {}, kills: 0, heads: 0, downs: 0, revives: 0, earned: 0, hurtT: 0, cola: false, down: null, dead: false };
    this.zmKit(p);
  },
  zmKit(p) {
    const z = p.z;
    z.guns = ZM.startGuns.slice(); z.melee = ZM.startMelee; z.ammo = {};
    for (const w of z.guns) z.ammo[w] = zmAmmo(w);
  },
  // what p is carrying (sendLoadout calls this on every spawn): their guns + melee and the ammo each one has left
  zmLoadout(p, want) {
    if (!p.z) this.zmJoin(p); // joined mid-game
    if (p.team !== 1) { p.team = 1; this.broadcast({ t: 'teams', game: this.game, list: [[p.id, 1, p.color]] }); }
    p.forced = true; // so the next mode hands their own loadout back
    send(p, { t: 'zl', slots: [...p.z.guns, p.z.melee], ammo: p.z.ammo, want: want || undefined, c: p.z.c });
  },
  // the room's collision: the map plus every shutter that's still down
  zmBoxes() { return this.map.boxes.concat(this.map.zm.doors.filter((d, i) => !this.zs.open[i]).map((d) => d.box)); },
  zmAreas() { return zmOpenAreas(this.map.zm, this.zs.open); }, // only open areas spawn zombies and sell you things
  // what everyone needs to draw it (rides along in every snapshot via roundInfo)
  zmInfo() {
    const zs = this.zs, n = now(), dn = [], pts = [];
    for (const h of this.humans()) {
      const z = h.z;
      if (!z) continue;
      pts.push([h.id, z.c, h.alive ? 1 : z.down ? 2 : 3]);
      if (h.alive || !z.down) continue;
      const rv = this.zmReviver(h, n);
      dn.push([h.id, r2(z.down.at[0]), r2(z.down.at[1]), r2(z.down.at[2]), Math.max(0, z.down.until - n), rv ? r2(rv.f) : 0, rv ? rv.p.id : 0]);
    }
    let alive = 0;
    for (const p of this.players.values()) if (p.zmz && p.alive) alive++;
    const bx = zs.box;
    return {
      n: zs.n, st: zs.st, left: zs.toSpawn + alive, br: zs.st === 'pre' || zs.st === 'break' ? Math.max(0, zs.until - n) : 0,
      o: zs.open.reduce((a, o, i) => (o ? a.concat(i) : a), []), pw: zs.power ? 1 : 0, bx: bx.st ? [bx.st, bx.by, bx.w, Math.max(0, bx.until - n)] : 0, dn, pts,
    };
  },

  // ---------------------------------------------------------- the round loop (tickRound hands over while zombies is on)
  zmRound(n) {
    const zs = this.zs, dt = Math.min(0.1, (n - zs.lastT) / 1000);
    zs.lastT = n; zs.tick++;
    for (const b of zs.dead) if (this.players.get(b.id) === b) this.remove(b); // killed last tick: everyone got the kill by now
    zs.dead.length = 0;
    zs.list.length = 0;
    for (const p of this.players.values()) if (p.zmz && p.alive) zs.list.push(p);
    if (zs.st === 'over') return;
    const hs = this.humans();
    this.zmFields(n, hs);
    this.zmPlayers(n, dt, hs);
    this.zmCrate(n);
    for (const b of zs.list) if (b.zmz.ph === 'hunt' && (n - b.zmz.seen > 25000 || b.zmz.stuck > 8)) { this.remove(b); zs.toSpawn++; } // lost or wedged: try again from a window
    if (hs.length && hs.every((h) => !h.alive)) { this.zmGameOver(); return; }
    if (zs.st !== 'live') { if (n >= zs.until) this.zmNextRound(n, hs); return; }
    let alive = 0;
    for (const b of this.players.values()) if (b.zmz && b.alive) alive++;
    if (zs.toSpawn > 0 && alive < zmMaxAlive(hs.length) && n >= zs.spawnAt) zs.spawnAt = n + (this.zmSpawn(n, hs) ? zmGap(zs.n, hs.length) : 500);
    if (zs.toSpawn <= 0 && !alive) this.zmCleared(n, hs);
  },
  zmNextRound(n, hs) {
    const zs = this.zs;
    zs.n++; zs.st = 'live';
    zs.toSpawn = zmCount(zs.n, hs.length); zs.spawnAt = n + 1500;
    for (const h of hs) if (!h.alive) this.zmRespawn(h); // the dead come back for the new round
    this.broadcast({ t: 'zround', k: 'start', n: zs.n, count: zs.toSpawn });
  },
  zmCleared(n, hs) {
    const zs = this.zs;
    zs.st = 'break'; zs.until = n + ZM.rest;
    this.broadcast({ t: 'zround', k: 'clear', n: zs.n, ms: ZM.rest });
    for (const h of hs) {
      stat(h, 'xp', 8 + zs.n * 4);
      if (zs.n % 5 === 0 && h.acct && store) { const kind = randomContainer(); store.grantRolls(h.acct.n, kind, 1).catch(() => {}); send(h, { t: 'roll+', n: 1, kind, why: `survived zombies round ${zs.n}` }); }
    }
  },
  // a flow field per living player, redone when they've moved, every so often, and right after a door opens
  zmFields(n, hs) {
    const zs = this.zs, nav = zs.nav;
    for (const id of zs.fields.keys()) if (!this.players.has(id)) zs.fields.delete(id);
    for (const h of hs) {
      if (!h.alive) continue;
      let f = zs.fields.get(h.id);
      if (!f) zs.fields.set(h.id, (f = { d: new Float32Array(nav.W * nav.D), t: 0, at: [1e9, 0, 0] }));
      const moved = Math.hypot(h.pos[0] - f.at[0], h.pos[2] - f.at[2]);
      if (f.t > zs.fieldT && n - f.t < 1500 && (n - f.t < 300 || moved < 0.75)) continue;
      flow(nav, zs.open, h.pos, this.boxes, f.d);
      f.t = n; f.at = h.pos.slice();
    }
  },
  // regen, bleeding out (paused while someone's reviving you)
  zmPlayers(n, dt, hs) {
    for (const h of hs) {
      const z = h.z;
      if (!z) continue;
      if (h.alive) { if (h.hp < 100 && n - z.hurtT > ZM.regenAfter * 1000) h.hp = Math.min(100, h.hp + ZM.regen * (z.cola ? 1.6 : 1) * dt); continue; }
      if (!z.down) continue;
      if (this.zmReviver(h, n)) z.down.until += dt * 1000;
      else if (n >= z.down.until) { z.down = null; z.dead = true; this.broadcast({ t: 'zdown', id: h.id, k: 'out' }); }
    }
  },
  zmReviver(h, n) {
    for (const p of this.players.values()) {
      const u = p.zu;
      if (p.alive && u && u.k === 'r' + h.id && !u.done && n - u.last < USE_GAP) return { p, f: Math.min(1, (n - u.t0) / (ZM.revive * 1000)) };
    }
    return null;
  },
  zmCrate(n) {
    const bx = this.zs.box;
    if (bx.st === 1 && n >= bx.until) { bx.st = 2; bx.until = n + ZM.offer; this.broadcast({ t: 'zbox', k: 'offer', by: bx.by, w: bx.w, ms: ZM.offer }); }
    else if (bx.st === 2 && (n >= bx.until || !this.players.has(bx.by))) { bx.st = 0; this.broadcast({ t: 'zbox', k: 'gone' }); }
  },
  // everyone's down: game over. how far you got, then the vote (and the play of the game, like any match)
  zmGameOver() {
    const zs = this.zs, n = now(), r = this.round;
    zs.st = 'over';
    const hs = this.humans().sort((a, b) => ((b.z && b.z.kills) || 0) - ((a.z && a.z.kills) || 0));
    r.over = true; r.next = n + VOTE_MS + 2000; r.winTeam = 0;
    this.startVote();
    this.broadcast({ t: 'round', over: 1, winner: 0, winTeam: 0, game: this.game, sc: null, top: hs.slice(0, 6).map((p) => [p.id, p.name, p.kills, p.deaths, 0]), next: VOTE_MS + 2000 });
    this.broadcast({ t: 'zmover', n: zs.n, rows: hs.map((p) => { const z = p.z || {}; return [p.id, p.name, z.kills || 0, z.heads || 0, z.downs || 0, z.revives || 0, z.earned || 0]; }) });
    setTimeout(() => {
      if (this.round !== r || !r.hl || r.hl.pending || !r.hl.clip || !r.hl.clip.frames.length) return;
      const k = this.players.get(r.hl.id);
      if (!k || k.isBot) return; // a zombie's kill (yours) is nobody's play of the game
      const { label, id, name, color, card, clip } = r.hl;
      this.broadcast({ t: 'hl', label, id, name, color, card, clip });
    }, 1600);
  },

  // ---------------------------------------------------------- players: down, revived, back next round
  // kill hook: a zombie pays out (+60, +100 for a headshot or melee kill), a player goes down (revivable while a friend is up)
  zmKilled(t, killer, w) {
    const zs = this.zs;
    t.respawnAt = Infinity; // nobody respawns on a timer here
    if (t.zmz) {
      zs.dead.push(t);
      if (killer && killer !== t && !killer.isBot && killer.z) {
        const melee = !!WEAPONS[w] && (WEAPONS[w].kind === 'melee' || w === 'slipper'), head = !!t.lastHs && !melee;
        this.zmGive(killer, melee || head ? ZM.bonus : ZM.kill, melee ? 'melee' : head ? 'head' : 'kill');
        killer.z.kills++;
        if (head) killer.z.heads++;
      }
      return;
    }
    if (t.isBot || !t.z) return;
    const z = t.z;
    z.downs++; z.cola = false;
    z.down = zs.st !== 'over' && this.humans().some((h) => h !== t && h.alive) ? { at: t.pos.slice(), until: now() + ZM.bleed * 1000 } : null;
    z.dead = !z.down;
    this.broadcast({ t: 'zdown', id: t.id, k: z.down ? 'down' : 'dead' });
  },
  zmUp(h, pos) { // back on your feet at pos, with your kit
    h.alive = true; h.hp = 100; h.vel = [0, 0, 0]; h.spawnT = now(); h.seq++; h.pos = pos.slice(); h.respawnAt = Infinity;
    h.slipUntil = 0; h.burnUntil = 0; h.sleepUntil = 0; h.frozenUntil = 0; h.frost = 0; h.healLeft = 0; h.z.hurtT = 0;
    send(h, { t: 'spawn', p: h.pos, q: h.seq });
    this.zmLoadout(h);
  },
  zmRespawn(h) {
    if (!h.z) this.zmJoin(h);
    if (!h.z.down) this.zmKit(h); // bled out: back to the revolver and the knife (still downed keeps their guns)
    h.z.down = null; h.z.dead = false;
    this.zmUp(h, this.pickSpawn(false, h));
  },
  zmRevive(h, by) {
    const at = h.z.down.at;
    h.z.down = null;
    this.zmUp(h, at);
    if (by && by.z) by.z.revives++;
    this.broadcast({ t: 'zdown', id: h.id, k: 'up', by: by ? by.id : 0 });
  },
  zmGive(p, d, why) { p.z.c += d; if (d > 0) p.z.earned += d; send(p, { t: 'zc', c: p.z.c, d, why }); },
  // damage hook: hits on zombies pay +10 (a zombie's first 10, one per player per 180 ms), zombie claws hit equally hard
  // in every room and half as hard with a Jank Cola, and getting hurt holds off your regen
  zmDamage(t, amt, a) {
    const n = now();
    if (t.zmz) {
      const z = t.zmz;
      if (a && !a.isBot && a.z && amt > 0 && z.hits < ZM.hitCap && n - (z.hitAt[a.id] || 0) >= ZM.hitGap) { z.hitAt[a.id] = n; z.hits++; this.zmGive(a, ZM.hit, 'hit'); }
      return amt;
    }
    if (t.isBot || !t.z) return amt;
    t.z.hurtT = n;
    if (!a || !a.zmz) return amt;
    return (amt * (DIFF[this.cfg.diff] || DIFF.normal).dmg * (t.z.cola ? 0.5 : 1)) / (this.mode === 'bots' ? 1 : 0.6); // damage() softens bots outside the Bots room: not these
  },
  // hit / fire / push hooks: only weapons you own, and guns need ammo. one shot = its fire message and its hits,
  // which all arrive within a fraction of the gun's fire interval
  zmArm(p, wid) {
    const z = p.z, w = WEAPONS[wid];
    if (!z || !w || (wid !== z.melee && !z.guns.includes(wid))) return false;
    if (z.ammo[wid] == null) return true; // melee, the cigarette, the blower
    const n = now(), iv = w.rate ? 1000 / fireRate(w, p.hp) : (w.cd || 0.35) * 750;
    if (n - (z.shotT[wid] || 0) < iv * 0.55) return true; // part of a shot we already counted
    if (z.ammo[wid] <= 0) return false;
    z.ammo[wid]--; z.shotT[wid] = n;
    if (!w.mag) send(p, { t: 'za', w: wid, n: z.ammo[wid] }); // the client counts mags itself, not these
    return true;
  },

  // ---------------------------------------------------------- F: doors, wall guns, the crate, power, cola, revives
  zmView(p) {
    const down = [];
    for (const h of this.humans()) if (!h.alive && h.z && h.z.down) down.push([h.id, ...h.z.down.at]);
    return { open: this.zs.open, power: this.zs.power, down, me: p.id };
  },
  // tryUse hook: 'use' arrives every 200 ms while F is held. hold it on the same thing long enough and it happens once.
  // only from inside an area that's open: movement is the client's, so walking through a shutter buys you nothing
  zmUse(p) {
    const zs = this.zs, n = now();
    if (!p.alive || !p.z || zs.st === 'over') return;
    const t = zs.areas.has(zmAreaAt(this.map.zm, p.pos)) ? zmTarget(this.map.zm, this.zmView(p), eyeOf(p), lookOf(p), 0.6) : null;
    if (!t) { p.zu = null; return; }
    let u = p.zu;
    if (!u || u.k !== t.k || n - u.last > USE_GAP) u = p.zu = { k: t.k, t0: n, last: n, done: false };
    u.last = n;
    if (u.done) return;
    const need = (t.kind === 'revive' ? ZM.revive : t.kind === 'power' ? ZM.power : ZM.hold) * 1000;
    if (n - u.t0 + 30 >= need) { u.done = true; this.zmDo(p, t); }
  },
  zmDo(p, t) {
    const zs = this.zs, Z = this.map.zm, z = p.z;
    if (t.kind === 'revive') { const h = this.players.get(t.id); if (h && !h.alive && h.z && h.z.down) this.zmRevive(h, p); return; }
    if (t.kind === 'door') { if (!zs.open[t.i] && this.zmPay(p, Z.doors[t.i].price, t.k)) this.zmOpen(t.i, p); return; }
    if (t.kind === 'buy') {
      const b = Z.buys[t.i];
      if (b.w === z.melee || z.guns.includes(b.w)) { // already yours: a refill
        const max = zmAmmo(b.w);
        if (max == null || z.ammo[b.w] >= max) { this.zmSay(p, t.k, false, max == null ? 'you already have it' : 'ammo full'); return; }
        if (!this.zmPay(p, zmAmmoPrice(b.price), t.k)) return;
        z.ammo[b.w] = max; this.zmLoadout(p); this.zmSay(p, t.k, true, `${WEAPONS[b.w].name} ammo`);
        return;
      }
      if (this.zmPay(p, b.price, t.k)) { this.zmGrant(p, b.w); this.zmSay(p, t.k, true, WEAPONS[b.w].name); }
      return;
    }
    if (t.kind === 'crate') {
      const bx = zs.box;
      if (bx.st === 2 && bx.by === p.id) { bx.st = 0; this.zmGrant(p, bx.w); this.zmSay(p, t.k, true, WEAPONS[bx.w].name); this.broadcast({ t: 'zbox', k: 'take', by: p.id, w: bx.w }); return; }
      if (bx.st) { this.zmSay(p, t.k, false, bx.st === 1 ? 'still spinning' : 'that one is someone else\'s'); return; }
      if (!this.zmPay(p, ZM.crate, t.k)) return;
      Object.assign(bx, { st: 1, by: p.id, w: zmPick([...z.guns, z.melee]), until: now() + ZM.spin });
      this.broadcast({ t: 'zbox', k: 'spin', by: p.id, w: bx.w, ms: ZM.spin });
      return;
    }
    if (t.kind === 'power') { if (!zs.power) { zs.power = true; this.broadcast({ t: 'zpower', by: p.id }); } return; }
    if (t.kind === 'cola') {
      if (!zs.power) { this.zmSay(p, t.k, false, 'no power. find the switch'); return; }
      if (z.cola) { this.zmSay(p, t.k, false, 'one is enough'); return; }
      if (this.zmPay(p, ZM.cola, t.k)) { z.cola = true; this.zmSay(p, t.k, true, 'JANK COLA'); this.broadcast({ t: 'fx', k: 'medkit', id: p.id }); }
    }
  },
  zmPay(p, price, k) {
    if (p.z.c < price) { this.zmSay(p, k, false, `need ${price}`); return false; }
    this.zmGive(p, -price, 'buy');
    return true;
  },
  zmSay(p, k, ok, m) { send(p, { t: 'zbuy', k, ok: ok ? 1 : 0, m }); },
  zmOpen(i, by) {
    const zs = this.zs;
    zs.open[i] = true; zs.boxes = this.zmBoxes(); zs.areas = this.zmAreas(); zs.fieldT = now();
    this.broadcast({ t: 'zdoor', i, by: by ? by.id : 0 });
  },
  // a new weapon: melee replaces your melee, a gun takes a free slot or replaces the gun in your hands
  zmGrant(p, w) {
    const z = p.z;
    if (WEAPONS[w].slot === 'melee') z.melee = w;
    else if (!z.guns.includes(w)) {
      if (z.guns.length < ZM.guns) z.guns.push(w);
      else { let i = z.guns.indexOf(p.w); if (i < 0) i = z.guns.length - 1; delete z.ammo[z.guns[i]]; z.guns[i] = w; }
    }
    if (zmAmmo(w) != null) z.ammo[w] = zmAmmo(w);
    this.zmLoadout(p, w);
  },

  // ---------------------------------------------------------- the zombies
  zmSpawn(n, hs) {
    const zs = this.zs, Z = this.map.zm, live = hs.filter((h) => h.alive);
    const wins = [];
    Z.windows.forEach((w, i) => { if (zs.areas.has(w.area)) wins.push(i); });
    if (!wins.length || !live.length) return false;
    const near = (i) => Math.min(...live.map((h) => dist3(Z.windows[i].in, h.pos)));
    wins.sort((a, b) => near(a) - near(b));
    const wi = pick(wins.slice(0, 3)), w = Z.windows[wi]; // one of the windows nearest the players
    const g = zmGait(zs.n, Math.random(), Math.random()), D = DIFF[this.cfg.diff] || DIFF.normal;
    const along = (Math.random() - 0.5) * 2.2, back = Math.random() * 0.8; // somewhere in the alley
    const pos = [w.out[0] - w.n[2] * along - w.n[0] * back, 0, w.out[2] + w.n[0] * along - w.n[2] * back];
    const b = this.newPlayer('Zombie', { isBot: true, pos, color: GLOW[g.kind], skins: {}, ai: { diff: this.cfg.diff, dummy: null } });
    b.w = ''; b.hp = Math.round(zmHp(zs.n) * D.hp); b.look = zombieLook(); b.kfx = 'none'; b.team = 0; b.yaw = w.yaw; b.pitch = 0.3;
    b.zmz = { ph: 'wait', win: wi, t: n + 300 + Math.random() * 1500, speed: g.speed * D.speed, run: g.kind, wish: [0, 0], target: 0, close: false,
      swingAt: 0, nextSwing: 0, hits: 0, hitAt: {}, seen: n, chk: n, chkPos: pos.slice(), stuck: 0 };
    this.players.set(b.id, b);
    this.broadcast({ t: 'pj', ...this.info(b) });
    zs.toSpawn--;
    return true;
  },
  // one zombie, one tick (stepBot hands them over): climb in, then chase, swipe and shuffle round each other
  zmStep(b, dt) {
    const zs = this.zs, z = b.zmz, n = now();
    if (!this.zm) return;
    if (z.ph !== 'hunt') { this.zmClimb(b, z, n); return; }
    const v = b.vel;
    const frozen = n < (b.frozenUntil || 0), slipping = n < (b.slipUntil || 0), stun = frozen || slipping || (b.sleepUntil || 0) > n || zs.st === 'over';
    if (!stun && (zs.tick + b.id) % 3 === 0) this.zmThink(b, z, n);
    let tx = 0, tz = 0;
    if (!stun) {
      const s = z.close ? 0 : z.speed * (z.swingAt ? 0.35 : 1);
      tx = z.wish[0] * s; tz = z.wish[1] * s;
      for (const o of zs.list) { // don't stack up on each other
        if (o === b) continue;
        const dx = b.pos[0] - o.pos[0], dz = b.pos[2] - o.pos[2], d2 = dx * dx + dz * dz;
        if (d2 > 0.8 || d2 < 1e-6 || Math.abs(b.pos[1] - o.pos[1]) > 1.5) continue;
        const d = Math.sqrt(d2), k = ((0.9 - d) * 7) / d;
        tx += dx * k; tz += dz * k;
      }
      for (const h of this.players.values()) { // and don't walk into the people they're clawing at (players don't collide)
        if (h.isBot || !h.alive) continue;
        const dx = b.pos[0] - h.pos[0], dz = b.pos[2] - h.pos[2], d2 = dx * dx + dz * dz;
        if (d2 > 0.64 || d2 < 1e-6 || Math.abs(b.pos[1] - h.pos[1]) > 1.6) continue;
        const d = Math.sqrt(d2), k = ((0.8 - d) * 10) / d;
        tx += dx * k; tz += dz * k;
      }
    }
    if (b.onGround) {
      if (frozen) { v[0] = 0; v[2] = 0; } else {
        const k = Math.min(1, (slipping ? 0.5 : Math.hypot(v[0], v[2]) > z.speed + 2.5 ? 3 : 10) * dt); // knocked flying: slide it out
        v[0] += (tx - v[0]) * k; v[2] += (tz - v[2]) * k;
      }
      if (z.jump && !stun) { v[1] = 8.4; b.onGround = false; }
    } else if (!stun) { const k = Math.min(1, 1.2 * dt); v[0] += (tx - v[0]) * k; v[2] += (tz - v[2]) * k; }
    z.jump = false;
    v[1] -= 26 * dt;
    const res = movePlayer(b.pos, v, dt, this.boxes, b.onGround);
    b.onGround = !!res.ground && v[1] <= 0.01;
    b.f = slipping ? FLAGS.SLIP : 0;
    if (b.pos[1] < this.map.killY) { this.kill(b, null, 'void'); return; }
    if (stun) return;
    const t = this.players.get(z.target);
    const fx = z.close && t ? t.pos[0] - b.pos[0] : tx, fz = z.close && t ? t.pos[2] - b.pos[2] : tz;
    if (Math.abs(fx) + Math.abs(fz) > 0.05) b.yaw = turn(b.yaw, Math.atan2(-fx, -fz), 7 * dt);
    b.pitch = 0.25; // arms out
    this.zmSwipe(b, z, t, n);
    if (n - z.chk > 1200) { // wedged on something: hop and sidestep
      const moved = Math.hypot(b.pos[0] - z.chkPos[0], b.pos[2] - z.chkPos[2]);
      if (!z.close && !z.swingAt && z.speed > 0 && moved < 0.6) { z.stuck++; z.jump = true; z.side = n + 700; z.sideDir = Math.random() < 0.5 ? 1 : -1; } else z.stuck = 0;
      z.chk = n; z.chkPos = b.pos.slice();
    }
  },
  // who to chase (the nearest player on foot, from the flow fields) and which way: straight at them when nothing's in the way
  zmThink(b, z, n) {
    const zs = this.zs, nav = zs.nav, c = cellOf(nav, b.pos);
    let best = null, bd = Infinity, bf = null;
    for (const h of this.players.values()) {
      if (h.isBot || !h.alive) continue;
      const f = zs.fields.get(h.id);
      let d = f && c >= 0 ? f.d[c] : Infinity;
      if (d === Infinity && f && c >= 0) for (const [di, dj, w] of D8) { const i = (c % nav.W) + di, j = ((c / nav.W) | 0) + dj; if (i >= 0 && j >= 0 && i < nav.W && j < nav.D) d = Math.min(d, f.d[j * nav.W + i] + w); }
      if (d === Infinity) d = 1000 + dist3(h.pos, b.pos); // can't walk there: worse than anyone we can reach
      if (d < bd) { bd = d; best = h; bf = d < 1000 ? f : null; }
    }
    z.target = best ? best.id : 0;
    if (!best) { z.wish = [0, 0]; z.close = false; return; }
    const dx = best.pos[0] - b.pos[0], dz = best.pos[2] - b.pos[2], dy = best.pos[1] - b.pos[1], hd = Math.hypot(dx, dz) || 1e-6;
    if (hd < 22) z.seen = n;
    z.close = hd < 0.85 && Math.abs(dy) < 2;
    let wx = dx / hd, wz = dz / hd;
    if (!(hd < 9 && Math.abs(dy) < 1.4 && this.zmClear(b.pos, best.pos, hd)) && bf) {
      const p = downhill(nav, zs.open, bf.d, b.pos, this.boxes);
      if (p) { const ex = p[0] - b.pos[0], ez = p[1] - b.pos[2], el = Math.hypot(ex, ez) || 1; wx = ex / el; wz = ez / el; }
    }
    if (n < (z.side || 0)) { const a = z.sideDir * 1.3, ca = Math.cos(a), sa = Math.sin(a); [wx, wz] = [wx * ca - wz * sa, wx * sa + wz * ca]; }
    z.wish = [wx, wz];
  },
  zmClear(a, b, hd) { // a straight walk from a to b with nothing in the way (knees and chest)
    const d = [(b[0] - a[0]) / hd, 0, (b[2] - a[2]) / hd];
    return !raycast([a[0], a[1] + 0.45, a[2]], d, hd, this.boxes) && !raycast([a[0], a[1] + 1.3, a[2]], d, hd, this.boxes);
  },
  // claws: a short windup everyone can see, then it lands if you're still in reach (jumping at you if you're up on something)
  zmSwipe(b, z, t, n) {
    if (z.swingAt) {
      if (n < z.swingAt) return;
      z.swingAt = 0;
      if (!t || !t.alive) return;
      const dx = t.pos[0] - b.pos[0], dz = t.pos[2] - b.pos[2], dy = t.pos[1] - b.pos[1], hd = Math.hypot(dx, dz) || 1e-6;
      if (hd > ZM.reachHit || dy < -1.3 || dy > ZM.reachUp + 0.3) return; // dodged
      const ry = t.pos[1] + 0.9 - b.pos[1] - 1.9, rl = Math.hypot(hd, ry); // from its head to your middle: over the top of anything you climbed on
      if (hd > 0.9 && raycast([b.pos[0], b.pos[1] + 1.9, b.pos[2]], [dx / rl, ry / rl, dz / rl], rl, this.boxes)) return; // not through a wall
      if (ZM.swipe > 0) this.hurt(t, b, 'bite', ZM.swipe, [(dx / hd) * 4, 2, (dz / hd) * 4]);
      return;
    }
    if (!t || !t.alive || n < z.nextSwing) return;
    const dx = t.pos[0] - b.pos[0], dz = t.pos[2] - b.pos[2], dy = t.pos[1] - b.pos[1];
    if (Math.hypot(dx, dz) > ZM.reach + (z.run ? 0.25 : 0) || dy < -1.2 || dy > ZM.reachUp) return;
    z.swingAt = n + ZM.windup; z.nextSwing = n + ZM.swipeCd;
    if (dy > 1 && b.onGround) z.jump = true;
    this.broadcast({ t: 'fx', k: 'swing', w: 'bite', id: b.id, a: [r2(b.pos[0]), r2(b.pos[1] + 1.4), r2(b.pos[2])] });
  },
  // still outside: wait at the window (banging on it), then climb over the sill and drop in
  zmClimb(b, z, n) {
    const zs = this.zs, w = this.map.zm.windows[z.win];
    b.vel = [0, 0, 0]; b.onGround = true; b.yaw = w.yaw; b.pitch = 0.3;
    if (z.ph === 'wait') {
      b.f = 0;
      if (zs.st !== 'over' && n >= z.t && zs.win[z.win] <= n) { z.ph = 'climb'; z.t0 = n; z.dur = z.run ? 850 : 1350; zs.win[z.win] = n + z.dur * 0.6; z.from = b.pos.slice(); }
      else if (n >= (z.bang || 0)) { z.bang = n + 600 + Math.random() * 900; this.broadcast({ t: 'fx', k: 'swing', w: 'bite', id: b.id, a: [r2(b.pos[0]), 1.4, r2(b.pos[2])] }); }
      return;
    }
    const k = Math.min(1, (n - z.t0) / z.dur), a = z.from, c = w.in, s = z.dur / 1000;
    const up = Math.min(1, Math.max(0, (k - 0.15) / 0.22)) * Math.min(1, Math.max(0, (0.92 - k) / 0.2)); // over the sill
    b.pos = [a[0] + (c[0] - a[0]) * k, up, a[2] + (c[2] - a[2]) * k];
    b.vel[0] = (c[0] - a[0]) / s; b.vel[2] = (c[2] - a[2]) / s; // so the legs walk
    b.f = k > 0.2 && k < 0.85 ? FLAGS.CROUCH : 0;
    if (k >= 1) { z.ph = 'hunt'; b.vel = [0, 0, 0]; b.onGround = false; z.chk = n; z.chkPos = b.pos.slice(); z.seen = n; }
  },
};

export function installZombies(Room, h) {
  ({ send, stat, store } = h);
  // zombies is on: this room has a zombies state, for the map it's playing on (stale between a map change and the next match)
  Object.defineProperty(Room.prototype, 'zm', { get() { return !!this.zs && this.zs.map === this.cfg.map; } });
  Object.assign(Room.prototype, methods);
}
