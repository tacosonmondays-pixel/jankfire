-- IN-WORLD FINISHERS (the VFX session, 20 Nov 2026; roblox/docs/FINISHERS.md "World finishers"). The owner: "finisher
-- cutscene should only play when you get the final hit on the game winning round and otherwise it can be like a valorant
-- weapon finisher instead". A finisher skin's round-winning kill (not the match's last) plays one of these on the
-- victim's real body, in the world, about 2 s, for everyone from their own view: no camera, no screen effects, no HUD.
-- Grander than a kill effect (KillFx, every kill), much smaller than the cinematic. Built mostly from the bought VFX packs
-- (templates WF_* in ReplicatedStorage.JankfireVfx, the 100+ pack's effects by number: roblox/docs/vfx/catalogue100),
-- played through VfxEmit and tinted to each theme's quiet colours; the rest is a few client-only parts and particles.
--   FW.play(id, victim, opts?) -> boolean   id = a Finishers.LIST key; victim = the dead body (frozen where it fell).
--       opts.from = where the killer stood (the pulls and pushes go away from them); opts.quiet = do nothing (returns
--       false: others' finishers are off, so the kill effect already on the body carries on);
--       opts.preview = a stand-in (a test mannequin): not hidden for good at the end, KillFx left alone
--   FW.length(id) -> seconds;  FW.stop(victim);  FW.has(id)
-- It takes the body from the kill effect that began at death (KillFx.reset) and leaves it hidden for good, as KillFx
-- does. Past FAR studs from the camera the body just hides. The workspace attribute WorldFinisherTimeScale (0..1)
-- slows or freezes every running one (photos).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local FW = {}
local FAR = 600 -- (the camera's distance to the body: arenas run 200-400 studs across, so anyone who can see it gets it)

-- the VFX pipeline's approved sprites (roblox/assets/vfx/assets.json; the same ids KillFx and Fx use)
local TEX = {
	glow = "rbxassetid://107753175681578", -- a soft round dot
	sparkle = "rbxassetid://118739981349944", -- four points
	dust = "rbxassetid://123624708348895", -- a puff, 16 frames (4x4)
	spark = "rbxassetid://73042129135061", -- a streak
	tracer = "rbxassetid://72229869149513", -- a beam core (v runs across)
	feather = "rbxassetid://92745845385867", -- a soft white feather
	streak = "rbxassetid://127914373549121", -- a soft white streak
	flame = "rbxassetid://77597527828324", -- a white flame tongue licking up, 16 frames (4x4)
	smoke = "rbxassetid://97407536340250", -- soft smoke, 16 frames (4x4)
	petal = "rbxassetid://72396403976507", -- a sakura petal
	bubble = "rbxassetid://127426547666953", -- a soap bubble
	ring = "rbxassetid://136567724057402", -- a ring
}
task.spawn(function()
	local list = {}
	for _, id in TEX do
		local d = Instance.new("Decal")
		d.Texture = id
		table.insert(list, d)
	end
	pcall(function() game:GetService("ContentProvider"):PreloadAsync(list) end)
end)

local folder: Folder = (workspace:FindFirstChild("JankWorldFinisher") :: Folder?) or Instance.new("Folder")
folder.Name = "JankWorldFinisher"
folder.Parent = workspace

local function ns(...: number): NumberSequence
	local a = { ... }
	if #a == 1 then return NumberSequence.new(a[1]) end
	local kp = {}
	for i = 1, #a, 2 do table.insert(kp, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(kp)
end
local function cs(...: any): ColorSequence
	local a = { ... }
	if #a == 1 then return ColorSequence.new(a[1]) end
	if #a == 2 and typeof(a[1]) == "Color3" then return ColorSequence.new(a[1], a[2]) end
	local kp = {}
	for i = 1, #a, 2 do table.insert(kp, ColorSequenceKeypoint.new(a[i], a[i + 1])) end
	return ColorSequence.new(kp)
end
local function NR(a: number, b: number?): NumberRange return NumberRange.new(a, b or a) end
local function clamp01(x: number): number return math.clamp(x, 0, 1) end
local function smooth(x: number): number x = clamp01(x); return x * x * (3 - 2 * x) end
local function lerp(a: number, b: number, t: number): number return a + (b - a) * t end
local function seg(t: number, a: number, b: number): number return clamp01((t - a) / (b - a)) end
local C = Color3.fromRGB

-- ------------------------------------------------------------------ the modules it leans on (all lazily, all optional)
local mods: { [string]: any } = {}
local function mod(name: string): any
	local m = mods[name]
	if m == nil then
		local s = script.Parent:FindFirstChild(name)
		local ok, res = false, nil
		if s and s:IsA("ModuleScript") then ok, res = pcall(require, s) end
		m = if ok and type(res) == "table" then res else false
		mods[name] = m
	end
	return if m then m else nil
end
-- the settings page's "gfx.particles" (0.25..1): every burst and stream here is scaled by it
local function amount(): number
	local K = mod("KillFx")
	local v = if K and K.setting then K.setting("gfx.particles", 1) else 1
	return if type(v) == "number" then math.clamp(v, 0.25, 1) else 1
end
local function many(n: number): number return math.max(1, math.floor(n * amount() + 0.5)) end
local function scaleT(): number
	local s = workspace:GetAttribute("WorldFinisherTimeScale")
	return if type(s) == "number" then math.clamp(s, 0, 1) else 1
end
-- a recorded sting at the body (Sfx: ReplicatedStorage.JankfireSounds by name; an empty or missing one is silent)
local function sting(name: string, at: Vector3, vol: number?, pitch: number?)
	local S = mod("Sfx")
	if S and S.play then pcall(S.play, name, at, vol, pitch) end
end

-- ------------------------------------------------------------------ a run
type P = { part: BasePart, lo: number, hi: number, cf: CFrame, decals: { Decal }, want: number? }
type Run = {
	m: Model, id: string, t: number, dur: number, parts: { P }, objs: { Instance }, emitters: { ParticleEmitter },
	hl: Highlight?, y0: number, y1: number, centre: Vector3, size: Vector3, width: number, cf: CFrame, h: number,
	away: Vector3, side: Vector3, step: (Run, number, number) -> (), s: { [string]: any }, done: boolean,
	own: boolean, preview: boolean, hold: { RBXScriptConnection }, base: { [P]: CFrame },
}
local runs: { Run } = {}
local busy: { [Model]: Run } = {}

local function fade(r: Run, p: P, a: number)
	if r.own then return end -- (your own body: the camera scripts own its fade)
	p.want = a
	p.part.LocalTransparencyModifier = a
	for _, d in p.decals do d.LocalTransparencyModifier = a end
end
local function fadeAll(r: Run, a: number) for _, p in r.parts do fade(r, p, a) end end
local function part(r: Run, size: Vector3, cf: CFrame): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size; p.CFrame = cf
	p.Parent = folder
	table.insert(r.objs, p)
	return p
end
local function prop(r: Run, shape: Enum.PartType?, size: Vector3, color: Color3, mat: Enum.Material?): Part
	local p = part(r, size, r.cf)
	p.Shape = shape or Enum.PartType.Block
	p.Transparency = 0; p.Color = color; p.Material = mat or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	return p
end
local function emitter(r: Run, at: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Rate = 0
	e.LockedToPart = false
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	e.LightInfluence = 0
	for k, v in props do (e :: any)[k] = v end
	e.TimeScale = scaleT()
	e.Parent = at
	table.insert(r.emitters, e)
	return e
end
local function pour(r: Run, key: string, e: ParticleEmitter, rate: number, dt: number)
	local acc = (r.s[key] or 0) + rate * dt * amount()
	local n = math.floor(acc)
	r.s[key] = acc - n
	if n > 0 then e:Emit(n) end
end
local function highlight(r: Run, fill: Color3, outline: Color3): Highlight
	local h = Instance.new("Highlight")
	h.Adornee = r.m
	h.DepthMode = Enum.HighlightDepthMode.Occluded
	h.FillColor = fill; h.OutlineColor = outline
	h.FillTransparency = 1; h.OutlineTransparency = 1
	h.Parent = folder
	r.hl = h
	table.insert(r.objs, h)
	return h
end
-- the whole body through T (a CFrame about the world), each part from where it was when the finisher began
local function moveBody(r: Run, T: CFrame)
	if r.own then return end
	for _, p in r.parts do p.part.CFrame = T * r.base[p] end
end
-- a pack effect (a WF_* template, or any JankfireVfx name) at cf, scale k, tinted
local function pack(r: Run, name: string, cf: CFrame, k: number, tint: Color3?): boolean
	if workspace:GetAttribute("WorldFinisherPacks") == false then return false end
	local V = mod("VfxEmit")
	if not V or not V.play then return false end
	local ok, res = pcall(V.play, name, cf, { scale = k, tint = tint })
	return ok and res == true
end
-- facing the camera, upright
local function facing(pos: Vector3): CFrame
	local cam = workspace.CurrentCamera
	local e = if cam then cam.CFrame.Position else pos + Vector3.new(0, 0, 10)
	local d = (e - pos) * Vector3.new(1, 0, 1)
	if d.Magnitude < 1e-3 then d = Vector3.new(0, 0, 1) end
	return CFrame.lookAt(pos, pos + d.Unit)
end
-- facing the camera fully (a sprite plane), and a flat floor plane at y
local function toEye(pos: Vector3): CFrame
	local cam = workspace.CurrentCamera
	local e = if cam then cam.CFrame.Position else pos + Vector3.new(0, 0, 10)
	if (e - pos).Magnitude < 1e-3 then e = pos + Vector3.new(0, 0, 1) end
	return CFrame.lookAt(pos, e)
end
local function floorAt(r: Run, y: number?): CFrame
	return CFrame.new(r.centre.X, y or (r.y0 + 0.1), r.centre.Z)
end
-- a beam between two world points on a holder part (a light shaft, a constellation line)
local function beam(r: Run, a: Vector3, b: Vector3, tex: string, c: Color3, w: number): (Beam, Attachment, Attachment)
	local bp = r.s.beamHolder
	if not bp then bp = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre)); r.s.beamHolder = bp end
	local a0 = Instance.new("Attachment"); a0.Parent = bp; a0.WorldPosition = a
	local a1 = Instance.new("Attachment"); a1.Parent = bp; a1.WorldPosition = b
	local bm = Instance.new("Beam")
	bm.Attachment0 = a0; bm.Attachment1 = a1; bm.Texture = tex; bm.TextureMode = Enum.TextureMode.Stretch; bm.TextureLength = 1
	bm.FaceCamera = true; bm.LightEmission = 1; bm.LightInfluence = 0; bm.Color = ColorSequence.new(c); bm.Brightness = 2
	bm.Width0 = w; bm.Width1 = w; bm.Segments = 1
	bm.Parent = bp
	return bm, a0, a1
end

-- a ring that grows on a plane (water ripples, a portal mouth): one particle lying across `cf`'s look direction
local function ringAt(r: Run, cf: CFrame, c: Color3, r0: number, r1: number, life: number, le: number?): ParticleEmitter
	local p = part(r, Vector3.new(0.2, 0.2, 0.2), cf)
	local e = emitter(r, p, { Texture = TEX.ring, Color = cs(c), LightEmission = le or 1, Brightness = 2,
		Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Front,
		Speed = NR(0.01), SpreadAngle = Vector2.new(0, 0), Size = ns(0, r0, 1, r1), Transparency = ns(0, 0.1, 0.7, 0.45, 1, 1),
		Lifetime = NR(life), Shape = Enum.ParticleEmitterShape.Box })
	e:Emit(1)
	return e
end

local STEP: { [string]: (Run, number, number) -> () } = {}
local LEN: { [string]: number } = {}
-- the stings: { at s, Sfx name, volume, pitch? } (recordings from the game's own library; roblox/docs/SOUNDS.md)
local STING: { [string]: { { any } } } = {}

-- ------------------------------------------------------------------ ASCENSION (Seraph): a shaft of light comes down,
-- two great arcs open like wings behind the body, it rises into the light shedding feathers, a gold halo flash
LEN.ascension = 2.1
STING.ascension = { { 0, "skin_ar_seraph_fire", 0.8 }, { 1.45, "box_bell", 1.2 } }
STEP.ascension = function(r, t, dt)
	local s = r.s
	local GOLD, WHITE = C(255, 214, 120), C(255, 246, 228)
	if not s.init then
		s.init = true
		s.h = highlight(r, WHITE, C(255, 236, 190))
		local top, bot = r.y1 + 16, r.y0 - 0.1
		s.b1 = beam(r, Vector3.new(r.centre.X, top, r.centre.Z), Vector3.new(r.centre.X, bot, r.centre.Z), TEX.glow, C(255, 232, 186), 0)
		s.b2 = beam(r, Vector3.new(r.centre.X, top, r.centre.Z), Vector3.new(r.centre.X, bot, r.centre.Z), TEX.tracer, WHITE, 0)
		s.ep = part(r, Vector3.new(r.width * 0.9, r.h * 0.8, r.width * 0.9), r.cf)
		s.feathers = emitter(r, s.ep, { Texture = TEX.feather, Color = cs(WHITE), LightEmission = 0.4, LightInfluence = 0.4,
			Size = ns(0, 0.35, 1, 0.25), Transparency = ns(0, 0.1, 0.7, 0.2, 1, 1), Lifetime = NR(1.0, 1.6), Speed = NR(1, 3),
			SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -2.5, 0), Drag = 2, Rotation = NR(0, 360), RotSpeed = NR(-120, 120) })
		s.motes = emitter(r, s.ep, { Texture = TEX.glow, Color = cs(GOLD), LightEmission = 1, Brightness = 2,
			Size = ns(0, 0.22, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NR(0.6, 1.0), Speed = NR(1.5, 4),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 3, 0) })
	end
	-- the shaft: down over 0.3 s, gone over the last 0.5
	local on = smooth(t / 0.3) * (1 - smooth(seg(t, 1.6, 2.1)))
	s.b1.Width0 = r.width * 1.7 * on; s.b1.Width1 = r.width * 1.25 * on
	s.b2.Width0 = r.width * 0.28 * on; s.b2.Width1 = r.width * 0.2 * on
	s.b1.Brightness = 1.1; s.b2.Brightness = 1.4
	s.b1.Transparency = ns(0, lerp(1, 0.75, on), 1, lerp(1, 0.45, on))
	s.b2.Transparency = ns(0, lerp(1, 0.6, on), 1, lerp(1, 0.3, on))
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.15, smooth(seg(t, 0.05, 0.45)))
	h.OutlineTransparency = lerp(1, 0.4, smooth(seg(t, 0.05, 0.45)))
	if not s.sparks and t >= 0.15 then s.sparks = true; pack(r, "WF_GoldSparks", floorAt(r), 0.45, GOLD) end
	-- the wings: two arcs open behind the body, mirrored
	for i, at in { 0.45, 0.75, 1.05 } do
		if not s["w" .. i] and t >= at then
			s["w" .. i] = true
			local lift0 = 3.4 * smooth(seg(at, 0.35, 1.5))
			local c = facing(r.centre + Vector3.new(0, r.h * 0.35 + lift0, 0))
			local back = -c.LookVector * 0.8
			pack(r, "WF_Arc", (c + back + c.RightVector * r.width * 0.6) * CFrame.Angles(0, 0, math.rad(-30)), 0.8, C(255, 240, 210))
			pack(r, "WF_Arc", (c + back - c.RightVector * r.width * 0.6) * CFrame.Angles(0, math.pi, math.rad(30)), 0.8, C(255, 240, 210))
		end
	end
	-- it rises into the light and goes, feet first
	local lift = 3.4 * smooth(seg(t, 0.35, 1.5))
	moveBody(r, CFrame.new(0, lift, 0))
	local line = lerp(r.y0 - 0.2, r.y1 + 0.4, smooth(seg(t, 0.6, 1.45)))
	for _, p in r.parts do fade(r, p, clamp01((line - p.lo) / math.max(0.2, p.hi - p.lo + 0.4))) end
	s.ep.CFrame = r.cf + Vector3.new(0, lift, 0)
	if t > 0.6 and t < 1.45 then pour(r, "f", s.feathers, 16, dt); pour(r, "m", s.motes, 40, dt) end
	-- the halo flash at the top, and a last fall of feathers
	if not s.halo and t >= 1.45 then
		s.halo = true
		pack(r, "WF_GoldFlash", toEye(Vector3.new(r.centre.X, r.y1 + lift + 0.6, r.centre.Z)), 0.75, C(255, 236, 190))
		s.feathers:Emit(many(14))
	end
end

-- ------------------------------------------------------------------ HELLGATE (Infernal): the floor cracks under the
-- body, a ring of fire climbs round it, it chars and is dragged down into the floor, a burst of red-black spikes as it
-- closes
LEN.hellgate = 2.0
STING.hellgate = { { 0, "crunch", 0.8 }, { 0.15, "flame_burn", 1 }, { 1.45, "skin_ar_infernal_fire", 0.85 } }
STEP.hellgate = function(r, t, dt)
	local s = r.s
	local ORANGE, DEEP = C(255, 96, 34), C(150, 34, 12)
	if not s.init then
		s.init = true
		s.h = highlight(r, C(58, 42, 34), ORANGE)
		pack(r, "LandCrack", floorAt(r), math.clamp(r.width * 0.45, 0.6, 1.4), C(255, 170, 120))
		s.ep = part(r, Vector3.new(r.width * 1.1, 0.4, r.width * 1.1), floorAt(r))
		s.flames = emitter(r, s.ep, { Texture = TEX.flame, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
			FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = cs(C(255, 190, 90), DEEP), LightEmission = 0.7, Brightness = 2.5,
			Size = ns(0, 1.2, 0.5, 1.8, 1, 0.6), Transparency = ns(0, 0.2, 0.7, 0.3, 1, 1), Lifetime = NR(0.45, 0.7),
			Speed = NR(4, 7), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(10, 10), Acceleration = Vector3.new(0, 5, 0) })
		s.embers = emitter(r, s.ep, { Texture = TEX.glow, Color = cs(C(255, 170, 80), DEEP), LightEmission = 1, Brightness = 3,
			Size = ns(0, 0.18, 1, 0), Transparency = ns(0, 0, 1, 1), Lifetime = NR(0.7, 1.2), Speed = NR(3, 8),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0, 4, 0), Drag = 1 })
	end
	if not s.ring and t >= 0.2 then s.ring = true; pack(r, "WF_FireRing", floorAt(r, r.y0 + 0.3), 0.45, C(255, 150, 90)) end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.05, smooth(seg(t, 0.2, 0.7)))
	h.OutlineTransparency = lerp(1, 0.2, smooth(seg(t, 0.2, 0.6)))
	-- dragged down: slow, then all at once; whatever has gone under the floor is gone
	local floorY = r.y0 + 0.05
	local down = (r.h + 0.6) * (seg(t, 0.55, 1.5) ^ 2.2)
	moveBody(r, CFrame.new(0, -down, 0))
	for _, p in r.parts do fade(r, p, clamp01((floorY - (p.lo - down)) / math.max(0.2, p.hi - p.lo))) end
	if t > 0.15 and t < 1.5 then pour(r, "f", s.flames, 30, dt); pour(r, "e", s.embers, 20, dt) end
	if not s.shut and t >= 1.45 then
		s.shut = true
		pack(r, "WF_RedSpikes", toEye(Vector3.new(r.centre.X, floorY + 0.8, r.centre.Z)), 0.35, C(255, 140, 90))
		s.embers:Emit(many(24))
	end
