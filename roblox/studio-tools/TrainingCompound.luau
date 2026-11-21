--!nocheck
-- TRAINING v5, THE COMPOUND (20 Nov 2026; vault Hubs/Training redo plan.md). The owner: "redo training hub entirely
-- basing it off the overwatch training hub in a way? keep shooting range, ... the gun shop eveyrthing else good to
-- change, dummy area, shooting range, course outside teleporter to parkour", then "oh I though training hub would get
-- enrirelyt redone?" and "by old design I meant lke the chunker structes you know? we just add subtle texture to them now".
-- A walled practice compound in the open, read whole from the GATEHOUSE's balcony: you arrive in the gatehouse, its big
-- south portal opens onto the BALCONY over the FIELD (the dummies, the GANTRY across it at 20 m), the COURSE's stepped
-- blocks and grand stair climb away on the right to the crowned TOP (the parkour teleporter, the egg door), the range's
-- long wall on the left. The range is through the gatehouse's east side (the range walk), the TUTORIAL HALL's corridor
-- through its west door. The range and the gun shop are TrainingV2's own range(), as before.
-- TrainingV2 loads this when T.ROOMS == "v5": C.apply(T, K) at load sets what the rest reads (T.DUMMIES, T.RAILS,
-- T.LANE, T.DUMMY_HP, T.HEALBACK, T.GOLD1, T.COURSE, T.TOPD3, T.EGG_DOOR, T.LOT_PANEL, T.ZONE, T.STAGE, T.TESTLINE,
-- T.TUTORIAL), C.build(B) builds everything but the range (C.OWN_ARRIVAL: no muster), C.SEAL the seal test's points.
-- The look: the 16 Nov chunky family (a few big shapes, rounded noses, quiet warm greys, one amber accent) with a SUBTLE
-- texture on top: MaterialVariants (C.materials(): pictures from tools/roblox/training_textures.py) put on by role at
-- the end of the build. The kit: tools/roblox/training_redo_models.py (Model C.KIT; T.import(C.KIT) puts it in
-- JankfireMeshes) and the 16 Nov tv_ pieces.
local C = {}
local V3, CF = Vector3.new, CFrame.new
local T, K, P, B
local NEON = Enum.Material.Neon
C.OWN_ARRIVAL = true
C.PUSH = 1
C.KIT = 97955674324764 -- tr_kit_1 (training_redo_models.py)
-- the subtle textures (Image assets) and how they tile; base = the material a part wears under the variant
C.TEX = {
	TrPlaster = { id = 71866904760269, studs = 12, base = Enum.Material.Plastic, organic = true },
	TrConcrete = { id = 123903475695499, studs = 16, base = Enum.Material.Concrete, organic = false },
	TrSlate = { id = 103582246698039, studs = 10, base = Enum.Material.Slate, organic = true },
	TrPaint = { id = 94577606854356, studs = 8, base = Enum.Material.Plastic, organic = true },
	TrTile = { id = 85307023114787, studs = 8, base = Enum.Material.Plastic, organic = false },
}

-- ---------------------------------------------------------------- the plan (world coordinates, y up; "north" = toward z -7996)
local Y0, GY = 240, 244 -- the field and the course; the gatehouse, balcony, walk and tutorial hall
-- the quiet family (warm off-white walls, mid-grey piers and frames, slate masses), one amber accent
local W = {
	wall = "8b8d92", wall2 = "95979c", warm = "8c8076", pier = "dcd3c3", pier2 = "cbc1ae", trim = "efe9dd", ceil = "8f9196",
	slate = "8e9298", plinth = "7d8086", deep = "555a62", floor = "86888c", floor2 = "76787c", ledge = "80848a", amber = "f0a53a",
	lamp = "ffe8cc", warmLamp = "ffd6a0", teal = "5fd89a", line = "b9b3a6", board = "2b3038", pale = "eeeae2", grey = "9aa0a8",
	panel = "efe2c8", panelSoft = "a89c86",
}
-- the kit's own colours (in its pieces' names) to this palette: its frames, towers and trims cream, its feet dark
local TRC = { ["8e9197"] = W.pier, ["7b7f87"] = W.pier2, ["e4e0d6"] = W.trim, ["d3cec4"] = "ddd5c6", ["c9c3b8"] = W.wall,
	["5f646e"] = W.plinth, ["4f545d"] = W.deep }
local GH = { x0 = -72, x1 = -8, z0 = -8064, z1 = -8132, nave = { -56, -24 }, piers = { -8080, -8096, -8112 }, aisle = 260, naveTop = 268, top = 272 }
GH.xm = (GH.x0 + GH.x1) / 2 -- -40: the compound's axis
GH.DOORS = { range = { z0 = -8114, z1 = -8130 }, tut = { z0 = -8120, z1 = -8132 } }
local BAL = { x0 = -104, x1 = 20, z0 = -8132, z1 = -8150 } -- (z0 under the gatehouse wall: no slit by the walk)
local WALK = { x0 = -4, x1 = 26, z0 = -8114, z1 = -8130, top = 256 }
local F = { x0 = -100, x1 = 20, z0 = -8150, z1 = -8258, stage = { x0 = -30, z0 = -8228, y = 242 }, towers = { -96, -64, 16 }, gz = -8210, gtop = 256.2 }
F.DECK = { x0 = -100, x1 = -66, z0 = -8228, top = 246 } -- the practice lane's deck at 30 m
local CO = { x0 = -330, x1 = -104, z0 = -8140, z1 = -8254, wallTop = 290 }
CO.TOP = { x0 = -330, x1 = -268, z0 = -8226, top = 270 } -- its back is the course's south wall (CO.z1)
CO.TOWER = { x = -196, z = -8196 }
CO.STAIR = { x0 = -268, x1 = -204, z0 = -8238, z1 = -8254 } -- the grand stair up the south wall, 240 at x1 to 270 at x0
local TU = { x0 = -268, x1 = -76, cz0 = -8120, cz1 = -8132, ceil = 258, rz0 = -8116, rz1 = -8006, top = 276 }
TU.ROOMS = {}
for i = 1, 4 do local x0 = -264 + (i - 1) * 44; TU.ROOMS[i] = { x0 = x0, x1 = x0 + 40, xm = x0 + 20 } end
local LID = { y = 296, x0 = -334, x1 = 26, z0 = -8132, z1 = -8262 } -- the unseen lid over the open part (field, course, balcony)
C.GH, C.F, C.CO, C.TU = GH, F, CO, TU

