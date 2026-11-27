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
HH.KIT = 124554368492862 -- (the hotel kit's Model asset: tools/roblox/hotel_models.py, uploaded 20 Nov)
local PAL = {
	wall = "d6cbb8", wall2 = "cbbfab", floor = "b5a996", floor2 = "a39784", runner = "3f5a4a", carpet = "6e5a4c",
	carpet2 = "7a6556", ceil = "e3d9c7", stone = "cdc2b1", stone2 = "b5aa98", accent = "4d6a58", wood = "6e5340",
	dark = "3a3530", wood2 = "5b4434", warm = "ffe2b8", soffit = "bfb29d", lamp = "ffe6c8",
}
HH.PAL = PAL
local function mat(name, fallback) local ok, m = pcall(function() return (Enum.Material :: any)[name] end); return if ok and m then m else fallback end

function HH.build(K, parent, name, site, live, opts)
	local MAT = K.MAT
	local PLASTER, MARBLE, CARPET = mat("Plaster", MAT.SmoothPlastic), mat("Marble", MAT.Slate), mat("Carpet", MAT.Fabric)
	local F0 = CFrame.new()
	-- (26 Nov, the owner: "the hotel spawn area" joined to THE ROTUNDA, larger) opts.lobbyOnly: the lobby alone (its VIP, lifts,
	-- reception, zombies room; the gym, bar and armory doors closed); opts.northOpen = { x0, x1, h }: one wide opening in
	-- the N wall in place of the PLAY portal. (26 Nov, the owner picked B: it goes live) opts.withBar: the lounge bar wing
	-- and the golf room behind it too (their tables, arcade, code panel and golf: the mini-games); opts.northPortal: the
	-- deep framed portal and its PLAY sign round the opening; opts.lookZ0: where the hotel's light stops toward the N
	opts = opts or {}
	local LOBBY, NO, BAR = opts.lobbyOnly, opts.northOpen, opts.withBar
	local GZ0, GZ1 = table.unpack(opts.golfZ or { -50, 44 }) -- (the golf room's z span; THE GRAND ROTUNDA moves it clear of its ring's gym)
	local f = K.begin(parent, name or HH.FOLDER, site or HH.SITE, HH.ID, { Title = HH.TITLE, Order = HH.ORDER, Accent = PAL.accent }, live)
	local box, cyl = K.box, K.cyl
	local H, MZ = 26, 14 -- (the lobby's ceiling; the mezzanine's floor)
	local FN, FS, FE, FW = CFrame.new(), CFrame.Angles(0, math.pi, 0), CFrame.Angles(0, -math.pi / 2, 0), CFrame.Angles(0, math.pi / 2, 0)
	local function at(x, y, z, yaw) return CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(yaw or 0), 0) end
	local function put(t, cf, o) return K.put(F0, t, cf, o) end
	-- (yaw for a kit piece: its front, +Z, toward: south 0, east 90, north 180, west -90)
	local NAVY = "28324a" -- (judge round 1: no screen shows near-black, even before it has anything on it)
	K.lookZone("hotel", -100, 130, -20, 60, opts.lookZ0 or -150, 140) -- (its own light: HubLook.looks.hotel, a step lower than the hub's)

	-- ============================================================== THE LOBBY (x -28..28, z -32..32)
	box(F0, "Shell", "Floor", -22, 22, -1, 0, -26, 26, PAL.floor)
	for _, s in { -1, 1 } do
		box(F0, "Shell", "FloorBorder", s * 22, s * 30, -1, 0, -34, 34, PAL.floor2)
		box(F0, "Shell", "FloorBorder", -22, 22, -1, 0, s * 26, s * 34, PAL.floor2)
	end
	local JOINT = "9a8e7d"
	for x = -16, 16, 8 do box(F0, "Scenery", "FloorJoint", x - 0.15, x + 0.15, 0, 0.02, -26, 26, JOINT) end
	for z = -24, 24, 8 do box(F0, "Scenery", "FloorJoint", -22, 22, 0, 0.02, z - 0.15, z + 0.15, JOINT) end
	-- the walls (plaster): the ballroom's doors N; the gym's W; the bar's E; S: the armory's mouth and the service door
	K.wall(FN, "Wall", -30, 30, 0, 28.4, -34, -32, PAL.wall, { NO or { -8, 8, 14 } }, PLASTER) -- (up to the ballroom's lid: it closes the vault's S end)
	K.wall(FW, "Wall", -32, 32, 0, H + 1, -30, -28, PAL.wall, if LOBBY then {} else { { -4, 4, 10 } }, PLASTER) -- (west: its x runs north)
	K.wall(FE, "Wall", -32, 32, 0, H + 1, -30, -28, PAL.wall, if LOBBY and not BAR then {} else { { 10, 18, 10 } }, PLASTER) -- (east: its x runs south)
	K.wall(FS, "Wall", -30, 30, 0, MZ, -34, -32, PAL.wall, if LOBBY then { { -26, -22, 8.5 } } else { { 16.5, 27.5, 11 }, { -26, -22, 8.5 } }, PLASTER) -- (south: its x runs west)
	for _, s in { -1, 1 } do box(F0, "Shell", "Wall", s * 20, s * 30, MZ, H + 1, 32, 34, PAL.wall, PLASTER) end -- (VIP's front fills x -20..20)
	box(F0, "Shell", "Roof", -30, 30, H, H + 1, -34, 34, PAL.soffit, PLASTER)
	-- the ceiling (round 2): 4 x 4 deep coffers, 14 x 16, each with a recessed lamp; two ring lights at the beams'
	-- crossings on the axis (round 3: flush, 1.8 deep, above the galleries' sight lines to the signs)
	-- (round 4, judge round 3: fewer, bigger coffers) 2 x 2 cells at twice the kit's size, a ring light in each
	for _, cx in { -14, 14 } do for _, cz in { -16, 16 } do
		local cf = put("ht_coffer", at(cx, H, cz))
		if cf then cf:ScaleTo(2) end
		put("ht_chandelier", at(cx, H - 0.7, cz))
		K.light(box(F0, "Scenery", "ChandelierLight", cx - 0.3, cx + 0.3, H - 4.6, H - 4.4, cz - 0.3, cz + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 32, 1.0, PAL.lamp)
	end end
	-- the cornice round the top of the walls
	for x = -24, 24, 8 do put("ht_cornice", at(x, H, -32, 0)); put("ht_cornice", at(x, H, 32, 180)) end
	for z = -28, 28, 8 do put("ht_cornice", at(-28, H, z, 90)); put("ht_cornice", at(28, H, z, -90)) end

	-- the mezzanine (W and E the whole length, S between them): a plaster underside, carpet on top, a fascia, a solid
	-- balustrade; piers at its edge; the grand stair up to it in the middle of the S run
	for _, s in { -1, 1 } do
		box(F0, "Shell", "Mezzanine", s * 20, s * 28, MZ - 1, MZ - 0.2, -32, 32, PAL.soffit, PLASTER)
		box(F0, "Shell", "MezzanineFloor", s * 20, s * 28, MZ - 0.2, MZ, -32, 32, PAL.carpet, CARPET)
		box(F0, "Scenery", "Fascia", s * 19.7, s * 20.1, MZ - 1.6, MZ + 0.1, -32, 24.3, PAL.ceil, PLASTER)
		for z = -28, 20, 8 do put("ht_baluster", at(s * 20.75, MZ, z, 90), { solid = true }) end
		put("ht_newel", at(s * 20.75, MZ, 24.75), { solid = true })
		for _, z in { -24, -8, 8, 24.6 } do put("ht_pier", at(s * 20.5, 0, z), { solid = true }) end -- (24.6: the corner, holding the S run too)
	end
	box(F0, "Shell", "Mezzanine", -20, 20, MZ - 1, MZ - 0.2, 24, 32, PAL.soffit, PLASTER)
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
	for _, sx in { -1, 1 } do K.light(box(F0, "Scenery", "StairFootLight", sx * 6.5 - 0.2, sx * 6.5 + 0.2, 4.4, 4.6, 4.8, 5.2, PAL.lamp, nil, { ghost = true, tr = 1 }), 14, 0.8, PAL.warm) end
	K.light(box(F0, "Scenery", "StairFrontLight", -0.2, 0.2, 3.0, 3.2, 1.2, 1.6, PAL.lamp, nil, { ghost = true, tr = 1 }), 11, 0.9, PAL.warm) -- (the bottom risers face the spawn: lit from in front)
	for _, p in { { 10, 8 }, { 15, 18 }, { 22, 26 } } do -- (round 4: the stair lit, not a black slope)
		K.light(box(F0, "Scenery", "StairLight", -0.3, 0.3, p[1] - 0.1, p[1] + 0.1, p[2] - 0.3, p[2] + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 18, 0.9, PAL.warm)
	end

	-- the floor's way: a green runner from the spawn, split round the fountain, to the ballroom's doors and on
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, -32, -29.2, PAL.runner, CARPET)
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, -10.8, -7.8, PAL.runner, CARPET)
	for _, s in { -1, 1 } do
		box(F0, "Scenery", "Runner", s * 9.4, s * 12.4, 0, 0.04, -29.2, -10.8, PAL.runner, CARPET)
		box(F0, "Scenery", "Runner", s * 3, s * 9.4, 0, 0.04, -29.2, -26.2, PAL.runner, CARPET)
		box(F0, "Scenery", "Runner", s * 3, s * 9.4, 0, 0.04, -13.8, -10.8, PAL.runner, CARPET)
	end
	-- (round 3) the ways from the spawn, inlaid in the same green (judge round 2): across the spawn to the gym's door, to
	-- the lounge's door, to the armory's mouth (TRAINING), and from the fountain's ring to reception
	local function way(x0, x1, z0, z1) box(F0, "Scenery", "RunnerBranch", x0, x1, 0, 0.04, z0, z1, PAL.runner, CARPET) end
	way(if LOBBY then 3.9 else -27.5, 14.75, -3.95, -2.45)
	if not LOBBY or BAR then way(13.25, 14.75, -2.45, 14.75); way(14.75, 27.5, 13.25, 14.75) end
	if not LOBBY then
		way(-14.75, -13.25, -2.45, 30); way(-24, -14.75, 28.5, 30)
	end
	way(11.7, 21.5, -16.75, -15.25)
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
	if not NO then put("ht_doorL", at(0, 0, -32, 0)) end -- (look only: its hull would fill the doorway)
	-- (round 5, judge round 4: the way to PLAY a deep framed portal) a sleeve 3.4 deep proud of the surround
	local PORTAL = not NO or opts.northPortal
	local PX, PH = if NO then NO[2] else 7.9, if NO then NO[3] else 14 -- (the sleeve's inner edge, the head's underside)
	if PORTAL then
		for _, sx in { -1, 1 } do box(F0, "Shell", "Portal", sx * PX, sx * (PX + 2), 0, PH, -32, -28.6, PAL.wall, PLASTER) end
		box(F0, "Shell", "Portal", -PX - 2, PX + 2, PH, PH + 2.4, -32, -28.6, PAL.wall, PLASTER)
	end
	for _, s in { -1, 1 } do if not NO or NO[2] < 12 then put("ht_pilaster", at(s * 13.6, 0, -32, 0), { solid = true }) end end
	-- (judge round 1: the door says what it is for, the name is its own big board over it)
	local Fn = CFrame.new(0, 0, -31.45) * CFrame.Angles(0, math.pi, 0)
	if PORTAL then K.wordSign(Fn, "Scenery", "WaySign", 12, 2.2, 0, PH + 1.2, -2.9, "PLAY", { accent = PAL.accent, bg = NAVY }) end
	K.wordSign(Fn, "Scenery", "NameSign", 16, 3.2, 0, 19.9, 0, "JANKFIRE", { accent = PAL.accent, bg = NAVY })
	-- raised panels in the bare plaster over the galleries (N and S walls' ends)
	for _, sx in { -1, 1 } do
		K.put(FN, "ht_wallpanel", at(sx * 24, MZ + 1, -32, 0))
		K.put(FS, "ht_wallpanel", at(sx * 24, MZ + 1, -32, 0))
		for _, x in { sx * 20.9, sx * 27.1 } do -- (round 3: the galleries end on a lit wall, not a dark one)
			K.put(FN, "ht_sconce", at(x, MZ + 5.5, -32, 0))
			K.light(box(FN, "Scenery", "SconceLight", x - 0.2, x + 0.2, MZ + 5.4, MZ + 5.6, -31.4, -31.0, PAL.lamp, nil, { ghost = true, tr = 1 }), 12, 0.6, PAL.lamp)
		end
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
	dadoRun(FN, -32, -28, 28, if NO then { { NO[1] - (if PORTAL then 2.2 else 1), NO[2] + (if PORTAL then 2.2 else 1) } } else { { -10, 10 }, { -15.5, -11.7 }, { 11.7, 15.5 } })
	dadoRun(FW, -28, -32, 32, { { -6, 6 }, { -22, -10 } })
	dadoRun(FE, -28, -32, 32, { { 8, 22 }, { -24, -8 } })
	dadoRun(FS, -32, -28, 28, { { 14.5, 29.5 }, { -28, -20 }, { -18, -6 }, { 4, 17 } })
	for _, z in { -24, -8, 8, 24 } do -- (the rooms along the galleries)
		K.put(FW, "ht_doors", at(-z, MZ, -28, 0))
		K.put(FE, "ht_doors", at(z, MZ, -28, 0))
	end
	for _, z in { -16, 0, 16 } do -- (round 5: a sconce over each bench)
		for _, w in { { FW, -z }, { FE, z } } do
			K.put(w[1], "ht_sconce", at(w[2], MZ + 6, -28, 0))
			K.light(box(w[1], "Scenery", "SconceLight", w[2] - 0.2, w[2] + 0.2, MZ + 5.9, MZ + 6.1, -27.4, -27.0, PAL.lamp, nil, { ghost = true, tr = 1 }), 12, 0.6, PAL.lamp)
		end
	end
	for _, z in { -16, 0, 16 } do -- (round 4: benches between the gallery doors)
		put("ht_sofa", at(-26.2, MZ, z, 90), { solid = true }); put("ht_sofa", at(26.2, MZ, z, -90), { solid = true })
	end
	-- the ways out named on the gallery fascias, big enough to read from the middle (judge round 1)
	local function fascia(x, z, dx, dz, w, title) K.wordSign(K.facing(x, z, dx, dz), "Scenery", "WaySign", w, 2.0, 0, 12.2, 0, title, { accent = PAL.accent, bg = NAVY }) end
	if not LOBBY then fascia(-19.7, 0, 1, 0, 8, "GYM") end
	if not LOBBY or BAR then fascia(19.7, 15.2, -1, 0, 10, "LOUNGE") end
	fascia(19.7, -16, -1, 0, 8, "SHOP")
	if not LOBBY then fascia(-13, 23.9, 0, -1, 12, "ARMORY  ·  TRAINING") end
	-- (round 5: ZOMBIES over its own door, not stacked over the lifts; TRAINING again over the armory's mouth)
	K.wordSign(K.facing(24, 31.95, 0, -1), "Scenery", "WaySign", 7, 1.6, 0, 10.4, 0, "ZOMBIES", { accent = PAL.accent, bg = NAVY })
	if not LOBBY then K.wordSign(K.facing(-22, 31.95, 0, -1), "Scenery", "WaySign", 9, 1.4, 0, 12.0, 0, "TRAINING", { accent = PAL.accent, bg = NAVY }) end
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
		put("ht_sofa", at(s * 25.8, 0, zc, if s < 0 then 90 else -90), { solid = true }) -- (26 Nov: 0.4 off the dado)
		put("ht_table", at(s * 23.2, 0, zc, 90), { solid = true })
		for _, dz in { -3.4, 3.4 } do put("ht_armchair", at(s * 21.2, 0, zc + dz, if s < 0 then -90 else 90), { solid = true }) end
		palm(s * 17.5, -28.4)
	end
	K.holoLoadout(K.at(F0, -25, -29, 90))
	K.bundles(K.at(F0, -23.6, -14.5, 90)) -- (26 Nov: a stud off the dado)
	-- reception: the desk (the shop's counter), Looticus behind it, the SHOP word on the wall over it
	put("ht_desk", at(24.0, 0, -16, -90), { solid = true })
	local pp = box(F0, "Scenery", "ShopPromptPart", 22.4, 23.0, 3.9, 4.5, -16.5, -15.5, PAL.stone, nil, { ghost = true, tr = 1 })
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ShopCounterPrompt"; pr.ActionText = "Shop"; pr.ObjectText = "Reception"; pr.HoldDuration = 0; pr.MaxActivationDistance = 9
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.RequiresLineOfSight = false
	pr:SetAttribute("ShopOpen", "tab:featured")
	pr.Parent = pp
	-- (round 3) the display wall behind reception (judge round 2: "nothing says what is sold"): pale panelling, four lit
	-- cases above head height, a gun in each, the cases' backs glowing warm
	box(F0, "Scenery", "ShopWall", 27.4, 28, 0, 12.8, -25.4, -6.6, PAL.ceil, PLASTER)
	for i, wid in { "ar", "sniper", "shotgun", "smg" } do
		local zc = -22 + (i - 1) * 4.4
		box(F0, "Scenery", "CaseBack", 27.2, 27.4, 6.0, 11.0, zc - 1.8, zc + 1.8, "e8d6b6", MAT.Neon, { ghost = true, noshadow = true, tr = 0.72 })
		box(F0, "Scenery", "CaseSill", 26.4, 27.4, 5.4, 6.0, zc - 2.2, zc + 2.2, PAL.wood, nil, { ghost = true })
		box(F0, "Scenery", "CaseHead", 26.4, 27.4, 11.0, 11.6, zc - 2.2, zc + 2.2, PAL.wood, nil, { ghost = true })
		for _, sz in { -1, 1 } do box(F0, "Scenery", "CaseSide", 26.4, 27.4, 5.4, 11.6, zc + sz * 1.8, zc + sz * 2.2, PAL.wood, nil, { ghost = true }) end
		K.gun(F0, "JankfireWeapons", "w_" .. wid, 3.6, 26.9, 8.5, zc, -90, "Show_w_" .. wid)
		K.light(box(F0, "Scenery", "CaseLight", 26.7, 27.1, 10.6, 10.8, zc - 0.2, zc + 0.2, PAL.lamp, nil, { ghost = true, tr = 1 }), 7, 0.8, PAL.lamp)
	end
	-- (round 4) a display plinth in front of reception: the newest premium weapon turning on it, lit from above
	cyl(F0, "Shell", "ShowPlinth", 16.5, 0, 3.2, -21.5, 3.6, PAL.stone)
	cyl(F0, "Scenery", "ShowPlinthLip", 16.5, 3.0, 3.3, -21.5, 3.9, PAL.wood)
	-- (polish: judges, the gun read as floating) two wood cradles on the plinth, the gun seated on them, still
	for _, dx in { -1.1, 1.1 } do box(F0, "Scenery", "Cradle", 16.5 + dx - 0.3, 16.5 + dx + 0.3, 3.3, 3.9, -22.1, -20.9, PAL.wood) end
	local sg = K.gun(F0, "JankfireWeapons", "w_minigun", 4.6, 16.5, 4.6, -21.5, 0, "Case_w_minigun") or K.gun(F0, "JankfireWeapons", "w_katana", 4.4, 16.5, 4.6, -21.5, 0, "Case_w_katana")
	if sg then
		local cf, size = sg:GetBoundingBox()
		sg:PivotTo(sg:GetPivot() + Vector3.new(0, (site or HH.SITE).Position.Y + 3.9 - (cf.Position.Y - size.Y / 2), 0)) -- (its underside on the cradles)
	end
	K.light(box(F0, "Scenery", "ShowLight", 16.2, 16.8, 12.4, 12.6, -21.8, -21.2, PAL.lamp, nil, { ghost = true, tr = 1 }), 12, 1.2, PAL.lamp,
		{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 40 })
	-- the lifts (HUBS travel) on the S wall, a pair either side of the stair
	put("ht_lift", at(12, 0, 32, 180))
	put("ht_lift", at(-10.4, 0, 32, 180))
	K.travelTerminal(K.at(F0, 12, 27.3, 0))
	K.wordSign(K.facing(12, 29.6, 0, -1), "Scenery", "LiftSign", 7.5, 1.6, 0, 10.9, 0, "HUBS", { accent = PAL.accent, bg = NAVY })

	if not LOBBY then
	-- ============================================================== THE BALLROOM (the pads; x -26..26, z -34..-153)
	-- (round 2: 17-long bays for the bigger pad, a cove where the vault springs, runner branches to every pad)
	-- (round 3, judges round 2/3: a pale stone floor; each pad in front of its own lit recess (the wall pushed back 2.5
	-- between the pilasters); thick ribs; the chandeliers a step down so the pads are the brightest things; each pad's
	-- blade on its own gantry; ONE thing on the end wall: the big cup in a lit niche. And (main, the copy risk: a straight
	-- mirrored hall reads as the reference's pad runway) a CROSSING in the middle: the third bay opens into two side
	-- alcoves (the spectate board W, the hall's counts E) under the skylight, the walk splitting round a round settee;
	-- two pads a side before it, three after)
	local BAY = 17
	local BZ0 = -34
	local BZ1 = BZ0 - 7 * BAY
	local PADBAY = { 0, 1, 3, 4, 5 } -- (the bays the pads stand in, in K.MODES order; bay 2 the crossing, bay 6 the stage)
	local XB = 2 -- (the crossing's bay)
	local function bz(k) return BZ0 - k * BAY end -- (bay k runs bz(k) .. bz(k + 1))
	box(F0, "Shell", "Floor", -40, 40, -1, 0, BZ1 - 2, BZ0, "a3947f")
	for _, x in { -36, -28, -20, -12, 12, 20, 28, 36 } do box(F0, "Scenery", "FloorJoint", x - 0.15, x + 0.15, 0, 0.02, BZ1, BZ0, "8c806e") end
	for k = 1, 13 do local z = BZ0 - k * BAY / 2; box(F0, "Scenery", "FloorJoint", -40, 40, 0, 0.02, z - 0.15, z + 0.15, "8c806e") end
	for _, s in { -1, 1 } do
		box(F0, "Shell", "Wall", s * 28.5, s * 30.5, 0, 18.6, bz(XB) - 1.8, BZ0, PAL.wall2, PLASTER) -- (the recesses' backs)
		box(F0, "Shell", "Wall", s * 28.5, s * 30.5, 0, 18.6, BZ1 - 2, bz(XB + 1) + 1.8, PAL.wall2, PLASTER)
		box(F0, "Shell", "Wall", s * 26, s * 28.5, 17.4, 18.6, BZ1 - 2, BZ0, PAL.wall2, PLASTER) -- (their head, the crossing's lintel)
		box(F0, "Shell", "Wall", s * 26, s * 28.5, 0, 17.4, BZ0 - 1.8, BZ0, PAL.wall2, PLASTER)
		box(F0, "Shell", "Wall", s * 26, s * 28.5, 0, 17.4, BZ1 - 2, bz(6) + 1.8, PAL.wall2, PLASTER) -- (the stage's bay: solid)
		for k = 1, 5 do box(F0, "Shell", "Wall", s * 26, s * 28.5, 0, 17.4, bz(k) - 1.8, bz(k) + 1.8, PAL.wall2, PLASTER) end
		for _, k in PADBAY do -- (each pad's recess lit from its head, warm, onto its back)
			local rl = box(F0, "Scenery", "RecessLight", s * 26.3, s * 28.2, 17.25, 17.4, bz(k + 1) + 2.2, bz(k) - 2.2, PAL.warm, MAT.Neon, { ghost = true, noshadow = true, tr = 0.5 })
			K.light(rl, 18, 0.9, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 150 })
		end
		-- the crossing's alcove: 10 deep, as tall as the recesses, a flat lit ceiling
		local za, zb = bz(XB) - 1.8, bz(XB + 1) + 1.8
		box(F0, "Shell", "Wall", s * 38, s * 40, 0, 18.6, zb - 2, za + 2, PAL.wall2, PLASTER)
		for _, zz in { za, zb } do box(F0, "Shell", "Wall", s * 28.5, s * 38, 0, 18.6, if zz == za then za else zz - 2, if zz == za then za + 2 else zz, PAL.wall2, PLASTER) end
		box(F0, "Shell", "AlcoveLid", s * 26, s * 40, 17.4, 18.6, zb - 2, za + 2, PAL.soffit, PLASTER)
		for _, zz in { za - 3.4, zb + 3.4 } do K.panel(F0, s * 33, 17.4, zz, 3, 4, { bright = 1.1, range = 20, lightHex = PAL.warm }) end
	end
	-- W: the spectate board (play-party draws the games on it); E: the hall's counts (IN QUEUE, HubConsole writes it)
	local zx = (bz(XB) + bz(XB + 1)) / 2
	K.spectateSpot(K.facing(-37.95, zx, 1, 0, 9.0), 11.6, 7.4)
	for i, t in { { -34.6, -32.0, 1.0 }, { -32.0, -29.4, 2.0 } } do -- (tiered seats, rising toward the hall)
		box(F0, "Shell", "Tier", t[1], t[2], 0, t[3], zx - 4, zx + 4, PAL.wood2, MAT.WoodPlanks)
		box(F0, "Scenery", "TierCushion", t[1] + 0.2, t[2] - 0.2, t[3], t[3] + 0.35, zx - 3.8, zx + 3.8, "6f8a76", CARPET)
	end
	K.light(box(F0, "Scenery", "BoardWash", -34.3, -33.7, 16.6, 16.8, zx - 0.3, zx + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 16, 0.7, PAL.lamp,
		{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 80 })
	K.trophyCase(K.facing(35.2, zx, -1, 0), 8)
	K.light(box(F0, "Scenery", "CaseWash", 33.7, 34.3, 16.6, 16.8, zx - 0.3, zx + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 16, 0.7, PAL.lamp,
		{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 80 })
	box(F0, "Shell", "Wall", -30.5, 30.5, 0, 28, BZ1 - 2, BZ1, PAL.wall2, PLASTER)
	for k = 0, 6 do put("ht_vault", at(0, 0, BZ0 - BAY / 2 - k * BAY), { solid = true }) end
	for k = 0, 7 do put("ht_vaultrib", at(0, 0, bz(k))) end
	box(F0, "Shell", "VaultLid", -30.5, 30.5, 27.4, 28.4, BZ1 - 2, BZ0, PAL.ceil, PLASTER) -- (closes the space over the shell)
	for _, s in { -1, 1 } do
		box(F0, "Scenery", "CoveLedge", s * 24.9, s * 26.05, 17.4, 17.9, BZ1, BZ0, PAL.ceil, PLASTER, { ghost = true })
		local cv = box(F0, "Scenery", "Cove", s * 24.9, s * 25.4, 17.9, 18.0, BZ1 + 0.5, BZ0 - 0.5, PAL.warm, MAT.Neon, { ghost = true, noshadow = true, tr = 0.5 })
		K.light(cv, 22, 0.5, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Top, angle = 150 })
	end
	for k = 1, 6 do
		for _, s in { -1, 1 } do put("ht_pilasterMid", at(s * 26, 0, bz(k), if s < 0 then 90 else -90), { solid = true }) end
	end
	-- the crossing's skylight: a lit panel in the vault's crown, in a deep frame
	local SZ0, SZ1 = bz(XB) - 2.5, bz(XB + 1) + 2.5
	local sk = box(F0, "Scenery", "Skylight", -4, 4, 25.75, 25.85, SZ1, SZ0, "fff6e8", MAT.Neon, { ghost = true, noshadow = true })
	K.light(sk, 30, 0.8, "fff6e8", { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 120 })
	for _, sx in { -1, 1 } do box(F0, "Scenery", "SkylightFrame", sx * 4, sx * 5.2, 24.9, 25.9, SZ1 - 1.2, SZ0 + 1.2, PAL.ceil, PLASTER) end
	for _, zz in { SZ0, SZ1 } do box(F0, "Scenery", "SkylightFrame", -5.2, 5.2, 25.1, 25.9, zz - 0.6, zz + 0.6, PAL.ceil, PLASTER) end
	for _, k in { 1, 4 } do
		local cz = BZ0 - BAY / 2 - k * BAY
		put("ht_chandelier", at(0, 25.9, cz))
		K.light(box(F0, "Scenery", "ChandelierLight", -0.3, 0.3, 22.4, 22.6, cz - 0.3, cz + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 34, 1.05, PAL.lamp)
	end
	-- the crossing's middle: a round settee (a hotel's borne) on a low stone dais; the walk splits round it
	cyl(F0, "Shell", "CrossDais", 0, 0, 0.5, zx, 13, PAL.stone, MARBLE)
	cyl(F0, "Scenery", "CrossDaisNosing", 0, 0.45, 0.6, zx, 13.4, PAL.stone2)
	cyl(F0, "Shell", "BorneSeat", 0, 0.5, 2.1, zx, 8.4, "b8ab97", CARPET)
	cyl(F0, "Scenery", "BorneBase", 0, 0.5, 0.9, zx, 8.8, PAL.wood)
	cyl(F0, "Shell", "BorneBack", 0, 2.1, 3.8, zx, 3.2, "b8ab97", CARPET)
	cyl(F0, "Scenery", "BorneCap", 0, 3.8, 4.2, zx, 3.6, PAL.wood)
	-- the floor: a stone walk down the middle (split round the dais), a pale threshold from it into each pad
	local WALK, EDGE = "9c907d", "d2c7b4" -- (round 5: the walk a step darker than the field, its edges pale)
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, bz(XB) - 0.6, BZ0, WALK)
	box(F0, "Scenery", "Runner", -3, 3, 0, 0.04, BZ1 + 15.5, bz(XB + 1) + 0.6, WALK)
	for _, sx in { -1, 1 } do
		box(F0, "Scenery", "RunnerEdge", sx * 3, sx * 3.45, 0, 0.05, bz(XB) - 0.6, BZ0, EDGE)
		box(F0, "Scenery", "RunnerEdge", sx * 3, sx * 3.45, 0, 0.05, BZ1 + 15.5, bz(XB + 1) + 0.6, EDGE)
		box(F0, "Scenery", "Runner", sx * 7.2, sx * 10.2, 0, 0.04, bz(XB + 1) + 0.6, bz(XB) - 0.6, WALK)
	end
	for _, zz in { bz(XB) - 0.6, bz(XB + 1) + 0.6 } do box(F0, "Scenery", "Runner", -10.2, 10.2, 0, 0.04, zz - 1.5, zz + 1.5, WALK) end
	-- one sign at the hall's entrance says how the pads work (round 4 of the pads: not on every board)
	-- (26 Nov, the owner: no one-line signs. the STEP ON A SIDE sign and its rods over the fountain are gone)
	-- the pads: five a side in K.MODES order (1V1 nearest the doors), each in its bay facing the walk (its blade on its
	-- own gantry); a pale threshold into each
	for i, md in K.MODES do
		local z = BZ0 - BAY / 2 - PADBAY[i] * BAY
		-- (the classic pad, the owner's pick: flush in front of its recess, its back edge at 24.2; its board and its plaque on
		-- the recess's back wall, the plaque under the cove)
		local dp = (K.CLASSIC_SIZE[md.id] or { 13.6, 11 })[2]
		local fx = 24.2 - dp
		-- (the owner, 21 Nov: "changed my mind no angeld") the board and its plaque FLAT on the recess's back wall, as on the
		-- Rotunda: the board's middle at 9.8, the plaque over it at 14.6
		for _, s in { -1, 1 } do
			K.pad(K.facing(s * fx, z, s, 0), md, if s < 0 then "lifts" else "east", if s < 0 then md.id else md.id .. "_e",
				{ lampY = 16, boardAt = K.facing(s * 28.45, z, -s, 0, 9.8), headerAt = K.facing(s * 28.45, z, -s, 0, 14.6), accent = PAL.accent })
		end
		for _, s in { -1, 1 } do
			box(F0, "Scenery", "Threshold", s * 3.45, s * fx, 0, 0.04, z - 1.5, z + 1.5, WALK)
			for _, dz in { -1.5, 1.5 } do box(F0, "Scenery", "ThresholdEdge", s * 3.45, s * fx, 0, 0.05, z + dz - 0.22, z + dz + 0.22, EDGE) end
			K.light(box(F0, "Scenery", "BayWash", s * 19 - 0.3, s * 19 + 0.3, 18.4, 18.6, z - 0.3, z + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 24, 0.6, PAL.warm,
				{ kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 70 })
		end
	end
	-- the stage: a two-step dais; the end wall ONE thing: the big cup on the dais in a tall niche lit from behind, two
	-- spots on it from the vault; the ranked boards on the stage bay's side walls, facing in
	box(F0, "Shell", "Stage", -24, 24, 0, 1.2, BZ1, BZ1 + 14, "8a6a50", MAT.WoodPlanks)
	box(F0, "Shell", "StageStep", -24, 24, 0, 0.6, BZ1 + 14, BZ1 + 15.2, "8a6a50", MAT.WoodPlanks)
	box(F0, "Scenery", "StageNosing", -24, 24, 1.2, 1.4, BZ1 + 13.6, BZ1 + 14.2, PAL.stone)
	-- (round 4, judge round 3: a real end piece) a tall chunky niche, its back a step darker, lit warm from its sill and its
	-- head; the cup 1.3x on a round plinth with a lit lip; a warm spot from above
	box(F0, "Scenery", "NicheBack", -12, 12, 1.2, 21, BZ1, BZ1 + 0.2, "a3947f", PLASTER)
	for _, sx in { -1, 1 } do box(F0, "Scenery", "NicheJamb", sx * 12, sx * 14.6, 0, 23.4, BZ1, BZ1 + 2.6, PAL.wall, PLASTER) end
	box(F0, "Scenery", "NicheHead", -14.6, 14.6, 21, 23.4, BZ1, BZ1 + 2.6, PAL.wall, PLASTER)
	local ns = box(F0, "Scenery", "NicheSill", -11.8, 11.8, 1.2, 1.4, BZ1 + 0.2, BZ1 + 0.6, PAL.warm, MAT.Neon, { ghost = true, noshadow = true, tr = 0.3 })
	K.light(ns, 22, 0.8, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Top, angle = 120 })
	local nh = box(F0, "Scenery", "NicheCove", -11.8, 11.8, 20.8, 21, BZ1 + 0.2, BZ1 + 2.4, PAL.warm, MAT.Neon, { ghost = true, noshadow = true, tr = 0.3 })
	K.light(nh, 22, 0.6, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 120 })
	cyl(F0, "Shell", "TrophyPlinth", 0, 1.2, 3.6, BZ1 + 8, 10, PAL.stone, MARBLE)
	cyl(F0, "Scenery", "TrophyPlinthLip", 0, 3.1, 3.35, BZ1 + 8, 10.3, PAL.wood)
	local cup = put("ht_trophy", at(0, 3.6, BZ1 + 8), { solid = true })
	if cup then
		cup:ScaleTo(1.3)
		for _, d in cup:GetDescendants() do if d:IsA("BasePart") then d.Color = if d.Color.R > 0.75 then K.c3("a89466") else K.c3("8f7a52") end end
	end
	local top = K.part("Scenery", "TrophySpot", F0 * CFrame.new(0, 25.4, BZ1 + 9), Vector3.new(0.4, 0.4, 0.4), PAL.lamp, nil, { ghost = true, tr = 1 })
	local tl = Instance.new("SpotLight"); tl.Face = Enum.NormalId.Bottom; tl.Range = 30; tl.Brightness = 1.0; tl.Angle = 50; tl.Color = K.c3(PAL.lamp); tl.Shadows = true; tl.Parent = top
	for _, sx in { -1, 1 } do K.light(box(F0, "Scenery", "StageLight", sx * 18 - 0.3, sx * 18 + 0.3, 11.8, 12, BZ1 + 8 - 0.3, BZ1 + 8 + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 26, 0.9, PAL.warm) end
	for _, sx in { -1, 1 } do
		local sp = K.part("Scenery", "TrophySpot", F0 * CFrame.lookAt(Vector3.new(sx * 7, 22, BZ1 + 22), Vector3.new(0, 13, BZ1 + 8)), Vector3.new(0.4, 0.4, 0.4), PAL.lamp, nil, { ghost = true, tr = 1 })
		local l = Instance.new("SpotLight"); l.Face = Enum.NormalId.Front; l.Range = 34; l.Brightness = 0.7; l.Angle = 36; l.Color = K.c3(PAL.lamp); l.Shadows = false; l.Parent = sp
	end
	K.boardSpot(K.facing(-20.3, BZ1 + 0.05, 0, 1, 9.0), "duels", 9.6, 7.4)
	K.boardSpot(K.facing(20.3, BZ1 + 0.05, 0, 1, 9.0), "party", 9.6, 7.4)

	-- ============================================================== THE GYM AND BOXING CLUB (west)
	K.gym(CFrame.Angles(0, math.pi, 0), { x0 = 30, x1 = 92, z0 = -32, z1 = 32, h = 24, rings = { { 46, -14 }, { 76, -14 }, { 46, 14 }, { 76, 14 } },
		locker = { x0 = 52, x1 = 88, z0 = 36, z1 = 60, door = { 66, 74 } } })
	put("ht_doorS", at(-28, 0, 0, 90))
	put("ht_doorS", at(-30, 0, 0, -90)) -- (the gym's side of the same door)

	end -- (not LOBBY: the ballroom and the gym)
	if not LOBBY or BAR then
	-- ============================================================== THE LOUNGE BAR (east: x 30..66, z -2..30, low)
	local BX0, BX1, BZa, BZb, BH = 30, 66, -2, 30, 14
	box(F0, "Shell", "Floor", BX0, BX1 + 2, -1, 0, BZa - 2, BZb + 2, "7a6450", MAT.WoodPlanks)
	box(F0, "Shell", "Roof", BX0, BX1 + 2, BH, BH + 1, BZa - 2, BZb + 2, PAL.soffit, PLASTER)
	box(F0, "Shell", "Wall", BX0, BX1, 0, BH, BZa - 2, BZa, PAL.wall2, PLASTER)
	box(F0, "Shell", "Wall", BX0, BX1, 0, BH, BZb, BZb + 2, PAL.wall2, PLASTER)
	K.wall(CFrame.Angles(0, -math.pi / 2, 0), "Wall", BZa - 2, BZb + 2, 0, BH, -(BX1 + 2), -BX1, PAL.wall2, { { 20, 28, 10 } }, PLASTER) -- (the golf room's door)
	put("ht_doorS", at(30, 0, 14, 90)) -- (the bar's side of the door from the lobby)
	put("ht_doorS", at(28, 0, 14, -90))
	-- (round 3, judge round 2: the lounge fell to near-black and was a plain box) a cream coffered ceiling, lamps in the
	-- coffers, three ring lights; a raised seating step along the N wall
	-- (27 Nov, Clip v2: the chandeliers, 5.9 across, hung into the beams across the room 6 apart: those beams are gone, the
	-- three along it stay, so the ceiling is long bays the chandeliers hang down the middle of)
	box(F0, "Scenery", "Beam", BX1 - 6 - 0.8, BX1 - 6 + 0.8, BH - 1.4, BH + 0.1, BZa, BZb, PAL.ceil, PLASTER, { ghost = true })
	for _, z in { 6, 14, 22 } do box(F0, "Scenery", "Beam", BX0, BX1, BH - 1.4, BH + 0.1, z - 0.8, z + 0.8, PAL.ceil, PLASTER, { ghost = true }) end
	for _, p in { { 39, 2 }, { 51, 2 }, { 57, 18 }, { 39, 26 }, { 57, 26 } } do K.panel(F0, p[1], BH, p[2], 3, 3, { bright = 1.0, range = 22, lightHex = PAL.warm }) end
	for _, p in { { 39, 10 }, { 51, 10 }, { 45, 18 } } do
		put("ht_chandelier", at(p[1], BH, p[2]))
		K.light(box(F0, "Scenery", "ChandelierLight", p[1] - 0.3, p[1] + 0.3, BH - 2.6, BH - 2.4, p[2] - 0.3, p[2] + 0.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 20, 0.9, PAL.lamp)
	end
	box(F0, "Shell", "SeatStep", 32, 60, 0, 0.8, BZa, 6, PAL.wood2, MAT.WoodPlanks)
	box(F0, "Scenery", "SeatStepNosing", 32, 60, 0.5, 0.95, 5.5, 6.3, PAL.wood)
	K.bar(K.at(F0, 62, 14, 90), 14) -- (its drinkers on the west side)
	-- (polish, judges: the lounge's weakest point) the back-bar: a chunky wood built-in on the E wall behind the bar, three lit
	-- shelves in it, a cornice; the golf door framed in the same wood, its name over it
	box(F0, "Shell", "BackBar", 64.9, 66, 0, 11.2, 5.4, 19.2, PAL.wood2)
	box(F0, "Scenery", "BackBarCornice", 64.4, 66, 11.2, 12.2, 5.0, 19.6, PAL.wood)
	for _, y in { 4.6, 7.0, 9.4 } do
		local sh = box(F0, "Scenery", "BackBarShelfLight", 64.85, 64.95, y, y + 0.15, 6.0, 18.6, PAL.warm, MAT.Neon, { ghost = true, noshadow = true, tr = 0.4 })
		K.light(sh, 8, 0.5, PAL.warm, { kind = "SurfaceLight", face = Enum.NormalId.Left, angle = 120 })
	end
	for _, zz in { { 19.2, 20.0 }, { 28.0, 28.8 } } do box(F0, "Scenery", "GolfDoorJamb", 64.6, 66, 0, 10.8, zz[1], zz[2], PAL.wood) end
	box(F0, "Scenery", "GolfDoorHead", 64.6, 66, 10.0, 10.8, 19.2, 28.8, PAL.wood)
	for _, x in { 36.2, 55.8 } do
		put("ht_sofa", at(x, 0.8, 0.2, 0), { solid = true })
		put("ht_table", at(x, 0.8, 3.4, 0), { solid = true })
	end
	-- (round 4, judge round 3: one big set piece) the fireplace on the N wall: a stone surround, a mantel, a lit firebox
	box(F0, "Shell", "Fireplace", 40, 52, 0.8, 9.2, BZa, BZa + 1.6, PAL.stone, MARBLE)
	box(F0, "Scenery", "Firebox", 43, 49, 1.2, 5.2, BZa + 1.55, BZa + 1.7, "2e2722")
	box(F0, "Shell", "Hearth", 40.6, 51.4, 0.8, 1.1, BZa + 1.6, BZa + 3.2, PAL.stone)
	for i, y in { 1.45, 1.85 } do
		K.part("Scenery", "Log", F0 * CFrame.new(46 + (i - 1.5) * 0.6, y, BZa + 1.95), Vector3.new(4.2, 0.55, 0.55), "4a3426", MAT.Wood, { shape = Enum.PartType.Cylinder })
	end
	local fire = box(F0, "Scenery", "Fire", 44, 48, 1.2, 2.2, BZa + 1.72, BZa + 1.8, "ff7a2a", MAT.Neon, { ghost = true, noshadow = true, tr = 0.35 })
	for i, f in { { 44.9, 1.5, 2.6 }, { 46.0, 1.9, 3.3 }, { 47.1, 1.5, 2.7 } } do -- (shaped flames: tall wedges standing on the logs)
		local hgt = f[3] - f[2]
		K.part("Scenery", "Flame", F0 * CFrame.new(f[1], f[2] + hgt / 2 + 0.3, BZa + 2.0), Vector3.new(0.5, hgt, 0.9), if i == 2 then "ffd27a" else "ff9a3a", MAT.Neon,
			{ cls = "WedgePart", ghost = true, noshadow = true, tr = 0.2 })
	end
	K.light(fire, 15, 1.2, "ff9a50")
	box(F0, "Scenery", "Mantel", 39.4, 52.6, 6.0, 6.7, BZa, BZa + 2.2, PAL.wood)
	box(F0, "Scenery", "Overmantel", 41.5, 50.5, 7.2, 12.4, BZa, BZa + 0.4, PAL.wood)
	local mirror = box(F0, "Scenery", "Mirror", 42.2, 49.8, 7.9, 11.7, BZa + 0.4, BZa + 0.5, "7d878c", MAT.Glass) -- (darker: it read as an empty white frame)
	mirror.Reflectance = 0.35
	K.tableSpot(K.at(F0, 40, 15, 0), "board"); K.tableSpot(K.at(F0, 52, 23, 0), "arm")
	K.arcadeSpot(K.at(F0, 36, 28.5, 0)); K.arcadeSpot(K.at(F0, 42, 28.5, 0)) -- (hub-minigames: the 2.8-deep cabinets clear the wall)
	K.codePanelSpot(K.at(F0, 46, BZb, 0)) -- (on the S wall, looking north into the bar)
	palm(62, 0.5); palm(59.5, 27.0) -- (27 Nov, Clip v2: its fronds were 1 into the S wall) -- (26 Nov: the first palm 2 in, its fronds were in the wall) -- (the second palm clear of the golf door's new frame)
	K.golfRoom(F0, { x0 = 70, x1 = 124, z0 = GZ0, z1 = GZ1, h = 18, door = { 68, 20, 28 }, doorSide = "w", doorEnd = "s" })
	for _, x in { 78, 94, 110 } do -- (round 5: no black void through the golf room's door)
		K.light(box(F0, "Scenery", "GolfLight", x - 0.3, x + 0.3, 15.8, 16, 23.7, 24.3, PAL.lamp, nil, { ghost = true, tr = 1 }), 28, 0.9, PAL.lamp)
	end
	K.wordSign(K.facing(65.95, 24, -1, 0), "Scenery", "WaySign", 8, 1.6, 0, 11.9, 0, "SLAP GOLF", { accent = PAL.accent, bg = NAVY })
	K.light(box(F0, "Scenery", "DoorLight", 70.6, 71, 9, 9.2, 23.8, 24.2, PAL.lamp, nil, { ghost = true, tr = 1 }), 22, 0.8, PAL.warm) -- (no black void through the door)

	end -- (not LOBBY, or BAR: the bar and the golf room)
	-- ============================================================== THE ARMORY (south-west) and THE SERVICE CORRIDOR (south-east)
	if not LOBBY then K.armory(CFrame.new(-22, 0, 0) * CFrame.Angles(0, math.pi, 0), { d0 = 34, d1 = 80, w = 5.5, h = 12, door = "HotelToTraining" }) end
	-- (the service corridor runs west behind the lobby's S wall: x 4..26, so its open front is all on that wall)
	K.zombieRoom(CFrame.new(24, 0, 32) * CFrame.Angles(0, math.pi, 0), { x0 = -2, x1 = 20, d = 18, h = 11, door = 4, guideSide = 1 })

	-- ============================================================== VIP: the suite at the top of the stair
	K.vip(CFrame.new(0, MZ, 32) * CFrame.Angles(0, math.pi, 0), { w = 12, d = 20, h = 11, front = 20, frontH = H - MZ })

	-- ============================================================== THE REGULARS
	-- Looticus: behind reception, on the W sofa, behind the bar
	local LOOT = { { "stand", 26.8, 0, -16, 90 }, { "sit", -25.6, 1.3, 14.4, 90 }, { "sit", -25.6, 1.3, 17.6, 90 } } -- (26 Nov: none behind the bar: 1.1 between counter and shelves)
	K.npc(F0, "Looticus", LOOT[1][2], LOOT[1][3], LOOT[1][4], LOOT[1][5])
	for k, w in LOOT do K.npcPoint(F0, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5]) end
	if not LOBBY then
	-- Frisk1636: along the ballroom's stage
	local BZ1 = -34 - 7 * 17
	local FR = { { "stop", -14 }, { "via", -6 }, { "stop", 0 }, { "via", 6 }, { "stop", 14 } }
	K.npc(F0, "Frisk1636", FR[1][2], 1.2, BZ1 + 14.2, 0)
	for k, w in FR do K.npcPoint(F0, "Frisk1636", k, w[1], "stand", w[2], 1.2, BZ1 + 14.2, 0, { pause = if w[1] == "stop" then { 8, 16 } else nil }) end
	-- Dune: round three sides of the gym's first ring
	local Fg = CFrame.Angles(0, math.pi, 0)
	local DU = { { "stop", 32.5, -14, -90 }, { "via", 32.5, -27.4, 180 }, { "stop", 46, -27.4, 180 }, { "via", 61, -27.4, 180 }, { "stop", 61, -14, 90 } }
	K.npc(Fg, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for k, w in DU do K.npcPoint(Fg, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end
	end -- (not LOBBY: Frisk1636 and Dune)
	for _, d in f:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "SpectatePanel" or d.Name == "LiveBoardPanel") then
			d.Color = K.c3(NAVY)
			for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do -- (a lit navy face, with its name, under whatever the board shows)
				local g = Instance.new("SurfaceGui"); g.Name = "Rest"; g.Face = face; g.LightInfluence = 0; g.Brightness = 1.4
				g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 20; g.Parent = d
				local fr = Instance.new("Frame"); fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = K.c3(NAVY); fr.BorderSizePixel = 0; fr.Parent = g
				local t = Instance.new("TextLabel"); t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(0.84, 0.3); t.Position = UDim2.fromScale(0.08, 0.26)
				t.Font = Enum.Font.GothamBlack; t.TextScaled = true; t.TextColor3 = K.c3("f2f0ea")
				t.Text = if d.Name == "SpectatePanel" then "SPECTATE" else "RANKED"; t.Parent = fr
				local u = Instance.new("TextLabel"); u.BackgroundTransparency = 1; u.Size = UDim2.fromScale(0.7, 0.14); u.Position = UDim2.fromScale(0.15, 0.6)
				u.Font = Enum.Font.GothamSemibold; u.TextScaled = true; u.TextColor3 = K.c3("c8d0e0"); u.Parent = fr
				u.Text = if d.Name == "SpectatePanel" then "LIVE MATCHES" elseif (d.Position - (HH.SITE).Position).X < 0 then "DUELS" else "PARTIES"
			end
		elseif d:IsA("Frame") and d.Parent and d.Parent:IsA("SurfaceGui") and d.Parent.Parent and d.Parent.Parent.Name == "CountBoard" then d.BackgroundColor3 = K.c3(NAVY)
		elseif d:IsA("BasePart") and d.Name == "MiniGameSpot" and d:GetAttribute("Game") == "golf" then
			d:SetAttribute("Door", Vector3.new(-28, 0, 24 - (GZ1 - 50))) -- (from the course's middle (z1 - 50) to the door's, z 24) -- (hub-minigames: the PLAY prompt just inside the golf room's door; LEAVE puts golfers back there)
		elseif d:IsA("BasePart") and d.Name == "TableRug" then d.Color = K.c3("8f8a76"); d.Material = MAT.SmoothPlastic -- (the kit's rug is near-black in the lounge's warm light)
		elseif d:IsA("BasePart") and d.Name:match("^ht_vault%d") then d.Color = K.c3("bdb09b") -- (round 3: the vault a step down: the pads the brightest)
		elseif d:IsA("BasePart") and d.Name == "StoolStem" then d.Size = Vector3.new(d.Size.X, 1.2, 1.2) -- (thick pedestals)
		elseif d:IsA("BasePart") and d.Name == "StoolFoot" then d.Size = Vector3.new(d.Size.X, 1.9, 1.9); d.Color = K.c3("a89466")
		elseif d:IsA("BasePart") and d.Name == "BarCounter" then d.Color = K.c3(PAL.wood); d.Material = MAT.Wood
		elseif d:IsA("BasePart") and d.Name == "BarTop" then d.Color = K.c3(PAL.stone)
		elseif d:IsA("BasePart") and d.Name == "BarShelfWall" then d.Color = K.c3(PAL.wood2)
		elseif d:IsA("BasePart") and d.Name == "StoolSeat" then d.Color = K.c3("6f8a76")
		elseif d:IsA("BasePart") and d.Name:match("^ht_coffer") then d.Color = K.c3("c9bca8") -- (round 4: the ceiling a step under the walls)
		end
	end
	-- (round 4) the bar's shelves: three big brass urns a shelf, not rows of little things (no bottles: the content rating)
	local rows = {}
	for _, d in f:GetDescendants() do
		if d:IsA("BasePart") and d.Name == "Bottle" then
			local y = math.floor(d.Position.Y * 2 + 0.5)
			rows[y] = rows[y] or {}; table.insert(rows[y], d)
		end
	end
	for _, list in rows do
		table.sort(list, function(a, b) return (a.Position.X + a.Position.Z) < (b.Position.X + b.Position.Z) end)
		for i, d in list do
			if i == 2 or i == math.ceil(#list / 2) + 1 or i == #list - 1 then
				local h = d.Size.X
				d.Size = Vector3.new(1.7, 1.5, 1.5); d.CFrame = d.CFrame + Vector3.new(0, (1.7 - h) / 2, 0); d.Color = K.c3("a89466"); d.Material = MAT.SmoothPlastic; d.Name = "Urn"
			else d:Destroy() end
		end
	end
	-- (26 Nov, main's list: HubSeat tags) a seat on every kit sofa cushion and armchair, so players can sit where the regulars do
	for _, d in f:GetDescendants() do
		if d:IsA("Model") and d.Name == "ht_sofa" then K.seatsOn(d, nil, 3) elseif d:IsA("Model") and d.Name == "ht_armchair" then K.seatsOn(d, nil, 1) end
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
		{ "to the ballroom's doors", F0, -6, 6, -38, -28.5 }, { "behind reception", F0, 26.3, 27.3, -23, -9 }, { "round the fountain W", F0, -14, -10, -26, -13 }, { "round the fountain E", F0, 10, 14, -26, -13 },
		{ "the ballroom's walk", F0, -10, 10, -66, -36 }, { "the ballroom's walk on", F0, -10, 10, -135, -87 },
		{ "round the crossing W", F0, -11.5, -7.5, -86, -67 }, { "round the crossing E", F0, 7.5, 11.5, -86, -67 },
		{ "into the W alcove", F0, -36, -27, -83, -80.6 }, { "into the E alcove", F0, 27, 33.5, -83, -80.6 }, { "into the gym", F0, -34, -24, -3, 3 }, { "into the bar", F0, 24, 34, 11, 17 },
		{ "into the armory", F0, -26, -18, 26.5, 35 }, { "into the service corridor", F0, 22.5, 25.5, 26, 34.5 },
		{ "to the lifts", F0, 9, 15, 20, 26 }, { "the W gallery", F0, -24.2, -21.8, -30, 22, 14 }, { "the E gallery", F0, 21.8, 24.2, -30, 22, 14 },
	}
end
function HH.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 8, 0 }, { F0, 0, 20, -10 }, { F0, 0, 8, -70 }, { F0, 0, 14, -110 }, { F0, -33, 8, -76.5 }, { F0, 33, 8, -76.5 }, { F0, 0, 14, -140 }, { F0, -60, 8, 0 }, { F0, 48, 6, 14 }, { F0, -22, 6, 56 }, { F0, 15, 6, 44 }, { F0, 0, 18, 44 }, { F0, 96, 6, 0 } }
end
local MZv = 14
HH.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 1.5), Vector3.new(0, 9, -30) },
	{ "lobby from the gallery", Vector3.new(-24, MZv + 5.4, 26), Vector3.new(8, 8, -20) },
	{ "ballroom", Vector3.new(0, 6.5, -37), Vector3.new(0, 5, -100) },
	{ "the crossing", Vector3.new(-8, 7, -62), Vector3.new(30, 6, -78) },
	{ "pads close", Vector3.new(4, 6, -55), Vector3.new(-22, 4, -64) },
	{ "the stair and the suite", Vector3.new(0, 6, -10), Vector3.new(0, 14, 30) },
	{ "south from the fountain", Vector3.new(4, 6, -12), Vector3.new(-10, 9, 30) },
	{ "reception", Vector3.new(4, 6, -10), Vector3.new(26, 4, -18) },
	{ "bar", Vector3.new(32, 6, 14), Vector3.new(62, 4, 10) },
	{ "ceiling", Vector3.new(-6, 5, 6), Vector3.new(0, 26, -20) },
}
return HH
