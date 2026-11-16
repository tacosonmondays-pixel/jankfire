--!nocheck
-- ROOFTOP V3 (16 Nov 2026): v1's layout kept exactly, redressed to the design principles of 16 Nov. The owner:
-- "rooftop v3 can it follow ther layout of v1 just updated with the new principles, loike the props but keep the layout
-- the same yk what I mean I really like v2 too keep working on it".
-- the collision is v1's own: R.build() copies every hit box of workspace.Map.Rooftop (Solid, the structure pass's
-- DressSolid cover, Pads, Spawns, TeamSpawns, Water) into workspace.Map.RooftopV3 at its own site, invisible, so v3
-- plays exactly like v1. the look is one Blender kit ("rooftop3": tools/roblox/rooftop3_models.py > rooftop3.glb > one
-- Model asset) made from the same boxes (tools/roblox/rooftop3_v1.json). the city round it reuses v2's tower designs.
-- v1 and v2 are never touched. which arena matches use is workspace.Map's attribute "Arena", and the rotation they
-- take turns from its attribute "ArenaPool" (ReplicatedStorage.Jankfire.Arena; Matches picks at each match's start).
-- run in Edit, from a clone (a require of the original is cached):
--   local R = require(game.ServerStorage.PolishBackup.RooftopV3:Clone())
--   R.import()        the kit's models into ServerStorage.JankfireMeshes (r3_*)
--   R.build()         wipe and rebuild workspace.Map.RooftopV3            R.clear()   take it away
--   R.check()         the copy is v1's collision exactly; spawn sight lines, clear spawns, pad flights
--   R.use("both")     matches take turns on v2 and v3 (the owner's pick, 16 Nov); R.use("all") adds v1
--   R.use("v3")       pins matches to v3 alone (the pool is just v3); "v2" for v2, "v1" for the old one
local ServerStorage = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local CollectionService = game:GetService("CollectionService")

local R = {}
R.NAME = "RooftopV3"
R.KIT = "rooftop3"
R.ASSET = 109680564367482 -- the uploaded rooftop3.glb (Model asset "jf_rooftop3_<n>"); set after each upload
local hex = Color3.fromHex
local V3, CF = Vector3.new, CFrame.new
local SP = Enum.Material.SmoothPlastic
local MAT = { plastic = SP, neon = Enum.Material.Neon, glass = Enum.Material.Glass, water = SP } -- (water: Glass drew busy white foam)
local SEE = { glass = 0.35, water = 0.25 }

local function lib(): Instance return ServerStorage:WaitForChild("JankfireMeshes") end
local function v1(): Instance return workspace.Map:FindFirstChild("Rooftop") end
local function layout()
	local m = ServerStorage.PolishBackup.RooftopV3Layout:Clone()
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
		d.Transparency = SEE[kind] or 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind == "plastic"
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
local function marker(parent: Instance, name: string, cf: CFrame, size: Vector3?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size or V3(2, 0.2, 2); p.CFrame = cf; p.Parent = parent
	return p
end
local function look(parent: Instance, name: string, cf: CFrame, size: Vector3, color: Color3): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Material = SP; p.Color = color; p.Size = size; p.CFrame = cf; p.Parent = parent
	return p
end
-- a copy of one of v1's hit boxes, moved to v3's site, invisible (the kit is the look). keeps v1's collision flags and
-- attributes (Mat: footsteps and impacts), drops anything drawn on it
local function hitCopy(p: BasePart, shift: CFrame, parent: Instance): BasePart
	local c = p:Clone()
	for _, ch in c:GetChildren() do
		if ch:IsA("Decal") or ch:IsA("Texture") or ch:IsA("SurfaceGui") or ch:IsA("Light") or ch:IsA("ParticleEmitter") then ch:Destroy() end
	end
	c.CFrame = shift * p.CFrame
	c.Transparency = 1; c.CastShadow = false; c.Anchored = true
	c:SetAttribute("DressHid", nil)
	c.Parent = parent
	return c
end

-- ---------------------------------------------------------------- the city round it (v2's tower designs, a fixed seed)
local CITY = {
	body = { hex("9da0a6"), hex("8c9096"), hex("a6a29a"), hex("7d8189"), hex("b0aca4"), hex("949089") },
	street = hex("3c4049"), smog = hex("929bab"), horizon = hex("b9c1cf"),
	-- (round 2: the arena melted into a city of its own pale colour) v3's copies of v2's towers are pulled toward a cool
	-- slate, so the warm arena stands out; v2's own templates are not touched
	cool = Color3.fromRGB(72, 80, 94), coolBy = 0.6, -- (rounds 3 and 4: darker and cooler)
}
local TOWERS = { "r2_twa", "r2_twb", "r2_twc", "r2_twd", "r2_twe", "r2_twf", "r2_twe", "r2_twf" }
local LANDMARKS = { { 430, 330, 230 }, { -470, -300, 210 }, { -60, -560, 250 } }
local TWH = 760 -- each v2 tower design's height from its foot (tools/roblox/rooftop2_models.py, TWH)
local function city(root: Instance, O: Vector3): number
	local f = folder(root, "City")
	local rng = Random.new(1603)
	look(f, "Street", CF(O + V3(0, -466, 0)), V3(2048, 2, 2048), CITY.street)
	for ix = -1, 1 do -- the smog: a pale layer far below the roofs ("into the smog"), so no edge of the ground shows
		for iz = -1, 1 do
			local sm = look(f, "Smog", CF(O + V3(ix * 2048, -260, iz * 2048)), V3(2048, 1, 2048), CITY.smog)
			sm.Transparency = 0.15
		end
	end
	local n = 0
	for gx = -660, 660, 66 do
		for gz = -520, 520, 66 do
			local ax, az = math.abs(gx), math.abs(gz)
			if ax < 220 and az < 130 then continue end -- the arena's own three towers (x -175..175, z -85..85)
			if rng:NextNumber() < 0.25 then continue end
			local nearMark = false
			for _, l in LANDMARKS do if math.abs(gx - l[1]) < 70 and math.abs(gz - l[2]) < 70 then nearMark = true end end
			if nearMark then continue end
			local x, z = gx + rng:NextInteger(-6, 6), gz + rng:NextInteger(-6, 6)
			local dist = math.max(ax / 1.3, az)
			local top = if dist < 260 then rng:NextInteger(-170, -40) elseif dist < 420 then rng:NextInteger(-90, 20) else rng:NextInteger(-10, 150)
			if rng:NextNumber() < 0.12 and dist > 380 then top += 90 end
			local t = lib():FindFirstChild(TOWERS[rng:NextInteger(1, #TOWERS)])
			if not t then continue end
			local m = t:Clone()
			m.Name = "Tower"
			for _, d in m:GetDescendants() do
				if d:IsA("BasePart") and d.Material ~= Enum.Material.Neon then d.Color = d.Color:Lerp(CITY.cool, CITY.coolBy) end
			end
			m:PivotTo(CF(O + V3(x, top - TWH, z)) * CFrame.Angles(0, rng:NextInteger(0, 3) * math.pi / 2, 0))
			m.Parent = f
			n += 1
			if n % 20 == 0 then task.wait() end
		end
	end
	for i = 0, 7 do -- a pale ring at the horizon, the haze's own colour, so nothing far out stands black
		local ang = i * math.pi / 4
		local cf = CF(O + V3(math.sin(ang) * 2400, -60, math.cos(ang) * 2400)) * CFrame.Angles(0, ang, 0)
		look(f, "Horizon", cf, V3(2048, 420, 4), CITY.horizon)
	end
	for _, l in LANDMARKS do
		local t = lib():FindFirstChild("r2_twg")
		if t then
			local m = t:Clone()
			m.Name = "Landmark"
			for _, d in m:GetDescendants() do
				if d:IsA("BasePart") and d.Material ~= Enum.Material.Neon then d.Color = d.Color:Lerp(CITY.cool, CITY.coolBy) end
			end
			m:PivotTo(CF(O + V3(l[1], l[3] - TWH, l[2])))
			m.Parent = f
		end
	end
	for _ = 1, 90 do -- low blocks along the streets far below
		local x, z = rng:NextInteger(-700, 700), rng:NextInteger(-560, 560)
		if math.abs(x) < 190 and math.abs(z) < 100 then continue end
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
	local src = v1()
	if not src then return "v1 (workspace.Map.Rooftop) is missing: v3 copies its collision" end
	local L = layout()
	local O: Vector3 = L.origin
	local shift = CF(O)
	R.clear()
	local root = Instance.new("Model")
	root.Name = R.NAME
	root:SetAttribute("KillY", src:GetAttribute("KillY") or L.killY)
	root:SetAttribute("MapId", "rooftop_v3")
	root:SetAttribute("StudsPerMetre", src:GetAttribute("StudsPerMetre") or 3)
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
	root.WorldPivot = shift
	-- v1's collision, exactly: Solid, the structure pass's DressSolid cover, pads, spawns, team spawns, water
	local ns, nd = 0, 0
	for i, p in src.Solid:GetDescendants() do
		if p:IsA("BasePart") then hitCopy(p, shift, solid); ns += 1 end
		if i % 150 == 0 then task.wait() end
	end
	local dress = src:FindFirstChild("Dress")
	if dress then
		for _, p in dress:GetDescendants() do
			if p:IsA("BasePart") and p.CanCollide then
				local c = hitCopy(p, shift, solid)
				c:SetAttribute("FromDress", true)
				nd += 1
			end
		end
	end
	for _, p in src.Pads:GetChildren() do
		if p:IsA("BasePart") then hitCopy(p, shift, pads) end
	end
	for _, s in src.Spawns:GetChildren() do -- plain parts (SpawnLocations would join Roblox's own spawning)
		if s:IsA("BasePart") then marker(spawns, s.Name, shift * s.CFrame, s.Size) end
	end
	for _, s in src.TeamSpawns:GetChildren() do
		if s:IsA("BasePart") then hitCopy(s, shift, team) end
	end
	for _, w in src.Water:GetChildren() do
		if w:IsA("BasePart") then
			local c = hitCopy(w, shift, water)
			c:SetAttribute("Arena", R.NAME)
			CollectionService:AddTag(c, "JankWater")
		end
	end
	-- the look: every model of the kit, its origin at the arena's origin
	local nm = 0
	for _, t in lib():GetChildren() do
		if t:GetAttribute("Kit") ~= R.KIT then continue end
		local m = t:Clone()
		m:PivotTo(shift)
		m.Parent = shell
		nm += 1
		task.wait()
	end
	-- lights: an invisible anchor per light
	for _, l in L.lights do
		local at = O + V3(l[2], l[3], l[4])
		local dir = V3(l[5], l[6], l[7])
		local a = marker(lights, "Light", CF(at), V3(0.4, 0.4, 0.4))
		if dir.Magnitude > 1e-3 then a.CFrame = CFrame.lookAt(at, at + dir.Unit) end
		local li = if l[1] == "spot" then Instance.new("SpotLight") else Instance.new("PointLight")
		li.Brightness = l[8]; li.Range = l[9]; li.Color = hex(l[11]); li.Shadows = false
		if l[1] == "spot" then li.Angle = l[10]; li.Face = Enum.NormalId.Front end
		li.Parent = a
	end
	local nt = city(root, O)
	return ("built %s at %s: %d kit models, %d of v1's hit boxes + %d cover boxes, %d spawns, %d team spawns, %d pads, %d water, %d lights, %d towers"):format(
		R.NAME, tostring(O), nm, ns, nd, #spawns:GetChildren(), #team:GetChildren(), #pads:GetChildren(), #water:GetChildren(), #L.lights, nt)
end

-- ---------------------------------------------------------------- checks
local function segHits(a: Vector3, b: Vector3, p: BasePart): boolean
	local c = p.CFrame
	local h = p.Size / 2
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
	local src = v1()
	if not root then return "not built" end
	if not src then return "v1 is missing" end
	local L = layout()
	local O: Vector3 = L.origin
	local out = {}
	-- 1. the copy is v1's collision exactly (same boxes, same flags, moved by O)
	-- (each v1 box needs a copy within 0.01 stud, same size, same flags, same turn: float precision at z -30000 is
	-- about 0.002, so exact keys would not do)
	local function same(p: BasePart, q: BasePart): boolean
		return ((q.Position - O) - p.Position).Magnitude < 0.01 and (q.Size - p.Size).Magnitude < 0.001
			and q.CanCollide == p.CanCollide and q.CanQuery == p.CanQuery
			and (q.CFrame.LookVector - p.CFrame.LookVector).Magnitude < 1e-4 and (q.CFrame.UpVector - p.CFrame.UpVector).Magnitude < 1e-4
	end
	local function cell(v: Vector3): string return ("%d %d %d"):format(math.floor(v.X / 4), math.floor(v.Y / 4), math.floor(v.Z / 4)) end
	local pool = {}
	local function addHave(q: BasePart, tag: string)
		local v = q.Position - O
		for dx = -1, 1 do for dy = -1, 1 do for dz = -1, 1 do
			local k = tag .. cell(v + V3(dx, dy, dz) * 2)
			pool[k] = pool[k] or {}
			if not table.find(pool[k], q) then table.insert(pool[k], q) end
		end end end
	end
	for _, q in root.Solid:GetChildren() do if q:IsA("BasePart") then addHave(q, "") end end
	for _, f in { "Pads", "TeamSpawns", "Water" } do
		for _, q in root[f]:GetChildren() do if q:IsA("BasePart") then addHave(q, f) end end
	end
	local used, missing, nv1, nwant = {}, 0, 0, 0
	local function find(p: BasePart, tag: string)
		nwant += 1
		for _, q in pool[tag .. cell(p.Position)] or {} do
			if not used[q] and same(p, q) then used[q] = true; return end
		end
		missing += 1
	end
	for _, p in src.Solid:GetDescendants() do if p:IsA("BasePart") then find(p, ""); nv1 += 1 end end
	if src:FindFirstChild("Dress") then
		for _, p in src.Dress:GetDescendants() do if p:IsA("BasePart") and p.CanCollide then find(p, "") end end
	end
	for _, f in { "Pads", "TeamSpawns", "Water" } do
		for _, p in src[f]:GetChildren() do if p:IsA("BasePart") then find(p, f) end end
	end
	local nhave = 0
	for _ in used do nhave += 1 end
	local total = #root.Solid:GetChildren() + #root.Pads:GetChildren() + #root.TeamSpawns:GetChildren() + #root.Water:GetChildren()
	local extra = total - nhave
	local sp1, sp3 = #src.Spawns:GetChildren(), #root.Spawns:GetChildren()
	table.insert(out, ("v1's collision copied: %d boxes missing, %d extra (v1 Solid %d, the kit was dressed from %d); spawns %d of %d"):format(missing, extra, nv1, L.v1Boxes, sp3, sp1))
	-- 2. team spawn sight lines (through v1's own boxes)
	local solids = root.Solid:GetChildren()
	local function blocked(a: Vector3, b: Vector3): boolean
		for _, p in solids do if p.CanCollide and segHits(a, b, p) then return true end end
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
	table.insert(out, ("team spawn sight lines open: %d of %d (v1's own layout)"):format(open, n))
	-- 3. kill line, pads
	table.insert(out, ("KillY %.1f, CentreX %.1f"):format(root:GetAttribute("KillY"), root:GetAttribute("CentreX")))
	for _, pad in root.Pads:GetChildren() do
		local v: Vector3 = pad:GetAttribute("Pad")
		if typeof(v) ~= "Vector3" then table.insert(out, "pad without a Pad attribute: " .. pad:GetFullName()); continue end
		local pos, t, landed = pad.Position + V3(0, 3, 0), 0, nil
		while t < 3 do
			local nxt = pos + v / 60
			v -= V3(0, workspace.Gravity / 60, 0)
			t += 1 / 60
			for _, p in solids do
				if p.CanCollide and segHits(pos - V3(0, 2.6, 0), nxt - V3(0, 2.6, 0), p) then landed = nxt; break end
			end
			pos = nxt
			if landed then break end
		end
		local rel = (landed or pos) - O
		table.insert(out, ("pad at %s lands at (%.1f, %.1f, %.1f) after %.2f s"):format(tostring(pad.Position - O), rel.X, rel.Y - 2.6, rel.Z, t))
	end
	-- 4. what is drawn: no kit part is solid or blocks shots
	local bad = 0
	for _, d in root.Shell:GetDescendants() do if d:IsA("BasePart") and (d.CanCollide or d.CanQuery) then bad += 1 end end
	table.insert(out, ("kit parts that collide or take shots: %d"):format(bad))
	return table.concat(out, "\n")
end

-- ---------------------------------------------------------------- the switch
-- one arena ("v1", "v2", "v3") pins matches to it: the pool is just that one. "both" = v2 and v3 take turns (Matches
-- picks at each match's start, a random one first after a server starts, never the same twice in a row); "all" adds v1
local USE = { v1 = "Rooftop", v2 = "RooftopV2", v3 = R.NAME, Rooftop = "Rooftop", RooftopV2 = "RooftopV2", RooftopV3 = R.NAME }
function R.use(which: string): string
	local list = if which == "both" then { "RooftopV2", R.NAME } elseif which == "all" then { "Rooftop", "RooftopV2", R.NAME } else { USE[which] or "Rooftop" }
	for _, n in list do
		if not workspace.Map:FindFirstChild(n) then return n .. " is not built" end
	end
	workspace.Map:SetAttribute("ArenaPool", table.concat(list, ","))
	workspace.Map:SetAttribute("Arena", list[1])
	return "matches now use " .. table.concat(list, " and ")
end

return R
