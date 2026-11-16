--!nocheck
-- THE ROTUNDA, part 2: the lift ring. behind the round room's five northern openings a curved walk, and off it five
-- lift bays, one per mode, left to right 1V1, 1V1V1, 2V2, 3V3, 4V4. the bays fan out from the FOCUS (the point on the
-- platform the spawn points stand round), each along the line through the middle of its opening, so every lift is
-- framed by its own two piers from where you appear. a bay is a tall shaft lit from the top: the pad lies on the
-- lift's deck (a kerb up from the walk), its board with the live count is in a chunky bezel on the shaft's back wall
-- between two guide rails, and a lit slot over every board (the game's name is on the
-- gallery, once). thick fins stand between the bays; a floor line runs from the focus to each deck. this replaces
-- the first round hub's pad corridor (two mirrored rows down a tunnel, which the owner called too on the nose).
-- called by HubRotunda.build with its helpers (B). distances here are from the focus
return function(B, R)
	local P, G = B.P, B.G
	local A, T = R.A, R.WALL
	local Neon = Enum.Material.Neon
	local S, C = "Shell", "Scenery"
	local D0, D1 = R.DECK0, R.DECK1 -- a deck's front, and the face of the wall behind it
	local BACK = D1 + 2
	local GREEN = { ["4f9a3a"] = "5f8a58", ["6bc24a"] = "7da06c", ["3f6b2a"] = "4f7550", ["4a3424"] = "6a5a4a", ["2a2c3e"] = P.pier2 }
	local bear = {}
	for i, md in R.MODES do bear[i] = R.liftBearing(md.side) end
	local half = (bear[5] - bear[1]) / 8 -- half a bay's angle
	local function hw(r) return r * math.tan(math.rad(half)) end

	for i, md in R.MODES do
		local b = bear[i]
		local F = B.lf(b)
		local w0 = R.reach(b, A + T) -- the round room's wall
		local wb, wf = hw(BACK) + 0.4, hw(D0 + 1.6) + 0.4
		local mid = (D0 + D1) / 2
		-- the bay's shell: floor, the ceiling over the walk, the shaft's front, lid and back wall
		B.box(F, S, "LiftFloor", -wb, wb, -2, -0.02, w0 - 3.4, BACK, P.floor)
		B.box(F, S, "WalkCeiling", -wf, wf, 14, 15, w0 - 2, D0 + 1.6, P.shell2)
		B.box(F, S, "ShaftFront", -wf, wf, 15, 23, D0, D0 + 1.6, P.shell)
		B.box(F, S, "ShaftLid", -wb, wb, 22, 23, D0, BACK, P.shell2)
		B.box(F, S, "BackWall", -wb, wb, 0, 23, D1, BACK, P.bay)
		-- the lift's deck with a marked nosing, the pad on it
		B.box(F, S, "Deck", -8, 8, 0, 0.6, D0, D1, P.deck)
		B.paint(F, "Nosing", -8, 8, 0.6, D0, D0 + 0.6, P.ray, 0.02)
		local pad = B.pad(F, md, 0, 0.6, D0 + 0.7 + md.dp / 2) -- (its front edge just behind the nosing)
		-- its board in a bezel on the back wall, between the guide rails
		local sc = 11.5 / 22
		local dc = D1 - 0.9 * sc
		B.put(F, "hb_screen", "Bezel", 0, 7.6, dc, 0, { scale = sc, seat = "centre", color = { ["2e3140"] = P.pier } })
		B.board(pad, F, md, 11.5, 5.75, 0, 7.6, dc - 0.12, 0, { thick = 0.5 })
		for _, s in { -1, 1 } do B.box(F, C, "GuideRail", s * 8.6 - 0.5, s * 8.6 + 0.5, 0, 22, D1 - 0.9, D1, P.cream, nil, G) end
		-- (round 2's judge: the bays were "dark boxes with a TV in them". so the top of the back wall is cut at 45 degrees with
		-- a hidden warm strip in it that washes the wall, and a warm light low in the bay lights the board's wall too)
		B.bar(F, C, "BayCove", 0, 2 * hw(D1) - 0.2, 0.6, D1 - 3.2, 22, D1, 19.2, P.cream, nil, G)
		B.box(F, C, "CoveStrip", -hw(D1) + 1.4, hw(D1) - 1.4, 18.8, 19.1, D1 - 0.4, D1 - 0.1, P.bayWash or P.strip, Neon, G)
		B.lamp(F, 0, 18.4, D1 - 1.4, 16, 1.1, P.bayWash or P.light, { spot = true, angle = 120, face = Enum.NormalId.Bottom })
		B.lamp(F, 0, 3.5, D1 - 4.5, 12, 0.6, P.bayWash or P.light)
		-- light: a big panel at the top of the shaft, a small one over the walk
		B.panel(F, 0, 22, mid, 8, 8)
		B.lamp(F, 0, 21.2, mid, 32, 1.7, P.light, { spot = true, angle = 80, shadows = true })
		B.panel(F, 0, 14, (w0 + D0) / 2, 2.4, 6)
		B.lamp(F, 0, 13, (w0 + D0) / 2, 20, 0.9)
		B.paint(F, "Ray", -0.32, 0.32, -0.02, w0, D0, P.ray, 0.05)
		B.lamp(F, 0, 9, D0 + 3, 15, 0.5) -- (a soft light in the mouth of the bay, on the board and the walls)
	end

	-- the fins between the bays: a light strip on each one's nose, a rib across the walk's ceiling
	for i = 1, 4 do
		local e = (bear[i] + bear[i + 1]) / 2
		local F = B.lf(e)
		B.box(F, S, "Fin", -1.3, 1.3, 0, 23, D0 - 0.6, BACK, P.shell)
		B.box(F, C, "FinNose", -1, 1, 0, 14, D0 - 1.1, D0 - 0.6, P.pier2, nil, G)
		B.box(F, C, "FinLight", -0.3, 0.3, 2.4, 11, D0 - 1.22, D0 - 1.1, P.strip, Neon, G)
		B.box(F, C, "WalkRib", -0.7, 0.7, 13.1, 14, R.reach(e, A + T), D0 - 0.6, P.cream, nil, G)
		B.lamp(F, 0, 6, D0 - 2.8, 12, 0.6)
	end
	-- the two end walls, which run in to the round room's corner piers; a plant in each end corner
	for _, s in { -1, 1 } do
		local e = s * (bear[5] + half)
		local F = B.lf(e)
		local w0 = R.reach(e, A + 1)
		B.box(F, S, "EndWall", -1.6, 1.6, 0, 23, w0, BACK, P.shell)
		B.box(F, C, "EndBase", -s * 1.6, -s * 1.95, 0, 0.7, w0 + 3, D0, P.pier2, nil, G)
		B.box(F, C, "EndLedge", -s * 1.6, -s * 2.1, 5, 5.5, w0 + 3, D0, P.cream, nil, G)
		B.box(F, C, "EndBand", -s * 1.6, -s * 1.75, 5.5, 7.2, w0 + 3, D0, P.band, nil, G)
		B.put(F, "bc_plantbig", "Plant", -s * 2.4, -0.02, D0 - 1.9, 0, { scale = 0.42, color = GREEN })
	end
end
