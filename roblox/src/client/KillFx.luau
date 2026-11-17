--!strict
-- KILL EFFECTS, drawn on every client (Shared.Flair "kill" items; doc FLAIR.md). The server picks the effect (the real
-- killer's, FlairServer), freezes the body where it fell (anchored, no collisions) and tells everyone (FlairKill); this
-- draws it. The body's own parts fade with LocalTransparencyModifier (nothing replicates), one Highlight tints them,
-- and a few particles and client-only parts do the rest; at the end the body is hidden for good (the respawn makes a
-- new one). Rules (the owner's brief, Rivals research): 1.5 s at most, the size of a body (nothing reaches more than
-- about 4 studs out), no tall pillars, no floor marks, no screen effects, quiet colours. A body further than FAR studs
-- from the camera just hides.
-- K.play(model, id, opts?) -> run handle (opts.preview: a client-only mannequin, the equip screen's)
-- K.scale(): the workspace attribute FlairTimeScale (0 freezes every running effect for photos; default 1)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any
local me = Players.LocalPlayer

local K = {}
local FAR = 320

-- the VFX pipeline's approved sprites (roblox/assets/vfx/assets.json): no new uploads for these effects
local TEX = {
	glow = "rbxassetid://107753175681578", -- a soft round dot
	sparkle = "rbxassetid://118739981349944", -- four points
	chips = "rbxassetid://81145557543325", -- 4 flakes (2x2)
	dust = "rbxassetid://123624708348895", -- a puff, 16 frames (4x4)
	lumps = "rbxassetid://82728391412819", -- 16 dense crisp lumps (4x4)
	spark = "rbxassetid://73042129135061", -- a streak
	ring = "rbxassetid://136567724057402", -- a ring
	tracer = "rbxassetid://72229869149513", -- a beam core (v runs across)
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

local folder: Folder = (workspace:FindFirstChild("JankKillFx") :: Folder?) or Instance.new("Folder")
folder.Name = "JankKillFx"
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
	local kp = {}
	for i = 1, #a, 2 do table.insert(kp, ColorSequenceKeypoint.new(a[i], a[i + 1])) end
	return ColorSequence.new(kp)
end
local function clamp01(x: number): number return math.clamp(x, 0, 1) end
local function smooth(x: number): number x = clamp01(x); return x * x * (3 - 2 * x) end
local function lerp(a: number, b: number, t: number): number return a + (b - a) * t end

function K.scale(): number
	local s = workspace:GetAttribute("FlairTimeScale")
	return if type(s) == "number" then math.clamp(s, 0, 1) else 1
end

-- ------------------------------------------------------------------ a run
type P = { part: BasePart, lo: number, hi: number, cf: CFrame, decals: { Decal }, want: number? }
type Run = {
	m: Model, id: string, t: number, dur: number, parts: { P }, objs: { Instance }, emitters: { ParticleEmitter },
	hl: Highlight?, y0: number, y1: number, centre: Vector3, size: Vector3, width: number, cf: CFrame,
	step: (Run, number, number) -> (), s: { [string]: any }, done: boolean, own: boolean, preview: boolean,
	hold: { RBXScriptConnection },
}
local runs: { Run } = {}
local busy: { [Model]: Run } = {}

local function fade(r: Run, p: P, a: number)
	if r.own then return end -- (your own body: the camera scripts own its fade)
	p.want = a -- (held: another script showing a part again mid-effect or after, e.g. a dead fighter's gun, is undone)
	p.part.LocalTransparencyModifier = a
	for _, d in p.decals do d.LocalTransparencyModifier = a end
end
local function fadeAll(r: Run, a: number) for _, p in r.parts do fade(r, p, a) end end
-- a sweep up (dir 1) or down (dir -1) through the body: each part goes as the line crosses it (soft over `soft` studs)
local function sweep(r: Run, line: number, dir: number, soft: number)
	for _, p in r.parts do
		local a
		if dir > 0 then a = (line - p.lo) / math.max(0.2, p.hi - p.lo + soft)
		else a = (p.hi - line) / math.max(0.2, p.hi - p.lo + soft) end
		fade(r, p, clamp01(a))
	end
end

local function part(r: Run, size: Vector3, cf: CFrame): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = size; p.CFrame = cf
	p.Parent = folder
	table.insert(r.objs, p)
	return p
end
local function emitter(r: Run, at: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Rate = 0
	e.LockedToPart = false
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	for k, v in props do (e :: any)[k] = v end
	e.TimeScale = K.scale()
	e.Parent = at
	table.insert(r.emitters, e)
	return e
end
-- emit at a rate per second through the frames (an accumulator per emitter)
local function pour(r: Run, key: string, e: ParticleEmitter, rate: number, dt: number)
	local acc = (r.s[key] or 0) + rate * dt
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

-- ------------------------------------------------------------------ the effects: step(run, t (s since start), dt)
local STEP: { [string]: (Run, number, number) -> () } = {}

-- DISSOLVE (free): the body washes pale, then comes apart from the feet up into fine motes that drift up and go
STEP.dissolve = function(r, t, dt)
	local s = r.s
	if not s.e then
		local h = highlight(r, Color3.fromRGB(226, 232, 240), Color3.fromRGB(255, 255, 255))
		s.h = h
		s.ep = part(r, Vector3.new(r.width, 0.35, r.width * 0.6), r.cf)
		s.e = emitter(r, s.ep, {
			Texture = TEX.glow, Color = cs(0, Color3.fromRGB(240, 244, 250), 1, Color3.fromRGB(190, 206, 228)),
			LightEmission = 0.55, LightInfluence = 0.15, Size = ns(0, 0.15, 0.5, 0.12, 1, 0),
			Transparency = ns(0, 0.05, 0.6, 0.35, 1, 1), Lifetime = NumberRange.new(0.55, 0.95), Speed = NumberRange.new(0.5, 1.8),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0, 3.2, 0), Drag = 1.6,
		})
		s.g = emitter(r, s.ep, {
			Texture = TEX.sparkle, Color = cs(Color3.fromRGB(235, 242, 255)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.3, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NumberRange.new(0.35, 0.6),
			Speed = NumberRange.new(0.4, 1.2), Rotation = NumberRange.new(0, 90), Acceleration = Vector3.new(0, 2, 0),
		})
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.42, smooth(t / 0.18)) + 0.58 * smooth((t - 0.95) / 0.3)
	h.OutlineTransparency = lerp(1, 0.72, smooth(t / 0.18)) + 0.28 * smooth((t - 0.95) / 0.3)
	local k = smooth((t - 0.12) / 1.0)
	local line = lerp(r.y0 - 0.2, r.y1 + 0.3, k)
	sweep(r, line, 1, 0.35)
	if t > 0.1 and t < 1.15 then
		s.ep.CFrame = CFrame.new(r.centre.X, line, r.centre.Z) * r.cf.Rotation
		pour(r, "a", s.e, 120, dt)
		pour(r, "b", s.g, 12, dt)
	end
end

-- SHATTER (free): the body glazes like ice for a beat, then breaks into glass shards that fly out and fall, with glints
STEP.shatter = function(r, t, dt)
	local s = r.s
	local BREAK = 0.14
	if not s.h then
		s.h = highlight(r, Color3.fromRGB(214, 230, 242), Color3.fromRGB(240, 248, 255))
	end
	if t < BREAK then
		s.h.FillTransparency = lerp(1, 0.12, smooth(t / BREAK))
		s.h.OutlineTransparency = lerp(1, 0.35, smooth(t / BREAK))
		return
	end
	if not s.shards then
		fadeAll(r, 1)
		s.h.FillTransparency = 1; s.h.OutlineTransparency = 1
		-- two wedges per body part (the biggest 14 parts), flying out from the middle of the body
		local list = table.clone(r.parts)
		table.sort(list, function(a, b) return a.part.Size.Magnitude > b.part.Size.Magnitude end)
		s.shards = {}
		local rng = Random.new()
		for i = 1, math.min(14, #list) do
			local p = list[i]
			local sz = p.part.Size
			for j = 1, 2 do
				local w = Instance.new("WedgePart")
				w.Anchored = true; w.CanCollide = false; w.CanQuery = false; w.CanTouch = false; w.CastShadow = false
				w.Material = Enum.Material.Ice; w.Color = Color3.fromRGB(206, 230, 246); w.Transparency = 0.22; w.Reflectance = 0.12
				w.Size = Vector3.new(math.clamp(sz.X * 0.6, 0.12, 1.1), math.clamp(sz.Y * 0.55, 0.12, 1.1), math.clamp(sz.Z * 0.6, 0.12, 1.1))
				local off = Vector3.new(rng:NextNumber(-0.25, 0.25) * sz.X, (j - 1.5) * 0.5 * sz.Y, rng:NextNumber(-0.25, 0.25) * sz.Z)
				local cf = p.part.CFrame * CFrame.new(off) * CFrame.Angles(rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28), 0)
				w.CFrame = cf
				w.Parent = folder
				table.insert(r.objs, w)
				local out = cf.Position - r.centre
				out = Vector3.new(out.X, 0, out.Z)
				out = if out.Magnitude > 1e-3 then out.Unit else Vector3.new(rng:NextNumber(-1, 1), 0, rng:NextNumber(-1, 1)).Unit
				table.insert(s.shards, { w = w, cf = cf, v = out * rng:NextNumber(5, 10) + Vector3.new(0, rng:NextNumber(3, 8), 0),
					spin = Vector3.new(rng:NextNumber(-9, 9), rng:NextNumber(-9, 9), rng:NextNumber(-9, 9)) })
			end
		end
		local ep = part(r, r.size * Vector3.new(0.7, 0.8, 0.7), r.cf)
		emitter(r, ep, {
			Texture = TEX.sparkle, Color = cs(Color3.fromRGB(236, 246, 255)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.4, 1, 0), Transparency = ns(0, 0, 1, 1), Lifetime = NumberRange.new(0.25, 0.5),
			Speed = NumberRange.new(3, 8), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 90),
		}):Emit(24)
		emitter(r, ep, {
			Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			FlipbookFramerate = NumberRange.new(16 / 0.6), Color = cs(Color3.fromRGB(222, 232, 242)), LightInfluence = 0.6, LightEmission = 0.1,
			Size = ns(0, 0.7, 1, 1.3), Transparency = ns(0, 0.55, 1, 1), Lifetime = NumberRange.new(0.6),
			Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 360),
		}):Emit(5)
	end
	local g = Vector3.new(0, -52, 0)
	local fadeK = smooth((t - 0.55) / 0.4)
	for _, sh in s.shards do
		sh.v += g * dt
		sh.cf = (sh.cf + sh.v * dt) * CFrame.Angles(sh.spin.X * dt, sh.spin.Y * dt, sh.spin.Z * dt)
		sh.w.CFrame = sh.cf
		sh.w.Transparency = lerp(0.22, 1, fadeK)
	end
end

-- EMBER (rare): the body chars dark with a glowing edge, then burns away from the head down into embers and ash
STEP.ember = function(r, t, dt)
	local s = r.s
	if not s.h then
		s.h = highlight(r, Color3.fromRGB(28, 22, 20), Color3.fromRGB(255, 128, 48))
		s.ep = part(r, Vector3.new(r.width, 0.35, r.width * 0.6), r.cf)
		s.em = emitter(r, s.ep, {
			Texture = TEX.glow, Color = cs(0, Color3.fromRGB(255, 196, 120), 0.4, Color3.fromRGB(255, 120, 40), 1, Color3.fromRGB(140, 40, 20)),
			LightEmission = 1, LightInfluence = 0, Size = ns(0, 0.13, 0.7, 0.1, 1, 0), Transparency = ns(0, 0, 0.7, 0.2, 1, 1),
			Lifetime = NumberRange.new(0.6, 1.1), Speed = NumberRange.new(0.8, 2.6), EmissionDirection = Enum.NormalId.Top,
			SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 4.5, 0), Drag = 0.9,
		})
		s.ash = emitter(r, s.ep, {
			Texture = TEX.chips, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.Random,
			Color = cs(0, Color3.fromRGB(70, 66, 62), 1, Color3.fromRGB(44, 42, 40)), LightInfluence = 1, LightEmission = 0,
			Size = ns(0, 0.18, 1, 0.13), Transparency = ns(0, 0.05, 0.7, 0.3, 1, 1), Lifetime = NumberRange.new(0.7, 1.1),
			Speed = NumberRange.new(0.3, 1.2), SpreadAngle = Vector2.new(70, 70), Acceleration = Vector3.new(0, -5, 0), Drag = 2,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-220, 220),
		})
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.08, smooth(t / 0.3)) + 0.92 * smooth((t - 1.1) / 0.3)
	h.OutlineTransparency = lerp(1, 0.25, smooth(t / 0.25)) + 0.75 * smooth((t - 0.8) / 0.5)
	local k = smooth((t - 0.28) / 1.0)
	local line = lerp(r.y1 + 0.3, r.y0 - 0.2, k)
	sweep(r, line, -1, 0.3)
	if t > 0.25 and t < 1.3 then
		s.ep.CFrame = CFrame.new(r.centre.X, line, r.centre.Z) * r.cf.Rotation
		pour(r, "a", s.em, 70, dt)
		pour(r, "b", s.ash, 45, dt)
	end
