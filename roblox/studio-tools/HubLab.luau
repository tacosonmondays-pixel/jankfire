--!nocheck
-- edit-time builder (2026-11-14) for the hub comparison: four more hubs, each its own idea on the same rules, built
-- far from the live hub under workspace.Map.HubLab. every hub has what a hub needs (spawn, six pads, a training door,
-- the name, info screens, somewhere to sit) but only Hub 1's pads start matches: these are for choosing a look.
-- usage: local L = require(game.ServerStorage.PolishBackup.HubLab:Clone()); print(L.build("Hub5_Depot"))  -- or L.buildAll()
-- a hub's own coordinates: x east, z south, y up from its floor. you spawn in the south and look north (-z) at the pads.
-- `face` is the way a thing's front looks, in degrees: 0 south (+z), 180 north, 90 east, -90 west.
local L = {}
local lib = game.ServerStorage.JankfireMeshes
local hub = workspace.Map.Hub
local PINK, CYAN, YEL, GREEN = "ff4fd8", "37d6ff", "ffe14d", "7dff4f"
L.SITES = { Hub2_Platform = Vector3.new(-600, 240, -10000), Hub3_Lanes = Vector3.new(-200, 240, -10000), Hub4_FoodCourt = Vector3.new(200, 240, -10000), Hub5_Depot = Vector3.new(600, 240, -10000) }
L.ORDER = { "Hub2_Platform", "Hub3_Lanes", "Hub4_FoodCourt", "Hub5_Depot" }
L.TITLE = { Hub2_Platform = "THE PLATFORM", Hub3_Lanes = "THE LANES", Hub4_FoodCourt = "THE FOOD COURT", Hub5_Depot = "THE DEPOT" }

-- the six modes, with the words and colours the live hub's signs use
local function modes()
	local t = {}
	for _, id in { "1v1", "1v1v1", "2v2", "3v3", "4v4", "5v5" } do
		local s = hub.Scenery.Corridor:FindFirstChild("ModeSign_" .. id)
		local labels = {}
		if s then for _, d in s:GetDescendants() do if d:IsA("TextLabel") and #labels < 2 then table.insert(labels, d) end end end
		t[id] = {
			id = id, title = labels[1] and labels[1].Text or string.upper(id), tag = labels[2] and labels[2].Text or "",
			color = labels[1] and labels[1].TextColor3:ToHex() or PINK,
			teams = if id == "1v1v1" then 3 else 2, size = tonumber(id:sub(1, 1)), soon = id == "5v5",
		}
	end
	return t
end

