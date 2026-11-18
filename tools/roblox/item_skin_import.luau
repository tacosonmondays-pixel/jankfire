-- gadget SKINS into the place (tools/roblox/item_skins.py; run in Studio, execute_luau, Edit, with ASSET and INFO filled
-- in from skins_v1.json). Each skin becomes a Model "<gadget>_<skin>" in ReplicatedStorage.JankfireSkins, built exactly
-- like a gadget template (item_import.luau: world size, pivot = the middle, pieces by node, GripPos / GripRot, WrapUV +
-- WrapZone on its wrap pieces), with attributes Weapon = the gadget id and Item = true: GunSkins.template(gadget, id)
-- finds it, LootTable.SKINS gives its name and rarity, and the gadget code (Utility.client itemModel, ThirdPerson)
-- wears it when the player's Skins attribute picks it. Upload pieces are named "<gadget>@<skin>_<node>__<look>".
local ASSET = 0 -- <- the upload's asset id
local INFO = nil :: any -- <- items.json, as a Luau table
local S = 3

local function look(p: BasePart, code: string)
	local kind, hex = string.sub(code, 1, 1), string.sub(code, 2, 7)
	p.Color = Color3.fromHex(hex)
	p.Material = if kind == "n" then Enum.Material.Neon else Enum.Material.SmoothPlastic
	p.Reflectance = 0
	p.Transparency = 0
	if p:IsA("MeshPart") then p.TextureID = "" end
	for _, c in p:GetChildren() do if c:IsA("SurfaceAppearance") then c:Destroy() end end
end

local res = game:GetService("InsertService"):LoadAsset(ASSET)
local byItem: { [string]: { BasePart } } = {}
for _, d in res:GetDescendants() do
	if d:IsA("BasePart") then
		local nm = if d.Parent and d.Parent ~= res and d.Parent:IsA("Model") then d.Parent.Name else d.Name
		d:SetAttribute("Piece", nm)
		local id = string.match(nm, "^(%a+@%a+)_")
		if id then byItem[id] = byItem[id] or {}; table.insert(byItem[id], d) end
	end
end
local lib = game.ReplicatedStorage:FindFirstChild("JankfireSkins")
if not lib then
	lib = Instance.new("Folder")
	lib.Name = "JankfireSkins"
	lib.Parent = game.ReplicatedStorage
end
local out = {}
local K = S / INFO.unit -- (world studs per upload stud)
for id, info in INFO.items do
	local parts = byItem[id]
	if not parts then table.insert(out, id .. ": MISSING"); continue end
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in parts do lo = lo:Min(p.Position - p.Size / 2); hi = hi:Max(p.Position + p.Size / 2) end
	local flo, fhi = Vector3.new(table.unpack(info.lo)), Vector3.new(table.unpack(info.hi))
	local origin = (lo + hi) / 2 - (flo + fhi) / 2 * INFO.unit -- (where the file's origin landed in the upload)
	local m = Instance.new("Model")
	m.Name = info.skin or (string.gsub(id, "@", "_"))
	local big: BasePart? = nil
	for _, p in parts do
		local node, code = string.match(p:GetAttribute("Piece") or p.Name, "^%a+@%a+_(.-)__(%w+)$")
		local c = p:Clone()
		for _, x in c:GetChildren() do if not x:IsA("SurfaceAppearance") then x:Destroy() end end
		c.Name = node or p.Name
		c:SetAttribute("Look", code); c:SetAttribute("Piece", nil)
		if code then look(c, code) end
		c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
		local wz = info.wrap
		if type(wz) == "table" and node then
			for _, zone in { "a", "b" } do
				if type(wz[zone]) == "table" and table.find(wz[zone], node) and c:IsA("MeshPart") then
					c:SetAttribute("WrapUV", true); c:SetAttribute("WrapZone", zone)
				end
			end
		end
		c.Size = p.Size * K
		c.CFrame = CFrame.new((p.Position - origin) * K)
		c.Parent = m
		if not big or c.Name == "body" then big = c end
	end
	m.PrimaryPart = big
	m.WorldPivot = CFrame.identity
	local g, gr = info.grip or { 0, 0, 0 }, info.gripRot or { 0, 0, 0 }
	m:SetAttribute("GripPos", Vector3.new(g[1], g[2], g[3]) * S)
	m:SetAttribute("GripRot", Vector3.new(gr[1], gr[2], gr[3]))
	m:SetAttribute("Asset", ASSET)
	m:SetAttribute("Weapon", info.item or string.match(id, "^(%a+)@"))
	m:SetAttribute("Item", true)
	m:SetAttribute("SkinName", info.name)
	m:SetAttribute("FileLo", flo); m:SetAttribute("FileHi", fhi)
	local old = lib:FindFirstChild(m.Name)
	if old then old:Destroy() end
	m.Parent = lib
	local _, size = m:GetBoundingBox()
	table.insert(out, ("%s: %d pieces, %.2f x %.2f x %.2f studs"):format(m.Name, #parts, size.X, size.Y, size.Z))
end
res:Destroy()
return table.concat(out, "\n")
