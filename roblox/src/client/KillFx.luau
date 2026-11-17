--!strict
-- KILL EFFECTS, drawn on every client (Shared.Flair "kill" items; doc FLAIR.md). The server picks the effect (the real
-- killer's, FlairServer), freezes the body where it fell (anchored, no collisions) and tells everyone (FlairKill); this
-- draws it. The body's own parts fade with LocalTransparencyModifier (nothing replicates), one Highlight tints them,
-- and a few particles and client-only parts do the rest; at the end the body is hidden for good (the respawn makes a
-- new one). Rules (the owner's brief, Rivals research): 1.5 s at most, the size of a body (nothing reaches more than
-- about 4 studs out), no tall pillars, no floor marks, no screen effects, quiet colours. A body further than FAR studs
-- from the camera, or any body when OTHERS' KILL EFFECTS is off in the settings (opts.quiet), just hides.
-- K.play(model, id, opts?) -> run handle (opts.preview: a client-only mannequin, the equip screen's; opts.from: where the
-- killer stood, for the ones that throw the body away from them)
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
	feather = "rbxassetid://92745845385867", -- a soft white feather
	streak = "rbxassetid://127914373549121", -- a soft white streak
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

-- the settings page's GRAPHICS rows (StarterPlayerScripts.Jankfire.Settings, the settings session's; defaults when it
-- isn't in): "gfx.particles" (0.25..1) scales every burst and stream here
local SettingsMod: any = nil
function K.setting(key: string, default: any): any
	if SettingsMod == nil then
		local m = script.Parent:FindFirstChild("Settings")
		local ok, res = false, nil
		if m and m:IsA("ModuleScript") then ok, res = pcall(require, m) end
		SettingsMod = if ok and type(res) == "table" and type(res.get) == "function" then res else false
	end
	if not SettingsMod then return default end
	local ok, v = pcall(SettingsMod.get, key)
	if ok and v ~= nil then return v end
	return default
end
local function amount(): number
	local k = K.setting("gfx.particles", 1)
	return if type(k) == "number" then math.clamp(k, 0.25, 1) else 1
end
-- a burst of n, fewer on the LOW preset (a single flash or ring stays one)
local function many(n: number): number
	if n <= 1 then return n end
	return math.max(1, math.floor(n * amount() + 0.5))
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
	hold: { RBXScriptConnection }, from: Vector3?,
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
		}):Emit(many(24))
		emitter(r, ep, {
			Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			FlipbookFramerate = NumberRange.new(16 / 0.6), Color = cs(Color3.fromRGB(222, 232, 242)), LightInfluence = 0.6, LightEmission = 0.1,
			Size = ns(0, 0.7, 1, 1.3), Transparency = ns(0, 0.55, 1, 1), Lifetime = NumberRange.new(0.6),
			Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 360),
		}):Emit(many(5))
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
		}):Emit(many(20))
		-- (torn flakes between the blots: a splash, not a handful of balls)
		emitter(r, ep, {
			Texture = TEX.chips, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.Random,
			Color = cs(Color3.fromRGB(12, 12, 18)), LightInfluence = 0.2, LightEmission = 0,
			Size = ns(0, 0.24, 1, 0.1), Transparency = ns(0, 0, 0.8, 0.1, 1, 1), Lifetime = NumberRange.new(0.4, 0.65),
			Speed = NumberRange.new(8, 15), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -62, 0), Drag = 1,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-300, 300),
		}):Emit(many(28))
		emitter(r, ep, {
			Texture = TEX.glow, Color = cs(0, Color3.fromRGB(10, 10, 16), 1, Color3.fromRGB(40, 44, 84)), LightInfluence = 0.2, LightEmission = 0,
			Size = ns(0, 0.14, 1, 0.07), Transparency = ns(0, 0, 0.8, 0.1, 1, 1), Lifetime = NumberRange.new(0.4, 0.7),
			Speed = NumberRange.new(9, 17), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -70, 0), Drag = 0.6,
		}):Emit(many(56))
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
		}):Emit(many(12))
	end
end

-- ------------------------------------------------------------------ the web game's twelve, restyled (17 Nov: the owner
-- asked for the web list itself; ids, names and rarities as shared/cosmetics.js has them, the look made quiet and serious:
-- no text anywhere, no gore, ≤1.5 s, nothing past a few studs except what leaves for good)

-- the whole body moved as one: each part from where it was when the effect began, through `T` (a CFrame about the world)
local function moveBody(r: Run, T: CFrame)
	if r.own then return end
	local s = r.s
	if not s.base then
		s.base = {}
		for _, p in r.parts do s.base[p] = p.part.CFrame end
	end
	for _, p in r.parts do
		local b = s.base[p]
		if b then p.part.CFrame = T * b end
	end
