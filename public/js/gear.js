// The new gear, client hub: wires the Big Laser Pointer (beam.js), the Instant Camera (photo.js), the Pop Quiz (quiz.js)
// and the Night Vision Goggles (goggles.js) into the game: server messages, keys, the G item hook, every frame.
import { W } from './weapons.js';
import { G } from './ctx.js';
import { ME } from './player.js';
import { net } from './net.js';
import { hud } from './hud.js';
import { recordEv, RP_HOOKS } from './replay.js';
import { beamStart, updateBeams, remoteCharge, beamsClear } from './beam.js';
import { WEAPONS } from '/shared/weapons.js';
import { onSnap, onPhotoNope, onFrame, onFrameGone, onPhotoTp, teleFx, updatePhoto, photoReset, holdingPhoto } from './photo.js';
import { onQuiz, onQuizEnd, quizKey, updateQuiz, quizReset, quizDeath } from './quiz.js';
import { nvToggle, nvFlashKey, onFlashed, nvFlashFx, updateGoggles, gogglesReset } from './goggles.js';

const L = WEAPONS.laser;
// G with one of these: true = handled here (no charge spent locally). the camera's first press is a free photo, the
// second prints it (that costs the charge, the normal way); the goggles' G is on/off, nvgFlash (middle click / N) fires the flash through useItem
function itemHook(id) {
  if (id === 'camera') {
    W.camPrint = holdingPhoto();
    if (W.camPrint) return false;
    W.itemT = performance.now();
    net.send({ t: 'item', i: 'camera', o: [ME.pos[0], ME.pos[1] + 1.6, ME.pos[2]], d: lookDir() });
    return true;
  }
  if (id === 'nvg') {
    if (!W.nvFire) { nvToggle(); return true; }
    W.nvFired = true;
    return false;
  }
  return false;
}
function lookDir() { const cp = Math.cos(ME.pitch); return [-Math.sin(ME.yaw) * cp, Math.sin(ME.pitch), -Math.cos(ME.yaw) * cp].map((x) => Math.round(x * 100) / 100); }

export function initGear() {
  W.itemHook = itemHook;
  net.on('snap', onSnap);
  net.on('photo!', onPhotoNope);
  net.on('frame', onFrame);
  net.on('framex', onFrameGone);
  net.on('ptp', onPhotoTp);
  net.on('quiz', onQuiz);
  net.on('quizx', onQuizEnd);
  net.on('flashed', onFlashed);
  // replays: someone else's beam follows their ghost's aim
  RP_HOOKS.push({ ev(m, ghosts) {
    if (m.t !== 'fx' || m.k !== 'beam') return false;
    const g = ghosts.get(m.id);
    if (g) beamStart(m.id, m.c, m.dur, () => (g.alive ? { o: g.muzzle(), d: g.look() } : null));
    return true;
  }, stop() { beamsClear(); } });
}
// the 'fx' kinds that are ours. true = handled
export function gearFx(m) {
  if (m.k === 'beam') {
    recordEv(m);
    const r = G.remotes.get(m.id);
    if (r) { r.lzK = 0; beamStart(m.id, m.c, m.dur, () => (r.alive && G.remotes.get(m.id) === r ? { o: r.muzzle(), d: r.look() } : null)); }
    return true;
  }
  if (m.k === 'tele') { recordEv(m); teleFx(m); return true; }
  if (m.k === 'nvflash') { recordEv(m); if (m.id !== G.myId) nvFlashFx(m); return true; }
  return false;
}
// named actions (the rebindable-keys work hooks these up): the goggles' flash is the middle mouse button, N on the
// keyboard. never H: H drops your gun in Plant & Defuse
export const GEAR_ACTIONS = { nvgFlash: { keys: ['KeyN'], mouse: [1] } };
// keys: 1-4 answer a pop quiz (and nothing else while you sit one), nvgFlash fires the goggles' flash
export function gearKeyDown(e) {
  if (quizKey(e)) return true;
  if (GEAR_ACTIONS.nvgFlash.keys.includes(e.code) && !e.repeat) { nvFlashKey(); return true; }
  return false;
}
// mousedown: true = it was ours (main.js asks before its own buttons)
export function gearMouseDown(e) {
  if (!GEAR_ACTIONS.nvgFlash.mouse.includes(e.button)) return false;
  e.preventDefault(); // no autoscroll on a middle click
  nvFlashKey();
  return true;
}
export function updateGear(dt, now) {
  updateBeams(dt, now);
  updatePhoto(dt, now);
  updateQuiz(dt, now);
  updateGoggles(dt, now);
  for (const r of G.remotes.values()) remoteCharge(r, dt);
}
export function gearSpawn() { quizReset(); gogglesReset(); }
export function gearLeave() { photoReset(); quizReset(); gogglesReset(); beamsClear(); }
// kill feed + death screen lines for the new gear (null = not ours)
export function gearKillParts(m, kn, kc, vn, vc, wname, wcolor) {
  if (m.w === 'quiz') return m.k ? [[kn, kc], [`  [${wname('quiz')}]  `, wcolor('quiz')], [vn, vc], ['  (failed maths)', '#aaa']] : [[vn, vc], ['  failed a pop quiz', '#7fffd4']];
  if (m.w === 'camera') return [[kn, kc], [`  [${wname('camera')}]  `, wcolor('camera')], [vn, vc], ['  (telefragged)', '#aaa']];
  return null;
}
export function gearDeathLine(m) { return m.w === 'quiz' ? quizDeath() : null; }
export { hud, L };
