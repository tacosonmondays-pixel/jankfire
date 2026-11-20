--!nocheck
-- THE ROTUNDA, part 2 in the owner's own layout (19 Nov 2026, the owner's sketch, side-session-notes/owner-hub-layout-
-- sketch-2026-11-19.png: "new layout for hub, way bigger mirrored pads, still retaining the upper balcony area which can
-- be used as more decorative instead of having pads up there!"). R.LAYOUT = "mirror" builds this instead of
-- HubRotundaLifts. behind the round room's five northern openings, one crescent PAD HALL, double height: ten pads round
-- its outer wall, mirrored (from the west going up: 1V1, 1V1V1, 2V2, 3V3, 4V4; down the east side the same the other way,
-- the two 4V4s meeting at the top: R.PADS), each bigger than the lifts' were (R.PAD_SIZE), on a low deck in its own bay
-- between tall fins, its board on the wall over it, a lit coffer in the roof over it. over the inner part of the hall a
-- MEZZANINE at the balcony's height (the round room's four balcony doorways open onto it): no pads up there any more, a
-- place to sit and watch: sofas facing a glass rail over the pads, planters, and two big frames on the end walls for the
-- live boards (BoardSpot markers). the jump pads (sides 3 and 11) still throw you onto the round room's balcony.
-- called by HubRotunda.build with its helpers (B). distances here are from the focus, bearings from its north (B.lf)
return function(B, R)
	local P, G = B.P, B.G
	local A, T = R.A, R.WALL
	local Neon = Enum.Material.Neon
	local S, C = "Shell", "Scenery"
	local Tags = game:GetService("CollectionService")
	local ACCENT = P.doorGlow or P.glow -- (the building's one accent)
	local H = R.PAD_HALL
	local E, D0, D1, MEZ = H.E, H.D0, H.D1, H.MEZ
	local OUT = D1 + 2 -- (the back wall's outer face)
	local UY, ROOF = R.UP_Y, R.UP_ROOF
	local LO = UY - 1 -- the mezzanine's underside
	local FT = UY - 0.1 -- the top of its slab, under the floor's finish
	local DECK = 0.45 -- a pad's deck over the floor
	local seat = { ["3b2a52"] = P.creamHi, ff4fd8 = P.band }

	-- ---- the shell, in thin slices round the crescent (each one's inner end tucked into the round room's wall): the floor,
	-- the roof, the back wall the full height, and the mezzanine's slab and floor out to its edge
	do
		local n = math.ceil(2 * E / 3.5)
		local sl = 2 * E / n
		for k = 0, n - 1 do
			local c = -E + (k + 0.5) * sl
			local F = B.lf(c)
			local w = (OUT + 2) * math.tan(math.rad(sl / 2)) + 0.3
			local wm = MEZ * math.tan(math.rad(sl / 2)) + 0.12
			B.box(F, S, "PadHallFloor", -w, w, -2.1, -0.02, R.reach(c, A + T - 1.5), OUT, P.floor) -- (its underside off the armory floor's)
			B.box(F, S, "PadHallRoof", -w, w, ROOF, ROOF + 1, R.reach(c, A + T) - 0.6, OUT + 2, P.shell2)
			B.box(F, S, "BackWall", -w, w, -0.04, ROOF + 0.96, D1, OUT, P.bay)
			B.box(F, S, "UpperSlab", -wm, wm, LO, FT, R.reach(c, A + T - 1.5), MEZ, P.shell2)
			B.box(F, S, "UpperFloor", -wm, wm, FT, UY, R.reach(c, A + T) - 0.4, MEZ, P.floor)
			-- the mezzanine's edge: a lit accent line along the slab's face, a glass rail with a cream cap
			B.box(F, C, "MezNosing", -wm, wm, LO + 0.3, LO + 0.46, MEZ, MEZ + 0.08, ACCENT, Neon, G)
			B.box(F, S, "MezGlass", -wm, wm, UY, UY + 3.2, MEZ - 0.5, MEZ - 0.36, "d8eef2", Enum.Material.Glass, { tr = 0.72 })
			B.box(F, C, "MezRail", -wm, wm, UY + 3.2, UY + 3.5, MEZ - 0.62, MEZ - 0.24, P.cream, nil, G)
			-- the back wall's finish over the pads: a band at the mezzanine's height, a cornice under the roof
			B.box(F, C, "UpperBand", -w + 0.3, w - 0.3, UY + 4, UY + 4.5, D1 - 0.25, D1, P.cream, nil, G)
			B.box(F, C, "Cornice", -w + 0.3, w - 0.3, ROOF - 1, ROOF, D1 - 0.8, D1, P.cream, nil, G)
		end
	end
	-- the rail's posts, every few degrees, and a light under the mezzanine's edge
	do
		local n = math.ceil(2 * E / 9)
		for k = 0, n do
			local c = -E + k * (2 * E / n)
			local F = B.lf(c)
			B.box(F, C, "MezPost", -0.22, 0.22, UY, UY + 3.5, MEZ - 0.66, MEZ - 0.2, P.cream, nil, G)
		end
	end

	-- ---- the pads, round the back wall, mirrored: each on a low deck with a lit lip, its board over it on the back wall
	-- in a bezel, guide rails either side up to a header panel, a lit coffer in the roof over it, a light on it
	local padAt = {}
	for _, p in R.PADS do
		local b = p.b
		local F = B.lf(b)
		local md = table.clone(R.MODES[p.mode])
		md.name, md.bank = p.name, p.bank or "lifts" -- (the west pad of each pair "lifts", the east one "east")
		md.w, md.dp = R.PAD_SIZE[md.id][1], R.PAD_SIZE[md.id][2]
		local dw = md.w / 2 + 0.6 -- (the deck a little wider than its pad: the fins between the bays take its corners)
		B.box(F, S, "Deck", -dw, dw, -0.04, DECK, D0, D1, P.deck)
		B.box(F, C, "DeckNosing", -dw - 0.03, dw + 0.03, DECK - 0.16, DECK + 0.02, D0 - 0.05, D0 + 0.3, ACCENT, Neon, G)
		local dP = D0 + 1.2 + md.dp / 2
		local pad = B.pad(F, md, 0, DECK, dP)
		pad:SetAttribute("Bearing", b)
		pad:SetAttribute("Sight", math.abs(b) <= R.PAD_SIGHT) -- (R.check: seen from where you come out onto the platform)
		padAt[p.name] = { b = b, d = dP }
		-- its board: big, high on the back wall, in the lifts' bezel
		local bw = 14
		local sc = bw / 22
		local by = 10
		local dc = D1 - 0.9 * sc
		B.put(F, "hb_screen", "Bezel", 0, by, dc, 0, { scale = sc, seat = "centre", color = { ["2e3140"] = P.pier } })
		B.board(pad, F, md, bw, bw / 2, 0, by, dc - 0.12, 0, { thick = 0.5 })
		for _, s in { -1, 1 } do B.box(F, C, "GuideRail", s * (bw / 2 + 1.2) - 0.5, s * (bw / 2 + 1.2) + 0.5, DECK, by + bw / 4 + 2.6, D1 - 0.9, D1, P.cream, nil, G) end
		B.box(F, C, "HeaderPanel", -bw / 2, bw / 2, by + bw / 4 + 1.4, by + bw / 4 + 2.4, D1 - 0.17, D1 - 0.05, P.panel, Neon, G)
		B.box(F, C, "HeaderFrame", -bw / 2 - 0.35, bw / 2 + 0.35, by + bw / 4 + 1.05, by + bw / 4 + 1.4, D1 - 0.35, D1 - 0.02, P.cream, nil, G)
		B.box(F, C, "HeaderFrame", -bw / 2 - 0.35, bw / 2 + 0.35, by + bw / 4 + 2.4, by + bw / 4 + 2.75, D1 - 0.35, D1 - 0.02, P.cream, nil, G)
		-- a lit coffer in the roof over the pad, in a cream frame
		local cfx, cfd = md.w / 2 - 0.4, md.dp / 2 - 0.4
		B.box(F, C, "PadCoffer", -cfx, cfx, ROOF - 0.3, ROOF - 0.12, dP - cfd, dP + cfd, P.panel, Neon, G)
		for _, s in { -1, 1 } do
			B.box(F, C, "PadCofferFrame", s * cfx, s * (cfx + 0.7), ROOF - 0.95, ROOF - 0.05, dP - cfd - 0.7, dP + cfd + 0.7, P.cream, nil, G)
			B.box(F, C, "PadCofferFrame", -cfx, cfx, ROOF - 0.9, ROOF - 0.08, dP + s * cfd, dP + s * (cfd + 0.7), P.cream, nil, G)
		end
		B.lamp(F, 0, ROOF - 1.2, dP, 30, 1.1, P.light, { spot = true, angle = 80, shadows = math.abs(b) < 10 })
		B.lamp(F, 0, 6, D1 - 3, 14, 0.5, P.bayWash or P.light) -- (a soft light on the board's wall)
	end
	-- the fins between the bays: tall, full height, a light strip on each one's nose. each stands on the edge of its bays
	-- (a pad's bay: its half width plus 1.6 either side, at its front edge), not halfway between two pads' middles
	do
		local list = table.clone(R.PADS)
		table.sort(list, function(a, b) return a.b < b.b end)
		local function half(p) return math.deg((R.PAD_SIZE[R.MODES[p.mode].id][1] / 2 + 1.6) / (D0 + 1.2)) end
		for i = 1, #list - 1 do
			local e = list[i].b + half(list[i])
			local F = B.lf(e)
			B.box(F, S, "Fin", -1.3, 1.3, -0.04, ROOF, D0 - 0.6, D1, P.shell)
			B.box(F, C, "FinNose", -1, 1, -0.04, ROOF - 1, D0 - 1.1, D0 - 0.6, P.pier2, nil, G)
			B.box(F, C, "FinLight", -0.3, 0.3, 2.4, ROOF - 3, D0 - 1.22, D0 - 1.1, P.strip, Neon, G)
			B.box(F, C, "FinBase", -1.35, 1.35, -0.04, 1, D0 - 1.4, D1 + 0.5, P.pier, nil, G) -- (its end in the back wall)
		end
	end

	-- ---- under the mezzanine: a light panel and a lamp over the walk in front of each opening, cream ribs across its
	-- underside between them
	for _, side in { 12, 13, 0, 1, 2 } do
		local b = R.liftBearing(side)
		local F = B.lf(b)
		local m0 = R.reach(b, A + T)
		B.panel(F, 0, LO, (m0 + MEZ) / 2, 2.4, 6)
		B.lamp(F, 0, LO - 1, (m0 + MEZ) / 2, 22, 0.8)
	end
	do
		local n = math.ceil(2 * E / 12)
		for k = 0, n do
			local c = -E + k * (2 * E / n)
			if math.abs(c) > E - 2 then continue end
			local F = B.lf(c)
			B.box(F, C, "WalkRib", -0.6, 0.6, LO - 0.8, LO, R.reach(c, A + T) + 0.3, MEZ, P.cream, nil, G)
		end
	end
	-- light over the open part of the hall in front of the decks, from the roof
	for _, p in R.PADS do
		local F = B.lf(p.b)
		B.panel(F, 0, ROOF, (MEZ + D0) / 2, 2.4, 6)
	end

	-- ---- along the round room's wall on the mezzanine: a dark foot and a cream rail, broken at each doorway, which gets a
	-- pale frame and a lit sill on this side too; a cornice; pilasters where the round room's faces meet
	for _, side in { 12, 13, 0, 1, 2 } do
		local F = B.side(side)
		local wo = B.wid(A + T) / 2 + 0.05
		local spans = if R.UP_DOORS[side] then { { -wo, -5.2 }, { 5.2, wo } } else { { -wo, wo } }
		for _, sp in spans do
			B.box(F, C, "UpperInBase", sp[1], sp[2], UY, UY + 0.7, A + T, A + T + 0.3, P.pier2, nil, G)
			B.box(F, C, "UpperInRail", sp[1], sp[2], UY + 3.3, UY + 3.62, A + T + 0.08, A + T + 0.42, P.cream, nil, G)
		end
		if R.UP_DOORS[side] then
			for _, s in { -1, 1 } do B.box(F, C, "UpperJambIn", s * 4.6, s * 5.2, UY + 0.04, UY + 9.4, A + T, A + T + 0.35, P.cream, nil, G) end
			B.box(F, C, "UpperHeadIn", -5.2, 5.2, UY + 8.8, UY + 9.4, A + T, A + T + 0.35, P.cream, nil, G)
			B.box(F, C, "UpperSillGlow", -4.6, 4.6, UY - 0.02, UY + 0.12, A + T + 0.05, A + T + 0.35, ACCENT, Neon, G)
			B.box(F, C, "UpperSillGlow", -4.6, 4.6, UY + 0.02, UY + 0.16, A - 0.55, A - 0.25, ACCENT, Neon, G)
		end
		local o = if side % 2 == 0 then 0 else 0.05
		B.box(F, C, "UpperInCornice", -wo, wo, ROOF - 1 - o, ROOF - o, A + T, A + T + 0.8, P.cream, nil, G)
	end
	do
		local rcO = (A + T) / math.cos(math.pi / R.N)
		for _, i in { 11, 12, 13, 0, 1, 2 } do
			local F = B.fr((i + 0.5) * 360 / R.N)
			B.box(F, C, "UpperInPilaster", -0.95, 0.95, UY - 0.02, ROOF - 1.1, rcO - 0.3, rcO + 0.4, P.pier2, nil, G)
			B.box(F, C, "UpperInPilasterBase", -1.15, 1.15, UY, UY + 1.1, rcO - 0.3, rcO + 0.4, P.pier, nil, G)
			B.box(F, C, "UpperInPilasterCap", -1.25, 1.25, ROOF - 1.2, ROOF, rcO - 0.3, rcO + 1.05, P.cream, nil, G)
		end
	end

	-- ---- the mezzanine's seats and planters (the owner's taste: few big pieces, flat colours): between the doorways a
	-- sofa facing the rail with an armchair either side, a planter at the round room's wall; the ends a planter each
	local doorB = {}
	for _, side in { 12, 13, 1, 2 } do table.insert(doorB, R.liftBearing(side)) end
	local groups = { 0, (doorB[3] + doorB[4]) / 2, -(doorB[3] + doorB[4]) / 2, (doorB[4] + E) / 2, -(doorB[4] + E) / 2 }
	for k, b in groups do
		local F = B.lf(b)
		local dS = MEZ - 4.2
		B.put(F, "bc_sofa", "MezSofa", 0, UY, dS, 180, { scale = 1.1, solid = true, color = seat })
		for _, s in { -1, 1 } do -- (beside the sofa, a row facing the view, turned in a little)
			B.put(F, "bc_armchair", "MezArmchair", s * 7.8, UY, dS + 0.4, 180 - s * 15, { scale = 1.1, solid = true, color = seat })
		end
		B.put(F, R.prop("rk_coffeetable", "bc_coffeetable"), "MezTable", 0, UY, dS - 3.6, 0, { solid = true })
		B.lamp(F, 0, UY + 7, dS - 2, 14, 0.5, P.warm)
	end
	for _, b in { (doorB[1] + doorB[2]) / 2, -(doorB[1] + doorB[2]) / 2, E - 3, -(E - 3) } do
		local F = B.lf(b)
		local d = R.reach(b, A + T) + 2.6
		B.put(F, R.prop("rk_planter", "bc_planter"), "MezPlanter", 0, UY, d, 0, { solid = true })
	end

	-- ---- the two end walls, full height, and on each over the mezzanine's level a big lit frame for a live board (a
	-- BoardSpot marker in it: Board = "duels" on the west, "top" on the east; whoever owns the board puts it there)
	for _, s in { -1, 1 } do
		local e = s * E
		local F = B.lf(e)
		local w0 = R.reach(e, A + 1)
		B.box(F, S, "EndWall", -1.6, 1.6, -0.04, ROOF + 0.96, w0, OUT + 2, P.shell)
		B.box(F, C, "EndBase", -s * 1.6, -s * 1.95, -0.04, 0.7, w0 + 3, D1, P.pier2, nil, G)
		B.box(F, C, "EndBand", -s * 1.6, -s * 1.75, 5.5, 7.2, w0 + 3, D1, P.band, nil, G)
		B.box(F, C, "EndUpBase", -s * 1.6, -s * 1.9, UY, UY + 1.1, R.reach(e, A + T) + 0.4, MEZ - 0.7, P.pier, nil, G)
		B.box(F, C, "EndUpCornice", -s * 1.6, -s * 2.4, ROOF - 1, ROOF, w0 + 3, D1, P.cream, nil, G)
		local pm, bh = (MEZ + D0) / 2 + 2, 9
		local yb = UY + 6.2
		B.box(F, C, "LiveBoardFrame", -s * 1.6, -s * 2.05, yb - bh / 2 - 0.45, yb + bh / 2 + 0.45, pm - 8.45, pm + 8.45, P.pier2, nil, G)
		B.box(F, C, "LiveBoardPanel", -s * 2.05, -s * 2.15, yb - bh / 2, yb + bh / 2, pm - 8, pm + 8, P.plate, nil, G)
		local spot = B.box(F, C, "BoardSpot", -s * 2.15, -s * 2.25, yb - bh / 2, yb + bh / 2, pm - 8, pm + 8, P.plate, nil, { ghost = true, tr = 1 })
		spot:SetAttribute("Board", if s < 0 then "duels" else "party")
		spot:SetAttribute("Facing", F.RightVector * -s) -- (the way the board's face looks, into the hall)
		Tags:AddTag(spot, "BoardSpot")
		-- (19 Nov, play-party-ranked: its ranked leaderboard is a screen any prompt with RankedBoard opens; nothing draws a
		-- board in the world yet. so each frame opens it: the west one the duels table, the east one the party table)
		local pr = Instance.new("ProximityPrompt")
		pr.Name = "BoardPrompt"; pr.ActionText = "Leaderboard"; pr.ObjectText = if s < 0 then "Duels" else "Parties"
		pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
		pr.MaxActivationDistance = 14; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
		pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
		pr:SetAttribute("RankedBoard", if s < 0 then "duels" else "party")
		pr.Parent = spot
		B.box(F, C, "LiveBoardCove", -s * 2.05, -s * 2.3, yb + bh / 2 + 0.45, yb + bh / 2 + 0.6, pm - 8.2, pm + 8.2, P.strip, Neon, G)
	end
end
