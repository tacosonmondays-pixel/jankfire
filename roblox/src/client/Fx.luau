--!strict
-- the client's effects, all moved every frame on the client (never server-stepped: the owner's "the bits spitting out
-- are clunky" note) and pooled (nothing is made or destroyed per shot). since 16 Nov 2026 (the VFX pipeline,
-- roblox/docs/VFX-PIPELINE.md) the gun effects follow the web game's own numbers (weapons.js:114-145 the flash; fx.js the
-- tracer, impact, sparks and explosion; flipbook.js the muzzle smoke, fireball and smoke cloud), drawn with Blender-made
-- sheets (roblox/assets/vfx, tools/roblox/vfx). meshes (fx_casing, fx_marble, fx_dust ...: ReplicatedStorage.JankfireFX)
-- fall back to a plain part of the same size and colour until they're imported
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local S = Weapons.S
local Holds = require(Shared:WaitForChild("Holds"))
-- first person: the viewmodel is drawn this much bigger than the web's metres (Holds.size), its flash with it
local FPK = S * ((Holds :: any).size or 1)
-- the effect clock: 1 normally; 0 freezes every effect where it is, 0.1 is slow motion (the VFX pipeline's frame
-- captures: Fx.setTimeScale, or the workspace attribute FxTimeScale in a Studio Play test)
local TS = { k = 1 }
local clockT = 0 -- seconds on the effect clock
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
	dt *= TS.k
	if dt <= 0 then return end
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
	-- the VFX pipeline's Blender sheets (roblox/assets/vfx/assets.json; Open Cloud Image uploads, 16 Nov 2026; the
	-- normal-blend ones alpha-bled, tools/roblox/vfx/bleed.py, so their soft edges don't go dark)
	flash = "rbxassetid://111717218327603", -- the web's 16-point star, 4 drawings (2x2)
	spike = "rbxassetid://100853288026710", -- the flash's flame, upright (particles)
	spikeH = "rbxassetid://129915677528999", -- the flash's flame lying along u (a Beam texture)
	spark = "rbxassetid://73042129135061", -- a streak (stretched along its flight)
	glow = "rbxassetid://107753175681578",
	tracer = "rbxassetid://72229869149513", -- a Beam core: v runs across it
	shock = "rbxassetid://136567724057402", -- the blast's ring on the floor
	chips = "rbxassetid://81145557543325", -- 4 flakes (2x2)
	dust = "rbxassetid://123624708348895", -- the impact puff, 16 frames (4x4)
	boom = "rbxassetid://92069836286961", -- the web's boom.png fireball baked again at 128 px, 64 frames (8x8)
	soft = "rbxassetid://101944596932707", -- the web's puffsoft.png smoke, 64 frames (8x8): for puffs living 2-4.5 s
	-- (a one-shot flipbook plays at most 30 frames a second: short-lived ones use the 16-frame sheets)
	soft4 = "rbxassetid://97407536340250", -- the same smoke, 16 frames (4x4)
	boom4 = "rbxassetid://101632032329716", -- the fireball, 16 frames (4x4, 256 px)
	feather = "rbxassetid://92745845385867", -- the high-tier skins' bits (SkinSets.FX)
	petal = "rbxassetid://72396403976507",
	sparkle = "rbxassetid://118739981349944", -- four points (the owner: sparkles you notice are real shapes)
	bubble = "rbxassetid://127426547666953", -- a soap bubble (the ducky skin)
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
local ALL: { ParticleEmitter } = {} -- every emitter made here (the effect clock sets their TimeScale)
-- what the effects cost: emits, particles, beams and lights since the counter was last read (the cost guard)
local STAT = { emits = 0, particles = 0, beams = 0, lights = 0, stepUs = 0 }
Fx.stats = STAT
local function emitters(n: number, props: { [string]: any }): EmPool
	local list = {}
	for i = 1, n do
		local att = Instance.new("Attachment")
		local pe = Instance.new("ParticleEmitter")
		pe.Enabled = false; pe.Rate = 0; pe.LockedToPart = false
		for k, v in props do (pe :: any)[k] = v end
		pe.TimeScale = TS.k
		pe.Parent = att
		att.Parent = host
		list[i] = { att = att, pe = pe }
		table.insert(ALL, pe)
	end
	return { list = list, i = 0 }
end
local function emit(pe: ParticleEmitter, n: number)
	if n <= 0 then return end
	STAT.emits += 1; STAT.particles += n
	pe:Emit(n)
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
-- a particle's Size is HALF its width (measured in Studio, 16 Nov 2026: a Size-1 particle is 2 studs across). every size
-- below is the width the web game uses, times H
local H = 0.5
-- keypoints with a random spread each: { t, value, envelope }
local function nsk(pts: { { number } }): NumberSequence
	local k = {}
	for _, p in pts do table.insert(k, NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0)) end
	return NumberSequence.new(k)
end
-- a size that grows the way the web's flipbook quads do: s0 + (s1 - s0) * sqrt(age)
local function grow(s0: number, s1: number, env: number?): NumberSequence
	local k = {}
	for _, t in { 0, 0.06, 0.15, 0.3, 0.5, 0.75, 1 } do
		table.insert(k, NumberSequenceKeypoint.new(t, s0 + (s1 - s0) * math.sqrt(t), (env or 0) * math.sqrt(t)))
	end
	return NumberSequence.new(k)
end
local FLIP2, FLIP4, FLIP8 = Enum.ParticleFlipbookLayout.Grid2x2, Enum.ParticleFlipbookLayout.Grid4x4, Enum.ParticleFlipbookLayout.Grid8x8
local RANDOM, ONESHOT = Enum.ParticleFlipbookMode.Random, Enum.ParticleFlipbookMode.OneShot
local function blend(e: ParticleEmitter) pcall(function() (e :: any).FlipbookBlendFrames = true end) end
local function blendPool(p: EmPool) for _, e in p.list do blend(e.pe) end end
local HOT = cs(Color3.fromRGB(255, 255, 255), Color3.fromRGB(255, 242, 176), Color3.fromRGB(255, 122, 16))

-- the muzzle flash (weapons.js:114-145): the star across the barrel, its flame along it, a soft glow round both. on for
-- 0.05 s (0.035 s on guns over 8 shots a second); each flash flickers between the 4 drawn stars (the web re-rolls its
-- star every frame), a random roll, 0.8-1.4 of its size
local FLASH = emitters(6, { Texture = TEX.flash, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(60),
	LightEmission = 1, LightInfluence = 0, Brightness = 2.5, ZOffset = 0.3, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
	Lifetime = NR(0.05), Speed = NR(0.01), Rotation = NR(0, 360), Transparency = ns(0, 0, 0.7, 0, 1, 0.3) })
-- (one of the 4 stars per flash, held: a 2-3 frame flash must never be a playing flipbook, its blending blurs it)
for _, e in FLASH.list do
	e.pe.FlipbookMode = Enum.ParticleFlipbookMode.Loop; e.pe.FlipbookStartRandom = true
	e.pe.FlipbookFramerate = NR(0)
	pcall(function() (e.pe :: any).FlipbookBlendFrames = false end)
end
local FLASH_TP = emitters(6, { Texture = TEX.flash, FlipbookLayout = FLIP2, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
	FlipbookStartRandom = true, FlipbookFramerate = NR(0), LightEmission = 1, LightInfluence = 0, Brightness = 2.5, ZOffset = 0.3,
	Lifetime = NR(0.05), Speed = NR(0), Rotation = NR(0, 360), Transparency = ns(0, 0, 0.7, 0, 1, 0.3) })
for _, e in FLASH_TP.list do pcall(function() (e.pe :: any).FlipbookBlendFrames = false end) end
-- the shot's smoke off the muzzle (flipbook.js muzzlePuff: 0.22 -> 0.85 m, 0.55-0.8 s, half see-through, 1.6 m/s along
-- the shot and a little up, drag 3.5). only for a muzzle over 1.3 m from the camera (never your own gun in first
-- person), at most one every 60 ms from about the same spot
local MPUFF = emitters(6, { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 1,
	Color = cs(Color3.fromRGB(176, 176, 176)), Size = grow(0.22 * S * H, 0.85 * S * H), Transparency = ns(0, 0.5, 0.75, 0.5, 1, 1),
	Lifetime = NR(0.55, 0.8), Speed = NR(1.64 * S), SpreadAngle = Vector2.new(6, 6), Drag = 3.5,
	Rotation = NR(0, 360), RotSpeed = NR(-115, 115) })
