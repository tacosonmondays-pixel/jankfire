// one command for the Roblox place: convert the map, build the place with Rojo (binary .rbxl + XML .rbxlx), run the
// tests. needs rojo (and lune for the tests: `cargo install rojo lune`, or from their GitHub releases).
// run: node tools/roblox/build.mjs [--no-test]
import { execFileSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.join(HERE, '..', '..'), RB = path.join(ROOT, 'roblox');
const tool = (n) => { for (const d of [...(process.env.PATH || '').split(path.delimiter), path.join(os.homedir(), '.cargo', 'bin'), path.join(os.homedir(), '.aftman', 'bin'), path.join(os.homedir(), '.rokit', 'bin')]) { for (const e of ['', '.exe']) { const f = path.join(d, n + e); if (fs.existsSync(f)) return f; } } return null; };
const run = (cmd, args, cwd = ROOT) => execFileSync(cmd, args, { cwd, stdio: 'inherit' });

run(process.execPath, [path.join(HERE, 'convert.mjs'), 'rooftop']);
run(process.execPath, [path.join(HERE, 'convert.mjs'), 'range', '20000,0,0']); // step 3: Training (the Range), 20000 studs east
// step 2: a Sound per rendered .ogg in ReplicatedStorage.JankfireSounds (SoundId empty until the owner uploads it;
// the File attribute says which file goes in it). list from tools/roblox/render_sounds.cjs
{
  const list = JSON.parse(fs.readFileSync(path.join(RB, 'assets', 'sounds', 'list.json'), 'utf8'));
  const kids = list.map((s) => ({ Name: s.name, ClassName: 'Sound', Properties: { Volume: { Float32: s.vol }, Attributes: { Attributes: { File: { String: `roblox/assets/sounds/${s.name}.ogg` }, What: { String: s.what } } } } }));
  fs.mkdirSync(path.join(RB, 'build'), { recursive: true });
  fs.writeFileSync(path.join(RB, 'build', 'Sounds.model.json'), JSON.stringify({ ClassName: 'Folder', Children: kids }, null, 1));
}
const rojo = tool('rojo');
if (!rojo) { console.log('no rojo: install it (cargo install rojo) to build the place'); process.exit(1); }
run(rojo, ['build', 'place.project.json', '-o', 'build/JANKFIRE-Rooftop.rbxl'], RB);
run(rojo, ['build', 'place.project.json', '-o', 'build/JANKFIRE-Rooftop.rbxlx'], RB);
if (process.argv.includes('--no-test')) process.exit(0);
run(process.execPath, [path.join(HERE, 'test-convert.mjs'), 'rooftop']);
run(process.execPath, [path.join(HERE, 'test-convert.mjs'), 'range']);
const lune = tool('lune');
if (lune) run(lune, ['run', 'tests/run'], RB); else console.log('(no lune: skipped the Luau tests)');
