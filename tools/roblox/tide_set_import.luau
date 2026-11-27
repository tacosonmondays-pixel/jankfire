-- (Edit, execute_luau) TIDECREST'S NIGHT WATERFALL SET into ReplicatedStorage.JankfireFinisherSets.TideWaterfall, for
-- client/FinisherPro.luau (26 Nov 2026; the owner: "make a demo set thats a nighttime japanese waterfall, treeline, and a
-- big moon makethe water pretty!"). The kit upload (tools/roblox/tide_waterfall.py, a Model under the owner's account)
-- painted from its pieces' names and pivoted on its origin marker (the floor under the killer's start), and what the kit
-- can't carry built here from the builder's tide_waterfall.json (copied into FX below): the falls (two Beam sheets each,
-- our own streak textures scrolling down), the spray and mist at their feet, foam rings, the lanterns' light, the moon
-- (a disc with its darker seas and a halo), the water, the moon's glitter road on the pool, and SceneLook - the Sky,
-- Atmosphere, Bloom and grade FinisherPro puts on for the scene (the place's own parked meanwhile).
local SET = 136826456466581 -- (the kit upload: tide_waterfall.glb v3, 26 Nov 2026 - the causeway through the pool, wide curtains, darker values; v2 88285832941384, v1 99855924480330)
local TEX = { streaks = "rbxassetid://86884977470079", streaks2 = "rbxassetid://74489285829676", ripple = "rbxassetid://111226912715998" }
local SMOKE = "rbxasset://textures/particles/smoke_main.dds"
local SPARK = "rbxasset://textures/particles/sparkles_main.dds"
local FX = {
	falls = {
		{ top = { -48.5, 7.2, 170.4 }, bottom = { -48.5, -1.3, 167 }, width = 15, face = { 0, 0, -1 } },
		{ top = { -23.5, 7.2, 170.4 }, bottom = { -23.5, -1.3, 167 }, width = 20, face = { 0, 0, -1 } },
		{ top = { 5.5, 7.2, 170.4 }, bottom = { 5.5, -1.3, 167 }, width = 15, face = { 0, 0, -1 } },
		{ top = { -117, 34.4, -22 }, bottom = { -113.5, -1.3, -22 }, width = 10, face = { 1, 0, 0 } },
		{ top = { -117, 34.4, -11 }, bottom = { -113.5, -1.3, -11 }, width = 7, face = { 1, 0, 0 } },
		{ top = { -138.5, 73.8, -17.5 }, bottom = { -135.5, 34.6, -17.5 }, width = 9, face = { 1, 0, 0 } },
	},
	mist = {
		{ at = { -20, -0.3, 166 }, size = { 80, 8 } },
		{ at = { -112, -0.3, -16 }, size = { 24, 9 } },
		{ at = { -132, 35, -16 }, size = { 16, 6 } },
	},
	foam = {
		{ at = { -20, -1.3, 165 }, r = 40, line = true },
		{ at = { -110, -1.3, -16 }, r = 14, line = false },
	},
	lanterns = { { -9, 5.225, -8 }, { 11, 5.225, -30 }, { -9, 5.225, -60 }, { 11, 5.225, 12 } },
	moon = { dir = { -0.068, 0.208, 0.976 }, dist = 1700, deg = 16 },
	water = { y = -1.3, boxes = { { -150, 20, -5.7, -120 }, { 7.7, 20, 36, -120 }, { -150, 172, 80, 18 } }, upper = { y = 7.5, box = { -150, 420, 80, 174 } } },
	glitter = { from = { -27.971, 400 }, to = { -1.678, 24 }, width = 9 },
}
local IS = game:GetService("InsertService")
local RS = game:GetService("ReplicatedStorage")
local sets = RS:FindFirstChild("JankfireFinisherSets")
if not sets then sets = Instance.new("Folder"); sets.Name = "JankfireFinisherSets"; sets.Parent = RS end
local function mat(n) local ok, m = pcall(function() return (Enum.Material :: any)[n] end); return if ok and m then m else Enum.Material.SmoothPlastic end
local KIND = { rock = mat("Slate"), stone = mat("Granite"), leaf = mat("Grass"), wood = mat("Wood"), neon = mat("Neon"), plastic = mat("SmoothPlastic"),
	glass = mat("Glass"), cloud = mat("SmoothPlastic"), mist = mat("SmoothPlastic") }
local root = IS:LoadAsset(SET)
local src = root:FindFirstChildWhichIsA("Model") or root
local set = Instance.new("Model")
set.Name = "TideWaterfall"
local origin = nil
local n = 0
for _, p in src:GetDescendants() do
	if p:IsA("BasePart") then
		local kind, hex = string.match(p.Name, "__(%a+)_(%x%x%x%x%x%x)$")
		if kind then p.Color = Color3.fromHex(hex); p.Material = KIND[kind] or Enum.Material.SmoothPlastic end
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.CastShadow = not (string.match(p.Name, "^mountains") or string.match(p.Name, "^clouds") or string.match(p.Name, "^mistmounds"))
		if kind == "mist" then p.Transparency = 0.62 end -- (the soft mounds of mist where the falls land)
		if string.sub(p.Name, 1, 9) == "kitorigin" then origin = p else n += 1 end
	end
end
assert(origin, "no origin marker")
local O = CFrame.new(origin.Position + Vector3.new(0, 60, 0)) -- (the kit's floor origin, where it came in)
for _, p in src:GetDescendants() do if p:IsA("BasePart") and p ~= origin then p.Parent = set end end
origin:Destroy()
root:Destroy()
-- (everything below is placed in kit space through O, then the whole set is moved to the world origin)
local function at(x, y, z) return O * CFrame.new(x, y, z) end
local fx = Instance.new("Folder"); fx.Name = "Fx"; fx.Parent = set
local function anchor(name, cf, size)
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size or Vector3.new(0.2, 0.2, 0.2); p.CFrame = cf; p.Parent = fx
	return p
end
local function num(a, b) return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) }) end
local WATER_C = Color3.fromRGB(214, 230, 248)
-- the falls
for i, f in FX.falls do
	local top, bot = Vector3.new(table.unpack(f.top)), Vector3.new(table.unpack(f.bottom))
	local p = anchor("Fall" .. i, at(top.X, top.Y, top.Z))
	local a0 = Instance.new("Attachment"); a0.Parent = p
	local a1 = Instance.new("Attachment"); a1.WorldPosition = (O * CFrame.new(bot)).Position; a1.Parent = p
	for layer = 1, 2 do
		local b = Instance.new("Beam")
		b.Name = "Sheet" .. layer
		b.Attachment0, b.Attachment1 = a0, a1
		b.FaceCamera = true
		b.Texture = if layer == 1 then TEX.streaks else TEX.streaks2
		b.TextureMode = Enum.TextureMode.Wrap
		b.TextureLength = if layer == 1 then 7 else 11
		b.TextureSpeed = if layer == 1 then 1.1 else 1.8
		b.Width0 = f.width * (if layer == 1 then 1 else 0.7)
		b.Width1 = f.width * (if layer == 1 then 1.18 else 0.85)
		b.Color = ColorSequence.new(WATER_C)
		b.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(0.08, if layer == 1 then 0.05 else 0.35),
			NumberSequenceKeypoint.new(0.85, if layer == 1 then 0.12 else 0.4), NumberSequenceKeypoint.new(1, 0.6) })
		b.LightEmission = if layer == 1 then 0.25 else 0.6
		b.LightInfluence = if layer == 1 then 0.7 else 0.4
		b.Segments = 8
		b.ZOffset = layer * 0.1
		b.Parent = p
	end
	-- the spray where it lands
	local sp = anchor("Spray" .. i, at(bot.X, bot.Y + 0.5, bot.Z), Vector3.new(f.width, 0.2, f.width * 0.6))
	local e = Instance.new("ParticleEmitter")
	e.Texture = SMOKE; e.Color = ColorSequence.new(Color3.fromRGB(222, 234, 248))
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, f.width * 0.5), NumberSequenceKeypoint.new(1, f.width * 1.4) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, 0.6), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(1.2, 2.4); e.Rate = 6 + f.width * 3; e.Speed = NumberRange.new(2, 5)
	e.SpreadAngle = Vector2.new(35, 35); e.EmissionDirection = Enum.NormalId.Top; e.Acceleration = Vector3.new(0, -1.5, 0); e.Drag = 1.2
	e.Shape = Enum.ParticleEmitterShape.Box; e.LightEmission = 0.15; e.LightInfluence = 0.8; e.RotSpeed = NumberRange.new(-20, 20); e.Rotation = NumberRange.new(0, 360)
	e.Parent = sp
