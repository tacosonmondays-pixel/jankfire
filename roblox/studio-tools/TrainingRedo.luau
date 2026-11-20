--!nocheck
-- TRAINING v4 (20 Nov 2026). The owner: "we also redo training hub entirely basing it off the overwatch training hub in a
-- way? keep shooting range ... the gun shop eveyrthing else good to change, dummy area, shooting range, course outside
-- teleporter to parkour", and "have a room with a course that teraches you how to use each gun ... a button you press
-- it, it pulls up a menu with all the weapons select one, and itll place a small course or shooting thingyu dpeending on
-- what you picked". The kind of place is a hero shooter's practice range (open, bright, readable); nothing of any game's
-- layout or look is copied. The plan sheet: roblox/docs/training/training_redo_plan.jpg.
--
-- This module wraps PolishBackup.TrainingRooms (v3): TrainingV2 loads it when T.ROOMS == "v4" and calls its apply and
-- build in v3's place.
--   * the dummies hall and the course hall stand open to the sky (v3's OPEN switch): the deep beams stay as an open
--     frame, an unseen lid at the walls' tops keeps everyone in. Their footprints are v3's, so the back lot's garage door,
--     the TOP door (the egg door), the gold Carls and the lot panel stay exactly where they are
--   * a doorway in the course hall's west wall (v3's WESTDOOR) opens into the TUTORIAL WING: a corridor along the course
--     hall's west side and four private rooms off its back side. Walk into a free room and it is yours; its console
--     opens the menu of every weapon, and the room rebuilds as that weapon's course (server/Tutorials.server.luau runs
--     them; shared/TutorialData.luau is one table per weapon)
-- What the game reads in each room (TrainingGround.Tutorial.Room<n>): Zone (its inside, a box), Origin (the floor
-- point at its mouth, looking into the room: courses are laid out from it), Console (with a Prompt), DoorLamp (the
-- strip over its mouth: the server colours it free or taken), DoorBlock (the mouth: each client makes it solid for
-- itself while the room is someone else's), Board (the back wall's screen; the client paints it).
local W = {}
local V3, CF = Vector3.new, CFrame.new
local T, K, P, R3, H, B
local Y0

-- ---------------------------------------------------------------- the plan (world coordinates, y up)
-- the corridor runs west from the course hall's west wall; the rooms open off its back side (toward the lot)
local WING = {
	x0 = -320, x1 = -136,              -- the corridor's inside (x1 = the course hall's west wall's outer face)
	cz0 = -8112, cz1 = -8136,          -- the corridor's inside, front (hub side) to back
	ceil = 256,                        -- the corridor's ceiling
	rz0 = -8140, rz1 = -8250,          -- each room's inside, its mouth wall to its back wall
	rtop = 272,                        -- the rooms' ceiling (their lit ceiling's underside is lower: beams)
	pierTop = 266,
}
WING.ROOMS = {}
for i = 1, 4 do
	local x0 = -320 + (i - 1) * 44
	WING.ROOMS[i] = { x0 = x0, x1 = x0 + 40, xm = x0 + 20 }
end
-- the rooms' beams across the ceiling (no piers down the walls: v4.1, the first photo read as a tunnel of piers; a
-- tutorial room is a clean box the hologram course stands in, its walls panelled flat)
WING.FR = { -8167.5, -8195, -8222.5 }
WING.SEAM = 13.75 -- the wall panels' width (8 down a room)
WING.MOUTH = { half = 6, top = 252 }  -- each room's mouth from the corridor
WING.WESTDOOR = { z0 = -8120, z1 = -8132, top = 251 } -- the course hall's west doorway: under the walk, clear of its brackets (-8118, -8134)
WING.CONSOLE = { dx = -12, z = -8148 } -- the console: left of the way in (facing in, +x is the right), 8 in
WING.FLOOR = "4a4f58"                 -- the rooms' floor (P.board): dark, so the hologram courses read on it
WING.GRID = "575d67"                  -- the projected grid's lines: a step lighter, no colour
WING.ACCENT = "8fd8cf"                -- the one accent: the tutorial's hologram tint (pale teal) on the lamp strip and the lens
W.WING = WING

local function blk(...) return H.blk(...) end