end

-- INK (epic): the body floods solid black, then bursts into heavy ink blots and droplets that fall
STEP.ink = function(r, t, dt)
	local s = r.s
	local BURST = 0.34
	if not s.h then s.h = highlight(r, Color3.fromRGB(12, 12, 18), Color3.fromRGB(12, 12, 18)) end
	if t < BURST then
		s.h.FillTransparency = lerp(1, 0, smooth(t / 0.26))
		return
	end
	if not s.burst then
		s.burst = true
		fadeAll(r, 1)
		s.h.FillTransparency = 1
		local ep = part(r, r.size * Vector3.new(0.6, 0.75, 0.6), r.cf)
		emitter(r, ep, {
			Texture = TEX.lumps, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.Random,
			Color = cs(Color3.fromRGB(14, 14, 20)), LightInfluence = 0.25, LightEmission = 0,
			Size = ns(0, 0.3, 0.25, 0.36, 1, 0.08), Transparency = ns(0, 0, 0.75, 0.05, 1, 1), Lifetime = NumberRange.new(0.45, 0.7),
			Speed = NumberRange.new(6, 13), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -58, 0), Drag = 1.4,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120),
		}):Emit(20)
		-- (torn flakes between the blots: a splash, not a handful of balls)
		emitter(r, ep, {
			Texture = TEX.chips, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.Random,
			Color = cs(Color3.fromRGB(12, 12, 18)), LightInfluence = 0.2, LightEmission = 0,
			Size = ns(0, 0.24, 1, 0.1), Transparency = ns(0, 0, 0.8, 0.1, 1, 1), Lifetime = NumberRange.new(0.4, 0.65),
			Speed = NumberRange.new(8, 15), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -62, 0), Drag = 1,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-300, 300),
		}):Emit(28)
		emitter(r, ep, {
			Texture = TEX.glow, Color = cs(0, Color3.fromRGB(10, 10, 16), 1, Color3.fromRGB(40, 44, 84)), LightInfluence = 0.2, LightEmission = 0,
			Size = ns(0, 0.14, 1, 0.07), Transparency = ns(0, 0, 0.8, 0.1, 1, 1), Lifetime = NumberRange.new(0.4, 0.7),
			Speed = NumberRange.new(9, 17), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -70, 0), Drag = 0.6,
		}):Emit(56)
	end