blendPool(MPUFF)
-- what a bullet knocks off a wall (fx.js impact: 10 grey squares off the normal at 4 m/s +- 3, 0.5 s, 0.15 -> 0.08 m,
-- gravity 12, fading 1 - t^2): Blender flakes, tumbling, in the surface's colour; then a small puff of its dust
local CHIPS = emitters(8, { Texture = TEX.chips, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(8, 14),
	LightInfluence = 0.6, LightEmission = 0, Size = ns(0, 0.38 * S * H, 1, 0.21 * S * H), Transparency = ns(0, 0, 0.5, 0.25, 1, 1),
	Lifetime = NR(0.5), Speed = NR(4 * S, 9 * S), SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, -12 * S, 0),
	Drag = 1, Rotation = NR(0, 360), RotSpeed = NR(-360, 360) })
local DUST = emitters(8, { Texture = TEX.dust, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 1,
	Size = ns(0, 0.3 * S * H, 1, 1.1 * S * H), Transparency = ns(0, 0.65, 0.25, 0.45, 0.6, 0.5, 1, 1),
	Lifetime = NR(0.55, 0.75), Speed = NR(0.5 * S, 1.6 * S), SpreadAngle = Vector2.new(25, 25), Drag = 4,
	Acceleration = Vector3.new(0, 0.4 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-40, 40) })
blendPool(DUST)
-- sparks (fx.js sparks: white and pale yellow turning orange, 0.1-0.3 s, gravity 14, drag 2), stretched along their flight
local SPARK = emitters(6, { Texture = TEX.spark, LightEmission = 1, LightInfluence = 0, Brightness = 3,
	Orientation = Enum.ParticleOrientation.VelocityParallel, Color = HOT,
	Size = ns(0, 0.11 * S * 2.4 * H, 1, 0.03 * S * 2.4 * H), Lifetime = NR(0.1, 0.3), Speed = NR(2.5 * S, 9.5 * S),
	SpreadAngle = Vector2.new(55, 55), Acceleration = Vector3.new(0, -14 * S, 0), Drag = 2 })
-- a quick white pop (the sparks' and the melee hit's flash sphere), sized per call
local POP = emitters(4, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 2,
	Lifetime = NR(0.12), Speed = NR(0), Transparency = ns(0, 0, 1, 1) })

-- the flash's light: a few PointLights on the host, lit for a moment and dimmed back out on the effect clock
type Lt = { l: PointLight, att: Attachment, t: number, life: number, b0: number, live: boolean }
local lights: { Lt } = {}
for i = 1, 6 do
	local att = Instance.new("Attachment"); att.Parent = host
	local l = Instance.new("PointLight"); l.Enabled = false; l.Shadows = false; l.Parent = att
	lights[i] = { l = l, att = att, t = 0, life = 0, b0 = 0, live = false }
end
local lightI = 0
local function lightFlash(at: Vector3, color: Color3, range: number, bright: number, life: number)
	lightI = lightI % #lights + 1
	local L = lights[lightI]
	L.att.WorldPosition = at
	L.l.Color = color; L.l.Range = range; L.l.Brightness = bright; L.l.Enabled = true
	L.t, L.life, L.b0, L.live = 0, life, bright, true
	STAT.lights += 1
end