-- ---------------------------------------------------------------- the wing
local function corridor()
	local x0, x1, z0, z1 = WING.x0, WING.x1, WING.cz0, WING.cz1
	local top = WING.ceil + 2
	blk("Shell", "WingFloor", x0, x1, 236, Y0, z0, z1, P.floor)
	-- walls: the front (hub side), the back (the rooms' front, with their mouths), the west end
	blk("Shell", "WingWallF", x0 - 4, x1, 234, top, z0 + 4, z0, P.courseWall)
	blk("Shell", "WingWallEnd", x0 - 4, x0, 234, top, z0, z1, P.courseWall)
	local edges = { x0 - 4 }
	for _, r in WING.ROOMS do table.insert(edges, r.xm - WING.MOUTH.half); table.insert(edges, r.xm + WING.MOUTH.half) end
	table.insert(edges, x1)
	for i = 1, #edges - 1, 2 do blk("Shell", "WingWallB", edges[i], edges[i + 1], 234, top, z1, z1 - 4, P.courseWall) end
	for _, r in WING.ROOMS do
		local a, b = r.xm - WING.MOUTH.half, r.xm + WING.MOUTH.half
		blk("Shell", "MouthHead", a, b, WING.MOUTH.top, top, z1, z1 - 4, P.courseWall)
		blk("Shell", "MouthSill", a, b, 236, Y0, z1, z1 - 4, P.floor2)
		-- the white noses round the mouth, both faces
		for _, z in { z1 + 0.1, z1 - 4.1 } do
			for _, x in { a, b } do
				B.part("Shell", "MouthNose", CF(x, (Y0 + WING.MOUTH.top) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), V3(WING.MOUTH.top - Y0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
			end
			B.part("Shell", "MouthNose", CF(r.xm, WING.MOUTH.top, z), V3(b - a + 1.4, 1.4, 1.4), P.trim, { cyl = true })
		end
	end
	blk("Shell", "WingCeiling", x0 - 4, x1, WING.ceil, top, z0 + 4, z1 - 4, P.ceil)
	-- the rooms' front wall above the corridor's roof (the rooms stand 16 taller: the live check found the gap)
	blk("Shell", "RoomsFront", x0 - 4, x1, top, WING.rtop + 2, z1, z1 - 4, P.courseWall)
	-- bones: piers on the front wall facing each room's mouth and between, the dado and band, beams across over them,
	-- lit panels between the beams
	local xs = {}
	for _, r in WING.ROOMS do table.insert(xs, r.xm - 22) end
	table.insert(xs, x1 - 2)
	for _, x in xs do
		blk("Shell", "Pier", x - 1.6, x + 1.6, Y0, WING.ceil - 2, z0, z0 - 2, P.pier)
		blk("Shell", "PierBase", x - 1.85, x + 1.85, Y0, Y0 + 1.3, z0, z0 - 2.25, P.deep)
		blk("Shell", "RoofBeam", x - 1.3, x + 1.3, WING.ceil - 2, WING.ceil, z0, z1, P.pier)
	end
	H.endWall(z0, -1, x0, x1, Y0)
	-- the band on the back wall stops at each mouth
	for i = 1, #edges - 1, 2 do
		blk("Shell", "Dado", math.max(edges[i], x0), edges[i + 1], Y0, Y0 + 1.2, z1, z1 + 0.2, P.floor2, { ghost = true })
	end
	for _, r in WING.ROOMS do
		local cx = r.xm - 11
		blk("Scenery", "CeilingPanel", cx - 7, cx + 7, WING.ceil - 0.32, WING.ceil - 0.2, z0 - 3, z1 + 3, P.panel, { ghost = true, mat = Enum.Material.Neon })
		B.lamp(r.xm, WING.ceil - 3, (z0 + z1) / 2, "point", 28, 0.5, P.lampWhite)
	end
	-- the wing's word over its way in, on the course side of the doorway: no, the doorway speaks for itself; the rooms'
	-- numbers over their mouths, and each mouth's lamp strip
	local tut = K.folderIn(B.root, "Tutorial")
	for i, r in WING.ROOMS do
		local room = K.folderIn(tut, "Room" .. i)
		B.text("RoomNumber", { { tostring(i), P.pale, "B", 1 } }, 3, 3, CF(r.xm, WING.MOUTH.top + 2.6, z1 + 0.06) * CFrame.Angles(0, math.pi, 0), { plate = P.board, thick = 0.12 }) -- (the words face the corridor)
		local lamp = blk("Scenery", "DoorLamp", r.xm - 4.5, r.xm + 4.5, WING.MOUTH.top + 0.75, WING.MOUTH.top + 1.15, z1 + 0.05, z1 + 0.3, WING.ACCENT, { ghost = true, mat = Enum.Material.Neon })
		lamp.Parent = room
	end
end

local function room(i, r)
	local x0, x1, z0, z1 = r.x0, r.x1, WING.rz0, WING.rz1
	local top = WING.rtop + 2
	local tut = K.folderIn(B.root, "Tutorial")
	local f = K.folderIn(tut, "Room" .. i)
	-- the floor: dark, with a projected grid a step lighter
	blk("Shell", "RoomFloor", x0, x1, 236, Y0, z0, z1, WING.FLOOR)
	for x = x0 + 4, x1 - 4, 8 do B.line(x, z0, x, z1, Y0, 0.16, WING.GRID, "Grid") end
	for z = z0 - 6, z1 + 2, -8 do B.line(x0, z, x1, z, Y0, 0.16, WING.GRID, "Grid") end
	-- walls: each side's own (the shared ones are built once: the west of room 1 and every east), the back
	if i == 1 then blk("Shell", "RoomWall", x0 - 4, x0, 234, top, z0 + 4, z1 - 4, P.courseWall) end
	blk("Shell", "RoomWall", x1, if i == #WING.ROOMS then WING.x1 else x1 + 4, 234, top, z0 + 4, z1 - 4, P.courseWall)
	blk("Shell", "RoomBack", x0 - 4, x1 + 4, 234, top, z1, z1 - 4, P.courseWall)
	-- bones: flat panelled walls (a dark plinth, pale panels proud of the wall with dark seams between, a lit cove over
	-- them), the bands round the ends, deep beams across with lit panels between, the ceiling
	for _, w in { { x0, 1 }, { x1, -1 } } do
		local side, dir = w[1], w[2]
		blk("Shell", "Plinth", side, side + dir * 0.35, Y0, Y0 + 1.4, z0, z1, P.deep)
		-- (v4.2, main: "bare white corridors when empty"): two tiers, a dark wainscot under a chair rail and pale panels
		-- over it, and a pilaster at every second seam (a steady rhythm down the room: 4 bays a side)
		local n = math.floor((z0 - z1) / WING.SEAM + 0.5)
		local step = (z0 - z1) / n
		for k = 0, n - 1 do
			local a, b = z0 - k * step - 0.35, z0 - (k + 1) * step + 0.35
			blk("Shell", "Wainscot", side, side + dir * 0.3, Y0 + 1.6, 248, a, b, P.ledgePanel)
			blk("Shell", "WallPanel", side, side + dir * 0.3, 248.6, 262, a, b, P.mass)
		end
		blk("Shell", "ChairRail", side, side + dir * 0.6, 248, 248.6, z0, z1, P.trim)
		for k = 2, n - 2, 2 do
			local z = z0 - k * step
			blk("Shell", "Pilaster", side, side + dir * 1.1, Y0, 262.4, z - 1, z + 1, P.pier2)
			blk("Shell", "PilasterBase", side, side + dir * 1.35, Y0, Y0 + 1.6, z - 1.2, z + 1.2, P.deep)
		end
		blk("Shell", "CoveShelf", side, side + dir * 0.9, 262.4, 263, z0, z1, P.trim)
		blk("Scenery", "CoveLight", side + dir * 0.2, side + dir * 0.35, 263, 263.25, z0 - 0.5, z1 + 0.5, P.litEdge, { ghost = true, mat = Enum.Material.Neon })
	end
	H.endWall(z0, -1, x0, x1, Y0, { skip = { r.xm - WING.MOUTH.half - 0.5, r.xm + WING.MOUTH.half + 0.5 } })
	H.endWall(z1, 1, x0, x1, Y0)
	H.roof(x0, x1, z0, z1, WING.FR, WING.pierTop, 4, 2, { r.xm - 10, r.xm + 10 }, 12)
	blk("Shell", "RoomRoof", x0 - 4, x1 + 4, WING.rtop, top, z0 + 4, z1 - 4, P.ceil)
	-- the projector over the middle: a chunky ring on the ceiling, a dark lens, a small lit eye (the courses come from it)
	local pz = (z0 + z1) / 2
	B.drum("Shell", "ProjectorRing", r.xm, pz, 268.6, 270, 9, P.pier2)
	B.drum("Shell", "ProjectorLens", r.xm, pz, 268.2, 268.6, 6, P.dark)
	B.drum("Scenery", "ProjectorEye", r.xm, pz, 268.05, 268.2, 2.4, WING.ACCENT, { ghost = true, mat = Enum.Material.Neon })
	-- the console, left of the way in, its word toward the mouth
	-- (v4.2) the lit ring on the floor under the projector, where the courses come from (pale, not the accent)
	for _, ring in { { 23, 21.8 }, { 13, 12 } } do
		B.drum("Scenery", "FloorRing", r.xm, pz, Y0 + 0.02, Y0 + 0.05, ring[1], P.litEdge, { ghost = true, mat = Enum.Material.Neon })
		B.drum("Scenery", "FloorRingIn", r.xm, pz, Y0 + 0.05, Y0 + 0.08, ring[2], WING.FLOOR, { ghost = true })
	end
	-- the console: a desk across the left of the way in, its screen tilted toward you, the accent (teal) on its front
	-- edge and screen only; the Console part (the server reads its Prompt) is its top's middle
	local c = WING.CONSOLE
	local cx, cz = r.xm + c.dx, c.z
	blk("Shell", "DeskBase", cx - 3.6, cx + 3.6, Y0, Y0 + 2.7, cz - 1.0, cz + 1.0, P.slate)
	blk("Shell", "DeskPlinth", cx - 3.8, cx + 3.8, Y0, Y0 + 0.5, cz - 1.2, cz + 1.2, P.deep)
	blk("Shell", "DeskTop", cx - 4.2, cx + 4.2, Y0 + 2.7, Y0 + 3.05, cz - 1.5, cz + 1.5, P.pier2)
	blk("Scenery", "DeskEdge", cx - 4.2, cx + 4.2, Y0 + 2.45, Y0 + 2.65, cz + 1.0, cz + 1.12, WING.ACCENT, { ghost = true, mat = Enum.Material.Neon })
	local scr = B.part("Shell", "DeskScreen", CF(cx, Y0 + 4.25, cz - 0.9) * CFrame.Angles(math.rad(-20), 0, 0), V3(6.4, 2.6, 0.3), P.board)
	local sg = Instance.new("SurfaceGui")
	sg.Name = "Gui"; sg.Face = Enum.NormalId.Back; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 40; sg.LightInfluence = 0
	local tl = Instance.new("TextLabel")
	tl.BackgroundTransparency = 1; tl.Size = UDim2.fromScale(0.86, 0.5); tl.Position = UDim2.fromScale(0.07, 0.25); tl.TextScaled = true
	tl.Text = "WEAPONS"; tl.TextColor3 = Color3.fromHex(WING.ACCENT); tl.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	tl.Parent = sg
	sg.Parent = scr
	B.part("Shell", "DeskScreenStand", CF(cx, Y0 + 3.2, cz - 1.0), V3(1.2, 0.5, 0.6), P.deep)
	local lp = B.lamp(cx, Y0 + 5.2, cz + 2.4, "point", 11, 0.6, WING.ACCENT)
	local btn = Instance.new("Part")
	btn.Name = "Console"; btn.Anchored = true; btn.Transparency = 1; btn.CanCollide = false; btn.CanQuery = false; btn.CanTouch = false
	btn.Size = V3(1, 1, 1); btn.CFrame = B.cf(cx, Y0 + 3.6, cz)
	btn.Parent = f
	local pp = Instance.new("ProximityPrompt")
	pp.Name = "Prompt"; pp.ActionText = "Weapons"; pp.ObjectText = "Tutorial"; pp.HoldDuration = 0
	pp.MaxActivationDistance = 9; pp.RequiresLineOfSight = false; pp.KeyboardKeyCode = Enum.KeyCode.E
	pp.Parent = btn
	-- the back wall's board: the weapon, its moves and the goal (TutorialUI paints it for the room's user)
	local board = B.text("Board", { { "", P.pale, "B", 1 } }, 24, 10, CF(r.xm, 259, z1 + 0.2) * CFrame.Angles(0, math.pi, 0), { plate = P.board, thick = 0.3 }) -- (facing into the room)
	board.Parent = f
	blk("Shell", "BoardFrame", r.xm - 12.8, r.xm + 12.8, 253.4, 264.6, z1, z1 + 0.15, P.trim, { ghost = true })
	-- (v4.2) the board's accent: a teal strip under it and a soft light on it
	blk("Scenery", "BoardEdge", r.xm - 12, r.xm + 12, 253.1, 253.35, z1 + 0.15, z1 + 0.35, WING.ACCENT, { ghost = true, mat = Enum.Material.Neon })
	B.lamp(r.xm, 251, z1 + 6, "point", 14, 0.5, WING.ACCENT)
	-- what the game reads
	local zone = Instance.new("Part")
	zone.Name = "Zone"; zone.Anchored = true; zone.Transparency = 1; zone.CanCollide = false; zone.CanQuery = false; zone.CanTouch = false
	zone.Size = V3(x1 - x0, WING.pierTop - Y0, z0 - z1)
	zone.CFrame = B.cf(r.xm, (Y0 + WING.pierTop) / 2, (z0 + z1) / 2)
	zone.Parent = f
	local origin = B.marker(f, "Origin", r.xm, Y0, z0 - 6, V3(r.xm, Y0, z0 - 20))
	origin.Size = V3(2, 0.2, 2)
	local db = Instance.new("Part")
	db.Name = "DoorBlock"; db.Anchored = true; db.Transparency = 1; db.CanCollide = false; db.CanQuery = false; db.CanTouch = false
	db.Size = V3(WING.MOUTH.half * 2, WING.MOUTH.top - Y0, 4)
	db.CFrame = B.cf(r.xm, (Y0 + WING.MOUTH.top) / 2, WING.cz1 - 2)
	db.Parent = f
	f:SetAttribute("Room", i)
	-- two lamps down the room (the ceiling's panels light it too)
	for _, z in { -8170, -8222 } do B.lamp(r.xm, WING.pierTop - 3, z, "point", 40, 0.45, P.lampWhite) end
end

-- ---------------------------------------------------------------- the parkour teleporter on the TOP gallery
-- (the owner: "course outside teleporter to parkour") the egg door's ring in its green, against the north wall east of
-- the TOP door, open to everyone: Doors.ToParkour (a plain Land door: LaserDoors) to the island's ParkourArrive
-- (studio-tools/ParkourIsland.luau). The TOP door beside it stays the gold Carls' locked secret
WING.PARKOUR = { x = -84, face = -8290, ring = 3 }
local function greenFx(at)
	local fx = Instance.new("Part")
	fx.Name = "ParkourPortalFx"; fx.Anchored = true; fx.CanCollide = false; fx.CanQuery = false; fx.CanTouch = false; fx.CastShadow = false
	fx.Transparency = 1; fx.Size = V3(5.6, 0.2, 5.6)
	fx.CFrame = B.at(at * CF(0, 3.9, 0) * CFrame.Angles(math.pi / 2, 0, 0))
	local function emitter(name)
		local e = Instance.new("ParticleEmitter")
		e.Name = name; e.Shape = Enum.ParticleEmitterShape.Disc; e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
		e.EmissionDirection = Enum.NormalId.Top; e.LightEmission = 1; e.LightInfluence = 0
		e.Parent = fx
		return e
	end
	local sw = emitter("Swirl")
	sw.Texture = "rbxasset://textures/particles/smoke_main.dds"
	sw.Color = ColorSequence.new(Color3.fromRGB(110, 255, 160), Color3.fromRGB(20, 190, 95))
	sw.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(0.5, 1.9), NumberSequenceKeypoint.new(1, 0.6) })
	sw.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.5), NumberSequenceKeypoint.new(0.75, 0.6), NumberSequenceKeypoint.new(1, 1) })
	sw.Lifetime = NumberRange.new(1.4, 2.2); sw.Rate = 26; sw.Speed = NumberRange.new(0.05, 0.25)
	sw.Rotation = NumberRange.new(0, 360); sw.RotSpeed = NumberRange.new(110, 190); sw.ZOffset = 0.4
	local mt = emitter("Motes")
	mt.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	mt.Color = ColorSequence.new(Color3.fromRGB(200, 255, 215), Color3.fromRGB(60, 255, 140))
	mt.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
	mt.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
	mt.Lifetime = NumberRange.new(1.4, 2.4); mt.Rate = 10; mt.Speed = NumberRange.new(0.6, 1.5)
	mt.SpreadAngle = Vector2.new(35, 35); mt.Drag = 0.6; mt.Acceleration = V3(0, 0.4, 0); mt.ZOffset = 0.4
	local pl = Instance.new("PointLight")
	pl.Color = Color3.fromRGB(70, 255, 140); pl.Range = 14; pl.Brightness = 1.4; pl.Shadows = false; pl.Parent = fx
	local hum = Instance.new("Sound")
	hum.Name = "Hum"; hum.SoundId = "rbxassetid://9125674114"; hum.Looped = true; hum.Volume = 0.3
	hum.RollOffMode = Enum.RollOffMode.InverseTapered; hum.RollOffMinDistance = 6; hum.RollOffMaxDistance = 38
	hum.Playing = true; hum.Parent = fx
	fx.Parent = B.root.Scenery