end
-- a client-only piece of a prop (anchored, no collisions), kept in the run's objects
local function prop(r: Run, shape: Enum.PartType?, size: Vector3, color: Color3, mat: Enum.Material?): Part
	local p = part(r, size, r.cf)
	p.Shape = shape or Enum.PartType.Block
	p.Transparency = 0; p.Color = color; p.Material = mat or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	return p
end
-- loose bits flying with gravity and drag (notes, cubes): { p, cf, v, spin, size? }
local function flyBits(bits: { any }, dt: number, g: number, drag: number)
	local k = math.max(0, 1 - drag * dt)
	for _, b in bits do
		b.v = Vector3.new(b.v.X * k, b.v.Y * k + g * dt, b.v.Z * k)
		b.cf = (b.cf + b.v * dt) * CFrame.Angles(b.spin.X * dt, b.spin.Y * dt, b.spin.Z * dt)
		b.p.CFrame = b.cf
	end
end
local function fadeBits(bits: { any }, a: number)
	for _, b in bits do b.p.Transparency = math.max(b.p.Transparency, a) end
end
-- facing the camera, flat (for props that show a front)
local function toCamera(r: Run): CFrame
	local cam = workspace.CurrentCamera
	local d = (cam.CFrame.Position - r.centre) * Vector3.new(1, 0, 1)
	d = if d.Magnitude > 1e-3 then d.Unit else Vector3.new(0, 0, 1)
	return CFrame.lookAt(Vector3.zero, d)
end
local function burstAt(r: Run, at: CFrame, size: Vector3): Part
	return part(r, size, at)
end

-- GIBS ("none", free): the body falls apart as it always has. nothing to draw

-- CONFETTI (free): a white pop, then the body bursts into paper confetti that flutters down. quiet paper colours, one amber
STEP.confetti = function(r, t, dt)
	local s = r.s
	if not s.h then s.h = highlight(r, Color3.fromRGB(250, 248, 242), Color3.fromRGB(255, 255, 255)) end
	if t < 0.08 then s.h.FillTransparency = lerp(1, 0.15, t / 0.08); return end
	if s.popped then return end
	s.popped = true
	fadeAll(r, 1)
	s.h.FillTransparency = 1
	local ep = burstAt(r, r.cf * CFrame.new(0, r.size.Y * 0.12, 0), Vector3.new(r.width * 0.6, r.size.Y * 0.4, r.width * 0.4))
	for _, c in { Color3.fromRGB(242, 238, 228), Color3.fromRGB(236, 196, 96), Color3.fromRGB(150, 160, 176), Color3.fromRGB(200, 156, 124) } do
		emitter(r, ep, {
			Texture = TEX.chips, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid2x2, FlipbookMode = Enum.ParticleFlipbookMode.Random,
			Color = cs(c), LightInfluence = 0.9, LightEmission = 0.05, Size = ns(0, 0.16, 1, 0.13),
			Transparency = ns(0, 0, 0.8, 0, 1, 1), Lifetime = NumberRange.new(1.0, 1.3), Speed = NumberRange.new(10, 17),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, -22, 0), Drag = 2.4,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-420, 420),
		}):Emit(many(18))
	end
	emitter(r, ep, {
		Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
		FlipbookFramerate = NumberRange.new(16 / 0.5), Color = cs(Color3.fromRGB(240, 238, 232)), LightInfluence = 0.7,
		Size = ns(0, 0.8, 1, 1.4), Transparency = ns(0, 0.5, 1, 1), Lifetime = NumberRange.new(0.5), Speed = NumberRange.new(0.5, 1.5),
		SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 360),
	}):Emit(many(4))
end