end

-- ------------------------------------------------------------------ SPLASHDOWN (Ducky): ripples spread round the body,
-- a whirlpool opens, it spins down the drain in a stream of bubbles, a splash, and a rubber duck bobs up in its place
LEN.splashdown = 2.2
STING.splashdown = { { 0, "blub", 1 }, { 0.45, "glug", 1 }, { 1.45, "splash", 1 }, { 1.6, "squeak", 1.1 } }
STEP.splashdown = function(r, t, dt)
	local s = r.s
	local AQUA = C(210, 236, 248)
	if not s.init then
		s.init = true
		s.h = highlight(r, C(232, 244, 255), C(255, 255, 255))
		local flat = floorAt(r, r.y0 + 0.08) * CFrame.Angles(math.rad(90), 0, 0) -- (its look straight up: the ring lies flat)
		for i = 0, 2 do task.delay(i * 0.18, function() if not r.done then ringAt(r, flat, AQUA, 0.6, r.width * 1.6 + i, 0.9, 0.6) end end) end
		s.ep = part(r, Vector3.new(r.width * 1.2, 0.6, r.width * 1.2), floorAt(r))
		s.bubbles = emitter(r, s.ep, { Texture = TEX.bubble, Color = cs(C(255, 240, 248)), LightEmission = 0.35, LightInfluence = 0.3,
			Size = ns(0, 0.15, 0.8, 0.32, 1, 0.05), Transparency = ns(0, 0.4, 0.15, 0, 0.9, 0.1, 1, 1), Lifetime = NR(0.7, 1.2),
			Speed = NR(2, 5), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(25, 25), Acceleration = Vector3.new(0, 2, 0), Drag = 1 })
	end
	if not s.vortex and t >= 0.3 then s.vortex = true; pack(r, "WF_Vortex", floorAt(r, r.y0 + 0.15), 0.32, AQUA) end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.55, smooth(seg(t, 0.2, 0.6)))
	h.OutlineTransparency = lerp(1, 0.3, smooth(seg(t, 0.2, 0.6)))
	-- spinning faster, sinking into the drain
	local u = seg(t, 0.35, 1.45)
	s.ang = (s.ang or 0) + dt * lerp(2, 22, u) * (if t < 1.45 then 1 else 0)
	local down = (r.h + 0.5) * (u ^ 1.8)
	local c = r.centre
	moveBody(r, CFrame.new(c.X, -down, c.Z) * CFrame.Angles(0, s.ang, 0) * CFrame.new(-c.X, 0, -c.Z))
	local floorY = r.y0 + 0.05
	for _, p in r.parts do fade(r, p, clamp01((floorY - (p.lo - down)) / math.max(0.2, p.hi - p.lo))) end
	if t > 0.1 and t < 1.5 then pour(r, "b", s.bubbles, 26, dt) end
	-- the splash, and the duck
	if not s.duck and t >= 1.45 then
		s.duck = {}
		s.bubbles:Emit(many(18))
		ringAt(r, floorAt(r, r.y0 + 0.1) * CFrame.Angles(math.rad(90), 0, 0), C(240, 250, 255), 0.5, r.width * 2.2, 0.55, 0.8)
		local YEL = C(255, 212, 64)
		local body = prop(r, Enum.PartType.Ball, Vector3.new(2.1, 2.1, 2.1), YEL)
		local head = prop(r, Enum.PartType.Ball, Vector3.new(1.35, 1.35, 1.35), YEL)
		local beak = prop(r, Enum.PartType.Block, Vector3.new(0.68, 0.22, 0.5), C(255, 140, 40))
		local eye1 = prop(r, Enum.PartType.Ball, Vector3.new(0.21, 0.21, 0.21), C(30, 26, 24))
		local eye2 = prop(r, Enum.PartType.Ball, Vector3.new(0.21, 0.21, 0.21), C(30, 26, 24))
		s.duck = { { body, CFrame.new(0, 0, 0) }, { head, CFrame.new(0, 1.2, -0.48) }, { beak, CFrame.new(0, 1.09, -1.25) },
			{ eye1, CFrame.new(0.35, 1.4, -1.0) }, { eye2, CFrame.new(-0.35, 1.4, -1.0) } }
		s.duckFace = facing(floorAt(r).Position)
	end
	if s.duckFace then
		local k = seg(t, 1.45, 1.75)
		local up = lerp(-2, 0.9, smooth(k)) + 0.12 * math.sin(t * 9) * seg(t, 1.7, 1.9)
		local sc = if t > 1.95 then 1 - smooth(seg(t, 1.95, 2.15)) else 1
		local base = s.duckFace * CFrame.new(0, up, 0) * CFrame.Angles(0, 0, 0.12 * math.sin(t * 7))
		for _, q in s.duck do
			local p = q[1] :: Part
			p.CFrame = base * CFrame.new(q[2].Position * sc)
			p.Transparency = if sc <= 0.02 then 1 else 0
			if sc < 1 then p.Size = p.Size * 0.9 end
		end
		if not s.popped and t >= 1.95 then s.popped = true; s.bubbles:Emit(many(10)) end
	end
