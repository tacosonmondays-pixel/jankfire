--!nocheck
-- THE ROTUNDA, part 3: the three rooms off the round room, each down a short hall that frames it.
--   the lounge   (south, behind the spawn, on the axis) small, low and warm: brick, timber beams, seats on a raised
--                wooden border round a sunk middle, and the hologram duck turning over its projector
--   the duels    (east) the gym's boxing ring, bigger, in the middle of a hall of seven more pads (R.HALL)
--   the armory   (west, on the spawn's left) cut corners; the game's own weapons on boards down both walls, and at
--                the far end of its aisle the red gate to the training ground
-- called by HubRotunda.build with its helpers (B)
return function(B, R)
	local P, G = B.P, B.G
	local A, T = R.A, R.WALL
	local Neon, Wood, Brick = Enum.Material.Neon, Enum.Material.Wood, Enum.Material.Brick
	local S, C = "Shell", "Scenery"
	local Tags = game:GetService("CollectionService")
	local D0 = A + T
	local GREEN = { ["4f9a3a"] = "5f8a58", ["6bc24a"] = "7da06c", ["3f6b2a"] = "4f7550", ["4a3424"] = "6a5a4a", eeeef2 = P.cream }

	-- a hall from the round room's wall to a room: floor, two walls, a lid. hw = half its width, h = its height
	local function hall(F, name, d1, hw, h, wall, floor, lid, wallMat, floorMat, lidMat)
		B.box(F, S, name .. "HallFloor", -hw - 3.2, hw + 3.2, -2, -0.05, A + 1.5, d1 - 2, floor, floorMat) -- (under the round floor's top: no shared plane)
		for _, s in { -1, 1 } do B.box(F, S, name .. "HallWall", s * hw, s * (hw + 3.2), 0, h + 1, D0 - 0.2, d1 - 0.1, wall, wallMat) end
		B.box(F, S, name .. "HallLid", -hw - 3.15, hw + 3.15, h, 12.6, D0 - 0.15, d1 - 2, lid, lidMat) -- (meets the room's wall instead of running into it; inside the walls' sides)
	end
	-- a room: floor, lid, four walls, the near wall left open for its hall (hw wide, hh high)
	local function room(F, name, x0, x1, d0, d1, h, hw, hh, wall, floor, lid, wallMat, floorMat)
		B.box(F, S, name .. "Floor", x0 - 2, x1 + 2, -2, -0.02, d0 - 2, d1 + 2, floor, floorMat)
		B.box(F, S, name .. "Lid", x0 - 2, x1 + 2, h, h + 1, d0 - 2, d1 + 2, lid)
		B.box(F, S, name .. "Wall", x0 - 2, x1 + 2, 0, h, d1, d1 + 2, wall, wallMat)
		B.box(F, S, name .. "Wall", x0 - 2, x0, 0, h, d0 - 2, d1, wall, wallMat)
		B.box(F, S, name .. "Wall", x1, x1 + 2, 0, h, d0 - 2, d1, wall, wallMat)
		B.box(F, S, name .. "Wall", x0, -hw, 0, h, d0 - 2, d0, wall, wallMat)
		B.box(F, S, name .. "Wall", hw, x1, 0, h, d0 - 2, d0, wall, wallMat)
		if hh < h then B.box(F, S, name .. "Wall", -hw, hw, hh, h, d0 - 2, d0, wall, wallMat) end
	end
	-- a corner cut at 45 degrees where a side wall meets the lid, running d0..d1 (s = which wall)
	local function cut(F, name, s, x, y, d0, d1, size, hex, mat)
		local c = size * 0.5
		B.box(F, C, name, s * (x - c) - size * 0.71, s * (x - c) + size * 0.71, y - c - 0.3, y - c + 0.3, d0, d1, hex, mat, { ghost = true, rot = CFrame.Angles(0, 0, -s * math.pi / 4) })
	end

	-- ------------------------------------------------------------ the lounge (side 7, due south)
	do
		local F = B.side(7)
		hall(F, "Lounge", 38, 5, 10.4, P.brick, P.wood, P.beam, Brick, Wood, Wood)
		room(F, "Lounge", -14, 14, 38, 60, 11, 5, 10.4, P.brick, P.carpet, P.shell2, Brick)
		B.lamp(F, 0, 9.2, 34.5, 12, 0.8, P.warm)
		-- the raised wooden border the seats stand on, with a dark nosing; the middle stays sunk
		local function step(x0, x1, d0, d1) B.box(F, S, "LoungeStep", x0, x1, -0.02, 0.6, d0, d1, P.wood, Wood) end
		step(-14, -8, 41, 60); step(8, 14, 41, 60); step(-8, 8, 54, 60)
		for _, s in { -1, 1 } do B.paint(F, "StepNose", s * 8, s * 8.5, 0.6, 41, 54, P.pier, 0.01) end
		B.paint(F, "StepNose", -8.5, 8.5, 0.6, 54, 54.5, P.pier, 0.01)
		-- timber beams across, a dark pier under each end, the corners of the room cut
		for _, d in { 43, 49, 55 } do
			B.box(F, C, "Beam", -14, 14, 9.9, 11, d - 0.6, d + 0.6, P.beam, Wood, G)
			for _, s in { -1, 1 } do B.box(F, C, "LoungePier", s * 13.3, s * 14, 0.6, 9.9, d - 0.7, d + 0.7, P.pier, nil, G) end
		end
		for _, k in { { -1, 58.2 }, { 1, 58.2 }, { -1, 39.8 }, { 1, 39.8 } } do
			local turn = (if k[2] > 50 then -1 else 1) * k[1] * math.pi / 4
			B.box(F, S, "LoungeCut", k[1] * 12.2 - 2.8, k[1] * 12.2 + 2.8, 0, 11, k[2] - 0.6, k[2] + 0.6, P.brick, Brick, { rot = CFrame.Angles(0, turn, 0) })
		end
		-- a wood rail and a pale ledge behind the seats
		for _, s in { -1, 1 } do
			B.box(F, C, "LoungeDado", s * 13.8, s * 14, 0.6, 3.6, 43.7, 54.3, P.wood, Wood, G)
			B.box(F, C, "LoungeLedge", s * 13.5, s * 14, 3.6, 3.95, 43.7, 54.3, P.creamHi, nil, G)
		end
		-- the duck: a projector on a round rug in the sunk middle, a faint beam, the duck turning in it
		B.cyl(F, C, "Rug", 0, -0.02, 0.03, 46.5, 12.4, P.creamHi, nil, G)
		B.cyl(F, C, "Rug", 0, -0.06, 0.07, 46.5, 11.4, P.band, nil, G)
		B.put(F, "bc_holoprojector", "HoloProjector", 0, 0, 46.5, 0, { solid = true, color = { ["37d6ff"] = "ffe9a8", ["8fe6ff"] = "ffe9a8" } })
		local duck = B.put(F, "pj_duck", "HoloDuck", 0, 4.2, 46.5, 0, { scale = 6, raw = true })
		if duck then
			for _, p in duck:GetDescendants() do
				if p:IsA("BasePart") then p.Material = Neon; p.Color = Color3.fromHex("ffd84a"); p.Transparency = 0.12; p.CastShadow = false; p.CanCollide = false; p.CanQuery = false end
			end
			duck:SetAttribute("Spin", 0.6); duck:SetAttribute("Bob", 0.25); Tags:AddTag(duck, "HubSpin")
		end
		B.lamp(F, 0, 5.6, 46.5, 13, 1, "ffe08a")
		-- seats: a sofa each side, an armchair beyond it, two armchairs at the back facing the door
		local seat = { ["3b2a52"] = P.creamHi, ff4fd8 = P.band }
		for _, s in { -1, 1 } do
			B.put(F, "bc_sofa", "Sofa", s * 13.4, 0.6, 48, -s * 90, { back = true, scale = 1.1, solid = true, color = seat })
			B.put(F, "bc_armchair", "Armchair", s * 4.7, 0.6, 59.2, 0, { back = true, scale = 1.1, solid = true, color = seat })
			B.put(F, "hb_droplight", "DropLight", s * 10.6, 11, 48, 0, { seat = "top", scale = 0.7, color = { fff1d6 = P.warm } })
			B.lamp(F, s * 10.6, 6.4, 48, 15, 0.9, P.warm, { shadows = s > 0 })
			B.put(F, "hb_walllight", "WallLight", s * 8, 6.4, 59.95, 0, { back = true, seat = "centre" })
			B.put(F, R.prop("rk_planter", "bc_plantbig"), "Planter", s * 11.4, 0.6, 42.6, 0, { scale = R.propScale("rk_planter", 0.85, 0.5), solid = true, color = GREEN })
		end
		B.lamp(F, 0, 6.4, 58.6, 13, 0.7, P.warm)
		B.put(F, R.prop("rk_coffeetable", "bc_coffeetable"), "CoffeeTable", 0, 0.6, 58.6, 0, { solid = true })
		B.put(F, "bc_arcade", "Arcade", 10.6, 0.6, 56.6, -45, { solid = true, color = { ff4fd8 = P.pier2, ffe14d = P.band, ["120818"] = P.pier } })
		B.put(F, "bc_fridge", "Fridge", -10.6, 0.6, 56.6, 45, { solid = true })
		B.text(F, "LoungeRule", { { "WEAPONS HOLSTERED", P.pale, "B", 0.56 }, { "the lounge is neutral ground", "d8dbe2", "S", 0.4 } }, 7.4, 1.5, 0, 8.2, 59.9, 0, { flush = true })
	end

	-- ------------------------------------------------------------ the duel hall (side 4, east): the ring and seven more pads
	-- (owner, 16 Nov: "we also need more pads somewhere?", and of the gym's ring: "is that intended what should we do?
	-- maybe make it a bit bigger". so the gym became the hall where most matches start, with its boxing ring kept as the
	-- centrepiece, bigger and on the door's axis: through the door you see the ring under its light frame, the 3v3
	-- straight ahead beyond it with the round target over its board, a 1v1 either side of it. R.HALL's pads stand round
	-- the walls facing the ring (a 2v2 on each side wall, a 1v1 either side of the door), each with its board on the wall
	-- behind it and a light panel over it, piers between them. 50 wide and 52 deep: its north wall is still about 5 clear
	-- of the lift ring's end wall. no floor lines: the pads and their boards read on their own)
	do
		local F = B.side(4)
		local X0, X1, D1, H = R.HALL_BOX[1], R.HALL_BOX[2], R.HALL_BOX[3], R.HALL_BOX[4]
		hall(F, "Duels", 40, 5, 11, P.shell2, P.floor, P.shell)
		for _, d in { 33.4, 37.8 } do -- two pale frames across the hall
			for _, s in { -1, 1 } do B.box(F, C, "HallFrame", s * 4.55, s * 5, 0, 11, d - 0.5, d + 0.5, P.cream, nil, G) end
			B.box(F, C, "HallFrame", -5, 5, 10.3, 11, d - 0.5, d + 0.5, P.cream, nil, G)
		end
		B.panel(F, 0, 11, 35.6, 2.4, 2.6)
		B.lamp(F, 0, 9.6, 35.6, 13, 0.7)
		room(F, "Duels", X0, X1, 40, D1, H, 5, 11, P.gymWall, P.gymFloor, P.shell2)
		-- the walls: a dark base, a pale band at shoulder height, the long walls' tops cut, two girders across
		for _, w in { { X0, X0 + 0.25, 40, D1 }, { X1 - 0.25, X1, 40, D1 }, { X0 + 0.25, X1 - 0.25, D1 - 0.25, D1 }, { X0 + 0.25, -5, 40, 40.25 }, { 5, X1 - 0.25, 40, 40.25 } } do
			B.box(F, C, "DuelsBase", w[1], w[2], 0, 0.8, w[3], w[4], P.pier, nil, G)
			B.box(F, C, "DuelsBand", w[1], w[2], 9.4, 9.9, w[3], w[4], P.cream, nil, G)
		end
		cut(F, "DuelsCut", -1, -X0, H, 40, D1, 3, P.shell2); cut(F, "DuelsCut", 1, X1, H, 40, D1, 3, P.shell2)
		for _, d in { 51.5, 77 } do B.box(F, C, "Girder", X0, X1, H - 1.6, H, d - 0.7, d + 0.7, P.cream, nil, G) end

		-- the ring, 20 across (the gym's was 17), its middle on the door's axis: a padded platform, four fat posts, two fat
		-- rounded rails each side, two steps up on the door's side, a square light frame over it, a lamp at each corner
		-- and the hall's one shadowed light straight over its middle
		local RD, RS, RH = R.HALL_RING, 10, 1.4
		local PO = RS - 0.7 -- (the posts' middles)
		B.box(F, S, "RingBase", -RS, RS, 0, RH, RD - RS, RD + RS, P.pier2)
		B.box(F, C, "RingApron", -RS - 0.1, RS + 0.1, RH - 0.4, RH - 0.04, RD - RS - 0.1, RD + RS + 0.1, P.creamHi, nil, G) -- (its top under the base's)
		B.box(F, C, "RingMat", -RS + 1, RS - 1, RH, RH + 0.08, RD - RS + 1, RD + RS - 1, P.band, nil, G)
		B.box(F, C, "RingMatLine", -RS + 1, RS - 1, RH + 0.08, RH + 0.1, RD - 0.25, RD + 0.25, P.creamHi, nil, G)
		B.box(F, S, "RingStep", -2.2, 2.2, 0, RH / 2, RD - RS - 1.2, RD - RS, P.pier2)
		B.box(F, S, "RingStep", -2.2, 2.2, RH / 2, RH, RD - RS - 0.6, RD - RS, P.pier2)
		for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
			B.cyl(F, C, "RingPost", cx * PO, RH, RH + 5, RD + cz * PO, 1.6, P.cream, nil, G)
			B.cyl(F, C, "RingPostCap", cx * PO, RH + 5, RH + 5.5, RD + cz * PO, 2, P.band, nil, G)
		end end
		for _, h in { RH + 2.1, RH + 3.9 } do
			for _, sd in { { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } } do
				local len = 2 * PO - 1.6
				local rail = B.box(F, C, "RingRail", 0, len, h - 0.42, h + 0.42, 0, 0.84, P.creamHi, nil, G)
				rail.Shape = Enum.PartType.Cylinder; rail.Size = Vector3.new(len, 0.84, 0.84)
				rail.CFrame = F * CFrame.new(sd[1] * PO, h, -(RD + sd[2] * PO)) * (if sd[1] ~= 0 then CFrame.Angles(0, math.pi / 2, 0) else CFrame.identity)
			end
		end
		B.lamp(F, 0, H - 1.6, RD, 36, 1.5, P.light, { spot = true, angle = 75, shadows = true })
		local LF, LY = 7.6, H - 4.4
		for _, s in { -1, 1 } do
			B.box(F, C, "LightFrame", -LF - 0.3, LF + 0.3, LY, LY + 0.6, RD + s * LF - 0.3, RD + s * LF + 0.3, P.pier, nil, G)
			B.box(F, C, "LightFrame", s * LF - 0.3, s * LF + 0.3, LY + 0.03, LY + 0.6, RD - LF - 0.3, RD + LF + 0.3, P.pier, nil, G)
		end
		for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
			B.box(F, C, "FrameRod", cx * LF - 0.3, cx * LF + 0.3, LY + 0.6, H, RD + cz * LF - 0.3, RD + cz * LF + 0.3, P.pier, nil, G)
			-- (the lamps at the frame's corners, off the door's axis: the view to the target runs between them)
			B.put(F, "hb_droplight", "RingLamp", cx * 5.2, LY, RD + cz * 5.2, 0, { seat = "top", scale = 0.8, color = { fff1d6 = P.warm } })
			B.lamp(F, cx * 5.2, LY - 3, RD + cz * 5.2, 16, 0.7, P.warm)
		end end

		-- the far wall, on the door's axis: a lit recess with the round target in it, over the 3v3's board
		local TY = 13.5
		B.box(F, C, "RecessBack", -5.6, 5.6, 9.8, 17.4, D1 - 0.65, D1 - 0.35, P.band, nil, G)
		for _, s in { -1, 1 } do B.box(F, C, "RecessSide", s * 5.6, s * 6.6, 9.8, 17.4, D1 - 2, D1 - 0.3, P.pier, nil, G) end
		B.box(F, C, "RecessHead", -6.6, 6.6, 17.4, 18, D1 - 2, D1 - 0.3, P.pier, nil, G)
		B.box(F, C, "RecessSill", -6.6, 6.6, 9.4, 9.8, D1 - 2, D1 - 0.3, P.pier, nil, G)
		for i, k in ipairs({ { 7, P.creamHi }, { 5.6, P.pier }, { 4.2, P.creamHi }, { 2.8, P.pier }, { 1.5, P.glow } }) do
			local disc = B.cyl(F, C, "Target", 0, 0, 0.12, 0, k[1], k[2], if i == 5 then Neon else nil, G)
			disc.CFrame = F * CFrame.new(0, TY, -(D1 - 0.75 - i * 0.1)) * CFrame.Angles(0, math.pi / 2, 0)
		end
		for _, s in { -1, 1 } do B.box(F, C, "TargetTick", s * 4.4 - 0.55, s * 4.4 + 0.55, TY - 0.3, TY + 0.3, D1 - 1.05, D1 - 0.65, P.creamHi, nil, G) end -- (two ticks, like sights)
		B.lamp(F, 0, H - 1.2, D1 - 7, 18, 1.2, P.warm, { spot = true, angle = 60, face = Enum.NormalId.Front })

		-- the pads: one frame per wall, its -Z out through the wall, x along the wall
		local walls = {
			far = function(at) return F * CFrame.new(at, 0, -D1) end,
			near = function(at) return F * CFrame.new(at, 0, -40) * CFrame.Angles(0, math.pi, 0) end,
			left = function(at) return F * CFrame.new(X0, 0, -at) * CFrame.Angles(0, math.pi / 2, 0) end,
			right = function(at) return F * CFrame.new(X1, 0, -at) * CFrame.Angles(0, -math.pi / 2, 0) end,
		}
		for _, e in R.HALL do
			local md = table.clone(R.MODES[e.mode])
			md.name, md.bank = e.name, "hall"
			md.w, md.dp = R.HALL_SIZE[md.id][1], R.HALL_SIZE[md.id][2]
			local W = walls[e.wall](e.at)
			local pad = B.pad(W, md, 0, 0, -(1.2 + md.dp / 2))
			local bw = md.w - 1.4
			B.board(pad, W, md, bw, bw / 2, 0, 5.4, -0.45, 0, { thick = 0.4 })
			B.box(W, C, "BoardFrame", -bw / 2 - 0.35, bw / 2 + 0.35, 5.4 - bw / 4 - 0.35, 5.4 + bw / 4 + 0.35, -0.25, 0, P.pier2, nil, G)
			B.panel(W, 0, H, -(1.2 + md.dp / 2), 3, 3)
			B.lamp(W, 0, H - 1.2, -(1.2 + md.dp / 2), 22, 0.9, P.light, { spot = true, angle = 90 })
		end
		-- piers between the pads, floor to the lid's cut
		local function pier(W, at) B.box(W, S, "DuelsPier", at - 0.7, at + 0.7, 0, H - 2.2, -1.4, 0, P.pier) end
		for _, at in { -8.6, 8.6 } do pier(walls.far(0), at) end
		for _, at in { 55.5, 72.5 } do pier(walls.left(0), at); pier(walls.right(0), -at) end
		for _, at in { -6.8, 6.8 } do pier(walls.near(0), at) end
	end

	-- ------------------------------------------------------------ the armory and the training gate (side 10, west)
	do
		local F = B.side(10)
		hall(F, "Armory", 38, 5, 11, P.shell, P.floor, P.shell2)
		for _, s in { -1, 1 } do cut(F, "HallCut", s, 5, 11, D0, 38, 2.4, P.pier) end
		B.panel(F, 0, 11, 34.6, 2.4, 4); B.lamp(F, 0, 10, 34.6, 13, 0.7)
		room(F, "Armory", -13, 13, 38, 64, 12, 5, 11, P.shell, P.floor2, P.shell2)
		for _, s in { -1, 1 } do
			cut(F, "ArmoryCut", s, 13, 12, 38, 64, 3.4, P.pier)
			B.box(F, C, "ArmoryBase", s * 12.7, s * 13, 0, 0.8, 38, 64, P.pier, nil, G)
		end
		for _, d in { 45, 56 } do B.panel(F, 0, 12, d, 1.8, 6); B.lamp(F, 0, 10.8, d, 22, 0.8, P.light, { shadows = d == 45 }) end
		-- cases on the counters
		-- (no cases on the counters any more: the owner's play-test, 16 Nov, found an SMG through a case and the katana
		-- through an ammo box. the boards' guns have the counters to themselves; R.check's OVERLAP test keeps it so)
		B.paint(F, "Ray", -0.45, 0.45, -0.02, D0, 60.4, "9dbb93", 0.05)
		-- the weapon boards: the game's own weapon models on dark boards over a counter, a light over each. the top row
		-- holds one long gun, the lower row two short ones (round 1's judge: "the guns are small on big blank panels")
		local racks = {
			{ -1, 46.6, { { "w_ar" }, { "w_smg", "w_pistol" } } }, { -1, 57.4, { { "w_sniper" }, { "w_revolver", "w_sawnoff" } } },
			{ 1, 46.6, { { "w_redline" }, { "w_burst", "w_marbles" } } }, { 1, 57.4, { { "w_lmg" }, { "w_shotgun", "w_katana" } } },
		}
		for _, rk in racks do
			local s, d = rk[1], rk[2]
			B.box(F, C, "GunBoard", s * 12.55, s * 13, 2.4, 8.2, d - 4.8, d + 4.8, P.pier, nil, G)
			B.box(F, S, "GunCounter", s * 11.3, s * 12.96, 0, 2, d - 4.8, d + 4.8, P.pier2)
			B.box(F, C, "GunBoardLedge", s * 11.1, s * 13, 2, 2.4, d - 5, d + 5, P.cream, nil, G)
			B.box(F, C, "GunBoardLight", s * 12.3, s * 13, 8.2, 8.6, d - 4.8, d + 4.8, P.pier2, nil, G)
			B.box(F, C, "GunBoardGlow", s * 12.35, s * 12.9, 8.06, 8.16, d - 4.4, d + 4.4, P.strip, Neon, G)
			B.lamp(F, s * 10.6, 7.4, d, 11, 0.8)
			for row, names in rk[3] do
				local len = if #names == 1 then 6.6 else 3.9
				local at = -(#names * len + (#names - 1) * 0.8) / 2
				for _, wname in names do
					B.gun(F, wname, len, s * 12.2, if row == 1 then 6.6 else 3.95, d + at + len / 2, if s > 0 then 90 else -90, "Rack_" .. wname)
					at += len + 0.8
				end
			end
		end
		-- kit along the walls, the aisle left clear
		B.put(F, "bc_toolbench", "ToolBench", 9.5, 0, 38.05, 180, { back = true, scale = 0.8, solid = true })
		-- a locker corner like a real one (the owner: the old lockers and bench were "too close together and looks
		-- awkward"): the lockers against the near wall, the bench parallel in front of them with 3 studs to walk between
		B.put(F, R.prop("rk_lockers", "bc_lockers"), "Lockers", -9.2, 0, 38.05, 180, { back = true, scale = 0.9, solid = true, color = { ["56683f"] = P.band, ["2a2d38"] = P.pier, b07a45 = P.wood } })
		B.put(F, R.prop("rk_bench", "bc_bench"), "Bench", -8.6, 0, 44.2, 180, { solid = true, color = { ["3b2a52"] = P.wood } })
		for _, k in { { -10.1, 52, 0.8 }, { 10.1, 52, 0.8 }, { -10.9, 62.2, 0.9 } } do
			B.put(F, "wh_crate", "Crate", k[1], 0, k[2], 12, { scale = k[3] * 0.6, solid = true, color = { ff4fd8 = P.band, a8703a = P.wood, ["8a5a32"] = "9c8a6c" } })
		end
		B.put(F, "bc_hardcase", "HardCase", 10.6, 0, 62, -20, { solid = true, color = { ["2f3b2a"] = P.pier2 } })
		B.put(F, "bc_ammocrate", "AmmoCrate", 10.8, 1.7, 62, 10, { color = { ["4a5a2c"] = "66705a", ["3a4622"] = "566050" } })
		-- the gate: a chunky frame on the far wall, red bars across it; walk in and you are in the training ground
		B.put(F, "hb_portal", "TrainingPortal", 0, 0, 64, 0, { back = true, scale = 0.6, color = { ff4fd8 = P.train, ["2e3140"] = P.pier, a4aab8 = P.pier2 } })
		B.box(F, C, "LaserVoid", -4.2, 4.2, 0, 9.96, 63.3, 63.6, "42121f", nil, G)
		B.box(F, C, "LaserField", -4.2, 4.2, 0, 9.96, 62.9, 63.05, "ff2a3a", Neon, { ghost = true, tr = 0.88 })
		for i = 1, 5 do
			local b = B.box(F, C, "LaserBar", -4.2, 4.2, i * 1.66 - 0.22, i * 1.66 + 0.22, 62.78, 63.22, "ff2a3a", Neon, G)
			b.Shape = Enum.PartType.Cylinder
		end
		B.lamp(F, 0, 5, 61.4, 9, 0.5, "ff6a6a") -- (round 1's judge: the red "floods the walls pink")
		B.text(F, "GateSign", { { "TRAINING GROUND", P.train, "B", 1 } }, 7.6, 1.1, 0, 10.9, 61.6, 0, { thick = 0.3 })
		B.trigger(F, R.ROOM .. "ToTraining", -3.9, 3.9, 0, 10, 60.6, 63.2, "@TrainSpawns", "TRAINING GROUND")
		-- (where the training hall's door lands you: on the round room's floor just inside the armory's hatch, looking
		-- north at the lifts. in the armory itself you arrived facing its gun wall: the tester, 16 Nov)
		for _, b in { 244, 252, 260 } do B.arrive(B.fr(b), { { 0, 20 } }, 0, 0) end
	end
end