-- TOMBSTONE (common): the body sinks into the floor as a plain stone marker rises where it stood, then both go. no words on it
STEP.grave = function(r, t, dt)
	local s = r.s
	if not s.stone then
		local face = toCamera(r)
		local w = math.clamp(r.width * 0.95, 1.8, 2.6)
		local hgt = w * 1.05
		local STONE = Color3.fromRGB(120, 124, 130)
		local slab = prop(r, nil, Vector3.new(w, hgt, 0.55), STONE, Enum.Material.Slate)
		local top = prop(r, Enum.PartType.Cylinder, Vector3.new(0.55, w, w), STONE, Enum.Material.Slate)
		local plinth = prop(r, nil, Vector3.new(w + 0.5, 0.35, 1.0), Color3.fromRGB(96, 100, 106), Enum.Material.Slate)
		s.stone = { slab = slab, top = top, plinth = plinth, face = face, w = w, h = hgt }
		local base = CFrame.new(r.centre.X, r.y0, r.centre.Z) * face.Rotation
		s.stoneBase = base
		local dp = burstAt(r, base, Vector3.new(w + 1, 0.3, 1.4))
		s.dust = emitter(r, dp, {
			Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			FlipbookFramerate = NumberRange.new(16 / 0.7), Color = cs(Color3.fromRGB(150, 146, 138)), LightInfluence = 0.9,
			Size = ns(0, 0.7, 1, 1.5), Transparency = ns(0, 0.45, 1, 1), Lifetime = NumberRange.new(0.7), Speed = NumberRange.new(1, 3),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(70, 70), Rotation = NumberRange.new(0, 360),
		})
	end
	local st = s.stone
	-- the stone: up from under the floor (0.12-0.5 s, a little overshoot), held, back down from 1.15 s
	local up = smooth((t - 0.12) / 0.38)
	local over = math.sin(math.clamp((t - 0.12) / 0.38, 0, 1) * math.pi) * 0.12
	local down = smooth((t - 1.15) / 0.35)
	local rise = (up + over) * (1 - down)
	local y = -(st.h + st.w / 2 + 0.4) * (1 - rise)
	local b = s.stoneBase * CFrame.new(0, y, 0)
	st.plinth.CFrame = b * CFrame.new(0, 0.17, 0)
	st.slab.CFrame = b * CFrame.new(0, 0.35 + st.h / 2, 0)
	st.top.CFrame = b * CFrame.new(0, 0.35 + st.h, 0) * CFrame.Angles(0, math.pi / 2, 0)
	if t > 0.14 and not s.puffed then s.puffed = true; s.dust:Emit(many(7)) end
	-- the body: down into the floor and out
	local sink = smooth((t - 0.2) / 0.9)
	moveBody(r, CFrame.new(0, -3.2 * sink, 0))
	for _, p in r.parts do fade(r, p, clamp01((t - 0.35) / 0.7)) end
end

-- MAKE IT RAIN (common): the body pops into a shower of plain paper notes (no print on them) that drift down
STEP.cash = function(r, t, dt)
	local s = r.s
	if not s.h then s.h = highlight(r, Color3.fromRGB(196, 214, 184), Color3.fromRGB(230, 240, 222)) end
	if t < 0.1 then s.h.FillTransparency = lerp(1, 0.35, t / 0.1); return end
	if not s.notes then
		fadeAll(r, 1)
		s.h.FillTransparency = 1
		s.notes = {}
		local rng = Random.new()
		for i = 1, 22 do
			local c = Color3.fromRGB(116 + rng:NextInteger(-8, 8), 148 + rng:NextInteger(-8, 8), 104 + rng:NextInteger(-6, 6))
			local n = prop(r, nil, Vector3.new(0.66, 0.03, 0.32), c)
			local at = r.centre + Vector3.new(rng:NextNumber(-0.5, 0.5) * r.width, rng:NextNumber(-0.3, 0.45) * r.size.Y, rng:NextNumber(-0.5, 0.5) * r.width)
			local cf = CFrame.new(at) * CFrame.Angles(rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28))
			local out = (at - r.centre) * Vector3.new(1, 0, 1)
			out = if out.Magnitude > 1e-3 then out.Unit else Vector3.new(1, 0, 0)
			table.insert(s.notes, { p = n, cf = cf, v = out * rng:NextNumber(3, 7) + Vector3.new(0, rng:NextNumber(8, 14), 0),
				spin = Vector3.new(rng:NextNumber(-7, 7), rng:NextNumber(-7, 7), rng:NextNumber(-7, 7)) })
		end
		local ep = burstAt(r, r.cf, r.size * Vector3.new(0.6, 0.6, 0.6))
		emitter(r, ep, {
			Texture = TEX.sparkle, Color = cs(Color3.fromRGB(236, 244, 226)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.3, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NumberRange.new(0.3, 0.5),
			Speed = NumberRange.new(3, 7), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 90),
		}):Emit(many(8))
	end
	flyBits(s.notes, dt, -26, 2.6)
	if t > 1.0 then fadeBits(s.notes, smooth((t - 1.0) / 0.4)) end
end

