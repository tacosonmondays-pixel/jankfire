--!strict
-- ZOMBIES: the test map (weapons-port, 20 Nov 2026), a plain blockout built to the map contract (roblox/docs/ZOMBIES.md)
-- so the mode can be tested before the school is ready. three areas: START (the squad starts here), HALL (east, through
-- a 750 shutter, double height with a LOFT up a stair: the multi-floor nav) and YARD (west, through a 1000 shutter).
-- seven windows with closed-in ledges outside, five wall guns, four spawns. run in Edit: it builds Model "ZTest" into
-- ServerStorage.ZMMaps (replacing an old one). nothing of it is in workspace until a game starts (Zombies.start clones it
-- far away). studs throughout; the floor's top is y 0
return function(): Model
	local SS = game:GetService("ServerStorage")
	local lib = SS:FindFirstChild("ZMMaps") or Instance.new("Folder")
	lib.Name = "ZMMaps"
	lib.Parent = SS
	local old = lib:FindFirstChild("ZTest")
	if old then old:Destroy() end
	local M = Instance.new("Model")
	M.Name = "ZTest"
	local geo = Instance.new("Folder"); geo.Name = "Geo"; geo.Parent = M
	local ZMf = Instance.new("Folder"); ZMf.Name = "ZM"; ZMf.Parent = M
	ZMf:SetAttribute("Label", "Test Block")
	ZMf:SetAttribute("Start", "start")
	local FLOOR, WALL, TRIM, SLATE = Color3.fromRGB(92, 96, 104), Color3.fromRGB(196, 198, 202), Color3.fromRGB(150, 154, 160), Color3.fromRGB(60, 66, 76)
	local H = 27 -- the roof's underside
	local function box(name: string, x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, col: Color3?, parent: Instance?): Part
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true
		p.Size = Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(z1 - z0))
		p.CFrame = CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		p.Color = col or WALL
		p.Material = Enum.Material.SmoothPlastic
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Parent = parent or geo
		return p
	end
	local function marker(name: string, cf: CFrame, size: Vector3, parent: Instance): Part
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Transparency = 1; p.Size = size; p.CFrame = cf; p.Parent = parent
		return p
	end
	local function folder(name: string): Folder
		local f = Instance.new("Folder"); f.Name = name; f.Parent = ZMf
		return f
	end
	local Areas, Doors, Windows, Buys, Spawns = folder("Areas"), folder("Doors"), folder("Windows"), folder("WallBuys"), folder("PlayerSpawns")
	-- a wall along x (at z) or along z (at x), from a to b, y0..y1, with holes { a, b, y0, y1 } along its length
	local T = 1.5
	local function wall(axis: string, at: number, a: number, b: number, y0: number, y1: number, holes: { { number } })
		table.sort(holes, function(h1, h2) return h1[1] < h2[1] end)
		local function seg(s0: number, s1: number, v0: number, v1: number)
			if s1 - s0 < 0.05 or v1 - v0 < 0.05 then return end
			if axis == "x" then box("Wall", s0, v0, at - T / 2, s1, v1, at + T / 2) else box("Wall", at - T / 2, v0, s0, at + T / 2, v1, s1) end
		end
		local cur = a
		for _, h in holes do
			seg(cur, h[1], y0, y1)
			seg(h[1], h[2], y0, h[3])
			seg(h[1], h[2], h[4], y1)
			cur = h[2]
		end
		seg(cur, b, y0, y1)
	end
	-- ---- floors, the roof, light
	box("Floor", -60, -1, -24, 72, 0, 24, FLOOR)
	box("Roof", -61.5, H, -25.5, 73.5, H + 1, 25.5, TRIM)
	for _, x in { -42, 0, 48 } do
		local l = box("Lamp", x - 3, H - 0.4, -1, x + 3, H, 1, Color3.new(1, 1, 1))
		l.Material = Enum.Material.Neon
		local pl = Instance.new("PointLight"); pl.Range = 60; pl.Brightness = 1.4; pl.Parent = l
	end
	-- ---- the loft over the hall's east half, the stair up to it (along +x on the south side), its rail
	box("Loft", 52, 11, -24, 72, 12, 24, FLOOR)
	for i = 1, 16 do box("Step", 28 + (i - 1) * 1.5, 0, 14, 28 + i * 1.5, 0.75 * i, 24, TRIM) end
	box("Rail", 51.4, 12, -24, 52, 15.5, 14, SLATE)
	-- ---- windows: the hole, the closed-in ledge outside, the markers
	local holes = { N = {}, S = {}, E = {}, W = {} }
	local function window(side: string, c: number, area: string, y0: number)
		local sill = y0 + 2.7
		table.insert(holes[side], { c - 3, c + 3, sill, sill + 6 })
		-- outward normal, the wall's outer face, along-the-wall axis
		local out = ({ N = Vector3.new(0, 0, -1), S = Vector3.new(0, 0, 1), E = Vector3.new(1, 0, 0), W = Vector3.new(-1, 0, 0) })[side]
		local face = ({ N = -24 - T, S = 24 + T, E = 72 + T, W = -60 - T })[side]
		local along = Vector3.new(math.abs(out.Z), 0, math.abs(out.X))
		local mid = (if out.X ~= 0 then Vector3.new(face, 0, c) else Vector3.new(c, 0, face))
		local function lbox(name: string, d0: number, d1: number, l0: number, l1: number, ya: number, yb: number)
			local p0 = mid + out * d0 + along * l0
			local p1 = mid + out * d1 + along * l1
			box(name, math.min(p0.X, p1.X), ya, math.min(p0.Z, p1.Z), math.max(p0.X, p1.X), yb, math.max(p0.Z, p1.Z), TRIM)
		end
		lbox("Ledge", 0, 9, -6, 6, y0 - 1, y0) -- its floor
		lbox("LedgeRoof", 0, 10, -7, 7, y0 + 10, y0 + 11)
		lbox("LedgeBack", 9, 10, -7, 7, y0 - 1, y0 + 10)
		lbox("LedgeSide", 0, 9, -7, -6, y0 - 1, y0 + 10)
		lbox("LedgeSide", 0, 9, 6, 7, y0 - 1, y0 + 10)
		local wm = Instance.new("Model"); wm.Name = "Window" .. side .. tostring(c); wm:SetAttribute("Area", area); wm.Parent = Windows
		local inner = mid - out * T
		marker("Out", CFrame.new(mid + out * 6 + Vector3.new(0, y0 + 0.5, 0)), Vector3.new(2, 1, 2), wm)
		marker("In", CFrame.new(inner - out * 4.5 + Vector3.new(0, y0 + 0.5, 0)), Vector3.new(2, 1, 2), wm)
		local bc = mid - out * (T / 2) + Vector3.new(0, sill + 3, 0)
		marker("Boards", CFrame.lookAt(bc, bc - out), Vector3.new(6, 6, 0.2), wm)
	end
	window("N", -10, "start", 0); window("S", 10, "start", 0)
	window("N", 40, "hall", 0); window("E", -10, "hall", 0); window("E", 10, "hall", 12)
	window("S", -42, "yard", 0); window("W", 0, "yard", 0)
	-- ---- the outer walls (with their windows) and the two inner ones (with the shutters' holes)
	wall("x", -24 - T / 2, -60 - T, 72 + T, 0, H, holes.N)
	wall("x", 24 + T / 2, -60 - T, 72 + T, 0, H, holes.S)
	wall("z", 72 + T / 2, -24, 24, 0, H, holes.E)
	wall("z", -60 - T / 2, -24, 24, 0, H, holes.W)
	wall("z", 24, -24, 24, 0, H, { { -6, 6, 0, 9 } })
	wall("z", -24, -24, 24, 0, H, { { -6, 6, 0, 9 } })
	-- ---- the shutters
	local function door(name: string, x: number, a: string, b: string, price: number)
		local d = Instance.new("Model"); d.Name = name; d:SetAttribute("A", a); d:SetAttribute("B", b); d:SetAttribute("Price", price); d.Parent = Doors
		local s = box("Shutter", x - 0.5, 0, -6, x + 0.5, 9, 6, SLATE, d)
		s.Material = Enum.Material.DiamondPlate
		box("Housing", x - 1.2, 9, -6.5, x + 1.2, 10.2, 6.5, TRIM, d)
	end
	door("ToHall", 24, "start", "hall", 750)
	door("ToYard", -24, "start", "yard", 1000)
	-- ---- the areas
	local function area(id: string, label: string, x0: number, z0: number, x1: number, z1: number)
		local p = marker(id, CFrame.new((x0 + x1) / 2, H / 2, (z0 + z1) / 2), Vector3.new(x1 - x0, H, z1 - z0), Areas)
		p:SetAttribute("Label", label)
	end
	area("start", "Start", -24, -24, 24, 24)
	area("hall", "Hall", 24, -24, 72, 24)
	area("yard", "Yard", -60, -24, -24, 24)
	-- ---- wall guns (on the inner face, facing into the room)
	local function buy(w: string, price: number, pos: Vector3, look: Vector3)
		local p = marker("Buy_" .. w, CFrame.lookAt(pos, pos + look), Vector3.new(4, 2, 0.2), Buys)
		p:SetAttribute("Weapon", w); p:SetAttribute("Price", price)
	end
	buy("revolver", 300, Vector3.new(-6, 4.5, 23.85), Vector3.new(0, 0, -1))
	buy("smg", 900, Vector3.new(6, 4.5, -23.85), Vector3.new(0, 0, 1))
	buy("shotgun", 1200, Vector3.new(58, 4.5, -23.85), Vector3.new(0, 0, 1))
	buy("ar", 1200, Vector3.new(71.85, 16.5, -6), Vector3.new(-1, 0, 0))
	buy("lever", 1100, Vector3.new(-59.85, 4.5, -10), Vector3.new(1, 0, 0))
	-- ---- spawns, the nav box
	for i, p in { Vector3.new(-6, 0, -6), Vector3.new(6, 0, -6), Vector3.new(-6, 0, 6), Vector3.new(6, 0, 6) } do
		marker("Spawn" .. i, CFrame.lookAt(p + Vector3.new(0, 0.5, 0), p + Vector3.new(1, 0.5, 0)), Vector3.new(2, 1, 2), Spawns)
	end
	marker("NavBounds", CFrame.new(6, 12.5, 0), Vector3.new(132, 27, 48), ZMf)
	M.PrimaryPart = nil
	M.Parent = lib
	return M
end
