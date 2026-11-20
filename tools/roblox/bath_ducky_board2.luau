-- BATH DUCKY finisher storyboard, round 2 (20 Nov 2026). The owner on round 1: "I dont like how the ducks look theyre
-- supposed to be rubber ducks, I want the reveal to look like the image, like a kaiju emeging from the water with a
-- perspective shot! then it pans to your oppenent at the door, and then back at you and the ducky, a ide shot of you in
-- the pool staring at your enemtn then you and the ducky spray hjim with water".
-- So: classic glossy rubber ducks (Tripo round 2, tools/roblox/bath_ducky_models.py), a tiled pool room with a door, the
-- player (killer) in the pool, the opponent (victim) at the door, six shots. Built in Studio (Edit) far off the map,
-- photographed one shot at a time and removed; nothing is saved into the place.
-- Run this file once (as an uploaded ModuleScript, require it); it defines shared.BD2:
--   BD2.build()   models, rigs and poses, the room          BD2.panel(n)   stages shot n (1-6), points the camera
--   BD2.clear()   removes everything, the Edit camera back  BD2.CAM[n]     each shot's lens, patch live to reframe
-- Poses are single keyframes of real clips, never keyed by hand: Roblox's own R15 idle and point for the player, and
-- the finisher session's uploaded victim clips (Finishers.ANIMS / SCENE_ANIMS) for the opponent.
local BD = {}
shared.BD2 = BD

local O = Vector3.new(-9400, 800, -8600) -- the floor of the set, far off every map
local IDS = { giant = 85544912707294, duck = 116208755186622 } -- the round-2 uploads (bd2_giant, bd2_duck)
BD.IDS = IDS
local ANIM = {
	idle = 507766666, point = 507770453, -- Roblox's own R15 idle and point
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
	water = rgb(104, 186, 228), splash = rgb(176, 224, 248), tile = rgb(186, 214, 222), poolTile = rgb(120, 190, 214),
	plaster = rgb(238, 233, 224), floor = rgb(226, 222, 214), coping = rgb(244, 242, 236), wood = rgb(176, 132, 92),
	door = rgb(150, 112, 80), hall = rgb(255, 248, 232), ray = rgb(255, 236, 170), towel = rgb(75, 155, 224),
}

local root, dyn, T, POSE, J = nil, nil, {}, {}, nil
local SIZES = {}
local WATER = -0.6 -- the pool's water surface
local POOL = { x0 = -28, x1 = 6, z0 = -16, z1 = 12, bottom = -3.2 }
local DOOR = { x = 36, z0 = -4, z1 = 2, h = 10 }

local function L(x, y, z) return O + Vector3.new(x, y, z) end

local function part(size, cf, colour, opts)
	opts = opts or {}
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	if opts.shape then p.Shape = opts.shape end
	p.Material = opts.mat or Enum.Material.SmoothPlastic
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