end

-- ------------------------------------------------------------------ HIGH NOON (Dust Drover): a gust of wind lines, a
-- dust devil turns up round the body and blows it away as sand, a tumbleweed rolls through behind
LEN.highnoon = 2.0
STING.highnoon = { { 0, "ricochet", 0.9 }, { 0.2, "slide", 0.8 } }
STEP.highnoon = function(r, t, dt)
	local s = r.s
	local SAND, DUN = C(232, 206, 160), C(206, 182, 142)
	if not s.init then
		s.init = true
		s.h = highlight(r, C(214, 190, 150), C(240, 220, 180))
		local c = facing(r.centre)
		s.wind = c.RightVector
		pack(r, "WF_WindLines", CFrame.lookAt(r.centre, r.centre + s.wind), 0.6, SAND)
		s.ep = part(r, Vector3.new(r.width * 0.9, r.h, r.width * 0.9), r.cf)
		s.sand = emitter(r, s.ep, { Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
			FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = cs(SAND), LightEmission = 0, LightInfluence = 0.6,
			Size = ns(0, 0.5, 1, 1.4), Transparency = ns(0, 0.3, 0.6, 0.45, 1, 1), Lifetime = NR(0.7, 1.1),
			Speed = NR(4, 8), SpreadAngle = Vector2.new(20, 20), Acceleration = Vector3.new(0, 1.5, 0), Drag = 1.5 })
		s.sand.EmissionDirection = Enum.NormalId.Right
		s.devil = part(r, Vector3.new(2.4, r.h + 1, 2.4), r.cf)
		s.devilE = emitter(r, s.devil, { Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
			FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = cs(DUN), LightEmission = 0, LightInfluence = 0.6,
			Size = ns(0, 0.8, 1, 2), Transparency = ns(0, 0.45, 0.7, 0.6, 1, 1), Lifetime = NR(0.6, 0.9), Speed = NR(1, 3),
			Acceleration = Vector3.new(0, 5, 0), RotSpeed = NR(-220, 220), Rotation = NR(0, 360),
			Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface })
	end
	if not s.swirl and t >= 0.2 then s.swirl = true; pack(r, "WF_Swirl", toEye(r.centre), 0.55, SAND) end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.25, smooth(seg(t, 0.15, 0.55)))
	h.OutlineTransparency = lerp(1, 0.5, smooth(seg(t, 0.15, 0.55)))
	-- blown away from the top down, the sand streaming downwind
	s.ep.CFrame = CFrame.fromMatrix(r.centre, s.wind, Vector3.yAxis) -- (its Right face along the wind)
	local line = lerp(r.y1 + 0.3, r.y0 - 0.3, smooth(seg(t, 0.4, 1.35)))
	for _, p in r.parts do fade(r, p, clamp01((p.hi - line) / math.max(0.2, p.hi - p.lo + 0.4))) end
	moveBody(r, CFrame.new(s.wind * 0.8 * smooth(seg(t, 0.4, 1.35))))
	s.devil.CFrame = r.cf * CFrame.Angles(0, t * 14, 0)
	if t > 0.25 and t < 1.4 then pour(r, "s", s.sand, 40, dt); pour(r, "d", s.devilE, 30, dt) end
	-- the tumbleweed: a loose ball of dry sticks bouncing through behind
	if not s.weed and t >= 1.0 then
		s.weed = {}
		local rng = Random.new(7)
		for _ = 1, 20 do
			local len = rng:NextNumber(1.4, 2.4)
			local p = prop(r, Enum.PartType.Cylinder, Vector3.new(len, 0.14, 0.14), C(190, 156, 104))
			local rel = CFrame.Angles(rng:NextNumber(0, 6.3), rng:NextNumber(0, 6.3), rng:NextNumber(0, 6.3)) * CFrame.new(rng:NextNumber(-0.35, 0.35), 0, 0)
			table.insert(s.weed, { p = p, rel = rel })
		end
		local back = -facing(r.centre).LookVector * 2.5
		s.weedFrom = r.centre + back - s.wind * 10
		s.weedTo = r.centre + back + s.wind * 10
	end
	if s.weed then
		local k = seg(t, 1.0, 2.0)
		local pos = s.weedFrom:Lerp(s.weedTo, k)
		local c = CFrame.new(pos.X, r.y0 + 0.9 + math.abs(math.sin(k * math.pi * 2.5)) * 0.7, pos.Z) * CFrame.fromAxisAngle(s.wind:Cross(Vector3.yAxis), k * 12)
		for _, w in s.weed do
			w.p.CFrame = c * w.rel
			w.p.Transparency = smooth(seg(k, 0.8, 1))
		end
	end