end
-- the mist lying over the falls' pools
for i, m in FX.mist do
	local p = anchor("Mist" .. i, at(m.at[1], m.at[2] + m.size[2] * 0.25, m.at[3]), Vector3.new(m.size[1], m.size[2] * 0.5, m.size[1] * 0.35))
	local e = Instance.new("ParticleEmitter")
	e.Texture = SMOKE; e.Color = ColorSequence.new(Color3.fromRGB(188, 204, 232))
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 10), NumberSequenceKeypoint.new(1, 22) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.8), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(6, 10); e.Rate = math.max(3, m.size[1] / 8); e.Speed = NumberRange.new(0.3, 1.1)
	e.SpreadAngle = Vector2.new(70, 70); e.Shape = Enum.ParticleEmitterShape.Box; e.LightInfluence = 1; e.RotSpeed = NumberRange.new(-6, 6)
	e.Rotation = NumberRange.new(0, 360); e.Parent = p
end
-- foam: soft rings spreading on the water
for i, m in FX.foam do
	local sz = if m.line then Vector3.new(m.r * 2, 0.1, 5) else Vector3.new(m.r, 0.1, m.r)
	local p = anchor("Foam" .. i, at(m.at[1], m.at[2] + 0.06, m.at[3]), sz)
	local e = Instance.new("ParticleEmitter")
	e.Texture = TEX.ripple; e.Color = ColorSequence.new(Color3.fromRGB(226, 236, 250))
	e.Orientation = Enum.ParticleOrientation.VelocityPerpendicular; e.EmissionDirection = Enum.NormalId.Top; e.Speed = NumberRange.new(0.02)
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.5), NumberSequenceKeypoint.new(1, 7) })
	e.Transparency = num(0.45, 1); e.Lifetime = NumberRange.new(1.4, 2.6); e.Rate = if m.line then 22 else 8
	e.Shape = Enum.ParticleEmitterShape.Box; e.LightInfluence = 0.7; e.LightEmission = 0.2; e.Rotation = NumberRange.new(0, 360)
	e.Parent = p
