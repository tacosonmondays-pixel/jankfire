--!nocheck
-- THE ROTUNDA, part 1: the round room. a stepped platform in the middle with a glowing ring in its top (you spawn inside
-- the ring), fourteen sides with a chunky pier at every corner, a ring balcony 14 up with a rail (two gaps over the
-- jump pads: the way up and the way down; doorways off it over the four outer lifts lead into the second floor), a
-- gallery over it (the game's name over the middle lift, banners on the
-- closed sides), a ribbed dome with a round skylight, and under the dome a lit ring with a hologram turning in it:
-- your own loadout, nine studs across, rising from a lens in the platform (HubHolo.client draws it). the eight ways out
-- get one word each on the balcony's edge; the closed sides: the jump pads and their boards (3 and 11) and the showroom (5 and 9: either side of the lounge's three arches), the trophy case and a plinth with
-- a bundle from the shop floating over it in front of a dark board under a lit cove. since 18 Nov the south sides 6, 7
-- and 8 are three round arches onto the spawn lounge (HubRotundaRooms), and the way up is lit: the jump pads glow and
-- breathe under a soft column of light, the four doorways into the second floor have lit frames. called by
-- HubRotunda.build with its helpers (B)
return function(B, R)
	local P, G = B.P, B.G
	local N, A, T, RY, RIN = R.N, R.A, R.WALL, R.RING_Y, R.RING_IN
	local step = 360 / N
	local Neon, Wood = Enum.Material.Neon, Enum.Material.Wood
	local S, C = "Shell", "Scenery"
	local Tags = game:GetService("CollectionService")
	local F0 = B.fr(0)
	local wid = B.wid
	local rc = A / math.cos(math.pi / N) -- how far out a corner is
	local mode = {}
	for _, md in R.MODES do mode[md.side] = md end
	-- what a way out is called and the colour of its word and floor line
	local WAY = { gym = { "gym", "GYM", P.pale, P.cream }, lounge = { "lounge", if R.LOUNGE_STYLE == "plaza" then "LOBBY" else "LOUNGE", P.pale, P.cream }, armory = { "training", "TRAINING", P.train, "9dbb93" },
		arcade = { nil, nil, P.pale, P.cream } } -- (the arches either side of the lounge's: no word of their own)
	local ACCENT = P.doorGlow or P.glow -- (the building's one accent: the way to go)

	-- ---- the floor, the platform, the lines
	B.cyl(F0, S, "Floor", 0, -2, 0, 0, 2 * (A + 3), P.floor)
	B.cyl(F0, C, "RingLine", 0, -0.04, 0.05, 0, 2 * 14.6, P.cream, nil, G) -- (every disc of a stack has its own bottom, sunk, 0.04 apart: the flicker finder counts faces within 0.02)
	B.cyl(F0, C, "RingFill", 0, -0.08, 0.09, 0, 2 * 14.1, P.floor, nil, G)
	B.cyl(F0, S, "DaisFoot", 0, -0.12, 0.6, 0, 2 * 13.4, P.pier)
	B.cyl(F0, S, "Dais", 0, 0.6, 1.2, 0, 2 * 12.6, P.cream)
	B.cyl(F0, C, "DaisTop", 0, 1.0, 1.24, 0, 2 * 12, P.floor2, nil, G)
	B.cyl(F0, C, "SpawnRing", 0, 1.04, 1.28, 0, 2 * 11.6, P.glow, Neon, G)
	B.cyl(F0, C, "DaisInner", 0, 1.08, 1.32, 0, 2 * 11, P.floor2, nil, G)
	-- the hologram's projector (owner, 16 Nov: "can it be even lower? like I don't have to look up to see it?"): a low drum
	-- with the lens in its top, in a ring rail that keeps you out of the hologram
	B.cyl(F0, S, "Pedestal", 0, 1.28, 2.2, 0, 4.4, P.cream)
	B.cyl(F0, C, "PedestalBand", 0, 1.3, 1.62, 0, 4.48, P.pier2, nil, G)
	B.cyl(F0, C, "LensRim", 0, 2.16, 2.4, 0, 3.4, P.pier, nil, G)
	B.cyl(F0, C, "Lens", 0, 2.2, 2.44, 0, 2.2, P.glow, Neon, G)
	local HR = 4 -- (the rail's radius: outside the hologram's 3.6)
	for k = 0, 15 do
		local Fk = B.fr(k * 22.5)
		local half = HR * math.tan(math.rad(11.25)) + 0.12
		B.box(Fk, C, "HoloRail", -half, half, 2.42, 2.7, HR - 0.15, HR + 0.15, P.creamHi)
		if k % 2 == 0 then B.cyl(Fk, C, "HoloRailPost", 0, 1.3, 2.42, HR, 0.34, P.pier2) end
	end
	-- (you appeared here, on the platform south of the projector, until 18 Nov; now in the lounge, HubRotundaRooms. the
	-- check still frames every lift from here, R.PLATFORM_LOOK: where you come out onto the platform)

	-- ---- the fourteen sides
	for i = 0, N - 1 do
		local F = B.side(i)
		local kind = R.OPEN[i]
		local wo = wid(A + T) / 2 + 0.05
		local wi = wid(A) / 2
		local wf = wid(RIN) / 2
		if kind then
			if R.UP_DOORS[i] then -- (a doorway off the balcony into the second floor: its sill just under the floor's finish)
				B.box(F, S, "Lintel", -wo, wo, 12, R.UP_Y - 0.06, A, A + T, P.shell)
				for _, s in { -1, 1 } do B.box(F, S, "Lintel", s * 4.6, s * wo, R.UP_Y - 0.06, 27.45, A, A + T, P.shell) end
				B.box(F, S, "Lintel", -4.6, 4.6, R.UP_Y + 8.8, 27.45, A, A + T, P.shell)
			elseif i == R.EGG_SIDE then -- (18 Nov: the hub egg's opening over the west arch: R.EGG_NICHE)
				local N = R.EGG_NICHE
				B.box(F, S, "Lintel", -wo, wo, 12, N[2], A, A + T, P.shell)
				for _, s in { -1, 1 } do B.box(F, S, "Lintel", s * N[1], s * wo, N[2], N[3], A, A + T, P.shell) end
				B.box(F, S, "Lintel", -wo, wo, N[3], 27.45, A, A + T, P.shell)
			else
				B.box(F, S, "Lintel", -wo, wo, 12, 27.45, A, A + T, P.shell) -- (tops under the piers', bottoms under the floor: no shared planes)
			end
			B.paint(F, "Threshold", -5.4, 5.4, 0, A - 0.3, A + T + 0.3, P.pier, 0.08)
			-- its word on the balcony's edge. (no floor lines any more: the owner, 16 Nov, "can you get rid of the lines leading
			-- to the pads": the five lifts are framed by their own piers and read on their own; the rooms' lines went with them)
			local id, word, hex
			if kind == "lift" then id, word, hex = mode[i].id, mode[i].title, P.word
			else id, word, hex = WAY[kind][1], WAY[kind][2], WAY[kind][3] end
			if kind == "lift" then -- (18 Nov, main: "the five lift bays should read as hotel lifts, with framed doors and a lit header over each": a pale frame inside the opening, a warm lit header over it)
				for _, s in { -1, 1 } do B.box(F, C, "LiftJamb", s * 4.85, s * 5.2, -0.04, 10.7, A - 0.2, A + 0.3, P.creamHi, nil, G) end -- (against the piers: the ways in and the sight lines to the pads stay as wide)
				B.box(F, C, "LiftHead", -5.05, 5.05, 10.7, 11.3, A - 0.5, A + 0.35, P.creamHi, nil, G)
				B.box(F, C, "LiftHeader", -3.4, 3.4, 11.35, 11.85, A - 0.38, A - 0.2, "e6c99a", Neon, G)
			end
			if P.doorGlow then -- (the glow palette: each way out lit along its threshold in its own colour, a lift also under its lintel)
				B.box(F, C, "DoorGlow", -4.9, 4.9, 0, 0.15, A - 0.55, A - 0.25, if kind == "lift" then P.doorGlow else hex, Neon, G)
			end
			if word then B.text(F, "Way_" .. id, { { word, hex, "B", 1 } }, if #word > 6 then 9 else 7, 1.9, 0, 13, RIN - 0.08, 0, { flush = true, thick = 0.25, pps = 50 }) end
		else
			B.box(F, S, "Wall", -wo, wo, -0.1, 27.45, A, A + T, P.shell)
			B.box(F, C, "Base", -5.3, 5.3, 0, 0.7, A - 0.35, A, P.pier, nil, G)
			B.box(F, C, "Dado", -5.3, 5.3, 0.7, 5, A - 0.22, A, P.wood, Wood, G)
			B.box(F, C, "Ledge", -5.3, 5.3, 5, 5.5, A - 0.6, A, P.cream, nil, G)
			B.box(F, C, "Band", -5.3, 5.3, 5.5, 7.2, A - 0.12, A, P.band, nil, G)
			B.bar(F, C, "Slope", 0, 10.6, 0.5, A - 1.7, 12, A, 10.3, P.shell2, nil, G)
			B.panel(F, 0, 12, 25.1, 5, 2)
			B.lamp(F, 0, 10.8, 25, 15, 0.55)
		end
		-- the ring balcony: its slab, its floor, and its rail (none over a jump pad, sides 3 and 11: the way up, and the way
		-- back down from the second floor)
		B.box(F, S, "Ring", -wi - 0.05, wi + 0.05, 12, RY, RIN, A, P.cream)
		B.box(F, C, "RingFloor", -wi, wi, RY, RY + 0.04, RIN + 0.9, A - 0.05, P.floor2, nil, G) -- (its end off the slab's outer face: the flicker finder, 18 Nov)
		if i == 3 or i == 11 then
			B.paint(F, "GapMark", -wf, wf, RY, RIN, RIN + 0.9, P.ray, 0.02)
		else
			B.put(F, "hb_rail", "Rail", 0, RY, RIN + 0.45, 0, { stretch = Vector3.new(wid(RIN + 0.4) / 9.5, 1, 1), solid = true,
				color = { ["2e3140"] = P.cream, c4c8d4 = P.creamHi, ["5b6478"] = P.cream, ["17141f"] = P.accent } })
		end
		-- the gallery: a lit panel in a dark frame, a cornice with a slope under it
		if R.UP_DOORS[i] then
			-- the doorway into the second floor: a pale frame round it on the room's side, the dark foot either side of it
			for _, s in { -1, 1 } do
				B.box(F, C, "GalleryBase", s * 5.2, s * (wi - 0.05), RY, RY + 0.6, A - 0.3, A, P.pier, nil, G)
				B.box(F, C, "UpperJamb", s * 4.6, s * 5.2, RY + 0.04, R.UP_Y + 9.4, A - 0.35, A, P.creamHi, nil, G)
			end
			B.box(F, C, "UpperHead", -5.2, 5.2, R.UP_Y + 8.8, R.UP_Y + 9.4, A - 0.35, A, P.creamHi, nil, G)
			-- (18 Nov, the owner: "how do we make it more obvious that there are pads on second floor": a lit line of the accent
			-- round the opening, on the frame's face, and a light just inside that washes the hall, seen from the ground floor)
			for _, s in { -1, 1 } do B.box(F, C, "UpperGlow", s * 4.68, s * 5.12, RY + 0.1, R.UP_Y + 8.95, A - 0.42, A - 0.35, ACCENT, Neon, G) end
			B.box(F, C, "UpperGlowHead", -5.12, 5.12, R.UP_Y + 8.95, R.UP_Y + 9.3, A - 0.42, A - 0.35, ACCENT, Neon, G)
			B.lamp(F, 0, R.UP_Y + 6, A + T + 2.5, 16, 1.1, ACCENT)
		else
			B.box(F, C, "GalleryBase", -wi + 0.05, wi - 0.05, RY, RY + 0.6, A - 0.3, A, P.pier, nil, G)
		end
		if i == 0 then
			B.text(F, "GalleryName", { { "JANKFIRE", P.word, "B", 1 } }, 10.6, 3.4, 0, 21.8, A - 0.3, 0, { flush = true, thick = 0.4, pps = 40 }) -- (high enough to clear the rail, seen from the platform)
		elseif i == R.EGG_SIDE then
			-- (18 Nov: the hub egg's hiding place. the main session gave training-v2 a hub egg, "hidden somewhere in Hub v3 that
			-- takes some exploring": this side's gallery window is a real opening, dark, in the same frame as the others; a
			-- hop up from the balcony (about 3 studs in Hub v3) and you are in a little closed room on the lounge's roof. the
			-- egg itself is training-v2's, in its own folder Map.Hub.HubEgg: nothing here builds or checks it)
			local N = R.EGG_NICHE
			for _, s in { -1, 1 } do B.box(F, C, "WindowFrame", s * N[1], s * (N[1] + 0.6), N[2] - 0.2, N[3] + 0.6, A - 0.4, A, P.pier, nil, G) end
			B.box(F, C, "WindowFrame", -N[1], N[1], N[3], N[3] + 0.6, A - 0.4, A, P.pier, nil, G)
			B.box(F, C, "WindowFrame", -N[1], N[1], N[2] - 0.2, N[2], A - 0.4, A, P.pier, nil, G)
			-- (18 Nov, the owner: "fix the hole where the jankfire npc is, it opens when you put his code in". the opening is
			-- shut for everyone by a finished panel in the wall's cream, flush with the wall's face inside its frame, solid;
			-- LoreLife.client hides it and turns its collision off, on that player's screen only, once they have entered the
			-- code. its NAME is the contract (EggNookDoor, anywhere under Map.Hub); the room behind it is untouched)
			local door = B.box(F, S, "EggNookDoor", -N[1], N[1], N[2], N[3], A, A + 0.5, P.cream)
			door:SetAttribute("EggNookDoor", true)
			game:GetService("CollectionService"):AddTag(door, "EggNookDoor")
			local FY, TOPY, D1 = R.LOUNGE_H + 1, N[3] + 1.1, A + T + 6 -- (its floor: the top of the lounge's lid; in the plaza a bay window's floor, HubRotundaRooms)
			local NW = if R.LOUNGE_STYLE == "plaza" then "958d80" else P.shell2 -- (the plaza: the bay window's body in the hotel's stone)
			for _, s in { -1, 1 } do B.box(F, S, "NicheWall", s * (N[1] + 0.9), s * (N[1] + 1.3), FY, TOPY, A + T, D1, NW) end
			B.box(F, S, "NicheWall", -(N[1] + 1.3), N[1] + 1.3, FY, TOPY, D1, D1 + 0.4, NW)
			B.box(F, S, "NicheLid", -(N[1] + 1.3), N[1] + 1.3, TOPY, TOPY + 0.4, A + T, D1 + 0.4, NW)
		elseif kind and not R.UP_DOORS[i] then
			B.box(F, C, "WindowFrame", -2.3, 2.3, 16.8, 23.4, A - 0.4, A, P.pier, nil, G)
			B.box(F, C, "Window", -1.7, 1.7, 17.4, 22.8, A - 0.52, A - 0.4, P.dim, Neon, G)
		elseif not R.UP_DOORS[i] and i ~= 3 and i ~= 11 then -- (18 Nov: no banner over a doorway into the second floor: it hung in the opening; none over the jump pads: the UPSTAIRS boards hang there, HubRotundaLifts)
			-- (a banner: the one soft thing that hangs in the room)
			B.box(F, C, "BannerRod", -2.6, 2.6, 23.5, 24, A - 0.9, A - 0.3, P.pier, nil, G)
			B.box(F, C, "Banner", -2.2, 2.2, 16.4, 23.5, A - 0.7, A - 0.55, P.band, nil, G)
			B.box(F, C, "BannerStripe", -2.2, 2.2, 17.6, 18.5, A - 0.74, A - 0.6, P.creamHi, nil, G)
			B.box(F, C, "BannerStripe", -2.2, 2.2, 19.1, 19.4, A - 0.74, A - 0.6, P.creamHi, nil, G)
		end
		B.box(F, C, "Cornice", -wi, wi, 26, 27.5, A - 1.2, A, P.cream, nil, G)
		B.bar(F, C, "CorniceSlope", 0, 2 * wi - 2.4, 0.5, A - 1.2, 26, A, 24.7, P.shell2, nil, G)
		-- the dome over it, and the skylight's curb
		B.bar(F, S, "DomePanel", 0, wid(A + 1.2) + 0.3, 1, 7.4, 39.9, A + 1.2, 27.4, P.dome)
		B.box(F, C, "Curb", -wid(8.6) / 2, wid(8.6) / 2, 38.8, 40.2, 7, 8.6, P.cream, nil, G)
		-- the hanging ring round the showpiece
		B.box(F, C, "Crown", -wid(10.4) / 2, wid(10.4) / 2, 21.4, 22.9, 9.2, 10.4, P.cream, nil, G)
		B.box(F, C, "CrownGlow", -wid(9.8) / 2 + 0.3, wid(9.8) / 2 - 0.3, 21.25, 21.4, 9.5, 10.1, P.halo or P.strip, Neon, G)
	end

	-- ---- a pier at every corner, floor to cornice, with a rib of the dome over it
	for i = 0, N - 1 do
		local F = B.fr((i + 0.5) * step)
		B.put(F, "hb_pier", "Pier", 0, 0, rc + 1.3, 0, { stretch = Vector3.new(2.9 / 6.2, 27.5 / 48, 4.4 / 3.6), solid = Vector3.new(2.9, 12, 4.2),
			color = { ["2e3140"] = P.pier, a4aab8 = P.pier2, ["5b6478"] = P.pier } })
		B.lamp(F, 0, 6, rc - 2.4, 10, 0.35)
		B.bar(F, C, "Rib", 0, 1.1, 1, 7.7, 39.2, 28.9, 27.3, P.cream, nil, G)
		if i >= 11 or i <= 2 then B.box(F, C, "PierBackLight", -0.3, 0.3, 2.6, 9.6, rc + 3.5, rc + 3.62, P.strip, Neon, G) end
	end

	-- ---- the dome's top, its light ring, and the lamps that light the room
	B.cyl(F0, C, "Skylight", 0, 40, 40.3, 0, 15.2, P.sky, Neon, G)
	B.cyl(F0, S, "DomeCap", 0, 40.3, 41.3, 0, 19, P.dome)
	B.put(F0, "bc_halo", "DomeRing", 0, 35.6, 0, 0, { seat = "centre", scale = 1.25, color = { ["37d6ff"] = P.strip, ff4fd9 = P.cream, ffe14d = P.cream } })
	B.lamp(F0, 0, 39.4, 0, 60, 0.8, P.light, { spot = true, angle = 100 })
	for k = 0, 3 do B.lamp(B.fr(45 + 90 * k), 0, 24, 15, 28, 0.5) end

	-- ---- the centrepiece: YOUR loadout as a hologram (owner, 16 Nov: "can the center gun thingy cycle your loadout but
	-- hologram style?"), over the platform under the ring that hangs from the dome on four spokes, rising from the lens
	-- in the platform. primary, secondary, melee, utility in turn, each in your wrap with your hat (HubHolo.client draws
	-- it on each player's own screen; here only its place). (first 13.4, then 13.9 up inside the ring; lowered to 9.5, then 8.2; now 6: a standing player's eye)
	B.cyl(F0, C, "Rod", 0, 22.4, 40, 0, 1.2, P.pier, nil, G)
	for k = 0, 3 do B.box(B.fr(45 + 90 * k), C, "Spoke", -0.5, 0.5, 21.6, 22.4, 0.6, 9.4, P.cream, nil, G) end
	-- (lowered on 16 Nov, the owner: "can the hologram in the hub be lowered down": its middle 9.5 up, just over the heads
	-- of players on the platform, at eye level from across the room, instead of up in the ring. it is see-through and has
	-- no collision, so R.check no longer counts it as a wall in the spawn's view or a thing in the spawn's keep-clear room)
	B.holo(F0, "HoloLoadout", "loadout", 0, 6, 0, 3.6, 3, { base = 6 - 2.44 })
	local up = B.lamp(F0, 0, 2.8, 0, 12, 1.4, P.light, { spot = true, angle = 30 }); up:FindFirstChildOfClass("SpotLight").Face = Enum.NormalId.Top
	B.lamp(F0, 0, 15.6, 0, 26, 1, P.light, { spot = true, angle = 110, shadows = true })
	-- (a secret: a small duck sits on top of the ring. only the balcony sees it)
	B.put(B.side(7), "pj_duck", "CrownDuck", 0, 22.9, 9.8, 0, { scale = 2.6, raw = true })

	-- ---- the doors' own shapes
	-- the lounge: a round arch of dark stones (it springs 6 up; 4.9 in radius); since 18 Nov three in a row, sides 6, 7, 8
	-- (18 Nov, the owner from the lounge: "can you fix the back side of this to make it look presentable". in Hub v3 the
	-- nine big stones went through the warp, which stretches heights over 9.5, and came out as odd pointed facets with
	-- holes beside them. so in Hub v3 each arch is made in world studs (B.rigid, its place warped, its parts not): 24
	-- small stones in a true half circle as wide as the way through (the collision boxes' faces), jambs under it, the
	-- spandrels filled up to the lintel, and on the lounge's side a cream hood round it, a keystone and imposts; the
	-- lounge also puts a clean pilaster over each of the round room's piers there (HubRotundaRooms). Hub v2 keeps the
	-- nine stones)
	local Kw = B.warp and B.warp.K
	for _, side in { 6, 7, 8 } do
		local F = B.side(side)
		if Kw then
			B.rigid(F, 0, A + T / 2, 0, function(Fl)
				local h = T / 2 * Kw -- (the wall's faces, either side of Fl's middle; d > 0 the lounge's side)
				local rI, SY = 4.8 * Kw, 6.6 -- (its inner radius: the collision boxes' inner faces; where it springs)
				local rO = rI + 1.9
				local top = R.hmap(R.V3.H, 12) -- (the lintel's underside)
				local hl = (rI + rO) / 2 * math.tan(math.rad(3.75)) + 0.03
				for k = 1, 24 do
					local a = math.rad((k - 0.5) * 7.5)
					local cx, cy = (rI + rO) / 2 * math.cos(a), SY + (rI + rO) / 2 * math.sin(a)
					local tx, ty = -math.sin(a) * hl, math.cos(a) * hl
					local o = (k % 2) * 0.04 -- (every other one a hair prouder: no two faces in one plane)
					B.spar(Fl, C, "ArchStone", -h - 0.4 - o, h + 0.4 + o, rO - rI, cx - tx, cy - ty, cx + tx, cy + ty, P.pier, nil, G)
					local hr = rO + 0.28 -- (the lounge's side: a cream hood round it)
					local hx, hy = hr * math.cos(a), SY + hr * math.sin(a)
					local hlh = hr * math.tan(math.rad(3.75)) + 0.03
					B.spar(Fl, C, "ArchHood", h, h + 0.75 + o, 0.56, hx + math.sin(a) * hlh, hy - math.cos(a) * hlh, hx - math.sin(a) * hlh, hy + math.cos(a) * hlh, P.creamHi, nil, G)
				end
				for _, s in { -1, 1 } do
					B.box(Fl, C, "ArchJamb", s * rI, s * (rO + 0.4), -0.04, SY + 0.05, -h - 0.4, h + 0.4, P.pier, nil, G)
					B.box(Fl, C, "ArchImpost", s * (rI - 0.3), s * (rO + 0.7), SY - 0.6, SY, h - 0.05, h + 0.65, P.cream, nil, G)
					-- the spandrel up to the lintel, in slices whose stepped bottoms the stones hide
					for _, sl in { { 3.4, 4.3 }, { 4.3, 5.1 }, { 5.1, 5.9 }, { 5.9, 6.7 }, { 6.7, 7.5 }, { 7.5, rO + 0.35 } } do
						local yb = if sl[2] < rO then SY + math.sqrt(rO * rO - sl[2] * sl[2]) else SY
						if yb < top then
							B.box(Fl, C, "ArchSpandrel", s * sl[1], s * sl[2], yb, top, -h + 0.05, h - 0.05, P.shell, nil, G)
							-- (the plaza: the lounge side's face in the hotel's stone, the round room's side as it was)
							if R.LOUNGE_STYLE == "plaza" then B.box(Fl, C, "ArchSkin", s * sl[1], s * sl[2], yb, top - 0.03, h - 0.05, h + 0.03, "a59d90", nil, G) end
						end
					end
				end
				B.box(Fl, C, "ArchKeystone", -0.75, 0.75, SY + rI - 0.25, SY + rO + 0.95, h, h + 0.9, P.cream, nil, G)
			end)
		else
			for k = 1, 9 do
				local a = math.rad((k - 0.5) * 20)
				local cx, cy = 6.5 * math.cos(a), 6 + 6.5 * math.sin(a)
				local tx, ty = -math.sin(a) * 1.5, math.cos(a) * 1.5
				B.spar(F, C, "ArchStone", A - 0.3, A + T + 0.1, 3.2, cx - tx, cy - ty, cx + tx, cy + ty, P.pier, nil, G)
			end
		end
		B.solid("ArchBoxL", Vector3.new(1.6, 12, T), F * CFrame.new(-5.6, 6, -(A + T / 2)))
		B.solid("ArchBoxR", Vector3.new(1.6, 12, T), F * CFrame.new(5.6, 6, -(A + T / 2)))
	end
	-- the armory: a hatch with its top corners cut
	do
		local F = B.side(10)
		for _, s in { -1, 1 } do
			B.spar(F, C, "HatchCut", A - 0.3, A + T + 0.1, 3, s * 6.4, 9.1, s * 2, 13.5, P.pier, nil, G)
		end
		B.box(F, C, "HatchHead", -3, 3, 11.4, 12, A - 0.3, A + T + 0.1, P.pier, nil, G)
	end
	-- the gym: a pale portal, deep, with its top corners cut, under a dark canopy with a light in it and the name on its
	-- front (round 1's judge: "a narrow plain rectangle with a thin frame")
	do
		local F = B.side(4)
		for _, s in { -1, 1 } do
			B.box(F, C, "PortalJamb", s * 4.5, s * 5.45, -0.04, 9.4, A - 0.5, A + T + 0.2, P.creamHi, nil, G) -- (just past the threshold's end, not on it)
			B.spar(F, C, "PortalCut", A - 0.5, A + T + 0.2, 1.1, s * 5.4, 8.8, s * 3.2, 11.1, P.creamHi, nil, G)
		end
		B.box(F, C, "PortalHead", -3.4, 3.4, 10.5, 11.1, A - 0.5, A + T + 0.2, P.creamHi, nil, G)
		B.box(F, C, "Canopy", -5.6, 5.6, 11.1, 12, A - 2.8, A + 0.2, P.pier, nil, G)
		B.box(F, C, "CanopyLight", -4.2, 4.2, 10.98, 11.1, A - 2.2, A - 1.2, P.strip, Neon, G)
		B.lamp(F, 0, 10.4, A - 1.6, 12, 0.6)
	end

	-- ---- what stands in the closed bays
	-- sides 3 and 11: the jump pads up to the balcony (and from it, through the doorways over the outer lifts, the second
	-- floor), a board on the wall behind each
	for _, i in { 3, 11 } do
		local F = B.side(i)
		B.jump(F, 0, 0, 18.2, 0, Vector3.new(0, 58, 6.2)) -- (6.2 out: you land mid-balcony, by the doorway, not against the wall) -- (the pad's arrows point away from its front: at the balcony)
		-- (18 Nov, the way up made obvious: a ring of the accent round the pad with a light in it. HubLife.client breathes
		-- it, tag HubBreathe: see-through between BreatheLo and BreatheHi, BreathePeriod s a breath, the light with it. Its
		-- light column up past the balcony went the same day, the owner: "I dont like the pillar of light from the teleporter")
		local ring = B.cyl(F, C, "JumpGlow", 0, -0.07, 0.13, 18.2, 2 * R.JUMP_GLOW, ACCENT, Neon, { ghost = true, tr = 0.2 })
		local gl = Instance.new("PointLight"); gl.Color = Color3.fromHex(ACCENT); gl.Range = 12; gl.Brightness = 1.2; gl.Shadows = false; gl.Parent = ring
		for _, q in { { ring, 0.1, 0.5 } } do
			q[1]:SetAttribute("BreatheLo", q[2]); q[1]:SetAttribute("BreatheHi", q[3]); q[1]:SetAttribute("BreathePeriod", 2.6)
			Tags:AddTag(q[1], "HubBreathe")
		end
		local lines = if i == 3
			then { { "HOW TO PLAY", P.pale, "B", 0.28 }, { "1   STEP ON A PAD IN YOUR TEAM'S COLOUR", "d8dbe2", "S", 0.18 }, { "2   THE LIFT GOES UP WHEN THE PAD IS FULL", "d8dbe2", "S", 0.18 }, { "3   FIRST TO FIVE ROUNDS WINS", "d8dbe2", "S", 0.18 }, { "4   STEP OFF TO LEAVE THE QUEUE", "d8dbe2", "S", 0.18 } }
			else { { "MORE PADS   ·   UPSTAIRS", "d8dbe2", "S", 0.3 }, { "TRAINING   ·   THROUGH THE ARMORY", "d8dbe2", "S", 0.3 }, { "LOADOUT   ·   PRESS L ANYWHERE", "d8dbe2", "S", 0.3 } } -- (no title, no "holstered" line: the owner, 16 Nov, "I dont want unnecessary flavor text everywhere")
		B.text(F, if i == 3 then "BoardHow" else "BoardNotice", lines, 9.2, 4.2, 0, 8.1, A - 0.62, 0, { flush = true, thick = 0.3, pps = 40 })
	end
	-- a regular (R.NPCS; HubNPCs builds them at start): Frisk1636 on the balcony over the lifts, the ranked guy. he moves
	-- between four spots on the rail (by the piers between the doorways), pausing at each, looking down at the platform;
	-- a via halfway between each two keeps his walk on the curve of the balcony (a straight line cuts in toward the rail);
	-- 3 out from the rail: the rail's ends by the piers and the banners on the wall leave about 3.3 between them
	for k = 1, 7 do
		local b = (-1.5 + (k - 1) * 0.5) * step
		if k == 1 then B.npc(B.fr(b), "Frisk1636", 0, RY + 0.04, RIN + 3, 180) end
		if k % 2 == 1 then B.npcPoint(B.fr(b), "Frisk1636", k, "stop", "stand", 0, RY + 0.04, RIN + 3, 180, { pause = { 8, 16 } })
		else B.npcPoint(B.fr(b), "Frisk1636", k, "via", "stand", 0, RY + 0.04, RIN + 3, 180) end
	end
	-- ---- the showroom: sides 5 and 9 either side of the lounge's arches (until 18 Nov also 6 and 8; owner, 16 Nov: "we also need
	-- holograms like in rivals with bundle sets that float and people can look at and interact with"). on each a round
	-- plinth like a small copy of the platform, a bundle from the shop floating over it (HubHolo.client: one bundle a
	-- plinth, its pieces in turn, a card with what's in it when you walk up, E or a click opens the shop on it), behind it
	-- a dark board in a pale frame with a lit cove under its head and the bundle's name on a plate at the top. the same
	-- frame on side 5 holds the trophy case (below): four of a kind round the arch read as one feature (the shop's half of
	-- the room, the pads' half facing it), where four odd props read as clutter
	local function showFrame(F, plate, l1, l2) -- (plate nil: no name plate)
		B.box(F, C, "ShowBoard", -4.2, 4.2, 0.7, 9.6, A - 0.8, A - 0.24, P.plate, nil, G)
		for _, s in { -1, 1 } do B.box(F, C, "ShowJamb", s * 4.2, s * 4.75, -0.04, 10.06, A - 1.05, A - 0.2, P.cream, nil, G) end
		B.box(F, C, "ShowHead", -4.75, 4.75, 9.6, 10.1, A - 1.35, A - 0.2, P.cream, nil, G)
		B.box(F, C, "ShowCove", -4, 4, 9.46, 9.6, A - 1.25, A - 1, P.strip, Neon, G)
		B.box(F, C, "ShowSill", -4.2, 4.2, 0.35, 0.7, A - 1, A - 0.26, P.pier, nil, G)
		if plate then B.text(F, plate, { { l1, P.glow, "S", 0.32 }, { l2, P.pale, "B", 0.58 } }, 6.4, 1.4, 0, 8.45, A - 0.8, 0, { flush = true, thick = 0.08, pps = 40 }) end
	end
	-- side 5, by the duel hall's door: the trophy case, with rubber-duck trophies (owner, 16 Nov: "can the trophy case, can
	-- they be ducky trophies?"): a glass-fronted case on a plinth, a podium in it, the big gold duck on its top step in the
	-- middle, silver on the left, bronze on the right, each on a slate trophy base with a blank little plate (the kit's
	-- rk_duckTrophy), lit warm from inside. the case is one model so R.check's overlap test weighs the ducks against it
	do
		local F = B.side(5)
		showFrame(F, nil) -- (no plate: the owner wants no labels for things you can see)
		local case = Instance.new("Model"); case.Name = "TrophyCase"
		local d0, d1 = A - 3.6, A - 0.8 -- (the case's front and back)
		local parts = {
			B.box(F, C, "CaseBase", -4.1, 4.1, 0, 1, d0, d1, P.pier2),
			B.box(F, C, "CaseTop", -4.1, 4.1, 6.9, 7.4, d0, d1, P.pier2),
			B.box(F, C, "CaseGlow", -3.7, 3.7, 6.78, 6.9, d0 + 0.5, d0 + 0.8, P.bayWash or P.warm, Neon, G),
			B.box(F, C, "CaseGlass", -3.9, 3.9, 1, 6.9, d0, d0 + 0.1, "dfe8ec", Enum.Material.Glass, { tr = 0.86, noShadow = true }),
			B.box(F, C, "Podium1", -1.35, 1.35, 1, 2.4, d0 + 0.3, d1, P.cream, nil, G),
			B.box(F, C, "Podium2", -3.9, -1.35, 1, 1.8, d0 + 0.3, d1, P.creamHi, nil, G),
			B.box(F, C, "Podium3", 1.35, 3.9, 1, 1.4, d0 + 0.3, d1, P.creamHi, nil, G),
		}
		for _, s in { -1, 1 } do
			table.insert(parts, B.box(F, C, "CasePost", s * 3.9, s * 4.1, 1, 6.9, d0, d1, P.pier2))
		end
		for _, p in parts do p.Parent = case end
		case.Parent = B.root.Scenery
		local dm = (d0 + 0.3 + d1) / 2 - 0.1
		for _, t in { { "DuckGold", 0, 2.4, 1.5, "d6b04e" }, { "DuckSilver", -2.62, 1.8, 1.2, "c5c9cf" }, { "DuckBronze", 2.62, 1.4, 1.05, "b47c4c" } } do
			B.put(F, "rk_duckTrophy", t[1], t[2], t[3], dm, 0, { scale = t[4], color = { b0b4ba = t[5] } })
		end
		B.lamp(F, 0, 6.6, dm, 10, 1, "fff1dc", { spot = true, angle = 110 })
		B.lamp(F, 0, 9.2, A - 1.6, 11, 0.45, P.warm, { spot = true, angle = 70 })
	end
	-- side 9: a bundle plinth (slot 3; 1, 2 and 4 are in the lounge's showroom since 18 Nov: sides 6 and 8 are arches)
	for k, i in { [3] = 9 } do
		local F = B.side(i)
		local dP = A - 3.4 -- (the plinth's middle)
		showFrame(F, "ShowName" .. k, "BUNDLE", "COMING SOON")
		B.cyl(F, C, "PlinthFoot", 0, 0, 0.35, dP, 4.6, P.pier)
		B.cyl(F, C, "Plinth", 0, 0.35, 1.5, dP, 4, P.cream)
		B.cyl(F, C, "PlinthTop", 0, 1.4, 1.53, dP, 3.6, P.floor2, nil, G)
		B.cyl(F, C, "PlinthRing", 0, 1.36, 1.57, dP, 3, P.glow, Neon, G)
		B.cyl(F, C, "PlinthInner", 0, 1.32, 1.61, dP, 2.6, P.floor2, nil, G)
		B.cyl(F, C, "PlinthLens", 0, 1.28, 1.65, dP, 0.9, P.glow, Neon, G)
		B.holo(F, "HoloBundle" .. k, "bundle", 0, 5.2, dP, 2.5, 2.8, { slot = k, base = 5.2 - 1.65, prompt = "View bundle" })
		B.lamp(F, 0, 9.2, A - 1.6, 11, 0.45, P.warm, { spot = true, angle = 70 })
	end
end
