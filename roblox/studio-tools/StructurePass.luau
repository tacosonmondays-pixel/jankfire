--!nocheck
-- STRUCTURE PASS (15 Nov 2026): the things three judges said paint could not fix on the Rooftop and in the playground.
-- it ADDS things (the serious pass only repainted): plant and cover on the two spawn roofs, window grids and crowns on
-- the towers round the arena, a furnished penthouse, new cabanas, a designed playground. everything it adds lives in a
-- folder called Dress (Map.Rooftop.Dress, Hub.Playground.Dress, ...), so it can be rebuilt or taken away as one thing,
-- and PolishBackup.SeriousPass skips those folders. the kits are Blender models (tools/roblox/*_models.py > one .glb
-- per kit > one Model asset); S.import brings a kit into ServerStorage.JankfireMeshes as templates.
-- run in Edit, from a clone (a require of the original is cached):
--   local S = require(game.ServerStorage.PolishBackup.StructurePass:Clone())
--   S.import("roofdress")   one kit by name (S.KITS), or S.import() for all
--   S.rooftop()  S.skyline()  S.lounge()  S.cabanas()  S.playground()  S.small()     each rebuilds its own part
--   S.all()      everything           S.clear("rooftop")   take one part away again (hidden boxes come back)
-- colours: the serious pass's palette. neutral greys, warm white light, one amber accent, red only for danger.
local ServerStorage = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")

local S = {}
local hex = Color3.fromHex
local V3, CF = Vector3.new, CFrame.new
local SP, CONC, NEON = Enum.Material.SmoothPlastic, Enum.Material.Concrete, Enum.Material.Neon
local WARM, AMBER, AMBERGLOW, TRIM, GRAPH, DARK, BOARD = hex("f2dcc0"), hex("d6a738"), hex("f0c468"), hex("c9c7c1"), hex("4d515a"), hex("34363d"), hex("16181d")
local LAMPLIGHT = Color3.fromRGB(255, 214, 170)

-- the kits: name > the Model asset made from tools/roblox/<name>_models.py
S.KITS = {
	roofdress = 137202955761678,
	lounge = 104158042477813,
	playground = 116399697029561,
}
-- (cloth is flat too: Roblox's Fabric weave is big and harsh on a sofa or a tent, the kind of noise the serious pass took out)
local MAT = {
	plastic = SP, concrete = CONC, neon = NEON, glass = Enum.Material.Glass, fabric = SP, wood = Enum.Material.Wood,
}

local function lib(): Instance return ServerStorage:WaitForChild("JankfireMeshes") end
local function roof(): Instance return workspace:WaitForChild("Map"):WaitForChild("Rooftop") end
local function hub(): Instance return workspace:WaitForChild("Map"):WaitForChild("Hub") end

-- ---------------------------------------------------------------- bringing a kit in
-- one asset holds every model of a kit: a piece is called "<model><n>__<kind>_<hex>", so the pieces are sorted into
-- models by name and painted from it (an upload loses its colours). the exporter turns the pieces before export
-- (rbxglb.turn_for_roblox), so they arrive in the kit's own frame: a template's pivot is the kit's origin (the middle
-- of its footprint, on the floor), its front is +Z
function S.import(which: string?): string
	local out = {}
	for kit, id in S.KITS do
		if which and kit ~= which then continue end
		local ok, container = pcall(function() return InsertService:LoadAsset(id) end)
		if not ok or not container then table.insert(out, kit .. " LOAD FAILED " .. tostring(container)); continue end
		local groups, bad = {}, 0
		for _, d in container:GetDescendants() do
			if not d:IsA("MeshPart") then continue end
			local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
			if not model or not MAT[kind] then bad += 1; continue end
			d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
			d.Transparency = if kind == "glass" then 0.35 else 0
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.CastShadow = kind ~= "neon" and kind ~= "glass"
			d:SetAttribute("Kind", kind)
			groups[model] = groups[model] or {}
			table.insert(groups[model], d)
		end
		local names = {}
		for name, parts in groups do
			local m = Instance.new("Model")
			m.Name = name
			for _, p in parts do p.Parent = m end
			m.WorldPivot = CFrame.identity
			m:SetAttribute("AssetId", id); m:SetAttribute("Kit", kit); m:SetAttribute("FileFrame", true)
			local old = lib():FindFirstChild(name)
			if old then old:Destroy() end
			m.Parent = lib()
			local _, size = m:GetBoundingBox()
			table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(name, #parts, size.X, size.Y, size.Z))
		end
		container:Destroy()
		table.sort(names)
		table.insert(out, kit .. ": " .. #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  "))
		task.wait()
	end
	return table.concat(out, "\n")
end

-- ---------------------------------------------------------------- helpers every part of the pass uses
local function folder(parent: Instance, name: string): Folder
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
-- a fresh, empty sub-folder of a Dress folder (what was there is thrown away: every part of the pass rebuilds itself)
local function fresh(dress: Instance, name: string): Folder
	local old = dress:FindFirstChild(name)
	if old then old:Destroy() end
	local f = Instance.new("Folder"); f.Name = name; f.Parent = dress
	return f
end
-- one copy of a template, its origin (floor, middle) at cf
local function put(name: string, cf: CFrame, parent: Instance, label: string?): Model?
	local t = lib():FindFirstChild(name)
	if not t then warn("StructurePass: no template " .. name); return nil end
	local m = t:Clone()
	m:PivotTo(cf)
	m.Name = label or name
	m.Parent = parent
	return m
end
-- a look-only box
local function slab(parent: Instance, name: string, cf: CFrame, size: Vector3, color: Color3, mat: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Material = mat or SP; p.Color = color; p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end
-- a box you cannot see that stops players and shots (the map's line-of-sight rays read CanQuery)
local function solid(parent: Instance, cf: CFrame, size: Vector3, wedge: boolean?): BasePart
	local p = Instance.new(if wedge then "WedgePart" else "Part")
	p.Name = "DressSolid"; p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Material = CONC; p.Color = hex("8b8984"); p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end
-- hide one of the map's own boxes behind a model (it stays solid); S.clear shows it again
local function hide(p: BasePart)
	if p:GetAttribute("DressHid") == nil then p:SetAttribute("DressHid", p.Transparency) end
	p.Transparency = 1
end
local function unhideAll(root: Instance)
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("DressHid") ~= nil then
			d.Transparency = d:GetAttribute("DressHid"); d:SetAttribute("DressHid", nil)
		end
	end
end
-- the map's own box of a given name nearest a point (they have no ids)
local function boxAt(root: Instance, name: string, at: Vector3, tol: number?): BasePart?
	local best, bd = nil, tol or 2
	for _, d in root:GetChildren() do
		if d:IsA("BasePart") and d.Name == name then
			local dist = (d.Position - at).Magnitude
			if dist < bd then best, bd = d, dist end
		end
	end
	return best
end
local function spot(parent: BasePart, face: Enum.NormalId, brightness: number, range: number, angle: number): SpotLight
	local l = Instance.new("SpotLight")
	l.Face = face; l.Brightness = brightness; l.Range = range; l.Angle = angle; l.Color = LAMPLIGHT; l.Shadows = false; l.Parent = parent
	return l
end
local function glowPart(m: Instance): BasePart?
	for _, d in m:GetDescendants() do if d:IsA("BasePart") and d.Material == NEON then return d end end
	return nil
end

-- ---------------------------------------------------------------- the two spawn roofs
-- everything is laid out for the WEST roof (x < 0) and mirrored onto the east one (x > -x, yaw > -yaw, and the mirrored
-- model where a piece is not the same both ways round), so cover and sight lines are the same at both ends. kept clear
-- on both: every TeamSpawn and Spawn (and the mirror of each), the jump pads and their flight, the stair heads, the
-- catwalk mouth. s = the boxes that make a piece solid, in the piece's own frame: { x, y, z, sx, sy, sz, wedge? }
local DECK = {
	-- the chiller stands 5.8 studs north of the lift hut: a lane between them, cover for whoever comes off the catwalk
	{ "rt_chiller", -116, -25, 0, m = true, s = { { 0, 3.5, 0, 20.4, 7.0, 8.4 } } },
	-- vents against the hut's south wall
	{ "rt_vents", -122, 19.1, 0, m = true, s = { { 0, 0.4, 0, 8, 0.8, 8 }, { -1.7, 4.1, 1.5, 3.4, 6.6, 3.4 }, { -1.7, 7.0, 1.5, 4.6, 1.4, 4.6 },
		{ 2.3, 3.1, -2.0, 3.0, 4.6, 3.0 }, { 2.3, 3.05, 2.2, 3.2, 4.5, 3.2 }, { -2.5, 4.9, -2.5, 1.6, 8.2, 1.6 } } },
	-- a ridge skylight over the map's flat glass slab, a roof fan over the low metal box beside it
	{ "rt_skylight", -114, 33, 0, s = { { 0, 2.25, 0, 7.6, 1.5, 11.2 } }, over = { "glass", -114, 0.8, 33 } },
	{ "rt_cowl", -102, 34.5, 0, s = { { 0, 2.2, 0, 6, 4.4, 6 } }, over = { "metal", -102, 0.9, 34.5 } },
	-- the stair head fills the north-west corner (the loose metal cube there is inside it now); its door faces the roof
	{ "rt_stairhead", -166.2, -45.3, 0, m = true, s = { { 0, 3.7, 0, 14, 7.4, 16 }, { 0, 8.7, 0, 14, 2.6, 16, true } }, over = { "metal", -168, 1.4, -48 } },
	{ "rt_duct", -171.9, -28.5, 90, s = { { 0, 1.5, 0, 16, 3.0, 2.4 } } },
	{ "rt_tank", -141, -50.5, 0, m = true, s = { { 0, 2.7, 0, 10, 5.4, 4.8 } } },
	-- one long barrel rooflight along the south edge (three domes in a row read as copy and paste)
	{ "rt_barrel", -146, 48, 0, s = { { 0, 1.2, 0, 15, 2.4, 5 } } },
	-- after the first judging ("from the spawn the bottom half of the picture is still bare paving, and the hut is the
	-- only thing that stands up"): a second plant group on a kerbed plinth north of the spawns, round the map's own two
	-- AC cubes (a roof fan and three flues, the tall thing), and a waist-high duct that turns a corner south of them.
	-- both are well off the spawns (8 studs and more) and off where the low pads land (-129, -32 and -119, 44)
	{ "rt_plinth", -148.5, -30, 0, s = { { 0, 0.5, 0, 22, 1.0, 12 } } },
	{ "rt_cowl", -148.5, -30, 0, y = 1, s = { { 0, 2.2, 0, 6, 4.4, 6 } } },
	{ "rt_stack", -141.5, -31, 0, y = 1, m = true, s = { { -0.1, 5.6, 0.2, 5, 11.2, 5 } } },
	{ "rt_ductL", -144, 21.5, 0, m = true, s = { { 0, 1.5, 0, 12, 3.0, 2.4 }, { 6, 1.5, 4, 2.4, 3.0, 8 } } },
}
-- the parapet of one spawn roof (west): { x, z, length, along } per run, and where the piers stand
local PARAPET = {
	{ -132, -54.6, 86.4, "x" }, { -132, 54.6, 86.4, "x" }, { -174.6, 0, 108, "z" },
	{ -89.4, -51, 6, "z" }, { -89.4, -27.8, 16.5, "z" }, { -89.4, 13.5, 42, "z" }, { -89.4, 50.2, 7.5, "z" },
}
local PIERS = { -- { x, z, along, lit }: lit = a real light (the gate posts of each way off the roof, and the corners)
	{ -174.6, -54.6, "x", true }, { -174.6, 54.6, "x", true }, { -89.4, -54.6, "x", true }, { -89.4, 54.6, "x", true },
	{ -174.6, -18, "z" }, { -174.6, 0, "z" }, { -174.6, 18, "z" }, { -174.6, 36, "z" },
	{ -157.5, -54.6, "x" }, { -140, -54.6, "x" }, { -122.5, -54.6, "x" }, { -105, -54.6, "x" },
	{ -157.5, 54.6, "x" }, { -140, 54.6, "x" }, { -122.5, 54.6, "x" }, { -105, 54.6, "x" },
	{ -89.4, -49.2, "z", true }, { -89.4, -34.85, "z", true }, { -89.4, -20.75, "z", true }, { -89.4, -6.3, "z", true },
	{ -89.4, 33.3, "z", true }, { -89.4, 47.65, "z", true },
}
-- lamps on the lift hut's walls (the hut is x -126..-108, z -15..15): { x, y, z, yaw }
local HUTLAMPS = {
	{ -126.6, 9.5, -10.5, -90 }, { -126.6, 9.5, 10.5, -90 }, { -107.4, 9.5, -8, 90 }, { -107.4, 9.5, 8, 90 },
	{ -117, 9.5, -15.6, 180 }, { -112.5, 9.5, 15.6, 0 },
}
-- paint on the deck: walkway bands { x0, x1, z0, z1 }, their edge lines, amber thresholds and brackets
local WALK = { { -130.4, -126.4, -44, 44.5 }, { -126.4, -89.9, -44, -40 }, { -126.4, -89.9, -20, -16 }, { -126.4, -89.9, 40.5, 44.5 } }
local LINES = { -- { x0, z0, x1, z1 }
	{ -130.4, -44, -130.4, 44.5 }, { -126.4, -40, -126.4, -20 }, { -126.4, -16, -126.4, 40.5 },
	{ -130.4, -44, -89.9, -44 }, { -126.4, -40, -89.9, -40 }, { -126.4, -20, -89.9, -20 }, { -126.4, -16, -89.9, -16 },
	{ -126.4, 40.5, -89.9, 40.5 }, { -130.4, 44.5, -89.9, 44.5 },
}
local THRESHOLDS = { { -90.3, -48, -36 }, { -90.3, -19.5, -7.5 }, { -90.3, 34.5, 46.5 } } -- { x, z0, z1 }

local function deckSide(dress: Instance, side: number)
	local name = if side < 0 then "West" else "East"
	local f = fresh(dress, name)
	local R = roof()
	local solidRoot = R:WaitForChild("Solid")
	-- (side -1 is the west roof as written; side +1 flips x and yaw)
	local function at(x: number, y: number, z: number, yawDeg: number): CFrame
		return CF(-side * x, y, z) * CFrame.Angles(0, math.rad(-side * yawDeg), 0)
	end
	local plant = Instance.new("Folder"); plant.Name = "Plant"; plant.Parent = f
	local solids = Instance.new("Folder"); solids.Name = "Solids"; solids.Parent = f
	for _, d in DECK do
		local model = if d.m and side > 0 then d[1] .. "M" else d[1]
		local cf = at(d[2], d.y or 0, d[3], d[4])
		local m = put(model, cf, plant, d[1])
		for _, b in d.s or {} do
			local lx = if side > 0 then -b[1] else b[1]
			solid(solids, cf * CF(lx, b[2], b[3]), V3(b[4], b[5], b[6]), b[7])
		end
		if d.over then
			local box = boxAt(solidRoot, d.over[1], V3(-side * d.over[2], d.over[3], d.over[4]))
			if box then hide(box) else warn("StructurePass: no box " .. d.over[1] .. " to hide for " .. d[1]) end
		end
		if m and d[1] == "rt_skylight" then
			local g = glowPart(m)
			if g then
				local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = 0.9; l.Range = 14; l.Shadows = false; l.Parent = g
			end
		elseif m and d[1] == "rt_stairhead" then
			local g = glowPart(m)
			if g then spot(g, Enum.NormalId.Bottom, 1.6, 18, 110) end
		end
	end
	-- the parapet: a pale coping along every run, piers with marker lamps
	local edge = Instance.new("Folder"); edge.Name = "Parapet"; edge.Parent = f
	for _, p in PARAPET do
		local m = put("rt_coping", at(p[1], 2.86, p[2], if p[4] == "x" then 0 else 90), edge)
		if m then
			local part = m:FindFirstChildWhichIsA("MeshPart")
			local cf = part.CFrame
			part.Size = V3(p[3] + 0.3, part.Size.Y, part.Size.Z)
			part.CFrame = cf
		end
	end
	for _, p in PIERS do
		local m = put("rt_pier", at(p[1], 0, p[2], if p[3] == "x" then 0 else 90), edge)
		local g = m and glowPart(m)
		if g and p[4] then
			local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = 0.7; l.Range = 11; l.Shadows = false; l.Parent = g
		elseif m then
			-- a lamp only on the corners and the gate posts (one on every pier read as a row of black pucks from above)
			for _, d in m:GetChildren() do
				if d:IsA("BasePart") and (d.Material == NEON or d.Color == DARK) then d:Destroy() end
			end
		end
	end
	-- the lift hut: lamps on its walls, and a readable LIFT sign over the white-on-white one
	local hut = Instance.new("Folder"); hut.Name = "Hut"; hut.Parent = f
	for _, l in HUTLAMPS do
		local m = put("rt_walllamp", at(l[1], l[2], l[3], l[4]), hut)
		local g = m and glowPart(m)
		if g then spot(g, Enum.NormalId.Bottom, 1.5, 20, 115) end
	end
	local sign = put("rt_liftsign", at(-126.52, 8.48, 0, -90), hut)
	if sign then
		local face = slab(hut, "LiftSignFace", at(-126.72, 9.42, 0, 90), V3(4.5, 1.46, 0.04), BOARD)
		face.Transparency = 1
		local g = Instance.new("SurfaceGui")
		g.Name = "Sign"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 60
		g.LightInfluence = 0; g.Brightness = 1; g.Parent = face
		local back = Instance.new("Frame")
		back.BackgroundColor3 = BOARD; back.BorderSizePixel = 0; back.Size = UDim2.fromScale(1, 1); back.Parent = g
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(0.86, 0.8); t.Position = UDim2.fromScale(0.07, 0.1); t.Text = "LIFT"; t.TextScaled = true
		t.FontFace = Font.new("rbxasset://fonts/families/BuilderExtended.json", Enum.FontWeight.Bold)
		t.TextColor3 = hex("f0f2f5"); t.Parent = g
	end
	-- paint on the deck: walkways from the hut to every way off the roof, amber where a step or a launch is
	local floor = Instance.new("Folder"); floor.Name = "Floor"; floor.Parent = f
	for _, w in WALK do
		slab(floor, "Walk", CF(-side * (w[1] + w[2]) / 2, 0.16, (w[3] + w[4]) / 2), V3(math.abs(w[2] - w[1]), 0.32, math.abs(w[4] - w[3])), hex("7c7f87"), CONC)
	end
	for _, l in LINES do
		local a, b = V3(-side * l[1], 0.2, l[2]), V3(-side * l[3], 0.2, l[4])
		local len = (b - a).Magnitude
		local alongX = math.abs(b.X - a.X) > math.abs(b.Z - a.Z)
		slab(floor, "Line", CF((a + b) / 2), if alongX then V3(len + 0.5, 0.42, 0.5) else V3(0.5, 0.42, len + 0.5), hex("a9abaf"), CONC)
	end
	for _, t in THRESHOLDS do
		slab(floor, "Threshold", CF(-side * t[1], 0.05, (t[2] + t[3]) / 2), V3(0.8, 0.1, t[3] - t[2]), AMBER)
	end
	local function brackets(cx: number, cz: number, hx: number, hz: number, len: number, color: Color3)
		for _, sx in { -1, 1 } do for _, sz in { -1, 1 } do
			local x, z = -side * cx + sx * hx, cz + sz * hz
			slab(floor, "Bracket", CF(x - sx * len / 2, 0.05, z), V3(len, 0.1, 0.45), color)
			slab(floor, "Bracket", CF(x, 0.05, z - sz * len / 2), V3(0.45, 0.1, len), color)
		end end
	end
	brackets(-150, 0, 18, 20, 7, AMBER) -- the muster box round the team's spawns
	brackets(-100.5, 21, 6.2, 6.2, 3, AMBER) -- the jump pad
	-- east roof only: the wooden shed in its south corner becomes a plant room (same box, so no cover changes)
	if side > 0 then
		put("rt_kiosk", CF(165, 0, 47.4) * CFrame.Angles(0, math.pi, 0), plant)
		for _, o in { { "wood", V3(165, 3.9, 47.4) }, { "roofpink", V3(165, 8.1, 47.4) } } do
			local box = boxAt(solidRoot, o[1], o[2])
			if box then hide(box) else warn("StructurePass: no " .. o[1] .. " box for the kiosk") end
		end
		-- and its three plain benches along the east edge become loungers (same boxes)
		for _, o in { { "white", -13.8 }, { "white", -22.8 }, { "toyteal", 13.2 } } do
			local box = boxAt(solidRoot, o[1], V3(167.7, 0.7, o[2]))
			if box and lib():FindFirstChild("rt_daybed") then
				local m = put("rt_daybed", CF(167.7, 0, o[2]), plant, "Lounger")
				if m then m:ScaleTo(0.74) end
				hide(box)
			end
		end
	end
	-- the plant's pale paint a step greyer: in the low sun c9c7c1 and 9a9da3 read as white (second judging)
	for _, d in plant:GetDescendants() do
		if d:IsA("BasePart") then
			if d.Color == TRIM then d.Color = hex("a9aaad") elseif d.Color == hex("9a9da3") then d.Color = hex("868990") end
		end
	end
	return f
end

function S.rooftop(): string
	local dress = folder(roof(), "Dress")
	local w = deckSide(dress, -1)
	task.wait()
	local e = deckSide(dress, 1)
	return ("rooftop: west %d things, east %d things"):format(#w:GetDescendants(), #e:GetDescendants())
end

-- ---------------------------------------------------------------- the penthouse: a lounge
-- most pieces stand over one of the map's own boxes (the box stays the collision and is hidden), so the cover in the
-- arena's middle is what it was. new and solid: a pool table on the map's centre line and a low table in front of
-- each upstairs sofa (a mirrored pair). rugs and lights are look-only.
local function overBoxes(solidRoot: Instance, list: { { any } })
	for _, o in list do
		local box = boxAt(solidRoot, o[1], V3(o[2], o[3], o[4]), 1.2)
		if box then hide(box) else warn(("StructurePass: no %s box at %.1f %.1f %.1f"):format(o[1], o[2], o[3], o[4])) end
	end
end
local function lampOn(m: Model?, kind: string, brightness: number, range: number)
	local g = m and glowPart(m)
	if not g then return end
	g.Color = hex("e6cfa8") -- (f2dcc0 read as a white slab from below)
	-- (shadows on: the lamp's own housing then keeps its light off the ceiling, where it showed as a warm smear)
	if kind == "spot" then spot(g, Enum.NormalId.Bottom, brightness, range, 130).Shadows = true
	else
		local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = brightness; l.Range = range; l.Shadows = true; l.Parent = g
	end
end

function S.lounge(): string
	local dress = folder(roof(), "Dress")
	local f = fresh(dress, "Lounge")
	local solidRoot = roof():WaitForChild("Solid")
	local PI = math.pi
	local UP, LOW = 0, -11.75 -- the two floors' tops
	local CEIL_UP, CEIL_LOW = 10.7, -0.85
	-- upstairs
	put("ph_sofa", CF(-10.5, UP, 12.775) * CFrame.Angles(0, PI, 0), f)
	put("ph_sofa", CF(9.9, UP, 12.775) * CFrame.Angles(0, PI, 0), f)
	put("ph_planter", CF(0, UP, -16.5), f)
	put("ph_pot", CF(-27.9, UP, -27.9), f)
	put("ph_pot", CF(-27.9, UP, 15.9) * CFrame.Angles(0, 2, 0), f)
	overBoxes(solidRoot, {
		{ "toypink", -10.5, 0.7, 12 }, { "toypink", -10.5, 2.2, 14.6 }, { "toypink", 9.9, 0.7, 12 }, { "toypink", 9.9, 2.2, 14.6 },
		{ "wood", 0, 1.3, -16.5 }, { "lawn", 0, 2.6, -16.5 }, { "pottery", -27.9, 1.2, -27.9 }, { "pottery", -27.9, 1.2, 15.9 },
	})
	-- a second group on the north side (it was an empty, cold half): a long sideboard with a lamp against the glass each
	-- side of the door, two tub chairs before each. a mirrored pair, and solid
	for _, sx in { -1, 1 } do
		local c = put("ph_console", CF(sx * 17, UP, -27.9), f)
		solid(f, CF(sx * 17, UP + 1.15, -27.9), V3(16.2, 2.3, 2.4))
		local cg = c and glowPart(c)
		if cg then
			local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = 0.8; l.Range = 12; l.Shadows = false; l.Parent = cg
		end
		for _, x in { 14, 20 } do
			put("ph_tub", CF(sx * x, UP, -22.6) * CFrame.Angles(0, PI, 0), f)
			solid(f, CF(sx * x, UP + 1.2, -22.6), V3(2.8, 2.4, 2.8))
		end
	end
	put("ph_pooltable", CF(0, UP, -3), f)
	solid(f, CF(0, UP + 1.5, -3), V3(9, 3, 5))
	for _, sx in { -1, 1 } do
		put("ph_coffee", CF(sx * 7.5, UP, 6.6), f)
		solid(f, CF(sx * 7.5, UP + 0.65, 6.6), V3(7, 1.3, 3.2))
		slab(f, "Rug", CF(sx * 9.6, UP + 0.035, 8.2), V3(17, 0.07, 9.5), hex("77736d"))
		slab(f, "RugEdge", CF(sx * 9.6, UP + 0.03, 8.2), V3(17.8, 0.06, 10.3), hex("b9b5ab"))
		lampOn(put("ph_raft", CF(sx * 9.6, CEIL_UP, 8.4), f), "spot", 1.7, 20)
	end
	lampOn(put("ph_raft", CF(0, CEIL_UP, -3), f), "spot", 1.9, 20)
	-- downstairs
	put("ph_bar", CF(-16.5, LOW, -26.5), f)
	overBoxes(solidRoot, { { "wood", -16.5, -10.1, -26.5 }, { "chrome", -16.5, -8.3, -24.6 } })
	for _, x in { -9.9, -14.4, -18.9, -23.4 } do
		put("ph_stool", CF(x, LOW, -21.5), f)
		overBoxes(solidRoot, { { "metal", x, -10.4, -21.5 } })
	end
	for _, t in { { -18, 1.5 }, { -4.5, 7.5 }, { 9, 0 } } do
		put("ph_table", CF(t[1], LOW, t[2]), f)
		-- two tub chairs at each standing table (the room was two tables with no seats)
		for _, sx in { -1, 1 } do
			put("ph_tub", CF(t[1] + sx * 3.9, LOW, t[2]) * CFrame.Angles(0, -sx * PI / 2, 0), f)
			solid(f, CF(t[1] + sx * 3.9, LOW + 1.2, t[2]), V3(2.8, 2.4, 2.8))
		end
		overBoxes(solidRoot, { { "wood", t[1], -10.5, t[2] }, { "chrome", t[1], -9.1, t[2] } })
	end
	for _, sx in { -1, 1 } do
		put("ph_sofalow", CF(sx * 18.8, LOW, 15.7) * CFrame.Angles(0, PI, 0), f)
		overBoxes(solidRoot, { { "toypink", sx * 18.8, -11, 15.7 }, { "toypink", sx * 18.8, -9.6, 16.9 } })
	end
	put("ph_cabinet", CF(27.5, LOW, -27) * CFrame.Angles(0, -PI / 2, 0), f)
	overBoxes(solidRoot, { { "toypurple", 27.5, -9, -27 } })
	slab(f, "Rug", CF(-4.5, LOW + 0.035, 3.75), V3(35, 0.07, 15.5), hex("585b64"))
	slab(f, "RugEdge", CF(-4.5, LOW + 0.03, 3.75), V3(35.8, 0.06, 16.3), hex("72757d"))
	-- (a spot pointing down, not a point light: a point light this close under the ceiling smeared a warm streak on it)
	lampOn(put("ph_ring", CF(-4.5, CEIL_LOW, 3.75), f), "spot", 1.6, 22)
	lampOn(put("ph_raft", CF(-16.5, CEIL_LOW, -24.2), f), "spot", 1.3, 18)
	-- a warm cove strip round the edge of both ceilings, in short lengths, each with a soft light, so the ceilings, the
	-- far walls and the stairs are lit (both floors were black above head height); the rafts throw a little light up too
	local cove = Instance.new("Folder"); cove.Name = "Cove"; cove.Parent = f
	for _, y in { CEIL_UP - 0.3, CEIL_LOW - 0.3 } do
		local runs = { -- { x0, z0, x1, z1 } inside the glass
			{ -28.8, -29.2, 28.8, -29.2 }, { -28.8, 17.2, 28.8, 17.2 }, { -29.2, -28.8, -29.2, 16.8 }, { 29.2, -28.8, 29.2, 16.8 },
		}
		for _, r in runs do
			local a, b = V3(r[1], y, r[2]), V3(r[3], y, r[4])
			local len = (b - a).Magnitude
			local n = math.max(2, math.floor(len / 14 + 0.5))
			for i = 0, n - 1 do
				local p0, p1 = a:Lerp(b, i / n), a:Lerp(b, (i + 1) / n)
				local alongX = math.abs(r[3] - r[1]) > 1
				local seg = slab(cove, "Cove", CF((p0 + p1) / 2), if alongX then V3((p1 - p0).Magnitude - 0.6, 0.3, 0.4) else V3(0.4, 0.3, (p1 - p0).Magnitude - 0.6), hex("e6cfa8"), NEON)
				local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = 0.55; l.Range = 13; l.Shadows = false; l.Parent = seg
			end
		end
	end
	for _, m in f:GetChildren() do
		local g = m.Name == "ph_raft" and glowPart(m)
		if g then
			local up = Instance.new("SpotLight"); up.Face = Enum.NormalId.Top; up.Angle = 120; up.Range = 9; up.Brightness = 0.5
			up.Color = LAMPLIGHT; up.Shadows = false; up.Parent = g
		end
	end
	return "lounge: " .. #f:GetDescendants() .. " things"
end

-- ---------------------------------------------------------------- the pool deck: four new cabanas
-- the pool deck model had its cabanas baked in (flat cloth cut-outs), so the model itself is swapped for one with the
-- cabanas cut away (tools/roblox/cut_cabanas.py, then export_models.py): S.pooldeck() brings it in. the old template is
-- kept in PolishBackup.StructureBackup; the new pieces take their paint from the old ones by name.
S.POOLDECK = 116688327933923
function S.pooldeck(): string
	local old = lib():FindFirstChild("arch_pooldeck")
	if not old then return "pooldeck: there is no arch_pooldeck template" end
	if old:GetAttribute("NoCabanas") then
		if old:GetAttribute("Facing") ~= 3 then -- (an import from before the frame fix below)
			local part = old:FindFirstChildWhichIsA("BasePart")
			local centre = old:GetBoundingBox().Position
			old.WorldPivot = CF(centre) * (part.CFrame - part.Position) * CFrame.Angles(0, math.pi, 0)
			old:SetAttribute("Facing", 3)
			return "pooldeck: the model without cabanas, its frame turned the right way round"
		end
		return "pooldeck: already the model without cabanas"
	end
	local ok, container = pcall(function() return InsertService:LoadAsset(S.POOLDECK) end)
	if not ok or not container then return "pooldeck: LOAD FAILED " .. tostring(container) end
	local m = Instance.new("Model"); m.Name = "arch_pooldeck"
	local n, unpainted = 0, {}
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local o = old:FindFirstChild(d.Name, true)
		if o and o:IsA("BasePart") then
			d.Color = o.Color; d.Material = o.Material; d.Transparency = o.Transparency; d.Reflectance = o.Reflectance; d.CastShadow = o.CastShadow
			d.MaterialVariant = o.MaterialVariant
			if o:IsA("MeshPart") and d.TextureID == "" and o.TextureID ~= "" then d.TextureID = o.TextureID end
			for k, v in o:GetAttributes() do d:SetAttribute(k, v) end
		else table.insert(unpainted, d.Name) end
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.Parent = m; n += 1
	end
	container:Destroy()
	if n == 0 then m:Destroy(); return "pooldeck: the asset had no meshes" end
	-- an upload arrives turned half way round its up axis, and MeshSwap reads a template's pieces in the frame of the
	-- template's own box (GetBoundingBox, which follows the model's pivot). so the FRAME is turned, by giving the model
	-- a pivot half a turn from its pieces, exactly as the old template sits. (turning the pieces of a model that has no
	-- pivot of its own turns its box with them and changes nothing: the DJ booth stayed at the penthouse end, twice)
	local centre = m:GetBoundingBox().Position
	m.WorldPivot = CF(centre) * CFrame.Angles(0, math.pi, 0)
	m:SetAttribute("NoCabanas", true); m:SetAttribute("AssetId", S.POOLDECK); m:SetAttribute("Facing", 3)
	local _, size = m:GetBoundingBox()
	local _, osize = old:GetBoundingBox()
	if (size - osize).Magnitude > 0.05 then
		m:Destroy()
		return ("pooldeck: REFUSED, the new model's box is %s and the old one's %s (MeshSwap fits by that box)"):format(tostring(size), tostring(osize))
	end
	local bak = folder(ServerStorage:WaitForChild("PolishBackup"), "StructureBackup")
	if bak:FindFirstChild("arch_pooldeck") then old:Destroy() else old.Parent = bak end
	m.Parent = lib()
	return ("pooldeck: %d pieces, box %.2f x %.2f x %.2f%s"):format(n, size.X, size.Y, size.Z, if #unpainted > 0 then ", NOT PAINTED: " .. table.concat(unpainted, ", ") else "")
end

function S.cabanas(): string
	local t = lib():FindFirstChild("arch_pooldeck")
	if not (t and t:GetAttribute("NoCabanas")) then return "cabanas: run S.pooldeck() first (the old cabanas are still in the pool deck model)" end
	local dress = folder(roof(), "Dress")
	local f = fresh(dress, "Cabanas")
	local FLOOR = -12
	for _, c in { { -48, 27 }, { 48, 27 }, { -48, 73.5 }, { 48, 73.5 } } do
		local cx, cz = c[1], c[2]
		local sx, sz = math.sign(cx), if cz < 50 then -1 else 1
		local m = put("rt_cabana", CF(cx, FLOOR, cz), f)
		lampOn(m, "point", 0.9, 15)
		-- its two padded sides stand where the map's cloth walls are (the outer sides), its daybed on the map's daybed
		put("rt_cabwall", CF(cx, FLOOR, cz + sz * 5.7), f)
		put("rt_cabwall", CF(cx + sx * 5.7, FLOOR, cz) * CFrame.Angles(0, math.pi / 2, 0), f)
		put("rt_daybed", CF(cx, FLOOR, cz) * CFrame.Angles(0, if sx > 0 then math.pi else 0, 0), f)
	end
	return "cabanas: " .. #f:GetDescendants() .. " things"
end

-- ---------------------------------------------------------------- small things
-- the two tents in the training hall: their white patterned canvas and red rug are pictures baked on the mesh, so a new
-- plain tent stands in their place (the old pieces are hidden, not removed)
function S.small(): string
	local tg = hub():WaitForChild("TrainingGround")
	local dress = folder(tg, "Dress")
	local f = fresh(dress, "Tents")
	local n = 0
	for _, d in tg:GetDescendants() do
		if d:IsA("Model") and (d.Name == "RangeTent" or d.Name == "HQTent") and not d:IsDescendantOf(dress) then
			local cf, size = d:GetBoundingBox()
			local m = put("tr_tent", CF(cf.Position.X, cf.Position.Y - size.Y / 2, cf.Position.Z) * cf.Rotation, f, d.Name)
			if m then
				m:ScaleTo(math.clamp(size.X / 12.4, 0.8, 1.3))
				for _, p in m:GetDescendants() do
					if p:IsA("BasePart") and p:GetAttribute("Kind") == "fabric" then p.Color = hex("72757b") end -- (8f9196 lit to white under the hall's lamps)
				end
			end
			for _, p in d:GetDescendants() do if p:IsA("BasePart") then hide(p) end end
			n += 1
		end
	end
	return "small: " .. n .. " tents"
end

-- ---------------------------------------------------------------- the playground
-- the secret movement course was a set of gridded test blocks on a bright sky. it is now a floodlit yard at dusk:
-- concrete pylons with pale collars, decks with a lit amber edge, grapple pods hung on cables from eight light masts,
-- no floor in sight (the pylons run down into the haze). every block of the course stays exactly where and what it was (it is the collision: pads,
-- hooks, jumps and the fall line do not change) and is hidden behind the piece made for it. new and solid, none of it
-- in a pad's flight: a slim pylon under each stepping stone and under the start deck, the finish sign's two posts.
-- its light is the "playground" look in ReplicatedStorage.Jankfire.HubLook.
local PG_DECKS = { ["64x64"] = "pg_deckA", ["64x48"] = "pg_deckB", ["48x48"] = "pg_deckC", ["48x32"] = "pg_deckD", ["64x32"] = "pg_deckE", ["64x16"] = "pg_deckF", ["32x48"] = "pg_deckG" }
local PG_GROUND = 208 -- where the course's own blocks end (the fall line is y 240)
local PG_DEEP = -140 -- the pylons you see run on down to here: far enough into the haze that they have no visible foot

function S.playground(): string
	local pg = hub():WaitForChild("Playground")
	local blocks = pg:WaitForChild("Blocks")
	local old = pg:FindFirstChild("Dress")
	if old then old:Destroy() end
	local dress = Instance.new("Folder"); dress.Name = "Dress"; dress.Parent = pg
	local function sub(name: string): Folder
		local f = Instance.new("Folder"); f.Name = name; f.Parent = dress
		return f
	end
	local pylons, decks, pods, masts, solids = sub("Pylons"), sub("Decks"), sub("Pods"), sub("Masts"), sub("Solids")
	-- a kit piece stretched to a box: every mesh of the piece fills the piece's own box, so each is scaled about the
	-- piece's origin
	local function stretched(name: string, at: Vector3, k: Vector3, parent: Instance): Model?
		local m = put(name, CF(at), parent)
		if not m then return nil end
		for _, p in m:GetChildren() do
			if p:IsA("BasePart") then
				local rel = p.Position - at
				p.Size = p.Size * k
				p.CFrame = CF(at + rel * k)
			end
		end
		return m
	end
	-- a pylon w x d up to y1: the shaft (it runs on down into the haze), a collar under its top, and on the tall ones
	-- more collars below, spaced a little differently from pylon to pylon (the same band at the same height on every
	-- one read as copy and paste)
	local function pylon(cx: number, cz: number, w: number, d: number, y0: number, y1: number)
		local foot = math.max(y0, PG_GROUND)
		local shaft = stretched("pg_shaft", V3(cx, PG_DEEP, cz), V3(w / 16, (y1 - PG_DEEP) / 16, d / 16), pylons)
		-- (16 Nov) the shaft's ribs ended in the concrete's own top, where players stand, and flickered: stop them 0.1 short
		if shaft then
			for _, p in shaft:GetChildren() do
				if p:IsA("BasePart") and p.Material ~= Enum.Material.Concrete then
					p.Size -= V3(0, 0.1, 0)
					p.CFrame -= V3(0, 0.05, 0)
				end
			end
		end
		local kc = math.sqrt(math.max(w, d) / 16)
		local y = y1 - 2.4 * kc - 0.05 -- (16 Nov: the collar's top met the shaft's top, where players stand, and flickered)
		stretched("pg_collar", V3(cx, y, cz), V3(w / 16, kc, d / 16), pylons)
		if y1 - foot > 150 then
			local step = 72 + ((math.floor(math.abs(cx) / 8) + math.floor(math.abs(cz) / 8)) % 3) * 16
			y -= step
			while y > foot + 30 do
				stretched("pg_collar", V3(cx, y, cz), V3(w / 16, kc, d / 16), pylons)
				y -= step
			end
		end
	end
	local spires, hooks = {}, {}
	local n = 0
	for _, b in blocks:GetChildren() do
		if not b:IsA("BasePart") then continue end
		local s, p = b.Size, b.Position
		local top, bottom = p.Y + s.Y / 2, p.Y - s.Y / 2
		if b.Name == "Hook" then
			put("pg_pod", CF(p), pods)
			table.insert(hooks, p)
		elseif b.Name == "Stone" then
			put("pg_stone", CF(p), decks)
			pylon(p.X, p.Z, 8, 8, PG_GROUND, bottom)
			solid(solids, CF(p.X, (PG_GROUND + bottom) / 2, p.Z), V3(8, bottom - PG_GROUND, 8))
		elseif s.Y <= 16.01 then
			local key, turn = ("%dx%d"):format(s.X, s.Z), 0
			if not PG_DECKS[key] then key, turn = ("%dx%d"):format(s.Z, s.X), math.pi / 2 end
			if PG_DECKS[key] then put(PG_DECKS[key], CF(p) * CFrame.Angles(0, turn, 0), decks)
			else warn("StructurePass: no deck for " .. b.Name .. " " .. tostring(s)); continue end
		elseif b.Name == "TowerC" then
			-- a tower with a landing on top: a deck for its top 16 studs, a pylon under it
			put("pg_deckG", CF(p.X, top - 8, p.Z), decks)
			pylon(p.X, p.Z, s.X, s.Z, bottom, top - 16)
		else
			pylon(p.X, p.Z, s.X, s.Z, bottom, top)
			if b.Name == "Spire" then
				local m = put("pg_masthead", CF(p.X, top, p.Z), masts)
				local g = m and glowPart(m)
				if g then
					local l = Instance.new("PointLight"); l.Color = LAMPLIGHT; l.Brightness = 1.4; l.Range = 60; l.Shadows = false; l.Parent = g
					-- (the lamp panels at f2dcc0 were white holes with bloom round them: dimmer and warmer)
					for _, d in m:GetChildren() do if d:IsA("BasePart") and d.Material == NEON and d.Color == WARM then d.Color = hex("b9a68a") end end
				end
				table.insert(spires, V3(p.X, top + 12.4, p.Z))
			end
		end
		hide(b)
		n += 1
	end
	-- the start deck stands on a pylon of its own
	local plaza = blocks:FindFirstChild("Plaza")
	if plaza then
		local bottom = plaza.Position.Y - plaza.Size.Y / 2
		pylon(plaza.Position.X, plaza.Position.Z, 24, 24, PG_GROUND, bottom)
		solid(solids, CF(plaza.Position.X, (PG_GROUND + bottom) / 2, plaza.Position.Z), V3(24, bottom - PG_GROUND, 24))
	end
	-- every pod hangs from the three nearest masts that are well above it (the old loose cables are hidden)
	local function cable(a: Vector3, b: Vector3)
		local len = (b - a).Magnitude
		local c = slab(pods, "Cable", CFrame.lookAt((a + b) / 2, b), V3(0.9, 0.9, len), hex("4d515a"))
		c.CastShadow = false
	end
	for _, h in hooks do
		local from = h + V3(0, 10.2, 0)
		local c = table.clone(spires)
		table.sort(c, function(a, b) return (a - from).Magnitude < (b - from).Magnitude end)
		local used = 0
		for _, s in c do
			if s.Y > from.Y + 14 and used < 3 then cable(from, s); used += 1 end
		end
	end
	for _, d in pg:WaitForChild("Deco"):GetChildren() do
		if d:IsA("BasePart") and d.Name == "Cable" then hide(d) end
	end
	-- the finish sign hangs in a gantry (its posts are solid); the start sign stands on two short legs
	local fb = pg:FindFirstChild("FinishBoard")
	if fb and fb:IsA("BasePart") then
		local base = fb.Position.Y - fb.Size.Y / 2 - 3
		put("pg_gantry", CF(fb.Position.X, base, fb.Position.Z), decks)
		for _, sx in { -12, 12 } do solid(solids, CF(fb.Position.X + sx, base + 6.7, fb.Position.Z), V3(2, 13.4, 2)) end
	end
	local tb = pg:FindFirstChild("TitleBoard")
	if tb and tb:IsA("BasePart") then
		local bottom = tb.Position.Y - tb.Size.Y / 2
		for _, sx in { -7, 7 } do
			slab(decks, "SignLeg", CF(tb.Position.X + sx, bottom - 2, tb.Position.Z), V3(1, 4, 1), GRAPH)
			slab(decks, "SignFoot", CF(tb.Position.X + sx, bottom - 3.8, tb.Position.Z), V3(2, 0.4, 2), TRIM)
		end
	end
	-- arrows painted on the decks where the way on is a walk or a jump (a pad says "jump" by itself)
	for _, c in { { 0, 304, -9409, 180 }, { -22, 304, -9400, -90 }, { 22, 336, -9488, 90 }, { 74, 400, -9336, -90 } } do
		local m = put("pg_chevron", CF(c[1], c[2] + 0.06, c[3]) * CFrame.Angles(0, math.rad(c[4]), 0), decks)
		if m then m:ScaleTo(1.1) end
	end
	-- the decks' lit edges and the pods' belts: a deeper amber than the kit's (f0c468 bloomed to yellow)
	for _, d in dress:GetDescendants() do
		if d:IsA("BasePart") and d.Material == NEON and d.Color == AMBERGLOW then d.Color = hex("d48a22") end
	end
	-- (no cloud floor: two tries, snow hills and then one faceted mound. the slate haze carries the void below)
	-- the gate back to training (a placed door kit, not built here) is a laser gate: tagged LaserGate, its laser (the
	-- big neon piece of its frame) marked Laser, so it clicks off as you walk up and back on after you
	-- (TrainingDoors.client; the owner, 16 Nov: "when you get close you hear a click and the laser gate turns off?")
	local rd = pg:FindFirstChild("ReturnDoor")
	if rd then
		game:GetService("CollectionService"):AddTag(rd, "LaserGate")
		local void = rd:FindFirstChild("LaserVoid")
		if void and void:IsA("BasePart") then rd:SetAttribute("Center", void.Position - Vector3.new(0, void.Size.Y / 2, 0)) end
		rd:SetAttribute("Near", 10)
		for _, d in rd:GetDescendants() do
			if d:IsA("BasePart") and d.Material == NEON and d.Size.X > 10 then d:SetAttribute("Laser", true) end
		end
	end
	return ("playground: %d blocks dressed, %d things"):format(n, #dress:GetDescendants())
end

-- ---------------------------------------------------------------- the skyline
-- the eight towers round the arena (and the three the arena stands on) were plain boxes. each gets a facade of real
-- parts, no pictures: a dark glass skin, floor bands and piers standing proud of it, a scatter of lit windows; the
-- tall ones get a crown, so no two tops are the same. the far, low city stays as it is. look-only: nothing here is
-- solid or stops a shot, and the towers' own boxes are not touched.
local GLASS, CONCRETE_L, BRICK, SILL = hex("2f3a48"), hex("7e828a"), hex("715a50"), hex("9a9189")
-- (lit windows are dim on purpose: at f2dcc0 they were glowing blocks, the brightest things in the sky)
-- (and warm WHITE, not amber: amber is the one accent, and amber windows put it on every tower)
local LITWARM, LITCOOL = hex("e2ddd3"):Lerp(Color3.new(0, 0, 0), 0.45), hex("dfe8ee"):Lerp(Color3.new(0, 0, 0), 0.58)

local function box(parent: Instance, name: string, cf: CFrame, size: Vector3, color: Color3, mat: Enum.Material?, reflect: number?): Part
	local p = slab(parent, name, cf, size, color, mat or CONC)
	if reflect then p.Reflectance = reflect end
	return p
end
local function drum(parent: Instance, name: string, at: Vector3, r: number, h: number, color: Color3, mat: Enum.Material?): Part
	local p = slab(parent, name, CF(at) * CFrame.Angles(0, 0, math.pi / 2), V3(h, r * 2, r * 2), color, mat or SP)
	p.Shape = Enum.PartType.Cylinder
	return p
end
-- one shaft's facade. o = { style = "grid" | "ribbon" | "fins" | "brick", floor = studs per floor, bay = studs per bay,
-- lit = how many lit windows, seed = number, cornice = studs left bare at the top (the tower's own neon band and cap) }
local function facade(parent: Instance, cx: number, cz: number, w: number, d: number, y0: number, y1: number, o: any): number
	local f = Instance.new("Folder"); f.Name = ("Shaft_%d_%d_%d"):format(cx, cz, y1)
	local top, base = y1 - (o.cornice or 8), y0
	local h, cy = top - base, (top + base) / 2
	if h < 6 then return 0 end
	local style = o.style or "grid"
	local floorH = o.floor or 12
	local bay = o.bay or 12
	local brick = style == "brick"
	local bandH = if style == "ribbon" then 5 elseif brick then 0.9 else 2.4
	local bandP = if style == "ribbon" then 1.2 else 0.7
	local pierW = if style == "fins" then 1.6 elseif brick then 4.6 else 2.2
	local pierP = if style == "fins" then 1.8 elseif brick then 0.5 else 1.0
	local bandC, pierC = if brick then SILL else CONCRETE_L, if brick then BRICK else CONCRETE_L
	local pierM = if brick then Enum.Material.Brick else CONC
	local hw, hd = w / 2, d / 2
	if not brick then box(f, "Glass", CF(cx, cy, cz), V3(w + 0.6, h, d + 0.6), GLASS, SP, 0.18) end
	-- floors: a band right round the shaft at every floor (a brick tower gets a ribbon of dark glass over a pale sill)
	local nf = math.max(1, math.floor(h / floorH + 0.5))
	local fh = h / nf
	for k = 0, nf do
		local y = base + k * fh
		if brick then
			if k < nf then
				box(f, "Windows", CF(cx, y + fh * 0.55, cz), V3(w + 0.3, fh * 0.56, d + 0.3), GLASS, SP, 0.18)
				box(f, "Sill", CF(cx, y + fh * 0.24, cz), V3(w + 1.0, bandH, d + 1.0), bandC, CONC)
			end
		else
			local thick = if k == nf then bandH * 1.6 else bandH
			box(f, "Band", CF(cx, y, cz), V3(w + 2 * bandP, thick, d + 2 * bandP), bandC, CONC)
		end
	end
	-- bays: piers up each face, and a square pier on each corner
	local nx, nz = math.max(1, math.floor(w / bay + 0.5)), math.max(1, math.floor(d / bay + 0.5))
	local sx, sz = w / nx, d / nz
	if style ~= "ribbon" then
		for i = 1, nx - 1 do
			for _, s in { -1, 1 } do box(f, "Pier", CF(cx - hw + i * sx, cy, cz + s * (hd + pierP / 2)), V3(pierW, h, pierP), pierC, pierM) end
		end
		for i = 1, nz - 1 do
			for _, s in { -1, 1 } do box(f, "Pier", CF(cx + s * (hw + pierP / 2), cy, cz - hd + i * sz), V3(pierP, h, pierW), pierC, pierM) end
		end
	end
	local cw = pierW + 1.2
	for _, a in { -1, 1 } do for _, b in { -1, 1 } do
		box(f, "Corner", CF(cx + a * (hw - cw / 2 + pierP), cy, cz + b * (hd - cw / 2 + pierP)), V3(cw, h, cw), pierC, pierM)
	end end
	-- lit windows, from a seeded dice (the same every build): each is exactly one cell of the grid. most sit together
	-- on one or two lit floors per shaft (somebody is working late), a few are scattered
	local rng = Random.new(o.seed or (cx * 7 + cz * 13 + y1))
	local winH = if brick then fh * 0.5 else fh - bandH - 1.4
	local used = {}
	local function light(face: number, k: number, i: number)
		local key = face * 100000 + k * 100 + i
		if used[key] then return end
		used[key] = true
		local alongX = face <= 2
		local step, half = if alongX then sx else sz, if alongX then hw else hd
		local span = if style == "ribbon" then step - 1.6 else step - pierW - 1.0
		local u = -half + (i + 0.5) * step
		local y = base + k * fh + (if brick then fh * 0.55 else fh / 2 + 0.2)
		local sgn = if face % 2 == 0 then 1 else -1
		local color = if rng:NextNumber() < 0.85 then LITWARM else LITCOOL
		if alongX then slab(f, "Lit", CF(cx + u, y, cz + sgn * (hd + 0.42)), V3(span, winH, 0.2), color, NEON)
		else slab(f, "Lit", CF(cx + sgn * (hw + 0.42), y, cz + u), V3(0.2, winH, span), color, NEON) end
	end
	local want = o.lit or 0
	local floors = if want >= 30 then 2 elseif want >= 10 then 1 else 0
	for _ = 1, floors do
		local k = rng:NextInteger(math.floor(nf * 0.25), math.max(math.floor(nf * 0.25), nf - 2))
		for face = 1, 4 do
			local n = if face <= 2 then nx else nz
			for i = 0, n - 1 do if rng:NextNumber() < 0.55 then light(face, k, i) end end
		end
	end
	for _ = 1, math.floor(want / 6) do
		local face = rng:NextInteger(1, 4)
		light(face, rng:NextInteger(0, nf - 1), rng:NextInteger(0, (if face <= 2 then nx else nz) - 1))
	end
	f.Parent = parent
	return #f:GetChildren()
end

-- the towers: { x, z, w, d, y0, y1, options }. the upper shafts of the four nearest are finest; what stands far below
-- the roofs you play on is coarser (taller floors, fewer lit windows)
local SHAFTS = {
	-- the arena's own three (their tops are the roofs you play on: no cornice left bare below y -30)
	{ 0, 0, 132, 168, -456, -22, { style = "brick", floor = 13, bay = 11, lit = 46, cornice = 6 } },
	{ -132, 0, 84, 108, -456, -2, { style = "grid", floor = 13, bay = 12, lit = 40, cornice = 9 } },
	{ 132, 0, 84, 108, -456, -2, { style = "brick", floor = 13, bay = 11, lit = 40, cornice = 9 } },
	-- north, south, east, west
	{ 0, -285, 78, 78, -242, 60, { style = "fins", floor = 12, bay = 6.5, lit = 44 } },
	{ 0, -285, 102, 102, -456, -243, { style = "grid", floor = 18, bay = 12.75, lit = 18 } },
	{ 0, 285, 108, 108, -456, 0, { style = "ribbon", floor = 12, bay = 13.5, lit = 60 } },
	{ 315, 0, 66, 66, -256, 30, { style = "grid", floor = 11, bay = 11, lit = 40 } },
	{ 315, 0, 90, 90, -456, -258, { style = "ribbon", floor = 18, bay = 15, lit = 14 } },
	{ -315, 0, 48, 48, -98, 150, { style = "grid", floor = 10.5, bay = 9.6, lit = 34 } },
	{ -315, 0, 72, 72, -289, -99, { style = "fins", floor = 14, bay = 6, lit = 20 } },
	{ -315, 0, 96, 96, -456, -291, { style = "grid", floor = 20, bay = 12, lit = 10 } },
	-- the four corners
	{ 315, 285, 42, 42, -82, 180, { style = "fins", floor = 12, bay = 5.25, lit = 26 } },
	{ 315, 285, 66, 66, -280, -84, { style = "grid", floor = 14, bay = 11, lit = 16 } },
	{ 315, 285, 90, 90, -456, -282, { style = "ribbon", floor = 20, bay = 15, lit = 8 } },
	{ 315, -285, 36, 36, -124, 105, { style = "ribbon", floor = 10, bay = 9, lit = 24 } },
	{ 315, -285, 60, 60, -302, -126, { style = "grid", floor = 14, bay = 10, lit = 14 } },
	{ 315, -285, 84, 84, -456, -303, { style = "fins", floor = 20, bay = 7, lit = 8 } },
	{ -315, -285, 90, 90, -456, -90, { style = "grid", floor = 15, bay = 11.25, lit = 36 } },
	{ -315, 285, 78, 78, -456, -45, { style = "ribbon", floor = 14, bay = 13, lit = 36 } },
}

function S.skyline(): string
	-- a few of the far city's roof slabs and strips float high in the haze with no building under them: from the
	-- arena only their glow shows, as specks in the sky. hidden (look-only boxes; S.clear("skyline") shows them again)
	for _, d in roof():WaitForChild("City"):GetChildren() do
		if d:IsA("BasePart") and d.Position.Y > -200 and V3(d.Position.X, 0, d.Position.Z).Magnitude > 500 then hide(d) end
	end
	local dress = folder(roof(), "Dress")
	local old = dress:FindFirstChild("Skyline")
	if old then old:Destroy() end
	local f = Instance.new("Folder"); f.Name = "Skyline"; f.Parent = dress
	local n = 0
	for i, s in SHAFTS do
		local o = s[7]
		o.seed = 1000 + i * 37
		n += facade(f, s[1], s[2], s[3], s[4], s[5], s[6], o)
		task.wait()
	end
	-- a second row: plain towers further out, so that from the roofs the gaps between the near towers show more city
	-- and not a bare line of haze. each is one box with wide floor bands and a few lit windows
	local far = Instance.new("Folder"); far.Name = "FarRow"; far.Parent = f
	for i, t in { { -640, -130, 60, 44 }, { -600, 300, 74, -30 }, { 650, 150, 56, 96 }, { 620, -340, 68, 6 }, { -190, -650, 62, 74 }, { 250, 660, 72, 24 }, { -330, 650, 58, 58 }, { 360, -640, 64, -16 } } do
		local x, z, w, top = t[1], t[2], t[3], t[4]
		box(far, "Tower", CF(x, (top - 456) / 2, z), V3(w, top + 456, w), hex("70747c"))
		n += facade(far, x, z, w, w, -456, top, { style = if i % 2 == 0 then "ribbon" else "grid", floor = 20, bay = w / 4, lit = 12, cornice = 0, seed = 300 + i * 11 })
		box(far, "Cap", CF(x, top + 1.5, z), V3(w * 0.5, 9, w * 0.4), hex("7e828a"))
	end
	task.wait()
	-- crowns: each tall tower ends differently
	local c = Instance.new("Folder"); c.Name = "Crowns"; c.Parent = f
	-- west (top 150): two set-backs and a mast with an amber lamp, the tallest thing against the sunset
	facade(c, -315, 0, 36, 36, 152, 180, { style = "grid", floor = 9, bay = 9, lit = 6, cornice = 0, seed = 11 })
	facade(c, -315, 0, 24, 24, 180, 202, { style = "fins", floor = 11, bay = 4.8, lit = 3, cornice = 0, seed = 12 })
	box(c, "Cap", CF(-315, 203, 0), V3(27, 2, 27), CONCRETE_L)
	drum(c, "Mast", V3(-315, 238, 0), 1.6, 68, hex("6a6e77"))
	for _, y in { 214, 232, 250 } do drum(c, "MastRing", V3(-315, y, 0), 2.6, 1.6, CONCRETE_L) end
	local lamp = slab(c, "MastLamp", CF(-315, 273.5, 0), V3(4, 4, 4), AMBERGLOW, NEON)
	lamp.Shape = Enum.PartType.Ball
	-- south-east (top 180): a chisel roof
	local w1 = Instance.new("WedgePart")
	w1.Name = "Chisel"; w1.Anchored = true; w1.CanCollide = false; w1.CanQuery = false; w1.CanTouch = false; w1.CastShadow = false
	w1.Material = SP; w1.Color = GLASS; w1.Reflectance = 0.18; w1.Size = V3(42.6, 44, 42.6); w1.CFrame = CF(315, 202, 285) * CFrame.Angles(0, math.pi / 2, 0); w1.Parent = c
	box(c, "ChiselEdge", CF(315, 180.8, 285), V3(46, 1.6, 46), CONCRETE_L)
	box(c, "ChiselFin", CF(315 - 21.6, 202, 285), V3(1.2, 44, 43.8), CONCRETE_L)
	-- north-east (top 105): an open frame with a lit lantern inside
	for _, a in { -1, 1 } do for _, b in { -1, 1 } do box(c, "Post", CF(315 + a * 15.5, 119, -285 + b * 15.5), V3(3, 26, 3), CONCRETE_L) end end
	box(c, "Ring", CF(315, 133, -285), V3(37, 3, 37), CONCRETE_L)
	drum(c, "Lantern", V3(315, 115, -285), 10.5, 16, hex("3a4656"))
	drum(c, "LanternGlow", V3(315, 115, -285), 10.9, 5, LITWARM, NEON)
	drum(c, "LanternCap", V3(315, 124, -285), 12, 1.6, CONCRETE_L)
	-- north (top 60): two set-backs with plant on top
	facade(c, 0, -285, 60, 60, 62, 80, { style = "fins", floor = 9, bay = 6, lit = 8, cornice = 0, seed = 21 })
	facade(c, 0, -285, 40, 40, 80, 94, { style = "grid", floor = 7, bay = 10, lit = 4, cornice = 0, seed = 22 })
	box(c, "Cap", CF(0, 95, -285), V3(43, 2, 43), CONCRETE_L)
	drum(c, "Cooler", V3(-9, 101, -285), 6.5, 10, hex("9a9da3"))
	drum(c, "Cooler", V3(9, 101, -285), 6.5, 10, hex("9a9da3"))
	drum(c, "CoolerTop", V3(-9, 106.4, -285), 5.4, 0.8, DARK)
	drum(c, "CoolerTop", V3(9, 106.4, -285), 5.4, 0.8, DARK)
	-- east (top 30): a screened plant deck
	for _, a in { -1, 1 } do
		box(c, "Screen", CF(315 + a * 29, 38, 0), V3(1.4, 12, 58), hex("6a6e77"), SP)
		box(c, "Screen", CF(315, 38, a * 29), V3(58, 12, 1.4), hex("6a6e77"), SP)
	end
	for _, y in { 34.5, 38, 41.5 } do box(c, "ScreenBand", CF(315, y, 0), V3(60.4, 0.9, 60.4), CONCRETE_L) end
	drum(c, "Cooler", V3(303, 40, -10), 8, 14, hex("9a9da3")); drum(c, "CoolerTop", V3(303, 47.4, -10), 6.8, 0.8, DARK)
	drum(c, "Cooler", V3(325, 40, 10), 8, 14, hex("9a9da3")); drum(c, "CoolerTop", V3(325, 47.4, 10), 6.8, 0.8, DARK)
	box(c, "PlantRoom", CF(322, 39, -14), V3(18, 12, 14), hex("8b8d93"))
	-- south (top 0, level with the roofs you play on, so you look across it): a lit glass vault and big plant
	local vault = drum(c, "Vault", V3(0, 2, 285), 15, 74, GLASS)
	vault.CFrame = CF(0, 2, 285); vault.Reflectance = 0.18
	local glow = drum(c, "VaultGlow", V3(0, 2, 285), 15.3, 3, LITWARM, NEON)
	glow.CFrame = CF(0, 2, 285)
	for _, x in { -30, -15, 15, 30 } do
		local rib = drum(c, "VaultRib", V3(x, 2, 285), 15.6, 1.4, CONCRETE_L, CONC)
		rib.CFrame = CF(x, 2, 285)
	end
	box(c, "VaultEnd", CF(-37.5, 8, 285), V3(1.6, 16, 34), CONCRETE_L); box(c, "VaultEnd", CF(37.5, 8, 285), V3(1.6, 16, 34), CONCRETE_L)
	for _, a in { -1, 1 } do
		box(c, "Parapet", CF(a * 53.4, 4.5, 285), V3(1.6, 5, 108), CONCRETE_L)
		box(c, "Parapet", CF(0, 4.5, 285 + a * 53.4), V3(108, 5, 1.6), CONCRETE_L)
	end
	for _, p in { { "rt_chiller", -30, 250, 2.2, 0 }, { "rt_chiller", 28, 322, 2.2, 180 }, { "rt_tank", -30, 322, 2.6, 0 }, { "rt_stairhead", 34, 248, 1.8, 180 }, { "rt_cowl", 4, 250, 2.4, 0 } } do
		local m = put(p[1], CF(p[2], 2, p[3]) * CFrame.Angles(0, math.rad(p[5]), 0), c)
		if m then m:ScaleTo(p[4]) end
	end
	-- the two lower corner towers: plant on their roofs (you see them from above)
	for _, t in { { -315, -285, -88, 90 }, { -315, 285, -43, 78 } } do
		local x, z, y, w = t[1], t[2], t[3], t[4]
		for _, a in { -1, 1 } do
			box(c, "Parapet", CF(x + a * (w / 2 - 0.8), y + 2.5, z), V3(1.6, 5, w), CONCRETE_L)
			box(c, "Parapet", CF(x, y + 2.5, z + a * (w / 2 - 0.8)), V3(w, 5, 1.6), CONCRETE_L)
		end
		box(c, "PlantRoom", CF(x - w * 0.18, y + 8, z + w * 0.15), V3(w * 0.34, 16, w * 0.28), hex("8b8d93"))
		drum(c, "Cooler", V3(x + w * 0.2, y + 6, z - w * 0.18), w * 0.11, 12, hex("9a9da3"))
		drum(c, "CoolerTop", V3(x + w * 0.2, y + 12.4, z - w * 0.18), w * 0.09, 0.8, DARK)
		local m = put("rt_chiller", CF(x + w * 0.15, y, z + w * 0.24), c)
		if m then m:ScaleTo(2) end
	end
	return ("skyline: %d facade parts, %d crown things"):format(n, #c:GetDescendants())
end

-- ---------------------------------------------------------------- checks
-- S.check(): the facts the pass promises. (1) every solid box on the west roof has its mirror image on the east roof,
-- so the two ends have the same cover; (2) no solid box stands within 3 studs of a spawn; (3) no solid box is in the
-- flight of a jump pad (the pad's Pad attribute is its launch velocity; the arc is followed until it is back down)
local function aabb(p: BasePart): (Vector3, Vector3)
	local cf, s = p.CFrame, p.Size / 2
	local lo, hi = V3(math.huge, math.huge, math.huge), V3(-math.huge, -math.huge, -math.huge)
	for _, a in { -1, 1 } do for _, b in { -1, 1 } do for _, c in { -1, 1 } do
		local w = cf * V3(a * s.X, b * s.Y, c * s.Z)
		lo = lo:Min(w); hi = hi:Max(w)
	end end end
	return lo, hi
end
local function inBox(lo: Vector3, hi: Vector3, p: Vector3, grow: number): boolean
	return p.X > lo.X - grow and p.X < hi.X + grow and p.Y > lo.Y - grow and p.Y < hi.Y + grow and p.Z > lo.Z - grow and p.Z < hi.Z + grow
end
function S.check(): string
	local out = {}
	local solids = {}
	for _, root in { roof():FindFirstChild("Dress"), hub():WaitForChild("Playground"):FindFirstChild("Dress") } do
		if root then
			for _, d in root:GetDescendants() do
				if d:IsA("BasePart") and d.Name == "DressSolid" then
					local lo, hi = aabb(d)
					table.insert(solids, { part = d, lo = lo, hi = hi })
				end
			end
		end
	end
	table.insert(out, #solids .. " solid boxes added in all")
	-- 1. the mirror
	local dress = roof():FindFirstChild("Dress")
	local west, east = dress and dress:FindFirstChild("West"), dress and dress:FindFirstChild("East")
	if west and east then
		local W, E = west.Solids:GetChildren(), east.Solids:GetChildren()
		local missing = 0
		for _, a in W do
			local alo, ahi = aabb(a)
			local found = false
			for _, b in E do
				local blo, bhi = aabb(b)
				if math.abs(alo.X + bhi.X) < 0.06 and math.abs(ahi.X + blo.X) < 0.06 and (V3(0, alo.Y, alo.Z) - V3(0, blo.Y, blo.Z)).Magnitude < 0.06
					and (V3(0, ahi.Y, ahi.Z) - V3(0, bhi.Y, bhi.Z)).Magnitude < 0.06 and a.ClassName == b.ClassName then found = true; break end
			end
			if not found then missing += 1; table.insert(out, ("  NO MIRROR for the box at %.1f, %.1f, %.1f"):format(a.Position.X, a.Position.Y, a.Position.Z)) end
		end
		table.insert(out, ("mirror: west %d boxes, east %d, without a twin %d"):format(#W, #E, missing))
	end
	-- 2. spawns
	local bad = 0
	local spawns = {}
	for _, name in { "Spawns", "TeamSpawns" } do
		local f = roof():FindFirstChild(name)
		if f then for _, d in f:GetDescendants() do if d:IsA("BasePart") then table.insert(spawns, d.Position) end end end
	end
	local arrive = hub():WaitForChild("Doors"):FindFirstChild("PlaygroundArrive")
	if arrive then for _, d in arrive:GetChildren() do if d:IsA("BasePart") then table.insert(spawns, d.Position) end end end
	for _, p in spawns do
		for _, s in solids do
			-- a standing player: from the marker up 6 studs, 3 studs clear to each side (and the same spot mirrored)
			for _, q in { p, V3(-p.X, p.Y, p.Z) } do
				if inBox(s.lo, s.hi, q + V3(0, 3, 0), 3) then bad += 1; table.insert(out, ("  SPAWN %.0f, %.0f, %.0f is inside or beside a new box"):format(q.X, q.Y, q.Z)) end
			end
		end
	end
	table.insert(out, ("spawns: %d checked (each also mirrored), %d blocked"):format(#spawns, bad))
	-- 3. jump pads
	local g = workspace.Gravity
	local pads, hit = 0, 0
	for _, f in { roof():FindFirstChild("Pads"), hub().Playground:FindFirstChild("Pads") } do
		if not f then continue end
		for _, pad in f:GetDescendants() do
			local v = pad:IsA("BasePart") and pad:GetAttribute("Pad")
			if typeof(v) ~= "Vector3" then continue end
			pads += 1
			-- (ray by ray along the arc: it ends on the first thing of the map it meets; a new box met first is in the way)
			local p0 = pad.Position + V3(0, 3, 0)
			local t, blocked = 0.12, nil
			local prev = p0 + v * t - V3(0, 0.5 * g * t * t, 0)
			while t < 8 do
				t += 0.03
				local p = p0 + v * t - V3(0, 0.5 * g * t * t, 0)
				local r = workspace:Raycast(prev, p - prev)
				if r then
					if r.Instance.Name == "DressSolid" then blocked = r.Instance end
					break
				end
				for _, sb in solids do if inBox(sb.lo, sb.hi, p, 1.5) then blocked = sb.part; break end end
				if blocked or p.Y < p0.Y - 60 then break end
				prev = p
			end
			if blocked then hit += 1; table.insert(out, ("  PAD at %.0f, %.0f, %.0f flies into the box at %.1f, %.1f, %.1f"):format(pad.Position.X, pad.Position.Y, pad.Position.Z, blocked.Position.X, blocked.Position.Y, blocked.Position.Z)) end
		end
	end
	table.insert(out, ("pads: %d flights followed, %d blocked"):format(pads, hit))
	return table.concat(out, "\n")
end

-- take one part of the pass away again: "rooftop" (West + East), "skyline", "lounge", "cabanas", "tents", "playground".
-- the map's own boxes that were hidden behind those models show again
function S.clear(which: string): string
	local dress = roof():FindFirstChild("Dress")
	local pg = hub():WaitForChild("Playground")
	local tg = hub():WaitForChild("TrainingGround")
	local n = 0
	local function drop(parent: Instance?, names: { string })
		if not parent then return end
		for _, name in names do
			local f = parent:FindFirstChild(name)
			if f then n += #f:GetDescendants(); f:Destroy() end
		end
	end
	local function show(root: Instance, keep: ((BasePart) -> boolean)?)
		for _, d in root:GetDescendants() do
			if d:IsA("BasePart") and d:GetAttribute("DressHid") ~= nil and (not keep or keep(d)) then
				d.Transparency = d:GetAttribute("DressHid"); d:SetAttribute("DressHid", nil)
			end
		end
	end
	if which == "rooftop" then
		drop(dress, { "West", "East" })
		show(roof():WaitForChild("Solid"), function(d) return math.abs(d.Position.X) > 88 end)
	elseif which == "lounge" then
		drop(dress, { "Lounge" })
		show(roof():WaitForChild("Solid"), function(d) return math.abs(d.Position.X) < 32 end)
	elseif which == "skyline" then
		drop(dress, { "Skyline" })
		show(roof():WaitForChild("City"))
	elseif which == "cabanas" then drop(dress, { "Cabanas" })
	elseif which == "tents" then
		drop(tg:FindFirstChild("Dress"), { "Tents" })
		show(tg)
	elseif which == "playground" then
		drop(pg, { "Dress" })
		show(pg)
	else return "clear: no part called " .. tostring(which) end
	return "clear " .. which .. ": " .. n .. " things removed"
end

function S.all(): string
	local out = {}
	for _, step in { S.import, S.rooftop, S.skyline, S.lounge, S.pooldeck, S.cabanas, S.small, S.playground, S.check } do
		table.insert(out, step())
		task.wait()
	end
	return table.concat(out, "\n")
end

return S