end

-- ASCEND (epic): a soft shaft of warm light no taller than a doorway gathers round the body; the body glows, lifts a
-- little and goes up into it as motes
STEP.ascend = function(r, t, dt)
	local s = r.s
	if not s.h then
		s.h = highlight(r, Color3.fromRGB(255, 242, 220), Color3.fromRGB(255, 250, 238))
		local top = r.y1 + 2.6
		local bot = r.y0 - 0.1
		local bp = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre.X, bot, r.centre.Z))
		local a0 = Instance.new("Attachment"); a0.Parent = bp; a0.WorldPosition = Vector3.new(r.centre.X, top, r.centre.Z)
		local a1 = Instance.new("Attachment"); a1.Parent = bp; a1.WorldPosition = Vector3.new(r.centre.X, bot, r.centre.Z)
		local function beam(tex: string, w: number, c: Color3): Beam
			local b = Instance.new("Beam")
			b.Attachment0 = a0; b.Attachment1 = a1; b.Texture = tex; b.TextureMode = Enum.TextureMode.Stretch; b.TextureLength = 1
			b.FaceCamera = true; b.LightEmission = 1; b.LightInfluence = 0; b.Color = ColorSequence.new(c); b.Brightness = 2.2
			b.Width0 = 0; b.Width1 = 0; b.Segments = 1
			b:SetAttribute("W", w)
			b.Parent = bp
			return b
		end
		s.b1 = beam(TEX.glow, r.width * 1.5, Color3.fromRGB(255, 238, 205))
		s.b2 = beam(TEX.tracer, r.width * 0.35, Color3.fromRGB(255, 250, 240))
		s.ep = part(r, Vector3.new(r.width * 0.8, r.size.Y * 0.8, r.width * 0.8), r.cf)
		s.e = emitter(r, s.ep, {
			Texture = TEX.glow, Color = cs(Color3.fromRGB(255, 240, 210)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.16, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NumberRange.new(0.6, 1.0),
			Speed = NumberRange.new(1.5, 4), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(12, 12),
			Acceleration = Vector3.new(0, 2, 0),
		})
		s.base = {}
		for _, p in r.parts do s.base[p] = p.part.CFrame end
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.2, smooth((t - 0.1) / 0.4)) + 0.8 * smooth((t - 1.15) / 0.3)
	h.OutlineTransparency = lerp(1, 0.5, smooth((t - 0.1) / 0.4)) + 0.5 * smooth((t - 1.15) / 0.3)
	-- the shaft: in over 0.25 s, out over the last 0.35
	local on = smooth(t / 0.25) * (1 - smooth((t - 1.15) / 0.35))
	for _, b in { s.b1, s.b2 } :: { Beam } do
		local w = (b:GetAttribute("W") :: number) * on
		b.Width0 = w * 0.35; b.Width1 = w
		b.Transparency = ns(0, 1, 0.35, lerp(1, 0.3, on), 1, lerp(1, 0.12, on))
	end
	-- the body lifts and goes, from the feet up
	local lift = 1.6 * smooth((t - 0.3) / 1.0)
	if not r.own then
		for _, p in r.parts do
			local b = s.base[p]
			if b then p.part.CFrame = b + Vector3.new(0, lift, 0) end
		end
	end
	local line = lerp(r.y0 - 0.2, r.y1 + 0.4, smooth((t - 0.55) / 0.8)) + lift
	for _, p in r.parts do
		fade(r, p, clamp01((line - (p.lo + lift)) / math.max(0.2, p.hi - p.lo + 0.4)))
	end
	if t > 0.35 and t < 1.3 then
		s.ep.CFrame = r.cf + Vector3.new(0, lift, 0)
		pour(r, "a", s.e, 45, dt)
	end
