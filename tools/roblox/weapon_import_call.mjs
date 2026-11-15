// prints the Luau to run in Studio (execute_luau, Edit) that brings uploaded weapon models into the place with
// PolishBackup.WeaponImport: each gun's asset id (roblox/assets/weapons/assets.json) + the bounds the exporter measured
// (export_report.json), which the importer checks the facing against. nothing is turned or painted by hand.
// run: node tools/roblox/weapon_import_call.mjs [id ...]     (no ids = every gun in assets.json that was exported turned)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'roblox', 'assets', 'weapons');
const ids = JSON.parse(fs.readFileSync(path.join(DIR, 'assets.json'), 'utf8'));
const rep = JSON.parse(fs.readFileSync(path.join(DIR, 'export_report.json'), 'utf8'));
const want = process.argv.slice(2);
const v = (a) => `Vector3.new(${a.join(', ')})`;
const rows = [];
for (const [id, asset] of Object.entries(ids)) {
  if (id === 'note' || (want.length && !want.includes(id))) continue;
  const r = rep['w_' + id];
  if (!r || !r.turned) { console.error(`skipped ${id}: not exported with the current export_weapons.py`); continue; }
  rows.push(`\t${id} = { id = ${asset}, lo = ${v(r.lo)}, hi = ${v(r.hi)} },`);
}
console.log(`local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())\nreturn W.run({\n${rows.join('\n')}\n})`);