end
local function parkourPortal()
	local pk = WING.PARKOUR
	local top = 270 -- (the TOP gallery: v3's C.GAL.top)
	local F = CFrame.lookAt(V3(pk.x, top, pk.face), V3(pk.x, top, pk.face - 1))
	local at = F * CF(0, 0, -pk.ring)
	local pm = B.put("te_portal", at, { name = "ParkourPortalRing", raw = true, color = { ["17181c"] = "1c7a44", f0a53a = "3ddc84" } })
	if pm then
		for _, d in pm:GetDescendants() do
			if d:IsA("BasePart") and (string.match(d.Name, "_17181c$") or string.match(d.Name, "_f0a53a$")) then d.Material = Enum.Material.Neon end
		end
	end
	greenFx(at)
	B.solid("ParkourPortalStep", F * CF(0, 0.3, -(pk.ring - 0.9)), V3(10.6, 0.6, 3.2))
	-- the trigger: from 1.6 in front of the ring back to the wall (deep enough to be inside at a run)
	local z0, z1 = pk.face - (pk.ring - 1.6), -8295.8
	B.trigger("ToParkour", pk.x - 3, pk.x + 3, top + 0.6, top + 7, z0, z1, { Land = "ParkourArrive", Say = "PARKOUR" })
	-- its word over it, on the north wall (a sign: the place's name, nothing else)
	B.text("ParkourWord", { { "PARKOUR", P.pale, "B", 1 } }, 9, 1.8, CF(pk.x, top + 11.2, -8295.7) * CFrame.Angles(0, math.pi, 0), { plate = P.board, thick = 0.2 })
end

-- ---------------------------------------------------------------- the range: each lane's distances on its floor
-- (v4.2: the side walls already say 15 / 30 / 45 M; now each lane says it too, flat on its floor in front of each row,
-- read from the plates. TrainingV2's range: lanes x 40 / 54 / 68, rows at z -8183 / -8228 / -8273 on floors 240 / 244 / 248)
local function rangeWords()
	for _, row in { { -8183, 240, 15 }, { -8228, 244, 30 }, { -8273, 248, 45 } } do
		for _, lx in { 40, 54, 68 } do
			B.text("LaneDistance", { { ("%d M"):format(row[3]), P.pale, "B", 1 } }, 5, 2, CF(lx, row[2] + 0.05, row[1] + 5.4) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
		end
	end
end

-- ---------------------------------------------------------------- the open halls' surfaces
-- (v4.2, main: "the course hall from above is very pale and grey; add contrast and the real surface textures") in the
-- dummies hall and the course hall only: concrete walls a step warmer, slate floors a step darker, the deep beams
-- dark steel, the piers concrete. Trims, noses and the lit strips keep their smooth pale paint (the edges still read)
local SURF = {
	wall = { Enum.Material.Concrete, "a1998e" },
	floor = { Enum.Material.Slate, "5f5e5a" },
	beam = { Enum.Material.Metal, "4b5058" },
	pier = { Enum.Material.Concrete, "858890" },
}
local function surfaces()
	local O = B.O
	local function inHalls(p)
		local x, z = p.Position.X - O.X, p.Position.Z - O.Z
		return (x > -137 and x < -67 and z < -8097 and z > -8301) or (x > -69 and x < 29 and z < -8141 and z > -8263)
	end
	local n = 0
	for _, p in B.root.Shell:GetChildren() do
		if not p:IsA("BasePart") or not inHalls(p) then continue end
		local nm = p.Name
		local k = if string.match(nm, "^CourseWall") or string.match(nm, "^HallWall") or nm == "HallEnd" or nm == "HallFront" then "wall"
			elseif nm == "CourseFloor" or nm == "HallFloor" or nm == "Stage" or nm == "StageStep" or nm == "Threshold" or nm == "WestThreshold" then "floor"
			elseif nm == "RoofBeam" then "beam"
			elseif nm == "Pier" then "pier" else nil
		if k then
			p.Material = SURF[k][1]
			p.Color = Color3.fromHex(SURF[k][2])
			n += 1
		end
	end
	return n
end

-- ---------------------------------------------------------------- the wrapper
function W.wrap(r3)
	R3 = r3
	local o = {}
	function o.apply(t, k)
		T, K = t, k
		P = T.P
		Y0 = k.Y0
		R3.OPEN = true
		R3.WESTDOOR = WING.WESTDOOR
		R3.apply(t, k)
		T.ZONE = { -330, 86, 220, 312, -8058, -8308 } -- (west to -330 for the wing)
		T.STAGE = V3(0, 0, 800) -- (a staging copy north of the hall: at v2's x +400 the wing would stand in the live range)
		T.TUTORIAL = WING
		-- the dummy yard (v3's dummies hall, open to the sky): on the old live-fire stage at 30 m, two ARMOURED (300 HP,
		-- a slate plate) and two HEAL-BACK (whole 2 s after your last hit), beside the static ones at 10 m, the strafer at
		-- 20 m and the practice lane's strafe / jump / health modes (its consoles)
		local sy = R3.D.STAGE.y
		T.DUMMIES.Armour1 = { -14, sy, -8240 }; T.DUMMIES.Armour2 = { -5, sy, -8240 }
		T.DUMMIES.Heal1 = { 5, sy, -8240 }; T.DUMMIES.Heal2 = { 14, sy, -8240 }
		T.DUMMY_HP = { Armour1 = 300, Armour2 = 300 }
		T.HEALBACK = { Heal1 = 2, Heal2 = 2 }
		o.SEAL = {}
		for _, q in R3.SEAL do if q.Y < 300 then table.insert(o.SEAL, q) end end -- (v3's skylight drum point is open sky now)
		for _, q in {
			V3(-230, Y0 + 4, -8124), V3(-140, 250, -8126), V3(-318, 252, -8114), V3(-138, Y0 + 3, -8126),
			V3(-130, 262, -8200), V3(-100, 298, -8200), V3(0, 274, -8200), V3(-44, 274, -8240),
		} do table.insert(o.SEAL, q) end
		for _, r in WING.ROOMS do
			for _, q in { V3(r.xm, Y0 + 4, -8150), V3(r.xm, 262, -8195), V3(r.x0 + 2, 268, -8246), V3(r.xm, Y0 + 3, -8138) } do table.insert(o.SEAL, q) end
		end
	end
	function o.build(b)
		B = b
		local msg = R3.build(b)
		R3.bind(b)
		H = R3.H
		corridor()
		for i, r in WING.ROOMS do room(i, r) end
		parkourPortal()
		local nS = surfaces()
		rangeWords()
		msg ..= (" (%d hall surfaces)"):format(nS)
		return msg .. " + v4: open sky, the tutorial wing (" .. #WING.ROOMS .. " rooms)"
	end
	return o
end

return W
