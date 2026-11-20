--!nonstrict
-- THREE CONCEPTS FOR THE WHOLE HUB (20 Nov 2026). The owner, on the ring hub: "redo hub I also dont like that entrance
-- to the gym", "Too empty", "I dont want random stuff thrown in", "I dont like the pads", "theyre just rectangles they
-- donbt fit the shape and the acrhces look ugly". The main session's brief: three genuinely different structures, each
-- keeping the 10 pads, the lounge (code panel, shop, tables), VIP, the armory with the training entrance, the gym with
-- 4 rings and its locker room, the live counts; the gym opening straight off the main space; full through purposeful
-- things (the games, the shop, the displays, the regulars, a big live screen) and layered architecture; one opening
-- language each; no cream round arches; pads shaped for where they sit.
--   A THE CONCOURSE: a long grand hall, the pads in column-and-beam bays down both sides under a mezzanine, the lounge
--     at the spawn end, the gym's full-width opening at the far end. Pads: PLAYER SPOTS across a low divider.
--   B THE ATRIUM: an octagonal three-level atrium round a hanging screen, the pads on the ground ring as raised
--     platforms shaped to their side, the lounge on the gallery above (looking down into the gym too), VIP at the top.
--     Openings: framed rectangular portals with a lit header. Pads: PLATFORMS with a filling rim light and a floating sign.
--   C THE SQUARE: a covered square round a screen tower, wings off each side through wide thin-framed openings: the
--     pads' gallery north, the gym east, the armory west, the lounge street south. Pads: GATES you step into.
-- Quick blockouts, not the real hub: built far off the map in workspace.HubConcepts (removed after the photos; never
-- saved). HC.build(name) -> { labels = { {text, x, z} }, shots = { {name, cam, look} } } in world studs.
local HC = {}
HC.SITES = { A = Vector3.new(3000, 240, -12000), B = Vector3.new(3600, 240, -12000), C = Vector3.new(4200, 240, -12000) }

local K = {
	floor = "5c616a", floor2 = "50555d", runner = "4a4644", wall = "6a727e", wall2 = "5c636f", col = "747c88", trim = "b3aea4",
	trim2 = "c4bfb5", ceil = "727a86", screen = "15181d", dark = "2a2d33", steel = "3a3f47", wood = "6b5646", carpet = "4f4846",
	carpet2 = "5a4f4a", sofa = "5e6470", glass = "a9bcc4", plant = "5f7a58", plant2 = "6a8562", soil = "3d3631", light = "f4f1ea",
	warm = "ffd7a0", pale = "e8ecef", amber = "e9a64a", gold = "c9a45a", plum = "4b4048", padBase = "4a4f57", gymFloor = "4c515a",
	gymWall = "c4c0b6", canvas = "d9d4c8", paving = "6b7078", cab = "2f333b", unlit = "3a3d44",
}
local TEAM = { "ff5ad2", "40d0ff", "e9a64a" } -- (the teams' colours: only as thin rims and lights)
local MODES = {
	{ id = "1v1", title = "1V1", n = 1, t = 2 }, { id = "1v1v1", title = "1V1V1", n = 1, t = 3 }, { id = "2v2", title = "2V2", n = 2, t = 2 },
	{ id = "3v3", title = "3V3", n = 3, t = 2 }, { id = "4v4", title = "4V4", n = 4, t = 2 },
}
local MAT = Enum.Material
local SP = MAT.SmoothPlastic
local O = CFrame.new()
local root: Folder = nil
local function c3(h) return Color3.fromHex(h) end

-- ------------------------------------------------------------------------------------------------ parts
local function mk(cls, name, cf, size, hex, mat, o)
	o = o or {}
	local p = Instance.new(cls)
	p.Name = name; p.Anchored = true; p.Size = size; p.CFrame = O * cf
	p.Color = c3(hex); p.Material = mat or SP
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	if o.tr then p.Transparency = o.tr end
	if o.shape then p.Shape = o.shape end
	if o.refl then p.Reflectance = o.refl end
	if o.noshadow then p.CastShadow = false end
	p.Parent = root
	return p
end
local function part(name, cf, size, hex, mat, o) return mk("Part", name, cf, size, hex, mat, o) end
-- a box in frame F: x0..x1, y0..y1, z0..z1
local function box(F, name, x0, x1, y0, y1, z0, z1, hex, mat, o)
	return part(name, F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
		Vector3.new(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(z1 - z0), 0.05)), hex, mat, o)
end
local function cyl(F, name, x, y0, y1, z, dia, hex, mat, o)
	o = o or {}; o.shape = Enum.PartType.Cylinder
	return part(name, F * CFrame.new(x, (y0 + y1) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), Vector3.new(math.max(y1 - y0, 0.05), dia, dia), hex, mat, o)
end
local function ball(F, name, x, y, z, dia, hex, mat, o)
	o = o or {}; o.shape = Enum.PartType.Ball
	return part(name, F * CFrame.new(x, y, z), Vector3.new(dia, dia, dia), hex, mat, o)
end
local function rod(F, name, a: Vector3, b: Vector3, dia, hex, mat, o) -- (not straight up)
	o = o or {}; o.shape = Enum.PartType.Cylinder
	local cf = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0)
	return part(name, F * cf, Vector3.new((b - a).Magnitude, dia, dia), hex, mat, o)
end
-- the triangle (xa, zin), (xa, zout), (xb, zout) in F, y0..y1 thick: a slanted side's fill (a WedgePart laid flat)
local function slant(F, name, xa, xb, zin, zout, y0, y1, hex, mat, o)
	local cf = F * CFrame.new((xa + xb) / 2, (y0 + y1) / 2, (zin + zout) / 2) * CFrame.Angles(0, math.pi, 0)
		* CFrame.Angles(0, 0, if xb < xa then -math.pi / 2 else math.pi / 2)
	return mk("WedgePart", name, cf, Vector3.new(y1 - y0, math.abs(xb - xa), math.abs(zout - zin)), hex, mat, o)
end
local function at(F, x, z, yaw, y) return F * CFrame.new(x, y or 0, z) * CFrame.Angles(0, math.rad(yaw or 0), 0) end
local function glow(p, range, bright, hex)
	local l = Instance.new("PointLight"); l.Range = range; l.Brightness = bright; l.Color = c3(hex or K.warm); l.Shadows = false; l.Parent = p
	return l
end
-- text on a part's face: lines { text, hex, height share, font }
local function text(p, face, lines, o)
	o = o or {}
	local g = Instance.new("SurfaceGui")
	g.Face = face; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = o.pps or 40
	g.LightInfluence = 0; g.Brightness = o.bright or 1.6; g.Parent = p
	local f = Instance.new("Frame"); f.Size = UDim2.fromScale(1, 1); f.BackgroundColor3 = c3(o.bg or K.screen)
	f.BackgroundTransparency = o.bgt or 1; f.BorderSizePixel = 0; f.Parent = g
	local lay = Instance.new("UIListLayout"); lay.FillDirection = Enum.FillDirection.Vertical
	lay.HorizontalAlignment = Enum.HorizontalAlignment.Center; lay.VerticalAlignment = Enum.VerticalAlignment.Center
	lay.SortOrder = Enum.SortOrder.LayoutOrder; lay.Parent = f
	for i, l in lines do
		local t = Instance.new("TextLabel")
		t.LayoutOrder = i; t.Size = UDim2.fromScale(0.94, l[3] or 0.4); t.BackgroundTransparency = 1
		t.Text = l[1]; t.TextColor3 = c3(l[2] or K.pale); t.Font = l[4] or Enum.Font.GothamBlack; t.TextScaled = true
		t.Parent = f
	end
	return g
end
local function panel(F, x, y, z, w, l, bright)
	local p = box(F, "LightPanel", x - w / 2, x + w / 2, y - 0.15, y, z - l / 2, z + l / 2, K.light, MAT.Neon, { noshadow = true })
	glow(p, 24, bright or 0.55, K.warm)
	return p
end

