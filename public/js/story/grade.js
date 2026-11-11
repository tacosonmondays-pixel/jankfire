// OVERDUE's world grade (owner: "can you add a darker filter,? I feel like its not very eerie.."). Story maps only:
// PvP never imports this. Two cheap halves that work with the shaders (post.js) OFF, on every preset:
//   1. the 3D image itself gets darker: the district's sky light and sun go down and colder, the fog and sky go
//      darker and greyer and close in (city/ingame.js calls gradeEnv on the blended district env each frame; the
//      train, which isn't a streamed city, gets the same from gradeFrame). glows, neon, emissive eyes and the lamps'
//      own point lights are untouched, so they pop more, not less
//   2. a fixed full-screen overlay (#stGrade) UNDER the HUD and the story UI: a cold multiply tint, a soft vignette,
//      a little desaturation and a tiled film grain. opacity only, no filter on the canvas (that would cost a pass)
import * as THREE from 'three';
import { G } from '../ctx.js';
import { MAP, MAPS } from '/shared/map.js';

// THE KNOB TABLE. per district (the slice's district ids, plus 'train' for the Under-Hill Loop fight):
//   light: sky light + sun x this    sky: fog + sky colours x this    fogIn: fog near/far x this (lower = closer)
//   desat: how much of the colour goes (light, fog, sky; and the overlay's share)    cold: lean toward COLD
//   vig: vignette strength    tint: the overlay's cold multiply    grain: film grain    flicker: the slow light dip
// the top-level ones scale every district (0 = none of it, 1 = as tabled): tune the whole look from here
export const STORY_GRADE = {
  on: true, // master switch (settings > video > "eerie story filter" turns it off for you: today's look)
  dark: 1, desat: 1, vignette: 1, grain: 1, flicker: 1,
  cold: 0x56709c, // what the dark leans toward (moonlight blue-grey, not navy)
  tintCol: '#7a88b0', // the overlay's multiply colour (a cold blue-grey: darkens and cools at once)
  perDistrict: {
    // the Bottom at dusk: cold and dim, the warm pools are the lamps' own lights (stream.js pickLights)
    bottom: { light: 0.32, sky: 0.32, fogIn: 0.5, desat: 0.5, cold: 0.5, vig: 1, tint: 0.55, grain: 0.09, flicker: 0.07 },
    // the Commute: grey, empty, foggy (the dusty orange is mostly gone)
    commute: { light: 0.38, sky: 0.42, fogIn: 0.3, desat: 0.78, cold: 0.4, vig: 0.95, tint: 0.5, grain: 0.09, flicker: 0 },
    // the Gut: red-black. the red stays (it's the point), the heart's flush still reads on top of it (ingame.js)
    gut: { light: 0.42, sky: 0.36, fogIn: 0.8, desat: 0.2, cold: 0.12, vig: 1, tint: 0.4, grain: 0.09, flicker: 0.09 },
    border: { light: 0.38, sky: 0.36, fogIn: 0.65, desat: 0.35, cold: 0.3, vig: 1, tint: 0.48, grain: 0.09, flicker: 0.07 },
    // the train tunnel: near-black between the bulbs (the fight's own lamps and the knots' glow stay as bright)
    train: { light: 0.45, sky: 0.6, fogIn: 0.8, desat: 0.3, cold: 0.35, vig: 1, tint: 0.4, grain: 0.1, flicker: 0.1 },
  },
};
const NONE = { light: 1, sky: 1, fogIn: 1, desat: 0, cold: 0, vig: 0, tint: 0, grain: 0, flicker: 0 };
const KEYS = Object.keys(NONE);