end

-- ------------------------------------------------------------------ INKFALL (Tidecrest): one black ink stroke across the
-- body; a held beat; the top half slides off along the stroke and both halves fall away into sakura petals
LEN.inkfall = 2.1
STING.inkfall = { { 0, "skin_katana_sakura_swing", 1 }, { 0.5, "skin_katana_sakura_hit", 0.9 } }
STEP.inkfall = function(r, t, dt)
	local s = r.s
	local PINK, INK = C(246, 196, 212), C(28, 26, 34)
	if not s.init then
		s.init = true
		s.h = highlight(r, C(250, 240, 238), INK)
		local c = toEye(r.centre)
		s.cut = c * CFrame.Angles(0, 0, math.rad(-35)) -- (the stroke: down-left to up-right across the body)
		pack(r, "WF_InkSlash", s.cut, 0.42, nil)
		pack(r, "WF_InkBlots", c, 0.05, nil)
		-- which side of the stroke each part is on (the plane through the middle, across the stroke)
		local n = s.cut.UpVector
		s.top = {}
		for _, p in r.parts do s.top[p] = (r.base[p].Position - r.centre):Dot(n) > 0 end
		s.dir = s.cut.RightVector
		s.ep = part(r, Vector3.new(r.width * 0.8, r.h * 0.8, r.width * 0.8), r.cf)
		s.petals = emitter(r, s.ep, { Texture = TEX.petal, Color = cs(PINK, C(255, 226, 232)), LightEmission = 0.2, LightInfluence = 0.5,
			Size = ns(0, 0.22, 1, 0.16), Transparency = ns(0, 0.05, 0.8, 0.2, 1, 1), Lifetime = NR(1.0, 1.6), Speed = NR(1.5, 4),
			SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0.6, -1.2, 0), Drag = 1.6, Rotation = NR(0, 360), RotSpeed = NR(-200, 200) })
	end
	local h = s.h :: Highlight
	-- a pale beat (the cut has landed and nobody knows yet), then the halves part and go to petals
	h.FillTransparency = lerp(1, 0.35, smooth(seg(t, 0.1, 0.35)))
	h.OutlineTransparency = lerp(1, 0.1, smooth(seg(t, 0.05, 0.2)))
	local slide = 1.3 * smooth(seg(t, 0.5, 1.1))
	local drop = 0.6 * smooth(seg(t, 0.6, 1.3))
	if not r.own then
		for _, p in r.parts do
			local b = r.base[p]
			if s.top[p] then p.part.CFrame = b + s.dir * slide + Vector3.new(0, -drop * 0.3, 0)
			else p.part.CFrame = b + Vector3.new(0, -drop, 0) end
		end
	end
	local k = smooth(seg(t, 0.75, 1.55))
	fadeAll(r, k)
	if t > 0.6 and t < 1.6 then pour(r, "p", s.petals, 55, dt) end
	if not s.burst and t >= 0.5 then s.burst = true; s.petals:Emit(many(20)) end
