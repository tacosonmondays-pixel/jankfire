--!nonstrict
-- HUBKIT: the shared kit the three hubs are built from (20 Nov 2026; the owner on the concepts sheet: "can you model all
-- 3 and let me have an option to travel between hubs"). C THE SQUARE (HubSquare), A THE CONCOURSE (HubConcourse), B THE
-- ATRIUM (HubAtrium) each compose their architecture from these parts and features. World studs, no warp. The
-- convention every hub follows (folders, markers, the Hub attribute) is side-session-notes/HUB-MARKERS.md.
--
-- A build: K.begin(folder, site) clears and makes `folder` (Map.Hub.<Name> live, or a staging folder) with Shell
-- (architecture: collides) and Scenery (things and markers: no collisions unless o.solid), QueuePads, HubSpawns,
-- HubArrive; frames are CFrames in the site's space (x east, z south, y up; a frame's look is its -Z, as Roblox's).
-- Every part a hub makes goes through K.box / K.cyl / ... so the counts and the flicker finder see it all.
local K = {}

K.P = { -- the hubs' palette: the ring's greys and creams, one brown, quiet floors; colour only on pads, signs, one accent
	shell = "535a66", shell2 = "5c636f", wall = "6a727e", wall2 = "5f6773", pier = "68707c", pier2 = "747c88", dome = "727a86",
	cream = "b3aea4", creamHi = "c4bfb5", brown = "5c4d42", wood = "8a6e55", woodDark = "5c4d42",
	floor = "5c616a", floor2 = "50555d", paving = "6e737b", paving2 = "62676f", carpet = "4f4846", carpet2 = "5a4f4a", runner = "4a4644",
	steel = "3a3f47", steel2 = "2d3138", dark = "2a2d33", screen = "15181d", glass = "a9bcc4", light = "f4f1ea", warm = "ffd7a0",
	pale = "e8ecef", amber = "e9a64a", gold = "c9a45a", plum = "4b4048", padBase = "474c54", plant = "5f7a58", plant2 = "6a8562",
	soil = "3d3631", gymFloor = "4c515a", gymWall = "c4c0b6", canvas = "d9d4c8", tile = "a9adb2", tileW = "d6d6d2", holo = "8fd8ff",
	wallLt = "8e8c86", wallLt2 = "7f7d78", creamWall = "c4c0b6", ply = "a08868", plank = "8c7454", conc = "77746c",
}
K.TEAM = { "ff5ad2", "40d0ff", "e9a64a" } -- (the teams' colours: thin rims and lights only)
K.MODES = {
	{ id = "1v1", title = "1V1", kind = "DUEL", size = 1, teams = 2 }, { id = "1v1v1", title = "1V1V1", kind = "FREE FOR ALL", size = 1, teams = 3 },
	{ id = "2v2", title = "2V2", kind = "DUOS", size = 2, teams = 2 }, { id = "3v3", title = "3V3", kind = "TRIOS", size = 3, teams = 2 },
	{ id = "4v4", title = "4V4", kind = "SQUADS", size = 4, teams = 2 },
}
local MAT = Enum.Material
local SP = MAT.SmoothPlastic
K.MAT = MAT
local Tags = game:GetService("CollectionService")
K.Tags = Tags

-- ------------------------------------------------------------------------------------------------ the style switch
-- (20 Nov 2026, the owner once the three hubs were in: "This current hub reads less like the old one, last one felt more
-- like robals with the old design phisophies"; main: rework each hub in the ring's look language, the first look one
-- switch away.) A hub names its style in K.begin's attrs (Style): "warm" = the hubs as first built (one sand family,
-- grainy floors, wood); "rivals" = the ring's language (vault: Design principles 1-3, For hubs): a cool two-tone, pale
-- structure on slate walls and floors, every surface SmoothPlastic, dim but for the lamps, signs, screens and pads.
-- K.part repaints by hex through K.RIVALS (so every kit piece follows) and drops the grainy materials; the rivals-only
-- pieces (K.portal, K.wordSign, K.drum, K.coffers, K.haunch, K.floorLine, K.nameBand, K.infoScreen) and the hubs'
-- own changes sit behind K.rivals(). attrs.Accent: the hub's one accent (seats, the floor's arrows, the signs' bars)
K.R = { -- the rivals palette, for the new pieces
	struct = "d6d5d0", structHi = "e6e5e1", wall = "666b74", wall2 = "5b6068", floor = "4c525b", floor2 = "434851",
	ceil = "52575e", line = "c9c7c1", dark = "3a3e45", screen = "15181d", light = "f5f7fa", slat = "dfe6ee", cool = "e6edf7",
}
K.RIVALS = {
	-- walls: slate
	["8e8c86"] = "666b74", ["7f7d78"] = "5b6068", ["c4c0b6"] = "6b7078", ["77746c"] = "6c7178", ["6c6862"] = "5c6168",
	-- structure: off-white, paler than the walls
	["b3aea4"] = "d6d5d0", ["c4bfb5"] = "e6e5e1", ["68707c"] = "c9cacd", ["747c88"] = "d2d3d5",
	-- floors: calm slate
	["6e737b"] = "4f555e", ["62676f"] = "454a52", ["50555d"] = "4a4f58", ["5c616a"] = "51565f", ["4a4644"] = "42464e", ["4f4846"] = "454950",
	-- ceilings, steel and the darks: mid values, nothing near black
	["727a86"] = "52575e", ["3a3f47"] = "50555d", ["2d3138"] = "464a51", ["2a2d33"] = "3a3e45", ["3a3d42"] = "40444b",
	-- the wood and the browns: pale grey and slate (no brown at all)
	["8a6e55"] = "a9acb0", ["5c4d42"] = "4a4e55", ["4b4048"] = "4c5057",
	-- seats: the hub's accent
	["5a4f4a"] = "accent", ["5e6470"] = "accent",
	-- the lamps' white: a touch cooler
	["f4f1ea"] = "f5f7fa",
}
local KEEP_MAT = { [MAT.Neon] = true, [MAT.Glass] = true, [MAT.ForceField] = true }

local S = { root = nil :: Folder?, site = CFrame.new(), hub = "", count = 0, lamps = 0, style = "warm", accent = "a65a3e" }
K.S = S
function K.rivals() return S.style == "rivals" end
local function c3(h) return Color3.fromHex(h) end
K.c3 = c3

-- ------------------------------------------------------------------------------------------------ the build's folders
function K.begin(parent: Instance, name: string, site: CFrame, hubId: string, attrs, live: boolean?)
	local old = parent:FindFirstChild(name); if old then old:Destroy() end
	local f = Instance.new("Folder"); f.Name = name
	f:SetAttribute("Hub", hubId)
	f:SetAttribute("Site", site.Position) -- (HubTravel: which hub a player is in, by the nearest site)
	for k, v in attrs or {} do f:SetAttribute(k, v) end
	for _, n in { "Shell", "Scenery", "QueuePads", "HubSpawns", "HubArrive" } do
		local c = Instance.new("Folder"); c.Name = n; c.Parent = f
	end
	S.root = f; S.site = site; S.hub = hubId; S.count = 0; S.lamps = 0; S.live = live == true; S.missing = 0
	S.style = (attrs and attrs.Style) or "warm"; S.accent = (attrs and attrs.Accent) or "a65a3e"
	if not live then f:SetAttribute("MiniGamesOff", true) end -- (hub-minigames builds nothing on a staging copy)
	if live then -- (a live build drops its old look zone: K.lookZone makes a new one if the hub wants it)
		local zf = parent:FindFirstChild("LookZones")
		local oz = zf and zf:FindFirstChild(name)
		if oz then oz:Destroy() end
	end
	f.Parent = parent
	return f
end
-- the hub's own light (HubLife: a part in Map.Hub.LookZones with the attribute Look names the look for whoever stands in
-- it; HubLook.looks[look]): a box x0..x1, y0..y1, z0..z1 in the site's frame. live builds only
function K.lookZone(look, x0, x1, y0, y1, z0, z1)
	if not S.live then return nil end
	local root = S.root :: Folder
	local hub = root.Parent :: Instance
	local zf = hub:FindFirstChild("LookZones")
	if not zf then zf = Instance.new("Folder"); zf.Name = "LookZones"; zf.Parent = hub end
	local p = Instance.new("Part"); p.Name = root.Name
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false; p.Transparency = 1
	p.Size = Vector3.new(x1 - x0, y1 - y0, z1 - z0); p.CFrame = S.site * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
	p:SetAttribute("Look", look); p:SetAttribute("Hub", S.hub)
	p.Parent = zf
	return p
end
function K.folder(name) return (S.root :: Folder):FindFirstChild(name) end

-- ------------------------------------------------------------------------------------------------ parts
-- o: tr, refl, shape, noshadow, solid (Scenery that collides), ghost (no collide, no query, no touch), parent, cls
function K.part(folder, name, cf, size, hex, mat, o)
	o = o or {}
	local p = Instance.new(o.cls or "Part")
	if S.style == "rivals" then -- (the style switch: the repaint, no grainy materials)
		local r = K.RIVALS[hex]
		if r == "accent" then hex = S.accent elseif r then hex = r end
		if mat and not KEEP_MAT[mat] then mat = SP end
	end
	p.Name = name; p.Anchored = true; p.Size = size; p.CFrame = S.site * cf
	p.Color = c3(hex); p.Material = mat or SP
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	if o.tr then p.Transparency = o.tr end
	if o.refl then p.Reflectance = o.refl end
	if o.shape then p.Shape = o.shape end
	if o.noshadow then p.CastShadow = false end
	local isShell = folder == "Shell"
	p.CanCollide = if o.ghost then false elseif o.solid ~= nil then o.solid else isShell
	if o.ghost then p.CanQuery = false; p.CanTouch = false end
	p:SetAttribute("Hub", S.hub)
	p.Parent = o.parent or (S.root :: Folder):FindFirstChild(folder) or S.root
	S.count += 1
	return p
end
-- a box in frame F from x0..x1, y0..y1, z0..z1 (F's own axes)
function K.box(F, folder, name, x0, x1, y0, y1, z0, z1, hex, mat, o)
	return K.part(folder, name, F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
		Vector3.new(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(z1 - z0), 0.05)), hex, mat, o)
end
-- an upright cylinder at (x, z) in F from y0 to y1, dia across
function K.cyl(F, folder, name, x, y0, y1, z, dia, hex, mat, o)
	o = o or {}; o.shape = Enum.PartType.Cylinder
	return K.part(folder, name, F * CFrame.new(x, (y0 + y1) / 2, z) * CFrame.Angles(0, 0, math.pi / 2), Vector3.new(math.max(y1 - y0, 0.05), dia, dia), hex, mat, o)
end
function K.ball(F, folder, name, x, y, z, dia, hex, mat, o)
	o = o or {}; o.shape = Enum.PartType.Ball
	return K.part(folder, name, F * CFrame.new(x, y, z), Vector3.new(dia, dia, dia), hex, mat, o)
end
-- a rod (a cylinder) between two points in F (not straight up: use K.cyl for that)
function K.rod(F, folder, name, a: Vector3, b: Vector3, dia, hex, mat, o)
	o = o or {}; o.shape = Enum.PartType.Cylinder
	return K.part(folder, name, F * CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), Vector3.new((b - a).Magnitude, dia, dia), hex, mat, o)
end
-- the flat triangle (xa, zin), (xa, zout), (xb, zout) in F, y0..y1 thick (a WedgePart laid flat). zout is the full-width
-- end; the triangle's point is at (xa, zin)
function K.slant(F, folder, name, xa, xb, zin, zout, y0, y1, hex, mat, o)
	o = o or {}; o.cls = "WedgePart"
	local flip = (zout < zin) -- (full width toward -z: the case the turn below was worked out for)
	local base = F * CFrame.new((xa + xb) / 2, (y0 + y1) / 2, (zin + zout) / 2)
	local turn = if flip then CFrame.Angles(0, math.pi, 0) * CFrame.Angles(0, 0, if xb < xa then -math.pi / 2 else math.pi / 2)
		else CFrame.Angles(0, 0, if xb < xa then math.pi / 2 else -math.pi / 2)
	return K.part(folder, name, base * turn, Vector3.new(y1 - y0, math.abs(xb - xa), math.abs(zout - zin)), hex, mat, o)
end
function K.at(F, x, z, yaw, y) return F * CFrame.new(x, y or 0, z) * CFrame.Angles(0, math.rad(yaw or 0), 0) end
-- a frame at (x, z) whose look is the direction (dx, dz)
function K.facing(x, z, dx, dz, y) return CFrame.lookAt(Vector3.new(x, y or 0, z), Vector3.new(x + dx, y or 0, z + dz)) end

-- ------------------------------------------------------------------------------------------------ text and light
-- lines on a part's face: { text, hex, height share, font ("B" black / "S" semibold / an Enum.Font) }; returns the gui,
-- its labels named Line1..n (o.names renames them, e.g. { [3] = "Status" })
function K.text(p, face, lines, o)
	o = o or {}
	local g = Instance.new("SurfaceGui")
	g.Face = face; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = o.pps or 40
	g.LightInfluence = 0; g.Brightness = o.bright or 1.6; g.Parent = p
	if o.guiName then g.Name = o.guiName end
	local f: Instance = g
	if not o.flat then -- (flat: the labels straight under the Gui, for readers that look them up there: HubHolo's ShowName plates)
		local fr = Instance.new("Frame"); fr.Name = "Body"; fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = c3(o.bg or K.P.screen)
		fr.BackgroundTransparency = o.bgt or 1; fr.BorderSizePixel = 0; fr.Parent = g
		f = fr
	end
	local lay = Instance.new("UIListLayout"); lay.FillDirection = Enum.FillDirection.Vertical
	lay.HorizontalAlignment = Enum.HorizontalAlignment.Center; lay.VerticalAlignment = Enum.VerticalAlignment.Center
	lay.SortOrder = Enum.SortOrder.LayoutOrder; lay.Padding = UDim.new(0.015, 0); lay.Parent = f
	for i, l in lines do
		local t = Instance.new("TextLabel")
		t.Name = (o.names and o.names[i]) or ("Line" .. i)
		t.LayoutOrder = i; t.Size = UDim2.fromScale(o.width or 0.94, l[3] or 0.4); t.BackgroundTransparency = 1
		t.Text = l[1]; t.TextColor3 = c3(l[2] or K.P.pale); t.TextScaled = true; t.RichText = true
		t.Font = if l[4] == "S" then Enum.Font.GothamSemibold elseif typeof(l[4]) == "EnumItem" then l[4] else Enum.Font.GothamBlack
		t.Parent = f
	end
	return g
end
-- a sign: a dark panel w x h at (x, y) in frame F's plane z (its face looking along F's look), lines on it
function K.sign(F, folder, name, w, h, x, y, z, lines, o)
	o = o or {}
	local p = K.box(F, folder, name, x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - (o.thick or 0.2), z, o.plate or K.P.screen, nil, { solid = false })
	K.text(p, Enum.NormalId.Front, lines, o)
	if o.both then K.text(p, Enum.NormalId.Back, lines, o) end
	return p
end
function K.light(p, range, bright, hex, o)
	o = o or {}
	local l = Instance.new(o.kind or "PointLight")
	-- (rivals: a cool white unless a lamp asks for warm: warm light only where people stop)
	l.Range = range; l.Brightness = bright; l.Color = c3(hex or (if S.style == "rivals" then K.R.cool else K.P.warm)); l.Shadows = o.shadows == true
	if o.kind == "SpotLight" or o.kind == "SurfaceLight" then l.Face = o.face or Enum.NormalId.Bottom; l.Angle = o.angle or 90 end
	l.Parent = p
	S.lamps += 1
	return l
end
-- a white light panel let into a ceiling whose underside is y: w (x) by l (z) in F, a soft light under it
function K.panel(F, x, y, z, w, l, o)
	o = o or {}
	local rv = S.style == "rivals" -- (rivals: a chunkier housing, the white panel just proud of it)
	local b, d = if rv then 0.7 else 0.35, if rv then 0.85 else 0.45
	K.box(F, "Scenery", "PanelHousing", x - w / 2 - b, x + w / 2 + b, y - d, y + 0.05, z - l / 2 - b, z + l / 2 + b, K.P.pier, nil, { ghost = true })
	local p = K.box(F, "Scenery", "LightPanel", x - w / 2, x + w / 2, y - d - 0.1, y - d + 0.05, z - l / 2, z + l / 2, o.hex or K.P.light, MAT.Neon, { ghost = true, noshadow = true })
	if o.range ~= 0 then K.light(p, o.range or 24, (o.bright or 0.55) * 1.5, o.lightHex or (if rv then K.R.cool else K.P.warm), { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 150 }) end
	return p
end
-- an invisible marker part (spawns, spots, arrival points): at (x, y, z) in F turned yaw, 2 x 0.2 x 2
function K.marker(F, folder, name, x, y, z, yaw, attrs, tags, o)
	o = o or {}
	local p = K.part(folder, name, F * CFrame.new(x, y + 0.1, z) * CFrame.Angles(0, math.rad(yaw or 0), 0), o.size or Vector3.new(2, 0.2, 2), K.P.pier, nil, { ghost = true, tr = 1, noshadow = true })
	for k, v in attrs or {} do p:SetAttribute(k, v) end
	for _, t in tags or {} do Tags:AddTag(p, t) end
	return p
end

-- a big screen of the live counts on a part's faces (default its four upright ones): IN QUEUE over a row per mode, the
-- count in a label named Count_<mode> (HubConsole writes it every second); tagged HubScreen
function K.screen(p, faces)
	Tags:AddTag(p, "HubScreen")
	for _, face in faces or { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right } do
		local g = Instance.new("SurfaceGui")
		g.Face = face; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 28; g.LightInfluence = 0; g.Brightness = 2
		g.Parent = p
		local f = Instance.new("Frame"); f.Size = UDim2.fromScale(1, 1); f.BackgroundColor3 = c3(K.P.screen); f.BorderSizePixel = 0; f.Parent = g
		local pad = Instance.new("UIPadding", f); pad.PaddingLeft = UDim.new(0.07, 0); pad.PaddingRight = UDim.new(0.07, 0); pad.PaddingTop = UDim.new(0.05, 0)
		local lay = Instance.new("UIListLayout", f); lay.SortOrder = Enum.SortOrder.LayoutOrder; lay.Padding = UDim.new(0.012, 0)
		local h = Instance.new("TextLabel"); h.Name = "Head"; h.LayoutOrder = 0; h.Size = UDim2.fromScale(1, 0.2); h.BackgroundTransparency = 1
		h.Text = "IN QUEUE"; h.Font = Enum.Font.GothamBlack; h.TextScaled = true; h.TextColor3 = c3(K.P.amber); h.Parent = f
		for i, md in K.MODES do
			local row = Instance.new("Frame"); row.Name = "Row_" .. md.id; row.LayoutOrder = i; row.Size = UDim2.fromScale(1, 0.135)
			row.BackgroundTransparency = 1; row.Parent = f
			local a = Instance.new("TextLabel"); a.Size = UDim2.fromScale(0.62, 1); a.BackgroundTransparency = 1; a.Text = md.title
			a.Font = Enum.Font.GothamBlack; a.TextScaled = true; a.TextXAlignment = Enum.TextXAlignment.Left; a.TextColor3 = c3(K.P.pale); a.Parent = row
			local b = Instance.new("TextLabel"); b.Name = "Count_" .. md.id; b.AnchorPoint = Vector2.new(1, 0); b.Position = UDim2.fromScale(1, 0)
			b.Size = UDim2.fromScale(0.36, 1); b.BackgroundTransparency = 1; b.Text = "0"; b.Font = Enum.Font.GothamBlack; b.TextScaled = true
			b.TextXAlignment = Enum.TextXAlignment.Right; b.TextColor3 = c3(K.P.holo); b.Parent = row
		end
	end
	K.light(p, 30, 0.45, "9fd0ff")
	return p
end

-- ------------------------------------------------------------------------------------------------ architecture
-- a wall with openings: along F's x from x0 to x1, its face at z0 (z1 behind), y0..y1, holes = { {xa, xb, height} }
function K.wall(F, name, x0, x1, y0, y1, z0, z1, hex, holes, mat)
	table.sort(holes or {}, function(a, b) return a[1] < b[1] end)
	local x = x0
	for _, hl in holes or {} do
		if hl[1] > x then K.box(F, "Shell", name, x, hl[1], y0, y1, z0, z1, hex, mat) end
		if hl[3] < y1 then K.box(F, "Shell", name, hl[1], hl[2], hl[3], y1, z0, z1, hex, mat) end
		x = hl[2]
	end
	if x < x1 then K.box(F, "Shell", name, x, x1, y0, y1, z0, z1, hex, mat) end