let armed = false, el = null, clock = 0;
const cold = new THREE.Color(), _c = new THREE.Color(), K = { ...NONE };
// story mode turns it on (boot.js init): the overlay element and the settings row only exist from here
export function initGrade() {
  armed = true;
  const row = document.getElementById('fxEerieRow'); if (row) row.classList.remove('hidden');
  el = document.createElement('div'); el.id = 'stGrade'; el.className = 'hidden';
  el.innerHTML = '<i class="gs"></i><i class="gt"></i><i class="gv"></i><i class="gg"></i>';
  const game = document.getElementById('game'); if (game) game.after(el); else document.body.prepend(el); // right over the canvas: everything else draws on top
  try { // the grain: one small tile of noise, made once (tiled and jittered by CSS, never redrawn)
    const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'), im = x.createImageData(128, 128);
    for (let i = 0; i < im.data.length; i += 4) { const v = Math.random() * 2 - 1; im.data[i] = im.data[i + 1] = im.data[i + 2] = v > 0 ? 255 : 0; im.data[i + 3] = (Math.abs(v) * (v > 0 ? 40 : 80)) | 0; } // (faint black or fainter white specks: a plain blend, no blend mode to pay for, and the blacks don't lift)
    x.putImageData(im, 0, 0); el.querySelector('.gg').style.backgroundImage = `url(${c.toDataURL()})`;
  } catch (e) { /* no grain, still graded */ }
}
// on: story mode, a story map, and you didn't switch it off
export function gradeActive() {
  if (!armed || !STORY_GRADE.on || (G.settings && G.settings.fxEerie === false)) return false;
  const d = MAPS[MAP.id]; return !!(d && d.story);
}
// the knobs here: the districts round you blended by weight (ws: districtWeights), or one named district
function knobs(ws, id) {
  for (const k of KEYS) K[k] = 0;
  let sum = 0;
  const add = (t, w) => { for (const k of KEYS) K[k] += (t[k] ?? NONE[k]) * w; sum += w; };
  if (ws) for (const [d, w] of ws) add(STORY_GRADE.perDistrict[d.id] || NONE, w);
  else add(STORY_GRADE.perDistrict[id] || NONE, 1);
  if (!sum) Object.assign(K, NONE); else for (const k of KEYS) K[k] /= sum;
  const g = STORY_GRADE, mix = (v, one, s) => one + (v - one) * s; // scale a knob's distance from "no grade"
  K.light = mix(K.light, 1, g.dark); K.sky = mix(K.sky, 1, g.dark); K.fogIn = mix(K.fogIn, 1, g.dark);
  K.desat *= g.desat; K.cold *= g.dark; K.vig *= g.vignette; K.tint *= g.dark; K.grain *= g.grain; K.flicker *= g.flicker;
  return K;
}
// a slow, barely-there dip: mostly nothing, now and then the light sags for a second (three slow sines agreeing)
function flick(t) { const n = Math.sin(t * 0.37) * Math.sin(t * 0.91 + 2) * Math.sin(t * 2.3 + 1); return Math.max(0, n) * (0.8 + 0.2 * Math.sin(t * 17)); }
// grey a colour toward its own brightness, lean it cold, darken it
function grade(c, desat, lean, k) {
  const l = c.r * 0.299 + c.g * 0.587 + c.b * 0.114;
  c.r += (l - c.r) * desat; c.g += (l - c.g) * desat; c.b += (l - c.b) * desat;
  _c.copy(cold).multiplyScalar(Math.max(l, 0.05) * 1.6); c.lerp(_c, lean);
  return c.multiplyScalar(k);
}
// the streamed city: grade the district env (stream.js applyEnv makes a fresh one each frame, so this never stacks)
export function gradeEnv(e, ws, haze) {
  if (!e || e._graded) return;
  e._graded = true;
  const k = knobs(ws); cold.setHex(STORY_GRADE.cold);
  for (const c of [e.fog, e.top, e.mid, e.bot]) grade(c, k.desat, k.cold * 0.6, k.sky);
  e.near *= k.fogIn; e.far = Math.max(e.near + 30, e.far * k.fogIn);
  const f = 1 - k.flicker * flick(clock);
  grade(e.hemi[0], k.desat * 0.8, k.cold * 0.5, 1); grade(e.hemi[1], k.desat, k.cold, 0.8); e.hemi[2] *= k.light * f; // (the ground bounce goes coldest: cold shadows)
  grade(e.sun[0], k.desat * 0.6, k.cold * 0.4, 1); e.sun[1] *= k.light * f;
  if (haze) haze.copy(e.fog).lerp(e.mid, 0.35); // the far city's haze, with the graded colours (stream.js set it ungraded)
}
// a story map that isn't a streamed city (the train): its lights and fog were set once by the map. grade them from
// those, and pick up a new base whenever something else sets them (a reload, a relight)
const T = { id: '', hemi: 0, sun: 0, near: 0, far: 0, fog: new THREE.Color(), set: null };
function gradeFixed(on) {
  const sc = G.scene, fog = sc && sc.fog, hemi = sc && sc.children.find((o) => o.isHemisphereLight), sun = sc && sc.children.find((o) => o.isDirectionalLight);
  if (!fog || !hemi || !sun) return;
  const S = T.set, moved = !S || T.id !== MAP.id || hemi.intensity !== S.hemi || sun.intensity !== S.sun || fog.near !== S.near || fog.far !== S.far || fog.color.getHex() !== S.fog;
  if (moved) { T.id = MAP.id; T.hemi = hemi.intensity; T.sun = sun.intensity; T.near = fog.near; T.far = fog.far; T.fog.copy(fog.color); }
  if (!on) { if (S && !moved) { hemi.intensity = T.hemi; sun.intensity = T.sun; fog.near = T.near; fog.far = T.far; fog.color.copy(T.fog); } T.set = null; return; } // switched off: put the map's own back
  const k = knobs(null, MAP.id === 'story_train' ? 'train' : MAP.id); cold.setHex(STORY_GRADE.cold);
  const f = 1 - k.flicker * flick(clock);
  hemi.intensity = T.hemi * k.light * f; sun.intensity = T.sun * k.light * f;
  fog.near = T.near * k.fogIn; fog.far = Math.max(fog.near + 10, T.far * k.fogIn); grade(fog.color.copy(T.fog), k.desat, k.cold * 0.6, k.sky);
  T.set = { hemi: hemi.intensity, sun: sun.intensity, near: fog.near, far: fog.far, fog: fog.color.getHex() };
}
// every frame (boot.js frame): the clock, the train's grade and the overlay
let shown = false, last = '';
export function gradeFrame(now) {
  if (!armed || !el) return;
  clock = now / 1000;
  const on = gradeActive(), d = MAPS[MAP.id];
  if (d && d.story && !d.stream) gradeFixed(on); // (a streamed city grades its env in ingame.js)
  if (on !== shown) { shown = on; el.classList.toggle('hidden', !on); }
  if (!on) return;
  const k = d && d.stream ? K : knobs(null, MAP.id === 'story_train' ? 'train' : MAP.id); // (K: what gradeEnv blended this frame)
  const chunky = !!(G.settings && G.settings.jank <= 1), v = `${(k.desat * 0.5).toFixed(2)}|${k.tint.toFixed(2)}|${k.vig.toFixed(2)}|${k.grain.toFixed(3)}|${chunky}`;
  if (v === last) return; // only touch the style when a district border changes it
  last = v; const [s, t, g, n] = v.split('|');
  el.style.setProperty('--gs', s); el.style.setProperty('--gt', t); el.style.setProperty('--gv', g); el.style.setProperty('--gg', n);
  el.style.setProperty('--gtc', STORY_GRADE.tintCol);
  el.classList.toggle('chunky', chunky); // Potato / Crusty: bigger grain, like their pixels
}
