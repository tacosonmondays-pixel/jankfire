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
me.CharacterAdded:Connect(function()
	mine.soakUntil, Body.pin = 0, nil
	Body.wet, Body.grip = 1, 1
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
	if f.k == "soak" then
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

