--!strict
-- HOLDOUT's world effects on your screen (26 Nov 2026; roblox/docs/HUNT.md sections 5-6).
--   "shatter" (model): a body that died in a round breaks into plain cubes, each part into a few in its own colour (the
--     avatar's own colours, its hat too), with about a dozen small dark-red cubes; they fly with the hit, bounce, and fade
--     out in 4 s (the red ones in 1.5 s). Plain Parts made here: nothing uploaded, no body parts, no realistic blood
--     (the maturity questionnaire's "unrealistic" blood and violence: see the doc)
--   "pulse" (models, s): the gunman's PULSE, hiders near him outlined through walls for a moment (his screen only)
--   "tracks" (points): the gunman's TRACKS, footprints where hiders ran (his screen only, faded in a few seconds)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent

local me = Players.LocalPlayer
local rng = Random.new()
local BLOOD = Color3.fromRGB(255, 176, 204) -- (owner 27 Nov: pink, a soft sakura pink; a clearly unreal colour, HUNT.md section 6)

local function fxFolder(): Folder
	local f = workspace:FindFirstChild("HuntFx") :: Folder?
	if not f then f = Instance.new("Folder"); f.Name = "HuntFx"; f.Parent = workspace end
	return f :: Folder
end

local function cube(size: Vector3, cf: CFrame, col: Color3, vel: Vector3, life: number, into: Instance): Part
	local c = Instance.new("Part")
	c.Size = size; c.CFrame = cf; c.Color = col; c.Material = Enum.Material.SmoothPlastic
	c.TopSurface = Enum.SurfaceType.Smooth; c.BottomSurface = Enum.SurfaceType.Smooth
	c.CanCollide = true; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false; c.Massless = false
	c.CustomPhysicalProperties = PhysicalProperties.new(0.8, 0.6, 0.35, 1, 1)
	c.Parent = into
	c.AssemblyLinearVelocity = vel
	c.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-12, 12), rng:NextNumber(-12, 12), rng:NextNumber(-12, 12))
	task.delay(math.max(0, life - 1.0), function()
		if c.Parent then TweenService:Create(c, TweenInfo.new(1.0), { Transparency = 1 }):Play() end
	end)
	Debris:AddItem(c, life + 0.1)
	return c
end

