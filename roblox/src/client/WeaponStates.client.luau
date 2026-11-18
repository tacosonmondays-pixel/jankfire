--!strict
-- weapons batch A (18 Nov 2026): what the server's states do on this machine (WEAPONS.md "Water Pistol", "Nail Gun").
-- soaked (SoakUntil, the server clock's end time, on a Player or a dummy's model): you run slower and slide (Body.wet /
-- Body.grip, read by Move.client) behind a thin wet edge on the screen; everyone soaked drips. pinned by a Nail Gun
-- (PinAt / PinUntil on you): Body.pin holds you on the wall. the server's Fx "pin" puts the big nails through whoever
-- it is for everyone to see, Fx "soak" splashes them. a pin or a soak from before your respawn is never carried over
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Body = require(script.Parent:WaitForChild("Body"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local SOAK = (Weapons.list.water and Weapons.list.water.soak) or { dur = 4, slow = 0.72, grip = 0.3 }
local function sNow(): number return workspace:GetServerTimeNow() end

-- ---------------------------------------------------------------- yours: soaked, pinned
local mine = { soakUntil = 0, life = 0 }
local function readPin()
	local at, untilT = me:GetAttribute("PinAt"), me:GetAttribute("PinUntil")
	if typeof(at) == "Vector3" and type(untilT) == "number" and untilT > sNow() then
		Body.pin = { at = at, untilT = untilT }
	end
end
me:GetAttributeChangedSignal("PinUntil"):Connect(readPin)
me:GetAttributeChangedSignal("SoakUntil"):Connect(function()
	local v = me:GetAttribute("SoakUntil")
	mine.soakUntil = if type(v) == "number" then v else 0
end)
me:GetAttributeChangedSignal("DashUntil"):Connect(function()
	local v, u = me:GetAttribute("DashV"), me:GetAttribute("DashUntil")
	if typeof(v) == "Vector3" and type(u) == "number" then Body.dash = { v = v, untilT = u } end
end)
me:GetAttributeChangedSignal("StunUntil"):Connect(function()
	local v = me:GetAttribute("StunUntil")
	Body.stunUntil = if type(v) == "number" then v else 0
end)
-- (weapons batch D) the TV Remote paused you: held still where you are (your client owns your body, so it's anchored
-- here), and the momentum you had comes back when it ends
me:GetAttributeChangedSignal("PauseUntil"):Connect(function()
	local u = me:GetAttribute("PauseUntil")
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if type(u) ~= "number" or not root then return end
	local left = u - workspace:GetServerTimeNow()
	if left <= 0 then return end
	local v = root.AssemblyLinearVelocity
	root.Anchored = true
	task.delay(left, function()
		if me:GetAttribute("PauseUntil") ~= u or not root.Parent then return end
		root.Anchored = false
		root.AssemblyLinearVelocity = v
		me:SetAttribute("PauseUntil", nil)
	end)
end)
me.CharacterAdded:Connect(function()
	mine.soakUntil, Body.pin = 0, nil
	Body.wet, Body.grip = 1, 1
	Body.stunUntil = 0
end)

-- the wet edge: four soft blue bands at the screen's edges, fading out over the last 0.8 s of the soak
local gui = Instance.new("ScreenGui")
gui.Name = "JankfireWet"; gui.IgnoreGuiInset = true; gui.ResetOnSpawn = false; gui.DisplayOrder = 2; gui.Enabled = false
gui.Parent = me:WaitForChild("PlayerGui")
local bands: { Frame } = {}
for _, b in { { UDim2.new(1, 0, 0.16, 0), UDim2.new(0, 0, 0, 0), 90 }, { UDim2.new(1, 0, 0.16, 0), UDim2.new(0, 0, 0.84, 0), -90 },
	{ UDim2.new(0.1, 0, 1, 0), UDim2.new(0, 0, 0, 0), 0 }, { UDim2.new(0.1, 0, 1, 0), UDim2.new(0.9, 0, 0, 0), 180 } } do
	local f = Instance.new("Frame")
	f.Size, f.Position = b[1] :: UDim2, b[2] :: UDim2
	f.BackgroundColor3 = Color3.fromRGB(80, 150, 205); f.BorderSizePixel = 0
	local g = Instance.new("UIGradient")
	g.Rotation = b[3] :: number
	g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) })
	g.Parent = f
	f.Parent = gui
	table.insert(bands, f)
end

-- (weapons batch B) tased: a faint white flicker over your screen while it lasts
local static = Instance.new("Frame")
static.Size = UDim2.fromScale(1, 1); static.BackgroundColor3 = Color3.fromRGB(235, 240, 210); static.BorderSizePixel = 0
static.BackgroundTransparency = 1
static.Parent = gui

