// the guns' first-person clips as Luau data (roblox/src/shared/Reloads.luau), read straight out of the web game:
//   public/js/reloads.js   RL          the reloads of ar, smg, revolver, shotgun, sniper (+ minigun, nailgun, water, scythe rifle)
//   public/js/rifles.js    ANIMS       the rifle pack: reloads, draws and the Yeehaw's lever_cycle
//   public/js/sidearms.js  SIDE_ANIMS  Plan B and Half a Shotgun: draws and reloads
//   public/js/anim.js                  pump_shotgun, bolt_sniper (the clips that play after a shot)
// each clip = the body keys (camera-space offsets, metres / radians), the sound events, and `ch`: the gun's own moving
// parts (mag, charging handle, pump, bolt, lever, hammer, feed cover, slide, hinge, cylinder, the whole-gun twirl).
// the off hand comes as `lh` = { { t, k, f } }: k 0 off screen..1 there, f what it follows (0 the gun, 1 the mag,
// 2 the charging handle, 3 the pump, 4 the bolt, 5 the cylinder, 6 / 7 shell 1 / 2; a fraction blends two), without
// the web's own offsets (Viewmodel puts the hand on each piece its own way). the hand-held props (`p_*`) are not
// ported. the Redline and the Marble
// Shotgun keep their hand-keyed clips in Anims.luau (tools/roblox/anims.mjs). no dependencies: the tables are cut out
// of the sources and evaluated on their own, because the files themselves import three.js and browser modules.
// run: node tools/roblox/reloads.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const read = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8').split(/\r?\n/);
const KDEF = "const PI = Math.PI, PI2 = PI * 2; const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });\n";
const cut = (src, a, b, what) => { if (a < 0 || b < 0) throw new Error(what + ' changed shape'); return src.slice(a, b + 1).join('\n'); };

// ---- reloads.js: magSwap + RL
let src = read('public/js/reloads.js');
let a = src.findIndex((l) => l.startsWith('const magSwap'));
let b = src.findIndex((l, i) => i > a && l.startsWith('const RL = {'));
let c = src.findIndex((l, i) => i > b && l.startsWith('};'));
const RL = new Function(KDEF + cut(src, a, c, 'reloads.js') + '\nreturn RL;')();

// ---- rifles.js: K, magSwap, rack, then Object.assign(ANIMS, { ... })
src = read('public/js/rifles.js');
a = src.findIndex((l) => l.startsWith('const K = '));
b = src.findIndex((l, i) => i > a && l.startsWith('Object.assign(ANIMS, {'));
c = src.findIndex((l, i) => i > b && l.startsWith('});'));
const RIFLES = new Function('const ANIMS = {};\n' + cut(src, a, c, 'rifles.js') + '\nreturn ANIMS;')();

// ---- sidearms.js: PI2, K, SIDE_ANIMS
src = read('public/js/sidearms.js');
a = src.findIndex((l) => l.startsWith('const PI2'));
b = src.findIndex((l, i) => i > a && l.startsWith('const SIDE_ANIMS = {'));
c = src.findIndex((l, i) => i > b && l.startsWith('};'));
const SIDE = new Function(cut(src, a, c, 'sidearms.js') + '\nreturn SIDE_ANIMS;')();

// ---- anim.js: the two follow-up clips, cut out by name
src = read('public/js/anim.js');
const one = (name) => {
  const i = src.findIndex((l) => l.startsWith(`  ${name}: {`));
  const j = src.findIndex((l, k) => k >= i && l.includes('events:'));
  return new Function(KDEF + `return ({ ${cut(src, i, j, 'anim.js ' + name).replace(/,\s*$/, '')} }).${name};`)();
};
// the pump and the bolt move by the clip's clock in the web game (glbkit.js stepParts): the same timings, as channels
const FOLLOW = {
  pump_shotgun: { ...one('pump_shotgun'), ch: { pump: [[0, 0], [0.1, 1], [0.17, 0]] } },
  bolt_sniper: { ...one('bolt_sniper'), ch: { bolt: [[0, 0, 0], [0.12, 1, 0], [0.22, 1, 1], [0.3, 1, 0], [0.42, 0, 0]] } },
};
// the Revolver's twirl round the trigger finger after a tap, and the turn it makes per fanned shot (public/js/twirl.js
// does these with a spring; here they are clips: a whole forward turn, the arm reaching out while it goes round)
const KK = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth') => ({ t, p, r, e, s: 1 });
const TWIRL = {
  twirl_revolver: { keys: [KK(0), KK(0.1, [-0.025, -0.02, -0.1], [0, 0.4, -0.15]), KK(0.2, [-0.02, -0.015, -0.08], [0, 0.3, -0.1]), KK(0.3)],
    ch: { twirl: [[0, 0], [0.24, -Math.PI * 2]] }, events: [[0.02, 'whoosh']] },
  fan_revolver: { keys: [KK(0), KK(0.05, [-0.015, -0.01, -0.06], [0, 0.25, -0.1]), KK(0.17)],
    ch: { twirl: [[0, 0], [0.165, -Math.PI * 2]] }, events: [] },
};