end

-- ------------------------------------------------------------------ WARP OUT (Star Drover): a teal hard-light ring opens
-- behind the body, the body is yanked back into it past streaking stars, and the ring snaps shut in a crackle
LEN.warpout = 1.9
STING.warpout = { { 0, "card_tp", 1 }, { 0.25, "laser_whine", 1.1 }, { 1.05, "skin_revolver_star_fire", 0.9 } }
STEP.warpout = function(r, t, dt)
	local s = r.s
	local TEAL, LILAC = C(69, 230, 214), C(201, 164, 216)
	if not s.init then
		s.init = true
		s.h = highlight(r, C(170, 250, 240), TEAL)
		s.to = r.centre + r.away * 6 + Vector3.new(0, 0.6, 0)
		s.mouth = ringAt(r, CFrame.lookAt(s.to, s.to - r.away), TEAL, 0.6, 5.5, 1.15, 1)
		s.ep = part(r, Vector3.new(r.width * 1.6, r.h * 1.2, 0.5), CFrame.lookAt(r.centre - r.away * 2, s.to))
		s.stars = emitter(r, s.ep, { Texture = TEX.streak, Color = cs(C(230, 255, 252), TEAL), LightEmission = 1, Brightness = 2,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Size = ns(0, 0.12, 1, 0.04), Transparency = ns(0, 0.1, 1, 1),
			Lifetime = NR(0.25, 0.4), Speed = NR(30, 45), EmissionDirection = Enum.NormalId.Front, SpreadAngle = Vector2.new(3, 3) })
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.3, smooth(seg(t, 0.1, 0.4)))
	h.OutlineTransparency = lerp(1, 0.1, smooth(seg(t, 0.1, 0.3)))
	-- pulled in: a lean back, then all at once, each part drawn towards the ring's middle and gone at it
	local k = seg(t, 0.3, 1.05) ^ 2.4
	if not r.own then
		for _, p in r.parts do
			local b = r.base[p]
			local pos = b.Position:Lerp(s.to, k)
			p.part.CFrame = (b - b.Position) + pos
		end
	end
	fadeAll(r, smooth(seg(t, 0.75, 1.05)))
	if t > 0.2 and t < 1.05 then pour(r, "s", s.stars, 70, dt) end
	if not s.shut and t >= 1.05 then
		s.shut = true
		pack(r, "WF_Bolt", toEye(s.to), 0.6, nil)
		pack(r, "WF_Star", toEye(s.to), 0.6, C(220, 255, 250))
	end
