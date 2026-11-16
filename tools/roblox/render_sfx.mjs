// JANKFIRE's sounds, take 2 (16 Nov 2026): every sound the Roblox game plays, rebuilt as layered synthesis. the
// first renders (render_guns / render_items / render_loot / render_sounds) copied the web game's Web Audio recipes:
// one oscillator and one filtered noise each, thin and toy-like. here each sound is built the way a recorded effect is
// mixed: a transient (the first milliseconds, which make it crisp), a body (its weight), detail (metal parts, glass,
// cloth, grit) and a tail (the room, echoes off the buildings across the street, a low rumble); then it is saturated,
// limited and peak-normalised, and its Roblox Volume is set from its measured loudness so the categories sit at fixed
// levels against each other (guns loudest, confirms above the gunfire, reload parts and footsteps under it).
// variants (Sounds named "<name>#2", "#3"... beside "<name>") come from the same recipe with another seed and small
// jitter; Sfx.luau picks one at random so repeats don't sound copied.
// no voices, no words, no music samples: all of it is maths. plain Node, no dependencies.
// run: node tools/roblox/render_sfx.mjs [only=name1,name2] [out=dir]   (default out: roblox/assets/sounds/v2)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  SR, N, zeros, db, rngFor, mix, gain, norm, env, ad, ahd, swell, glide, expRamp, white, pink, brown, filt, lp, hp, bp,
  lp2, hp2, osc, strike, partials, bell, sat, convVerb, echoes, finish, loudness, writeWav, peak,
} from './sfx_dsp.mjs';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const arg = (k) => { const a = process.argv.find((x) => x.startsWith(k + '=')); return a ? a.slice(k.length + 1) : null; };
const OUT = path.resolve(arg('out') || path.join(ROOT, 'roblox/assets/sounds/v2'));
const ONLY = arg('only') ? new Set(arg('only').split(',')) : null;
const { PI, sin, exp, min, max, abs, pow } = Math;

// every target loudness below is relative; CAL moves them all together (set so the guns land about where the
// first renders were, a touch louder: the owner's ears are used to that level)
const CAL = -9;

const DEFS = [];
// o: { cat, what, lu (target loudness heard at the Sound's Volume, LUFS), vars, fin (finish options), jitter }
const def = (name, o, fn) => DEFS.push({ name, vars: 1, ...o, fn });

// a shaped hump: rises as t^2 to `pk`, then decays
const hump = (pk, d) => (t) => (t < 0 ? 0 : t < pk ? (t / pk) * (t / pk) : exp(-(t - pk) / d));
const noteHz = (n) => 440 * pow(2, (n - 69) / 12); // MIDI note -> Hz

// ---------------------------------------------------------------- building blocks
function tick(R, s, f, d = 0.006, g = 1) { // a tiny pitched transient
  const t = white(s, R); hp2(t, f); env(t, ad(0.0001, d)); return gain(norm(t), g);
}
function thump(s, f0, f1, sw, d, drive = 1.8, atk = 0.0008) {
  const t = osc(s, glide(f0, f1, sw)); env(t, ad(atk, d)); sat(t, drive); return norm(t);
}
function airy(R, s, f, q, e, color = 'pink') { // filtered noise under an envelope; f can sweep
  const n = color === 'pink' ? pink(s, R) : white(s, R); filt(n, 'bp', f, q); env(n, e); return norm(n);
}
// the room a sound is in: room 0.45 (tight) .. 0.85 (big, about 1.7 s) sets the decay, damp how fast its top end dies
function roomOf(x, room = 0.6, damp = 0.45, hpHz = 150) {
  const w = convVerb(x, { rt60: 0.3 + (room - 0.4) * 3, hf0: 9000, hf1: 3200 - damp * 4000 }); hp(w, hpHz); return norm(w);
}

// a gunshot: crack (N-wave + hiss), blast (swept, saturated noise with the gun's body), thump (falling sine for the
// chest), the action's metal (struck resonators), and the tail (room + echoes + rumble)
function gun(R, J, o) {
  const len = o.len, out = zeros(len);
  const C = o.crack;
  const ck = white(len, R); env(ck, (t) => exp(-t / J(C.d))); hp2(ck, J(C.hp)); norm(ck); mix(out, ck, C.g);
  if (C.nw) { const T = N(C.nw / 1000), nw = new Float64Array(T + 1); for (let i = 0; i < T; i++) nw[i] = 1 - 2 * i / T; mix(out, nw, C.g); }
  const B = o.blast;
  const bl = (B.pink ? pink : white)(len, R);
  filt(bl, 'lp', glide(J(B.f0), J(B.f1), B.sw), 0.9);
  if (B.body) filt(bl, 'peak', J(B.body[0]), B.body[2], B.body[1]);
  env(bl, ahd(0.0003, B.hold ?? 0.003, J(B.d)));
  const dry = Float64Array.from(bl);
  norm(bl); sat(bl, B.drive ?? 2.5); mix(out, norm(bl), B.g);
  const T = o.thump;
  mix(out, thump(len, J(T.f0, 0.03), J(T.f1, 0.03), T.sw, J(T.d), T.drive ?? 1.8), T.g);
  for (const m of o.mech || []) {
    const s = strike(m.len ?? 0.08, R, m.modes.map(([f, q, g]) => [J(f, 0.03), q, g]), m.sharp ?? 0.0005);
    env(s, ad(0.0002, m.d ?? 0.02)); mix(out, norm(s), m.g, m.at);
  }
  const L = o.tail;
  if (L) {
    const src = Float64Array.from(dry); lp(src, L.lp ?? 2400); norm(src);
    if (L.verb) mix(out, roomOf(src, L.room ?? 0.6, L.damp ?? 0.45), L.verb);
    if (L.echo) mix(out, norm(echoes(src, L.echo, len)), L.g ?? 0.25);
    if (L.rumble) { const r = brown(len, R); lp2(r, L.rumble.lp ?? 220); env(r, ad(L.rumble.a ?? 0.006, J(L.rumble.d))); mix(out, norm(r), L.rumble.g); }
  }
  return out;
}

// the Redline's motor: a sawtooth + pulse at the engine's firing rate, rough like combustion, through a closing filter
function engine(R, s, f, { d = 0.06, cut = 2400, drive = 4, rise = 1.12, riseT = 0.05 } = {}) {
  const ff = (t) => f * (1 + (rise - 1) * min(1, t / riseT));
  const n = zeros(s);
  mix(n, osc(s, ff, 'saw'), 0.7);
  mix(n, osc(s, (t) => ff(t) * 0.5, 'pulse', 0, 0.3), 0.5);
  const am = white(s, R); lp(am, f * 0.8); norm(am);
  for (let i = 0; i < n.length; i++) n[i] *= 1 + 0.35 * am[i];
  filt(n, 'lp', glide(cut * 1.6, cut * 0.5, 0.04), 1.2);
  env(n, ad(0.002, d)); norm(n); sat(n, drive); return norm(n);
}

// glass marble / small hard thing clicking
function clink(R, J, s, f = 4300, d = 0.03) {
  const o = partials(s, [[J(f), 1, d], [J(f * 1.62), 0.55, d * 0.66], [J(f * 2.21), 0.3, d * 0.4]], R, 0.0002);
  mix(o, tick(R, s, 5000, 0.0004), 0.5);
  return norm(o);
}

