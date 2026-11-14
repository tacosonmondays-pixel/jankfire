--!strict
-- the step 2 effects, all on the client, moved every frame (never server-stepped: the owner's "the bits spitting out
-- are clunky" note). each looks for its Blender mesh in ReplicatedStorage.JankfireFX (fx_flash_star, fx_tracer,
-- fx_casing, fx_marble, fx_spark, fx_impact, fx_parry_star, fx_dust: roblox/assets/fx/, see roblox/README.md) and
-- falls back to a plain part of the same size and colour until it's imported
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local S = Weapons.S
local Fx = {}
local folder = Instance.new("Folder")
folder.Name = "JankfireFx"
folder.Parent = workspace

local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function castMap(o: Vector3, d: Vector3): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	return workspace:Raycast(o, d, mapParams)
end
Fx.castMap = castMap

-- a Blender mesh from the library (its first MeshPart), or a plain part. POOLED: a finished bit goes back on its
-- shelf (hidden, parked out of the way) and the next effect of that kind reuses it, so firing never makes and destroys
-- parts all the time
local shelf: { [string]: { BasePart } } = {}
local PARK = CFrame.new(0, -5000, 0)
local function source(name: string): BasePart?
	local lib = ReplicatedStorage:FindFirstChild("JankfireFX")
	local t = lib and lib:FindFirstChild(name)
	if not t then return nil end
	return if t:IsA("BasePart") then t else t:FindFirstChildWhichIsA("BasePart", true)
end
local function piece(name: string, shape: Enum.PartType, size: Vector3, color: Color3, mat: Enum.Material, meshLen: number?): BasePart
	local src = source(name)
	local key = name .. (if src then "|mesh" else "|" .. shape.Name)
	local list = shelf[key]
	local p: BasePart? = list and table.remove(list)
	if not p then
		local q: BasePart
		if src then q = src:Clone() else local b = Instance.new("Part"); b.Shape = shape; q = b end
		q:SetAttribute("FxKey", key)
		q.Anchored = true; q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
		q.Parent = folder
		p = q
	end
	local part = p :: BasePart
	if src then
		-- fit the mesh to the size asked for, keeping its proportions along its longest side
		local sz = src.Size
		part.Size = sz * ((meshLen or math.max(size.X, size.Y, size.Z)) / math.max(sz.X, sz.Y, sz.Z))
	else
		part.Size = size
	end
	part.Name = name; part.Color = color; part.Material = mat; part.Transparency = 0
	return part
end
Fx.piece = piece
-- a bit is done: back on its shelf for the next effect (up to 160 of each kind are kept)
local function release(p: BasePart)
	local key = p:GetAttribute("FxKey")
	if type(key) ~= "string" or not p.Parent then p:Destroy(); return end
	local list = shelf[key] or {}
	shelf[key] = list
	if #list >= 160 then p:Destroy(); return end
	p.Transparency = 1
	p.CFrame = PARK
	local l = p:FindFirstChildOfClass("PointLight")
	if l then l.Enabled = false end
	table.insert(list, p)
end

-- the live bits, stepped every frame
type Bit = {
	p: BasePart, v: Vector3, w: Vector3, t: number, life: number, grav: number, bounce: number, fade: number,
	spin: CFrame, size0: Vector3?, grow: number?, stick: boolean?, step: ((Bit, number) -> ())?,
}
local bits: { Bit } = {}
local function add(b: Bit) table.insert(bits, b) end

RunService.RenderStepped:Connect(function(dt: number)
	for i = #bits, 1, -1 do
		local b = bits[i]
		b.t += dt
		if b.t >= b.life or not b.p.Parent then
			release(b.p); table.remove(bits, i); continue
		end
		if b.step then
			b.step(b, dt)
		else
			if not b.stick then
				b.v -= Vector3.new(0, b.grav * dt, 0)
				local pos = b.p.Position
				local mv = b.v * dt
				if b.bounce > 0 and mv.Magnitude > 1e-4 then
					local hit = castMap(pos, mv)
					if hit then -- bounce off what it hit, lose most of it, roll to a stop
						local n = hit.Normal
						b.v = (b.v - 2 * b.v:Dot(n) * n) * b.bounce
						if b.v.Magnitude < 2 then b.stick = true end
						mv = n * 0.02
						b.w *= 0.6
					end
				end
				b.p.CFrame = (b.p.CFrame + mv) * CFrame.fromEulerAnglesXYZ(b.w.X * dt, b.w.Y * dt, b.w.Z * dt)
			end
		end
		if b.grow and b.size0 then b.p.Size = b.size0 * (1 + b.grow * (b.t / b.life)) end
		local fadeFrom = b.life - b.fade
		if b.t > fadeFrom then b.p.Transparency = math.clamp((b.t - fadeFrom) / math.max(b.fade, 1e-3), 0, 1) end
	end
end)

-- a straight additive streak from the muzzle to the hit, fading (0.045 m thick for 0.2 s on the Redline)
function Fx.tracer(from: Vector3, to: Vector3, color: Color3, width: number, life: number)
	local d = to - from
	local L = d.Magnitude
	if L < 0.2 then return end
	local p = piece("fx_tracer", Enum.PartType.Block, Vector3.new(width, width, L), color, Enum.Material.Neon)
	p.Size = Vector3.new(width, width, L)
	p.CFrame = CFrame.lookAt(from + d / 2, to)
	p.Transparency = 0.1
	add({ p = p, v = Vector3.zero, w = Vector3.zero, t = 0, life = life, grav = 0, bounce = 0, fade = life, spin = CFrame.identity, stick = true })
