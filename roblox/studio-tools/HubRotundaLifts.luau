--!nocheck
-- THE ROTUNDA, part 2: the lift ring and the second floor over it. behind the round room's five northern openings a
-- curved walk, and off it five lift bays, one per mode, left to right 1V1, 1V1V1, 2V2, 3V3, 4V4. the bays fan out from
-- the FOCUS (the point on the platform the spawn points stand round), each along the line through the middle of its
-- opening, so every lift is framed by its own two piers from where you appear. the pad lies on the lift's deck (a kerb
-- up from the walk), its board with the live count in a chunky bezel on the bay's back wall between two guide rails.
-- thick fins stand between the bays; no floor lines. this replaced the first round hub's pad corridor (two mirrored rows
-- down a tunnel, which the owner called too on the nose).
-- THE SECOND FLOOR (owner, 16 Nov: "can you try to create a second floor of pads above the current one"): over the walk
-- and the bays, at the balcony's height, a crescent hall with seven more pads round its outer wall (R.UPPER), each with
-- its board on the wall behind it and a light panel over it, piers between. the bays were tall shafts lit from the top
-- until then; now they are 13 high, the second floor their ceiling. the way up is the jump pads to the balcony (sides 3
-- and 11: the owner, "we dont need stairs or escalators, we already have the jump pads"), then a doorway off the
-- balcony over each of the four outer lifts (HubRotundaCentre); the way down, the balcony's gaps over the jump pads.
-- called by HubRotunda.build with its helpers (B). distances here are from the focus
return function(B, R)
	local P, G = B.P, B.G
	local A, T = R.A, R.WALL
	local Neon = Enum.Material.Neon
	local S, C = "Shell", "Scenery"
	local D0, D1 = R.DECK0, R.DECK1 -- a deck's front, and the face of the wall behind it
	local BACK = D1 + 2
	local UY, ROOF, OUT = R.UP_Y, R.UP_ROOF, R.UP_OUT
	local LO = UY - 1 -- the second floor's underside: the ceiling of the walk and the bays
	local FT = UY - 0.1 -- the top of its slab, under the floor's finish (the doorways' sills are at UY - 0.06)
	local bear = {}
	for i, md in R.MODES do bear[i] = R.liftBearing(md.side) end
	local half = (bear[5] - bear[1]) / 8 -- half a bay's angle
	local E = R.endBearing() -- the end walls (bear[5] + half)
	local function hw(r) return r * math.tan(math.rad(half)) end

	for i, md in R.MODES do
		local b = bear[i]
		local F = B.lf(b)
		local w0 = R.reach(b, A + T) -- the round room's wall
		local wb = hw(BACK) + 0.4
		local mid = (D0 + D1) / 2
		-- the bay's shell: floor and back wall (the second floor is its ceiling)
		B.box(F, S, "LiftFloor", -wb, wb, -2, -0.02, w0 - 3.4, BACK, P.floor)
		B.box(F, S, "BackWall", -wb, wb, 0, LO, D1, BACK, P.bay)
		-- the lift's deck with a marked nosing, the pad on it
		B.box(F, S, "Deck", -8, 8, 0, 0.6, D0, D1, P.deck)
		B.paint(F, "Nosing", -8, 8, 0.6, D0, D0 + 0.6, P.ray, 0.02)
		local pad = B.pad(F, md, 0, 0.6, D0 + 0.7 + md.dp / 2) -- (its front edge just behind the nosing)
		-- its board in a bezel on the back wall, between the guide rails
		local sc = 11.5 / 22
		local dc = D1 - 0.9 * sc
		B.put(F, "hb_screen", "Bezel", 0, 7.6, dc, 0, { scale = sc, seat = "centre", color = { ["2e3140"] = P.pier } })
		B.board(pad, F, md, 11.5, 5.75, 0, 7.6, dc - 0.12, 0, { thick = 0.5 })
		for _, s in { -1, 1 } do B.box(F, C, "GuideRail", s * 8.6 - 0.5, s * 8.6 + 0.5, 0, LO, D1 - 0.9, D1, P.cream, nil, G) end
		-- the top of the back wall cut at 45 degrees, a warm light washing the board's wall (round 2's judge: the bays were
		-- "dark boxes with a TV in them"), a light panel in the ceiling over the deck and one over the walk
		B.bar(F, C, "BayCove", 0, 2 * hw(D1) - 0.2, 0.6, D1 - 1.4, LO + 0.3, D1, LO - 1.1, P.cream, nil, G)
		B.lamp(F, 0, LO - 1.6, D1 - 1.6, 14, 1, P.bayWash or P.light, { spot = true, angle = 120, face = Enum.NormalId.Bottom })
		B.lamp(F, 0, 3.5, D1 - 4.5, 12, 0.6, P.bayWash or P.light)
		B.panel(F, 0, LO, mid - 1, 7, 5)
		B.lamp(F, 0, LO - 1, mid - 1, 24, 1.4, P.light, { spot = true, angle = 90, shadows = true })
		B.panel(F, 0, LO, (w0 + D0) / 2, 2.4, 6)
		B.lamp(F, 0, LO - 1, (w0 + D0) / 2, 20, 0.9)
		B.lamp(F, 0, 9, D0 + 3, 15, 0.5) -- (a soft light in the mouth of the bay, on the board and the walls)
	end

	-- the fins between the bays: a light strip on each one's nose, a rib across the walk's ceiling
	for i = 1, 4 do
		local e = (bear[i] + bear[i + 1]) / 2
		local F = B.lf(e)
		B.box(F, S, "Fin", -1.3, 1.3, 0, LO, D0 - 0.6, BACK, P.shell)
		B.box(F, C, "FinNose", -1, 1, 0, LO, D0 - 1.1, D0 - 0.6, P.pier2, nil, G)
		B.box(F, C, "FinLight", -0.3, 0.3, 2.4, 11, D0 - 1.22, D0 - 1.1, P.strip, Neon, G)
		B.box(F, C, "WalkRib", -0.7, 0.7, LO - 0.9, LO, R.reach(e, A + T), D0 - 0.6, P.cream, nil, G)
		B.lamp(F, 0, 6, D0 - 2.8, 12, 0.6)
	end

	-- ---- the second floor: its slab and floor, its roof, in thin slices round the crescent (each one's inner end tucked
	-- into the round room's wall), the outer wall behind the pads
	do
		local n = math.ceil(2 * E / 3.7)
		local sl = 2 * E / n
		for k = 0, n - 1 do
			local c = -E + (k + 0.5) * sl
			local F = B.lf(c)
			local w = (OUT + 2) * math.tan(math.rad(sl / 2)) + 0.3
			B.box(F, S, "UpperSlab", -w, w, LO, FT, R.reach(c, A + T - 1.5), OUT + 2, P.shell2)
			B.box(F, S, "UpperFloor", -w, w, FT, UY, R.reach(c, A + T) - 0.4, OUT, P.floor)
			B.box(F, S, "UpperRoof", -w, w, ROOF, ROOF + 1, R.reach(c, A + T) - 0.6, OUT + 2, P.shell2)
		end
	end
	-- its pads, left to right, round the outer wall
	local nU = #R.UPPER
	for i, u in R.UPPER do
		local b = (i - (nU + 1) / 2) * R.UP_PITCH
		local F = B.lf(b)
		local md = table.clone(R.MODES[u.mode])
		md.name, md.bank = u.name, "upper"
		md.w, md.dp = R.UP_SIZE[md.id][1], R.UP_SIZE[md.id][2]
		local w = (OUT + 2) * math.tan(math.rad(R.UP_PITCH / 2)) + 0.4
		B.box(F, S, "UpperWall", -w, w, FT, ROOF + 0.96, OUT, OUT + 2, P.bay) -- (from the slab's top: no face shared with its underside. the bay's own pale wall, as in the lifts)
		B.box(F, C, "UpperBase", -w, w, UY, UY + 0.8, OUT - 0.25, OUT, P.pier, nil, G)
		B.box(F, C, "UpperBand", -w, w, UY + 9.4, UY + 9.9, OUT - 0.25, OUT, P.cream, nil, G)
		local dP = OUT - 1.2 - md.dp / 2
		local pad = B.pad(F, md, 0, UY, dP)
		local bw = md.w - 1.4
		B.board(pad, F, md, bw, bw / 2, 0, UY + 5.4, OUT - 0.45, 0, { thick = 0.4 })
		B.box(F, C, "BoardFrame", -bw / 2 - 0.35, bw / 2 + 0.35, UY + 5.4 - bw / 4 - 0.35, UY + 5.4 + bw / 4 + 0.35, OUT - 0.25, OUT - 0.02, P.pier2, nil, G)
		-- the bay round it (the owner's main session, 16 Nov: the hall "reads plain next to the rotunda below it"): guide rails
		-- either side of the board as in the lift bays, a cream lintel across the bay's mouth between the fins, the top of
		-- the wall cut at 45 degrees with a hidden lit strip under its lip washing the wall (no lamps: a strip glows)
		for _, s in { -1, 1 } do B.box(F, C, "UpperRail", s * (bw / 2 + 0.9) - 0.45, s * (bw / 2 + 0.9) + 0.45, UY - 0.04, ROOF - 1.6, OUT - 0.9, OUT - 0.02, P.cream, nil, G) end
		local wb = OUT * math.tan(math.rad(R.UP_PITCH / 2)) - 0.75 -- (the bay's half width at its wall, between the fins)
		local wh = (OUT - 4.9) * math.tan(math.rad(R.UP_PITCH / 2))
		B.box(F, C, "UpperBayHead", -wh, wh, ROOF - 2.2, ROOF - 1.6, OUT - 5.3, OUT - 4.5, P.cream, nil, G)
		B.bar(F, C, "UpperCove", 0, 2 * wb, 0.6, OUT - 1.4, ROOF + 0.3, OUT, ROOF - 1.1, P.cream, nil, G)
		B.box(F, C, "UpperCoveStrip", -wb + 0.6, wb - 0.6, ROOF - 1.4, ROOF - 1.2, OUT - 0.32, OUT - 0.1, P.bayWash or P.strip, Neon, G)
		-- the ceiling over the walk in coffers: a cream beam across at d 39.5 and at d 52 (the radial ribs are below)
		for _, d in { 39.5, 52 } do
			local wd = d * math.tan(math.rad(R.UP_PITCH / 2))
			B.box(F, C, "UpperBeam", -wd, wd, ROOF - 0.8, ROOF - 0.04, d - 0.5, d + 0.5, P.cream, nil, G)
		end
		B.panel(F, 0, ROOF, dP, 3, 3)
		B.lamp(F, 0, ROOF - 1.2, dP, 22, 0.9, P.light, { spot = true, angle = 90 })
		B.panel(F, 0, ROOF, 44, 2.4, 6)
		B.lamp(F, 0, ROOF - 1.2, 44, 22, 0.6)
	end
	-- the fins that make the bays (between the pads and at each end), a light strip on each one's nose, a cream rib from
	-- each across the ceiling to the round room's wall
	for i = 0, nU do
		local b = (i - nU / 2) * R.UP_PITCH
		local F = B.lf(b)
		B.box(F, S, "UpperFin", -0.7, 0.7, UY - 0.04, ROOF, OUT - 5.2, OUT - 0.02, P.shell) -- (feet just into the floor: no face shared with the dark foot along the wall)
		B.box(F, C, "UpperFinLight", -0.22, 0.22, UY + 2.4, UY + 10.4, OUT - 5.32, OUT - 5.2, P.strip, Neon, G)
		B.box(F, C, "UpperRib", -0.5, 0.5, ROOF - 0.8, ROOF, R.reach(b, A + T) + 0.3, OUT - 5.2, P.cream, nil, G)
	end
	-- along the round room's wall inside the hall: a dark foot and a cream rail at hand height, broken at each doorway,
	-- which gets a pale frame on this side too
	for _, side in { 12, 13, 0, 1, 2 } do
		local F = B.side(side)
		local wo = B.wid(A + T) / 2 + 0.05
		local spans = if R.UP_DOORS[side] then { { -wo, -5.2 }, { 5.2, wo } } else { { -wo, wo } }
		for _, sp in spans do
			B.box(F, C, "UpperInBase", sp[1], sp[2], UY, UY + 0.7, A + T, A + T + 0.3, P.pier2, nil, G)
			B.box(F, C, "UpperInRail", sp[1], sp[2], UY + 3.3, UY + 3.62, A + T + 0.08, A + T + 0.42, P.cream, nil, G)
		end
		if R.UP_DOORS[side] then
			for _, s in { -1, 1 } do B.box(F, C, "UpperJambIn", s * 4.6, s * 5.2, UY + 0.04, UY + 9.4, A + T, A + T + 0.35, P.creamHi, nil, G) end
			B.box(F, C, "UpperHeadIn", -5.2, 5.2, UY + 8.8, UY + 9.4, A + T, A + T + 0.35, P.creamHi, nil, G)
		end
	end

	-- ---- the two end walls, which run in to the round room's corner piers and close the second floor's ends too
	for _, s in { -1, 1 } do
		local e = s * E
		local F = B.lf(e)
		local w0 = R.reach(e, A + 1)
		B.box(F, S, "EndWall", -1.6, 1.6, 0, ROOF, w0, OUT + 2, P.shell)
		B.box(F, C, "EndBase", -s * 1.6, -s * 1.95, 0, 0.7, w0 + 3, D0, P.pier2, nil, G)
		B.box(F, C, "EndLedge", -s * 1.6, -s * 2.1, 5, 5.5, w0 + 3, D0, P.cream, nil, G)
		B.box(F, C, "EndBand", -s * 1.6, -s * 1.75, 5.5, 7.2, w0 + 3, D0, P.band, nil, G)
		-- (no pot plant here any more: the owner, 16 Nov, after a play-test: "in the match pads theres random pots on the
		-- ground?". the walk past the lifts keeps clear floor)
	end
end
