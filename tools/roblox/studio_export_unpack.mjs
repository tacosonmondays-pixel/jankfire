// Turns what ServerStorage.PolishBackup.StudioExport (roblox/studio-tools/StudioExport.luau) returned through the
// Roblox Studio MCP into real files under roblox/.
// Why this shape: Studio can't write files and its HTTP allowlist blocks localhost, so the place leaves Studio as the
// return value of execute_luau. The MCP cuts a result at 100,000 characters and saves big results as text files, so
// the export is one long ASCII bundle handed over in slices ("JFSLICE0003/0041:...").
//   node tools/roblox/studio_export_unpack.mjs <folder with the MCP result files | the files themselves>
// Run from the repo root. Slices may come in any order; extra files are ignored.
import fs from 'node:fs';
import path from 'node:path';

const base = path.resolve('roblox');
const inputs = [];
for (const a of process.argv.slice(2)) {
  if (fs.statSync(a).isDirectory()) for (const f of fs.readdirSync(a)) inputs.push(path.join(a, f)); else inputs.push(a);
}
const slices = new Map();
let total = 0;
for (const f of inputs) {
  if (!f.endsWith('.txt')) continue;
  const fd = fs.openSync(f, 'r'); const hb = Buffer.alloc(17); fs.readSync(fd, hb, 0, 17, 0); fs.closeSync(fd);
  const m = /^JFSLICE(\d{4})\/(\d{4}):$/.exec(hb.toString('latin1'));
  if (!m) continue;
  const i = Number(m[1]); total = Number(m[2]);
  const prev = slices.get(i);
  if (!prev || fs.statSync(f).mtimeMs > prev.t) slices.set(i, { t: fs.statSync(f).mtimeMs, f }); // newest export wins
}
if (!total) { console.error('no JFSLICE files found'); process.exit(1); }
const missing = [];
for (let i = 1; i <= total; i++) if (!slices.has(i)) missing.push(i);
if (missing.length) { console.error('missing slices: ' + missing.join(', ')); process.exit(1); }
let bundle = '';
for (let i = 1; i <= total; i++) bundle += fs.readFileSync(slices.get(i).f, 'latin1').slice(17);
const end = bundle.indexOf('JFEND');
if (end < 0) { console.error('no end marker: the last slice is missing or cut'); process.exit(1); }
const items = JSON.parse(bundle.slice(0, end));
let nText = 0, nBin = 0, bytes = 0;
for (const it of items) {
  const dest = path.resolve(base, it.path);
  if (!dest.startsWith(base + path.sep)) throw new Error('path escapes roblox/: ' + it.path);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  const buf = Buffer.from(it.text64 ?? it.bin64, 'base64');
  fs.writeFileSync(dest, buf); bytes += buf.length;
  if (it.text64 !== undefined) nText++; else nBin++;
}
console.log(`${total} slices -> ${nText} text files, ${nBin} model files, ${bytes} bytes`);
