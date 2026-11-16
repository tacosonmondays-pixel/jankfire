--!nocheck
-- ROOFTOP V2 (16 Nov 2026): a second Rooftop arena, built to the design principles of 16 Nov at its own site (world
-- 0, 0, 8000). v1 (workspace.Map.Rooftop) is never touched. Which one matches are played in is the switch
-- workspace.Map's attribute "Arena" ("Rooftop" = v1, the default; "RooftopV2"), read by every script through
-- ReplicatedStorage.Jankfire.Arena.
-- the look is one Blender kit ("rooftop2": tools/roblox/rooftop2_models.py > rooftop2.glb > one Model asset); the hit
-- boxes, spawn points, team spawns, jump pads, water and lights come from the same Python run as RooftopV2Layout, so
-- the look and the collision cannot drift apart. the city round it is built here (plain parts, a fixed seed).
-- run in Edit, from a clone (a require of the original is cached):
--   local R = require(game.ServerStorage.PolishBackup.RooftopV2:Clone())
--   R.import()        the kit's models into ServerStorage.JankfireMeshes (r2_*)
--   R.build()         wipe and rebuild workspace.Map.RooftopV2           R.clear()   take it away
--   R.check()         spawn sight lines, clear spawn points, pad flights (the same checks the Python run makes)
--   R.use("v2")       matches go to v2 (R.use("v1") back to the old one: the default)
local ServerStorage = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local CollectionService = game:GetService("CollectionService")

local R = {}
R.NAME = "RooftopV2"
R.KIT = "rooftop2"
R.ASSET = 92666701963187 -- the uploaded rooftop2.glb (Model asset "jf_rooftop2_5"); set after each upload
local hex = Color3.fromHex
local V3, CF = Vector3.new, CFrame.new
local SP = Enum.Material.SmoothPlastic
local MAT = { plastic = SP, neon = Enum.Material.Neon, glass = Enum.Material.Glass }

local function lib(): Instance return ServerStorage:WaitForChild("JankfireMeshes") end
local function layout()
	local m = ServerStorage.PolishBackup.RooftopV2Layout:Clone()
	local L = require(m)
	m:Destroy()
	return L
end

