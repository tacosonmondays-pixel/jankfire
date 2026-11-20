--!nonstrict
-- THE HOTEL (20 Nov 2026; the owner: "try 3 new ones, on elike the previous hub one thats like a full hotel look", and
-- "by old design I meant lke the chunker structes you know? we just add subtle texture to them now"; "the old hub shold
-- be the minimum going forward"). The whole hub is one hotel interior: you arrive in a double-height LOBBY (a coffered
-- plaster ceiling, two ring chandeliers, a mezzanine on three sides behind a solid balustrade, giant pilasters, the
-- fountain with real water, the grand stair up to the suite, reception, the lifts); the pads are in the BALLROOM through
-- the big doors north (a barrel vault on pilasters, chandeliers, the stage with the ranked boards); the gym and boxing
-- club west, the lounge bar east (the game tables, the arcade, the code panel, the golf room off it), the armory and the
-- training gate down the south-west corridor, the boarded service corridor (zombies) south-east, VIP as the suite at
-- the top of the stair. Vault plan: Hubs/Hotel hub plan.md. Built from HubKit, the hotel kit
-- (tools/roblox/hotel_models.py, K.importKit("hotel", HH.KIT)) and the shared pad (K.pad).
-- World studs from the site: x east, z south, y up; you arrive facing north.
local HH = {}
HH.ID, HH.FOLDER, HH.TITLE, HH.ORDER = "hotel", "Hotel", "THE HOTEL", 4
HH.SITE = CFrame.new(-200, 240, -17400)
HH.KIT = 140589799606267 -- (the hotel kit's Model asset: tools/roblox/hotel_models.py, uploaded 20 Nov)
local PAL = {
	wall = "d6cbb8", wall2 = "cbbfab", floor = "d2c9ba", floor2 = "b9ae9e", runner = "3f5a4a", carpet = "6e5a4c",
	carpet2 = "7a6556", ceil = "e3d9c7", stone = "cdc2b1", stone2 = "b5aa98", accent = "4d6a58", wood = "6e5340",
	dark = "3a3530", warm = "ffe2b8", lamp = "ffe6c8",
}
HH.PAL = PAL
local function mat(name, fallback) local ok, m = pcall(function() return (Enum.Material :: any)[name] end); return if ok and m then m else fallback end

function HH.build(K, parent, name, site, live)
	local MAT = K.MAT
	local PLASTER, MARBLE, CARPET = mat("Plaster", MAT.SmoothPlastic), mat("Marble", MAT.Slate), mat("Carpet", MAT.Fabric)
	local F0 = CFrame.new()
	local f = K.begin(parent, name or HH.FOLDER, site or HH.SITE, HH.ID, { Title = HH.TITLE, Order = HH.ORDER, Accent = PAL.accent }, live)
	local box, cyl = K.box, K.cyl
	local H, MZ = 26, 14 -- (the lobby's ceiling; the mezzanine's floor)
	local FN, FS, FE, FW = CFrame.new(), CFrame.Angles(0, math.pi, 0), CFrame.Angles(0, -math.pi / 2, 0), CFrame.Angles(0, math.pi / 2, 0)
	local function at(x, y, z, yaw) return CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(yaw or 0), 0) end
	local function put(t, cf, o) return K.put(F0, t, cf, o) end
	-- (yaw for a kit piece: its front, +Z, toward: south 0, east 90, north 180, west -90)
	local NAVY = "28324a" -- (judge round 1: no screen shows near-black, even before it has anything on it)
	K.lookZone("hotel", -100, 130, -20, 60, -150, 140) -- (its own light: HubLook.looks.hotel, a step lower than the hub's)

	-- ============================================================== THE LOBBY (x -28..28, z -32..32)
	box(F0, "Shell", "Floor", -22, 22, -1, 0, -26, 26, PAL.floor, MARBLE)
	for _, s in { -1, 1 } do
		box(F0, "Shell", "FloorBorder", s * 22, s * 30, -1, 0, -34, 34, PAL.floor2, MARBLE)
		box(F0, "Shell", "FloorBorder", -22, 22, -1, 0, s * 26, s * 34, PAL.floor2, MARBLE)
	end
	-- the walls (plaster): the ballroom's doors N; the gym's W; the bar's E; S: the armory's mouth and the service door
	K.wall(FN, "Wall", -30, 30, 0, 28.4, -34, -32, PAL.wall, { { -8, 8, 14 } }, PLASTER) -- (up to the ballroom's lid: it closes the vault's S end)
	K.wall(FW, "Wall", -32, 32, 0, H + 1, -30, -28, PAL.wall, { { -4, 4, 10 } }, PLASTER) -- (west: its x runs north)
	K.wall(FE, "Wall", -32, 32, 0, H + 1, -30, -28, PAL.wall, { { 10, 18, 10 } }, PLASTER) -- (east: its x runs south)
	K.wall(FS, "Wall", -30, 30, 0, MZ, -34, -32, PAL.wall, { { 16.5, 27.5, 11 }, { -26, -22, 8.5 } }, PLASTER) -- (south: its x runs west)
	for _, s in { -1, 1 } do box(F0, "Shell", "Wall", s * 20, s * 30, MZ, H + 1, 32, 34, PAL.wall, PLASTER) end -- (VIP's front fills x -20..20)
	box(F0, "Shell", "Roof", -30, 30, H, H + 1, -34, 34, PAL.ceil, PLASTER)
	-- the ceiling (round 2): 4 x 4 deep coffers, 14 x 16, each with a recessed lamp; two chandeliers hung from the beams'
	-- crossings on the axis (over the fountain, over the stair)
	for _, cx in { -21, -7, 7, 21 } do for _, cz in { -24, -8, 8, 24 } do
		put("ht_coffer", at(cx, H, cz))
		local lp = box(F0, "Scenery", "CofferLamp", cx - 2.2, cx + 2.2, H - 0.45, H - 0.38, cz - 2.2, cz + 2.2, "fff4e6", MAT.Neon, { ghost = true, noshadow = true })
		K.light(lp, 34, 0.45, PAL.lamp, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 120 })
	end end
	for _, cz in { -16, 16 } do
		put("ht_chandelier", at(0, H - 2, cz))
		K.light(box(F0, "Scenery", "ChandelierLight", -0.3, 0.3, H - 6.6, H - 6.4, cz - 0.3, cz + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 24, 1.2, PAL.lamp)
	end
	-- the cornice round the top of the walls
	for x = -24, 24, 8 do put("ht_cornice", at(x, H, -32, 0)); put("ht_cornice", at(x, H, 32, 180)) end
	for z = -28, 28, 8 do put("ht_cornice", at(-28, H, z, 90)); put("ht_cornice", at(28, H, z, -90)) end

	-- the mezzanine (W and E the whole length, S between them): a plaster underside, carpet on top, a fascia, a solid
	-- balustrade; piers at its edge; the grand stair up to it in the middle of the S run
	for _, s in { -1, 1 } do
		box(F0, "Shell", "Mezzanine", s * 20, s * 28, MZ - 1, MZ - 0.2, -32, 32, PAL.ceil, PLASTER)
		box(F0, "Shell", "MezzanineFloor", s * 20, s * 28, MZ - 0.2, MZ, -32, 32, PAL.carpet, CARPET)
		box(F0, "Scenery", "Fascia", s * 19.7, s * 20.1, MZ - 1.6, MZ + 0.1, -32, 24.3, PAL.ceil, PLASTER)
		for z = -28, 20, 8 do put("ht_baluster", at(s * 20.75, MZ, z, 90), { solid = true }) end
		put("ht_newel", at(s * 20.75, MZ, 24.75), { solid = true })
		for _, z in { -24, -8, 8, 24.6 } do put("ht_pier", at(s * 20.5, 0, z), { solid = true }) end -- (24.6: the corner, holding the S run too)
	end
	box(F0, "Shell", "Mezzanine", -20, 20, MZ - 1, MZ - 0.2, 24, 32, PAL.ceil, PLASTER)
	box(F0, "Shell", "MezzanineFloor", -20, 20, MZ - 0.2, MZ, 24, 32, PAL.carpet, CARPET)
	box(F0, "Scenery", "Fascia", -20.1, 20.1, MZ - 1.6, MZ + 0.1, 23.9, 24.3, PAL.ceil, PLASTER)
	for _, x in { -16, -8, 8, 16 } do put("ht_baluster", at(x, MZ, 24.75, 0), { solid = true }) end
	for _, s in { -1, 1 } do put("ht_newel", at(s * 4.95, MZ, 24.75), { solid = true }) end
	-- under the mezzanine: a warm flat ceiling with lamps
	for _, s in { -1, 1 } do for _, z in { -20, 0, 20 } do K.panel(F0, s * 24, MZ - 1, z, 3, 6, { bright = 0.6, range = 16, lightHex = PAL.warm }) end end
	for _, x in { -14, 14 } do K.panel(F0, x, MZ - 1, 28.2, 6, 3, { bright = 0.6, range = 16, lightHex = PAL.warm }) end
	-- the stair: 21 marble steps from z 4 (floor) to z 24 (the mezzanine), x -4..4; stepped cheeks with a raked cap
	local SN, SR, RUN = 21, MZ / 21, 20 / 21
	for i = 1, SN do
		local z0 = 4 + (i - 1) * RUN
		box(F0, "Shell", "Stair", -4, 4, 0, i * SR, z0, z0 + RUN, PAL.stone, MARBLE)
		for _, s in { -1, 1 } do box(F0, "Shell", "StairCheek", s * 4, s * 5.2, 0, i * SR + 2.4, z0, z0 + RUN, PAL.ceil, PLASTER) end
	end
	local rake = math.atan2(MZ, 20)
	for _, s in { -1, 1 } do
		local mid = Vector3.new(s * 4.6, (SR + MZ) / 2 + 2.4 + 0.25, 4 + 10)
		K.part("Scenery", "StairCap", F0 * CFrame.new(mid) * CFrame.Angles(-rake, 0, 0), Vector3.new(1.6, 0.5, math.sqrt(20 * 20 + MZ * MZ) + 0.6), PAL.stone, nil, {})
		put("ht_newel", at(s * 4.6, 0, 3.0), { solid = true })
	end
	box(F0, "Scenery", "StairRunner", -2.4, 2.4, 0, 0.04, 2.0, 4.0, PAL.runner, CARPET)

	-- the floor's way: a green runner from the spawn, split round the fountain, to the ballroom's doors and on
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, -32, -29.2, PAL.runner, CARPET)
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, -10.8, -7.8, PAL.runner, CARPET)
	for _, s in { -1, 1 } do
		box(F0, "Scenery", "Runner", s * 10.2, s * 11.7, 0, 0.04, -29.2, -10.8, PAL.runner, CARPET)
		box(F0, "Scenery", "Runner", s * 3, s * 10.2, 0, 0.04, -29.2, -27.7, PAL.runner, CARPET)
		box(F0, "Scenery", "Runner", s * 3, s * 10.2, 0, 0.04, -12.3, -10.8, PAL.runner, CARPET)
	end
	-- the spawn: a round medallion in the marble, eight places facing north, the arrival point
	cyl(F0, "Scenery", "SpawnRing", 0, -0.02, 0.07, -3.2, 9.2, PAL.stone2, MARBLE)
	cyl(F0, "Scenery", "SpawnPlate", 0, 0.07, 0.1, -3.2, 7.6, PAL.runner, CARPET)
	for i = 0, 7 do K.marker(F0, "HubSpawns", "Spawn", -3.6 + (i % 4) * 2.4, 0.1, -4.4 + math.floor(i / 4) * 2.4, 0) end
	K.marker(F0, "HubArrive", "Arrive", 0, 0.1, -6.6, 0)

	-- the fountain, the lobby's centre object (18 across, 10 high): still water on a flat disc (judge round 1: Terrain
	-- water in a shallow basin meshed as a crumpled mound), an invisible kerb round its rim
	put("ht_fountain", at(0, 0, -20))
	cyl(F0, "Scenery", "Water", 0, 1.5, 1.62, -20, 14.0, "2f6a74", MAT.Glass, { tr = 0.15, ghost = true }) -- (brim-full, just under the rim's lip)
	for i = 0, 15 do
		local a = i * math.pi / 8
		K.part("Shell", "FountainKerb", F0 * CFrame.new(math.cos(a) * 8.0, 0.9, -20 + math.sin(a) * 8.0) * CFrame.Angles(0, -a, 0), Vector3.new(2.0, 1.8, 3.6), PAL.stone, nil, { tr = 1, noshadow = true })
	end
	cyl(F0, "Shell", "FountainCore", 0, 0, 5.0, -20, 4.4, PAL.stone, nil, { tr = 1, noshadow = true })

	-- the N wall: the ballroom's doors in a deep surround, giant pilasters either side, the name over the doors
	put("ht_doorL", at(0, 0, -32, 0)) -- (look only: its hull would fill the doorway)
	for _, s in { -1, 1 } do put("ht_pilaster", at(s * 13.6, 0, -32, 0), { solid = true }) end
	-- (judge round 1: the door says what it is for, the name is its own big board over it)
	local Fn = CFrame.new(0, 0, -31.45) * CFrame.Angles(0, math.pi, 0)
	K.wordSign(Fn, "Scenery", "WaySign", 10, 2.2, 0, 17.7, 0, "PLAY", { accent = PAL.accent })
	K.wordSign(Fn, "Scenery", "NameSign", 16, 3.2, 0, 21.3, 0, "JANKFIRE", { accent = PAL.accent })
	-- raised panels in the bare plaster over the galleries (N and S walls' ends)
	for _, sx in { -1, 1 } do
		K.put(FN, "ht_wallpanel", at(sx * 24, MZ + 1, -32, 0))
		K.put(FS, "ht_wallpanel", at(sx * 24, MZ + 1, -32, 0))
	end
	-- the walls' lower half: a panelled wood dado; sconces and room doors upstairs
	-- (in FW a world z is local x -z, in FE it is +z; the walls' faces: N and S at local z -32, W and E at -28)
	local function dadoRun(F, zf, x0, x1, skip)
		for x = x0 + 4, x1 - 4, 8 do
			local clear = true
			for _, k in skip or {} do if x + 4 > k[1] and x - 4 < k[2] then clear = false end end
			if clear then K.put(F, "ht_dado", at(x, 0, zf, 0)) end
		end
	end
	dadoRun(FN, -32, -28, 28, { { -10, 10 }, { -15.5, -11.7 }, { 11.7, 15.5 } })
	dadoRun(FW, -28, -32, 32, { { -6, 6 }, { -22, -10 } })
	dadoRun(FE, -28, -32, 32, { { 8, 22 }, { -24, -8 } })
	dadoRun(FS, -32, -28, 28, { { 14.5, 29.5 }, { -28, -20 }, { -18, -6 }, { 4, 17 } })
	for _, z in { -24, -8, 8, 24 } do -- (the rooms along the galleries; the W wall's N half carries SPECTATE)
		if z > 0 then K.put(FW, "ht_doors", at(-z, MZ, -28, 0)) end
		K.put(FE, "ht_doors", at(z, MZ, -28, 0))
	end
	K.spectateSpot(K.facing(-28, -16, 1, 0, 20.6), 16, 7)
	-- the ways out named on the gallery fascias, big enough to read from the middle (judge round 1)
	local function fascia(x, z, dx, dz, w, title) K.wordSign(K.facing(x, z, dx, dz), "Scenery", "WaySign", w, 2.0, 0, 12.9, 0, title, { accent = PAL.accent }) end
	fascia(-19.7, 0, 1, 0, 8, "GYM")
	fascia(19.7, 15.2, -1, 0, 10, "LOUNGE")
	fascia(19.7, -16, -1, 0, 8, "SHOP")
	fascia(-11, 23.9, 0, -1, 12, "ARMORY  ·  TRAINING")
	fascia(11, 23.9, 0, -1, 10, "ZOMBIES")
	for _, w in { { FW, -1, { -18, 16 } }, { FE, 1, { 4, 26 } } } do
		for _, z in w[3] do
			local x = z * w[2]
			K.put(w[1], "ht_sconce", at(x, 8.5, -28, 0))
			K.light(box(w[1], "Scenery", "SconceLight", x - 0.2, x + 0.2, 8.4, 8.6, -27.4, -27.0, PAL.lamp, nil, { ghost = true, tr = 1 }), 14, 0.55, PAL.lamp)
		end
	end

	-- the corners under the mezzanine: seating on rugs (W by the stair, E between reception and the bar's door), palms,
	-- the loadout and the bundles (W), reception (E)
	local function palm(x, z) put("ht_palm", at(x, 0, z)); cyl(F0, "Shell", "PalmPot", x, 0, 2.3, z, 3.2, PAL.stone, nil, { tr = 1, noshadow = true }) end
	for _, s in { -1, 1 } do
		local zc = if s < 0 then 16 else 0
		box(F0, "Scenery", "Rug", s * 21.5, s * 27.6, 0, 0.04, zc - 5, zc + 5, PAL.carpet2, CARPET)
		put("ht_sofa", at(s * 26.2, 0, zc, if s < 0 then 90 else -90), { solid = true })
		put("ht_table", at(s * 23.2, 0, zc, 90), { solid = true })
		for _, dz in { -3.4, 3.4 } do put("ht_armchair", at(s * 21.2, 0, zc + dz, if s < 0 then -90 else 90), { solid = true }) end
		palm(s * 17.5, -28.4)
	end
	K.holoLoadout(K.at(F0, -25, -29, 90))
	K.bundles(K.at(F0, -24.6, -14.5, 90))
	-- reception: the desk (the shop's counter), Looticus behind it, the SHOP word on the wall over it
	put("ht_desk", at(24.0, 0, -16, -90), { solid = true })
	local pp = box(F0, "Scenery", "ShopPromptPart", 22.4, 23.0, 3.9, 4.5, -16.5, -15.5, PAL.stone, nil, { ghost = true, tr = 1 })
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ShopCounterPrompt"; pr.ActionText = "Shop"; pr.ObjectText = "Reception"; pr.HoldDuration = 0; pr.MaxActivationDistance = 9
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.RequiresLineOfSight = false
	pr:SetAttribute("ShopOpen", "tab:featured")
	pr.Parent = pp
	-- the lifts (HUBS travel) on the S wall, a pair either side of the stair
	put("ht_lift", at(12, 0, 32, 180))
	put("ht_lift", at(-10.4, 0, 32, 180))
	K.travelTerminal(K.at(F0, 12, 27.3, 0))
	K.wordSign(K.facing(12, 30.35, 0, -1), "Scenery", "LiftSign", 4.2, 1.0, 0, 10.8, 0, "HUBS", { accent = PAL.accent })

	-- ============================================================== THE BALLROOM (the pads; x -26..26, z -34..-136)
	-- (round 2: 17-long bays for the bigger pad, a darker vault and carpet, a lit cove where the vault springs, a blade
	-- sign over every pad, runner branches to every pad, the hall ending on a lit set piece: the counts over the trophies)
	local BAY = 17
	local BZ0, BZ1 = -34, -34 - 6 * BAY
	box(F0, "Shell", "Floor", -28, 28, -1, 0, BZ1 - 2, BZ0, "75604f", CARPET) -- (round 2: a step darker than the lobby, never near-black)
	for _, s in { -1, 1 } do box(F0, "Shell", "Wall", s * 26, s * 28, 0, 18.6, BZ1 - 2, BZ0, PAL.wall2, PLASTER) end
	box(F0, "Shell", "Wall", -28, 28, 0, 28, BZ1 - 2, BZ1, PAL.wall2, PLASTER)
	for k = 0, 5 do put("ht_vault", at(0, 0, BZ0 - BAY / 2 - k * BAY), { solid = true }) end
	for k = 0, 6 do put("ht_vaultrib", at(0, 0, BZ0 - k * BAY)) end
	box(F0, "Shell", "VaultLid", -28, 28, 27.4, 28.4, BZ1 - 2, BZ0, PAL.ceil, PLASTER) -- (closes the space over the shell)
	for _, s in { -1, 1 } do
		box(F0, "Scenery", "CoveLedge", s * 24.9, s * 26.05, 17.4, 17.9, BZ1, BZ0, PAL.ceil, PLASTER, { ghost = true })
		local cv = box(F0, "Scenery", "Cove", s * 24.9, s * 25.4, 17.9, 18.0, BZ1 + 0.5, BZ0 - 0.5, PAL.warm, MAT.Neon, { ghost = true, noshadow = true })
		K.light(cv, 22, 0.6, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Top, angle = 150 })
	end
	for k = 1, 5 do
		local z = BZ0 - k * BAY
		for _, s in { -1, 1 } do put("ht_pilasterMid", at(s * 26, 0, z, if s < 0 then 90 else -90), { solid = true }) end
	end
	for _, k in { 1, 3, 5 } do
		local cz = BZ0 - BAY / 2 - k * BAY
		put("ht_chandelier", at(0, 26.6, cz))
		K.light(box(F0, "Scenery", "ChandelierLight", -0.3, 0.3, 21.4, 21.6, cz - 0.3, cz + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 36, 1.4, PAL.lamp)
	end
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, BZ1 + 15.5, BZ0, PAL.runner, CARPET)
	-- the pads: five a side, 1V1 nearest the doors, each in its bay facing the walkway; a branch of the runner to each;
	-- a blade over each, square to the wall, read from up and down the hall
	for k, md in K.MODES do
		local z = BZ0 - BAY / 2 - (k - 1) * BAY
		K.pad(K.facing(-12.4, z, -1, 0), md, "lifts", md.id, { lampY = 16 })
		K.pad(K.facing(12.4, z, 1, 0), md, "east", md.id .. "_e", { lampY = 16 })
		for _, s in { -1, 1 } do
			box(F0, "Scenery", "RunnerBranch", s * 3, s * 12.4, 0, 0.04, z - 0.75, z + 0.75, PAL.runner, CARPET)
			K.padBlade(CFrame.new(s * 23.0, 16.8, z), md, 3.4, 4.0)
			K.light(box(F0, "Scenery", "BayWash", s * 19 - 0.3, s * 19 + 0.3, 18.4, 18.6, z - 0.3, z + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 24, 0.9, PAL.warm,
				{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 70 })
		end
	end
	-- the stage: a two-step dais; on the end wall the trophies (with the ranked boards either side) and over them the
	-- hall's own count board (IN QUEUE, HubConsole writes it) in a pale frame, lit warm
	box(F0, "Shell", "Stage", -24, 24, 0, 1.2, BZ1, BZ1 + 14, PAL.wood, MAT.WoodPlanks)
	box(F0, "Shell", "StageStep", -24, 24, 0, 0.6, BZ1 + 14, BZ1 + 15.2, PAL.wood, MAT.WoodPlanks)
	box(F0, "Scenery", "StageNosing", -24, 24, 1.2, 1.4, BZ1 + 13.6, BZ1 + 14.2, PAL.stone)
	K.trophyWall(K.at(F0, 0, BZ1 + 0.05, 180, 1.2)) -- (with the two ranked boards either side)
	box(F0, "Scenery", "CountFrame", -10.2, 10.2, 14.6, 24.4, BZ1, BZ1 + 0.8, PAL.ceil, PLASTER)
	local cb = box(F0, "Scenery", "CountBoard", -9.2, 9.2, 15.4, 23.6, BZ1 + 0.8, BZ1 + 1.0, NAVY)
	K.screen(cb, { Enum.NormalId.Back })
	K.light(box(F0, "Scenery", "CountWash", -0.3, 0.3, 25.6, 25.8, BZ1 + 4, BZ1 + 4.6, PAL.lamp, nil, { ghost = true, tr = 1 }), 22, 0.8, PAL.warm,
		{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 60 })

	-- ============================================================== THE GYM AND BOXING CLUB (west)
	K.gym(CFrame.Angles(0, math.pi, 0), { x0 = 30, x1 = 92, z0 = -32, z1 = 32, h = 24, rings = { { 46, -14 }, { 76, -14 }, { 46, 14 }, { 76, 14 } },
		locker = { x0 = 52, x1 = 88, z0 = 36, z1 = 60, door = { 66, 74 } } })
	put("ht_doorS", at(-28, 0, 0, 90))
	put("ht_doorS", at(-30, 0, 0, -90)) -- (the gym's side of the same door)

	-- ============================================================== THE LOUNGE BAR (east: x 30..66, z -2..30, low)
	local BX0, BX1, BZa, BZb, BH = 30, 66, -2, 30, 14
	box(F0, "Shell", "Floor", BX0, BX1 + 2, -1, 0, BZa - 2, BZb + 2, PAL.wood, MAT.WoodPlanks)
	box(F0, "Shell", "Roof", BX0, BX1 + 2, BH, BH + 1, BZa - 2, BZb + 2, PAL.ceil, PLASTER)
	box(F0, "Shell", "Wall", BX0, BX1, 0, BH, BZa - 2, BZa, PAL.wall2, PLASTER)
	box(F0, "Shell", "Wall", BX0, BX1, 0, BH, BZb, BZb + 2, PAL.wall2, PLASTER)
	K.wall(CFrame.Angles(0, -math.pi / 2, 0), "Wall", BZa - 2, BZb + 2, 0, BH, -(BX1 + 2), -BX1, PAL.wall2, { { 20, 28, 10 } }, PLASTER) -- (the golf room's door)
	put("ht_doorS", at(30, 0, 14, 90)) -- (the bar's side of the door from the lobby)
	put("ht_doorS", at(28, 0, 14, -90))
	for x = BX0 + 3, BX1 - 3, 6 do box(F0, "Scenery", "Beam", x - 0.6, x + 0.6, BH - 1.4, BH + 0.1, BZa, BZb, PAL.wood, MAT.Wood, { ghost = true }) end
	for _, p in { { 38, 6 }, { 50, 6 }, { 38, 22 }, { 50, 22 }, { 60, 14 } } do K.panel(F0, p[1], BH, p[2], 3, 3, { bright = 0.6, range = 16, lightHex = PAL.warm }) end
	K.bar(K.at(F0, 62, 14, 90), 14) -- (its drinkers on the west side)
	for _, x in { 36, 46, 56 } do
		put("ht_sofa", at(x, 0, 0.2, 0), { solid = true })
		put("ht_table", at(x, 0, 3.4, 0), { solid = true })
	end
	K.tableSpot(K.at(F0, 40, 15, 0), "board"); K.tableSpot(K.at(F0, 52, 23, 0), "arm")
	K.arcadeSpot(K.at(F0, 36, 29.6, 0)); K.arcadeSpot(K.at(F0, 42, 29.6, 0))
	K.codePanelSpot(K.at(F0, 46, BZb, 0)) -- (on the S wall, looking north into the bar)
	palm(64, 0.5); palm(64, 27.5)
	K.golfRoom(F0, { x0 = 70, x1 = 124, z0 = -50, z1 = 44, h = 18, door = { 68, 20, 28 }, doorSide = "w", doorEnd = "s" })

	-- ============================================================== THE ARMORY (south-west) and THE SERVICE CORRIDOR (south-east)
	K.armory(CFrame.new(-22, 0, 0) * CFrame.Angles(0, math.pi, 0), { d0 = 34, d1 = 80, w = 5.5, h = 12, door = "HotelToTraining" })
	-- (the service corridor runs west behind the lobby's S wall: x 4..26, so its open front is all on that wall)
	K.zombieRoom(CFrame.new(24, 0, 32) * CFrame.Angles(0, math.pi, 0), { x0 = -2, x1 = 20, d = 18, h = 11, door = 4, guideSide = 1 })

	-- ============================================================== VIP: the suite at the top of the stair
	K.vip(CFrame.new(0, MZ, 32) * CFrame.Angles(0, math.pi, 0), { w = 12, d = 20, h = 11, front = 20, frontH = H - MZ })

	-- ============================================================== THE REGULARS
	-- Looticus: behind reception, on the W sofa, behind the bar
	local LOOT = { { "stand", 27.0, 0, -16, 90 }, { "sit", -25.6, 1.3, 14.4, 90 }, { "sit", -25.6, 1.3, 17.6, 90 }, { "stand", 64.4, 0, 14, -90 } }
	K.npc(F0, "Looticus", LOOT[1][2], LOOT[1][3], LOOT[1][4], LOOT[1][5])
	for k, w in LOOT do K.npcPoint(F0, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5]) end
	-- Frisk1636: along the ballroom's stage
	local BZ1 = -34 - 6 * 17
	local FR = { { "stop", -14 }, { "via", -6 }, { "stop", 0 }, { "via", 6 }, { "stop", 14 } }
	K.npc(F0, "Frisk1636", FR[1][2], 1.2, BZ1 + 9, 0)
	for k, w in FR do K.npcPoint(F0, "Frisk1636", k, w[1], "stand", w[2], 1.2, BZ1 + 9, 0, { pause = if w[1] == "stop" then { 8, 16 } else nil }) end
	-- Dune: round three sides of the gym's first ring
	local Fg = CFrame.Angles(0, math.pi, 0)
	local DU = { { "stop", 32.5, -14, -90 }, { "via", 32.5, -27.4, 180 }, { "stop", 46, -27.4, 180 }, { "via", 61, -27.4, 180 }, { "stop", 61, -14, 90 } }
	K.npc(Fg, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for k, w in DU do K.npcPoint(Fg, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end
	for _, d in f:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "SpectatePanel" or d.Name == "LiveBoardPanel") then
			d.Color = K.c3(NAVY)
			for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do -- (a lit navy face under whatever the board shows)
				local g = Instance.new("SurfaceGui"); g.Name = "Rest"; g.Face = face; g.LightInfluence = 0; g.Brightness = 1
				g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 4; g.Parent = d
				local fr = Instance.new("Frame"); fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = K.c3(NAVY); fr.BorderSizePixel = 0; fr.Parent = g
			end
		elseif d:IsA("Frame") and d.Parent and d.Parent:IsA("SurfaceGui") and d.Parent.Parent and d.Parent.Parent.Name == "CountBoard" then d.BackgroundColor3 = K.c3(NAVY)
		elseif d:IsA("BasePart") and d.Name == "TableRug" then d.Color = K.c3("7d6654") end -- (the kit's rug is near-black in the lounge's warm light)
	end
	return f
end

-- the fountain's water: Terrain water in the basin (on = false takes it away again). Terrain is not in the hub's folder:
-- a rebuild lays it again, taking the hub away must call HH.water(site, false)
function HH.water(site, on)
	local cf = (site or HH.SITE) * CFrame.new(0, -1.1, -20)
	workspace.Terrain:FillCylinder(cf, 4.2, 6.5, if on then Enum.Material.Water else Enum.Material.Air) -- (y -3.2..1.0: a thin layer meshed as a mound)
end

-- the check: walks (boxes that must stay clear) and leaks (points no ray may get out of), in the site's frame
function HH.walks(K)
	local F0 = CFrame.new()
	return {
		{ "to the ballroom's doors", F0, -6, 6, -38, -28.5 }, { "round the fountain W", F0, -14, -10, -26, -13 }, { "round the fountain E", F0, 10, 14, -26, -13 },
		{ "the ballroom's walk", F0, -10, 10, -118, -36 }, { "into the gym", F0, -34, -24, -3, 3 }, { "into the bar", F0, 24, 34, 11, 17 },
		{ "into the armory", F0, -26, -18, 26.5, 35 }, { "into the service corridor", F0, 22.5, 25.5, 26, 34.5 },
		{ "to the lifts", F0, 9, 15, 20, 26 }, { "the W gallery", F0, -27, -22, -30, 22, 14 }, { "the E gallery", F0, 22, 27, -30, 22, 14 },
	}
end
function HH.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 8, 0 }, { F0, 0, 20, -10 }, { F0, 0, 8, -70 }, { F0, 0, 14, -110 }, { F0, -60, 8, 0 }, { F0, 48, 6, 14 }, { F0, -22, 6, 56 }, { F0, 15, 6, 44 }, { F0, 0, 18, 44 }, { F0, 96, 6, 0 } }
end
local MZv = 14
HH.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 1.5), Vector3.new(0, 9, -30) },
	{ "lobby from the gallery", Vector3.new(-24, MZv + 5.4, 26), Vector3.new(8, 8, -20) },
	{ "ballroom", Vector3.new(0, 6.5, -37), Vector3.new(0, 5, -100) },
	{ "pads close", Vector3.new(4, 6, -55), Vector3.new(-22, 4, -64) },
	{ "the stair and the suite", Vector3.new(0, 6, -10), Vector3.new(0, 14, 30) },
	{ "reception", Vector3.new(4, 6, -10), Vector3.new(26, 4, -18) },
	{ "bar", Vector3.new(32, 6, 14), Vector3.new(62, 4, 10) },
	{ "ceiling", Vector3.new(-6, 5, 6), Vector3.new(0, 26, -20) },
}
return HH