-- beams (the tracers; the flash's flame along the barrel): two pooled attachments each, shown for a while on the
-- effect clock; fade = the opacity runs 1 -> 0 over the life (else on, then off, like the web's flash)
type Bm = { b: Beam, a0: Attachment, a1: Attachment, t: number, life: number, live: boolean, fade: boolean }
type BmPool = { list: { Bm }, i: number, n: number, props: { [string]: any } }
local beamPools: { BmPool } = {}
local function beamPool(n: number, props: { [string]: any }): BmPool
	local p: BmPool = { list = {}, i = 0, n = n, props = props }
	table.insert(beamPools, p)
	return p
end
local function beam(pool: BmPool, from: Vector3, to: Vector3, color: Color3, w0: number, w1: number, life: number, fade: boolean)
	pool.i = pool.i % pool.n + 1
	local B = pool.list[pool.i]
	if not B then
		local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
		a0.Parent = host; a1.Parent = host
		local b = Instance.new("Beam")
		b.Attachment0 = a0; b.Attachment1 = a1; b.TextureMode = Enum.TextureMode.Stretch; b.TextureLength = 1
		b.FaceCamera = true; b.Segments = 1; b.Enabled = false
		for k, v in pool.props do (b :: any)[k] = v end
		b.Parent = host
		B = { b = b, a0 = a0, a1 = a1, t = 0, life = 1, live = false, fade = true }
		pool.list[pool.i] = B
	end
	local X = B :: Bm
	X.a0.WorldPosition = from; X.a1.WorldPosition = to
	X.b.Color = ColorSequence.new(color); X.b.Width0 = w0; X.b.Width1 = w1
	X.b.Transparency = NumberSequence.new(0); X.b.Enabled = true
	X.t, X.life, X.live, X.fade = 0, life, true, fade
	STAT.beams += 1
end
-- tracers (fx.js tracer): a straight line from the muzzle to the hit in the gun's colour, its opacity running 1 -> 0
-- over its life; a soft core (the texture's solid middle is about half the beam's width, hence TR_WIDE)
-- (round 2: less glow, so each gun's colour survives on screen: the critic saw them all wash to white)
local TRACERS = beamPool(48, { Texture = TEX.tracer, LightEmission = 0.5, LightInfluence = 0, Brightness = 1.3 })
local TR_WIDE = 1.5
function Fx.tracer(from: Vector3, to: Vector3, color: Color3, width: number, life: number)
	if (to - from).Magnitude < 0.2 then return end
	beam(TRACERS, from, to, color, width * TR_WIDE, width * TR_WIDE, life, true)
end
-- the flash's flame along the barrel, exactly the web's way: two thin crossed planes (one upright, one flat) lying
-- along the barrel, each showing the flame drawing on both faces, unlit. from behind the gun they are slivers, from the
-- side a flame tongue. (a camera-facing Beam turned its flame across the shot in Studio, 16 Nov)
type Fl = { a: BasePart, b: BasePart, t: number, life: number, live: boolean }
local flames: { Fl } = {}
local flameI = 0
local function flamePlane(): BasePart
	local p = Instance.new("Part")
	p.Name = "FxFlame"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(1, 1, 0.02); p.CFrame = PARK
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
		local g = Instance.new("SurfaceGui")
		g.Face = face; g.LightInfluence = 0; g.Brightness = 1.3; g.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
		g.CanvasSize = Vector2.new(128, 128); g.Enabled = false
		local im = Instance.new("ImageLabel")
		im.BackgroundTransparency = 1; im.Size = UDim2.fromScale(1, 1); im.Image = TEX.spikeH
		-- (seen on the Front face the part's +X is on the viewer's left: turn the drawing round so its root stays at the
		-- muzzle end, -X, on both faces; the flame is symmetric top to bottom)
		im.Rotation = if face == Enum.NormalId.Front then 180 else 0
		im.Parent = g
		g.Parent = p
	end
	p.Parent = folder
	return p
end
local function flameShow(pos: Vector3, dir: Vector3, len: number, thick: number, color: Color3?, life: number)
	flameI = flameI % 8 + 1
	local F = flames[flameI]
	if not F then F = { a = flamePlane(), b = flamePlane(), t = 0, life = 0, live = false }; flames[flameI] = F end
	local FF = F :: Fl
	-- the drawing's flame fills 0.95 of its width and 0.3 of its height
	local size = Vector3.new(len / 0.95, thick / 0.3, 0.02)
	local up = if math.abs(dir.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	local mid = pos + dir * (len / 2 - 0.08 / 0.4 * len) -- from 0.08 behind the star to 0.32 ahead of it
	local right = dir:Cross(up).Unit
	-- the part's X runs along the barrel (the drawing's root at -X, the muzzle end)
	local cfA = CFrame.fromMatrix(mid, dir, dir:Cross(right).Unit * -1)
	local cfB = cfA * CFrame.Angles(math.pi / 2, 0, 0)
	for _, p in { FF.a, FF.b } do
		p.Size = size
		for _, g in p:GetChildren() do
			local sg = g :: SurfaceGui
			sg.Enabled = true
			local im = sg:FindFirstChildOfClass("ImageLabel")
			if im then im.ImageColor3 = color or Color3.new(1, 1, 1) end
		end
	end
	FF.a.CFrame = cfA; FF.b.CFrame = cfB
	FF.t, FF.life, FF.live = 0, life, true
end
local function flameOff(F: Fl)
	F.live = false
	for _, p in { F.a, F.b } do
		p.CFrame = PARK
		for _, g in p:GetChildren() do (g :: SurfaceGui).Enabled = false end
	end
end

-- things that happen a moment later on the effect clock (the blast's soot)
local timers: { { at: number, fn: () -> () } } = {}
local function after(d: number, fn: () -> ()) table.insert(timers, { at = clockT + d, fn = fn }) end
-- the high-tier skin whose gun a shot left from (set by the skins section further down)
local skinAt: (p: Vector3) -> any = function(_p: Vector3): any return nil end
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

-- little flakes off the surface (fx.js impact's grey squares, here in the surface's colour; long = splinters)
local function chunks(at: Vector3, n: Vector3, count: number, color: Color3, _mat: Enum.Material?, long: boolean?)
	local pe = emAt(CHIPS, at + n * 0.08, n)
	-- (the web's grey-green #999988 turning #444444, with a little of the surface's own colour)
	local c0 = color:Lerp(Color3.fromRGB(153, 153, 136), 0.7)
	pe.Color = cs(c0, c0:Lerp(Color3.fromRGB(68, 68, 68), 0.75))
	pe.Size = if long then ns(0, 0.46 * S * H, 1, 0.26 * S * H) else ns(0, 0.38 * S * H, 1, 0.21 * S * H)
	emit(pe, count)
end
local function puff(at: Vector3, n: Vector3, color: Color3, count: number)
	local pe = emAt(DUST, at + n * 0.15, n)
	pe.Color = cs(color)
	emit(pe, count)
end
local function sparkBurst(at: Vector3, dir: Vector3, count: number)
	emit(emAt(SPARK, at, dir), count)
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

-- a bullet (or pellet) hitting the map (fx.js impact: 10 squares sprayed off the wall; sparks off metal). what flies off
-- depends on the material. o.hole = false: no hole (marbles); o.scale: a smaller or bigger hit
function Fx.impact(at: Vector3, normal: Vector3, inst: Instance?, mat: Enum.Material?, o: { hole: boolean?, scale: number? }?)
	local kind = (mat and KIND[mat]) or "hard"
	if kind == "water" then Fx.splash(at, 0.3); return end
	local part = if inst and inst:IsA("BasePart") then inst else nil
	local visible = part ~= nil and part.Transparency < 0.9
	local base = if part and visible then part.Color else KIND_COL[kind]
	local sc = (o and o.scale) or 1
	local function k(x: number): number return math.max(1, math.floor(x * sc + 0.5)) end
	if kind == "metal" then
		sparkBurst(at + normal * 0.05, normal, k(7))
		chunks(at, normal, k(4), base, Enum.Material.Metal)
		puff(at, normal, Color3.fromRGB(110, 110, 114), 1)
	elseif kind == "glass" then
		chunks(at, normal, k(8), Color3.fromRGB(200, 235, 255), Enum.Material.Glass)
		sparkBurst(at, normal, k(2))
	elseif kind == "wood" then
		chunks(at, normal, k(8), base:Lerp(Color3.fromRGB(225, 195, 150), 0.4), Enum.Material.Wood, true)
		puff(at, normal, base:Lerp(Color3.fromRGB(205, 180, 140), 0.5), 1)
	elseif kind == "soft" then
		puff(at, normal, base:Lerp(Color3.fromRGB(150, 130, 100), 0.4), 2)
		chunks(at, normal, k(6), base, Enum.Material.Ground)
	elseif kind == "cloth" then
		puff(at, normal, base:Lerp(Color3.new(1, 1, 1), 0.4), 1)
		chunks(at, normal, k(4), base, Enum.Material.Fabric)
	else -- concrete, brick, tiles, plastic...: the web's 10 chips, in the surface's colour, and a puff of its dust
		chunks(at, normal, k(10), base, Enum.Material.Slate)
		puff(at, normal, base:Lerp(Color3.fromRGB(200, 195, 188), 0.55), 1)
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

-- the muzzle: the star + its flame + a glow and a light, and the smoke puff for shots seen from away from the muzzle.
-- (the web shows its flash in first person only; here everyone's gun flashes, the same drawing.) big = the web's x1.6
-- guns, fast = over 8 shots a second (a 0.035 s flash). color tints the drawing (nil: as drawn)
local lastPuff, lastPuffAt = -1, Vector3.zero
function Fx.muzzle(at: CFrame, big: boolean, fpv: boolean, color: Color3?, fast: boolean?)
	-- (first person: matched to the web's flash on screen in the frame captures, 16 Nov: 0.45 of the viewmodel's scale)
	local k = (if fpv then FPK * 0.45 else S) * (if big then 1.6 else 1)
	local life = if fast then 0.035 else 0.05
	local pos, dir = at.Position, at.LookVector
	local tint = cs(color or Color3.new(1, 1, 1))
	local f = emAt(if fpv then FLASH else FLASH_TP, pos, dir)
	f.Size = nsk({ { 0, 0.24 * k * 1.1 * H, 0.24 * k * 0.3 * H }, { 1, 0.24 * k * 1.1 * H, 0.24 * k * 0.3 * H } })
	f.Lifetime = NR(life); f.Color = tint
	emit(f, 1)
	-- the flame runs from just behind the star to 0.32 ahead of it, 0.4 long, 0.14 thick (the drawing's flame is 0.3 of
	-- the texture's height), the same 0.8-1.4 size
	local fk = k * (0.8 + math.random() * 0.6)
	flameShow(pos, dir, 0.4 * fk, 0.14 * fk, color, life)
	lightFlash(pos + dir * 0.15 * k, Color3.fromRGB(255, 220, 170), if fpv then 6 else 8, if big then 1.8 else 1.2, life * 1.4)
	-- the smoke: never off your own gun in first person (it would sit in your face)
	local cam = workspace.CurrentCamera
	if cam and (pos - cam.CFrame.Position).Magnitude > 1.3 * S
		and not (clockT - lastPuff < 0.06 and (pos - lastPuffAt).Magnitude < 0.6 * S) then
		lastPuff, lastPuffAt = clockT, pos
		local d = dir * 1.6 + Vector3.new(0, 0.35, 0)
		local p = emAt(MPUFF, pos + dir * 0.15 * S, d)
		p.Speed = NR(d.Magnitude * S)
		emit(p, 1)
	end
end

-- one gun shot as everyone sees it (weapons.js fire feedback): the flash (not through a scope) and a tracer from the
-- muzzle to each end, bent at each bounce (the Revolver). w = the weapon's row in Weapons. the web's numbers: tracer
-- 0.045 m thick for 0.2 s, 0.03 m for 0.07 s on guns over 8 shots a second, the row's own `thick` (sniper, dmr) else
function Fx.gunShot(w: any, at: CFrame, ends: { Vector3 }, path: { any }?, fpv: boolean, noFlash: boolean?)
	local fx = w.fx or {}
	local fast = (w.rate or 0) > 8
	local big = w.id == "shotgun" or w.id == "sniper" or w.id == "autoshot" or w.id == "dmr"
	-- a high-tier skin's own flash and tracer colours (SkinSets.FX), and its after-firing effects switch on
	local sk = skinAt(at.Position)
	if sk then sk.afterT = clockT end
	if not noFlash then Fx.muzzle(at, big, fpv, if sk then sk.spec.flash else nil, fast) end
	if fx.spray or #ends == 0 then return end -- (the marbles are their own tracers)
	local col = (if sk then sk.spec.tracer else nil) or w.tracer or Color3.fromRGB(255, 240, 160)
	local wide = w.thick or (if fast then 0.03 else 0.045) * S
	local life = if fast then 0.07 else 0.2
	local a = at.Position
	-- your own tracer starts 3 studs out, so it never reads as a line out of your eye (first person only)
	if fpv and #ends > 0 and (ends[1] - a).Magnitude > 9 then a += (ends[1] - a).Unit * 3 end
	if path then
		for i, b in path do
			if typeof(b) == "Vector3" and i <= 2 then Fx.tracer(a, b, col, wide, life); a = b end
		end
		Fx.tracer(a, ends[1], col, wide, life)
	else
		for _, e in ends do Fx.tracer(a, e, col, wide, life) end
	end
end

-- the old single star (kept for anything that still calls it): the muzzle without the smoke
function Fx.flash(at: CFrame, big: boolean, color: Color3?, _lightRange: number?)
	Fx.muzzle(at, big, true, color)
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
	ringStep(dt * TS.k)
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

-- sparks (fx.js sparks): hot white / pale yellow streaks flying sideways and up off the edge, turning orange, plus a
-- small white pop (pop = its radius in metres: 0.15, 0.22 for a perfect parry; it just fades)
function Fx.sparks(at: Vector3, dir: Vector3, n: number, pop: number)
	emit(emAt(SPARK, at, Vector3.yAxis * 0.8 - dir * 0.2), n)
	if pop > 0 then
		local p = emAt(POP, at, Vector3.yAxis)
		p.Size = NumberSequence.new(pop * 2 * S * 2.2 * H) -- (the glow's bright middle is under half its width)
		p.Lifetime = NR(if pop > 0.18 then 0.16 else 0.1)
		p.Transparency = ns(0, 0, 1, 1)
		emit(p, 1)
	end
end

-- the melee hit flash (fx.js: a white sphere growing to r metres and fading in 0.3 s) + yellow-to-orange sparks
function Fx.blast(at: Vector3, r: number)
	local p = emAt(POP, at, Vector3.yAxis)
	p.Size = ns(0, 0.3 * r * S * 2.2 * H, 1, r * S * 2.2 * H)
	p.Lifetime = NR(0.3)
	p.Transparency = ns(0, 0.05, 1, 1)
	emit(p, 1)
	Fx.sparks(at, Vector3.yAxis, 24, 0)
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

-- ---------------------------------------------------------------- the frag's blast (fx.js explosion + flipbook.js boomSprite)
-- R = the blast radius in studs (the frag: 7.5 m). the web, in metres (r = R / 3, s = max(3.6, 2.7 r) the fireball's
-- quad): a white pop 0.5 -> 0.5 + r/2 m round in 0.08 s; the baked fireball s * 0.9 -> 1.25 across over 1.5 s,
-- centred s * 0.12 up and rising, with 3 smaller ones (0.45 -> 0.8 s, 1.25-1.75 s) off-centre; 0.65 s later 5 dark
-- soot puffs (0.7 r -> 1.5 r, 2.6-4.2 s) rolling up; 22 hot sparks; 25 white feathers drifting down. on top (the
-- port's own, after the owner's reference clips of layered blasts, 16 Nov): a ring racing out across the floor, the
-- floor's dust kicked up, dark shards flung out, slow cinders drifting up, a scorch on the floor, and a light
type Rig = { part: BasePart, up: Attachment, mid: Attachment, fl: Attachment, core: ParticleEmitter, big: ParticleEmitter,
	small: ParticleEmitter, soot: ParticleEmitter, sparks: ParticleEmitter, feathers: ParticleEmitter, ring: ParticleEmitter,
	kick: ParticleEmitter, shards: ParticleEmitter, cinders: ParticleEmitter, scorch: BasePart, mark: Decal, markT: number, blended: boolean? }
local rigs: { Rig } = {}
local rigI = 0
local function rigEmitter(parent: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Enabled = false; e.Rate = 0; e.LockedToPart = false
	for k, v in props do (e :: any)[k] = v end
	e.TimeScale = TS.k
	e.Parent = parent
	table.insert(ALL, e)
	return e
end
local function newRig(): Rig
	local p = Instance.new("Part")
	p.Name = "FxBlast"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.one; p.CFrame = PARK; p.Parent = folder
	local function att(): Attachment local a = Instance.new("Attachment"); a.Parent = p; return a end
	local up, mid, fl = att(), att(), att()
	local sc = Instance.new("Part")
	sc.Name = "FxScorch"; sc.Anchored = true; sc.CanCollide = false; sc.CanQuery = false; sc.CanTouch = false; sc.CastShadow = false
	sc.Transparency = 1; sc.Size = Vector3.new(1, 0.05, 1); sc.CFrame = PARK; sc.Parent = folder
	local mark = Instance.new("Decal")
	mark.Texture = TEX.glow; mark.Face = Enum.NormalId.Top; mark.Color3 = Color3.fromRGB(0, 0, 0); mark.Transparency = 1; mark.Parent = sc
	return { part = p, up = up, mid = mid, fl = fl, scorch = sc, mark = mark, markT = -1,
		shards = rigEmitter(mid, { Texture = TEX.chips, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(10, 16),
			LightInfluence = 0.8, Color = cs(Color3.fromRGB(70, 66, 62), Color3.fromRGB(44, 42, 40)),
			Size = ns(0, 0.3 * S * H, 1, 0.22 * S * H), Transparency = ns(0, 0, 0.8, 0, 1, 1), Lifetime = NR(0.9, 1.5),
			Speed = NR(8 * S, 20 * S), SpreadAngle = Vector2.new(75, 75), Acceleration = Vector3.new(0, -22 * S, 0), Drag = 0.6,
			Rotation = NR(0, 360), RotSpeed = NR(-420, 420) }),
		cinders = rigEmitter(mid, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 3,
			Color = cs(Color3.fromRGB(255, 170, 80), Color3.fromRGB(255, 96, 30)), Size = ns(0, 0.07 * S * H, 1, 0.03 * S * H),
			Transparency = ns(0, 0, 0.7, 0.2, 1, 1), Lifetime = NR(1.2, 2.2), Speed = NR(2 * S, 7 * S),
			SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 1.5 * S, 0), Drag = 1.5 }),
		core = rigEmitter(mid, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 3, Color = cs(Color3.fromRGB(255, 246, 208)),
			Lifetime = NR(0.1), Speed = NR(0), Transparency = ns(0, 0, 1, 1), ZOffset = 2 }),
		big = rigEmitter(up, { Texture = TEX.boom4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightEmission = 0, LightInfluence = 0,
			Brightness = 1.15, Lifetime = NR(1.5), Speed = NR(0.5 * S), SpreadAngle = Vector2.zero, Rotation = NR(0, 360),
			Transparency = ns(0, 0, 0.75, 0, 1, 1), ZOffset = 1 }),
		small = rigEmitter(p, { Texture = TEX.boom4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightEmission = 0, LightInfluence = 0,
			Brightness = 1.15, Lifetime = NR(1.25, 1.75), Speed = NR(0.6 * S, 1.2 * S), SpreadAngle = Vector2.new(30, 30),
			Rotation = NR(0, 360), RotSpeed = NR(-11, 11), Transparency = ns(0, 0.05, 0.75, 0.05, 1, 1), ZOffset = 0.8 }),
		soot = rigEmitter(p, { Texture = TEX.soft, FlipbookLayout = FLIP8, FlipbookMode = ONESHOT, LightEmission = 0, LightInfluence = 0.35,
			Color = cs(Color3.fromRGB(62, 60, 58)), Lifetime = NR(2.6, 4.2), Speed = NR(0.7 * S, 1.5 * S), SpreadAngle = Vector2.new(30, 30),
			Drag = 0.3, Rotation = NR(0, 360), RotSpeed = NR(-11, 11), Transparency = ns(0, 0.45, 0.75, 0.45, 1, 1) }),
		sparks = rigEmitter(mid, { Texture = TEX.spark, LightEmission = 1, LightInfluence = 0, Brightness = 3,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Color = cs(Color3.fromRGB(255, 242, 176), Color3.fromRGB(255, 122, 26)), Size = ns(0, 0.12 * S * 2.4 * H, 1, 0.04 * S * 2.4 * H),
			Lifetime = NR(0.5, 1), Speed = NR(5.2 * S, 23.4 * S), SpreadAngle = Vector2.new(180, 180),
			Acceleration = Vector3.new(0, -14 * S, 0), Drag = 1.2 }),
		feathers = rigEmitter(mid, { Texture = TEX.chips, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(5, 9),
			LightInfluence = 0.5, Color = cs(Color3.fromRGB(255, 255, 255), Color3.fromRGB(255, 238, 170)),
			Size = ns(0, 0.18 * S * 1.8 * H, 1, 0.15 * S * 1.8 * H), Transparency = ns(0, 0, 0.6, 0.15, 1, 1),
			Lifetime = NR(1.2, 2.4), Speed = NR(3 * S, 12 * S), SpreadAngle = Vector2.new(60, 60),
			Acceleration = Vector3.new(0, -4 * S, 0), Drag = 2.5, Rotation = NR(0, 360), RotSpeed = NR(-200, 200) }),
		ring = rigEmitter(fl, { Texture = TEX.shock, LightEmission = 0.25, LightInfluence = 0.6, Color = cs(Color3.fromRGB(206, 198, 186)),
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Lifetime = NR(0.45), Speed = NR(0.01),
			Transparency = ns(0, 0.45, 1, 1) }),
		kick = rigEmitter(fl, { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 1,
			Color = cs(Color3.fromRGB(176, 170, 162)), Lifetime = NR(0.7, 1.2), SpreadAngle = Vector2.new(80, 80), Drag = 4,
			Rotation = NR(0, 360), RotSpeed = NR(-30, 30), Transparency = ns(0, 0.35, 0.6, 0.5, 1, 1) }),
	}
end
local function floorBelow(at: Vector3, depth: number): Vector3?
	local hit = castMap(at + Vector3.new(0, 0.5, 0), Vector3.new(0, -depth, 0))
	return hit and hit.Position
end
function Fx.explosion(at: Vector3, R: number)
	rigI = rigI % 3 + 1
	local rig = rigs[rigI] or newRig()
	if not rig.blended then rig.blended = true; for _, e in { rig.big, rig.small, rig.soot, rig.kick } do blend(e) end end
	rigs[rigI] = rig
	local r = R / S
	local s = math.max(3.6, r * 2.7) * S
	-- the part is the box the smaller fireballs and the soot come out of (0.8 r wide, from the middle to 0.35 r up)
	rig.part.Size = Vector3.new(0.8 * R, 0.35 * R, 0.8 * R)
	rig.part.CFrame = CFrame.new(at + Vector3.new(0, 0.175 * R, 0))
	rig.mid.WorldPosition = at
	rig.up.WorldPosition = at + Vector3.new(0, s * 0.12, 0)
	rig.core.Size = ns(0, 1 * S * 1.6 * H, 1, (1 + r) * S * 1.6 * H)
	emit(rig.core, 1)
	rig.big.Size = grow(0.9 * s * H, 1.25 * s * H)
	emit(rig.big, 1)
	rig.small.Size = grow(0.45 * s * H, 0.8 * s * H)
	emit(rig.small, 3)
	emit(rig.sparks, 22)
	emit(rig.feathers, 25)
	emit(rig.shards, 14)
	emit(rig.cinders, 30)
	lightFlash(at, Color3.fromRGB(255, 200, 140), math.min(60, R * 1.6), 5, 0.25)
	local soot = rig.soot
	after(0.65, function()
		soot.Size = grow(0.7 * R * H, 1.5 * R * H)
		emit(soot, 5)
	end)
	local fl = floorBelow(at, R * 0.5)
	if fl then
		rig.fl.WorldPosition = fl + Vector3.new(0, 0.15, 0)
		rig.ring.Size = ns(0, 0.2 * R * H, 0.25, 1.4 * R * H, 1, 2.2 * R * H)
		emit(rig.ring, 1)
		rig.kick.Size = grow(0.8 * S * H, 2.6 * S * H)
		rig.kick.Speed = NR(R * 0.6, R * 1.1)
		emit(rig.kick, 14)
		-- a soft dark scorch where it went off, fading over 8 s
		rig.scorch.Size = Vector3.new(R * 0.9, 0.05, R * 0.9)
		rig.scorch.CFrame = CFrame.new(fl + Vector3.new(0, 0.06, 0)) * CFrame.Angles(0, math.random() * 6.28, 0)
		rig.mark.Transparency = 0.25
		rig.markT = clockT
	end
end

-- ---------------------------------------------------------------- smoke bomb clouds (flipbook.js softCloud)
-- the web: soft see-through puffs anywhere in a disc of radius r (6.5 m), 0.4 + h^2 * 3.4 m up (most of them low),
-- 3.3 -> 6..7.6 m across, 3-4.5 s each, rising 0.2-0.65 m/s and spreading; 26 at once, then 24 a second. here: two
-- boxes (low and wide, high and narrower) that puff the web's own smoke sheet. it stops feeding 3 s before the server's
-- cloud ends, so what you see thins out as the cover goes (the gameplay's 10 s)
type Cloud = { lo: BasePart, hi: BasePart, a: ParticleEmitter, b: ParticleEmitter, untilT: number, stopT: number, live: boolean }
local clouds: { [any]: Cloud } = {}
local spareClouds: { Cloud } = {}
local SMOKE_GREY = Color3.fromRGB(214, 214, 214)
local function cloudPart(): BasePart
	local p = Instance.new("Part")
	p.Name = "FxCloud"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.CFrame = PARK; p.Parent = folder
	return p
end
local function puffs(parent: BasePart, rate: number): ParticleEmitter
	local e = rigEmitter(parent, { Texture = TEX.soft, FlipbookLayout = FLIP8, FlipbookMode = ONESHOT, LightInfluence = 1, LightEmission = 0,
		Color = cs(SMOKE_GREY), Size = grow(3.3 * S * H, 6.8 * S * H, 0.8 * S * H), Transparency = ns(0, 0.1, 0.75, 0.1, 1, 1),
		Lifetime = NR(3, 4.5), Rate = rate, Speed = NR(0.6, 1.95), SpreadAngle = Vector2.new(35, 35),
		Rotation = NR(0, 360), RotSpeed = NR(-9, 9) })
	blend(e)
	return e -- (a part's emitter puffs anywhere inside the part's box)
end
function Fx.smokeCloud(id: any, at: Vector3, r: number, left: number)
	if clouds[id] then return end
	local c = table.remove(spareClouds)
	if not c then
		local lo, hi = cloudPart(), cloudPart()
		c = { lo = lo, hi = hi, a = puffs(lo, 17), b = puffs(hi, 9), untilT = 0, stopT = 0, live = true }
	end
	local cc = c :: Cloud
	cc.lo.Size = Vector3.new(1.6 * r, 1.2 * S, 1.6 * r); cc.lo.CFrame = CFrame.new(at + Vector3.new(0, 1 * S, 0))
	cc.hi.Size = Vector3.new(1.3 * r, 2.4 * S, 1.3 * r); cc.hi.CFrame = CFrame.new(at + Vector3.new(0, 2.6 * S, 0))
	cc.untilT = clockT + left; cc.stopT = clockT + math.max(0, left - 3); cc.live = true
	emit(cc.a, 16); emit(cc.b, 10)
	cc.a.Enabled = true; cc.b.Enabled = true
	clouds[id] = cc
end
function Fx.smokeStop(id: any)
	local c = clouds[id]
	if c then c.stopT = math.min(c.stopT, clockT) end
end
local function cloudStep()
	for id, c in clouds do
		if clockT >= c.stopT and c.a.Enabled then c.a.Enabled = false; c.b.Enabled = false end
		if clockT >= math.max(c.untilT, c.stopT) + 4.6 then -- (the last puffs have lived out)
			clouds[id] = nil; c.live = false
			c.lo.CFrame = PARK; c.hi.CFrame = PARK
			table.insert(spareClouds, c)
		end
	end
end

-- ---------------------------------------------------------------- item looks (batch 3)
-- after the owner's reference clips (16 Nov: layered ability effects: a water dome with orbiting bands and a rippling
-- floor; a spiral whirlwind; a black hole). the kind of layering, not their looks; our colours stay the items' own and
-- quiet. the gameplay (sizes, times) stays the web game's: the dome is 4.4 m round for 7 s, the heal lasts 1 s
local DOME_C = Color3.fromRGB(96, 206, 236)
local HEAL_C = Color3.fromRGB(120, 230, 150)
local ITEMFX = emitters(4, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 2, Speed = NR(0),
	Lifetime = NR(0.25), Transparency = ns(0, 0, 1, 1) })
local DROPS = emitters(3, { Texture = TEX.glow, LightEmission = 0.6, LightInfluence = 0.4, Brightness = 1.5,
	Color = cs(Color3.fromRGB(235, 250, 255), DOME_C), Size = ns(0, 0.09 * S * H, 1, 0.03 * S * H), Transparency = ns(0, 0, 0.7, 0.2, 1, 1),
	Lifetime = NR(0.45, 0.95), Speed = NR(1.5 * S, 6 * S), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -14 * S, 0), Drag = 1.5 })
local FLOORRING = emitters(4, { Texture = TEX.shock, LightEmission = 0.7, LightInfluence = 0.3, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
	Speed = NR(0.01), Lifetime = NR(0.5), Transparency = ns(0, 0.2, 1, 1) })
local function floorRing(at: Vector3, color: Color3, r0: number, r1: number, life: number, tr: number)
	local e = emAt(FLOORRING, at + Vector3.new(0, 0.12, 0), Vector3.yAxis)
	e.Color = cs(color); e.Lifetime = NR(life)
	e.Size = ns(0, r0 * 2 * H, 0.3, (r0 + (r1 - r0) * 0.7) * 2 * H, 1, r1 * 2 * H)
	e.Transparency = ns(0, tr, 1, 1)
	emit(e, 1)
end
Fx.floorRing = floorRing

-- a tilted band round a dome or a hole: a thin flat ring (the shock-ring drawing on both faces of a flat part), turned
-- every frame on the effect clock
type Band = { p: BasePart, d1: Decal, d2: Decal, tilt: CFrame, spin: number, live: boolean }
local bands: { Band } = {}
local function band(): Band
	for _, b in bands do if not b.live then b.live = true; return b end end
	local p = Instance.new("Part")
	p.Name = "FxBand"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(1, 0.05, 1); p.CFrame = PARK; p.Parent = folder
	local function dc(face: Enum.NormalId): Decal
		local d = Instance.new("Decal"); d.Texture = TEX.shock; d.Face = face; d.Transparency = 1; d.Parent = p; return d
	end
	local b: Band = { p = p, d1 = dc(Enum.NormalId.Top), d2 = dc(Enum.NormalId.Bottom), tilt = CFrame.identity, spin = 0, live = true }
	table.insert(bands, b)
	return b
end
local function bandOff(b: Band)
	b.live = false; b.p.CFrame = PARK; b.d1.Transparency = 1; b.d2.Transparency = 1
end

-- ---- the shield dome: the item keeps its ForceField ball and floor band (Utility); this adds, on the effect clock: a
-- flash and a ring racing out across the floor as it opens, two faint bands orbiting it, a slow ripple out from its
-- foot every 1.4 s, and when it goes, its skin bursts into droplets that rain down
type DomeFx = { at: Vector3, r: number, floor: Vector3?, b1: Band, b2: Band, t: number, nextRipple: number }
local domesFx: { [any]: DomeFx } = {}
function Fx.domeOpen(id: any, at: Vector3, r: number, floorAt: Vector3?, fresh: boolean)
	if domesFx[id] then return end
	-- (a dome that was already standing, for someone joining late: no opening, the bands already in)
	local t0 = if fresh then 0 else 1
	local d: DomeFx = { at = at, r = r, floor = floorAt, b1 = band(), b2 = band(), t = t0, nextRipple = t0 + 0.6 }
	for i, b in { d.b1, d.b2 } do
		b.p.Size = Vector3.new(r * 2.06, 0.05, r * 2.06)
		b.tilt = CFrame.Angles(if i == 1 then 0.42 else -0.3, 0, if i == 1 then 0.18 else -0.25)
		b.spin = if i == 1 then 0.9 else -0.65
		b.d1.Color3 = DOME_C; b.d2.Color3 = DOME_C
	end
	domesFx[id] = d
	if fresh then
		local g = emAt(ITEMFX, at, Vector3.yAxis)
		g.Color = cs(Color3.fromRGB(225, 250, 255), DOME_C); g.Lifetime = NR(0.3)
		g.Size = ns(0, r * 0.3 * 2 * H, 1, r * 1.2 * 2 * H); g.Transparency = ns(0, 0.35, 1, 1)
		emit(g, 1)
		if floorAt then floorRing(floorAt, DOME_C, r * 0.4, r * 1.25, 0.5, 0.1) end
	end
end
function Fx.domeClose(id: any, popped: boolean)
	local d = domesFx[id]
	if not d then return end
	domesFx[id] = nil
	bandOff(d.b1); bandOff(d.b2)
	if popped then
		-- droplets off its whole skin (web fx.droplets: 40 off the surface, then rain): emitted from 6 points round it
		for i = 0, 5 do
			local a = i / 6 * math.pi * 2
			local p = d.at + Vector3.new(math.cos(a) * d.r * 0.8, d.r * 0.35, math.sin(a) * d.r * 0.8)
			emit(emAt(DROPS, p, (p - d.at).Unit + Vector3.new(0, 0.4, 0)), 7)
		end
		if d.floor then floorRing(d.floor, DOME_C, d.r * 0.9, d.r * 1.4, 0.4, 0.3) end
	end
end
local function domeFxStep(dt: number)
	for _, d in domesFx do
		d.t += dt
		local open = math.min(1, d.t / 0.25)
		for _, b in { d.b1, d.b2 } do
			b.p.CFrame = CFrame.new(d.at) * b.tilt * CFrame.Angles(0, d.t * b.spin, 0)
			local tr = 1 - (1 - 0.72) * open -- faint: the dome's own skin is the star
			b.d1.Transparency = tr; b.d2.Transparency = tr
		end
		if d.floor and d.t >= d.nextRipple then
			d.nextRipple += 1.4
			floorRing(d.floor, DOME_C, d.r * 0.95, d.r * 1.35, 1.1, 0.55)
		end
	end
end

-- ---- the medkit's heal (web: 16 green and white bits rising off the chest over 1 s): two soft green ribbons spiralling
-- up round the body (a Trail on a part that climbs a helix), a ring of light at the feet, sparkles drifting up
type Spiral = { p: BasePart, tr: Trail, root: BasePart, t: number, phase: number, live: boolean }
local spirals: { Spiral } = {}
local SPARKLE = emitters(3, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 2,
	Color = cs(Color3.fromRGB(236, 255, 240), HEAL_C), Size = ns(0, 0.06 * S * H, 0.5, 0.09 * S * H, 1, 0), Transparency = ns(0, 0.1, 1, 1),
	Lifetime = NR(0.6, 1), Speed = NR(1.2 * S, 2.6 * S), SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0, 1.5 * S, 0), Drag = 1.5 })
local function spiral(): Spiral
	for _, s in spirals do if not s.live then s.live = true; return s end end
	local p = Instance.new("Part")
	p.Name = "FxSpiral"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.one * 0.2; p.CFrame = PARK; p.Parent = folder
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position = Vector3.new(0, 0.18 * S, 0); a1.Position = Vector3.new(0, -0.18 * S, 0); a0.Parent = p; a1.Parent = p
	local tr = Instance.new("Trail")
	tr.Attachment0 = a0; tr.Attachment1 = a1; tr.Texture = TEX.tracer; tr.LightEmission = 1; tr.LightInfluence = 0; tr.Brightness = 1.5
	tr.Color = cs(Color3.fromRGB(236, 255, 240), HEAL_C); tr.Transparency = ns(0, 0.15, 1, 1); tr.Lifetime = 0.35
	tr.WidthScale = ns(0, 1, 1, 0); tr.FaceCamera = true; tr.Enabled = false; tr.Parent = p
	local s: Spiral = { p = p, tr = tr, root = p, t = 0, phase = 0, live = true }
	table.insert(spirals, s)
	return s
end
function Fx.heal(root: BasePart)
	for i = 0, 1 do
		local s = spiral()
		s.root, s.t, s.phase = root, 0, i * math.pi
		s.p.CFrame = root.CFrame
		s.tr:Clear(); s.tr.Enabled = true
	end
	local feet = root.Position - Vector3.new(0, 0.95 * S, 0)
	floorRing(feet, HEAL_C, 0.3 * S, 1.1 * S, 0.7, 0.35)
	local e = emAt(SPARKLE, root.Position + Vector3.new(0, 0.2 * S, 0), Vector3.yAxis)
	emit(e, 16)
end
local function spiralStep(dt: number)
	for _, s in spirals do
		if not s.live then continue end
		s.t += dt
		if s.t >= 1.05 or not s.root.Parent then
			s.tr.Enabled = false
			if s.t >= 1.5 then s.live = false; s.p.CFrame = PARK end
			continue
		end
		-- 1.75 turns in 1 s, from the shins to over the head, the radius closing in as it climbs
		local u = s.t / 1.05
		local a = s.phase + u * math.pi * 3.5
		local rr = (0.55 - 0.2 * u) * S
		local y = (-0.75 + 1.6 * u) * S
		local c = s.root.Position
		s.p.CFrame = CFrame.lookAt(c + Vector3.new(math.cos(a) * rr, y, math.sin(a) * rr), c + Vector3.new(math.cos(a + 0.4) * rr, y + 0.1, math.sin(a + 0.4) * rr))
	end
end

-- ---- the rubber duck's hole: the item keeps its core, shell, ring and orbiting duck (Utility); this adds a bright rim
-- (light bent round the edge), dust streaking in on a spiral, and the pop: everything sucked in for a beat, then a
-- violet flash, a ring out across the floor and the bits flung out
local HOLE_C = Color3.fromRGB(150, 110, 220)
type HoleFx = { at: Vector3, R: number, rim: Band, swirl: ParticleEmitter, host: BasePart, t: number }
local holesFx: { [any]: HoleFx } = {}
local swirlHosts: { BasePart } = {}
function Fx.holeOpen(id: any, at: Vector3, R: number, age: number?)
	if holesFx[id] then return end
	local h = table.remove(swirlHosts)
	if not h then
		local p = Instance.new("Part")
		p.Name = "FxHole"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1; p.Shape = Enum.PartType.Ball; p.Parent = folder
		rigEmitter(p, { Texture = TEX.spark, LightEmission = 1, LightInfluence = 0, Brightness = 2, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Color = cs(Color3.fromRGB(215, 195, 255), HOLE_C), Size = ns(0, 0.16 * S * H, 1, 0.05 * S * H), Transparency = ns(0, 0.6, 0.3, 0.1, 1, 1),
			Lifetime = NR(0.55, 0.8), Rate = 30, Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
			ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Drag = 0 })
		h = p
	end
	local hp = h :: BasePart
	hp.Size = Vector3.one * R * 0.9; hp.CFrame = CFrame.new(at)
	local e = hp:FindFirstChildOfClass("ParticleEmitter") :: ParticleEmitter
	e.Speed = NR(R * 0.45 / 0.7, R * 0.45 / 0.55)
	e.Enabled = true
	local rim = band()
	rim.p.Size = Vector3.new(3.4 * S, 0.05, 3.4 * S); rim.tilt = CFrame.identity; rim.spin = 0
	rim.d1.Color3 = Color3.fromRGB(205, 180, 255); rim.d2.Color3 = rim.d1.Color3
	holesFx[id] = { at = at, R = R, rim = rim, swirl = e, host = hp, t = math.max(0, age or 0) } -- (age: already open for late joiners)
end
function Fx.holeMove(id: any, at: Vector3)
	local h = holesFx[id]
	if h then h.at = at; h.host.CFrame = CFrame.new(at) end
end
function Fx.holePop(id: any, at: Vector3?, r: number?)
	local h = holesFx[id]
	if h then
		holesFx[id] = nil
		h.swirl.Enabled = false; h.host.CFrame = PARK
		table.insert(swirlHosts, h.host)
		bandOff(h.rim)
	end
	if not at then return end
	local rr = r or 9 * S
	-- a beat of collapse (a dark glow folding in), then the flash, the ring and the burst
	local g = emAt(ITEMFX, at, Vector3.yAxis)
	g.Color = cs(Color3.fromRGB(235, 220, 255), HOLE_C); g.Lifetime = NR(0.3)
	g.Size = ns(0, rr * 0.25 * 2 * H, 0.25, rr * 0.6 * 2 * H, 1, rr * 0.9 * 2 * H); g.Transparency = ns(0, 0.1, 1, 1)
	emit(g, 1)
	local fl = floorBelow(at, rr * 0.6)
	if fl then floorRing(fl, HOLE_C, rr * 0.2, rr * 1.1, 0.45, 0.15) end
	lightFlash(at, Color3.fromRGB(190, 150, 255), math.min(60, rr * 1.4), 5, 0.3)
end
local function holeFxStep(dt: number)
	for _, h in holesFx do
		h.t += dt
		local cam = workspace.CurrentCamera
		-- the rim faces the camera (light bending round the edge is seen from everywhere), pulsing a little
		local look = if cam then (cam.CFrame.Position - h.at) else Vector3.zAxis
		h.rim.p.CFrame = CFrame.lookAt(h.at, h.at + look) * CFrame.Angles(math.pi / 2, 0, 0)
		local g = math.min(1, h.t / 0.3)
		local k = g * (1 + 0.06 * math.sin(h.t * 20))
		h.rim.p.Size = Vector3.new(3.4 * S * k, 0.05, 3.4 * S * k)
		local tr = 1 - 0.55 * g
		h.rim.d1.Transparency = tr; h.rim.d2.Transparency = tr
	end
end

-- ---------------------------------------------------------------- high-tier skins' own effects (SkinSets.FX)
-- the gun models session's spec (roblox/src/shared/SkinSets.luau): per skin, idle particles at points on the gun
-- (metres in the gun's frame: x right, y up, z back), mirrored with `both`, some only after firing (`afterFire`); a glow
-- colour; its own flash and tracer colours. Fx.skinIdle hangs the emitters on a built gun (WeaponModels.build: k =
-- studs per metre; the viewmodel's and every third-person copy), and a shot from a registered gun takes its colours.
-- cheap: a few slow particles each, nothing in front of the sights (the points are behind and beside the optic)
type SkinFx = { model: Model, spec: any, muzzle: Attachment?, after: { ParticleEmitter }, afterT: number }
local skinned: { [Model]: SkinFx } = {}
local function skinSpec(model: Model): any
	local id = model:GetAttribute("Skin")
	if type(id) ~= "string" then return nil end
	local m = Shared:FindFirstChild("SkinSets")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, SS = pcall(require, m)
	return if ok and type(SS) == "table" and SS.FX then SS.FX[id] else nil
end
-- one kind's particle: a texture, how it moves, how it fades. sz = the spec's size (metres) x k
local function skinProps(e: any, sz: number, k: number): { [string]: any }
	local col = e.colour or Color3.new(1, 1, 1)
	local kind = e.kind
	local fall = e.drift == "fall"
	local life = NR((e.life or 1) * 0.8, (e.life or 1) * 1.2)
	local fade = ns(0, 1, 0.15, 0.05, 0.75, 0.1, 1, 1)
	if kind == "feather" then -- (the drawing's feather is 0.88 of its height)
		return { Texture = TEX.feather, Color = cs(col), LightInfluence = 0.6, LightEmission = 0.15, Size = NumberSequence.new(sz / 0.88 * H),
			Transparency = fade, Lifetime = life, Speed = NR(0.05 * k, 0.2 * k), SpreadAngle = Vector2.new(180, 180),
			Acceleration = Vector3.new(0, (if fall then -0.6 else 0.3) * k, 0), Drag = 3, Rotation = NR(0, 360), RotSpeed = NR(-90, 90) }
	elseif kind == "petal" then
		return { Texture = TEX.petal, Color = cs(col), LightInfluence = 0.7, LightEmission = 0.1, Size = NumberSequence.new(sz / 0.8 * H),
			Transparency = fade, Lifetime = life, Speed = NR(0.05 * k, 0.25 * k), SpreadAngle = Vector2.new(180, 180),
			Acceleration = Vector3.new(0, (if fall then -0.4 else 0.3) * k, 0), Drag = 3, Rotation = NR(0, 360), RotSpeed = NR(-120, 120) }
	elseif kind == "sparkle" then -- (twinkles: grows in, shrinks away)
		return { Texture = TEX.sparkle, Color = cs(col), LightInfluence = 0, LightEmission = 1, Brightness = 2,
			Size = ns(0, 0, 0.35, sz / 0.97 * H, 1, 0), Transparency = NumberSequence.new(0.1), Lifetime = life,
			Speed = NR(0.02 * k, 0.1 * k), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, (if fall then -0.2 else 0.25) * k, 0),
			Drag = 2, Rotation = NR(-15, 15), RotSpeed = NR(-40, 40) }
	elseif kind == "ember" then -- (the glow's bright middle is under half its width)
		return { Texture = TEX.glow, Color = cs(col, col:Lerp(Color3.fromRGB(120, 20, 0), 0.6)), LightInfluence = 0, LightEmission = 1, Brightness = 3,
			Size = ns(0, sz / 0.45 * H, 1, 0), Transparency = ns(0, 0.1, 0.7, 0.3, 1, 1), Lifetime = life,
			Speed = NR(0.05 * k, 0.25 * k), SpreadAngle = Vector2.new(30, 30), Acceleration = Vector3.new(0, (if fall then -0.3 else 0.6) * k, 0), Drag = 1.5 }
	elseif kind == "bubble" then -- (a soap bubble: rises with a slow wobble, swells a touch and is gone at the end: the pop)
		local w = sz / 0.96 * H
		return { Texture = TEX.bubble, Color = cs(col), LightInfluence = 0.3, LightEmission = 0.35, Brightness = 1.2,
			Size = ns(0, w * 0.5, 0.15, w, 0.85, w * 1.05, 0.93, w * 1.2, 1, w * 0.2),
			Transparency = ns(0, 0.6, 0.12, 0, 0.88, 0.05, 0.93, 0.3, 1, 1), Lifetime = life,
			Speed = NR(0.1 * k, 0.3 * k), SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0.15 * k, (if fall then -0.15 else 0.25) * k, 0),
			Drag = 1.2, Rotation = NR(-10, 10), RotSpeed = NR(-20, 20) }
	else -- haze: a faint soft puff (the heat off a barrel)
		return { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, Color = cs(col), LightInfluence = 0.6,
			Size = grow(sz * H, sz * 2.5 * H), Transparency = ns(0, 0.85, 0.5, 0.75, 1, 1), Lifetime = life,
			Speed = NR(0.1 * k, 0.3 * k), SpreadAngle = Vector2.new(20, 20), Acceleration = Vector3.new(0, (if fall then -0.2 else 0.4) * k, 0), Drag = 1 }
	end
end
function Fx.skinIdle(model: Model, k: number, spec: any?)
	if skinned[model] then return end
	local sp = spec or skinSpec(model)
	local root = model.PrimaryPart
	if not sp or not root then return end
	local S_: SkinFx = { model = model, spec = sp, muzzle = root:FindFirstChild("Muzzle") :: Attachment?, after = {}, afterT = -99 }
	for _, e in sp.idle or {} do
		local pts = {}
		for _, p in e.at or {} do
			table.insert(pts, Vector3.new(p[1], p[2], p[3]))
			if e.both and math.abs(p[1]) > 1e-3 then table.insert(pts, Vector3.new(-p[1], p[2], p[3])) end
		end
		for _, p in pts do
			local att = Instance.new("Attachment")
			att.Name = "SkinFx"; att.Position = p * k; att.Parent = root
			local em = rigEmitter(att, skinProps(e, (e.size or 0.02) * k, k))
			em.Rate = (e.rate or 1) / #pts
			em.Enabled = not e.afterFire
			if e.afterFire then table.insert(S_.after, em) end
		end
	end
	if sp.glow and sp.glow.colour then
		local att = Instance.new("Attachment"); att.Name = "SkinFx"; att.Parent = root
		local l = Instance.new("PointLight")
		l.Color = sp.glow.colour; l.Brightness = 0.5; l.Range = 1.4 * k; l.Shadows = false; l.Parent = att
	end
	skinned[model] = S_
end
function Fx.skinOff(model: Model)
	local S_ = skinned[model]
	if not S_ then return end
	skinned[model] = nil
	local root = model.PrimaryPart
	if root then for _, c in root:GetChildren() do if c.Name == "SkinFx" then c:Destroy() end end end
end
-- the registered skinned gun whose muzzle a shot left from (within 2.5 studs), if any
skinAt = function(p: Vector3): any
	for m, S_ in skinned do
		if not m.Parent then skinned[m] = nil; continue end
		local mz = S_.muzzle
		if mz and (mz.WorldPosition - p).Magnitude < 2.5 then return S_ end
	end
	return nil
end
local function skinStep()
	for m, S_ in skinned do
		if not m.Parent then skinned[m] = nil; continue end
		if #S_.after > 0 then
			local on = clockT - S_.afterT < 1.5
			for _, e in S_.after do if e.Enabled ~= on then e.Enabled = on end end
		end
	end
end
-- (WeaponModels.build calls onBuilt, if set, on every gun it makes: the viewmodel's, each third-person copy, the hub's;
-- skinned ones get their effects. one line in WeaponModels, the gun models session's file)
do
	local wm = Shared:FindFirstChild("WeaponModels")
	if wm and wm:IsA("ModuleScript") then
		local ok, WM = pcall(require, wm)
		if ok and type(WM) == "table" then
			(WM :: any).onBuilt = function(m: Model, k: number)
				if m:GetAttribute("Skin") ~= nil then task.defer(Fx.skinIdle, m, k) end
			end
		end
	end
end

-- ---------------------------------------------------------------- the effect clock's stepper
-- tracers fade, lights dim, delayed bits go off, clouds stop feeding; STAT.stepUs = this step's cost (smoothed, us)
RunService.RenderStepped:Connect(function(rdt: number)
	local dt = rdt * TS.k
	if dt <= 0 then return end
	local t0 = os.clock()
	clockT += dt
	for _, pool in beamPools do
		for _, B in pool.list do
			if not B.live then continue end
			B.t += dt
			local u = B.t / B.life
			if u >= 1 then B.live = false; B.b.Enabled = false; continue end
			if B.fade then B.b.Transparency = NumberSequence.new(u) end
		end
	end
	for _, F in flames do
		if not F.live then continue end
		F.t += dt
		if F.t >= F.life then flameOff(F) end
	end
	for _, L in lights do
		if not L.live then continue end
		L.t += dt
		local u = L.t / L.life
		if u >= 1 then L.live = false; L.l.Enabled = false; continue end
		L.l.Brightness = L.b0 * (1 - u)
	end
	for i = #timers, 1, -1 do
		local tm = timers[i]
		if clockT >= tm.at then table.remove(timers, i); tm.fn() end
	end
	cloudStep()
	domeFxStep(dt); spiralStep(dt); holeFxStep(dt); skinStep()
	for _, rg in rigs do -- the scorch marks fade over 8 s
		if rg.markT >= 0 then
			local u = (clockT - rg.markT) / 8
			if u >= 1 then rg.markT = -1; rg.mark.Transparency = 1; rg.scorch.CFrame = PARK
			else rg.mark.Transparency = 0.25 + 0.75 * u * u end
		end
	end
	STAT.stepUs = STAT.stepUs * 0.9 + (os.clock() - t0) * 1e6 * 0.1
end)

-- the effect clock: 0 freezes everything where it is (particles, tracers, lights, the moving bits), 1 is normal
function Fx.setTimeScale(k: number)
	TS.k = math.max(0, k)
	for _, e in ALL do e.TimeScale = TS.k end
end
-- (Studio only: the frame captures freeze every copy of this module at once through a workspace attribute)
if RunService:IsStudio() then
	workspace:GetAttributeChangedSignal("FxTimeScale"):Connect(function()
		local v = workspace:GetAttribute("FxTimeScale")
		Fx.setTimeScale(if type(v) == "number" then v else 1)
	end)
end
-- everything off at once (between captures)
function Fx.clear()
	for _, e in ALL do e:Clear() end
	for _, pool in beamPools do for _, B in pool.list do B.live = false; B.b.Enabled = false end end
	for _, L in lights do L.live = false; L.l.Enabled = false end
	for _, F in flames do flameOff(F) end
	table.clear(timers)
	for i = #bits, 1, -1 do release(bits[i].p) end
	table.clear(bits)
	for _, c in clouds do c.stopT = clockT - 10; c.untilT = clockT - 10 end
	for _, rg in rigs do rg.markT = -1; rg.mark.Transparency = 1; rg.scorch.CFrame = PARK end
	for id in domesFx do Fx.domeClose(id, false) end
	for id in holesFx do Fx.holePop(id) end
	for _, sp in spirals do sp.live = false; sp.tr.Enabled = false; sp.p.CFrame = PARK end
	cloudStep()
end
Fx.clock = function(): number return clockT end
-- load every drawing now, not on the first shot (a fresh 750 KB fireball sheet was still loading on the first blast)
task.spawn(function()
	local list = {}
	for _, id in TEX do if type(id) == "string" and id:find("rbxassetid://") then table.insert(list, id) end end
	pcall(function() game:GetService("ContentProvider"):PreloadAsync(list) end)
end)

return Fx