-- MISSING TEXTURE (rare): the body flickers and breaks into small cubes, near-black and one muted magenta (the old
-- missing-texture check, quietened), which drift off and blink out
STEP.pixel = function(r, t, dt)
	local s = r.s
	local MAG, BLK = Color3.fromRGB(170, 60, 150), Color3.fromRGB(24, 24, 30)
	if not s.h then s.h = highlight(r, MAG, BLK); s.tick = -1 end
	if t < 0.14 then
		local k = math.floor(t / 0.035)
		if k ~= s.tick then s.tick = k; s.h.FillTransparency = if k % 2 == 0 then 0.25 else 0.7; s.h.OutlineTransparency = 0.3 end
		return
	end
	if not s.cubes then
		fadeAll(r, 1)
		s.h.FillTransparency = 1; s.h.OutlineTransparency = 1
		s.cubes = {}
		local rng = Random.new()
		local list = table.clone(r.parts)
		table.sort(list, function(a, b) return a.part.Size.Magnitude > b.part.Size.Magnitude end)
		for i = 1, math.min(15, #list) do
			local pp = list[i].part
			for j = 1, 2 do
				local sz = rng:NextNumber(0.3, 0.46)
				local c = prop(r, nil, Vector3.new(sz, sz, sz), if (i + j) % 2 == 0 then MAG else BLK)
				local off = Vector3.new(rng:NextNumber(-0.3, 0.3) * pp.Size.X, rng:NextNumber(-0.35, 0.35) * pp.Size.Y, rng:NextNumber(-0.3, 0.3) * pp.Size.Z)
				local cf = pp.CFrame * CFrame.new(off)
				local out = (cf.Position - r.centre) * Vector3.new(1, 0, 1)
				out = if out.Magnitude > 1e-3 then out.Unit else Vector3.new(0, 0, 1)
				table.insert(s.cubes, { p = c, cf = cf, v = out * rng:NextNumber(1.5, 4) + Vector3.new(0, rng:NextNumber(1.5, 5), 0),
					spin = Vector3.new(rng:NextNumber(-3, 3), rng:NextNumber(-3, 3), rng:NextNumber(-3, 3)) })
			end
		end
	end
	flyBits(s.cubes, dt, -11, 0.8)
	local k = math.floor(t / 0.06)
	if k ~= s.tick then
		s.tick = k
		local rng = Random.new(k)
		for _, c in s.cubes do
			local gone = clamp01((t - 0.75) / 0.45)
			c.p.Transparency = if rng:NextNumber() < gone then 1 elseif rng:NextNumber() < 0.15 then 0.6 else 0
		end
	end
end

-- BALLOONS (rare): a small bunch of plain balloons ties on, and the body floats up and away, fading
STEP.balloon = function(r, t, dt)
	local s = r.s
	if not s.balls then
		s.balls = {}
		local cols = { Color3.fromRGB(236, 230, 214), Color3.fromRGB(176, 182, 192), Color3.fromRGB(226, 178, 84), Color3.fromRGB(116, 134, 162), Color3.fromRGB(226, 220, 204) }
		local hold = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre.X, r.y1 - 1.2, r.centre.Z))
		local a0 = Instance.new("Attachment"); a0.Parent = hold
		s.hold = hold
		local rng = Random.new()
		for i, c in cols do
			local d = rng:NextNumber(1.0, 1.25)
			local b = prop(r, Enum.PartType.Ball, Vector3.new(d, d * 1.12, d), c)
			b.Reflectance = 0.04
			local ang = (i - 1) / #cols * math.pi * 2 + rng:NextNumber(-0.3, 0.3)
			local off = Vector3.new(math.cos(ang) * 0.9, 2.4 + rng:NextNumber(0, 1.3), math.sin(ang) * 0.9)
			local a1 = Instance.new("Attachment"); a1.Position = Vector3.new(0, -d * 0.5, 0); a1.Parent = b
			local str = Instance.new("Beam")
			str.Attachment0 = a0; str.Attachment1 = a1; str.Width0 = 0.03; str.Width1 = 0.03; str.FaceCamera = true; str.Segments = 1
			str.Color = ColorSequence.new(Color3.fromRGB(214, 218, 224)); str.LightInfluence = 1; str.Transparency = NumberSequence.new(0.15)
			str.Parent = b
			table.insert(s.balls, { p = b, off = off, d = d, beam = str })
		end
	end
	local pop = smooth(t / 0.18)
	local lift = 6.5 * smooth((t - 0.22) / 1.28) ^ 1.4
	local sway = math.sin(t * 3.2) * 0.35 * smooth((t - 0.2) / 0.5)
	local T = CFrame.new(sway, lift, 0)
	moveBody(r, T)
	s.hold.CFrame = T * CFrame.new(r.centre.X, r.y1 - 1.2, r.centre.Z)
	for i, b in s.balls do
		local bob = math.sin(t * 4 + i) * 0.08
		b.p.Size = Vector3.new(b.d, b.d * 1.12, b.d) * math.max(0.05, pop)
		b.p.CFrame = T * CFrame.new(r.centre.X + b.off.X, r.y1 + b.off.Y * pop + bob, r.centre.Z + b.off.Z)
		local f = smooth((t - 1.2) / 0.3)
		b.p.Transparency = f
		b.beam.Transparency = NumberSequence.new(lerp(0.15, 1, f))
	end
	for _, p in r.parts do fade(r, p, smooth((t - 0.85) / 0.6)) end
end

