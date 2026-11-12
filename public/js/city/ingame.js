// The streamed city inside the real game: world.js loads this (dynamic import) only when a map says `stream: <city>`
// (the story maps, registered by storymap.js), so PvP never downloads a byte of it. It runs a CityStream into the
// game's own BOXES (every collision call keeps working), blends the district sky / fog / light onto the scene each
// frame, holds you in place until the ground under you has streamed in, and runs the district gimmicks on you.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME, slip } from '../player.js';
import { sfx } from '../audio.js';
import { BOXES } from '/shared/map.js';
import { CityStream } from './stream.js';
import { cityUniforms } from './mats.js';
import { propEnv } from './props.js';
import { stepGimmicks } from '/shared/city/gimmicks.js';
import { K } from '../keys.js';
import { hud } from '../hud.js';
import { updateBeds, stopBeds } from './beds.js';
import { districtWeights } from '/shared/city/plan.js';
import { startGoo, stopGoo, updateGoo } from './gutgoo.js';
import { startHeart, stopHeart, updateHeart, gutBeat } from './bigheart.js'; // the Big Heart, the Gut's one beat and its ground fog
import { gradeActive, gradeEnv } from '../story/grade.js'; // story mode's eerie grade (darker, colder, closer fog)
import { startHills, stopHills, updateHills } from './hillfx.js'; // the hills' dust, loose rocks and litter

let S = null, hooks = null;
const tmp = new THREE.Color();
// world.js gives us its sky painter and the scene's lights
export function startCity(def, h) {
  stopCity();
  hooks = h;
  propEnv(G.renderer);
  S = new CityStream({ scene: G.scene, city: def.stream, preset: G.settings ? G.settings.jank : 1, boxes: BOXES, renderer: G.renderer }); // (renderer: new models' shaders warm up before they're drawn)
  S.useWas = false;
  startHeart(S.root); startGoo(S.root); startHills(S.root);
  // the city code took a second to arrive and you may have started falling: put you back where the map dropped you
  // (its spawn if you're near it, else a bit above where you are) and hold you there until the ground is in
  const sp = def.spawns && def.spawns[0];
  ME.hold = sp && Math.hypot(ME.pos[0] - sp[0], ME.pos[2] - sp[2]) < 30 ? sp.slice() : [ME.pos[0], ME.pos[1] + 30, ME.pos[2]];
  S.holding = true;
  return S;
}
export function stopCity() { stopHeart(); stopGoo(); stopHills(); if (S) { S.dispose(); S = null; } stopBeds(); G.cityReady = false; }
export const cityStream = () => S;

