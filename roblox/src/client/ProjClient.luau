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
function P.throw(held: string, eye: Vector3, look: Vector3, c: number?): boolean
	local w = W[held] :: any
	if not w or (w.kind ~= "proj" and w.kind ~= "bow") then return false end
	local t = os.clock()
	if t < (nextT[held] or 0) then return false end
	nextT[held] = t + (w.cd or 0.5)
	local r = Remotes:FindFirstChild("Throw")
	if r and r:IsA("RemoteEvent") then r:FireServer(held, eye, look, c) end
	if w.snd then Sfx.play(w.snd) end
	if w.snd2 then task.delay(0.03, Sfx.play, w.snd2) end
	return true
end

-- (weapons batch D) the Bow's draw: when you started pulling (nil: not drawing). the hold reads P.drawn() (0..1)
P.bowT = nil :: number?
function P.drawn(): number
	local w = W.bow :: any
	return if P.bowT and w then math.clamp((os.clock() - (P.bowT :: number)) / w.drawT, 0, 1) else 0
end
-- each arrow tip's colour (the shooter's next one is BowTip on them)
P.TIP = {
	regular = Color3.fromRGB(221, 221, 221), power = Color3.fromRGB(255, 225, 77), knockback = Color3.fromRGB(79, 216, 255),
	flame = Color3.fromRGB(255, 106, 26), explosion = Color3.fromRGB(255, 48, 48), gas = Color3.fromRGB(125, 255, 79),
	sleep = Color3.fromRGB(176, 125, 255),
} :: { [string]: Color3 }

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
	bowl = { Color3.fromRGB(44, 52, 92), "Ball", Vector3.new(2.7, 2.7, 2.7) }, -- (weapons batch D)
	slipper = { Color3.fromRGB(255, 154, 213), "Block", Vector3.new(1.0, 0.35, 2.1) },
	arrow = { Color3.fromRGB(120, 90, 60), "Block", Vector3.new(0.12, 0.12, 2.4) },
	card = { Color3.fromRGB(245, 245, 240), "Block", Vector3.new(0.27, 0.03, 0.39) }, -- (batch E)
}
type Live = { part: BasePart, p: Vector3, v: Vector3, g: number, k: string, spin: number, r: number? }
local live: { [number]: Live } = {}
-- the kit models for the shots (guns-remodel, v813: JankfireWeapons w_pj_*, built in metres, nose along -Z, origin at
-- the middle); a kind with none (the tennis ball, the blood cross) stays a simple shape
local KIT = { rocket = "w_pj_chicken", peel = "w_pj_banana", snow = "w_pj_snowball", bowl = "w_pj_bowling", slipper = "w_pj_slipper", arrow = "w_pj_arrow", card = "w_pj_card" } :: { [string]: string }
-- (a thrown card shows its suit's pip only: the kit's pip_h / pip_s / pip_c / pip_d / pip_j sit on top of each other)
local function pips(root: BasePart, suit: string?)
	local m = root.Parent
	if not m or not m:IsA("Model") then return end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and string.sub(d.Name, 1, 4) == "pip_" then
			d.Transparency = if suit and string.sub(d.Name, 5, 5) == suit then 0 else 1
		end
	end
end
-- (an arrow's tip in its tip's colour: the kit's tip_ pieces, or the stand-in's point)
local function tint(root: BasePart, tip: string?)
	local col = tip and P.TIP[tip]
	if not col then return end
	local m = root.Parent
	if m and m:IsA("Model") then
		for _, d in m:GetDescendants() do if d:IsA("BasePart") and string.sub(d.Name, 1, 4) == "tip_" then d.Color = col end end
	end
end
-- (the bowling ball rolls: each client keeps it on the floor itself, the server only sends walls and hits)
local floorParams = RaycastParams.new()
floorParams.FilterType = Enum.RaycastFilterType.Include
local function kit(name: string, fitR: number?): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local t = lib and lib:FindFirstChild(name)
	if not t or not t:IsA("Model") then return nil end
	local m = t:Clone()
	m:ScaleTo(m:GetScale() * S) -- (metres to studs: S studs a metre)
	if fitR then -- (the bowling ball: as big as what it hits with, whatever size the file is)
		local _, size = m:GetBoundingBox()
		local big = math.max(size.X, size.Y, size.Z)
		if big > 1e-3 then m:ScaleTo(m:GetScale() * (2 * fitR) / big) end
	end
	return m
