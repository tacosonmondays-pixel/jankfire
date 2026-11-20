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
	crack = "rbxassetid://101305195948274", -- radiating ground cracks, one 1024 px image (the practice loop's, ours)
	arc = "rbxassetid://108885047117384", -- a wind arc (the practice loop's, ours)
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

-- a flat sprite lying on the floor (cracks, a hole, whirlpool arms): one particle, its size by `sz` over its life
local function flat(r: Run, tex: string, c: Color3, sz: NumberSequence, life: number, le: number, props: { [string]: any }?): ParticleEmitter
	local p = part(r, Vector3.new(0.2, 0.2, 0.2), floorAt(r, r.y0 + 0.06) * CFrame.Angles(math.rad(90), 0, 0))
	local e = emitter(r, p, { Texture = tex, Color = cs(c), LightEmission = le, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
		EmissionDirection = Enum.NormalId.Front, Speed = NR(0.01), SpreadAngle = Vector2.new(0, 0), Size = sz,
		Transparency = ns(0, 0, 0.8, 0, 1, 1), Lifetime = NR(life), Rotation = NR(0, 360) })
	if props then for k, v in props do (e :: any)[k] = v end end
	return e
end
-- a SHELL of the body: each part copied client-side, its textures stripped, one flat colour; the body itself hidden.
-- real geometry, so particles and beams in front of it sort properly (a Highlight's fill draws over them: kill-effects'
-- Ember lesson). returns { { p = copy, base = its CFrame } }
local function shell(r: Run, c: Color3, mat: Enum.Material?): { any }
	local out = {}
	local m = Instance.new("Model"); m.Name = "Shell"; m.Parent = folder
	table.insert(r.objs, m)
	for _, q in r.parts do
		local ok, cp = pcall(function() return q.part:Clone() end)
		if ok and cp then
			for _, d in cp:GetChildren() do if not d:IsA("SpecialMesh") then d:Destroy() end end
			local sp = cp:FindFirstChildOfClass("SpecialMesh")
			if sp then sp.TextureId = "" end
			if cp:IsA("MeshPart") then pcall(function() (cp :: any).TextureID = "" end) end
			cp.Anchored = true; cp.CanCollide = false; cp.CanQuery = false; cp.CanTouch = false; cp.CastShadow = false
			cp.Color = c; cp.Material = mat or Enum.Material.SmoothPlastic; cp.Transparency = 0
			cp.LocalTransparencyModifier = 0
			cp.CFrame = r.base[q]
			cp.Parent = m
			table.insert(out, { p = cp, base = r.base[q], q = q })
		end
	end
	fadeAll(r, 1)
	r.s.shellModel = m
	return out
end
-- the body's parts by name (R15 first, then R6); nil when it has none of them
local function bodyPart(r: Run, names: { string }): BasePart?
	for _, n in names do
		local p = r.m:FindFirstChild(n, true)
		if p and p:IsA("BasePart") then return p end
	end
	return nil
end

local STEP: { [string]: (Run, number, number) -> () } = {}
local LEN: { [string]: number } = {}
-- the stings: { at s, Sfx name, volume, pitch? } (recordings from the game's own library; roblox/docs/SOUNDS.md)
local STING: { [string]: { { any } } } = {}

-- ------------------------------------------------------------------ ASCENSION (Seraph): a soft shaft of light comes
-- down round the body, a pair of feathered wings opens behind its shoulders, it rises 1.5 body heights into the light,
-- and at the top it bursts into feathers under a gold halo flash
LEN.ascension = 2.1
STING.ascension = { { 0, "skin_ar_seraph_fire", 0.8 }, { 1.4, "box_bell", 1.2 } }
STEP.ascension = function(r, t, dt)
	local s = r.s
	local GOLD, WHITE = C(255, 220, 140), C(255, 246, 228)
	local BH = r.h
	if not s.init then
		s.init = true
		s.h = highlight(r, WHITE, C(255, 236, 190))
		local top, bot = r.y0 + 2.7 * BH, r.y0 - 0.1
		-- (Attachment0 at the top: the shaft fades out up there instead of running into the sky)
		s.b1 = beam(r, Vector3.new(r.centre.X, top, r.centre.Z), Vector3.new(r.centre.X, bot, r.centre.Z), TEX.glow, C(255, 236, 196), 0)
		s.b2 = beam(r, Vector3.new(r.centre.X, top, r.centre.Z), Vector3.new(r.centre.X, bot, r.centre.Z), TEX.tracer, WHITE, 0)
		s.ep = part(r, Vector3.new(r.width * 0.9, BH * 0.8, r.width * 0.9), r.cf)
		s.feathers = emitter(r, s.ep, { Texture = TEX.feather, Color = cs(WHITE), LightEmission = 0.5, LightInfluence = 0.3,
			Size = ns(0, 0.7, 1, 0.5), Transparency = ns(0, 0.05, 0.6, 0.15, 1, 1), Lifetime = NR(0.55, 0.8), Speed = NR(5, 9),
			SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -4, 0), Drag = 3, Rotation = NR(0, 360), RotSpeed = NR(-140, 140) })
		s.motes = emitter(r, s.ep, { Texture = TEX.glow, Color = cs(GOLD), LightEmission = 1, Brightness = 2,
			Size = ns(0, 0.25, 1, 0), Transparency = ns(0, 0.1, 1, 1), Lifetime = NR(0.6, 1.0), Speed = NR(2, 5),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 3, 0) })
		-- the wings: five long feathers a side fanned out from the shoulders, on a holder that rises with the body
		s.wingP = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new()) -- (at the origin: its attachments are placed by world position)
		s.wingE = {}
		for side = -1, 1, 2 do
			for i = 1, 6 do
				local a = math.rad(-78 + i * 11) -- (each feather's way, from flat outwards: the inner ones hang down)
				local L = (0.22 + 0.04 * i) * BH
				local at = Instance.new("Attachment")
				at.Parent = s.wingP
				local e = emitter(r, at, { Texture = TEX.feather, Color = cs(C(255, 244, 222)), LightEmission = 1, Brightness = 0.9,
					Size = ns(0, 0, 0.25, L * 0.5, 0.85, L * 0.5, 1, 0), Transparency = ns(0, 0.15, 0.8, 0.15, 1, 1),
					Lifetime = NR(1.15), Speed = NR(0), Rotation = NR(side * (90 - math.deg(a))),
					LockedToPart = true, ZOffset = -1 })
				table.insert(s.wingE, { e = e, at = at, side = side, a = a, L = L, i = i })
			end
			for i = 1, 5 do -- (the coverts: short feathers over the long ones' roots, so each wing is one shape)
				local a = math.rad(-40 + i * 8)
				local L = 0.17 * BH
				local at = Instance.new("Attachment")
				at.Parent = s.wingP
				local e = emitter(r, at, { Texture = TEX.feather, Color = cs(C(255, 248, 232)), LightEmission = 1, Brightness = 0.9,
					Size = ns(0, 0, 0.25, L * 0.5, 0.85, L * 0.5, 1, 0), Transparency = ns(0, 0.1, 0.8, 0.1, 1, 1),
					Lifetime = NR(1.0), Speed = NR(0), Rotation = NR(side * (90 - math.deg(a))), LockedToPart = true, ZOffset = -0.5 })
				table.insert(s.wingE, { e = e, at = at, side = side, a = a, L = L, i = i + 0.3, covert = true })
			end
		end
	end
	local lift = 1.5 * BH * smooth(seg(t, 0.5, 1.4))
	-- the shaft: in over 0.3 s, gone over 1.6-2.0
	local on = smooth(t / 0.3) * (1 - smooth(seg(t, 1.6, 2.0)))
	s.b1.Width0 = r.width * 1.3 * on; s.b1.Width1 = r.width * 1.3 * on
	s.b2.Width0 = r.width * 0.25 * on; s.b2.Width1 = r.width * 0.25 * on
	s.b1.Brightness = 1.2; s.b2.Brightness = 1.5
	s.b1.Transparency = ns(0, 1, 0.3, lerp(1, 0.55, on), 1, lerp(1, 0.4, on))
	s.b2.Transparency = ns(0, 1, 0.3, lerp(1, 0.45, on), 1, lerp(1, 0.3, on))
	-- the wings sit behind the shoulders, in the plane facing whoever's watching
	local c = facing(r.centre + Vector3.new(0, lift, 0))
	local sh = r.centre + Vector3.new(0, BH * 0.22 + lift, 0) - c.LookVector * 0.6
	for _, w in s.wingE do
		-- the leading edge rises out at 32 degrees; each feather hangs from its point on it
		local edge = c.RightVector * w.side * math.cos(math.rad(32)) + Vector3.yAxis * math.sin(math.rad(32))
		local root = sh + c.RightVector * w.side * r.width * 0.2 + edge * (w.i - 0.5) * BH * 0.125
		local dir = c.RightVector * math.cos(w.a) * w.side + Vector3.yAxis * math.sin(w.a)
		w.at.WorldPosition = root + dir * w.L * (if w.covert then 0.3 else 0.45) + (if w.covert then c.LookVector * 0.1 else Vector3.zero)
	end
	if not s.wingsOut and t >= 0.3 then s.wingsOut = true; for _, w in s.wingE do w.e:Emit(1) end end
	local h = s.h :: Highlight
	-- (fully white until it bursts at 1.3: nothing of its own colours shows through a half fade)
	h.FillTransparency = if t < 1.3 then lerp(1, 0, smooth(seg(t, 0.05, 0.3))) else 1
	h.OutlineTransparency = if t < 1.3 then lerp(1, 0.4, smooth(seg(t, 0.05, 0.3))) else 1
	moveBody(r, CFrame.new(0, lift, 0))
	fadeAll(r, if t >= 1.3 then 1 else 0)
	s.ep.CFrame = r.cf + Vector3.new(0, lift, 0)
	if t > 0.5 and t < 1.4 then pour(r, "m", s.motes, 30, dt) end
	if t > 1.3 and t < 1.45 then pour(r, "f", s.feathers, 40, dt) end
	-- the burst at the top (1.3): the body goes to feathers under a gold halo at its head: a ring of beams tilted 25
	-- degrees towards whoever's watching (it reads as a halo from any height), 0.6 body heights across, widening to 1.5x
	-- as it fades over 0.25 s
	if not s.halo and t >= 1.3 then
		s.halo = {}
		s.haloAt = Vector3.new(r.centre.X, r.y1 + lift + 0.3, r.centre.Z)
		for i = 1, 20 do
			local bm, a0, a1 = beam(r, s.haloAt, s.haloAt, TEX.tracer, C(255, 210, 122), 0.2)
			bm.Brightness = 3
			table.insert(s.halo, { bm = bm, a0 = a0, a1 = a1, i = i })
		end
		pack(r, "WF_GoldFlash", toEye(s.haloAt), 0.4, C(255, 236, 196))
		s.feathers.Speed = NR(8, 13)
		s.feathers:Emit(many(52))
		-- one soft gold bloom on the halo
		local bp = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(s.haloAt))
		emitter(r, bp, { Texture = TEX.glow, Color = cs(C(255, 214, 130)), LightEmission = 1, Brightness = 2, Size = ns(0, BH * 0.25, 1, BH * 0.45),
			Transparency = ns(0, 0.3, 1, 1), Lifetime = NR(0.15), Speed = NR(0) }):Emit(1)
	end
	if s.halo then
		local k = seg(t, 1.3, 1.55)
		local rad = BH * 0.3 * lerp(1, 1.5, smooth(k))
		local c2 = facing(s.haloAt) * CFrame.Angles(math.rad(90 - 25), 0, 0)
		for _, q in s.halo do
			local a0, a1 = (q.i - 1) / 20 * math.pi * 2, q.i / 20 * math.pi * 2
			q.a0.WorldPosition = (c2 * CFrame.new(math.cos(a0) * rad, math.sin(a0) * rad, 0)).Position
			q.a1.WorldPosition = (c2 * CFrame.new(math.cos(a1) * rad, math.sin(a1) * rad, 0)).Position
			q.bm.Transparency = NumberSequence.new(smooth(k))
		end
	end
end

-- ------------------------------------------------------------------ HELLGATE (Infernal): the body flushes red, dark
-- cracks glowing orange inside open across the floor, a wall of fire climbs round it, it chars and sinks into a dark
-- hole with a red rim, and a burst of red-black spikes marks the hole closing
LEN.hellgate = 2.0
STING.hellgate = { { 0, "crunch", 0.8 }, { 0.3, "flame_burn", 1 }, { 1.45, "skin_ar_infernal_fire", 0.85 } }
STEP.hellgate = function(r, t, dt)
	local s = r.s
	local ORANGE, DEEP, RED, CHAR = C(255, 110, 40), C(150, 34, 12), C(214, 44, 24), C(58, 42, 34)
	local BH = r.h
	if not s.init then
		s.init = true
		s.h = highlight(r, RED, ORANGE)
		-- the cracks: dark lines, and the same lines glowing orange inside them
		local grow = ns(0, BH * 0.3, 0.16, BH * 1.05, 1, BH * 1.1)
		flat(r, TEX.crack, C(36, 20, 14), grow, 1.75, 0, { Transparency = ns(0, 0, 0.8, 0, 1, 1), ZOffset = 0 }):Emit(1)
		flat(r, TEX.crack, C(255, 120, 40), grow, 1.75, 1, { Brightness = 2.5, Transparency = ns(0, 0.2, 0.8, 0.3, 1, 1), ZOffset = 0.5 }):Emit(1)
		-- the fire wall: flames up from a ring round the body
		s.ring = part(r, Vector3.new(BH * 1.3, 0.3, BH * 1.3), floorAt(r, r.y0 + 0.15))
		s.flames = emitter(r, s.ring, { Texture = TEX.flame, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
			FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Color = cs(C(255, 196, 96), DEEP), LightEmission = 0.75, Brightness = 2.5,
			Size = ns(0, 1.4, 0.5, 2.0, 1, 0.7), Transparency = ns(0, 0.1, 0.7, 0.3, 1, 1), Lifetime = NR(0.35, 0.45),
			Speed = NR(6, 9), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(3, 3), Acceleration = Vector3.new(0, 2, 0),
			Shape = Enum.ParticleEmitterShape.Cylinder, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface })
		s.embers = emitter(r, s.ring, { Texture = TEX.glow, Color = cs(C(255, 170, 80), DEEP), LightEmission = 1, Brightness = 3,
			Size = ns(0, 0.2, 1, 0), Transparency = ns(0, 0, 1, 1), Lifetime = NR(0.4, 0.6), Speed = NR(4, 10),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0, 4, 0), Drag = 1 })
	end
	-- the hole under the body (0.55-1.75): a true black disc a body height across (a thin part just over the floor), an
	-- orange glow at its rim
	if not s.hole and t >= 0.55 then
		s.hole = prop(r, Enum.PartType.Cylinder, Vector3.new(0.04, 0.1, 0.1), C(0, 0, 0))
		s.hole.Material = Enum.Material.SmoothPlastic
		s.hole.CastShadow = false
		flat(r, TEX.ring, ORANGE, ns(0, 0, 0.25, BH * 0.58, 0.85, BH * 0.58, 1, 0), 1.2, 1, { Brightness = 3, ZOffset = 1.5 }):Emit(1)
	end
	if s.hole then
		local open = smooth(seg(t, 0.55, 0.85)) * (1 - smooth(seg(t, 1.4, 1.6)))
		local d = math.max(0.05, BH * 1.0 * open)
		s.hole.Size = Vector3.new(0.04, d, d)
		s.hole.CFrame = CFrame.new(r.centre.X, r.y0 + 0.07, r.centre.Z) * CFrame.Angles(0, 0, math.pi / 2)
		s.hole.Transparency = if open < 0.02 then 1 else 0
	end
	local h = s.h :: Highlight
	-- the catch: red at once, then charred
	local char = smooth(seg(t, 0.25, 0.6))
	h.FillColor = RED:Lerp(CHAR, char)
	h.FillTransparency = lerp(1, 0.25, smooth(seg(t, 0, 0.18))) - 0.2 * char
	h.OutlineTransparency = lerp(1, 0.15, smooth(seg(t, 0, 0.18)))
	-- sinking: knee-deep by 0.95 s, the shoulders by 1.3, gone at 1.5
	local floorY = r.y0 + 0.05
	local down = (BH + 0.4) * (seg(t, 0.6, 1.5) ^ 1.4)
	moveBody(r, CFrame.new(0, -down, 0))
	for _, p in r.parts do fade(r, p, clamp01((floorY - (p.lo - down)) / math.max(0.2, p.hi - p.lo))) end
	-- the rim flames flare to about 0.8 body heights as the hole closes (1.35-1.6), then stop; none left by 1.75
	local flare = t > 1.35 and t < 1.6
	s.flames.Speed = if flare then NR(BH * 1.7, BH * 2.1) else NR(6, 9)
	if flare ~= s.flaring then -- (the flare's flames are 2.5x as big: the flipbook's flame fills only part of its frame)
		s.flaring = flare
		s.flames.Size = if flare then ns(0, BH * 0.45, 0.5, BH * 0.6, 1, BH * 0.2) else ns(0, 1.4, 0.5, 2.0, 1, 0.7)
	end
	if t > 0.3 and t < 1.6 then pour(r, "f", s.flames, if flare then 95 else 55, dt); end
	if t > 0.3 and t < 1.5 then pour(r, "e", s.embers, 16, dt) end
	if not s.flamesOff and t >= 1.75 then s.flamesOff = true; s.flames:Clear() end
	-- THE STRIKE (1.45): a plume out of the closing hole, the finisher's tallest moment: streaks 0.4-0.6 body heights
	-- long thrown 1.8-2 body heights up (black core, deep red, ember tips), black ash shards, a wide soft glow column
	-- that fades from the top down, then slow embers 1.6-1.85; all gone by 1.85
	if not s.plume and t >= 1.45 then
		local floorY0 = r.y0 + 0.1
		s.plume = part(r, Vector3.new(BH * 0.4, 0.2, BH * 0.4), floorAt(r, floorY0))
		local up = BH * 7 -- (with gravity BH*5: 1 body height up by 0.15 s, about 1.9 by 0.3 s)
		s.plumeE = emitter(r, s.plume, { Texture = TEX.spark, Color = cs(0, C(255, 138, 58), 0.25, C(122, 14, 10), 1, C(58, 8, 6)),
			LightEmission = 0.1, LightInfluence = 0, Brightness = 1, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Size = ns(0, BH * 0.28, 1, BH * 0.22), Transparency = ns(0, 0, 0.6, 0.1, 1, 1), Lifetime = NR(0.28, 0.34), Rotation = NR(90),
			Speed = NR(up * 0.9, up * 1.1), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(17, 17),
			Acceleration = Vector3.new(0, -BH * 5, 0) })
		s.plumeE:Emit(many(26))
		emitter(r, s.plume, { Texture = TEX.spark, Color = cs(C(12, 8, 7)), LightEmission = 0, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Size = ns(0, BH * 0.1, 1, BH * 0.05), Transparency = ns(0, 0, 0.8, 0.1, 1, 1), Lifetime = NR(0.3, 0.38), Speed = NR(up * 0.7, up * 0.95),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(20, 20), Acceleration = Vector3.new(0, -BH * 3, 0),
			Rotation = NR(90) }):Emit(many(12))
		-- the column: two soft beams from the floor to 1.5 body heights (a wide dim one, a narrower brighter core)
		local base = Vector3.new(r.centre.X, floorY0, r.centre.Z)
		s.col = {}
		for _, q in { { BH * 0.75, 1.2, C(122, 14, 10), 0.35 }, { BH * 0.25, 1.4, C(176, 48, 20), 0.6 } } do
			local bm, a0, a1 = beam(r, base, base + Vector3.new(0, BH * 1.5, 0), TEX.glow, q[3], q[1])
			bm.Brightness = q[2]; bm.Segments = 4; bm.LightEmission = q[4]
			table.insert(s.col, bm)
		end
		s.ash = emitter(r, s.plume, { Texture = TEX.glow, Color = cs(C(255, 160, 80), C(150, 40, 14)), LightEmission = 1, Brightness = 2.5,
			Size = ns(0, 0.16, 1, 0), Transparency = ns(0, 0, 1, 1), Lifetime = NR(0.18, 0.24), Speed = NR(3, 6),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 3, 0), Drag = 1 })
		s.ash.Shape = Enum.ParticleEmitterShape.Box
	end
	if s.plumeE and t < 1.66 then pour(r, "plumeAcc", s.plumeE, if t < 1.52 then 120 else 45, dt) end
	if s.ash and not s.ashOut and t >= 1.6 then s.ashOut = true; s.ash:Emit(many(25)) end
	if s.col then
		-- 0.25 s: full at 1.45-1.52, then fading from the top down until 1.7
		local g = seg(t, 1.5, 1.7)
		for _, bm in s.col do
			bm.Transparency = ns(0, lerp(0.4, 1, smooth(seg(g, 0.35, 1))), 0.5, lerp(0.45, 1, smooth(seg(g, 0.15, 0.8))), 1, lerp(0.6, 1, smooth(seg(g, 0, 0.5))))
		end
	end
