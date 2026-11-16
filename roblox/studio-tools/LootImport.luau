-- The loot containers into the place (roblox/docs/LOOT.md). ServerStorage.PolishBackup.LootImport, run from Studio
-- (execute_luau, Edit):
--
--   local L = require(game.ServerStorage.PolishBackup.LootImport:Clone())
--   L.load(<asset id>)      -- the upload (tools/roblox/loot_models.py: the three in one model) -> ReplicatedStorage.JankfireLoot
--   L.check()               -- each one there, its moving groups, its height
--
-- An upload's pieces arrive as MeshParts (inside Models named "<kind>_<node>__<look>") at their box centres, unrotated,
-- 1 stud = 1 file unit. Each container becomes a Model "<kind>" whose pivot is the middle of its bottom face (the
-- file's origin); a piece whose node is "<Group>-<name>" goes into the Model <Group> (Lid, Zip, FlapL, FlapR, Cap) with
-- the group's hinge (a CFrame in the container's frame) and swing angle as attributes. LootOpening.luau moves them.
local L = {}

-- from loot_models.py's loot.json: each container's box in the file, its height, how it opens and its groups
L.DATA = {
	crate = { lo = { -2.02, 0, -1.44 }, hi = { 2.02, 2.39, 1.3581 }, height = 2.33, open = "hinge", groups = { Lid = { hinge = { 0.0000, 1.7800, 1.2600 }, angle = 108 } } },
	bag = { lo = { -1.99, -0.02, -0.9927 }, hi = { 1.99, 2, 0.9927 }, height = 2, open = "flap", run = 2.94, groups = { FlapL = { hinge = { 0.0000, 1.2200, -0.8827 }, angle = -80 }, FlapR = { hinge = { 0.0000, 1.2200, 0.8827 }, angle = 80 }, Zip = {  } } },
	spray = { lo = { -0.6375, 0, -0.6375 }, hi = { 0.6375, 3.56, 0.6375 }, height = 3.56, open = "pop", groups = { Cap = { hinge = { 0.0000, 3.1300, 0.0000 } } } },
}
L.ASSET = 98609732244394 -- jf_loot_containers_1 (16 Nov 2026)

local function look(p: BasePart, code: string)
	local kind, hex = string.sub(code, 1, 1), string.sub(code, 2, 7)
	p.Color = Color3.fromHex(hex)
	p.Material = if kind == "n" then Enum.Material.Neon else Enum.Material.SmoothPlastic
	p.Reflectance = 0
	p.Transparency = 0
	if p:IsA("MeshPart") then p.TextureID = "" end
	for _, c in p:GetChildren() do if c:IsA("SurfaceAppearance") then c:Destroy() end end
end

local function v3(t: { number }): Vector3 return Vector3.new(t[1], t[2], t[3]) end

function L.load(assetId: number?)
	local id = assetId or L.ASSET
	assert(type(id) == "number" and id > 0, "no asset id")
	local ok, res = pcall(function() return game:GetService("InsertService"):LoadAsset(id) end)
	if not ok then return "load failed: " .. tostring(res) end
	local byKind: { [string]: { BasePart } } = {}
	for _, d in res:GetDescendants() do
		if d:IsA("BasePart") then
			local nm = if d.Parent and d.Parent ~= res and d.Parent:IsA("Model") then d.Parent.Name else d.Name
			d:SetAttribute("Piece", nm)
			local kind = string.match(nm, "^(%a+)_")
			if kind then
				byKind[kind] = byKind[kind] or {}
				table.insert(byKind[kind], d)
			end
		end
	end
	local lib = game.ReplicatedStorage:FindFirstChild("JankfireLoot")
	if not lib then
		lib = Instance.new("Folder")
		lib.Name = "JankfireLoot"
		lib.Parent = game.ReplicatedStorage
	end
	local out = {}
	for kind, info in L.DATA do
		local parts = byKind[kind]
		if not parts then table.insert(out, kind .. ": MISSING in the upload"); continue end
		local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
		for _, p in parts do lo = lo:Min(p.Position - p.Size / 2); hi = hi:Max(p.Position + p.Size / 2) end
		-- where the file's origin landed: the upload's box against the file's box
		local origin = (lo + hi) / 2 - (v3(info.lo) + v3(info.hi)) / 2
		local m = Instance.new("Model")
		m.Name = kind
		local groups: { [string]: Model } = {}
		local body: BasePart? = nil
		for _, p in parts do
			local node, code = string.match(p:GetAttribute("Piece") or p.Name, "^%a+_(.-)__(%w+)$")
			local c = p:Clone()
			for _, x in c:GetChildren() do if not x:IsA("SurfaceAppearance") then x:Destroy() end end
			c.Name = node or p.Name
			c:SetAttribute("Look", code); c:SetAttribute("Piece", nil)
			if code then look(c, code) end
			c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
			c.CastShadow = not (node and string.find(node, "glow"))
			c.CFrame = CFrame.new(p.Position - origin)
			local grp, rest = string.match(node or "", "^(%u%a+)%-(.+)$")
			if grp then
				c.Name = rest
				local g = groups[grp]
				if not g then
					g = Instance.new("Model")
					g.Name = grp
					groups[grp] = g
					g.Parent = m
				end
				c.Parent = g
			else
				c.Parent = m
				if c.Name == "body" and (not body or c.Size.Magnitude > (body :: BasePart).Size.Magnitude) then body = c end
			end
			if c.Name == "glow" then c.Transparency = 1 end
		end
		for grp, g in groups do
			local gi = info.groups and info.groups[grp] or {}
			local big: BasePart? = nil
			for _, c in g:GetChildren() do if c:IsA("BasePart") and (not big or c.Size.Magnitude > big.Size.Magnitude) then big = c end end
			g.PrimaryPart = big
			g.WorldPivot = if gi.hinge then CFrame.new(v3(gi.hinge)) else (big and big.CFrame or CFrame.identity)
			if gi.hinge then g:SetAttribute("Hinge", CFrame.new(v3(gi.hinge))) end
			if gi.angle then g:SetAttribute("Angle", gi.angle) end
			if grp == "Zip" and info.run then g:SetAttribute("Run", info.run) end
		end
		m.PrimaryPart = body
		m.WorldPivot = CFrame.identity
		m:SetAttribute("Height", info.height)
		m:SetAttribute("Open", info.open)
		m:SetAttribute("Asset", id)
		local old = lib:FindFirstChild(kind)
		if old then old:Destroy() end
		m.Parent = lib
		local n = 0
		for _, d in m:GetDescendants() do if d:IsA("BasePart") then n += 1 end end
		table.insert(out, ("%s: %d pieces"):format(kind, n))
	end
	res:Destroy()
	return table.concat(out, "\n")
end

function L.check(): string
	local lib = game.ReplicatedStorage:FindFirstChild("JankfireLoot")
	if not lib then return "no ReplicatedStorage.JankfireLoot" end
	local out = {}
	for kind, info in L.DATA do
		local m = lib:FindFirstChild(kind)
		if not m then table.insert(out, kind .. ": MISSING"); continue end
		local miss = {}
		for grp in info.groups or {} do if not m:FindFirstChild(grp) then table.insert(miss, grp) end end
		local _, size = m:GetBoundingBox()
		table.insert(out, ("%s: size %.2f x %.2f x %.2f, height %s, open %s%s"):format(kind, size.X, size.Y, size.Z,
			tostring(m:GetAttribute("Height")), tostring(m:GetAttribute("Open")), if #miss > 0 then ", MISSING " .. table.concat(miss, ",") else ""))
	end
	return table.concat(out, "\n")
end

return L
