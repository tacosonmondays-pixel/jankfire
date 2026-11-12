// the near plane while swimming: open sea has no box under it, and that once read as a 600 m drop (near 2.4 m, the
// camera went glitchy in water). zfight.js's browser imports are pointed at the repo in a temp copy
import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
test('swimming keeps the 10 cm near plane; high up it still grows', async () => {
  const M = await import(path.join(root, 'shared/map.js'));
  let src = fs.readFileSync(path.join(root, 'public/js/zfight.js'), 'utf8');
  for (const f of ['map', 'physics', 'overlay']) src = src.replace(`'/shared/${f}.js'`, `'${path.join(root, 'shared', f + '.js')}'`);
  const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'zf-')), 'zfight.mjs'); fs.writeFileSync(tmp, src);
  const Z = await import(tmp);
  const cam = { position: { x: 0, y: 0, z: 0 }, near: 0.1, updateProjectionMatrix() {} };
  const at = (x, y, z) => { Object.assign(cam.position, { x, y, z }); for (let i = 0; i < 6; i++) Z.depthNear(cam); return cam.near; };
  for (const id of ['islands', 'platform']) {
    M.setMap(id); const sea = M.MAPS[id].seaY;
    for (let x = -140; x <= 140; x += 20) for (let z = -140; z <= 140; z += 20) {
      assert.ok(at(x, sea + 0.6, z) <= 0.11, `${id}: near ${cam.near} swimming at ${x},${z}`);
      assert.ok(at(x, sea - 0.5, z) <= 0.11, `${id}: near ${cam.near} under water at ${x},${z}`);
    }
    assert.ok(at(0, sea + 220, 0) > 1, `${id}: near still grows high up`);
  }
});