-- ---------------------------------------------------------------- the kit: one asset, sorted into models by name
function R.import(id: number?): string
	id = id or R.ASSET
	local ok, container = pcall(function() return InsertService:LoadAsset(id) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind ~= "neon"
		d.DoubleSided = false
		d:SetAttribute("Kind", kind)
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	for _, old in lib():GetChildren() do
		if old:GetAttribute("Kit") == R.KIT then old:Destroy() end
	end
	local names = {}
	for name, parts in groups do
		local m = Instance.new("Model")
		m.Name = name
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", id); m:SetAttribute("Kit", R.KIT); m:SetAttribute("FileFrame", true)
		m.Parent = lib()
		table.insert(names, ("%s %d"):format(name, #parts))
	end
	container:Destroy()
	table.sort(names)
	return ("kit %s (asset %d): %d models%s\n  %s"):format(R.KIT, id, #names, if bad > 0 then ", " .. bad .. " pieces with no name rule" else "", table.concat(names, "\n  "))
end

-- ---------------------------------------------------------------- helpers
local function folder(parent: Instance, name: string): Folder
	local f = Instance.new("Folder"); f.Name = name; f.Parent = parent
	return f
end
local function marker(parent: Instance, name: string, at: Vector3, size: Vector3?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size or V3(2, 0.2, 2); p.CFrame = CF(at); p.Parent = parent
	return p
end
local function solidPart(parent: Instance, cf: CFrame, size: Vector3, cylinder: boolean?): Part
	local p = Instance.new("Part")
	p.Name = "Solid"; p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Material = SP; p.Color = hex("8e8a83")
	if cylinder then p.Shape = Enum.PartType.Cylinder end
	p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end
local function look(parent: Instance, name: string, cf: CFrame, size: Vector3, color: Color3, mat: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Material = mat or SP; p.Color = color; p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end

-- ---------------------------------------------------------------- the city round it (plain parts, a fixed seed)
-- quiet mid greys, floor bands, a few warm lit windows; well below the arena near it (the arena's edges are sky),
-- taller further out (the backdrop). the street far below is a dark plane: falling past the kill line (y -484.8) is
-- "into the smog".
local CITY = {
	body = { hex("9da0a6"), hex("8c9096"), hex("a6a29a"), hex("7d8189"), hex("b0aca4"), hex("949089") },
	glass = { hex("5e6873"), hex("6a7179"), hex("545d68") },
	band = hex("bdb8ae"), lit = hex("f2dcc0"), street = hex("4a4d53"), block = hex("6f7076"), smog = hex("c3c7cd"),
}
local TOWERS = { "r2_twa", "r2_twb", "r2_twc", "r2_twd", "r2_twe", "r2_twf", "r2_twe", "r2_twf" }
-- three landmarks (r2_twg, a broad tower stepping in at the top), placed by hand far out, tall: { x, z, top }
local LANDMARKS = { { -430, 330, 230 }, { 470, -300, 210 }, { 60, 560, 250 } }
local TWH = 760 -- each tower design's height from its foot (tools/roblox/rooftop2_models.py, TWH)
local function city(root: Instance, O: Vector3)
	local f = folder(root, "City")
	local rng = Random.new(1602)
	look(f, "Street", CF(O + V3(0, -466, 0)), V3(2048, 2, 2048), CITY.street)
	-- the smog (the game's own word for the drop: "into the smog"): a pale layer far below the roofs, nine plates (a
	-- part is at most 2048 across), so the towers rise out of it and no edge of the ground ever shows
	for ix = -1, 1 do
		for iz = -1, 1 do
			local sm = look(f, "Smog", CF(O + V3(ix * 2048, -260, iz * 2048)), V3(2048, 1, 2048), CITY.smog)
			sm.Transparency = 0.1
		end
	end
	local n = 0
	for gx = -660, 660, 66 do
		for gz = -520, 520, 66 do
			local ax, az = math.abs(gx), math.abs(gz)
			if ax < 200 and az < 120 then continue end -- the arena's own three towers
			if rng:NextNumber() < 0.25 then continue end
			local nearMark = false
			for _, l in LANDMARKS do if math.abs(gx - l[1]) < 70 and math.abs(gz - l[2]) < 70 then nearMark = true end end
			if nearMark then continue end
			local x, z = gx + rng:NextInteger(-6, 6), gz + rng:NextInteger(-6, 6)
			local dist = math.max(ax / 1.3, az)
			-- the arena is the tallest roof near it (so its edges are sky), the city rises further out
			local top = if dist < 260 then rng:NextInteger(-170, -40) elseif dist < 420 then rng:NextInteger(-90, 20) else rng:NextInteger(-10, 150)
			if rng:NextNumber() < 0.12 and dist > 380 then top += 90 end
			local t = lib():FindFirstChild(TOWERS[rng:NextInteger(1, #TOWERS)])
			if not t then continue end
			local m = t:Clone()
			m.Name = "Tower"
			m:PivotTo(CF(O + V3(x, top - TWH, z)) * CFrame.Angles(0, rng:NextInteger(0, 3) * math.pi / 2, 0))
			m.Parent = f
			n += 1
			if n % 20 == 0 then task.wait() end
		end
	end
	for _, l in LANDMARKS do
		local t = lib():FindFirstChild("r2_twg")
		if t then
			local m = t:Clone()
			m.Name = "Landmark"
			m:PivotTo(CF(O + V3(l[1], l[3] - TWH, l[2])))
			m.Parent = f
		end
	end
	-- low blocks along the streets far below, so the drop reads as a city and not a void
	for i = 1, 90 do
		local x, z = rng:NextInteger(-700, 700), rng:NextInteger(-560, 560)
		if math.abs(x) < 170 and math.abs(z) < 80 then continue end
		local w, d, h = rng:NextInteger(20, 44), rng:NextInteger(20, 44), rng:NextInteger(20, 90)
		look(f, "Block", CF(O + V3(x, -466 + h / 2, z)), V3(w, h, d), CITY.body[rng:NextInteger(1, #CITY.body)]:Lerp(CITY.street, 0.3))
	end
	return n
end

-- ---------------------------------------------------------------- build
function R.clear(): string
	local old = workspace.Map:FindFirstChild(R.NAME)
	if old then old:Destroy() end
	for _, p in CollectionService:GetTagged("JankWater") do
		if p:IsDescendantOf(workspace) and p:GetAttribute("Arena") == R.NAME then p:Destroy() end
	end
	return "cleared"
end

function R.build(): string
	local L = layout()
	local O: Vector3 = L.origin
	R.clear()
	local root = Instance.new("Model")
	root.Name = R.NAME
	root:SetAttribute("KillY", L.killY)
	root:SetAttribute("MapId", "rooftop_v2")
	root:SetAttribute("StudsPerMetre", 3)
	root:SetAttribute("CentreX", O.X)
	root:SetAttribute("Built", os.date("!%Y-%m-%d %H:%M"))
	local shell = folder(root, "Shell")
	local solid = folder(root, "Solid")
	local pads = folder(root, "Pads")
	local spawns = folder(root, "Spawns")
	local team = folder(root, "TeamSpawns")
	local water = folder(root, "Water")
	local lights = folder(root, "Lights")
	root.Parent = workspace.Map -- (after Rooftop, so Map's first Model stays v1)
	root.WorldPivot = CF(O)
	-- the look: every model of the kit, its origin at the arena's origin
	local nm = 0
	for _, t in lib():GetChildren() do
		if t:GetAttribute("Kit") ~= R.KIT or string.sub(t.Name, 1, 5) == "r2_tw" then continue end -- (towers: city())
		local m = t:Clone()
		m:PivotTo(CF(O))
		m.Parent = shell
		nm += 1
		task.wait()
	end
	-- hit boxes
	local ns = 0
	for i, s in L.solids do
		if s[1] == "b" then
			local cf = CF(O + V3(s[2], s[3], s[4])) * CFrame.Angles(s[8], s[9], s[10])
			solidPart(solid, cf, V3(s[5], s[6], s[7]))
		else
			local h = s[6]
			local cf = CF(O + V3(s[2], s[3] + h / 2, s[4])) * CFrame.Angles(0, 0, math.pi / 2)
			solidPart(solid, cf, V3(h, s[5] * 2, s[5] * 2), true)
		end
		ns += 1
		if i % 150 == 0 then task.wait() end
	end
	-- spawn points (plain parts: SpawnLocations would join Roblox's own spawning), team spawns, pads, water
	for _, s in L.spawns do marker(spawns, s[1], O + V3(s[2], s[3] + 0.1, s[4]), V3(4, 0.2, 4)) end
	for _, s in L.team do marker(team, s[1], O + V3(s[2], s[3], s[4])) end
	for _, p in L.pads do
		local pad = Instance.new("Part")
		pad.Name = "pad"; pad.Anchored = true; pad.CanCollide = true; pad.CanQuery = true; pad.CanTouch = true
		pad.Transparency = 1; pad.Material = SP; pad.Color = hex("37d6ff"); pad.Size = V3(7.5, 0.45, 7.5)
		pad.CFrame = CF(O + V3(p[1], p[2] + 0.225, p[3]))
		pad:SetAttribute("Mat", "pad"); pad:SetAttribute("Pad", V3(p[4], p[5], p[6]))
		pad.Parent = pads
	end
	for i, w in L.water do
		local p = Instance.new("Part")
		p.Name = if i == 1 then "PoolWater" else "PoolWater" .. i
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1
		p.Size = V3(w[4], w[5], w[6]); p.CFrame = CF(O + V3(w[1], w[2], w[3]))
		p:SetAttribute("Arena", R.NAME)
		p.Parent = water
		CollectionService:AddTag(p, "JankWater")
	end
	-- lights: an invisible anchor per light
	for _, l in L.lights do
		local at = O + V3(l[2], l[3], l[4])
		local dir = V3(l[5], l[6], l[7])
		local a = marker(lights, "Light", at, V3(0.4, 0.4, 0.4))
		if dir.Magnitude > 1e-3 then a.CFrame = CFrame.lookAt(at, at + dir.Unit) end
		local li = if l[1] == "spot" then Instance.new("SpotLight") else Instance.new("PointLight")
		li.Brightness = l[8]; li.Range = l[9]; li.Color = hex(l[11]); li.Shadows = false
		if l[1] == "spot" then li.Angle = l[10]; li.Face = Enum.NormalId.Front end
		li.Parent = a
	end
	local nt = city(root, O)
	return ("built %s at %s: %d kit models, %d hit boxes, %d spawns, %d team spawns, %d pads, %d water, %d lights, %d towers"):format(
		R.NAME, tostring(O), nm, ns, #L.spawns, #L.team, #L.pads, #L.water, #L.lights, nt)
end

-- ---------------------------------------------------------------- checks
local function segHits(a: Vector3, b: Vector3, p: BasePart): boolean
	local c = p.CFrame
	local h = p.Size / 2
	if p.Shape == Enum.PartType.Cylinder then h = V3(h.X, h.Y * 0.92, h.Z * 0.92) end
	local pa, pb = c:PointToObjectSpace(a), c:PointToObjectSpace(b)
	local d = pb - pa
	local t0, t1 = 0, 1
	for _, k in { "X", "Y", "Z" } do
		local dk, pk, hk = d[k], pa[k], h[k]
		if math.abs(dk) < 1e-9 then
			if math.abs(pk) > hk then return false end
		else
			local u0, u1 = (-hk - pk) / dk, (hk - pk) / dk
			if u0 > u1 then u0, u1 = u1, u0 end
			t0, t1 = math.max(t0, u0), math.min(t1, u1)
			if t0 > t1 then return false end
		end
	end
	return true
end

function R.check(): string
	local root = workspace.Map:FindFirstChild(R.NAME)
	if not root then return "not built" end
	local solids = root.Solid:GetChildren()
	local out = {}
	local function blocked(a: Vector3, b: Vector3): boolean
		for _, p in solids do if segHits(a, b, p) then return true end end
		return false
	end
	local att, def = {}, {}
	for _, s in root.TeamSpawns:GetChildren() do table.insert(if s.Name == "att" then att else def, s.Position) end
	local open, n = 0, 0
	for _, a in att do for _, b in def do
		for _, h in { 2.5, 4.6 } do
			n += 1
			if not blocked(a + V3(0, h, 0), b + V3(0, h, 0)) then open += 1 end
		end
	end end
	table.insert(out, ("team spawn sight lines open: %d of %d"):format(open, n))
	-- clear space over every spawn
	local bad = {}
	for _, f in { root.Spawns, root.TeamSpawns } do
		for _, s in f:GetChildren() do
			local params = OverlapParams.new()
			params.FilterType = Enum.RaycastFilterType.Include
			params.FilterDescendantsInstances = { root.Solid }
			local hits = workspace:GetPartBoundsInBox(CF(s.Position + V3(0, 3, 0)), V3(2, 5, 2), params)
			if #hits > 0 then table.insert(bad, s.Name) end
		end
	end
	table.insert(out, "spawn points blocked: " .. (if #bad > 0 then table.concat(bad, ", ") else "none"))
	-- kill line below every hit box top that you could fall from
	local lowest = math.huge
	for _, p in solids do lowest = math.min(lowest, p.Position.Y - p.Size.Y / 2) end
	table.insert(out, ("lowest hit box bottom y %.1f, KillY %.1f"):format(lowest, root:GetAttribute("KillY")))
	-- pad flights with the game's gravity
	for _, pad in root.Pads:GetChildren() do
		local v: Vector3 = pad:GetAttribute("Pad")
		local pos, t, landed = pad.Position + V3(0, 3, 0), 0, nil
		while t < 3 do
			local nxt = pos + v / 60
			v -= V3(0, workspace.Gravity / 60, 0)
			t += 1 / 60
			for _, p in solids do
				if segHits(pos - V3(0, 2.6, 0), nxt - V3(0, 2.6, 0), p) then landed = nxt; break end
			end
			pos = nxt
			if landed then break end
		end
		local rel = (landed or pos) - root:GetPivot().Position
		table.insert(out, ("pad at %s lands at (%.1f, %.1f, %.1f) after %.2f s"):format(tostring(pad.Position - root:GetPivot().Position), rel.X, rel.Y - 2.6, rel.Z, t))
	end
	return table.concat(out, "\n")
end

-- ---------------------------------------------------------------- the switch
function R.use(which: string): string
	local name = if which == "v2" or which == R.NAME then R.NAME else "Rooftop"
	if name == R.NAME and not workspace.Map:FindFirstChild(R.NAME) then return "v2 is not built" end
	workspace.Map:SetAttribute("Arena", name)
	return "matches now use " .. name
end

return R