-- ------------------------------------------------------------------------------------------------ people
local SKIN = { "c69c7c", "8d5f45", "e0b896", "6e4a37", "b5876a", "d9a882" }
local SHIRT = { "6d7f8f", "8a6d5a", "5a6e5a", "7a5a5a", "565a72", "8c8478", "4f5f6a", "9a8064", "6a5a7a", "7d8a96" }
local pn = 0
-- a person: Fp at their feet, facing Fp's look; sit = on a seat 1.45 high under their hips (thighs forward)
local function person(Fp, sit, shirtHex)
	pn += 1
	local skin, shirt = SKIN[pn % #SKIN + 1], shirtHex or SHIRT[pn % #SHIRT + 1]
	local pants = ({ "33363d", "3f3a34", "2f3540", "45474d" })[pn % 4 + 1]
	if sit then
		box(Fp, "Person", -0.9, 0.9, 0, 1.45, -2.05, -1.45, pants)
		box(Fp, "Person", -0.9, 0.9, 1.45, 2.0, -2.05, 0.1, pants)
		box(Fp, "Person", -0.95, 0.95, 2.0, 3.95, -0.45, 0.45, shirt)
		for _, s in { -1, 1 } do box(Fp, "Person", s * 0.95, s * 1.45, 2.2, 3.9, -0.7, 0.3, shirt) end
		ball(Fp, "Person", 0, 4.6, 0, 1.3, skin)
	else
		for _, s in { -1, 1 } do box(Fp, "Person", s * 0.05, s * 0.93, 0, 2.0, -0.45, 0.45, pants) end
		box(Fp, "Person", -0.95, 0.95, 2.0, 4.0, -0.48, 0.48, shirt)
		for _, s in { -1, 1 } do box(Fp, "Person", s * 0.97, s * 1.47, 2.1, 3.95, -0.42, 0.42, shirt) end
		ball(Fp, "Person", 0, 4.7, 0, 1.3, skin)
	end
end
-- a regular (HubNPCs' people) in their own avatar, from the saved copies; a person in a gold shirt if there is none
local function regular(Fp, who)
	local src = game:GetService("ServerStorage"):FindFirstChild("JankfireNPCs")
	local m0 = src and src:FindFirstChild(who)
	if not (m0 and m0:IsA("Model")) then person(Fp, false, K.gold); return end
	local m = m0:Clone()
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false end
		if d:IsA("BaseScript") then d:Destroy() end
		if d:IsA("Humanoid") then d.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	end
	m.Parent = root
	local want = O * Fp
	local piv = m:GetPivot()
	local look = Vector3.new(want.LookVector.X, 0, want.LookVector.Z).Unit
	m:PivotTo(CFrame.lookAt(piv.Position, piv.Position + look))
	local bb, size = m:GetBoundingBox()
	local d = Vector3.new(want.X - bb.X, want.Y - (bb.Y - size.Y / 2), want.Z - bb.Z)
	m:PivotTo(m:GetPivot() + d)
end

-- ------------------------------------------------------------------------------------------------ things
-- (each faces its frame's look, -Z; built from the floor up)
local function sofa(Fp, len, hex, people)
	box(Fp, "Sofa", -len / 2, len / 2, 0, 1.45, -1.0, 1.2, hex)
	box(Fp, "Sofa", -len / 2, len / 2, 1.45, 3.5, 1.2, 1.9, hex)
	for _, s in { -1, 1 } do box(Fp, "Sofa", s * len / 2, s * (len / 2 + 0.7), 0, 2.3, -1.0, 1.9, hex) end
	for i = 1, people or 0 do person(Fp * CFrame.new(-len / 2 + len * (i - 0.5) / people, 0, 0), true) end
end
local function cluster(Fc, people) -- a rug, a sofa, two armchairs facing in, a low table, a tall planter
	cyl(Fc, "Rug", 0, 0, 0.06, 0, 11, K.carpet, MAT.Fabric)
	sofa(Fc * CFrame.new(0, 0, 3.4), 6.4, K.sofa, math.min(people or 0, 2))
	for i, s in { -1, 1 } do
		local Fa = Fc * CFrame.new(s * 3.9, 0, -0.8) * CFrame.Angles(0, math.rad(s * 90), 0)
		sofa(Fa, 2.2, K.sofa, if (people or 0) > 1 + i then 1 else 0)
	end
	box(Fc, "LowTable", -1.5, 1.5, 0, 1.2, -1.6, 0.6, K.wood, MAT.Wood)
	cyl(Fc, "Planter", 4.6, 0, 2.2, 4.6, 2.4, K.trim)
	ball(Fc, "Bush", 4.6, 3.4, 4.6, 3.2, K.plant, MAT.Grass)
end
local function planterBench(F, len, people) -- along F's z: a planter with bushes, a bench ledge either side
	box(F, "Planter", -1.3, 1.3, 0, 2.4, -len / 2, len / 2, K.trim)
	box(F, "Soil", -1.05, 1.05, 2.4, 2.45, -len / 2 + 0.25, len / 2 - 0.25, K.soil)
	local nb = math.max(2, math.floor(len / 3))
	for i = 1, nb do ball(F, "Bush", ((i % 2) - 0.5) * 0.6, 3.3, -len / 2 + (i - 0.5) * len / nb, 2.5, if i % 2 == 0 then K.plant else K.plant2, MAT.Grass) end
	for _, s in { -1, 1 } do box(F, "Bench", s * 1.3, s * 2.5, 0, 1.45, -len / 2, len / 2, K.wood, MAT.Wood) end
	for i = 1, people or 0 do
		local s = if i % 2 == 0 then 1 else -1
		person(F * CFrame.new(s * 1.8, 0, -len / 2 + len * (i - 0.5) / people) * CFrame.Angles(0, math.rad(-90 * s), 0), true)
	end
end
local function chess(Fp, people)
	cyl(Fp, "TableFoot", 0, 0, 0.3, 0, 2.2, K.dark)
	cyl(Fp, "TableStem", 0, 0.3, 2.5, 0, 0.5, K.dark)
	cyl(Fp, "TableTop", 0, 2.5, 2.7, 0, 3.8, K.wood, MAT.Wood)
	box(Fp, "Board", -1.0, 1.0, 2.7, 2.76, -1.0, 1.0, "d8d2c4")
	for i = 0, 3 do for j = 0, 3 do
		if (i + j) % 2 == 0 then box(Fp, "Square", -1 + i * 0.5, -0.5 + i * 0.5, 2.76, 2.78, -1 + j * 0.5, -0.5 + j * 0.5, "3a3530") end
	end end
	for _, s in { -1, 1 } do
		cyl(Fp, "Stool", 0, 0, 1.45, s * 3.0, 1.6, K.dark)
		if people then person(Fp * CFrame.new(0, 0, s * 3.0) * CFrame.Angles(0, if s > 0 then 0 else math.pi, 0), true) end
	end
end
local function armTable(Fp, people)
	box(Fp, "ArmTable", -1.3, 1.3, 0, 3.0, -0.8, 0.8, K.dark)
	box(Fp, "ArmTop", -1.6, 1.6, 3.0, 3.25, -1.1, 1.1, K.wood, MAT.Wood)
	for i, s in { -1, 1 } do cyl(Fp, "ElbowPad", s * 0.5, 3.25, 3.33, 0, 0.8, if i == 1 then "8f4a45" else "4a6585") end
	if people then
		for _, s in { -1, 1 } do person(Fp * CFrame.new(s * 2.2, 0, 0) * CFrame.Angles(0, math.rad(s * 90), 0), false) end
	end
end
local function arcade(Fp, player)
	box(Fp, "Cabinet", -1.5, 1.5, 0, 6.4, -1.0, 1.3, K.cab)
	box(Fp, "CabinetDeck", -1.5, 1.5, 3.0, 3.5, -1.6, -1.0, K.cab)
	box(Fp, "CabinetScreen", -1.2, 1.2, 3.9, 5.6, -1.06, -1.0, "35708c", MAT.Neon)
	local mq = box(Fp, "CabinetMarquee", -1.5, 1.5, 5.85, 6.4, -1.1, -1.0, K.amber, MAT.Neon)
	glow(mq, 8, 0.4, K.amber)
	if player then person(Fp * CFrame.new(0, 0, -2.7) * CFrame.Angles(0, math.pi, 0), false) end
end
local function ring(Fp, S) -- a boxing ring S across: skirt, canvas, slim posts, slim vinyl corner pads, three ropes
	local h = S / 2
	box(Fp, "RingSkirt", -h, h, 0, 1.3, -h, h, "3c4048", MAT.Fabric)
	box(Fp, "RingApron", -h - 0.1, h + 0.1, 0.95, 1.25, -h - 0.1, h + 0.1, K.trim2)
	box(Fp, "RingMat", -h + 0.8, h - 0.8, 1.3, 1.36, -h + 0.8, h - 0.8, K.canvas, MAT.Fabric)
	local po = h - 1.2
	for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
		cyl(Fp, "RingPost", cx * po, 1.3, 6.4, cz * po, 0.7, K.steel)
		cyl(Fp, "CornerPad", cx * po, 2.4, 5.6, cz * po, 0.95, if cx < 0 and cz < 0 then "8f4a45" elseif cx > 0 and cz > 0 then "4a6585" else K.trim2)
	end end
	for _, y in { 2.8, 3.9, 5.0 } do
		for _, s in { -1, 1 } do
			rod(Fp, "Rope", Vector3.new(-po, y, s * po), Vector3.new(po, y, s * po), 0.26, K.trim2)
			rod(Fp, "Rope", Vector3.new(s * po, y, -po), Vector3.new(s * po, y, po), 0.26, K.trim2)
		end
	end
end
local function shop(Fp, len)
	box(Fp, "Counter", -len / 2, len / 2, 0, 3.4, -1.0, 1.0, K.wood, MAT.Wood)
	box(Fp, "CounterTop", -len / 2 - 0.2, len / 2 + 0.2, 3.4, 3.7, -1.25, 1.1, K.trim2)
	box(Fp, "ShopShelves", -len / 2, len / 2, 0, 9, 3.6, 4.6, K.wall2)
	for _, y in { 2.4, 4.6, 6.8 } do
		box(Fp, "Shelf", -len / 2 + 0.3, len / 2 - 0.3, y, y + 0.2, 2.8, 3.6, K.trim)
		local n = math.floor((len - 0.8) / 1.6)
		for i = 0, n - 1 do
			box(Fp, "Goods", -len / 2 + 0.6 + i * 1.6, -len / 2 + 1.7 + i * 1.6, y + 0.2, y + 1.1 + (i % 3) * 0.35, 3.0, 3.5, ({ "8a6d5a", "5a6e7a", "7a7a6a", "6a5a6a", "9a8064" })[i % 5 + 1])
		end
	end
	local s = box(Fp, "ShopSign", -len / 2 + 1, len / 2 - 1, 9.3, 10.9, 3.4, 3.6, K.screen)
	text(s, Enum.NormalId.Front, { { "SHOP", K.amber, 0.85 } })
	local l = box(Fp, "ShopLight", -len / 2 + 0.5, len / 2 - 0.5, 8.7, 8.9, 2.6, 3.0, K.warm, MAT.Neon)
	glow(l, 14, 0.6)
end
local function codePanel(Fp) -- on a wall, facing out
	box(Fp, "CodePanel", -1.8, 1.8, 2.4, 7.2, -0.3, 0, K.screen)
	local sc = box(Fp, "CodeScreen", -1.4, 1.4, 5.9, 6.8, -0.36, -0.3, "2f6a5a", MAT.Neon)
	glow(sc, 6, 0.4, "8fe0c8")
	for i = 0, 2 do for j = 0, 3 do box(Fp, "CodeKey", -1.2 + i * 0.85, -0.6 + i * 0.85, 2.9 + j * 0.75, 3.5 + j * 0.75, -0.42, -0.3, K.trim2) end end
end
local function trophyCase(Fp)
	box(Fp, "CaseBase", -4, 4, 0, 1.4, -1.2, 1.2, K.dark)
	box(Fp, "CaseGlass", -3.9, 3.9, 1.4, 7.4, -1.1, 1.1, K.glass, MAT.Glass, { tr = 0.6 })
	box(Fp, "CaseTop", -4, 4, 7.4, 7.8, -1.2, 1.2, K.dark)
	for _, y in { 1.4, 4.3 } do
		box(Fp, "CaseShelf", -3.8, 3.8, y, y + 0.15, -1.0, 1.0, K.trim)
		for i = -1, 1 do
			cyl(Fp, "Trophy", i * 2.4, y + 0.15, y + 1.6, 0, 0.6, K.gold, MAT.Metal)
			ball(Fp, "Trophy", i * 2.4, y + 2.0, 0, 1.0, K.gold, MAT.Metal)
		end
	end
	local l = box(Fp, "CaseLight", -3.6, 3.6, 7.2, 7.35, -0.6, 0.6, K.warm, MAT.Neon)
	glow(l, 9, 0.7)
end
local function holoCyl(Fp, y0, h, dia, hex)
	local c = cyl(Fp, "Holo", 0, y0, y0 + h, 0, dia, hex, MAT.Neon, { tr = 0.8, noshadow = true })
	glow(c, 10, 0.8, hex)
end
local function bundle(Fp)
	cyl(Fp, "PlinthFoot", 0, 0, 0.35, 0, 4.6, K.dark)
	cyl(Fp, "Plinth", 0, 0.35, 1.4, 0, 4.0, K.trim)
	cyl(Fp, "PlinthRing", 0, 1.36, 1.46, 0, 3.0, "8fd8ff", MAT.Neon)
	holoCyl(Fp, 1.5, 4.6, 2.8, "8fd8ff")
	local b = part("BundleBox", Fp * CFrame.new(0, 3.6, 0) * CFrame.Angles(0.4, 0.7, 0.2), Vector3.new(1.5, 1.5, 1.5), K.gold, MAT.Metal)
	b.Parent = root
end
local function holo(Fp, kind)
	cyl(Fp, "HoloFoot", 0, 0, 0.5, 0, 6.4, K.dark)
	cyl(Fp, "HoloPlinth", 0, 0.5, 1.6, 0, 5.6, K.trim)
	cyl(Fp, "HoloLens", 0, 1.56, 1.66, 0, 2.2, "8fd8ff", MAT.Neon)
	holoCyl(Fp, 1.7, 7.5, 4.4, "8fd8ff")
	if kind == "loadout" then -- (a gun turning in the light)
		box(Fp * CFrame.new(0, 5.2, 0) * CFrame.Angles(0, 0.6, 0), "HoloGun", -1.8, 1.8, -0.35, 0.35, -0.3, 0.3, "9ad8f0", MAT.Neon)
		box(Fp * CFrame.new(0, 5.2, 0) * CFrame.Angles(0, 0.6, 0), "HoloGun", 0.6, 1.2, -1.4, -0.35, -0.25, 0.25, "9ad8f0", MAT.Neon)
	else -- (mastery: a blade in its camo, a ring of the levels round it)
		box(Fp * CFrame.new(0, 5.4, 0) * CFrame.Angles(0, 0.3, 0.2), "HoloBlade", -0.25, 0.25, -2.2, 2.2, -0.1, 0.1, K.gold, MAT.Neon)
		cyl(Fp, "HoloLevels", 0, 3.0, 3.12, 0, 4.0, K.gold, MAT.Neon, { tr = 0.3 })
	end
	local s = box(Fp, "HoloSign", -2.2, 2.2, 9.4, 10.3, -0.05, 0.05, K.screen, nil, { tr = 1 })
	text(s, Enum.NormalId.Front, { { if kind == "loadout" then "YOUR LOADOUT" else "MASTERY", K.pale, 0.9 } }, { bgt = 0.5 })
	text(s, Enum.NormalId.Back, { { if kind == "loadout" then "YOUR LOADOUT" else "MASTERY", K.pale, 0.9 } }, { bgt = 0.5 })
end
local SCREEN_LINES = {
	{ "NEXT MATCH", K.amber, 0.16 }, { "ROOFTOP  ·  2V2  ·  0:42", K.pale, 0.2 },
	{ "MAP VOTE    GUT 3    SUBURB 5    BAZAAR 1", "c8d0d8", 0.13 }, { "1V1 2   1V1V1 0   2V2 3   3V3 1   4V4 6", "8fd8ff", 0.13 },
}
local function liveScreen(cf, w, h, faces)
	part("ScreenFrame", cf, Vector3.new(w + 0.8, h + 0.8, 0.9), K.trim2)
	local sc = part("LiveScreen", cf, Vector3.new(w, h, 1.0), K.screen)
	for _, f in faces do text(sc, f, SCREEN_LINES, { pps = 24, bright = 2 }) end
	glow(sc, 26, 0.5, "9fd0ff")
	return sc
end
local function board(Fp, title) -- a ranked board on a wall, facing out
	box(Fp, "BoardFrame", -4.8, 4.8, 2.6, 10.6, -0.4, 0, K.trim2)
	local b = box(Fp, "Board", -4.4, 4.4, 3.0, 10.2, -0.5, -0.4, K.screen)
	text(b, Enum.NormalId.Front, { { title, K.amber, 0.16 }, { "1   ·   2140", K.pale, 0.11 }, { "2   ·   2085", K.pale, 0.11 }, { "3   ·   1990", K.pale, 0.11 },
		{ "4   ·   1932", K.pale, 0.11 }, { "5   ·   1870", K.pale, 0.11 } }, { pps = 30 })
end
local function weaponWall(Fp, len) -- a lit board with rows of guns, facing out
	box(Fp, "WeaponWall", -len / 2, len / 2, 1.2, 9.4, -0.5, 0, K.wall2)
	for r = 0, 2 do
		local y = 2.6 + r * 2.4
		for i = 0, math.floor(len / 3.2) - 1 do
			local x = -len / 2 + 1.6 + i * 3.2
			box(Fp, "Gun", x - 1.2, x + 1.2, y, y + 0.45, -0.85, -0.5, K.dark)
			box(Fp, "Gun", x + 0.2, x + 0.6, y - 0.6, y, -0.8, -0.55, K.dark)
		end
	end
	local l = box(Fp, "WallLight", -len / 2 + 0.4, len / 2 - 0.4, 9.4, 9.6, -0.9, -0.5, K.warm, MAT.Neon)
	glow(l, 14, 0.6)
end
local function trainingGate(Fp) -- the training entrance: a black opening behind a laser fence, framed
	box(Fp, "GateBack", -6, 6, 0, 10, 0, 0.4, "101114")
	for _, s in { -1, 1 } do box(Fp, "GateFrame", s * 6, s * 7, 0, 11, -0.6, 0.4, K.steel) end
	local hd = box(Fp, "GateHead", -7, 7, 10, 11.6, -0.6, 0.4, K.screen)
	text(hd, Enum.NormalId.Front, { { "TRAINING", K.pale, 0.8 } })
	for i = 0, 5 do box(Fp, "Laser", -5.9, 5.9, 1 + i * 1.5, 1.08 + i * 1.5, -0.35, -0.3, "ff3b3b", MAT.Neon, { noshadow = true }) end
end
local function jumpPad(Fp)
	cyl(Fp, "JumpPad", 0, 0, 0.5, 0, 4.4, K.dark)
	local g = cyl(Fp, "JumpGlow", 0, 0.45, 0.6, 0, 3.4, "8fd8ff", MAT.Neon)
	glow(g, 8, 0.8, "8fd8ff")
end
local function duck(Fp, s) -- the VIP's gold duck
	ball(Fp, "Duck", 0, 1.4 * s, 0, 2.6 * s, K.gold, MAT.Metal)
	ball(Fp, "Duck", 0, 2.9 * s, -0.7 * s, 1.6 * s, K.gold, MAT.Metal)
	box(Fp, "Duck", -0.35 * s, 0.35 * s, 2.7 * s, 2.95 * s, -1.9 * s, -1.4 * s, "c9803a", MAT.Metal)
end
local function lockerBank(Fp, len) -- tall lockers against a wall, facing out
	box(Fp, "LockerBody", -len / 2, len / 2, 0.35, 7.7, 0, 1.6, K.dark)
	box(Fp, "LockerCap", -len / 2, len / 2, 7.7, 7.9, -0.1, 1.6, K.trim)
	for i = 0, math.floor(len / 1.8) - 1 do
		local x = -len / 2 + 0.9 + i * 1.8
		box(Fp, "LockerDoor", x - 0.8, x + 0.8, 0.6, 7.45, -0.06, 0, "6c6862")
	end
end
local function bags(F, x0, x1, z, rail) -- a row of tall heavy bags on short chains from a rail
	box(F, "BagRail", x0 - 1, x1 + 1, 10.4, 10.9, z - 0.2, z + 0.2, K.steel)
	local n = math.floor((x1 - x0) / 4) + 1
	for i = 0, n - 1 do
		local x = x0 + i * (x1 - x0) / math.max(n - 1, 1)
		cyl(F, "Chain", x, 8.9, 10.4, z, 0.15, K.steel)
		cyl(F, "HeavyBag", x, 2.8, 8.9, z, 2.0, "6e4a44")
	end
end
local function ringLights(F, x, z, y)
	box(F, "LampBeam", x - 9, x + 9, y, y + 0.45, z - 0.2, z + 0.2, K.trim)
	for _, s in { -1, 1 } do
		cyl(F, "LampShade", x + s * 5, y - 1.2, y, z, 1.6, K.dark)
		local l = cyl(F, "Lamp", x + s * 5, y - 1.3, y - 1.2, z, 1.3, K.warm, MAT.Neon)
		glow(l, 20, 0.9)
	end
end

-- ------------------------------------------------------------------------------------------------ the pads
local function slots(md) return md.n * md.t end
-- (1) PLAYER SPOTS (A): in a bay, F at the bay's mouth on the floor, its look into the bay; W across, D deep. a low stage
-- with a lit nosing, a low divider down the middle with the mode's name, a marked spot for each player (a thin rim in
-- the side's colour, the middle lit when someone stands there)
local function padSpots(F, W, D, md, joined)
	box(F, "PadStage", -W / 2, W / 2, 0, 0.4, -D, 0, K.padBase)
	box(F, "PadNosing", -W / 2, W / 2, 0, 0.46, -0.4, 0, K.trim2)
	local nl = box(F, "PadNosingLight", -W / 2 + 0.3, W / 2 - 0.3, 0.14, 0.24, 0.0, 0.04, K.light, MAT.Neon, { noshadow = true })
	local spots = {}
	if md.t == 2 then
		local dv = box(F, "PadDivider", -0.25, 0.25, 0.4, 1.5, -D + 0.8, -1.6, K.trim)
		local dc = box(F, "PadDividerCap", -0.32, 0.32, 1.5, 1.62, -D + 0.7, -1.5, K.dark)
		text(dv, Enum.NormalId.Left, { { md.title, K.pale, 0.8 } }); text(dv, Enum.NormalId.Right, { { md.title, K.pale, 0.8 } })
		for i = 1, md.n do
			table.insert(spots, { -2.7, -2.4 - (i - 1) * 2.3, 1, -90 }); table.insert(spots, { 2.7, -2.4 - (i - 1) * 2.3, 2, 90 })
		end
	else
		for k, x in { -3.8, 0, 3.8 } do table.insert(spots, { x, -4.4, k, 180 }) end
		for _, x in { -1.9, 1.9 } do box(F, "PadDivider", x - 0.2, x + 0.2, 0.4, 1.5, -D + 1.2, -2.2, K.trim) end
	end
	for i, s in spots do
		local on = i <= joined
		cyl(F, "SpotRim", s[1], 0.4, 0.43, s[2], 2.5, TEAM[s[3]], MAT.Neon, { noshadow = true })
		local c = cyl(F, "Spot", s[1], 0.4, 0.47, s[2], 2.16, if on then TEAM[s[3]] else K.dark, if on then MAT.Neon else nil, { tr = if on then 0.35 else 0 })
		if on then glow(c, 7, 0.9, TEAM[s[3]]); person(F * CFrame.new(s[1], 0.47, s[2]) * CFrame.Angles(0, math.rad(s[4]), 0), false) end
	end
	return nl
end
-- (2) PLATFORM (B): one of a side's two pads on the octagon's ground ring, Fk the side's frame (-z out), the pad from
-- the side's middle (gap g) to its slanted end; raised, a step at its front, a rim light along its front edge in a
-- segment per player that fills as they join, a thin line between the sides, a sign floating over it
local T225 = math.tan(math.rad(22.5))
local function hw(r) return r * T225 end
local function padPlatform(Fk, left, md, joined, rin, rout)
	local g = 0.7
	local xi = hw(rin) - 0.8 -- (the slanted side's x at the inner edge, at the outer edge)
	local xo = hw(rout) - 0.8
	local x0, x1 = if left then -xi else g, if left then -g else xi
	local H = 1.1
	box(Fk, "PadPlatform", x0, x1, 0, H, -rout, -rin, K.padBase)
	if left then slant(Fk, "PadPlatform", -xi, -xo, -rin, -rout, 0, H, K.padBase) else slant(Fk, "PadPlatform", xi, xo, -rin, -rout, 0, H, K.padBase) end
	box(Fk, "PadStep", x0, x1, 0, 0.55, -rin, -rin + 1.1, K.padBase)
	box(Fk, "PadEdge", x0, x1, H - 0.08, H + 0.02, -rin - 0.45, -rin, K.trim2)
	local n = slots(md)
	local seg = (x1 - x0 - 0.6) / n
	for i = 1, n do
		local team = if md.t == 3 then i else (if i <= n / 2 then 1 else 2)
		local on = (if md.t == 3 then i <= joined else (if i <= n / 2 then i <= math.ceil(joined / 2) else i - n / 2 <= math.floor(joined / 2)))
		local sx = x0 + 0.3 + (i - 1) * seg
		local r = box(Fk, "PadRim", sx + 0.06, sx + seg - 0.06, H + 0.02, H + 0.1, -rin - 0.4, -rin - 0.1, if on then TEAM[team] else K.unlit, if on then MAT.Neon else nil, { noshadow = true })
		if on then glow(r, 5, 0.7, TEAM[team]) end
	end
	local xm = (x0 + x1) / 2
	if md.t == 2 then box(Fk, "PadLine", xm - 0.08, xm + 0.08, H, H + 0.03, -rout + 0.4, -rin - 0.6, K.screen) end
	cyl(Fk, "PadEmitter", xm, H, H + 0.12, -rout + 1.6, 0.9, "8fd8ff", MAT.Neon)
	local zm = -(rin + rout) / 2
	local sp = part("PadSign", Fk * CFrame.lookAt(Vector3.new(xm, 8.6, zm), Vector3.new(xm, 8.6, zm + 10)), Vector3.new(6.4, 3.4, 0.1), K.screen, nil, { tr = 1 })
	text(sp, Enum.NormalId.Front, { { md.title, "dff6ff", 0.5 }, { ("%d / %d"):format(joined, n), if joined > 0 then K.amber else "9fb0bc", 0.32 } }, { bgt = 0.55, pps = 40 })
	-- the players on it: each side's half, rows from the front, facing in
	local placed = 0
	for i = 1, joined do
		local team = if md.t == 3 then i else (if i % 2 == 1 then 1 else 2)
		local k = if md.t == 3 then 1 else math.ceil(i / 2)
		local hx = if md.t == 3 then x0 + (x1 - x0) * (i - 0.5) / 3 else (if team == 1 then (x0 + xm) / 2 else (xm + x1) / 2)
		person(Fk * CFrame.new(hx + (if k % 2 == 0 then 0.9 else -0.9), H, -rin - 2.4 - (k - 1) * 2.6) * CFrame.Angles(0, math.pi, 0), false)
		placed += 1
	end
end
-- (3) GATE (C): a framed portal set into a wall, F at its mouth on the floor, its look into the alcove (5 deep, 10
-- wide): a half for each side split by a mullion (thirds for 1v1v1), a thin light in the side's colour up each jamb,
-- a marked place per player inside, the mode and the count on the header facing out
local function padGate(F, md, joined)
	box(F, "GateFloor", -5, 5, 0, 0.3, -5, 0, K.padBase)
	box(F, "GateSill", -5.8, 5.8, 0, 0.36, -0.5, 0.3, K.trim2)
	for _, s in { -1, 1 } do
		box(F, "GatePost", s * 5, s * 5.8, 0, 10.8, -0.6, 0.4, K.steel)
		local l = box(F, "GateLight", s * 4.94, s * 5.0, 0.6, 9.2, -0.4, 0.2, TEAM[if s < 0 then 1 else 2], MAT.Neon, { noshadow = true })
		glow(l, 6, 0.5, TEAM[if s < 0 then 1 else 2])
	end
	local hd = box(F, "GateHeader", -5.8, 5.8, 9.4, 10.8, -0.6, 0.4, K.screen)
	text(hd, Enum.NormalId.Back, { { ("%s    %d / %d"):format(md.title, joined, slots(md)), if joined > 0 then K.amber else K.pale, 0.8 } })
	local cut = if md.t == 3 then { -1.67, 1.67 } else { 0 }
	for _, x in cut do box(F, "GateMullion", x - 0.18, x + 0.18, 0.3, 9.4, -0.5, 0.3, K.steel) end
	box(F, "GateBack", -5, 5, 0.3, 9.4, -5.2, -5.0, "20252c", MAT.Neon, { tr = 0.1 })
	-- the places: each side's half (or third), in a grid
	local places = {}
	if md.t == 3 then
		for k = 1, 3 do table.insert(places, { -3.33 + (k - 1) * 3.33, -2.5, k }) end
	else
		local grid = ({ { { 2.5, -2.5 } }, { { 2.5, -1.6 }, { 2.5, -3.6 } }, { { 1.5, -1.6 }, { 3.6, -1.6 }, { 2.5, -3.7 } },
			{ { 1.5, -1.5 }, { 3.6, -1.5 }, { 1.5, -3.6 }, { 3.6, -3.6 } } })[md.n]
		for k, p in grid do
			table.insert(places, { -p[1], p[2], 1 }); table.insert(places, { p[1], p[2], 2 })
		end
	end
	for i, p in places do
		local on = i <= joined
		cyl(F, "GateSpot", p[1], 0.3, 0.33, p[2], 1.7, TEAM[p[3]], MAT.Neon, { noshadow = true })
		cyl(F, "GateSpotIn", p[1], 0.3, 0.36, p[2], 1.4, if on then TEAM[p[3]] else K.dark, if on then MAT.Neon else nil, { tr = if on then 0.35 else 0 })
		if on then person(F * CFrame.new(p[1], 0.36, p[2]) * CFrame.Angles(0, math.pi, 0), false) end
	end
end

-- ------------------------------------------------------------------------------------------------ the concepts
local function begin(name)
	local f = workspace:FindFirstChild("HubConcepts")
	if not f then f = Instance.new("Folder"); f.Name = "HubConcepts"; f.Parent = workspace end
	local old = f:FindFirstChild(name); if old then old:Destroy() end
	root = Instance.new("Folder"); root.Name = name; root.Parent = f
	O = CFrame.new(HC.SITES[name])
	pn = 0
end
local function W(v: Vector3) return (O * CFrame.new(v)).Position end
local function shot(S, name, cam, look) table.insert(S, { name, W(cam), W(look) }) end

-- A: THE CONCOURSE ----------------------------------------------------------------------------------
function HC.A()
	begin("A")
	local F0 = CFrame.new()
	local L, S = {}, {}
	local T = 31 -- (the hall's ceiling)
	box(F0, "Floor", -40, 40, -1, 0, -72, 72, K.floor)
	box(F0, "Runner", -7, 7, 0, 0.04, -66, 66, K.runner, MAT.Fabric)
	-- the walls: the armory's way in the west one, the gym's whole end north, the VIP's door and windows south
	box(F0, "Wall", 38, 40, 0, T, -72, 72, K.wall)
	box(F0, "Wall", -40, -38, 0, T, -72, -66, K.wall); box(F0, "Wall", -40, -38, 0, T, -50, 72, K.wall); box(F0, "Wall", -40, -38, 13, T, -66, -50, K.wall)
	box(F0, "Wall", -40, -20, 0, T, -72, -70, K.wall); box(F0, "Wall", 20, 40, 0, T, -72, -70, K.wall); box(F0, "Wall", -20, 20, 21, T, -72, -70, K.wall)
	for _, s in { -1, 1 } do
		box(F0, "Wall", s * 16, s * 40, 0, T, 70, 72, K.wall)
		box(F0, "Wall", s * 5.6, s * 16, 0, 2, 70, 72, K.wall); box(F0, "Wall", s * 5.6, s * 16, 9, T, 70, 72, K.wall)
		box(F0, "VipWindow", s * 5.6, s * 16, 2, 9, 70.8, 71.2, K.glass, MAT.Glass, { tr = 0.55 })
		box(F0, "VipDoorPost", s * 5.6, s * 6.4, 0, 11.4, 69.4, 70, K.gold, MAT.Metal)
	end
	box(F0, "Wall", -5.6, 5.6, 10.6, T, 70, 72, K.wall)
	local vs = box(F0, "VipSign", -5.6, 5.6, 11.6, 13.4, 69.4, 70, K.screen)
	text(vs, Enum.NormalId.Front, { { "VIP", K.gold, 0.8 } })
	box(F0, "VipDoorHead", -6.4, 6.4, 10.6, 11.4, 69.4, 70, K.gold, MAT.Metal)
	box(F0, "Roof", -40, 40, T, T + 1, -72, 72, K.ceil)
	for z = -65, 65, 10 do box(F0, "CeilingBeam", -26, 26, T - 2.6, T, z - 0.7, z + 0.7, K.trim) end
	for z = -60, 60, 10 do panel(F0, 0, T, z, 12, 8.4, 0.5) end
	-- columns and beams: the nave's edge, the mezzanine over the side aisles (fascia, glass rail)
	local CZ = { -60, -45, -30, -15, 0, 15, 30, 45, 60 }
	for _, s in { -1, 1 } do
		for _, z in CZ do
			box(F0, "Column", s * 25, s * 27, 0, T, z - 1, z + 1, K.col)
			box(F0, "ColumnCap", s * 24.7, s * 27.3, 12.3, 13, z - 1.3, z + 1.3, K.trim)
		end
		box(F0, "Mezzanine", s * 26, s * 38, 13, 14, -70, 70, K.floor2)
		box(F0, "MezzFascia", s * 25.4, s * 26.2, 12.6, 14.5, -70, 70, K.trim)
		box(F0, "MezzRail", s * 25.9, s * 26.2, 14.5, 17.6, -70, 70, K.glass, MAT.Glass, { tr = 0.6 })
		box(F0, "MezzRailTop", s * 25.8, s * 26.3, 17.6, 18.0, -70, 70, K.trim)
		for z = -60, 60, 15 do panel(F0, s * 32, T, z, 6, 10, 0.4) end
	end
	-- the pad bays: five a side between the columns (south to north 1v1 .. 4v4, both sides alike), each a stage of
	-- player spots under a beam whose face carries the mode and the count, a backdrop with a lit cove, fins between
	local BZ = { 22.5, 7.5, -7.5, -22.5, -37.5 }
	local JOIN = { [-1] = { 0, 0, 3, 0, 5 }, [1] = { 1, 0, 0, 2, 0 } }
	for _, s in { -1, 1 } do
		for k, zc in BZ do
			local md = MODES[k]
			box(F0, "BayBeam", s * 25.2, s * 26.8, 10.4, 12.6, zc - 6.5, zc + 6.5, K.trim)
			local sg = box(F0, "BaySign", s * 25.05, s * 25.2, 10.6, 12.4, zc - 6.1, zc + 6.1, K.screen)
			local j = JOIN[s][k]
			text(sg, if s > 0 then Enum.NormalId.Left else Enum.NormalId.Right, { { ("%s   %d / %d"):format(md.title, j, slots(md)), if j > 0 then K.amber else K.pale, 0.8 } })
			box(F0, "BayBack", s * 37.5, s * 38, 0.8, 11.6, zc - 6.6, zc + 6.6, K.wall2)
			local cv = box(F0, "BayCove", s * 36.9, s * 37.5, 11.6, 11.8, zc - 6.4, zc + 6.4, K.light, MAT.Neon, { noshadow = true })
			glow(cv, 12, 0.4)
			local F = CFrame.lookAt(Vector3.new(s * 27, 0, zc), Vector3.new(s * 28, 0, zc))
			padSpots(F, 13.4, 10.4, md, j)
			table.insert(L, { md.title, s * 32, zc })
		end
		for _, z in { -45, -30, -15, 0, 15, 30 } do box(F0, "BayFin", s * 27, s * 38, 0, 13, z - 0.4, z + 0.4, K.wall2) end
	end
	-- the spawn end: the lounge in the hall itself. the spawn rug; the shop under the east mezzanine, its bundles in
	-- front; the arcade, the code panel and seats under the west one; the tables either side of the runner; YOUR
	-- LOADOUT at the head of the middle island
	cyl(F0, "SpawnRing", 0, 0, 0.05, 58, 12.6, K.trim2); cyl(F0, "SpawnRug", 0, 0, 0.08, 58, 12, K.carpet2, MAT.Fabric)
	shop(at(F0, 32, 46, 90), 20)
	regular(at(F0, 34.4, 46, 90), "Looticus")
	for _, z in { 38, 46, 54 } do bundle(at(F0, 21, z, 90)) end
	for i, z in { 34, 37.6, 41.2 } do arcade(at(F0, -36.4, z, -90), i ~= 2) end
	codePanel(at(F0, -38, 50, -90))
	cluster(at(F0, -31, 61, 90), 3); cluster(at(F0, 31, 63, -90), 2)
	chess(at(F0, -14, 40, 0), true); chess(at(F0, -14, 50, 90), false)
	armTable(at(F0, 13, 41, 0), true); armTable(at(F0, 13, 51, 0), false)
	holo(at(F0, 0, 30, 180), "loadout")
	for _, s in { -1, 1 } do jumpPad(at(F0, s * 18, 26, 0)) end
	-- the middle island: planters with benches down the runner, people on them; the big live screen over it
	planterBench(at(F0, 0, 17, 0), 12, 3); planterBench(at(F0, 0, -3, 0), 12, 2); planterBench(at(F0, 0, -26, 0), 12, 3)
	liveScreen(CFrame.lookAt(Vector3.new(0, 21, -14), Vector3.new(0, 21, -4)), 30, 10, { Enum.NormalId.Front, Enum.NormalId.Back })
	for _, s in { -1, 1 } do cyl(F0, "ScreenRod", s * 12, 26.4, T, -14, 0.35, K.steel) end
	holo(at(F0, 0, -50, 180), "mastery")
	-- the far end: the hall of fame (east), the armory's way in (west), the gym's whole end
	board(at(F0, 37.9, -64, 90), "DUELS"); board(at(F0, 37.9, -52, 90), "PARTIES")
	trophyCase(at(F0, 30, -58, 90))
	regular(at(F0, 33, -48, 90), "Frisk1636")
	for _, z in { -66, -50 } do box(F0, "ArmoryColumn", -40, -37, 0, 13, z - 1, z + 1, K.col) end
	local ab = box(F0, "ArmoryBeam", -40, -37.4, 11, 13, -66, -50, K.trim)
	local asg = box(F0, "ArmorySign", -37.4, -37.25, 11.2, 12.8, -64, -52, K.screen)
	text(asg, Enum.NormalId.Right, { { "ARMORY  ·  TRAINING", K.pale, 0.75 } })
	-- the armory room, the training gate at its far end
	box(F0, "Floor", -78, -40, -1, 0, -74, -42, K.floor2)
	box(F0, "Wall", -80, -78, 0, 15, -74, -42, K.wall); box(F0, "Wall", -80, -40, 0, 15, -76, -74, K.wall); box(F0, "Wall", -80, -40, 0, 15, -42, -40, K.wall)
	box(F0, "Roof", -80, -40, 15, 16, -76, -40, K.ceil)
	weaponWall(at(F0, -59, -73.9, 180), 30); weaponWall(at(F0, -59, -42.1, 0), 30)
	trainingGate(at(F0, -77.9, -58, -90))
	for _, z in { -66, -50 } do panel(F0, -59, 15, z, 20, 4) end
	for i = 1, 3 do person(at(F0, -64 + i * 5, -46.5, 180), false) end
	-- the gym, through the north end's whole width: its rings straight ahead
	box(F0, "GymFrame", -20.6, -20, 0, 21.6, -70.6, -69.4, K.steel); box(F0, "GymFrame", 20, 20.6, 0, 21.6, -70.6, -69.4, K.steel)
	local gh = box(F0, "GymHeader", -20.6, 20.6, 19.4, 21.6, -70.6, -69.4, K.screen)
	text(gh, Enum.NormalId.Back, { { "GYM", K.pale, 0.8 } })
	box(F0, "GymFloor", -38, 38, -1, 0, -134, -72, K.gymFloor, MAT.Rubber)
	box(F0, "Wall", -40, -38, 0, 23, -136, -72, K.gymWall); box(F0, "Wall", 38, 40, 0, 23, -136, -104, K.gymWall); box(F0, "Wall", 38, 40, 0, 23, -96, -72, K.gymWall)
	box(F0, "Wall", 38, 40, 10, 23, -104, -96, K.gymWall); box(F0, "Wall", -40, 40, 0, 23, -136, -134, K.gymWall)
	box(F0, "Roof", -40, 40, 23, 24, -136, -72, K.ceil)
	for _, p in { { -15, -91 }, { 15, -91 }, { -15, -115 }, { 15, -115 } } do ring(at(F0, p[1], p[2], 0), 20); ringLights(F0, p[1], p[2], 17) end
	bags(F0, -34, -6, -131.5); bags(F0, 6, 22, -131.5)
	for _, z in { -80, -103, -126 } do panel(F0, 0, 23, z, 10, 3) end
	regular(at(F0, 12, -64, 180), "Dune")
	for i, p in { { -15, -86 }, { -14, -95 }, { 15, -112 } } do person(at(F0, p[1], p[2], i * 120, 1.36), false) end
	-- the locker room off the gym's east wall
	box(F0, "Floor", 40, 66, -1, 0, -124, -76, "a9adb2", MAT.CeramicTiles)
	box(F0, "Wall", 66, 68, 0, 13, -126, -74, K.gymWall); box(F0, "Wall", 40, 68, 0, 13, -126, -124, K.gymWall); box(F0, "Wall", 40, 68, 0, 13, -76, -74, K.gymWall)
	box(F0, "Roof", 40, 68, 13, 14, -126, -74, K.ceil)
	lockerBank(at(F0, 53, -123.9, 180), 24); lockerBank(at(F0, 53, -76.1, 0), 24)
	box(F0, "LockerBench", 46, 62, 0, 1.6, -101, -99, K.wood, MAT.Wood)
	-- the VIP room behind the south wall: the gold duck, sofas, Trisangle
	box(F0, "Floor", -18, 18, -1, 0, 72, 100, K.plum, MAT.Fabric)
	box(F0, "Wall", -20, -18, 0, 15, 72, 102, K.wall); box(F0, "Wall", 18, 20, 0, 15, 72, 102, K.wall); box(F0, "Wall", -20, 20, 0, 15, 100, 102, K.wall)
	box(F0, "Roof", -20, 20, 15, 16, 72, 102, K.ceil)
	cyl(F0, "DuckPlinth", 0, 0, 2.4, 94, 5, K.dark); duck(at(F0, 0, 94, 180, 2.4), 1.4)
	sofa(at(F0, -12, 86, -90), 7, K.plum, 1); sofa(at(F0, 12, 86, 90), 7, K.plum, 0)
	regular(at(F0, 9, 86, 90), "Trisangle")
	panel(F0, 0, 15, 86, 8, 8, 0.7)
	-- people about the hall and on the mezzanine
	for i, p in { { -4, 36, 160 }, { 5, 22, 200 }, { -10, 8, 90 }, { 9, -8, 250 }, { -6, -40, 30 }, { 7, -58, 190 }, { 18, 34, 270 }, { -20, 20, 90 }, { 19, -20, 270 }, { -19, -33, 90 } } do
		person(at(F0, p[1], p[2], p[3]), false)
	end
	for i, p in { { -27.5, 40, -90 }, { -27.5, 2, -90 }, { -27.5, -30, -90 }, { 27.5, 20, 90 }, { 27.5, -12, 90 }, { 27.5, -44, 90 } } do
		person(at(F0, p[1], p[2], p[3], 14), false)
	end
	cluster(at(F0, -32, -60, 90, 14), 2); cluster(at(F0, 32, 58, -90, 14), 2)
	-- plan labels and the shots
	for _, l in { { "SPAWN", 0, 58 }, { "VIP", 0, 87 }, { "SHOP", 34, 46 }, { "BUNDLES", 21, 46 }, { "ARCADE", -34, 37 }, { "CODE PANEL", -33, 50 },
		{ "TABLES", -14, 45 }, { "ARM", 13, 46 }, { "LOADOUT", 0, 30 }, { "LIVE SCREEN", 0, -14 }, { "MASTERY", 0, -50 }, { "GYM 4 RINGS", 0, -103 },
		{ "LOCKERS", 53, -100 }, { "ARMORY", -59, -58 }, { "TRAINING", -73, -58 }, { "HALL OF FAME", 32, -58 } } do table.insert(L, l) end
	shot(S, "spawn", Vector3.new(0, 5.4, 64), Vector3.new(0, 8.5, -10))
	shot(S, "gym", Vector3.new(-14, 6.2, -38), Vector3.new(4, 4, -100))
	shot(S, "mezzanine", Vector3.new(-31, 19.5, 52), Vector3.new(-2, 8, -20))
	shot(S, "pad_on", Vector3.new(-12, 6.4, 0.5), Vector3.new(-32, 1.2, -7.5))
	shot(S, "pad_off", Vector3.new(-12, 6.4, -14.5), Vector3.new(-32, 1.2, -22.5))
	return { labels = L, shots = S, plan = { c = W(Vector3.new(-5, 0, -30)), h = 175 } }
end

-- B: THE ATRIUM ----------------------------------------------------------------------------------------
local function sideF(b) return CFrame.Angles(0, -math.rad(b), 0) end -- (looking out at bearing b: -z out, x to the right)
function HC.B()
	begin("B")
	local F0 = CFrame.new()
	local L, S = {}, {}
	local RW, RV, RV3, Y2, Y3, TOP = 40, 18, 24, 15, 29, 44
	box(F0, "Floor", -42, 42, -1, 0, -42, 42, K.floor)
	-- the octagon: walls (portals with lit headers: the gym SE, the armory SW), the two galleries, the roof
	for b = 0, 315, 45 do
		local Fk = sideF(b)
		local ww = hw(RW + 2) + 0.05
		if b == 135 or b == 225 then
			local ow = if b == 135 then 12 else 7
			local oh = if b == 135 then 13.5 else 11
			box(Fk, "Wall", -ww, -ow, 0, TOP, -RW - 2, -RW, K.wall); box(Fk, "Wall", ow, ww, 0, TOP, -RW - 2, -RW, K.wall)
			box(Fk, "Wall", -ow, ow, oh + 1.6, TOP, -RW - 2, -RW, K.wall)
			for _, s in { -1, 1 } do box(Fk, "PortalFrame", s * ow, s * (ow + 0.8), 0, oh + 1.6, -RW - 0.4, -RW + 0.4, K.steel) end
			local hd = box(Fk, "PortalHeader", -ow - 0.8, ow + 0.8, oh, oh + 1.6, -RW - 0.4, -RW + 0.5, K.screen)
			text(hd, Enum.NormalId.Back, { { if b == 135 then "GYM" else "ARMORY  ·  TRAINING", K.pale, 0.75 } })
			local hl = box(Fk, "PortalLight", -ow, ow, oh - 0.2, oh, -RW - 0.2, -RW + 0.3, K.light, MAT.Neon, { noshadow = true })
			glow(hl, 14, 0.6)
		else
			box(Fk, "Wall", -ww, ww, 0, TOP, -RW - 2, -RW, K.wall)
		end
		-- the galleries: level 2 from the void's edge out, level 3 from further out; fascias, glass rails
		for _, lv in { { RV, Y2 }, { RV3, Y3 } } do
			local r0, y = lv[1], lv[2]
			box(Fk, "Gallery", -hw(r0), hw(r0), y - 1, y, -RW, -r0, K.floor2)
			slant(Fk, "Gallery", -hw(r0), -hw(RW), -r0, -RW, y - 1, y, K.floor2); slant(Fk, "Gallery", hw(r0), hw(RW), -r0, -RW, y - 1, y, K.floor2)
			box(Fk, "GalleryFascia", -hw(r0), hw(r0), y - 1.5, y + 0.3, -r0 - 0.05, -r0 + 0.6, K.trim)
			box(Fk, "GalleryRail", -hw(r0 - 0.4), hw(r0 - 0.4), y + 0.3, y + 3.4, -r0 + 0.1, -r0 + 0.35, K.glass, MAT.Glass, { tr = 0.6 })
			box(Fk, "GalleryRailTop", -hw(r0 - 0.4), hw(r0 - 0.4), y + 3.4, y + 3.8, -r0 + 0.05, -r0 + 0.4, K.trim)
			panel(Fk, 0, y - 1, -(r0 + RW) / 2 - 1, 7, 5, 0.45)
		end
		box(Fk, "Roof", -hw(RV), hw(RV), TOP, TOP + 1, -RW - 2, -RV, K.ceil)
		slant(Fk, "Roof", -hw(RV), -hw(RW + 2), -RV, -RW - 2, TOP, TOP + 1, K.ceil); slant(Fk, "Roof", hw(RV), hw(RW + 2), -RV, -RW - 2, TOP, TOP + 1, K.ceil)
		panel(Fk, 0, TOP, -(RV3 + RW) / 2, 8, 5, 0.5)
		-- a column at each corner of the void, up to the roof
		local a = math.rad(b + 22.5)
		local rc = RV / math.cos(math.rad(22.5)) + 0.6
		cyl(F0, "Column", math.sin(a) * rc, 0, TOP, -math.cos(a) * rc, 2, K.col)
		rod(F0, "RoofRib", Vector3.new(0, TOP - 0.6, 0), Vector3.new(math.sin(a) * rc, TOP - 0.6, -math.cos(a) * rc), 0.9, K.trim)
	end
	box(F0, "Skylight", -RV, RV, TOP + 0.2, TOP + 0.4, -RV, RV, K.light, MAT.Neon, { noshadow = true })
	-- the ten pads on the ground ring: W, NW, N, NE, E sides, two each (west to east 1v1 .. 4v4 | 4v4 .. 1v1)
	local order = { 1, 2, 3, 4, 5, 5, 4, 3, 2, 1 }
	local join = { 0, 0, 3, 0, 6, 0, 2, 0, 0, 1 }
	local k = 0
	for _, b in { 270, 315, 0, 45, 90 } do
		for _, left in { true, false } do
			k += 1
			padPlatform(sideF(b), left, MODES[order[k]], join[k], 24, 38.5)
			local a = math.rad(b + (if left then -11 else 11))
			table.insert(L, { MODES[order[k]].title, math.sin(a) * 31, -math.cos(a) * 31 })
		end
	end
	-- the middle: a round seating island under the hanging screen, jump pads up to level 2
	cyl(F0, "Island", 0, 0, 0.5, 0, 17, K.trim2)
	cyl(F0, "IslandPlanter", 0, 0.5, 2.8, 0, 7, K.trim); cyl(F0, "IslandSoil", 0, 2.8, 2.85, 0, 6.4, K.soil)
	for i = 0, 4 do ball(F0, "Bush", math.cos(i * 1.26) * 1.8, 4.2, math.sin(i * 1.26) * 1.8, 3.4, if i % 2 == 0 then K.plant else K.plant2, MAT.Grass) end
	for i = 0, 7 do
		local a = i * math.pi / 4
		local Fb = CFrame.new(math.sin(a) * 6, 0.5, -math.cos(a) * 6) * CFrame.Angles(0, -a, 0)
		box(Fb, "IslandBench", -1.8, 1.8, 0, 1.0, -0.8, 0.8, K.wood, MAT.Wood)
		if i % 3 ~= 1 then person(Fb * CFrame.new(0, -0.45, 0.3), true) end
	end
	local cube = box(F0, "ScreenCube", -8, 8, 20, 28, -8, 8, K.screen)
	for _, f in { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right } do text(cube, f, SCREEN_LINES, { pps = 20, bright = 2 }) end
	glow(cube, 30, 0.6, "9fd0ff")
	box(F0, "ScreenCubeCap", -8.4, 8.4, 28, 28.6, -8.4, 8.4, K.trim2); box(F0, "ScreenCubeFoot", -8.4, 8.4, 19.4, 20, -8.4, 8.4, K.trim2)
	for _, s in { -1, 1 } do cyl(F0, "ScreenRod", s * 5, 28.6, TOP, s * 5, 0.35, K.steel) end
	for _, b in { 160, 200 } do jumpPad(CFrame.new(math.sin(math.rad(b)) * 13, 0, -math.cos(math.rad(b)) * 13)) end
	-- the spawn, under the south gallery, facing the middle
	cyl(F0, "SpawnRing", 0, 0, 0.05, 31, 11.6, K.trim2); cyl(F0, "SpawnRug", 0, 0, 0.08, 31, 11, K.carpet2, MAT.Fabric)
	trophyCase(at(sideF(180), 0, -39, 180)); for _, x in { -9, 9 } do bundle(at(sideF(180), x, -36.5, 180)) end
	-- level 2, the lounge: the shop (S), tables (SW, E), arcade (W), seats (NW, NE), code panel (N), the gym window (SE)
	local function L2(b, x, z, yaw) return at(sideF(b), x, z, yaw, Y2) end
	shop(L2(180, 0, -35.2, 180), 14); regular(L2(180, 0, -37.4, 180), "Looticus")
	chess(L2(225, -4.5, -30, 0), true); chess(L2(225, 5, -31, 90), false)
	for i, x in { -3.6, 0, 3.6 } do arcade(L2(270, x, -38.6, 180), i ~= 2) end
	cluster(L2(315, 0, -31, 0), 3); cluster(L2(45, 0, -31, 0), 2)
	codePanel(L2(0, 0, -40, 180))
	armTable(L2(90, -4, -30, 90), true); armTable(L2(90, 5, -31, 90), false)
	box(sideF(135), "GymWindow", -12, 12, Y2 + 1.5, Y2 + 9, -RW - 0.3, -RW + 0.1, K.glass, MAT.Glass, { tr = 0.5 })
	box(sideF(135), "Wall", -12, 12, Y2, Y2 + 1.5, -RW - 2, -RW, K.wall)
	for i, x in { -6, 0, 6 } do
		box(sideF(135), "WatchBench", x - 2.2, x + 2.2, Y2, Y2 + 1.45, -RW + 3.5, -RW + 5, K.wood, MAT.Wood)
		person(at(sideF(135), x - 0.8, -RW + 4.2, 0, Y2), true)
	end
	-- level 3: VIP behind glass (N), the ranked boards and Frisk (NW, NE), YOUR LOADOUT (W) and MASTERY (E), seats (S)
	local function L3(b, x, z, yaw) return at(sideF(b), x, z, yaw, Y3) end
	local Fv = sideF(0)
	box(Fv, "VipGlass", -12, 12, Y3, Y3 + 11, -30.4, -30, K.glass, MAT.Glass, { tr = 0.5 })
	for _, s in { -1, 1 } do box(Fv, "VipDoorPost", s * 2.6, s * 3.4, Y3, Y3 + 9, -30.6, -29.8, K.gold, MAT.Metal) end
	local vsn = box(Fv, "VipSign", -3.4, 3.4, Y3 + 9, Y3 + 10.6, -30.6, -29.8, K.screen); text(vsn, Enum.NormalId.Back, { { "VIP", K.gold, 0.8 } })
	box(Fv, "VipFloor", -hw(30), hw(30), Y3, Y3 + 0.06, -40, -30.4, K.plum, MAT.Fabric)
	cyl(Fv, "DuckPlinth", 0, Y3, Y3 + 2, -37, 4, K.dark); duck(at(Fv, 0, -37, 0, Y3 + 2), 1.1)
	sofa(at(Fv, -7, -35, 90, Y3), 5, K.plum, 0); regular(at(Fv, 7, -34.5, -90, Y3), "Trisangle")
	board(L3(315, 0, -39.9, 180), "DUELS"); board(L3(45, 0, -39.9, 180), "PARTIES"); regular(L3(315, 4, -34, 180), "Frisk1636")
	holo(L3(270, 0, -33, 0), "loadout"); holo(L3(90, 0, -33, 0), "mastery")
	cluster(L3(180, 0, -33, 180), 2)
	-- the gym through the SE portal, the locker room past it; the armory through the SW one
	local Fg = sideF(135)
	box(Fg, "GymFloor", -34, 34, -1, 0, -108, -42, K.gymFloor, MAT.Rubber)
	box(Fg, "Wall", -36, -34, 0, 25, -110, -42, K.gymWall); box(Fg, "Wall", 34, 36, 0, 25, -110, -42, K.gymWall); box(Fg, "Wall", -36, 36, 0, 25, -110, -108, K.gymWall)
	box(Fg, "Roof", -36, 36, 25, 26, -110, -42, K.ceil)
	for _, p in { { -14, -61 }, { 14, -61 }, { -14, -87 }, { 14, -87 } } do ring(at(Fg, p[1], p[2], 0), 20); ringLights(Fg, p[1], p[2], 18) end
	bags(Fg, -30, -4, -105.5); bags(Fg, 4, 20, -105.5)
	for _, z in { -55, -75, -95 } do panel(Fg, 0, 25, z, 12, 3) end
	regular(at(Fg, 10, -46, 0), "Dune")
	for i, p in { { -14, -57 }, { -13, -66 }, { 14, -84 } } do person(at(Fg, p[1], p[2], i * 130, 1.36), false) end
	box(Fg, "Floor", 36, 60, -1, 0, -100, -60, "a9adb2", MAT.CeramicTiles)
	box(Fg, "Wall", 60, 62, 0, 13, -102, -58, K.gymWall); box(Fg, "Wall", 36, 62, 0, 13, -102, -100, K.gymWall); box(Fg, "Wall", 36, 62, 0, 13, -60, -58, K.gymWall)
	box(Fg, "Roof", 36, 62, 13, 14, -102, -58, K.ceil)
	lockerBank(at(Fg, 59.9, -80, -90), 36)
	local Fa = sideF(225)
	box(Fa, "Floor", -16, 16, -1, 0, -76, -42, K.floor2)
	box(Fa, "Wall", -18, -16, 0, 15, -78, -42, K.wall); box(Fa, "Wall", 16, 18, 0, 15, -78, -42, K.wall); box(Fa, "Wall", -18, 18, 0, 15, -78, -76, K.wall)
	box(Fa, "Roof", -18, 18, 15, 16, -78, -42, K.ceil)
	weaponWall(at(Fa, -15.9, -58, -90), 28); weaponWall(at(Fa, 15.9, -58, 90), 28)
	trainingGate(at(Fa, 0, -75.9, 0))
	panel(Fa, 0, 15, -58, 10, 20)
	-- people about the ground ring and at the rails
	for i, p in { { -6, 22, 200 }, { 8, 20, 160 }, { -20, 4, 80 }, { 21, -4, 270 }, { -12, -18, 30 }, { 12, -19, 330 }, { 3, 12, 0 } } do person(at(F0, p[1], p[2], p[3]), false) end
	for _, b in { 200, 240, 300, 20, 60, 120 } do
		local a = math.rad(b)
		person(CFrame.new(math.sin(a) * (RV + 1.4), Y2, -math.cos(a) * (RV + 1.4)) * CFrame.Angles(0, -a + math.pi, 0), false)
	end
	for _, b in { 160, 250, 110 } do
		local a = math.rad(b)
		person(CFrame.new(math.sin(a) * (RV3 + 1.4), Y3, -math.cos(a) * (RV3 + 1.4)) * CFrame.Angles(0, -a + math.pi, 0), false)
	end
	for _, l in { { "SPAWN", 0, 31 }, { "SCREEN + SEATS", 0, 0 }, { "GYM 4 RINGS", 52, 52 }, { "LOCKERS", 66, 25 }, { "ARMORY", -45, 45 }, { "TRAINING", -54, 54 },
		{ "TROPHIES + BUNDLES", 0, 38 } } do table.insert(L, l) end
	shot(S, "spawn", Vector3.new(0, 5.4, 34), Vector3.new(0, 11, -12))
	shot(S, "gym", Vector3.new(-8, 6.2, 2), Vector3.new(46, 4, 46))
	shot(S, "level2", Vector3.new(-7, Y2 + 5.4, 34), Vector3.new(8, Y2 - 2, -20))
	local Fp = sideF(315) * CFrame.new(-5, 0, -31)
	shot(S, "pad_on", (sideF(315) * CFrame.new(-5, 7, -15)).Position, (sideF(315) * CFrame.new(-5, 1.5, -33)).Position)
	shot(S, "pad_off", (sideF(45) * CFrame.new(5, 7, -15)).Position, (sideF(45) * CFrame.new(5, 1.5, -33)).Position)
	return { labels = L, shots = S, plan = { c = W(Vector3.new(14, 0, 14)), h = 150 }, levels = "L2 (lounge): shop, tables, arcade, seats, gym window   L3: VIP, ranked boards, loadout + mastery" }
end

-- C: THE SQUARE ---------------------------------------------------------------------------------------
function HC.C()
	begin("C")
	local F0 = CFrame.new()
	local L, S = {}, {}
	local TOP = 34
	box(F0, "Floor", -34, 34, -1, 0, -34, 34, K.paving, MAT.Slate)
	-- the square's four sides, each a wide opening in a thin frame with its name over it; a gallery round at 12
	local OPEN = { N = { -18, 18, "PADS" }, S = { -20, 20, "LOUNGE  ·  SHOP  ·  VIP" }, E = { -20, 20, "GYM" }, W = { -12, 12, "ARMORY  ·  TRAINING" } }
	local OH = 11
	for side, o in OPEN do
		local F = if side == "N" then CFrame.new() elseif side == "S" then CFrame.Angles(0, math.pi, 0) elseif side == "E" then CFrame.Angles(0, -math.pi / 2, 0) else CFrame.Angles(0, math.pi / 2, 0)
		box(F, "Wall", -34, o[1], 0, TOP, -34, -32, K.wall); box(F, "Wall", o[2], 34, 0, TOP, -34, -32, K.wall); box(F, "Wall", o[1], o[2], OH, TOP, -34, -32, K.wall)
		for _, x in { o[1], o[2] } do box(F, "OpeningFrame", x - 0.25, x + 0.25, 0, OH + 0.3, -32.3, -31.8, K.steel) end
		box(F, "OpeningFrame", o[1] - 0.25, o[2] + 0.25, OH, OH + 0.3, -32.3, -31.8, K.steel)
		local hl = box(F, "OpeningLight", o[1] + 0.3, o[2] - 0.3, OH - 0.2, OH, -32.2, -31.9, K.light, MAT.Neon, { noshadow = true })
		glow(hl, 14, 0.5)
		local sg = box(F, "OpeningSign", (o[1] + o[2]) / 2 - 9, (o[1] + o[2]) / 2 + 9, OH + 2.6, OH + 4.6, -32.2, -32, K.screen)
		text(sg, Enum.NormalId.Back, { { o[3], K.pale, 0.75 } })
		local gx = if side == "N" or side == "S" then 32 else 26 -- (the corners belong to the north and south ones)
		box(F, "Gallery", -gx, gx, 11.6, 12.6, -32, -26, K.floor2)
		box(F, "GalleryFascia", -26.3, 26.3, 11.2, 12.9, -26.3, -25.7, K.trim)
		box(F, "GalleryRail", -25.9, 25.9, 12.9, 16, -26.1, -25.8, K.glass, MAT.Glass, { tr = 0.6 })
		box(F, "GalleryRailTop", -26, 26, 16, 16.4, -26.15, -25.75, K.trim)
		for _, x in { -24, -12, 12, 24 } do box(F, "Column", x - 0.9, x + 0.9, 0, 11.6, -26.9, -25.1, K.col) end
	end
	box(F0, "Roof", -34, 34, TOP, TOP + 1, -34, 34, K.ceil)
	for v = -24, 24, 8 do
		box(F0, "RoofBeam", -32, 32, TOP - 2, TOP, v - 0.5, v + 0.5, K.trim); box(F0, "RoofBeam", v - 0.5, v + 0.5, TOP - 2, TOP, -32, 32, K.trim)
	end
	for x = -20, 20, 8 do for z = -20, 20, 8 do panel(F0, x, TOP, z, 6.6, 6.6, 0.35) end end
	-- the middle: the screen tower on a planter with a bench ring
	box(F0, "Tower", -3, 3, 0, 24, -3, 3, K.col)
	local sc = box(F0, "TowerScreen", -6.5, 6.5, 14, 21, -6.5, 6.5, K.screen)
	for _, f in { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right } do text(sc, f, SCREEN_LINES, { pps = 22, bright = 2 }) end
	glow(sc, 30, 0.6, "9fd0ff")
	box(F0, "TowerCap", -7, 7, 21, 21.8, -7, 7, K.trim2); box(F0, "TowerFoot", -7, 7, 13.2, 14, -7, 7, K.trim2)
	cyl(F0, "TowerPlanter", 0, 0, 2.4, 0, 13, K.trim); cyl(F0, "TowerSoil", 0, 2.4, 2.45, 0, 12.2, K.soil)
	for i = 0, 7 do ball(F0, "Bush", math.cos(i * 0.785) * 4.8, 3.4, math.sin(i * 0.785) * 4.8, 2.8, if i % 2 == 0 then K.plant else K.plant2, MAT.Grass) end
	for i = 0, 7 do
		local a = i * math.pi / 4 + math.pi / 8
		local Fb = CFrame.new(math.sin(a) * 8.2, 0, -math.cos(a) * 8.2) * CFrame.Angles(0, -a, 0)
		box(Fb, "TowerBench", -2.2, 2.2, 0, 1.45, -0.8, 0.8, K.wood, MAT.Wood)
		if i % 2 == 0 then person(Fb * CFrame.new(0, 0, 0.1), true) end
	end
	-- the corners: YOUR LOADOUT (NE), MASTERY (NW), the bundles (SW), seats (SE); planters by the walls; jump pads
	holo(at(F0, 21, -21, 225), "loadout"); holo(at(F0, -21, -21, 135), "mastery")
	for _, p in { { -26, 15 }, { -21, 21 }, { -15, 26 } } do bundle(at(F0, p[1], p[2], 45)) end
	cluster(at(F0, 20, 20, -45), 3); regular(at(F0, 13, 15, 200), "Dune")
	for _, s in { -1, 1 } do jumpPad(at(F0, s * 12, -12, 0)) end
	cyl(F0, "SpawnRing", 0, 0, 0.05, 22, 11.6, K.trim2); cyl(F0, "SpawnRug", 0, 0, 0.08, 22, 11, K.carpet2, MAT.Fabric)
	-- the pads' gallery north: ten gates in its walls, five a side, 1v1 nearest the square .. 4v4 at the far end
	local WZ0, WZ1 = -34, -100
	box(F0, "Floor", -27, 27, -1, 0, WZ1 - 2, WZ0, K.floor2)
	box(F0, "Runner", -6, 6, 0, 0.04, WZ1 + 2, WZ0, K.runner, MAT.Fabric)
	box(F0, "Roof", -27, 27, 20, 21, WZ1 - 2, WZ0, K.ceil)
	box(F0, "Wall", -27, 27, 0, 20, WZ1 - 2, WZ1, K.wall)
	local GZ = { -44, -56, -68, -80, -92 }
	local GJ = { [-1] = { 0, 0, 3, 0, 4 }, [1] = { 1, 0, 0, 2, 0 } }
	for _, s in { -1, 1 } do
		box(F0, "Wall", s * 25, s * 27, 0, 20, WZ1, WZ0, K.wall)
		local edges = { WZ0 }
		for _, zc in GZ do table.insert(edges, zc + 5); table.insert(edges, zc - 5) end
		table.insert(edges, WZ1)
		for i = 1, #edges, 2 do box(F0, "GateFin", s * 20, s * 25, 0, 20, edges[i + 1], edges[i], K.wall2) end
		for k, zc in GZ do
			box(F0, "Wall", s * 20, s * 25, 11, 20, zc - 5, zc + 5, K.wall2)
			padGate(CFrame.lookAt(Vector3.new(s * 20, 0, zc), Vector3.new(s * 21, 0, zc)), MODES[k], GJ[s][k])
			table.insert(L, { MODES[k].title, s * 22.5, zc })
		end
	end
	for z = -44, -92, -12 do panel(F0, 0, 20, z, 8, 6) end
	board(at(F0, -7, WZ1 + 0.1, 0), "DUELS"); board(at(F0, 7, WZ1 + 0.1, 0), "PARTIES")
	trophyCase(at(F0, 0, WZ1 + 5, 0)); regular(at(F0, -10, WZ1 + 6, 180), "Frisk1636")
	for i, p in { { -4, -50, 90 }, { 5, -62, 270 }, { -3, -75, 120 }, { 6, -88, 300 } } do person(at(F0, p[1], p[2], p[3]), false) end
	-- the gym east, straight through its opening; the locker room off its south wall
	box(F0, "GymFloor", 34, 98, -1, 0, -32, 32, K.gymFloor, MAT.Rubber)
	box(F0, "Wall", 98, 100, 0, 24, -34, 34, K.gymWall); box(F0, "Wall", 34, 100, 0, 24, -34, -32, K.gymWall)
	box(F0, "Wall", 34, 82, 0, 24, 32, 34, K.gymWall); box(F0, "Wall", 90, 100, 0, 24, 32, 34, K.gymWall); box(F0, "Wall", 82, 90, 10, 24, 32, 34, K.gymWall)
	box(F0, "Roof", 34, 100, 24, 25, -34, 34, K.ceil)
	for _, p in { { 52, -13 }, { 80, -13 }, { 52, 13 }, { 80, 13 } } do ring(at(F0, p[1], p[2], 90), 20); ringLights(at(F0, p[1], p[2], 90), 0, 0, 18) end
	bags(at(F0, 96, 0, 90), -26, 26, 0)
	for _, x in { 52, 80 } do panel(F0, x, 24, 0, 3, 10) end
	for i, p in { { 52, -9 }, { 54, -17 }, { 80, 16 } } do person(at(F0, p[1], p[2], i * 100, 1.36), false) end
	box(F0, "Floor", 60, 98, -1, 0, 34, 60, "a9adb2", MAT.CeramicTiles)
	box(F0, "Wall", 58, 60, 0, 13, 34, 62, K.gymWall); box(F0, "Wall", 98, 100, 0, 13, 34, 62, K.gymWall); box(F0, "Wall", 58, 100, 0, 13, 60, 62, K.gymWall)
	box(F0, "Roof", 58, 100, 13, 14, 34, 62, K.ceil)
	lockerBank(at(F0, 79, 59.9, 0), 36)
	-- the armory west, the training gate at its far end
	box(F0, "Floor", -76, -34, -1, 0, -22, 22, K.floor2)
	box(F0, "Wall", -78, -76, 0, 15, -24, 24, K.wall); box(F0, "Wall", -78, -34, 0, 15, -24, -22, K.wall); box(F0, "Wall", -78, -34, 0, 15, 22, 24, K.wall)
	box(F0, "Roof", -78, -34, 15, 16, -24, 24, K.ceil)
	weaponWall(at(F0, -55, -21.9, 180), 34); weaponWall(at(F0, -55, 21.9, 0), 34)
	trainingGate(at(F0, -75.9, 0, -90))
	panel(F0, -55, 15, 0, 26, 6)
	for i = 1, 3 do person(at(F0, -62 + i * 6, -17, 180), false) end
	-- the lounge street south: the shop (east side), the arcade and the code panel (west wall), the tables, seats; VIP at its end
	box(F0, "Floor", -26, 26, -1, 0, 34, 84, K.floor)
	box(F0, "Runner", -5, 5, 0, 0.04, 34, 82, K.carpet, MAT.Fabric)
	box(F0, "Wall", -28, -26, 0, 17, 34, 86, K.wall); box(F0, "Wall", 26, 28, 0, 17, 34, 86, K.wall)
	box(F0, "Roof", -28, 28, 17, 18, 34, 86, K.ceil)
	for z = 42, 78, 9 do panel(F0, 0, 17, z, 10, 4) end
	shop(at(F0, 21.5, 52, 90), 18); regular(at(F0, 23.6, 52, 90), "Looticus")
	for i, z in { 40, 43.6, 47.2 } do arcade(at(F0, -24.6, z, -90), i ~= 2) end
	codePanel(at(F0, -26, 62, -90))
	chess(at(F0, -10, 46, 0), true); chess(at(F0, -10, 56, 90), false); armTable(at(F0, 8, 46, 0), true); armTable(at(F0, 8, 56, 0), false)
	cluster(at(F0, -15, 72, 90), 3); cluster(at(F0, 14, 73, -90), 2)
	for _, s in { -1, 1 } do
		box(F0, "Wall", s * 16, s * 28, 0, 17, 84, 86, K.wall)
		box(F0, "Wall", s * 5.6, s * 16, 0, 2, 84, 86, K.wall); box(F0, "Wall", s * 5.6, s * 16, 9, 17, 84, 86, K.wall)
		box(F0, "VipWindow", s * 5.6, s * 16, 2, 9, 84.8, 85.2, K.glass, MAT.Glass, { tr = 0.55 })
		box(F0, "VipDoorPost", s * 5.6, s * 6.4, 0, 11.4, 83.4, 84, K.gold, MAT.Metal)
	end
	box(F0, "Wall", -5.6, 5.6, 10.6, 17, 84, 86, K.wall)
	local vs = box(F0, "VipSign", -5.6, 5.6, 11.6, 13.4, 83.4, 84, K.screen); text(vs, Enum.NormalId.Front, { { "VIP", K.gold, 0.8 } })
	box(F0, "Floor", -18, 18, -1, 0, 86, 110, K.plum, MAT.Fabric)
	box(F0, "Wall", -20, -18, 0, 15, 86, 112, K.wall); box(F0, "Wall", 18, 20, 0, 15, 86, 112, K.wall); box(F0, "Wall", -20, 20, 0, 15, 110, 112, K.wall)
	box(F0, "Roof", -20, 20, 15, 16, 86, 112, K.ceil)
	cyl(F0, "DuckPlinth", 0, 0, 2.4, 104, 5, K.dark); duck(at(F0, 0, 104, 180, 2.4), 1.4)
	sofa(at(F0, -12, 96, -90), 7, K.plum, 1); regular(at(F0, 9, 96, 90), "Trisangle")
	panel(F0, 0, 15, 96, 8, 8, 0.7)
	-- people in the square and on its gallery
	for i, p in { { -8, 14, 160 }, { 9, 10, 200 }, { -16, 2, 80 }, { 17, -6, 260 }, { -10, -16, 20 }, { 8, -20, 340 }, { 24, 4, 270 }, { -24, -4, 90 } } do person(at(F0, p[1], p[2], p[3]), false) end
	for _, p in { { -14, -28, 180 }, { 10, -28, 180 }, { 28, -10, 270 }, { 28, 14, 270 }, { -28, 8, 90 }, { 14, 28, 0 } } do person(at(F0, p[1], p[2], p[3], 12.6), false) end
	for _, l in { { "SPAWN", 0, 22 }, { "SCREEN TOWER", 0, 0 }, { "LOADOUT", 21, -21 }, { "MASTERY", -21, -21 }, { "BUNDLES", -21, 21 }, { "GYM 4 RINGS", 66, 0 },
		{ "LOCKERS", 79, 47 }, { "ARMORY", -55, 0 }, { "TRAINING", -72, 8 }, { "SHOP", 21, 52 }, { "ARCADE", -22, 44 }, { "TABLES", -1, 51 }, { "CODE", -22, 62 },
		{ "VIP", 0, 98 }, { "RANKED + TROPHIES", 0, -95 } } do table.insert(L, l) end
	shot(S, "spawn", Vector3.new(0, 5.4, 26), Vector3.new(0, 9.5, -20))
	shot(S, "gym", Vector3.new(6, 6.2, 6), Vector3.new(70, 3, -2))
	shot(S, "lounge", Vector3.new(-2, 6.2, 36), Vector3.new(4, 4, 82))
	shot(S, "pad_on", Vector3.new(9, 5.8, -60), Vector3.new(-24, 4, -68))
	shot(S, "pad_off", Vector3.new(9, 5.8, -72), Vector3.new(-24, 4, -80))
	return { labels = L, shots = S, plan = { c = W(Vector3.new(10, 0, 0)), h = 175 } }
end

function HC.build(name) return (HC :: any)[name]() end
-- hide what is over head height in a concept, for its plan (they're removed after anyway)
function HC.planCut(name, above)
	local f = workspace:FindFirstChild("HubConcepts")
	local r = f and f:FindFirstChild(name)
	if not r then return 0 end
	local n, y0 = 0, HC.SITES[name].Y + (above or 11)
	for _, p in r:GetDescendants() do
		if p:IsA("BasePart") and p.Position.Y - p.Size.Y / 2 > y0 then p:Destroy(); n += 1 end
	end
	for _, m in r:GetChildren() do if m:IsA("Model") then local cf, s = m:GetBoundingBox(); if cf.Y - s.Y / 2 > y0 then m:Destroy() end end end
	return n
end
function HC.clear() local f = workspace:FindFirstChild("HubConcepts"); if f then f:Destroy() end end
return HC