end
-- a wide opening's thin frame on a wall's face (z the face; the room it is seen from is on the +z side, the frame stands
-- proud toward it): posts, head, a lit strip under the head, the name on a dark sign above it facing the room
function K.thinFrame(F, xa, xb, h, z, title, o)
	o = o or {}
	if S.style == "rivals" then return K.portal(F, xa, xb, h, z, title, o) end -- (rivals: a deep framed portal instead)
	local d = o.depth or 0.5
	for _, x in { xa, xb } do K.box(F, "Scenery", "OpeningFrame", x - 0.3, x + 0.3, -0.04, h + 0.3, z, z + d, K.P.steel) end
	K.box(F, "Scenery", "OpeningFrame", xa - 0.3, xb + 0.3, h - 0.05, h + 0.4, z, z + d, K.P.steel)
	local l = K.box(F, "Scenery", "OpeningLight", xa + 0.4, xb - 0.4, h - 0.22, h - 0.02, z + 0.1, z + d - 0.1, K.P.light, MAT.Neon, { ghost = true, noshadow = true })
	K.light(l, o.range or 16, 0.5)
	if title then
		local w = o.signW or math.min(xb - xa - 2, math.max(8, #title * 0.85))
		local Fs = F * CFrame.new((xa + xb) / 2, 0, o.signZ or (z + 0.3)) * CFrame.Angles(0, math.pi, 0) -- (its front looks at the room)
		K.sign(Fs, "Scenery", "WaySign", w, o.signH or 1.9, 0, o.signY or (h + 1.7), 0, { { title, K.P.pale, 0.72 } }, { pps = 46 })
	end
end
-- a column: square (w) with a base and a cap band, or round (o.round)
function K.column(F, x, z, y0, y1, w, o)
	o = o or {}
	if o.round then
		K.cyl(F, "Shell", "Column", x, y0, if o.cap and math.abs(y1 - o.cap) < 0.01 then y1 - 0.1 else y1, z, w, o.hex or K.P.pier2, o.mat or MAT.Concrete)
		K.cyl(F, "Scenery", "ColumnBase", x, y0, y0 + 0.8, z, w + 0.5, K.P.pier)
		if o.cap then K.cyl(F, "Scenery", "ColumnCap", x, o.cap - 0.6, o.cap, z, w + 0.6, K.P.cream) end
	else
		K.box(F, "Shell", "Column", x - w / 2, x + w / 2, y0, if o.cap and math.abs(y1 - o.cap) < 0.01 then y1 - 0.1 else y1, z - w / 2, z + w / 2, o.hex or K.P.pier2, o.mat or MAT.Concrete) -- (its top inside the cap)
		K.box(F, "Scenery", "ColumnBase", x - w / 2 - 0.25, x + w / 2 + 0.25, y0, y0 + 0.8, z - w / 2 - 0.25, z + w / 2 + 0.25, K.P.pier)
		if o.cap then K.box(F, "Scenery", "ColumnCap", x - w / 2 - 0.3, x + w / 2 + 0.3, o.cap - 0.6, o.cap, z - w / 2 - 0.3, z + w / 2 + 0.3, K.P.cream) end
	end
end
-- a glass rail along F's x at the edge z (the walkway on +z side of it), from y (the floor) up
function K.rail(F, x0, x1, y, z)
	if S.style == "rivals" then -- (rivals: a solid parapet, slate with a pale coping: chunky, no glass)
		K.box(F, "Scenery", "Parapet", x0, x1, y, y + 3.2, z - 0.5, z + 0.5, K.R.wall2, nil, { solid = true })
		K.box(F, "Scenery", "ParapetCap", x0 - 0.05, x1 + 0.05, y + 3.2, y + 3.6, z - 0.65, z + 0.65, K.R.struct)
		return
	end
	K.box(F, "Scenery", "RailGlass", x0, x1, y, y + 3.1, z - 0.15, z + 0.15, K.P.glass, MAT.Glass, { tr = 0.6, solid = true })
	K.box(F, "Scenery", "RailTop", x0, x1, y + 3.1, y + 3.5, z - 0.25, z + 0.25, K.P.cream)
	K.box(F, "Scenery", "RailFoot", x0, x1, y, y + 0.3, z - 0.25, z + 0.25, K.P.steel)
end

-- ------------------------------------------------------------------------------------------------ the rivals pieces
-- a WedgePart standing up in F: its square corner at (x, y) in F's x-y plane, its legs `leg` long toward sx (along x) and
-- sy (along y), z0..z1 deep; its slope faces away from the corner (a chamfer in a frame's corner)
function K.chamfer(F, folder, name, x, y, z0, z1, leg, sx, sy, hex, o)
	o = o or {}; o.cls = "WedgePart"
	local Y, Z = Vector3.new(0, sy, 0), Vector3.new(-sx, 0, 0)
	local cf = CFrame.fromMatrix(Vector3.new(x + sx * leg / 2, y + sy * leg / 2, (z0 + z1) / 2), Y:Cross(Z), Y, Z)
	return K.part(folder, name, F * cf, Vector3.new(math.abs(z1 - z0), leg, leg), hex, nil, o)
end
-- a lit word sign facing F's look (as K.sign: the plate in F's plane z, w x h round (x, y)): a dark plate, the word lit
-- pale, an accent bar under it, a pale housing whose lips stand proud of the plate
function K.wordSign(F, folder, name, w, h, x, y, z, title, o)
	o = o or {}
	local lip = o.lip or 0.4
	K.box(F, folder, name .. "Housing", x - w / 2 - lip, x + w / 2 + lip, y - h / 2 - lip, y + h / 2 + lip, z - 0.1, z + (o.back or 0.5), K.R.struct)
	for _, s in { -1, 1 } do
		K.box(F, folder, name .. "Lip", x - w / 2 - lip, x + w / 2 + lip, y + s * (h / 2 - 0.02), y + s * (h / 2 + lip), z - 0.45, z - 0.05, K.R.struct)
		K.box(F, folder, name .. "Lip", x + s * (w / 2 - 0.02), x + s * (w / 2 + lip - 0.03), y - h / 2 - 0.1, y + h / 2 + 0.1, z - 0.44, z - 0.06, K.R.struct)
	end
	local p = K.box(F, folder, name, x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - 0.25, z, K.R.screen, nil, { solid = false })
	K.text(p, Enum.NormalId.Front, { { title, o.textHex or "f2f0ea", o.share or 0.6 } }, { pps = o.pps or 46, bright = 2.2, bg = o.bg, bgt = if o.bg then 0 else nil }) -- (o.bg: a lit face, never black)
	K.box(F, folder, name .. "Bar", x - w / 2 + 0.5, x + w / 2 - 0.5, y - h / 2 + 0.16, y - h / 2 + 0.34, z - 0.3, z - 0.24, o.accent or S.accent, MAT.Neon, { ghost = true, noshadow = true })
	return p
end
-- (rivals) a deep framed opening, in place of K.thinFrame (the same F, xa, xb, h, z: z the wall's face, the room on +z): a
-- pale sleeve through the wall standing proud both sides (jambs and a head), the head's inner corners chamfered, a lit
-- strip under the head, a threshold; the name on a K.wordSign at o.signZ / o.signY facing the room
function K.portal(F, xa, xb, h, z, title, o)
	o = o or {}
	local inn, out, hd, ch = o.inset or 0.8, o.cover or 0.8, o.headD or 1.4, o.chamfer or 1.2
	local z0, z1 = z - (o.back or 2) - (o.proudBack or 0.6), z + (o.proud or 1.0)
	local col = K.R.struct
	for _, sx in { -1, 1 } do
		local xe = if sx < 0 then xa else xb
		K.box(F, "Shell", "PortalJamb", xe + sx * out, xe - sx * inn, 0, h - hd + 0.2, z0, z1, col)
		-- (the chamfer's square corner sunk 0.05 into the jamb and the head: no faces shared)
		K.chamfer(F, "Scenery", "PortalChamfer", xe - sx * (inn - 0.05), h - hd + 0.05, z0 + 0.05, z1 - 0.05, ch + 0.05, -sx, -1, col)
	end
	K.box(F, "Shell", "PortalHead", xa - out, xb + out, h - hd, h + 0.3, z0, z1, col)
	local lit = K.box(F, "Scenery", "PortalLight", xa + inn + ch + 0.4, xb - inn - ch - 0.4, h - hd - 0.14, h - hd + 0.02, (z0 + z1) / 2 - 0.35, (z0 + z1) / 2 + 0.35, K.R.slat, MAT.Neon, { ghost = true, noshadow = true })
	K.light(lit, o.range or 14, 0.5, nil, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 120 })
	K.box(F, "Scenery", "PortalSill", xa + inn, xb - inn, -0.08, 0.11, z0, z1, col, nil, { ghost = true }) -- (over the floor's lines and runners)
	if title then
		local w = o.signW or math.min(xb - xa - 2, math.max(8, #title * 0.95))
		local Fs = F * CFrame.new((xa + xb) / 2, 0, o.signZ or (z1 + 0.1)) * CFrame.Angles(0, math.pi, 0) -- (its front looks at the room)
		K.wordSign(Fs, "Scenery", "WaySign", w, o.signH or 2.4, 0, o.signY or (h + 1.9), 0, title, { accent = o.accent })
	end
end
-- (rivals) a coffered ceiling under y: beams on the lines xs (running along z) and zs (running along x), bosses where they
-- cross, a lamp panel in every cell; o.skip(cx, cz, w, l) -> true leaves a cell open (a hole for a drum); o.d the depth
function K.coffers(F, xs, zs, y, o)
	o = o or {}
	local d, bw = o.d or 1.8, o.bw or 1.0
	local skip = o.skip or function() return false end
	local open = {}
	for i = 1, #xs - 1 do for j = 1, #zs - 1 do
		local cx, cz, cw, cl = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2, xs[i + 1] - xs[i], zs[j + 1] - zs[j]
		open[i .. "," .. j] = skip(cx, cz, cw, cl)
		if not open[i .. "," .. j] and cw >= 5 and cl >= 5 and o.lamps ~= false and (not o.checker or (i + j) % 2 == 0) then
			local lw = o.lampW or 4.4
			K.panel(F, cx, y, cz, math.min(lw, cw - 2.6), math.min(lw, cl - 2.6), { bright = o.bright or 0.5, range = o.range or 40, lightHex = o.lightHex })
		end
	end end
	local function on(i, j) return i >= 1 and j >= 1 and i < #xs and j < #zs and not open[i .. "," .. j] end
	local nb = bw / 2 + 0.15
	for i = 1, #xs do for j = 1, #zs - 1 do
		if on(i - 1, j) or on(i, j) then K.box(F, "Scenery", "Coffer", xs[i] - bw / 2, xs[i] + bw / 2, y - d, y + 0.1, zs[j] + nb - 0.05, zs[j + 1] - nb + 0.05, K.R.struct, nil, { ghost = true }) end
	end end
	for j = 1, #zs do for i = 1, #xs - 1 do
		if on(i, j - 1) or on(i, j) then K.box(F, "Scenery", "Coffer", xs[i] + nb - 0.05, xs[i + 1] - nb + 0.05, y - d, y + 0.1, zs[j] - bw / 2, zs[j] + bw / 2, K.R.struct, nil, { ghost = true }) end
	end end
	for i = 1, #xs do for j = 1, #zs do
		if on(i - 1, j - 1) or on(i, j - 1) or on(i - 1, j) or on(i, j) then
			K.box(F, "Scenery", "CofferBoss", xs[i] - nb, xs[i] + nb, y - d - 0.15, y + 0.13, zs[j] - nb, zs[j] + nb, K.R.structHi, nil, { ghost = true })
		end
	end end
end
-- (rivals) a haunch: a slanted plank along F's x (x0..x1) from a wall (its face z = zw, at y = yTop - drop) up to the
-- ceiling (z = zw + run, y = yTop): the room's top corners cut off (an octagonal section). A pale ledge and a lit line
-- along its foot (o.cove ~= false)
function K.haunch(F, x0, x1, zw, run, yTop, drop, o)
	o = o or {}
	local a, b = Vector3.new(0, yTop - drop, zw), Vector3.new(0, yTop, zw + run)
	local n = Vector3.new(0, math.abs(run), -math.sign(run) * drop).Unit -- (toward the corner it hides)
	local th = o.thick or 0.6
	local mid = Vector3.new((x0 + x1) / 2, 0, 0) + (a + b) / 2 + n * (o.off or th / 2) -- (o.off < 0: under the slope, a rib)
	K.part("Scenery", o.name or "Haunch", F * CFrame.lookAt(mid, mid + Vector3.xAxis, n), Vector3.new((b - a).Magnitude + (o.extra or 0.1), th, math.abs(x1 - x0)), o.hex or K.R.ceil, nil, { ghost = true })
	if o.cove ~= false then
		local sg = math.sign(run)
		local tr = o.trim or 0 -- (o.trim: the ledge and its line stop short of the ends, where another side's meet them)
		K.box(F, "Scenery", "HaunchLedge", x0 + tr, x1 - tr, yTop - drop - 0.75, yTop - drop - 0.2, zw - sg * 0.1, zw + sg * 0.8, K.R.struct, nil, { ghost = true })
		local c = K.box(F, "Scenery", "HaunchCove", x0 + tr + 0.3, x1 - tr - 0.3, yTop - drop - 0.2, yTop - drop - 0.05, zw - sg * 0.05, zw + sg * 0.45, K.R.slat, MAT.Neon, { ghost = true, noshadow = true })
		if o.light ~= false then K.light(c, o.range or 14, o.bright or 0.35, nil, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 150 }) end
	end
end
-- (rivals) a line on the floor (its top y, default 0) through the points { {x, z}, ... } in F: w wide, a hair proud of the
-- floor (no plane shared), alternate pieces a hair apart in height where they overlap; a round piece at each joint
function K.floorLine(F, pts, w, hex, y, o)
	o = o or {}
	y = y or 0
	for i = 1, #pts - 1 do
		local a, b = pts[i], pts[i + 1]
		local dx, dz = b[1] - a[1], b[2] - a[2]
		local len = math.sqrt(dx * dx + dz * dz)
		local top = y + 0.065 + (i % 2) * 0.01
		K.part("Scenery", o.name or "FloorLine", F * CFrame.new((a[1] + b[1]) / 2, top - 0.08, (a[2] + b[2]) / 2) * CFrame.Angles(0, math.atan2(dx, dz), 0),
			Vector3.new(w, 0.16, len), hex, nil, { ghost = true, noshadow = true })
		if i > 1 then K.cyl(F, "Scenery", o.name or "FloorLine", a[1], y - 0.1, y + 0.04, a[2], w, hex, nil, { ghost = true, noshadow = true }) end
	end
end
-- the points of an arc on the floor: round (cx, cz) at r from angle a0 to a1 (degrees, 0 = +x, 90 = +z), n pieces
function K.arcPts(cx, cz, r, a0, a1, n)
	local out = {}
	for i = 0, n do
		local a = math.rad(a0 + (a1 - a0) * i / n)
		table.insert(out, { cx + r * math.cos(a), cz + r * math.sin(a) })
	end
	return out
end
-- (rivals) an arrow head on the floor at (x, z) in F pointing along (dx, dz), s across
function K.chevron(F, x, z, dx, dz, s, hex, y)
	local Fc = F * CFrame.new(x, 0, z) * CFrame.Angles(0, math.atan2(dx, dz), 0) -- (its +z: the way it points)
	for k, sd in { -1, 1 } do
		local ax, az = sd * s / 2, -s / 2
		local len = math.sqrt(ax * ax + az * az)
		K.part("Scenery", "FloorArrow", Fc * CFrame.new(ax / 2, (y or 0) - 0.01 + (k - 1) * 0.025, az / 2) * CFrame.Angles(0, math.atan2(ax, az), 0),
			Vector3.new(0.8, 0.16, len + 0.4), hex, nil, { ghost = true, noshadow = true })
	end
end
-- (rivals; R4) THE NAME: a band round (cx, cz) in F, half wide, y0..y1, JANKFIRE lit on all four faces, an accent line
-- under the word, pale edges above and below
function K.nameBand(F, cx, cz, half, y0, y1, o)
	o = o or {}
	local p = K.box(F, "Shell", "NameBand", cx - half, cx + half, y0, y1, cz - half, cz + half, K.R.screen)
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right } do
		K.text(p, face, { { o.text or "JANKFIRE", "f2f0ea", 0.62 } }, { pps = 40, bright = 2.4 })
	end
	K.box(F, "Scenery", "NameBandEdge", cx - half - 0.3, cx + half + 0.3, y0 - 0.5, y0 + 0.05, cz - half - 0.3, cz + half + 0.3, K.R.struct)
	K.box(F, "Scenery", "NameBandEdge", cx - half - 0.3, cx + half + 0.3, y1 - 0.05, y1 + 0.5, cz - half - 0.3, cz + half + 0.3, K.R.struct)
	for k = 0, 3 do
		local Fk = F * CFrame.new(cx, 0, cz) * CFrame.Angles(0, k * math.pi / 2, 0)
		K.box(Fk, "Scenery", "NameBandBar", -half + 1.2, half - 1.2, y0 + 0.22, y0 + 0.42, -half - 0.06, -half + 0.02, S.accent, MAT.Neon, { ghost = true, noshadow = true })
	end
	K.light(p, 18, 0.4, nil)
	return p
end
-- (rivals; R4) THE NAME on a hanging board: two-faced, w x h round F (its faces along F's look and back), pale edges, an
-- accent line under the word on each face; o.hang = the ceiling's underside (F's y): two pale rods up to it
function K.nameBoard(F, w, h, o)
	o = o or {}
	local p = K.box(F, "Scenery", "NameBoard", -w / 2, w / 2, -h / 2, h / 2, -0.4, 0.4, K.R.screen)
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do K.text(p, face, { { o.text or "JANKFIRE", "f2f0ea", 0.62 } }, { pps = 40, bright = 2.4 }) end
	K.box(F, "Scenery", "NameBoardEdge", -w / 2 - 0.3, w / 2 + 0.3, -h / 2 - 0.5, -h / 2 + 0.05, -0.6, 0.6, K.R.struct)
	K.box(F, "Scenery", "NameBoardEdge", -w / 2 - 0.3, w / 2 + 0.3, h / 2 - 0.05, h / 2 + 0.5, -0.6, 0.6, K.R.struct)
	for _, s in { -1, 1 } do
		K.box(F, "Scenery", "NameBoardBar", -w / 2 + 1.2, w / 2 - 1.2, -h / 2 + 0.22, -h / 2 + 0.42, s * 0.38, s * 0.46, S.accent, MAT.Neon, { ghost = true, noshadow = true })
		if o.hang then K.box(F, "Scenery", "NameBoardRod", s * (w / 2 - 1.5) - 0.25, s * (w / 2 - 1.5) + 0.25, h / 2 + 0.45, o.hang + 0.1, -0.25, 0.25, K.R.struct) end
	end
	K.light(p, 16, 0.35, nil)
	return p
end
-- (rivals; R5) an info screen on a wall: F = its middle on the wall's face, its look out to the viewers; w x h. kind "tips":
-- its text is HubLife's TIPS, one every 7 s (tag HubTip); "news": o.text, still
function K.infoScreen(F, w, h, kind, o)
	o = o or {}
	K.box(F, "Scenery", "InfoFrame", -w / 2 - 0.6, w / 2 + 0.6, -h / 2 - 0.6, h / 2 + 0.6, -0.7, 0.05, K.R.struct)
	local p = K.box(F, "Scenery", "InfoScreen", -w / 2, w / 2, -h / 2, h / 2, -0.85, -0.65, K.R.screen)
	local g = Instance.new("SurfaceGui"); g.Name = "Info"; g.Face = Enum.NormalId.Front; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	g.PixelsPerStud = 30; g.LightInfluence = 0; g.Brightness = 1.8; g.Parent = p
	local fr = Instance.new("Frame"); fr.Name = "Body"; fr.Size = UDim2.fromScale(1, 1); fr.BackgroundColor3 = c3(K.R.screen); fr.BorderSizePixel = 0; fr.ClipsDescendants = true; fr.Parent = g
	local hd = Instance.new("TextLabel"); hd.Name = "Head"; hd.BackgroundTransparency = 1; hd.Position = UDim2.fromScale(0.06, 0.08); hd.Size = UDim2.fromScale(0.88, 0.2)
	hd.Font = Enum.Font.GothamBlack; hd.TextScaled = true; hd.TextXAlignment = Enum.TextXAlignment.Left; hd.TextColor3 = c3(S.accent)
	hd.Text = if kind == "news" then "NEWS" else "TIPS"; hd.Parent = fr
	local bar = Instance.new("Frame"); bar.Name = "Rule"; bar.BackgroundColor3 = c3(S.accent); bar.BorderSizePixel = 0; bar.Position = UDim2.fromScale(0.06, 0.31); bar.Size = UDim2.fromScale(0.88, 0.018); bar.Parent = fr
	local t = Instance.new("TextLabel"); t.Name = "Line"; t.BackgroundTransparency = 1; t.Font = Enum.Font.GothamBold; t.TextColor3 = c3("e8ecf2")
	t.TextScaled = true; t.TextWrapped = true; t.TextXAlignment = Enum.TextXAlignment.Left; t.TextYAlignment = Enum.TextYAlignment.Top
	t.Position = UDim2.fromScale(0.06, 0.39); t.Size = UDim2.fromScale(0.88, 0.5)
	if kind == "news" then
		t.Text = o.text or ""
	else
		t.Text = o.text or "step on a pad in your team's colour to queue. step off to leave the queue."
		Tags:AddTag(t, "HubTip")
	end
	t.Parent = fr
	K.light(p, 12, 0.3, "cfe0ff")
	return p
end
-- (rivals) THE DRUM: a round lantern over a square hole in a roof (the roof's underside at y; the hole's half side
-- o.hole, its corners filled here so the drum stands on an octagon): n walls round radius r (inside), a light slat down
-- each, pale ribs at the corners, pale bands at its foot and top; a cone of planks up to an oculus (a lit disc), pale ribs
-- and light slats under the planks; a ring of spot lights at its foot. (cx, cz) its middle in F
function K.drum(F, cx, cz, y, o)
	o = o or {}
	local r, h, n, rise, oc = o.r or 12, o.h or 9, o.n or 16, o.rise or 5, o.oc or 4
	local hole, t = o.hole or r, 1.2
	local da = 2 * math.pi / n
	local Fc = F * CFrame.new(cx, 0, cz)
	local cut = r * math.sqrt(2) -- (x + z on the cut across each corner: the drum's wall stands on it)
	for _, sx in { -1, 1 } do for _, sz in { -1, 1 } do
		K.slant(Fc, "Shell", "DrumCorner", sx * hole, sx * (cut - hole), sz * (cut - hole), sz * hole, y, y + 1, K.R.ceil)
	end end
	local yt = y + h
	for i = 0, n - 1 do
		local a = i * da
		local Fw = Fc * CFrame.lookAt(Vector3.zero, Vector3.new(math.cos(a), 0, math.sin(a))) -- (its -z: out)
		local half = (r + t) * math.tan(da / 2) + 0.05
		K.box(Fw, "Shell", "DrumWall", -half, half, y, yt, -(r + t), -r, K.R.ceil)
		K.box(Fw, "Scenery", "DrumSlat", -0.45, 0.45, y + 2.2, yt - 1.8, -r - 0.1, -r + 0.15, K.R.slat, MAT.Neon, { ghost = true, noshadow = true })
		local bh = (i % 2) * 0.04
		K.box(Fw, "Scenery", "DrumFoot", -half + 0.1, half - 0.1, y - 0.12, y + 1.0 + bh, -r - 0.1, -r + 0.5, K.R.struct, nil, { ghost = true })
		K.box(Fw, "Scenery", "DrumTop", -half + 0.1, half - 0.1, yt - 1.0 - bh, yt - 0.06, -r - 0.1, -r + 0.6, K.R.struct, nil, { ghost = true })
		local av = a + da / 2
		local Fv = Fc * CFrame.lookAt(Vector3.zero, Vector3.new(math.cos(av), 0, math.sin(av)))
		local rv = r / math.cos(da / 2)
		K.box(Fv, "Scenery", "DrumRib", -0.6, 0.6, y - 0.16, yt - 0.06, -rv - 0.2, -rv + 0.75, K.R.struct, nil, { ghost = true })
		-- the cone: a plank on this side, a rib under the seam at its corner, a light slat down its middle
		local d1, dv = Vector3.new(math.cos(a), 0, math.sin(a)), Vector3.new(math.cos(av), 0, math.sin(av))
		local p0, p1 = Vector3.new(0, yt, 0) + d1 * (r + 0.4), Vector3.new(0, yt + rise, 0) + d1 * oc
		local pm, L = (p0 + p1) / 2, (p1 - p0).Magnitude
		local cf = CFrame.lookAt(pm, p1, Vector3.yAxis)
		K.part("Shell", "DrumPlank", Fc * cf * CFrame.new(0, 0.3, 0), Vector3.new(2 * (r + 0.4) * math.tan(da / 2) + 0.2, 0.6, L), K.R.ceil)
		K.part("Scenery", "DrumSlat", Fc * cf * CFrame.new(0, -0.09, -0.6), Vector3.new(0.7, 0.16, L - 3), K.R.slat, MAT.Neon, { ghost = true, noshadow = true })
		local q0, q1 = Vector3.new(0, yt, 0) + dv * ((r + 0.4) / math.cos(da / 2)), Vector3.new(0, yt + rise, 0) + dv * (oc / math.cos(da / 2))
		K.part("Scenery", "DrumRib", Fc * CFrame.lookAt((q0 + q1) / 2, q1, Vector3.yAxis) * CFrame.new(0, -0.35, 0), Vector3.new(1.0, 0.8, (q1 - q0).Magnitude), K.R.struct, nil, { ghost = true })
	end
	K.cyl(Fc, "Shell", "DrumOculusRing", 0, yt + rise - 0.2, yt + rise + 0.6, 0, 2 * (oc + 1.4), K.R.struct)
	local ocl = K.cyl(Fc, "Scenery", "DrumOculus", 0, yt + rise - 0.36, yt + rise - 0.22, 0, 2 * oc, K.R.slat, MAT.Neon, { ghost = true, noshadow = true })
	K.light(ocl, 60, o.oculusBright or 0.6, nil, { kind = "SurfaceLight", face = Enum.NormalId.Bottom, angle = 70 })
	-- the spot ring at the drum's foot, down onto the floor
	for i = 0, (o.spots or 8) - 1 do
		local a = (i + 0.5) * 2 * math.pi / (o.spots or 8)
		local sp = K.box(Fc, "Scenery", "DrumSpot", math.cos(a) * (r - 1.6) - 0.3, math.cos(a) * (r - 1.6) + 0.3, y + 1.2, y + 1.4, math.sin(a) * (r - 1.6) - 0.3, math.sin(a) * (r - 1.6) + 0.3, K.R.struct, nil, { ghost = true, tr = 1, noshadow = true })
		K.light(sp, o.spotRange or 52, o.spotBright or 0.6, nil, { kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 40 })
	end
end

-- ------------------------------------------------------------------------------------------------ seats and seating
-- a seat players can sit on (hub-minigames' HubSeats): an invisible part on the cushion's top, facing the way you face
function K.seat(F, x, y, z, yaw)
	return K.marker(F, "Scenery", "HubSeat", x, y - 0.1, z, yaw or 0, nil, { "HubSeat" }, { size = Vector3.new(1.8, 0.2, 1.8) })
end
-- a bench facing F's look (-Z): len long, a padded top, two legs; a seat every 2.2
function K.bench(F, len, o)
	o = o or {}
	K.box(F, "Shell", "Bench", -len / 2, len / 2, 0.4, 1.3, -0.8, 0.8, o.hex or K.P.wood, MAT.Wood)
	K.box(F, "Scenery", "BenchPad", -len / 2 + 0.1, len / 2 - 0.1, 1.3, 1.5, -0.72, 0.72, o.pad or K.P.carpet2, MAT.Fabric)
	for _, s in { -1, 1 } do K.box(F, "Scenery", "BenchLeg", s * (len / 2 - 0.9) - 0.3, s * (len / 2 - 0.9) + 0.3, 0, 0.4, -0.6, 0.6, K.P.steel) end
	if o.back then K.box(F, "Scenery", "BenchBack", -len / 2, len / 2, 1.5, 3.6, 0.5, 0.8, o.hex or K.P.wood, MAT.Wood) end
	local n = math.max(1, math.floor(len / 2.2))
	for i = 1, n do K.seat(F, -len / 2 + len * (i - 0.5) / n, 1.5, 0, 0) end
end
-- a sofa facing F's look: len long, chunky (seat, back, arms), a seat per cushion
function K.sofa(F, len, hex, o)
	o = o or {}
	hex = hex or "5e6470"
	K.box(F, "Shell", "Sofa", -len / 2, len / 2, 0, 1.45, -1.0, 1.2, hex, MAT.Fabric)
	K.box(F, "Scenery", "SofaBack", -len / 2, len / 2, 1.45, 3.4, 1.2, 1.9, hex, MAT.Fabric)
	for _, s in { -1, 1 } do K.box(F, "Scenery", "SofaArm", s * len / 2, s * (len / 2 + 0.7), 0, 2.3, -1.0, 1.9, hex, MAT.Fabric) end
	local n = math.max(1, math.floor(len / 2.4))
	if not o.noSeats then for i = 1, n do K.seat(F, -len / 2 + len * (i - 0.5) / n, 1.45, 0.1, 0) end end
end
-- a seating cluster round F (its look toward the room): a rug, a sofa behind, two armchairs facing in, a low table, a
-- tall planter, a drop light
function K.cluster(F, o)
	o = o or {}
	K.cyl(F, "Scenery", "Rug", 0, 0, 0.06, 0, 11, K.P.carpet, MAT.Fabric)
	K.sofa(F * CFrame.new(0, 0, 3.4), 6.4, o.hex, { noSeats = o.npcSofa }) -- (a regular's sofa: its seats are the regular's points)
	for _, s in { -1, 1 } do K.sofa(F * CFrame.new(s * 3.9, 0, -0.8) * CFrame.Angles(0, math.rad(s * 90), 0), 2.2, o.hex) end
	K.box(F, "Shell", "LowTable", -1.5, 1.5, 0, 1.2, -1.6, 0.6, K.P.woodDark, MAT.Wood)
	K.cyl(F, "Shell", "Planter", 4.6, 0, 2.2, 4.6, 2.4, K.P.cream)
	K.ball(F, "Scenery", "Bush", 4.6, 3.4, 4.6, 3.2, K.P.plant, MAT.Grass)
	if o.lampY then
		K.cyl(F, "Scenery", "PendantCord", 0, o.lampY - 3, o.lampY, -0.5, 0.12, K.P.steel)
		local l = K.cyl(F, "Scenery", "Pendant", 0, o.lampY - 3.8, o.lampY - 3, -0.5, 2.2, K.P.dark)
		K.light(K.cyl(F, "Scenery", "PendantGlow", 0, o.lampY - 3.85, o.lampY - 3.75, -0.5, 1.8, K.P.warm, MAT.Neon, { ghost = true }), 14, 0.6, K.P.warm) -- (a place to stop: warm)
	end
end
-- a bar facing F's look (the drinkers' side): counter, top, a lit line, stools with seats, shelves behind
function K.bar(F, len)
	len = len or 12
	K.box(F, "Shell", "BarCounter", -len / 2, len / 2, 0, 3.8, -0.9, 0.9, K.P.pier)
	K.box(F, "Scenery", "BarTop", -len / 2 - 0.4, len / 2 + 0.4, 3.8, 4.15, -1.25, 1.1, K.P.creamHi)
	K.box(F, "Scenery", "BarLine", -len / 2 + 0.4, len / 2 - 0.4, 3.5, 3.62, -0.98, -0.9, K.P.amber, MAT.Neon, { ghost = true })
	for i = -2, 2 do
		local x = i * len / 5.5
		K.cyl(F, "Scenery", "StoolFoot", x, 0, 0.3, -2.6, 1.2, K.P.steel)
		K.cyl(F, "Scenery", "StoolStem", x, 0.3, 2.4, -2.6, 0.3, K.P.pier2)
		K.cyl(F, "Shell", "StoolSeat", x, 2.4, 2.8, -2.6, 1.5, K.P.shell2)
		K.seat(F, x, 2.8, -2.6, 180) -- (facing the bar)
	end
	K.box(F, "Scenery", "BarShelfWall", -len / 2, len / 2, 0, 8, 2.6, 3.0, K.P.wall2)
	for _, y in { 4.4, 6.4 } do
		K.box(F, "Scenery", "BarShelf", -len / 2 + 0.4, len / 2 - 0.4, y, y + 0.25, 2.0, 2.6, K.P.cream)
		for i = 0, math.floor(len / 1.1) - 2 do K.cyl(F, "Scenery", "Bottle", -len / 2 + 1 + i * 1.1, y + 0.25, y + 1.3 + (i % 3) * 0.2, 2.3, 0.5, ({ "6f7a68", "8a7a62", "5d6470" })[i % 3 + 1]) end
	end
end

-- ------------------------------------------------------------------------------------------------ the games' spots
-- a MiniGameSpot (hub-minigames builds the game on it): invisible, tagged, Game, look = the game's own (see MiniGames' L)
function K.gameSpot(F, game, y, attrs)
	local m = K.marker(F, "Scenery", "MiniGameSpot", 0, (y or 0) - 0.1, 0, 0, attrs, { "MiniGameSpot" }, { size = Vector3.new(1, 0.2, 1) })
	m:SetAttribute("Game", game)
	return m
end
-- a table's place (arm / board): a rug under where the game's table and its two seats go (seats at +-look)
function K.tableSpot(F, game)
	K.cyl(F, "Scenery", "TableRug", 0, 0, 0.06, 0, 10, if S.style == "rivals" then K.P.carpet else K.P.carpet2, MAT.Fabric) -- (rivals: the accent is for seats)
	K.cyl(F, "Scenery", "TableRugEdge", 0, -0.02, 0.04, 0, 10.6, K.P.cream)
	return K.gameSpot(F, game)
end
-- the arcade cabinet's place: its back to a wall, its screen along F's look, 4.5 clear in front
function K.arcadeSpot(F) return K.gameSpot(F, "arcade") end

-- ------------------------------------------------------------------------------------------------ boards and displays
-- a ranked board's place (play-party's: a BoardSpot, Board "duels" / "party", Facing out of the wall, a BoardPrompt
-- with RankedBoard that opens the table): a frame and a dark panel on a wall at F (its look out of the wall)
function K.boardSpot(F, board, w, h)
	w, h = w or 12, h or 8
	K.box(F, "Scenery", "LiveBoardFrame", -w / 2 - 0.45, w / 2 + 0.45, -h / 2 - 0.45, h / 2 + 0.45, -0.45, 0, K.P.pier2)
	K.box(F, "Scenery", "LiveBoardPanel", -w / 2, w / 2, -h / 2, h / 2, -0.55, -0.45, K.P.screen)
	local spot = K.box(F, "Scenery", "BoardSpot", -w / 2, w / 2, -h / 2, h / 2, -0.65, -0.55, K.P.screen, nil, { ghost = true, tr = 1 })
	spot:SetAttribute("Board", board)
	spot:SetAttribute("Facing", (S.site * F).LookVector)
	Tags:AddTag(spot, "BoardSpot")
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "BoardPrompt"; pr.ActionText = "Leaderboard"; pr.ObjectText = if board == "duels" then "Duels" else "Parties"
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = 14; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr:SetAttribute("RankedBoard", board)
	pr.Parent = spot
	local cove = K.box(F, "Scenery", "LiveBoardCove", -w / 2 - 0.2, w / 2 + 0.2, h / 2 + 0.45, h / 2 + 0.7, -0.7, 0, K.P.creamHi)
	return spot
end
-- the SPECTATE board's place (play-party's spectating, 20 Nov: the owner wants a board in the hubs to watch games in
-- progress): F = the board's middle on its wall (or screen) face, its look out toward the viewers; w x h of board. A frame
-- (o.flush: none, the face is the frame) and a dark panel, then the marker in front of it: a Part named SpectateBoard (tag
-- SpectateBoard, Hub), w x h x 0.1, invisible, its front (-Z) face to the viewers; play-party draws the board on it
function K.spectateSpot(F, w, h, o)
	o = o or {}
	local dz = if o.flush then 0 else (o.depth or 0.6)
	if not o.flush then
		K.box(F, "Scenery", "SpectateFrame", -w / 2 - 0.45, w / 2 + 0.45, -h / 2 - 0.45, h / 2 + 0.45, -dz, 0, K.P.pier2)
	end
	K.box(F, "Scenery", "SpectatePanel", -w / 2, w / 2, -h / 2, h / 2, -dz - 0.08, -dz, K.P.screen)
	local m = K.box(F, "Scenery", "SpectateBoard", -w / 2, w / 2, -h / 2, h / 2, -dz - 0.18, -dz - 0.08, K.P.screen, nil, { ghost = true, tr = 1, noshadow = true })
	Tags:AddTag(m, "SpectateBoard")
	return m
end
-- a trophy case (a glass box on a plinth, two shelves of gold trophies, a light in its top) facing F's look
function K.trophyCase(F, w)
	w = w or 8
	K.box(F, "Shell", "CaseBase", -w / 2, w / 2, 0, 1.4, -1.2, 1.2, K.P.dark)
	K.box(F, "Scenery", "CaseGlass", -w / 2 + 0.1, w / 2 - 0.1, 1.4, 7.4, -1.1, 1.1, K.P.glass, MAT.Glass, { tr = 0.6, solid = true })
	K.box(F, "Scenery", "CaseTop", -w / 2, w / 2, 7.4, 7.8, -1.2, 1.2, K.P.dark)
	for _, y in { 1.4, 4.3 } do
		K.box(F, "Scenery", "CaseShelf", -w / 2 + 0.2, w / 2 - 0.2, y, y + 0.15, -1.0, 1.0, K.P.cream)
		for i = -1, 1 do
			K.cyl(F, "Scenery", "Trophy", i * w * 0.3, y + 0.15, y + 1.6, 0, 0.6, K.P.gold, MAT.Metal)
			K.ball(F, "Scenery", "Trophy", i * w * 0.3, y + 2.0, 0, 1.0, K.P.gold, MAT.Metal)
		end
	end
	K.light(K.box(F, "Scenery", "CaseLight", -w / 2 + 0.4, w / 2 - 0.4, 7.2, 7.35, -0.6, 0.6, K.P.warm, MAT.Neon, { ghost = true }), 10, 0.7)
end
-- the end of a pads gallery: a lit recess in the wall with the trophy case, the two ranked boards either side; F at the
-- wall's face (its look into the room)
function K.trophyWall(F)
	K.box(F, "Scenery", "RecessBack", -9, 9, 0.6, 12, 0, 0.3, K.P.wall2)
	for _, s in { -1, 1 } do K.box(F, "Scenery", "RecessSide", s * 9, s * 10, 0, 13, -1.6, 0.3, K.P.pier) end
	K.box(F, "Scenery", "RecessHead", -10, 10, 12, 13, -1.6, 0.3, K.P.pier)
	K.light(K.box(F, "Scenery", "RecessCove", -8.6, 8.6, 11.6, 11.8, -1.2, 0, K.P.light, MAT.Neon, { ghost = true }), 18, 0.6)
	K.trophyCase(F * CFrame.new(0, 0, -2.6), 12)
	for _, s in { -1, 1 } do K.boardSpot(F * CFrame.new(s * 15, 7.4, -0.05), if s < 0 then "duels" else "party", 9.6, 7.4) end
end

-- ------------------------------------------------------------------------------------------------ rooms
-- a room box: floor (o.floor, o.floorMat), lid at h, walls round x0..x1, z0..z1 (in F) with holes per side
-- { n = { {xa, xb, h} }, s = ..., e = { {za, zb, h} }, w = ... }; 2 thick, outside the given box
function K.room(F, name, x0, x1, z0, z1, h, o)
	o = o or {}
	local hole = o.holes or {}
	K.box(F, "Shell", name .. "Floor", x0 - 2, x1 + 2, -1, 0, z0 - 2, z1 + 2, o.floor or K.P.floor, o.floorMat)
	K.box(F, "Shell", name .. "Lid", x0 - 2, x1 + 2, h, h + 1, z0 - 2, z1 + 2, o.lid or K.P.dome)
	K.wall(F, name .. "Wall", x0 - 2, x1 + 2, 0, h, z0 - 2, z0, o.wall or K.P.wall, hole.n or {}, o.wallMat)
	K.wall(F, name .. "Wall", x0 - 2, x1 + 2, 0, h, z1, z1 + 2, o.wall or K.P.wall, hole.s or {}, o.wallMat)
	local FE = F * CFrame.new(0, 0, 0)
	-- (east and west walls: boxes along z with holes along z)
	for _, side in { { "e", x1, x1 + 2 }, { "w", x0 - 2, x0 } } do
		local list = hole[side[1]] or {}
		table.sort(list, function(a, b) return a[1] < b[1] end)
		local z = z0
		for _, hl in list do
			if hl[1] > z then K.box(F, "Shell", name .. "Wall", side[2], side[3], 0, h, z, hl[1], o.wall or K.P.wall, o.wallMat) end
			if hl[3] < h then K.box(F, "Shell", name .. "Wall", side[2], side[3], hl[3], h, hl[1], hl[2], o.wall or K.P.wall, o.wallMat) end
			z = hl[2]
		end
		if z < z1 then K.box(F, "Shell", name .. "Wall", side[2], side[3], 0, h, z, z1, o.wall or K.P.wall, o.wallMat) end
	end
end
-- a boxing ring S across at F (look along one side of the mat): skirt, apron, canvas, slim posts with slim vinyl
-- corner pads (one corner red, the opposite blue), three ropes, steps; the boxing spot on the mat (Ring, Half), a light
-- beam with two lamps over it at lampY
function K.ring(F, S, idx, lampY)
	local h = S / 2
	local RH = 1.4
	K.box(F, "Shell", "RingBase", -h, h, 0, RH, -h, h, "3c4048", MAT.Fabric)
	K.box(F, "Scenery", "RingApron", -h - 0.1, h + 0.1, RH - 0.4, RH - 0.04, -h - 0.1, h + 0.1, K.P.creamHi)
	K.box(F, "Scenery", "RingMat", -h + 0.8, h - 0.8, RH, RH + 0.08, -h + 0.8, h - 0.8, K.P.canvas, MAT.Fabric)
	local po = h - 1.1
	for _, cx in { -1, 1 } do for _, cz in { -1, 1 } do
		K.cyl(F, "Scenery", "RingPost", cx * po, RH + 0.04, RH + 5, cz * po, 0.7, K.P.steel)
		K.cyl(F, "Scenery", "RingPostCap", cx * po, RH + 5, RH + 5.3, cz * po, 0.95, K.P.dark)
		local col = if cx < 0 and cz < 0 then "8f4a45" elseif cx > 0 and cz > 0 then "4a6585" else K.P.creamHi
		K.cyl(F, "Scenery", "CornerPad", cx * po, RH + 1.15, RH + 4.45, cz * po, 0.95, col)
		for _, y in { RH + 2.2, RH + 3.4 } do K.cyl(F, "Scenery", "CornerStrap", cx * po, y - 0.06, y + 0.06, cz * po, 1.0, K.P.pier) end
	end end
	for _, y in { RH + 1.6, RH + 2.8, RH + 4.0 } do
		for _, s in { -1, 1 } do
			K.rod(F, "Scenery", "RingRope", Vector3.new(-po + 0.4, y, s * po), Vector3.new(po - 0.4, y, s * po), 0.32, K.P.creamHi)
			K.rod(F, "Scenery", "RingRope", Vector3.new(s * po, y, -po + 0.4), Vector3.new(s * po, y, po - 0.4), 0.32, K.P.creamHi)
		end
	end
	K.box(F, "Shell", "RingStep", -1.6, 1.6, 0, RH / 2, h, h + 1.2, K.P.pier2)
	K.box(F, "Shell", "RingStep", -1.6, 1.6, RH / 2, RH, h, h + 0.6, K.P.pier2)
	local m = K.gameSpot(F, "box", RH + 0.08, { Ring = idx, Half = h - 0.8 })
	if lampY then
		K.box(F, "Scenery", "LampBeam", -h + 1, h - 1, lampY, lampY + 0.4, -0.2, 0.2, K.P.cream, nil, { ghost = true })
		for _, s in { -1, 1 } do
			K.cyl(F, "Scenery", "RodToBeam", s * (h - 1.5), lampY + 0.4, lampY + 6, 0, 0.14, K.P.cream, nil, { ghost = true })
			K.cyl(F, "Scenery", "LampShade", s * 4, lampY - 1.1, lampY, 0, 1.8, K.P.dark, nil, { ghost = true })
			K.light(K.cyl(F, "Scenery", "Lamp", s * 4, lampY - 1.2, lampY - 1.1, 0, 1.5, K.P.warm, MAT.Neon, { ghost = true }), 22, 0.8)
		end
	end
	return m
end
-- tall heavy bags (3x as tall as wide) on short chains from a rail along F's x at z, from x0 to x1
function K.bags(F, x0, x1, z)
	K.box(F, "Scenery", "BagRail", x0 - 1, x1 + 1, 10.4, 10.9, z - 0.2, z + 0.2, K.P.steel, nil, { ghost = true })
	local n = math.max(2, math.floor((x1 - x0) / 4.5) + 1)
	for i = 0, n - 1 do
		local x = x0 + i * (x1 - x0) / (n - 1)
		K.cyl(F, "Scenery", "BagChain", x, 8.9, 10.4, z, 0.16, K.P.steel)
		K.cyl(F, "Shell", "HeavyBag", x, 2.8, 8.9, z, 2.0, "6e4a44")
		K.cyl(F, "Scenery", "BagBand", x, 2.65, 3.1, z, 2.06, K.P.creamHi)
	end
end
-- tall lockers in a bank against a wall, facing F's look (len along x), a door per 1.8
function K.lockers(F, len)
	K.box(F, "Shell", "LockerBody", -len / 2, len / 2, 0.35, 7.7, 0, 1.6, K.P.pier)
	K.box(F, "Scenery", "LockerPlinth", -len / 2 + 0.05, len / 2 - 0.05, 0, 0.35, 0.12, 1.6, K.P.shell)
	K.box(F, "Scenery", "LockerCap", -len / 2 - 0.05, len / 2 + 0.05, 7.7, 7.9, -0.1, 1.6, K.P.cream)
	local n = math.floor(len / 1.8)
	for i = 0, n - 1 do
		local x = -len / 2 + len * (i + 0.5) / n
		K.box(F, "Scenery", "LockerDoor", x - 0.8, x + 0.8, 0.6, 7.45, -0.06, 0, "6c6862")
		for _, y in { 6.6, 6.95 } do K.box(F, "Scenery", "LockerVent", x - 0.45, x + 0.45, y, y + 0.14, -0.1, -0.06, K.P.shell) end
		K.box(F, "Scenery", "LockerHandle", x + 0.48, x + 0.6, 3.7, 4.5, -0.18, -0.06, "b8bcc0")
	end
end
-- (everything in F: the Square's F is the identity, the Concourse's turns it to open south)
-- THE GYM: a room x0..x1, z0..z1 (in F) open on its west side (o.open = { x, za, zb }: the opening's wall line and
-- width), a rubber floor, padded lower walls, four rings (o.rings) with their spots and lamps, heavy bags on the far
-- wall, speed bags and a conditioning corner on the north wall, mirrors on the south wall, a round timer over the
-- opening; the LOCKER ROOM off it (o.locker = { x0, x1, z0, z1, door = { xa, xb } } on the gym's south wall)
function K.gym(F, o)
	local x0, x1, z0, z1, h = o.x0, o.x1, o.z0, o.z1, o.h
	local lk = o.locker
	K.box(F, "Shell", "GymFloor", x0, x1 + 2, -1, 0, z0 - 2, z1 + 2, K.P.gymFloor, MAT.Rubber)
	K.box(F, "Shell", "GymLid", x0, x1 + 2, h, h + 1, z0 - 2, z1 + 2, K.P.dome)
	K.box(F, "Shell", "GymWall", x1, x1 + 2, 0, h, z0 - 2, z1 + 2, K.P.gymWall)
	K.box(F, "Shell", "GymWall", x0, x1, 0, h, z0 - 2, z0, K.P.gymWall)
	if lk then
		K.wall(F, "GymWall", x0, x1, 0, h, z1, z1 + 2, K.P.gymWall, { { lk.door[1], lk.door[2], 10 } })
	else
		K.box(F, "Shell", "GymWall", x0, x1, 0, h, z1, z1 + 2, K.P.gymWall)
	end
	-- padded lower walls (smooth vinyl) with a cream cap
	K.box(F, "Scenery", "GymPad", x1 - 0.35, x1, 0, 5, z0, z1, K.P.pier)
	K.box(F, "Scenery", "GymPad", x0 + 0.4, x1 - 0.35, 0, 5, z0, z0 + 0.35, K.P.pier)
	K.box(F, "Scenery", "GymPadCap", x1 - 0.45, x1, 5, 5.3, z0, z1, K.P.cream)
	K.box(F, "Scenery", "GymPadCap", x0 + 0.4, x1 - 0.45, 5, 5.3, z0, z0 + 0.45, K.P.cream)
	for i, r in o.rings do K.ring(F * CFrame.new(r[1], 0, r[2]) * CFrame.Angles(0, math.pi / 2, 0), 22, i, h - 7) end
	-- girders over the rings, panels between
	for _, x in { (o.rings[1][1] + o.rings[2][1]) / 2, x0 + 4, x1 - 4 } do K.box(F, "Scenery", "Girder", x - 0.7, x + 0.7, h - 1.6, h, z0, z1, K.P.cream, nil, { ghost = true }) end
	for _, x in { o.rings[1][1], o.rings[2][1] } do K.panel(F, x, h, 0, 3, 10, { bright = 0.45 }) end
	K.bags(F * CFrame.new(x1 - 3.5, 0, (z0 + z1) / 2) * CFrame.Angles(0, math.pi / 2, 0), -((z1 - z0) / 2 - 6), (z1 - z0) / 2 - 6, 0)
	-- the north wall: speed bags under round boards, a kettlebell rack and a medicine-ball rack between
	for _, x in { x0 + 10, x0 + 18 } do
		local Fs = F * CFrame.new(x, 0, z0 + 0.4) * CFrame.Angles(0, math.pi, 0)
		K.box(Fs, "Scenery", "SpeedBagBracket", -0.3, 0.3, 6.95, 7.25, -2.4, 0, K.P.pier2)
		K.cyl(Fs, "Scenery", "SpeedBagBoard", 0, 7.25, 7.65, -2.4, 3.4, K.P.woodDark, MAT.Wood)
		K.cyl(Fs, "Scenery", "SpeedBagSwivel", 0, 6.6, 7.25, -2.4, 0.16, K.P.steel)
		K.ball(Fs, "Scenery", "SpeedBag", 0, 6.0, -2.4, 1.05, "7a4842")
	end
	local Fk = F * CFrame.new(x1 - 22, 0, z0 + 1.6) * CFrame.Angles(0, math.pi, 0)
	for _, y in { 0.9, 2.6 } do K.box(Fk, "Scenery", "KbShelf", -4.5, 4.5, y, y + 0.3, -1.3, 1.3, K.P.cream) end
	for _, x in { -4.25, 4.25 } do for _, z in { -1.05, 1.05 } do K.box(Fk, "Shell", "KbLeg", x - 0.18, x + 0.18, 0, 2.85, z - 0.18, z + 0.18, K.P.pier2) end end
	for i = 0, 4 do K.ball(Fk, "Scenery", "Kettlebell", -3.6 + i * 1.8, 3.55, 0, 1.3, K.P.steel) end
	for i = 0, 3 do K.ball(Fk, "Scenery", "Kettlebell", -2.7 + i * 1.8, 1.95, 0, 1.5, K.P.pier2) end
	local Fm = F * CFrame.new(x1 - 12, 0, z0 + 1.6) * CFrame.Angles(0, math.pi, 0)
	for _, y in { 0.9, 2.8 } do K.box(Fm, "Scenery", "BallShelf", -3.4, 3.4, y, y + 0.3, -1.3, 1.3, K.P.cream) end
	for _, x in { -3.15, 3.15 } do for _, z in { -1.05, 1.05 } do K.box(Fm, "Shell", "BallLeg", x - 0.18, x + 0.18, 0, 3.05, z - 0.18, z + 0.18, K.P.pier2) end end
	for i, col in { "6c6862", K.P.woodDark, K.P.steel } do
		K.ball(Fm, "Scenery", "MedBall", -2.2 + (i - 1) * 2.2, 2.1, 0, 1.9, col)
		K.ball(Fm, "Scenery", "MedBall", -2.2 + (i - 1) * 2.2, 4.0, 0, 1.9, col)
	end
	-- the round timer over the far end, facing the opening
	local Ft = F * CFrame.new(x1 - 0.1, 15.5, (z0 + z1) / 2) * CFrame.Angles(0, -math.pi / 2, 0)
	K.cyl(Ft * CFrame.Angles(math.pi / 2, 0, 0), "Scenery", "TimerRim", 0, -0.18, 0.18, 0, 6.2, K.P.cream)
	K.cyl(Ft * CFrame.Angles(math.pi / 2, 0, 0), "Scenery", "TimerFace", 0, 0.18, 0.42, 0, 5.4, "2c2f36")
	-- the locker room
	if lk then
		K.box(F, "Shell", "LockerFloor", lk.x0 - 2, lk.x1 + 2, -1, 0, lk.z0 - 2, lk.z1 + 2, K.P.tile, MAT.CeramicTiles)
		K.box(F, "Shell", "LockerLid", lk.x0 - 2, lk.x1 + 2, 12, 13, lk.z0 - 2, lk.z1 + 2, K.P.dome)
		K.box(F, "Shell", "LockerWall", lk.x0 - 2, lk.x0, 0, 12, lk.z0 - 2, lk.z1 + 2, K.P.gymWall)
		K.box(F, "Shell", "LockerWall", lk.x1, lk.x1 + 2, 0, 12, lk.z0 - 2, lk.z1 + 2, K.P.gymWall)
		K.box(F, "Shell", "LockerWall", lk.x0, lk.x1, 0, 12, lk.z1, lk.z1 + 2, K.P.gymWall)
		K.wall(F, "LockerWall", lk.x0, lk.x1, 0, 12, lk.z0 - 2, lk.z0, K.P.gymWall, { { lk.door[1], lk.door[2], 10 } })
		local len = lk.x1 - lk.x0 - 1
		K.lockers(F * CFrame.new((lk.x0 + lk.x1) / 2, 0, lk.z1 - 0.05 - 1.6), len)
		K.bench(F * CFrame.new((lk.x0 + lk.x1) / 2, 0, (lk.z0 + lk.z1) / 2 + 2) * CFrame.Angles(0, math.pi, 0), len - 8)
		K.panel(F, (lk.x0 + lk.x1) / 2, 12, (lk.z0 + lk.z1) / 2, 10, 3)
	end
end
-- THE GOLF ROOM (hub-minigames' SLAP GOLF: 44 x 80 of course built by MiniGolf on the spot): a room x0..x1, z0..z1 in F,
-- h high, its door at o.door = { wall x, za, zb } on its east wall; the spot 10 studs of floor in from the door's end
-- (north) plus half the course, its look south; beams, a panel over each hole
function K.golfRoom(F, o)
	local side, south = o.doorSide or "e", o.doorEnd == "s"
	K.room(F, "Golf", o.x0, o.x1, o.z0, o.z1, o.h, { floor = K.P.carpet, floorMat = MAT.Fabric, holes = { [side] = { { o.door[2], o.door[3], 10 } } } })
	local cx = (o.x0 + o.x1) / 2
	local cz = if south then o.z1 - 10 - 40 else o.z0 + 10 + 40
	K.gameSpot(F * CFrame.new(cx, 0, cz) * CFrame.Angles(0, if south then 0 else math.pi, 0), "golf") -- (look away from the door's end)
	for z = o.z0 + 12, o.z1 - 6, 12 do K.box(F, "Scenery", "GolfBeam", o.x0, o.x1, o.h - 1.4, o.h, z - 0.5, z + 0.5, K.P.cream, nil, { ghost = true }) end
	-- (neutral light: the warm panels over-saturated the lawn and rails, hub-minigames' note)
	for _, dx in { -15, 0, 15 } do for _, dz in { -20, 20 } do K.panel(F, cx + dx, o.h, cz + dz, 6, 12, { bright = 0.45, lightHex = "eef2f6" }) end end
	K.panel(F, cx, o.h, if south then o.z1 - 5 else o.z0 + 5, 20, 3, { lightHex = "eef2f6" })
end
-- the place the lore session puts the code panel (lore-npcs' LoreNPCs / LoreSpots): F on a wall's face, its look out
function K.codePanelSpot(F) return K.marker(F, "Scenery", "CodePanelSpot", 0, 0, 0, 0, nil, { "CodePanelSpot" }) end
-- the HUBS terminal: a slim lit pillar with a screen and the travel prompt (HubTravelUI opens the chooser)
function K.travelTerminal(F)
	K.box(F, "Shell", "TravelPillar", -0.9, 0.9, 0, 5.6, -0.7, 0.7, K.P.pier2)
	local sc = K.box(F, "Scenery", "TravelScreen", -0.75, 0.75, 3.2, 5.2, -0.78, -0.7, K.P.screen)
	K.text(sc, Enum.NormalId.Front, { { "HUBS", K.P.amber, 0.4 }, { "TRAVEL", K.P.pale, 0.28 } })
	K.light(K.box(F, "Scenery", "TravelLight", -0.9, 0.9, 5.6, 5.8, -0.7, 0.7, K.P.amber, MAT.Neon, { ghost = true }), 8, 0.5, K.P.amber)
	local spot = K.marker(F, "TravelSpot", "TravelSpot", 0, 0, -1.4, 0, nil, nil, { size = Vector3.new(1, 0.2, 1) })
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "TravelPrompt"; pr.ActionText = "Travel"; pr.ObjectText = "Hubs"; pr.HoldDuration = 0; pr.MaxActivationDistance = 10
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.RequiresLineOfSight = false
	pr:SetAttribute("HubTravel", true)
	pr.Parent = spot
	return spot
end

-- ------------------------------------------------------------------------------------------------ the pads
-- every pad keeps the QueuePads contract (play-party's Matches / QuickJoin / PadGlow): a Model in the hub's QueuePads
-- with Mode, Teams, Size, PadId, Bank (+ Hub, Design); parts Base, Side<i> (Team; LookVector away from where people
-- come from: QUICK JOIN faces you along -LookVector), Glow (Team, a PointLight in it: PadGlow dims and lights it), Slot
-- specks (Team, Slot, Off: Matches' places), Edge, and the Sign with labels Status and Sub (Matches writes them)
local function padModel(md, bank, name, design)
	local m = Instance.new("Model"); m.Name = name
	m:SetAttribute("Mode", md.id); m:SetAttribute("Teams", md.teams); m:SetAttribute("Size", md.size)
	m:SetAttribute("PadId", name); m:SetAttribute("Bank", bank); m:SetAttribute("Hub", S.hub); m:SetAttribute("Design", design)
	m.Parent = K.folder("QueuePads")
	return m
end
local function slotSpeck(F, m, x, y, z, team, slot)
	local q = K.part("Scenery", "Slot", F * CFrame.new(x, y, z), Vector3.new(0.05, 0.05, 0.05), K.TEAM[team], nil, { ghost = true, tr = 1, noshadow = true, parent = m })
	q:SetAttribute("Team", team); q:SetAttribute("Slot", slot); q:SetAttribute("Off", 1)
	return q
end
local function padGlow(F, m, x0, x1, y0, y1, z0, z1, team)
	local g = K.box(F, "Scenery", "Glow", x0, x1, y0, y1, z0, z1, K.TEAM[team], MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.78 })
	g:SetAttribute("Team", team)
	local l = Instance.new("PointLight"); l.Color = c3(K.TEAM[team]); l.Range = 7; l.Brightness = 0.12; l.Shadows = false; l.Parent = g
	return g
end
local function padSign(F, m, md, w, h, x, y, z, face)
	local counts = {}
	for t = 1, md.teams do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(K.TEAM[t], md.size)) end
	local p = K.box(F, "Scenery", "Sign", x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - 0.25, z, "20232e", nil, { parent = m })
	local rv = S.style == "rivals"
	K.text(p, face, { { md.title, K.P.pale, if rv then 0.26 else 0.3 }, { md.kind, "c8cdd6", if rv then 0.11 else 0.13, "S" }, { table.concat(counts, "   vs   "), "ffffff", if rv then 0.4 else 0.33 },
		{ "step on a side to queue", "c8c8dc", if rv then 0.12 else 0.15, "S" } }, { names = { [3] = "Status", [4] = "Sub" }, pps = 46, bright = if rv then 2 else nil })
	if rv then -- (rivals: the board in a pale housing, a bar per side in its team's colour under it: outside the pad's model)
		K.box(F, "Scenery", "PadBoardHousing", x - w / 2 - 0.35, x + w / 2 + 0.35, y - h / 2 - 0.35, y + h / 2 + 0.35, z - 0.43, z - 0.1, K.R.struct)
		local n = md.teams
		for t = 1, n do
			local xa = x - w / 2 + (t - 1) * w / n
			K.box(F, "Scenery", "PadBoardBar", xa + 0.2, xa + w / n - 0.2, y - h / 2 - 0.7, y - h / 2 - 0.36, z - 0.4, z - 0.12, K.TEAM[t], MAT.Neon, { ghost = true, noshadow = true })
		end
	end
	return p
end
-- (1) PLAYER SPOTS: a low stage in a bay, F at the bay's mouth on the floor, its look into the bay (W across, D deep).
-- a lit nosing (each side's stretch of its line in the side's colour: Glow), the sides split by low dividers with the
-- mode's name on them, a marked spot per player (a rim in the side's colour, a dark disc; Matches' Slot speck on it),
-- a soft light over each side; the Sign over the mouth (o.signY, o.signZ: on the bay's beam, its face to the hall)
function K.spotsPad(F, md, bank, name, o)
	o = o or {}
	local W, D = o.w or 13.4, o.d or 10.4
	local m = padModel(md, bank, name, "spots")
	K.box(F, "Scenery", "Base", -W / 2, W / 2, 0, 0.4, -D, 0, K.P.padBase, nil, { parent = m, solid = true })
	K.box(F, "Scenery", "Edge", -W / 2, W / 2, 0, 0.46, -0.4, 0.06, K.P.creamHi, nil, { parent = m, solid = true }) -- (the nosing)
	local n = md.teams
	local gap = 0.5
	local sw = (W - (n - 1) * gap) / n
	for t = 1, n do
		local xa = -W / 2 + (t - 1) * (sw + gap)
		local xb = xa + sw
		local sd = K.box(F, "Scenery", "Side" .. t, xa + 0.1, xb - 0.1, 0.4, 0.46, -D + 0.3, -0.45, "4d535c", nil, { parent = m, solid = false })
		sd:SetAttribute("Team", t)
		padGlow(F, m, xa + 0.3, xb - 0.3, 0.12, 0.32, 0.06, 0.12, t) -- (the nosing's line under its lip)
		local cols = if md.size >= 3 then 2 else 1
		local rows = math.ceil(md.size / cols)
		for sl = 1, md.size do
			local c, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
			local x = xa + sw * (c + 0.5) / cols
			local z = -1.0 - (D - 2.0) * (r + 0.5) / rows
			slotSpeck(F, m, x, 0.46, z, t, sl)
			K.cyl(F, "Scenery", "PlaceRim", x, 0.46, 0.49, z, math.min(2.4, sw / cols - 0.4), K.TEAM[t], MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.5 })
			K.cyl(F, "Scenery", "PlaceDisc", x, 0.48, 0.52, z, math.min(2.0, sw / cols - 0.8), K.P.dark, nil, { ghost = true, parent = m })
		end
		K.light(K.box(F, "Scenery", "SideLamp", (xa + xb) / 2 - 0.5, (xa + xb) / 2 + 0.5, (o.lampY or 12) - 0.2, o.lampY or 12, -D / 2 - 0.5, -D / 2 + 0.5, K.P.pier, nil, { ghost = true, tr = 1, parent = m }),
			14, 0.9, "fff4e6", { kind = "SpotLight", angle = 75 })
	end
	for t = 1, n - 1 do
		local x = -W / 2 + t * (sw + gap) - gap / 2
		local dv = K.box(F, "Shell", "PadDivider", x - 0.22, x + 0.22, 0.4, 1.6, -D + 0.8, -1.4, K.P.cream)
		K.box(F, "Scenery", "PadDividerCap", x - 0.3, x + 0.3, 1.6, 1.72, -D + 0.7, -1.3, K.P.dark)
		K.text(dv, Enum.NormalId.Left, { { md.title, K.P.dark, 0.7 } }); K.text(dv, Enum.NormalId.Right, { { md.title, K.P.dark, 0.7 } })
	end
	padSign(F, m, md, o.signW or (W - 0.6), o.signH or (if S.style == "rivals" then 3.0 else 2.0), 0, o.signY or 11.5, o.signZ or 2.0, Enum.NormalId.Back) -- (rivals: a bigger board)
	return m
end
-- (2) PLATFORM (the Atrium): one of an octagon side's two pads on the ground ring. Fk = the side's frame (its look out,
-- x to the right, the side's middle line at x 0); left = the side's left half. Raised 1.1 from rin to rout, its outer end
-- slanted along the octagon's corner line; a step at its front; a lit rim along the front edge, its stretch per side in
-- the side's colour (Glow); a thin dark line between the sides; a marked place per player; the Sign floating over the
-- platform's middle, its face to the middle of the room
local T225 = math.tan(math.rad(22.5))
K.T225 = T225
function K.platformPad(Fk, left, md, bank, name, rin, rout, o)
	o = o or {}
	local m = padModel(md, bank, name, "platform")
	local g = 0.7 -- (the gap at the side's middle line)
	local xi, xo = rin * T225 - 0.8, rout * T225 - 0.8 -- (the slanted end's x at the inner edge, at the outer edge)
	local x0, x1 = if left then -xi else g, if left then -g else xi
	local H = 1.1
	K.box(Fk, "Scenery", "Base", x0, x1, 0, H, -rout, -rin, K.P.padBase, nil, { parent = m, solid = true })
	K.slant(Fk, "Scenery", "BaseWing", if left then -xi else xi, if left then -xo else xo, -rin, -rout, 0, H, K.P.padBase, nil, { parent = m, solid = true })
	K.box(Fk, "Scenery", "PadStep", x0, x1, 0, 0.55, -rin, -rin + 1.1, K.P.padBase, nil, { parent = m, solid = true })
	K.box(Fk, "Scenery", "Edge", x0, x1, H - 0.1, H + 0.07, -rin - 0.45, -rin + 0.12, K.P.creamHi, nil, { parent = m, solid = true })
	local n = md.teams
	local sw = (x1 - x0) / n
	for t = 1, n do
		local xa, xb = x0 + (t - 1) * sw, x0 + t * sw
		local sd = K.box(Fk, "Scenery", "Side" .. t, xa + 0.15, xb - 0.15, H, H + 0.06, -rout + 0.5, -rin - 0.5, "4d535c", nil, { parent = m, solid = false })
		sd:SetAttribute("Team", t)
		padGlow(Fk, m, xa + 0.3, xb - 0.3, H + 0.02, H + 0.1, -rin - 0.42, -rin - 0.1, t) -- (the front rim's stretch)
		local cols = if md.size >= 3 then 2 else 1
		local rows = math.ceil(md.size / cols)
		local depth = rout - rin - 2.4
		for sl = 1, md.size do
			local c, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
			local x = xa + sw * (c + 0.5) / cols
			local z = -rin - 1.6 - depth * (r + 0.5) / rows
			slotSpeck(Fk, m, x, H + 0.06, z, t, sl)
			K.cyl(Fk, "Scenery", "PlaceRim", x, H + 0.06, H + 0.09, z, math.min(2.4, sw / cols - 0.5), K.TEAM[t], MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.5 })
			K.cyl(Fk, "Scenery", "PlaceDisc", x, H + 0.08, H + 0.12, z, math.min(2.0, sw / cols - 0.9), K.P.dark, nil, { ghost = true, parent = m })
		end
		if t < n then K.box(Fk, "Scenery", "PadLine", xb - 0.08, xb + 0.08, H + 0.06, H + 0.09, -rout + 0.6, -rin - 0.6, K.P.screen, nil, { ghost = true, parent = m }) end
	end
	-- a soft light over it (under the gallery), the floating sign
	local xm, zm = (x0 + x1) / 2, -(rin + rout) / 2
	K.light(K.box(Fk, "Scenery", "PadLamp", xm - 0.5, xm + 0.5, (o.lampY or 13.4) - 0.2, o.lampY or 13.4, zm - 0.5, zm + 0.5, K.P.pier, nil, { ghost = true, tr = 1, parent = m }),
		14, 0.55, "f2f4f8", { kind = "SpotLight", angle = 80 })
	padSign(Fk, m, md, math.min(x1 - x0 - 0.6, 7.4), 3.0, xm, o.signY or 8.8, zm + 0.125, Enum.NormalId.Back)
	return m
end
-- (3) THE GATE: a framed portal set into a wall that you step into. F at its mouth on the floor, its look into the
-- alcove (W wide, D deep). Each side (team) has its part of the alcove's floor (a half; thirds for 1v1v1) split by a slim
-- mullion, a thin light up its jamb and a thin rim at its front (Glow), a marked place per player; the mode, its kind and
-- the count on the sign over the frame, facing out
function K.gatePad(F, md, bank, name, o)
	o = o or {}
	local W, D = o.w or 10, o.d or 5
	local m = padModel(md, bank, name, "gate")
	K.box(F, "Scenery", "Base", -W / 2, W / 2, 0, 0.3, -D, 0, K.P.padBase, nil, { parent = m, solid = true })
	K.box(F, "Scenery", "Edge", -W / 2 - 0.8, W / 2 + 0.8, 0, 0.36, -0.5, 0.3, K.P.creamHi, nil, { parent = m, solid = true }) -- (the sill)
	local n = md.teams
	local gap = 0.36
	local sw = (W - (n - 1) * gap) / n
	for t = 1, n do
		local xa = -W / 2 + (t - 1) * (sw + gap)
		local xb = xa + sw
		local s = K.box(F, "Scenery", "Side" .. t, xa, xb, 0.3, 0.42, -D + 0.3, -0.45, "4d535c", nil, { parent = m, solid = false })
		s:SetAttribute("Team", t)
		padGlow(F, m, xa + 0.2, xb - 0.2, 0.42, 0.47, -0.62, -0.5, t) -- (a thin rim at the side's front)
		-- the places: a grid in the side's part (Matches' specks), each marked with a small rimmed disc
		local cols = if md.size >= 3 then 2 else 1
		local rows = math.ceil(md.size / cols)
		for sl = 1, md.size do
			local c, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
			local x = xa + sw * (c + 0.5) / cols
			local z = -0.6 - (D - 1.2) * (r + 0.5) / rows
			slotSpeck(F, m, x, 0.36, z, t, sl)
			K.cyl(F, "Scenery", "PlaceRim", x, 0.42, 0.45, z, 1.6, K.TEAM[t], MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.5 })
			K.cyl(F, "Scenery", "PlaceDisc", x, 0.44, 0.48, z, 1.3, K.P.dark, nil, { ghost = true, parent = m })
		end
	end
	-- the frame: steel posts, a head; a thin light up each outer jamb in its side's colour (Glow too); mullions
	for i, s in { -1, 1 } do
		K.box(F, "Scenery", "GatePost", s * (W / 2 - 0.3), s * (W / 2 + 0.8), 0, 10.8, -0.6, 0.5, K.P.steel, nil, { solid = true }) -- (proud of the walls' pilasters)
		padGlow(F, m, s * (W / 2 - 0.36), s * (W / 2 - 0.3), 0.6, 9.2, -0.4, 0.2, if s < 0 then 1 else n)
	end
	K.box(F, "Scenery", "GateHead", -W / 2 - 0.8, W / 2 + 0.8, 9.4, 10.8, -0.6, 0.5, K.P.steel, nil, { solid = true })
	for t = 1, n - 1 do
		local x = -W / 2 + t * (sw + gap) - gap / 2
		K.box(F, "Scenery", "GateMullion", x - 0.16, x + 0.16, 0.42, 9.4, -0.5, 0.3, K.P.steel)
	end
	-- the back: a matte panel proud of the wall, framed; a low warm fill under the head (a dim, readable alcove)
	K.box(F, "Scenery", "GateBack", -W / 2 + 0.3, W / 2 - 0.3, 0.3, 9.4, -D, -D + 0.12, "3a3d42", nil, { noshadow = true })
	for _, y in { 3.2, 6.4 } do K.box(F, "Scenery", "GateBackRail", -W / 2 + 0.3, W / 2 - 0.3, y - 0.08, y + 0.08, -D + 0.12, -D + 0.2, K.P.steel) end
	local rv = S.style == "rivals"
	if rv then -- (rivals: each side's part of the back glows softly in its team's colour: the pads the brightest, most colourful things in view)
		for t = 1, n do
			local xa = -W / 2 + (t - 1) * (sw + gap)
			K.box(F, "Scenery", "GateBackTint", xa + 0.6, xa + sw - 0.6, 1.0, 8.8, -D + 0.12, -D + 0.17, K.TEAM[t], MAT.Neon, { ghost = true, noshadow = true, tr = 0.86 })
		end
	end
	K.light(K.box(F, "Scenery", "GateFill", -0.5, 0.5, 9.0, 9.2, -D / 2 - 0.5, -D / 2 + 0.5, K.P.pier, nil, { ghost = true, tr = 1, parent = m }), 9, if rv then 0.6 else 0.35, if rv then "f2f4f8" else K.P.warm)
	padSign(F, m, md, if rv then W - 0.4 else W + 1.6, if rv then 4.0 else 2.8, 0, if rv then 14.5 else 12.3, 0.45, Enum.NormalId.Back) -- (rivals: its housing clear of the fins' pilasters)
	return m
end

-- (4) THE PAD (20 Nov 2026, the owner: "also the new pads look hideas referenbce rivals please"): ONE pad for every hub,
-- a floor plate you step onto, in Rivals' grammar (a plate one step up off the walkway, the teams facing across a low
-- divider, a spot per player, the count screen right behind, the mode's name over it) in our own shapes
-- (tools/roblox/pad_models.py: the plinth, the divider, the foot-plates, the pale frame; K.importKit brings them in).
-- F = the plinth's front middle on the walkway floor, its look into the bay (-Z). Footprint (round 4) 12.74 wide x
-- 13.4 deep (z 0..-13.4); the gantry at its back is 11.8 wide, 14.4 high (z -11.35..-13.25), its board y 9.25..13.55;
-- (round 7) the board in its frame reaches y 14.8 + o.rise; turned by o.turn its back corner reaches about z -15: give it
-- a bay at least 13 wide, 15.5 deep (13.6 with no turn) and 15.2 + o.rise high, its floor flat. o.lampY: the lamps over
-- the teams (default 13, o.lampY = false: none). The pieces: K.importKit("pads", K.PAD_KIT) once per build.
-- The contract (play-party, 20 Nov; side-session-notes/HUB-KIT-CONTRACTS.md): a Model in QueuePads; Side1..N flat
-- plates (local Y up) where people stand, each looking so that minus its look faces the way a joiner should look (the
-- outer halves at each other, a middle third out at the walkway: QUICK JOIN); a Slot speck per player on its own plate;
-- a Glow (Team) per side for PadGlow; the Status and Sub labels inside the Model (the count screen)
-- (round 3, 20 Nov, after two judge rounds: the team's colour is the plate itself, muted, lighting up when the side is
-- taken; big pale marks in a line per team, the teams facing across a low pale kerb; no strips, no blocks; the board
-- on an open gantry at the plate's back edge, above the players' heads; the mode across the plinth's front)
-- (round 4, judge round 3: the plates glow (the Glow sheet under the marks, half lit at rest), round pale marks, a wider
-- kerb, thick gantry posts into the plinth, the board raised clear of hats with the mode as big as the counts, and the
-- mode's blade on the pad's own gantry, not a pier, so it never reads over the next pad)
K.PAD = { w = 12.4, d = 13.4, top = 1.2, frameW = 10.8, frameH = 14.2 }
K.PAD_KIT = 102127176872071 -- (the pad kit's Model asset, round 6: tools/roblox/pad_models.py, uploaded 20 Nov; round 5 was 81129917407402; round 7 builds its board in Lua and leaves out jpad_totem)
K.TEAM_MUTED = { "b0578f", "3f8fa8", "b08a46" } -- (the teams' colours at rest on a plate; the Glow is the full colour)
K.TEAM_GLOW = {} -- (a palette's own lane-glow colours, when it gives them: TeamColors entries' glow; else K.glowHex derives one)
-- (20 Nov, the owner: "maybe lets use differnt accent colors than the rivals one please") the teams' colours come from
-- ONE place, ReplicatedStorage.Jankfire.TeamColors (play-party's module: the matches read it too, so pads and matches
-- agree; its OLD switch brings back the values above). Read at build time; without the module the values above stand
do
	local jf = game:GetService("ReplicatedStorage"):FindFirstChild("Jankfire")
	local mod = jf and jf:FindFirstChild("TeamColors")
	if mod and mod:IsA("ModuleScript") then
		local ok, TC = pcall(require, mod:Clone())
		if ok and type(TC) == "table" and type(TC.list) == "function" then
			local list = TC.list()
			for i = 1, 3 do
				local e = list[i]
				if e then
					K.TEAM[i] = (string.gsub(e.hex, "#", "")); K.TEAM_MUTED[i] = (string.gsub(e.muted, "#", ""))
					if type(e.glow) == "string" then K.TEAM_GLOW[i] = (string.gsub(e.glow, "#", "")) end -- (a set's own lane glow: pastels)
				end
			end
		end
	end
end
local function padPiece(m, F, tmpl, cf, solid)
	local lib = game:GetService("ServerStorage"):FindFirstChild("JankfireMeshes")
	local t = lib and lib:FindFirstChild(tmpl)
	if not t then S.missing = (S.missing or 0) + 1; return nil end
	local c = t:Clone()
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = solid == true; d.CanQuery = solid == true; d.CanTouch = solid == true
			d:SetAttribute("Hub", S.hub); S.count += 1
		end
	end
	c:PivotTo(S.site * F * cf)
	c.Parent = m
	return c
end
-- (main, 20 Nov: in the photos the lit lanes washed out to yellow and pale cyan) the glow's own colour: the team's hue,
-- deeper and more saturated, so neon keeps it under the bloom (the counts and the HUD keep the team's own hex)
function K.glowHex(t)
	if K.TEAM_GLOW[t] then return K.TEAM_GLOW[t] end -- (the palette's own: pastels need a richer glow than they derive to)
	local c = c3(K.TEAM[t])
	local h, s, v = c:ToHSV()
	if s < 0.2 then return K.TEAM[t] end -- (a pale team stays itself)
	return Color3.fromHSV(h, math.min(1, s * 1.15), v * 0.78):ToHex()
end
-- (20 Nov ~23:30, the owner, via main: "Yes, those": the Rotunda-era pads, v641 / v743) THE CLASSIC PAD, now the default
-- style (K.PAD_STYLE; o.style = "plinth" brings back round 7): a flush pad you walk onto, no step, set in a shallow tray:
-- a dark base, a soft plate per team with a neon Glow over it (dim and breathing while open, full while taken; PadGlow),
-- a dark gap between the sides, a chunky cream rim with a warm line on its inner edge; no marks (the places are specks);
-- sizes growing with the mode. Its board is NOT on the pad: a lit navy board on the bay's back wall (o.boardAt: a CFrame
-- in the hub's frame at the board's middle, its look out at the walkway; without it the pad stands its own cream back
-- panel), the mode's plaque over it (o.headerAt). F = the pad's front middle on the floor, its look into the bay (-Z).
-- o.dims = { wide, deep } overrides the mode's size for a bay that can't take it (the Concourse's 14.2-wide bays)
K.PAD_STYLE = "classic"
K.CLASSIC_SIZE = { ["1v1"] = { 12.4, 9.6 }, ["1v1v1"] = { 15.6, 9.6 }, ["2v2"] = { 13.6, 11 }, ["3v3"] = { 14.4, 11.2 }, ["4v4"] = { 15.6, 11.2 } }
function K.padClassic(F, md, bank, name, o)
	local m = padModel(md, bank, name, "classic")
	m:SetAttribute("RestSub", "") -- (Matches' resting Sub line: a hub says "step on a side" once, at its pads' entrance)
	local sz = o.dims or K.CLASSIC_SIZE[md.id] or { 13.6, 11 }
	local w, dp = sz[1], sz[2]
	local RIM, CREAM, LINE, BASE = 0.7, o.rim or "efe6d6", "fff1d8", o.base or "3a3631"
	-- the tray: a dark base, the rim round it (cream, a little proud), its warm inner line
	K.box(F, "Scenery", "Base", -w / 2, w / 2, 0, 0.14, -dp, 0, BASE, nil, { parent = m, solid = true })
	for _, r in { { -w / 2, w / 2, -RIM, 0 }, { -w / 2, w / 2, -dp, -dp + RIM }, { -w / 2, -w / 2 + RIM, -dp + RIM, -RIM }, { w / 2 - RIM, w / 2, -dp + RIM, -RIM } } do
		K.box(F, "Scenery", "Rim", r[1], r[2], 0, 0.34, r[3], r[4], CREAM, nil, { parent = m, solid = true })
	end
	local iw, idp = w / 2 - RIM, dp - RIM
	for _, r in { { -iw, iw, -RIM - 0.12, -RIM }, { -iw, iw, -idp, -idp + 0.12 }, { -iw, -iw + 0.12, -idp, -RIM }, { iw - 0.12, iw, -idp, -RIM } } do
		K.box(F, "Scenery", "RimLine", r[1], r[2], 0.3, 0.35, r[3], r[4], LINE, MAT.Neon, { parent = m, ghost = true, noshadow = true, tr = 0.25 })
	end
	-- the sides: n plates side by side across the tray, a dark 0.8 gap between them
	local n = md.teams
	local gap = 0.8
	local pw = (2 * iw - 0.4 - (n - 1) * gap) / n
	local z0, z1 = -RIM - 0.2, -idp + 0.2
	local zc, d = (z0 + z1) / 2, z0 - z1
	local cols = if md.size >= 4 then 2 else 1
	local rows = math.ceil(md.size / cols)
	for t = 1, n do
		local cx = -iw + 0.2 + pw / 2 + (t - 1) * (pw + gap)
		local xa, xb = cx - pw / 2, cx + pw / 2
		-- the plate: the team's soft colour, flat, its look so that minus it is where a joiner faces
		local face = if t == 1 then Vector3.xAxis elseif t == n then -Vector3.xAxis else Vector3.zAxis
		local c = Vector3.new(cx, 0.2, zc)
		local size = if math.abs(face.X) > 0.5 then Vector3.new(d, 0.12, pw) else Vector3.new(pw, 0.12, d)
		local sd = K.part("Scenery", "Side" .. t, F * CFrame.lookAt(c, c - face), size, K.TEAM_MUTED[t], MAT.SmoothPlastic, { parent = m, solid = true })
		sd:SetAttribute("Team", t)
		-- its Glow: a neon sheet over it in the team's richer colour, its light the same tint (never white)
		local g = K.box(F, "Scenery", "Glow", xa + 0.15, xb - 0.15, 0.265, 0.29, z1 + 0.15, z0 - 0.15, K.glowHex(t), MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.6 })
		g:SetAttribute("Team", t)
		g:SetAttribute("GlowOpen", 0.6); g:SetAttribute("GlowTaken", 0.15)
		g:SetAttribute("GlowLight", 0.7); g:SetAttribute("GlowRange", 7)
		local gl = Instance.new("PointLight"); gl.Color = c3(K.glowHex(t)); gl.Range = 7; gl.Brightness = 0.7; gl.Shadows = false; gl.Parent = g
		-- the places: specks inside the plate that never show (Matches' Slot, Off = 1), as on the Rotunda's pads
		for sl = 1, md.size do
			local cc, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
			local ox = if cols == 1 then 0 else (cc - 0.5) * (pw / 2)
			local oz = zc + d * (0.5 - (r + 0.5) / rows)
			local q = K.part("Scenery", "Slot", F * CFrame.new(cx + ox, 0.2, oz), Vector3.new(0.05, 0.05, 0.05), K.TEAM[t], nil, { ghost = true, tr = 1, noshadow = true, parent = m })
			q:SetAttribute("Team", t); q:SetAttribute("Slot", sl); q:SetAttribute("Off", 1)
		end
	end
	-- the board: on the bay's back wall (o.boardAt), else on a cream back panel the pad stands 0.8 behind itself
	local BW, BH = o.boardW or 12, o.boardH or 5.5
	local FB = o.boardAt
	if not FB then
		K.box(F, "Scenery", "BackPanel", -6.6, 6.6, 0, 13, -dp - 1.6, -dp - 0.8, CREAM, nil, { parent = m, solid = true })
		FB = F * CFrame.new(0, 9.6, -dp - 0.8) * CFrame.Angles(0, math.pi, 0) -- (its look back out at the walkway)
	end
	K.box(FB, "Scenery", "BoardFrame", -BW / 2 - 0.5, BW / 2 + 0.5, -BH / 2 - 0.5, BH / 2 + 0.5, -0.05, 0.4, "c9c5bc", nil, { parent = m })
	local counts = {}
	for t = 1, n do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(K.TEAM[t], md.size)) end
	local scr = K.box(FB, "Scenery", "Screen", -BW / 2, BW / 2, -BH / 2, BH / 2, -0.15, -0.05, "28324a", nil, { parent = m })
	-- (the counts' line is only as tall as one line of them can be wide, so the scaled text never breaks onto two lines)
	-- (21 Nov, the judges: one name per pad. With a plaque (o.headerAt) the plaque names the mode and the board only
	-- counts; without one the board's first line names it. o.boardTitle = true / false forces either)
	local cl = { table.concat(counts, if n == 2 then ' <font color="#8a93a6">vs</font> ' else "  "), "ffffff", if n == 2 then 0.44 else 0.36 }
	if o.boardTitle == false or (o.boardTitle == nil and o.headerAt ~= nil) then
		K.text(scr, Enum.NormalId.Front, { cl, { "", "c8d0e0", 0.1, "S" } }, { names = { "Status", "Sub" }, pps = 40, bright = 2, bg = "28324a", bgt = 0 })
	else
		K.text(scr, Enum.NormalId.Front, { { md.title .. "  " .. md.kind, "f2f0ea", 0.26 }, cl, { "", "c8d0e0", 0.1, "S" } },
			{ names = { [2] = "Status", [3] = "Sub" }, pps = 40, bright = 2, bg = "28324a", bgt = 0 })
	end
	K.light(scr, 14, 0.45, "dfe8ff")
	-- the mode's plaque over the board (o.headerAt), in the hub's sign family
	if o.headerAt then K.wordSign(o.headerAt, "Scenery", "PadHeader", o.headerW or 9, o.headerH or 2.4, 0, 0, 0, md.title, { accent = o.accent or S.accent, bg = "28324a" }) end
	return m
end
function K.pad(F, md, bank, name, o)
	o = o or {}
	if (o.style or K.PAD_STYLE) == "classic" then return K.padClassic(F, md, bank, name, o) end
	local m = padModel(md, bank, name, "plate")
	m:SetAttribute("RestSub", "") -- (Matches' resting Sub line, a2121b9: the hint is said once, at a hub's pads' entrance)
	local TOP = K.PAD.top
	padPiece(m, F, "jpad_plinth", CFrame.new(), true)
	if o.gantry == true then padPiece(m, F, "jpad_totem", CFrame.new(), true) end -- (round 7: a stem and a framed board instead)
	local n = md.teams
	local span = if n == 2 then { { -5.5, -0.5 }, { 0.5, 5.5 } } else { { -5.5, -2.3 }, { -1.3, 1.3 }, { 2.3, 5.5 } }
	local z0, z1 = -0.7, -11.4 -- (the lanes' front and back: they sit 0.4 down inside the plinth's rim)
	local zc = (z0 + z1) / 2
	for _, x in (if n == 2 then { 0 } else { -1.8, 1.8 }) do padPiece(m, F, "jpad_divider", CFrame.new(x, TOP, zc), true) end
	local lampY = if o.lampY == nil then 13 else o.lampY
	for t = 1, n do
		local xa, xb = span[t][1], span[t][2]
		local cx, w, d = (xa + xb) / 2, xb - xa, z0 - z1
		-- the lane: the team's colour (muted), flat, its look so that minus it is where a joiner faces
		local face = if t == 1 then Vector3.xAxis elseif t == n then -Vector3.xAxis else Vector3.zAxis
		local c = Vector3.new(cx, TOP + 0.03, zc)
		local size = if math.abs(face.X) > 0.5 then Vector3.new(d, 0.1, w) else Vector3.new(w, 0.1, d)
		local sd = K.part("Scenery", "Side" .. t, F * CFrame.lookAt(c, c - face), size, K.TEAM_MUTED[t], MAT.Concrete, { parent = m, solid = true })
		sd:SetAttribute("Team", t)
		-- the Glow (PadGlow: half lit while open, full while taken): a sheet over the lane, under the marks; its light
		-- short and low, so it lights the lane, not the pillars round it (judges, round 4)
		-- (round 6, judge round 5: the lane must read as its colour, brighter than anything round it; no lit edge bands:
		-- neon lane edges are the reference's device)
		local g = K.box(F, "Scenery", "Glow", xa + 0.15, xb - 0.15, TOP + 0.085, TOP + 0.1, z1 + 0.15, z0 - 0.15, K.glowHex(t), MAT.Neon, { ghost = true, noshadow = true, parent = m, tr = 0.45 })
		g:SetAttribute("Team", t)
		g:SetAttribute("GlowOpen", 0.45); g:SetAttribute("GlowTaken", 0.15) -- (PadGlow, play-party 4063e2e)
		g:SetAttribute("GlowLight", 0.7); g:SetAttribute("GlowRange", 5) -- (its light at rest: PadGlow a2121b9)
		local gl = Instance.new("PointLight"); gl.Color = c3(K.glowHex(t)); gl.Range = 5; gl.Brightness = 0.7; gl.Shadows = false; gl.Parent = g
		-- the marks: a line of raised pale discs per team (the teams face each other across the kerb); each Slot a disc
		-- of the team's colour on its mark that Matches shows while the place is taken
		local zs = { zc }
		if md.size == 2 then zs = { zc + 2.7, zc - 2.7 }
		elseif md.size == 3 then zs = { zc + 3.4, zc, zc - 3.4 }
		elseif md.size >= 4 then zs = { zc + 4.05, zc + 1.35, zc - 1.35, zc - 4.05 } end
		for sl, z in zs do
			padPiece(m, F, "jpad_spot", CFrame.new(cx, TOP + 0.1, z), false)
			local q = K.cyl(F, "Scenery", "Slot", cx, TOP + 0.4, TOP + 0.45, z, 1.1, K.glowHex(t), MAT.Neon, { ghost = true, tr = 1, noshadow = true, parent = m })
			q:SetAttribute("Team", t); q:SetAttribute("Slot", sl); q:SetAttribute("Off", 1)
		end
		if lampY then
			K.light(K.box(F, "Scenery", "SideLamp", cx - 0.5, cx + 0.5, lampY - 0.2, lampY, zc - 0.5, zc + 0.5, K.P.pier, nil, { ghost = true, tr = 1, parent = m }),
				16, 0.8, "fff4e6", { kind = "SpotLight", angle = 70 })
		end
	end
	-- (round 7) the plinth's front in the teams' colours under each team's lane, faintly lit, so the colour reaches the
	-- walkway's eye line; the mode across it and on both ends, pale
	for t = 1, n do
		local xa, xb = span[t][1], span[t][2]
		if t == 1 then xa = -6.2 end
		if t == n then xb = 6.2 end
		local _, ts = c3(K.TEAM[t]):ToHSV()
		if ts < 0.2 then -- (a pale team: its muted grey, so the pale label still reads on it)
			K.box(F, "Scenery", "KerbFace", xa, xb, 0.1, 1.5, 0.0, 0.06, K.TEAM_MUTED[t], nil, { parent = m, ghost = true, noshadow = true })
		else
			K.box(F, "Scenery", "KerbFace", xa, xb, 0.1, 1.5, 0.0, 0.06, K.glowHex(t), MAT.Neon, { parent = m, ghost = true, noshadow = true, tr = 0.55 })
		end
	end
	local label = md.title .. "  ·  " .. md.kind
	local kb = K.box(F, "Scenery", "KerbSign", -4.6, 4.6, 0.25, 1.35, 0.07, 0.1, "7d7a76", nil, { parent = m, ghost = true, tr = 1 })
	K.text(kb, Enum.NormalId.Back, { { label, "1f2633", 0.9 } }, { pps = 40, bright = 1.4 }) -- (dark on the teams' tinted front: pastels too)
	for _, sx in { -1, 1 } do
		local ke = K.box(F, "Scenery", "KerbSign", sx * 6.38, sx * 6.42, 0.15, 1.05, -12.4, -1.0, "7d7a76", nil, { parent = m, ghost = true, tr = 1 })
		K.text(ke, if sx > 0 then Enum.NormalId.Right else Enum.NormalId.Left, { { label, "ece6da", 0.9 } }, { pps = 40, bright = 1.4 })
	end
	-- the board (round 7, judge round 6): one chunky object with its pad: a deep slate frame on one wide stem rising
	-- from the plinth's back rim; o.turn turns it about the stem toward a hall's entrance (degrees, + toward local +X),
	-- o.rise lifts it (a hub steps later pads up so every board clears the one in front). The mode's name on it at about
	-- 60% of the counts (Status); Sub empty at rest (Matches writes it; a hub says "step on a side" once, at its entrance)
	local rise = o.rise or 0
	local BODY = "8f8b85"
	K.box(F, "Scenery", "Stem", -1.5, 1.5, 1.2, 8.6 + rise, -13.0, -11.6, BODY, nil, { parent = m, solid = true })
	local FB = F * CFrame.new(0, 11.5 + rise, -12.3) * CFrame.Angles(0, math.rad(o.turn or 0), 0)
	K.box(FB, "Scenery", "BoardFrame", -6.5, 6.5, -3.25, 3.25, -0.6, 0.6, BODY, nil, { parent = m, solid = true })
	K.box(FB, "Scenery", "BoardLip", -6.5, 6.5, 3.25, 3.55, -0.7, 0.7, "a19d96", nil, { parent = m })
	local counts = {}
	for t = 1, n do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(K.TEAM[t], md.size)) end
	local scr = K.box(FB, "Scenery", "Screen", -5.9, 5.9, -2.6, 2.6, 0.6, 0.7, "28324a", nil, { parent = m })
	-- (the counts' line is only as tall as one line of them can be wide, so the scaled text never breaks onto two lines)
	K.text(scr, Enum.NormalId.Back, { { md.title .. "  " .. md.kind, "f2f0ea", 0.26 }, { table.concat(counts, if n == 2 then ' <font color="#8a93a6">vs</font> ' else "  "), "ffffff", if n == 2 then 0.44 else 0.36 },
		{ "", "c8d0e0", 0.1, "S" } }, { names = { [2] = "Status", [3] = "Sub" }, pps = 40, bright = 2, bg = "28324a", bgt = 0 })
	K.light(scr, 14, 0.45, "dfe8ff")
	-- the head (round 5): the mode's word on the gantry's head; round 6: only on request (o.head), the board says it
	if o.head == true then
		K.box(F, "Scenery", "Head", -6.1, 6.1, 14.4, 16.0, -13.25, -11.35, "7d7a76", nil, { parent = m, solid = true })
		local hp = K.box(F, "Scenery", "HeadPlate", -5.7, 5.7, 14.55, 15.85, -11.4, -11.3, "28324a", nil, { parent = m })
		K.text(hp, Enum.NormalId.Back, { { md.kind, "f2f0ea", 0.8 } }, { pps = 40, bright = 2, bg = "28324a", bgt = 0 })
	end
	return m
end
-- (20 Nov, the TeamColors flip: main, "never a visible mismatch") recolour pads already built (any design) to the palette
-- in K.TEAM / K.TEAM_MUTED: colour only, no geometry. Each part or light in a pad Model whose colour is one of the old
-- teams' colours takes the new one (the Side plates the muted one); a part with a Team attribute and a team colour is
-- caught either way. old = { full = { hex... }, muted = { hex... } } (the colours the pads were built with). Returns a count
function K.recolorPads(padsFolder, old)
	local n = 0
	local function near(c, hex)
		local o = c3(hex)
		return math.abs(c.R - o.R) + math.abs(c.G - o.G) + math.abs(c.B - o.B) < 0.06
	end
	local function teamOf(c)
		for t, hx in old.full do if near(c, hx) then return t, false end end
		for t, hx in old.muted or {} do if near(c, hx) then return t, true end end
		return nil
	end
	for _, m in padsFolder:GetChildren() do
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") then
				local t, muted = teamOf(d.Color)
				if t and K.TEAM[t] then
					d.Color = c3(if muted or d.Name:match("^Side") then K.TEAM_MUTED[t] elseif d.Material == MAT.Neon then K.glowHex(t) else K.TEAM[t]); n += 1
				end
			elseif d:IsA("Light") then
				local t = teamOf(d.Color)
				if t and K.TEAM[t] then d.Color = c3(K.glowHex(t)); n += 1 end
			end
		end
	end
	return n
end
-- a pad's mode as a two-faced BLADE sign for a hub's piers (judge round 2: a sign per pad readable down the hall): F at
-- its middle, its faces along F's look and back (hang it square to the wall, so the faces look up and down the row)
function K.padBlade(F, md, w, h)
	w, h = w or 3.4, h or 4.6
	K.box(F, "Scenery", "BladeHousing", -w / 2 - 0.3, w / 2 + 0.3, -h / 2 - 0.3, h / 2 + 0.3, -0.35, 0.35, "c9c5bc")
	local p = K.box(F, "Scenery", "Blade", -w / 2, w / 2, -h / 2, h / 2, -0.45, 0.45, "28324a")
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
		K.text(p, face, { { md.title, "f2f0ea", 0.42 }, { md.kind, "c8d0e0", 0.16, "S" } }, { pps = 40, bright = 1.8, bg = "28324a", bgt = 0 }) -- (navy, lit: never a black slab)
	end
	K.light(p, 10, 0.3, "dfe8ff")
	return p
end
-- one piece of a Blender kit (a template in JankfireMeshes, its pivot the kit's origin) at cf in F; o.solid: it
-- collides and is queryable (walls, floors, furniture), else look only; o.folder (default "Scenery"); o.parent
function K.put(F, tmpl, cf, o)
	o = o or {}
	local lib = game:GetService("ServerStorage"):FindFirstChild("JankfireMeshes")
	local t = lib and lib:FindFirstChild(tmpl)
	if not t then S.missing = (S.missing or 0) + 1; return nil end
	local c = t:Clone()
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = o.solid == true; d.CanQuery = o.solid == true; d.CanTouch = o.solid == true
			if o.noshadow then d.CastShadow = false end
			d:SetAttribute("Hub", S.hub); S.count += 1
		end
	end
	c:PivotTo(S.site * F * (cf or CFrame.new()))
	c.Parent = o.parent or K.folder(o.folder or "Scenery")
	return c
end
-- bring a Blender kit (one Model asset holding many models: pieces "<model><n>__<kind>_<hex>") into
-- ServerStorage.JankfireMeshes as templates, painted from the names; each template's pivot is the kit's own origin (the
-- exporter turned the pieces, rbxglb.turn_for_roblox: they arrive in the file's frame, front +Z). Edit time only
local KIT_MAT = { plastic = SP, concrete = MAT.Concrete, neon = MAT.Neon, glass = MAT.Glass, fabric = SP, wood = MAT.Wood, slate = MAT.Slate }
function K.importKit(kit, id)
	local ok, container = pcall(function() return game:GetService("InsertService"):LoadAsset(id) end)
	if not ok or not container then return kit .. " LOAD FAILED " .. tostring(container) end
	local lib = game:GetService("ServerStorage"):FindFirstChild("JankfireMeshes")
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not KIT_MAT[kind] then bad += 1; continue end
		d.Material = KIT_MAT[kind]; d.Color = c3(h); d.TextureID = ""
		d.Transparency = if kind == "glass" then 0.35 else 0
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind ~= "neon" and kind ~= "glass"
		d:SetAttribute("Kind", kind)
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for nm, parts in groups do
		local m = Instance.new("Model"); m.Name = nm
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", id); m:SetAttribute("Kit", kit); m:SetAttribute("FileFrame", true)
		local old = lib:FindFirstChild(nm); if old then old:Destroy() end
		m.Parent = lib
		local _, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(nm, #parts, size.X, size.Y, size.Z))
	end
	container:Destroy()
	table.sort(names)
	return kit .. ": " .. #names .. " models" .. (if bad > 0 then ", " .. bad .. " unnamed pieces" else "") .. "; " .. table.concat(names, ", ")
end

-- ------------------------------------------------------------------------------------------------ kit models and guns
-- a model from the props kit (ServerStorage.JankfireMeshes): scaled, its bottom on F's floor at (x, z) + y, turned yaw,
-- recoloured (o.color = { oldHex = newHex } by the parts' _hex suffix; o.gold = all gold metal), no shadows if o.noShadow
function K.kit(F, tmpl, name, x, y, z, yaw, o)
	o = o or {}
	local lib = game:GetService("ServerStorage"):FindFirstChild("JankfireMeshes")
	local t = lib and lib:FindFirstChild(tmpl)
	if not (t and t:IsA("Model")) then S.missing = (S.missing or 0) + 1; return nil end
	local m = t:Clone(); m.Name = name
	if o.scale then m:ScaleTo(m:GetScale() * o.scale) end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
			if o.solid ~= true then d.CanCollide = false end
			if o.noShadow then d.CastShadow = false end
			local hex = d.Name:match("_(%x%x%x%x%x%x)$")
			if o.gold then d.Color = c3(if (d.Color.R + d.Color.G + d.Color.B) < 0.45 then "2a2620" else K.P.gold); d.Material = MAT.Metal; d.Reflectance = 0.1
			elseif o.color and hex and o.color[hex:lower()] then d.Color = c3(o.color[hex:lower()]) end
			d:SetAttribute("Hub", S.hub)
			S.count += 1
		elseif d:IsA("BaseScript") then d:Destroy() end
	end
	local cf, size = m:GetBoundingBox()
	local want = S.site * F * CFrame.new(x, (y or 0) + size.Y / 2, z) * CFrame.Angles(0, math.rad(yaw or 0), 0)
	m:PivotTo(want * cf:ToObjectSpace(m:GetPivot()) * CFrame.new()) -- (its box's middle where asked)
	local cf2 = m:GetBoundingBox()
	m:PivotTo(m:GetPivot() + (want.Position - cf2.Position))
	m.Parent = o.parent or K.folder("Scenery")
	return m
end
-- a weapon from ReplicatedStorage.JankfireWeapons (w_<id>) or an item (JankfireItems x_<id>) as a display piece: tags,
-- scripts, sounds, effects and lights gone, anchored, nothing collides or casts; scaled by k (or to len along its Z);
-- its middle at (x, y, z) in F, its length along F's x turned yaw
K.GUN_MAX = 2.5 -- (the most a displayed gun is scaled up from its own size: a card is not a rifle, a pistol still reads)
function K.gun(F, src, wname, len, x, y, z, yaw, name, k)
	local folder = game:GetService("ReplicatedStorage"):FindFirstChild(src)
	local t = folder and folder:FindFirstChild(wname)
	if not t then return nil end
	local m = t:Clone()
	m.Name = name or ("Rack_" .. wname)
	for _, tg in Tags:GetTags(m) do Tags:RemoveTag(m, tg) end
	for _, d in m:GetDescendants() do
		for _, tg in Tags:GetTags(d) do Tags:RemoveTag(d, tg) end
		if d:IsA("BaseScript") or d:IsA("Sound") or d:IsA("ParticleEmitter") or d:IsA("Light") or d:IsA("Beam") or d:IsA("Trail") or d:IsA("ProximityPrompt") then d:Destroy()
		elseif d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false; S.count += 1 end
	end
	if m:IsA("Model") then
		local _, size = m:GetBoundingBox()
		m:ScaleTo(m:GetScale() * (k or math.min(len / math.max(size.Z, 0.1), K.GUN_MAX)))
		local cf = m:GetBoundingBox()
		m.PrimaryPart = nil
		m.WorldPivot = cf
		m:PivotTo(S.site * F * CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(90 + (yaw or 0)), 0))
	end
	m.Parent = K.folder("Scenery")
	return m
end

-- ------------------------------------------------------------------------------------------------ holograms
-- a hologram drum (HubHolo draws it on each client): kind "loadout" (your loadout) or "bundle" (the shop's bundle
-- Slot, or the VIP pack's with Offer "vip"); its middle at (x, y, z) in F, r across, h high, Base = studs from its
-- middle down to the lens; prompt text -> a BundlePrompt (HubHolo fills it); o.folder puts it apart (ShowName lookups)
function K.holo(F, kind, x, y, z, r, h, o)
	o = o or {}
	local p = K.cyl(F, "Scenery", "Holo_" .. kind, x, y - h / 2, y + h / 2, z, 2 * r, K.P.holo, nil, { ghost = true, tr = 1, noshadow = true, parent = o.parent })
	Tags:AddTag(p, "HubHolo")
	p:SetAttribute("Holo", kind); p:SetAttribute("HoloEnvelope", true)
	p:SetAttribute("Radius", r); p:SetAttribute("Height", h); p:SetAttribute("Base", o.base or 0); p:SetAttribute("Color", K.P.holo)
	if o.slot then p:SetAttribute("Slot", o.slot) end
	if o.offer then p:SetAttribute("Offer", o.offer) end
	if o.prompt then
		local pr = Instance.new("ProximityPrompt")
		pr.Name = "BundlePrompt"; pr.ActionText = o.prompt; pr.ObjectText = "Bundle"
		pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
		pr.MaxActivationDistance = 10; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
		pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
		pr.Parent = p
	end
	return p
end
-- a round plinth with a lit lens (dia across, top at h)
local function plinth(F, x, z, dia, h, folder)
	K.cyl(F, "Shell", "PlinthFoot", x, 0, 0.35, z, dia + 0.6, K.P.pier, nil, { parent = folder })
	K.cyl(F, "Shell", "Plinth", x, 0.35, h, z, dia, K.P.cream, nil, { parent = folder })
	K.cyl(F, "Scenery", "PlinthTop", x, h - 0.1, h + 0.03, z, dia - 0.4, K.P.floor2, nil, { ghost = true, parent = folder })
	K.cyl(F, "Scenery", "PlinthRing", x, h - 0.14, h + 0.07, z, dia - 1.0, K.P.holo, MAT.Neon, { ghost = true, noshadow = true, parent = folder })
	K.cyl(F, "Scenery", "PlinthLens", x, h - 0.18, h + 0.11, z, 0.9, K.P.holo, MAT.Neon, { ghost = true, noshadow = true, parent = folder })
end
-- YOUR LOADOUT on a big plinth, its label over it
function K.holoLoadout(F)
	plinth(F, 0, 0, 5.6, 1.6)
	K.holo(F, "loadout", 0, 1.6 + 3.4, 0, 2.4, 6.4, { base = 3.4 })
	K.light(K.box(F, "Scenery", "LampSpot", -0.5, 0.5, 9.6, 9.8, -0.5, 0.5, K.P.pier, nil, { ghost = true, tr = 1 }), 12, 0.5, K.P.holo)
end
-- the shop's bundles on plinths in an arc round F (its look toward the room), each with its name plate (ShowName<Slot>
-- beside it in the same folder: HubHolo writes the bundle's name on it)
function K.bundles(F, slots)
	slots = slots or { 1, 2, 3 }
	for i, slot in slots do
		local k = i - (#slots + 1) / 2 -- (a shallow arc, its wings forward, each turned in a little)
		local Fp = F * CFrame.new(k * 5.2, 0, -math.abs(k) * 1.6) * CFrame.Angles(0, math.rad(-k * 16), 0)
		plinth(Fp, 0, 0, 3.8, 1.4)
		K.holo(Fp, "bundle", 0, 1.4 + 2.2, 0, 1.8, 3.6, { base = 2.2, slot = slot, prompt = "View bundle" })
		local plate = K.box(Fp, "Scenery", "ShowName" .. slot, -1.6, 1.6, 0.5, 1.3, -2.5, -2.35, K.P.screen, nil, { solid = false })
		K.text(plate, Enum.NormalId.Front, { { "BUNDLE", K.P.holo, 0.38, "S" }, { "COMING SOON", K.P.pale, 0.5 } }, { guiName = "Gui", flat = true, pps = 60 })
		K.box(Fp, "Scenery", "ShowNameStand", -0.2, 0.2, 0, 0.5, -2.45, -2.25, K.P.steel)
	end
end

-- ------------------------------------------------------------------------------------------------ jump pads
-- a jump pad (Move.client reads Pad: the world launch velocity) at F, vel = (right, up, forward along F's look)
function K.jumpPad(F, vel)
	local m = Instance.new("Model"); m.Name = "JumpPad"; m.Parent = K.folder("Scenery")
	K.cyl(F, "Scenery", "PadBase", 0, 0, 0.45, 0, 5.2, K.P.steel, nil, { parent = m })
	K.cyl(F, "Scenery", "PadTop", 0, 0.45, 0.55, 0, 4.2, K.P.pier2, nil, { parent = m })
	local g = K.cyl(F, "Scenery", "PadGlow", 0, 0.5, 0.6, 0, 3.4, K.P.holo, MAT.Neon, { parent = m, noshadow = true })
	Tags:AddTag(g, "HubBreathe"); g:SetAttribute("BreatheLo", 0.1); g:SetAttribute("BreatheHi", 0.5); g:SetAttribute("BreathePeriod", 2.6)
	K.light(g, 8, 0.8, K.P.holo)
	local top = K.box(F, "Scenery", "JumpPadTop", -2.7, 2.7, 0, 0.6, -2.7, 2.7, K.P.pier, nil, { parent = m, tr = 1, solid = true })
	local w = S.site * F
	top:SetAttribute("Pad", w.RightVector * vel.X + w.UpVector * vel.Y + w.LookVector * vel.Z)
	-- a ring on the floor round it
	K.cyl(F, "Scenery", "JumpRing", 0, -0.02, 0.08, 0, 8, K.P.holo, MAT.Neon, { ghost = true, tr = 0.6, noshadow = true })
	return m
end

-- ------------------------------------------------------------------------------------------------ the shop counter
-- a counter facing F's look (the customers' side), shelves of goods behind, a lit sign SHOP; a Shop prompt on the
-- counter (ShopClient opens the shop: "tab:featured")
function K.shop(F, len)
	K.box(F, "Shell", "Counter", -len / 2, len / 2, 0, 3.4, -1.0, 1.0, K.P.wood, MAT.Wood)
	K.box(F, "Scenery", "CounterTop", -len / 2 - 0.2, len / 2 + 0.2, 3.4, 3.7, -1.25, 1.1, K.P.creamHi)
	K.box(F, "Scenery", "CounterLine", -len / 2 + 0.3, len / 2 - 0.3, 3.1, 3.2, -1.06, -1.0, K.P.amber, MAT.Neon, { ghost = true })
	K.box(F, "Shell", "ShopShelves", -len / 2, len / 2, 0, 9, 3.8, 4.8, K.P.wall2)
	for _, y in { 2.4, 4.6, 6.8 } do
		K.box(F, "Scenery", "Shelf", -len / 2 + 0.3, len / 2 - 0.3, y, y + 0.2, 3.0, 3.8, K.P.cream)
		local n = math.floor((len - 0.8) / 1.6)
		for i = 0, n - 1 do
			K.box(F, "Scenery", "Goods", -len / 2 + 0.6 + i * 1.6, -len / 2 + 1.7 + i * 1.6, y + 0.2, y + 1.1 + (i % 3) * 0.35, 3.2, 3.7, ({ "8a6d5a", "5a6e7a", "7a7a6a", "6a5a6a", "9a8064" })[i % 5 + 1])
		end
	end
	K.sign(F, "Scenery", "ShopSign", len - 4, 1.8, 0, 10.4, 3.6, { { "SHOP", K.P.amber, 0.8 } }, { pps = 40 })
	K.light(K.box(F, "Scenery", "ShopLight", -len / 2 + 0.5, len / 2 - 0.5, 8.7, 8.9, 2.8, 3.2, K.P.warm, MAT.Neon, { ghost = true }), 16, 0.6, K.P.warm)
	local pp = K.box(F, "Scenery", "ShopPromptPart", -0.5, 0.5, 3.8, 4.4, -0.3, 0.3, K.P.pier, nil, { ghost = true, tr = 1 })
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ShopCounterPrompt"; pr.ActionText = "Shop"; pr.ObjectText = "Counter"; pr.HoldDuration = 0; pr.MaxActivationDistance = 9
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.RequiresLineOfSight = false
	pr:SetAttribute("ShopOpen", "tab:featured")
	pr.Parent = pp
end

-- ------------------------------------------------------------------------------------------------ the regulars
local MX = {
	rise = "rbxassetid://117955942892612", settle = "rbxassetid://97331327036036", trisIdle = "rbxassetid://122668447841808", look = "rbxassetid://114005193645149",
	lootIdle = "rbxassetid://81991323034085", stretch = "rbxassetid://75542542460583", duneIdle = "rbxassetid://90791386511358", shift = "rbxassetid://86800381172094",
	friskIdle = "rbxassetid://132599545925485",
}
local GEN_WALK = "rbxassetid://135619112265836"
K.NPCS = { -- (the ring's R.NPCS, the same regulars in every hub)
	Looticus = { user = "roblox_user_4547551380", id = 4547551380, pose = "sit", role = "SHOP", prompt = { "Shop", "ShopOpen", "tab:containers" }, moves = "teleport", idle = MX.lootIdle, extra = MX.look, extraLen = 4, extraStand = MX.stretch, extraStandLen = 8.9, every = { 15, 30 }, rise = MX.rise, riseLen = 2.27, settle = MX.settle, settleLen = 2.23 },
	Dune = { user = "Doonamei", id = 56917496, pose = "stand", role = "QUESTS", prompt = { "Quests", "QuestsOpen", true }, badge = "QuestNews", moves = "pingpong", idle = MX.duneIdle, extra = MX.shift, extraLen = 9.4, every = { 20, 40 }, walk = GEN_WALK },
	Frisk1636 = { user = "BruhFrisk1636", id = 5028123368, pose = "stand", role = "RANKED", prompt = { "Ranked", "RankedBoard", "duels" }, moves = "pingpong", idle = MX.friskIdle, walk = GEN_WALK },
	ZombieGuide = { pose = "stand", role = "ZOMBIES", prompt = { "Play", "ZombiesQueue", true }, objectText = "Zombies", idle = MX.friskIdle, noLabel = true },
	Trisangle = { user = "Xxxglowingstarlightx", id = 2321239144, pose = "sit", vipDaily = true, role = "DAILY REWARD", moves = "seats", moveEvery = { 45, 90 }, idle = MX.trisIdle, extra = MX.look, extraLen = 4, every = { 12, 25 }, walk = GEN_WALK, rise = MX.rise, riseLen = 2.27, settle = MX.settle, settleLen = 2.23 },
}
-- a regular's place (HubNPCs builds them there): a Seat (seated) or a Part, at (x, y, z) in F turned yaw; y = the
-- cushion's top for a seat, the floor for a standing one. o.door: the Vector3 (site frame) that joins two aisles
function K.npc(F, who, x, y, z, yaw, o)
	o = o or {}
	local info = K.NPCS[who]
	if not info then return nil end
	local p = Instance.new(if info.pose == "sit" then "Seat" else "Part")
	p.Name = "Regular_" .. who .. "_Place"; p.Size = Vector3.new(2, 0.2, 2)
	p.CFrame = S.site * F * CFrame.new(x, y + 0.1, z) * CFrame.Angles(0, math.rad(yaw or 0), 0)
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1; p.CastShadow = false
	if p:IsA("Seat") then (p :: Seat).Disabled = true end
	p:SetAttribute("Who", who); p:SetAttribute("User", info.user); p:SetAttribute("UserId", info.id); p:SetAttribute("Pose", info.pose)
	p:SetAttribute("Hub", S.hub)
	if info.vipDaily then p:SetAttribute("VipDaily", true) end
	if info.role then p:SetAttribute("Role", info.role) end
	if info.badge then p:SetAttribute("Badge", info.badge) end
	if info.prompt then
		local at = Instance.new("Attachment"); at.Name = "PromptAt"; at.Position = Vector3.new(0, if info.pose == "sit" then 1.4 else 3.2, 0); at.Parent = p
		local pr = Instance.new("ProximityPrompt")
		pr.Name = info.prompt[1] .. "Prompt"; pr.ActionText = info.prompt[1]; pr.ObjectText = info.objectText or who
		pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
		pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
		pr:SetAttribute(info.prompt[2], info.prompt[3])
		pr.Parent = at
	end
	if info.idle then p:SetAttribute("Idle", info.idle) end
	if info.walk then p:SetAttribute("Walk", info.walk) end
	if info.moves then p:SetAttribute("Moves", info.moves) end
	if info.moveEvery then p:SetAttribute("MoveEvery", Vector2.new(info.moveEvery[1], info.moveEvery[2])) end
	if info.extra then p:SetAttribute("Extra", info.extra); p:SetAttribute("ExtraLen", info.extraLen or 4) end
	if info.extraStand then p:SetAttribute("ExtraStand", info.extraStand); p:SetAttribute("ExtraStandLen", info.extraStandLen or 4) end
	if info.every then p:SetAttribute("ExtraEvery", Vector2.new(info.every[1], info.every[2])) end
	if info.rise then
		p:SetAttribute("Rise", info.rise); p:SetAttribute("RiseLen", info.riseLen or 2)
		p:SetAttribute("Settle", info.settle); p:SetAttribute("SettleLen", info.settleLen or 2.5)
	end
	if o.door then p:SetAttribute("Door", (S.site * F * CFrame.new(o.door)).Position) end -- (in F: the VIP room's, not the hub's middle)
	if info.noLabel then p:SetAttribute("NoLabel", true) end
	p.Parent = K.folder("Scenery")
	Tags:AddTag(p, "HubNPC")
	if who == "ZombieGuide" then Tags:AddTag(p, "ZombieGuide") end
	if info.pose == "sit" then Tags:AddTag(p, "HubSeat") end -- (players sit there too while the regular is away: HubSeats; NpcHere while they're on it)
	return p
end
-- one of a regular's points (HubNPCs walks or puffs them between): kind seat / spot / stop / via, pose sit / stand,
-- at (x, y, z) in F turned yaw; o.pause {a, b}; o.approach / o.aisle / o.stand: Vector3s in F's space (on the floor);
-- a sit point is a seat players can use too (HubSeat)
function K.npcPoint(F, who, index, kind, pose, x, y, z, yaw, o)
	o = o or {}
	local p = K.part("Scenery", ("NPCPoint_%s_%d"):format(who, index), F * CFrame.new(x, y + 0.1, z) * CFrame.Angles(0, math.rad(yaw or 0), 0),
		Vector3.new(2, 0.2, 2), K.P.pier, nil, { ghost = true, tr = 1, noshadow = true })
	p:SetAttribute("Who", who); p:SetAttribute("Index", index); p:SetAttribute("Kind", kind); p:SetAttribute("Pose", pose)
	if o.pause then p:SetAttribute("Pause", Vector2.new(o.pause[1], o.pause[2])) end
	local W = S.site * F
	if o.approach then p:SetAttribute("Approach", (W * CFrame.new(o.approach)).Position) end
	if o.aisle then p:SetAttribute("Aisle", (W * CFrame.new(o.aisle)).Position) end
	if pose == "sit" then
		p:SetAttribute("Stand", if o.stand then (W * CFrame.new(o.stand)).Position else p.CFrame * Vector3.new(0, 0, -1.9))
		Tags:AddTag(p, "HubSeat")
	end
	Tags:AddTag(p, "NPCPoint")
	return p
end

-- a glass showcase on a plinth with a weapon turning in it (HubSpin), facing F's look; a light in its top
function K.showcase(F, wid, name)
	K.box(F, "Shell", "ShowBase", -1.6, 1.6, 0, 2.4, -1.6, 1.6, K.P.dark)
	K.box(F, "Scenery", "ShowBand", -1.65, 1.65, 2.2, 2.43, -1.65, 1.65, K.P.gold, MAT.Metal)
	K.box(F, "Scenery", "ShowGlass", -1.5, 1.5, 2.4, 6.6, -1.5, 1.5, K.P.glass, MAT.Glass, { tr = 0.7, solid = true })
	K.box(F, "Scenery", "ShowTop", -1.6, 1.6, 6.6, 7.0, -1.6, 1.6, K.P.dark)
	K.light(K.box(F, "Scenery", "ShowLight", -0.9, 0.9, 6.45, 6.6, -0.9, 0.9, K.P.warm, MAT.Neon, { ghost = true }), 8, 0.7)
	local g = K.gun(F, "JankfireWeapons", "w_" .. wid, 2.6, 0, 4.4, 0, 0, name or ("Show_w_" .. wid), nil)
	if g then g:SetAttribute("Spin", 0.4); g:SetAttribute("SpinNear", 70); Tags:AddTag(g, "HubSpin") end
	return g
end

-- ------------------------------------------------------------------------------------------------ the zombies entrance
-- (20 Nov 2026; the owner: "To all the lobbies can you add like a door that's open with a busted room with a npc just
-- dummy for now ... or like a makeshift garage ... to represent the zombie mode"; main: make it the way in, Jankfield
-- High's look, quiet colours, no gore). A wrecked room behind an open doorway in a hub wall. F = the doorway's middle on
-- the hub side of the wall, on the floor, its look into the room; the wall is o.t thick and the hub builder cuts its hole
-- (o.door wide, 8.5 high). The room is x o.x0..o.x1 across, o.d deep past the wall, o.h high. Inside: boarded windows, a
-- dying bulb (HubFlicker), tipped desks and a chair, a workbench with tools, plywood sheets and planks, a boarded door,
-- a hazard-taped square with the queue prompt (ZombiesSpot, ZombiesQueue: play-party starts the zombies search). Outside:
-- a ZOMBIES board over the door, the guide (a regular, Who ZombieGuide) beside it (o.guideSide 1 / -1)
local function zmPart(F, name, cf, size, hex, mat, o)
	return K.part("Scenery", name, F * cf, size, hex, mat, o)
end
local function zmDesk(F, x, z, yaw, tipped)
	local Fd = F * CFrame.new(x, 0, z) * CFrame.Angles(0, math.rad(yaw), 0)
	if tipped then Fd = Fd * CFrame.new(0, 1.2, 0) * CFrame.Angles(math.rad(90), 0, 0) * CFrame.new(0, -1.2, 0) end
	K.box(Fd, "Scenery", "ZmDeskTop", -1.6, 1.6, 2.4, 2.6, -1.1, 1.1, "8a7a62", MAT.Wood, { solid = true })
	for _, sx in { -1, 1 } do for _, sz in { -1, 1 } do K.box(Fd, "Scenery", "ZmDeskLeg", sx * 1.4 - 0.08, sx * 1.4 + 0.08, 0, 2.4, sz * 0.9 - 0.08, sz * 0.9 + 0.08, K.P.steel) end end
	K.box(Fd, "Scenery", "ZmDeskShelf", -1.4, 1.4, 1.7, 1.8, -0.9, 0.9, "6f7b80")
end
function K.zombieRoom(F, o)
	local P = K.P
	local t, d, h = o.t or 2, o.d or 18, o.h or 11
	local x0, x1 = o.x0, o.x1
	local zb = -t - d -- (the back wall's inner face)
	local zm = -t - d / 2
	-- the shell: a bare concrete box
	K.box(F, "Shell", "ZmFloor", x0 - 2, x1 + 2, -1, 0, zb - 2, -t, "57554f", MAT.Concrete)
	K.box(F, "Shell", "ZmLid", x0 - 2, x1 + 2, h, h + 1, zb - 2, -t, P.dome)
	K.box(F, "Shell", "ZmWall", x0 - 2, x0, 0, h, zb, -t, P.conc, MAT.Concrete)
	K.box(F, "Shell", "ZmWall", x1, x1 + 2, 0, h, zb, -t, P.conc, MAT.Concrete)
	K.box(F, "Shell", "ZmWall", x0 - 2, x1 + 2, 0, h, zb - 2, zb, P.conc, MAT.Concrete)
	for _, x in { x0 + 0.06, x1 - 0.06 } do K.box(F, "Scenery", "ZmStain", x - 0.05, x + 0.05, 0, 2.2, zb + 0.5, -t - 0.5, "4f4d48", MAT.Concrete) end
	-- boarded windows on the back wall (a dark pane, a frame, planks nailed across at angles)
	local W = { (x0 + x1) / 2 - (x1 - x0) * 0.22, (x0 + x1) / 2 + (x1 - x0) * 0.22 }
	for i, wx in W do
		K.box(F, "Scenery", "ZmPane", wx - 2.4, wx + 2.4, 3.6, 8, zb, zb + 0.08, "1c1e22", nil, { noshadow = true })
		for _, e in { { -2.6, -2.4 }, { 2.4, 2.6 } } do K.box(F, "Scenery", "ZmFrame", wx + e[1], wx + e[2], 3.4, 8.2, zb, zb + 0.3, P.plank, MAT.Wood) end
		for _, y in { 3.4, 8 } do K.box(F, "Scenery", "ZmFrame", wx - 2.6, wx + 2.6, y, y + 0.2, zb, zb + 0.3, P.plank, MAT.Wood) end
		for k, a in { -9, 7, -4 } do
			zmPart(F, "ZmBoard", CFrame.new(wx, 4.3 + k * 1.15, zb + 0.38 + k * 0.05) * CFrame.Angles(0, 0, math.rad(a + i * 3)), Vector3.new(6.2, 0.75, 0.16), if k == 2 then P.ply else P.plank, MAT.Wood)
		end
	end
	-- a boarded door in the side wall (x1), and the open doorway's broken leaf, swung in against the x0 side
	local bz = zb + 4.5
	K.box(F, "Scenery", "ZmDoorFrame", x1 - 0.3, x1, 0, 7.8, bz - 2.1, bz + 2.1, P.plank, MAT.Wood)
	K.box(F, "Scenery", "ZmDoorPanel", x1 - 0.35, x1 - 0.3, 0, 7.5, bz - 1.8, bz + 1.8, "4a4844")
	for k, a in { -14, 10, -6 } do zmPart(F, "ZmBoard", CFrame.new(x1 - 0.46 - k * 0.05, 1.8 + k * 1.7, bz) * CFrame.Angles(math.rad(a), 0, 0), Vector3.new(0.16, 0.75, 4.6), P.plank, MAT.Wood) end
	local dw = o.door or 5
	zmPart(F, "ZmLeaf", CFrame.new(-dw / 2 - 2.6, 3.85, -t - 0.5) * CFrame.Angles(0, math.rad(-8), math.rad(4)), Vector3.new(4.4, 7.6, 0.25), P.ply, MAT.Wood, { solid = true }) -- (off its hinges, leant against the wall beside the doorway)
	zmPart(F, "ZmLeafPlank", CFrame.new(-dw / 2 - 2.6, 4.2, -t - 0.7) * CFrame.Angles(0, math.rad(-8), math.rad(32)), Vector3.new(4.6, 0.6, 0.12), P.plank, MAT.Wood)
	-- the workbench along the x0 wall, its tools; plywood sheets against the back wall; planks on the floor
	local Fb = F * CFrame.new(x0 + 1.3, 0, zm + 1) * CFrame.Angles(0, math.rad(-90), 0)
	K.box(Fb, "Shell", "ZmBench", -3.2, 3.2, 3.0, 3.3, -1.2, 1.2, P.plank, MAT.Wood)
	for _, sx in { -1, 1 } do for _, sz in { -1, 1 } do K.box(Fb, "Scenery", "ZmBenchLeg", sx * 3 - 0.15, sx * 3 + 0.15, 0, 3.0, sz * 1 - 0.15, sz * 1 + 0.15, P.plank, MAT.Wood) end end
	K.box(Fb, "Scenery", "ZmBenchShelf", -3, 3, 0.8, 1.0, -1.0, 1.0, P.plank, MAT.Wood)
	K.box(Fb, "Scenery", "ZmToolbox", -2.4, -0.8, 3.3, 4.1, -0.6, 0.2, "7a4a40", MAT.Metal)
	K.box(Fb, "Scenery", "ZmToolboxLid", -2.45, -0.75, 4.1, 4.2, -0.65, 0.25, "6a3e36", MAT.Metal)
	K.box(Fb, "Scenery", "ZmHammer", 0.2, 1.8, 3.35, 3.5, 0.2, 0.36, "6b5646", MAT.Wood)
	K.box(Fb, "Scenery", "ZmHammerHead", 1.6, 1.9, 3.3, 3.6, 0.0, 0.56, K.P.steel, MAT.Metal)
	K.box(Fb, "Scenery", "ZmWrench", 2.2, 3.0, 3.3, 3.38, -0.7, -0.5, "9aa0a6", MAT.Metal)
	K.box(Fb, "Scenery", "ZmVise", 2.4, 3.1, 3.3, 4.0, 0.6, 1.1, "4d535c", MAT.Metal)
	local lamp = K.box(Fb, "Scenery", "ZmWorkLamp", -0.3, 0.3, 3.3, 4.6, -1.0, -0.4, "c9a45a", MAT.Metal)
	K.light(lamp, 11, 0.45, "ffd9a0")
	for k = 0, 2 do
		zmPart(F, "ZmPlywood", CFrame.new((x0 + x1) / 2 + (k - 1) * 0.5 + (x1 - x0) * 0.05, 3.6, zb + 0.9 + k * 0.25) * CFrame.Angles(math.rad(-11 - k * 2), math.rad(k * 3), 0), Vector3.new(4.2, 7.2, 0.18), if k == 1 then P.plank else P.ply, MAT.Wood)
	end
	for k, pl in { { 0.25, 0.6, 30 }, { -0.15, 0.45, -50 }, { 0.1, 0.3, 75 }, { -0.3, 0.75, 12 } } do
		zmPart(F, "ZmPlank", CFrame.new(x0 + (x1 - x0) * (0.5 + pl[1]), 0.08 + k * 0.01, -t - d * pl[2]) * CFrame.Angles(0, math.rad(pl[3]), 0), Vector3.new(5, 0.16, 0.7), P.plank, MAT.Wood)
	end
	-- school desks: two standing askew, two on their sides; a chair down
	zmDesk(F, x0 + (x1 - x0) * 0.72, zm + 1.5, 18, false)
	zmDesk(F, x0 + (x1 - x0) * 0.82, zb + 3.2, -25, true)
	zmDesk(F, x0 + (x1 - x0) * 0.36, -t - 3.2, 70, true)
	local Fc = F * CFrame.new(x0 + (x1 - x0) * 0.6, 0.9, -t - 4.2) * CFrame.Angles(0, math.rad(40), math.rad(90))
	K.box(Fc, "Scenery", "ZmChairSeat", -0.9, 0.9, -0.1, 0.1, -0.9, 0.9, "6f7b80")
	K.box(Fc, "Scenery", "ZmChairBack", -0.9, 0.9, 0.1, 1.8, 0.75, 0.9, "6f7b80")
	-- the queue spot: a hazard-taped square on the floor, the prompt in its middle; the mode's name on the back wall
	local sx, sz = (x0 + x1) / 2 + (o.spotX or 0), zm - 1
	for i = -3, 2 do
		for _, e in { { -3, 1 }, { 3, 1 } } do
			K.box(F, "Scenery", "ZmTape", sx + e[1] - 0.15, sx + e[1] + 0.15, 0.02, 0.05, sz + i + 0.02, sz + i + 0.98, if i % 2 == 0 then P.amber else P.steel2)
			K.box(F, "Scenery", "ZmTape", sx + i + 0.02, sx + i + 0.98, 0.02, 0.05, sz + e[1] - 0.15, sz + e[1] + 0.15, if i % 2 == 0 then P.amber else P.steel2)
		end
	end
	local spot = K.marker(F, "Scenery", "ZombiesSpot", sx, 0, sz, 0, nil, { "ZombiesSpot" }, { size = Vector3.new(1, 0.2, 1) })
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ZombiesPrompt"; pr.ActionText = "Play"; pr.ObjectText = "Zombies"; pr.HoldDuration = 0; pr.MaxActivationDistance = 9
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.RequiresLineOfSight = false
	pr:SetAttribute("ZombiesQueue", true)
	pr.Parent = spot
	local bsg = K.box(F * CFrame.new(sx, 0, zb + 0.02) * CFrame.Angles(0, math.pi, 0), "Scenery", "ZmBackSign", -3.4, 3.4, 8.7, 10.3, -0.2, 0, P.screen)
	K.text(bsg, Enum.NormalId.Front, { { "ZOMBIES", P.amber, 0.8 } }, { pps = 46 })
	-- the dying bulb over the spot (HubFlicker), its cord; a second dim light by the door
	K.cyl(F, "Scenery", "ZmCord", sx, h - 2.4, h, sz + 1.5, 0.1, K.P.steel2)
	local bulb = K.ball(F, "Scenery", "ZmBulb", sx, h - 2.6, sz + 1.5, 0.7, "ffe2b0", MAT.Neon, { ghost = true, noshadow = true })
	K.light(bulb, 22, 1.1, "ffd9a0", { shadows = true })
	Tags:AddTag(bulb, "HubFlicker")
	K.light(K.box(F, "Scenery", "ZmFill", -0.5, 0.5, h - 0.4, h - 0.2, -t - 2.5, -t - 1.5, P.pier, nil, { ghost = true, tr = 1 }), 12, 0.35, "c8d0d8")
	-- outside: the ZOMBIES board over the door, hung a little askew; the guide by the door, facing the hub
	local Fs = F * CFrame.new(0, 0, 0.32) * CFrame.Angles(0, math.pi, math.rad(-2.5))
	K.sign(Fs, "Scenery", "ZmSign", 7.4, 1.9, 0, 9.7, 0, { { "ZOMBIES", K.P.dark, 0.78 } }, { plate = P.ply, pps = 46 })
	for _, x in { -3.2, 3.2 } do K.box(F, "Scenery", "ZmSignNail", x - 0.08, x + 0.08, 9.6, 9.76, 0.32, 0.4, K.P.steel) end
	local gs = o.guideSide or 1
	K.npc(F, "ZombieGuide", gs * (dw / 2 + 2.2), 0, 2.2, 180)
	return spot
end

-- ------------------------------------------------------------------------------------------------ the VIP room
-- the VIP room behind a front wall: F at the wall's outer face (the street side) on the floor, its look INTO the room.
-- the wall 2 thick with a 6-wide door and glass either side; sliding door leaves (VipDoor, each door in its own folder:
-- HubVip groups leaves by parent); the Get VIP prompt outside; the room (VipRoom: non-VIPs are put Out); the gold duck,
-- two sofas (Trisangle's four seats), the VIP pack's two plinths (Offer "vip") in their own folder; o = { w, d, h }
function K.vip(F, o)
	local w, d, h = o.w, o.d, o.h
	local P = K.P
	-- the front wall with its door and windows
	local front = o.front or (w + 2) -- (the wall closes the whole street's end; the room behind it is narrower)
	K.wall(F, "VipWall", -front, front, 0, o.frontH or h, -2, 0, P.wall, { { -14, -6.5, 9 }, { -3, 3, 10 }, { 6.5, 14, 9 } }) -- (frontH: up to the street's roof)
	for _, s in { -1, 1 } do
		K.box(F, "Shell", "VipWall", s * 6.5, s * 14, 0, 2, -2, 0, P.wall) -- (under the window)
		K.box(F, "Scenery", "VipGlass", s * 6.5, s * 14, 2, 9, -1.15, -0.85, P.glass, MAT.Glass, { tr = 0.55, solid = true })
		K.box(F, "Scenery", "VipDoorPost", s * 3, s * 3.7, 0, 11, 0, 0.5, P.gold, MAT.Metal)
	end
	K.box(F, "Scenery", "VipDoorHead", -3.7, 3.7, 10, 11, 0, 0.5, P.gold, MAT.Metal)
	K.sign(F * CFrame.new(0, 0, 0.7) * CFrame.Angles(0, math.pi, 0), "Scenery", "VipSign", 7, 1.8, 0, 12.2, 0, { { "VIP", P.gold, 0.8 } }, { pps = 46 }) -- (facing the street)
	-- the door's leaves, sliding apart
	local leaves = Instance.new("Folder"); leaves.Name = "VipDoorLeaves"; leaves.Parent = K.folder("Scenery")
	for _, s in { -1, 1 } do
		local m = Instance.new("Model"); m.Name = "VipLeaf"; m.Parent = leaves
		K.box(F, "Scenery", "Leaf", if s < 0 then -3 else 0, if s < 0 then 0 else 3, 0, 10, -1.2, -0.8, P.plum, nil, { parent = m, solid = true })
		K.box(F, "Scenery", "LeafLine", if s < 0 then -0.25 else 0, if s < 0 then 0 else 0.25, 0.4, 9.6, -1.25, -0.75, P.gold, MAT.Metal, { parent = m, ghost = true })
		m:SetAttribute("Slide", (S.site * F).RightVector * (s * 3))
		Tags:AddTag(m, "VipDoor")
	end
	local pp = K.box(F, "Scenery", "VipPromptPart", -1, 1, 3.6, 5.6, 0.6, 1.0, P.pier, nil, { ghost = true, tr = 1 })
	Tags:AddTag(pp, "VipPrompt")
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "VipPrompt"; pr.ActionText = "Get VIP"; pr.ObjectText = "VIP ROOM"; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.HoldDuration = 0
	pr.MaxActivationDistance = 9; pr.RequiresLineOfSight = false; pr:SetAttribute("ShopOpen", "vip"); pr.Parent = pp
	-- the room
	K.box(F, "Shell", "VipFloor", -w - 2, w + 2, -1, 0, -d - 4, -2, P.plum, MAT.Fabric)
	K.box(F, "Shell", "VipLid", -w - 2, w + 2, h, h + 1, -d - 4, -2, P.dome)
	K.box(F, "Shell", "VipWall", -w - 2, -w, 0, h, -d - 4, -2, P.wall2)
	K.box(F, "Shell", "VipWall", w, w + 2, 0, h, -d - 4, -2, P.wall2)
	K.box(F, "Shell", "VipWall", -w, w, 0, h, -d - 4, -d - 2, P.wall2)
	for _, s in { -1, 1 } do K.box(F, "Scenery", "VipWainscot", s * (w - 0.3), s * w, 0, 4, -d - 2, -2, P.brown, MAT.Wood) end
	K.box(F, "Scenery", "VipCove", -w + 0.5, w - 0.5, h - 0.6, h - 0.4, -d - 1.8, -2.2, "ffd9a0", MAT.Neon, { ghost = true })
	local room = K.box(F, "Scenery", "VipRoomBox", -w, w, 0, h, -d - 2, -2, P.pier, nil, { ghost = true, tr = 1 })
	Tags:AddTag(room, "VipRoom")
	local W = S.site * F
	room:SetAttribute("Out", (W * CFrame.new(0, 3, 4)).Position)
	room:SetAttribute("OutLook", -W.LookVector)
	-- the gold duck on a plinth at the far end, a ring of light over it
	local DD = -d - 2 + 4.5
	K.cyl(F, "Shell", "DuckPlinth", 0, 0, 2.4, DD, 4.6, P.dark)
	K.cyl(F, "Scenery", "DuckPlinthBand", 0, 2.2, 2.44, DD, 4.72, P.gold, MAT.Metal)
	local duck = K.kit(F, "pj_duck", "VipDuck", 0, 2.44, DD, 0, { scale = 5, gold = true })
	K.light(K.box(F, "Scenery", "DuckSpot", -0.5, 0.5, h - 0.8, h - 0.6, DD - 0.5, DD + 0.5, P.pier, nil, { ghost = true, tr = 1 }), 13, 1.2, "ffe2b0", { kind = "SpotLight", angle = 45 })
	-- the VIP pack's plinths either side of the door, inside (their own folder: not mixed with the hub's bundle plates)
	local vf = Instance.new("Folder"); vf.Name = "VipPlinths"; vf.Parent = K.folder("Scenery")
	for k, s in { -1, 1 } do
		plinth(F, s * 7, -5.5, 3, 1.4, vf)
		K.holo(F, "bundle", s * 7, 1.4 + 1.6, -5.5, 1.6, 2.4, { base = 1.6, slot = k, offer = "vip", prompt = "View", parent = vf })
	end
	-- two plum sofas facing each other across a rug and a low table; Trisangle on them
	local mid = -2 - d / 2 - 1
	K.cyl(F, "Scenery", "VipRug", 0, 0, 0.06, mid, 12, "4b4048", MAT.Fabric)
	K.box(F, "Shell", "VipTable", -1.6, 1.6, 0, 1.2, mid - 1.4, mid + 1.4, P.woodDark, MAT.Wood)
	for _, s in { -1, 1 } do
		local Fs = F * CFrame.new(s * (w - 2.2), 0, mid) * CFrame.Angles(0, math.rad(s * 90), 0) -- (its back to the side wall, facing in)
		K.box(Fs, "Shell", "VipSofa", -3.6, 3.6, 0, 1.45, -1.0, 1.2, P.plum, MAT.Fabric)
		K.box(Fs, "Scenery", "VipSofaBack", -3.6, 3.6, 1.45, 3.4, 1.2, 1.9, P.plum, MAT.Fabric)
		for _, a in { -1, 1 } do K.box(Fs, "Scenery", "VipSofaArm", a * 3.6, a * 4.3, 0, 2.3, -1.0, 1.9, P.plum, MAT.Fabric) end
	end
	K.light(K.box(F, "Scenery", "LampSpot", -0.5, 0.5, h - 1.2, h - 1, mid - 0.5, mid + 0.5, P.pier, nil, { ghost = true, tr = 1 }), 16, 0.6, "ffd9a0")
	-- Trisangle: her place on the left sofa's door end, her four seats (both ends of both sofas), the way between them
	local sx = w - 2.2
	local function seatAt(s, dz) return Vector3.new(s * (sx + 0.1), 0, mid + dz) end
	K.npc(F, "Trisangle", seatAt(-1, 1.6).X, 1.45, seatAt(-1, 1.6).Z, -90, { door = Vector3.new(0, 0, -4.5) })
	local k = 0
	for _, s in { -1, 1 } do
		for _, dz in { 1.6, -1.6 } do
			k += 1
			local p = seatAt(s, dz)
			K.npcPoint(F, "Trisangle", k, "seat", "sit", p.X, 1.45, p.Z, s * 90,
				{ approach = Vector3.new(s * (sx - 1.9 - 1.7), 0, p.Z), aisle = Vector3.new(s * 4.6, 0, -4.5) })
		end
	end
end

-- ------------------------------------------------------------------------------------------------ the armory and the training gate
-- THE ARMORY: a hall in frame F (its look away from the way in, x across): d from d0 to d1, x +-w, h high, open at d0.
-- the standard weapons on lit bracket boards down the left wall (the same scale for all), the gadgets on sills under
-- them; the premium weapons turning in glass cases down the right wall (a View prompt opens the shop); a bundle
-- hologram (Slot 5) by the gate; the TRAINING GATE in the far wall (GateKit: lasers, a roll-up door, a black back) and
-- its door box in Map.Hub.Doors (o.door = its name: Land "@TrainSpawns")
local STANDARD = { "sniper", "dmr", "lmg", "autoshot", "burst", "ar", "lever", "shotgun", "smg", "bow", "revolver", "sawnoff", "pistol", "akimbo", "knife" }
local PREMIUM = { "chicken", "minigun", "redline", "laser", "bowling", "shredder", "tennis", "banana", "cart", "nailgun", "blower", "marbles", "cig", "bloodcross",
	"cards", "snowball", "water", "taser", "remote", "lasso", "bread", "scythe", "katana", "slapper", "scales", "slipper" }
local function liveSets()
	local RS = game:GetService("ReplicatedStorage")
	local ok, Roster = pcall(function() return require((RS:WaitForChild("Jankfire"):WaitForChild("Roster") :: ModuleScript):Clone()) end)
	local isLive = function(id) return true end
	local items = {}
	if ok and type(Roster) == "table" and Roster.byId then
		isLive = function(id) local e = Roster.byId[id]; return e ~= nil and e.live == true end
		for _, e in Roster.list or {} do if e.slot == "utility" and e.live then table.insert(items, e.id) end end
	end
	local std, prem = {}, {}
	local premSet = {}
	for _, id in PREMIUM do premSet[id] = true; if isLive(id) then table.insert(prem, id) end end
	for _, id in STANDARD do if isLive(id) then table.insert(std, id) end end
	if ok and type(Roster) == "table" and Roster.list then
		for _, e in Roster.list do
			if e.live and e.slot ~= "utility" and not premSet[e.id] and not table.find(STANDARD, e.id) and not table.find(std, e.id) then table.insert(std, e.id) end
		end
	end
	local names = {}
	if ok and type(Roster) == "table" and Roster.byId then for id, e in Roster.byId do names[id] = e.name end end
	return std, prem, items, names
end
function K.armory(F, o)
	local P = K.P
	local d0, d1, w, h = o.d0, o.d1, o.w, o.h
	-- the hall (z = -d in F)
	K.box(F, "Shell", "ArmoryFloor", -w - 2, w + 2, -1, 0, -d1 - 2, -d0, P.floor2, MAT.Concrete)
	K.box(F, "Scenery", "ArmoryRunner", -3.5, 3.5, 0, 0.05, -d1 + 3, -d0, P.runner, MAT.Fabric)
	K.box(F, "Shell", "ArmoryLid", -w - 2, w + 2, h, h + 1, -d1 - 2, -d0, P.dome)
	K.box(F, "Shell", "ArmoryWall", -w - 2, -w, 0, h, -d1 - 2, -d0, P.wall)
	K.box(F, "Shell", "ArmoryWall", w, w + 2, 0, h, -d1 - 2, -d0, P.wall)
	-- the far wall: a solid back layer, a front layer with the gate's opening (8.4 x 10)
	K.box(F, "Shell", "ArmoryWall", -w, w, 0, h, -d1 - 2, -d1 - 1.5, P.wall)
	K.wall(F, "ArmoryWall", -w, w, 0, h, -d1 - 1.5, -d1, P.wall, { { -4.2, 4.2, 9.96 } })
	-- coffers: beams across, panels between
	for d = d0 + 6, d1 - 4, 8 do K.box(F, "Scenery", "CeilingBeam", -w, w, h - 1.3, h, -d - 0.45, -d + 0.45, P.cream, nil, { ghost = true }) end
	for d = d0 + 10, d1 - 6, 8 do K.panel(F, 0, h, -d, 10, 3, { bright = 0.45 }) end
	-- the walls' bays: pilasters every 9.2
	for d = d0 + 1, d1 - 1, 9.2 do for _, s in { -1, 1 } do K.box(F, "Scenery", "ArmoryPilaster", s * (w - 0.7), s * w, 0, h - 1.3, -d - 0.7, -d + 0.7, P.pier) end end
	local std, prem, items, names = liveSets()
	-- standard weapons on boards down the left wall: rows of 3 per bay, all at one scale
	local Fl = F * CFrame.new(-w + 0.3, 0, 0) * CFrame.Angles(0, -math.pi / 2, 0) -- (on the left wall's face, looking into the hall: its x runs along +z, so x = -d)
	local bays = math.floor((d1 - d0 - 2) / 9.2)
	local i = 0
	for b = 1, bays do
		local dc = -(d0 + 1 + (b - 0.5) * 9.2) -- (Fl's x runs along +z in F: the hall is at -d)
		K.box(Fl, "Scenery", "RackBoard", dc - 3.9, dc + 3.9, 2.2, 11.4, -0.45, 0, P.wall2)
		K.light(K.box(Fl, "Scenery", "RackLight", dc - 3.7, dc + 3.7, 11.2, 11.4, -0.9, -0.45, P.warm, MAT.Neon, { ghost = true }), 12, 0.5)
		K.box(Fl, "Scenery", "RackSill", dc - 4.0, dc + 4.0, 2.0, 2.3, -1.4, -0.02, P.cream)
		for r = 1, 3 do
			i += 1
			local id = std[i]
			if id then
				local y = 3.9 + (r - 1) * 2.6
				K.box(Fl, "Scenery", "Bracket", dc - 0.15, dc + 0.15, y - 0.6, y - 0.35, -1.0, -0.45, P.steel)
				K.gun(Fl, "JankfireWeapons", "w_" .. id, 5, dc, y, -0.9, 0, "Rack_w_" .. id, nil)
			end
		end
	end
	-- the gadgets on the sills
	for j, id in items do
		local b = math.floor((j - 1) / 3)
		local dc = -(d0 + 1 + (b + 0.5) * 9.2) + ((j - 1) % 3 - 1) * 2.4
		if b < bays then K.gun(Fl, "JankfireItems", "x_" .. id, 1.25, dc, 2.9, -0.9, 0, "Rack_x_" .. id, nil) end
	end
	-- premium weapons turning in cases down the right wall
	local Fr = F * CFrame.new(w - 0.3, 0, 0) * CFrame.Angles(0, math.pi / 2, 0) -- (the right wall's face, looking in; x runs along +d)
	local per = math.max(1, math.min(#prem, math.floor((d1 - d0 - 4) / 3.1)))
	for j = 1, per do
		local id = prem[j]
		local dc = d0 + 2 + (j - 0.5) * (d1 - d0 - 4) / per
		local x = dc -- (Fr's x runs along -z in F: +d)
		K.box(Fr, "Shell", "CaseFoot", x - 1.3, x + 1.3, 0, 2.4, -2.6, -0.2, P.dark)
		K.box(Fr, "Scenery", "CaseGlass", x - 1.25, x + 1.25, 2.4, 6.2, -2.55, -0.25, P.glass, MAT.Glass, { tr = 0.65, solid = true })
		K.box(Fr, "Scenery", "CaseLid", x - 1.3, x + 1.3, 6.2, 6.5, -2.6, -0.2, P.dark)
		K.light(K.box(Fr, "Scenery", "CaseLight", x - 0.8, x + 0.8, 6.05, 6.2, -1.8, -1.0, P.warm, MAT.Neon, { ghost = true }), 6, 0.6)
		local g = K.gun(Fr, "JankfireWeapons", "w_" .. id, 2.2, x, 4.2, -1.4, 0, "Case_w_" .. id, nil)
		if g then g:SetAttribute("Spin", 0.5); g:SetAttribute("SpinNear", 70); Tags:AddTag(g, "HubSpin") end
		local cp = K.box(Fr, "Scenery", "CasePrompt", x - 0.2, x + 0.2, 3.6, 4.0, -2.9, -2.7, P.pier, nil, { ghost = true, tr = 1 })
		local pr = Instance.new("ProximityPrompt")
		pr.Name = "CasePrompt"; pr.ActionText = "View"; pr.ObjectText = names[id] or string.upper(id)
		pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0; pr.MaxActivationDistance = 7
		pr.RequiresLineOfSight = false; pr.ClickablePrompt = true; pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
		pr:SetAttribute("ShopOpen", "tab:featured"); pr:SetAttribute("Weapon", id)
		pr.Parent = cp
	end
	-- the bundle hologram by the gate (Slot 5) and its plate
	plinth(F, -w + 5, -d1 + 5, 3.8, 1.4)
	K.holo(F, "bundle", -w + 5, 1.4 + 2.2, -d1 + 5, 1.8, 3.6, { base = 2.2, slot = 5, prompt = "View bundle" })
	local plate = K.box(F, "Scenery", "ShowName5", -w + 3.4, -w + 6.6, 0.5, 1.3, -d1 + 7.6, -d1 + 7.45, P.screen, nil, { solid = false })
	K.text(plate, Enum.NormalId.Back, { { "BUNDLE", P.holo, 0.38, "S" }, { "COMING SOON", P.pale, 0.5 } }, { guiName = "Gui", flat = true, pps = 60 })
	-- the training gate: GateKit's lasers, roll-up door and black back in the far wall's opening; the kit frame round it;
	-- the door box (in Map.Hub.Doors when live) that takes you to the training ground
	local Fg = F * CFrame.new(0, 0, -d1)
	local GK = require((game:GetService("ServerStorage"):WaitForChild("PolishBackup"):WaitForChild("GateKit") :: ModuleScript):Clone())
	local gf = Instance.new("Folder"); gf.Name = "TrainingGate"; gf.Parent = K.folder("Scenery")
	GK.build(S.site * Fg, gf, { door = "TrainingShutter", lasers = "TrainingLaserGate" })
	K.kit(Fg, "hb_portal", "TrainingPortal", 0, 0, 0.6, 180, { scale = GK.FRAME.scale, color = GK.FRAME.color })
	K.light(K.box(Fg, "Scenery", "GateLamp", -0.5, 0.5, GK.LAMP.up, GK.LAMP.up + 0.2, GK.LAMP.out - 0.5, GK.LAMP.out + 0.5, P.pier, nil, { ghost = true, tr = 1 }), GK.LAMP.range, GK.LAMP.bright, GK.LAMP.hex)
	K.sign(F * CFrame.new(0, 0, -d1 + 0.3) * CFrame.Angles(0, math.pi, 0), "Scenery", "GateSign", 10, 1.6, 0, 12.4, 0, { { "TRAINING", P.pale, 0.75 } }, { pps = 46 }) -- (facing the hall)
	if S.live and o.door then
		local doors = workspace.Map.Hub:FindFirstChild("Doors")
		if doors then
			local old = doors:FindFirstChild(o.door); if old then old:Destroy() end
			local t = Instance.new("Part")
			t.Name = o.door; t.Anchored = true; t.CanCollide = false; t.CanQuery = false; t.CanTouch = false; t.Transparency = 1; t.CastShadow = false
			t.Size = Vector3.new(7.8, 10, 2.6); t.CFrame = S.site * F * CFrame.new(0, 5, -(d1 - 1.6) - 1.3)
			t:SetAttribute("Land", "@TrainSpawns"); t:SetAttribute("Say", "TRAINING GROUND"); t:SetAttribute("Hub", S.hub)
			t.Parent = doors
		end
	end
end

-- ------------------------------------------------------------------------------------------------ the check
-- walks: { name, F, x0, x1, z0, z1, y } boxes that must be clear of anything solid from the floor's step (y + 0.6) to
-- head height (y + 6); leaks: { F, x, y, z } points from which no ray may get out (12 rays round, 3 up/down tilts)
function K.check(walks, leaks, ignore)
	local root = S.root :: Folder
	local issues = {}
	local op = OverlapParams.new(); op.FilterType = Enum.RaycastFilterType.Include; op.FilterDescendantsInstances = { root }
	for _, w in walks do
		local F = w[2]
		local cf = S.site * F * CFrame.new((w[3] + w[4]) / 2, (w[7] or 0) + 3.3, (w[5] + w[6]) / 2)
		local size = Vector3.new(math.abs(w[4] - w[3]), 5.4, math.abs(w[6] - w[5]))
		for _, p in workspace:GetPartBoundsInBox(cf, size, op) do
			if p.CanCollide and p.Transparency < 1 and not (ignore and ignore(p)) then
				table.insert(issues, ("WALK %s: %s in the way"):format(w[1], p:GetFullName():gsub("^.-" .. root.Name .. "%.", "")))
				break
			end
		end
	end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { root }
	local nLeak = 0
	for _, l in leaks do
		local o = (S.site * l[1] * CFrame.new(l[2], l[3], l[4])).Position
		for i = 0, 11 do
			for _, tilt in { -0.35, 0, 0.6 } do
				local a = i * math.pi / 6
				local dir = Vector3.new(math.cos(a), tilt, math.sin(a)).Unit * 400
				if not workspace:Raycast(o, dir, rp) then nLeak += 1 end
			end
		end
		if not workspace:Raycast(o, Vector3.new(0, 400, 0), rp) then nLeak += 1 end
		if not workspace:Raycast(o, Vector3.new(0, -60, 0), rp) then nLeak += 1 end
	end
	if nLeak > 0 then table.insert(issues, ("LEAKS: %d rays got out"):format(nLeak)) end
	return issues
end

return K
