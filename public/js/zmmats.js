// Zombies map materials: what makes Jankfield High read as a school (lockers, chalkboards, book spines, the gym court,
// kids' paintings) and Second Opinion General as a hospital (lino, bed sheets, curtains, heart monitors, x-ray
// lightboxes, morgue drawers, pill shelves), plus their signs in the game's voice. Added to world.js's set like rigmats.js.
import * as THREE from 'three';

const rnd = (n) => (Math.random() * n) | 0;
const FONT = '"Arial Black", Impact, "Comic Sans MS", sans-serif';
const HAND = '"Comic Neue", "Comic Sans MS", cursive';

export function addZmMaps(out, canvasTex, speckle) {
  const lam = (t, tile, o) => ({ mat: new THREE.MeshLambertMaterial({ map: t, ...o }), tile });
  const smooth = (t) => { t.magFilter = THREE.LinearFilter; return t; };
  // ---- signs (the same sign painter as rigmats.js)
  const sign = (bg, fg, lines, w = 256, h = 64, o = {}) => {
    const t = smooth(canvasTex(h, (g) => {
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
    }, w));
    return { mat: o.lit ? new THREE.MeshBasicMaterial({ map: t }) : new THREE.MeshLambertMaterial({ map: t }), tile: 1 };
  };
  // a chalkboard: wooden frame, smeared green slate, wobbly chalk handwriting, a chalk tray
  const chalk = (lines, o = {}) => lam(smooth(canvasTex(128, (g, s, w) => {
    g.fillStyle = '#8a5a2c'; g.fillRect(0, 0, w, s);
    g.fillStyle = o.bg || '#27503a'; g.fillRect(7, 7, w - 14, s - 18);
    for (let i = 0; i < 26; i++) { g.fillStyle = `rgba(255,255,255,${0.02 + Math.random() * 0.04})`; g.fillRect(8 + rnd(w - 60), 8 + rnd(s - 34), 20 + rnd(60), 5 + rnd(12)); }
    g.fillStyle = '#e8e2d0'; g.fillRect(w * 0.3, s - 9, 14, 3); g.fillStyle = '#ff9ad0'; g.fillRect(w * 0.6, s - 9, 10, 3);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const px = Math.min(26, (s - 40) / lines.length * 0.8);
    lines.forEach((ln, i) => {
      let fs = px; g.font = `bold ${fs}px ${HAND}`; while (g.measureText(ln).width > w - 34 && fs > 7) { fs -= 1; g.font = `bold ${fs}px ${HAND}`; }
      g.save(); g.translate(w / 2, 20 + (i + 0.5) * (s - 42) / lines.length); g.rotate((Math.random() - 0.5) * 0.05);
      g.fillStyle = i % 3 === 2 && o.pink ? '#ffb0dc' : '#f2f0e4'; g.fillText(ln, 0, 0); g.restore();
    });
  }, 256)), 1);

  // ================================================================ JANKFIELD HIGH
  // lockers: two 0.5 m doors a metre, vents up top, a little handle, the odd dent and sticker
  const locker = (rgb, dark) => lam(canvasTex(32, (g, s) => {
    speckle(g, s, rgb, 8, 2); g.fillStyle = dark;
    for (const x of [0, 16]) { g.fillRect(x, 0, 1, s); g.fillRect(x + 15, 0, 1, s); g.fillRect(x, 0, 16, 1); g.fillRect(x, s - 1, 16, 1); for (let y = 4; y < 11; y += 2) g.fillRect(x + 4, y, 8, 1); }
    g.fillStyle = '#d8d8e0'; g.fillRect(12, 17, 2, 4); g.fillRect(28, 17, 2, 4);
    g.fillStyle = ['#ffe14d', '#39ff14', '#fff'][rnd(3)]; g.fillRect(3 + 16 * rnd(2), 22, 4, 3);
  }), 1);
  out.lockerb = locker([74, 132, 190], '#2c4e78'); out.lockerp = locker([226, 96, 170], '#8a2c68');
  // library shelves: three rows of book spines a metre
  out.books = lam(canvasTex(48, (g, s) => {
    g.fillStyle = '#5a3a1c'; g.fillRect(0, 0, s, s);
    const C = ['#c8202c', '#2050b0', '#2a8a4a', '#e8c040', '#8a4ac0', '#e86a20', '#e8e0d0', '#20a0a8', '#ff4fd8'];
    for (let r = 0; r < 3; r++) for (let x = 1; x < s - 1;) { const w = 2 + rnd(3), h = 9 + rnd(5); g.fillStyle = C[rnd(C.length)]; g.fillRect(x, r * 16 + 15 - h, w, h); if (w > 2) { g.fillStyle = 'rgba(255,255,255,0.5)'; g.fillRect(x + 1, r * 16 + 17 - h, 1, 3); } x += w + (Math.random() < 0.12 ? 2 : 0); }
    g.fillStyle = '#7a5228'; for (let r = 0; r < 3; r++) g.fillRect(0, r * 16 + 15, s, 1);
  }), 1);
  // the gym court (drawn once over the whole floor): boards, a boundary, the centre circle with the mascot's face, two keys
  out.court = lam(smooth(canvasTex(384, (g, s, w) => {
    for (let x = 0; x < w; x += 8) { const k = 196 + rnd(22); g.fillStyle = `rgb(${k},${k * 0.72 | 0},${k * 0.4 | 0})`; g.fillRect(x, 0, 8, s); }
    g.fillStyle = 'rgba(90,50,20,0.25)'; for (let i = 0; i < 90; i++) g.fillRect(rnd(w / 8) * 8, rnd(s), 8, 1);
    g.strokeStyle = '#f4f0e8'; g.lineWidth = 4; g.strokeRect(10, 10, w - 20, s - 20);
    g.beginPath(); g.moveTo(10, s / 2); g.lineTo(w - 10, s / 2); g.stroke();
    g.fillStyle = '#ff4fd8'; g.beginPath(); g.arc(w / 2, s / 2, 38, 0, 7); g.fill(); g.stroke();
    g.fillStyle = '#ffe14d'; g.beginPath(); g.ellipse(w / 2, s / 2, 17, 22, 0, 0, 7); g.fill(); // the fighting mannequin: a blank egg. fierce.
    g.strokeStyle = '#120818'; g.lineWidth = 3; g.beginPath(); g.moveTo(w / 2 - 12, s / 2 - 8); g.lineTo(w / 2 - 3, s / 2 - 4); g.moveTo(w / 2 + 12, s / 2 - 8); g.lineTo(w / 2 + 3, s / 2 - 4); g.stroke();
    g.strokeStyle = '#f4f0e8'; g.lineWidth = 4;
    for (const e of [0, 1]) { const y = e ? s - 10 : 10, d = e ? -1 : 1; g.fillStyle = 'rgba(79,216,255,0.55)'; g.fillRect(w / 2 - 34, Math.min(y, y + d * 76), 68, 76); g.strokeRect(w / 2 - 34, Math.min(y, y + d * 76), 68, 76); g.beginPath(); g.arc(w / 2, y + d * 76, 34, e ? Math.PI : 0, e ? Math.PI * 2 : Math.PI); g.stroke(); g.beginPath(); g.arc(w / 2, y, 104, e ? Math.PI : 0, e ? Math.PI * 2 : Math.PI); g.stroke(); }
  }, 256)), 1);
  out.backboard = lam(canvasTex(48, (g, s, w) => { g.fillStyle = '#f4f0e8'; g.fillRect(0, 0, w, s); g.strokeStyle = '#c8202c'; g.lineWidth = 3; g.strokeRect(2, 2, w - 4, s - 4); g.strokeRect(w / 2 - 12, s - 26, 24, 18); }, 80), 1);
  out.hoop = { mat: new THREE.MeshLambertMaterial({ color: 0xff6a1a }), tile: 1 };
  // art class: three proud paintings
  const art = (bg, draw) => lam(smooth(canvasTex(96, (g, s, w) => { g.fillStyle = '#f4f0e8'; g.fillRect(0, 0, w, s); g.fillStyle = bg; g.fillRect(4, 4, w - 8, s - 8); g.lineCap = 'round'; draw(g, w, s); }, 128)), 1);
  out.kidart1 = art('#bfe8ff', (g, w, s) => { g.fillStyle = '#7dff4f'; g.fillRect(4, s - 26, w - 8, 22); g.fillStyle = '#ffe14d'; g.beginPath(); g.arc(w - 26, 24, 13, 0, 7); g.fill(); g.strokeStyle = '#ffe14d'; g.lineWidth = 3; for (let a = 0; a < 7; a += 0.8) { g.beginPath(); g.moveTo(w - 26 + Math.cos(a) * 16, 24 + Math.sin(a) * 16); g.lineTo(w - 26 + Math.cos(a) * 23, 24 + Math.sin(a) * 23); g.stroke(); } g.fillStyle = '#ff3030'; g.fillRect(22, s - 50, 36, 28); g.fillStyle = '#8a4a2a'; g.beginPath(); g.moveTo(16, s - 50); g.lineTo(40, s - 72); g.lineTo(64, s - 50); g.fill(); g.fillStyle = '#120818'; g.font = `bold 11px ${HAND}`; g.fillText('my house (b4)', 10, 18); });
  out.kidart2 = art('#ffd6ec', (g, w, s) => { g.strokeStyle = '#120818'; g.lineWidth = 4; for (const [x, c] of [[34, '#7dff4f'], [64, '#ffe14d'], [94, '#7dff4f']]) { g.fillStyle = c; g.beginPath(); g.ellipse(x, 34, 9, 12, 0, 0, 7); g.fill(); g.stroke(); g.beginPath(); g.moveTo(x, 46); g.lineTo(x, 68); g.moveTo(x - 12, 52); g.lineTo(x + 12, c === '#ffe14d' ? 52 : 44); g.moveTo(x, 68); g.lineTo(x - 8, 84); g.moveTo(x, 68); g.lineTo(x + 8, 84); g.stroke(); } g.fillStyle = '#120818'; g.font = `bold 11px ${HAND}`; g.fillText('me + my new frends', 10, 18); });
  out.kidart3 = art('#fff6c0', (g, w, s) => { for (let i = 0; i < 46; i++) { g.strokeStyle = ['#ff4fd8', '#4fd8ff', '#39ff14', '#ff3030', '#8a4ac0'][rnd(5)]; g.lineWidth = 2 + rnd(5); g.beginPath(); g.moveTo(8 + rnd(w - 16), 22 + rnd(s - 30)); g.lineTo(8 + rnd(w - 16), 22 + rnd(s - 30)); g.stroke(); } g.fillStyle = '#120818'; g.font = `bold 11px ${HAND}`; g.fillText('"feelings" A+', 10, 18); });
  out.chalk1 = chalk(['2 + 2 = 5', '(show your working)', 'test friday. bring a brain.'], { pink: 1 });
  out.chalk2 = chalk(['the mitochondria is the', 'powerhouse of the cell', 'this is all anyone remembers']);
  out.chalk3 = chalk(Array(6).fill('I will not bite my classmates'));
  // the periodic table, as remembered
  out.sgnperiodic = lam(smooth(canvasTex(128, (g, s, w) => {
    g.fillStyle = '#f4f0e8'; g.fillRect(0, 0, w, s); g.fillStyle = '#120818'; g.font = `bold 13px ${FONT}`; g.fillText('PERIODIC TABLE (from memory)', 8, 16);
    const C = ['#ff9ad0', '#ffe14d', '#9adfff', '#a8f090', '#d0b0ff'], E = { 0: 'H', 17: 'He', 40: 'Jk', 22: 'Fe', 47: 'Au', 58: '??', 75: 'Um' };
    for (let r = 0; r < 6; r++) for (let c = 0; c < 18; c++) { if ((r === 0 && c > 0 && c < 17) || (r < 3 && c > 1 && c < 12)) continue; const i = r * 18 + c; g.fillStyle = C[(c * 7 + r * 3) % 5]; g.fillRect(6 + c * 13.6, 24 + r * 16, 12.6, 15); if (E[i]) { g.fillStyle = '#120818'; g.font = `bold 8px ${FONT}`; g.fillText(E[i], 7 + c * 13.6, 35 + r * 16); } }
  }, 256)), 1);
  out.sgnschool = sign('#ff4fd8', '#ffe14d', ['JANKFIELD HIGH', 'home of the fighting mannequins'], 448, 64, { small: '#fff' });
  out.sgntrophy = sign('#3a2a1a', '#ffe14d', ['TROPHIES', 'participation, mostly'], 256, 64, { small: '#fff' });
  out.sgnprom = sign('#120818', '#ff4fd8', ['PROM IS CANCELLED', 'reason: zombies. no refunds.'], 256, 160, { small: '#ffe14d' });
  out.sgnmenu = sign('#1a3a2a', '#fff', ['TODAY: MEAT?', 'the question mark is load-bearing', 'also: beige'], 256, 96, { small: '#ffe14d' });
  out.sgnnorun = sign('#ffe14d', '#120818', ['NO RUNNING', 'walking fast while screaming is fine'], 320, 64, { small: '#c81a2a' });
  out.sgnhall = sign('#f4f0e8', '#2050b0', ['HALL PASS REQUIRED', 'zombies exempt, apparently'], 320, 64, { small: '#120818' });
  out.sgnlab = sign('#2050b0', '#fff', ['SCIENCE LAB', 'goggles: somewhere'], 256, 48, { small: '#ffe14d' });
  out.sgnboiler = sign('#c81a2a', '#fff', ['BOILER ROOM', 'staff only. the staff are zombies now.'], 320, 80, { small: '#ffe14d' });
  out.sgnchamps = sign('#2050b0', '#ffe14d', ['REGIONAL CHAMPS 1997', 'it was a small region'], 384, 96, { small: '#fff' });
  out.sgnscore = sign('#120818', '#ff3030', ['HOME 02 : 99 DEAD', 'period 4 of 4. nobody is coming to stop this.'], 320, 128, { small: '#ffe14d', lit: 1 });
  out.sgnlib = sign('#3a2a1a', '#fff', ['LIBRARY', 'shhh. they can hear you.'], 256, 48, { small: '#ffe14d' });
  out.sgnart = sign('#ff4fd8', '#fff', ['ART ROOM', 'everything in here is a masterpiece'], 256, 48, { small: '#120818' });
  out.sgnprin = sign('#120818', '#ffe14d', ['PRINCIPAL', 'you are in so much trouble'], 256, 48, { small: '#fff' });
  out.sgndet = sign('#f4f0e8', '#c81a2a', ['DETENTION LIST', 'everyone', '(see me after the apocalypse)'], 256, 128, { small: '#120818' });

  // ================================================================ SECOND OPINION GENERAL
  out.lino = lam(canvasTex(16, (g, s) => { speckle(g, s, [206, 222, 208], 8, 2); g.fillStyle = 'rgba(120,170,150,0.55)'; g.fillRect(0, 0, 8, 8); g.fillRect(8, 8, 8, 8); g.fillStyle = 'rgba(60,80,70,0.25)'; g.fillRect(rnd(s), rnd(s), 3, 1); }), 2);
  out.linob = lam(canvasTex(16, (g, s) => { speckle(g, s, [196, 208, 226], 8, 2); g.fillStyle = 'rgba(110,140,190,0.5)'; g.fillRect(0, 0, 8, 8); g.fillRect(8, 8, 8, 8); }), 2);
  out.hospglass = { mat: new THREE.MeshLambertMaterial({ color: 0xbfe8e0, transparent: true, opacity: 0.28, depthWrite: false }), tile: 2 }; // the ramp's box: you see who's coming
  out.mint = lam(canvasTex(16, (g, s) => { speckle(g, s, [150, 206, 180], 8, 2); }), 2);
  out.sheet = lam(canvasTex(16, (g, s) => { speckle(g, s, [238, 240, 244], 6, 2); g.fillStyle = 'rgba(120,170,220,0.5)'; for (let y = 3; y < s; y += 8) g.fillRect(0, y, s, 1); }), 0.8);
  out.blanket = lam(canvasTex(16, (g, s) => { speckle(g, s, [110, 190, 200], 12, 2); g.fillStyle = 'rgba(255,255,255,0.3)'; for (let x = 0; x < s; x += 4) g.fillRect(x, 0, 1, s); }), 0.8);
  out.curtain = lam(canvasTex(16, (g, s) => { for (let x = 0; x < s; x++) { const k = 0.78 + 0.22 * Math.sin(x / s * Math.PI * 6); g.fillStyle = `rgb(${150 * k | 0},${200 * k | 0},${230 * k | 0})`; g.fillRect(x, 0, 1, s); } g.fillStyle = '#e8e8f0'; g.fillRect(0, 0, s, 1); }), 1, { side: THREE.DoubleSide });
  // steel body drawers, three a metre across, a handle and a tag each
  out.morgue = lam(canvasTex(32, (g, s) => { speckle(g, s, [150, 158, 168], 8, 2); g.strokeStyle = '#4a5058'; g.lineWidth = 1; g.strokeRect(1.5, 1.5, s - 3, s - 3); g.fillStyle = '#e0e4ea'; g.fillRect(11, 20, 10, 2); g.fillStyle = '#f4f0e8'; g.fillRect(13, 8, 6, 4); g.fillStyle = '#4a5058'; g.fillRect(14, 9, 4, 1); }), 0.8);
  // pharmacy shelves: rows of boxes and bottles
  out.pills = lam(canvasTex(48, (g, s) => {
    g.fillStyle = '#e8ecf0'; g.fillRect(0, 0, s, s);
    const C = ['#ff4fd8', '#4fd8ff', '#ffe14d', '#39ff14', '#ff7a1a', '#fff', '#d0b0ff'];
    for (let r = 0; r < 3; r++) { for (let x = 1; x < s - 2;) { const w = 3 + rnd(4), h = 6 + rnd(7), c = C[rnd(C.length)]; g.fillStyle = c; g.fillRect(x, r * 16 + 14 - h, w, h); g.fillStyle = 'rgba(18,8,24,0.55)'; g.fillRect(x, r * 16 + 14 - h + 2, w, 2); if (rnd(3) === 0) { g.fillStyle = '#f4f0e8'; g.fillRect(x + 1, r * 16 + 12 - h, w - 2, 2); } x += w + 1; } g.fillStyle = '#9aa2ac'; g.fillRect(0, r * 16 + 14, s, 2); }
  }), 1);
  // a heart monitor: one bored green trace
  out.ecg = { mat: new THREE.MeshBasicMaterial({ map: smooth(canvasTex(64, (g, s, w) => { g.fillStyle = '#06140a'; g.fillRect(0, 0, w, s); g.strokeStyle = 'rgba(57,255,20,0.18)'; g.lineWidth = 1; for (let x = 0; x < w; x += 8) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, s); g.stroke(); } g.strokeStyle = '#39ff14'; g.lineWidth = 2; g.beginPath(); g.moveTo(0, 38); for (const [x, y] of [[14, 38], [18, 32], [22, 38], [28, 38], [31, 12], [35, 54], [39, 38], [52, 38], [56, 30], [60, 38], [72, 38], [96, 38]]) g.lineTo(x, y); g.stroke(); g.fillStyle = '#39ff14'; g.font = `bold 11px ${FONT}`; g.fillText('BPM 0', 54, 14); g.fillStyle = '#ffe14d'; g.font = `8px ${FONT}`; g.fillText('(fine)', 60, 58); }, 96)) }), tile: 1 };
  // an x-ray lightbox: a mannequin, seen through
  out.xraylit = { mat: new THREE.MeshBasicMaterial({ map: smooth(canvasTex(128, (g, s, w) => {
    g.fillStyle = '#d8ecff'; g.fillRect(0, 0, w, s); g.fillStyle = '#0a1420'; g.fillRect(5, 5, w - 10, s - 10);
    g.strokeStyle = '#bfe2ff'; g.fillStyle = '#bfe2ff'; g.lineCap = 'round'; const cx = w / 2;
    g.lineWidth = 3; g.beginPath(); g.ellipse(cx, 24, 10, 13, 0, 0, 7); g.stroke(); g.fillRect(cx - 5, 26, 3, 3); g.fillRect(cx + 2, 26, 3, 3);
    g.lineWidth = 4; g.beginPath(); g.moveTo(cx, 38); g.lineTo(cx, 84); g.stroke();
    g.lineWidth = 2; for (let y = 46; y < 72; y += 6) { g.beginPath(); g.ellipse(cx, y, 16 - (y - 46) * 0.15, 4, 0, 0, 7); g.stroke(); }
    g.lineWidth = 3; g.beginPath(); g.moveTo(cx - 18, 44); g.lineTo(cx - 28, 70); g.lineTo(cx - 24, 94); g.moveTo(cx + 18, 44); g.lineTo(cx + 28, 70); g.lineTo(cx + 24, 94); g.moveTo(cx - 8, 86); g.lineTo(cx - 10, 122); g.moveTo(cx + 8, 86); g.lineTo(cx + 10, 122); g.stroke();
    g.beginPath(); g.arc(cx - 28, 70, 3, 0, 7); g.arc(cx + 28, 70, 3, 0, 7); g.fill(); // ball joints, obviously
    g.fillStyle = '#ffe14d'; g.fillRect(cx + 3, 56, 7, 5); // a swallowed coin
  }, 96)) }), tile: 1 };
  // the eye chart
  out.eyechart = lam(smooth(canvasTex(160, (g, s, w) => { g.fillStyle = '#f4f0e8'; g.fillRect(0, 0, w, s); g.strokeStyle = '#120818'; g.lineWidth = 3; g.strokeRect(2, 2, w - 4, s - 4); g.fillStyle = '#120818'; g.textAlign = 'center'; ['J', 'A N', 'K F I', 'R E O K', 'y o u r e f i n e'].forEach((ln, i) => { g.font = `bold ${[44, 30, 22, 15, 9][i]}px ${FONT}`; g.fillText(ln, w / 2, [46, 80, 106, 126, 144][i]); }); }, 112)), 1);
  // the children's ward mural: a sun, a rainbow, three happy mannequins
  out.mural = lam(smooth(canvasTex(128, (g, s, w) => {
    g.fillStyle = '#bfe8ff'; g.fillRect(0, 0, w, s); g.fillStyle = '#7dff4f'; g.fillRect(0, s - 28, w, 28);
    ['#ff3030', '#ff7a1a', '#ffe14d', '#39ff14', '#4fd8ff', '#8a4ac0'].forEach((c, i) => { g.strokeStyle = c; g.lineWidth = 6; g.beginPath(); g.arc(w / 2, s - 26, 96 - i * 6, Math.PI, Math.PI * 2); g.stroke(); });
    g.fillStyle = '#ffe14d'; g.beginPath(); g.arc(46, 30, 18, 0, 7); g.fill(); g.fillStyle = '#120818'; g.fillRect(39, 25, 3, 3); g.fillRect(50, 25, 3, 3); g.fillRect(41, 35, 10, 2);
    for (const [x, c] of [[w - 110, '#ff9ad0'], [w - 76, '#ffe14d'], [w - 42, '#9adfff']]) { g.fillStyle = c; g.strokeStyle = '#120818'; g.lineWidth = 3; g.beginPath(); g.ellipse(x, s - 62, 9, 12, 0, 0, 7); g.fill(); g.stroke(); g.fillRect(x - 8, s - 50, 16, 22); g.strokeRect(x - 8, s - 50, 16, 22); g.beginPath(); g.moveTo(x - 8, s - 44); g.lineTo(x - 18, s - 56); g.moveTo(x + 8, s - 44); g.lineTo(x + 18, s - 56); g.moveTo(x - 4, s - 28); g.lineTo(x - 4, s - 12); g.moveTo(x + 4, s - 28); g.lineTo(x + 4, s - 12); g.stroke(); }
  }, 384)), 1);
  out.sgnhosp = sign('#4fd8ff', '#fff', ['SECOND OPINION GENERAL', 'you will probably be fine'], 448, 64, { small: '#120818' });
  out.sgner = sign('#c81a2a', '#fff', ['EMERGENCY', 'take a number. current wait: forever.'], 320, 64, { small: '#ffe14d' });
  out.sgnwait = sign('#120818', '#39ff14', ['NOW SERVING: 003', 'your number: 8,412'], 256, 80, { small: '#ffe14d', lit: 1 });
  out.sgnpharm = sign('#1a8a3a', '#fff', ['PHARMACY', 'ask about our pills (do not)'], 256, 48, { small: '#ffe14d' });
  out.sgnwarda = sign('#f4f0e8', '#2050b0', ['WARD A', 'visiting hours are over'], 256, 48, { small: '#120818' });
  out.sgnwardb = sign('#f4f0e8', '#2050b0', ['WARD B', 'like ward A, but upstairs'], 256, 48, { small: '#120818' });
  out.sgnxray = sign('#120818', '#4fd8ff', ['X-RAY', 'smile with your bones'], 256, 48, { small: '#fff' });
  out.sgnmorgue = sign('#3a3a44', '#fff', ['MORGUE', 'quiet please (they were)'], 256, 48, { small: '#ffe14d' });
  out.sgnsurg = sign('#1a6a5a', '#fff', ['OPERATING THEATRE', 'no refunds'], 320, 48, { small: '#ffe14d' });
  out.sgnicu = sign('#f4f0e8', '#c81a2a', ['INTENSIVE CARE', 'we care. intensely.'], 256, 48, { small: '#120818' });
  out.sgnkids = sign('#ffe14d', '#ff4fd8', ['CHILDREN\'S WARD', 'be brave. braver than that.'], 256, 48, { small: '#120818' });
  out.sgnstaff = sign('#3a2a1a', '#fff', ['STAFF ONLY', 'the coffee is also dead'], 256, 48, { small: '#ffe14d' });
  out.sgnwash = sign('#4fd8ff', '#120818', ['WASH YOUR HANDS', 'all of them'], 256, 64, { small: '#120818' });
  out.sgnramp = sign('#ffe14d', '#120818', ['RAMP', 'it is a ramp. legally.'], 256, 64, { small: '#c81a2a' });
  out.sgngen = sign('#c81a2a', '#fff', ['BACKUP GENERATOR', 'pull lever. hope.'], 256, 64, { small: '#ffe14d' });
  out.sgnquiet = sign('#f4f0e8', '#1a6a5a', ['QUIET PLEASE', 'healing in progress'], 256, 64, { small: '#120818' });
  out.sgnbridge = sign('#2050b0', '#fff', ['SKYBRIDGE', 'do not look down at the waiting room'], 320, 48, { small: '#ffe14d' });
}
