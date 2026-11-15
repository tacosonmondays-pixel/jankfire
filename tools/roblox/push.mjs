// packs script files into one Roblox model file (.rbxm) so a batch of code changes can go INTO Studio in one go:
// upload the .rbxm as a Model (Open Cloud, like the weapon models), LoadAsset it in Studio, and copy each script's
// Source onto the script of the same name (the Luau for that is printed at the end). use it for new or generated
// modules and for edits too big to type through the Studio MCP's multi_edit. the files must be Studio's current
// source plus your change: export first (studio_export_unpack.mjs) or compare checksums, or you overwrite newer work.
// run: node tools/roblox/push.mjs <out.rbxm> roblox/src/client/Arsenal.client.luau roblox/src/shared/Reloads.luau ...
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const [out, ...files] = process.argv.slice(2);
if (!out || !files.length) { console.error('usage: node tools/roblox/push.mjs <out.rbxm> <roblox/src/.../File.luau> ...'); process.exit(1); }
const tree = { $className: 'Folder' };
for (const f of files) {
  const abs = path.resolve(ROOT, f);
  // (roblox/studio-tools/X.luau goes to ServerStorage.PolishBackup: the edit-time helpers and the paint book)
  const m = /roblox[\\/]src[\\/](shared|client|server)[\\/](.+?)(\.client|\.server)?\.luau$/.exec(abs)
    || /roblox[\\/]studio-(tools)[\\/](.+?)\.luau$/.exec(abs);
  if (!m) throw new Error('not a roblox/src or roblox/studio-tools script: ' + f);
  tree[m[1]] ??= { $className: 'Folder' };
  tree[m[1]][m[2]] = { $path: abs.replace(/\\/g, '/') };
}
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'jankpush-'));
const proj = path.join(dir, 'default.project.json');
fs.writeFileSync(proj, JSON.stringify({ name: 'JankPush', tree }, null, 1));
const rojo = process.env.ROJO || path.join(os.homedir(), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe');
execFileSync(rojo, ['build', proj, '-o', path.resolve(out)], { stdio: 'inherit' });
console.log('packed', files.length, 'scripts into', out, fs.statSync(out).size, 'bytes');
console.log(`-- in Studio (Edit), after uploading it as a Model:
local id = 0 -- <- the uploaded model's asset id
local c = game:GetService("InsertService"):LoadAsset(id)
local dest = { shared = game.ReplicatedStorage.Jankfire, client = game.StarterPlayer.StarterPlayerScripts.Jankfire, server = game.ServerScriptService.Jankfire, tools = game.ServerStorage.PolishBackup }
local out = {}
for _, folder in c:FindFirstChildOfClass("Folder"):GetChildren() do
	for _, s in folder:GetChildren() do
		local t = dest[folder.Name]:FindFirstChild(s.Name)
		if t then
			if t.Source ~= s.Source then t.Source = s.Source; table.insert(out, "updated " .. folder.Name .. "/" .. s.Name) end
		else s.Parent = dest[folder.Name]; table.insert(out, "added " .. folder.Name .. "/" .. s.Name) end
	end
end
c:Destroy()
return table.concat(out, "\\n")`);
