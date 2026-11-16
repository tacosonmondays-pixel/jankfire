-- The weapon hats into the place (roblox/docs/GUN-HATS.md). ServerStorage.PolishBackup.HatImport, run from Studio
-- (execute_luau, Edit):
--
--   local H = require(game.ServerStorage.PolishBackup.HatImport:Clone())
--   H.load(<asset id>)      -- the upload (tools/roblox/hat_models.py: every hat in one model) -> ReplicatedStorage.JankfireHats
--   H.check()               -- every hat there, its pieces in the hat finish, its moving bits present
--
-- An upload's pieces arrive as MeshParts named "<hat>_<node>__<look>" at their box centres, unrotated, 1 stud = one
-- template stud (UNIT metres: the file is 10 x the hat's size). Each hat becomes a Model "hat_<id>" whose pivot is the
-- hat's foot (the file's origin), each piece a MeshPart named by its node, painted from its look code (p = SmoothPlastic,
-- n = Neon, m = Metal: the Royal Duck's gold) like WeaponImport paints the guns. GunHats.luau builds the hats in the game from these templates.
local H = {}

local function data()
	local m = game.ReplicatedStorage.Jankfire:FindFirstChild("GunHatData")
	assert(m, "ReplicatedStorage.Jankfire.GunHatData is missing (push it first)")
	return require(m:Clone())
end

-- p / n / m + rrggbb [+ aa: opacity, two hex digits] (tools/roblox/hat_models.py look)
local function look(p: BasePart, code: string)
	local kind, hex, alpha = string.sub(code, 1, 1), string.sub(code, 2, 7), string.sub(code, 8, 9)
	p.Color = Color3.fromHex(hex)
	p.Material = if kind == "n" then Enum.Material.Neon elseif kind == "m" then Enum.Material.Metal else Enum.Material.SmoothPlastic
	p.Reflectance = 0
	p.Transparency = if #alpha == 2 then 1 - (tonumber(alpha, 16) or 255) / 255 else 0
	if p:IsA("MeshPart") then p.TextureID = "" end
	for _, c in p:GetChildren() do if c:IsA("SurfaceAppearance") then c:Destroy() end end
end

function H.load(assetId: number?)
	local D = data()
	local id = assetId or D.ASSET
	assert(type(id) == "number" and id > 0, "no asset id")
	local ok, res = pcall(function() return game:GetService("InsertService"):LoadAsset(id) end)
	if not ok then return "load failed: " .. tostring(res) end
	local byHat: { [string]: { BasePart } } = {}
	for _, d in res:GetDescendants() do
		if d:IsA("BasePart") then
			-- (the piece's name rides on the Model round it; the MeshPart itself is named after the mesh)
			local nm = if d.Parent and d.Parent ~= res and d.Parent:IsA("Model") then d.Parent.Name else d.Name
			d:SetAttribute("Piece", nm)
			local hat = string.match(nm, "^(%a+)_")
			if hat then
				byHat[hat] = byHat[hat] or {}
				table.insert(byHat[hat], d)
			end
		end
	end
	local lib = game.ReplicatedStorage:FindFirstChild("JankfireHats")
	if not lib then
		lib = Instance.new("Folder")
		lib.Name = "JankfireHats"
		lib.Parent = game.ReplicatedStorage
	end
	local out = {}
	for _, hid in D.ORDER do
		if hid == "none" then continue end
		local parts = byHat[hid]
		local info = D.HATS[hid]
		if not parts or not info or not info.lo then table.insert(out, hid .. ": MISSING in the upload"); continue end
		-- the hat's box in the upload against its file box: where the file's origin (the foot) landed
		local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
		for _, p in parts do
			lo = lo:Min(p.Position - p.Size / 2); hi = hi:Max(p.Position + p.Size / 2)
		end
		local U = 1 / D.UNIT -- (template studs per metre)
		local origin = (lo + hi) / 2 - (info.lo + info.hi) / 2 * U
		local m = Instance.new("Model")
		m.Name = "hat_" .. hid
		for _, p in parts do
			local node, code = string.match(p:GetAttribute("Piece") or p.Name, "^%a+_(.-)__(%w+)$")
			local c = p:Clone()
			for _, x in c:GetChildren() do if not x:IsA("SurfaceAppearance") then x:Destroy() end end
			c.Name = node or p.Name
			c:SetAttribute("Look", code); c:SetAttribute("Piece", nil)
			if code then look(c, code) end
			c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
			c.CFrame = CFrame.new(p.Position - origin)
			c.Parent = m
		end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("Unit", D.UNIT)
		m:SetAttribute("Asset", id)
		local old = lib:FindFirstChild(m.Name)
		if old then old:Destroy() end
		m.Parent = lib
		local size = (hi - lo) * D.UNIT
		table.insert(out, ("%s: %d pieces, %.3f x %.3f x %.3f m"):format(hid, #parts, size.X, size.Y, size.Z))
	end
	res:Destroy()
	return table.concat(out, "\n")
end

function H.check()
	local D = data()
	local lib = game.ReplicatedStorage:FindFirstChild("JankfireHats")
	if not lib then return "no JankfireHats" end
	local bad = {}
	for _, hid in D.ORDER do
		if hid == "none" then continue end
		local m = lib:FindFirstChild("hat_" .. hid)
		if not m then table.insert(bad, hid .. " missing"); continue end
		for _, p in m:GetChildren() do
			local mat = p.Material
			if p:IsA("MeshPart") and not (p.TextureID == "" and (mat == Enum.Material.SmoothPlastic or mat == Enum.Material.Neon or mat == Enum.Material.Metal)) then
				table.insert(bad, hid .. "." .. p.Name .. " off-finish")
			end
		end
		for node in (D.MOVES[hid] or {}) do
			if not m:FindFirstChild(node) then table.insert(bad, hid .. " has no moving " .. node) end
		end
	end
	return if #bad == 0 then "hats ok" else table.concat(bad, "\n")
end

return H