// ================================================================= guns (the shot you hear most)
const RIFLE_ECHO = [[0.09, 1, 1900], [0.19, 0.55, 1300], [0.33, 0.25, 900]];
def('gun_ar', { cat: 'gun', what: 'Assault Rifle shot', lu: -11, vars: 3, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 0.75,
  crack: { g: 0.55, hp: 2600, d: 0.0011, nw: 0.5 },
  blast: { g: 1, f0: 7500, f1: 650, sw: 0.012, d: 0.032, body: [850, 4, 1], drive: 2.6 },
  thump: { g: 0.75, f0: 190, f1: 72, sw: 0.014, d: 0.05 },
  mech: [{ g: 0.12, at: 0.011, modes: [[2400, 35, 1], [3700, 45, 0.7], [5600, 55, 0.5]] }],
  tail: { lp: 2600, verb: 0.12, room: 0.55, echo: RIFLE_ECHO, g: 0.24, rumble: { g: 0.22, lp: 240, d: 0.1 } },
}));
def('gun_smg', { cat: 'gun', what: 'SMG shot', lu: -12, vars: 3, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 0.55,
  crack: { g: 0.6, hp: 3200, d: 0.0009 },
  blast: { g: 1, f0: 8500, f1: 950, sw: 0.008, d: 0.022, body: [1250, 4, 1.2], drive: 2.3 },
  thump: { g: 0.55, f0: 230, f1: 95, sw: 0.01, d: 0.03 },
  mech: [{ g: 0.14, at: 0.008, modes: [[3200, 40, 1], [4800, 50, 0.7], [7000, 60, 0.4]] }],
  tail: { lp: 3000, verb: 0.1, room: 0.45, echo: [[0.08, 1, 2100], [0.17, 0.45, 1400]], g: 0.18, rumble: { g: 0.12, lp: 260, d: 0.07 } },
}));
def('gun_burst', { cat: 'gun', what: 'Hat Trick shot (three-round burst)', lu: -11.5, vars: 3, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 0.7,
  crack: { g: 0.6, hp: 2800, d: 0.001, nw: 0.45 },
  blast: { g: 1, f0: 8000, f1: 750, sw: 0.01, d: 0.028, body: [1050, 4, 1.1], drive: 2.5 },
  thump: { g: 0.65, f0: 200, f1: 80, sw: 0.012, d: 0.042 },
  mech: [{ g: 0.12, at: 0.01, modes: [[2700, 40, 1], [4100, 50, 0.7], [6200, 60, 0.4]] }],
  tail: { lp: 2800, verb: 0.11, room: 0.5, echo: RIFLE_ECHO, g: 0.2, rumble: { g: 0.18, lp: 250, d: 0.09 } },
}));
def('gun_lmg', { cat: 'gun', what: 'Belt Sander shot (cold barrel; hot = louder and lower in Sfx.gun)', lu: -11, vars: 3, fin: { push: 5.5 } }, (R, J) => gun(R, J, {
  len: 0.8,
  crack: { g: 0.5, hp: 2300, d: 0.0012, nw: 0.6 },
  blast: { g: 1, f0: 6500, f1: 520, sw: 0.014, d: 0.04, body: [650, 5, 1], drive: 3 },
  thump: { g: 0.9, f0: 170, f1: 60, sw: 0.016, d: 0.065, drive: 2 },
  mech: [{ g: 0.13, at: 0.012, modes: [[1800, 30, 1], [2700, 40, 0.8], [4100, 50, 0.5]] }, { g: 0.06, at: 0.03, modes: [[3300, 40, 1], [5000, 50, 0.6]] }],
  tail: { lp: 2400, verb: 0.12, room: 0.6, echo: RIFLE_ECHO, g: 0.26, rumble: { g: 0.28, lp: 220, d: 0.12 } },
}));
def('gun_dmr', { cat: 'gun', what: 'Second Opinion shot', lu: -9.5, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 1.3,
  crack: { g: 0.8, hp: 2200, d: 0.0013, nw: 0.7 },
  blast: { g: 1, f0: 8500, f1: 450, sw: 0.016, d: 0.055, body: [700, 4, 0.9], drive: 3 },
  thump: { g: 0.95, f0: 160, f1: 50, sw: 0.02, d: 0.07, drive: 2 },
  mech: [{ g: 0.1, at: 0.016, modes: [[2000, 30, 1], [3100, 40, 0.7], [4600, 50, 0.4]] }],
  tail: { lp: 2200, verb: 0.15, room: 0.7, echo: [[0.13, 1, 1700], [0.28, 0.55, 1100], [0.5, 0.28, 800]], g: 0.3, rumble: { g: 0.36, lp: 200, d: 0.28 } },
}));
def('gun_sniper', { cat: 'gun', what: 'Sniper shot (a long crack that rolls off the buildings)', lu: -8.5, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 1.8,
  crack: { g: 0.9, hp: 2000, d: 0.0016, nw: 0.85 },
  blast: { g: 1, f0: 9000, f1: 350, sw: 0.018, d: 0.07, body: [600, 4, 0.8], drive: 3 },
  thump: { g: 1, f0: 140, f1: 42, sw: 0.03, d: 0.09, drive: 2.2 },
  tail: { lp: 2200, verb: 0.17, room: 0.8, echo: [[0.15, 1, 1600], [0.32, 0.6, 1100], [0.55, 0.32, 800], [0.82, 0.16, 600]], g: 0.34, rumble: { g: 0.5, lp: 180, d: 0.42 } },
}));
def('gun_shotgun', { cat: 'gun', what: 'Shotgun shot (the pump is its own clip)', lu: -9, fin: { push: 5.5 } }, (R, J) => gun(R, J, {
  len: 1.3,
  crack: { g: 0.5, hp: 1800, d: 0.002 },
  blast: { g: 1, f0: 5000, f1: 300, sw: 0.02, d: 0.08, body: [420, 5, 0.9], drive: 3, pink: true },
  thump: { g: 1, f0: 125, f1: 46, sw: 0.03, d: 0.08, drive: 2.2 },
  tail: { lp: 1800, verb: 0.16, room: 0.7, echo: [[0.12, 1, 1500], [0.26, 0.55, 1000], [0.45, 0.28, 800]], g: 0.32, rumble: { g: 0.48, lp: 200, d: 0.3 } },
}));
def('gun_sawnoff', { cat: 'gun', what: 'Half a Shotgun shot (the biggest boom)', lu: -8.5, fin: { push: 6 } }, (R, J) => gun(R, J, {
  len: 1.4,
  crack: { g: 0.55, hp: 1500, d: 0.0025 },
  blast: { g: 1, f0: 4200, f1: 220, sw: 0.025, d: 0.1, body: [330, 6, 0.8], drive: 3.5, pink: true },
  thump: { g: 1, f0: 105, f1: 40, sw: 0.035, d: 0.1, drive: 2.5 },
  tail: { lp: 1500, verb: 0.16, room: 0.75, echo: [[0.12, 1, 1300], [0.27, 0.58, 900], [0.47, 0.3, 700]], g: 0.34, rumble: { g: 0.58, lp: 170, d: 0.34 } },
}));
def('gun_autoshot', { cat: 'gun', what: 'Lawn Mower shot (automatic shotgun, the action clacks)', lu: -10, vars: 2, fin: { push: 5.5 } }, (R, J) => gun(R, J, {
  len: 0.95,
  crack: { g: 0.45, hp: 1800, d: 0.0018 },
  blast: { g: 1, f0: 4500, f1: 320, sw: 0.018, d: 0.06, body: [450, 5, 1], drive: 3, pink: true },
  thump: { g: 0.95, f0: 115, f1: 46, sw: 0.025, d: 0.07, drive: 2.2 },
  mech: [{ g: 0.16, at: 0.045, modes: [[1500, 25, 1], [2400, 30, 0.8], [3600, 40, 0.5]] }, { g: 0.1, at: 0.075, modes: [[2100, 30, 1], [3300, 40, 0.6]] }],
  tail: { lp: 1900, verb: 0.13, room: 0.6, echo: [[0.11, 1, 1500], [0.24, 0.5, 1000]], g: 0.27, rumble: { g: 0.3, lp: 200, d: 0.2 } },
}));
def('gun_lever', { cat: 'gun', what: 'Yeehaw shot (lever-action rifle; the lever is its own clip)', lu: -9.5, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 1.3,
  crack: { g: 0.7, hp: 2200, d: 0.0014, nw: 0.6 },
  blast: { g: 1, f0: 7000, f1: 380, sw: 0.016, d: 0.06, body: [520, 5, 0.9], drive: 2.7 },
  thump: { g: 0.95, f0: 135, f1: 48, sw: 0.022, d: 0.075, drive: 2 },
  tail: { lp: 2000, verb: 0.16, room: 0.72, echo: [[0.14, 1, 1500], [0.3, 0.55, 1000], [0.52, 0.28, 700]], g: 0.32, rumble: { g: 0.36, lp: 190, d: 0.3 } },
}));
def('gun_revolver', { cat: 'gun', what: 'Revolver shot (magnum: sharp crack, heavy boom)', lu: -9.5, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 1.2,
  crack: { g: 0.85, hp: 2300, d: 0.0015, nw: 0.4 },
  blast: { g: 1, f0: 9000, f1: 420, sw: 0.014, d: 0.05, body: [900, 4, 1], drive: 3 },
  thump: { g: 0.85, f0: 165, f1: 55, sw: 0.018, d: 0.06, drive: 2 },
  tail: { lp: 2400, verb: 0.15, room: 0.7, echo: [[0.12, 1, 1800], [0.27, 0.5, 1200], [0.48, 0.24, 800]], g: 0.3, rumble: { g: 0.3, lp: 210, d: 0.24 } },
}));
def('gun_pistol', { cat: 'gun', what: 'Plan B shot (light pistol, the slide snaps)', lu: -11.5, vars: 2, fin: { push: 5 } }, (R, J) => gun(R, J, {
  len: 0.65,
  crack: { g: 0.7, hp: 2800, d: 0.0011 },
  blast: { g: 1, f0: 8500, f1: 800, sw: 0.009, d: 0.028, body: [1300, 4, 1.2], drive: 2.4 },
  thump: { g: 0.6, f0: 215, f1: 88, sw: 0.01, d: 0.035 },
  mech: [{ g: 0.15, at: 0.01, modes: [[2800, 40, 1], [4200, 50, 0.7], [6300, 60, 0.4]] }],
  tail: { lp: 2800, verb: 0.12, room: 0.5, echo: [[0.09, 1, 2000], [0.2, 0.45, 1300]], g: 0.2, rumble: { g: 0.14, lp: 250, d: 0.1 } },
}));
// the Marble Shotgun: a shotgun's thoomp with a spray of glass marbles clicking off things after it
def('gun_marbles', { cat: 'gun', what: 'Marble Shotgun shot (boom + glass marbles)', lu: -10, fin: { push: 5 } }, (R, J) => {
  const o = gun(R, J, {
    len: 1.0,
    crack: { g: 0.4, hp: 2000, d: 0.0018 },
    blast: { g: 1, f0: 4200, f1: 420, sw: 0.02, d: 0.06, body: [520, 4, 1], drive: 2.6, pink: true },
    thump: { g: 0.9, f0: 125, f1: 50, sw: 0.025, d: 0.1, drive: 2 },
    tail: { lp: 1900, verb: 0.12, room: 0.6, echo: [[0.11, 1, 1500], [0.24, 0.45, 1000]], g: 0.22, rumble: { g: 0.25, lp: 200, d: 0.2 } },
  });
  for (let k = 0; k < 14; k++) {
    const t = 0.03 + pow(R(), 1.6) * 0.32;
    mix(o, clink(R, J, 0.08, 3600 + R() * 2800, 0.02 + R() * 0.02), 0.22 * (1 - t * 1.6), t);
  }
  return o;
});
// the Redline: a compact rifle shot riding an engine bark; full HP is low and long, near death it screams
const redline = (k) => (R, J) => {
  const len = [0.42, 0.28, 0.16][k];
  const o = gun(R, J, {
    len,
    crack: { g: 0.55, hp: 2800 + k * 600, d: 0.001 },
    blast: { g: 1, f0: 7000 + k * 1500, f1: 700 + k * 300, sw: 0.01, d: [0.03, 0.022, 0.014][k], body: [900 + k * 300, 4, 1.1], drive: 2.6 },
    thump: { g: 0.6 - k * 0.12, f0: 200, f1: 80, sw: 0.01, d: [0.045, 0.03, 0.018][k] },
    tail: k < 2 ? { lp: 2600, verb: 0.08, room: 0.45, echo: [[0.08, 1, 2000]], g: 0.12 - k * 0.04, rumble: { g: 0.12, lp: 240, d: 0.06 } } : null,
  });
  mix(o, engine(R, len, [92, 150, 235][k], { d: [0.07, 0.045, 0.028][k], cut: [2200, 3200, 5200][k], drive: 4 + k }), [0.55, 0.6, 0.7][k], 0.002);
  return o;
};
def('gun_redline_k0', { cat: 'gun', what: 'Redline shot at full HP (engine low and slow)', lu: -11, fin: { push: 5 } }, redline(0));
def('gun_redline_k5', { cat: 'gun', what: 'Redline shot at half HP', lu: -11.5, fin: { push: 5 } }, redline(1));
def('gun_redline_k10', { cat: 'gun', what: 'Redline shot near death (engine screaming, up to 22 a second)', lu: -12, fin: { push: 5, fade: 0.01 } }, redline(2));