end

-- the muzzle flash: a star facing forward + side spikes, random roll and 0.8-1.4 size, 0.05 s (x1.6 'big')
function Fx.flash(at: CFrame, big: boolean, color: Color3?, lightRange: number?)
	local s = (0.24 * S) * (0.8 + math.random() * 0.6) * (if big then 1.6 else 1)
	-- (the Blender star is 0.24 m across with 0.4 m spikes running forward: its longest side is the spikes)
	local p = piece("fx_flash_star", Enum.PartType.Cylinder, Vector3.new(0.02, s, s), color or Color3.fromRGB(255, 225, 120), Enum.Material.Neon, s * 0.42 / 0.24)
	p.CFrame = at * CFrame.Angles(0, 0, math.random() * math.pi * 2) * (if p:IsA("MeshPart") then CFrame.identity else CFrame.Angles(0, math.pi / 2, 0))
	add({ p = p, v = Vector3.zero, w = Vector3.zero, t = 0, life = 0.05, grav = 0, bounce = 0, fade = 0.02, spin = CFrame.identity, stick = true })
	-- (pooled stars keep their light: switched back on here, off again when the star is shelved)
	local light = p:FindFirstChildOfClass("PointLight") or Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 200, 120); light.Range = lightRange or 10; light.Brightness = 3; light.Enabled = true; light.Parent = p
end

-- a brass casing out of the port: up and right, spinning, one or two bounces, fades (owner: smooth, not clunky)
function Fx.brass(at: CFrame, big: boolean)
	local sz = Vector3.new(0.03, 0.03, 0.07) * S * (if big then 1.6 else 1)
	local p = piece("fx_casing", Enum.PartType.Cylinder, sz, Color3.fromRGB(214, 168, 70), Enum.Material.Metal)
	p.CFrame = at
	local v = at.RightVector * (2.2 + math.random()) * S + at.UpVector * (2.4 + math.random()) * S + at.LookVector * -0.4 * S
	add({ p = p, v = v, w = Vector3.new(math.random() * 30 - 15, math.random() * 30, math.random() * 20), t = 0, life = 1.4, grav = 4.5 * S * 2, bounce = 0.35, fade = 0.4, spin = CFrame.identity })
end

