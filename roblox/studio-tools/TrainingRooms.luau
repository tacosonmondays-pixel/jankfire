--!nocheck
-- TRAINING ROOMS v3 (18 Nov 2026): the dummies room and the movement course, redone from scratch. the owner, of the
-- muster with its COURSE and DUMMIES arches: "instead of an extension can you do a complete remodel the only thing I
-- want to keep is the vip room and the shooting range area and the training hub but these two rooms can be redone
-- entirely". (the old yard had grown a side hall through an arcade, the course an entry strip: both read as add-ons.)
-- the idea: three plain rectangles of one building, the same bones in each, so nothing looks bolted on:
--   * piers at a steady 16-stud rhythm up every long wall, carrying deep roof beams with rounded white noses, a flat
--     ceiling with lit panels between them; a dark plinth and a pale band low on the walls, and a band of high lit
--     panels (the clerestory) between the piers under the beams
--   * the DUMMIES HALL straight ahead of the muster: one hall 88 wide under one roof, no arcade. the main lane on the
--     muster's axis (10/20/30 m, the strafer, the live-fire stage and its two shooters, the garage door to the back
--     lot in the end wall) and the practice lane beside it (rails at 10 and 20 m, the deck at 30 m with its board and
--     the big target over it), parted by a low lane wall, as a real range parts its lanes
--   * the COURSE: a low LOBBY off the muster's west passage, open on its far side into the COURSE HALL, the tallest
--     room: a walk on brackets up the west wall, a core tower on a plinth in the middle under a skylight (bridged from
--     the walk), and at the far end the TOP gallery, a solid mass the hall's width at 270 with the gold dummies' door in
--     its back wall (TrainingV2's topRoom, TrainingLot's eggDoor and portal)
-- what the game reads is what the old rooms made, under the same names: Hub.DummySpots, TrainingGround.LiveFire,
-- TrainingGround.Practice, heal pads, Doors.ToPlayground, Doors.TrainingArrive, T.EGG_DOOR, T.COURSE (gold Carl 3)
-- and T.GOLD1 (gold Carl 1; TrainingLot). TrainingV2 calls R.apply(T, K) at load when T.ROOMS == "v3" and R.build(B)
-- in place of its yard and course; T.check takes R.SEAL as the rooms' seal points.
local R = {}
local V3, CF = Vector3.new, CFrame.new
local T, K, P
local Y0, MY, MZ, MTOP, NEON, PASS

-- ---------------------------------------------------------------- the plan (world coordinates, y up)
-- the dummies hall: inside faces; the main lane's axis is the muster's (x 0); the practice lane west of the lane wall
local D = { x0 = -64, x1 = 24, z0 = -8146, z1 = -8258, split = -24, pierTop = 268, beamTop = 273, roof = 275 }
D.PIERS = { -8162, -8178, -8194, -8210, -8226, -8242 } -- (the frames; 16-stud end bays at the muster and the end wall)
D.STAGE = { z = -8228, y = 242 } -- the live-fire end's floor, the garage door's sill (TrainingLot: L.DOOR.y0)
D.DECK = { x0 = -64, x1 = -30, z0 = -8226, top = 246 } -- the practice lane's 30 m deck
-- (v3.1, after the owner's reference, a compound of levels with steel bridges, and the main session's note that the
-- blockout read close to the old yard) the overlook: a mezzanine across the front wall over the muster's arch, a stair
-- up the east side; the gantry: the hall's centrepiece, a steel bridge across the whole hall at the 20 m line on three
-- towers, the practice lane's 20 m dummy riding a rail on it
D.MEZ = { z1 = -8156, top = 259, thick = 1.6, stair = { x0 = 16, x1 = 24, n = 19 } }
D.GANTRY = { z = -8206, half = 3, top = 256, deep = 4, towers = { { -64, -58 }, { -27, -21 }, { 18, 24 } }, towerTop = 262 }
-- the course: the lobby (low), the hall (tall)
local LOB = { x0 = -68, x1 = -30, z0 = -8102, z1 = -8142, ceil = 256 }
local C = { x0 = -132, x1 = -72, z0 = -8102, z1 = -8296, top = 296, open = { -8106, -8138, 254 } } -- (open: the lobby's way in, z and head)
C.xm = (C.x0 + C.x1) / 2 -- -102
C.GZ = {} -- every 16: the walk's brackets
for z = -8118, -8278, -16 do table.insert(C.GZ, z) end
C.FR = {} -- every 32 (v3.2): the piers and the roof's beams (the main session: the hall read as "a long narrow corridor of piers")
for z = -8118, -8278, -32 do table.insert(C.FR, z) end
C.WALK = { x0 = C.x0, x1 = C.x0 + 8, z0 = -8102, z1 = -8282, top = 254, gap = { -8226, -8234 } } -- the west walk, its gap
-- (v3.1) the watch steps up the south wall to the walk's start (a way up anyone can walk, a place to sit and watch); the
-- east block, a platform mass against the east wall, reached across the hall by a steel bridge from the walk; a pad from
-- its far end up onto the TOP gallery
C.STEPS = { x0 = -84, run = 2.4, rise = 1, n = 14, z0 = -8102, z1 = -8114 } -- (walkable since 18 Nov: the pads are gone)
-- the stair up to the TOP gallery (18 Nov, the owner, of the two pads either side of the dark floor in front of the
-- gallery: "get rid of these teleporters", "move the stairs to fill this space"): from the bridge's north edge straight
-- up to the gallery on the TOP door's axis, solid under, cheek walls both sides
C.GSTAIR = { x0 = C.xm - 8, x1 = C.xm + 8, n = 16, rise = 1, run = 1.25 }
C.BLOCK = { x0 = -86, x1 = C.x1, z0 = -8250, z1 = -8276, top = 254 }
C.BRIDGE = { z0 = -8256, z1 = -8262, post = -105 }
C.GAL = { z0 = -8282, top = 270 } -- the TOP gallery: the hall's width, from z0 to the north wall
C.CORE = { x = C.xm, z = -8198, plinth = 10, ledge = 254, body = 6, top = 268 } -- the core: plinth half-width, body's
C.SKY = { x0 = C.xm - 10, x1 = C.xm + 10, z0 = -8188, z1 = -8208, top = 316 }
R.D, R.LOB, R.C = D, LOB, C

-- ---------------------------------------------------------------- what the rest reads (set before anything builds)
function R.apply(t, k)
	T, K = t, k
	P = T.P
	Y0, MY, MZ, MTOP, NEON, PASS = k.Y0, k.MY, k.MZ, k.MTOP, k.NEON, k.PASS
	-- the dummies: the main lane's as before (the Plinker's view of the spawns and the gun sessions' test line hold),
	-- the practice lane's down its middle, the course's runner on a rail between the core and the gallery
	T.DUMMIES = {
		Dummy = { 0, Y0, -8206 }, -- (no Plinker, Plinker2 since 18 Nov: the owner, "these shooting dummies are now redundant")
		Stand1 = { -9, Y0, -8173.5 }, Stand2 = { 9, Y0, -8173.5 },
		Stand3 = { -44, Y0, -8173.5 }, Stand4 = { -44, D.GANTRY.top, D.GANTRY.z }, Dummy2 = { -50, D.DECK.top, -8238 },
		Runner = { C.xm, Y0, -8226 },
	}
	T.RAILS = { Stand3 = { 6, 8 }, Stand4 = { 10, 14 }, Dummy2 = { 8, 20 }, Runner = { 16, 14 } }
	-- (18 Nov, the owner: "this button is redundant", "these shooting dummies are now redundant": no live-fire end, no
	-- console, no shooters; the practice lane's own shoot-back stays)
	T.NO_LIVE = true
	T.LANE = { Stand3 = true, Stand4 = true, Dummy2 = true }
	-- gold Carl 1: on the practice deck's far corner by the big target (shot from the lane below); gold Carl 3: on the
	-- core's top, looking back at the lobby's way in
	T.GOLD1 = { "practice deck", V3(-59, D.DECK.top, -8253), V3(-44, D.DECK.top, -8160) }
	T.COURSE = { tower = V3(C.CORE.x, C.CORE.top, C.CORE.z), look = V3(-72, C.CORE.top, -8122) }
	-- the gold dummies' door: the TOP gallery's back wall on the hall's axis (TrainingV2.topRoom builds the room)
	T.TOPD3 = { x = C.xm, y = C.GAL.top, w = 12, h = 10.5, frame = C.z1 + 4.2, face = C.z1 + 5.8, back = T.FACE + 0.3, cut = 1.95, jamb = 1.8 }
	local td = T.TOPD3
	T.EGG_DOOR = { cf = CFrame.lookAt(V3(td.x, td.y, td.face), V3(td.x, td.y, td.face - 1)), w = 8.4, h = 8.6,
		cw = td.w, ch = td.h, wall = P.recess, room = td.face - td.back, door = 2.4,
		plate = false, green = true } -- (the panel beside it says LOCKED/OPEN; the owner: "make the teleporter have a cool green effect")
	-- the gold dummies' panel (the owner: "the dummy prop that displays how many you've found should be moved to the door
	-- that leads to the teleporter"): on the gallery's back wall beside the TOP frame, west of it (TrainingLot builds it;
	-- x its middle, y its housing's foot, face the wall's face, labels under its three men)
	T.LOT_PANEL = { x = td.x - 14, y = td.y + 1.6, face = C.z1, labels = { "DUMMIES", "RANGE", "COURSE" } }
	-- the seal test's points inside these rooms (T.check adds the muster's, the range's and the basement's)
	R.SEAL = {
		V3(0, Y0 + 4, -8200), V3(0, 256, -8200), V3(0, 266, -8240), V3(-44, Y0 + 4, -8170), V3(-44, 262, -8200),
		V3(-56, D.DECK.top + 4, -8250), V3(20, D.STAGE.y + 4, -8250), V3(-20, 250, -8155), V3(-60, 264, -8150),
		V3(-48, Y0 + 4, -8122), V3(-36, 252, -8108), V3(-64, 250, -8138),
		V3(C.xm, Y0 + 4, -8130), V3(C.xm, 272, -8150), V3(C.xm, 290, -8250), V3(-128, 258, -8200), V3(C.xm, C.CORE.top + 4, C.CORE.z),
		V3(C.xm, 306, C.CORE.z), V3(-100, C.GAL.top + 4, -8290), V3(-76, 262, -8120), V3(-80, Y0 + 4, -8270), V3(-126, 284, -8288),
		V3(td.x, td.y + 4, td.back + 4), V3(td.x, td.y + 8, td.back + 2),
		V3(0, 263, -8151), V3(-40, 263, -8151), V3(-30, 261, D.GANTRY.z), V3(-79, 258, -8263), V3(-100, 258, -8108),
	}