end

-- ------------------------------------------------------------------ LANTERN LIGHT (Pumpkin Patch): a pumpkin's ribs rise
-- out of the floor round the body and close over it, its carved face lights from inside, then it puffs away into smoke
LEN.lanternlight = 2.2
STING.lanternlight = { { 0, "rope_creak", 0.9 }, { 0.9, "skin_smg_pumpkin_fire", 0.7 }, { 1.6, "skin_frag_lantern_blast", 0.8 } }
STEP.lanternlight = function(r, t, dt)
	local s = r.s
	local PUMP, GLOW = C(222, 120, 40), C(255, 176, 80)
	local R = math.max(1.7, r.width * 0.75)
	local H = math.max(3.2, r.h * 0.95)
	if not s.init then
		s.init = true
		s.face = facing(floorAt(r).Position)
		s.ribs = {}
		for i = 1, 8 do
			local p = prop(r, Enum.PartType.Block, Vector3.new(1, 1, 1), PUMP)
			local m = Instance.new("SpecialMesh"); m.MeshType = Enum.MeshType.Sphere; m.Parent = p
			p.Size = Vector3.new(R * 0.9, H, R * 0.9)
			table.insert(s.ribs, { p = p, a = (i - 0.5) / 8 * math.pi * 2 })
		end
		s.stem = prop(r, Enum.PartType.Cylinder, Vector3.new(0.8, 0.45, 0.45), C(96, 84, 48))
		-- the carved face: two eyes and a grin, lit from inside (on the side facing whoever's watching)
		s.carve = {}
		for _, q in { { -0.42, 0.25, 0.42, 0.42 }, { 0.42, 0.25, 0.42, 0.42 }, { 0, -0.35, 1.1, 0.3 } } do
			local p = prop(r, Enum.PartType.Block, Vector3.new(q[3], q[4], 0.1), GLOW, Enum.Material.Neon)
			p.Transparency = 1
			table.insert(s.carve, { p = p, x = q[1], y = q[2] })
		end
		s.light = Instance.new("PointLight"); s.light.Color = GLOW; s.light.Range = 14; s.light.Brightness = 0; s.light.Shadows = false
		s.light.Parent = s.stem
	end
	-- the ribs rise (0-0.5), lean in and close (0.4-0.9); the body is hidden as they meet
	local rise = smooth(seg(t, 0, 0.5))
	local close = smooth(seg(t, 0.4, 0.9))
	local gone = smooth(seg(t, 1.65, 2.1))
	local cy = r.y0 + H * 0.5 * rise - H * 0.55 * (1 - rise)
	for _, q in s.ribs do
		local out = lerp(R * 1.25, R * 0.55, close)
		local lean = lerp(0.35, 0, close)
		local dir = Vector3.new(math.cos(q.a), 0, math.sin(q.a))
		local pos = Vector3.new(r.centre.X, cy, r.centre.Z) + dir * out
		local cf = CFrame.lookAt(pos, pos + dir) * CFrame.Angles(-lean, 0, 0)
		q.p.CFrame = cf
		q.p.Size = Vector3.new(R * 0.9, H, R * 0.9) * (1 - gone * 0.9)
		q.p.Transparency = gone
	end
	s.stem.CFrame = CFrame.new(r.centre.X, cy + H * 0.5 * close + 0.15, r.centre.Z) * CFrame.Angles(0, 0, math.pi / 2)
	s.stem.Transparency = if close > 0.6 then gone else 1
	fadeAll(r, smooth(seg(t, 0.55, 0.85)))
	-- the face lights and flickers
	local lit = smooth(seg(t, 0.9, 1.15)) * (1 - gone)
	for _, q in s.carve do
		local fc = s.face + Vector3.new(0, cy - r.y0 - 0.1, 0)
		q.p.CFrame = fc * CFrame.new(q.x * R * 0.6, q.y * H * 0.3 + H * 0.05, -R * 0.62)
		q.p.Transparency = 1 - lit * (0.75 + 0.25 * math.sin(t * 31))
	end
	s.light.Brightness = 3 * lit
	if not s.puff and t >= 1.65 then
		s.puff = true
		pack(r, "WF_Puff", toEye(Vector3.new(r.centre.X, r.y0 + H * 0.5, r.centre.Z)), 0.3, C(196, 188, 206))
		pack(r, "WF_GoldSparks", floorAt(r), 0.35, C(255, 170, 90))
	end
end

-- ------------------------------------------------------------------ STARCHART (Triangulum): the body goes night blue,
-- stars light on its joints one by one, lines draw between them, the body fades and the constellation rises into the sky
LEN.starchart = 2.1
STING.starchart = { { 0.4, "ting", 0.6, 1.3 }, { 0.58, "ting", 0.6, 1.45 }, { 0.76, "ting", 0.6, 1.6 }, { 1.4, "skin_sniper_triangulum_cycle", 1 } }
local JOINTS = {
	{ "Head" }, { "UpperTorso", "Torso" }, { "LeftHand", "Left Arm" }, { "RightHand", "Right Arm" },
	{ "LeftFoot", "Left Leg" }, { "RightFoot", "Right Leg" },
}
local LINKS = { { 1, 2 }, { 2, 3 }, { 2, 4 }, { 2, 5 }, { 2, 6 } }
STEP.starchart = function(r, t, dt)
	local s = r.s
	local STAR, NIGHT = C(255, 231, 166), C(36, 44, 92)
	if not s.init then
		s.init = true
		s.h = highlight(r, NIGHT, C(255, 236, 196))
		-- the joints (R15 or R6 names; an odd body falls back to points round its middle)
		s.pts = {}
		for i, names in JOINTS do
			local found: BasePart? = nil
			for _, n in names do
				local p = r.m:FindFirstChild(n, true)
				if p and p:IsA("BasePart") then found = p; break end
			end
			local pos = if found then found.Position else r.centre + Vector3.new(math.cos(i) * r.width * 0.4, (i == 1 and 1 or -0.3) * r.h * 0.4, math.sin(i) * r.width * 0.4)
			if found and (names[1] == "LeftFoot" or names[1] == "RightFoot") and found.Name ~= names[1] then pos -= Vector3.new(0, found.Size.Y * 0.4, 0) end
			if found and (names[1] == "LeftHand" or names[1] == "RightHand") and found.Name ~= names[1] then pos -= found.CFrame.UpVector * found.Size.Y * 0.4 end
			s.pts[i] = pos
		end
		s.ep = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new())
		s.lines = {}
		s.lit = {}
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.1, smooth(seg(t, 0, 0.3))) + 0.9 * smooth(seg(t, 0.35, 0.8))
	h.OutlineTransparency = lerp(1, 0.3, smooth(seg(t, 0, 0.3))) + 0.7 * smooth(seg(t, 0.6, 1.0))
	-- the stars light, 0.1 s apart from the head down; each line draws from its first star to the next
	local rise = 2.4 * smooth(seg(t, 1.35, 2.05))
	s.ep.CFrame = CFrame.new(0, rise, 0)
	for i, pos in s.pts do
		if not s.lit[i] and t >= 0.4 + (i - 1) * 0.09 then
			s.lit[i] = true
			local a = Instance.new("Attachment"); a.Parent = s.ep; a.Position = pos -- (s.ep sits at the origin, risen)
			local big = if i == 1 then 1.3 else 1
			emitter(r, a, { Texture = TEX.sparkle, Color = cs(STAR), LightEmission = 1, Brightness = 3,
				Size = ns(0, 0, 0.12, 0.9 * big, 0.3, 0.55 * big, 1, 0.5 * big), Transparency = ns(0, 0, 0.85, 0, 1, 1),
				Lifetime = NR(1.9 - i * 0.1), Speed = NR(0), Rotation = NR(0, 30), RotSpeed = NR(-15, 15), LockedToPart = true }):Emit(1)
			emitter(r, a, { Texture = TEX.glow, Color = cs(STAR), LightEmission = 1, Brightness = 1.5,
				Size = ns(0, 0, 0.1, 0.8 * big, 1, 0.5 * big), Transparency = ns(0, 0.3, 0.85, 0.4, 1, 1), Lifetime = NR(1.9 - i * 0.1),
				Speed = NR(0), LockedToPart = true }):Emit(1)
			if i == 1 then pack(r, "WF_Star", toEye(pos), 0.5, STAR) end
		end
	end
	for j, l in LINKS do
		local a, b = s.pts[l[1]], s.pts[l[2]]
		local k = smooth(seg(t, 0.5 + j * 0.09, 0.72 + j * 0.09))
		if k > 0 then
			local L = s.lines[j]
			if not L then
				local bm, a0, a1 = beam(r, a, a, TEX.tracer, STAR, 0.08)
				L = { bm = bm, a0 = a0, a1 = a1 }
				s.lines[j] = L
			end
			local lift = Vector3.new(0, rise, 0)
			L.a0.WorldPosition = a + lift
			L.a1.WorldPosition = a:Lerp(b, k) + lift
			L.bm.Transparency = NumberSequence.new(lerp(0.15, 1, smooth(seg(t, 1.7, 2.05))))
		end
	end
	fadeAll(r, smooth(seg(t, 0.4, 0.85)))
	if not s.fin and t >= 1.4 then s.fin = true; pack(r, "WF_SparkRing", toEye(s.pts[2] + Vector3.new(0, 1, 0)), 0.5, STAR) end
