--!strict
-- MAP ROOMS: where a hub pad's players vote on the map (18 Nov 2026, the owner: "map select should happen after pads
-- itll spawn you in liek a void area where the map options appear then itll bring you to said map"). one room per
-- group voting at once, built from code when a pad sends its group and destroyed after it has gone to the arena, like
-- the party lobbies (LobbyRooms). they stand in a row far from every map (workspace.MapRooms, out of Map, so ZoneCull
-- leaves them drawn while everything else is put aside), with their own dark look (HubLook "void", the "staging" zone).
-- a room: a round charcoal platform in a dark void, a lower ring under its edge; on the far side three big framed
-- displays on an arc, each showing one map's picture and name, softly lit from its own screen; a round floor plate in
-- front of each (standing on it votes for that map). an invisible rail round the rim keeps everyone on. the house look:
-- few big rounded shapes, flat greys, no colour but the amber plate of the map that wins (Matches runs the vote)
local Workspace = game:GetService("Workspace")

local MapRooms = {}

MapRooms.ORIGIN = Vector3.new(0, 1400, -60000) -- the first room's floor centre: far from the hub, the lobbies and every arena
MapRooms.STEP = Vector3.new(400, 0, 0)
MapRooms.RADIUS = 40 -- the platform's walkable radius
MapRooms.PLATE_R = 5.5 -- a vote plate's radius

local ACCENT = Color3.fromRGB(214, 150, 40)
local C = {
	floor = Color3.fromRGB(56, 59, 66), under = Color3.fromRGB(38, 40, 46), ring = Color3.fromRGB(46, 49, 56),
	frame = Color3.fromRGB(34, 36, 42), plinth = Color3.fromRGB(44, 47, 54), plate = Color3.fromRGB(78, 82, 92),
	plateRim = Color3.fromRGB(40, 43, 50), screen = Color3.fromRGB(18, 19, 22), text = Color3.fromRGB(236, 238, 242),
	muted = Color3.fromRGB(150, 156, 166),
}
local FONT = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Heavy)
local FONT_BOLD = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Bold)

export type Room = {
	slot: number, model: Model, origin: CFrame, spots: { CFrame }, look: Vector3,
	plates: { Vector3 }, screens: { BasePart }, frames: { BasePart }, plateParts: { BasePart },
}

local rooms: { [number]: Room } = {}

local function folder(): Folder
	local f = Workspace:FindFirstChild("MapRooms")
	if not f then
		f = Instance.new("Folder")
		f.Name = "MapRooms"
		f.Parent = Workspace
	end
	return f :: Folder
end

