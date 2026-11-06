// Plant & Defuse bots that play as a team (the economy mode). Installed with the econ* methods (server/econ.js).
//
// Every map's tactical spots are worked out from its own data, so a map pass that moves a site or a lane needs no edit
// here: map.sites (the plant boxes), map.nav (the lanes bots walk to each site) and map.teamSpawns. From those:
//   entry  where a lane steps onto a site; stage  ~20 m back along it (attackers group up there, defenders retake from there)
//   holds  spots near a site that see an attackers' entry, best with cover in front (defenders hold the angle)
//   plants spots inside the site with cover that the defenders' entries can't see (the carrier plants there)
//   post   after the plant: spots that see the bomb, with cover, out of the defenders' entries' sight
// One brain per side (this.ec.tac) runs a few times a second; each bot asks it for a goal in econBotGoal.
//   attack   gather at a stage -> execute together (smokes on the holds and the defenders' entries, frags on the holds)
//            -> plant in a safe spot -> post-plant spots, push the defuser. Save when the round is lost.
//   defense  split onto the sites and hold angles -> rotate on info (2+ attackers seen at a site, a teammate killed
//            there) -> after a plant: group at a stage, retake together, the kit holder defuses when it's clear. Save
//            when the defuse can't make it in time.
//   buying   one plan per team and round: full / force / eco (save) / pistol; the rich buy a rifle for a broke teammate
//            and drop it at their feet; roles get smokes or frags.
// JF_ECON_LOG=1 prints the plans and why each round was won (bots-only test matches).
import { WEAPONS } from '../shared/weapons.js';
import { BOMB, siteAt } from '../shared/modes.js';
import { ECON, GEAR, weaponPrice, econWeapon, itemSpec, refillPrice } from '../shared/econ.js';
import { raycast, query, PH } from '../shared/physics.js';
import { patternOf } from '../shared/tactical.js';

const LOG = !!process.env.JF_ECON_LOG;
const now = () => Date.now();
const pick = (a) => a[(Math.random() * a.length) | 0];
const hyp = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const d3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const r1 = (x) => Math.round(x * 10) / 10;
const xz = (q) => `${Math.round(q[0])},${Math.round(q[2])}`;
const SPOTS = new WeakMap(); // map -> tactical spots
let D = null; // from server.js: navGraph
export function aiDeps(d) { D = d; }
const STAGE_D = 20, RETAKE_D = 16; // m back from a site's entry where attackers group up / defenders gather for a retake
const RUN = 6.2; // m/s a bot really covers along a route (8.5 top speed, corners, jumps)
const SMOKE_R = 6.5;
const centroid = (list) => { if (!list || !list.length) return null; const c = [0, 0, 0]; for (const q of list) for (let k = 0; k < 3; k++) c[k] += q[k] / list.length; return c; };
const inBox = (s, q, pad) => q[0] >= s.min[0] - pad && q[0] <= s.max[0] + pad && q[2] >= s.min[2] - pad && q[2] <= s.max[2] + pad;
const usable = (x) => x && (WEAPONS[x.id].kind === 'hitscan' || WEAPONS[x.id].kind === 'proj') && WEAPONS[x.id].slot !== 'melee' && (!x.lim || x.m + x.r > 0);
const RIFLES = ['ar', 'ar', 'ar', 'redline', 'redline', 'chicken', 'burst', 'dmr', 'lmg'];
const FORCE = ['smg', 'smg', 'shotgun', 'banana', 'bowling', 'lever', 'autoshot', 'tennis'];
const SIDEARM_BUYS = ['pistol', 'akimbo', 'sawnoff']; // a pistol-round upgrade over the free revolver