// ================================================================= hits, headshots, kills
function hitLayers(R, s) {
  const o = zeros(s);
  mix(o, partials(s, [[2950, 1, 0.02], [4420, 0.5, 0.013], [6300, 0.25, 0.008]], R, 0.0003), 1);
  mix(o, thump(s, 330, 170, 0.012, 0.009, 1.5, 0.0005), 0.25);
  mix(o, tick(R, s, 5000, 0.0006), 0.5);
  return o;
}
def('hit', { cat: 'confirm', what: 'hit marker: you hit someone (a crisp tick that cuts through gunfire)', lu: -16, fin: { push: 3 } }, (R) => hitLayers(R, 0.12));
function dink(R, s, f) {
  return partials(s, [[f, 1, 0.16], [f * 2.03, 0.45, 0.1], [f * 2.74, 0.35, 0.07], [f * 3.93, 0.18, 0.045], [f * 5.4, 0.1, 0.03]], R, 0.0004);
}
def('headshot', { cat: 'confirm', what: 'headshot: a bright metal dink over the hit tick', lu: -13.5, fin: { push: 3 } }, (R) => {
  const o = zeros(0.55);
  mix(o, dink(R, 0.55, 2380), 1);
  mix(o, hitLayers(R, 0.55), 0.55);
  mix(o, tick(R, 0.55, 4000, 0.0008), 0.5);
  return o;
});
def('headshot_ko', { cat: 'confirm', what: 'killing headshot: the dink, a lower bell under it, and weight', lu: -12, fin: { push: 3 } }, (R) => {
  const o = zeros(0.95);
  mix(o, dink(R, 0.95, 2380), 1);
  mix(o, partials(0.95, [[1190, 1, 0.32], [1190 * 2.01, 0.4, 0.2], [1190 * 3.0, 0.2, 0.12]], R, 0.001), 0.6);
  mix(o, hitLayers(R, 0.95), 0.5);
  mix(o, thump(0.95, 120, 52, 0.02, 0.09, 2), 0.55);
  mix(o, roomOf(o, 0.6, 0.5), 0.14);
  return o;
});
function tonk(R, s) {
  const o = zeros(s), f = 640;
  mix(o, partials(s, [[f, 1, 0.11], [f * 1.59, 0.6, 0.075], [f * 2.3, 0.4, 0.05], [f * 3.1, 0.22, 0.03]], R, 0.0005), 0.9);
  mix(o, thump(s, 210, 85, 0.015, 0.05, 2), 0.8);
  const n = white(s, R); lp(n, 1600); env(n, ad(0.0005, 0.02)); mix(o, norm(n), 0.4);
  return o;
}
def('headshot_taken', { cat: 'confirm', what: 'you took a headshot: a dull helmet tonk', lu: -13.5, fin: { push: 3 } }, (R) => tonk(R, 0.45));
def('headshot_taken_ko', { cat: 'confirm', what: 'a headshot killed you: the tonk, a muffled boom and a short ring', lu: -12.5, fin: { push: 3 } }, (R) => {
  const o = zeros(1.4);
  mix(o, tonk(R, 1.4), 0.9);
  mix(o, thump(1.4, 120, 40, 0.04, 0.25, 2), 0.7);
  const m = pink(1.4, R); filt(m, 'lp', glide(1500, 150, 0.15), 1); env(m, ad(0.003, 0.35)); mix(o, norm(m), 0.35);
  const ring = osc(1.4, 3150); env(ring, ahd(0.05, 0.1, 0.32)); mix(o, ring, 0.07);
  mix(o, roomOf(o, 0.65, 0.5), 0.15);
  return o;
});
def('hurt', { cat: 'confirm', what: 'you got hurt: a muffled body hit', lu: -16, fin: { push: 3 } }, (R) => {
  const o = zeros(0.3);
  mix(o, thump(0.3, 185, 75, 0.02, 0.035, 2.2), 0.9);
  const n = white(0.3, R); filt(n, 'lp', glide(2400, 400, 0.02)); env(n, ad(0.0005, 0.025)); mix(o, norm(n), 0.55);
  mix(o, tick(R, 0.3, 2500, 0.0015), 0.25);
  return o;
});
def('kill', { cat: 'confirm', what: 'you got a kill: a punch and two clean chimes a fifth apart', lu: -12.5, fin: { push: 3 } }, (R) => {
  const o = zeros(1.1);
  mix(o, thump(1.1, 150, 52, 0.03, 0.09, 2), 0.7);
  mix(o, norm(bell(1.1, 880, { ratio: 3.01, index: 1.6, idxDecay: 0.05, decay: 0.22 })), 0.55);
  mix(o, norm(bell(1.1, 1318.5, { ratio: 3.01, index: 1.4, idxDecay: 0.06, decay: 0.38 })), 0.6, 0.075);
  mix(o, norm(bell(1.1, 1760, { ratio: 2, index: 0.8, idxDecay: 0.1, decay: 0.3 })), 0.25, 0.075);
  const sh = white(1.1, R); hp2(sh, 7000); env(sh, ad(0.001, 0.05)); mix(o, norm(sh), 0.12, 0.075);
  mix(o, roomOf(o, 0.6, 0.5), 0.18);
  return o;
});
def('death', { cat: 'confirm', what: 'you died: a low hit, the world going muffled, a soft falling tone', lu: -13, fin: { push: 3 } }, (R) => {
  const o = zeros(1.7);
  mix(o, thump(1.7, 110, 38, 0.06, 0.3, 2), 0.8);
  const n = pink(1.7, R); filt(n, 'lp', glide(2500, 120, 0.15), 1.2); env(n, ad(0.003, 0.35)); mix(o, norm(n), 0.5);
  for (const [f, g] of [[392, 0.22], [466.2, 0.15]]) { const t = osc(1.7, expRamp(f, f / 2, 1.1), 'tri'); lp(t, 900); env(t, ahd(0.06, 0.25, 0.45)); mix(o, norm(t), g, 0.05); }
  mix(o, roomOf(o, 0.7, 0.5), 0.2);
  return o;
});