end

-- ---------------------------------------------------------------- helpers
local B
local function blk(...) return B.blk(...) end
-- a wall's bones along a long side: piers (and their bases) at the frames, the dark plinth, the pale band, the high lit
-- panels between the piers. side = the wall's inside face (x), dir = +1 if the room is to +x of it. zs = the frames,
-- za..zb = the wall's length, y0 = the floor, top = the piers' tops, clere = { y0, y1 } of the lit panels
local function longWall(side, dir, zs, za, zb, y0, top, clere, o)
	o = o or {}
	local zl, zh = math.min(za, zb), math.max(za, zb)
	for _, z in zs do
		blk("Shell", "Pier", side, side + dir * 2, y0, top, z - 1.6, z + 1.6, P.pier)
		blk("Shell", "PierBase", side, side + dir * 2.25, y0, y0 + 1.3, z - 1.85, z + 1.85, P.deep)
		blk("Shell", "PierCap", side, side + dir * 2.5, top - 1.2, top, z - 1.9, z + 1.9, P.trim)
		-- the haunch: a chunky wedge under the cap where the beam lands, so pier and beam read as one frame
		if o.haunch then
			local f = side + dir * 2
			B.part("Shell", "Haunch", CF(f + dir * 1.2, top - 1.2 - 1.2, z) * CFrame.Angles(0, dir * math.pi / 2, 0) * CFrame.Angles(math.pi, 0, 0), V3(2.6, 2.4, 2.4), P.pier, { wedge = true })
		end
		-- a sconce on the pier's face (the old yard's): a dark housing, a warm light let into it, a warm lamp
		if o.sconce then
			local f, y = side + dir * 2, if type(o.sconce) == "function" then o.sconce(z) else o.sconce
			if not y then continue end
			blk("Scenery", "SconceHousing", f, f + dir * 0.6, y, y + 3, z - 0.9, z + 0.9, P.dark)
			blk("Scenery", "SconceLight", f + dir * 0.55, f + dir * 0.7, y + 0.4, y + 2.6, z - 0.55, z + 0.55, P.warm, { ghost = true, mat = NEON })
			B.lamp(f + dir * 1.4, y + 1.5, z, "point", 13, 0.4, P.warm)
		end
	end
	blk("Shell", "Dado", side, side + dir * 0.2, y0, y0 + 1.2, zl, zh, P.floor2, { ghost = true })
	if not o.noBand then blk("Shell", "Band", side, side + dir * 0.3, y0 + 8, y0 + 8.6, zl, zh, P.trim, { ghost = true }) end
	-- the clerestory: a pale panel proud of the wall in every bay, a lit strip along its top (a cove)
	local edges = { zh }
	for _, z in zs do table.insert(edges, z + 1.6); table.insert(edges, z - 1.6) end
	table.insert(edges, zl)
	table.sort(edges, function(a, b) return a > b end)
	for i = 1, #edges - 1, 2 do
		local a, b = edges[i] - 1.2, edges[i + 1] + 1.2
		if a - b > 4 then
			blk("Scenery", "Clerestory", side, side + dir * 0.25, clere[1], clere[2], a, b, P.mass, { ghost = true })
			blk("Scenery", "ClereLight", side + dir * 0.25, side + dir * 0.4, clere[2] - 0.5, clere[2] - 0.25, a, b, P.litEdge, { ghost = true, mat = NEON })
		end
	end
end
-- the same along a short side (an end or front wall, along x): plinth and band only
local function endWall(side, dir, xa, xb, y0, o)
	o = o or {}
	local xl, xh = math.min(xa, xb), math.max(xa, xb)
	for _, s in o.skip and { { xl, o.skip[1] }, { o.skip[2], xh } } or { { xl, xh } } do
		if s[2] - s[1] > 0.5 then
			blk("Shell", "Dado", s[1], s[2], y0, y0 + 1.2, side, side + dir * 0.2, P.floor2, { ghost = true })
			blk("Shell", "Band", s[1], s[2], y0 + 8, y0 + 8.6, side, side + dir * 0.3, P.trim, { ghost = true })
		end
	end
end
-- the bones along a short wall (along x): piers at xs and the high pale panels with their lit cove between them (skip:
-- an x range with no panel, over a doorway)
local function endBones(side, dir, xs, xa, xb, y0, top, clere, o)
	o = o or {}
	local xl, xh = math.min(xa, xb), math.max(xa, xb)
	for _, x in xs do
		blk("Shell", "Pier", x - 1.6, x + 1.6, y0, top, side, side + dir * 2, P.pier)
		blk("Shell", "PierBase", x - 1.85, x + 1.85, y0, y0 + 1.3, side, side + dir * 2.25, P.deep)
		blk("Shell", "PierCap", x - 1.9, x + 1.9, top - 1.2, top, side, side + dir * 2.5, P.trim)
	end
	local edges = { xl }
	for _, x in xs do table.insert(edges, x - 1.6); table.insert(edges, x + 1.6) end
	table.insert(edges, xh)
	table.sort(edges)
	for i = 1, #edges - 1, 2 do
		local a, b = edges[i] + 1.2, edges[i + 1] - 1.2
		local segs = { { a, b } }
		if o.skip and o.skip[1] < b and o.skip[2] > a then segs = { { a, o.skip[1] }, { o.skip[2], b } } end
		for _, sg in segs do
			if sg[2] - sg[1] > 4 then
				blk("Scenery", "Clerestory", sg[1], sg[2], clere[1], clere[2], side, side + dir * 0.25, P.mass, { ghost = true })
				blk("Scenery", "ClereLight", sg[1], sg[2], clere[2] - 0.5, clere[2] - 0.25, side + dir * 0.25, side + dir * 0.4, P.litEdge, { ghost = true, mat = NEON })
			end
		end
	end
