// BATTLE ISLAND, step 2: hero picks, the MECH METER, energy cells and the island's zone schedule. On top of server/island.js
// (squads, downs, revives) and the royale; the mech itself is MECH DROP's (server/mech.js: mechCall drops it, mechEnter
// climbs in, mechExit ejects): nothing here duplicates it. The server owns the meter, every pick, every cell and the call.
import { raycast } from '../shared/physics.js';
import { outOfBounds } from '../shared/bounds.js';
import { ISLE, ISLE_ZONE, ISLE_FINAL } from '../shared/island.js';
import { HEROES, HERO_IDS, isHero, heroFor, heroName } from '../shared/heroes.js';

const now = () => Date.now();
const r2 = (x) => Math.round(x * 100) / 100;
const hdist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const vec3 = (a) => (Array.isArray(a) && a.length === 3 && a.every((x) => typeof x === 'number' && Number.isFinite(x) && Math.abs(x) < 1e6) ? a.slice() : null);
const LOG = !!process.env.JF_ISLE_LOG;
// test knobs: the meter fills this many times faster (JF_ISLE_METER), the island's zone runs x this long (JF_ISLE_ZONE)
const knob = (k, lo, hi) => { const v = Number(process.env[k]); return Number.isFinite(v) && v >= lo && v <= hi ? v : null; };
if (knob('JF_ISLE_METER', 0.1, 100)) ISLE.meter.time /= knob('JF_ISLE_METER', 0.1, 100);
if (knob('JF_ISLE_ZONE', 0.02, 5)) for (const z of ISLE_ZONE) { z[0] *= knob('JF_ISLE_ZONE', 0.02, 5); z[1] *= knob('JF_ISLE_ZONE', 0.02, 5); }

