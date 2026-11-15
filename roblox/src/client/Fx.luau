--!strict
-- the step 2 effects, all on the client, moved every frame (never server-stepped: the owner's "the bits spitting out
-- are clunky" note). each looks for its Blender mesh in ReplicatedStorage.JankfireFX (fx_flash_star, fx_tracer,
-- fx_casing, fx_marble, fx_spark, fx_impact, fx_parry_star, fx_dust: roblox/assets/fx/, see roblox/README.md) and
-- falls back to a plain part of the same size and colour until it's imported
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))

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

-- a Blender mesh from the library (its first MeshPart), or a plain part
local function piece(name: string, shape: Enum.PartType, size: Vector3, color: Color3, mat: Enum.Material, meshLen: number?): BasePart
	local lib = ReplicatedStorage:FindFirstChild("JankfireFX")
	local t = lib and lib:FindFirstChild(name)
	local p: BasePart
	if t then
		local src = if t:IsA("BasePart") then t else t:FindFirstChildWhichIsA("BasePart", true)
		if src then
			p = src:Clone()
			-- fit the mesh to the size asked for, keeping its proportions along its longest side
			local sz = p.Size
			local f = (meshLen or math.max(size.X, size.Y, size.Z)) / math.max(sz.X, sz.Y, sz.Z)
			p.Size = sz * f
		else
			p = Instance.new("Part")
		end
	else
		local q = Instance.new("Part")
		q.Shape = shape; q.Size = size
		p = q
	end
	p.Name = name; p.Color = color; p.Material = mat
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Parent = folder
	return p
end
Fx.piece = piece

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
			b.p:Destroy(); table.remove(bits, i); continue
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
function Fx.flash(at: CFrame, big: boolean, color: Color3?)
	local s = (0.24 * S) * (0.8 + math.random() * 0.6) * (if big then 1.6 else 1)
	-- (the Blender star is 0.24 m across with 0.4 m spikes running forward: its longest side is the spikes)
	local p = piece("fx_flash_star", Enum.PartType.Cylinder, Vector3.new(0.02, s, s), color or Color3.fromRGB(255, 225, 120), Enum.Material.Neon, s * 0.42 / 0.24)
	p.CFrame = at * CFrame.Angles(0, 0, math.random() * math.pi * 2) * (if p:IsA("MeshPart") then CFrame.identity else CFrame.Angles(0, math.pi / 2, 0))
	add({ p = p, v = Vector3.zero, w = Vector3.zero, t = 0, life = 0.05, grav = 0, bounce = 0, fade = 0.02, spin = CFrame.identity, stick = true })
	local light = Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 200, 120); light.Range = 10; light.Brightness = 3; light.Parent = p
end

-- a brass casing out of the port: up and right, spinning, one or two bounces, fades (owner: smooth, not clunky)
function Fx.brass(at: CFrame, big: boolean)
	local sz = Vector3.new(0.03, 0.03, 0.07) * S * (if big then 1.6 else 1)
	local p = piece("fx_casing", Enum.PartType.Cylinder, sz, Color3.fromRGB(214, 168, 70), Enum.Material.Metal)
	p.CFrame = at
	local v = at.RightVector * (2.2 + math.random()) * S + at.UpVector * (2.4 + math.random()) * S + at.LookVector * -0.4 * S
	add({ p = p, v = v, w = Vector3.new(math.random() * 30 - 15, math.random() * 30, math.random() * 20), t = 0, life = 1.4, grav = 4.5 * S * 2, bounce = 0.35, fade = 0.4, spin = CFrame.identity })
end

-- bullet impact: grey-brown chunks off the surface, 0.5 s
function Fx.impact(at: Vector3, normal: Vector3)
	for i = 1, 6 do
		local p = piece("fx_dust", Enum.PartType.Block, Vector3.new(0.12, 0.12, 0.12) * (0.6 + math.random() * 0.8), Color3.fromRGB(120 + i * 6, 104, 88), Enum.Material.Slate)
		p.CFrame = CFrame.new(at + normal * 0.1) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
		local v = (normal + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 1.2).Unit * (4 + math.random() * 8)
		add({ p = p, v = v, w = Vector3.new(10, 6, 8), t = 0, life = 0.5, grav = 40, bounce = 0, fade = 0.25, spin = CFrame.identity })
	end
end

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
			local flown = 0
			add({ p = p, v = u * 70 * S, w = Vector3.new(math.random() * 20, math.random() * 20, 0), t = 0, life = 2.6 + math.random(), grav = 22 * S, bounce = 0.45, fade = 0.6, spin = CFrame.identity,
				step = function(b: Bit, dt: number)
					if flown < L then -- along the pellet's path to where it ended
						local s = math.min(70 * S * dt, L - flown)
						flown += s
						b.p.CFrame = b.p.CFrame + u * s
						if flown >= L then b.v = (-u * 0.3 + Vector3.new(0, 0.4, 0)) * 6 * S * math.random() end
						return
					end
					if b.stick then return end
					b.v -= Vector3.new(0, b.grav * dt, 0)
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
