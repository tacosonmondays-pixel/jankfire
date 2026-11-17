--!nonstrict
-- the gate between the hub and the training area, the same on both sides (owner, 17 Nov: "can the laser fence be on
-- both side of the hub and same with the garage door because its weird to have the grid on one side and a garage door
-- on the other"; then "the garage door should be behind the laser, hello??"): the red laser fence at the opening's
-- face, the roll-up garage door just behind it, the dark plate behind that (an open gate shows a black doorway: owner,
-- 17 Nov, "I like the old black entrances for doors idk if i like the gold.."; the amber portal tried at v656 is gone),
-- one amber light bar over the head. walk up to it and the lasers click off (Near 17), then the door rolls up
-- (Near 13); walk away and both close again. TrainingDoors.client does both on every screen
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
K.DEPTH = 1.45 -- (the opening's face to the back of the dark plate)
K.FRAME = { scale = 0.6, color = { ff4fd8 = "f0a53a", ["2e3140"] = "3f4753", a4aab8 = "747c88" } } -- (hb_portal: amber trim on slate)
K.LAMP = { up = 8, out = 1.5, range = 10, bright = 0.5, hex = "ffc27a" } -- (a warm point light this far up and out in front)
K.COL = { slat = "6b7079", back = "2b2d33", laser = "ff2a3a", bar = "f0a53a" }

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
	-- the dark plate behind: what an open gate shows (black in the hub's light)
	box("GateBack", -hw, hw, 0, H, 1.15, K.DEPTH, K.COL.back).Parent = parent
	-- the amber light bar along the head, in front
	box("GateLightBar", -hw + 0.2, hw - 0.2, H - 0.01, H + 0.39, -0.3, 0, K.COL.bar, true).Parent = parent
	return door, lasers
end

return K