end

-- ------------------------------------------------------------------ SPLASHDOWN (Ducky): the body pales to water blue,
-- ripples spread, a whirlpool with turning arms opens under it, it spins down the drain in a ring of foam, a splash
-- column goes up as the head goes under, and a rubber duck pops up in its place with a bounce
LEN.splashdown = 2.2
STING.splashdown = { { 0, "blub", 1 }, { 0.4, "glug", 1 }, { 1.2, "splash", 1 }, { 1.35, "squeak", 1.1 } }
STEP.splashdown = function(r, t, dt)
	local s = r.s
	local AQUA, TEALW = C(210, 236, 248), C(190, 235, 240)
	local BH = r.h
	if not s.init then
		s.init = true
		s.h = highlight(r, C(170, 215, 240), C(255, 255, 255))
		local flatCF = floorAt(r, r.y0 + 0.08) * CFrame.Angles(math.rad(90), 0, 0)
		for i = 0, 2 do task.delay(i * 0.18, function() if not r.done then ringAt(r, flatCF, AQUA, 0.6, r.width * 1.6 + i, 0.9, 0.6) end end) end
		s.ep = part(r, Vector3.new(r.width * 1.1, 0.6, r.width * 1.1), floorAt(r))
		s.bubbles = emitter(r, s.ep, { Texture = TEX.bubble, Color = cs(C(255, 244, 250)), LightEmission = 0.35, LightInfluence = 0.3,
			Size = ns(0, 0.15, 0.8, 0.32, 1, 0.05), Transparency = ns(0, 0.4, 0.15, 0, 0.9, 0.1, 1, 1), Lifetime = NR(0.3, 0.45),
			Speed = NR(2, 5), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(25, 25), Acceleration = Vector3.new(0, 2, 0), Drag = 1 })
		s.rim = part(r, Vector3.new(BH * 1.2, 0.2, BH * 1.2), floorAt(r, r.y0 + 0.1))
		s.foam = emitter(r, s.rim, { Texture = TEX.bubble, Color = cs(C(240, 250, 255)), LightEmission = 0.4, LightInfluence = 0.3,
			Size = ns(0, 0.2, 1, 0.1), Transparency = ns(0, 0.2, 1, 1), Lifetime = NR(0.35, 0.6), Speed = NR(2, 4),
			EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(10, 10), Shape = Enum.ParticleEmitterShape.Cylinder,
			ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface })
	end
	-- the whirlpool (0.3-1.65): four turning arms and a darker eye, all ours, all gone by 1.7 (no mark left)
	if not s.vortex and t >= 0.3 then
		s.vortex = true
		for i = 0, 3 do
			flat(r, TEX.arc, TEALW, ns(0, 0, 0.15, BH * 0.62, 0.8, BH * 0.62, 1, BH * 0.3), 1.35, 0.8,
				{ Rotation = NR(i * 90), RotSpeed = NR(-320), Brightness = 1.6, Transparency = ns(0, 0.2, 0.75, 0.3, 1, 1) }):Emit(1)
		end
		flat(r, TEX.glow, C(40, 80, 96), ns(0, 0, 0.2, BH * 0.35, 0.8, BH * 0.35, 1, 0), 1.35, 0,
			{ Transparency = ns(0, 0.3, 0.8, 0.35, 1, 1), ZOffset = -0.5 }):Emit(1)
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.35, smooth(seg(t, 0, 0.3)))
	h.OutlineTransparency = lerp(1, 0.3, smooth(seg(t, 0, 0.3)))
	local u = seg(t, 0.35, 1.2)
	s.ang = (s.ang or 0) + dt * lerp(2, 24, u) * (if t < 1.2 then 1 else 0)
	local down = (BH + 0.5) * (u ^ 1.6)
	local c = r.centre
	moveBody(r, CFrame.new(c.X, -down, c.Z) * CFrame.Angles(0, s.ang, 0) * CFrame.new(-c.X, 0, -c.Z))
	local floorY = r.y0 + 0.05
	for _, p in r.parts do fade(r, p, clamp01((floorY - (p.lo - down)) / math.max(0.2, p.hi - p.lo))) end
	if t > 0.1 and t < 1.2 then pour(r, "b", s.bubbles, 24, dt) end
	if t > 0.3 and t < 1.25 then pour(r, "fo", s.foam, 45, dt) end
	-- the splash: a crown of white spray about 1.2 body heights tall, 1.05-1.4 as the head goes under. The streaks die
	-- while still rising (so none lies flat at the top of its arc)
	if not s.crown and t >= 1.05 then
		s.crownP = part(r, Vector3.new(r.width * 1.0, 0.2, r.width * 1.0), floorAt(r))
		s.crown = emitter(r, s.crownP, { Texture = TEX.streak, Color = cs(C(245, 252, 255)), LightEmission = 0.8, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Size = ns(0, BH * 0.16, 1, BH * 0.08), Rotation = NR(90), Transparency = ns(0, 0, 0.7, 0.2, 1, 1), Lifetime = NR(0.3, 0.4),
			Speed = NR(BH * 4.6, BH * 5.4), EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(9, 9), Acceleration = Vector3.new(0, -BH * 7, 0) })
		s.crown:Emit(many(16))
		-- the crown sheet: a thin white wall of water round the drain flaring 12 degrees out, 0.95 body heights tall, 0.3 s
		s.sheet = {}
		for i = 1, 14 do
			local a = i / 14 * math.pi * 2
			local d = Vector3.new(math.cos(a), 0, math.sin(a))
			local base = Vector3.new(r.centre.X, r.y0 + 0.05, r.centre.Z)
			local bm, a0, a1 = beam(r, base + d * BH * 0.3, base + d * BH * 0.3, TEX.glow, C(245, 252, 255), 0.9)
			bm.Brightness = 1.4
			bm.Transparency = ns(0, 0.25, 0.7, 0.4, 1, 1)
			table.insert(s.sheet, { bm = bm, a1 = a1, d = d, base = base })
		end
		s.drops = emitter(r, s.crownP, { Texture = TEX.glow, Color = cs(AQUA), LightEmission = 0.6, Size = ns(0, 0.22, 1, 0.08),
			Transparency = ns(0, 0.1, 1, 1), Lifetime = NR(0.3, 0.45), Speed = NR(14, 22), EmissionDirection = Enum.NormalId.Top,
			SpreadAngle = Vector2.new(25, 25), Acceleration = Vector3.new(0, -50, 0) })
		ringAt(r, floorAt(r, r.y0 + 0.1) * CFrame.Angles(math.rad(90), 0, 0), C(245, 252, 255), 0.5, r.width * 2.0, 0.45, 0.8)
	end
	if s.crown and t < 1.28 then pour(r, "cr", s.crown, 140, dt); pour(r, "dr", s.drops, 50, dt) end
	if s.sheet then
		-- up to 0.95 body heights by 1.2 (flaring 12 degrees out), holding, thinning away by 1.4
		local up = smooth(seg(t, 1.05, 1.2))
		local k = seg(t, 1.2, 1.4)
		local L = BH * 0.95 * up
		for _, q in s.sheet do
			q.a1.WorldPosition = q.base + q.d * (BH * 0.3 + L * 0.21) + Vector3.new(0, L * 0.98 * (1 - 0.2 * k), 0)
			q.bm.Width0 = BH * 0.16 * (1 - k); q.bm.Width1 = BH * 0.24 * (1 - k)
			q.bm.Transparency = ns(0, 0.2 + 0.8 * k, 0.7, 0.35 + 0.65 * k, 1, 1)
		end
	end
	-- the duck: side-on (its head and beak make the shape from any angle), up at 1.3 with an overshoot, then sitting on
	-- the water bobbing; off with a pop of bubbles
	if not s.duck and t >= 1.28 then
		local YEL = C(255, 216, 74)
		local K = 1.75 -- (bright yellow, with a yellow fill so it reads as yellow under any light)
		local m = Instance.new("Model"); m.Name = "Duck"; m.Parent = folder
		table.insert(r.objs, m)
		local function piece(shape, size, col)
			local p = prop(r, shape, size * K, col); p.Parent = m
			return p
		end
		local body = piece(Enum.PartType.Ball, Vector3.new(2.1, 2.1, 2.1), YEL)
		local tail = piece(Enum.PartType.Ball, Vector3.new(0.9, 0.9, 0.9), YEL)
		local head = piece(Enum.PartType.Ball, Vector3.new(1.2, 1.2, 1.2), YEL)
		local beak = piece(Enum.PartType.Block, Vector3.new(0.5, 0.2, 0.62), C(255, 140, 40))
		local eye1 = piece(Enum.PartType.Ball, Vector3.new(0.2, 0.2, 0.2), C(30, 26, 24))
		local eye2 = piece(Enum.PartType.Ball, Vector3.new(0.2, 0.2, 0.2), C(30, 26, 24))
		s.duck = { { body, Vector3.new(0, 0, 0) }, { tail, Vector3.new(0, 0.55, 0.95) }, { head, Vector3.new(0, 1.15, -0.62) },
			{ beak, Vector3.new(0, 1.05, -1.32) }, { eye1, Vector3.new(0.42, 1.32, -0.92) }, { eye2, Vector3.new(-0.42, 1.32, -0.92) } }
		for _, q in s.duck do q[2] *= K; q[3] = q[1].Size end
		local hl = Instance.new("Highlight"); hl.Adornee = m; hl.FillColor = YEL; hl.FillTransparency = 0.55; hl.OutlineColor = C(255, 255, 240)
		hl.OutlineTransparency = 0.3; hl.DepthMode = Enum.HighlightDepthMode.Occluded; hl.Parent = folder
		table.insert(r.objs, hl)
		local lt = Instance.new("PointLight"); lt.Color = C(255, 236, 170); lt.Range = 8; lt.Brightness = 1.6; lt.Shadows = false; lt.Parent = body
		s.duckFace = facing(floorAt(r).Position) * CFrame.Angles(0, math.rad(-75), 0) -- (side-on to whoever's watching)
		s.duckR = 1.05 * K
	end
	if s.duck then
		local rest = s.duckR * 0.55 -- (sitting in the water)
		local y
		if t < 1.42 then y = lerp(-s.duckR * 2, s.duckR * 1.35, smooth(seg(t, 1.28, 1.42)))
		elseif t < 1.6 then y = lerp(s.duckR * 1.35, rest, smooth(seg(t, 1.42, 1.6)))
		else y = rest + 0.1 * math.sin((t - 1.6) * 11) end
		local sc = 1 - smooth(seg(t, 1.78, 1.92))
		local base = s.duckFace * CFrame.new(0, y, 0) * CFrame.Angles(0.06 * math.sin(t * 6), 0, 0.08 * math.sin(t * 7))
		for _, q in s.duck do
			local p = q[1] :: Part
			p.CFrame = base * CFrame.new(q[2] * sc)
			p.Size = q[3] * math.max(0.02, sc)
			p.Transparency = if sc <= 0.03 then 1 else 0
		end
		if not s.popped and t >= 1.78 then s.popped = true; s.bubbles:Emit(many(10)) end
		-- small ripples under it while it bobs
		for i, at in { 1.45, 1.62 } do
			if not s["rp" .. i] and t >= at then
				s["rp" .. i] = true
				ringAt(r, floorAt(r, r.y0 + 0.09) * CFrame.Angles(math.rad(90), 0, 0), C(225, 245, 255), 0.4, BH * 0.6, 0.45, 0.6)
			end
		end
	end
end

-- ------------------------------------------------------------------ HIGH NOON (Dust Drover): a gust of wind lines and
-- the body goes sand-coloured, a tapered dust devil turns up round it, the body is blown away from the top down in fine
-- streaks of sand, and a tumbleweed rolls through behind
LEN.highnoon = 2.0
STING.highnoon = { { 0, "ricochet", 0.9 }, { 0.2, "slide", 0.8 } }
STEP.highnoon = function(r, t, dt)
	local s = r.s
	local SAND, DUN, PALE = C(216, 180, 122), C(206, 172, 120), C(240, 226, 192)
	local BH = r.h
	if not s.init then
		s.init = true
		-- the catch: the body is a figure of sand at once (a shell: it can fade part by part with no Highlight over it)
		s.shell = shell(r, SAND)
		local hl = Instance.new("Highlight"); hl.Adornee = s.shellModel; hl.FillTransparency = 1; hl.OutlineColor = C(246, 232, 200)
		hl.OutlineTransparency = 0.35; hl.DepthMode = Enum.HighlightDepthMode.Occluded; hl.Parent = folder
		table.insert(r.objs, hl)
		s.hl = hl
		local c = facing(r.centre)
		s.wind = c.RightVector
		pack(r, "WF_WindLines", CFrame.lookAt(r.centre, r.centre + s.wind), 1.0, PALE)
		-- the gust: streaks flying through along the wind
		local g = part(r, Vector3.new(0.4, BH * 1.1, r.width * 1.4), CFrame.fromMatrix(r.centre - s.wind * 7, s.wind, Vector3.yAxis))
		emitter(r, g, { Texture = TEX.streak, Color = cs(PALE), LightEmission = 0.6, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Size = ns(0, 0.2, 1, 0.12), Transparency = ns(0, 0.2, 0.7, 0.3, 1, 1), Lifetime = NR(0.35, 0.5), Speed = NR(30, 42),
			EmissionDirection = Enum.NormalId.Right, SpreadAngle = Vector2.new(2, 2) }):Emit(many(12))
		-- the sand off the body: fine streaks blowing downwind, from a thin slab that follows the dissolving line
		s.ep = part(r, Vector3.new(0.4, 0.6, r.width), CFrame.fromMatrix(r.centre, s.wind, Vector3.yAxis))
		s.sand = emitter(r, s.ep, { Texture = TEX.streak, Color = cs(C(226, 198, 144), SAND), LightEmission = 0.5, Orientation = Enum.ParticleOrientation.VelocityParallel,
			Size = ns(0, 0.3, 1, 0.12), Transparency = ns(0, 0.1, 0.6, 0.25, 1, 1), Lifetime = NR(0.45, 0.58), Speed = NR(10, 18),
			EmissionDirection = Enum.NormalId.Right, SpreadAngle = Vector2.new(12, 12), Acceleration = Vector3.new(0, 2, 0), Drag = 1 })
		s.devil = {}
	end
	-- the dust devil (0.25-1.4): flat wind arcs spinning round the body, stacked narrow at the foot to wide at the top
	if not s.devilOn and t >= 0.25 then
		s.devilOn = true
		local right = facing(r.centre).RightVector
		local rng = Random.new(3)
		for i = 1, 14 do
			local y = math.clamp((i - 1 + rng:NextNumber(-0.2, 0.2)) / 13, 0, 1)
			local rad = BH * (0.25 + 0.45 * y) * rng:NextNumber(0.85, 1.15)
			local pos = Vector3.new(r.centre.X, r.y0 + 0.1 + y * BH * 2.0, r.centre.Z)
			local tilt = math.rad((if i % 2 == 0 then 30 else -30) + rng:NextNumber(-8, 8))
			local p = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(pos) * CFrame.fromAxisAngle(right, tilt) * CFrame.Angles(math.rad(90), 0, 0))
			local e = emitter(r, p, { Texture = TEX.arc, Color = cs(SAND), LightEmission = 0.35, LightInfluence = 0.4, Brightness = 1.4,
				Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Front, Speed = NR(0.01),
				SpreadAngle = Vector2.new(0, 0), Size = ns(0, rad * 0.5, 0.2, rad, 0.8, rad, 1, rad * 0.8),
				Transparency = ns(0, 0.45, 0.2, 0.25, 0.75, 0.3, 1, 1), Lifetime = NR(1.15), Rotation = NR(i * 47), RotSpeed = NR(-380 - rng:NextNumber(0, 200)) })
			e:Emit(1)
			local e2 = e:Clone(); e2.Rotation = NR(i * 47 + 180); e2.Parent = p; table.insert(r.emitters, e2); e2:Emit(1)
			local e3 = e:Clone(); e3.Size = ns(0, rad * 0.46, 0.2, rad * 0.93, 0.8, rad * 0.93, 1, rad * 0.75); e3.Rotation = NR(i * 47 + 90)
			e3.Parent = p; table.insert(r.emitters, e3); e3:Emit(1)
		end
		pack(r, "WF_Swirl", toEye(r.centre), 0.8, SAND)
		-- the funnel's body: a faint sand cone of soft dust up the middle
		for i = 0, 5 do
			local y = i / 5
			local cp = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new(r.centre.X, r.y0 + 0.2 + y * BH * 1.9, r.centre.Z))
			emitter(r, cp, { Texture = TEX.dust, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.Loop,
				Color = cs(SAND), LightEmission = 0.3, LightInfluence = 0.4, Size = ns(0, BH * (0.2 + 0.4 * y), 1, BH * (0.22 + 0.42 * y)),
				Transparency = ns(0, 1, 0.2, 0.72, 0.8, 0.75, 1, 1), Lifetime = NR(1.1), Speed = NR(0), RotSpeed = NR(-120, 120), Rotation = NR(0, 360) }):Emit(1)
		end
	end
	-- eroded from the top down in four slices: each slice turns to sand where it stands, with a puff of streaks
	local step = math.floor(smooth(seg(t, 0.45, 1.3)) * 4 + 0.001)
	local line = r.y1 + 0.05 - (r.y1 - r.y0 + 0.1) * step / 4
	for _, q in s.shell do
		local mid = (q.q.hi + q.q.lo) * 0.5
		q.p.Transparency = if mid > line then 1 else 0
	end
	if step > (s.step or 0) then
		s.step = step
		s.ep.CFrame = CFrame.fromMatrix(Vector3.new(r.centre.X, line + (r.y1 - r.y0) / 8, r.centre.Z), s.wind, Vector3.yAxis)
		s.sand:Emit(many(30))
	end
	s.hl.OutlineTransparency = 0.35 + 0.65 * smooth(seg(t, 0.9, 1.3))
	if t > 0.45 and t < 1.35 then pour(r, "s", s.sand, 60, dt) end
	-- the tumbleweed: a ball of dry sticks rolling through behind, 1.2-1.85
	if not s.weed and t >= 1.15 then
		s.weed = {}
		s.weedM = Instance.new("Model"); s.weedM.Name = "Weed"; s.weedM.Parent = folder
		table.insert(r.objs, s.weedM)
		local rng = Random.new(7)
		for _ = 1, 40 do
			local len = BH * rng:NextNumber(0.34, 0.48)
			local p = prop(r, Enum.PartType.Cylinder, Vector3.new(len, 0.2, 0.2), C(201, 166, 107))
			p.Parent = s.weedM
			local off = rng:NextUnitVector() * BH * rng:NextNumber(0.1, 0.24)
			local rel = CFrame.new(off) * CFrame.Angles(rng:NextNumber(0, 6.3), rng:NextNumber(0, 6.3), rng:NextNumber(0, 6.3))
			table.insert(s.weed, { p = p, rel = rel })
		end
		local whl = Instance.new("Highlight"); whl.Adornee = s.weedM; whl.FillColor = C(222, 192, 136); whl.FillTransparency = 0.45
		whl.OutlineTransparency = 1; whl.DepthMode = Enum.HighlightDepthMode.Occluded; whl.Parent = folder
		table.insert(r.objs, whl)
		s.weedHL = whl
		local back = -facing(r.centre).LookVector * BH * 0.9
		s.weedFrom = r.centre + back - s.wind * 10
		s.weedTo = r.centre + back + s.wind * 10
	end
	if s.weed then
		local k = seg(t, 1.15, 1.8)
		local pos = s.weedFrom:Lerp(s.weedTo, k)
		local c = CFrame.new(pos.X, r.y0 + BH * 0.3 + math.abs(math.sin(k * math.pi * 2)) * BH * 0.15, pos.Z) * CFrame.fromAxisAngle(s.wind:Cross(Vector3.yAxis), k * 10)
		for _, w in s.weed do
			w.p.CFrame = c * w.rel
			w.p.Transparency = smooth(seg(t, 1.8, 1.95))
		end
		s.weedHL.FillTransparency = 0.45 + 0.55 * smooth(seg(t, 1.8, 1.95))
	end