const SKIP = new Set(['redline', 'marbles']);
const PARTS = new Set(['mag', 'charge', 'pump', 'bolt', 'cyl', 'lever', 'lhammer', 'cover', 'twirl', 'belt', 'slide', 'hinge', 'shells', 'cock', 'box', 'cocker']);
// (the owner, 19 Nov 2026: "make sure guns have accurate ways to reload and parts that a normal gun would have or most of
// them at least!"; guns-remodel's audit) channels the web clips only had as sounds, timed to those sounds. rows are
// [t, down, back, tip] like a mag (GunParts): the Minigun's ammo box drops off at boxPop and the new one comes up and
// seats with the belt; the Nail Gun's strip slides out at the click and back in at nailIn
const EXTRA = {
  minigun: { box: [[0, 0, 0, 0], [0.42, 0, 0, 0], [0.5, -0.05, 0.01, 0], [0.72, -0.5, 0.06, 0], [1.9, -0.5, 0, 0], [2.12, -0.06, 0, 0], [2.18, 0.006, 0, 0], [2.26, 0, 0, 0]] },
  nailgun: { mag: [[0, 0, 0, 0], [0.28, 0, 0, 0], [0.36, -0.04, 0.02, 0], [0.52, -0.36, 0.06, 0], [0.74, -0.36, 0, 0], [0.88, -0.05, 0, 0], [0.93, 0.006, 0, 0], [0.98, 0, 0, 0]] },
};
// Lefty & Righty's parts in its 1.5 s per-hand reload (the gun's own dip is the hold session's, Viewmodel: these keys
// stay still): the mag drops and a fresh one goes in, then the cocker (its charging handle) is pulled
const KK0 = (t) => ({ t, p: [0, 0, 0], r: [0, 0, 0], e: 'smooth', s: 1 });
const AKIMBO = {
  reload_akimbo: { keys: [KK0(0), KK0(1.5)], events: [[0.14, 'magOut'], [1.0, 'magIn'], [1.26, 'chargeBack'], [1.34, 'chargeHome']],
    ch: { mag: [[0, 0, 0, 0], [0.12, 0, 0, 0], [0.2, -0.05, 0.01, 0], [0.36, -0.36, 0.06, 0], [0.7, -0.36, 0, 0], [0.94, -0.05, 0, 0], [1.0, 0.006, 0, 0], [1.05, 0, 0, 0]],
      cocker: [[0, 0], [1.24, 0], [1.3, 1], [1.38, 0]] } },
};
const WANT = /^(reload_|draw_|lever_cycle)/; // (no inspects: there is no inspect key on Roblox yet)
const n = (x) => String(Math.round(x * 10000) / 10000);
const v = (arr) => `{ ${arr.map(n).join(', ')} }`;
const eases = new Set();
let out = `--!strict
-- GENERATED by tools/roblox/reloads.mjs from the web game (public/js/reloads.js, rifles.js, sidearms.js, anim.js):
-- don't edit by hand. the guns' clips in first person, same shape as Anims.luau: keys = t (s), p offset (m, camera
-- space), r euler XYZ offset (rad), e ease into the key; events = { time, name } for the sounds; ch = the gun's own
-- moving parts, each a list of { t, value... } (GunParts.luau moves the pieces). Viewmodel merges these into Anims; a
-- gun with no reload of its own borrows reload_ar, stretched to its reload time.
return {
`;
const ids = [];
// the off hand's follow codes: reloads.js and rifles.js as they are; sidearms.js 1 the mag, 2 / 3 shell 1 / 2
const SIDE_F = (f) => (f < 2 ? f : f + 4);
function emit(name, r, mapF = (f) => f) {
  if (!Array.isArray(r.keys)) return;
  const dur = r.dur ?? r.keys[r.keys.length - 1].t;
  ids.push(name);
  out += `\t${name} = {\n\t\tdur = ${n(dur)},\n\t\tkeys = {\n`;
  for (const k of r.keys) { eases.add(k.e); out += `\t\t\t{ t = ${n(k.t)}, p = ${v(k.p)}, r = ${v(k.r)}, e = "${k.e}" },\n`; }
  out += `\t\t},\n\t\tevents = { ${(r.events || []).map(([t, nm]) => `{ ${n(t)}, "${nm}" }`).join(', ')} },\n`;
  const ch = Object.entries(r.ch || {}).filter(([k]) => PARTS.has(k));
  if (ch.length) out += `\t\tch = { ${ch.map(([k, rows]) => `${k} = { ${rows.map(v).join(', ')} }`).join(', ')} },\n`;
  const lh = r.ch && r.ch.lh;
  if (lh) out += `\t\tlh = { ${lh.map((row) => v([row[0], row[1], mapF(row[2] ?? 0)])).join(', ')} },\n`;
  out += '\t},\n';
}
for (const [id, r] of Object.entries(RL)) if (!SKIP.has(id)) emit('reload_' + id, EXTRA[id] ? { ...r, ch: { ...(r.ch || {}), ...EXTRA[id] } } : r);
for (const [name, r] of Object.entries(RIFLES)) if (WANT.test(name)) emit(name, r);
for (const [name, r] of Object.entries(SIDE)) if (WANT.test(name) && !name.includes('akimbo')) emit(name, r, SIDE_F);
for (const [name, r] of Object.entries(FOLLOW)) emit(name, r);
for (const [name, r] of Object.entries(TWIRL)) emit(name, r);
for (const [name, r] of Object.entries(AKIMBO)) emit(name, r);
out += '}\n';
fs.writeFileSync(path.join(ROOT, 'roblox/src/shared/Reloads.luau'), out);
console.log('clips:', ids.join(', '), '| eases:', [...eases].join(', '), '|', out.length, 'chars');
