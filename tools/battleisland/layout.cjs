// Battle Island design sheets from the master plan (shared/battleisland.js): the top-down layout (shaded relief, roads,
// POIs named, a scale bar), the island's silhouette, and a heightmap for the Blender blockout (make_blockout.py).
// usage: node tools/battleisland/layout.cjs <outdir>     (writes layout.png, silhouette.png, height.bin + height.json)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), url = require('url');
const root = path.resolve(__dirname, '../..'), out = path.resolve(process.argv[2] || 'docs/maps/battleisland');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const M = await import(url.pathToFileURL(path.join(root, 'shared/battleisland.js')).href);
  const { islandH, PLAN, SEA, segDist } = M;
  const [X0, Z0, X1, Z1] = [-420, -380, 420, 380], S = 1, W = (X1 - X0) / S, H = (Z1 - Z0) / S;
  const hs = new Float32Array(W * H);
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) hs[j * W + i] = islandH(X0 + i * S, Z0 + j * S);
  fs.writeFileSync(path.join(out, 'height.bin'), Buffer.from(hs.buffer));
  fs.writeFileSync(path.join(out, 'height.json'), JSON.stringify({ x0: X0, z0: Z0, step: S, w: W, h: H, sea: SEA, pois: PLAN.pois, roads: PLAN.roads, river: PLAN.river }));
  // colour: sea by depth, beach, grass / jungle / rock by height and slope, hill-shaded from the north-west
  const lerp = (a, b, t) => a + (b - a) * t, mixc = (a, b, t) => a.map((v, k) => lerp(v, b[k], t));
  const rgb = new Uint8ClampedArray(W * H * 4), sil = new Uint8ClampedArray(W * H * 4);
  const jungle = (x, z) => segDist(x, z, PLAN.river.pts) < 60 || Math.hypot(x - 70, z + 6) < 70;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const k = j * W + i, h = hs[k], x = X0 + i * S, z = Z0 + j * S;
    const hx = hs[j * W + Math.min(W - 1, i + 1)] - hs[j * W + Math.max(0, i - 1)], hz = hs[Math.min(H - 1, j + 1) * W + i] - hs[Math.max(0, j - 1) * W + i];
    const slope = Math.hypot(hx, hz) / 2, shade = Math.max(0.45, Math.min(1.35, 1 + (-hx - hz) * 0.35));
    let c;
    if (h < SEA) { const d = Math.min(1, (SEA - h) / 8); c = mixc([110, 236, 226], [28, 70, 168], Math.pow(d, 0.6)); }
    else {
      if (h < SEA + 1.4) c = [246, 224, 160];
      else if (slope > 1.1) c = [168, 150, 136];
      else if (jungle(x, z)) c = [48, 156, 70];
      else if (h > 30) c = [134, 170, 96];
      else c = [116, 206, 86];
      c = c.map((v) => v * shade);
      for (const r of PLAN.roads) if (segDist(x, z, r.pts) < r.w / 2) { c = [96, 88, 84]; break; }
    }
    rgb.set([c[0], c[1], c[2], 255], k * 4);
    const land = h >= SEA;
    sil.set(land ? [255, 79, 216, 255] : [18, 8, 24, 255], k * 4);
  }
  const b = await chromium.launch({ args: ['--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: W + 360, height: H + 80 }, deviceScaleFactor: 2 });
  const font = 'data:font/woff2;base64,' + fs.readFileSync(path.join(root, 'public/fonts/comic-neue-latin-700-normal.woff2')).toString('base64');
  await pg.setContent(`<html><head><style>@font-face{font-family:CN;src:url(${font})}body{margin:0;background:#120818;font-family:CN}</style></head>
    <body><canvas id=c width=${W + 360} height=${H + 80}></canvas></body></html>`);
  await pg.evaluate(async ({ px, sil, W, H, X0, Z0, pois, islets }) => {
    await document.fonts.load('20px CN');
    const cv = document.getElementById('c'), g = cv.getContext('2d');
    const draw = (data, ox, oy) => { const im = new ImageData(new Uint8ClampedArray(data), W, H); g.putImageData(im, ox, oy); };
    draw(px, 20, 60);
    g.fillStyle = '#ffe14d'; g.font = '34px CN'; g.fillText('BATTLE ISLAND: layout (design draft)', 20, 42);
    g.strokeStyle = '#ff4fd8'; g.lineWidth = 3; g.strokeRect(20, 60, W, H);
    const P = (x, z) => [20 + (x - X0), 60 + (z - Z0)];
    // the mech drop pads (open sky, level): yellow rings
    for (const p of pois) for (const [dx, dz, r] of p.drop) { const [x, z] = P(p.c[0] + dx, p.c[1] + dz); g.strokeStyle = '#ffe14d'; g.lineWidth = 3; g.beginPath(); g.arc(x, z, r, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.moveTo(x - r * 0.6, z); g.lineTo(x + r * 0.6, z); g.moveTo(x, z - r * 0.6); g.lineTo(x, z + r * 0.6); g.stroke(); }
    for (const p of pois) {
      const [a, c] = P(p.rect[0], p.rect[1]), [e, f] = P(p.rect[2], p.rect[3]);
      g.strokeStyle = p.color; g.lineWidth = 3; g.setLineDash([8, 5]); g.strokeRect(a, c, e - a, f - c); g.setLineDash([]);
      const [cx, cz] = P(p.c[0] + (p.lab ? p.lab[0] : 0), p.c[1] + (p.lab ? p.lab[1] : 0));
      g.font = '19px CN'; const tw = g.measureText(p.name.toUpperCase()).width;
      g.fillStyle = 'rgba(18,8,24,0.88)'; g.fillRect(cx - tw / 2 - 6, cz - 15, tw + 12, 24); g.strokeStyle = p.color; g.lineWidth = 2; g.strokeRect(cx - tw / 2 - 6, cz - 15, tw + 12, 24);
      g.fillStyle = '#fff'; g.fillText(p.name.toUpperCase(), cx - tw / 2, cz + 3);
    }
    // scale bar + north arrow
    const [sx, sy] = [40, 60 + H - 30];
    g.fillStyle = '#fff'; g.fillRect(sx, sy, 100, 8); g.fillStyle = '#120818'; g.fillRect(sx + 50, sy + 1, 50, 6);
    g.font = '16px CN'; g.fillStyle = '#fff'; g.fillText('100 m', sx + 30, sy - 6);
    g.fillText('N', W - 20, 92); g.beginPath(); g.moveTo(W - 14, 100); g.lineTo(W - 22, 124); g.lineTo(W - 6, 124); g.fill();
    // the legend: the POIs, numbered
    let y = 90; g.font = '22px CN'; g.fillStyle = '#ffe14d'; g.fillText('POIs', W + 40, y); y += 12;
    g.font = '15px CN';
    pois.forEach((p, i) => { y += 26; g.fillStyle = p.color; g.fillRect(W + 40, y - 12, 14, 14); g.fillStyle = '#fff'; g.fillText(p.name, W + 62, y); y += 18; g.fillStyle = '#c8b8d8'; const s = p.blurb.length > 38 ? p.blurb.slice(0, 38) + '...' : p.blurb; g.fillText(s, W + 62, y); });
    y += 40; g.fillStyle = '#ffe14d'; g.font = '20px CN'; g.fillText('size', W + 40, y); g.font = '15px CN'; g.fillStyle = '#fff';
    for (const s of ['land ~560 x 460 m', 'peak 62 m (Dead Air)', 'roads 12-14 m (mechs pass)', 'shallows <1.5 m: walk (60%)', 'deep water: into the sea', 'yellow rings: mech drop pads']) { y += 22; g.fillText(s, W + 40, y); }
    // the silhouette: its own canvas, saved separately
    const c2 = document.createElement('canvas'); c2.width = W; c2.height = H; c2.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(sil), W, H), 0, 0);
    window.__sil = c2.toDataURL('image/png');
  }, { px: Array.from(rgb), sil: Array.from(sil), W, H, X0, Z0, pois: PLAN.pois, islets: PLAN.islets });
  await pg.screenshot({ path: path.join(out, 'layout.png') });
  const silUrl = await pg.evaluate(() => window.__sil);
  fs.writeFileSync(path.join(out, 'silhouette.png'), Buffer.from(silUrl.split(',')[1], 'base64'));
  await b.close();
  console.log('wrote', out);
})();
