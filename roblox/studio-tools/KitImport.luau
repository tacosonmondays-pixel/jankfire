--!nocheck
-- edit-time tool: brings uploaded kit models (Open Cloud Model assets made from the Blender .glb files) into
-- ServerStorage.JankfireMeshes as templates. an upload arrives grey and turned half way round, so each piece is painted
-- from its name ("<model><n>__<kind>_<hex>": kind = plastic | neon | wood | diamond) and the model is turned back about
-- its middle. the template's pivot is the middle of its box, unrotated; its front is +Z.
-- usage: local K = require(game.ServerStorage.PolishBackup.KitImport:Clone()); print(K.run({ dp_office = 123456789 }))
local K = {}
local MAT = { plastic = Enum.Material.SmoothPlastic, neon = Enum.Material.Neon, wood = Enum.Material.Wood, diamond = Enum.Material.DiamondPlate }

function K.run(kit)
	local IS = game:GetService("InsertService")
	local lib = game.ServerStorage.JankfireMeshes
	local flagSrc = lib.bc_rangecounter:FindFirstChildWhichIsA("MeshPart", true)
	local out = {}
	for name, id in kit do
		local ok, container = pcall(function() return IS:LoadAsset(id) end)
		if not ok or not container then table.insert(out, name .. " LOAD FAILED " .. tostring(container)); continue end
		local m = Instance.new("Model")
		m.Name = name
		local n, bad = 0, 0
		for _, d in container:GetDescendants() do
			if d:IsA("MeshPart") then
				local kind, hex = d.Name:match("__(%a+)_(%x%x%x%x%x%x)")
				if kind and MAT[kind] then d.Material = MAT[kind]; d.Color = Color3.fromHex(hex) else bad += 1 end
				d.TextureID = ""
				d.Anchored = true
				d.CanCollide = flagSrc.CanCollide; d.CanQuery = flagSrc.CanQuery; d.CanTouch = flagSrc.CanTouch
				d.CastShadow = kind ~= "neon"
				d.Parent = m
				n += 1
			end
		end
		container:Destroy()
		if n == 0 then table.insert(out, name .. " HAD NO MESHES"); m:Destroy(); continue end
		local cf = m:GetBoundingBox()
		local fix = cf * CFrame.Angles(0, math.pi, 0) * cf:Inverse()
		for _, p in m:GetChildren() do p.CFrame = fix * p.CFrame end
		local cf2, size = m:GetBoundingBox()
		m.WorldPivot = CFrame.new(cf2.Position)
		m:PivotTo(CFrame.new(0, 0, 0))
		m:SetAttribute("UploadFlipFixed", true)
		m:SetAttribute("AssetId", id)
		local old = lib:FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib
		table.insert(out, ("%s: %d parts (%d unpainted) %.1f x %.1f x %.1f"):format(name, n, bad, size.X, size.Y, size.Z))
		task.wait()
	end
	table.sort(out)
	return table.concat(out, "\n")
end

return K
