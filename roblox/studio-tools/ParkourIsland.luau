--!nocheck
-- THE PARKOUR ISLAND (20 Nov 2026, the training redo: the owner, "course outside teleporter to parkour"). Reached from
-- training's TOP gallery through a green teleporter (Doors.ToParkour, TrainingRedo), open to everyone (the gold Carls'
-- secret playground stays the egg door's). Built for the moves the game really has (Move.client: sprint, slide, slide
-- jump, bhop, the grapple and its jump; there is no wall-run), a loop of five stations with a checkpoint after each:
--   1 SPRINT GAPS   four blocks, gaps 8 to 14, each 2 higher (a sprint jump carries ~31)
--   2 SLIDE         a strip with three bars at 3.4 to slide under, then a 34 gap: only a slide jump clears it
--   3 BHOP STONES   six small stones 18 apart: land and jump to keep the speed
--   4 GRAPPLE SWING a 100 gap with two tall pillars either side of the line to swing from
--   5 CLIMB         a tower up to 70: grapple up its face (ledges on the way), the FINISH on top
-- Parkour.server runs it (the clock from leaving the start, splits at the checkpoints, a fall puts you on your last
-- one, the finish, today's best); LaserDoors moves you in and out (Doors.ParkourArrive, Doors.FromParkour,
-- Doors.ParkourAgain: plain Land doors). Its zone (Hub.ParkourZone) counts as the playground's (Matches.zoneOf): any
-- weapon, its own look. ZoneCull draws it only near it.
--   local P = require(ServerStorage.PolishBackup.ParkourIsland:Clone())
--   P.build()  P.check()  P.remove()
local P = {}
local V3, CF = Vector3.new, CFrame.new
local SP, NEON, CONC = Enum.Material.SmoothPlastic, Enum.Material.Neon, Enum.Material.Concrete

P.SITE = V3(1400, 300, -8400) -- the start deck's top middle (checked free: nothing within the island's box)
P.FALL = 50                   -- this far under the site: back on your last checkpoint
P.ZONE = { -60, 360, -120, 130, -40, 290 } -- x0, x1, y0, y1, z0, z1 (local)
P.PORTAL_KIT = "te_portal"
P.LEG = -110 -- how far down the columns under the decks go (local)   -- the egg door's ring (TrainingLot imports it into JankfireMeshes)

