-- BATH DUCKY reveal storyboard stage (19 Nov 2026). The owner's own 9-panel storyboard, built in Studio (Edit) with a
-- real R15 avatar rig, our Tripo ducks (tools/roblox/bath_ducky_models.py) and chunky parts, far off the map, then
-- photographed one panel at a time and removed. Nothing here is saved into the place.
-- Run this whole file once with execute_luau (Edit); it defines shared.BD:
--   shared.BD.build()      loads the models and poses, builds the bathroom (about 3 s)
--   shared.BD.panel(n)     stages panel n (1-9) and points the camera; screen_capture takes the photo
--   shared.BD.clear()      removes everything and puts the Edit camera back
-- Poses come from Roblox's own R15 animations (KeyframeSequenceProvider): sit, idle, point, cheer; one keyframe each,
-- picked by a measurement (the highest hands for cheer, the furthest reach for point), never keyed by hand.
local BD = {}
shared.BD = BD

local O = Vector3.new(-9400, 800, -8600) -- the stage origin: the floor, far off every map
local IDS = { giant = 119395047122064, army = 111415394427988, tub = 112698164363965 }
local ANIM = { sit = 2506281703, idle = 507766666, point = 507770453, cheer = 507770677 }

local InsertService = game:GetService("InsertService")
local KSP = game:GetService("KeyframeSequenceProvider")
local Players = game:GetService("Players")

local function rgb(r, g, b) return Color3.fromRGB(r, g, b) end
local C = {
	skin = rgb(232, 186, 150), robe = rgb(207, 230, 246), trim = rgb(246, 246, 242), belt = rgb(75, 155, 224),
	foam = rgb(246, 246, 242), water = rgb(120, 190, 225), waterDark = rgb(46, 88, 122), shadow = rgb(8, 14, 24),
	splash = rgb(170, 220, 245), bubble = rgb(220, 240, 255), ink = rgb(40, 34, 40), eye = rgb(250, 250, 248),
	mouth = rgb(110, 40, 40), tile = rgb(186, 214, 222), plaster = rgb(238, 233, 224), floor = rgb(226, 222, 214),
	wood = rgb(176, 132, 92), candle = rgb(240, 232, 210), flame = rgb(255, 190, 90), ray = rgb(255, 236, 170),
	towel = rgb(75, 155, 224), mat = rgb(150, 196, 226),
}

local root, dyn, T, POSE, J = nil, nil, {}, {}, nil
local WATER_TOP = 3.35

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

local function ball(pos, r, colour, opts)
	opts = opts or {}
	opts.shape = Enum.PartType.Ball
	return part(Vector3.new(r * 2, r * 2, r * 2), CFrame.new(pos), colour, opts)
end

local function rod(a, b, r, colour, opts) -- a cylinder from a to b
	opts = opts or {}
	opts.shape = Enum.PartType.Cylinder
	local d = (b - a).Magnitude
	return part(Vector3.new(d, r * 2, r * 2), CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), colour, opts)
end

