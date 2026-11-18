--!strict
-- BloodCrossFx: everything you see of the Blood Cross (18 Nov 2026; the owner: "blood cross looks bad compared to the web
-- version, the cross is too rectangular, I wanted it to be like cool and vfx-ish"), rebuilt from the web's own
-- public/js/bloodcross.js as energy and light: additive glow, a white-hot core, a red haze, sharp tapered shapes.
--   the bolt   a glowing dart turned along its flight (tapered Beams: a short nose, a long tail that reads as its trail),
--              a red haze and hot specks shed behind it, a red light riding with it
--   the stick  a small cross of LIGHT in whoever it hit: four tapered blades of light from the hit point (the web's
--              upright cross: the lower one long, the top and sides short), each a red haze, the cross's colour and a
--              white-hot line, round a hot point in a soft glow; it throbs faster as the fuse runs
--   the erupt  spikes burst out along the same upright cross (overshoot, settle, throb), the crossing raised over their
--              chest so the long blade runs down through them to the floor; thorns on each; light streaks off the ends
--   the pop    a red glow flash, a white-hot core for a blink, light streaks, sparks, a hanging red haze, the blast ring
--              on the floor, a short red light
--   walls      a scorch glow on the wall, a spray and a sizzle of light streaks, fizzling into a puff of haze
--   you        crossed yourself: you can't see your own chest, so your screen pulses red, then flashes
-- The owner (18 Nov, via main): "vfx looks good just make upright", and of the web's flat red cross sign: "it would look
-- better without it". So no symbol, no printed cross, no sprite of one anywhere: the upright cross is only ever drawn
-- by the light itself (tapered blades, spikes), and never equal-armed (the lower arm is 2.3x the others: an equal-armed
-- red plus is the protected Red Cross emblem). (v944 drew it as a saltire X of sprites: vfx_xblade / vfx_xcore, parked.)
-- CONTENT LINE (the account has a warning): no blood or gore on Roblox. The web's blood, drips, splats and wall stains
-- are red light, haze and sparks here. The Shadow Cross skin (bloodcross_shadow) is purple throughout (web PAL.shadow).
-- Studio photos: the workspace attribute FxTimeScale = 0 freezes all of it, like Fx.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons")) :: any

local BC = {}
local me = Players.LocalPlayer
local S = Weapons.S
local W = Weapons.list.bloodcross or {}
local H = 0.5 -- (a ParticleEmitter's Size is half the particle's width)

local TEX = {
	glow = "rbxassetid://107753175681578",
	spark = "rbxassetid://73042129135061",
	core = "rbxassetid://72229869149513", -- a Beam core: v runs across it
	shock = "rbxassetid://136567724057402", -- a ring
}
-- the web's palettes (bloodcross.js PAL): glow = the red haze, core = the white-hot bits, x = the cross, deep = its rim
local function rgb(h: number): Color3 return Color3.fromRGB(bit32.rshift(h, 16) % 256, bit32.rshift(h, 8) % 256, h % 256) end
BC.PAL = {
	blood = { core = rgb(0xffc0c8), glow = rgb(0xff1a2e), red = rgb(0xd0001a), bolt = rgb(0xff4a5c), x = rgb(0xff2a3a), deep = rgb(0x9a0010) },
	shadow = { core = rgb(0xf0d8ff), glow = rgb(0xa02bff), red = rgb(0x7414c8), bolt = rgb(0xd070ff), x = rgb(0xc860ff), deep = rgb(0x30004a) },
}
type Pal = { core: Color3, glow: Color3, red: Color3, bolt: Color3, x: Color3, deep: Color3 }
-- the shooter's palette: the Shadow Cross is purple (their "Skins" attribute, as GunSkins reads it)
function BC.palOf(who: any): Pal
	local p = if typeof(who) == "Instance" and who:IsA("Player") then who elseif type(who) == "number" then Players:GetPlayerByUserId(who) else nil
	local s = p and p:GetAttribute("Skins")
	if type(s) == "string" and string.find(s, "bloodcross=bloodcross_shadow", 1, true) then return BC.PAL.shadow :: Pal end
	return BC.PAL.blood :: Pal
end

-- ---------------------------------------------------------------- the clock (FxTimeScale freezes it in Studio)
local ts = 1
local function readTs()
	if not RunService:IsStudio() then return end
	local v = workspace:GetAttribute("FxTimeScale")
	ts = if type(v) == "number" then math.max(0, v) else 1
end
readTs()
workspace:GetAttributeChangedSignal("FxTimeScale"):Connect(readTs)

local folder = Instance.new("Folder")
folder.Name = "BloodCrossFx"
folder.Parent = workspace
local function ns(...: number): NumberSequence
	local a = { ... }
	local k = {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end
local function cs(a: Color3, b: Color3?): ColorSequence return if b then ColorSequence.new(a, b) else ColorSequence.new(a) end
local function NR(a: number, b: number?): NumberRange return NumberRange.new(a, b or a) end
local function anchor(cf: CFrame, name: string?): Part
	local p = Instance.new("Part")
	p.Name = name or "BCFx"; p.Size = Vector3.new(0.1, 0.1, 0.1); p.Transparency = 1; p.CFrame = cf
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Parent = folder
	return p
end
local function att(parent: Instance, pos: Vector3?): Attachment
	local a = Instance.new("Attachment")
	a.Parent = parent
	if pos then a.Position = pos end
	return a
end
-- every emitter we make runs on our clock
local live: { [ParticleEmitter]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local function em(parent: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Enabled = false; e.Rate = 0; e.LightInfluence = 0; e.Speed = NR(0)
	for k, v in props do (e :: any)[k] = v end
	e.TimeScale = ts
	e.Parent = parent
	live[e] = true
	return e
end
-- a tapered Beam from a to b (FaceCamera): w0 wide at a, w1 at b
local function blade(a0: Attachment, a1: Attachment, w0: number, w1: number, col: Color3, tr0: number, tr1: number, emission: number, bright: number): Beam
	local b = Instance.new("Beam")
	b.Attachment0, b.Attachment1 = a0, a1
	b.FaceCamera = true; b.Segments = 1
	b.Width0, b.Width1 = w0, w1
	b.Color = cs(col); b.Transparency = ns(0, tr0, 1, tr1)
	b.Texture = TEX.core; b.TextureMode = Enum.TextureMode.Stretch
	b.LightEmission = emission; b.LightInfluence = 0; b.Brightness = bright
	b.Parent = a0.Parent
	return b
end
local function light(parent: Instance, col: Color3, range: number, bright: number): PointLight
	local l = Instance.new("PointLight")
	l.Color, l.Range, l.Brightness, l.Shadows = col, range, bright, false
	l.Parent = parent
	return l
end

-- things that run on the clock: fn(age, step) returns true when done
local steps: { { t: number, fn: (number, number) -> boolean } } = {}
local function run(fn: (number, number) -> boolean) table.insert(steps, { t = 0, fn = fn }) end
RunService.RenderStepped:Connect(function(dt: number)
	local d = dt * ts
	for e in live do if e.Parent then e.TimeScale = ts else live[e] = nil end end
	for i = #steps, 1, -1 do
		local s = steps[i]
		s.t += d
		local ok, done = pcall(s.fn, s.t, d)
		if not ok or done then table.remove(steps, i) end
	end
end)

-- ---------------------------------------------------------------- the bolt
-- dress a projectile part (ProjClient moves it nose-first: its LookVector is the flight): a dart of tapered beams, its
-- long tail the trail, a red haze and hot specks shed behind, a red light. the part itself goes clear
function BC.bolt(part: BasePart, pal: Pal)
	part.Transparency = 1
	local nose, mid, tail = att(part, Vector3.new(0, 0, -0.55)), att(part, Vector3.zero), att(part, Vector3.new(0, 0, 4.2))
	blade(mid, nose, 0.95, 0, pal.glow, 0.55, 0.7, 1, 1.2)
	blade(mid, tail, 0.95, 0, pal.glow, 0.55, 1, 1, 1.2)
	blade(mid, nose, 0.42, 0, pal.bolt, 0, 0.1, 0.6, 1.6)
	blade(mid, tail, 0.42, 0, pal.red, 0.05, 0.9, 0.6, 1.4)
	blade(mid, nose, 0.13, 0, pal.core, 0, 0, 1, 3)
	blade(mid, tail, 0.13, 0, pal.core, 0, 1, 1, 3)
	-- (the shed haze shrinks as it falls behind: a tapering wake, not a dotted line)
	em(mid, { Texture = TEX.glow, Rate = 70, Enabled = true, LightEmission = 0.7, Brightness = 1.4, Color = cs(pal.glow, pal.deep),
		Size = ns(0, 0.55, 1, 0.15), Transparency = ns(0, 0.5, 1, 1), Lifetime = NR(0.15, 0.3), Speed = NR(0.3, 1),
		SpreadAngle = Vector2.new(180, 180), Drag = 3 })
	em(mid, { Texture = TEX.glow, Rate = 30, Enabled = true, LightEmission = 1, Brightness = 3, Color = cs(pal.core, pal.glow),
		Size = ns(0, 0.13, 1, 0), Lifetime = NR(0.15, 0.3), Speed = NR(1, 3), SpreadAngle = Vector2.new(180, 180), Drag = 2 })
	light(part, pal.glow, 7, 0.8)
end

-- ---------------------------------------------------------------- a cross of light
-- four tapered blades from one point c on a part (part space): up, down, right, left; each a red haze, the cross's
-- colour and a white-hot line (Beams). lens: { up, down, side }; ws: { short, long } widths; thorns along the arms
type Arm = { c: Vector3, tip: Attachment, d: Vector3, len: number, w: number, layers: { Beam }, thorns: { any } }
local function crossArms(part: BasePart, c: Vector3, up: Vector3, right: Vector3, lens: { number }, ws: { number }, pal: Pal, thorns: boolean): { Arm }
	local mid = att(part, c)
	local arms: { Arm } = {}
	for i, d in { up, -up, right, -right } do
		local len = if i == 1 then lens[1] elseif i == 2 then lens[2] else lens[3]
		local w = if i == 2 then ws[2] else ws[1]
		local tip = att(part, c)
		local layers = {
			blade(mid, tip, w, 0, pal.glow, 0.45, 0.8, 1, 1.4),
			blade(mid, tip, w * 0.37, 0, pal.x, 0, 0.1, 0.5, 1.6),
			blade(mid, tip, w * 0.11, 0, pal.core, 0, 0.1, 1, 3.5),
		}
		local th = {}
		if thorns then
			for j, f in (if i == 2 then { 0.3, 0.45, 0.6, 0.75 } else { 0.45, 0.7 }) do
				local side = if j % 2 == 0 then 1 else -1
				local base, tp = att(part, c), att(part, c)
				local perp = (if i <= 2 then right else up) * side
				table.insert(th, { base = base, tip = tp, f = f, dir = (d * 0.6 + perp * 0.8).Unit, l = 0.18 * lens[3] * (1 - 0.4 * f),
					b = blade(base, tp, 0.22, 0, pal.x, 0, 0.3, 0.6, 1.5) })
			end
		end
		table.insert(arms, { c = c, tip = tip, d = d, len = len, w = w, layers = layers, thorns = th })
	end
	return arms
end
-- k: length (0..1+), wk: width, glowT: the haze layer's transparency, throb: -1..1
local function placeArms(arms: { Arm }, k: number, wk: number, glowT: number, throb: number)
	for _, s in arms do
		s.tip.Position = s.c + s.d * s.len * math.max(0.001, k)
		s.layers[1].Width0 = s.w * wk * (1 + 0.15 * throb); s.layers[2].Width0 = s.w * 0.37 * wk; s.layers[3].Width0 = s.w * 0.11 * wk
		s.layers[1].Transparency = ns(0, glowT, 1, 0.85)
		for _, th in s.thorns do
			local b = s.c + s.d * s.len * k * th.f
			th.base.Position = b; th.tip.Position = b + th.dir * th.l * k
			th.b.Width0 = 0.22 * wk
		end
	end
end

local function centreOf(model: Instance?): Vector3?
	if typeof(model) ~= "Instance" then return nil end
	local r = (model :: Instance):FindFirstChild("UpperTorso") or (model :: Instance):FindFirstChild("Torso") or (model :: Instance):FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r.Position else nil
end
local function rootOf(model: Instance?): BasePart?
	if typeof(model) ~= "Instance" then return nil end
	local r = (model :: Instance):FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end

-- ---------------------------------------------------------------- you were crossed: your screen pulses, then flashes
local ov: { gui: ScreenGui?, t: number, te: number, tb: number, fuse: number, pal: Pal, on: boolean } =
	{ gui = nil, t = 0, te = -1, tb = -1, fuse = 0.6, pal = BC.PAL.blood :: Pal, on = false }
local function ovMake()
	if ov.gui and ov.gui.Parent then return end
	local pg = me:FindFirstChildOfClass("PlayerGui")
	if not pg then return end
	local g = Instance.new("ScreenGui")
	g.Name = "BloodCrossed"; g.IgnoreGuiInset = true; g.ResetOnSpawn = false; g.DisplayOrder = 40
	local flash = Instance.new("Frame")
	flash.Name = "Flash"; flash.Size = UDim2.fromScale(1, 1); flash.BorderSizePixel = 0; flash.BackgroundTransparency = 1
	flash.Parent = g
	g.Parent = pg
	ov.gui = g
end
local function ovTick(d: number)
	if not ov.on then return end
	ovMake()
	local g = ov.gui
	if not g then return end
	ov.t += d
	if ov.te >= 0 then ov.te += d end
	if ov.tb >= 0 then ov.tb += d end
	local a -- (how much red covers the screen)
	if ov.tb >= 0 then a = 0.38 * math.max(0, 1 - ov.tb / 0.45)
	elseif ov.te >= 0 then a = 0.22
	else local k = math.min(1, ov.t / ov.fuse); a = (0.04 + 0.1 * k) * math.abs(math.sin(ov.t * (8 + 16 * k))) end
	local fl = g:FindFirstChild("Flash") :: Frame
	fl.BackgroundColor3 = ov.pal.glow
	fl.BackgroundTransparency = 1 - a
	if ov.tb > 0.5 or ov.t > ov.fuse + 3 then ov.on = false; fl.BackgroundTransparency = 1 end
end

-- ---------------------------------------------------------------- marks: stick, erupt, pop
type Mark = { host: Attachment, glow: ParticleEmitter, hot: ParticleEmitter, arms: { Arm }, pal: Pal, size: number,
	t: number, te: number, tb: number, fuse: number, model: Instance?, spikes: { Arm }?, sp: Part?, raise: number? }
local marks: { Mark } = {}
local function newMark(model: Instance?, at: Vector3, pal: Pal, thin: boolean)
	local r = rootOf(model)
	local size = (if thin then 0.7 else 1)
	local part: BasePart = r or anchor(CFrame.new(at))
	local c = part.CFrame:PointToObjectSpace(at)
	-- (the cross's plane faces where it came from: out of them through the hit point)
	local out = if r then at - r.Position else (workspace.CurrentCamera :: Camera).CFrame.Position - at
	local n = Vector3.new(out.X, 0, out.Z)
	n = if n.Magnitude > 1e-3 then n.Unit else -Vector3.zAxis
	local upL = part.CFrame:VectorToObjectSpace(Vector3.yAxis)
	local rightL = part.CFrame:VectorToObjectSpace(n:Cross(Vector3.yAxis).Unit)
	local arms = crossArms(part, c, upL, rightL, { 0.62 * size, 1.45 * size, 0.62 * size }, { 0.75 * size, 0.85 * size }, pal, false)
	local host = att(part, c)
	local g = em(host, { Texture = TEX.glow, LightEmission = 1, Brightness = 1.5, Color = cs(pal.glow), LockedToPart = true, Lifetime = NR(30),
		Size = NumberSequence.new(2.6 * size * H), Transparency = NumberSequence.new(0.55) })
	local hot = em(host, { Texture = TEX.glow, LightEmission = 1, Brightness = 3, Color = cs(pal.core), LockedToPart = true, Lifetime = NR(30),
		Size = NumberSequence.new(0.5 * size * H), Transparency = NumberSequence.new(0), ZOffset = 2 })
	g:Emit(1); hot:Emit(1)
	local mk: Mark = { host = host, glow = g, hot = hot, arms = arms, pal = pal, size = size, t = 0, te = -1, tb = -1,
		fuse = (W.fuse or 0.6), model = model }
	table.insert(marks, mk)
	placeArms(arms, 1, 1, 0.45, 0)
	-- a spray of light where it went in (the web's spurt, as sparks: no blood)
	local sp = em(host, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 3,
		Color = cs(pal.core, pal.glow), Size = ns(0, 0.35, 1, 0.08), Lifetime = NR(0.15, 0.3), Speed = NR(10, 22),
		SpreadAngle = Vector2.new(60, 60), Drag = 4 })
	sp:Emit(10)
	local own = if r then nil else part
	run(function(t: number, d: number): boolean
		if mk.te >= 0 then mk.te += d end
		if mk.tb >= 0 then mk.tb += d end
		mk.t = t
		if not host.Parent then return true end
		if mk.tb < 0 then
			-- stuck: it throbs faster as the fuse runs; bigger once the spikes are out
			local k = math.min(1, t / mk.fuse)
			local beat = math.abs(math.sin(t * (7 + 18 * k)))
			local sc = 1 + 0.22 * beat * (0.4 + k) + (if mk.te >= 0 then 0.3 else 0)
			placeArms(arms, sc, sc, 0.45 - 0.15 * k * beat, beat)
			mk.glow.Size = NumberSequence.new(size * (2.4 + 0.9 * k * beat + (if mk.te >= 0 then 0.9 else 0)) * H)
			mk.glow.Transparency = NumberSequence.new(0.6 - 0.25 * k * beat - (if mk.te >= 0 then 0.15 else 0))
			mk.hot.Size = NumberSequence.new(size * (0.5 + 0.25 * beat) * H)
		else
			local k = math.min(1, mk.tb / 0.45)
			local sc = 1.3 * (1 - k)
			placeArms(arms, sc, sc, 0.6, 0)
			mk.glow.Size = NumberSequence.new(math.max(0.001, size * 2.8 * (1 - k) * H)); mk.hot.Size = NumberSequence.new(math.max(0.001, size * 0.6 * (1 - k) * H))
		end
		-- the spikes: burst out (overshoot, settle), throb, then thin away with the pop
		if mk.te >= 0 and mk.spikes then
			local e = mk.te
			local kk = if e < 0.06 then (e / 0.06) * 1.2 elseif e < 0.13 then 1.2 - ((e - 0.06) / 0.07) * 0.2 else 1
			local w = 0.3 + 0.7 * math.min(1, e / 0.06)
			local fade = if mk.tb >= 0 then math.min(1, mk.tb / 0.45) else 0
			placeArms(mk.spikes, kk * (1 + 0.25 * fade), w * (1 - fade), 0.45 + 0.4 * fade, math.sin(t * 40))
			if mk.sp and model then local c2 = centreOf(model); if c2 then mk.sp.CFrame = CFrame.new(c2 + Vector3.yAxis * (mk.raise or 0)) end end
		end
		if (mk.tb >= 0 and mk.tb >= 0.5) or t > mk.fuse + 4 then
			-- (everything it put on their body: the blades, their attachments, the shared crossing point)
			local midA = arms[1].layers[1].Attachment0
			for _, a in arms do
				for _, b in a.layers do b:Destroy() end
				for _, th in a.thorns do th.b:Destroy(); th.base:Destroy(); th.tip:Destroy() end
				a.tip:Destroy()
			end
			if midA then midA:Destroy() end
			host:Destroy()
			if own then own:Destroy() end
			if mk.sp then mk.sp:Destroy() end
			local i = table.find(marks, mk); if i then table.remove(marks, i) end
			return true
		end
		return false
	end)
	return mk
end
local function markOf(model: Instance?): Mark?
	for i = #marks, 1, -1 do if marks[i].model == model and marks[i].tb < 0 then return marks[i] end end
	return nil
end

-- the erupt: the cross bursting out of them, in the plane facing where the shot came from. its crossing is raised half
-- the way from their chest to the floor above the chest, so the long lower blade runs down through them to just over the
-- floor; the top and side arms 0.45 of it (never equal-armed). k: 0.7 for a thin shot
local downParams = RaycastParams.new()
downParams.FilterType = Enum.RaycastFilterType.Exclude
local function erupt(mk: Mark, at: Vector3, thin: boolean)
	if mk.te >= 0 then return end
	mk.te = 0
	local r = rootOf(mk.model)
	local out = if r then (mk.host.WorldPosition - r.Position) else (workspace.CurrentCamera :: Camera).CFrame.Position - at
	local n = Vector3.new(out.X, 0, out.Z)
	n = if n.Magnitude > 1e-3 then n.Unit else -Vector3.zAxis
	local right = n:Cross(Vector3.yAxis).Unit
	local skip: { Instance } = { folder }
	if typeof(mk.model) == "Instance" then table.insert(skip, mk.model :: Instance) end
	downParams.FilterDescendantsInstances = skip
	local hit = workspace:Raycast(at, Vector3.new(0, -8 * S, 0), downParams)
	local fl = math.clamp(if hit then at.Y - hit.Position.Y else 4, 2, 6)
	local k = if thin then 0.7 else 1
	local raise = 0.5 * fl
	local Ld = (fl + raise - 0.25) * k
	local Ls = 0.45 * Ld
	local host = anchor(CFrame.new(at + Vector3.yAxis * raise), "BCSpikes")
	local arms = crossArms(host, Vector3.zero, Vector3.yAxis, right, { Ls, Ld, Ls }, { 1.5, 1.7 }, mk.pal, true)
	mk.sp = host; mk.spikes = arms; mk.raise = raise
	placeArms(arms, 0.01, 0.3, 0.45, 0)
	-- light streaks thrown off all four ends
	for _, s in arms do
		local e = att(host, s.d * s.len)
		local st = em(e, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 3,
			Color = cs(mk.pal.core, mk.pal.glow), Size = ns(0, 0.45, 1, 0.1), Lifetime = NR(0.15, 0.3), Speed = NR(15, 35),
			SpreadAngle = Vector2.new(20, 20), Drag = 3 })
		e.WorldCFrame = CFrame.lookAt(e.WorldPosition, e.WorldPosition + s.d) * CFrame.Angles(-math.pi / 2, 0, 0)
		st:Emit(8)
	end
end

local floorParams = RaycastParams.new()
floorParams.FilterType = Enum.RaycastFilterType.Exclude
local function pop(at: Vector3, pal: Pal, thin: boolean)
	local k = if thin then 0.6 else 1
	local host = anchor(CFrame.new(at), "BCPop")
	local a = att(host)
	-- the red glow (grows 1.2 -> 6 m and fades), the white-hot core for a blink
	em(a, { Texture = TEX.glow, LightEmission = 1, Brightness = 1.6, Color = cs(pal.glow), Lifetime = NR(0.55),
		Size = ns(0, 1.2 * S * H * k, 0.4, 4.5 * S * H * k, 1, 6 * S * H * k), Transparency = ns(0, 0.35, 0.5, 0.7, 1, 1), ZOffset = 0 }):Emit(1)
	em(a, { Texture = TEX.glow, LightEmission = 1, Brightness = 3, Color = cs(pal.core), Lifetime = NR(0.14),
		Size = ns(0, 0.4 * S * H * k, 1, 1.8 * S * H * k), Transparency = ns(0, 0, 1, 1), ZOffset = 2 }):Emit(1)
	-- a few long thin streaks bursting out (the critic: a harder edge to the flash)
	em(a, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 4,
		Color = cs(pal.core, pal.glow), Size = ns(0, 1.2 * k, 1, 0.25 * k), Lifetime = NR(0.12, 0.2), Speed = NR(55 * k, 80 * k),
		SpreadAngle = Vector2.new(180, 180), Drag = 6 }):Emit(5)
	-- light sparks flung out (the web's glowing droplets, as light), a few white-hot
	em(a, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 3,
		Color = cs(pal.core, pal.glow), Size = ns(0, 0.7 * k, 1, 0.15), Lifetime = NR(0.25, 0.55), Speed = NR(18 * k, 40 * k),
		SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -25, 0), Drag = 2.5 }):Emit(math.floor(36 * k))
	em(a, { Texture = TEX.glow, LightEmission = 1, Brightness = 2.5, Color = cs(pal.core, pal.glow), Size = ns(0, 0.22 * k, 1, 0),
		Lifetime = NR(0.3, 0.6), Speed = NR(10, 26), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -18, 0), Drag = 2 }):Emit(math.floor(18 * k))
	-- a red haze that hangs a moment
	em(a, { Texture = TEX.glow, LightEmission = 0.35, Brightness = 1.2, Color = cs(pal.glow, pal.deep), Size = ns(0, 1.2 * k, 1, 2.2 * k),
		Transparency = ns(0, 0.55, 0.4, 0.7, 1, 1), Lifetime = NR(0.7, 1.2), Speed = NR(1, 4), SpreadAngle = Vector2.new(180, 180), Drag = 2.5 }):Emit(math.floor(12 * k))
	-- the blast ring on the floor
	if not thin then
		floorParams.FilterDescendantsInstances = { folder, me.Character :: any }
		local hit = workspace:Raycast(at, Vector3.new(0, -4 * S, 0), floorParams)
		local fy = if hit then hit.Position.Y + 0.08 else at.Y - 2.5
		local ra = att(host); ra.WorldPosition = Vector3.new(at.X, fy, at.Z)
		local blastR = (W.blastR or 3 * S)
		em(ra, { Texture = TEX.shock, Orientation = Enum.ParticleOrientation.VelocityPerpendicular, LightEmission = 1, Brightness = 2.5,
			Color = cs(pal.glow), Lifetime = NR(0.32), Speed = NR(0.01), EmissionDirection = Enum.NormalId.Top,
			Size = ns(0, 0.3 * H, 0.5, blastR * 0.9 * H, 1, blastR * H), Transparency = ns(0, 0.05, 0.6, 0.4, 1, 1) }):Emit(1)
	end
	-- (a red light for a moment: at 4 over 22 studs a frozen photo showed the whole room red; 1.6 over 14)
	local l = light(host, pal.glow, 14 * k, 1.6)
	run(function(t: number): boolean
		l.Brightness = 1.6 * math.max(0, 1 - t / 0.3)
		if t > 1.5 then host:Destroy(); return true end
		return false
	end)
end

-- ---------------------------------------------------------------- walls: a scorch glow and a sizzle of light
-- no symbol on the wall (the owner: the web's flat red cross sign "would look better without it"): a soft round glow
-- flat on the wall that fades, a spray of light streaks off it, a sizzle, then a puff of haze
local function wallX(at: Vector3, n: Vector3, pal: Pal)
	local nn = if n.Magnitude > 0.5 then n.Unit else Vector3.yAxis
	local up = if math.abs(nn.Y) < 0.9 then Vector3.yAxis else ((workspace.CurrentCamera :: Camera).CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
	local p = at + nn * 0.06
	local face = anchor(CFrame.lookAt(p, p + nn, up), "BCWall")
	local SZ = 3.2
	face.Size = Vector3.new(SZ, SZ, 0.05)
	local sg = Instance.new("SurfaceGui")
	sg.Face = Enum.NormalId.Front; sg.LightInfluence = 0; sg.Brightness = 1.6; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	sg.PixelsPerStud = 40; sg.ZOffset = 1
	local scorch = Instance.new("ImageLabel")
	scorch.Size = UDim2.fromScale(1, 1); scorch.BackgroundTransparency = 1; scorch.Image = TEX.glow; scorch.ImageColor3 = pal.glow
	scorch.Parent = sg
	local hotspot = Instance.new("ImageLabel")
	hotspot.AnchorPoint = Vector2.new(0.5, 0.5); hotspot.Position = UDim2.fromScale(0.5, 0.5); hotspot.Size = UDim2.fromScale(0.35, 0.35)
	hotspot.BackgroundTransparency = 1; hotspot.Image = TEX.glow; hotspot.ImageColor3 = pal.core
	hotspot.Parent = sg
	sg.Parent = face
	local a = att(face, Vector3.new(0, 0, -0.1))
	local sizzle = em(a, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 3,
		Color = cs(pal.core, pal.glow), Size = ns(0, 0.25, 1, 0.05), Lifetime = NR(0.15, 0.3), Speed = NR(6, 14),
		SpreadAngle = Vector2.new(70, 70), EmissionDirection = Enum.NormalId.Front, Drag = 3, Rate = 40 })
	-- (it went in: a spray of light streaks off the wall)
	local sp = em(a, { Texture = TEX.spark, Orientation = Enum.ParticleOrientation.VelocityParallel, LightEmission = 1, Brightness = 3,
		Color = cs(pal.core, pal.glow), Size = ns(0, 0.45, 1, 0.08), Lifetime = NR(0.15, 0.3), Speed = NR(12, 26),
		SpreadAngle = Vector2.new(55, 55), EmissionDirection = Enum.NormalId.Front, Drag = 4 })
	sp:Emit(12)
	local l = light(face, pal.glow, 8, 1.2)
	local puffed = false
	run(function(t: number): boolean
		local s = if t < 0.06 then t / 0.06 * 1.2 elseif t < 0.7 then 1 + 0.08 * math.sin(t * 25) else math.max(0, 1 - (t - 0.7) / 0.3)
		scorch.ImageTransparency = 1 - 0.85 * s; hotspot.ImageTransparency = 1 - math.min(1, s * 1.1)
		hotspot.Size = UDim2.fromScale(0.35 * (0.8 + 0.2 * s), 0.35 * (0.8 + 0.2 * s))
		l.Brightness = 1.2 * s
		sizzle.Enabled = t < 0.95
		if t >= 1 and not puffed then
			puffed = true
			-- the fizzle: a puff of red haze and a last spray of light
			em(a, { Texture = TEX.glow, LightEmission = 0.4, Brightness = 1.2, Color = cs(pal.glow, pal.deep), Size = ns(0, 0.6, 1, 1.6),
				Transparency = ns(0, 0.5, 1, 1), Lifetime = NR(0.5, 0.9), Speed = NR(1.5, 4), SpreadAngle = Vector2.new(60, 60),
				EmissionDirection = Enum.NormalId.Front, Drag = 2 }):Emit(10)
			sp:Emit(8)
		end
		if t > 2 then face:Destroy(); return true end
		return false
	end)
end

-- ---------------------------------------------------------------- the server's events (ProjClient's "bcross")
-- f: { st = "stick" | "erupt" | "boom" | "wall" | "refund", model, p, n, thin }; pal: the shooter's (ProjClient knows it
-- from the bolt's id); a mark remembers its own for the erupt and the pop
function BC.event(f: any, pal: Pal?)
	local st = f.st
	local model = f.model
	local mine = typeof(model) == "Instance" and model == me.Character
	if st == "stick" then
		local p = pal or BC.PAL.blood :: Pal
		local at = if typeof(f.p) == "Vector3" then f.p else centreOf(model)
		if mine then
			-- (nothing is drawn at your own chest: the screen keeps the palette for the burst and the pop)
			ov.on = true; ov.t = 0; ov.te = -1; ov.tb = -1; ov.fuse = W.fuse or 0.6; ov.pal = p
			return
		end
		if at then newMark(model, at, p, f.thin == true) end
	elseif st == "erupt" then
		if mine then ov.te = 0; return end
		local mk = markOf(model)
		local at = if typeof(f.p) == "Vector3" then f.p else centreOf(model)
		if not mk and at then mk = newMark(model, at, pal or BC.PAL.blood :: Pal, f.thin == true); (mk :: Mark).t = (mk :: Mark).fuse end
		if mk and at then erupt(mk :: Mark, at, f.thin == true) end
	elseif st == "boom" then
		local at = if typeof(f.p) == "Vector3" then f.p else centreOf(model)
		local mk = markOf(model)
		local p = if mk then mk.pal else (if mine then ov.pal else pal or BC.PAL.blood :: Pal)
		if mk then mk.tb = 0 end
		if mine then ov.tb = 0 end
		if at then pop(at, p, f.thin == true) end
	elseif st == "wall" then
		if typeof(f.p) == "Vector3" then wallX(f.p, if typeof(f.n) == "Vector3" then f.n else Vector3.yAxis, pal or BC.PAL.blood :: Pal) end
	end
end
RunService.RenderStepped:Connect(function(dt: number) ovTick(dt * ts) end)

return BC
