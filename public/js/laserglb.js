// Big Laser Pointer made in Blender (the weapon or a skin like the Cat Laser): gives it the hooks the code model has
// (gearmodels.js laserBuild) so the charge still shows: beam.js chargeLook lights userData.leds, tints userData.emit,
// presses userData.button (its y goes 0.047 -> 0.042), swells userData.orb; weapons.js swings userData.charm.
// The glb names its parts in meta.laser = { leds: [5 node names], emit, button, charm }; the orb is made here, at the muzzle.
import * as THREE from 'three';

const meshOf = (o) => { let m = null; if (o) o.traverse((c) => { if (!m && c.isMesh) m = c; }); return m; };
function glow(o, color) { // its own unlit material (chargeLook recolours each one on its own)
  const m = meshOf(o);
  if (!m) return null;
  m.material = new THREE.MeshBasicMaterial({ color });
  m.userData.noWrap = true;
  return m;
}
export function laserAuthored(id, g, mt) {
  if (id !== 'laser') return;
  const L = mt.laser && typeof mt.laser === 'object' ? mt.laser : {}, ud = g.userData;
  const node = (n) => (typeof n === 'string' && n ? g.getObjectByName(n) : null);
  for (const k of ['leds', 'emit', 'button', 'charm', 'orb']) delete ud[k];
  if (Array.isArray(L.leds)) { const leds = L.leds.map((n) => glow(node(n), 0x0b2a08)).filter(Boolean); if (leds.length) ud.leds = leds; }
  const em = glow(node(L.emit), 0x1d7a10); if (em) ud.emit = em;
  const b = node(L.button);
  if (b && b.parent) { // a holder under it so the press can set position.y = 0.047 (rest) like the code model's button
    g.updateMatrixWorld(true);
    const h = new THREE.Group(); h.position.set(0, b.position.y - 0.047, 0); b.parent.add(h); h.add(b); b.position.y = 0.047;
    ud.button = b;
  }
  const c = node(L.charm); if (c) ud.charm = c;
  const orb = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), new THREE.MeshBasicMaterial({ color: 0x39ff14, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false }));
  orb.userData.noWrap = true; orb.scale.setScalar(0.001); orb.visible = false;
  orb.position.copy(ud.muzzle || new THREE.Vector3(0, 0, -0.42)); g.add(orb); ud.orb = orb;
}
