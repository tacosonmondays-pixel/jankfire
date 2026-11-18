--!nocheck
-- THE ROTUNDA, part 3: the three rooms off the round room, each down a short hall that frames it.
--   the lounge   (south, on the axis) where you appear since 18 Nov: a big room as wide as the round room, open onto it
--                through three arches, the spawn rug on its front floor, the showroom down its west wall, seats down
--                its east wall; in its middle the old small lounge as a bay under a timber canopy (brick, beams, seats
--                on a raised wooden border round a sunk middle, the hologram duck turning over its projector); behind
--                its far wall, through a door on the axis, the VIP room. since 18 Nov (R.LOUNGE_STYLE = "plaza") the
--                hotel plaza instead: a courtyard in front of the three arches under a glass roof, hotel rooms round it
--                over arcades (the boutique, the lounge and bar, the reception, the VIP door), a fountain, trees
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

	-- ---- the VIP room, behind the lounge (owner, 16 Nov: VIP, the game pass, "lets you enter the VIP room"). its door
	-- is in the middle of the lounge's far wall, on the spawn's axis behind the duck: dark leaves in a brass frame, VIP
	-- over it. a VIP player's own screen slides the leaves open and lets them through (HubVip.client: the player
	-- attribute VIP, which the server's Vip.luau sets); anyone else finds it shut, and its prompt opens the shop on the
	-- VIP tile (ShopOpen = "vip"); the server puts anyone who isn't VIP back out of the room (HubVip.server, the part
	-- tagged VipRoom). inside: a cosy, darker, warmer lounge, its floor level with the lounge's raised back; walnut
	-- panelling under a brass line, plum sofas facing each other over a round rug, a gold duck on a dark plinth at the
	-- far end in a pool of light, and the Ducky pack's skins turning over two plinths by the door (HubHolo, Offer =
	-- "vip": the pack's live skins, its wrap and its hat)
	-- (a function since the plaza, 18 Nov: F = the frame whose d = 60 is the face of the wall the VIP door is in)
	local function vipRoom(F)
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
		local tris = B.npc(F, "Trisangle", -(VX - 0.2) + 2.2, 2.35, 69.8, -90)
		-- the seats she moves between (either end of either sofa): she stands up onto the point in front of one (its
		-- Stand, R.NPC_STAND out), steps on out to its approach (1.7 further), and goes along the aisle beside the table
		-- and across the room by the door (clear of the table, the sofas and the plinths); or straight along the front
		-- of the sofa to its other end
		if tris then tris:SetAttribute("Door", F * Vector3.new(0, FY, -65.6)) end
		local SX = (VX - 0.2) - 2.2
		for k, w in { { -1, 69.8 }, { -1, 72.4 }, { 1, 69.8 }, { 1, 72.4 } } do
			local s, d = w[1], w[2]
			B.npcPoint(F, "Trisangle", k, "seat", "sit", s * SX, 2.35, d, s * 90, { approach = F * Vector3.new(s * (SX - R.NPC_STAND - 1.7), FY, -d), aisle = F * Vector3.new(s * 5.2, FY, -67) })
		end
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

	-- ------------------------------------------------------------ the hotel plaza (side 7, due south; R.LOUNGE_STYLE = "plaza")
	-- (18 Nov 2026, the owner: "can you try remodelling the hub lounge into like a hotel plaza? rn a lot of your extensions
	-- just look like well extensions, it doesnt look very natural". one building round a covered courtyard, in the round
	-- room's own language turned inside out: its piers floor to cornice, the balcony's band, the gallery's windows, its
	-- cornice. the round room's three south faces are the courtyard's north side (the arches the way in, a balcony over
	-- the middle one, a bay window over each side one: the west one holds the hub egg's nook, R.EGG_NICHE); three walls
	-- close the rest, over arcades: the showroom down the west one, seats and the bar down the east one, the reception
	-- and the VIP door in the south one. 18 Nov, the owner: "the lobby area looks like the outside of a hotel rather than
	-- the inside now!", so it is a LOBBY, inside: a mezzanine gallery with a balustrade round three sides, panelled
	-- doors off it, a coffered plaster ceiling with chandeliers, rugs and seating. R.PLAZA has the plan)
	local function plaza(vipRoom)
		local F7 = B.side(7)
		local PZ = R.PLAZA
		local X, DS, BACK, OUT, FW, BEAM, ROOF = PZ.X, PZ.D, PZ.BACK, PZ.OUT, PZ.WALL, PZ.BEAM, PZ.ROOF
		local ACCENT = P.doorGlow or P.glow
		local GLASS = P.plate -- (the shops' doors and the lounge's windows: dark, nothing behind them)
		local WATER, LEAF = "6f9498", { "5f7a58", "6a8562", "56704f" }
		local seat = { ["3b2a52"] = P.creamHi, ff4fd8 = P.band }
		-- (the hotel's paint, 18 Nov, main: "lighter, warm quiet stone or plaster for the facades and arcades": warm stone
		-- walls, a paler stone for their trim, warm grey floors; colour stays on the pads, the boards and the one accent)
		local STONE, STONE2, TRIM, TRIM2 = "958d80", "857e73", "b8b0a1", "c8c1b3"
		local FLOOR, FLOOR2 = "68645d", "57534d"
		local PIERC = { ["2e3140"] = "8e877c", a4aab8 = "a39b8e", ["5b6478"] = "a39b8e", f4f8ff = "f0d6a8" } -- (the piers' light slots warm too; shaft, corbel and head one colour: their backs share a plane, seen from the arcades)
		local LIT = "dcbf8f" -- (a shop's window lit warm)
		local WOOD, WOOD2, PLASTER = "6b5444", "5e4a3c", "a39b8e" -- (the lobby's panelling and doors; its ceiling)
		local wo = B.wid(A + T) / 2 -- (a round-room side's outer half width)
		local rcO = (A + T) / math.cos(math.pi / R.N)
		local cx, cd = rcO * math.sin(3 * math.pi / R.N), rcO * math.cos(3 * math.pi / R.N) -- the round room's outer corner between sides 6 / 8 and 5 / 9
		local PDs = table.clone(PZ.PIERS_D); table.insert(PDs, DS) -- (the side facades' piers, the corner last)
		local PXs = { -X }
		for i = #PZ.PIERS_X, 1, -1 do table.insert(PXs, -PZ.PIERS_X[i]) end
		for _, x in PZ.PIERS_X do table.insert(PXs, x) end
		table.insert(PXs, X)
		-- a facade's frame: x along it, its face at d = A, d > A into its wall (the round room's sides' numbers: the same
		-- trim fits). the west one's x runs north, the east one's south
		local function FWest(dc) return F7 * CFrame.new(X, 0, -dc) * CFrame.Angles(0, -math.pi / 2, 0) * CFrame.new(0, 0, A) end
		local function FEast(dc) return F7 * CFrame.new(-X, 0, -dc) * CFrame.Angles(0, math.pi / 2, 0) * CFrame.new(0, 0, A) end
		local function FSouth(xc) return F7 * CFrame.new(xc, 0, -DS) * CFrame.new(0, 0, A) end

		-- ---- the floor: the courtyard (the round room's stone), the arcades a step darker
		B.box(F7, S, "PlazaFloor", -X, X, -2.1, -0.05, cd - 1, DS, FLOOR) -- (its top 0.05 under the round room's floor, which lies over its front)
		for _, s in { -1, 1 } do B.box(F7, S, "PlazaFloor", s * X, s * (OUT + 2), -2.1, -0.05, cd, BACK + 2, FLOOR2) end
		B.box(F7, S, "PlazaFloor", -X, X, -2.1, -0.05, DS, BACK + 2, FLOOR2) -- (bottoms under the VIP room's floor's)

		-- ---- the outer walls (the arcades' backs), the arcades' north ends, their ceilings
		for _, s in { -1, 1 } do
			B.box(F7, S, "PlazaWall", s * OUT, s * (OUT + 2), -0.04, BEAM, cd, BACK + 2, STONE2) -- (bottoms under the piers' bases')
			B.box(F7, S, "PlazaWall", s * (X + FW), s * OUT, -0.04, BEAM, cd, cd + 2, STONE2) -- (an arcade's north end)
			B.box(F7, S, "PlazaWall", s * X, s * (X + FW), -0.04, BEAM, cd - 0.7, PDs[1] - 1.4, STONE2) -- (the facade's solid north end, against the round room)
			B.box(F7, S, "PlazaWall", s * 2.45, s * OUT, -0.04, BEAM, BACK - 0.04, BACK + 2, STONE2) -- (the south arcade's back, either side of the VIP door; its face a hair in front of the VIP room's floor's end)
			B.box(F7, S, "ArcadeLid", s * (X + FW), s * (OUT + 2), BEAM, BEAM + 1, cd, BACK + 2, PLASTER)
		end
		B.box(F7, S, "PlazaWall", -2.45, 2.45, 9.15, BEAM, BACK, BACK + 2, STONE2) -- (over the VIP door)
		B.box(F7, S, "ArcadeLid", -(X + FW), X + FW, BEAM, BEAM + 1, DS + FW, BACK + 2, PLASTER)
		-- the facades' walls, from the openings' head to the ceiling
		for _, s in { -1, 1 } do B.box(F7, S, "FacadeWall", s * X, s * (X + FW), BEAM, ROOF, cd - 0.3, DS + FW, STONE) end
		B.box(F7, S, "FacadeWall", -X, X, BEAM, ROOF, DS, DS + FW, STONE)

		-- ---- the ceiling: one flat plaster ceiling over the whole lobby (its north edge on the round room's faces: a
		-- parapet on each, the lid's corners as wedges laid flat, as the lounge's were), coffered by deep beams, a warm
		-- downlight in each coffer, a rose over each chandelier. (18 Nov, the owner: "the lobby area looks like the outside
		-- of a hotel rather than the inside now!": no glass roof, no daylight; the coffers line up on the two chandeliers)
		local XF = X + FW
		B.box(F7, S, "PlazaLid", -XF, XF, ROOF, ROOF + 1, A + T, DS + FW, PLASTER)
		for _, s in { -1, 1 } do
			B.box(F7, S, "PlazaLid", s * cx, s * XF, ROOF, ROOF + 1, cd - 0.3, A + T, PLASTER)
			local w = B.box(F7, S, "PlazaLidCorner", 0, 1, ROOF, ROOF + 1, cd, A + T, PLASTER, nil, { wedge = true })
			local vY, vZ = Vector3.new(-s, 0, 0), Vector3.new(0, 0, -1)
			w.Size = Vector3.new(1, cx - wo, A + T - cd)
			w.CFrame = F7 * CFrame.fromMatrix(Vector3.new(s * (cx + wo) / 2, ROOF + 0.5, -(cd + A + T) / 2), vY:Cross(vZ), vY, vZ)
		end
		local CX = { -15.83, -9.5, -3.17, 3.17, 9.5, 15.83 } -- (the beams along the lobby)
		local CD = { 33.7, 40.25, 47.75, 55.25, 62.75 } -- (across it: the coffers' middles at 44 and 59 are the chandeliers')
		for _, x in CX do B.box(F7, C, "CofferBeam", x - 0.45, x + 0.45, ROOF - 1.2, ROOF, A + T, DS, TRIM, nil, G) end
		for _, d in CD do B.box(F7, C, "CofferBeam", -X, X, ROOF - 1.15, ROOF, d - 0.45, d + 0.45, TRIM, nil, G) end -- (bottoms 0.05 off the others')
		local cxs = { -12.67, -6.33, 0, 6.33, 12.67 }
		local cds = { 37, 44, 51.5, 59, 66 }
		for _, x in cxs do
			for _, d in cds do
				if x == 0 and (d == 44 or d == 59) then
					B.cyl(F7, C, "CeilingRose", 0, ROOF - 0.4, ROOF - 0.02, d, 3.2, TRIM2, nil, G)
				else
					B.cyl(F7, C, "Downlight", x, ROOF - 0.1, ROOF - 0.02, d, 0.9, "f0d6a8", Neon, G)
				end
			end
		end
		for _, e in { { -9.5, 40 }, { 9.5, 40 }, { -9.5, 62 }, { 9.5, 62 } } do B.lamp(F7, e[1], ROOF - 3, e[2], 40, 0.25, P.warm) end
		B.lamp(F7, 0, ROOF - 1.5, (37 + DS) / 2, 50, 0.25, P.warm, { spot = true, angle = 120 })

		-- ---- the walls over the arcades. one bay between two piers: the band over the opening (the gallery's edge rests on
		-- it), a gallery's wall over that (a wood dado and its rail, a panelled wood door to each room, a moulded plaster
		-- panel over each door on the picture rail, a sconce between the doors), a frieze and the cornice. grand = one wide
		-- double door (the south wall's middle bay, over the VIP door); plain = only the lines. (18 Nov: inside, not
		-- outside: no windows, shutters, balconies or flower boxes)
		local bayN = 0
		local function bay(Ff, w, kind, only)
			local hw = w / 2
			bayN += 1
			B.box(Ff, C, "Band", -hw, hw, BEAM + 0.03, BEAM + 2.2, A - 0.3, A, TRIM, nil, G) -- (its bottom off the round room's lintels')
			if kind ~= "plain" then B.box(Ff, C, "Soffit", -hw, hw, BEAM - 0.15, BEAM, A, A + FW, TRIM2, nil, G) end -- (the opening's head, under the wall)
			B.box(Ff, C, "StringCourse", if only == 1 then -1.5 else -hw, if only == -1 then 1.5 else hw, 21.4, 21.8, A - 0.25, A, TRIM, nil, G)
			B.box(Ff, C, "Frieze", -hw, hw, 25.6, 26, A - 0.5, A, TRIM, nil, G)
			B.box(Ff, C, "Cornice", -hw, hw, 26, 27.42, A - 1.2, A, TRIM, nil, G) -- (its top under the piers' heads')
			if kind == "plain" then return end
			local d0, d1 = if only == 1 then -1.5 else -hw, if only == -1 then 1.5 else hw
			B.box(Ff, C, "GalleryDado", d0, d1, BEAM + 2.25, BEAM + 3.5, A - 0.08, A, WOOD, nil, G)
			B.box(Ff, C, "GalleryDadoRail", d0, d1, BEAM + 3.5, BEAM + 3.75, A - 0.2, A, TRIM, nil, G)
			local function door(x, half)
				for _, s in { -1, 1 } do B.box(Ff, C, "DoorJamb", x + s * half, x + s * (half + 0.4), BEAM + 2.25, 20.4, A - 0.35, A, TRIM2, nil, G) end
				B.box(Ff, C, "DoorHead", x - half - 0.4, x + half + 0.4, 20.4, 20.9, A - 0.4, A, TRIM2, nil, G)
				B.box(Ff, C, "Door", x - half, x + half, BEAM + 2.25, 20.4, A - 0.14, A, WOOD, nil, G)
				local leaves = if half > 2 then { { x - half, x }, { x, x + half } } else { { x - half, x + half } }
				for _, lf in leaves do
					for _, y in { { BEAM + 2.75, 16.9 }, { 17.4, 19.9 } } do B.box(Ff, C, "DoorPanel", lf[1] + 0.3, lf[2] - 0.3, y[1], y[2], A - 0.22, A - 0.14, WOOD2, nil, G) end
					B.box(Ff, C, "DoorHandle", lf[2] - 0.55, lf[2] - 0.4, 16.8, 17.5, A - 0.32, A - 0.14, "b59a5c", nil, G)
				end
			end
			local function panel(x, half)
				B.box(Ff, C, "WallPanel", x - half, x + half, 22, 25, A - 0.06, A, STONE2, nil, G)
				for _, s in { -1, 1 } do B.box(Ff, C, "WallPanelFrame", x + s * half, x + s * (half + 0.22), 22, 25, A - 0.18, A, TRIM2, nil, G) end
				for _, y in { { 21.82, 22 }, { 25, 25.22 } } do B.box(Ff, C, "WallPanelFrame", x - half - 0.22, x + half + 0.22, y[1], y[2], A - 0.18, A, TRIM2, nil, G) end
			end
			local function sconce(x)
				B.box(Ff, C, "SconcePlate", x - 0.3, x + 0.3, 17.6, 18.8, A - 0.12, A, TRIM, nil, G)
				B.box(Ff, C, "SconceArm", x - 0.08, x + 0.08, 18.1, 18.3, A - 0.6, A - 0.12, "b59a5c", nil, G)
				B.box(Ff, C, "SconceShade", x - 0.3, x + 0.3, 18.3, 19.1, A - 0.85, A - 0.35, "f0d6a8", Neon, G)
				B.lamp(Ff, x, 18.7, A - 0.9, 12, 0.2, P.warm)
			end
			if kind == "grand" then door(0, 2.2); panel(0, 2.2); sconce(-4.2); sconce(4.2)
			else
				for _, s in { -1, 1 } do if not only or s == only then door(s * 2.9, 1.25); panel(s * 2.9, 1.15) end end
				if not only then sconce(0) end
			end
		end
		-- the piers: the round room's, floor to cornice, set into the facade's wall
		local function pier(Ff, x, name)
			B.put(Ff, "hb_pier", name or "Pier", x, 0, A + FW / 2, 0, { stretch = Vector3.new(2.9 / 6.2, 27.5 / 48, 4.4 / 3.6), solid = Vector3.new(2.9, BEAM, 4.2),
				color = PIERC })
		end
		local north = PDs[1] - 1.45 -- (where the side facades' solid north ends stop)
		for _, side in { { FWest, 1 }, { FEast, -1 } } do
			local Ff, s = side[1], side[2]
			for k = 1, #PDs - 1 do
				local dc = (PDs[k] + PDs[k + 1]) / 2
				bay(Ff(dc), PDs[k + 1] - PDs[k], nil, if k == 1 then -s else nil) -- (x runs north on the west one, south on the east one)
			end
			bay(Ff((cd - 0.3 + PDs[1]) / 2), PDs[1] - (cd - 0.3), "plain") -- (over the solid north end: only the lines)
			-- the solid north end's face, trimmed as the round room's closed sides are (its north part is inside the round
			-- room's wall)
			local Fn = Ff((cd - 0.3 + north) / 2)
			local hw = (north - (cd - 0.3)) / 2
			B.box(Fn, C, "Base", -hw, hw, 0, 0.7, A - 0.35, A, "7a746a", nil, G)
			B.box(Fn, C, "Dado", -hw, hw, 0.7, 5, A - 0.22, A, WOOD, Wood, G)
			B.box(Fn, C, "Ledge", -hw, hw, 5, 5.5, A - 0.6, A, TRIM, nil, G)
			for k = 1, #PDs - 1 do pier(Ff(PDs[k]), 0) end
		end
		for k = 1, #PXs - 1 do
			local xc = (PXs[k] + PXs[k + 1]) / 2
			bay(FSouth(xc), PXs[k + 1] - PXs[k], if math.abs(xc) < 0.1 then "grand" else nil)
		end
		for k = 2, #PXs - 1 do pier(FSouth(PXs[k]), 0) end
		-- the mezzanine gallery round three sides (18 Nov, the owner's lobby: "a mezzanine with a balustrade"): its floor on
		-- the band's top, 2.6 out from the walls, an edge, turned balusters under a rail. the side ones start past the bay
		-- windows over the side arches; the south one runs across and holds the corners
		do
			local GD, GY = 2.6, BEAM + 2.2
			local G0 = 34 -- (where the side ones start: clear of the bay walls over the side arches)
			local function rail(x0, x1, d0, d1, o)
				B.box(F7, C, "GalleryRail", x0, x1, GY + 3.1 + o, GY + 3.45 + o, d0, d1, TRIM, nil, G)
				B.box(F7, C, "GalleryRailFoot", x0, x1, GY, GY + 0.22, d0, d1, TRIM, nil, G)
			end
			for _, s in { -1, 1 } do
				B.box(F7, C, "GalleryFloor", s * (X - GD), s * (X - 0.3), GY - 0.6, GY, G0, DS - GD, TRIM, nil, G)
				B.box(F7, C, "GalleryEdge", s * (X - GD - 0.2), s * (X - GD), GY - 0.75, GY + 0.08, G0, DS - GD, TRIM2, nil, G)
				rail(s * (X - GD - 0.05), s * (X - GD + 0.35), G0, DS - GD + 0.35, 0)
				rail(s * (X - GD + 0.35), s * (X - 0.3), G0, G0 + 0.35, 0.02) -- (its north end closed)
				for d = G0 + 0.45, DS - GD - 0.3, 0.9 do B.cyl(F7, C, "Baluster", s * (X - GD + 0.15), GY + 0.22, GY + 3.1, d, 0.26, TRIM2, nil, G) end
				for x = X - GD + 1.05, X - 0.6, 0.9 do B.cyl(F7, C, "Baluster", s * x, GY + 0.22, GY + 3.1, G0 + 0.17, 0.26, TRIM2, nil, G) end
			end
			B.box(F7, C, "GalleryFloor", -(X - 0.3), X - 0.3, GY - 0.6, GY, DS - GD, DS - 0.3, TRIM, nil, G)
			B.box(F7, C, "GalleryEdge", -(X - GD), X - GD, GY - 0.72, GY + 0.11, DS - GD - 0.2, DS - GD, TRIM2, nil, G)
			rail(-(X - GD - 0.05), X - GD - 0.05, DS - GD - 0.05, DS - GD + 0.35, 0.03)
			for x = -(X - GD) + 0.6, X - GD - 0.5, 0.9 do B.cyl(F7, C, "Baluster", x, GY + 0.22, GY + 3.1, DS - GD + 0.15, 0.26, TRIM2, nil, G) end
		end

		-- the courtyard's two south corners: a pier set across each, as the round room's stand between its sides
		for _, s in { -1, 1 } do
			local Fc = F7 * CFrame.new(s * X, 0, -DS) * CFrame.Angles(0, -s * math.pi / 4, 0)
			B.put(Fc, "hb_pier", "Pier", 0, 0, 1.1, 0, { stretch = Vector3.new(2.9 / 6.2, 27.5 / 48, 4.4 / 3.6), solid = Vector3.new(2.9, BEAM, 4.2),
				color = PIERC })
		end

		-- ---- the round room's three south faces, from the courtyard: a parapet up to the ceiling, the same lines as the
		-- facades (the band, the string course, the frieze, the cornice), each arch framed (imposts, a keystone), a
		-- balcony with doors and a window over the middle one, a bay window over each side one
		for _, k in { 6, 7, 8 } do
			local Fk = B.side(k)
			local o = if k == 7 then 0 else 0.05 -- (the corners where two faces' trim meets: not in one plane)
			local e = A + T
			B.box(Fk, S, "Parapet", -(wo + 0.05), wo + 0.05, 27.48 + o, ROOF, e - 1.2, e, STONE) -- (from over the lintels' tops: the cornice hides the seam)
			B.box(Fk, C, "Band", -(wo + 0.15), wo + 0.15, 14.2 + o, 14.7 + o, e, e + 0.3, TRIM, nil, G)
			-- (a skin of the stone on the wall's outer face from the arches' tops up, with a hole for the hub egg's nook)
			local N = R.EGG_NICHE
			if k == R.EGG_SIDE then
				B.box(Fk, C, "FaceSkin", -(wo + 0.05), wo + 0.05, 12.05, 16.38, e, e + 0.06, STONE, nil, G) -- (under the built-out wall)
			elseif k ~= 7 then
				B.box(Fk, C, "FaceSkin", -(wo + 0.05), wo + 0.05, 12.05, 16.38, e, e + 0.06, STONE, nil, G)
			else
				B.box(Fk, C, "StringCourse", -(wo + 0.15), wo + 0.15, 21.4 + o, 21.8 + o, e, e + 0.25, TRIM, nil, G)
				B.box(Fk, C, "FaceSkin", -(wo + 0.05), wo + 0.05, 12.05, 27.4, e, e + 0.06, STONE, nil, G)
			end
			if k == 7 then
				B.box(Fk, C, "Frieze", -(wo + 0.25), wo + 0.25, 25.6 + o, 26 + o, e, e + 0.5, TRIM, nil, G)
				B.box(Fk, C, "Cornice", -(wo + 0.35), wo + 0.35, 26 + o, 27.5 + o, e, e + 1.2, TRIM, nil, G)
			end
			if k == 7 then
				B.box(Fk, C, "BalconySlab", -3.4, 3.4, 14.2, 14.7, e, e + 2.4, TRIM, nil, G)
				B.box(Fk, C, "Balustrade", -3.4, 3.4, 14.7, 15.9, e + 2.12, e + 2.4, TRIM2, nil, G)
				for _, s in { -1, 1 } do
					B.box(Fk, C, "Balustrade", s * 3.12, s * 3.4, 14.7, 15.9, e, e + 2.12, TRIM2, nil, G)
					B.bar(Fk, C, "BalconyCorbel", s * 2.6, 0.8, 0.5, e + 2.2, 14.2, e, 12.9, TRIM, nil, G)
					B.box(Fk, C, "DoorJamb", s * 2, s * 2.4, 14.7, 20.4, e, e + 0.35, TRIM2, nil, G)
					B.box(Fk, C, "WindowJamb", s * 2, s * 2.35, 21.8, 24.8, e, e + 0.3, TRIM2, nil, G)
				end
				B.box(Fk, C, "DoorHead", -2.4, 2.4, 20.4, 20.9, e, e + 0.4, TRIM2, nil, G)
				B.box(Fk, C, "Door", -2, 2, 14.7, 20.4, e, e + 0.12, WOOD, nil, G)
				B.box(Fk, C, "DoorMullion", -0.12, 0.12, 14.7, 20.4, e + 0.12, e + 0.3, TRIM2, nil, G)
				B.box(Fk, C, "WindowHead", -2.35, 2.35, 24.8, 25.25, e, e + 0.35, TRIM2, nil, G)
				B.box(Fk, C, "WallPanel", -2, 2, 21.8, 24.8, e, e + 0.1, STONE2, nil, G)
			else
				-- (18 Nov, main for the owner: "the bay boxes become part of the wall": this face is built out to where the
				-- bay window's front was, from over the arch to the ceiling, so the bay is the wall. side 8's keeps the hub
				-- egg's nook inside it: its walls and lid are HubRotundaCentre's, R.EGG_NICHE; here the floor and the rest)
				local hw, D1 = N[1] + 1.3, e + 6
				local FD1 = D1 + 0.4 -- (the built-out front)
				if k == R.EGG_SIDE then
					B.box(Fk, S, "OrielFloor", -hw, hw, 16.4, 17, e, FD1, STONE2) -- (the nook's floor; side 6's wall is solid)
					for _, sg in { -1, 1 } do B.box(Fk, S, "FaceMass", sg * hw, sg * (wo + 0.05), 16.4, ROOF, e, FD1, STONE) end
					B.box(Fk, S, "FaceMass", -hw, hw, N[3] + 1.5, ROOF, e, FD1, STONE) -- (over the nook's lid)
				else
					B.box(Fk, S, "FaceMass", -(wo + 0.05), wo + 0.05, 16.4, ROOF, e, FD1, STONE)
				end
				B.box(Fk, C, "FaceMassEdge", -(wo + 0.05), wo + 0.05, 16.1, 16.95, FD1, FD1 + 0.3, TRIM, nil, G)
				B.box(Fk, C, "StringCourse", -(wo + 0.05), wo + 0.05, 21.4 + o, 21.8 + o, FD1, FD1 + 0.25, TRIM, nil, G)
				B.box(Fk, C, "Frieze", -(wo + 0.05), wo + 0.05, 25.6 + o, 26 + o, FD1, FD1 + 0.5, TRIM, nil, G)
				B.box(Fk, C, "Cornice", -(wo + 0.05), wo + 0.05, 26 + o, 27.5 + o, FD1, FD1 + 1.2, TRIM, nil, G)
				-- where the window was: a tall wood panel in a pale frame
				B.box(Fk, C, "OrielPanel", -2.3, 2.3, 18, 21.3, FD1, FD1 + 0.1, WOOD, nil, G)
				B.box(Fk, C, "OrielPanel", -2.3, 2.3, 21.9, 23.4, FD1, FD1 + 0.1, WOOD, nil, G)
				for _, sg in { -1, 1 } do B.box(Fk, C, "OrielJamb", sg * 2.3, sg * 2.7, 17.6, 23.9, FD1, FD1 + 0.35, TRIM2, nil, G) end
				B.box(Fk, C, "OrielHead", -2.7, 2.7, 23.4, 23.9, FD1, FD1 + 0.35, TRIM2, nil, G)
				B.box(Fk, C, "OrielSill", -2.9, 2.9, 17.4, 18, FD1, FD1 + 0.55, TRIM, nil, G)
			end
		end

		-- the round room's piers between and beside the arches, from the courtyard: clean pilasters in world studs (as
		-- the arches are), base and cap, up to the cornice
		if B.warp then
			for i = 5, 8 do
				B.rigid(B.fr((i + 0.5) * 360 / R.N), 0, rcO, 0, function(Fl)
					local top = R.hmap(R.V3.H, 26)
					B.box(Fl, C, "PlazaPilaster", -2.45, 2.45, 0.4, top - 0.1, -1.6, 1, "8e877c", nil, G)
					B.box(Fl, C, "PlazaPilasterBase", -2.9, 2.9, -0.04, 1.3, -1.7, 1.5, "7a746a", nil, G)
					B.box(Fl, C, "PlazaPilasterCap", -2.9, 2.9, top - 0.2, top + 0.9, -1.7, 1.4, TRIM, nil, G)
				end)
			end
		end

		-- ---- the spawn rug in the courtyard, the middle arch straight ahead, a runner from the arch to it (and on, past
		-- the fountain, to the VIP door)
		local mid = 0
		for _, sp in R.SPAWNS do mid += sp[2] / #R.SPAWNS end
		B.cyl(F7, C, "SpawnRug", 0, -0.06, 0.04, mid, 2 * 6.4, P.creamHi, nil, G)
		B.cyl(F7, C, "SpawnRug", 0, -0.1, 0.08, mid, 2 * 5.9, "57514d", nil, G)
		B.cyl(F7, C, "RugRing", 0, -0.14, 0.12, mid, 2 * 5.3, ACCENT, Neon, G)
		B.cyl(F7, C, "SpawnRug", 0, -0.18, 0.16, mid, 2 * 5, "57514d", nil, G)
		local list = {}
		for _, sp in R.SPAWNS do
			local l = B.fr(0):PointToObjectSpace(F7 * Vector3.new(sp[1], 0, -sp[2]))
			table.insert(list, { l.X, -l.Z })
		end
		B.spawns(list, 0.16)
		local FD = 59 -- (the fountain's middle)
		for _, run in { { A + T + 0.2, mid }, { FD + 7.45, BACK - 0.3 } } do -- (the second from the fountain's floor ring on)
			B.paint(F7, "Runner", -2.2, 2.2, -0.05, run[1], run[2], P.carpet, 0.03)
			for _, s in { -1, 1 } do B.paint(F7, "RunnerEdge", s * 2.2, s * 2.6, -0.05, run[1], run[2], P.creamHi, 0.03) end
		end

		-- ---- the fountain: a round basin, a column and a bowl, water spilling from the bowl, and the duck on top (a
		-- stone duck now; until the plaza a hologram over a projector), a ring set in the floor round it
		B.cyl(F7, C, "FountainRing", 0, -0.06, 0.03, FD, 2 * 7.4, P.cream, nil, G)
		B.cyl(F7, C, "FountainRingFill", 0, -0.1, 0.07, FD, 2 * 6.9, P.floor2, nil, G)
		B.cyl(F7, C, "FountainBasin", 0, 0, 1.3, FD, 2 * 5.2, P.cream)
		B.cyl(F7, C, "FountainWater", 0, 1.22, 1.38, FD, 2 * 4.5, WATER, Enum.Material.Glass, { ghost = true, tr = 0.3 })
		local Fc = F7 * CFrame.new(0, 0, -FD)
		for k = 0, 15 do -- (the basin's coping: a ring of blocks, every other one 0.03 higher so no two tops share a plane)
			local Fk = Fc * CFrame.Angles(0, k * math.pi / 8, 0)
			local o = (k % 2) * 0.03
			local half = 4.85 * math.tan(math.pi / 16) + 0.03
			B.box(Fk, C, "FountainCoping", -half, half, 1.3 + o, 1.75 + o, 4.45, 5.25, P.creamHi, nil, G)
		end
		B.cyl(F7, C, "FountainColumn", 0, 1.3, 4.4, FD, 1.8, P.cream)
		B.cyl(F7, C, "FountainBowl", 0, 4.4, 5, FD, 2 * 2.4, P.creamHi, nil, G)
		B.cyl(F7, C, "FountainBowlWater", 0, 4.92, 5.08, FD, 2 * 2.05, WATER, Enum.Material.Glass, { ghost = true, tr = 0.3 })
		local spill = B.cyl(F7, C, "FountainSpill", 0, 4.6, 4.7, FD, 2 * 2.35, WATER, nil, { ghost = true, tr = 1 })
		do
			local pe = Instance.new("ParticleEmitter")
			pe.Name = "Spill"; pe.Rate = 45; pe.Lifetime = NumberRange.new(0.45, 0.6); pe.Speed = NumberRange.new(0.5, 1.2)
			pe.EmissionDirection = Enum.NormalId.Left -- (the part lies on its side: its -X face is down)
			pe.Acceleration = Vector3.new(0, -24, 0); pe.Size = NumberSequence.new(0.14); pe.LightEmission = 0.2
			pe.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0.8) })
			pe.Color = ColorSequence.new(Color3.fromHex("d8e6e8")); pe.Parent = spill
		end
		local duck = B.put(F7, "pj_duck", "FountainDuck", 0, 5.1, FD, 180, { scale = 6, raw = true }) -- (180: the model's own front is its back; it looks north, at the arches)
		if duck then
			for _, p in duck:GetDescendants() do
				if p:IsA("BasePart") then
					local dark = p.Color.R + p.Color.G + p.Color.B < 0.45 -- (its eyes stay dark)
					p.Color = if dark then Color3.fromHex("3a3d44") else Color3.fromHex(P.creamHi)
					p.Material = Enum.Material.SmoothPlastic; p.CanCollide = false
				end
			end
		end
		B.lamp(F7, 0, 9.2, FD, 16, 0.6, P.warm, { spot = true, angle = 60 })

		-- ---- two chandeliers on rods from the ceiling's roses, over the rug and over the fountain (18 Nov, main: "chunky and clearly
		-- chandeliers"): a big ring with candles and drops under it, a smaller ring over it with candles, a lantern in the
		-- middle, a warm light in each
		for ci, dc in { mid, FD } do
			local Fq = F7 * CFrame.new(0, 0, -dc)
			for _, t in { { 4.4, 18.6, 0.9, 16, 2 }, { 2.5, 21.2, 0.7, 12, 2 } } do
				local r, y0, h, n = t[1], t[2], t[3], t[4]
				for k = 0, n - 1 do
					local Fk = Fq * CFrame.Angles(0, k * 2 * math.pi / n, 0)
					local o = (k % 2) * 0.03
					local half = r * math.tan(math.pi / n) + 0.03
					B.box(Fk, C, "ChandelierRing", -half, half, y0 + o, y0 + h + o, r - 0.45, r + 0.45, TRIM, nil, G)
					if k % 2 == 0 then
						B.cyl(Fk, C, "Candle", 0, y0 + h, y0 + h + 0.9, r, 0.55, TRIM2, nil, G)
						B.cyl(Fk, C, "CandleFlame", 0, y0 + h + 0.9, y0 + h + 1.25, r, 0.34, P.warm, Neon, G)
					end
					if r > 3 then
						B.box(Fk, C, "ChandelierGlow", -half + 0.05, half - 0.05, y0 - 0.15 + o, y0 + o, r - 0.3, r + 0.3, "f0d6a8", Neon, G)
						if k % 2 == 1 then B.cyl(Fk, C, "ChandelierDrop", 0, y0 - 1.3, y0 - 0.15, r, 0.32, "e8eef0", Neon, G) end
						if k % 4 == 1 then B.box(Fk, C, "ChandelierSpoke", -0.22, 0.22, y0 + 0.3, y0 + 0.65, 0.8, r - 0.4, TRIM, nil, G) end
					end
				end
			end
			B.cyl(Fq, C, "ChandelierLantern", 0, 17.6, 21.9, 0, 1.7, TRIM2, nil, G)
			B.cyl(Fq, C, "ChandelierLanternGlow", 0, 18.4, 21.1, 0, 1.76, P.warm, Neon, { ghost = true, tr = 0.35 })
			B.cyl(Fq, C, "ChandelierFinial", 0, 16.9, 17.6, 0, 0.9, TRIM, nil, G)
			B.cyl(Fq, C, "ChandelierRod", 0, 21.9, ROOF - 0.4, 0, 0.5, "7a746a", nil, G)
			B.lamp(Fq, 0, 17.4, 0, 34, 0.6, P.warm, { shadows = ci == 2 })
		end

		-- ---- big trees in pots: two each side on the piers' lines, two either side of the way to the VIP door. (people-
		-- sized: world studs, B.rigid)
		local function tree(x, d, turn)
			B.rigid(F7, x, d, turn, function(Fl)
				B.cyl(Fl, C, "TreePot", 0, 0, 3, 0, 4.4, TRIM)
				B.cyl(Fl, C, "TreePotRim", 0, 2.8, 3.3, 0, 4.8, TRIM2, nil, G)
				B.cyl(Fl, C, "TreeSoil", 0, 3.05, 3.22, 0, 4, "4a4038", nil, G)
				for i = 0, 5 do B.cyl(Fl, C, "TreeTrunk", 0.06 * i, 3.2 + i * 1.25, 4.45 + i * 1.25, 0, 0.95 - i * 0.06, if i % 2 == 0 then "7a6450" else "6b5644", nil, G) end
				-- (each leaf a long blade from the crown, the low ones drooping, the high ones reaching up)
				for i, t in { { 0, -22, 6.2 }, { 45, -28, 5.8 }, { 90, -20, 6.4 }, { 135, -30, 5.6 }, { 180, -24, 6 }, { 225, -26, 5.8 }, { 270, -21, 6.2 }, { 315, -29, 5.6 },
					{ 20, 28, 4.6 }, { 110, 34, 4.4 }, { 200, 30, 4.8 }, { 290, 36, 4.2 } } do
					local Fb = Fl * CFrame.new(0, 10.6, 0) * CFrame.Angles(0, math.rad(t[1]), 0) * CFrame.Angles(math.rad(t[2]), 0, 0)
					B.box(Fb, C, "TreeLeaves", -0.6, 0.6, -0.09, 0.09, 0.3, t[3], LEAF[(i - 1) % 3 + 1], nil, G)
					B.box(Fb, C, "TreeLeaves", -0.08, 0.08, 0.09, 0.2, 0.3, t[3] - 0.4, "4f6a48", nil, G) -- (its rib)
				end
				B.ball(Fl, C, "TreeLeaves", 0, 10.6, 0, 1.5, LEAF[1], nil, G)
			end)
		end
		for _, s in { -1, 1 } do
			tree(s * 12.5, 39, 20 * s); tree(s * 12.5, 57, -35 * s); tree(s * PZ.PIERS_X[1], 64.5, 70 * s)
		end

		-- ---- seating in the lobby either side, between the trees: a rug with a border, a sofa with its back to the
		-- piers, two armchairs facing each other, a low table
		for _, s in { -1, 1 } do
			B.box(F7, C, "LobbyRug", s * 8.2, s * 16, -0.07, 0, 42.2, 53.8, "6f6052", nil, G) -- (its top 0.06 under the inner one's)
			B.box(F7, C, "LobbyRug", s * 8.6, s * 15.6, -0.06, 0.06, 42.6, 53.4, "4f4440", nil, G)
			B.put(F7, "bc_sofa", "LobbySofa", s * 16.3, 0, 48, -90 * s, { back = true, scale = 1.1, solid = true, color = seat })
			B.rigid(F7, s * 12, 48, 0, function(Fl) -- (a low wood table)
				B.box(Fl, C, "LobbyTable", -1.6, 1.6, 1.5, 1.85, -2.6, 2.6, WOOD, nil, G)
				for _, c in { { -1.3, -2.3 }, { 1.3, -2.3 }, { -1.3, 2.3 }, { 1.3, 2.3 } } do B.box(Fl, C, "LobbyTableLeg", c[1] - 0.15, c[1] + 0.15, 0, 1.5, c[2] - 0.15, c[2] + 0.15, WOOD2, nil, G) end
				B.solid("LobbyTableBox", Vector3.new(3.2, 1.85, 5.2), Fl * CFrame.new(0, 0.925, 0))
			end)
			for _, j in { -1, 1 } do B.put(F7, "bc_armchair", "LobbyArmchair", s * 10.6, 0, 48 + j * 4.6, if j < 0 then 180 else 0, { scale = 1.1, solid = true, color = seat }) end
		end

		-- ---- the arcades: a light panel and a lamp in each bay's ceiling, a dado and a ledge along the back walls, a
		-- cornice where they meet the ceiling
		local AX = (X + FW + OUT) / 2 -- (the side arcades' middle)
		local AD = (DS + FW + BACK) / 2 -- (the south one's)
		for _, s in { -1, 1 } do
			for k = 1, #PDs - 1 do
				local dc = (PDs[k] + PDs[k + 1]) / 2
				B.panel(F7, s * AX, BEAM, dc, 2.6, 6)
				B.lamp(F7, s * AX, BEAM - 2, dc, 20, 0.4, P.warm)
			end
			B.box(F7, C, "ArcadeDado", s * (OUT - 0.22), s * OUT, 0, 3.6, cd + 2, BACK, WOOD, Wood, G)
			B.box(F7, C, "ArcadeLedge", s * (OUT - 0.5), s * OUT, 3.6, 3.95, cd + 2, BACK, TRIM2, nil, G)
			B.box(F7, C, "ArcadeCornice", s * (OUT - 0.8), s * OUT, BEAM - 0.8, BEAM, cd + 2, BACK - 0.8, TRIM, nil, G)
			B.box(F7, C, "ArcadeDado", s * 3.3, s * (OUT - 0.22), 0, 3.6, BACK - 0.22, BACK, WOOD, Wood, G)
			B.box(F7, C, "ArcadeLedge", s * 3.3, s * (OUT - 0.5), 3.6, 3.95, BACK - 0.5, BACK, TRIM2, nil, G)
			B.box(F7, C, "ArcadeCornice", s * 3.3, s * OUT, BEAM - 0.8, BEAM, BACK - 0.8, BACK, TRIM, nil, G)
		end
		for k = 1, #PXs - 1 do
			local xc = (PXs[k] + PXs[k + 1]) / 2
			B.panel(F7, xc, BEAM, AD, 6, 2.6)
			if math.abs(xc) > 0.1 then B.lamp(F7, xc, BEAM - 2, AD, 20, 0.4, P.warm) end
		end

		-- every bay of the arcades' back walls a framed front (18 Nov, main: "the arcade bays at ground level should read
		-- as shopfronts or doorways into rooms ... each with its own framed entrance"): pilasters at its ends, a fascia
		-- with a warm lit band under it (no awnings: they are indoors); "shop" = a glazed front and a door, "window" = glazed
		-- (a seat stands in front of it), "frame" = only the frame, its fascia higher (the bundles' boards, the bar's back,
		-- the reception's board are its window)
		local function shopfront(Fb, w, kind)
			local hw = w / 2
			local f0 = if kind == "frame" then BEAM - 1.7 else BEAM - 2.6
			for _, s in { -1, 1 } do B.box(Fb, C, "ShopPilaster", s * (hw - 0.8), s * hw, -0.04, BEAM - 0.8, A - 0.45, A, STONE2, nil, G) end
			B.box(Fb, C, "ShopFascia", -hw + 0.8, hw - 0.8, f0, BEAM - 0.8, A - 0.55, A, TRIM, nil, G)
			B.box(Fb, C, "ShopLight", -hw + 1.1, hw - 1.1, f0 - 0.2, f0, A - 0.5, A - 0.2, LIT, Neon, G)
			if kind == "door" then -- (a wood door in a pale frame, no glass)
				B.box(Fb, C, "ShopDoor", -1.6, 1.6, 0.02, BEAM - 3.4, A - 0.3, A - 0.12, WOOD, nil, G)
				for _, y in { { 0.6, 4.2 }, { 4.7, BEAM - 3.9 } } do B.box(Fb, C, "DoorPanel", -1.3, 1.3, y[1], y[2], A - 0.38, A - 0.3, WOOD2, nil, G) end
				for _, s in { -1, 1 } do B.box(Fb, C, "ShopDoorJamb", s * 1.6, s * 2.05, 0.02, BEAM - 3, A - 0.4, A - 0.08, TRIM2, nil, G) end
				B.box(Fb, C, "ShopDoorHead", -2.05, 2.05, BEAM - 3.4, BEAM - 3, A - 0.45, A - 0.08, TRIM2, nil, G)
			end
			if kind == "shop" or kind == "window" then
				local g0, g1 = -hw + 1.3, hw - 1.3
				local lit = kind == "shop"
				B.box(Fb, C, "ShopSill", -hw + 0.8, hw - 0.8, -0.04, 1.2, A - 0.45, A, STONE2, nil, G)
				B.box(Fb, C, "ShopGlass", g0, g1, 1.2, BEAM - 3.2, A - 0.15, A, if lit then LIT else GLASS, if lit then Neon else nil, { ghost = true, tr = if lit then 0.25 else 0 })
				for _, x in { g0 + (g1 - g0) / 3, g0 + 2 * (g1 - g0) / 3 } do B.box(Fb, C, "ShopMullion", x - 0.14, x + 0.14, 1.2, BEAM - 3.2, A - 0.3, A - 0.15, TRIM2, nil, G) end
				B.box(Fb, C, "ShopTransom", g0, g1, BEAM - 3.6, BEAM - 3.3, A - 0.3, A - 0.15, TRIM2, nil, G)
				if kind == "shop" then
					B.box(Fb, C, "ShopDoor", -1.5, 1.5, 0.02, BEAM - 3.6, A - 0.35, A - 0.18, GLASS, nil, G)
					for _, s in { -1, 1 } do B.box(Fb, C, "ShopDoorJamb", s * 1.5, s * 1.85, 0.02, BEAM - 3.6, A - 0.4, A - 0.15, TRIM2, nil, G) end
				end
			end
		end
		local function backFrame(side, dc) -- (a side arcade's back wall, x along it; d = A its face)
			return F7 * CFrame.new(side * OUT, 0, -dc) * CFrame.Angles(0, -side * math.pi / 2, 0) * CFrame.new(0, 0, A)
		end
		for k = 1, #PDs - 1 do
			local dc = (PDs[k] + PDs[k + 1]) / 2
			shopfront(backFrame(1, dc), PDs[k + 1] - PDs[k] - 3, "frame") -- (west: the boutique's windows are its bundles' boards)
			shopfront(backFrame(-1, dc), PDs[k + 1] - PDs[k] - 3, "frame") -- (east: the lounge; its middle bay the bar. no glass: 18 Nov, "no windows")
		end
		for k = 1, #PXs - 1 do
			local xc = (PXs[k] + PXs[k + 1]) / 2
			if math.abs(xc) < 0.1 then continue end -- (the VIP door's own frame)
			shopfront(F7 * CFrame.new(xc, 0, -BACK) * CFrame.new(0, 0, A), PXs[k + 1] - PXs[k] - 3, if xc < 0 then "frame" else "door") -- (the reception east, the porter's door west)
		end

		-- ---- the west arcade: the showroom, three of the shop's bundles (slots 1, 2 and 4; 3 is on side 9 by the arches),
		-- each on a plinth in its bay in front of a dark board in a pale frame with a lit cove
		local function showFrame(Fq, plate, l1, l2)
			B.box(Fq, C, "ShowBoard", -4.2, 4.2, 0.7, 9.6, A - 0.8, A - 0.24, P.plate, nil, G)
			for _, s in { -1, 1 } do B.box(Fq, C, "ShowJamb", s * 4.2, s * 4.75, -0.04, 10.06, A - 1.05, A - 0.2, P.cream, nil, G) end
			B.box(Fq, C, "ShowHead", -4.75, 4.75, 9.6, 10.1, A - 1.35, A - 0.2, P.cream, nil, G)
			B.box(Fq, C, "ShowCove", -4, 4, 9.46, 9.6, A - 1.25, A - 1, P.strip, Neon, G)
			B.box(Fq, C, "ShowSill", -4.2, 4.2, 0.35, 0.7, A - 1, A - 0.26, P.pier, nil, G)
			if plate then B.text(Fq, plate, { { l1, P.glow, "S", 0.32 }, { l2, P.pale, "B", 0.58 } }, 6.4, 1.4, 0, 8.45, A - 0.8, 0, { flush = true, thick = 0.08, pps = 40 }) end
		end
		for k, slot in { 1, 2, 4 } do
			local dc = (PDs[k] + PDs[k + 1]) / 2
			local Fq = F7 * CFrame.new(OUT, 0, -dc) * CFrame.Angles(0, -math.pi / 2, 0) * CFrame.new(0, 0, A) -- (d = A: the back wall's face)
			showFrame(Fq, "ShowName" .. slot, "BUNDLE", "COMING SOON")
			local dP = A - 3.4
			B.cyl(Fq, C, "PlinthFoot", 0, 0, 0.35, dP, 4.6, P.pier)
			B.cyl(Fq, C, "Plinth", 0, 0.35, 1.5, dP, 4, P.cream)
			B.cyl(Fq, C, "PlinthTop", 0, 1.4, 1.53, dP, 3.6, P.floor2, nil, G)
			B.cyl(Fq, C, "PlinthRing", 0, 1.36, 1.57, dP, 3, P.glow, Neon, G)
			B.cyl(Fq, C, "PlinthInner", 0, 1.32, 1.61, dP, 2.6, P.floor2, nil, G)
			B.cyl(Fq, C, "PlinthLens", 0, 1.28, 1.65, dP, 0.9, P.glow, Neon, G)
			B.holo(Fq, "HoloBundle" .. slot, "bundle", 0, 5.2, dP, 2.5, 2.8, { slot = slot, base = 5.2 - 1.65, prompt = "View bundle" })
			B.lamp(Fq, 0, 9.2, A - 1.6, 11, 0.45, P.warm, { spot = true, angle = 70 })
		end

		-- ---- the east arcade, the lounge: seats in its first and last bays (a sofa on the wall, armchairs facing in, a low
		-- table, a round rug, a drop light), the bar in the middle one (a counter with stools, the fridge and shelves
		-- behind it), the arcade machine by the last bay's seats
		local SOFA_X = OUT - 0.55
		for _, k in { 1, #PDs - 1 } do
			local dc = (PDs[k] + PDs[k + 1]) / 2
			B.cyl(F7, C, "ArcadeRug", -24.2, -0.06, 0.04, dc, 7.2, "56504c", nil, G)
			B.put(F7, "bc_sofa", "ArcadeSofa", -SOFA_X, 0, dc, 90, { back = true, scale = 1.1, solid = true, color = seat })
			B.put(F7, R.prop("rk_coffeetable", "bc_coffeetable"), "ArcadeTable", -21.3, 0, dc, 90, { solid = true })
			for _, j in (if k == 1 then { 1 } else { -1 }) do B.put(F7, "bc_armchair", "ArcadeArmchair", -24.6, 0, dc + j * 5, if j < 0 then 180 else 0, { scale = 1.1, solid = true, color = seat }) end
			B.put(F7, "hb_droplight", "DropLight", -24.2, BEAM, dc, 0, { seat = "top", scale = 0.8, color = { fff1d6 = P.warm } })
		end
		local dg = (PDs[2] + PDs[3]) / 2
		local d3 = (PDs[#PDs - 1] + PDs[#PDs]) / 2
		local dA = cd + 2.25 -- (its back to the arcade's north wall)
		B.put(F7, "bc_arcade", "Arcade", -24, 0, dA, 180, { back = true, solid = true, color = { ff4fd8 = P.pier2, ffe14d = P.band, ["120818"] = P.pier } })
		local fridge = B.put(F7, "bc_fridge", "Fridge", -(OUT - 0.25), 0, dg + 3.4, 90, { back = true, solid = true })
		if fridge then B.unseam(fridge:FindFirstChild("fridge6__plastic_120818", true), 0.05, "bottom") end -- (its top was on the red body's)
		do -- the bar: a counter across the bay, stools in front, shelves on the wall behind (people-sized: world studs)
			local Fb = backFrame(-1, dg)
			for _, y in { 4.2, 6.6 } do B.box(Fb, C, "BarShelf", -3.6, 2.2, y, y + 0.3, A - 1.1, A - 0.2, TRIM, nil, G) end
			for i = 0, 5 do
				local bx = -3.2 + i * 0.95
				B.cyl(Fb, C, "Bottle", bx, 4.5, 5.6 + (i % 3) * 0.25, A - 0.65, 0.5, ({ "6f7a68", "8a7a62", "5d6470" })[i % 3 + 1], nil, G)
				B.cyl(Fb, C, "Bottle", bx + 0.4, 6.9, 7.8 + (i % 2) * 0.3, A - 0.65, 0.45, ({ "7a6a58", "68707c", "6f7a68" })[i % 3 + 1], nil, G)
			end
			B.lamp(Fb, 0, BEAM - 3, A - 1.5, 14, 0.5, P.warm, { spot = true, angle = 80 })
			B.rigid(F7, -(OUT - 4.6), dg, 90, function(Fl)
				B.box(Fl, C, "BarCounter", -5.6, 5.6, 0, 3.8, -0.9, 0.9, "6f675c")
				B.box(Fl, C, "BarTop", -6, 6, 3.8, 4.15, -1.25, 1.1, TRIM2, nil, G)
				B.box(Fl, C, "BarRail", -5.4, 5.4, 0.55, 0.75, -1.45, -1.25, "b59a5c", nil, G)
				B.box(Fl, C, "BarLine", -5.4, 5.4, 3.5, 3.62, -0.98, -0.9, ACCENT, Neon, G)
				for i = -2, 2 do
					B.cyl(Fl, C, "StoolFoot", i * 2.2, 0, 0.3, -2.6, 1.2, "6f675c", nil, G)
					B.cyl(Fl, C, "StoolStem", i * 2.2, 0.3, 2.4, -2.6, 0.3, "8e877c", nil, G)
					B.cyl(Fl, C, "StoolSeat", i * 2.2, 2.4, 2.8, -2.6, 1.5, "6d665d", nil, G)
				end
				B.solid("BarBox", Vector3.new(12, 4.15, 2.4), Fl * CFrame.new(0, 2.07, 0.05))
			end)
		end
		-- a regular (HubNPCs builds them at start): Looticus, the shop's man, on the first sofa; he puffs to either end of
		-- either sofa, behind the bar, to the arcade machine, or to the boutique behind a pier
		B.npc(F7, "Looticus", -(SOFA_X - 2.2), 1.75, (PDs[1] + PDs[2]) / 2 - 1.4, -90)
		local d1 = (PDs[1] + PDs[2]) / 2
		for k, w in { { "sit", -(SOFA_X - 2.2), 1.75, d1 - 1.4, -90 }, { "sit", -(SOFA_X - 2.2), 1.75, d1 + 1.6, -90 }, { "sit", -(SOFA_X - 2.2), 1.75, d3 - 1.4, -90 },
			{ "sit", -(SOFA_X - 2.2), 1.75, d3 + 1.6, -90 }, { "stand", -(OUT - 2.2), 0, dg, -90 }, { "stand", -23, 0, dA + 3.6, 180 }, { "stand", 25.2, 0, PDs[3], 90 } } do
			B.npcPoint(F7, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5])
		end

		-- ---- the south arcade: the reception desk in its east bay facing the courtyard (a long counter with rounded ends,
		-- a lamp on it, the one accent along its front), a board on the wall behind; two luggage carts in the west bay
		local xr = (PXs[1] + PXs[2]) / 2
		B.rigid(F7, xr, AD - 0.6, 0, function(Fl)
			B.box(Fl, C, "Desk", -5.5, 5.5, 0, 3.4, -0.9, 0.9, "6f675c")
			for _, s in { -1, 1 } do
				B.cyl(Fl, C, "DeskEnd", s * 5.5, 0.05, 3.35, 0, 1.8, "6f675c")
				B.cyl(Fl, C, "DeskTopEnd", s * 5.8, 3.45, 3.71, -0.1, 2.2, TRIM2, nil, G)
			end
			B.box(Fl, C, "DeskTop", -5.8, 5.8, 3.4, 3.75, -1.2, 1, TRIM2, nil, G)
			B.box(Fl, C, "DeskFront", -5.1, 5.1, 0.45, 3.0, -1.0, -0.9, "8a8174", nil, G)
			B.box(Fl, C, "DeskKick", -5.3, 5.3, 0, 0.35, -0.98, -0.9, "57534d", nil, G)
			B.box(Fl, C, "DeskLine", -5.1, 5.1, 3.12, 3.24, -1.06, -1.0, ACCENT, Neon, G)
			B.cyl(Fl, C, "DeskLampFoot", 3.6, 3.75, 4, 0.2, 0.7, P.pier, nil, G)
			B.cyl(Fl, C, "DeskLampStem", 3.6, 4, 5, 0.2, 0.22, P.pier, nil, G)
			B.ball(Fl, C, "DeskLampShade", 3.6, 5.3, 0.2, 1.1, P.warm, Neon, G)
			B.lamp(Fl, 3.6, 5.3, 0.2, 10, 0.5, P.warm)
		end)
		do
			local Fr = F7 * CFrame.new(xr, 0, -BACK) * CFrame.new(0, 0, A) -- (d = A: the back wall's face)
			showFrame(Fr)
			for _, y in { 3.6, 6.1 } do B.box(Fr, C, "BoardShelf", -4.2, 4.2, y, y + 0.25, A - 1.2, A - 0.8, TRIM, nil, G) end
			B.lamp(Fr, 0, 9.2, A - 1.6, 11, 0.45, P.warm, { spot = true, angle = 70 })
		end
		-- (the corner where the east and south arcades meet is kept clear: the lore code panel's place, R.CODE_SPOT. a
		-- warm light over it)
		B.lamp(F7, -(X + FW + OUT) / 2, BEAM - 2, (DS + FW + BACK) / 2, 18, 0.5, P.warm)
		local function cart(x, d, turn)
			B.rigid(F7, x, d, turn, function(Fl)
				B.box(Fl, C, "CartBed", -1.7, 1.7, 0.55, 0.8, -0.95, 0.95, P.pier)
				for _, a in { { -1.3, -0.7 }, { 1.3, -0.7 }, { -1.3, 0.7 }, { 1.3, 0.7 } } do
					local wh = B.box(Fl, C, "CartWheel", a[1] - 0.12, a[1] + 0.12, 0, 0.5, a[2] - 0.25, a[2] + 0.25, P.plate, nil, G)
					wh.Shape = Enum.PartType.Cylinder
				end
				for _, s in { -1, 1 } do B.cyl(Fl, C, "CartPost", s * 1.5, 0.8, 4.5, 0, 0.26, P.creamHi, nil, G) end
				local bar = B.box(Fl, C, "CartBar", -1.5, 1.5, 4.38, 4.62, -0.12, 0.12, P.creamHi, nil, G)
				bar.Shape = Enum.PartType.Cylinder
				B.box(Fl, C, "Suitcase", -1.2, 0.5, 0.8, 2.1, -0.65, 0.6, "6a6460", nil, G)
				B.box(Fl, C, "Suitcase", -0.9, 0.7, 2.1, 3.0, -0.5, 0.45, "586170", nil, G)
				B.box(Fl, C, "Suitcase", 0.65, 1.3, 0.8, 1.7, -0.45, 0.4, "8a7f72", nil, G)
			end)
		end
		local xw = (PXs[#PXs - 1] + PXs[#PXs]) / 2
		cart(xw - 2.4, AD - 0.8, 18); cart(xw + 2.6, AD + 0.6, -14)

		-- ---- the VIP room behind the south arcade: its door in the arcade's back wall, on the axis
		vipRoom(F7 * CFrame.new(0, 0, -(BACK - 60)))
	end

	-- ------------------------------------------------------------ the lounge (side 7, due south)
	-- (18 Nov 2026, the owner: "Can the current lounge be turned into a part of a larger lounge where players will now spawn
	-- making the central [room] feel more spacious!!". the small warm lounge, everything in it, is the middle bay of a big
	-- one now, moved R.LOUNGE_S further out with the VIP room behind it (frame F below: its numbers as they were): its
	-- walls and hall gone, its low ceiling kept as a timber canopy on two posts and the far wall. round it the big room
	-- (frame F7): as wide as the round room, open onto it through the three arches of sides 6, 7 and 8
	-- (HubRotundaCentre), your spawn rug on its front floor (R.SPAWNS), the showroom's plinths down its west wall, seats
	-- along its east wall, timber beams and white panels under a high ceiling)
	if R.LOUNGE_STYLE == "plaza" then plaza(vipRoom) else do
		local F7 = B.side(7)
		local LS, LX, LH = R.LOUNGE_S, R.LOUNGE_X, R.LOUNGE_H
		local F = F7 * CFrame.new(0, 0, -LS)
		local FAR = 60 + LS -- the far wall's face (the VIP door's), in F7
		local ACCENT = P.doorGlow or P.glow
		local seat = { ["3b2a52"] = P.creamHi, ff4fd8 = P.band }
		do
			local wo = B.wid(A + T) / 2 -- (a side's outer half width: where an arch's side meets the lounge's)
			local rcO = (A + T) / math.cos(math.pi / R.N)
			local cx, cd = rcO * math.sin(3 * math.pi / R.N), rcO * math.cos(3 * math.pi / R.N) -- the round room's corner between the arches' sides and 5 / 9
			local FLOOR, WALL, LID = "4a4542", P.brick, P.shell2
			-- the floor: the front (its top under the round room's floor and the arches' thresholds), each side's front and
			-- wing; the bay keeps its own carpet (below)
			-- (its top 0.05 under the round room's floor, which lies over its front: no faces within 0.02)
			B.box(F7, S, "LoungeFloor", -cx, cx, -2, -0.05, cd - 1, 36 + LS, FLOOR)
			for _, s in { -1, 1 } do
				B.box(F7, S, "LoungeFloor", s * cx, s * (LX + 2), -2, -0.05, cd, 36 + LS, FLOOR)
				B.box(F7, S, "LoungeFloor", s * 16, s * (LX + 2), -2, -0.05, 36 + LS, FAR + 2, FLOOR)
			end
			-- the walls: each side's, a short one each side of the arches into the round room's corner, the far wall either
			-- side of and over the VIP door
			for _, s in { -1, 1 } do
				B.box(F7, S, "LoungeWall", s * LX, s * (LX + 2), 0, LH, cd, FAR + 2, WALL, Brick)
				B.box(F7, S, "LoungeWall", s * (cx - 0.6), s * LX, 0, LH, cd, cd + 2, WALL, Brick)
				B.box(F7, S, "LoungeWall", s * 2.45, s * LX, 0, LH, FAR, FAR + 2, WALL, Brick)
			end
			B.box(F7, S, "LoungeWall", -2.45, 2.45, 9.15, LH, FAR, FAR + 2, WALL, Brick)
			-- the ceiling: from the round room's wall face out, each side's front, and the triangle over the floor in front of
			-- an arch's side (a wedge laid flat: its slope on the round room's wall)
			B.box(F7, S, "LoungeLid", -(LX + 2), LX + 2, LH, LH + 1, A + T, FAR + 2, LID)
			for _, s in { -1, 1 } do
				B.box(F7, S, "LoungeLid", s * cx, s * (LX + 2), LH, LH + 1, cd, A + T, LID)
				local w = B.box(F7, S, "LoungeLidCorner", 0, 1, LH, LH + 1, cd, A + T, LID, nil, { wedge = true })
				local vY, vZ = Vector3.new(-s, 0, 0), Vector3.new(0, 0, -1)
				w.Size = Vector3.new(1, cx - wo, A + T - cd)
				w.CFrame = F7 * CFrame.fromMatrix(Vector3.new(s * (cx + wo) / 2, LH + 0.5, -(cd + A + T) / 2), vY:Cross(vZ), vY, vZ)
			end
			-- the walls' trim: a wood dado to hand height and a pale ledge along each side wall and the far wall's wings, a
			-- cream cornice under the ceiling all round
			for _, s in { -1, 1 } do
				B.box(F7, C, "LoungeDado", s * (LX - 0.22), s * LX, 0, 3.6, cd + 2, FAR, P.wood, Wood, G)
				B.box(F7, C, "LoungeLedge", s * (LX - 0.5), s * LX, 3.6, 3.95, cd + 2, FAR, P.creamHi, nil, G)
				B.box(F7, C, "LoungeDado", s * 16.4, s * (LX - 0.22), 0, 3.6, FAR - 0.22, FAR, P.wood, Wood, G)
				B.box(F7, C, "LoungeLedge", s * 16.4, s * (LX - 0.5), 3.6, 3.95, FAR - 0.5, FAR, P.creamHi, nil, G)
				B.box(F7, C, "LoungeCornice", s * (LX - 0.8), s * LX, LH - 0.8, LH, cd + 2, FAR - 0.8, P.cream, nil, G)
				B.box(F7, C, "LoungeCornice", s * cx, s * (LX - 0.8), LH - 0.8, LH, cd + 2, cd + 2.8, P.cream, nil, G)
			end
			B.box(F7, C, "LoungeCornice", -LX, LX, LH - 0.8, LH, FAR - 0.8, FAR, P.cream, nil, G)
			-- (18 Nov, the owner: "can you fix the back side of this to make it look presentable": the round room's three
			-- faces seen from the lounge get the lounge's cornice carried across, a band over the arches, and a clean
			-- pilaster over each of the round room's piers between and beside the arches, in world studs in Hub v3 as the
			-- arches are, HubRotundaCentre)
			for _, k in { 6, 7, 8 } do
				local Fk = B.side(k)
				local o = if k == 7 then 0 else 0.05 -- (the corners where two faces' trim meets: not in one plane)
				B.box(Fk, C, "LoungeCornice", -(wo + 0.15), wo + 0.15, LH - 0.8 - o, LH - o, A + T, A + T + 0.8, P.cream, nil, G)
				B.box(Fk, C, "ArchBand", -(wo + 0.1), wo + 0.1, 12 + o, 12.6 + o, A + T, A + T + 0.35, P.cream, nil, G)
			end
			if B.warp then
				for i = 5, 8 do
					B.rigid(B.fr((i + 0.5) * 360 / R.N), 0, rcO, 0, function(Fl)
						local band = R.hmap(R.V3.H, 12)
						B.box(Fl, C, "LoungePilaster", -2.45, 2.45, 0.4, R.hmap(R.V3.H, LH - 0.8), -1.6, 1, P.pier2, nil, G)
						B.box(Fl, C, "LoungePilasterBase", -2.9, 2.9, -0.04, 1.3, -1.7, 1.5, P.pier, nil, G)
						B.box(Fl, C, "LoungePilasterCap", -2.9, 2.9, band - 0.2, band + 0.9, -1.7, 1.4, P.cream, nil, G)
					end)
				end
			end
			-- timber beams across under the ceiling (one in front of the bay's canopy, two over each wing), white panels
			-- between them, the lights
			B.box(F7, C, "LoungeBeam", -(LX - 0.8), LX - 0.8, LH - 1.4, LH, 39.6, 40.8, P.beam, Wood, G)
			for _, s in { -1, 1 } do
				for _, d in { 52, 64 } do B.box(F7, C, "LoungeBeam", s * 16.6, s * (LX - 0.8), LH - 1.4, LH, d - 0.6, d + 0.6, P.beam, Wood, G) end
				B.panel(F7, s * 16, LH, 34.6, 7, 3.4)
				for _, d in { 46, 58 } do
					B.panel(F7, s * 22.2, LH, d, 4, 7)
					B.lamp(F7, s * 22.2, LH - 2.5, d, 22, 0.55, P.warm)
				end
			end
			B.panel(F7, 0, LH, 34.6, 7, 3.4)
			B.lamp(F7, 0, LH - 2, 35, 26, 0.8, P.light)
			-- where you appear: a round rug on the front floor, a ring of the accent in it, the spawn points on it looking out
			-- through the middle arch (Hub.HubSpawns; R.SPAWNS in this frame, B.spawns wants the north frame)
			local mid = 0
			for _, sp in R.SPAWNS do mid += sp[2] / #R.SPAWNS end
			B.cyl(F7, C, "SpawnRug", 0, -0.06, 0.04, mid, 2 * 6.4, P.creamHi, nil, G)
			B.cyl(F7, C, "SpawnRug", 0, -0.1, 0.08, mid, 2 * 5.9, "57514d", nil, G)
			B.cyl(F7, C, "RugRing", 0, -0.14, 0.12, mid, 2 * 5.3, ACCENT, Neon, G)
			B.cyl(F7, C, "SpawnRug", 0, -0.18, 0.16, mid, 2 * 5, "57514d", nil, G)
			local list = {}
			for _, sp in R.SPAWNS do
				local l = B.fr(0):PointToObjectSpace(F7 * Vector3.new(sp[1], 0, -sp[2]))
				table.insert(list, { l.X, -l.Z })
			end
			B.spawns(list, 0.16)
			-- a big planter in each front corner
			for _, s in { -1, 1 } do
				B.put(F7, R.prop("rk_planter", "bc_plantbig"), "Planter", s * 25.2, 0, cd + 4.8, 0, { scale = R.propScale("rk_planter", 1.1, 0.65), solid = true, color = GREEN })
			end
			-- the showroom (west, x > 0): three of the shop's bundles on plinths down the wall (slots 1, 2 and 4; 3 is on side
			-- 9 by the arches), each in front of a dark board in a pale frame with a lit cove, as the round room's were
			local function showFrame(Fq, plate, l1, l2)
				B.box(Fq, C, "ShowBoard", -4.2, 4.2, 0.7, 9.6, A - 0.8, A - 0.24, P.plate, nil, G)
				for _, s in { -1, 1 } do B.box(Fq, C, "ShowJamb", s * 4.2, s * 4.75, -0.04, 10.06, A - 1.05, A - 0.2, P.cream, nil, G) end
				B.box(Fq, C, "ShowHead", -4.75, 4.75, 9.6, 10.1, A - 1.35, A - 0.2, P.cream, nil, G)
				B.box(Fq, C, "ShowCove", -4, 4, 9.46, 9.6, A - 1.25, A - 1, P.strip, Neon, G)
				B.box(Fq, C, "ShowSill", -4.2, 4.2, 0.35, 0.7, A - 1, A - 0.26, P.pier, nil, G)
				B.text(Fq, plate, { { l1, P.glow, "S", 0.32 }, { l2, P.pale, "B", 0.58 } }, 6.4, 1.4, 0, 8.45, A - 0.8, 0, { flush = true, thick = 0.08, pps = 40 })
			end
			for _, e in { { 1, 37.5 }, { 2, 48.5 }, { 4, 59.5 } } do
				local slot = e[1]
				local Fq = F7 * CFrame.new(LX, 0, -e[2]) * CFrame.Angles(0, -math.pi / 2, 0) * CFrame.new(0, 0, A) -- (d = A: the wall's face)
				showFrame(Fq, "ShowName" .. slot, "BUNDLE", "COMING SOON")
				local dP = A - 3.4
				B.cyl(Fq, C, "PlinthFoot", 0, 0, 0.35, dP, 4.6, P.pier)
				B.cyl(Fq, C, "Plinth", 0, 0.35, 1.5, dP, 4, P.cream)
				B.cyl(Fq, C, "PlinthTop", 0, 1.4, 1.53, dP, 3.6, P.floor2, nil, G)
				B.cyl(Fq, C, "PlinthRing", 0, 1.36, 1.57, dP, 3, P.glow, Neon, G)
				B.cyl(Fq, C, "PlinthInner", 0, 1.32, 1.61, dP, 2.6, P.floor2, nil, G)
				B.cyl(Fq, C, "PlinthLens", 0, 1.28, 1.65, dP, 0.9, P.glow, Neon, G)
				B.holo(Fq, "HoloBundle" .. slot, "bundle", 0, 5.2, dP, 2.5, 2.8, { slot = slot, base = 5.2 - 1.65, prompt = "View bundle" })
				B.lamp(Fq, 0, 9.2, A - 1.6, 11, 0.45, P.warm, { spot = true, angle = 70 })
			end
			-- the seats (east, x < 0): two groups, each a long sofa on the wall, two armchairs facing it over a low table on a
			-- round rug, a drop light over the table
			for _, dc in { 44.5, 58.5 } do
				B.cyl(F7, C, "WingRug", -22.4, -0.06, 0.04, dc, 11, "56504c", nil, G)
				B.put(F7, "bc_sofa", "WingSofa", -(LX - 0.55), 0, dc, 90, { back = true, scale = 1.1, solid = true, color = seat })
				B.put(F7, R.prop("rk_coffeetable", "bc_coffeetable"), "WingTable", -22.4, 0, dc, 90, { solid = true })
				for _, k in { -1, 1 } do
					B.put(F7, "bc_armchair", "WingArmchair", -18.4, 0, dc + k * 3.2, -90 + k * 20, { scale = 1.1, solid = true, color = seat })
				end
				B.put(F7, "hb_droplight", "DropLight", -22.4, LH, dc, 0, { seat = "top", scale = 0.9, color = { fff1d6 = P.warm } })
				B.lamp(F7, -22.4, LH - 5.5, dc, 18, 0.7, P.warm)
			end
		end
		-- THE BAY: the old lounge, as it was (its floor, the beams, the seats, the duck), its lid now a canopy over it with a
		-- timber edge, on two posts at its open front and the far wall
		B.box(F, S, "LoungeFloor", -16, 16, -1.9, -0.05, 36, 62, P.carpet) -- (its underside off the VIP floor's)
		B.box(F, S, "LoungeLid", -16, 16, 11, 12, 36, 61.9, P.shell2) -- (its end inside the far wall, not on its face)
		B.box(F, C, "CanopyEdge", -16.4, 16.4, 10.3, 12.4, 35.6, 36, P.beam, Wood, G)
		for _, s in { -1, 1 } do
			B.box(F, C, "CanopyEdge", s * 16, s * 16.4, 10.3, 12.4, 36, 60, P.beam, Wood, G)
			B.box(F, S, "CanopyPost", s * 14.8, s * 16.3, 0, 11, 36, 37.6, P.beam, Wood) -- (up to the canopy; inside its edge's face)
		end
		B.lamp(F, 0, 9.2, 34.5, 12, 0.8, P.warm)
		-- the raised wooden border the seats stand on, with a dark nosing; the middle stays sunk
		local function step(x0, x1, d0, d1) B.box(F, S, "LoungeStep", x0, x1, -0.02, 0.6, d0, d1, P.wood, Wood) end
		step(-14, -8, 41, 60); step(8, 14, 41, 60); step(-8, 8, 54, 60)
		for _, s in { -1, 1 } do B.paint(F, "StepNose", s * 8, s * 8.5, 0.6, 41, 54, P.pier, 0.01) end
		B.paint(F, "StepNose", -8.5, 8.5, 0.6, 54, 54.5, P.pier, 0.01)
		-- timber beams across, a dark pier under each end, the corners of the room cut
		for _, d in { 43, 49, 55 } do
			B.box(F, C, "Beam", -14, 14, 9.9, 11, d - 0.6, d + 0.6, P.beam, Wood, G)
			for _, s in { -1, 1 } do B.box(F, C, "LoungePier", s * 13.3, s * 14.06, 0.6, 9.9, d - 0.7, d + 0.7, P.pier, nil, G) end -- (proud of the rail behind the seats, now that no wall hides their backs)
		end
		-- (its cut corners went with its walls, 18 Nov)
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
		local fridge = B.put(F, "bc_fridge", "Fridge", -10.6, 0.6, 56.6, 45, { solid = true })
		if fridge then B.unseam(fridge:FindFirstChild("fridge6__plastic_120818", true), 0.05, "bottom") end -- (its top was on the red body's)
		-- (no "WEAPONS HOLSTERED" sign: the HUD says so, and the owner wants no flavour text)
		-- a regular (HubNPCs builds them at start): Looticus on the east sofa, at its door end, looking over at the duck.
		-- (the seat's top on the sofa's cushion: its fabric starts at 1.92, the cushion's top about 2.45)
		B.npc(F, "Looticus", 11.2, 2.35, 46.6, 90)
		-- where he puffs to: either end of either sofa, or standing on the sunk floor in front of the arcade or the fridge
		-- (clear of the armchairs by the VIP door and of the raised border's edge: R.check stands a body on each)
		for k, w in { { "sit", 11.2, 2.35, 46.6, 90 }, { "sit", 11.2, 2.35, 49.6, 90 }, { "sit", -11.2, 2.35, 46.6, -90 }, { "sit", -11.2, 2.35, 49.6, -90 }, { "stand", 6.5, 0, 51.8, -60 }, { "stand", -6.5, 0, 51.8, 60 } } do
			B.npcPoint(F, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5])
		end
		-- (18 Nov) and, the shop's man, by the showroom: between its second and third plinths, looking into the lounge
		B.npcPoint(F7, "Looticus", 7, "spot", "stand", 21, 0, 54, 90)

		vipRoom(F)
	end end

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
		-- a regular (R.NPCS; HubNPCs builds them at start): Dune, the quests guy, walking round three sides of the ring and
		-- back (the aisles either side and behind it; on the door's side the ring's corners and the benches leave less
		-- room than he is wide), pausing at the weights, behind the ring and at the bags, always facing the ring there.
		-- the walk stays clear of the posts, the benches, the bags and the tyres (R.check sweeps his body along it)
		B.npc(F, "Dune", 11.9, 0, 58, 90)
		for k, w in { { "stop", 11.9, 58, 90 }, { "via", 11.9, 70.4, 0 }, { "stop", 0, 71.6, 180 }, { "via", -12, 71, 0 }, { "stop", -13, 58, -90 } } do
			B.npcPoint(F, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil })
		end

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
		-- (18 Nov: the sawn-off's hinge lies 0.014 under and 0.017 over its frame in the kit model: thinned on show here)
		local saw = B.root.Scenery:FindFirstChild("Rack_w_sawnoff")
		if saw then B.unseam(saw:FindFirstChild("hinge_wzB__dark", true), 0.06) end
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
		-- the gate: a chunky frame on the far wall and in it the gate's kit, the same on the training side (GateKit; owner,
		-- 17 Nov: "can the laser fence be on both side of the hub and same with the garage door because its weird to have
		-- the grid on one side and a garage door on the other"): a roll-up garage door with the laser fence just inside it.
		-- walk up and the door rolls up, then the lasers click off (owner, 16 Nov: "when you get close you hear a click and
		-- the laser gate turns off"); walk in and you are in the training ground
		local GK = require(game.ServerStorage.PolishBackup.GateKit:Clone())
		B.put(F, "hb_portal", "TrainingPortal", 0, 0, 64, 0, { back = true, scale = GK.FRAME.scale, color = GK.FRAME.color })
		GK.build(F * CFrame.new(0, 0, -62.2), B.root.Scenery, { door = "TrainingShutter", lasers = "TrainingLaserGate" })
		B.lamp(F, 0, GK.LAMP.up, 62.2 - GK.LAMP.out, GK.LAMP.range, GK.LAMP.bright, GK.LAMP.hex)
		-- (no sign over the gate: the round room's word TRAINING names this way, and the HUD names the place on entry)
		B.trigger(F, R.ROOM .. "ToTraining", -3.9, 3.9, 0, 10, 60.6, 63.2, "@TrainSpawns", "TRAINING GROUND")
		-- (where the training hall's door lands you: on the round room's floor just inside the armory's hatch, looking
		-- north at the lifts. in the armory itself you arrived facing its gun wall: the tester, 16 Nov)
		for _, b in { 244, 252, 260 } do B.arrive(B.fr(b), { { 0, 20 } }, 0, 0) end
	end
end
