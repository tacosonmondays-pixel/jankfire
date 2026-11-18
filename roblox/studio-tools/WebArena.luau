--!strict
-- WebArena: builds the arenas ported from the web game (17 Nov 2026; the owner: "We do need more maps, we technically
-- have really pretty rooftop maps v2 and v3!! We can bring over some of the other ones!!"). Each arena is made by one
-- Blender script (tools/roblox/<map>_models.py) from the web map's own boxes (tools/roblox/arenas/<id>.json, x3: 1 m =
-- 3 studs), which writes two things: the kit (one .glb, uploaded as a Model, ids in W.ASSETS) and
-- ServerStorage.PolishBackup.<Name>Layout (the hit boxes, pads, spawns, team spawns, water and lights, in studs local to
-- the arena's origin). The arena is workspace.Map.<Name>: the web's boxes as invisible hit boxes (they collide and take
-- shots, their material and colour pick the impact effect), the kit as the look (never collides, never takes shots).
--
--   local W = require(game.ServerStorage.PolishBackup.WebArena:Clone())
--   print(W.import("Crate"))   -- the kit into ServerStorage.JankfireMeshes (after each upload: set W.ASSETS first)
--   print(W.build("Crate"))    -- wipe and remake workspace.Map.Crate
--   print(W.check("Crate"))    -- the hit boxes, spawns on floors, team spawn sight lines, pad flights, part counts
--   print(W.solid("Gut"))      -- just the hit boxes again (the kit, the lights and hand-set attributes stay)
--   print(W.pool("add", "Crate"))  -- into the match rotation (workspace.Map's ArenaPool); "remove" takes it out
--
-- What the game reads off the arena model (ReplicatedStorage.Jankfire.Arena, Matches, HubLife, ZoneCull): KillY (the
-- fall line), CentreX (the line team spawns face), Title (the first banner), Look (its light: HubLook.byArena),
-- MaxTeam (the biggest team it takes: a 4v4 never lands on a tiny arena), ZonePiece (ZoneCull puts it aside when
-- nobody is near, however few parts it has), and on a walled arena SkyY, EdgeTop, EdgeSeen (its wall box: wallBox
-- below). Matches copies the whole model for side-by-side matches, so everything
-- an arena needs lives inside it.
local ServerStorage = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local CollectionService = game:GetService("CollectionService")

local W = {}
-- the uploaded <kit>.glb per arena (Model asset "jf_<kit>_<n>"); set after each upload
W.ASSETS = { Crate = 89096180387869, Platform = 96303120157194, Bazaar = 111940015941791, Gut = 117631287535839,
	BazaarV2 = 131330198115223, DesertV2 = 127676315267642, SuburbV2 = 105919865840853,
	Backrooms = 119038836389515, Forest = 130312556142076, ArcticCabin = 112062417043410,
	Skatepark = 83118877796009, Station = 95570686035667 } :: { [string]: number }

local hex = Color3.fromHex
local V3, CF = Vector3.new, CFrame.new
local SP = Enum.Material.SmoothPlastic
local MAT = { plastic = SP, neon = Enum.Material.Neon, glass = Enum.Material.Glass, water = SP } :: { [string]: Enum.Material }
local SEE = { glass = 0.35, water = 0.25 } :: { [string]: number }

local function lib(): Instance return ServerStorage:WaitForChild("JankfireMeshes") end
local function layout(name: string): any
	local src = ServerStorage.PolishBackup:FindFirstChild(name .. "Layout")
	assert(src, "no ServerStorage.PolishBackup." .. name .. "Layout")
	local m = src:Clone()
	local L = require(m) :: any
	m:Destroy()
	return L
end
local function folder(parent: Instance, name: string): Folder
	local f = Instance.new("Folder"); f.Name = name; f.Parent = parent
	return f
end
local function marker(parent: Instance, name: string, cf: CFrame, size: Vector3): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end
local function material(name: string): Enum.Material
	local ok, m = pcall(function() return (Enum.Material :: any)[name] end)
	return if ok and m then m else SP
end

-- ---------------------------------------------------------------- the kit: one asset, sorted into models by name
function W.import(name: string, id: number?): string
	local L = layout(name)
	local aid = id or W.ASSETS[name]
	if not aid or aid == 0 then return "no asset id for " .. name .. ": set W.ASSETS." .. name end
	local ok, container = pcall(function() return InsertService:LoadAsset(aid) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
		d.Transparency = SEE[kind] or 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind == "plastic"
		d.DoubleSided = false
		d:SetAttribute("Kind", kind)
		-- a picture on this colour's pieces (the layout's `surfaces`, 18 Nov 2026: the Backrooms' wallpaper, carpet,
		-- ceiling tiles, pool tiles; the builder gives those meshes world-scaled UVs, so the picture repeats in studs)
		local pic = L.surfaces and L.surfaces[string.lower(h)]
		if pic then
			for _, old in d:GetChildren() do if old:IsA("SurfaceAppearance") then old:Destroy() end end
			local sa = Instance.new("SurfaceAppearance")
			sa.ColorMap = pic
			sa.Parent = d
		end
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	for _, old in lib():GetChildren() do
		if old:GetAttribute("Kit") == L.kit then old:Destroy() end
	end
	local names = {}
	for mname, parts in groups do
		local m = Instance.new("Model")
		m.Name = mname
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", aid); m:SetAttribute("Kit", L.kit); m:SetAttribute("FileFrame", true)
		m.Parent = lib()
		table.insert(names, ("%s %d"):format(mname, #parts))
	end
	container:Destroy()
	table.sort(names)
	return ("kit %s (asset %d): %d models%s\n  %s"):format(L.kit, aid, #names, if bad > 0 then ", " .. bad .. " pieces with no name rule" else "", table.concat(names, "\n  "))
end

-- a patch kit (18 Nov 2026: arenakit's --only=<model>,...): swaps just the models in asset `id` into the kit library and
-- into the built arena's Shell (placed as W.build places them), and leaves everything else as it is: the other models,
-- the Gut's installed heart, hand-set attributes. (a later full W.import + W.build needs a kit uploaded whole)
--   print(W.swap("Gut", <asset id>))
function W.swap(name: string, id: number): string
	local L = layout(name)
	local root = workspace.Map:FindFirstChild(name)
	if not root then return name .. " is not built" end
	local shell = root:FindFirstChild("Shell")
	local ok, container = pcall(function() return InsertService:LoadAsset(id) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
		d.Transparency = SEE[kind] or 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind == "plastic"
		d.DoubleSided = false
		d:SetAttribute("Kind", kind)
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for mname, parts in groups do
		for _, old in lib():GetChildren() do
			if old.Name == mname and old:GetAttribute("Kit") == L.kit then old:Destroy() end
		end
		local m = Instance.new("Model")
		m.Name = mname
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", id); m:SetAttribute("Kit", L.kit); m:SetAttribute("FileFrame", true)
		m.Parent = lib()
		local was = 0
		if shell then
			for _, old in shell:GetChildren() do
				if old.Name == mname then old:Destroy(); was += 1 end
			end
			local c = m:Clone()
			c:PivotTo(CF(L.origin))
			c.Parent = shell
		end
		table.insert(names, ("%s %d pieces (%d old in the arena replaced)"):format(mname, #parts, was))
	end
	container:Destroy()
	table.sort(names)
	return ("swapped into %s (asset %d)%s:\n  %s"):format(name, id, if bad > 0 then ", " .. bad .. " pieces with no name rule" else "", table.concat(names, "\n  "))
end

-- ---------------------------------------------------------------- build
-- "stops you, takes no shots" (flag "c": the Gut's rails, the columns over the roofs, roofs.py): CanQuery off is not
-- enough, Roblox still lets rays hit a part that collides. so such a part goes into the collision group JFRayBlind, which
-- collides with the players' groups (JFPlayers, JFShredded, VipGuest) but not with Default, the group every ray, rope
-- and bullet is cast in (Main.server sets the same up at run time)
local RAYBLIND = "JFRayBlind"
local function rayBlindGroup()
	local PS = game:GetService("PhysicsService")
	if not PS:IsCollisionGroupRegistered(RAYBLIND) then PS:RegisterCollisionGroup(RAYBLIND) end
	PS:CollisionGroupSetCollidable(RAYBLIND, "Default", false)
end

-- the hit boxes (the web's boxes, or a hand-made layout's) into the arena's Solid folder
local function hitBoxes(L: any, O: Vector3, solid: Instance)
	pcall(rayBlindGroup)
	-- the web's boxes: invisible, solid, they take shots (their material and colour: the impact's dust and chips)
	for i, b in L.solid do
		if L.mats and type(b[7]) == "number" then b = { b[1], b[2], b[3], b[4], b[5], b[6], table.unpack(L.mats[b[7]]) } end
		local size = V3(b[4] - b[1], b[5] - b[2], b[6] - b[3])
		local p = Instance.new("Part")
		p.Name = "Solid"
		p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = true; p.CastShadow = false
		p.Transparency = 1
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Material = material(b[7]); p.Color = hex(b[8])
		p.Size = size
		p.CFrame = CF(O + V3((b[1] + b[4]) / 2, (b[2] + b[5]) / 2, (b[3] + b[6]) / 2))
		p:SetAttribute("Mat", b[9])
		p.Parent = solid
		if i % 200 == 0 then task.wait() end
	end
	-- turned hit boxes (a layout may have them: the Gut's spiral stair, its balcony, round posts). flags "c": the box
	-- stops you but takes no shots (rails you can shoot through)
	for i, b in (L.solidR or {}) do
		local mt = L.mats[b[8]]
		local p = Instance.new("Part")
		p.Name = "Solid"
		p.Anchored = true; p.CanCollide = true; p.CanTouch = true; p.CastShadow = false
		p.CanQuery = not string.find(b[9] or "", "c", 1, true)
		if not p.CanQuery then p.CollisionGroup = RAYBLIND end
		-- flags "s": a roof over a spawn (roofs.py open_up, 18 Nov 2026): you can hook it and land on it, but Move.client
		-- slides you off toward the middle like the wall box's ledge, so nobody camps over a spawn
		if string.find(b[9] or "", "s", 1, true) then p:SetAttribute("Slide", true) end
		p.Transparency = 1
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Material = material(mt[1]); p.Color = hex(mt[2])
		p.Size = V3(b[4], b[5], b[6])
		p.CFrame = CF(O + V3(b[1], b[2], b[3])) * CFrame.Angles(0, math.rad(b[7]), 0)
		p:SetAttribute("Mat", mt[3])
		p.Parent = solid
		if i % 200 == 0 then task.wait() end
	end
end

-- the wall box of a walled arena (18 Nov 2026, tools/roblox/wallbox.py): no lid; the sky line (SkyY: Move.client lets
-- nothing lift you over it, Main.server puts anyone 60 studs over it out of the world), the step round the edge (its
-- top, EdgeTop, is a ledge Move.client slides you off) and how high the edge scenery behind the step is seen (EdgeSeen:
-- above it the grid patch shows on the step, WallGrid.client). all world heights (a copy keeps its arena's height)
local function wallBox(root: Instance, L: any, O: Vector3)
	root:SetAttribute("SkyY", if L.skyY then O.Y + L.skyY else nil)
	root:SetAttribute("EdgeTop", if L.edgeTop then O.Y + L.edgeTop else nil)
	root:SetAttribute("EdgeSeen", if L.edgeSeen then O.Y + L.edgeSeen else nil)
end

-- the jump pads: invisible parts with their throw (attribute Pad, Move.client); the kit draws them
local function padParts(L: any, O: Vector3, pads: Instance)
	for _, b in L.pads do
		local p = Instance.new("Part")
		p.Name = "pad"
		p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = true; p.CastShadow = false
		p.Transparency = 1; p.Material = SP
		p.Size = V3(b[4] - b[1], b[5] - b[2], b[6] - b[3])
		p.CFrame = CF(O + V3((b[1] + b[4]) / 2, (b[2] + b[5]) / 2, (b[3] + b[6]) / 2))
		p:SetAttribute("Mat", "pad")
		p:SetAttribute("Pad", V3(b[7], b[8], b[9]))
		p.Parent = pads
	end
end

function W.clear(name: string): string
	local old = workspace.Map:FindFirstChild(name)
	if old then old:Destroy() end
	for _, p in CollectionService:GetTagged("JankWater") do
		if p:IsDescendantOf(workspace) and p:GetAttribute("Arena") == name then p:Destroy() end
	end
	return "cleared " .. name
end

function W.build(name: string): string
	local L = layout(name)
	local O: Vector3 = L.origin
	local at = CF(O)
	W.clear(name)
	local root = Instance.new("Model")
	root.Name = name
	root:SetAttribute("KillY", O.Y + L.killY)
	root:SetAttribute("MapId", L.mapId)
	root:SetAttribute("StudsPerMetre", 3)
	root:SetAttribute("CentreX", O.X + L.centreX)
	root:SetAttribute("Title", L.title)
	root:SetAttribute("Look", L.look)
	if L.maxTeam and L.maxTeam > 0 then root:SetAttribute("MaxTeam", L.maxTeam) end
	root:SetAttribute("ZonePiece", true)
	root:SetAttribute("Built", os.date("!%Y-%m-%d %H:%M"))
	local shell = folder(root, "Shell")
	local solid = folder(root, "Solid")
	local pads = folder(root, "Pads")
	local spawns = folder(root, "Spawns")
	local team = folder(root, "TeamSpawns")
	local water = folder(root, "Water")
	local lights = folder(root, "Lights")
	local back = folder(root, "Backdrop")
	root.WorldPivot = at
	root.Parent = workspace.Map
	hitBoxes(L, O, solid)
	wallBox(root, L, O)
	padParts(L, O, pads)
	for i, s in L.spawns do -- plain parts (SpawnLocations would join Roblox's own spawning)
		marker(spawns, "Spawn" .. i, CF(O + V3(s[1], s[2], s[3])), V3(4, 0.2, 4))
	end
	for _, side in { "att", "def", "mid" } do
		for _, s in (L.team[side] or {}) do
			local p = marker(team, side, CF(O + V3(s[1], s[2], s[3])), V3(2, 0.2, 2))
			if s[4] then p:SetAttribute("Face", V3(s[4], 0, s[5])) end -- (its heading; Matches.teamSpawns turns you to it)
		end
	end
	for i, w in L.water do
		local p = marker(water, "Water" .. i, CF(O + V3((w[1] + w[4]) / 2, (w[2] + w[5]) / 2, (w[3] + w[6]) / 2)), V3(w[4] - w[1], w[5] - w[2], w[6] - w[3]))
		p:SetAttribute("Arena", name)
		CollectionService:AddTag(p, "JankWater")
	end
	-- the look: every model of the kit, its origin at the arena's origin
	local nm = 0
	for _, t in lib():GetChildren() do
		if t:GetAttribute("Kit") ~= L.kit then continue end
		local m = t:Clone()
		m:PivotTo(at)
		m.Parent = shell
		nm += 1
		if nm % 6 == 0 then task.wait() end
	end
	for _, l in L.lights do
		local pos = O + V3(l[2], l[3], l[4])
		local dir = V3(l[5], l[6], l[7])
		local a = marker(lights, "Light", CF(pos), V3(0.4, 0.4, 0.4))
		if dir.Magnitude > 1e-3 then a.CFrame = CFrame.lookAt(pos, pos + dir.Unit) end
		local li: Light = if l[1] == "spot" then Instance.new("SpotLight") else Instance.new("PointLight")
		li.Brightness = l[8]; (li :: any).Range = l[9]; li.Color = hex(l[11]); li.Shadows = false
		if l[1] == "spot" then (li :: any).Angle = l[10]; (li :: any).Face = Enum.NormalId.Front end
		li.Parent = a
	end
	-- the backdrop: look-only boxes too big or too far for the kit (Roblox shrinks an upload past 2,048 studs), as plain
	-- Parts, each cut into tiles under 2,000 studs a side
	local nb = 0
	for _, b in (L.backdrop or {}) do
		local size = V3(b[4] - b[1], b[5] - b[2], b[6] - b[3])
		local n = V3(math.ceil(size.X / 2000), math.ceil(size.Y / 2000), math.ceil(size.Z / 2000))
		local t = V3(size.X / n.X, size.Y / n.Y, size.Z / n.Z)
		for i = 0, n.X - 1 do for j = 0, n.Y - 1 do for k = 0, n.Z - 1 do
			local p = Instance.new("Part")
			p.Name = "Backdrop"
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
			p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
			p.Material = MAT[b[8]] or SP; p.Transparency = SEE[b[8]] or 0; p.Color = hex(b[7])
			p.Size = t
			p.CFrame = CF(O + V3(b[1] + (i + 0.5) * t.X, b[2] + (j + 0.5) * t.Y, b[3] + (k + 0.5) * t.Z))
			p.Parent = back
			nb += 1
		end end end
	end
	if nm == 0 then return "built " .. name .. " WITHOUT its kit (run W.import first)" end
	return ("built %s at %s: %d kit models, %d hit boxes, %d pads, %d spawns, %d team spawns, %d water, %d lights, %d backdrop parts"):format(
		name, tostring(O), nm, #L.solid + #(L.solidR or {}), #L.pads, #L.spawns, #team:GetChildren(), #L.water, #L.lights, nb)
end

-- just the hit boxes again, from the layout (the kit, the lights and everything set on the arena by hand stay: the Gut's
-- heart, the desert's wind, SuburbV2's Enabled). for a change to the hit boxes only, like the wall box (18 Nov)
function W.solid(name: string): string
	local root = workspace.Map:FindFirstChild(name)
	if not root then return name .. " is not built" end
	local L = layout(name)
	local O: Vector3 = L.origin
	local old = root:FindFirstChild("Solid")
	local n0 = if old then #old:GetChildren() else 0
	local solid = folder(root, "Solid")
	solid.Parent = nil
	hitBoxes(L, O, solid)
	if old then old:Destroy() end
	solid.Parent = root
	wallBox(root, L, O)
	-- (and the pads again: 18 Nov 2026, the open roofs brought new ones)
	local oldPads = root:FindFirstChild("Pads")
	local p0 = if oldPads then #oldPads:GetChildren() else 0
	local pads = folder(root, "Pads")
	pads.Parent = nil
	padParts(L, O, pads)
	if oldPads then oldPads:Destroy() end
	pads.Parent = root
	return ("%s: hit boxes %d -> %d, pads %d -> %d, SkyY %s, EdgeTop %s, EdgeSeen %s"):format(name, n0, #solid:GetChildren(), p0, #pads:GetChildren(),
		tostring(root:GetAttribute("SkyY")), tostring(root:GetAttribute("EdgeTop")), tostring(root:GetAttribute("EdgeSeen")))
end

-- ---------------------------------------------------------------- checks
local function segHits(a: Vector3, b: Vector3, p: BasePart): boolean
	local c = p.CFrame
	local h = p.Size / 2
	local pa, pb = c:PointToObjectSpace(a), c:PointToObjectSpace(b)
	local d = pb - pa
	local t0, t1 = 0, 1
	for _, k in { "X", "Y", "Z" } do
		local dk, pk, hk = (d :: any)[k], (pa :: any)[k], (h :: any)[k]
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

function W.check(name: string): string
	local root = workspace.Map:FindFirstChild(name)
	if not root then return name .. " is not built" end
	local L = layout(name)
	local O: Vector3 = L.origin
	local out = {}
	-- 1. the hit boxes are the layout's (the web's boxes x3)
	local have = root.Solid:GetChildren()
	local bad = 0
	-- (each layout box needs a built one within 0.05 stud, same size: float precision far from the world's origin is
	-- a few thousandths, so exact keys would not do)
	local cells: { [string]: { BasePart } } = {}
	local function cell(v: Vector3): string return ("%d %d %d"):format(math.floor(v.X / 4), math.floor(v.Y / 4), math.floor(v.Z / 4)) end
	for _, p in have do
		if p:IsA("BasePart") then
			local k = cell(p.Position - O)
			cells[k] = cells[k] or {}
			table.insert(cells[k], p)
		end
	end
	local used = {}
	local want = {}
	for _, b in L.solid do
		table.insert(want, { V3((b[1] + b[4]) / 2, (b[2] + b[5]) / 2, (b[3] + b[6]) / 2), V3(b[4] - b[1], b[5] - b[2], b[6] - b[3]) })
	end
	for _, b in (L.solidR or {}) do table.insert(want, { V3(b[1], b[2], b[3]), V3(b[4], b[5], b[6]) }) end
	for _, w in want do
		local c, size = w[1], w[2]
		local found = false
		for dx = -1, 1 do for dy = -1, 1 do for dz = -1, 1 do
			if found then continue end
			for _, p in cells[cell(c + V3(dx, dy, dz) * 2)] or {} do
				if not used[p] and ((p.Position - O) - c).Magnitude < 0.05 and (p.Size - size).Magnitude < 0.05 then used[p] = true; found = true; break end
			end
		end end end
		if not found then bad += 1 end
	end
	local extra = 0
	for _, p in have do if p:IsA("BasePart") and not used[p] then extra += 1 end end
	table.insert(out, ("hit boxes: %d in the layout, %d built, %d missing, %d extra"):format(#want, #have, bad, extra))
	-- 1b. the wall box (wallbox.py): no lid (nothing solid stands over the sky line but the walls), the walls and the step
	local sky = root:GetAttribute("SkyY")
	if type(sky) == "number" then
		local over, bound, ledge, lid = 0, 0, 0, 0
		for _, p in have do
			if not p:IsA("BasePart") then continue end
			local m = p:GetAttribute("Mat")
			if m == "bound" then bound += 1 elseif m == "ledge" then ledge += 1 end
			local top = p.Position.Y + p.Size.Y / 2
			if top > sky and m ~= "bound" then over += 1 end
			if p.Size.Y < 12 and p.Size.X > 150 and p.Size.Z > 150 and p.Position.Y > sky then lid += 1 end
		end
		table.insert(out, ("wall box: SkyY %.0f, EdgeTop %.0f, EdgeSeen %.0f; walls %d, step boxes %d; a lid: %d; other solids reaching past the sky line: %d (the old lid's columns, out of reach)"):format(
			sky, root:GetAttribute("EdgeTop") or 0, root:GetAttribute("EdgeSeen") or 0, bound, ledge, lid, over))
	end
	-- 1c. the roofs (roofs.py): body-only columns standing higher than 40 over the street (the old ceilings over the
	-- roofs: none once a map's roofs are open), and the roofs that shed you (Slide)
	do
		local cols, slide = 0, 0
		for _, p in have do
			if not p:IsA("BasePart") then continue end
			if p.CollisionGroup == RAYBLIND and p.Position.Y + p.Size.Y / 2 > O.Y + 40 then cols += 1 end
			if p:GetAttribute("Slide") then slide += 1 end
		end
		table.insert(out, ("roofs: %d body-only columns over 40 (ceilings over roofs), %d boxes that shed you (Slide)"):format(cols, slide))
	end
	-- 2. every spawn stands on something solid within a stud under it
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { root.Solid, root.Pads }
	local function floored(f: Instance): (number, number)
		local n, ok = 0, 0
		for _, s in f:GetChildren() do
			if not s:IsA("BasePart") then continue end
			n += 1
			local r = workspace:Raycast(s.Position + V3(0, 2, 0), V3(0, -4, 0), rp)
			if r and (s.Position.Y - r.Position.Y) < 1.0 and (s.Position.Y - r.Position.Y) > -0.5 then ok += 1 end
		end
		return ok, n
	end
	local a1, n1 = floored(root.Spawns)
	local a2, n2 = floored(root.TeamSpawns)
	table.insert(out, ("spawns on a floor: %d of %d; team spawns: %d of %d"):format(a1, n1, a2, n2))
	-- 3. team spawn sight lines (through the hit boxes)
	local solids = root.Solid:GetChildren()
	local function blocked(a: Vector3, b: Vector3): boolean
		for _, p in solids do if (p :: BasePart).CanCollide and segHits(a, b, p :: BasePart) then return true end end
		return false
	end
	local att, def = {}, {}
	for _, s in root.TeamSpawns:GetChildren() do
		if s.Name == "att" then table.insert(att, (s :: BasePart).Position) elseif s.Name == "def" then table.insert(def, (s :: BasePart).Position) end
	end
	local open, n = 0, 0
	for _, a in att do for _, b in def do
		for _, h in { 2.5, 4.6 } do
			n += 1
			if not blocked(a + V3(0, h, 0), b + V3(0, h, 0)) then open += 1 end
		end
	end end
	table.insert(out, ("team spawn sight lines open: %d of %d"):format(open, n))
	-- 4. the fall line, the pads' flights
	local lowest = math.huge
	for _, b in L.solid do lowest = math.min(lowest, b[5]) end
	table.insert(out, ("KillY %.1f (local %.1f; the lowest hit box top is %.1f), CentreX %.1f, Title %s, Look %s, MaxTeam %s"):format(
		root:GetAttribute("KillY"), L.killY, lowest, root:GetAttribute("CentreX"), tostring(root:GetAttribute("Title")), tostring(root:GetAttribute("Look")), tostring(root:GetAttribute("MaxTeam"))))
	for _, pad in root.Pads:GetChildren() do
		local v: Vector3 = (pad :: BasePart):GetAttribute("Pad") :: Vector3
		local pos, t, landed = (pad :: BasePart).Position + V3(0, 3, 0), 0, nil
		while t < 4 do
			local nxt = pos + v / 60
			v -= V3(0, workspace.Gravity / 60, 0)
			t += 1 / 60
			for _, p in solids do
				if (p :: BasePart).CanCollide and segHits(pos - V3(0, 2.6, 0), nxt - V3(0, 2.6, 0), p :: BasePart) then landed = nxt; break end
			end
			pos = nxt
			if landed then break end
		end
		local rel = (landed or pos) - O
		table.insert(out, ("pad at %s lands at (%.1f, %.1f, %.1f) after %.2f s%s"):format(tostring((pad :: BasePart).Position - O), rel.X, rel.Y - 2.6, rel.Z, t, if landed then "" else " (NO LANDING)"))
	end
	-- 5. what is drawn: no kit part is solid or blocks shots; what it costs
	local solidKit, meshes, tris = 0, 0, 0
	for _, d in root.Shell:GetDescendants() do
		if d:IsA("BasePart") then
			meshes += 1
			if d.CanCollide or d.CanQuery then solidKit += 1 end
		end
	end
	local parts = 0
	for _, d in root:GetDescendants() do if d:IsA("BasePart") then parts += 1 end end
	table.insert(out, ("kit parts that collide or take shots: %d; parts in the arena %d (kit meshes %d, hit boxes %d), lights %d"):format(
		solidKit, parts, meshes, #solids, #root.Lights:GetChildren()))
	return table.concat(out, "\n")
end

-- ---------------------------------------------------------------- the rotation
-- W.pool("add", name) / W.pool("remove", name) / W.pool("only", name) / W.pool("set", "RooftopV2,RooftopV3,Crate")
function W.pool(op: string, what: string): string
	local map = workspace.Map
	local cur = map:GetAttribute("ArenaPool")
	local list = {}
	if type(cur) == "string" then for n in string.gmatch(cur, "[^,%s]+") do table.insert(list, n) end end
	if op == "add" then
		if not map:FindFirstChild(what) then return what .. " is not built" end
		if not table.find(list, what) then table.insert(list, what) end
	elseif op == "remove" then
		local i = table.find(list, what)
		if i then table.remove(list, i) end
	elseif op == "only" then
		list = { what }
	elseif op == "set" then
		list = {}
		for n in string.gmatch(what, "[^,%s]+") do table.insert(list, n) end
	end
	for _, n in list do if not map:FindFirstChild(n) then return n .. " is not built: pool left as " .. tostring(cur) end end
	map:SetAttribute("ArenaPool", table.concat(list, ","))
	return "ArenaPool = " .. table.concat(list, ",")
end

return W
