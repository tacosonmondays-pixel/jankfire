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

	-- ============================================================== N: THE PADS COURT
	-- (21 Nov: the CLASSIC pads, the owner's pick, their boards and plaques FLAT on the bay walls: "no angeld")
	-- Round 3 (both judges twice, the copy check: any straight hall with the pads mirrored down both walls is the
	-- reference's pad corridor, whatever its dressing): the pads round a COURT, Rotunda style. An eleven-sided room off
	-- a short vestibule: the vestibule is one side, the ten others a bay each (1V1 either side of the way in, 4V4 at the
	-- back either side of the far corner), each pad flush in its bay facing the middle, its board and plaque flat on the
	-- bay's wall (so the boards across the court face the way in); chunky fins at the corners, ribs from a round lantern
	-- to each fin; in the middle a round planted settee. The ranked boards face each other in the vestibule.
	local NH = 20
	local NS = 11
	local HALF = math.pi / NS
	local AP = 31 -- (the bays' walls' distance from the middle)
	local CZ = -77
	local VZ0, VZ1 = -34, CZ + AP -- (the vestibule: from the square's north opening to the court's open side)
	local C = Vector3.new(0, 0, CZ)
	local PW, PD = 11.2, 9.4 -- (the court's pads: one size, so ten fit round it; o.dims)
	local function dir(t) return Vector3.new(math.sin(t), 0, -math.cos(t)) end -- (t from north, clockwise; the way in is south)
	local function sideF(t) return CFrame.lookAt(C, C + dir(t)) end
	local RV = AP / math.cos(HALF) -- (a corner's distance)
	-- the floor, the roof (a slab over the whole court; the corners outside its walls closed in)
	box(F0, "Shell", "Floor", -RV - 2.4, RV + 2.4, -1, 0, CZ - RV - 2.4, VZ1, "9a9286") -- (go-live: a warm mid grey, not the near-black brown)
	box(F0, "Shell", "Roof", -RV - 2.4, RV + 2.4, NH, NH + 1, CZ - RV - 2.4, VZ1, P.dome)
	-- the vestibule: 18 wide, its walls closing the square's 36-wide opening down to it; a lower ceiling
	box(F0, "Shell", "Floor", -9.1, 9.1, -1, 0, VZ1, VZ0, "9a9286")
	box(F0, "Shell", "Roof", -11.1, 11.1, 14, 15, VZ1, VZ0, P.dome)
	for _, s in { -1, 1 } do
		box(F0, "Shell", "Wall", s * 9.1, s * 11.1, 0, 14, VZ1, VZ0, P.wallLt)
		box(F0, "Shell", "Wall", s * 11.1, s * 18.5, 0, 14, VZ0 - 2, VZ0, P.wallLt) -- (behind the square's opening, either side)
		box(F0, "Scenery", "VestPilaster", s * 8.6, s * 9.1, 0, 13.4, VZ1 + 0.2, VZ1 + 1.0, P.pier)
		-- the ranked boards, one on each wall, facing each other
		K.boardSpot(K.facing(s * 9.1, (VZ0 + VZ1) / 2 + 0.4, -s, 0, 7.2), if s < 0 then "duels" else "party", 9.6, 7.4)
	end
	box(F0, "Shell", "Wall", -9.1, 9.1, 14, NH, VZ1 - 1, VZ1 + 1, P.wallLt) -- (over the court's open side, to its roof)
	box(F0, "Scenery", "VestLintel", -9.1, 9.1, 13.2, 14, VZ1 - 0.2, VZ1 + 1.2, P.cream)
	-- (26 Nov, the owner: no one-line signs. the STEP ON A SIDE sign is gone: the plaques and boards say what each pad is)
	-- the court's walls, fins and pads
	for k = 0, NS - 1 do
		local t = math.pi + k * 2 * HALF -- (k = 0: the way in, south)
		local Fs = sideF(t)
		local hl = (AP + 2) * math.tan(HALF) + 0.05
		if k > 0 then
			box(Fs, "Shell", "Wall", -hl, hl, 0, NH, -AP - 2, -AP, P.wallLt)
			box(Fs, "Scenery", "BayHead", -hl + 1, hl - 1, NH - 2.2, NH - 1.4, -AP + 0.6, -AP, P.cream) -- (a cornice over each bay)
			K.panel(Fs, 0, NH, -AP + 6.5, 8, 4, { bright = 0.6, range = 22 })
		end
		-- the fin at this side's left corner (between it and the next), a pilaster face; a rib from it to the lantern
		local tv = t - HALF
		local Fv = sideF(tv)
		if k ~= 0 and k ~= 1 then -- (the way in's corners: the vestibule's walls end there)
			box(Fv, "Shell", "GateFin", -0.7, 0.7, 0, NH, -RV - 0.5, -RV + 2.8, P.wallLt2)
			box(Fv, "Scenery", "FinPilaster", -0.9, 0.9, 0, NH - 1.2, -RV + 2.4, -RV + 2.9, P.pier)
		end
		K.rod(F0, "Scenery", "CeilingRib", C + Vector3.new(0, NH - 0.9, 0) + dir(tv) * 7.4, C + Vector3.new(0, NH - 0.9, 0) + dir(tv) * (RV - 1), 1.3, P.cream, nil, { ghost = true })
	end
	local MODEK = { 1, 2, 3, 4, 5 }
	for i, md in K.MODES do
		for _, s in { -1, 1 } do -- (west: the "lifts" bank; east: "east")
			local t = math.pi - s * MODEK[i] * 2 * HALF
			local d = dir(t)
			local F = C + d * (AP - 0.2 - PD)
			local B = C + d * (AP - 0.05)
			K.pad(K.facing(F.X, F.Z, d.X, d.Z), md, if s < 0 then "lifts" else "east", if s < 0 then md.id else md.id .. "_e",
				{ dims = { PW, PD }, boardAt = K.facing(B.X, B.Z, -d.X, -d.Z, 9.8), headerAt = K.facing(B.X, B.Z, -d.X, -d.Z, 15.4), headerW = 10.6, headerH = 3.2 }) -- (go-live, the judges: the plaque bigger)
		end
	end
	-- the lantern: a deep round drum in the ceiling's middle, its lit ring under it
	cyl(F0, "Scenery", "Lantern", 0, NH - 2.6, NH, CZ, 15, P.cream, nil, { ghost = true })
	K.light(cyl(F0, "Scenery", "LanternGlow", 0, NH - 2.7, NH - 2.6, CZ, 12.6, "d8cdb8", MAT.Neon, { ghost = true, noshadow = true, tr = 0.35 }), 34, 0.5) -- (go-live: it blew out in the photos)
	-- the middle: a big round planted settee on a dais (the walk goes round it)
	cyl(F0, "Shell", "MidDais", 0, 0, 0.5, CZ, 13, P.pier)
	cyl(F0, "Scenery", "MidDaisNosing", 0, 0.45, 0.6, CZ, 13.4, P.creamHi)
	cyl(F0, "Shell", "MidSeat", 0, 0.5, 1.9, CZ, 10.4, P.wood, MAT.Wood)
	cyl(F0, "Scenery", "MidSeatPad", 0, 1.9, 2.1, CZ, 10, P.carpet2, MAT.Fabric)
	cyl(F0, "Shell", "MidPlanter", 0, 2.1, 2.9, CZ, 6.2, P.cream) -- (go-live: lower, the far 4V4s show over it from the door)
	cyl(F0, "Scenery", "MidSoil", 0, 2.9, 2.96, CZ, 5.6, P.soil)
	K.ball(F0, "Scenery", "Bush", 0, 4.3, CZ, 3.6, P.plant, MAT.Grass)
	for a = 0, 300, 60 do
		local r = math.rad(a)
		K.ball(F0, "Scenery", "Bush", math.sin(r) * 1.7, 3.5, CZ + math.cos(r) * 1.7, 1.9, if a % 120 == 0 then P.plant2 else P.plant, MAT.Grass)
		K.seat(F0, math.sin(r) * 4.5, 2.1, CZ + math.cos(r) * 4.5, a + 180)
	end
	do -- (the ranked boards: a lit navy face with its name at rest, under whatever the board shows; no dead black)
		local site = f:GetAttribute("Site")
		for _, d in f:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "LiveBoardPanel" and site and math.abs((d.Position - site).Z - (VZ0 + VZ1) / 2) < 6 and math.abs((d.Position - site).X) < 10 then
				d.Color = K.c3("28324a")
				for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
					local g = Instance.new("SurfaceGui"); g.Name = "Rest"; g.Face = face; g.LightInfluence = 0; g.Brightness = 1.4
					g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 20; g.Parent = d
					local fr = Instance.new("Frame"); fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = K.c3("28324a"); fr.BorderSizePixel = 0; fr.Parent = g
					local t = Instance.new("TextLabel"); t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(0.84, 0.3); t.Position = UDim2.fromScale(0.08, 0.26)
					t.Font = Enum.Font.GothamBlack; t.TextScaled = true; t.TextColor3 = K.c3("f2f0ea"); t.Text = "RANKED"; t.Parent = fr
					local u = Instance.new("TextLabel"); u.BackgroundTransparency = 1; u.Size = UDim2.fromScale(0.7, 0.14); u.Position = UDim2.fromScale(0.15, 0.6)
					u.Font = Enum.Font.GothamSemibold; u.TextScaled = true; u.TextColor3 = K.c3("c8d0e0"); u.Parent = fr
					u.Text = if (d.Position - site).X < 0 then "DUELS" else "PARTIES"
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
	K.bar(K.at(F0, -20.6, 82.4, -90), 8) -- (27 Nov, Clip v2: 12 long at z 80 it ran through the sofa group and its planter: 8 long, between them and the tall planter)
	K.codePanelSpot(K.at(F0, -24, 60, -90, 0))
	K.vip(CFrame.new(0, 0, SZ1) * CFrame.Angles(0, math.pi, 0), { w = 16, d = 24, h = 14, front = 26, frontH = SH })

	-- ============================================================== THE ZOMBIES ROOM, off the square's south-east corner
	K.zombieRoom(CFrame.new(30, 0, 32) * CFrame.Angles(0, math.pi, 0), { x0 = -20, x1 = 2, d = 18, h = 11, door = 4, guideSide = 1 })

	-- ============================================================== THE GOLF ROOM, off the street's west side
	K.golfRoom(CFrame.new(), { x0 = -82, x1 = -28, z0 = 38, z1 = 132, h = 18, door = { -26, 42, 50 } })

	-- ============================================================== THE REGULARS
	-- Looticus (the shop's man): on the street's sofas, behind the shop counter, behind the bar; he puffs between them
	local LOOT = { { "sit", -19.5, 1.45, 70.4, -90 }, { "sit", -19.5, 1.45, 73.6, -90 }, { "sit", 12.5, 1.45, 72.4, 90 }, { "sit", 12.5, 1.45, 75.6, 90 },
		{ "stand", 16.4, 0, 52, 90 } } -- (26 Nov: before the shop counter, not behind it: no room there; none behind the bar)
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
		{ "the vestibule", F0, -6, 6, -46, -36 }, { "the court, west of the middle", F0, -19, -8, -82, -72 }, { "the court, east of the middle", F0, 8, 19, -82, -72 }, { "the court, north of the middle", F0, -5, 5, -96, -85 },
		{ "the square to the gym", F0, 22, 38, -6, 6 }, { "the square to the armory", F0, -40, -24, -5, 5 },
		{ "the square to the lounge", F0, -3, 3, 26, 88 }, { "the street to the golf room", F0, -32, -20, 43, 49 },
		{ "into the zombies room", F0, 28.5, 31.5, 26, 39 },
	}
end
function HS.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 8, 10 }, { F0, 0, 20, 0 }, { F0, 0, 12, -77 }, { F0, 14, 8, -77 }, { F0, 0, 8, -40 }, { F0, 66, 10, 0 }, { F0, -56, 8, 0 }, { F0, 0, 8, 62 }, { F0, -55, 8, 85 }, { F0, 0, 6, 104 }, { F0, 40, 6, 44 } }
end
HS.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 27), Vector3.new(0, 9.5, -20) },
	{ "gym", Vector3.new(8, 6.2, 6), Vector3.new(72, 3, -2) },
	{ "pads", Vector3.new(0, 6, -50), Vector3.new(-14, 4, -92) },
	{ "lounge", Vector3.new(-2, 6.2, 37), Vector3.new(4, 4, 88) },
	{ "gallery", Vector3.new(-26, 17.6, 28), Vector3.new(6, 8, -12) },
	{ "zombies", Vector3.new(24, 6, 20), Vector3.new(36, 4, 44) },
}
return HS
