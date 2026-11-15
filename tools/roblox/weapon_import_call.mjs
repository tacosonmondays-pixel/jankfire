// prints the Luau to run in Studio (execute_luau, Edit) that brings uploaded weapon models into the place with
// PolishBackup.WeaponImport: each gun's asset id (roblox/assets/weapons/assets.json) + the bounds the exporter measured
// (export_report.json), which the importer checks the facing against, + every piece's paint code (the report's paint:
// weapon_paint.py, "calm" unless the exporter was told --paint web). nothing is turned or painted by hand.
// run: node tools/roblox/weapon_import_call.mjs [--paint] [id ...]   (no ids = every gun in assets.json that was exported turned)
//   --paint   print the call that only REPAINTS the templates already in the place (W.paint): no asset is loaded
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'roblox', 'assets', 'weapons');
const ids = JSON.parse(fs.readFileSync(path.join(DIR, 'assets.json'), 'utf8'));
const rep = JSON.parse(fs.readFileSync(path.join(DIR, 'export_report.json'), 'utf8'));
const only = process.argv.includes('--paint');
const want = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const v = (a) => `Vector3.new(${a.join(', ')})`;
const rows = [];
let name = null;
for (const [id, asset] of Object.entries(ids)) {
  if (id === 'note' || (want.length && !want.includes(id))) continue;
  const r = rep['w_' + id];
  if (!r || !r.turned) { console.error(`skipped ${id}: not exported with the current export_weapons.py`); continue; }
  if (!r.paint) { console.error(`skipped ${id}: the report has no paint for it (py tools/roblox/weapon_paint.py <report>)`); continue; }
  if (name && name !== r.paint) { console.error(`the report mixes paints (${name}, ${r.paint}): repaint it first`); process.exit(1); }
  name = r.paint;
  const paint = `{ ${r.pieces.map((p) => `["${p.name}"] = "${p.paint}"`).join(', ')} }`;
  rows.push(only ? `\t${id} = ${paint},` : `\t${id} = { id = ${asset}, lo = ${v(r.lo)}, hi = ${v(r.hi)}, paint = ${paint} },`);
}
console.log(`local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())\nreturn W.${only ? 'paint' : 'run'}({\n${rows.join('\n')}\n}, { name = "${name}" })`);