// ================================================================= melee (katana)
def('swing', { cat: 'melee', what: 'melee whoosh (katana swing, item throw)', lu: -17, vars: 2, fin: { push: 2 } }, (R, J) => {
  const s = 0.38, o = zeros(s), pk = J(0.09);
  mix(o, airy(R, s, (t) => 500 + 1900 * sin(PI * min(1, t / 0.24)), 1.4, hump(pk, 0.06)), 1);
  mix(o, airy(R, s, (t) => 1100 + 3600 * sin(PI * min(1, t / 0.24)), 2, hump(pk, 0.045), 'white'), 0.35);
  const w = pink(s, R); lp(w, 300); env(w, hump(pk, 0.05)); mix(o, norm(w), 0.2);
  return o;
});
def('bonk', { cat: 'melee', what: 'melee hit (the katana landing)', lu: -12, fin: { push: 4 } }, (R) => {
  const s = 0.45, o = zeros(s);
  mix(o, thump(s, 170, 62, 0.02, 0.045, 2.5), 0.9);
  const b = white(s, R); filt(b, 'lp', glide(4000, 500, 0.015), 0.9); env(b, ahd(0.0003, 0.002, 0.035)); sat(norm(b), 2); mix(o, norm(b), 0.9);
  mix(o, tick(R, s, 3000, 0.003), 0.45);
  const e = strike(s, R, [[2700, 60, 1], [4100, 70, 0.6]]); env(e, ad(0.0002, 0.05)); mix(o, norm(e), 0.12);
  mix(o, roomOf(o, 0.5, 0.5), 0.08);
  return o;
});
def('tink', { cat: 'melee', what: 'small parry tink / the blade hitting a wall', lu: -18, vars: 2 }, (R, J) => {
  const o = partials(0.25, [[J(3900), 1, 0.06], [J(6050), 0.5, 0.035], [J(8300), 0.25, 0.02]], R, 0.0002);
  mix(o, tick(R, 0.25, 4500, 0.0005), 0.6);
  return o;
});
def('ting', { cat: 'melee', what: 'katana draw: the blade sliding out and ringing', lu: -15 }, (R) => {
  const s = 0.75, o = zeros(s), slide = zeros(s);
  for (const [f, g] of [[2900, 1], [4450, 0.8], [6600, 0.6], [8800, 0.4]]) {
    const n = white(s, R); filt(n, 'bp', (t) => f * (1 + 0.06 * min(1, t / 0.2)), 45); mix(slide, norm(n), g);
  }
  env(slide, (t) => (t < 0.18 ? pow(t / 0.18, 1.5) : exp(-(t - 0.18) / 0.06)));
  mix(o, norm(slide), 0.7);
  mix(o, partials(s - 0.17, [[3050, 1, 0.35], [4620, 0.6, 0.25], [6900, 0.35, 0.15], [9100, 0.2, 0.1]], R, 0.002), 0.55, 0.17);
  mix(o, airy(R, s, 3000, 0.7, hump(0.15, 0.05), 'white'), 0.12);
  return o;
});
function clang(R, s, f) {
  const o = zeros(s);
  mix(o, tick(R, s, 2200, 0.003), 0.8);
  mix(o, partials(s, [[f, 1, 0.45], [f * 2.76, 0.75, 0.32], [f * 5.4, 0.5, 0.2], [f * 8.93, 0.3, 0.12], [3150, 0.6, 0.28], [4720, 0.4, 0.2], [6350, 0.25, 0.12]], R, 0.0003), 0.9);
  mix(o, thump(s, 240, 110, 0.01, 0.03, 2), 0.5);
  return o;
}
def('parry', { cat: 'melee', what: 'katana parry: blade striking blade', lu: -11.5, fin: { push: 3 } }, (R) => {
  const o = clang(R, 1.3, 820);
  mix(o, roomOf(o, 0.65, 0.4), 0.2);
  return o;
});
def('parry_perfect', { cat: 'melee', what: 'PERFECT parry: a bigger clang with a rising chime', lu: -10.5, fin: { push: 3 } }, (R) => {
  const s = 1.8, o = clang(R, s, 760);
  mix(o, norm(bell(s, 1760, { ratio: 2, index: 0.9, decay: 0.45 })), 0.4, 0.05);
  mix(o, norm(bell(s, 2637, { ratio: 2, index: 0.7, decay: 0.5 })), 0.32, 0.12);
  mix(o, roomOf(o, 0.8, 0.35), 0.28);
  return o;
});
def('ricochet', { cat: 'melee', what: 'ricochet: a bullet whining off (perfect parry sends them home)', lu: -16, vars: 2 }, (R, J) => {
  const s = 0.42, o = zeros(s), f0 = J(3400), f1 = J(1150);
  mix(o, tick(R, s, 2500, 0.002), 0.5);
  const w = osc(s, (t) => expRamp(f0, f1, 0.28)(t) * (1 + 0.015 * sin(2 * PI * 38 * t)));
  const w2 = osc(s, (t) => expRamp(f0, f1, 0.28)(t) * 1.5, 'tri');
  mix(w, w2, 0.25); env(w, ahd(0.005, 0.03, 0.1)); mix(o, norm(w), 0.5);
  mix(o, airy(R, s, glide(5000, 1500, 0.1), 3, ad(0.003, 0.08), 'white'), 0.3);
  return o;
});

