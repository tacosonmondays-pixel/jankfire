// Platform materials: the rig's deck plate and see-through grating, the lattice of the derrick, the cranes and the flare
// boom, safety-yellow and rig-red paint, the living quarters' white cladding, the lifeboats' orange, the flare's flame,
// the grey North Sea, signs in the game's voice. Added to world.js's set like vibe.js and islandmats.js.
import * as THREE from 'three';

const rnd = (n) => (Math.random() * n) | 0;
const FONT = '"Arial Black", Impact, "Comic Sans MS", sans-serif';

export function addRig(out, canvasTex, speckle) {
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  const crisp = (t) => { t.generateMipmaps = false; t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter; return t; }; // (see-through: no mipmaps, or far lattice fades to nothing)
  const cut = (t, tile) => ({ mat: new THREE.MeshLambertMaterial({ map: crisp(t), transparent: true, alphaTest: 0.5, side: THREE.DoubleSide }), tile });
  // ---- the decks: diamond-tread plate, and open grating you can see the sea through
  out.deckplate = lam(canvasTex(16, (g, s) => {
    speckle(g, s, [98, 106, 116], 10, 2);
    g.fillStyle = '#868e99'; for (let y = 1; y < s; y += 4) for (let x = (y >> 2) % 2 ? 0 : 2; x < s; x += 4) g.fillRect(x, y, 2, 1);
    g.fillStyle = 'rgba(120,70,40,0.35)'; for (let i = 0; i < 3; i++) g.fillRect(rnd(s), rnd(s), 2 + rnd(3), 1); // rust
  }), 1.6);
  out.grating = cut(canvasTex(16, (g, s) => {
    g.clearRect(0, 0, s, s); g.fillStyle = '#7d848e';
    for (let x = 0; x < s; x += 2) g.fillRect(x, 0, 1, s); // the bearing bars
    for (let y = 0; y < s; y += 4) g.fillRect(0, y, s, 1); // the cross bars (holes 1 x 3 px: more steel than hole, so it reads from far off)
  }), 1);
  // ---- the lattice: the derrick, the crane booms, the flare boom, the jacket's bracing (X braces in a frame)
  out.truss = cut(canvasTex(32, (g, s) => {
    g.clearRect(0, 0, s, s); g.fillStyle = '#d8b21a';
    g.fillRect(0, 0, s, 3); g.fillRect(0, s - 3, s, 3); g.fillRect(0, 0, 3, s); g.fillRect(s - 3, 0, 3, s);
    for (let i = 0; i < s; i++) { g.fillRect(i - 1, i - 1, 3, 3); g.fillRect(s - i - 2, i - 1, 3, 3); }
    g.fillStyle = '#8a6a0a'; g.fillRect(0, s - 1, s, 1); g.fillRect(s - 1, 0, 1, s);
  }), 3);
  out.trussred = cut(canvasTex(32, (g, s) => {
    g.clearRect(0, 0, s, s); g.fillStyle = '#c8402e';
    g.fillRect(0, 0, s, 3); g.fillRect(0, s - 3, s, 3); g.fillRect(0, 0, 3, s); g.fillRect(s - 3, 0, 3, s);
    for (let i = 0; i < s; i++) { g.fillRect(i - 1, i - 1, 3, 3); g.fillRect(s - i - 2, i - 1, 3, 3); }
    g.fillStyle = '#f2efe8'; g.fillRect(0, (s >> 1) - 1, 3, 3); g.fillRect(s - 3, (s >> 1) - 1, 3, 3);
  }), 3);
  out.net = cut(canvasTex(16, (g, s) => { g.clearRect(0, 0, s, s); g.fillStyle = '#d8d0b0'; for (let i = 0; i < s; i += 3) { g.fillRect(i, 0, 1, s); g.fillRect(0, i, s, 1); } }), 0.8);
  // ---- paint: safety yellow, rig red, grey steel, the process modules' blue, the living quarters' white panels
  out.rigyellow = lam(canvasTex(16, (g, s) => { speckle(g, s, [236, 196, 36], 12, 2); g.fillStyle = 'rgba(90,60,20,0.35)'; g.fillRect(rnd(s), rnd(s), 2, 1); }), 1.5);
  out.rigred = lam(canvasTex(16, (g, s) => { speckle(g, s, [196, 54, 40], 12, 2); g.fillStyle = 'rgba(60,20,10,0.4)'; g.fillRect(rnd(s), rnd(s), 3, 1); }), 1.5);
  out.rigsteel = lam(canvasTex(16, (g, s) => { speckle(g, s, [118, 124, 134], 10, 2); g.fillStyle = '#5e646e'; for (let x = 2; x < s; x += 6) for (let y = 2; y < s; y += 6) g.fillRect(x, y, 1, 1); }), 1.5);
  out.rigblue = lam(canvasTex(16, (g, s) => { speckle(g, s, [70, 112, 156], 10, 2); g.fillStyle = '#3e6890'; for (let x = 3; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 1.6);
  out.rigwhite = lam(canvasTex(16, (g, s) => { speckle(g, s, [232, 234, 236], 6, 4); g.fillStyle = '#b8bcc4'; for (let x = 7; x < s; x += 8) g.fillRect(x, 0, 1, s); g.fillRect(0, s - 1, s, 1); }), 2);
  out.lifeboat = lam(canvasTex(16, (g, s) => { speckle(g, s, [255, 112, 28], 10, 2); g.fillStyle = '#f4f0e8'; g.fillRect(0, 10, s, 2); }), 2.4);
  out.pipe = lam(canvasTex(16, (g, s) => { speckle(g, s, [150, 152, 144], 10, 2); g.fillStyle = '#6e706a'; for (let x = 5; x < s; x += 8) g.fillRect(x, 0, 2, s); }), 2);
  out.bop = lam(canvasTex(16, (g, s) => { speckle(g, s, [206, 44, 34], 12, 2); g.fillStyle = '#5a1410'; for (let y = 3; y < s; y += 6) for (let x = 1; x < s; x += 3) g.fillRect(x, y, 1, 1); }), 1.2);
  // ---- the flame (lit by itself: it's on fire), the sea (grey-green, deep)
  out.flame = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(32, (g, s) => {
    g.fillStyle = '#ff5a14'; g.fillRect(0, 0, s, s);
    for (let i = 0; i < 30; i++) { g.fillStyle = i % 3 ? '#ffb020' : '#ffe14d'; g.fillRect(rnd(s), rnd(s), 2 + rnd(4), 3 + rnd(6)); }
    g.fillStyle = '#c8200a'; for (let i = 0; i < 8; i++) g.fillRect(rnd(s), rnd(s), 1 + rnd(3), 4);
  }) }), tile: 2 };
  out.seanorth = { mat: new THREE.MeshBasicMaterial({ color: 0x24607a, transparent: true, opacity: 0.86, depthWrite: false }), tile: 4 };
  out.foam = { mat: new THREE.MeshBasicMaterial({ color: 0xe8f2f4, transparent: true, opacity: 0.8 }), tile: 1 };
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
  out.adglug = ad('#120818', '#ffe14d', ['GLUG OIL', 'we put the oil in toil'], 320, 80, { small: '#fff' });
  out.addays = ad('#f4f0e8', '#c81a2a', ['DAYS WITHOUT AN ACCIDENT: 0', 'previous record: 0'], 320, 64, { small: '#120818', lit: false });
  out.admuster = ad('#1a8a3a', '#fff', ['MUSTER POINT', 'stand here and panic'], 256, 64, { small: '#ffe14d', lit: false });
  out.adgalley = ad('#3a2a1a', '#ffe14d', ['THE GALLEY', 'today: soup (wet)'], 256, 64, { small: '#fff', lit: false });
  out.adcontrol = ad('#120818', '#ff3030', ['CONTROL ROOM', 'do not press the big red button'], 320, 64, { small: '#fff', lit: false });
  out.adflare = ad('#c81a2a', '#fff', ['FLARE TIP', 'do not toast marshmallows'], 256, 64, { small: '#ffe14d', lit: false });
  out.admud = ad('#5a3a1a', '#fff', ['MUD', 'it is mostly mud'], 192, 64, { small: '#ffe14d', lit: false });
  out.adxmas = ad('#1a6a2a', '#fff', ['CHRISTMAS TREES', 'not that kind. well. now that kind.'], 320, 64, { small: '#ffe14d', lit: false });
  out.adbop = ad('#c81a2a', '#fff', ['BLOWOUT PREVENTER', 'prevents blowouts. mostly.'], 320, 64, { small: '#ffe14d', lit: false });
  out.adlifeboat = ad('#ff7a1a', '#120818', ['LIFEBOAT', 'seats 6. we have 40.'], 256, 64, { small: '#120818', lit: false });
  out.adcompress = ad('#3e6890', '#fff', ['COMPRESSOR HOUSE', 'ear defenders: optional (they are not)'], 320, 64, { small: '#ffe14d', lit: false });
  out.adsnack = ad('#ff4fd8', '#fff', ['THE SNACK RUN', 'snacks to the rig since 1986'], 320, 64, { small: '#120818' });
  out.adsnacks = ad('#ff4fd8', '#ffe14d', ['SNACKS'], 192, 64, { lit: false });
  out.adhelideck = ad('#120818', '#4fd8ff', ['HELIDECK', 'no parking. no picnics. no.'], 256, 64, { small: '#fff' });
  out.adpig = ad('#3e6890', '#fff', ['PIG LAUNCHER', 'no pigs were harmed'], 256, 64, { small: '#ffe14d', lit: false });
  out.addeep = ad('#ffe14d', '#120818', ['MIND THE GAP', 'it is the sea'], 192, 64, { small: '#c81a2a', lit: false });
  out.flagglug = ad('#ffe14d', '#120818', ['GLUG'], 160, 96, { lit: false });
  out.adtoad = ad('#39ff14', '#120818', ['THE TOAD', 'personnel transfer. very safe.'], 256, 64, { small: '#120818' });
  out.adslurp = ad('#120818', '#ff4fd8', ['SLURP OIL', 'we were here first (we were not)'], 320, 80, { small: '#fff' });
  out.flagslurp = ad('#ff4fd8', '#120818', ['SLURP'], 160, 96, { lit: false });
}