end
local function shape(k: string, r: number?): BasePart
	local m = if KIT[k] then kit(KIT[k], if k == "bowl" then r else nil) else nil
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
-- a looped recording riding something (the rolling ball): the library's own Sound cloned onto it, gone with it
-- (Sfx.play's copies are cleaned up after a few seconds)
local function loopOn(part: Instance, name: string)
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local s = lib and lib:FindFirstChild(name)
	if not s or not s:IsA("Sound") then return end
	local c = s:Clone()
	c.Looped = true
	c.Parent = part
	c:Play()
end
-- the whole drawn thing a part belongs to (a kit model's root can sit inside a node model: destroying only its parent
-- left the rest lying there, the owner's peels that never went away)
local function topOf(part: Instance): Instance
	local top = part
	while top.Parent and top.Parent ~= folder and top.Parent ~= workspace do top = top.Parent :: Instance end
	return top
end
local function drop(id: number)
	local L = live[id]
	if not L then return end
	live[id] = nil
	topOf(L.part):Destroy()
end
local drawSent = false -- (the Bow's draw as the server knows it: BowDraw true at the press, false when it ends)
RunService.RenderStepped:Connect(function(dt: number)
	if (P.bowT ~= nil) ~= drawSent then
		drawSent = P.bowT ~= nil
		local r = Remotes:FindFirstChild("BowDraw")
		if r and r:IsA("RemoteEvent") then r:FireServer(drawSent) end
	end
	local map = workspace:FindFirstChild("Map")
	if map then floorParams.FilterDescendantsInstances = { map } end
	for _, L in live do
		L.v -= Vector3.new(0, L.g * S * dt, 0)
		L.p += L.v * dt
		if L.k == "bowl" and map and L.r then
			local hit = workspace:Raycast(L.p + Vector3.new(0, L.r, 0), Vector3.new(0, -2 * L.r, 0), floorParams)
			if hit and L.p.Y - hit.Position.Y < L.r then
				L.p = Vector3.new(L.p.X, hit.Position.Y + L.r, L.p.Z)
				if L.v.Y < 0 then L.v = Vector3.new(L.v.X, 0, L.v.Z) end
			end
		end
		L.spin += dt * 18
		local face = if L.v.Magnitude > 0.1 then CFrame.lookAt(L.p, L.p + L.v) else CFrame.new(L.p)
		local cf = if L.k == "rocket" or L.k == "blood" or L.k == "arrow" then face elseif L.k == "card" then face * CFrame.Angles(0, L.spin * 2, 0) else face * CFrame.Angles(L.spin, L.spin * 0.6, 0)
		local m = topOf(L.part)
		if m:IsA("Model") then m:PivotTo(cf) else L.part.CFrame = cf end
	end
end)

-- ---------------------------------------------------------------- peels, frost, the blood cross
local peels: { [number]: Instance } = {} -- (the whole peel: its kit model or the stand-in part)
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
		live[f.id] = { part = shape(kind, tonumber(f.r)), p = f.p, v = f.v, g = tonumber(f.g) or 0, k = kind, spin = 0, r = tonumber(f.r) }
		if kind == "bowl" then loopOn(live[f.id].part, "bowl_roll") end -- (batch D: the ball's roll, wherever it goes)
		if kind == "arrow" then
			local part = live[f.id].part
			tint(part, f.tip)
			if part.Parent == folder and type(f.tip) == "string" and P.TIP[f.tip] then part.Color = P.TIP[f.tip] end -- (the stand-in: all of it)
		end
		if f.by ~= me.UserId and w and w.snd then Sfx.play(w.snd, f.p, 0.8) end
		if f.by ~= me.UserId and w and w.snd2 then task.delay(0.03, Sfx.play, w.snd2, f.p, 0.8) end
	elseif k == "proju" and type(f.id) == "number" then
		local L = live[f.id]
		if L and typeof(f.p) == "Vector3" and typeof(f.v) == "Vector3" then
			L.p, L.v = f.p, f.v
			if L.k == "ball" then Sfx.play("tennis_bounce", f.p, 0.8, 1 + 0.08 * (tonumber(f.b) or 0)) end
			if f.h then -- (batch D: the bowling ball or the slipper went through someone)
				Sfx.play(if L.k == "bowl" then "bowl_hit" else "slipper_hit", f.p, 0.9)
			end
		end
	elseif k == "projx" and type(f.id) == "number" then
		local L = live[f.id]
		local at = if typeof(f.p) == "Vector3" then f.p elseif L then L.p else nil
		local kind = L and L.k
		-- (batch D: an arrow in a wall stays there a few seconds)
		if f.stuck and L then
			local m = topOf(L.part)
			if m:IsA("Model") then
				live[f.id] = nil
				task.delay(4, function() m:Destroy() end)
			else
				live[f.id] = nil
				local part = L.part
				task.delay(4, function() part:Destroy() end)
			end
			Sfx.play("arrow_wall", at or L.p, 0.8)
			return
		end
		drop(f.id)
		if not at then return end
		if f.c then Sfx.play("slipper_catch", at, 0.7) end -- (batch D: the slipper back in your hand)
		if kind == "arrow" and f.b then Sfx.play("arrow_hit", at, 0.9) end
		if f.x then
			Fx.explosion(at, tonumber(f.r) or 22.5)
			Sfx.play("boom", at, 1)
		elseif f.b then
			if kind == "snow" then Fx.drip(at, 8); Sfx.play("thwack", at, 0.7)
			elseif kind == "peel" then Fx.impact(at, Vector3.yAxis, nil, Enum.Material.SmoothPlastic, { hole = false, scale = 0.8 }); Sfx.play("bonk", at, 0.8)
			else Fx.impact(at, Vector3.yAxis, nil, Enum.Material.Fabric, { hole = false, scale = 0.6 }) end
		end
	elseif k == "thrust" and typeof(f.p) == "Vector3" then
		-- (owner, 18 Nov 2026) the Chicken Rocket's back-blast behind the launcher. close to your own camera (yours, in first
		-- person or the shoulder camera) the fireball would fill the screen: a puff and the boom instead
		local cam = workspace.CurrentCamera
		if cam and (cam.CFrame.Position - f.p).Magnitude < 3.5 * Weapons.S then
			Fx.impact(f.p, if typeof(f.d) == "Vector3" then f.d else Vector3.yAxis, nil, Enum.Material.Slate, { hole = false, scale = 1.2 })
			Sfx.play("boom", nil, 0.35)
		else
			Fx.explosion(f.p, 1.5 * Weapons.S)
			Sfx.play("boom", f.p, 0.55)
		end
	elseif k == "projn" and type(f.ids) == "table" and type(f.ps) == "table" and type(f.vs) == "table" then
		-- (batch E) a whole fan of cards in one message
		for i, id in f.ids do
			local p, v = f.ps[i], f.vs[i]
			if type(id) ~= "number" or typeof(p) ~= "Vector3" or typeof(v) ~= "Vector3" then continue end
			local part = shape("card")
			pips(part, if type(f.suit) == "string" then f.suit else nil)
			live[id] = { part = part, p = p, v = v, g = tonumber(f.g) or 0, k = "card", spin = math.random() * 6, r = tonumber(f.r) }
		end
		if f.by ~= me.UserId then Sfx.play("card_throw", f.ps[1], 0.7) end
	elseif k == "bowlstrike" and typeof(f.p) == "Vector3" then
		Sfx.play("bowl_strike", f.p, 1) -- (batch D: three down)
	elseif k == "peel" and type(f.id) == "number" and typeof(f.p) == "Vector3" then
		-- (owner, 18 Nov 2026: "they clip throught the floor") the peel lies flat on the surface it landed on (the server's
		-- normal: slopes and steps too), turned at random about it, its lowest point on the surface
		local nrm = if typeof(f.n) == "Vector3" and f.n.Magnitude > 0.5 then (f.n :: Vector3).Unit else Vector3.yAxis
		local m = kit("w_pj_peel")
		local root: Instance
		if m then
			for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end end
			root = m
		else
			local part = Instance.new("Part")
			part.Size = Vector3.new(1.0, 0.12, 0.9); part.Color = Color3.fromRGB(225, 200, 85); part.Material = Enum.Material.SmoothPlastic
			part.Anchored = true; part.CanCollide = false; part.CanQuery = false; part.CastShadow = false
			root = part
		end
		local rx = (if math.abs(nrm.Y) < 0.95 then Vector3.yAxis else Vector3.xAxis):Cross(nrm).Unit
		local base = CFrame.fromMatrix(f.p, rx, nrm) * CFrame.Angles(0, math.random() * 2 * math.pi, 0)
		local function place(cf: CFrame) if root:IsA("Model") then root:PivotTo(cf) else (root :: BasePart).CFrame = cf end end
		place(base)
		local low = math.huge -- (how far the lowest corner sits along the normal from the hit point)
		local parts = if root:IsA("BasePart") then { root } else root:GetDescendants()
		for _, b in parts do
			if not b:IsA("BasePart") then continue end
			local h = b.Size / 2
			for _, c in { Vector3.new(1, 1, 1), Vector3.new(1, 1, -1), Vector3.new(1, -1, 1), Vector3.new(1, -1, -1), Vector3.new(-1, 1, 1), Vector3.new(-1, 1, -1), Vector3.new(-1, -1, 1), Vector3.new(-1, -1, -1) } do
				low = math.min(low, (b.CFrame * (h * c) - f.p):Dot(nrm))
			end
		end
		if low < math.huge then place(base + nrm * (0.02 - low)) end
		root.Parent = folder
		peels[f.id] = root
	elseif k == "peelx" and type(f.id) == "number" then
		local root = peels[f.id]
		peels[f.id] = nil
		if root then
			local at = if root:IsA("Model") then root:GetPivot().Position elseif root:IsA("BasePart") then root.Position else nil
			if f.s then
				if at then Sfx.play("bonk", at, 0.6, 1.3) end
				root:Destroy() -- (stepped on: gone at once)
			else
				-- (its time is up: it fades out, not a pop)
				local list = if root:IsA("BasePart") then { root } else root:GetDescendants()
				local t0 = os.clock()
				local conn: RBXScriptConnection
				conn = RunService.RenderStepped:Connect(function()
					local k2 = math.clamp((os.clock() - t0) / 0.6, 0, 1)
					for _, b in list do if b:IsA("BasePart") then b.LocalTransparencyModifier = k2 end end
					if k2 >= 1 then conn:Disconnect(); root:Destroy() end
				end)
			end
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
