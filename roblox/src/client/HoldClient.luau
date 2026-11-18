--!strict
-- weapons batch B (18 Nov 2026): your side of the held-trigger weapons (kind "hold": the Leaf Blower, the Hot Sauce,
-- the Big Laser Pointer; HoldWeapons.server does the hurting). Arsenal calls press / release on the trigger and step
-- every frame: this tells the server where you look while it's down, pushes YOU (the blower's thrust and hover, the
-- breath's jet, the laser's kick), slows you while the laser charges (speed), and draws everyone's: the blower's air
-- and leaves, the breath of fire, the laser's charge glow and beam, a burnt swig's smoke
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Body = require(script.Parent:WaitForChild("Body"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local H = {}
local me = Players.LocalPlayer
local W = Weapons.list
local st = { wid = nil :: string?, down = false, t0 = 0, aimT = 0, fuel = 4, exhaleUntil = 0, cdUntil = 0 }

local function send(wid: string, mode: any, look: Vector3?)
	local r = Remotes:FindFirstChild("Hold")
	if r and r:IsA("RemoteEvent") then r:FireServer(wid, mode, look) end
end
local function cam(): (Vector3, Vector3)
	local c = workspace.CurrentCamera
	return c.CFrame.Position, c.CFrame.LookVector
end

function H.press(wid: string)
	local w = W[wid]
	if not w or w.kind ~= "hold" or st.down then return end
	local now = os.clock()
	if w.hold == "beam" and now < st.cdUntil then return end
	if w.hold == "breath" and now < st.exhaleUntil then return end
	st.wid, st.down, st.t0, st.aimT = wid, true, now, 0
	local _, look = cam()
	send(wid, true, look)
end
function H.release(wid: string?)
	if not st.down or not st.wid then return end
	local w = W[st.wid] :: any
	local now = os.clock()
	local held = now - st.t0
	st.down = false
	local _, look = cam()
	send(st.wid :: string, false, look)
	if w.hold == "breath" and held > 0.12 and held <= w.maxCharge then
		st.exhaleUntil = now + math.min(held, w.maxCharge) * w.exhaleMul
	elseif w.hold == "beam" then
		local k = math.clamp((held - w.tap) / (w.charge - w.tap), 0, 1)
		local dur = w.dur[1] + (w.dur[2] - w.dur[1]) * k
		st.cdUntil = now + dur + w.cd
		if k > 0.5 then Body.push(-look * 5 * k * Weapons.S) end -- (a big beam kicks you back)
	end
end
-- the laser slows you while it charges (Arsenal multiplies your run speed by this)
function H.speed(): number
	local w = st.wid and W[st.wid] :: any
	return if st.down and w and w.hold == "beam" then w.slow or 1 else 1
end
-- every frame, with what you hold: put the trigger down if you swapped away, tell the server where you look, push you
function H.step(dt: number, held: string)
	local w = W[held] :: any
	if st.down and st.wid ~= held then H.release(st.wid) end
	if not w or w.kind ~= "hold" then
		if w == nil or w.kind ~= "hold" then st.fuel = math.min(4, st.fuel + 0.8 * dt) end
		return
	end
	local now = os.clock()
	local _, look = cam()
	local live = st.down or now < st.exhaleUntil or now < st.cdUntil - (w.cd or 0)
	if live and now - st.aimT > 1 / 15 then st.aimT = now; send(held, "aim", look) end
	if w.hold == "blow" then
		if st.down and st.fuel > 0 then
			st.fuel = math.max(0, st.fuel - dt)
			local v = -look * w.self * dt
			-- (pointed at the floor: off the ground and held up)
			if look.Y < -0.3 and Body.hum and Body.hum.FloorMaterial ~= Enum.Material.Air then v += Vector3.new(0, 2, 0) end
			Body.push(v)
		elseif not st.down then
			st.fuel = math.min(w.fuel, st.fuel + w.regen * dt)
		end
	elseif w.hold == "breath" and now < st.exhaleUntil then
		Body.push(-look * w.jet * dt)
	end
	if w.hold == "breath" and st.down and now - st.t0 > w.coughAt then st.down = false end -- (the server burnt you)
end
me.CharacterAdded:Connect(function() st.down, st.fuel, st.exhaleUntil, st.cdUntil = false, 4, 0, 0 end)

-- ---------------------------------------------------------------- everyone's: the server's Fx
local loops: { [string]: { e: ParticleEmitter?, s: Sound?, untilT: number? } } = {}
local beamT: { [string]: number } = {} -- (when each shooter's beam last ticked: its zap plays once, on the first)
local function handOf(model: any): (Vector3?, Vector3?)
	if typeof(model) ~= "Instance" then return nil, nil end
	if model == me.Character then
		local p, l = cam()
		return p + l * 2 - workspace.CurrentCamera.CFrame.UpVector * 0.5, l
	end
	local hw = (model :: Instance):FindFirstChild("HeldWeapon")
	local hr = hw and (hw :: Model).PrimaryPart
	local a = hr and hr:FindFirstChild("Muzzle")
	local head = (model :: Instance):FindFirstChild("Head") :: BasePart?
	local look = if head then head.CFrame.LookVector else Vector3.zAxis
	if a and a:IsA("Attachment") then return a.WorldPosition, look end
	return if head then head.Position else nil, look
end
local function emitter(kind: string): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.LightInfluence = 0.6
	if kind == "blow" then
		e.Color = ColorSequence.new(Color3.fromRGB(150, 140, 95), Color3.fromRGB(110, 120, 80))
		e.Size = NumberSequence.new(0.25, 0.15); e.Transparency = NumberSequence.new(0.1, 1)
		e.Speed = NumberRange.new(40, 60); e.Lifetime = NumberRange.new(0.3, 0.6); e.Rate = 60
		e.SpreadAngle = Vector2.new(18, 18); e.RotSpeed = NumberRange.new(-400, 400); e.Drag = 3
	else -- (the breath: fire from the mouth, dark at the end)
		e.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 140)), ColorSequenceKeypoint.new(0.4, Color3.fromRGB(240, 120, 40)), ColorSequenceKeypoint.new(1, Color3.fromRGB(60, 45, 40)) })
		e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 2.4) })
		e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) })
		e.Speed = NumberRange.new(30, 42); e.Lifetime = NumberRange.new(0.5, 0.9); e.Rate = 90
		e.SpreadAngle = Vector2.new(14, 14); e.LightEmission = 0.6; e.Drag = 1.5
	end
	return e