local function shatter(model: Instance?)
	if not (model and model:IsA("Model") and model.Parent) then return end
	local root = model:FindFirstChild("HumanoidRootPart") :: BasePart?
	local centre = if root then root.Position else model:GetPivot().Position
	local v0 = if root then root.AssemblyLinearVelocity else Vector3.zero
	if v0.Magnitude > 80 then v0 = v0.Unit * 80 end
	local into = fxFolder()
	local made, CAP = 0, 96
	for _, p in model:GetDescendants() do
		if not p:IsA("BasePart") or p.Name == "HumanoidRootPart" then continue end
		if p.Transparency >= 0.9 or p.LocalTransparencyModifier >= 0.9 then continue end
		p.LocalTransparencyModifier = 1
		if made >= CAP then continue end
		local s = p.Size
		local nx = math.clamp(math.floor(s.X / 0.9 + 0.5), 1, 2)
		local ny = math.clamp(math.floor(s.Y / 0.9 + 0.5), 1, 3)
		local nz = math.clamp(math.floor(s.Z / 0.9 + 0.5), 1, 2)
		local sub = Vector3.new(s.X / nx, s.Y / ny, s.Z / nz)
		local edge = math.max(0.3, math.min(sub.X, sub.Y, sub.Z) * 0.95)
		for i = 0, nx - 1 do for j = 0, ny - 1 do for k = 0, nz - 1 do
			if made >= CAP then break end
			local off = Vector3.new((i + 0.5) * sub.X - s.X / 2, (j + 0.5) * sub.Y - s.Y / 2, (k + 0.5) * sub.Z - s.Z / 2)
			local cf = p.CFrame * CFrame.new(off)
			local out = cf.Position - centre
			out = if out.Magnitude > 1e-3 then out.Unit else Vector3.yAxis
			local vel = v0 * 0.45 + out * rng:NextNumber(6, 16) + Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(6, 16), rng:NextNumber(-4, 4))
			cube(Vector3.new(edge, edge, edge), cf, p.Color, vel, 4.0, into)
			made += 1
		end end end
	end
	-- a dozen small pink cubes (cartoon, never a spray or a pool)
	for _ = 1, 12 do
		local e = rng:NextNumber(0.22, 0.4)
		local dir = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0.2, 1), rng:NextNumber(-1, 1)).Unit
		cube(Vector3.new(e, e, e), CFrame.new(centre + dir * 0.8), BLOOD, v0 * 0.3 + dir * rng:NextNumber(10, 20), 1.5, into)
	end
	-- (the face and clothes go with the parts: decals on a hidden part don't draw)
end

local function pulse(models: { Model }, show: number)
	for _, m in models do
		if typeof(m) ~= "Instance" or not m:IsA("Model") or not m.Parent then continue end
		local h = Instance.new("Highlight")
		h.Name = "HuntPulse"; h.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
		h.FillColor = Color3.fromRGB(236, 214, 170); h.FillTransparency = 0.65
		h.OutlineColor = Color3.fromRGB(255, 240, 210); h.OutlineTransparency = 0.1
		h.Parent = m
		task.delay(math.max(0.3, show - 0.4), function()
			if h.Parent then TweenService:Create(h, TweenInfo.new(0.4), { FillTransparency = 1, OutlineTransparency = 1 }):Play() end
		end)
		Debris:AddItem(h, show + 0.1)
	end
end

local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
local function tracks(points: { Vector3 })
	local into = fxFolder()
	local fresh = 3.0
	for _, pv in HC.PASSIVES do if pv.id == "tracks" then fresh = pv.fresh end end
	ray.FilterDescendantsInstances = { into, me.Character :: any }
	for _, at in points do
		if typeof(at) ~= "Vector3" then continue end
		local hit = workspace:Raycast(at + Vector3.new(0, 2, 0), Vector3.new(0, -5, 0), ray)
		local y = if hit then hit.Position.Y + 0.04 else at.Y
		local f = Instance.new("Part")
		f.Anchored = true; f.CanCollide = false; f.CanQuery = false; f.CanTouch = false; f.CastShadow = false
		f.Size = Vector3.new(0.7, 0.05, 1.2); f.Color = Color3.fromRGB(64, 66, 70); f.Material = Enum.Material.SmoothPlastic
		f.Transparency = 0.25
		f.CFrame = CFrame.new(at.X, y, at.Z) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
		f.Parent = into
		TweenService:Create(f, TweenInfo.new(fresh, Enum.EasingStyle.Linear), { Transparency = 1 }):Play()
		Debris:AddItem(f, fresh + 0.1)
	end
end

-- ------------------------------------------------------------------ stage 3: the traps' looks
local pg = me:WaitForChild("PlayerGui")
local blindGui = Instance.new("ScreenGui"); blindGui.Name = "HuntBlind"; blindGui.IgnoreGuiInset = true; blindGui.ResetOnSpawn = false
blindGui.DisplayOrder = 20; blindGui.Enabled = false; blindGui.Parent = pg
local white = Instance.new("Frame"); white.BackgroundColor3 = Color3.fromRGB(244, 238, 226); white.BorderSizePixel = 0
white.Size = UDim2.fromScale(1, 1); white.BackgroundTransparency = 0.05; white.Parent = blindGui
local function blind(secs: number)
	local blur = Instance.new("BlurEffect"); blur.Size = 24; blur.Parent = workspace.CurrentCamera
	blindGui.Enabled = true
	white.BackgroundTransparency = 0.05
	TweenService:Create(white, TweenInfo.new(secs, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { BackgroundTransparency = 1 }):Play()
	TweenService:Create(blur, TweenInfo.new(secs, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Size = 0 }):Play()
	task.delay(secs, function() blindGui.Enabled = false; blur:Destroy() end)
end
local function emitter(at: Vector3, props: { [string]: any }, life: number): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1; p.Size = Vector3.new(1, 1, 1)
	p.CFrame = CFrame.new(at); p.Parent = fxFolder()
	local e = Instance.new("ParticleEmitter")
	for k, v in props do (e :: any)[k] = v end
	e.Parent = p
	task.delay(math.max(0.1, life - (props.Lifetime and (props.Lifetime :: NumberRange).Max or 1)), function() e.Enabled = false end)
	Debris:AddItem(p, life + 3)
	return p
end
local function spray(at: Vector3, dir: Vector3)
	local p = emitter(at, { Texture = "rbxasset://textures/particles/smoke_main.dds", Rate = 90, Lifetime = NumberRange.new(0.5, 0.8),
		Speed = NumberRange.new(26, 34), SpreadAngle = Vector2.new(14, 14), Size = NumberSequence.new(0.6, 3.2),
		Transparency = NumberSequence.new(0.35, 1), Color = ColorSequence.new(Color3.fromRGB(236, 214, 196)), Drag = 4 }, 0.5)
	p.CFrame = CFrame.lookAt(at, at + dir)
	local e = p:FindFirstChildOfClass("ParticleEmitter")
	if e then e.EmissionDirection = Enum.NormalId.Front end
end
local function zap(a: Vector3, b: Vector3)
	local p0 = Instance.new("Part"); p0.Anchored = true; p0.CanCollide = false; p0.CanQuery = false; p0.Transparency = 1
	p0.Size = Vector3.new(0.2, 0.2, 0.2); p0.CFrame = CFrame.new(a); p0.Parent = fxFolder()
	local p1 = p0:Clone(); p1.CFrame = CFrame.new(b); p1.Parent = fxFolder()
	local a0 = Instance.new("Attachment"); a0.Parent = p0
	local a1 = Instance.new("Attachment"); a1.Parent = p1
	local beam = Instance.new("Beam"); beam.Attachment0 = a0; beam.Attachment1 = a1; beam.Width0 = 0.12; beam.Width1 = 0.12
	beam.Color = ColorSequence.new(Color3.fromRGB(226, 236, 255)); beam.LightEmission = 1; beam.FaceCamera = true
	beam.Segments = 8; beam.CurveSize0 = 1.2; beam.CurveSize1 = -1.2; beam.Parent = p0
	Debris:AddItem(p0, 0.25); Debris:AddItem(p1, 0.25)
end
local function smoke(at: Vector3, secs: number, radius: number)
	for i = 0, 5 do
		local a = i * math.pi / 3
		local o = if i == 0 then Vector3.zero else Vector3.new(math.cos(a), 0, math.sin(a)) * radius * 0.5
		emitter(at + o + Vector3.new(0, 3, 0), { Texture = "rbxasset://textures/particles/smoke_main.dds", Rate = 14,
			Lifetime = NumberRange.new(3, 4), Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(180, 180),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 4), NumberSequenceKeypoint.new(1, radius * 0.7) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, 0.08), NumberSequenceKeypoint.new(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(184, 186, 188)), RotSpeed = NumberRange.new(-20, 20), Drag = 1 }, secs)
	end
end

Remote.OnClientEvent:Connect(function(op: string, a: any, b: any, c: any, d: any)
	if op == "shatter" then shatter(a)
	elseif op == "pulse" and type(a) == "table" then pulse(a, tonumber(b) or 1.5)
	elseif op == "tracks" and type(a) == "table" then tracks(a)
	elseif op == "blind" then blind(tonumber(a) or 3)
	elseif op == "fx" then
		if a == "spray" and typeof(b) == "Vector3" and typeof(c) == "Vector3" then spray(b, c)
		elseif a == "zap" and typeof(b) == "Vector3" and typeof(c) == "Vector3" then zap(b, c)
		elseif a == "smoke" and typeof(b) == "Vector3" then smoke(b, tonumber(c) or 8, tonumber(d) or 14) end
	end
end)
