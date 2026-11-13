// node --test tests/texkit_repro.test.mjs : the arch texture kit regenerates byte for byte. texkit.py + brtex.py are run
// into a temp dir and every committed png in public/models/arch/kit (and kit.json) must come out identical, so nobody
// hand-appends a texture again. needs python3 + numpy + Pillow; skips with a note when they're missing
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readdirSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const KIT = join(ROOT, 'public', 'models', 'arch', 'kit');
const ARCH = join(ROOT, 'tools', 'blender', 'arch');
const py = spawnSync('python3', ['-c', 'import numpy, PIL'], { encoding: 'utf8' });
const skip = py.status !== 0 ? 'python3 with numpy + Pillow not found (pip install numpy pillow), texkit repro not checked' : false;

test('texkit.py + brtex.py regenerate the committed kit byte for byte', { skip, timeout: 300000 }, () => {
  const out = mkdtempSync(join(tmpdir(), 'texkit-'));
  try {
    for (const s of ['texkit.py', 'brtex.py']) {
      const r = spawnSync('python3', [join(ARCH, s), '--out', out], { encoding: 'utf8', timeout: 240000 });
      assert.equal(r.status, 0, `${s} failed: ${r.stderr}`);
    }
    const kept = readdirSync(KIT).filter((f) => f.endsWith('.png') || f === 'kit.json');
    assert.ok(kept.length > 20, 'no committed kit found');
    const bad = [];
    for (const f of kept) {
      const p = join(out, f);
      if (!existsSync(p)) bad.push(`${f}: not made by texkit.py / brtex.py (hand-added?)`);
      else if (!readFileSync(p).equals(readFileSync(join(KIT, f)))) bad.push(`${f}: regenerates differently`);
    }
    for (const f of readdirSync(out)) if (!kept.includes(f)) bad.push(`${f}: generated but not committed`);
    assert.deepEqual(bad, [], 'kit drifted from the generator; put new textures in texkit.py with a PIN seed and regenerate');
  } finally { rmSync(out, { recursive: true, force: true }); }
});