-- CHICKENS (epic): a soft pop of feathers, and where the body was, three small chickens scatter and run off
local function chicken(r: Run): { any }
	local W, BEAK, COMB = Color3.fromRGB(238, 230, 212), Color3.fromRGB(214, 150, 70), Color3.fromRGB(176, 72, 66)
	local body = prop(r, Enum.PartType.Ball, Vector3.new(0.95, 0.85, 1.05), W)
	local head = prop(r, Enum.PartType.Ball, Vector3.new(0.55, 0.58, 0.55), W)
	local beak = prop(r, nil, Vector3.new(0.18, 0.12, 0.26), BEAK)
	local comb = prop(r, Enum.PartType.Ball, Vector3.new(0.12, 0.24, 0.26), COMB)
	local tail = prop(r, nil, Vector3.new(0.5, 0.42, 0.18), W)
	return { { body, CFrame.new(0, 0.5, 0) }, { head, CFrame.new(0, 1.0, -0.42) }, { beak, CFrame.new(0, 0.98, -0.75) },
		{ comb, CFrame.new(0, 1.3, -0.42) }, { tail, CFrame.new(0, 0.82, 0.48) * CFrame.Angles(math.rad(-30), 0, 0) } }
end
STEP.chicken = function(r, t, dt)
	local s = r.s
	if not s.h then s.h = highlight(r, Color3.fromRGB(246, 240, 228), Color3.fromRGB(255, 255, 255)) end
	if t < 0.1 then s.h.FillTransparency = lerp(1, 0.2, t / 0.1); return end
	if not s.birds then
		fadeAll(r, 1)
		s.h.FillTransparency = 1
		local ep = burstAt(r, r.cf, r.size * Vector3.new(0.6, 0.6, 0.6))
		emitter(r, ep, {
			Texture = TEX.feather, Color = cs(Color3.fromRGB(244, 238, 226)), LightInfluence = 0.8, LightEmission = 0.05,
			Size = ns(0, 0.26, 1, 0.22), Transparency = ns(0, 0, 0.75, 0.1, 1, 1), Lifetime = NumberRange.new(0.9, 1.3),
			Speed = NumberRange.new(5, 11), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -7, 0), Drag = 2.6,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-220, 220),
		}):Emit(many(24))
		s.birds = {}
		local rng = Random.new()
		local a0 = rng:NextNumber(0, math.pi * 2)
		for i = 1, 3 do
			local ang = a0 + (i - 1) * math.pi * 2 / 3 + rng:NextNumber(-0.3, 0.3)
			table.insert(s.birds, { bits = chicken(r), dir = Vector3.new(math.cos(ang), 0, math.sin(ang)), speed = rng:NextNumber(6.5, 8.5), ph = rng:NextNumber(0, 6) })
		end
	end
	local run = t - 0.1
	for _, b in s.birds do
		local at = Vector3.new(r.centre.X, r.y0, r.centre.Z) + b.dir * (0.4 + b.speed * run)
		local hop = math.abs(math.sin(run * 16 + b.ph)) * 0.22
		local base = CFrame.lookAt(at, at + b.dir) * CFrame.new(0, hop, 0) * CFrame.Angles(0, 0, math.sin(run * 16 + b.ph) * 0.12)
		local f = smooth((t - 1.15) / 0.35)
		for _, bit in b.bits do
			bit[1].CFrame = base * bit[2]
			bit[1].Transparency = f
		end
	end
end

