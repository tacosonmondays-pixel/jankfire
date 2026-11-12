// Jank Royale on the server: the blimp, the drop, loot on the floor, inventories, armour, the zone, placements, and
// the bots that play it. Installed onto Room (server.js) like the other add-on modes: everything here is a Room method,
// and server.js only calls a handful of small hooks (see `brOn` in server.js).
// The server owns all of it: what's on the floor, who holds what, how many bullets are left, armour, the zone's damage.
import { pitUnder } from '../shared/pits.js';
import { GAMES } from '../shared/modes.js';
import { MAPS } from '../shared/map.js';
import { WEAPONS, ITEMS, BOT_DIFF, FLAGS } from '../shared/weapons.js';
import { raycast, PH } from '../shared/physics.js';
import { navSteer } from '../shared/nav.js';
import { outOfBounds } from '../shared/bounds.js';
import { poiAt, BR, ZONE, TIERS, GUNS, MELEE, GADGETS, STUFF, ARMOR_OF, ammoFor, bucketFor, blimpAt, blimpDone, zoneAt, outsideZone, hookCharges, hookSpend } from '../shared/royale.js';
import { onWarm, onForget } from './graphs.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const pick = (a) => a[(Math.random() * a.length) | 0];
const hdist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const num = (x) => (typeof x === 'number' ? x : 0);
const wpick = (tbl) => { // weighted pick from { id: { w } }
  let s = 0;
  for (const k in tbl) s += tbl[k].w;
  let r = Math.random() * s;
  for (const k in tbl) { r -= tbl[k].w; if (r <= 0) return k; }
  return Object.keys(tbl)[0];
};
const LOG = !!process.env.JF_BR_LOG; // test knob: print how every royale went (drops, deaths, the winner)

// ------------------------------------------------------------ loot spots (found once per map, from its boxes)
// a grid over the play area; at each point, every floor you could stand on going down (roof, upper floors, ground).
// indoor = there's a ceiling within 12 m. these are where loot can go and where the zone may end
function findSpots(map) {
  if (map._brSpots) return map._brSpots;
  const b = map.bounds || [-60, -60, 60, 60], boxes = map.boxes, out = [];
  const step = 3.2;
  for (let x = b[0] + 2; x < b[2] - 2; x += step) for (let z = b[1] + 2; z < b[3] - 2; z += step) {
    const px = x + (Math.random() - 0.5) * 1.6, pz = z + (Math.random() - 0.5) * 1.6;
    let top = 80;
    for (let lv = 0, bottom = false; lv < 5 && !bottom; lv++) {
      const h = raycast([px, top, pz], [0, -1, 0], top - map.killY, boxes);
      if (!h || h.axis !== 1) break;
      const y = top - h.t;
      if (y < map.killY + 2) break;
      const box = h.box;
      bottom = !!box.terr; // shaped ground (shared/terrain.js): nothing to stand on under it, only its own hidden slab
      top = box.min[1] - 0.05;
      if (box.pad || box.max[0] - box.min[0] < 1.2 || box.max[2] - box.min[2] < 1.2) continue; // jump pads, beams, railings
      const p = [px, y, pz];
      if (raycast([px, y + 0.05, pz], [0, 1, 0], 2.1, boxes)) continue; // no headroom
      const ceil = raycast([px, y + 0.05, pz], [0, 1, 0], 12, boxes);
      // feet room: not hugging a wall (loot in walls is no fun)
      let tight = false;
      for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (raycast([px, y + 0.5, pz], [d[0], 0, d[1]], 0.7, boxes)) tight = true;
      if (tight) continue;
      out.push({ p, indoor: !!ceil, ground: lv === 0 ? !ceil : false, lv });
    }
  }
  return (map._brSpots = out);
}
// the points bots can walk to and the zone can close on: open ground inside the play area
function groundSpots(map) {
  if (map._brGround) return map._brGround;
  return (map._brGround = findSpots(map).filter((s) => onGround(map, s.p) && !outOfBounds(map, s.p)));
}
// is p down on the ground (not a roof)? a city (Jankburg): street level, under 1.6 m. an island (shaped ground with a
// sea: map.boxes.terrain + map.seaY): on the terrain's own surface, and above the sea
export function onGround(map, p) {
  const T = map.boxes && map.boxes.terrain;
  if (!T || map.seaY == null) return p[1] < 1.6;
  const g = T.at(p[0], p[2]);
  return g != null && Math.abs(g - p[1]) <= 0.3 && (map.seaY == null || g > map.seaY);
}
export { groundSpots }; // (tests)

// a tier for a find: its base tier, plus luck (better spots roll higher)
function rollTier(base, q) {
  let t = base;
  while (t < 4 && Math.random() < 0.14 + q * 0.22) t++;
  return t;
}

