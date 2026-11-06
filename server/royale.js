// Jank Royale on the server: the blimp, the drop, loot on the floor, inventories, armour, the zone, placements, and
// the bots that play it. Installed onto Room (server.js) like the other add-on modes: everything here is a Room method,
// and server.js only calls a handful of small hooks (see `brOn` in server.js).
// The server owns all of it: what's on the floor, who holds what, how many bullets are left, armour, the zone's damage.
import { GAMES } from '../shared/modes.js';
import { WEAPONS, ITEMS, BOT_DIFF, FLAGS } from '../shared/weapons.js';
import { raycast, PH } from '../shared/physics.js';
import { outOfBounds } from '../shared/bounds.js';
import { BR, ZONE, TIERS, GUNS, MELEE, GADGETS, STUFF, ARMOR_OF, ammoFor, bucketFor, blimpAt, blimpDone, zoneAt, outsideZone } from '../shared/royale.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const pick = (a) => a[(Math.random() * a.length) | 0];
const hdist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
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
    for (let lv = 0; lv < 5; lv++) {
      const h = raycast([px, top, pz], [0, -1, 0], top - map.killY, boxes);
      if (!h || h.axis !== 1) break;
      const y = top - h.t;
      if (y < map.killY + 2) break;
      const box = h.box;
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
  return (map._brGround = findSpots(map).filter((s) => s.p[1] < 1.6 && !outOfBounds(map, s.p)));
}

// a tier for a find: its base tier, plus luck (better spots roll higher)
function rollTier(base, q) {
  let t = base;
  while (t < 4 && Math.random() < 0.22 + q * 0.28) t++;
  return t;
}

