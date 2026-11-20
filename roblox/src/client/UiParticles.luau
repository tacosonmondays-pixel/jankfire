--!strict
-- UiParticles: particles on the screen, inside a GUI Frame (20 Nov 2026; main for the owner, from a "particle 2D test"
-- reference: thick 2D fire, smoke and embers rising along the bottom of a screen. Roblox has no GUI particles; this is
-- our own code, the KIND of look, not anyone's effect). An emitter spawns recycled ImageLabels in its frame:
--   texture, cell (a flipbook cell's size in pixels on the sheet), frames + cols (the sheet's layout), fps (0 = hold
--   one random frame, nil = play the cells over the particle's life once)
--   rate (particles a second while enabled) or bursts (emit(n)); life {min, max} seconds
--   size: { {t, share of the frame's height}, ... } over life; colour: { {t, Color3}, ... }; alpha: { {t, transparency}, ... }
--   area: where they're born, {x0, y0, x1, y1} in the frame's scale (default the bottom edge); speed {min, max} in frame
--   heights a second; dir (degrees, 0 = up, 90 = right) and spread (degrees either side); accel (frame heights / s^2,
--   Vector2, y up); drag; sway (sideways wobble, frame heights); rot {min, max}, spin {min, max} (degrees / s); z
-- Cheap: one shared RenderStepped connection that exists only while something is alive; at most MAX_LIVE particles on
-- screen and MAX_SPAWN born a frame; rates and bursts follow the settings' particle slider (Fx.density).
-- A world-space pack emitter can be read as a spec too (UiParticles.fromEmitter): its EmitCount / EmitDelay /
-- EmitDuration attributes then drive play(), the same rules as VfxEmit.
local RunService = game:GetService("RunService")

local UiParticles = {}

local MAX_LIVE = 360
local MAX_SPAWN = 40

local Fx: any = nil
do
	local m = script.Parent:FindFirstChild("Fx")
	if m and m:IsA("ModuleScript") then
		local ok, F = pcall(require, m)
		if ok then Fx = F end
	end
end
local function density(): number
	local d = if Fx then Fx.density else nil
	return if type(d) == "number" then math.clamp(d, 0, 2) else 1
end

export type Spec = {
	texture: string, cell: Vector2?, frames: number?, cols: number?, fps: number?,
	rate: number?, life: { number }, size: { { number } }, colour: { { any } }?, alpha: { { number } }?,
	area: { number }?, speed: { number }?, dir: number?, spread: number?, accel: Vector2?, drag: number?, sway: number?,
	rot: { number }?, spin: { number }?, z: number?,
}
type P = { im: ImageLabel, e: any, t: number, life: number, x: number, y: number, vx: number, vy: number, rot: number,
	spin: number, seed: number, frame: number }
type Em = { frame: GuiObject, spec: Spec, on: boolean, acc: number, alive: number, dead: boolean }

local parts: { P } = {}
local ems: { Em } = {}
local spare: { ImageLabel } = {}
local conn: RBXScriptConnection? = nil

-- a curve { {t, v}, ... } read at u (0..1): numbers or Color3s, linear between keys
local function curve(c: { { any } }?, u: number, d: any): any
	if not c or #c == 0 then return d end
	if u <= c[1][1] then return c[1][2] end
	for i = 2, #c do
		local a, b = c[i - 1], c[i]
		if u <= b[1] then
			local k = (u - a[1]) / math.max(b[1] - a[1], 1e-4)
			if typeof(a[2]) == "Color3" then return (a[2] :: Color3):Lerp(b[2], k) end
			return a[2] + (b[2] - a[2]) * k
		end
	end
	return c[#c][2]
end
local function rnd(r: { number }?, d: number): number
	if not r then return d end
	local lo = r[1]
	local hi = r[2] or lo
	return lo + math.random() * (hi - lo)
end

local function newLabel(): ImageLabel
	local im = table.remove(spare)
	if im then return im end
	local l = Instance.new("ImageLabel")
	l.BackgroundTransparency = 1; l.AnchorPoint = Vector2.new(0.5, 0.5); l.BorderSizePixel = 0
	l.ScaleType = Enum.ScaleType.Stretch
	return l
end
local function drop(p: P)
	p.im.Visible = false
	p.im.Parent = nil
	if #spare < MAX_LIVE then table.insert(spare, p.im) else p.im:Destroy() end
end

local step: (dt: number) -> ()
local function wake()
	if not conn then conn = RunService.RenderStepped:Connect(function(dt) step(dt) end) end
end

local function spawn(E: Em, n: number)
	local s = E.spec
	local fr = E.frame
	for _ = 1, n do
		if #parts >= MAX_LIVE then return end
		local a = s.area or { 0, 1, 1, 1 }
		local im = newLabel()
		im.Image = s.texture
		local cell = s.cell
		local frames = s.frames or 1
		local f = 0
		if cell then
			im.ImageRectSize = cell
			if s.fps ~= nil then f = math.random(0, frames - 1) end -- (held or looping: a random frame to start from)
		else
			im.ImageRectSize = Vector2.zero
		end
		im.ZIndex = s.z or 1
		im.Visible = true
		im.Parent = fr
		local dir = math.rad((s.dir or 0) + (math.random() * 2 - 1) * (s.spread or 0))
		local sp = rnd(s.speed, 0)
		table.insert(parts, { im = im, e = E, t = 0, life = rnd(s.life, 1),
			x = a[1] + math.random() * (a[3] - a[1]), y = a[2] + math.random() * (a[4] - a[2]),
			vx = math.sin(dir) * sp, vy = math.cos(dir) * sp, rot = rnd(s.rot, 0), spin = rnd(s.spin, 0),
			seed = math.random() * 100, frame = f })
		E.alive += 1
	end
	wake()
end

step = function(dt: number)
	local born = 0
	for _, E in ems do
		if E.on and not E.dead and E.frame.Parent and E.frame.Visible then
			E.acc += (E.spec.rate or 0) * density() * dt
			local n = math.floor(E.acc)
			if n > 0 then
				E.acc -= n
				n = math.min(n, MAX_SPAWN - born)
				if n > 0 then spawn(E, n); born += n end
			end
		end
	end
	for i = #parts, 1, -1 do
		local p = parts[i]
		local s: Spec = p.e.spec
		p.t += dt
		local u = p.t / p.life
		if u >= 1 or not p.e.frame.Parent then
			drop(p); p.e.alive -= 1
			parts[i] = parts[#parts]; parts[#parts] = nil
			continue
		end
		local acc = s.accel or Vector2.zero
		p.vx += acc.X * dt; p.vy += acc.Y * dt
		local drag = s.drag or 0
		if drag > 0 then local k = math.exp(-drag * dt); p.vx *= k; p.vy *= k end
		local H = p.e.frame.AbsoluteSize.Y
		local W = math.max(p.e.frame.AbsoluteSize.X, 1)
		-- (speeds are in frame heights: the x step is scaled to the frame's width)
		p.x += p.vx * dt * H / W
		p.y -= p.vy * dt
		local sway = (s.sway or 0) * math.sin(p.t * 2.3 + p.seed) * H / W
		local sz = curve(s.size, u, 0.05) * H
		p.rot += p.spin * dt
		local im = p.im
		im.Position = UDim2.fromScale(p.x + sway, p.y)
		im.Size = UDim2.fromOffset(sz, sz)
		im.Rotation = p.rot
		im.ImageColor3 = curve(s.colour, u, Color3.new(1, 1, 1))
		im.ImageTransparency = curve(s.alpha, u, 0)
		local cell = s.cell
		if cell then
			local frames = s.frames or 1
			local cols = s.cols or frames
			local f = if s.fps == 0 then p.frame
				elseif s.fps then (p.frame + math.floor(p.t * (s.fps :: number))) % frames
				else math.min(frames - 1, math.floor(u * frames))
			im.ImageRectOffset = Vector2.new((f % cols) * cell.X, (f // cols) * cell.Y)
		end
	end
	-- (asleep when nothing is alive and nothing is emitting)
	if #parts == 0 then
		local any = false
		for _, E in ems do if E.on and not E.dead then any = true; break end end
		if not any and conn then (conn :: RBXScriptConnection):Disconnect(); conn = nil end
	end
end

-- an emitter in a frame. :emit(n) bursts; :enable(on) runs its rate; :stop() stops spawning (the live ones finish);
-- :destroy() clears it at once
function UiParticles.new(frame: GuiObject, spec: Spec): any
	local E: Em = { frame = frame, spec = spec, on = false, acc = 0, alive = 0, dead = false }
	table.insert(ems, E)
	local api = {}
	function api.emit(_: any, n: number) spawn(E, math.max(1, math.floor(n * density() + 0.5))) end
	function api.enable(_: any, on: boolean) E.on = on; if on then wake() end end
	function api.stop(_: any) E.on = false end
	function api.destroy(_: any)
		E.dead = true; E.on = false
		for i = #parts, 1, -1 do
			if parts[i].e == E then drop(parts[i]); parts[i] = parts[#parts]; parts[#parts] = nil end
		end
		local k = table.find(ems, E)
		if k then table.remove(ems, k) end
	end
	return api
end

-- a pack's world-space emitter read as a screen spec (studs become frame heights through pxPerStud / the frame's
-- height); play(frame, emitter) then fires it by its EmitCount / EmitDelay / EmitDuration attributes
function UiParticles.fromEmitter(pe: ParticleEmitter, studsPerHeight: number): Spec
	local function seq(ns: NumberSequence, k: number): { { number } }
		local out = {}
		for _, kp in ns.Keypoints do table.insert(out, { kp.Time, kp.Value * k }) end
		return out
	end
	local cols, frames = 1, 1
	local lay = pe.FlipbookLayout
	if lay == Enum.ParticleFlipbookLayout.Grid2x2 then cols, frames = 2, 4
	elseif lay == Enum.ParticleFlipbookLayout.Grid4x4 then cols, frames = 4, 16
	elseif lay == Enum.ParticleFlipbookLayout.Grid8x8 then cols, frames = 8, 64 end
	local col = {}
	for _, kp in pe.Color.Keypoints do table.insert(col, { kp.Time, kp.Value }) end
	local k = 2 / studsPerHeight -- (a particle's Size is half its width)
	local acc = pe.Acceleration
	return {
		texture = pe.Texture, cell = if frames > 1 then Vector2.new(1024 / cols, 1024 / cols) else nil, frames = frames, cols = cols,
		fps = if pe.FlipbookMode == Enum.ParticleFlipbookMode.Random then 0 else nil,
		rate = pe.Rate, life = { pe.Lifetime.Min, pe.Lifetime.Max }, size = seq(pe.Size, k), colour = col,
		alpha = seq(pe.Transparency, 1), speed = { pe.Speed.Min / studsPerHeight, pe.Speed.Max / studsPerHeight },
		dir = 0, spread = pe.SpreadAngle.X, accel = Vector2.new(acc.X, acc.Y) / studsPerHeight, drag = pe.Drag,
		rot = { pe.Rotation.Min, pe.Rotation.Max }, spin = { pe.RotSpeed.Min, pe.RotSpeed.Max }, z = 2,
	}
end
function UiParticles.play(frame: GuiObject, pe: ParticleEmitter, studsPerHeight: number): any
	local em = UiParticles.new(frame, UiParticles.fromEmitter(pe, studsPerHeight))
	local delay = pe:GetAttribute("EmitDelay")
	local dur = pe:GetAttribute("EmitDuration")
	local cnt = pe:GetAttribute("EmitCount")
	task.delay(if type(delay) == "number" then delay else 0, function()
		if type(dur) == "number" and dur > 0 then
			em:enable(true)
			task.delay(dur, function() em:stop() end)
		else
			em:emit(if type(cnt) == "number" then cnt else 1)
		end
	end)
	return em
end

-- ---- presets (quiet palette: one warm accent)
local TEX = {
	flame = "rbxassetid://77597527828324", -- a flame tongue licking up, 16 frames (4x4, 256 px), white for a tint
	tongues = "rbxassetid://76464949862705", -- groups of flame tongues, 64 frames looping (8x8, 128 px; the RANKED fire)
	-- the Combat VFX pack's fire flipbook (coldd Development, credited; its Flame Pillar's body), 64 frames (8x8)
	packFire = "rbxassetid://17406297832",
	smoke = "rbxassetid://97407536340250", -- soft smoke, 16 frames (4x4, 256 px)
	glow = "rbxassetid://107753175681578", -- a soft round glow
	spark = "rbxassetid://73042129135061", -- a short streak
}
-- fire along the bottom of a frame (a legendary reveal): flame tongues, smoke above them, embers rising. colour: the
-- accent (default a legendary gold). returns a handle with :stop() (let it burn down) and :destroy()
function UiParticles.fireStrip(frame: GuiObject, colour: Color3?, fireTex: { id: string, cell: number }?): any
	-- (sizes and speeds in the frame's height H; the frame is the bottom third of the screen. round 3, 20 Nov, main for
	-- the owner: "a thick fire WALL: a bright white-hot glowing base, dense overlapping flame bodies, smoke rolling above,
	-- and embers". round 1 was small tips, round 2 thin wisps)
	local c = colour or Color3.fromRGB(240, 178, 52)
	local hot = c:Lerp(Color3.new(1, 1, 1), 0.65)
	local deep = c:Lerp(Color3.fromRGB(120, 40, 10), 0.5)
	local ft = fireTex or { id = TEX.tongues, cell = 128 } -- (the pack sheet's size can't be read here: ours is known 1024)
	-- the glow band: white-hot at the bottom edge through the colour to clear, about 14% of the screen tall, flickering
	local band = Instance.new("Frame")
	band.Name = "FireBand"; band.BorderSizePixel = 0; band.BackgroundColor3 = Color3.new(1, 1, 1); band.BackgroundTransparency = 0.05
	band.AnchorPoint = Vector2.new(0, 1); band.Position = UDim2.fromScale(0, 1); band.Size = UDim2.fromScale(1, 0.42); band.ZIndex = 1
	local g = Instance.new("UIGradient")
	g.Rotation = -90
	g.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, hot), ColorSequenceKeypoint.new(0.35, c), ColorSequenceKeypoint.new(1, deep) })
	g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.4, 0.45), NumberSequenceKeypoint.new(1, 1) })
	g.Parent = band
	band.Parent = frame
	local flick = game:GetService("TweenService"):Create(band, TweenInfo.new(0.32, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{ BackgroundTransparency = 0.22 })
	flick:Play()
	local bodies = UiParticles.new(frame, { texture = ft.id, cell = Vector2.new(ft.cell, ft.cell), frames = 64, cols = 8, fps = 30,
		rate = 60, life = { 0.7, 1.1 }, size = { { 0, 0.42 }, { 0.35, 0.62 }, { 1, 0.5 } },
		colour = { { 0, hot }, { 0.5, c }, { 1, deep } }, alpha = { { 0, 0.35 }, { 0.15, 0.02 }, { 0.75, 0.15 }, { 1, 1 } },
		area = { -0.04, 0.98, 1.04, 1.12 }, speed = { 0.12, 0.26 }, spread = 6, rot = { -6, 6 }, z = 2 })
	local surge = UiParticles.new(frame, { texture = ft.id, cell = Vector2.new(ft.cell, ft.cell), frames = 64, cols = 8, fps = 30,
		life = { 0.9, 1.3 }, size = { { 0, 0.5 }, { 0.3, 0.78 }, { 1, 0.4 } },
		colour = { { 0, hot }, { 0.5, c }, { 1, deep } }, alpha = { { 0, 0.3 }, { 0.15, 0.0 }, { 0.7, 0.2 }, { 1, 1 } },
		area = { -0.04, 0.95, 1.04, 1.1 }, speed = { 0.2, 0.4 }, spread = 6, z = 2 })
	local smoke = UiParticles.new(frame, { texture = TEX.smoke, cell = Vector2.new(256, 256), frames = 16, cols = 4,
		rate = 14, life = { 2.0, 3.0 }, size = { { 0, 0.6 }, { 1, 1.2 } }, colour = { { 0, Color3.fromRGB(60, 46, 40) }, { 1, Color3.fromRGB(30, 27, 27) } },
		alpha = { { 0, 1 }, { 0.25, 0.62 }, { 1, 1 } }, area = { -0.06, 0.55, 1.06, 0.8 }, speed = { 0.14, 0.26 }, spread = 10,
		sway = 0.04, rot = { 0, 360 }, spin = { -12, 12 }, z = 1 })
	local embers = UiParticles.new(frame, { texture = TEX.glow, rate = 40, life = { 2.4, 4.0 },
		size = { { 0, 0.03 }, { 0.3, 0.038 }, { 1, 0.012 } }, colour = { { 0, hot }, { 0.6, c }, { 1, deep } },
		alpha = { { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }, area = { 0, 0.7, 1, 1.0 }, speed = { 0.7, 1.3 }, spread = 18,
		accel = Vector2.new(0, 0.12), drag = 0.25, sway = 0.05, z = 3 })
	local all = { bodies, surge, smoke, embers }
	for _, e in { bodies, smoke, embers } do e:enable(true) end
	surge:emit(34); bodies:emit(40); embers:emit(30); smoke:emit(8)
	local h = {}
	function h.stop(_: any)
		for _, e in all do e:stop() end
		flick:Cancel()
		game:GetService("TweenService"):Create(band, TweenInfo.new(1.2), { BackgroundTransparency = 1 }):Play()
	end
	function h.destroy(_: any)
		for _, e in all do e:destroy() end
		flick:Cancel(); band:Destroy()
	end
	return h
end

return UiParticles
