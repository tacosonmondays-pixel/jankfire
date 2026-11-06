// Scary Forest materials: bark, pine needles, log cabin walls, a lake, the radio mast's red lights, signs in the game's
// voice. Added to world.js's set like vibe.js. The ones that blink (mast lights, hazards, the lantern) are kept in
// FMATS so forest.js can animate them.
import * as THREE from 'three';

const rnd = (n) => (Math.random() * n) | 0;
const FONT = '"Arial Black", Impact, "Comic Sans MS", sans-serif';
export const FMATS = {};

export function addForest(out, canvasTex, speckle) {
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  const flat = (rgb, vary = 14, px = 2) => (g, s, w) => speckle(g, s, rgb, vary, px, w);
  const stripes = (rgb, line, step = 4, vert = false) => (g, s) => { speckle(g, s, rgb, 14, 2); g.fillStyle = line; for (let i = step - 1; i < s; i += step) vert ? g.fillRect(i, 0, 1, s) : g.fillRect(0, i, s, 1); };
  const blobs = (g, s, cols, n, rmin, rmax) => { // wrapped so the tile is seamless
    for (let i = 0; i < n; i++) {
      g.fillStyle = cols[i % cols.length];
      const x = rnd(s), y = rnd(s), r = rmin + rnd(rmax - rmin);
      for (const ox of [-s, 0, s]) for (const oy of [-s, 0, s]) { g.beginPath(); g.ellipse(x + ox, y + oy, r, r * 0.7, 0, 0, Math.PI * 2); g.fill(); }
    }
  };
  // ---- the floor of the woods: needles, dirt, mud, trails
  out.needles = lam(canvasTex(32, (g, s) => { speckle(g, s, [58, 52, 36], 22, 2); blobs(g, s, ['rgba(40,64,30,0.5)', 'rgba(92,66,40,0.45)', 'rgba(30,26,20,0.4)'], 14, 2, 6); g.fillStyle = 'rgba(140,100,60,0.5)'; for (let i = 0; i < 26; i++) { const x = rnd(s), y = rnd(s); g.fillRect(x, y, 3, 1); } }), 3);
  out.dirtroad = lam(canvasTex(32, (g, s) => { speckle(g, s, [104, 82, 58], 22, 2); g.fillStyle = 'rgba(60,44,30,0.5)'; g.fillRect(0, 7, s, 3); g.fillRect(0, 22, s, 3); blobs(g, s, ['rgba(140,116,84,0.35)'], 6, 1, 3); }), 4);
  out.trail = lam(canvasTex(16, flat([92, 72, 50], 20)), 2);
  out.mud = lam(canvasTex(16, flat([52, 44, 34], 14)), 2);
  out.gravel = lam(canvasTex(16, (g, s) => { speckle(g, s, [110, 108, 104], 40, 1); }), 1.5);
  out.ash = lam(canvasTex(16, (g, s) => { speckle(g, s, [62, 60, 58], 30, 1); g.fillStyle = '#1a1816'; for (let i = 0; i < 10; i++) g.fillRect(rnd(s), rnd(s), 2, 2); }), 1);
  out.charcoal = { mat: new THREE.MeshLambertMaterial({ color: 0x1c1a18 }), tile: 1 };
  // ---- trees
  const bark = (rgb, dark) => (g, s) => { speckle(g, s, rgb, 18, 2); g.fillStyle = dark; for (let x = 1; x < s; x += 4) g.fillRect(x + rnd(2), 0, 1, s); for (let i = 0; i < 6; i++) g.fillRect(rnd(s), rnd(s), 2, 3); };
  out.bark = lam(canvasTex(16, bark([74, 54, 40], '#2a1c12')), 1.5);
  out.bark2 = lam(canvasTex(16, bark([88, 70, 56], '#30241a')), 1.5);
  out.deadbark = lam(canvasTex(16, bark([118, 114, 106], '#4a4640')), 1.5);
  out.birch = lam(canvasTex(16, (g, s) => { speckle(g, s, [214, 210, 196], 10, 2); g.fillStyle = '#1e1c1a'; for (let i = 0; i < 9; i++) g.fillRect(rnd(s), rnd(s), 3 + rnd(4), 1); }), 1.5);
  const needle = (rgb) => (g, s) => { speckle(g, s, rgb, 26, 2); g.fillStyle = 'rgba(0,0,0,0.25)'; for (let y = 3; y < s; y += 4) for (let x = (y >> 2) % 2 ? 0 : 2; x < s; x += 4) g.fillRect(x, y, 2, 1); };
  out.pine = lam(canvasTex(16, needle([30, 62, 44])), 2);
  out.pine2 = lam(canvasTex(16, needle([22, 50, 40])), 2);
  out.birchleaf = lam(canvasTex(16, flat([92, 110, 52], 30)), 2);
  out.fern = lam(canvasTex(16, flat([40, 78, 40], 34)), 1.5);
  out.bush = lam(canvasTex(16, flat([34, 58, 36], 28)), 1.5);
  out.reed = lam(canvasTex(16, flat([108, 104, 64], 20)), 1);
  out.logside = lam(canvasTex(16, stripes([96, 70, 48], '#3a2616', 3)), 1);
  out.logend = lam(canvasTex(16, (g, s) => { speckle(g, s, [176, 140, 96], 12, 1); g.strokeStyle = '#7a5a36'; for (let r = 2; r < 8; r += 2) { g.beginPath(); g.arc(8, 8, r, 0, 7); g.stroke(); } }), 1);
  out.rootball = lam(canvasTex(16, (g, s) => { speckle(g, s, [70, 54, 40], 30, 2); g.fillStyle = '#2a1c12'; for (let i = 0; i < 8; i++) g.fillRect(rnd(s), 0, 1, s); }), 1.5);
  out.rockf = lam(canvasTex(16, (g, s) => { speckle(g, s, [96, 98, 102], 24, 2); g.fillStyle = '#4a4c52'; g.fillRect(2, 5, 6, 1); g.fillRect(9, 11, 5, 1); }), 2);
  out.rockmoss = lam(canvasTex(16, (g, s) => { speckle(g, s, [92, 96, 96], 22, 2); blobs(g, s, ['rgba(60,96,44,0.7)'], 5, 2, 5); }), 2);
  // ---- buildings
  out.logwall = lam(canvasTex(16, (g, s) => { speckle(g, s, [104, 74, 50], 16, 1); g.fillStyle = '#2e1e12'; for (let y = 3; y < s; y += 4) g.fillRect(0, y, s, 1); g.fillStyle = 'rgba(255,220,170,0.12)'; for (let y = 0; y < s; y += 4) g.fillRect(0, y, s, 1); }), 1.2);
  out.planks = lam(canvasTex(16, (g, s) => { speckle(g, s, [110, 98, 82], 14, 1); g.fillStyle = '#3e342a'; for (let x = 3; x < s; x += 4) g.fillRect(x, 0, 1, s); g.fillRect(rnd(s), rnd(s), 1, 1); }), 1.2);
  out.towerwood = lam(canvasTex(16, stripes([124, 96, 66], '#4a3420', 4, true)), 1.2);
  out.stonebase = lam(canvasTex(16, (g, s) => { speckle(g, s, [104, 100, 96], 26, 2); g.fillStyle = '#3a3836'; g.fillRect(0, 7, s, 1); g.fillRect(0, 15, s, 1); g.fillRect(5, 0, 1, 7); g.fillRect(11, 8, 1, 7); }), 1.4);
  out.cabinroof = lam(canvasTex(16, stripes([58, 46, 42], '#201814', 4)), 1.2);
  out.cabinroof2 = lam(canvasTex(16, (g, s) => { stripes([52, 52, 40], '#1e1c14', 4)(g, s); blobs(g, s, ['rgba(70,96,50,0.6)'], 3, 2, 4); }), 1.2);
  out.shedmetal = lam(canvasTex(16, stripes([120, 128, 120], '#5a625a', 3, true)), 1.4);
  out.bedsheet = lam(canvasTex(16, (g, s) => { speckle(g, s, [150, 140, 128], 10, 2); g.fillStyle = 'rgba(80,40,30,0.4)'; g.fillRect(4, 6, 6, 4); }), 2);
  out.glassdark = { mat: new THREE.MeshLambertMaterial({ color: 0x0c141c, emissive: 0x05080c }), tile: 1 };
  out.officechair = { mat: new THREE.MeshPhongMaterial({ color: 0x1a1c24, shininess: 60, specular: 0x666688 }), tile: 1 };
  out.coolerwater = { mat: new THREE.MeshPhongMaterial({ color: 0x5ab8ff, shininess: 120, specular: 0xffffff, transparent: true, opacity: 0.8 }), tile: 1 };
  out.cooler = { mat: new THREE.MeshPhongMaterial({ color: 0xc8202c, shininess: 80, specular: 0xffffff }), tile: 1 };
  out.tentorange = lam(canvasTex(16, stripes([220, 110, 30], 'rgba(0,0,0,0.25)', 5)), 1.5);
  out.tentgreen = lam(canvasTex(16, stripes([60, 120, 70], 'rgba(0,0,0,0.25)', 5)), 1.5);
  out.tentdark = { mat: new THREE.MeshBasicMaterial({ color: 0x050405 }), tile: 1 };
  out.boatwood = lam(canvasTex(16, stripes([150, 60, 40], '#4a1a10', 3)), 1);
  out.canoe = { mat: new THREE.MeshPhongMaterial({ color: 0x2a8a8a, shininess: 90, specular: 0xffffff }), tile: 1 };
  out.carrust = lam(canvasTex(16, (g, s) => { speckle(g, s, [70, 96, 120], 12, 2); blobs(g, s, ['rgba(140,70,30,0.8)', 'rgba(90,44,20,0.7)'], 7, 1, 4); }), 1.5);
  out.rangergreen = lam(canvasTex(16, flat([46, 80, 52], 8)), 2);
  out.generator = lam(canvasTex(16, (g, s) => { speckle(g, s, [220, 180, 40], 12, 2); g.fillStyle = '#222'; g.fillRect(2, 4, 12, 2); g.fillRect(2, 9, 12, 2); }), 1.5);
  out.cable = lam(canvasTex(16, stripes([40, 40, 44], '#111', 2)), 0.6);
  const cl = canvasTex(16, (g, s) => { g.clearRect(0, 0, s, s); g.strokeStyle = '#6a7276'; g.lineWidth = 1; for (let i = -s; i < s * 2; i += 4) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + s, s); g.moveTo(i + s, 0); g.lineTo(i, s); g.stroke(); } });
  cl.minFilter = THREE.NearestFilter; cl.generateMipmaps = false; // mipmaps turned the mesh into a solid grey sheet at a distance
  out.chainlink = { mat: new THREE.MeshLambertMaterial({ map: cl, transparent: true, alphaTest: 0.5, side: THREE.DoubleSide }), tile: 1 };
  out.mastred = lam(canvasTex(16, flat([210, 40, 36], 10)), 2);
  out.mastwhite = lam(canvasTex(16, flat([226, 226, 222], 8)), 2);
  // ---- things that glow (forest.js blinks them)
  FMATS.mastlight = out.mastlight = { mat: new THREE.MeshBasicMaterial({ color: 0xff1a1a }), tile: 1 };
  FMATS.hazard2 = out.hazard2 = { mat: new THREE.MeshBasicMaterial({ color: 0xffa21a }), tile: 1 };
  FMATS.lantern = out.lantern = { mat: new THREE.MeshBasicMaterial({ color: 0xffc46a }), tile: 1 };
  out.radiopanel = { mat: new THREE.MeshBasicMaterial({ map: canvasTex(32, (g, s) => { g.fillStyle = '#10141a'; g.fillRect(0, 0, s, s); for (let y = 3; y < s; y += 6) for (let x = 3; x < s; x += 5) { g.fillStyle = ['#39ff14', '#ff3030', '#ffe14d', '#203040'][rnd(4)]; g.fillRect(x, y, 2, 2); } g.fillStyle = '#4fd8ff'; g.fillRect(3, s - 8, s - 6, 4); }) }), tile: 1 };
  out.warnsign = { mat: new THREE.MeshBasicMaterial({ color: 0xff3a20 }), tile: 1 };
  // the lake: dark, a little see-through, a cold glint of moon on it
  out.lakewater = { mat: new THREE.MeshPhongMaterial({ color: 0x060c16, specular: 0x9ab4e0, shininess: 70, transparent: true, opacity: 0.93, depthWrite: false }), tile: 4 };
  // ---- signs and paper (fit: drawn once across the face)
  const sign = (bg, fg, lines, w = 256, h = 96, o = {}) => {
    const t = canvasTex(h, (g) => {
      g.fillStyle = bg; g.fillRect(0, 0, w, h);
      if (o.wood) { g.fillStyle = 'rgba(0,0,0,0.18)'; for (let y = 6; y < h; y += 12) g.fillRect(0, y, w, 2); }
      g.strokeStyle = fg; g.lineWidth = 4; g.strokeRect(6, 6, w - 12, h - 12);
      g.textAlign = 'center'; g.textBaseline = 'middle';
      const n = lines.length;
      lines.forEach((ln, i) => {
        const big = i === 0, px = big ? (n > 1 ? h * 0.3 : h * 0.46) : h * 0.15;
        let fs = px; g.font = `${big ? 'bold ' : ''}${fs | 0}px ${FONT}`;
        while (g.measureText(ln).width > w - 26 && fs > 8) { fs -= 2; g.font = `${big ? 'bold ' : ''}${fs | 0}px ${FONT}`; }
        const y = n === 1 ? h / 2 : big ? h * 0.34 : h * (0.6 + (i - 1) * 0.16);
        g.fillStyle = big ? fg : (o.small || fg); g.fillText(ln, w / 2, y);
      });
    }, w);
    t.magFilter = THREE.LinearFilter;
    return { mat: new THREE.MeshLambertMaterial({ map: t, emissive: 0x181410 }), tile: 1 };
  };
  const wood = '#6a4a2a';
  out.signtrail = sign(wood, '#ffe9b0', ['SCARY FOREST', 'trailhead. stay on the path. no refunds.', 'if a tall man offers you a job, do not make eye contact'], 256, 96, { wood: 1, small: '#fff4d8' });
  out.signranger = sign('#2e5034', '#ffe14d', ['RANGER STATION', 'closed. the ranger went for a walk', 'in 1998'], 256, 96, { small: '#fff' });
  out.signtower = sign(wood, '#ffe9b0', ['FIRE LOOKOUT', 'climb at own risk. look at own risk.'], 256, 96, { wood: 1, small: '#fff4d8' });
  out.signmast = sign('#e8e4dc', '#d81e30', ['KEEP OUT', 'radio mast. 1,000,000 watts of smooth jazz'], 256, 96, { small: '#120818' });
  out.signturn = sign('#ff7a1a', '#120818', ['PROPERTY LINE', 'turn back. the woods past here are not yours'], 256, 96, { small: '#120818' });
  out.mapsheet = { mat: new THREE.MeshLambertMaterial({ map: canvasTex(32, (g, s) => { g.fillStyle = '#d8ccaa'; g.fillRect(0, 0, s, s); g.strokeStyle = '#6a8a5a'; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(rnd(s), rnd(s), 3 + rnd(8), 0, 7); g.stroke(); } g.fillStyle = '#d81e30'; g.fillRect(14, 14, 4, 4); }) }), tile: 1 };
  // the corkboard in the cabin: HR has been here
  const t = canvasTex(96, (g) => {
    const w = 192, h = 96;
    speckle(g, h, [160, 120, 70], 30, 2, w);
    const notes = [['MANDATORY FUN', 'in the woods. attendance is tracked'], ['PERFORMANCE REVIEW', 'tonight. he will find you'], ['DO NOT LOOK AT', 'the tall guy from HR'], ['WE ARE A FAMILY', '(you cannot leave)']];
    notes.forEach(([a, b], i) => {
      const x = 8 + (i % 2) * 92, y = 6 + ((i / 2) | 0) * 46;
      g.save(); g.translate(x + 42, y + 20); g.rotate((Math.random() - 0.5) * 0.18);
      g.fillStyle = i === 2 ? '#ffe14d' : '#f4f0e4'; g.fillRect(-42, -19, 84, 38);
      g.fillStyle = '#d81e30'; g.beginPath(); g.arc(0, -16, 3, 0, 7); g.fill();
      g.fillStyle = '#120818'; g.textAlign = 'center'; g.font = `bold 10px ${FONT}`; g.fillText(a, 0, -2); g.font = `8px ${FONT}`; g.fillText(b, 0, 11);
      g.restore();
    });
  }, 192);
  t.magFilter = THREE.LinearFilter;
  out.hrboard = { mat: new THREE.MeshLambertMaterial({ map: t }), tile: 1 };
}