-- ---------------------------------------------------------------- impacts, holes, water (2026-11-14 polish; all pooled)
-- textures: ours (fx_bullethole, fx_ripple, fx_blob: Open Cloud Decal uploads 115670769810545 / 89688159673467 /
-- 94585227818836; these are their image ids) + Roblox's built-in particle sheets
local TEX = {
	hole = "rbxassetid://120874106121066",
	ripple = "rbxassetid://93806501334938",
	blob = "rbxassetid://96136840417410",
	smoke = "rbxasset://textures/particles/smoke_main.dds",
	fire = "rbxasset://textures/particles/fire_main.dds",
}
local function ns(...: number): NumberSequence
	local a = { ... }
	local k = {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end
local function cs(...: Color3): ColorSequence
	local a = { ... }
	if #a == 1 then return ColorSequence.new(a[1]) end
	local k = {}
	for i, c in a do table.insert(k, ColorSequenceKeypoint.new((i - 1) / (#a - 1), c)) end
	return ColorSequence.new(k)
end

-- particle emitters on attachments of one hidden part: an effect moves the next emitter of its pool to the spot,
-- points it and calls :Emit (nothing is created per shot). pools cycle, so a colour set for one hit doesn't recolour
-- the last few
local host = Instance.new("Part")
host.Name = "FxEmitters"; host.Anchored = true; host.CanCollide = false; host.CanQuery = false; host.CanTouch = false
host.Transparency = 1; host.Size = Vector3.new(0.2, 0.2, 0.2); host.CFrame = CFrame.identity
host.Parent = folder
type Em = { att: Attachment, pe: ParticleEmitter }
type EmPool = { list: { Em }, i: number }
local function emitters(n: number, props: { [string]: any }): EmPool
	local list = {}
	for i = 1, n do
		local att = Instance.new("Attachment")
		local pe = Instance.new("ParticleEmitter")
		pe.Enabled = false; pe.Rate = 0; pe.LockedToPart = false
		for k, v in props do (pe :: any)[k] = v end
		pe.Parent = att
		att.Parent = host
		list[i] = { att = att, pe = pe }
	end
	return { list = list, i = 0 }
end
-- the next emitter of a pool, moved to `at`, its +Y (where it emits) along `dir`
local function emAt(p: EmPool, at: Vector3, dir: Vector3): ParticleEmitter
	p.i = p.i % #p.list + 1
	local e = p.list[p.i]
	local d = if dir.Magnitude > 1e-4 then dir.Unit else Vector3.yAxis
	local up = if math.abs(d.Y) > 0.98 then Vector3.xAxis else Vector3.yAxis
	e.att.WorldCFrame = CFrame.lookAt(at, at + d, up) * CFrame.Angles(-math.pi / 2, 0, 0)
	return e.pe
end
local NR = NumberRange.new
local FIRE = emitters(4, { Texture = TEX.fire, LightEmission = 1, LightInfluence = 0, Brightness = 4, ZOffset = 0.3,
	Color = cs(Color3.fromRGB(255, 248, 210), Color3.fromRGB(255, 196, 70), Color3.fromRGB(255, 90, 25)),
	Size = ns(0, 0.16 * S, 0.4, 0.26 * S, 1, 0), Transparency = ns(0, 0, 0.6, 0.2, 1, 1),
	Lifetime = NR(0.05, 0.1), Speed = NR(6 * S, 12 * S), SpreadAngle = Vector2.new(9, 9), Drag = 6,
	Rotation = NR(0, 360), RotSpeed = NR(-300, 300) })
-- first person: the same fire, small (the muzzle is a stud or two from your eye)
local FIRE_FP = emitters(4, { Texture = TEX.fire, LightEmission = 1, LightInfluence = 0, Brightness = 3, ZOffset = 0.2,
	Color = cs(Color3.fromRGB(255, 248, 210), Color3.fromRGB(255, 196, 70), Color3.fromRGB(255, 90, 25)),
	Size = ns(0, 0.05 * S, 0.4, 0.085 * S, 1, 0), Transparency = ns(0, 0.05, 0.6, 0.3, 1, 1),
	Lifetime = NR(0.035, 0.06), Speed = NR(2 * S, 4 * S), SpreadAngle = Vector2.new(10, 10), Drag = 6,
	Rotation = NR(0, 360), RotSpeed = NR(-300, 300) })
local GLOW = emitters(4, { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 3,
	Color = cs(Color3.fromRGB(255, 214, 120)), Size = ns(0, 0.45 * S, 1, 0.15 * S), Transparency = ns(0, 0.15, 1, 1),
	Lifetime = NR(0.06), Speed = NR(0) })
local SMOKE = emitters(4, { Texture = TEX.smoke, LightInfluence = 1, Color = cs(Color3.fromRGB(205, 200, 195)),
	Size = ns(0, 0.08 * S, 1, 0.55 * S), Transparency = ns(0, 0.7, 0.25, 0.75, 1, 1),
	Lifetime = NR(0.5, 0.9), Speed = NR(0.4 * S, 1.2 * S), SpreadAngle = Vector2.new(25, 25), Drag = 3,
	Acceleration = Vector3.new(0, 0.6 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-40, 40) })
local DUST = emitters(12, { Texture = TEX.smoke, LightInfluence = 1,
	Size = ns(0, 0.12 * S, 1, 0.8 * S), Transparency = ns(0, 0.3, 0.45, 0.55, 1, 1),
	Lifetime = NR(0.45, 1), Speed = NR(0.8 * S, 2.6 * S), SpreadAngle = Vector2.new(38, 38), Drag = 5,
	Acceleration = Vector3.new(0, -0.8 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-60, 60) })
local SPARK = emitters(4, { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 5,
	Orientation = Enum.ParticleOrientation.VelocityParallel,
	Color = cs(Color3.fromRGB(255, 252, 225), Color3.fromRGB(255, 200, 90), Color3.fromRGB(255, 110, 30)),
	Size = ns(0, 0.045 * S, 1, 0), Squash = ns(0, 2.2, 1, 2.2),
	Lifetime = NR(0.12, 0.32), Speed = NR(4 * S, 11 * S), SpreadAngle = Vector2.new(55, 55),
	Acceleration = Vector3.new(0, -20 * S, 0), Drag = 1.5 })
local function drops(size: number, speed: number, spread: number, life: number): EmPool
	return emitters(5, { Texture = TEX.blob, LightInfluence = 0.5, LightEmission = 0.45, Color = cs(Color3.fromRGB(225, 246, 255)),
		Size = ns(0, size, 1, size * 0.45), Transparency = ns(0, 0.1, 0.7, 0.35, 1, 1),
		Lifetime = NR(life * 0.6, life), Speed = NR(speed * 0.4, speed), SpreadAngle = Vector2.new(spread, spread),
		Acceleration = Vector3.new(0, -26 * S, 0) })
end
local DROPS_S = drops(0.085 * S, 5 * S, 18, 0.6)
local DROPS_L = drops(0.11 * S, 7.5 * S, 28, 1)
local MIST = emitters(4, { Texture = TEX.smoke, LightInfluence = 0.7, LightEmission = 0.15, Color = cs(Color3.fromRGB(240, 250, 255)),
	Size = ns(0, 0.3 * S, 1, 1.4 * S), Transparency = ns(0, 0.5, 1, 1), Lifetime = NR(0.4, 0.8),
	Speed = NR(0.5 * S, 2 * S), SpreadAngle = Vector2.new(60, 60), Drag = 3, Rotation = NR(0, 360), RotSpeed = NR(-30, 30) })
-- ripples: flat rings on the surface. a pool of 32 thin invisible parts with the ring texture on their top face, each
-- grown and faded every frame (particles can't be made to lie flat reliably)
type Ring = { p: BasePart, d: Decal, t: number, life: number, s0: number, s1: number, tr: number, live: boolean }
local rings: { Ring } = {}
local ringI = 0
local function ring(at: Vector3, s0: number, s1: number, life: number, tr: number)
	ringI = ringI % 32 + 1
	local r = rings[ringI]
	if not r then
		local p = Instance.new("Part")
		p.Name = "Ripple"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1
		local d = Instance.new("Decal")
		d.Texture = TEX.ripple; d.Face = Enum.NormalId.Top; d.Transparency = 1
		d.Parent = p
		p.Parent = folder
		r = { p = p, d = d, t = 0, life = 1, s0 = 1, s1 = 1, tr = 0, live = false }
		rings[ringI] = r
	end
	local rr = r :: Ring
	rr.t, rr.life, rr.s0, rr.s1, rr.tr, rr.live = 0, life, s0, s1, tr, true
	rr.p.Size = Vector3.new(s0, 0.05, s0)
	rr.p.CFrame = CFrame.new(at + Vector3.new(0, 0.1, 0)) * CFrame.Angles(0, math.random() * math.pi * 2, 0)
	rr.d.Transparency = tr
end
local function ringStep(dt: number)
	for _, r in rings do
		if not r.live then continue end
		r.t += dt
		local k = r.t / r.life
		if k >= 1 then r.live = false; r.d.Transparency = 1; continue end
		local s = r.s0 + (r.s1 - r.s0) * (1 - (1 - k) * (1 - k)) -- fast out, slowing as it spreads
		r.p.Size = Vector3.new(s, 0.05, s)
		r.d.Transparency = r.tr + (1 - r.tr) * k
	end
end
-- if our uploaded ring doesn't load on this machine (a fresh upload can say "no asset content representation" for a
-- while), the ripples use Roblox's own shockwave ring instead
task.spawn(function()
	local ok = true
	pcall(function()
		game:GetService("ContentProvider"):PreloadAsync({ TEX.ripple }, function(_, status)
			if status ~= Enum.AssetFetchStatus.Success then ok = false end
		end)
	end)
	if ok then return end
	TEX.ripple = "rbxasset://textures/particles/explosion01_shockwave_main.dds"
	for _, r in rings do r.d.Texture = TEX.ripple end
end)

-- bullet holes: a ring of 90 decals that get reused oldest-first; each fades out over its last 4 s of 14. each has a
-- small dark core disc too, so there's a hole even if the decal's image hasn't loaded
local HOLES, HOLE_LIFE, HOLE_FADE = 90, 14, 4
type Hole = { p: BasePart, d: Decal, core: BasePart, t: number }
local holes: { Hole } = {}
local holeI = 0
local function hole(at: Vector3, n: Vector3, size: number)
	holeI = holeI % HOLES + 1
	local h = holes[holeI]
	if not h then
		local p = Instance.new("Part")
		p.Name = "BulletHole"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1
		local d = Instance.new("Decal")
		d.Texture = TEX.hole; d.Face = Enum.NormalId.Front
		d.Parent = p
		local c = Instance.new("Part")
		c.Name = "Core"; c.Shape = Enum.PartType.Cylinder; c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
		c.CastShadow = false; c.Material = Enum.Material.SmoothPlastic; c.Color = Color3.fromRGB(22, 19, 18)
		c.Parent = p
		p.Parent = folder
		h = { p = p, d = d, core = c, t = 0 }
		holes[holeI] = h
	end
	local hh = h :: Hole
	local up = if math.abs(n.Y) > 0.98 then Vector3.zAxis else Vector3.yAxis
	-- floors often have a thin look-only layer (deck boards, rugs) over the collision box: lift the hole above it
	local lift = if n.Y > 0.7 then 0.08 else 0.03
	local cf = CFrame.lookAt(at + n * (lift - 0.02), at + n * 2, up) * CFrame.Angles(0, 0, math.random() * math.pi * 2)
	hh.p.Size = Vector3.new(size, size, 0.04)
	hh.p.CFrame = cf
	hh.d.Transparency = 0
	local cd = size * 0.3
	hh.core.Size = Vector3.new(0.02, cd, cd)
	hh.core.CFrame = cf * CFrame.new(0, 0, -0.012) * CFrame.Angles(0, math.pi / 2, 0)
	hh.core.Transparency = 0
	hh.t = os.clock()
end

-- what a surface is made of decides what flies off it
local KIND: { [Enum.Material]: string } = {}
for name, kind in {
	Metal = "metal", DiamondPlate = "metal", CorrodedMetal = "metal", Foil = "metal", Neon = "metal",
	Glass = "glass", Ice = "glass", Glacier = "glass", ForceField = "glass",
	Wood = "wood", WoodPlanks = "wood",
	Grass = "soft", LeafyGrass = "soft", Ground = "soft", Mud = "soft", Sand = "soft", Snow = "soft", Salt = "soft",
	Fabric = "cloth", Rubber = "cloth", Cardboard = "cloth", Carpet = "cloth", Leather = "cloth",
	Water = "water",
} do
	local ok, m = pcall(function() return (Enum.Material :: any)[name] end)
	if ok and m then KIND[m] = kind end
end
local KIND_COL: { [string]: Color3 } = { metal = Color3.fromRGB(120, 122, 128), glass = Color3.fromRGB(190, 225, 240),
	wood = Color3.fromRGB(150, 110, 70), soft = Color3.fromRGB(110, 95, 70), cloth = Color3.fromRGB(170, 160, 150), hard = Color3.fromRGB(165, 160, 152) }

-- little pooled chunks off the surface (long = splinters)
local function chunks(at: Vector3, n: Vector3, count: number, color: Color3, mat: Enum.Material, long: boolean?)
	for _ = 1, count do
		local s = 0.05 * S * (0.6 + math.random() * 0.9)
		local size = if long then Vector3.new(s * 0.5, s * 0.5, s * 3) else Vector3.new(s, s, s)
		local p = piece("fx_dust", Enum.PartType.Block, size, color:Lerp(Color3.new(0, 0, 0), math.random() * 0.25), mat)
		if long then p.Size = size end
		p.CFrame = CFrame.new(at + n * 0.1) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
		local v = (n + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 1.3).Unit * (1.5 + math.random() * 3) * S
		add({ p = p, v = v, w = Vector3.new(math.random() * 20 - 10, math.random() * 20 - 10, 8), t = 0, life = 0.45 + math.random() * 0.3,
			grav = 26 * S, bounce = 0, fade = 0.2, spin = CFrame.identity })
	end
end
local function puff(at: Vector3, n: Vector3, color: Color3, count: number)
	local pe = emAt(DUST, at + n * 0.15, n)
	pe.Color = cs(color)
	pe:Emit(count)
end
local function sparkBurst(at: Vector3, dir: Vector3, count: number)
	emAt(SPARK, at, dir):Emit(count)
end

-- the water: invisible parts tagged "JankWater" (the pool's volume; its top face is the surface). Terrain water fills
-- them (ServerScriptService.JankWater) for the swimming; these just tell the effects where the water is
local waters: { BasePart } = {}
local function refreshWaters()
	local list = {}
	for _, p in CollectionService:GetTagged("JankWater") do if p:IsA("BasePart") then table.insert(list, p) end end
	waters = list
end
CollectionService:GetInstanceAddedSignal("JankWater"):Connect(refreshWaters)
CollectionService:GetInstanceRemovedSignal("JankWater"):Connect(refreshWaters)
refreshWaters()
-- the water volume a point is in, and the surface's height there
function Fx.waterAt(p: Vector3): (BasePart?, number?)
	for _, w in waters do
		local l = w.CFrame:PointToObjectSpace(p)
		local h = w.Size / 2
		if math.abs(l.X) <= h.X and math.abs(l.Z) <= h.Z and l.Y <= h.Y and l.Y >= -h.Y then
			return w, w.CFrame:PointToWorldSpace(Vector3.new(l.X, h.Y, l.Z)).Y
		end
	end
	return nil, nil
end
-- where the segment a -> b goes through a water surface (either way), if it does
function Fx.waterCross(a: Vector3, b: Vector3): Vector3?
	for _, w in waters do
		local la, lb = w.CFrame:PointToObjectSpace(a), w.CFrame:PointToObjectSpace(b)
		local h = w.Size / 2
		if (la.Y - h.Y) * (lb.Y - h.Y) < 0 then
			local l = la:Lerp(lb, (la.Y - h.Y) / (la.Y - lb.Y))
			if math.abs(l.X) <= h.X and math.abs(l.Z) <= h.Z then return w.CFrame:PointToWorldSpace(Vector3.new(l.X, h.Y, l.Z)) end
		end
	end
	return nil
end
-- spreading rings: s = a bullet or a marble, m = a swimmer's wake, l = someone jumping in
function Fx.ripple(at: Vector3, size: string)
	if size == "l" then
		ring(at, 0.6 * S, 4.5 * S, 1.6, 0.05)
		task.delay(0.2, function() ring(at, 0.3 * S, 3.2 * S, 1.4, 0.2) end)
		task.delay(0.45, function() ring(at, 0.2 * S, 2.2 * S, 1.2, 0.35) end)
	elseif size == "m" then
		ring(at, 0.4 * S, 2.4 * S, 1.2, 0.35)
	else
		ring(at, 0.15 * S, 1.6 * S, 1, 0.1)
		task.delay(0.12, function() ring(at, 0.05 * S, 1 * S, 0.8, 0.3) end)
	end
end
-- a splash on the surface: power 0.15 (a marble), 0.3 (a bullet), 0.6-1.6 (someone jumping in, harder = bigger)
function Fx.splash(at: Vector3, power: number)
	if power >= 0.6 then
		emAt(DROPS_L, at, Vector3.yAxis):Emit(math.floor(16 + 18 * power))
		emAt(MIST, at, Vector3.yAxis):Emit(math.floor(2 + 3 * power))
		Fx.ripple(at, "l")
		Sfx.play("splash", at, math.min(1.5, 0.6 + power * 0.5))
	else
		emAt(DROPS_S, at, Vector3.yAxis):Emit(math.floor(4 + 16 * power))
		if power >= 0.25 then emAt(MIST, at, Vector3.yAxis):Emit(1); Sfx.play("splash", at, 0.35, 1.4) end
		Fx.ripple(at, "s")
	end
end
-- marbles plopping in: at most 6 a frame (a shotgun blast into the pool is up to ~100 marbles)
local plopBudget = 6
local function plop(at: Vector3)
	if plopBudget <= 0 then return end
	plopBudget -= 1
	Fx.splash(at, 0.15)
end

-- a bullet (or pellet) hitting the map: what flies off depends on the material. o.hole = false: no hole (marbles);
-- o.scale: a smaller or bigger hit
function Fx.impact(at: Vector3, normal: Vector3, inst: Instance?, mat: Enum.Material?, o: { hole: boolean?, scale: number? }?)
	local kind = (mat and KIND[mat]) or "hard"
	if kind == "water" then Fx.splash(at, 0.3); return end
	local part = if inst and inst:IsA("BasePart") then inst else nil
	local visible = part ~= nil and part.Transparency < 0.9
	local base = if part and visible then part.Color else KIND_COL[kind]
	local sc = (o and o.scale) or 1
	local function k(x: number): number return math.max(1, math.floor(x * sc + 0.5)) end
	if kind == "metal" then
		sparkBurst(at + normal * 0.05, normal, k(10))
		puff(at, normal, Color3.fromRGB(95, 95, 100), k(2))
		chunks(at, normal, k(2), base, Enum.Material.Metal)
	elseif kind == "glass" then
		chunks(at, normal, k(6), Color3.fromRGB(200, 235, 255), Enum.Material.Glass)
		sparkBurst(at, normal, k(3))
	elseif kind == "wood" then
		puff(at, normal, base:Lerp(Color3.fromRGB(205, 180, 140), 0.5), k(4))
		chunks(at, normal, k(4), base:Lerp(Color3.fromRGB(225, 195, 150), 0.4), Enum.Material.Wood, true)
	elseif kind == "soft" then
		puff(at, normal, base:Lerp(Color3.fromRGB(150, 130, 100), 0.4), k(7))
		chunks(at, normal, k(4), base, Enum.Material.Ground)
	elseif kind == "cloth" then
		puff(at, normal, base:Lerp(Color3.new(1, 1, 1), 0.4), k(3))
	else -- concrete, brick, tiles, plastic...: a dust puff in the surface's colour + chips
		puff(at, normal, base:Lerp(Color3.fromRGB(200, 195, 188), 0.55), k(5))
		chunks(at, normal, k(4), base, Enum.Material.Slate)
	end
	-- a hole in what it hit (visible, fixed surfaces: not dirt, not the invisible collision boxes behind the models)
	if not (o and o.hole == false) and visible and kind ~= "soft" and part and part.Anchored then
		hole(at, normal, 0.16 * S * (0.8 + math.random() * 0.4) * sc)
	end
end

-- the katana biting a wall or the floor: sparks skidding off anything hard, a puff off anything soft
function Fx.slash(at: Vector3, normal: Vector3, inst: Instance?, mat: Enum.Material?, dir: Vector3)
	local kind = (mat and KIND[mat]) or "hard"
	if kind == "water" then Fx.splash(at, 0.45); return end
	local part = if inst and inst:IsA("BasePart") then inst else nil
	local base = if part and part.Transparency < 0.9 then part.Color else KIND_COL[kind]
	local glance = dir - 2 * dir:Dot(normal) * normal -- the blade skids off along the surface
	if kind == "metal" or kind == "hard" or kind == "glass" then
		sparkBurst(at + normal * 0.05, normal + glance.Unit, 18)
		puff(at, normal, base:Lerp(Color3.fromRGB(200, 195, 188), 0.55), 3)
	else
		puff(at, normal, base:Lerp(Color3.fromRGB(190, 170, 140), 0.45), 5)
		chunks(at, normal, 3, base, if kind == "wood" then Enum.Material.Wood else Enum.Material.Ground, kind == "wood")
	end
end

-- the muzzle: the flash star + its light (Fx.flash), a burst of fire out of the barrel, a glow seen from outside, and a
-- wisp of smoke every few shots
local shots = 0
function Fx.muzzle(at: CFrame, big: boolean, fpv: boolean, color: Color3?)
	Fx.flash(at, big, color, if fpv then 7 else 14)
	local pos, dir = at.Position, at.LookVector
	if fpv then
		emAt(FIRE_FP, pos + dir * 0.1, dir):Emit(if big then 6 else 3)
	else
		emAt(FIRE, pos, dir):Emit(if big then 10 else 5)
		emAt(GLOW, pos + dir * 0.2, dir):Emit(1)
	end
	shots += 1
	if big or shots % 3 == 0 then emAt(SMOKE, pos + dir * 0.3, dir):Emit(if big then 3 else 1) end
end

-- someone else's shot: where its pellets ended, found again on this machine (a short ray at each end) so everyone sees
-- the holes, dust and splashes, not just the shooter
function Fx.shotEnds(from: Vector3, ends: { Vector3 }, marbles: boolean)
	local o = if marbles then { hole = false, scale = 0.7 } else nil
	for i, e in ends do
		if i > 6 then break end
		local wx = Fx.waterCross(from, e)
		if wx then if not marbles then Fx.splash(wx, 0.3) end; continue end -- (marbles plop in on their own)
		local d = e - from
		local L = d.Magnitude
		if L < 0.5 then continue end
		local hit = castMap(from, d / L * (L + 0.6))
		if hit and (hit.Position - e).Magnitude < 1.5 then Fx.impact(hit.Position, hit.Normal, hit.Instance, hit.Material, o) end
	end
end

-- every frame: holes fade near the end of their life (checked 5x a second), the marble-plop budget refills
local holeAcc = 0
RunService.RenderStepped:Connect(function(dt: number)
	plopBudget = 6
	ringStep(dt)
	holeAcc += dt
	if holeAcc < 0.2 then return end
	holeAcc = 0
	local now = os.clock()
	for _, h in holes do
		local age = now - h.t
		if h.d.Transparency < 1 and age > HOLE_LIFE - HOLE_FADE then
			h.d.Transparency = math.clamp((age - (HOLE_LIFE - HOLE_FADE)) / HOLE_FADE, 0, 1)
			h.core.Transparency = h.d.Transparency
		end
	end
end)

-- swimmers (players and dummies): a big splash when someone drops in, a wake while they paddle along the top, drips
-- when they climb out. 20 checks a second, a point-in-box test per person
type Wet = { inside: boolean, last: number, top: number }
local wetState: { [Model]: Wet } = setmetatable({}, { __mode = "k" }) :: any
local wetAcc = 0
local function wetCheck(ch: Model, now: number)
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then return end
	local pos = root.Position
	local w, top = Fx.waterAt(pos - Vector3.new(0, 2.8, 0))
	local s = wetState[ch]
	if not s then wetState[ch] = { inside = w ~= nil, last = 0, top = top or 0 }; return end
	local v = root.AssemblyLinearVelocity
	if w and top then
		local surf = Vector3.new(pos.X, top, pos.Z)
		if not s.inside then
			Fx.splash(surf, math.clamp(0.6 - v.Y / 60, 0.6, 1.6))
			s.last = now
		elseif pos.Y - top < 3 then
			local spd = Vector3.new(v.X, 0, v.Z).Magnitude
			if now - s.last > (if spd > 4 then 0.28 else 1.1) then
				s.last = now
				Fx.ripple(surf, "m")
				if spd > 8 then emAt(DROPS_S, surf, Vector3.yAxis):Emit(3) end
			end
		end
		s.top = top
	elseif s.inside then
		local surf = Vector3.new(pos.X, s.top, pos.Z)
		emAt(DROPS_S, surf, Vector3.yAxis):Emit(5)
		Fx.ripple(surf, "m")
	end
	s.inside = w ~= nil
end
RunService.Heartbeat:Connect(function(dt: number)
	if #waters == 0 then return end
	wetAcc += dt
	if wetAcc < 0.05 then return end
	wetAcc = 0
	local now = os.clock()
	for _, pl in Players:GetPlayers() do if pl.Character then wetCheck(pl.Character, now) end end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do if m:IsA("Model") then wetCheck(m, now) end end end
end)

-- blood: red bits from the chest or head, away from the shooter
function Fx.blood(at: Vector3, dir: Vector3, dmg: number)
	local n = math.min(14, 3 + math.floor(dmg * 0.25))
	for _ = 1, n do
		local p = piece("fx_dust", Enum.PartType.Block, Vector3.new(0.15, 0.15, 0.15), if math.random() < 0.5 then Color3.fromRGB(200, 20, 30) else Color3.fromRGB(120, 0, 10), Enum.Material.SmoothPlastic)
		p.CFrame = CFrame.new(at)
		local v = (dir + Vector3.new(math.random() - 0.5, math.random() * 0.8, math.random() - 0.5)).Unit * (6 + math.random() * 14)
		add({ p = p, v = v, w = Vector3.new(8, 8, 8), t = 0, life = 0.7, grav = 60, bounce = 0, fade = 0.3, spin = CFrame.identity })
	end
end

-- sparks: hot white/yellow streaks sideways and up, turning orange, plus a white pop
function Fx.sparks(at: Vector3, dir: Vector3, n: number, pop: number)
	for _ = 1, n do
		local p = piece("fx_spark", Enum.PartType.Block, Vector3.new(0.06, 0.06, 0.35), Color3.fromRGB(255, 250, 200), Enum.Material.Neon)
		local v = (dir * 0.6 + Vector3.new(math.random() - 0.5, math.random() * 0.9, math.random() - 0.5)).Unit * (2.5 + math.random() * 7) * S
		p.CFrame = CFrame.lookAt(at, at + v)
		add({ p = p, v = v, w = Vector3.zero, t = 0, life = 0.1 + math.random() * 0.2, grav = 30, bounce = 0, fade = 0.1, spin = CFrame.identity,
			step = function(b: Bit, dt: number)
				b.v -= Vector3.new(0, b.grav * dt, 0)
				local pos = b.p.Position + b.v * dt
				b.p.CFrame = CFrame.lookAt(pos, pos + b.v)
				b.p.Color = Color3.fromRGB(255, 250, 200):Lerp(Color3.fromRGB(255, 120, 30), b.t / b.life)
			end })
	end
	if pop > 0 then
		local s = piece("fx_parry_star", Enum.PartType.Ball, Vector3.new(pop, pop, pop) * 2 * S, Color3.new(1, 1, 1), Enum.Material.Neon)
		s.CFrame = CFrame.new(at) * CFrame.Angles(0, 0, math.random() * 6)
		add({ p = s, v = Vector3.zero, w = Vector3.zero, t = 0, life = 0.14, grav = 0, bounce = 0, fade = 0.12, spin = CFrame.identity, size0 = s.Size, grow = 0.8, stick = true })
	end
end

-- the melee hit flash: a white pop growing to the radius and fading in 0.3 s + yellow-to-orange sparks
function Fx.blast(at: Vector3, r: number)
	local p = piece("fx_impact", Enum.PartType.Ball, Vector3.new(0.3, 0.3, 0.3) * r * S, Color3.new(1, 1, 1), Enum.Material.Neon)
	p.CFrame = CFrame.new(at) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
	add({ p = p, v = Vector3.zero, w = Vector3.zero, t = 0, life = 0.3, grav = 0, bounce = 0, fade = 0.3, spin = CFrame.identity, size0 = p.Size, grow = 2.3, stick = true })
	Fx.sparks(at, Vector3.yAxis, 16, 0)
end

-- the Marble Shotgun's marbles: fly along the pellet paths at 70 m/s, bounce, rattle and roll, then fade
local MARBLE = { Color3.fromRGB(47, 123, 255), Color3.fromRGB(25, 195, 125), Color3.fromRGB(255, 79, 79), Color3.fromRGB(255, 210, 59), Color3.fromRGB(176, 125, 255), Color3.fromRGB(255, 138, 26), Color3.fromRGB(55, 214, 255) }
local liveMarbles = 0
function Fx.marbles(from: Vector3, ends: { Vector3 }, perEnd: number)
	for _, e in ends do
		for _ = 1, perEnd do
			if liveMarbles > 400 then return end
			local jitter = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.8
			local d = (e + jitter - from)
			local L = d.Magnitude
			if L < 0.1 then continue end
			liveMarbles += 1
			local p = piece("fx_marble", Enum.PartType.Ball, Vector3.new(0.16, 0.16, 0.16), MARBLE[math.random(#MARBLE)], Enum.Material.Glass)
			p.Transparency = 0.15
			local u = d / L
			p.CFrame = CFrame.new(from)
			local flown, wet = 0, false
			add({ p = p, v = u * 70 * S, w = Vector3.new(math.random() * 20, math.random() * 20, 0), t = 0, life = 2.6 + math.random(), grav = 22 * S, bounce = 0.45, fade = 0.6, spin = CFrame.identity,
				step = function(b: Bit, dt: number)
					if flown < L then -- along the pellet's path to where it ended
						local s = math.min(70 * S * dt, L - flown)
						flown += s
						b.p.CFrame = b.p.CFrame + u * s
						if flown >= L then b.v = (-u * 0.3 + Vector3.new(0, 0.4, 0)) * 6 * S * math.random() end
					elseif not b.stick then
						if wet then -- in the pool: it sinks slowly, like a marble should
							b.v *= math.max(0, 1 - dt * 4)
							b.v -= Vector3.new(0, b.grav * 0.25 * dt, 0)
						else
							b.v -= Vector3.new(0, b.grav * dt, 0)
						end
						local mv = b.v * dt
						local hit = castMap(b.p.Position, mv)
						if hit then
							local n = hit.Normal
							b.v = (b.v - 2 * b.v:Dot(n) * n) * b.bounce
							b.v = Vector3.new(b.v.X * 0.8, b.v.Y, b.v.Z * 0.8) -- rolling friction
							if b.v.Magnitude < 1.5 then b.stick = true end
							mv = n * 0.02
						end
						b.p.CFrame = b.p.CFrame + mv
					end
					if not wet and #waters > 0 then -- plop: a little splash where it goes in
						local pos = b.p.Position
						local w, top = Fx.waterAt(pos)
						if w and top then wet = true; plop(Vector3.new(pos.X, top, pos.Z)) end
					end
				end })
			task.delay(4, function() liveMarbles -= 1 end)
		end
	end
end

-- marbles resting on the floor: one patch from the server, kicked about by nobody (they just sit there, glinting)
local patches: { [number]: { parts: { BasePart }, c: Vector3, r: number } } = {}
local function scatter(c: Vector3, r: number, n: number, into: { BasePart })
	for _ = 1, n do
		local a, rr = math.random() * math.pi * 2, math.sqrt(math.random()) * r
		local p = piece("fx_marble", Enum.PartType.Ball, Vector3.new(0.16, 0.16, 0.16), MARBLE[math.random(#MARBLE)], Enum.Material.Glass)
		p.Transparency = 0.15
		p.CFrame = CFrame.new(c + Vector3.new(math.cos(a) * rr, 0.08, math.sin(a) * rr))
		table.insert(into, p)
	end
end
function Fx.patchAdd(id: number, c: Vector3, r: number, n: number)
	Fx.patchDrop(id)
	local pt = { parts = {}, c = c, r = r }
	-- the shot's own marbles are still landing: the patch fills in as they arrive
	task.delay(Weapons.MSLIP.land, function() if patches[id] == pt then scatter(c, r, n, pt.parts) end end)
	patches[id] = pt
end
function Fx.patchThin(id: number, n: number, r: number, at: Vector3?)
	local pt = patches[id]
	if not pt then return end
	pt.r = r
	while #pt.parts > n do
		local p = table.remove(pt.parts, math.random(#pt.parts)) :: BasePart
		-- the ones that go get kicked away from whoever slipped
		local from = at or pt.c
		local d = (p.Position - from)
		local v = (Vector3.new(d.X, 0, d.Z).Unit * (4 + math.random() * 6) + Vector3.new(0, 3 + math.random() * 4, 0)) * S
		if v ~= v then v = Vector3.new(0, 10, 0) end
		add({ p = p, v = v, w = Vector3.new(10, 10, 0), t = 0, life = 1.5, grav = 22 * S, bounce = 0.4, fade = 0.5, spin = CFrame.identity })
	end
end
function Fx.patchDrop(id: number)
	local pt = patches[id]
	if not pt then return end
	patches[id] = nil
	for _, p in pt.parts do
		add({ p = p, v = Vector3.zero, w = Vector3.zero, t = 0, life = 0.4, grav = 0, bounce = 0, fade = 0.4, spin = CFrame.identity, stick = true })
	end
end

-- a reload prop held in the viewmodel (the Redline's jerry can, the marble bag): the Blender model if it's imported
-- (all its pieces, its own colours), else a plain block. size = its longest side, studs
function Fx.prop(name: string, size: Vector3, color: Color3): Model
	local m = Instance.new("Model")
	m.Name = name
	local lib = ReplicatedStorage:FindFirstChild("JankfireFX")
	local t = lib and lib:FindFirstChild(name)
	if t then
		local c = t:Clone()
		local parts = if c:IsA("BasePart") then { c } else c:GetDescendants()
		for _, d in parts do if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false; d.Parent = m end end
		if m:FindFirstChildWhichIsA("BasePart") then
			local _, ext = m:GetBoundingBox()
			m:ScaleTo(math.max(size.X, size.Y, size.Z) / math.max(ext.X, ext.Y, ext.Z))
		end
	end
	if not m:FindFirstChildWhichIsA("BasePart") then
		local p = Instance.new("Part")
		p.Size = size; p.Color = color; p.Material = Enum.Material.SmoothPlastic
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Parent = m
	end
	m.Parent = workspace.CurrentCamera
	return m
end

return Fx
