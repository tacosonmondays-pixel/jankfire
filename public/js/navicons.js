// Little 3D props for the home menu's buttons, built from chunky boxes like everything else and rendered once into
// pictures in the shared icon studio (icons.js studioIcon: its light rig, ink outline and hard accent shadow, the same
// look as the customize hub's tabs): a gold trophy, a cog, a guide book, one of the cats from the board of directors,
// a clipboard of patch notes. CUSTOMIZE shows your own gun and CONTAINERS the 3D crate (home.js sets those).
import * as THREE from 'three';
import { M, buildWeapon } from './models.js';
import { studioIcon } from './icons.js';
import { buildContainer } from './crate3d.js';

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
// the props are posed facing the camera already (each BUILD sets its own turn), so the studio adds only a slight tip
export function navPic(id) { return BUILD[id] ? studioIcon('nav:' + id, () => { const g = new THREE.Group(); BUILD[id](g); return g; }, { w: 48, h: 48, accent: '#4fd8ff', yaw: 0, pitch: 0.1, roll: 0 }) : ''; }

// CUSTOMIZE's picture: your equipped gun, made to read at 50 px: three-quarters from the front and tipped up (side-on
// it's a thin dark stick), framed to the gun, in the studio's light with a pink rim + shadow (like the hub's WEAPONS tab)
export function navGunPic(id, skin) {
  const key = 'navgun:' + id + '|' + (Array.isArray(skin) ? skin.join(',') : '');
  return studioIcon(key, () => buildWeapon(id, skin), { w: 64, h: 64, accent: '#ff4fd8', yaw: -1.0, pitch: 0.35, roll: 0.32, pad: 1.06 });
}
// CONTAINERS' picture: the 3D crate, in the same studio look as the rest of the column
export function navCratePic() { return studioIcon('nav:crate', () => buildContainer('crate'), { w: 48, h: 48, accent: '#ff4fd8', yaw: -0.6, pitch: 0.35, roll: 0 }); }
