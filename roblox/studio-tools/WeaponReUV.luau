--!nocheck
-- edit-time tool (27 Nov 2026): the wrap UV standard changed (tools/roblox/gun_uvs.py: 0.6 m a tile, conformal, seams
-- on hidden edges), so every wrappable kit piece gets its new mesh IN PLACE: tools/roblox/reuv_glb.py re-UV'd the exact
-- uploaded files (same pieces, names, vertices), they were uploaded again, and this module puts each new mesh on the
-- live part with MeshPart:ApplyMesh. Only parts marked WrapUV change; every attribute, child (SurfaceAppearances of
-- baked or Tripo pieces, hat seats, NoWrap parts) and paint stays. A part whose mesh size doesn't match is left alone
-- and reported.
-- The gadgets too (tools/roblox/reuv_items.py): ReplicatedStorage.JankfireItems x_<item> and the gadget skins in
-- JankfireSkins (Item = true), keys "x_<item>" and "<item>_<skin>" in the pack.
-- THE OLD UVs ARE A SWITCH: R.backup() parks the current sets once in ServerStorage.PolishBackup.UV1 (the kit set,
-- the live templates, the skins, the Shredder tools, the gadgets); R.switch("uv1") puts them back, R.switch("uv2") the
-- new ones (parked by R.park2() after the roll-out).
-- usage (Edit, execute_luau):
--   local R = require(game.ServerStorage.PolishBackup.WeaponReUV:Clone())
--   R.backup()
--   R.apply({ ar = 123, ["ar@ar_bullpup"] = 456 })   -- book key -> the new upload's asset id
local R = {}
local RS = game:GetService("ReplicatedStorage")
local IS = game:GetService("InsertService")

local function pb() return game.ServerStorage.PolishBackup end