end

-- STATIC (legendary): the body breaks up like a lost signal (flicker, jitter, slices), then snaps out to a point
STEP.static = function(r, t, dt)
	local s = r.s
	local OUT = 0.62
	if not s.h then
		s.h = highlight(r, Color3.fromRGB(168, 226, 255), Color3.fromRGB(235, 250, 255))
		s.base = {}
		for _, p in r.parts do s.base[p] = p.part.CFrame end
		s.bars = {}
		for i = 1, 5 do
			local b = part(r, Vector3.new(r.width * 1.5, 0.06, 0.06), r.cf)
			b.Material = Enum.Material.Neon; b.Color = Color3.fromRGB(190, 236, 255); b.Transparency = 1
			s.bars[i] = b
		end
		s.tick = -1
	end
	local rng = s.rng or Random.new()
	s.rng = rng
	if t < OUT then
		local tick = math.floor(t / 0.05)
		if tick ~= s.tick then
			s.tick = tick
			s.h.FillTransparency = ({ 0.15, 0.45, 0.75, 0.3 })[rng:NextInteger(1, 4)]
			s.h.OutlineTransparency = ({ 0.3, 0.7, 1 })[rng:NextInteger(1, 3)]
			local off = Vector3.new(rng:NextNumber(-0.3, 0.3), 0, rng:NextNumber(-0.3, 0.3)) * (if tick % 3 == 0 then 1 else 0.3)
			for _, p in r.parts do
				local b = s.base[p]
				if b and not r.own then p.part.CFrame = b + off end
				fade(r, p, if rng:NextNumber() < 0.18 + t * 0.4 then 1 else 0)
			end
			for _, b in s.bars do
				local y = lerp(r.y0 + 0.2, r.y1 - 0.1, rng:NextNumber())
				b.CFrame = CFrame.new(r.centre.X, y, r.centre.Z) * r.cf.Rotation
				b.Transparency = if rng:NextNumber() < 0.6 then 0.15 else 1
			end
		end
		return
	end
	if not s.out then
		s.out = true
		fadeAll(r, 1)
		s.h.FillTransparency = 1; s.h.OutlineTransparency = 1
		for _, b in s.bars do b.Transparency = 1 end
		local ep = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre))
		emitter(r, ep, {
			Texture = TEX.glow, Color = cs(Color3.fromRGB(205, 242, 255)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 1.1, 1, 0), Transparency = ns(0, 0.1, 1, 0.6), Lifetime = NumberRange.new(0.26), Speed = NumberRange.new(0),
		}):Emit(1)
		emitter(r, ep, {
			Texture = TEX.ring, Color = cs(Color3.fromRGB(205, 242, 255)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.2, 1, 1.5), Transparency = ns(0, 0.35, 1, 1), Lifetime = NumberRange.new(0.3), Speed = NumberRange.new(0),
		}):Emit(1)
		emitter(r, ep, {
			Texture = TEX.spark, Color = cs(Color3.fromRGB(215, 245, 255)), LightEmission = 1, LightInfluence = 0,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Size = ns(0, 0.2, 1, 0), Transparency = ns(0, 0, 1, 1),
			Lifetime = NumberRange.new(0.15, 0.25), Speed = NumberRange.new(10, 16), SpreadAngle = Vector2.new(180, 180),
		}):Emit(12)
	end