// ================================================================= handling (reloads, swaps, dry fire)
def('click', { cat: 'handling', what: 'mechanical click (weapon swap, reload parts at pitches 0.8-1.5, UI)', lu: -20 }, (R) => {
  const s = 0.1, o = zeros(s);
  const a = strike(s, R, [[2300, 25, 1], [3600, 35, 0.8], [5200, 45, 0.6], [7400, 55, 0.35]], 0.0004); env(a, ad(0.0001, 0.012)); mix(o, norm(a), 1);
  const b = strike(s, R, [[3000, 30, 1], [4700, 40, 0.7], [6900, 50, 0.4]], 0.0003); env(b, ad(0.0001, 0.008)); mix(o, norm(b), 0.55, 0.011);
  mix(o, thump(s, 520, 260, 0.008, 0.008, 1.3, 0.0003), 0.25);
  return o;
});
def('empty', { cat: 'handling', what: 'dry fire: the hammer falling on nothing', lu: -19 }, (R) => {
  const s = 0.1, o = zeros(s);
  const a = strike(s, R, [[1750, 12, 1], [2800, 15, 0.7], [4200, 20, 0.4]], 0.0005); env(a, ad(0.0001, 0.006)); mix(o, norm(a), 1);
  mix(o, thump(s, 600, 420, 0.01, 0.007, 1.2, 0.0003), 0.25);
  return o;
});
def('reload', { cat: 'handling', what: 'magazine in: the seat and the catch', lu: -17 }, (R) => {
  const s = 0.3, o = zeros(s);
  mix(o, thump(s, 260, 130, 0.01, 0.02, 1.6), 0.6);
  const n = white(s, R); lp(n, 2800); env(n, ad(0.0003, 0.012)); mix(o, norm(n), 0.55);
  const h = strike(s, R, [[1300, 10, 1], [2150, 14, 0.7], [3500, 18, 0.5]]); env(h, ad(0.0002, 0.03)); mix(o, norm(h), 0.6);
  const c = strike(s, R, [[3100, 40, 1], [4600, 50, 0.7], [6900, 60, 0.4]], 0.0003); env(c, ad(0.0001, 0.01)); mix(o, norm(c), 0.7, 0.05);
  return o;
});
def('thwack', { cat: 'handling', what: 'heavy metal clunk (the Marble Shotgun lid, covers slamming)', lu: -15 }, (R) => {
  const s = 0.3, o = zeros(s);
  mix(o, thump(s, 180, 80, 0.012, 0.04, 2), 0.8);
  const k = strike(s, R, [[880, 20, 1], [1480, 24, 0.8], [2330, 28, 0.6], [3420, 32, 0.4]]); env(k, ad(0.0001, 0.05)); mix(o, norm(k), 0.7);
  const n = white(s, R); lp(n, 2200); env(n, ad(0.0003, 0.02)); mix(o, norm(n), 0.5);
  return o;
});
def('marble', { cat: 'handling', what: 'one glass marble clack (also cases and belt links, pitched up)', lu: -21, vars: 2 }, (R, J) => {
  const o = clink(R, J, 0.15, 4300, 0.03);
  mix(o, thump(0.15, 900, 700, 0.006, 0.006, 1, 0.0002), 0.2);
  return o;
});
def('glug', { cat: 'handling', what: 'Redline reload: the jerry can glugging', lu: -18 }, (R) => {
  const s = 0.38, o = zeros(s);
  for (const [t, f] of [[0, 300], [0.075, 255], [0.16, 330]]) {
    const b = osc(0.13, (u) => f * (1 + 0.7 * min(1, u / 0.045))); env(b, ad(0.004, 0.03)); mix(o, norm(b), 0.8, t);
  }
  const sl = pink(s, R); lp(sl, 700); env(sl, ahd(0.01, 0.12, 0.06)); mix(o, norm(sl), 0.25);
  return o;
});
def('rev_up', { cat: 'handling', what: 'Redline reload: the engine revving', lu: -15 }, (R) => {
  const s = 0.62, o = zeros(s);
  const f = (t) => 40 + 140 * (t < 0.34 ? pow(t / 0.34, 1.4) : 1 - 0.08 * (t - 0.34) / 0.25);
  const e = zeros(s); mix(e, osc(s, f, 'saw'), 0.7); mix(e, osc(s, (t) => f(t) * 0.5, 'pulse', 0, 0.3), 0.5);
  const am = white(s, R); lp(am, 60); norm(am);
  for (let i = 0; i < e.length; i++) e[i] *= 1 + 0.3 * am[i];
  filt(e, 'lp', (t) => f(t) * 9, 1.5); env(e, ahd(0.02, 0.36, 0.08)); sat(norm(e), 5); mix(o, norm(e), 1);
  mix(o, airy(R, s, 1200, 0.8, ahd(0.02, 0.36, 0.08), 'white'), 0.15);
  return o;
});
def('boing', { cat: 'handling', what: 'Marble Shotgun reload: a marble bouncing out', lu: -19 }, (R, J) => {
  const s = 0.6, o = zeros(s);
  mix(o, thump(s, 500, 250, 0.01, 0.02, 1.5), 0.3);
  let t = 0.02, gap = 0.12, a = 1;
  for (let k = 0; k < 7; k++) { mix(o, clink(R, J, 0.08, 4100 * (1 + (R() - 0.5) * 0.06), 0.025), a, t); t += gap; gap *= 0.72; a *= 0.78; }
  return o;
});

// ================================================================= movement (new: Steps.client.luau)
function step(R, J, kind) {
  const s = kind === 'metal' ? 0.3 : 0.2, o = zeros(s);
  const soft = kind === 'soft';
  mix(o, thump(s, J(soft ? 130 : 160, 0.08), J(soft ? 70 : 85, 0.08), 0.01, J(soft ? 0.024 : 0.015), 1.5, 0.001), soft ? 0.5 : 0.4);
  const toe = J(0.022, 0.25);
  if (kind === 'hard') {
    const g = white(s, R); bp(g, J(2200, 0.15), 0.8); env(g, ad(0.0008, J(0.012, 0.2))); mix(o, norm(g), 0.65);
    const g2 = white(s, R); hp2(g2, J(3500)); env(g2, ad(0.0005, 0.006)); mix(o, norm(g2), 0.35, toe);
  } else if (soft) {
    const g = white(s, R); lp(g, J(900, 0.15)); env(g, ad(0.004, 0.03)); mix(o, norm(g), 0.6);
    const r = white(s, R); hp(r, 2500); env(r, ad(0.01, 0.03)); mix(o, norm(r), 0.12, toe);
  } else if (kind === 'wood') {
    const k = strike(s, R, [[J(190), 6, 1], [J(430), 8, 0.7], [J(790), 10, 0.5], [J(1500), 12, 0.3]]); env(k, ad(0.0005, 0.04)); mix(o, norm(k), 0.7);
    const n = white(s, R); lp(n, 2500); env(n, ad(0.0003, 0.01)); mix(o, norm(n), 0.4);
    const n2 = white(s, R); bp(n2, 1800, 1); env(n2, ad(0.0005, 0.008)); mix(o, norm(n2), 0.3, toe);
  } else { // metal: grating and plates ringing a little
    const k = strike(s, R, [[J(620), 30, 0.8], [J(1170), 35, 1], [J(1930), 40, 0.7], [J(2870), 45, 0.5], [J(4100), 50, 0.3]]); env(k, ad(0.0003, 0.07)); mix(o, norm(k), 0.55);
    const g = white(s, R); hp2(g, 2500); env(g, ad(0.0003, 0.006)); mix(o, norm(g), 0.4);
    const k2 = strike(s, R, [[J(1400), 30, 1], [J(2600), 40, 0.6]]); env(k2, ad(0.0003, 0.03)); mix(o, norm(k2), 0.25, toe);
  }
  return o;
}
for (const kind of ['hard', 'metal', 'wood', 'soft']) {
  def('step_' + kind, { cat: 'move', what: `footstep on ${kind} floors`, lu: kind === 'soft' ? -26 : -24.5, vars: 4, jitter: 1, fin: { push: 3 } }, (R, J) => step(R, J, kind));
}
def('jump', { cat: 'move', what: 'jump: push-off scuff and a cloth whoosh', lu: -25, vars: 2, fin: { push: 2 } }, (R, J) => {
  const s = 0.28, o = zeros(s);
  const g = white(s, R); bp(g, J(1800), 0.9); env(g, ad(0.0005, 0.01)); mix(o, norm(g), 0.5);
  mix(o, thump(s, 150, 80, 0.01, 0.02, 1.5), 0.35);
  mix(o, airy(R, s, glide(800, 1800, 0.08), 1, hump(J(0.05), 0.06)), 0.5);
  return o;
});
def('land', { cat: 'move', what: 'landing: both feet, the kit settling', lu: -18, vars: 2, fin: { push: 3 } }, (R, J) => {
  const s = 0.38, o = zeros(s);
  mix(o, thump(s, 140, 55, 0.012, J(0.05), 2), 0.9);
  mix(o, thump(s, 150, 60, 0.012, 0.035, 2), 0.55, J(0.018, 0.2));
  const n = white(s, R); filt(n, 'lp', glide(3000, 600, 0.02)); env(n, ad(0.0005, 0.03)); mix(o, norm(n), 0.6);
  const k = strike(s, R, [[1700, 30, 1], [2600, 35, 0.7], [3900, 40, 0.5]]); env(k, ad(0.0003, 0.04)); mix(o, norm(k), 0.12, 0.01);
  mix(o, airy(R, s, 2000, 0.7, ad(0.004, 0.04), 'white'), 0.15);
  return o;
});
def('slide', { cat: 'move', what: 'slide: shoes and clothes scraping along the floor', lu: -20, fin: { push: 2 } }, (R) => {
  const s = 0.75, o = zeros(s);
  const am = white(s, R); lp(am, 45); norm(am);
  const a = pink(s, R); bp(a, 1400, 0.7); const b = white(s, R); bp(b, 3200, 2);
  mix(a, norm(b), 0.4);
  for (let i = 0; i < a.length; i++) a[i] *= 0.6 + 0.4 * abs(am[i]);
  env(a, ahd(0.03, 0.35, 0.15)); mix(o, norm(a), 1);
  mix(o, thump(s, 140, 70, 0.01, 0.03, 1.5), 0.3);
  return o;
});

