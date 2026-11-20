-- BATH DUCKY finisher animatic, round 5 (20 Nov 2026): round 4 (the giant clawfoot tub of real Terrain water, the grand
-- bathroom in the late sun, the Spider-Verse duck: ink outline, motion on twos) made slower, with the owner's new beats
-- (the held look and the head snap, the door, the walk in, the look, the awkward hold in the air) and the water as real
-- particles with gravity instead of parts; see the round-5 section below. Built on bath_ducky_board3.luau (round 4).
-- Run as an uploaded ModuleScript (require it); it defines shared.BD4: build(), panel(n), frame(i), clear(), CAM, PLAN.
-- Everything is temporary: the stage, the Terrain water and the camera's colour grade are removed by clear().
local BD = {}
shared.BD4 = BD

local O = Vector3.new(-9400, 800, -8600) -- the floor of the set, far off every map
local IDS = { giant = 85544912707294, duck = 116208755186622, tub = 107087577101161 } -- bd2_giant, bd2_duck, bd3_tub
BD.IDS = IDS
local ANIM = {
	idle = 507766666, point = 507770453, sit = 2506281703, -- Roblox's own R15 idle, point and sit
	look = 77808638913840, -- victim_lookaround_t2: standing, looking round (FinisherScene's)
	pulled = 122059547987683, -- yanked backwards off the feet, arms reaching forward (Warp Out's victim clip)
}

local InsertService = game:GetService("InsertService")
local KSP = game:GetService("KeyframeSequenceProvider")
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")

local function rgb(r, g, b) return Color3.fromRGB(r, g, b) end
local C = {
	skin = rgb(232, 186, 150), trunks = rgb(75, 155, 224), foam = rgb(246, 246, 242),
	vSkin = rgb(176, 128, 96), vTop = rgb(72, 70, 82), vLegs = rgb(46, 58, 88),
	water = rgb(104, 186, 228), splash = rgb(160, 214, 242), tile = rgb(200, 218, 214), poolTile = rgb(120, 190, 214),
	plaster = rgb(240, 234, 224), floor = rgb(228, 222, 212), coping = rgb(244, 242, 236), wood = rgb(176, 132, 92),
	door = rgb(150, 112, 80), hall = rgb(255, 248, 232), ray = rgb(255, 214, 140), towel = rgb(75, 155, 224),
	pot = rgb(214, 196, 170), leaf = rgb(96, 140, 92), leaf2 = rgb(120, 160, 104), gold = rgb(217, 173, 69), mat = rgb(150, 196, 226),
	candle = rgb(240, 232, 210), flame = rgb(255, 190, 90),
}

local root, dyn, T, POSE, J = nil, nil, {}, {}, nil
local SIZES = {}
local WATER = 7.0 -- the tub's water surface (Terrain water from the tub's floor at 1.8: deep)
local ROOM = { x0 = -56, x1 = 46, z0 = -38, z1 = 38, h = 46 }
local TUB = { x = -12, z = -2, hx = 19.7, hz = 11.7, r = 7.7, floor = 1.8 } -- the inside of bd3_tub (42 x 26, wall 1.3)
local SEAT_TOP = 3.6 -- a hidden step inside the tub's east end: you stand on it chest-deep
local DOOR = { x = 46, z0 = -4, z1 = 2, h = 10 }

local function L(x, y, z) return O + Vector3.new(x, y, z) end

local function part(size, cf, colour, opts)
	opts = opts or {}
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	if opts.shape then p.Shape = opts.shape end
	p.Material = opts.mat or Enum.Material.SmoothPlastic -- (Glass jets read as grey pipes in round 4's first cut)
	p.Size, p.CFrame, p.Color = size, cf, colour
	p.Transparency = opts.tr or 0
	p.Reflectance = opts.refl or 0
	p.CastShadow = opts.shadow ~= false
	p.Name = opts.name or "bd"
	p.Parent = opts.parent or dyn
	return p
end
local function box(x0, y0, z0, x1, y1, z1, colour, opts) -- a block between two corners (stage coords)
	return part(Vector3.new(x1 - x0, y1 - y0, z1 - z0), CFrame.new(L((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), colour, opts)
end
local function ball(pos, r, colour, opts)
	opts = opts or {}
	opts.shape = Enum.PartType.Ball
	return part(Vector3.new(r * 2, r * 2, r * 2), CFrame.new(pos), colour, opts)
end
local function rod(a, b, r, colour, opts)
	opts = opts or {}
	opts.shape = Enum.PartType.Cylinder
	return part(Vector3.new((b - a).Magnitude, r * 2, r * 2), CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), colour, opts)
end

local function loadModel(id, name)
	local a = InsertService:LoadAsset(id)
	local m = Instance.new("Model")
	m.Name = name
	for _, d in a:GetDescendants() do
		if d:IsA("MeshPart") then
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch = true, false, false, false
			d.Material = Enum.Material.SmoothPlastic
			d.Reflectance = 0.06 -- (glossy rubber)
			d.Color = Color3.new(1, 1, 1) -- the vertex colours carry the paint
			d.Parent = m
		end
	end
	a:Destroy()
	local cf, size = m:GetBoundingBox()
	m.WorldPivot = CFrame.new(cf.Position - Vector3.new(0, size.Y / 2, 0)) -- the bottom, facing -Z (the duck's front)
	return m
end

-- ------------------------------------------------------------------ rigs and poses
local function newRig(kind)
	local rig = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
	rig.Name = kind == "victim" and "Opponent" or "Player"
	local hum = rig:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	for _, d in rig:GetChildren() do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("BodyColors") then d:Destroy() end
	end
	for _, d in rig:GetChildren() do
		if d:IsA("BasePart") then
			local n = d.Name
			if kind == "victim" then
				d.Color = (n:find("Torso") or n:find("Arm")) and C.vTop or (n:find("Leg") or n:find("Foot")) and C.vLegs or C.vSkin
				if n == "LowerTorso" then d.Color = C.vLegs end
			else -- in the pool: swim trunks
				d.Color = (n == "LowerTorso" or n:find("UpperLeg")) and C.trunks or C.skin
			end
		end
	end
	return rig
end

local function joints(rig)
	local out = {}
	for _, d in rig:GetDescendants() do
		if d:IsA("Motor6D") and d.Part0 and d.Part1 then
			out[d.Part1.Name] = { p0 = d.Part0.Name, c0 = d.C0, c1 = d.C1 }
		elseif d:IsA("AnimationConstraint") and d.Attachment0 and d.Attachment1 then
			out[d.Attachment1.Parent.Name] = { p0 = d.Attachment0.Parent.Name, c0 = d.Attachment0.CFrame, c1 = d.Attachment1.CFrame }
		end
	end
	return out
end

local function fk(map, rootCF)
	local out = { HumanoidRootPart = rootCF }
	local function go(n)
		if out[n] then return out[n] end
		local j = J[n]
		if not j then return nil end
		local p0 = go(j.p0)
		if not p0 then return nil end
		local cf = p0 * j.c0 * (map[n] or CFrame.identity) * j.c1:Inverse()
		out[n] = cf
		return cf
	end
	for n in J do go(n) end
	return out
end

-- one keyframe of a real clip, picked by score(fk result) (highest wins; no score = the first keyframe)
local function pickPose(name, score)
	local ks = KSP:GetKeyframeSequenceAsync("rbxassetid://" .. ANIM[name])
	local kfs = ks:GetKeyframes()
	table.sort(kfs, function(a, b) return a.Time < b.Time end)
	local best, bestS, bestT = nil, -math.huge, 0
	for _, kf in kfs do
		local map = {}
		for _, p in kf:GetDescendants() do
			if p:IsA("Pose") then map[p.Name] = p.CFrame end
		end
		local s = score and score(fk(map, CFrame.identity), kf.Time, kfs[#kfs].Time) or -kf.Time
		if s > bestS then best, bestS, bestT = map, s, kf.Time end
	end
	return best, bestT, kfs[#kfs].Time
end

local function pose(rig, map, pos, yaw, opts)
	opts = opts or {}
	local rootCF = CFrame.new(pos) * CFrame.Angles(0, yaw or 0, 0) * CFrame.Angles(opts.tilt or 0, 0, 0)
	local cfs = fk(map, rootCF)
	local shift = Vector3.zero
	if opts.ground then
		local low = math.huge
		for _, n in { "LeftFoot", "RightFoot" } do low = math.min(low, cfs[n].Position.Y - SIZES[n].Y / 2) end
		shift = Vector3.new(0, opts.ground - low, 0)
	elseif opts.hips then
		shift = Vector3.new(0, opts.hips - cfs.LowerTorso.Position.Y, 0)
	end
	for _, d in rig:GetDescendants() do
		if d:IsA("Motor6D") or d:IsA("AnimationConstraint") or d:IsA("Weld") or d:IsA("WeldConstraint") then d:Destroy() end
	end
	for n, cf in cfs do
		local p = rig:FindFirstChild(n)
		if p and p:IsA("BasePart") then p.Anchored, p.CanCollide = true, false; p.CFrame = cf + shift end
	end
	rig.HumanoidRootPart.Transparency = 1
	rig.Parent = dyn
	return rig
end

-- the dynamic head's own expressions (FaceControls)
local EXPR = {
	closed = { LeftEyeClosed = 1, RightEyeClosed = 1, LeftLipCornerPuller = 0.55, RightLipCornerPuller = 0.55, LeftCheekRaiser = 0.3, RightCheekRaiser = 0.3 },
	shout = { JawDrop = 0.75, LeftEyeUpperLidRaiser = 1, RightEyeUpperLidRaiser = 1, LeftInnerBrowRaiser = 1, RightInnerBrowRaiser = 1, EyesLookUp = 1 },
	stern = { LeftBrowLowerer = 1, RightBrowLowerer = 1, LeftEyeClosed = 0.3, RightEyeClosed = 0.3, LipsTogether = 0.6, LeftLipCornerDown = 0.3, RightLipCornerDown = 0.3 },
	puzzled = { LeftInnerBrowRaiser = 0.8, RightOuterBrowRaiser = 0.6, JawDrop = 0.15, EyesLookLeft = 0.4 },
	drenched = { LeftEyeClosed = 1, RightEyeClosed = 1, JawDrop = 0.6, LeftLipStretcher = 0.7, RightLipStretcher = 0.7, LeftBrowLowerer = 0.6, RightBrowLowerer = 0.6 },
}
local function face(rig, kind)
	local fc = rig.Head:FindFirstChildOfClass("FaceControls")
	if not fc then return end
	for k, v in EXPR[kind] or {} do pcall(function() fc[k] = v end) end
end

local function foamHair(rig)
	local h, s = rig.Head.CFrame, rig.Head.Size.Y
	for _, b in { { 0, 0.62, 0.05, 0.42 }, { -0.36, 0.5, 0.05, 0.32 }, { 0.36, 0.5, 0.05, 0.32 }, { 0, 0.5, 0.36, 0.34 },
		{ -0.2, 0.78, 0.2, 0.28 }, { 0.22, 0.74, -0.15, 0.27 }, { -0.25, 0.55, -0.3, 0.26 }, { 0.3, 0.52, 0.32, 0.25 } } do
		ball((h * CFrame.new(b[1] * s, b[2] * s, b[3] * s)).Position, b[4] * s, C.foam, { parent = rig })
	end
	local d = T.duck:Clone()
	d:ScaleTo(d:GetScale() * 0.55 / 1.6) -- (the stage duck is 1.6 tall: this one 0.55)
	d:PivotTo(h * CFrame.new(0, 0.98 * s, 0.05))
	d.Parent = rig
end

-- the skin in the hand: the Royal Duck Sniper (20 Nov, the owner: the special cutscene belongs to one gun in the set,
-- "maybe the ducky sniper"; Finishers.splashdown lists only sniper_ducky_tripo); a small rubber duck if it is missing
local HELD_SKIN = "sniper_ducky_tripo"
local function gunInHand(rig)
	local skins = RS:FindFirstChild("JankfireSkins")
	local tpl = skins and skins:FindFirstChild(HELD_SKIN)
	local hand, lower = rig.RightHand, rig.RightLowerArm
	local dir = (hand.Position - lower.Position).Unit
	local at = hand.Position + dir * 0.15
	if tpl then
		-- a kit gun is in metres in its file frame (FileFrame: the origin is the hand, the barrel runs along -Z, no
		-- attachments): every piece x3 about the origin (as FinisherScene does the katana), the origin on the hand
		local g = tpl:Clone()
		local want = CFrame.lookAt(at, at + dir, Vector3.yAxis)
		for _, d in g:GetDescendants() do
			if d:IsA("BasePart") then
				local oc = d.CFrame
				d.Anchored = true; d.CanCollide = false; d.CastShadow = false
				d.Size *= 3
				d.CFrame = want * CFrame.new(oc.Position * 3) * oc.Rotation
			elseif d:IsA("BaseScript") or d:IsA("JointInstance") or d:IsA("Constraint") then
				d:Destroy()
			end
		end
		g.Parent = rig
		local hi, lo = tpl:GetAttribute("FileHi"), tpl:GetAttribute("FileLo")
		local tip = Vector3.new(0, (typeof(hi) == "Vector3" and hi.Y or 0.06) * 0.5, (typeof(lo) == "Vector3" and lo.Z or -0.27)) * 3
		return want * tip, HELD_SKIN
	end
	local d = T.duck:Clone()
	d:ScaleTo(d:GetScale() * 0.9 / 1.6)
	d:PivotTo(CFrame.lookAt(at, at + Vector3.new(dir.X, 0, dir.Z)))
	d.Parent = rig
	return at + dir * 0.6 + Vector3.new(0, 0.5, 0), "toy duck"
end

-- ------------------------------------------------------------------ ducks and water
local function scaleBy(m, k) m:ScaleTo(m:GetScale() * k) end

local function duck(kind, pos, facing, opts)
	opts = opts or {}
	local m = T[kind]:Clone()
	if opts.scale then scaleBy(m, opts.scale) end
	local look = Vector3.new(facing.X, 0, facing.Z).Unit
	m:PivotTo(CFrame.lookAt(pos, pos + look) * CFrame.Angles(opts.pitch or 0, 0, opts.roll or 0))
	m.Parent = dyn
	return m
end
-- the beak's tip: the front-most point of the model at the beak's height (measured on the mesh box once per model)
local function beakOf(m)
	local cf, size = m:GetBoundingBox()
	local piv = m:GetPivot()
	return piv * Vector3.new(0, size.Y * 0.57, -size.Z * 0.5) -- (giant take 80995e0c: the beak at 0.57 of the height, its tip the front-most point)
end

local function jet(a, b, r)
	rod(a, b, r, C.splash, { tr = 0.25, shadow = false })
	local dir = (b - a).Unit
	for i = 1, 14 do
		local u = i / 14
		local p = a + (b - a) * u + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * r * 2.2
		ball(p, r * (0.25 + math.random() * 0.4), C.splash, { tr = 0.2, shadow = false })
	end
	return dir
end

local function splashAt(c, radius, height, n)
	for i = 0, n - 1 do -- a crown of water: arcs of balls thrown out and up
		local a = i / n * math.pi * 2 + math.random() * 0.2
		local dir = Vector3.new(math.cos(a), 0, math.sin(a))
		for k = 0, 4 do
			local u = k / 4
			ball(c + dir * (radius + u * radius * 0.5) + Vector3.new(0, height * (u * 1.4 - u * u), 0),
				(radius * 0.16) * (1 - u * 0.6), C.splash, { tr = 0.18, shadow = false })
		end
	end
	for _ = 1, n * 3 do
		local a = math.random() * math.pi * 2
		local d = radius * (0.6 + math.random() * 1.2)
		ball(c + Vector3.new(math.cos(a) * d, math.random() * height * 1.6, math.sin(a) * d), radius * (0.02 + math.random() * 0.05), C.splash, { tr = 0.15, shadow = false })
	end
end

local function foamPile(centre, radius, n, rmin, rmax)
	for i = 1, n do
		local a = i * 2.39996
		local d = radius * math.sqrt(i / n)
		ball(centre + Vector3.new(math.cos(a) * d, (math.random() - 0.3) * 0.3, math.sin(a) * d), rmin + math.random() * (rmax - rmin), C.foam)
	end
end

-- ------------------------------------------------------------------ the pool room (static)
local function room()
	-- round 4 (20 Nov), the owner: "that's a pool not a tub! The water also has to be deeper?.. make the scene look
	-- prettier", and "Can the water be actual water and have lighting shadows?". A grand bathroom: a giant clawfoot tub
	-- (bd3_tub) full of real Terrain water, tall windows on the west wall where the late sun is (the saved Lighting's sun is
	-- low in the -X), so long warm shafts and window shadows fall across the room; marble, pale tiles, plants, gold.
	local R = { parent = root }
	local tiles = { parent = root, mat = Enum.Material.CeramicTiles }
	local plaster = { parent = root, mat = Enum.Material.Plaster }
	local marble = { parent = root, mat = Enum.Material.Marble }
	box(ROOM.x0, -1, ROOM.z0, ROOM.x1 + 10, 0, ROOM.z1, C.floor, marble)
	box(ROOM.x0 - 1, ROOM.h, ROOM.z0 - 1, ROOM.x1 + 1, ROOM.h + 1, ROOM.z1 + 1, C.plaster, plaster) -- ceiling
	local function wall(x0, z0, x1, z1, top)
		box(x0, 0, z0, x1, math.min(14, top or ROOM.h), z1, C.tile, tiles)
		if (top or ROOM.h) > 14 then box(x0, 14, z0, x1, top or ROOM.h, z1, C.plaster, plaster) end
	end
	wall(ROOM.x0, ROOM.z0 - 1, ROOM.x1, ROOM.z0) -- back
	wall(ROOM.x0, ROOM.z1, ROOM.x1, ROOM.z1 + 1) -- front
	-- the west wall: three tall arched-top windows (open: the sun comes straight in), white frames and a cross of mullions
	local wx = ROOM.x0
	local spans = { { ROOM.z0, -27 }, { -15, -9 }, { 3, 9 }, { 21, ROOM.z1 } }
	for _, sp in spans do wall(wx - 1, sp[1], wx, sp[2]) end
	for _, wz in { { -27, -15 }, { -9, 3 }, { 9, 21 } } do
		box(wx - 1, 0, wz[1], wx, 4, wz[2], C.tile, tiles) -- sill wall
		box(wx - 1, 32, wz[1], wx, ROOM.h, wz[2], C.plaster, plaster) -- over the window
		local mid = (wz[1] + wz[2]) / 2
		box(wx - 1.2, 4, wz[1], wx + 0.3, 4.6, wz[2], C.coping, R) -- sill
		box(wx - 1.1, 31.4, wz[1], wx + 0.2, 32, wz[2], C.coping, R)
		box(wx - 1.1, 4, mid - 0.35, wx + 0.2, 32, mid + 0.35, C.coping, R) -- mullion
		box(wx - 1.1, 17.6, wz[1], wx + 0.2, 18.3, wz[2], C.coping, R) -- transom
		box(wx - 1.1, 4, wz[1], wx + 0.2, 32, wz[1] + 0.5, C.coping, R)
		box(wx - 1.1, 4, wz[2] - 0.5, wx + 0.2, 32, wz[2], C.coping, R)
	end
	-- the east wall with the door, the lit hall behind it
	local ex = ROOM.x1
	wall(ex, ROOM.z0, ex + 1, DOOR.z0)
	wall(ex, DOOR.z1, ex + 1, ROOM.z1)
	box(ex, DOOR.h, DOOR.z0, ex + 1, 14, DOOR.z1, C.tile, tiles)
	box(ex, 14, DOOR.z0, ex + 1, ROOM.h, DOOR.z1, C.plaster, plaster)
	box(ex - 0.4, 0, DOOR.z0 - 0.6, ex + 1.4, DOOR.h + 0.6, DOOR.z0, C.coping, R)
	box(ex - 0.4, 0, DOOR.z1, ex + 1.4, DOOR.h + 0.6, DOOR.z1 + 0.6, C.coping, R)
	box(ex - 0.4, DOOR.h, DOOR.z0, ex + 1.4, DOOR.h + 0.6, DOOR.z1, C.coping, R)
	part(Vector3.new(0.4, DOOR.h - 0.2, DOOR.z1 - DOOR.z0), CFrame.new(L(ex + 1, (DOOR.h - 0.2) / 2, DOOR.z1)) * CFrame.Angles(0, math.rad(-70), 0)
		* CFrame.new(0, 0, -(DOOR.z1 - DOOR.z0) / 2), C.door, R)
	box(ex + 1, 0, -9, ex + 10, 14, -8, C.plaster, plaster)
	box(ex + 1, 0, 6, ex + 10, 14, 7, C.plaster, plaster)
	box(ex + 1, 14, -9, ex + 10, 15, 7, C.plaster, plaster)
	local hall = box(ex + 9, 0, -8, ex + 10, 14, 6, C.hall, { parent = root, mat = Enum.Material.Neon })
	local hl = Instance.new("PointLight"); hl.Range = 22; hl.Brightness = 2; hl.Color = rgb(255, 240, 210); hl.Parent = hall
	-- a warm low light over the room (the sun does the rest), with shadows
	for _, p in { { -12, -2 }, { 22, -2 } } do
		local lamp = box(p[1] - 5, ROOM.h - 0.3, p[2] - 3, p[1] + 5, ROOM.h, p[2] + 3, Color3.new(1, 1, 1), { parent = root, mat = Enum.Material.Neon })
		local sl = Instance.new("SurfaceLight"); sl.Face = Enum.NormalId.Bottom; sl.Range = 50; sl.Brightness = 0.35; sl.Angle = 110
		sl.Color = rgb(255, 236, 214); sl.Shadows = true; sl.Parent = lamp
	end
	-- plants by the windows, a towel rail, a round mat, a bench by the door, candles on the tub's step
	for _, pz in { -30, -12, 6, 24 } do
		local x = ROOM.x0 + 4
		part(Vector3.new(3.2, 3.6, 3.6), CFrame.new(L(x, 1.6, pz)) * CFrame.Angles(0, 0, math.pi / 2), C.pot, { parent = root, shape = Enum.PartType.Cylinder })
		for k, b in { { 0, 5.2, 0, 2.6 }, { 1.4, 6.6, 0.8, 2.0 }, { -1.2, 6.4, -0.9, 2.1 }, { 0.3, 7.8, -0.2, 1.6 } } do
			ball(L(x + b[1], b[2], pz + b[3]), b[4], k % 2 == 0 and C.leaf or C.leaf2, { parent = root })
		end
	end
	box(30, 7, ROOM.z0 + 0.2, 38, 7.4, ROOM.z0 + 0.8, C.gold, R)
	box(30.6, 2.6, ROOM.z0 + 0.3, 33.6, 7, ROOM.z0 + 0.9, C.towel, R)
	box(34.4, 3.2, ROOM.z0 + 0.3, 37.4, 7, ROOM.z0 + 0.9, C.coping, R)
	part(Vector3.new(0.2, 14, 14), CFrame.new(L(24, 0.1, -2)) * CFrame.Angles(0, 0, math.pi / 2), C.mat, { parent = root, shape = Enum.PartType.Cylinder })
	box(28, 0, 14, 40, 1.8, 17, C.wood, R)
	for _, c in { { 12, 2.2, 13 }, { 13.6, 1.6, 14.4 }, { 11.2, 2.8, 15 } } do
		part(Vector3.new(c[2], 1.0, 1.0), CFrame.new(L(c[1], c[2] / 2, c[3])) * CFrame.Angles(0, 0, math.pi / 2), C.candle, { parent = root, shape = Enum.PartType.Cylinder })
		local f = part(Vector3.new(0.3, 0.55, 0.3), CFrame.new(L(c[1], c[2] + 0.35, c[3])), C.flame, { parent = root, mat = Enum.Material.Neon, shadow = false })
		local fl = Instance.new("PointLight"); fl.Range = 10; fl.Brightness = 0.8; fl.Color = rgb(255, 196, 120); fl.Parent = f
	end
	-- the tub, the hidden step inside its east end, and the water: real Terrain water shaped to the tub's inside
	local tub = T.tub:Clone()
	tub:PivotTo(CFrame.new(L(TUB.x, 0, TUB.z)) * CFrame.Angles(0, math.pi, 0)) -- (the tap at the west end, behind the duck)
	tub.Parent = root
	box(TUB.x + TUB.hx - 4.6, TUB.floor, TUB.z - 4, TUB.x + TUB.hx - 0.2, SEAT_TOP, TUB.z + 4, C.coping, R)
	BD.fillWater(Enum.Material.Water)
end

-- the tub's inside as a rounded rectangle of Terrain water (two blocks and four corner cylinders), from 4 up to WATER
-- (3 deep: chest-high where you stand); Air clears it again (BD.clear). The edges sit a little inside the enamel.
function BD.fillWater(mat)
	local t = workspace.Terrain
	local hx, hz, r = TUB.hx - 0.3, TUB.hz - 0.3, TUB.r - 0.3
	local y0, y1 = 4.0, WATER -- (from a voxel boundary: Terrain is 4-stud voxels, and a lower start spills under the tub)
	local h = y1 - y0
	local c = L(TUB.x, (y0 + y1) / 2, TUB.z)
	if mat == Enum.Material.Air then
		t:FillBlock(CFrame.new(L(TUB.x, 3.5, TUB.z)), Vector3.new(hx * 2 + 12, 19, hz * 2 + 12), mat)
		return
	end
	t:FillBlock(CFrame.new(c), Vector3.new(hx * 2, h, (hz - r) * 2), mat)
	t:FillBlock(CFrame.new(c), Vector3.new((hx - r) * 2, h, hz * 2), mat)
	for _, sx in { -1, 1 } do
		for _, sz in { -1, 1 } do
			t:FillCylinder(CFrame.new(c + Vector3.new(sx * (hx - r), 0, sz * (hz - r))), h, r, mat)
		end
	end
end

-- ------------------------------------------------------------------ the camera (a 16:9 band of the viewport keeps `fov`)
local saved
local function shot(c)
	local cam = workspace.CurrentCamera
	saved = saved or { cam.CFrame, cam.FieldOfView }
	cam.CameraType = Enum.CameraType.Scriptable
	local vs = cam.ViewportSize
	cam.FieldOfView = math.deg(2 * math.atan(math.tan(math.rad(c[3]) / 2) * vs.Y / (vs.X * 9 / 16)))
	cam.CFrame = CFrame.lookAt(L(c[1][1], c[1][2], c[1][3]), L(c[2][1], c[2][2], c[2][3])) * CFrame.Angles(0, 0, math.rad(c[4] or 0))
end

-- each shot's lens: eye, look-at (stage coords), FOV of the 16:9 band, roll (deg)
BD.CAM = {
	[1] = { { 7.5, 7.6, 3 }, { -15, 18, -2 }, 64, -4 }, -- THE RISE: low on the water behind you, looking up past you
	[2] = { { 6.2, 9.8, -1.5 }, { 44, 4.6, -1 }, 26, 0 }, -- THE OPPONENT: the lens swings to the door
	[3] = { { 17, 10.6, 4 }, { -8, 16, -2 }, 60, 0 }, -- YOU AND THE DUCKY: back to them, from the door side
	-- round 6 (20 Nov), the owner: "the overhead shot needs to be closer in": both high shots come in (were
	-- { { -8, 26, 35 }, { 14, 6, -4 }, 60 } and { { -22, 21, 11 }, { 40, 4, -1.5 }, 52 })
	[4] = { { 8, 18, 24 }, { 10, 6, -3 }, 70, 0 }, -- THE STANDOFF: high over the near side, you and the duck to the door
	[5] = { { -6, 18, 20 }, { -2, 12, -2 }, 64, 0 }, -- THE SPRAY: high and close on you and the duck firing
	[6] = { { 37.5, 2.6, -6.5 }, { 43.5, 4.0, -1 }, 50, -3 }, -- SOAKED: on the opponent as the jets hit
	-- the opening (played before shot 1)
	[7] = { { -4, 10.2, -4.5 }, { 5.4, 8.2, -2 }, 46, 0 }, -- CALM: in front of you, low over the water
	[8] = { { 8.2, 10.8, 0.4 }, { -10, 6.2, -2 }, 58, 0 }, -- THE SHADOW: just behind and above your head, down the tub
	[9] = { { -8, 19, 31 }, { -14, 8, -2 }, 52, 0 }, -- IT EMERGES: wide on the tub from the near side
	[10] = { { -1.5, 7.6, -1 }, { -10.8, 8.6, -2 }, 46, 4 }, -- THE EYES: low at the water line, close on the face
}

-- ------------------------------------------------------------------ the shots
local P = {}
local PLAYER_AT = Vector3.new(4.6, SEAT_TOP, -2)
local DUCK_AT = Vector3.new(-17, 0, -2)
local OPP_AT = Vector3.new(43.5, 0, -1)
local GIANT_H = 22

local function giant(y)
	local g = duck("giant", L(DUCK_AT.X, y, DUCK_AT.Z), Vector3.new(1, 0, 0))
	-- Spider-Verse: an ink outline round the duck (its motion is stepped on twos in the animatic)
	local h = Instance.new("Highlight")
	h.FillTransparency = 1; h.OutlineTransparency = 0; h.OutlineColor = Color3.fromRGB(26, 20, 30)
	h.DepthMode = Enum.HighlightDepthMode.Occluded
	h.Parent = g
	return g
end
local function floaters()
	for _, d in { { -28, -9, 0.6 }, { -6, 7.5, -0.4 }, { 1, -9.5, 2.2 }, { -10, -10.5, 1.2 }, { 3, 6.5, -2.4 }, { -29, 6, 0.2 } } do
		duck("duck", L(d[1], WATER - 0.45, d[2]), Vector3.new(math.cos(d[3]), 0, math.sin(d[3])))
	end
end
local function player(map, yaw, expr, opts)
	local p = newRig("player")
	pose(p, map, L(PLAYER_AT.X, 0, PLAYER_AT.Z), yaw, { ground = O.Y + SEAT_TOP, tilt = opts and opts.tilt })
	foamHair(p)
	face(p, expr)
	foamPile(L(PLAYER_AT.X, WATER, PLAYER_AT.Z), 2.2, 12, 0.3, 0.6)
	return p
end
local function opponent(map, expr, opts)
	local v = newRig("victim")
	pose(v, map, L(OPP_AT.X, 0, OPP_AT.Z), math.pi / 2, { ground = O.Y, tilt = opts and opts.tilt }) -- facing the pool (-X)
	-- the victim clips carry their own root turn (the pulled take faces 90 deg off): turn the body in place until the
	-- chest faces the pool (-X)
	local lv = v.UpperTorso.CFrame.LookVector
	local turn = math.atan2(-lv.X, -lv.Z) - math.atan2(1, 0)
	local c = v.UpperTorso.Position
	local rot = CFrame.new(c) * CFrame.Angles(0, -turn, 0) * CFrame.new(-c)
	for _, d in v:GetDescendants() do
		if d:IsA("BasePart") then d.CFrame = rot * d.CFrame end
	end
	face(v, expr)
	return v
end

P[1] = function() -- the rise: the giant erupts like a kaiju, seen from the water past the player
	player(POSE.idle, math.pi / 2, "shout", { tilt = 0.12 }) -- facing the duck (-X: +90 deg of yaw), leaning back to look up
	local g = giant(WATER - 5.4)
	splashAt(L(DUCK_AT.X, WATER, DUCK_AT.Z), 10, 12, 18)
	foamPile(L(DUCK_AT.X + 6, WATER, DUCK_AT.Z), 7, 30, 0.5, 1.2)
	for _, b in dyn:GetChildren() do -- keep the duck's face clear: no splash in front of it above the water
		if b:IsA("Part") and b.Shape == Enum.PartType.Ball and b.Transparency > 0.1 then
			local q = b.Position - O
			if q.X > DUCK_AT.X + 5 and q.Y > WATER + 1.1 then b:Destroy() end
		end
	end
	floaters()
	local head = L(DUCK_AT.X - 2, WATER + 19.6, DUCK_AT.Z)
	for i = -4, 4 do
		local a = i * 0.26
		local dir = Vector3.new(-0.2, math.cos(a), math.sin(a)).Unit
		part(Vector3.new(0.12, 60, 1.2), CFrame.lookAt(head, head + Vector3.new(1, 0, 0), dir) * CFrame.new(0, 30, 0),
			C.ray, { mat = Enum.Material.Neon, tr = 0.9, shadow = false })
	end
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[1])
end

P[2] = function() -- the pan: the opponent stands in the doorway
	player(POSE.idle, -math.pi / 2, "stern")
	giant(WATER - 3.4)
	floaters()
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[2])
end

local function together(expr)
	player(POSE.idle, -math.pi / 2, expr) -- facing the door (+X: -90 deg of yaw)
	giant(WATER - 3.4)
	floaters()
end

P[3] = function() -- back to you and the ducky: both staring at the door
	together("stern")
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[3])
end

P[4] = function() -- the standoff, wide
	together("stern")
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[4])
end

local function spray(drench)
	local p = newRig("player")
	pose(p, POSE.point, L(PLAYER_AT.X, 0, PLAYER_AT.Z), -math.pi / 2, { ground = O.Y + SEAT_TOP })
	foamHair(p)
	face(p, "stern")
	foamPile(L(PLAYER_AT.X, WATER, PLAYER_AT.Z), 2.2, 12, 0.3, 0.6)
	local muzzle, held = gunInHand(p)
	local g = giant(WATER - 3.4)
	floaters()
	local v = opponent(drench and POSE.pulled or POSE.look, drench and "drenched" or "puzzled", { })
	local chest = v.UpperTorso.Position
	jet(beakOf(g), chest + Vector3.new(-0.3, 0.2, 0.4), 0.9)
	jet(muzzle, chest + Vector3.new(-0.3, -0.3, -0.3), 0.3)
	if drench then
		splashAt(chest - Vector3.new(0.8, 0, 0), 1.6, 2.2, 14)
		part(Vector3.new(0.12, 7, 7), CFrame.new(L(OPP_AT.X - 2, 0.06, OPP_AT.Z)) * CFrame.Angles(0, 0, math.pi / 2), C.splash,
			{ shape = Enum.PartType.Cylinder, tr = 0.4, shadow = false }) -- the puddle
	end
	return held
end

P[5] = function() -- the spray: you and the ducky soak him
	BD.held = spray(false)
	shot(BD.CAM[5])
end

P[6] = function() -- soaked: the jets hit, he is knocked back
	BD.held = spray(true)
	shot(BD.CAM[6])
end

-- ------------------------------------------------------------------ the opening (the owner's sketch, 20 Nov)
-- "I want a shot of the pool with the shadow in it like over the head and behind, and it emerges then blame that the
-- rise shot and them everything folows your story board", then "maybe a shot focus on it emerging from the water with
-- anime flare lines from the eyes". The sheet plays them before shot 1: CALM, SHADOW, EMERGE, EYES, then the rise.
local RELAX_AT = Vector3.new(5.4, 0, -2) -- leaning back against the tub's east end, facing the length of it (-X)
local EYE = Vector3.new(0.124, 0.679, -0.282) -- the giant's eyes in its own frame, per unit of height (measured)

local function relaxer(expr)
	local p = newRig("player")
	pose(p, POSE.sit, L(RELAX_AT.X, 0, RELAX_AT.Z), math.pi / 2, { tilt = 0.45, hips = O.Y + WATER - 2.0 })
	foamHair(p)
	face(p, expr)
	foamPile(L(RELAX_AT.X - 0.6, WATER, RELAX_AT.Z), 2.6, 16, 0.3, 0.7)
	return p
end

local function setWater(colour, tr) end -- (the water is Terrain now: its look is the place's own, the v3 pool water)

-- water running off a dome: thin sheets down its sides, drops, and foam rings spreading on the surface
local function pour(centre, radius, top, n)
	for i = 0, n - 1 do
		local a = i / n * math.pi * 2 + math.random() * 0.3
		local d = Vector3.new(math.cos(a), 0, math.sin(a))
		local p0 = centre + d * radius * 0.55 + Vector3.new(0, top - centre.Y - radius * 0.25, 0)
		local p1 = centre + d * radius * 1.02
		rod(p0, p1, 0.12 + math.random() * 0.12, C.splash, { tr = 0.3, shadow = false })
		for k = 1, 3 do
			ball(p1 + Vector3.new(0, math.random() * 2, 0) + d * math.random() * 0.8, 0.08 + math.random() * 0.12, C.splash, { tr = 0.2, shadow = false })
		end
	end
	for ring = 1, 3 do
		local r = radius * (1.1 + ring * 0.35)
		for i = 0, 27 do
			local a = i / 28 * math.pi * 2
			ball(centre + Vector3.new(math.cos(a) * r, 0, math.sin(a) * r), 0.25 + 0.1 * (3 - ring), C.foam, { tr = 0.25 * ring, shadow = false })
		end
	end
end

-- anime flare lines off an eye: a white glint and thin light streaks, warm white with one gold line (quiet palette)
local function flare(at, toward)
	ball(at, 0.45, Color3.fromRGB(255, 250, 238), { mat = Enum.Material.Neon, shadow = false })
	local right = toward:Cross(Vector3.yAxis).Unit
	for _, s in { { 0, 14, 0.07, false }, { 180, 9, 0.06, false }, { 35, 6, 0.05, true }, { 145, 5, 0.05, false },
		{ -30, 5, 0.05, false }, { -150, 4, 0.04, false }, { 90, 3.2, 0.05, false } } do
		local a = math.rad(s[1])
		local dir = (right * math.cos(a) + Vector3.yAxis * math.sin(a)).Unit
		part(Vector3.new(s[3], s[3], s[2]), CFrame.lookAt(at + dir * s[2] / 2, at + dir * s[2]),
			s[4] and Color3.fromRGB(255, 205, 90) or Color3.fromRGB(255, 244, 214), { mat = Enum.Material.Neon, tr = 0.15, shadow = false })
	end
end

local function eyesOf(g)
	local _, size = g:GetBoundingBox()
	local h = size.Y
	local piv = g:GetPivot()
	return piv * Vector3.new(-EYE.X * h, EYE.Y * h, EYE.Z * h), piv * Vector3.new(EYE.X * h, EYE.Y * h, EYE.Z * h)
end

P[7] = function() -- CALM: relaxing in the pool, nothing wrong yet
	setWater(C.water, 0.35)
	relaxer("closed")
	floaters()
	shot(BD.CAM[7])
end

P[8] = function() -- THE SHADOW: over your head, from behind: a huge duck shape in the water ahead of you
	setWater(Color3.fromRGB(46, 88, 122), 0.45)
	relaxer("closed")
	floaters()
	local g = T.giant:Clone()
	local main = g:FindFirstChildWhichIsA("MeshPart")
	local sh = main:Clone()
	-- the duck's side profile (round head, beak, body, tail: an arch), laid flat just under the surface, head toward you
	sh.Size = Vector3.new(0.4, main.Size.Y * 0.85, main.Size.Z * 0.85)
	sh.Color, sh.CastShadow, sh.Reflectance = Color3.fromRGB(8, 14, 24), false, 0
	sh.CFrame = CFrame.fromMatrix(L(-9, WATER - 1.3, -2), Vector3.new(0, 1, 0), Vector3.new(1, 0, 0), Vector3.new(0, 0, -1))
	sh.Parent = dyn
	g:Destroy()
	shot(BD.CAM[8])
end

P[9] = function() -- IT EMERGES: wide on the pool, the crown and the foam cap break the surface, water pouring off
	setWater(C.water, 0.35)
	relaxer("shout")
	floaters()
	local g = giant(WATER + 6 - GIANT_H)
	local top = L(DUCK_AT.X, WATER + 6, DUCK_AT.Z)
	pour(L(DUCK_AT.X + 1, WATER, DUCK_AT.Z), 6.5, top.Y, 16)
	shot(BD.CAM[9])
end

P[10] = function() -- THE EYES: close on it emerging, the eyes clear the water, flare lines off them
	setWater(C.water, 0.35)
	local g = giant(WATER + 1.3 - EYE.Y * GIANT_H)
	local l, r = eyesOf(g)
	local toward = Vector3.new(1, 0, 0)
	flare(l + toward * 0.4, toward)
	flare(r + toward * 0.4, toward)
	pour(L(DUCK_AT.X + 2, WATER, DUCK_AT.Z), 7.5, O.Y + WATER + 1.3 + 0.32 * GIANT_H, 20)
	for _, q in dyn:GetChildren() do -- this close, the sheets of water read as bars across the face: drops and rings only
		if q:IsA("Part") and q.Shape == Enum.PartType.Cylinder and q.Material ~= Enum.Material.Neon then q:Destroy() end
	end
	shot(BD.CAM[10])
end

-- ------------------------------------------------------------------ the animatic (20 Nov): the shots in motion
-- The owner judges finishers as video. BD.frame(i) stages frame i of BD.PLAN: each shot is staged once (BD.panel), then
-- every frame only moves things: the duck rising, the shadow sliding in, the flare lines growing, the jets reaching
-- out, the opponent playing his clip, the lens pushing, rising or panning. Captured frame by frame, assembled by
-- tools/roblox/bath_ducky_video.py (24 fps, letterbox, sound).
BD.PLAN = { { 7, 8 }, { 8, 10 }, { 9, 12 }, { 10, 10 }, { 1, 17 }, { 2, 10 }, { 3, 6 }, { 4, 8 }, { 5, 12 }, { 6, 14 } }

local CLIPS = {}
local function clip(name)
	if CLIPS[name] then return CLIPS[name] end
	local ks = KSP:GetKeyframeSequenceAsync("rbxassetid://" .. ANIM[name])
	local kfs = ks:GetKeyframes()
	table.sort(kfs, function(a, b) return a.Time < b.Time end)
	local out = {}
	for _, kf in kfs do
		local map = {}
		for _, p in kf:GetDescendants() do
			if p:IsA("Pose") then map[p.Name] = p.CFrame end
		end
		table.insert(out, { t = kf.Time, map = map })
	end
	CLIPS[name] = out
	return out
end
-- a clip at time t: the two keyframes round it, blended joint by joint
local function posePlay(name, t)
	local k = clip(name)
	if t <= k[1].t then return k[1].map end
	if t >= k[#k].t then return k[#k].map end
	local i = 1
	while k[i + 1].t < t do i += 1 end
	local a, b = k[i], k[i + 1]
	local w = (t - a.t) / math.max(1e-4, b.t - a.t)
	local m = {}
	for n, cf in a.map do m[n] = cf:Lerp(b.map[n] or cf, w) end
	for n, cf in b.map do
		if not m[n] then m[n] = cf end
	end
	return m
end

local function V(t) return Vector3.new(t[1], t[2], t[3]) end
local function ease(u) u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
local function lerp(a, b, u) return a + (b - a) * u end
local function lens(eye, look, fov, roll) shot({ { eye.X, eye.Y, eye.Z }, { look.X, look.Y, look.Z }, fov, roll or 0 }) end
local function cam(n) local c = BD.CAM[n]; return V(c[1]), V(c[2]), c[3], c[4] or 0 end

-- what the staging of a shot made, each part with its starting state
local B = {}
local function grab()
	B = { parts = {} }
	for _, d in dyn:GetChildren() do
		if d:IsA("Model") and d.Name == "BathDucky" then B.giant = d; B.giantCF = d:GetPivot() end
		if d:IsA("Model") and d.Name == "Opponent" then B.opp = d end
		if d:IsA("BasePart") then
			local e = { p = d, cf = d.CFrame, size = d.Size, tr = d.Transparency }
			table.insert(B.parts, e)
			if d:IsA("MeshPart") and d.Name == "bd2_giant" then B.shadow = e end
		end
	end
end
local function isSplash(e) return e.p.Color == C.splash end
local function isRing(e) return e.p.Color == C.foam and e.tr > 0 end
local function giantDown(dy) if B.giant then B.giant:PivotTo(B.giantCF - Vector3.new(0, dy, 0)) end end
-- Spider-Verse timing: the duck's u snapped to every other frame of the shot (on twos); the lens keeps every frame
local function tw(u)
	local n = math.max(1, (B.n or 2) - 1)
	return math.floor(u * n / 2 + 1e-6) * 2 / n
end
local function placeOpp(map)
	local v = B.opp
	if not v then return end
	pose(v, map, L(OPP_AT.X, 0, OPP_AT.Z), math.pi / 2, { ground = O.Y })
	local lv = v.UpperTorso.CFrame.LookVector
	local turn = math.atan2(-lv.X, -lv.Z) - math.atan2(1, 0)
	local c = v.UpperTorso.Position
	local rot = CFrame.new(c) * CFrame.Angles(0, -turn, 0) * CFrame.new(-c)
	for _, d in v:GetDescendants() do
		if d:IsA("BasePart") then d.CFrame = rot * d.CFrame end
	end
end

local F = {}
F[7] = function(u) -- CALM: a slow push-in
	local e, l, f, r = cam(7)
	lens(e + (e - l).Unit * 2.5 * (1 - ease(u)), l, f, r)
end
F[8] = function(u) -- THE SHADOW: it slides in under the water toward you
	if B.shadow then B.shadow.p.CFrame = B.shadow.cf - Vector3.new(7 * (1 - ease(tw(u))), 0, 0) end
	local e, l, f, r = cam(8)
	lens(e + Vector3.new(0, 0.5 * (1 - ease(u)), 0), l, f, r)
end
F[9] = function(u) -- IT EMERGES: the dome comes up, the water runs off once it is out, the lens shudders
	giantDown(6 * (1 - ease(tw(u))))
	for _, e in B.parts do
		if isSplash(e) or isRing(e) then e.p.Transparency = u < 0.45 and 1 or e.tr end
	end
	local e, l, f, r = cam(9)
	local k = u > 0.3 and 1 or 0
	lens(e + Vector3.new(math.sin(u * 37) * 0.12, math.cos(u * 29) * 0.1, 0) * k, l, f, r)
end
F[10] = function(u) -- THE EYES: they clear the water, then the flare lines shoot out
	giantDown(2.2 * (1 - ease(math.min(tw(u) / 0.5, 1))))
	local k = math.clamp((tw(u) - 0.5) / 0.35, 0, 1)
	for _, e in B.parts do
		if e.p.Material == Enum.Material.Neon then
			if e.p:IsA("Part") and e.p.Shape == Enum.PartType.Ball then
				e.p.Size = e.size * math.max(k, 0.01)
				e.p.Transparency = k == 0 and 1 or e.tr
			else
				local len = e.size.Z
				local dir = e.cf.LookVector
				local at = e.cf.Position - dir * len / 2
				local lk = math.max(len * k, 0.01)
				e.p.Size = Vector3.new(e.size.X, e.size.Y, lk)
				e.p.CFrame = CFrame.lookAt(at + dir * lk / 2, at + dir * lk)
				e.p.Transparency = k == 0 and 1 or e.tr
			end
		end
	end
	local e, l, f, r = cam(10)
	lens(e + (l - e).Unit * 1.2 * ease(u), l, f, r)
end
F[1] = function(u) -- THE RISE: up out of the water, the splash bursts, the rays come on, the lens rises
	giantDown(8 * (1 - ease(math.min(tw(u) / 0.7, 1))))
	for _, e in B.parts do
		if isSplash(e) then e.p.Transparency = u < 0.2 and 1 or e.tr end
		if e.p.Material == Enum.Material.Neon and math.abs(e.size.Y - 60) < 0.1 then
			e.p.Transparency = u < 0.45 and 1 or lerp(1, e.tr, (u - 0.45) / 0.55)
		end
	end
	local e, l, f, r = cam(1)
	lens(e + Vector3.new(0, -0.35 + 1.3 * ease(u), 0), l + Vector3.new(0, -4 * (1 - ease(u)), 0), f, r)
end
F[2] = function(u) -- THE OPPONENT: a whip pan off the duck to the door, zooming in; he looks round
	local e, l, f, r = cam(2)
	local w = ease(ease(u))
	lens(e, lerp(Vector3.new(-14, WATER + 13, -2), l, w), lerp(60, f, w), r)
	placeOpp(posePlay("look", 1.0 + 1.8 * u))
end
F[3] = function(u) -- YOU AND THE DUCKY: a slow push-in
	local e, l, f, r = cam(3)
	lens(e + (e - l).Unit * 3 * (1 - ease(u)), l, f, r)
end
F[4] = function(u) -- THE STANDOFF: a slow drift
	local e, l, f, r = cam(4)
	lens(e + Vector3.new(-2 * (1 - ease(u)), 0, 0), l, f, r)
end
F[5] = function(u) -- THE SPRAY: the beak's jet reaches the door first, the pistol's a beat later
	local rods = {}
	for _, e in B.parts do
		if e.p:IsA("Part") and e.p.Shape == Enum.PartType.Cylinder and isSplash(e) then table.insert(rods, e) end
	end
	for _, e in rods do
		local len = e.size.X
		local a = e.cf * Vector3.new(-len / 2, 0, 0)
		local b = e.cf * Vector3.new(len / 2, 0, 0)
		local dir = (b - a).Unit
		e.k = math.clamp((u - (e.size.Y > 1 and 0 or 0.15)) / 0.5, 0, 1)
		e.a, e.dir = a, dir
		local lk = math.max(len * e.k, 0.01)
		e.p.Size = Vector3.new(lk, e.size.Y, e.size.Z)
		e.p.CFrame = CFrame.lookAt(a + dir * lk / 2, a + dir * lk) * CFrame.Angles(0, math.pi / 2, 0)
		e.p.Transparency = e.k == 0 and 1 or e.tr
	end
	for _, e in B.parts do
		if e.p:IsA("Part") and e.p.Shape == Enum.PartType.Ball and isSplash(e) then
			for _, rd in rods do
				local q = e.cf.Position - rd.a
				local t = q:Dot(rd.dir) / rd.size.X
				if t > -0.05 and t < 1.05 and (q - rd.dir * q:Dot(rd.dir)).Magnitude < rd.size.Y * 2 then
					e.p.Transparency = t <= rd.k and e.tr or 1
				end
			end
		end
	end
	local e, l, f, r = cam(5)
	lens(e + Vector3.new(0, math.sin(u * 50) * 0.06, 0), l, f, r)
end
F[6] = function(u) -- SOAKED: knocked back through the hit, the lens leans in
	placeOpp(posePlay("pulled", 0.3 + 1.2 * u))
	local e, l, f, r = cam(6)
	lens(e + (l - e).Unit * 1.0 * ease(u), l, f, r - 3 * ease(u))
end

function BD.frame(i)
	local s, n0 = nil, 0
	for _, row in BD.PLAN do
		if i < n0 + row[2] then s = row; break end
		n0 += row[2]
	end
	if not s then return "past the end" end
	local u = s[2] > 1 and (i - n0) / (s[2] - 1) or 0
	if BD.cur ~= s[1] then
		BD.panel(s[1])
		grab()
		B.n = s[2]
		BD.cur = s[1]
		task.wait(1) -- (fresh clones can be missing from a capture taken at once)
	end
	F[s[1]](u)
	return string.format("f%03d shot %d u %.2f", i, s[1], u)
end

-- ------------------------------------------------------------------ round 5 (20 Nov): slower, new beats, real water
-- The owner on the round-4 animatic: "Ducky cinematic goes by too quickly!! Ducky emerges pause on him, his head snaps!!
-- Enemy walks in after opening door shot of enemy looking the shot of in air like I mentioned it's supposed to be
-- awkward and silly so pause it for a second then he gets splashed used some of the new vfx we got for the water, also
-- the water that comes off the duck should be actual water with physics rn it's just like code built tubes ??"
-- So: every shot longer (about 21 s in all); after the rise a held look at the duck, then its head snaps round; the
-- door opens, he walks in, a look shot, then (after the spray starts) he jumps in fright and the picture HOLDS on him in
-- the air for a second before the splash lands. All the water is particles now (ParticleEmitters with gravity and drag,
-- stepped a fixed slice of time per captured frame: BD.frame), no more parts for water: sheets and drops spilling off
-- the duck, a crown of water thrown up round it, rings spreading on the surface, the jets as real arcing streams; the hit
-- is the bought Combat VFX pack's slam, streaks and a ring (ReplicatedStorage.JankfireVfx HitSlam) recoloured to
-- water, with our splash crown.
ANIM.walk = 507777826 -- Roblox's own R15 walk
ANIM.jump = 507765000 -- Roblox's own R15 jump

local SMOKE = "rbxasset://textures/particles/smoke_main.dds"
local TEXW = { bubble = "rbxassetid://127426547666953", crown = "rbxassetid://97108513980197", ripple = "rbxassetid://93806501334938" }
local WATER_CS = ColorSequence.new(rgb(240, 250, 255), rgb(150, 205, 236))
local function NSK(t)
	local k = {}
	for _, p in t do table.insert(k, NumberSequenceKeypoint.new(p[1], p[2])) end
	return NumberSequence.new(k)
end
local function fxHost(cf, size, parent)
	return part(size, cf, Color3.new(1, 1, 1), { parent = parent or dyn, tr = 1, shadow = false, name = "fxhost" })
end
local function em(parent, t)
	local e = Instance.new("ParticleEmitter")
	e.Texture = SMOKE; e.Color = WATER_CS; e.LightInfluence = 0.7; e.LightEmission = 0.15
	e.Rate = 0; e.TimeScale = 0 -- (frozen until BD.frame steps it)
	for k, v in t do e[k] = v end
	e.Parent = parent
	return e
end
-- water spilling off a body: streaks that lift a little and fall (gravity), and drops thrown wider
local function spill(host, rate)
	em(host, { Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(1, 4),
		SpreadAngle = Vector2.new(70, 70), Acceleration = Vector3.new(0, -60, 0), Drag = 0.4, Lifetime = NumberRange.new(0.7, 1.3),
		Rate = rate, Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NSK({ { 0, -2.2 }, { 1, -1.4 } }),
		Size = NSK({ { 0, 0.35 }, { 1, 0.75 } }), Transparency = NSK({ { 0, 0.2 }, { 0.8, 0.45 }, { 1, 1 } }) })
	em(host, { Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(4, 10),
		SpreadAngle = Vector2.new(85, 85), Acceleration = Vector3.new(0, -70, 0), Lifetime = NumberRange.new(0.5, 1.0),
		Rate = rate * 0.5, Size = NSK({ { 0, 0.22 }, { 1, 0.12 } }), Transparency = NSK({ { 0, 0.1 }, { 1, 0.6 } }) })
end
-- a crown of water thrown up from the surface round something breaking it, falling back
local function crown(at, radius, rate, burst)
	local h = fxHost(CFrame.new(at), Vector3.new(radius * 2, 0.2, radius * 2))
	local e = em(h, { Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(16, 30), SpreadAngle = Vector2.new(22, 22),
		Acceleration = Vector3.new(0, -55, 0), Drag = 0.2, Lifetime = NumberRange.new(0.9, 1.5), Rate = rate,
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NSK({ { 0, -2.4 }, { 1, -1.2 } }),
		Size = NSK({ { 0, 0.6 }, { 1, 1.3 } }), Transparency = NSK({ { 0, 0.15 }, { 0.75, 0.4 }, { 1, 1 } }) })
	e:SetAttribute("Burst", burst or 0)
	return h
end
-- rings spreading on the surface, and soap bubbles drifting up
local function ripples(at, radius, rate)
	local h = fxHost(CFrame.new(at + Vector3.new(0, 0.05, 0)), Vector3.new(radius * 2, 0.1, radius * 2))
	em(h, { Texture = TEXW.ripple, Color = ColorSequence.new(rgb(235, 246, 255)), Shape = Enum.ParticleEmitterShape.Disc,
		EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.05, 0.1), Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
		Lifetime = NumberRange.new(1.4, 2.0), Rate = rate, Size = NSK({ { 0, 2 }, { 1, 11 } }),
		Transparency = NSK({ { 0, 0.35 }, { 1, 1 } }), LightEmission = 0.3 })
	return h
end
local function bubblesUp(at, radius, rate)
	local h = fxHost(CFrame.new(at), Vector3.new(radius * 2, 0.2, radius * 2))
	em(h, { Texture = TEXW.bubble, Color = ColorSequence.new(rgb(255, 255, 255)), Shape = Enum.ParticleEmitterShape.Disc,
		EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(30, 30),
		Acceleration = Vector3.new(0, 1, 0), Lifetime = NumberRange.new(2, 3.5), Rate = rate, Size = NSK({ { 0, 0.5 }, { 1, 1.1 } }),
		Transparency = NSK({ { 0, 0.2 }, { 1, 0.9 } }), LightEmission = 0.35, LightInfluence = 0.3 })
	return h
end
-- a jet: a real stream fired from `from` at `to`, arcing a little under gravity; it reaches its end and stops there
local function stream(from, to, width, speed)
	local dist = (to - from).Magnitude
	local t = dist / speed
	local h = fxHost(CFrame.lookAt(from, to + Vector3.new(0, 0.5 * 14 * t * t, 0)), Vector3.new(0.3, 0.3, 0.3)) -- (aimed up: it falls onto the mark)
	local e = em(h, { EmissionDirection = Enum.NormalId.Front, Speed = NumberRange.new(speed * 0.97, speed), SpreadAngle = Vector2.new(2.5, 2.5),
		Acceleration = Vector3.new(0, -14, 0), Lifetime = NumberRange.new(dist / speed), Rate = 420,
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NSK({ { 0, -2.6 }, { 1, -2 } }),
		Size = NSK({ { 0, width }, { 1, width * 1.5 } }), Transparency = NSK({ { 0, 0.1 }, { 0.85, 0.3 }, { 1, 0.8 } }) })
	e.Enabled = false
	return e, dist / speed
end
-- the hit: the bought pack's slam (streaks and a ring), recoloured to water and shrunk to fit, plus our splash crown and
-- drops thrown off (the pack's KillIceBurst was tried: its snowflake sprites read as snow, not water)
local function scaleNS(ns, k)
	local kp = {}
	for _, q in ns.Keypoints do table.insert(kp, NumberSequenceKeypoint.new(q.Time, q.Value * k, q.Envelope * k)) end
	return NumberSequence.new(kp)
end
local function splashKit(at, toward)
	local made = {}
	local lib = RS:FindFirstChild("JankfireVfx")
	for _, n in { "HitSlam" } do
		local t = lib and lib:FindFirstChild(n)
		if t then
			local c = t:Clone()
			local host = fxHost(CFrame.lookAt(at, at + toward), Vector3.new(1, 1, 1))
			if c:IsA("BasePart") then
				c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.Transparency = 1
				c.CFrame = host.CFrame
				c.Parent = dyn
			elseif c:IsA("Attachment") then
				c.CFrame = CFrame.identity; c.Parent = host
			elseif c:IsA("Model") then
				c:PivotTo(host.CFrame); c.Parent = dyn
			else -- a folder of effects: hang them all on the host
				for _, d in c:GetDescendants() do
					if d:IsA("ParticleEmitter") or d:IsA("Attachment") then d.Parent = host end
				end
				c:Destroy()
				c = host
			end
			for _, d in c:GetDescendants() do
				if d:IsA("ParticleEmitter") then
					d.Color = WATER_CS; d.TimeScale = 0; d.Enabled = false
					d.Size = scaleNS(d.Size, 0.6)
					table.insert(made, d)
				elseif d:IsA("Beam") or d:IsA("Trail") or d:IsA("Light") then
					d.Enabled = false
				elseif d:IsA("BaseScript") then
					d:Destroy()
				end
			end
		end
	end
	local h = fxHost(CFrame.lookAt(at, at + toward), Vector3.new(1.5, 1.5, 1.5))
	local cr = em(h, { Texture = TEXW.crown, Color = ColorSequence.new(rgb(240, 250, 255)), Speed = NumberRange.new(0.5),
		Lifetime = NumberRange.new(0.5, 0.7), Size = NSK({ { 0, 1.5 }, { 1, 5 } }), Transparency = NSK({ { 0, 0.1 }, { 1, 1 } }),
		Rotation = NumberRange.new(-20, 20), LightEmission = 0.3 })
	local dr = em(h, { Shape = Enum.ParticleEmitterShape.Sphere, Speed = NumberRange.new(14, 28), SpreadAngle = Vector2.new(180, 180),
		Acceleration = Vector3.new(0, -60, 0), Lifetime = NumberRange.new(0.6, 1.1), Orientation = Enum.ParticleOrientation.VelocityParallel,
		Squash = NSK({ { 0, -2.4 }, { 1, -1.6 } }), Size = NSK({ { 0, 0.3 }, { 1, 0.5 } }), Transparency = NSK({ { 0, 0.1 }, { 1, 0.9 } }) })
	table.insert(made, cr); table.insert(made, dr)
	cr:SetAttribute("Burst", 5); dr:SetAttribute("Burst", 90)
	return made
end
local function burst(list)
	for _, e in list do e:Emit(e:GetAttribute("Burst") or e:GetAttribute("EmitCount") or 20) end
end
-- run every emitter on the stage for dt seconds of simulation, then freeze them (a frame's worth of physics)
local function stepFx(dt)
	if dt <= 0 then return end
	local ems = {}
	for _, d in root:GetDescendants() do
		if d:IsA("ParticleEmitter") then table.insert(ems, d) end
	end
	for _, e in ems do e.TimeScale = 1 end
	task.wait(dt)
	for _, e in ems do e.TimeScale = 0 end
end
BD.stepFx = stepFx
local function preroll(t) stepFx(t) end -- (run the water on before the shot starts)

-- the door: shut until the door shot, then it swings open into the hall
local DOOR_STATE = { [7] = 0, [8] = 0, [9] = 0, [10] = 0, [1] = 0, [11] = 0 }
local function setDoor(a)
	for _, d in root:GetChildren() do
		if d:IsA("Part") and d.Color == C.door then
			d.CFrame = CFrame.new(L(ROOM.x1 + 1, (DOOR.h - 0.2) / 2, DOOR.z1)) * CFrame.Angles(0, math.rad(a), 0)
				* CFrame.new(0, 0, -(DOOR.z1 - DOOR.z0) / 2)
		end
	end
end

-- the opponent anywhere along the walk in, facing the room; the clip's own root turn is taken out (chest to -X)
local function placeOppAt(v, map, x, lift)
	pose(v, map, L(x, 0, OPP_AT.Z), math.pi / 2, { ground = O.Y + (lift or 0) })
	local lv = v.UpperTorso.CFrame.LookVector
	local turn = math.atan2(-lv.X, -lv.Z) - math.atan2(1, 0)
	local c = v.UpperTorso.Position
	local rot = CFrame.new(c) * CFrame.Angles(0, -turn, 0) * CFrame.new(-c)
	for _, d in v:GetDescendants() do
		if d:IsA("BasePart") then d.CFrame = rot * d.CFrame end
	end
end

local RISEN = WATER - 5.4 -- the giant's pivot at the end of the rise
local function wetGiant(g, rate)
	local _, size = g:GetBoundingBox()
	local piv = g:GetPivot()
	local h = fxHost(piv * CFrame.new(0, size.Y * 0.5, 0), Vector3.new(size.X, size.Y * 0.55, size.Z), g)
	spill(h, rate)
	local top = fxHost(piv * CFrame.new(0, size.Y * 0.93, size.Z * 0.05), Vector3.new(size.X * 0.45, 0.2, size.Z * 0.4), g)
	em(top, { Shape = Enum.ParticleEmitterShape.Disc, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(2, 5),
		SpreadAngle = Vector2.new(80, 80), Acceleration = Vector3.new(0, -60, 0), Drag = 0.3, Lifetime = NumberRange.new(0.8, 1.4),
		Rate = rate * 0.35, Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NSK({ { 0, -2 }, { 1, -1.4 } }),
		Size = NSK({ { 0, 0.4 }, { 1, 0.8 } }), Transparency = NSK({ { 0, 0.2 }, { 0.8, 0.45 }, { 1, 1 } }) })
	return h
end

P[1] = function() -- THE RISE: up out of the deep water like a kaiju, water pouring off it, a crown of water, rays
	player(POSE.idle, math.pi / 2, "shout", { tilt = 0.12 })
	local g = giant(RISEN)
	wetGiant(g, 320)
	crown(L(DUCK_AT.X, WATER, DUCK_AT.Z), 8, 160, 420)
	ripples(L(DUCK_AT.X, WATER, DUCK_AT.Z), 10, 4)
	bubblesUp(L(DUCK_AT.X + 4, WATER, DUCK_AT.Z), 8, 6)
	foamPile(L(DUCK_AT.X + 6, WATER, DUCK_AT.Z), 7, 30, 0.5, 1.2)
	floaters()
	local head = L(DUCK_AT.X - 2, WATER + 19.6, DUCK_AT.Z)
	for i = -4, 4 do
		local a = i * 0.26
		local dir = Vector3.new(-0.2, math.cos(a), math.sin(a)).Unit
		part(Vector3.new(0.12, 60, 1.2), CFrame.lookAt(head, head + Vector3.new(1, 0, 0), dir) * CFrame.new(0, 30, 0),
			C.ray, { mat = Enum.Material.Neon, tr = 0.9, shadow = false })
	end
	shot(BD.CAM[1])
end

P[9] = function() -- IT EMERGES: the crown and foam cap break the surface, water running off it, rings spreading
	relaxer("shout")
	floaters()
	local g = giant(WATER + 6 - GIANT_H)
	wetGiant(g, 140)
	crown(L(DUCK_AT.X, WATER, DUCK_AT.Z), 6, 70, 160)
	ripples(L(DUCK_AT.X, WATER, DUCK_AT.Z), 9, 3)
	shot(BD.CAM[9])
end

P[10] = function() -- THE EYES: the eyes clear the water, flare lines; water sheeting off the head
	local g = giant(WATER + 1.3 - EYE.Y * GIANT_H)
	local l, r = eyesOf(g)
	local toward = Vector3.new(1, 0, 0)
	flare(l + toward * 0.4, toward)
	flare(r + toward * 0.4, toward)
	wetGiant(g, 160)
	ripples(L(DUCK_AT.X + 3, WATER, DUCK_AT.Z), 8, 3)
	preroll(0.4)
	shot(BD.CAM[10])
end

P[11] = function() -- THE PAUSE AND THE SNAP: a held look at it dripping, then its head snaps round
	player(POSE.idle, math.pi / 2, "shout", { tilt = 0.12 })
	local g = giant(RISEN)
	wetGiant(g, 90)
	ripples(L(DUCK_AT.X, WATER, DUCK_AT.Z), 10, 2)
	floaters()
	preroll(1.2)
	shot(BD.CAM[11])
end

P[12] = function() -- THE DOOR: it swings open, light floods in, a figure behind it
	local v = newRig("victim")
	placeOppAt(v, POSE.idle, ROOM.x1 + 5)
	face(v, "puzzled")
	shot(BD.CAM[12])
end

P[13] = function() -- HE WALKS IN
	local v = newRig("victim")
	placeOppAt(v, POSE.idle, ROOM.x1 + 5)
	face(v, "puzzled")
	shot(BD.CAM[13])
end

P[14] = function() -- HE LOOKS: close on him, looking round, then he sees it
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[14])
end

for _, n in { 3, 4 } do -- YOU AND THE DUCKY, THE STANDOFF: as round 4, the duck still dripping
	P[n] = function()
		player(POSE.idle, -math.pi / 2, "stern")
		local g = giant(WATER - 3.4)
		wetGiant(g, 30)
		floaters()
		opponent(POSE.look, "puzzled")
		preroll(1.0)
		shot(BD.CAM[n])
	end
end

local function sprayRig()
	local p = newRig("player")
	pose(p, POSE.point, L(PLAYER_AT.X, 0, PLAYER_AT.Z), -math.pi / 2, { ground = O.Y + SEAT_TOP })
	foamHair(p)
	face(p, "stern")
	foamPile(L(PLAYER_AT.X, WATER, PLAYER_AT.Z), 2.2, 12, 0.3, 0.6)
	local muzzle, held = gunInHand(p)
	local g = giant(WATER - 3.4)
	wetGiant(g, 40)
	floaters()
	return muzzle, held, g
end
-- the jets aim at where his chest is in the soak (he is in the air for the hold, so they aim just under him there)
local function jets(muzzle, g, target)
	local e1, t1 = stream(beakOf(g), target + Vector3.new(-0.3, 0.2, 0.4), 1.25, 62)
	local e2, t2 = stream(muzzle, target + Vector3.new(-0.3, -0.3, -0.3), 0.5, 70)
	return e1, t1, e2, t2
end

P[5] = function() -- THE SPRAY: the beak's stream fires, the sniper's a beat later
	local muzzle, held, g = sprayRig()
	local v = opponent(POSE.look, "puzzled")
	local e1, _, e2 = jets(muzzle, g, v.UpperTorso.Position)
	e1:SetAttribute("Start", 0); e2:SetAttribute("Start", 0.2)
	BD.held = held
	shot(BD.CAM[5])
end

P[15] = function() -- IN THE AIR: he jumps in fright and the picture holds on him, the streams a breath away
	local muzzle, held, g = sprayRig()
	local v = newRig("victim")
	local jmap = pickPose("jump", function(cfs) return cfs.LeftHand.Position.Y + cfs.RightHand.Position.Y end)
	placeOppAt(v, jmap, OPP_AT.X, 3.2)
	face(v, "shout")
	local chest = v.UpperTorso.Position
	local e1, t1, e2, t2 = jets(muzzle, g, chest)
	e1.Enabled = true; e2.Enabled = true
	preroll(math.min(t1, t2) * 0.9) -- the fronts of the streams stop just short of him
	BD.held = held
	shot(BD.CAM[15])
end

P[6] = function() -- SOAKED: the streams land, the pack's burst and ring in water, he is knocked back, dripping
	local muzzle, held, g = sprayRig()
	local v = opponent(POSE.pulled, "drenched")
	local chest = v.UpperTorso.Position
	local e1, t1, e2, t2 = jets(muzzle, g, chest)
	e1.Enabled = true; e2.Enabled = true
	preroll(math.max(t1, t2) + 0.05)
	BD.splash = splashKit(chest - Vector3.new(0.6, 0, 0), Vector3.new(-1, 0.2, 0))
	local drip = fxHost(v.UpperTorso.CFrame, Vector3.new(2.4, 3, 1.4), v)
	spill(drip, 60)
	part(Vector3.new(0.12, 7, 7), CFrame.new(L(OPP_AT.X - 2, 0.06, OPP_AT.Z)) * CFrame.Angles(0, 0, math.pi / 2), C.splash,
		{ shape = Enum.PartType.Cylinder, tr = 0.45, shadow = false }) -- the puddle
	BD.held = held
	shot(BD.CAM[6])
end

-- the new lenses
BD.CAM[11] = { { 3, 9.5, 2 }, { -15, 16, -2 }, 50, 0 } -- THE PAUSE AND THE SNAP: on the duck, from you
BD.CAM[12] = { { 31, 6.5, 9 }, { 46, 5, -1 }, 46, 0 } -- THE DOOR
BD.CAM[13] = { { 35, 5.5, 5 }, { 45, 4.8, -1 }, 44, 0 } -- HE WALKS IN (only staging: F[13] tracks low ahead of him since round 6)
BD.CAM[14] = { { 40.4, 5.3, 1.6 }, { 43.5, 4.9, -1 }, 38, 0 } -- HE LOOKS
BD.CAM[15] = { { 33.5, 6.6, 11 }, { 40.5, 6.8, -1 }, 54, 2 } -- IN THE AIR

-- the frame motion for the new and changed shots
F[11] = function(u) -- held still, then the snap: looking aside, then round to face you in two frames (a small overshoot)
	local n = math.max(1, B.n - 1)
	local k = math.floor(u * n + 0.5)
	local snapAt = math.floor(n * 0.62)
	local a = k < snapAt and 26 or (k == snapAt and -7 or 0)
	if B.giant then B.giant:PivotTo(B.giantCF * CFrame.Angles(0, math.rad(a), 0)) end
	local e, l, f, r = cam(11)
	lens(e + (l - e).Unit * 0.6 * ease(u), l, f, r)
end
F[12] = function(u) -- the door swings open
	setDoor(-70 * ease(math.clamp((u - 0.25) / 0.55, 0, 1)))
	local e, l, f, r = cam(12)
	lens(e, l, f, r)
end
-- HE WALKS IN, round 6 (the owner: "guy walking in needs a different more dynamic angle"): a low lens on the floor
-- ahead of him, tracking back as he comes through the door, looking up at him, tilted, a little bob with his steps
F[13] = function(u)
	local k = clip("walk")
	local walkLen = k[#k].t
	local x = lerp(ROOM.x1 + 5, OPP_AT.X, math.clamp(u * 1.08, 0, 1)) -- (steady steps, a beat to settle at the end)
	if B.opp then placeOppAt(B.opp, posePlay("walk", (u * 1.7 * 0.8) % walkLen), x) end
	local w = ease(u)
	local bob = math.abs(math.sin(u * math.pi * 4)) * 0.08
	local eye = Vector3.new(x - lerp(5.2, 6.8, w), 0.9 + 0.5 * w + bob, -1 + lerp(1.8, 1.2, u))
	lens(eye, Vector3.new(x, 4.6, -1), lerp(70, 62, w), lerp(11, 5, w))
end
F[14] = function(u) -- he looks round; at the end his face drops
	if B.opp then
		placeOppAt(B.opp, posePlay("look", 1.0 + 1.6 * u), OPP_AT.X)
		if u > 0.75 then face(B.opp, "shout") end
	end
	local e, l, f, r = cam(14)
	lens(e + (l - e).Unit * 0.5 * ease(u), l, f, r)
end
F[5] = function(u) -- the streams switch on in turn; the physics does the rest
	for _, d in root:GetDescendants() do
		if d:IsA("ParticleEmitter") and d:GetAttribute("Start") then d.Enabled = u >= d:GetAttribute("Start") end
	end
	local e, l, f, r = cam(5)
	lens(e + Vector3.new(0, math.sin(u * 50) * 0.06, 0), l, f, r)
end
F[15] = function(u) -- the hold: nothing moves but a slow creep of the lens
	local e, l, f, r = cam(15)
	lens(e + (l - e).Unit * 0.4 * u, l, f, r)
end
F[6] = function(u) -- the splash lands on the first frame, then he is knocked back through it
	if BD.splash and not B.burst then burst(BD.splash); B.burst = true end
	if B.opp then placeOppAt(B.opp, posePlay("pulled", 0.3 + 1.2 * u), OPP_AT.X) end
	local e, l, f, r = cam(6)
	lens(e + (l - e).Unit * 1.0 * ease(u), l, f, r - 3 * ease(u))
end
-- the rise and the emergence: only the giant's own motion (on twos) and the lens; the water is physics now
F[9] = function(u)
	giantDown(6 * (1 - ease(tw(u))))
	if tw(u) >= 0.3 and not B.burst then
		for _, d in root:GetDescendants() do
			if d:IsA("ParticleEmitter") and (d:GetAttribute("Burst") or 0) > 0 then d:Emit(d:GetAttribute("Burst")) end
		end
		B.burst = true
	end
	local e, l, f, r = cam(9)
	local k = u > 0.3 and 1 or 0
	lens(e + Vector3.new(math.sin(u * 37) * 0.12, math.cos(u * 29) * 0.1, 0) * k, l, f, r)
end
F[1] = function(u)
	giantDown(8 * (1 - ease(math.min(tw(u) / 0.7, 1))))
	for _, e in B.parts do
		if e.p.Material == Enum.Material.Neon and math.abs(e.size.Y - 60) < 0.1 then
			e.p.Transparency = u < 0.45 and 1 or lerp(1, e.tr, (u - 0.45) / 0.55)
		end
	end
	if u < 0.05 and not B.burst then
		for _, d in root:GetDescendants() do
			if d:IsA("ParticleEmitter") and (d:GetAttribute("Burst") or 0) > 0 then d:Emit(d:GetAttribute("Burst")) end
		end
		B.burst = true
	end
	local e, l, f, r = cam(1)
	lens(e + Vector3.new(0, -0.35 + 1.3 * ease(u), 0), l + Vector3.new(0, -4 * (1 - ease(u)), 0), f, r)
end

-- the cut, slower: { shot, captured frames, seconds } (about 21 s, 219 frames; the duck shots at 12 a second, on twos); dt per frame = seconds / frames of physics
BD.PLAN = { { 7, 10, 1.5 }, { 8, 12, 1.6 }, { 9, 22, 1.8 }, { 10, 19, 1.6 }, { 1, 24, 2.0 }, { 11, 22, 1.8 }, { 12, 12, 1.3 },
	{ 13, 20, 1.7 }, { 14, 12, 1.2 }, { 3, 8, 1.0 }, { 4, 8, 1.2 }, { 5, 14, 1.2 }, { 6, 24, 2.0 } }
-- (round 6, the owner: "theres like a freeze frame of him in the air get rid of that and cut straight to him getting
-- drenched": IN THE AIR, shot 15, is out of the cut; P[15]/F[15] stay for the record)
local HOLD = { [15] = true }
function BD.first(n) -- the frame number shot n starts at (for test frames)
	local i = 0
	for _, row in BD.PLAN do
		if row[1] == n then return i, row[2] end
		i += row[2]
	end
end

function BD.frame(i)
	local s, n0 = nil, 0
	for _, row in BD.PLAN do
		if i < n0 + row[2] then s = row; break end
		n0 += row[2]
	end
	if not s then return "past the end" end
	local u = s[2] > 1 and (i - n0) / (s[2] - 1) or 0
	if BD.cur ~= s[1] then
		BD.splash = nil
		BD.panel(s[1])
		setDoor(DOOR_STATE[s[1]] or -70)
		grab()
		B.n = s[2]
		BD.cur = s[1]
		task.wait(1) -- (fresh clones can be missing from a capture taken at once)
	end
	F[s[1]](u)
	if not HOLD[s[1]] then stepFx(s[3] / s[2]) end
	return string.format("f%03d shot %d u %.2f", i, s[1], u)
end

-- ------------------------------------------------------------------ build / panel / clear
function BD.build()
	BD.clear(true)
	BD.cur = nil
	math.randomseed(20)
	root = Instance.new("Folder")
	root.Name = "BathDuckyBoard4"
	T.giant = loadModel(IDS.giant, "BathDucky")
	T.duck = loadModel(IDS.duck, "RubberDuck")
	T.tub = loadModel(IDS.tub, "Tub")
	local _, gs = T.giant:GetBoundingBox()
	T.giant:ScaleTo(GIANT_H / gs.Y)
	local _, ds = T.duck:GetBoundingBox()
	T.duck:ScaleTo(1.6 / ds.Y)
	local probe = newRig("player")
	J = joints(probe)
	for _, d in probe:GetChildren() do
		if d:IsA("BasePart") then SIZES[d.Name] = d.Size end
	end
	POSE.idle = pickPose("idle")
	POSE.sit = pickPose("sit")
	local reach = function(cfs) return -(cfs.RightHand.Position.Z) + cfs.RightHand.Position.Y * 0.3 end
	local t1, t2, t3
	POSE.point, t1 = pickPose("point", reach)
	-- standing, looking round: the frame whose head turns furthest from straight ahead
	POSE.look, t2 = pickPose("look", function(cfs)
		local lv = cfs.Head.LookVector
		return math.abs(math.atan2(lv.X, -lv.Z))
	end)
	-- knocked back: the frame whose head is furthest back while still well off the floor
	POSE.pulled, t3 = pickPose("pulled", function(cfs)
		local h = cfs.Head.Position
		return (h.Y > -0.5) and h.Z or -math.huge
	end)
	probe:Destroy()
	dyn = Instance.new("Folder")
	dyn.Name = "Panel"
	dyn.Parent = root
	root.Parent = workspace
	room()
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "BathDuckyGrade"; cc.TintColor = Color3.fromRGB(255, 246, 234); cc.Saturation = 0.12; cc.Contrast = 0.06
	cc.Parent = workspace.CurrentCamera
	return string.format("built: point %.2fs, look %.2fs, pulled %.2fs; giant %.1f tall", t1, t2, t3, GIANT_H)
end

function BD.dry() -- read-only: load and measure, parent nothing
	local out = {}
	for k, id in IDS do
		local m = loadModel(id, k)
		local _, size = m:GetBoundingBox()
		table.insert(out, string.format("%s %.2fx%.2fx%.2f parts %d", k, size.X, size.Y, size.Z, #m:GetChildren()))
		m:Destroy()
	end
	local probe = newRig("player")
	J = joints(probe)
	for _, d in probe:GetChildren() do
		if d:IsA("BasePart") then SIZES[d.Name] = d.Size end
	end
	probe:Destroy()
	for _, n in { "idle", "point", "look", "pulled" } do
		local ok, _, t, len = pcall(pickPose, n)
		table.insert(out, n .. (ok and string.format(" ok (%.2f of %.2fs)", t or 0, len or 0) or (" FAILED " .. tostring(t))))
	end
	local skins = RS:FindFirstChild("JankfireSkins")
	local tpl = skins and skins:FindFirstChild("pistol_ducky_tripo")
	if tpl then
		local rootP = tpl.PrimaryPart or tpl:FindFirstChildWhichIsA("BasePart", true)
		table.insert(out, string.format("pistol: %s, Grip %s, Muzzle %s, scale %.2f", tpl.ClassName, tostring(rootP and rootP:FindFirstChild("Grip") ~= nil),
			tostring(rootP and rootP:FindFirstChild("Muzzle") ~= nil), tpl:IsA("Model") and tpl:GetScale() or 0))
	else
		table.insert(out, "pistol_ducky_tripo NOT in JankfireSkins")
	end
	return table.concat(out, string.char(10))
end

function BD.panel(n)
	math.randomseed(200 + n)
	dyn:ClearAllChildren()
	P[n]()
	game:GetService("Selection"):Set({})
	return "shot " .. n .. " staged" .. (BD.held and (" (held: " .. BD.held .. ")") or "")
end

function BD.clear(keepCamera)
	pcall(BD.fillWater, Enum.Material.Air)
	local g = workspace.CurrentCamera:FindFirstChild("BathDuckyGrade")
	if g then g:Destroy() end
	local old = workspace:FindFirstChild("BathDuckyBoard4")
	while old do
		old:Destroy()
		old = workspace:FindFirstChild("BathDuckyBoard4")
	end
	if saved and not keepCamera then
		local cam = workspace.CurrentCamera
		cam.CFrame, cam.FieldOfView = saved[1], saved[2]
		saved = nil
	end
	return "cleared"
end

return "BD4 ready"
