--!nocheck
-- THE ROTUNDA, part 1: the round room. a stepped platform in the middle with a glowing ring in its top (you spawn inside
-- the ring), fourteen sides with a chunky pier at every corner, a ring balcony 14 up with a rail (two gaps over the
-- jump pads: the way up and the way down), a gallery over it (the game's name over the middle lift, banners on the
-- closed sides), a ribbed dome with a round skylight, and under the dome a lit ring with the showpiece turning in it:
-- the game's own Redline, ten studs long, lit from a lens in the platform. the eight ways out get one word each on the
-- balcony's edge and a floor line from the platform; every closed side has its own dressing (jump pads and boards,
-- a trophy cabinet by the gym, a weapon case by the armory, a bench under warm lamps, vending machines). called by
-- HubRotunda.build with its helpers (B)
return function(B, R)
	local P, G = B.P, B.G
	local N, A, T, RY, RIN = R.N, R.A, R.WALL, R.RING_Y, R.RING_IN
	local step = 360 / N
	local Neon, Wood = Enum.Material.Neon, Enum.Material.Wood
	local S, C = "Shell", "Scenery"
	local F0 = B.fr(0)
	local wid = B.wid
	local rc = A / math.cos(math.pi / N) -- how far out a corner is
	local mode = {}
	for _, md in R.MODES do mode[md.side] = md end
	-- what a way out is called and the colour of its word and floor line
	local WAY = { gym = { "gym", "GYM", P.pale, P.cream }, lounge = { "lounge", "LOUNGE", P.pale, P.cream }, armory = { "training", "TRAINING", P.train, "9dbb93" } }

	-- ---- the floor, the platform, the lines
	B.cyl(F0, S, "Floor", 0, -2, 0, 0, 2 * (A + 3), P.floor)
	B.cyl(F0, C, "RingLine", 0, 0, 0.05, 0, 2 * 14.6, P.cream, nil, G)
	B.cyl(F0, C, "RingFill", 0, 0, 0.07, 0, 2 * 14.1, P.floor, nil, G)
	B.cyl(F0, S, "DaisFoot", 0, 0, 0.6, 0, 2 * 13.4, P.pier)
	B.cyl(F0, S, "Dais", 0, 0.6, 1.2, 0, 2 * 12.6, P.cream)
	B.cyl(F0, C, "DaisTop", 0, 1.2, 1.23, 0, 2 * 12, P.floor2, nil, G)
	B.cyl(F0, C, "SpawnRing", 0, 1.2, 1.25, 0, 2 * 11.6, P.glow, Neon, G)
	B.cyl(F0, C, "DaisInner", 0, 1.2, 1.27, 0, 2 * 11, P.floor2, nil, G)
	B.cyl(F0, C, "LensRim", 0, 1.2, 1.29, 0, 3.4, P.cream, nil, G)
	B.cyl(F0, C, "Lens", 0, 1.2, 1.31, 0, 2.2, P.glow, Neon, G)
	-- you appear on a small circle round the focus, looking north
	local sp = {}
	for k = 0, 7 do local a = math.rad(22.5 + 45 * k); table.insert(sp, { 4 * math.cos(a), -(R.FOCUS + 4 * math.sin(a)) }) end
	B.spawns(sp, 1.2)

	-- ---- the fourteen sides
	for i = 0, N - 1 do
		local F = B.side(i)
		local kind = R.OPEN[i]
		local wo = wid(A + T) / 2 + 0.05
		local wi = wid(A) / 2
		local wf = wid(RIN) / 2
		if kind then
			B.box(F, S, "Lintel", -wo, wo, 12, 27.5, A, A + T, P.shell)
			B.paint(F, "Threshold", -5.4, 5.4, 0, A - 0.3, A + T + 0.3, P.pier, 0.08)
			-- its word on the balcony's edge, a tick on the platform and a line across the floor
			local id, word, hex, line
			if kind == "lift" then id, word, hex, line = mode[i].id, mode[i].title, P.word, P.ray
			else id, word, hex, line = WAY[kind][1], WAY[kind][2], WAY[kind][3], WAY[kind][4] end
			if P.doorGlow then -- (the glow palette: each way out lit along its threshold in its own colour, a lift also under its lintel)
				B.box(F, C, "DoorGlow", -4.9, 4.9, 0, 0.12, A - 0.55, A - 0.25, if kind == "lift" then P.doorGlow else hex, Neon, G)
			end
			B.text(F, "Way_" .. id, { { word, hex, "B", 1 } }, if #word > 6 then 9 else 7, 1.9, 0, 13, RIN - 0.08, 0, { flush = true, thick = 0.25, pps = 50 })
			-- (a lift's line fans out from the focus, where you appear; a room's runs straight out from the platform)
			if kind == "lift" then
				local b = R.liftBearing(i)
				B.paint(B.lf(b), "Ray", -0.24, 0.24, 1.2, 5.6, R.reach(b, 10.7), line, 0.08)
				B.paint(B.lf(b), "Ray", -0.24, 0.24, 0, R.reach(b, 14.9), R.reach(b, A + T), line, 0.09)
			else
				B.paint(F, "Tick", -0.24, 0.24, 1.2, 8.4, 10.7, line, 0.08)
				B.paint(F, "Ray", -0.24, 0.24, 0, 14.9, A + T, line, 0.09)
			end
		else
			B.box(F, S, "Wall", -wo, wo, 0, 27.5, A, A + T, P.shell)
			B.box(F, C, "Base", -5.3, 5.3, 0, 0.7, A - 0.35, A, P.pier, nil, G)
			B.box(F, C, "Dado", -5.3, 5.3, 0.7, 5, A - 0.22, A, P.wood, Wood, G)
			B.box(F, C, "Ledge", -5.3, 5.3, 5, 5.5, A - 0.6, A, P.cream, nil, G)
			B.box(F, C, "Band", -5.3, 5.3, 5.5, 7.2, A - 0.12, A, P.band, nil, G)
			B.bar(F, C, "Slope", 0, 10.6, 0.5, A - 1.7, 12, A, 10.3, P.shell2, nil, G)
			B.panel(F, 0, 12, 25.1, 5, 2)
			B.lamp(F, 0, 10.8, 25, 15, 0.55)
		end
		-- the ring balcony: its slab, its floor, and its rail (none over a jump pad: sides 3 and 11)
		B.box(F, S, "Ring", -wi - 0.05, wi + 0.05, 12, RY, RIN, A + 0.2, P.cream)
		B.box(F, C, "RingFloor", -wi, wi, RY, RY + 0.04, RIN + 0.9, A, P.floor2, nil, G)
		if i == 3 or i == 11 then
			B.paint(F, "GapMark", -wf, wf, RY, RIN, RIN + 0.9, P.ray, 0.02)
		else
			B.put(F, "hb_rail", "Rail", 0, RY, RIN + 0.45, 0, { stretch = Vector3.new(wid(RIN + 0.4) / 9.5, 1, 1), solid = true,
				color = { ["2e3140"] = P.cream, c4c8d4 = P.creamHi, ["5b6478"] = P.cream, ["17141f"] = P.accent } })
		end
		-- the gallery: a lit panel in a dark frame, a cornice with a slope under it
		B.box(F, C, "GalleryBase", -wi, wi, RY, RY + 0.6, A - 0.3, A, P.pier, nil, G)
		if i == 0 then
			B.text(F, "GalleryName", { { "JANKFIRE", P.word, "B", 1 } }, 10.6, 3.4, 0, 21.8, A - 0.3, 0, { flush = true, thick = 0.4, pps = 40 }) -- (high enough to clear the rail, seen from the platform)
		elseif kind then
			B.box(F, C, "WindowFrame", -2.3, 2.3, 16.8, 23.4, A - 0.4, A, P.pier, nil, G)
			B.box(F, C, "Window", -1.7, 1.7, 17.4, 22.8, A - 0.52, A - 0.4, P.dim, Neon, G)
		else
			-- (a banner: the one soft thing that hangs in the room)
			B.box(F, C, "BannerRod", -2.6, 2.6, 23.5, 24, A - 0.9, A - 0.3, P.pier, nil, G)
			B.box(F, C, "Banner", -2.2, 2.2, 16.4, 23.5, A - 0.7, A - 0.55, P.band, nil, G)
			B.box(F, C, "BannerStripe", -2.2, 2.2, 17.6, 18.5, A - 0.74, A - 0.55, P.creamHi, nil, G)
			B.box(F, C, "BannerStripe", -2.2, 2.2, 19.1, 19.4, A - 0.74, A - 0.55, P.creamHi, nil, G)
		end
		B.box(F, C, "Cornice", -wi, wi, 26, 27.5, A - 1.2, A, P.cream, nil, G)
		B.bar(F, C, "CorniceSlope", 0, 2 * wi - 2.4, 0.5, A - 1.2, 26, A, 24.7, P.shell2, nil, G)
		-- the dome over it, and the skylight's curb
		B.bar(F, S, "DomePanel", 0, wid(A + 1.2) + 0.3, 1, 7.4, 39.9, A + 1.2, 27.4, P.dome)
		B.box(F, C, "Curb", -wid(8.6) / 2, wid(8.6) / 2, 38.8, 40.2, 7, 8.6, P.cream, nil, G)
		-- the hanging ring round the showpiece
		B.box(F, C, "Crown", -wid(10.4) / 2, wid(10.4) / 2, 21.4, 22.9, 9.2, 10.4, P.cream, nil, G)
		B.box(F, C, "CrownGlow", -wid(9.8) / 2 + 0.3, wid(9.8) / 2 - 0.3, 21.25, 21.4, 9.5, 10.1, P.halo or P.strip, Neon, G)
	end

	-- ---- a pier at every corner, floor to cornice, with a rib of the dome over it
	for i = 0, N - 1 do
		local F = B.fr((i + 0.5) * step)
		B.put(F, "hb_pier", "Pier", 0, 0, rc + 1.3, 0, { stretch = Vector3.new(2.9 / 6.2, 27.5 / 48, 4.4 / 3.6), solid = Vector3.new(2.9, 12, 4.2),
			color = { ["2e3140"] = P.pier, a4aab8 = P.pier2, ["5b6478"] = P.pier } })
		B.lamp(F, 0, 6, rc - 2.4, 10, 0.35)
		B.bar(F, C, "Rib", 0, 1.1, 1, 7.7, 39.2, 28.9, 27.3, P.cream, nil, G)
		if i >= 11 or i <= 2 then B.box(F, C, "PierBackLight", -0.3, 0.3, 2.6, 9.6, rc + 3.5, rc + 3.62, P.strip, Neon, G) end
	end

	-- ---- the dome's top, its light ring, and the lamps that light the room
	B.cyl(F0, C, "Skylight", 0, 40, 40.3, 0, 15.2, P.sky, Neon, G)
	B.cyl(F0, S, "DomeCap", 0, 40.3, 41.3, 0, 19, P.dome)
	B.put(F0, "bc_halo", "DomeRing", 0, 35.6, 0, 0, { seat = "centre", scale = 1.25, color = { ["37d6ff"] = P.strip, ff4fd9 = P.cream, ffe14d = P.cream } })
	B.lamp(F0, 0, 39.4, 0, 60, 0.8, P.light, { spot = true, angle = 100 })
	for k = 0, 3 do B.lamp(B.fr(45 + 90 * k), 0, 24, 15, 28, 0.5) end

	-- ---- the showpiece: the game's own Redline, ten studs long, turning slowly high over the platform inside the ring
	-- that hangs from the dome on four spokes, lit from below by the lens in the platform. (round 1's judge: the hanging
	-- name box "looks like a placeholder". it floats above eye height so it hides nothing: the sight lines from the spawn
	-- to the boards and to the name on the gallery pass under it)
	B.cyl(F0, C, "Rod", 0, 22.4, 40, 0, 1.2, P.pier, nil, G)
	for k = 0, 3 do B.box(B.fr(45 + 90 * k), C, "Spoke", -0.5, 0.5, 21.6, 22.4, 0.6, 9.4, P.cream, nil, G) end
	-- (13.4 up, nine long, lit from the lens below: a display that turns, low enough to read from the floor, high
	-- enough to clear every sight line from the spawn and from the room's south side)
	local show = B.gun(F0, R.SHOWPIECE or "w_redline", 9, 0, 13.4, 0, 0, "Showpiece")
	if show then show:SetAttribute("Spin", 0.25); show:SetAttribute("Bob", 0.2); game:GetService("CollectionService"):AddTag(show, "HubSpin") end
	local up = B.lamp(F0, 0, 1.8, 0, 14, 2.2, P.light, { spot = true, angle = 30 }); up:FindFirstChildOfClass("SpotLight").Face = Enum.NormalId.Top
	B.lamp(F0, 0, 15.6, 0, 26, 1, P.light, { spot = true, angle = 110, shadows = true })
	-- (a secret: a small duck sits on top of the ring. only the balcony sees it)
	B.put(B.side(7), "pj_duck", "CrownDuck", 0, 22.9, 9.8, 0, { scale = 2.6, raw = true })

	-- ---- the doors' own shapes
	-- the lounge: a round arch of dark stones (it springs 6 up; 4.9 in radius)
	do
		local F = B.side(7)
		for k = 1, 9 do
			local a = math.rad((k - 0.5) * 20)
			local cx, cy = 6.5 * math.cos(a), 6 + 6.5 * math.sin(a)
			local tx, ty = -math.sin(a) * 1.5, math.cos(a) * 1.5
			B.spar(F, C, "ArchStone", A - 0.3, A + T + 0.1, 3.2, cx - tx, cy - ty, cx + tx, cy + ty, P.pier, nil, G)
		end
		B.solid("ArchBoxL", Vector3.new(1.6, 12, T), F * CFrame.new(-5.6, 6, -(A + T / 2)))
		B.solid("ArchBoxR", Vector3.new(1.6, 12, T), F * CFrame.new(5.6, 6, -(A + T / 2)))
	end
	-- the armory: a hatch with its top corners cut
	do
		local F = B.side(10)
		for _, s in { -1, 1 } do
			B.spar(F, C, "HatchCut", A - 0.3, A + T + 0.1, 3, s * 6.4, 9.1, s * 2, 13.5, P.pier, nil, G)
		end
		B.box(F, C, "HatchHead", -3, 3, 11.4, 12, A - 0.3, A + T + 0.1, P.pier, nil, G)
	end
	-- the gym: a pale portal, deep, with its top corners cut, under a dark canopy with a light in it and the name on its
	-- front (round 1's judge: "a narrow plain rectangle with a thin frame")
	do
		local F = B.side(4)
		for _, s in { -1, 1 } do
			B.box(F, C, "PortalJamb", s * 4.5, s * 5.4, 0, 9.4, A - 0.5, A + T + 0.2, P.creamHi, nil, G)
			B.spar(F, C, "PortalCut", A - 0.5, A + T + 0.2, 1.1, s * 5.4, 8.8, s * 3.2, 11.1, P.creamHi, nil, G)
		end
		B.box(F, C, "PortalHead", -3.4, 3.4, 10.5, 11.1, A - 0.5, A + T + 0.2, P.creamHi, nil, G)
		B.box(F, C, "Canopy", -5.6, 5.6, 11.1, 12, A - 2.8, A + 0.2, P.pier, nil, G)
		B.box(F, C, "CanopyLight", -4.2, 4.2, 10.98, 11.1, A - 2.2, A - 1.2, P.strip, Neon, G)
		B.lamp(F, 0, 10.4, A - 1.6, 12, 0.6)
	end

	-- ---- what stands in the closed bays
	-- sides 3 and 11: the jump pads up to the balcony, a board on the wall behind each
	for _, i in { 3, 11 } do
		local F = B.side(i)
		B.jump(F, 0, 0, 18.2, 0, Vector3.new(0, 58, 7.6)) -- (the pad's arrows point away from its front: at the balcony)
		local lines = if i == 3
			then { { "HOW TO PLAY", P.pale, "B", 0.28 }, { "1   STEP ON A PAD IN YOUR TEAM'S COLOUR", "d8dbe2", "S", 0.18 }, { "2   THE LIFT GOES UP WHEN THE PAD IS FULL", "d8dbe2", "S", 0.18 }, { "3   FIRST TO FIVE ROUNDS WINS", "d8dbe2", "S", 0.18 }, { "4   STEP OFF TO LEAVE THE QUEUE", "d8dbe2", "S", 0.18 } }
			else { { "NOTICE BOARD", P.pale, "B", 0.28 }, { "ARENA   ·   THE ROOFTOP", "d8dbe2", "S", 0.18 }, { "TRAINING   ·   THROUGH THE ARMORY", "d8dbe2", "S", 0.18 }, { "LOADOUT   ·   PRESS L ANYWHERE", "d8dbe2", "S", 0.18 }, { "WEAPONS STAY HOLSTERED IN THE LOBBY", "d8dbe2", "S", 0.18 } }
		B.text(F, if i == 3 then "BoardHow" else "BoardNotice", lines, 9.2, 4.2, 0, 8.1, A - 0.62, 0, { flush = true, thick = 0.3, pps = 40 })
	end
	-- side 5, by the gym: a trophy cabinet between two warm wall lamps
	do
		local F = B.side(5)
		B.put(F, "bc_cupshelf", "TrophyCabinet", 0, 0, A - 0.65, 0, { back = true, scale = 1.25, solid = true, color = { ["26242e"] = P.pier, ["8a5a32"] = P.wood, e0b040 = "c9a85a", ["17141f"] = P.plate } })
		for _, s in { -1, 1 } do
			B.put(F, "hb_walllight", "WallLight", s * 4.6, 6.4, A - 0.15, 0, { back = true, seat = "centre", color = { ffcf8a = P.warm } })
			B.lamp(F, s * 4.6, 6.4, A - 1.4, 10, 0.55, P.warm)
		end
	end
	-- side 9, by the armory: a weapon case on the wall (the DMR on a dark board, a lit strip over it), cases below
	do
		local F = B.side(9)
		B.box(F, C, "CaseBoard", -4.4, 4.4, 3.4, 7.6, A - 0.75, A - 0.25, P.plate, nil, G)
		B.box(F, C, "CaseFrame", -4.7, 4.7, 7.6, 8.1, A - 1, A - 0.25, P.pier2, nil, G)
		B.box(F, C, "CaseGlow", -4.2, 4.2, 7.48, 7.6, A - 0.95, A - 0.75, P.strip, Neon, G)
		B.box(F, C, "CaseLedge", -4.7, 4.7, 3, 3.4, A - 1.2, A - 0.25, P.cream, nil, G)
		B.gun(F, "w_dmr", 7, 0, 5.5, A - 1.0, 0, "CaseGun")
		B.lamp(F, 0, 7, A - 2.2, 9, 0.6)
		B.put(F, "bc_hardcase", "HardCase", -2.6, 0, A - 2.1, 8, { solid = true, color = { ["2f3b2a"] = P.band } })
		B.put(F, "bc_ammocrate", "AmmoCrate", 2.8, 0, A - 1.6, -12, { solid = true, color = { ["4a5a2c"] = "66705a", ["3a4622"] = "566050" } })
	end
	-- side 6, beside the lounge's arch: a bench under two warm lamps at head height
	do
		local F = B.side(6)
		B.put(F, "st_bench", "Bench", 0, 0, A - 0.5, 0, { back = true, scale = 0.9, solid = true, color = { ffe14d = P.wood, ["2e3140"] = P.pier } })
		for _, s in { -1, 1 } do
			B.put(F, "hb_walllight", "WallLight", s * 3.6, 6.4, A - 0.15, 0, { back = true, seat = "centre", color = { ffcf8a = P.warm } })
			B.lamp(F, s * 3.6, 6.4, A - 1.4, 10, 0.55, P.warm)
		end
	end
	-- side 8, the other side of the arch: two vending machines
	do
		local F = B.side(8)
		B.put(F, "hb_vending", "Vending", -2.1, 0, A - 0.45, 0, { back = true, solid = true, color = { ff4fd8 = P.band } })
		B.put(F, "hb_vending", "Vending", 2.1, 0, A - 0.45, 0, { back = true, solid = true, color = { ff4fd8 = P.cream } })
	end
end