end

-- ------------------------------------------------------------------ INKFALL (Tidecrest): the body pales; one bold sumi
-- stroke is drawn across it; everything holds; the top half slides down along the stroke; both halves burst into sakura
-- petals that drift up and away
LEN.inkfall = 2.0
STING.inkfall = { { 0.12, "skin_katana_sakura_swing", 1 }, { 0.55, "skin_katana_sakura_hit", 0.9 } }
STEP.inkfall = function(r, t, dt)
	local s = r.s
	local PINK, INK = C(248, 200, 214), C(16, 14, 20)
	local BH = r.h
	if not s.init then
		s.init = true
		s.h = highlight(r, C(238, 236, 234), INK)
		-- the stroke runs through the waist seam (the upper body above it is one rigid piece), up to the right at 18 degrees
		local ut = bodyPart(r, { "UpperTorso" })
		local tor = bodyPart(r, { "Torso" })
		local waistY = if ut then ut.Position.Y - ut.Size.Y * 0.45 elseif tor then tor.Position.Y - tor.Size.Y * 0.2 else r.centre.Y
		local mid = Vector3.new(r.centre.X, waistY, r.centre.Z)
		local c = toEye(mid)
		s.cut = c * CFrame.Angles(0, 0, math.rad(18))
		s.dir = s.cut.RightVector
		s.a = mid - s.dir * BH * 0.8 + c.LookVector * 0.6
		s.b = mid + s.dir * BH * 0.8 + c.LookVector * 0.6
		local n = s.cut.UpVector
		s.top = {}
		-- (which half: by limb, so an arm hanging past the cut still goes with its shoulder; anything else by its joint,
		-- then by where it is)
		local function side(bp: BasePart, depth: number): boolean?
			local nm = bp.Name
			if nm == "Head" or nm == "UpperTorso" or nm == "Torso" or nm:find("Arm") or nm:find("Hand") then return true end
			if nm == "LowerTorso" or nm == "HumanoidRootPart" or nm:find("Leg") or nm:find("Foot") then return false end
			if depth > 4 then return nil end
			for _, j in bp:GetChildren() do
				if (j:IsA("JointInstance") or j:IsA("WeldConstraint")) and (j :: any).Part1 == bp and (j :: any).Part0 then
					return side((j :: any).Part0, depth + 1)
				end
			end
			local ac = bp.Parent
			if ac and ac:IsA("Accessory") then
				for _, w in bp:GetChildren() do
					if w:IsA("Weld") and w.Part1 and w.Part1 ~= bp then return side(w.Part1, depth + 1) end
					if w:IsA("Weld") and w.Part0 and w.Part0 ~= bp then return side(w.Part0, depth + 1) end
				end
			end
			return nil
		end
		for _, p in r.parts do
			local v = side(p.part, 0)
			if v == nil then v = (r.base[p].Position - mid):Dot(n) > 0 end
			s.top[p] = v
		end
		s.mid = mid + c.LookVector * 0.6
		-- (the petals spray from along the stroke)
		s.ep = part(r, Vector3.new(BH * 1.5, BH * 0.3, 0.4), CFrame.fromMatrix(mid, s.dir, n))
		s.petals = emitter(r, s.ep, { Texture = TEX.petal, Color = cs(C(246, 193, 207), C(229, 143, 168)), LightEmission = 0.4, LightInfluence = 0.3,
			Size = ns(0, 0.75, 1, 0.55), Squash = NumberSequence.new(0.6), Transparency = ns(0, 0, 0.75, 0.15, 1, 1), Lifetime = NR(0.55, 0.68), Speed = NR(3, 7),
			SpreadAngle = Vector2.new(180, 180), Acceleration = s.dir * 4 + Vector3.new(0, 1.5, 0), Drag = 1.8, Rotation = NR(0, 360), RotSpeed = NR(-260, 260) })
	end
	-- the stroke: drawn in 0.1 s at 0.15, held, gone by 1.25
	if not s.stroke and t >= 0.15 then
		local bm, a0, a1 = beam(r, s.a, s.a, TEX.tracer, INK, BH * 0.12)
		bm.LightEmission = 0; bm.Brightness = 1; bm.Width0 = BH * 0.03; bm.Width1 = BH * 0.11; bm.Segments = 12
		bm.CurveSize0 = BH * 0.12; bm.CurveSize1 = -BH * 0.08
		-- (a faint pale halo behind it, so the stroke still reads where it crosses a dark floor)
		local hb = Instance.new("Beam")
		hb.Attachment0 = a0; hb.Attachment1 = a1; hb.Texture = TEX.glow; hb.TextureMode = Enum.TextureMode.Stretch
		hb.FaceCamera = true; hb.LightEmission = 1; hb.LightInfluence = 0; hb.Color = ColorSequence.new(C(255, 246, 240)); hb.Brightness = 0.6
		hb.Width0 = BH * 0.12; hb.Width1 = BH * 0.3; hb.Segments = 12; hb.CurveSize0 = bm.CurveSize0; hb.CurveSize1 = bm.CurveSize1; hb.ZOffset = -0.5
		hb.Parent = bm.Parent
		s.stroke = { bm = bm, a0 = a0, a1 = a1, hb = hb }
	end
	if s.stroke then
		local k = smooth(seg(t, 0.15, 0.25))
		s.stroke.a1.WorldPosition = s.a:Lerp(s.b, k)
		local g = smooth(seg(t, 0.5, 0.68)) -- (the ink goes as the halves part: the gap and its pale edge are the cut now)
		s.stroke.bm.Transparency = ns(0, lerp(0.5, 1, g), 0.12, g, 0.8, g, 1, lerp(0.75, 1, g))
		s.stroke.hb.Transparency = ns(0, 1, 0.2, lerp(0.7, 1, g), 0.8, lerp(0.7, 1, g), 1, 1)
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.3, smooth(seg(t, 0, 0.15))) + 0.7 * smooth(seg(t, 0.95, 1.1))
	h.OutlineTransparency = lerp(1, 0.1, smooth(seg(t, 0, 0.15))) + 0.9 * smooth(seg(t, 1.0, 1.15))
	-- the cut opens (0.55-0.9): the top half slides 0.4 body heights along the stroke and turns 12 degrees about its
	-- end, leaving a clear gap with a thin pale edge; then both go
	local slide = BH * 0.6 * smooth(seg(t, 0.55, 0.95))
	local turn = math.rad(25) * smooth(seg(t, 0.55, 0.95))
	local pivot = s.a
	local axis = s.cut.LookVector
	if not r.own then
		for _, p in r.parts do
			local b = r.base[p]
			if s.top[p] then
				local rot = CFrame.fromAxisAngle(axis, turn)
				local pos = pivot + rot * (b.Position - pivot) + s.dir * slide + s.cut.UpVector * BH * 0.06 * smooth(seg(t, 0.55, 0.7)) - Vector3.new(0, BH * 0.18 * smooth(seg(t, 0.7, 0.95)), 0)
				p.part.CFrame = CFrame.new(pos) * rot * (b - b.Position)
			end
		end
	end
	-- ink on the cut (0.5-1.0): a thin black line with a soft pink glow behind it, on both faces, only across the body
	-- (0.5 body heights); the top face rides with the top half
	if not s.edge and t >= 0.5 then
		s.edge = {}
		for face = 1, 2 do
			local a, b = s.mid - s.dir * BH * 0.25, s.mid + s.dir * BH * 0.25
			local gm, g0, g1 = beam(r, a, b, TEX.glow, PINK, BH * 0.14)
			gm.Brightness = 1.4; gm.ZOffset = -0.3
			local bm, a0, a1 = beam(r, a, b, TEX.tracer, INK, BH * 0.035)
			bm.LightEmission = 0; bm.Brightness = 1
			table.insert(s.edge, { face = face, bm = bm, gm = gm, ends = { a0, a1, g0, g1 }, a = a, b = b })
		end
	end
	if s.edge then
		local v = smooth(seg(t, 0.5, 0.6)) * (1 - smooth(seg(t, 0.9, 1.0)))
		local rot = CFrame.fromAxisAngle(axis, turn)
		local function moved(x: Vector3): Vector3
			return pivot + rot * (x - pivot) + s.dir * slide + s.cut.UpVector * BH * 0.06 * smooth(seg(t, 0.55, 0.7)) - Vector3.new(0, BH * 0.18 * smooth(seg(t, 0.7, 0.95)), 0)
		end
		for _, q in s.edge do
			local a, b = q.a, q.b
			if q.face == 2 then a, b = moved(a), moved(b) end
			q.ends[1].WorldPosition = a; q.ends[2].WorldPosition = b; q.ends[3].WorldPosition = a; q.ends[4].WorldPosition = b
			q.bm.Transparency = ns(0, 1, 0.15, lerp(1, 0.05, v), 0.85, lerp(1, 0.05, v), 1, 1)
			q.gm.Transparency = NumberSequence.new(lerp(1, 0.35, v))
		end
	end
	fadeAll(r, smooth(seg(t, 0.98, 1.12)))
	if not s.burst and t >= 1.0 then s.burst = true; s.petals:Emit(many(60)) end
	if t > 1.0 and t < 1.25 then pour(r, "p", s.petals, 60, dt) end
