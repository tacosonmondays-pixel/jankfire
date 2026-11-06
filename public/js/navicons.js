// Little 3D props for the home menu's buttons, built from chunky boxes like everything else and rendered once into
// pictures (icons.js objIcon caches them): a gold trophy, a cog, a guide book, one of the cats from the board of
// directors, a clipboard of patch notes. CUSTOMIZE shows your own gun and CONTAINERS the 3D crate (home.js sets those).
import * as THREE from 'three';
import { M, buildWeapon } from './models.js';
import { objIcon } from './icons.js';

const box = (g, w, h, d, c, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), M(c)); m.position.set(x, y, z); g.add(m); return m; };
const cyl = (g, rt, rb, h, seg, c, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), M(c)); m.position.set(x, y, z); g.add(m); return m; };
const BUILD = {
  leaders(g) { // a cheap gold trophy on a wooden block
    box(g, 0.7, 0.18, 0.5, 0x6a4420, 0, 0.09, 0);
    box(g, 0.5, 0.06, 0.04, 0xffe14d, 0, 0.1, 0.26); // the plaque
    cyl(g, 0.08, 0.12, 0.22, 8, 0xffc21a, 0, 0.29, 0);
    cyl(g, 0.38, 0.16, 0.5, 8, 0xffc21a, 0, 0.65, 0);
    for (const s of [-1, 1]) { const h = new THREE.Mesh(new THREE.TorusGeometry(0.13, 0.04, 4, 8), M(0xe0a010)); h.position.set(s * 0.4, 0.7, 0); h.rotation.y = Math.PI / 2; g.add(h); }
    box(g, 0.12, 0.12, 0.02, 0xff4fd8, 0, 0.7, 0.33); // a star sticker someone put on it
  },
  settings(g) { // a fat cog with a bolt in the middle
    const c = cyl(g, 0.42, 0.42, 0.16, 12, 0xc8ccd2); c.rotation.x = Math.PI / 2;
    for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2, t = box(g, 0.18, 0.2, 0.16, 0xaab0b8, Math.cos(a) * 0.48, Math.sin(a) * 0.48, 0); t.rotation.z = a; }
    const h = cyl(g, 0.15, 0.15, 0.2, 6, 0x3a3a44, 0, 0, 0.01); h.rotation.x = Math.PI / 2;
    box(g, 0.06, 0.06, 0.04, 0xff4fd8, 0.24, 0.16, 0.1);
    g.rotation.set(-0.35, 0.45, 0.2);
  },
  guide(g) { // a thick pink manual nobody read, a bookmark sticking out
    box(g, 0.9, 0.08, 0.65, 0xff4fd8, 0, 0.04, 0);
    box(g, 0.84, 0.18, 0.6, 0xfff4e0, 0.02, 0.17, 0);
    box(g, 0.9, 0.08, 0.65, 0xff4fd8, 0, 0.3, 0);
    box(g, 0.04, 0.4, 0.66, 0xc0309a, -0.44, 0.17, 0); // the spine
    box(g, 0.1, 0.02, 0.3, 0x4fd8ff, 0.2, 0.35, 0.3);
    box(g, 0.34, 0.02, 0.12, 0xffe14d, 0.08, 0.35, -0.06); // the "?" sticker
    g.rotation.set(0.5, -0.5, 0);
  },
  lore(g) { // one of the cats (they run the company)
    box(g, 0.7, 0.55, 0.55, 0xff9a3c, 0, 0.3, 0);
    for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.26, 4), M(0xff9a3c)); e.position.set(s * 0.22, 0.68, 0); e.rotation.y = Math.PI / 4; g.add(e); }
    for (const s of [-1, 1]) { box(g, 0.12, 0.14, 0.02, 0xffffff, s * 0.15, 0.36, 0.28); box(g, 0.06, 0.08, 0.02, 0x111111, s * 0.15 + 0.02, 0.35, 0.29); }
    box(g, 0.08, 0.06, 0.02, 0xff4fd8, 0, 0.24, 0.29);
    box(g, 0.3, 0.08, 0.04, 0x111111, 0, 0.08, 0.29); // a tiny tie
    g.rotation.set(0.15, -0.35, 0);
  },
  patchnotes(g) { // a clipboard with a list on it
    box(g, 0.7, 0.9, 0.05, 0x8a5a2a, 0, 0, 0);
    box(g, 0.58, 0.74, 0.02, 0xffffff, 0, -0.05, 0.035);
    for (let i = 0; i < 4; i++) box(g, i % 2 ? 0.3 : 0.4, 0.05, 0.01, i === 0 ? 0xff3030 : 0x3a3a44, -0.04, 0.2 - i * 0.15, 0.05);
    box(g, 0.3, 0.12, 0.08, 0xc8ccd2, 0, 0.42, 0.04); // the clip
    g.rotation.set(-0.2, 0.4, 0.12);
  },
};
export function navPic(id) { return BUILD[id] ? objIcon('nav:' + id, () => { const g = new THREE.Group(); BUILD[id](g); return g; }) : ''; }

// CUSTOMIZE's picture: your equipped gun, made to read at 50 px. turned three-quarters and tipped up (side-on it's a
// thin dark stick), centred on its own bounds, with its own key light and a pink rim light riding along in the group
// (the shared icon renderer's lights are tuned for the hotbar, which is bigger). the socket adds a hard outline (css)
export function navGunPic(id, skin) {
  const key = 'navgun:' + id + '|' + (Array.isArray(skin) ? skin.join(',') : '');
  return objIcon(key, () => {
    const outer = new THREE.Group(), g = buildWeapon(id, skin);
    g.rotation.set(0, -Math.PI / 2 + 0.75, 0); // muzzle to the right, turned toward you
    const tilt = new THREE.Group(); tilt.add(g); tilt.rotation.set(0.35, 0, 0.32); // a little from above, nose up
    tilt.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(tilt), c = box.getCenter(new THREE.Vector3());
    tilt.position.sub(c); // framed to the model's bounds
    outer.add(tilt);
    const keyL = new THREE.DirectionalLight(0xffffff, 3.2); keyL.position.set(0.6, 1.2, 2.5);
    const fill = new THREE.AmbientLight(0xffffff, 2.2);
    const rim = new THREE.DirectionalLight(0xff4fd8, 3.5); rim.position.set(-1.5, 1, -2.5);
    outer.add(keyL, keyL.target, fill, rim, rim.target);
    return outer;
  });
}
