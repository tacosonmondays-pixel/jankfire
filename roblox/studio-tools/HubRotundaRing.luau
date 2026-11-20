--!nocheck
-- THE RING: the centre redone (20 Nov 2026). The owner on the live hub: "It just feels so empty, but I dont want random
-- stuff thrown in! also a balcanoy facing inwrod and outward and the arches are now so far back? should we redo the
-- center area entirely again?"; main: one design for the round hall, the pads and the gallery; the lounge, the VIP
-- room, the armory, the gym's corridor, the gym and the locker room stay. So, built by structure and not by props:
-- * ONE ROUND HALL, its middle R.RING.C north of the old one and its wall R.RING.R round it: its south edge is where the
--   old round room's was, so the plaza's three arches (the old sides 6, 7 and 8, kept as they were) still open off it;
--   the gym's corridor and the armory meet its wall further round.
-- * TEN PAD ARCHES straight off the hall, round its north (R.RING_PADS: from the west end 1V1, 1V1V1, 2V2, 3V3, 4V4,
--   then back down the east, the two 4V4s meeting at the top). each pad lies in a lit alcove behind its arch, turned so
--   its length runs away from the hall (that is how ten of them fit round the curve at their size: the arc is what
--   limits it, not the depth); the alcove widens behind the arch; the pad's sign and its live count over the arch.
-- * EVERY WAY OUT AN ARCH IN THE SAME RING: the gym, the armory, the plaza's three, the jump pads' bays, the trophy case
--   and a bundle plinth in blind arches; a column between every two, carrying the gallery.
-- * ONE GALLERY, FACING IN: a ring round the hall over the arches (over the alcoves' fronts round the north, a balcony
--   on the wall round the south), a glass rail, built-in seats along it; the jump pads throw you up to it. its back is a
--   finished wall; nothing of it looks out.
-- * ONE CENTREPIECE THAT DOES SOMETHING: a round console on a raised plinth in the middle, its rim showing how many wait
--   for each mode (the client writes the numbers), YOUR loadout as a hologram over it; built-in benches round it facing
--   in; rings in the floor that answer the dome's.
-- * a coffered dome on a ring beam, one big oculus over the console. lights even: no glare strips.
-- called by HubRotunda.build with its helpers (B) when R.LAYOUT is "ring" (R.PARTS)
return function(B, R)
	local P, G = B.P, B.G
	local K = R.RING
	local RC, RR, WT, RB = K.C, K.R, K.WT, K.RB
	local GS, GY, GI, GD, TOP, DOME, OC = K.GS, K.GY, K.GI, K.GD, K.TOP, K.DOME, K.OC
	local A, T, N = R.A, R.WALL, R.N
	local step = 360 / N
	local Neon = Enum.Material.Neon
	local S, C = "Shell", "Scenery"
	local Tags = game:GetService("CollectionService")
	local ACCENT = P.doorGlow or P.glow
	local DECK = 0.45
	local AL = K.ALPHA
	local Fc0 = B.fr(0) * CFrame.new(0, 0, -RC) -- the hall's middle, facing north
	local function fc(b) return Fc0 * CFrame.Angles(0, -math.rad(b), 0) end
	local function ch(r, deg) return 2 * r * math.tan(math.rad(math.abs(deg)) / 2) end
	local function wrap(b) return ((b + 180) % 360) - 180 end
	-- (the old axes: the point t along the old bearing b, x to its right; where a line x right of the axis meets a circle
	-- of radius r round the hall's middle; the bearing of a point from the hall's middle)
	local function cross(b, r, x)
		local sb, cb = math.sin(math.rad(b)), math.cos(math.rad(b))
		return RC * cb + math.sqrt(math.max(RC * RC * cb * cb - x * x - 2 * x * RC * sb - RC * RC + r * r, 0))
	end
	local function fromC(b, t, x)
		local rb = math.rad(b)
		local px = t * math.sin(rb) + x * math.cos(rb)
		local pz = t * math.cos(rb) - x * math.sin(rb)
		return math.deg(math.atan2(px, pz - RC))
	end
	local CW = math.deg(2.6 / RR) -- (a column's width, as an angle at the wall)
	-- the gym's corridor (old side 4) and the armory (old side 10): where their insides meet the wall
	local gB, aB = 4 * step, 10 * step
	local function opening(b, hw)
		local p, q = fromC(b, cross(b, RR, -hw), -hw), fromC(b, cross(b, RR, hw), hw)
		return math.min(p, q), math.max(p, q)
	end
	local gLo, gHi = opening(gB, 5) -- (the way through, at the wall's face)
	local aLo, aHi = opening(aB, 5)
	local gO0, gO1 = opening(gB, 8.2) -- (the corridors' outer faces: the columns stand just outside them)
	local aO0, aO1 = opening(aB, 8.2)
	local gAx, aAx = fromC(gB, cross(gB, RR, 0), 0), fromC(aB, cross(aB, RR, 0), 0) -- (where their axes meet the wall)
	-- the plaza's three arches stay on the old round room's faces 6, 7, 8: their ends, seen from the hall's middle
	local rcA = A / math.cos(math.pi / N)
	local S6 = fromC(5.5 * step, rcA, 0) -- (the corner between the old sides 5 and 6)
	local S8 = fromC(8.5 * step, rcA, 0) -- (8 and 9: negative, west)
	R.RING_AT = { gLo = gLo, gHi = gHi, aLo = aLo, aHi = aHi, S6 = S6, S8 = S8 } -- (for R.check)

	-- ---- the bays round the ring, west to east the long way round the north: each { b0, b1, kind }
	local bays = {}
	table.insert(bays, { S8, aO0 - CW / 2, "bundle" })
	table.insert(bays, { aO0 - CW / 2, aO1 + CW / 2, "armory" })
	table.insert(bays, { aO1 + CW / 2, -AL, "jump" })
	for _, q in R.RING_PADS do table.insert(bays, { q.b0, q.b1, "pad", q }) end
	table.insert(bays, { AL, gO0 - CW / 2, "jump" })
	table.insert(bays, { gO0 - CW / 2, gO1 + CW / 2, "gym" })
	table.insert(bays, { gO1 + CW / 2, S6, "trophy" })
	local function mid(by) return (by[1] + by[2]) / 2 end
	local function span(by) return by[2] - by[1] end
	local function inPads(b) return math.abs(b) <= AL + 0.01 end

	-- ---- the floor: one disc, a ring of slices out under the wall (into the alcoves round the north, to the threshold at
	-- the gym's and the armory's arches), and rings in it that answer the dome's: each a cream disc under a floor disc a
	-- little smaller, every disc its own height (no two faces in one plane)
	B.cyl(Fc0, S, "HallFloor", 0, -2, 0, 0, 2 * (RR - 1), P.floor)
	for k = 0, 71 do
		local b = -180 + (k + 0.5) * 5
		local rO = RR + WT + 0.6
		if inPads(b) then rO = RB + 1
		elseif (b > gLo - 1 and b < gHi + 1) or (b > aLo - 1 and b < aHi + 1) then rO = RR + 1.5 end
		B.box(fc(b), S, "HallFloorRing", -ch(rO, 5) / 2 - 0.12, ch(rO, 5) / 2 + 0.12, -2, 0, RR - 2, rO, P.floor)
	end
	local FY = 0
	for i, r in { 31.4, 24.4, 19.4 } do
		-- (tops 0.05 apart and off the floor's: 0.02 flickered from across the hall; bottoms deep in the floor, each its own
		-- and off the plinth's and the jump glow's)
		local t = 0.05 * (2 * i - 1)
		B.cyl(Fc0, C, "FloorRing", 0, -0.25 - 0.07 * (2 * i - 1), t, 0, 2 * r, P.cream, nil, G)
		B.cyl(Fc0, C, "FloorRingFill", 0, -0.25 - 0.07 * (2 * i), t + 0.05, 0, 2 * (r - 0.6), P.floor, nil, G)
		FY = t + 0.05 -- (the floor's top inside the inner ring)
	end

	-- ---- the centrepiece: a raised round plinth, the console on it (its rim: one panel per mode, the count under the
	-- mode's name; HubConsole.client writes the numbers), the lens on its top and YOUR loadout as a hologram over it
	-- (HubHolo.client draws it), built-in benches round it facing in
	B.cyl(Fc0, S, "Plinth", 0, -0.1, 0.65, 0, 2 * 12.5, P.pier)
	B.cyl(Fc0, S, "PlinthTop", 0, 0.65, 1.2, 0, 2 * 11, P.cream)
	B.cyl(Fc0, C, "PlinthFloor", 0, 1.1, 1.26, 0, 2 * 10.6, P.floor2, nil, G)
	-- (main, staging 1: "make the console clearly the hero ... its count rim readable from the spawn arch": taller, its
	-- panels bigger, the count as big as the mode's name, one panel square to the lobby's arch; the benches lower)
	local CT = 7 -- (the console's top)
	B.cyl(Fc0, S, "Console", 0, 1.2, CT, 0, 2 * 6.6, P.pier2)
	B.cyl(Fc0, C, "ConsoleBand", 0, 1.15, 2.4, 0, 2 * 6.75, P.pier, nil, G) -- (its foot off the console's)
	B.cyl(Fc0, C, "ConsoleCap", 0, CT, CT + 0.5, 0, 2 * 7.0, P.cream, nil, G)
	B.cyl(Fc0, C, "ConsoleLens", 0, CT + 0.45, CT + 0.7, 0, 2 * 2.2, P.glow, Neon, G)
	for i, md in R.MODES do
		local b = 180 + (i - 1) * 72
		local p = B.text(fc(b), "ConsoleRim_" .. md.id, { { md.title, P.word, "B", 0.46 }, { "0 WAITING", P.glow, "B", 0.4 } }, 7.2, 3.4, 0, 4.6, 6.7, 180, { flush = true, thick = 0.14, plate = "20232e", pps = 40 })
		p:SetAttribute("Mode", md.id)
		Tags:AddTag(p, "HubConsoleRim")
	end
	B.holo(Fc0, "HoloLoadout", "loadout", 0, CT + 3.6, 0, 3.6, 3, { base = 3.6 - 0.7 })
	local up = B.lamp(Fc0, 0, CT + 1, 0, 12, 1.2, P.light, { spot = true, angle = 30 }); up:FindFirstChildOfClass("SpotLight").Face = Enum.NormalId.Top
	for q = 0, 3 do
		for k = 0, 2 do
			local b = q * 90 + 18 + k * 27
			local F = fc(b)
			local hw = ch(16.2, 24) / 2
			B.box(F, S, "BenchBase", -hw, hw, FY - 0.02, 1.1, 15.6, 17.6, P.pier)
			B.box(F, C, "BenchSeat", -hw + 0.1, hw - 0.1, 1.1, 1.6, 15.7, 17.05, P.creamHi, Enum.Material.Fabric, G)
			B.box(F, S, "BenchBack", -hw, hw, 1.1, 2.5, 17.05, 17.6, P.pier2)
			B.box(F, C, "BenchCap", -hw - 0.05, hw + 0.05, 2.5, 2.75, 16.95, 17.7, P.cream, nil, G)
		end
	end

	-- ---- an arch: a round head (its crown at `crown`, as wide as 2 * ow) in a band of wall d0..d1 deep, the wall round it
	-- from xa to xb (the bay's width) up to `top`; cream stones round the head on the hall's face
	local function arch(F, ow, crown, top, xa, xb, d0, d1, hex)
		local spr = crown - ow
		B.box(F, S, "ArchWall", xa, -ow, -0.1, top, d0, d1, hex)
		B.box(F, S, "ArchWall", ow, xb, -0.1, top, d0, d1, hex)
		B.box(F, S, "ArchWall", -ow, ow, crown, top, d0, d1, hex)
		for _, s in { -1, 1 } do
			for _, sl in { { 0, 0.35 }, { 0.35, 0.6 }, { 0.6, 0.78 }, { 0.78, 0.9 }, { 0.9, 1 } } do
				local a, bb = sl[1] * ow, sl[2] * ow
				local yb = spr + math.sqrt(math.max(ow * ow - bb * bb, 0))
				if yb < crown then B.box(F, C, "ArchSpandrel", s * a, s * bb, yb, crown, d0 + 0.05, d1 - 0.05, hex, nil, G) end
			end
		end
		local rI, rO = ow, ow + 0.9
		for k = 1, 9 do
			local a = math.rad((k - 0.5) * 20)
			local cx, cy = (rI + rO) / 2 * math.cos(a), spr + (rI + rO) / 2 * math.sin(a)
			local hl = (rI + rO) / 2 * math.tan(math.rad(10)) + 0.03
			local tx, ty = -math.sin(a) * hl, math.cos(a) * hl
			local o = (k % 2) * 0.04
			B.spar(F, C, "ArchStone", d0 - 0.3 - o, d0, rO - rI, cx - tx, cy - ty, cx + tx, cy + ty, P.cream, nil, G) -- (in front of the wall, not into it: the keystone's underside lay in the wall's)
		end
		for _, s in { -1, 1 } do B.box(F, C, "ArchJamb", s * (ow - 0.06), s * (ow + 0.5), -0.04, spr + 0.1, d0 - 0.3, d0 + 0.3, P.cream, nil, G) end -- (a hair proud of the opening's sides)
	end

	-- ---- round the ring: each bay's wall, its arch or what stands in it
	for _, by in bays do
		local b = mid(by)
		local F = fc(b)
		local half = ch(RR + WT, span(by)) / 2 + 0.25
		local kind = by[3]
		if kind == "pad" then
			local q = by[4]
			-- the arch (narrower than the pad behind it), the wall up to the gallery's floor
			local ow = ch(RR, span(by)) / 2 - 1.75
			arch(F, ow, K.CROWN, GS, -half, half, RR, RR + WT, P.shell)
			-- the pad, turned so its length runs out from the hall, on a low deck with a lit lip, in its alcove
			local md = table.clone(R.MODES[q.mode])
			md.name, md.bank, md.w, md.dp = q.name, q.bank or "lifts", q.w, q.dp
			local rM = RR + WT + 1 + q.w / 2
			local pad = B.pad(F * CFrame.new(0, 0, -rM) * CFrame.Angles(0, math.pi / 2, 0), md, 0, DECK, 0)
			pad:SetAttribute("Bearing", q.b); pad:SetAttribute("Sight", false); pad:SetAttribute("Ring", true)
			-- (play-party-ranked: QUICK JOIN stands you on a plate facing -its LookVector, "into the hub", and Matches reads a
			-- side in its own frame. turned with the pad, a plate would face along the curve: so each plate is turned back a
			-- quarter, its width and depth swapped (the same footprint), its LookVector out to the alcove's back)
			for _, sp in pad:GetChildren() do
				if sp:IsA("BasePart") and sp.Name:sub(1, 4) == "Side" then
					local sz = sp.Size
					sp.CFrame = sp.CFrame * CFrame.Angles(0, -math.pi / 2, 0)
					sp.Size = Vector3.new(sz.Z, sz.Y, sz.X)
				end
			end
			local dw = ch(RR + WT, span(by)) / 2 - 0.9
			B.box(F, S, "Deck", -dw, dw, -0.04, DECK, RR + WT + 0.3, RB - 0.3, P.deck)
			B.box(F, C, "DeckNosing", -dw - 0.03, dw + 0.03, DECK - 0.16, DECK + 0.02, RR + WT + 0.25, RR + WT + 0.55, ACCENT, Neon, G)
			-- its sign over the arch (the mode, its kind, who waits: Matches writes Status and Sub)
			local bw = math.min(ch(RR, span(by)) - 3.6, 11)
			local bh = bw * 0.5
			B.board(pad, F, md, bw, bh, 0, K.CROWN + 0.55 + bh / 2, RR - 0.25, 0, { thick = 0.4 })
			-- the alcove: its lowered ceiling (pale, a downlight in it and a spot on the pad), its back wall
			local lw = ch(RB + 0.5, span(by)) / 2 + 0.25
			B.box(F, S, "AlcoveLid", -lw, lw, K.ALID, K.ALID + 0.4, RR + WT - 0.2, RB + 0.5, P.creamHi)
			-- (main, staging 1: "near-black around a very bright pink pad": the walls the hall's mid-tone, one soft light)
			B.box(F, S, "AlcoveBack", -lw, lw, -0.04, K.ALID + 0.46, RB, RB + 1.6, P.pier2) -- (its top off the lid's)
			B.panel(F, 0, K.ALID, rM, 2.2, 2.2)
			B.lamp(F, 0, K.ALID - 1.2, rM, 20, 0.75, P.light)
		elseif kind == "gym" or kind == "armory" then
			-- the way through: the corridor's walls (HubRotundaRooms) start in this wall; here the wall over the way and the
			-- jambs out to the bay's edges where the corridor's walls don't reach
			local ob = if kind == "gym" then gB else aB
			local p1, p2 = fromC(ob, cross(ob, RR, -8.2), -8.2), fromC(ob, cross(ob, RR, 8.2), 8.2)
			local w0, w1 = math.min(p1, p2), math.max(p1, p2)
			local xw0, xw1 = RR * math.tan(math.rad(w0 - b)), RR * math.tan(math.rad(w1 - b)) -- (the corridor's outer faces, across this bay)
			if xw0 > -half then B.box(F, S, "HallWall", -half, xw0 + 0.3, -0.1, TOP, RR, RR + WT, P.shell) end
			if xw1 < half then B.box(F, S, "HallWall", xw1 - 0.3, half, -0.1, TOP, RR, RR + WT, P.shell) end
			B.box(F, S, "HallWall", -half, half, 11.06, TOP, RR, RR + WT, P.shell) -- (its underside off the corridor's lid's and the room's wall's, both 11)
			local ow = ch(RR, (if kind == "gym" then gHi - gLo else aHi - aLo)) / 2 + 0.2 -- (round the way itself, centred where its axis meets the wall)
			local Fa = fc(if kind == "gym" then gAx else aAx)
			for k = 1, 9 do
				local a = math.rad((k - 0.5) * 20)
				local rI, rO = ow, ow + 0.9
				local spr = 11 - ow
				local cx, cy = (rI + rO) / 2 * math.cos(a), spr + (rI + rO) / 2 * math.sin(a)
				local hl = (rI + rO) / 2 * math.tan(math.rad(10)) + 0.03
				local tx, ty = -math.sin(a) * hl, math.cos(a) * hl
				B.spar(Fa, C, "ArchStone", RR - 0.3 - (k % 2) * 0.04, RR + 0.3, rO - rI, cx - tx, cy - ty, cx + tx, cy + ty, P.cream, nil, G)
			end
			local word = if kind == "gym" then { "Way_gym", "GYM", P.pale } else { "Way_training", "TRAINING", P.train or P.pale }
			B.text(F, word[1], { { word[2], word[3], "B", 1 } }, if #word[2] > 6 then 9 else 6, 1.8, 0, 13.6, RR - 0.08, 0, { flush = true, thick = 0.25, pps = 50 })
		else
			-- a solid bay up to the ring beam: the jump pads', the trophy case's, the bundle plinth's
			B.box(F, S, "HallWall", -half, half, -0.1, TOP, RR, RR + WT, P.shell)
			B.box(F, C, "Base", -half + 0.6, half - 0.6, 0, 0.7, RR - 0.35, RR, P.pier, nil, G)
			if kind == "trophy" or kind == "bundle" then
				-- over the gallery, the two ranked boards' places (play-party-ranked's: a BoardSpot, Board "duels" west and
				-- "party" east, Facing into the hall, a BoardPrompt with RankedBoard that opens the table): a big lit frame on
				-- the wall, seen across the hall and reached from the gallery
				local bw = math.min(ch(RR, span(by)) - 2.6, 15)
				local yb, bh = GY + 5.6, 8
				B.box(F, C, "LiveBoardFrame", -bw / 2 - 0.45, bw / 2 + 0.45, yb - bh / 2 - 0.45, yb + bh / 2 + 0.45, RR - 0.45, RR, P.pier2, nil, G)
				B.box(F, C, "LiveBoardPanel", -bw / 2, bw / 2, yb - bh / 2, yb + bh / 2, RR - 0.55, RR - 0.45, P.plate, nil, G)
				local spot = B.box(F, C, "BoardSpot", -bw / 2, bw / 2, yb - bh / 2, yb + bh / 2, RR - 0.65, RR - 0.55, P.plate, nil, { ghost = true, tr = 1 })
				local board = if kind == "bundle" then "duels" else "party"
				spot:SetAttribute("Board", board)
				spot:SetAttribute("Facing", -F.LookVector) -- (into the hall)
				Tags:AddTag(spot, "BoardSpot")
				local pr = Instance.new("ProximityPrompt")
				pr.Name = "BoardPrompt"; pr.ActionText = "Leaderboard"; pr.ObjectText = if board == "duels" then "Duels" else "Parties"
				pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
				pr.MaxActivationDistance = 14; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
				pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
				pr:SetAttribute("RankedBoard", board)
				pr.Parent = spot
				B.box(F, C, "LiveBoardCove", -bw / 2 - 0.2, bw / 2 + 0.2, yb + bh / 2 + 0.45, yb + bh / 2 + 0.7, RR - 0.7, RR, P.cream, nil, G)
			end
		end
	end

	-- the alcoves' side walls: one on every edge between two pads' bays, and the two ends
	do
		local edges = {}
		for _, q in R.RING_PADS do table.insert(edges, q.b0) end
		table.insert(edges, R.RING_PADS[#R.RING_PADS].b1)
		for _, e in edges do
			B.box(fc(e), S, "AlcoveFin", -0.8, 0.8, -0.04, K.ALID + 0.2, RR + WT - 0.4, RB + 0.2, P.pier2)
		end
	end

	-- ---- the plaza's three arches on the old round room's faces 6, 7 and 8, as they were (the lounge's side of them is
	-- HubRotundaRooms'), their walls now up to the ring beam; the old piers at their corners (the lounge puts a pilaster
	-- over each); the lobby's word over the middle one
	for _, side in { 6, 7, 8 } do
		local F = B.side(side)
		local wo = B.wid(A + T) / 2 + 0.05
		-- (from the lobby's parapet up, 27.48, only the hall's side of the wall: the parapet is its lobby side, and the two
		-- faces in one plane flickered)
		B.box(F, S, "Lintel", -wo, wo, 12, 27.48, A, A + T, P.shell)
		B.box(F, S, "LintelTop", -wo, wo, 27.48, TOP, A, A + T - 1.2, P.shell)
		B.paint(F, "Threshold", -5.4, 5.4, 0, A - 0.3, A + T + 0.3, P.pier, 0.08)
		if side == 7 then B.text(F, "Way_lounge", { { if R.LOUNGE_STYLE == "plaza" then "LOBBY" else "LOUNGE", P.pale, "B", 1 } }, 7, 1.8, 0, 13.6, A - 0.08, 0, { flush = true, thick = 0.25, pps = 50 }) end
	end
	local Kw = B.warp and B.warp.K
	for _, side in { 6, 7, 8 } do
		local F = B.side(side)
		if Kw then
			B.rigid(F, 0, A + T / 2, 0, function(Fl)
				local h = T / 2 * Kw
				local rI, SY = 4.8 * Kw, 6.6
				local rO = rI + 1.9
				local top = R.hmap(R.V3.H, 12)
				for k = 1, 24 do
					local a = math.rad((k - 0.5) * 7.5)
					local cx, cy = (rI + rO) / 2 * math.cos(a), SY + (rI + rO) / 2 * math.sin(a)
					local hl = (rI + rO) / 2 * math.tan(math.rad(3.75)) + 0.03
					local tx, ty = -math.sin(a) * hl, math.cos(a) * hl
					local o = (k % 2) * 0.04
					B.spar(Fl, C, "ArchStone", -h - 0.4 - o, h + 0.4 + o, rO - rI, cx - tx, cy - ty, cx + tx, cy + ty, P.pier, nil, G)
					local hr = rO + 0.28
					local hx, hy = hr * math.cos(a), SY + hr * math.sin(a)
					local hlh = hr * math.tan(math.rad(3.75)) + 0.03
					B.spar(Fl, C, "ArchHood", h, h + 0.75 + o, 0.56, hx + math.sin(a) * hlh, hy - math.cos(a) * hlh, hx - math.sin(a) * hlh, hy + math.cos(a) * hlh, P.creamHi, nil, G)
				end
				for _, s in { -1, 1 } do
					B.box(Fl, C, "ArchJamb", s * rI, s * (rO + 0.4), -0.04, SY + 0.05, -h - 0.4, h + 0.4, P.pier, nil, G)
					B.box(Fl, C, "ArchImpost", s * (rI - 0.3), s * (rO + 0.7), SY - 0.6, SY, h - 0.05, h + 0.65, P.cream, nil, G)
					for _, sl in { { 3.4, 4.3 }, { 4.3, 5.1 }, { 5.1, 5.9 }, { 5.9, 6.7 }, { 6.7, 7.5 }, { 7.5, rO + 0.35 } } do
						local yb = if sl[2] < rO then SY + math.sqrt(rO * rO - sl[2] * sl[2]) else SY
						if yb < top then
							B.box(Fl, C, "ArchSpandrel", s * sl[1], s * sl[2], yb, top, -h + 0.05, h - 0.05, P.shell, nil, G)
							if R.LOUNGE_STYLE == "plaza" then B.box(Fl, C, "ArchSkin", s * sl[1], s * sl[2], yb, top - 0.03, h - 0.05, h + 0.03, P.bay, nil, G) end
						end
					end
				end
				B.box(Fl, C, "ArchKeystone", -0.75, 0.75, SY + rI - 0.25, SY + rO + 0.95, h, h + 0.9, P.cream, nil, G)
			end)
		end
		B.solid("ArchBoxL", Vector3.new(1.6, 12, T), F * CFrame.new(-5.6, 6, -(A + T / 2)))
		B.solid("ArchBoxR", Vector3.new(1.6, 12, T), F * CFrame.new(5.6, 6, -(A + T / 2)))
	end
	for _, i in { 5, 6, 7, 8 } do
		local F = B.fr((i + 0.5) * step)
		local pier = B.put(F, "hb_pier", "Pier", 0, 0, rcA + 1.3, 0, { stretch = Vector3.new(2.9 / 6.2, 27.5 / 48, 4.4 / 3.6), solid = Vector3.new(2.9, 12, 4.2),
			color = { ["2e3140"] = P.pier, a4aab8 = P.pier2, ["5b6478"] = P.pier } })
		if pier then for _, q in pier:GetDescendants() do if q:IsA("BasePart") and q.Material == Neon then q.Material = Enum.Material.SmoothPlastic; q.Color = Color3.fromHex(P.cream) end end end
	end

	-- ---- the columns: one between every two bays round the ring, floor to the gallery's underside, carrying it; over the
	-- gallery a slimmer pilaster up to the ring beam (free-standing round the north, on the wall round the south)
	local cols = {}
	for _, by in bays do table.insert(cols, by[1]) end
	table.insert(cols, bays[#bays][2])
	for _, cb in cols do
		if math.abs(math.abs(cb) - S6) < 0.5 then continue end -- (the old piers stand there)
		local F = fc(cb)
		local col = B.put(F, "hb_pier", "Column", 0, 0, RR - 1.2, 0, { stretch = Vector3.new(2.9 / 6.2, GS / 48, 2.6 / 3.6), solid = Vector3.new(2.6, 12, 2.4),
			color = { ["2e3140"] = P.pier, a4aab8 = P.cream, ["5b6478"] = P.pier } })
		if col then -- (no glare strips, main: the kit's lit strip a plain cream inlay here)
			for _, q in col:GetDescendants() do
				if q:IsA("BasePart") and q.Material == Neon then q.Material = Enum.Material.SmoothPlastic; q.Color = Color3.fromHex(P.cream) end
			end
		end
		B.box(F, C, "ColumnCap", -1.7, 1.7, GS - 0.7, GS - 0.12, RR - 2.7, RR + 0.2, P.cream, nil, G) -- (its top off the soffit's)
		B.box(F, C, "UpperPilaster", -0.75, 0.75, GY, TOP - 1.2, RR - 0.75, RR + 0.35, P.pier2, nil, G)
	end

	-- ---- the gallery: a ring of slab round the hall at GY (deep over the alcoves' fronts round the north, a balcony on the
	-- wall round the south), a pale soffit under its overhang with downlights in it, a cream fascia on its edge, a glass
	-- rail (open over the jump pads: the way up and back down), built-in seats along the rail round the north, a finished
	-- wall at its back, its own ceiling, lamps
	local jumpE, jumpW = { AL, gO0 - CW / 2 }, { aO1 + CW / 2, -AL }
	local function overJump(b) return (b > jumpE[1] + 0.5 and b < jumpE[2] - 0.5) or (b > jumpW[1] + 0.5 and b < jumpW[2] - 0.5) end
	for k = 0, 71 do
		local b = -180 + (k + 0.5) * 5
		local F = fc(b)
		local rO = if inPads(b) then RR + GD + 0.3 else RR + 0.3
		local w = ch(rO, 5) / 2 + 0.12
		B.box(F, S, "GallerySlab", -w, w, GS, GY - 0.1, RR - GI, rO, P.shell2)
		B.box(F, C, "GalleryFloor", -w, w, GY - 0.1, GY, RR - GI + 0.1, rO - 0.1, P.floor, nil, G)
		local wi = ch(RR - GI, 5) / 2 + 0.06
		B.box(F, C, "GalleryFascia", -wi, wi, GS - 0.45, GY + 0.15, RR - GI - 0.32, RR - GI, P.cream, nil, G)
		B.box(F, C, "GallerySoffit", -wi, wi, GS - 0.25, GS - 0.05, RR - GI, RR, P.creamHi, nil, G)
		if not overJump(b) then
			B.box(F, S, "GalleryGlass", -wi, wi, GY, GY + 3.2, RR - GI + 0.2, RR - GI + 0.34, "d8eef2", Enum.Material.Glass, { tr = 0.72 })
			B.box(F, C, "GalleryRail", -wi - 0.04, wi + 0.04, GY + 3.2, GY + 3.5, RR - GI + 0.08, RR - GI + 0.46, P.cream, nil, G)
		end
		B.box(F, C, "RingBeam", -ch(RR + 0.6, 5) / 2 - 0.1, ch(RR + 0.6, 5) / 2 + 0.1, TOP - 1.2, TOP + 0.3, RR - 0.9, RR + 0.6, P.cream, nil, G)
		if inPads(b) then
			-- round the north: the gallery's back wall (finished, nothing looks out), its ceiling
			local wb = ch(RR + GD + 2, 5) / 2 + 0.12
			B.box(F, S, "GalleryWall", -wb, wb, GS + 0.06, TOP, RR + GD, RR + GD + 2, P.bay) -- (its foot in the slab, off the slab's underside)
			B.box(F, C, "GalleryDado", -wb + 0.1, wb - 0.1, GY, GY + 4, RR + GD - 0.2, RR + GD, P.brown, nil, G)
			B.box(F, C, "GalleryBand", -wb + 0.1, wb - 0.1, GY + 4, GY + 4.4, RR + GD - 0.3, RR + GD, P.cream, nil, G)
			B.box(F, S, "GalleryCeiling", -wb, wb, TOP, TOP + 0.8, RR - 0.6, RR + GD + 2, P.creamHi)
		end
	end
	for _, s in { -1, 1 } do -- (the north part's two ends)
		B.box(fc(s * AL), S, "GalleryEnd", -0.8, 0.8, GS + 0.06, TOP, RR + WT - 0.2, RR + GD + 2, P.bay) -- (its foot in the slab, off the slab's underside)
	end
	-- soffit downlights, one a bay; the gallery's own lamps over the seats round the north; the seats
	for _, by in bays do
		local b = mid(by)
		B.panel(fc(b), 0, GS - 0.25, RR - GI / 2, 1.6, 1.6)
		B.lamp(fc(b), 0, GS - 1.2, RR - GI / 2, 18, 0.5)
		if by[3] == "pad" then
			local F = fc(b)
			local hw = ch(RR - GI + 1.5, span(by)) / 2 - 1.3
			B.box(F, S, "GallerySeat", -hw, hw, GY - 0.02, GY + 1.3, RR - GI + 0.6, RR - GI + 2.1, P.pier)
			B.box(F, C, "GallerySeatTop", -hw + 0.1, hw - 0.1, GY + 1.3, GY + 1.75, RR - GI + 0.65, RR - GI + 2.05, P.creamHi, Enum.Material.Fabric, G)
			B.box(F, S, "GallerySeatBack", -hw, hw, GY - 0.02, GY + 2.7, RR - GI + 2.1, RR - GI + 2.5, P.pier2)
			B.panel(F, 0, TOP, RR + GD / 2 + 1, 2, 2)
			B.lamp(F, 0, TOP - 1.2, RR + GD / 2 + 1, 18, 0.5)
		end
	end

	-- ---- the dome: coffered (panels between radial ribs, two ring ribs) on the ring beam, the oculus at its top over the
	-- console, its light straight down on it, a few lamps round its foot
	for k = 0, 35 do
		local b = k * 10
		B.bar(fc(b), S, "DomePanel", 0, ch(RR + 0.8, 10) + 0.3, 1, OC + 0.6, DOME + 0.2, RR + 0.8, TOP + 0.2, P.dome)
		B.bar(fc(b + 5), C, "DomeRib", 0, 1, 1, OC + 0.6, DOME - 0.6, RR + 0.2, TOP - 0.6, P.cream, nil, G)
		for _, f in { 1 / 3, 2 / 3 } do
			local r, yy = RR + (OC - RR) * f, TOP + (DOME - TOP) * f
			B.box(fc(b), C, "DomeRing", -ch(r, 10) / 2 - 0.08, ch(r, 10) / 2 + 0.08, yy - 1.3, yy - 0.5, r - 0.55, r + 0.55, P.cream, nil, G)
		end
		B.box(fc(b), C, "OculusCurb", -ch(OC + 0.9, 10) / 2 - 0.06, ch(OC + 0.9, 10) / 2 + 0.06, DOME - 0.5, DOME + 0.9, OC - 0.2, OC + 0.9, P.cream, nil, G)
	end
	B.cyl(Fc0, C, "Oculus", 0, DOME + 0.7, DOME + 0.84, 0, 2 * OC, "f6f2e8", Neon, G) -- (its top under the curb's)
	B.cyl(Fc0, S, "DomeCap", 0, DOME + 0.9, DOME + 1.9, 0, 2 * (OC + 1.4), P.dome)
	B.lamp(Fc0, 0, DOME - 1, 0, 80, 1, P.light, { spot = true, angle = 70, shadows = true })
	for k = 0, 7 do B.lamp(fc(k * 45 + 22.5), 0, TOP - 2.5, RR - 6, 36, 0.45) end
	-- (a secret: a small duck sits on the ring beam over the north column. only the gallery sees it)
	B.put(fc(0), "pj_duck", "CrownDuck", 0, TOP + 0.3, RR - 0.15, 0, { scale = 2.6, raw = true })

	-- ---- the jump pads, in their own bays between the pads and the gym's and armory's arches: a ring of the accent round
	-- each, breathing; they throw you onto the gallery. the boards on the bays' walls: how to play, and where things are
	for _, jb in { { jumpE, "BoardHow" }, { jumpW, "BoardNotice" } } do
		local b = (jb[1][1] + jb[1][2]) / 2
		local F = fc(b)
		B.jump(F, 0, 0, RR - 8, 0, K.JUMP)
		local ring = B.cyl(F, C, "JumpGlow", 0, -0.07, 0.17, RR - 8, 2 * R.JUMP_GLOW, ACCENT, Neon, { ghost = true, tr = 0.2 }) -- (its top clear of the outer floor ring's)
		local gl = Instance.new("PointLight"); gl.Color = Color3.fromHex(ACCENT); gl.Range = 8; gl.Brightness = 1.2; gl.Shadows = false; gl.Parent = ring
		ring:SetAttribute("BreatheLo", 0.1); ring:SetAttribute("BreatheHi", 0.5); ring:SetAttribute("BreathePeriod", 2.6)
		Tags:AddTag(ring, "HubBreathe")
		local bw = math.min(ch(RR, math.abs(jb[1][2] - jb[1][1])) - 0.8, 9.2)
		local lines = if jb[2] == "BoardHow"
			then { { "HOW TO PLAY", P.pale, "B", 0.28 }, { "1   STEP ON A PAD IN YOUR TEAM'S COLOUR", "d8dbe2", "S", 0.18 }, { "2   WHEN THE PAD IS FULL, VOTE FOR A MAP", "d8dbe2", "S", 0.18 }, { "3   FIRST TO FIVE ROUNDS WINS", "d8dbe2", "S", 0.18 }, { "4   STEP OFF TO LEAVE THE QUEUE", "d8dbe2", "S", 0.18 } }
			else { { "PADS   ·   IN THE ARCHES ROUND THE HALL", "d8dbe2", "S", 0.3 }, { "TRAINING   ·   THROUGH THE ARMORY", "d8dbe2", "S", 0.3 }, { "LOADOUT   ·   PRESS L ANYWHERE", "d8dbe2", "S", 0.3 } }
		B.text(F, jb[2], lines, bw, bw * 0.46, 0, 7.6, RR - 0.62, 0, { flush = true, thick = 0.3, pps = 40 })
	end

	-- ---- the trophy case (east) and a bundle plinth (west) in blind arches: as on the old sides 5 and 9, against the wall
	local function showFrame(F, plate, l1, l2)
		B.box(F, C, "ShowBoard", -4.2, 4.2, 0.7, 9.6, RR - 0.8, RR - 0.24, P.plate, nil, G)
		for _, s in { -1, 1 } do B.box(F, C, "ShowJamb", s * 4.2, s * 4.75, -0.04, 10.06, RR - 1.05, RR - 0.2, P.cream, nil, G) end
		B.box(F, C, "ShowHead", -4.75, 4.75, 9.6, 10.1, RR - 1.35, RR - 0.2, P.cream, nil, G)
		B.box(F, C, "ShowSill", -4.2, 4.2, 0.35, 0.7, RR - 1, RR - 0.26, P.pier, nil, G)
		if plate then B.text(F, plate, { { l1, P.glow, "S", 0.32 }, { l2, P.pale, "B", 0.58 } }, 6.4, 1.4, 0, 8.45, RR - 0.8, 0, { flush = true, thick = 0.08, pps = 40 }) end
	end
	do
		local F = fc(mid(bays[#bays]))
		showFrame(F, nil)
		local case = Instance.new("Model"); case.Name = "TrophyCase"
		local d0, d1 = RR - 3.6, RR - 0.8
		local parts = {
			B.box(F, C, "CaseBase", -4.1, 4.1, 0, 1, d0, d1, P.pier2),
			B.box(F, C, "CaseTop", -4.1, 4.1, 6.9, 7.4, d0, d1, P.pier2),
			B.box(F, C, "CaseGlass", -3.9, 3.9, 1, 6.9, d0, d0 + 0.1, "dfe8ec", Enum.Material.Glass, { tr = 0.86, noShadow = true }),
			B.box(F, C, "Podium1", -1.35, 1.35, 1, 2.4, d0 + 0.3, d1, P.cream, nil, G),
			B.box(F, C, "Podium2", -3.9, -1.35, 1, 1.8, d0 + 0.3, d1, P.creamHi, nil, G),
			B.box(F, C, "Podium3", 1.35, 3.9, 1, 1.4, d0 + 0.3, d1, P.creamHi, nil, G),
		}
		for _, s in { -1, 1 } do table.insert(parts, B.box(F, C, "CasePost", s * 3.9, s * 4.1, 1, 6.9, d0, d1, P.pier2)) end
		for _, p in parts do p.Parent = case end
		case.Parent = B.root.Scenery
		local dm = (d0 + 0.3 + d1) / 2 - 0.1
		for _, t in { { "DuckGold", 0, 2.4, 1.5, "d6b04e" }, { "DuckSilver", -2.62, 1.8, 1.2, "c5c9cf" }, { "DuckBronze", 2.62, 1.4, 1.05, "b47c4c" } } do
			B.put(F, "rk_duckTrophy", t[1], t[2], t[3], dm, 0, { scale = t[4], color = { b0b4ba = t[5] } })
		end
		B.lamp(F, 0, 6.6, dm, 10, 1, "fff1dc", { spot = true, angle = 110 })
	end
	do
		local F = fc(mid(bays[1]))
		local dP = RR - 3.4
		showFrame(F, "ShowName3", "BUNDLE", "COMING SOON")
		B.cyl(F, C, "PlinthFoot", 0, 0, 0.35, dP, 4.6, P.pier)
		B.cyl(F, C, "BundlePlinth", 0, 0.35, 1.5, dP, 4, P.cream)
		B.cyl(F, C, "PlinthTopDisc", 0, 1.4, 1.53, dP, 3.6, P.floor2, nil, G)
		B.cyl(F, C, "PlinthRing", 0, 1.36, 1.57, dP, 3, P.glow, Neon, G)
		B.cyl(F, C, "PlinthInner", 0, 1.32, 1.61, dP, 2.6, P.floor2, nil, G)
		B.cyl(F, C, "PlinthLens", 0, 1.28, 1.65, dP, 0.9, P.glow, Neon, G)
		B.holo(F, "HoloBundle3", "bundle", 0, 5.2, dP, 2.5, 2.8, { slot = 3, base = 5.2 - 1.65, prompt = "View bundle" })
	end

	-- ---- a regular (R.NPCS): Frisk1636, the ranked guy, walks the gallery round the north behind the seats, pausing to
	-- look down into the hall
	for k = 1, 7 do
		local b = -36 + (k - 1) * 12
		local F = fc(b)
		if k == 1 then B.npc(F, "Frisk1636", 0, GY + 0.04, RR + 4.5, 180) end
		if k % 2 == 1 then B.npcPoint(F, "Frisk1636", k, "stop", "stand", 0, GY + 0.04, RR + 4.5, 180, { pause = { 8, 16 } })
		else B.npcPoint(F, "Frisk1636", k, "via", "stand", 0, GY + 0.04, RR + 4.5, 180) end
	end
end