-- BLUE SCREEN (epic): the body is replaced by a flat blue panel carrying the web game's words (FATAL ERROR, player.exe:
-- the owner, 17 Nov, said text is fine here; it's drawn live in the game's font, never baked into an uploaded picture) and
-- a bar filling up, which then switches off like an old monitor: down to a bright line, a dot, gone. the one kill effect
-- with words on it
STEP.bsod = function(r, t, dt)
	local s = r.s
	if not s.gui then
		s.h = highlight(r, Color3.fromRGB(60, 100, 190), Color3.fromRGB(150, 180, 240))
		local hold = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre))
		local w, h = math.max(2.6, r.width * 1.35), math.max(3.2, r.size.Y * 0.82)
		local g = Instance.new("BillboardGui")
		g.Size = UDim2.new(w, 0, h, 0); g.AlwaysOnTop = false; g.LightInfluence = 0; g.Brightness = 1.3
		g.MaxDistance = 400; g.Adornee = hold; g.Parent = hold
		local bg = Instance.new("Frame")
		bg.BackgroundColor3 = Color3.fromRGB(38, 76, 160); bg.BorderSizePixel = 0; bg.AnchorPoint = Vector2.new(0.5, 0.5)
		bg.Position = UDim2.fromScale(0.5, 0.5); bg.Size = UDim2.fromScale(1, 1); bg.Parent = g
		local function bar(x: number, y: number, ww: number, hh: number, c: Color3, a: number?): Frame
			local f = Instance.new("Frame")
			f.BackgroundColor3 = c; f.BorderSizePixel = 0; f.Position = UDim2.fromScale(x, y); f.Size = UDim2.fromScale(ww, hh)
			f.BackgroundTransparency = a or 0; f.Parent = bg
			return f
		end
		local LITE = Color3.fromRGB(214, 224, 244)
		local function words(text: string, y: number, hh: number, weight: Enum.FontWeight, a: number)
			local l = Instance.new("TextLabel")
			l.BackgroundTransparency = 1; l.Position = UDim2.fromScale(0.1, y); l.Size = UDim2.fromScale(0.8, hh)
			l.FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", weight); l.Text = text; l.TextScaled = true
			l.TextColor3 = LITE; l.TextTransparency = a; l.TextXAlignment = Enum.TextXAlignment.Left; l.Parent = bg
		end
		words("FATAL ERROR", 0.1, 0.15, Enum.FontWeight.Bold, 0)
		words("player.exe", 0.29, 0.085, Enum.FontWeight.Medium, 0.1)
		bar(0.1, 0.46, 0.64, 0.035, LITE, 0.35); bar(0.1, 0.52, 0.5, 0.035, LITE, 0.35)
		local track = bar(0.1, 0.7, 0.8, 0.06, Color3.fromRGB(20, 40, 96))
		local fill = Instance.new("Frame")
		fill.BackgroundColor3 = LITE; fill.BorderSizePixel = 0; fill.Size = UDim2.fromScale(0, 1); fill.Parent = track
		s.gui, s.bg, s.fill, s.w, s.h2 = g, bg, fill, w, h
		g.Enabled = false
	end
	if t < 0.06 then s.h.FillTransparency = lerp(1, 0.2, t / 0.06); return end
	if not s.on then
		s.on = true
		fadeAll(r, 1)
		s.h.FillTransparency = 1; s.h.OutlineTransparency = 1
		s.gui.Enabled = true
	end
	local g = s.gui :: BillboardGui
	local pin = smooth((t - 0.06) / 0.08)
	s.fill.Size = UDim2.fromScale(clamp01((t - 0.15) / 0.6) * 0.75, 1)
	local off1 = smooth((t - 0.8) / 0.14) -- down to a line
	local off2 = smooth((t - 0.94) / 0.14) -- in to a dot
	local w = s.w * (0.92 + 0.08 * pin) * lerp(1, 0.04, off2)
	local h = s.h2 * (0.92 + 0.08 * pin) * lerp(1, 0.035, off1)
	g.Size = UDim2.new(w, 0, h, 0)
	s.bg.BackgroundColor3 = Color3.fromRGB(38, 76, 160):Lerp(Color3.fromRGB(236, 242, 255), off1)
	for _, c in s.bg:GetChildren() do if c:IsA("GuiObject") then c.Visible = off1 < 0.5 end end
	s.bg.BackgroundTransparency = smooth((t - 1.08) / 0.12)
end