// ================================================================= items
def('boom', { cat: 'item', what: 'a frag going off', lu: -8.5, fin: { push: 6 } }, (R, J) => {
  const s = 2.6, o = gun(R, J, {
    len: s,
    crack: { g: 0.7, hp: 1500, d: 0.002, nw: 1.2 },
    blast: { g: 1, f0: 6000, f1: 200, sw: 0.05, d: 0.22, body: [300, 5, 0.8], drive: 3.2, pink: true, hold: 0.01 },
    thump: { g: 1, f0: 80, f1: 34, sw: 0.05, d: 0.2, drive: 2.5 },
    tail: { lp: 1200, verb: 0.2, room: 0.85, echo: [[0.18, 1, 1000], [0.4, 0.6, 700], [0.75, 0.3, 500]], g: 0.32, rumble: { g: 0.7, lp: 150, d: 0.9, a: 0.02 } },
  });
  for (let k = 0; k < 18; k++) { const t = 0.05 + pow(R(), 1.5) * 0.6; mix(o, clink(R, J, 0.06, 1800 + R() * 3500, 0.012), 0.06, t); }
  return o;
});
def('heal', { cat: 'item', what: 'the medkit: a spray and a soft rising chime', lu: -16 }, (R) => {
  const s = 0.75, o = zeros(s);
  mix(o, airy(R, s, 4200, 0.9, ahd(0.01, 0.12, 0.08), 'white'), 0.5);
  mix(o, norm(bell(s, 659.3, { ratio: 2, index: 0.6, decay: 0.25, atk: 0.01 })), 0.45, 0.04);
  mix(o, norm(bell(s, 987.8, { ratio: 2, index: 0.6, decay: 0.3, atk: 0.01 })), 0.45, 0.13);
  mix(o, roomOf(o, 0.6, 0.5), 0.15);
  return o;
});
def('reverse', { cat: 'item', what: 'a shield dome going up / the reverse card: a swell into a soft thoom', lu: -15 }, (R) => {
  const s = 0.85, o = zeros(s), at = 0.42;
  const n = pink(s, R); filt(n, 'lp', (t) => 300 + 4000 * min(1, t / at), 1.5); env(n, swell(at, 0.12, 0.05)); mix(o, norm(n), 0.7);
  mix(o, thump(s - at, 150, 90, 0.02, 0.15, 1.8, 0.002), 0.7, at);
  const sh = osc(s - at, (t) => 520 * (1 + 0.01 * sin(2 * PI * 6 * t))); env(sh, ad(0.01, 0.2)); mix(o, sh, 0.18, at);
  mix(o, roomOf(o, 0.65, 0.5), 0.15);
  return o;
});
def('pop', { cat: 'item', what: 'a shield dome going out / the pop quiz: a crisp energy pop', lu: -15 }, (R, J) => {
  const s = 0.4, o = zeros(s);
  mix(o, thump(s, 900, 200, 0.012, 0.04, 2, 0.0003), 0.8);
  mix(o, tick(R, s, 2000, 0.02), 0.5);
  for (let k = 0; k < 5; k++) mix(o, clink(R, J, 0.06, 5000 + R() * 3000, 0.015), 0.12, 0.01 + R() * 0.08);
  mix(o, roomOf(o, 0.5, 0.5), 0.12);
  return o;
});
def('blow', { cat: 'item', what: 'a smoke bomb popping into a cloud: a pop, then the hiss', lu: -14 }, (R) => {
  const s = 1.1, o = zeros(s);
  mix(o, thump(s, 200, 80, 0.012, 0.04, 2), 0.7);
  const b = white(s, R); lp(b, 2000); env(b, ad(0.0005, 0.03)); mix(o, norm(b), 0.6);
  const h = white(s, R); bp(h, 3000, 0.6); env(h, ahd(0.03, 0.15, 0.25));
  const fl = white(s, R); lp(fl, 30); norm(fl);
  for (let i = 0; i < h.length; i++) h[i] *= 0.75 + 0.25 * fl[i];
  mix(o, norm(h), 0.55, 0.02);
  return o;
});
def('popper', { cat: 'item', what: 'the party popper: a sharp cap snap and paper fluttering', lu: -13 }, (R) => {
  const s = 0.85, o = zeros(s);
  mix(o, tick(R, s, 1500, 0.006), 0.8);
  mix(o, thump(s, 300, 120, 0.008, 0.02, 2), 0.6);
  mix(o, roomOf(o, 0.5, 0.4), 0.15);
  for (let k = 0; k < 40; k++) { const t = 0.03 + pow(R(), 1.3) * 0.55; const g = white(0.012, R); hp(g, 3000 + R() * 3000); env(g, ad(0.0005, 0.002)); mix(o, norm(g), 0.08 * (1 - t), t); }
  return o;
});
def('squeak', { cat: 'item', what: 'a rubber duck squeak', lu: -16, vars: 1 }, (R) => {
  const s = 0.3, o = zeros(s);
  const f = (t) => (t < 0.08 ? 1100 + 400 * (t / 0.08) : 1500 - 200 * min(1, (t - 0.08) / 0.12)) * (1 + 0.02 * sin(2 * PI * 25 * t));
  const v = osc(s, f, 'saw'); bp(v, 2000, 3); lp(v, 4500); env(v, ahd(0.012, 0.13, 0.03)); mix(o, norm(v), 0.85);
  mix(o, airy(R, s, 2500, 1.5, ahd(0.01, 0.13, 0.03), 'white'), 0.12);
  return o;
});
def('quack', { cat: 'item', what: 'the duck sticking to someone: a short nasal quack', lu: -15 }, (R) => {
  const s = 0.3, o = zeros(s);
  const v = osc(s, glide(300, 235, 0.08), 'saw');
  const a = Float64Array.from(v); bp(a, 900, 4); const b = Float64Array.from(v); bp(b, 2400, 4); const c = Float64Array.from(v); lp(c, 600);
  mix(o, norm(a), 1); mix(o, norm(b), 0.55); mix(o, norm(c), 0.4);
  env(o, ahd(0.01, 0.07, 0.05)); sat(norm(o), 1.5);
  return o;
});
def('hole', { cat: 'item', what: 'a black hole humming (3 s)', lu: -15, fin: { push: 2, fade: 0.4 } }, (R) => {
  const s = 3.0, o = zeros(s);
  mix(o, osc(s, 55), 0.6); mix(o, osc(s, 110.7), 0.35); mix(o, osc(s, 82.6, 'tri'), 0.2);
  const n = pink(s, R); filt(n, 'lp', (t) => 200 + 1300 * min(1, t / 2.5), 2);
  for (let i = 0; i < n.length; i++) n[i] *= 0.6 + 0.4 * sin(2 * PI * 4 * i / SR);
  mix(o, norm(n), 0.5);
  sat(norm(o), 1.6);
  env(o, (t) => min(1, t / 0.3) * min(1, (s - t) / 0.5));
  return o;
});
def('ropesnap', { cat: 'item', what: 'your rope snapping in a black hole', lu: -14 }, (R) => {
  const s = 0.4, o = zeros(s);
  mix(o, tick(R, s, 2000, 0.004), 0.9);
  const tw = osc(s, glide(190, 90, 0.06), 'saw'); lp(tw, 1400); env(tw, ad(0.001, 0.1)); mix(o, norm(tw), 0.5);
  mix(o, airy(R, s, glide(4000, 900, 0.06), 1.2, ad(0.002, 0.06), 'white'), 0.4);
  return o;
});
def('shutter', { cat: 'item', what: 'the instant camera taking a photo: a shutter click-clack', lu: -16 }, (R) => {
  const s = 0.25, o = zeros(s);
  const a = strike(s, R, [[3200, 25, 1], [5100, 30, 0.6]], 0.0003); env(a, ad(0.0001, 0.01)); mix(o, norm(a), 1);
  const b = strike(s, R, [[2600, 25, 1], [4300, 30, 0.6]], 0.0003); env(b, ad(0.0001, 0.012)); mix(o, norm(b), 0.8, 0.035);
  mix(o, tick(R, s, 3000, 0.008), 0.3, 0.035);
  mix(o, thump(s, 400, 220, 0.008, 0.012, 1.3), 0.2);
  return o;
});
def('whirr', { cat: 'item', what: 'a small motor: the camera spitting a print, the training doors sliding', lu: -16 }, (R) => {
  const s = 0.68, o = zeros(s);
  const m = zeros(s); mix(m, osc(s, 180, 'saw'), 0.6); mix(m, osc(s, 360, 'saw'), 0.3); lp(m, 1600);
  mix(m, osc(s, 1450), 0.12);
  const g = white(s, R); bp(g, 2000, 1);
  for (let i = 0; i < g.length; i++) g[i] *= 0.5 + 0.5 * sin(2 * PI * 30 * i / SR);
  mix(m, norm(g), 0.25);
  env(m, (t) => min(1, t / 0.05) * (t < 0.52 ? 1 : exp(-(t - 0.52) / 0.04)));
  mix(o, norm(m), 1);
  return o;
});
def('photoin', { cat: 'item', what: 'coming out of a photo: a rising whoosh and a paper flap', lu: -15 }, (R) => {
  const s = 0.55, o = zeros(s);
  mix(o, airy(R, s, (t) => 400 + 3500 * min(1, t / 0.3), 1.2, swell(0.3, 0.08, 0.05)), 0.8);
  mix(o, thump(s - 0.3, 260, 140, 0.01, 0.03, 1.5), 0.45, 0.3);
  mix(o, airy(R, s - 0.3, 1800, 1, ad(0.001, 0.015), 'white'), 0.35, 0.3);
  return o;
});
def('photoout', { cat: 'item', what: 'going into a photo: a falling whoosh into a flat thunk', lu: -15 }, (R) => {
  const s = 0.5, o = zeros(s);
  mix(o, airy(R, s, (t) => 3800 - 3400 * min(1, t / 0.25), 1.2, hump(0.1, 0.07)), 0.8);
  mix(o, thump(s - 0.22, 220, 110, 0.01, 0.03, 1.6), 0.55, 0.22);
  return o;
});
def('framepop', { cat: 'item', what: 'a printed photo popping up or away: card on card', lu: -15 }, (R) => {
  const s = 0.35, o = zeros(s);
  mix(o, thump(s, 260, 130, 0.01, 0.03, 1.6), 0.7);
  const n = white(s, R); bp(n, 1200, 0.9); env(n, ad(0.0005, 0.03)); mix(o, norm(n), 0.55);
  mix(o, tick(R, s, 3500, 0.002), 0.3);
  return o;
});
def('bloop', { cat: 'item', what: 'blowing a soap bubble', lu: -18 }, (R) => {
  const s = 0.2, o = zeros(s);
  const b = osc(s, (t) => 300 + 400 * min(1, t / 0.1)); env(b, ahd(0.006, 0.05, 0.03)); mix(o, norm(b), 0.9);
  mix(o, airy(R, s, 1500, 1, ahd(0.01, 0.04, 0.03), 'white'), 0.15);
  return o;
});
def('plip', { cat: 'item', what: 'a little soap bubble popping', lu: -21 }, (R) => {
  const s = 0.08, o = zeros(s);
  const b = osc(s, glide(1800, 900, 0.006)); env(b, ad(0.0003, 0.008)); mix(o, norm(b), 0.8);
  mix(o, tick(R, s, 3000, 0.002), 0.5);
  return o;
});
def('glorp', { cat: 'item', what: 'getting sealed in a giant bubble: a wet, closing gloop', lu: -14 }, (R) => {
  const s = 0.5, o = zeros(s);
  const b = osc(s, (t) => 180 + 240 * min(1, t / 0.2)); env(b, ahd(0.02, 0.1, 0.1)); mix(o, norm(b), 0.8);
  mix(o, airy(R, s, (t) => 400 + 800 * min(1, t / 0.2), 4, ahd(0.02, 0.12, 0.1)), 0.45);
  lp(o, 2200);
  return o;
});
def('bigpop', { cat: 'item', what: 'a giant bubble popping (also the crate lid fallback)', lu: -13 }, (R, J) => {
  const s = 0.6, o = zeros(s);
  mix(o, thump(s, 600, 150, 0.012, 0.05, 2), 0.8);
  const b = white(s, R); bp(b, 2500, 0.8); env(b, ad(0.0005, 0.03)); mix(o, norm(b), 0.6);
  mix(o, airy(R, s, 6000, 0.8, ad(0.005, 0.12), 'white'), 0.25);
  for (let k = 0; k < 6; k++) mix(o, partials(0.05, [[2000 + R() * 2000, 1, 0.008]], R, 0.0003), 0.12, 0.03 + R() * 0.25);
  return o;
});
def('blub', { cat: 'item', what: 'blubbing inside a bubble', lu: -20 }, (R) => {
  const s = 0.2, o = zeros(s);
  const b = osc(s, (t) => 250 + 200 * min(1, t / 0.06)); env(b, ad(0.004, 0.04)); lp(b, 1200); mix(o, norm(b), 1);
  return o;
});

