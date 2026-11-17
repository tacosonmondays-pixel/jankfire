--!strict
-- FINISHER EFFECTS: each finisher theme's pieces (shared/Finishers.luau; roblox/docs/FINISHERS.md). client/Finisher.luau
-- runs the cut and calls a theme at its moments: impact(run, S) once when the slug lands, resolve(run, S, u, dt) every
-- frame of the last shot (u 0 -> 1). Everything here is client-only parts and particles in workspace.JankFinisherFx,
-- built from the VFX pipeline's approved sprites (roblox/assets/vfx/assets.json: no new uploads), cleared at the end or
-- on SKIP. Cheap: a handful of emitters, a few dozen parts at most, fewer particles on the LOW preset and on phones.
-- S (the stage, Finisher.luau) gives: V (the victim's root at the kill), H (where the shot lands), dir (the shot's
-- line), fwd / right (killer -> victim on the ground, and its right), side (+1 / -1, the camera's side), floorY,
-- victim = { model, root, base (its root's frame at the impact) }, and these the theme writes: victimOffset (a CFrame
-- after base), victimFade (0..1), victimTint (Color3 or nil), focusUp (studs the orbit's look rises).
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")

local FFx = {}

local TEX = { -- (approved; KillFx and Fx use the same ids)
	glow = "rbxassetid://107753175681578",
	sparkle = "rbxassetid://118739981349944",
	spark = "rbxassetid://73042129135061",
	ring = "rbxassetid://136567724057402",
	feather = "rbxassetid://92745845385867",
	petal = "rbxassetid://72396403976507",
	bubble = "rbxassetid://127426547666953",
	heart = "rbxassetid://108731430634300",
	flame = "rbxassetid://77597527828324", -- 4x4 flipbook
	smoke = "rbxassetid://97407536340250", -- 4x4 flipbook
	streak = "rbxassetid://127914373549121",
	dust = "rbxassetid://123624708348895", -- 4x4 flipbook
}
FFx.TEX = TEX
task.spawn(function()
	local list = {}
	for _, id in TEX do
		local d = Instance.new("Decal")
		d.Texture = id
		table.insert(list, d)
	end
	pcall(function() game:GetService("ContentProvider"):PreloadAsync(list) end)
end)

-- ------------------------------------------------------------------ small helpers
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
	if typeof(a[1]) == "Color3" then -- (colours only: spread evenly)
		local kp = {}
		for i, c in a do table.insert(kp, ColorSequenceKeypoint.new((i - 1) / (#a - 1), c)) end
		return ColorSequence.new(kp)
	end
	local kp = {}
	for i = 1, #a, 2 do table.insert(kp, ColorSequenceKeypoint.new(a[i], a[i + 1])) end
	return ColorSequence.new(kp)
end
local function clamp01(x: number): number return math.clamp(x, 0, 1) end
local function smooth(x: number): number x = clamp01(x); return x * x * (3 - 2 * x) end
local function lerp(a: number, b: number, t: number): number return a + (b - a) * t end
local function seg(u: number, a: number, b: number): number return clamp01((u - a) / (b - a)) end -- (u's place between a and b)
local function backOut(x: number): number -- (overshoots a little, then settles)
	x = clamp01(x)
	local c1 = 1.70158
	local c3 = c1 + 1
	return 1 + c3 * (x - 1) ^ 3 + c1 * (x - 1) ^ 2
end
FFx.smooth, FFx.lerp, FFx.seg, FFx.backOut = smooth, lerp, seg, backOut

-- the settings page's particle amount (0.25..1), lower again on a phone
local SettingsMod: any = nil
local function setting(key: string, default: any): any
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
FFx.setting = setting
local PHONE = UIS.TouchEnabled and not UIS.KeyboardEnabled
local function amount(): number
	local k = setting("gfx.particles", 1)
	k = if type(k) == "number" then math.clamp(k, 0.25, 1) else 1
	return if PHONE then k * 0.6 else k
end
local function many(n: number): number
	if n <= 1 then return n end
	return math.max(1, math.floor(n * amount() + 0.5))
end
FFx.many = many

-- ------------------------------------------------------------------ a run: everything one finisher made
export type Run = { folder: Folder, objs: { Instance }, emitters: { ParticleEmitter }, s: { [string]: any }, scale: number }

local root: Folder? = nil
local function rootFolder(): Folder
	if root and root.Parent then return root end
	local f = Instance.new("Folder")
	f.Name = "JankFinisherFx"
	f.Parent = workspace
	root = f
	return f
end

function FFx.new(): Run
	local f = Instance.new("Folder")
	f.Name = "Run"
	f.Parent = rootFolder()
	return { folder = f, objs = {}, emitters = {}, s = {}, scale = 1 }
end

function FFx.clear(r: Run)
	for _, o in r.objs do pcall(function() o:Destroy() end) end
	table.clear(r.objs)
	table.clear(r.emitters)
	pcall(function() r.folder:Destroy() end)
end

-- the slow-motion feel: every emitter's TimeScale (1 = real time)
function FFx.timeScale(r: Run, k: number)
	r.scale = k
	for _, e in r.emitters do if e.Parent then e.TimeScale = k end end
end

local function part(r: Run, size: Vector3, cf: CFrame, colour: Color3?, mat: Enum.Material?, tr: number?): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Size = size; p.CFrame = cf
	p.Color = colour or Color3.new(1, 1, 1)
	p.Material = mat or Enum.Material.SmoothPlastic
	p.Transparency = tr or 0
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = r.folder
	table.insert(r.objs, p)
	return p
end
FFx.part = part
-- a rounded piece (a sphere mesh stretched to the part's size): the chunky style's basic shape
local function blob(r: Run, size: Vector3, cf: CFrame, colour: Color3, mat: Enum.Material?, tr: number?): Part
	local p = part(r, Vector3.new(1, 1, 1), cf, colour, mat, tr)
	local m = Instance.new("SpecialMesh")
	m.MeshType = Enum.MeshType.Sphere
	m.Scale = size
	m.Parent = p
	p:SetAttribute("Base", size)
	return p
end
FFx.blob = blob
local function setBlob(p: Part, size: Vector3)
	local m = p:FindFirstChildOfClass("SpecialMesh")
	if m then m.Scale = size end
end
-- a holder for emitters at a point (an invisible part)
local function anchor(r: Run, cf: CFrame, size: Vector3?): Part
	return part(r, size or Vector3.new(0.2, 0.2, 0.2), cf, nil, nil, 1)
end
FFx.anchor = anchor

local function emitter(r: Run, at: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Rate = 0
	e.LockedToPart = false
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	e.LightEmission = 0.6
	for k, v in props do (e :: any)[k] = v end
	e.TimeScale = r.scale
	e.Parent = at
	table.insert(r.objs, e)
	table.insert(r.emitters, e)
	return e
end
FFx.emitter = emitter
local function burst(e: ParticleEmitter, n: number) e:Emit(many(n)) end
FFx.burst = burst
-- a steady stream's rate, scaled
local function rate(e: ParticleEmitter, n: number) e.Rate = n * amount() end
FFx.rate = rate

local function light(r: Run, at: BasePart, colour: Color3, range: number, bright: number): PointLight
	local l = Instance.new("PointLight")
	l.Color = colour; l.Range = range; l.Brightness = bright; l.Shadows = false
	l.Parent = at
	table.insert(r.objs, l)
	return l
end
FFx.light = light

local function highlight(r: Run, m: Model, fill: Color3, outline: Color3): Highlight
	local h = Instance.new("Highlight")
	h.Adornee = m
	h.FillColor = fill; h.OutlineColor = outline
	h.FillTransparency = 1; h.OutlineTransparency = 1
	h.DepthMode = Enum.HighlightDepthMode.Occluded
	h.Parent = r.folder
	table.insert(r.objs, h)
	return h
end
FFx.highlight = highlight

-- a flat ring that faces the camera and grows (a shock ring), out of one particle
local function ringBurst(r: Run, at: Vector3, colour: Color3, s0: number, s1: number, life: number)
	local a = anchor(r, CFrame.new(at))
	local e = emitter(r, a, { Texture = TEX.ring, Color = cs(colour), LightEmission = 1, Size = ns(0, s0, 1, s1),
		Transparency = ns(0, 0, 0.6, 0.3, 1, 1), Lifetime = NumberRange.new(life), Speed = NumberRange.new(0),
		Orientation = Enum.ParticleOrientation.FacingCamera, ZOffset = 1 })
	e:Emit(1)
end
FFx.ringBurst = ringBurst

-- ------------------------------------------------------------------ the slug: the shot, slowed down to be seen
-- a glowing core with a trail and the theme's bits shed behind it. set(pos, dir) each frame; done() lets it fade
function FFx.slug(r: Run, look: any): any
	local core = blob(r, Vector3.new(0.34, 0.34, 1.1) * (look.size or 1), CFrame.new(0, -500, 0), look.core, Enum.Material.Neon)
	local glow = anchor(r, CFrame.new(0, -500, 0))
	local g = emitter(r, glow, { Texture = TEX.glow, Color = cs(look.trail), LightEmission = 1, Size = ns(1.4 * (look.size or 1)),
		Transparency = ns(0, 0.35, 1, 1), Lifetime = NumberRange.new(0.12), Speed = NumberRange.new(0), Rate = 60 })
	local a0 = Instance.new("Attachment"); a0.Position = Vector3.new(0, 0.16, 0); a0.Parent = core
	local a1 = Instance.new("Attachment"); a1.Position = Vector3.new(0, -0.16, 0); a1.Parent = core
	local tr = Instance.new("Trail")
	tr.Attachment0 = a0; tr.Attachment1 = a1
	tr.Color = cs(look.core, look.trail)
	tr.Transparency = ns(0, 0, 1, 1)
	tr.LightEmission = 1
	tr.Lifetime = 0.35
	tr.WidthScale = ns(0, 1, 1, 0.2)
	tr.FaceCamera = true
	tr.Parent = core
	table.insert(r.objs, tr)
	local shed: ParticleEmitter? = nil
	if look.tex then
		shed = emitter(r, glow, { Texture = TEX[look.tex], Color = cs(look.shed or look.trail), LightEmission = look.shedLight or 0.5,
			Size = ns(0, look.shedSize or 0.35, 1, (look.shedSize or 0.35) * 0.6), Transparency = ns(0, 0, 0.7, 0.2, 1, 1),
			Lifetime = NumberRange.new(0.6, 1.1), Speed = NumberRange.new(0.5, 2), SpreadAngle = Vector2.new(180, 180),
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-120, 120), Drag = 2,
			Acceleration = Vector3.new(0, look.shedFall or -2, 0) })
		rate(shed, look.shedRate or 40)
	end
	local S = {}
	function S.set(pos: Vector3, dir: Vector3)
		core.CFrame = CFrame.lookAt(pos, pos + dir)
		glow.CFrame = core.CFrame
	end
	function S.done()
		g.Rate = 0
		if shed then shed.Rate = 0 end
		core.Transparency = 1
	end
	return S
end

-- ------------------------------------------------------------------ the charge: the skin's light gathering at the muzzle
-- an orb that swells, motes drawn in from all round, a light; set(u) as it builds, done() as the shot leaves
function FFx.charge(r: Run, at: Vector3, look: any): any
	local orb = blob(r, Vector3.new(0.1, 0.1, 0.1), CFrame.new(at), look.core, Enum.Material.Neon)
	local spot = anchor(r, CFrame.new(at))
	local glow = emitter(r, spot, { Texture = TEX.glow, Color = cs(look.trail), LightEmission = 1, Size = ns(0.6),
		Transparency = ns(0, 0.4, 1, 1), Lifetime = NumberRange.new(0.1), Speed = NumberRange.new(0), Rate = 50 })
	local shell = anchor(r, CFrame.new(at), Vector3.new(4.5, 4.5, 4.5))
	local motes = emitter(r, shell, { Texture = TEX.spark, Color = cs(look.core, look.trail), LightEmission = 1,
		Size = ns(0, 0.05, 0.3, 0.16, 1, 0), Lifetime = NumberRange.new(0.28, 0.32), Speed = NumberRange.new(7, 8),
		Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Orientation = Enum.ParticleOrientation.VelocityParallel })
	local l = light(r, spot, look.trail, 10, 0)
	return {
		set = function(u: number)
			local k = 1 - (1 - math.clamp(u, 0, 1)) ^ 2
			local d = 0.12 + 0.5 * k
			setBlob(orb, Vector3.new(d, d, d))
			glow.Size = ns(0.4 + 1.1 * k)
			rate(motes, 70)
			l.Brightness = 1.3 * k
		end,
		done = function()
			orb.Transparency = 1
			glow.Rate = 0
			motes.Rate = 0
			l.Brightness = 0
		end,
	}
end

-- smoke at the hit: a few soft puffs thrown back along the shot, tinted for the theme
function FFx.smoke(r: Run, at: Vector3, dir: Vector3, colour: Color3?)
	local a = anchor(r, CFrame.lookAt(at, at - dir))
	local e = emitter(r, a, { Texture = TEX.smoke, Color = cs(colour or Color3.fromRGB(150, 146, 140)), LightEmission = 0,
		Size = ns(0, 0.6, 1, 2.6), Transparency = ns(0, 0.35, 0.6, 0.6, 1, 1), Lifetime = NumberRange.new(0.7, 1),
		Speed = NumberRange.new(2.5, 5), SpreadAngle = Vector2.new(35, 35), Drag = 2.5, Rotation = NumberRange.new(0, 360),
		RotSpeed = NumberRange.new(-40, 40), EmissionDirection = Enum.NormalId.Front,
		FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot })
	burst(e, 5)
end

-- ------------------------------------------------------------------ the themes
FFx.THEMES = {} :: { [string]: any }

-- SERAPH · ASCENSION: a column of light falls on the victim, two great wings open behind them, they rise into it and
-- go to white, feathers drift down, a gold halo
FFx.THEMES.seraph = {
	slug = { core = Color3.fromRGB(255, 250, 236), trail = Color3.fromRGB(255, 205, 95), tex = "feather", shed = Color3.fromRGB(250, 246, 236),
		shedSize = 0.45, shedRate = 45, shedFall = -1.5, shedLight = 0.2 },
	flash = Color3.fromRGB(255, 236, 190), smoke = Color3.fromRGB(236, 230, 214),
	orbit = { r0 = 10, r1 = 14, h0 = 1.2, h1 = 5.5, sweep = 72, look0 = 1, look1 = 4.2, fov0 = 54, fov1 = 62 },
	sounds = { impact = { "hit", "round_end" }, resolve = { { 0.02, "reverse", 0.9 }, { 0.72, "kill", 0.8 } } },
	impact = function(r: Run, S: any)
		local a = anchor(r, CFrame.new(S.H))
		local f = emitter(r, a, { Texture = TEX.feather, Color = cs(Color3.fromRGB(250, 246, 236)), LightEmission = 0.15,
			Size = ns(0, 0.55, 1, 0.4), Transparency = ns(0, 0, 0.8, 0.2, 1, 1), Lifetime = NumberRange.new(0.9, 1.6),
			Speed = NumberRange.new(6, 14), SpreadAngle = Vector2.new(70, 70), Drag = 4, Rotation = NumberRange.new(0, 360),
			RotSpeed = NumberRange.new(-200, 200), Acceleration = Vector3.new(0, -3, 0), EmissionDirection = Enum.NormalId.Front })
		a.CFrame = CFrame.lookAt(S.H, S.H + S.dir)
		burst(f, 26)
		local s = emitter(r, a, { Texture = TEX.sparkle, Color = cs(Color3.fromRGB(255, 214, 120)), LightEmission = 1,
			Size = ns(0, 0.6, 1, 0), Lifetime = NumberRange.new(0.3, 0.6), Speed = NumberRange.new(4, 10), SpreadAngle = Vector2.new(180, 180), Drag = 3 })
		burst(s, 14)
		ringBurst(r, S.H, Color3.fromRGB(255, 220, 140), 0.5, 7, 0.35)
	end,
	resolve = function(r: Run, S: any, u: number, _dt: number)
		local st = r.s
		local V = S.V
		local floorY = S.floorY
		if not st.built then
			st.built = true
			-- the column: a wide soft shaft and a bright core, from far above down to the floor
			local h = 90
			local mid = CFrame.new(V.X, floorY + h / 2, V.Z) * CFrame.Angles(0, 0, math.rad(90))
			st.shaft = part(r, Vector3.new(h, 4.2, 4.2), mid, Color3.fromRGB(255, 232, 170), Enum.Material.Neon, 1)
			st.shaft.Shape = Enum.PartType.Cylinder
			st.core = part(r, Vector3.new(h, 1.1, 1.1), mid, Color3.fromRGB(255, 252, 240), Enum.Material.Neon, 1)
			st.core.Shape = Enum.PartType.Cylinder
			st.lamp = anchor(r, CFrame.new(V + Vector3.new(0, 4, 0)))
			st.light = light(r, st.lamp, Color3.fromRGB(255, 220, 150), 22, 0)
			-- motes rising in the column, feathers drifting down round it
			st.motes = emitter(r, st.core, { Texture = TEX.sparkle, Color = cs(Color3.fromRGB(255, 226, 150)), LightEmission = 1,
				Size = ns(0, 0, 0.3, 0.35, 1, 0), Lifetime = NumberRange.new(0.8, 1.4), Speed = NumberRange.new(0),
				Acceleration = Vector3.new(0, 9, 0), Shape = Enum.ParticleEmitterShape.Cylinder })
			st.feathers = emitter(r, anchor(r, CFrame.new(V + Vector3.new(0, 11, 0)), Vector3.new(9, 1, 9)), { Texture = TEX.feather,
				Color = cs(Color3.fromRGB(250, 246, 236)), LightEmission = 0.1, Size = ns(0, 0.5, 1, 0.42),
				Transparency = ns(0, 1, 0.15, 0, 0.8, 0, 1, 1), Lifetime = NumberRange.new(2, 2.6), Speed = NumberRange.new(0.5, 1.5),
				Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90), Acceleration = Vector3.new(0, -2.2, 0),
				EmissionDirection = Enum.NormalId.Bottom, SpreadAngle = Vector2.new(30, 30), Drag = 0.6 })
			-- the wings: five long rounded feathers a side fanning out from the upper back, white with a gold leading edge
			st.wings = {}
			for _, sd in { -1, 1 } do
				for i = 1, 5 do
					local len = ({ 6.2, 5.6, 4.9, 4.1, 3.3 })[i]
					local w = blob(r, Vector3.new(0.34, 0.95, len), CFrame.new(V), Color3.fromRGB(246, 242, 232))
					local e = blob(r, Vector3.new(0.12, 0.2, len * 0.96), CFrame.new(V), Color3.fromRGB(255, 205, 95), Enum.Material.Neon)
					table.insert(st.wings, { w = w, e = e, side = sd, i = i, len = len })
				end
			end
			st.halo = part(r, Vector3.new(2.6, 0.05, 2.6), CFrame.new(V), Color3.new(1, 1, 1), nil, 1)
			for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
				local d = Instance.new("Decal")
				d.Texture = TEX.ring; d.Face = face; d.Color3 = Color3.fromRGB(255, 214, 110); d.Transparency = 1
				d.Parent = st.halo
				table.insert(r.objs, d)
			end
			st.white = highlight(r, S.victim.model, Color3.fromRGB(255, 248, 230), Color3.fromRGB(255, 210, 110))
		end
		-- the light comes down first, then everything opens and rises; it all lets go at the end
		local inA = smooth(seg(u, 0, 0.18))
		local outA = smooth(seg(u, 0.84, 1))
		st.shaft.Transparency = 1 - 0.22 * inA * (1 - outA)
		st.core.Transparency = 1 - 0.5 * inA * (1 - outA)
		st.light.Brightness = 3.2 * inA * (1 - outA)
		rate(st.motes, if u < 0.9 then 40 else 0)
		rate(st.feathers, if u > 0.08 and u < 0.86 then 26 else 0)
		-- the victim rises into the light and goes to white
		local lift = smooth(seg(u, 0.1, 0.95)) * 5.5
		S.victimOffset = CFrame.new(0, lift, 0) * CFrame.Angles(math.rad(12 * smooth(seg(u, 0.05, 0.6))), 0, 0) -- (leaning back, face up)
		st.white.FillTransparency = 1 - 0.85 * smooth(seg(u, 0.25, 0.75))
		st.white.OutlineTransparency = 1 - 0.6 * smooth(seg(u, 0.2, 0.5)) * (1 - outA)
		S.victimFade = smooth(seg(u, 0.78, 0.94))
		S.focusUp = lift * 0.8
		-- the wings unfold from folded down to spread, behind the upper back, and rise with the body
		local back = S.victim.base * CFrame.new(0, lift + 1.1, 0.55)
		local open = backOut(seg(u, 0.1, 0.5))
		local beat = math.sin(seg(u, 0.5, 1) * math.pi * 1.2) * 0.12
		local wingT = 1 - smooth(seg(u, 0.8, 0.96))
		for _, f in st.wings do
			local fan = math.rad(lerp(-75, ({ 52, 36, 20, 4, -12 })[f.i], open) + beat * 30)
			local sweepBack = math.rad(lerp(20, 12, open))
			-- (turned so the feather's -z points out to its own side, then swept a little back, then fanned up)
			local cf = back * CFrame.new(f.side * 0.35, 0, 0) * CFrame.Angles(0, -f.side * math.rad(90), 0) * CFrame.Angles(0, -f.side * sweepBack, 0)
				* CFrame.Angles(fan, 0, 0) * CFrame.new(0, 0, -f.len / 2)
			f.w.CFrame = cf
			f.e.CFrame = cf * CFrame.new(0, 0.42, 0)
			local tr = 1 - wingT * smooth(seg(u, 0.06, 0.18))
			f.w.Transparency = tr
			f.e.Transparency = tr
			local base = Vector3.new(0.34, 0.95, f.len) * lerp(0.4, 1, open)
			setBlob(f.w, base)
			setBlob(f.e, Vector3.new(0.12, 0.2, f.len * 0.96) * lerp(0.4, 1, open))
		end
		-- the halo settles over the head
		local head = S.victim.base.Position + Vector3.new(0, lift + 2.9 + 0.6 * (1 - smooth(seg(u, 0.3, 0.6))), 0)
		st.halo.CFrame = CFrame.new(head)
		local hT = 1 - smooth(seg(u, 0.3, 0.55)) * (1 - outA)
		for _, d in st.halo:GetChildren() do if d:IsA("Decal") then d.Transparency = hT end end
		-- the end: a burst of feathers where they were
		if u >= 0.86 and not st.gone then
			st.gone = true
			local a = anchor(r, CFrame.new(S.victim.base.Position + Vector3.new(0, lift + 1, 0)), Vector3.new(2, 4, 2))
			local f = emitter(r, a, { Texture = TEX.feather, Color = cs(Color3.fromRGB(250, 246, 236)), LightEmission = 0.2,
				Size = ns(0, 0.6, 1, 0.45), Transparency = ns(0, 0, 0.8, 0.2, 1, 1), Lifetime = NumberRange.new(1, 1.6),
				Speed = NumberRange.new(3, 8), SpreadAngle = Vector2.new(180, 180), Drag = 3, Rotation = NumberRange.new(0, 360),
				RotSpeed = NumberRange.new(-150, 150), Acceleration = Vector3.new(0, -1.5, 0) })
			burst(f, 40)
			ringBurst(r, a.Position, Color3.fromRGB(255, 232, 170), 1, 12, 0.45)
		end
	end,
}

-- INFERNAL · HELLGATE: the floor cracks open in glowing lines under the victim, a pit of fire opens, flames climb out
-- and pull them down; it seals over with a last gout of fire
FFx.THEMES.infernal = {
	slug = { core = Color3.fromRGB(255, 196, 120), trail = Color3.fromRGB(255, 90, 30), tex = "spark", shed = Color3.fromRGB(255, 150, 60),
		shedSize = 0.3, shedRate = 55, shedFall = -6, shedLight = 1 },
	flash = Color3.fromRGB(255, 120, 60), smoke = Color3.fromRGB(70, 52, 46),
	orbit = { r0 = 7.5, r1 = 10.5, h0 = 1.6, h1 = 5.4, sweep = 66, look0 = 0.6, look1 = -1.2, fov0 = 54, fov1 = 62 },
	sounds = { impact = { "hit", "round_end" }, resolve = { { 0.04, "boom", 0.55 }, { 0.8, "death", 0.6 } } },
	impact = function(r: Run, S: any)
		local a = anchor(r, CFrame.lookAt(S.H, S.H + S.dir))
		local s = emitter(r, a, { Texture = TEX.spark, Color = cs(Color3.fromRGB(255, 220, 140), Color3.fromRGB(255, 90, 30)),
			LightEmission = 1, Size = ns(0, 0.5, 1, 0), Lifetime = NumberRange.new(0.3, 0.7), Speed = NumberRange.new(10, 22),
			SpreadAngle = Vector2.new(60, 60), Drag = 2, Acceleration = Vector3.new(0, -14, 0), EmissionDirection = Enum.NormalId.Front,
			Orientation = Enum.ParticleOrientation.VelocityParallel })
		burst(s, 30)
		local sm = emitter(r, a, { Texture = TEX.smoke, Color = cs(Color3.fromRGB(60, 44, 40)), LightEmission = 0, Size = ns(0, 1, 1, 3),
			Transparency = ns(0, 0.3, 1, 1), Lifetime = NumberRange.new(0.6, 0.9), Speed = NumberRange.new(2, 4), SpreadAngle = Vector2.new(40, 40),
			FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot })
		burst(sm, 4)
		ringBurst(r, S.H, Color3.fromRGB(255, 120, 50), 0.5, 6, 0.3)
	end,
	resolve = function(r: Run, S: any, u: number, _dt: number)
		local st = r.s
		local V = S.V
		local floorY = S.floorY
		local ground = Vector3.new(V.X, floorY + 0.04, V.Z)
		if not st.built then
			st.built = true
			-- the cracks: seven jagged lines out from under the feet, three pieces each
			st.cracks = {}
			local rng = Random.new(7)
			for i = 1, 7 do
				local ang = (i / 7) * math.pi * 2 + rng:NextNumber(-0.25, 0.25)
				local pts = { ground }
				local p = ground
				local total = rng:NextNumber(4.5, 7.5)
				for k = 1, 3 do
					ang += rng:NextNumber(-0.5, 0.5)
					p += Vector3.new(math.cos(ang), 0, math.sin(ang)) * (total / 3)
					table.insert(pts, p)
				end
				local pieces = {}
				for k = 1, 3 do
					local glowP = part(r, Vector3.new(0.22, 0.05, 0.1), CFrame.new(ground), Color3.fromRGB(255, 120, 40), Enum.Material.Neon)
					table.insert(pieces, { p = glowP, a = pts[k], b = pts[k + 1], w = 0.34 - k * 0.07 })
				end
				table.insert(st.cracks, pieces)
			end
			-- the pit: a dark disc with a glowing rim
			st.rim = part(r, Vector3.new(0.06, 1, 1), CFrame.new(ground) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(255, 110, 36), Enum.Material.Neon)
			st.rim.Shape = Enum.PartType.Cylinder
			st.pit = part(r, Vector3.new(0.08, 1, 1), CFrame.new(ground + Vector3.new(0, 0.02, 0)) * CFrame.Angles(0, 0, math.rad(90)), Color3.fromRGB(14, 6, 4))
			st.pit.Shape = Enum.PartType.Cylinder
			st.lamp = anchor(r, CFrame.new(ground + Vector3.new(0, 1.5, 0)))
			st.light = light(r, st.lamp, Color3.fromRGB(255, 100, 40), 18, 0)
			local fire = anchor(r, CFrame.new(ground + Vector3.new(0, 0.3, 0)), Vector3.new(3.2, 0.2, 3.2))
			st.fire = emitter(r, fire, { Texture = TEX.flame, Color = cs(Color3.fromRGB(255, 236, 190), Color3.fromRGB(255, 110, 36)),
				LightEmission = 1, Size = ns(0, 1.2, 0.5, 2.4, 1, 0.8), Transparency = ns(0, 0.1, 0.7, 0.3, 1, 1),
				Lifetime = NumberRange.new(0.45, 0.8), Speed = NumberRange.new(5, 10), SpreadAngle = Vector2.new(12, 12),
				EmissionDirection = Enum.NormalId.Top, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
				FlipbookMode = Enum.ParticleFlipbookMode.OneShot, Rotation = NumberRange.new(-15, 15) })
			st.embers = emitter(r, fire, { Texture = TEX.spark, Color = cs(Color3.fromRGB(255, 200, 120), Color3.fromRGB(255, 80, 30)),
				LightEmission = 1, Size = ns(0, 0.22, 1, 0), Lifetime = NumberRange.new(0.8, 1.4), Speed = NumberRange.new(6, 12),
				SpreadAngle = Vector2.new(25, 25), EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 2, 0),
				Orientation = Enum.ParticleOrientation.VelocityParallel, Drag = 0.8 })
			st.smoke = emitter(r, fire, { Texture = TEX.smoke, Color = cs(Color3.fromRGB(46, 34, 32)), LightEmission = 0,
				Size = ns(0, 1.5, 1, 4.5), Transparency = ns(0, 0.45, 1, 1), Lifetime = NumberRange.new(1, 1.4), Speed = NumberRange.new(3, 6),
				EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(20, 20), FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4,
				FlipbookMode = Enum.ParticleFlipbookMode.OneShot })
			st.burn = highlight(r, S.victim.model, Color3.fromRGB(40, 12, 6), Color3.fromRGB(255, 110, 36))
		end
		-- cracks race out, the pit opens, fire climbs; the victim drops in; the pit seals with a last gout
		local crackU = smooth(seg(u, 0, 0.22))
		local closeU = smooth(seg(u, 0.86, 1))
		for _, pieces in st.cracks do
			for k, c in pieces do
				local g = clamp01(crackU * 3 - (k - 1))
				local a, b = c.a, c.a:Lerp(c.b, g)
				local L = (b - a).Magnitude
				if L < 0.02 then c.p.Transparency = 1
				else
					c.p.Transparency = closeU
					c.p.Size = Vector3.new(c.w * (1 - 0.5 * closeU), 0.05, L)
					c.p.CFrame = CFrame.lookAt((a + b) / 2, b)
				end
			end
		end
		local pitR = 3.4 * smooth(seg(u, 0.08, 0.32)) * (1 - closeU)
		st.pit.Size = Vector3.new(0.08, math.max(0.05, pitR * 2), math.max(0.05, pitR * 2))
		st.rim.Size = Vector3.new(0.06, math.max(0.05, pitR * 2 + 0.5), math.max(0.05, pitR * 2 + 0.5))
		st.pit.Transparency = if pitR < 0.05 then 1 else 0
		st.rim.Transparency = if pitR < 0.05 then 1 else 0
		st.light.Brightness = 3 * smooth(seg(u, 0, 0.2)) * (1 - closeU) + (if u > 0.8 and u < 0.9 then 3 else 0)
		rate(st.fire, if u > 0.1 and u < 0.86 then 55 else 0)
		rate(st.embers, if u > 0.06 and u < 0.9 then 45 else 0)
		rate(st.smoke, if u > 0.15 and u < 0.8 then 8 else 0)
		-- the victim sinks into the pit, tipping forward, burning dark
		local sink = (smooth(seg(u, 0.32, 0.86)) ^ 1.4) * 7.5
		S.victimOffset = CFrame.new(0, -sink, 0) * CFrame.Angles(math.rad(-16 * smooth(seg(u, 0.1, 0.5))), 0, 0) -- (tipping forward)
		st.burn.FillTransparency = 1 - 0.55 * smooth(seg(u, 0.2, 0.6))
		st.burn.OutlineTransparency = 1 - 0.9 * smooth(seg(u, 0.15, 0.4))
		S.victimFade = smooth(seg(u, 0.8, 0.88))
		S.focusUp = -sink * 0.25
		if u >= 0.82 and not st.gout then
			st.gout = true
			local a = anchor(r, CFrame.new(ground + Vector3.new(0, 0.5, 0)), Vector3.new(2, 0.2, 2))
			local g = emitter(r, a, { Texture = TEX.flame, Color = cs(Color3.fromRGB(255, 240, 200), Color3.fromRGB(255, 90, 30)),
				LightEmission = 1, Size = ns(0, 2, 0.4, 4, 1, 1.2), Transparency = ns(0, 0, 0.6, 0.3, 1, 1), Lifetime = NumberRange.new(0.5, 0.8),
				Speed = NumberRange.new(14, 22), SpreadAngle = Vector2.new(10, 10), EmissionDirection = Enum.NormalId.Top,
				FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot })
			burst(g, 16)
		end
	end,
}

-- DUCKY · SPLASHDOWN: a giant rubber duck (the VIP set's: yellow, orange bill, a pink bow with a gold star) drops out
-- of the sky onto the victim, squashes on landing in a burst of soap bubbles, bobs, then pops into bubbles
FFx.THEMES.ducky = {
	slug = { core = Color3.fromRGB(255, 236, 244), trail = Color3.fromRGB(244, 154, 192), tex = "bubble", shed = Color3.fromRGB(241, 228, 234),
		shedSize = 0.5, shedRate = 30, shedFall = 1.5, shedLight = 0.2 },
	flash = Color3.fromRGB(255, 205, 225), smoke = Color3.fromRGB(246, 232, 238),
	orbit = { r0 = 12, r1 = 17, h0 = 2, h1 = 6.5, sweep = 62, look0 = 1.5, look1 = 4, fov0 = 58, fov1 = 64 },
	sounds = { impact = { "hit", "bloop" }, resolve = { { 0.0, "photoin", 0.7 }, { 0.27, "squeak", 1 }, { 0.3, "blub", 1 },
		{ 0.5, "quack", 0.9 }, { 0.84, "bigpop", 0.8 } } },
	impact = function(r: Run, S: any)
		local a = anchor(r, CFrame.lookAt(S.H, S.H + S.dir))
		local b = emitter(r, a, { Texture = TEX.bubble, Color = cs(Color3.fromRGB(241, 228, 234)), LightEmission = 0.3,
			Size = ns(0, 0.2, 0.3, 0.6, 1, 0.5), Transparency = ns(0, 0.1, 0.85, 0.2, 1, 1), Lifetime = NumberRange.new(0.6, 1.1),
			Speed = NumberRange.new(4, 9), SpreadAngle = Vector2.new(80, 80), Drag = 3, Acceleration = Vector3.new(0, 3, 0),
			EmissionDirection = Enum.NormalId.Front })
		burst(b, 20)
		local h = emitter(r, a, { Texture = TEX.heart, Color = cs(Color3.fromRGB(255, 160, 200)), LightEmission = 1, Size = ns(0, 0.5, 1, 0),
			Lifetime = NumberRange.new(0.4, 0.7), Speed = NumberRange.new(3, 7), SpreadAngle = Vector2.new(180, 180), Drag = 3 })
		burst(h, 8)
		ringBurst(r, S.H, Color3.fromRGB(247, 182, 205), 0.5, 6, 0.3)
	end,
	resolve = function(r: Run, S: any, u: number, _dt: number)
		local st = r.s
		local V = S.V
		local floorY = S.floorY
		local face = -S.fwd -- (the duck faces the killer)
		if not st.built then
			st.built = true
			-- the duck, in its own frame (y up, -z its front), studs; one Model of chunky rounded pieces
			local YEL = Color3.fromRGB(246, 208, 70)
			local SHADE = Color3.fromRGB(232, 182, 52)
			local ORA = Color3.fromRGB(240, 140, 52)
			local PINK = Color3.fromRGB(242, 122, 168)
			local GOLD = Color3.fromRGB(246, 215, 138)
			local pieces = {
				{ Vector3.new(10, 6.4, 12.5), CFrame.new(0, 3.2, 0.6), YEL }, -- body
				{ Vector3.new(4.6, 2.6, 5.5), CFrame.new(0, 5.2, 5.6) * CFrame.Angles(math.rad(35), 0, 0), YEL }, -- tail
				{ Vector3.new(6.4, 6.2, 6.2), CFrame.new(0, 8.4, -3.4), YEL }, -- head
				{ Vector3.new(4.4, 1.3, 3.4), CFrame.new(0, 7.6, -7.0), ORA }, -- bill, top
				{ Vector3.new(3.8, 0.9, 2.8), CFrame.new(0, 6.9, -6.7), ORA }, -- bill, bottom
				{ Vector3.new(1.3, 4.0, 7.5), CFrame.new(-4.9, 3.6, 0.8) * CFrame.Angles(math.rad(-10), 0, math.rad(-8)), SHADE }, -- wings
				{ Vector3.new(1.3, 4.0, 7.5), CFrame.new(4.9, 3.6, 0.8) * CFrame.Angles(math.rad(-10), 0, math.rad(8)), SHADE },
				{ Vector3.new(1.1, 1.3, 0.7), CFrame.new(-1.75, 9.3, -6.15), Color3.fromRGB(28, 24, 26) }, -- eyes
				{ Vector3.new(1.1, 1.3, 0.7), CFrame.new(1.75, 9.3, -6.15), Color3.fromRGB(28, 24, 26) },
				{ Vector3.new(0.4, 0.45, 0.3), CFrame.new(-1.55, 9.6, -6.5), Color3.new(1, 1, 1) }, -- eye lights
				{ Vector3.new(0.4, 0.45, 0.3), CFrame.new(1.95, 9.6, -6.5), Color3.new(1, 1, 1) },
				{ Vector3.new(2.6, 1.9, 1.3), CFrame.new(-1.7, 11.5, -2.4) * CFrame.Angles(0, 0, math.rad(25)), PINK }, -- bow
				{ Vector3.new(2.6, 1.9, 1.3), CFrame.new(1.7, 11.5, -2.4) * CFrame.Angles(0, 0, math.rad(-25)), PINK },
				{ Vector3.new(1.1, 1.1, 1.1), CFrame.new(0, 11.5, -2.5), GOLD, Enum.Material.Neon }, -- the bow's star clip
				{ Vector3.new(1.4, 0.9, 0.5), CFrame.new(-2.9, 7.6, -5.5), Color3.fromRGB(250, 170, 160) }, -- cheeks
				{ Vector3.new(1.4, 0.9, 0.5), CFrame.new(2.9, 7.6, -5.5), Color3.fromRGB(250, 170, 160) },
			}
			st.duck = {}
			for _, pc in pieces do
				local p = blob(r, pc[1], CFrame.new(V), pc[3], pc[4] or Enum.Material.SmoothPlastic)
				p.CastShadow = true -- (its own shadow grows on the floor as it falls: no decal)
				table.insert(st.duck, { p = p, size = pc[1], cf = pc[2] })
			end
			st.bubbles = emitter(r, anchor(r, CFrame.new(V.X, floorY + 1, V.Z), Vector3.new(14, 1, 14)), { Texture = TEX.bubble,
				Color = cs(Color3.fromRGB(241, 228, 234)), LightEmission = 0.3, Size = ns(0, 0.3, 0.2, 0.9, 1, 0.8),
				Transparency = ns(0, 0.2, 0.85, 0.25, 1, 1), Lifetime = NumberRange.new(1.2, 2), Speed = NumberRange.new(2, 5),
				EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 1.5, 0), Drag = 0.6 })
			st.lamp = anchor(r, CFrame.new(V + Vector3.new(0, 6, 0)))
			st.light = light(r, st.lamp, Color3.fromRGB(255, 200, 220), 20, 0)
		end
		-- the fall (ease in, like gravity), the squash on landing, a springy recovery, a bob, then the pop
		local LAND = 0.3
		local h
		if u < LAND then
			local k = u / LAND
			h = 38 * (1 - k * k)
		else
			h = 0
		end
		local sx, sy = 1, 1
		if u < LAND then
			sy = 1 + 0.25 * (u / LAND) -- (stretched as it falls)
			sx = 1 - 0.08 * (u / LAND)
		else
			local k = (u - LAND) / 0.5
			local spring = math.exp(-5 * k) * math.cos(k * math.pi * 3.2)
			sy = 1 - 0.32 * spring
			sx = 1 + 0.18 * spring
		end
		local popU = smooth(seg(u, 0.82, 0.93))
		local big = 1 + 0.18 * popU
		local wob = if u > LAND then math.sin((u - LAND) * 18) * math.exp(-(u - LAND) * 4) * 0.08 else 0
		local base = CFrame.lookAt(Vector3.new(V.X, floorY, V.Z), Vector3.new(V.X, floorY, V.Z) + Vector3.new(face.X, 0, face.Z))
			* CFrame.new(0, h, 0) * CFrame.Angles(0, 0, wob)
		local scale = Vector3.new(sx, sy, sx) * big
		for _, d in st.duck do
			local o = d.cf
			d.p.CFrame = base * CFrame.new(o.Position * scale) * o.Rotation
			setBlob(d.p, d.size * scale)
			d.p.Transparency = popU
		end
		st.light.Brightness = if u > LAND then 1.6 * (1 - popU) else 0
		rate(st.bubbles, if u > LAND and u < 0.9 then 30 else 0)
		if u >= LAND and not st.landed then
			st.landed = true
			local a = anchor(r, CFrame.new(V.X, floorY + 1.5, V.Z), Vector3.new(8, 1, 8))
			local b = emitter(r, a, { Texture = TEX.bubble, Color = cs(Color3.fromRGB(241, 228, 234)), LightEmission = 0.3,
				Size = ns(0, 0.4, 0.3, 1.1, 1, 0.9), Transparency = ns(0, 0.1, 0.85, 0.2, 1, 1), Lifetime = NumberRange.new(0.8, 1.5),
				Speed = NumberRange.new(8, 16), SpreadAngle = Vector2.new(80, 80), EmissionDirection = Enum.NormalId.Top, Drag = 2.5,
				Acceleration = Vector3.new(0, 2, 0) })
			burst(b, 46)
			ringBurst(r, Vector3.new(V.X, floorY + 1.2, V.Z), Color3.fromRGB(247, 182, 205), 2, 22, 0.45)
		end
		if u >= 0.84 and not st.popped then
			st.popped = true
			local a = anchor(r, CFrame.new(V.X, floorY + 6, V.Z), Vector3.new(9, 9, 9))
			local b = emitter(r, a, { Texture = TEX.bubble, Color = cs(Color3.fromRGB(241, 228, 234)), LightEmission = 0.3,
				Size = ns(0, 0.5, 0.2, 1.2, 1, 1), Transparency = ns(0, 0.1, 0.85, 0.2, 1, 1), Lifetime = NumberRange.new(0.8, 1.4),
				Speed = NumberRange.new(5, 12), SpreadAngle = Vector2.new(180, 180), Drag = 2.5 })
			burst(b, 60)
			local s = emitter(r, a, { Texture = TEX.sparkle, Color = cs(Color3.fromRGB(246, 215, 138)), LightEmission = 1, Size = ns(0, 0.8, 1, 0),
				Lifetime = NumberRange.new(0.4, 0.8), Speed = NumberRange.new(6, 14), SpreadAngle = Vector2.new(180, 180), Drag = 3 })
			burst(s, 20)
		end
		-- the victim looks up at it, then is gone under it
		S.victimOffset = CFrame.new()
		S.victimFade = if u >= LAND then 1 else 0
		S.focusUp = math.min(h * 0.1, 3) + 1.2 * smooth(seg(u, LAND, 0.5))
	end,
}

return FFx