end

-- ------------------------------------------------------------------ WARP OUT (Star Drover): the body lights teal, a thin
-- ring opens one body width behind it facing the killer, dark inside with a few stars; the body is yanked back into it,
-- stretched, past star streaks, and the ring snaps shut in a teal crackle
LEN.warpout = 1.7
STING.warpout = { { 0, "card_tp", 1 }, { 0.6, "laser_whine", 1.1 }, { 1.15, "skin_revolver_star_fire", 0.9 } }
STEP.warpout = function(r, t, dt)
	local s = r.s
	local TEAL, WHITE = C(69, 230, 214), C(235, 255, 252)
	local BH = r.h
	if not s.init then
		s.init = true
		s.h = highlight(r, C(150, 245, 232), TEAL)
		-- the ring floats one body width behind the body, its middle a body height up, facing the killer
		s.to = Vector3.new(r.centre.X, r.y0 + BH, r.centre.Z) + r.away * r.width * 1.1
		s.mouthCF = CFrame.lookAt(s.to, s.to - r.away)
		s.R = BH * 0.8
		-- the rim: 32 beams round the circle, each two chords long and overlapping its neighbours by half, so the tracer
		-- texture's faded ends never leave a gap (it reads as one ring, an ellipse from any side)
		s.rimPts = {}
		s.rim = {}
		for i = 1, 32 do
			local bm, a0, a1 = beam(r, s.to, s.to, TEX.tracer, TEAL, 0.3)
			bm.Brightness = 2.5
			local gm, g0, g1 = beam(r, s.to, s.to, TEX.glow, TEAL, 1.6) -- (a soft wide glow behind the rim)
			gm.Brightness = 1.5
			table.insert(s.rim, { bm = bm, a0 = a0, a1 = a1, gm = gm, g0 = g0, g1 = g1, i = i })
		end
		-- the dark inside: a thin black disc in the ring's own plane, sized with it
		s.disc = prop(r, Enum.PartType.Cylinder, Vector3.new(0.05, 0.1, 0.1), C(6, 22, 26))
		s.disc.Transparency = 1
		s.streakP = part(r, Vector3.new(r.width * 1.6, BH, 0.5), CFrame.lookAt(r.centre - r.away * 2.5, s.to))
		s.streaks = emitter(r, s.streakP, { Texture = TEX.streak, Color = cs(WHITE, TEAL), LightEmission = 1, Brightness = 2.5,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Size = ns(0, 0.24, 1, 0.08), Transparency = ns(0, 0, 1, 1),
			Lifetime = NR(0.25, 0.35), Speed = NR(20, 28), EmissionDirection = Enum.NormalId.Front, SpreadAngle = Vector2.new(3, 3) })
	end
	-- open 0.3-0.65, held, snapped shut 1.12-1.2
	local open = smooth(seg(t, 0.3, 0.65)) * (1 - seg(t, 1.12, 1.2))
	local rr = s.R * open
	local c = s.mouthCF
	for _, q in s.rim do
		local a0 = (q.i - 1.5) / 32 * math.pi * 2 -- (each segment two chords long: its faded ends lie under its neighbours' middles)
		local a1 = (q.i + 0.5) / 32 * math.pi * 2
		q.a0.WorldPosition = (c * CFrame.new(math.cos(a0) * rr, math.sin(a0) * rr, 0)).Position
		q.a1.WorldPosition = (c * CFrame.new(math.cos(a1) * rr, math.sin(a1) * rr, 0)).Position
		q.g0.WorldPosition = q.a0.WorldPosition; q.g1.WorldPosition = q.a1.WorldPosition
		q.bm.Width0 = 0.6 * open; q.bm.Width1 = 0.6 * open
		q.gm.Width0 = 1.6 * open; q.gm.Width1 = 1.6 * open
		q.bm.Transparency = NumberSequence.new(if open > 0.02 then 0.25 else 1) -- (two overlap everywhere: each a bit fainter)
		q.gm.Transparency = NumberSequence.new(if open > 0.02 then 0.75 else 1)
	end
	local d = rr * 2 * 0.85
	s.disc.Size = Vector3.new(0.05, math.max(0.05, d), math.max(0.05, d))
	s.disc.CFrame = c * CFrame.Angles(0, math.rad(90), 0)
	s.disc.Transparency = if open > 0.02 then 0.08 else 1
	-- a few stars just in front of the dark inside
	if not s.inside and t >= 0.3 then
		s.inside = true
		local rp = part(r, Vector3.new(s.R * 1.1, s.R * 1.1, 0.1), s.mouthCF * CFrame.new(0, 0, -0.3))
		emitter(r, rp, { Texture = TEX.sparkle, Color = cs(WHITE), LightEmission = 1, Brightness = 3, Size = ns(0, 0, 0.3, 0.3, 0.9, 0.3, 1, 0),
			Transparency = ns(0, 0.1, 1, 0.3), Lifetime = NR(0.85), Speed = NR(0), ZOffset = 0.5, Rotation = NR(0, 90) }):Emit(20)
		-- a slow teal swirl in the window
		local sw = part(r, Vector3.new(0.2, 0.2, 0.2), s.mouthCF * CFrame.new(0, 0, -0.2))
		emitter(r, sw, { Texture = TEX.arc, Color = cs(TEAL), LightEmission = 0.7, Brightness = 1.2, Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			EmissionDirection = Enum.NormalId.Front, Speed = NR(0.01), SpreadAngle = Vector2.new(0, 0), Size = ns(0, 0, 0.35, s.R * 0.6, 0.9, s.R * 0.6, 1, 0),
			Transparency = ns(0, 0.4, 0.9, 0.5, 1, 1), Lifetime = NR(0.85), Rotation = NR(0, 360), RotSpeed = NR(90) }):Emit(2)
	end
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.3, smooth(seg(t, 0, 0.25)))
	h.OutlineTransparency = lerp(1, 0.1, smooth(seg(t, 0, 0.2)))
	-- the pull (0.8-1.05): into the ring's middle, shrinking to a third and stretched towards it
	local k = smooth(seg(t, 0.8, 1.05))
	if not r.own then
		for _, p in r.parts do
			local b = r.base[p]
			local rel = b.Position - r.centre
			local along = r.away * rel:Dot(r.away)
			local side = rel - along
			local pos = r.centre:Lerp(s.to, k) + (along * lerp(1, 1.6, k) + side) * lerp(1, 0.3, k)
			p.part.CFrame = (b - b.Position) + pos
		end
	end
	fadeAll(r, smooth(seg(t, 0.92, 1.08)))
	if t > 0.65 and t < 1.1 then pour(r, "s", s.streaks, 26, dt) end
	-- the shut is the strike: a teal crackle of bolt arcs out of the closing ring
	if not s.shut and t >= 1.12 then
		s.shut = true
		local rng = Random.new()
		s.bolts = {}
		for i = 1, 5 do
			local ang = rng:NextNumber(0, math.pi * 2)
			local a = s.to
			local b = (s.mouthCF * CFrame.new(math.cos(ang) * BH * 0.9, math.sin(ang) * BH * 0.9, rng:NextNumber(-0.5, 0.5))).Position
			local bm = beam(r, a, b, TEX.tracer, C(110, 240, 222), 0.3)
			bm.Brightness = 3; bm.Segments = 8
			bm.CurveSize0 = rng:NextNumber(-1.4, 1.4); bm.CurveSize1 = rng:NextNumber(-1.4, 1.4)
			table.insert(s.bolts, bm)
		end
		local cp = part(r, Vector3.new(0.3, 0.3, 0.3), s.mouthCF)
		emitter(r, cp, { Texture = TEX.spark, Color = cs(WHITE, TEAL), LightEmission = 1, Brightness = 3,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Size = ns(0, 0.3, 1, 0.05), Transparency = ns(0, 0, 1, 1),
			Lifetime = NR(0.12, 0.22), Speed = NR(18, 30), SpreadAngle = Vector2.new(180, 180) }):Emit(many(14))
		emitter(r, cp, { Texture = TEX.glow, Color = cs(TEAL), LightEmission = 1, Brightness = 2, Size = ns(0, BH * 0.45, 1, BH * 0.1),
			Transparency = ns(0, 0.2, 1, 1), Lifetime = NR(0.18), Speed = NR(0) }):Emit(1)
	end
	if s.bolts then
		local g = smooth(seg(t, 1.2, 1.42))
		for _, bm in s.bolts do bm.Transparency = NumberSequence.new(g); bm.Width0 = 0.3 * (1 - g); bm.Width1 = 0.08 end
	end
