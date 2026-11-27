--!strict
-- HuntBuild (26 Nov 2026): the edit-time builder of HOLDOUT's lobby, THE HOUSE (roblox/docs/HUNT.md). WebArena builds
-- the house's look and hit boxes from ServerStorage.PolishBackup.HuntHouseLayout (W.import + W.build, like any arena);
-- this adds what an arena doesn't have, all baked into workspace.Map.HuntHouse.Hunt so the running game (and later the
-- house's own place) needs nothing from PolishBackup:
--   Doors       a Model per door: an anchored Hinge (its PrimaryPart, the closed frame), the leaf's meshes and an
--               invisible collision Leaf welded to it (server/HuntProps swings it); attributes Kind, Width, Slide
--   Rollup      the garage's roll-up door (Closed / Open CFrame attributes) and its Buttons
--   Switches    a plate per room light switch (Room); the Light markers get Room too
--   Props       TV screens (Room), taps (an attachment each), the fridge's door, toilets, the basketball
--   Tables      the store tables' prompt parts (Shop = the ShopOpen value, Label)
--   Seats       HubSeat-tagged cushion tops (server/HubSeats gives them Sit prompts)
--   Bouncy      the trampoline's mat and the beds' tops (attribute Trampoline = power; HuntMoves.client bounces you)
--   Spawns      where you appear (facing their LookVector); Exit, the porch's BACK TO HUB; Board, the round board
--   Zone        the lot's box (the server's "in the house" test)
-- and a look zone in Map.Hub.LookZones (HubLife gives anyone inside it HubLook's "hunt_house").
--   local B = require(game.ServerStorage.PolishBackup.HuntBuild:Clone())
--   print(B.build())       -- after W.import("HuntHouse", id) and W.build("HuntHouse")
--   print(B.check())       -- counts, and whatever is missing
local ServerStorage = game:GetService("ServerStorage")
local CollectionService = game:GetService("CollectionService")

local B = {}
B.NAME = "HuntHouse"

local V3, CF = Vector3.new, CFrame.new
local hex = Color3.fromHex

local function layout(): any
	local src = ServerStorage.PolishBackup:FindFirstChild(B.NAME .. "Layout")
	assert(src, "no ServerStorage.PolishBackup." .. B.NAME .. "Layout")
	local m = src:Clone()
	local L = require(m) :: any
	m:Destroy()
	return L
end
local function folder(parent: Instance, name: string): Folder
	local f = Instance.new("Folder"); f.Name = name; f.Parent = parent
	return f
end
local function part(parent: Instance, name: string, cf: CFrame, size: Vector3, solid: boolean?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = solid == true; p.CanQuery = solid == true; p.CanTouch = false
	p.CastShadow = false; p.Transparency = 1; p.Size = size; p.CFrame = cf
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end
-- a quarter-turn frame, as the layout's furniture uses (turn 0 faces +z): CFrame.Angles(0, turn * 90 deg, 0)
local function turnCF(x: number, y: number, z: number, turn: number, O: Vector3): CFrame
	return CF(O + V3(x, y, z)) * CFrame.Angles(0, turn * math.pi / 2, 0)
end

-- the templates (the kit's hx_* models, imported into ServerStorage.JankfireMeshes by W.import): kept in
-- ServerStorage.HuntTemplates; the built Shell's copies go
local function templates(root: Instance): Folder
	local t = ServerStorage:FindFirstChild("HuntTemplates") :: Folder?
	if t then t:Destroy() end
	local tf = Instance.new("Folder"); tf.Name = "HuntTemplates"; tf.Parent = ServerStorage
	local lib = ServerStorage:FindFirstChild("JankfireMeshes")
	for _, m in (if lib then lib:GetChildren() else {}) do
		if m:GetAttribute("Kit") == "hunthouse" and string.sub(m.Name, 1, 3) == "hx_" then m:Clone().Parent = tf end
	end
	local shell = root:FindFirstChild("Shell")
	if shell then for _, m in shell:GetChildren() do if string.sub(m.Name, 1, 3) == "hx_" then m:Destroy() end end end
	return tf
end
-- the template's meshes, placed by `at` (their kit frame's origin = the template's own origin), welded to `to`
local function hang(tf: Folder, name: string, at: CFrame, into: Instance, to: BasePart): number
	local tpl = tf:FindFirstChild(name)
	if not tpl then return 0 end
	local n = 0
	for _, d in tpl:GetDescendants() do
		if d:IsA("BasePart") then
			local c = d:Clone()
			c.CFrame = at * d.CFrame
			c.Anchored = false; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.Massless = true
			c.Parent = into
			local w = Instance.new("WeldConstraint"); w.Part0 = to; w.Part1 = c; w.Parent = c
			n += 1
		end
	end
	return n
end

local TEMPLATE = { int = "hx_doorint", front = "hx_doorfront", back = "hx_doorback", gate = "hx_gate", slide = "hx_slide" }

local function doors(H: any, O: Vector3, tf: Folder, into: Folder): number
	local n = 0
	for _, d in H.doors do
		local w = d.a1 - d.a0
		local h = d.y1 - d.y0
		-- (the sliding glass door's moving half is always the a0 half: the kit's fixed glass fills the a1 half)
		local fromA0 = d.hinge == "a0" or d.kind == "slide"
		local hingeA = if fromA0 then d.a0 else d.a1
		local pos = if d.axis == "x" then V3(hingeA, d.y0, d.line) else V3(d.line, d.y0, hingeA)
		-- the leaf runs from its hinge along local +x: toward a1 from a0's hinge, or back toward a0 from a1's
		local yaw: number
		if d.axis == "x" then yaw = if fromA0 then 0 else math.pi
		else yaw = if fromA0 then -math.pi / 2 else math.pi / 2 end
		local at = CF(O + pos) * CFrame.Angles(0, yaw, 0)
		local m = Instance.new("Model")
		m.Name = "Door_" .. d.id
		local hinge = part(m, "Hinge", at, V3(0.4, 0.4, 0.4))
		m.PrimaryPart = hinge
		local leafW = if d.kind == "slide" then w / 2 else w
		local leaf = part(m, "Leaf", at * CF(leafW / 2, h / 2, 0), V3(leafW - 0.1, h - 0.05, 0.4), true)
		leaf.Anchored = false; leaf.Massless = true
		leaf:SetAttribute("Mat", "wood")
		local lw = Instance.new("WeldConstraint"); lw.Part0 = hinge; lw.Part1 = leaf; lw.Parent = leaf
		local tname = TEMPLATE[d.kind] or "hx_doorint"
		-- (the sliding glass door: its moving half sits a little inside the wall's middle, the fixed half outside it)
		local tat = if d.kind == "slide" then at * CF(0, 0, -0.35) else at
		if d.kind == "slide" then hinge.CFrame = tat; leaf.CFrame = tat * CF(leafW / 2, h / 2, 0) end
		hang(tf, tname, tat, m, hinge)
		m:SetAttribute("Kind", d.kind); m:SetAttribute("Width", leafW); m:SetAttribute("Id", d.id)
		if d.kind == "slide" then m:SetAttribute("Slide", leafW) end
		if d.kind == "front" then m:SetAttribute("Front", true) end
		m.Parent = into
		n += 1
	end
	return n
end

local function rollup(H: any, O: Vector3, tf: Folder, into: Folder): string
	local r = H.rollup
	local cx = (r.a0 + r.a1) / 2
	local m = Instance.new("Model"); m.Name = "Rollup"
	local closed = CF(O + V3(cx, r.y0, r.z))
	-- open: tipped back to lie flat under the garage's ceiling, its bottom edge just inside the opening
	local open = CF(O + V3(cx, 12.2, r.z - 0.3)) * CFrame.Angles(-math.pi / 2, 0, 0)
	local root = part(m, "Root", closed, V3(0.4, 0.4, 0.4))
	m.PrimaryPart = root
	local panel = part(m, "Panel", closed * CF(0, (r.y1 - r.y0) / 2, 0), V3(r.a1 - r.a0, r.y1 - r.y0, 0.5), true)
	panel.Anchored = false; panel.Massless = true; panel:SetAttribute("Mat", "metal")
	local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = panel; w.Parent = panel
	hang(tf, "hx_rollup", closed, m, root)
	m:SetAttribute("Closed", closed); m:SetAttribute("Open", open)
	m.Parent = into
	local bf = folder(into, "Buttons")
	local gb = H.garageButton
	local b1 = part(bf, "Button", CFrame.lookAt(O + V3(gb[1], gb[2], gb[3]), O + V3(gb[1] + gb[4], gb[2], gb[3] + gb[5])), V3(1.2, 1.6, 0.4))
	b1:SetAttribute("Side", "in")
	local b2 = part(bf, "Button", CFrame.lookAt(O + V3(100.5, 3.4, 44.5), O + V3(100.5, 3.4, 50)), V3(1.2, 1.6, 0.4))
	b2:SetAttribute("Side", "out")
	return "rollup + 2 buttons"
end

local function switches(H: any, O: Vector3, tf: Folder, root: Instance, into: Folder): (number, number)
	local n = 0
	for _, s in H.switches do
		local pos = O + V3(s[2], s[3], s[4])
		local face = V3(s[5], 0, s[6])
		local at = CFrame.lookAt(pos, pos - face) -- (its -Z into the wall: the plate's front, +Z, into the room)
		local plate = part(into, "Switch", at * CF(0, 0, 0.06), V3(0.8, 1.2, 0.2))
		plate:SetAttribute("Room", s[1])
		local tpl = tf:FindFirstChild("hx_switch")
		if tpl then
			for _, d in tpl:GetDescendants() do
				if d:IsA("BasePart") then
					local c = d:Clone(); c.CFrame = at * d.CFrame; c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
					c.Parent = plate
				end
			end
		end
		n += 1
	end
	-- the Light markers WebArena made: each gets the Room of the layout's light nearest it
	local lights = root:FindFirstChild("Lights")
	local tagged = 0
	for _, lm in (if lights then lights:GetChildren() else {}) do
		if not lm:IsA("BasePart") then continue end
		local best, bd = nil, 2.0
		for _, l in H.lightRooms do
			local d = (lm.Position - (O + V3(l[2], l[3], l[4]))).Magnitude
			if d < bd then best, bd = l[1], d end
		end
		if best then lm:SetAttribute("Room", best); tagged += 1 end
	end
	return n, tagged
end

local function props(H: any, O: Vector3, tf: Folder, into: Folder): string
	local nt, nw, nf, nl = 0, 0, 0, 0
	for _, t in H.tvs do -- the screen: a thin panel just proud of the TV's dark screen (HuntProps lights it)
		local at = turnCF(t[1], t[2], t[3], t[4], O)
		local s = part(into, "TV", at * CF(0, 3.5, 0.62), V3(11.0, 6.0, 0.08)) -- (0.62: clear of the TV mesh's own screen, round 7)
		s.Transparency = 0; s.Material = Enum.Material.Neon; s.Color = Color3.fromRGB(100, 110, 122); s.CanQuery = false -- (rounds 6-9: a lit slate glow, never a black slab)
		s:SetAttribute("Kind", "tv")
		nt += 1
	end
	for _, p in H.props do
		local kind = p[1]
		local pos = O + V3(p[2], p[3], p[4])
		if kind == "tap" then
			local a = part(into, "Tap", CF(pos + V3(0, 0.6, 0)), V3(1, 1, 1))
			a:SetAttribute("Kind", "tap"); a:SetAttribute("Room", p[5])
			nw += 1
		elseif kind == "toilet" then
			local a = part(into, "Toilet", CF(pos + V3(0, 3.0, 0)), V3(2.5, 2.5, 2.5))
			a:SetAttribute("Kind", "toilet")
			nl += 1
		elseif kind == "ball" then
			local b = Instance.new("Part")
			b.Name = "Ball"; b.Shape = Enum.PartType.Ball; b.Size = V3(2.4, 2.4, 2.4); b.Color = hex("b26a40")
			b.Material = Enum.Material.SmoothPlastic; b.Anchored = true; b.CFrame = CF(pos)
			b.CustomPhysicalProperties = PhysicalProperties.new(0.4, 0.5, 0.7, 1, 1)
			b:SetAttribute("Kind", "ball"); b:SetAttribute("Home", pos); b:SetAttribute("HuntBall", true)
			b.Parent = into
		end
	end
	for _, f in H.fridges do -- the fridge's upper door: hinged at its front edge (the fridge's local -x side)
		local at = turnCF(f[1], f[2], f[3], f[4], O) * CF(-2.85, 6.8, 2.2)
		local m = Instance.new("Model"); m.Name = "Fridge"
		local hinge = part(m, "Hinge", at, V3(0.4, 0.4, 0.4))
		m.PrimaryPart = hinge
		local leaf = part(m, "Leaf", at * CF(2.85, 2.5, 0.16), V3(5.7, 5.0, 0.32), true)
		leaf.Anchored = false; leaf.Massless = true
		local w = Instance.new("WeldConstraint"); w.Part0 = hinge; w.Part1 = leaf; w.Parent = leaf
		hang(tf, "hx_fridgedoor", at, m, hinge)
		local light = Instance.new("PointLight"); light.Name = "Inside"; light.Range = 9; light.Brightness = 0.8
		light.Color = hex("e8f2ff"); light.Enabled = false; light.Parent = hinge
		m:SetAttribute("Kind", "fridge")
		m.Parent = into
		nf += 1
	end
	return ("%d TVs, %d taps, %d fridge, %d toilets, the ball"):format(nt, nw, nf, nl)
end

-- the seats: the cushion top of each, local to the piece (its front +z); several on a sofa or a bench
local SEATS = {
	sofa3 = { { -6, 2.9, 0.6 }, { 0, 2.9, 0.6 }, { 6, 2.9, 0.6 } }, sofa2 = { { -3, 2.9, 0.6 }, { 3, 2.9, 0.6 } },
	armchair = { { 0, 2.9, 0.6 } }, chair = { { 0, 3.2, 0.1 } }, stool = { { 0, 4.0, 0 } }, bench = { { -2, 3.0, 0 }, { 2, 3.0, 0 } },
	patiochair = { { 0, 2.6, 0.1 } }, lounger = { { 0, 2.3, 0 } }, officechair = { { 0, 3.1, 0 } }, beanbag = { { 0, 2.3, 0.4 } },
	swing = { { 0, 0.3, 0 } },
}
local function seats(H: any, O: Vector3, into: Folder): number
	local n = 0
	for _, s in H.seats do
		local kind = s[1]
		local at = turnCF(s[2], s[3], s[4], s[5], O)
		local spots = SEATS[kind]
		if kind == "treebench" then
			spots = {}
			for k = 0, 5 do
				local a = k * math.pi / 3
				table.insert(spots, { math.sin(a) * 4.4, 2.9, math.cos(a) * 4.4, a })
			end
		end
		for _, sp in (spots or {}) do
			local cf = at * CF(sp[1], sp[2], sp[3])
			if sp[4] then cf = at * CFrame.Angles(0, sp[4], 0) * CF(0, sp[2], 4.4) end
			local p = part(into, "Seat", cf, V3(2.0, 0.2, 2.0))
			CollectionService:AddTag(p, "HubSeat")
			n += 1
		end
	end
	return n
end

local BEDS = { bedking = { 13.4, 16.4 }, beddouble = { 10.4, 14.4 }, bunk = { 7.2, 14.2 } }
local function bouncy(H: any, O: Vector3, into: Folder): number
	local n = 0
	for _, b in H.beds do
		local sz = BEDS[b[1]]
		if not sz then continue end
		local at = turnCF(b[2], b[3], b[4], b[5], O)
		local tops = if b[1] == "bunk" then { 4.6, 9.8 } else { 4.9 }
		for _, y in tops do
			local p = part(into, "Bed", at * CF(0, y - 0.2, 0.8), V3(sz[1], 0.4, sz[2] - 2.0), true)
			p:SetAttribute("Trampoline", 0.55); p.CanQuery = false
			n += 1
		end
	end
	-- the trampoline: a round mat (a cylinder lying on its side) and the padded ring round it
	local t = H.tramp
	local c = O + V3(t.x, 0, t.z)
	local top = t.y + 2.6
	local mat = Instance.new("Part")
	mat.Name = "Trampoline"; mat.Shape = Enum.PartType.Cylinder; mat.Anchored = true; mat.Transparency = 1
	mat.CanCollide = true; mat.CanQuery = false; mat.CanTouch = false; mat.CastShadow = false
	mat.Size = V3(0.4, (t.r - 3.0) * 2, (t.r - 3.0) * 2)
	mat.CFrame = CF(c + V3(0, top - 0.2, 0)) * CFrame.Angles(0, 0, math.pi / 2)
	mat:SetAttribute("Trampoline", 1); mat:SetAttribute("Mat", "fabric")
	mat.Parent = into
	for k = 0, 15 do
		local a = k * math.pi / 8
		local rr = t.r - 1.3
		local p = part(into, "Pad", CFrame.lookAt(c + V3(math.cos(a) * rr, t.y + 2.35, math.sin(a) * rr), c + V3(0, t.y + 2.35, 0)),
			V3(rr * 2 * math.sin(math.pi / 16) + 0.6, 1.7, 3.4), true)
		p:SetAttribute("Trampoline", 0.7); p.CanQuery = false
	end
	return n + 1
end

-- the house is two uploads (one 247k-triangle kit came back "Unknown Error" from Open Cloud; its halves went up fine):
-- the architecture through W.import("HuntHouse", ARCH) as any arena, then the furniture and the moving pieces with
-- this, which paints them the same way (a piece's name: <model><n>__<kind>_<hex>) and adds them to the same kit
-- WITHOUT clearing it (W.import clears the kit first)
B.ARCH = 113950542566812
B.FURN = 124923882312765
local MAT = { plastic = Enum.Material.SmoothPlastic, neon = Enum.Material.Neon, glass = Enum.Material.Glass, water = Enum.Material.SmoothPlastic }
local SEE = { glass = 0.35, water = 0.25 }
function B.importExtra(id: number?): string
	local aid = id or B.FURN
	local L = layout()
	local ok, container = pcall(function() return game:GetService("InsertService"):LoadAsset(aid) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local lib = ServerStorage:WaitForChild("JankfireMeshes")
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
		d.Transparency = SEE[kind] or 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind == "plastic"; d.DoubleSided = false
		d:SetAttribute("Kind", kind)
		local pic = L.surfaces and L.surfaces[string.lower(h)]
		if pic then local sa = Instance.new("SurfaceAppearance"); sa.ColorMap = pic; sa.Parent = d end
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	for _, old in lib:GetChildren() do
		if old:GetAttribute("Kit") == L.kit and old:GetAttribute("AssetId") == aid then old:Destroy() end
	end
	local names = {}
	for mname, parts in groups do
		local m = Instance.new("Model")
		m.Name = mname
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", aid); m:SetAttribute("Kit", L.kit); m:SetAttribute("FileFrame", true)
		m.Parent = lib
		table.insert(names, ("%s %d"):format(mname, #parts))
	end
	container:Destroy()
	table.sort(names)
	return ("extra kit %d: %d models%s: %s"):format(aid, #names, if bad > 0 then ", " .. bad .. " unnamed" else "", table.concat(names, ", "))
end

-- the gunman's intro kit (tools/roblox/hunt_intro_models.py; HUNT.md section 11): its rooms and the mask go to
-- ReplicatedStorage[HuntConfig.INTRO.kit] for the clients (HuntIntro) and the server (HuntMask), each model at its file
-- frame (room A round the origin, B at +40 x, the mask round a head at -40 x: HuntIntroData.origin)
B.INTRO = 70825613805108 -- (27 Nov: hunt_intro4: + the wreck pieces (chair, lamp, armchair, papers, frame, door) for the gunman's walk)
function B.importIntro(id: number?): string
	local aid = id or B.INTRO
	local HC = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
	local ok, container = pcall(function() return game:GetService("InsertService"):LoadAsset(aid) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local RS = game:GetService("ReplicatedStorage")
	local old = RS:FindFirstChild(HC.INTRO.kit)
	if old then old:Destroy() end
	local kit = Instance.new("Folder")
	kit.Name = HC.INTRO.kit
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = hex(h); d.TextureID = ""
		d.Transparency = SEE[kind] or 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind == "plastic"; d.DoubleSided = false
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for mname, parts in groups do
		local m = Instance.new("Model")
		m.Name = mname
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", aid)
		m.Parent = kit
		table.insert(names, ("%s %d"):format(mname, #parts))
	end
	container:Destroy()
	kit:SetAttribute("AssetId", aid)
	kit.Parent = RS
	table.sort(names)
	return ("intro kit %d: %d models%s: %s"):format(aid, #names, if bad > 0 then ", " .. bad .. " unnamed" else "", table.concat(names, ", "))
end

function B.build(): string
	local L = layout()
	local H = L.hunt
	local O: Vector3 = L.origin
	local map = workspace:FindFirstChild("Map")
	local root = map and map:FindFirstChild(B.NAME)
	if not root then return "no workspace.Map." .. B.NAME .. ": W.import + W.build it first" end
	root:SetAttribute("Enabled", false) -- (never in the PvP pool)
	root:SetAttribute("HuntLobby", true)
	root:SetAttribute("Title", "THE HOUSE")
	local old = root:FindFirstChild("Hunt")
	if old then old:Destroy() end
	local hf = Instance.new("Folder"); hf.Name = "Hunt"
	local tf = templates(root)
	local out = {}
	table.insert(out, ("%d doors"):format(doors(H, O, tf, folder(hf, "Doors"))))
	table.insert(out, rollup(H, O, tf, folder(hf, "Garage")))
	local ns, nl = switches(H, O, tf, root, folder(hf, "Switches"))
	table.insert(out, ("%d switches, %d lights by room"):format(ns, nl))
	table.insert(out, props(H, O, tf, folder(hf, "Props")))
	local tables = folder(hf, "Tables")
	for _, t in H.tables do
		local p = part(tables, "Table", CFrame.lookAt(O + V3(t[2], t[3] + 4.0, t[4] + 3.4), O + V3(t[2], t[3] + 4.0, t[4] + 10)), V3(9, 4, 1))
		p:SetAttribute("Tab", t[1])
	end
	table.insert(out, ("%d store tables"):format(#H.tables))
	table.insert(out, ("%d seats"):format(seats(H, O, folder(hf, "Seats"))))
	table.insert(out, ("%d bouncy"):format(bouncy(H, O, folder(hf, "Bouncy"))))
	local sp = folder(hf, "Spawns")
	for i, s in H.spawns do
		local pos = O + V3(s[1], s[2] + 0.1, s[3])
		part(sp, "Spawn" .. i, CFrame.lookAt(pos, pos + V3(s[4], 0, s[5])), V3(4, 0.2, 4))
	end
	local ex = H.exit
	local e = part(hf, "Exit", CF(O + V3(ex.at[1], ex.at[2] + 3.0, ex.at[3])), V3(6, 6, 2))
	e:SetAttribute("Door", ex.door)
	local bd = H.board
	local bp = part(hf, "Board", CFrame.lookAt(O + V3(bd.at[1] + 0.12, bd.at[2], bd.at[3]), O + V3(bd.at[1] + 5, bd.at[2], bd.at[3])), V3(bd.size[1], bd.size[2], 0.05))
	bp:SetAttribute("Kind", "board")
	local z = H.zone
	local zp = part(hf, "Zone", CF(O + V3((z[1] + z[4]) / 2, (z[2] + z[5]) / 2, (z[3] + z[6]) / 2)), V3(z[4] - z[1], z[5] - z[2], z[6] - z[3]))
	zp:SetAttribute("Kind", "zone")
	hf.Parent = root
	-- the look: a zone in Map.Hub.LookZones (HubLife: whoever stands in it gets HubLook "hunt_house")
	local hub = map:FindFirstChild("Hub")
	local lz = hub and hub:FindFirstChild("LookZones")
	if hub and not lz then lz = folder(hub, "LookZones") end
	if lz then
		local o = lz:FindFirstChild("HuntHouseLook")
		if o then o:Destroy() end
		local p = zp:Clone(); p.Name = "HuntHouseLook"; p:SetAttribute("Look", "hunt_house"); p:SetAttribute("Kind", nil)
		p.Parent = lz
	end
	return "THE HOUSE: " .. table.concat(out, ", ")
end

function B.check(): string
	local map = workspace:FindFirstChild("Map")
	local root = map and map:FindFirstChild(B.NAME)
	local hf = root and root:FindFirstChild("Hunt")
	if not hf then return "not built" end
	local out = {}
	for _, f in hf:GetChildren() do table.insert(out, f.Name .. " " .. #f:GetChildren()) end
	table.sort(out)
	local look = map:FindFirstChild("Hub") and map.Hub:FindFirstChild("LookZones") and map.Hub.LookZones:FindFirstChild("HuntHouseLook")
	return table.concat(out, ", ") .. (if look then "; look zone OK" else "; NO LOOK ZONE")
end

return B
