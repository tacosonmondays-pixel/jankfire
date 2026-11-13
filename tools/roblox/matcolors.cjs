// pulls every map material's look out of the web game's renderer (public/js/world.js builds them as canvas textures):
// the texture's average colour times the material's colour, plus its glow. writes tools/roblox/matcolors.json, which
// the place builder reads. run: node tools/roblox/matcolors.cjs [port]   (starts its own server)
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const { chromium } = require('playwright');
const ROOT = path.join(__dirname, '..', '..'), PORT = Number(process.argv[2]) || 3917;
(async () => {
  const srv = spawn('node', ['server.js'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT) }, stdio: 'ignore' });
  for (let i = 0; i < 120; i++) { try { await fetch(`http://localhost:${PORT}/`); break; } catch { await new Promise((r) => setTimeout(r, 500)); } }
  const br = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  try {
    const pg = await br.newPage();
    await pg.goto(`http://localhost:${PORT}/`, { waitUntil: 'load' });
    await pg.waitForTimeout(6000);
    const out = await pg.evaluate(async () => {
      const w = await import('/js/world.js');
      let M = w.mapMats();
      if (!M) { w.loadMap('rooftop'); M = w.mapMats(); }
      const res = {};
      const avg = (img) => {
        if (!img || !img.width) return null;
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
        const g = c.getContext('2d'); g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, c.width, c.height).data; let r = 0, gg = 0, b = 0, a = 0, n = 0;
        for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; b += d[i + 2]; a += d[i + 3]; n++; }
        return [r / n / 255, gg / n / 255, b / n / 255, a / n / 255];
      };
      for (const [k, v] of Object.entries(M)) {
        const m = v && (v.mat || v);
        if (!m || !m.color) continue;
        const t = m.map && m.map.image ? avg(m.map.image) : null;
        const c = m.color.clone(); // (linear in three; convert back to sRGB for Roblox)
        const lin = [c.r, c.g, c.b].map((x) => (x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055));
        const col = t ? [t[0] * lin[0], t[1] * lin[1], t[2] * lin[2]] : lin;
        const e = m.emissive ? [m.emissive.r, m.emissive.g, m.emissive.b] : [0, 0, 0];
        const em = m.emissiveMap && m.emissiveMap.image ? avg(m.emissiveMap.image) : null;
        res[k] = { c: col.map((x) => +x.toFixed(3)), e: e.map((x) => +x.toFixed(3)), em: !!em, op: m.transparent ? +(m.opacity ?? 1).toFixed(2) : 1, alphaTex: t ? +t[3].toFixed(2) : 1 };
      }
      return res;
    });
    fs.writeFileSync(path.join(__dirname, 'matcolors.json'), JSON.stringify(out, null, 0).replace(/\},"/g, '},\n"') + '\n');
    console.log('materials:', Object.keys(out).length);
  } finally { await br.close(); srv.kill(); }
})();
