--!nocheck
-- TRAINING V2: the training area rebuilt to the 16 Nov 2026 design principles, and its edit-time builder. the owner, 16
-- Nov: "can we rebuild a new training area too with our new design principles as well as a version of rooftop that
-- follows our design principles? Keep the current one rooftop v1 vs v2 and we'll compare". about the old hall (14 Nov):
-- "rn its big with a lot of empty space yk". the old hall stays as v1, one switch away.
-- the idea: a small eight-sided MUSTER room you arrive in (a lantern drum over a low round dais), and three rooms off it,
-- each with one job and its own shape and ceiling: the DUMMY YARD straight ahead (a ribbed vault, the Plinker's round
-- stand and a big target at its end), the FIRING RANGE on the right (Cardboard Carl's: booths under a coffered canopy,
-- then a lane open to the sky stepping up in terraces), the MOVEMENT COURSE on the left (the tallest room: ledges up the
-- west wall with jump pads, a tower with a chute down, a pit to slide-jump, grapple discs, the playground's secret
-- bullseye). a bench bay off the muster is the place to stop. plan and log: vault Hubs\Training v2 plan.md
--   usage (Studio's command bar, Edit; a require of the original is cached, so require a clone):
--     local T = require(game.ServerStorage.PolishBackup.TrainingV2:Clone())
--     T.import()          the kit (tools/roblox/training_models.py, Model asset T.KIT) into ServerStorage.JankfireMeshes
--     T.build("stage")    a copy to look at, T.STAGE studs east of the real site, under workspace.Map.TrainingStage
--     T.build("live")     v2 for real: parks v1 in PolishBackup.TrainingV1 the first time, then wipes and remakes
--                         Hub.TrainingGround and every marker the game reads (below). = T.switch("v2")
--     T.switch("v1")      the old hall back, exactly as it was (copied out of PolishBackup.TrainingV1)
--     T.check()           markers, the zone, the Plinker's view of the spawn points, every plate's view of every Carl
--     T.unstage()         takes the staging copy away
-- what the game reads, by name (all remade by a live build; the hub session owns Doors.RotundaToTraining and
-- Doors.HubArrive, never touched here): Hub.TrainSpawns (you arrive and respawn on these), Hub.DummySpots (Dummy,
-- Plinker, Stand1, Stand2), Hub.TrainingZone (inside it you are "in training"), Hub.Barrier (unseen walls round the
-- area), Hub.TrainingGround.Range (Plates, Spots, Board: RangeTest), Hub.TrainingGround.PropCollision.RangeCounterBox
-- (the hub builders clone it as their invisible box), Hub.Doors.ToHub (the way back), Hub.Doors.ToPlayground (the
-- secret), Hub.Doors.TrainingArrive (where the playground's way back lands). the gun sessions test at (-16, 243.2,
-- -8150) against Stand1 at (-16, 240, -8170): both kept.
-- push 10 (16 Nov, the owner: "can you add a large garage door that leads outside to the big rivals style training
-- grounds, you have to do like a little easter egg to get it or something"): the yard ends on a garage door, and
-- behind it THE BACK LOT, built by ServerStorage.PolishBackup.TrainingLot (roblox/studio-tools/TrainingLot.luau) from
-- here; the zone and the barrier take the lot in. the door and the egg are the server's: TheLot.server.luau.
-- a build wipes and remakes: change the builder, never the built parts. coordinates are the world's (the old hall's
-- site); a staging copy is the same build moved T.STAGE along x.
local T = {}
local SS = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local hub = workspace.Map.Hub
local SP, NEON = Enum.Material.SmoothPlastic, Enum.Material.Neon
local V3, CF = Vector3.new, CFrame.new

T.KIT = 88505948716411 -- the kit's Model asset (tv_kit_4: training_models.py; rework 3 added the flat grapple hoop)
T.STAGE = V3(400, 0, 0)
T.PUSH = 12
T.VERSION = "v2"

-- the paint: one quiet family for the big surfaces, colour only where it tells the player something
T.P = {
	wall = "b9b5ae", wall2 = "c4c0b8", warmWall = "c8bdae", pier = "8f9299", pier2 = "7d8088", trim = "e2ded5",
	floor = "7a7873", floor2 = "6c6a66", line = "a6a49e", ceil = "aeaba5", dark = "686d77", deep = "5a5f69", slate = "62666f",
	board = "4a4f58", courseFloor = "67655f", ledge = "7a7e86", ledgePanel = "6c7079", litEdge = "cfd2d6", recess = "50545c", courseWall = "a8a29a", mass = "d8d3ca", massPanel = "c6c0b5", lantern = "9ea3aa", tan = "b49a7a", amber = "f0a53a", amberGlow = "c48a3c", white = "f4f6f8", panel = "aeb2b8", warm = "ffd9a8", lampWhite = "f2efe8", red = "ff3b3b",
	cyan = "37d6ff", grey = "9aa0a8", pale = "eceae4",
	chill = "6fbf86", normal = "e8b440", sweaty = "d65a58",
}
local P = T.P
T.REMAP = { ["3d414a"] = P.deep, ["4a4e57"] = P.dark, ["2e3140"] = P.dark, ["17141f"] = P.dark, ["2a2d38"] = P.dark }
local MAT = { plastic = SP, neon = NEON }

-- the plan (world coordinates; y is height)
local Y0, MY = 240, 241                       -- the yard's floor (and the course's); the muster's floor
local MX, MZ, A, WALL = 0, -8122, 20, 4       -- the muster: its middle, its apothem, its wall
local MTOP = MY + 16                           -- the muster's wall tops (the cove starts there)
local TAN8 = math.tan(math.pi / 8)
T.SPOTS = { -- Cardboard Carl's: { x, floor y, z } feet of each Carl, three rows at 15, 30 and 45 m from the plates
	{ 37, 241.2, -8183 }, { 45.5, 241.2, -8183 }, { 54, 241.2, -8183 }, { 62.5, 241.2, -8183 }, { 71, 241.2, -8183 },
	{ 37, 245.2, -8228 }, { 45.5, 245.2, -8228 }, { 54, 245.2, -8228 }, { 62.5, 245.2, -8228 }, { 71, 245.2, -8228 },
	{ 38, 249.2, -8273 }, { 46, 249.2, -8273 }, { 54, 249.2, -8273 }, { 62, 249.2, -8273 }, { 70, 249.2, -8273 },
}
T.PLATES = { { "Easy", 40, "CHILL", "chill" }, { "Medium", 54, "NORMAL", "normal" }, { "Hard", 68, "SWEATY", "sweaty" } }
T.PLATE_Z = -8138
-- spawn points: two arcs either side of the dais, out of the line the Plinker sees through the yard's opening
T.SPAWNS = { { -12.5, -8111.5 }, { -15.5, -8117.5 }, { -11.5, -8132 }, { 12.5, -8111.5 }, { 15.5, -8117.5 }, { 11.5, -8132 } }
T.DUMMIES = { Dummy = { 0, 239, -8202 }, Plinker = { -15, 245.2, -8246 }, Stand1 = { -16, 240, -8170 }, Stand2 = { 16, 240, -8178 } }
T.ZONE = { -94, 86, 232, 312, -8092, -8308 } -- x0, x1, y0, y1, z0, z1 (the hall: its barrier)
T.FACE = -8300                                 -- the hall's back since push 10: the inside of the back lot's facade
T.LOT = { -186, 186, 440, -8734 }              -- the back lot: x0, x1, its lid, its far end (the zone takes it in)

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
local function lib() return SS:WaitForChild("JankfireMeshes") end

