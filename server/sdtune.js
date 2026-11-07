// Search & Destroy tuning on the server (owner, 2026-11-07: "search and destroy should be 5v5! ... match like valorants
// guns and dmg"). Installed from installEcon. It only wraps Room methods and only changes anything in Plant & Defuse:
//   - damage: every gun in the S&D table (shared/sdgun.js) does head / body / legs damage with range falloff, measured
//     here from server positions. the client says how many of its hits were legs (lg), like it already says heads (h)
//   - 5v5: a Plant & Defuse Bots room (or bots lobby) holds 10 fighters, bots topping up and making room for people;
//     an Online Plant & Defuse lobby takes at most 10 humans
import { WEAPONS } from '../shared/weapons.js';
import { sdRow, sdDamage, BOT_LEGS } from '../shared/sdgun.js';

export const SD5 = { size: 10 }; // fighters in a Plant & Defuse room: 5 a side
if (process.env.JF_SD_SIZE) SD5.size = Math.max(2, Math.min(16, Number(process.env.JF_SD_SIZE) | 0 || SD5.size)); // test knob: a smaller (or bigger) room
const LOG = !!process.env.JF_SD_LOG; // test knob: print every S&D hit (zones, range, damage)
const clampInt = (v, lo, hi) => (Number.isInteger(v) ? Math.max(lo, Math.min(hi, v)) : lo);

export function installSdTune(Room) {
  const P = Room.prototype;
  const orig = { applyHitscan: P.applyHitscan, onHit: P.onHit, botWant: P.botWant };
  if (!orig.applyHitscan || !orig.onHit || !orig.botWant) throw new Error('sdtune: Room is missing applyHitscan / onHit / botWant');

  // the leg count rides on the hit message; applyHitscan reads it from p for the length of this one call
  P.onHit = function (p, m) {
    if (!this.isEcon() || !m || m.t !== 'hit') return orig.onHit.call(this, p, m);
    p.sdLg = typeof m.lg === 'number' ? m.lg : 0;
    try { return orig.onHit.call(this, p, m); } finally { p.sdLg = 0; }
  };
  P.applyHitscan = function (p, t, wid, n, h, d, mul = 1) {
    if (!this.isEcon() || !sdRow(wid)) return orig.applyHitscan.call(this, p, t, wid, n, h, d, mul);
    if (this.parryShot(p, t, wid, n, h, d, mul)) return; // (no katanas on sale, but a parry is a parry)
    const rx = this.rifleShot(p, t, wid, h); // the rifle pack's timing checks (a burst is still three) stay; its bonuses don't
    if (!rx) return;
    const w = WEAPONS[wid], pellets = w.pellets || 1;
    let lg;
    if (p.isBot) { lg = 0; for (let i = 0; i < n - h; i++) if (Math.random() < BOT_LEGS) lg++; }
    else lg = clampInt(p.sdLg, 0, n - h);
    const body = n - h - lg, dist = Math.hypot(t.pos[0] - p.pos[0], t.pos[1] - p.pos[1], t.pos[2] - p.pos[2]);
    const dmg = (sdDamage(wid, 'h', dist) * h + sdDamage(wid, 'b', dist) * body + sdDamage(wid, 'l', dist) * lg) * mul;
    const k = (w.kb || 0) * n;
    if (LOG) console.log(`[sdhit] ${p.name} ${wid} -> ${t.name} ${Math.round(dist)}m h${h} b${body} l${lg} x${mul} = ${Math.round(dmg)}`);
    this.hurt(t, p, wid, dmg, [d[0] * k, d[1] * k + (w.kbUp || 0) * (n / pellets), d[2] * k], { hs: h > 0 });
  };

  // ---------------------------------------------------------- 5v5
  const sdGame = (room) => (room.lobby ? room.lobby.next : room.game) === 'bomb';
  P.botWant = function () {
    if (!sdGame(this) || (this.lobby && this.lobby.online) || (this.mode !== 'bots' && !this.lobby)) return orig.botWant.call(this);
    const h = this.humans().filter((p) => !p.watch).length;
    return Math.max(0, SD5.size - Math.max(1, h));
  };
  // the lobby methods are added after installEcon (installLobby): wrap them once the module has finished installing
  queueMicrotask(() => {
    const lo = { lobbySize: P.lobbySize, lobbyOpen: P.lobbyOpen };
    if (lo.lobbySize) P.lobbySize = function () { return sdGame(this) ? SD5.size : lo.lobbySize.call(this); };
    if (lo.lobbyOpen) P.lobbyOpen = function (mode, kind) {
      if (!lo.lobbyOpen.call(this, mode, kind)) return false;
      return !(sdGame(this) && this.lobby && this.lobby.online && this.lobbyHumans().length >= SD5.size); // online S&D: 10 people
    };
  });
}
