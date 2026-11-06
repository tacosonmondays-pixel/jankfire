// The map pass look: cyberpunk x late-90s glossy toy CG x ugly-on-purpose. Extra map materials, added to world.js's set.
// - glossy: shiny rubbery plastic (Phong with a hard white highlight): toys, the bus, chrome
// - loud: clashing, noisy, over-saturated textures (acid lawns, confetti rubber, camo, marbled ceilings)
// - neon / screens: unlit, so they glow in any light (and through the fog a bit)
// - ads: one picture per face (boxes with fit: 1), deadpan corporate copy. all names and slogans are our own
import * as THREE from 'three';

const rnd = (n) => (Math.random() * n) | 0;
const FONT = '"Arial Black", Impact, "Comic Sans MS", sans-serif';

export function addVibe(out, canvasTex, speckle) {
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  const gloss = (t, tile, o) => ({ mat: new THREE.MeshPhongMaterial({ map: t, shininess: 90, specular: 0xffffff, ...o }), tile });
  const flat = (hex) => (g, s, w) => { speckle(g, s, hex, 10, 2, w); };
  const blobs = (g, s, cols, n, rmin, rmax) => { // wrapped so the tile is seamless
    for (let i = 0; i < n; i++) {
      g.fillStyle = cols[i % cols.length];
      const x = rnd(s), y = rnd(s), r = rmin + rnd(rmax - rmin);
      for (const ox of [-s, 0, s]) for (const oy of [-s, 0, s]) { g.beginPath(); g.ellipse(x + ox, y + oy, r, r * (0.5 + Math.random()), Math.random() * 3, 0, Math.PI * 2); g.fill(); }
    }
  };
  const siding = (rgb, line) => (g, s) => { speckle(g, s, rgb, 10, 2); g.fillStyle = line; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); };
  const shingle = (a, b) => (g, s) => { speckle(g, s, a, 14, 2); g.fillStyle = b; for (let y = 3; y < s; y += 4) { g.fillRect(0, y, s, 1); for (let x = (y >> 2) % 2 ? 0 : 4; x < s; x += 8) g.fillRect(x, y - 3, 1, 3); } };

  // ---- glossy toys (Nubby energy): plain saturated plastic with a hot highlight
  for (const [k, hex] of Object.entries({ toyred: 0xff2a3a, toyblue: 0x2a6cff, toygreen: 0x3ee05a, toyorange: 0xff8a1a, toyteal: 0x19d6c8, toypink: 0xff5ad0, toyyellow: 0xffd21a, toypurple: 0x9a4aff })) {
    out[k] = { mat: new THREE.MeshPhongMaterial({ color: hex, shininess: 110, specular: 0xffffff }), tile: 1 };
  }
  for (const [k, hex] of Object.entries({ carred: 0xd81e30, carblue: 0x1e5ad8, carwhite: 0xf0f0f4, carblack: 0x1e1e26, cargreen: 0x1ea04a, caryellow: 0xf0c418 })) out[k] = { mat: new THREE.MeshPhongMaterial({ color: hex, shininess: 100, specular: 0xffffff }), tile: 1 }; // toy-car paint
  out.chrome = { mat: new THREE.MeshPhongMaterial({ color: 0xb8c2d0, shininess: 140, specular: 0xffffff, emissive: 0x161a22 }), tile: 1 };
  out.busyellow = gloss(canvasTex(16, flat([255, 196, 24])), 2);
  out.seat = gloss(canvasTex(16, (g, s) => { speckle(g, s, [30, 150, 140], 12, 2); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, 7, s, 1); }), 1);
  // a googly face, once per side: the eyes don't quite agree on where to look
  const face = (bg, mouth) => (g, s) => {
    const gr = g.createRadialGradient(s * 0.35, s * 0.3, 4, s / 2, s / 2, s * 0.75); gr.addColorStop(0, '#fff'); gr.addColorStop(0.18, bg); gr.addColorStop(1, '#000'); // a baked shine
    g.fillStyle = gr; g.fillRect(0, 0, s, s);
    for (const [x, px, py] of [[0.32, 0.06, 0.05], [0.68, -0.04, 0.07]]) {
      g.fillStyle = '#fff'; g.beginPath(); g.arc(s * x, s * 0.38, s * 0.15, 0, 7); g.fill();
      g.strokeStyle = '#000'; g.lineWidth = 2; g.stroke();
      g.fillStyle = '#000'; g.beginPath(); g.arc(s * (x + px), s * (0.38 + py), s * 0.065, 0, 7); g.fill();
    }
    g.fillStyle = mouth; g.beginPath(); g.ellipse(s / 2, s * 0.7, s * 0.24, s * 0.12, 0, 0, Math.PI); g.fill();
    g.fillStyle = '#fff'; g.fillRect(s * 0.36, s * 0.7, s * 0.28, s * 0.05);
  };
  out.toyface = gloss(canvasTex(64, face('#ffb31a', '#7a0a2a')), 1);
  out.toyface2 = gloss(canvasTex(64, face('#ff4fd8', '#2a0a5a')), 1);

  // ---- loud ground and walls (ugly on purpose)
  out.lawn = lam(canvasTex(32, (g, s) => { speckle(g, s, [82, 176, 58], 42, 2); g.fillStyle = 'rgba(20,80,0,0.18)'; g.fillRect(0, 0, s / 2, s); }), 4); // mown grass for parks and planters: the same green as the grass round it, with stripes
  out.rubber = lam(canvasTex(32, (g, s) => { speckle(g, s, [40, 30, 60], 20, 2); blobs(g, s, ['#ff2ad4', '#7aff1a', '#19e6ff', '#ffe14d'], 26, 1, 3); }), 2); // playground confetti rubber
  out.camo = lam(canvasTex(32, (g, s) => { speckle(g, s, [150, 120, 60], 30, 2); blobs(g, s, ['#4a5a18', '#2a1a0a', '#c88a2a', '#7a2a6a'], 22, 3, 7); }), 3); // noisy camo floor
  out.leopard = lam(canvasTex(32, (g, s) => { speckle(g, s, [230, 160, 40], 30, 2); blobs(g, s, ['#2a1408'], 18, 2, 4); }), 2);
  out.marble = lam(canvasTex(64, (g, s) => { // acid-green marbled ceiling
    speckle(g, s, [90, 220, 60], 40, 2);
    g.strokeStyle = 'rgba(255,40,200,0.5)'; g.lineWidth = 2;
    for (let i = 0; i < 9; i++) { g.beginPath(); let x = rnd(s), y = 0; g.moveTo(x, y); while (y < s) { x += rnd(13) - 6; y += 4; g.lineTo(x, y); } g.stroke(); }
  }), 4);
  out.magenta = lam(canvasTex(16, (g, s) => { speckle(g, s, [220, 30, 170], 40, 2); g.fillStyle = 'rgba(60,0,40,0.3)'; for (let x = 0; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 2);
  out.asphalt = lam(canvasTex(32, (g, s) => { speckle(g, s, [84, 82, 92], 20, 2); blobs(g, s, ['rgba(255,60,200,0.07)', 'rgba(60,255,220,0.07)', 'rgba(0,0,0,0.2)'], 10, 2, 6); }), 4); // oily
  out.wetroad = lam(canvasTex(32, (g, s) => { speckle(g, s, [40, 40, 56], 14, 2); blobs(g, s, ['rgba(255,60,200,0.18)', 'rgba(60,220,255,0.18)'], 8, 3, 8); g.fillStyle = '#ffe14d'; for (let x = 0; x < s; x += 16) g.fillRect(x, 15, 8, 2); }), 10);
  out.wetroadz = lam(canvasTex(32, (g, s) => { speckle(g, s, [40, 40, 56], 14, 2); blobs(g, s, ['rgba(255,60,200,0.18)', 'rgba(60,220,255,0.18)'], 8, 3, 8); g.fillStyle = '#ffe14d'; for (let y = 0; y < s; y += 16) g.fillRect(15, y, 2, 8); }), 10);
  // city pavement (the kerbed blocks and the sidewalks): dark wet violet slate with the street's neon in the puddles, a step
  // up from the asphalt so the kerbs still read, never the pale grey slab it used to be against the dark streets
  out.pavecity = lam(canvasTex(16, (g, s) => { speckle(g, s, [60, 56, 76], 10, 2); blobs(g, s, ['rgba(255,60,200,0.08)', 'rgba(60,220,255,0.08)'], 4, 1, 3); g.fillStyle = '#2c2938'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 3);
  // bomb site floors: each site its own colour underfoot too (A red, B cyan)
  out.dockred = lam(canvasTex(32, (g, s) => { speckle(g, s, [116, 42, 50], 16, 2); blobs(g, s, ['rgba(0,0,0,0.22)', 'rgba(255,90,90,0.12)'], 7, 2, 6); g.fillStyle = 'rgba(255,220,80,0.55)'; g.fillRect(0, 0, s, 1); }), 6);
  out.floorcyan = lam(canvasTex(32, (g, s) => { speckle(g, s, [36, 92, 104], 12, 2); blobs(g, s, ['rgba(120,255,255,0.08)'], 5, 2, 5); g.fillStyle = 'rgba(10,30,40,0.7)'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 4);
  out.asphaltn = lam(canvasTex(32, (g, s) => { speckle(g, s, [36, 36, 48], 14, 2); blobs(g, s, ['rgba(255,60,200,0.06)', 'rgba(60,220,255,0.06)'], 9, 2, 6); }), 14); // the far city's streets, wet
  out.seawater = { mat: new THREE.MeshPhongMaterial({ color: 0x0c2238, emissive: 0x040a16, specular: 0x88aacc, shininess: 70 }), tile: 1 };
  { // brick tenements with windows: some lit (they glow), some not
    const lit = [], c32 = 32;
    for (let y = 3; y < c32; y += 8) for (let x = 2; x < c32; x += 6) lit.push([x, y, Math.random() < 0.45, Math.random() < 0.12]);
    const base = canvasTex(c32, (g, s) => { speckle(g, s, [130, 60, 50], 22, 2); g.fillStyle = 'rgba(60,20,16,0.5)'; for (let y = 0; y < s; y += 4) g.fillRect(0, y, s, 1); for (const [x, y, on, neon] of lit) { g.fillStyle = on ? (neon ? '#ff4fd8' : '#ffe9a0') : '#1a1c2a'; g.fillRect(x, y, 3, 4); } });
    const glow = canvasTex(c32, (g, s) => { g.fillStyle = '#000'; g.fillRect(0, 0, s, s); for (const [x, y, on, neon] of lit) if (on) { g.fillStyle = neon ? '#ff4fd8' : '#ffe9a0'; g.fillRect(x, y, 3, 4); } });
    out.tenement = lam(base, 6, { emissive: 0xffffff, emissiveMap: glow });
  }
  out.crosswalk = lam(canvasTex(16, (g, s) => { g.fillStyle = '#2a2a38'; g.fillRect(0, 0, s, s); g.fillStyle = '#e8e8f0'; g.fillRect(0, 0, s / 2, s); }), 2);
  out.sidepink = lam(canvasTex(16, siding([255, 120, 190], '#b0407a')), 1.2);
  out.sidelemon = lam(canvasTex(16, siding([250, 236, 80], '#a89a20')), 1.2);
  out.sidelilac = lam(canvasTex(16, siding([180, 140, 255], '#6a4aaa')), 1.2);
  out.sidemint = lam(canvasTex(16, siding([110, 240, 190], '#3a9a70')), 1.2);
  out.sideorange = lam(canvasTex(16, siding([255, 150, 50], '#a85a10')), 1.2);
  out.roofteal = gloss(canvasTex(16, shingle([20, 170, 170], '#0a5a5a')), 1.5);
  out.roofpink = gloss(canvasTex(16, shingle([240, 60, 150], '#7a1050')), 1.5);
  out.roofblue = lam(canvasTex(16, (g, s) => { speckle(g, s, [40, 100, 200], 14, 2); g.fillStyle = '#1a3a7a'; for (let x = 0; x < s; x += 4) g.fillRect(x, 0, 1, s); g.fillStyle = '#7ab0ff'; for (let x = 2; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 2); // corrugated
  out.asphalt2 = lam(canvasTex(16, (g, s) => { speckle(g, s, [70, 74, 86], 12, 2); }), 3);
  out.dirtroad = lam(canvasTex(16, (g, s) => { speckle(g, s, [178, 134, 86], 26, 2); g.fillStyle = 'rgba(90,60,30,0.35)'; for (let i = 0; i < 6; i++) g.fillRect(rnd(s), rnd(s), 1, 1); }), 3);
  out.pottery = lam(canvasTex(16, (g, s) => { speckle(g, s, [196, 98, 52], 18, 2); g.fillStyle = '#7a2a10'; g.fillRect(0, 5, s, 1); g.fillStyle = '#f2d9a0'; g.fillRect(0, 9, s, 1); }), 1);
  out.rock = lam(canvasTex(32, (g, s) => { speckle(g, s, [170, 92, 58], 22, 2); for (let y = 0; y < s; y += 6) { g.fillStyle = y % 12 ? 'rgba(120,50,30,0.35)' : 'rgba(230,170,110,0.3)'; g.fillRect(0, y, s, 2); } }), 6); // banded red rock
  out.camel = lam(canvasTex(16, (g, s) => { speckle(g, s, [196, 160, 110], 16, 2); }), 2);
  out.wallkid = lam(canvasTex(32, (g, s) => { for (let x = 0; x < s; x += 8) { g.fillStyle = (x / 8) % 2 ? '#bfe8ff' : '#ffd0ec'; g.fillRect(x, 0, 8, s); } g.fillStyle = '#ffe14d'; for (const [x, y] of [[4, 6], [20, 14], [12, 26], [28, 4]]) { g.fillRect(x - 1, y - 3, 2, 6); g.fillRect(x - 3, y - 1, 6, 2); } }), 24); // nursery wallpaper, stars
  out.skypane = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(64, (g, s, w) => { const gr = g.createLinearGradient(0, 0, 0, s); gr.addColorStop(0, '#5aa8ff'); gr.addColorStop(1, '#dff0ff'); g.fillStyle = gr; g.fillRect(0, 0, w, s); g.fillStyle = '#fff'; for (const [x, y, r] of [[30, 30, 9], [42, 26, 11], [56, 32, 8], [110, 22, 10], [124, 28, 8], [96, 30, 7]]) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); } g.fillStyle = '#8a5a2a'; g.fillRect(w / 2 - 1, 0, 2, s); g.fillRect(0, s / 2 - 1, w, 2); }, 160) }), tile: 1 };
  out.picket = lam(canvasTex(16, (g, s) => { g.fillStyle = '#f4f2ec'; g.fillRect(0, 0, s, s); g.fillStyle = '#b8b4c8'; for (let x = 3; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 1);
  out.plywood = lam(canvasTex(16, (g, s) => { speckle(g, s, [200, 160, 100], 40, 1); }), 1.5);
  out.jersey = lam(canvasTex(16, (g, s) => { speckle(g, s, [190, 190, 196], 14, 2); for (let x = 0; x < s; x += 8) { g.fillStyle = '#e8202a'; g.fillRect(x, 2, 4, 3); g.fillStyle = '#fff'; g.fillRect(x + 4, 2, 4, 3); } }), 2);
  out.truckbox = lam(canvasTex(16, (g, s) => { speckle(g, s, [236, 236, 240], 8, 2); g.fillStyle = 'rgba(80,70,50,0.25)'; g.fillRect(0, s - 3, s, 3); }), 2);
  out.burnt = lam(canvasTex(16, (g, s) => { speckle(g, s, [40, 30, 26], 26, 2); blobs(g, s, ['#5a2a10', '#1a1010'], 5, 1, 3); }), 1);
  out.leaves2 = lam(canvasTex(16, (g, s) => { speckle(g, s, [150, 240, 30], 60, 2); }), 2);
  out.blossom = lam(canvasTex(16, (g, s) => { speckle(g, s, [255, 90, 200], 60, 2); }), 2);
  out.rust = lam(canvasTex(16, (g, s) => { speckle(g, s, [150, 70, 40], 40, 2); blobs(g, s, ['#5a2a14', '#c86a2a'], 6, 1, 3); }), 2);
  out.cardboard = lam(canvasTex(16, (g, s) => { speckle(g, s, [196, 150, 96], 14, 1); g.fillStyle = '#d8c090'; g.fillRect(0, 7, s, 2); g.fillStyle = '#7a5a30'; g.fillRect(0, 0, s, 1); g.fillRect(0, 0, 1, s); }), 1);
  out.pallet = lam(canvasTex(16, (g, s) => { speckle(g, s, [180, 140, 90], 20, 1); g.fillStyle = '#4a3418'; for (let x = 4; x < s; x += 5) g.fillRect(x, 0, 1, s); }), 1.2);
  out.shelf = lam(canvasTex(16, (g, s) => { speckle(g, s, [40, 90, 220], 14, 2); g.fillStyle = '#ff8a1a'; g.fillRect(0, 0, s, 3); }), 2); // blue racking with orange beams
  out.fence = { mat: new THREE.MeshLambertMaterial({ map: canvasTex(16, (g, s) => { g.clearRect(0, 0, s, s); g.fillStyle = '#9aa0aa'; for (let i = -s; i < s; i += 4) { for (let k = 0; k < s; k++) { g.fillRect((i + k) & (s - 1), k, 1, 1); g.fillRect((i - k + 2 * s) & (s - 1), k, 1, 1); } } }), transparent: true, alphaTest: 0.5, side: THREE.DoubleSide }), tile: 1 }; // chain link you can see through
  out.shelfstock = lam(canvasTex(16, (g, s) => { const c = ['#ff2ad4', '#19e6ff', '#ffe14d', '#7aff1a', '#ff5a1a', '#fff']; for (let y = 0; y < s; y += 4) for (let x = 0; x < s; x += 3) { g.fillStyle = c[rnd(c.length)]; g.fillRect(x, y, 2, 3); } }), 1);
  out.barrel = gloss(canvasTex(16, (g, s) => { speckle(g, s, [30, 90, 200], 16, 2); g.fillStyle = '#ffe14d'; g.fillRect(0, 3, s, 2); g.fillRect(0, 11, s, 2); }), 1.2);
  out.barrelr = gloss(canvasTex(16, (g, s) => { speckle(g, s, [210, 30, 40], 16, 2); g.fillStyle = '#111'; g.fillRect(0, 3, s, 2); g.fillRect(0, 11, s, 2); }), 1.2);
  out.graffiti = lam(canvasTex(64, (g, s) => { // a roller door somebody had opinions about
    speckle(g, s, [140, 146, 156], 10, 2); g.fillStyle = 'rgba(0,0,0,0.25)'; for (let y = 2; y < s; y += 4) g.fillRect(0, y, s, 1);
    g.font = `bold 15px ${FONT}`; g.textAlign = 'center';
    g.lineWidth = 4; g.strokeStyle = '#120818'; g.fillStyle = ['#ff2ad4', '#7aff1a', '#19e6ff'][rnd(3)];
    const w = ['JANK', 'NO', 'LOL', 'WHY', 'RENT'][rnd(5)];
    g.save(); g.translate(s / 2, s / 2); g.rotate(-0.2); g.strokeText(w, 0, 0); g.fillText(w, 0, 0); g.restore();
  }), 6);
  // ---- screens and neon
  out.tvstatic = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(32, (g, s) => { speckle(g, s, [150, 150, 160], 200, 1); }) }), tile: 1 };
  for (const [k, hex] of Object.entries({ neonpink: 0xff2ad4, neoncyan: 0x19f0ff, neonyellow: 0xfff04d, neongreen: 0x5aff2a, neonred: 0xff2a3a })) out[k] = { mat: new THREE.MeshBasicMaterial({ color: hex }), tile: 1 };
  out.lamp = { mat: new THREE.MeshBasicMaterial({ color: 0xfff6c8 }), tile: 1 };
  out.window = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(32, (g, s) => { // night windows: some lit, some on a screen
    g.fillStyle = '#141828'; g.fillRect(0, 0, s, s);
    for (let y = 2; y < s; y += 8) for (let x = 2; x < s; x += 8) { const k = Math.random(); g.fillStyle = k < 0.3 ? '#ffe9a0' : k < 0.38 ? '#ff4fd8' : k < 0.44 ? '#19e6ff' : '#232a40'; g.fillRect(x, y, 5, 5); }
  }) }), tile: 6 };

  // ---- ads and signs (fit: drawn once across the face)
  const ad = (bg, fg, lines, w = 256, h = 96, o = {}) => {
    const t = canvasTex(h, (g) => {
      g.fillStyle = bg; g.fillRect(0, 0, w, h);
      if (o.stripes) { g.fillStyle = o.stripes; for (let x = -h; x < w; x += 24) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 12, 0); g.lineTo(x + 12 + h, h); g.lineTo(x + h, h); g.fill(); } }
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
  const neon = (txt, col) => ad('#0a0614', col, [txt], 256, 64, {});
  // bomb site boards: a huge letter you can read from across the map, each site its own colour
  out.sitea = ad('#14060c', '#ff3a4a', ['A', 'BOMB SITE A'], 192, 192, { small: '#ffe14d' });
  out.siteb = ad('#06101a', '#19e6ff', ['B', 'BOMB SITE B'], 192, 192, { small: '#ffe14d' });
  out.signopen = neon('OPEN HOUSE', '#ff4fd8');
  out.adbig1 = ad('#ff4fd8', '#ffe14d', ['SUBURBIA™', 'OWN A HOME*', '*rented by the hour'], 256, 96, { small: '#fff' });
  out.adstore = ad('#19e6ff', '#ff2a3a', ['MEGA-MART EXPRESS', 'OPEN 25 HOURS'], 320, 64, { small: '#120818' });
  out.adclosed = ad('#ffe14d', '#ff2a3a', ['ROAD CLOSED', 'nothing past this point. really.'], 256, 96, { stripes: 'rgba(0,0,0,0.12)', small: '#120818' });
  out.adfun = ad('#7aff1a', '#ff2ad4', ['FUN ZONE', 'fun is mandatory'], 256, 96, { small: '#120818' });
  out.adhoa = ad('#f4f2ec', '#2a6cff', ['H.O.A. OFFICE', 'we are watching your lawn'], 320, 64, { small: '#ff2a3a', lit: false });
  out.adbus = ad('#ffc418', '#120818', ['JANK TRANSIT', 'we get you there (eventually)'], 320, 64, { lit: false });
  out.adtruck = ad('#f4f4f8', '#ff2a3a', ['MEAT-ISH™', 'now 40% meat'], 256, 96, { small: '#2a6cff', lit: false });
  out.adtruck2 = ad('#f4f4f8', '#19a04a', ['CRATE & BARREL & CRATE', 'logistics, probably'], 256, 96, { small: '#120818', lit: false });
  out.plaque = ad('#c8a040', '#120818', ['OUR FOUNDER'], 128, 64, { lit: false });
  out.flagcorp = ad('#2a6cff', '#fff', ['☺ CORP'], 160, 96);
  out.adcity1 = ad('#120818', '#19e6ff', ['NEUROSPOON', 'think less. spoon more.'], 256, 96, { small: '#ff4fd8' });
  out.adcity2 = ad('#ff2a3a', '#ffe14d', ['JANK COLA', 'now with 0% water'], 256, 96, { small: '#fff' });
  out.adcity3 = ad('#7aff1a', '#120818', ['GRAPPLE INC.', 'hang in there™'], 256, 96, { small: '#120818' });
  out.adcity4 = ad('#ffe14d', '#ff2ad4', ['ORGAN LEASING', 'your liver, our future'], 256, 96, { small: '#120818' });
  out.adcity5 = ad('#2a0a5a', '#ff4fd8', ['SPOON BANK', 'we hold your spoons'], 256, 96, { small: '#19e6ff' });
  out.adcity6 = ad('#19e6ff', '#120818', ['SLEEP.EXE', 'dreams now ad-supported'], 256, 96, { small: '#ff2a3a' });
  out.neonbar = neon('BAR?', '#19f0ff');
  out.neonnoodle = neon('NOODLE', '#ff4fd8');
  out.neonhotel = neon('HOTEL 4 HOURS', '#fff04d');
  out.neonwork = neon('WORK HARDER', '#ff2a3a');
  out.adwater = ad('#19d6c8', '#fff', ['SUBURBIA', 'water: now with extra water'], 256, 96, { small: '#120818', lit: false });
  out.adoffice = ad('#ffe14d', '#120818', ['SITE OFFICE', 'knock. then knock louder.'], 256, 64, { lit: false });
  out.adware = ad('#2a6cff', '#ffe14d', ['DOCK 3', 'no loitering. no not-loitering.'], 256, 96, { small: '#fff', lit: false });
  out.adshred = ad('#ffe14d', '#ff2a3a', ['DANGER', 'industrial shredder. do not feed.'], 256, 96, { stripes: 'rgba(0,0,0,0.14)', small: '#120818', lit: false });
  // Desert (Dry Gulch): the town's signs
  out.adsaloon = ad('#7a2a10', '#ffe14d', ['THE THIRSTY CACTUS', 'saloon. no refunds. no cactus.'], 320, 64, { small: '#fff', lit: false });
  out.adbank = ad('#f2e2b8', '#1a5a2a', ['BANK OF DRY GULCH', 'your gold, our problem'], 320, 64, { small: '#7a2a10', lit: false });
  out.adsheriff = ad('#2a1a10', '#ffe14d', ['SHERIFF', 'out to lunch since 1887'], 256, 64, { small: '#ff7a1a', lit: false });
  out.adhotel = ad('#ff4fd8', '#ffe14d', ['HOTEL', 'beds: allegedly'], 256, 64, { small: '#fff' });
  out.adgeneral = ad('#ffe14d', '#7a2a10', ['GENERAL STORE', 'we have rope. that is it.'], 320, 64, { small: '#120818', lit: false });
  out.adundertaker = ad('#120818', '#d8d8d8', ['UNDERTAKER', 'pre-dig your plot today'], 256, 64, { small: '#ff4fd8', lit: false });
  out.adlivery = ad('#7a4a20', '#ffe14d', ['LIVERY', 'horses sold separately'], 256, 64, { small: '#fff', lit: false });
  out.admine = ad('#ffe14d', '#120818', ['JANK MINING CO.', 'dig deep. ask nothing.'], 256, 96, { stripes: 'rgba(0,0,0,0.12)', small: '#ff2a3a', lit: false });
  out.addepot = ad('#2a6cff', '#fff', ['DRY GULCH', 'elevation: yes. trains: once'], 256, 64, { small: '#ffe14d', lit: false });
  out.adwanted = ad('#f2e2b8', '#120818', ['WANTED', 'you. probably.', 'reward: a hat'], 128, 160, { small: '#7a2a10', lit: false });
  out.adassay = ad('#d8d0b0', '#7a2a10', ['ASSAY OFFICE', 'is it gold? (no)'], 256, 64, { small: '#120818', lit: false });
  // Desert S&D (the payroll job)
  out.adstage = ad('#1a5a2a', '#ffe14d', ['STAGE CO.', 'arrives eventually. leaves faster.'], 256, 64, { small: '#fff', lit: false });
  out.adpayroll = ad('#ffe14d', '#7a2a10', ['PAYROLL', 'do not rob. please.'], 192, 96, { stripes: 'rgba(0,0,0,0.12)', small: '#120818', lit: false });
  out.adpowder = ad('#ff2a3a', '#ffe14d', ['POWDER', 'no smoking. no fire. no fun.'], 192, 64, { small: '#fff', lit: false });
}
