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
	bhdisk = "rbxassetid://108998749126513", -- the black hole's accretion disk from above (tools/roblox/vfx/bh_sheets.py)
	bhhalo = "rbxassetid://115358722214312", -- its lensing halo: the photon ring and the bent-over arcs
	-- black hole v3 (17 Nov; tools/roblox/vfx/bh3_sheets.py)
	bhdisk3 = "rbxassetid://102511491188854", -- the disk from above: white-hot inner edge, orange, then magenta and purple clouds
	bhhalo3 = "rbxassetid://135232907882413", -- the warm photon ring and the lensed arcs over the top and under the bottom
	bhshade = "rbxassetid://121099071721160", -- a soft round shade, white (tinted dark: the dark twins)
	bhflare = "rbxassetid://100443875393789", -- the opening's lens flare: a hot core, a long thin level streak, thin rays
	-- the high-tier skins' bullet trails (17 Nov; tools/roblox/vfx/trail_sheets.py), white for Fx to tint
	heart = "rbxassetid://108731430634300", -- a small soft heart (Wish Duck)
	dash = "rbxassetid://100999224406963", -- a Beam strip: one dash and a gap along its length, wrapped into a rail (Streamliner)
	cotton2 = "rbxassetid://96781809339333", -- a thick lumpy smoke puff, 64 frames (8x8; tools/roblox/vfx/cotton_sheet.py)
	lumps = "rbxassetid://82728391412819", -- 16 dense crisp lumpy puffs (4x4; tools/roblox/vfx/lumps_sheet.py): fireball, smoke
	streak = "rbxassetid://127914373549121", -- a soft white streak (the spark drawing is warm)
	pulse = "rbxassetid://84623963828273", -- a Beam strip: one soft bead of light along u, a tight core across v (tools/roblox/vfx/vine_sprite.py)
	flame = "rbxassetid://77597527828324", -- a flame tongue licking up, 16 frames (4x4; tools/roblox/vfx/flame_sheet.py)
	-- the muzzle flash since 17 Nov (the owner: the web's 16-point star "looks kinda ugly"): flame tongues from Kenney's
	-- Particle Pack (CC0, kenney.nl) laid out by tools/roblox/vfx/mflash_sheet.py; warm as drawn, the N ones white for
	-- a skin's own flash colour
	mflash = "rbxassetid://114197784927969", -- the flash seen down the barrel: 5-7 uneven tongues round a hot core (2x2)
	mflashN = "rbxassetid://94655748843416",
	mside = "rbxassetid://131614116535562", -- one tongue lying along +X, its root at the left (2x2; see SIDE_X0)
	msideN = "rbxassetid://131131912689549",
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
	pe:Emit(math.max(1, math.floor(n * ((Fx :: any).density or 1) + 0.5))) -- (Settings > GRAPHICS: PARTICLES)
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
-- a ONE-SHOT flipbook plays at its FlipbookFramerate (default 1 frame a second!, at most 30), not over the particle's
-- life: measured in Studio 16 Nov, the fireball sat on its first frame. so: frames / the mean lifetime
local function oneshot(e: ParticleEmitter, frames: number)
	local life = (e.Lifetime.Min + e.Lifetime.Max) / 2
	e.FlipbookFramerate = NR(math.clamp(frames / math.max(life, 0.05), 1, 30))
	blend(e)
end
local function blendPool(p: EmPool, frames: number) for _, e in p.list do oneshot(e.pe, frames) end end
local HOT = cs(Color3.fromRGB(255, 255, 255), Color3.fromRGB(255, 242, 176), Color3.fromRGB(255, 122, 16))

-- the muzzle flash (weapons.js:114-145): the star across the barrel, its flame along it, a soft glow round both. on for
-- 0.05 s (0.035 s on guns over 8 shots a second); each flash flickers between the 4 drawn stars (the web re-rolls its
-- star every frame), a random roll, 0.8-1.4 of its size
local FLASH = emitters(6, { Texture = TEX.mflash, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(60),
	LightEmission = 0.3, LightInfluence = 0, Brightness = 1.0, ZOffset = 0.3, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
	Lifetime = NR(0.05), Speed = NR(0.01), Rotation = NR(0, 360), Transparency = ns(0, 0, 0.7, 0, 1, 0.3) })
-- (one of the 4 stars per flash, held: a 2-3 frame flash must never be a playing flipbook, its blending blurs it)
for _, e in FLASH.list do
	e.pe.FlipbookMode = Enum.ParticleFlipbookMode.Loop; e.pe.FlipbookStartRandom = true
	e.pe.FlipbookFramerate = NR(0)
	pcall(function() (e.pe :: any).FlipbookBlendFrames = false end)
end
local FLASH_TP = emitters(6, { Texture = TEX.mflash, FlipbookLayout = FLIP2, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
	FlipbookStartRandom = true, FlipbookFramerate = NR(0), LightEmission = 0.45, LightInfluence = 0, Brightness = 1.15, ZOffset = 0.3,
	Lifetime = NR(0.05), Speed = NR(0), Rotation = NR(0, 360), Transparency = ns(0, 0, 0.7, 0, 1, 0.3) })
for _, e in FLASH_TP.list do pcall(function() (e.pe :: any).FlipbookBlendFrames = false end) end
local FWHITE = Color3.new(1, 1, 1)
local function flameCS(c: Color3): ColorSequence -- white core -> the glow colour -> a dim tail
	return ColorSequence.new({ ColorSequenceKeypoint.new(0, FWHITE), ColorSequenceKeypoint.new(0.25, c:Lerp(FWHITE, 0.3)),
		ColorSequenceKeypoint.new(0.6, c), ColorSequenceKeypoint.new(1, c:Lerp(Color3.new(0, 0, 0), 0.6)) })
end
-- a flaming skin's shot: flame tongues thrown off the muzzle, coloured by the wrap's glow (FacingCamera, upright)
local FLAMEBURST = emitters(4, { Texture = TEX.flame, FlipbookLayout = FLIP4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
	FlipbookStartRandom = true, FlipbookFramerate = NR(24, 30), LightEmission = 1, LightInfluence = 0, Brightness = 2,
	Lifetime = NR(0.14, 0.24), SpreadAngle = Vector2.new(28, 28), Drag = 6, Rotation = NR(-20, 20),
	Transparency = ns(0, 0, 0.6, 0.2, 1, 1) })
-- the shot's smoke off the muzzle (flipbook.js muzzlePuff: 0.22 -> 0.85 m, 0.55-0.8 s, half see-through, 1.6 m/s along
-- the shot and a little up, drag 3.5). only for a muzzle over 1.3 m from the camera (never your own gun in first
-- person), at most one every 60 ms from about the same spot
local MPUFF = emitters(6, { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 1,
	Color = cs(Color3.fromRGB(176, 176, 176)), Size = grow(0.22 * S * H, 0.85 * S * H), Transparency = ns(0, 0.5, 0.75, 0.5, 1, 1),
	Lifetime = NR(0.55, 0.8), Speed = NR(1.64 * S), SpreadAngle = Vector2.new(6, 6), Drag = 3.5,
	Rotation = NR(0, 360), RotSpeed = NR(-115, 115) })
blendPool(MPUFF, 16)
-- what a bullet knocks off a wall (fx.js impact: 10 grey squares off the normal at 4 m/s +- 3, 0.5 s, 0.15 -> 0.08 m,
-- gravity 12, fading 1 - t^2): Blender flakes, tumbling, in the surface's colour; then a small puff of its dust
local CHIPS = emitters(8, { Texture = TEX.chips, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, FlipbookFramerate = NR(8, 14),
	LightInfluence = 0.6, LightEmission = 0, Size = ns(0, 0.38 * S * H, 1, 0.21 * S * H), Transparency = ns(0, 0, 0.5, 0.25, 0.8, 0.64, 1, 1),
	Lifetime = NR(0.5), Speed = NR(1.5 * S, 7 * S), SpreadAngle = Vector2.new(65, 65), Acceleration = Vector3.new(0, -12 * S, 0),
	Drag = 0, Rotation = NR(0, 360), RotSpeed = NR(-360, 360) })
local DUST = emitters(8, { Texture = TEX.dust, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 1,
	Size = ns(0, 0.2 * S * H, 1, 0.72 * S * H), Transparency = ns(0, 0.82, 0.25, 0.72, 0.6, 0.75, 1, 1),
	Lifetime = NR(0.55, 0.75), Speed = NR(0.5 * S, 1.6 * S), SpreadAngle = Vector2.new(25, 25), Drag = 4,
	Acceleration = Vector3.new(0, 0.4 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-40, 40) })
blendPool(DUST, 16)
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
type Bm = { b: Beam, a0: Attachment, a1: Attachment, t: number, life: number, live: boolean, fade: boolean, tr0: number }
type BmPool = { list: { Bm }, i: number, n: number, props: { [string]: any } }
local beamPools: { BmPool } = {}
local function beamPool(n: number, props: { [string]: any }): BmPool
	local p: BmPool = { list = {}, i = 0, n = n, props = props }
	table.insert(beamPools, p)
	return p
end
-- (tr0: its opacity at the start, 0 = solid; the beam is handed back for a caller that bends it)
local function beam(pool: BmPool, from: Vector3, to: Vector3, color: Color3, w0: number, w1: number, life: number, fade: boolean,
	tr0: number?): Bm
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
		B = { b = b, a0 = a0, a1 = a1, t = 0, life = 1, live = false, fade = true, tr0 = 0 }
		pool.list[pool.i] = B
	end
	local X = B :: Bm
	X.a0.WorldPosition = from; X.a1.WorldPosition = to
	X.b.Color = ColorSequence.new(color); X.b.Width0 = w0; X.b.Width1 = w1
	X.b.Transparency = NumberSequence.new(tr0 or 0); X.b.Enabled = true
	X.t, X.life, X.live, X.fade, X.tr0 = 0, life, true, fade, tr0 or 0
	STAT.beams += 1
	return X