export function installRoyale(Room, H) {
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
      const zone = { t0: n, c0: [z0[0], z0[1]], r0: z0[2], steps };
      const end = steps.reduce((t, s) => t + (s.wait + s.shrink) * 1000, n) + 90000;
      this.br = { id: n, phase: 'blimp', path, zone, t0: n, peak: 0, winner: 0, endAt: 0, out: [], zoneT: n, loot: new Map(), nextLoot: 1, log: [] };
      if (this.round) { this.round.target = 0; this.round.ends = end; }
      this.brSpawnLoot();
      const list = this.fighters();
      for (const p of list) this.brBoard(p);
      this.br.peak = list.length;
      this.broadcast({ t: 'br', k: 'start', ...this.brState() });
      for (const p of list) this.brLoadout(p);
      if (LOG) console.log(`[br] start on ${map.name}: ${list.length} in the blimp, ${this.br.loot.size} loot`);
    },
    brClear() {
      this.br = null;
      for (const p of this.players.values()) { p.br = null; p.f &= ~FLAGS.GLIDE; }
      this.broadcast({ t: 'br', k: 'off' });
      if (this.mode === 'bots') this.fillBots();
    },
    brState() {
      const B = this.br;
      return {
        path: B.path, zone: B.zone, phase: B.phase, at: now(),
        loot: [...B.loot.values()].map((l) => this.brLootInfo(l)),
        blimp: this.fighters().filter((p) => p.br && p.br.inBlimp).map((p) => p.id),
        out: B.out.map((o) => [o.id, o.place]),
      };
    },
    brLootInfo(l) { return [l.i, l.k, l.id, l.tier || 0, l.n || 0, l.a == null ? -1 : l.a, l.p[0], l.p[1], l.p[2]]; },
    // on board: fresh pockets (a loaf of bread), full HP, riding along
    brBoard(p) {
      p.br = { match: this.br.id, slots: [null, null], melee: { w: BR.melee, tier: 0 }, gadget: null, cola: 0, medkit: 0, armor: 0, inBlimp: true, fly: null, out: false, place: 0, heal: null, ai: null, kills: 0 };
      p.alive = true; p.hp = 100; p.vel = [0, 0, 0]; p.healLeft = 0;
      p.respawnAt = 0;
      const bp = blimpAt(this.br.path, now());
      p.pos = [bp[0], bp[1] - 3, bp[2]];
      p.w = BR.melee;
      if (p.isBot) { p.ai.ammo = 1; p.ai.reloadUntil = 0; p.ai.hook = null; p.g = null; }
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
      } else {
        p.br = { match: B.id, out: true, late: true, slots: [], melee: null };
        p.alive = false; p.hp = 0; p.respawnAt = p.minRespawnAt = Infinity;
        send(p, { t: 'br', k: 'late' });
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
      const want = Math.max(60, Math.min(260, Math.round(area / 220)));
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
        const q = Math.min(1, (s.indoor ? 0.5 : s.lv > 0 ? 0.45 : 0.15) + s.lv * 0.1 + Math.random() * 0.25);
        const at = (k) => [r2(s.p[0] + (k ? (Math.random() - 0.5) * 1.6 : 0)), r2(s.p[1] + 0.02), r2(s.p[2] + (k ? (Math.random() - 0.5) * 1.6 : 0))];
        const r = Math.random();
        if (r < 0.46) {
          const id = wpick(GUNS), l = this.brAddLoot({ k: 'gun', id, tier: rollTier(GUNS[id].tier, q), p: at(0) });
          l.a = ammoFor(id, 1);
          if (Math.random() < 0.55) this.brAddLoot({ k: 'ammo', id: 'ammo', p: at(1) });
        } else if (r < 0.52) { const id = wpick(MELEE); this.brAddLoot({ k: 'melee', id, tier: rollTier(MELEE[id].tier, q * 0.5), p: at(0) }); }
        else if (r < 0.66) { const id = wpick(GADGETS); this.brAddLoot({ k: 'gadget', id, tier: GADGETS[id].tier, n: GADGETS[id].n, p: at(0) }); }
        else if (r < 0.79) { const id = Math.random() < 0.55 - q * 0.2 ? 'plate' : Math.random() < 0.8 ? 'vest' : 'fridge'; this.brAddLoot({ k: 'armor', id, p: at(0) }); }
        else if (r < 0.92) { const id = Math.random() < 0.72 - q * 0.2 ? 'cola' : 'medkit'; this.brAddLoot({ k: 'heal', id, n: id === 'cola' ? 2 : 1, p: at(0) }); }
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
            k = Math.max(0, s.slots.findIndex((g) => g && g.w === p.w)); // swap the one in your hands (holding the bread: the first)
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
      } else if (l.k === 'armor') {
        if (s.armor >= BR.armor.max) return false;
        s.armor = Math.min(BR.armor.max, s.armor + ARMOR_OF[l.id]);
      }
      if (!took) return false;
      B.loot.delete(i);
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
      if (s.gadget && s.gadget.n > 0) { p.item = s.gadget.i; p.ic = s.gadget; }
      send(p, { t: 'brinv', s: s.slots.map((g) => (g ? [g.w, g.tier, g.ammo == null ? -1 : g.ammo] : 0)), m: s.melee ? [s.melee.w, s.melee.tier] : 0, g: s.gadget && s.gadget.n > 0 ? [s.gadget.i, s.gadget.n] : 0, c: s.cola, k: s.medkit, ar: Math.round(s.armor), hl: s.heal ? [s.heal.k, Math.max(0, s.heal.until - now())] : 0 });
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
        case 's': return !!s.inBlimp; // riding the blimp: the server knows where you are
        case 'brjump': this.brJump(p); return true;
        case 'brpick': if (Number.isInteger(m.i) && now() - (p.brPickT || 0) > 80) { p.brPickT = now(); if (!this.brPick(p, m.i, m.f === 1)) this.brLoadout(p); } return true;
        case 'brheal': if (m.k === 'cola' || m.k === 'medkit') this.brHeal(p, m.k); return true;
        case 'respawn': case 'itemsel': case 'deploy': return true; // no respawns, items come off the floor, no killstreaks
        case 'fire': case 'hit': case 'push': {
          if (s.inBlimp || s.out) return true;
          if (m.t === 'push' && m.w === 'hook') return false;
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
      s.out = true; s.heal = null; s.fly = null; t.f &= ~FLAGS.GLIDE;
      const left = this.brAlive().length;
      s.place = left + 1;
      B.out.push({ id: t.id, place: s.place });
      if (killer && killer !== t && killer.br) killer.br.kills++;
      this.brDropAll(t);
      this.broadcast({ t: 'br', k: 'out', id: t.id, place: s.place, by: killer && killer !== t ? killer.id : 0, w, left });
      if (LOG) {
        const why = w === 'zone' ? 'the zone' : w === 'void' ? (killer ? `${killer.name} (knocked into the void)` : 'the void') : killer && killer !== t ? `${killer.name} with ${w}` : w;
        const hp = killer && killer !== t ? ` (killer had ${Math.round(killer.hp)} hp, ${Math.round(killer.br ? killer.br.armor : 0)} armour)` : '';
        const kit = (s.slots || []).filter(Boolean).map((g) => `${TIERS[g.tier].name[0]}-${g.w}`).join('+') || 'bread only';
        B.log.push(`#${s.place} ${t.name} died to ${why}${hp}, carried ${kit}, ${s.kills} kills, ${Math.round((now() - B.t0) / 1000)}s in`);
      }
    },
    brAlive() { return this.fighters().filter((p) => p.br && !p.br.out && p.br.match === this.br.id); },
    // who can a bot see as a target (nobody on the blimp, nobody who's out)
    brTargetable(t) { return !(t.br && (t.br.inBlimp || t.br.out)); },

    // ---------------------------------------------------------- the clock: blimp, zone damage, heals, the winner
    tickBR(n) {
      const B = this.br;
      if (!B || !this.brOn) return;
      const alive = this.brAlive();
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
        for (const p of alive) if (!p.br.inBlimp && outsideZone(zn, p.pos)) this.damage(p, zn.dps * 0.5, null, 'zone');
      }
      // last one standing (or nobody: the zone got the last two at once)
      const left = this.brAlive();
      if (!B.endAt && ((B.peak >= 2 && left.length <= 1) || !left.length || n >= this.round.ends)) {
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
      if (B.endAt && n >= B.endAt && !this.round.over) this.endRound();
    },
    // the end screen: by placement (the winner first), then kills
    brSort(list) {
      const place = (p) => (p.br && p.br.place) || (p.br && !p.br.out ? 1 : 999);
      list.sort((a, b) => place(a) - place(b) || b.kills - a.kills);
    },
    brBoardInfo() { return this.fighters().filter((p) => p.br && p.br.match === (this.br && this.br.id)).map((p) => [p.id, p.br.place || (p.br.out ? 0 : 1), p.br.kills || 0]); },

    // ---------------------------------------------------------- bots: drop, glide, loot, rotate, heal, pick the gun for the range
    // (the fighting itself is botThink's; these steer it)
    brBotStep(b, dt) {
      const s = b.br;
      if (!s || s.out) return false;
      const n = now();
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
        if (l.p[1] < 1.6) c.p = l.p; // land on the ground in that area
        cells.set(k, c);
      }
      for (const o of this.fighters()) if (o !== b && o.br && o.br.ai && o.br.ai.cell) { const c = cells.get(o.br.ai.cell); if (c) c.taken++; }
      const aggro = Math.random();
      let best = null, bv = -1e9;
      for (const [k, c] of cells) {
        if (outOfBounds(this.map, c.p) || c.p[1] > 1.6) continue;
        const v = c.v * (aggro > 0.75 ? 1.6 : 1) - c.taken * c.taken * (aggro > 0.75 ? 1 : 6) + Math.random() * 6;
        if (v > bv) { bv = v; best = [k, c]; }
      }
      const drop = best ? best[1].p.slice() : (spots[0] ? spots[0].p.slice() : [0, 0, 0]);
      if (LOG) B.log.push(`${b.name} wants to land at ${drop[0] | 0},${drop[2] | 0} (${aggro > 0.75 ? 'hot drop' : 'quiet'})`);
      return { drop, cell: best ? best[0] : null, aggro, jumpR: 25 + Math.random() * 25, lastD: null, loot: 0, lootT: 0, skip: new Map(), roam: null, roamT: 0, pickT: 0, healT: 0, wT: 0 };
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
      if (moved && b.onGround) { s.fly = null; b.f = 0; if (LOG) this.br.log.push(`${b.name} landed ${Math.round(tl)} m from where it wanted`); }
      if (b.pos[1] < this.map.killY) this.kill(b, null, 'void');
    },
    brMove(b, dt) { const res = H.movePlayer(b.pos, b.vel, dt, this.boxes, false); b.onGround = !!res.ground && b.vel[1] <= 0.01; return true; },

    // what a bot wants right now (botGoal): out of the zone, heal up, loot, or move with the circle
    brBotGoal(b) {
      const s = b.br;
      if (!s || s.out || s.inBlimp || s.fly || !s.ai) return null;
      const ai = s.ai, n = now(), B = this.br;
      const zn = zoneAt(B.zone, n);
      const t = this.players.get(b.ai.target), fighting = t && t.alive && b.ai.seenAt;
      // 1. the zone: outside (or about to be) = go, even mid-fight
      const dc = Math.hypot(b.pos[0] - zn.c[0], b.pos[2] - zn.c[1]);
      if (dc > zn.r - 3) return { p: this.brInward(b, zn.c, zn.r), force: true, r: 0 };
      // rotate ahead of the circle: once the next one is known and the wait is running out
      const nx = zn.next;
      if (nx) {
        const dn = Math.hypot(b.pos[0] - nx.c[0], b.pos[2] - nx.c[1]), soon = zn.shrinking || zn.left < 22000 + dn / 6 * 1000;
        if (soon && dn > nx.r * 0.8) return { p: this.brInward(b, nx.c, nx.r * 0.7), force: zn.shrinking && dc > zn.r * 0.8, r: 0 };
      }
      // 2. heal when it's quiet
      const need = 100 - b.hp;
      if (!fighting && !s.heal && need > 20 && (s.cola || s.medkit) && n > ai.healT) {
        ai.healT = n + 1500;
        this.brHeal(b, need > 45 && s.medkit ? 'medkit' : s.cola ? 'cola' : 'medkit');
      }
      if (s.heal) return fighting ? null : { p: b.pos, force: true, r: 0 };
      // 3. loot: the best thing nearby that's actually an upgrade
      if (n > ai.lootT) { ai.lootT = n + 450; ai.loot = this.brBotLoot(b); }
      const l = ai.loot && B.loot.get(ai.loot);
      if (l) {
        const d = hdist(b.pos, l.p);
        if (d < BR.pickR && Math.abs(l.p[1] - b.pos[1]) < 1.6) {
          if (!this.brPick(b, l.i, true)) ai.skip.set(l.i, n + 60000);
          ai.loot = 0; ai.lootT = 0;
          return null;
        }
        if (!ai.lootSince || ai.lootFor !== l.i) { ai.lootFor = l.i; ai.lootSince = n; }
        if (n - ai.lootSince > 9000) { ai.skip.set(l.i, n + 60000); ai.loot = 0; } // can't get there: forget it
        if (!fighting) return { p: [l.p[0], l.p[1], l.p[2]], force: false, r: 0 };
      }
      // 4. nothing to do: drift toward the middle of the (next) circle, somewhere new now and then
      if (!ai.roam || n > ai.roamT || hdist(b.pos, ai.roam) < 4) {
        const c = nx ? nx.c : zn.c, r = nx ? nx.r : zn.r;
        const a = Math.random() * Math.PI * 2, d = Math.random() * r * 0.6;
        ai.roam = this.brInward(b, [c[0] + Math.cos(a) * d, c[1] + Math.sin(a) * d], 1);
        ai.roamT = n + 12000 + Math.random() * 8000;
      }
      return fighting ? null : { p: ai.roam, force: false, r: 0 };
    },
    // a walkable point near (x, z) inside a circle of radius r round c (bots aim for ground spots)
    brInward(b, c, r) {
      const g = groundSpots(this.map);
      let best = null, bd = 1e9;
      for (let i = 0; i < 40 && g.length; i++) {
        const s = g[(Math.random() * g.length) | 0];
        if (Math.hypot(s.p[0] - c[0], s.p[2] - c[1]) > Math.max(2, r)) continue;
        const d = hdist(s.p, b.pos);
        if (d < bd) { bd = d; best = s.p; }
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
        const worst = Math.min(...s.slots.map((g) => g.tier + (GUNS[g.w] ? GUNS[g.w].tier : 0) + (g.ammo === 0 ? -9 : 0)));
        const v = l.tier + (GUNS[l.id] ? GUNS[l.id].tier : 0);
        return v > worst + 0.5 ? 2 + v - worst : 0;
      }
      if (l.k === 'armor') return s.armor < BR.armor.max - 10 ? 2 + ARMOR_OF[l.id] / 25 : 0;
      if (l.k === 'heal') return s[l.id] < BR[l.id].n ? (b.hp < 70 ? 4 : 1.5) : 0;
      if (l.k === 'ammo') return s.slots.some((g) => g && g.ammo != null && g.ammo < ammoFor(g.w)) ? 1.6 : 0;
      if (l.k === 'gadget') return !s.gadget || s.gadget.n <= 0 ? 1.2 : s.gadget.i === l.id ? 0.6 : 0;
      if (l.k === 'melee') return s.melee.w === BR.melee ? 1 + l.tier : MELEE[l.id] && l.tier > s.melee.tier ? 1 : 0;
      return 0;
    },
    brBotLoot(b) {
      const B = this.br, ai = b.br.ai, n = now(), zn = zoneAt(B.zone, n);
      let best = 0, bv = 0;
      for (const l of B.loot.values()) {
        const d = hdist(b.pos, l.p);
        if (d > 45 || Math.abs(l.p[1] - b.pos[1]) > 1.8 || (ai.skip.get(l.i) || 0) > n) continue;
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
        const v = fit(g.w) * TIERS[g.tier].mul;
        if (v > bv) { bv = v; best = g.w; }
      }
      if (b.w !== best) { b.w = best; b.ai.ammo = Math.min(WEAPONS[best].mag || 1, this.brAmmo(b, best)); b.ai.nextShot = Math.max(b.ai.nextShot, n + 350); b.ai.reloadUntil = 0; }
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
      if (s.slots && !s.slots.some(Boolean) && d > 10) return 1e9; // bread only: go find a gun first
      if (now() - (t.lastAttackT || 0) < 3000 && t.lastAttacker !== b.id) score *= 0.55; // someone's already shooting them: help finish the job
      return score * (0.6 + theirs / 250);
    },
  });
}
