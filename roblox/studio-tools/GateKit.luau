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
--
-- THE LOOKS (27 Nov, the owner, on main's note that every judge reads the red laser fence before a shutter as "closed,
-- keep out" rather than "this way to training": "You can try?? Let me know send screenshots"). K.STYLE picks the look
-- every build gets (o.style for one build); K.restyle(door, style) turns a gate that is already built into another look
-- where it stands, without rebuilding its hub:
--   "classic": the red lasers, the roll-up shutter, the dark plate, the amber light bar (17 Nov to 27 Nov)
--   "lit":     no shutter and no lasers: the way through ends on a white light panel in a pale back wall, a white
--              sill light across the threshold, the light thrown out onto the floor in front (the compound's white
--              light panels; no colour)
--   "scan":    no shutter: the dark doorway the owner liked, three thin cool-white scan lines across it and the white
--              sill light (the lines carry Fade for a by-distance fade the client does not do yet: they click off)
--   "litscan": the lit way through with the roller box over the head (the door rolled away into it) and the scan lines
--   "passage": THE LOOK SINCE 27 NOV. two blind judges picked "lit" over the old gate (6 and 6.5 for reading as a way in,
--              against 2) and both asked for depth instead of its flat glowing plate: a short lit passage drawn in
--              perspective (sides and ceiling closing in to a pale end wall, a white light panel on its ceiling), the
--              white sill light between the pillars; no lasers, no shutter, no colour
-- in every look the door stays a Model named o.door with Center, Top and Near (HubRotHotel puts TRAINING over it by
-- them), but only "classic" makes it a Shutter with slats; the back plate is always a part named GateBack
local CollectionService = game:GetService("CollectionService")

local K = {}
K.W, K.H = 8.4, 9.96 -- (the opening: across, up)
K.DEPTH = 1.45 -- (the opening's face to the back of the dark plate)
K.FRAME = { scale = 0.6, color = { ff4fd8 = "f0a53a", ["2e3140"] = "3f4753", a4aab8 = "747c88" } } -- (hb_portal: amber trim on slate)
K.LAMP = { up = 8, out = 1.5, range = 10, bright = 0.5, hex = "ffc27a" } -- (a warm point light this far up and out in front)
K.COL = { slat = "6b7079", back = "2b2d33", laser = "ff2a3a", bar = "f0a53a", housing = "3f4753",
	litBack = "c9cfcf", panel = "eef3f2", sill = "e9eeec", scan = "d6f1ff", passEnd = "d4d9d7", passSide = "aeb5b8", passTop = "c3c9ca" }
K.STYLE = "passage"
-- the door's path (26 Nov, the owner: "the door goes over the the frrame, like clips through it"; the clip check,
-- PolishBackup.Clip, found every gate's slats rising up to 0.95 over the opening into whatever wall stood there). the
-- slats run x -4.2..4.2 at d 0.6..1.0 (in from the opening's face, F's -Z) and rise K.LIFT; a slat is hidden once its
-- bottom passes the opening's head (Top = H), so over the head a slat shows at most its own height, 0.95. they roll up
-- into K.HOUSING over the head: a slate roller box x -4.5..4.5, H..H+1.3 up, d 0.45..1.45 (to the dark plate's back).
-- a builder's wall over the opening must leave that box clear (a slot) or stand wholly in front of or behind it; the
-- laser fence (d 0..0.44) and the light bar (d -0.3..0) stay in front of it
K.LIFT = 10.3
K.HOUSING = { x = 4.5, up = 1.3, d0 = 0.45, d1 = 1.45 }

-- the parts of one look at F (W, H: the opening), into parent; door = the Model that stands for the door
local function parts(F: CFrame, parent: Instance, door: Model, lasersName: string, style: string, W: number, H: number)
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
	local hw = W / 2
	local lasers = nil
	door:SetAttribute("Center", (F * CFrame.new(0, 0, -0.8)).Position)
	door:SetAttribute("Top", (F * CFrame.new(0, H, 0)).Y)
	door:SetAttribute("Near", 13)
	door:SetAttribute("Look", style)
	if style == "classic" then
		-- the door: nine slats just behind the lasers; they roll up into the head (hidden above Top)
		local sh = H / 9.96
		for k = 0, 8 do
			local y = (0.2 + k * 1.08) * sh
			local sl = box("ShutterSlat", -hw, hw, y, y + 0.95 * sh, 0.6, 1.0, K.COL.slat)
			sl:SetAttribute("Shut", sl.CFrame)
			sl.Parent = door
		end
		door:SetAttribute("Shutter", true)
		door:SetAttribute("Lift", K.LIFT * sh)
		CollectionService:AddTag(door, "Shutter")
		-- the laser fence at the opening's face, in front of the door: a faint red sheet and five red bars
		lasers = Instance.new("Model")
		lasers.Name = lasersName
		box("LaserField", -hw, hw, 0, H, 0.15, 0.3, K.COL.laser, true, 0.88).Parent = lasers
		for i = 1, 5 do
			local bar = box("LaserBar", -hw, hw, i * 1.66 * sh - 0.22, i * 1.66 * sh + 0.22, 0, 0.44, K.COL.laser, true)
			bar.Shape = Enum.PartType.Cylinder
			bar.Parent = lasers
		end
		lasers:SetAttribute("Center", (F * CFrame.new(0, 5, -0.22)).Position)
		lasers:SetAttribute("Near", 17) -- (first: they click off before the door behind them starts up)
		-- the dark plate behind: what an open gate shows (black in the hub's light)
		box("GateBack", -hw, hw, 0, H, 1.15, K.DEPTH, K.COL.back).Parent = parent
		-- the roller box over the head the slats roll up into (K.HOUSING)
		local HS = K.HOUSING
		box("ShutterHousing", -HS.x, HS.x, H, H + HS.up, HS.d0, HS.d1, K.COL.housing).Parent = parent
		-- the amber light bar along the head, in front
		box("GateLightBar", -hw + 0.2, hw - 0.2, H - 0.01, H + 0.39, -0.3, 0, K.COL.bar, true).Parent = parent
	elseif style == "passage" then
		-- the way through as a short lit passage (both judges, 27 Nov, picking "lit": "replace the flat white panel with
		-- a short visible passage ... side walls that recede ... a softer light at the far end"). the gate is only
		-- K.DEPTH deep, so the passage is drawn in perspective: its sides and ceiling close in from the mouth (behind the
		-- frame's pillars) to a smaller pale end wall, and a white light panel on its ceiling lights it
		local D1 = K.DEPTH
		-- (the mouth meets the pillars' faces and the head, so no dark gap shows round it)
		local mx, md, ex, ed = hw - 0.02, 0.3, hw - 1.6, D1 - 0.1 -- (mouth half-width and depth, end half-width and depth)
		local mt, et = H - 0.02, H - 1.2 -- (the ceiling's height at the mouth and at the end)
		-- a slab from point a to point b (F space, plan: x, y, d), w across, t thick, its face turned by up
		local function slab(name, a: Vector3, b: Vector3, w: number, t: number, across: Vector3, hex: string, neon: boolean?)
			local pa, pb = Vector3.new(a.X, a.Y, -a.Z), Vector3.new(b.X, b.Y, -b.Z)
			local mid, along = (pa + pb) / 2, pb - pa
			local up = along:Cross(across).Unit
			local p = Instance.new("Part")
			p.Name = name
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
			p.Size = Vector3.new(w, t, along.Magnitude)
			p.CFrame = F * CFrame.lookAt(mid, mid + along, up)
			p.Color = Color3.fromHex(hex)
			p.Material = if neon then Enum.Material.Neon else Enum.Material.SmoothPlastic
			p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
			p.Parent = parent
			return p
		end
		-- the end wall: the whole opening at the back (the gaps by the pillars show it too)
		box("GateBack", -hw, hw, 0, H, ed, D1, K.COL.passEnd).Parent = parent
		-- the sides, closing in (each its own slab, 0.2 thick, the full height at the mouth)
		for _, s in { -1, 1 } do
			local w = slab("GatePassageSide", Vector3.new(s * mx, mt / 2, md), Vector3.new(s * ex, mt / 2, ed), mt, 0.2, Vector3.yAxis, K.COL.passSide)
			w.Size = Vector3.new(mt, 0.2, w.Size.Z) -- (its width runs up: the slab stands on its edge)
		end
		-- the ceiling, coming down toward the end, and its white light panel
		slab("GatePassageCeiling", Vector3.new(0, mt, md), Vector3.new(0, et, ed), 2 * mx, 0.2, Vector3.xAxis, K.COL.passTop)
		-- (the panel 0.14 under the ceiling's line, along the ceiling's downward normal: the slab is 0.2 thick)
		local dy, dd = et - mt, ed - md
		local len = math.sqrt(dy * dy + dd * dd)
		local ny, nd = -dd / len * 0.14, dy / len * 0.14 -- (down, and out toward the room)
		local pnl = slab("GatePanel", Vector3.new(0, mt + ny, md + 0.25 + nd), Vector3.new(0, et + ny, ed - 0.15 + nd), 2 * ex - 0.8, 0.05, Vector3.xAxis, K.COL.panel, true)
		local pl = Instance.new("PointLight")
		pl.Color = Color3.fromRGB(236, 243, 242); pl.Brightness = 1.1; pl.Range = 11; pl.Shadows = false; pl.Parent = pnl
		-- the sill: a white light strip across the threshold, between the pillars
		box("GateSill", -hw + 0.6, hw - 0.6, 0, 0.14, -0.25, 0.35, K.COL.sill, true).Parent = parent -- (0.14: clear of floor bands and lines, ZFight)
	else
		local lit = style == "lit" or style == "litscan"
		if lit then
			-- a pale back wall and in it a white light panel (inset 0.6 all round), its light thrown out over the threshold
			box("GateBack", -hw, hw, 0, H, 1.15, K.DEPTH, K.COL.litBack).Parent = parent
			local pnl = box("GatePanel", -hw + 0.6, hw - 0.6, 0.6, H - 0.6, 1.08, 1.15, K.COL.panel, true)
			local sl = Instance.new("SurfaceLight")
			sl.Face = Enum.NormalId.Back; sl.Color = Color3.fromRGB(236, 243, 242); sl.Brightness = 1.2; sl.Range = 14; sl.Angle = 100
			sl.Shadows = false; sl.Parent = pnl
			pnl.Parent = parent
		else
			box("GateBack", -hw, hw, 0, H, 1.15, K.DEPTH, K.COL.back).Parent = parent
		end
		-- the sill: a white light strip across the threshold, just proud of the floor
		box("GateSill", -hw, hw, 0, 0.05, -0.25, 0.35, K.COL.sill, true).Parent = parent
		if style == "litscan" then
			local HS = K.HOUSING
			box("ShutterHousing", -HS.x, HS.x, H, H + HS.up, HS.d0, HS.d1, K.COL.housing).Parent = parent
		end
		if style == "scan" or style == "litscan" then
			-- three thin cool-white scan lines across the face; they fade as anyone walks up (Fade), and never block
			lasers = Instance.new("Model")
			lasers.Name = lasersName
			for _, f in { 0.3, 0.55, 0.8 } do -- (0.6 in from each side: the frame's jambs stand in front of the plate's edges)
				local bar = box("LaserBar", -hw + 0.6, hw - 0.6, f * H - 0.05, f * H + 0.05, 0.1, 0.2, K.COL.scan, true, 0.35)
				bar.Shape = Enum.PartType.Cylinder
				bar.Parent = lasers
			end
			lasers:SetAttribute("Center", (F * CFrame.new(0, H / 2, -0.15)).Position)
			lasers:SetAttribute("Near", 18)
			lasers:SetAttribute("Fade", true)
		end
	end
	if lasers then
		lasers.Parent = parent
		CollectionService:AddTag(lasers, "LaserGate")
	end
	return lasers
end

function K.build(F: CFrame, parent: Instance, o: { door: string?, lasers: string?, style: string?, w: number?, h: number? }?)
	local opts = o or {}
	local door = Instance.new("Model")
	door.Name = opts.door or "GateDoor"
	door.Parent = parent
	local lasers = parts(F, parent, door, opts.lasers or "GateLasers", opts.style or K.STYLE, opts.w or K.W, opts.h or K.H)
	return door, lasers
end

-- a gate already built (its door Model: a Shutter with slats, or a look's door with Center and Top) turned into another
-- look where it stands: its F, width and height read off the door (a hub's warp may have stretched them), everything
-- the old look made beside it in its folder taken away, the new look built. returns a line saying what it did
local LOOK_PARTS = { GateBack = true, GatePanel = true, GateSill = true, ShutterHousing = true, GateLightBar = true,
	GatePassageSide = true, GatePassageCeiling = true }
function K.restyle(door: Model, style: string): string
	local parent = door.Parent
	if not parent then return "no parent" end
	local F, W, H
	local low = nil
	for _, s in door:GetChildren() do
		if s:IsA("BasePart") and typeof(s:GetAttribute("Shut")) == "CFrame" and (not low or s:GetAttribute("Shut").Y < low:GetAttribute("Shut").Y) then low = s end
	end
	local top = door:GetAttribute("Top")
	if low then
		local sh = low:GetAttribute("Shut")
		F = sh * CFrame.new(0, -(low.Size.Y / 2 + 0.2 * low.Size.Y / 0.95), 0.8)
		W = low.Size.X
	elseif typeof(door:GetAttribute("F")) == "CFrame" then
		F = door:GetAttribute("F")
		W = door:GetAttribute("W") or K.W
	else
		return door:GetFullName() .. ": no slats and no F, not a GateKit door"
	end
	H = if type(top) == "number" then top - F.Y else K.H
	-- the old look's parts beside it (within the opening's reach of F), and its lasers
	local gone = 0
	for _, d in parent:GetChildren() do
		local near = false
		if d:IsA("BasePart") and LOOK_PARTS[d.Name] then near = (d.Position - F.Position).Magnitude < W + H
		elseif d:IsA("Model") and CollectionService:HasTag(d, "LaserGate") then
			local c = d:GetAttribute("Center")
			near = typeof(c) == "Vector3" and (c - F.Position).Magnitude < W + H
		end
		if near then d:Destroy(); gone += 1 end
	end
	for _, s in door:GetChildren() do s:Destroy() end
	CollectionService:RemoveTag(door, "Shutter")
	for _, a in { "Shutter", "Lift" } do door:SetAttribute(a, nil) end
	local lasersName = if door.Name == "HubShutter" then "HubLaserGate" elseif door.Name == "TrainingShutter" then "TrainingLaserGate" else door.Name .. "Lasers"
	parts(F, parent, door, lasersName, style, W, H)
	door:SetAttribute("F", F); door:SetAttribute("W", W)
	return ("%s: %s (%d old parts away; W %.2f H %.2f)"):format(door:GetFullName(), style, gone, W, H)
end

return K