local function newHub(name)
	local H = { name = name, O = L.SITES[name], missing = {}, count = 0, M = modes(), discAt = {}, spawnAt = {} }
	local lab = workspace.Map:FindFirstChild("HubLab")
	if not lab then lab = Instance.new("Folder"); lab.Name = "HubLab"; lab.Parent = workspace.Map end
	local old = lab:FindFirstChild(name); if old then old:Destroy() end
	local root = Instance.new("Folder"); root.Name = name
	for _, n in { "Shell", "Scenery", "Pads", "Spawns", "Collision" } do local f = Instance.new("Folder"); f.Name = n; f.Parent = root end
	H.root = root
	-- its doors, arrival markers and look zone live with the live hub's (the door and lighting scripts read them there)
	for _, c in hub.Doors:GetChildren() do if c.Name:sub(1, #name + 1) == name .. "_" then c:Destroy() end end
	local lz = hub:FindFirstChild("LookZones")
	if not lz then lz = Instance.new("Folder"); lz.Name = "LookZones"; lz.Parent = hub end
	local oz = lz:FindFirstChild(name); if oz then oz:Destroy() end

	function H.w(x, y, z) return H.O + Vector3.new(x, y, z) end
	local function front(face) local a = math.rad(face); return Vector3.new(math.sin(a), 0, math.cos(a)) end
	H.front = front

	-- a plain block from corner to corner (shell, floor paint, fat trim)
	function H.block(folder, bname, x0, x1, y0, y1, z0, z1, hex, mat, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = bname; p.Anchored = true
		p.Size = Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0))
		p.CFrame = CFrame.new(H.w((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) * (o.rot or CFrame.identity)
		p.Color = Color3.fromHex(hex); p.Material = mat or Enum.Material.SmoothPlastic
		p.Transparency = o.tr or 0
		if o.ghost then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end
		if o.noShadow or o.ghost then p.CastShadow = false end
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Parent = root[folder]
		H.count += 1
		return p
	end

	-- a closed room: floor, ceiling, four walls. o.open.N / S / W / E = { { from, to, height }, ... } leaves doorways
	-- (N is the far wall at z0, S the near wall at z1, W at x0, E at x1)
	function H.room(rname, x0, x1, z0, z1, h, o)
		o = o or {}
		local wall, floor, ceil = o.wall or "6c6e73", o.floor or "4c4e53", o.ceil or "50535f"
		if not o.noFloor then H.block("Shell", rname .. "Floor", x0 - 2, x1 + 2, -2, 0, z0 - 2, z1 + 2, floor, o.floorMat) end
		if not o.noCeil then H.block("Shell", rname .. "Ceiling", x0 - 2, x1 + 2, h, h + 1, z0 - 2, z1 + 2, ceil, o.ceilMat) end
		local open = o.open or {}
		local function run(side, a0, a1, fixed0, fixed1, alongX)
			local gaps = open[side] or {}
			table.sort(gaps, function(p, q) return p[1] < q[1] end)
			local at = a0
			local function seg(s0, s1, y0, y1)
				if s1 - s0 < 0.05 or y1 - y0 < 0.05 then return end
				if alongX then H.block("Shell", rname .. "Wall" .. side, s0, s1, y0, y1, fixed0, fixed1, wall, o.wallMat)
				else H.block("Shell", rname .. "Wall" .. side, fixed0, fixed1, y0, y1, s0, s1, wall, o.wallMat) end
			end
			for _, g in gaps do
				seg(at, g[1], 0, h)
				seg(g[1], g[2], g[3], h) -- the wall above the doorway
				at = g[2]
			end
			seg(at, a1, 0, h)
		end
		if not (o.skip and o.skip.N) then run("N", x0 - 2, x1 + 2, z0 - 2, z0, true) end
		if not (o.skip and o.skip.S) then run("S", x0 - 2, x1 + 2, z1, z1 + 2, true) end
		if not (o.skip and o.skip.W) then run("W", z0, z1, x0 - 2, x0, false) end
		if not (o.skip and o.skip.E) then run("E", z0, z1, x1, x1 + 2, false) end
	end

	local boxSrc = hub.TrainingGround.PropCollision:FindFirstChild("RangeCounterBox")
	function H.solid(sname, size, cf)
		local b = boxSrc:Clone(); b.Name = sname; b.Size = size; b.CFrame = cf; b.Parent = root.Collision
		return b
	end

	-- a model from the library. (x, z) is the middle of its footprint, or with o.back the point on the wall its back goes against
	function H.put(tmpl, pname, x, y, z, face, o)
		o = o or {}
		local t = lib:FindFirstChild(tmpl)
		if not t then H.missing[tmpl] = (H.missing[tmpl] or 0) + 1; return nil end
		local m = t:Clone(); m.Name = pname or tmpl
		if o.scale and math.abs(o.scale - 1) > 0.005 then m:ScaleTo(o.scale) end
		local _, sz = m:GetBoundingBox()
		local f = front(face or 0)
		local pos = Vector3.new(x, y, z)
		if o.back then pos += f * (sz.Z / 2) end
		local cy = if o.seat == "top" then y - sz.Y / 2 elseif o.seat == "centre" then y else y + sz.Y / 2
		local cf = CFrame.new(H.w(pos.X, cy, pos.Z)) * CFrame.Angles(0, math.rad(face or 0), 0)
		m:PivotTo(cf)
		if o.color then
			for _, p in m:GetDescendants() do
				if p:IsA("BasePart") then for key, hex in o.color do if p.Name:find("_" .. key, 1, true) then p.Color = Color3.fromHex(hex) end end end
			end
		end
		m.Parent = root.Scenery
		if typeof(o.solid) == "table" then
			-- a list of boxes { sx, sy, sz, ox, oy, oz } for things you walk through or into (arches, booths): the size, then
			-- the box's middle measured from the model's bottom centre in the model's own directions (x along its width,
			-- y up, z out of its front). oy left out = the box stands on the floor.
			local base = CFrame.new(cf.Position.X, H.O.Y + cy - sz.Y / 2, cf.Position.Z) * cf.Rotation
			for i, b in o.solid do
				H.solid((pname or tmpl) .. "Box" .. i, Vector3.new(b[1], b[2], b[3]), base * CFrame.new(b[4] or 0, b[5] or b[2] / 2, b[6] or 0))
			end
		elseif o.solid then
			local s = if typeof(o.solid) == "Vector3" then o.solid else sz
			H.solid((pname or tmpl) .. "Box", s, CFrame.new(cf.Position.X, H.O.Y + cy - sz.Y / 2 + s.Y / 2, cf.Position.Z) * cf.Rotation)
		end
		H.count += 1
		return m, sz, cf
	end

	-- words on a dark plate. lines = { { text, hex, "L" or "F", height 0..1 }, ... } stacked top to bottom.
	-- o.both = the same words on the back; o.backLines = other words on the back; o.clear = no plate (words on a model's
	-- own plate); o.flush = (x, y, z) is the face the words are on, not the middle of the plate; o.plate = plate colour.
	-- a scaled label can be 100 px tall at most, so the picture is made coarser by itself when a line is taller than that
	-- (otherwise big names come out small on big plates).
	function H.text(tname, lines, w, h, x, y, z, face, o)
		o = o or {}
		local thick = o.thick or 0.3
		local p = Instance.new("Part")
		p.Name = tname; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Size = Vector3.new(w, h, thick)
		p.Color = Color3.fromHex(o.plate or "2e3140"); p.Material = Enum.Material.SmoothPlastic
		p.Transparency = o.clear and 1 or 0
		local at = Vector3.new(x, y, z)
		if o.flush then at -= front(face) * (thick / 2) end
		p.CFrame = CFrame.new(H.w(at.X, at.Y, at.Z)) * CFrame.Angles(0, math.rad(face) + math.pi, 0)
		local sides = { { Enum.NormalId.Front, lines } }
		if o.backLines or o.both then table.insert(sides, { Enum.NormalId.Back, o.backLines or lines }) end
		for _, side in sides do
			local lines = side[2]
			local total, tallest = 0, 0
			for _, ln in lines do total += ln[4]; tallest = math.max(tallest, ln[4]) end
			local k = 0.92 / math.max(total, 0.01)
			local g = Instance.new("SurfaceGui")
			g.Name = "Gui"; g.Face = side[1]; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			g.PixelsPerStud = math.min(o.pps or 30, math.max(8, math.floor(100 / math.max(tallest * k * h, 0.01))))
			g.LightInfluence = 0
			local yAt = 0.04
			for i, ln in lines do
				local t = Instance.new("TextLabel")
				t.Name = "Line" .. i; t.BackgroundTransparency = 1; t.TextScaled = true
				t.Text = ln[1]; t.TextColor3 = Color3.fromHex(ln[2] or "ffffff")
				t.FontFace = Font.new(if ln[3] == "L" then "rbxasset://fonts/families/LuckiestGuy.json" else "rbxasset://fonts/families/FredokaOne.json")
				t.Size = UDim2.new(0.94, 0, ln[4] * k, 0); t.Position = UDim2.new(0.03, 0, yAt, 0)
				if ln[3] == "L" then local s = Instance.new("UIStroke"); s.Thickness = 3; s.Color = Color3.fromHex("14101e"); s.Parent = t end
				t.Parent = g
				yAt += ln[4] * k
			end
			g.Parent = p
		end
		p.Parent = root.Scenery
		H.count += 1
		return p
	end

	function H.lamp(x, y, z, range, bright, hex, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = "LampSpot"; p.Size = Vector3.new(1, 0.2, 1); p.Transparency = 1; p.Anchored = true
		p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Position = H.w(x, y, z)
		local l = Instance.new(if o.spot then "SpotLight" else "PointLight")
		l.Range = range; l.Brightness = bright; l.Color = Color3.fromHex(hex or "f6f1e6"); l.Shadows = o.shadows or false
		if o.spot then l.Face = Enum.NormalId.Bottom; l.Angle = o.angle or 120 end
		l.Parent = p
		p.Parent = root.Scenery
		return p
	end

	-- a queue pad: a dark base, the team plates to stand on, white edges. `face` looks at what you queue for
	-- (train door, pins, counter, bay); the plates sit side by side across that.
	function H.pad(id, x, z, face, w, d)
		local md = H.M[id]
		local f = front(face)
		local r = Vector3.new(f.Z, 0, -f.X)
		local m = Instance.new("Model"); m.Name = id
		m:SetAttribute("Mode", id); m:SetAttribute("Teams", md.teams); m:SetAttribute("Size", md.size); m:SetAttribute("ForShow", true)
		local rot = CFrame.Angles(0, math.rad(face), 0)
		local function plate(pn, cx, cz, sx, sz, hex, mat, yy, th)
			local p = Instance.new("Part")
			p.Name = pn; p.Anchored = true; p.Size = Vector3.new(sx, th or 0.12, sz)
			p.CFrame = CFrame.new(H.w(x, yy or 0.07, z) + r * cx + f * cz) * rot
			p.Color = Color3.fromHex(hex); p.Material = mat or Enum.Material.SmoothPlastic
			p.CanCollide = false; p.CastShadow = false; p.Parent = m
			return p
		end
		plate("Base", 0, 0, w, d, "1b1c22", nil, 0.04, 0.08)
		local cols = if md.soon then { "6a6e7c", "6a6e7c" } elseif md.teams == 3 then { PINK, YEL, CYAN } else { PINK, CYAN }
		local n = #cols
		local pw = (w - 1.2 - (n - 1) * 0.8) / n
		for i, hex in cols do
			local cx = -(w - 1.2) / 2 + pw / 2 + (i - 1) * (pw + 0.8)
			local s = plate("Side" .. i, cx, 0, pw, d - 1.2, hex, Enum.Material.Neon, 0.12, 0.14)
			s:SetAttribute("Team", i)
			s.Color = Color3.fromHex(hex):Lerp(Color3.new(0, 0, 0), 0.28)
			-- a closed pad is flat mid grey, not dark neon (that rendered as a black pit in every hub)
			if md.soon then s.Material = Enum.Material.SmoothPlastic; s.Color = Color3.fromHex("7d8291") end
		end
		if md.soon then -- and has a fat yellow tape cross over it
			local len = math.sqrt((w - 2.4) ^ 2 + (d - 2.4) ^ 2)
			for _, sgn in { 1, -1 } do
				local t = plate("Tape", 0, 0, len, 1.1, YEL, nil, 0.22, 0.06)
				t.CFrame = t.CFrame * CFrame.Angles(0, sgn * math.atan2(d - 2.4, w - 2.4), 0)
			end
		end
		for _, e in { { 0, d / 2 - 0.2, w, 0.4 }, { 0, -d / 2 + 0.2, w, 0.4 }, { w / 2 - 0.2, 0, 0.4, d }, { -w / 2 + 0.2, 0, 0.4, d } } do
			plate("Edge", e[1], e[2], e[3], e[4], "f4f8ff", Enum.Material.Neon, 0.14, 0.1)
		end
		m.Parent = root.Pads
		H.count += 1
		return m
	end

	-- the pad's two signs: the mode with its line, and the count screen in a chunky bezel
	function H.modeSign(id, x, y, z, face, o)
		o = o or {}
		local md = H.M[id]
		local s = o.scale or 1
		return H.text("ModeText_" .. id, { { md.title, md.color, "L", 0.6 }, { md.tag, "ffffff", "F", 0.3 } }, 13 * s, 3.6 * s, x, y, z, face, { both = o.both, plate = o.plate })
	end
	function H.countScreen(id, x, y, z, face, wide, o)
		o = o or {}
		local md = H.M[id]
		local n = md.size
		local status = if md.soon then "coming soon(ish)" elseif md.teams == 3 then ("0/1  vs  0/1  vs  0/1") else ("0/%d  vs  0/%d"):format(n, n)
		local f = front(face)
		local _, bsz = H.put("hb_screen", "Bezel_" .. id, x, y, z, face, { scale = wide / 22, seat = "centre" })
		-- o.hang = ceiling height: a fat mount from the top of the bezel up to the ceiling
		if o.hang and bsz then H.block("Scenery", "ScreenMount", x - 0.8, x + 0.8, y + bsz.Y / 2 - 0.2, o.hang, z - 0.8, z + 0.8, "5b6478", nil, { ghost = true }) end
		local lines = { { md.title, "ffffff", "L", 0.5 }, { status, if md.soon then "c8c8dc" else md.color, "F", 0.26 }, { if md.soon then "we checked. it isn't." else "step on a side to queue", "c8c8dc", "F", 0.16 } }
		-- o.both = the same on the back, as its own thin plate just proud of the bezel's back (the bezel is solid)
		if o.both then
			local out = 0.9 * wide / 22 + 0.2
			H.text("SignBack_" .. id, lines, wide, wide / 2, x - f.X * out, y, z - f.Z * out, face + 180, { plate = "0a0c16", thick = 0.2, pps = 24, flush = true })
		end
		return H.text("Sign_" .. id, lines, wide, wide / 2, x + f.X * 0.12, y, z + f.Z * 0.12, face, { plate = "0a0c16", thick = 0.5, pps = 24 })
	end

	function H.spawns(list)
		for _, s in list do
			table.insert(H.spawnAt, s)
			local p = Instance.new("Part")
			p.Name = "HubSpawn"; p.Size = Vector3.new(2, 0.2, 2); p.Transparency = 1; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			p.CFrame = CFrame.lookAt(H.w(s[1], 0.1, s[2]), H.w(s[1], 0.1, s[2] - 10))
			p.Parent = root.Spawns
		end
		-- where a visitor from another hub lands: the same spots, kept with the live hub's door markers
		local f = Instance.new("Folder"); f.Name = name .. "_Arrive"
		for i, s in list do
			if i <= 4 then
				local p = Instance.new("Part")
				p.Name = "Arrive"; p.Size = Vector3.new(2, 0.2, 2); p.Transparency = 1; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
				p.CFrame = CFrame.lookAt(H.w(s[1], 0.1, s[2]), H.w(s[1], 0.1, s[2] - 10))
				p.Parent = f
			end
		end
		f.Parent = hub.Doors
	end

	-- a box you walk into to be taken somewhere. land = the name of a marker folder in Hub.Doors, or "@TrainSpawns"
	function H.trigger(suffix, x0, x1, y0, y1, z0, z1, land, say)
		local p = Instance.new("Part")
		p.Name = name .. "_" .. suffix; p.Anchored = true; p.Transparency = 1; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Size = Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0))
		p.Position = H.w((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		p:SetAttribute("Land", land); p:SetAttribute("Say", say)
		p.Parent = hub.Doors
		return p
	end

	-- the way to training: a chunky door frame in a wall, a red laser field to walk into, a fat head over the frame with
	-- the plate on it. o.frame = { oldHex = newHex } recolours the frame, o.head = the head's colour, o.plate = the plate's
	function H.trainingDoor(x, z, face, words, o)
		o = o or {}
		local f = front(face)
		local r = Vector3.new(f.Z, 0, -f.X)
		local cmap = { [PINK] = GREEN }
		for k, v in o.frame or {} do cmap[k] = v end
		H.put("hb_portal", "TrainingPortal", x + f.X * 1.2, 0, z + f.Z * 1.2, face, { color = cmap })
		local lz = Instance.new("Part")
		lz.Name = "LaserField"; lz.Anchored = true; lz.Size = Vector3.new(14, 16.6, 0.3); lz.Material = Enum.Material.Neon
		lz.Color = Color3.fromHex("ff2a3a"); lz.Transparency = 0.8; lz.CanCollide = false; lz.CastShadow = false
		lz.CFrame = CFrame.new(H.w(x + f.X * 0.4, 8.3, z + f.Z * 0.4)) * CFrame.Angles(0, math.rad(face), 0)
		lz.Parent = root.Scenery
		local back = Instance.new("Part")
		back.Name = "LaserVoid"; back.Anchored = true; back.Size = Vector3.new(14, 16.6, 0.4); back.Color = Color3.fromHex("2a0c16")
		back.Material = Enum.Material.SmoothPlastic; back.CFrame = lz.CFrame * CFrame.new(0, 0, -0.5); back.Parent = root.Scenery
		-- six fat laser bars across the doorway over a faint red haze (one flat red sheet read as a blank panel)
		for i = 1, 6 do
			local b = Instance.new("Part")
			b.Name = "LaserBar"; b.Shape = Enum.PartType.Cylinder; b.Anchored = true; b.Size = Vector3.new(14, 0.55, 0.55)
			b.Material = Enum.Material.Neon; b.Color = Color3.fromHex("ff2a3a"); b.CanCollide = false; b.CanQuery = false; b.CanTouch = false; b.CastShadow = false
			b.CFrame = lz.CFrame * CFrame.new(0, -8.3 + i * 2.37, 0.15)
			b.Parent = root.Scenery
		end
		H.lamp(x + f.X * 5, 8, z + f.Z * 5, 18, 1.0, "ff5a5a")
		local hc = Vector3.new(x, 0, z) + f * 1.475
		local ex, ez = math.abs(r.X) * 8.6 + math.abs(f.X) * 1.475, math.abs(r.Z) * 8.6 + math.abs(f.Z) * 1.475
		H.block("Scenery", "DoorHead", hc.X - ex, hc.X + ex, 19.6, 22.8, hc.Z - ez, hc.Z + ez, o.head or "a4aab8")
		H.text("TrainingPlate", { { words[1], GREEN, "L", 0.6 }, { words[2], "ffffff", "F", 0.34 } }, 16, 2.6, x + f.X * 3.1, 21.2, z + f.Z * 3.1, face, { plate = o.plate })
		local c = Vector3.new(x, 0, z) + f * 3.2
		local hx, hz = math.abs(r.X) * 6.5 + math.abs(f.X) * 1.6, math.abs(r.Z) * 6.5 + math.abs(f.Z) * 1.6
		H.trigger("ToTraining", c.X - hx, c.X + hx, 0, 14, c.Z - hz, c.Z + hz, "@TrainSpawns", "TRAINING GROUND")
	end

	-- a glowing floor disc that takes you to another hub
	function H.disc(suffix, x, z, label, sub, land, say, hex)
		local p = Instance.new("Part")
		p.Name = "HubDisc"; p.Shape = Enum.PartType.Cylinder; p.Anchored = true; p.Size = Vector3.new(0.3, 8, 8)
		p.CFrame = CFrame.new(H.w(x, 0.15, z)) * CFrame.Angles(0, 0, math.pi / 2)
		p.Material = Enum.Material.Neon; p.Color = Color3.fromHex(hex or GREEN):Lerp(Color3.new(0, 0, 0), 0.2); p.CanCollide = false; p.CastShadow = false
		p.Parent = root.Scenery
		-- a fat post on a foot, a pale board, the words on both sides of it
		H.block("Scenery", "DiscPost", x - 0.7, x + 0.7, 0.3, 4.8, z - 0.7, z + 0.7, "a4aab8", nil, { ghost = true })
		H.block("Scenery", "DiscFoot", x - 1.3, x + 1.3, 0.3, 0.9, z - 1.3, z + 1.3, "5b6478", nil, { ghost = true })
		H.block("Scenery", "DiscBoard", x - 4.9, x + 4.9, 4.7, 7.7, z - 0.35, z + 0.35, "a4aab8", nil, { ghost = true })
		H.text("DiscSign", { { label, hex or GREEN, "L", 0.6 }, { sub, "ffffff", "F", 0.34 } }, 9, 2.6, x, 6.2, z, 0, { both = true, thick = 0.9 })
		table.insert(H.discAt, { x, z })
		H.trigger(suffix, x - 2.6, x + 2.6, 0, 6, z - 2.6, z + 2.6, land, say)
	end

	function H.zone(x0, x1, z0, z1, h, look)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Transparency = 1; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Size = Vector3.new(x1 - x0 + 30, h + 60, z1 - z0 + 30)
		p.Position = H.w((x0 + x1) / 2, h / 2, (z0 + z1) / 2)
		p:SetAttribute("Look", look)
		p.Parent = lz
	end

	-- the discs every show hub has by its spawn: on to the next one, and back to Hub 1
	-- (spread = how far each disc is from x: wide enough that their sign boards are not between a new arrival's camera and the room)
	function H.tourDiscs(x, z, spread)
		spread = spread or 7
		local i = table.find(L.ORDER, name)
		local nxt = L.ORDER[i % #L.ORDER + 1]
		H.disc("ToNext", x - spread, z, "NEXT HUB", L.TITLE[nxt], nxt .. "_Arrive", L.TITLE[nxt], YEL)
		H.disc("ToHub1", x + spread, z, "HUB 1", "THE ROTUNDA", "HubArrive", "BACK TO THE ROTUNDA", PINK)
	end

	-- an info screen: a chunky bezel with words in it
	function H.screen(sname, lines, x, y, z, face, wide)
		local f = front(face)
		H.put("hb_screen", sname .. "Bezel", x, y, z, face, { scale = wide / 22, seat = "centre" })
		return H.text(sname, lines, wide, wide / 2, x + f.X * 0.12, y, z + f.Z * 0.12, face, { plate = "0a0c16", thick = 0.5, pps = 24 })
	end
	-- an invisible ramp under a staircase: `rise` up over `run`, climbing toward `face`
	function H.ramp(x, z, face, width, rise, run, y0)
		local w = Instance.new("WedgePart")
		w.Name = "StairRamp"; w.Size = Vector3.new(width, rise, run); w.Anchored = true; w.Transparency = 1; w.CastShadow = false
		w.CFrame = CFrame.new(H.w(x, (y0 or 0) + rise / 2, z)) * CFrame.Angles(0, math.rad(face), 0)
		w.CanCollide = boxSrc.CanCollide; w.CanQuery = boxSrc.CanQuery; w.CanTouch = boxSrc.CanTouch; w.CollisionGroup = boxSrc.CollisionGroup
		w.Parent = root.Collision
	end
	-- flat floor paint
	function H.paint(x0, x1, z0, z1, hex, o)
		return H.block("Scenery", "Hazard", x0, x1, 0.02, 0.08, z0, z1, hex or YEL, (o and o.mat) or nil, { ghost = true, rot = o and o.rot })
	end

	function H.done()
		root.Parent = lab
		local miss = {}
		for k, v in H.missing do table.insert(miss, k .. " x" .. v) end
		table.sort(miss)
		-- a spawn point too near a travel disc sends people away when they step back
		local near = math.huge
		for _, s in H.spawnAt do for _, d in H.discAt do
			near = math.min(near, math.max(math.abs(s[1] - d[1]) - 2.6, math.abs(s[2] - d[2]) - 2.6, 0))
		end end
		local warn = if near < 3.9 then (" | WARNING: a spawn point is %.1f studs from a travel disc (keep 4)"):format(near) else ""
		return ("%s: %d things built%s%s"):format(name, H.count, #miss > 0 and (" | not in the library yet: " .. table.concat(miss, ", ")) or "", warn)
	end
	return H
end
L.newHub = newHub
L.BUILD = {}

function L.build(name)
	local fn = L.BUILD[name]
	if not fn then return "no such hub: " .. tostring(name) end
	return fn(newHub(name))
end
function L.buildAll()
	local out = {}
	for _, n in L.ORDER do table.insert(out, L.build(n)); task.wait() end
	table.insert(out, L.build("Hub1_Tour"))
	return table.concat(out, "\n")
end

-- ------------------------------------------------------------------ Hub 5: THE DEPOT
-- a delivery depot. six loading bays along the north wall, six modes; the warehouse kit (wh_*) and the depot kit (dp_*)
L.BUILD.Hub5_Depot = function(H)
	-- (smooth walls: Metal gave no flat colour in this light and photographed black. a paler ceiling, so the top of the room is not a void)
	H.room("Depot", -78, 78, -60, 60, 36, { wall = "7c8090", floor = "54565c", floorMat = Enum.Material.Concrete, ceil = "767b8c" })
	-- nothing in here is painted near-black: the kit's darkest paints are lifted to slate
	local LIFT = { ["17141f"] = "2e3140", ["1f2230"] = "2e3140", ["120818"] = "2e3140", ["1f2a3a"] = "3a4a66" }
	local function lift(more) local t = table.clone(LIFT); for k, v in more or {} do t[k] = v end; return t end
	-- a fat safety band round the walls
	H.block("Scenery", "Hazard", -78, 78, 8, 9.6, -60, -59.8, YEL, nil, { ghost = true }); H.block("Scenery", "Hazard", -78, 78, 8, 9.6, 59.8, 60, YEL, nil, { ghost = true })
	H.block("Scenery", "Hazard", -78, -77.8, 8, 9.6, -60, 60, YEL, nil, { ghost = true }); H.block("Scenery", "Hazard", 77.8, 78, 8, 9.6, -60, 60, YEL, nil, { ghost = true })
	-- steel: three girder lines with light panels under every girder, paler than the ceiling they hang under
	for _, z in { -28, 4, 36 } do
		for _, cx in { -52, 0, 52 } do
			H.put("wh_girder", "Girder", cx, 36, z, 0, { scale = 0.93, seat = "top", color = { ["2e3140"] = "8a93a8", ["5b6478"] = "a4aab8" } })
			-- (the twelve panels over the aisle, the vans and the pads cast shadows, each a tighter and stronger cone, so things sit on
			-- the floor with a shadow; the six along the side walls are a soft wash with no shadows, for phones)
			for _, dx in { -13, 13 } do
				local inner = math.abs(cx + dx) < 45
				H.lamp(cx + dx, 29.9, z, if inner then 50 else 56, if inner then 3.0 else 1.4, "f6f1e6", { spot = true, shadows = inner, angle = if inner then 95 else 120 })
			end
		end
		-- columns on the south line only (the two rows further north stood between the spawn and four of the six bays)
		if z == 36 then
			for _, x in { -26, 26 } do H.put("wh_column", "Column", x, 0, z, 0, { scale = 0.89, solid = Vector3.new(4.2, 32, 4.2), color = lift({ ["2e3140"] = "5b6478", ["5b6478"] = "8a93a8" }) }) end
			-- pale rafters across the girders (the three middle ones stop at the north girder, short of the name)
			for _, x in { -52, -26, 0, 26, 52 } do H.block("Scenery", "Rafter", x - 1.2, x + 1.2, 34.2, 36, if math.abs(x) == 52 then -60 else -26, 60, "a4aab8", nil, { ghost = true }) end
			-- (and shallow ones on over the bays, above the top of the name plate, so the ceiling there is not a bare slab)
			for _, x in { -26, 0, 26 } do H.block("Scenery", "Rafter", x - 1.2, x + 1.2, 35.2, 36, -60, -26, "a4aab8", nil, { ghost = true }) end
		end
	end
	-- the six bays
	for i, id in { "1v1", "1v1v1", "2v2", "3v3", "4v4", "5v5" } do
		local x = -62.5 + (i - 1) * 25
		local md = H.M[id]
		local bay = H.put("dp_dockbay", "DockBay", x, 0, -60, 0, { back = true, color = LIFT })
		-- (the dock plate's diamond pattern read as speckle close up: smooth, like everything else)
		if bay then for _, p in bay:GetDescendants() do if p:IsA("BasePart") and p.Material == Enum.Material.DiamondPlate then p.Material = Enum.Material.SmoothPlastic end end end
		H.put("wh_rollup", "BayDoor", x, 0, -60, 0, { back = true, scale = 0.82, color = LIFT }) -- (fills the 18-high opening up to the header)
		H.pad(id, x, -43, 180, 20, 14)
		H.countScreen(id, x, 9.4, -57.7, 0, 15)
		H.modeSign(id, x, 24.2, -59.7, 0, { scale = 1.5 })
		H.text("BayNumber", { { string.char(64 + i), YEL, "L", 1 } }, 4.6, 2.0, x, 19.8, -57.85, 0, { clear = true }) -- (bays are lettered A to F: numbers argued with the mode names. just proud of the header plate, whose face is z -57.75)
		if not md.soon then H.lamp(x, 4, -43, 24, 0.8, md.color) end -- the pad's own glow, low over it (the closed pad does not glow, so it has no lamp)
		H.lamp(x, 17.7, -56.9, 24, 0.9, "f6f1e6", { spot = true }) -- a real light under the header's light bar
		-- you stop at the bay door, not inside it
		H.solid("BayBox", Vector3.new(24, 21, 3), CFrame.new(H.w(x, 10.5, -58.5)))
		for _, s in { -1, 1 } do H.solid("BumperBox", Vector3.new(2.4, 3, 1.5), CFrame.new(H.w(x + s * 10.75, 1.5, -57.35))) end -- (the two bumper stacks, measured: they end at z -56.6)
	end
	-- (the name as big as the wall over the bay signs allows, on a yellow-edged board; pps 18 lets the letters grow past the 100 px cap)
	H.block("Scenery", "NameBoard", -31, 31, 27.2, 36, -60, -59.85, YEL, nil, { ghost = true })
	H.text("Name", { { "JANKFIRE DEPOT", YEL, "L", 0.72 }, { "we deliver. usually.", "ffffff", "F", 0.24 } }, 60.8, 8, 0, 31.6, -59.7, 0, { plate = "2e3140", pps = 18 })
	-- and again where a new arrival can read it: one word, hung low under the middle girder between the two notice screens
	-- (under the girder's light strip and over the wall name as seen from the spawn), with the same word on the back for the bays
	H.block("Scenery", "NameNearBoard", -17.1, 17.1, 21, 27.8, 6.05, 6.2, YEL, nil, { ghost = true })
	H.text("NameNear", { { "JANKFIRE", YEL, "L", 1 } }, 33, 6.4, 0, 24.4, 6.35, 0, { plate = "2e3140", pps = 18 })
	H.text("NameNearBack", { { "JANKFIRE", YEL, "L", 1 } }, 33, 6.4, 0, 24.4, 5.9, 180, { plate = "2e3140", pps = 18 })
	for _, x in { -12, 12 } do H.block("Scenery", "NameStrap", x - 0.7, x + 0.7, 27.8, 33, 6.05, 7.45, "5b6478", nil, { ghost = true }) end
	-- floor paint: the centre aisle and the line in front of the bays
	H.paint(-10.3, -9.7, -34, 42); H.paint(9.7, 10.3, -34, 42); H.paint(-76, 76, -34.6, -34)
	for _, z in { 30, 14, -2, -18 } do
		for _, s in { -1, 1 } do H.paint(-0.5, 0.5, z - 3, z + 3, "f4f8ff", { rot = CFrame.Angles(0, s * math.rad(35), 0) * CFrame.new(s * 1.6, 0, 0) }) end
	end
	-- the mezzanine along the west wall, with the dispatch office on it
	for _, zc in { 18, 46 } do
		H.put("wh_mezz", "Mezzanine", -78, 0, zc, 90, { back = true, color = { ["17141f"] = "3a4052", ["2e3140"] = "4a5266", ["5b6478"] = "8a93a8" } }) -- (a deck you can see the underside of, not a black slab; posts paler than the wall behind them)
		for _, dz in { -12, 12 } do H.solid("MezzPost", Vector3.new(2.6, 13, 2.6), CFrame.new(H.w(-63.8, 6.5, zc + dz))) end
		H.lamp(-69, 12.1, zc, 20, 1.2, "ffe9c8") -- (under the deck's own light strip)
	end
	H.solid("MezzDeck", Vector3.new(16, 1.2, 56), CFrame.new(H.w(-70, 13.4, 32)))
	H.put("wh_stairs", "MezzanineStairs", -51, 8.44, 50, 90, { seat = "centre" })
	H.ramp(-51, 50, -90, 8, 14, 21)
	-- (the rails stop you: a box on each, and on the one across the north end)
	for _, z in { 11, 25, 39 } do
		H.put("wh_rail", "MezzanineRail", -62.4, 14.02, z, 90, { color = LIFT })
		H.solid("RailBox", Vector3.new(0.8, 4.7, 14), CFrame.new(H.w(-62.4, 16.4, z)))
	end
	H.put("wh_rail", "MezzanineRail", -70, 14.02, 4.5, 0, { color = LIFT }); H.solid("RailBox", Vector3.new(14, 4.7, 0.8), CFrame.new(H.w(-70, 16.4, 4.5)))
	H.put("dp_office", "Office", -78, 14.02, 18, 90, { back = true, solid = true, color = LIFT })
	H.text("OfficeSign", { { "DISPATCH", YEL, "L", 1 } }, 11.4, 1.8, -66.28, 22.62, 18, 90, { clear = true }) -- (just proud of the sign plate, whose face is x -66.2)
	H.lamp(-65.4, 19, 18, 18, 0.7, "ffe9b8") -- the lit windows spill onto the deck
	-- (the south end of the deck is not left bare: a stack of crates in its corner, and one that closes the gap between the stair
	-- head and the south wall, where there is no rail)
	H.put("wh_crate", "Crate", -64.8, 14.02, 57.2, 6, { solid = true })
	H.put("wh_crate", "Crate", -74.6, 14.02, 56.6, 3, { solid = true }); H.put("wh_crate", "Crate", -74.4, 14.02, 50.9, -8, { solid = true }); H.put("wh_crate", "Crate", -74.5, 19.12, 54, 14, { solid = true })
	-- under the deck: the break corner
	H.put("hb_vending", "Vending", -78, 0, 37, 90, { back = true, solid = true, color = lift({ [PINK] = CYAN }) })
	H.put("hb_vending", "Vending", -78, 0, 41, 90, { back = true, solid = true, color = lift({ [PINK] = YEL }) })
	H.put("bc_fridge", "Fridge", -76, 0, 44.5, 90, { solid = true, color = LIFT })
	H.put("bc_watercooler", "WaterCooler", -76.4, 0, 33.5, 90, { color = LIFT })
	H.put("bc_arcade", "Arcade", -78, 0, 30, 90, { back = true, solid = true, color = LIFT })
	H.text("BreakSign", { { "BREAK AREA", CYAN, "L", 0.56 }, { "breaks are 4 minutes. reading this took 1.", "ffffff", "F", 0.34 } }, 14, 2.8, -77.8, 9.4, 18, 90)
	-- (two fat benches under the sign and two canteen tables, in the kit's own flat plastic; the machines stand in one run)
	for _, z in { 12, 23 } do H.put("st_bench", "Bench", -78, 0, z, 90, { back = true, solid = true, color = { ["2e3140"] = "5b6478" } }) end
	H.put("fc_table", "Table", -68, 0, 18, 0, { solid = true }); H.put("fc_table", "Table", -70, 0, 52, 0, { solid = true })
	-- racking up the east wall with the conveyor running in front of it; racking along the south wall and the north end of the west wall
	for _, z in { -24, -8, 8, 24, 40 } do H.put("wh_rack", "Rack", 78, 0, z, -90, { back = true, solid = true, color = LIFT }) end
	for _, z in { -20, 0, 20, 40 } do H.put("dp_conveyor", "Conveyor", 70.2, 0, z, -90, { solid = true, color = LIFT }) end
	-- the depot's own idea, overhead: a second conveyor carries parcels from the dispatch office across the whole room, on a beam
	-- hung from the ceiling (over the vans and the forklift, between the girder lines, above every lamp's cone)
	for _, cx in { -52, -32, -12, 8, 28, 48, 68 } do H.put("dp_conveyor", "ConveyorHigh", cx, 25, 20, 0, { color = LIFT }) end
	H.block("Scenery", "ConveyorBeam", -62, 78, 24.2, 25, 17.6, 22.4, "a4aab8", nil, { ghost = true })
	-- (it comes out of a fat hood on the front of the dispatch office's roof and leaves through another over the east racking)
	H.block("Scenery", "Chute", -70, -60.2, 24.2, 32.6, 16.2, 23.8, "5b6478", nil, { ghost = true }); H.block("Scenery", "ChuteLip", -60.6, -59.8, 31, 32.6, 16.2, 23.8, YEL, nil, { ghost = true })
	H.block("Scenery", "Chute", 73.6, 78, 24.2, 32.6, 16.2, 23.8, "5b6478", nil, { ghost = true }); H.block("Scenery", "ChuteLip", 73.2, 74, 31, 32.6, 16.2, 23.8, YEL, nil, { ghost = true })
	for _, x in { -61.2, -42, -22, -2, 18, 38, 58, 77.2 } do
		H.block("Scenery", "ConveyorCradle", x - 0.8, x + 0.8, 23.4, 24.2, 16.3, 23.7, "a4aab8", nil, { ghost = true })
		for _, z in { 17, 23 } do H.block("Scenery", "ConveyorDrop", x - 0.8, x + 0.8, 23.4, 36, z - 0.7, z + 0.7, "a4aab8", nil, { ghost = true }) end
	end
	for _, z in { -24, -8 } do H.put("wh_rack", "Rack", -78, 0, z, 90, { back = true, solid = true, color = LIFT }) end
	-- (three along the south wall, starting clear of the HUB 1 disc; crates fill the corner they leave)
	for _, x in { 30, 46.4, 62.8 } do H.put("wh_rack", "Rack", x, 0, 60, 180, { back = true, solid = true, color = LIFT }) end
	H.put("wh_crate", "Crate", 75, 0, 57, 4, { solid = true }); H.put("wh_crate", "Crate", 75, 0, 51.4, -4, { solid = true }); H.put("wh_crate", "Crate", 75, 5.1, 54.3, 12, { solid = true })
	-- (west of the staff door the wall stays low, so the training door shows from the spawn: the NEXT HUB disc, and a plate that
	-- points at the door. its words say which door, because the disc under it is not the way to training)
	H.text("NextDoorSign", { { "TRAINING IS NEXT DOOR", GREEN, "L", 0.58 }, { "literally. the red one. not the disc.", "ffffff", "F", 0.34 } }, 15, 2.8, -18, 14.2, 59.7, 180)
	-- vans, the forklift, pallet trucks, crates
	H.put("wh_van", "Van", -44, 0, 2, 176, { solid = true, color = LIFT })
	H.put("wh_van", "Van", 46, 0, 0, 184, { solid = true, color = lift({ [PINK] = CYAN }) }) -- (parked well short of the bay line, so the way east to bays E and F stays wide)
	H.put("wh_van", "Van", 50, 0, 38, 86, { solid = true, color = lift({ [PINK] = GREEN }) }) -- a third, nose to the conveyor
	H.paint(38, 62, 30.6, 31.2); H.paint(38, 62, 44.8, 45.4)
	H.paint(-51, -50.4, -10, 14); H.paint(-37.6, -37, -10, 14); H.paint(39, 39.6, -12, 12); H.paint(52.4, 53, -12, 12)
	local FORK = { ["17141f"] = "5b6478", ["2e3140"] = "8a93a8" } -- (slate and steel, not near-black; the east one stands clear of the sightline to bay F)
	H.put("wh_forklift", "Forklift", 32, 0, 24, 130, { solid = true, color = FORK }); H.put("wh_forklift", "Forklift", -49, 0, 28, 40, { solid = true, color = FORK }) -- (the second fills the floor in front of the mezzanine)
	H.put("dp_palletjack", "PalletTruck", 16, 0, 12, 200, { solid = true, color = LIFT }); H.put("dp_palletjack", "PalletTruck", -18, 0, -2, 160, { solid = true, color = LIFT }) -- (clear of the way west to bays A and B)
	for _, s in { { 54, 20 }, { -30, 28 } } do
		H.put("wh_crate", "Crate", s[1], 0, s[2], 4, { solid = true }); H.put("wh_crate", "Crate", s[1] + 5.6, 0, s[2] - 0.3, -6, { solid = true }); H.put("wh_crate", "Crate", s[1] + 2.7, 5.1, s[2], 20, { solid = true })
	end
	-- the spawn by the staff entrance, the way to training, the tour discs
	H.put("wh_rollup", "StaffDoor", 0, 0, 60, 180, { back = true, scale = 0.55, color = LIFT })
	H.text("StaffSign", { { "STAFF ENTRANCE", "ffffff", "L", 0.6 }, { "you work here now.", "c8c8dc", "F", 0.34 } }, 14, 2.4, 0, 14.2, 59.7, 180)
	-- (the incident board now hangs big on the back of the news screen, where the bays can read it; this one, between the two
	-- tour discs, says what the discs are. it goes when the discs go)
	H.screen("OtherHubs", { { "OTHER HUBS", YEL, "L", 0.3 }, { "stand on a disc.", "ffffff", "F", 0.3 }, { "you will be shipped. returns accepted.", "c8c8dc", "F", 0.2 } }, 0, 23.3, 59.25, 180, 18)
	local sp = {}
	for _, z in { 42, 46 } do for _, x in { -6, -2, 2, 6 } do table.insert(sp, { x, z }) end end -- (the tour discs are 16 studs off to either side, behind)
	H.spawns(sp)
	H.trainingDoor(-36, 60, 180, { "TRAINING", "staff only. you are staff." })
	H.lamp(-36, 16.5, 58.2, 26, 1.1, "f6f1e6", { spot = true, angle = 150 }) -- a real light at the door frame's white bar (this corner was the dimmest)
	-- it is behind you when you spawn, so the floor shows the way: a green line off the aisle, and a sign where it starts
	H.paint(-34.8, -10.3, 39.7, 40.3, GREEN); H.paint(-34.8, -34.2, 40.3, 56.6, GREEN)
	for _, x in { -18, -28 } do
		for _, s in { -1, 1 } do H.paint(x - 2.6, x + 2.6, 39.6, 40.4, GREEN, { rot = CFrame.Angles(0, -s * math.rad(35), 0) * CFrame.new(0, 0, s * 1.4) }) end
	end
	for _, s in { -1, 1 } do H.paint(-34.9, -34.1, 45.4, 50.6, GREEN, { rot = CFrame.Angles(0, -s * math.rad(35), 0) * CFrame.new(s * 1.4, 0, 0) }) end
	H.block("Scenery", "SignBase", -20.1, -17.1, 0, 0.7, 35.5, 38.5, "2e3140"); H.block("Scenery", "SignPost", -19.2, -18, 0.7, 5.2, 36.4, 37.6, "5b6478")
	H.text("TrainingSign", { { "TRAINING", GREEN, "L", 0.6 }, { "follow the green line. it's green.", "ffffff", "F", 0.34 } }, 9.4, 2.6, -18.6, 6.5, 37, 0, { both = true, thick = 0.6 })
	H.tourDiscs(0, 55.5, 16) -- (spread wide: their sign boards are out of a new arrival's view)
	-- two notice screens strapped to the middle girder, facing the spawn up the aisle (high enough that, from the spawn, they sit
	-- over the bay signs behind them and hide none). each has a second screen on its back, for people coming back from the bays
	H.screen("Tips", { { "DEPOT NOTICE", CYAN, "L", 0.24 }, { "stand on a colour. that's the whole skill.", "ffffff", "F", 0.40 }, { "training is behind you.", GREEN, "F", 0.36 } }, -26, 21.9, 6.62, 0, 14)
	H.screen("News", { { "JANK NEWS 24", "ff3b3b", "L", 0.3 }, { "PARCEL MARKED FRAGILE ARRIVES FINE. STAFF SUSPICIOUS.", YEL, "F", 0.6 } }, 26, 21.9, 6.62, 0, 14)
	H.screen("TipsBack", { { "TRAINING", GREEN, "L", 0.4 }, { "far end, on the right. red door.", "ffffff", "F", 0.4 } }, -26, 21.9, 5.4, 180, 14)
	H.screen("NewsBack", { { "DAYS SINCE LAST INCIDENT", YEL, "L", 0.26 }, { "0", "ffffff", "L", 0.5 }, { "it was you. it's fine.", "c8c8dc", "F", 0.18 } }, 26, 21.9, 5.4, 180, 14)
	-- (fat straps up the girder's south face for the front screens, and a hanger under the girder for each back one)
	for _, x in { -31.5, -20.5, 20.5, 31.5 } do
		H.block("Scenery", "ScreenStrap", x - 0.7, x + 0.7, 26.8, 33, 6.05, 7.45, "5b6478", nil, { ghost = true })
		H.block("Scenery", "ScreenStrap", x - 0.7, x + 0.7, 26.8, 30.2, 4.7, 6.05, "5b6478", nil, { ghost = true })
	end
	-- (the hanging screens cast no shadow: under the shadow lamps theirs fell as loose dark blobs on the aisle floor)
	for _, n in { "TipsBezel", "NewsBezel", "TipsBackBezel", "NewsBackBezel" } do
		local b = H.root.Scenery:FindFirstChild(n)
		if b then for _, p in b:GetDescendants() do if p:IsA("BasePart") then p.CastShadow = false end end end
	end
	H.zone(-78, 78, -60, 60, 36, "lab_depot")
	return H.done()
end

-- ------------------------------------------------------------------ Hub 2: THE PLATFORM
-- an underground station. a concourse (spawn), ticket gates, an island platform between the PINK LINE and the CYAN LINE;
-- you queue in the boarding zone in front of a train door. kit st_*
L.BUILD.Hub2_Platform = function(H)
	local TILE, FLOOR, STEEL, PALE, SLATE = "c9cdd8", "6e778c", "a4aab8", "dfe3ec", "5b6478"
	local Neon, Tiles = Enum.Material.Neon, Enum.Material.CeramicTiles
	-- floor lines are Neon (plain paint washes out to pastel under these lamps) and a step darker than the pad plates,
	-- so the pads stay the brightest things on the floor. SHUT is the flat grey of a closed pad
	local LPINK, LCYAN, LGREEN, SHUT = "7a2868", "1a727c", "3d7c27", "9197a6"
	-- the lamps. nine of them cast shadows (KEY): the bars over the platform walk, over the side aisles and over the
	-- spawn, and one under the doorway girder. each owns its own patch of floor, so what stands there has one clear
	-- shadow. the rest only fill (FILL), weak and short, or every shadow is washed out by the lamp next door
	local KEY, FILL = { spot = true, shadows = true, angle = 110 }, { spot = true, angle = 110 }
	-- nothing in this station is painted near-black: the kit's dark trim becomes slate, its darkest parts the sign-plate navy
	local function tint(extra)
		local t = { ["2e3140"] = SLATE, ["17141f"] = "2e3140" }
		for k, v in extra or {} do t[k] = v end
		return t
	end
	-- the same for what the shared helpers build: a screen's bezel becomes slate and its face the sign-plate navy
	-- (the helpers paint a screen face 0a0c16), and so do a pad's base and the back of the training doorway
	local NAVY = Color3.fromHex("2e3140")
	local function slate(mname, face)
		local m = H.root.Scenery:FindFirstChild(mname)
		if m then
			for _, p in m:GetDescendants() do
				if p:IsA("BasePart") and p.Name:find("_2e3140", 1, true) then p.Color = Color3.fromHex(SLATE) end
			end
		end
		if face then face.Color = NAVY end
	end
	-- a straight stroke of floor paint from (ax, az) to (bx, bz)
	local function stroke(ax, az, bx, bz, wide, hex, mat)
		local dx, dz = bx - ax, bz - az
		local len = math.sqrt(dx * dx + dz * dz)
		local cx, cz = (ax + bx) / 2, (az + bz) / 2
		return H.block("Scenery", "Hazard", cx - len / 2, cx + len / 2, 0.02, 0.08, cz - wide / 2, cz + wide / 2, hex, mat, { ghost = true, rot = CFrame.Angles(0, math.atan2(-dz, dx), 0) })
	end
	-- a train car. its windows are pale glass, not lamps: glowing, they were brighter than the pads right in front of them
	local function car(cname, x, y, z, face, o)
		local m = H.put("st_train", cname, x, y, z, face, o)
		if m then
			for _, p in m:GetDescendants() do
				if p:IsA("BasePart") and p.Name:find("_ffe9b8", 1, true) then p.Material = Enum.Material.SmoothPlastic; p.Color = Color3.fromHex("a9bcdc") end
			end
		end
		return m
	end
	-- the floor is mid grey tiles (a pale floor burns out to flat white under the strip lights)
	H.room("Concourse", -50, 50, 16, 66, 26, { wall = TILE, floor = FLOOR, floorMat = Tiles, ceil = "8a90a0", open = { N = { { -17.5, 17.5, 20 } } } })
	H.room("Hall", -38, 38, -92, 16, 26, { wall = TILE, ceil = "8a90a0", noFloor = true, skip = { S = true } })
	-- (the platform stops where the concourse floor starts, so the two tiled tops never share a plane)
	H.block("Shell", "Platform", -17.5, 17.5, -4, 0, -94, 14, FLOOR, Tiles)
	H.block("Shell", "TrackBed", -40, -17.5, -4, -2, -94, 16, "4a4f60"); H.block("Shell", "TrackBed", 17.5, 40, -4, -2, -94, 16, "4a4f60")
	-- the hall's walls start at platform height: close the 2 studs under them, down to the track bed
	H.block("Shell", "PitWall", -40, -38, -2, 0, -94, 16, "565b6b"); H.block("Shell", "PitWall", 38, 40, -2, 0, -94, 16, "565b6b")
	H.block("Shell", "PitWall", -38, -17.5, -2, 0, -94, -92, "565b6b"); H.block("Shell", "PitWall", 17.5, 38, -2, 0, -94, -92, "565b6b")
	for _, s in { -1, 1 } do
		local line = if s < 0 then PINK else CYAN
		-- the line's colour as a fat band on its wall, the yellow strip at the platform edge, two rails
		H.block("Scenery", "Hazard", s * 37.8, s * 38, 11, 13.4, -92, 16, line, nil, { ghost = true })
		-- (the edge strips are lower than a pad's base, top 0.08, so a pad covers them cleanly where it crosses them)
		H.block("Scenery", "Hazard", s * 15.8, s * 17.3, 0.02, 0.06, -92, 16, YEL, nil, { ghost = true })
		H.block("Scenery", "Hazard", s * 14.9, s * 15.5, 0.02, 0.06, -92, 16, "3d4358", nil, { ghost = true })
		for _, rx in { 20.5, 25.5 } do H.block("Scenery", "Rail", s * rx - 0.3, s * rx + 0.3, -2, -1.6, -92, 16, "8a909e", nil, { ghost = true }) end
		-- three cars, the tunnel they came out of, the buffer stop they stop at (its beam faces the train)
		for _, zc in { -68, -37, -6 } do car("Train", s * 23, -2, zc, -s * 90, { solid = true, color = tint({ [PINK] = line }) }) end
		H.put("st_tunnel", "Tunnel", s * 25.5, -2, -92, 0, { back = true, scale = 0.9, color = tint() })
		H.block("Scenery", "TunnelDark", s * 25.5 - 7.2, s * 25.5 + 7.2, -2, 9, -92, -91.8, "262d48", nil, { ghost = true })
		H.put("st_buffer", "Buffer", s * 23, -2, 12.4, 180, { solid = true })
		for _, z in { -83.5, -52.5, -21.5, 9.5 } do H.put("hb_pier", "Pier", s * 38, -2, z, -s * 90, { back = true, scale = 0.583, color = tint() }) end
	end
	-- the six boarding zones: mode sign and count screen hang over each
	local zones = { { "1v1", -1, -6 }, { "2v2", -1, -37 }, { "3v3", -1, -68 }, { "1v1v1", 1, -6 }, { "4v4", 1, -37 }, { "5v5", 1, -68 } }
	-- in this station a mode wears its line's colour on every sign (the board used to print PINK LINE rows in cyan)
	for _, zn in zones do
		local md = H.M[zn[1]]
		if not md.soon then md.color = if zn[2] < 0 then PINK else CYAN end
	end
	for _, zn in zones do
		local id, s, zc = zn[1], zn[2], zn[3]
		local md = H.M[id]
		local base = H.pad(id, s * 12.5, zc, s * 90, 26, 9):FindFirstChild("Base")
		if base then base.Color = NAVY end
		H.put("hb_hangsign", "ModeSign", s * 12.5, 26, zc, 90, { seat = "top", color = { ["2e3140"] = STEEL, ["5b6478"] = "c9cedb" } })
		H.modeSign(id, s * 12.5, 18.85, zc, 90, { both = true })
		slate("Bezel_" .. id, H.countScreen(id, s * 12.5, 12.4, zc, -s * 90, 11))
		H.block("Scenery", "Rod", s * 12.5 - 0.3, s * 12.5 + 0.3, 16.2, 16.6, zc - 0.3, zc + 0.3, STEEL, nil, { ghost = true })
		H.lamp(s * 12.5, 9, zc, 20, 0.8, md.color)
		-- the count again on the car between its two doors, where someone standing on the pad is looking
		-- (the hanging screen is straight overhead from the pad; it is for the aisle)
		local n = md.size
		local status = if md.soon then "coming soon(ish)" elseif md.teams == 3 then "0/1  vs  0/1  vs  0/1" else ("0/%d  vs  0/%d"):format(n, n)
		H.text("CarCount_" .. id, { { md.title, "ffffff", "L", 0.5 }, { status, if md.soon then "c8c8dc" else md.color, "F", 0.26 }, { if md.soon then "we checked. it isn't." else "step on a side to queue", "c8c8dc", "F", 0.16 } }, 8.8, 4.2, s * 17.8, 5.0, zc, -s * 90, { thick = 0.2, flush = true, pps = 24 })
		-- the mode again under the girder you walk under to reach it, so all six read from the spawn (the hanging signs
		-- are edge on from there). it hangs below the girder with WAY OUT on its back for the walk home
		-- (0.9 under the girder on two fat stubs: low enough that the departures board never cuts its top line off)
		for _, dx in { -4, 4 } do H.block("Scenery", "Rod", s * 7 + dx - 0.5, s * 7 + dx + 0.5, 16.3, 17.4, zc + 15, zc + 16, STEEL, nil, { ghost = true }) end
		H.text("GantryText_" .. id, { { md.title, md.color, "L", 0.6 }, { md.tag, "ffffff", "F", 0.3 } }, 13, 3.6, s * 7, 14.6, zc + 15.5, 0, { thick = 1, backLines = { { "WAY OUT", YEL, "L", 0.6 }, { "concourse · training", "ffffff", "F", 0.3 } } })
		-- the plates over the car's two doorways (6 x 1, their faces 5 out from the car's middle and 10.08 up from its wheels)
		H.text("DoorText", { { md.title, md.color, "L", 1 } }, 5.6, 0.8, s * 17.94, 8.08, zc - s * 7.5, -s * 90, { clear = true, thick = 0.1, pps = 60 })
		H.text("DoorText", { { if md.soon then "NOT IN SERVICE" elseif s < 0 then "PINK LINE" else "CYAN LINE", if md.soon then "c8c8dc" elseif s < 0 then PINK else CYAN, "L", 1 } }, 5.6, 0.8, s * 17.94, 8.08, zc + s * 7.5, -s * 90, { clear = true, thick = 0.1, pps = 60 })
	end
	-- roof girders with light panels (pale steel: structure is paler than what is behind it), light bars down the middle
	for _, z in { -83.5, -52.5, -21.5, 9.5 } do
		H.put("wh_girder", "Girder", 0, 26, z, 0, { scale = 1.357, seat = "top", color = { ["2e3140"] = PALE, ["5b6478"] = STEEL, ["f4f8ff"] = "d4d9e4" } })
		for _, x in { -19, 19 } do H.lamp(x, 17.2, z, 40, 1.2, "f4f8ff", FILL) end
		-- the girder by the doorway also holds the key for the gate line: one lamp whose light comes through the doorway
		-- toward a new arrival, so each gate has one shadow on the floor in front of it
		if z > 0 then H.lamp(0, 17.2, z, 44, 2.8, "f4f8ff", KEY) end
	end
	for _, z in { -68, -37, -6 } do H.put("hb_bar", "LightBar", 0, 26, z, 90, { seat = "top", color = { ["2e3140"] = STEEL } }); H.lamp(0, 23.6, z, 46, 2.4, "f4f8ff", KEY) end
	-- the floor shows the way: follow the pink line to the pink train and the cyan line to the cyan one. each line
	-- turns into each of its boarding zones; past its last open zone it carries on in flat grey to the closed one
	for _, s in { -1, 1 } do
		local hex = if s < 0 then LPINK else LCYAN
		local last = 46
		for _, zn in zones do
			if zn[2] == s then
				local soon = H.M[zn[1]].soon
				H.paint(s * 4, s * 8, zn[3] - 0.8, zn[3] + 0.8, if soon then SHUT else hex, if soon then nil else { mat = Neon })
				if not soon then last = math.min(last, zn[3] - 0.8) end
			end
		end
		H.paint(s * 2.4, s * 4, last, 46, hex, { mat = Neon })
		if last > -68.8 then H.paint(s * 2.4, s * 4, -68.8, last, SHUT) end
		-- arrowheads between the two lines, pointing up the platform
		for _, z in { 41, 32, 23, 8, -21.5, -52.5 } do
			local live = z - 2.2 > last
			stroke(s * 3.2, z + 2.2, s * 0.75, z - 2.2, 1.2, if live then hex else SHUT, if live then Neon else nil)
		end
	end
	-- the end of the line: a giant screen on the far wall between the tunnel mouths, the name readable from the spawn
	slate("EndBoardBezel", H.screen("EndBoard", { { "JANKFIRE", YEL, "L", 0.5 }, { "END OF THE LINE", "ffffff", "L", 0.2 }, { "this train terminates here. so do most plans.", "c8c8dc", "F", 0.16 } }, 0, 10.5, -91.1, 0, 24))
	-- each line's name on the wall behind its buffer
	for _, s in { -1, 1 } do
		H.text("LineName", { { if s < 0 then "PINK LINE" else "CYAN LINE", if s < 0 then PINK else CYAN, "L", 0.6 }, { "terminates here. so will you, shortly.", "ffffff", "F", 0.3 } }, 16, 4, s * 27.75, 14.5, 13.84, 180)
	end
	-- the concourse. the departures board hangs over the gate line, in front of a new arrival (the game is first person:
	-- from the spawn rows its words are 18 to 31 degrees up). it carries the name, all six modes and the way to training
	H.put("st_board", "Departures", 0, 26, 20, 0, { seat = "top", color = tint() })
	local rows = { { "JANKFIRE CENTRAL", YEL, "L", 0.28 }, { "DEPARTURES  ·  mind the jank between the train and the platform", "ffffff", "F", 0.095 } }
	for _, zn in zones do
		local md = H.M[zn[1]]
		table.insert(rows, { ("%s  ·  %s LINE  ·  %s"):format(md.title, zn[2] < 0 and "PINK" or "CYAN", md.soon and "cancelled (ish)" or md.tag), md.color, "F", 0.115 })
	end
	table.insert(rows, { "TRAINING  ·  WAY OUT  ·  the red door on your left", GREEN, "F", 0.115 })
	-- (the board's two plates are 28 x 7.4, 0.6 out from its middle, 3.8 to 11.2 below the ceiling)
	H.text("DeparturesText", rows, 27, 7, 0, 18.5, 20.66, 0, { clear = true, thick = 0.1 })
	H.text("ArrivalsText", { { "ARRIVALS", YEL, "L", 0.26 }, { "YOU  ·  just now  ·  on time, somehow", "ffffff", "F", 0.15 }, { "YOUR FRIEND  ·  delayed  ·  still in the menu", CYAN, "F", 0.15 }, { "THE OTHER TEAM  ·  expected  ·  unfortunately", PINK, "F", 0.15 }, { "A PIGEON  ·  platform 2  ·  no ticket", "c8c8dc", "F", 0.15 } }, 27, 7, 0, 18.5, 19.34, 180, { clear = true, thick = 0.1 })
	-- the ticket gates: identical units, all facing the spawn (green arrows this way). only a gate's body is solid, so
	-- you walk through the flaps; the bodies stand the same either side of the centre walk (15.4 between them, and the
	-- one flap that reaches into it stops short of the 12 stud walk)
	for _, x in { -14, -8, 9.6, 15.6 } do H.put("st_gate", "Gate", x, 0, 22, 0, { solid = { { 2.2, 4, 6, -0.8, 2, 0 } }, color = tint() }) end
	-- the nave: two portal frames from the gates wall to the back wall, their hanging lights over the way in
	for _, s in { -1, 1 } do
		H.put("hb_arch", "NaveFrame", s * 20, 0, 41, -s * 90, { scale = 0.735, color = tint() })
		for _, z in { 17.6, 64.4 } do H.solid("FrameLeg", Vector3.new(3.2, 26, 3.2), CFrame.new(H.w(s * 20, 13, z))) end
		for _, z in { 32.2, 49.8 } do H.lamp(s * 20, 21.8, z, 36, 0.8, "f4f8ff", FILL) end
		-- light bars over the side aisles, a bench under each big screen
		for _, z in { 30, 52 } do H.put("hb_bar", "LightBar", s * 36, 26, z, 90, { seat = "top", color = { ["2e3140"] = STEEL } }); H.lamp(s * 36, 23.6, z, 42, 2.4, "f4f8ff", KEY) end
		H.put("st_bench", "Bench", s * 37, 0, 16, 0, { back = true, solid = true, color = tint() })
		-- the line totems at the ends of the gate line: which side is which (their panels are 2.4 x 5, 0.57 out, 5.7 up)
		local pink = s < 0
		local hex = if pink then PINK else CYAN
		H.put("st_totem", "Totem", s * 20, 0, 23, 0, { solid = true, color = tint(if pink then { [CYAN] = PINK } else nil) })
		H.text("TotemText", { { if pink then "PINK" else "CYAN", hex, "L", 0.2 }, { "LINE", hex, "L", 0.2 }, { if pink then "1V1" else "1V1V1", "ffffff", "F", 0.13 }, { if pink then "2V2" else "4V4", "ffffff", "F", 0.13 }, { if pink then "3V3" else "5V5", "ffffff", "F", 0.13 }, { if pink then "the pink one." else "the cyan one.", "c8c8dc", "F", 0.1 } }, 2.2, 4.8, s * 20, 5.7, 23.63, 0, { clear = true, thick = 0.1, pps = 60 })
		H.text("TotemText", { { "WAY", YEL, "L", 0.28 }, { "OUT", YEL, "L", 0.28 }, { "you only just", "ffffff", "F", 0.12 }, { "got here.", "ffffff", "F", 0.12 } }, 2.2, 4.8, s * 20, 5.7, 22.37, 180, { clear = true, thick = 0.1, pps = 60 })
	end
	H.put("hb_bar", "LightBar", 0, 26, 57, 0, { seat = "top", color = { ["2e3140"] = STEEL } }); H.lamp(0, 23.6, 57, 42, 2.6, "f4f8ff", KEY)
	-- the hall's rhythm carried into the concourse: piers up the walls, each line's colour as a band round its corner
	for _, x in { -42, 42 } do H.put("hb_pier", "Pier", x, 0, 66, 180, { back = true, scale = 0.542, color = tint() }) end
	H.put("hb_pier", "Pier", -50, 0, 62.5, 90, { back = true, scale = 0.542, color = tint() })
	for _, z in { 21, 63.2 } do H.put("hb_pier", "Pier", 50, 0, z, -90, { back = true, scale = 0.542, color = tint() }) end
	H.block("Scenery", "Hazard", -50, -15.5, 11, 13.4, 65.8, 66, PINK, nil, { ghost = true }); H.block("Scenery", "Hazard", -50, -49.8, 11, 13.4, 59.5, 66, PINK, nil, { ghost = true })
	H.block("Scenery", "Hazard", 15.5, 50, 11, 13.4, 65.8, 66, CYAN, nil, { ghost = true }); H.block("Scenery", "Hazard", 49.8, 50, 11, 13.4, 57.5, 66, CYAN, nil, { ghost = true })
	-- and a sign on each stretch of the back wall above the band
	H.text("LostSign", { { "LOST PROPERTY", YEL, "L", 0.6 }, { "mostly matches. some dignity.", "ffffff", "F", 0.34 } }, 16, 4, -31, 17.5, 65.84, 180)
	H.text("SnackSign", { { "REFRESHMENTS", YEL, "L", 0.6 }, { "exact change only. nobody has change.", "ffffff", "F", 0.34 } }, 16, 4, 32, 17.5, 65.84, 180)
	-- the silly thing: the YELLOW LINE's only car, parked on the concourse with two benches to wait for it on. the line was never built
	car("YellowCar", 50, 0, 42, -90, { back = true, solid = true, color = tint({ [PINK] = YEL }) })
	for _, rx in { 42.5, 47.5 } do H.block("Scenery", "Rail", rx - 0.3, rx + 0.3, 0, 0.4, 23.5, 60.5, "8a909e", nil, { ghost = true }) end
	H.put("st_buffer", "Buffer", 45, 0, 25, 0, { solid = true }); H.put("st_buffer", "Buffer", 45, 0, 59, 180, { solid = true })
	H.text("DoorText", { { "YELLOW LINE", YEL, "L", 1 } }, 5.6, 0.8, 39.94, 10.08, 49.5, -90, { clear = true, thick = 0.1, pps = 60 })
	H.text("DoorText", { { "NOT IN SERVICE", "c8c8dc", "L", 1 } }, 5.6, 0.8, 39.94, 10.08, 34.5, -90, { clear = true, thick = 0.1, pps = 60 })
	H.text("YellowSign", { { "THE YELLOW LINE", YEL, "L", 0.6 }, { "never built. the train turned up anyway.", "ffffff", "F", 0.3 } }, 30, 5, 49.84, 18, 42, -90)
	H.put("st_bench", "Bench", 33, 0, 36, 90, { solid = true, color = tint() }); H.put("st_bench", "Bench", 33, 0, 49, 90, { solid = true, color = tint() })
	H.put("st_bench", "Bench", -30, 0, 66, 180, { back = true, solid = true, color = tint() })
	-- the ticket office on the west wall, shutter down, and two benches back to back to wait for it on
	H.put("st_bench", "Bench", -35, 0, 31.5, 180, { solid = true, color = tint() }); H.put("st_bench", "Bench", -35, 0, 34.5, 0, { solid = true, color = tint() })
	H.put("wh_rollup", "TicketShutter", -50, 0, 28, 90, { back = true, scale = 0.76, color = tint({ ["7d8496"] = "e8ecf4", [PINK] = CYAN, ["17141f"] = "3d4358" }) })
	H.text("TicketSign", { { "TICKETS", YEL, "L", 0.6 }, { "closed. the trains are free. so is losing.", "ffffff", "F", 0.34 } }, 16, 2.8, -49.84, 18.6, 28, 90)
	-- the line map on the wall behind the spawn
	H.text("LineMap", { { "LINE MAP", YEL, "L", 0.24 }, { "PINK LINE  ·  1V1  -  2V2  -  3V3", PINK, "F", 0.17 }, { "CYAN LINE  ·  1V1V1  -  4V4  -  5V5 (ish)", CYAN, "F", 0.17 }, { "YELLOW LINE  ·  see: wishful thinking", YEL, "F", 0.17 }, { "you are here. so is everyone else.", "c8c8dc", "F", 0.13 } }, 30, 9, 0, 15, 65.84, 180)
	for i, x in { 27, 32, 37 } do H.put("hb_vending", "Vending", x, 0, 66, 180, { back = true, solid = true, color = tint({ [PINK] = ({ PINK, CYAN, YEL })[i] }) }) end
	slate("TipsBezel", H.screen("Tips", { { "PLATFORM TIP", CYAN, "L", 0.3 }, { "stand on your team's colour to board. stepping off gets you off. that's the whole skill.", "ffffff", "F", 0.6 } }, 37, 13, 16.75, 0, 20))
	slate("NewsBezel", H.screen("News", { { "JANK NEWS 24", "ff3b3b", "L", 0.3 }, { "TRAIN ARRIVES ON TIME. PASSENGERS DEMAND AN EXPLANATION.", YEL, "F", 0.6 } }, -37, 13, 16.75, 0, 20))
	local sp = {}
	for _, z in { 50, 54 } do for _, x in { -6, -2, 2, 6 } do table.insert(sp, { x, z }) end end
	H.spawns(sp)
	H.trainingDoor(-50, 50, 90, { "WAY OUT · TRAINING", "mind the dummies. they don't mind you." }, { frame = { ["2e3140"] = SLATE } })
	local void = H.root.Scenery:FindFirstChild("LaserVoid")
	if void then void.Color = Color3.fromHex("42121f") end
	-- a fat green line on the floor from in front of the spawn to the training door, with arrowheads along it
	local ax, az, bx, bz = -4.6, 41.2, -46, 50
	stroke(ax, az, bx, bz, 2, LGREEN, Neon)
	local glen = math.sqrt((bx - ax) ^ 2 + (bz - az) ^ 2)
	local ux, uz = (bx - ax) / glen, (bz - az) / glen
	for _, t in { 8, 20, 32 } do
		local px, pz = ax + ux * t, az + uz * t
		for _, sd in { -1, 1 } do stroke(px + ux * 2, pz + uz * 2, px - ux * 1.6 - uz * sd * 3, pz - uz * 1.6 + ux * sd * 3, 1.2, LGREEN, Neon) end
	end
	-- the travel discs stand wide of the spawn, clear of the frame legs
	H.tourDiscs(0, 60, 15.5)
	H.zone(-52, 52, -94, 68, 26, "lab_platform")
	return H.done()
end

-- ------------------------------------------------------------------ Hub 3: THE LANES
-- a bowling alley. six lanes, six modes: you queue on a lane's approach. kit bw_*
L.BUILD.Hub3_Lanes = function(H)
	H.room("Alley", -68, 68, -84, 56, 24, { wall = "6a5c90", floor = "45287a", floorMat = Enum.Material.Carpet, ceil = "6a5fa0" }) -- (a clean purple carpet in a mid value: paler burns white under the lamps, the old dark Fabric went brown and speckled)
	-- wood to the dado, a fat pink band over it
	for _, w in { { -68, 68, 55.7, 56 }, { -68, -67.7, -84, 33 }, { -68, -67.7, 47, 56 }, { 67.7, 68, -84, 56 } } do -- (the west wall's trim stops at the training doorway's posts)
		H.block("Scenery", "Dado", w[1], w[2], 0, 6, w[3], w[4], "a8703a", Enum.Material.Wood, { ghost = true })
		H.block("Scenery", "Hazard", w[1], w[2], 6, 7.4, w[3], w[4], PINK, nil, { ghost = true })
	end
	-- the machine wall behind the pins, with the name on it
	H.block("Shell", "Masking", -68, 68, 7, 24, -84, -69.2, "3a2d5c")
	-- (painted straight on the wall, from the pinsetters' tops up: from the spawn the whole of it shows under the hanging mode signs,
	-- and nothing hangs between those signs and the wall: each sign carries its own count)
	H.text("Name", { { "JANKFIRE LANES", YEL, "L", 0.8 }, { "six lanes. six modes. no bumpers.", "ffffff", "F", 0.2 } }, 110, 14.4, 0, 14.7, -69.05, 0, { plate = "3a2d5c" })
	local ids = { "1v1", "1v1v1", "2v2", "3v3", "4v4", "5v5" }
	local cols = { PINK, CYAN, GREEN, YEL, PINK, "8a90a0" } -- (each lane's own colour: its pinsetter, its light, its line on the floor)
	for i, id in ids do
		local x = -50 + (i - 1) * 20
		H.block("Scenery", "Lane", x - 6, x + 6, 0, 0.3, -66, -4, "e2c08a", Enum.Material.WoodPlanks)
		H.block("Scenery", "Gutter", x - 7.2, x - 6, 0, 0.12, -66, -4, "2e3140", nil, { ghost = true }); H.block("Scenery", "Gutter", x + 6, x + 7.2, 0, 0.12, -66, -4, "2e3140", nil, { ghost = true })
		H.block("Scenery", "PinDeck", x - 7, x + 7, 0, 0.3, -76, -66, "2e3140")
		H.block("Shell", "MachineGap", x + 7, if i == 6 then 68 else x + 13, 0, 7, -84, -69.2, "3a2d5c") -- (the last one runs to the east wall: no pocket behind the machines)
		H.pad(id, x, 5, 180, 16, 16)
		H.put("bw_pins", "Pins", x, 0.3, -71, 0, { solid = true }) -- (solid, and the housing too: a lane ends at its pins)
		H.put("bw_pinsetter", "Pinsetter", x, 0, -71.5, 0, { solid = true, color = { [PINK] = cols[i], ["17141f"] = "3a2d5c" } })
		H.text("LaneNumber", { { "LANE " .. i, "ffffff", "L", 1 } }, 10.8, 1.6, x, 5.83, -68.74, 0, { clear = true, flush = true }) -- (the housing's score plate: its face is 2.75 out from the middle, the words go over the five dots)
		-- one board per lane: the mode, its line and who is waiting, on both faces. (a count screen further down the lane slid
		-- under its neighbour's sign from anywhere but its own pad, so the count is the board's third line)
		local md = H.M[id]
		local status = if md.soon then "closed for waxing. (ish)" elseif md.teams == 3 then "0/1  vs  0/1  vs  0/1" else ("0/%d  vs  0/%d"):format(md.size, md.size)
		H.put("hb_hangsign", "ModeSign", x, 24, 0, 0, { seat = "top", color = { ["2e3140"] = "8f86c4", ["5b6478"] = "a59ad8" } }) -- (over the pad's far edge: far enough from the spawn that all six fit in one look)
		H.text("Sign_" .. id, { { md.title, md.color, "L", 0.44 }, { md.tag, "ffffff", "F", 0.26 }, { status, if md.soon then "c8c8dc" else md.color, "F", 0.30 } }, 13.4, 4.4, x, 16.8, 0, 0, { both = true, thick = 1.7 }) -- (1.7 thick: it caps the 1.6 deep frame instead of sinking into it)
		H.lamp(x, 18.3, -35, 40, 0.9, cols[i]); H.lamp(x, 4.3, -68.3, 16, 1.5, "fff1d6") -- (under the girder's panels; at the housing's five lit dots)
		-- the floor: a stem in the lane's colour from the cross line to its pad
		H.paint(x - 0.8, x + 0.8, 13.6, 18.7, cols[i])
		H.put("bc_chevron", "Arrow", x, 0.09, 16.2, 180, { color = { f4f8ff = cols[i] } })
	end
	H.block("Shell", "MachineGap", -68, -57, 0, 7, -84, -69.2, "3a2d5c")
	for i = 0, 6 do -- the capping between the lanes (and to the side walls)
		local a = if i == 0 then -68 else -50 + (i - 1) * 20 + 7.2
		local b = if i == 6 then 68 else -50 + i * 20 - 7.2
		H.block("Scenery", "Capping", a, b, 0, 1.2, -66, -4, "a4aab8")
	end
	for _, x in { -40, 0, 40 } do
		H.put("bw_ballreturn", "BallReturn", x, 0, 6, 0, { solid = true, color = { ["17141f"] = "3a2d5c" } })
	end
	-- four booths in a row behind the approach, open toward the lanes, a wide aisle up the middle. you can walk in and sit:
	-- the back, the two sides, the seats and the table are solid, the middle is open
	local BOOTH = { { 14, 4.2, 1, 0, nil, -3.5 }, { 1.4, 4.2, 7.6, -6.3, nil, -0.2 }, { 1.4, 4.2, 7.6, 6.3, nil, -0.2 }, { 2.7, 2, 6.6, -4.95, nil, 0.1 }, { 2.7, 2, 6.6, 4.95, nil, 0.1 }, { 8.4, 2, 2.7, 0, nil, -2.15 }, { 3, 3.3, 3, 0, nil, 1.5 } }
	for i, x in { -38, -24, 24, 38 } do -- (two pairs side by side with no slot between: the aisle is 34 wide and pads 2 to 5 show up it)
		H.put("bw_booth", "Booth", x, 0, 30, 180, { solid = BOOTH, color = { [CYAN] = ({ PINK, YEL, CYAN, GREEN })[i], ["2e3140"] = "6a55b0", ["17141f"] = "3a2d5c" } }) -- (purple shells: the dark ones were black slabs across the first view)
		H.lamp(x, 4.5, 28.5, 12, 0.6, "ffe9b8") -- the little lamp on its table is a real one
	end
	-- the side walls: piers, and beside the lanes a board flat on the wall, two speakers under it, a spare giant pin by the pins
	for _, s in { -1, 1 } do
		for _, z in { -66, -35, -4, 26 } do H.put("hb_pier", "Pier", s * 68, 0, z, -s * 90, { back = true, scale = 0.5 }) end
		-- (hung 5.5 under the ceiling on a fat mount, so its words show below the row of mode signs from the spawn and the cross walk)
		H.put("st_board", "WallBoard", s * 68, 18.5, -19.5, -s * 90, { back = true, seat = "top", scale = 0.85, color = { ["17141f"] = "3a2d5c", ["2e3140"] = "8f86c4", ["5b6478"] = "a59ad8" } })
		H.block("Scenery", "BoardMount", s * 66.9, s * 68, 18.5, 24, -27.7, -11.3, "8f86c4", nil, { ghost = true })
		for _, z in { -41.5, -59.8 } do H.put("bc_speaker", "Speaker", s * 68, 1.2, z, -s * 90, { back = true, scale = 2, solid = true, color = { ["17141f"] = "6a55b0", ["3a3f4a"] = "3a2d5c", ["2a2d38"] = "4a3d6a" } }) end -- (either side of the spare pin, out from under the lowered board)
		H.put("bw_giantpin", "SidePin", s * 62.6, 1.2, -50.5, 0, { solid = true, color = { ["17141f"] = "3a2d5c" } })
		H.text("SidePinPlate", { { if s < 0 then "SPARE PIN" else "SPARE SPARE PIN", YEL, "L", 1 } }, 4.8, 0.9, s * 62.6, 1.9, -45.99, 0, { clear = true, flush = true })
		H.lamp(s * 60.44, 3.4, -48.34, 18, 0.8, "ffe9b8") -- (over the plinth's uplight on the lane side)
	end
	H.text("ScoresText", { { "HIGH SCORES", YEL, "L", 0.26 }, { "1  ·  DAVE  ·  300  ·  nobody saw it", "ffffff", "F", 0.15 }, { "2  ·  DAVE'S MUM  ·  212  ·  everybody saw it", CYAN, "F", 0.15 }, { "3  ·  THE GUTTER  ·  undefeated", PINK, "F", 0.15 }, { "4  ·  YOU  ·  pending", "c8c8dc", "F", 0.15 } }, 23, 6, -66.76, 12.12, -19.5, 90, { clear = true, flush = true, thick = 0.1 })
	H.text("TonightText", { { "TONIGHT", YEL, "L", 0.26 }, { "LEAGUE NIGHT  ·  cancelled. nobody is in a league.", "ffffff", "F", 0.15 }, { "DISCO BOWLING  ·  the lights are just like this.", CYAN, "F", 0.15 }, { "SHOE HIRE  ·  free. the shoes do nothing.", PINK, "F", 0.15 }, { "BUMPERS  ·  no.", "c8c8dc", "F", 0.15 } }, 23, 6, 66.76, 12.12, -19.5, -90, { clear = true, flush = true, thick = 0.1 })
	-- girders with light panels over the booths and half way down the lanes
	for _, z in { 17, -35 } do
		for _, cx in { -45.3, 0, 45.3 } do
			H.put("wh_girder", "Girder", cx, 24, z, 0, { scale = 0.81, seat = "top", color = { ["2e3140"] = "8f86c4", ["5b6478"] = "a59ad8" } }) -- (paler than the wall and the lid behind it)
			for _, dx in { -11.3, 11.3 } do H.lamp(cx + dx, 18.7, z, 44, if z > 0 then 2.8 else 1.4, "fff1d6", { spot = true, shadows = z > 0, angle = if z > 0 then 96 else 120 }); if z > 0 then H.lamp(cx + dx, 18.5, z, 18, 0.7, "efe6ff") end end -- (the six over the cross walk and the pads cast shadows; the lane row has nothing under it to cast one)
		end
	end
	-- a fat clamp over each girder joint (the webs stop 2.5 short of it), and four ribs across the concourse ceiling from those
	-- joints and the outer girders' middles: girders, clamps and ribs are one pale frame under a darker lid
	for _, s in { -1, 1 } do
		for _, z in { -35, 17 } do H.block("Scenery", "GirderClamp", s * 22.65 - 2.8, s * 22.65 + 2.8, 18.6, 24, z - 2.1, z + 2.1, "a59ad8", nil, { ghost = true }) end
		for _, x in { 22.65, 45.3 } do H.block("Scenery", "Rib", s * x - 1.5, s * x + 1.5, 22.4, 24, 18.8, 56, "a59ad8", nil, { ghost = true }) end
	end
	-- (each main panel has two lamps: a spot down that casts shadows, in a 96 degree cone so the floor is pools of light and
	-- not one flat wash, and a small glow that lights the ceiling and the top of the walls round the panel)
	for _, p in { { -58, 42 }, { -34, 42 }, { 0, 42 }, { 34, 42 }, { 58, 42 } } do H.put("hb_bar", "LightBar", p[1], 24, p[2], 0, { seat = "top", color = { ["2e3140"] = "8f86c4" } }); H.lamp(p[1], 21.6, p[2], 40, 2.4, "fff1d6", { spot = true, shadows = true, angle = 96 }); H.lamp(p[1], 21.2, p[2], 24, 0.7, "efe6ff") end -- (and the five over the concourse: eleven shadow lamps in all)
	-- the concourse: shoes, snacks, machines, the giant pin
	H.put("bw_counter", "ShoeCounter", -42, 0, 56, 180, { back = true, solid = true, color = { ["17141f"] = "3a2d5c" } })
	H.text("ShoeSign", { { "SHOES", CYAN, "L", 0.6 }, { "two left feet available", "ffffff", "F", 0.34 } }, 16, 3, -42, 12.6, 55.85, 180)
	H.put("bc_lockers", "Lockers", -60, 0, 56, 180, { back = true, scale = 1.5, solid = true, color = { ["56683f"] = CYAN, ["2a2d38"] = "5b6478", ["17141f"] = "3a2d5c" } })
	-- one fat shelf with three small gold giant pins on it for trophies (the old cup rack was thin shelves and cups the size of dots)
	H.block("Scenery", "TrophyShelf", -32, -21, 7.6, 8.8, 52.4, 56, "a8703a", Enum.Material.Wood, { ghost = true })
	for _, x in { -30, -26.5, -23 } do H.put("bw_giantpin", "Trophy", x, 8.8, 54.2, 180, { scale = 0.36, color = { f4f2ec = YEL, ["17141f"] = "3a2d5c" } }) end
	H.text("TrophySign", { { "TROPHIES", YEL, "L", 0.6 }, { "all for turning up.", "ffffff", "F", 0.34 } }, 10, 2.2, -26.5, 17.2, 55.85, 180)
	H.put("st_bench", "Bench", -26.5, 0, 56, 180, { back = true, solid = true })
	-- the lane guide on the wall behind the spawn
	local guide = { { "LANE GUIDE", YEL, "L", 0.22 } }
	for i, id in ids do local md = H.M[id]; table.insert(guide, { ("LANE %d  ·  %s  ·  %s"):format(i, md.title, if md.soon then "closed for waxing. (ish)" else md.tag), md.color, "F", 0.115 }) end
	table.insert(guide, { "TRAINING  ·  the red door in the west wall  ·  also the fire exit", GREEN, "F", 0.115 })
	H.text("LaneGuide", guide, 30, 9, 0, 15, 55.85, 180)
	-- the snack bar, with a table to eat at
	H.put("fc_stall", "SnackBar", 34.5, 0, 56, 180, { back = true, solid = true, color = { [PINK] = CYAN } })
	H.text("SnackName", { { "NACHOS. JUST NACHOS.", YEL, "L", 1 } }, 21.4, 2.9, 34.5, L.FASCIA_Y, 56 - L.FASCIA_OUT, 180, { clear = true })
	H.put("fc_table", "Table", 53, 0, 42, 20, { solid = Vector3.new(6, 3.3, 6), color = { [YEL] = PINK } })
	for i, x in { 50.5, 54.7, 58.9 } do H.put("hb_vending", "Vending", x, 0, 56, 180, { back = true, solid = true, color = { [PINK] = ({ YEL, PINK, CYAN })[i], ["17141f"] = "3a2d5c" } }) end
	for _, z in { 39, 44, 49 } do H.put("bc_arcade", "Arcade", 68, 0, z, -90, { back = true, scale = 1.3, solid = true, color = { ["17141f"] = "3a2d5c", ["120818"] = "3a2d5c" } }) end
	H.text("ArcadeSign", { { "ARCADE", PINK, "L", 0.6 }, { "one game. it is the one you are in.", "ffffff", "F", 0.34 } }, 14, 2.8, 67.85, 12.4, 44, -90)
	H.put("bw_giantpin", "GiantPin", 57, 0, 30.5, -45, { solid = Vector3.new(6.4, 17.4, 6.4), color = { ["17141f"] = "3a2d5c" } }) -- (at the east end of the booth row, its plate turned toward the spawn)
	H.text("PinPlate", { { "JANKFIRE", YEL, "L", 1 } }, 4.8, 0.9, 57 - 3.189, 0.7, 30.5 + 3.189, -45, { clear = true, flush = true }) -- (the plate's face is 4.5 out from the pin's middle)
	H.lamp(57, 2.2, 33.55, 18, 0.8, "ffe9b8") -- (over the plinth's south uplight)
	H.screen("Tips", { { "HOUSE RULES", CYAN, "L", 0.3 }, { "stand on your colour to queue. stepping off un-queues you. that's the whole skill.", "ffffff", "F", 0.6 } }, 67.35, 15, 11, -90, 16)
	H.screen("News", { { "JANK NEWS 24", "ff3b3b", "L", 0.3 }, { "LOCAL MAN BOWLS 300. NOBODY SAW IT. HE SAYS IT COUNTS.", YEL, "F", 0.6 } }, -67.35, 15, 11, 90, 16)
	for _, s in { -1, 1 } do H.put("st_bench", "Bench", s * 68, 0, 11, -s * 90, { back = true, solid = true }) end -- a bench under each screen
	-- a totem at the west end of the booth row (the giant pin has the east end): it faces the spawn and points at the door
	-- (at twice its size its two panels are 4.8 x 10, 1.14 out from its middle, 11.4 up)
	H.put("st_totem", "Totem", -56, 0, 30, 90, { scale = 2, solid = true, color = { [CYAN] = GREEN, ["17141f"] = "3a2d5c" } })
	H.text("TotemText", { { "TRAINING", GREEN, "L", 0.16 }, { "<<<", GREEN, "L", 0.24 }, { "it is the big red door. people still miss it.", "ffffff", "F", 0.6 } }, 4.2, 9.5, -54.84, 11.4, 30, 90, { clear = true, flush = true, thick = 0.1 })
	H.text("TotemText", { { "THE LANES", YEL, "L", 0.22 }, { "<<<", YEL, "L", 0.2 }, { "six of them. pick one. they are all the same lane.", "ffffff", "F", 0.58 } }, 4.2, 9.5, -57.16, 11.4, 30, -90, { clear = true, flush = true, thick = 0.1 })
	-- the floor shows the way: a yellow line up the aisle to a cross line that runs past every lane; green goes to training
	H.paint(-0.8, 0.8, 20.3, 45.5, YEL); H.paint(-50.8, 50.8, 18.7, 20.3, YEL)
	for _, z in { 41, 33, 25 } do H.put("bc_chevron", "Arrow", 0, 0.09, z, 180, { color = { f4f8ff = PINK } }) end
	for _, s in { -1, 1 } do for _, x in { 20, 40 } do H.put("bc_chevron", "Arrow", s * x, 0.09, 19.5, s * 90, { color = { f4f8ff = PINK } }) end end
	H.paint(-62, -9, 40.2, 41.8, GREEN)
	for _, x in { -18, -36, -54 } do H.put("bc_chevron", "Arrow", x, 0.09, 41, -90, { color = { f4f8ff = GREEN } }) end
	local sp = {}
	for _, z in { 39, 43 } do for _, x in { -5.4, -1.8, 1.8, 5.4 } do table.insert(sp, { x, z }) end end
	H.spawns(sp)
	H.trainingDoor(-68, 40, 90, { "TRAINING", "the fire exit. the fire is optional." })
	-- the word on the floor ahead of the spawn, where a first look lands (the door is square to the left): green, pointing
	-- west, drawn long like a road marking so it reads from eye height
	local tf = H.text("TrainingFloor", { { "TRAINING", GREEN, "L", 1 } }, 9.4, 5, -7.9, 0, 29.1, 0, { clear = true, thick = 0.2 })
	tf.CFrame = CFrame.new(H.w(-7.9, 0, 29.1)) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.Angles(0, math.pi, 0)
	tf.Gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize; tf.Gui.CanvasSize = Vector2.new(470, 100)
	H.put("bc_chevron", "Arrow", -14.9, 0.09, 29.1, -90, { color = { f4f8ff = GREEN } })
	-- the two travel discs every show hub has, behind the spawn but set wider apart than H.tourDiscs puts them: its sign
	-- boards would stand between the camera and the room for anyone who has just spawned
	local nxt = L.ORDER[table.find(L.ORDER, H.name) % #L.ORDER + 1]
	H.disc("ToNext", -16, 51.5, "NEXT HUB", L.TITLE[nxt], nxt .. "_Arrive", L.TITLE[nxt], YEL)
	H.disc("ToHub1", 16, 51.5, "HUB 1", "THE ROTUNDA", "HubArrive", "BACK TO THE ROTUNDA", PINK)
	-- every model in here is flat smooth plastic (a few older props came with metal parts, which render near black under these lamps)
	for _, p in H.root.Scenery:GetDescendants() do if p:IsA("BasePart") and p.Material == Enum.Material.Metal then p.Material = Enum.Material.SmoothPlastic end end
	H.zone(-68, 68, -84, 56, 24, "lab_lanes")
	return H.done()
end

-- ------------------------------------------------------------------ Hub 4: THE FOOD COURT
-- a mall food court under a glass roof. six stalls, six modes: you queue at a stall. kit fc_*
L.BUILD.Hub4_FoodCourt = function(H)
	local WALL, FLOOR, TILE = "aab7d3", "c8a888", "e8ecf4" -- (walls a step darker than the structure, so piers and arches stand out; the floor a warm mid tile: a pale one burns white under the sun)
	-- a booth against a wall: you can step up into it, its back is solid
	local function booth(bx, bz, bface)
		local bf = H.front(bface)
		local _, _, bcf = H.put("bw_booth", "Booth", bx, 0, bz, bface, { back = true, color = { ["17141f"] = "2e3140" } }) -- (nothing near-black: its base is the kit's navy)
		if bcf then
			H.solid("BoothBase", Vector3.new(13.2, 0.9, 7), CFrame.new(bcf.Position.X, H.O.Y + 0.45, bcf.Position.Z) * bcf.Rotation)
			H.solid("BoothBack", Vector3.new(14, 4.2, 1.6), CFrame.new(bcf.Position.X - bf.X * 3.2, H.O.Y + 2.1, bcf.Position.Z - bf.Z * 3.2) * bcf.Rotation)
			local bp = bcf.Position - H.O
			H.lamp(bp.X + bf.X * 1.5, 4.4, bp.Z + bf.Z * 1.5, 12, 0.6, "ffe9b8") -- the little lamp on its table is a real one
		end
	end
	H.room("Court", -70, 70, -70, 70, 44, { wall = WALL, floor = FLOOR, floorMat = Enum.Material.CeramicTiles, noCeil = true })
	H.block("Shell", "CourtCeiling", -72, 72, 44, 45, -72, -40, "a4aab8"); H.block("Shell", "CourtCeiling", -72, 72, 44, 45, 40, 72, "a4aab8")
	H.block("Shell", "CourtCeiling", -72, -40, 44, 45, -40, 40, "a4aab8"); H.block("Shell", "CourtCeiling", 40, 72, 44, 45, -40, 40, "a4aab8")
	H.block("Shell", "Skylight", -40, 40, 44, 44.6, -40, 40, "cfe8ff", Enum.Material.Glass, { tr = 0.6, noShadow = true })
	for _, z in { -30, -10, 10, 30 } do
		H.put("fc_skytruss", "SkyTruss", 0, 44, z * 0.8, 0, { scale = 1.333, seat = "top" }) -- (at -24, -8, 8, 24: the north one's lamps hang clear of the name board as seen from the spawn)
		-- (fill, turned well down: at 1.6 they burnt the floor white. the south truss's lamps cast shadows: the sun does that job under the rest)
		for _, x in { -23.1, 0, 23.1 } do H.lamp(x, 36.6, z * 0.8, 44, 0.5, "fff7e6", { spot = true, shadows = z > 20 }) end
	end
	-- three fat light panels in the ceiling over the entrance side, which the sun never reaches (each a real lamp that casts shadows:
	-- with the south truss's three and the six arch lamps that makes twelve shadow lamps, and no more)
	for _, px in { -31, 0, 31 } do
		H.put("hb_panel", "EntranceLight", px, 44, 55, 0, { scale = 3.5, seat = "top" })
		H.lamp(px, 40.8, 55, 60, 0.8, "fff1d6", { spot = true, angle = 110, shadows = true })
	end
	-- a fat colour band round the walls, piers between the stalls
	for _, w in { { -70, 70, -70, -69.8 }, { -70, 70, 69.8, 70 }, { -70, -69.8, -70, 70 }, { 69.8, 70, -70, 70 } } do H.block("Scenery", "Hazard", w[1], w[2], 15, 17, w[3], w[4], CYAN, nil, { ghost = true }) end
	-- (a pier each side of every stall, in line with the legs of the arch in front of it; none through the name or the doors)
	local PIER = { back = true, scale = 0.917, color = { a4aab8 = TILE } }
	for _, x in { -40, -8, 8, 40 } do H.put("hb_pier", "Pier", x, 0, -70, 0, PIER) end
	for _, x in { -52, -16, 16, 52 } do H.put("hb_pier", "Pier", x, 0, 70, 180, PIER) end
	for _, z in { -40, -8, 8, 40 } do H.put("hb_pier", "Pier", -70, 0, z, 90, PIER); H.put("hb_pier", "Pier", 70, 0, z, -90, PIER) end
	-- the six stalls
	local stalls = {
		-- (in an order you can walk: clockwise from the spawn, 1v1 first on your left. name and colour stay with the mode.
		-- last: the giant food that stands on the stall's roof, how far to slide it along the roof to centre its body, and a turn
		-- for the taco, which is flat side-on: turned a little it shows its filling)
		{ "1v1", -70, 24, 90, "ONE ON ONE NOODLES", PINK, "fc_food_noodles", 0.3 }, { "1v1v1", -70, -24, 90, "THREE'S A CROWD KEBABS", YEL, "fc_food_kebab", 0 },
		{ "2v2", -24, -70, 0, "TWO FOR TWO TACOS", CYAN, "fc_food_taco", 0, 18 }, { "3v3", 24, -70, 0, "TRIPLE STACK BURGERS", GREEN, "fc_food_burger", 0 },
		{ "4v4", 70, -24, -90, "FOUR SQUARE PIZZA", "ff9a1f", "fc_food_pizza", 0 }, { "5v5", 70, 24, -90, "HIGH FIVE FRIES", "8a90a0", "fc_food_fries", 0.45 },
	}
	for _, s in stalls do
		local id, x, z, face, words, col = s[1], s[2], s[3], s[4], s[5], s[6]
		local f = H.front(face)
		H.put("fc_stall", "Stall", x, 0, z, face, { back = true, solid = true, color = { [PINK] = col } })
		H.text("StallName", { { words, col, "L", 1 } }, 21.4, 2.9, x + f.X * L.FASCIA_OUT, L.FASCIA_Y, z + f.Z * L.FASCIA_OUT, face, { clear = true })
		H.pad(id, x + f.X * 18, z + f.Z * 18, face + 180, 22, 14)
		H.countScreen(id, x + f.X * 7.4, 6.63, z + f.Z * 7.4, face, 7.5) -- stands on the counter (top 4.0), its bezel ends just under the awning (9.25)
		-- a pale arch stands over the queue, floor to roof; the mode hangs from it, high enough to leave the stall's own name in view
		local r = Vector3.new(f.Z, 0, -f.X)
		local sx, sz = x + f.X * 24, z + f.Z * 24
		H.put("hb_rib", "QueueArch", sx, 0, sz, face, { scale = 2.19, color = { a4aab8 = TILE } })
		H.lamp(sx, 37.3, sz, 50, 1.2, "fff7e6", { spot = true, shadows = true })
		local hx, hz = sx + f.X * 2.05, sz + f.Z * 2.05 -- (the sign's rods go up beside the arch's own light, not through it)
		H.put("hb_hangsign", "ModeFrame", hx, 38.54, hz, face, { scale = 1.5, seat = "top" })
		-- (the mode's words in the stall's own colour, on a plate as deep as the frame so the frame's rim does not cover the tagline)
		H.text("ModeText_" .. id, { { H.M[id].title, col, "L", 0.6 }, { H.M[id].tag, "ffffff", "F", 0.3 } }, 19.5, 5.4, hx, 27.81, hz, face, { both = true, thick = 2.0 })
		for _, k in { -16.1, 16.1 } do -- the arch's two legs are solid, the way through is open
			local px, pz = sx + r.X * k, sz + r.Z * k
			H.solid("ArchLeg", Vector3.new(math.abs(r.X) * 3.2 + math.abs(f.X) * 7, 40, math.abs(r.Z) * 3.2 + math.abs(f.Z) * 7), CFrame.new(H.w(px, 20, pz)))
		end
		H.lamp(x + f.X * 18, 5, z + f.Z * 18, 24, 1.0, col) -- the pad's glow, low over the pad, in the stall's colour: one colour means one stall (sign, glow, name, stripe)
		-- a fat stripe and an arrow from the loop to the pad, in the stall's own colour
		local a0, a1 = Vector3.new(x, 0, z) + f * 25.4 - r * 1.5, Vector3.new(x, 0, z) + f * 32.2 + r * 1.5
		H.paint(a0.X, a1.X, a0.Z, a1.Z, col)
		H.put("bc_chevron", "Arrow", x + f.X * 28.8, 0.09, z + f.Z * 28.8, face + 180, { scale = 1.5 })
		-- one giant food on the stall's roof says what the stall is from across the court
		H.put(s[7], "RoofFood", x + f.X * 3.5 + r.X * s[8], 13.9, z + f.Z * 3.5 + r.Z * s[8], face + (s[9] or 0))
		-- lit like a shop sign: a fat light bar on the wall over it, and the stall's own white strip under it as a footlight
		H.put("hb_bar", "FoodLight", x, 27.5, z, face, { back = true, scale = 1.5 })
		H.lamp(x + f.X * 2.4, 27.2, z + f.Z * 2.4, 20, 0.9, "fff1d6", { spot = true, angle = 110 })
		for _, k in { -6, 6 } do H.lamp(x + f.X * 6.8 + r.X * k, 14.4, z + f.Z * 6.8 + r.Z * k, 15, 0.45, "fff1d6") end
	end
	H.text("Name", { { "JANKFIRE", YEL, "L", 0.8 }, { "FOOD COURT · est. whenever", "17141f", "F", 0.2 } }, 60, 10.3, 0, 36.85, -40.35, 0, { plate = "ff4fd8" })
	-- (the name hangs across the front of the two north arches, above their mode signs: clear of the duck's head from the spawn)
	H.block("Scenery", "NameBoard", -30.8, 30.8, 31.4, 42.3, -42.3, -40.5, TILE, nil, { ghost = true }) -- (a fat board with an edge, thickened forward so it clears the mode frames behind it)
	-- the middle: the duck, tables, trees
	local _, dsz = H.put("fc_duck", "Duck", 0, 0, 0, 0, { scale = 1.3, solid = Vector3.new(27.3, 2.86, 27.3) })
	dsz = dsz or Vector3.new(28.6, 16.9, 28.64)
	H.solid("DuckBody", Vector3.new(9, 9, 13), CFrame.new(H.w(0, 7, -1.4))); H.solid("DuckHead", Vector3.new(6.5, 6.5, 6.5), CFrame.new(H.w(0, 13, 3.3))) -- (you cannot walk through the duck)
	H.text("DuckPlate", { { "JANKFIRE", YEL, "L", 1 } }, 7.28, 1.3, 0, 1.3, dsz.Z / 2 + 0.07, 0, { clear = true }) -- (the plate is the front-most thing on the model, so its face is half the box's depth out; all of it 1.3 times the file's size)
	for i = 0, 7 do
		local a = math.rad(22.5 + 45 * i)
		H.put("fc_table", "Table", 24 * math.sin(a), 0, 24 * math.cos(a), i * 25, { solid = Vector3.new(6, 3.3, 6), color = { [YEL] = ({ YEL, PINK, CYAN })[i % 3 + 1] } })
	end
	-- trees: four at the island's corners, one each side of the entrance, a giant in each north corner
	-- (the island's south pair is low: the side stalls' signs show over them from the spawn)
	for i, p in { { -25, -25, 1.4 }, { 25, -25, 1.4 }, { 25, 25, 0.8 }, { -25, 25, 0.8 }, { -46.5, 61.5, 1 }, { 47.5, 50.5, 1 } } do -- (and the two by the entrance stay under the notices on the walls behind them)
		H.put("fc_tree", "Tree", p[1], 0, p[2], i * 90, { scale = p[3], solid = Vector3.new(7 * p[3], 2.6 * p[3], 7 * p[3]) })
	end
	for _, s in { -1, 1 } do H.put("fc_tree", "BigTree", s * 57, 0, -52, s * 90, { scale = 1.8, solid = Vector3.new(12.6, 4.68, 12.6) }) end
	for _, p in { { -16, 28.5, 0 }, { 16, 28.5, 0 }, { -16, -28.5, 180 }, { 16, -28.5, 180 } } do H.put("fc_bin", "Bin", p[1], 0, p[2], p[3], { solid = true, color = { ["17141f"] = "2e3140" } }) end
	for _, a in { 45, 180, 270 } do H.put("fc_wetfloor", "WetFloor", 16.6 * math.sin(math.rad(a)), 0, 16.6 * math.cos(math.rad(a)), a, { scale = 1.2 }) end -- it is a fountain: the floor round it is wet
	-- the entrance wall: the doors you came in by, the way to training, two screens between the side stalls
	H.block("Scenery", "MallDoors", -12, 12, 0, 16, 69.6, 70, "7fbfe8", nil, { ghost = true }) -- (sky blue and not glowing: the pads stay the brightest things)
	for _, x in { -12, -4, 4, 12 } do H.block("Scenery", "DoorPost", x - 0.5, x + 0.5, 0, 16.6, 69.2, 70, "2e3140", nil, { ghost = true }) end
	H.block("Scenery", "DoorHead", -12.5, 12.5, 16, 17.2, 69.2, 70, "2e3140", nil, { ghost = true })
	H.text("DoorSign", { { "EXIT TO THE CAR PARK", "ffffff", "L", 0.58 }, { "the car park is not in the game.", "c8c8dc", "F", 0.34 } }, 20, 3, 0, 19.2, 69.7, 180)
	H.text("EntranceName", { { "JANKFIRE", YEL, "L", 1 } }, 24, 5.2, 0, 25.6, 69.7, 180, { plate = "ff4fd8" })
	H.screen("Tips", { { "COURT RULES", CYAN, "L", 0.3 }, { "stand on your colour at a stall to queue. stepping off un-queues you. that's the whole skill.", "ffffff", "F", 0.6 } }, -66, 26.5, 0, 90, 16) -- (each screen is bolted across the two piers between a wall's stalls, and shows whole between the arch legs in front)
	H.screen("News", { { "JANK NEWS 24", "ff3b3b", "L", 0.3 }, { "DUCK FOUNTAIN STILL JUST A DUCK. INVESTIGATION ONGOING.", YEL, "F", 0.6 } }, 66, 26.5, 0, -90, 16)
	-- floor paint: a pink stem from the spawn to a loop that runs past every stall (12 wide, kept clear), a green line to training
	-- (lines 3 wide; the stem starts under both spawn rows, so the way forward is at your feet)
	H.paint(-1.5, 1.5, 37.8, 57, PINK)
	H.paint(-37.8, 37.8, 34.8, 37.8, PINK); H.paint(-37.8, 37.8, -37.8, -34.8, PINK); H.paint(-37.8, -34.8, -34.8, 34.8, PINK); H.paint(34.8, 37.8, -34.8, 34.8, PINK)
	local ARROW = { color = { f4f8ff = YEL }, scale = 1.5 }
	H.put("bc_chevron", "Arrow", 0, 0.09, 42, 180, ARROW)
	for _, s in { -1, 1 } do H.put("bc_chevron", "Arrow", s * 27, 0.09, 36.3, s * 90, ARROW); H.put("bc_chevron", "Arrow", s * 36.3, 0.09, 0, 180, ARROW) end -- (clear of the stall stripes' own arrows)
	H.paint(-32.5, -1.5, 45.5, 48.5, GREEN); H.paint(-32.5, -29.5, 48.5, 64.6, GREEN) -- (the green line branches off the stem)
	H.put("bc_chevron", "Arrow", -12, 0.09, 47, -90, { scale = 1.2 }); H.put("bc_chevron", "Arrow", -24, 0.09, 47, -90, { scale = 1.2 }); H.put("bc_chevron", "Arrow", -31, 0.09, 57, 0, { scale = 1.2 })
	-- words on the floor either side of the stem, readable as you arrive (the training door is behind you, so the floor has to say it;
	-- anything tall enough to carry these words would stand between the spawn and the stalls)
	for _, fwd in { { -12.5, "<<< TRAINING", GREEN, "follow the green line. you are staff now." }, { 12.5, "YOU ARE HERE", YEL, "so is the duck." } } do
		local fw = H.text("FloorWord", { { fwd[2], fwd[3], "L", 0.62 }, { fwd[4], "ffffff", "L", 0.3 } }, 15, 3.6, fwd[1], 0, 41.9, 0, { clear = true })
		fw.CFrame = CFrame.fromMatrix(H.w(fwd[1], -0.04, 41.9), Vector3.new(-1, 0, 0), Vector3.new(0, 0, -1), Vector3.new(0, -1, 0))
	end
	-- two totems where the stem leaves the spawn: the way to training, and where you are
	-- (small, out to the sides of the spawn rows and turned to face them: you read them when you look left or right, and
	-- nothing stands between a spawn point and the duck, the stalls or the training door. the words sit on the screens)
	local TS, TX, TZ = 1.2, 21.5, 56.8
	local TOTEM = { scale = TS, solid = true, color = { ["17141f"] = "2e3140" } }
	H.put("st_totem", "Totem", -TX, 0, TZ, 90, TOTEM); H.put("st_totem", "Totem", TX, 0, TZ, -90, TOTEM)
	local TW, TH, TY, TO, TT = 1.9 * TS, 4.75 * TS, 5.7 * TS, 0.6 * TS + 0.03, { clear = true, flush = true, thick = 0.1 }
	H.text("TotemText", { { "TRAINING", GREEN, "L", 0.2 }, { "<<<", GREEN, "L", 0.2 }, { "behind you, on your left. follow the green line. staff only. you are staff now.", "ffffff", "F", 0.6 } }, TW, TH, -TX + TO, TY, TZ, 90, TT)
	H.text("TotemText", { { "EXIT", "ffffff", "L", 0.22 }, { "the doors you came in by. they are still doors.", "c8c8dc", "F", 0.6 } }, TW, TH, -TX - TO, TY, TZ, -90, TT)
	H.text("TotemText", { { "YOU ARE HERE", YEL, "L", 0.26 }, { "so is the duck. six stalls, six queues. stand on a colour. that is the whole plan.", "ffffff", "F", 0.7 } }, TW, TH, TX - TO, TY, TZ, -90, TT)
	H.text("TotemText", { { "OTHER HUBS", YEL, "L", 0.26 }, { "the glowing discs by the doors. yellow goes on. pink goes home.", "ffffff", "F", 0.66 } }, TW, TH, TX + TO, TY, TZ, 90, TT)
	-- south-west: the information kiosk and a bench by the staff door
	local kiosk = H.put("dp_office", "Kiosk", -70, 0, 57, 90, { back = true, solid = true, color = { ["17141f"] = "2e3140", ["1f2230"] = "2e3140" } })
	-- (its windows burnt to white: now a deeper amber glow, with a real warm lamp inside)
	if kiosk then for _, p in kiosk:GetDescendants() do if p:IsA("BasePart") and p.Name:find("_ffe9b8", 1, true) then p.Color = Color3.fromHex("b98a42") end end end
	H.lamp(-63, 5, 57, 18, 0.7, "ffd9a0")
	H.text("KioskSign", { { "INFORMATION", YEL, "L", 0.6 }, { "we don't have any.", "ffffff", "F", 0.36 } }, 11, 1.8, -58.13, 8.6, 57, 90, { clear = true })
	H.put("st_bench", "Bench", -58, 0, 50, 90, { back = true, solid = true }) -- (under the kiosk's windows, clear of its sign and its door)
	-- south-east: the food truck, a booth, vending, two more tables
	H.put("wh_van", "FoodTruck", 62.5, 0, 57, 180, { solid = true })
	H.text("TruckSign", { { "FOOD TRUCK", YEL, "L", 0.6 }, { "parked indoors. nobody asks.", "17141f", "F", 0.34 } }, 12.5, 4.4, 57.43, 6.8, 59.7, -90, { clear = true })
	H.put("hb_vending", "Vending", 22, 0, 70, 180, { back = true, solid = true, color = { [PINK] = CYAN, ["17141f"] = "2e3140" } })
	H.put("hb_vending", "Vending", 26.2, 0, 70, 180, { back = true, solid = true, color = { [PINK] = YEL, ["17141f"] = "2e3140" } })
	H.put("bc_arcade", "Arcade", 30.4, 0, 70, 180, { back = true, solid = true, color = { ["17141f"] = "2e3140", ["120818"] = "2e3140" } })
	booth(41, 70, 180)
	H.put("fc_table", "Table", 25, 0, 50, 15, { solid = Vector3.new(6, 3.3, 6), color = { [YEL] = PINK } }); H.put("fc_table", "Table", 35.5, 0, 54.5, 40, { solid = Vector3.new(6, 3.3, 6), color = { [YEL] = CYAN } })
	-- three notices on the bare stretches of wall: over the booth, over the kiosk, over the truck
	H.screen("AdSpecial", { { "TODAY'S SPECIAL", YEL, "L", 0.3 }, { "the same as yesterday's special. yesterday's was also this.", "ffffff", "F", 0.6 } }, 34, 27, 69.2, 180, 18)
	H.screen("AdLost", { { "LOST PROPERTY", PINK, "L", 0.3 }, { "one duck. large. yellow. if it is yours, we have questions.", "ffffff", "F", 0.6 } }, -69.2, 27, 57, 90, 18)
	H.screen("AdParking", { { "INDOOR PARKING", CYAN, "L", 0.3 }, { "spaces: 1. taken: 1. please stop asking the truck to move.", "ffffff", "F", 0.6 } }, 69.2, 27, 57, -90, 18)
	-- the north corners: a booth under each giant tree
	booth(-56, -70, 0); booth(56, -70, 0)
	local sp = {}
	for _, z in { 50, 54 } do for _, x in { -6, -2, 2, 6 } do table.insert(sp, { x, z }) end end
	H.spawns(sp)
	H.trainingDoor(-31, 70, 180, { "TRAINING", "staff only. staff is a state of mind." }, { frame = { a4aab8 = "e8ecf4" }, head = "e8ecf4" })
	H.text("TrainingBig", { { "TRAINING", GREEN, "L", 1 } }, 20, 4.5, -31, 27.5, 69.7, 180) -- (big, on the wall over the door: it reads from across the court)
	H.tourDiscs(0, 62.5, 16)
	H.zone(-70, 70, -70, 70, 44, "lab_foodcourt")
	return H.done()
end
-- ------------------------------------------------------------------ the way out of Hub 1: four discs on the rotunda floor
L.SITES.Hub1_Tour = Vector3.new(0, 240, -8036)
L.BUILD.Hub1_Tour = function(H)
	local cols = { CYAN, PINK, YEL, GREEN }
	-- out by the two south diagonal walls, two a side: clear of the four doorways, of the stage and of the spawn rows
	-- (spawn rows are at x +-2.2 and +-6.6, z -18 and -22.5: every disc is 9 or more from the nearest point, and the
	-- end of every sign board 4 or more; the boards stop short of the corner piers)
	local at = { { 20.6, -9.3 }, { 15.6, -17.7 }, { -15.6, -17.7 }, { -20.6, -9.3 } }
	for i, n in L.ORDER do
		H.disc("To" .. n, at[i][1], at[i][2], "HUB " .. (i + 1), L.TITLE[n], n .. "_Arrive", L.TITLE[n], cols[i])
	end
	return H.done()
end

L.FASCIA_OUT, L.FASCIA_Y = 6.26, 11.95 -- where a stall's name plate is, out from the wall and up (set from the fc_stall model)

--@HUBS@

return L
