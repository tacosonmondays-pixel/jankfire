// Anime speed lines: white streaks from the edges of the screen toward where you're flying.
// Drawn on a tiny 2D canvas over the game (crunchy on purpose), more lines the faster you go.
import * as THREE from 'three';

const W = 320, H = 180;
let cv = null, x = null, acc = 0, shown = false;
const v = new THREE.Vector3();

function init() {
  cv = document.getElementById('speedLinesCv'); // the settings checkbox is #speedLines
  if (!cv) return false;
  cv.width = W; cv.height = H;
  x = cv.getContext('2d');
  return true;
}

// speed in m/s, vel = world velocity, cam = the game camera
export function updateSpeedLines(dt, speed, vel, cam, extra = 0, enabled = true) {
  if (!cv && !init()) return;
  const k = enabled ? Math.max(extra, Math.min(1, (speed - 22) / 60)) : 0;
  acc += dt;
  if (acc < 1 / 30) return; // 30 fps is plenty for this
  acc = 0;
  if (k <= 0.01) { if (shown) { x.clearRect(0, 0, W, H); shown = false; } return; }
  shown = true;
  x.clearRect(0, 0, W, H);
  // focus point = where your velocity points on screen
  let fx = 0, fy = 0;
  if (speed > 1) {
    v.set(vel[0], vel[1], vel[2]).normalize().transformDirection(cam.matrixWorldInverse);
    if (v.z < -0.2) {
      const f = 1 / Math.tan((cam.fov * Math.PI) / 360);
      fx = Math.max(-0.7, Math.min(0.7, (v.x / -v.z) * f / cam.aspect));
      fy = Math.max(-0.7, Math.min(0.7, (v.y / -v.z) * f));
    }
  }
  const cx = (fx * 0.5 + 0.5) * W, cy = (-fy * 0.5 + 0.5) * H;
  const R = Math.hypot(W, H) * 0.75;
  const n = Math.round(14 + k * 70);
  // past mach 1 the lines go hot pink + yellow
  const hot = speed * 3.6 > 1235;
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const r0 = R * (0.42 + Math.random() * 0.3 - k * 0.12);
    const wdt = 0.6 + Math.random() * 2.6 * k;
    const ca = Math.cos(a), sa = Math.sin(a);
    x.globalAlpha = (0.12 + Math.random() * 0.4) * k;
    x.fillStyle = hot ? (Math.random() < 0.5 ? '#ff4fd8' : '#ffe14d') : '#ffffff';
    x.beginPath();
    x.moveTo(cx + ca * r0, cy + sa * r0);
    x.lineTo(cx + ca * R - sa * wdt, cy + sa * R + ca * wdt);
    x.lineTo(cx + ca * R + sa * wdt, cy + sa * R - ca * wdt);
    x.fill();
  }
  x.globalAlpha = 1;
}
