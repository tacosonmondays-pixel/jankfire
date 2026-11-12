// OVERDUE camera shots: named framings aimed at actors, shared by cutscenes and comic panels.
// shotPose(c, u, who, where, eyeP) -> { pos, look, roll }. c = { shot, target, from, path, look, offset, r, turn, up },
// u = 0..1 through the shot (dollies and orbits move with it), who(k) -> actor, where(mark) -> [x, y, z]
import * as THREE from 'three';
import { headPos } from './actors.js';
import { faceFwd, reachOf } from './shotfit.js'; // face shots: which way the face really looks, and standing clear of the body

const v1 = new THREE.Vector3(), fw = new THREE.Vector3(), side = new THREE.Vector3(), hf = new THREE.Vector3();
const ss = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
export const SHOTS = ['closeup', 'extreme', 'over', 'lowAngle', 'wide', 'dolly', 'orbit', 'whip', 'top', 'two'];

export function shotPose(c, u, who, where, eyeP) {
  const pos = new THREE.Vector3(), look = new THREE.Vector3(), e = ss(u);
  let roll = 0;
  if (c.path) {
    const pts = c.path.map((m) => new THREE.Vector3(...where(m)));
    const curve = new THREE.CatmullRomCurve3(pts.length > 1 ? pts : [pts[0], pts[0].clone().add(new THREE.Vector3(0, 0.01, 0))]);
    curve.getPoint(e, pos);
    if (c.look) aimAt(c.look, who, where, look); else curve.getPoint(Math.min(1, e + 0.05), look);
  } else {
    const a = who(c.target);
    if (!a) return null;
    headPos(a, v1);
    const s = a.ch.root.scale.y, H = a.L.height;
    fw.set(-Math.sin(a.yaw), 0, -Math.cos(a.yaw)); side.set(Math.cos(a.yaw), 0, -Math.sin(a.yaw));
    const big = Math.max(1, s * 0.85) + (a.L.look === 'gordo' ? 0.35 : 0);
    switch (c.shot || 'closeup') {
      case 'closeup': if (faceFwd(a, hf)) { fw.copy(hf); side.set(-fw.z, 0, fw.x); } pos.copy(v1).addScaledVector(fw, Math.max((1.3 - 0.25 * e) * big, reachOf(a, v1, fw) + 0.5)).addScaledVector(side, 0.35); look.copy(v1); look.y -= 0.05; break;
      case 'extreme': if (faceFwd(a, hf)) fw.copy(hf); pos.copy(v1).addScaledVector(fw, 0.62 * big); look.copy(v1); break;
      case 'over': { const b = who(c.from); if (!b) { pos.copy(v1).addScaledVector(fw, 2); look.copy(v1); break; } headPos(b, pos); const d = v1.clone().sub(pos).setY(0).normalize(); pos.addScaledVector(d, -0.75).addScaledVector(new THREE.Vector3(-d.z, 0, d.x), -0.45); pos.y += 0.1; look.copy(v1); break; }
      case 'two': { const b = who(c.from); const m = b ? headPos(b, new THREE.Vector3()).add(v1).multiplyScalar(0.5) : v1.clone(); const d = b ? v1.clone().sub(headPos(b, new THREE.Vector3())) : fw.clone(); const L = Math.max(1.5, d.length()); d.setY(0).normalize(); pos.copy(m).add(new THREE.Vector3(-d.z, 0, d.x).multiplyScalar(L * 1.25 + 1)); pos.y += 0.2; look.copy(m); break; }
      case 'low': case 'lowAngle': pos.copy(a.ch.root.position).addScaledVector(fw, 2.2 * s + 0.6).addScaledVector(side, 0.8); pos.y += 0.25; look.copy(v1); look.y -= H * 0.1; break;
      case 'wide': pos.copy(a.ch.root.position).addScaledVector(fw, 5 + 1.5 * e).addScaledVector(side, 2.5); pos.y += 2.2; look.copy(a.ch.root.position); look.y += H * 0.5; break;
      case 'dolly': pos.copy(v1).addScaledVector(fw, (3.6 - 2.2 * e) * big).addScaledVector(side, 1.2 - 1.6 * e); pos.y += 0.1; look.copy(v1); break;
      case 'orbit': { const ang = a.yaw + (c.from0 ?? 0.6) + e * (c.turn ?? 1.6), r = (c.r ?? 2.6) * big; pos.set(v1.x - Math.sin(ang) * r, v1.y + (c.up ?? 0.3), v1.z - Math.cos(ang) * r); look.copy(v1); look.y -= H * 0.15; break; }
      case 'whip': { const k = ss(Math.min(1, u * 4)); pos.copy(v1).addScaledVector(fw, 2.2 * s).addScaledVector(side, 0.6); if (eyeP) pos.lerp(new THREE.Vector3(...eyeP), 1 - k); look.copy(v1); roll = (1 - k) * 0.4; break; }
      case 'top': pos.copy(a.ch.root.position); pos.y += 9; pos.z += 0.01; look.copy(a.ch.root.position); break;
      default: pos.copy(v1).addScaledVector(fw, 2); look.copy(v1);
    }
  }
  if (c.offset) pos.add(new THREE.Vector3(...c.offset));
  if (c.lookOffset) look.add(new THREE.Vector3(...c.lookOffset));
  return { pos, look, roll: (c.roll || 0) + roll };
}
function aimAt(m, who, where, out) { const a = typeof m === 'string' ? who(m) : null; if (a) return headPos(a, out); const p = where(m); return out.set(p[0], p[1], p[2]); }
