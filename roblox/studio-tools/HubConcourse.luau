--!nonstrict
-- A: THE CONCOURSE (20 Nov 2026; the owner: "can you model all 3 and let me have an option to travel between hubs").
-- A long grand hall, 76 wide inside and 140 long, 31 high. Columns and beams down both sides hold a mezzanine over the
-- side aisles, and the pads sit under it in five bays a side: PLAYER SPOTS on a low stage, the mode and its count on
-- the bay's beam. The lounge fills the spawn end (south): the shop and its bundles east, the arcade, the code panel and
-- the bar west, the tables and seats either side. A middle island of planters and benches runs down the nave under a big
-- live screen. At the far end (north) the gym opens across the hall's whole middle; the hall of fame (the ranked boards,
-- the trophies) is in the east corner, the armory with the training gate opens off the west corner. VIP is behind the
-- south wall, the golf room behind the east wall's lounge end, the locker room off the gym's east side.
-- In world studs from the site, x east, z south (north = -z). Built by HubKit (side-session-notes/HUB-MARKERS.md).
local HC = {}
HC.ID, HC.FOLDER, HC.TITLE, HC.ORDER = "concourse", "Concourse", "THE CONCOURSE", 2
HC.SITE = CFrame.new(-200, 240, -14200)

local BZ = { 22.5, 7.5, -7.5, -22.5, -37.5 } -- (the bays' middles, 1v1 nearest the spawn)
local CZ = { -60, -45, -30, -15, 0, 15, 30, 45, 60 } -- (the columns)

function HC.build(K, parent, name, site, live)
	local P, MAT = K.P, K.MAT
	local F0 = CFrame.new()
	local f = K.begin(parent, name or HC.FOLDER, site or HC.SITE, HC.ID, { Title = HC.TITLE, Order = HC.ORDER }, live)
	local box, cyl = K.box, K.cyl
	local T, MY = 31, 13 -- (the ceiling's underside, the mezzanine's underside)
	-- frames for the long walls and the mezzanines: in ME (east) and MW (west) x runs along the hall (ME: north, MW:
	-- south) and z runs out from the middle line, so z 26..38 is a side aisle on either side
	local ME, MW = CFrame.Angles(0, math.pi / 2, 0), CFrame.Angles(0, -math.pi / 2, 0)
	local FE, FW = CFrame.Angles(0, -math.pi / 2, 0), CFrame.Angles(0, math.pi / 2, 0) -- (the east / west wall's face at z -38: x runs south / north)

	-- ============================================================== THE HALL
	box(F0, "Shell", "Floor", -26, 26, -1, 0, -70, 72, P.paving, MAT.Slate) -- (to 72: under the VIP doorway)
	for _, s in { -1, 1 } do box(F0, "Shell", "FloorAisle", s * 26, s * 40, -1, 0, -72, 72, P.paving2, MAT.Slate) end
	box(F0, "Shell", "FloorEnd", -26, 26, -1, 0, -72, -70, P.paving2, MAT.Slate)
	box(F0, "Scenery", "Runner", -6, 6, 0, 0.05, -66, 28, P.runner, MAT.Fabric)
	-- the walls: the golf room's door in the east one, the armory's way in the west one, the gym across the north one
	K.wall(FE, "Wall", -72, 72, 0, T, -40, -38, P.wall, { { 58, 66, 10 } })
	K.wall(FW, "Wall", -72, 72, 0, T, -40, -38, P.wall, { { 46, 59, 12 }, { -54, -49, 8.5 } }) -- (-54..-49: the zombies room's doorway, z 49..54)
	K.wall(F0, "Wall", -38, 38, 0, T, -72, -70, P.wall, { { -20, 20, 21 } })
	box(F0, "Shell", "Roof", -40, 40, T, T + 1, -72, 72, P.dome)
	-- the columns (full height, a band at the mezzanine), the mezzanine over each side aisle: its slab, a cream fascia,
	-- the glass rail; pilasters on the walls above it, a band; benches along the rail looking down the hall
	for _, s in { -1, 1 } do
		local R = if s > 0 then ME else MW
		for _, z in CZ do K.column(F0, s * 26, z, 0, T, 2, { cap = MY }) end
		box(R, "Shell", "Mezzanine", -70, 70, MY, MY + 1, 26, 38, P.floor2)
		box(R, "Scenery", "MezzFascia", -70, 70, MY - 0.4, MY + 1.2, 25.4, 26.2, P.cream) -- (its top under the rail's foot)
		K.rail(R, -70, 70, MY + 1, 26)
		for _, z in CZ do box(F0, "Scenery", "Pilaster", s * 37.4, s * 38, MY + 1, T, z - 0.9, z + 0.9, P.pier) end
		box(R, "Scenery", "WallBand", -70, 70, 24, 24.6, 37.7, 38, P.cream)
		for _, x in { -46, -16, 14, 44 } do K.bench(R * CFrame.new(x, MY + 1, 29), 10, { back = true }) end -- (their look: to the middle; clear of the jump pads' landings)
		for _, z in { -52.5, -22.5, 7.5, 37.5, 60 } do K.panel(F0, s * 32, T, z, 6, 10, { bright = 0.55, range = 22 }) end
	end
	-- the roof: beams across every 10, the nave's panels between them
	for z = -65, 65, 10 do box(F0, "Scenery", "CeilingBeam", -26, 26, T - 2.6, T, z - 0.7, z + 0.7, P.cream, nil, { ghost = true }) end
	for z = -60, 60, 10 do K.panel(F0, 0, T, z, 12, 8.4, { bright = 0.75, range = 40 }) end
	for _, s in { -1, 1 } do box(F0, "Scenery", "RoofEdgeBeam", s * 25.3, s * 26.7, T - 2.6, T, -70, 70, P.cream, nil, { ghost = true }) end

	-- ============================================================== THE PAD BAYS (under the mezzanine)
	-- five a side: a beam across each bay's mouth carrying its sign, fins between bays, a backdrop with a lit cove
	for _, s in { -1, 1 } do
		for k, zc in BZ do
			local md = K.MODES[k]
			box(F0, "Scenery", "BayBeam", s * 25.2, s * 26.8, 10.4, 12.6, zc - 7, zc + 7, P.cream)
			box(F0, "Scenery", "BayBack", s * 37.45, s * 38, 0.8, 11.6, zc - 6.6, zc + 6.6, P.wall2)
			K.light(box(F0, "Scenery", "BayCove", s * 36.9, s * 37.45, 11.6, 11.8, zc - 6.4, zc + 6.4, P.light, MAT.Neon, { ghost = true, noshadow = true }), 14, 0.45)
			K.spotsPad(K.facing(s * 27, zc, s, 0), md, if s < 0 then "lifts" else "east", if s < 0 then md.id else md.id .. "_e",
				{ w = 12.6, d = 10.4, signY = 11.5, signZ = 2.0, lampY = 12.6 })
		end
		for _, z in { -45, -30, -15, 0, 15, 30 } do box(F0, "Shell", "BayFin", s * 27, s * 38, 0, MY, z - 0.4, z + 0.4, P.wall2) end
	end

	-- ============================================================== THE SPAWN END: the lounge
	cyl(F0, "Scenery", "SpawnRing", 0, -0.02, 0.06, 58, 12.6, P.creamHi)
	cyl(F0, "Scenery", "SpawnRug", 0, 0.06, 0.1, 58, 11.8, P.carpet2, MAT.Fabric)
	for i = 0, 7 do K.marker(F0, "HubSpawns", "Spawn", -3.6 + (i % 4) * 2.4, 0.1, 57 + math.floor(i / 4) * 2.4, 0) end
	K.marker(F0, "HubArrive", "Arrive", 0, 0.1, 52, 0)
	K.travelTerminal(K.at(F0, 10, 66, 0))
	K.holoLoadout(K.at(F0, 0, 34, 180))
	-- east: the shop under the mezzanine, its bundles in front; the golf room's door beyond it
	K.shop(K.at(F0, 33, 44, 90), 20)
	K.bundles(K.at(F0, 22, 44, 90))
	K.thinFrame(FE, 58, 66, 10, -38, "GOLF")
	-- west: the arcade, the code panel, the bar
	K.arcadeSpot(K.at(F0, -36.4, 35, -90))
	K.codePanelSpot(K.at(F0, -38, 42, -90))
	K.bar(K.at(F0, -33, 64, -90), 10)
	for _, z in { 40, 60 } do for _, s in { -1, 1 } do K.panel(F0, s * 32, MY, z, 6, 8, { bright = 0.5, range = 16 }) end end
	-- the tables either side of the middle; seats by the south wall
	K.tableSpot(K.at(F0, -12, 44, 0), "board"); K.tableSpot(K.at(F0, 12, 44, 0), "arm")
	K.cluster(K.at(F0, -19, 63, -90), { npcSofa = true }); K.cluster(K.at(F0, 19, 63, 90), { npcSofa = true })
	for _, s in { -1, 1 } do K.jumpPad(K.at(F0, s * 17, 27, if s > 0 then -90 else 90), Vector3.new(0, 60, 11)) end

	-- the zombies room behind the west wall, its door between the code panel and the bar
	K.zombieRoom(CFrame.new(-38, 0, 51.5) * CFrame.Angles(0, math.pi / 2, 0), { x0 = -10.5, x1 = 11.5, d = 18, h = 11, door = 5, guideSide = -1 })
	-- the VIP end wall: pilasters either side of the VIP front's windows, a cornice over them, a band up high
	for _, s in { -1, 1 } do for _, x in { 17, 25 } do box(F0, "Scenery", "EndPilaster", s * x - 0.8, s * x + 0.8, 0, T, 69.4, 70, P.pier) end end
	box(F0, "Scenery", "EndCornice", -26.3, 26.3, 15.4, 16.2, 69.3, 70, P.cream)
	box(F0, "Scenery", "EndBand", -26.3, 26.3, 24, 24.6, 69.2, 70, P.cream)
	for _, x in { -8.5, 8.5 } do K.panel(F0 * CFrame.new(0, 0, 0), x, T, 64, 8, 6, { bright = 0.7, range = 36 }) end

	-- ============================================================== THE MIDDLE ISLAND and the big screen
	for _, zc in { 17, -3, -26 } do
		local Fi = F0 * CFrame.new(0, 0, zc)
		box(Fi, "Shell", "Planter", -1.3, 1.3, 0, 2.2, -6, 6, P.cream)
		box(Fi, "Scenery", "PlanterSoil", -1.0, 1.0, 2.2, 2.26, -5.7, 5.7, P.soil)
		for i = -2, 2 do K.ball(Fi, "Scenery", "Bush", 0, 3.1, i * 2.3, 2.6, if i % 2 == 0 then P.plant else P.plant2, MAT.Grass) end
		for _, s in { -1, 1 } do K.bench(Fi * CFrame.new(s * 2.6, 0, 0) * CFrame.Angles(0, math.rad(if s < 0 then 90 else -90), 0), 10) end
	end
	local scr = box(F0, "Scenery", "LiveScreen", -15, 15, 16, 26, -15.5, -14.5, P.screen) -- (hung from the beam at z -15)
	K.screen(scr, { Enum.NormalId.Front }) -- (the counts face north; the spawn side carries the SPECTATE board)
	K.spectateSpot(K.facing(0, -14.5, 0, 1, 21), 28, 9.4, { flush = true })
	box(F0, "Scenery", "LiveScreenFrame", -15.4, 15.4, 26, 26.5, -15.7, -14.3, P.creamHi)
	box(F0, "Scenery", "LiveScreenFrame", -15.4, 15.4, 15.5, 16, -15.7, -14.3, P.creamHi)
	for _, s in { -1, 1 } do cyl(F0, "Scenery", "ScreenRod", s * 12, 26.5, T - 2.6, -15, 0.35, P.steel) end

	-- ============================================================== THE FAR END
	-- the hall of fame in the east corner: the two ranked boards on the wall, the trophy case between them
	K.boardSpot(K.at(F0, 37.95, -65.5, 90, 6.2), "duels", 7.6, 6.6)
	K.boardSpot(K.at(F0, 37.95, -50.5, 90, 6.2), "party", 7.6, 6.6)
	K.trophyCase(K.at(F0, 36.6, -58, 90), 5.6)
	K.panel(F0, 32, MY, -58, 6, 16, { bright = 0.5, range = 16 })
	-- the armory's way in from the west corner (under the mezzanine), its sign under the mezzanine's edge
	K.thinFrame(FW, 46, 59, 12, -38, "ARMORY  ·  TRAINING", { signW = 12, signZ = -26.15, signY = MY - 0.4 - 1.0 })
	K.panel(F0, -32, MY, -52.5, 6, 10, { bright = 0.5, range = 16 })
	for _, z in { -66, -62 } do K.bench(K.at(F0, -36.6, z, -90), 3.4, { back = true }) end
	-- the gym, across the north wall's middle: its frame and sign
	K.thinFrame(F0, -20, 20, 21, -70, "GYM", { signW = 14 })

	-- ============================================================== THE GYM (north), its locker room (east of it)
	K.gym(CFrame.Angles(0, math.pi / 2, 0), { x0 = 72, x1 = 134, z0 = -38, z1 = 38, h = 23, rings = { { 86, -15 }, { 116, -15 }, { 86, 15 }, { 116, 15 } },
		locker = { x0 = 76, x1 = 124, z0 = 42, z1 = 66, door = { 96, 104 } } })

	-- ============================================================== THE ARMORY (west), the training gate at its end
	K.armory(CFrame.new(0, 0, -52.5) * CFrame.Angles(0, math.pi / 2, 0), { d0 = 40, d1 = 86, w = 16, h = 15, door = "ConcourseToTraining" })

	-- ============================================================== VIP (south) and THE GOLF ROOM (east)
	K.vip(CFrame.new(0, 0, 70) * CFrame.Angles(0, math.pi, 0), { w = 16, d = 24, h = 14, front = 38, frontH = T })
	K.golfRoom(F0, { x0 = 42, x1 = 96, z0 = -28, z1 = 66, h = 18, door = { 40, 58, 66 }, doorSide = "w", doorEnd = "s" })

	-- ============================================================== THE REGULARS
	-- Looticus: the lounge's sofas, behind the shop counter, behind the bar
	local LOOT = { { "sit", -22.5, 1.45, 61.4, -90 }, { "sit", -22.5, 1.45, 64.6, -90 }, { "sit", 22.5, 1.45, 61.4, 90 }, { "sit", 22.5, 1.45, 64.6, 90 },
		{ "stand", 35.4, 0, 44, 90 }, { "stand", -34.8, 0, 64, -90 } }
	K.npc(F0, "Looticus", LOOT[1][2], LOOT[1][3], LOOT[1][4], LOOT[1][5])
	for k, w in LOOT do K.npcPoint(F0, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5]) end
	-- Frisk1636: up and down before the hall of fame
	local FR = { { "stop", -66 }, { "via", -60 }, { "stop", -58 }, { "via", -55 }, { "stop", -50 } }
	K.npc(F0, "Frisk1636", 30, 0, FR[1][2], -90)
	for k, w in FR do K.npcPoint(F0, "Frisk1636", k, w[1], "stand", 30, 0, w[2], -90, { pause = if w[1] == "stop" then { 8, 16 } else nil }) end
	-- Dune: round three sides of the gym's first ring
	local DU = { { "stop", -15, -73.6, 0 }, { "via", -28.6, -73.6, 90 }, { "stop", -28.6, -86, -90 }, { "via", -28.6, -98.6, 0 }, { "stop", -15, -98.6, 180 } }
	K.npc(F0, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for k, w in DU do K.npcPoint(F0, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end
	return f
end

-- the check: the ways that must stay clear (walks) and the rooms no ray may get out of (leaks), in site frames
function HC.walks(K)
	local F0 = CFrame.new()
	return {
		{ "the east lane, spawn to the far end", F0, 7.5, 14, -66, 52 }, { "the west lane, spawn to the far end", F0, -14, -7.5, -66, 52 },
		{ "the spawn to the VIP door", F0, -2, 2, 52, 69 }, { "into the gym", F0, -3.5, 3.5, -100, -60 },
		{ "into the armory", F0, -52, -27, -57, -48 }, { "into the golf room", F0, 28, 50, 59, 65 },
		{ "the east mezzanine", F0, 31, 37, -68, 68, 14 }, { "the west mezzanine", F0, -37, -31, -68, 68, 14 },
		{ "the hall of fame", F0, 27.5, 33, -69, -46 }, { "into the zombies room", F0, -48, -30, 49.8, 52.2 },
	}
end
function HC.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 8, 0 }, { F0, 0, 26, 40 }, { F0, 32, 17, 0 }, { F0, -32, 17, -30 }, { F0, 0, 10, -100 }, { F0, -62, 8, -52 },
		{ F0, 70, 8, 20 }, { F0, 0, 6, 86 }, { F0, 54, 6, -100 }, { F0, -50, 6, 46 } }
end
HC.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 64), Vector3.new(0, 9, 20) },
	{ "bays", Vector3.new(-10, 6.5, 2), Vector3.new(30, 4, 16) },
	{ "gym", Vector3.new(0, 6.5, -44), Vector3.new(0, 5, -100) },
	{ "mezzanine", Vector3.new(33, 19.5, 52), Vector3.new(-4, 10, -20) },
	{ "lounge", Vector3.new(-16, 6.5, 28), Vector3.new(22, 4, 60) },
	{ "armory", Vector3.new(-30, 6.5, -50), Vector3.new(-84, 4, -53) },
	{ "zombies", Vector3.new(-24, 6, 58), Vector3.new(-48, 4, 50) },
}
return HC
