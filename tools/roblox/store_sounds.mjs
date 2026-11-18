// the game's sounds from Roblox's licensed library (16 Nov 2026): the owner didn't want code-generated sounds, so
// every name in ReplicatedStorage.JankfireSounds now plays a recorded effect from the "Pro Sound Effects" library
// (Roblox's licensed set, free for any experience) or Roblox's own UI pack. no user uploads, nothing ripped from games.
// picks live in roblox/assets/sounds/store.json: name -> takes [{ id, title, region: [start, end] | null, L }]. L is
// the loudness Studio measured (an AudioAnalyzer: loudest 0.4 s of RMS, dB). each Sound's Volume puts that loudness at
// its category's level: the target per name is the one render_sfx.mjs used (roblox/assets/sounds/v2/list.json,
// "target", LUFS) moved onto the analyzer's scale by store.json's "offset" (measured on the v2 renders).
// a region plays only that slice of a clip (one shot out of a sequence, one footstep out of a walk).
// store.loop[name] = true makes the Sound Looped (a region loops just that slice); store.roll[name] = [min, max] sets
// its RollMin / RollMax attributes (how far Sfx lets a copy out in the world carry, studs) and the Sound's own
// InverseTapered roll-off, for a caller that clones it onto an Attachment itself (the loops).
// prints the Luau to paste into Studio (Edit): node tools/roblox/store_sounds.mjs [only=skin_,zone_] > swap.luau
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const store = JSON.parse(fs.readFileSync(path.join(ROOT, 'roblox/assets/sounds/store.json'), 'utf8'));
const list = JSON.parse(fs.readFileSync(path.join(ROOT, 'roblox/assets/sounds/v2/list.json'), 'utf8'));
const off = store.offset ?? 0;
const rows = [];
// only=skin_,zone_ : just the names starting with those (leave the rest of the library as it is in Studio)
const onlyArg = process.argv.find((x) => x.startsWith('only='));
const ONLY = onlyArg ? onlyArg.slice(5).split(',') : null;
for (const [name, takes] of Object.entries(store.sounds)) {
  if (ONLY && !ONLY.some((p) => name.startsWith(p))) continue;
  // (store.targets: names take 2 never had, e.g. skin_* and zone_*; a recorded distance take "gun_ar@179" levels like
  // its close take "gun_ar" unless it has its own: Sfx's distance roll-off does the fading)
  const near = name.includes('@') ? name.slice(0, name.indexOf('@')) : null;
  const base = list[name]?.target ?? store.targets?.[name] ?? (near && (list[near]?.target ?? store.targets?.[near]));
  if (base == null) throw new Error('no target for ' + name);
  if (!takes.length) continue;
  const L = takes.reduce((a, t) => a + t.L, 0) / takes.length;
  const target = base + off + (store.trim?.[name] ?? 0);
  const vol = store.vol?.[name] ?? Math.max(0.05, Math.min(3, Math.pow(10, (target - L) / 20))); // (store.vol: set by ear-substitute after Play)
  const t = takes.map((k) => `{${k.id},${k.region ? k.region[0] : -1},${k.region ? k.region[1] : -1}}`).join(',');
  const j = store.jitter?.[name];
  const lp = store.loop?.[name] === true;
  const rl = store.roll?.[name];
  const extra = j != null || lp || rl ? `,${j ?? 'nil'},${lp ? 'true' : 'nil'}${rl ? `,${rl[0]},${rl[1]}` : ''}` : '';
  rows.push(`{"${name}",${Math.round(vol * 100) / 100},{${t}}${extra}}`);
}
console.log(`-- JankfireSounds from the licensed library (tools/roblox/store_sounds.mjs, roblox/assets/sounds/store.json)
local lib = game.ReplicatedStorage.JankfireSounds
local D = {
${rows.join(',\n')}
}
local function apply(s, take)
	s.SoundId = "rbxassetid://" .. string.format("%d", take[1])
	if take[2] >= 0 then
		s.PlaybackRegionsEnabled = true; s.PlaybackRegion = NumberRange.new(take[2], take[3])
	else
		s.PlaybackRegionsEnabled = false; s.PlaybackRegion = NumberRange.new(0, 60000)
	end
end
local n, takes = 0, 0
for _, d in ipairs(D) do
	local name, vol, list, jit, loop, rmin, rmax = d[1], d[2], d[3], d[4], d[5], d[6], d[7]
	local s = lib:FindFirstChild(name)
	if not s then s = Instance.new("Sound"); s.Name = name; s.Parent = lib end
	if s:GetAttribute("SoundIdV2") == nil then s:SetAttribute("SoundIdV2", s.SoundId); s:SetAttribute("VolumeV2", s.Volume) end
	s.Volume = vol
	if jit then s:SetAttribute("Jitter", jit) end
	if loop then s.Looped = true end
	if rmin then
		s:SetAttribute("RollMin", rmin); s:SetAttribute("RollMax", rmax)
		s.RollOffMode = Enum.RollOffMode.InverseTapered; s.RollOffMinDistance = rmin; s.RollOffMaxDistance = rmax
	end
	apply(s, list[1])
	for _, c in ipairs(lib:GetChildren()) do if string.match(c.Name, "^(.-)#%d+$") == name then c:Destroy() end end
	for k = 2, #list do
		local t = s:Clone(); t.Name = name .. "#" .. k
		for _, a in ipairs({ "SoundIdV1", "VolumeV1", "SoundIdV2", "VolumeV2" }) do t:SetAttribute(a, nil) end
		apply(t, list[k]); t.Parent = lib; takes += 1
	end
	n += 1
end
return n .. " sounds, " .. takes .. " extra takes; children " .. #lib:GetChildren()`);