end

-- ------------------------------------------------------------------ playing
local function finish(r: Run)
	if r.done then return end
	r.done = true
	busy[r.m] = nil
	fadeAll(r, 1)
	-- the parts it moved go back (a respawned mannequin or a body that's hidden anyway)
	if r.s.base then for p, cf in r.s.base do if p.part.Parent then p.part.CFrame = cf end end end
	if r.hl then r.hl:Destroy() end
	for _, e in r.emitters do e.Rate = 0 end
	local objs = r.objs
	task.delay(1.2, function() for _, o in objs do o:Destroy() end end) -- (the last particles finish their lives)
	if r.own or r.preview then return end
	-- the body stays hidden until it's gone: anything put on it later (a gun copy, a hat) hides too
	table.insert(r.hold, r.m.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") then d.LocalTransparencyModifier = 1 elseif d:IsA("Decal") then d.LocalTransparencyModifier = 1 end
	end))
end

function K.play(m: Model, id: string, opts: { preview: boolean? }?): Run?
	local step = STEP[id]
	local item = Flair.info("kill", id)
	if not step or not item or not m or not m.Parent then return nil end
	local old = busy[m]
	if old then finish(old); for _, x in old.hold do x:Disconnect() end end
	local cf, size = m:GetBoundingBox()
	local cam = workspace.CurrentCamera
	local preview = opts ~= nil and opts.preview == true
	local r: Run = {
		m = m, id = id, t = 0, dur = item.dur, parts = {}, objs = {}, emitters = {}, hl = nil,
		y0 = math.huge, y1 = -math.huge, centre = cf.Position, size = size, width = math.clamp(math.max(size.X, size.Z), 1.4, 4),
		cf = cf, step = step, s = {}, done = false, own = (m == me.Character) and not preview, preview = preview, hold = {},
	}
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" and d.Transparency < 0.99 then
			local pcf, sz = d.CFrame, d.Size * 0.5
			local ext = math.abs(pcf.RightVector.Y) * sz.X + math.abs(pcf.UpVector.Y) * sz.Y + math.abs(pcf.LookVector.Y) * sz.Z
			local p: P = { part = d, lo = pcf.Position.Y - ext, hi = pcf.Position.Y + ext, cf = pcf, decals = {} }
			for _, c in d:GetChildren() do if c:IsA("Decal") then table.insert(p.decals, c) end end
			r.y0 = math.min(r.y0, p.lo); r.y1 = math.max(r.y1, p.hi)
			table.insert(r.parts, p)
		end
	end
	if #r.parts == 0 then return nil end
	busy[m] = r
	if not r.own then
		for _, p in r.parts do
			table.insert(r.hold, p.part:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(function()
				local w = p.want
				if w and p.part.LocalTransparencyModifier ~= w then p.part.LocalTransparencyModifier = w end
			end))
		end
		local c2: RBXScriptConnection? = nil
		c2 = m.AncestryChanged:Connect(function(_, parent)
			if parent then return end
			for _, x in r.hold do x:Disconnect() end
			if c2 then c2:Disconnect() end
		end)
	end
	-- far away: no show, just gone
	if cam and (cam.CFrame.Position - r.centre).Magnitude > FAR and not preview then
		finish(r)
		return r
	end
	table.insert(runs, r)
	return r
end

-- stop one early (the equip screen's mannequin) and put the body back as it was
function K.reset(m: Model)
	local r = busy[m]
	if r then finish(r); for _, x in r.hold do x:Disconnect() end end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).LocalTransparencyModifier = 0 end
	end
end

local lastScale = 1
RunService.RenderStepped:Connect(function(dt: number)
	if #runs == 0 then return end
	local sc = K.scale()
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
		if not ok then warn("[jankfire] kill effect " .. r.id .. ": " .. tostring(err)) end
		if not ok or r.t >= r.dur then
			table.remove(runs, i)
			finish(r)
		end
	end
	lastScale = sc
end)

K.TEX = TEX
return K