local function part(parent: Instance, name: string, size: Vector3, cf: CFrame, color: Color3, shape: Enum.PartType?, mat: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanTouch = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Material = mat or Enum.Material.SmoothPlastic
	p.Color = color
	if shape then p.Shape = shape end
	p.Size = size
	p.CFrame = cf
	p.Parent = parent
	return p
end
-- a flat disc (a cylinder on its side, its round face up) of diameter d and height h, centred at cf
local function disc(parent: Instance, name: string, d: number, h: number, cf: CFrame, color: Color3, mat: Enum.Material?): Part
	return part(parent, name, Vector3.new(h, d, d), cf * CFrame.Angles(0, 0, math.rad(90)), color, Enum.PartType.Cylinder, mat)
end

local function surfaceText(p: BasePart, face: Enum.NormalId, name: string, size: number, color: Color3, font: Font): TextLabel
	local g = Instance.new("SurfaceGui")
	g.Name = name
	g.Face = face
	g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	g.PixelsPerStud = 40
	g.LightInfluence = 0
	g.Brightness = 1
	g.Parent = p
	local t = Instance.new("TextLabel")
	t.Name = "Text"
	t.BackgroundTransparency = 1
	t.Size = UDim2.fromScale(1, 1)
	t.FontFace = font
	t.TextColor3 = color
	t.TextScaled = true
	t.Text = ""
	local lim = Instance.new("UITextSizeConstraint")
	lim.MaxTextSize = size
	lim.Parent = t
	t.Parent = g
	return t
end

-- the three displays: big (each map fills a good part of the view: the main session, 18 Nov, "about twice the size
-- and bring the arc closer"), on an arc round the spot where the group lands (VIEW, room space: -z is the far side),
-- each turned to it, far enough apart that the three frames stand clear of each other
local VIEW = Vector3.new(0, 0, 22)
local SLOT_ANGLE = { -54, 0, 54 } -- degrees round from straight ahead
local DISPLAY_R = { 42, 34, 42 } -- from VIEW to each display's face (the middle one, the one you face on landing, nearer)
local PLATE_D = 26 -- from VIEW to a plate's middle
local SW, SH = 30, 16.9 -- the screen (16:9); the frame is 3 wider and 3.5 taller

local function build(slot: number): Room
	local o = CFrame.new(MapRooms.ORIGIN + MapRooms.STEP * (slot - 1))
	local m = Instance.new("Model")
	m.Name = ("MapRoom%d"):format(slot)
	local R = MapRooms.RADIUS
	-- the platform: a thick charcoal disc, a lower, wider ring under its edge, a dark underside
	disc(m, "Floor", R * 2, 4, o * CFrame.new(0, -2, 0), C.floor)
	disc(m, "Ring", R * 2 + 6, 2, o * CFrame.new(0, -3.6, 0), C.ring)
	disc(m, "Under", R * 2 - 10, 6, o * CFrame.new(0, -7, 0), C.under)
	-- the rail: invisible walls round the rim, so nobody walks off into the void
	local n = 28
	for i = 1, n do
		local a = (i - 0.5) / n * math.pi * 2
		local w = part(m, "Rail", Vector3.new(2 * math.pi * (R + 1) / n + 0.6, 40, 1), o * CFrame.Angles(0, a, 0) * CFrame.new(0, 20, -(R + 1)), C.under)
		w.Transparency = 1
		w.CanQuery = false
	end
	local screens, frames, plates, plateParts = {}, {}, {}, {}
	for i, deg in SLOT_ANGLE do
		local turn = o * CFrame.new(VIEW) * CFrame.Angles(0, math.rad(-deg), 0)
		-- the display: a dark slab frame, rounded at the sides (two thick upright cylinders), on a low plinth
		local base = turn * CFrame.new(0, 0, -DISPLAY_R[i])
		local FW, FH = SW + 3, SH + 3.5
		local fy = 2.4 + FH / 2 -- (the frame stands on the plinth, a hand over it)
		part(m, "Plinth" .. i, Vector3.new(FW, 2, 6), base * CFrame.new(0, 1, -1), C.plinth)
		local frame = part(m, "Frame" .. i, Vector3.new(FW, FH, 2), base * CFrame.new(0, fy, -1.6), C.frame)
		for _, sx in { -1, 1 } do
			part(m, "Edge" .. i, Vector3.new(FH, 2.6, 2.6), base * CFrame.new(sx * FW / 2, fy, -1.6) * CFrame.Angles(0, 0, math.rad(90)), C.frame, Enum.PartType.Cylinder)
		end
		part(m, "Cap" .. i, Vector3.new(FW, 2.6, 2.6), base * CFrame.new(0, 2.4 + FH, -1.6), C.frame, Enum.PartType.Cylinder) -- (a cylinder runs along x: the frame's width)
		-- the screen: 16:9, flush in the frame's face, its own light falling on the plate in front
		local screen = part(m, "Screen" .. i, Vector3.new(SW, SH, 0.4), base * CFrame.new(0, 2.4 + FH - 1 - SH / 2, -0.5), C.screen)
		local g = Instance.new("SurfaceGui")
		g.Name = "Picture"
		g.Face = Enum.NormalId.Back -- (the face towards the platform's middle: room space +z)
		g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = 30
		g.LightInfluence = 0
		g.Brightness = 1.1
		g.Parent = screen
		local img = Instance.new("ImageLabel")
		img.Name = "Image"
		img.BackgroundColor3 = C.screen
		img.BorderSizePixel = 0
		img.Size = UDim2.fromScale(1, 1)
		img.ScaleType = Enum.ScaleType.Crop
		img.Image = ""
		img.Parent = g
		local light = Instance.new("SurfaceLight")
		light.Face = Enum.NormalId.Back; light.Brightness = 0.45; light.Range = 30; light.Angle = 120
		light.Color = Color3.fromRGB(226, 230, 238); light.Shadows = false
		light.Parent = screen
		-- the name and the votes on the frame's lower strip (a thin strip part in front of the frame)
		local strip = part(m, "Strip" .. i, Vector3.new(SW, 2.4, 0.3), base * CFrame.new(0, 2.4 + 1.25, -0.45), C.frame)
		local name = surfaceText(strip, Enum.NormalId.Back, "Name", 60, C.text, FONT)
		name.Size = UDim2.fromScale(0.72, 1)
		name.TextXAlignment = Enum.TextXAlignment.Left
		local votes = Instance.new("TextLabel")
		votes.Name = "Votes"
		votes.BackgroundTransparency = 1
		votes.AnchorPoint = Vector2.new(1, 0)
		votes.Position = UDim2.fromScale(1, 0)
		votes.Size = UDim2.fromScale(0.28, 1)
		votes.FontFace = FONT_BOLD
		votes.TextColor3 = C.muted
		votes.TextScaled = true
		votes.TextXAlignment = Enum.TextXAlignment.Right
		votes.Text = ""
		local vlim = Instance.new("UITextSizeConstraint")
		vlim.MaxTextSize = 44
		vlim.Parent = votes
		votes.Parent = name.Parent
		-- the vote plate in front of it: a pale disc on a dark rim
		local pc = turn * CFrame.new(0, 0, -PLATE_D)
		disc(m, "PlateRim" .. i, MapRooms.PLATE_R * 2 + 1.4, 0.3, pc * CFrame.new(0, 0.15, 0), C.plateRim)
		local plate = disc(m, "Plate" .. i, MapRooms.PLATE_R * 2, 0.4, pc * CFrame.new(0, 0.2, 0), C.plate)
		plate:SetAttribute("Option", i)
		table.insert(screens, screen)
		table.insert(frames, frame)
		table.insert(plates, pc.Position)
		table.insert(plateParts, plate)
	end
	-- a dim light high over the middle, so the players can see each other
	local top = part(m, "TopLight", Vector3.new(1, 1, 1), o * CFrame.new(0, 34, 6), C.under)
	top.Transparency = 1
	top.CanCollide = false
	top.CanQuery = false
	local pl = Instance.new("PointLight")
	pl.Brightness = 0.5; pl.Range = 60; pl.Color = Color3.fromRGB(220, 224, 232); pl.Shadows = false
	pl.Parent = top
	-- where the group arrives: the near side, in two rows, facing the displays
	local spots = {}
	for row = 0, 1 do
		for col = -2, 1 do
			local p = (o * CFrame.new((col + 0.5) * 5, 0, 22 + row * 5)).Position
			table.insert(spots, CFrame.lookAt(p, p + Vector3.new(0, 0, -1)))
		end
	end
	m:SetAttribute("Slot", slot)
	m.WorldPivot = o
	m.Parent = folder()
	return { slot = slot, model = m, origin = o, spots = spots, look = Vector3.new(0, 0, -1), plates = plates, screens = screens,
		frames = frames, plateParts = plateParts }
end

-- a free room (built now), or nil if something went wrong
function MapRooms.claim(): Room?
	local k = 1
	while rooms[k] do k += 1 end
	local ok, r = pcall(build, k)
	if not ok then warn("[jankfire] map room: " .. tostring(r)); return nil end
	rooms[k] = r :: Room
	return r :: Room
end

function MapRooms.release(r: Room)
	if rooms[r.slot] == r then rooms[r.slot] = nil end
	if r.model.Parent then r.model:Destroy() end
end

-- the displays: cards = { { id, title, thumb } } (up to 3), counts = { [id] = votes }, picked = the winner once there
-- is one (its frame gets the amber edge, the others go dim)
function MapRooms.show(r: Room, cards: { any }, counts: { [string]: number }, picked: string?)
	for i = 1, 3 do
		local card = cards[i]
		local screen = r.screens[i]
		local g = screen and screen:FindFirstChild("Picture")
		local img = g and g:FindFirstChild("Image") :: ImageLabel?
		local strip = r.model:FindFirstChild("Strip" .. i)
		local nameG = strip and strip:FindFirstChild("Name")
		local name = nameG and nameG:FindFirstChild("Text") :: TextLabel?
		local votes = nameG and nameG:FindFirstChild("Votes") :: TextLabel?
		local won = picked ~= nil and card ~= nil and card.id == picked
		local dim = picked ~= nil and not won
		if img then
			img.Image = if card then card.thumb or "" else ""
			img.ImageTransparency = if dim then 0.65 else 0
		end
		if name then
			name.Text = if card then string.upper(card.title or card.id) else ""
			name.TextColor3 = if dim then C.muted else C.text
		end
		if votes then
			local k = if card then counts[card.id] or 0 else 0
			votes.Text = if k == 1 then "1 VOTE" elseif k > 1 then ("%d VOTES"):format(k) else ""
			votes.TextColor3 = if won then ACCENT else C.muted
		end
		-- (the winner: its frame a shade lighter and its plate amber, flat, no glow: the room stays quiet)
		local frame = r.frames[i]
		if frame then frame.Color = if won then C.plinth:Lerp(C.plate, 0.5) else C.frame end
		local plate = r.plateParts[i]
		if plate then plate.Color = if won then ACCENT elseif dim then C.plateRim else C.plate end
	end
end

-- which plate (1-3) a body stands on, or nil
function MapRooms.plateAt(r: Room, pos: Vector3): number?
	for i, c in r.plates do
		local d = Vector3.new(pos.X - c.X, 0, pos.Z - c.Z).Magnitude
		if d <= MapRooms.PLATE_R and math.abs(pos.Y - c.Y) < 8 then return i end
	end
	return nil
end

function MapRooms.count(): number
	local n = 0
	for _ in rooms do n += 1 end
	return n
end

return MapRooms