-- ---------------------------------------------------------------- the kit
-- one asset holds every model: a piece is "<model><n>__<kind>_<hex>"; the exporter turned them so they arrive in the
-- kit's own frame (pivot = the kit origin, the middle of the footprint on the floor; front +Z)
function T.import(): string
	local ok, container = pcall(function() return InsertService:LoadAsset(T.KIT) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
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
		m:SetAttribute("AssetId", T.KIT); m:SetAttribute("Kit", "training"); m:SetAttribute("FileFrame", true)
		local old = lib():FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib()
		local _, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(name, #parts, size.X, size.Y, size.Z))
	end
	container:Destroy()
	table.sort(names)
	return #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  ")
end

-- ---------------------------------------------------------------- the build context
local function new(live)
	local O = if live then Vector3.zero else T.STAGE
	local B = { live = live, O = O, count = 0, lamps = 0, shadows = 0, missing = {} }
	local root = Instance.new("Folder"); root.Name = "TrainingGround"
	for _, n in { "Shell", "Scenery", "Collision", "Range", "PropCollision" } do folderIn(root, n) end
	folderIn(root.Range, "Plates"); folderIn(root.Range, "Spots")
	B.root = root
	-- where the markers go: the hub itself (live) or the copy's own Game folder (stage: nothing reads them there)
	if live then
		B.mk = hub; B.doors = hub.Doors
	else
		local g = folderIn(root, "Game")
		B.mk = g; B.doors = folderIn(g, "Doors")
	end
	-- the hub builders' invisible box, made first so the solids below can be copies of it
	local box = Instance.new("Part")
	box.Name = "RangeCounterBox"; box.Anchored = true; box.Transparency = 1; box.CanCollide = true; box.CanQuery = true
	box.CanTouch = false; box.CastShadow = false; box.Material = Enum.Material.Plastic
	box.Size = V3(1, 1, 1); box.CFrame = CF(O)
	box.Parent = root.PropCollision
	B.boxSrc = box

	function B.cf(x, y, z) return CF(O.X + x, O.Y + y, O.Z + z) end
	function B.at(cf) return CF(O) * cf end -- a CFrame in plan coordinates into the world
	local function style(p, hex, o)
		p.Anchored = true
		p.Color = Color3.fromHex(hex); p.Material = o.mat or SP
		p.Transparency = o.tr or 0
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		if o.ghost then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false end
		if o.nc then p.CanCollide = false end
		if o.nq then p.CanQuery = false end
		if o.noShadow or p.Material == NEON then p.CastShadow = false end
		p.CanTouch = false
	end
	-- a block by its corners (plan coordinates; any order)
	function B.blk(folder, name, x0, x1, y0, y1, z0, z1, hex, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = name
		p.Size = V3(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(z1 - z0), 0.05))
		p.CFrame = B.cf((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		style(p, hex, o)
		p.Parent = root[folder]
		B.count += 1
		return p
	end
	-- a block at a CFrame (plan coordinates) with a size; o.wedge = a WedgePart, o.cyl = a cylinder (its axis along x)
	function B.part(folder, name, cf, size, hex, o)
		o = o or {}
		local p = Instance.new(if o.wedge then "WedgePart" else "Part")
		p.Name = name
		if o.cyl then p.Shape = Enum.PartType.Cylinder end
		p.Size = size; p.CFrame = B.at(cf)
		style(p, hex, o)
		p.Parent = root[folder]
		B.count += 1
		return p
	end
	-- a block in a turned frame F (a plan CFrame): x0..x1 across, y0..y1 up (absolute heights), d0..d1 out along -Z
	function B.fbox(F, folder, name, x0, x1, y0, y1, d0, d1, hex, o)
		local size = V3(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(d1 - d0), 0.05))
		return B.part(folder, name, F * CF((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2), size, hex, o)
	end
	-- an upright drum: dia across, y0..y1
	function B.drum(folder, name, x, z, y0, y1, dia, hex, o)
		local t = table.clone(o or {}); t.cyl = true
		return B.part(folder, name, CF(x, (y0 + y1) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), V3(y1 - y0, dia, dia), hex, t)
	end
	-- a slab whose top runs from (a0, h0) to (a1, h1) along x (axis "x") or z (axis "z"), w wide, 1 thick
	function B.ramp(folder, name, axis, a0, h0, a1, h1, c0, c1, hex, o)
		if a1 < a0 then a0, h0, a1, h1 = a1, h1, a0, h0 end
		local len = math.abs(a1 - a0)
		local ang = math.atan2(h1 - h0, a1 - a0)
		local mid = (a0 + a1) / 2
		local hy = (h0 + h1) / 2
		local w = math.abs(c1 - c0)
		local cm = (c0 + c1) / 2
		local th = (o and o.thick) or 1
		local hyp = len / math.cos(ang)
		local cf
		if axis == "x" then
			cf = CF(mid, hy, cm) * CFrame.Angles(0, 0, ang) * CF(0, -th / 2, 0)
			return B.part(folder, name, cf, V3(math.abs(hyp), th, w), hex, o)
		else
			-- along z: rising toward +z
			cf = CF(cm, hy, mid) * CFrame.Angles(-ang, 0, 0) * CF(0, -th / 2, 0)
			return B.part(folder, name, cf, V3(w, th, math.abs(hyp)), hex, o)
		end
	end
	-- an invisible box that stops players and shots (the line-of-sight rays read CanQuery)
	function B.solid(name, cf, size)
		local b = B.boxSrc:Clone()
		b.Name = name; b.Size = size; b.CFrame = B.at(cf); b.Parent = root.Collision
		return b
	end
	-- a model from the kit (or ServerStorage.JankfireMeshes), its pivot at cf (plan coordinates). o.color = { oldHex =
	-- newHex } (a piece's colour is the hex in its name), o.scale, o.name, o.raw (keep the kit's colours)
	function B.put(tmpl, cf, o)
		o = o or {}
		local t = lib():FindFirstChild(tmpl)
		if not t then B.missing[tmpl] = (B.missing[tmpl] or 0) + 1; return nil end
		local m = t:Clone()
		m.Name = o.name or tmpl
		if o.scale and math.abs(o.scale - 1) > 0.005 then
			m.Parent = workspace -- (ScaleTo wants the model in the place)
			m:ScaleTo(o.scale)
		end
		if t:GetAttribute("FileFrame") then
			m:PivotTo(B.at(cf))
		else
			-- an older kit model (KitImport): its pivot is the middle of its box; stand it on cf's floor point
			local bcf, sz = m:GetBoundingBox()
			m:PivotTo(B.at(cf) * CF(0, sz.Y / 2, 0) * m:GetPivot():ToObjectSpace(bcf):Inverse())
		end
		for _, p in m:GetDescendants() do
			if not p:IsA("BasePart") then continue end
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			local key = string.match(p.Name, "_(%x%x%x%x%x%x)$")
			local to = key and ((o.color and o.color[key]) or (not o.raw and T.REMAP[key]))
			if to then p.Color = Color3.fromHex(to) end
			if o.unglow and p.Material == NEON then p.Material = SP end
			if p.Material ~= NEON and p.Material ~= Enum.Material.Glass then p.Material = SP end
			if p.Material == NEON then p.CastShadow = false end
		end
		m.Parent = root.Scenery
		B.count += 1
		return m
	end
	-- words on a plate: lines = { { text, hex, "B" heavy or "S" semibold, share of the height }, ... }. cf's look is the
	-- way the words face (toward the reader). o.plate = its colour, o.clear = no plate, o.rich, o.thick
	function B.text(name, lines, w, h, cf, o)
		o = o or {}
		local thick = o.thick or 0.3
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Size = V3(w, h, thick)
		p.Color = Color3.fromHex(o.plate or P.board); p.Material = SP
		p.Transparency = if o.clear then 1 else 0
		p.CFrame = B.at(cf)
		local total, tallest = 0, 0
		for _, ln in lines do total += ln[4]; tallest = math.max(tallest, ln[4]) end
		local k = 0.9 / math.max(total, 0.01)
		local g = Instance.new("SurfaceGui")
		g.Name = "Gui"; g.Face = o.face or Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = math.min(o.pps or 28, math.max(8, math.floor(110 / math.max(tallest * k * h, 0.01))))
		g.LightInfluence = 0
		local yAt = 0.05
		for i, ln in lines do
			local t = Instance.new("TextLabel")
			t.Name = "Line" .. i; t.BackgroundTransparency = 1; t.TextScaled = true; t.RichText = o.rich or false
			t.Text = ln[1]; t.TextColor3 = Color3.fromHex(ln[2] or P.pale)
			t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", if ln[3] == "S" then Enum.FontWeight.SemiBold else Enum.FontWeight.Heavy)
			t.Size = UDim2.new(0.92, 0, ln[4] * k, 0); t.Position = UDim2.new(0.04, 0, yAt, 0)
			t.Parent = g
			yAt += ln[4] * k
		end
		g.Parent = p
		p.Parent = root.Scenery
		B.count += 1
		return p
	end
	-- a real light. kind "point" or "spot"; o.look = a plan point a spot aims at (else straight down), o.angle, o.shadows
	function B.lamp(x, y, z, kind, range, bright, hex, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = "Lamp"; p.Size = V3(0.6, 0.6, 0.6); p.Transparency = 1; p.Anchored = true
		p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		local at = V3(x, y, z)
		if o.look then p.CFrame = B.at(CFrame.lookAt(at, o.look)) else p.CFrame = B.cf(x, y, z) end
		local l = Instance.new(if kind == "spot" then "SpotLight" else "PointLight")
		l.Range = range; l.Brightness = bright; l.Color = Color3.fromHex(hex or P.lampWhite); l.Shadows = o.shadows or false
		if kind == "spot" then l.Face = if o.look then Enum.NormalId.Front else Enum.NormalId.Bottom; l.Angle = o.angle or 110 end
		l.Parent = p
		p.Parent = root.Scenery
		B.lamps += 1
		if l.Shadows then B.shadows += 1 end
		return p
	end
	-- a marker the game reads (a spawn point, a dummy's spot, a Carl's spot): small, unseen, not in anyone's way
	function B.marker(parent, name, x, y, z, look)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Size = V3(2, 0.2, 2); p.Transparency = 1
		p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		local at = V3(x, y, z)
		p.CFrame = B.at(if look then CFrame.lookAt(at, V3(look.X, y, look.Z)) else CF(at))
		p.Parent = parent
		return p
	end
	-- a box you walk into to be taken somewhere (LaserDoors reads Hub.Doors by name)
	function B.trigger(name, x0, x1, y0, y1, z0, z1, attrs)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Transparency = 1; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Size = V3(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0))
		p.CFrame = B.cf((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		for k, v in attrs or {} do p:SetAttribute(k, v) end
		p:SetAttribute("Built", "TrainingV2")
		p.Parent = B.doors
		return p
	end
	-- a jump pad (Move throws you off any part with a Pad attribute: its launch velocity, world studs/s)
	function B.pad(x, y, z, vel)
		B.put("bc_jumppad", CF(x, y, z), { name = "JumpPad", scale = 0.8, color = { ff4fd8 = P.pier2, ffe14d = P.cyan, d6dbe3 = P.pier } })
		local top = B.part("Collision", "JumpPadTop", CF(x, y + 0.25, z), V3(5.4, 0.5, 5.4), P.pier, { tr = 1, noShadow = true })
		top:SetAttribute("Pad", vel)
		return top
	end
	-- a grapple disc (look only: the beam or wall behind it is what the rope takes)
	function B.hook(x, y, z, facing)
		local r = if facing == "down" then CFrame.Angles(math.pi / 2, 0, 0) elseif facing == "north" then CFrame.Angles(0, math.pi, 0)
			elseif facing == "east" then CFrame.Angles(0, math.pi / 2, 0) elseif facing == "west" then CFrame.Angles(0, -math.pi / 2, 0) else CFrame.identity
		return B.put("tv_hook", CF(x, y, z) * r, { name = "GrappleDisc" })
	end
	-- a flat painted line on a floor (no collision): from (x0, z0) to (x1, z1), w wide, at height y
	function B.line(x0, z0, x1, z1, y, w, hex, name)
		local len = math.sqrt((x1 - x0) ^ 2 + (z1 - z0) ^ 2)
		local cf = CFrame.lookAt(V3((x0 + x1) / 2, y + 0.02, (z0 + z1) / 2), V3(x1, y + 0.02, z1))
		return B.part("Scenery", name or "FloorLine", cf, V3(w, 0.04, len), hex, { ghost = true })
	end
	-- an arrow on a floor pointing along (dx, dz)
	function B.chevron(x, y, z, dx, dz, size, hex)
		local yaw = math.atan2(-dx, -dz)
		for s = -1, 1, 2 do
			local cf = CF(x, y + 0.03, z) * CFrame.Angles(0, yaw, 0) * CFrame.Angles(0, s * math.rad(40), 0) * CF(0, 0, size * 0.35)
			B.part("Scenery", "Chevron", cf, V3(size * 0.22, 0.04, size * 0.75), hex, { ghost = true })
		end
	end
	return B
end

-- ---------------------------------------------------------------- the muster (arrival)
-- side i of the octagon: bearing i * 45 (0 = north, ahead as you arrive; 90 = east). its frame F: origin the muster's
-- middle at y 0, -Z outward, +X to the right as you look out
local function sideFrame(B, i) return CF(MX, 0, MZ) * CFrame.Angles(0, -math.rad(i * 45), 0) end
local function muster(B)
	local W = 2 * (A + WALL) * TAN8 + 0.2 -- a side's width at the wall's outside (the insides overlap into the neighbours)
	-- floor: one slab under the whole room and its walls
	B.blk("Shell", "MusterFloor", MX - A - WALL, MX + A + WALL, 236, MY, MZ - A, MZ + A + WALL, P.floor)
	-- under the north side (the yard's floor is a step lower): solid to the ground either side of the opening
	for _, sx in { -1, 1 } do B.blk("Shell", "NorthSill", sx * 6, sx * ((A + WALL) * TAN8 + 0.1), 236, MY, MZ - A, MZ - A - WALL, P.wall) end
	-- the eight sides. holes = { w, y0, y1 } over the muster floor
	local HOLES = { [0] = { 12, 0, 12 }, [2] = { 12, 0, 12 }, [6] = { 12, 0, 12 }, [4] = { 10.8, 0, 12 }, [5] = { 12, 0, 12 }, [3] = { 13, 2, 11.5, recess = 2 },
		[1] = { 10.4, 1.5, 14, recess = 3, back = P.warmWall }, [7] = { 10.4, 1.5, 14, recess = 3, back = P.warmWall } }
	for i = 0, 7 do
		local F = sideFrame(B, i)
		local h = HOLES[i]
		local nm = "MusterWall" .. i
		if not h then
			B.fbox(F, "Shell", nm, -W / 2, W / 2, MY, MTOP, A, A + WALL, P.wall)
		else
			local w, y0, y1 = h[1], MY + h[2], MY + h[3]
			B.fbox(F, "Shell", nm, -W / 2, -w / 2, MY, MTOP, A, A + WALL, P.wall)
			B.fbox(F, "Shell", nm, w / 2, W / 2, MY, MTOP, A, A + WALL, P.wall)
			B.fbox(F, "Shell", nm, -w / 2, w / 2, y1, MTOP, A, A + WALL, P.wall)
			if y0 > MY then B.fbox(F, "Shell", nm, -w / 2, w / 2, MY, y0, A, A + WALL, P.wall) end
			if h.recess then B.fbox(F, "Shell", nm .. "Back", -w / 2, w / 2, y0, y1, A + h.recess, A + WALL, h.back or P.deep) end
		end
		-- a base strip and a band at one height all round (broken by the openings)
		local inner = 2 * A * TAN8
		local function segs(cut)
			if cut then return { { -inner / 2, -cut }, { cut, inner / 2 } } end
			return { { -inner / 2, inner / 2 } }
		end
		for _, seg in segs(if h and h[2] == 0 then h[1] / 2 else nil) do
			B.fbox(F, "Shell", "Dado", seg[1], seg[2], MY, MY + 1.2, A - 0.2, A, P.floor2, { ghost = true })
		end
		B.fbox(F, "Shell", "Band", -inner / 2 - 0.15, inner / 2 + 0.15, MY + 14.5, MY + 15.1, A - 0.3, A, P.trim, { ghost = true })
	end
	-- the crown: a cove off the wall tops, a ring, the lantern drum with lit panels, a round light in its cap
	B.put("tv_crown", CF(MX, MY, MZ), { name = "MusterCrown" })
	for i = 0, 7 do
		local F = sideFrame(B, i)
		B.fbox(F, "Scenery", "LanternPanel", -3, 3, MY + 22.5, MY + 29.5, 11.75, 11.95, P.lantern, { ghost = true, mat = NEON })
	end
	B.drum("Scenery", "LanternLight", MX, MZ, MY + 31.7, MY + 31.95, 9, P.lantern, { ghost = true, mat = NEON })
	B.lamp(MX, MY + 30.5, MZ, "spot", 42, 1.6, P.lampWhite, { angle = 110, shadows = true })
	for _, b in { 45, 135, 225, 315 } do
		local r = math.rad(b)
		B.lamp(MX + 8 * math.sin(r), MY + 25, MZ - 8 * math.cos(r), "point", 22, 0.55, P.lampWhite)
	end
	-- the dais in the middle (one step up) and the lines from it to every way out
	B.put("tv_dais", CF(MX, MY, MZ), { name = "Dais", unglow = true, color = { f0a53a = P.amber } })
	B.drum("Collision", "DaisSolid", MX, MZ, MY, MY + 1, 14, P.pier, { tr = 1, noShadow = true })
	B.drum("Scenery", "FloorRing", MX, MZ, MY, MY + 0.012, 21, P.line, { ghost = true })
	B.drum("Scenery", "FloorRingIn", MX, MZ, MY, MY + 0.02, 19.4, P.floor2, { ghost = true })
	B.line(MX, MZ - 7.2, MX, MZ - A, MY, 1.1, P.line)
	B.line(MX + 7.2, MZ, MX + A, MZ, MY, 1.1, P.line)
	B.line(MX - 7.2, MZ, MX - A, MZ, MY, 1.1, P.line)
	B.line(MX, MZ + 7.2, MX, MZ + A, MY, 1.1, P.line)
	-- the three framed ways out, one heavy word on each head
	for _, s in { { 0, "DUMMIES" }, { 2, "RANGE" }, { 6, "COURSE" } } do
		local F = sideFrame(B, s[1])
		B.put("tv_frameMid", F * CF(0, MY, -(A + WALL / 2)), { name = "Frame" .. s[2] })
		B.text("Word" .. s[2], { { s[2], P.amber, "B", 1 } }, 9.2, 1.7, F * CF(0, MY + 13.2, -(A - 0.42)) * CFrame.Angles(0, math.pi, 0), { plate = P.pier, thick = 0.2 })
	end
	-- the gate back to the hub (south): the hub's own gate on this side too
	local G = sideFrame(B, 4)
	B.put("hb_portal", G * CF(0, MY, -(A + 1.2)), { name = "HubGate", scale = 0.6, color = { ff4fd8 = P.amber, ["2e3140"] = P.dark, a4aab8 = P.pier } })
	-- this side of the gate is calm (the hub's side keeps its red bars): a slate shutter of slats, one amber light bar
	-- across its head. walk into it and you are back in the hub
	B.fbox(G, "Shell", "GateVoid", -5.4, 5.4, MY, MY + 12, A + 3.4, A + WALL, "33363d")
	B.fbox(G, "Scenery", "ShutterBack", -4.2, 4.2, MY, MY + 9.96, A + 2.6, A + 2.9, "3a3e46", { ghost = true })
	for k = 0, 8 do
		local y = MY + 0.2 + k * 1.08
		B.fbox(G, "Scenery", "ShutterSlat", -4.2, 4.2, y, y + 0.95, A + 1.5, A + 1.9, P.pier2, { ghost = true })
	end
	B.fbox(G, "Scenery", "GateLightBar", -4.0, 4.0, MY + 9.95, MY + 10.35, A + 1.4, A + 1.7, P.amberGlow, { ghost = true, mat = NEON })
	B.lamp(0, MY + 8, MZ + A - 1.5, "point", 10, 0.5, "ffc27a")
	B.text("WordHUB", { { "HUB", P.amber, "B", 1 } }, 7.6, 1.6, G * CF(0, MY + 13.4, -(A - 0.32)) * CFrame.Angles(0, math.pi, 0), { plate = P.dark, thick = 0.25 })
	B.trigger("ToHub", MX - 4.2, MX + 4.2, MY, MY + 10, MZ + A + 0.6, MZ + A + 3.6)
	-- the bench bay (south-west): the place to stop. low, warm, a bench, lockers, water
	local S = sideFrame(B, 5)
	-- (a step down into it, the same thick frame as the other doors, a low curved ceiling, one built-in bench)
	B.fbox(S, "Shell", "BayFloor", -8, 8, 236, MY - 1, A + WALL, A + WALL + 7.5, P.floor2)
	B.part("Shell", "BayStepNose", S * CF(0, MY - 0.5, -(A + WALL + 0.05)), V3(12, 0.9, 0.9), P.trim, { cyl = true })
	B.fbox(S, "Shell", "BayWall", -8, -6.2, MY - 1, MY + 13.5, A + WALL - 0.5, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayWall", 6.2, 8, MY - 1, MY + 13.5, A + WALL - 0.5, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayBack", -8, 8, MY - 1, MY + 13.5, A + WALL + 6, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayCeiling", -8, 8, MY + 12.6, MY + 13.5, A + 0.5, A + WALL + 7.5, P.ceil)
	B.put("tv_frameMid", S * CF(0, MY, -(A + WALL / 2)), { name = "FrameBay" })
	for _, d in { 1.9, 5.6 } do B.put("tv_vault", S * CF(0, MY + 9.4, -(A + WALL + d)), { name = "BayVault", scale = 0.26 }) end
	B.fbox(S, "Shell", "BuiltInBench", -6, 6, MY - 1, MY + 0.8, A + WALL + 4.2, A + WALL + 6, P.tan)
	B.fbox(S, "Shell", "BenchBack", -6, 6, MY + 0.8, MY + 3.4, A + WALL + 5.6, A + WALL + 6, P.tan)
	for _, sx in { -2.5, 2.5 } do
		local q = S:PointToWorldSpace(V3(sx, MY + 6.5, -(A + WALL + 4.5)))
		B.lamp(q.X, q.Y, q.Z, "point", 14, 0.8, P.warm)
	end
	for _, sx in { -2.5, 2.5 } do
		B.put("bc_sconce", S * CF(sx, MY + 5.6, -(A + WALL + 5.5)), { name = "Sconce" })
	end
	-- the board in the south-east recess: where everything is
	local E = sideFrame(B, 3)
	B.text("TrainingBoard", {
		{ "TRAINING", P.amber, "B", 1.25 },
		{ "DUMMIES  ·  AHEAD", P.pale, "B", 0.62 },
		{ "RANGE  ·  RIGHT", P.pale, "B", 0.62 },
		{ "COURSE  ·  LEFT", P.pale, "B", 0.62 },
		{ "the dummies hit back in here.", P.grey, "S", 0.42 },
	}, 11.6, 8, E * CF(0, MY + 6.1, -(A + 1.8)) * CFrame.Angles(0, math.pi, 0), { plate = P.board, thick = 0.25 })
	B.put("tv_lightbar", E * CF(0, MY + 11.45, -(A + 1)), { name = "BoardLight" })
	-- the two diagonal sides by the yard: a bay set back 2 with a warm lamp in it, tall lit panels on the piers either side
	for _, i in { 1, 7 } do
		local F = sideFrame(B, i)
		for _, sx in { -6.75, 6.75 } do
			B.fbox(F, "Scenery", "PanelHousing", sx - 1, sx + 1, MY + 2, MY + 13.2, A - 0.5, A, P.dark)
			B.fbox(F, "Scenery", "PanelLight", sx - 0.45, sx + 0.45, MY + 2.6, MY + 12.6, A - 0.62, A - 0.48, P.panel, { ghost = true, mat = NEON })
		end
		-- a seat along the back, the next room's name over it, one big warm lamp over the name
		B.fbox(F, "Shell", "SeatLedge", -5.2, 5.2, MY, MY + 1.8, A + 1.2, A + 3, P.trim)
		B.put("tv_target", F * CF(0, MY + 7.4, -(A + 2.75)), { name = "BayTarget", scale = 0.42 })
		B.fbox(F, "Scenery", "BayLampHousing", -3.6, 3.6, MY + 11.2, MY + 12.4, A + 1.0, A + 3, P.dark)
		B.fbox(F, "Scenery", "BayLamp", -3.1, 3.1, MY + 11.05, MY + 11.2, A + 1.3, A + 2.7, P.warm, { ghost = true, mat = NEON })
		local q = F:PointToWorldSpace(V3(0, MY + 10.4, -(A + 1.6)))
		B.lamp(q.X, q.Y, q.Z, "point", 18, 0.85, P.warm)
	end
	-- the passages: north into the yard (down a step), east into the range (up a step), west into the course (down)
	B.ramp("Shell", "RampN", "z", MZ - A, MY, MZ - A - WALL, Y0, MX - 6, MX + 6, P.floor)
	B.ramp("Shell", "RampE", "x", MX + A + WALL, MY, 30, 242, MZ - 9, MZ + 9, P.floor)
	B.blk("Shell", "RampEFill", MX + A + WALL, 30, 236, MY - 0.5, MZ - 9, MZ + 9, P.floor)
	B.ramp("Shell", "RampW", "x", MX - A - WALL, MY, -30, Y0, MZ - 9, MZ + 9, P.floor)
	B.blk("Shell", "RampWFill", -30, MX - A - WALL, 236, Y0 - 0.5, MZ - 9, MZ + 9, P.floor)
	for _, sgn in { 1, -1 } do
		local x0, x1 = MX + sgn * (A + WALL), sgn * 30
		for _, sz in { -1, 1 } do
			-- a wall whose inside face runs from the frame (6 off the axis) to the room (8.5 off)
			local a, b = V3(x0, 0, MZ + sz * 6), V3(x1, 0, MZ + sz * 8.5)
			local d = (b - a).Unit
			local n = V3(0, 0, sz)
			n = (n - d * n:Dot(d)).Unit
			local mid = (a + b) / 2 + n * 2
			B.part("Shell", "PassageWall", CFrame.lookAt(V3(mid.X, 246.5, mid.Z), V3(mid.X, 246.5, mid.Z) + d), V3(4, 21, (b - a).Magnitude + 0.6), P.wall)
		end
		B.blk("Shell", "PassageCeiling", x0, x1, MY + 12, 257, MZ - 10, MZ + 10, P.ceil)
		B.blk("Scenery", "PassageLight", (x0 + x1) / 2 - 2, (x0 + x1) / 2 + 2, MY + 11.75, MY + 11.95, MZ - 1.5, MZ + 1.5, P.panel, { ghost = true, mat = NEON })
		B.lamp((x0 + x1) / 2, MY + 11, MZ, "point", 14, 0.6, P.lampWhite)
	end
	-- spawn points: you arrive facing the yard
	local sp = folderIn(B.mk, "TrainSpawns")
	for _, s in T.SPAWNS do B.marker(sp, "TrainSpawn", s[1], MY + 0.7, s[2], V3(MX, MY, MZ - A - 4)) end
end

-- ---------------------------------------------------------------- the dummy yard
-- a vaulted hall: walks either side at the yard's floor, the middle lane a step down (the strafing dummy's), cover in
-- the side bays a third and two thirds of the way down and low walls in the lane, the Plinker on a two-step round stand
-- in front of a heavy shutter at the end (where the dummies come out): the thing the yard ends on
local YX, YZ0, YZ1 = 24, -8146, -8258
local LANE = { x = 13, z0 = -8158, z1 = -8218, y = 239 }
local STAGE = { z = -8228, y = 242 } -- the far third: a stage for the Plinker, a step up from the walks (z -8226..-8228)
local PIERS = { -8162, -8178, -8194, -8210, -8226, -8242 }
local function yard(B)
	-- floors: the walks and both ends at the yard's floor, the lane a step down with a half-step at each end
	B.blk("Shell", "YardFloor", -YX - 4, -LANE.x, 236, Y0, YZ0 + 0.1, STAGE.z + 2, P.floor)
	B.blk("Shell", "YardFloor", LANE.x, YX + 4, 236, Y0, YZ0 + 0.1, STAGE.z + 2, P.floor)
	B.blk("Shell", "YardFloor", -LANE.x, LANE.x, 236, Y0, YZ0 + 0.1, LANE.z0, P.floor)
	B.blk("Shell", "YardFloor", -LANE.x, LANE.x, 236, Y0, LANE.z1, STAGE.z + 2, P.floor)
	B.blk("Shell", "StageStep", -YX - 4, YX + 4, 236, Y0 + 1, STAGE.z + 2, STAGE.z, P.floor2)
	B.blk("Shell", "Stage", -YX - 4, YX + 4, 236, STAGE.y, STAGE.z, YZ1 - 4, P.floor)
	B.part("Shell", "StageNose", CF(0, STAGE.y - 0.45, STAGE.z + 0.05), V3(2 * YX - 3.4, 0.9, 0.9), P.trim, { cyl = true })
	B.part("Shell", "StepNose", CF(0, Y0 + 0.55, STAGE.z + 2.05), V3(2 * YX - 3.4, 0.9, 0.9), P.trim, { cyl = true })
	B.blk("Shell", "Lane", -LANE.x, LANE.x, 236, LANE.y, LANE.z0, LANE.z1, P.floor2)
	B.blk("Shell", "LaneStep", -LANE.x, LANE.x, 236, LANE.y + 0.5, LANE.z0, LANE.z0 - 1.6, P.floor2)
	B.blk("Shell", "LaneStep", -LANE.x, LANE.x, 236, LANE.y + 0.5, LANE.z1 + 1.6, LANE.z1, P.floor2)
	for _, sx in { -1, 1 } do
		B.blk("Shell", "Kerb", sx * LANE.x, sx * (LANE.x + 0.7), Y0 - 0.05, Y0 + 0.2, LANE.z0, LANE.z1, P.trim)
		B.blk("Shell", "KerbFace", sx * (LANE.x - 0.02), sx * (LANE.x - 0.1), LANE.y, Y0 - 0.05, LANE.z0, LANE.z1, P.slate, { ghost = true })
	end
	B.blk("Shell", "YardWallW", -YX - 4, -YX, 236, 258.6, YZ0, YZ1, P.wall)
	B.blk("Shell", "YardWallE", YX, YX + 4, 236, 258.6, YZ0, YZ1, P.wall)
	-- the end wall: the garage door's opening on the axis (push 10; the door, its frame and panel: TrainingLot)
	B.blk("Shell", "YardEnd", -YX - 4, -12, 236, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardEnd", 12, YX + 4, 236, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardEnd", -12, 12, 258.5, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardFront", -YX - 4, -9.9, 236, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardFront", 9.9, YX + 4, 236, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardFront", -9.9, 9.9, MTOP, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardRoof", -YX - 4, YX + 4, 270.5, 272, YZ0 + 4, YZ1 - 4, P.wall, { nq = true })
	for _, e in { { -YX - 4.4, -YX - 2.4, YZ0 + 4.4, YZ1 - 4.4 }, { YX + 2.4, YX + 4.4, YZ0 + 4.4, YZ1 - 4.4 } } do
		B.blk("Shell", "RoofCoping", e[1], e[2], 271, 273, e[3], e[4], P.wall2, { nq = true })
	end
	-- base strip and band along both long walls and the end
	for _, sx in { -1, 1 } do
		B.blk("Shell", "Dado", sx * YX, sx * (YX - 0.2), Y0, Y0 + 1.2, YZ0, YZ1, P.floor2, { ghost = true })
		B.blk("Shell", "Band", sx * YX, sx * (YX - 0.3), Y0 + 8, Y0 + 8.6, YZ0, YZ1, P.trim, { ghost = true })
	end
	B.blk("Shell", "Dado", -YX, -15.2, STAGE.y, STAGE.y + 1.2, YZ1, YZ1 + 0.2, P.floor2, { ghost = true })
	B.blk("Shell", "Dado", 15.2, YX, STAGE.y, STAGE.y + 1.2, YZ1, YZ1 + 0.2, P.floor2, { ghost = true })
	-- piers with a capital under every rib, a lamp on each
	for _, z in PIERS do
		for _, sx in { -1, 1 } do
			B.blk("Shell", "Pier", sx * YX, sx * (YX - 1.6), Y0, 257.4, z - 1.5, z + 1.5, P.pier)
			B.blk("Shell", "PierBase", sx * YX, sx * (YX - 1.85), Y0, Y0 + 1.3, z - 1.75, z + 1.75, P.deep)
			B.blk("Shell", "PierCap", sx * YX, sx * (YX - 2.3), 257.4, 258.4, z - 1.9, z + 1.9, P.trim)
			B.blk("Scenery", "SconceHousing", sx * (YX - 1.6), sx * (YX - 2.2), 249.5, 252.5, z - 0.9, z + 0.9, P.dark)
			B.blk("Scenery", "SconceLight", sx * (YX - 2.15), sx * (YX - 2.3), 249.9, 252.1, z - 0.55, z + 0.55, P.warm, { ghost = true, mat = NEON })
			B.lamp(sx * (YX - 3), 251, z, "point", 13, 0.4, P.warm)
		end
	end
	-- the vault: seven bays and a rib at every pier (and against both end walls)
	for k = 0, 6 do B.put("tv_vault", CF(0, 258, YZ0 - 8 - 16 * k), { name = "Vault" }) end
	for _, z in PIERS do B.put("tv_rib", CF(0, 258, z), { name = "Rib" }) end
	B.put("tv_rib", CF(0, 258, YZ0 - 1.2), { name = "Rib" })
	B.put("tv_rib", CF(0, 258, YZ1 + 1.2), { name = "Rib" })
	B.put("tv_rib", CF(0, 258, STAGE.z - 0.8), { name = "Rib" })
	for _, sx in { -1, 1 } do
		B.blk("Shell", "Pier", sx * YX, sx * (YX - 2.2), Y0, 257.4, STAGE.z + 3.5, STAGE.z - 2.4, P.pier)
		B.blk("Shell", "PierCap", sx * YX, sx * (YX - 2.8), 257.4, 258.4, STAGE.z + 3.8, STAGE.z - 2.7, P.trim)
	end
	for k = 0, 6 do
		local z = YZ0 - 8 - 16 * k
		if k ~= 6 then B.put("tv_lightbar", CF(0, 267.95, z) * CFrame.Angles(0, math.pi / 2, 0), { name = "VaultLight" }) end
		B.lamp(0, 266.4, z, "spot", 34, 1.1, P.lampWhite, { angle = 115, shadows = (k == 1 or k == 4) })
	end
	-- the floor: a pale line at every pier, rings where the still dummies stand, the strafing dummy's track
	for _, z in PIERS do
		if z > STAGE.z + 2 then
			for _, sx in { -1, 1 } do B.line(sx * (LANE.x + 0.7), z, sx * (YX - 1.6), z, Y0 + 0.01, 0.7, P.line, "PierLine") end
		end
		if z < LANE.z0 and z > LANE.z1 then B.line(-LANE.x, z, LANE.x, z, LANE.y + 0.01, 0.7, P.line, "PierLine") end
	end
	for _, n in { "Stand1", "Stand2" } do
		local d = T.DUMMIES[n]
		B.drum("Scenery", "StandRing", d[1], d[3], d[2], d[2] + 0.05, 4, P.trim, { ghost = true })
		B.drum("Scenery", "StandRingIn", d[1], d[3], d[2], d[2] + 0.06, 2.9, P.floor2, { ghost = true })
	end
	local dm = T.DUMMIES.Dummy
	B.line(dm[1] - 12, dm[3], dm[1] + 12, dm[3], dm[2] + 0.02, 0.9, P.line, "DummyTrack")
	for _, sx in { -12, 12 } do B.line(dm[1] + sx, dm[3] - 1.6, dm[1] + sx, dm[3] + 1.6, dm[2] + 0.03, 0.9, P.line, "DummyTrackEnd") end
	-- the Plinker's round stand on the stage, and the target on the end wall behind it (the thing the yard ends on)
	local pk = T.DUMMIES.Plinker
	B.put("tv_pulpit", CF(pk[1], STAGE.y, pk[3]), { name = "PlinkerStand" })
	B.drum("Collision", "PlinkerStandSolid", pk[1], pk[3], STAGE.y, STAGE.y + 2, 12.4, P.pier, { tr = 1, noShadow = true })
	B.drum("Shell", "PlinkerTop", pk[1], pk[3], STAGE.y + 1.9, pk[2] - 0.3, 8, P.pier2)
	B.drum("Shell", "PlinkerTopLip", pk[1], pk[3], pk[2] - 0.35, pk[2], 8.5, P.trim)
	-- a round light in the vault's crown over the stage (on the axis: the stand is off it since push 12); two spots on
	-- the garage door behind it
	B.drum("Scenery", "StageLightStem", 0, pk[3], 266.8, 268.2, 2, P.dark)
	B.drum("Scenery", "StageLightRim", 0, pk[3], 266.3, 266.9, 10.4, P.trim)
	B.drum("Scenery", "StageLight", 0, pk[3], 266.1, 266.35, 9, P.panel, { ghost = true, mat = NEON })
	-- (push 12: the Plinker's stand off the axis, to the left of the door, so it stops blocking the doorway and the view; the spots dimmer and lower,
	-- they blew the shutter's top out white)
	B.lamp(-8, 263, YZ1 + 10, "spot", 28, 0.55, P.lampWhite, { look = V3(0, 246, YZ1), angle = 70 })
	B.lamp(8, 263, YZ1 + 10, "spot", 28, 0.55, P.lampWhite, { look = V3(0, 246, YZ1), angle = 70 })
	-- cover in the side bays, alternating: a head-high wall on one side and a chest-high wall on the other, then the
	-- other way round; two low walls in the lane before the stage; the middle kept open
	for _, c in { { -1, -8186, "high" }, { 1, -8186, "low" }, { -1, -8202, "low" }, { 1, -8202, "high" } } do
		local x, z = c[1] * 19.2, c[2]
		if c[3] == "high" then
			for _, dz in { -2.5, 2.5 } do B.put("tv_block", CF(x, Y0, z + dz), { name = "Block" }) end
			B.solid("BlockBox", CF(x, Y0 + 3.8, z), V3(5, 7.6, 10))
		else
			B.put("tv_cover", CF(x, Y0, z) * CFrame.Angles(0, math.pi / 2, 0), { name = "Cover" })
			B.solid("CoverBox", CF(x, Y0 + 2.35, z), V3(2.4, 4.7, 10))
		end
	end

	-- the dummies' spots
	local ds = folderIn(B.mk, "DummySpots")
	for n, d in T.DUMMIES do B.marker(ds, n, d[1], d[2], d[3], V3(d[1], d[2], d[3] + 10)) end
end

-- ---------------------------------------------------------------- the firing range (Cardboard Carl's)
-- booths under a coffered canopy, then the lane open to the sky between thick portal frames, stepping up in two
-- kerbed terraces; the Carls stand on three low plinths; the lane ends on a backstop bank and a rack of steel plates
local RX0, RX1, RZ0, RZ1 = 30, 78, -8102, -8300
local DECK, DECK_Z = 242, -8148
local T1Z, T2Z = -8205, -8250
local RTOP, RTOP_W = 270, 280 -- the walls' tops (the west one higher: the yard and the course stand behind it)
local PIERS_R = { -8150, -8170, -8190, -8210, -8230, -8250, -8270 }
local BEAMS = { -8150, -8170, -8190, -8210, -8230 } -- (none over the far end: the target stays in sight under them)
local BEAM_Y = 263 -- the portal beams' undersides
local ROWS = { { -8183, Y0 }, { -8228, 244 }, { -8273, 248 } } -- each row of Carls: its z and the floor its plinth stands on
local PASS = 8.5 -- half the width of the passage from the muster where it meets the room (it widens from 6)
local function range(B)
	-- floors: the deck, the lane, two terraces
	B.blk("Shell", "Deck", RX0, RX1, 236, DECK, RZ0, DECK_Z, P.floor)
	B.blk("Shell", "Lane", RX0, RX1, 236, Y0, DECK_Z, T1Z, P.floor)
	B.blk("Shell", "Terrace1", RX0, RX1, 236, 244, T1Z, T2Z, P.floor)
	B.blk("Shell", "Terrace2", RX0, RX1, 236, 248, T2Z, RZ1, P.floor)
	B.blk("Shell", "EdgeFace", RX0, RX1, Y0, DECK - 0.6, DECK_Z - 0.05, DECK_Z - 0.15, P.slate, { ghost = true })
	B.blk("Shell", "EdgeCap", RX0, RX1, DECK - 0.6, DECK + 0.05, DECK_Z + 0.3, DECK_Z - 0.35, P.trim)
	-- each terrace: a darker face and a thick rounded nose along its edge (open at the side steps)
	for _, e in { { T1Z, Y0, 244 }, { T2Z, 244, 248 } } do
		B.blk("Shell", "EdgeFace", RX0, RX1, e[2], e[3], e[1] + 0.05, e[1] + 0.15, P.slate, { ghost = true })
		B.part("Shell", "TerraceNose", CF((RX0 + RX1) / 2, e[3], e[1] + 0.1), V3(RX1 - RX0 - 10, 1.6, 1.6), P.trim, { cyl = true })
		B.blk("Scenery", "TerraceLight", RX0 + 5, RX1 - 5, e[3] - 1.35, e[3] - 1.05, e[1] + 0.16, e[1] + 0.24, P.litEdge, { ghost = true, mat = NEON })
	end
	-- steps at the sides: deck to lane, lane to the first terrace, to the second
	for _, x in { { RX0, RX0 + 5 }, { RX1 - 5, RX1 } } do
		B.blk("Shell", "Step", x[1], x[2], 236, 241, DECK_Z, DECK_Z - 3, P.floor2)
		B.blk("Shell", "Step", x[1], x[2], 236, 242, T1Z + 4, T1Z, P.floor2)
		B.blk("Shell", "Step", x[1], x[2], 236, 246, T2Z + 4, T2Z, P.floor2)
	end
	-- the rows: a low plinth along each row of Carls, so the rows are there between runs too
	for _, r in ROWS do
		B.blk("Shell", "RowPlinth", RX0 + 3.5, RX1 - 3.5, r[2], r[2] + 1.2, r[1] + 1.8, r[1] - 1.8, P.pier2)
		B.part("Shell", "RowNose", CF((RX0 + RX1) / 2, r[2] + 0.6, r[1] + 1.8), V3(RX1 - RX0 - 7, 1.2, 1.2), P.pier2, { cyl = true })
		B.blk("Shell", "RowPlinthEdge", RX0 + 3.5, RX1 - 3.5, r[2] + 1.2, r[2] + 1.25, r[1] + 1.8, r[1] + 1.3, P.trim, { ghost = true })
	end
	-- walls (the west one with the passage from the muster) up to RTOP, a 45-degree cut along the top inside edge
	B.blk("Shell", "RangeWallW", RX0 - 4, RX0, 236, RTOP_W, RZ0 + 4, MZ + PASS, P.wall)
	B.blk("Shell", "RangeWallW", RX0 - 4, RX0, 236, RTOP_W, MZ - PASS, RZ1 - 4, P.wall)
	B.blk("Shell", "RangeWallW", RX0 - 4, RX0, MY + 12, RTOP_W, MZ + PASS, MZ - PASS, P.wall)
	B.blk("Shell", "RangeWallE", RX1, RX1 + 4, 236, RTOP, RZ0 + 4, RZ1 - 4, P.wall)
	B.blk("Shell", "RangeBack", RX0 - 4, RX1 + 4, 236, RTOP, RZ0 + 4, RZ0, P.wall)
	B.blk("Shell", "RangeEnd", RX0 - 4, RX1 + 4, 236, RTOP, RZ1, RZ1 - 4, P.wall)
	for _, sx in { RX0, RX1 } do
		B.part("Shell", "WallCut", CF(sx, if sx == RX0 then RTOP_W else RTOP, (RZ0 + RZ1) / 2) * CFrame.Angles(0, 0, math.rad(45)), V3(2.83, 2.83, math.abs(RZ1 - RZ0)), P.wall2)
	end

	B.part("Shell", "WallCut", CF((RX0 + RX1) / 2, RTOP, RZ1) * CFrame.Angles(math.rad(45), 0, 0), V3(RX1 - RX0, 2.83, 2.83), P.wall2)
	B.part("Shell", "WallCut", CF((RX0 + RX1) / 2, RTOP, RZ0) * CFrame.Angles(math.rad(45), 0, 0), V3(RX1 - RX0, 2.83, 2.83), P.wall2)
	-- a base strip on each level and a band along both sides
	for _, sx in { RX0, RX1 } do
		local s = if sx == RX0 then 1 else -1
		B.blk("Shell", "Band", sx, sx + s * 0.3, 254, 254.7, DECK_Z, RZ1, P.trim, { ghost = true })
		for _, seg in { { DECK_Z, T1Z, Y0 }, { T1Z, T2Z, 244 }, { T2Z, RZ1, 248 } } do
			B.blk("Shell", "Dado", sx, sx + s * 0.2, seg[3], seg[3] + 1.2, seg[1], seg[2], P.floor2, { ghost = true })
		end
	end
	-- thick full-height piers each side (bays between them); deep beams across the near part, open sky over the far end
	for _, z in PIERS_R do
		local fy = if z > DECK_Z then DECK elseif z > T1Z then Y0 elseif z > T2Z then 244 else 248
		for _, sx in { RX0, RX1 } do
			local s = if sx == RX0 then 1 else -1
			local top = if sx == RX0 then RTOP_W else RTOP
			B.blk("Shell", "Pier", sx, sx + s * 2.6, 236, top - 2, z - 2, z + 2, P.pier)
			B.blk("Shell", "PierBase", sx, sx + s * 2.85, 236, fy + 1.3, z - 2.25, z + 2.25, P.deep)
			B.blk("Shell", "PierCap", sx, sx + s * 3.0, top - 2.8, top - 2, z - 2.4, z + 2.4, P.trim)
		end
	end
	for _, z in BEAMS do
		B.blk("Shell", "Beam", RX0 + 2.6, RX1 - 2.6, BEAM_Y, BEAM_Y + 3.6, z - 1.2, z + 1.2, P.pier)
		B.blk("Shell", "BeamSoffit", RX0 + 2.6, RX1 - 2.6, BEAM_Y - 0.2, BEAM_Y + 0.05, z - 0.8, z + 0.8, P.pier2, { ghost = true })
	end

	-- the canopy over the deck: a coffered ceiling with lit panels, a deep fascia at its front
	local CY = 258.5 -- (the canopy's underside, 16.5 over the deck)
	B.blk("Shell", "Canopy", RX0, RX1, CY, CY + 1.5, RZ0, DECK_Z - 1, P.ceil)
	B.blk("Shell", "CanopyRoof", RX0, RX1, CY + 1.5, CY + 1.8, RZ0, DECK_Z - 1, P.slate)
	for _, z in { -8114, -8126, -8138 } do B.blk("Shell", "CanopyBeam", RX0, RX1, CY - 1.4, CY, z - 0.7, z + 0.7, P.pier) end
	for _, x in { 46, 62 } do B.blk("Shell", "CanopyBeam", x - 0.7, x + 0.7, CY - 1.4, CY, RZ0, DECK_Z, P.pier) end
	B.blk("Shell", "Fascia", RX0, RX1, CY - 2.6, CY + 2, DECK_Z + 1, DECK_Z - 1.2, P.pier)
	B.blk("Shell", "FasciaEdge", RX0, RX1, CY - 2.6, CY - 2.2, DECK_Z + 1.1, DECK_Z - 1.3, P.trim)
	for _, x in { 38, 54, 70 } do
		for _, z in { -8108, -8120, -8132, -8143 } do
			B.blk("Scenery", "CanopyPanel", x - 3, x + 3, CY - 0.25, CY - 0.05, z - 2.6, z + 2.6, "a7acb3", { ghost = true, mat = NEON })
		end
		B.lamp(x, CY - 0.7, -8137, "spot", 26, 1.0, P.lampWhite, { angle = 120, shadows = x == 54 })
		B.lamp(x, CY - 0.7, -8110, "spot", 24, 0.7, P.warm, { angle = 120 })
	end
	-- kit at the back of the deck: cases and an ammo crate (what the place is for)
	for _, c in { { 34.5, -8105.5, 0 }, { 73.5, -8105.5, 180 } } do
		B.put("bc_hardcase", CF(c[1], DECK, c[2]) * CFrame.Angles(0, math.rad(c[3]), 0), { name = "HardCase", color = { ["2f3b2a"] = P.pier2 } })
		B.solid("CaseBox", CF(c[1], DECK + 1, c[2]), V3(4, 2, 3))
		B.put("bc_ammocrate", CF(c[1], DECK + 1.9, c[2]), { name = "AmmoCrate", color = { ["4a5a2c"] = "6c7466", ["3a4622"] = "5c6358" } })
	end
	-- the firing line: a counter (its box is the hub builders' RangeCounterBox), booths, three plates
	B.blk("Scenery", "Counter", 36, 72, DECK, 244.8, DECK_Z + 2.4, DECK_Z + 0.2, P.pier, { nc = true })
	B.blk("Scenery", "CounterTop", 35.7, 72.3, 244.8, 245.4, DECK_Z + 2.7, DECK_Z - 0.1, P.trim, { nc = true })
	local cb = B.boxSrc
	cb.Size = V3(36, 3.4, 2.4); cb.CFrame = B.cf(54, DECK + 1.7, DECK_Z + 1.2)
	for _, x in { 47, 61 } do
		B.put("tv_booth", CF(x, DECK, -8141), { name = "Booth" })
		B.solid("BoothBox", CF(x, DECK + 2.5, -8141), V3(1.2, 5, 5))
	end
	for _, pl in T.PLATES do
		local x, z = pl[2], T.PLATE_Z
		B.blk("Scenery", "PlateRim", x - 4.5, x + 4.5, DECK, DECK + 0.06, z - 3.5, z + 3.5, P.deep, { ghost = true })
		local p = B.part("Range", pl[1], CF(x, DECK + 0.1, z) * CFrame.Angles(0, -math.pi / 2, 0), V3(6, 0.16, 8), P[pl[4]], { ghost = true })
		p.Parent = B.root.Range.Plates
		local g = Instance.new("SurfaceGui")
		g.Name = "Gui"; g.Face = Enum.NormalId.Top; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 24
		g.LightInfluence = 0.4
		local t = Instance.new("TextLabel")
		t.Name = "Name"; t.BackgroundTransparency = 1; t.TextScaled = true; t.Text = pl[3]; t.TextColor3 = Color3.fromHex("2c2f36")
		t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
		t.Size = UDim2.new(0.86, 0, 0.5, 0); t.Position = UDim2.new(0.07, 0, 0.25, 0)
		t.Parent = g
		g.Parent = p
		B.text("Booth" .. pl[3], { { pl[3], P[pl[4]], "B", 1 } }, 6.4, 1.5, CF(x, DECK + 1.5, DECK_Z + 2.55) * CFrame.Angles(0, math.pi, 0), { plate = P.board, thick = 0.2 })
	end
	-- the board, on the west wall in the first bay, facing the booths (the lane's middle stays clear to the target)
	local board = Instance.new("Part")
	board.Name = "Board"; board.Anchored = true; board.CanCollide = false; board.CanQuery = false; board.CanTouch = false
	board.Size = V3(13.5, 7, 0.4); board.Color = Color3.fromHex(P.board); board.Material = SP; board.CastShadow = false
	board.CFrame = B.cf(RX0 + 3.35, 255.8, -8160) * CFrame.Angles(0, -math.pi / 2, 0)
	board.Parent = B.root.Range
	-- (on two arms off the wall, clear of the piers either side, so it reads square from the booths)
	B.blk("Scenery", "BoardFrame", RX0 + 2.85, RX0 + 3.15, 252.0, 259.6, -8152.95, -8167.05, P.dark, { ghost = true })
	for _, z in { -8155, -8165 } do
		for _, y in { 253, 258.6 } do B.blk("Shell", "BoardArm", RX0, RX0 + 2.9, y - 0.3, y + 0.3, z - 0.3, z + 0.3, P.pier) end
	end
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 32
	g.LightInfluence = 0
	local function lbl(name, text, x, y, w, h, hex, weight)
		local t = Instance.new("TextLabel")
		t.Name = name; t.BackgroundTransparency = 1; t.TextScaled = true; t.Text = text; t.TextColor3 = Color3.fromHex(hex)
		t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", weight)
		t.Position = UDim2.new(x, 0, y, 0); t.Size = UDim2.new(w, 0, h, 0)
		t.Parent = g
	end
	lbl("ScoreT", "CARLS DOWN", 0.06, 0.07, 0.38, 0.12, P.grey, Enum.FontWeight.Bold)
	lbl("LeftT", "CARLS LEFT", 0.56, 0.07, 0.38, 0.12, P.grey, Enum.FontWeight.Bold)
	lbl("Score", "00", 0.06, 0.2, 0.38, 0.5, P.pale, Enum.FontWeight.Heavy)
	lbl("Left", "25", 0.56, 0.2, 0.38, 0.5, P.amber, Enum.FontWeight.Heavy)
	lbl("Line", "CARDBOARD CARL'S · stand on a plate. he won't shoot back.", 0.06, 0.72, 0.88, 0.25, P.pale, Enum.FontWeight.SemiBold)
	g.Line.TextWrapped = true
	g.Parent = board
	-- the Carls' spots (each looks at the plates) on the row plinths, a foot-mark at each, the distance at each row
	for _, s in T.SPOTS do
		B.marker(B.root.Range.Spots, "Spot", s[1], s[2] + 0.1, s[3], V3(54, s[2], T.PLATE_Z))
		B.drum("Scenery", "CarlMark", s[1], s[3], s[2], s[2] + 0.05, 3.2, P.line, { ghost = true })
	end
	for _, row in { { -8183, "15 M" }, { -8221, "30 M" }, { -8280, "45 M" } } do
		B.text("Distance", { { row[2], P.pale, "B", 1 } }, 5, 2.2, CF(RX0 + 0.2, 252, row[1]) * CFrame.Angles(0, -math.pi / 2, 0), { plate = P.board, thick = 0.2 })
		B.text("Distance", { { row[2], P.pale, "B", 1 } }, 5, 2.2, CF(RX1 - 0.2, 252, row[1]) * CFrame.Angles(0, math.pi / 2, 0), { plate = P.board, thick = 0.2 })
	end
	-- lines down the lane from each booth
	for _, pl in T.PLATES do B.line(pl[2], DECK_Z - 0.4, pl[2], -8180.8, Y0, 0.6, P.line, "LaneLine") end
	-- the end: a slate backstop bank with a rounded top, and the big target centred on the backstop wall over it
	-- (rework 4: one thick slate backstop the full width, its top edge cut, the big target in a round recess on it, and
	-- a hood over the end, so the lane ends under cover)
	local BZ = -8288
	B.blk("Shell", "Backstop", RX0, RX1, 236, 274, BZ, RZ1, P.pier2)
	B.part("Shell", "BackstopCut", CF((RX0 + RX1) / 2, 274, BZ) * CFrame.Angles(math.rad(45), 0, 0), V3(RX1 - RX0, 2.83, 2.83), P.pier2)
	B.part("Scenery", "TargetRim", CF(54, 261, BZ + 0.05) * CFrame.Angles(0, math.pi / 2, 0), V3(0.1, 26.6, 26.6), P.litEdge, { cyl = true, ghost = true, mat = NEON })
	B.part("Shell", "TargetRecess", CF(54, 261, BZ + 0.15) * CFrame.Angles(0, math.pi / 2, 0), V3(0.3, 25, 25), P.recess, { cyl = true })
	B.put("tv_target", CF(54, 261, BZ + 1.0), { name = "EndTarget", scale = 1.4 })
	B.blk("Shell", "Hood", RX0, RX1, 275.5, 277, -8279, RZ1, P.pier2)
	B.blk("Shell", "HoodFascia", RX0, RX1, 274.2, 277.4, -8279, -8280.6, P.pier)
	B.lamp(42, 274.6, -8282, "spot", 40, 1.0, P.lampWhite, { look = V3(54, 261, BZ), angle = 55 })
	B.lamp(66, 274.6, -8282, "spot", 40, 1.0, P.lampWhite, { look = V3(54, 261, BZ), angle = 55 })
end

-- ---------------------------------------------------------------- the movement course
-- the tallest room: ledges up the west wall with jump pads, a gallery along the north wall, an eight-sided tower under
-- a skylight drum with an open chute back down to the start, a pit to slide-jump on the slide lane, grapple rings
-- hanging from the ceiling beams, the playground's secret bullseye high on the north wall
local CX0, CX1, CZ0, CZ1, CTOP = -86, -30, -8102, -8230, 288
local PIT = { x0 = -40, x1 = -30, z0 = -8186, z1 = -8208 }
local LEDGES = { -- { name, x0, x1, z0, z1, top }
	{ "Ledge1", -86, -74, -8102, -8150, 250 },
	{ "Ledge2", -86, -74, -8154, -8198, 260 },
	{ "Ledge3", -86, -74, -8202, -8230, 270 },
	{ "Gallery", -74, -42, -8218, -8230, 270 },
}
local TOWER = { x = -58, z = -8170, top = 268 }
local SKY = { x0 = -72, x1 = -44, z0 = -8150, z1 = -8182, top = 306 } -- the skylight drum, on the beam lines round the tower
local function course(B)
	-- floor round the pit, the pit (4 down) with a step out on its west side
	B.blk("Shell", "CourseFloor", CX0 - 4, PIT.x0, 234, Y0, CZ0 + 4, CZ1 - 4, P.courseFloor)
	B.blk("Shell", "CourseFloor", PIT.x0, CX1, 234, Y0, CZ0 + 4, PIT.z0, P.courseFloor)
	B.blk("Shell", "CourseFloor", PIT.x0, CX1, 234, Y0, PIT.z1, CZ1 - 4, P.courseFloor)
	B.blk("Shell", "PitFloor", PIT.x0, CX1, 232, 236, PIT.z0, PIT.z1, P.floor2)
	B.blk("Shell", "PitStep", PIT.x0, PIT.x0 + 3, 236, 238, PIT.z0, PIT.z1, P.floor2)
	B.blk("Shell", "PitFace", PIT.x0, CX1, 236, Y0, PIT.z0 - 0.02, PIT.z0 - 0.12, P.slate, { ghost = true })
	B.blk("Shell", "PitFace", PIT.x0, CX1, 236, Y0, PIT.z1 + 0.02, PIT.z1 + 0.12, P.slate, { ghost = true })
	B.blk("Shell", "PitFace", PIT.x0 + 0.02, PIT.x0 + 0.12, 238, Y0, PIT.z0, PIT.z1, P.slate, { ghost = true })
	-- the slide lane down the east side to the pit: a darker strip, arrows, an amber edge to jump from
	B.blk("Scenery", "SlideLane", PIT.x0, CX1, Y0, Y0 + 0.03, -8106, PIT.z0, P.floor2, { ghost = true })
	for z = -8116, -8176, -15 do B.chevron(-35, Y0, z, 0, -1, 7, P.line) end
	B.blk("Scenery", "JumpEdge", PIT.x0, CX1, Y0, Y0 + 0.05, PIT.z0, PIT.z0 + 0.9, P.amber, { ghost = true })
	B.blk("Scenery", "LandEdge", PIT.x0, CX1, Y0, Y0 + 0.05, PIT.z1, PIT.z1 - 0.9, P.line, { ghost = true })
	B.text("SlideWord", { { "SLIDE", P.line, "B", 1 } }, 8, 2.6, CF(-35, Y0 + 0.05, -8108) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
	-- walls (the east one with the passage from the muster)
	B.blk("Shell", "CourseWallE", CX1, CX1 + 4, 234, CTOP + 4, CZ0 + 4, MZ + PASS, P.courseWall)
	B.blk("Shell", "CourseWallE", CX1, CX1 + 4, 234, CTOP + 4, MZ - PASS, CZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallE", CX1, CX1 + 4, MY + 12, CTOP + 4, MZ + PASS, MZ - PASS, P.courseWall)
	B.blk("Shell", "CourseWallW", CX0 - 4, CX0, 234, CTOP + 4, CZ0 + 4, CZ1 - 4, P.courseWall)
	-- (rework 5: the south wall, the end of the view from the gallery, opens into a deep lit bay on the tower's axis,
	-- framed in the ledges' rounded white noses)
	local SB = { x0 = TOWER.x - 13, x1 = TOWER.x + 13, y0 = 246, y1 = 282, back = CZ0 + 8 }
	B.blk("Shell", "CourseWallS", CX0 - 4, SB.x0, 234, CTOP + 4, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "CourseWallS", SB.x1, CX1 + 4, 234, CTOP + 4, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "CourseWallS", SB.x0, SB.x1, 234, SB.y0, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "CourseWallS", SB.x0, SB.x1, SB.y1, CTOP + 4, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "StartBaySill", SB.x0, SB.x1, 234, SB.y0, SB.back, CZ0 + 4, P.ledge)
	B.blk("Shell", "StartBayBack", SB.x0 - 2, SB.x1 + 2, 234, SB.y1 + 2, SB.back + 1, SB.back, P.ledge)
	B.blk("Shell", "StartBayCheek", SB.x0 - 2, SB.x0, SB.y0, SB.y1 + 2, SB.back, CZ0 + 4, P.courseWall)
	B.blk("Shell", "StartBayCheek", SB.x1, SB.x1 + 2, SB.y0, SB.y1 + 2, SB.back, CZ0 + 4, P.courseWall)
	B.blk("Shell", "StartBayHead", SB.x0, SB.x1, SB.y1, SB.y1 + 2, SB.back, CZ0 + 4, P.ceil)
	B.blk("Shell", "StartBayPanel", SB.x0 + 3, SB.x1 - 3, SB.y0 + 3, SB.y1 - 5, SB.back - 0.05, SB.back - 0.35, P.ledgePanel)
	B.blk("Scenery", "StartBayLight", SB.x0 + 1, SB.x1 - 1, SB.y1 - 0.25, SB.y1, SB.back - 0.2, CZ0 + 3.6, P.litEdge, { ghost = true, mat = NEON })
	B.lamp(TOWER.x, SB.y1 - 3, CZ0 + 5, "point", 22, 0.8, P.lampWhite)
	for _, x in { SB.x0, SB.x1 } do
		B.part("Shell", "StartBayNose", CF(x, (SB.y0 + SB.y1) / 2, CZ0 - 0.1) * CFrame.Angles(0, 0, math.pi / 2), V3(SB.y1 - SB.y0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	end
	for _, y in { SB.y0, SB.y1 } do
		B.part("Shell", "StartBayNose", CF(TOWER.x, y, CZ0 - 0.1), V3(SB.x1 - SB.x0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	end
	B.blk("Shell", "CourseWallN", CX0 - 4, CX1 + 4, 234, CTOP + 4, CZ1, CZ1 - 4, P.courseWall)
	for _, w in { { CX1, CX1 - 0.2, CZ0, MZ + PASS }, { CX1, CX1 - 0.2, MZ - PASS, CZ1 } } do
		B.blk("Shell", "Dado", w[1], w[2], Y0, Y0 + 1.2, w[3], w[4], P.floor2, { ghost = true })
	end
	-- piers on the beam grid down the east wall (the ceiling's beams land on them), bands at the ledges' heights
	for _, z in { -8134, -8150, -8166, -8182, -8198, -8214 } do
		local y0 = if z < PIT.z0 + 2 and z > PIT.z1 - 2 then 236 else Y0
		B.blk("Shell", "Pier", CX1, CX1 - 2.4, y0, CTOP, z - 1.6, z + 1.6, P.pier)
		B.blk("Shell", "PierBase", CX1, CX1 - 2.65, y0, y0 + 1.3, z - 1.85, z + 1.85, P.deep)
	end
	-- (rework 5: the beams land on the west wall too: piers from a corbel above head height on ledge 3, so the high
	-- wall over the ledges has the same rhythm as the east one)
	for k = 1, 7 do
		local z = CZ0 - 16 * k
		B.blk("Shell", "PierW", CX0, CX0 + 2.4, 279, CTOP, z - 1.6, z + 1.6, P.pier)
		B.blk("Shell", "PierWCorbel", CX0, CX0 + 2.8, 277.6, 279, z - 2, z + 2, P.pier2)
	end
	-- the coffered ceiling: beams both ways, lit panels in every other coffer, and over the tower a skylight drum open
	-- to the sky (the beams across it stay, as its bars)
	local cy0, cy1 = CTOP + 4, CTOP + 6
	B.blk("Shell", "CourseCeiling", CX0 - 4, CX1 + 4, cy0, cy1, CZ0 + 4, SKY.z0 - 1.2, P.ceil)
	B.blk("Shell", "CourseCoping", CX1 + 2.6, CX1 + 4.6, cy0 - 1, cy1 + 1.2, CZ0 + 4.4, CZ1 - 4.4, P.wall2, { nq = true })
	B.blk("Shell", "CourseBand", CX1 + 4, CX1 + 4.3, 276, 277, CZ0 + 4, CZ1 - 4, P.trim, { ghost = true })
	B.blk("Shell", "CourseCeiling", CX0 - 4, CX1 + 4, cy0, cy1, SKY.z1 + 1.2, CZ1 - 4, P.ceil)
	B.blk("Shell", "CourseCeiling", CX0 - 4, SKY.x0 + 1.2, cy0, cy1, SKY.z0 - 1.2, SKY.z1 + 1.2, P.ceil)
	B.blk("Shell", "CourseCeiling", SKY.x1 - 1.2, CX1 + 4, cy0, cy1, SKY.z0 - 1.2, SKY.z1 + 1.2, P.ceil)
	local zb = {}
	for k = 1, 7 do table.insert(zb, CZ0 - 16 * k) end
	for _, z in zb do B.blk("Shell", "CeilingBeam", CX0, CX1, CTOP, CTOP + 4, z - 1.2, z + 1.2, P.pier) end
	for _, x in { -44, -58, -72 } do B.blk("Shell", "CeilingBeam", x - 1.2, x + 1.2, CTOP, CTOP + 4, CZ0, CZ1, P.pier) end
	for _, w in {
		{ SKY.x0 - 1.2, SKY.x0 + 1.2, SKY.z0 + 1.2, SKY.z1 - 1.2 }, { SKY.x1 - 1.2, SKY.x1 + 1.2, SKY.z0 + 1.2, SKY.z1 - 1.2 },
		{ SKY.x0 - 1.2, SKY.x1 + 1.2, SKY.z0 + 1.2, SKY.z0 - 1.2 }, { SKY.x0 - 1.2, SKY.x1 + 1.2, SKY.z1 + 1.2, SKY.z1 - 1.2 },
	} do
		B.blk("Shell", "SkyDrum", w[1], w[2], CTOP, SKY.top, w[3], w[4], P.wall2)
	end
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0 + 1.6, SKY.z0 - 1.6, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z1 + 1.6, SKY.z1 - 1.6, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x0 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0, SKY.z1, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x1 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0, SKY.z1, P.wall2)
	local xs = { -79, -65, -51, -37 }
	for row = 0, 7 do
		local z = CZ0 - 8 - 16 * row
		for col, x in xs do
			local inSky = x > SKY.x0 and x < SKY.x1 and z < SKY.z0 and z > SKY.z1
			if (row + col) % 2 == 0 and not inSky then
				B.blk("Scenery", "CoffersPanel", x - 4, x + 4, CTOP + 3.75, CTOP + 3.95, z - 4, z + 4, P.panel, { ghost = true, mat = NEON })
				if row % 2 == 0 then B.lamp(x, CTOP + 3.2, z, "spot", 62, 1.1, P.lampWhite, { angle = 120, shadows = (row == 6 and col == 2) }) end
			end
		end
	end
	-- the ledges up the west wall and the gallery along the north wall: a slab with a pale fascia and a pale lip at the
	-- edge, thick columns under the front
	-- (rework 3: solid masses stepping up, off-white against the darker walls, a rounded nose along each edge you jump
	-- from, a sunk panel on each face with the ledge's number on it)
	for _, L in LEDGES do
		local name, x0, x1, z0, z1, top = table.unpack(L)
		-- (rework 4: slate masses with a rounded white nose and a lit strip under it, on a darker floor)
		B.blk("Shell", name, x0, x1, Y0, top, z0, z1, P.ledge)
		if name == "Gallery" then
			B.part("Shell", "Nose", CF((x0 + x1) / 2, top - 0.1, z0 + 0.1), V3(x1 - x0, 1.4, 1.4), P.trim, { cyl = true })
			B.blk("Scenery", "EdgeLight", x0, x1, top - 1.3, top - 1.0, z0 + 0.05, z0 + 0.2, P.litEdge, { ghost = true, mat = NEON })
			B.blk("Shell", "FacePanel", x0 + 3, x1 - 3, Y0 + 3, top - 4, z0 + 0.05, z0 + 0.35, P.ledgePanel)
		else
			local mid = (z0 + z1) / 2
			B.part("Shell", "Nose", CF(x1 - 0.1, top - 0.1, mid) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(z1 - z0), 1.4, 1.4), P.trim, { cyl = true })
			B.blk("Scenery", "EdgeLight", x1 + 0.05, x1 + 0.2, top - 1.3, top - 1.0, z0, z1, P.litEdge, { ghost = true, mat = NEON })
			B.blk("Shell", "FacePanel", x1 + 0.05, x1 + 0.35, Y0 + 3, top - 4, z0 - 3, z1 + 3, P.ledgePanel)
			local n = string.sub(name, -1)
			B.text("LedgeNo", { { n, P.amber, "B", 1 } }, 3.4, 3.8, CF(x1 + 0.5, top - 3.6, mid) * CFrame.Angles(0, -math.pi / 2, 0), { plate = P.board, thick = 0.2 })
		end
	end
	-- jump pads: floor to ledge 1, ledge 1 to 2, 2 to 3, floor to the tower's top
	B.pad(-66, Y0, -8136, V3(-14, 52, 0)) -- (between the chute's piers, where the line from the door leads)
	B.pad(-80, 250, -8143, V3(0, 52, -14))
	B.pad(-80, 260, -8191, V3(0, 52, -14))
	B.pad(-44, Y0, TOWER.z, V3(-12, 80, 0))
	-- the tower (eight-sided, under the skylight), and the open chute from its top back down to the start
	B.put("tv_towerOct", CF(TOWER.x, Y0, TOWER.z), { name = "Tower" })
	B.drum("Collision", "TowerSolid", TOWER.x, TOWER.z, Y0, TOWER.top, 16.6, P.pier, { tr = 1, noShadow = true })
	local cz0, cz1 = TOWER.z + 8, -8110 -- (the chute runs from the tower's south face to the floor near the start)
	local clen = cz1 - cz0
	local ch = TOWER.top - Y0
	B.ramp("Shell", "Chute", "z", cz0, TOWER.top, cz1, Y0, TOWER.x - 4, TOWER.x + 4, P.ledge, { thick = 2 })
	local slope = math.atan2(ch, clen)
	-- (rework 3: two thick piers under it, not stilts; a head block where it meets the tower)
	for _, z in { -8126, -8146 } do
		local top = Y0 + (z - cz1) / (cz0 - cz1) * ch - 2 / math.cos(slope) + 0.2
		B.blk("Shell", "ChutePier", TOWER.x - 3.5, TOWER.x + 3.5, Y0, top, z - 2, z + 2, P.pier)
		B.blk("Shell", "ChutePierBase", TOWER.x - 3.8, TOWER.x + 3.8, Y0, Y0 + 1.3, z - 2.3, z + 2.3, P.deep)
	end
	B.blk("Shell", "ChuteHead", TOWER.x - 4, TOWER.x + 4, TOWER.top - 3, TOWER.top, cz0 + 1.6, cz0 - 0.6, P.ledge)
	local L = math.sqrt(clen * clen + ch * ch)
	for _, sx in { -4.4, 4.4 } do
		-- (a curb along each side, stopping short of the tower's deck)
		local cf = CF(TOWER.x + sx, Y0 + ch / 2 + 1.2, (cz0 + cz1) / 2) * CFrame.Angles(slope, 0, 0) * CF(0, 0, 1)
		B.part("Shell", "ChuteCurb", cf, V3(1.2, 2.6, L - 2), P.ledge)
		B.part("Scenery", "ChuteRail", cf * CF(0, 1.3, 0) * CFrame.Angles(0, math.pi / 2, 0), V3(L - 2, 1.4, 1.4), P.trim, { cyl = true, ghost = true })
	end
	-- grapple rings hanging from the ceiling beams: over the pit, between the tower and the gallery, over the tower (from
	-- the skylight's bars), over the start
	for _, h in { { -37, -8198 }, { -58, -8198 }, { -58, -8166 }, { -72, -8134 }, { -44, -8134 } } do
		B.put("tv_hoop", CF(h[1], CTOP, h[2]), { name = "GrappleRing" })
	end
	-- the playground's secret: a bullseye high on the north wall over the gallery. too high to jump to: grapple into it
	-- the top: a deep frame on the north wall at the gallery's middle, lit, with its word (the course's far end)
	B.put("tv_frameWide", CF(TOWER.x, 270, CZ1 + 1.8), { name = "FrameTop", scale = 0.75 })
	B.blk("Shell", "TopPanel", TOWER.x - 6, TOWER.x + 6, 270, 280.5, CZ1 + 0.05, CZ1 + 0.3, P.recess)
	B.blk("Scenery", "TopLight", TOWER.x - 5, TOWER.x + 5, 279.6, 279.9, CZ1 + 0.3, CZ1 + 1.6, P.warm, { ghost = true, mat = NEON })
	B.lamp(TOWER.x, 278, CZ1 + 3, "point", 16, 0.7, P.warm)
	B.text("WordTOP", { { "TOP", P.amber, "B", 1 } }, 7, 1.5, CF(TOWER.x, 280.9, CZ1 + 3.85) * CFrame.Angles(0, math.pi, 0), { plate = P.pier, thick = 0.2 })
	-- the way in: a line from the door to the first pad, an arrow at it
	B.line(-31.5, MZ, -61.5, -8135.4, Y0, 0.9, P.line, "RouteLine")
	B.chevron(-60.5, Y0, -8135.2, -1, 0, 5, P.line)
	local bx, by, bz = -80, 283, CZ1 + 0.45 -- (over ledge 3, off the line you see from the entrance)
	B.put("tv_target", CF(bx, by, bz), { name = "SecretBullseye", scale = 0.6 })
	B.trigger("ToPlayground", bx - 3, bx + 3, by - 3, by + 3, CZ1 + 1.2, CZ1 + 4.2)
	local ta = folderIn(B.doors, "TrainingArrive")
	for _, x in { -84, -80, -76 } do
		local p = B.marker(ta, "TrainingArrive", x, 270.1, CZ1 + 6, V3(x, 270, CZ1 + 20))
		p:SetAttribute("Built", "TrainingV2")
	end
end

-- ---------------------------------------------------------------- the zone, the barrier, the finish
local function bounds(B, withLot)
	local z = T.ZONE
	local lz = T.LOT
	local zp = Instance.new("Part")
	zp.Name = "TrainingZone"; zp.Anchored = true; zp.Transparency = 1; zp.CanCollide = false; zp.CanQuery = false; zp.CanTouch = false
	if withLot then -- one box round the hall and the back lot
		zp.Size = V3(lz[2] - lz[1] + 4, lz[3] + 4 - z[3], math.abs(lz[4] - 2 - z[5]))
		zp.CFrame = B.cf((lz[1] + lz[2]) / 2, (z[3] + lz[3] + 4) / 2, (z[5] + lz[4] - 2) / 2)
	else
		zp.Size = V3(z[2] - z[1], z[4] - z[3], math.abs(z[6] - z[5]))
		zp.CFrame = B.cf((z[1] + z[2]) / 2, (z[3] + z[4]) / 2, (z[5] + z[6]) / 2)
	end
	zp.Parent = B.mk
	local bar = folderIn(B.mk, "Barrier")
	local function wall(name, x0, x1, y0, y1, z0, z1)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Transparency = 1; p.CanCollide = true; p.CanQuery = false; p.CanTouch = false
		p.Size = V3(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0))
		p.CFrame = B.cf((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		p.Parent = bar
	end
	if not withLot then
		wall("Lid", z[1] - 2, z[2] + 2, z[4], z[4] + 2, z[5] + 2, z[6] - 2)
		wall("Side", z[1] - 2, z[1], z[3], z[4], z[5], z[6])
		wall("Side", z[2], z[2] + 2, z[3], z[4], z[5], z[6])
		wall("Back", z[1], z[2], z[3], z[4], z[6], z[6] - 2)
		wall("Front", z[1], z[2], z[3], z[4], z[5] + 2, z[5])
		return
	end
	-- the hall's back is the lot's facade (solid; the garage the one way through): its barrier stops at the facade,
	-- and a wall over the facade's top up to the lot's lid closes the gap (nobody grapples out of the range over it)
	local F = T.FACE
	wall("Lid", z[1] - 2, z[2] + 2, z[4], z[4] + 2, z[5] + 2, F)
	wall("Side", z[1] - 2, z[1], z[3], z[4], z[5], F)
	wall("Side", z[2], z[2] + 2, z[3], z[4], z[5], F)
	wall("Front", z[1], z[2], z[3], z[4], z[5] + 2, z[5])
	wall("Back", z[1] - 2, z[2] + 2, 284, lz[3], F, F - 4)
	wall("LotLid", lz[1] - 2, lz[2] + 2, lz[3], lz[3] + 2, F, lz[4] - 2)
	wall("LotSide", lz[1] - 2, lz[1], z[3], lz[3], F, lz[4])
	wall("LotSide", lz[2], lz[2] + 2, z[3], lz[3], F, lz[4])
	wall("LotBack", lz[1] - 2, lz[2] + 2, z[3], lz[3], lz[4], lz[4] - 2)
	wall("LotFront", lz[1], z[1] - 2, z[3], lz[3], F, F - 2)
	wall("LotFront", z[2] + 2, lz[2], z[3], lz[3], F, F - 2)
end

-- what a live build owns in the hub (and v1 had): parked whole, put back whole
local OWNED = { "TrainingGround", "TrainSpawns", "DummySpots", "TrainingZone", "Barrier" }
local OWNED_DOORS = { "ToHub", "ToPlayground", "TrainingArrive", "LotExit" }
local function clearLive()
	for _, n in OWNED do local c = hub:FindFirstChild(n); if c then c:Destroy() end end
	for _, n in OWNED_DOORS do local c = hub.Doors:FindFirstChild(n); if c then c:Destroy() end end
end

-- park v1 (the old hall and its markers) in PolishBackup.TrainingV1, once
function T.park(): string
	local PB = SS.PolishBackup
	if PB:FindFirstChild("TrainingV1") then return "v1 already parked" end
	local tg = hub:FindFirstChild("TrainingGround")
	if not tg then return "nothing to park: no TrainingGround" end
	if tg:GetAttribute("Version") == T.VERSION then return "the live one is v2: nothing to park" end
	local park = Instance.new("Folder"); park.Name = "TrainingV1"
	park:SetAttribute("Note", "the training hall before v2 (16 Nov 2026): TrainingGround and its markers as they were. TrainingV2.switch(\"v1\") puts copies back")
	local d = Instance.new("Folder"); d.Name = "Doors"; d.Parent = park
	for _, n in OWNED do local c = hub:FindFirstChild(n); if c then c:Clone().Parent = park end end
	for _, n in OWNED_DOORS do local c = hub.Doors:FindFirstChild(n); if c then c:Clone().Parent = d end end
	park.Parent = PB
	return ("v1 parked: %d things"):format(#park:GetDescendants())
end

local function setLook(which)
	local look = game.ReplicatedStorage:FindFirstChild("Jankfire") and game.ReplicatedStorage.Jankfire:FindFirstChild("HubLook")
	if look then look:SetAttribute("TrainingLook", which) end
end

function T.build(mode): string
	local live = mode == "live"
	if live then
		local parked = T.park()
		if not SS.PolishBackup:FindFirstChild("TrainingV1") then return "STOPPED: v1 could not be parked (" .. parked .. ")" end
		clearLive()
	else
		local old = workspace.Map:FindFirstChild("TrainingStage"); if old then old:Destroy() end
	end
	local B = new(live)
	muster(B); yard(B); range(B); course(B)
	-- the back lot (push 10): its own builder, with this build's context
	local lotSrc = SS.PolishBackup:FindFirstChild("TrainingLot")
	local lotNote = ""
	if lotSrc then lotNote = "\n" .. require(lotSrc:Clone()).build(B, T) end
	bounds(B, lotSrc ~= nil)
	local root = B.root
	root:SetAttribute("Version", T.VERSION); root:SetAttribute("Push", T.PUSH)
	for _, p in root:GetDescendants() do if p:IsA("BasePart") then p.Anchored = true end end
	local home
	if live then
		home = hub
		setLook("v2")
	else
		home = Instance.new("Folder"); home.Name = "TrainingStage"; home.Parent = workspace.Map
	end
	-- (into the place in pieces: one write of the whole build can stall Studio)
	local kids = root:GetChildren()
	for _, f in kids do f.Parent = nil end
	root.Parent = home
	for _, f in kids do f.Parent = root; task.wait() end
	local parts = 0
	for _, p in root:GetDescendants() do if p:IsA("BasePart") then parts += 1 end end
	local miss = {}
	for k, n in B.missing do table.insert(miss, k .. " x" .. n) end
	return ("training v2 built %s: %d things, %d parts, %d lamps, %d with shadows%s%s"):format(if live then "LIVE" else "as a staging copy at x +" .. T.STAGE.X,
		#root:GetDescendants(), parts, B.lamps, B.shadows, if #miss > 0 then "  MISSING: " .. table.concat(miss, ", ") else "", lotNote)
end

function T.unstage(): string
	local s = workspace.Map:FindFirstChild("TrainingStage")
	if s then s:Destroy(); return "staging copy removed" end
	return "no staging copy"
end

function T.switch(which): string
	if which == "v2" then return T.build("live") end
	if which ~= "v1" then return "switch(\"v1\") or switch(\"v2\")" end
	local park = SS.PolishBackup:FindFirstChild("TrainingV1")
	if not park then return "STOPPED: no PolishBackup.TrainingV1 (v1 was never parked: it is still live)" end
	clearLive()
	for _, c in park:GetChildren() do
		if c.Name == "Doors" then
			for _, d in c:GetChildren() do d:Clone().Parent = hub.Doors end
		else
			c:Clone().Parent = hub
		end
		task.wait()
	end
	setLook("v1")
	return "v1 is live again (the old hall and its markers, copied from PolishBackup.TrainingV1)"
end

-- ---------------------------------------------------------------- checks
-- live (or the staging copy with stage = true): the markers, the zone, sight lines that matter
function T.check(stage): string
	local out, bad = {}, 0
	local O = if stage then T.STAGE else Vector3.zero
	local base = if stage then workspace.Map:FindFirstChild("TrainingStage") else hub
	local tg = base and base:FindFirstChild("TrainingGround")
	if not tg then return "no TrainingGround" end
	local mk = if stage then tg:FindFirstChild("Game") else hub
	local doors = if stage then mk:FindFirstChild("Doors") else hub.Doors
	local function need(cond, what) if not cond then bad += 1; table.insert(out, "MISSING " .. what) end end
	local sp = mk:FindFirstChild("TrainSpawns"); need(sp and #sp:GetChildren() >= 4, "TrainSpawns")
	local ds = mk:FindFirstChild("DummySpots")
	for n in T.DUMMIES do need(ds and ds:FindFirstChild(n), "DummySpots." .. n) end
	local zone = mk:FindFirstChild("TrainingZone"); need(zone, "TrainingZone")
	need(mk:FindFirstChild("Barrier"), "Barrier")
	for _, n in OWNED_DOORS do if n ~= "LotExit" or tg:FindFirstChild("Lot") then need(doors:FindFirstChild(n), "Doors." .. n) end end
	local r = tg:FindFirstChild("Range")
	need(r and r:FindFirstChild("Plates") and #r.Plates:GetChildren() == 3, "Range.Plates (3)")
	need(r and r:FindFirstChild("Spots") and #r.Spots:GetChildren() >= 10, "Range.Spots")
	local gui = r and r:FindFirstChild("Board") and r.Board:FindFirstChild("Gui")
	for _, n in { "Score", "Left", "Line" } do need(gui and gui:FindFirstChild(n), "Board.Gui." .. n) end
	need(tg:FindFirstChild("PropCollision") and tg.PropCollision:FindFirstChild("RangeCounterBox"), "PropCollision.RangeCounterBox")
	if bad > 0 then return table.concat(out, "\n") end
	-- every marker inside the zone
	local function inZone(p) local rel = zone.CFrame:PointToObjectSpace(p); local h = zone.Size / 2; return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z end
	local outside = 0
	for _, f in { sp, ds, r.Plates, r.Spots, doors.TrainingArrive } do for _, c in f:GetChildren() do if c:IsA("BasePart") and not inZone(c.Position) then outside += 1; table.insert(out, "outside the zone: " .. c:GetFullName()) end end end
	-- sight lines against the solid build (CanQuery parts, like the game's own rays)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { tg }
	local function clear(a, b)
		local hit = workspace:Raycast(a, b - a, rp)
		return hit == nil, hit
	end
	local pk = ds.Plinker.Position + V3(0, 4.8, 0)
	local seen = 0
	for _, s in sp:GetChildren() do
		local ok = clear(pk, s.Position + V3(0, 3.5, 0))
		if ok then seen += 1 end
	end
	table.insert(out, ("spawn points the Plinker can see: %d of %d"):format(seen, #sp:GetChildren()))
	local blocked = 0
	for _, pl in r.Plates:GetChildren() do
		local eye = pl.Position + V3(0, 4.9, 0)
		for _, s in r.Spots:GetChildren() do
			local okC = clear(eye, s.Position + V3(0, 3.6, 0))
			local okH = clear(eye, s.Position + V3(0, 6.2, 0))
			if not okC and not okH then blocked += 1; table.insert(out, ("Carl hidden from %s at (%.0f, %.0f, %.0f)"):format(pl.Name, s.Position.X - O.X, s.Position.Y, s.Position.Z)) end
		end
	end
	table.insert(out, ("plate-to-Carl sight lines blocked: %d of %d"):format(blocked, #r.Plates:GetChildren() * #r.Spots:GetChildren()))
	local gunOk = clear(V3(-16, 245, -8150) + O, ds.Stand1.Position + V3(0, 4, 0))
	table.insert(out, "gun sessions' test line (-16, 245, -8150) to Stand1: " .. (if gunOk then "clear" else "BLOCKED"))
	-- nothing solid where you appear
	local op = OverlapParams.new(); op.FilterType = Enum.RaycastFilterType.Include; op.FilterDescendantsInstances = { tg }; op.RespectCanCollide = true
	local stuck = 0
	for _, f in { sp, doors.TrainingArrive } do
		for _, s in f:GetChildren() do
			local hits = workspace:GetPartBoundsInBox(CF(s.Position + V3(0, 3.2, 0)), V3(2.5, 5, 2.5), op)
			if #hits > 0 then stuck += 1; table.insert(out, "something solid at " .. s:GetFullName() .. ": " .. hits[1].Name) end
		end
	end
	table.insert(out, ("arrival points with something solid in them: %d"):format(stuck))
	table.insert(out, ("markers outside the zone: %d"):format(outside))
	local lotSrc = SS.PolishBackup:FindFirstChild("TrainingLot")
	if lotSrc and tg:FindFirstChild("Lot") then
		for _, l in require(lotSrc:Clone()).check(tg, mk) do table.insert(out, l) end
	end
	return table.concat(out, "\n")
end

return T