end

-- ------------------------------------------------------------------ the loop
local function finish(r: Run)
	if r.done then return end
	r.done = true
	busy[r.m] = nil
	fadeAll(r, 1)
	if r.preview and r.base then for p, cf in r.base do if p.part.Parent then p.part.CFrame = cf end end end
	for _, e in r.emitters do e.Rate = 0 end
	local objs = r.objs
	task.delay(1.6, function() for _, o in objs do o:Destroy() end end) -- (the last particles finish their lives)
	if r.own or r.preview then return end
	-- the body stays hidden until it's gone: anything put on it later hides too
	table.insert(r.hold, r.m.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).LocalTransparencyModifier = 1 end
	end))
end

function FW.has(id: string): boolean return STEP[id] ~= nil end
function FW.length(id: string): number return LEN[id] or 0 end
function FW.ids(): { string }
	local t = {}
	for id in STEP do table.insert(t, id) end
	table.sort(t)
	return t
end

function FW.play(id: string, victim: Model, opts: { from: Vector3?, quiet: boolean?, preview: boolean? }?): boolean
	local step = STEP[id]
	if not step or not victim or not victim.Parent then return false end
	local o = opts or {}
	if o.quiet then return false end -- (others' finishers turned off: the kill effect already on the body carries on)
	local preview = o.preview == true
	-- take the body from the kill effect that began at its death (it puts the body back as it was)
	if not preview then
		local K = mod("KillFx")
		if K and K.reset then pcall(K.reset, victim) end
	end
	local old = busy[victim]
	if old then finish(old) end
	local cf, size = victim:GetBoundingBox()
	local r: Run = {
		m = victim, id = id, t = 0, dur = LEN[id], parts = {}, objs = {}, emitters = {}, hl = nil,
		y0 = math.huge, y1 = -math.huge, centre = cf.Position, size = size, width = math.clamp(math.max(size.X, size.Z), 1.4, 4),
		cf = CFrame.new(cf.Position), h = 0, away = Vector3.new(0, 0, 1), side = Vector3.new(1, 0, 0), step = step, s = {},
		done = false, own = (victim == me.Character) and not preview, preview = preview, hold = {}, base = {},
	}
	for _, d in victim:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" and d.Transparency < 0.99 then
			local pcf, sz = d.CFrame, d.Size * 0.5
			local ext = math.abs(pcf.RightVector.Y) * sz.X + math.abs(pcf.UpVector.Y) * sz.Y + math.abs(pcf.LookVector.Y) * sz.Z
			local p: P = { part = d, lo = pcf.Position.Y - ext, hi = pcf.Position.Y + ext, cf = pcf, decals = {} }
			for _, c in d:GetChildren() do if c:IsA("Decal") then table.insert(p.decals, c) end end
			r.y0 = math.min(r.y0, p.lo); r.y1 = math.max(r.y1, p.hi)
			r.base[p] = pcf
			table.insert(r.parts, p)
		end
	end
	if #r.parts == 0 then return false end
	r.h = math.max(1, r.y1 - r.y0)
	r.centre = Vector3.new(cf.Position.X, (r.y0 + r.y1) / 2, cf.Position.Z)
	r.cf = CFrame.new(r.centre)
	-- away from the killer (or from the camera)
	local from = o.from or (workspace.CurrentCamera and workspace.CurrentCamera.CFrame.Position) or (r.centre - Vector3.new(0, 0, 10))
	local a = (r.centre - from) * Vector3.new(1, 0, 1)
	r.away = if a.Magnitude > 1e-3 then a.Unit else Vector3.new(0, 0, 1)
	r.side = r.away:Cross(Vector3.yAxis)
	busy[victim] = r
	if not r.own then
		for _, p in r.parts do
			table.insert(r.hold, p.part:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(function()
				local w = p.want
				if w and p.part.LocalTransparencyModifier ~= w then p.part.LocalTransparencyModifier = w end
			end))
		end
		local c2: RBXScriptConnection? = nil
		c2 = victim.AncestryChanged:Connect(function(_, parent)
			if parent then return end
			for _, x in r.hold do x:Disconnect() end
			if c2 then c2:Disconnect() end
		end)
	end
	local cam = workspace.CurrentCamera
	if cam and (cam.CFrame.Position - r.centre).Magnitude > FAR and not preview then
		finish(r)
		return true
	end
	for _, q in STING[id] or {} do
		task.delay(q[1], function() if not r.done or r.t < r.dur then sting(q[2], r.centre, q[3], q[4]) end end)
	end
	table.insert(runs, r)
	return true
end

function FW.stop(victim: Model)
	local r = busy[victim]
	if r then finish(r) end
end

local lastScale = 1
RunService.RenderStepped:Connect(function(dt: number)
	if #runs == 0 then return end
	local sc = scaleT()
	local d = dt * sc
	for i = #runs, 1, -1 do
		local r = runs[i]
		if sc ~= lastScale then for _, e in r.emitters do e.TimeScale = sc end end
		if r.done or not r.m.Parent then
			table.remove(runs, i)
			if not r.done then finish(r) end
			continue
		end
		r.t += d
		local ok, err = pcall(r.step, r, r.t, d)
		if not ok then warn("[jankfire] world finisher " .. r.id .. ": " .. tostring(err)) end
		if not ok or r.t >= r.dur then
			table.remove(runs, i)
			finish(r)
		end
	end
	lastScale = sc
end)

FW.TEX = TEX
return FW
