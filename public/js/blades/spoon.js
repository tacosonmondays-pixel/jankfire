// Spoon knife skin: a stamped 18/10 stainless serving spoon, held like a knife (bowl up, tip to -Z). It still stabs.
//   Overall ~215 mm: a 140 mm flat handle (22 mm wide at the rounded paddle end, narrowing to 7 mm at the neck, 2.5 mm
//   thick), a short neck that dips the bowl a little below the handle line, and a 65 x 44 mm oval bowl 11 mm deep with a
//   rolled rim. The handle rises slightly toward the butt, like real flatware, so the knuckles clear the bowl.
// Refs: common serving spoon sizes (21-23 cm overall, bowl 6-7 cm long, 4-5 cm wide); 18/10 flatware is 2-3 mm thick.
// Held like every knife: the grip axis is y = 0 and the hand sits over z -0.036 .. +0.08.
import { THREE, mat } from './kit.js';

const MM = 0.001;
const STEEL = 0xd6dbe1, RIM = 0xf2f5f8, BOWL_IN = 0xc9cfd6;
const BUTT_Z = 0.092, NECK_Z = -0.042, BOWL_Z0 = -0.058, BOWL_L = 0.065, BOWL_W = 0.044, BOWL_D = 0.011;
const T = 2.5 * MM; // handle thickness

// the handle seen from above: [x, z] outline, a rounded paddle at the butt tapering into the neck
function handleShape() {
  const pts = [];
  const half = (z) => { // half width (m) along the handle
    const f = (BUTT_Z - z) / (BUTT_Z - NECK_Z); // 0 at the butt, 1 at the neck
    return (11 - 7.5 * Math.pow(f, 0.8)) * MM;
  };
  const N = 14;
  for (let i = 0; i <= N; i++) { const z = BUTT_Z - 0.012 - (BUTT_Z - 0.012 - NECK_Z) * (i / N); pts.push([half(z), z]); }
  // the neck: narrow, then flaring into the bowl's back
  pts.push([3.2 * MM, -0.05], [6 * MM, BOWL_Z0 - 0.002]);
  const right = pts.slice(), left = pts.slice().reverse().map(([x, z]) => [-x, z]);
  // the rounded paddle end (half ellipse past BUTT_Z - 12 mm)
  const cap = [];
  for (let i = 1; i < 10; i++) { const a = Math.PI * (i / 10); cap.push([Math.cos(a) * 11 * MM, BUTT_Z - 0.012 + Math.sin(a) * 12 * MM]); }
  const all = [...right.reverse(), ...cap.reverse().map(([x, z]) => [x, z]), ...left.reverse()];
  const s = new THREE.Shape();
  all.forEach(([x, z], i) => (i ? s.lineTo(x, z) : s.moveTo(x, z))); // shape y = z: rotateX(+90deg) sends shape y to model z
  return s;
}

export function build(root) {
  // built bowl-up, then turned on its side so the bowl faces out like a knife's flat (reads from the side and in first person)
  const g = new THREE.Group(); g.rotation.z = -Math.PI / 2; root.add(g);
  // handle: the flat stamped blank, a touch of bevel, tilted up toward the butt (about 5 degrees)
  const hg = new THREE.ExtrudeGeometry(handleShape(), { depth: T, bevelEnabled: true, bevelThickness: 0.4 * MM, bevelSize: 0.5 * MM, bevelSegments: 1, curveSegments: 6 });
  hg.rotateX(Math.PI / 2); // shape (x, y) -> (x, z); extrusion -> -y
  hg.translate(0, T / 2, 0);
  const handle = new THREE.Mesh(hg, mat(STEEL));
  handle.rotation.x = -0.085; // butt up
  g.add(handle);
  // bowl: an oval half-shell, opening up, sitting a little below the handle line, with a rolled rim
  const cz = BOWL_Z0 - BOWL_L / 2, rimY = -1.2 * MM;
  const shell = (sx, sy, sz, color, side) => {
    const geo = new THREE.SphereGeometry(1, 20, 8, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2); // the lower half
    const m = new THREE.Mesh(geo, mat(color).clone());
    m.material.side = side;
    m.scale.set(sx, sy, sz); m.position.set(0, rimY, cz);
    return m;
  };
  g.add(shell(BOWL_W / 2, BOWL_D, BOWL_L / 2, STEEL, THREE.FrontSide)); // the back of the bowl
  g.add(shell(BOWL_W / 2 - 0.9 * MM, BOWL_D - 0.9 * MM, BOWL_L / 2 - 0.9 * MM, BOWL_IN, THREE.BackSide)); // the inside, seen from above
  const rim = new THREE.Mesh(new THREE.TorusGeometry(1, 0.03, 4, 28), mat(RIM));
  rim.rotation.x = Math.PI / 2; rim.scale.set(BOWL_W / 2 - 0.4 * MM, BOWL_L / 2 - 0.4 * MM, 1.4 * MM);
  rim.position.set(0, rimY, cz); g.add(rim);
  // the neck dips down into the bowl's back
  const neck = new THREE.Mesh(new THREE.BoxGeometry(5 * MM, T, 0.02), mat(STEEL));
  neck.position.set(0, -0.6 * MM, -0.05); neck.rotation.x = 0.07; g.add(neck);

  root.userData.muzzle = new THREE.Vector3(rimY, 0, BOWL_Z0 - BOWL_L);
  root.userData.len = BUTT_Z + 0.012 - (BOWL_Z0 - BOWL_L); // ~0.227
}
// a hat on the handle, over the middle of the grip
export const hatAt = [[0, 0.0095, 0.035], 0.045]; // on the handle's top edge (it's on its side)
