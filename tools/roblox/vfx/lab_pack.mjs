// Packs ModuleScripts for a VFX capture Play test into one .rbxm (Rojo), named as given, in a Folder "FxLabPack":
// the effects module under test, the previous one made freezable, and FxLab.luau. Upload it as a Model (Open Cloud),
// then in the Play test's Server: InsertService:LoadAsset(id) and parent the folder to ReplicatedStorage, so the Client
// can clone and require the modules (roblox/docs/VFX-PIPELINE.md, step 3). Nothing in the place changes.
//
//   node tools/roblox/vfx/lab_pack.mjs <out.rbxm> Fx=roblox/src/client/Fx.luau FxOld=<file> FxLab=tools/roblox/vfx/FxLab.luau
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const [out, ...pairs] = process.argv.slice(2);
if (!out || !pairs.length) { console.error('usage: lab_pack.mjs <out.rbxm> Name=file.luau ...'); process.exit(1); }
const tree = { $className: 'Folder' };
for (const p of pairs) {
  const [name, file] = p.split('=');
  tree[name] = { $path: path.resolve(file).replace(/\\/g, '/') };
}
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'jfvfxpack-'));
const proj = path.join(dir, 'default.project.json');
fs.writeFileSync(proj, JSON.stringify({ name: 'FxLabPack', tree }, null, 1));
const rojo = process.env.ROJO || path.join(os.homedir(), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe');
execFileSync(rojo, ['build', proj, '-o', path.resolve(out)], { stdio: 'inherit' });
fs.rmSync(dir, { recursive: true, force: true });
console.log('packed', pairs.length, 'modules into', out, fs.statSync(out).size, 'bytes');