end
-- deep roof beams across a room at the frames (zs), from x0 to x1, undersides at y; a rounded white nose under each;
-- the ceiling slab over them, lit panels in every bay along xs (centres) w wide
local function roof(x0, x1, za, zb, zs, y, depth, slab, xs, w, o)
	o = o or {}
	for _, z in zs do
		blk("Shell", "RoofBeam", x0, x1, y, y + depth, z - 1.3, z + 1.3, P.pier)
		B.part("Shell", "BeamNose", CF((x0 + x1) / 2, y + 0.05, z) * CFrame.Angles(0, 0, 0), V3(x1 - x0, 1.2, 1.2), P.trim, { cyl = true })
	end
	local top = y + depth
	if not o.noSlab then blk("Shell", "Ceiling", x0, x1, top, top + slab, za, zb, P.ceil) end
	local edges = { math.max(za, zb) }
	for _, z in zs do table.insert(edges, z + 1.3); table.insert(edges, z - 1.3) end
	table.insert(edges, math.min(za, zb))
	table.sort(edges, function(a, b) return a > b end)
	for i = 1, #edges - 1, 2 do
		local a, b = edges[i], edges[i + 1]
		if a - b < 6 then continue end
		for _, x in xs do
			if o.skip and o.skip(x, (a + b) / 2) then continue end
			blk("Shell", "PanelRim", x - w / 2 - 0.5, x + w / 2 + 0.5, top - 0.2, top - 0.02, a - 1.5, b + 1.5, P.trim, { ghost = true })
			blk("Scenery", "CeilingPanel", x - w / 2, x + w / 2, top - 0.32, top - 0.2, a - 2, b + 2, P.panel, { ghost = true, mat = NEON })
		end
	end
end
-- a slab you stand on, with the house's white nose on its open edge(s) and a lit strip under the nose
local function slab(name, x0, x1, z0, z1, top, thick, edges)
	blk("Shell", name, x0, x1, top - thick, top, z0, z1, P.ledge)
	for _, e in edges or {} do
		if e == "x0" or e == "x1" then
			local x = if e == "x0" then x0 else x1
			B.part("Shell", "Nose", CF(x, top - 0.1, (z0 + z1) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(z1 - z0), 1.4, 1.4), P.trim, { cyl = true })
			local s = if e == "x0" then -1 else 1
			blk("Scenery", "EdgeLight", x + s * 0.05, x + s * 0.2, top - 1.3, top - 1.0, z0, z1, P.litEdge, { ghost = true, mat = NEON })
		else
			local z = if e == "z0" then z0 else z1
			B.part("Shell", "Nose", CF((x0 + x1) / 2, top - 0.1, z), V3(math.abs(x1 - x0), 1.4, 1.4), P.trim, { cyl = true })
			local s = if (e == "z0") == (z0 > z1) then 1 else -1
			blk("Scenery", "EdgeLight", x0, x1, top - 1.3, top - 1.0, z + s * 0.05, z + s * 0.2, P.litEdge, { ghost = true, mat = NEON })
		end
	end
end
-- a cheek wall up a stair's open side, so it shows no sawtooth: a wedge under the slope from the foot (a0, floor y0) to
-- the head (a1, y1), a band of even height over it and a pale cap, the stair running along axis "x" or "z"; c0..c1 the
-- wall's thickness across
local function cheek(axis, a0, a1, y0, y1, c0, c1, hex)
	local L, H = math.abs(a1 - a0), y1 - y0
	local up = 1.2
	local am, cm, w = (a0 + a1) / 2, (c0 + c1) / 2, math.abs(c1 - c0)
	local dir = if a1 > a0 then 1 else -1
	local cf
	if axis == "z" then
		cf = CF(cm, y0 + H / 2, am) * (if dir > 0 then CFrame.identity else CFrame.Angles(0, math.pi, 0))
	else
		cf = CF(am, y0 + H / 2, cm) * CFrame.Angles(0, if dir > 0 then math.pi / 2 else -math.pi / 2, 0)
	end
	B.part("Shell", "Cheek", cf, V3(w, H, L), hex, { wedge = true })
	B.ramp("Shell", "CheekBand", axis, a0, y0 + up, a1, y1 + up, c0, c1, hex, { thick = up + 0.15 })
	B.ramp("Shell", "CheekCap", axis, a0, y0 + up + 0.3, a1, y1 + up + 0.3, math.min(c0, c1) - 0.15, math.max(c0, c1) + 0.15, P.trim, { thick = 0.3 })
end
-- a console (the live-fire console's kind; hold E): its button goes in folder f with a Prompt
local function console(f, name, word, cx, cz, hex, action, objectText)
	local ch = Y0 + 2.55
	blk("Shell", "ConsoleBase", cx - 1.6, cx + 1.6, Y0, ch - 0.55, cz + 1.2, cz - 1.2, P.slate)
	B.part("Shell", if name == "LiveButton" then "ConsoleTop" else "PracticeTop", CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0), V3(3.6, 0.8, 2.9), P.pier2)
	local btn = B.part("Scenery", name, CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0) * CF(0, 0.45, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.5, 1.7, 1.7), hex, { cyl = true, ghost = true })
	btn.Parent = f
	local pp = Instance.new("ProximityPrompt")
	pp.Name = "Prompt"; pp.ActionText = action; pp.ObjectText = objectText; pp.HoldDuration = if name == "LiveButton" then 0.4 else 0.3
	pp.MaxActivationDistance = if name == "LiveButton" then 9 else 8; pp.RequiresLineOfSight = false; pp.KeyboardKeyCode = Enum.KeyCode.E
	pp.Parent = btn
	if word then B.text("ConsoleWord", { { word, P.pale, "B", 1 } }, 2.9, 0.55, CF(cx, Y0 + 1.15, cz + 1.24) * CFrame.Angles(0, math.pi, 0), { plate = P.slate, thick = 0.05 }) end
	return btn
end
local function cover(x, z, kind, turned)
	if kind == "high" then
		for _, dz in { -2.5, 2.5 } do B.put("tv_block", CF(x, Y0, z + dz), { name = "Block" }) end
		B.solid("BlockBox", CF(x, Y0 + 3.8, z), V3(5, 7.6, 10))
	else
		B.put("tv_cover", CF(x, Y0, z) * CFrame.Angles(0, if turned then 0 else math.pi / 2, 0), { name = "Cover" })
		B.solid("CoverBox", CF(x, Y0 + 2.35, z), if turned then V3(10, 4.7, 2.4) else V3(2.4, 4.7, 10))
	end
end
local function distWord(x, y, z, k, w)
	B.text("DistWord", { { ("%d M"):format(k * 10), P.pale, "B", 1 } }, w or 7, 2.6, CF(x, y + 0.05, z + 2.2) * CFrame.Angles(0, math.pi, 0) * CFrame.Angles(math.pi / 2, 0, 0), { clear = true, thick = 0.05 })
end