// ================================================================= slips, rounds, loot
def('whoops', { cat: 'ui', what: 'a slip (marbles underfoot, the training door): a quick falling whoosh', lu: -15 }, (R) => {
  const s = 0.55, o = zeros(s);
  mix(o, airy(R, s, (t) => 2600 * pow(0.25, min(1, t / 0.3)), 1.5, hump(0.06, 0.12)), 0.8);
  const t = osc(s, expRamp(900, 300, 0.35), 'tri'); lp(t, 1500); env(t, ahd(0.01, 0.15, 0.1)); mix(o, norm(t), 0.22);
  mix(o, thump(s, 160, 70, 0.012, 0.04, 1.8), 0.4, 0.3);
  return o;
});
def('clatter', { cat: 'ui', what: 'MARBLES: a pile of marbles going everywhere', lu: -14 }, (R, J) => {
  const s = 0.85, o = zeros(s);
  for (let k = 0; k < 28; k++) { const t = pow(R(), 1.7) * 0.6; mix(o, clink(R, J, 0.07, 3200 + R() * 3500, 0.015 + R() * 0.02), 0.5 * (1 - t), t); }
  for (let k = 0; k < 4; k++) mix(o, thump(0.1, 400 + R() * 200, 200, 0.008, 0.015, 1.5), 0.2, R() * 0.3);
  return o;
});
function chord(R, s, notes, { cut = 2500, a = 0.004, h = 0.08, d = 0.4, detune = 0.004 } = {}) {
  const o = zeros(s);
  for (const n of notes) for (const dt of [-detune, detune]) mix(o, osc(s, noteHz(n) * (1 + dt), 'saw', R()), 0.5);
  filt(o, 'lp', glide(cut * 2, cut, 0.15), 0.8); env(o, ahd(a, h, d)); return norm(o);
}
def('round_start', { cat: 'ui', what: 'ROUND START: a riser into a bright hit and chord', lu: -12, fin: { push: 3 } }, (R) => {
  const s = 2.3, o = zeros(s), at = 0.7;
  const r = pink(s, R); filt(r, 'lp', expRamp(300, 6000, at), 1.2); env(r, swell(at, 0.25, 0.04)); mix(o, norm(r), 0.5);
  mix(o, thump(s - at, 120, 45, 0.03, 0.25, 2.2), 0.9, at);
  mix(o, chord(R, s - at, [57, 64, 69, 73], { cut: 3000, d: 0.35 }), 0.45, at);
  mix(o, norm(bell(s - at, 880, { decay: 0.5 })), 0.3, at);
  mix(o, norm(bell(s - at, 1318.5, { decay: 0.6 })), 0.25, at + 0.06);
  mix(o, roomOf(o, 0.8, 0.4), 0.3);
  return o;
});
def('round_end', { cat: 'ui', what: 'match over: a soft hit and a settled chord', lu: -12.5, fin: { push: 3 } }, (R) => {
  const s = 2.1, o = zeros(s);
  mix(o, thump(s, 100, 45, 0.03, 0.3, 2), 0.7);
  mix(o, chord(R, s, [50, 57, 62, 66], { cut: 2500, a: 0.01, h: 0.15, d: 0.5 }), 0.5);
  mix(o, norm(bell(s, 587.3, { decay: 0.6 })), 0.35, 0.02);
  mix(o, norm(bell(s, 880, { decay: 0.6 })), 0.3, 0.1);
  mix(o, roomOf(o, 0.8, 0.4), 0.32);
  return o;
});
def('loot_tick', { cat: 'loot', what: 'a card passing the marker', lu: -23 }, (R) => {
  const s = 0.06, o = partials(s, [[2500, 1, 0.008], [3900, 0.4, 0.005]], R, 0.0002);
  const k = strike(s, R, [[1800, 10, 1]]); env(k, ad(0.0001, 0.006)); mix(o, norm(k), 0.4);
  return o;
});
def('loot_land', { cat: 'loot', what: 'a crate landing: a heavy thud with the box ringing', lu: -12.5, fin: { push: 4 } }, (R) => {
  const s = 0.85, o = zeros(s);
  mix(o, thump(s, 90, 45, 0.02, 0.15, 2.4), 1);
  const n = white(s, R); filt(n, 'lp', glide(3000, 500, 0.02)); env(n, ad(0.0005, 0.06)); mix(o, norm(n), 0.6);
  const k = strike(s, R, [[180, 8, 1], [340, 10, 0.8], [520, 12, 0.6], [1250, 20, 0.3]]); env(k, ad(0.0005, 0.12)); mix(o, norm(k), 0.5);
  const r = strike(s, R, [[2100, 30, 1], [3300, 40, 0.6]]); env(r, ad(0.0003, 0.05)); mix(o, norm(r), 0.1, 0.02);
  mix(o, roomOf(o, 0.6, 0.5), 0.15);
  return o;
});
def('loot_pop', { cat: 'loot', what: 'the crate opening: the latch, a puff of air and the lid', lu: -14 }, (R) => {
  const s = 0.55, o = zeros(s);
  const c = strike(s, R, [[3100, 40, 1], [4600, 50, 0.6]], 0.0003); env(c, ad(0.0001, 0.01)); mix(o, norm(c), 0.6);
  mix(o, airy(R, s, 1400, 0.8, ad(0.002, 0.04), 'white'), 0.6, 0.02);
  mix(o, thump(s, 300, 140, 0.01, 0.03, 1.8), 0.5, 0.03);
  mix(o, airy(R, s, 8000, 0.7, ad(0.002, 0.1), 'white'), 0.1, 0.03);
  mix(o, roomOf(o, 0.55, 0.5), 0.12);
  return o;
});
function sparkle(R, s, at, g, n = 10) { const o = zeros(s); for (let k = 0; k < n; k++) mix(o, partials(0.12, [[5000 + R() * 4000, 1, 0.03]], R, 0.001), g * (1 - k / n), at + k * 0.035 + R() * 0.02); return o; }
def('loot_win_common', { cat: 'loot', what: 'a common item: one soft chime', lu: -15 }, (R) => {
  const s = 0.9, o = zeros(s);
  mix(o, norm(bell(s, 1046.5, { ratio: 3.01, index: 1.2, decay: 0.35 })), 0.8);
  mix(o, roomOf(o, 0.6, 0.5), 0.18);
  return o;
});
def('loot_win_rare', { cat: 'loot', what: 'a rare item: two chimes and a glint', lu: -13.5 }, (R) => {
  const s = 1.2, o = zeros(s);
  mix(o, norm(bell(s, 1046.5, { decay: 0.35 })), 0.7);
  mix(o, norm(bell(s, 1568, { decay: 0.45 })), 0.7, 0.09);
  mix(o, sparkle(R, s, 0.1, 0.12, 6), 1);
  mix(o, roomOf(o, 0.65, 0.5), 0.2);
  return o;
});
def('loot_win_epic', { cat: 'loot', what: 'an epic item: a low hit, three rising chimes and a chord', lu: -12, fin: { push: 3 } }, (R) => {
  const s = 1.7, o = zeros(s);
  mix(o, thump(s, 110, 45, 0.03, 0.2, 2.2), 0.7);
  [1046.5, 1318.5, 1568].forEach((f, i) => mix(o, norm(bell(s, f, { decay: 0.45 })), 0.55, i * 0.08));
  mix(o, chord(R, s, [60, 64, 67, 72], { cut: 2600, d: 0.45 }), 0.3);
  mix(o, sparkle(R, s, 0.16, 0.12, 8), 1);
  mix(o, roomOf(o, 0.75, 0.45), 0.25);
  return o;
});
def('loot_win_legendary', { cat: 'loot', what: 'a legendary item: a short riser, a big hit, a chord and an arpeggio', lu: -11, fin: { push: 3 } }, (R) => {
  const s = 2.5, o = zeros(s), at = 0.25;
  const r = pink(s, R); filt(r, 'lp', expRamp(500, 7000, at), 1.2); env(r, swell(at, 0.08, 0.03)); mix(o, norm(r), 0.4);
  mix(o, thump(s - at, 110, 40, 0.03, 0.3, 2.4), 0.9, at);
  mix(o, chord(R, s - at, [48, 55, 60, 64, 67], { cut: 3200, d: 0.6 }), 0.45, at);
  [1046.5, 1318.5, 1568, 2093].forEach((f, i) => mix(o, norm(bell(s, f, { decay: 0.5 })), 0.45, at + i * 0.07));
  mix(o, sparkle(R, s, at + 0.3, 0.14, 12), 1);
  mix(o, roomOf(o, 0.85, 0.4), 0.32);
  return o;
});