-- the skin in the hand (the VIP Ducky pistol, as the finisher's killer holds it); a small rubber duck if it is missing
local function gunInHand(rig)
	local skins = RS:FindFirstChild("JankfireSkins")
	local tpl = skins and skins:FindFirstChild("pistol_ducky_tripo")
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
		return want * tip, "pistol_ducky_tripo"
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
	local R = { parent = root }
	local tiles = { parent = root, mat = Enum.Material.CeramicTiles }
	local plaster = { parent = root, mat = Enum.Material.Plaster }
	-- the floor round the pool (top at 0), the pool's walls and bottom, its white coping
	box(-36, -1, -30, POOL.x0, 0, 30, C.floor, tiles)
	box(POOL.x1, -1, -30, 37, 0, 30, C.floor, tiles) -- (to the wall: the hall has its own floor)
	box(POOL.x0, -1, POOL.z1, POOL.x1, 0, 30, C.floor, tiles)
	box(POOL.x0, -1, -30, POOL.x1, 0, POOL.z0, C.floor, tiles)
	box(POOL.x0 - 1, POOL.bottom - 1, POOL.z0 - 1, POOL.x1 + 1, POOL.bottom, POOL.z1 + 1, C.poolTile, tiles)
	box(POOL.x0 - 1, POOL.bottom, POOL.z0 - 1, POOL.x0, 0, POOL.z1 + 1, C.poolTile, tiles)
	box(POOL.x1, POOL.bottom, POOL.z0 - 1, POOL.x1 + 1, 0, POOL.z1 + 1, C.poolTile, tiles)
	box(POOL.x0, POOL.bottom, POOL.z0 - 1, POOL.x1, 0, POOL.z0, C.poolTile, tiles)
	box(POOL.x0, POOL.bottom, POOL.z1, POOL.x1, 0, POOL.z1 + 1, C.poolTile, tiles)
	for _, c in { { POOL.x0 - 1.2, POOL.z0 - 1.2, POOL.x1 + 1.2, POOL.z0 }, { POOL.x0 - 1.2, POOL.z1, POOL.x1 + 1.2, POOL.z1 + 1.2 },
		{ POOL.x0 - 1.2, POOL.z0, POOL.x0, POOL.z1 }, { POOL.x1, POOL.z0, POOL.x1 + 1.2, POOL.z1 } } do
		box(c[1], 0, c[2], c[3], 0.3, c[4], C.coping, R)
	end
	local w = box(POOL.x0, WATER - 0.3, POOL.z0, POOL.x1, WATER, POOL.z1, C.water, { parent = root, tr = 0.35, shadow = false })
	w.Name = "Water"
	-- the walls: tiles to 12, plaster to 40; the right wall (x 36) has the door
	local function wall(x0, z0, x1, z1)
		box(x0, 0, z0, x1, 12, z1, C.tile, tiles)
		box(x0, 12, z0, x1, 40, z1, C.plaster, plaster)
	end
	wall(-37, -31, 37, -30) -- back
	wall(-37, 30, 37, 31) -- front
	wall(-37, -30, -36, 30) -- left
	wall(36, -30, 37, DOOR.z0) -- right, either side of the door
	wall(36, DOOR.z1, 37, 30)
	box(36, DOOR.h, DOOR.z0, 37, 12, DOOR.z1, C.tile, tiles)
	box(36, 12, DOOR.z0, 37, 40, DOOR.z1, C.plaster, plaster)
	box(-37, 40, -31, 37, 41, 31, C.plaster, plaster) -- ceiling
	-- the door frame, the door swung open into the hall, the bright hall behind
	box(35.6, 0, DOOR.z0 - 0.6, 37.4, DOOR.h + 0.6, DOOR.z0, C.coping, R)
	box(35.6, 0, DOOR.z1, 37.4, DOOR.h + 0.6, DOOR.z1 + 0.6, C.coping, R)
	box(35.6, DOOR.h, DOOR.z0, 37.4, DOOR.h + 0.6, DOOR.z1, C.coping, R)
	part(Vector3.new(0.4, DOOR.h - 0.2, DOOR.z1 - DOOR.z0), CFrame.new(L(37, (DOOR.h - 0.2) / 2, DOOR.z1)) * CFrame.Angles(0, math.rad(-70), 0)
		* CFrame.new(0, 0, -(DOOR.z1 - DOOR.z0) / 2), C.door, R)
	box(37, -1, -8, 46, 0, 6, C.floor, tiles)
	box(37, 0, -9, 46, 14, -8, C.plaster, plaster)
	box(37, 0, 6, 46, 14, 7, C.plaster, plaster)
	box(37, 14, -9, 46, 15, 7, C.plaster, plaster)
	local hall = box(45, 0, -8, 46, 14, 6, C.hall, { parent = root, mat = Enum.Material.Neon })
	local hl = Instance.new("PointLight"); hl.Range = 22; hl.Brightness = 2; hl.Color = rgb(255, 240, 210); hl.Parent = hall
	-- dim room light (the saved Lighting is the Rooftop's bright day), towels, a bench
	for _, p in { { -11, -2 }, { 20, -2 } } do
		local lamp = box(p[1] - 6, 39.7, p[2] - 4, p[1] + 6, 40, p[2] + 4, Color3.new(1, 1, 1), { parent = root, mat = Enum.Material.Neon })
		local sl = Instance.new("SurfaceLight"); sl.Face = Enum.NormalId.Bottom; sl.Range = 45; sl.Brightness = 0.45; sl.Angle = 120; sl.Parent = lamp
	end
	box(18, 7, -29.8, 24, 7.3, -29.4, C.coping, R)
	box(18.4, 3, -29.7, 23.6, 7, -29.3, C.towel, R)
	box(14, 0, 20, 26, 1.6, 23, C.wood, R)
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
	[1] = { { 5, -0.1, 3 }, { -14, 10.5, -2 }, 64, -4 }, -- THE RISE: low on the water behind the player, looking up past them
	[2] = { { -1, 2.0, -1.5 }, { 34, 4.6, -1 }, 28, 0 }, -- THE OPPONENT: the lens swings to the door
	[3] = { { 12, 3.0, 4 }, { -8, 9, -2 }, 60, 0 }, -- YOU AND THE DUCKY: back to them, from the door side
	[4] = { { -6, 18, 29 }, { 10, 3, -3 }, 60, 0 }, -- THE STANDOFF: wide, the pool and the door
	[5] = { { -19, 13, 10 }, { 30, 3, -1.5 }, 52, 0 }, -- THE SPRAY: over the duck's and the player's shoulders
	[6] = { { 27.5, 2.6, -6.5 }, { 33.5, 4.0, -1 }, 50, -3 }, -- SOAKED: on the opponent as the jets hit
}

-- ------------------------------------------------------------------ the shots
local P = {}
local PLAYER_AT = Vector3.new(-2, POOL.bottom, -2)
local DUCK_AT = Vector3.new(-16, 0, -2)
local OPP_AT = Vector3.new(33.5, 0, -1)
local GIANT_H = 22

local function giant(y)
	return duck("giant", L(DUCK_AT.X, y, DUCK_AT.Z), Vector3.new(1, 0, 0))
end
local function floaters()
	for _, d in { { -24, -12, 0.6 }, { -6, 9, -0.4 }, { 2, -12, 2.2 }, { -9, -13, 1.2 }, { 3, 8, -2.4 }, { -26, 8, 0.2 } } do
		duck("duck", L(d[1], WATER - 0.45, d[2]), Vector3.new(math.cos(d[3]), 0, math.sin(d[3])))
	end
end
local function player(map, yaw, expr, opts)
	local p = newRig("player")
	pose(p, map, L(PLAYER_AT.X, 0, PLAYER_AT.Z), yaw, { ground = O.Y + POOL.bottom, tilt = opts and opts.tilt })
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
	local g = giant(-6)
	splashAt(L(DUCK_AT.X, WATER, DUCK_AT.Z), 10, 12, 18)
	foamPile(L(DUCK_AT.X + 6, WATER, DUCK_AT.Z), 7, 30, 0.5, 1.2)
	for _, b in dyn:GetChildren() do -- keep the duck's face clear: no splash in front of it above the water
		if b:IsA("Part") and b.Shape == Enum.PartType.Ball and b.Transparency > 0.1 then
			local q = b.Position - O
			if q.X > DUCK_AT.X + 5 and q.Y > 0.5 then b:Destroy() end
		end
	end
	floaters()
	local head = L(DUCK_AT.X - 2, 19, DUCK_AT.Z)
	for i = -4, 4 do
		local a = i * 0.26
		local dir = Vector3.new(-0.2, math.cos(a), math.sin(a)).Unit
		part(Vector3.new(0.12, 60, 1.2), CFrame.lookAt(head, head + Vector3.new(1, 0, 0), dir) * CFrame.new(0, 30, 0),
			C.ray, { mat = Enum.Material.Neon, tr = 0.88, shadow = false })
	end
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[1])
end