end
-- tracers (fx.js tracer): a straight line from the muzzle to the hit in the gun's colour, its opacity running 1 -> 0
-- over its life; a soft core (the texture's solid middle is about half the beam's width, hence TR_WIDE)
-- (round 2: less glow, so each gun's colour survives on screen: the critic saw them all wash to white)
local TRACERS = beamPool(48, { Texture = TEX.tracer, LightEmission = 0.3, LightInfluence = 0, Brightness = 0.85 })
local TR_WIDE = 1.5
-- taper: the near end's width as a share of the far end's (your own tracer comes to a point at the gun, round 4)
function Fx.tracer(from: Vector3, to: Vector3, color: Color3, width: number, life: number, taper: number?)
	if (to - from).Magnitude < 0.2 then return end
	beam(TRACERS, from, to, color, width * TR_WIDE * (taper or 1), width * TR_WIDE, life, true)
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
		im.BackgroundTransparency = 1; im.Size = UDim2.fromScale(1, 1); im.Image = TEX.mside
		im.ImageRectSize = Vector2.new(512, 512) -- (one of the sheet's four, picked per shot)
		-- (seen on the Front face the part's +X is on the viewer's left: turn the drawing round so its root stays at the
		-- muzzle end, -X, on both faces; the flame is symmetric top to bottom)
		im.Rotation = if face == Enum.NormalId.Front then 180 else 0
		im.Parent = g
		g.Parent = p
	end
	p.Parent = folder
	return p
end
-- where the side sheet's flame shows (alpha over 0.2, measured on the sheet): from SIDE_X0 to SIDE_X1 of a cell's width,
-- SIDE_TH of its height thick
local SIDE_X0, SIDE_X1, SIDE_TH = 0.065, 0.64, 0.15
local function flameShow(pos: Vector3, dir: Vector3, len: number, thick: number, color: Color3?, life: number)
	flameI = flameI % 8 + 1
	local F = flames[flameI]
	if not F then F = { a = flamePlane(), b = flamePlane(), t = 0, life = 0, live = false }; flames[flameI] = F end
	local FF = F :: Fl
	local size = Vector3.new(len / (SIDE_X1 - SIDE_X0), thick / SIDE_TH, 0.02)
	local up = if math.abs(dir.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	-- the flame shows from 0.2 of its length behind the flash to 0.8 ahead of it
	local mid = pos + dir * (size.X * (0.5 - SIDE_X0) - 0.2 * len)
	local cell = Vector2.new(math.random(0, 1) * 512, math.random(0, 1) * 512)
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
			if im then
				im.Image = if color then TEX.msideN else TEX.mside
				im.ImageColor3 = color or Color3.new(1, 1, 1); im.ImageRectOffset = cell
			end
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
local skinShot: (S_: any) -> () = function(_S: any) end
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
	-- (the web's grey-green #999988, #444444 by a quarter second (half its life), a touch of the surface's own colour;
	-- round 2: in the surface's colour they vanished against a white wall)
	local c0 = color:Lerp(Color3.fromRGB(153, 153, 136), 0.9)
	pe.Color = cs(c0, Color3.fromRGB(68, 68, 68), Color3.fromRGB(58, 58, 58))
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
	-- the wall box of a walled arena (tools/roblox/wallbox.py, 18 Nov): bullets stop on it, and instead of chips off thin
	-- air its grid shows where they hit (WallGrid.client says whether it is the wall box there)
	if inst and inst:IsA("BasePart") then
		local m = inst:GetAttribute("Mat")
		if m == "bound" or m == "ledge" then
			local wg = script.Parent:FindFirstChild("WallGridHit")
			if wg and wg:IsA("BindableFunction") and wg:Invoke(at, normal, inst) == true then return end
		end
	end
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
		puff(at, normal, Color3.fromRGB(160, 160, 160):Lerp(base, 0.25), 1)
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
-- how far the nearest wall is from a muzzle (5 = none within 5 studs): three short rays, ahead and to both sides,
-- missing the effects, the camera's viewmodel and everyone's characters
local wallParams = RaycastParams.new()
wallParams.FilterType = Enum.RaycastFilterType.Exclude
local function wallNear(pos: Vector3, dir: Vector3): number
	local skip: { Instance } = { folder }
	local cam = workspace.CurrentCamera
	if cam then table.insert(skip, cam) end
	for _, pl in Players:GetPlayers() do if pl.Character then table.insert(skip, pl.Character) end end
	wallParams.FilterDescendantsInstances = skip
	local side = dir:Cross(Vector3.yAxis)
	side = if side.Magnitude > 0.1 then side.Unit else Vector3.xAxis
	local best = 5
	for _, d in { dir, side, -side } do
		local hit = workspace:Raycast(pos - dir * 0.3, d * 5, wallParams)
		if hit and hit.Distance < best then best = hit.Distance end
	end
	return best
end
function Fx.muzzle(at: CFrame, big: boolean, fpv: boolean, color: Color3?, fast: boolean?)
	-- (first person: matched to the web's flash on screen in the frame captures, 16 Nov: 0.45 of the viewmodel's scale)
	-- (round 2: a quarter bigger, 0.1 m ahead of the muzzle, the handguard hid a quarter of it; others' 1.4x so the star
	-- reads at range instead of a dot)
	-- (round 4: on screen half the web's 0.24 m at its 1 m eye distance: 0.72 of the viewmodel's scale matches it)
	local k = (if fpv then FPK * 0.72 else S * 1.4) * (if big then 1.6 else 1)
	local life = if fast then 0.035 else 0.05
	local pos, dir = at.Position, at.LookVector
	if fpv then pos += dir * 0.16 * FPK end
	-- (17 Nov: the sheet's tongues are coloured as drawn; a skin's flash colour tints the white copy. they fill about half
	-- a cell where the old star filled it all: x1.8 keeps the flash's size on screen)
	local f = emAt(if fpv then FLASH else FLASH_TP, pos, dir)
	f.Texture = if color then TEX.mflashN else TEX.mflash
	local fs = 0.24 * k * 1.1 * H * 1.8
	f.Size = nsk({ { 0, fs, fs * 0.27 }, { 1, fs, fs * 0.27 } })
	f.Lifetime = NR(life); f.Color = cs(color or FWHITE)
	emit(f, 1)
	-- the flame runs from just behind the star to 0.32 ahead of it, 0.4 long, 0.14 thick (the drawing's flame is 0.3 of
	-- the texture's height), the same 0.8-1.4 size
	local fk = k * (0.8 + math.random() * 0.6)
	flameShow(pos, dir, 0.4 * fk, 0.14 * fk * (if fpv then 1.5 else 1), color, life) -- (first person: seen from behind, wider)
	-- (round 13: firing a stud or two from a wall, the light blew half the screen out: the nearest wall within 5 studs,
	-- straight ahead or to either side, dims it; at 2 studs a 1.5 power still lit the wall bright, so squared)
	local near = wallNear(pos, dir)
	local dim = math.clamp((near - 0.4) / 4.6, 0.06, 1) ^ 2
	lightFlash(pos + dir * 0.15 * k, Color3.fromRGB(255, 220, 170), (if fpv then 6 else 8) * math.max(dim, 0.4),
		(if big then 1.8 else 1.2) * dim, life * 1.4)
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

-- ---- the high-tier skins' bullet trails (the owner, 17 Nov: "make sure special weapons have custom bullet trails ... that
-- match the style of the gun"; the gun models session's sheet, one trail shape per skin): SkinSets.FX[id].bullet =
-- { kind = ..., colour = ... } replaces the plain tracer with the kind's own line, a few particles along it and a small
-- flourish where it ends. Cheap: one or two beams and a handful of particles a shot. Your own shot (first person):
-- nothing within 6 studs of the eye or in the first quarter of the path, half as many bits, no ring at the muzzle, the
-- smoke lighter; the line itself starts 3.5 studs out (Fx.gunShot)
--   feathers  (Seraph) a gold-white streak shedding 3-4 white feathers that drift down; a soft gold flare where it lands
--   ember     (Infernal) a hot orange core, a dark smoke wisp lingering behind it, sparks falling off; an ember burst
--   wisp      (Pumpkin Patch) an orange flame wisp, gently S-curved (a curved Beam); a grey puff at the muzzle every
--             third shot
--   bubbles   (Bubble Bath) the pink tracer with soap bubbles along it that swell and pop in ~0.45 s
--   hearts    (Wish Duck) the pink tracer with tiny hearts twinkling along it; a sparkle burst where it lands
--   dust      (Dust Drover) a warm gold streak; a dust kick where it lands
--   powder    (Iron Horse) the gold tracer; a black-powder puff off the muzzle
--   hardlight (Star Drover) a thin white-teal core in a teal glow, a ring flaring off the muzzle; a ring burst where it lands
--   rail      (Streamliner) a teal rail of dashes running forward (vfx_dash, wrapped) with rings along it
--   stars     (Triangulum) a thin gold-white line with small stars twinkling along it; a fading star where it lands
local TRP = {
	feather = emitters(4, { Texture = TEX.feather, LightInfluence = 0.5, LightEmission = 0.3, Color = cs(Color3.fromRGB(252, 248, 238)),
		Size = NumberSequence.new(0.15 * S / 0.88 * H), Transparency = ns(0, 0.05, 0.7, 0.15, 1, 1), Lifetime = NR(1, 1.4), -- (round 16: 0.07 m read as specks at 16 studs)
		Speed = NR(0.3 * S, 0.8 * S), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -1.2 * S, 0), Drag = 2.5,
		Rotation = NR(0, 360), RotSpeed = NR(-140, 140) }),
	spark = emitters(6, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1,
		LightInfluence = 0, Brightness = 3, Color = cs(Color3.fromRGB(255, 214, 140), Color3.fromRGB(255, 84, 28)),
		Size = ns(0, 0.05 * S * 3.4 * H, 1, 0.016 * S * 3.4 * H), Transparency = ns(0, 0, 0.7, 0.2, 1, 1), Lifetime = NR(0.3, 0.5),
		Speed = NR(0.6 * S, 2.2 * S), SpreadAngle = Vector2.new(70, 70), Acceleration = Vector3.new(0, -12 * S, 0), Drag = 1.5 }),
	bubble = emitters(4, { Texture = TEX.bubble, LightInfluence = 0.3, LightEmission = 0.35, Brightness = 1.2,
		Color = cs(Color3.fromRGB(255, 230, 242)), Size = ns(0, 0.1 * S * H, 0.15, 0.2 * S * H, 0.85, 0.21 * S * H, 0.93, 0.24 * S * H, 1, 0.04 * S * H),
		Transparency = ns(0, 0.5, 0.15, 0, 0.85, 0.05, 0.93, 0.3, 1, 1), Lifetime = NR(0.4, 0.55), Speed = NR(0.1 * S, 0.4 * S),
		SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.5 * S, 0), Drag = 1.5, Rotation = NR(-10, 10) }),
	heart = emitters(6, { Texture = TEX.heart, LightEmission = 0.7, LightInfluence = 0, Brightness = 1.6,
		Color = cs(Color3.fromRGB(255, 150, 196)), Size = nsk({ { 0, 0 }, { 0.3, 0.12 * S * H / 0.6, 0.03 * S }, { 1, 0 } }),
		Transparency = NumberSequence.new(0.05), Lifetime = NR(0.35, 0.55), Speed = NR(0.1 * S, 0.4 * S),
		SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.5 * S, 0), Drag = 2, Rotation = NR(-20, 20) }),
	star = emitters(8, { Texture = TEX.sparkle, LightEmission = 1, LightInfluence = 0, Brightness = 2.5,
		Color = cs(Color3.fromRGB(255, 240, 204)), Size = nsk({ { 0, 0 }, { 0.35, 0.12 * S / 0.97 * H, 0.04 * S }, { 1, 0 } }),
		Transparency = NumberSequence.new(0.05), Lifetime = NR(0.4, 0.75), Speed = NR(0.05 * S, 0.2 * S),
		SpreadAngle = Vector2.new(180, 180), Drag = 3, Rotation = NR(-15, 15), RotSpeed = NR(-60, 60) }),
	big = emitters(4, { Texture = TEX.sparkle, LightEmission = 1, LightInfluence = 0, Brightness = 3,
		Size = ns(0, 0, 0.2, 0.4 * S / 0.97 * H, 1, 0), Transparency = ns(0, 0, 0.6, 0.15, 1, 1), Lifetime = NR(0.6),
		Speed = NR(0), Rotation = NR(-10, 10), RotSpeed = NR(-40, 40) }),
	glow = emitters(6, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 2, Speed = NR(0),
		Transparency = ns(0, 0.1, 1, 1) }),
	ring = emitters(8, { Texture = TEX.shock, LightEmission = 1, LightInfluence = 0, Brightness = 2,
		Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Speed = NR(0.01), Transparency = ns(0, 0.1, 1, 1) }),
	puff = emitters(6, { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 0.7,
		LightEmission = 0.05, Transparency = ns(0, 0.35, 0.5, 0.55, 1, 1), Lifetime = NR(0.6, 0.9), Speed = NR(0.3 * S, 0.9 * S),
		SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 0.4 * S, 0), Drag = 2.5, Rotation = NR(0, 360), RotSpeed = NR(-40, 40) }),
	petal = emitters(6, { Texture = TEX.petal, LightInfluence = 0.7, LightEmission = 0.15,
		Color = cs(Color3.fromRGB(240, 176, 194), Color3.fromRGB(250, 226, 232)), Size = NumberSequence.new(0.026 * S / 0.8 * H),
		Transparency = ns(0, 0.05, 0.75, 0.15, 1, 1), Lifetime = NR(0.7, 1.1), SpreadAngle = Vector2.new(50, 50),
		Acceleration = Vector3.new(0, -0.8 * S, 0), Drag = 3, Rotation = NR(0, 360), RotSpeed = NR(-160, 160) }),
	smoke = beamPool(16, { Texture = TEX.tracer, LightEmission = 0, LightInfluence = 0.6, Brightness = 1 }),
	hard = beamPool(12, { Texture = TEX.tracer, LightEmission = 1, LightInfluence = 0, Brightness = 2.4 }),
	dash = beamPool(8, { Texture = TEX.dash, TextureMode = Enum.TextureMode.Wrap, TextureLength = 0.8 * S, TextureSpeed = 2.5,
		LightEmission = 1, LightInfluence = 0, Brightness = 2 }),
	wisp = beamPool(16, { Texture = TEX.tracer, LightEmission = 0.6, LightInfluence = 0, Brightness = 1.3, Segments = 12 }),
	n = setmetatable({}, { __mode = "k" }) :: any, -- (shots per gun spec: the pumpkin's puff every third)
}
for _, e in TRP.puff.list do oneshot(e.pe, 16) end
type TrailO = { col: Color3, wide: number, life: number, fpv: boolean, taper: number?, first: boolean, last: boolean, spec: any }
-- points along a -> b at fractions spread over u0..u1 (jittered), skipping any too near the eye
local function trailPts(a: Vector3, b: Vector3, n: number, u0: number, u1: number, eye: Vector3?, keep: number): { Vector3 }
	local out = {}
	for i = 1, n do
		local u = u0 + (u1 - u0) * ((i - 0.5 + (math.random() - 0.5) * 0.8) / n)
		local p = a:Lerp(b, u)
		if not eye or (p - eye).Magnitude > keep then table.insert(out, p) end
	end
	return out
end
-- an attachment's frame at p with its X axis (a Beam's curve leaves along it) along x
local function axisCF(p: Vector3, x: Vector3): CFrame
	local up = if math.abs(x.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	local z = x:Cross(up).Unit
	return CFrame.fromMatrix(p, x, z:Cross(x).Unit, z)
end
function Fx.bulletTrail(bs: any, a: Vector3, b: Vector3, o: TrailO)
	local len = (b - a).Magnitude
	if len < 0.2 then return end
	local dir = (b - a) / len
	local kind = bs.kind
	local col = bs.colour or o.col
	local cam = workspace.CurrentCamera
	local eye = if o.fpv and cam then cam.CFrame.Position else nil
	local keep = 6
	local u0 = if o.fpv then 0.25 else 0.08
	local function count(n: number): number return if o.fpv then math.max(1, math.floor(n / 2)) else n end
	local function along(pool: EmPool, n: number, d: Vector3?)
		for _, p in trailPts(a, b, count(n), u0, 0.95, eye, keep) do emit(emAt(pool, p, d or Vector3.yAxis), 1) end
	end
	local function glowAt(c: Color3, size: number, life: number)
		local g = emAt(TRP.glow, b - dir * 0.15, -dir)
		g.Color = cs(c); g.Size = ns(0, size * 0.6, 0.3, size, 1, size * 0.4); g.Lifetime = NR(life)
		emit(g, 1)
	end
	local tw = o.wide * TR_WIDE
	if kind == "feathers" then
		Fx.tracer(a, b, col, o.wide * 1.1, o.life * 1.15, o.taper)
		along(TRP.feather, 4)
		if o.last then glowAt(Color3.fromRGB(255, 214, 130), 0.35 * S, 0.2) end
	elseif kind == "ember" then
		Fx.tracer(a, b, Color3.fromRGB(255, 150, 66), o.wide * 0.85, o.life, o.taper)
		local sa = if o.fpv then a + dir * math.min(len * 0.5, 4) else a
		beam(TRP.smoke, sa, b, Color3.fromRGB(62, 50, 46), tw * 1.8, tw * 2.8, 0.7, true, if o.fpv then 0.75 else 0.4) -- (round 16: 0.45 s from 0.55 was gone by 0.3)
		along(TRP.spark, 4, -dir * 0.3 + Vector3.new(0, -0.6, 0))
		if o.last then
			emit(emAt(TRP.spark, b - dir * 0.1, -dir + Vector3.new(0, 0.6, 0)), 6)
			glowAt(Color3.fromRGB(255, 120, 50), 0.3 * S, 0.15)
		end
	elseif kind == "wisp" then
		local B = beam(TRP.wisp, a, b, col, tw * 0.9 * (o.taper or 1), tw * 1.1, o.life * 1.2, true)
		local side = dir:Cross(Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5))
		side = if side.Magnitude > 1e-3 then side.Unit else dir:Cross(Vector3.yAxis).Unit
		local x = (dir + side * 0.12).Unit
		B.a0.WorldCFrame = axisCF(a, x); B.a1.WorldCFrame = axisCF(b, x)
		B.b.CurveSize0 = len * 0.33; B.b.CurveSize1 = len * 0.33
		B.b.Color = cs(Color3.fromRGB(255, 206, 120), col, Color3.fromRGB(255, 104, 36))
		if o.first and not o.fpv then
			local n = (TRP.n[bs] or 0) + 1
			TRP.n[bs] = n
			if n % 3 == 0 then
				local p = emAt(TRP.puff, a + dir * 0.3 * S, dir + Vector3.new(0, 0.4, 0))
				p.Color = cs(Color3.fromRGB(176, 168, 160)); p.Size = grow(0.1 * S * H, 0.32 * S * H)
				emit(p, 1)
			end
		end
	elseif kind == "bubbles" then
		Fx.tracer(a, b, col, o.wide, o.life, o.taper)
		along(TRP.bubble, 2)
	elseif kind == "hearts" then
		Fx.tracer(a, b, col, o.wide, o.life, o.taper)
		along(TRP.heart, 5)
		if o.last then
			local s = emAt(TRP.star, b - dir * 0.15, -dir)
			s.Color = cs(Color3.fromRGB(255, 226, 150), Color3.fromRGB(255, 160, 200)); s.Speed = NR(0.8 * S, 2 * S)
			emit(s, 6)
		end
	elseif kind == "dust" then
		Fx.tracer(a, b, col, o.wide * 1.15, o.life, o.taper)
		if o.last then
			local p = emAt(TRP.puff, b - dir * 0.2, -dir + Vector3.new(0, 0.8, 0))
			p.Color = cs(Color3.fromRGB(206, 182, 142)); p.Size = grow(0.12 * S * H, 0.45 * S * H)
			emit(p, 2)
		end
	elseif kind == "powder" then
		Fx.tracer(a, b, col, o.wide, o.life, o.taper)
		if o.first and not o.fpv then
			local p = emAt(TRP.puff, a + dir * 0.35 * S, dir + Vector3.new(0, 0.25, 0))
			p.Color = cs(Color3.fromRGB(74, 68, 64)); p.Size = grow(0.15 * S * H, 0.55 * S * H)
			emit(p, 2)
		end
	elseif kind == "hardlight" then
		Fx.tracer(a, b, col, o.wide, o.life, o.taper)
		beam(TRP.hard, a, b, Color3.fromRGB(214, 255, 250), tw * 0.35 * (o.taper or 1), tw * 0.35, o.life, true)
		if o.first and not o.fpv then
			local r = emAt(TRP.ring, a + dir * 0.35 * S, dir)
			r.Color = cs(col); r.Size = ns(0, 0.04 * S, 1, 0.3 * S); r.Lifetime = NR(0.15)
			emit(r, 1)
		end
		if o.last then
			local r = emAt(TRP.ring, b - dir * 0.1, -dir)
			r.Color = cs(col); r.Size = ns(0, 0.08 * S, 1, 0.6 * S); r.Lifetime = NR(0.22)
			emit(r, 1)
			glowAt(col, 0.25 * S, 0.12)
		end
	elseif kind == "rail" then
		beam(TRP.dash, a, b, col, tw * 1.3 * (o.taper or 1), tw * 1.3, o.life * 1.3, true)
		for _, p in trailPts(a, b, count(5), u0, 0.95, eye, keep) do
			local r = emAt(TRP.ring, p, dir)
			r.Color = cs(col); r.Size = NumberSequence.new(0.16 * S); r.Lifetime = NR(0.25)
			emit(r, 1)
		end
	elseif kind == "stars" then
		Fx.tracer(a, b, col, o.wide * 0.6, o.life * 1.2, o.taper)
		local s = TRP.star
		for _, p in trailPts(a, b, count(7), u0, 0.97, eye, keep) do
			local e = emAt(s, p, Vector3.yAxis)
			e.Color = cs(col); e.Speed = NR(0.05 * S, 0.2 * S)
			emit(e, 1)
		end
		if o.last then
			local e = emAt(TRP.big, b - dir * 0.2, -dir)
			e.Color = cs(col)
			emit(e, 1)
		end
	else
		Fx.tracer(a, b, col, o.wide, o.life, o.taper)
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
	if sk then sk.afterT = clockT; skinShot(sk) end
	if not noFlash then
		Fx.muzzle(at, big, fpv, if sk then sk.spec.flash else nil, fast)
		if sk and sk.glow and #sk.flames > 0 then
			local fb = emAt(FLAMEBURST, at.Position + at.LookVector * 0.1 * (if fpv then FPK else S), at.LookVector)
			local kk = if fpv then FPK * 0.6 else S
			fb.Color = flameCS(sk.glow); fb.Size = ns(0, 0.12 * kk, 0.4, 0.22 * kk, 1, 0.1 * kk)
			fb.Speed = NR(2 * kk, 5 * kk)
			emit(fb, 6)
		end
	end
	if fx.spray or #ends == 0 then return end -- (the marbles are their own tracers)
	local col = (if sk and sk.glow and #sk.flames > 0 then sk.glow else nil) or (if sk then sk.spec.tracer else nil) or w.tracer
		or Color3.fromRGB(255, 240, 160)
	local wide = (w.thick or (if fast then 0.03 else 0.045) * S) * (if sk and sk.glow and #sk.flames > 0 then 1.6 else 1)
	local life = if fast then 0.07 else 0.2
	local a = at.Position
	-- your own tracer starts 3 studs out, so it never reads as a line out of your eye (first person only)
	if fpv and #ends > 0 and (ends[1] - a).Magnitude > 9 then a += (ends[1] - a).Unit * 3.5 end
	local taper = if fpv then 0.15 else nil
	-- (a high-tier skin's own bullet trail, SkinSets.FX[id].bullet: Fx.bulletTrail; its muzzle bits on the first leg only,
	-- its flourish where the last one ends)
	local bs = if sk then sk.spec.bullet else nil
	local function line(p: Vector3, q: Vector3, tp: number?, first: boolean, last: boolean)
		if bs then
			Fx.bulletTrail(bs, p, q, { col = col, wide = wide, life = life, fpv = fpv, taper = tp, first = first, last = last, spec = bs })
		else
			Fx.tracer(p, q, col, wide, life, tp)
		end
	end
	if path then
		local first = true
		for i, b in path do
			if typeof(b) == "Vector3" and i <= 2 then line(a, b, taper, first, false); a = b; taper = nil; first = false end
		end
		line(a, ends[1], taper, first, true)
	else
		for _, e in ends do line(a, e, taper, true, true) end
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
type Rig = { part: BasePart, up: Attachment, mid: Attachment, fl: Attachment, core: ParticleEmitter,
	soot: ParticleEmitter, sparks: ParticleEmitter, feathers: ParticleEmitter, ring: ParticleEmitter,
	kick: ParticleEmitter, shards: ParticleEmitter, cinders: ParticleEmitter, scorch: BasePart, mark: Decal, markT: number, blended: boolean?,
	bodyBox: BasePart, boom: ParticleEmitter }
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
	-- (round 3, the critic: the 0.5-1.2 s smoke read as a see-through maroon fog with no outline. now the fireball hands
	-- over at 0.3-0.8 s to a cluster of opaque lumpy grey puffs with a few orange hot pockets glowing inside, as the web's
	-- boom turns to rolling dark smoke; the box sits up off the floor so no puff cuts into it)
	local bb = Instance.new("Part")
	bb.Name = "FxBlastBody"; bb.Anchored = true; bb.CanCollide = false; bb.CanQuery = false; bb.CanTouch = false; bb.CastShadow = false
	bb.Transparency = 1; bb.Size = Vector3.one; bb.CFrame = PARK; bb.Parent = folder
	return { part = p, up = up, mid = mid, fl = fl, scorch = sc, mark = mark, markT = -1, bodyBox = bb,
		-- (main, after 7 rounds of layered round particles landing at "soft discs": take the shape from the reference. the
		-- web's own boom bake (`vfx_boom_4x4`: cream fireball -> dark smoke with orange inside -> shrinking smoke) played as
		-- 7 smaller copies clustered, each turned at random, in two waves: one 256 px cell then covers ~5 m, not 30 (the
		-- round-1 blur), and the cluster makes the cauliflower. its colours and timing are the web's own)
		boom = rigEmitter(bb, { Texture = TEX.boom4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightEmission = 0, LightInfluence = 0,
			Brightness = 1, Lifetime = NR(1.4, 1.7), Speed = NR(0.5 * S, 2 * S), SpreadAngle = Vector2.new(180, 180), Drag = 3,
			Acceleration = Vector3.new(0, 0.6 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-15, 15),
			Transparency = ns(0, 0, 0.85, 0, 1, 1) }),
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
		soot = rigEmitter(bb, { Texture = TEX.cotton2, FlipbookLayout = FLIP8, FlipbookMode = ONESHOT, LightEmission = 0, LightInfluence = 0.4,
			Color = cs(Color3.fromRGB(60, 59, 58)), Lifetime = NR(2.2, 3.2), Speed = NR(0.8 * S, 1.6 * S), SpreadAngle = Vector2.new(30, 30),
			Drag = 0.6, Acceleration = Vector3.new(0, 0.5 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-11, 11),
			Transparency = ns(0, 0.4, 0.2, 0.15, 0.7, 0.25, 1, 1) }),
		sparks = rigEmitter(mid, { Texture = TEX.spark, LightEmission = 1, LightInfluence = 0, Brightness = 3,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Color = cs(Color3.fromRGB(255, 226, 140), Color3.fromRGB(255, 140, 30)), Size = ns(0, 0.12 * S * 3.4 * H, 1, 0.05 * S * 3.4 * H),
			Lifetime = NR(0.5, 1), Speed = NR(5.2 * S, 23.4 * S), SpreadAngle = Vector2.new(180, 180),
			Acceleration = Vector3.new(0, -14 * S, 0), Drag = 1.2 }),
		feathers = rigEmitter(mid, { Texture = TEX.feather, -- (round 3: flakes read as round white dots; the feather drawing)
			LightInfluence = 0.5, Color = cs(Color3.fromRGB(255, 255, 255), Color3.fromRGB(255, 238, 170)),
			Size = ns(0, 0.18 * S * 1.8 * H / 0.88, 1, 0.15 * S * 1.8 * H / 0.88), Transparency = ns(0, 0, 0.6, 0.15, 1, 1),
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
	if not rig.blended then
		rig.blended = true
		oneshot(rig.soot, 64); oneshot(rig.kick, 16); oneshot(rig.boom, 16)
	end
	rigs[rigI] = rig
	local r = R / S
	local s = math.max(3.6, r * 2.7) * S
	-- (the rig's part: 0.8 r wide, from the middle to 0.35 r up)
	rig.part.Size = Vector3.new(0.8 * R, 0.35 * R, 0.8 * R)
	rig.part.CFrame = CFrame.new(at + Vector3.new(0, 0.175 * R, 0))
	rig.mid.WorldPosition = at
	rig.up.WorldPosition = at + Vector3.new(0, s * 0.12, 0)
	rig.core.Size = ns(0, 1 * S * 1.6 * H, 1, (1 + r) * S * 1.6 * H)
	emit(rig.core, 1)
	-- the fireball: 7 copies of the web's boom from a box low over the blast (0.45 r wide, centred 0.25 r up), 4 at once
	-- and 3 a moment later so their frames differ; each drawn ~8 m (its fire fills 0.6 of the cell); the size follows the
	-- blast (s = the web's max(3.6, 2.7 r) m: 20 m for the frag)
	local bb = rig.bodyBox
	bb.Size = Vector3.new(0.45 * R, 0.2 * R, 0.45 * R)
	bb.CFrame = CFrame.new(at + Vector3.new(0, 0.25 * R, 0))
	local ks = s / (20 * S)
	local boom = rig.boom
	boom.Size = grow(7 * ks * S * H, 9.5 * ks * S * H, 0.8 * ks * S * H)
	emit(boom, 4)
	after(0.06, function() emit(boom, 3) end)
	emit(rig.sparks, 22)
	emit(rig.feathers, 25)
	emit(rig.shards, 14)
	emit(rig.cinders, 30)
	lightFlash(at, Color3.fromRGB(255, 200, 140), math.min(60, R * 1.6), 5, 0.25)
	-- small dark soot puffs from 0.65 s
	local soot = rig.soot
	after(0.65, function()
		soot.Size = grow(1.5 * 1.3 * S * H, 3.2 * 1.3 * S * H)
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
type Cloud = { lo: BasePart, hi: BasePart, a: ParticleEmitter, b: ParticleEmitter, untilT: number, stopT: number, live: boolean,
	shell: { BasePart }, at: Vector3, r: number, t0: number }
-- the cloud's body: a few soft grey spheres inside the puffs (the research's "mesh shell"). particles thin out on low
-- graphics settings and leave see-through gaps; the shell keeps the cover the same for everyone. faint enough that the
-- puffs, not balls, are what you see
local USE_SHELL = false -- (round 2: the spheres read as hard see-through balls; the puffs carry the cover)
local SHELL = { { 0, 1.3, 0, 0.62 }, { 0.5, 0.9, 0, 0.42 }, { -0.5, 0.9, 0, 0.42 }, { 0, 0.9, 0.5, 0.42 }, { 0, 0.9, -0.5, 0.42 },
	{ 0.3, 1.9, 0.25, 0.36 }, { -0.3, 1.8, -0.3, 0.36 } } -- { x / r, y (studs / S), z / r, radius / r }
local clouds: { [any]: Cloud } = {}
local spareClouds: { Cloud } = {}
local SMOKE_GREY = Color3.fromRGB(226, 229, 232) -- (round 4: a touch cool; the room's warm light made it cream)
local function cloudPart(): BasePart
	local p = Instance.new("Part")
	p.Name = "FxCloud"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.CFrame = PARK; p.Parent = folder
	return p
end
-- (round 2, the critic: the web's wispy puffsoft frames read as thin steam, the pillars showed through; the web's cloud is
-- a solid white mass. now our own thick lumpy puff, which fills about 0.7 of its square: drawn 1.3x to keep the web's
-- 3.3 -> 6.8 m puffs, a few more of them)
local function puffs(parent: BasePart, rate: number): ParticleEmitter
	-- (round 6 tried the shaded lumps here: taller and see-through; the cotton puffs again, with less room light so the
	-- warm rooms don't cream it)
	local e = rigEmitter(parent, { Texture = TEX.cotton2, FlipbookLayout = FLIP8, FlipbookMode = ONESHOT, LightInfluence = 0.4, LightEmission = 0,
		Color = cs(SMOKE_GREY), Size = grow(2.2 * 1.3 * S * H, 4.4 * 1.3 * S * H, 0.5 * S * H), Transparency = ns(0, 0.08, 0.75, 0.08, 1, 1),
		Lifetime = NR(3, 4.5), Rate = rate, Speed = NR(0.3, 1.1), SpreadAngle = Vector2.new(35, 35),
		Rotation = NR(0, 360), RotSpeed = NR(-9, 9) })
	oneshot(e, 64)
	return e -- (a part's emitter puffs anywhere inside the part's box)
end
function Fx.smokeCloud(id: any, at: Vector3, r: number, left: number)
	if clouds[id] then return end
	local c = table.remove(spareClouds)
	if not c then
		local lo, hi = cloudPart(), cloudPart()
		local shell = {}
		for _ in (if USE_SHELL then SHELL else {}) do
			local b = Instance.new("Part")
			b.Name = "FxCloudBody"; b.Shape = Enum.PartType.Ball; b.Material = Enum.Material.SmoothPlastic; b.Color = SMOKE_GREY
			b.Anchored = true; b.CanCollide = false; b.CanQuery = false; b.CanTouch = false; b.CastShadow = false
			b.Transparency = 1; b.CFrame = PARK; b.Parent = folder
			table.insert(shell, b)
		end
		c = { lo = lo, hi = hi, a = puffs(lo, 32), b = puffs(hi, 10), untilT = 0, stopT = 0, live = true, shell = shell,
			at = Vector3.zero, r = 1, t0 = 0 }
	end
	local cc = c :: Cloud
	-- (round 3: low and wide like the web's 0.4-3.8 m, about 2.5 times as wide as it is tall)
	cc.lo.Size = Vector3.new(1.75 * r, 0.8 * S, 1.75 * r); cc.lo.CFrame = CFrame.new(at + Vector3.new(0, 1.5 * S, 0)) -- (round 4: more at the rim)
	cc.hi.Size = Vector3.new(1.1 * r, 0.8 * S, 1.1 * r); cc.hi.CFrame = CFrame.new(at + Vector3.new(0, 2.2 * S, 0))
	cc.untilT = clockT + left; cc.stopT = clockT + math.max(0, left - 3); cc.live = true
	cc.at, cc.r, cc.t0 = at, r, clockT
	emit(cc.a, 26); emit(cc.b, 8)
	cc.a.Enabled = true; cc.b.Enabled = true
	clouds[id] = cc
end
function Fx.smokeStop(id: any)
	local c = clouds[id]
	if c then c.stopT = math.min(c.stopT, clockT) end
end
local function cloudStep()
	for _, c in clouds do -- the body: swells in over 1.2 s, thins out as the feeding stops
		local grow = math.clamp((clockT - c.t0) / 1.2, 0, 1)
		local fade = if clockT >= c.stopT then math.clamp((clockT - c.stopT) / 2.5, 0, 1) else 0
		for i, b in c.shell do
			local sh = SHELL[i]
			local rad = c.r * sh[4] * (0.55 + 0.45 * grow)
			b.Size = Vector3.one * rad * 2
			b.CFrame = CFrame.new(c.at + Vector3.new(sh[1] * c.r, sh[2] * S, sh[3] * c.r))
			b.Transparency = 1 - 0.6 * grow * (1 - fade)
		end
	end
	for id, c in clouds do
		if clockT >= c.stopT and c.a.Enabled then c.a.Enabled = false; c.b.Enabled = false end
		if clockT >= math.max(c.untilT, c.stopT) + 4.6 then -- (the last puffs have lived out)
			clouds[id] = nil; c.live = false
			c.lo.CFrame = PARK; c.hi.CFrame = PARK
			for _, b in c.shell do b.Transparency = 1; b.CFrame = PARK end
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

-- ---- the rubber duck's black hole (the owner, 16 Nov evening: "actual blackhole effect for duck pls"; v3 on 17 Nov after
-- the owner's reference clip: a hot pink spark, a white-gold lens flare, then the hole opens on a warm photon ring and a
-- wide purple and magenta disk with an orange inner edge; looked at for the sequence and the colours, nothing traced).
-- Fx draws the whole hole; Utility keeps the gameplay (3 s, the pull, the pop), the little duck orbiting and the one
-- stuck to someone. The timeline runs from the hole's first message (u; a duck stuck to someone sends it 0.3 s before
-- the pull starts, a duck whose fuse ran out the moment it starts; late joiners skip the opening):
--   0      the spark: a small hot pink point, a soft pink glow and a pink light on what is near
--   0.07   the flare: a white-gold star with a long thin horizontal streak (it stays level on screen, like a lens's),
--          at its biggest about 0.1 s later, shrinking into the opening; the horizon swallows its middle
--   0.2    the hole opens over 0.33 s, quick then settling: the horizon, the disk, the halo and their shades grow together
--   then it holds:
--     a pure black event horizon (a black Neon ball: unlit, no shine), 2 m across as the web's core
--     the accretion disk (vfx_bhdisk3): a flat sprite in the disk's plane, tilted 20 degrees, turning about half a turn
--       a second; copies crossfade (mirror ramps, so the brightness holds) so the clouds keep changing
--     its dark twin under it (vfx_bhshade, normal blend, deep purple): the room behind the disk goes dark so the colours
--       keep their strength on our light maps (VFX-STUDY: dark twins)
--     a warm band in the disk's plane at its hot inner edge, whose near arc crosses the horizon's lower part from the side
--     the lensing halo (vfx_bhhalo3, camera-facing): the thin warm photon ring, the disk's far side bent over the top
--       and under the bottom; a dark round shade behind it (the shadow round the horizon)
--     streaks falling in on a spiral, magenta far out and white-hot at the end; dark flakes on a slower spiral; grey
--       dust on the floor below drawn in; a faint warm-violet light pulse
--   0.16 s before the pop (the hole's age reaches Items.DUCK.holeTime - 0.16) it collapses: everything sucked into the
--   middle, so it is a point when the server's pop comes: a white-gold flare, the glow, a ring out across the floor
-- first person stays clear: within 3.2 horizon radii of the camera the sprites fade (out by 1.4: the one the duck is
-- stuck to has the camera inside the hole and sees only the streaks and flakes pour into them)
local BHK = {
	HZ = 1 * S, -- the horizon's radius (the web's core is 2 m across)
	DISK_W = 3.6 * S, -- the disk sprite's half width (its inner edge, 0.29 of it, just outside the horizon)
	HALO_W = 2.5 * S, -- the halo's (its photon ring at 0.42 of it)
	SHADE_W = 2.1 * S, -- the round shade behind the halo
	BAND_W = 1.24 * S, -- the band (the ring drawing's ring at 0.94 of it: 1.17 m, the disk's hot inner edge; round 15: at
	-- 2.25 m it drew a pale ring round the middle of the disk, a Saturn look)
	FLARE_W = 3.4 * S, -- the opening flare at its biggest (round 15: 2.8 read faint against a lit wall)
	TILT = CFrame.Angles(math.rad(20), 0, math.rad(-6)), -- (round 3: 14 read as a line from the side)
	FLARE_T = 0.07, OPEN0 = 0.2, OPEN1 = 0.53, COLLAPSE = 0.16,
	HOLE_T = ((require(Shared:WaitForChild("Items")) :: any).DUCK.holeTime :: number),
	-- (each disk copy: 1.2 s, in and out over 12 % of it; the next starts as the last begins to go. the shades, the
	-- band and the halo are one long particle each)
	LIFE = 1.2, EVERY = 1.2 * 0.88, LONG = 6,
}
type BH = { hz: BasePart, disk: ParticleEmitter, diskShade: ParticleEmitter, band: ParticleEmitter, halo: ParticleEmitter,
	haloShade: ParticleEmitter, spark: ParticleEmitter, sparkGlow: ParticleEmitter, flare: ParticleEmitter, swirl: BasePart,
	dust: ParticleEmitter, dustAtt: Attachment, fall: ParticleEmitter, outer: BasePart, bits: ParticleEmitter, light: PointLight }
type HoleFx = { at: Vector3, R: number, rig: BH, u: number, age: number, nextLayer: number, nextDust: number, ang: number,
	opened: boolean, flared: boolean, closing: boolean, k: number, f: number, life: number, dc: number, lit: boolean }
local holesFx: { [any]: HoleFx } = {}
local bhFree: { BH } = {}
local bhDying: { { rig: BH, t: number, k0: number } } = {}
local function bhPart(name: string, shape: Enum.PartType): BasePart
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Shape = shape; p.Transparency = 1; p.Size = Vector3.one; p.CFrame = PARK; p.Parent = folder
	return p
end
local function newBH(): BH
	local K = BHK
	local hz = bhPart("FxHoleHorizon", Enum.PartType.Ball)
	hz.Material = Enum.Material.Neon; hz.Color = Color3.new(0, 0, 0); hz.Transparency = 0; hz.Size = Vector3.one * 0.01
	local flat = Enum.ParticleOrientation.VelocityPerpendicular
	local diskAtt = Instance.new("Attachment"); diskAtt.CFrame = K.TILT; diskAtt.Parent = hz
	-- (ZOffset sorts them: the dark shades first, then the glowing layers over them)
	local diskShade = rigEmitter(diskAtt, { Texture = TEX.bhshade, LightEmission = 0, LightInfluence = 0, Color = cs(Color3.fromRGB(16, 6, 28)),
		Orientation = flat, Speed = NR(0.01), LockedToPart = true, Size = NumberSequence.new(0.01), Lifetime = NR(K.LONG), ZOffset = -0.8 })
	local disk = rigEmitter(diskAtt, { Texture = TEX.bhdisk3, LightEmission = 1, LightInfluence = 0, Brightness = 1.8,
		Orientation = flat, Speed = NR(0.01), LockedToPart = true, Size = NumberSequence.new(0.01), Lifetime = NR(K.LIFE),
		Rotation = NR(0, 360), RotSpeed = NR(-200, -160) }) -- (about half a turn a second)
	-- the warm band: from the side its near arc crosses in front of the horizon's lower half (round 4: the side view
	-- read as an eclipse without it)
	local band = rigEmitter(diskAtt, { Texture = TEX.shock, LightEmission = 1, LightInfluence = 0, Brightness = 1.1,
		Orientation = flat, Speed = NR(0.01), LockedToPart = true, Color = cs(Color3.fromRGB(255, 214, 160)),
		Size = NumberSequence.new(0.01), Lifetime = NR(K.LONG), ZOffset = 0.1 })
	local haloAtt = Instance.new("Attachment"); haloAtt.Parent = hz -- (on the middle: an emitter on a part spawns anywhere in it)
	local haloShade = rigEmitter(haloAtt, { Texture = TEX.bhshade, LightEmission = 0, LightInfluence = 0, Color = cs(Color3.fromRGB(10, 4, 18)),
		Speed = NR(0), LockedToPart = true, Size = NumberSequence.new(0.01), Lifetime = NR(K.LONG), ZOffset = -1 })
	local halo = rigEmitter(haloAtt, { Texture = TEX.bhhalo3, LightEmission = 1, LightInfluence = 0, Brightness = 2.2,
		Speed = NR(0), LockedToPart = true, Size = NumberSequence.new(0.01), Lifetime = NR(K.LONG), ZOffset = 0.3 })
	-- the opening: the spark (a hot point and its soft glow; the glow drawing's bright middle is under half its width)
	-- and the flare
	local spark = rigEmitter(haloAtt, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 3,
		Color = cs(Color3.fromRGB(255, 214, 240), Color3.fromRGB(255, 84, 176)), Speed = NR(0), LockedToPart = true,
		Size = ns(0, 0.05 * S, 0.25, 0.24 * S, 1, 0.1 * S), Transparency = ns(0, 0, 0.6, 0.1, 1, 1), Lifetime = NR(0.22), ZOffset = 0.5 })
	local sparkGlow = rigEmitter(haloAtt, { Texture = TEX.glow, LightEmission = 1, LightInfluence = 0, Brightness = 1.2,
		Color = cs(Color3.fromRGB(255, 92, 178)), Speed = NR(0), LockedToPart = true,
		Size = ns(0, 0.2 * S, 0.3, 0.8 * S, 1, 0.5 * S), Transparency = ns(0, 0.45, 0.5, 0.6, 1, 1), Lifetime = NR(0.26), ZOffset = 0.4 })
	local flare = rigEmitter(haloAtt, { Texture = TEX.bhflare, LightEmission = 1, LightInfluence = 0, Brightness = 4,
		Speed = NR(0), LockedToPart = true, Rotation = NR(-8, 8), RotSpeed = NR(-25, 25), Lifetime = NR(0.42) })
	-- the streaks: from a flat band round the disk's plane, 5 m out, ending 1.2 m out (round 4: straight scratches up to
	-- the ceiling); the part turning under them bends each path into a spiral. magenta far out, white-hot at the end
	local swirl = bhPart("FxHoleSwirl", Enum.PartType.Block) -- (a block: a ball part keeps its sides equal)
	swirl.Size = Vector3.new(10 * S, 1.6 * S, 10 * S)
	local fall = rigEmitter(swirl, { Texture = TEX.streak, LightEmission = 1, LightInfluence = 0, Brightness = 2,
		Orientation = Enum.ParticleOrientation.VelocityParallel, LockedToPart = true,
		Color = cs(Color3.fromRGB(226, 112, 236), Color3.fromRGB(255, 226, 190)), Size = ns(0, 0.1 * S, 1, 0.16 * S),
		Squash = ns(0, 0.5, 1, 2), Transparency = ns(0, 1, 0.15, 0.15, 0.75, 0.1, 1, 1), Lifetime = NR(0.8, 0.9),
		Speed = NR(2.6 * S, 2.9 * S), Drag = -1.5, Shape = Enum.ParticleEmitterShape.Cylinder,
		ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Rate = 60 })
	-- the loose bits: small dark flakes from 4.5 m out, slower, tumbling, stretched as they go in
	local outer = bhPart("FxHoleDebris", Enum.PartType.Ball)
	outer.Size = Vector3.one * 9 * S
	local bits = rigEmitter(outer, { Texture = TEX.chips, FlipbookLayout = FLIP2, FlipbookMode = RANDOM, LightEmission = 0,
		LightInfluence = 1, LockedToPart = true, Color = cs(Color3.fromRGB(92, 90, 98), Color3.fromRGB(44, 42, 50)),
		Size = ns(0, 0.45 * S * H, 0.7, 0.4 * S * H, 1, 0.12 * S * H), Transparency = ns(0, 1, 0.15, 0, 0.9, 0, 1, 1), Lifetime = NR(1.5, 1.7),
		Speed = NR(1.7 * S, 2 * S), Drag = -1, Rotation = NR(0, 360), RotSpeed = NR(-300, 300),
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = ns(0, 0, 0.7, 0, 1, 2.5),
		Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Rate = 12 })
	-- grey dust on the floor below drawn in: a flat ring shrinking to the middle, slow at first, quick at the end
	local dustAtt = Instance.new("Attachment"); dustAtt.Parent = hz
	local dust = rigEmitter(dustAtt, { Texture = TEX.shock, LightEmission = 0.3, LightInfluence = 0.7,
		Orientation = flat, Speed = NR(0.01), Color = cs(Color3.fromRGB(150, 148, 156)),
		Size = ns(0, 6 * S * H * 2, 0.5, 4.6 * S * H * 2, 0.8, 2.8 * S * H * 2, 1, 1.2 * S * H * 2),
		Transparency = ns(0, 1, 0.3, 0.84, 0.85, 0.86, 1, 1), Lifetime = NR(0.9) })
	local light = Instance.new("PointLight")
	-- (round 3: at 1.4-2 over 14 m it washed the whole room; a faint pulse on what is near)
	light.Color = Color3.fromRGB(232, 168, 214); light.Range = 6 * S; light.Brightness = 0; light.Shadows = false
	light.Enabled = false; light.Parent = hz
	return { hz = hz, disk = disk, diskShade = diskShade, band = band, halo = halo, haloShade = haloShade, spark = spark,
		sparkGlow = sparkGlow, flare = flare, swirl = swirl, dust = dust, dustAtt = dustAtt, fall = fall, outer = outer, bits = bits,
		light = light }
end
local function bhPark(b: BH)
	b.fall.Enabled = false; b.bits.Enabled = false
	for _, e in { b.disk, b.diskShade, b.band, b.halo, b.haloShade, b.spark, b.sparkGlow, b.flare, b.fall, b.bits, b.dust } do e:Clear() end
	b.hz.Size = Vector3.one * 0.01
	b.hz.CFrame = PARK; b.swirl.CFrame = PARK; b.outer.CFrame = PARK
	b.light.Enabled = false
	table.insert(bhFree, b)
end
-- the hole's size: k = how far open (0..1, the opening and the collapse); the sprites only (the horizon is set each step)
local function bhSize(b: BH, k: number)
	local K = BHK
	k = math.max(k, 0.001)
	b.disk.Size = NumberSequence.new(K.DISK_W * k); b.diskShade.Size = NumberSequence.new(K.DISK_W * 1.08 * k)
	b.band.Size = NumberSequence.new(K.BAND_W * k)
	b.halo.Size = NumberSequence.new(K.HALO_W * k); b.haloShade.Size = NumberSequence.new(K.SHADE_W * k)
end
-- how much of it shows: f = 1 far from the camera, 0 with the camera inside it (first person stays clear)
local function bhFade(b: BH, f: number)
	local o = 0.92 * f
	b.disk.Transparency = ns(0, 1, 0.12, 1 - o, 0.88, 1 - o, 1, 1)
	b.diskShade.Transparency = NumberSequence.new(1 - 0.8 * f)
	b.band.Transparency = NumberSequence.new(1 - 0.75 * f)
	b.halo.Transparency = NumberSequence.new(1 - 0.92 * f)
	b.haloShade.Transparency = NumberSequence.new(1 - 0.85 * f)
	b.flare.Transparency = ns(0, 1 - f, 0.7, 1 - 0.9 * f, 1, 1)
end
-- the flare at the opening (big, slow-ish) or at the pop (smaller, quick)
local function bhFlare(b: BH, pop: boolean)
	local W = BHK.FLARE_W
	if pop then
		b.flare.Lifetime = NR(0.3); b.flare.Size = ns(0, W * 0.5, 0.2, W * 0.85, 1, 0)
	else
		b.flare.Lifetime = NR(0.42); b.flare.Size = ns(0, W * 0.15, 0.25, W, 0.6, W * 0.45, 1, 0)
	end
	emit(b.flare, 1)
end
-- returns true: Fx draws the whole hole (Utility then makes no core, shell or ring of its own). age: the hole's age
-- (below 0 while it is about to open: a duck stuck to someone); life: when it pops (a Duck Rain sky hole's own, 2.6 s;
-- else the duck's)
function Fx.holeOpen(id: any, at: Vector3, R: number, age: number?, life: number?): boolean
	if holesFx[id] then return true end
	local b = table.remove(bhFree) or newBH()
	local a = age or 0
	local h: HoleFx = { at = at, R = R, rig = b, u = math.max(0, a), age = a, nextLayer = 0, nextDust = 0, ang = 0,
		opened = false, flared = false, closing = false, k = -1, f = -1, life = life or BHK.HOLE_T, dc = math.huge, lit = false }
	holesFx[id] = h
	b.hz.CFrame = CFrame.new(at); b.swirl.CFrame = CFrame.new(at); b.outer.CFrame = CFrame.new(at)
	bhSize(b, 0)
	if h.u < BHK.FLARE_T then
		local cam = workspace.CurrentCamera
		if not cam or (cam.CFrame.Position - at).Magnitude > 2.3 * BHK.HZ then -- (not in the face of the one it's stuck to)
			emit(b.spark, 1); emit(b.sparkGlow, 1)
		end
		lightFlash(at, Color3.fromRGB(255, 92, 182), 3.5 * S, 1.1, 0.25) -- (round 15: at 3 over 15 studs it flooded the near wall)
	elseif h.u > BHK.FLARE_T + 0.15 then
		h.flared = true -- (a late joiner: no opening)
	end
	return true
end
function Fx.holeMove(id: any, at: Vector3)
	local h = holesFx[id]
	if h then h.at = at end
end
function Fx.holePop(id: any, at: Vector3?, r: number?)
	local h = holesFx[id]
	local b: BH? = nil
	if h then
		holesFx[id] = nil
		local rig = h.rig
		b = rig
		rig.fall.Enabled = false; rig.bits.Enabled = false
		for _, e in { rig.disk, rig.diskShade, rig.band, rig.halo, rig.haloShade, rig.spark, rig.sparkGlow, rig.flare } do e:Clear() end
		table.insert(bhDying, { rig = rig, t = 0, k0 = rig.hz.Size.X / (2 * BHK.HZ) })
	end
	if not at then return end
	local rr = r or 9 * S
	-- the pop: a white-gold flare where the hole was, a warm-white glow going magenta, a ring out across the floor, a short
	-- sharp light (round 15: 5 over 38 studs for 0.3 s, and a glow 48 studs across, whited out the hall: a snap now)
	if b then bhFlare(b, true) end
	local g = emAt(ITEMFX, at, Vector3.yAxis)
	g.Color = cs(Color3.fromRGB(255, 240, 222), Color3.fromRGB(226, 96, 200)); g.Lifetime = NR(0.16)
	g.Size = ns(0, rr * 0.18 * 2 * H, 0.3, rr * 0.4 * 2 * H, 1, rr * 0.55 * 2 * H); g.Transparency = ns(0, 0.25, 1, 1)
	emit(g, 1)
	local fl = floorBelow(at, rr * 0.6)
	if fl then floorRing(fl, Color3.fromRGB(176, 160, 186), rr * 0.2, rr * 1.1, 0.45, 0.25) end
	lightFlash(at, Color3.fromRGB(240, 176, 236), math.min(60, rr * 0.55), 1.6, 0.12)
end
local function holeFxStep(dt: number)
	local K = BHK
	local cam = workspace.CurrentCamera
	local camPos = if cam then cam.CFrame.Position else Vector3.zero
	for _, h in holesFx do
		h.u += dt; h.age += dt; h.ang += dt
		local b = h.rig
		local at = h.at
		if not h.flared and h.u >= K.FLARE_T then
			h.flared = true
			bhFlare(b, false)
			lightFlash(at, Color3.fromRGB(255, 226, 180), 6 * S, 1.6, 0.35) -- (round 15: 4 over 27 studs washed the hall out)
		end
		if not h.opened and h.u >= K.OPEN0 then
			h.opened = true
			b.fall.Enabled = true; b.bits.Enabled = true -- (the light: the budget below)
			emit(b.diskShade, 1); emit(b.disk, 1); emit(b.band, 1); emit(b.haloShade, 1); emit(b.halo, 1)
			h.nextLayer = h.u + K.EVERY
		end
		-- open (eased: quick, then settling) and the collapse just before the pop
		local g = math.clamp((h.u - K.OPEN0) / (K.OPEN1 - K.OPEN0), 0, 1)
		g = 1 - (1 - g) ^ 3
		local c = math.clamp((h.life - h.age) / K.COLLAPSE, 0, 1)
		if c < 1 and not h.closing then h.closing = true; b.fall.Enabled = false; b.bits.Enabled = false end
		local k = g * c ^ 1.3
		-- (the horizon breathes a little once open: 3 % at the web core's 20 rad/s)
		local pulse = if g >= 1 and c >= 1 then 1 + 0.03 * math.sin(h.u * 20) else 1
		b.hz.Size = Vector3.one * 2 * K.HZ * math.max(k * pulse, 0.005)
		b.hz.CFrame = CFrame.new(at)
		b.swirl.CFrame = CFrame.new(at) * K.TILT * CFrame.Angles(0, -h.ang * 3, 0)
		b.outer.CFrame = CFrame.new(at) * K.TILT * CFrame.Angles(0, -h.ang * 0.9, 0)
		if math.abs(k - h.k) > 0.004 or (k >= 1 and h.k < 1) then h.k = k; bhSize(b, k) end
		h.dc = (camPos - at).Magnitude
		local f = math.clamp((h.dc - 1.4 * K.HZ) / (1.8 * K.HZ), 0, 1)
		f = f * f * (3 - 2 * f)
		if math.abs(f - h.f) > 0.02 or ((f <= 0 or f >= 1) and f ~= h.f) then h.f = f; bhFade(b, f) end
		b.light.Brightness = (0.22 + 0.1 * math.sin(h.u * 5)) * k -- (round 4: the walls 10 m off still went lavender)
		if h.opened and not h.closing and h.u >= h.nextLayer then
			h.nextLayer += K.EVERY
			emit(b.disk, 1)
		end
		-- grey dust on the floor under it drawn in (only when the floor is close below)
		if h.opened and not h.closing and h.u >= h.nextDust then
			h.nextDust = h.u + 0.5
			local fl = floorBelow(at, 4 * S)
			if fl then
				b.dustAtt.WorldCFrame = CFrame.new(fl + Vector3.new(0, 0.12, 0))
				emit(b.dust, 1)
			end
		end
	end
	-- the room light budget: only the two open holes nearest the camera light the room (Duck Rain, 17 Nov: with many
	-- holes open their lights stacked into a lavender room); their glow is in the sprites
	local n1: HoleFx?, n2: HoleFx? = nil, nil
	for _, h in holesFx do
		if not h.opened then continue end
		if not n1 or h.dc < (n1 :: HoleFx).dc then n2 = n1; n1 = h
		elseif not n2 or h.dc < (n2 :: HoleFx).dc then n2 = h end
	end
	for _, h in holesFx do
		local lit = h == n1 or h == n2
		if lit ~= h.lit then h.lit = lit; h.rig.light.Enabled = lit end
	end
	-- popped: the horizon (what is left of it) gone in 0.1 s, the light's flash dying; parked once the pop's flare is over
	for i = #bhDying, 1, -1 do
		local d = bhDying[i]
		d.t += dt
		if d.t >= 0.35 then table.remove(bhDying, i); bhPark(d.rig); continue end
		local u = math.min(1, d.t / 0.1)
		d.rig.hz.Size = Vector3.one * 2 * K.HZ * math.max(d.k0 * (1 - u) * (1 - u), 0.005)
		d.rig.light.Brightness = 1.2 * math.max(0, 1 - d.t / 0.12)
	end
end

-- ---------------------------------------------------------------- high-tier skins' own effects (SkinSets.FX)
-- the gun models session's spec (roblox/src/shared/SkinSets.luau): per skin, idle particles at points on the gun
-- (metres in the gun's frame: x right, y up, z back), mirrored with `both`, some only after firing (`afterFire`); a glow
-- colour; its own flash and tracer colours. Fx.skinIdle hangs the emitters on a built gun (WeaponModels.build: k =
-- studs per metre; the viewmodel's and every third-person copy), and a shot from a registered gun takes its colours.
-- cheap: a few slow particles each, nothing in front of the sights (the points are behind and beside the optic)
type SkinFx = { model: Model, spec: any, muzzle: Attachment?, after: { ParticleEmitter }, afterT: number, idle: { ParticleEmitter }, fp: boolean,
	quiet: boolean, flames: { ParticleEmitter }, lit: { BasePart }, glowId: string?, glow: Color3?, glowT: number, k: number,
	shot: { any }, lever: { any }, pulse: { BasePart }, pulsing: boolean, light: PointLight?, vis: BasePart?, tint: { ParticleEmitter },
	coils: { any }, coilBeams: { any } }
local skinned: { [Model]: SkinFx } = {}
local skinGlow: (any, boolean?) -> ()
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
	elseif kind == "mote" then -- (a soft glowing mote: fades in, drifts slowly, fades out, its colour kept; the glow's
		-- bright middle is under half its width)
		local w = sz / 0.45 * H
		return { Texture = TEX.glow, Color = cs(col), LightInfluence = 0, LightEmission = 1, Brightness = 2,
			Size = ns(0, 0, 0.25, w, 0.8, w * 0.9, 1, 0), Transparency = NumberSequence.new(0.15), Lifetime = life,
			Speed = NR(0.02 * k, 0.07 * k), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, (if fall then -0.06 else 0.08) * k, 0),
			Drag = 1.5 }
	elseif kind == "aura" then -- (a soft glow round a piece: big faint glows swelling and fading in place, overlapping into
		-- a slow breathing light; sz = the glow's visible width)
		local w = sz / 0.45 * H
		return { Texture = TEX.glow, Color = cs(col), LightInfluence = 0, LightEmission = 1, Brightness = 1,
			Size = ns(0, w * 0.75, 1, w * 1.1), Transparency = ns(0, 1, 0.45, 0.8, 1, 1), Lifetime = life,
			Speed = NR(0, 0), Rotation = NR(0, 360), RotSpeed = NR(-10, 10) }
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
-- a shot's or a lever cycle's burst (spec.shot / spec.lever): a spark (a hot streak flying off, falling), a puff (a small
-- soft curl of gunsmoke) or steam (a round white chuff: the lumpy cotton puff). sz = the spec's size (metres) x k
local function burstProps(e: any, sz: number, k: number): { [string]: any }
	local col = e.colour or Color3.new(1, 1, 1)
	local life = e.life or (if e.kind == "spark" then 0.15 else 0.8)
	local sp = e.speed or (if e.kind == "spark" then 1.2 elseif e.kind == "steam" then 0.4 else 0.15)
	local spread = e.spread or (if e.kind == "spark" then 35 else 20)
	if e.kind == "spark" then
		return { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, LightInfluence = 0,
			-- (the drawing's streak fills under a third of its square, as the frag's sparks: x3.4. round 11 in Play: at x1 unseen)
			Brightness = 3, Color = cs(col:Lerp(FWHITE, 0.55), col), Size = ns(0, sz * 3.4 * H, 1, sz * 1.4 * H),
			Transparency = ns(0, 0, 0.7, 0.2, 1, 1), Lifetime = NR(life * 0.6, life), Speed = NR(sp * 0.5 * k, sp * k),
			SpreadAngle = Vector2.new(spread, spread), Acceleration = Vector3.new(0, -6 * k, 0), Drag = 2 }
	elseif e.kind == "steam" then
		return { Texture = TEX.cotton2, FlipbookLayout = FLIP8, FlipbookMode = ONESHOT, LightEmission = 0.1, LightInfluence = 0.5,
			Color = cs(col), Size = grow(sz * H, sz * 2.6 * H), Transparency = ns(0, 0.25, 0.5, 0.45, 1, 1),
			Lifetime = NR(life * 0.8, life * 1.1), Speed = NR(sp * 0.6 * k, sp * k), SpreadAngle = Vector2.new(spread, spread),
			Acceleration = Vector3.new(0, 0.35 * k, 0), Drag = 2.5, Rotation = NR(0, 360), RotSpeed = NR(-40, 40) }
	else
		return { Texture = TEX.soft4, FlipbookLayout = FLIP4, FlipbookMode = ONESHOT, LightInfluence = 0.7,
			Color = cs(col), Size = grow(sz * H, sz * 3 * H), Transparency = ns(0, 0.45, 0.5, 0.6, 1, 1),
			Lifetime = NR(life * 0.8, life * 1.2), Speed = NR(sp * 0.5 * k, sp * k), SpreadAngle = Vector2.new(spread, spread),
			Acceleration = Vector3.new(0, 0.3 * k, 0), Drag = 1.5, Rotation = NR(0, 360), RotSpeed = NR(-70, 70) }
	end
end
-- a wrap's glow colour: its own `glow` (hex or Color3), else its neon palette slot, else its brightest saturated colour,
-- else gold (no wrap, or a grey one)
local GOLD = Color3.fromHex("ffc94a")
local Roster = require(Shared:WaitForChild("Roster")) :: any
local function wrapGlow(id: string?): Color3
	local wr = if id then Roster.wrapById[id] else nil
	if not wr then return GOLD end
	if typeof(wr.glow) == "Color3" then return wr.glow end
	if type(wr.glow) == "string" then return Color3.fromHex(wr.glow) end
	if wr.neon and wr.pal[wr.neon[1]] then return wr.pal[wr.neon[1]] end
	local best, score = nil, 0.3
	for _, c in wr.pal do
		local _, sat, val = c:ToHSV()
		if sat * val > score then best, score = c, sat * val end
	end
	return best or GOLD
end
-- the wrap on a built gun: WeaponModels.wrap marks its painted pieces' pictures with "Wrap"; a model may also say WrapId
local function modelWrap(m: Model): string?
	local w = m:GetAttribute("WrapId")
	if type(w) == "string" then return if w == "" then nil else w end
	for _, d in m:GetDescendants() do
		local a = d:GetAttribute("Wrap")
		if type(a) == "string" then return a end
	end
	return nil
end
-- a coiling vine's layers from its colour c: the soft halo c, the body a deeper gold (normal blend: it holds on a white
-- gun and light walls), the core white-hot, the running beads between
local VINE_DEEP = Color3.fromRGB(190, 105, 10)
local function coilShade(c: Color3, role: string): Color3
	if role == "body" then return c:Lerp(VINE_DEEP, 0.45)
	elseif role == "core" then return c:Lerp(FWHITE, 0.7)
	elseif role == "bead" then return c:Lerp(FWHITE, 0.5)
	end
	return c
end
-- a vine's joints on its helix at time t: each joint's X axis along the helix (so the beams between bend into their
-- arcs), its Y axis out from the axis; the helix turns round its axis at cl.rate rad/s (`spin` mirrors the far side)
local function coilPlace(cl: any, t: number)
	local off = t * cl.rate * cl.spin + cl.phase
	local w = cl.T * 2 * math.pi
	for j = 0, cl.n do
		local u = j / cl.n
		local th = u * w * cl.spin + off
		local c_, s_ = math.cos(th), math.sin(th)
		local rad = cl.e1 * c_ + cl.e2 * s_
		local tan = cl.d + (cl.e2 * c_ - cl.e1 * s_) * (cl.r * w * cl.spin)
		cl.atts[j].CFrame = CFrame.fromMatrix(cl.a + cl.d * u + rad * cl.r, tan.Unit, rad)
	end
end
-- (re)colour a skin's flames, lit parts and vines from its gun's wrap; cheap to call: only acts when the wrap changed
skinGlow = function(S_: any, force: boolean?)
	if #S_.flames == 0 and #S_.lit == 0 and #S_.coilBeams == 0 then return end
	local id = modelWrap(S_.model)
	if not force and S_.glow and id == S_.glowId then return end
	S_.glowId = id
	local c = wrapGlow(id)
	S_.glow = c
	local cs_ = flameCS(c)
	for _, e in S_.flames do e.Color = cs_ end
	for _, p in S_.lit do if p.Parent then p.Color = c end end
	-- (idle bits marked `tint` and a `glow.tint` light take the wrap's glow colour too: gold with no wrap)
	if #S_.tint > 0 then local q = ColorSequence.new(c); for _, e in S_.tint do e.Color = q end end
	for _, cb in S_.coilBeams do if cb.tint then cb.b.Color = ColorSequence.new(coilShade(c, cb.role)) end end
	if S_.light and S_.spec.glow and S_.spec.glow.tint then S_.light.Color = c end
end
function Fx.skinIdle(model: Model, k: number, spec: any?)
	if skinned[model] then return end
	local sp = spec or skinSpec(model)
	local root = model.PrimaryPart
	if not sp or not root then return end
	local S_: SkinFx = { model = model, spec = sp, muzzle = root:FindFirstChild("Muzzle") :: Attachment?, after = {}, afterT = -99,
		idle = {}, fp = model:IsDescendantOf(workspace.CurrentCamera), quiet = false, flames = {}, lit = {}, glowId = nil, glow = nil,
		glowT = 0, k = k, shot = {}, lever = {}, pulse = {}, pulsing = false, light = nil, vis = nil, tint = {}, coils = {},
		coilBeams = {} }
	-- (the piece that says whether your own gun is showing: its biggest visible one. the Root is always invisible, so
	-- watching it, as rounds 4-10 did, kept every first-person skin effect off)
	local best = 0
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and d ~= root and d.Transparency < 0.99 and not d:GetAttribute("Hide") then
			local v = d.Size.X * d.Size.Y * d.Size.Z
			if v > best then best = v; S_.vis = d end
		end
	end
	for _, e in sp.idle or {} do
		-- (e.fp: the rate's share in first person, your own gun; 0 = none there)
		local fpK = if S_.fp and type(e.fp) == "number" then e.fp else 1
		if fpK <= 0 then continue end
		local pts = {}
		for _, p in e.at or {} do
			table.insert(pts, Vector3.new(p[1], p[2], p[3]))
			if e.both and math.abs(p[1]) > 1e-3 then table.insert(pts, Vector3.new(-p[1], p[2], p[3])) end
		end
		for _, p in pts do
			local att = Instance.new("Attachment")
			att.Name = "SkinFx"; att.Position = p * k; att.Parent = root
			local em = rigEmitter(att, skinProps(e, (e.size or 0.02) * k, k))
			em.LockedToPart = model:IsDescendantOf(workspace.CurrentCamera) -- (first person: they ride with the view)
			if em.FlipbookMode == ONESHOT then oneshot(em, 16) end
			em.Rate = (e.rate or 1) * fpK / #pts
			em.Enabled = not e.afterFire
			if e.afterFire then table.insert(S_.after, em) else table.insert(S_.idle, em) end
			if e.tint then table.insert(S_.tint, em) end
		end
	end
	-- each shot's and each lever cycle's bursts (the space-western pair: the hammer's spark, the rotor's sparks, gunsmoke
	-- curling off the muzzle, the Iron Horse's steam chuffs and wheel sparks): spec.shot / spec.lever = { kind, colour, n
	-- (or { min, max }) a point, size (metres), life, speed (m/s), spread, delay (s after the shot; a lever's after its
	-- clack), at = points, dir = where they fly (the gun frame; default up), both = mirrored }. emitters wait at the points
	-- (riding the view in first person) and Emit when Fx.gunShot sees a shot from this gun
	local function bursts(list: { any }?, into: { any })
		for _, e in list or {} do
			local d0 = if e.dir then Vector3.new(e.dir[1], e.dir[2], e.dir[3]) else Vector3.yAxis
			local pts = {}
			for _, p in e.at or {} do
				table.insert(pts, { Vector3.new(p[1], p[2], p[3]), d0 })
				if e.both and math.abs(p[1]) > 1e-3 then table.insert(pts, { Vector3.new(-p[1], p[2], p[3]), d0 * Vector3.new(-1, 1, 1) }) end
			end
			for _, pd in pts do
				local att = Instance.new("Attachment")
				att.Name = "SkinFx"; att.Parent = root
				local d = if pd[2].Magnitude > 1e-4 then pd[2].Unit else Vector3.yAxis
				local up = if math.abs(d.Y) > 0.98 then Vector3.xAxis else Vector3.yAxis
				att.CFrame = CFrame.lookAt(pd[1] * k, pd[1] * k + d, up) * CFrame.Angles(-math.pi / 2, 0, 0) -- (+Y along d)
				local em = rigEmitter(att, burstProps(e, (e.size or 0.03) * k, k))
				em.LockedToPart = S_.fp
				if e.kind == "steam" then oneshot(em, 64) elseif e.kind ~= "spark" then oneshot(em, 16) end
				table.insert(into, { em = em, n = e.n or 1, delay = e.delay or 0, puff = e.kind ~= "spark", at = att })
			end
		end
	end
	bursts(sp.shot, S_.shot)
	bursts(sp.lever, S_.lever)
	-- glow pieces that flare on each shot (spec.pulse = { parts = name starts, t = s }: pieces named "<start>...__glow")
	if sp.pulse and sp.pulse.parts then
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") and string.sub(d.Name, -6) == "__glow" then
				for _, pre in sp.pulse.parts do
					if string.sub(d.Name, 1, #pre) == pre then table.insert(S_.pulse, d); break end
				end
			end
		end
	end
	-- trails off glowing edges as the gun moves (spec.trail: segs = { { a, b }, ... } in the gun frame, metres; the ribbon
	-- spans each seg, so a seg along a wing's top feather or a blade gives a streak that width; width1 / width0 taper it
	-- along its length). short and glowing; in first person capped short so turning never smears it across the view
	local tr = sp.trail
	-- (first person: the guns' trails drew as stray straight lines after the draw, so none on a gun there; the katana's
	-- swing trail stays, main's note: it never covers the sights. third person and other players: always)
	local wrow = (Weapons.list :: any)[model.Name]
	local melee = wrow ~= nil and wrow.kind == "melee"
	if tr and tr.segs and (melee or not model:IsDescendantOf(workspace.CurrentCamera)) then
		local fp = model:IsDescendantOf(workspace.CurrentCamera)
		for _, seg in tr.segs do
			local pairs_ = { { seg[1], seg[2] } }
			if tr.both and math.abs(seg[1][1]) + math.abs(seg[2][1]) > 1e-3 then
				table.insert(pairs_, { { -seg[1][1], seg[1][2], seg[1][3] }, { -seg[2][1], seg[2][2], seg[2][3] } })
			end
			for _, ab in pairs_ do
				local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
				a0.Name = "SkinFx"; a1.Name = "SkinFx"
				a0.Position = Vector3.new(ab[1][1], ab[1][2], ab[1][3]) * k; a1.Position = Vector3.new(ab[2][1], ab[2][2], ab[2][3]) * k
				a0.Parent = root; a1.Parent = root
				local t = Instance.new("Trail")
				t.Name = "SkinFx"; t.Attachment0 = a0; t.Attachment1 = a1; t.Texture = TEX.tracer; t.TextureMode = Enum.TextureMode.Stretch
				t.Color = cs(tr.colour or Color3.new(1, 1, 1)); t.LightEmission = 1; t.LightInfluence = 0; t.Brightness = 2
				t.Lifetime = (tr.life or 0.18) * (if fp then 0.6 else 1)
				t.Transparency = ns(0, 0.15, 1, 1)
				local taper = if tr.width0 and tr.width1 and tr.width0 > 0 then tr.width1 / tr.width0 else 0
				t.WidthScale = ns(0, 1, 1, taper)
				t.MinLength = 0.02 * k
				if fp then t.MaxLength = 0.35 * k end
				t.Parent = root
			end
		end
	end
	-- coiling vines of light (17 Nov, the owner's reference clip: weapons wrapped in coiling ribbons of golden light, like
	-- glowing vines; particle strands first, which read as thin dotted arcs): spec.coil = { { a, b (the axis, gun frame,
	-- metres), r (radius), turns (along it), spin (rad/s the helix turns round its axis), strands, colour, size (the
	-- vine's width, metres), pulse (the running beads' TextureSpeed; 0 = none), beads (a quarter turn), fp (its width in
	-- first person, your own gun; 0 = none there), tint, both } }. Each strand is a chain of Beams, one a quarter turn or
	-- less, between attachments on the helix whose X axes lie along it, so each beam bends into its arc (a cubic Bezier:
	-- CurveSize = 4/3 tan(dθ/4) |dp/dθ|). Four layers an arc: a wide soft halo, a deep-gold body, a white-hot core, beads
	-- of light running along; the vine tapers to nothing at both ends. skinStep turns the helix, so it winds along the gun
	-- like a barber's pole. Beams ride the gun, so first person has them too (the particles smeared there)
	for _, c in sp.coil or {} do
		local fpK = if S_.fp and type(c.fp) == "number" then c.fp else 1
		if fpK <= 0 then continue end
		local axes = { { Vector3.new(c.a[1], c.a[2], c.a[3]), Vector3.new(c.b[1], c.b[2], c.b[3]) } }
		if c.both and math.abs(c.a[1]) + math.abs(c.b[1]) > 1e-3 then
			table.insert(axes, { Vector3.new(-c.a[1], c.a[2], c.a[3]), Vector3.new(-c.b[1], c.b[2], c.b[3]) })
		end
		local col = c.colour or GOLD
		local T = c.turns or 1.5
		local nArc = math.max(2, math.ceil(T * 4 - 1e-6))
		local tw = T * 2 * math.pi
		local dth = tw / nArc
		local r = (c.r or 0.05) * k
		local w = (c.size or 0.012) * k * fpK
		local function taper(t: number): number return math.clamp(math.min(t, 1 - t) / 0.2, 0, 1) ^ 0.6 end
		for ai, ab in axes do
			local d = (ab[2] - ab[1]) * k
			local dir = d.Unit
			local e1 = dir:Cross(Vector3.yAxis)
			if e1.Magnitude < 1e-3 then e1 = dir:Cross(Vector3.xAxis) end
			e1 = e1.Unit
			local e2 = dir:Cross(e1)
			local spd = math.sqrt((d.Magnitude / tw) ^ 2 + r * r) -- |dp/dθ|, the same all along a helix
			local curve = 4 / 3 * math.tan(dth / 4) * spd
			local arcLen = spd * dth
			local n = c.strands or 2
			for i = 1, n do
				local atts = {}
				for j = 0, nArc do
					local att = Instance.new("Attachment")
					att.Name = "SkinFx"; att.Parent = root
					atts[j] = att
				end
				local cl = { atts = atts, a = ab[1] * k, d = d, e1 = e1, e2 = e2, r = r, T = T, n = nArc,
					spin = if ai == 2 then -1 else 1, rate = c.spin or 1.5, phase = (i - 1) / n * 2 * math.pi }
				coilPlace(cl, clockT)
				table.insert(S_.coils, cl)
				for j = 0, nArc - 1 do
					local t0, t1 = taper(j / nArc), taper((j + 1) / nArc)
					local layers = {
						{ "halo", TEX.tracer, 3.2, 1, 1.2, 0.55, 0 },
						{ "body", TEX.tracer, 1.5, 0.15, 1, 0, 0.001 },
						{ "core", TEX.tracer, 0.7, 1, 3.5, 0, 0.002 },
					}
					if (c.pulse or 1) ~= 0 then table.insert(layers, { "bead", TEX.pulse, 2, 1, 4, 0, 0.003 }) end
					for _, L in layers do
						local b = Instance.new("Beam")
						b.Attachment0 = atts[j]; b.Attachment1 = atts[j + 1]
						b.CurveSize0 = curve; b.CurveSize1 = curve; b.Segments = 10; b.FaceCamera = true
						b.Texture = L[2]; b.Width0 = w * L[3] * t0; b.Width1 = w * L[3] * t1
						b.LightEmission = L[4]; b.LightInfluence = 0; b.Brightness = L[5]
						b.Transparency = NumberSequence.new(L[6]); b.ZOffset = L[7]
						b.Color = ColorSequence.new(coilShade(col, L[1]))
						if L[1] == "bead" then
							-- (one bead or more a quarter turn: a whole number to an arc, so they run on across the joins)
							b.TextureMode = Enum.TextureMode.Wrap; b.TextureLength = arcLen / (c.beads or 1)
							b.TextureSpeed = c.pulse or 1
						else
							b.TextureMode = Enum.TextureMode.Stretch; b.TextureLength = 1
						end
						b.Name = "SkinFx"; b.Parent = root
						table.insert(S_.coilBeams, { b = b, role = L[1], tint = c.tint })
					end
				end
			end
		end
	end
	-- the angel weapons' flames (the owner, 17 Nov: "glowing parts with cool vfx ... when you add a spray to it, it changes
	-- the color of the glow like flameish effect"): flame tongues licking up off the lit edges (spec.flame.segs: polylines
	-- in the gun frame, metres, `both` mirrors), one small emitter every 7 cm; their colour and the lit parts' (names
	-- ending "__lit") follow the equipped wrap's glow colour (skinGlow)
	local fl = sp.flame
	-- (fl.fp: the flames' rate share in first person, your own gun; 0 = none there. the angel rifle's wing flames sit
	-- close to the eye there)
	local flK = if fl and S_.fp and type(fl.fp) == "number" then fl.fp else 1
	if fl and fl.segs and flK > 0 then
		-- (round 8 in Play on a stand-in rifle: at 0.08 m and 30 a metre they read as small candle flames, and a violet
		-- wrap's barely showed on a light wall: taller, about twice as many, brighter)
		local fh = (fl.size or 0.12) * k
		local step = fl.step or 0.07
		local perPoint = (fl.rate or 60) * step * flK
		local lift = fl.lift or 1 -- (how far they rise off the edge: small flames need less, or they float above it)
		local function seg(a: Vector3, b: Vector3)
			local n = math.max(1, math.floor((b - a).Magnitude / step + 0.5))
			for i = 0, n do
				local att = Instance.new("Attachment")
				att.Name = "SkinFx"; att.Position = a:Lerp(b, i / n) * k; att.Parent = root
				local em = rigEmitter(att, { Texture = TEX.flame, FlipbookLayout = FLIP4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
					FlipbookStartRandom = true, FlipbookFramerate = NR(18, 26), LightEmission = 1, LightInfluence = 0, Brightness = 2.4,
					Size = ns(0, fh / 0.86 * H * 0.6, 0.3, fh / 0.86 * H, 1, fh / 0.86 * H * 0.7), Transparency = ns(0, 1, 0.15, 0.1, 0.7, 0.3, 1, 1),
					Lifetime = NR(0.35, 0.55), Speed = NR(0.1 * k * lift, 0.3 * k * lift), SpreadAngle = Vector2.new(10, 10),
					Acceleration = Vector3.new(0, 0.6 * k * lift, 0), Rotation = NR(-8, 8), LockedToPart = S_.fp })
				em.Rate = perPoint
				em.Enabled = true
				table.insert(S_.flames, em); table.insert(S_.idle, em)
			end
		end
		for _, sg in fl.segs do
			for i = 1, #sg - 1 do
				local a, b = Vector3.new(sg[i][1], sg[i][2], sg[i][3]), Vector3.new(sg[i + 1][1], sg[i + 1][2], sg[i + 1][3])
				seg(a, b)
				if fl.both and math.abs(a.X) + math.abs(b.X) > 1e-3 then seg(a * Vector3.new(-1, 1, 1), b * Vector3.new(-1, 1, 1)) end
			end
		end
	end
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and string.sub(d.Name, -5) == "__lit" then table.insert(S_.lit, d) end
	end
	if sp.glow and sp.glow.colour then
		local att = Instance.new("Attachment"); att.Name = "SkinFx"; att.Parent = root
		local ga = sp.glow.at -- (where the light sits, the gun frame in metres; the root by default)
		if ga then att.Position = Vector3.new(ga[1], ga[2], ga[3]) * k end
		local l = Instance.new("PointLight")
		l.Color = sp.glow.colour; l.Brightness = sp.glow.bright or 0.5; l.Range = (sp.glow.range or 1.4) * k; l.Shadows = false; l.Parent = att
		S_.light = l
	end
	skinned[model] = S_
	skinGlow(S_, true)
end
function Fx.skinOff(model: Model)
	local S_ = skinned[model]
	if not S_ then return end
	skinned[model] = nil
	local root = model.PrimaryPart
	if root then for _, c in root:GetChildren() do if c.Name == "SkinFx" then c:Destroy() end end end
end
-- the registered skinned gun whose muzzle a shot left from: the nearest within 2.5 studs. (round 12 in first person:
-- the first one within reach was often the copy hidden in your character's hand, a stud or two from the viewmodel's,
-- so your shots' bursts went off on a gun you can't see)
skinAt = function(p: Vector3): any
	local best, bd = nil, 2.5
	for m, S_ in skinned do
		if not m.Parent then skinned[m] = nil; continue end
		local mz = S_.muzzle
		local d = if mz then (mz.WorldPosition - p).Magnitude else math.huge
		if d < bd then best, bd = S_, d end
	end
	return best
end
-- a shot from a registered skinned gun: its shot bursts, its lever bursts at the lever cycle's clack, its glow pieces
-- flare for spec.pulse.t. your own in first person: none while aiming or hidden, no puff across the middle fifth
local LEVER_CLACK = 0.04 + 0.19 -- (Weapons' lever: its cycle starts 0.04 s in; Reloads' lever_cycle clacks at 0.19 s)
skinShot = function(S_: any)
	if not S_.quiet then
		local function go(list: { any }, base: number)
			for _, b in list do
				after(base + b.delay, function()
					if not b.em.Parent or S_.quiet then return end
					local cam = workspace.CurrentCamera
					if b.puff and S_.fp and cam then
						local sp = cam:WorldToViewportPoint(b.at.WorldPosition)
						local vp = cam.ViewportSize
						if math.abs(sp.X - vp.X / 2) < vp.X * 0.1 and math.abs(sp.Y - vp.Y / 2) < vp.Y * 0.1 then return end
					end
					emit(b.em, if type(b.n) == "table" then math.random(b.n[1], b.n[2]) else b.n)
				end)
			end
		end
		go(S_.shot, 0)
		go(S_.lever, LEVER_CLACK)
	end
	if #S_.pulse > 0 and not S_.pulsing then
		S_.pulsing = true
		local was = {}
		for i, p in S_.pulse do was[i] = p.Color; p.Color = p.Color:Lerp(FWHITE, 0.55) end
		local l = S_.light
		local lb = if l then l.Brightness else 0
		if l then l.Brightness = lb + 2 end
		after(S_.spec.pulse.t or 0.1, function()
			for i, p in S_.pulse do if p.Parent then p.Color = was[i] end end
			if l then l.Brightness = lb end
			S_.pulsing = false
		end)
	end
end
-- (round 4: first-person bubbles drifted by the sight while aiming, and hung in the view while the gun was hidden. the
-- game's aim narrows the view (Arsenal: baseFov / zoom), so a view under 0.95 of the widest seen lately is aiming)
local wideFov = 70
-- the angel katana's flame trail (the owner: "a bit of a trail as you move"; main, round 9: tall tongues standing up
-- over the crosshair read as a fire wall, not a swing): thin flame licks laid along the blade's path, stretched with
-- its motion (VelocityParallel), from the blade's outer half, gone in ~0.2 s, in the wrap's glow colour. your own in
-- first person smaller and dimmer and never in the middle fifth of the screen; Arsenal's smear takes the glow colour too
local FLAMEARC = emitters(8, { Texture = TEX.flame, FlipbookLayout = FLIP4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
	FlipbookStartRandom = true, FlipbookFramerate = NR(24, 30), LightEmission = 1, LightInfluence = 0,
	Orientation = Enum.ParticleOrientation.VelocityParallel, Lifetime = NR(0.15, 0.22), SpreadAngle = Vector2.new(6, 6), Drag = 6,
	Squash = ns(0, 1.2, 1, 2.4), Transparency = ns(0, 0.1, 0.5, 0.35, 1, 1) })
type BladeLast = { a: Vector3, b: Vector3, t: number }
local bladeLast: { [Model]: BladeLast } = {}
function Fx.bladeGlow(model: Model?): Color3?
	local S_ = if model then skinned[model] else nil
	return if S_ and #S_.flames > 0 then S_.glow else nil
end
function Fx.bladeFlames(model: Model?, a: Vector3, b: Vector3)
	local S_ = if model then skinned[model] else nil
	-- (a high-tier katana's own swing bits, SkinSets.FX[id].swing: Sakura's petals, Ribbon Duck's sparkles, shed along the
	-- blade's path, flung a little with it)
	local sw = if S_ then S_.spec.swing else nil
	local fl = S_ ~= nil and #S_.flames > 0 and S_.glow ~= nil
	if not model or not S_ or not (fl or sw) then return end
	local last = bladeLast[model]
	bladeLast[model] = { a = a, b = b, t = clockT }
	local dt = if last then clockT - last.t else 0
	if not last or dt <= 0 or dt > 0.1 then return end
	local kk = S_.k
	local cam = workspace.CurrentCamera
	local vp = if cam then cam.ViewportSize else Vector2.new(1, 1)
	local c = if fl then flameCS(S_.glow :: Color3) else nil
	-- (round 10 in Play: right in first person; in third person too thin and faint to read: wider, brighter, one more)
	for _, u in (if S_.fp then { 0.7, 0.95 } else { 0.55, 0.75, 0.95 }) do
		local pNow, pWas = a:Lerp(b, u), last.a:Lerp(last.b, u)
		local v = (pNow - pWas) / dt
		if v.Magnitude < 0.5 then continue end
		if S_.fp and cam then -- (first person: never across the middle fifth of the screen, where you aim)
			local sp = cam:WorldToViewportPoint(pNow)
			if math.abs(sp.X - vp.X / 2) < vp.X * 0.1 and math.abs(sp.Y - vp.Y / 2) < vp.Y * 0.1 then continue end
		end
		local at = pWas:Lerp(pNow, math.random())
		if c then
			local e = emAt(FLAMEARC, at, v)
			local w = (if S_.fp then 0.025 else 0.09) * kk
			e.Color = c; e.Size = ns(0, w * 0.7, 0.3, w, 1, w * 0.4)
			e.Speed = NR(v.Magnitude * 0.06, v.Magnitude * 0.1)
			e.Brightness = if S_.fp then 1.2 else 3
			emit(e, 1)
		end
		if sw then
			local e = emAt(if sw.kind == "petal" then TRP.petal else TRP.star, at, v)
			e.Speed = NR(v.Magnitude * 0.04, v.Magnitude * 0.09)
			if sw.kind ~= "petal" then e.Color = cs(sw.colour or Color3.fromRGB(255, 226, 150)) end
			emit(e, if S_.fp then 1 else 2)
		end
	end
end
-- your melee hit landing with a high-tier katana (Arsenal, next to Sfx.skinHit): a burst of its swing bits on them
function Fx.skinHit(model: Model?, at: Vector3)
	local S_ = if model then skinned[model] else nil
	local sw = if S_ then S_.spec.swing else nil
	if not sw then return end
	local e = emAt(if sw.kind == "petal" then TRP.petal else TRP.star, at, Vector3.yAxis)
	e.Speed = NR(1.2 * S, 3 * S)
	if sw.kind ~= "petal" then e.Color = cs(sw.colour or Color3.fromRGB(255, 226, 150)) end
	emit(e, 7)
end
-- someone else's swing: their flame skin's blade flares for 0.25 s (Arsenal's swing event; your own blade is fed frame by
-- frame from the first-person smear)
type SwingF = { m: Model, t: number }
local swingsLive: { SwingF } = {}
function Fx.swingFlames(char: Model?)
	if not char then return end
	for m, S_ in skinned do
		if (#S_.flames > 0 or S_.spec.swing) and m:IsDescendantOf(char) then table.insert(swingsLive, { m = m, t = 0 }) end
	end
end
local function swingFlameStep(dt: number)
	for i = #swingsLive, 1, -1 do
		local sw = swingsLive[i]
		sw.t += dt
		local root = sw.m.PrimaryPart
		if sw.t > 0.25 or not root or not sw.m.Parent then bladeLast[sw.m] = nil; table.remove(swingsLive, i); continue end
		local mid, tip = root:FindFirstChild("Mid") :: Attachment?, root:FindFirstChild("Muzzle") :: Attachment?
		if mid and tip then Fx.bladeFlames(sw.m, mid.WorldPosition, tip.WorldPosition) end
	end
end
local function skinStep()
	local cam = workspace.CurrentCamera
	local fov = if cam then cam.FieldOfView else 70
	wideFov = math.max(fov, wideFov - 0.02)
	local aiming = fov < wideFov * 0.95
	for m, S_ in skinned do
		if not m.Parent then skinned[m] = nil; continue end
		-- (any gun that isn't showing goes quiet: the viewmodel in third person, and in first person the copy in your
		-- character's hand, whose effects drew round your hand before round 12; your own in first person also while aiming)
		do
			local vis = S_.vis
			local hidden = vis == nil or vis.Parent == nil or vis.LocalTransparencyModifier >= 0.99 or vis.Transparency >= 0.99
			local quiet = hidden or (S_.fp and aiming)
			if quiet ~= S_.quiet then
				S_.quiet = quiet
				for _, e in S_.idle do e.Enabled = not quiet; if hidden then e:Clear() end end
				for _, cb in S_.coilBeams do cb.b.Enabled = not quiet end
			end
		end
		if (#S_.flames > 0 or #S_.lit > 0 or #S_.coilBeams > 0) and clockT - S_.glowT > 1 then S_.glowT = clockT; skinGlow(S_) end
		-- (the vines' helixes turn; nothing while the gun is quiet)
		if #S_.coils > 0 and not S_.quiet then
			for _, cl in S_.coils do coilPlace(cl, clockT) end
		end
		if #S_.after > 0 then
			local on = clockT - S_.afterT < 1.5 and not S_.quiet
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
			if B.fade then B.b.Transparency = NumberSequence.new(B.tr0 + (1 - B.tr0) * u) end
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
	domeFxStep(dt); spiralStep(dt); holeFxStep(dt); skinStep(); swingFlameStep(dt)
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
