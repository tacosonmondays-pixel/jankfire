--!nonstrict
-- B: THE ATRIUM (20 Nov 2026; the owner: "can you model all 3 and let me have an option to travel between hubs"). An
-- octagonal hall three levels high (80 across inside, 44 high) round a big screen hung in the middle over a round
-- island of seats. The ten pads sit on the ground ring as raised PLATFORMS shaped to their side (W, NW, N, NE, E, two a
-- side), each with a rim light and a floating sign. Level 2 (y 15) is the lounge: the shop over the spawn (S), the
-- tables, the arcade, a bar, seats, the code panel, and a window into the gym. Level 3 (y 29): VIP behind glass (N),
-- the ranked boards, your loadout, the bundles. The gym opens off the SE side through a framed portal, the armory with
-- the training gate off the SW. Jump pads go up a level at a time. Lit under each level (the blockout's dark spot).
-- In world studs from the site, x east, z south; sideF(b) looks out at bearing b (0 north, 90 east), x to its right.
local HA = {}
HA.ID, HA.FOLDER, HA.TITLE, HA.ORDER = "atrium", "Atrium", "THE ATRIUM", 3
HA.SITE = CFrame.new(-200, 240, -15800)

local RW, RV, RV3, Y2, Y3, TOP = 40, 18, 24, 15, 29, 44
local function sideF(b) return CFrame.Angles(0, -math.rad(b), 0) end
HA.sideF = sideF

function HA.build(K, parent, name, site, live)
	local P, MAT = K.P, K.MAT
	local F0 = CFrame.new()
	local f = K.begin(parent, name or HA.FOLDER, site or HA.SITE, HA.ID, { Title = HA.TITLE, Order = HA.ORDER }, live)
	local box, cyl = K.box, K.cyl
	local function hw(r) return r * K.T225 end
	local function at(b, x, z, yaw, y) return K.at(sideF(b), x, z, yaw, y) end

	-- ============================================================== THE OCTAGON
	local ww = hw(RW + 2) + 0.05
	for b = 0, 315, 45 do
		local Fk = sideF(b)
		for _, s in { -1, 1 } do K.slant(Fk, "Shell", "Floor", 0, s * hw(RW + 2), 0, -RW - 2, -1, 0, "8a8781", MAT.Slate) end -- (an octagon: a square slab would meet the gym's and the armory's floors in one plane)
		if b == 135 then -- (the gym: its portal on the ground, a window from level 2)
			for _, s in { -1, 1 } do box(Fk, "Shell", "Wall", s * 12, s * ww, 0, TOP, -RW - 2, -RW, P.wallLt) end
			box(Fk, "Shell", "Wall", -12, 12, 10.4, Y2 + 1.5, -RW - 2, -RW, P.wallLt)
			box(Fk, "Shell", "Wall", -12, 12, Y2 + 9, TOP, -RW - 2, -RW, P.wallLt)
			box(Fk, "Scenery", "GymWindow", -12, 12, Y2 + 1.5, Y2 + 9, -RW - 1.15, -RW - 0.85, P.glass, MAT.Glass, { tr = 0.55, solid = true })
			for _, x in { -6, 0, 6 } do box(Fk, "Scenery", "WindowMullion", x - 0.15, x + 0.15, Y2 + 1.5, Y2 + 9, -RW - 1.3, -RW - 0.7, P.steel) end
		elseif b == 225 then
			K.wall(Fk, "Wall", -ww, ww, 0, TOP, -RW - 2, -RW, P.wallLt, { { -7, 7, 10.4 } })
		elseif b == 180 then -- (the zombies room's doorway, beside the spawn)
			K.wall(Fk, "Wall", -ww, ww, 0, TOP, -RW - 2, -RW, P.wallLt, { { 9, 14, 8.5 } })
		elseif b == 0 then -- (VIP's front fills level 3 up)
			box(Fk, "Shell", "Wall", -ww, ww, 0, Y3, -RW - 2, -RW, P.wallLt)
		else
			box(Fk, "Shell", "Wall", -ww, ww, 0, TOP, -RW - 2, -RW, P.wallLt)
		end
		-- the two galleries: level 2 from the void's edge out, level 3 from further out; fascias, glass rails
		for _, lv in { { RV, Y2 }, { RV3, Y3 } } do
			local r0, y = lv[1], lv[2]
			box(Fk, "Shell", "Gallery", -hw(r0), hw(r0), y - 1, y, -RW, -r0, P.wood, MAT.WoodPlanks) -- (wood: a warm floor up there, a warm ceiling under it)
			for _, s in { -1, 1 } do K.slant(Fk, "Shell", "Gallery", s * hw(r0), s * hw(RW), -r0, -RW, y - 1, y, P.wood, MAT.WoodPlanks) end
			box(Fk, "Scenery", "GalleryFascia", -hw(r0), hw(r0), y - 1.5, y + 0.2, -r0 - 0.12, -r0 + 0.6, P.cream) -- (its back face behind the rail foot's)
			K.rail(Fk * CFrame.Angles(0, math.pi, 0), -hw(r0 - 0.4), hw(r0 - 0.4), y, r0 - 0.2)
		end
		-- lights under each level and under the roof
		for _, z in { -26.5, -35 } do K.panel(Fk, 0, Y2 - 1, z, 8, 4, { bright = 1.5, range = 22 }) end -- (the ground ring, under level 2: the blockout's dark spot)
		K.panel(Fk, 0, Y3 - 1, -33, 9, 5, { bright = 0.9, range = 20 })
		K.panel(Fk, 0, TOP, -33, 9, 5, { bright = 0.85, range = 24 })
		-- a downlight at the void's edge under the roof, onto the middle
		local dl = box(Fk, "Scenery", "VoidLamp", -0.5, 0.5, TOP - 0.7, TOP - 0.5, -RV + 1.5, -RV + 2.5, P.pier, nil, { ghost = true, tr = 1 })
		K.light(dl, 60, 1.3, P.warm, { kind = "SpotLight", angle = 55 })
		-- the roof over the levels; a column at each corner of the void up to it, a rib from the middle to each
		box(Fk, "Shell", "Roof", -hw(RV), hw(RV), TOP, TOP + 1, -RW - 2, -RV, P.dome)
		for _, s in { -1, 1 } do K.slant(Fk, "Shell", "Roof", s * hw(RV), s * hw(RW + 2), -RV, -RW - 2, TOP, TOP + 1, P.dome) end
		local a = math.rad(b + 22.5)
		local rc = RV / math.cos(math.rad(22.5)) + 0.6
		K.column(F0, math.sin(a) * rc, -math.cos(a) * rc, 0, TOP, 2, { round = true, cap = Y2 - 1, hex = P.creamHi, mat = MAT.SmoothPlastic })
		K.rod(F0, "Scenery", "RoofRib", Vector3.new(0, TOP - 0.6, 0), Vector3.new(math.sin(a) * rc, TOP - 0.6, -math.cos(a) * rc), 0.9, P.cream, nil, { ghost = true })
	end
	box(F0, "Scenery", "Skylight", -RV, RV, TOP + 0.2, TOP + 0.4, -RV, RV, P.light, MAT.Neon, { solid = false, noshadow = true }) -- (queryable: it closes the roof)
	local sk = box(F0, "Scenery", "SkylightLamp", -1, 1, TOP - 0.4, TOP - 0.2, -1, 1, P.pier, nil, { ghost = true, tr = 1 })
	K.light(sk, 60, 1.6, P.light, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 120 })
	box(F0, "Shell", "FloorUnder", -42, 42, -1.6, -1, -42, 42, P.paving2) -- (under the floor's wedges: their seams are hairlines)

	-- ============================================================== THE PADS (ground ring, W to E)
	local ORDER = { 1, 2, 3, 4, 5, 5, 4, 3, 2, 1 }
	local k = 0
	for _, b in { 270, 315, 0, 45, 90 } do
		for _, left in { true, false } do
			k += 1
			local md = K.MODES[ORDER[k]]
			K.platformPad(sideF(b), left, md, if k <= 5 then "lifts" else "east", if k <= 5 then md.id else md.id .. "_e", 24, 38.5, { lampY = Y2 - 1.2, signY = 8.8 })
		end
	end

	-- ============================================================== THE MIDDLE: the island and the screen
	cyl(F0, "Shell", "Island", 0, 0, 0.5, 0, 17, P.creamHi)
	cyl(F0, "Shell", "IslandPlanter", 0, 0.5, 2.8, 0, 7, P.cream)
	cyl(F0, "Scenery", "IslandSoil", 0, 2.8, 2.86, 0, 6.4, P.soil)
	for i = 0, 4 do K.ball(F0, "Scenery", "Bush", math.cos(i * 1.26) * 1.8, 4.1, math.sin(i * 1.26) * 1.8, 3.2, if i % 2 == 0 then P.plant else P.plant2, MAT.Grass) end
	for i = 0, 7 do
		local a = i * math.pi / 4
		K.bench(CFrame.new(math.sin(a) * 6, 0.5, -math.cos(a) * 6) * CFrame.Angles(0, -a, 0), 3.6) -- (facing out)
	end
	local cube = box(F0, "Scenery", "ScreenCube", -8, 8, 20, 28, -8, 8, P.screen)
	K.screen(cube, { Enum.NormalId.Front, Enum.NormalId.Back }) -- (the counts face north and south)
	for _, sx in { -1, 1 } do K.spectateSpot(K.facing(sx * 8, 0, sx, 0, 24), 15.6, 7.6, { flush = true }) end -- (the SPECTATE boards face east and west)
	box(F0, "Scenery", "ScreenCubeCap", -8.4, 8.4, 28, 28.6, -8.4, 8.4, P.creamHi)
	box(F0, "Scenery", "ScreenCubeFoot", -8.4, 8.4, 19.4, 20, -8.4, 8.4, P.creamHi)
	for i = 0, 3 do
		local a = math.rad(22.5 + i * 90)
		cyl(F0, "Scenery", "ScreenRod", math.sin(a) * 7, 28.6, TOP - 0.6, -math.cos(a) * 7, 0.35, P.steel)
	end
	-- jump pads: the ground to level 2 (S), level 2 to level 3 (WSW, ESE)
	for _, b in { 160, 200 } do
		local a = math.rad(b)
		K.jumpPad(K.facing(math.sin(a) * 13, -math.cos(a) * 13, math.sin(a), -math.cos(a)), Vector3.new(0, 60, 9))
	end
	for _, b in { 225, 135 } do -- (the middle of the SW and SE sides: clear of the columns)
		local a = math.rad(b)
		K.jumpPad(K.facing(math.sin(a) * 21, -math.cos(a) * 21, math.sin(a), -math.cos(a), Y2), Vector3.new(0, 60, 4.7))
	end

	-- ============================================================== THE GROUND RING: the spawn (S), the trophies
	local FS = sideF(180)
	cyl(FS, "Scenery", "SpawnRing", 0, -0.02, 0.06, -30, 12.4, P.creamHi)
	cyl(FS, "Scenery", "SpawnRug", 0, 0.06, 0.1, -30, 11.6, P.carpet2, MAT.Fabric)
	for i = 0, 7 do K.marker(FS, "HubSpawns", "Spawn", -3.6 + (i % 4) * 2.4, 0.1, -29 - math.floor(i / 4) * 2.4, 180) end
	K.marker(FS, "HubArrive", "Arrive", 0, 0.1, -24, 180)
	K.travelTerminal(at(180, -12, -35, 180))
	K.trophyCase(at(180, -6, -38.6, 180), 7)
	-- the zombies room behind the south wall, its door beside the spawn
	K.zombieRoom(sideF(180) * CFrame.new(11.5, 0, -RW), { x0 = -13.5, x1 = 4.5, d = 18, h = 11, door = 5, guideSide = -1 })
	-- the portals: the gym (SE), the armory (SW), their signs under level 2
	K.thinFrame(sideF(135), -12, 12, 10.4, -RW, "GYM", { signW = 10, signY = 12.4 })
	K.thinFrame(sideF(225), -7, 7, 10.4, -RW, "ARMORY  ·  TRAINING", { signW = 12, signY = 12.4 })

	-- ============================================================== LEVEL 2: the lounge
	local function L2(b, x, z, yaw) return at(b, x, z, yaw, Y2) end
	K.shop(L2(180, 0, -35.2, 180), 14)
	K.tableSpot(L2(225, 0, -30, 0), "board")
	K.arcadeSpot(L2(270, -4, -38.5, 180)); K.arcadeSpot(L2(270, 4, -38.5, 180)) -- (hub-minigames: a hair off the wall)
	local FCnw = L2(315, 0, -31, 180)
	K.cluster(FCnw, { npcSofa = true })
	K.codePanelSpot(L2(0, 0, -RW, 180))
	for _, s in { -1, 1 } do K.bench(L2(0, s * 10.5, -38.4, 180), 6, { back = true }) end
	K.bar(L2(45, 0, -36.8, 180), 12)
	K.tableSpot(L2(90, 0, -30, 0), "arm")
	for _, x in { -7, 0, 7 } do K.bench(L2(135, x, -36.2, 0), 4.4) end -- (looking into the gym)

	-- ============================================================== LEVEL 3: VIP, the ranked boards, loadout, bundles
	local function L3(b, x, z, yaw) return at(b, x, z, yaw, Y3) end
	K.vip(sideF(0) * CFrame.new(0, Y3, -RW), { w = 14, d = 22, h = 12, front = ww, frontH = TOP - Y3 })
	K.boardSpot(at(315, 0, -RW + 0.05, 180, Y3 + 6.2), "duels", 10, 7)
	K.boardSpot(at(45, 0, -RW + 0.05, 180, Y3 + 6.2), "party", 10, 7)
	K.holoLoadout(L3(270, 0, -33, 0))
	K.bundles(L3(90, 0, -33, 180))
	K.cluster(L3(180, 0, -32, 180))
	for _, b in { 225, 135 } do for _, s in { -1, 1 } do K.bench(L3(b, s * 7.5, -26.6, 180), 6) end end -- (looking down into the middle; the jump pads land between them)

	-- ============================================================== THE GYM (SE) and THE ARMORY (SW)
	local Fg = sideF(135) * CFrame.Angles(0, math.pi / 2, 0) -- (x out from the middle, z across)
	K.gym(Fg, { x0 = 42, x1 = 108, z0 = -34, z1 = 34, h = 25, rings = { { 57, -14 }, { 87, -14 }, { 57, 14 }, { 87, 14 } },
		locker = { x0 = 62, x1 = 100, z0 = 38, z1 = 60, door = { 78, 86 } } })
	for _, s in { -1, 1 } do box(Fg, "Shell", "GymFront", 40, 42, 0, 25, s * 17.4, s * 36, P.gymWall) end -- (the gym is wider than the octagon's side)
	K.armory(sideF(225), { d0 = 42, d1 = 82, w = 14, h = 14, door = "AtriumToTraining" })

	-- ============================================================== THE REGULARS
	-- Looticus: the shop (level 2 S), the NW sofa, behind the bar (NE)
	K.npc(FCnw, "Looticus", -1.6, 1.45, 3.5, 0)
	K.npcPoint(FCnw, "Looticus", 1, "spot", "sit", -1.6, 1.45, 3.5, 0)
	K.npcPoint(FCnw, "Looticus", 2, "spot", "sit", 1.6, 1.45, 3.5, 0)
	K.npcPoint(sideF(180), "Looticus", 3, "spot", "stand", 0, Y2, -37.6, 180)
	K.npcPoint(sideF(45), "Looticus", 4, "spot", "stand", 0, Y2, -38.25, 180)
	-- Frisk1636: along level 3 between the two boards
	local FR = { { 315, 0, -34, "stop" }, { 337.5, 0, -32.5, "via" }, { 0, 0, -30, "stop" }, { 22.5, 0, -32.5, "via" }, { 45, 0, -34, "stop" } }
	K.npc(sideF(315), "Frisk1636", 0, Y3, -34, 0)
	for i, w in FR do K.npcPoint(sideF(w[1]), "Frisk1636", i, w[4], "stand", w[2], Y3, w[3], 0, { pause = if w[4] == "stop" then { 8, 16 } else nil }) end
	-- Dune: round three sides of the gym's first ring
	local DU = { { "stop", 43.6, -14, -90 }, { "via", 43.6, -27.4, -90 }, { "stop", 57, -27.4, 180 }, { "via", 70.4, -27.4, 90 }, { "stop", 70.4, -14, 90 } }
	K.npc(Fg, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for i, w in DU do K.npcPoint(Fg, "Dune", i, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end
	return f
end

-- the check: walks (boxes that must be clear, in site frames) and leaks (points no ray may get out of)
function HA.walks(K)
	return {
		{ "the spawn to the island", sideF(180), -1.5, 1.5, -26, -10 }, { "the ground ring W", sideF(270), -6, 6, -22, -11 },
		{ "the ground ring N", sideF(0), -6, 6, -22, -11 }, { "the ground ring E", sideF(90), -6, 6, -22, -11 },
		{ "into the gym", sideF(135), -2.5, 2.5, -74, -12 }, { "into the armory", sideF(225), -2.5, 2.5, -60, -12 },
		{ "level 2 W", sideF(270), -6, 6, -24, -19.5, Y2 }, { "level 2 N", sideF(0), -6, 6, -24, -19.5, Y2 }, { "level 2 E", sideF(90), -6, 6, -24, -19.5, Y2 },
		{ "level 3 S", sideF(180), -6, 6, -29.4, -25.5, Y3 }, { "level 3 N", sideF(0), -6, 6, -29.4, -25.5, Y3 },
		{ "into the zombies room", sideF(180), 9.8, 13.2, -46, -34 },
	}
end
function HA.leaks()
	return { { CFrame.new(), 0, 8, 0 }, { CFrame.new(), 0, 36, 0 }, { sideF(180), 0, Y2 + 4, -30 }, { sideF(0), 0, Y3 + 4, -32 },
		{ sideF(135) * CFrame.Angles(0, math.pi / 2, 0), 75, 10, 0 }, { sideF(225), 0, 6, -60 }, { sideF(0), 0, Y3 + 5, -55 }, { sideF(180), 7, 6, -52 } }
end
HA.SHOTS = {
	{ "spawn", (sideF(180) * CFrame.new(0, 5.4, -35)).Position, Vector3.new(0, 11, 0) },
	{ "pads", Vector3.new(4, 6.5, 6), (sideF(315) * CFrame.new(0, 2, -32)).Position },
	{ "level 2", (sideF(180) * CFrame.new(-6, Y2 + 5.4, -30)).Position, (sideF(0) * CFrame.new(0, Y2 + 2, -30)).Position },
	{ "gym", (sideF(135) * CFrame.new(0, 6.5, -20)).Position, (sideF(135) * CFrame.new(0, 4, -80)).Position },
	{ "level 3 + VIP", (sideF(180) * CFrame.new(0, Y3 + 5.4, -30)).Position, (sideF(0) * CFrame.new(0, Y3 + 5, -40)).Position },
	{ "armory", (sideF(225) * CFrame.new(0, 6.5, -24)).Position, (sideF(225) * CFrame.new(0, 4, -82)).Position },
}
return HA