P[2] = function() -- the pan: the opponent stands in the doorway
	player(POSE.idle, -math.pi / 2, "stern")
	giant(-4)
	floaters()
	opponent(POSE.look, "puzzled")
	shot(BD.CAM[2])
end

local function together(expr)
	player(POSE.idle, -math.pi / 2, expr) -- facing the door (+X: -90 deg of yaw)
	giant(-4)
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
	pose(p, POSE.point, L(PLAYER_AT.X, 0, PLAYER_AT.Z), -math.pi / 2, { ground = O.Y + POOL.bottom })
	foamHair(p)
	face(p, "stern")
	foamPile(L(PLAYER_AT.X, WATER, PLAYER_AT.Z), 2.2, 12, 0.3, 0.6)
	local muzzle, held = gunInHand(p)
	local g = giant(-4)
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

-- ------------------------------------------------------------------ build / panel / clear
function BD.build()
	BD.clear(true)
	math.randomseed(20)
	root = Instance.new("Folder")
	root.Name = "BathDuckyBoard2"
	T.giant = loadModel(IDS.giant, "BathDucky")
	T.duck = loadModel(IDS.duck, "RubberDuck")
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
	local old = workspace:FindFirstChild("BathDuckyBoard2")
	while old do
		old:Destroy()
		old = workspace:FindFirstChild("BathDuckyBoard2")
	end
	if saved and not keepCamera then
		local cam = workspace.CurrentCamera
		cam.CFrame, cam.FieldOfView = saved[1], saved[2]
		saved = nil
	end
	return "cleared"
end

return "BD2 ready"