const GUT_FLUSH = new THREE.Color(0xa01428); // the colour the fog flushes (its beat is the Big Heart's: gutbeat.js)
let lastCall = 0;
export function updateCity(dt) {
  if (!S) return;
  if (G.settings && S.preset !== G.settings.jank) S.setPreset(G.settings.jank);
  S.update(G.camera, dt);
  updateHeart(dt, S, G.camera); // (ticks the Gut's clock: the fog below reads it)
  updateGoo(dt, S, G.camera); // the bile pools: bubbles that pop, green in the mist over them
  updateHills(dt); // landing dust, loose rocks, litter off the ridges (hillfx.js)
  updateBeds(G.joined ? districtWeights(S.city, G.camera.position.x, G.camera.position.z, 40) : [], dt); // the district music (fades out on the menu: the menu song is on)
  const e = S.env;
  if (S.weather.started) hud.msg('PAPER STORM', 1.6, 'brag');
  if (e && gradeActive()) gradeEnv(e, districtWeights(S.city, G.camera.position.x, G.camera.position.z, 40), cityUniforms.uHaze.value);
  if (e && G.scene.fog) {
    G.scene.fog.color.copy(e.fog); G.scene.fog.near = e.near; G.scene.fog.far = e.far;
    if (e.pulse > 0.01) { // the gut's fog has a heartbeat: lub, dub, rest. on each beat it closes in and flushes red
      const k = gutBeat.k * e.pulse; // (the same lub-dub curve as before, on the heart's clock: it closes in as the wave starts at the top of the heart)
      G.scene.fog.near = e.near * (1 - 0.4 * k); G.scene.fog.far = e.far * (1 - 0.14 * k); G.scene.fog.color.lerp(GUT_FLUSH, 0.3 * k);
    }
    if (hooks && hooks.sky) hooks.sky({ top: e.top.getHex(), mid: e.mid.getHex(), bot: e.bot.getHex() });
    const hemi = G.scene.children.find((o) => o.isHemisphereLight), sun = G.scene.children.find((o) => o.isDirectionalLight);
    if (hemi) { hemi.color.copy(e.hemi[0]); hemi.groundColor.copy(e.hemi[1]); hemi.intensity = e.hemi[2]; }
    if (sun) { sun.color.copy(e.sun[0]); sun.intensity = e.sun[1]; }
  }
  // the server moved you (a respawn, a story cut to a fight: a new spawn seq): hold there, not where you were
  if (ME.seq !== S.holdSeq) { const was = S.holdSeq; S.holdSeq = ME.seq; if (was !== undefined) ME.hold = ME.pos.slice(); } // (the first look is startCity's own hold)
  // the ground under you hasn't streamed in yet: wait for it (no falling through the world on a slow machine)
  if (S.holding || (ME.alive && !S.ready(ME.pos[0], ME.pos[2]))) {
    ME.vel[0] = ME.vel[1] = ME.vel[2] = 0;
    if (ME.hold) { ME.pos[0] = ME.hold[0]; ME.pos[1] = ME.hold[1]; ME.pos[2] = ME.hold[2]; }
    if (S.ready(ME.pos[0], ME.pos[2])) S.holding = false; // in: let go
  } else ME.hold = ME.pos.slice();
  G.cityReady = !S.holding && !S.first; G.cityProgress = S.progress(); // (the story's loading card and its background downloads wait for this)
  // the gimmicks: ziplines (use key), moving streets, lungs, acid
  if (!ME.alive) return;
  const use = K.isDown('use'), press = use && !S.useWas; S.useWas = use;
  const me = { pos: ME.pos, vel: ME.vel, ground: !!ME.onGround || !!ME.ground, zip: S.zip, bounceT: S.bounceT, padT: S.padT, slipT: S.slipT };
  const fwd = [-Math.sin(ME.yaw || 0), 0, -Math.cos(ME.yaw || 0)];
  const ev = stepGimmicks(me, S.triggers(), dt, { use: press, jump: K.isDown('jump') && !S.jumpWas, face: fwd, beat: cityUniforms.uBeat.value, sliding: !!ME.sliding });
  S.jumpWas = K.isDown('jump'); S.zip = me.zip; S.bounceT = me.bounceT; S.padT = me.padT; S.slipT = me.slipT;
  const now = performance.now();
  for (const x of ev) {
    // the playground's toys (playground.js): pads throw you, peels and marbles trip you (the PvP slip), the Banister
    if (x.kind === 'pad') { sfx.pad(); hud.msg(x.name || 'BOING', 1.2, 'brag'); lastCall = now; continue; }
    if (x.kind === 'slip') { slip(now, x.what); hud.msg(x.what === 'marbles' ? 'MARBLES!' : 'PEELED', 1.2, 'brag'); lastCall = now; continue; }
    if (x.kind === 'slide' && x.v > 18 && now - lastCall > 4000) { hud.msg(x.v > 26 ? 'BANISTER BURN' : 'THE BANISTER', 1.4, 'brag'); lastCall = now; continue; }
    const say = x.kind === 'zipOn' ? 'ZIPLINE!' : x.kind === 'bounce' ? (x.v > 30 ? 'BIG BREATH' : 'LUNG!') : x.kind === 'surf' ? 'RIDING THE BEAT' : x.kind === 'carry' ? (x.name === 'PERISTALSIS' ? 'THE STREET IS DIGESTING YOU' : 'IT ONLY GOES DOWN') : x.kind === 'hot' ? 'HOT ZONE: DO NOT LICK' : null;
    if (say && now - lastCall > (x.kind === 'carry' || x.kind === 'hot' ? 5000 : 600)) { hud.msg(say, 1.4, 'brag'); lastCall = now; }
  }
  void tmp;
}