end
-- the lanterns' warm light (the scene's one accent)
for i, l in FX.lanterns do
	local p = anchor("Lantern" .. i, at(l[1], l[2], l[3]))
	local pl = Instance.new("PointLight"); pl.Color = Color3.fromRGB(255, 194, 128); pl.Brightness = 2.2; pl.Range = 18; pl.Shadows = true; pl.Parent = p
end
-- the moon: a big pale disc low over the cascade, its seas a little darker, a faint halo round it
local md = Vector3.new(table.unpack(FX.moon.dir)).Unit
local mp = md * FX.moon.dist
local D = 2 * FX.moon.dist * math.tan(math.rad(FX.moon.deg / 2))
local face = CFrame.lookAt((O * CFrame.new(mp)).Position, O.Position) * CFrame.Angles(0, math.rad(90), 0) -- (a cylinder's axis is its X)
local moon = Instance.new("Model"); moon.Name = "Moon"; moon.Parent = set
local function disc(name, d, back, col, tr, mat_)
	local p = Instance.new("Part"); p.Name = name; p.Shape = Enum.PartType.Cylinder; p.Anchored = true; p.CanCollide = false; p.CanQuery = false
	p.CanTouch = false; p.CastShadow = false; p.Size = Vector3.new(1, d, d); p.CFrame = face * CFrame.new(back, 0, 0)
	p.Color = col; p.Material = mat_ or Enum.Material.Neon; p.Transparency = tr; p.Parent = moon
	return p
end
-- (v1373: the first disc blew out white under the night's exposure, seas and all: a dimmer moon, darker seas)
disc("Disc", D, 0, Color3.fromRGB(172, 166, 148), 0)
local rnd = Random.new(17)
-- (the seas: three soft overlapping patches a little darker than the disc, in front of it - the disc's +X faces the
-- lane; the first cut put five round dark spots behind it, then in front they read as a paw print. The halos behind)
for k, s in { { 0.16, -0.1, 0.42, 0.62 }, { -0.18, 0.08, 0.32, 0.68 }, { 0.02, 0.24, 0.22, 0.72 } } do
	local sea = disc("Sea" .. k, D * s[3], 0.8, Color3.fromRGB(150, 145, 128), s[4])
	sea.Size = Vector3.new(0.5, D * s[3], D * s[3] * 0.82)
	sea.CFrame = face * CFrame.new(0.8, s[2] * D, s[1] * D) * CFrame.Angles(math.rad(25 * k), 0, 0)
end
disc("Halo", D * 1.5, -4, Color3.fromRGB(120, 140, 196), 0.975)
disc("Halo2", D * 2.3, -6, Color3.fromRGB(90, 110, 170), 0.99)
local W = Instance.new("Model"); W.Name = "Water"; W.Parent = set
local function water(x0, z0, x1, z1, y)
	local p = Instance.new("Part"); p.Name = "Water"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.CastShadow = false; p.Material = Enum.Material.Glass; p.Color = Color3.fromRGB(34, 58, 96); p.Transparency = 0.18; p.Reflectance = 0.35
	p.Size = Vector3.new(math.abs(x1 - x0), 0.6, math.abs(z1 - z0))
	p.CFrame = at((x0 + x1) / 2, y - 0.3, (z0 + z1) / 2); p.Parent = W
end
for _, b in FX.water.boxes do water(b[1], b[2], b[3], b[4], FX.water.y) end
local ub = FX.water.upper.box
water(ub[1], ub[2], ub[3], ub[4], FX.water.upper.y)
do
	local g = FX.glitter
	local a, b = Vector3.new(g.from[1], 0, g.from[2]), Vector3.new(g.to[1], 0, g.to[2])
	-- (the road runs from the cascade to the terrace; the far part on the lake above is the upper level)
	for _, seg in { { a:Lerp(b, 0.42), b, FX.water.y }, { a, a:Lerp(b, 0.42), FX.water.upper.y } } do
		local p0, p1, y = seg[1], seg[2], seg[3]
		local mid, len = (p0 + p1) / 2, (p1 - p0).Magnitude
		local cf = CFrame.lookAt(Vector3.new(mid.X, 0, mid.Z), Vector3.new(p1.X, 0, p1.Z))
		local road = anchor("MoonRoad", O * CFrame.new(0, y + 0.05, 0) * cf, Vector3.new(g.width, 0.1, len))
		local e = Instance.new("ParticleEmitter")
		e.Texture = SPARK; e.Color = ColorSequence.new(Color3.fromRGB(255, 244, 220))
		e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 1.1), NumberSequenceKeypoint.new(1, 0) })
		e.Transparency = num(0.1, 0.6); e.Lifetime = NumberRange.new(0.25, 0.7); e.Rate = len * 1.6; e.Speed = NumberRange.new(0)
		e.Shape = Enum.ParticleEmitterShape.Box; e.LightEmission = 1; e.LightInfluence = 0; e.ZOffset = 0.3; e.Parent = road
		local sheen = Instance.new("Part"); sheen.Name = "MoonSheen"; sheen.Anchored = true; sheen.CanCollide = false; sheen.CanQuery = false
		sheen.CanTouch = false; sheen.CastShadow = false; sheen.Material = Enum.Material.Neon; sheen.Color = Color3.fromRGB(120, 132, 168)
		sheen.Transparency = 0.8; sheen.Size = Vector3.new(g.width * 0.8, 0.05, len); sheen.CFrame = road.CFrame * CFrame.new(0, 0.02, 0); sheen.Parent = W
	end
