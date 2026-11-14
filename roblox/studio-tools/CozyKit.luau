-- edit-time helper for the cozy pass (2026-11-14): places props from ServerStorage.JankfireMeshes through PropPlacer
-- (so nothing overlaps or lands in a doorway / walkway / spawn), adds their invisible collision boxes, wall sconces
-- with a warm glow, and flat floor grates. not used at runtime.
-- usage: local K = require(game.ServerStorage.PolishBackup.CozyKit:Clone()); K.setup(); K.put{...}; print(K.report())
local K = {}
local hub = workspace.Map.Hub
local tg = hub.TrainingGround
local JM = game.ServerStorage.JankfireMeshes
local P = require(script.Parent.PropPlacer:Clone())
local V = Vector3.new
K.P = P
K.made = 0

local FLAT = { Arrow = 1, EdgeLine = 1, Accent = 1, FloorRing = 1, FloorDash = 1, FloorDisc = 1, Carpet = 1, Hazard = 1, BrickSkin = 1,
	DustMotes = 1, HoloBeam = 1, Bunting = 1, Light = 1, Mat = 1, FloorGrate = 1 }

function K.setup()
	P.reset()
	local function collect(folder)
		for _, c in folder:GetChildren() do
			if c:IsA("Folder") then
				if c.Name ~= "Accents" and c.Name ~= "FillLights" then collect(c) end
			elseif (c:IsA("Model") or (c:IsA("BasePart") and c.Transparency < 1)) and not FLAT[c.Name] then
				P.register(c.Name, c)
			end
		end
	end
	collect(hub.Scenery); collect(tg.Scenery)
	for _, pad in hub.QueuePads:GetChildren() do
		if pad:FindFirstChild("PadModel") then P.register("pad " .. pad.Name, pad.PadModel) end
	end
	-- the same keep-out zones OverlapCheck uses (written for Origin z -8000)
	local Z = {
		{ "rotunda N door", V(-7, 240.2, -8008.5), V(7, 257, -8005) }, { "rotunda S door", V(-7, 240.2, -8067), V(7, 257, -8063.5) },
		{ "rotunda W door", V(-30.5, 240.2, -8043), V(-27, 257, -8029) }, { "rotunda E door", V(27, 240.2, -8043), V(30.5, 257, -8029) },
		{ "N hallway", V(-6.4, 240.2, -8005), V(6.4, 249, -7975) }, { "S hallway", V(-8, 240.2, -8085), V(8, 249, -8066) },
		{ "W hallway", V(-59, 240.2, -8040), V(-29, 249, -8032) }, { "E hallway", V(29, 240.2, -8040), V(59, 249, -8032) },
		{ "lounge door", V(-50, 240.2, -8029), V(-40, 249, -8024.5) }, { "depot door", V(-66, 240.2, -8043), V(-58, 249, -8029) },
		{ "gym door", V(58, 240.2, -8043), V(66, 249, -8029) }, { "corridor walkway", V(-12.8, 240.2, -7973), V(12.8, 262, -7882) },
		{ "laser door approach", V(-7, 240.2, -8089), V(7, 254, -8080) }, { "training door approach", V(-9, 240.2, -8132), V(9, 254, -8105.4) },
	}
	for _, z in Z do P.keepOut(z[1], z[2], z[3]) end
	for _, s in hub.HubSpawns:GetChildren() do P.keepOut("HubSpawn", s.Position - V(1.2, 0, 1.2), s.Position + V(1.2, 6, 1.2)) end
	for _, s in hub.TrainSpawns:GetChildren() do P.keepOut("TrainSpawn", s.Position - V(2, 0.5, 2), s.Position + V(2, 6, 2)) end
	for _, s in hub.Doors.HubArrive:GetChildren() do P.keepOut("HubArrive", s.Position - V(1.2, 0, 1.2), s.Position + V(1.2, 6, 1.2)) end
	for _, s in hub.DummySpots:GetChildren() do P.keepOut("DummySpot " .. s.Name, s.Position - V(4, 0, 4), s.Position + V(4, 8, 4)) end
	for _, p in hub.Build:GetChildren() do
		if p.Name == "BalconyPad" then P.keepOut("launch column", p.Position - V(3.6, -0.4, 3.6), p.Position + V(3.6, 20, 3.6)) end
	end
end

local function collisionFolder(parent: Instance): Instance
	return if parent:IsDescendantOf(tg) then tg.PropCollision else hub.Build.PropCollision
end

-- an invisible solid box round a placed model (same flags as the older boxes: collides, bullets hit it)
function K.solid(m: Model, name: string?, shrinkTop: number?)
	local ref = m:FindFirstChildWhichIsA("BasePart", true)
	local rot = if ref then CFrame.fromOrientation(0, math.rad(ref.Orientation.Y), 0) else CFrame.identity
	local old = m.WorldPivot
	m.WorldPivot = CFrame.new(m:GetPivot().Position) * rot
	local cf, sz = m:GetBoundingBox()
	m.WorldPivot = old
	local b = Instance.new("Part")
	b.Name = (name or m.Name) .. "Box"
	b.Anchored = true; b.CanCollide = true; b.CanQuery = true; b.CanTouch = false; b.Transparency = 1; b.CastShadow = false
	local cut = shrinkTop or 0
	b.Size = V(sz.X, sz.Y - cut, sz.Z)
	b.CFrame = cf * CFrame.new(0, -cut / 2, 0)
	b.Parent = collisionFolder(m)
	return b
end

-- o: PropPlacer fields + solid=true (add a collision box), web=true (web-game prop: scale 3 unless o.scale is given)
function K.put(o: any): Model?
	if o.web and not o.scale then o.scale = 3 end
	local m = P.place(o)
	if not m then return nil end
	K.made += 1
	if o.solid then K.solid(m, o.label or o.name) end
	return m
end

-- a warm wall lamp. wall = { axis, face, side } like PropPlacer; along = the other horizontal coordinate; y = centre height
function K.sconce(parent: Instance, wall: any, along: number, y: number, o: any?)
	local yaw = if wall.axis == "x" then (if wall.side > 0 then math.pi / 2 else -math.pi / 2) else (if wall.side > 0 then 0 else math.pi)
	local at = if wall.axis == "x" then V(wall.face, 240, along) else V(along, 240, wall.face)
	local m = P.place({ name = "bc_sconce", at = at, yaw = yaw, wall = wall, lift = y - 240 - 0.8, parent = parent, label = "Sconce" })
	if not m then return nil end
	K.made += 1
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.CastShadow = false
			if d.Material == Enum.Material.Neon then
				local l = Instance.new("PointLight")
				l.Color = (o and o.color) or Color3.fromRGB(255, 196, 128); l.Brightness = (o and o.b) or 1.1; l.Range = (o and o.range) or 15; l.Shadows = false
				l.Parent = d
				if o and o.color then d.Color = o.color end
			end
		end
	end
	return m
end

-- a flat purple-edged floor grate (look only, never blocks anything)
function K.grate(parent: Instance, x: number, z: number, yaw: number?, floorY: number?)
	local m = JM.bc_floorgrate:Clone()
	m.Name = "FloorGrate"
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end end
	local cf, sz = m:GetBoundingBox()
	m:PivotTo(CFrame.new(x, (floorY or 240) + sz.Y / 2 + 0.03, z) * CFrame.Angles(0, yaw or 0, 0) * (cf:Inverse() * m:GetPivot()))
	m.Parent = parent
	K.made += 1
	return m
end

function K.report(): string
	return K.made .. " placed\n" .. table.concat(P.log, "\n")
end

return K