-- ---------------------------------------------------------------- what the rest reads
function C.apply(t, k)
	T, K = t, k
	P = T.P
	T.ZONE = { -336, 86, 220, 312, -7996, -8308 }
	T.STAGE = V3(0, 0, 800) -- (a staging copy north of the hall: nothing stands there)
	T.TESTLINE = V3(-14, 249, -8144) -- (the gun sessions' spot: on the balcony, over Stand1)
	T.NO_LIVE = true
	-- the dummies: the field's main lane (10 m pair, 20 m strafer under the gantry, armoured and heal-back on the stage at
	-- 30 m), the practice lane (rails at 10 m, on the gantry at 20 m, on the deck at 30 m), the course's runner
	local sy = F.stage.y
	T.DUMMIES = {
		Dummy = { -4, Y0, F.gz }, Stand1 = { -14, Y0 + 1, -8180 }, Stand2 = { 6, Y0 + 1, -8180 },
		Stand3 = { -82, Y0, -8180 }, Stand4 = { -80, F.gtop + 2.4, F.gz }, Dummy2 = { -84, F.DECK.top, -8242 },
		Runner = { -160, Y0, -8174 },
		Armour1 = { -26, sy + 1, -8240 }, Armour2 = { -18, sy + 1, -8240 }, Heal1 = { -2, sy + 1, -8240 }, Heal2 = { 6, sy + 1, -8240 },
	}
	T.RAILS = { Stand3 = { 6, 8 }, Stand4 = { 10, 14 }, Dummy2 = { 8, 20 }, Runner = { 16, 14 } }
	T.LANE = { Stand3 = true, Stand4 = true, Dummy2 = true }
	T.DUMMY_HP = { Armour1 = 300, Armour2 = 300 }
	T.HEALBACK = { Heal1 = 2, Heal2 = 2 }
	-- gold Carl 1 on the practice deck's far corner, shot from the balcony; gold 3 on the course's tower, shot from the
	-- course's start
	T.GOLD1 = { "practice deck", V3(-96, F.DECK.top, -8254), V3(-90, GY + 4, -8144) }
	T.COURSE = { tower = V3(CO.TOWER.x, 270, CO.TOWER.z), look = V3(-112, GY + 4, -8144) }
	-- the gold dummies' door: the TOP's back wall (the course's south wall), its room through the wall
	local WF = CO.z1
	T.TOPD3 = { x = -304, y = CO.TOP.top, w = 12, h = 10.5, frame = WF + 4.2, face = WF + 5.8, back = WF - 3.7, cut = 1.95, jamb = 1.8, wall = WF, backTo = WF - 4 }
	local td = T.TOPD3
	T.EGG_DOOR = { cf = CFrame.lookAt(V3(td.x, td.y, td.face), V3(td.x, td.y, td.face - 1)), w = 8.4, h = 8.6,
		cw = td.w, ch = td.h, wall = P.recess, room = td.face - td.back, door = 2.4, plate = false, green = true }
	T.LOT_PANEL = { x = td.x + 14, y = td.y + 1.6, face = WF, labels = { "DUMMIES", "RANGE", "COURSE" } }
	T.TUTORIAL = TU
	-- the seal test's points (T.check adds the range's and the basement's)
	C.SEAL = {
		V3(GH.xm, GY + 4, -8098), V3(GH.xm, GY + 20, -8098), V3(GH.xm, 274, -8098), V3(-64, GY + 4, -8080), V3(-16, GY + 4, -8120),
		V3(-81, GY + 4, -8098), V3(10, GY + 4, -8122), V3(GH.xm, GY + 6, -8143), V3(-60, GY + 30, -8143),
		V3(-40, Y0 + 4, -8180), V3(-40, Y0 + 30, -8230), V3(0, Y0 + 4, -8240), V3(-84, F.DECK.top + 4, -8245), V3(-40, F.gtop + 6, F.gz),
		V3(-120, Y0 + 4, -8150), V3(-200, Y0 + 4, -8170), V3(-300, Y0 + 4, -8150), V3(-300, CO.TOP.top + 4, -8240), V3(-230, 285, -8200),
		V3(CO.TOWER.x, 272, CO.TOWER.z), V3(td.x, td.y + 4, td.back + 1),
		V3(-180, GY + 4, -8126), V3(-100, GY + 4, -8126),
	}
	for _, r in TU.ROOMS do
		for _, q in { V3(r.xm, GY + 4, -8100), V3(r.xm, 262, -8060), V3(r.x0 + 2, 270, -8016), V3(r.xm, GY + 3, -8118) } do table.insert(C.SEAL, q) end
	end
end

-- ---------------------------------------------------------------- helpers
local roles = {} -- [part] = texture name (the materials pass at the end)
local function blk(folder, name, x0, x1, y0, y1, z0, z1, hex, o)
	local p = B.blk(folder, name, x0, x1, y0, y1, z0, z1, hex, o)
	if o and o.tex then roles[p] = o.tex end
	return p
end
local function nose(name, a0, a1, y, c, axis, d, hex)
	-- a rounded nose (a fat cylinder) along x (axis "x": from a0 to a1 at z = c) or along z, d across
	d = d or 1.2
	if axis == "x" then
		return B.part("Shell", name, CF((a0 + a1) / 2, y, c), V3(math.abs(a1 - a0), d, d), hex or W.trim, { cyl = true })
	end
	return B.part("Shell", name, CF(c, y, (a0 + a1) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(a1 - a0), d, d), hex or W.trim, { cyl = true })
end
-- a solid mass you stand on (slate), the white nose round its top edges (which: any of "x0","x1","z0","z1")
local function mass(name, x0, x1, z0, z1, y0, top, edges, hex)
	blk("Shell", name, x0, x1, y0, top, z0, z1, hex or W.slate, { tex = "TrSlate" })
	for _, e in edges or {} do
		if e == "x0" or e == "x1" then nose(name .. "Nose", z0, z1, top - 0.35, if e == "x0" then x0 else x1, "z")
		else nose(name .. "Nose", x0, x1, top - 0.35, if e == "z0" then z0 else z1, "x") end
	end
end
-- an unseen lid / wall: stops bodies (and the seal test meets it), lets every ray through (no grapple to the sky)
local function seal(name, x0, x1, y0, y1, z0, z1)
	local p = B.blk("Collision", name, x0, x1, y0, y1, z0, z1, W.wall, { tr = 1, nq = true, noShadow = true })
	p.CastShadow = false
	return p
end
-- words on a plate; cf's look is the way the words face (toward the reader)
local function word(name, txt, w, h, cf, plate)
	return B.text(name, { { txt, W.pale, "B", 1 } }, w, h, cf, { plate = plate or W.board, thick = 0.25 })
end
local function facing(x, y, z, tx, tz) return CFrame.lookAt(V3(x, y, z), V3(tx, y, tz)) end
-- a stair flight along x or z: from (a0, h0) to (a1, h1), c0..c1 across, n steps, rounded noses, solid under, cheeks
local function stair(name, axis, a0, a1, h0, h1, c0, c1, n, hex, cheek, noNose)
	local run = (a1 - a0) / n
	local rise = (h1 - h0) / n
	if cheek and rise > 0 then
		local lo, hi = math.min(c0, c1), math.max(c0, c1)
		for _, sd in { "c0", "c1" } do
			if cheek == sd or cheek == "both" then
				local cc0 = if sd == "c0" then c0 else c1
				local cc = if cc0 == lo then lo - 1.2 else hi + 1.2
				local y0, y1 = h0 + rise + 3.2, h1 + rise + 3.2
				local p0 = if axis == "x" then V3(a0, y0, cc) else V3(cc, y0, a0)
				local p1 = if axis == "x" then V3(a1, y1, cc) else V3(cc, y1, a1)
				B.part("Shell", name .. "CheekRail", CFrame.lookAt((p0 + p1) / 2, p1) * CFrame.Angles(0, math.pi / 2, 0), V3((p1 - p0).Magnitude, 2.6, 2.6), W.trim, { cyl = true })
			end
		end
	end
	for k = 1, n do
		if rise < 0 and k == n then break end -- (going down: the floor is the last step)
		local aa, ab = a0 + (k - 1) * run, a0 + k * run
		local top = h0 + k * rise
		local ne = if rise < 0 then ab else aa -- (the edge you step over)
		if axis == "x" then
			blk("Shell", name .. "Step", aa, ab, math.min(h0, h1) - 4, top, c0, c1, hex or W.ledge, { tex = "TrSlate" })
			if not noNose then nose(name .. "Nose", c0, c1, top - 0.3, ne, "z", 0.6) end
		else
			blk("Shell", name .. "Step", c0, c1, math.min(h0, h1) - 4, top, aa, ab, hex or W.ledge, { tex = "TrSlate" })
			if not noNose then nose(name .. "Nose", c0, c1, top - 0.3, ne, "x", 0.6) end
		end
		-- the cheeks: a stepped wall 3 over each tread, outside the flight
		local lo, hi = math.min(c0, c1), math.max(c0, c1)
		for _, sd in { "c0", "c1" } do
			if cheek == sd or cheek == "both" then
				local cc = if sd == "c0" then c0 else c1
				local q0, q1 = if cc == lo then lo - 2.4 else hi, if cc == lo then lo else hi + 2.4
				if axis == "x" then blk("Shell", name .. "Cheek", aa, ab, math.min(h0, h1) - 4, top + 3.2, q0, q1, W.slate, { tex = "TrSlate" })
				else blk("Shell", name .. "Cheek", q0, q1, math.min(h0, h1) - 4, top + 3.2, aa, ab, W.slate, { tex = "TrSlate" }) end
			end
		end
	end
end
-- a kit frame in a wall hole: the unseen solids from its opening to the hole's sides (its jambs stop you); axis = the
-- way the hole's width runs
local function jambs(name, cx, cz, axis, open, hole, h, thick)
	local gap = (hole - open) / 2
	if gap <= 0.05 then return end
	for _, sd in { -1, 1 } do
		local off = sd * (open / 2 + gap / 2)
		if axis == "x" then B.solid(name, CF(cx + off, GY + h / 2, cz), V3(gap, h, thick))
		else B.solid(name, CF(cx, GY + h / 2, cz + off), V3(thick, h, gap)) end
	end
end
-- a court wall's dress (staging 1: the open courts' walls were blank planes): a slate plinth, deep piers every 'bay'
-- on bases, string courses (o.rails), a two-tier cornice under the top. along = "x" (the wall runs along x, its face at
-- z = face) or "z" (its face at x = face); dir = the side the court is on (+1 / -1). o.holes = { { a0, a1, y0, y1 } }
-- stay clear (doors, the target, the TOP)
local function dressWall(name, along, face, dir, a0, a1, y0, y1, o)
	o = o or {}
	local holes = o.holes or {}
	local function clear(aa, ab, ya, yb)
		for _, h in holes do
			if ab > h[1] and aa < h[2] and yb > h[3] and ya < h[4] then return false end
		end
		return true
	end
	local function box(nm, aa, ab, ya, yb, out, hex, tex)
		if ab - aa < 0.2 then return end
		local c0, c1 = face, face + dir * out
		if along == "x" then blk("Shell", nm, aa, ab, ya, yb, c0, c1, hex, { tex = tex })
		else blk("Shell", nm, c0, c1, ya, yb, aa, ab, hex, { tex = tex }) end
	end
	local function segs(ya, yb)
		local cuts = {}
		for _, h in holes do if yb > h[3] and ya < h[4] then table.insert(cuts, h) end end
		table.sort(cuts, function(p, q) return p[1] < q[1] end)
		local out, x = {}, a0
		for _, h in cuts do
			if h[1] > x then table.insert(out, { x, math.min(h[1], a1) }) end
			x = math.max(x, h[2])
		end
		if x < a1 then table.insert(out, { x, a1 }) end
		return out
	end
	local function run(nm, ya, yb, out, hex, tex) for _, g in segs(ya, yb) do box(nm, g[1], g[2], ya, yb, out, hex, tex) end end
	if not o.noPlinth then run(name .. "Plinth", y0, y0 + 2.6, 1.2, W.plinth, "TrSlate") end
	local ct = y1
	run(name .. "Cornice", ct - 4.8, ct - 2.4, 2.0, W.pier2, "TrPaint")
	run(name .. "CorniceTop", ct - 2.4, ct - 1.0, 3.2, W.trim, "TrPaint")
	for _, g in segs(ct - 2.9, ct - 1.9) do
		if g[2] - g[1] > 0.6 then nose(name .. "CorniceLip", g[1], g[2], ct - 2.4, face + dir * 3.2, along, 1.8) end
	end
	local bay = o.bay or 24
	local n = math.floor((a1 - a0) / bay)
	local start = a0 + ((a1 - a0) - n * bay) / 2
	local placed = {}
	for k = 0, n do
		local pa = start + k * bay
		local inRange = not o.piersIn or (pa - 3.5 >= o.piersIn[1] and pa + 3.5 <= o.piersIn[2])
		if inRange and pa - 3.5 >= a0 and pa + 3.5 <= a1 and clear(pa - 3.6, pa + 3.6, y0, ct - 4.8) then
			box(name .. "Pier", pa - 3, pa + 3, y0, ct - 4.8, 3.2, W.pier, "TrPaint")
			box(name .. "PierCap", pa - 3.5, pa + 3.5, ct - 6.2, ct - 4.8, 3.7, W.trim, "TrPaint")
			if not o.noPlinth then box(name .. "PierBase", pa - 3.5, pa + 3.5, y0, y0 + 3.4, 3.7, W.plinth, "TrSlate") end
			table.insert(placed, pa)
		end
	end
	-- each bay framed (a cream frame half a pier wide stands 1.2 off the wall: the slate inside reads set back), and in
	-- every second bay a tall white panel in a chunky housing (o.panels)
	if o.frames then
		local fb = y0 + (if o.noPlinth then 0 else 2.6)
		local ft = ct - 6.2
		for i = 1, #placed - 1 do
			local a, b = placed[i] + 3, placed[i + 1] - 3
			if clear(a, b, fb, ft) then
				box(name .. "BayFrame", a, a + 1.6, fb, ft, 1.2, W.pier2, "TrPaint")
				box(name .. "BayFrame", b - 1.6, b, fb, ft, 1.2, W.pier2, "TrPaint")
				box(name .. "BayFrame", a + 1.6, b - 1.6, ft - 1.6, ft, 1.2, W.pier2, "TrPaint")
				box(name .. "BayFrame", a + 1.6, b - 1.6, fb, fb + 1.6, 1.2, W.pier2, "TrPaint")
				if i % 2 == 0 then
					box(name .. "BayInfill", a + 1.6, b - 1.6, fb + 1.6, ft - 1.6, 0.4, "a4a6ab", "TrPlaster")
					local m, hw = (a + b) / 2, (b - a) / 6
					local l0, l1 = ft - 5.2, ft - 2.6
					box(name .. "BayLampHousing", m - hw - 1, m + hw + 1, l0 - 1, l1 + 1, 1.3, W.trim, "TrPaint")
					local q0, q1 = face + dir * 1.3, face + dir * 1.4
					if along == "x" then blk("Scenery", name .. "BayLamp", m - hw, m + hw, l0, l1, q0, q1, W.panel, { ghost = true, mat = NEON })
					else blk("Scenery", name .. "BayLamp", q0, q1, l0, l1, m - hw, m + hw, W.panel, { ghost = true, mat = NEON }) end
				end
				if o.panels and i % 2 == 1 then
					local m, hw = (a + b) / 2, (b - a) / 4
					local p0, p1 = y0 + (o.panelY or 6), y0 + (o.panelY or 6) + (o.panelH or 14)
					box(name .. "PanelHousing", m - hw - 1.2, m - hw, p0 - 1.2, p1 + 1.2, 1.0, W.trim, "TrPaint")
					box(name .. "PanelHousing", m + hw, m + hw + 1.2, p0 - 1.2, p1 + 1.2, 1.0, W.trim, "TrPaint")
					box(name .. "PanelHousing", m - hw, m + hw, p1, p1 + 1.2, 1.0, W.trim, "TrPaint")
					box(name .. "PanelHousing", m - hw, m + hw, p0 - 1.2, p0, 1.0, W.trim, "TrPaint")
					local q0, q1 = face + dir * 0.3, face + dir * 0.45
					local pn = if along == "x" then blk("Scenery", name .. "Panel", m - hw, m + hw, p0, p1, q0, q1, W.panelSoft, { ghost = true, mat = NEON })
						else blk("Scenery", name .. "Panel", q0, q1, p0, p1, m - hw, m + hw, W.panelSoft, { ghost = true, mat = NEON })
					local lp = if along == "x" then V3(m, (p0 + p1) / 2, face + dir * 4) else V3(face + dir * 4, (p0 + p1) / 2, m)
					B.lamp(lp.X, lp.Y, lp.Z, "point", 22, 0.45, W.warmLamp)
				end
			end
		end
	end
	-- a lamp in a chunky housing in each bay between two piers (the kit's tr_lamp, half as big again), warm light
	if o.lamps then
		for i = 1, #placed - 1 do
			local m = (placed[i] + placed[i + 1]) / 2
			local ly = y0 + (o.lampY or 9)
			if clear(m - 3, m + 3, ly - 1, ly + 7) then
				local at = if along == "x" then V3(m, ly, face) else V3(face, ly, m)
				local look = if along == "x" then V3(m, ly, face + dir * 10) else V3(face + dir * 10, ly, m)
				local cf = CFrame.lookAt(at, look)
				B.put("tr_lamp", cf * CFrame.Angles(0, math.pi, 0), { name = name .. "Lamp", scale = 1.5 })
				local lp = cf * CF(0, 3.2, -2.6)
				B.lamp(lp.X, lp.Y, lp.Z, "point", 18, 0.45, W.warmLamp)
			end
		end
	end
end
-- a square lit panel set up into a chunky housing under a ceiling at height cy (judge round 1: no flush strips)
local function ceilPanel(cx, cy, cz, sz, hex)
	local h = sz / 2
	blk("Shell", "PanelFrame", cx - h - 1, cx + h + 1, cy - 0.9, cy, cz - h - 1, cz - h, W.trim, { tex = "TrPaint" })
	blk("Shell", "PanelFrame", cx - h - 1, cx + h + 1, cy - 0.9, cy, cz + h, cz + h + 1, W.trim, { tex = "TrPaint" })
	blk("Shell", "PanelFrame", cx - h - 1, cx - h, cy - 0.9, cy, cz - h, cz + h, W.trim, { tex = "TrPaint" })
	blk("Shell", "PanelFrame", cx + h, cx + h + 1, cy - 0.9, cy, cz - h, cz + h, W.trim, { tex = "TrPaint" })
	blk("Scenery", "Panel", cx - h, cx + h, cy - 0.14, cy - 0.04, cz - h, cz + h, hex or W.panel, { ghost = true, mat = NEON })
end
-- a gallery on piers along a wall (the course's north side, over the sprint lane): its deck, front beam, nose and
-- parapet (open at 'gap'), lit panels under it. zw = the wall's face, zf = the deck's front edge (the court toward -z)
local function gallery(name, x0, x1, zw, zf, top, bay, gap)
	blk("Shell", name .. "Deck", x0, x1, top - 2, top, zw, zf, W.floor, { tex = "TrConcrete" })
	blk("Shell", name .. "Beam", x0, x1, top - 4.2, top - 2, zf + 2.2, zf, W.pier2, { tex = "TrPaint" })
	nose(name .. "Nose", x0, x1, top - 4.2, zf + 0.2, "x", 0.9)
	for _, s in { { x0, gap[1] }, { gap[2], x1 } } do
		blk("Shell", name .. "Parapet", s[1], s[2], top, top + 3.2, zf + 2.4, zf, W.wall2, { tex = "TrPlaster" })
		blk("Shell", name .. "ParapetCap", s[1], s[2], top + 3.2, top + 3.9, zf + 2.7, zf - 0.3, W.trim, { tex = "TrPaint" })
	end
	local n = math.max(1, math.floor((x1 - x0) / bay))
	local sp = (x1 - x0 - 4) / n
	for k = 0, n do
		local px = x0 + 2 + k * sp
		blk("Shell", name .. "Pier", px - 1.8, px + 1.8, Y0, top - 4.2, zf + 3.6, zf, W.pier, { tex = "TrPaint" })
		blk("Shell", name .. "PierBase", px - 2.2, px + 2.2, Y0, Y0 + 1.6, zf + 4, zf - 0.4, W.plinth, { tex = "TrSlate" })
		if k < n then
			ceilPanel(px + sp / 2, top - 2, (zw + zf) / 2 + 1, 4)
		end
	end
end
-- a covered walk along the field's east wall (z0 > z1): its roof on square columns, a deep front beam, a nose, a cap, lit
-- panels in its soffit
local function colonnade(z0, z1)
	local xw, xf, top = F.x1, F.x1 - 10, 258
	blk("Shell", "ColonnadeRoof", xf, xw, top - 2, top, z1, z0, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "ColonnadeBeam", xf, xf + 2.2, top - 4.2, top - 2, z1, z0, W.pier2, { tex = "TrPaint" })
	nose("ColonnadeNose", z1, z0, top - 4.2, xf + 0.2, "z", 0.9)
	blk("Shell", "ColonnadeCap", xf - 0.3, xw, top, top + 0.8, z1 - 0.3, z0 + 0.3, W.trim, { tex = "TrPaint" })
	local n = math.max(1, math.floor((z0 - z1) / 18))
	local sp = (z0 - z1 - 4) / n
	for k = 0, n do
		local cz = z1 + 2 + k * sp
		if math.abs(cz - F.gz) < 7 then continue end -- (the gantry's tower stands there)
		blk("Shell", "Column", xf, xf + 3.4, Y0, top - 4.2, cz - 1.7, cz + 1.7, W.pier, { tex = "TrPaint" })
		blk("Shell", "ColumnBase", xf - 0.4, xf + 3.8, Y0, Y0 + 1.6, cz - 2.1, cz + 2.1, W.plinth, { tex = "TrSlate" })
		if k < n then
			ceilPanel((xf + xw) / 2 + 1, top - 2, cz + sp / 2, 4)
		end
	end
end
-- a console (hold E): its button in folder f with a Prompt (the practice lane's two)
local function console(f, name, wordTxt, cx, cy, cz, hex, action, objectText)
	local ch = cy + 2.55
	blk("Shell", "ConsoleBase", cx - 1.6, cx + 1.6, cy, ch - 0.55, cz - 1.2, cz + 1.2, W.plinth, { tex = "TrSlate" })
	B.part("Shell", "PracticeTop", CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0), V3(3.6, 0.8, 2.9), W.pier2)
	local btn = B.part("Scenery", name, CF(cx, ch, cz) * CFrame.Angles(math.rad(28), 0, 0) * CF(0, 0.45, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.5, 1.7, 1.7), hex, { cyl = true, ghost = true })
	btn.Parent = f
	local pp = Instance.new("ProximityPrompt")
	pp.Name = "Prompt"; pp.ActionText = action; pp.ObjectText = objectText; pp.HoldDuration = 0.3
	pp.MaxActivationDistance = 8; pp.RequiresLineOfSight = false; pp.KeyboardKeyCode = Enum.KeyCode.E
	pp.Parent = btn
	B.text("ConsoleWord", { { wordTxt, W.pale, "B", 1 } }, 2.9, 0.55, CF(cx, cy + 1.15, cz + 1.24) * CFrame.Angles(0, math.pi, 0), { plate = W.slate, thick = 0.05 })
	return btn
end
-- a dummy's track across a floor (judge round 2: the old stops read as stray cubes): a dark bed, rounded low bumpers
-- across its ends
local function railBed(x, y, z, span)
	local half = span + 1.4
	blk("Scenery", "RailBed", x - half, x + half, y + 0.005, y + 0.03, z - 1.3, z + 1.3, W.deep, { ghost = true })
	for _, sd in { -1, 1 } do nose("RailStop", z - 1.5, z + 1.5, y + 0.3, x + sd * (half + 0.5), "z", 1.0, W.pier2) end
end
-- a bench from blocks (the family's: a slate base, a cream seat with a rounded front), along "x" or "z"
local function bench(x, z, along)
	local L, D = 5.6, 2.4
	if along == "z" then
		blk("Shell", "BenchBase", x - D / 2 + 0.3, x + D / 2 - 0.3, GY, GY + 1.6, z - L / 2 + 0.5, z + L / 2 - 0.5, W.plinth, { tex = "TrSlate" })
		blk("Shell", "BenchSeat", x - D / 2, x + D / 2, GY + 1.6, GY + 2.2, z - L / 2, z + L / 2, W.pier2, { tex = "TrPaint" })
	else
		blk("Shell", "BenchBase", x - L / 2 + 0.5, x + L / 2 - 0.5, GY, GY + 1.6, z - D / 2 + 0.3, z + D / 2 - 0.3, W.plinth, { tex = "TrSlate" })
		blk("Shell", "BenchSeat", x - L / 2, x + L / 2, GY + 1.6, GY + 2.2, z - D / 2, z + D / 2, W.pier2, { tex = "TrPaint" })
	end
end
-- the arrival hall's map table: a slate plinth, a cream top with a rounded edge, and on it the compound in blocks at 1:32
-- (the gatehouse marked by a warm light), seen from the spawns
local function mapTable(cx, cz)
	local hw, hd = 7.2, 5.5
	B.drum("Shell", "MapDaisLip", cx, cz, GY, GY + 0.5, 23.4, W.plinth)
	B.drum("Shell", "MapDais", cx, cz, GY, GY + 1, 22, W.pier2)
	blk("Shell", "MapPlinth", cx - hw + 0.6, cx + hw - 0.6, GY, GY + 3, cz - hd + 0.6, cz + hd - 0.6, W.slate, { tex = "TrSlate" })
	for _, c in { { -1, -1 }, { -1, 1 }, { 1, -1 }, { 1, 1 } } do
		B.part("Shell", "MapPlinthCorner", CF(cx + c[1] * (hw - 0.6), GY + 1.5, cz + c[2] * (hd - 0.6)) * CFrame.Angles(0, 0, math.pi / 2), V3(3, 1.4, 1.4), W.slate, { cyl = true })
	end
	blk("Shell", "MapTop", cx - hw, cx + hw, GY + 3, GY + 3.5, cz - hd, cz + hd, W.pier2, { tex = "TrPaint" })
	nose("MapTopLip", cx - hw, cx + hw, GY + 3.25, cz - hd, "x", 0.7)
	nose("MapTopLip", cx - hw, cx + hw, GY + 3.25, cz + hd, "x", 0.7)
	nose("MapTopLip", cz - hd, cz + hd, GY + 3.25, cx - hw, "z", 0.7)
	nose("MapTopLip", cz - hd, cz + hd, GY + 3.25, cx + hw, "z", 0.7)
	local sc, MX, MZ, base = 1 / 32, -126, -8150, GY + 3.5
	local function piece(name, x0, x1, z0, z1, top, hex, o)
		local h = math.max(0.3, (top - 236) * sc)
		local a0, a1 = cx + (x0 - MX) * sc, cx + (x1 - MX) * sc
		local b0, b1 = cz + (z0 - MZ) * sc, cz + (z1 - MZ) * sc
		if math.abs(a1 - a0) < 0.34 then local m = (a0 + a1) / 2; a0, a1 = m - 0.17, m + 0.17 end
		if math.abs(b1 - b0) < 0.34 then local m = (b0 + b1) / 2; b0, b1 = m - 0.17, m + 0.17 end
		return blk("Shell", name, a0, a1, base, base + h, b0, b1, hex, o or { nc = true })
	end
	piece("MapGround", -334, 82, -7996, -8304, 236, W.floor2) -- (the base: 0.3)
	piece("MapField", -100, 20, -8150, -8258, 245, W.floor)
	piece("MapCourse", -330, -104, -8140, -8254, 245, W.floor)
	piece("MapGatehouse", -76, -4, -8060, -8136, 274, W.pier)
	piece("MapHall", -268, -88, -8006, -8120, 278, W.pier2)
	piece("MapRange", 26, 82, -8098, -8304, 252, W.slate)
	piece("MapTop", -330, -268, -8226, -8254, 270, W.slate)
	B.drum("Shell", "MapTower", cx + (-196 - MX) * sc, cz + (-8196 - MZ) * sc, base, base + (272 - 236) * sc, 22 * sc + 0.2, W.wall, { nc = true })
	-- you are here
	B.drum("Scenery", "MapHere", cx + (-40 - MX) * sc, cz + (-8098 - MZ) * sc, base + (274 - 236) * sc, base + (274 - 236) * sc + 0.12, 1.2, W.teal, { ghost = true, mat = NEON })
	B.lamp(cx, GY + 9, cz, "point", 14, 0.5, W.warmLamp)
end
local gunList = nil
local NICHE_GUNS = { "w_ar", "w_shotgun", "w_sniper", "w_smg", "w_dmr", "w_burst", "w_lmg", "w_redline", "w_autoshot", "w_lever" }
local function gunOn(k, cf)
	if not gunList then
		gunList = {}
		local lib = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireWeapons")
		for _, n in NICHE_GUNS do
			local c = lib and lib:FindFirstChild(n)
			if c and c:IsA("Model") then table.insert(gunList, c) end
		end
		if #gunList == 0 then
			for _, c in (if lib then lib:GetChildren() else {}) do
				if c:IsA("Model") and string.sub(c.Name, 1, 2) == "w_" then table.insert(gunList, c) end
			end
			table.sort(gunList, function(a, b) return a.Name < b.Name end)
		end
	end
	if #gunList == 0 then return end
	local m = gunList[(k - 1) % #gunList + 1]:Clone()
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
		elseif d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Sound") then d:Destroy() end
	end
	m.Parent = workspace
	m:PivotTo(CFrame.new(m:GetPivot().Position))
	local function ext()
		local lo, hi = V3(math.huge, math.huge, math.huge), V3(-math.huge, -math.huge, -math.huge)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") and d.Transparency < 0.95 then
				local h = d.Size / 2
				for _, c in { V3(1, 1, 1), V3(1, 1, -1), V3(1, -1, 1), V3(1, -1, -1), V3(-1, 1, 1), V3(-1, 1, -1), V3(-1, -1, 1), V3(-1, -1, -1) } do
					local q = d.CFrame:PointToWorldSpace(h * c)
					lo = lo:Min(q); hi = hi:Max(q)
				end
			end
		end
		return hi - lo, (hi + lo) / 2
	end
	local e0 = ext()
	local long = math.max(e0.X, e0.Y, e0.Z)
	if long > 0.1 and long < 1e6 then m:ScaleTo(m:GetScale() * math.clamp(7.4 / long, 0.5, 40)) end
	local e, mid = ext()
	local rot = CFrame.identity
	if e.Z > e.X and e.Z >= e.Y then rot = CFrame.Angles(0, math.pi / 2, 0) elseif e.Y > e.X and e.Y > e.Z then rot = CFrame.Angles(0, 0, math.pi / 2) end
	m:PivotTo(B.at(cf) * rot * CFrame.new(m:GetPivot().Position - mid))
	m.Name = "NicheGun"
	m.Parent = B.root.Scenery
end
local nicheN = 0
-- a gun niche on a wall: wx = the wall's face, dir = the way into the room, along z; its middle at height y
local function niche(wx, dir, z, y, full)
	local hw, hh, dp = 4.6, 3.0, 1.5
	nicheN += 1
	blk("Shell", "NicheBack", wx, wx + dir * 0.3, y - hh, y + hh, z - hw, z + hw, W.deep, { tex = "TrSlate" })
	blk("Shell", "NicheFrame", wx, wx + dir * dp, y + hh, y + hh + 1.2, z - hw - 1.2, z + hw + 1.2, W.pier2, { tex = "TrPaint" })
	blk("Shell", "NicheFrame", wx, wx + dir * dp, y - hh - 1.2, y - hh, z - hw - 1.2, z + hw + 1.2, W.pier2, { tex = "TrPaint", nc = true })
	local sb = if full then GY else y - hh -- (full: the side bars down to the floor, so nothing stands out at head height)
	blk("Shell", "NicheFrame", wx, wx + dir * dp, sb, y + hh, z - hw - 1.2, z - hw, W.pier2, { tex = "TrPaint" })
	blk("Shell", "NicheFrame", wx, wx + dir * dp, sb, y + hh, z + hw, z + hw + 1.2, W.pier2, { tex = "TrPaint" })
	blk("Scenery", "NicheLight", wx + dir * 0.4, wx + dir * 1.3, y + hh - 0.25, y + hh - 0.05, z - hw + 0.4, z + hw - 0.4, W.panel, { ghost = true, mat = NEON })
	blk("Shell", "NicheCradle", wx + dir * 0.3, wx + dir * 1.4, y - hh, y - hh + 1.6, z - 2.6, z + 2.6, W.pier2, { tex = "TrPaint", nc = true })
	local at = V3(wx + dir * 0.9, y + 0.2, z)
	gunOn(nicheN, CFrame.lookAt(at, at + V3(dir, 0, 0)))
	B.lamp(wx + dir * 2.5, y + 1, z, "point", 10, 0.35, W.warmLamp)
end
-- a lit display on an aisle's outer wall (judge round 2: the bays held nothing): a cream frame, a soft-lit panel, over
-- head height; wx = the wall's face, dir = the way into the room
local function display(wx, dir, z)
	local y0, y1, h = GY + 8, GY + 13, 4
	blk("Shell", "DisplayFrame", wx, wx + dir * 0.9, y0 - 1, y1 + 1, z - h - 1, z + h + 1, W.pier2, { tex = "TrPaint" })
	blk("Scenery", "DisplayPanel", wx + dir * 0.9, wx + dir * 1.0, y0, y1, z - h, z + h, W.panelSoft, { ghost = true, mat = NEON })
	B.lamp(wx + dir * 3, (y0 + y1) / 2, z, "point", 16, 0.4, W.warmLamp)
end
local function lampWall(x, y, z, look, range, bright)
	-- the kit's wall light (a white panel in a chunky housing), turned to face 'look', and a real light in front of it
	local cf = CFrame.lookAt(V3(x, y, z), V3(look.X, y, look.Z))
	B.put("tr_lamp", cf * CFrame.Angles(0, math.pi, 0), { name = "WallLamp" })
	local lp = cf * CF(0, 2.1, -1.6)
	B.lamp(lp.X, lp.Y, lp.Z, "point", range or 18, bright or 0.6, W.lamp)
end

-- a part with round holes cut out of it (GeometryService), in its place under the same name; nil if the cut fails
local function cut(p, holes)
	local ok, res = pcall(function()
		return game:GetService("GeometryService"):SubtractAsync(p, holes, { CollisionFidelity = Enum.CollisionFidelity.Box, RenderFidelity = Enum.RenderFidelity.Precise, SplitApart = false })
	end)
	for _, h in holes do h:Destroy() end
	if not ok or type(res) ~= "table" or not res[1] then p:Destroy(); return nil end
	local u = res[1]
	u.Name = p.Name; u.Anchored = true; u.UsePartColor = true; u.Color = p.Color; u.Material = p.Material
	u.CanCollide = false; u.CanQuery = false; u.CanTouch = false; u.CastShadow = p.CastShadow
	for k, v in p:GetAttributes() do u:SetAttribute(k, v) end
	for _, t in p:GetTags() do u:AddTag(t) end
	roles[p] = nil -- (no picture on a cut part: its triangles show as seams)
	u.Parent = p.Parent
	p:Destroy()
	return u
end
local function cylAt(folder, name, x, z, y0, y1, dia, hex)
	return B.drum(folder, name, x, z, y0, y1, dia, hex)
end

-- the hall's centre on its dais at (cx, cz)
local function hallCentre(cx, cz)
	B.drum("Shell", "MapDaisLip", cx, cz, GY, GY + 0.5, 23.4, W.plinth)
	B.drum("Shell", "MapDais", cx, cz, GY, GY + 1, 22, W.pier2)
	local d0 = GY + 1
	B.drum("Shell", "HallDrumBase", cx, cz, d0, d0 + 1.2, 11.4, W.trim)
	B.drum("Shell", "HallDrum", cx, cz, d0 + 1.2, GY + 6, 10, W.pier2)
	B.drum("Shell", "HallDrumBand", cx, cz, GY + 6, GY + 7.6, 10, W.slate)
	B.drum("Shell", "HallDrum", cx, cz, GY + 7.6, GY + 15.4, 10, W.pier2)
	B.drum("Scenery", "HallDrumGlow", cx, cz, GY + 15.2, GY + 15.4, 12.6, "c9bfae", { ghost = true, mat = NEON })
	local h, s0, s1 = 7, GY + 15.4, GY + 19.4
	blk("Shell", "SignBox", cx - h, cx + h, s0, s1, cz - h, cz + h, W.pier2, { tex = "TrPaint" })
	blk("Shell", "SignBoxCap", cx - h - 0.5, cx + h + 0.5, s1, s1 + 0.8, cz - h - 0.5, cz + h + 0.5, W.trim, { tex = "TrPaint" })
	for _, f in { { 0, 1, "FIELD" }, { 0, -1, "HUB" }, { -1, 0, "RANGE" }, { 1, 0, "TUTORIAL" } } do
		local fx, fz = cx + f[1] * (h + 0.16), cz + f[2] * (h + 0.16)
		word("SignBox" .. f[3], f[3], 11, 2.6, facing(fx, (s0 + s1) / 2, fz, fx + f[1] * 20, fz + f[2] * 20), W.board)
	end
	-- (the column on up into the skylight, to its lit panel)
	B.drum("Shell", "SignColumn", cx, cz, s1 + 0.8, GH.top + 3.8, 7, W.pier2)
	B.drum("Shell", "SignColumnCollar", cx, cz, s1 + 0.8, s1 + 2, 8.4, W.trim)
	for _, dz in { -9, 9 } do B.lamp(cx, GY + 13, cz + dz, "point", 18, 0.45, W.warmLamp) end
end

-- ---------------------------------------------------------------- the gatehouse (arrival)
local function gatehouse()
	local x0, x1, z0, z1 = GH.x0, GH.x1, GH.z0, GH.z1
	local top = GH.top
	local n0, n1 = GH.nave[1], GH.nave[2]
	-- (21 Nov 2026, the owner: gaps by the mirror, to the tutorial rooms and to the range: each wing's floor stopped at
	-- this hall's wall line and the hall's floor at its inner face, so every doorway through the 4-stud walls had none)
	-- the hall's floor runs out under its west, east and north walls; the balcony's floor runs in under the south one
	blk("Shell", "GateFloor", x0 - 4, x1 + 4, 236, GY, z0 + 4, z1, W.floor, { tex = "TrConcrete" })
	-- walls: north (the hub gate on the axis), west (the mirror bay, the tutorial door), east (the range door), south
	-- (the big portal onto the balcony)
	local gx0, gx1 = GH.xm - 6.6, GH.xm + 6.6
	blk("Shell", "GateWallN", x0 - 4, gx0, 236, top, z0 + 4, z0, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallN", gx1, x1 + 4, 236, top, z0 + 4, z0, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallN", gx0, gx1, GY + 13, top, z0 + 4, z0, W.wall, { tex = "TrPlaster" })
	local md = { z0 = -8092, z1 = -8104 } -- the mirror bay's mouth
	local td = GH.DOORS.tut
	for _, s in { { z0 + 4, md.z0 }, { md.z1, td.z0 }, { td.z1, z1 - 4 } } do
		blk("Shell", "GateWallW", x0 - 4, x0, 236, top, s[1], s[2], W.wall, { tex = "TrPlaster" })
	end
	blk("Shell", "GateWallW", x0 - 4, x0, GY + 14, top, md.z0, md.z1, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallW", x0 - 4, x0, GY + 12, top, td.z0, td.z1, W.wall, { tex = "TrPlaster" })
	local rd = GH.DOORS.range
	blk("Shell", "GateWallE", x1, x1 + 4, 236, top, z0 + 4, rd.z0, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallE", x1, x1 + 4, 236, top, rd.z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallE", x1, x1 + 4, GY + 12, top, rd.z0, rd.z1, W.wall, { tex = "TrPlaster" })
	local px0, px1 = GH.xm - 12, GH.xm + 12
	blk("Shell", "GateWallS", x0 - 4, px0 - 3.6, 236, top, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallS", px1 + 3.6, x1 + 4, 236, top, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "GateWallS", px0 - 3.6, px1 + 3.6, GY + 19.4, top, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	B.put("tr_portalBig", CF(GH.xm, GY, z1 - 2), { name = "GatePortal" })
	jambs("PortalJamb", GH.xm, z1 - 2, "x", 24, 31.2, 19.4, 6)
	-- the doors' frames (the kit's), each with its word on the head
	B.put("tr_portal", CF(x1 + 2, GY, (rd.z0 + rd.z1) / 2) * CFrame.Angles(0, math.pi / 2, 0), { name = "RangeFrame", scale = 0.85 })
	B.put("tr_portal", CF(x0 - 2, GY, (td.z0 + td.z1) / 2) * CFrame.Angles(0, -math.pi / 2, 0), { name = "TutorialFrame", scale = 0.72 })
	jambs("RangeJamb", x1 + 2, (rd.z0 + rd.z1) / 2, "z", 16 * 0.85, rd.z0 - rd.z1, 12, 4)
	jambs("TutorialJamb", x0 - 2, (td.z0 + td.z1) / 2, "z", 16 * 0.72, td.z0 - td.z1, 12, 4)
	-- (the words on the frames' heads, under their trim bars: the frame's face is half its depth in from the wall's middle)
	for _, d in { { x1 + 2 - 3 * 0.85, -1, (rd.z0 + rd.z1) / 2, "RANGE" }, { x0 - 2 + 3 * 0.72, 1, (td.z0 + td.z1) / 2, "TUTORIAL" } } do
		local fx, dir, zc = d[1], d[2], d[3]
		blk("Shell", "DoorHeader", fx, fx + dir * 0.9, GY + 12.1, GY + 14.3, zc - 6.5, zc + 6.5, W.pier2, { tex = "TrPaint" })
		word("Word" .. d[4], d[4], 10.5, 1.8, facing(fx + dir * 1.05, GY + 13.2, zc, fx + dir * 20, zc), W.board)
	end
	-- the nave and the aisles: square piers on bases, beams across the aisles at each pier, an arcade beam along the
	-- nave, the aisles' low ceilings, the clerestory over the arcade, the nave's stepped coffers and the lantern
	for _, nx in { n0, n1 } do
		for _, z in GH.piers do
			blk("Shell", "Pier", nx - 1.8, nx + 1.8, GY, GH.aisle, z - 1.8, z + 1.8, W.pier, { tex = "TrPaint" })
			blk("Shell", "PierBase", nx - 2.2, nx + 2.2, GY, GY + 1.4, z - 2.2, z + 2.2, W.plinth, { tex = "TrSlate" })
			blk("Shell", "PierCap", nx - 2.3, nx + 2.3, GH.aisle - 1.2, GH.aisle, z - 2.3, z + 2.3, W.trim, { tex = "TrPaint" })
			local ox = if nx == n0 then x0 else x1
			blk("Shell", "AisleBeam", math.min(nx, ox), math.max(nx, ox), GH.aisle - 2, GH.aisle, z - 1.4, z + 1.4, W.pier2, { tex = "TrPaint" })
		end
		blk("Shell", "Arcade", nx - 1.8, nx + 1.8, GH.aisle, GH.aisle + 2.4, z0, z1, W.pier2, { tex = "TrPaint" })
		nose("ArcadeNose", z0, z1, GH.aisle + 2.4, nx, "z", 1.0)
		-- the clerestory wall over the arcade: pale, with a lit band
		blk("Shell", "Clerestory", nx - 1.2, nx + 1.2, GH.aisle + 2.4, GH.naveTop, z0, z1, W.wall2, { tex = "TrPlaster" })
	end
	for _, a in { { x0, n0 }, { n1, x1 } } do
		blk("Shell", "AisleCeiling", a[1], a[2], GH.aisle, GH.aisle + 1, z0, z1, W.ceil, { tex = "TrPlaster" })
		for _, z in { -8088, -8104, -8120 } do
			local cx = (a[1] + a[2]) / 2
			ceilPanel(cx, GH.aisle, z, 7)
			for _, q in { { -6.6, 6.6, -6.6, -5.4 }, { -6.6, 6.6, 5.4, 6.6 }, { -6.6, -5.4, -5.4, 5.4 }, { 5.4, 6.6, -5.4, 5.4 } } do
				blk("Shell", "CofferRing", cx + q[1], cx + q[2], GH.aisle - 1.6, GH.aisle, z + q[3], z + q[4], W.pier2, { tex = "TrPaint" })
			end
		end
	end
	-- the nave's ceiling: a deep frame round a stepped coffer, the lantern in the middle up to the roof
	local lz0, lz1 = -8088, -8108
	blk("Shell", "NaveCeiling", n0, n1, GH.naveTop, GH.naveTop + 1.2, z0, lz0, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "NaveCeiling", n0, n1, GH.naveTop, GH.naveTop + 1.2, lz1, z1, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "NaveCeiling", n0, GH.xm - 9, GH.naveTop, GH.naveTop + 1.2, lz0, lz1, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "NaveCeiling", GH.xm + 9, n1, GH.naveTop, GH.naveTop + 1.2, lz0, lz1, W.ceil, { tex = "TrPlaster" })
	for _, z in { z0 - 8, -8122 } do blk("Shell", "NaveBeam", n0, n1, GH.naveTop - 2.2, GH.naveTop, z - 1.2, z + 1.2, W.pier2, { tex = "TrPaint" }) end
	-- the lantern: a drum of thick posts with lit panels between, up to the roof, a white light at its top
	for _, sx in { -1, 1 } do
		blk("Shell", "LanternWall", GH.xm + sx * 9, GH.xm + sx * 10.4, GH.naveTop, top + 4, lz0, lz1, W.wall2, { tex = "TrPlaster" })
	end
	for _, z in { lz0, lz1 } do blk("Shell", "LanternWall", GH.xm - 10.4, GH.xm + 10.4, GH.naveTop, top + 4, z - (if z == lz0 then 0 else 1.4), z + (if z == lz0 then 1.4 else 0), W.wall2, { tex = "TrPlaster" }) end
	blk("Shell", "Roof", x0 - 4, x1 + 4, top, top + 2, z0 + 4, lz0 + 1.4, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "Roof", x0 - 4, x1 + 4, top, top + 2, lz1 - 1.4, z1 - 4, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "Roof", x0 - 4, GH.xm - 10.4, top, top + 2, lz0 + 1.4, lz1 - 1.4, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "Roof", GH.xm + 10.4, x1 + 4, top, top + 2, lz0 + 1.4, lz1 - 1.4, W.ceil, { tex = "TrPlaster" })
	blk("Shell", "LanternRoof", GH.xm - 10.4, GH.xm + 10.4, top + 4, top + 6, lz0 + 1.4, lz1 - 1.4, W.ceil, { tex = "TrPlaster" })
	ceilPanel(GH.xm, top + 4, (lz0 + lz1) / 2, 14)
	-- the round skylight in the lantern: the opening filled but for a round hole, a cream drum up to the lit panel, a
	-- cream ring housing under its rim
	local lc = (lz0 + lz1) / 2
	local plate = blk("Shell", "SkylightCeiling", GH.xm - 9, GH.xm + 9, GH.naveTop, GH.naveTop + 1.2, lz0 + 1.4, lz1 - 1.4, W.ceil, { tex = "TrPlaster" })
	cut(plate, { cylAt("Shell", "Hole", GH.xm, lc, GH.naveTop - 1, GH.naveTop + 2, 14.6, W.ceil) })
	local drum = cylAt("Shell", "SkylightDrum", GH.xm, lc, GH.naveTop + 0.2, top + 4, 17, W.pier2)
	cut(drum, { cylAt("Shell", "Hole", GH.xm, lc, GH.naveTop - 1, top + 6, 14, W.pier2) })
	local ring = cylAt("Shell", "SkylightRing", GH.xm, lc, GH.naveTop - 1.6, GH.naveTop + 0.2, 17.8, W.trim)
	cut(ring, { cylAt("Shell", "Hole", GH.xm, lc, GH.naveTop - 3, GH.naveTop + 2, 14, W.trim) })
	for _, sx in { -1, 1 } do B.lamp(GH.xm + sx * 5.2, GH.naveTop - 1, lc, "point", 34, 0.4, W.lamp) end
	-- the floor: a darker band round the nave, a pale line from the gate to the portal
	blk("Shell", "NaveBand", n0 + 2, n1 - 2, GY, GY + 0.04, z0 + 2, z1 - 2, W.floor2, { ghost = true, tex = "TrConcrete" })
	-- the floor lines (over the nave's band): from the gate to the dais and on to the portal, a ring round the dais
	-- (open where the axis crosses it), from it to the range door and the tutorial door
	local LY = GY + 0.01
	B.line(GH.xm, z0 + 6, GH.xm, -8086.5, LY, 1.0, W.line, "AxisLine")
	B.line(GH.xm, -8109.5, GH.xm, z1 - 1, LY, 1.0, W.line, "AxisLine")
	B.drum("Shell", "DaisStep", GH.xm, -8098, GY, GY + 0.25, 28, "a4a6ab")
	for _, b in { { 8, x1 - 1, rd.z0 + (rd.z1 - rd.z0) / 2 }, { -8, x0 + 1, td.z0 + (td.z1 - td.z0) / 2 } } do
		local bx = GH.xm + b[1]
		local zs = -8098 - math.sqrt(13.6 ^ 2 - b[1] ^ 2)
		B.line(bx, zs, bx, b[3] - 0.5, LY, 1.0, W.line, "DoorLine")
		local sd = if b[1] > 0 then 1 else -1
		B.line(bx + sd * 0.5, b[3], b[2], b[3], LY, 1.0, W.line, "DoorLine")
	end
	hallCentre(GH.xm, -8098)
	-- the nave's piers with rounded corners
	for _, nx in { GH.nave[1], GH.nave[2] } do
		for _, pz in GH.piers do
			for _, c in { { -1, -1 }, { -1, 1 }, { 1, -1 }, { 1, 1 } } do
				B.part("Shell", "PierCorner", CF(nx + c[1] * 1.8, (GY + GH.aisle - 1.2) / 2, pz + c[2] * 1.8) * CFrame.Angles(0, 0, math.pi / 2), V3(GH.aisle - 1.2 - GY, 1.3, 1.3), W.pier, { cyl = true })
			end
		end
	end
	-- the hub's gate on the axis (GateKit, the hub session's: the same door both sides)
	local G = CF(GH.xm, 0, z0) * CFrame.Angles(0, -math.pi, 0) -- (-Z of this frame points out through the north wall)
	local GK = require(game.ServerStorage.PolishBackup.GateKit:Clone())
	B.put("hb_portal", G * CF(0, GY, -1.2), { name = "HubGate", scale = GK.FRAME.scale, color = GK.FRAME.color })
	B.fbox(G, "Shell", "GateVoid", -6.6, 6.6, GY, GY + 13, 3.4, 4.2, "33363d")
	GK.build(B.at(G * CF(0, GY, -1.5)), B.root.Scenery, { door = "HubShutter", lasers = "HubLaserGate" })
	local gl = G * CF(0, GY + GK.LAMP.up, -(1.5 - GK.LAMP.out))
	B.lamp(gl.X, gl.Y, gl.Z, "point", GK.LAMP.range, GK.LAMP.bright, GK.LAMP.hex)
	B.put("tr_portalBig", CF(GH.xm, GY, z0 - 3) * CFrame.Angles(0, math.pi, 0), { name = "HubPortal" })
	jambs("HubPortalJamb", GH.xm, z0 - 3, "x", 24, 31.2, 19.4, 6)
	blk("Scenery", "HubPortalSoffit", GH.xm - 9, GH.xm + 9, GY + 15.86, GY + 16, z0 - 1, z0 - 5, W.panel, { ghost = true, mat = NEON }) -- (the gate in a lit frame)
	word("WordHUB", "HUB", 16, 2.2, facing(GH.xm, GY + 17.4, z0 - 6.15, GH.xm, z0 - 30), W.board)
	blk("Shell", "SignHousing", GH.xm - 8, GH.xm + 8, 264.2, 267.6, z1 + 0.9, z1, W.pier2, { tex = "TrPaint" })
	word("SignFIELD", "FIELD", 13, 2.4, facing(GH.xm, 265.9, z1 + 1.05, GH.xm, z1 + 20), W.board)
	B.trigger("ToHub", GH.xm - 4.2, GH.xm + 4.2, GY, GY + 10, z0 + 0.6, z0 + 3.6)
	-- spawns: two arcs either side of the axis in the nave, looking at the portal (and the field beyond it)
	local sp = K.folderIn(B.mk, "TrainSpawns")
	for _, s in { { -50, -8086 }, { -52, -8096 }, { -50, -8106 }, { -30, -8086 }, { -28, -8096 }, { -30, -8106 }, { -46, -8116 }, { -34, -8116 } } do
		B.marker(sp, "TrainSpawn", s[1], GY + 0.7, s[2], V3(GH.xm, GY, -8160))
	end
	-- the mirror bay (west aisle): a deep bay off the west wall, a step down, a low curved ceiling, the projector and the
	-- MirrorSpot (TrainingDoors.client stands your hologram on it), warm lamps
	local bx0, bx1 = x0 - 14, x0 - 4
	local BAY_TOP = GY + 15
	blk("Shell", "BayFloor", bx0, bx1, 236, GY, md.z0, md.z1, W.floor2, { tex = "TrConcrete" }) -- (to the wall's back face: the hall's floor runs out under the wall)
	blk("Shell", "BayWall", bx0 - 4, bx1, 236, BAY_TOP + 2, md.z0 + 4, md.z0, W.warm, { tex = "TrPlaster" })
	blk("Shell", "BayWall", bx0 - 4, bx1, 236, BAY_TOP + 2, md.z1, md.z1 - 4, W.warm, { tex = "TrPlaster" })
	blk("Shell", "BayBack", bx0 - 4, bx0, 236, BAY_TOP + 2, md.z0, md.z1, W.warm, { tex = "TrPlaster" })
	blk("Shell", "BayCeiling", bx0 - 4, bx1, BAY_TOP, BAY_TOP + 2, md.z0 + 4, md.z1 - 4, W.ceil, { tex = "TrPlaster" })
	ceilPanel((bx0 + bx1) / 2, BAY_TOP, (md.z0 + md.z1) / 2, 5)
	-- the mouth's frame: cream reveals in the wall's thickness, a head under the aisle beam, a frame proud of the hall's
	-- face (the opening 9.6 wide, 12.6 tall)
	local mz = (md.z0 + md.z1) / 2
	for _, sd in { -1, 1 } do
		local e = if sd < 0 then md.z1 else md.z0
		blk("Shell", "MirrorReveal", x0 - 4, x0, GY, GY + 14, e, e - sd * 1.2, W.pier, { tex = "TrPaint" })
		blk("Shell", "MirrorFrame", x0, x0 + 1.2, GY, GY + 14, e + sd * 1.4, e - sd * 1.2, W.pier, { tex = "TrPaint" })
	end
	blk("Shell", "MirrorHead", x0 - 4, x0 + 1.2, GY + 12.6, GY + 14, md.z0 - 1.2, md.z1 + 1.2, W.pier2, { tex = "TrPaint" })
	local pc = V3((bx0 + bx1) / 2 - 1, GY, mz)
	B.drum("Shell", "MirrorBase", pc.X, pc.Z, GY, GY + 0.5, 5.8, W.pier2)
	B.drum("Shell", "MirrorDrum", pc.X, pc.Z, GY + 0.45, GY + 1.15, 4.8, W.slate)
	B.drum("Scenery", "MirrorGlowBand", pc.X, pc.Z, GY + 0.7, GY + 0.82, 4.86, "8fd8ff", { ghost = true, mat = NEON })
	B.drum("Shell", "MirrorTrim", pc.X, pc.Z, GY + 1.1, GY + 1.27, 5.0, W.trim)
	local lensAt = CF(pc.X, GY + 1.27, pc.Z)
	B.part("Scenery", "MirrorLens", lensAt * CFrame.Angles(0, 0, math.pi / 2), V3(0.12, 4.2, 4.2), W.deep, { cyl = true, ghost = true })
	B.part("Scenery", "MirrorLensGlow", lensAt * CF(0, 0.07, 0) * CFrame.Angles(0, 0, math.pi / 2), V3(0.05, 3.2, 3.2), "8fd8ff", { cyl = true, ghost = true, mat = NEON })
	local ms = B.marker(B.root.Scenery, "MirrorSpot", lensAt.X, lensAt.Y + 0.06, lensAt.Z, V3(GH.xm, GY, lensAt.Z))
	ms:SetAttribute("Near", 18)
	ms:SetAttribute("Clear", BAY_TOP - (lensAt.Y + 0.06)) -- (the room over the spot: TrainingDoors.client fits the statue under it)
	for _, dz in { -3.5, 3.5 } do B.lamp(bx0 + 2, GY + 10, pc.Z + dz, "point", 16, 0.8, W.warmLamp) end
	-- benches in the east aisle (a place to stop), lamps on the walls
	for _, d in { { x1, -1, -8072 }, { x1, -1, -8088 }, { x1, -1, -8104 }, { x0, 1, -8072 }, { x0, 1, -8112 } } do
		niche(d[1], d[2], d[3], GY + 9.6, true) -- (its frame clear of the aisle beams)
		bench(d[1] + d[2] * 3.8, d[3], "z") -- (out from the wall: a head on the bench stays clear of the niche)
	end
end

-- ---------------------------------------------------------------- the balcony and the range walk
local function balcony()
	local x0, x1, z0, z1 = BAL.x0, BAL.x1, BAL.z0, BAL.z1
	blk("Shell", "BalconyFloor", x0, x1, 236, GY, z0, z1, W.floor, { tex = "TrConcrete" })
	-- its face down to the field: a slate retaining wall with the white nose at the top
	blk("Shell", "BalconyFace", x0, x1, Y0 - 4, GY, z1, z1 - 0.6, W.slate, { tex = "TrSlate" })
	-- the parapet (the kit's, 8-long runs), open at the stairs: the middle (on the axis) and the practice lane's
	local gaps = { { GH.xm - 8, GH.xm + 8 }, { -96, -88 } }
	local x = x0 + 4
	while x + 4 <= x1 do
		local inGap = false
		for _, g in gaps do if x + 4 > g[1] and x - 4 < g[2] then inGap = true end end
		if not inGap then
			B.put("tr_parapet", CF(x, GY, z1 + 1.25), { name = "Parapet" })
			B.solid("ParapetSolid", CF(x, GY + 1.6, z1 + 1.25), V3(8, 3.2, 2.5)) -- (kit meshes stop nobody)
		end
		x += 8
	end
	blk("Shell", "ParapetEnd", x - 4, x1, GY, GY + 3.8, z1 + 2.7, z1, W.pier2, { tex = "TrPaint" })
	-- the stairs down: the axis's (wide), the practice lane's
	stair("BalconyStair", "z", z1, z1 - 10, GY, Y0, gaps[1][1], gaps[1][2], 5, W.ledge)
	stair("LaneStair", "z", z1, z1 - 8, GY, Y0, gaps[2][1], gaps[2][2], 5, W.ledge)
	-- (the stairs come down, not up: re-lay their tops as the right heights)
	-- the course's way down at the balcony's west end: steps down westward into the course's start
	stair("CourseStair", "x", x0, x0 - 8, GY, Y0, -8140, z1, 5, W.ledge)
	-- lamp posts on the parapet line at the stairs
	for _, lx in { GH.xm - 12, GH.xm + 12, -102 } do
		blk("Shell", "LampPost", lx - 0.8, lx + 0.8, GY, GY + 10, z1 + 0.5, z1 + 2.1, W.pier2, { tex = "TrPaint" })
		B.put("tr_lamp", CF(lx, GY + 10, z1 + 1.3) * CFrame.Angles(0, math.pi, 0), { name = "PostLamp", scale = 0.7 })
		B.lamp(lx, GY + 12, z1 - 1, "point", 22, 0.5, W.lamp)
	end
	word("WordCOURSE", "COURSE", 8, 1.5, facing(x0 + 6, GY + 8.5, -8136.15, x0 + 6, -8160), W.board) -- (on the corridor wall over the balcony's west end, facing south)
	dressWall("GateFront", "x", -8136, -1, -76, -4, GY, GH.top, { holes = { { -57, -23, 236, 264.5 } }, bay = 12, frames = true })
	blk("Shell", "SignHousing", GH.xm - 8, GH.xm + 8, 264.2, 267.6, -8136, -8136.9, W.pier2, { tex = "TrPaint" })
	word("SignHUB", "HUB", 13, 2.4, facing(GH.xm, 265.9, -8137.05, GH.xm, -8160), W.board)
	dressWall("CorridorFront", "x", -8136, -1, -104, -76, GY, TU.ceil + 2, { holes = { { -103, -93, 250, 254.5 } }, bay = 14 })
end

local function walk()
	local x0, x1, z0, z1 = WALK.x0, WALK.x1, WALK.z0, WALK.z1
	blk("Shell", "WalkFloor", x0, 14, 236, GY, z0, z1, W.floor, { tex = "TrConcrete" })
	B.ramp("Shell", "WalkRamp", "x", 14, GY, 22, 242, z0, z1, W.floor, { thick = 4 })
	blk("Shell", "WalkFloor", 22, x1 + 4, 236, 242, z0, z1, W.floor, { tex = "TrConcrete" }) -- (on under the range's wall to its deck: no gap in the door)
	blk("Shell", "WalkWall", x0, x1, 236, WALK.top + 2, z0 + 4, z0, W.wall, { tex = "TrPlaster" })
	blk("Shell", "WalkWall", x0, x1, 236, WALK.top + 2, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "WalkCeiling", x0, x1, WALK.top, WALK.top + 2, z0, z1, W.ceil, { tex = "TrPlaster" })
	for _, bx in { 2, 10 } do blk("Shell", "WalkBeam", bx - 1.2, bx + 1.2, WALK.top - 1.8, WALK.top, z0, z1, W.pier2, { tex = "TrPaint" }) end
	bench(6, z0 - 1.6, "x")
	lampWall(6, GY + 6, z1, V3(6, 0, z1 + 10), 20, 0.5)
end

-- ---------------------------------------------------------------- the field (the dummy area)
local function field()
	local x0, x1, z0, z1 = F.x0, F.x1, F.z0, F.z1
	blk("Shell", "FieldFloor", x0, x1, 236, Y0, z0, z1, W.floor, { tex = "TrConcrete" })
	local st = F.stage
	blk("Shell", "Stage", st.x0, x1, Y0 - 1, st.y, st.z0, z1 - 4, W.floor2, { tex = "TrConcrete" }) -- (on under the far wall to the lot's bay: no gap under the garage door)
	nose("StageNose", st.x0, x1, st.y - 0.45, st.z0, "x", 0.9)
	-- the east wall (in front of the range's west wall), piers on it; the far wall with the garage (TrainingLot builds
	-- the door, its frame, transom and panel at the opening x -12..12, sill 242, face z -8258), the big target on the
	-- compound's axis; the west terrace wall (low: the course shows over it)
	blk("Shell", "FieldWallE", x1, x1 + 6, 236, 280, BAL.z0, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "FarWall", x0 - 4, -12, 236, 290, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "FarWall", 12, x1 + 6, 236, 290, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "FarWall", -12, 12, 258.55, 290, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	dressWall("FarWall", "x", z1, 1, x0, x1, Y0, 290, { holes = { { -26, 16, 236, 262 }, { -60, -20, 236, 300 } }, bay = 18, frames = true })
	dressWall("EastWall", "z", x1, -1, z1, z0, 258, 280, { noPlinth = true, bay = 26, holes = { { -8216, -8204, 236, 262 } } })
	colonnade(-8154, -8246)
	blk("Shell", "Walkway", x1 - 10, x1, Y0, Y0 + 1, z0, F.stage.z0, "8d9097", { tex = "TrConcrete" })
	blk("Shell", "Walkway", x0, x0 + 4, Y0, Y0 + 1, z0, F.DECK.z0, "8d9097", { tex = "TrConcrete" })
	-- the far third: a terrace between the practice deck (246) and the stage (242) at 244, its stair on the main lane
	local BA = { x0 = F.DECK.x1, x1 = st.x0, z0 = F.DECK.z0, top = 244 }
	mass("Bastion", BA.x0, BA.x1, BA.z0, z1, 236, BA.top, { "z0", "x1" })
	stair("BastionStair", "z", BA.z0 + 6, BA.z0, Y0, BA.top, GH.xm - 6, GH.xm + 6, 4, W.ledge) -- (in the axis lane)
	-- the target on the axis, in a deep round recess with a lit rim
	local tx = GH.xm
	-- the tower block behind it: 4 forward of the wall, up past the walls' top, cream corners, a rounded coping
	local tf = z1 + 4
	blk("Shell", "TargetTower", tx - 18, tx + 18, 236, 298, z1, tf, W.pier2, { tex = "TrPaint" })
	for _, sd in { -1, 1 } do blk("Shell", "TargetTowerCorner", tx + sd * 18 - 1.6, tx + sd * 18 + 1.6, Y0, 296, tf + 1.2, z1, W.pier, { tex = "TrPaint" }) end
	blk("Shell", "TargetTowerCoping", tx - 19.8, tx + 19.8, 296, 298.6, z1, tf + 1.8, W.trim, { tex = "TrPaint" })
	nose("TargetTowerLip", tx - 19.8, tx + 19.8, 296.2, tf + 1.8, "x", 2.2)
	for _, d in { { 15, 1.4, W.pier }, { 9.6, 1.6, W.slate }, { 5.4, 1.8, W.pier2 } } do
		B.part("Shell", "TowerEmblem", CF(tx, 286, tf + d[2] / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(d[2], d[1], d[1]), d[3], { cyl = true })
	end
	z1 = tf -- (the target and its frame stand on the tower's face)
	B.part("Shell", "TargetRecess", CF(tx, 258, z1 + 0.35) * CFrame.Angles(0, math.pi / 2, 0), V3(0.7, 22, 22), W.slate, { cyl = true })
	B.part("Scenery", "TargetRim", CF(tx, 258, z1 + 0.75) * CFrame.Angles(0, math.pi / 2, 0), V3(0.12, 22.6, 22.6), W.trim, { cyl = true, ghost = true })
	B.put("tv_target", CF(tx, 258, z1 + 1.4), { name = "FieldTarget", scale = 1.15 })
	-- its cream frame (the field's big thing on the axis)
	blk("Shell", "TargetPanel", tx - 12, tx + 12, 242, 270, z1, z1 + 0.3, W.slate, { tex = "TrSlate" })
	B.lamp(tx, 262, z1 + 9, "point", 30, 0.5, W.lamp)
	blk("Shell", "TargetFrame", tx - 15, tx + 15, 270, 273.4, z1, z1 + 2, W.pier, { tex = "TrPaint" })
	blk("Shell", "TargetFrame", tx - 15, tx - 12, 242, 270, z1, z1 + 2, W.pier, { tex = "TrPaint" })
	blk("Shell", "TargetFrame", tx + 12, tx + 15, 242, 270, z1, z1 + 2, W.pier, { tex = "TrPaint" })
	blk("Shell", "TargetFrameCap", tx - 15.6, tx + 15.6, 273.4, 274.6, z1, z1 + 2.6, W.trim, { tex = "TrPaint" })
	nose("TargetFrameLip", tx - 15.6, tx + 15.6, 273.4, z1 + 2.6, "x", 1.0)
	-- (bodies only, in front of the target: nobody stands with their head under its rim; shots pass)
	local tg = B.solid("TargetGuard", CF(tx, 257, z1 + 3.8), V3(24, 26, 7.6))
	tg.CanQuery = false; tg.CollisionGroup = T.RANGE_WALL_GROUP or "JFRayBlind"
	z1 = F.z1
	-- the west terrace wall
	blk("Shell", "TerraceWall", x0 - 4, x0, 236, Y0 + 7, z0 - 0.6, z1, W.slate, { tex = "TrSlate" })
	nose("TerraceNose", z0 - 0.6, z1, Y0 + 7, x0 - 2, "z", 1.6)
	-- the gantry: three towers (the kit's) and a deck across the field at 20 m, white noses along both edges
	for _, gx in F.towers do
		blk("Shell", "GantryTower", gx - 4.4, gx + 4.4, Y0, F.gtop, F.gz - 4.4, F.gz + 4.4, W.pier, { tex = "TrPaint" })
		blk("Shell", "GantryTowerBase", gx - 4.5, gx + 4.5, Y0, Y0 + 3.4, F.gz - 4.5, F.gz + 4.5, W.plinth, { tex = "TrSlate" }) -- (flush: no ledge by the board)
		blk("Shell", "GantryTowerCap", gx - 5, gx + 5, F.gtop - 1.6, F.gtop, F.gz - 5, F.gz + 5, W.trim, { tex = "TrPaint" })
	end
	blk("Shell", "GantryDeck", x0, x1, F.gtop, F.gtop + 2.4, F.gz - 4, F.gz + 4, W.pier2, { tex = "TrPaint" })
	blk("Shell", "GantrySoffit", x0, x1, F.gtop - 1.2, F.gtop, F.gz - 3, F.gz + 3, W.slate, { tex = "TrSlate" })
	for _, s in { -1, 1 } do
		nose("GantryNose", x0, x1, F.gtop + 2.4, F.gz + s * 4, "x", 1.1)
		blk("Shell", "GantryFascia", x0, x1, F.gtop - 2.4, F.gtop, F.gz + s * 3, F.gz + s * 4, W.pier2, { tex = "TrPaint" })
		blk("Shell", "GantryCurb", x0, x1, F.gtop + 2.4, F.gtop + 3.6, F.gz + s * 4, F.gz + s * 3, W.wall2, { tex = "TrPlaster" })
	end
	-- the gantry's gate on the compound's axis (judge round 1: a big thing in the middle, every move framed): two cream
	-- piers and a lintel over the deck, the opening framing the far wall's target from the gatehouse
	for _, gx in { GH.xm - 12, GH.xm + 12 } do
		blk("Shell", "GatePier", gx - 4, gx + 4, Y0, 262.4, F.gz - 4.6, F.gz + 4.6, W.pier, { tex = "TrPaint" })
		blk("Shell", "GatePierBase", gx - 4.6, gx + 4.6, Y0, Y0 + 3.6, F.gz - 5.2, F.gz + 5.2, W.plinth, { tex = "TrSlate" })
	end
	blk("Shell", "GateLintel", GH.xm - 16, GH.xm + 16, 258.6, 262.4, F.gz - 4.6, F.gz + 4.6, W.pier2, { tex = "TrPaint" })
	blk("Shell", "GateLintelCap", GH.xm - 16.8, GH.xm + 16.8, 262.4, 263.8, F.gz - 5.4, F.gz + 5.4, W.trim, { tex = "TrPaint" })
	for _, sd in { -1, 1 } do nose("GateLintelLip", GH.xm - 16.8, GH.xm + 16.8, 262.4, F.gz + sd * 5.4, "x", 1.0) end
	-- distance: posts (the kit's) at the sides at 10 and 30 m, plates on the towers at 20 m, pale lines across
	local function plate(txt, x, y, z)
		word("DistPlate", txt, 2.6, 1.2, facing(x, y, z, x, z + 10), W.board)
	end
	for _, pp in { { -96, -8180, 10, Y0 }, { 16, -8180, 10, Y0 } } do
		B.put("tr_post", CF(pp[1], pp[4], pp[2]), { name = "DistPost" })
		B.solid("DistPostSolid", CF(pp[1], pp[4] + 3.3, pp[2]), V3(2.4, 6.6, 2.4))
		plate(("%d M"):format(pp[3]), pp[1], pp[4] + 4.3, pp[2] + 1.25)
	end
	-- (the static dummies' plinths)
	for _, nm in { "Stand1", "Stand2", "Armour1", "Armour2", "Heal1", "Heal2" } do
		local d = T.DUMMIES[nm]
		B.drum("Shell", "DummyPlinthLip", d[1], d[3], d[2] - 1, d[2] - 0.6, 7.2, W.plinth)
		B.drum("Shell", "DummyPlinth", d[1], d[3], d[2] - 1, d[2] - 0.25, 6.4, W.pier2)
		B.drum("Shell", "DummyPlinthTop", d[1], d[3], d[2] - 0.25, d[2], 5.8, W.trim)
	end
	word("DistPlate", "30 M", 4, 1.8, facing(-72, F.DECK.top - 3, F.DECK.z0 + 0.15, -72, F.DECK.z0 + 10), W.board) -- (clear of the board in the balcony's view)
	word("DistPlate", "20 M", 6.4, 2.4, facing(GH.xm, 260.5, F.gz + 4.75, GH.xm, F.gz + 14), W.board) -- (on the gate's lintel)
	-- the axis lane (judge round 2: the empty floor): its walls line up with the balcony's stair and the gate's opening
	for _, lx in { GH.xm - 8 - 1.7, GH.xm + 8 + 1.7 } do
		for _, zz in { { F.z0 - 8, F.gz + 4.6 }, { F.gz - 4.6, F.DECK.z0 } } do
			blk("Shell", "LaneWall", lx - 1.7, lx + 1.7, Y0, Y0 + 3.5, zz[1], zz[2], W.slate, { tex = "TrSlate" })
			nose("LaneWallLip", zz[1], zz[2], Y0 + 2.5, lx, "z", 3.4) -- (a rounded cap the wall's width)
		end
		-- the 10 m plinth on it, its plate toward the balcony
		blk("Shell", "DistPlinth", lx - 2.4, lx + 2.4, Y0, Y0 + 7.4, -8182.4, -8177.6, W.plinth, { tex = "TrSlate" })
		blk("Shell", "DistPlinthCap", lx - 2.8, lx + 2.8, Y0 + 7.4, Y0 + 8.4, -8182.8, -8177.2, W.trim, { tex = "TrPaint" })
		word("DistPlate", "10 M", 3.6, 1.8, facing(lx, Y0 + 5.6, -8177.45, lx, -8160), W.board)
	end
	-- cover in the middle band (the main lane and the practice lane stay clear)
	mass("CoverBlock", -62, -54, -8186, -8196, 236, Y0 + 4.6, { "z0", "z1" })
	for _, c in { { "tv_cover", -60, -8238, math.pi / 2, 244 } } do
		B.put(c[1], CF(c[2], c[5], c[3]) * CFrame.Angles(0, c[4], 0), { name = "Cover" })
		B.solid("CoverBox", CF(c[2], c[5] + 2.35, c[3]), if c[4] == 0 then V3(10, 4.7, 2.4) else V3(2.4, 4.7, 10))
	end
	-- the practice lane (the field's west strip): its deck at 30 m, its rails, consoles on the balcony, its board, a heal
	-- pad, its box (its dummies shoot back only at players inside it)
	local pr = K.folderIn(B.root, "Practice")
	local DK = F.DECK
	mass("PracticeDeck", DK.x0, DK.x1, DK.z0, z1, 236, DK.top, { "z0", "x1" })
	stair("DeckStair", "x", DK.x1 + 4, DK.x1, 244, DK.top, DK.z0 - 1, DK.z0 - 9, 2, W.ledge) -- (up from the terrace)
	local s3, s4, s5 = T.DUMMIES.Stand3, T.DUMMIES.Stand4, T.DUMMIES.Dummy2
	console(pr, "BehaviourButton", "BEHAVIOUR", -100, GY, -8143, W.amber, "Change", "BEHAVIOUR")
	console(pr, "HealthButton", "HEALTH", -84, GY, -8143, "6fbf86", "Change", "HEALTH")
	local board = Instance.new("Part")
	board.Name = "Board"; board.Anchored = true; board.CanCollide = false; board.CanQuery = false; board.CanTouch = false; board.CastShadow = false
	board.Size = V3(22, 5.6, 0.25); board.Color = Color3.fromHex(W.board); board.Material = Enum.Material.SmoothPlastic
	board.CFrame = B.at(facing(-80, Y0 + 9.2, F.gz + 4.45, -80, F.gz + 20))
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 40; g.LightInfluence = 0
	for i, c in { { "Damage", "DAMAGE", "0" }, { "Dps", "DPS", "-" }, { "Ttk", "TIME TO KILL", "-" } } do
		local col = Instance.new("Frame")
		col.Name = c[1]; col.BackgroundTransparency = 1; col.Size = UDim2.fromScale(1 / 3, 1); col.Position = UDim2.fromScale((i - 1) / 3, 0)
		local lab = Instance.new("TextLabel")
		lab.Name = c[1] .. "Label"; lab.BackgroundTransparency = 1; lab.Size = UDim2.fromScale(0.9, 0.26); lab.Position = UDim2.fromScale(0.05, 0.1)
		lab.TextScaled = true; lab.Text = c[2]; lab.TextColor3 = Color3.fromHex(W.grey)
		lab.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.SemiBold)
		lab.Parent = col
		local val = Instance.new("TextLabel")
		val.Name = c[1] .. "Value"; val.BackgroundTransparency = 1; val.Size = UDim2.fromScale(0.9, 0.5); val.Position = UDim2.fromScale(0.05, 0.4)
		val.TextScaled = true; val.Text = c[3]; val.TextColor3 = Color3.fromHex(W.pale)
		val.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
		val.Parent = col
		col.Parent = g
	end
	g.Parent = board
	board.Parent = pr
	-- (the board hangs under the gantry's deck between its west towers, facing the balcony, on two hangers)
	blk("Shell", "BoardPlinth", -91.6, -68.4, Y0, Y0 + 5.9, F.gz + 3.4, F.gz + 4.6, W.pier2, { tex = "TrPaint", nq = true })
	nose("BoardPlinthLip", -91.6, -68.4, Y0 + 5.55, F.gz + 4.6, "x", 1.2)
	blk("Shell", "BoardHousing", -91.6, -68.4, Y0 + 5.9, Y0 + 12.5, F.gz + 4.0, F.gz + 4.3, W.pier2, { tex = "TrPaint" })
	K.healPad(B, -91, Y0, -8166)
	local zone = Instance.new("Part")
	zone.Name = "Zone"; zone.Anchored = true; zone.Transparency = 1; zone.CanCollide = false; zone.CanQuery = false; zone.CanTouch = false
	zone.Size = V3(-60 - x0, 30, z0 - z1); zone.CFrame = B.cf((x0 + -60) / 2, Y0 + 15, (z0 + z1) / 2)
	zone.Parent = pr
	-- lamps: tall posts along the east wall throw light across the field (the daylight does the rest)
	for _, pz in { -8170, -8230 } do B.lamp(x1 - 6, 270, pz, "point", 60, 0.4, W.lamp) end
end

-- ---------------------------------------------------------------- the course (outside)
local function course()
	local x0, x1, z0, z1 = CO.x0, CO.x1, CO.z0, CO.z1
	blk("Shell", "CourseFloor", x0, x1, 236, Y0, z0, z1, W.floor, { tex = "TrConcrete" })
	-- walls: west and south (the TOP's back: a hole for the egg door's room), the north wall is the tutorial corridor's
	-- south wall (tutorial()), the east is the field's terrace wall
	blk("Shell", "CourseWallW", x0 - 4, x0, 236, CO.wallTop, TU.cz1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CourseWallN", x0, TU.x0 - 4, 236, CO.wallTop, TU.cz1, z0, W.wall, { tex = "TrPlaster" })
	local td = T.TOPD3
	local hx0, hx1, hy0, hy1 = td.x - td.w / 2, td.x + td.w / 2, td.y, td.y + td.h
	blk("Shell", "CourseWallS", x0 - 4, hx0, 236, CO.wallTop, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CourseWallS", hx1, x1, 236, CO.wallTop, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CourseWallS", hx0, hx1, 236, hy0, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CourseWallS", hx0, hx1, hy1, CO.wallTop, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	dressWall("CourseWallW", "z", x0, 1, z1, z0, Y0, CO.wallTop, { bay = 28, frames = true, holes = { { -8193, -8183, 269, 279 } } })
	dressWall("CourseWallS", "x", z1, 1, x0, x1, Y0, CO.wallTop, { bay = 26, frames = true, holes = { { -330, -264, 236, 300 }, { -270, -202, 236, 273 } } })
	dressWall("CourseWallN", "x", z0, -1, x0, x1, 256, CO.wallTop, { noPlinth = true, bay = 26, piersIn = { -300, -118 } })
	for i, pl in ipairs({ { -145, -8206, 243.4 }, { -155, -8204, 246.8 }, { -165, -8201, 250.2 }, { -175, -8197, 253.8 } }) do
		B.drum("Shell", "CoursePlinth" .. i, pl[1], pl[2], 236, pl[3] - 0.6, 8, W.slate)
		B.drum("Shell", "CoursePlinthCap" .. i, pl[1], pl[2], pl[3] - 0.6, pl[3], 8.6, W.trim)
	end
	-- the start pad by the way in
	B.drum("Shell", "StartPadLip", -130, -8204, Y0, Y0 + 0.6, 21, W.trim)
	B.drum("Shell", "StartPad", -130, -8204, Y0, Y0 + 1, 19.6, W.slate)
	gallery("Gallery", -300, -118, z0, z0 - 18, 256, 22, { -133, -123 })
	stair("GalleryStair", "z", -8186, -8158, Y0, 256, -132, -124, 16, W.ledge, "both")
	-- 1 the sprint lane along the north wall, three low hurdles
	for _, hx in { -150, -176, -202 } do
		blk("Shell", "Hurdle", hx - 1.2, hx + 1.2, Y0, Y0 + 1.6, z0 - 2, z0 - 14, W.slate, { tex = "TrSlate" })
		nose("HurdleNose", z0 - 2, z0 - 14, Y0 + 1.6, hx, "z", 0.9)
	end
	-- 2 the slide tunnel: a heavy block over the lane, 3.4 to its underside (crouch or slide)
	local sx0, sx1 = -262, -226
	blk("Shell", "SlideBlock", sx0, sx1, Y0 + 3.4, 254, z0, z0 - 16, W.slate, { tex = "TrSlate" }) -- (up to the gallery's deck)
	nose("SlideNose", z0, z0 - 16, Y0 + 3.4, sx1, "z", 1.2)
	nose("SlideNose", z0, z0 - 16, Y0 + 3.4, sx0, "z", 1.2)
	blk("Shell", "SlideSide", sx0, sx1, Y0, 254, z0 - 16, z0 - 18, W.slate, { tex = "TrSlate" })
	blk("Scenery", "SlideLight", sx0 + 1, sx1 - 1, Y0 + 3.3, Y0 + 3.4, z0 - 5, z0 - 11, W.lamp, { ghost = true, mat = NEON })
	-- 3 the west climb: four blocks stepping up south along the west wall (4 each: a jump), then the TOP by the grapple
	local climbs = { { -8158, -8174, 244 }, { -8178, -8192, 248 }, { -8196, -8208, 252 }, { -8212, -8222, 256 } }
	for i, c in ipairs(climbs) do mass("Climb" .. i, x0, x0 + 26, c[1], c[2], 236, c[3], { "z0", "x1" }) end
	-- grapple hoops (the 16 Nov kit's) under a beam over the climb, to swing up onto the TOP
	blk("Shell", "HoopBeam", x0, x0 + 34, 278, 281, -8214, -8220, W.pier2, { tex = "TrPaint" })
	for _, hx in { x0 + 8, x0 + 22 } do B.put("tv_hoop", CF(hx, 278, -8217), { name = "GrappleHoop" }) end
	blk("Shell", "HoopColumn", x0 + 32, x0 + 36, Y0, 281, -8215, -8219, W.pier, { tex = "TrPaint" })
	blk("Shell", "HoopColumnBase", x0 + 31.5, x0 + 36.5, Y0, Y0 + 1.6, -8214.5, -8219.5, W.plinth, { tex = "TrSlate" })
	-- 4 the tower in the middle (the 16 Nov kit's eight-sided one), gold Carl 3 on its top
	local tx, tz, tr = CO.TOWER.x, CO.TOWER.z, 11
	B.drum("Shell", "TowerBase", tx, tz, Y0, Y0 + 3.4, tr * 2 + 1.6, W.plinth)
	B.drum("Shell", "TowerDrum", tx, tz, Y0, 268.6, tr * 2, W.wall)
	B.drum("Shell", "TowerCap", tx, tz, 268.6, 270, tr * 2 + 1, W.trim) -- (its top is the deck; gold 3 stands on it)
	-- the deck's parapet: a ring of cream blocks, open where the last ledge comes up (north-west)
	for k = 0, 11 do
		local ang = k * 30
		if ang == 210 or ang == 240 or ang == 90 then continue end -- (the last ledge comes up at 225; the bridge leaves at 90)
		local cf = CF(tx, 0, tz) * CFrame.Angles(0, math.rad(ang), 0) * CF(tr - 0.4, 271.3, 0)
		B.part("Shell", "TowerParapet", cf, V3(1.2, 2.6, 6), W.pier2)
	end
	local ry = 258.4
	B.drum("Shell", "TowerRing", tx, tz, ry - 2.4, ry, 29, W.pier2)
	for k = 0, 15 do
		local cf = CF(tx, 0, tz) * CFrame.Angles(0, math.rad(k * 22.5), 0)
		B.part("Shell", "TowerRingLip", cf * CF(tr + 3.5, ry - 0.5, 0) * CFrame.Angles(0, math.pi / 2, 0), V3(5.8, 1.8, 1.8), W.trim, { cyl = true })
	end
	for _, st in { { 268, 262.4 }, { 232, 265.8 } } do
		local cf = CF(tx, 0, tz) * CFrame.Angles(0, math.rad(st[1]), 0)
		B.part("Shell", "TowerStep", cf * CF(tr + 1.75, (ry + st[2]) / 2, 0), V3(3.5, st[2] - ry, 6), W.pier2)
		B.part("Shell", "TowerStepNose", cf * CF(tr + 3.5, st[2] - 0.5, 0) * CFrame.Angles(0, math.pi / 2, 0), V3(6, 1.4, 1.4), W.trim, { cyl = true })
	end
	-- the bridge from the drum's deck (south) round to the TOP: a spur south, then west at the deck's height, a knee-high
	-- cream parapet both sides, a deep fascia under, two piers
	local by0, bz0, bz1 = 268.4, -8218, -8228
	blk("Shell", "BridgeDeck", tx - 4, tx + 4, by0, 270, tz - tr + 0.5, bz1, W.floor, { tex = "TrConcrete" })
	blk("Shell", "BridgeDeck", CO.TOP.x1 - 2, tx - 4, by0, 270, bz0, bz1, W.floor, { tex = "TrConcrete" })
	blk("Shell", "BridgeFascia", CO.TOP.x1 - 2, tx + 4, by0 - 2.2, by0, bz0 + 0.5, bz1 - 0.5, W.pier2, { tex = "TrPaint" })
	blk("Shell", "BridgeFascia", tx - 4, tx + 4, by0 - 2.2, by0, tz - tr + 0.5, bz0, W.pier2, { tex = "TrPaint" })
	for _, pr in { { CO.TOP.x1 - 2, tx - 4, bz0 - 1.2, bz0 }, { CO.TOP.x1 - 2, tx + 4, bz1, bz1 + 1.2 } } do
		blk("Shell", "BridgeParapet", pr[1], pr[2], 270, 272.6, pr[3], pr[4], W.pier2, { tex = "TrPaint" })
	end
	for _, sd in { -1, 1 } do blk("Shell", "BridgeParapet", tx + sd * 4 - 0.6, tx + sd * 4 + 0.6, 270, 272.6, tz - tr + 0.5, if sd < 0 then bz0 else bz1, W.pier2, { tex = "TrPaint" }) end
	for _, px in { -224, -248 } do
		blk("Shell", "BridgePier", px - 2.2, px + 2.2, Y0, by0 - 2.2, bz0 - 0.8, bz1 + 0.8, W.pier, { tex = "TrPaint" })
		blk("Shell", "BridgePierBase", px - 2.6, px + 2.6, Y0, Y0 + 3, bz0 - 0.4, bz1 + 0.4, W.plinth, { tex = "TrSlate" })
	end
	-- 5 the runway and the gap (slide-jump it)
	mass("Runway", -190, -150, -8222, -8236, 236, Y0 + 4, { "z0", "x1" })
	-- the lookouts: x0..x1 along the wall, out = how far into the course, along "x" (the south wall) or "z" (the west)
	local function lookout(name, along, face, dir, a0, a1, out, y)
		local function box(nm, aa, ab, ya, yb, o0, o1, hex)
			if along == "x" then blk("Shell", nm, aa, ab, ya, yb, face + dir * o0, face + dir * o1, hex, { tex = "TrPaint" })
			else blk("Shell", nm, face + dir * o0, face + dir * o1, ya, yb, aa, ab, hex, { tex = "TrPaint" }) end
		end
		box(name .. "Deck", a0, a1, y - 1.6, y, 0, out, W.pier2)
		box(name .. "Fascia", a0, a1, y - 3.4, y - 1.6, out - 1.4, out, W.pier)
		box(name .. "Parapet", a0, a1, y, y + 3, out - 2.2, out, W.pier2)
		box(name .. "Parapet", a0, a0 + 2.2, y, y + 3, 0, out - 2.2, W.pier2)
		box(name .. "Parapet", a1 - 2.2, a1, y, y + 3, 0, out - 2.2, W.pier2)
		for _, ca in { a0 + 3, a1 - 3 } do box(name .. "Corbel", ca - 1.6, ca + 1.6, y - 8, y - 1.6, 0, out - 2, W.pier) end
		local c = face + dir * (out - 1.1)
		if along == "x" then nose(name .. "Lip", a0, a1, y + 3, c, "x", 2.6) else nose(name .. "Lip", a0, a1, y + 3, c, "z", 2.6) end
	end
	lookout("WestLookout", "z", CO.x0, 1, -8196, -8170, 8, 260) -- (low enough that a jump from it never reaches the bullseye's trigger)
	lookout("SouthLookout", "x", CO.z1, 1, -176, -150, 8, 260)
	mass("Landing", -126, -108, -8222, -8236, 236, Y0 + 4, { "z0", "x0" })
	-- 6 the grand stair up the south wall to the TOP: 30 steps, cheek walls, a white nose on every tread
	local S = CO.STAIR
	-- three flights of eight (1.25 a step, treads 2 deep), two landings eight long
	local fl = { { S.x1, S.x1 - 16, Y0, Y0 + 10 }, { S.x1 - 24, S.x1 - 40, Y0 + 10, Y0 + 20 }, { S.x1 - 48, S.x0, Y0 + 20, CO.TOP.top } }
	for i, f in fl do stair("GrandStair" .. i, "x", f[1], f[2], f[3], f[4], S.z0, S.z1, 8, W.ledge, "c0", true) end
	for _, ld in { { S.x1 - 16, S.x1 - 24, Y0 + 10 }, { S.x1 - 40, S.x1 - 48, Y0 + 20 } } do
		blk("Shell", "StairLanding", ld[1], ld[2], 236, ld[3], S.z0, S.z1, W.ledge, { tex = "TrSlate" })
		blk("Shell", "StairLandingCheek", ld[1], ld[2], 236, ld[3] + 3.2, S.z0, S.z0 + 2.4, W.slate, { tex = "TrSlate" })
		nose("StairLandingCheekCap", ld[2], ld[1], ld[3] + 3.2, S.z0 + 1.2, "x", 2.5)
	end
	local function stairY(x)
		local d = S.x1 - x
		if d <= 16 then return Y0 + d * 10 / 16 elseif d <= 24 then return Y0 + 10 elseif d <= 40 then return Y0 + 10 + (d - 24) * 10 / 16
		elseif d <= 48 then return Y0 + 20 else return Y0 + 20 + (d - 48) * 10 / 16 end
	end
	local bxs = { -218, -236, -254 }
	for _, bx in bxs do
		blk("Shell", "StairPier", bx - 3, bx + 3, stairY(bx) - 2, CO.wallTop - 4.8, z1, z1 + 3.2, W.pier, { tex = "TrPaint" })
		blk("Shell", "StairPierCap", bx - 3.5, bx + 3.5, CO.wallTop - 6.2, CO.wallTop - 4.8, z1, z1 + 3.7, W.trim, { tex = "TrPaint" })
	end
	for i = 1, #bxs - 1 do
		local m = (bxs[i] + bxs[i + 1]) / 2
		local p0 = stairY(bxs[i + 1]) + 6
		local p1 = p0 + 12
		-- a framed bay between the buttresses (no blank glowing panel)
		blk("Shell", "StairBayFrame", m - 5.4, m + 5.4, p1, p1 + 1.4, z1, z1 + 1.2, W.pier2, { tex = "TrPaint" })
		blk("Shell", "StairBayFrame", m - 5.4, m + 5.4, p0 - 1.4, p0, z1, z1 + 1.2, W.pier2, { tex = "TrPaint" })
		blk("Shell", "StairBayFrame", m - 5.4, m - 4, p0, p1, z1, z1 + 1.2, W.pier2, { tex = "TrPaint" })
		blk("Shell", "StairBayFrame", m + 4, m + 5.4, p0, p1, z1, z1 + 1.2, W.pier2, { tex = "TrPaint" })
		B.lamp(m, (p0 + p1) / 2, z1 + 5, "point", 20, 0.4, W.warmLamp)
	end
	-- the gate at the stair's head: a cream pier over the cheek, a pilaster on the wall, a lintel with a lit soffit
	local gx0, gx1 = S.x0 + 1.8, S.x0 - 1.8
	blk("Shell", "StairGatePier", gx1, gx0, 236, 283, S.z0 + 2.4, S.z0 - 1.2, W.pier, { tex = "TrPaint" })
	blk("Shell", "StairGatePier", gx1, gx0, CO.TOP.top, 283, z1 + 3.2, z1, W.pier, { tex = "TrPaint" })
	blk("Shell", "StairGateLintel", gx1 - 0.4, gx0 + 0.4, 283, 286.4, S.z0 + 2.4, z1, W.pier2, { tex = "TrPaint" })
	nose("StairGateLip", S.z0 + 2.4, z1, 286.4, gx0 + 0.4, "z", 1.4)
	blk("Scenery", "StairGateSoffit", gx1 + 0.6, gx0 - 0.6, 282.86, 283, S.z0 - 1.6, z1 + 3.6, W.panel, { ghost = true, mat = NEON })
	B.lamp(S.x0 + 4, 279, (S.z0 + z1) / 2, "point", 22, 0.5, W.lamp)
	word("StairGateWord", "PARKOUR", 10, 1.8, facing(gx0 + 0.55, 284.3, (S.z0 + 2.4 + z1) / 2, gx0 + 20, (S.z0 + 2.4 + z1) / 2), W.board)
	-- 7 the TOP: a solid mass the width of the course's west end, the crown arch on its front edge, the egg door and the
	-- parkour teleporter in its back wall, TrainingArrive on it
	local TP = CO.TOP
	mass("TopMass", TP.x0, TP.x1, TP.z0, z1, 236, TP.top, { "z0", "x1" })
	for _, px in { -322, -304, -286 } do
		blk("Shell", "TopPier", px - 2.6, px + 2.6, Y0, TP.top - 1.4, TP.z0, TP.z0 + 2.4, W.pier, { tex = "TrPaint" })
		blk("Shell", "TopPierBase", px - 3, px + 3, Y0, Y0 + 3.4, TP.z0, TP.z0 + 2.9, W.plinth, { tex = "TrSlate" })
	end
	B.put("tr_crown", CF(-297, TP.top, TP.z0 - 2.6), { name = "TopCrown" })
	for _, sx in { -1, 1 } do B.solid("CrownLeg", CF(-297 + sx * 10, TP.top + 7, TP.z0 - 2.6), V3(4, 14, 4)) end
	K.topRoom(B, T.TOPD3)
	local ta = K.folderIn(B.doors, "TrainingArrive")
	for _, ax in { -316, -310 } do B.marker(ta, "TrainingArrive", ax, TP.top + 0.1, -8238, V3(ax, TP.top, -8200)) end
	-- the parkour teleporter (the egg door's ring in its green), east of the egg door on the back wall
	C.parkourPortal(-276, z1 + 4, TP.top)
	-- the secret bullseye high on the west wall (grapple it): to the playground
	local by, bz = 274, -8188
	B.put("tv_target", CF(x0 + 0.45, by, bz) * CFrame.Angles(0, math.pi / 2, 0), { name = "SecretTarget", scale = 0.4 })
	B.trigger("ToPlayground", x0 + 1.2, x0 + 4.2, by - 3, by + 3, bz - 3, bz + 3)
	-- the course's runner on its rail across the floor
	local rn = T.DUMMIES.Runner
	-- light: posts along the north wall's foot
	for _, lx in { -140, -200, -280 } do B.lamp(lx, 268, z0 - 20, "point", 60, 0.35, W.lamp) end
end

-- the green ring (the egg door's), its trigger to the parkour island
function C.parkourPortal(px, faceZ, top)
	local F2 = CFrame.lookAt(V3(px, top, faceZ), V3(px, top, faceZ - 1))
	local ring = 3
	local at = F2 * CF(0, 0, -ring)
	local pm = B.put("te_portal", at, { name = "ParkourPortalRing", raw = true, color = { ["17181c"] = "1c7a44", f0a53a = "3ddc84" } })
	if pm then
		for _, d in pm:GetDescendants() do
			if d:IsA("BasePart") and (string.match(d.Name, "_17181c$") or string.match(d.Name, "_f0a53a$")) then d.Material = NEON end
		end
	end
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
	local pl = Instance.new("PointLight")
	pl.Color = Color3.fromRGB(70, 255, 140); pl.Range = 14; pl.Brightness = 1.4; pl.Shadows = false; pl.Parent = fx
	local hum = Instance.new("Sound")
	hum.Name = "Hum"; hum.SoundId = "rbxassetid://9125674114"; hum.Looped = true; hum.Volume = 0.3
	hum.RollOffMode = Enum.RollOffMode.InverseTapered; hum.RollOffMinDistance = 6; hum.RollOffMaxDistance = 38
	hum.Playing = true; hum.Parent = fx
	fx.Parent = B.root.Scenery
	B.solid("ParkourPortalStep", F2 * CF(0, 0.3, -(ring - 0.9)), V3(10.6, 0.6, 3.2))
	local hwR, htR = 5.4, 10.8
	if pm then local _, bs = pm:GetBoundingBox(); hwR = math.max(bs.X, bs.Z) / 2; htR = bs.Y end
	local zf0, zf1 = faceZ - 1.4, faceZ - 4 -- (from in front of the ring back to the wall)
	for _, sd in { -1, 1 } do
		blk("Shell", "ParkourPortalJamb", px + sd * (hwR + 0.2), px + sd * (hwR + 1.8), top, top + htR + 3.4, zf0, zf1, W.pier, { tex = "TrPaint" })
	end
	blk("Shell", "ParkourPortalHead", px - hwR - 1.8, px + hwR + 1.8, top + htR + 3.4, top + htR + 5.2, zf0, zf1, W.pier2, { tex = "TrPaint" })
	B.trigger("ToParkour", px - 3, px + 3, top + 0.6, top + 7, faceZ - (ring - 1.6), faceZ - 3.9, { Land = "ParkourArrive", Say = "PARKOUR" })
	word("ParkourWord", "PARKOUR", 9, 1.8, F2 * CF(0, 11.2, -3.7) * CFrame.Angles(0, math.pi, 0), W.board)
end

-- ---------------------------------------------------------------- the tutorial hall
local function tutorial()
	local cz0, cz1 = TU.cz0, TU.cz1
	local x0, x1 = TU.x0, TU.x1
	-- the corridor: floor, the south wall (shared with the course: 8 thick west of the balcony), the west end, ceiling
	blk("Shell", "CorridorFloor", x0, x1, 236, GY, cz0 + 4, cz1, W.floor, { tex = "TrConcrete" }) -- (under the mouths too)
	blk("Shell", "CorridorWallS", x0 - 4, BAL.x0, 236, CO.wallTop, cz1, cz1 - 8, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CorridorWallS", BAL.x0, x1, 236, TU.ceil + 2, cz1, cz1 - 4, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CorridorWallW", x0 - 4, x0, 236, TU.top + 2, TU.rz1 - 4, cz1, W.wall, { tex = "TrPlaster" })
	blk("Shell", "CorridorCeiling", x0, x1, TU.ceil, TU.ceil + 2, cz0, cz1, W.ceil, { tex = "TrPlaster" })
	for x = x0 + 12, x1 - 4, 24 do
		blk("Shell", "CorridorBeam", x - 1.2, x + 1.2, TU.ceil - 1.8, TU.ceil, cz0, cz1, W.pier2, { tex = "TrPaint" })
		ceilPanel(x + 12, TU.ceil, (cz0 + cz1) / 2, 5)
	end
	-- the rooms' front wall with the mouths, between the corridor and the rooms
	local edges = { x0 - 4 }
	for _, r in TU.ROOMS do table.insert(edges, r.xm - 6); table.insert(edges, r.xm + 6) end
	table.insert(edges, x1)
	for i = 1, #edges - 1, 2 do blk("Shell", "RoomsFront", edges[i], edges[i + 1], 236, TU.top + 2, cz0 + 4, cz0, W.wall, { tex = "TrPlaster" }) end
	local tut = K.folderIn(B.root, "Tutorial")
	for i, r in TU.ROOMS do
		local f = K.folderIn(tut, "Room" .. i)
		blk("Shell", "MouthHead", r.xm - 6, r.xm + 6, GY + 12, TU.top + 2, cz0 + 4, cz0, W.wall, { tex = "TrPlaster" })
		B.put("tr_portal", CF(r.xm, GY, cz0 + 2), { name = "RoomFrame", scale = 0.72 })
		jambs("RoomJamb", r.xm, cz0 + 2, "x", 16 * 0.72, 12, 12, 4)
		word("RoomNumber", tostring(i), 2.6, 2.6, facing(r.xm + 9.4, GY + 7.2, cz0 - 0.15, r.xm + 9.4, cz0 - 10), W.board) -- (beside the door, faces the corridor)
		local lamp = blk("Scenery", "DoorLamp", r.xm - 4.5, r.xm + 4.5, GY + 12.9, GY + 13.3, cz0 - 0.3, cz0 - 0.05, W.teal, { ghost = true, mat = NEON })
		lamp.Parent = f
	end
	for i, r in TU.ROOMS do C.room(i, r) end
	-- the corridor's east end: the door into the gatehouse (its west wall's south door)
	word("WordFIELD", "FIELD", 7, 1.4, facing(x1 - 0.15, GY + 13.1, (cz0 + cz1) / 2, x1 - 10, (cz0 + cz1) / 2), W.board)
end

function C.room(i, r)
	local x0, x1, z0, z1 = r.x0, r.x1, TU.rz0, TU.rz1 -- (z0 the mouth's side, z1 the back: the room runs +z)
	local top = TU.top
	local tut = K.folderIn(B.root, "Tutorial")
	local f = K.folderIn(tut, "Room" .. i)
	blk("Shell", "RoomFloor", x0, x1, 236, GY, z0, z1, "7e8086", { tex = "TrTile" })
	if i == 1 then blk("Shell", "RoomWall", x0 - 4, x0, 236, top + 2, z0, z1, W.wall, { tex = "TrPlaster" }) end -- (into the back wall: no seam)
	blk("Shell", "RoomWall", x1, x1 + 4, 236, top + 2, z0, z1, W.wall, { tex = "TrPlaster" })
	blk("Shell", "RoomBack", x0 - 4, x1 + 4, 236, top + 2, z1, z1 - 4, W.wall, { tex = "TrPlaster" })
	-- walls: a dark wainscot under a chair rail, pale panels, a pilaster every second seam, a lit cove
	local n = 8
	local step = (z1 - z0) / n
	for _, w in { { x0, 1 }, { x1, -1 } } do
		local side, dir = w[1], w[2]
		blk("Shell", "Plinth", side, side + dir * 0.35, GY, GY + 1.4, z0, z1, W.deep, { tex = "TrSlate" })
		for k = 0, n - 1 do
			local a, b = z0 + k * step + 0.35, z0 + (k + 1) * step - 0.35
			blk("Shell", "Wainscot", side, side + dir * 0.3, GY + 1.6, GY + 8, a, b, W.ledge, { tex = "TrPaint" })
			blk("Shell", "WallPanel", side, side + dir * 0.3, GY + 8.6, GY + 22, a, b, W.wall2, { tex = "TrPlaster" })
		end
		for _, pzc in { 13, 36, 68, 97 } do
			local zc = z0 + pzc
			blk("Shell", "WallPlinth", side, side + dir * 2.6, GY, GY + 3.4, zc - 5, zc + 5, W.pier2, { tex = "TrPaint" })
			blk("Shell", "WallPlinthTop", side, side + dir * 2.9, GY + 3.4, GY + 3.9, zc - 5.3, zc + 5.3, W.trim, { tex = "TrPaint" })
			nose("WallPlinthLip", zc - 5.3, zc + 5.3, GY + 3.65, side + dir * 2.9, "z", 0.7)
			blk("Shell", "PlinthShelf", side, side + dir * 2.4, GY + 9.8, GY + 10.6, zc - 5.3, zc + 5.3, W.trim, { tex = "TrPaint" })
			blk("Scenery", "PlinthShelfLight", side + dir * 0.4, side + dir * 2.1, GY + 9.7, GY + 9.8, zc - 4.8, zc + 4.8, W.panel, { ghost = true, mat = NEON })
			B.lamp(side + dir * 2.2, GY + 8.6, zc, "point", 12, 0.5, W.warmLamp)
			niche(side, dir, zc, GY + 15) -- (over the head of anyone standing on the plinth)
		end
		for k = 2, n - 2, 2 do
			local z = z0 + k * step
			blk("Shell", "Pilaster", side, side + dir * 1.5, GY, GY + 22.4, z - 1.6, z + 1.6, W.pier, { tex = "TrPaint" })
		end
		blk("Shell", "CoveShelf", side, side + dir * 0.9, GY + 22.4, GY + 23, z0, z1, W.trim, { tex = "TrPaint" })
		blk("Scenery", "CoveLight", side + dir * 0.2, side + dir * 0.35, GY + 23, GY + 23.25, z0 + 0.5, z1 - 0.5, W.lamp, { ghost = true, mat = NEON })
	end
	-- the ceiling: deep beams across with lit panels between, the roof
	local beams = { z0 + 22, z0 + 44, z0 + 66, z0 + 88 } -- (none on the middle: the projector)
	for _, z in beams do blk("Shell", "RoomBeam", x0, x1, top - 8, top - 4, z - 1.3, z + 1.3, W.pier2, { tex = "TrPaint" }) end
	for _, z in { z0 + 44, z0 + 88 } do
		for _, sd in { -1, 1 } do
			local wx = if sd < 0 then x0 else x1
			blk("Shell", "BayJamb", wx, wx - sd * 2.4, GY, top - 8, z - 1.6, z + 1.6, W.pier, { tex = "TrPaint" })
			B.part("Shell", "BayChamfer", CF(wx - sd * 3.4, top - 9.6, z) * CFrame.Angles(0, 0, sd * math.rad(45)), V3(4.2, 4.2, 3.2), W.pier, {})
		end
		blk("Shell", "BayHead", x0, x1, top - 8, top - 6.4, z - 1.8, z + 1.8, W.pier, { tex = "TrPaint" })
	end
	blk("Shell", "RoomCeiling", x0, x1, top - 4, top, z0, z1, W.ceil, { tex = "TrPlaster" })
	for k = 0, 4 do
		local za, zb = z0 + k * 22 + 3, z0 + (k + 1) * 22 - 3
		if k ~= 2 then for _, px in { r.xm - 9, r.xm + 9 } do ceilPanel(px, top - 4, (za + zb) / 2, 7, "c9bfae") end end
	end
	blk("Shell", "RoomRoof", x0 - 4, x1 + 4, top, top + 2, z0, z1 - 4, W.ceil, { tex = "TrPlaster" })
	-- the projector (the kit's) over the middle, the lit ring on the floor under it
	local pz = (z0 + z1) / 2
	ceilPanel(r.xm, top - 4, pz, 12, "c9bfae")
	for _, q in { { -8.5, 8.5, -8.5, -7 }, { -8.5, 8.5, 7, 8.5 }, { -8.5, -7, -7, 7 }, { 7, 8.5, -7, 7 } } do
		blk("Shell", "CofferFrame", r.xm + q[1], r.xm + q[2], top - 5.8, top - 4, pz + q[3], pz + q[4], W.pier2, { tex = "TrPaint" })
	end
	B.drum("Shell", "FiringPadLip", r.xm, z0 + 6, GY, GY + 0.25, 7.6, W.plinth)
	B.drum("Shell", "FiringPad", r.xm, z0 + 6, GY, GY + 0.5, 6.6, W.pier2)
	-- the console: the kit's desk on the left of the way in (facing in, +x is the left here), its screen toward you,
	-- the teal only on it and on the board
	local cx, cz = r.xm + 12, z0 + 8
	B.put("tr_desk", CF(cx, GY, cz) * CFrame.Angles(0, math.pi, 0), { name = "Desk" })
	B.solid("DeskSolid", CF(cx, GY + 1.5, cz), V3(8.4, 3, 3))
	local scr = B.part("Shell", "DeskScreen", CF(cx, GY + 4.25, cz + 0.9) * CFrame.Angles(math.rad(20), 0, 0), V3(6.4, 2.6, 0.3), W.board)
	local sg = Instance.new("SurfaceGui")
	sg.Name = "Gui"; sg.Face = Enum.NormalId.Front; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 40; sg.LightInfluence = 0
	local tl = Instance.new("TextLabel")
	tl.BackgroundTransparency = 1; tl.Size = UDim2.fromScale(0.86, 0.5); tl.Position = UDim2.fromScale(0.07, 0.25); tl.TextScaled = true
	tl.Text = "WEAPONS"; tl.TextColor3 = Color3.fromHex(W.teal); tl.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	tl.Parent = sg
	sg.Parent = scr
	blk("Scenery", "DeskEdge", cx - 4.2, cx + 4.2, GY + 2.45, GY + 2.65, cz - 1.12, cz - 1.0, W.teal, { ghost = true, mat = NEON })
	B.lamp(cx, GY + 5.2, cz - 2.4, "point", 11, 0.6, W.teal)
	local btn = Instance.new("Part")
	btn.Name = "Console"; btn.Anchored = true; btn.Transparency = 1; btn.CanCollide = false; btn.CanQuery = false; btn.CanTouch = false
	btn.Size = V3(1, 1, 1); btn.CFrame = B.cf(cx, GY + 3.6, cz)
	btn.Parent = f
	local pp = Instance.new("ProximityPrompt")
	pp.Name = "Prompt"; pp.ActionText = "Weapons"; pp.ObjectText = "Tutorial"; pp.HoldDuration = 0
	pp.MaxActivationDistance = 9; pp.RequiresLineOfSight = false; pp.KeyboardKeyCode = Enum.KeyCode.E
	pp.Parent = btn
	-- the back wall's board (TutorialUI and the server paint it), its teal strip and soft light
	local zb = z1 - 4 -- (the back wall's face: the wall is z1 - 4 .. z1)
	blk("Shell", "EndStep", x0, x1, GY, GY + 0.8, zb - 3.2, zb, W.pier2, { tex = "TrPaint" })
	nose("EndStepNose", x0, x1, GY + 0.45, zb - 3.2, "x", 0.9)
	local board = B.text("Board", { { "ROOM " .. i, W.pale, "B", 1 } }, 24, 10, facing(r.xm, GY + 15, zb - 0.35, r.xm, zb - 20), { plate = W.board, thick = 0.3 })
	board.Parent = f
	blk("Shell", "BoardFrame", r.xm - 13.8, r.xm + 13.8, GY + 20, GY + 21.8, zb, zb - 3, W.pier, { tex = "TrPaint" })
	blk("Shell", "BoardFrame", r.xm - 13.8, r.xm + 13.8, GY + 8.2, GY + 10, zb, zb - 3, W.pier, { tex = "TrPaint" })
	blk("Shell", "BoardFrame", r.xm - 13.8, r.xm - 12, GY + 10, GY + 20, zb, zb - 3, W.pier, { tex = "TrPaint" })
	blk("Shell", "BoardFrame", r.xm + 12, r.xm + 13.8, GY + 10, GY + 20, zb, zb - 3, W.pier, { tex = "TrPaint" })
	blk("Scenery", "BoardEdge", r.xm - 12, r.xm + 12, GY + 9.7, GY + 9.9, zb - 3, zb - 3.1, W.teal, { ghost = true, mat = NEON })
	B.lamp(r.xm, GY + 7, zb - 6, "point", 14, 0.35, W.warmLamp)
	for _, z in { z0 + 26, z0 + 80 } do B.lamp(r.xm, top - 7, z, "point", 40, 0.45, W.lamp) end
	-- what the game reads
	local zone = Instance.new("Part")
	zone.Name = "Zone"; zone.Anchored = true; zone.Transparency = 1; zone.CanCollide = false; zone.CanQuery = false; zone.CanTouch = false
	zone.Size = V3(x1 - x0, 22, z1 - z0)
	zone.CFrame = B.cf(r.xm, GY + 11, (z0 + z1) / 2)
	zone.Parent = f
	B.marker(f, "Origin", r.xm, GY, z0 + 6, V3(r.xm, GY, z0 + 20))
	local db = Instance.new("Part")
	db.Name = "DoorBlock"; db.Anchored = true; db.Transparency = 1; db.CanCollide = false; db.CanQuery = false; db.CanTouch = false
	db.Size = V3(12, 12, 4)
	db.CFrame = B.cf(r.xm, GY + 6, TU.cz0 + 2)
	db.Parent = f
	f:SetAttribute("Room", i)
end

-- ---------------------------------------------------------------- the unseen lid and seal walls over the open part
local function lids()
	local L = LID
	seal("CompoundLid", L.x0, L.x1, L.y, L.y + 4, L.z0, L.z1)
	-- above the visible walls up to the lid (bodies stop, rays pass): west, south, east, the north line
	seal("SealWest", L.x0, CO.x0, CO.wallTop - 1, L.y + 1, L.z0, L.z1)
	seal("SealSouth", L.x0, L.x1, 270, L.y + 1, F.z1 - 0.1, L.z1)
	seal("SealEast", F.x1 + 0.1, L.x1, 270, L.y + 1, L.z0, L.z1)
	seal("SealNorth", L.x0, L.x1, 258, L.y + 1, -8132, -8136)
end

-- ---------------------------------------------------------------- the subtle textures: the variants, then put on by role
function C.materials(): string
	local MS = game:GetService("MaterialService")
	local n = 0
	for name, d in C.TEX do
		local mv = MS:FindFirstChild(name)
		if not (mv and mv:IsA("MaterialVariant")) then mv = Instance.new("MaterialVariant"); mv.Name = name end
		mv.BaseMaterial = d.base
		mv.ColorMap = "rbxassetid://" .. d.id
		mv.StudsPerTile = d.studs
		mv.MaterialPattern = if d.organic then Enum.MaterialPattern.Organic else Enum.MaterialPattern.Regular
		mv.Parent = MS
		n += 1
	end
	return n .. " material variants"
end
-- kit pieces carry their colour in their names: map the quiet family to the variants
local HEX_TEX = {
	["c9c3b8"] = "TrPlaster", ["d3cec4"] = "TrPlaster", ["8e9197"] = "TrPaint", ["7b7f87"] = "TrPaint", ["e4e0d6"] = "TrPaint",
	["5f646e"] = "TrSlate", ["4f545d"] = "TrSlate",
	["c4c0b8"] = "TrPlaster", ["b9b5ae"] = "TrPlaster", ["8f9299"] = "TrPaint", ["7d8088"] = "TrPaint", ["e2ded5"] = "TrPaint",
	["4a4e57"] = "TrSlate", ["3d414a"] = "TrSlate",
}
local function dress(p: BasePart, tex: string)
	local d = C.TEX[tex]
	if not d then return end
	if p.Material == NEON or p.Material == Enum.Material.Glass or p.Material == Enum.Material.ForceField or p.Transparency >= 0.99 then return end
	if p:FindFirstChildOfClass("SurfaceGui") then return end
	p.Material = d.base
	p.MaterialVariant = tex
end
local function materialsPass(before)
	local n = 0
	for p, tex in roles do if p.Parent then dress(p, tex); n += 1 end end
	-- the kit's meshes placed by this build (new since 'before')
	for _, d in B.root:GetDescendants() do
		if d:IsA("BasePart") and not before[d] and not roles[d] then
			local key = string.match(d.Name, "_(%x%x%x%x%x%x)$")
			local tex = key and HEX_TEX[string.lower(key)]
			if not tex and d:IsA("MeshPart") then tex = HEX_TEX[string.lower(d.Color:ToHex())] end
			if tex then dress(d, tex); n += 1 end
		end
	end
	return n
end

-- ---------------------------------------------------------------- build
function C.build(b): string
	B = b
	local put0 = B.put
	B.put = function(tmpl, cf, o)
		if string.sub(tmpl, 1, 3) == "tr_" then o = table.clone(o or {}); o.color = TRC end
		return put0(tmpl, cf, o)
	end
	roles = {}
	local before = {}
	for _, d in B.root:GetDescendants() do before[d] = true end
	C.materials()
	gatehouse()
	balcony()
	walk()
	field()
	course()
	tutorial()
	lids()
	-- the dummies' spots
	local ds = K.folderIn(B.mk, "DummySpots")
	for nm, d in T.DUMMIES do
		local m = B.marker(ds, nm, d[1], d[2], d[3], V3(d[1], d[2], d[3] + 10))
		local r = T.RAILS[nm]
		if r then m:SetAttribute("Span", r[1]); m:SetAttribute("Speed", r[2]) end
		if T.LANE[nm] then m:SetAttribute("Lane", "practice") end
		if T.DUMMY_HP[nm] then m:SetAttribute("HP", T.DUMMY_HP[nm]) end
		if T.HEALBACK[nm] then m:SetAttribute("HealBack", T.HEALBACK[nm]) end
	end
	B.put = put0
	local nTex = materialsPass(before)
	return ("v5 compound: gatehouse, balcony, walk, field, course, tutorial hall (%d rooms); %d parts with a texture"):format(#TU.ROOMS, nTex)
end

return C