-- the paint (TrainingV2's family): quiet masses, pale tops, one accent on the checkpoints and lines
local C = { mass = "a9a59e", side = "8f9299", top = "d8d3ca", trim = "e2ded5", dark = "5a5f69", accent = "8fd8cf", green = "3ddc84", core = "1c7a44" }

-- the plan, local: x right, z forward (into the course: world -z), y up from the site
P.START = { x0 = -20, x1 = 20, z0 = -15, z1 = 15, top = 0 }
P.GAPS = { { -6, 28, 2 }, { 6, 48, 4 }, { -6, 70, 6 }, { 6, 94, 8 } } -- block centres x, z, top (10 x 10)
P.CPS = {
	{ name = "CP1", x0 = -12, x1 = 12, z0 = 110, z1 = 128, top = 8 },
	{ name = "CP2", x0 = -12, x1 = 12, z0 = 230, z1 = 250, top = 8 },
	{ name = "CP3", x0 = 136, x1 = 160, z0 = 228, z1 = 252, top = 8 },
	{ name = "CP4", x0 = 260, x1 = 284, z0 = 228, z1 = 252, top = 8 },
}
P.STRIP = { x0 = -6, x1 = 6, z0 = 128, z1 = 196, top = 8, bars = { 142, 158, 174 }, bar = 3.4 }
P.STONES = { 30, 48, 66, 84, 102, 120 } -- x, at z 240, 6 x 6, top 8
P.PILLARS = { { 190, 214 }, { 222, 266 } } -- x, z: 8 x 8 from -40 to 52
P.TOWER = { x0 = 292, x1 = 318, z0 = 228, z1 = 252, top = 70, ledges = { { 22, "w" }, { 38, "e" }, { 54, "w" } } }

local root, doorsF
local count = 0
local function W(x, y, z) return P.SITE + V3(x, y, -z) end
local function blk(parent, name, x0, x1, y0, y1, z0, z1, hex, o)
	o = o or {}
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true; p.CanTouch = false
	p.Size = V3(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(z1 - z0), 0.05))
	p.CFrame = CF(W((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
	p.Color = Color3.fromHex(hex); p.Material = o.mat or SP
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	if o.ghost then p.CanCollide = false; p.CanQuery = false; p.CastShadow = false end
	if p.Material == NEON then p.CastShadow = false end
	p.Parent = parent
	count += 1
	return p
end
-- a block you stand on: a concrete mass, a pale top slab, the white nose round its top edge
local function deck(name, x0, x1, z0, z1, top, depth)
	local m = Instance.new("Model")
	m.Name = name
	blk(m, "Mass", x0, x1, top - depth, top - 0.6, z0, z1, C.mass, { mat = CONC })
	-- a column under it down into the haze (a structure standing in the sky, not tiles floating), set in from the edges
	local w, d = math.abs(x1 - x0), math.abs(z1 - z0)
	local cw, cd = math.max(2.5, w * 0.45), math.max(2.5, d * 0.45)
	local cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
	blk(m, "Column", cx - cw / 2, cx + cw / 2, P.LEG, top - depth, cz - cd / 2, cz + cd / 2, C.side, { mat = CONC })
	blk(m, "ColumnCap", cx - cw / 2 - 0.6, cx + cw / 2 + 0.6, top - depth - 1.2, top - depth, cz - cd / 2 - 0.6, cz + cd / 2 + 0.6, C.dark)
	blk(m, "Top", x0, x1, top - 0.6, top, z0, z1, C.top)
	for _, e in { { x0, x1, z0, z0 }, { x0, x1, z1, z1 } } do
		local p = Instance.new("Part")
		p.Name = "Nose"; p.Anchored = true; p.CanTouch = false; p.Shape = Enum.PartType.Cylinder
		p.Size = V3(math.abs(x1 - x0), 0.9, 0.9); p.CFrame = CF(W((x0 + x1) / 2, top - 0.3, e[3]))
		p.Color = Color3.fromHex(C.trim); p.Material = SP
		p.Parent = m
		count += 1
	end
	for _, x in { x0, x1 } do
		local p = Instance.new("Part")
		p.Name = "Nose"; p.Anchored = true; p.CanTouch = false; p.Shape = Enum.PartType.Cylinder
		p.Size = V3(math.abs(z1 - z0), 0.9, 0.9); p.CFrame = CF(W(x, top - 0.3, (z0 + z1) / 2)) * CFrame.Angles(0, math.pi / 2, 0)
		p.Color = Color3.fromHex(C.trim); p.Material = SP
		p.Parent = m
		count += 1
	end
	m.Parent = root.Course
	return m
end
local function zone(name, x0, x1, y0, y1, z0, z1, attrs)
	local p = blk(root.Game, name, x0, x1, y0, y1, z0, z1, C.accent, { ghost = true })
	p.Transparency = 1
	for k, v in attrs or {} do p:SetAttribute(k, v) end
	return p
end
local function marker(parent, name, x, y, z)
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.Size = V3(2, 0.2, 2); p.Transparency = 1
	p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	local at = W(x, y, z)
	p.CFrame = CFrame.lookAt(at, at + V3(0, 0, -1)) -- (facing into the course)
	p.Parent = parent
	return p
end
-- a green ring (the egg door's, recoloured as its green one) standing at x, z on a top. face = the local z way it faces
-- (+1: into the course, -1: back toward the start); its trigger runs 4.5 behind it (LaserDoors looks every 0.1 s: a
-- trigger must be deep enough to be inside of at a run)
local function portal(name, x, z, top, face, say)
	local lib = game:GetService("ServerStorage"):FindFirstChild("JankfireMeshes")
	local t = lib and lib:FindFirstChild(P.PORTAL_KIT)
	local at = W(x, top, z)
	local look = CFrame.lookAt(at, at + V3(0, 0, -face)) -- (local +z is world -z)
	if t then
		local m = t:Clone()
		m.Name = name .. "Ring"
		m:PivotTo(look)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
				-- (the kit's pieces carry their colour in their names: the black middle, the amber line)
				if string.match(d.Name, "_17181c$") then d.Color = Color3.fromHex(C.core); d.Material = NEON
				elseif string.match(d.Name, "_f0a53a$") then d.Color = Color3.fromHex(C.green); d.Material = NEON
				elseif d.Material ~= NEON then d.Material = SP end
			end
		end
		m.Parent = root.Scenery
	else
		-- (no kit here: a plain chunky frame)
		blk(root.Scenery, name .. "Frame", x - 4, x + 4, top, top + 9, z - 0.6, z + 0.6, C.side)
		blk(root.Scenery, name .. "Core", x - 3, x + 3, top + 0.8, top + 8, z - 0.3, z + 0.3, C.core, { ghost = true, mat = NEON })
	end
	local l = Instance.new("PointLight")
	l.Color = Color3.fromHex(C.green); l.Range = 14; l.Brightness = 1.2
	local lp = blk(root.Scenery, name .. "Light", x - 0.3, x + 0.3, top + 4, top + 4.6, z + 1, z + 1.6, C.green, { ghost = true })
	lp.Transparency = 1
	l.Parent = lp
	local trig = blk(doorsF, name, x - 3, x + 3, top, top + 8, z + face * 0.6, z - face * 4.5, C.green, { ghost = true })
	trig.Transparency = 1
	trig:SetAttribute("Land", say.land)
	trig:SetAttribute("Say", say.text)
	trig:SetAttribute("Built", "ParkourIsland")
	return trig
end

-- ------------------------------------------------------------------ build
function P.remove()
	local hub = workspace.Map.Hub
	local old = hub:FindFirstChild("Parkour")
	if old then old:Destroy() end
	local z = hub:FindFirstChild("ParkourZone")
	if z then z:Destroy() end
	for _, d in hub.Doors:GetChildren() do
		if d:GetAttribute("Built") == "ParkourIsland" then d:Destroy() end
	end
	return "parkour removed"
end

function P.build(): string
	P.remove()
	count = 0
	local hub = workspace.Map.Hub
	root = Instance.new("Folder")
	root.Name = "Parkour"
	for _, n in { "Course", "Scenery", "Game" } do
		local f = Instance.new("Folder"); f.Name = n; f.Parent = root
	end
	doorsF = hub.Doors
	local S = P.START
	-- the start deck: the way back, the board, the arrival marks, the line
	deck("StartDeck", S.x0, S.x1, S.z0, S.z1, S.top, 10)
	blk(root.Course, "StartLine", S.x0 + 1, S.x1 - 1, S.top, S.top + 0.08, S.z1 - 1.4, S.z1 - 0.8, C.accent, { ghost = true, mat = NEON })
	portal("FromParkour", -12, -10, S.top, 1, { land = "TrainingArrive", text = "BACK TO TRAINING" })
	local arr = Instance.new("Folder"); arr.Name = "ParkourArrive"
	for _, x in { -4, 0, 4 } do marker(arr, "Spot", x, S.top, -4) end
	arr:SetAttribute("Built", "ParkourIsland")
	arr.Parent = doorsF
	local board = blk(root.Scenery, "Board", 8, 19, S.top + 3, S.top + 9.5, 12.6, 13, C.dark)
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 40; g.LightInfluence = 0
	local tl = Instance.new("TextLabel")
	tl.Name = "Text"; tl.BackgroundTransparency = 1; tl.Size = UDim2.fromScale(1, 1); tl.TextScaled = true; tl.TextWrapped = true
	tl.TextColor3 = Color3.fromHex("eceae4"); tl.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	tl.Text = "PARKOUR"
	tl.Parent = g
	g.Parent = board
	board.CFrame = CFrame.lookAt(board.Position, board.Position + V3(0, 0, 1)) -- (on the deck's front edge, right, facing you as you arrive)
	blk(root.Scenery, "BoardPost", 12.9, 14.1, S.top, S.top + 3, 12.6, 13, C.side)
	-- 1 sprint gaps
	for i, b in P.GAPS do deck("Gap" .. i, b[1] - 5, b[1] + 5, b[2] - 5, b[2] + 5, b[3], 8) end
	-- checkpoints
	for i, c in P.CPS do
		deck(c.name .. "Deck", c.x0, c.x1, c.z0, c.z1, c.top, 10)
		local mx, mz = (c.x0 + c.x1) / 2, (c.z0 + c.z1) / 2
		blk(root.Course, "CheckpointPad", mx - 4, mx + 4, c.top, c.top + 0.1, mz - 4, mz + 4, C.accent, { ghost = true, mat = NEON })
		local z = zone(c.name, c.x0, c.x1, c.top, c.top + 10, c.z0, c.z1, { Checkpoint = i })
		z.CFrame = CFrame.lookAt(z.Position, z.Position + V3(0, 0, -1))
	end
	-- 2 the slide strip, its bars, the gap to CP2
	local st = P.STRIP
	deck("SlideStrip", st.x0, st.x1, st.z0, st.z1, st.top, 6)
	for _, z in st.bars do
		local y = st.top + st.bar + 0.6
		local bar = Instance.new("Part")
		bar.Name = "Bar"; bar.Anchored = true; bar.CanTouch = false; bar.Shape = Enum.PartType.Cylinder
		bar.Size = V3(st.x1 - st.x0 + 2.4, 1.2, 1.2); bar.CFrame = CF(W(0, y, z))
		bar.Color = Color3.fromHex(C.trim); bar.Material = SP
		bar.Parent = root.Course
		for _, x in { st.x0 - 0.9, st.x1 + 0.9 } do blk(root.Course, "BarPost", x - 0.6, x + 0.6, st.top - 6, y + 0.6, z - 0.6, z + 0.6, C.side) end
	end
	-- 3 bhop stones (at z 240, between CP2 and CP3)
	for i, x in P.STONES do deck("Stone" .. i, x - 3, x + 3, 237, 243, 8, 5) end
	-- 4 grapple pillars
	for i, pl in P.PILLARS do
		blk(root.Course, "Pillar" .. i, pl[1] - 4, pl[1] + 4, P.LEG, 52, pl[2] - 4, pl[2] + 4, C.side, { mat = CONC })
		blk(root.Course, "PillarCap", pl[1] - 4.4, pl[1] + 4.4, 52, 53.2, pl[2] - 4.4, pl[2] + 4.4, C.top)
	end
	-- 5 the tower: a mass with ledges up its south face (toward CP4), the finish on top
	local tw = P.TOWER
	blk(root.Course, "Tower", tw.x0, tw.x1, P.LEG, tw.top - 0.6, tw.z0, tw.z1, C.mass, { mat = CONC })
	blk(root.Course, "TowerTop", tw.x0, tw.x1, tw.top - 0.6, tw.top, tw.z0, tw.z1, C.top)
	for _, l in tw.ledges do
		local x0 = if l[2] == "w" then tw.x0 - 6 else tw.x1 - 0.01
		local x1 = if l[2] == "w" then tw.x0 + 0.01 else tw.x1 + 6
		blk(root.Course, "Ledge", x0, x1, l[1] - 1.2, l[1], tw.z0 + 4, tw.z1 - 4, C.top)
	end
	blk(root.Course, "FinishLine", tw.x0 + 1, tw.x1 - 1, tw.top, tw.top + 0.08, tw.z0 + 1, tw.z0 + 1.6, C.accent, { ghost = true, mat = NEON })
	portal("ParkourAgain", tw.x0 + 6, tw.z1 - 4.6, tw.top, -1, { land = "ParkourArrive", text = "PARKOUR" })
	portal("FromParkour2", tw.x1 - 6, tw.z1 - 4.6, tw.top, -1, { land = "TrainingArrive", text = "BACK TO TRAINING" })
	-- what Parkour.server reads
	zone("Start", S.x0, S.x1, S.top - 1, S.top + 12, S.z0, S.z1)
	zone("Finish", tw.x0, tw.x1, tw.top, tw.top + 12, tw.z0, tw.z1)
	root:SetAttribute("FallY", P.SITE.Y - P.FALL)
	root:SetAttribute("Checkpoints", #P.CPS)
	root:SetAttribute("Built", "ParkourIsland")
	root.Parent = hub
	local Z = P.ZONE
	local zp = Instance.new("Part")
	zp.Name = "ParkourZone"; zp.Anchored = true; zp.Transparency = 1; zp.CanCollide = false; zp.CanQuery = false; zp.CanTouch = false
	zp.Size = V3(Z[2] - Z[1], Z[4] - Z[3], Z[6] - Z[5])
	zp.CFrame = CF(W((Z[1] + Z[2]) / 2, (Z[3] + Z[4]) / 2, (Z[5] + Z[6]) / 2))
	zp.Parent = hub
	return ("parkour built: %d parts at %s"):format(count, tostring(P.SITE))
end

-- ------------------------------------------------------------------ check: the gaps are what the moves can do
function P.check(): string
	local out = {}
	local hub = workspace.Map.Hub
	local root2 = hub:FindFirstChild("Parkour")
	if not root2 then return "no parkour" end
	-- nothing else in the island's box
	local Z = P.ZONE
	local box = CF(W((Z[1] + Z[2]) / 2, (Z[3] + Z[4]) / 2, (Z[5] + Z[6]) / 2))
	local op = OverlapParams.new(); op.FilterType = Enum.RaycastFilterType.Exclude; op.FilterDescendantsInstances = { root2, hub.Doors, hub:FindFirstChild("ParkourZone") }
	local others = workspace:GetPartBoundsInBox(box, V3(Z[2] - Z[1], Z[4] - Z[3], Z[6] - Z[5]), op)
	table.insert(out, ("other parts in the island's box: %d%s"):format(#others, if #others > 0 then " (" .. others[1]:GetFullName() .. ")" else ""))
	-- the landings: every checkpoint, the stones and the tower top have floor under their middle
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { root2.Course }
	local bad = 0
	for _, c in P.CPS do
		if not workspace:Raycast(W((c.x0 + c.x1) / 2, c.top + 5, (c.z0 + c.z1) / 2), V3(0, -10, 0), rp) then bad += 1 end
	end
	table.insert(out, "checkpoints with no floor: " .. bad)
	table.insert(out, ("gaps: sprint %d/%d/%d/%d, slide-jump gap %d, stones %d apart, the swing %d"):format(
		P.GAPS[1][2] - 5 - P.START.z1, P.GAPS[2][2] - P.GAPS[1][2] - 10, P.GAPS[3][2] - P.GAPS[2][2] - 10, P.GAPS[4][2] - P.GAPS[3][2] - 10,
		P.CPS[2].z0 - P.STRIP.z1, P.STONES[2] - P.STONES[1], P.CPS[4].x0 - P.CPS[3].x1))
	local n = 0
	for _, d in root2:GetDescendants() do if d:IsA("BasePart") then n += 1 end end
	table.insert(out, "parts: " .. n)
	return table.concat(out, "\n")
end

return P
