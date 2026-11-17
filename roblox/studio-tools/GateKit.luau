--!nonstrict
-- the gate between the hub and the training area, the same on both sides (owner, 17 Nov: "can the laser fence be on
-- both side of the hub and same with the garage door because its weird to have the grid on one side and a garage door
-- on the other"; then "the garage door should be behind the laser, hello??"): the red laser fence at the opening's
-- face, the roll-up garage door just behind it, a portal behind that (not a dead end: an open gate shows a calm amber
-- glow, brightest low down, a slow swirl of paler light in it, a warm light spilling out onto the floor;
-- GatePortal.client turns the swirl; tagged "GatePortal"), one amber light bar over the head. walk up to it and the
-- lasers click off (Near 17), then the door rolls up (Near 13); walk away and both close again. TrainingDoors.client
-- does both on every screen
-- (the door: a Model tagged "Shutter" with Shutter, Lift, Top, Center and Near, its slats' Shut places; the lasers: a
-- Model tagged "LaserGate" with Center and Near): only on screen, the slats and the lasers never block. the walk-in
-- trigger, the walls round the opening and the frame are each builder's own; the frame is the kit's hb_portal at
-- GateKit.FRAME, so both sides wear the same colours. HubRotunda (the armory's gate) and TrainingV2 (the muster's gate
-- home) both build theirs here:
--   local K = require(game.ServerStorage.PolishBackup.GateKit:Clone())
--   K.build(F, parent, { door = "...", lasers = "..." })
-- F: a frame on the floor in the middle of the opening, its -Z the way you walk in; d = how far in from the door's face
local CollectionService = game:GetService("CollectionService")

local K = {}
K.W, K.H = 8.4, 9.96 -- (the opening: across, up)
K.DEPTH = 1.45 -- (the opening's face to the back of the portal)
K.FRAME = { scale = 0.6, color = { ff4fd8 = "f0a53a", ["2e3140"] = "3f4753", a4aab8 = "747c88" } } -- (hb_portal: amber trim on slate)
K.LAMP = { up = 8, out = 1.5, range = 10, bright = 0.5, hex = "ffc27a" } -- (a warm point light this far up and out in front)
K.COL = { slat = "6b7079", back = "2b2d33", laser = "ff2a3a", bar = "f0a53a", portal = "f0a53a", portalHi = "ffe2b0", portalDeep = "1c1610" }

function K.build(F: CFrame, parent: Instance, o: { door: string?, lasers: string? }?)
	local opts = o or {}
	local function box(name, x0, x1, y0, y1, d0, d1, hex, neon, tr)
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Size = Vector3.new(x1 - x0, y1 - y0, d1 - d0)
		p.CFrame = F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2)
		p.Color = Color3.fromHex(hex)
		p.Material = if neon then Enum.Material.Neon else Enum.Material.SmoothPlastic
		p.Transparency = tr or 0
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		return p
	end
	local hw, H = K.W / 2, K.H
	-- the door: nine slats just behind the lasers; they roll up into the head (hidden above Top)
	local door = Instance.new("Model")
	door.Name = opts.door or "GateDoor"
	local bottom: BasePart? = nil
	for k = 0, 8 do
		local y = 0.2 + k * 1.08
		local sl = box("ShutterSlat", -hw, hw, y, y + 0.95, 0.6, 1.0, K.COL.slat)
		sl:SetAttribute("Shut", sl.CFrame)
		sl.Parent = door
		bottom = bottom or sl
	end
	local b0 = bottom :: BasePart
	door:SetAttribute("Shutter", true)
	door:SetAttribute("Lift", 10.3)
	door:SetAttribute("Top", b0.Position.Y - 0.475 + 9.76)
	door:SetAttribute("Center", Vector3.new(b0.Position.X, b0.Position.Y - 0.675, b0.Position.Z))
	door:SetAttribute("Near", 13)
	door.Parent = parent
	CollectionService:AddTag(door, "Shutter")
	-- the laser fence at the opening's face, in front of the door: a faint red sheet and five red bars
	local lasers = Instance.new("Model")
	lasers.Name = opts.lasers or "GateLasers"
	box("LaserField", -hw, hw, 0, H, 0.15, 0.3, K.COL.laser, true, 0.88).Parent = lasers
	for i = 1, 5 do
		local bar = box("LaserBar", -hw, hw, i * 1.66 - 0.22, i * 1.66 + 0.22, 0, 0.44, K.COL.laser, true)
		bar.Shape = Enum.PartType.Cylinder
		bar.Parent = lasers
	end
	lasers:SetAttribute("Center", (F * CFrame.new(0, 5, -0.22)).Position)
	lasers:SetAttribute("Near", 17) -- (first: they click off before the door behind them starts up)
	lasers.Parent = parent
	CollectionService:AddTag(lasers, "LaserGate")
	-- the portal behind (its face toward you is the part's Back): a deep warm dark, an amber glow rising from the floor,
	-- a soft round swirl of paler light that GatePortal.client turns slowly; and its light out over the floor in front
	local portal = box("GatePortal", -hw, hw, 0, H, 1.15, K.DEPTH, K.COL.portalDeep)
	local sg = Instance.new("SurfaceGui")
	sg.Name = "PortalFace"; sg.Face = Enum.NormalId.Back; sg.LightInfluence = 0; sg.Brightness = 1.3
	sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 24
	sg.Parent = portal
	local function layer(name, hex, z)
		local fr = Instance.new("Frame")
		fr.Name = name; fr.Size = UDim2.fromScale(1, 1); fr.BorderSizePixel = 0; fr.ZIndex = z
		fr.BackgroundColor3 = Color3.fromHex(hex)
		fr.Parent = sg
		return fr
	end
	layer("Deep", K.COL.portalDeep, 1)
	local rise = layer("Rise", K.COL.portal, 2) -- (the glow from the floor up: brightest low down)
	local g1 = Instance.new("UIGradient")
	g1.Rotation = 90
	g1.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.92), NumberSequenceKeypoint.new(0.55, 0.62), NumberSequenceKeypoint.new(1, 0.18) })
	g1.Parent = rise
	local swirl = layer("Swirl", K.COL.portalHi, 3) -- (a soft round of paler light, turned slowly: GatePortal.client)
	swirl.AnchorPoint = Vector2.new(0.5, 0.5); swirl.Position = UDim2.fromScale(0.5, 0.56); swirl.Size = UDim2.fromScale(1.15, 0.97)
	local corner = Instance.new("UICorner"); corner.CornerRadius = UDim.new(0.5, 0); corner.Parent = swirl
	local g2 = Instance.new("UIGradient")
	g2.Name = "Turn"
	g2.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromHex(K.COL.portal)), ColorSequenceKeypoint.new(0.5, Color3.fromHex(K.COL.portalHi)), ColorSequenceKeypoint.new(1, Color3.fromHex(K.COL.portal)) })
	g2.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.97), NumberSequenceKeypoint.new(0.5, 0.72), NumberSequenceKeypoint.new(1, 0.97) })
	g2.Parent = swirl
	local spill = Instance.new("SurfaceLight") -- (the glow out over the floor in front)
	spill.Face = Enum.NormalId.Back; spill.Color = Color3.fromHex(K.COL.portal); spill.Brightness = 0.9; spill.Range = 11; spill.Angle = 110; spill.Shadows = false
	spill.Parent = portal
	portal.Parent = parent
	CollectionService:AddTag(portal, "GatePortal")
	-- the amber light bar along the head, in front
	box("GateLightBar", -hw + 0.2, hw - 0.2, H - 0.01, H + 0.39, -0.3, 0, K.COL.bar, true).Parent = parent
	return door, lasers
end

return K