end

-- ------------------------------------------------------------------ LANTERN LIGHT (Pumpkin Patch): the body flushes
-- orange, a pumpkin's ribs rise round it and close over it, its carved face and seams light from inside, then it swells
-- and pops into a warm cloud
LEN.lanternlight = 2.2
STING.lanternlight = { { 0, "rope_creak", 0.9 }, { 0.85, "skin_smg_pumpkin_fire", 0.7 }, { 1.7, "skin_frag_lantern_blast", 0.8 } }
STEP.lanternlight = function(r, t, dt)
	local s = r.s
	local GLOW = C(255, 196, 92)
	local BH = r.h
	local R = math.max(1.9, BH * 0.62)
	local H = BH * 1.3
	if not s.init then
		s.init = true
		s.h = highlight(r, C(255, 150, 60), C(255, 200, 120))
		s.face = facing(floorAt(r).Position)
		local fl = s.face.LookVector
		s.a0 = math.atan2(fl.Z, fl.X) -- (the ribs turned so two of them meet down the middle of the face)
		s.ribs = {}
		for i = 1, 8 do
			local p = prop(r, Enum.PartType.Block, Vector3.new(1, 1, 1), if i % 2 == 0 then C(246, 134, 42) else C(230, 116, 34))
			local m = Instance.new("SpecialMesh"); m.MeshType = Enum.MeshType.Sphere; m.Parent = p
			table.insert(s.ribs, { p = p, a = s.a0 + (i - 0.5) / 8 * math.pi * 2 })
		end
		s.stem = prop(r, Enum.PartType.Cylinder, Vector3.new(0.9, 0.5, 0.5), C(96, 84, 48))
		-- the glowing seams between the ribs (they light with the face, so it glows from every side)
		s.seams = {}
		for i = 1, 8 do
			local p = prop(r, Enum.PartType.Block, Vector3.new(0.07, H * 0.5, 0.07), GLOW, Enum.Material.Neon)
			p.Transparency = 1
			table.insert(s.seams, { p = p, a = s.a0 + i / 8 * math.pi * 2 })
		end
		-- the carved face: two triangle eyes, each on one of the two front ribs, and a wide grin with three teeth
		s.carve = {}
		local function tri(x: number, y: number, w: number, hgt: number)
			for side = -1, 1, 2 do
				local p = Instance.new("WedgePart")
				p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
				p.Material = Enum.Material.Neon; p.Color = GLOW; p.Transparency = 1
				p.Size = Vector3.new(0.12, hgt, w * 0.5)
				p.Parent = folder
				table.insert(r.objs, p)
				table.insert(s.carve, { p = p, x = x, dx = side * w * 0.25, y = y, rot = CFrame.Angles(0, math.rad(-90 * side), 0) })
			end
		end
		tri(-0.33, 0.17, 0.2 * BH, 0.2 * BH)
		tri(0.33, 0.17, 0.2 * BH, 0.2 * BH)
		local mouth = prop(r, Enum.PartType.Block, Vector3.new(R * 1.0, 0.11 * BH, 0.12), GLOW, Enum.Material.Neon)
		mouth.Transparency = 1
		table.insert(s.carve, { p = mouth, x = 0, y = -0.17, rot = CFrame.new() })
		for i, q in { { -0.22, 1 }, { 0, -1 }, { 0.22, 1 } } do -- (teeth: pumpkin-coloured blocks over the grin's edges)
			local p = prop(r, Enum.PartType.Block, Vector3.new(R * 0.16, 0.06 * BH, 0.14), C(182, 86, 26))
			table.insert(s.carve, { p = p, x = q[1], y = -0.17 + q[2] * 0.035, z = -0.05, rot = CFrame.new(), solid = true })
		end
		s.light = Instance.new("PointLight"); s.light.Color = GLOW; s.light.Range = 11; s.light.Brightness = 0; s.light.Shadows = false
		s.light.Parent = s.stem
	end
	-- the catch: an orange flush on the body while the ribs come up round it (0-0.35), closing over it by 0.8
	local h = s.h :: Highlight
	h.FillTransparency = lerp(1, 0.35, smooth(seg(t, 0, 0.2)))
	h.OutlineTransparency = lerp(1, 0.3, smooth(seg(t, 0, 0.2)))
	local rise = smooth(seg(t, 0, 0.35))
	local close = smooth(seg(t, 0.35, 0.8))
	local swell = 1 + 0.15 * smooth(seg(t, 1.7, 1.82))
	local gone = smooth(seg(t, 1.82, 1.88))
	local cy = r.y0 + H * 0.5 * rise - H * 0.55 * (1 - rise)
	for _, q in s.ribs do
		local out = lerp(R * 1.3, R * 0.55, close) * swell
		local lean = lerp(0.35, 0, close)
		local dir = Vector3.new(math.cos(q.a), 0, math.sin(q.a))
		local pos = Vector3.new(r.centre.X, cy, r.centre.Z) + dir * out
		q.p.CFrame = CFrame.lookAt(pos, pos + dir) * CFrame.Angles(-lean, 0, 0)
		q.p.Size = Vector3.new(R * 0.95, H, R * 0.95) * swell
		q.p.Transparency = gone
	end
	s.stem.CFrame = CFrame.new(r.centre.X, cy + H * 0.5 * close * swell + 0.2, r.centre.Z) * CFrame.Angles(0, 0, math.pi / 2)
	s.stem.Transparency = if close > 0.6 then gone else 1
	fadeAll(r, smooth(seg(t, 0.55, 0.75)))
	-- the face and seams: from 0.85, full by 1.1, flickering; gone with the pop
	local lit = smooth(seg(t, 0.85, 1.1)) * (1 - gone)
	local fl = lit * (0.85 + 0.15 * math.sin(t * 29))
	local fc = s.face * CFrame.new(0, cy - r.y0 - 0.05, 0)
	for _, q in s.carve do
		q.p.CFrame = fc * CFrame.new(q.x * R * 1.1 + (q.dx or 0), q.y * H, -R * 1.02 * swell + (q.z or 0)) * q.rot
		q.p.Transparency = if q.solid then (if lit > 0.05 then gone else 1) else 1 - fl
	end
	for _, q in s.seams do
		local dir = Vector3.new(math.cos(q.a), 0, math.sin(q.a))
		local pos = Vector3.new(r.centre.X, cy, r.centre.Z) + dir * R * 0.84 * swell
		q.p.CFrame = CFrame.lookAt(pos, pos + dir)
		q.p.Transparency = 1 - fl * 0.45
	end
	-- a warm flash out of the face just before the pop
	local flash = smooth(seg(t, 1.66, 1.74)) * (1 - smooth(seg(t, 1.76, 1.82)))
	s.light.Brightness = 4 * lit + 10 * flash
	if flash > 0 then for _, q in s.carve do if not q.solid then q.p.Transparency = 0 end end end
	-- the pop (1.82): a warm cloud about 1.5 body heights wide, sparks, gone by 2.2
	if not s.puff and t >= 1.82 then
		s.puff = true
		local mid = Vector3.new(r.centre.X, r.y0 + H * 0.5, r.centre.Z)
		-- (radial and rising, all of it gone within 0.3 s)
		local e = part(r, Vector3.new(BH * 0.8, BH * 0.8, BH * 0.8), CFrame.new(mid))
		emitter(r, e, { Texture = TEX.smoke, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
			Color = cs(C(220, 176, 136)), LightEmission = 0.35, LightInfluence = 0.5, Size = ns(0, BH * 0.3, 1, BH * 0.75),
			Transparency = ns(0, 0.15, 0.6, 0.35, 1, 1), Lifetime = NR(0.28, 0.36), Speed = NR(3, 7), SpreadAngle = Vector2.new(180, 180),
			Acceleration = Vector3.new(0, 10, 0), Drag = 2, Rotation = NR(0, 360) }):Emit(many(16))
		emitter(r, e, { Texture = TEX.glow, Color = cs(C(255, 180, 90), C(150, 60, 20)), LightEmission = 1, Brightness = 2.5,
			Size = ns(0, 0.22, 1, 0), Transparency = ns(0, 0, 1, 1), Lifetime = NR(0.22, 0.3), Speed = NR(10, 16),
			SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 6, 0), Drag = 2 }):Emit(many(26))
	end