-- YEET (epic): the body is launched straight up, spinning, a dotted streak under it, and blinks out high above with a glint
STEP.yeet = function(r, t, dt)
	local s = r.s
	if not s.e then
		s.h = highlight(r, Color3.fromRGB(236, 242, 255), Color3.fromRGB(255, 255, 255))
		s.ep = part(r, Vector3.new(r.width * 0.5, 0.4, r.width * 0.5), r.cf)
		s.e = emitter(r, s.ep, {
			Texture = TEX.glow, Color = cs(Color3.fromRGB(236, 242, 252)), LightEmission = 0.8, LightInfluence = 0,
			Size = ns(0, 0.22, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NumberRange.new(0.35, 0.5), Speed = NumberRange.new(0, 0.6),
		})
		local feet = burstAt(r, CFrame.new(r.centre.X, r.y0 + 0.2, r.centre.Z), Vector3.new(r.width, 0.3, r.width))
		emitter(r, feet, {
			Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			FlipbookFramerate = NumberRange.new(16 / 0.6), Color = cs(Color3.fromRGB(200, 198, 192)), LightInfluence = 0.9,
			Size = ns(0, 0.7, 1, 1.5), Transparency = ns(0, 0.45, 1, 1), Lifetime = NumberRange.new(0.6), Speed = NumberRange.new(2, 4),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(80, 80), Rotation = NumberRange.new(0, 360),
		}):Emit(many(6))
		s.glint = burstAt(r, r.cf, Vector3.new(0.2, 0.2, 0.2))
		s.ge = emitter(r, s.glint, {
			Texture = TEX.sparkle, Color = cs(Color3.fromRGB(255, 248, 230)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.4, 0.3, 1.4, 1, 0), Transparency = ns(0, 0, 1, 0.4), Lifetime = NumberRange.new(0.35), Speed = NumberRange.new(0),
			Rotation = NumberRange.new(0, 45),
		})
	end
	s.h.FillTransparency = lerp(1, 0.55, smooth(t / 0.08)) + 0.45 * smooth((t - 0.2) / 0.3)
	local u = math.max(0, t - 0.06)
	local up = 22 * u + 34 * u * u
	local spin = u * 11
	local c = r.centre
	local T = CFrame.new(c + Vector3.new(0, up, 0)) * CFrame.Angles(math.sin(u * 3) * 0.25, spin, 0) * CFrame.new(-c)
	moveBody(r, T)
	if t < 1.0 then
		s.ep.CFrame = CFrame.new(c + Vector3.new(0, up - r.size.Y * 0.3, 0))
		pour(r, "a", s.e, 90, dt)
	end
	if t > 0.98 and not s.dinged then
		s.dinged = true
		s.glint.CFrame = CFrame.new(c + Vector3.new(0, up, 0))
		s.ge:Emit(1)
		fadeAll(r, 1)
	elseif not s.dinged then
		for _, p in r.parts do fade(r, p, smooth((t - 0.7) / 0.28) * 0.6) end
	end
end

-- BIG DUCK (legendary): a big rubber duck drops onto the body, settles with a squash, gulps, and shrinks away with a puff.
-- built from a few round pieces, the game's own duck yellow
local function duck(r: Run): { any }
	local Y, BEAK, EYE = Color3.fromRGB(236, 196, 72), Color3.fromRGB(214, 128, 52), Color3.fromRGB(26, 26, 30)
	local pieces = {
		{ prop(r, Enum.PartType.Ball, Vector3.new(4.0, 3.0, 4.6), Y), CFrame.new(0, 1.5, 0.2), Vector3.new(4.0, 3.0, 4.6) },
		{ prop(r, Enum.PartType.Ball, Vector3.new(2.4, 2.4, 2.4), Y), CFrame.new(0, 3.5, -1.3), Vector3.new(2.4, 2.4, 2.4) },
		{ prop(r, Enum.PartType.Ball, Vector3.new(1.3, 0.55, 1.2), BEAK), CFrame.new(0, 3.3, -2.6), Vector3.new(1.3, 0.55, 1.2) },
		{ prop(r, Enum.PartType.Ball, Vector3.new(0.32, 0.32, 0.32), EYE), CFrame.new(0.62, 3.85, -2.2), Vector3.new(0.32, 0.32, 0.32) },
		{ prop(r, Enum.PartType.Ball, Vector3.new(0.32, 0.32, 0.32), EYE), CFrame.new(-0.62, 3.85, -2.2), Vector3.new(0.32, 0.32, 0.32) },
		{ prop(r, Enum.PartType.Ball, Vector3.new(1.6, 1.4, 1.6), Y), CFrame.new(0, 2.4, 2.4) * CFrame.Angles(math.rad(-35), 0, 0), Vector3.new(1.6, 1.4, 1.6) },
	}
	for _, p in pieces do p[1].Material = Enum.Material.SmoothPlastic; p[1].Reflectance = 0.05 end
	return pieces
end
STEP.duck = function(r, t, dt)
	local s = r.s
	if not s.duck then
		s.duck = duck(r)
		s.face = toCamera(r)
		local foot = CFrame.new(r.centre.X, r.y0, r.centre.Z)
		s.foot = foot
		local ep = burstAt(r, foot * CFrame.new(0, 1.2, 0), Vector3.new(3.5, 1.5, 3.5))
		s.puff = emitter(r, ep, {
			Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			FlipbookFramerate = NumberRange.new(16 / 0.6), Color = cs(Color3.fromRGB(244, 240, 228)), LightInfluence = 0.8,
			Size = ns(0, 0.9, 1, 1.8), Transparency = ns(0, 0.4, 1, 1), Lifetime = NumberRange.new(0.6), Speed = NumberRange.new(2, 5),
			SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 360),
		})
	end
	-- drop (0-0.3), squash on landing (0.3-0.5), a gulp (0.6-0.8), shrink away (0.95-1.3)
	local drop = clamp01(t / 0.3)
	local y = 9 * (1 - drop * drop)
	local land = clamp01((t - 0.3) / 0.2)
	local sq = if t >= 0.3 then 1 - 0.22 * math.sin(land * math.pi) else 1
	local gulp = if t > 0.6 and t < 0.8 then math.sin((t - 0.6) / 0.2 * math.pi) * 0.12 else 0
	local shrink = 1 - smooth((t - 0.95) / 0.35)
	local k = math.max(0.02, shrink)
	if t >= 0.3 and not s.landed then
		s.landed = true
		fadeAll(r, 1)
		s.puff:Emit(many(8))
	end
	if t >= 1.28 and not s.gone then s.gone = true; s.puff:Emit(many(6)) end
	local base = s.foot * CFrame.new(0, y, 0) * s.face.Rotation * CFrame.Angles(0, math.rad(35) + (1 - shrink) * 2.5, 0)
	for _, p in s.duck do
		local off = p[2]
		local scaleY = sq * (1 + gulp)
		local pos = Vector3.new(off.X * k * (2 - sq), off.Y * k * scaleY, off.Z * k)
		p[1].Size = Vector3.new(p[3].X * (2 - sq), p[3].Y * scaleY, p[3].Z) * k
		p[1].CFrame = base * CFrame.new(pos) * off.Rotation
		p[1].Transparency = if k <= 0.03 then 1 else 0
	end