end
local function loopOn(key: string, kind: string, model: any, snd: string?, untilT: number?)
	local L = loops[key] or {}
	loops[key] = L
	L.untilT = untilT
	if not L.e then
		local att = Instance.new("Attachment")
		att.Parent = workspace.Terrain
		local e = emitter(kind)
		e.Parent = att
		L.e = e
		local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
		local src = snd and lib and lib:FindFirstChild(snd)
		if src and src:IsA("Sound") then
			local s = src:Clone(); s.Looped = true; s.Parent = att; s:Play(); L.s = s
		end
	end
	;(L :: any).model = model
end
local function loopOff(key: string)
	local L = loops[key]
	if not L then return end
	if L.e then local a = L.e.Parent; L.e.Enabled = false; task.delay(1, function() if a then a:Destroy() end end) end
	loops[key] = nil
end
RunService.RenderStepped:Connect(function()
	for key, L in loops do
		local p, l = handOf((L :: any).model)
		if L.untilT and os.clock() > L.untilT then loopOff(key) continue end
		if p and l and L.e and L.e.Parent and L.e.Parent:IsA("Attachment") then
			(L.e.Parent :: Attachment).WorldCFrame = CFrame.lookAt(p, p + l) * CFrame.Angles(-math.pi / 2, 0, 0)
		end
	end
end)
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" or type(f.k) ~= "string" then return end
	local key = tostring(f.by or f.model) .. ":" .. f.k
	if f.k == "blow" then
		if f.on then loopOn(key, "blow", f.model, "blower_loop") else loopOff(key) end
	elseif f.k == "breath" then
		if f.on then loopOn(key, "breath", f.model, "breath_loop", os.clock() + (tonumber(f.dur) or 3.6)) else loopOff(key) end
	elseif f.k == "cough" then
		local p = handOf(f.model)
		if p then Fx.impact(p, Vector3.yAxis, nil, Enum.Material.Slate, { hole = false, scale = 1.4 }) end
	elseif f.k == "charge" and f.on then
		local p = handOf(f.model)
		if p then Sfx.play("laser_whine", if f.model == me.Character then nil else p, 0.8) end -- (the charge rising)
	elseif f.k == "beam" and typeof(f.a) == "Vector3" and typeof(f.b) == "Vector3" then
		local t = os.clock()
		if t - (beamT[key] or -1) > 0.3 then Sfx.play("laser_fire", if f.model == me.Character then nil else f.a, 1) end
		beamT[key] = t
		-- the beam: a green tube as wide as its reach (r grows with the charge, kq) round a white core
		local wide = (0.22 + 0.48 * math.clamp(tonumber(f.kq) or 0, 0, 1)) * Weapons.S
		local p = handOf(f.model) or f.a
		Fx.tracer(p :: Vector3, f.b, Color3.fromRGB(120, 255, 100), wide * 2, 0.12)
		Fx.tracer(p :: Vector3, f.b, Color3.fromRGB(235, 255, 230), wide * 0.6, 0.12)
	end
end)

return H
