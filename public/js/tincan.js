// the TROLLEY's tin can (its LMB, a bouncing projectile: 'trcan'). a chunky soup can: tin body with rolled rims, a
// bright label with a stripe, a half-open lid flapping off the top. the geometry is shared by every can
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

let KIT = null;
function kit() {
  if (KIT) return KIT;
  const R = 0.2, H = 0.42;
  const rims = mergeGeometries([0.5, 0.17, -0.17, -0.5].map((y) => new THREE.TorusGeometry(R + 0.006, 0.014, 4, 18).rotateX(Math.PI / 2).translate(0, y * H, 0)));
  const ends = new THREE.CircleGeometry(R, 18).rotateX(Math.PI / 2).translate(0, -H / 2, 0); // (the bottom: the top's open)
  const lid = new THREE.CylinderGeometry(R * 0.98, R * 0.98, 0.012, 18).translate(R, 0, 0); // hinged at its edge
  // the label: a canvas strip (red with a cream band and a cartoon tomato-ish blob)
  const c = document.createElement('canvas'); c.width = 128; c.height = 32;
  const g = c.getContext('2d');
  g.fillStyle = '#e8262e'; g.fillRect(0, 0, 128, 32);
  g.fillStyle = '#fff3c4'; g.fillRect(0, 11, 128, 10);
  g.fillStyle = '#16161a'; g.font = 'bold 9px sans-serif'; for (let x = 4; x < 128; x += 64) g.fillText('JANK SOUP', x, 19);
  g.fillStyle = '#ffd23a'; for (let x = 52; x < 128; x += 64) { g.beginPath(); g.arc(x, 6, 4, 0, Math.PI * 2); g.fill(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.wrapS = THREE.RepeatWrapping;
  KIT = {
    body: new THREE.CylinderGeometry(R, R, H * 0.66, 18, 1, true), tin: new THREE.CylinderGeometry(R, R, H, 18, 1, true), rims, ends, lid,
    tinM: new THREE.MeshPhongMaterial({ color: 0xc8d2dc, specular: 0xffffff, shininess: 120, flatShading: true, emissive: 0x1a1d22, side: THREE.DoubleSide }),
    labelM: new THREE.MeshLambertMaterial({ map: tex, emissive: 0x2a0606, side: THREE.DoubleSide }),
  };
  for (const k of ['body', 'tin', 'rims', 'ends', 'lid']) KIT[k].userData.shared = true;
  return KIT;
}
// a can in g (models.js buildProjectile): spins as it flies (main.js tumbles every plain projectile)
export function buildTinCan(g) {
  const K = kit();
  g.add(new THREE.Mesh(K.tin, K.tinM), new THREE.Mesh(K.body, K.labelM), new THREE.Mesh(K.rims, K.tinM), new THREE.Mesh(K.ends, K.tinM));
  const lid = new THREE.Mesh(K.lid, K.tinM); lid.position.set(-0.2, 0.215, 0); lid.rotation.z = 0.9; g.add(lid); // (half open: it's been opened with a knife)
  g.scale.setScalar(1.15);
  return g;
}
