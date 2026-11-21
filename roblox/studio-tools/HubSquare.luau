--!nonstrict
-- C: THE SQUARE (20 Nov 2026; the owner picked "all 3", the Square first: the concepts sheet's fullest from the spawn).
-- A covered square round a screen tower, a gallery round it at 12 with columns and a glass rail, a roof of steel beams
-- and white panels with a lantern over the tower; four wide openings in thin steel frames, each with a lit strip and its
-- name over it, into the wings: the PADS gallery north (ten gates set into its walls), the GYM east (its four rings in
-- sight from the square), the ARMORY and the training gate west, the LOUNGE street south (the shop and Looticus, the
-- bundles, the arcade, the tables, seats and a bar, VIP at its end) with the GOLF room off it.
-- World studs from the site (x east, z south, y up). Built from HubKit; the convention: side-session-notes/HUB-MARKERS.md.
-- HS.build(parent, name, site) -> the folder; HS.check() -> issues; HS.SHOTS for the photos.
local HS = {}
HS.ID, HS.FOLDER, HS.TITLE, HS.ORDER = "square", "Square", "THE SQUARE", 1
HS.SITE = CFrame.new(-200, 240, -12600)

function HS.build(K, parent, name, site, live)
	local P, MAT = K.P, K.MAT
	local F0 = CFrame.new()
	local f = K.begin(parent, name or HS.FOLDER, site or HS.SITE, HS.ID, { Title = HS.TITLE, Order = HS.ORDER }, live)
	local box, cyl = K.box, K.cyl
	local H, GY, TOP = 11, 12.4, 34 -- (the openings' head, the gallery's floor, the roof's underside)

	-- ============================================================== THE SQUARE
	-- the floor: a paved field, a darker border band, a ring round the tower (pieces side by side: no two tops in one plane)
	box(F0, "Shell", "Floor", -29, 29, -1, 0, -29, 29, P.paving, MAT.Slate)
	for _, s in { -1, 1 } do
		box(F0, "Shell", "FloorBand", s * 29, s * 34, -1, 0, -34, 34, P.paving2, MAT.Slate)
		box(F0, "Shell", "FloorBand", -29, 29, -1, 0, s * 29, s * 34, P.paving2, MAT.Slate)
	end
	-- the walls: openings N (pads), E (gym), W (armory), S (lounge), each under the gallery
	K.wall(F0, "Wall", -34, 34, 0, TOP, -34, -32, P.wallLt, { { -18, 18, H } })
	K.wall(F0, "Wall", -34, 34, 0, TOP, 32, 34, P.wallLt, { { -20, 20, H }, { 28, 32, 8.5 } }) -- (28..32: the zombies room's doorway, clear of the east wall's end)
	K.wall(CFrame.Angles(0, -math.pi / 2, 0), "Wall", -32, 32, 0, TOP, -34, -32, P.wallLt, { { -20, 20, H } }) -- (east: its x runs south)
	K.wall(CFrame.Angles(0, math.pi / 2, 0), "Wall", -32, 32, 0, TOP, -34, -32, P.wallLt, { { -12, 12, H } }) -- (west: its x runs north)
	local FN, FS, FE, FW = CFrame.new(), CFrame.Angles(0, math.pi, 0), CFrame.Angles(0, -math.pi / 2, 0), CFrame.Angles(0, math.pi / 2, 0)
	local WS = { signZ = -26.15, signY = GY - 1.5 - 0.95 } -- (under the gallery's fascia, facing the square)
	K.thinFrame(FN, -18, 18, H, -32, "PADS", WS)
	K.thinFrame(FS, -20, 20, H, -32, "LOUNGE  ·  SHOP  ·  VIP", { signW = 22, signZ = WS.signZ, signY = WS.signY })
	K.thinFrame(FE, -20, 20, H, -32, "GYM", WS)
	K.thinFrame(FW, -12, 12, H, -32, "ARMORY  ·  TRAINING", { signW = 20, signZ = WS.signZ, signY = WS.signY })
	box(F0, "Shell", "Roof", -34, 34, TOP, TOP + 1, -34, 34, P.dome)
	-- the gallery round the square at 12: its slab, a cream fascia, the glass rail, columns under its edge; pilasters on
	-- the walls above it; a band
	for _, R in { FN, FS, FE, FW } do
		local gx = if R == FN or R == FS then 32 else 26 -- (the corners belong to the north and south runs)
		box(R, "Shell", "Gallery", -gx, gx, GY - 1, GY, -32, -26, P.floor2)
		box(R, "Scenery", "GalleryFascia", -26.3, 26.3, GY - 1.5, GY + 0.2, -26.3, -25.8, P.cream) -- (the inner edge, all four the same length: they meet at the corners)
		K.rail(R, -26, 26, GY, -26)
		for _, x in { -26, -14, 14, 26 } do
			if math.abs(x) < 26 or R == FN or R == FS then K.column(R, x, -25.9, 0, GY - 1, 1.8, { cap = GY - 1 }) end
		end
		for _, x in { -26, -14, 14, 26 } do box(R, "Scenery", "Pilaster", x - 0.9, x + 0.9, GY, TOP, -32, -31.4, P.pier) end
		box(R, "Scenery", "WallBand", -gx + (if gx == 26 then 5.6 else 0), gx - (if gx == 26 then 5.6 else 0), 22, 22.6, -32, -31.7, P.cream) -- (the side runs' bands stop short of the long runs')
		K.bench(R * CFrame.new(0, GY, -30.9) * CFrame.Angles(0, math.pi, 0), 18, { back = true }) -- (against the wall, facing the square)
		K.panel(R, 0, GY - 1, -29, 16, 3, { bright = 0.8, range = 16 })
	end
	-- (the side runs' rails between the long runs' ends)
	-- the roof: steel beams every 8, white panels between, a lantern over the tower
	for v = -24, 24, 8 do
		box(F0, "Scenery", "RoofBeam", -32, 32, TOP - 2, TOP, v - 0.45, v + 0.45, P.cream, nil, { ghost = true })
		box(F0, "Scenery", "RoofBeam", v - 0.45, v + 0.45, TOP - 2, TOP, -32, 32, P.cream, nil, { ghost = true })
	end
	for x = -20, 20, 8 do for z = -20, 20, 8 do
		if math.abs(x) > 8 or math.abs(z) > 8 then K.panel(F0, x, TOP, z, 6.4, 6.4, { range = 40, bright = 0.6 }) end -- (40: from 34 up the light must reach the floor)
	end end
	box(F0, "Scenery", "LanternGlow", -7.6, 7.6, TOP - 0.2, TOP, -7.6, 7.6, P.light, MAT.Neon, { ghost = true, noshadow = true })

	-- the screen tower: a column, four screens of the counts (HubScreen: HubConsole writes them), a planter and a ring of
	-- benches round its foot
	box(F0, "Shell", "Tower", -3, 3, 0, 26, -3, 3, P.pier2, MAT.Concrete)
	local scr = box(F0, "Scenery", "TowerScreen", -6.5, 6.5, 14, 21, -6.5, 6.5, P.screen)
	K.screen(scr)
	box(F0, "Scenery", "TowerCap", -7, 7, 21, 21.8, -7, 7, P.creamHi); box(F0, "Scenery", "TowerFoot", -7, 7, 13.2, 14, -7, 7, P.creamHi)
	cyl(F0, "Shell", "TowerPlanter", 0, 0, 2.2, 0, 13, P.cream)
	cyl(F0, "Scenery", "TowerSoil", 0, 2.2, 2.26, 0, 12.2, P.soil)
	for i = 0, 7 do K.ball(F0, "Scenery", "Bush", math.cos(i * math.pi / 4) * 4.6, 3.2, math.sin(i * math.pi / 4) * 4.6, 2.8, if i % 2 == 0 then P.plant else P.plant2, MAT.Grass) end
	for i = 0, 7 do
		local a = i * math.pi / 4 + math.pi / 8
		K.bench(CFrame.new(math.sin(a) * 9.4, 0, -math.cos(a) * 9.4) * CFrame.Angles(0, -a, 0), 4.2) -- (facing out)
	end
	-- the SPECTATE board on the west wall over the gallery, facing the spawn's side of the square
	K.spectateSpot(K.facing(-32, 0, 1, 0, 21), 16, 9) -- (its frame clears the gallery bench's back below it)
	-- the corners: YOUR LOADOUT (NE), the bundles (SW), seats (SE, NW); the HUBS terminal by the spawn; jump pads up
	K.holoLoadout(K.at(F0, 21, -21, 225))
	K.bundles(K.at(F0, -21, 21, -45))
	-- (the SE corner stays clear: the way to the zombies room)
	K.cluster(K.at(F0, -21, -21, -135))
	for _, s in { -1, 1 } do K.jumpPad(K.at(F0, s * 20, 2, if s > 0 then -90 else 90), Vector3.new(0, 60, 9)) end
	-- the spawn: a rug, the spawn points facing north, the arrival point, the travel terminal
	cyl(F0, "Scenery", "SpawnRing", 0, -0.02, 0.06, 22, 12.4, P.creamHi)
	cyl(F0, "Scenery", "SpawnRug", 0, 0.06, 0.1, 22, 11.6, P.carpet2, MAT.Fabric)
	for i = 0, 7 do K.marker(F0, "HubSpawns", "Spawn", -3.6 + (i % 4) * 2.4, 0.1, 21 + math.floor(i / 4) * 2.4, 0) end
	K.marker(F0, "HubArrive", "Arrive", 0, 0.1, 17, 0)
	K.travelTerminal(K.at(F0, 9, 25, -20))

	-- ============================================================== N: THE PADS GALLERY
	-- (21 Nov: the CLASSIC pads, the owner's pick, as in THE HOTEL) 50 wide, five bays a side 17 long between chunky fins,
	-- 1V1 nearest the square; each pad flush in front of its bay's wall, its board and mode plaque FLAT on the wall (the
	-- owner: "no angeld"). Round 2 (both judges, the copy check: a straight runway with the pads mirrored down both walls
	-- to one thing at the end is the reference's pad corridor): the east bank STAGGERED half a bay; no runner: a planted
	-- SPINE of three islands down the middle (benches facing the pads) splits the walk into two lanes, a crossing between
	-- the islands; a spine beam overhead with the bays' beams off it (herringbone), the lights a step down over the lanes
	local BAY = 17
	local NZ0, NH = -34, 20
	local OFF = { [-1] = 0, [1] = BAY / 2 } -- (the east bank half a bay further in)
	local NZ1 = NZ0 - 5 * BAY - BAY / 2 - 6
	box(F0, "Shell", "Floor", -25, 25, -1, 0, NZ1, NZ0, P.floor2)
	box(F0, "Shell", "Roof", -27, 27, NH, NH + 1, NZ1 - 2, NZ0, P.dome)
	box(F0, "Shell", "Wall", -27, 27, 0, NH, NZ1 - 2, NZ1, P.wallLt)
	for _, s in { -1, 1 } do
		box(F0, "Shell", "Wall", s * 25, s * 27, 0, NH, NZ1, NZ0, P.wallLt)
		local za, zb = NZ0 - OFF[s], NZ0 - OFF[s] - 5 * BAY -- (this bank's first and last fin)
		for k = 0, 5 do -- (the fins between the bays, chunky, a pilaster face on each; a beam off each to the spine)
			local z = za - k * BAY
			box(F0, "Shell", "GateFin", s * 22.6, s * 25, 0, NH, z - 1.3, z + 1.3, P.wallLt2)
			box(F0, "Scenery", "FinPilaster", s * 22.2, s * 22.65, 0, NH - 1.2, z - 1.0, z + 1.0, P.pier)
			box(F0, "Scenery", "CeilingBeam", s * 1.1, s * 22.6, NH - 1.6, NH, z - 0.6, z + 0.6, P.cream, nil, { ghost = true })
		end
		-- (the bank's ends: solid piers to the mouth and to the end wall, a bench against each long enough for one)
		for _, e in { { NZ0, za + 1.3 }, { zb - 1.3, NZ1 } } do
			if e[1] - e[2] > 0.1 then
				box(F0, "Shell", "BankEnd", s * 22.6, s * 25, 0, NH, e[2], e[1], P.wallLt2)
				if e[1] - e[2] >= 7 then K.bench(K.at(F0, s * 21.4, (e[1] + e[2]) / 2, s * 90), math.min(10, e[1] - e[2] - 1.6), { back = true }) end
			end
		end
		for i, md in K.MODES do
			local zc = za - BAY / 2 - (i - 1) * BAY
			local dp = (K.CLASSIC_SIZE[md.id] or { 13.6, 11 })[2]
			K.pad(K.facing(s * (22.4 - dp), zc, s, 0), md, if s < 0 then "lifts" else "east", if s < 0 then md.id else md.id .. "_e",
				{ boardAt = K.facing(s * 24.95, zc, -s, 0, 9.8), headerAt = K.facing(s * 24.95, zc, -s, 0, 14.6) })
			box(F0, "Scenery", "PadThreshold", s * 6.4, s * (22.4 - dp), 0, 0.05, zc - 1.5, zc + 1.5, P.floor, nil)
			K.panel(F0, s * 11.5, NH, zc, 9, 5, { bright = 0.6, range = 24 })
		end
	end
	box(F0, "Scenery", "CeilingSpine", -1.1, 1.1, NH - 1.9, NH, NZ1, NZ0, P.cream, nil, { ghost = true })
	-- the spine: two islands (a planter, bushes, a bench either side facing its bank) and, between them, the gallery's
	-- middle: a big round planted settee on a dais under a round lantern (the walk splits round it; it closes the view
	-- down the middle, so the hall reads as two lanes round a centre, not one runway to its end)
	for _, zc in { NZ0 - 23, NZ0 - 81 } do
		local Fi = F0 * CFrame.new(0, 0, zc)
		box(Fi, "Shell", "Planter", -1.3, 1.3, 0, 2.2, -7, 7, P.cream)
		box(Fi, "Scenery", "PlanterSoil", -1.0, 1.0, 2.2, 2.26, -6.7, 6.7, P.soil)
		for i = -2, 2 do K.ball(Fi, "Scenery", "Bush", 0, 3.1, i * 2.6, 2.8, if i % 2 == 0 then P.plant else P.plant2, MAT.Grass) end
		for _, s in { -1, 1 } do K.bench(Fi * CFrame.new(s * 2.6, 0, 0) * CFrame.Angles(0, math.rad(if s < 0 then 90 else -90), 0), 12) end
	end
	local ZM = NZ0 - 52
	cyl(F0, "Shell", "MidDais", 0, 0, 0.5, ZM, 12, P.pier)
	cyl(F0, "Scenery", "MidDaisNosing", 0, 0.45, 0.6, ZM, 12.4, P.creamHi)
	cyl(F0, "Shell", "MidSeat", 0, 0.5, 1.9, ZM, 9.6, P.wood, MAT.Wood)
	cyl(F0, "Scenery", "MidSeatPad", 0, 1.9, 2.1, ZM, 9.2, P.carpet2, MAT.Fabric)
	cyl(F0, "Shell", "MidPlanter", 0, 2.1, 4.2, ZM, 5.6, P.cream)
	cyl(F0, "Scenery", "MidSoil", 0, 4.2, 4.26, ZM, 5, P.soil)
	K.ball(F0, "Scenery", "Bush", 0, 5.9, ZM, 4.4, P.plant, MAT.Grass)
	for a = 0, 300, 60 do
		local r = math.rad(a)
		K.ball(F0, "Scenery", "Bush", math.sin(r) * 1.7, 5.0, ZM + math.cos(r) * 1.7, 2.4, if a % 120 == 0 then P.plant2 else P.plant, MAT.Grass)
		K.seat(F0, math.sin(r) * 4.1, 2.1, ZM + math.cos(r) * 4.1, a + 180)
	end
	cyl(F0, "Scenery", "MidLantern", 0, NH - 2.9, NH - 1.95, ZM, 10, P.cream, nil, { ghost = true })
	K.light(cyl(F0, "Scenery", "MidLanternGlow", 0, NH - 3.0, NH - 2.9, ZM, 8.6, P.light, MAT.Neon, { ghost = true, noshadow = true }), 22, 0.6)
	-- (one sign at the gallery's mouth says how the pads work: the boards don't)
	K.wordSign(K.facing(0, NZ0 - 2, 0, 1), "Scenery", "WaySign", 14, 1.7, 0, 16.6, 0, "STEP ON A SIDE TO QUEUE", { bg = "28324a" })
	K.trophyWall(K.at(F0, 0, NZ1 + 0.05, 180)) -- (its look south, into the gallery)
	do -- (the ranked boards at the end: a lit navy face with its name at rest, under whatever the board shows; no dead black)
		local site = f:GetAttribute("Site")
		for _, d in f:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "LiveBoardPanel" and site and (d.Position - site).Z < NZ1 + 10 then
				d.Color = K.c3("28324a")
				for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
					local g = Instance.new("SurfaceGui"); g.Name = "Rest"; g.Face = face; g.LightInfluence = 0; g.Brightness = 1.4
					g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 20; g.Parent = d
					local fr = Instance.new("Frame"); fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = K.c3("28324a"); fr.BorderSizePixel = 0; fr.Parent = g
					local t = Instance.new("TextLabel"); t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(0.84, 0.3); t.Position = UDim2.fromScale(0.08, 0.26)
					t.Font = Enum.Font.GothamBlack; t.TextScaled = true; t.TextColor3 = K.c3("f2f0ea"); t.Text = "RANKED"; t.Parent = fr
					local u = Instance.new("TextLabel"); u.BackgroundTransparency = 1; u.Size = UDim2.fromScale(0.7, 0.14); u.Position = UDim2.fromScale(0.15, 0.6)
					u.Font = Enum.Font.GothamSemibold; u.TextScaled = true; u.TextColor3 = K.c3("c8d0e0"); u.Parent = fr
					u.Text = if (d.Position - site).X > 0 then "DUELS" else "PARTIES"
				end
			end
		end
	end

	-- ============================================================== E: THE GYM
	K.gym(CFrame.new(), { x0 = 34, x1 = 98, z0 = -32, z1 = 32, h = 24, open = { 32, -20, 20 }, rings = { { 50, -14 }, { 82, -14 }, { 50, 14 }, { 82, 14 } },
		locker = { x0 = 62, x1 = 98, z0 = 36, z1 = 60, door = { 84, 90 } } })

	-- ============================================================== W: THE ARMORY, the training gate at its end
	K.armory(CFrame.Angles(0, math.pi / 2, 0), { d0 = 34, d1 = 80, w = 20, h = 16, open = 12, door = "SquareToTraining" })

	-- ============================================================== S: THE LOUNGE STREET, VIP at its end
	local SZ0, SZ1, SH = 34, 90, 16
	box(F0, "Shell", "Floor", -26, 26, -1, 0, SZ0, SZ1 + 2, P.wood, MAT.WoodPlanks)
	box(F0, "Scenery", "Runner", -3.5, 3.5, 0, 0.05, SZ0, SZ1, P.carpet, MAT.Fabric)
	K.wall(FE, "Wall", SZ0, SZ1, 0, SH, -26, -24, P.creamWall, {}) -- (east: FE's x runs south)
	K.wall(FW, "Wall", -SZ1, -SZ0, 0, SH, -26, -24, P.creamWall, { { -50, -42, 10 } }) -- (west, the golf room's door at z 42..50: FW's x runs north)
	-- (the wainscot leaves the shop's shelves, the golf door and the code panel's place clear)
	for _, w in { { 1, 34, 43 }, { 1, 61, 90 }, { -1, 34, 42 }, { -1, 50, 57 }, { -1, 63, 90 } } do
		box(F0, "Scenery", "Wainscot", w[1] * 23.8, w[1] * 24, 0, 4, w[2], w[3], P.wood, MAT.Wood)
		box(F0, "Scenery", "WainscotCap", w[1] * 23.7, w[1] * 24, 4, 4.25, w[2], w[3], P.cream)
	end
	for _, sd in { -1, 1 } do
		box(F0, "Scenery", "StreetBand", sd * 23.6, sd * 24, 11.6, 12.2, SZ0, SZ1, P.cream)
		K.light(box(F0, "Scenery", "StreetCove", sd * 23.25, sd * 23.6, 12.05, 12.2, SZ0 + 1, SZ1 - 1, P.light, MAT.Neon, { ghost = true, noshadow = true }), 12, 0.8, P.warm,
			{ kind = "SurfaceLight", face = Enum.NormalId.Top, angle = 140 })
		for _, z in { 36, if sd < 0 then 70 else 64, 88 } do box(F0, "Scenery", "StreetPilaster", sd * 23.2, sd * 24, 0, SH, z - 0.8, z + 0.8, P.creamHi) end -- (west: 70, clear of the code panel's side spots at 54.4 and 65.6)
	end
	-- the banquette along the east wall, its small tables
	box(F0, "Shell", "Banquette", 21.4, 23.2, 0.4, 1.5, 66, 86, P.woodDark, MAT.Wood)
	box(F0, "Scenery", "BanquettePad", 21.5, 23.1, 1.5, 1.75, 66.1, 85.9, P.carpet2, MAT.Fabric)
	box(F0, "Scenery", "BanquetteBack", 22.7, 23.2, 1.75, 4.6, 66, 86, P.carpet2, MAT.Fabric)
	box(F0, "Scenery", "BanquetteFoot", 21.6, 23.2, 0, 0.4, 66.2, 85.8, P.steel)
	for z = 67.1, 85, 2.2 do K.seat(F0, 22.2, 1.75, z, 90) end
	for _, z in { 70, 77, 84 } do
		K.cyl(F0, "Shell", "CafeTable", 19.2, 2.3, 2.5, z, 2.6, P.creamHi)
		K.cyl(F0, "Scenery", "CafeTableStem", 19.2, 0, 2.3, z, 0.3, P.steel)
		K.cyl(F0, "Scenery", "CafeTableFoot", 19.2, 0, 0.12, z, 1.4, P.steel)
	end
	K.showcase(K.at(F0, -7, 62, 0), "minigun"); K.showcase(K.at(F0, 7, 62, 0), "redline")
	for _, x in { -21, 21 } do
		K.cyl(F0, "Shell", "TallPlanter", x, 0, 3.2, 88, 2.6, P.cream)
		K.ball(F0, "Scenery", "Bush", x, 4.6, 88, 3.4, P.plant2, MAT.Grass)
	end
	box(F0, "Shell", "Roof", -26, 26, SH, SH + 1, SZ0, SZ1 + 2, P.dome)
	for z = 39, 79, 10 do K.panel(F0, 0, SH, z, 10, 4, { bright = 1.0, range = 24 }) end
	for z = 44, 84, 10 do box(F0, "Scenery", "CeilingBeam", -24, 24, SH - 1.4, SH, z - 0.5, z + 0.5, P.cream, nil, { ghost = true }) end
	K.shop(K.at(F0, 19, 52, 90), 18)
	K.arcadeSpot(K.at(F0, -22.2, 38, -90)) -- (hub-minigames: 0.2 off the wainscot cap)
	K.tableSpot(K.at(F0, -9, 48, 0), "board"); K.tableSpot(K.at(F0, 9, 48, 0), "arm")
	K.cluster(K.at(F0, -16, 72, -90), { npcSofa = true, lampY = SH }); K.cluster(K.at(F0, 9, 74, 90), { npcSofa = true, lampY = SH })
	K.bar(K.at(F0, -20.6, 80, -90))
	K.codePanelSpot(K.at(F0, -24, 60, -90, 0))
	K.vip(CFrame.new(0, 0, SZ1) * CFrame.Angles(0, math.pi, 0), { w = 16, d = 24, h = 14, front = 26, frontH = SH })

	-- ============================================================== THE ZOMBIES ROOM, off the square's south-east corner
	K.zombieRoom(CFrame.new(30, 0, 32) * CFrame.Angles(0, math.pi, 0), { x0 = -20, x1 = 2, d = 18, h = 11, door = 4, guideSide = 1 })

	-- ============================================================== THE GOLF ROOM, off the street's west side
	K.golfRoom(CFrame.new(), { x0 = -82, x1 = -28, z0 = 38, z1 = 132, h = 18, door = { -26, 42, 50 } })

	-- ============================================================== THE REGULARS
	-- Looticus (the shop's man): on the street's sofas, behind the shop counter, behind the bar; he puffs between them
	local LOOT = { { "sit", -19.5, 1.45, 70.4, -90 }, { "sit", -19.5, 1.45, 73.6, -90 }, { "sit", 12.5, 1.45, 72.4, 90 }, { "sit", 12.5, 1.45, 75.6, 90 },
		{ "stand", 21.4, 0, 52, 90 }, { "stand", -22.4, 0, 80, -90 } }
	K.npc(F0, "Looticus", LOOT[1][2], LOOT[1][3], LOOT[1][4], LOOT[1][5])
	for k, w in LOOT do K.npcPoint(F0, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5]) end
	-- Frisk1636 (ranked): along the north gallery's rail, looking down at the square
	local FR = { { "stop", -16 }, { "via", -8 }, { "stop", 0 }, { "via", 8 }, { "stop", 16 } }
	K.npc(F0, "Frisk1636", FR[1][2], GY, -28.4, 180)
	for k, w in FR do K.npcPoint(F0, "Frisk1636", k, w[1], "stand", w[2], GY, -28.4, 180, { pause = if w[1] == "stop" then { 8, 16 } else nil }) end
	-- Dune (quests): round three sides of the gym's first ring
	local DU = { { "stop", 36.5, -14, -90 }, { "via", 36.5, -27.4, 180 }, { "stop", 50, -27.4, 180 }, { "via", 65, -27.4, 180 }, { "stop", 65, -14, 90 } }
	K.npc(F0, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for k, w in DU do K.npcPoint(F0, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end
	return f
end

-- the check: the ways that must stay clear (walks) and the rooms no ray may get out of (leaks), in site frames
function HS.walks(K)
	local F0 = CFrame.new()
	return {
		{ "the square, spawn round the tower", F0, 11.5, 17, -14, 18 }, { "the square, the tower to the pads", F0, -10, 10, -32, -12 },
		{ "the pads gallery's west lane", F0, -10.6, -6.6, -126, -36 }, { "the pads gallery's east lane", F0, 6.6, 10.6, -126, -36 },
		{ "the square to the gym", F0, 22, 38, -6, 6 }, { "the square to the armory", F0, -40, -24, -5, 5 },
		{ "the square to the lounge", F0, -3, 3, 26, 88 }, { "the street to the golf room", F0, -32, -20, 43, 49 },
		{ "into the zombies room", F0, 28.5, 31.5, 26, 39 },
	}
end
function HS.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 8, 10 }, { F0, 0, 20, 0 }, { F0, 0, 8, -70 }, { F0, 7, 8, -112 }, { F0, 66, 10, 0 }, { F0, -56, 8, 0 }, { F0, 0, 8, 62 }, { F0, -55, 8, 85 }, { F0, 0, 6, 104 }, { F0, 40, 6, 44 } }
end
HS.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 27), Vector3.new(0, 9.5, -20) },
	{ "gym", Vector3.new(8, 6.2, 6), Vector3.new(72, 3, -2) },
	{ "pads", Vector3.new(9, 5.8, -48), Vector3.new(-24, 4, -60) },
	{ "lounge", Vector3.new(-2, 6.2, 37), Vector3.new(4, 4, 88) },
	{ "gallery", Vector3.new(-26, 17.6, 28), Vector3.new(6, 8, -12) },
	{ "zombies", Vector3.new(24, 6, 20), Vector3.new(36, 4, 44) },
}
return HS
