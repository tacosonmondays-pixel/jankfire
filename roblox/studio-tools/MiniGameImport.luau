-- PolishBackup.MiniGameImport (18 Nov 2026): the hub's mini-games' furniture and pieces (tools/roblox/minigame_models.py,
-- one upload) into ReplicatedStorage.JankfireMiniGames.Kit, one Model per piece name (mg_armtable, mg_stool,
-- mg_boardtable, mg_chair, mg_pawn ... mg_king, mg_man, mg_cabinet), painted from the piece names
-- ("<model><n>__<kind>_<hex>"), no collisions, queries or touches (the server adds its own collision boxes). the upload
-- lands in the file's own frame (rbxglb.turn_for_roblox): a model's origin is its floor centre and its front faces +Z.
-- server/MiniGames.server builds the games from these; client/MiniBoardUI sets the pieces. run in Edit:
--   local I = require(game.ServerStorage.PolishBackup.MiniGameImport:Clone()); print(I.run())
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local I = {}
I.ASSET = 96758810630944 -- (tools/roblox/minigame_models.py: v2, 19 Nov 2026, the clearer chess pieces and the cabinet lid's cushions; v1 was 134966926271798)
I.MORE = { 93628648477968 } -- (tools/roblox/boxing_models.py, 19 Nov 2026: mg_glove) every upload whose pieces join the kit
local MAT = { plastic = Enum.Material.SmoothPlastic, neon = Enum.Material.Neon, wood = Enum.Material.SmoothPlastic, fabric = Enum.Material.SmoothPlastic }

function I.run(id: number?): string
	local ok, container = pcall(function() return InsertService:LoadAsset(id or I.ASSET) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	if not id then
		for _, more in I.MORE do
			local ok2, c2 = pcall(function() return InsertService:LoadAsset(more) end)
			if not ok2 or not c2 then return "LOAD FAILED " .. more .. " " .. tostring(c2) end
			for _, d in c2:GetChildren() do d.Parent = container end
			c2:Destroy()
		end
	end
	local root = ReplicatedStorage:FindFirstChild("JankfireMiniGames")
	if not root then
		root = Instance.new("Folder")
		root.Name = "JankfireMiniGames"
		root.Parent = ReplicatedStorage
	end
	local old = root:FindFirstChild("Kit")
	local kit = Instance.new("Folder")
	kit.Name = "Kit"
	kit:SetAttribute("AssetId", id or I.ASSET)
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = Color3.fromHex(h); d.TextureID = ""
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind ~= "neon"
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for name, parts in groups do
		local m = Instance.new("Model")
		m.Name = name
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m.Parent = kit
		local cf, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.2f x %.2f x %.2f, floor %.2f)"):format(name, #parts, size.X, size.Y, size.Z, cf.Y - size.Y / 2))
	end
	container:Destroy()
	if old then old:Destroy() end
	kit.Parent = root
	table.sort(names)
	return #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  ")
end

return I
