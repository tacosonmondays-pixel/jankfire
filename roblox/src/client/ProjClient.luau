--!strict
-- weapons batch C (18 Nov 2026): your side of the projectile weapons (WeaponProj.server flies them). throw = your
-- click (Arsenal calls it: the server checks and spawns); everyone's shots are replayed here from the server's spawn
-- (Fx "proj": where, velocity, gravity), corrected at every bounce ("proju") and ended where the server says ("projx":
-- a blast, a splat, a ball's last bounce). also: the peels on the floor, frost / frozen solid / shattered, and the blood
-- cross (stuck, the X bursting out, the pop: deep red, stylised, no realistic blood). until the kit models are in
-- (JankfireWeapons pj_<kind>) the shots are simple shapes
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local P = {}
local me = Players.LocalPlayer
local W = Weapons.list
local S = Weapons.S
local nextT: { [string]: number } = {}

-- your click: the server decides everything (it gates the cooldown too); this only keeps you from spamming it
function P.throw(held: string, eye: Vector3, look: Vector3): boolean
	local w = W[held] :: any
	if not w or w.kind ~= "proj" then return false end
	local t = os.clock()
	if t < (nextT[held] or 0) then return false end
	nextT[held] = t + (w.cd or 0.5)
	local r = Remotes:FindFirstChild("Throw")
	if r and r:IsA("RemoteEvent") then r:FireServer(held, eye, look) end
	if w.snd then Sfx.play(w.snd) end
	if w.snd2 then task.delay(0.03, Sfx.play, w.snd2) end
	return true
end

-- ---------------------------------------------------------------- the shots in flight
local folder = Instance.new("Folder")
folder.Name = "JankfireProj"
folder.Parent = workspace
local LOOK = {
	rocket = { Color3.fromRGB(235, 205, 80), "Block", Vector3.new(0.5, 0.45, 1.1) },
	peel = { Color3.fromRGB(240, 215, 90), "Block", Vector3.new(0.35, 0.3, 1.0) },
	ball = { Color3.fromRGB(205, 235, 80), "Ball", Vector3.new(0.6, 0.6, 0.6) },
	snow = { Color3.fromRGB(240, 246, 252), "Ball", Vector3.new(0.78, 0.78, 0.78) },
	blood = { Color3.fromRGB(120, 10, 24), "Ball", Vector3.new(0.4, 0.4, 0.4) },
}
type Live = { part: BasePart, p: Vector3, v: Vector3, g: number, k: string, spin: number }
local live: { [number]: Live } = {}
-- the kit models for the shots (guns-remodel, v813: JankfireWeapons w_pj_*, built in metres, nose along -Z, origin at
-- the middle); a kind with none (the tennis ball, the blood cross) stays a simple shape
local KIT = { rocket = "w_pj_chicken", peel = "w_pj_banana", snow = "w_pj_snowball" } :: { [string]: string }
local function kit(name: string): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local t = lib and lib:FindFirstChild(name)
	if not t or not t:IsA("Model") then return nil end
	local m = t:Clone()
	m:ScaleTo(m:GetScale() * S) -- (metres to studs: S studs a metre)
	return m
end
local function shape(k: string): BasePart
	local m = if KIT[k] then kit(KIT[k]) else nil
	if m then
		local root = m.PrimaryPart or m:FindFirstChildWhichIsA("BasePart")
		if root then
			for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end end
			m.Parent = folder
			return root :: BasePart
		end
		m:Destroy()
	end
	local L = LOOK[k] or LOOK.ball
	local part = Instance.new("Part")
	part.Shape = Enum.PartType[L[2] :: string]
	part.Size = L[3] :: Vector3
	part.Color = L[1] :: Color3
	part.Material = if k == "snow" then Enum.Material.Snow elseif k == "blood" then Enum.Material.Glass else Enum.Material.SmoothPlastic
	part.Anchored = true; part.CanCollide = false; part.CanQuery = false; part.CanTouch = false; part.CastShadow = false
	part.Parent = folder
	return part
end
local function drop(id: number)
	local L = live[id]
	if not L then return end
	live[id] = nil
	local m = L.part.Parent
	if m and m ~= folder and m:IsA("Model") then m:Destroy() else L.part:Destroy() end
end
RunService.RenderStepped:Connect(function(dt: number)
	for _, L in live do
		L.v -= Vector3.new(0, L.g * S * dt, 0)
		L.p += L.v * dt
		L.spin += dt * 18
		local face = if L.v.Magnitude > 0.1 then CFrame.lookAt(L.p, L.p + L.v) else CFrame.new(L.p)
		local cf = if L.k == "rocket" or L.k == "blood" then face else face * CFrame.Angles(L.spin, L.spin * 0.6, 0)
		local m = L.part.Parent
		if m and m:IsA("Model") and m ~= folder then (m :: Model):PivotTo(cf) else L.part.CFrame = cf end
	end
end)

-- ---------------------------------------------------------------- peels, frost, the blood cross
local peels: { [number]: BasePart } = {}
local function rootOf(m: any): BasePart?
	return if typeof(m) == "Instance" then (m :: Instance):FindFirstChild("HumanoidRootPart") :: BasePart? else nil
end
local function cross(at: Vector3, size: number, life: number, attach: BasePart?)
	-- a deep red X (two flat bars), held on the body it's in
	for i = 0, 1 do
		local b = Instance.new("Part")
		b.Size = Vector3.new(size, size * 0.18, 0.12)
		b.Color = Color3.fromRGB(140, 14, 30); b.Material = Enum.Material.Neon
		b.Anchored = attach == nil; b.CanCollide = false; b.CanQuery = false; b.CanTouch = false; b.CastShadow = false
		local cam = workspace.CurrentCamera
		local face = CFrame.lookAt(at, at + (cam.CFrame.Position - at))
		b.CFrame = face * CFrame.Angles(0, 0, (i == 0 and 1 or -1) * math.pi / 4)
		if attach then
			local wd = Instance.new("WeldConstraint"); wd.Part0 = attach; wd.Part1 = b; wd.Parent = b
		end
		b.Parent = folder
		task.delay(life, function() b:Destroy() end)
	end
end
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" or type(f.k) ~= "string" then return end
	local k = f.k
	if k == "proj" and type(f.id) == "number" and typeof(f.p) == "Vector3" and typeof(f.v) == "Vector3" then
		local w = W[f.w] :: any
		local kind = w and w.proj or "ball"
		live[f.id] = { part = shape(kind), p = f.p, v = f.v, g = tonumber(f.g) or 0, k = kind, spin = 0 }
		if f.by ~= me.UserId and w and w.snd then Sfx.play(w.snd, f.p, 0.8) end
		if f.by ~= me.UserId and w and w.snd2 then task.delay(0.03, Sfx.play, w.snd2, f.p, 0.8) end
	elseif k == "proju" and type(f.id) == "number" then
		local L = live[f.id]
		if L and typeof(f.p) == "Vector3" and typeof(f.v) == "Vector3" then
			L.p, L.v = f.p, f.v
			if L.k == "ball" then Sfx.play("tennis_bounce", f.p, 0.8, 1 + 0.08 * (tonumber(f.b) or 0)) end
		end
	elseif k == "projx" and type(f.id) == "number" then
		local L = live[f.id]
		local at = if typeof(f.p) == "Vector3" then f.p elseif L then L.p else nil
		local kind = L and L.k
		drop(f.id)
		if not at then return end
		if f.x then
			Fx.explosion(at, tonumber(f.r) or 22.5)
			Sfx.play("boom", at, 1)
		elseif f.b then
			if kind == "snow" then Fx.drip(at, 8); Sfx.play("thwack", at, 0.7)
			elseif kind == "peel" then Fx.impact(at, Vector3.yAxis, nil, Enum.Material.SmoothPlastic, { hole = false, scale = 0.8 }); Sfx.play("bonk", at, 0.8)
			else Fx.impact(at, Vector3.yAxis, nil, Enum.Material.Fabric, { hole = false, scale = 0.6 }) end
		end
	elseif k == "peel" and type(f.id) == "number" and typeof(f.p) == "Vector3" then
		local m = kit("w_pj_peel")
		local part: BasePart
		if m then
			for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false end end
			m:PivotTo(CFrame.new(f.p + Vector3.new(0, 0.05, 0)) * CFrame.Angles(0, math.random() * 6.28, 0))
			m.Parent = folder
			part = (m.PrimaryPart or m:FindFirstChildWhichIsA("BasePart")) :: BasePart
		else
			part = Instance.new("Part")
			part.Size = Vector3.new(1.0, 0.12, 0.9); part.Color = Color3.fromRGB(225, 200, 85); part.Material = Enum.Material.SmoothPlastic
			part.Anchored = true; part.CanCollide = false; part.CanQuery = false; part.CastShadow = false
			part.CFrame = CFrame.new(f.p + Vector3.new(0, 0.06, 0)) * CFrame.Angles(0, math.random() * 6.28, 0)
			part.Parent = folder
		end
		peels[f.id] = part
	elseif k == "peelx" and type(f.id) == "number" then
		local part = peels[f.id]
		peels[f.id] = nil
		if part then
			if f.s then Sfx.play("bonk", part.Position, 0.6, 1.3) end
			local m = part.Parent
			if m and m ~= folder and m:IsA("Model") then m:Destroy() else part:Destroy() end
		end
	elseif k == "frost" or k == "freeze" then
		local r = rootOf(f.model)
		if r then Fx.drip(r.Position + Vector3.new(0, 1, 0), if k == "freeze" then 14 else 4) end
		if k == "freeze" and r then
			-- frozen solid: a pale ice box round them for the freeze
			local ice = Instance.new("Part")
			ice.Size = Vector3.new(4, 6.5, 4); ice.Color = Color3.fromRGB(200, 230, 245); ice.Material = Enum.Material.Ice
			ice.Transparency = 0.45; ice.Anchored = true; ice.CanCollide = false; ice.CanQuery = false; ice.CastShadow = false
			ice.CFrame = r.CFrame * CFrame.new(0, 0.3, 0)
			ice.Parent = folder
			Sfx.play("ting", r.Position, 0.8)
			task.delay(tonumber(f.dur) or 2.4, function() ice:Destroy() end)
		end
	elseif k == "shatter" and typeof(f.p) == "Vector3" then
		for _ = 1, 3 do Fx.impact(f.p, Vector3.yAxis, nil, Enum.Material.Ice, { hole = false, scale = 1.6 }) end
		Sfx.play("ting", f.p, 1, 1.4)
	elseif k == "bcross" then
		local st = f.st
		local r = rootOf(f.model)
		if st == "stick" then
			if type(f.id) == "number" then drop(f.id) end
			if r then cross(r.Position, 1.2, 0.85, r) end
			Sfx.play("blood_stick", if typeof(f.p) == "Vector3" then f.p else nil, 0.8)
		elseif st == "erupt" then
			if r then cross(r.Position + Vector3.new(0, 0.5, 0), if f.thin then 2.4 else 4, 0.3, r) end
			Sfx.play("blood_erupt", if r then r.Position else nil, 0.9)
		elseif st == "boom" then
			if typeof(f.p) == "Vector3" then
				Fx.blast(f.p, if f.thin then 0.8 else 1.4)
				Sfx.play("blood_boom", f.p, 1)
			end
		elseif st == "wall" then
			if type(f.id) == "number" then drop(f.id) end
			if typeof(f.p) == "Vector3" then cross(f.p, 1.0, 1.2, nil) end
		end
	end
end)

return P