// ================================================================= render
fs.mkdirSync(OUT, { recursive: true });
const listFile = path.join(OUT, 'list.json');
const prev = fs.existsSync(listFile) ? JSON.parse(fs.readFileSync(listFile, 'utf8')) : {};
const list = ONLY ? prev : {};
const r2 = (x) => Math.round(x * 100) / 100;
for (const d of DEFS) {
  if (ONLY && !ONLY.has(d.name)) continue;
  const files = [], louds = [];
  let secs = 0, pk = 0;
  for (let v = 0; v < d.vars; v++) {
    const R = rngFor(d.name + '/' + v);
    const spread = v === 0 && !d.jitter ? 0 : 1;
    const J = (x, p = 0.05) => x * (1 + (R() * 2 - 1) * p * spread);
    const raw = d.fn(R, J, v);
    const out = finish(raw, d.fin || {});
    const file = v === 0 ? d.name + '.wav' : `${d.name}-${v + 1}.wav`;
    writeWav(path.join(OUT, file), out);
    files.push(file); louds.push(loudness(out));
    secs = Math.max(secs, out.length / SR); pk = Math.max(pk, peak(out));
  }
  const L = louds.reduce((a, b) => a + b, 0) / louds.length;
  const vol = Math.min(3, Math.pow(10, (d.lu + CAL - L) / 20));
  list[d.name] = { cat: d.cat, what: d.what, files, secs: r2(secs), peak: r2(pk), lufs: r2(L), target: d.lu + CAL, vol: r2(vol) };
  console.log(`${d.name.padEnd(20)} ${d.cat.padEnd(9)} ${String(r2(secs)).padStart(5)}s x${d.vars}  L ${r2(L).toFixed(1).padStart(6)}  vol ${r2(vol)}`);
}
fs.writeFileSync(listFile, JSON.stringify(list, null, 1));
