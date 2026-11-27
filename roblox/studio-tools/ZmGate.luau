--!strict
-- ZmGate (27 Nov 2026; roblox/docs/ZOMBIES.md 4.9): the school's front gate for the ZOMBIES news intro. The owner:
-- "can you do a shot of the school gate and multiple zombies piling up?". The school (Map.JankfieldHighV2B) had a
-- chain-link fence along the front of its grounds and no gate, and nothing outside the fence to stand on. This adds,
-- in the map's own frame (so every game's copy has it): two chunky stone pillars and a pair of iron bar gates in the
-- fence line at the end of the drive (x 28, z 171: between the trees), a pavement and a stretch of road outside it, and one
-- sodium street lamp. All of it is set dressing: no collisions, no queries, outside the play space. The news feed's
-- crowd stands on the road and the film shakes the gate leaves (ZombieCine).
-- Studio, Edit:
--   require(game.ServerStorage.PolishBackup.ZmGate:Clone()).build(workspace.Map.JankfieldHighV2B) -> report
-- (replaces an older ZmFrontGate). The model: ZmFrontGate, PrimaryPart GateBase (on the ground in the gate's middle,
-- LookVector out to the road), LeafL / LeafR (models; attribute Hinge = the hinge's point in GateBase's space, Sign =
-- which way the leaf runs from it).
local G = {}

local STONE, CAP, IRON, ROAD, KERB, POST = Color3.fromRGB(176, 170, 160), Color3.fromRGB(146, 141, 132), Color3.fromRGB(40, 43, 48),
	Color3.fromRGB(58, 60, 64), Color3.fromRGB(150, 148, 142), Color3.fromRGB(52, 55, 60)