const M = {
  // ---------------------------------------------------------- the map's tactical spots (worked out once per map)
  econAiMap() {
    const m = this.map;
    let S = SPOTS.get(m);
    if (S) return S;
    const ts = m.teamSpawns || {};
    const attC = centroid(ts.att) || m.spawns[0], defC = centroid(ts.def) || m.spawns[m.spawns.length - 1];
    const g = m.graph ? null : this.econAiGraph();
    S = { attC, defC, sites: {} };
    for (const site of m.sites || []) S.sites[site.id] = this.econAiSite(site, attC, defC, g);
    SPOTS.set(m, S);
    if (LOG) for (const [id, s] of Object.entries(S.sites)) console.log(`[tac] map ${m.name} site ${id}: ${s.lanes.filter((l) => l.side === 'att').length} attack lanes, ${s.lanes.filter((l) => l.side === 'def').length} defense lanes, ${s.holds.length} holds, ${s.plants.length} plant spots, ${s.grid.length} standing spots`);
    return S;
  },
  econAiGraph() { return D && D.navGraph ? D.navGraph(this.map) : null; },
  // a floor a bot can stand on near height y (null if none): no roofs far above, room for the body
  econAiStand(x, z, y, up = 2.6, down = 3) {
    const o = [x, y + up, z];
    for (const b of query(this.boxes, x - 0.05, z - 0.05, x + 0.05, z + 0.05)) if (o[1] > b.min[1] && o[1] < b.max[1] && x > b.min[0] && x < b.max[0] && z > b.min[2] && z < b.max[2]) return null;
    const h = raycast(o, [0, -1, 0], up + down, this.boxes);
    if (!h) return null;
    const fy = h.point[1], hw = PH.halfW;
    for (const b of query(this.boxes, x - hw, z - hw, x + hw, z + hw)) {
      if (b.max[0] > x - hw && b.min[0] < x + hw && b.max[2] > z - hw && b.min[2] < z + hw && b.min[1] < fy + PH.height && b.max[1] > fy + 0.15) return null;
    }
    return [x, fy, z];
  },
  econAiSees(a, c) { // a, c feet positions: eye to chest, walls only (smoke is the live check, canSee)
    const e = [a[0], a[1] + PH.eye, a[2]], t = [c[0], c[1] + 1.1, c[2]];
    const d = [t[0] - e[0], t[1] - e[1], t[2] - e[2]], l = Math.hypot(...d);
    return l < 0.1 || !raycast(e, d.map((v) => v / l), l, this.boxes);
  },
  // cover: something at hip height between the spot and where the threat comes from, close by
  econAiCover(q, from) {
    const o = [q[0], q[1] + 0.8, q[2]], d = [from[0] - q[0], 0, from[2] - q[2]], l = Math.hypot(d[0], d[2]) || 1;
    const h = raycast(o, [d[0] / l, 0, d[2] / l], 2.6, this.boxes);
    return h ? 1 : 0;
  },
  econAiNode(g, q) { // the lane-graph waypoint a bot can walk straight from to q
    if (!g) return -1;
    let best = -1, bd = 1e9;
    for (let i = 0; i < g.pts.length; i++) {
      const d = Math.hypot(g.pts[i][0] - q[0], g.pts[i][1] - q[2]);
      if (d < bd && d < 40 && this.clearPath(q, g.pts[i])) { bd = d; best = i; }
    }
    return best;
  },
  econAiSite(site, attC, defC, g) {
    const y0 = site.min[1], c = [(site.min[0] + site.max[0]) / 2, y0, (site.min[2] + site.max[2]) / 2];
    const flo = (x, z, yRef) => { const s = this.econAiStand(x, z, yRef, 2.2, 5); return s ? s[1] : yRef; };
    const lanes = [];
    for (const lane of (this.map.nav && this.map.nav[site.id]) || []) {
      if (!lane.length) continue;
      const pts = lane.map((q) => { const y = q.length > 2 ? q[2] : flo(q[0], q[1], y0); return [q[0], y, q[1]]; });
      const side = hyp(pts[0], attC) < hyp(pts[0], defC) ? 'att' : 'def';
      let ei = pts.length - 1;
      while (ei > 0 && inBox(site, pts[ei], 2.5)) ei--;
      let si = ei, acc = 0;
      const want = side === 'att' ? STAGE_D : RETAKE_D;
      while (si > 0 && acc < want) { acc += d3(pts[si], pts[si - 1]); si--; }
      lanes.push({ side, pts, ei, si, entry: pts[ei], stage: pts[si], node: g ? this.econAiNode(g, pts[si]) : -1 });
    }
    if (!lanes.some((l) => l.side === 'att')) lanes.push(this.econAiFakeLane(c, attC, 'att', g));
    if (!lanes.some((l) => l.side === 'def')) lanes.push(this.econAiFakeLane(c, defC, 'def', g));
    // every spot a bot can stand on around the site and walk to (straight from a lane point near the site, or the centre)
    const refs = [c], defRefs = [c];
    for (const l of lanes) for (let i = Math.max(0, l.si - 1); i < l.pts.length; i++) { refs.push(l.pts[i]); if (l.side === 'def') defRefs.push(l.pts[i]); }
    const walk = (r, q) => Math.abs(r[1] - q[1]) < 1.3 && hyp(r, q) < 30 && this.clearPath(r, [q[0], q[2]]);
    const grid = [];
    for (let x = site.min[0] - 16; x <= site.max[0] + 16; x += 2) {
      for (let z = site.min[2] - 16; z <= site.max[2] + 16; z += 2) {
        const q = this.econAiStand(x, z, y0, 1.6, 3.5) || this.econAiStand(x, z, y0, 4.2, 3.5); // under a ceiling, then galleries
        if (!q || q[1] < y0 - 2.5 || q[1] > y0 + 2.6) continue;
        const ref = refs.find((r) => walk(r, q));
        if (!ref) continue;
        // def: the defenders can walk there from their side (a roof only the attackers' lane climbs onto is no hold)
        grid.push({ p: q, node: g ? this.econAiNode(g, q) : -1, on: !!siteAt(this.map, q), def: defRefs.some((r) => walk(r, q)) });
      }
    }
    const attE = lanes.filter((l) => l.side === 'att'), defE = lanes.filter((l) => l.side === 'def');
    // holds: for each attackers' entry, spots 8-26 m away that see it, best with cover toward it and on the defenders' side
    const holds = [];
    attE.forEach((l, li) => {
      const cand = [];
      for (const s of grid) {
        const d = hyp(s.p, l.entry);
        if (!s.def || d < 8 || d > 26 || !this.econAiSees(s.p, l.entry)) continue;
        const sc = 6 - Math.abs(d - 15) * 0.25 + this.econAiCover(s.p, l.entry) * 3.5 + (hyp(s.p, defC) < hyp(l.entry, defC) ? 1.5 : -2) + (s.on ? 0.8 : 0) - (this.econAiSees(s.p, l.stage) ? 0 : -0.5);
        cand.push({ ...s, sc, lane: li, look: l.entry });
      }
      cand.sort((a, b) => b.sc - a.sc);
      const mine = [];
      for (const s of cand) { if (mine.length >= 4) break; if (mine.every((o) => hyp(o.p, s.p) > 3.5) && holds.every((o) => hyp(o.p, s.p) > 2.5)) mine.push(s); }
      holds.push(...mine);
    });
    // plant spots: inside the site, cover, hidden from the defenders' entries and the holds of the other attack lanes
    const plants = [];
    attE.forEach((l, li) => {
      const cand = [];
      for (const s of grid) {
        if (!s.on || !siteAt(this.map, [s.p[0], s.p[1] + 0.1, s.p[2]])) continue;
        let sc = 0;
        for (const e of defE) if (this.econAiSees(s.p, e.entry)) sc -= 3;
        for (const h of holds) if (h.lane !== li && this.econAiSees(s.p, h.p)) sc -= 0.7;
        for (const e of defE) sc += this.econAiCover(s.p, e.entry) * 2;
        sc -= Math.abs(hyp(s.p, l.entry) - 8) * 0.2;
        cand.push({ ...s, sc, lane: li });
      }
      cand.sort((a, b) => b.sc - a.sc);
      plants.push(cand.slice(0, 3));
    });
    return { id: site.id, site, c, lanes, attE, defE, grid, holds, plants };
  },
  econAiFakeLane(c, from, side, g) { // a site without lanes from that side: a straight line toward that side's spawn
    const d = [from[0] - c[0], 0, from[2] - c[2]], l = Math.hypot(d[0], d[2]) || 1;
    const at = (k) => { const q = [c[0] + (d[0] / l) * k, c[1], c[2] + (d[2] / l) * k]; const s = this.econAiStand(q[0], q[2], c[1], 2.2, 5); return s || q; };
    const entry = at(14), stage = at(14 + (side === 'att' ? STAGE_D : RETAKE_D));
    return { side, pts: [stage, entry, c], ei: 1, si: 0, entry, stage, node: g ? this.econAiNode(g, stage) : -1 };
  },
  // walk to q: on maze maps botThink's navSteer finds the way; elsewhere the lane graph, then straight
  econAiGo(b, q, node, key) {
    if (this.map.graph || node == null || node < 0) return q;
    return this.navTo(b, key, q, [node]);
  },
  // a goal for botThink: p = where to walk next (a lane waypoint or the spot), at = the spot itself
  econAiTo(b, q, node, key, extra) { return { p: this.econAiGo(b, q, node, key), at: q, r: 1, ...extra }; },

  // ---------------------------------------------------------- the two brains
  econAiState() {
    const B = this.bomb, ec = this.ec;
    if (!ec.tac || ec.tac.n !== B.n || ec.tac.att !== B.att) {
      ec.tac = { n: B.n, att: B.att, A: null, Dd: null, buy: {}, log: [], seen: [], dead: [], live: 0 };
    }
    return ec.tac;
  },
  tacLog(T, s) {
    const B = this.bomb, left = B.buyUntil ? 'buy' : r1(Math.max(0, (B.ph === 'planted' ? B.explodeAt : B.ends) - now()) / 1000) + 's';
    T.log.push(`[${B.ph === 'planted' ? 'fuse ' : ''}${left}] ${s}`);
    if (LOG) console.log(`[tac] r${B.n} ${T.log[T.log.length - 1]}`);
  },
  econAiBots(team) { return this.fighters().filter((p) => p.isBot && p.alive && p.team === team && p.ec && !p.ec.out); },
  econAiAlive(team) { return this.fighters().filter((p) => p.alive && p.team === team && !(p.ec && p.ec.out)); },
  // a few times a second: what both sides know and plan
  econAiTick(n) {
    const B = this.bomb, ec = this.ec;
    if (!B || !ec || B.ph === 'done' || B.between || !(this.map.sites || []).length) return;
    if (n < (ec.tacT || 0)) return;
    ec.tacT = n + 200;
    const T = this.econAiState();
    if (B.buyUntil) return;
    if (!T.live) {
      T.live = n;
      if (LOG) this.tacLog(T, `live: ${this.fighters().filter((p) => p.alive).map((p) => `${p.name.replace(' [bot]', '')}(${p.team === B.att ? 'att' : 'def'}) ${xz(p.pos)}`).join(' | ')}`);
    }
    const S = this.econAiMap();
    // what the bots see: enemies they have eyes on right now, remembered for a few seconds per side
    for (const p of this.fighters()) {
      if (!p.isBot || !p.alive || !p.ai || !p.ai.seenAt) continue;
      const t = this.players.get(p.ai.target);
      if (t && t.alive) T.seen.push({ by: p.team, id: t.id, p: t.pos.slice(), n, carrier: B.carrier === t.id });
    }
    T.seen = T.seen.filter((s) => n - s.n < 8000);
    T.dead = T.dead.filter((s) => n - s.n < 8000);
    this.econAiAttack(T, S, n);
    this.econAiDefense(T, S, n);
  },
  econAiSiteNear(S, q, r = 34) {
    let best = null, bd = r;
    for (const s of Object.values(S.sites)) { const d = inBox(s.site, q, 0) ? 0 : hyp(s.c, q); if (d < bd) { bd = d; best = s; } }
    return best;
  },
  econAiLeft() { const B = this.bomb; return Math.max(0, (B.ph === 'planted' ? B.explodeAt : B.ends) - now()) / 1000; },

  // ---------------------------------------------------------- attack
  econAiAttack(T, S, n) {
    const B = this.bomb, team = B.att, bots = this.econAiBots(team);
    if (!bots.length) return;
    let A = T.A;
    if (!A) {
      // pick a site: not the one that just went badly (the side remembers), then one attack lane (a split with 4+)
      const ids = Object.keys(S.sites);
      const mem = this.ec.tacMem || (this.ec.tacMem = {});
      let site = pick(ids);
      if (ids.length > 1 && mem.lostAt && mem.lostAt[team] && Math.random() < 0.65) site = pick(ids.filter((i) => i !== mem.lostAt[team])) || site;
      const s = S.sites[site], lanes = s.attE.map((l, i) => i);
      const main = pick(lanes);
      const groups = [{ lane: main, ids: [] }];
      const split = lanes.length > 1 && bots.length >= 4 && Math.random() < 0.35;
      if (split) groups.push({ lane: pick(lanes.filter((i) => i !== main)), ids: [] });
      const sorted = bots.slice().sort((a, c) => a.id - c.id);
      sorted.forEach((b, i) => { const gi = split && i % 3 === 2 && B.carrier !== b.id ? 1 : 0; groups[gi].ids.push(b.id); });
      A = T.A = { site, groups, phase: 'gather', t0: n, execAt: 0, util: [], post: new Map(), planted: false, saveWhy: '' };
      const lname = (gi) => { const l = s.attE[groups[gi].lane]; return `lane ${groups[gi].lane + 1} (stage ${xz(l.stage)})`; };
      this.tacLog(T, `ATTACK plan: ${bots.length} bots hit ${site} via ${lname(0)}${split ? ` + split of ${groups[1].ids.length} via ${lname(1)}` : ''}`);
    }
    const s = S.sites[A.site], left = this.econAiLeft();
    const alive = this.econAiAlive(team).length, defAlive = this.econAiAlive(3 - team).length;
    if (B.ph === 'planted') {
      if (!A.planted) {
        A.planted = true; A.phase = 'post'; A.post.clear(); this.tacLog(T, `planted at ${B.site} (${xz(B.p)}) by ${this.econAiName(B.planter)}, ${alive}v${defAlive}`);
        if (LOG && T.Dd) for (const d of this.econAiBots(3 - team)) { const a = T.Dd.assign.get(d.id), sp = a && a.spot; this.tacLog(T, `  defender ${d.name} at ${xz(d.pos)} y${r1(d.pos[1])} (${d.ai.ecTac}) on ${a ? a.site : '?'}${sp ? `, ${Math.round(hyp(d.pos, sp.p))} m from its spot ${xz(sp.p)}` : ''}${d.ai.seenAt ? ', sees someone' : ''}`); }
      }
      return;
    }
    if (A.phase === 'save') return;
    // the round is lost: no time to get the bomb down, or alone against a full side late
    const car = this.players.get(B.carrier);
    const from = car && car.alive ? car.pos : B.drop || S.attC;
    const need = hyp(from, s.c) / RUN * 1.25 + BOMB.plant + 2;
    if ((left < need && left < 25) || (alive === 1 && defAlive >= 3 && left < 50)) {
      A.phase = 'save';
      A.saveWhy = left < need ? `${r1(left)}s left, ${r1(need)}s needed to plant` : `1v${defAlive}`;
      this.tacLog(T, `attackers SAVE: ${A.saveWhy}`);
      return;
    }
    if (A.phase === 'gather') {
      let ready = true, contact = false;
      for (const g of A.groups) {
        const l = s.attE[g.lane];
        for (const id of g.ids) {
          const b = this.players.get(id);
          if (!b || !b.alive) continue;
          if (hyp(b.pos, l.stage) > 9) ready = false;
          if (b.ai.seenAt && hyp(b.pos, l.stage) < 22) contact = true;
        }
      }
      const late = n - T.live > 30000 || left < 45;
      if (ready || contact || late) {
        if (!ready && !contact) { // who kept the team waiting
          const far = A.groups.flatMap((g) => g.ids.map((id) => [this.players.get(id), s.attE[g.lane].stage])).filter(([p, st]) => p && p.alive && hyp(p.pos, st) > 9);
          this.tacLog(T, `late to the stage: ${far.map(([p, st]) => `${p.name} ${Math.round(hyp(p.pos, st))} m away at ${xz(p.pos)}${p.ai.ecTac ? ' (' + p.ai.ecTac + ')' : ''}`).join(', ')}`);
        }
        A.phase = 'exec'; A.execAt = n;
        this.econAiUtilPlan(A, s, bots);
        this.tacLog(T, `EXECUTE ${A.site}: ${ready ? 'grouped up' : contact ? 'spotted at the stage, go' : 'out of time to wait'} (${alive} alive, ${A.util.length} utility planned)`);
      }
    }
  },
  // smokes on the defenders' entries and on the hold that watches our entry; frags on the holds
  econAiUtilPlan(A, s, bots) {
    const U = [];
    const holds = A.groups.flatMap((g) => s.holds.filter((h) => h.lane === g.lane)).slice(0, 4);
    const smokeAt = [];
    for (const e of s.defE) smokeAt.push(e.entry);
    for (const g of A.groups) { const l = s.attE[g.lane], h = holds.find((o) => o.lane === g.lane); if (h) smokeAt.push([h.p[0] * 0.55 + l.entry[0] * 0.45, h.p[1], h.p[2] * 0.55 + l.entry[2] * 0.45]); }
    let si = 0, fi = 0;
    for (const b of bots) {
      const it = b.ec.it;
      if (!it || it.n <= 0) continue;
      for (let k = 0; k < it.n; k++) {
        if (it.id === 'smoke' && si < smokeAt.length) U.push({ id: b.id, i: 'smoke', at: smokeAt[si++], done: false });
        else if (it.id === 'frag' && holds.length) U.push({ id: b.id, i: 'frag', at: holds[fi++ % holds.length].p, done: false });
      }
    }
    A.util = U;
  },
  econAiName(id) { const p = this.players.get(id); return p ? p.name : '#' + id; },

  // ---------------------------------------------------------- defense
  econAiDefense(T, S, n) {
    const B = this.bomb, team = 3 - B.att, bots = this.econAiBots(team);
    if (!bots.length) return;
    let Dd = T.Dd;
    if (!Dd) {
      // split onto the sites: more on the one the attackers went to last time
      const ids = Object.keys(S.sites), mem = this.ec.tacMem || (this.ec.tacMem = {});
      const fav = mem.hit && mem.hit[B.att] && S.sites[mem.hit[B.att]] && Math.random() < 0.6 ? mem.hit[B.att] : pick(ids);
      const order = [fav, ...ids.filter((i) => i !== fav)];
      Dd = T.Dd = { assign: new Map(), hot: null, hotT: 0, retake: null, save: false, saveWhy: '' };
      const sorted = bots.slice().sort((a, c) => a.id - c.id);
      const used = new Set();
      sorted.forEach((b, i) => {
        const site = order[i % order.length], s = S.sites[site];
        const spot = this.econAiPickHold(s, used, i < order.length ? null : 'any');
        if (spot) used.add(spot);
        Dd.assign.set(b.id, { site, spot });
      });
      const per = {};
      for (const a of Dd.assign.values()) per[a.site] = (per[a.site] || 0) + 1;
      this.tacLog(T, `DEFENSE split: ${Object.entries(per).map(([k, v]) => `${v} on ${k}`).join(', ')}`);
    }
    if (B.ph === 'planted') { this.econAiRetake(T, S, Dd, bots, n); return; }
    // info: 2+ different attackers seen near one site (or the carrier, or a teammate killed there) -> everyone rotates
    // there but one anchor per other site when we're 4+
    const cnt = {};
    for (const x of T.seen) {
      if (x.by !== team) continue;
      const s = this.econAiSiteNear(S, x.p);
      if (!s) continue;
      (cnt[s.id] ||= new Set()).add(x.id);
      if (x.carrier) cnt[s.id].add('carrier');
    }
    for (const x of T.dead) { if (x.team !== team) continue; const s = this.econAiSiteNear(S, x.p); if (s) (cnt[s.id] ||= new Set()).add('dead' + x.id); }
    let hot = null, hc = 1;
    for (const [id, set] of Object.entries(cnt)) if (set.size > hc) { hc = set.size; hot = id; }
    if (hot && hot !== Dd.hot && n - Dd.hotT > 6000) {
      Dd.hot = hot; Dd.hotT = n;
      const away = bots.filter((b) => Dd.assign.get(b.id) && Dd.assign.get(b.id).site !== hot);
      const keep = bots.length >= 4 ? new Set(Object.keys(S.sites).filter((id) => id !== hot).map((id) => { const a = away.find((b) => Dd.assign.get(b.id).site === id); return a && a.id; }).filter(Boolean)) : new Set();
      // rotators don't trickle onto a site the attackers are taking one at a time: they meet at the site's defenders'
      // stage, hold the way in from there together, and retake from there if the bomb goes down
      const s = S.sites[hot], mid = centroid(away.map((b) => b.pos)) || S.defC;
      const lane = s.defE.slice().sort((a, c) => hyp(a.stage, mid) - hyp(c.stage, mid))[0];
      let moved = 0;
      for (const b of away) {
        if (keep.has(b.id)) continue;
        const a = moved * 2.1 + 0.6, q = this.econAiStand(lane.stage[0] + Math.cos(a) * 2.2, lane.stage[2] + Math.sin(a) * 2.2, lane.stage[1], 1.6, 3) || lane.stage;
        Dd.assign.set(b.id, { site: hot, spot: { p: q, node: lane.node, look: s.c }, rot: true });
        moved++;
      }
      Dd.rotStage = lane;
      this.tacLog(T, `defenders ROTATE to ${hot}: ${[...cnt[hot]].filter((k) => typeof k === 'number').length} attackers seen${cnt[hot].has('carrier') ? ' (with the bomb)' : ''}${[...cnt[hot]].some((k) => String(k).startsWith('dead')) ? ', a teammate died there' : ''}; ${moved} rotating, ${keep.size} anchor(s) stay`);
    }
  },
  // a hold on site s that nobody has: the best one per entry first; 'back' = a deep one (rotators arriving late)
  econAiPickHold(s, used, how) {
    const free = s.holds.filter((h) => !used.has(h));
    if (!free.length) return null;
    if (how === 'back') return free.slice().sort((a, c) => hyp(a.p, this.econAiMap().defC) - hyp(c.p, this.econAiMap().defC))[0];
    const byLane = {};
    for (const h of free) if (!byLane[h.lane]) byLane[h.lane] = h;
    const firsts = Object.values(byLane);
    return how === 'any' ? free[(Math.random() * Math.min(free.length, 3)) | 0] : pick(firsts);
  },
  econAiRetake(T, S, Dd, bots, n) {
    const B = this.bomb, s = S.sites[B.site], left = this.econAiLeft();
    if (!s) return;
    const att = this.econAiAlive(B.att).length, def = this.econAiAlive(3 - B.att).length;
    if (!Dd.retake) {
      // gather at the defenders' stage closest to where most of us are
      const mid = centroid(bots.map((b) => b.pos)) || S.defC;
      const lane = s.defE.slice().sort((a, c) => hyp(a.stage, mid) - hyp(c.stage, mid))[0];
      Dd.retake = { stage: lane.stage, node: lane.node, go: false, t0: n, defuser: 0 };
      this.tacLog(T, `RETAKE ${B.site}: ${def}v${att}, gathering at ${xz(lane.stage)}`);
    }
    const R = Dd.retake;
    // the defuser: a kit first, then whoever is closest
    const cands = bots.map((b) => [b, hyp(b.pos, B.p) / RUN + (b.ec.kit ? ECON.kitDefuse : BOMB.defuse) + (b.ec.kit ? 0 : 1.5)]).sort((a, c) => a[1] - c[1]);
    const best = cands[0];
    if (best && (!R.defuser || !bots.some((b) => b.id === R.defuser))) R.defuser = best[0].id;
    if (Dd.save) return;
    const dfz = this.players.get(R.defuser), dfzT = dfz ? hyp(dfz.pos, B.p) / RUN + (dfz.ec.kit ? ECON.kitDefuse : BOMB.defuse) : 99;
    const humansLeft = this.econAiAlive(3 - B.att).some((p) => !p.isBot);
    if ((left < dfzT - 0.4 && !(B.act && B.act.kind === 'defuse')) || (def === 1 && att >= 3 && !(dfz && dfz.ec.kit && left > dfzT + 6) && !humansLeft)) {
      Dd.save = true;
      Dd.saveWhy = left < dfzT ? `${r1(left)}s on the fuse, the defuse needs ${r1(dfzT)}s` : `1v${att} with no time for a kit defuse`;
      this.tacLog(T, `defenders SAVE: ${Dd.saveWhy}`);
      return;
    }
    if (!R.go) {
      const far = bots.filter((b) => hyp(b.pos, R.stage) > 10 && hyp(b.pos, B.p) > 12);
      const urgent = left < dfzT + hyp(R.stage, B.p) / RUN + 5;
      if (!far.length || urgent || n - R.t0 > 14000) {
        R.go = true;
        this.tacLog(T, `retake GO: ${far.length ? (urgent ? 'no time to wait' : 'waited long enough') : 'grouped up'} (${def}v${att}, defuser ${this.econAiName(R.defuser)}${dfz && dfz.ec.kit ? ' with pliers' : ''})`);
        // utility: frags on the post-plant spots that see the bomb, a smoke between them and the bomb
        for (const b of bots) {
          const it = b.ec.it;
          if (!it || it.n <= 0) continue;
          if (it.id === 'smoke') { const e = s.attE[0] ? s.attE[0].entry : s.c; (R.util ||= []).push({ id: b.id, i: 'smoke', at: [B.p[0] * 0.6 + e[0] * 0.4, B.p[1], B.p[2] * 0.6 + e[2] * 0.4], done: false }); }
          else if (it.id === 'frag') { const ps = T.seen.filter((x) => x.by !== B.att && hyp(x.p, B.p) < 26); if (ps.length) (R.util ||= []).push({ id: b.id, i: 'frag', at: pick(ps).p, done: false }); }
        }
      }
    }
  },

  // ---------------------------------------------------------- one bot's goal (econBotGoal asks this first)
  econAiGoal(b) {
    const B = this.bomb, ec = this.ec;
    if (!ec || !ec.tac || ec.tac.n !== B.n || B.ph === 'done' || B.between) return null;
    const T = ec.tac, S = this.econAiMap(), n = now();
    const g = b.team === B.att ? this.econAiAttGoal(b, T, S, n) : this.econAiDefGoal(b, T, S, n);
    b.ai.ecTac = g ? g.tac : '';
    return g;
  },
  econAiAttGoal(b, T, S, n) {
    const B = this.bomb, A = T.A;
    if (!A) return null;
    const s = S.sites[A.site];
    if (A.phase === 'save') return this.econAiTo(b, S.attC, this.econAiNodeOf(S.attC), 'save', { r: 3, force: true, tac: 'save' });
    if (B.drop && B.ph === 'live' && this.dropChasers().includes(b.id)) return null; // the dropped bomb: the default fetch
    if (B.ph === 'planted' && B.p) {
      // defuse going on: whoever sees the defuser shoots (botThink retargets), the rest push the bomb
      if (B.act && B.act.kind === 'defuse') {
        const dfz = this.players.get(B.act.id);
        if (dfz && this.canSee([b.pos[0], b.pos[1] + PH.eye, b.pos[2]], [dfz.pos[0], dfz.pos[1] + 1, dfz.pos[2]])) { b.ai.target = dfz.id; b.ai.retarget = n + 700; return { p: b.pos, at: b.pos, r: 9, tac: 'hold', hold: true, look: B.p }; }
        return this.econAiTo(b, B.p, this.econAiNodeOf(B.p), 'bomb', { r: 1.5, tac: 'push' });
      }
      let sp = A.post.get(b.id);
      if (!sp) { sp = this.econAiPostSpot(b, A, s); A.post.set(b.id, sp); }
      return this.econAiTo(b, sp.p, sp.node, 'post' + xz(sp.p), { r: 1, tac: 'hold', hold: true, look: [B.p[0], B.p[1] - 0.6, B.p[2]] });
    }
    const g = A.groups.find((x) => x.ids.includes(b.id)) || A.groups[0];
    const l = s.attE[g.lane];
    if (A.phase === 'gather') {
      // walk the lane to the stage; mill about a little there (a carrier standing still drops the bomb as AFK)
      if (hyp(b.pos, l.stage) < 6) {
        if (!b.ai.mill || n > b.ai.mill.t) { const a = Math.random() * Math.PI * 2; b.ai.mill = { t: n + 2500, p: this.econAiStand(l.stage[0] + Math.cos(a) * 2.5, l.stage[2] + Math.sin(a) * 2.5, l.stage[1], 1.5, 3) || l.stage }; }
        return { p: b.ai.mill.p, at: b.ai.mill.p, r: 0.6, tac: 'stage', look: l.entry };
      }
      return this.econAiTo(b, l.stage, l.node, 'stage' + A.site + g.lane, { r: 1.5, tac: 'gather', look: l.entry });
    }
    // execute. utility first (thrown from wherever it lands), then the site
    if (n - A.execAt < 9000) for (const u of A.util) if (!u.done && u.id === b.id && this.econAiThrowAt(b, u)) return { p: b.pos, at: b.pos, r: 9, tac: 'throw', hold: true };
    if (B.carrier === b.id) {
      const sp = this.econAiPlantSpot(b, A, s, g);
      const onSite = !!siteAt(this.map, b.pos);
      const mates = this.econAiBots(B.att).filter((o) => o !== b && siteAt(this.map, o.pos)).length;
      const wait = !onSite && !mates && n - A.execAt < 4500 && this.econAiBots(B.att).length > 1; // let someone else take the first fight
      if (wait) return this.econAiTo(b, l.entry, this.econAiNodeOf(l.entry), 'entry' + A.site + g.lane, { r: 5, tac: 'stack', look: s.c });
      const t = this.players.get(b.ai.target), fight = t && t.alive && b.ai.seenAt && d3(t.pos, b.pos) < 30;
      const there = hyp(b.pos, sp.p) < 1.2 || (onSite && hyp(b.pos, sp.p) < 3 && b.ai.plantStuck && n > b.ai.plantStuck);
      if (onSite && !fight && there) return { p: b.pos, use: true, r: 99, force: true, tac: 'plant' };
      if (hyp(b.pos, sp.p) < 3) { if (!b.ai.plantStuck) b.ai.plantStuck = n + 2500; } else b.ai.plantStuck = 0;
      if (onSite && fight && n - A.execAt > 25000 && this.econAiLeft() < 20) return { p: b.pos, use: true, r: 99, force: true, tac: 'plant' }; // out of time: plant anyway
      return this.econAiTo(b, sp.p, sp.node, 'plant' + A.site, { r: 0, force: !fight, tac: 'carry' });
    }
    // everyone else clears a hold (where the defenders sit), one each, then holds it
    let c = b.ai.clear;
    if (!c || c.n !== B.n) {
      const taken = new Set(this.econAiBots(B.att).map((o) => o.ai.clear && o.ai.clear.n === B.n && o.ai.clear.h).filter(Boolean));
      const hs = s.holds.filter((h) => !taken.has(h)).sort((a, c2) => (a.lane === g.lane ? 0 : 1) - (c2.lane === g.lane ? 0 : 1) || hyp(a.p, l.entry) - hyp(c2.p, l.entry));
      c = b.ai.clear = { n: B.n, h: hs[0] || s.holds[0] || { p: s.c, node: -1, look: s.c } };
    }
    const h = c.h;
    return this.econAiTo(b, h.p, h.node, 'clear' + xz(h.p), { r: 1.2, tac: 'clear', look: s.c });
  },
  econAiNodeOf(q) { // cached: a bomb or spawn point keeps its waypoint
    const g = this.map.graph ? null : this.econAiGraph();
    if (!g) return -1;
    const S = this.econAiMap(), k = xz(q);
    S.nodes ||= new Map();
    if (!S.nodes.has(k)) S.nodes.set(k, this.econAiNode(g, q));
    return S.nodes.get(k);
  },
  econAiPlantSpot(b, A, s, g) {
    if (b.ai.plant && b.ai.plant.n === this.bomb.n && b.ai.plant.site === A.site) return b.ai.plant.s;
    const list = s.plants[g.lane] || s.plants[0] || [];
    const sp = list.length ? list[Math.random() < 0.7 ? 0 : (Math.random() * list.length) | 0] : { p: s.c, node: -1 };
    b.ai.plant = { n: this.bomb.n, site: A.site, s: sp };
    return sp;
  },
  // after the plant: a spot that sees the bomb from cover, out of the defenders' entries' sight, apart from teammates
  econAiPostSpot(b, A, s) {
    const B = this.bomb, bp = B.p, taken = [...A.post.values()];
    let best = null, bs = -1e9;
    for (const q of s.grid) {
      const d = hyp(q.p, bp);
      if (d < 6 || d > 24 || Math.abs(q.p[1] - bp[1]) > 3) continue;
      if (taken.some((o) => hyp(o.p, q.p) < 4)) continue;
      const e = [q.p[0], q.p[1] + PH.eye, q.p[2]], c = [bp[0], bp[1] + 0.4, bp[2]], v = [c[0] - e[0], c[1] - e[1], c[2] - e[2]], l = Math.hypot(...v);
      if (raycast(e, v.map((x) => x / l), l, this.boxes)) continue;
      let sc = 5 - Math.abs(d - 13) * 0.25 - hyp(q.p, b.pos) * 0.05;
      for (const de of s.defE) { if (this.econAiSees(q.p, de.entry)) sc -= 2; sc += this.econAiCover(q.p, de.entry) * 2; }
      if (sc > bs) { bs = sc; best = q; }
    }
    return best || { p: bp, node: -1 };
  },
  econAiDefGoal(b, T, S, n) {
    const B = this.bomb, Dd = T.Dd;
    if (!Dd) return null;
    if (B.ph === 'planted' && B.p && Dd.retake) {
      const R = Dd.retake;
      if (Dd.save) return this.econAiTo(b, S.defC, this.econAiNodeOf(S.defC), 'save', { r: 3, force: true, tac: 'save' });
      for (const u of R.util || []) if (!u.done && u.id === b.id && this.econAiThrowAt(b, u)) return { p: b.pos, at: b.pos, r: 9, tac: 'throw', hold: true };
      const near = hyp(b.pos, B.p) < 12;
      if (!R.go && !near) return this.econAiTo(b, R.stage, R.node, 'retake' + B.site, { r: 2, tac: 'regroup', look: B.p });
      if (b.id === R.defuser) {
        const t = this.players.get(b.ai.target), seen = t && t.alive && b.ai.seenAt && d3(t.pos, b.pos) < 35;
        const left = this.econAiLeft(), need = (b.ec.kit ? ECON.kitDefuse : BOMB.defuse) + 0.3;
        const crit = left < need + hyp(b.pos, B.p) / RUN + 2.5;
        const close = hyp(b.pos, B.p) < 8;
        if (seen && !crit) return this.econAiTo(b, B.p, this.econAiNodeOf(B.p), 'bomb', { r: BOMB.defuseRange - 0.6, tac: 'retake' }); // fight first
        return { p: close ? B.p : this.econAiGo(b, B.p, this.econAiNodeOf(B.p), 'bomb'), at: B.p, use: close, r: BOMB.defuseRange - 0.6, force: true, tac: 'defuse' };
      }
      // cover the defuser: stand a few metres off the bomb toward where the attackers come from
      const ck = B.n + ':' + xz(B.p);
      if (!b.ai.cover || b.ai.cover.k !== ck) { const a = (b.id * 2.4) % (Math.PI * 2); b.ai.cover = { k: ck, q: this.econAiStand(B.p[0] + Math.cos(a) * 5, B.p[2] + Math.sin(a) * 5, B.p[1], 2, 3) || B.p }; }
      const q = b.ai.cover.q;
      return this.econAiTo(b, q, this.econAiNodeOf(q), 'cover' + B.site, { r: 1.5, tac: 'cover', look: S.attC });
    }
    const a = Dd.assign.get(b.id);
    if (!a) { const s0 = Object.values(S.sites)[0]; Dd.assign.set(b.id, { site: s0.id, spot: this.econAiPickHold(s0, new Set(), 'any') }); return null; }
    const s = S.sites[a.site], h = a.spot;
    if (process.env.JF_TAC_TRACE && h && n - (b.ai.trT || 0) > 2000) { b.ai.trT = n; const g = this.econAiGraph(); console.log(`[trace] ${b.name} at ${xz(b.pos)} -> spot ${xz(h.p)} node ${h.node}${g && h.node >= 0 ? ' ' + g.pts[h.node].join(',') : ''} route ${(b.ai.rnodes || []).map((i) => g.pts[i].map(Math.round).join(',')).join(' > ')} ri ${b.ai.ri} direct ${b.ai.direct}`); }
    if (!h) return this.econAiTo(b, s.c, this.econAiNodeOf(s.c), 'site' + a.site, { r: 2, tac: 'hold', look: S.attC });
    return this.econAiTo(b, h.p, h.node, 'hold' + xz(h.p), { r: 0.9, tac: 'hold', hold: true, look: h.look });
  },

  // ---------------------------------------------------------- moving and aiming (botThink, after the walk is planned)
  // holding: stand on the spot and watch the angle; when someone shows up, shoot from the spot instead of charging
  econAiHold(b, goal, t, wx, wz, dt) {
    const ai = b.ai, at = goal.at || goal.p, gl = Math.hypot(at[0] - b.pos[0], at[2] - b.pos[2]);
    const fighting = t && t.alive && ai.seenAt;
    if (!goal.use && this.projectiles.size) {
      for (const pr of this.projectiles.values()) {
        if (pr.k !== 'frag' || pr.o === b.id) continue;
        const o = this.players.get(pr.o);
        if (o && o.team === b.team) continue;
        const dx = b.pos[0] - pr.p[0], dz = b.pos[2] - pr.p[2], d = Math.hypot(dx, dz);
        if (d < 8 && Math.abs(b.pos[1] - pr.p[1]) < 4) return [dx / (d || 1), dz / (d || 1)]; // run
      }
    }
    if (goal.hold && gl < Math.max(1.6, goal.r + 0.6) && !goal.use) {
      if (fighting) { const s = ai.strafeDir * 0.12; return [Math.cos(b.yaw) * s, -Math.sin(b.yaw) * s]; } // a tiny jiggle, no charge (moving ruins your aim)
      if (gl < goal.r) { wx = 0; wz = 0; }
    }
    // moving wrecks a gun's aim in this mode (shared/tactical.js): with someone in sight and in range, stop to shoot
    if (fighting && !goal.force) {
      const w = WEAPONS[b.w], P = patternOf(b.w), t2 = t && Math.hypot(t.pos[0] - b.pos[0], t.pos[2] - b.pos[2]);
      if (w && w.kind === 'hitscan' && P && P.move >= 0.7 && t2 < Math.min(w.range || 60, 45)) { wx *= 0.12; wz *= 0.12; }
    }
    if (goal.look && !fighting && (gl < 6 || goal.tac === 'stage' || goal.tac === 'stack')) {
      const e = [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], dx = goal.look[0] - e[0], dy = goal.look[1] + 1.1 - e[1], dz = goal.look[2] - e[2];
      const yaw = Math.atan2(-dx, -dz), want = Math.atan2(dy, Math.hypot(dx, dz));
      let d = yaw - b.yaw; d = ((d + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
      b.yaw += d * Math.min(1, 6 * dt);
      b.pitch += (want - b.pitch) * Math.min(1, 6 * dt);
    }
    return [wx, wz];
  },
  // throw item u.i so it lands near u.at: try arcs from low to high and take the first that gets there without hitting
  // a wall on the way. false = not from here (keep walking)
  econAiThrowAt(b, u) {
    const e = b.ec;
    if (!e.it || e.it.id !== u.i || e.it.n <= 0) { u.done = true; return false; }
    if (hyp(b.pos, u.at) > 30 || now() - (b.ai.throwT || 0) < 900) return false;
    const arc = this.econAiArc(b, u.at, u.i);
    if (!arc) return false;
    b.yaw = Math.atan2(-arc[0], -arc[2]); b.pitch = Math.asin(Math.max(-1, Math.min(1, arc[1])));
    b.ai.throwT = now();
    const before = e.it.n;
    this.econItem(b, { i: u.i, o: [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], d: arc }, false);
    if (!e.it || e.it.n < before) {
      u.done = true;
      const T = this.ec.tac;
      if (T) this.tacLog(T, `${b.name} throws a ${u.i === 'smoke' ? 'smoke' : 'frag'} at ${xz(u.at)}`);
    }
    return true;
  },
  econAiArc(b, at, item) {
    const w = WEAPONS[item === 'smoke' ? 'smokegren' : 'frag'];
    const o = [b.pos[0], b.pos[1] + PH.eye, b.pos[2]], hx = at[0] - o[0], hz = at[2] - o[2], hl = Math.hypot(hx, hz) || 1;
    let best = null, be = 4;
    for (let th = -0.15; th < 1.2; th += 0.06) {
      const d = [Math.cos(th) * hx / hl, Math.sin(th), Math.cos(th) * hz / hl];
      const p = [o[0] + d[0] * 0.7, o[1] + d[1] * 0.7, o[2] + d[2] * 0.7], v = [d[0] * w.speed + b.vel[0] * 0.35, d[1] * w.speed + 3 + b.vel[1] * 0.35, d[2] * w.speed + b.vel[2] * 0.35];
      let land = null;
      for (let k = 0; k < 90 && !land; k++) {
        const dt = 0.035, np = [p[0] + v[0] * dt, p[1] + v[1] * dt, p[2] + v[2] * dt];
        const seg = [np[0] - p[0], np[1] - p[1], np[2] - p[2]], sl = Math.hypot(...seg);
        const h = raycast(p, seg.map((x) => x / sl), sl, this.boxes);
        if (h) land = h.point; else { p[0] = np[0]; p[1] = np[1]; p[2] = np[2]; v[1] -= w.grav * dt; }
      }
      if (!land) continue;
      const err = Math.hypot(land[0] - at[0], land[2] - at[2]) + Math.max(0, Math.abs(land[1] - at[1]) - 1) * 2;
      if (err < be) { be = err; best = d; if (err < 1.2) break; }
    }
    return best;
  },

  // ---------------------------------------------------------- buying: one plan per team and round
  econAiBuyPlan(team) {
    const T = this.econAiState();
    if (T.buy[team]) return T.buy[team];
    const B = this.bomb, att = team === B.att, ec = this.ec;
    const bots = this.fighters().filter((p) => p.isBot && p.team === team && p.ec && p.alive && !p.ec.out);
    const pistol = B.n === 1 || B.n === BOMB.swapAfter + 1;
    const lastHalf = B.n === BOMB.swapAfter, enemyMP = B.wins[3 - team] >= BOMB.wins - 1, ourMP = B.wins[team] >= BOMB.wins - 1;
    const kit = att ? 0 : GEAR.kit.price;
    const hasGun = (p) => usable(p.ec.sl.primary);
    const fullCost = (p) => (hasGun(p) ? 0 : weaponPrice('ar')) + 1000 + kit + 300; // rifle, vest + bucket, (pliers), a grenade
    const nextLoss = ECON.loss[Math.min(ECON.loss.length, (ec.lose[team] || 0) + 1) - 1];
    const plan = { mode: 'eco', why: '', gifts: new Map(), role: new Map() };
    const total = bots.reduce((s, p) => s + p.ec.$, 0), need = bots.reduce((s, p) => s + fullCost(p), 0);
    const canFull = bots.filter((p) => p.ec.$ >= fullCost(p)).length;
    if (!bots.length) plan.mode = 'eco';
    else if (pistol) { plan.mode = 'pistol'; plan.why = 'pistol round'; }
    else if (canFull >= Math.ceil(bots.length * 0.6) || total >= need) { plan.mode = 'full'; plan.why = `${canFull}/${bots.length} can full-buy (team ${total} of ${need})`; }
    else if (enemyMP || lastHalf) { plan.mode = 'force'; plan.why = enemyMP ? 'they are on match point' : 'last round of the half'; }
    else if (!(ec.lose[team] || 0) && total / bots.length >= 1900) { plan.mode = 'force'; plan.why = 'won the last round: keep the pressure on'; }
    else {
      const nextFull = bots.filter((p) => p.ec.$ + nextLoss >= fullCost(p)).length;
      const avg = total / bots.length;
      if (nextFull >= Math.ceil(bots.length * 0.6)) { plan.mode = 'eco'; plan.why = `saving: a loss (+${nextLoss}) still means a full buy next round`; }
      else if (avg >= 2000) { plan.mode = 'force'; plan.why = `saving wouldn't get a full buy next round (avg ${Math.round(avg)})`; }
      else { plan.mode = 'eco'; plan.why = `broke (avg ${Math.round(avg)}), building money`; }
    }
    if (ourMP && plan.mode === 'eco' && total / Math.max(1, bots.length) >= 1900) { plan.mode = 'force'; plan.why = 'match point: no saving now'; }
    // full buy: the rich buy a rifle for teammates who can't afford one
    if (plan.mode === 'full') {
      const poor = bots.filter((p) => !hasGun(p) && p.ec.$ < weaponPrice('ar') + GEAR.vest.price).sort((a, c) => a.ec.$ - c.ec.$);
      const rich = bots.filter((p) => p.ec.$ - fullCost(p) >= weaponPrice('ar') + 300).sort((a, c) => c.ec.$ - a.ec.$);
      for (const p of poor) { const r = rich.shift(); if (!r) break; plan.gifts.set(r.id, p.id); }
    }
    // utility roles: attackers bring two smokers (the rest frags); defenders frags, one smoke for retakes
    bots.slice().sort((a, c) => a.id - c.id).forEach((p, i) => plan.role.set(p.id, att ? (i < 2 ? 'smoke' : 'frag') : i === 0 ? 'smoke' : 'frag'));
    T.buy[team] = plan;
    this.tacLog(T, `${att ? 'ATTACK' : 'DEFENSE'} buy: ${plan.mode.toUpperCase()} (${plan.why})${plan.gifts.size ? `, ${plan.gifts.size} rifle(s) bought for teammates` : ''}`);
    return plan;
  },
  // one bot's shopping, by its team's plan (econBotBuy). true = handled
  econAiBuy(b) {
    if (!(this.map.sites || []).length) return false;
    const plan = this.econAiBuyPlan(b.team), e = b.ec, B = this.bomb, att = b.team === B.att;
    const buy = (k, id) => this.econBuy(b, { k, id }, true);
    const gun = (list, keep) => { const ok = list.filter((id) => econWeapon(id) && weaponPrice(id) != null && weaponPrice(id) + keep <= e.$); return ok.length > 0 && buy('w', pick(ok)); };
    const util = (n) => { const id = plan.role.get(b.id) || 'frag', s = itemSpec(id); for (let i = 0; i < n && s && e.$ >= s.price; i++) if (!buy('i', id)) break; };
    const hasGun = usable(e.sl.primary);
    e.mode = plan.mode;
    if (plan.mode === 'pistol') {
      const r = Math.random();
      if (att) { if (r < 0.55) buy('g', 'vest'); else util(2); }
      else if (r < 0.4) buy('g', 'vest'); else { buy('g', 'kit'); util(1); }
      if (Math.random() < 0.4) gun(SIDEARM_BUYS, 0); // whatever's left: a better sidearm
    } else if (plan.mode === 'full') {
      const gift = plan.gifts.get(b.id);
      if (!hasGun) {
        const sniper = econWeapon('sniper') && e.$ >= weaponPrice('sniper') + 1400 + (gift ? 3000 : 0) && Math.random() < 0.25;
        if (!(sniper && buy('w', 'sniper')) && !gun(RIFLES, 1000)) gun(RIFLES, 650) || gun(FORCE, 650);
      }
      if (gift) this.econAiGift(b, gift);
      if (!buy('g', 'helm')) buy('g', 'vest');
      if (!att && e.$ >= GEAR.kit.price) buy('g', 'kit');
      util(2);
    } else if (plan.mode === 'force') {
      if (!hasGun && !gun(FORCE, 650) && !gun(FORCE, 0)) gun(['marbles', 'akimbo', 'sawnoff'], 0); // no rifle money: a shotgunny sidearm
      buy('g', 'vest');
      if (!att && e.$ >= GEAR.kit.price + 300) buy('g', 'kit');
      util(1);
    } else if (att && e.$ >= 2500) util(1); // eco: keep the money (a smoke at most)
    if (e.sl.primary && e.sl.primary.lim && e.sl.primary.m + e.sl.primary.r < 10 && refillPrice(e.sl.primary.id) <= e.$) buy('w', e.sl.primary.id);
    return true;
  },
  // buy a second rifle and leave the first at our feet for teammate `to` (it walks over and picks it up)
  econAiGift(b, to) {
    const e = b.ec, mate = this.players.get(to);
    if (!mate || !mate.alive || !mate.ec || usable(mate.ec.sl.primary) || !usable(e.sl.primary)) return;
    const before = new Set(this.ec.drops.keys());
    const id = e.sl.primary.id === 'ar' ? 'redline' : 'ar'; // the same gun again would only refill it: buy the other rifle, ours drops
    if (!econWeapon(id) || e.$ < weaponPrice(id) || !this.econBuy(b, { k: 'w', id }, true)) return;
    const d = [...this.ec.drops.values()].find((x) => !before.has(x.id) && x.k === 'w');
    if (!d) return;
    mate.ai.gift = d.id;
    const T = this.ec.tac;
    if (T) this.tacLog(T, `${b.name} drops a ${WEAPONS[d.x.id].name} for ${mate.name}`);
  },

  // ---------------------------------------------------------- deaths and round ends (for the info and the log)
  econAiDeath(t, killer) {
    const ec = this.ec, B = this.bomb;
    if (!ec || !ec.tac || !B || B.ph === 'done') return;
    const T = ec.tac;
    T.dead.push({ team: t.team, id: t.id, p: t.pos.slice(), n: now() });
    if (killer && killer !== t && killer.team !== t.team) T.seen.push({ by: t.team, id: killer.id, p: killer.pos.slice(), n: now(), carrier: B.carrier === killer.id });
    const k = (T.k ||= { 1: 0, 2: 0 });
    if (t.team) k[t.team]++;
    const side = (p) => (p.team === B.att ? 'att' : 'def');
    const how = killer && killer !== t ? `${killer.name} (${side(killer)}, ${killer.isBot && killer.ai && killer.ai.ecTac ? killer.ai.ecTac + ', ' : ''}${killer.w}) kills ${t.name} (${side(t)}${t.isBot && t.ai && t.ai.ecTac ? ', ' + t.ai.ecTac : ''})` : `${t.name} (${side(t)}) dies`;
    this.tacLog(T, (T.first ? '' : 'first blood: ') + how);
    T.first = 1;
  },
  econAiRoundEnd(win, why) {
    const ec = this.ec, B = this.bomb;
    if (!ec) return;
    const T = this.econAiState(), att = B.att, mem = ec.tacMem || (ec.tacMem = {});
    if (T.A) {
      (mem.hit ||= {})[att] = T.A.site;
      (mem.lostAt ||= {})[att] = win === att ? null : T.A.site;
    }
    const aliveA = this.econAiAlive(att).length, aliveD = this.econAiAlive(3 - att).length; // (after a bomb blast: whoever it left)
    const story = {
      elim: win === att ? 'attackers wiped the defenders' : 'defenders wiped the attackers',
      time: 'time ran out with no plant', defused: 'the bomb was defused', exploded: 'the bomb exploded',
    }[why] || why;
    const buy = `buys: att ${T.buy[att] ? T.buy[att].mode : '-'} vs def ${T.buy[3 - att] ? T.buy[3 - att].mode : '-'}`;
    const line = `ROUND ${B.n} -> ${win === att ? 'ATTACK' : 'DEFENSE'} (team ${win}) wins: ${story} | ${buy} | alive ${aliveA} att / ${aliveD} def | deaths att ${(T.k && T.k[att]) || 0}, def ${(T.k && T.k[3 - att]) || 0}`;
    T.result = { n: B.n, win, att, why, line, log: T.log.slice() };
    (ec.tacRounds ||= []).push(T.result);
    if (LOG) console.log(`[round] ${line}`);
  },
};

export default M;
