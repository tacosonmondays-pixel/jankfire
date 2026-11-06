// The streamed city inside the real game: world.js loads this (dynamic import) only when a map says `stream: <city>`
// (the story maps, registered by storymap.js), so PvP never downloads a byte of it. It runs a CityStream into the
// game's own BOXES (every collision call keeps working), blends the district sky / fog / light onto the scene each
// frame, holds you in place until the ground under you has streamed in, and runs the district gimmicks on you.
import * as THREE from 'three';
import { G } from '../ctx.js';
import { ME } from '../player.js';
import { BOXES } from '/shared/map.js';
import { CityStream } from './stream.js';
import { cityUniforms } from './mats.js';
import { propEnv } from './props.js';
import { stepGimmicks } from '/shared/city/gimmicks.js';
import { K } from '../keys.js';
import { hud } from '../hud.js';

let S = null, hooks = null;
const tmp = new THREE.Color();
// world.js gives us its sky painter and the scene's lights
export function startCity(def, h) {
  stopCity();
  hooks = h;
  propEnv(G.renderer);
  S = new CityStream({ scene: G.scene, city: def.stream, preset: G.settings ? G.settings.jank : 1, boxes: BOXES });
  S.useWas = false;
  // the city code took a second to arrive and you may have started falling: put you back where the map dropped you
  // (its spawn if you're near it, else a bit above where you are) and hold you there until the ground is in
  const sp = def.spawns && def.spawns[0];
  ME.hold = sp && Math.hypot(ME.pos[0] - sp[0], ME.pos[2] - sp[2]) < 30 ? sp.slice() : [ME.pos[0], ME.pos[1] + 30, ME.pos[2]];
  S.holding = true;
  return S;
}
export function stopCity() { if (S) { S.dispose(); S = null; } }
export const cityStream = () => S;

let lastCall = 0;
export function updateCity(dt) {
  if (!S) return;
  if (G.settings && S.preset !== G.settings.jank) S.setPreset(G.settings.jank);
  S.update(G.camera, dt);
  const e = S.env;
  if (S.weather.started) hud.msg('PAPER STORM', 1.6, 'brag');
  if (e && G.scene.fog) {
    G.scene.fog.color.copy(e.fog); G.scene.fog.near = e.near; G.scene.fog.far = e.far;
    if (hooks && hooks.sky) hooks.sky({ top: e.top.getHex(), mid: e.mid.getHex(), bot: e.bot.getHex() });
    const hemi = G.scene.children.find((o) => o.isHemisphereLight), sun = G.scene.children.find((o) => o.isDirectionalLight);
    if (hemi) { hemi.color.copy(e.hemi[0]); hemi.groundColor.copy(e.hemi[1]); hemi.intensity = e.hemi[2]; }
    if (sun) { sun.color.copy(e.sun[0]); sun.intensity = e.sun[1]; }
  }
  // the ground under you hasn't streamed in yet: wait for it (no falling through the world on a slow machine)
  if (S.holding || (ME.alive && !S.ready(ME.pos[0], ME.pos[2]))) {
    ME.vel[0] = ME.vel[1] = ME.vel[2] = 0;
    if (ME.hold) { ME.pos[0] = ME.hold[0]; ME.pos[1] = ME.hold[1]; ME.pos[2] = ME.hold[2]; }
    if (S.ready(ME.pos[0], ME.pos[2])) S.holding = false; // in: let go
  } else ME.hold = ME.pos.slice();
  // the gimmicks: ziplines (use key), moving streets, lungs, acid
  if (!ME.alive) return;
  const use = K.isDown('use'), press = use && !S.useWas; S.useWas = use;
  const me = { pos: ME.pos, vel: ME.vel, ground: !!ME.onGround || !!ME.ground, zip: S.zip, bounceT: S.bounceT };
  const fwd = [-Math.sin(ME.yaw || 0), 0, -Math.cos(ME.yaw || 0)];
  const ev = stepGimmicks(me, S.triggers(), dt, { use: press, jump: K.isDown('jump') && !S.jumpWas, face: fwd, beat: cityUniforms.uBeat.value });
  S.jumpWas = K.isDown('jump'); S.zip = me.zip; S.bounceT = me.bounceT;
  const now = performance.now();
  for (const x of ev) {
    const say = x.kind === 'zipOn' ? 'ZIPLINE!' : x.kind === 'bounce' ? (x.v > 30 ? 'BIG BREATH' : 'LUNG!') : x.kind === 'surf' ? 'RIDING THE BEAT' : x.kind === 'carry' ? (x.name === 'PERISTALSIS' ? 'THE STREET IS DIGESTING YOU' : 'IT ONLY GOES DOWN') : x.kind === 'hot' ? 'HOT ZONE: DO NOT LICK' : null;
    if (say && now - lastCall > (x.kind === 'carry' || x.kind === 'hot' ? 5000 : 600)) { hud.msg(say, 1.4, 'brag'); lastCall = now; }
  }
  void tmp;
}