export function installRoyale(Room, H) {
  onWarm((room, m) => { if (room.brOn) groundSpots(m); }); // a royale starting: its loot spots now, not at the first drop (server/graphs.js)
  onForget((m) => { delete m._brSpots; delete m._brGround; delete m._brGrid; }); // nobody's played it for a while
  const { send } = H;
  Object.defineProperty(Room.prototype, 'brOn', {
    get() { return (this.mode === 'ffa' || this.mode === 'bots') && !!GAMES[this.game].royale && !!this.map.royale; },
  });
  Object.assign(Room.prototype, {
    // ---------------------------------------------------------- a match: the blimp, the zone plan, loot everywhere
    brRound() {
      if (!this.brOn) { if (this.br) this.brClear(); return; }
      if (this.mode === 'bots') this.fillBots();
      const n = now(), map = this.map, R = map.royale, z0 = R.zone0 || [0, 0, 150];
      // the blimp: a straight line over the middle (give or take), any direction
      const a = Math.random() * Math.PI * 2, d = [Math.cos(a), Math.sin(a)], off = (Math.random() - 0.5) * 70;
      const mid = [z0[0] - d[1] * off, z0[1] + d[0] * off];
      const path = { a: [r2(mid[0] - d[0] * BR.blimp.len), r2(mid[1] - d[1] * BR.blimp.len)], d: [r2(d[0]), r2(d[1])], y: R.blimpY || 75, t0: n };
      // the zone: each circle sits inside the last one, centred on ground you can stand on
      const ground = groundSpots(map), steps = [];
      let c = [z0[0], z0[1]], r = z0[2];
      for (const [wait, shrink, share, dps] of ZONE) {
        const nr = z0[2] * share, room = Math.max(0, r - nr);
        const ok = ground.filter((s) => Math.hypot(s.p[0] - c[0], s.p[2] - c[1]) <= room * 0.9);
        const nc = ok.length ? pick(ok).p : null;
        const cc = nc ? [r2(nc[0]), r2(nc[2])] : c;
        steps.push({ c: cc, r: r2(nr), wait, shrink, dps });
        c = cc; r = nr;
      }
      if (this.isleOn) this.isleZoneSteps(steps, z0, ground); // battle island: its own 5 rings (server/islemeter.js)
      const zone = { t0: n, c0: [z0[0], z0[1]], r0: z0[2], steps };
      const end = steps.reduce((t, s) => t + (s.wait + s.shrink) * 1000, n) + 90000;
      this.br = { id: n, phase: 'blimp', path, zone, t0: n, peak: 0, winner: 0, endAt: 0, out: [], zoneT: n, loot: new Map(), nextLoot: 1, log: [], leader: 0, crates: [], nextCrate: 1, drops: [75000, 170000], goblins: [42000, 150000], vend: new Map() };
      for (const g of [...this.players.values()]) if (g.goblin) this.remove(g);
      if (this.round) { this.round.target = 0; this.round.ends = end; }
      this.brSpawnLoot();
      if (this.isleOn) this.isleCells(); // battle island: energy cells for the mech meter
      const list = this.fighters();
      for (const p of list) this.brBoard(p);
      this.br.peak = list.length;
      this.broadcast({ t: 'br', k: 'start', ...this.brState() });
      if (this.isleOn) this.isleStart(); // battle island: who's in which squad
      for (const p of list) this.brLoadout(p);
      if (LOG) console.log(`[br] start on ${map.name}: ${list.length} in the blimp, ${this.br.loot.size} loot`);
    },
    brClear() {
      for (const g of [...this.players.values()]) if (g.goblin) this.remove(g);
      this.br = null;
      for (const p of this.players.values()) { p.br = null; p.f &= ~FLAGS.GLIDE; }
      this.broadcast({ t: 'br', k: 'off' });
      if (this.mode === 'bots') this.fillBots();
    },
    brState() {
      const B = this.br;
      return {
        path: B.path, zone: B.zone, phase: B.phase, at: now(),
        loot: [...B.loot.values()].map((l) => this.brLootInfo(l)), leader: B.leader, crates: B.crates.filter((c) => !c.open).map((c) => this.brCrateInfo(c)),
        goblins: [...this.players.values()].filter((g) => g.goblin).map((g) => g.id),
        blimp: this.fighters().filter((p) => p.br && p.br.inBlimp).map((p) => p.id),
        out: B.out.map((o) => [o.id, o.place]),
      };
    },
    brLootInfo(l) { return [l.i, l.k, l.id, l.tier || 0, l.n || 0, l.a == null ? -1 : l.a, l.p[0], l.p[1], l.p[2]]; },
    // on board: fresh pockets (a loaf of bread), full HP, riding along
    brBoard(p) {
      p.br = { match: this.br.id, slots: [null, null], melee: { w: BR.melee, tier: 0 }, gadget: null, cola: 0, medkit: 0, armor: 0, inBlimp: true, fly: null, out: false, place: 0, heal: null, ai: null, kills: 0, picks: 0, gunT: 0, skips: 0, landT: 0, mailed: false, mailAt: 0 };
      p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.healLeft = 0;
      p.respawnAt = 0;
      const bp = blimpAt(this.br.path, now());
      p.pos = [bp[0], bp[1] - 3, bp[2]];
      p.w = BR.melee;
      if (p.isBot) { p.ai.ammo = 1; p.ai.reloadUntil = 0; p.ai.hook = null; p.g = null; }
      if (this.isleOn) this.isleBoard(p); // battle island: your squad
    },
    // a late joiner: a seat on the blimp if it's still near the start, otherwise watch until the next one
    brJoin(p) {
      const B = this.br;
      if (!B || !this.brOn) return;
      if (p.isBot && !(B.phase === 'blimp' && now() - B.t0 < BR.late)) { p.br = { match: B.id, out: true, slots: [], melee: null }; p.alive = false; p.hp = 0; p.respawnAt = p.minRespawnAt = Infinity; return; }
      send(p, { t: 'br', k: 'start', ...this.brState() });
      if (B.phase === 'blimp' && now() - B.t0 < BR.late && !blimpDone(B.path, now())) {
        this.brBoard(p);
        this.broadcast({ t: 'br', k: 'board', id: p.id });
        this.brLoadout(p);
        if (this.isleOn) this.isleStart();
      } else {
        p.br = { match: B.id, out: true, late: true, slots: [], melee: null };
        p.alive = false; p.hp = 0; p.respawnAt = p.minRespawnAt = Infinity;
        send(p, { t: 'br', k: 'late' });
        if (this.isleOn) this.isleJoin(p); // (who's who, to watch)
      }
    },
    brLeave(p) {
      if (!this.br || !p.br || p.br.out) return;
      p.br.out = true;
      this.brDropAll(p);
    },

    // ---------------------------------------------------------- loot
    brSpawnLoot() {
      const map = this.map, B = this.br, all = findSpots(map).slice().sort(() => Math.random() - 0.5);
      const bb = map.bounds || [-60, -60, 60, 60], area = (bb[2] - bb[0]) * (bb[3] - bb[1]);
      const want = Math.max(60, Math.min(map.royale.loot || 260, Math.round(area / 220)));
      const chosen = [];
      // indoors first (that's where the good stuff is), then roofs, then the street
      all.sort((s, t) => (t.indoor - s.indoor) + (Math.random() - 0.5) * 1.2);
      for (const s of all) {
        if (chosen.length >= want) break;
        if (outOfBounds(map, s.p)) continue;
        if (chosen.some((c) => Math.abs(c.p[1] - s.p[1]) < 2 && Math.hypot(c.p[0] - s.p[0], c.p[2] - s.p[2]) < BR.spotGap)) continue;
        chosen.push(s);
      }
      B.spots = chosen;
      for (const s of chosen) {
        const poi = poiAt(map, s.p); // districts loot better or worse (Liberal Lane: liberal helpings)
        const q = Math.min(1, (s.indoor ? 0.5 : s.lv > 0 ? 0.45 : 0.15) + s.lv * 0.1 + Math.random() * 0.25 + (poi ? poi.loot : 0));
        const TG = map.boxes.terrain, at = (k) => { const x = s.p[0] + (k ? (Math.random() - 0.5) * 1.6 : 0), z = s.p[2] + (k ? (Math.random() - 0.5) * 1.6 : 0), g = TG ? TG.at(x, z) : null; return [r2(x), r2((g != null && Math.abs(g - s.p[1]) < 0.9 ? g : s.p[1]) + 0.02), r2(z)]; }; // (on shaped ground the second and third item sit on the slope, not at the first one's height)
        const r = Math.random(), big = poi && poi.mod === 'large' ? 2 : 1; // liberal helpings
        if (r < 0.46) {
          const id = wpick(GUNS), l = this.brAddLoot({ k: 'gun', id, tier: rollTier(GUNS[id].tier, q), p: at(0) });
          l.a = ammoFor(id, big);
          if (Math.random() < 0.55) this.brAddLoot({ k: 'ammo', id: 'ammo', p: at(1) });
        } else if (r < 0.52) { const id = wpick(MELEE); this.brAddLoot({ k: 'melee', id, tier: rollTier(MELEE[id].tier, q * 0.5), p: at(0) }); }
        else if (r < 0.66) { const id = wpick(GADGETS); this.brAddLoot({ k: 'gadget', id, tier: GADGETS[id].tier, n: GADGETS[id].n * big, p: at(0) }); }
        else if (r < 0.79) { const id = Math.random() < 0.55 - q * 0.2 ? 'plate' : Math.random() < 0.8 ? 'vest' : 'fridge'; this.brAddLoot({ k: 'armor', id, p: at(0) }); }
        else if (r < 0.92) { const id = Math.random() < 0.72 - q * 0.2 ? 'cola' : 'medkit'; this.brAddLoot({ k: 'heal', id, n: (id === 'cola' ? 2 : 1) * big, p: at(0) }); }
        else this.brAddLoot({ k: 'ammo', id: 'ammo', p: at(0) });
      }
    },
    brAddLoot(o) {
      const B = this.br, l = { i: B.nextLoot++, tier: 0, n: 0, a: null, ...o };
      B.loot.set(l.i, l);
      return l;
    },
    // something new on the floor (dropped / spilled): everyone gets told
    brDrop(p, o) {
      if (!this.br) return null;
      const a = Math.random() * Math.PI * 2, d = 0.4 + Math.random() * 1.1;
      let pos = [p.pos[0] + Math.cos(a) * d, p.pos[1] + 0.6, p.pos[2] + Math.sin(a) * d];
      const h = raycast(pos, [0, -1, 0], 30, this.boxes);
      pos = h ? [pos[0], pos[1] - h.t + 0.02, pos[2]] : [p.pos[0], p.pos[1] + 0.02, p.pos[2]];
      const l = this.brAddLoot({ ...o, p: pos.map(r2), by: p.id, byT: now() });
      this.broadcast({ t: 'br', k: 'loot', l: [this.brLootInfo(l)] });
      return l;
    },
    // died or left: everything in your pockets spills out (the bread too: someone might want a snack)
    brDropAll(p) {
      const s = p.br;
      if (!s || !s.slots) return;
      for (const g of s.slots) if (g) this.brDrop(p, { k: 'gun', id: g.w, tier: g.tier, a: g.ammo });
      if (s.melee && s.melee.w !== BR.melee) this.brDrop(p, { k: 'melee', id: s.melee.w, tier: s.melee.tier });
      if (s.gadget && s.gadget.n > 0) this.brDrop(p, { k: 'gadget', id: s.gadget.i, tier: (GADGETS[s.gadget.i] || {}).tier || 0, n: s.gadget.n });
      if (s.cola) this.brDrop(p, { k: 'heal', id: 'cola', n: s.cola });
      if (s.medkit) this.brDrop(p, { k: 'heal', id: 'medkit', n: s.medkit });
      if (s.slots.some(Boolean) && Math.random() < 0.7) this.brDrop(p, { k: 'ammo', id: 'ammo' });
      s.slots = [null, null]; s.gadget = null; s.cola = 0; s.medkit = 0;
    },
    // pick something up. manual = pressed F (swaps are allowed); auto = walked over it (only free stuff)
    brPick(p, i, manual) {
      const B = this.br, s = p.br, l = B && B.loot.get(i);
      if (!l || !s || s.out || s.inBlimp || !p.alive) return false;
      const reach = BR.pickR + 0.9 + Math.min(3, Math.hypot(p.vel[0], p.vel[2]) * 0.12);
      if (hdist(p.pos, l.p) > reach || l.p[1] - p.pos[1] > 2.4 || p.pos[1] - l.p[1] > 2.2) return false;
      if (!manual && l.by === p.id && now() - l.byT < BR.dropNo * 3) return false;
      let took = true;
      if (l.k === 'gun') {
        const same = s.slots.find((g) => g && g.w === l.id);
        if (same) { // the same gun again: its bullets, and the better of the two
          if (same.ammo != null && l.a != null) same.ammo += l.a;
          if (l.tier > same.tier) same.tier = l.tier;
        } else {
          let k = s.slots.indexOf(null);
          if (k < 0) {
            if (!manual) return false;
            k = p.isBot ? this.brWorstSlot(p) : Math.max(0, s.slots.findIndex((g) => g && g.w === p.w)); // swap the one in your hands (holding the bread: the first); bots drop their worst
            const old = s.slots[k];
            this.brDrop(p, { k: 'gun', id: old.w, tier: old.tier, a: old.ammo });
          }
          s.slots[k] = { w: l.id, tier: l.tier, ammo: l.a };
        }
      } else if (l.k === 'melee') {
        if (!manual) return false;
        if (s.melee && s.melee.w !== BR.melee) this.brDrop(p, { k: 'melee', id: s.melee.w, tier: s.melee.tier });
        s.melee = { w: l.id, tier: l.tier };
      } else if (l.k === 'gadget') {
        if (s.gadget && s.gadget.i === l.id) s.gadget.n = Math.min(6, s.gadget.n + l.n);
        else {
          if (s.gadget && s.gadget.n > 0) { if (!manual) return false; this.brDrop(p, { k: 'gadget', id: s.gadget.i, tier: (GADGETS[s.gadget.i] || {}).tier || 0, n: s.gadget.n }); }
          s.gadget = { i: l.id, n: l.n, next: 0 };
        }
        p.item = l.id; p.ic = s.gadget; this.sendIc(p);
      } else if (l.k === 'ammo') {
        let any = false;
        for (const g of s.slots) if (g && g.ammo != null) { g.ammo += bucketFor(g.w); any = true; }
        took = any;
      } else if (l.k === 'heal') {
        const cap = BR[l.id].n, room = cap - s[l.id];
        if (room <= 0) return false;
        const t = Math.min(room, l.n || 1);
        s[l.id] += t;
        if (t < (l.n || 1)) { l.n -= t; this.broadcast({ t: 'br', k: 'loot', l: [this.brLootInfo(l)] }); this.brLoadout(p); return true; }
      } else if (l.k === 'cell') { // battle island: +20% mech meter (server/islemeter.js)
        if (!this.isleOn || !this.isleCell(p)) return false;
      } else if (l.k === 'armor') {
        if (s.armor >= BR.armor.max) return false;
        s.armor = Math.min(BR.armor.max, s.armor + ARMOR_OF[l.id]);
      }
      if (!took) return false;
      B.loot.delete(i);
      s.picks++; if (l.k === 'gun' && !s.gunT) s.gunT = now();
      this.broadcast({ t: 'br', k: 'take', i, by: p.id });
      this.brLoadout(p);
      return true;
    },
    // your pockets, for your hotbar and HUD (bots don't need telling)
    brLoadout(p) {
      const s = p.br;
      if (p.isBot || !s || s.match !== (this.br && this.br.id)) return;
      if (p.forced) { p.forced = false; send(p, { t: 'loadout', lo: null }); }
      if (!s.slots) return;
      const gHeld = s.gadget && (s.gadget.n > 0 || (ITEMS[s.gadget.i] && ITEMS[s.gadget.i].keep)); // goggles stay with no flashes left
      if (gHeld) { p.item = s.gadget.i; p.ic = s.gadget; }
      send(p, { t: 'brinv', s: s.slots.map((g) => (g ? [g.w, g.tier, g.ammo == null ? -1 : g.ammo] : 0)), m: s.melee ? [s.melee.w, s.melee.tier] : 0, g: gHeld ? [s.gadget.i, s.gadget.n] : 0, c: s.cola, k: s.medkit, ar: Math.round(s.armor), hl: s.heal ? [s.heal.k, Math.max(0, s.heal.until - now())] : 0 });
    },
    // the item key (G) in a royale: whatever gadget you picked up, no recharging
    brIc(p) {
      const s = p.br;
      if (!s || !s.gadget) { const z = { i: p.item, n: 0, next: 0 }; p.ic = z; return z; }
      s.gadget.next = 0;
      p.item = s.gadget.i;
      return s.gadget;
    },
    brHas(p, w) {
      const s = p.br;
      if (!s || !s.slots) return false;
      if (s.melee && s.melee.w === w) return true;
      return s.slots.some((g) => g && g.w === w);
    },
    brTierOf(p, w) {
      const s = p.br;
      if (!s || !s.slots) return 0;
      if (s.melee && s.melee.w === w) return s.melee.tier;
      const g = s.slots.find((x) => x && x.w === w);
      return g ? g.tier : 0;
    },

    // ---------------------------------------------------------- messages (true = handled here)
    brHandle(p, m) {
      const s = p.br;
      if (!this.br || !s) return m.t === 'respawn' || m.t === 'itemsel' || m.t === 'deploy';
      switch (m.t) {
        case 's': if (s.inBlimp) return true; this.brHookSnap(p, m); return false; // riding the blimp: the server knows where you are. otherwise: grapple charges
        case 'brjump': this.brJump(p); return true;
        case 'brpick': if (Number.isInteger(m.i) && now() - (p.brPickT || 0) > 80) { p.brPickT = now(); if (!this.brPick(p, m.i, m.f === 1)) this.brLoadout(p); } return true;
        case 'brkick': this.brKick(p); return true;
        case 'brheal': if (m.k === 'cola' || m.k === 'medkit') this.brHeal(p, m.k); return true;
        case 'brdrop': case 'brswap': if (now() - (p.brInvT || 0) > 120) { p.brInvT = now(); this.brInvAct(p, m); } return true; // the backpack (Tab)
        case 'respawn': case 'itemsel': case 'deploy': return true; // no respawns, items come off the floor, no killstreaks
        case 'fire': case 'hit': case 'push': {
          if (s.inBlimp || s.out) return true;
          if (m.t === 'push' && m.w === 'hook') { if (!this.brHookUse(p)) return true; s.hookPush = now(); return false; } // grabbing a person spends a charge too (none: no tug)
          if (m.t === 'hit' && m.w === 'popper') return false; // the party popper is a gadget (useItem checks it)
          if (typeof m.w !== 'string' || !this.brHas(p, m.w)) return true;
          if (s.heal) { s.heal = null; this.brLoadout(p); } // shooting puts the cola down
          const g = s.slots.find((x) => x && x.w === m.w);
          if (g && g.ammo != null) {
            if (g.ammo <= 0) { if (m.t === 'fire') this.brLoadout(p); return true; }
            if (m.t === 'fire') g.ammo--;
          }
          return false;
        }
      }
      return false;
    },
    // ---------------------------------------------------------- the backpack (Tab): drop things, swap the two gun slots
    // {t:'brswap'} | {t:'brdrop', k: 'gun', i: 0 | 1} | {k: 'melee'} | {k: 'gadget'} | {k: 'cola' | 'medkit', n}
    brInvAct(p, m) {
      const s = p.br;
      if (!s || !s.slots || s.out || s.inBlimp || !p.alive) return;
      if (m.t === 'brswap') { s.slots = [s.slots[1], s.slots[0]]; this.brLoadout(p); return; }
      if (m.k === 'gun' && (m.i === 0 || m.i === 1) && s.slots[m.i]) {
        const g = s.slots[m.i];
        s.slots[m.i] = null;
        this.brDrop(p, { k: 'gun', id: g.w, tier: g.tier, a: g.ammo });
        if (p.w === g.w) p.w = s.melee ? s.melee.w : BR.melee;
      } else if (m.k === 'melee' && s.melee && s.melee.w !== BR.melee) { // (the loaf stays: you need something to hit with)
        this.brDrop(p, { k: 'melee', id: s.melee.w, tier: s.melee.tier });
        if (p.w === s.melee.w) p.w = BR.melee;
        s.melee = { w: BR.melee, tier: 0 };
      } else if (m.k === 'gadget' && s.gadget && s.gadget.n > 0) {
        this.brDrop(p, { k: 'gadget', id: s.gadget.i, tier: (GADGETS[s.gadget.i] || {}).tier || 0, n: s.gadget.n });
        s.gadget = null; p.ic = { i: p.item, n: 0, next: 0 };
      } else if ((m.k === 'cola' || m.k === 'medkit') && s[m.k] > 0) {
        const n = Math.max(1, Math.min(s[m.k], Number.isInteger(m.n) ? m.n : 1));
        s[m.k] -= n;
        if (s.heal && s.heal.k === m.k && s[m.k] <= 0) s.heal = null;
        this.brDrop(p, { k: 'heal', id: m.k, n });
      } else return;
      this.brLoadout(p);
    },
    // ---------------------------------------------------------- grapple charges (BR.hook): the client asks, the server counts
    // a new rope (none before, or the point jumped somewhere else) spends a charge; none left = the rope is cut and the
    // client is told. a person grab (push 'hook') spends it first, so the rope that follows it in the next snapshot is free
    brHookSnap(p, m) {
      const s = p.br, g = m.g;
      if (!p.alive || m.q !== p.seq || !g || !Array.isArray(g) || g.length !== 3 || !g.every(Number.isFinite)) return; // (stale snapshots: the normal path drops them too)
      if (p.g && Math.hypot(p.g[0] - g[0], p.g[1] - g[1], p.g[2] - g[2]) < 6) return; // the same rope
      if (now() - (s.hookPush || 0) < 1500) { s.hookPush = 0; return; } // the rope of a person grab we just paid for
      if (!this.brHookUse(p)) m.g = 0; // cut: everyone sees no rope
    },
    brHookUse(p) {
      const s = p.br, n = now();
      if (!s) return true;
      const h = hookSpend(s.hook, n);
      if (!h) {
        if (!p.isBot && n - (s.hookNoT || 0) > 350) { s.hookNoT = n; send(p, { t: 'br', k: 'hook', h: s.hook, no: 1 }); }
        return false;
      }
      s.hook = h;
      if (!p.isBot) send(p, { t: 'br', k: 'hook', h });
      return true;
    },
    brHookReady(b) { return !b.br || hookCharges(b.br.hook, now()).n >= 1; }, // bots: only grapple with a charge (server.js botThink)
    // jump out of the blimp (it has to be moving)
    brJump(p) {
      const B = this.br, s = p.br;
      if (!B || !s || !s.inBlimp) return;
      const n = now(), bp = blimpAt(B.path, n);
      if (bp[3] <= 0 && !blimpDone(B.path, n)) return;
      s.inBlimp = false; s.fly = 'fall'; s.jumpT = n;
      p.pos = [bp[0], bp[1] - 3, bp[2]]; p.vel = [B.path.d[0] * BR.blimp.speed * 0.5, 0, B.path.d[1] * BR.blimp.speed * 0.5];
      p.spawnT = n; // a moment of grace while you get your bearings
      this.broadcast({ t: 'br', k: 'jump', id: p.id, p: p.pos.map(r2) });
      if (LOG && p.isBot) B.log.push(`${p.name} jumped at ${p.pos[0] | 0},${p.pos[2] | 0}`);
      if (this.isleOn) this.isleJumped(p); // battle island: the squad's bots jump with you
    },
    brHeal(p, k) {
      const s = p.br;
      if (!p.alive || s.inBlimp || s.heal || s[k] <= 0 || p.hp >= BR[k].max) { this.brLoadout(p); return; }
      s.heal = { k, until: now() + BR.healMs[k] };
      this.broadcast({ t: 'br', k: 'heal', id: p.id, h: k, ms: BR.healMs[k] });
      this.brLoadout(p);
    },

    // ---------------------------------------------------------- damage + deaths
    // a better gun hits harder; armour soaks a share until it breaks; the zone ignores armour
    brDamage(t, amt, attacker, w) {
      const ts = t.br;
      if (ts && (ts.inBlimp || ts.out)) return 0;
      if (attacker && attacker !== t && attacker.br) amt *= TIERS[this.brTierOf(attacker, w)].mul;
      const tp = w !== 'zone' && poiAt(this.map, t.pos);
      if (tp && tp.mod === 'numbers' && attacker && attacker !== t) { // Number Works: every hit is a lucky 7 (x0.7) or an unlucky 13 (x1.3)
        const lucky = Math.random() < 0.5; amt *= lucky ? 0.7 : 1.3;
        if (now() - (t.brNumT || 0) > 350) { t.brNumT = now(); this.broadcast({ t: 'br', k: 'num', id: t.id, n: lucky ? 7 : 13 }); }
      }
      if (ts && ts.armor > 0 && w !== 'zone' && w !== 'void') {
        const soak = Math.min(ts.armor, amt * BR.armor.absorb);
        ts.armor -= soak; amt -= soak;
        if (ts.armor <= 0.5) { ts.armor = 0; this.broadcast({ t: 'br', k: 'crack', id: t.id }); }
        if (!t.isBot) send(t, { t: 'brar', ar: Math.round(ts.armor) });
      }
      return amt;
    },
    brKill(t, killer, w) {
      const B = this.br, s = t.br;
      if (!B || !s || s.out) return;
      t.respawnAt = t.minRespawnAt = Infinity;
      if (t.goblin) { this.brGoblinPop(t, killer); return; }
      const n = now(), zn = zoneAt(B.zone, n), kp = killer && killer !== t ? poiAt(this.map, killer.pos) : null;
      if (kp && kp.mod === 'dividend' && killer.br && !killer.br.out) { // Corp Hill: a kill pays a shareholder dividend
        killer.br.armor = Math.min(BR.armor.max, killer.br.armor + 25); this.brLoadout(killer);
        this.broadcast({ t: 'br', k: 'dividend', id: killer.id });
      }
      if (B.leader === t.id && killer && killer !== t) { // the kill leader's bounty: a legendary, right there
        const id = wpick(GUNS); this.brDrop(t, { k: 'gun', id, tier: 4, a: ammoFor(id, 1.5) });
        this.broadcast({ t: 'br', k: 'bounty', id: t.id, by: killer.id });
        B.leader = 0;
      }
      if (!s.mailed && zn && zn.phase <= 1 && !(zn.phase === 1 && zn.shrinking)) { // RETURN TO SENDER: once, before circle 2 closes
        s.mailed = true; s.mailAt = n + 5000; s.heal = null; s.fly = null; t.f &= ~FLAGS.GLIDE;
        if (killer && killer !== t && killer.br) killer.br.kills++;
        this.brDropAll(t); s.armor = 0;
        this.broadcast({ t: 'br', k: 'mail', id: t.id, ms: 5000, by: killer && killer !== t ? killer.id : 0 });
        if (LOG) B.log.push(`${t.name} died to ${killer && killer !== t ? killer.name : w}, RETURNED TO SENDER`);
        return;
      }
      s.out = true; s.heal = null; s.fly = null; t.f &= ~FLAGS.GLIDE;
      const left = this.brAlive().length;
      s.place = this.isleOn ? this.islePlace(t) : left + 1; // (battle island: the squad's place, once it's out)
      B.out.push({ id: t.id, place: s.place });
      if (killer && killer !== t && killer.br) killer.br.kills++;
      const kit = (s.slots || []).filter(Boolean).map((g) => `${TIERS[g.tier].name[0]}-${g.w}(${g.ammo == null ? 'inf' : g.ammo})`).join('+') || 'bread only';
      this.brDropAll(t);
      this.broadcast({ t: 'br', k: 'out', id: t.id, place: s.place, by: killer && killer !== t ? killer.id : 0, w, left });
      if (LOG) {
        const why = w === 'zone' ? 'the zone' : w === 'void' ? (killer ? `${killer.name} (knocked into the void)` : 'the void') : killer && killer !== t ? `${killer.name} with ${w}` : w;
        const hp = killer && killer !== t ? ` (killer had ${Math.round(killer.hp)} hp, ${Math.round(killer.br ? killer.br.armor : 0)} armour)` : '';
        B.log.push(`#${s.place} ${t.name} died to ${why}${hp}, carried ${kit}, ${Math.round(s.armor)} armour, ${s.kills} kills, ${s.picks} pick-ups (first gun ${s.gunT ? Math.round((s.gunT - s.landT) / 1000) + 's after landing' : 'never'}), gave up on ${s.skips}, ${Math.round((now() - B.t0) / 1000)}s in`);
      }
    },
    brAlive() { return this.fighters().filter((p) => p.br && !p.br.out && !p.goblin && p.br.match === this.br.id); },
    // who can a bot see as a target (nobody on the blimp, nobody who's out)
    brTargetable(t) { return !(t.br && (t.br.inBlimp || t.br.out || t.br.mailAt)); },

    // ---------------------------------------------------------- the clock: blimp, zone damage, heals, the winner
    tickBR(n) {
      const B = this.br;
      if (this.brOn && (!B || B.match === undefined && !B.id)) { if (!B) this.startRound(); return; } // switched in without a fresh match (a room that starts in this mode): start one
      if (!B || !this.brOn) return;
      const alive = this.brAlive();
      B.peak = Math.max(B.peak, alive.length); // (late boarders count too)
      // the blimp: riders move with it; at the end of the line everyone still on it gets thrown out
      if (B.phase === 'blimp') {
        const bp = blimpAt(B.path, n), done = blimpDone(B.path, n);
        let riders = 0;
        for (const p of alive) {
          if (!p.br.inBlimp) continue;
          riders++;
          p.pos = [bp[0], bp[1] - 3, bp[2]]; p.vel = [0, 0, 0];
          if (done) { this.brJump(p); if (!p.isBot) send(p, { t: 'br', k: 'eject' }); }
        }
        if (!riders || done) B.phase = 'live';
      }
      // landed? (players say so with their snapshots: on the floor = no umbrella)
      for (const p of alive) if (!p.isBot && p.br.fly && !p.br.inBlimp && n - (p.br.jumpT || 0) > 1500 && !(p.f & FLAGS.GLIDE) && Math.abs(p.vel[1]) < 0.5) p.br.fly = null;
      // heals finishing
      for (const p of alive) {
        const h = p.br.heal;
        if (!h || n < h.until) continue;
        p.br.heal = null;
        if (p.br[h.k] > 0) { p.br[h.k]--; this.heal(p, BR[h.k].heal, BR[h.k].max); this.broadcast({ t: 'fx', k: 'medkit', id: p.id }); }
        this.brLoadout(p);
      }
      // the zone: twice a second, outside = hurt (more every circle)
      if (n - B.zoneT >= 500) {
        B.zoneT = n;
        const zn = zoneAt(B.zone, n);
        for (const p of alive) if (!p.br.inBlimp && outsideZone(zn, p.pos)) {
          this.damage(p, zn.dps * 0.5, null, 'zone');
          if (!p.alive) continue;
          // the eviction notice: the zone shoves you back in, harder every circle
          const dx = zn.c[0] - p.pos[0], dz = zn.c[1] - p.pos[2], l = Math.hypot(dx, dz) || 1, k = 4 + zn.phase * 1.5;
          this.knock(p, [dx / l * k, 2.5, dz / l * k], 'zone');
        }
      }
      if (LOG && process.env.JF_BR_DUMP && n - (B.dumpT || 0) > 8000) { // test knob: what every bot is up to
        B.dumpT = n;
        for (const p of alive) if (p.isBot && p.br.ai) { const ai = p.br.ai, l = B.loot.get(ai.loot); console.log(`[dump] ${p.name}#${p.id} ${p.br.inBlimp ? 'blimp' : p.br.fly || 'ground'} at ${p.pos.map((x) => x | 0)} hp ${p.hp | 0} w ${p.w} target ${p.ai.target || '-'}${p.ai.seenAt ? '(seen)' : ''} loot ${l ? l.id + '@' + l.p.map((x) => x | 0) : '-'} goal ${p.br.ai.why || '?'} picks ${p.br.picks}`); }
      }
      this.tickBRTwists(n);
      if (this.isleOn) { this.tickIsle(n); this.isleWinCheck(n); } // battle island: bleed-outs, revives, last squad standing
      // last one standing (or nobody: the zone got the last two at once)
      const left = this.brAlive();
      if (!this.isleOn && !B.endAt && ((B.peak >= 2 && left.length <= 1) || !left.length || n >= this.round.ends)) {
        B.winner = left.length === 1 ? left[0].id : 0;
        if (left.length === 1) { left[0].br.place = 1; }
        B.endAt = n + 3200;
        this.broadcast({ t: 'br', k: 'win', id: B.winner });
        if (LOG) {
          const w = left[0];
          B.log.push(w ? `WINNER ${w.name}: ${w.br.kills} kills, ${Math.round(w.hp)} hp, ${Math.round(w.br.armor)} armour, kit ${w.br.slots.filter(Boolean).map((g) => `${TIERS[g.tier].name[0]}-${g.w}`).join('+')}, ${Math.round((n - B.t0) / 1000)}s` : 'no winner');
          console.log('[br] ' + B.log.join('\n[br] '));
        }
      }
      if (B.endAt && n >= B.endAt && !this.round.over) { for (const g of [...this.players.values()]) if (g.goblin) this.remove(g); this.endRound(); } // (goblins don't go on the leaderboard)
    },
    // the end screen: by placement (the winner first), then kills
    brSort(list) {
      const place = (p) => (p.br && p.br.place) || (p.br && !p.br.out ? 1 : 999);
      list.sort((a, b) => place(a) - place(b) || b.kills - a.kills);
    },
    brBoardInfo() { return this.fighters().filter((p) => p.br && !p.goblin && p.br.match === (this.br && this.br.id)).map((p) => [p.id, p.br.place || (p.br.out ? 0 : 1), p.br.kills || 0]); },

    // ---------------------------------------------------------- bots: drop, glide, loot, rotate, heal, pick the gun for the range
    // (the fighting itself is botThink's; these steer it)
    brBotStep(b, dt) {
      const s = b.br;
      if (!s || s.out) return false;
      const n = now();
      if (b.goblin) { this.brGoblinStep(b, dt); return true; }
      const gp = poiAt(this.map, b.pos); b.gravMul = gp && gp.mod === 'lowgrav' ? 0.4 : 1;
      if (!s.ai) s.ai = this.brBotBrain(b);
      if (s.inBlimp) {
        // jump when the blimp is about as close to where you want to land as it gets
        const B = this.br, bp = blimpAt(B.path, n), d = hdist(bp, s.ai.drop);
        if (bp[3] > 0 && (d < s.ai.jumpR || (s.ai.lastD != null && d > s.ai.lastD + 0.05 && d < 160))) this.brJump(b);
        s.ai.lastD = d;
        return true;
      }
      if (s.fly) { this.brBotFly(b, dt); return true; }
      return false;
    },
    brBotBrain(b) {
      // where to land: a busy area for the brave, a quiet one for the rest (bots spread over the map)
      const B = this.br, spots = B.spots || [], cells = new Map();
      for (const l of B.loot.values()) {
        const k = Math.floor(l.p[0] / 30) + ',' + Math.floor(l.p[2] / 30), c = cells.get(k) || { v: 0, p: l.p, n: 0, taken: 0 };
        c.v += l.k === 'gun' ? 2 + l.tier : 1; c.n++;
        if (onGround(this.map, l.p) && !raycast([l.p[0], l.p[1] + 0.3, l.p[2]], [0, 1, 0], 80, this.boxes)) c.p = l.p; // land on open ground in that area (not on the roof over it)
        cells.set(k, c);
      }
      for (const o of this.fighters()) if (o !== b && o.br && o.br.ai && o.br.ai.cell) { const c = cells.get(o.br.ai.cell); if (c) c.taken++; }
      const aggro = Math.random();
      let best = null, bv = -1e9;
      for (const [k, c] of cells) {
        if (outOfBounds(this.map, c.p) || !onGround(this.map, c.p)) continue; // (the island: land, not the sea)
        const v = (c.v * (aggro > 0.8 ? 1.5 : 1)) / Math.pow(1 + c.taken * (aggro > 0.8 ? 0.4 : 2.5), 2) + Math.random() * 4; // the brave go where the loot is; the rest go where the people aren't
        if (v > bv) { bv = v; best = [k, c]; }
      }
      let drop = best ? best[1].p.slice() : (spots[0] ? spots[0].p.slice() : [0, 0, 0]);
      const pads = (this.map.royale && this.map.royale.drops) || [];
      if (pads.length && (!best || Math.random() < 0.5)) { const d = pick(pads); drop = [d[0], d[1], d[2]]; } // a map's drop pads (the island: always land)
      if (LOG) B.log.push(`${b.name} wants to land at ${drop[0] | 0},${drop[2] | 0} (${aggro > 0.75 ? 'hot drop' : 'quiet'})`);
      return { drop, cell: best ? best[0] : null, aggro, cautious: Math.random(), jumpR: 25 + Math.random() * 25, lastD: null, loot: 0, lootT: 0, skip: new Map(), roam: null, roamT: 0, pickT: 0, healT: 0, wT: 0 };
    },
    // falling, then the umbrella: steer at the drop spot
    brBotFly(b, dt) {
      const s = b.br, ai = s.ai, v = b.vel;
      const tx = ai.drop[0] - b.pos[0], tz = ai.drop[2] - b.pos[2], tl = Math.hypot(tx, tz) || 1;
      const below = raycast([b.pos[0], b.pos[1], b.pos[2]], [0, -1, 0], 200, this.boxes), hgt = below ? below.t : 200;
      if (s.fly === 'fall' && hgt < BR.fall.open) s.fly = 'glide';
      const sp = s.fly === 'glide' ? BR.glide.speed : BR.fall.steer, want = Math.min(sp, tl * 1.5);
      v[0] += (tx / tl * want - v[0]) * Math.min(1, dt * 3); v[2] += (tz / tl * want - v[2]) * Math.min(1, dt * 3);
      if (s.fly === 'glide') v[1] += (-BR.glide.vy - v[1]) * Math.min(1, dt * 4);
      else v[1] = Math.max(-BR.fall.vMax, v[1] - 26 * dt);
      b.yaw = Math.atan2(-tx, -tz);
      const moved = this.brMove(b, dt);
      b.f = s.fly === 'glide' ? FLAGS.GLIDE : 0;
      if (moved && b.onGround) { s.fly = null; b.f = 0; s.landT = now(); if (LOG) this.br.log.push(`${b.name} landed ${Math.round(tl)} m from where it wanted`); }
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    },
    brMove(b, dt) { const res = H.movePlayer(b.pos, b.vel, dt, this.boxes, false); b.onGround = !!res.ground && b.vel[1] <= 0.01; return true; },

    // what a bot wants right now (botGoal): out of the zone, heal up, loot, or move with the circle
    brBotGoal(b) {
      const s = b.br;
      if (!s || s.out || s.inBlimp || s.fly || !s.ai) return null;
      const ai = s.ai, n = now(), B = this.br;
      const zn = zoneAt(B.zone, n);
      // stuck (behind a barrier, on a deck, in a corner): hop and try somewhere else for a few seconds
      if (!ai.stP || hdist(ai.stP, b.pos) > 1.5) { ai.stP = b.pos.slice(); ai.stT = n; }
      else if (n - ai.stT > 3000 && !(b.ai.target && b.ai.seenAt)) {
        const a = Math.random() * Math.PI * 2;
        ai.unstuck = { p: [b.pos[0] + Math.cos(a) * 12, b.pos[1], b.pos[2] + Math.sin(a) * 12], until: n + 2500 };
        ai.stT = n; ai.loot = 0; ai.lootT = n + 2500; ai.roam = null;
      }
      if (ai.unstuck && n < ai.unstuck.until) { b.ai.navJump = Math.random() < 0.3; ai.why = 'unstuck'; return { p: ai.unstuck.p, force: true, r: 0 }; }
      const t = this.players.get(b.ai.target), fighting = t && t.alive && b.ai.seenAt;
      // 1. the zone: outside (or about to be) = go, even mid-fight
      const dc = Math.hypot(b.pos[0] - zn.c[0], b.pos[2] - zn.c[1]);
      if (dc > zn.r - 3) { ai.why = 'zone'; return { p: this.brInward(b, zn.c, zn.r), force: true, r: 0 }; }
      // rotate ahead of the circle: once the next one is known and the wait is running out
      const nx = zn.next;
      if (nx) {
        // how long the walk in takes (bots walk ~7 m/s with the odd detour), plus a margin: leave when that's all that's left
        const dn = Math.hypot(b.pos[0] - nx.c[0], b.pos[2] - nx.c[1]), walk = Math.max(0, dn - nx.r * 0.75) / 6.5 + 8 + ai.cautious * 10;
        const soon = (zn.shrinking && dn > nx.r * 0.9) || zn.left < walk * 1000;
        if (soon && dn > nx.r * 0.75) {
          ai.why = 'rotate';
          const l = this.brBotLoot(b, 10); // grab what's right on the way
          if (l && zn.left > (walk + 6) * 1000) { const it = B.loot.get(l); if (hdist(b.pos, it.p) < BR.pickR) this.brPick(b, l, true); else return { p: it.p.slice(), force: false, r: 0 }; }
          return { p: this.brInward(b, nx.c, nx.r * 0.7), force: zn.shrinking && dc > zn.r * 0.8, r: 0 };
        }
      }
      // gadgets: throw the frag / duck at whoever it's fighting; smoke, bubble or reverse card when it's losing
      if (fighting && s.gadget && s.gadget.n > 0 && n > (ai.gadT || 0)) this.brBotGadget(b, t, n);
      // 2. heal when it's quiet
      const need = 100 - b.hp;
      if (!fighting && !s.heal && need > 20 && (s.cola || s.medkit) && n > ai.healT) {
        ai.healT = n + 1500;
        this.brHeal(b, need > 45 && s.medkit ? 'medkit' : s.cola ? 'cola' : 'medkit');
      }
      if (s.heal) return fighting ? null : { p: b.pos, force: true, r: 0 };
      // 3. loot: the best thing nearby that's actually an upgrade (no gun yet: a gun, now)
      if (n > ai.lootT) { ai.lootT = n + 450; ai.loot = this.brBotLoot(b); }
      const l = ai.loot && B.loot.get(ai.loot);
      const unarmed = !s.slots.some(Boolean);
      if (l) {
        const d = hdist(b.pos, l.p);
        if (d < BR.pickR && Math.abs(l.p[1] - b.pos[1]) < 1.6) {
          if (!this.brPick(b, l.i, true)) { ai.skip.set(l.i, n + 60000); s.skips++; }
          ai.loot = 0; ai.lootT = 0;
          return null;
        }
        if (!ai.lootSince || ai.lootFor !== l.i) { ai.lootFor = l.i; ai.lootSince = n; }
        if (n - ai.lootSince > 9000) { ai.skip.set(l.i, n + 60000); ai.loot = 0; s.skips++; } // can't get there: forget it
        ai.why = 'loot'; if (!fighting || (unarmed && l.k === 'gun' && !(t && dist3(t.pos, b.pos) < 4))) return { p: [l.p[0], l.p[1], l.p[2]], force: !!fighting, r: 0 };
      }
      // stuck up on a roof with nothing to grab: walk off it (a short drop doesn't hurt)
      if (b.pos[1] > 2.5 && !l) { ai.why = 'off roof'; if (!ai.roofGo || n > ai.roofT) { ai.roofGo = this.brInward(b, [b.pos[0], b.pos[2]], 40, true); ai.roofT = n + 6000; } b.ai.navJump = Math.random() < 0.15; return { p: ai.roofGo, force: true, r: 0 }; } // hop the parapet
      // 4. nothing to do: drift toward the middle of the (next) circle, somewhere new now and then
      if (!ai.roam || n > ai.roamT || hdist(b.pos, ai.roam) < 4) {
        const c = nx ? nx.c : zn.c, r = nx ? nx.r : zn.r;
        const a = Math.random() * Math.PI * 2, d = Math.random() * r * 0.6;
        ai.roam = this.brInward(b, [c[0] + Math.cos(a) * d, c[1] + Math.sin(a) * d], 1);
        ai.roamT = n + 12000 + Math.random() * 8000;
      }
      ai.why = fighting ? 'fight' : 'roam';
      return fighting ? null : { p: ai.roam, force: false, r: 0 };
    },
    // a walkable point near (x, z) inside a circle of radius r round c (bots aim for ground spots)
    brInward(b, c, r, open = false) {
      // ground spots in a 16 m grid (once per map): look in the cells the circle covers, keep the one nearest the bot
      const map = this.map;
      if (!map._brGrid) { const G = new Map(); for (const sp of groundSpots(map)) { const k = Math.floor(sp.p[0] / 16) + ',' + Math.floor(sp.p[2] / 16); if (!G.has(k)) G.set(k, []); G.get(k).push(sp); } map._brGrid = G; }
      const R = Math.max(2, r), i0 = Math.floor((c[0] - R) / 16), i1 = Math.floor((c[0] + R) / 16), j0 = Math.floor((c[1] - R) / 16), j1 = Math.floor((c[1] + R) / 16);
      let best = null, bd = 1e9, seen = 0;
      for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
        const list = map._brGrid.get(i + ',' + j);
        if (!list) continue;
        for (let q = 0; q < list.length; q += 1 + (list.length > 12 ? 2 : 0)) { // (a sample of busy cells)
          const sp = list[q];
          if (open && sp.indoor) continue;
          if (Math.hypot(sp.p[0] - c[0], sp.p[2] - c[1]) > R) continue;
          const d = hdist(sp.p, b.pos) + Math.random() * 6; seen++;
          if (d < bd) { bd = d; best = sp.p; }
        }
      }
      return best ? best.slice() : [c[0], 0, c[1]];
    },
    // how much a bot wants a floor item (0 = not at all)
    brBotWant(b, l) {
      const s = b.br;
      if (l.k === 'gun') {
        const same = s.slots.find((g) => g && g.w === l.id);
        if (same) return l.tier > same.tier ? 3 : same.ammo != null && same.ammo < 30 ? 1.5 : 0;
        if (s.slots.includes(null)) return 4 + l.tier + (GUNS[l.id] ? GUNS[l.id].tier : 0);
        const worst = Math.min(...s.slots.map((g) => g.tier + (GUNS[g.w] ? GUNS[g.w].tier : 0) + (g.ammo === 0 ? -9 : 0))); // (brWorstSlot is the one that goes)
        const v = l.tier + (GUNS[l.id] ? GUNS[l.id].tier : 0);
        return v > worst + 0.5 ? 2 + v - worst : 0;
      }
      if (l.k === 'armor') return s.armor < BR.armor.max - 10 ? 2 + ARMOR_OF[l.id] / 25 : 0;
      if (l.k === 'heal') return s[l.id] < BR[l.id].n ? (b.hp < 70 ? 4 : 1.5) : 0;
      if (l.k === 'ammo') return s.slots.some((g) => g && g.ammo != null && g.ammo < ammoFor(g.w)) ? 1.6 : 0;
      if (l.k === 'gadget') return !s.gadget || s.gadget.n <= 0 ? 1.2 : s.gadget.i === l.id ? 0.6 : 0;
      if (l.k === 'melee') return s.melee.w === BR.melee ? 1 + l.tier : MELEE[l.id] && l.tier > s.melee.tier ? 1 : 0;
      if (l.k === 'cell') return this.isleOn ? this.isleCellWant(b) : 0; // battle island: energy cells
      return 0;
    },
    brBotLoot(b, range = 45) {
      const B = this.br, ai = b.br.ai, n = now(), zn = zoneAt(B.zone, n);
      let best = 0, bv = 0;
      for (const l of B.loot.values()) {
        const d = hdist(b.pos, l.p);
        if (d > (l.crate ? Math.max(range, 110) : range) || Math.abs(l.p[1] - b.pos[1]) > 1.8 || (ai.skip.get(l.i) || 0) > n) continue;
        if (l.by === b.id && n - l.byT < 45000) continue; // what it just put down
        if (outsideZone(zn, l.p)) continue;
        const w = this.brBotWant(b, l);
        if (w <= 0) continue;
        const v = w / (d + 6);
        if (v > bv) { bv = v; best = l.i; }
      }
      return best;
    },
    // the right gun for the range (and one with bullets), every few hundred ms
    brBotWeapon(b, dist) {
      const s = b.br;
      if (!s || !s.slots || s.inBlimp || s.out) return;
      const n = now();
      if (n < (s.ai ? s.ai.wT : 0)) return;
      if (s.ai) s.ai.wT = n + 350;
      const fit = (id) => {
        const close = { shotgun: 3, marbles: 3, shredder: 3, smg: 2.4, minigun: 2.2, redline: 1.6, cig: 2.5, blower: 2, banana: 1.4, cards: 1.4, snowball: 1.2, bloodcross: 2, revolver: 1.5, ar: 1.6, bow: 0.8, chicken: 1, bowling: 1.4, sniper: 0.4 };
        const mid = { ar: 3, redline: 2.8, smg: 2.2, minigun: 2.6, revolver: 2.4, chicken: 2.3, bow: 2, bowling: 1.6, banana: 1.8, cards: 1.6, snowball: 1.4, bloodcross: 1.8, sniper: 1.8, shotgun: 1, marbles: 0.6 };
        const far = { sniper: 3, ar: 2.2, revolver: 2, bow: 1.8, redline: 1.6, minigun: 1.2, chicken: 1.2, smg: 0.9 };
        const tbl = dist < 9 ? close : dist < 32 ? mid : far;
        return tbl[id] || 0.3;
      };
      let best = s.melee ? s.melee.w : BR.melee, bv = dist < 3.5 ? 2.2 : 0.2;
      for (const g of s.slots) {
        if (!g || (g.ammo != null && g.ammo <= 0)) continue;
        if ((WEAPONS[g.w].kind === 'cone' && g.w !== 'shredder') || WEAPONS[g.w].kind === 'beam') continue; // bots can't work a cig, a leaf blower or the laser
        const v = fit(g.w) * TIERS[g.tier].mul;
        if (v > bv) { bv = v; best = g.w; }
      }
      if (b.w !== best) { b.w = best; b.ai.ammo = Math.min(WEAPONS[best].mag || 1, this.brAmmo(b, best)); b.ai.nextShot = Math.max(b.ai.nextShot, n + 350); b.ai.reloadUntil = 0; }
    },
    brWorstSlot(b) {
      const v = (g) => g.tier + (GUNS[g.w] ? GUNS[g.w].tier : 0) + (g.ammo === 0 ? -9 : 0);
      const s = b.br.slots;
      return v(s[0]) <= v(s[1]) ? 0 : 1;
    },
    brBotGadget(b, t, n) {
      const g = b.br.gadget, ai = b.br.ai, d = dist3(t.pos, b.pos);
      const hurtNow = b.lastAttackT && n - b.lastAttackT < 1500, low = b.hp + b.br.armor < 60;
      const attack = { frag: [7, 28], duck: [8, 30], wand: [3, 14] }[g.i]; // (no party popper: its hits come from a client)
      const guard = g.i === 'smoke' || g.i === 'bubble' || g.i === 'reverse';
      if (attack ? d < attack[0] || d > attack[1] : !(guard && low && hurtNow)) return;
      ai.gadT = n + 3500 + Math.random() * 2500;
      const e = [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], to = guard ? [b.pos[0], b.pos[1], b.pos[2]] : [t.pos[0], t.pos[1] + 1, t.pos[2]];
      const dx = to[0] - e[0], dz = to[2] - e[2], hd = Math.hypot(dx, dz) || 1;
      const up = g.i === 'frag' || g.i === 'duck' ? Math.min(0.6, hd / 45) : 0; // lob it
      const dir = guard ? [0, -1, 0] : [dx / hd, (to[1] - e[1]) / hd + up, dz / hd];
      const l = Math.hypot(...dir);
      b.item = g.i;
      this.useItem(b, { i: g.i, o: e, d: dir.map((x) => x / l) });
      if (LOG) this.br.log.push(`${b.name} used ${g.i} (${guard ? 'saving itself' : `at ${t.name}, ${d | 0} m`})`);
    },
    // a drop ahead (no floor within 15 m, 2.5 or 5 m out): don't jump, turn round; in the air, steer back to the last floor
    brBotEdge(b, wx, wz, jump) {
      if (!wx && !wz) return [wx, wz, jump];
      const deep = (d) => !raycast([b.pos[0] + wx * d, b.pos[1] + 0.5, b.pos[2] + wz * d], [0, -1, 0], 15, this.boxes) || !!pitUnder(this.map, b.pos[0] + wx * d, b.pos[1] + 0.5, b.pos[2] + wz * d); // (a lava pit counts: it has a floor, it's still a drop)
      if (!deep(2.5) && !deep(5)) return [wx, wz, jump];
      if (!b.onGround && b.ground) { const dx = b.ground[0] - b.pos[0], dz = b.ground[2] - b.pos[2], l = Math.hypot(dx, dz) || 1; return [dx / l, dz / l, false]; }
      if (deep(2.5)) return [-wx, -wz, false];
      return [wx, wz, false];
    },
    brAmmo(b, w) { const g = b.br && b.br.slots.find((x) => x && x.w === w); return g && g.ammo != null ? g.ammo : 1e9; },
    // a bot's shot spends a real bullet (false = that gun's empty: swap)
    brBotShot(b) {
      const g = b.br && b.br.slots && b.br.slots.find((x) => x && x.w === b.w);
      if (!g) return b.br && b.br.melee && b.br.melee.w === b.w;
      if (g.ammo == null) return true;
      if (g.ammo <= 0) { if (b.br.ai) b.br.ai.wT = 0; return false; }
      g.ammo--;
      if (b.br.heal) b.br.heal = null;
      return true;
    },
    // third-partying and picking fights: weak bots leave far-off people alone, everyone likes a target that's already hurt
    brBotScore(b, t, score) {
      const s = b.br;
      if (!s || !t.br) return score;
      const mine = b.hp + (s.armor || 0), theirs = t.hp + (t.br.armor || 0), d = Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]);
      if (mine < 55 && d > 18) return 1e9; // hurt: not looking for trouble
      const hitMe = b.lastAttacker === t.id && now() - (b.lastAttackT || 0) < 2500;
      if (s.slots && !s.slots.some(Boolean) && d > 5 && !hitMe) return 1e9; // bread only: go find a gun first (unless they're on you)
      if (s.ai && s.ai.cautious > 0.55 && d > 30 && !hitMe && theirs > 60) return 1e9; // careful ones don't start long-range fights
      if (t.goblin) return d < 25 ? score * 1.2 : 1e9; // a loot goblin up close: pop it
      if (this.br && this.br.leader === t.id && d < 70) score *= 0.6; // the bounty
      if (now() - (t.lastAttackT || 0) < 3000 && t.lastAttacker !== b.id) score *= 0.55; // someone's already shooting them: help finish the job
      return score * (0.6 + theirs / 250);
    },

    // ---------------------------------------------------------- the twists: return to sender, the bounty, supply drops, loot goblins
    tickBRTwists(n) {
      const B = this.br, t = n - B.t0, zn = zoneAt(B.zone, n);
      // mailed back: five seconds after dying you fall out of the sky in a box, somewhere in the next circle
      for (const p of this.fighters()) {
        const s = p.br;
        if (!s || !s.mailAt || n < s.mailAt || s.match !== B.id) continue;
        s.mailAt = 0; s.out = false; s.slots = [null, null]; s.melee = { w: BR.melee, tier: 0 }; s.gadget = null; s.armor = 0; s.inBlimp = false; s.fly = 'fall'; s.jumpT = n;
        const c = zn.next || zn, at = this.brInward(p, c.c, Math.max(8, c.r * 0.7));
        p.alive = true; p.hp = 100; p.pos = [at[0], (this.map.royale.blimpY || 120) * 0.7, at[2]]; p.vel = [0, -4, 0]; p.spawnT = n; p.seq++; p.w = BR.melee;
        this.resetLife(p);
        if (p.isBot) { s.ai = this.brBotBrain(p); s.ai.drop = at; } else { H.send(p, { t: 'spawn', p: p.pos, q: p.seq }); }
        this.broadcast({ t: 'br', k: 'mailed', id: p.id, p: p.pos });
        this.brLoadout(p);
      }
      // the kill leader (2+ kills): everyone sees where they are
      if (n - (B.leaderT || 0) > 1000) {
        B.leaderT = n;
        let top = null;
        for (const p of this.brAlive()) if ((p.br.kills || 0) >= 2 && (!top || p.br.kills > top.br.kills)) top = p;
        const id = top ? top.id : 0;
        if (id !== B.leader) { B.leader = id; this.broadcast({ t: 'br', k: 'leader', id, n: top ? top.br.kills : 0 }); }
      }
      // supply blimp drops: a crate on an umbrella over the next circle; grab it in the air or wait for it to land
      if (B.drops.length && t >= B.drops[0] && zn) {
        B.drops.shift();
        const c = zn.next || zn, at = this.brInward({ pos: [c.c[0], 0, c.c[1]] }, c.c, Math.max(6, c.r * 0.6));
        const y0 = 120, h = raycast([at[0], y0, at[2]], [0, -1, 0], 200, this.boxes), land = h ? y0 - h.t : 0;
        const cr = { id: B.nextCrate++, x: at[0], z: at[2], y0, land, v: 5, t0: n, open: false };
        B.crates.push(cr);
        this.broadcast({ t: 'br', k: 'crate', c: this.brCrateInfo(cr) });
      }
      for (const cr of B.crates) {
        if (cr.open) continue;
        const y = Math.max(cr.land, cr.y0 - cr.v * (n - cr.t0) / 1000), p = [cr.x, y, cr.z];
        const grab = this.brAlive().find((q) => !q.br.inBlimp && hdist(q.pos, p) < 2.6 && Math.abs(q.pos[1] + 0.9 - p[1]) < 2.6);
        if (grab || y <= cr.land) this.brCrateOpen(cr, grab, p);
      }
      // loot goblins: a vending machine on legs, full of epics, running away from everyone
      if (B.goblins.length && t >= B.goblins[0]) { B.goblins.shift(); this.brGoblinSpawn(); }
    },
    brCrateInfo(c) { return [c.id, r2(c.x), r2(c.z), c.y0, r2(c.land), c.v, c.t0]; },
    brCrateOpen(cr, by, p) {
      cr.open = true;
      const who = by || { id: 0, pos: [p[0], p[1] - 0.9, p[2]] };
      const gun = wpick(GUNS), gun2 = wpick(GUNS);
      for (const o of [{ k: 'gun', id: gun, tier: 4, a: ammoFor(gun, 2) }, { k: 'gun', id: gun2, tier: 3, a: ammoFor(gun2, 2) }, { k: 'armor', id: 'fridge' }, { k: 'heal', id: 'medkit', n: 2 }, { k: 'ammo', id: 'ammo' }]) {
        const l = this.brDrop(who, o); if (l) { l.crate = true; l.by = 0; }
      }
      this.broadcast({ t: 'br', k: 'crateopen', id: cr.id, by: by ? by.id : 0 });
      if (LOG) this.br.log.push(`supply crate ${by ? 'grabbed mid-air by ' + by.name : 'landed'}`);
    },
    brGoblinSpawn() {
      const B = this.br, zn = zoneAt(B.zone, now()), c = zn.next || zn;
      const at = this.brInward({ pos: [c.c[0], 0, c.c[1]] }, c.c, Math.max(10, c.r * 0.8));
      const g = this.newPlayer('LOOT GOBLIN', { isBot: true, pos: [at[0], at[1] + 0.2, at[2]], color: '#39ff14', w: 'bread', skins: {}, ai: { diff: 'normal', target: 0, retarget: 0, nextShot: Infinity, seenAt: 0, ammo: 1, reloadUntil: 0, jumpT: 0, wp: null, seed: 0, dummy: null, strafeDir: 1 } });
      g.goblin = true; g.hp = 250; g.team = 0;
      g.br = { match: B.id, slots: [null, null], melee: { w: BR.melee, tier: 0 }, gadget: null, cola: 0, medkit: 0, armor: 0, inBlimp: false, fly: null, out: false, place: 0, heal: null, ai: null, kills: 0, picks: 0, goblin: true };
      this.players.set(g.id, g);
      this.broadcast({ t: 'pj', ...this.info(g) });
      this.broadcast({ t: 'br', k: 'goblin', id: g.id });
      if (LOG) B.log.push(`a loot goblin appeared at ${at[0] | 0},${at[2] | 0}`);
    },
    // run from whoever's closest (through the walk graph), hop now and then; wander when nobody's around
    brGoblinStep(g, dt) {
      const n = now(), ai = g.ai;
      let near = null, nd = 40;
      for (const p of this.brAlive()) { const d = hdist(p.pos, g.pos); if (d < nd) { nd = d; near = p; } }
      if (near && (!ai.flee || n > ai.fleeT || hdist(g.pos, ai.flee) < 3)) {
        const dx = g.pos[0] - near.pos[0], dz = g.pos[2] - near.pos[2], l = Math.hypot(dx, dz) || 1;
        ai.flee = this.brInward(g, [g.pos[0] + dx / l * 30, g.pos[2] + dz / l * 30], 14); ai.fleeT = n + 2500;
      } else if (!near && (!ai.flee || n > ai.fleeT)) { ai.flee = this.brInward(g, [g.pos[0], g.pos[2]], 25); ai.fleeT = n + 6000; }
      let wx = 0, wz = 0;
      if (ai.flee) {
        const st = this.map.graph && navSteer(this.map.graph, ai.nav || (ai.nav = {}), g.pos, ai.flee, n);
        if (st) { wx = st[0]; wz = st[1]; } else { const dx = ai.flee[0] - g.pos[0], dz = ai.flee[2] - g.pos[2], l = Math.hypot(dx, dz) || 1; wx = dx / l; wz = dz / l; }
      }
      const v = g.vel, sp = near ? 9.5 : 4;
      if (g.onGround) { v[0] += (wx * sp - v[0]) * Math.min(1, dt * 8); v[2] += (wz * sp - v[2]) * Math.min(1, dt * 8); if (near && Math.random() < dt * 1.2) v[1] = 8; }
      v[1] -= 26 * dt;
      if (wx || wz) g.yaw = Math.atan2(-wx, -wz);
      this.brMove(g, dt);
      if (g.pos[1] < this.map.killY) this.kill(g, null, 'void');
    },
    brGoblinPop(g, killer) {
      g.br.out = true;
      for (let i = 0; i < 4; i++) { const id = wpick(GUNS); const l = this.brDrop(g, i < 3 ? { k: 'gun', id, tier: 3 + (Math.random() < 0.35 ? 1 : 0), a: ammoFor(id, 1.5) } : { k: 'gadget', id: wpick(GADGETS), tier: 3, n: 2 }); if (l) l.by = 0; }
      this.brDrop(g, { k: 'armor', id: 'vest' });
      this.broadcast({ t: 'br', k: 'goblinpop', id: g.id, by: killer && killer !== g ? killer.id : 0 });
      setTimeout(() => { if (this.players.get(g.id) === g) this.remove(g); }, 1500);
      if (LOG) this.br.log.push(`loot goblin popped by ${killer && killer !== g ? killer.name : 'nobody'}`);
    },
    // Neon Market: kick a vending machine (F next to it), get a gadget. each machine pays out once a minute
    brKick(p) {
      const B = this.br, ms = this.map.vending || [];
      if (!p.alive || p.br.inBlimp || p.br.out) return;
      let best = -1, bd = 2.4;
      ms.forEach((m, i) => { const d = Math.hypot(m[0] - p.pos[0], m[1] - p.pos[2]); if (d < bd) { bd = d; best = i; } });
      if (best < 0) return;
      const n = now();
      if (n < (B.vend.get(best) || 0)) { H.send(p, { t: 'br', k: 'kick', ok: 0, i: best }); return; }
      B.vend.set(best, n + 60000);
      const id = wpick(GADGETS), l = this.brDrop(p, { k: 'gadget', id, tier: GADGETS[id].tier, n: GADGETS[id].n });
      if (l) l.by = 0;
      this.broadcast({ t: 'br', k: 'kick', ok: 1, i: best, id: p.id });
    },
  });
}
