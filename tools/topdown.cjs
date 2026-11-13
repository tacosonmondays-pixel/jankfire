// The big map's top-down pictures for the royale maps (Jankburg, Battle Island): renders each map in the real game
// (Too HD) from straight above with an orthographic camera, writes the POI names on in the comic style and saves
// public/maps/topdown/<map>.jpg + <map>.json (the world rect the picture covers). The big map (fullmap.js) draws it
// instead of the painted boxes, with zoom and pan. Re-run after a royale map changes:
//   PORT=3000 node server.js &   then   node tools/topdown.cjs [url] [map,map] [size px]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const url = process.argv[2] || 'http://localhost:3000/';
const only = process.argv[3] ? process.argv[3].split(',') : ['jankburg', 'battleisland'];
const SIZE = Number(process.argv[4]) || 2048;
const out = path.join(__dirname, '..', 'public', 'maps', 'topdown');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 600 } });
  pg.setDefaultTimeout(300000);
  pg.on('pageerror', (e) => console.log('page error:', e.message));
  await pg.addInitScript(() => { localStorage.setItem('jf_giftseen_all', '1'); localStorage.setItem('jankfire', JSON.stringify({ jank: 3, fov: 75, name: 'topdown', killcam: false })); });
  await pg.goto(url + (url.includes('?') ? '&' : '?') + 'wip=1'); await sleep(2500);
  for (const id of only) {
    // load the map and park the game's own camera high over the middle, looking down: every chunk counts as in view
    await pg.evaluate(async (id) => {
      const { G } = await import('/js/ctx.js'); const { loadMap } = await import('/js/world.js'); const { MAPS } = await import('/shared/map.js');
      await import('/shared/royale.js');
      const m = MAPS[id], [cx, , ] = m.royale.zone0, cz = m.royale.zone0[1];
      G.cfg.map = id; loadMap(id);
      document.getElementById('menu').classList.add('hidden');
      G.thumbCam = [cx, 700, cz, 0, -1.5];
    }, id);
    await sleep(9000);
    const res = await pg.evaluate(async ({ id, S }) => {
      const THREE = await import('three');
      const { G } = await import('/js/ctx.js'); const { MAPS } = await import('/shared/map.js');
      const m = MAPS[id], [cx, cz, r0] = m.royale.zone0, R = r0 * 1.05; // the same rect the big map uses (minimap.js mapExtent)
      const ext = [cx - R, cz - R, cx + R, cz + R];
      const cam = new THREE.OrthographicCamera(-R, R, R, -R, 1, 3000);
      cam.position.set(cx, 1200, cz); cam.up.set(0, 0, -1); cam.lookAt(cx, 0, cz); cam.updateMatrixWorld(); // north up, east right
      // out of the picture: fog, the sky dome, clouds, weather, players, the blimp / zone, pings
      const hidden = [], fog = G.scene.fog, bg = G.scene.background;
      G.scene.fog = null;
      G.scene.traverse((o) => {
        if (!o.visible) return;
        const big = o.isMesh && o.geometry && (o.geometry.boundingSphere || (o.geometry.computeBoundingSphere(), o.geometry.boundingSphere));
        const sky = o.isMesh && o.material && (o.material.side === THREE.BackSide || (big && big.radius > 1400 && !o.material.map && o.material.depthWrite === false));
        if (/^(br_|fm_|sky|cloud|rain|wx)/i.test(o.name || '') || sky || o.isSprite || o.isPoints) { o.visible = false; hidden.push(o); }
      });
      for (const r of G.remotes.values()) if (r.ch && r.ch.root.visible) { r.ch.root.visible = false; hidden.push(r.ch.root); }
      if (G.vmScene) { G.vmScene.visible = false; hidden.push(G.vmScene); }
      // the sun's shadows over the whole map for this one picture (in game they only cover the ground round you)
      const sun = []; G.scene.traverse((o) => { if (o.isDirectionalLight && o.castShadow) sun.push(o); });
      const shadowWas = sun.map((l) => { const c = l.shadow.camera; return { l, p: l.position.clone(), t: l.target.position.clone(), c: [c.left, c.right, c.top, c.bottom, c.near, c.far], ms: l.shadow.mapSize.clone() }; });
      for (const l of sun) {
        const dir = l.position.clone().sub(l.target.position).normalize(), c = l.shadow.camera;
        l.target.position.set(cx, 0, cz); l.position.set(cx + dir.x * 900, dir.y * 900, cz + dir.z * 900);
        l.target.updateMatrixWorld(); l.updateMatrixWorld();
        Object.assign(c, { left: -R * 1.5, right: R * 1.5, top: R * 1.5, bottom: -R * 1.5, near: 1, far: 2400 }); c.updateProjectionMatrix();
        l.shadow.mapSize.set(4096, 4096); if (l.shadow.map) { l.shadow.map.dispose(); l.shadow.map = null; }
      }
      const rd = G.renderer, old = rd.getSize(new THREE.Vector2()), pr = rd.getPixelRatio();
      rd.setPixelRatio(1); rd.setSize(S, S, false);
      G.scene.background = new THREE.Color(m.sea ? 0x1f8fb8 : 0x2a1a10);
      rd.render(G.scene, cam);
      const c = document.createElement('canvas'); c.width = c.height = S;
      const x = c.getContext('2d');
      x.drawImage(rd.domElement, 0, 0, S, S);
      rd.setPixelRatio(pr); rd.setSize(old.x, old.y, false);
      for (const s of shadowWas) { const c = s.l.shadow.camera; s.l.position.copy(s.p); s.l.target.position.copy(s.t); [c.left, c.right, c.top, c.bottom, c.near, c.far] = s.c; c.updateProjectionMatrix(); s.l.shadow.mapSize.copy(s.ms); if (s.l.shadow.map) { s.l.shadow.map.dispose(); s.l.shadow.map = null; } }
      G.scene.fog = fog; G.scene.background = bg; for (const o of hidden) o.visible = true;
      // the POI names: big comic stickers (the colour of the POI, a thick black edge, a hard pink shadow)
      await document.fonts.load(`bold ${Math.round(S / 40)}px "Comic Neue"`);
      const k = S / (2 * R), at = (wx, wz) => [(wx - ext[0]) * k, (wz - ext[1]) * k];
      for (const p of m.royale.pois || []) {
        const c0 = p.c ? [p.c[0] + (p.lab ? p.lab[0] : 0), p.c[1] + (p.lab ? p.lab[1] : 0)] : [(p.rect[0] + p.rect[2]) / 2, (p.rect[1] + p.rect[3]) / 2];
        const t = p.name.toUpperCase(), rw = (p.rect[2] - p.rect[0]) * k;
        x.font = `bold 100px "Comic Neue", sans-serif`;
        const fs = Math.round(Math.min(S / 34, Math.max(S / 70, rw * 0.94 / (x.measureText(t).width / 100)))); // fits its own district (Jankburg's sit side by side)
        x.font = `bold ${fs}px "Comic Neue", sans-serif`; x.textAlign = 'center'; x.textBaseline = 'middle';
        const half = x.measureText(t).width / 2 + fs * 0.3, [px0, py0] = at(c0[0], c0[1]);
        const px = Math.max(half, Math.min(S - half, px0)), py = Math.max(fs, Math.min(S - fs, py0)); // never off the picture's edge
        x.save(); x.translate(px, py); x.rotate(((t.length % 5) - 2) * 0.012);
        x.lineJoin = 'round';
        x.lineWidth = fs * 0.32; x.strokeStyle = '#ff00dc'; x.strokeText(t, fs * 0.09, fs * 0.09); // the hard shadow
        x.strokeStyle = '#000'; x.strokeText(t, 0, 0);
        x.fillStyle = p.color || '#ffe14d'; x.fillText(t, 0, 0);
        x.restore();
      }
      return { ext: ext.map((v) => Math.round(v * 100) / 100), jpg: c.toDataURL('image/jpeg', 0.86), hidden: hidden.length };
    }, { id, S: SIZE });
    fs.writeFileSync(path.join(out, id + '.jpg'), Buffer.from(res.jpg.split(',')[1], 'base64'));
    fs.writeFileSync(path.join(out, id + '.json'), JSON.stringify({ map: id, ext: res.ext, size: SIZE, names: true }) + '\n');
    console.log('topdown', id, res.ext.join(','), 'hid', res.hidden, Math.round(fs.statSync(path.join(out, id + '.jpg')).size / 1024) + ' KB');
  }
  await b.close();
})();
