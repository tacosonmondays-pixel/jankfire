// First-person gun bob: one dip per footstep (same stride lengths as everyone's third-person legs), bigger the faster
// you go, a steady rattle when you're zooming, and a stumble when you slip on marbles. Screen shake off = calmer.
import { ME } from './player.js';
import { G } from './ctx.js';

const TAU = Math.PI * 2;
const cl = (v, a, b) => (v < a ? a : v > b ? b : v);
const ss = (a, b, v) => { const t = cl((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const B = { x: 0, y: 0, rx: 0, rz: 0, ph: 0, k: 0, slipT: -1e9, slipping: false };

// hs: your ground speed. returns offsets for the viewmodel's base pose (reused object, no garbage)
export function vmBob(dt, now, hs) {
  const calm = G.settings && G.settings.shake === false ? 0.4 : 1;
  const g = ME.onGround && !ME.sliding;
  const L = Math.min(4.3, 1.2 + 0.29 * hs) * (ME.crouching ? 0.7 : ME.walking ? 0.65 : 1); // metres per stride (two steps)
  if (g) B.ph += Math.min(TAU * 4.5 * dt, (hs * dt / L) * TAU);
  B.k += ((g ? Math.min(1, hs / 5) : 0) - B.k) * Math.min(1, dt * 10);
  const run = ss(6, 10, hs), spr = ss(11.5, 14, hs), zoom = ss(17, 24, hs);
  const amp = (0.011 + 0.008 * run + 0.01 * spr) * (1 - zoom * 0.6) * B.k * (ME.crouching ? 0.6 : ME.walking ? 0.55 : 1) * calm;
  const s = Math.sin(B.ph), d = Math.abs(Math.cos(B.ph)) - 0.5; // d: a sharp dip at each foot strike
  B.x = s * amp * 1.1;
  B.y = d * amp * 1.6 + Math.sin(now * 0.055) * 0.0018 * zoom * B.k * calm;
  B.rx = d * amp * 2.5;
  B.rz = s * amp * 3.5;
  // marbles: the gun gets flung up and wobbles while your feet are gone, then settles
  const slipping = now < (ME.slipUntil || 0);
  if (slipping && !B.slipping) B.slipT = now;
  B.slipping = slipping;
  const t = (now - B.slipT) / 1000;
  if (t >= 0 && t < 2) {
    const fling = ss(0, 0.1, t) * (1 - ss(0.1, 0.6, t)), wob = ss(0.05, 0.25, t) * (1 - ss(1.4, 2, t));
    B.rx += (fling * 0.85 + Math.sin(t * 9) * 0.12 * wob) * calm;
    B.rz += (fling * 0.5 + Math.sin(t * 14) * 0.25 * wob) * calm;
    B.x -= (fling * 0.05 + Math.sin(t * 7) * 0.015 * wob) * calm;
    B.y += (fling * 0.06 - wob * 0.03) * calm;
  }
  return B;
}
