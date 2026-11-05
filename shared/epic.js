// EPIC kills: far, hard or stupid enough that the victim has to sit through the whole killcam.
// The server decides at kill time from what it trusts (its own positions, the hit, the killer's state) and holds the
// victim's respawn for as long as the epic killcam runs. Clients only play it back. Bots never get one.
import { WEAPONS } from './weapons.js';

// a long kill is harder with some weapons: effective distance = real distance x this (not listed: 1, or 2.5 for melee)
export const EPIC_W = {
  sniper: 1, scythe_rifle: 1, ar: 0.9, minigun: 1, redline: 1, bowling: 1, chicken: 1, smg: 1.15, revolver: 1.2, slipper: 1.2,
  banana: 1.3, bow: 1.3, snowball: 1.5, cards: 1.5, cig: 2, shotgun: 2.2, marbles: 2.6,
  bread: 2.5, katana: 2.5, knife: 2.5, slapper: 2.5, spoon: 2.5, scythe: 2.5, popper: 2.5,
};
export const epicMul = (w) => EPIC_W[w] || (WEAPONS[w] && WEAPONS[w].kind === 'melee' ? 2.5 : 1); // melee from other branches too
// nobody aimed these (or the killer could be anywhere by the time they land)
const NEVER = new Set(['void', 'cough', 'tbag', 'duck', 'frag', 'bomb', 'hook', 'blower']);
// effective metres each kind of kill needs. two or more style points at once only need `combo`.
// anti-farm: a victim who hasn't moved `moved` metres in `still` ms is never an epic kill
export const EPIC = { far: 60, hs: 40, air: 30, rope: 30, fast: 30, hp: 25, ns: 20, combo: 20, airH: 3, kmh: 300, lowHp: 10, still: 5000, moved: 0.6 };

// k = { dist, w, hs, ns, air, rope, kmh, hp, still } -> null, or { d: metres, why: ['far', 'hs', 'ns', 'rope' | 'air', 'fast', 'hp'], kmh?, hp? }
export function epicCheck(k) {
  if (!k || NEVER.has(k.w) || !(k.dist > 0) || k.still >= EPIC.still) return null;
  const wd = WEAPONS[k.w];
  const ed = k.dist * epicMul(k.w);
  const why = [];
  if (k.hs && wd && !wd.auto && !(wd.pellets > 1)) why.push('hs'); // a headshot only counts with one careful bullet
  if (k.ns) why.push('ns');
  if (k.rope) why.push('rope'); else if (k.air) why.push('air');
  if (k.kmh >= EPIC.kmh) why.push('fast');
  if (k.hp > 0 && k.hp < EPIC.lowHp) why.push('hp');
  const need = Math.min(EPIC.far, ...why.map((s) => EPIC[s]), why.length >= 2 ? EPIC.combo : Infinity);
  if (ed < need) return null;
  if (ed >= EPIC.far) why.unshift('far');
  return { d: Math.round(k.dist), why, kmh: why.includes('fast') ? Math.round(k.kmh) : undefined, hp: why.includes('hp') ? Math.ceil(k.hp) : undefined };
}

// the epic killcam (ms around the kill): starts `delay` after you die, `pre` of lead-up, ends `post` after the kill
// (the clip only has frames up to about then). slow: [from, to, speed], deepest first.
export const EPIC_CAM = { delay: 900, pre: 3400, post: 800, slow: [[-120, 100, 0.15], [-600, 350, 0.3]] };
// how long that takes to watch, from the moment you die: the server holds the respawn this long
export function epicCamMs(c = EPIC_CAM) {
  const xs = [...new Set([-c.pre, c.post, ...c.slow.flatMap(([a, b]) => [a, b])])].filter((x) => x >= -c.pre && x <= c.post).sort((a, b) => a - b);
  let ms = c.delay;
  for (let i = 0; i + 1 < xs.length; i++) {
    const mid = (xs[i] + xs[i + 1]) / 2, seg = c.slow.find(([a, b]) => mid >= a && mid <= b);
    ms += (xs[i + 1] - xs[i]) / (seg ? seg[2] : 1);
  }
  return Math.round(ms);
}