local function strip(name: string): string
	-- an upload's piece is "<node>__<material>__<look code>" (rbxglb.look_code); the templates lost the code on import
	-- (and Blender's ".001" when one pack holds two pieces of one name)
	name = string.gsub(name, "%.%d+$", "")
	local base = string.match(name, "^(.-)__[pnmsgwr]%x%x%x%x%x%x%x*%+?$")
	return base or name
end

local SETS = {
	{ "kit", function() return pb().WeaponSets.kit end },
	{ "weapons", function() return RS.JankfireWeapons end },
	{ "skins", function() return RS:FindFirstChild("JankfireSkins") end },
	{ "tools", function() return RS:FindFirstChild("JankfireTools") end },
	{ "items", function() return RS:FindFirstChild("JankfireItems") end },
}

function R.backup(force: boolean?)
	local b = pb():FindFirstChild("UV1")
	if b and not force then return "UV1 backup already there (" .. #b:GetChildren() .. " sets)" end
	if b then b:Destroy() end
	b = Instance.new("Folder"); b.Name = "UV1"
	local out = {}
	for _, s in SETS do
		local f = s[2]()
		if f then
			local c = f:Clone(); c.Name = s[1]; c.Parent = b
			table.insert(out, s[1] .. " " .. #c:GetChildren())
		end
	end
	b.Parent = pb()
	return "UV1 backup: " .. table.concat(out, ", ")
end

-- the models a book key lives in: the kit set's w_<key>, the live template if it is that kit model (or wears that
-- skin), the skin's JankfireSkins model
local function targets(key: string)
	local out = {}
	-- a gadget (x_<item>) or a gadget skin (<item>_<skin>, Item = true)
	local items, sk0 = RS:FindFirstChild("JankfireItems"), RS:FindFirstChild("JankfireSkins")
	if string.sub(key, 1, 2) == "x_" then
		local m = items and items:FindFirstChild(key)
		if m then table.insert(out, m) end
		return out
	end
	local gs = sk0 and sk0:FindFirstChild(key)
	if gs and gs:GetAttribute("Item") then table.insert(out, gs); return out end
	local kit = pb().WeaponSets.kit:FindFirstChild("w_" .. key)
	if kit then table.insert(out, kit) end
	local wid, skin = string.match(key, "^([%w_]+)@([%w_]+)$")
	local lib = RS.JankfireWeapons
	if not wid then
		local live = lib:FindFirstChild("w_" .. key)
		if live and live:GetAttribute("Set") == "kit" and not live:GetAttribute("Skin") then table.insert(out, live) end
	else
		local live = lib:FindFirstChild("w_" .. wid)
		if live and live:GetAttribute("Skin") == skin then table.insert(out, live) end
		local sk = RS:FindFirstChild("JankfireSkins")
		local m = sk and sk:FindFirstChild(skin)
		if m and m:GetAttribute("Weapon") == wid then table.insert(out, m) end
	end
	-- the Shredder and its skins are Tools (JankfireTools.Shredder, Shredder@<skin>; the kit set keeps them too)
	local tools = RS:FindFirstChild("JankfireTools")
	if tools and (key == "shredder" or wid == "shredder") then
		local nm = if wid then "Shredder@" .. skin else "Shredder"
		local t = tools:FindFirstChild(nm)
		if t then table.insert(out, t) end
		local k2 = pb().WeaponSets.kit:FindFirstChild(nm)
		if k2 then table.insert(out, k2) end
	end
	return out
end

-- src: node -> the new piece, or a list of candidates (two pieces of one node, or two files' versions of one model):
-- the one whose mesh size matches the live part goes on
local function pick(c, p: MeshPart)
	if c == nil then return nil, false end
	local list = if typeof(c) == "table" then c else { c }
	for _, s in list do
		if (s.MeshSize - p.MeshSize).Magnitude <= 1e-3 * math.max(1, p.MeshSize.Magnitude) then return s, true end
	end
	return list[1], false
end

local function applyKey(key: string, src: { [string]: any }, dry: boolean?, tot)
	local tg = targets(key)
	local a, sk, nm = 0, 0, 0
	for _, m in tg do
		tot.models += 1
		for _, p in m:GetDescendants() do
			if not (p:IsA("MeshPart") and p:GetAttribute("WrapUV")) then continue end
			local s, fits = pick(src[p.Name] or src[strip(p.Name)], p)
			if not s then nm += 1; continue end
			if not fits then sk += 1; continue end
			if not dry then
				local size, cf = p.Size, p.CFrame
				p:ApplyMesh(s)
				p.Size = size; p.CFrame = cf
			end
			a += 1
		end
	end
	tot.applied += a; tot.skipped += sk; tot.nomatch += nm
	return ("%s: %d models, %d parts%s%s"):format(key, #tg, a, if sk > 0 then ", SIZE MISMATCH " .. sk else "", if nm > 0 then ", no match " .. nm else "")
end

local function summary(dry, tot, lines)
	table.sort(lines)
	return ("%s%d parts in %d models%s%s\n"):format(if dry then "(dry) " else "", tot.applied, tot.models,
		if tot.skipped > 0 then ", " .. tot.skipped .. " size mismatches (left alone)" else "",
		if tot.nomatch > 0 then ", " .. tot.nomatch .. " WrapUV parts with no new piece" else "") .. table.concat(lines, "\n")
end

-- one upload per gun: rows = { [book key] = asset id }
function R.apply(rows: { [string]: number }, dry: boolean?)
	local lines, tot = {}, { applied = 0, skipped = 0, nomatch = 0, models = 0 }
	for key, id in rows do
		local ok, pk = pcall(function() return IS:LoadAsset(id) end)
		if not ok then table.insert(lines, key .. ": LOAD FAILED " .. tostring(pk)); continue end
		local src = {}
		for _, d in pk:GetDescendants() do
			if d:IsA("MeshPart") then src[strip(d.Name)] = d end
		end
		table.insert(lines, applyKey(key, src, dry, tot))
		pk:Destroy()
		task.wait()
	end
	return summary(dry, tot, lines)
end

-- one upload per family batch (tools/roblox/reuv_pack.py): every piece named "<book key>~<piece>"
function R.applyPack(id: number, dry: boolean?)
	local ok, pk = pcall(function() return IS:LoadAsset(id) end)
	if not ok then return "LOAD FAILED " .. tostring(pk) end
	local by: { [string]: { [string]: MeshPart } } = {}
	for _, d in pk:GetDescendants() do
		if d:IsA("MeshPart") then
			local key, piece = string.match(d.Name, "^(.-)~(.+)$")
			if key then
				by[key] = by[key] or {}
				local node = strip(piece)
				local had = by[key][node]
				if had == nil then by[key][node] = d
				elseif typeof(had) == "table" then table.insert(had, d)
				else by[key][node] = { had, d } end
			end
		end
	end
	local lines, tot = {}, { applied = 0, skipped = 0, nomatch = 0, models = 0 }
	for key, src in by do table.insert(lines, applyKey(key, src, dry, tot)) end
	pk:Destroy()
	return summary(dry, tot, lines)
end

-- park the current (new) sets as UV2, so the switch can go both ways
function R.park2()
	local b = pb():FindFirstChild("UV2")
	if b then b:Destroy() end
	b = Instance.new("Folder"); b.Name = "UV2"
	for _, s in SETS do
		local f = s[2]()
		if f then local c = f:Clone(); c.Name = s[1]; c.Parent = b end
	end
	b.Parent = pb()
	return "UV2 parked"
end

-- put a parked set back: "uv1" (the old UVs) or "uv2" (the new). Whole sets are replaced.
function R.switch(which: string)
	local b = pb():FindFirstChild(string.upper(which))
	if not b then return "no " .. string.upper(which) .. " in PolishBackup" end
	local out = {}
	for _, s in SETS do
		local saved = b:FindFirstChild(s[1])
		local live = s[2]()
		if not (saved and live) then continue end
		local parent, name = live.Parent, live.Name
		local attrs = live:GetAttributes()
		live:Destroy()
		local c = saved:Clone(); c.Name = name
		for k, v in attrs do c:SetAttribute(k, v) end
		c.Parent = parent
		table.insert(out, name)
	end
	RS.JankfireWeapons:SetAttribute("UVs", which)
	return "switched to " .. which .. ": " .. table.concat(out, ", ")
end

return R
