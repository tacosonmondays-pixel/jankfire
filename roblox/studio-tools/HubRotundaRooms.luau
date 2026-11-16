--!nocheck
-- THE ROTUNDA, part 3: the three rooms off the round room, each down a short hall that frames it.
--   the lounge   (south, behind the spawn, on the axis) small, low and warm: brick, timber beams, seats on a raised
--                wooden border round a sunk middle, and the hologram duck turning over its projector; behind its far
--                wall, through a door on the axis, the VIP room
--   the gym      (east) the locker room with the boxing ring, only for looks
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
	-- a room: floor, lid, four walls, the near wall left open for its hall (hw wide, hh high); far = a doorway in the far
	-- wall { half its width, its height }
	local function room(F, name, x0, x1, d0, d1, h, hw, hh, wall, floor, lid, wallMat, floorMat, far)
		B.box(F, S, name .. "Floor", x0 - 2, x1 + 2, -2, -0.02, d0 - 2, d1 + 2, floor, floorMat)
		B.box(F, S, name .. "Lid", x0 - 2, x1 + 2, h, h + 1, d0 - 2, d1 + 2, lid)
		if far then
			B.box(F, S, name .. "Wall", x0 - 2, -far[1], 0, h, d1, d1 + 2, wall, wallMat)
			B.box(F, S, name .. "Wall", far[1], x1 + 2, 0, h, d1, d1 + 2, wall, wallMat)
			B.box(F, S, name .. "Wall", -far[1], far[1], far[2], h, d1, d1 + 2, wall, wallMat)
		else
			B.box(F, S, name .. "Wall", x0 - 2, x1 + 2, 0, h, d1, d1 + 2, wall, wallMat)
		end
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
		room(F, "Lounge", -14, 14, 38, 60, 11, 5, 10.4, P.brick, P.carpet, P.shell2, Brick, nil, { 2.45, 9.15 }) -- (the VIP door: below)
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
		B.cyl(F, C, "Rug", 0, -0.04, 0.03, 46.5, 12.4, P.creamHi, nil, G)
		B.cyl(F, C, "Rug", 0, -0.09, 0.07, 46.5, 11.4, P.band, nil, G)
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
			B.put(F, "bc_armchair", "Armchair", s * 6.6, 0.6, 59.2, 0, { back = true, scale = 1.1, solid = true, color = seat }) -- (either side of the VIP door)
			B.put(F, "hb_droplight", "DropLight", s * 10.6, 11, 48, 0, { seat = "top", scale = 0.7, color = { fff1d6 = P.warm } })
			B.lamp(F, s * 10.6, 6.4, 48, 15, 0.9, P.warm, { shadows = s > 0 })
			B.put(F, "hb_walllight", "WallLight", s * 8, 6.4, 59.95, 0, { back = true, seat = "centre" })
			B.put(F, R.prop("rk_planter", "bc_plantbig"), "Planter", s * 11.4, 0.6, 42.6, 0, { scale = R.propScale("rk_planter", 0.85, 0.5), solid = true, color = GREEN })
		end
		B.lamp(F, 0, 6.4, 58.6, 13, 0.7, P.warm)
		B.put(F, "bc_arcade", "Arcade", 10.6, 0.6, 56.6, -45, { solid = true, color = { ff4fd8 = P.pier2, ffe14d = P.band, ["120818"] = P.pier } })
		B.put(F, "bc_fridge", "Fridge", -10.6, 0.6, 56.6, 45, { solid = true })
		-- (no "WEAPONS HOLSTERED" sign: the HUD says so, and the owner wants no flavour text)
		-- a regular (HubNPCs builds them at start): Looticus on the east sofa, at its door end, looking over at the duck.
		-- (the seat's top on the sofa's cushion: its fabric starts at 1.92, the cushion's top about 2.45)
		B.npc(F, "Looticus", 11.2, 2.35, 46.6, 90)

		-- ---- the VIP room, behind the lounge (owner, 16 Nov: VIP, the game pass, "lets you enter the VIP room"). its door
		-- is in the middle of the lounge's far wall, on the spawn's axis behind the duck: dark leaves in a brass frame, VIP
		-- over it. a VIP player's own screen slides the leaves open and lets them through (HubVip.client: the player
		-- attribute VIP, which the server's Vip.luau sets); anyone else finds it shut, and its prompt opens the shop on the
		-- VIP tile (ShopOpen = "vip"); the server puts anyone who isn't VIP back out of the room (HubVip.server, the part
		-- tagged VipRoom). inside: a cosy, darker, warmer lounge, its floor level with the lounge's raised back; walnut
		-- panelling under a brass line, plum sofas facing each other over a round rug, a gold duck on a dark plinth at the
		-- far end in a pool of light, and the Ducky pack's skins turning over two plinths by the door (HubHolo, Offer =
		-- "vip": the pack's live skins, its wrap and its hat)
		do
			local GOLD, DARK, WALNUT, WALLV, PLUM = "b59a5c", "2c2a31", "5b4a3c", "3a3740", "5e5162"
			local FY, CH = 0.6, 10.4 -- its floor's top (the lounge's raised back) and its ceiling
			local VX, V0, V1 = 11, 62, 80 -- half its width, its near and far walls' faces
			B.box(F, S, "VipFloor", -VX - 2, VX + 2, -2, FY, 60, V1 + 2, "3d3539")
			for _, s in { -1, 1 } do B.box(F, S, "VipWall", s * VX, s * (VX + 2), FY, CH, V0, V1, WALLV) end
			B.box(F, S, "VipWall", -VX - 2, VX + 2, FY, CH, V1, V1 + 2, WALLV)
			B.box(F, S, "VipLid", -VX - 2, VX + 2, CH, CH + 1, 60.5, V1 + 2, "2f2c34") -- (its near edge inside the lounge's wall: no face shared with it)
			-- its side of the lounge's wall, lined
			for _, s in { -1, 1 } do B.box(F, C, "VipLining", s * 3.3, s * VX, FY, CH, V0, V0 + 0.25, WALLV, nil, G) end
			B.box(F, C, "VipLining", -3.3, 3.3, 9.7, CH, V0, V0 + 0.25, WALLV, nil, G)
			-- walnut panelling to the brass line, a warm light hidden along the top of the walls
			local function dado(x0, x1, d0, d1)
				B.box(F, C, "VipDado", x0, x1, FY, 4, d0, d1, WALNUT, nil, G)
				B.box(F, C, "VipBrass", x0, x1, 4, 4.18, d0, d1, GOLD, nil, G)
			end
			for _, s in { -1, 1 } do
				dado(s * (VX - 0.15), s * VX, V0 + 0.25, V1)
				dado(s * 3.3, s * VX, V0 + 0.25, V0 + 0.4)
				B.box(F, C, "VipCove", s * (VX - 0.12), s * VX, CH - 0.6, CH - 0.45, V0 + 0.25, V1, "ffd9a0", Neon, G)
			end
			dado(-VX, VX, V1 - 0.15, V1)
			B.box(F, C, "VipCove", -VX, VX, CH - 0.6, CH - 0.45, V1 - 0.12, V1, "ffd9a0", Neon, G)
			-- the gold duck on its plinth at the far end, a ring of light over it
			local DD = V1 - 4
			B.cyl(F, S, "VipPlinth", 0, FY - 0.04, 2.4, DD, 4.2, DARK)
			B.cyl(F, C, "VipPlinthBand", 0, 2.2, 2.44, DD, 4.32, GOLD, nil, G)
			local duck = B.put(F, "pj_duck", "VipDuck", 0, 2.44, DD, 180, { scale = 5, raw = true }) -- (180: the model's own front is its back. owner, 16 Nov: "can you have it face the other way?": it looks into the room, at the door)
			if duck then
				for _, p in duck:GetDescendants() do
					if p:IsA("BasePart") then
						local dark = p.Color.R + p.Color.G + p.Color.B < 0.45 -- (its eyes stay dark)
						p.Color = if dark then Color3.fromHex("2a2620") else Color3.fromHex("c9a45a")
						p.Material = Enum.Material.Metal; p.Reflectance = if dark then 0 else 0.12; p.CanCollide = false
					end
				end
			end
			B.cyl(F, C, "VipHaloRing", 0, CH - 0.12, CH - 0.02, DD, 7.6, DARK, nil, G)
			B.cyl(F, C, "VipHalo", 0, CH - 0.16, CH - 0.1, DD, 6.6, "e8cf98", Neon, { ghost = true, tr = 0.4 })
			B.lamp(F, 0, CH - 0.8, DD, 13, 1.3, "ffe2b0", { spot = true, angle = 45 })
			-- the seats: plum sofas facing each other over a round rug, a low table between, armchairs by the duck
			B.cyl(F, C, "VipRug", 0, FY - 0.02, FY + 0.04, 71, 12, "4b4048", nil, G)
			local plush = { ["3b2a52"] = "3a3440", ff4fd8 = PLUM } -- (plum cushions on dark frames: the gold stays on the trim and the duck)
			for _, s in { -1, 1 } do
				B.put(F, "bc_sofa", "VipSofa", s * (VX - 0.2), FY, 71, -s * 90, { back = true, scale = 1.1, solid = true, color = plush })
				B.put(F, "bc_armchair", "VipArmchair", s * 6.4, FY, DD + 0.6, s * 25, { scale = 1.05, solid = true, color = plush })
				B.lamp(F, s * 7, CH - 1.2, 71, 14, 0.55, "ffd9a0")
			end
			B.put(F, R.prop("rk_coffeetable", "bc_coffeetable"), "VipTable", 0, FY, 71, 0, { solid = true })
			-- a regular (R.NPCS; HubNPCs builds them at start): Trisangle on the east sofa, at its door end, across from the door
			B.npc(F, "Trisangle", -(VX - 0.2) + 2.2, 2.35, 69.8, -90)
			-- the Ducky pack, turning over two plinths either side of the door
			for k, s in { -1, 1 } do
				local x, d = s * 7.4, 64.6
				B.cyl(F, C, "VipShowFoot", x, FY - 0.04, FY + 0.3, d, 3.6, DARK)
				B.cyl(F, C, "VipShow", x, FY + 0.3, FY + 1.3, d, 3, WALNUT)
				B.cyl(F, C, "VipShowTop", x, FY + 1.26, FY + 1.34, d, 2.6, GOLD, nil, G)
				B.cyl(F, C, "VipShowLens", x, FY + 1.3, FY + 1.38, d, 0.9, "ffe2b0", Neon, G)
				B.holo(F, "HoloVip" .. k, "bundle", x, FY + 3.6, d, 1.6, 2.4, { slot = k, base = 3.6 - 1.38, prompt = "View", offer = "vip" })
			end
			-- the door: a brass frame, two dark leaves (slid open on a VIP player's own screen), VIP over it, the prompt
			for _, s in { -1, 1 } do
				B.box(F, C, "VipJamb", s * 2.4, s * 3.3, -0.04, 9.7, 59.7, 62.3, GOLD, nil, G)
				local m = Instance.new("Model"); m.Name = "VipDoorLeaf"
				B.box(F, C, "Leaf", 0, s * 2.4, FY, 9.1, 60.9, 61.1, DARK).Parent = m
				B.box(F, C, "LeafLine", s * 0.25, s * 0.55, FY + 0.2, 8.9, 60.86, 61.14, GOLD, nil, G).Parent = m
				m:SetAttribute("Slide", F:VectorToWorldSpace(Vector3.new(s * 2.3, 0, 0)))
				m.Parent = B.root.Scenery
				Tags:AddTag(m, "VipDoor")
			end
			B.box(F, C, "VipHead", -3.3, 3.3, 9.1, 9.7, 59.7, 62.3, GOLD, nil, G)
			B.text(F, "VipWord", { { "VIP", GOLD, "B", 1 } }, 3.4, 1.05, 0, 10.25, 59.9, 0, { flush = true, thick = 0.1, pps = 50, plate = DARK })
			local pp = B.box(F, C, "VipPrompt", -1, 1, 3, 5, 59.2, 59.6, DARK, nil, { ghost = true, tr = 1 })
			local pr = Instance.new("ProximityPrompt")
			pr.ActionText = "Get VIP"; pr.ObjectText = "VIP ROOM"; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.HoldDuration = 0
			pr.MaxActivationDistance = 9; pr.RequiresLineOfSight = false
			pr:SetAttribute("ShopOpen", "vip")
			pr.Parent = pp
			Tags:AddTag(pp, "VipPrompt")
			B.lamp(F, 0, 9.4, 58.4, 9, 0.6, "ffd9a0", { spot = true, angle = 70, face = Enum.NormalId.Bottom })
			-- the room itself, for the server's check: who is in it (and where they go if they shouldn't be)
			local zone = B.box(F, "Collision", "VipRoom", -VX, VX, FY, CH, V0, V1, DARK, nil, { ghost = true, tr = 1 })
			zone:SetAttribute("Out", F * Vector3.new(0, FY + 3, -57.4))
			zone:SetAttribute("OutLook", F:VectorToWorldSpace(Vector3.new(0, 0, 1)))
			Tags:AddTag(zone, "VipRoom")
		end
	end

	-- ------------------------------------------------------------ the gym (side 4, east)
	-- (the owner, 16 Nov evening: "I liked the old locker room with the boxing ring", then, with the second floor: "we can
	-- recreate the boxing gym and put just for aesthetic". so the locker room again, no pads in it and nothing behind
	-- it: a room to walk into. the owner's earlier notes kept: the ring and the target centred on the door's axis ("the
	-- boxing ring and the backwall decor are off center from the entrance ... maybe make it a bit bigger"); lockers and
	-- benches with room to walk ("too close together and looks awkward"); clear aisles either side of the ring; no floor
	-- lines)
	do
		local F = B.side(4)
		local GX, GD, GH = R.GYM_BOX[1], R.GYM_BOX[2], R.GYM_BOX[3]
		-- walls, floor and lid of a room from d0 to d1; near / far = a door { half width, height }, true = solid, nil = none
		local function shell(name, x, d0, d1, h, near, far, wall, floor, lid, from)
			B.box(F, S, name .. "Floor", -x - 2, x + 2, -2, -0.02, from or d0 - 2, d1 + 2, floor)
			B.box(F, S, name .. "Lid", -x - 2, x + 2, h, h + 1, from or d0 - 2, d1 + 2, lid)
			for _, s in { -1, 1 } do B.box(F, S, name .. "Wall", s * x, s * (x + 2), 0, h, d0 - 2, d1 + 2, wall) end
			local function across(dA, dB, door)
				if door == true then B.box(F, S, name .. "Wall", -x, x, 0, h, dA, dB, wall)
				elseif door then
					for _, s in { -1, 1 } do B.box(F, S, name .. "Wall", s * door[1], s * x, 0, h, dA, dB, wall) end
					B.box(F, S, name .. "Wall", -door[1], door[1], door[2], h, dA, dB, wall)
				end
			end
			across(d0 - 2, d0, near); across(d1, d1 + 2, far)
		end
		hall(F, "Gym", 40, 5, 11, P.shell2, P.floor, P.shell)
		for _, d in { 33.4, 37.8 } do -- two pale frames across the hall
			for _, s in { -1, 1 } do B.box(F, C, "HallFrame", s * 4.55, s * 5, 0, 11, d - 0.5, d + 0.5, P.cream, nil, G) end
			B.box(F, C, "HallFrame", -5, 5, 10.3, 11, d - 0.5, d + 0.5, P.cream, nil, G)
		end
		B.panel(F, 0, 11, 35.6, 2.4, 2.6)
		B.lamp(F, 0, 9.6, 35.6, 13, 0.7)

		-- ---- the gym
		shell("Gym", GX, 40, GD, GH, { 5, 11 }, true, P.gymWall, P.gymFloor, P.shell)
		for _, w in { { -GX, -GX + 0.2, 40, GD }, { GX - 0.2, GX, 40, GD }, { -GX + 0.2, GX - 0.2, GD - 0.2, GD } } do
			B.box(F, C, "GymDado", w[1], w[2], 0, 4, w[3], w[4], P.pier2, nil, G)
		end
		for _, w in { { -GX, -GX + 0.3, 40, GD }, { GX - 0.3, GX, 40, GD }, { -GX + 0.3, GX - 0.3, GD - 0.3, GD } } do
			B.box(F, C, "GymLine", w[1], w[2], 4, 4.6, w[3], w[4], P.band, nil, G)
		end
		cut(F, "GymCut", -1, GX, GH, 40, GD, 3, P.shell); cut(F, "GymCut", 1, GX, GH, 40, GD, 3, P.shell)
		for _, d in { 45.6, 70.6 } do B.box(F, C, "Girder", -GX, GX, GH - 1.6, GH, d - 0.7, d + 0.7, P.cream, nil, G) end
		for _, d in { 51, 64 } do
			for _, s in { -1, 1 } do B.box(F, S, "GymPier", s * (GX - 1.4), s * GX, 0, GH - 2.2, d - 1.1, d + 1.1, P.pier) end
		end
		for _, k in { { -14, 52 }, { 14, 52 }, { -14, 64 }, { 14, 64 } } do
			B.panel(F, k[1], GH, k[2], 3, 3); B.lamp(F, k[1], GH - 1.2, k[2], 24, 0.45)
		end
		-- the far wall, on the door's axis: the round target in a lit recess at eye height
		local TY = 9.5
		B.box(F, C, "RecessBack", -5.6, 5.6, TY - 2.7, TY + 3.3, GD - 0.65, GD - 0.35, P.band, nil, G)
		for _, s in { -1, 1 } do B.box(F, C, "RecessSide", s * 5.6, s * 6.6, TY - 2.7, TY + 3.3, GD - 2, GD - 0.3, P.pier, nil, G) end
		B.box(F, C, "RecessHead", -6.6, 6.6, TY + 3.3, TY + 4, GD - 2, GD - 0.3, P.pier, nil, G)
		B.box(F, C, "RecessSill", -6.6, 6.6, TY - 3.1, TY - 2.7, GD - 2, GD - 0.3, P.pier, nil, G)
		for i, k in ipairs({ { 5.4, P.creamHi }, { 4.3, P.pier }, { 3.2, P.creamHi }, { 2.1, P.pier }, { 1.1, P.glow } }) do
			local disc = B.cyl(F, C, "Target", 0, 0, 0.12, 0, k[1], k[2], if i == 5 then Neon else nil, G)
			disc.CFrame = F * CFrame.new(0, TY, -(GD - 0.75 - i * 0.1)) * CFrame.Angles(0, math.pi / 2, 0)
		end
		for _, s in { -1, 1 } do B.box(F, C, "TargetTick", s * 3.9 - 0.5, s * 3.9 + 0.5, TY - 0.25, TY + 0.25, GD - 1.05, GD - 0.65, P.creamHi, nil, G) end
		B.lamp(F, 0, GH - 1.4, GD - 8, 18, 1.2, P.warm, { spot = true, angle = 60, face = Enum.NormalId.Front })

		-- the ring, 19 across (it was 17), its middle on the door's axis: a padded platform, four fat posts, two fat rounded
		-- rails each side, two steps up on the door's side, a square light frame over it with a warm lamp at each corner, the
		-- room's one shadowed light straight over its middle
		local RD, RS, RH = R.GYM_RING, 9.5, 1.4
		local PO = RS - 0.7
		B.box(F, S, "RingBase", -RS, RS, 0, RH, RD - RS, RD + RS, P.pier2)
		B.box(F, C, "RingApron", -RS - 0.1, RS + 0.1, RH - 0.4, RH - 0.04, RD - RS - 0.1, RD + RS + 0.1, P.creamHi, nil, G)
		B.box(F, C, "RingMat", -RS + 1, RS - 1, RH, RH + 0.08, RD - RS + 1, RD + RS - 1, P.band, nil, G)
		B.box(F, C, "RingMatLine", -RS + 1, RS - 1, RH + 0.08, RH + 0.12, RD - 0.25, RD + 0.25, P.creamHi, nil, G)
		B.box(F, S, "RingStep", -2.2, 2.2, 0, RH / 2, RD - RS - 1.2, RD - RS, P.pier2)
		B.box(F, S, "RingStep", -2.2, 2.2, RH / 2, RH, RD - RS - 0.6, RD - RS, P.pier2)
		for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
			B.cyl(F, C, "RingPost", cx * PO, RH + 0.04, RH + 5, RD + cz * PO, 1.6, P.cream, nil, G)
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
		B.lamp(F, 0, GH - 1.6, RD, 36, 1.5, P.light, { spot = true, angle = 75, shadows = true })
		local LF, LY = 7.2, GH - 4.2
		for _, s in { -1, 1 } do
			B.box(F, C, "LightFrame", -LF - 0.3, LF + 0.3, LY, LY + 0.6, RD + s * LF - 0.3, RD + s * LF + 0.3, P.pier, nil, G)
			B.box(F, C, "LightFrame", s * LF - 0.3, s * LF + 0.3, LY + 0.03, LY + 0.6, RD - LF - 0.3, RD + LF + 0.3, P.pier, nil, G)
		end
		for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
			B.box(F, C, "FrameRod", cx * LF - 0.3, cx * LF + 0.3, LY + 0.6, GH, RD + cz * LF - 0.3, RD + cz * LF + 0.3, P.pier, nil, G)
			B.put(F, "hb_droplight", "RingLamp", cx * 5, LY, RD + cz * 5, 0, { seat = "top", scale = 0.8, color = { fff1d6 = P.warm } })
			B.lamp(F, cx * 5, LY - 3, RD + cz * 5, 16, 0.7, P.warm)
		end end
		-- the kit (R.prop: the hub's own chunky kit; the old bc_ pieces if it isn't imported). by the door, a locker bank
		-- against each side wall with a bench in front of it; bags along the north wall's far half, weights along the
		-- south's; tyres and the sparring dummy in the far corners. the aisles either side of the ring stay clear
		for _, s in { -1, 1 } do
			B.put(F, R.prop("rk_lockers", "bc_lockers"), "Lockers", s * (GX - 0.05), 0, 45.3, -s * 90, { back = true, solid = true, color = { ["56683f"] = P.band, ["2a2d38"] = P.pier, b07a45 = P.wood } })
			B.put(F, R.prop("rk_bench", "bc_bench"), "Bench", s * (GX - 5.8), 0, 45.3, 90, { solid = true, color = { ["3b2a52"] = P.wood } })
		end
		for _, d in { 55.4, 59.6 } do B.put(F, R.prop("rk_punchbag", "bc_punchbag"), "PunchBag", -GX + 2, 0, d, 90, { solid = Vector3.new(3.2, 7.4, 3.2), color = { c8262e = P.pier2, ["17141f"] = P.cream } }) end
		B.paint(F, "Mat", -GX + 0.3, -GX + 3.7, -0.02, 53.4, 61.6, P.band, 0.03)
		B.put(F, R.prop("rk_dumbbells", "bc_dumbbells"), "Dumbbells", GX - 1.1, 0, 57.5, -90, { scale = R.propScale("rk_dumbbells", 1, 0.8), solid = true })
		B.put(F, R.prop("rk_tyres", "bc_tyres"), "Tyres", -GX + 3.4, 0, GD - 3.2, 90, { scale = R.propScale("rk_tyres", 1, 0.6), solid = true })
		do -- the sparring dummy in the far south corner (it also shows the room's scale)
			local x, d = GX - 3.4, GD - 3.2
			B.cyl(F, S, "DummyBase", x, 0, 0.4, d, 2.8, P.pier2)
			B.cyl(F, C, "DummyPost", x, 0.4, 3.2, d, 0.8, P.pier, nil, G)
			B.box(F, C, "DummyBody", x - 1.2, x + 1.2, 3.2, 6.2, d - 0.65, d + 0.65, P.creamHi, nil, G)
			local head = B.box(F, C, "DummyHead", x - 0.8, x + 0.8, 6.3, 7.9, d - 0.8, d + 0.8, P.creamHi, nil, G)
			head.Shape = Enum.PartType.Ball
			B.solid("DummyBox", Vector3.new(2.6, 8, 2.6), F * CFrame.new(x, 4, -d))
		end
		-- a regular (R.NPCS; HubNPCs builds them at start): Dune standing just off the south aisle (outside it: the walk
		-- past the ring stays clear), between the weights and the dummy, turned to the ring's middle
		B.npc(F, "Dune", 15.4, 0, 62.5, 105)

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
		-- (no guide line down the aisle to the gate: the owner called floor lines and arrows "ugly and redundant". the gate
		-- reads on its own: TRAINING GROUND over the laser frame at the aisle's end)
		-- the weapon boards: the game's own weapon models on dark boards over a counter, a light over each. every gun at its
		-- true size, one scale for all (the owner, 16 Nov: they "look massive, at least scale them, because a revolver is
		-- not the size of a sniper"): the long guns along the top row, the shorter ones and the sidearms under them, room
		-- between
		local GUN_K = 3.5 -- (the sniper 7.3 long, the AR 4.2, the pistol 1.2)
		local racks = {
			{ -1, 46.6, { { "w_sniper" }, { "w_ar", "w_pistol" } } }, { -1, 57.4, { { "w_lmg" }, { "w_smg", "w_revolver" } } },
			{ 1, 46.6, { { "w_burst", "w_marbles" }, { "w_shotgun", "w_sawnoff" } } }, { 1, 57.4, { { "w_redline" }, { "w_katana" } } },
		}
		local weapons = game.ReplicatedStorage:FindFirstChild("JankfireWeapons")
		local function long(w)
			local t = weapons and weapons:FindFirstChild(w)
			if not t then return 0 end
			local _, sz = t:GetBoundingBox()
			return sz.Z * GUN_K
		end
		for _, rk in racks do
			local s, d = rk[1], rk[2]
			B.box(F, C, "GunBoard", s * 12.55, s * 13, 2.4, 8.2, d - 4.8, d + 4.8, P.pier, nil, G)
			B.box(F, S, "GunCounter", s * 11.3, s * 12.96, 0, 2, d - 4.8, d + 4.8, P.pier2)
			B.box(F, C, "GunBoardLedge", s * 11.1, s * 13, 2, 2.4, d - 5, d + 5, P.cream, nil, G)
			B.box(F, C, "GunBoardLight", s * 12.3, s * 13, 8.2, 8.6, d - 4.8, d + 4.8, P.pier2, nil, G)
			B.box(F, C, "GunBoardGlow", s * 12.35, s * 12.9, 8.06, 8.16, d - 4.4, d + 4.4, P.strip, Neon, G)
			B.lamp(F, s * 10.6, 7.4, d, 11, 0.8)
			for row, names in rk[3] do
				local lens, total = {}, (#names - 1) * 0.9
				for i, w in names do lens[i] = long(w); total += lens[i] end
				local at = -total / 2
				for i, w in names do
					B.gun(F, w, nil, s * 12.2, if row == 1 then 6.5 else 4, d + at + lens[i] / 2, if s > 0 then 90 else -90, "Rack_" .. w, GUN_K)
					at += lens[i] + 0.9
				end
			end
		end
		-- kit along the walls, the aisle left clear
		-- a gun maintenance bench where the tool bench was (the owner, 16 Nov, of the workbench with the pegboard and the
		-- toolboxes: "can we fix that crafting station or replace it with something else?"): a heavy bench against the near
		-- wall, a rifle lying on a cleaning mat, a vice, a few rounds and a cleaning rod by it, two ammo cans on the shelf
		-- under it, a warm lamp over it. chunky pieces, flat colours, no text
		do
			local bench = Instance.new("Model"); bench.Name = "GunBench"
			local x0, x1, d0, d1 = 6.6, 12.4, 38.15, 41.1 -- (its footprint: the near wall's face is at d 38)
			local parts = {
				B.box(F, C, "BenchTop", x0, x1, 2.9, 3.4, d0, d1, P.wood),
				B.box(F, C, "BenchShelf", x0 + 0.3, x1 - 0.3, 0.8, 1.05, d0 + 0.2, d1 - 0.3, P.pier2),
				B.box(F, C, "BenchBack", x0, x1, 3.4, 4.4, d0, d0 + 0.35, P.pier2),
				B.box(F, C, "Mat", 7.8, 12.2, 3.4, 3.46, 39, 41, P.band, nil, G),
				B.box(F, C, "ViceBase", 6.85, 7.65, 3.4, 3.8, 39.3, 40.5, P.pier),
				B.box(F, C, "ViceJaw", 6.95, 7.55, 3.8, 4.35, 39.4, 39.62, P.pier2),
				B.box(F, C, "ViceJaw", 6.95, 7.55, 3.8, 4.35, 40.18, 40.4, P.pier2),
			}
			for _, lx in { x0 + 0.25, x1 - 0.25 } do
				for _, ld in { d0 + 0.3, d1 - 0.3 } do table.insert(parts, B.box(F, C, "BenchLeg", lx - 0.25, lx + 0.25, 0, 2.9, ld - 0.25, ld + 0.25, P.pier)) end
			end
			for k, rx in { 11.45, 11.7, 11.95 } do
				local r = B.cyl(F, C, "Round", rx, 3.4, 3.4 + 0.42 + 0.04 * k, 38.8, 0.18, "b8a985", nil, G)
				table.insert(parts, r)
			end
			local rod = B.box(F, C, "CleaningRod", 8.1, 11, 3.46, 3.58, 38.79, 38.91, P.pier, nil, G)
			rod.Shape = Enum.PartType.Cylinder
			table.insert(parts, rod)
			for _, cx in { 7.9, 9.9 } do
				table.insert(parts, B.box(F, C, "AmmoCan", cx - 0.7, cx + 0.7, 1.05, 1.85, 38.7, 40.6, "5f6b5a"))
				table.insert(parts, B.box(F, C, "AmmoCanHandle", cx - 0.4, cx + 0.4, 1.85, 1.95, 39.57, 39.73, "434a55", nil, G))
			end
			for _, p in parts do p.Parent = bench end
			bench.Parent = B.root.Scenery
			B.solid("GunBenchBox", Vector3.new(x1 - x0, 3.4, d1 - d0), F * CFrame.new((x0 + x1) / 2, 1.7, -(d0 + d1) / 2))
			local gun = B.gun(F, "w_burst", nil, 10, 3.46 + 0.03 + 0.06 * GUN_K, 40, 0, "Bench_w_burst", GUN_K)
			if gun then gun:PivotTo(gun:GetPivot() * CFrame.Angles(0, 0, math.pi / 2)) end -- (lying on its side)
			B.lamp(F, 9.6, 7.2, 39.8, 9, 0.6, P.warm, { spot = true, angle = 70, face = Enum.NormalId.Bottom })
		end
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
		-- (the lasers are one model tagged LaserGate: TrainingDoors.client switches its LaserField and LaserBars off with a
		-- click while anyone is within Near of it, and back on after. owner, 16 Nov: "when you go to the laser gate, when
		-- you get close you hear a click and the laser gate turns off")
		local gate = Instance.new("Model"); gate.Name = "TrainingLaserGate"
		local field = B.box(F, C, "LaserField", -4.2, 4.2, 0, 9.96, 62.9, 63.05, "ff2a3a", Neon, { ghost = true, tr = 0.88 })
		field.Parent = gate
		for i = 1, 5 do
			local b = B.box(F, C, "LaserBar", -4.2, 4.2, i * 1.66 - 0.22, i * 1.66 + 0.22, 62.78, 63.22, "ff2a3a", Neon, G)
			b.Shape = Enum.PartType.Cylinder
			b.Parent = gate
		end
		gate:SetAttribute("Center", (F * CFrame.new(0, 5, -63)).Position); gate:SetAttribute("Near", 9)
		gate.Parent = B.root.Scenery
		game:GetService("CollectionService"):AddTag(gate, "LaserGate")
		B.lamp(F, 0, 5, 61.4, 9, 0.5, "ff6a6a") -- (round 1's judge: the red "floods the walls pink")
		-- (no sign over the gate: the round room's word TRAINING names this way, and the HUD names the place on entry)
		B.trigger(F, R.ROOM .. "ToTraining", -3.9, 3.9, 0, 10, 60.6, 63.2, "@TrainSpawns", "TRAINING GROUND")
		-- (where the training hall's door lands you: on the round room's floor just inside the armory's hatch, looking
		-- north at the lifts. in the armory itself you arrived facing its gun wall: the tester, 16 Nov)
		for _, b in { 244, 252, 260 } do B.arrive(B.fr(b), { { 0, 20 } }, 0, 0) end
	end
end