export function installIsleMeter(Room, H) {
  const { send } = H;
  Object.assign(Room.prototype, {
    // ---------------------------------------------------------- hero picks (the lobby = before you jump)
    // a match starts: everyone gets a hero, people first (what they picked: the loadout's mech frame or the blimp
    // pick), then bots fill the gaps. no doubles in a squad (until the squad outnumbers the roster)
    isleHeroAll() {
      const by = new Map();
      for (const p of this.fighters()) if (this.isleIn(p)) (by.get(p.sq) || by.set(p.sq, []).get(p.sq)).push(p);
      for (const list of by.values()) {
        list.sort((a, b) => (a.isBot - b.isBot) || a.id - b.id);
        const taken = [];
        for (const p of list) {
          const want = p.isBot ? HERO_IDS[(Math.random() * HERO_IDS.length) | 0] : p.heroWant || p.mechFrame; // (bots: any, then the gaps)
          p.hero = heroFor(want, taken, list.length);
          taken.push(p.hero);
          if (!p.mm || p.mm.match !== this.br.id) p.mm = { match: this.br.id, v: 0, sv: -1, sT: 0, out: false };
        }
      }
    },
    // {t:'hero', h}: change your pick while you're still on the blimp. a clash with a squadmate: refused, you keep yours
    isleHeroPick(p, h) {
      const n = now();
      if (n - (p.heroT || 0) < 250) return;
      p.heroT = n;
      if (!isHero(h)) return;
      p.heroWant = h; // (your next match too)
      if (!this.isleIn(p) || !p.br.inBlimp || !p.alive) { if (this.isleIn(p)) send(p, { t: 'isle', k: 'hero', id: p.id, h: p.hero, no: 1, why: 'only on the blimp' }); return; }
      const mates = this.isleMates(p.sq), taken = mates.filter((o) => o !== p).map((o) => o.hero);
      if (heroFor(h, taken, mates.length) !== h) { send(p, { t: 'isle', k: 'hero', id: p.id, h: p.hero, no: 1, why: `a squadmate has ${heroName(h)}` }); return; }
      p.hero = h;
      this.broadcast({ t: 'isle', k: 'hero', id: p.id, h });
    },
    isleHeroList() { return this.fighters().filter((p) => this.isleIn(p) && p.hero).map((p) => [p.id, p.hero]); },

    // ---------------------------------------------------------- the MECH METER
    isleMeterOn(p) { return this.isleIn(p) && this.isleUp(p) && !!p.mm && p.mm.match === this.br.id && !p.br.inBlimp && !p.br.fly && !p.mech && !this.mechOf(p); },
    // add to p's meter (why: for the log). nothing while your mech is out, you're down or still in the sky
    isleMeter(p, add, why) {
      if (!(add > 0) || !this.isleMeterOn(p)) return;
      const M = p.mm, was = M.v;
      M.v = Math.min(ISLE.meter.max, M.v + add);
      if (was < ISLE.meter.max && M.v >= ISLE.meter.max) { this.isleMeterSend(p, true); if (LOG && why !== 'time') this.br.isle.log.push(`${p.name} MECH READY (${why})`); }
    },
    isleMeterSend(p, now1) {
      const M = p.mm, n = now(), v = Math.floor(M.v), out = !!(p.mech || this.mechOf(p));
      if (p.isBot || (!now1 && (v === M.sv && out === M.out) ) || (!now1 && n - M.sT < 250)) return;
      M.sv = v; M.sT = n; M.out = out;
      send(p, { t: 'isle', k: 'mm', v, out: out ? 1 : 0, h: p.hero });
    },
    // tickIsle hook: time fills it; everyone hears their own
    isleMeterTick(n, dt) {
      const per = ISLE.meter.max / ISLE.meter.time * dt / 1000;
      for (const p of this.fighters()) {
        if (!p.mm || !this.isleIn(p)) continue;
        this.isleMeter(p, per, 'time');
        this.isleMeterSend(p, false);
        if (p.isBot && p.mm.v >= ISLE.meter.max) this.isleBotCall(p, n);
      }
    },
    // the streak key at 100%: MECH DROP's own call (the marker's checks: range, sight, floor, open sky). 'deploy' with
    // r 'mechdrop' and at = where you aimed. refused: the meter stays full
    isleCall(p, m) {
      const n = now();
      if (n - (p.callT || 0) < 300) return;
      p.callT = n;
      const at = vec3(m.at);
      if (m.r !== 'mechdrop' || !at || !p.mm) return;
      if (!this.isleIn(p) || !p.alive || p.dn || p.br.inBlimp || p.br.fly) return;
      if (p.mech || this.mechOf(p)) { this.mechNo(p, 'your mech is already out'); return; }
      if (p.rig || this.isBall(p) || p.ballUntil > n || p.trap) { this.mechNo(p, 'not right now'); return; }
      if (p.mm.v < ISLE.meter.max) { this.mechNo(p, `meter at ${Math.floor(p.mm.v)}%`); this.isleMeterSend(p, true); return; }
      const f = HEROES[p.hero] ? HEROES[p.hero].frame : 'paperplane';
      if (!this.mechCall(p, at, f)) { this.isleMeterSend(p, true); return; }
      p.mm.v = 0;
      this.isleMeterSend(p, true);
      this.broadcast({ t: 'isle', k: 'call', id: p.id, h: p.hero });
      if (LOG) this.br.isle.log.push(`${p.name} CALLED ${heroName(p.hero)}`);
    },
    // mech.js hook: your mech is gone (blown up, flew off unused, the match ended it): the meter restarts with a head start
    isleMechEnd(p) {
      if (!p || !p.mm || !this.isleIn(p) || p.mech || this.mechOf(p)) return;
      if (LOG && p.isBot) this.br.isle.log.push(`${p.name}'s mech ends: ${p.dn ? 'down' : !p.alive ? 'dead' : 'up'}`);
      p.mm.v = ISLE.meter.after;
      this.isleMeterSend(p, true);
      if (LOG) this.br.isle.log.push(`${p.name}'s mech is gone: meter back to ${ISLE.meter.after}`);
    },

    // ---------------------------------------------------------- energy cells (loot k 'cell')
    // brRound hook: the map's own cell spots (map.royale.cells, [x, y, z] each), else next to every `every`th loot spot
    isleCells() {
      const B = this.br, R = this.map.royale || {};
      let pts = Array.isArray(R.cells) && R.cells.length ? R.cells.filter((c) => vec3(c)).map((c) => [r2(c[0]), r2(c[1] + 0.02), r2(c[2])]) : null;
      if (!pts) {
        pts = [];
        (B.spots || []).forEach((s, i) => { if (i % ISLE.cells.every === 3) { const a = Math.random() * 6.28; pts.push([r2(s.p[0] + Math.cos(a) * 0.9), r2(s.p[1] + 0.02), r2(s.p[2] + Math.sin(a) * 0.9)]); } });
      }
      for (const p of pts) this.brAddLoot({ k: 'cell', id: 'cell', p });
      B.cellN = pts.length;
    },
    // brPick hook: true = taken (+20%). not while your mech is out or your meter's full (it stays on the floor)
    isleCell(p) {
      if (!this.isleMeterOn(p) || p.mm.v >= ISLE.meter.max) return false;
      this.isleMeter(p, ISLE.meter.cell, 'cell');
      this.isleMeterSend(p, true);
      p.br.cells = (p.br.cells || 0) + 1;
      return true;
    },
    isleCellWant(b) { return !this.isleMeterOn(b) ? 0 : b.mm.v < 60 ? 5 : b.mm.v < ISLE.meter.max - 10 ? 3 : 0; }, // (brBotWant: an emptier meter wants them more)
    // isleBotStep hook: a bot whose mech is standing there waiting (it was down when it landed, or it hopped out) climbs back in
    isleBotMech(b, n) {
      const m = this.mechOf(b);
      if (!m || b.mech || b.dn || (m.st !== 'wait' && m.st !== 'idle') || n < (b.mechTryT || 0)) return;
      b.mechTryT = n + 1000;
      if (hdist(b.pos, m.p) < 40) { b.pos = m.p.slice(); this.mechEnter(b, n); } // (like MECH DROP's own bot climb-in)
    },

    // ---------------------------------------------------------- bots call theirs in near a fight
    isleBotCall(b, n) {
      if (n < (b.callT || 0) || !this.isleMeterOn(b) || b.rig || this.isBall(b)) return;
      b.callT = n + 1500;
      const t = this.players.get(b.ai && b.ai.target);
      if (!t || !t.alive || !b.ai.seenAt || hdist(t.pos, b.pos) > 45) return; // near a fight, not just anywhere
      const fw = [-Math.sin(b.yaw), -Math.cos(b.yaw)], f = HEROES[b.hero] ? HEROES[b.hero].frame : 'paperplane';
      for (const k of [6, 3, 0]) {
        const at = [b.pos[0] + fw[0] * k, b.pos[1] + 0.3, b.pos[2] + fw[1] * k];
        if (this.mechCall(b, at, f)) {
          b.mm.v = 0;
          this.broadcast({ t: 'isle', k: 'call', id: b.id, h: b.hero });
          if (LOG) this.br.isle.log.push(`${b.name} CALLED ${heroName(b.hero)} (fighting ${t.name})`);
          return;
        }
      }
    },

    // ---------------------------------------------------------- the island's zone schedule (brRound hook)
    // 5 rings (ISLE_ZONE). the last one: a map finale spot if it has some (map.royale.finale [x, z, r]), else open
    // ground near the middle, checked for floor all round (never over the void or the sea). the rings in between slide
    // from the first circle to it, each one inside the last
    isleZoneSteps(steps, z0, ground) {
      const map = this.map, R = map.royale || {}, fin = Array.isArray(R.finale) ? R.finale.filter((f) => Array.isArray(f) && f.length >= 2 && f.every(Number.isFinite)) : [];
      let F = null, rF = ISLE_FINAL.r;
      const cands = fin.length ? fin.slice().sort(() => Math.random() - 0.5).map((f) => [f[0], f[1], Math.max(ISLE_FINAL.r, f[2] || 0)])
        : ground.filter((s) => Math.hypot(s.p[0] - z0[0], s.p[2] - z0[1]) <= z0[2] * ISLE_FINAL.lean).sort(() => Math.random() - 0.5).slice(0, 60).map((s) => [s.p[0], s.p[2], ISLE_FINAL.r]);
      for (const c of cands) if (Math.hypot(c[0] - z0[0], c[1] - z0[1]) <= z0[2] - c[2] && this.isleLand(c[0], c[1], c[2])) { F = [c[0], c[1]]; rF = c[2]; break; }
      if (!F) F = [z0[0], z0[1]]; // (nothing checked out: the middle of the first circle)
      const rs = ISLE_ZONE.map(([, , share], i) => (i === ISLE_ZONE.length - 1 ? rF : Math.max(rF, z0[2] * share))), tot = z0[2] - rF;
      steps.length = 0;
      ISLE_ZONE.forEach(([wait, shrink, , dps], i) => {
        const k = tot > 0 ? (z0[2] - rs[i]) / tot : 1; // how far along to the last ring: each step moves at most as much as the circle shrinks
        steps.push({ c: [r2(z0[0] + (F[0] - z0[0]) * k), r2(z0[1] + (F[1] - z0[1]) * k)], r: r2(rs[i]), wait, shrink, dps });
      });
      return steps;
    },
    // is there floor all round this circle? (the middle + 8 points at 80%): no void, no deep water
    isleLand(x, z, r) {
      const map = this.map, T = map.boxes && map.boxes.terrain, sea = map.seaY;
      for (let i = 0; i <= 8; i++) {
        const a = i * Math.PI / 4, k = i ? r * 0.8 : 0, px = x + Math.cos(a) * k, pz = z + Math.sin(a) * k;
        if (outOfBounds(map, [px, 0, pz])) return false;
        if (T && sea != null) { const g = T.at(px, pz); if (g == null || sea - g > (map.wade || 1.5)) return false; continue; }
        const h = raycast([px, 120, pz], [0, -1, 0], 120 - map.killY, map.boxes);
        if (!h || 120 - h.t < map.killY + 2) return false;
      }
      return true;
    },
  });
}
