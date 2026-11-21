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
-- push 19 (18 Nov, a friend found the hub cramped; the owner: "perhaps in the training hub too the dummies and course
-- section"): the yard has a side hall through an arcade in its west wall (aisle), and the course is an L twice the floor
-- (course): its entry strip from the same passage, its main hall north to the lot's facade. the range, the mirror and
-- the muster are as they were.
-- a build wipes and remakes: change the builder, never the built parts. coordinates are the world's (the old hall's
-- site); a staging copy is the same build moved T.STAGE along x.
local T = {}
local SS = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local hub = workspace.Map.Hub
local SP, NEON = Enum.Material.SmoothPlastic, Enum.Material.Neon
local V3, CF = Vector3.new, CFrame.new

T.KIT = 125980153806984 -- the kit's Model asset (tv_kit_8: training_models.py; 16 Nov: cover, block, booth and bench remodelled, flicker fixes in the kit)
T.STAGE = V3(400, 0, 0)
T.PUSH = 24
T.VERSION = "v2"
-- the dummies room and the course (18 Nov, the owner: "instead of an extension can you do a complete remodel ... these two
-- rooms can be redone entirely"): "v3" = PolishBackup.TrainingRooms (roblox/studio-tools/TrainingRooms.luau) builds them
-- new, "v2" = this module's own yard (with its side hall) and course (with its strip), one switch away
-- (20 Nov 2026, the owner: "redo training hub entirely"): "v4" = PolishBackup.TrainingRedo (roblox/studio-tools/
-- TrainingRedo.luau) wraps the v3 rooms: both halls open to the sky, the tutorial wing west of the course hall
T.ROOMS = "v5" -- (20 Nov 2026, judged ring-or-better: the compound. "v4" = TrainingRedo, live from place version 1209 to this switch, one switch away; "v3" = the rooms live from place version 917 to the redo; "v2" brings back the old yard and course)

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
-- Cardboard Carl's: { x, floor y, z } feet of each Carl, three rows at 15, 30 and 45 m from the plates. since 16 Nov
-- (the owner: "keep in mind there will be multiple people in these hubs") the lane is three lanes, one per plate, each
-- with its own run: three spots per row in each (a spot's lane is the plate nearest it: attribute Lane)
T.SPOTS = {}
for _, row in { { 241.2, -8183 }, { 245.2, -8228 }, { 249.2, -8273 } } do
	for _, lx in { 40, 54, 68 } do
		for _, dx in { -4.5, 0, 4.5 } do table.insert(T.SPOTS, { lx + dx, row[1], row[2] }) end
	end
end
T.PLATES = { { "Easy", 40, "CHILL", "chill" }, { "Medium", 54, "NORMAL", "normal" }, { "Hard", 68, "SWEATY", "sweaty" } }
T.PLATE_Z = -8138
-- spawn points: two arcs either side of the dais, out of the line the Plinker sees through the yard's opening
T.SPAWNS = { { -12.5, -8111.5 }, { -15.5, -8117.5 }, { -11.5, -8132 }, { 12.5, -8111.5 }, { 15.5, -8117.5 }, { 11.5, -8132 } }
-- (16 Nov, the owner: "maybe have dummies marked every so many meters, and an area where you can activate dummies that
-- shoot back": two standing dummies on the 10 m line, the moving one on the 20 m line, and the two that shoot back at
-- the far corners of the live-fire end, past the 30 m line)
-- (18 Nov, more room: the standing two 18 apart, not 14; the side hall's three in a line down its middle, x -43.8: one
-- standing at 10 m, one on a round stand at 20 m, the second strafer at 30 m, where nothing stands in his way)
T.DUMMIES = { Dummy = { 0, 239, -8206 }, Plinker = { -17, 245.2, -8240 }, Plinker2 = { 17, 245.2, -8240 }, Stand1 = { -9, 239, -8173.5 }, Stand2 = { 9, 239, -8173.5 },
	Stand3 = { -42.5, 240, -8173.5 }, Stand4 = { -43.8, 240, -8206 }, Dummy2 = { -48, 246, -8236 }, Runner = { -98, 240, -8210 } } -- (the standing ones just before the 10 m line, their rings clear of it)
-- (18 Nov, the practice pass: the owner, "can the training hub be like the overwatch training one to an extent like the
-- indoor part except for the shoot range that can stay as is". the side hall is the practice lane: its three on rails,
-- slow at 10 m, quicker at 20 m, quickest at 30 m up on the deck, set by the lane's consoles (Dummies.luau); the course
-- has a runner on a long rail between its towers, to shoot at while you swing. { span each way, walk speed }; a spot with
-- a Span is a rail. the yard's own strafer keeps its old 12 at 22, with no attributes)
T.RAILS = { Stand3 = { 6, 8 }, Stand4 = { 10, 14 }, Dummy2 = { 7, 20 }, Runner = { 18, 14 } }
T.LANE = { Stand3 = true, Stand4 = true, Dummy2 = true }
T.LIVE = { line = -8223 } -- the live-fire end: everything south of this line (the stage, the door)
T.ZONE = { -140, 86, 220, 312, -8058, -8308 } -- x0, x1, y0, y1, z0, z1 (the hall: its barrier; down to 220 for the basement; west to -140 since the course grew and south to -8058 for the gold dummies' door, 18 Nov)
-- the back lot's way down (17 Nov, the owner: the lot's EXIT door "seemly leads no where, can it be like a basement
-- section?"): the façade's opening (door, x) leads onto a landing at the top of a stairwell cut into the range's
-- backstop (well: range() leaves it out of the backstop and the end wall); the stairs run down east to floor, and the
-- basement (room) lies under the range's far terrace (its underside is 236). TrainingLot builds the stairs, the
-- basement, its things and its way out
T.BASEMENT = { door = { 52, 64 }, well = { x0 = 52, x1 = 78, z0 = -8300, z1 = -8290, top = 252 }, floor = 226.4,
	room = { x0 = 40, x1 = 78, z0 = -8288, z1 = -8262, ceil = 234.9 } }
-- the basement's way out, walked (owner, 17 Nov: "can you make the exit actually connect to an exit because there should
-- be no way for it to just tp you back into the main hub area"): the EXIT door in its west wall opens onto a landing
-- under the far terrace; stairs climb south (flight A, under a thinner piece of the terrace), turn on a landing inside
-- the backstop bank, climb east (flight B) to a corridor at the terrace's height, and a door in the bank's face, west
-- of the big target, lets you out onto the far terrace. that door opens from the corridor only (TrainingDoors.client:
-- the hall can't get down to the lot this way). range() leaves the stair hall out of the far terrace and the bank;
-- TrainingLot builds the stairs, walls, lamps and doors. 24 risers of 0.9 from the basement's floor (226.4) to 248
T.BASEMENT.exit = {
	x0 = 30.5, east = 51,          -- the stair hall's inside, west to east (the bank: x 30..52)
	land = { x1 = 38, z0 = -8281, z1 = -8273 }, -- the landing behind the EXIT door
	fA = { x1 = 36, n = 12 },      -- flight A: x0..x1, rising south from land.z0, 12 risers to landA's height
	landA = { x1 = 36.5, z0 = -8299.5, z1 = -8293 },
	fB = { x0 = 36.5, z0 = -8299.5, z1 = -8294, n = 12 }, -- flight B: rising east from x0, 12 risers to 248
	hall = { x0 = 36.5, z0 = -8293.5, z1 = -8289 },        -- the corridor at 248 (and landing B east of flight B's top)
	out = { x0 = 36.8, x1 = 41.0, top = 255.5 },            -- the door in the bank's face (west of the target's rim)
	face = -8288, skin = -8289, back = -8299.5, ceil = 257, thin = { x1 = 37, y = 244 }, top = 248,
}
-- the gold dummies' door (17 Nov, the owner: a dead end "should be the locked door connected to the dummies", opening
-- onto a portal to the playground for whoever has found them): TrainingLot's eggDoor builds it where this says, nil = not
-- built. { cf = the floor in the middle of the opening's face, its -Z the way you walk in (the corridor's end wall
-- TrainingLot.EGG_DEPTH behind it), w, h = the opening, cw, ch = the corridor's width and height, wall = their colour }
T.EGG_DOOR = nil :: { cf: CFrame, w: number?, h: number?, cw: number?, ch: number?, wall: string? }? -- (set with the course since 18 Nov: EGGC)
T.FACE = -8300                                 -- the hall's back since push 10: the inside of the back lot's facade
T.LOT = { -186, 186, 440, -8734 }              -- the back lot: x0, x1, its lid, its far end (the zone takes it in)
-- head room (16 Nov, the hold session: strafing into the yard's console put your eye 0.6 from its top, which then filled
-- a corner of the screen). wherever you can stand in the hall, nothing you can see at head height may come nearer your
-- eye than `near`: `eye` is your eye over the floor, `body` the narrowest your body and head get (the test's stand-in,
-- waist to crown). the props in `guard` get an unseen box `margin` past theirs each way (bodies stop on it, so your head
-- stops short of the prop). walls and posts that run from your waist to over your head are left alone: you walk into
-- those the same in every game
-- (the first run's finds: the console's top; the shop shelf's top, where you could stand with your head in the headsets
-- on the slatwall)
T.HEAD = { eye = 4.5, near = 1.0, body = V3(1.2, 3.2, 1.2), margin = 0.8, guard = { "ConsoleTop", "ShelfTop", "AisleTarget", "PracticeTop" }, bodiesOnly = { PracticeTop = true } } -- (the side hall's target since 18 Nov: a mesh on the end wall you could walk your face into)

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
local function lib() return SS:WaitForChild("JankfireMeshes") end

-- ---------------------------------------------------------------- the kit
-- one asset holds every model: a piece is "<model><n>__<kind>_<hex>"; the exporter turned them so they arrive in the
-- kit's own frame (pivot = the kit origin, the middle of the footprint on the floor; front +Z)
function T.import(kit: number?): string
	local KIT = kit or T.KIT
	local ok, container = pcall(function() return InsertService:LoadAsset(KIT) end)
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
		m:SetAttribute("AssetId", KIT); m:SetAttribute("Kit", "training"); m:SetAttribute("FileFrame", true)
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
	-- (the pad's arrows point along its own -Z, as HubLab found: it is turned so they point the way it throws you)
	function B.pad(x, y, z, vel)
		local yaw = math.atan2(-vel.X, -vel.Z)
		B.put("bc_jumppad", CF(x, y, z) * CFrame.Angles(0, yaw, 0), { name = "JumpPad", scale = 0.8, color = { ff4fd8 = P.pier2, ffe14d = P.cyan, d6dbe3 = P.pier } })
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
	-- (the frames' openings are 12 x 12: the holes 0.05 bigger all round, so the walls' cut faces sit inside the frames)
	local HOLES = { [0] = { 12.1, 0, 12.05 }, [2] = { 12.1, 0, 12.05 }, [6] = { 12.1, 0, 12.05 }, [4] = { 10.8, 0, 12 }, [5] = { 12.1, 0, 12.05 }, [3] = { 13, 2, 11.5, recess = 2 },
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
	-- (16 Nov, the owner: "there is a roof ... that lets you clip through it and get outside". the crown is a mesh
	-- that nothing touches: thick unseen solids just behind its inside faces, side by side all round)
	for i = 0, 7 do
		local F = sideFrame(B, i)
		B.solid("CrownCoveSolid", F * CF(0, MY + 19.06, -19.06) * CFrame.Angles(math.rad(-45), 0, 0), V3(18.6, 3, 7.9))
		B.solid("CrownCoveSolid", F * CF(0, MY + 18.6, -22.7), V3(21.5, 5.2, 4.6))
		B.solid("CrownRingSolid", F * CF(0, MY + 21.5, -14.35), V3(14.5, 3, 4.7))
		B.solid("CrownDrumSolid", F * CF(0, MY + 26.8, -13.9), V3(13.6, 13.6, 3.8))
	end
	B.solid("CrownCapSolid", CF(MX, MY + 34, MZ), V3(30, 4, 30))
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
	B.drum("Scenery", "FloorRing", MX, MZ, MY + 0.03, MY + 0.06, 21, P.line, { ghost = true })
	B.drum("Scenery", "FloorRingIn", MX, MZ, MY + 0.06, MY + 0.1, 19.4, P.floor2, { ghost = true })
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
	-- the gate's kit, the same as on the hub's side (GateKit, the hub session's; owner, 17 Nov: "can the laser fence be on
	-- both side of the hub and same with the garage door because its weird to have the grid on one side and a garage door
	-- on the other"): the same frame and colours, a roll-up garage door with the laser fence just inside it, the dark
	-- plate behind, the amber light bar over the head. walk up and the door rolls up, then the lasers click off (both on
	-- every screen: TrainingDoors.client); walk into it and you are back in the hub
	local GK = require(game.ServerStorage.PolishBackup.GateKit:Clone())
	B.put("hb_portal", G * CF(0, MY, -(A + 1.2)), { name = "HubGate", scale = GK.FRAME.scale, color = GK.FRAME.color })
	B.fbox(G, "Shell", "GateVoid", -5.4, 5.4, MY, MY + 12, A + 3.4, A + WALL, "33363d")
	GK.build(B.at(G * CF(0, MY, -(A + 1.5))), B.root.Scenery, { door = "HubShutter", lasers = "HubLaserGate" })
	B.lamp(0, MY + GK.LAMP.up, MZ + A + 1.5 - GK.LAMP.out, "point", GK.LAMP.range, GK.LAMP.bright, GK.LAMP.hex)
	B.text("WordHUB", { { "HUB", P.amber, "B", 1 } }, 7.6, 1.6, G * CF(0, MY + 13.4, -(A - 0.32)) * CFrame.Angles(0, math.pi, 0), { plate = P.dark, thick = 0.25 })
	B.trigger("ToHub", MX - 4.2, MX + 4.2, MY, MY + 10, MZ + A + 0.6, MZ + A + 3.6)
	-- the bench bay (south-west): the place to stop. low, warm, a bench, lockers, water
	local S = sideFrame(B, 5)
	-- (a step down into it, the same thick frame as the other doors, a low curved ceiling, one built-in bench)
	B.fbox(S, "Shell", "BayFloor", -7.95, 7.95, 236.05, MY - 1, A + WALL, A + WALL + 7.5, P.floor2)
	B.part("Shell", "BayStepNose", S * CF(0, MY - 0.5, -(A + WALL + 0.05)), V3(12, 0.9, 0.9), P.trim, { cyl = true })
	B.fbox(S, "Shell", "BayWall", -8, -6.2, MY - 1, MY + 13.5, A + WALL - 0.5, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayWall", 6.2, 8, MY - 1, MY + 13.5, A + WALL - 0.5, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayBack", -7.95, 7.95, MY - 1, MY + 13.4, A + WALL + 6, A + WALL + 7.5, P.warmWall)
	B.fbox(S, "Shell", "BayCeiling", -7.95, 7.95, MY + 12.6, MY + 13.45, A + 0.5, A + WALL + 7.5, P.ceil)
	B.put("tv_frameMid", S * CF(0, MY, -(A + WALL / 2)), { name = "FrameBay" })
	for _, d in { 1.9, 5.6 } do B.put("tv_vault", S * CF(0, MY + 9.4, -(A + WALL + d)), { name = "BayVault", scale = 0.26 }) end
	-- (16 Nov, the owner, of the bay with a lone gold dummy in it: "it seems random having this opening with a dummy in
	-- it, maybe it can be another room, or it can be a hologram version of your avatar". it is the mirror now: you, as
	-- a hologram in the hub's style, holding your loadout and turning slowly over a lens. TrainingDoors.client draws it
	-- on your screen only; MirrorSpot is where it stands)
	-- (16 Nov, the owner: the podium with your name and numbers, then "I dont like that podium can you do a differnt
	-- design? maybe we dont need the stats or guns laying down". it stands on a plain round projector now: a wide low
	-- drum, a slimmer one on it with one soft glow band, a pale trim ring, the lens on top. no words, no gun)
	local pc = S * CF(0, 0, -(A + WALL + 3.0))
	B.drum("Shell", "MirrorBase", pc.X, pc.Z, MY - 1, MY - 0.25, 5.8, P.pier2)
	B.drum("Shell", "MirrorDrum", pc.X, pc.Z, MY - 0.3, MY + 1.0, 4.8, P.slate)
	B.drum("Scenery", "MirrorGlowBand", pc.X, pc.Z, MY + 0.3, MY + 0.42, 4.86, "8fd8ff", { ghost = true, mat = NEON })
	B.drum("Shell", "MirrorTrim", pc.X, pc.Z, MY + 0.95, MY + 1.12, 5.0, P.trim)
	local lensAt = S * CF(0, MY + 1.12, -(A + WALL + 3.0)) -- (on the projector's top)
	B.part("Scenery", "MirrorLens", lensAt * CFrame.Angles(0, 0, math.pi / 2), V3(0.12, 4.2, 4.2), P.dark, { cyl = true, ghost = true })
	B.part("Scenery", "MirrorLensGlow", lensAt * CF(0, 0.07, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.05, 3.2, 3.2), "8fd8ff", { cyl = true, ghost = true, mat = NEON })
	local ms = B.marker(B.root.Scenery, "MirrorSpot", lensAt.X, lensAt.Y + 0.06, lensAt.Z, S:PointToWorldSpace(V3(0, MY, 0)))
	ms:SetAttribute("Near", 18)
	for _, sx in { -2.5, 2.5 } do
		local q = S:PointToWorldSpace(V3(sx, MY + 6.5, -(A + WALL + 4.5)))
		B.lamp(q.X, q.Y, q.Z, "point", 14, 0.8, P.warm)
	end
	for _, sx in { -5, 5 } do
		B.put("bc_sconce", S * CF(sx, MY + 5.6, -(A + WALL + 5.5)), { name = "Sconce" })
	end
	-- (no MIRROR word over it since 16 Nov: the owner wants no labels for things you can already see)
	B.fbox(S, "Shell", "BayCeilingSolid", -8, 8, MY + 13.5, MY + 16.5, A + 0.5, A + WALL + 7.5, P.ceil, { tr = 1, noShadow = true })
	-- the board in the south-east recess: where everything is
	local E = sideFrame(B, 3)
	B.text("TrainingBoard", {
		{ "TRAINING", P.amber, "B", 1.25 },
		{ "DUMMIES  ·  AHEAD", P.pale, "B", 0.62 },
		{ "RANGE  ·  RIGHT", P.pale, "B", 0.62 },
		{ "COURSE  ·  LEFT", P.pale, "B", 0.62 },
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
		B.blk("Shell", "PassageCeiling", math.min(x0, x1) + 0.05, math.max(x0, x1) - 0.05, MY + 11.9, 257, MZ - 10, MZ + 10, P.ceil) -- (0.1 under the walls' heads, 0.05 under the frames' bands: flicker list)
		B.lamp((x0 + x1) / 2, MY + 11, MZ, "point", 14, 0.6, P.lampWhite)
		-- (18 Nov, the owner, from the course's side: "can you fix the back side of this to make it look presentable": the
		-- passage was bare walls and a flat ceiling. now the house's finish on every face you see from inside: a dark
		-- skirting along the ramp, a framing strip at each end of each wall with a pale panel between, a cornice with its
		-- white nose, a lit coffer in the ceiling, and the room-side opening framed in white noses)
		local fA, fB = MY, if sgn > 0 then 242 else Y0 -- (the floor at the frame and at the room)
		local cy = MY + 11.9 -- (the ceiling's underside)
		for _, sz in { -1, 1 } do
			local a, b = V3(x0, 0, MZ + sz * 6), V3(x1, 0, MZ + sz * 8.5)
			local len = (b - a).Magnitude
			local d = (b - a).Unit
			local n = V3(0, 0, sz)
			n = (n - d * n:Dot(d)).Unit -- (out of the passage, into the wall)
			local function at(t, off, y) return a + d * (t * len) - n * off + V3(0, y, 0) end
			local function fl(t) return fA + (fB - fA) * t end
			local pa, pb = at(0, 0.1, fA + 0.6), at(1, 0.1, fB + 0.6)
			B.part("Shell", "PassageSkirt", CFrame.lookAt((pa + pb) / 2, pb), V3(0.2, 1.2, (pb - pa).Magnitude), P.floor2, { ghost = true })
			for _, t in { 0.7 / len, 1 - 0.7 / len } do
				local f = fl(t)
				local c = at(t, 0.2, (f + cy) / 2)
				B.part("Shell", "PassageStrip", CFrame.lookAt(c, c + d), V3(0.4, cy - f, 1.4), P.pier)
			end
			local p0 = math.max(fA, fB) + 1.9
			local pc = at(0.5, 0.06, (p0 + cy - 1.6) / 2)
			B.part("Shell", "PassagePanel", CFrame.lookAt(pc, pc + d), V3(0.12, cy - 1.6 - p0, len - 3.4), P.mass, { ghost = true })
			local cc = at(0.5, 0.15, cy - 0.3)
			B.part("Shell", "PassageCornice", CFrame.lookAt(cc, cc + d), V3(0.3, 0.6, len), P.trim, { ghost = true })
			local nc = at(0.5, 0.35, cy - 0.7)
			B.part("Shell", "PassageNose", CFrame.lookAt(nc, nc + d) * CFrame.Angles(0, math.pi / 2, 0), V3(len, 0.7, 0.7), P.trim, { cyl = true, ghost = true })
		end
		local mx, lx = (x0 + x1) / 2, math.abs(x1 - x0)
		B.blk("Shell", "PassageCofferRim", mx - lx / 2 + 0.7, mx + lx / 2 - 0.7, cy - 0.18, cy - 0.02, MZ - 6.2, MZ + 6.2, P.trim, { ghost = true })
		B.blk("Scenery", "PassageLight", mx - lx / 2 + 1.3, mx + lx / 2 - 1.3, cy - 0.3, cy - 0.18, MZ - 5.4, MZ + 5.4, P.panel, { ghost = true, mat = NEON })
		local rx = x1 + sgn * 0.1 -- (the room's face of its wall)
		for _, sz in { -1, 1 } do
			B.part("Shell", "PassageJambNose", CF(rx, (fB + MY + 12) / 2, MZ + sz * 8.5) * CFrame.Angles(0, 0, math.pi / 2), V3(MY + 12 - fB + 1.4, 1.4, 1.4), P.trim, { cyl = true })
		end
		B.part("Shell", "PassageHeadNose", CF(rx, MY + 12, MZ) * CFrame.Angles(0, math.pi / 2, 0), V3(17 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
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
-- the side hall (18 Nov: a friend found the hub cramped, and the owner, "perhaps in the training hub too the dummies and
-- course section"): the yard's west wall opens on an arcade into a second lane the yard's length, 28 wide under a flat
-- coffered ceiling, with its own three dummies, cover along its far wall and the big target on its end wall. the vaulted
-- hall itself is as it was. the arcade: the yard's own piers stand free as its columns from the yard's front to the
-- stage's pier; past that (the live-fire end) the wall stays whole. x0 = its west wall's face, x1 = the columns' faces
local AISLE = { x0 = -58, x1 = -29.6, ceil = 262, head = 256, open = STAGE.z + 3.5 }
AISLE.x = (AISLE.x0 + AISLE.x1) / 2
-- the practice lane's deck (18 Nov): the far third raised 6, a slate mass with the ledges' white nose, stairs up its
-- arcade side; the 30 m dummy runs on it. from the lane you shoot up at it; from it you fight down the lane
AISLE.deck = { x1 = -38, z0 = -8226, top = 246, steps = 8 }
-- a rail across a floor (the practice pass): a dark bed under the dummy's track, chunky stops at its ends (none where
-- the floor's own step ends it), its pale middle the distance line drawn there or its own (o.line)
local function rail(B, x, y, z, span, o)
	o = o or {}
	local half = span + 1.4
	B.blk("Scenery", "RailBed", x - half, x + half, y + 0.005, y + 0.025, z - 1.2, z + 1.2, P.deep, { ghost = true })
	if o.line then B.blk("Scenery", "RailLine", x - half, x + half, y + 0.03, y + 0.06, z - 0.25, z + 0.25, P.line, { ghost = true }) end
	if o.stops ~= false then
		for _, sx in { -1, 1 } do
			local ex = x + sx * (half + 0.6)
			B.blk("Shell", "RailStop", ex - 0.6, ex + 0.6, y, y + 0.9, z - 1.3, z + 1.3, P.pier2)
			B.blk("Shell", "RailStopCap", ex - 0.65, ex + 0.65, y + 0.9, y + 1.05, z - 1.35, z + 1.35, P.trim)
		end
	end
end
-- a heal pad (the practice pass): stand on it under full health for +Heal HP; it comes back after Every s (Dummies.luau)
local function healPad(B, x, y, z)
	local m = Instance.new("Model")
	m.Name = "HealPad"
	local parts = {
		B.drum("Shell", "HealPadBase", x, z, y, y + 0.3, 4.6, P.pier2),
		B.drum("Scenery", "HealPadRing", x, z, y + 0.3, y + 0.34, 4.0, P.trim, { ghost = true }),
		B.blk("Scenery", "HealPlus", x - 1.3, x + 1.3, y + 0.34, y + 0.42, z - 0.42, z + 0.42, P.chill, { ghost = true, mat = NEON }),
		B.blk("Scenery", "HealPlus", x - 0.42, x + 0.42, y + 0.34, y + 0.43, z - 1.3, z + 1.3, P.chill, { ghost = true, mat = NEON }),
	}
	for _, q in parts do q.Parent = m end
	m:SetAttribute("Heal", 75); m:SetAttribute("Every", 10); m:SetAttribute("Ready", true)
	m.WorldPivot = B.at(CF(x, y, z))
	m.Parent = B.root.Scenery
	return m
end
local function aisle(B)
	local x0, x1, ax, top = AISLE.x0, AISLE.x1, AISLE.x, AISLE.ceil + 2.5
	local wx = -YX - 4 -- (-28: the yard's wall's outside, now the arcade's back)
	B.blk("Shell", "AisleFloor", x0 - 4, wx, 236, Y0, YZ0, YZ1 - 4, P.floor)
	B.blk("Shell", "AisleWallW", x0 - 4, x0, 236, top, YZ0, YZ1 - 4, P.wall)
	B.blk("Shell", "AisleFront", x0 - 4, wx, 236, top, YZ0, YZ0 - 4, P.wall)
	B.blk("Shell", "AisleEnd", x0 - 4, wx, 236, top, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "AisleCeiling", x0 - 4, wx + 2, AISLE.ceil, top, YZ0, YZ1 - 4, P.ceil) -- (into the yard's wall over the arcade)
	-- the arcade: a column at every pier in the open stretch (the pier's own block and cap stay on the yard's side), a
	-- rounded white nose under the head of every opening on both faces
	local cols = {}
	for _, z in PIERS do if z > AISLE.open then table.insert(cols, z) end end
	for _, z in cols do
		B.blk("Shell", "ArcadeColumn", x1, -YX, Y0, AISLE.head, z - 1.5, z + 1.5, P.pier)
		B.blk("Shell", "ArcadeBase", x1 - 0.25, wx, Y0, Y0 + 1.3, z - 1.75, z + 1.75, P.deep)
	end
	local edges = { YZ0 - 4 }
	for _, z in cols do table.insert(edges, z + 1.5); table.insert(edges, z - 1.5) end
	table.insert(edges, AISLE.open)
	for i = 1, #edges, 2 do
		local za, zb = edges[i], edges[i + 1]
		for _, x in { wx, -YX } do
			B.part("Shell", "ArcadeNose", CF(x, AISLE.head, (za + zb) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(za - zb, 1.4, 1.4), P.trim, { cyl = true })
		end
	end
	-- the far wall's piers on the same lines, beams across the ceiling from them to the arcade, a lit panel in every bay
	for _, z in PIERS do
		B.blk("Shell", "Pier", x0, x0 + 1.6, Y0, AISLE.ceil - 2.6, z - 1.5, z + 1.5, P.pier)
		B.blk("Shell", "PierBase", x0, x0 + 1.85, Y0, Y0 + 1.3, z - 1.75, z + 1.75, P.deep)
		B.blk("Shell", "AisleBeam", x0, wx + 1, AISLE.ceil - 2.6, AISLE.ceil + 0.1, z - 1.15, z + 1.15, P.pier)
		B.blk("Scenery", "SconceHousing", x0 + 1.6, x0 + 2.2, 249.5, 252.5, z - 0.9, z + 0.9, P.dark)
		B.blk("Scenery", "SconceLight", x0 + 2.15, x0 + 2.3, 249.9, 252.1, z - 0.55, z + 0.55, P.warm, { ghost = true, mat = NEON })
	end
	for _, z in { -8178, -8226 } do B.lamp(x0 + 3, 251, z, "point", 13, 0.4, P.warm) end
	local bays = { (YZ0 - 4 + PIERS[1]) / 2 }
	for i = 1, #PIERS - 1 do table.insert(bays, (PIERS[i] + PIERS[i + 1]) / 2) end
	table.insert(bays, (PIERS[#PIERS] + YZ1) / 2)
	for _, z in bays do
		B.blk("Scenery", "AislePanel", ax - 4, ax + 4, AISLE.ceil - 0.2, AISLE.ceil - 0.02, z - 4, z + 4, P.panel, { ghost = true, mat = NEON })
	end
	for i, z in { -8170, -8202, -8234 } do B.lamp(ax, AISLE.ceil - 1, z, "spot", 30, 1.0, P.lampWhite, { angle = 115, shadows = i == 2 }) end
	-- base strip and band on its three walls (the yard's at the same heights)
	B.blk("Shell", "Dado", x0, x0 + 0.2, Y0, Y0 + 1.2, YZ0 - 4, YZ1, P.floor2, { ghost = true })
	B.blk("Shell", "Band", x0, x0 + 0.3, Y0 + 8, Y0 + 8.6, YZ0 - 4, YZ1, P.trim, { ghost = true })
	for _, z in { { YZ0 - 4, YZ0 - 4.2 }, { YZ1, YZ1 + 0.2 } } do
		B.blk("Shell", "Dado", x0, wx, Y0, Y0 + 1.2, z[1], z[2], P.floor2, { ghost = true })
		B.blk("Shell", "Band", x0, wx, Y0 + 8, Y0 + 8.6, z[1], z[1] + (z[2] - z[1]) * 1.5, P.trim, { ghost = true })
	end
	-- the deck at the far end, its stairs up the arcade side (to the arcade's wall, whole there), its landing
	local D = AISLE.deck
	local pr = folderIn(B.root, "Practice")
	B.blk("Shell", "Deck", x0, D.x1, Y0, D.top, D.z0, YZ1, P.ledge)
	B.part("Shell", "Nose", CF((x0 + D.x1) / 2, D.top - 0.1, D.z0 + 0.1), V3(D.x1 - x0, 1.4, 1.4), P.trim, { cyl = true })
	B.blk("Scenery", "EdgeLight", x0, D.x1, D.top - 1.3, D.top - 1.0, D.z0 + 0.05, D.z0 + 0.2, P.litEdge, { ghost = true, mat = NEON })
	local rise = (D.top - Y0) / D.steps
	for k = 1, D.steps do
		local za, zb = D.z0 - (k - 1) * 2, D.z0 - k * 2
		B.blk("Shell", "DeckStep", D.x1, wx, Y0, Y0 + k * rise, za, zb, P.ledge)
		B.part("Shell", "StepNose", CF((D.x1 + wx) / 2, Y0 + k * rise - 0.3, za + 0.05), V3(wx - D.x1, 0.6, 0.6), P.trim, { cyl = true })
	end
	B.blk("Shell", "DeckLanding", D.x1, wx, Y0, D.top, D.z0 - 2 * D.steps, YZ1, P.ledge)
	-- the board on the deck's face: your own numbers, painted on your screen by PracticeBoard.client
	local bw, bh = 16, 3.6
	local board = Instance.new("Part")
	board.Name = "Board"; board.Anchored = true; board.CanCollide = false; board.CanQuery = false; board.CanTouch = false; board.CastShadow = false
	board.Size = V3(bw, bh, 0.25); board.Color = Color3.fromHex(P.board); board.Material = SP
	board.CFrame = B.at(CFrame.lookAt(V3((x0 + D.x1) / 2, Y0 + 0.5 + bh / 2, D.z0 + 0.15), V3((x0 + D.x1) / 2, Y0 + 0.5 + bh / 2, D.z0 + 10)))
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 40; g.LightInfluence = 0
	for i, c in { { "Damage", "DAMAGE", "0" }, { "Dps", "DPS", "-" }, { "Ttk", "TIME TO KILL", "-" } } do
		local col = Instance.new("Frame")
		col.Name = c[1]; col.BackgroundTransparency = 1; col.Size = UDim2.fromScale(1 / 3, 1); col.Position = UDim2.fromScale((i - 1) / 3, 0)
		local lab = Instance.new("TextLabel")
		lab.Name = c[1] .. "Label"; lab.BackgroundTransparency = 1; lab.Size = UDim2.fromScale(0.9, 0.26); lab.Position = UDim2.fromScale(0.05, 0.1)
		lab.TextScaled = true; lab.Text = c[2]; lab.TextColor3 = Color3.fromHex(P.grey)
		lab.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.SemiBold)
		lab.Parent = col
		local val = Instance.new("TextLabel")
		val.Name = c[1] .. "Value"; val.BackgroundTransparency = 1; val.Size = UDim2.fromScale(0.9, 0.5); val.Position = UDim2.fromScale(0.05, 0.4)
		val.TextScaled = true; val.Text = c[3]; val.TextColor3 = Color3.fromHex(P.pale)
		val.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
		val.Parent = col
		col.Parent = g
	end
	g.Parent = board
	board.Parent = pr
	-- the rails: slow at 10 m, quicker on the 20 m line, quickest on the deck's 30 m line
	local s3, s4, s5 = T.DUMMIES.Stand3, T.DUMMIES.Stand4, T.DUMMIES.Dummy2
	rail(B, s3[1], Y0, s3[3], T.RAILS.Stand3[1], { line = true })
	rail(B, s4[1], Y0, s4[3], T.RAILS.Stand4[1])
	rail(B, s5[1], D.top, s5[3], T.RAILS.Dummy2[1])
	-- the floor: a pale line at every pier short of the deck, the 10 and 20 m lines on the floor and the 30 m on the deck,
	-- their numbers to the arcade side
	for _, z in PIERS do if z > D.z0 + 1 then B.line(x0 + 1.85, z, x1, z, Y0 + 0.01, 0.7, P.line, "PierLine") end end
	for k, z in { -8176, -8206, -8236 } do
		local fy, xe = if z < D.z0 then D.top else Y0, if z < D.z0 then D.x1 else x1
		B.blk("Scenery", "DistLine", x0 + 1.85, xe, fy + 0.03, fy + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true })
		B.text("DistWord", { { ("%d M"):format(k * 10), P.pale, "B", 1 } }, 6, 2.4, CF(xe - 4.2, fy + 0.05, z + 2.2) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
	end
	-- the two consoles at the lane's start (the live-fire console's kind; hold E): BEHAVIOUR and HEALTH (Dummies.luau)
	local function console(name, word, cx, cz, hex)
		local ch = Y0 + 2.55
		B.blk("Shell", "ConsoleBase", cx - 1.6, cx + 1.6, Y0, ch - 0.55, cz + 1.2, cz - 1.2, P.slate)
		B.part("Shell", "PracticeTop", CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0), V3(3.6, 0.8, 2.9), P.pier2)
		local btn = B.part("Scenery", name, CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0) * CF(0, 0.45, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.5, 1.7, 1.7), hex, { cyl = true, ghost = true })
		btn.Parent = pr
		local pp = Instance.new("ProximityPrompt")
		pp.Name = "Prompt"; pp.ActionText = "Change"; pp.ObjectText = word; pp.HoldDuration = 0.3
		pp.MaxActivationDistance = 8; pp.RequiresLineOfSight = false; pp.KeyboardKeyCode = Enum.KeyCode.E
		pp.Parent = btn
		B.text("ConsoleWord", { { word, P.pale, "B", 1 } }, 2.9, 0.55, CF(cx, Y0 + 1.15, cz + 1.24) * CFrame.Angles(0, math.pi, 0), { plate = P.slate, thick = 0.05 })
	end
	console("BehaviourButton", "BEHAVIOUR", x0 + 5.5, YZ0 - 14, P.amber)
	console("HealthButton", "HEALTH", x0 + 11.5, YZ0 - 14, P.chill)
	healPad(B, x1 - 4.9, Y0, YZ0 - 10)
	-- the lane's box: the dummies shoot back only at players inside it
	local zone = Instance.new("Part")
	zone.Name = "Zone"; zone.Anchored = true; zone.Transparency = 1; zone.CanCollide = false; zone.CanQuery = false; zone.CanTouch = false
	zone.Size = V3(wx - x0, AISLE.ceil - Y0, (YZ0 - 4) - YZ1); zone.CFrame = B.cf((x0 + wx) / 2, (Y0 + AISLE.ceil) / 2, (YZ0 - 4 + YZ1) / 2)
	zone.Parent = pr
	-- cover along the far wall, as on the yard's east walk: a chest-high wall, then a head-high one, centred in their bays
	B.put("tv_cover", CF(x0 + 4.8, Y0, -8170) * CFrame.Angles(0, math.pi / 2, 0), { name = "Cover" })
	B.solid("CoverBox", CF(x0 + 4.8, Y0 + 2.35, -8170), V3(2.4, 4.7, 10))
	for _, dz in { -2.5, 2.5 } do B.put("tv_block", CF(x0 + 4.8, Y0, -8186 + dz), { name = "Block" }) end
	B.solid("BlockBox", CF(x0 + 4.8, Y0 + 3.8, -8186), V3(5, 7.6, 10))
	-- the end: the big target on the end wall, lit from the last bay
	B.put("tv_target", CF(ax, 254, YZ1 + 0.75), { name = "AisleTarget", scale = 0.75 }) -- (over the deck since 18 Nov)
	B.lamp(ax, AISLE.ceil - 1.5, YZ1 + 9, "spot", 24, 0.6, P.lampWhite, { look = V3(ax, 254, YZ1), angle = 70 })
end
local function yard(B)
	-- floors: the walks and both ends at the yard's floor, the lane a step down with a half-step at each end
	B.blk("Shell", "YardFloor", -YX - 4, -LANE.x, 236, Y0, YZ0 + 0.1, STAGE.z + 2, P.floor)
	B.blk("Shell", "YardFloor", LANE.x, YX + 4, 236, Y0, YZ0 + 0.1, STAGE.z + 2, P.floor)
	B.blk("Shell", "YardFloor", -LANE.x, LANE.x, 236, Y0, YZ0 + 0.1, LANE.z0, P.floor)
	B.blk("Shell", "YardFloor", -LANE.x, LANE.x, 236, Y0, LANE.z1, STAGE.z + 2, P.floor)
	B.blk("Shell", "StageStep", -YX - 4, YX + 4, 236, Y0 + 1, STAGE.z + 2, STAGE.z, P.floor2)
	B.blk("Shell", "Stage", -YX - 3.95, YX + 3.95, 236.05, STAGE.y, STAGE.z, YZ1 - 3.95, P.floor)
	B.part("Shell", "StageNose", CF(0, STAGE.y - 0.45, STAGE.z + 0.05), V3(2 * YX - 3.4, 0.9, 0.9), P.trim, { cyl = true })
	B.part("Shell", "StepNose", CF(0, Y0 + 0.55, STAGE.z + 2.05), V3(2 * YX - 3.4, 0.9, 0.9), P.trim, { cyl = true })
	B.blk("Shell", "Lane", -LANE.x, LANE.x, 236, LANE.y, LANE.z0, LANE.z1, P.floor2)
	B.blk("Shell", "LaneStep", -LANE.x, LANE.x, 236, LANE.y + 0.5, LANE.z0, LANE.z0 - 1.6, P.floor2)
	B.blk("Shell", "LaneStep", -LANE.x, LANE.x, 236, LANE.y + 0.5, LANE.z1 + 1.6, LANE.z1, P.floor2)
	for _, sx in { -1, 1 } do
		B.blk("Shell", "Kerb", sx * LANE.x, sx * (LANE.x + 0.7), Y0 - 0.05, Y0 + 0.2, LANE.z0, LANE.z1, P.trim)
		B.blk("Shell", "KerbFace", sx * (LANE.x - 0.02), sx * (LANE.x - 0.1), LANE.y, Y0 - 0.05, LANE.z0, LANE.z1, P.slate, { ghost = true })
	end
	-- (16 Nov, the owner: "there is a roof in the dummy part of the training hub that lets you clip through it and get
	-- outside": the vault is a mesh nothing touches, and these walls stopped at its springing, so over the vault the
	-- sides were open. the walls go up to the roof now, and thick unseen solids line the vault's inside)
	-- (18 Nov: the west wall is the side hall's arcade: whole over the openings' heads and along the live-fire end)
	B.blk("Shell", "YardWallW", -YX - 4, -YX, AISLE.head, 272, YZ0, YZ1, P.wall)
	B.blk("Shell", "YardWallW", -YX - 4, -YX, 236, AISLE.head, AISLE.open, YZ1, P.wall)
	B.blk("Shell", "YardWallE", YX, YX + 4, 236, 272, YZ0, YZ1, P.wall)
	do
		local R = (48 * 48 / 4 + 10 * 10) / (2 * 10) -- the vault's arc (tv_rib, tv_vault): span 48, rise 10 from y 258
		local th0 = math.asin(24 / R)
		local N = 16
		for i = 0, N - 1 do
			local a = -th0 + (i + 0.5) * 2 * th0 / N
			local chord = 2 * (R + 4) * math.sin(th0 / N) + 0.6
			B.solid("VaultSolid", CF(0, 258 + 10 - R, (YZ0 + YZ1) / 2) * CFrame.Angles(0, 0, -a) * CF(0, R + 2, 0), V3(chord, 4, YZ0 - YZ1))
		end
	end
	-- the end wall: the garage door's opening on the axis (push 10; the door, its frame and panel: TrainingLot)
	B.blk("Shell", "YardEnd", -YX - 4, -12, 236, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardEnd", 12, YX + 4, 236, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardEnd", -12, 12, 258.55, 271, YZ1, YZ1 - 4, P.wall)
	B.blk("Shell", "YardFront", -YX - 4, -9.9, 236, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardFront", 9.9, YX + 4, 236, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardFront", -9.9, 9.9, MTOP, 271, YZ0 + 4, YZ0, P.wall)
	B.blk("Shell", "YardRoof", -YX - 4, YX + 4, 270.5, 272, YZ0 + 4, YZ1 - 4, P.wall, { nq = true })
	for _, e in { { -YX - 4.4, -YX - 2.4, YZ0 + 4.4, YZ1 - 4.4 }, { YX + 2.4, YX + 4.4, YZ0 + 4.4, YZ1 - 4.4 } } do
		B.blk("Shell", "RoofCoping", e[1], e[2], 271, 273, e[3], e[4], P.wall2, { nq = true })
	end
	-- base strip and band along both long walls and the end
	for _, sx in { -1, 1 } do
		local z0 = if sx < 0 then AISLE.open else YZ0 -- (the west one only where the wall is whole)
		B.blk("Shell", "Dado", sx * YX, sx * (YX - 0.2), Y0, Y0 + 1.2, z0, YZ1, P.floor2, { ghost = true })
		B.blk("Shell", "Band", sx * YX, sx * (YX - 0.3), Y0 + 8, Y0 + 8.6, z0, YZ1, P.trim, { ghost = true })
	end
	B.blk("Shell", "Dado", -YX, -24, STAGE.y, STAGE.y + 1.2, YZ1, YZ1 + 0.2, P.floor2, { ghost = true }) -- (clear of the lot's panels)
	B.blk("Shell", "Dado", 24, YX, STAGE.y, STAGE.y + 1.2, YZ1, YZ1 + 0.2, P.floor2, { ghost = true })
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
		B.drum("Scenery", "StandRing", d[1], d[3], d[2] + 0.03, d[2] + 0.06, 4, P.trim, { ghost = true })
		B.drum("Scenery", "StandRingIn", d[1], d[3], d[2] + 0.06, d[2] + 0.1, 2.9, P.floor2, { ghost = true })
	end
	-- the distances (owner, 16 Nov: "maybe have dummies marked every so many meters"): a line across the floor every
	-- 10 m from the yard's mouth, its number big on the floor before it
	for k, z in { -8176, -8206, -8236 } do
		local fy = if z < STAGE.z then STAGE.y elseif z < LANE.z0 and z > LANE.z1 then LANE.y else Y0
		if fy == LANE.y then
			B.blk("Scenery", "DistLine", -LANE.x, LANE.x, fy + 0.03, fy + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true })
			for _, sx in { -1, 1 } do B.blk("Scenery", "DistLine", sx * (LANE.x + 0.7), sx * (YX - 1.6), Y0 + 0.03, Y0 + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true }) end
		else -- (on the stage: between the shooters' stands)
			B.blk("Scenery", "DistLine", -10.4, 10.4, fy + 0.03, fy + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true })
		end
		B.text("DistWord", { { ("%d M"):format(k * 10), P.pale, "B", 1 } }, 7, 2.6, CF(0, fy + 0.05, z + 2.2) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
	end
	-- the live-fire end: a hazard band across the floor at its line, LIVE FIRE on the stage, a console where you come
	-- into the yard (hold E: the two at the back shoot at whoever is past the line for 90 s, and never past it:
	-- Dummies), a beacon post at each end of the line that turns red while they are live. (16 Nov, the owner: "the
	-- button to activate the bots that fire back being all the way back is redundant": you switch it on as you come
	-- in, then walk down to the line. it stood at the line on the west wall until then)
	local lf = folderIn(B.root, "LiveFire")
	lf:SetAttribute("Line", B.at(CF(0, 0, T.LIVE.line)).Position.Z)
	local zp = Instance.new("Part")
	zp.Name = "Zone"; zp.Anchored = true; zp.Transparency = 1; zp.CanCollide = false; zp.CanQuery = false; zp.CanTouch = false
	zp.Size = V3(2 * YX, 30, T.LIVE.line - YZ1); zp.CFrame = B.cf(0, Y0 + 15, (T.LIVE.line + YZ1) / 2)
	zp.Parent = lf
	for k = 0, 23 do
		local x0 = -YX + 2 * k
		B.blk("Scenery", "LiveBand", x0, x0 + 2, Y0 + 0.03, Y0 + 0.07, T.LIVE.line + 0.7, T.LIVE.line - 0.7, if k % 2 == 0 then P.amber else P.slate, { ghost = true })
	end
	B.text("LiveWord", { { "LIVE FIRE", P.amber, "B", 1 } }, 13, 2.8, CF(0, STAGE.y + 0.05, STAGE.z - 2.5) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
	for _, sx in { -1, 1 } do
		local x = sx * (YX - 2.6)
		B.blk("Shell", "LivePost", x - 0.7, x + 0.7, Y0, Y0 + 7, T.LIVE.line + 0.7, T.LIVE.line - 0.7, P.slate)
		local lamp = B.blk("Scenery", "LiveLamp", x - 0.9, x + 0.9, Y0 + 7, Y0 + 8.4, T.LIVE.line + 0.9, T.LIVE.line - 0.9, "6b4a46", { ghost = true })
		lamp:SetAttribute("Lamp", true)
		lamp.Parent = lf
		local pl = Instance.new("PointLight"); pl.Color = Color3.fromRGB(255, 70, 50); pl.Range = 16; pl.Brightness = 1.2; pl.Enabled = false; pl.Parent = lamp
	end
	-- the console: a slate pedestal with a sloped face and a big round button (hold E), just inside the yard's door on
	-- the east walk, its face to you as you come in. (16 Nov: its top's high edge stood at 4.8, over your eye (4.2 on the
	-- owner's avatar), and from 0.6 off it filled a corner of the screen. it is 1.2 lower now, a desk you look down on, and
	-- T.HEAD.guard keeps your head off it)
	local cx, cz, ch = 16.5, YZ0 - 5, Y0 + 2.55
	B.blk("Shell", "ConsoleBase", cx - 1.6, cx + 1.6, Y0, ch - 0.55, cz + 1.2, cz - 1.2, P.slate)
	B.part("Shell", "ConsoleTop", CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0), V3(3.6, 0.8, 2.9), P.pier2)
	local btn = B.part("Scenery", "LiveButton", CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0) * CF(0, 0.45, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.5, 1.7, 1.7), "8a3a33", { cyl = true, ghost = true })
	btn:SetAttribute("Lamp", true)
	btn.Parent = lf
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "Prompt"; pr.ActionText = "Live fire on"; pr.ObjectText = "Shooting dummies"; pr.HoldDuration = 0.4
	pr.MaxActivationDistance = 9; pr.RequiresLineOfSight = false; pr.KeyboardKeyCode = Enum.KeyCode.E
	pr.Parent = btn
	local dm = T.DUMMIES.Dummy
	-- (the moving one strafes along the 20 m line: it is his track; since 18 Nov a rail's bed under it, the lane's step
	-- for its stops)
	rail(B, dm[1], LANE.y, dm[3], 11.4, { stops = false })
	healPad(B, YX - 4, STAGE.y, YZ1 + 6) -- (the live-fire end: on the stage by the east wall, clear of the door and the stand)
	-- the shooters' round stands at the live-fire end's far corners
	local pk = T.DUMMIES.Plinker
	for _, n in { "Plinker", "Plinker2" } do
		local q = T.DUMMIES[n]
		B.put("tv_pulpit", CF(q[1], STAGE.y, q[3]), { name = "PlinkerStand" })
		B.drum("Collision", "PlinkerStandSolid", q[1], q[3], STAGE.y, STAGE.y + 2, 12.4, P.pier, { tr = 1, noShadow = true })
		B.drum("Shell", "PlinkerTop", q[1], q[3], STAGE.y + 1.9, q[2] - 0.3, 8, P.pier2)
		B.drum("Shell", "PlinkerTopLip", q[1], q[3], q[2] - 0.35, q[2], 8.5, P.trim)
	end
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
	-- other way round; two low walls in the lane before the stage; the middle kept open. (18 Nov: the west walk's two
	-- went into the side hall, so the arcade's openings stay clear)
	for _, c in { { 1, -8186, "low" }, { 1, -8202, "high" } } do
		local x, z = c[1] * 19.2, c[2]
		if c[3] == "high" then
			for _, dz in { -2.5, 2.5 } do B.put("tv_block", CF(x, Y0, z + dz), { name = "Block" }) end
			B.solid("BlockBox", CF(x, Y0 + 3.8, z), V3(5, 7.6, 10))
		else
			B.put("tv_cover", CF(x, Y0, z) * CFrame.Angles(0, math.pi / 2, 0), { name = "Cover" })
			B.solid("CoverBox", CF(x, Y0 + 2.35, z), V3(2.4, 4.7, 10))
		end
	end

	aisle(B)
	-- the dummies' spots
	local ds = folderIn(B.mk, "DummySpots")
	for n, d in T.DUMMIES do
		local m = B.marker(ds, n, d[1], d[2], d[3], V3(d[1], d[2], d[3] + 10))
		local r = T.RAILS[n]
		if r then m:SetAttribute("Span", r[1]); m:SetAttribute("Speed", r[2]) end
		if T.LANE[n] then m:SetAttribute("Lane", "practice") end
	end
end

-- ---------------------------------------------------------------- the firing range (Cardboard Carl's)
-- booths under a coffered canopy, then the lane open to the sky between thick portal frames, stepping up in two
-- kerbed terraces; the Carls stand on three low plinths; the lane ends on a backstop bank and a rack of steel plates
local RX0, RX1, RZ0, RZ1 = 30, 78, -8102, -8300
T.RANGE_WALL_GROUP = "JFRayBlind" -- (the range's bodies-only wall: Main.server's group, colliding with the players' groups and not with Default, where rays, ropes and bullets are cast)
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
	-- (the second terrace stops short of the basement's stairwell, T.BASEMENT.well, cut into the backstop over it, and
	-- of the walk-out's stair hall in the bank, T.BASEMENT.exit; over its first flight it is 4 thick, 244..248)
	local EX = T.BASEMENT.exit
	B.blk("Shell", "Terrace2", RX0, RX1, 236, 248, T2Z, EX.land.z0, P.floor)
	B.blk("Shell", "Terrace2", EX.thin.x1, RX1, 236, 248, EX.land.z0, EX.face, P.floor)
	B.blk("Shell", "Terrace2", RX0, EX.thin.x1, EX.thin.y, 248, EX.land.z0, EX.face, P.floor)
	B.blk("Shell", "Terrace2", T.BASEMENT.well.x0, RX1, 236, 248, EX.face, T.BASEMENT.well.z1, P.floor)
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
		B.blk("Shell", "Step", x[1], x[2], 236.05, 241, DECK_Z, DECK_Z - 3, P.floor2)
		B.blk("Shell", "Step", x[1], x[2], 236.05, 242, T1Z + 4, T1Z, P.floor2)
		B.blk("Shell", "Step", x[1], x[2], 236.05, 246, T2Z + 4, T2Z, P.floor2)
	end
	-- (16 Nov: three lanes, one per plate) low dividers down the lane between them, broken at the row plinths and the
	-- terrace noses, so each runner has a lane of their own and the view down the lane stays open
	for _, x in { 47, 61 } do
		for _, seg in { { DECK_Z - 0.4, -8181, Y0 }, { -8185, T1Z + 1, Y0 }, { T1Z - 1, -8226, 244 }, { -8230, T2Z + 1, 244 }, { T2Z - 1, -8271, 248 }, { -8275, -8287, 248 } } do
			B.blk("Shell", "LaneDivider", x - 0.6, x + 0.6, seg[3], seg[3] + 2.2, seg[1], seg[2], P.pier2)
			B.part("Shell", "LaneDividerNose", CF(x, seg[3] + 2.2, (seg[1] + seg[2]) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(seg[2] - seg[1]), 1.3, 1.3), P.trim, { cyl = true })
		end
	end
	-- (16 Nov, sealing: the lane is open to the sky, so an unseen lid at the walls' tops keeps you inside, and a thick
	-- one over the canopy)
	B.solid("RangeLid", CF((RX0 + RX1) / 2, RTOP + 6, (DECK_Z + RZ1) / 2), V3(RX1 - RX0 + 8, 4, DECK_Z - RZ1 + 8)) -- (4 over the walls' tops: no room to stand on them; clear of the gold one on the beam)
	-- (20 Nov 2026, the owner, from the live game: "my friend went into wher ethe e dummies flip up") nobody walks, jumps,
	-- grapples or dashes down-range: a wall for BODIES only across the lane at the deck's edge, floor to the lid. It is
	-- CanQuery off (every ray passes: bullets, the sniper, the grapple's aim, the projectiles' sweeps) and in JFRayBlind,
	-- the group that collides with the players' groups only (Main.server; the arenas' roof columns use it): physical
	-- projectiles in Default, like the cart, pass. A low rail on the deck's edge shows the line. Anyone down-range (the basement's
	-- walk-out opens onto the far terrace) is put back on the deck by RangeBack as they come up the lane
	pcall(function() game:GetService("PhysicsService"):RegisterCollisionGroup(T.RANGE_WALL_GROUP) end)
	local bw = B.blk("Collision", "RangeWall", RX0, RX1, Y0, RTOP + 10, DECK_Z - 0.4, DECK_Z - 4.4, P.wall, { tr = 1, nq = true, noShadow = true })
	bw.CastShadow = false
	pcall(function() bw.CollisionGroup = T.RANGE_WALL_GROUP end)
	B.part("Scenery", "RangeRail", CF((RX0 + RX1) / 2, DECK + 1.1, DECK_Z + 0.4) * CFrame.Angles(0, 0, 0), V3(RX1 - RX0 - 0.4, 0.5, 0.5), P.trim, { cyl = true, ghost = true })
	for x = RX0 + 0.8, RX1 - 0.8, 6.8 do
		B.blk("Scenery", "RangeRailPost", x - 0.25, x + 0.25, DECK, DECK + 1.1, DECK_Z + 0.15, DECK_Z + 0.65, P.pier2, { ghost = true })
	end
	B.trigger("RangeBack", RX0, RX1, Y0, Y0 + 14, DECK_Z - 4.6, DECK_Z - 12, { Land = "RangeDeck" })
	local rd = Instance.new("Folder"); rd.Name = "RangeDeck"; rd:SetAttribute("Built", "TrainingV2"); rd.Parent = B.doors
	for _, x in { 44, 54, 64 } do B.marker(rd, "Spot", x, DECK, DECK_Z + 12, V3(x, DECK, DECK_Z - 20)) end
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
	-- (the end wall has the lot's exit door in it: T.BASEMENT.door, up to the well's top)
	local BD, BW = T.BASEMENT.door, T.BASEMENT.well
	B.blk("Shell", "RangeEnd", RX0 - 4, BD[1], 236, RTOP, RZ1, RZ1 - 4, P.wall)
	B.blk("Shell", "RangeEnd", BD[2], RX1 + 4, 236, RTOP, RZ1, RZ1 - 4, P.wall)
	B.blk("Shell", "RangeEnd", BD[1], BD[2], BW.top, RTOP, RZ1, RZ1 - 4, P.wall)
	B.blk("Shell", "RangeEnd", BD[1], BD[2], 236, 239, RZ1, RZ1 - 4, P.wall) -- (under the lot's threshold, ExitFloor 239..240)
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
			B.blk("Shell", "PierCap", sx, sx + s * 3.0, top - 2.8, top - 1.95, z - 2.4, z + 2.4, P.trim)
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
	B.solid("CanopySolid", CF((RX0 + RX1) / 2, CY + 3.3, (RZ0 + DECK_Z - 1) / 2), V3(RX1 - RX0, 3, RZ0 - DECK_Z + 1))
	for _, z in { -8114, -8126, -8138 } do B.blk("Shell", "CanopyBeam", RX0, RX1, CY - 1.4, CY, z - 0.7, z + 0.7, P.pier) end
	for _, x in { 46, 62 } do B.blk("Shell", "CanopyBeam", x - 0.7, x + 0.7, CY - 1.4, CY, RZ0, DECK_Z, P.pier) end
	B.blk("Shell", "Fascia", RX0, RX1, CY - 2.6, CY + 2, DECK_Z + 1, DECK_Z - 1.2, P.pier)
	B.blk("Shell", "FasciaEdge", RX0, RX1, CY - 2.65, CY - 2.2, DECK_Z + 1.1, DECK_Z - 1.3, P.trim)
	for _, x in { 38, 54, 70 } do
		for _, z in { -8108, -8120, -8132, -8143 } do
			B.blk("Scenery", "CanopyPanel", x - 3, x + 3, CY - 0.25, CY - 0.05, z - 2.6, z + 2.6, "a7acb3", { ghost = true, mat = NEON })
		end
		B.lamp(x, CY - 0.7, -8137, "spot", 26, 1.0, P.lampWhite, { angle = 120, shadows = x == 54 })
		B.lamp(x, CY - 0.7, -8110, "spot", 24, 0.7, P.warm, { angle = 120 })
	end
	-- the gun shop at the back of the deck (owner, 16 Nov: "behind the shooting range is still really bland, maybe you
	-- can have a gun shop look behind it like this with an npc me?"): a pale slatwall let into the back wall with our
	-- guns hung on it in rows, a glass counter with the sidearms and items under its glass, the shopkeeper behind it (the
	-- owner's own avatar, with the shop on his prompt: ShopKeeper.server), a low dark shelf of ammo boxes with headsets
	-- on hooks over it at the west end, a tall lit glass case at the east end, the canopy's light panels over it all.
	-- no words, names or marks anywhere. the guns are made when the server starts (ShopKeeper.server, from
	-- WeaponModels: always today's models) at the Pegs in Range.Shop: Gun = a weapon id or "item:<id>", Len = the
	-- longest it may be, High = the tallest, Out = which way is out of the surface it hangs or rests on, Hook = it
	-- hangs on two hooks. the place behind the counter is shut off (the counter, its two returns, ShopBox over them)
	local SH = folderIn(B.root.Range, "Shop")
	local WZ = RZ0 - 0.5 -- the slatwall's face
	local GLASS = "d3e0e6"
	local function glass(name, x0, x1, y0, y1, z0, z1)
		return B.blk("Scenery", name, x0, x1, y0, y1, z0, z1, GLASS, { mat = Enum.Material.Glass, tr = 0.6, noShadow = true })
	end
	local function peg(gun, x, y, z, rot, len, high, out, hook)
		local p = B.marker(SH, "Peg", x, y, z)
		p.CFrame = B.at(CF(x, y, z) * rot)
		p:SetAttribute("Gun", gun); p:SetAttribute("Len", len); p:SetAttribute("High", high); p:SetAttribute("Out", out)
		if hook then p:SetAttribute("Hook", true) end
		return p
	end
	local HANG = CFrame.Angles(0, math.pi / 2, 0)      -- barrel to -x, its right side to the deck
	local LIE = CFrame.Angles(math.pi / 2, 0, 0) * HANG -- the same gun on its left side, its right side up
	local OUT_WALL, UP = V3(0, 0, -1), V3(0, 1, 0)
	-- the slatwall: a pale panel let into the back wall, dark slats across it, a trim along its head
	B.blk("Shell", "Slatwall", RX0 + 1.6, 67.6, DECK + 4.4, DECK + 12.2, RZ0 + 0.1, WZ, "e4e1da")
	for k = 0, 7 do
		local y = DECK + 4.95 + k * 1.0
		B.blk("Scenery", "Slat", RX0 + 1.75, 67.45, y - 0.08, y + 0.08, WZ + 0.05, WZ - 0.06, P.slate, { ghost = true })
	end
	B.blk("Scenery", "SlatwallTrim", RX0 + 1.4, 67.8, DECK + 12.15, DECK + 12.45, RZ0 + 0.1, WZ - 0.15, P.trim, { ghost = true })
	-- the guns on it, three rows, the long ones up top
	for _, row in {
		{ DECK + 11.0, { { "sniper", 45.6, 6.0 }, { "lmg", 52.0, 5.8 }, { "dmr", 58.2, 5.6 }, { "ar", 64.2, 5.0 } } },
		{ DECK + 8.7, { { "shotgun", 45.4, 5.4 }, { "lever", 51.6, 5.4 }, { "burst", 57.8, 5.2 }, { "autoshot", 63.9, 5.2 } } },
		{ DECK + 6.4, { { "smg", 45.0, 4.4 }, { "redline", 50.6, 5.0 }, { "marbles", 57.2, 4.6 }, { "sawnoff", 63.2, 4.2 } } },
	} do
		for _, g in row[2] do peg(g[1], g[2], row[1], WZ, HANG, g[3], 1.9, OUT_WALL, true) end
	end
	-- the west end: a low dark shelf full of ammo boxes, two ammo cans on it, headsets on hooks over it
	local SX0, SX1 = RX0 + 1.6, 41.2
	B.blk("Scenery", "ShelfBack", SX0 + 0.05, SX1 - 0.05, DECK, DECK + 4.18, RZ0 + 0.05, RZ0 - 0.3, P.board)
	for _, x in { SX0, SX1 - 0.3 } do B.blk("Scenery", "ShelfSide", x, x + 0.3, DECK, DECK + 4.2, RZ0 + 0.03, RZ0 - 2.8, P.board) end
	B.blk("Scenery", "ShelfTop", SX0 - 0.1, SX1 + 0.1, DECK + 4.15, DECK + 4.4, RZ0 + 0.02, RZ0 - 2.95, P.board)
	local BOX = { "b49a7a", "8f9299", "6c7466", "c8bdae", "7d8088", "a0835f" }
	local WIDE = { 1.3, 1.0, 1.3, 0.9, 1.2, 1.0, 1.25 }
	local TALL = { 0.9, 0.7, 0.85, 0.95, 0.75, 0.8 }
	for si, yb in { DECK + 0.1, DECK + 1.5, DECK + 2.9 } do
		B.blk("Scenery", "Shelf", SX0 + 0.25, SX1 - 0.25, yb, yb + 0.2, RZ0 - 0.25, RZ0 - 2.7, P.board)
		local x, i = SX0 + 0.55, si * 2
		while true do
			local w = WIDE[i % #WIDE + 1]
			if x + w > SX1 - 0.55 then break end
			local h = TALL[i % #TALL + 1]
			B.blk("Scenery", "AmmoBox", x, x + w, yb + 0.18, yb + 0.2 + h, RZ0 - 0.5, RZ0 - 2.3, BOX[i % #BOX + 1], { ghost = true })
			x += w + 0.16; i += 1
		end
	end
	local function can(x, y, z)
		B.blk("Scenery", "AmmoCan", x - 0.85, x + 0.85, y - 0.02, y + 1.0, z - 0.47, z + 0.47, "6c7466", { ghost = true })
		B.blk("Scenery", "AmmoCanLid", x - 0.9, x + 0.9, y + 0.98, y + 1.14, z - 0.52, z + 0.52, "5c6358", { ghost = true })
		B.blk("Scenery", "AmmoCanHandle", x - 0.45, x + 0.45, y + 1.12, y + 1.26, z - 0.1, z + 0.1, P.slate, { ghost = true })
	end
	can(34.4, DECK + 4.4, RZ0 - 1.5)
	can(38.4, DECK + 4.4, RZ0 - 1.5)
	local function headset(x, y, accent)
		local band = if accent then P.amber else "3a3e46"
		B.blk("Scenery", "Hook", x - 0.11, x + 0.11, y - 0.33, y - 0.07, WZ + 0.05, WZ - 0.95, P.slate, { ghost = true })
		B.blk("Scenery", "HeadsetBand", x - 0.8, x + 0.8, y - 0.1, y + 0.12, WZ - 0.3, WZ - 0.72, band, { ghost = true })
		for _, sx in { -1, 1 } do
			B.blk("Scenery", "HeadsetArm", x + sx * 0.8 - 0.11, x + sx * 0.8 + 0.11, y - 1.0, y + 0.02, WZ - 0.32, WZ - 0.7, band, { ghost = true })
			B.part("Scenery", "HeadsetCup", CF(x + sx * 0.72, y - 1.3, WZ - 0.51), V3(0.5, 1.1, 1.1), "4a4f58", { cyl = true, ghost = true })
			B.part("Scenery", "HeadsetPad", CF(x + sx * 0.42, y - 1.3, WZ - 0.51), V3(0.16, 0.86, 0.86), "2e3238", { cyl = true, ghost = true })
		end
	end
	for _, y in { DECK + 10.8, DECK + 7.8 } do
		for _, x in { 33.6, 36.4, 39.2 } do headset(x, y, x == 36.4 and y > DECK + 9) end
	end
	-- the glass counter: a dark base, one glass box with a dark bed in it for the sidearms and items, slim posts and a
	-- rim; a closed return at each end back to the wall
	local CX0, CX1, CZ0, CZ1 = 43.6, 64.4, RZ0 - 5.8, RZ0 - 8.4
	B.blk("Shell", "CounterBase", CX0, CX1, DECK, DECK + 0.9, CZ0, CZ1, P.board)
	glass("CounterGlass", CX0 + 0.1, CX1 - 0.1, DECK + 0.85, DECK + 3.4, CZ0 - 0.1, CZ1 + 0.1)
	B.blk("Scenery", "CounterBed", CX0 + 0.3, CX1 - 0.3, DECK + 1.45, DECK + 1.6, CZ0 - 0.3, CZ1 + 0.3, "3a3e46", { ghost = true })
	B.blk("Scenery", "CounterLight", CX0 + 0.5, CX1 - 0.5, DECK + 3.2, DECK + 3.3, CZ0 - 0.3, CZ0 - 0.5, P.lampWhite, { ghost = true, mat = NEON })
	for _, x in { CX0 + 0.05, 53.85, CX1 - 0.35 } do
		for _, z in { CZ1 + 0.05, CZ0 - 0.35 } do
			B.blk("Scenery", "CounterPost", x, x + 0.3, DECK + 0.85, DECK + 3.45, z, z + 0.3, P.slate, { ghost = true })
		end
	end
	for _, z in { CZ1, CZ0 - 0.3 } do B.blk("Scenery", "CounterRim", CX0, CX1, DECK + 3.35, DECK + 3.55, z, z + 0.3, P.slate, { ghost = true }) end
	for _, x in { CX0 + 0.02, CX1 - 0.3 } do B.blk("Scenery", "CounterRim", x, x + 0.28, DECK + 3.36, DECK + 3.53, CZ1 + 0.02, CZ0 - 0.02, P.slate, { ghost = true }) end
	for _, r in { { 41.6, 43.5, 41.5, 43.55 }, { 64.5, 66.4, 64.45, 66.5 } } do -- (their tops stop 0.05 short of the rim)
		B.blk("Shell", "CounterReturn", r[1], r[2], DECK, DECK + 3.3, RZ0 + 0.1, CZ1, P.board)
		B.blk("Scenery", "CounterReturnTop", r[3], r[4], DECK + 3.25, DECK + 3.5, RZ0 + 0.1, CZ1 - 0.1, P.slate, { ghost = true })
	end
	for _, it in { { "pistol", 46.4, 2.4 }, { "revolver", 50.4, 2.6 }, { "item:frag", 54.4, 1.2 }, { "item:medkit", 58.0, 1.7 }, { "item:bubble", 61.6, 1.5 } } do
		local rot = if string.find(it[1], "^item:") then CFrame.identity else LIE
		peg(it[1], it[2], DECK + 1.6, (CZ0 + CZ1) / 2, rot, it[3], 1.4, UP)
	end
	B.solid("ShopBox", CF((41.5 + 66.5) / 2, (DECK + 3.45 + CY) / 2, (RZ0 + CZ1) / 2), V3(25, CY - DECK - 3.45, math.abs(CZ1 - RZ0))) -- (up to the canopy)
	B.marker(SH, "ShopKeeperSpot", 54, DECK, RZ0 - 3.4, V3(54, DECK, RZ0 - 20))
	-- the east end: a tall glass case, lit from its head, a gun on each shelf
	local TX0, TX1, TZ0, TZ1 = 68.6, 76.2, RZ0 - 0.15, RZ0 - 3.6
	B.blk("Shell", "CaseBase", TX0, TX1, DECK, DECK + 1.2, RZ0 + 0.1, TZ1, P.board)
	glass("CaseGlass", TX0 + 0.1, TX1 - 0.1, DECK + 1.15, DECK + 9.3, TZ0, TZ1 + 0.1)
	B.blk("Scenery", "CaseCap", TX0 - 0.1, TX1 + 0.1, DECK + 9.25, DECK + 9.9, RZ0 + 0.1, TZ1 - 0.1, P.board)
	B.blk("Scenery", "CaseLight", TX0 + 0.5, TX1 - 0.5, DECK + 9.1, DECK + 9.27, TZ1 + 0.4, TZ1 + 0.75, P.lampWhite, { ghost = true, mat = NEON })
	for _, x in { TX0 + 0.05, TX1 - 0.35 } do
		for _, z in { TZ1 + 0.05, TZ0 - 0.25 } do
			B.blk("Scenery", "CasePost", x, x + 0.3, DECK + 1.15, DECK + 9.3, z, z + 0.3, P.slate, { ghost = true })
		end
	end
	for _, y in { DECK + 3.95, DECK + 6.65 } do
		B.blk("Scenery", "CaseShelf", TX0 + 0.3, TX1 - 0.3, y, y + 0.1, TZ0 - 0.2, TZ1 + 0.3, P.slate, { ghost = true })
	end
	local cz = (TZ0 + TZ1) / 2
	peg("item:duck", 70.9, DECK + 1.2, cz, CFrame.identity, 2.2, 2.4, UP)
	peg("item:medkit", 74.0, DECK + 1.2, cz, CFrame.identity, 1.8, 2.4, UP)
	peg("shredder", (TX0 + TX1) / 2, DECK + 4.05, cz, HANG, 6.4, 2.4, UP)
	peg("katana", (TX0 + TX1) / 2, DECK + 6.75, cz, HANG, 6.6, 2.2, UP)
	-- (16 Nov, the owner: "gun shop part looks really cute ... can you add more props like cases and bags and cans maybe
	-- some spilt ones" and "can the cases have more stuff too?": stacked hard cases, duffel bags and ammo cans on the
	-- floor either side, a box tipped over with its rounds across the floor and one on the counter's glass, and
	-- magazines, ammo boxes, a scope and loose rounds in the counter and the tall case between the guns)
	local prng = Random.new(1611)
	local BRASS, CASE, LATCH = "c9a24a", "3a3e46", "8f9299"
	local function bit(name, cf, size, hex, cyl) return B.part("Scenery", name, cf, size, hex, { ghost = true, cyl = cyl }) end
	local function hardCase(x, y, z, yaw, len)
		local F = CF(x, y, z) * CFrame.Angles(0, yaw, 0)
		bit("HardCase", F * CF(0, 0.29, 0), V3(len, 0.6, 1.5), CASE)
		bit("HardCaseRim", F * CF(0, 0.32, 0), V3(len + 0.06, 0.1, 1.56), P.slate)
		bit("HardCaseHandle", F * CF(0, 0.32, -0.81), V3(0.9, 0.16, 0.14), P.slate)
		for _, sx in { -0.32, 0.32 } do bit("HardCaseLatch", F * CF(sx * len, 0.32, -0.79), V3(0.3, 0.22, 0.1), LATCH) end
	end
	local function duffel(x, y, z, yaw, len, hex)
		local F = CF(x, y, z) * CFrame.Angles(0, yaw, 0)
		bit("Duffel", F * CF(0, 0.66, 0), V3(len, 1.36, 1.36), hex, true)
		for _, sx in { -1, 1 } do bit("DuffelEnd", F * CF(sx * (len / 2 - 0.05), 0.66, 0), V3(0.16, 1.2, 1.2), P.slate, true) end
		for _, sx in { -0.22, 0.22 } do bit("DuffelStrap", F * CF(sx * len, 0.66, 0), V3(0.2, 1.42, 1.42), P.slate, true) end
		bit("DuffelHandle", F * CF(0, 1.38, 0), V3(len * 0.5, 0.12, 0.28), P.slate)
	end
	local function canAt(x, y, z, yaw)
		local F = CF(x, y, z) * CFrame.Angles(0, yaw, 0)
		bit("AmmoCan", F * CF(0, 0.49, 0), V3(1.7, 1.02, 0.94), "6c7466")
		bit("AmmoCanLid", F * CF(0, 1.06, 0), V3(1.8, 0.16, 1.04), "5c6358")
		bit("AmmoCanHandle", F * CF(0, 1.19, 0), V3(0.9, 0.14, 0.2), P.slate)
	end
	local function round(cf) bit("Round", cf, V3(0.42, 0.13, 0.13), BRASS, true) end -- (lying: its middle 0.06 up)
	-- a small box tipped on its side, its rounds out across the surface in a fan
	local function spill(x, y, z, yaw, n, reach)
		local F = CF(x, y, z) * CFrame.Angles(0, yaw, 0)
		reach = reach or 1.6
		bit("AmmoBoxTipped", F * CF(0, 0.28, 0) * CFrame.Angles(0, 0, math.rad(84)), V3(0.6, 0.95, 0.7), "b49a7a")
		for i = 1, n do
			local d = 0.5 + prng:NextNumber() * reach
			local a = prng:NextNumber(-0.7, 0.7) * math.min(1, reach / 1.6)
			round(F * CF(d * math.cos(a) + 0.3, 0.06, d * math.sin(a)) * CFrame.Angles(0, prng:NextNumber() * 6.28, 0))
		end
	end
	local function ammoBox(cf, hex) bit("AmmoBox", cf * CF(0, 0.17, 0), V3(0.62, 0.36, 0.9), hex or "b49a7a") end
	local function mag(cf) bit("Magazine", cf * CF(0, 0.12, 0), V3(0.95, 0.26, 0.5), "2e3238") end
	-- a rug on the deck in front of the counter (the owner: "can you put a rug in the middle or something?"): a dark
	-- field in a tan border, flat to the floor, nothing to trip on
	B.blk("Scenery", "RugBorder", 45, 63, DECK - 0.02, DECK + 0.05, RZ0 - 9.6, RZ0 - 18.6, "a0835f", { ghost = true })
	B.blk("Scenery", "Rug", 45.7, 62.3, DECK - 0.02, DECK + 0.08, RZ0 - 10.3, RZ0 - 17.9, "3e434b", { ghost = true })
	B.blk("Scenery", "RugBand", 46.4, 61.6, DECK - 0.02, DECK + 0.1, RZ0 - 11.0, RZ0 - 11.25, "a0835f", { ghost = true })
	B.blk("Scenery", "RugBand", 46.4, 61.6, DECK - 0.02, DECK + 0.1, RZ0 - 16.95, RZ0 - 17.2, "a0835f", { ghost = true })
	-- the floor, west: two hard cases stacked, a duffel, a can, a spill
	hardCase(35.2, DECK, RZ0 - 5.2, 0.05, 4.2)
	hardCase(35.4, DECK + 0.58, RZ0 - 5.3, -0.08, 3.6)
	duffel(39.4, DECK, RZ0 - 4.6, 1.45, 3.0, "4f5868")
	canAt(33.0, DECK, RZ0 - 7.6, 0.4)
	spill(36.8, DECK, RZ0 - 8.6, 2.6, 9)
	B.solid("ShopPropBox", CF(36.4, DECK + 0.8, RZ0 - 5.8), V3(8.8, 1.6, 4.4))
	-- the floor, east: cans stacked in front of the tall case, a duffel, a long case on its side
	canAt(69.6, DECK, RZ0 - 6.6, 0.1)
	canAt(71.6, DECK, RZ0 - 6.7, -0.15)
	canAt(70.6, DECK + 1.12, RZ0 - 6.6, 0.3)
	duffel(74.6, DECK, RZ0 - 7.1, 0.2, 3.2, "5c6358")
	spill(72.8, DECK, RZ0 - 9.4, -2.2, 8)
	B.solid("ShopPropBox", CF(72.2, DECK + 1.1, RZ0 - 6.9), V3(8.4, 2.2, 2.6))
	-- the counter: a box spilt on its glass by the till end
	spill(62.2, DECK + 3.4, (CZ0 + CZ1) / 2, math.pi - 0.3, 6, 0.9)
	-- in the counter, between the guns and items: rounds, magazines, ammo boxes, a scope
	local bz = (CZ0 + CZ1) / 2
	local bed = DECK + 1.6
	ammoBox(CF(44.7, bed, bz + 0.3) * CFrame.Angles(0, 0.2, 0))
	for k = 0, 4 do round(CF(44.4 + k * 0.22, bed + 0.06, bz - 0.6) * CFrame.Angles(0, math.pi / 2, 0)) end
	mag(CF(48.3, bed, bz + 0.35) * CFrame.Angles(0, 0.3, 0)); mag(CF(48.5, bed, bz - 0.4) * CFrame.Angles(0, -0.2, 0))
	bit("Scope", CF(52.3, bed + 0.2, bz) * CFrame.Angles(0, 0.15, 0), V3(1.7, 0.36, 0.36), "2e3238", true)
	for _, dx in { -0.62, 0.62 } do bit("ScopeRing", CF(52.3 + dx, bed + 0.2, bz + dx * 0.15), V3(0.12, 0.46, 0.46), P.slate, true) end
	ammoBox(CF(56.2, bed, bz) * CFrame.Angles(0, -0.25, 0), "c8bdae")
	mag(CF(59.8, bed, bz + 0.3) * CFrame.Angles(0, 0.1, 0)); mag(CF(59.9, bed, bz - 0.45) * CFrame.Angles(0, 0.35, 0))
	ammoBox(CF(63.2, bed, bz + 0.35) * CFrame.Angles(0, 0.1, 0), "8f9299")
	for k = 0, 3 do round(CF(62.9 + k * 0.24, bed + 0.06, bz - 0.55) * CFrame.Angles(0, math.pi / 2, 0)) end
	-- in the tall case: a box between the duck and the medkit, magazines and boxes along each shelf's front
	local fz = TZ1 + 0.75
	ammoBox(CF(72.55, DECK + 1.2, cz) * CFrame.Angles(0, 0.1, 0), "c8bdae")
	for _, y in { DECK + 4.05, DECK + 6.75 } do
		mag(CF(70.0, y, fz) * CFrame.Angles(0, 0.2, 0))
		ammoBox(CF(72.4, y, fz) * CFrame.Angles(0, math.pi / 2, 0))
		for k = 0, 3 do round(CF(74.2 + k * 0.24, y + 0.06, fz) * CFrame.Angles(0, math.pi / 2, 0)) end
	end
	-- a white light on the gun wall, a warm one on the shelf
	B.lamp(54, CY - 1.0, RZ0 - 9, "spot", 22, 0.8, P.lampWhite, { look = V3(54, DECK + 8, RZ0), angle = 100 })
	B.lamp(36.4, CY - 1.0, RZ0 - 7, "spot", 16, 0.5, P.warm, { look = V3(36.4, DECK + 6, RZ0), angle = 90 })
	local best = Instance.new("Part")
	best.Name = "BestBoard"; best.Anchored = true; best.CanCollide = false; best.CanQuery = false; best.CanTouch = false
	best.Size = V3(13.6, 3.6, 0.4); best.Color = Color3.fromHex(P.board); best.Material = SP; best.CastShadow = false
	best.CFrame = B.cf((RX0 + RX1) / 2, DECK + 14.4, RZ0 - 0.4) -- (its front, -z, faces the lanes; over the slatwall)
	best.Parent = B.root.Range
	do
		local g = Instance.new("SurfaceGui")
		g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 32; g.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.Name = "Best"; t.BackgroundTransparency = 1; t.TextScaled = true; t.TextWrapped = true; t.RichText = true
		t.Text = "BEST TODAY\nCHILL —   NORMAL —   SWEATY —"; t.TextColor3 = Color3.fromHex(P.pale)
		t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
		t.Size = UDim2.new(0.92, 0, 0.84, 0); t.Position = UDim2.new(0.04, 0, 0.08, 0)
		t.Parent = g
		g.Parent = best
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
	-- (16 Nov: three lanes, a run on each at once: a row per lane, and the last thing that happened)
	lbl("Title", "CARDBOARD CARL'S", 0.06, 0.05, 0.88, 0.14, P.amber, Enum.FontWeight.Heavy)
	for i, pl in T.PLATES do
		lbl("Name" .. pl[1], pl[3], 0.06, 0.12 + i * 0.15, 0.3, 0.12, P[pl[4]], Enum.FontWeight.Heavy)
		lbl("Row" .. pl[1], "free", 0.38, 0.12 + i * 0.15, 0.56, 0.12, P.pale, Enum.FontWeight.Bold)
	end
	lbl("Line", "stand on a plate. 25 cardboard men. he won't shoot back.", 0.06, 0.78, 0.88, 0.18, P.grey, Enum.FontWeight.SemiBold)
	g.Line.TextWrapped = true
	g.Parent = board
	-- the Carls' spots (each looks at the plates) on the row plinths, a foot-mark at each, the distance at each row
	for _, s in T.SPOTS do
		local lane, lx = "Easy", 40
		for _, pl in T.PLATES do if math.abs(pl[2] - s[1]) < math.abs(lx - s[1]) then lane, lx = pl[1], pl[2] end end
		local m = B.marker(B.root.Range.Spots, "Spot", s[1], s[2] + 0.1, s[3], V3(lx, s[2], T.PLATE_Z))
		m:SetAttribute("Lane", lane)
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
	-- (the stairwell down to the basement is a hollow in it: T.BASEMENT.well; and west of it the walk-out's stair hall,
	-- T.BASEMENT.exit: a skin round it, its door in the face, open under 244 over flight A)
	local W, EX = T.BASEMENT.well, T.BASEMENT.exit
	assert(EX.face == BZ, "T.BASEMENT.exit.face is the backstop's face")
	B.blk("Shell", "Backstop", RX0, EX.hall.x0, EX.thin.y, 274, BZ, EX.skin, P.pier2)
	B.blk("Shell", "Backstop", EX.hall.x0, EX.out.x0, 236, 274, BZ, EX.skin, P.pier2)
	B.blk("Shell", "Backstop", EX.out.x1, W.x0, 236, 274, BZ, EX.skin, P.pier2)
	B.blk("Shell", "Backstop", EX.out.x0, EX.out.x1, EX.out.top, 274, BZ, EX.skin, P.pier2)
	B.blk("Shell", "Backstop", EX.out.x0, EX.out.x1, 236, EX.top, BZ, EX.skin, P.pier2)
	B.blk("Shell", "Backstop", RX0, W.x0, EX.ceil, 274, EX.skin, EX.back, P.pier2)
	B.blk("Shell", "Backstop", RX0, W.x0, 236, 274, EX.back, RZ1, P.pier2)
	B.blk("Shell", "Backstop", RX0, EX.x0, 236, EX.ceil, EX.skin, EX.back, P.pier2)
	B.blk("Shell", "Backstop", EX.east, W.x0, 236, EX.ceil, EX.skin, EX.back, P.pier2)
	B.blk("Shell", "Backstop", W.x0, RX1, 236, 274, BZ, W.z1, P.pier2)
	B.blk("Shell", "Backstop", W.x0, RX1, W.top, 274, W.z1, RZ1, P.pier2)
	B.part("Shell", "BackstopCut", CF((RX0 + RX1) / 2, 274, BZ) * CFrame.Angles(math.rad(45), 0, 0), V3(RX1 - RX0, 2.83, 2.83), P.pier2)
	B.part("Scenery", "TargetRim", CF(54, 261, BZ + 0.05) * CFrame.Angles(0, math.pi / 2, 0), V3(0.1, 26.6, 26.6), P.litEdge, { cyl = true, ghost = true, mat = NEON })
	B.part("Shell", "TargetRecess", CF(54, 261, BZ + 0.15) * CFrame.Angles(0, math.pi / 2, 0), V3(0.3, 25, 25), P.recess, { cyl = true })
	B.put("tv_target", CF(54, 261, BZ + 1.0), { name = "EndTarget", scale = 1.4 })
	B.blk("Shell", "Hood", RX0, RX1, 275.5, 277, -8279, RZ1, P.pier2)
	B.blk("Shell", "HoodFascia", RX0, RX1, 274.2, 277.4, -8278.95, -8280.6, P.pier)
	B.lamp(42, 274.6, -8282, "spot", 40, 1.0, P.lampWhite, { look = V3(54, 261, BZ), angle = 55 })
	B.lamp(66, 274.6, -8282, "spot", 40, 1.0, P.lampWhite, { look = V3(54, 261, BZ), angle = 55 })
end

-- ---------------------------------------------------------------- the movement course
-- the tallest room: ledges up the west wall with jump pads, a gallery along the north wall, an eight-sided tower under
-- a skylight drum, grapple rings hanging from the ceiling beams, the playground's secret bullseye high on the north wall.
-- (18 Nov, more room: a friend found the hub cramped, and the owner: "perhaps in the training hub too the dummies and
-- course section". it is an L now. the same short passage from the muster comes into an entry strip the course's whole
-- width, and the main hall runs north from the strip, 194 long, to the back lot's façade (the yard's side hall lies
-- east of it). the same pieces spread along the longer walls, a second, taller tower at the far end, and grapple rings
-- on the beam crossings from the entrance to the gallery: one long swing run)
local CX0, CX1, CZ0, CZ1, CTOP = -132, -64, -8102, -8296, 288 -- the main hall: west and east walls' faces, south and north, the beams' undersides
local STRIP = { x1 = -30, z1 = -8144 } -- the entry strip: from the west wall to the passage's wall (x), from the south wall to its north wall (z)
local CXM = (CX0 + CX1) / 2 -- -98: the main hall's axis (the start bay, the tower, the skylight, the top)
local GX = {} -- the beams along the hall: on the axis and every 13.6 out, the last two over the strip only
for k = -2, 4 do table.insert(GX, CXM + 13.6 * k) end
local GZ = { -8114, -8130 } -- the beams across: two over the strip, then every 16 down the main hall
for z = -8162, -8274, -16 do table.insert(GZ, z) end
local LEDGES = { -- { name, x0, x1, z0, z1, top }
	{ "Ledge1", CX0, CX0 + 12, CZ0, -8166, 250 },
	{ "Ledge2", CX0, CX0 + 12, -8170, -8230, 260 },
	{ "Ledge3", CX0, CX0 + 12, -8234, CZ1, 270 },
	{ "Gallery", CX0 + 12, -76, -8282, CZ1, 270 },
}
local TOWER = { x = CXM, z = -8178, top = 268 }
local TOWER2 = { x = CXM + 13.6, z = -8258, scale = 1.2 } -- the far tower: the same kit piece a fifth bigger (top 273.6)
local SKY = { x0 = CXM - 13.6, x1 = CXM + 13.6, z0 = -8162, z1 = -8194, top = 306 } -- the skylight drum, on the beam lines round the tower
T.COURSE = { tower = V3(TOWER.x, TOWER.top, TOWER.z) } -- (TrainingLot: gold Carl 3 stands on the tower)
-- the gold dummies' door (17 Nov, the owner, of a dead end: "this should be the locked door connected to the dummies!
-- Since when its unlocked the garage door will open a portal to the floating training area", "its up the ramp on the
-- left side of the training hub"; 18 Nov, the main session: build it into this rebuild where a ramp on the left still
-- leads to it). come from the muster into the course and on your left, in the strip's south wall, a framed opening:
-- a ramp up (rise over ramp) into a corridor that ends on the locked roll-up door (TrainingLot.eggDoor). x = its axis,
-- w = its width inside, ceil = its ceiling, face = the door's face (z)
-- (OFF since the same day, EGG_STRIP: the owner's dead end was the TOP frame on the gallery all along, see TOPD; the
-- corridor stays here, unbuilt, in case it is wanted back)
local EGG_STRIP = false
local EGGC = { x = -44, w = 12, ramp = 16, rise = 4, flat = 12, ceil = 256 }
EGGC.face = CZ0 + 4 + EGGC.ramp + EGGC.flat -- (-8070: from the wall's outside face, up the ramp and along the level)
if EGG_STRIP then
	T.EGG_DOOR = { cf = CFrame.lookAt(V3(EGGC.x, Y0 + EGGC.rise, EGGC.face), V3(EGGC.x, Y0 + EGGC.rise, EGGC.face + 1)), w = 8.4, h = 9.96,
		cw = EGGC.w, ch = EGGC.ceil - Y0 - EGGC.rise, wall = P.wall }
end
-- the gold dummies' door, where the owner meant it (18 Nov, a screenshot of the course's TOP frame on the gallery: "this
-- door is still open bro this is what should lead to the teleporter"; their 17 Nov dead end, "a portal teleporter that
-- takes you to the training area thats in the air", was this frame's dark panel): the frame stands 2.4 further out from
-- the north wall, the locked roll-up door fills its mouth (TrainingLot.eggDoor), and behind it, through the wall, a
-- short room (the frame's own look: warm walls, a dark skirting, the top corners cut, a lit ceiling strip) ends on the
-- portal (TrainingLot's te_portal: a ring with a black middle on a step, no light column) that takes key holders to the
-- playground. x, y = the opening's middle and floor; w, h = the frame's hole (tv_frameWide at 0.75); frame = the
-- frame's pivot (z, its depth's middle; it is 3.6 deep); face = the door's face (0.3 inside the frame's front); back =
-- the room's back wall's face (0.3 off the façade's inside)
local TOPD = { x = CXM, y = 270, w = 12, h = 10.5, frame = CZ1 + 4.2, face = CZ1 + 5.8, back = T.FACE + 0.3, cut = 1.95, jamb = 1.8 }
if not EGG_STRIP then
	T.EGG_DOOR = { cf = CFrame.lookAt(V3(TOPD.x, TOPD.y, TOPD.face), V3(TOPD.x, TOPD.y, TOPD.face - 1)), w = 8.4, h = 8.6,
		cw = TOPD.w, ch = TOPD.h, wall = P.recess, room = TOPD.face - TOPD.back, door = 2.4 }
end
T.TOPD = TOPD
-- the room behind the TOP door: the collar between the frame and the wall, the frame's depth made solid (kit meshes
-- have no collision), the lining, skirting, cut corners, ceiling, floor and back, a lit strip and a lamp
local function topRoom(B, D)
	local TOPD = D or TOPD
	local x0, x1, y0, y1 = TOPD.x - TOPD.w / 2, TOPD.x + TOPD.w / 2, TOPD.y, TOPD.y + TOPD.h
	local oy1 = y1 + TOPD.jamb
	local front, fb = TOPD.frame + 1.8, TOPD.frame - 1.78 -- (the frame's front; its back, 0.02 inside it)
	-- the collar: the frame's section carried back to the wall (the wall's colour: from the gallery, the wall steps out
	-- to meet the frame)
	B.blk("Shell", "TopCollar", x0 - TOPD.jamb, x0, y0, oy1, fb, (TOPD.wall or CZ1), P.courseWall)
	B.blk("Shell", "TopCollar", x1, x1 + TOPD.jamb, y0, oy1, fb, (TOPD.wall or CZ1), P.courseWall)
	B.blk("Shell", "TopCollar", x0, x1, y1, oy1, fb, (TOPD.wall or CZ1), P.courseWall)
	-- the frame itself stops nobody: its jambs and head, unseen and solid, from its front to the collar
	B.solid("TopFrameSolid", CF(x0 - TOPD.jamb / 2, (y0 + oy1) / 2, (front + fb) / 2), V3(TOPD.jamb, oy1 - y0, front - fb))
	B.solid("TopFrameSolid", CF(x1 + TOPD.jamb / 2, (y0 + oy1) / 2, (front + fb) / 2), V3(TOPD.jamb, oy1 - y0, front - fb))
	B.solid("TopFrameSolid", CF(TOPD.x, (y1 + oy1) / 2, (front + fb) / 2), V3(TOPD.w, oy1 - y1, front - fb))
	-- inside: warm lining, a dark skirting, the frame's cut corners carried on, a ceiling, a floor and the back
	for _, sx in { -1, 1 } do
		local wx = TOPD.x + sx * TOPD.w / 2
		B.blk("Shell", "TopLining", wx, wx - sx * 0.3, y0, y1, fb, TOPD.back, P.warmWall)
		B.blk("Shell", "TopDado", wx - sx * 0.3, wx - sx * 0.5, y0, y0 + 1.2, fb, TOPD.back, P.floor2, { ghost = true })
		local c = TOPD.cut
		B.part("Shell", "TopChamfer", CF(wx, y1, (fb + TOPD.back) / 2) * CFrame.Angles(0, 0, math.rad(45)), V3(c * math.sqrt(2), c * math.sqrt(2), fb - TOPD.back), P.warmWall)
	end
	B.blk("Shell", "TopCeiling", x0, x1, y1 - 0.06, y1, fb, TOPD.back, P.ceil)
	B.blk("Shell", "TopFloor", x0 + 0.3, x1 - 0.3, y0, y0 + 0.06, TOPD.face - 2.4, TOPD.back, P.ledge)
	B.blk("Shell", "TopBack", x0, x1, y0, y1, TOPD.back, (TOPD.backTo or T.FACE), P.warmWall) -- (v5: TOPD.wall / TOPD.backTo: a TOP on any wall)
	B.blk("Scenery", "TopLight", x0 + 2.6, x1 - 2.6, y1 - 0.24, y1 - 0.06, fb - 0.6, fb - 3.4, P.panel, { ghost = true, mat = NEON })
	B.lamp(TOPD.x, y1 - 1.2, fb - 2, "point", 14, 0.6, P.warm)
end
local function eggCorridor(B)
	local x0, x1 = EGGC.x - EGGC.w / 2, EGGC.x + EGGC.w / 2
	local zIn, top = CZ0 + 4, Y0 + EGGC.rise -- (the course wall's outside face; the level floor)
	local zUp = zIn + EGGC.ramp
	local zEnd = EGGC.face + 3.2 -- (TrainingLot.EGG_DEPTH: the end wall's face, behind the door)
	B.ramp("Shell", "EggRamp", "z", zIn, Y0, zUp, top, x0, x1, P.floor)
	B.blk("Shell", "EggRampFill", x0, x1, 236, Y0 - 0.5, zIn, zUp, P.floor)
	B.blk("Shell", "EggFloor", x0, x1, 236, top, zUp, zEnd + 4, P.floor)
	for _, sx in { -1, 1 } do
		local wx = EGGC.x + sx * EGGC.w / 2
		B.blk("Shell", "EggWall", wx, wx + sx * 4, 236, EGGC.ceil + 2, zIn - 0.05, zEnd + 4, P.warmWall)
		-- (the owner's shot: warm walls, a dark skirting, the upper corners cut off)
		B.ramp("Shell", "EggDado", "z", zIn, Y0 + 1.2, zUp, top + 1.2, wx, wx - sx * 0.2, P.floor2, { thick = 1.2, ghost = true })
		B.blk("Shell", "EggDado", wx, wx - sx * 0.2, top, top + 1.2, zUp, zEnd, P.floor2, { ghost = true })
		B.part("Shell", "EggChamfer", CF(wx, EGGC.ceil, (zIn + zEnd) / 2) * CFrame.Angles(0, 0, math.rad(45)), V3(2.4, 2.4, zEnd - zIn), P.warmWall)
	end
	B.blk("Shell", "EggCeiling", x0 - 4, x1 + 4, EGGC.ceil, EGGC.ceil + 2, zIn - 0.05, zEnd + 4, P.ceil)
	B.blk("Shell", "EggEnd", x0 - 4, x1 + 4, 236, EGGC.ceil + 2, zEnd, zEnd + 4, P.wall)
	B.blk("Scenery", "EggLight", x0 + 2, x1 - 2, EGGC.ceil - 0.2, EGGC.ceil - 0.02, EGGC.face - 9, EGGC.face - 4, P.panel, { ghost = true, mat = NEON })
	B.lamp(EGGC.x, EGGC.ceil - 1, EGGC.face - 6.5, "point", 18, 0.7, P.lampWhite)
	-- the mouth: the muster's frame, in the course's south wall
	B.put("tv_frameMid", CF(EGGC.x, Y0, CZ0 + 2), { name = "FrameEgg" })
end
local function course(B)
	local SX1, SZ1, W2 = STRIP.x1, STRIP.z1, CTOP + 4
	-- the floor, whole: the strip and the main hall. (the long-jump pit, its slide lane, words, lines and numbers went on
	-- 16 Nov, the owner: "this jumping thing is redundant")
	B.blk("Shell", "CourseFloor", CX0 - 3.95, SX1, 234, Y0, CZ0 + 3.95, SZ1, P.courseFloor)
	B.blk("Shell", "CourseFloor", CX0 - 3.95, CX1, 234, Y0, SZ1, CZ1 - 3.95, P.courseFloor)
	-- walls: the strip's east one with the passage from the muster, its north one (the yard's side hall behind it), the
	-- main hall's east one, west and north
	B.blk("Shell", "CourseWallE", SX1, SX1 + 4, 234, W2, CZ0 + 4, MZ + PASS, P.courseWall)
	B.blk("Shell", "CourseWallE", SX1, SX1 + 4, 234, W2, MZ - PASS, SZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallE", SX1, SX1 + 4, MY + 12, W2, MZ + PASS, MZ - PASS, P.courseWall)
	B.blk("Shell", "CourseWallIn", CX1, SX1 + 4, 234, W2, SZ1, SZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallE", CX1, CX1 + 4, 234, W2, SZ1 - 4, CZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallW", CX0 - 4, CX0, 234, W2, CZ0 + 4, CZ1 - 4, P.courseWall)
	-- (the north wall has the TOP room's hole through it since 18 Nov: TOPD)
	local hx0, hx1, hy0, hy1 = TOPD.x - TOPD.w / 2, TOPD.x + TOPD.w / 2, TOPD.y, TOPD.y + TOPD.h
	B.blk("Shell", "CourseWallN", CX0 - 4, hx0, 234, W2, CZ1, CZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallN", hx1, CX1 + 4, 234, W2, CZ1, CZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallN", hx0, hx1, 234, hy0, CZ1, CZ1 - 4, P.courseWall)
	B.blk("Shell", "CourseWallN", hx0, hx1, hy1, W2, CZ1, CZ1 - 4, P.courseWall)
	-- (rework 5: the south wall, the end of the view from the gallery, opens into a deep lit bay on the main hall's axis,
	-- framed in the ledges' rounded white noses)
	local SB = { x0 = CXM - 13, x1 = CXM + 13, y0 = 246, y1 = 282, back = CZ0 + 8 }
	B.blk("Shell", "CourseWallS", CX0 - 4, SB.x0, 234, W2, CZ0 + 4, CZ0, P.courseWall)
	if EGG_STRIP then
		local ex0, ex1 = EGGC.x - 6.05, EGGC.x + 6.05 -- (the egg corridor's mouth: the frames' 12 x 12 holes, 0.05 bigger all round)
		B.blk("Shell", "CourseWallS", SB.x1, ex0, 234, W2, CZ0 + 4, CZ0, P.courseWall)
		B.blk("Shell", "CourseWallS", ex1, SX1 + 4, 234, W2, CZ0 + 4, CZ0, P.courseWall)
		B.blk("Shell", "CourseWallS", ex0, ex1, Y0 + 12.05, W2, CZ0 + 4, CZ0, P.courseWall)
	else
		B.blk("Shell", "CourseWallS", SB.x1, SX1 + 4, 234, W2, CZ0 + 4, CZ0, P.courseWall)
	end
	B.blk("Shell", "CourseWallS", SB.x0, SB.x1, 234, SB.y0, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "CourseWallS", SB.x0, SB.x1, SB.y1, W2, CZ0 + 4, CZ0, P.courseWall)
	B.blk("Shell", "StartBaySill", SB.x0, SB.x1, 234, SB.y0, SB.back, CZ0 + 4, P.ledge)
	B.blk("Shell", "StartBayBack", SB.x0 - 2, SB.x1 + 2, 234, SB.y1 + 2, SB.back + 1, SB.back, P.ledge)
	B.blk("Shell", "StartBayCheek", SB.x0 - 2, SB.x0, SB.y0, SB.y1 + 2, SB.back, CZ0 + 4, P.courseWall)
	B.blk("Shell", "StartBayCheek", SB.x1, SB.x1 + 2, SB.y0, SB.y1 + 2, SB.back, CZ0 + 4, P.courseWall)
	B.blk("Shell", "StartBayHead", SB.x0, SB.x1, SB.y1, SB.y1 + 2, SB.back, CZ0 + 4, P.ceil)
	B.blk("Shell", "StartBayPanel", SB.x0 + 3, SB.x1 - 3, SB.y0 + 3, SB.y1 - 5, SB.back - 0.05, SB.back - 0.35, P.ledgePanel)
	B.blk("Scenery", "StartBayLight", SB.x0 + 1, SB.x1 - 1, SB.y1 - 0.25, SB.y1, SB.back - 0.2, CZ0 + 3.6, P.litEdge, { ghost = true, mat = NEON })
	B.lamp(CXM, SB.y1 - 3, CZ0 + 5, "point", 22, 0.8, P.lampWhite)
	for _, x in { SB.x0, SB.x1 } do
		B.part("Shell", "StartBayNose", CF(x, (SB.y0 + SB.y1) / 2, CZ0 - 0.1) * CFrame.Angles(0, 0, math.pi / 2), V3(SB.y1 - SB.y0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	end
	for _, y in { SB.y0, SB.y1 } do
		B.part("Shell", "StartBayNose", CF(CXM, y, CZ0 - 0.1), V3(SB.x1 - SB.x0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	end
	for _, w in {
		{ SX1, SX1 - 0.2, CZ0, MZ + PASS }, { SX1, SX1 - 0.2, MZ - PASS, SZ1 }, { CX1, CX1 - 0.2, SZ1, CZ1 },
	} do
		B.blk("Shell", "Dado", w[1], w[2], Y0, Y0 + 1.2, w[3], w[4], P.floor2, { ghost = true })
	end
	-- (the strip's north wall is the first thing you face coming in: two broad steps against it, a place to stand and
	-- watch the course, slate masses with the ledges' white noses on their edges)
	for _, t in { { Y0 + 3, SZ1 + 10 }, { Y0 + 6, SZ1 + 5 } } do
		B.blk("Shell", "WatchStep", CX1 + 0.1, SX1 - 0.1, Y0, t[1], SZ1, t[2], P.ledge)
		B.part("Shell", "Nose", CF((CX1 + SX1) / 2, t[1] - 0.1, t[2] + 0.1), V3(SX1 - CX1 - 0.2, 1.4, 1.4), P.trim, { cyl = true })
		B.blk("Scenery", "EdgeLight", CX1 + 0.1, SX1 - 0.1, t[1] - 1.3, t[1] - 1.0, t[2] + 0.05, t[2] + 0.2, P.litEdge, { ghost = true, mat = NEON })
	end
	-- piers on the beam grid (the ceiling's beams land on them): down the main hall's east wall, and two on the strip's
	-- north wall
	for _, z in GZ do
		if z > SZ1 then continue end
		B.blk("Shell", "Pier", CX1, CX1 - 2.4, Y0, CTOP, z - 1.6, z + 1.6, P.pier)
		B.blk("Shell", "PierBase", CX1, CX1 - 2.65, Y0, Y0 + 1.3, z - 1.85, z + 1.85, P.deep)
	end
	for _, x in GX do
		if x < CX1 then continue end
		B.blk("Shell", "Pier", x - 1.6, x + 1.6, Y0, CTOP, SZ1, SZ1 + 2.4, P.pier)
		B.blk("Shell", "PierBase", x - 1.85, x + 1.85, Y0, Y0 + 1.3, SZ1, SZ1 + 2.65, P.deep)
	end
	-- (rework 5: the beams land on the west wall too: piers from a corbel above head height on ledge 3, so the high
	-- wall over the ledges has the same rhythm as the east one)
	for _, z in GZ do
		B.blk("Shell", "PierW", CX0, CX0 + 2.4, 279, CTOP, z - 1.6, z + 1.6, P.pier)
		B.blk("Shell", "PierWCorbel", CX0, CX0 + 2.8, 277.6, 279, z - 2, z + 2, P.pier2)
	end
	-- the coffered ceiling: beams both ways, lit panels in every other coffer, and over the tower a skylight drum open
	-- to the sky (the beams across it stay, as its bars)
	local cy0, cy1 = CTOP + 4, CTOP + 6
	B.blk("Shell", "CourseCeiling", CX0 - 4, SX1 + 4, cy0, cy1, CZ0 + 4, SZ1, P.ceil)
	B.blk("Shell", "CourseCeiling", CX0 - 4, CX1 + 4, cy0, cy1, SZ1, SKY.z0 - 1.15, P.ceil)
	B.blk("Shell", "CourseCeiling", CX0 - 4, CX1 + 4, cy0, cy1, SKY.z1 + 1.15, CZ1 - 4, P.ceil)
	B.blk("Shell", "CourseCeiling", CX0 - 4, SKY.x0 + 1.15, cy0, cy1, SKY.z0 - 1.15, SKY.z1 + 1.15, P.ceil)
	B.blk("Shell", "CourseCeiling", SKY.x1 - 1.15, CX1 + 4, cy0, cy1, SKY.z0 - 1.15, SKY.z1 + 1.15, P.ceil)
	B.blk("Shell", "CourseCoping", SX1 + 2.6, SX1 + 4.6, cy0 - 1, cy1 + 1.2, CZ0 + 4.4, SZ1 - 4.4, P.wall2, { nq = true })
	B.blk("Shell", "CourseBand", SX1 + 4, SX1 + 4.3, 276, 277, CZ0 + 4, SZ1 - 4, P.trim, { ghost = true })
	for _, z in GZ do B.blk("Shell", "CeilingBeam", CX0, if z > SZ1 then SX1 else CX1, CTOP, CTOP + 4, z - 1.15, z + 1.15, P.pier) end
	for _, x in GX do B.blk("Shell", "CeilingBeam", x - 1.15, x + 1.15, CTOP, CTOP + 4, CZ0, if x < CX1 then CZ1 else SZ1, P.pier) end
	for _, w in {
		{ SKY.x0 - 1.2, SKY.x0 + 1.2, SKY.z0 + 1.2, SKY.z1 - 1.2 }, { SKY.x1 - 1.2, SKY.x1 + 1.2, SKY.z0 + 1.2, SKY.z1 - 1.2 },
		{ SKY.x0 - 1.2, SKY.x1 + 1.2, SKY.z0 + 1.2, SKY.z0 - 1.2 }, { SKY.x0 - 1.2, SKY.x1 + 1.2, SKY.z1 + 1.2, SKY.z1 - 1.2 },
	} do
		B.blk("Shell", "SkyDrum", w[1], w[2], CTOP, SKY.top, w[3], w[4], P.wall2)
	end
	-- (16 Nov, sealing: the drum is open to the sky, so an unseen lid over it: you see out, you cannot grapple out)
	B.solid("SkyLid", CF((SKY.x0 + SKY.x1) / 2, SKY.top + 2, (SKY.z0 + SKY.z1) / 2), V3(SKY.x1 - SKY.x0 + 4, 4, SKY.z0 - SKY.z1 + 4))
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0 + 1.6, SKY.z0 - 1.6, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z1 + 1.6, SKY.z1 - 1.6, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x0 - 1.6, SKY.x0 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0, SKY.z1, P.wall2)
	B.blk("Shell", "SkyCoping", SKY.x1 - 1.6, SKY.x1 + 1.6, SKY.top, SKY.top + 0.6, SKY.z0, SKY.z1, P.wall2)
	-- a lit panel in every other coffer (the coffers' middles: between the beam lines, and the half bays at the walls)
	local xs, zs = {}, {}
	for i = 1, #GX - 1 do table.insert(xs, (GX[i] + GX[i + 1]) / 2) end
	table.insert(xs, (GX[#GX] + SX1) / 2)
	table.insert(zs, (CZ0 + GZ[1]) / 2)
	for i = 1, #GZ - 1 do table.insert(zs, if GZ[i] > SZ1 and GZ[i + 1] < SZ1 then (GZ[i] + SZ1) / 2 else (GZ[i] + GZ[i + 1]) / 2) end
	table.insert(zs, (GZ[#GZ] + CZ1) / 2)
	table.insert(zs, 4, (SZ1 + GZ[3]) / 2) -- (the strip's last bay and the main hall's first meet on the strip's wall)
	for row, z in zs do
		for col, x in xs do
			local inHall = x < CX1 or z > SZ1
			local inSky = x > SKY.x0 and x < SKY.x1 and z < SKY.z0 and z > SKY.z1
			if inHall and not inSky and (row + col) % 2 == 0 then
				B.blk("Scenery", "CoffersPanel", x - 4, x + 4, CTOP + 3.75, CTOP + 3.95, z - 4, z + 4, P.panel, { ghost = true, mat = NEON })
			end
		end
	end
	for i, l in { { -118.4, -8122 }, { -91.2, -8122 }, { -50.4, -8122 }, { -77.6, -8170 }, { -118.4, -8202 }, { -77.6, -8234 }, { -118.4, -8266 }, { CXM, -8285 } } do
		B.lamp(l[1], CTOP + 3.2, l[2], "spot", 62, 1.1, P.lampWhite, { angle = 120, shadows = i == 4 })
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
	-- jump pads: floor to ledge 1 (its arrows to the ledge's wall), ledge 1 to 2, 2 to 3, each 7 short of the ledge's end.
	-- (the one by the tower that threw you onto its top went on 16 Nov, the owner: "the one near the cylinder, is
	-- redundant. the one that lifts you should face toward the wall": the ring over the tower takes your grapple up there)
	B.pad(CX0 + 20, Y0, -8134, V3(-14, 52, 0))
	B.pad(CX0 + 6, 250, LEDGES[1][5] + 7, V3(0, 52, -14))
	B.pad(CX0 + 6, 260, LEDGES[2][5] + 7, V3(0, 52, -14))
	-- the towers: the eight-sided one under the skylight, the bigger one at the far end, off the axis toward the gallery's
	-- end. (the open chute from the tower's top went on 16 Nov, the owner: "what is the slope to the cylinder thingy?")
	B.put("tv_towerOct", CF(TOWER.x, Y0, TOWER.z), { name = "Tower" })
	B.drum("Collision", "TowerSolid", TOWER.x, TOWER.z, Y0, TOWER.top, 16.6, P.pier, { tr = 1, noShadow = true })
	B.put("tv_towerOct", CF(TOWER2.x, Y0, TOWER2.z), { name = "TowerFar", scale = TOWER2.scale })
	B.drum("Collision", "TowerSolid", TOWER2.x, TOWER2.z, Y0, Y0 + (TOWER.top - Y0) * TOWER2.scale, 16.6 * TOWER2.scale, P.pier, { tr = 1, noShadow = true })
	-- the runner (18 Nov, the practice pass): a dummy on a long rail across the main hall between the towers, to shoot
	-- at while you swing over it
	local rn = T.DUMMIES.Runner
	rail(B, rn[1], Y0, rn[3], T.RAILS.Runner[1], { line = true })
	-- grapple rings on the beam crossings: over the strip as you come in, over the tower (from the skylight's bars), down
	-- the hall in a zigzag, over the far tower, and by ledge 3 and the gallery
	for _, h in { { -57.2, -8130 }, { -84.4, -8130 }, { CXM, TOWER.z }, { -111.6, -8210 }, { -84.4, -8226 }, { TOWER2.x, TOWER2.z }, { -111.6, -8274 } } do
		B.put("tv_hoop", CF(h[1], CTOP, h[2]), { name = "GrappleRing" })
	end
	-- the top: a deep frame on the north wall at the gallery's middle, with its word (the course's far end). since 18 Nov
	-- it is the gold dummies' door (TOPD, topRoom; the door itself is TrainingLot's eggDoor, where T.EGG_DOOR says)
	B.put("tv_frameWide", CF(CXM, 270, TOPD.frame), { name = "FrameTop", scale = 0.75 })
	if EGG_STRIP then
		B.blk("Shell", "TopPanel", CXM - 6, CXM + 6, 270, 280.5, CZ1 + 0.05, CZ1 + 0.3, P.recess)
		B.blk("Scenery", "TopLight", CXM - 5, CXM + 5, 279.6, 279.9, CZ1 + 0.3, CZ1 + 1.6, P.warm, { ghost = true, mat = NEON })
		B.lamp(CXM, 278, CZ1 + 3, "point", 16, 0.7, P.warm)
	else
		topRoom(B)
	end
	B.text("WordTOP", { { "TOP", P.amber, "B", 1 } }, 7, 1.5, CF(CXM, 280.9, TOPD.frame + 2.05) * CFrame.Angles(0, math.pi, 0), { plate = P.pier, thick = 0.2 })
	-- the playground's secret: a bullseye high on the north wall over ledge 3. too high to jump to: grapple into it
	-- (the line and arrow from the door to the first pad went on 16 Nov: "an arrow that looks ugly and is redundant")
	local bx, by, bz = CX0 + 6, 283, CZ1 + 0.45 -- (over ledge 3, off the line you see from the entrance)
	B.put("tv_target", CF(bx, by, bz), { name = "SecretBullseye", scale = 0.6 })
	B.trigger("ToPlayground", bx - 3, bx + 3, by - 3, by + 3, CZ1 + 1.2, CZ1 + 4.2)
	local ta = folderIn(B.doors, "TrainingArrive")
	for _, x in { CX0 + 2, CX0 + 6, CX0 + 10 } do
		local p = B.marker(ta, "TrainingArrive", x, 270.1, CZ1 + 6, V3(x, 270, CZ1 + 20))
		p:SetAttribute("Built", "TrainingV2")
	end
	if EGG_STRIP then eggCorridor(B) end
end

-- ---------------------------------------------------------------- the zone, the barrier, the finish
local function bounds(B, withLot)
	local z = T.ZONE
	local lz = T.LOT
	local zp = Instance.new("Part")
	zp.Name = "TrainingZone"; zp.Anchored = true; zp.Transparency = 1; zp.CanCollide = false; zp.CanQuery = false; zp.CanTouch = false
	if withLot then -- one box round the hall and the back lot (and the v4 wing, west of the lot's width)
		local xa, xb = math.min(lz[1] - 2, z[1]), math.max(lz[2] + 2, z[2])
		zp.Size = V3(xb - xa, lz[3] + 4 - z[3], math.abs(lz[4] - 2 - z[5]))
		zp.CFrame = B.cf((xa + xb) / 2, (z[3] + lz[3] + 4) / 2, (z[5] + lz[4] - 2) / 2)
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
local OWNED_DOORS = { "ToHub", "ToPlayground", "TrainingArrive", "LotExit", "EggPortal", "ToParkour", "RangeBack", "RangeDeck" } -- (ToParkour: v4's TOP teleporter; RangeBack/RangeDeck: down-range back onto the deck)
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

-- ---------------------------------------------------------------- the flicker pass (16 Nov)
-- two visible faces of different looks in one plane, facing the same way, flicker as the camera moves (z-fighting:
-- the owner saw it all over the maps). after a build, PolishBackup.ZFight finds every such pair in the training
-- ground and the lot, and one BLOCK of the pair grows ZF_EPS past the other: on tops and sides the block with the
-- smaller face (the ring, the trim, the edge: the detail meant to be seen), on undersides the one with the bigger face
-- (the slab). a block only grows, so no wall, floor or unseen solid gets thinner and the seal stays shut; the one
-- exception is a block meeting a kit mesh's underside, which steps back behind it. pairs of two kit meshes are the
-- kit's (training_models.py, lot_models.py). passes repeat (a grown face can meet a third one) until none is left.
local ZF_EPS = 0.04
local function zfAxis(p: BasePart, n: Vector3)
	local c = p.CFrame
	for _, k in { "X", "Y", "Z" } do
		local ax = if k == "X" then c.RightVector elseif k == "Y" then c.UpVector else -c.LookVector
		local d = ax:Dot(n)
		if math.abs(d) > 0.999 then return k end
	end
	return nil
end
local function zfBlock(p: Instance, n: Vector3): boolean
	return p:IsA("Part") and p.Shape == Enum.PartType.Block and zfAxis(p, n) ~= nil
end
local function zfPlane(p: BasePart, n: Vector3): number -- where p's face that faces n lies, along n
	return n:Dot(p.Position) + p.Size[zfAxis(p, n)] / 2
end
local function zfArea(p: BasePart, n: Vector3): number
	local k, s = zfAxis(p, n), p.Size
	return if k == "X" then s.Y * s.Z elseif k == "Y" then s.X * s.Z else s.X * s.Y
end
function T.dezfight(root: Instance): string
	local src = SS.PolishBackup:FindFirstChild("ZFight")
	if not src then return "flicker pass: no PolishBackup.ZFight" end
	local m = src:Clone(); m.Parent = SS
	local Z = require(m); m:Destroy()
	local first, moved, last, seen = nil, 0, 0, 0
	for pass = 1, 6 do
		Z.start({ root }, {})
		while Z.step(30) ~= "done" do end
		local res = Z.results()
		local vis = 0
		for _, r in res do if not r.covered then vis += 1 end end
		first = first or vis
		last, seen = vis, #res
		local todo = {} -- part -> { [face key] = { n, delta } }
		local function want(p: BasePart, n: Vector3, delta: number)
			if math.abs(delta) > 0.12 then return end -- (a safety: a hit is never more than 0.02 + EPS away)
			local k = zfAxis(p, n)
			local ax = if k == "X" then p.CFrame.RightVector elseif k == "Y" then p.CFrame.UpVector else -p.CFrame.LookVector
			local key = k .. (if ax:Dot(n) > 0 then "+" else "-")
			todo[p] = todo[p] or {}
			local had = todo[p][key]
			if not had or (delta > 0 and delta > had[2]) or (delta < 0 and had[2] < 0 and delta < had[2]) then todo[p][key] = { n, delta } end
		end
		for _, r in res do
			local A, Bp, n = r.A, r.B, r.n
			local under = n.Y < -0.7
			local a, b = zfBlock(A, n), zfBlock(Bp, n)
			if a and b then
				local small, big = A, Bp
				if zfArea(A, n) > zfArea(Bp, n) then small, big = Bp, A end
				local win, other = small, big
				if under then win, other = big, small end
				want(win, n, zfPlane(other, n) - zfPlane(win, n) + ZF_EPS)
			elseif a or b then
				local blk = if a then A else Bp
				local dm = n:Dot(r.pt or r.c)
				want(blk, n, dm - zfPlane(blk, n) + (if under then -ZF_EPS else ZF_EPS))
			end
		end
		local n = 0
		for p, faces in todo do
			for _, f in faces do
				local nn, delta = f[1], f[2]
				local k = zfAxis(p, nn)
				local sz = p.Size[k] + delta
				if sz >= 0.05 then
					local cf = p.CFrame
					p.Size = V3(if k == "X" then sz else p.Size.X, if k == "Y" then sz else p.Size.Y, if k == "Z" then sz else p.Size.Z)
					p.CFrame = cf + nn * (delta / 2)
					n += 1
				end
			end
		end
		moved += n
		if n == 0 then break end
	end
	Z.clear()
	return ("flicker pass (ZFight): %d visible pairs of faces in one plane before, %d after (%d block faces moved; %d pairs left in all, hidden ones and kit meshes)"):format(first or 0, last, moved, seen)
end

-- unseen boxes round the props named in T.HEAD.guard: the prop's box on the plan's axes plus T.HEAD.margin each way,
-- from 3 under it to 8 over it (so nobody jumps onto one), in Collision. they stop bodies and shots like the hall's other
-- solids; the prompts on those props do not need sight
local function headGuards(B): number
	local want = {}
	for _, n in T.HEAD.guard do want[n] = true end
	local n = 0
	for _, d in B.root:GetDescendants() do
		if not want[d.Name] then continue end
		local cf, sz
		if d:IsA("BasePart") then cf, sz = d.CFrame, d.Size elseif d:IsA("Model") then cf, sz = d:GetBoundingBox() else continue end
		local R, U, L = cf.RightVector, cf.UpVector, cf.LookVector
		local h = V3(math.abs(R.X) * sz.X + math.abs(U.X) * sz.Y + math.abs(L.X) * sz.Z,
			math.abs(R.Y) * sz.X + math.abs(U.Y) * sz.Y + math.abs(L.Y) * sz.Z,
			math.abs(R.Z) * sz.X + math.abs(U.Z) * sz.Y + math.abs(L.Z) * sz.Z) / 2
		local m = T.HEAD.margin
		local lo, hi = cf.Position.Y - h.Y - 3, cf.Position.Y + h.Y + 8
		local g = B.boxSrc:Clone()
		g.Name = "HeadGuard"; g:SetAttribute("For", d.Name)
		if T.HEAD.bodiesOnly and T.HEAD.bodiesOnly[d.Name] then g.CanQuery = false end -- (the practice lane's consoles: you shoot over them)
		g.Size = V3(2 * (h.X + m), hi - lo, 2 * (h.Z + m)); g.CFrame = CF(cf.Position.X, (lo + hi) / 2, cf.Position.Z)
		g.Parent = B.root.Collision
		n += 1
	end
	return n
end

-- the v3 rooms (T.ROOMS): their module sets what the rest reads (T.DUMMIES, T.RAILS, T.LANE, T.COURSE, T.GOLD1,
-- T.EGG_DOOR, T.TOPD3) now, before anything builds or checks
local ROOMS3 = nil
-- (20 Nov 2026, the owner: "oh I though training hub would get enrirelyt redone?") "v5" = PolishBackup.TrainingCompound
-- (roblox/studio-tools/TrainingCompound.luau): a new compound on new footprints with its own arrival (OWN_ARRIVAL: no
-- muster); the range (and the shop) as before. vault Hubs/Training redo plan.md
if T.ROOMS == "v5" then
	local src5 = SS:FindFirstChild("PolishBackup") and SS.PolishBackup:FindFirstChild("TrainingCompound")
	if src5 then
		ROOMS3 = require(src5:Clone())
		ROOMS3.apply(T, { Y0 = Y0, MY = MY, MZ = MZ, MTOP = MTOP, NEON = NEON, PASS = PASS, folderIn = folderIn, rail = rail, healPad = healPad, topRoom = topRoom })
	end
end
if T.ROOMS == "v3" or T.ROOMS == "v4" then
	local src = SS:FindFirstChild("PolishBackup") and SS.PolishBackup:FindFirstChild("TrainingRooms")
	local src4 = SS:FindFirstChild("PolishBackup") and SS.PolishBackup:FindFirstChild("TrainingRedo")
	if src and (T.ROOMS == "v3" or src4) then
		ROOMS3 = require(src:Clone())
		if T.ROOMS == "v4" then ROOMS3 = require(src4:Clone()).wrap(ROOMS3) end
		ROOMS3.apply(T, { Y0 = Y0, MY = MY, MZ = MZ, MTOP = MTOP, NEON = NEON, PASS = PASS, folderIn = folderIn, rail = rail, healPad = healPad, topRoom = topRoom })
	end
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
	if (T.ROOMS == "v3" or T.ROOMS == "v4" or T.ROOMS == "v5") and not ROOMS3 then return "STOPPED: T.ROOMS is " .. T.ROOMS .. " but its module (TrainingRooms, TrainingRedo or TrainingCompound) is missing" end
	if not (ROOMS3 and ROOMS3.OWN_ARRIVAL) then muster(B) end
	if ROOMS3 then ROOMS3.build(B) else yard(B) end
	range(B)
	if not ROOMS3 then course(B) end
	-- the back lot (push 10): its own builder, with this build's context
	local lotSrc = SS.PolishBackup:FindFirstChild("TrainingLot")
	local lotNote = ""
	if lotSrc then lotNote = "\n" .. require(lotSrc:Clone()).build(B, T) end
	local guards = headGuards(B)
	lotNote ..= ("\nhead guards: %d"):format(guards)
	bounds(B, lotSrc ~= nil)
	local root = B.root
	root:SetAttribute("Version", T.VERSION); root:SetAttribute("Push", T.PUSH)
	for _, p in root:GetDescendants() do if p:IsA("BasePart") then p.Anchored = true end end
	local home
	if live then
		home = hub
		setLook(if T.ROOMS == "v5" then "v5" else "v2") -- (v5 has its own late-afternoon look: HubLook.looks.training_v5)
	else
		home = Instance.new("Folder"); home.Name = "TrainingStage"; home.Parent = workspace.Map
	end
	-- (into the place in pieces: one write of the whole build can stall Studio)
	local kids = root:GetChildren()
	for _, f in kids do f.Parent = nil end
	root.Parent = home
	for _, f in kids do f.Parent = root; task.wait() end
	local zfNote = "\n" .. T.dezfight(root)
	local parts = 0
	for _, p in root:GetDescendants() do if p:IsA("BasePart") then parts += 1 end end
	local miss = {}
	for k, n in B.missing do table.insert(miss, k .. " x" .. n) end
	return ("training v2 built %s: %d things, %d parts, %d lamps, %d with shadows%s%s"):format(if live then "LIVE" else "as a staging copy at x +" .. T.STAGE.X,
		#root:GetDescendants(), parts, B.lamps, B.shadows, if #miss > 0 then "  MISSING: " .. table.concat(miss, ", ") else "", lotNote .. zfNote)
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
-- head room: from every spot on the hall's floors (`step` apart) where your body fits, nothing you can see at head height
-- comes within T.HEAD.near of your eye. what counts: a prop whose top or underside is about your eye's height, a thing
-- on a wall at head height, anything you could walk your head into. what does not: a wall or post from your waist to over
-- your head (it stops your body first), and a table or counter you look down on (its top more than 0.4 under your eye)
function T.headRoom(stage, step): (string, number)
	local H = T.HEAD
	local O = if stage then T.STAGE else Vector3.zero
	local base = if stage then workspace.Map:FindFirstChild("TrainingStage") else hub
	local tg = base and base:FindFirstChild("TrainingGround")
	if not tg then return "head room: no TrainingGround", -1 end
	step = step or 0.5
	-- (parts you can see but not shoot are read too, and put back after)
	local was, wasGroup = {}, {}
	for _, d in tg:GetDescendants() do
		if d:IsA("BasePart") and not d.CanQuery and (d.Transparency < 0.95 or (d.CanCollide and d.CollisionGroup == (T.RANGE_WALL_GROUP or "JFRayBlind"))) then
			was[d] = true; d.CanQuery = true
			-- (a bodies-only guard's group meets the players' groups, not the probe's Default: in Default for the check)
			if d.CollisionGroup ~= "Default" then wasGroup[d] = d.CollisionGroup; d.CollisionGroup = "Default" end
		end
	end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { tg }; rp.RespectCanCollide = true
	local fit = OverlapParams.new(); fit.FilterType = Enum.RaycastFilterType.Include; fit.FilterDescendantsInstances = { tg }; fit.RespectCanCollide = true
	local see = OverlapParams.new(); see.FilterType = Enum.RaycastFilterType.Include; see.FilterDescendantsInstances = { tg }
	local body = Instance.new("Part")
	body.Name = "HeadRoomProbe"; body.Anchored = true; body.CanCollide = false; body.CanQuery = false; body.CanTouch = false; body.Transparency = 1
	body.Size = H.body; body.Parent = workspace
	local ball = body:Clone(); ball.Shape = Enum.PartType.Ball; ball.Size = V3(2, 2, 2) * H.near; ball.Parent = workspace
	local tight = body:Clone(); tight.Shape = Enum.PartType.Ball; tight.Size = V3(1.2, 1.2, 1.2); tight.Parent = workspace
	local lot = tg:FindFirstChild("Lot")
	local Z = T.ZONE
	local spots, found, order = 0, {}, {}
	local walkOn = {} -- (the parts someone stands on: T.floorGaps reads them)
	T.walkOn = walkOn
	-- (a kit model counts whole: a cover wall's cap is part of the wall)
	local span = {}
	local function spanOf(p)
		local m = p:FindFirstAncestorOfClass("Model")
		local o = if m and m:IsDescendantOf(tg) then m else p
		local r = span[o]
		if not r then
			local c, sz
			if o:IsA("Model") then c, sz = o:GetBoundingBox() else c, sz = o.CFrame, o.Size end
			local hy = (math.abs(c.RightVector.Y) * sz.X + math.abs(c.UpVector.Y) * sz.Y + math.abs(c.LookVector.Y) * sz.Z) / 2
			r = { c.Position.Y - O.Y - hy, c.Position.Y - O.Y + hy }
			span[o] = r
		end
		return r[1], r[2]
	end
	local ok, err = pcall(function()
		for x = Z[1] + 1, Z[2] - 1, step do
			for z = T.FACE + 1, Z[5] - 1, step do
				local y = Z[4]
				for _ = 1, 5 do
					local h = workspace:Raycast(V3(x, y, z) + O, V3(0, Z[3] - y, 0), rp)
					if not h then break end
					y = h.Position.Y - O.Y - 0.05
					if h.Normal.Y < 0.7 then continue end
					local f = h.Position.Y - O.Y
					if f > Y0 + 14 then continue end -- (up in the vaults: lamp tops nobody stands on)
					if not workspace:Raycast(V3(x, f + 0.5, z) + O, V3(0, 120, 0), rp) then continue end -- (a roof: outside)
					body.CFrame = CF(V3(x, f + 2 + H.body.Y / 2, z) + O)
					if #workspace:GetPartsInPart(body, fit) > 0 then continue end
					spots += 1
					walkOn[h.Instance] = true
					local eye = V3(x, f + H.eye, z) + O
					ball.CFrame = CF(eye)
					local hits = workspace:GetPartsInPart(ball, see)
					if #hits == 0 then continue end
					local close = nil
					for _, p in hits do
						if p.Transparency >= 0.95 or (lot and p:IsDescendantOf(lot)) then continue end
						local lo, hi = spanOf(p)
						if lo <= f + 2.3 and hi >= f + H.eye + 0.15 then continue end -- (a wall: waist to over your eye; you see its face)
						if hi < f + H.eye - 0.4 then continue end -- (under your eye: you look down on it)
						-- (a thin sign or panel flat on a wall you walk into: the wall stops you, the same as the wall)
						local sz = p.Size
						local thin = math.min(sz.X, sz.Y, sz.Z)
						if thin <= 0.4 then
							local ax = if sz.X == thin then p.CFrame.RightVector elseif sz.Y == thin then p.CFrame.UpVector else p.CFrame.LookVector
							local onWall = false
							for _, sg in { 1, -1 } do
								local w = workspace:Raycast(p.Position, ax * sg * (thin / 2 + 0.6), rp)
								if w and w.Instance ~= p then
									local wl, wh = spanOf(w.Instance)
									if wl <= f + 2.3 and wh >= f + H.eye + 0.15 then onWall = true end
								end
							end
							if onWall then continue end
						end
						if close == nil then
							tight.CFrame = CF(eye)
							close = {}
							for _, q in workspace:GetPartsInPart(tight, see) do close[q] = true end
						end
						local key = p.Parent.Name .. "/" .. p.Name
						local r = found[key]
						if not r then r = { n = 0, min = H.near }; found[key] = r; table.insert(order, key) end
						r.n += 1
						local d = if close[p] then 0.6 else H.near
						if d < r.min or not r.at then r.min = d; r.at = eye - O; r.f = f; r.lo = lo - f; r.hi = hi - f; r.ghost = not p.CanCollide end
					end
				end
			end
		end
	end)
	body:Destroy(); ball:Destroy(); tight:Destroy()
	for d in was do d.CanQuery = false end
	for d, g in wasGroup do d.CollisionGroup = g end
	if not ok then return "head room: FAILED " .. tostring(err), -1 end
	local out = {}
	table.sort(order, function(a, b) return found[a].min < found[b].min or (found[a].min == found[b].min and found[a].n > found[b].n) end)
	local tooNear = 0
	for i, key in order do
		local r = found[key]
		if r.min < 0.61 then tooNear += 1 end
		if i <= 30 then
			table.insert(out, ("HEAD HEIGHT %s: your eye within %.1f at (%.1f, %.1f, %.1f), floor %.1f, it spans %.1f..%.1f over it%s (%d spots)"):format(
				key, r.min, r.at.X, r.at.Y, r.at.Z, r.f, r.lo, r.hi, if r.ghost then ", walk-through" else "", r.n))
		end
	end
	local guards = 0
	for _, d in tg:GetDescendants() do if d.Name == "HeadGuard" then guards += 1 end end
	table.insert(out, 1, ("head room: %d spots to stand on (%.1f apart); things at head height within %.1f of your eye %d (within 0.6: %d); guards %d"):format(
		spots, step, H.near, #order, tooNear, guards))
	return table.concat(out, "\n"), #order
end

-- (21 Nov 2026, the owner in v5: "a gap in the floor by it", "another gap leading to the training rooms", "a gap to the
-- range": every wing's floor stopped at the hall wall's inner face, so each doorway through a 4-stud wall had none)
-- floor continuity: any two floors someone stands on (T.walkOn, from T.headRoom) that are upright blocks with their tops
-- level (within 0.05) and face each other across a strip 0.05..6 studs wide are tested in 0.5-stud slices along it:
-- a slice with nothing solid in it at floor level is a hole you can see or fall into. (wider strips are jumps by design)
function T.floorGaps(stage): string
	local O = if stage then T.STAGE else Vector3.zero
	local walk = T.walkOn
	if not walk then return "floor gaps: run T.headRoom first" end
	local floors = {}
	for p in walk do
		if p:IsA("Part") and p.Shape == Enum.PartType.Block and math.abs(p.CFrame.UpVector.Y) > 0.999 then
			local cf, sz = p.CFrame, p.Size
			local R, L = cf.RightVector, cf.LookVector
			local hx = (math.abs(R.X) * sz.X + math.abs(L.X) * sz.Z) / 2
			local hz = (math.abs(R.Z) * sz.X + math.abs(L.Z) * sz.Z) / 2
			-- (a floor is at least 4 x 4: panel frames, benches and prop boxes are not routes)
			if hx >= 2 and hz >= 2 then table.insert(floors, { x0 = cf.X - hx, x1 = cf.X + hx, z0 = cf.Z - hz, z1 = cf.Z + hz, top = cf.Y + sz.Y / 2, p = p }) end
		end
	end
	local base = if stage then workspace.Map:FindFirstChild("TrainingStage") else hub
	local tg = base and base:FindFirstChild("TrainingGround")
	if not tg then return "floor gaps: no TrainingGround" end
	local op = OverlapParams.new(); op.RespectCanCollide = true
	op.FilterType = Enum.RaycastFilterType.Include; op.FilterDescendantsInstances = { tg }
	local rp = RaycastParams.new(); rp.RespectCanCollide = true
	rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { tg }
	local holes, list = 0, {}
	local function strip(a, b, along, c0, c1, top, fa, fb)
		-- (a..b across the strip, c0..c1 along it; along = "x" when the strip runs along x)
		local w = b - a
		local seen = false
		local c = c0
		while c < c1 - 0.01 do
			local cn = math.min(c + 0.5, c1)
			local mid = (c + cn) / 2
			local pos = if along == "x" then Vector3.new(mid, top - 0.15, (a + b) / 2) else Vector3.new((a + b) / 2, top - 0.15, mid)
			local size = if along == "x" then Vector3.new(math.max(cn - c - 0.04, 0.05), 0.26, math.max(w - 0.02, 0.02)) else Vector3.new(math.max(w - 0.02, 0.02), 0.26, math.max(cn - c - 0.04, 0.05))
			-- (open at floor level, and a real drop under it: between two benches the floor is 2 below, not a hole)
			if #workspace:GetPartBoundsInBox(CFrame.new(pos), size, op) == 0
				and not workspace:Raycast(Vector3.new(pos.X, top + 0.05, pos.Z), Vector3.new(0, -3, 0), rp) then
				holes += 1
				if not seen and #list < 20 then
					seen = true
					table.insert(list, ("FLOOR GAP %.2f wide at (%.1f, %.1f, %.1f) between %s and %s"):format(w, pos.X - O.X, top - O.Y, pos.Z - O.Z, fa.p.Name, fb.p.Name))
				end
			end
			c = cn
		end
	end
	for i, A in floors do
		for j = i + 1, #floors do
			local Bf = floors[j]
			if math.abs(A.top - Bf.top) <= 0.05 then
				-- across x (A west of B, or B west of A), along z
				local z0, z1 = math.max(A.z0, Bf.z0), math.min(A.z1, Bf.z1)
				if z1 - z0 >= 0.5 then
					local g1, g2 = Bf.x0 - A.x1, A.x0 - Bf.x1
					if g1 > 0.05 and g1 <= 6 then strip(A.x1, Bf.x0, "z", z0, z1, A.top, A, Bf) end
					if g2 > 0.05 and g2 <= 6 then strip(Bf.x1, A.x0, "z", z0, z1, A.top, Bf, A) end
				end
				local x0, x1 = math.max(A.x0, Bf.x0), math.min(A.x1, Bf.x1)
				if x1 - x0 >= 0.5 then
					local g1, g2 = Bf.z0 - A.z1, A.z0 - Bf.z1
					if g1 > 0.05 and g1 <= 6 then strip(A.z1, Bf.z0, "x", x0, x1, A.top, A, Bf) end
					if g2 > 0.05 and g2 <= 6 then strip(Bf.z1, A.z0, "x", x0, x1, A.top, Bf, A) end
				end
			end
		end
	end
	table.insert(list, 1, ("floor gaps between level floors you stand on (strips 0.05..6 wide, 0.5 slices): %d open slices, %d floors"):format(holes, #floors))
	return table.concat(list, "\n")
end

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
	for _, n in OWNED_DOORS do
		if n ~= "LotExit" and (n ~= "EggPortal" or T.EGG_DOOR) then need(doors:FindFirstChild(n), "Doors." .. n) end -- (LotExit: gone since the walk-out; kept in the list so a rebuild clears an old one)
	end
	local r = tg:FindFirstChild("Range")
	need(r and r:FindFirstChild("Plates") and #r.Plates:GetChildren() == 3, "Range.Plates (3)")
	need(r and r:FindFirstChild("Spots") and #r.Spots:GetChildren() >= 10, "Range.Spots")
	local gui = r and r:FindFirstChild("Board") and r.Board:FindFirstChild("Gui")
	for _, n in { "RowEasy", "RowMedium", "RowHard", "Line" } do need(gui and gui:FindFirstChild(n), "Board.Gui." .. n) end
	local lf = tg:FindFirstChild("LiveFire")
	if not T.NO_LIVE then need(lf and lf:FindFirstChild("Zone") and lf:FindFirstChild("LiveButton") and lf.LiveButton:FindFirstChild("Prompt"), "LiveFire (Zone, LiveButton.Prompt)") end
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
	-- the shooters stand inside the live-fire end and fire only there
	if not T.NO_LIVE then
		local zp = lf.Zone
		local function inLive(p) local rel = zp.CFrame:PointToObjectSpace(p); local h = zp.Size / 2; return math.abs(rel.X) <= h.X and math.abs(rel.Z) <= h.Z end
		table.insert(out, ("shooters inside the live-fire end: %d of 2"):format((if inLive(ds.Plinker.Position) then 1 else 0) + (if ds:FindFirstChild("Plinker2") and inLive(ds.Plinker2.Position) then 1 else 0)))
	else
		table.insert(out, "no live-fire end (T.NO_LIVE): live fire " .. tostring(lf ~= nil) .. ", shooters' spots " .. tostring(ds:FindFirstChild("Plinker") ~= nil))
	end
	local blocked, lines = 0, 0
	for _, pl in r.Plates:GetChildren() do
		local eye = pl.Position + V3(0, 4.9, 0)
		for _, s in r.Spots:GetChildren() do
			if s:GetAttribute("Lane") ~= pl.Name then continue end
			lines += 1
			local okC = clear(eye, s.Position + V3(0, 3.6, 0))
			local okH = clear(eye, s.Position + V3(0, 6.2, 0))
			if not okC and not okH then blocked += 1; table.insert(out, ("Carl hidden from %s at (%.0f, %.0f, %.0f)"):format(pl.Name, s.Position.X - O.X, s.Position.Y, s.Position.Z)) end
		end
	end
	table.insert(out, ("plate-to-Carl sight lines blocked (each plate to its own lane): %d of %d"):format(blocked, lines))
	local tl = T.TESTLINE or V3(-16, 245, -8150) -- (v5 moves the gun sessions' spot: T.TESTLINE)
	local gunOk = clear(tl + O, ds.Stand1.Position + V3(0, 4, 0))
	table.insert(out, ("gun sessions' test line (%.0f, %.0f, %.0f) to Stand1: "):format(tl.X, tl.Y, tl.Z) .. (if gunOk then "clear" else "BLOCKED"))
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
	-- the hall is sealed (owner, 16 Nov: "there is a roof in the dummy part ... that lets you clip through it and get
	-- outside"). from points inside every room, a ray each way (26) must meet something you cannot walk through
	-- (CanCollide) within 300 studs, like the hub's leak test, and what it meets must be at least 2 studs thick there:
	-- a fast player (grapple, pads) goes through thin skins
	local cp = RaycastParams.new(); cp.FilterType = Enum.RaycastFilterType.Include; cp.FilterDescendantsInstances = { tg }; cp.RespectCanCollide = true
	local S5 = sideFrame(nil, 5)
	local pts = if ROOMS3 and ROOMS3.OWN_ARRIVAL then {} else {
		V3(0, MY + 4, MZ), V3(0, MY + 14, MZ), V3(0, MY + 26, MZ), V3(12, MY + 4, MZ + 8), V3(-12, MY + 12, MZ - 8),
		S5:PointToWorldSpace(V3(0, MY + 4, -(A + WALL + 3))), V3(26, MY + 4, MZ), V3(-26, MY + 4, MZ),
	}
	for _, q in {
		V3(54, DECK + 4, -8125), V3(54, DECK + 14, -8125), V3(54, Y0 + 4, -8170), V3(40, 252, -8270), V3(68, 266, -8240),
		V3(72, 238, -8295), V3(48, 230, -8275), V3(70, 230, -8270), -- (the stairwell's foot and the basement; rays from the stairs' top would go out the door onto the lot)
		V3(33, 230, -8277), V3(33, 242, -8296), V3(44, 252, -8291), -- (the walk-out: its landing, the turn in the bank, the corridor)
	} do table.insert(pts, q) end
	local v2pts = {
		V3(-58, Y0 + 4, -8120), V3(CXM, Y0 + 4, -8120), V3(-80, 274, -8225), V3(CXM, 286, TOWER.z), V3(-50, 280, -8130),
		V3(-90, Y0 + 4, -8240), V3(CX0 + 6, 274, CZ1 + 6), V3(-100, 282, CZ1 + 8), V3(-70, 270, -8200), V3(CX0 + 30, 285, -8125),
		V3(TOWER2.x, Y0 + 40, TOWER2.z), if EGG_STRIP then V3(EGGC.x, Y0 + 3, CZ0 + 8) else V3(TOPD.x, TOPD.y + 4, TOPD.back + 4), -- (the course since 18 Nov: the strip, the main hall, over ledge 3, the gallery, the far tower; the TOP room)
		if EGG_STRIP then V3(EGGC.x, Y0 + 9, EGGC.face - 6) else V3(TOPD.x, TOPD.y + 8, TOPD.back + 2),
		V3(AISLE.x, Y0 + 4, -8160), V3(AISLE.x, AISLE.ceil - 4, -8200), V3(AISLE.x, Y0 + 4, -8250), V3(AISLE.x1 + 1, 250, -8186), -- (the yard's side hall, and in an opening of its arcade)
	}
	for _, q in (if ROOMS3 and ROOMS3.SEAL then ROOMS3.SEAL else v2pts) do table.insert(pts, q) end
	if not (ROOMS3 and ROOMS3.OWN_ARRIVAL) then
		for _, z in { -8154, -8186, -8218, -8250 } do
			for _, x in { -16, 0, 16 } do for _, y in { Y0 + 4, 252, 262 } do table.insert(pts, V3(x, y, z)) end end
		end
	end
	local leaks, rays, thin = 0, 0, {}
	for _, at in pts do
		for x = -1, 1 do for y = -1, 1 do for z = -1, 1 do
			if x == 0 and y == 0 and z == 0 then continue end
			rays += 1
			local h = workspace:Raycast(at + O, V3(x, y, z).Unit * 600, cp) -- (600 since v4: the wing's corridor runs 300+ in a line from the muster)
			if not h then
				leaks += 1
				if leaks <= 12 then table.insert(out, ("LEAK from (%.0f, %.0f, %.0f) toward (%d, %d, %d)"):format(at.X, at.Y, at.Z, x, y, z)) end
			elseif h.Instance:IsA("Part") and (h.Instance :: Part).Shape == Enum.PartType.Block then
				local p = h.Instance :: Part
				local n = p.CFrame:VectorToObjectSpace(h.Normal)
				local t = if math.abs(n.X) > 0.7 then p.Size.X elseif math.abs(n.Y) > 0.7 then p.Size.Y elseif math.abs(n.Z) > 0.7 then p.Size.Z else math.min(p.Size.X, p.Size.Y, p.Size.Z)
				-- (thin only matters where it is the last thing: past it, nothing)
				if t < 1.9 and not workspace:Raycast(h.Position + V3(x, y, z).Unit * 0.02, V3(x, y, z).Unit * 600, cp) then thin[p:GetFullName()] = t end
			end
		end end end
	end
	local nThin = 0
	for name, t in thin do nThin += 1; if nThin <= 12 then table.insert(out, ("THIN %.2f: %s"):format(t, name)) end end
	table.insert(out, ("the hall sealed: %d rays from %d points, leaks %d, skins under 2 studs %d"):format(rays, #pts, leaks, nThin))
	table.insert(out, (T.headRoom(stage)))
	table.insert(out, (T.floorGaps(stage)))
	local lotSrc = SS.PolishBackup:FindFirstChild("TrainingLot")
	if lotSrc and tg:FindFirstChild("Lot") then
		for _, l in require(lotSrc:Clone()).check(tg, mk, T, O) do table.insert(out, l) end
	end
	return table.concat(out, "\n")
end

return T