end

-- BLAST ZONE (legendary): a white-hot flash and shock ring, and the body is knocked clean away from whoever got the
-- kill, spinning, out of sight
STEP.blastzone = function(r, t, dt)
	local s = r.s
	if not s.h then
		s.h = highlight(r, Color3.fromRGB(255, 232, 196), Color3.fromRGB(255, 246, 230))
		local away = (r.centre - (r.from or (r.centre - workspace.CurrentCamera.CFrame.LookVector))) * Vector3.new(1, 0, 1)
		away = if away.Magnitude > 1e-3 then away.Unit else Vector3.new(0, 0, -1)
		s.dir = (away + Vector3.new(0, 0.32, 0)).Unit
		s.axis = away:Cross(Vector3.yAxis)
		local ep = burstAt(r, r.cf, Vector3.new(0.4, 0.4, 0.4))
		s.ring = emitter(r, ep, {
			Texture = TEX.ring, Color = cs(Color3.fromRGB(255, 236, 206)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 0.6, 1, 4.2), Transparency = ns(0, 0.2, 1, 1), Lifetime = NumberRange.new(0.32), Speed = NumberRange.new(0),
		})
		s.flash = emitter(r, ep, {
			Texture = TEX.glow, Color = cs(Color3.fromRGB(255, 244, 226)), LightEmission = 1, LightInfluence = 0,
			Size = ns(0, 2.4, 1, 0), Transparency = ns(0, 0, 1, 0.5), Lifetime = NumberRange.new(0.2), Speed = NumberRange.new(0),
		})
		s.sparks = emitter(r, ep, {
			Texture = TEX.spark, Color = cs(0, Color3.fromRGB(255, 240, 214), 1, Color3.fromRGB(255, 170, 90)), LightEmission = 1, LightInfluence = 0,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Size = ns(0, 0.34, 1, 0), Transparency = ns(0, 0, 1, 1),
			Lifetime = NumberRange.new(0.18, 0.3), Speed = NumberRange.new(28, 46), SpreadAngle = Vector2.new(180, 180),
		})
		s.tp = part(r, Vector3.new(r.width * 0.5, r.size.Y * 0.5, r.width * 0.5), r.cf)
		s.trail = emitter(r, s.tp, {
			Texture = TEX.glow, Color = cs(Color3.fromRGB(255, 232, 200)), LightEmission = 0.9, LightInfluence = 0,
			Size = ns(0, 0.3, 1, 0), Transparency = ns(0, 0.15, 1, 1), Lifetime = NumberRange.new(0.25, 0.35), Speed = NumberRange.new(0, 0.5),
		})
	end
	if t < 0.06 then s.h.FillTransparency = lerp(1, 0, t / 0.06); return end
	if not s.hit then
		s.hit = true
		s.ring:Emit(1); s.flash:Emit(1); s.sparks:Emit(many(18))
	end
	s.h.FillTransparency = lerp(0, 1, smooth((t - 0.06) / 0.2))
	s.h.OutlineTransparency = lerp(0.3, 1, smooth((t - 0.06) / 0.35))
	local u = t - 0.06
	local dist = 150 * u - 20 * u * u
	local c = r.centre
	local T = CFrame.new(c + s.dir * dist) * CFrame.fromAxisAngle(s.axis, u * 22) * CFrame.new(-c)
	moveBody(r, T)
	if t < 0.75 then
		s.tp.CFrame = CFrame.new(c + s.dir * dist)
		pour(r, "a", s.trail, 140, dt)
	end
	if t > 0.7 then for _, p in r.parts do fade(r, p, smooth((t - 0.7) / 0.25)) end end
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

function K.play(m: Model, id: string, opts: { preview: boolean?, from: Vector3?, quiet: boolean? }?): Run?
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
		from = opts and opts.from,
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
	if (opts and opts.quiet) or (cam and (cam.CFrame.Position - r.centre).Magnitude > FAR and not preview) then
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
