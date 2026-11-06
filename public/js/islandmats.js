// Islands materials: the volcano's rock and its lava, thatch and bamboo for the beach huts, the wreck's planks and its
// sail, the tropical sea and its surf, the skull's pale rock, signs in the game's voice. Added to world.js's set like
// vibe.js and forestmats.js.
import * as THREE from 'three';

const rnd = (n) => (Math.random() * n) | 0;
const FONT = '"Arial Black", Impact, "Comic Sans MS", sans-serif';

export function addIslands(out, canvasTex, speckle) {
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  const lines = (rgb, line, step = 4, vert = false, vary = 14) => (g, s) => { speckle(g, s, rgb, vary, 2); g.fillStyle = line; for (let i = step - 1; i < s; i += step) vert ? g.fillRect(i, 0, 1, s) : g.fillRect(0, i, s, 1); };
  // ---- the volcano: dark rock with a few cracks still warm, and the lava down its throat
  out.basalt = lam(canvasTex(16, (g, s) => {
    speckle(g, s, [64, 56, 70], 20, 2); g.fillStyle = '#2a2230'; for (let i = 0; i < 7; i++) g.fillRect(rnd(s), rnd(s), 2 + rnd(3), 1);
    g.fillStyle = 'rgba(255,110,40,0.6)'; g.fillRect(rnd(s), rnd(s), 3, 1); g.fillRect(rnd(s), rnd(s), 1, 2);
  }), 2);
  out.lava = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(32, (g, s) => {
    g.fillStyle = '#ff4a10'; g.fillRect(0, 0, s, s);
    for (let i = 0; i < 26; i++) { g.fillStyle = i % 3 ? '#ffb020' : '#ffe14d'; g.fillRect(rnd(s), rnd(s), 2 + rnd(5), 1 + rnd(3)); }
    g.fillStyle = '#7a1408'; for (let i = 0; i < 10; i++) g.fillRect(rnd(s), rnd(s), 4 + rnd(6), 1);
  }) }), tile: 3 };
  // ---- the beach: the sea (see-through over the shallows' sand), its surf, wet sand, the huts' thatch and bamboo
  out.sea = { mat: new THREE.MeshBasicMaterial({ color: 0x2ab8d4, transparent: true, opacity: 0.6, depthWrite: false }), tile: 4 };
  out.surf = { mat: new THREE.MeshBasicMaterial({ color: 0xf4fbff, transparent: true, opacity: 0.85 }), tile: 1 };
  out.wetsand = lam(canvasTex(16, (g, s) => speckle(g, s, [178, 150, 104], 18, 1)), 2);
  out.thatch = lam(canvasTex(16, lines([204, 164, 84], '#8a6a30', 3)), 1.2);
  out.bamboo = lam(canvasTex(16, (g, s) => { lines([182, 170, 96], '#7a7034', 4, true, 10)(g, s); g.fillStyle = '#5e5422'; for (let y = 5; y < s; y += 8) g.fillRect(0, y, s, 1); }), 1);
  // ---- the wreck: weathered deck planks, the tarred hull (weed along the waterline), the torn sail
  out.shipwood = lam(canvasTex(16, lines([116, 82, 54], '#3a2414', 4, false, 16)), 1.2);
  out.shiphull = lam(canvasTex(16, (g, s) => { lines([64, 46, 36], '#1e140e', 4, false, 12)(g, s); g.fillStyle = 'rgba(60,140,90,0.5)'; for (let i = 0; i < 6; i++) g.fillRect(rnd(s), s - 4 + rnd(4), 3, 2); }), 1.2);
  out.sail = lam(canvasTex(16, (g, s) => { speckle(g, s, [230, 218, 190], 10, 2); g.fillStyle = 'rgba(120,90,60,0.35)'; g.fillRect(3, 4, 5, 4); g.fillRect(10, 11, 4, 3); }), 2, { side: THREE.DoubleSide });
  // ---- Skull Rock: pale, a bit bony
  out.skullrock = lam(canvasTex(16, (g, s) => { speckle(g, s, [216, 208, 188], 16, 2); g.fillStyle = '#9a927e'; for (let i = 0; i < 5; i++) g.fillRect(rnd(s), rnd(s), 3, 1); }), 2);
  out.skulldark = { mat: new THREE.MeshBasicMaterial({ color: 0x120a10 }), tile: 1 };
  // ---- signs (the same sign painter as vibe.js)
  const ad = (bg, fg, lines, w = 256, h = 96, o = {}) => {
    const t = canvasTex(h, (g) => {
      g.fillStyle = bg; g.fillRect(0, 0, w, h);
      g.strokeStyle = fg; g.lineWidth = 4; g.strokeRect(5, 5, w - 10, h - 10);
      g.textAlign = 'center'; g.textBaseline = 'middle';
      const n = lines.length;
      lines.forEach((ln, i) => {
        const big = i === 0, px = big ? (n > 1 ? h * 0.36 : h * 0.5) : h * 0.16;
        g.font = `${big ? 'bold ' : ''}${px | 0}px ${FONT}`;
        const y = n === 1 ? h / 2 : big ? h * 0.38 : h * (0.66 + (i - 1) * 0.17);
        let fs = px; while (g.measureText(ln).width > w - 24 && fs > 8) { fs -= 2; g.font = `${big ? 'bold ' : ''}${fs}px ${FONT}`; }
        if (big) { g.lineWidth = Math.max(3, fs / 7); g.strokeStyle = '#120818'; g.strokeText(ln, w / 2 + 3, y + 3); g.strokeText(ln, w / 2, y); }
        g.fillStyle = big ? fg : (o.small || fg); g.fillText(ln, w / 2, y);
      });
    }, w);
    t.magFilter = THREE.LinearFilter;
    return { mat: o.lit === false ? new THREE.MeshLambertMaterial({ map: t }) : new THREE.MeshBasicMaterial({ map: t }), tile: 1 };
  };
  out.flagskull = ad('#120818', '#fff', ['☠ JANK'], 160, 96, { lit: false });
  out.adtiki = ad('#3a1a08', '#ffe14d', ['TIKI BAR', 'drinks with tiny umbrellas. umbrellas extra'], 320, 64, { small: '#fff', lit: false });
  out.adbait = ad('#1a4a6a', '#fff', ['BAIT & TACKLE', 'worms: fresh. ish.'], 256, 64, { small: '#ffe14d', lit: false });
  out.adtreasure = ad('#5a3a10', '#ffe14d', ['TREASURE', 'already dug up. sorry.'], 256, 64, { small: '#fff', lit: false });
  out.advolcano = ad('#2a2230', '#ff7a1a', ['MOUNT KABOOM', 'please do not feed the volcano'], 320, 64, { small: '#ffe14d', lit: false });
  out.adfort = ad('#4a4038', '#fff', ['FORT SPLINTER', 'mind the splinters'], 256, 64, { small: '#ffe14d', lit: false });
  out.adlight = ad('#c81a2a', '#fff', ['LIGHTHOUSE', 'lights on. nobody home.'], 256, 64, { small: '#ffe14d', lit: false });
  out.adsurf = ad('#ff4fd8', '#fff', ['SURF SCHOOL', 'lesson 1: do not'], 256, 64, { small: '#120818', lit: false });
  out.adship = ad('#2a1a10', '#ffe14d', ['THE SOGGY BISCUIT'], 320, 64, { lit: false });
  out.adcannon = ad('#120818', '#ff3030', ['HUMAN CANNONBALL', 'stand here. trust us.'], 320, 64, { small: '#fff' });
}