end
-- the scene's own look: FinisherPro clones these into Lighting for the scene (the place's own parked meanwhile)
local look = Instance.new("Folder"); look.Name = "SceneLook"; look.Parent = set
local sky = Instance.new("Sky"); sky.Name = "SceneSky"; sky.StarCount = 3000; sky.CelestialBodiesShown = false; sky.Parent = look
local atmo = Instance.new("Atmosphere"); atmo.Name = "SceneAtmo"; atmo.Density = 0.3; atmo.Offset = 0.12
atmo.Color = Color3.fromRGB(96, 114, 164); atmo.Decay = Color3.fromRGB(52, 62, 104); atmo.Glare = 0; atmo.Haze = 1.4; atmo.Parent = look
local bloom = Instance.new("BloomEffect"); bloom.Name = "SceneBloom"; bloom.Intensity = 0.9; bloom.Size = 30; bloom.Threshold = 0.9; bloom.Parent = look
local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "SceneGrade"; cc.TintColor = Color3.fromRGB(230, 238, 255); cc.Contrast = 0.1
cc.Saturation = -0.04; cc.Brightness = 0.02; cc.Parent = look
-- (the set sits with its floor origin at the world's origin: FinisherPro pivots it onto the scene's spot)
set.WorldPivot = O
set:PivotTo(CFrame.new())
local old = sets:FindFirstChild("TideWaterfall"); if old then old:Destroy() end
set.Parent = sets
local beams, emitters = 0, 0
for _, d in set:GetDescendants() do if d:IsA("Beam") then beams += 1 elseif d:IsA("ParticleEmitter") then emitters += 1 end end
return string.format("TideWaterfall: %d kit pieces, %d beams, %d emitters, moon %.0f studs across at %.0f", n, beams, emitters, D, FX.moon.dist)