-- a jagged bolt from a to b: a few short tracers bent off the line (the Taser's links and the crackle on the stunned)
local function bolt(a: Vector3, b: Vector3, col: Color3, n: number, jag: number, wide: number, life: number)
	local d = b - a
	if d.Magnitude < 0.05 then return end
	local side = d:Cross(Vector3.yAxis)
	side = if side.Magnitude > 1e-3 then side.Unit else Vector3.xAxis
	local up = side:Cross(d.Unit)
	local prev = a
	for i = 1, n do
		local u = i / n
		local p = a + d * u
		if i < n then p += side * (math.random() - 0.5) * 2 * jag + up * (math.random() - 0.5) * 2 * jag end
		Fx.tracer(prev, p, col, wide, life)
		prev = p
	end
end

-- ---------------------------------------------------------------- everyone soaked drips
local dripAcc = 0
local function soakedModels(): { Model }
	local out = {}
	local t = sNow()
	for _, p in Players:GetPlayers() do
		local v = p:GetAttribute("SoakUntil")
		if type(v) == "number" and v > t and p.Character then table.insert(out, p.Character) end
	end
	local d = workspace:FindFirstChild("Dummies")
	if d then
		for _, m in d:GetChildren() do
			local v = m:GetAttribute("SoakUntil")
			if m:IsA("Model") and type(v) == "number" and v > t then table.insert(out, m) end
		end
	end
	return out
end

RunService.RenderStepped:Connect(function(dt: number)
	local t = sNow()
	local left = mine.soakUntil - t
	local wet = left > 0 and SOAK.dur - left >= -0.5 -- (a stale end time from a clock jump is ignored)
	Body.wet = if wet then SOAK.slow else 1
	Body.grip = if wet then SOAK.grip else 1
	gui.Enabled = wet
	if wet then
		local a = math.clamp(left / 0.8, 0, 1)
		for _, f in bands do f.BackgroundTransparency = 1 - 0.55 * a end
	end
	if Body.pin and t >= Body.pin.untilT then Body.pin = nil end
	local stunned = Body.stunned()
	static.BackgroundTransparency = if stunned then 0.86 + math.random() * 0.1 else 1
	gui.Enabled = wet or stunned
	dripAcc += dt
	if dripAcc < 0.12 then return end
	dripAcc = 0
	local cam = workspace.CurrentCamera
	for _, m in soakedModels() do
		local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not r then continue end
		if m == me.Character and cam and (cam.CFrame.Position - r.Position).Magnitude < 4.5 then continue end -- (not in your eyes)
		local off = Vector3.new((math.random() - 0.5) * 2, math.random() * 2.5 - 1, (math.random() - 0.5) * 2)
		Fx.drip(r.Position + off)
	end
	-- (weapons batch B) the stunned crackle: a short arc somewhere on everyone tased (not round your own eyes)
	local function crackle(m: Instance?, v: any)
		local r = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not r or type(v) ~= "number" or v <= t then return end
		if m == me.Character and cam and (cam.CFrame.Position - r.Position).Magnitude < 4.5 then return end
		local a = r.Position + Vector3.new((math.random() - 0.5) * 2, math.random() * 3 - 1.5, (math.random() - 0.5) * 2)
		bolt(a, a + Vector3.new((math.random() - 0.5) * 2, (math.random() - 0.5) * 2, (math.random() - 0.5) * 2), Color3.fromRGB(200, 235, 255), 3, 0.25, 0.05, 0.08)
	end
	for _, p in Players:GetPlayers() do crackle(p.Character, p:GetAttribute("StunUntil")) end
	local dz = workspace:FindFirstChild("Dummies")
	if dz then for _, m in dz:GetChildren() do crackle(m, m:GetAttribute("StunUntil")) end end
end)

-- ---------------------------------------------------------------- someone else's Minigun spinning: its whine at them
-- (yours is Arsenal's own, in your ears). the Spin attribute is the server's, set while their trigger is down
local whine: { [Player]: Sound } = {}
local function setWhine(p: Player)
	local on = p ~= me and p:GetAttribute("Spin") == true
	local s = whine[p]
	local root = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
	if on and not s and root then
		local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
		local src = lib and lib:FindFirstChild("minigun_spin")
		if src and src:IsA("Sound") then
			local c = src:Clone()
			c.Looped = true
			c.RollOffMode = Enum.RollOffMode.InverseTapered; c.RollOffMinDistance = 8; c.RollOffMaxDistance = 160
			c.Parent = root
			c:Play()
			whine[p] = c
		end
	elseif (not on or not root) and s then
		s:Destroy()
		whine[p] = nil
	end
end
local function watch(p: Player)
	p:GetAttributeChangedSignal("Spin"):Connect(function() setWhine(p) end)
	p.CharacterAdded:Connect(function() local s = whine[p]; if s then s:Destroy(); whine[p] = nil end; setWhine(p) end)
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(function(p) local s = whine[p]; if s then s:Destroy() end; whine[p] = nil end)

-- ---------------------------------------------------------------- the server's Fx: a soak's splash, a pin's big nails
local function rootOf(m: any): BasePart?
	if typeof(m) ~= "Instance" then return nil end
	return (m :: Instance):FindFirstChild("HumanoidRootPart") :: BasePart?
end
local function bigNail(cf: CFrame, life: number)
	local n = Instance.new("Part")
	n.Name = "PinNail"; n.Anchored = true; n.CanCollide = false; n.CanQuery = false; n.CanTouch = false; n.CastShadow = false
	n.Material = Enum.Material.Metal; n.Color = Color3.fromRGB(170, 176, 184)
	n.Shape = Enum.PartType.Cylinder; n.Size = Vector3.new(1.6, 0.16, 0.16)
	n.CFrame = cf
	local head = Instance.new("Part")
	head.Name = "PinNailHead"; head.Anchored = true; head.CanCollide = false; head.CanQuery = false; head.CanTouch = false
	head.Material = Enum.Material.Metal; head.Color = Color3.fromRGB(150, 156, 164)
	head.Shape = Enum.PartType.Cylinder; head.Size = Vector3.new(0.08, 0.42, 0.42)
	head.CFrame = cf * CFrame.new(-0.8, 0, 0)
	head.Parent = n
	n.Parent = workspace:FindFirstChild("JankfireFx") or workspace
	task.delay(life, function() n:Destroy() end)
end
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	if f.k == "dash" and typeof(f.a) == "Vector3" and typeof(f.b) == "Vector3" then
		-- (the Scythe's dash) a teal streak and three fading afterimages along the path
		Fx.tracer(f.a, f.b, Color3.fromRGB(62, 230, 200), 0.5, 0.25)
		for i = 1, 3 do
			local g = Instance.new("Part")
			g.Size = Vector3.new(2, 5, 1); g.Color = Color3.fromRGB(62, 230, 200); g.Material = Enum.Material.Neon
			g.Transparency = 0.6 + i * 0.1; g.Anchored = true; g.CanCollide = false; g.CanQuery = false; g.CastShadow = false
			g.CFrame = CFrame.lookAt((f.a :: Vector3):Lerp(f.b, i / 4), f.b :: Vector3)
			g.Parent = workspace:FindFirstChild("JankfireFx") or workspace
			task.delay(0.25, function() g:Destroy() end)
		end
		Sfx.play("scythe_dash", f.a :: Vector3, 1)
	elseif (f.k == "burn" or f.k == "sleep") and typeof(f.model) == "Instance" then
		-- (weapons batch D, the Bow's tips) on fire for 3 s; asleep for 4 s: slow purple motes over the head
		local m = f.model :: Instance
		local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not r then return end
		local dur = tonumber(f.dur) or 3
		if f.k == "burn" then
			local fire = Instance.new("Fire")
			fire.Size = 4; fire.Heat = 6; fire.Color = Color3.fromRGB(255, 120, 40); fire.SecondaryColor = Color3.fromRGB(255, 200, 80)
			fire.Parent = r
			task.delay(dur, function() fire.Enabled = false; task.delay(1, function() fire:Destroy() end) end)
			local lib = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireSounds")
			local src = lib and lib:FindFirstChild("flame_burn") -- (a loop: cloned onto them for the burn, then gone)
			if src and src:IsA("Sound") then
				local c = src:Clone(); c.Looped = true; c.Parent = r; c:Play()
				task.delay(dur, function() c:Destroy() end)
			end
		else
			local a = Instance.new("Attachment"); a.Position = Vector3.new(0, 3.5, 0); a.Parent = r
			local pe = Instance.new("ParticleEmitter")
			pe.Color = ColorSequence.new(Color3.fromRGB(176, 125, 255)); pe.LightEmission = 0.6
			pe.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 0) })
			pe.Transparency = NumberSequence.new(0.2, 1); pe.Rate = 6; pe.Lifetime = NumberRange.new(1.2, 1.8)
			pe.Speed = NumberRange.new(0.6, 1.2); pe.SpreadAngle = Vector2.new(25, 25); pe.Parent = a
			task.delay(dur, function() a:Destroy() end)
			Sfx.play("sleep_hit", r.Position, 0.8)
			-- asleep yourself: the camera sinks to the floor till you wake
			if m == me.Character then
				local hum = m:FindFirstChildOfClass("Humanoid")
				if hum then
					hum.CameraOffset = Vector3.new(0, -2.5, 0)
					task.delay(dur, function() if hum.Parent then hum.CameraOffset = Vector3.zero end end)
				end
			end
		end
	elseif f.k == "gas" and typeof(f.p) == "Vector3" then
		-- the gas tip's cloud: a pale green haze the size of its reach, thinning out over its 4.5 s
		local ball = Instance.new("Part")
		ball.Shape = Enum.PartType.Ball
		local r = tonumber(f.r) or 16.5
		ball.Size = Vector3.new(r * 2, r * 2, r * 2); ball.CFrame = CFrame.new(f.p :: Vector3)
		ball.Color = Color3.fromRGB(125, 255, 79); ball.Material = Enum.Material.SmoothPlastic; ball.Transparency = 0.82
		ball.Anchored = true; ball.CanCollide = false; ball.CanQuery = false; ball.CanTouch = false; ball.CastShadow = false
		ball.Parent = workspace:FindFirstChild("JankfireFx") or workspace
		local dur = tonumber(f.dur) or 4.5
		game:GetService("TweenService"):Create(ball, TweenInfo.new(dur, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 }):Play()
		task.delay(dur, function() ball:Destroy() end)
		local lib = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireSounds")
		local src = lib and lib:FindFirstChild("gas_hiss") -- (a loop: on the cloud, gone with it)
		if src and src:IsA("Sound") then local c = src:Clone(); c.Looped = true; c.Parent = ball; c:Play() end
	elseif f.k == "tvpause" and typeof(f.model) == "Instance" then
		-- (weapons batch D) the TV Remote's pause: they go grey and still for the pause
		local m = f.model :: Instance
		local h = Instance.new("Highlight")
		h.FillColor = Color3.fromRGB(150, 150, 160); h.FillTransparency = 0.45
		h.OutlineColor = Color3.fromRGB(255, 90, 138); h.OutlineTransparency = 0.2
		h.DepthMode = Enum.HighlightDepthMode.Occluded
		h.Parent = m
		task.delay(tonumber(f.dur) or 1.2, function() h:Destroy() end)
		local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		Sfx.play("remote_pause", if r then r.Position else nil, 0.9)
	elseif f.k == "tvrewind" and typeof(f.a) == "Vector3" and typeof(f.b) == "Vector3" then
		-- the rewind: a pink streak from where they were back to where they were 2 s ago
		Fx.tracer(f.a, f.b, Color3.fromRGB(255, 90, 138), 0.4, 0.35)
		Sfx.play("remote_rewind", f.b :: Vector3, 0.9)
	elseif (f.k == "gavel" or f.k == "gavelx") and typeof(f.p) == "Vector3" then
		-- the Scales' pillar: a gold ring on the floor and a faint column rising for its second, then the strike
		local at, r, h = f.p :: Vector3, tonumber(f.r) or 6.9, tonumber(f.h) or 9.6
		local folder = workspace:FindFirstChild("JankfireFx") or workspace
		local function disc(size: Vector3, y: number, a: number, life: number): Part
			local d = Instance.new("Part")
			d.Shape = Enum.PartType.Cylinder; d.Size = size
			d.CFrame = CFrame.new(at + Vector3.new(0, y, 0)) * CFrame.Angles(0, 0, math.pi / 2)
			d.Color = Color3.fromRGB(255, 200, 58); d.Material = Enum.Material.Neon; d.Transparency = a
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
			d.Parent = folder
			task.delay(life, function() d:Destroy() end)
			return d
		end
		if f.k == "gavel" then
			local dur = tonumber(f.dur) or 1
			disc(Vector3.new(0.12, r * 2, r * 2), 0.06, 0.55, dur)
			local col = disc(Vector3.new(h, r * 2, r * 2), h / 2, 0.92, dur)
			game:GetService("TweenService"):Create(col, TweenInfo.new(dur), { Transparency = 0.7 }):Play()
			Sfx.play("gavel_charge", at, 0.8)
		else
			local col = disc(Vector3.new(h, r * 2, r * 2), h / 2, 0.35, 0.35)
			game:GetService("TweenService"):Create(col, TweenInfo.new(0.35), { Transparency = 1 }):Play()
			Sfx.play("gavel_strike", at, 1)
		end
	elseif f.k == "zap" and type(f.links) == "table" then
		-- (weapons batch B) the Taser: two dark wires out to whoever it hit, a yellow bolt down them, cyan bolts on to
		-- everyone soaked it jumped to (70 ms apart), sparks where they land; or the darts into the wall on a miss
		local first = f.links[1]
		local from = if type(first) == "table" and typeof(first[1]) == "Vector3" then first[1] :: Vector3
			elseif typeof(f.miss) == "Vector3" then nil else nil
		local shooter = if typeof(f.model) == "Instance" then f.model :: Instance else nil
		local mz: Vector3? = nil
		if shooter == me.Character then
			local cam = workspace.CurrentCamera
			mz = if cam then cam.CFrame.Position + cam.CFrame.LookVector * 1.5 - cam.CFrame.UpVector * 0.6 else nil
		else
			local hw = shooter and shooter:FindFirstChild("HeldWeapon")
			local hr = hw and (hw :: Model).PrimaryPart
			local a = hr and hr:FindFirstChild("Muzzle")
			mz = if a and a:IsA("Attachment") then a.WorldPosition else from
		end
		local to = if type(first) == "table" and typeof(first[2]) == "Vector3" then first[2] :: Vector3 elseif typeof(f.miss) == "Vector3" then f.miss :: Vector3 else nil
		if mz and to then
			local side = (to - mz):Cross(Vector3.yAxis)
			side = if side.Magnitude > 1e-3 then side.Unit * 0.25 else Vector3.zero
			Fx.tracer(mz, to + side, Color3.fromRGB(40, 42, 46), 0.035, 0.75)
			Fx.tracer(mz, to - side, Color3.fromRGB(40, 42, 46), 0.035, 0.75)
		end
		if type(first) == "table" and mz and typeof(first[2]) == "Vector3" then
			bolt(mz, first[2] :: Vector3, Color3.fromRGB(240, 235, 120), 7, 0.35, 0.09, 0.2)
			Fx.impact(first[2] :: Vector3, Vector3.yAxis, nil, Enum.Material.Metal, { hole = false, scale = 0.6 })
			Sfx.play("taser_buzz", first[2] :: Vector3, 1)
		elseif to then
			Fx.impact(to, Vector3.yAxis, nil, Enum.Material.Metal, { hole = false, scale = 0.4 })
		end
		for i = 2, #f.links do
			local l = f.links[i]
			if type(l) ~= "table" or typeof(l[1]) ~= "Vector3" or typeof(l[2]) ~= "Vector3" then continue end
			task.delay((i - 1) * 0.07, function()
				bolt(l[1] :: Vector3, l[2] :: Vector3, Color3.fromRGB(140, 220, 255), 6, 0.4, 0.07, 0.2)
				Fx.impact(l[2] :: Vector3, Vector3.yAxis, nil, Enum.Material.Metal, { hole = false, scale = 0.5 })
				Sfx.play("taser_arc", l[2] :: Vector3, 0.8)
			end)
		end
	elseif f.k == "soak" then
		local r = rootOf(f.model)
		if r then Fx.drip(r.Position + Vector3.new(0, 1, 0), 10); Sfx.play("water_soak", r.Position, 0.8) end
	elseif f.k == "pin" and typeof(f.at) == "Vector3" then
		local at = f.at :: Vector3
		local life = (tonumber(f.dur) or 1.1) + 0.4
		local nrm = if typeof(f.n) == "Vector3" and (f.n :: Vector3).Magnitude > 0.5 then (f.n :: Vector3).Unit else nil
		Sfx.play("nail_pinned", at + Vector3.new(0, 2, 0), 1)
		if nrm then
			-- through the sleeves, the legs and the hood, into the wall behind them (their back to it)
			local side = nrm:Cross(Vector3.yAxis)
			side = if side.Magnitude > 1e-3 then side.Unit else Vector3.xAxis
			for _, o in { { -1.4, 4.4 }, { 1.4, 4.4 }, { -0.6, 0.9 }, { 0.6, 0.9 }, { 0, 6.2 } } do
				local p = at + side * o[1] + Vector3.new(0, o[2], 0) + nrm * 0.2
				bigNail(CFrame.lookAt(p, p - nrm) * CFrame.Angles(0, math.pi / 2, 0), life)
			end
		else
			-- no wall: four through the feet and the hem into the floor
			for i = 0, 3 do
				local a = i * math.pi / 2 + math.pi / 4
				local p = at + Vector3.new(math.cos(a) * 1.2, 0.6, math.sin(a) * 1.2)
				bigNail(CFrame.lookAt(p, p - Vector3.yAxis) * CFrame.Angles(0, math.pi / 2, 0), life)
			end
		end
		if f.model == me.Character then readPin() end
	end
end)