end

-- ------------------------------------------------------------------ STARCHART (Triangulum): the body becomes a night-
-- blue figure, stars light on its joints one by one, gold lines draw between them, then the figure fades and the
-- constellation rises into the sky
LEN.starchart = 2.1
STING.starchart = { { 0.35, "ting", 0.5, 1.3 }, { 0.55, "ting", 0.5, 1.45 }, { 0.75, "ting", 0.5, 1.6 }, { 1.25, "skin_sniper_triangulum_cycle", 1 } }
local JOINTS = {
	{ "Head" }, { "UpperTorso", "Torso" }, { "LeftUpperArm", "Left Arm" }, { "RightUpperArm", "Right Arm" },
	{ "LeftLowerArm" }, { "RightLowerArm" }, { "LeftHand" }, { "RightHand" }, { "LowerTorso" },
	{ "LeftLowerLeg", "Left Leg" }, { "RightLowerLeg", "Right Leg" }, { "LeftFoot" }, { "RightFoot" },
}
-- (a star chart, not a stick figure: some joints are left on their own)
local LINKS = { { 1, 2 }, { 2, 3 }, { 2, 4 }, { 4, 6 }, { 6, 8 }, { 2, 9 }, { 9, 10 }, { 9, 11 }, { 10, 12 } }
local BIG = { [1] = true, [2] = true, [7] = true, [8] = true } -- (head, chest, hands: the bright ones)
STEP.starchart = function(r, t, dt)
	local s = r.s
	local STAR, NIGHT, INDIGO = C(255, 236, 190), C(27, 32, 80), C(90, 96, 200)
	local BH = r.h
	if not s.init then
		s.init = true
		s.shell = shell(r, NIGHT, Enum.Material.Neon) -- (a faint glow of its own, so it holds on a dark map)
		local hl = Instance.new("Highlight"); hl.Adornee = s.shellModel; hl.FillTransparency = 1; hl.OutlineColor = STAR
		hl.OutlineTransparency = 1; hl.DepthMode = Enum.HighlightDepthMode.Occluded; hl.Parent = folder
		table.insert(r.objs, hl)
		s.hl = hl
		-- the joints, just in front of the body (towards whoever's watching) so the stars sit on it
		local toCam = facing(r.centre).LookVector * 0.7
		s.pts = {}
		for i, names in JOINTS do
			local p = bodyPart(r, names)
			if p then
				local pos = p.Position
				if names[1] == "UpperTorso" then pos += p.CFrame.UpVector * p.Size.Y * 0.4 end
				s.pts[i] = pos + toCam
			end
		end
		s.ep = part(r, Vector3.new(0.2, 0.2, 0.2), CFrame.new())
		s.lines = {}
		s.lit = {}
		s.order = {}
		for i in s.pts do table.insert(s.order, i) end
		table.sort(s.order)
	end
	-- the figure: the shell darkens in (it is the body now), its outline lights, then it fades 0.9-1.3
	s.hl.OutlineTransparency = lerp(1, 0.35, smooth(seg(t, 0, 0.3))) + 0.65 * smooth(seg(t, 0.9, 1.3))
	local f = smooth(seg(t, 0.9, 1.3))
	for _, q in s.shell do q.p.Transparency = f end
	local rise = 1.5 * BH * smooth(seg(t, 1.2, 2.0))
	s.ep.CFrame = CFrame.new(0, rise, 0)
	-- it grows to about 1.6x as it rises, about its own middle
	local grow = lerp(1, 1.6, smooth(seg(t, 1.2, 1.8)))
	local cen = s.pts[2] or r.centre
	local function at(i: number): Vector3 return cen + (s.pts[i] - cen) * grow end
	if s.atts then for i, a in s.atts do a.Position = at(i) end end
	-- the stars, one by one 0.35-0.75 s, from the head down
	local n = #s.order
	for j, i in s.order do
		if not s.lit[i] and t >= 0.35 + (j - 1) * (0.4 / math.max(1, n - 1)) then
			s.lit[i] = true
			local a = Instance.new("Attachment"); a.Parent = s.ep; a.Position = at(i)
			s.atts = s.atts or {}
			s.atts[i] = a
			local big = if BIG[i] then 1.35 else 0.6
			local life = 1.75 - (j - 1) * 0.03
			local fadeOut = ns(0, 0, 0.75, 0, 1, 1)
			emitter(r, a, { Texture = TEX.glow, Color = cs(if BIG[i] then STAR else INDIGO), LightEmission = 1, Brightness = if BIG[i] then 1.2 else 1.5,
				Size = ns(0, 0, 0.1, if BIG[i] then BH * 0.13 else 0.55 * big, 1, if BIG[i] then BH * 0.11 else 0.45 * big), Transparency = fadeOut, Lifetime = NR(life), Speed = NR(0), LockedToPart = true, ZOffset = 1 }):Emit(1)
			emitter(r, a, { Texture = TEX.sparkle, Color = cs(STAR), LightEmission = 1, Brightness = 3,
				Size = ns(0, 0, 0.08, 0.6 * big, 0.25, 0.45 * big, 1, 0.42 * big), Transparency = fadeOut, Lifetime = NR(life), Speed = NR(0),
				Rotation = NR(0, 25), RotSpeed = NR(-12, 12), LockedToPart = true, ZOffset = 2 }):Emit(1)
		end
	end
	-- the lines, 0.6-1.0, solid and bright; they rise with the stars and fade with them
	for j, l in LINKS do
		local a, b = s.pts[l[1]] and at(l[1]), s.pts[l[2]] and at(l[2])
		if a and b then
			local k = smooth(seg(t, 0.6 + j * 0.025, 0.72 + j * 0.025))
			if k > 0 then
				local L = s.lines[j]
				if not L then
					local bm, a0, a1 = beam(r, a, a, TEX.tracer, STAR, 0.08)
					bm.Brightness = 2.2
					L = { bm = bm, a0 = a0, a1 = a1 }
					s.lines[j] = L
				end
				local lift = Vector3.new(0, rise, 0)
				L.a0.WorldPosition = a + lift
				L.a1.WorldPosition = a:Lerp(b, k) + lift
				L.bm.Transparency = NumberSequence.new(lerp(0.15, 1, smooth(seg(t, 1.8, 2.08))))
			end
		end
	end
	if not s.fin and t >= 1.25 and s.pts[2] then s.fin = true; pack(r, "WF_SparkRing", toEye(cen + Vector3.new(0, rise, 0)), 0.5, STAR) end
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