local function loadModel(id, name)
	local a = InsertService:LoadAsset(id)
	local m = Instance.new("Model")
	m.Name = name
	for _, d in a:GetDescendants() do
		if d:IsA("MeshPart") then
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch = true, false, false, false
			d.Material = Enum.Material.SmoothPlastic
			d.Color = Color3.new(1, 1, 1) -- the vertex colours carry the paint (rbxglb.bake_vertex_colours)
			d.Parent = m
		end
	end
	a:Destroy()
	local cf, size = m:GetBoundingBox()
	m.WorldPivot = CFrame.new(cf.Position - Vector3.new(0, size.Y / 2, 0)) -- the feet, facing -Z (the duck's front)
	return m
end

-- ------------------------------------------------------------------ the rig and its poses
local function newRig(robe)
	local desc = Instance.new("HumanoidDescription")
	local rig = Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	rig.Name = "Player"
	local hum = rig:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	for _, d in rig:GetChildren() do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("BodyColors") then d:Destroy() end
	end
	-- colour by hand (BodyColors would paint whole limbs): in the robe, torso, arms and thighs are robe and the hands,
	-- shins and feet stay skin
	local ROBED = { UpperTorso = true, LowerTorso = true, LeftUpperArm = true, RightUpperArm = true, LeftLowerArm = true,
		RightLowerArm = true, LeftUpperLeg = true, RightUpperLeg = true }
	for _, d in rig:GetChildren() do
		if d:IsA("BasePart") then d.Color = (robe and ROBED[d.Name]) and C.robe or C.skin end
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

-- one keyframe of a Roblox R15 animation, picked by score(fk result) (highest wins)
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
		local s = score and score(fk(map, CFrame.identity)) or -kf.Time
		if s > bestS then best, bestS, bestT = map, s, kf.Time end
	end
	return best, bestT, #kfs
end

local SIZES = {}
local function pose(rig, map, pos, yaw, opts)
	opts = opts or {}
	local rootCF = CFrame.new(pos) * CFrame.Angles(0, yaw or 0, 0) * CFrame.Angles(opts.tilt or 0, 0, 0)
	local cfs = fk(map, rootCF)
	local shift = Vector3.zero
	if opts.ground then -- the lowest foot on the floor
		local low = math.huge
		for _, n in { "LeftFoot", "RightFoot" } do
			low = math.min(low, cfs[n].Position.Y - SIZES[n].Y / 2)
		end
		shift = Vector3.new(0, opts.ground - low, 0)
	elseif opts.hips then
		shift = Vector3.new(0, opts.hips - cfs.LowerTorso.Position.Y, 0)
	end
	for _, d in rig:GetDescendants() do
		if d:IsA("Motor6D") or d:IsA("AnimationConstraint") or d:IsA("Weld") or d:IsA("WeldConstraint") then d:Destroy() end
	end
	for n, cf in cfs do
		local p = rig:FindFirstChild(n)
		if p and p:IsA("BasePart") then
			p.Anchored, p.CanCollide = true, false
			p.CFrame = cf + shift
		end
	end
	rig.HumanoidRootPart.Transparency = 1
	rig.Parent = dyn
	return rig
end

-- the face: the avatar's own dynamic head (FaceControls), so the expressions are the rig's, not stuck-on parts.
--   closed (relaxed, smiling)  open (neutral)  shout (surprise)  cheer (open-mouthed grin)  blank (half lids, flat mouth)
local EXPR = {
	closed = { LeftEyeClosed = 1, RightEyeClosed = 1, LeftLipCornerPuller = 0.55, RightLipCornerPuller = 0.55, LeftCheekRaiser = 0.3, RightCheekRaiser = 0.3 },
	open = {},
	down = { EyesLookDown = 0.8, LeftInnerBrowRaiser = 0.6, RightInnerBrowRaiser = 0.6 },
	shout = { JawDrop = 0.75, LeftEyeUpperLidRaiser = 1, RightEyeUpperLidRaiser = 1, LeftInnerBrowRaiser = 1, RightInnerBrowRaiser = 1, LeftOuterBrowRaiser = 0.8, RightOuterBrowRaiser = 0.8 },
	cheer = { JawDrop = 0.55, LeftLipCornerPuller = 1, RightLipCornerPuller = 1, LeftCheekRaiser = 0.7, RightCheekRaiser = 0.7, LeftEyeClosed = 0.35, RightEyeClosed = 0.35 },
	blank = { LeftEyeClosed = 0.55, RightEyeClosed = 0.55, LipsTogether = 0.4, EyesLookUp = 0.1 },
}
BD.partFaces = false -- true: draw the face as parts on a blank head (if FaceControls do not show in Edit)
local function face(rig, kind)
	local h = rig.Head
	local fc = h:FindFirstChildOfClass("FaceControls")
	if fc and not BD.partFaces then
		for k, v in EXPR[kind] or {} do
			pcall(function() fc[k] = v end)
		end
		return
	end
	if h:IsA("MeshPart") then h.TextureID = "" end
	local front = -h.Size.Z / 2 - 0.02
	local function on(x, y, z) return h.CFrame * CFrame.new(x, y, front + (z or 0)) end
	for _, sx in { -1, 1 } do
		local x = sx * 0.21
		if kind == "closed" then
			part(Vector3.new(0.26, 0.05, 0.05), on(x, 0.1) * CFrame.Angles(0, 0, sx * 0.25), C.ink, { parent = rig })
		else
			part(Vector3.new(0.05, 0.3, 0.3), on(x, 0.1) * CFrame.Angles(0, math.pi / 2, 0), C.eye, { shape = Enum.PartType.Cylinder, parent = rig })
			part(Vector3.new(0.05, 0.12, 0.12), on(x, kind == "blank" and 0.04 or 0.08, -0.02) * CFrame.Angles(0, math.pi / 2, 0), C.ink, { shape = Enum.PartType.Cylinder, parent = rig })
			if kind == "blank" then -- the lid comes down to the middle of the eye, a dark line on its edge
				part(Vector3.new(0.34, 0.17, 0.06), on(x, 0.185, -0.03), C.skin, { parent = rig })
				part(Vector3.new(0.34, 0.04, 0.07), on(x, 0.1, -0.035), C.ink, { parent = rig })
			end
		end
	end
	if kind == "shout" or kind == "cheer" then
		part(Vector3.new(0.05, 0.22, 0.34), on(0, -0.28) * CFrame.Angles(0, math.pi / 2, 0), C.mouth, { shape = Enum.PartType.Cylinder, parent = rig })
	elseif kind == "closed" then
		part(Vector3.new(0.3, 0.05, 0.05), on(0, -0.27), C.ink, { parent = rig })
	else
		part(Vector3.new(0.28, 0.045, 0.05), on(0, -0.27), C.ink, { parent = rig })
	end
end

-- a cap of foam on the head, with or without a tiny duck sitting on top
local function foamHair(rig, withDuck)
	local h = rig.Head.CFrame
	local s = rig.Head.Size.Y
	for _, b in { { 0, 0.62, 0.05, 0.42 }, { -0.36, 0.5, 0.05, 0.32 }, { 0.36, 0.5, 0.05, 0.32 }, { 0, 0.5, 0.36, 0.34 },
		{ -0.2, 0.78, 0.2, 0.28 }, { 0.22, 0.74, -0.15, 0.27 }, { -0.25, 0.55, -0.3, 0.26 }, { 0.3, 0.52, 0.32, 0.25 } } do
		ball((h * CFrame.new(b[1] * s, b[2] * s, b[3] * s)).Position, b[4] * s, C.foam, { parent = rig })
	end
	if withDuck then
		local d = T.army:Clone()
		d:ScaleTo(0.26)
		d:PivotTo(h * CFrame.new(0, 0.98 * s, 0.05))
		d.Parent = rig
	end
end

local function robeBits(rig)
	local lt, ut = rig.LowerTorso, rig.UpperTorso
	part(Vector3.new(lt.Size.X + 0.16, 0.34, lt.Size.Z + 0.16), lt.CFrame, C.belt, { parent = rig })
	part(Vector3.new(0.34, 0.5, 0.16), lt.CFrame * CFrame.new(0.35, -0.2, -lt.Size.Z / 2 - 0.08) * CFrame.Angles(0, 0, 0.3), C.belt, { parent = rig })
	for _, sx in { -1, 1 } do -- the lapels: a V of white trim down the chest
		part(Vector3.new(0.3, 1.5, 0.08), ut.CFrame * CFrame.new(sx * 0.3, 0.05, -ut.Size.Z / 2 - 0.03) * CFrame.Angles(0, 0, -sx * 0.32), C.trim, { parent = rig })
	end
	local legs = rig.LeftUpperLeg.Position.Y - rig.LeftLowerLeg.Position.Y
	if legs > 0.5 then -- standing: the skirt of the robe over the thighs
		part(Vector3.new(2.15, 1.35, 1.15), lt.CFrame * CFrame.new(0, -0.8, 0), C.robe, { parent = rig })
	end
	for _, n in { "LeftLowerArm", "RightLowerArm" } do -- the cuffs
		local a = rig[n]
		part(Vector3.new(a.Size.X + 0.14, 0.28, a.Size.Z + 0.14), a.CFrame * CFrame.new(0, -a.Size.Y / 2 + 0.14, 0), C.trim, { parent = rig })
	end
end

-- ------------------------------------------------------------------ ducks
local function duck(kind, pos, facing, opts)
	opts = opts or {}
	local m = T[kind]:Clone()
	if opts.scale then m:ScaleTo(opts.scale) end
	local look = Vector3.new(facing.X, 0, facing.Z).Unit
	m:PivotTo(CFrame.lookAt(pos, pos + look) * CFrame.Angles(opts.pitch or 0, 0, opts.roll or 0))
	if kind == "giant" then
		local lids = m:FindFirstChild("bd_lids")
		if lids then lids.Transparency = opts.lids and 0 or 1 end
	end
	m.Parent = dyn
	return m
end

local BILL = { giant = Vector3.new(0, 5.8, -3.8), army = Vector3.new(0, 1.42, -0.9) }
local function billOf(m, kind, scale)
	return m:GetPivot() * (BILL[kind] * (scale or 1))
end

local function stream(from, to, r)
	rod(from, to, r, C.splash, { tr = 0.25, shadow = false })
	local dir = (to - from).Unit
	for i = 1, 5 do
		local p = to - dir * (i * 0.3) + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * r * 3
		ball(p, r * (0.5 + math.random() * 0.6), C.splash, { tr = 0.2, shadow = false })
	end
end

local function foamPile(centre, radius, n, rmin, rmax)
	for i = 1, n do
		local a = i * 2.39996
		local d = radius * math.sqrt(i / n)
		ball(centre + Vector3.new(math.cos(a) * d, (math.random() - 0.3) * 0.3, math.sin(a) * d), rmin + math.random() * (rmax - rmin), C.foam)
	end
end

local function unfoam(r)
	local p = dyn:FindFirstChild("Player")
	if not p then return end
	local h = p.Head.Position
	for _, b in dyn:GetChildren() do
		if b:IsA("Part") and b.Shape == Enum.PartType.Ball and b.Transparency == 0 then
			local d = b.Position - h
			if Vector3.new(d.X, 0, d.Z).Magnitude < r and b.Position.Y > h.Y - 2.2 and d.Z > -1.5 then b:Destroy() end
		end
	end
end

local function bubbles(n, lo, hi)
	for _ = 1, n do
		local p = lo + (hi - lo) * Vector3.new(math.random(), math.random(), math.random())
		ball(p, 0.2 + math.random() * 0.6, C.bubble, { tr = 0.55, refl = 0.25, shadow = false })
	end
end

-- ------------------------------------------------------------------ the bathroom (static for every panel)
local tub, water
local function room()
	local s = { parent = root, shadow = true }
	part(Vector3.new(46, 1, 42), CFrame.new(L(0, -0.5, 4)), C.floor, { parent = root, mat = Enum.Material.CeramicTiles })
	part(Vector3.new(46, 1, 42), CFrame.new(L(0, 20.5, 4)), C.plaster, { parent = root, mat = Enum.Material.Plaster })
	for _, w in { { Vector3.new(46, 21, 1), L(0, 10, -14.5) }, { Vector3.new(46, 21, 1), L(0, 10, 25.5) },
		{ Vector3.new(1, 21, 42), L(-23.5, 10, 4) }, { Vector3.new(1, 21, 42), L(23.5, 10, 4) } } do
		part(w[1] - Vector3.new(0, 12, 0), CFrame.new(w[2] - Vector3.new(0, 6, 0)), C.tile, { parent = root, mat = Enum.Material.CeramicTiles })
		part(w[1] - Vector3.new(0, 9, 0), CFrame.new(w[2] + Vector3.new(0, 4.5, 0)), C.plaster, { parent = root, mat = Enum.Material.Plaster })
	end
	part(Vector3.new(46, 0.4, 0.5), CFrame.new(L(0, 8.6, -13.9)), C.trim, s) -- the tile cap rail on the back wall
	part(Vector3.new(0.5, 0.4, 42), CFrame.new(L(-22.9, 8.6, 4)), C.trim, s)
	part(Vector3.new(0.5, 0.4, 42), CFrame.new(L(22.9, 8.6, 4)), C.trim, s)
	-- a towel rail with a folded towel, a shelf, a bath mat
	part(Vector3.new(5, 0.3, 0.3), CFrame.new(L(12, 7.2, -13.6)), C.trim, s)
	part(Vector3.new(3.6, 4.2, 0.5), CFrame.new(L(12, 5.2, -13.45)), C.towel, s)
	part(Vector3.new(3.6, 0.6, 0.55), CFrame.new(L(12, 3.4, -13.45)), C.trim, s)
	part(Vector3.new(6, 0.4, 1.4), CFrame.new(L(-12, 7, -13.3)), C.wood, s)
	part(Vector3.new(8, 0.15, 3.6), CFrame.new(L(-1, 0.07, -3.6)), C.mat, s)
	-- light: a ceiling panel and warm candles
	local lamp = part(Vector3.new(10, 0.3, 6), CFrame.new(L(0, 20, -2)), Color3.new(1, 1, 1), { parent = root, mat = Enum.Material.Neon })
	local sl = Instance.new("SurfaceLight"); sl.Face = Enum.NormalId.Bottom; sl.Range = 32; sl.Brightness = 0.35; sl.Angle = 120; sl.Parent = lamp
	for _, c in { { -7.6, 1.5, -5.6 }, { -8.6, 1.0, -6.6 }, { -6.7, 1.9, -6.9 }, { 7.7, 1.2, -5.7 } } do
		local h = c[2]
		part(Vector3.new(h, 0.7, 0.7), CFrame.new(L(c[1], h / 2, c[3])) * CFrame.Angles(0, 0, math.pi / 2), C.candle, { parent = root, shape = Enum.PartType.Cylinder })
		local f = part(Vector3.new(0.22, 0.4, 0.22), CFrame.new(L(c[1], h + 0.25, c[3])), C.flame, { parent = root, mat = Enum.Material.Neon, shadow = false })
		local fl = Instance.new("PointLight"); fl.Range = 9; fl.Brightness = 0.6; fl.Color = rgb(255, 196, 120); fl.Parent = f
	end
	-- the tub, its water
	tub = T.tub:Clone()
	tub:PivotTo(CFrame.new(L(0, 0, -9)))
	tub.Parent = root
	water = tub:FindFirstChild("bd_water")
	WATER_TOP = water.Position.Y - O.Y + water.Size.Y / 2
	water.CastShadow = false
end

-- ------------------------------------------------------------------ the camera (a 16:9 band of the viewport keeps `fov`)
local saved
local function shot(eye, look, fov, roll)
	local cam = workspace.CurrentCamera
	saved = saved or { cam.CFrame, cam.FieldOfView }
	cam.CameraType = Enum.CameraType.Scriptable
	local vs = cam.ViewportSize
	cam.FieldOfView = math.deg(2 * math.atan(math.tan(math.rad(fov) / 2) * vs.Y / (vs.X * 9 / 16)))
	cam.CFrame = CFrame.lookAt(L(eye[1], eye[2], eye[3]), L(look[1], look[2], look[3])) * CFrame.Angles(0, 0, math.rad(roll or 0))
end

local function setWater(colour, tr)
	water.Color, water.Transparency = colour, tr
end

-- ------------------------------------------------------------------ the nine panels
-- each panel's lens: eye, look-at (stage coords), FOV of the 16:9 band, roll (deg). patch BD.CAM[n] live to reframe
BD.CAM = {
	[1] = { { -2.4, 5.4, 1.0 }, { -3.0, 4.5, -9 }, 38, 0 },
	[2] = { { 5.0, 4.75, -7.4 }, { -2.6, 3.7, -9.3 }, 52, 0 },
	[3] = { { -2.2, 2.9, 0.2 }, { 2.0, 7.6, -9.2 }, 64, -4 },
	[4] = { { 0, 3, 8 }, { -2, 1.2, -0.5 }, 58, 0 },
	[5] = { { 0.9, 4.2, 14.5 }, { 0.9, 4.0, -1.5 }, 50, 0 },
	[6] = { { 1.0, 5.6, 10.5 }, { 1.0, 5.0, -1.5 }, 44, 0 },
	[7] = { { 1.0, 4.6, 8.5 }, { 1.0, 4.3, -1.5 }, 64, 6 },
	[9] = { { 0.9, 3.9, 10.5 }, { 1.2, 4.9, -1.5 }, 54, 0 },
}
local function camFor(n)
	local c = BD.CAM[n]
	shot(c[1], c[2], c[3], c[4])
end

local P = {}
local SIT_HIPS = function() return WATER_TOP - 1.1 end
local function bather(kind, hair)
	local r = newRig(false)
	pose(r, POSE.sit, L(-3.2, 0, -9), math.pi, { tilt = 0.32, hips = O.Y + SIT_HIPS() }) -- facing the lens, leaning back
	face(r, kind)
	foamHair(r, hair)
	return r
end

P[1] = function() -- peaceful bath time: slow push-in
	setWater(C.water, 0.25)
	bather("closed", true)
	foamPile(L(-2.6, WATER_TOP, -8.6), 3.4, 46, 0.35, 0.8)
	foamPile(L(2.8, WATER_TOP, -9.2), 2.2, 18, 0.3, 0.6)
	bubbles(8, L(-6, WATER_TOP + 0.5, -11), L(2, WATER_TOP + 5, -7))
	unfoam(2.2)
	camFor(1)
end

P[2] = function() -- something beneath: the water darkens, a duck-shaped shadow slides in under the player
	setWater(C.waterDark, 0.5)
	bather("down", true)
	foamPile(L(-3.4, WATER_TOP, -8.4), 1.8, 16, 0.3, 0.6)
	local g = T.giant:Clone()
	local main = g:FindFirstChild("bd_giant")
	local sh = main:Clone()
	sh.Size = Vector3.new(main.Size.X * 0.6, main.Size.Y * 0.6, 0.3)
	sh.Color, sh.CastShadow = C.shadow, false
	-- lying flat just under the surface, head toward the player (up -> -X, face down)
	sh.CFrame = CFrame.fromMatrix(L(0.6, WATER_TOP - 0.3, -9), Vector3.new(0, 0, -1), Vector3.new(-1, 0, 0), Vector3.new(0, 1, 0))
	sh.Parent = dyn
	g:Destroy()
	unfoam(1.6)
	camFor(2)
end

P[3] = function() -- the reveal: the giant erupts, splash and light rays, camera low and rising
	setWater(C.water, 0.2)
	bather("shout", false)
	local g = duck("giant", L(2.4, 1.7, -9.2), Vector3.new(0, 0, 1)) -- the feet stay inside the tub
	local c = L(2.4, WATER_TOP, -9.2)
	for i = 0, 13 do -- a crown of water round the waist
		local a = i / 14 * math.pi * 2
		local dir = Vector3.new(math.cos(a), 0, math.sin(a))
		for k = 0, 3 do
			ball(c + dir * (3.2 + k * 0.9) + Vector3.new(0, 0.5 + k * 1.1 - k * k * 0.18, 0), 0.75 - k * 0.14, C.splash, { tr = 0.18 })
		end
	end
	for _ = 1, 40 do
		local a = math.random() * math.pi * 2
		local d = 2 + math.random() * 6
		ball(c + Vector3.new(math.cos(a) * d, 1 + math.random() * 8, math.sin(a) * d * 0.7), 0.15 + math.random() * 0.35, C.splash, { tr = 0.15, shadow = false })
	end
	foamPile(c + Vector3.new(0, 0.2, 0), 4.5, 30, 0.35, 0.8)
	local head = L(2.4, 8.2, -10.5)
	for i = -3, 3 do -- light rays fanning up from behind the head
		local a = i * 0.32
		local dir = Vector3.new(math.sin(a), math.cos(a), -0.15).Unit
		part(Vector3.new(0.6, 30, 0.1), CFrame.lookAt(head, head + Vector3.new(0, 0, -1), dir) * CFrame.new(0, 15, 0),
			C.ray, { mat = Enum.Material.Neon, tr = 0.9, shadow = false })
	end
	camFor(3)
end

local MARCH = { { -1, -2.4 }, { -3.4, -1.0 }, { -5.8, -2.4 }, { -8.2, -1.0 }, { -10.6, -2.4 }, { -13, -1.0 }, { -15.4, -2.4 }, { -17.8, -1.0 } }
P[4] = function() -- the duck march, tracked from the side
	setWater(C.water, 0.25)
	bather("open", true)
	foamPile(L(-2.6, WATER_TOP, -8.6), 3.0, 30, 0.3, 0.7)
	unfoam(1.6)
	duck("giant", L(5.5, 0, -1.7), Vector3.new(1, 0, 0), { roll = math.rad(5) })
	for i, m in MARCH do
		duck("army", L(m[1] + 1.2, 0, m[2] + 1.0), Vector3.new(1, 0, 0), { roll = math.rad(i % 2 == 0 and 9 or -9) })
	end
	camFor(4)
end

local FRONT = { -8, -5.8, -3.6, 1.0, 5.2, 7.4, 9.6 }
local BACK = { -9.8, -6.9, 8.1, 11 }
local function lineUp(lids, robe)
	local p = newRig(true)
	pose(p, POSE.idle, L(-1.2, 0, -1.2), math.pi, { ground = O.Y })
	robeBits(p)
	foamHair(p, false)
	local g = duck("giant", L(3.6, 0, -2.6), Vector3.new(0, 0, 1), { lids = lids })
	local army = {}
	for _, x in FRONT do table.insert(army, duck("army", L(x, 0, 1.8), Vector3.new(0, 0, 1))) end
	for _, x in BACK do table.insert(army, duck("army", L(x, 0, -2.4), Vector3.new(0, 0, 1))) end
	return p, g, army
end

P[5] = function() -- formation: everyone stops and lines up facing the camera
	setWater(C.water, 0.25)
	local p = lineUp(false)
	face(p, "open")
	camFor(5)
end

P[6] = function() -- the stare: dead silent, every face half-lidded, slow push-in
	setWater(C.water, 0.25)
	local p = lineUp(true)
	face(p, "blank")
	camFor(6)
end

P[7] = function() -- the water attack: everyone squirts at the lens, quick zoom and shake
	setWater(C.water, 0.25)
	local p = newRig(true)
	pose(p, POSE.point, L(-1.2, 0, -1.2), math.pi, { ground = O.Y })
	robeBits(p)
	foamHair(p, false)
	face(p, "blank")
	local e = BD.CAM[7][1]
	local eye = L(e[1], e[2], e[3])
	local function target() return eye + Vector3.new((math.random() - 0.5) * 2.4, (math.random() - 0.5) * 1.6, -1.2) end
	-- the player squeezes a rubber duck at the lens: in the pointing hand, bill forward
	local hand = p.RightHand.CFrame
	local toy = duck("army", hand.Position + Vector3.new(0, -0.35, 0.2), Vector3.new(0, 0, 1), { scale = 0.38 })
	stream(billOf(toy, "army", 0.38), target(), 0.14)
	local g = duck("giant", L(3.6, 0, -2.6), Vector3.new(0, 0, 1), { lids = true })
	stream(billOf(g, "giant"), target(), 0.45)
	for _, x in FRONT do
		local d = duck("army", L(x, 0, 1.8), Vector3.new(0, 0, 1))
		stream(billOf(d, "army"), target(), 0.18)
	end
	for _, x in BACK do duck("army", L(x, 0, -2.4), Vector3.new(0, 0, 1)) end
	for _, b in dyn:GetChildren() do
		if b:IsA("Part") and b.Shape == Enum.PartType.Ball and (b.Position - eye).Magnitude < 3.6 then
			b:Destroy()
		elseif b:IsA("Part") and b.Shape == Enum.PartType.Cylinder then
			local a = b.CFrame * Vector3.new(-b.Size.X / 2, 0, 0)
			local e2 = b.CFrame * Vector3.new(b.Size.X / 2, 0, 0)
			if (a - eye).Magnitude < (e2 - eye).Magnitude then a, e2 = e2, a end
			local len = math.max(1, (e2 - a).Magnitude - 1.4)
			e2 = a + (e2 - a).Unit * len
			b.Size = Vector3.new(len, b.Size.Y * 0.8, b.Size.Z * 0.8)
			b.CFrame = CFrame.lookAt((a + e2) / 2, e2) * CFrame.Angles(0, math.pi / 2, 0)
			b.Transparency = 0.3
		end
	end
	camFor(7)
end

P[8] = P[7] -- the soak is a lens pass over panel 7's frame (duck_board_sheet.py), same staging

P[9] = function() -- the end card: the player cheers among the ducks and bubbles
	setWater(C.water, 0.25)
	local p = newRig(true)
	pose(p, POSE.cheer, L(-1.4, 0, 0), math.pi, { ground = O.Y })
	robeBits(p)
	foamHair(p, true)
	face(p, "cheer")
	duck("giant", L(4.2, 0, -3.2), Vector3.new(-0.25, 0, 1), { roll = math.rad(-4) })
	for _, d in { { -6.2, 1.6, 0.4 }, { -4.6, -2.2, 0.2 }, { 1.8, 2.4, -0.3 }, { 7.6, 1.6, -0.4 }, { 9.2, -1.2, -0.2 }, { -8.2, -1.0, 0.5 } } do
		duck("army", L(d[1], 0, d[2]), Vector3.new(d[3], 0, 1), { roll = math.rad(d[3] * 12) })
	end
	bubbles(34, L(-12, 1.5, -6), L(13, 13, 4))
	camFor(9)
end

-- ------------------------------------------------------------------ build / panel / clear
function BD.build()
	BD.clear(true)
	math.randomseed(19)
	root = Instance.new("Folder")
	root.Name = "BathDuckyBoard"
	T.giant = loadModel(IDS.giant, "BathDucky")
	T.army = loadModel(IDS.army, "ArmyDuck")
	T.tub = loadModel(IDS.tub, "Tub")
	local probe = newRig(false)
	J = joints(probe)
	for _, d in probe:GetChildren() do
		if d:IsA("BasePart") then SIZES[d.Name] = d.Size end
	end
	local info = {}
	POSE.sit = pickPose("sit")
	local hands = function(cfs) return cfs.LeftHand.Position.Y + cfs.RightHand.Position.Y end
	local reach = function(cfs) return -(cfs.RightHand.Position.Z) + cfs.RightHand.Position.Y * 0.3 end
	local t1, t2
	POSE.idle = pickPose("idle")
	POSE.cheer, t1 = pickPose("cheer", hands)
	POSE.point, t2 = pickPose("point", reach)
	probe:Destroy()
	dyn = Instance.new("Folder")
	dyn.Name = "Panel"
	dyn.Parent = root
	root.Parent = workspace
	room()
	local names = {}
	for _, k in { "giant", "army", "tub" } do
		for _, d in T[k]:GetChildren() do table.insert(names, k .. ":" .. d.Name .. string.format("(%.1f,%.1f,%.1f)", d.Size.X, d.Size.Y, d.Size.Z)) end
	end
	local nj = 0
	for _ in J do nj += 1 end
	return string.format("built: water top %.2f, cheer at %.2fs, point at %.2fs, joints %d, head %s | %s", WATER_TOP, t1, t2, nj, tostring(SIZES.Head), table.concat(names, " "))
end

function BD.dry() -- read-only: load and measure everything, parent nothing
	local out = {}
	for k, id in IDS do
		local m = loadModel(id, k)
		local _, size = m:GetBoundingBox()
		local names = {}
		for _, d in m:GetChildren() do table.insert(names, d.Name) end
		table.insert(out, string.format("%s %.1fx%.1fx%.1f [%s]", k, size.X, size.Y, size.Z, table.concat(names, ",")))
		m:Destroy()
	end
	local probe = newRig(true)
	J = joints(probe)
	local nj, kinds = 0, {}
	for _, j in J do nj += 1 end
	for _, d in probe:GetDescendants() do
		if d:IsA("Motor6D") or d:IsA("AnimationConstraint") then kinds[d.ClassName] = true end
		if d:IsA("BasePart") then SIZES[d.Name] = d.Size end
	end
	local hands = function(cfs) return cfs.LeftHand.Position.Y + cfs.RightHand.Position.Y end
	local reach = function(cfs) return -(cfs.RightHand.Position.Z) + cfs.RightHand.Position.Y * 0.3 end
	local _, t1, n1 = pickPose("cheer", hands)
	local _, t2, n2 = pickPose("point", reach)
	local _, _, n3 = pickPose("sit")
	local _, _, n4 = pickPose("idle")
	local kl = {}
	for k in kinds do table.insert(kl, k) end
	table.insert(out, string.format("rig joints %d (%s) head %s; cheer %.2fs of %d kfs, point %.2fs of %d, sit %d kfs, idle %d",
		nj, table.concat(kl, ","), tostring(SIZES.Head), t1, n1, t2, n2, n3, n4))
	probe:Destroy()
	return table.concat(out, "\n")
end

function BD.panel(n)
	math.randomseed(100 + n)
	dyn:ClearAllChildren()
	P[n]()
	game:GetService("Selection"):Set({})
	return "panel " .. n .. " staged"
end

function BD.clear(keepCamera)
	local old = workspace:FindFirstChild("BathDuckyBoard")
	while old do
		old:Destroy()
		old = workspace:FindFirstChild("BathDuckyBoard")
	end
	if saved and not keepCamera then
		local cam = workspace.CurrentCamera
		cam.CFrame, cam.FieldOfView = saved[1], saved[2]
		saved = nil
	end
	return "cleared"
end

return "BD ready"