function G.build(map: Model): string
	local old = map:FindFirstChild("ZmFrontGate")
	if old then old:Destroy() end
	local pv = map:GetPivot()
	local m = Instance.new("Model")
	m.Name = "ZmFrontGate"
	-- the gate's frame: x along the fence, y up, z out to the road (the map's +z)
	local base = Instance.new("Part")
	base.Name = "GateBase"
	base.Size = Vector3.new(0.2, 0.2, 0.2); base.Transparency = 1
	base.CFrame = CFrame.lookAt(pv:PointToWorldSpace(Vector3.new(28, 0, 171)), pv:PointToWorldSpace(Vector3.new(28, 0, 181)))
	base.Parent = m
	m.PrimaryPart = base
	local gf = base.CFrame
	local n = 0
	local function part(parent: Instance, name: string, size: Vector3, cf: CFrame, col: Color3, shape: Enum.PartType?): Part
		local p = Instance.new("Part")
		p.Name = name
		if shape then p.Shape = shape end
		p.Size = size
		p.CFrame = cf
		p.Color = col
		p.Material = Enum.Material.SmoothPlastic
		p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		p.Parent = parent
		n += 1
		return p
	end
	-- (in the gate's frame: +x right as you look out from the school, +z out)
	local function at(x: number, y: number, z: number): CFrame return gf * CFrame.new(-x, y, -z) end
	-- the pillars, their caps and ball finials
	for _, x in { -8.5, 8.5 } do
		part(m, "Pillar", Vector3.new(3, 12, 3), at(x, 6, 0), STONE)
		part(m, "PillarCap", Vector3.new(3.7, 0.9, 3.7), at(x, 12.45, 0), CAP)
		part(m, "PillarBall", Vector3.new(1.8, 1.8, 1.8), at(x, 13.8, 0), STONE, Enum.PartType.Ball)
	end
	-- the leaves: three rails and nine round bars with ball tips each, hinged on the pillars' inner faces
	for _, side in { -1, 1 } do
		local leaf = Instance.new("Model")
		leaf.Name = if side < 0 then "LeafL" else "LeafR"
		local hx = 7 * side -- (the hinge, on the pillar's inner face)
		leaf:SetAttribute("Hinge", Vector3.new(-hx, 0, 0)) -- (GateBase's object space: at() flips x)
		leaf:SetAttribute("Sign", side)
		for _, y in { 0.9, 5.0, 9.0 } do
			part(leaf, "Rail", Vector3.new(7, 0.45, 0.35), at(hx - 3.5 * side, y, 0), IRON)
		end
		for k = 0, 8 do
			local x = hx - side * (0.45 + 0.76 * k)
			part(leaf, "Bar", Vector3.new(9.2, 0.3, 0.3), at(x, 5.0, 0) * CFrame.Angles(0, 0, math.rad(90)), IRON, Enum.PartType.Cylinder)
			part(leaf, "Tip", Vector3.new(0.46, 0.46, 0.46), at(x, 9.8, 0), IRON, Enum.PartType.Ball)
		end
		leaf.Parent = m
	end
	-- the road outside, its kerb and a sodium lamp
	part(m, "Pavement", Vector3.new(96, 1, 10), at(0, -0.35, 5.5), KERB) -- (the street trees stand on it)
	part(m, "Road", Vector3.new(96, 1, 24), at(0, -0.55, 22.5), ROAD)
	part(m, "LampPost", Vector3.new(10, 0.5, 0.5), at(-16, 5, 4.5) * CFrame.Angles(0, 0, math.rad(90)), POST, Enum.PartType.Cylinder)
	part(m, "LampArm", Vector3.new(0.35, 0.35, 2.6), at(-16, 9.9, 3.4), POST)
	local head = part(m, "LampHead", Vector3.new(1.1, 0.5, 1.6), at(-16, 9.75, 2.2), Color3.fromRGB(255, 196, 120))
	head.Material = Enum.Material.Neon
	local l = Instance.new("SpotLight")
	l.Face = Enum.NormalId.Bottom; l.Angle = 110; l.Range = 30; l.Brightness = 2.2; l.Color = Color3.fromRGB(255, 186, 110); l.Shadows = true
	l.Parent = head
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
	m.Parent = map
	return string.format("ZmFrontGate: %d parts at %s, out %s", n, tostring(base.Position), tostring(base.CFrame.LookVector))
end

-- ---------------------------------------------------------------- the hedges, A or B (27 Nov 2026; the owner: "can we
-- make the shrubs better looking?" and "I heard if you take a leaf texture you can place it in different planes to create
-- a shrub?"). A (sc_hedgeA, in the school's kit: tools/roblox/school_models.py hedge_v2) is soft lumpy bodies in muted
-- greens; B (sc_hedgeB, tools/roblox/school_hedgeB.py) is the same bodies as a dark core wrapped in leaf cards (the leaf
-- atlas, tools/roblox/leaf_atlas.py). The planters are the kit's (sc_ground). Hit boxes: the layout's, either way.
--   require(game.ServerStorage.PolishBackup.ZmGate:Clone()).importHedgesB(workspace.Map.JankfieldHighV2B, <asset id>, <leaf image id>)
--   require(game.ServerStorage.PolishBackup.ZmGate:Clone()).hedges(workspace.Map.JankfieldHighV2B, "A" | "B")  -- the switch
-- (the one not shown waits in ServerStorage.ZmHedges; every game's copy of the school has the shown one). The leaves'
-- picture goes on as a SurfaceAppearance (AlphaMode Transparency) from the atlas uploaded as an Image: the copy a .glb
-- upload makes of its picture lost the alpha (27 Nov test: black squares round the leaves)
local function store(): Folder
	local f = game:GetService("ServerStorage"):FindFirstChild("ZmHedges")
	if not f then f = Instance.new("Folder"); f.Name = "ZmHedges"; f.Parent = game:GetService("ServerStorage") end
	return f :: Folder
end
function G.importHedgesB(map: Model, id: number, leafImage: number): string
	local shell = map:FindFirstChild("Shell")
	local ground = shell and shell:FindFirstChild("sc_ground")
	if not ground then return "no Shell.sc_ground to line up with" end
	local box = game:GetService("InsertService"):LoadAsset(id)
	local m = Instance.new("Model")
	m.Name = "sc_hedgeB"
	local nc, nl = 0, 0
	for _, d in box:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local hx = string.match(d.Name, "^zb_core%d+__(%x%x%x%x%x%x)")
		if hx then
			d.Color = Color3.fromHex(hx); d.Material = Enum.Material.SmoothPlastic; d.TextureID = ""
			nc += 1
		elseif string.match(d.Name, "^zb_leaf") then
			d.Color = Color3.new(1, 1, 1); d.Material = Enum.Material.SmoothPlastic; d.TextureID = ""
			d.DoubleSided = true; d.CastShadow = false
			local sa = Instance.new("SurfaceAppearance")
			sa.ColorMap = "rbxassetid://" .. tostring(leafImage)
			sa.AlphaMode = Enum.AlphaMode.Transparency
			sa.Parent = d
			nl += 1
		else
			continue
		end
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.Parent = m
	end
	box:Destroy()
	m.WorldPivot = CFrame.identity -- (the file's own frame: the kit's, as WebArena.swap places it)
	m:PivotTo(ground:GetPivot())
	local old = store():FindFirstChild("sc_hedgeB") or shell:FindFirstChild("sc_hedgeB")
	if old then old:Destroy() end
	m:SetAttribute("AssetId", id)
	m.Parent = store()
	return string.format("sc_hedgeB: %d core pieces, %d leaf pieces (waiting in ServerStorage.ZmHedges)", nc, nl)
end
function G.hedges(map: Model, which: string): string
	local shell = map:FindFirstChild("Shell")
	if not shell then return "no Shell" end
	local st = store()
	local want, other = "sc_hedge" .. which, (if which == "A" then "sc_hedgeB" else "sc_hedgeA")
	local w = shell:FindFirstChild(want) or st:FindFirstChild(want)
	if not w then return "no " .. want end
	local o = shell:FindFirstChild(other)
	if o then o.Parent = st end
	w.Parent = shell
	return "hedges " .. which .. " shown"
end

return G