-- ---------------------------------------------------------------- the dummies hall
local function hallShell()
	local x0, x1, z0, z1 = D.x0, D.x1, D.z0, D.z1
	local top = D.roof + 2
	-- floors: the hall at 240, the live-fire stage (242) across the main lane, the practice deck (246) across the
	-- practice lane west of its stairs
	blk("Shell", "HallFloor", x0 - 4, x1 + 4, 236, Y0, z0 + 0.1, D.STAGE.z + 2, P.floor)
	blk("Shell", "StageStep", D.split, x1 + 4, 236, Y0 + 1, D.STAGE.z + 2, D.STAGE.z, P.floor2)
	blk("Shell", "Stage", D.split, x1 + 3.95, 236.05, D.STAGE.y, D.STAGE.z, z1 - 3.95, P.floor)
	B.part("Shell", "StageNose", CF((D.split + x1) / 2, D.STAGE.y - 0.45, D.STAGE.z + 0.05), V3(x1 - D.split - 1.4, 0.9, 0.9), P.trim, { cyl = true })
	B.part("Shell", "StepNose", CF((D.split + x1) / 2, Y0 + 0.55, D.STAGE.z + 2.05), V3(x1 - D.split - 1.4, 0.9, 0.9), P.trim, { cyl = true })
	-- walls: west, east, the end (the garage door's opening on the axis: TrainingLot builds the door, frame and panel),
	-- the front (the muster's arch on the axis)
	blk("Shell", "HallWallW", x0 - 4, x0, 236, top, z0 + 4, z1 - 4, P.wall)
	blk("Shell", "HallWallE", x1, x1 + 4, 236, top, z0 + 4, z1 - 4, P.wall)
	blk("Shell", "HallEnd", x0 - 4, -12, 236, top, z1, z1 - 4, P.wall)
	blk("Shell", "HallEnd", 12, x1 + 4, 236, top, z1, z1 - 4, P.wall)
	blk("Shell", "HallEnd", -12, 12, 258.55, top, z1, z1 - 4, P.wall)
	blk("Shell", "HallFront", x0 - 4, -9.9, 236, top, z0 + 4, z0, P.wall)
	blk("Shell", "HallFront", 9.9, x1 + 4, 236, top, z0 + 4, z0, P.wall)
	blk("Shell", "HallFront", -9.9, 9.9, MTOP, top, z0 + 4, z0, P.wall)
	-- the bones
	longWall(x0, 1, D.PIERS, z0, z1, Y0, D.pierTop, { 257, 265 }, { sconce = function(z) return if z < D.DECK.z0 + 1 then 255.5 else 249.5 end, haunch = true }) -- (over the deck: clear of an eye on it)
	longWall(x1, -1, D.PIERS, z0, z1, Y0, D.pierTop, { 257, 265 }, { sconce = function(z) return if z < D.STAGE.z + 1 then 251.5 elseif z > D.MEZ.z1 - 30 then nil else 249.5 end, haunch = true })
	endBones(z0, -1, { -44 }, x0, D.split - 1.6, Y0, D.pierTop, { 261, 266 })
	endBones(z0, -1, {}, D.split + 1.6, x1, Y0, D.pierTop, { 261, 266 })
	endWall(z0, -1, x0, x1, Y0, { skip = { -10.5, 10.5 } })
	endWall(z1, 1, x0, D.DECK.x1, D.DECK.top)
	endWall(z1, 1, -24, x1, D.STAGE.y, { skip = { -12.6, 12.6 } })
	-- a pier on the end wall where the lanes part, and one on the front wall: the lane wall's line runs from wall to wall
	for _, w in { { z1, 1 }, { z0, -1 } } do
		blk("Shell", "Pier", D.split - 1.6, D.split + 1.6, Y0, D.pierTop, w[1], w[1] + w[2] * 2, P.pier)
		blk("Shell", "PierBase", D.split - 1.85, D.split + 1.85, Y0, Y0 + 1.3, w[1], w[1] + w[2] * 2.25, P.deep)
		blk("Shell", "PierCap", D.split - 1.9, D.split + 1.9, D.pierTop - 1.2, D.pierTop, w[1], w[1] + w[2] * 2.5, P.trim)
	end
	-- the roof: a deep beam at every frame from wall to wall (one span: one room), two rows of lit panels
	roof(x0 - 4, x1 + 4, z0 + 4, z1 - 4, D.PIERS, D.pierTop, D.beamTop - D.pierTop, 2, { -44, 0 }, 14)
	for _, e in { { x0 - 4.4, x0 - 2.4 }, { x1 + 2.4, x1 + 4.4 } } do
		blk("Shell", "RoofCoping", e[1], e[2], top, top + 2, z0 + 4.4, z1 - 4.4, P.wall2, { nq = true })
	end
	-- lamps down both lanes under the beams
	for i, z in D.PIERS do
		if i % 2 == 1 then
			B.lamp(0, D.pierTop - 3, z - 8, "point", 30, 0.55, P.lampWhite)
			B.lamp(-44, D.pierTop - 3, z - 8, "point", 30, 0.5, P.lampWhite)
		end
	end
end

-- the overlook: a mezzanine slab across the front wall on chunky corbels, its open edge with the white nose, a lit
-- strip and a low parapet; a straight stair up the east side, its treads with noses, solid under
local function overlook()
	local M = D.MEZ
	local x0, x1, z0 = D.x0, D.x1, D.z0
	slab("Overlook", x0, x1, z0, M.z1, M.top, M.thick, { "z1" })
	local sx0, sx1 = M.stair.x0, M.stair.x1
	blk("Shell", "Parapet", x0, sx0, M.top, M.top + 1.1, M.z1 + 0.6, M.z1, P.slate)
	blk("Shell", "ParapetCap", x0 - 0.1, sx0 + 0.1, M.top + 1.1, M.top + 1.4, M.z1 + 0.75, M.z1 - 0.15, P.trim)
	for _, x in { -54, -34, -14, 4 } do
		blk("Shell", "Corbel", x - 1.2, x + 1.2, M.top - M.thick - 3.2, M.top - M.thick, z0, z0 - 6, P.pier)
		blk("Shell", "CorbelFoot", x - 1.0, x + 1.0, M.top - M.thick - 4.6, M.top - M.thick - 3.2, z0, z0 - 3, P.pier)
	end
	-- the stair: rising toward the overlook (to +z) along the east wall
	local n = M.stair.n
	local rise = (M.top - Y0) / n
	local zTop = M.z1
	for k = 1, n do
		local za, zb = zTop - (n - k + 1) * 1.5, zTop - (n - k) * 1.5
		blk("Shell", "OverlookStep", sx0, sx1, Y0, Y0 + k * rise, za, zb, P.ledge)
		B.part("Shell", "StepNose", CF((sx0 + sx1) / 2, Y0 + k * rise - 0.3, za + 0.05), V3(sx1 - sx0, 0.6, 0.6), P.trim, { cyl = true })
	end
	cheek("z", zTop - n * 1.5, zTop, Y0, M.top, sx0 - 0.6, sx0, P.slate) -- (main: "a raw sawtooth profile" from the hall)
	B.lamp((x0 + x1) / 2, M.top + 6, z0 - 6, "point", 40, 0.45, P.lampWhite)
end
-- the gantry: a deep steel girder across the hall at the 20 m line, three towers under it (the west wall, the lane wall's
-- end, the east wall), an amber line along its face (the room's one accent), lit underneath; the practice dummy's rail
-- on its deck over the practice lane
local function gantry()
	local G = D.GANTRY
	local za, zb = G.z + G.half, G.z - G.half
	blk("Shell", "GantryGirder", D.x0, D.x1, G.top - G.deep, G.top, za, zb, P.pier)
	for _, z in { za, zb } do
		B.part("Shell", "GantryNose", CF((D.x0 + D.x1) / 2, G.top - G.deep, z), V3(D.x1 - D.x0, 1.2, 1.2), P.trim, { cyl = true })
		B.part("Shell", "GantryNose", CF((D.x0 + D.x1) / 2, G.top, z), V3(D.x1 - D.x0, 1.0, 1.0), P.trim, { cyl = true })
		local sg = if z == za then 1 else -1
		blk("Scenery", "GantryLine", D.x0, D.x1, G.top - G.deep / 2 - 0.2, G.top - G.deep / 2 + 0.2, z, z + sg * 0.12, P.amber, { ghost = true })
	end
	blk("Scenery", "GantryLight", D.x0 + 2, D.x1 - 2, G.top - G.deep - 0.15, G.top - G.deep, G.z + 1.2, G.z - 1.2, P.litEdge, { ghost = true, mat = NEON })
	for _, t in G.towers do
		blk("Shell", "GantryTower", t[1], t[2], Y0, G.towerTop, za + 1, zb - 1, P.pier2)
		blk("Shell", "GantryTowerBase", t[1] - 0.3, t[2] + 0.3, Y0, Y0 + 1.3, za + 1.3, zb - 1.3, P.deep)
		blk("Shell", "GantryTowerCap", t[1] - 0.4, t[2] + 0.4, G.towerTop, G.towerTop + 0.8, za + 1.4, zb - 1.4, P.trim)
	end
	B.lamp(0, G.top - G.deep - 2, G.z, "point", 26, 0.4, P.lampWhite)
end

local function mainLane()
	local x1, z1 = D.x1, D.z1
	-- the floor's marks: a pale line under every frame, the strafer's rail, the distance lines and their numbers
	for _, z in D.PIERS do
		if z > D.STAGE.z + 2 then B.line(D.split + 1.2, z, x1 - 2, z, Y0 + 0.01, 0.7, P.line, "PierLine") end
	end
	for k, z in { -8176, -8206, -8236 } do
		local fy = if z < D.STAGE.z then D.STAGE.y else Y0
		blk("Scenery", "DistLine", D.split + 1.2, x1 - 2, fy + 0.03, fy + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true })
		if z < D.STAGE.z then distWord(-12, fy, z, k) else distWord(0, fy, z, k) end
	end
	local dm = T.DUMMIES.Dummy
	K.rail(B, dm[1], Y0, dm[3], 11.4, {})
	-- (no live-fire end since 18 Nov, the owner: "this button is redundant", "these shooting dummies are now redundant":
	-- its console, its two shooters on their round stands, its line, posts, word and heal pad are gone; the stage
	-- stays, the garage door's floor)
	-- two spots on the garage door, from the last bay
	B.lamp(-8, 263, z1 + 10, "spot", 28, 0.55, P.lampWhite, { look = V3(0, 246, z1), angle = 70 })
	B.lamp(8, 263, z1 + 10, "spot", 28, 0.55, P.lampWhite, { look = V3(0, 246, z1), angle = 70 })
	-- cover on the east walk: a chest-high wall, then a head-high one
	cover(14.2, -8194, "low")
	cover(19.2, -8216, "high")
end

local function practiceLane()
	local x0, z0, z1 = D.x0, D.z0, D.z1
	local DK = D.DECK
	local pr = K.folderIn(B.root, "Practice")
	-- the lane wall: waist high, slate with a pale cap, from the 10 m line's front to the stage's step (open at both ends)
	blk("Shell", "LaneWall", D.split - 1, D.split + 1, Y0, Y0 + 3.2, -8162, -8202, P.slate)
	blk("Shell", "LaneWallCap", D.split - 1.2, D.split + 1.2, Y0 + 3.2, Y0 + 3.6, -8161.8, -8202.2, P.trim)
	-- the deck at the far end: a slate mass with the white nose, the board on its face, stairs up its east side
	slab("Deck", x0, DK.x1, DK.z0, z1, DK.top, DK.top - 236, { "z0" })
	local steps = 8
	local rise = (DK.top - Y0) / steps
	for k = 1, steps do
		local za, zb = DK.z0 + 16 - (k - 1) * 2, DK.z0 + 16 - k * 2
		blk("Shell", "DeckStep", DK.x1, D.split, Y0, Y0 + k * rise, za, zb, P.ledge)
		B.part("Shell", "StepNose", CF((DK.x1 + D.split) / 2, Y0 + k * rise - 0.3, za + 0.05), V3(D.split - DK.x1, 0.6, 0.6), P.trim, { cyl = true })
	end
	blk("Shell", "DeckLanding", DK.x1, D.split, 236, DK.top, DK.z0, z1, P.ledge)
	blk("Shell", "DeckKerb", D.split - 0.6, D.split, DK.top, DK.top + 1.1, DK.z0, z1 - 0.05, P.slate) -- (a kerb along the deck's edge over the stage, 4 below)
	local bw, bh = 16, 3.6
	local board = Instance.new("Part")
	board.Name = "Board"; board.Anchored = true; board.CanCollide = false; board.CanQuery = false; board.CanTouch = false; board.CastShadow = false
	board.Size = V3(bw, bh, 0.25); board.Color = Color3.fromHex(P.board); board.Material = Enum.Material.SmoothPlastic
	local bx = (x0 + DK.x1) / 2
	board.CFrame = B.at(CFrame.lookAt(V3(bx, Y0 + 0.5 + bh / 2, DK.z0 + 0.15), V3(bx, Y0 + 0.5 + bh / 2, DK.z0 + 10)))
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 40; g.LightInfluence = 0
	for i, c in { { "Damage", "DAMAGE", "0" }, { "Dps", "DPS", "-" }, { "Ttk", "TIME TO KILL", "-" } } do
		local col = Instance.new("Frame")
		col.Name = c[1]; col.BackgroundTransparency = 1; col.Size = UDim2.fromScale(1 / 3, 1); col.Position = UDim2.fromScale((i - 1) / 3, 0)
		local lab = Instance.new("TextLabel")
		lab.Name = c[1] .. "Label"; lab.BackgroundTransparency = 1; lab.Size = UDim2.fromScale(0.9, 0.26); lab.Position = UDim2.fromScale(0.05, 0.1)
		lab.TextScaled = true; lab.Text = c[2]; lab.TextColor3 = Color3.fromHex(P.grey)
		lab.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.SemiBold)
		lab.Parent = col
		local val = Instance.new("TextLabel")
		val.Name = c[1] .. "Value"; val.BackgroundTransparency = 1; val.Size = UDim2.fromScale(0.9, 0.5); val.Position = UDim2.fromScale(0.05, 0.4)
		val.TextScaled = true; val.Text = c[3]; val.TextColor3 = Color3.fromHex(P.pale)
		val.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
		val.Parent = col
		col.Parent = g
	end
	g.Parent = board
	board.Parent = pr
	-- the rails: slow at 10 m, quicker at 20 m, quickest on the deck at 30 m
	local s3, s4, s5 = T.DUMMIES.Stand3, T.DUMMIES.Stand4, T.DUMMIES.Dummy2
	K.rail(B, s3[1], Y0, s3[3], T.RAILS.Stand3[1], { line = true })
	K.rail(B, s4[1], s4[2], s4[3], T.RAILS.Stand4[1])
	K.rail(B, s5[1], DK.top, s5[3], T.RAILS.Dummy2[1])
	for _, z in D.PIERS do if z > DK.z0 + 1 then B.line(x0 + 2.2, z, D.split - 1.2, z, Y0 + 0.01, 0.7, P.line, "PierLine") end end
	for k, z in { -8176, -8206, -8236 } do
		local fy = if z < DK.z0 then DK.top else Y0
		local xe = if z < DK.z0 then DK.x1 else D.split - 1.2
		blk("Scenery", "DistLine", x0 + 2.2, xe, fy + 0.03, fy + 0.06, z + 0.25, z - 0.25, P.line, { ghost = true })
		distWord(xe - 4.2, fy, z, k, 6)
	end
	-- the consoles at the lane's start, BEHAVIOUR and HEALTH (Dummies.luau), and a heal pad
	console(pr, "BehaviourButton", "BEHAVIOUR", x0 + 6, z0 - 12, P.amber, "Change", "BEHAVIOUR")
	console(pr, "HealthButton", "HEALTH", x0 + 12, z0 - 12, P.chill, "Change", "HEALTH")
	K.healPad(B, D.split - 5, Y0, z0 - 10)
	-- the lane's box: its dummies shoot back only at players inside it
	local zone = Instance.new("Part")
	zone.Name = "Zone"; zone.Anchored = true; zone.Transparency = 1; zone.CanCollide = false; zone.CanQuery = false; zone.CanTouch = false
	zone.Size = V3(D.split - x0, 30, z0 - z1); zone.CFrame = B.cf((x0 + D.split) / 2, Y0 + 15, (z0 + z1) / 2)
	zone.Parent = pr
	-- cover along the west wall: a chest-high wall, then a head-high one
	cover(x0 + 4.8, -8170, "low")
	cover(x0 + 4.8, -8188, "high")
	-- the big target on the end wall over the deck, lit from the last bay
	local tx = (x0 + DK.x1) / 2 + 4
	B.put("tv_target", CF(tx, 256, z1 + 0.75), { name = "AisleTarget", scale = 0.75 })
	B.lamp(tx, 264, z1 + 10, "spot", 24, 0.6, P.lampWhite, { look = V3(tx, 256, z1), angle = 70 })
end

-- ---------------------------------------------------------------- the course: lobby and hall
local function lobby()
	local x0, x1, z0, z1 = LOB.x0, LOB.x1, LOB.z0, LOB.z1
	local top = LOB.ceil + 2
	blk("Shell", "LobbyFloor", x0, x1, 236, Y0, z0, z1, P.floor)
	-- the east wall with the muster's west passage (as the old strip's), the south wall; the north wall is the dummies
	-- hall's front, the west the course hall's east wall
	blk("Shell", "LobbyWallE", x1, x1 + 4, 234, top, z0 + 4, MZ + PASS, P.courseWall)
	blk("Shell", "LobbyWallE", x1, x1 + 4, 234, top, MZ - PASS, z1 - 4, P.courseWall)
	blk("Shell", "LobbyWallE", x1, x1 + 4, MY + 12, top, MZ + PASS, MZ - PASS, P.courseWall)
	blk("Shell", "LobbyWallS", x0 - 4, x1 + 4, 234, top, z0 + 4, z0, P.courseWall)
	blk("Shell", "LobbyCeiling", x0, x1, LOB.ceil, top, z0, z1, P.ceil)
	-- bones: a plinth and band round it, two beams across with their noses, lit coffers between
	for _, w in { { x1, -1, MZ - PASS, z1 }, { x1, -1, z0, MZ + PASS } } do
		blk("Shell", "Dado", w[1], w[1] + w[2] * 0.2, Y0, Y0 + 1.2, w[3], w[4], P.floor2, { ghost = true })
	end
	endWall(z0, -1, x0, x1, Y0)
	endWall(z1, 1, x0, x1, Y0)
	roof(x0, x1, z0, z1, { -8111.5, -8132.5 }, LOB.ceil - 2, 2, 0, { -58, -40 }, 10, { noSlab = true })
	for _, z in { -8111.5, -8132.5 } do
		blk("Shell", "Pier", x1, x1 - 2, Y0, LOB.ceil - 2, z - 1.6, z + 1.6, P.pier)
		blk("Shell", "PierBase", x1, x1 - 2.25, Y0, Y0 + 1.3, z - 1.85, z + 1.85, P.deep)
		blk("Scenery", "SconceHousing", x1 - 2, x1 - 2.6, 247.5, 250.5, z - 0.9, z + 0.9, P.dark)
		blk("Scenery", "SconceLight", x1 - 2.55, x1 - 2.7, 247.9, 250.1, z - 0.55, z + 0.55, P.warm, { ghost = true, mat = NEON })
	end
	-- the long walls panelled: piers lined up with the beams, the pale panels with their lit cove between
	endBones(z0, -1, { -49 }, x0, x1 - 2, Y0, LOB.ceil - 2, { 245, 252 })
	endBones(z1, 1, { -49 }, x0, x1 - 2, Y0, LOB.ceil - 2, { 245, 252 })
	-- two benches against the south wall, facing the course
	for _, x in { -60, -40 } do B.put("tv_bench", CF(x, Y0, z0 - 2.2), { name = "Bench" }) end
	B.lamp(-49, LOB.ceil - 2, -8122, "point", 26, 0.6, P.lampWhite)
end

local function courseShell()
	local x0, x1, z0, z1 = C.x0, C.x1, C.z0, C.z1
	local top = C.top + 4 + 2
	blk("Shell", "CourseFloor", x0 - 3.95, x1, 234, Y0, z0 + 3.95, z1 - 3.95, P.courseFloor)
	blk("Shell", "CourseWallW", x0 - 4, x0, 234, top, z0 + 4, z1 - 4, P.courseWall)
	blk("Shell", "CourseWallS", x0 - 4, x1 + 4, 234, top, z0 + 4, z0, P.courseWall)
	-- the east wall: the lobby's way in at the south (a wide opening under a deep lintel), whole north of it
	local o = C.open
	blk("Shell", "Threshold", x1, x1 + 4, 234, Y0, o[1], o[2], P.courseFloor)
	blk("Shell", "CourseWallE", x1, x1 + 4, 234, top, z0 + 4, o[1], P.courseWall)
	blk("Shell", "CourseWallE", x1, x1 + 4, o[3], top, o[1], o[2], P.courseWall)
	blk("Shell", "CourseWallE", x1, x1 + 4, 234, top, o[2], z1 - 4, P.courseWall)
	for _, z in { o[1], o[2] } do
		B.part("Shell", "OpenNose", CF(x1 - 0.1, (Y0 + o[3]) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), V3(o[3] - Y0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
		B.part("Shell", "OpenNose", CF(x1 + 4.1, (Y0 + o[3]) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), V3(o[3] - Y0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	end
	B.part("Shell", "OpenNose", CF(x1 - 0.1, o[3], (o[1] + o[2]) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(o[1] - o[2] + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	B.part("Shell", "OpenNose", CF(x1 + 4.1, o[3], (o[1] + o[2]) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(o[1] - o[2] + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	-- the north wall, with the TOP room's hole through it (T.TOPD3)
	local td = T.TOPD3
	local hx0, hx1, hy0, hy1 = td.x - td.w / 2, td.x + td.w / 2, td.y, td.y + td.h
	blk("Shell", "CourseWallN", x0 - 4, hx0, 234, top, z1, z1 - 4, P.courseWall)
	blk("Shell", "CourseWallN", hx1, x1 + 4, 234, top, z1, z1 - 4, P.courseWall)
	blk("Shell", "CourseWallN", hx0, hx1, 234, hy0, z1, z1 - 4, P.courseWall)
	blk("Shell", "CourseWallN", hx0, hx1, hy1, top, z1, z1 - 4, P.courseWall)
	-- bones
	longWall(x0, 1, C.FR, z0, z1, Y0, C.top, { 283, 293 }, { sconce = 263, haunch = true }) -- (over the walk, clear of an eye on it)
	local east = {}
	for _, z in C.FR do if z < o[2] - 2 or z > o[1] + 2 then table.insert(east, z) end end
	longWall(x1, -1, east, o[2], z1, Y0, C.top, { 283, 293 }, { sconce = 249.5, haunch = true })
	endWall(z0, -1, x0, x1, Y0)
	endBones(z0, -1, { -112, -92 }, x0, x1, Y0, C.top, { 283, 293 })
	-- the roof: beams at the frames, the skylight drum over the core (open to the sky, an unseen lid), lit panels
	local S = C.SKY
	local function inSky(x, z) return x > S.x0 - 2 and x < S.x1 + 2 and z < S.z0 + 2 and z > S.z1 - 2 end
	roof(x0 - 4, x1 + 4, z0 + 4, z1 - 4, C.FR, C.top - 1, 5, 0, { C.xm - 16, C.xm + 16 }, 10, { noSlab = true, skip = inSky })
	local cy0, cy1 = C.top + 4, C.top + 6
	blk("Shell", "CourseCeiling", x0 - 4, x1 + 4, cy0, cy1, z0 + 4, S.z0, P.ceil)
	blk("Shell", "CourseCeiling", x0 - 4, x1 + 4, cy0, cy1, S.z1, z1 - 4, P.ceil)
	blk("Shell", "CourseCeiling", x0 - 4, S.x0, cy0, cy1, S.z0, S.z1, P.ceil)
	blk("Shell", "CourseCeiling", S.x1, x1 + 4, cy0, cy1, S.z0, S.z1, P.ceil)
	for _, w in { { S.x0 - 1.2, S.x0 + 1.2, S.z0 + 1.2, S.z1 - 1.2 }, { S.x1 - 1.2, S.x1 + 1.2, S.z0 + 1.2, S.z1 - 1.2 },
		{ S.x0 - 1.2, S.x1 + 1.2, S.z0 + 1.2, S.z0 - 1.2 }, { S.x0 - 1.2, S.x1 + 1.2, S.z1 + 1.2, S.z1 - 1.2 } } do
		blk("Shell", "SkyDrum", w[1], w[2], C.top + 4, S.top, w[3], w[4], P.wall2)
	end
	B.solid("SkyLid", CF((S.x0 + S.x1) / 2, S.top + 2, (S.z0 + S.z1) / 2), V3(S.x1 - S.x0 + 4, 4, S.z0 - S.z1 + 4))
	for _, w in { { S.x0 - 1.6, S.x1 + 1.6, S.z0 + 1.6, S.z0 - 1.6 }, { S.x0 - 1.6, S.x1 + 1.6, S.z1 + 1.6, S.z1 - 1.6 },
		{ S.x0 - 1.6, S.x0 + 1.6, S.z0 - 1.6, S.z1 + 1.6 }, { S.x1 - 1.6, S.x1 + 1.6, S.z0 - 1.6, S.z1 + 1.6 } } do
		blk("Shell", "SkyCoping", w[1], w[2], S.top, S.top + 0.6, w[3], w[4], P.wall2) -- (a ring round the drum's top, open in the middle)
	end
	for _, e in { { x0 - 4.4, x0 - 2.4 }, { x1 + 2.4, x1 + 4.4 } } do
		blk("Shell", "RoofCoping", e[1], e[2], cy1, cy1 + 2, z0 + 4.4, z1 - 4.4, P.wall2, { nq = true })
	end
	-- lamps: down the hall high up, and over the walk
	for i, z in C.GZ do
		if i % 2 == 0 then
			B.lamp(C.xm, C.top - 4, z, "point", 44, 0.55, P.lampWhite)
			B.lamp(C.WALK.x1 + 2, C.WALK.top + 9, z, "point", 18, 0.4, P.lampWhite)
		end
	end
end

local function courseRoute()
	local x0, x1, z0, z1 = C.x0, C.x1, C.z0, C.z1
	local W, G, CO = C.WALK, C.GAL, C.CORE
	-- the TOP gallery: a solid mass the hall's width at the far end, a lit edge and the white nose on its face, panels
	-- let into the face; the TOP frame and door in the wall over it (TrainingV2.topRoom, TrainingLot.eggDoor)
	slab("Gallery", x0, x1, G.z0, z1, G.top, G.top - 234, { "z0" })
	for _, x in { -124, -110, -94, -80 } do
		blk("Shell", "GalleryPanel", x - 5, x + 5, Y0 + 3, G.top - 5, G.z0 + 0.25, G.z0, P.massPanel, { ghost = true })
	end
	for _, x in { -117, -102, -87 } do -- (pilasters between the panels, the middle one under the TOP door)
		blk("Shell", "GalleryPier", x - 1.6, x + 1.6, Y0, G.top - 1.6, G.z0 + 1, G.z0, P.pier)
		blk("Shell", "PierBase", x - 1.85, x + 1.85, Y0, Y0 + 1.3, G.z0 + 1.25, G.z0, P.deep)
	end
	blk("Shell", "Dado", x0 + 2, x1 - 2, Y0, Y0 + 1.2, G.z0 + 0.2, G.z0, P.floor2, { ghost = true })
	-- the west walk: on brackets at the frames, a gap to cross, the white nose on its open edge
	for _, seg in { { W.z0, W.gap[1] }, { W.gap[2], W.z1 } } do slab("Walk", W.x0, W.x1, seg[1], seg[2], W.top, 1.4, { "x1" }) end
	for _, seg in { { W.gap[1], W.gap[1] }, { W.gap[2], W.gap[2] } } do
		B.part("Shell", "Nose", CF((W.x0 + W.x1) / 2, W.top - 0.1, seg[1]), V3(W.x1 - W.x0, 1.4, 1.4), P.trim, { cyl = true })
	end
	-- the watch steps: broad walkable steps up the south wall from the lobby's side to the walk's start, noses lit, a
	-- cheek wall on the hall's side
	local ST = C.STEPS
	for k = 1, ST.n do
		local xa, xb = ST.x0 - (k - 1) * ST.run, ST.x0 - k * ST.run
		blk("Shell", "WatchStep", xb, xa, Y0, Y0 + k * ST.rise, ST.z0, ST.z1, P.ledge)
		B.part("Shell", "Nose", CF(xa + 0.1, Y0 + k * ST.rise - 0.1, (ST.z0 + ST.z1) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(ST.z1 - ST.z0), 1.4, 1.4), P.trim, { cyl = true })
		blk("Scenery", "EdgeLight", xa + 0.05, xa + 0.2, Y0 + k * ST.rise - 1.3, Y0 + k * ST.rise - 1.0, ST.z0, ST.z1, P.litEdge, { ghost = true, mat = NEON })
	end
	local lx = ST.x0 - ST.n * ST.run
	cheek("x", ST.x0, lx, Y0, W.top, ST.z1 - 0.6, ST.z1, P.slate)
	blk("Shell", "WatchLanding", W.x1, lx, Y0, W.top, ST.z0, ST.z1, P.ledge)
	B.part("Shell", "Nose", CF((W.x1 + lx) / 2, W.top - 0.1, ST.z1), V3(lx - W.x1, 1.4, 1.4), P.trim, { cyl = true })
	-- the east block: a pale mass against the east wall with panels, the white nose round its open edges
	local BK = C.BLOCK
	blk("Shell", "EastBlock", BK.x0, BK.x1, Y0, BK.top, BK.z0, BK.z1, P.mass)
	blk("Shell", "CoreBase", BK.x0 - 0.25, BK.x1, Y0, Y0 + 1.3, BK.z0 + 0.25, BK.z1 - 0.25, P.deep)
	blk("Shell", "BlockPanel", BK.x0 - 0.25, BK.x0, Y0 + 3, BK.top - 3, BK.z0 - 3, BK.z1 + 3, P.massPanel, { ghost = true })
	for _, z in { BK.z0, BK.z1 } do
		blk("Shell", "BlockPanel", BK.x0 + 3, BK.x1 - 1, Y0 + 3, BK.top - 3, z, z + (if z == BK.z0 then 0.25 else -0.25), P.massPanel, { ghost = true })
		B.part("Shell", "Nose", CF((BK.x0 + BK.x1) / 2, BK.top - 0.1, z), V3(BK.x1 - BK.x0, 1.4, 1.4), P.trim, { cyl = true })
	end
	B.part("Shell", "Nose", CF(BK.x0, BK.top - 0.1, (BK.z0 + BK.z1) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(BK.z0 - BK.z1 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
	-- the steel bridge across the hall, walk to block: a girder deck, noses both sides, an amber line along its faces
	-- (the course's accent is the same one), a post under its middle
	local BR = C.BRIDGE
	blk("Shell", "Bridge", W.x1, BK.x0, W.top - 2.4, W.top, BR.z0, BR.z1, P.pier)
	for _, z in { BR.z0, BR.z1 } do
		B.part("Shell", "Nose", CF((W.x1 + BK.x0) / 2, W.top - 0.1, z), V3(BK.x0 - W.x1, 1.2, 1.2), P.trim, { cyl = true })
		local sg = if z == BR.z0 then 1 else -1
		blk("Scenery", "BridgeLine", W.x1, BK.x0, W.top - 1.4, W.top - 1.0, z, z + sg * 0.12, P.amber, { ghost = true })
	end
	blk("Shell", "BridgePost", BR.post - 1.2, BR.post + 1.2, Y0, W.top - 2.4, BR.z0 - 1.8, BR.z1 + 1.8, P.pier2)
	blk("Shell", "PierBase", BR.post - 1.45, BR.post + 1.45, Y0, Y0 + 1.3, BR.z0 - 1.55, BR.z1 + 1.55, P.deep)
	-- the stair from the bridge up to the gallery
	local GS = C.GSTAIR
	local zf = BR.z1
	for k = 1, GS.n do
		local za, zb = zf - (k - 1) * GS.run, zf - k * GS.run
		blk("Shell", "GalleryStep", GS.x0, GS.x1, Y0, W.top + k * GS.rise, za, zb, P.ledge)
		B.part("Shell", "StepNose", CF((GS.x0 + GS.x1) / 2, W.top + k * GS.rise - 0.3, za - 0.05), V3(GS.x1 - GS.x0, 0.6, 0.6), P.trim, { cyl = true })
	end
	for _, c in { { GS.x0 - 0.6, GS.x0 }, { GS.x1, GS.x1 + 0.6 } } do
		cheek("z", zf, zf - GS.n * GS.run, W.top, G.top, c[1], c[2], P.slate)
		blk("Shell", "StairSide", c[1], c[2], Y0, W.top, zf, zf - GS.n * GS.run, P.slate) -- (the cheek carried down to the floor)
	end
	for _, z in C.GZ do
		if z < W.z0 and z > W.z1 and not (z < W.gap[1] and z > W.gap[2]) then
			blk("Shell", "Bracket", W.x0, W.x1 - 1, W.top - 5.4, W.top - 1.4, z - 1.4, z + 1.4, P.pier)
			blk("Shell", "BracketFoot", W.x0, W.x0 + 3, W.top - 7.4, W.top - 5.4, z - 1.2, z + 1.2, P.pier) -- (stepped, not a brace: a slanting one came within 1 of an eye under the walk)
		end
	end
	-- the core: a plinth (its top the ledge you land on), the body on it, both in the course's pale mass with panels,
	-- the skylight over it; the bridge from the walk to its ledge
	local px0, px1, pz0, pz1 = CO.x - CO.plinth, CO.x + CO.plinth, CO.z + CO.plinth, CO.z - CO.plinth
	blk("Shell", "CorePlinth", px0, px1, Y0, CO.ledge, pz0, pz1, P.mass)
	blk("Shell", "CoreBase", px0 - 0.25, px1 + 0.25, Y0, Y0 + 1.3, pz0 + 0.25, pz1 - 0.25, P.deep)
	blk("Shell", "CorePanel", px0 - 0.25, px0, Y0 + 3, CO.ledge - 3, pz0 - 3, pz1 + 3, P.massPanel, { ghost = true })
	blk("Shell", "CorePanel", px1, px1 + 0.25, Y0 + 3, CO.ledge - 3, pz0 - 3, pz1 + 3, P.massPanel, { ghost = true })
	blk("Shell", "CorePanel", px0 + 3, px1 - 3, Y0 + 3, CO.ledge - 3, pz0, pz0 + 0.25, P.massPanel, { ghost = true })
	blk("Shell", "CorePanel", px0 + 3, px1 - 3, Y0 + 3, CO.ledge - 3, pz1 - 0.25, pz1, P.massPanel, { ghost = true })
	for _, e in { "x0", "x1", "z0", "z1" } do
		if e == "x0" or e == "x1" then
			local x = if e == "x0" then px0 else px1
			B.part("Shell", "Nose", CF(x, CO.ledge - 0.1, CO.z) * CFrame.Angles(0, math.pi / 2, 0), V3(pz0 - pz1 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
		else
			local z = if e == "z0" then pz0 else pz1
			B.part("Shell", "Nose", CF(CO.x, CO.ledge - 0.1, z), V3(px1 - px0 + 1.4, 1.4, 1.4), P.trim, { cyl = true })
		end
	end
	local b = CO.body
	blk("Shell", "CoreBody", CO.x - b, CO.x + b, CO.ledge, CO.top, CO.z + b, CO.z - b, P.pier2)
	blk("Shell", "CoreTop", CO.x - b - 0.3, CO.x + b + 0.3, CO.top - 0.6, CO.top, CO.z + b + 0.3, CO.z - b - 0.3, P.trim)
	for _, sx in { -1, 1 } do for _, sz in { -1, 1 } do
		blk("Scenery", "CoreEdge", CO.x + sx * b - 0.15, CO.x + sx * b + 0.15, CO.ledge + 1, CO.top - 1, CO.z + sz * b - 0.15, CO.z + sz * b + 0.15, P.litEdge, { ghost = true, mat = NEON })
	end end
	-- the bridge from the walk to the core's ledge, its noses on both sides
	blk("Shell", "Bridge", W.x1, px0, W.top - 1.4, W.top, CO.z + 3, CO.z - 3, P.ledge)
	for _, sz in { -1, 1 } do
		B.part("Shell", "Nose", CF((W.x1 + px0) / 2, W.top - 0.1, CO.z + sz * 3), V3(px0 - W.x1, 1.4, 1.4), P.trim, { cyl = true })
	end
	-- (no jump pads since 18 Nov, the owner: "get rid of these teleporters": the watch steps, the bridge and the stair are
	-- the way up; the core's top is the grapple rings')
	-- grapple rings on the beams: over the floor run, and from the core's top north to the gallery
	for _, h in { { C.xm - 14, -8150 }, { C.xm + 14, -8166 }, { C.xm, -8230 }, { C.xm - 10, -8262 } } do
		B.put("tv_hoop", CF(h[1], C.top, h[2]), { name = "GrappleRing" })
	end
	-- the floor run at the start: cover to vault and weave through
	for _, c in { { -114, -8126, "low", true }, { -90, -8130, "high" }, { -100, -8146, "low", true }, { -122, -8142, "high" } } do cover(c[1], c[2], c[3], c[4]) end
	-- the runner: a rail across the floor between the core and the gallery
	local rn = T.DUMMIES.Runner
	K.rail(B, rn[1], Y0, rn[3], T.RAILS.Runner[1], { line = true })
	-- the playground's secret: a bullseye high on the north wall over the gallery's west end (grapple into it)
	local bx, by, bz = x0 + 6, 283, z1 + 0.45
	B.put("tv_target", CF(bx, by, bz), { name = "SecretBullseye", scale = 0.6 })
	B.trigger("ToPlayground", bx - 3, bx + 3, by - 3, by + 3, z1 + 1.2, z1 + 4.2)
	local ta = K.folderIn(B.doors, "TrainingArrive")
	for _, x in { x0 + 2, x0 + 6, x0 + 10 } do
		local p = B.marker(ta, "TrainingArrive", x, G.top + 0.1, z1 + 6, V3(x, G.top, z1 + 20))
		p:SetAttribute("Built", "TrainingV2")
	end
	-- the TOP: its frame and word, the room behind (TrainingV2.topRoom); the door itself is TrainingLot's
	local td = T.TOPD3
	B.put("tv_frameWide", CF(td.x, td.y, td.frame), { name = "FrameTop", scale = 0.75 })
	K.topRoom(B, td)
	B.text("WordTOP", { { "TOP", P.amber, "B", 1 } }, 7, 1.5, CF(td.x, td.y + 10.9, td.frame + 2.05) * CFrame.Angles(0, math.pi, 0), { plate = P.pier, thick = 0.2 })
end

-- ---------------------------------------------------------------- build
function R.build(b): string
	B = b
	hallShell()
	overlook()
	gantry()
	mainLane()
	practiceLane()
	lobby()
	courseShell()
	courseRoute()
	-- the dummies' spots
	local ds = K.folderIn(B.mk, "DummySpots")
	for n, d in T.DUMMIES do
		local m = B.marker(ds, n, d[1], d[2], d[3], V3(d[1], d[2], d[3] + 10))
		local r = T.RAILS[n]
		if r then m:SetAttribute("Span", r[1]); m:SetAttribute("Speed", r[2]) end
		if T.LANE[n] then m:SetAttribute("Lane", "practice") end
	end
	return "rooms v3"
end

return R
